import argparse
import difflib
import unicodedata
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import types
import typing
import warnings
from datetime import datetime
from pathlib import Path


TEXT_FILES = [
    "ozet.tex",
    "abstract.tex",
    "summary.tex",
    "tesekkur.tex",
    "onsoz.tex",
    "bolum1.tex",
    "bolum2.tex",
    "bolum3.tex",
    "bolum4.tex",
    "bolum5.tex",
    "bolum6.tex",
    "ekler.tex",
    "ozgecmis.tex",
]
SIGNATURE_FILES = ["tez.tex", *TEXT_FILES]
REVIEW_SETTINGS_FILE = "yazim-denetimi-ayarlar.json"
REVIEW_SUMMARY_FILE = "yazim-denetimi-ozet.json"

MOJIBAKE = ["Ä", "Å", "Ã", "�"]
PLACEHOLDERS = ["TODO", "???", "XXXXX", "Tez Başlığı", "Thesis Title", "Öğrenci Adı", "Name SURNAME"]
STRUCTURE_IGNORED_ENVS = {"center", "table", "figure", "tabular", "tabularx", "longtable", "comment"}
COMMON_SUGGESTIONS = [
    (re.compile(r"\bher\s+şey\b", re.I), "TDK'ya göre genellikle `her şey` ayrı yazılır; bağlama göre kontrol edin."),
    (re.compile(r"\bbir\s+çok\b", re.I), "`birçok` çoğu bağlamda bitişik yazılır."),
    (re.compile(r"\bhiç\s+bir\b", re.I), "`hiçbir` çoğu bağlamda bitişik yazılır."),
    (re.compile(r"\byada\b", re.I), "`ya da` ayrı yazılır."),
    (re.compile(r"\bveya\s+da\b", re.I), "`veya da` yerine genellikle `veya` ya da `ya da` tercih edilir."),
    (re.compile(r"\s+([,.;:!?])"), "Noktalama işaretinden önce boşluk olmamalı."),
    (re.compile(r"(?<!\d)([,.;:!?])(?=[^\s}\]\d])"), "Noktalama işaretinden sonra boşluk gerekebilir."),
    (re.compile(r"\b(\w+)\s+\1\b", re.I), "Art arda yinelenen sözcük olabilir."),
]
FOREIGN_TECHNICAL_PHRASES_TR = [
    "alternating direction",
    "finite difference",
    "crank-nicolson",
    "newell-whitehead-segel",
    "hopf-cole",
    "b-spline",
]
FOREIGN_TECHNICAL_PHRASE_PATTERNS_TR = [
    (re.compile(r"newell-whitehead-segel(?:\s*\(NWS\))?", re.I), "newell-whitehead-segel"),
    *[
        (re.compile(rf"(?<![A-Za-z]){re.escape(phrase)}(?![A-Za-z])", re.I), phrase)
        for phrase in FOREIGN_TECHNICAL_PHRASES_TR
        if phrase != "newell-whitehead-segel"
    ],
]

DICTIONARY_CACHE = {}
SUGGESTION_INDEX_CACHE = {}
SPELL_CHECK_CACHE = {}
SPELL_SUGGESTION_CACHE = {}
ZEMBEREK_ENGINE = None
ZEMBEREK_LOAD_ATTEMPTED = False
ZEMBEREK_LOAD_ERROR = ""
ZEMBEREK_LOAD_LOCK = threading.Lock()
MAX_SPELLING_WARNINGS_PER_LINE = 8
MANUAL_VERTICAL_SPACE_RE = re.compile(r"\\(?:bigskip|medskip|smallskip)\b")


def datetime_now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _install_zemberek_compat():
    # zemberek-python 0.2.x still expects compatibility modules removed in
    # newer Python versions, and one language-model reader needs unsigned byte
    # arithmetic with current numpy. Keep the patch local and best-effort.
    if "typing.io" not in sys.modules:
        typing_io = types.ModuleType("typing.io")
        typing_io.TextIO = typing.TextIO
        typing_io.BinaryIO = typing.BinaryIO
        sys.modules["typing.io"] = typing_io
    if "typing.re" not in sys.modules:
        typing_re = types.ModuleType("typing.re")
        typing_re.Pattern = typing.Pattern
        typing_re.Match = typing.Match
        sys.modules["typing.re"] = typing_re

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from zemberek.lm.compression.gram_data_array import GramDataArray

    def ubyte(values, index):
        return int(values[index]) & 255

    def get_probability_rank(self, index: int) -> int:
        page_id = self.rshift(index, self.page_shift)
        page_index = (index & self.index_mask) * self.block_size + self.fp_size
        data = self.data[page_id]
        if self.prob_size == 1:
            return ubyte(data, page_index)
        if self.prob_size == 2:
            return (ubyte(data, page_index) << 8) | ubyte(data, page_index + 1)
        if self.prob_size == 3:
            return (ubyte(data, page_index) << 16) | (ubyte(data, page_index + 1) << 8) | ubyte(data, page_index + 2)
        return -1

    def get_back_off_rank(self, index: int) -> int:
        page_id = self.rshift(index, self.page_shift)
        page_index = (index & self.index_mask) * self.block_size + self.fp_size + self.prob_size
        data = self.data[page_id]
        if self.backoff_size == 1:
            return ubyte(data, page_index)
        if self.backoff_size == 2:
            return (ubyte(data, page_index) << 8) | ubyte(data, page_index + 1)
        if self.backoff_size == 3:
            return (ubyte(data, page_index) << 16) | (ubyte(data, page_index + 1) << 8) | ubyte(data, page_index + 2)
        return -1

    GramDataArray.get_probability_rank = get_probability_rank
    GramDataArray.get_back_off_rank = get_back_off_rank


class ZemberekSpellEngine:
    def __init__(self, morphology, checker):
        self.morphology = morphology
        self.checker = checker
        self.accept_cache = {}
        self.deascii_cache = {}
        self.suggest_cache = {}

    def accepts(self, word):
        value = str(word).strip("'’")
        if not value:
            return True
        key = value.casefold()
        if key not in self.accept_cache:
            try:
                self.accept_cache[key] = bool(self.morphology.analyze(value).analysis_results)
            except Exception:
                self.accept_cache[key] = False
        return self.accept_cache[key]

    def deascii_candidates(self, word, max_candidates=256):
        value = str(word).strip("'’").casefold()
        if value in self.deascii_cache:
            return self.deascii_cache[value][:max_candidates]
        if not value or not re.fullmatch(r"[a-z]+", value):
            return []
        choices = {
            "c": ("c", "\u00e7"),
            "g": ("g", "\u011f"),
            "i": ("i", "\u0131"),
            "o": ("o", "\u00f6"),
            "s": ("s", "\u015f"),
            "u": ("u", "\u00fc"),
        }
        variants = [""]
        for char in value:
            options = choices.get(char, (char,))
            next_variants = []
            for prefix in variants:
                for option in options:
                    next_variants.append(prefix + option)
                    if len(next_variants) >= max_candidates:
                        break
                if len(next_variants) >= max_candidates:
                    break
            variants = next_variants
        candidates = []
        seen = {value}
        for candidate in variants:
            if candidate in seen:
                continue
            seen.add(candidate)
            if self.accepts(candidate):
                candidates.append(candidate)
        candidates.sort(key=lambda item: sum(1 for left, right in zip(value, item) if left != right))
        self.deascii_cache[value] = candidates
        return candidates

    def suggest(self, word, limit=3):
        value = str(word).strip("'’")
        key = value.casefold()
        if key not in self.suggest_cache:
            suggestions = self.deascii_candidates(value)
            try:
                suggestions.extend(list(self.checker.suggest_for_word(value)))
            except Exception:
                pass
            deduped = []
            seen = set()
            for suggestion in suggestions:
                normalized = str(suggestion).casefold()
                if normalized not in seen:
                    seen.add(normalized)
                    deduped.append(suggestion)
            self.suggest_cache[key] = deduped
        return self.suggest_cache[key][:limit]


def load_zemberek_engine():
    global ZEMBEREK_ENGINE, ZEMBEREK_LOAD_ATTEMPTED, ZEMBEREK_LOAD_ERROR
    if os.environ.get("INONU_DISABLE_ZEMBEREK") == "1":
        ZEMBEREK_LOAD_ERROR = "INONU_DISABLE_ZEMBEREK=1"
        return None
    with ZEMBEREK_LOAD_LOCK:
        if ZEMBEREK_LOAD_ATTEMPTED:
            return ZEMBEREK_ENGINE
        ZEMBEREK_LOAD_ATTEMPTED = True
        try:
            _install_zemberek_compat()
            logging.getLogger("zemberek").setLevel(logging.ERROR)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                from zemberek import TurkishMorphology, TurkishSpellChecker
                morphology = TurkishMorphology.create_with_defaults()
                checker = TurkishSpellChecker(morphology)
            ZEMBEREK_ENGINE = ZemberekSpellEngine(morphology, checker)
        except Exception as exc:
            ZEMBEREK_LOAD_ERROR = f"{type(exc).__name__}: {exc}"
            ZEMBEREK_ENGINE = None
    return ZEMBEREK_ENGINE


def dictionary_status(dictionary, lang):
    if str(lang).lower().startswith("en"):
        if getattr(dictionary, "hunspell", None):
            return "İngilizce Hunspell sözlüğü aktif."
        return "İngilizce temel sözlük aktif."
    if getattr(dictionary, "zemberek", None):
        return "Türkçe Zemberek morfoloji sözlüğü aktif."
    if getattr(dictionary, "hunspell", None):
        return "Türkçe Hunspell sözlüğü aktif."
    if ZEMBEREK_LOAD_ERROR:
        return f"Türkçe Zemberek sözlüğü aktif değil ({ZEMBEREK_LOAD_ERROR}); zayıf sözlük alarmı bastırıldı."
    return "Türkçe Zemberek sözlüğü aktif değil; zayıf sözlük alarmı bastırıldı."


class SpellDictionary:
    def __init__(self, words=None, hunspell=None, zemberek=None, path=None):
        self.words = words or set()
        self.hunspell = hunspell
        self.zemberek = zemberek
        self.path = path

    def __bool__(self):
        return bool(self.words or self.hunspell or self.zemberek)

    def __contains__(self, word):
        return word in self.words

    def __iter__(self):
        return iter(self.words)

    def accepts(self, word):
        value = str(word).strip("'’")
        if not value:
            return True
        if value.casefold() in self.words:
            return True
        if self.hunspell:
            try:
                if self.hunspell.lookup(value) or self.hunspell.lookup(value.casefold()):
                    return True
            except Exception:
                pass
        if self.zemberek and self.zemberek.accepts(value):
            return True
        return False

    def suggest(self, word, limit=3):
        if self.zemberek:
            suggestions = self.zemberek.suggest(word, limit=limit)
            if suggestions:
                return suggestions
        if self.hunspell:
            try:
                return list(self.hunspell.suggest(word))[:limit]
            except Exception:
                return []
        return []

TECHNICAL_WORDS = {
    "latex", "tex", "pdf", "apa", "nws", "cpu", "matlab", "bsm", "exbsm",
    "efdb", "efdm", "grid", "mesh", "crank", "nicolson", "richtmyer",
    "newell", "whitehead", "segel", "gordon", "zeldovich", "rosenau", "burgers",
    "lyapunov", "poincare", "vonneumann", "neumann", "nümerik", "non-lineer",
    "lineer", "lineerleştirmeli", "semi-analitik", "galerkin", "kollokasyon",
    "kuadratik", "viskosite", "spline", "b-spline", "hopf-cole",
    "lax", "kantorovich", "hersch",
}
SPELLING_STOPWORDS_TR = {
    "olarak", "olduğu", "olduğunu", "olabilir", "bulunur", "bulunmaktadır",
    "gösterilir", "gösterilmiştir", "verilir", "verilmiştir", "kullanılır",
    "kullanılmıştır", "edilir", "edilmiştir", "elde", "sonuç", "sonuçlar",
    "yaklaşık", "çözüm", "çözümler", "fonksiyon", "denklem", "denklemi",
    "problem", "problemi", "şekil", "çizelge", "bölüm", "teorem", "lemma",
    "boyunca", "herhangi", "yoktur", "vardır", "değer", "değerler",
    "değerleri", "çalışma", "çalışmada", "çalışmanın", "çalışmasında",
    "yöntem", "yöntemi", "yöntemler", "yakınsaklık", "kararlılık",
}
SPELLING_STOPWORDS_EN = {
    "where", "therefore", "because", "section", "chapter", "figure", "table",
    "tables", "chapters", "equation", "equations", "problem", "problems",
    "solution", "solutions", "method", "methods", "analysis", "results",
    "theorem", "lemma", "finite", "difference", "numerical", "implicit",
    "explicit", "linear", "nonlinear", "linearized", "linearization",
    "conditions", "presented", "introduced", "considering", "obtained",
    "using", "evaluated", "consists", "graphs", "provides", "describes",
    "conclusions", "detail", "research", "references", "figures", "included",
    "clearly", "abbreviations", "forms", "symbols", "excluding", "keywords",
    "words", "reduced", "pages", "firstly", "review", "successfully",
    "additionally", "approximately", "investigated", "demonstrated",
    "scheme", "stability", "accuracy", "comparison", "particularly",
    "internally", "classical",
    "able", "about", "above", "according", "achieve", "achieved", "across",
    "addition", "additional", "after", "algorithm", "algorithms", "also",
    "among", "approach", "approaches", "appropriate", "arbitrary", "based",
    "basic", "before", "between", "brief", "calculated", "case", "cases",
    "coefficient", "coefficients", "common", "complete", "complex",
    "concept", "concepts", "condition", "convergence", "corresponding",
    "data", "defined", "definition", "definitions", "demonstrate",
    "dependent", "derived", "design", "determined", "different",
    "dimensional", "directly", "discussion", "during", "each", "effective",
    "example", "examples", "existing", "experimental", "following",
    "function", "functions", "general", "generally", "important",
    "initial", "internal", "interval", "known", "light", "main",
    "mathematical", "model", "models", "necessary", "needed", "normal",
    "order", "orders", "ordinary", "other", "parameter", "parameters",
    "partial", "physical", "preferred", "process", "proposed", "purpose",
    "regarding", "researcher", "researchers", "respectively", "same",
    "several", "should", "shown", "similar", "simple", "simulation",
    "source", "specific", "standard", "studies", "study", "such",
    "system", "systems", "technique", "techniques", "theoretical",
    "through", "throughout", "type", "used", "various", "well", "which",
    "while", "with", "without",
}
TURKISH_SUFFIXES = [
    "lerindeki", "larındaki", "lerimizden", "larımızdan", "lerimizin", "larımızın",
    "lerinizin", "larınızın", "lerini", "larını", "lerin", "ların",
    "larının", "lerinin", "larındaki", "lerindeki", "larından", "lerinden",
    "larında", "lerinde", "larımız", "lerimiz", "lardan", "lerden",
    "larla", "lerle", "lara", "lere", "ları", "leri", "larıdır", "leridir",
    "ılarak", "ilerek", "ularak", "ülerek", "arak", "erek",
    "maktır", "mektir", "maktadır", "mektedir",
    "mıştır", "miştir", "muştur", "müştür", "mış", "miş", "muş", "müş",
    "ıldı", "ildi", "uldu", "üldü", "ındı", "indi", "undu", "ündü",
    "ıldı", "ildi", "uldu", "üldü", "dı", "di", "du", "dü", "tı", "ti", "tu", "tü",
    "dığı", "diği", "duğu", "düğü", "tığı", "tiği", "tuğu", "tüğü",
    "dığını", "diğini", "duğunu", "düğünü", "tığını", "tiğini", "tuğunu", "tüğünü",
    "dığında", "diğinde", "duğunda", "düğünde", "tığında", "tiğinde", "tuğunda", "tüğünde",
    "ımız", "imiz", "umuz", "ümüz", "ının", "inin", "unun", "ünün",
    "ından", "inden", "undan", "ünden", "ında", "inde", "unda", "ünde",
    "dır", "dir", "dur", "dür", "tır", "tir", "tur", "tür",
    "dan", "den", "tan", "ten", "dır", "dir", "la", "le",
    "lar", "ler", "li", "lı", "lu", "lü", "siz", "sız", "suz", "süz",
    "mak", "mek", "ması", "mesi", "ma", "me", "ki", "de", "da", "nin", "nın",
    "yı", "yi", "yu", "yü", "nı", "ni", "nu", "nü", "ı", "i", "u", "ü", "a", "e",
]

VISIBLE_TEXT_COMMANDS = {
    "chapter",
    "section",
    "subsection",
    "subsubsection",
    "caption",
    "item",
    "textbf",
    "emph",
    "textit",
    "underline",
}

METADATA_TEXT_COMMANDS = {
    "tr": {
        "anabilimdali": {0},
        "programi": {0},
        "kucukbaslik": {0, 1, 2},
        "baslik": {0, 1, 2},
        "anahtarkelimeler": {0},
        "ithaf": {0},
    },
    "en": {
        "anabilimdali": {1},
        "programi": {1},
        "title": {0, 1, 2},
        "anahtarkelimeler": {1},
        "keywords": {0},
    },
}


def read_text(path):
    for encoding in ("utf-8-sig", "utf-8", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def default_review_settings():
    return {
        "user_words": {"tr": [], "en": []},
        "ignored_findings": [],
    }


def load_review_settings(workdir):
    settings = default_review_settings()
    path = Path(workdir) / REVIEW_SETTINGS_FILE
    if not path.exists():
        return settings
    try:
        data = json.loads(read_text(path))
    except (json.JSONDecodeError, OSError):
        return settings
    if isinstance(data.get("user_words"), dict):
        for lang in ("tr", "en"):
            words = data["user_words"].get(lang, [])
            if isinstance(words, list):
                settings["user_words"][lang] = sorted({str(word).strip() for word in words if str(word).strip()}, key=str.casefold)
    elif isinstance(data.get("user_words"), list):
        settings["user_words"]["tr"] = sorted({str(word).strip() for word in data["user_words"] if str(word).strip()}, key=str.casefold)
    ignored = data.get("ignored_findings", [])
    if isinstance(ignored, list):
        settings["ignored_findings"] = sorted({str(item).strip() for item in ignored if str(item).strip()})
    return settings


def save_review_settings(workdir, settings):
    path = Path(workdir) / REVIEW_SETTINGS_FILE
    normalized = default_review_settings()
    user_words = settings.get("user_words", {}) if isinstance(settings, dict) else {}
    for lang in ("tr", "en"):
        words = user_words.get(lang, []) if isinstance(user_words, dict) else []
        normalized["user_words"][lang] = sorted({str(word).strip() for word in words if str(word).strip()}, key=str.casefold)
    ignored = settings.get("ignored_findings", []) if isinstance(settings, dict) else []
    normalized["ignored_findings"] = sorted({str(item).strip() for item in ignored if str(item).strip()})
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def review_user_words(settings, lang):
    key = "en" if str(lang).lower().startswith("en") else "tr"
    words = settings.get("user_words", {}).get(key, []) if isinstance(settings, dict) else []
    return {str(word).casefold().strip("'’") for word in words if str(word).strip()}


def add_user_word(workdir, word, lang="tr"):
    clean = str(word or "").strip().strip("'’")
    if not clean:
        return False
    key = "en" if str(lang).lower().startswith("en") else "tr"
    settings = load_review_settings(workdir)
    words = settings.setdefault("user_words", {}).setdefault(key, [])
    existing = {str(item).casefold() for item in words}
    if clean.casefold() in existing:
        return False
    words.append(clean)
    save_review_settings(workdir, settings)
    return True


def issue_token_for_finding(raw, message):
    raw = str(raw or "")
    message = str(message or "")
    token_match = re.search(r"`([^`]+)`", message)
    if token_match:
        return token_match.group(1).casefold()
    if "Örnek/yer tutucu" in message or "Örnek/placeholder" in message:
        for token in PLACEHOLDERS:
            if token.casefold() in raw.casefold():
                return token.casefold()
    for pattern in issue_patterns_for_message(message):
        match = re.search(pattern, raw, re.I)
        if match:
            return match.group(0).casefold().strip()
    return message.casefold()


def finding_kind(message):
    value = re.sub(r"`[^`]+`", "`...`", str(message or ""))
    value = re.sub(r"\s+Öneri:\s*`...`", "", value)
    value = value.replace("yer tutucu", "placeholder").replace("Yer tutucu", "Placeholder")
    return value.casefold().strip()


def finding_ignore_key(rel, number, message, raw):
    return "|".join([
        str(rel).replace("\\", "/"),
        str(int(number)),
        finding_kind(message),
        issue_token_for_finding(raw, message),
    ])


def add_ignored_finding(workdir, rel, number, message, raw):
    settings = load_review_settings(workdir)
    ignored = settings.setdefault("ignored_findings", [])
    key = finding_ignore_key(rel, number, message, raw)
    if key in ignored:
        return False
    ignored.append(key)
    save_review_settings(workdir, settings)
    return True


def finding_category(message):
    message = str(message or "")
    if "Kılavuz yazım kuralı" in message:
        return "Kılavuz yazım kuralı"
    if "TeX ön kontrol" in message:
        return "TeX ön kontrol"
    if "PDF Unicode" in message:
        return "PDF karakter bozulması"
    if "yer tutucu" in message or "placeholder" in message:
        return "Yer tutucu"
    if "Sözlükte bulunmayan" in message or "Bitişik yazılmış" in message or "Sayı/sözcük" in message:
        return "Sözlük uyarıları"
    if "Noktalama" in message or "yinelenen" in message or "Cümle çok uzun" in message:
        return "Noktalama"
    if "karakter bozulması" in message:
        return "İçerik"
    return "Diğer"


def finding_stable_key(rel, number, message, raw):
    return finding_ignore_key(rel, number, message, raw)


def find_dictionary(lang, workdir=None):
    lang = "en_US" if str(lang).lower().startswith("en") else "tr_TR"
    candidates = []
    if workdir:
        workdir = Path(workdir)
        candidates.extend([
            workdir / "system" / "dicts" / f"{lang}.dic",
            workdir / "dicts" / f"{lang}.dic",
            workdir.parent / "system" / "dicts" / f"{lang}.dic",
        ])
    candidates.extend([
        Path(r"C:\Program Files\LyX 2.5\Resources\dicts") / f"{lang}.dic",
        Path(r"C:\Program Files\LyX 2.4\Resources\dicts") / f"{lang}.dic",
        Path(r"C:\Program Files\Common Files\Adobe\Acrobat\DC\Linguistics\Providers\Plugins2\AdobeHunspellPlugin\Dictionaries") / lang / f"{lang}.dic",
    ])
    for root in (Path(r"C:\Program Files"), Path(r"C:\Program Files (x86)")):
        if root.exists():
            try:
                for path in root.glob(f"**/{lang}.dic"):
                    candidates.append(path)
            except OSError:
                pass
    for path in candidates:
        if path.exists():
            return path
    return None


def load_dictionary(lang, workdir=None):
    key = "en" if str(lang).lower().startswith("en") else "tr"
    cache_key = (key, str(Path(workdir).resolve()) if workdir else "")
    if cache_key in DICTIONARY_CACHE:
        return DICTIONARY_CACHE[cache_key]
    path = find_dictionary("en_US" if key == "en" else "tr_TR", workdir=workdir)
    words = set()
    hunspell = None
    zemberek = load_zemberek_engine() if key == "tr" else None
    if path:
        aff_path = path.with_suffix(".aff")
        if aff_path.exists() and os.environ.get("INONU_USE_SPYLLS_HUNSPELL") != "0":
            try:
                from spylls.hunspell import Dictionary as HunspellDictionary
                hunspell = HunspellDictionary.from_files(str(path.with_suffix("")))
            except Exception:
                hunspell = None
        for raw in read_text(path).splitlines()[1:]:
            word = raw.split("/", 1)[0].strip().casefold()
            word = re.sub(r"[^a-zçğıöşüâîûäëïöüéèêôA-ZÇĞİÖŞÜÂÎÛÄËÏÖÜÉÈÊÔ'-]", "", word).casefold()
            if word:
                words.add(word)
    dictionary = SpellDictionary(words=words, hunspell=hunspell, zemberek=zemberek, path=path)
    DICTIONARY_CACHE[cache_key] = dictionary
    return dictionary


def dictionary_accepts(word, dictionary, lang):
    lower = word.casefold().strip("'’")
    if len(lower) < 4 or lower in TECHNICAL_WORDS:
        return True
    if str(lang).lower().startswith("en") and lower in SPELLING_STOPWORDS_EN:
        return True
    if any(char.isdigit() for char in lower) or re.search(r"[A-ZÇĞİÖŞÜ]{2,}", word):
        return True
    if "-" in lower:
        parts = [part for part in re.split(r"[-‐‑‒–—]", lower) if part]
        if parts and all(dictionary_accepts(part, dictionary, lang) for part in parts):
            return True
    cache_key = (id(dictionary), lower)
    if cache_key in SPELL_CHECK_CACHE:
        return SPELL_CHECK_CACHE[cache_key]
    if hasattr(dictionary, "accepts") and dictionary.accepts(word):
        SPELL_CHECK_CACHE[cache_key] = True
        return True
    if lower in dictionary:
        SPELL_CHECK_CACHE[cache_key] = True
        return True
    if str(lang).lower().startswith("en"):
        candidates = {lower}
        if lower.endswith("ies") and len(lower) > 4:
            candidates.add(lower[:-3] + "y")
        if lower.endswith("es") and len(lower) > 3:
            candidates.add(lower[:-2])
            candidates.add(lower[:-1])
        if lower.endswith("s") and len(lower) > 3:
            candidates.add(lower[:-1])
        if lower.endswith("ied") and len(lower) > 4:
            candidates.add(lower[:-3] + "y")
        if lower.endswith("ed") and len(lower) > 4:
            candidates.add(lower[:-2])
            candidates.add(lower[:-1])
        if lower.endswith("ing") and len(lower) > 5:
            candidates.add(lower[:-3])
            candidates.add(lower[:-3] + "e")
        for suffix in ("ingly", "edly", "ally", "ation", "ations", "ment", "ments", "ness", "less", "ful", "ers", "er", "ly"):
            if lower.endswith(suffix) and len(lower) > len(suffix) + 3:
                stem = lower[:-len(suffix)]
                candidates.add(stem)
                if suffix in {"er", "ers"}:
                    candidates.add(stem + "e")
                elif suffix == "ally":
                    candidates.add(stem + "al")
        if any(candidate in dictionary or candidate in SPELLING_STOPWORDS_EN for candidate in candidates):
            SPELL_CHECK_CACHE[cache_key] = True
            return True
    if not str(lang).lower().startswith("en") and getattr(dictionary, "zemberek", None):
        candidates = dictionary.zemberek.deascii_candidates(lower, max_candidates=32)
        if candidates:
            suggestion = candidates[0]
            if suggestion.casefold() != lower and suggestion_is_confident(lower, suggestion, lang):
                SPELL_CHECK_CACHE[cache_key] = False
                return False
    if not str(lang).lower().startswith("en"):
        ascii_lower = lower.replace("â", "a").replace("î", "i").replace("û", "u")
        if ascii_lower in dictionary:
            SPELL_CHECK_CACHE[cache_key] = True
            return True
        if getattr(dictionary, "zemberek", None):
            SPELL_CHECK_CACHE[cache_key] = False
            return False
        stems = {lower, ascii_lower}
        for _depth in range(3):
            new_stems = set()
            for candidate in stems:
                for suffix in TURKISH_SUFFIXES:
                    if candidate.endswith(suffix) and len(candidate) - len(suffix) >= 3:
                        stem = candidate[:-len(suffix)]
                        new_stems.update({stem, stem + "k", stem + "ğ", stem + "m"})
            if any(stem in dictionary or stem in TECHNICAL_WORDS for stem in new_stems):
                SPELL_CHECK_CACHE[cache_key] = True
                return True
            stems.update(new_stems)
    SPELL_CHECK_CACHE[cache_key] = False
    return False


def turkish_ascii_key(value):
    value = str(value).casefold().translate(str.maketrans({
        "\u00e7": "c", "\u011f": "g", "\u0131": "i", "\u00f6": "o", "\u015f": "s", "\u00fc": "u",
        "\u00e2": "a", "\u00ee": "i", "\u00fb": "u",
    }))
    value = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in value if not unicodedata.combining(ch))


def edit_distance_at_most_one(left, right):
    if abs(len(left) - len(right)) > 1:
        return False
    i = j = edits = 0
    while i < len(left) and j < len(right):
        if left[i] == right[j]:
            i += 1
            j += 1
            continue
        edits += 1
        if edits > 1:
            return False
        if len(left) == len(right):
            i += 1
            j += 1
        elif len(left) > len(right):
            i += 1
        else:
            j += 1
    return edits + (len(left) - i) + (len(right) - j) <= 1


def suggestion_quality(word, suggestion, lang):
    if not suggestion:
        return None
    source = str(word).casefold().strip("'’")
    target = str(suggestion).casefold().strip("'’")
    if source == target or abs(len(source) - len(target)) > 2:
        return None
    source_key = turkish_ascii_key(source)
    target_key = turkish_ascii_key(target)
    if source_key[:2] != target_key[:2]:
        return None
    is_english = str(lang).lower().startswith("en")
    if source_key == target_key:
        return 0
    if source_key.startswith(target_key) or target_key.startswith(source_key):
        return 1
    if abs(len(source_key) - len(target_key)) == 1 and edit_distance_at_most_one(source_key, target_key):
        return 2
    ratio = difflib.SequenceMatcher(None, source_key, target_key).ratio()
    if is_english and ratio >= 0.93:
        return 3
    return None


def choose_best_suggestion(word, suggestions, lang):
    ranked = []
    for suggestion in suggestions:
        quality = suggestion_quality(word, suggestion, lang)
        if quality is not None:
            ranked.append((quality, len(str(suggestion)), str(suggestion)))
    if not ranked:
        return None
    ranked.sort()
    best_quality = ranked[0][0]
    best_targets = {turkish_ascii_key(item[2]) for item in ranked if item[0] == best_quality}
    if best_quality > 0 and len(best_targets) > 1:
        return None
    return ranked[0][2]


def spelling_suggestion(word, dictionary, cutoff=0.95, lang=None):
    lower = word.casefold().strip("'’")
    if len(lower) < 4 or not dictionary:
        return None
    lang_key = "en" if str(lang).lower().startswith("en") else "tr"
    suggestion_cache_key = (id(dictionary), lang_key, lower)
    if suggestion_cache_key in SPELL_SUGGESTION_CACHE:
        return SPELL_SUGGESTION_CACHE[suggestion_cache_key]
    if hasattr(dictionary, "suggest"):
        suggestions = dictionary.suggest(word, limit=3)
        if suggestions:
            suggestion = choose_best_suggestion(word, suggestions, lang_key)
            if suggestion:
                SPELL_SUGGESTION_CACHE[suggestion_cache_key] = suggestion
                return suggestion
    first = lower[:1]
    index_cache_key = id(dictionary)
    index = SUGGESTION_INDEX_CACHE.get(index_cache_key)
    if index is None:
        index = {}
        for item in dictionary:
            if item:
                index.setdefault((item[:1], len(item)), []).append(item)
        SUGGESTION_INDEX_CACHE[index_cache_key] = index
    candidates = []
    for size in range(len(lower) - 1, len(lower) + 2):
        candidates.extend(index.get((first, size), []))
    candidates.extend(word for word in SPELLING_STOPWORDS_TR if word[:1] == first and abs(len(word) - len(lower)) <= 2)
    candidates.extend(word for word in SPELLING_STOPWORDS_EN if word[:1] == first and abs(len(word) - len(lower)) <= 2)
    matches = difflib.get_close_matches(lower, candidates, n=1, cutoff=cutoff)
    suggestion = matches[0] if matches else None
    if suggestion and not suggestion_is_confident(word, suggestion, lang_key):
        suggestion = None
    SPELL_SUGGESTION_CACHE[suggestion_cache_key] = suggestion
    return suggestion


def suggestion_is_confident(word, suggestion, lang):
    return suggestion_quality(word, suggestion, lang) is not None


def latex_text_to_unicode(line):
    value = line
    value = value.replace("``", " ").replace("''", " ")
    replacements = [
        (r'\\i\{\}', "ı"),
        (r'\\i\s+(?=[.,;:!?])', "ı"),
        (r'\\i\s+(?=[A-Za-zÇĞİÖŞÜçğıöşü])', "ı"),
        (r'\\i', "ı"),
        (r'\\"\{a\}', "ä"),
        (r'\\"\{A\}', "Ä"),
        (r'\\"\{o\}', "ö"),
        (r'\\"\{O\}', "Ö"),
        (r'\\"\{u\}', "ü"),
        (r'\\"\{U\}', "Ü"),
        (r'\\c\{c\}', "ç"),
        (r'\\c\{C\}', "Ç"),
        (r'\\c\{s\}', "ş"),
        (r'\\c\{S\}', "Ş"),
        (r'\\u\{g\}', "ğ"),
        (r'\\u\{G\}', "Ğ"),
    ]
    for pattern, replacement in replacements:
        value = re.sub(pattern, replacement, value)
    value = value.replace(r"\ ", " ")
    value = re.sub(r'\\["`\'^~=.]\{([A-Za-z])\}', r"\1", value)
    return value


def strip_latex(line):
    line = latex_text_to_unicode(line)
    line = re.sub(r"%.*", "", line)
    line = re.sub(r"\$[^$]*\$", " ", line)
    line = re.sub(r"\\label\{[^{}]*\}", " ", line)
    line = re.sub(r"\\(?:chapter|section|subsection|subsubsection)\*?\{([^{}]*)\}", r"\1", line)
    line = re.sub(r"\\(?:textbf|emph|textit|underline|caption)\*?\{([^{}]*)\}", r"\1", line)
    line = re.sub(r"\\(?:cite[tp]?|parencite|textcite|autocite)\{[^{}]*\}", " __CITATION__ ", line)
    line = re.sub(r"\\ref\{[^{}]*\}", " __REF__ ", line)
    line = line.replace("~", " ")
    line = re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?", " ", line)
    line = line.replace("{", " ").replace("}", " ")
    return re.sub(r"\s+", " ", line).strip()


def has_source_space_before_punctuation(raw):
    code = re.sub(r"(?<!\\)%.*", "", raw)
    return bool(re.search(r"\s+([,.;:!?])", code))


def spelling_language_for_path(rel, default_language):
    name = Path(rel).name.lower()
    if name in {"summary.tex", "summary_body.tex", "abstract.tex", "abstract_body.tex"}:
        return "en"
    if name == "ozet.tex":
        return "tr"
    return default_language


def read_decimal_separator(workdir, language="tr"):
    tex_path = Path(workdir) / "tez.tex"
    if tex_path.exists():
        text = read_text(tex_path)
        match = re.search(r"\\ondalikayirici\s*\{([^{}]+)\}", text)
        if match:
            value = match.group(1).strip().casefold()
            if value in {"nokta", "point", "dot", "."}:
                return "nokta"
            if value in {"virgul", "virgül", "comma", ","}:
                return "virgul"
    return "nokta" if str(language).lower().startswith("en") else "virgul"


def is_structural_latex(raw):
    stripped = raw.strip()
    return stripped.startswith((
        r"\begin{",
        r"\end{",
        r"\includegraphics",
        r"\label{",
        r"\ref{",
        r"\pageref{",
        r"\captionsetup",
        r"\bibliographystyle",
        r"\bibliography",
    ))


def is_latex_control_line(raw):
    stripped = raw.strip()
    if not stripped or stripped.startswith("%"):
        return True
    if stripped.startswith((
        r"\documentclass",
        r"\usepackage",
        r"\RequirePackage",
        r"\input",
        r"\include",
        r"\includedocskip",
        r"\graphicspath",
        r"\DeclareGraphicsExtensions",
        r"\newtheorem",
        r"\theoremstyle",
        r"\providecommand",
        r"\setcounter",
        r"\renewcommand",
        r"\newcommand",
        r"\bibliographystyle",
        r"\bibliography",
        r"\begin{document}",
        r"\end{document}",
    )):
        return True
    command = re.match(r"\\([A-Za-z]+)\*?", stripped)
    return bool(command and command.group(1) not in VISIBLE_TEXT_COMMANDS)


def parse_latex_command_groups(lines, start_index):
    first_line = lines[start_index]
    match = re.match(r"\s*\\([A-Za-z]+)\*?", first_line)
    if not match:
        return "", [], start_index
    command = match.group(1)
    groups = []
    current = []
    depth = 0
    group_start_line = start_index + 1
    line_index = start_index
    position = match.end()
    while line_index < len(lines):
        line = lines[line_index]
        if line_index != start_index:
            if depth == 0 and groups and not line.lstrip().startswith("{"):
                break
            position = 0
        while position < len(line):
            char = line[position]
            if char == "%" and (position == 0 or line[position - 1] != "\\"):
                break
            if char == "{":
                if depth == 0:
                    current = []
                    group_start_line = line_index + 1
                else:
                    current.append(char)
                depth += 1
            elif char == "}":
                if depth > 0:
                    depth -= 1
                    if depth == 0:
                        groups.append((group_start_line, "".join(current)))
                    else:
                        current.append(char)
            else:
                if depth > 0:
                    current.append(char)
            position += 1
        if depth > 0:
            current.append(" ")
        if depth == 0 and groups:
            next_line = lines[line_index + 1] if line_index + 1 < len(lines) else ""
            if not next_line.lstrip().startswith("{"):
                break
        line_index += 1
    return command, groups, line_index


def iter_metadata_lines(workdir, language="tr"):
    tex_path = workdir / "tez.tex"
    if not tex_path.exists():
        return
    lang_key = "en" if str(language).lower().startswith("en") else "tr"
    command_map = METADATA_TEXT_COMMANDS[lang_key]
    lines = read_text(tex_path).splitlines()
    line_index = 0
    while line_index < len(lines):
        raw = lines[line_index]
        if r"\begin{document}" in raw:
            break
        match = re.match(r"\s*\\([A-Za-z]+)\*?", raw)
        if not match:
            line_index += 1
            continue
        command = match.group(1)
        if command not in command_map:
            line_index += 1
            continue
        _command, groups, consumed_index = parse_latex_command_groups(lines, line_index)
        for group_index, (group_line, content) in enumerate(groups):
            if group_index in command_map[command]:
                text = strip_latex(content)
                if text:
                    yield tex_path, group_line, f"\\{command}{{{content}}}", text
        line_index = max(consumed_index + 1, line_index + 1)


def normalized_file_scope(only_files):
    if not only_files:
        return None
    return {Path(item).as_posix() for item in only_files}


def iter_tex_lines(workdir, language="tr", only_files=None):
    file_scope = normalized_file_scope(only_files)
    if file_scope is None or "tez.tex" in file_scope:
        yield from iter_metadata_lines(workdir, language=language)
    math_envs = {"equation", "align", "alignat", "gather", "multline", "eqnarray", "split", "cases"}
    non_prose_envs = {
        "table", "tabular", "tabularx", "longtable", "array",
        "figure", "center", "minipage", "picture", "tikzpicture",
    }
    for name in TEXT_FILES:
        if name == "summary.tex" and (workdir / "abstract.tex").exists():
            continue
        if file_scope is not None and Path(name).as_posix() not in file_scope:
            continue
        path = workdir / name
        if path.exists():
            in_math = False
            non_prose_stack = []
            for number, raw in enumerate(read_text(path).splitlines(), start=1):
                stripped = raw.strip()
                begin_match = re.match(r"\\begin\{([^{}*]+)\*?\}", stripped)
                end_match = re.match(r"\\end\{([^{}*]+)\*?\}", stripped)
                if begin_match and begin_match.group(1) in non_prose_envs:
                    non_prose_stack.append(begin_match.group(1))
                    continue
                if end_match and non_prose_stack and end_match.group(1) == non_prose_stack[-1]:
                    non_prose_stack.pop()
                    continue
                if non_prose_stack:
                    continue
                if begin_match and begin_match.group(1) in math_envs:
                    in_math = True
                    continue
                if end_match and end_match.group(1) in math_envs:
                    in_math = False
                    continue
                if in_math:
                    continue
                if is_latex_control_line(raw):
                    continue
                if re.search(r"[_^&]|\\(?:equiv|notag|quad|frac|sum|int|left|right|cdot|times|text)\b", raw):
                    continue
                if re.search(r"\$|<\s*\w|\\triangle|\\dot|\\frac", raw):
                    continue
                text = strip_latex(raw)
                if text:
                    yield path, number, raw, text


def sentence_warnings(text):
    parts = re.split(r"(?<=[.!?])\s+", text)
    warnings = []
    for sentence in parts:
        words = re.findall(r"\b[\wçğıöşüÇĞİÖŞÜ]+\b", sentence)
        if len(words) > 45:
            warnings.append("Cümle çok uzun görünüyor; iki cümleye bölmek okunabilirliği artırabilir.")
    return warnings


def looks_like_legacy_wrapped_turkish_line(raw, text):
    raw = str(raw or "")
    text = str(text or "")
    if not re.search(r"\\(?:i|c\{|u\{|\"|\.)", raw):
        return False
    stripped_raw = raw.strip()
    stripped_text = text.strip()
    if not stripped_text:
        return False
    if stripped_raw.endswith(("\\i", r"\i\\", "%")):
        return True
    if re.match(r"^[a-zçğıöşüâîû]{2,}", stripped_text) and not re.search(r"[.!?:;]\s*$", stripped_text):
        return True
    words = re.findall(r"\b[\wçğıöşüÇĞİÖŞÜâîûÂÎÛ'-]{3,}\b", stripped_text)
    if words and words[-1].casefold().endswith(("ı", "i", "u", "ü")) and stripped_raw.endswith(("\\i", r"\i\\", '\\"{u}', '\\"{o}')):
        return True
    return False


def unescaped_percent_at_line_end(raw):
    return bool(re.search(r"(?<!\\)%\s*$", raw or ""))


def looks_like_wrapped_word_continuation(raw, text, previous_raw=None, previous_number=None, number=None):
    raw = str(raw or "")
    text = str(text or "")
    previous_raw = str(previous_raw or "")
    first_word = re.match(r"\s*([a-zçğıöşüâîû][\wçğıöşüâîû'-]{1,})\b", text)
    if not first_word:
        return False
    if previous_number is not None and number is not None and int(number) != int(previous_number) + 1:
        return False
    if not previous_raw.strip():
        return False
    if re.search(r"[.!?:;]\s*(?:%.*)?$", previous_raw.strip()) and not unescaped_percent_at_line_end(previous_raw):
        return False
    current_starts_as_suffix = first_word.group(1).casefold().startswith((
        "m", "n", "r", "s", "t", "l", "y", "d", "k",
        "ması", "mesi", "mış", "miş", "ndan", "nden", "lar", "ler",
    ))
    previous_has_tex_accent = bool(re.search(r"\\(?:i|c\{|u\{|\"|\.)", previous_raw))
    current_has_tex_accent = bool(re.search(r"\\(?:i|c\{|u\{|\"|\.)", raw))
    if unescaped_percent_at_line_end(previous_raw):
        return current_starts_as_suffix or previous_has_tex_accent or current_has_tex_accent
    if previous_has_tex_accent and (current_has_tex_accent or current_starts_as_suffix):
        return True
    previous_tail = strip_latex(previous_raw).strip()
    if previous_tail and re.search(r"[a-zçğıöşüâîû]$", previous_tail) and current_starts_as_suffix and current_has_tex_accent:
        return True
    return False


def is_heading_source_line(raw):
    return bool(re.search(r"\\(?:chapter|section|subsection|subsubsection)\*?\{", raw or ""))


def latex_command_contents(value, command):
    contents = []
    pattern = "\\" + command
    index = 0
    while True:
        start = str(value or "").find(pattern, index)
        if start < 0:
            break
        brace = str(value or "").find("{", start + len(pattern))
        if brace < 0:
            break
        depth = 0
        current = []
        pos = brace
        while pos < len(value):
            char = value[pos]
            if char == "{" and (pos == 0 or value[pos - 1] != "\\"):
                if depth > 0:
                    current.append(char)
                depth += 1
            elif char == "}" and (pos == 0 or value[pos - 1] != "\\"):
                depth -= 1
                if depth == 0:
                    contents.append("".join(current))
                    pos += 1
                    break
                current.append(char)
            else:
                if depth > 0:
                    current.append(char)
            pos += 1
        index = max(pos, start + len(pattern))
    return contents


def guideline_writing_rule_warnings(raw, text, rel=None, decimal_separator="virgul"):
    warnings = []
    source = re.sub(r"(?<!\\)%.*", "", raw or "")
    visible = text or ""
    punctuation_text = re.sub(r"\s*__CITATION__\s*(?=[,.;:!?])", "", visible)
    punctuation_text = re.sub(r"\s*__CITATION__\s*", " ", punctuation_text)
    punctuation_text = re.sub(r"\s*__REF__\s*(?=[,.;:!?])", "", punctuation_text)
    punctuation_text = re.sub(r"\s*__REF__\s*", " ", punctuation_text)
    reference = "Referans: tez yazım kılavuzu metin biçimi, noktalama, sayı ve birim kullanımı kuralları."
    line_language = spelling_language_for_path(rel or "", "tr")
    is_english_line = str(line_language).lower().startswith("en")
    is_metadata_line = Path(rel or "").name == "tez.tex"

    def add(message, suggestion):
        warnings.append(f"Kılavuz yazım kuralı: {message} {reference} Öneri: {suggestion}")

    if re.search(r"\\(?:textcolor|color|hl)\b", source):
        add(
            "Metin içinde renkli yazı, vurgulama veya işaretleme kullanılmış olabilir.",
            "Bilimsel içerik metninde rengi kaldırın; normal siyah metin kullanın.",
        )
    if re.search(r"\\underline\s*\{", source):
        add(
            "Altı çizili yazı tercih edilmemelidir.",
            r"\underline{...} yerine normal metin kullanın; gerekiyorsa terimi italik yazın.",
        )

    if not is_english_line and not is_metadata_line:
        source_without_italic = re.sub(r"\\(?:textit|emph)\s*\{[^{}]*\}", " ", source)
        for pattern, _base_phrase in FOREIGN_TECHNICAL_PHRASE_PATTERNS_TR:
            visible_match = pattern.search(visible)
            source_match = pattern.search(source_without_italic)
            if visible_match and source_match:
                phrase = visible_match.group(0)
                add(
                    f"Türkçe metinde yabancı teknik terim italik yazılmalı olabilir: `{phrase}`.",
                    rf"`\textit{{{phrase}}}` biçimini kullanın veya Türkçe karşılığı varsa onu tercih edin.",
                )
    def allowed_bold_label_line(value):
        matches = latex_command_contents(value or "", "textbf")
        matches = [item for item in matches if len(item) <= 120]
        if not matches:
            return False
        allowed_labels = {
            "amaç:", "materyal ve metot:", "bulgular:", "sonuç:", "anahtar kelimeler:",
            "aim:", "material and method:", "results:", "conclusion:", "keywords:",
            "adı soyadı:", "ad-soyad:", "doğum yeri ve yılı:", "e-posta:", "öğrenim durumu:",
            "öğrenim durumu", "lisans:", "lisans", "yüksek lisans:", "yüksek lisans",
            "mesleki deneyimler:", "mesleki deneyimler", "mesleki deneyimler ve ödüller",
            "tezden türetilen yayınlar, sunumlar ve patentler",
            "diğer yayınlar, sunumlar ve patentler",
        }
        theorem_like = {"problem", "problem:", "teorem", "teorem:", "lemma", "lemma:", "önerme", "önerme:", "sonuç", "sonuç:", "tanım", "tanım:", "kanıt", "kanıt:", "proof", "proof:", "remark", "remark:"}
        allowed_ascii = {turkish_ascii_key(label) for label in allowed_labels | theorem_like}
        for label in matches:
            normalized = strip_latex(label).strip().casefold()
            normalized = re.sub(r"\s+", " ", normalized)
            normalized_ascii = turkish_ascii_key(normalized)
            if normalized in allowed_labels or normalized_ascii in allowed_ascii:
                continue
            if normalized.isdigit():
                continue
            if re.match(r"^(problem|teorem|lemma|önerme|sonuç|tanım|kanıt|proof|remark)\s*\d*\.?:?$", normalized) or re.match(r"^(problem|teorem|lemma|onerme|sonuc|tanim|kanit|proof|remark)\s*\d*\.?:?$", normalized_ascii):
                continue
            return False
        return True

    if re.search(r"\\textbf\s*\{", source) and not is_heading_source_line(source) and not allowed_bold_label_line(source):
        add(
            "Kalın yazı başlıklar dışında vurgu amacıyla kullanılmamalıdır.",
            r"Metin içindeki \textbf{...} kullanımını kaldırın veya gerçekten başlıksa başlık komutuna taşıyın.",
        )

    if rel and re.match(r"bolum\d+\.tex$", Path(rel).name, re.I) and MANUAL_VERTICAL_SPACE_RE.search(source):
        add(
            "Ana metinde manuel dikey boşluk komutu kullanılmış olabilir.",
            r"Paragraf ve başlık boşluklarını şablona bırakın; zorunlu değilse \bigskip, \medskip veya \smallskip komutunu kaldırın.",
        )

    if re.search(r"\\%\s+\d", source) or re.search(r"%\s+\d", visible):
        add(
            "Yüzde işareti ile sayı arasında boşluk bırakılmış.",
            r"\% 15 yerine \%15 yazın.",
        )
    if re.search(r"\d+\s+%", visible) or re.search(r"\d+\s+\\%", source):
        add(
            "Yüzde işareti sayının hemen önünde olmalıdır.",
            r"15 \% yerine \%15 yazın.",
        )

    heading_number = re.match(r"\s*\d+(?:\.\d+)+\s+\S+", visible or "")
    likely_plain_heading_number = False
    if heading_number:
        rest = re.sub(r"^\s*\d+(?:\.\d+)+\s+", "", visible or "").strip()
        words = re.findall(r"\b[\wçğıöşüÇĞİÖŞÜâîûÂÎÛ'-]+\b", rest)
        likely_plain_heading_number = bool(
            rest
            and len(words) <= 10
            and not re.search(r"[.!?]\s*$", rest)
            and rest[:1].isupper()
        )
    decimal_dot = re.search(r"(?<![\w\\])\d+\.\d+(?![\w])", visible)
    decimal_comma = re.search(r"(?<![\w\\])\d+,\d+(?![\w])", visible)
    if decimal_separator == "virgul" and decimal_dot and not is_english_line and not ((is_heading_source_line(source) or likely_plain_heading_number) and heading_number and decimal_dot.start() == heading_number.start()):
        token = decimal_dot.group(0)
        add(
            f"Ondalık sayı nokta ile yazılmış olabilir: `{token}`.",
            f"Seçili ondalık ayırıcı virgül olduğu için `{token.replace('.', ',')}` biçimini kullanın; denklem/kod bağlamıysa kontrol edin.",
        )
    if decimal_separator == "nokta" and decimal_comma and not ((is_heading_source_line(source) or likely_plain_heading_number) and heading_number and decimal_comma.start() == heading_number.start()):
        token = decimal_comma.group(0)
        add(
            f"Ondalık sayı virgül ile yazılmış olabilir: `{token}`.",
            f"Seçili ondalık ayırıcı nokta olduğu için `{token.replace(',', '.')}` biçimini kullanın; denklem/kod bağlamıysa kontrol edin.",
        )

    if re.search(r"(?<!\d)[,.;:!?](?=[^\s,.;:!?])", punctuation_text):
        add(
            "Noktalama işaretinden sonra boşluk olmayabilir.",
            "Virgül, nokta, noktalı virgül, iki nokta ve soru işaretinden sonra bir boşluk bırakın.",
        )
    if re.search(r"\s+[,.;:!?]", punctuation_text):
        add(
            "Noktalama işaretinden önce boşluk bırakılmış olabilir.",
            "Noktalama işaretini önceki sözcüğe bitişik yazın.",
        )

    unit_pattern = r"(?<![\w\\])\d+(?:[,.]\d+)?(cm|mm|m|km|kg|g|mg|L|mL|ml|s|dk|sn|Hz|kHz|MHz|Pa|kPa|MPa|N|J|W|V|A)\b"
    unit_match = re.search(unit_pattern, visible)
    if unit_match:
        add(
            f"Sayı ile birim sembolü arasında boşluk eksik olabilir: `{unit_match.group(0)}`.",
            f"`{unit_match.group(0)}` yerine sayı ile birim arasına boşluk koyun.",
        )
    if re.search(r"\d+\s+°\s*C|\d+°\s+C|\d+\s+°C", visible):
        add(
            "Derece/sıcaklık gösteriminde gereksiz boşluk olabilir.",
            "37°C biçimini kullanın; yüzde ve derece işaretlerinde boşluk bırakmayın.",
        )

    if not is_heading_source_line(source) and not is_metadata_line:
        uppercase_words = [word for word in re.findall(r"\b[A-ZÇĞİÖŞÜ]{4,}\b", visible) if word not in {"APA", "SI", "DNA", "RNA", "PDF", "YÖK"}]
        if len(uppercase_words) >= 4:
            add(
                "Başlık dışında tamamı büyük harfli metin kullanılmış olabilir.",
                "Kısaltmalar dışında gövde metninde normal büyük/küçük harf düzeni kullanın.",
            )
    return warnings


def spelling_warnings(text, dictionary, lang, allow_uppercase_suggestions=False, personal_words=None, skip_first_word=False):
    if not dictionary:
        return []
    warnings = []
    seen = set()
    is_english = str(lang).lower().startswith("en")
    stopwords = SPELLING_STOPWORDS_EN if is_english else SPELLING_STOPWORDS_TR
    personal_words = personal_words or set()
    if not is_english and not getattr(dictionary, "zemberek", None) and not getattr(dictionary, "hunspell", None):
        return []
    number_prefixes = ("bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz", "on")
    words = re.findall(r"\b[\wçğıöşüÇĞİÖŞÜâîûÂÎÛ'-]{5,}\b", text)
    if skip_first_word and words:
        words = words[1:]
    for word in words:
        clean = word.strip("'’")
        lower = clean.casefold()
        if lower in seen or lower in stopwords or lower in personal_words:
            continue
        if not is_english and clean[:1].isupper():
            continue
        seen.add(lower)
        if dictionary_accepts(clean, dictionary, lang):
            continue
        if not is_english:
            if lower.endswith(("ve", "ile")):
                for suffix in ("ve", "ile"):
                    stem = lower[:-len(suffix)]
                    if len(stem) >= 5 and dictionary_accepts(stem, dictionary, lang):
                        warnings.append(f"Bitişik yazılmış sözcük olabilir: `{clean}`")
                        break
                if warnings and warnings[-1].endswith(f"`{clean}`"):
                    if len(warnings) >= MAX_SPELLING_WARNINGS_PER_LINE:
                        break
                    continue
            for prefix in number_prefixes:
                if lower.startswith(prefix) and len(lower) > len(prefix) + 3:
                    rest = lower[len(prefix):]
                    if len(rest) >= 4 and rest in dictionary:
                        warnings.append(f"Sayı/sözcük birleşmiş olabilir: `{clean}`")
                        break
            if warnings and warnings[-1].endswith(f"`{clean}`"):
                if len(warnings) >= MAX_SPELLING_WARNINGS_PER_LINE:
                    break
                continue
        suggestion = None
        if allow_uppercase_suggestions or not clean[:1].isupper():
            suggestion = spelling_suggestion(clean, dictionary, cutoff=0.96 if not is_english else 0.93, lang=lang)
        if suggestion_is_confident(clean, suggestion, lang):
            warnings.append(f"Sözlükte bulunmayan sözcük olabilir: `{clean}`. Öneri: `{suggestion}`")
        else:
            warnings.append(f"Sözlükte bulunmayan sözcük olabilir: `{clean}`.")
        if len(warnings) >= MAX_SPELLING_WARNINGS_PER_LINE:
            break
    return warnings


def analyze(workdir, language="tr", only_files=None):
    findings = []
    text_export = []
    dictionary_cache = {}
    decimal_separator = read_decimal_separator(workdir, language=language)
    settings = load_review_settings(workdir)
    ignored_findings = set(settings.get("ignored_findings", []))
    previous_prose = {}

    def append_finding(rel, number, message, raw):
        if finding_ignore_key(rel, number, message, raw) in ignored_findings:
            return
        findings.append((rel, number, message, raw))

    for path, number, raw, text in iter_tex_lines(workdir, language=language, only_files=only_files):
        rel = path.relative_to(workdir)
        previous_number, previous_raw = previous_prose.get(path, (None, None))
        skip_first_spelling_word = looks_like_wrapped_word_continuation(
            raw,
            text,
            previous_raw=previous_raw,
            previous_number=previous_number,
            number=number,
        )
        if (
            not skip_first_spelling_word
            and re.match(r"\s*[a-zçğıöşüâîû][\wçğıöşüâîû'-]{1,}\b", text or "")
            and re.search(r"\\(?:i|c\{|u\{|\"|\.)", raw or "")
        ):
            skip_first_spelling_word = True
        if (
            not skip_first_spelling_word
            and re.match(r"\s*[lmnrstdk][\wçğıöşüâîû'-]{3,}\b", text or "", re.I)
            and MANUAL_VERTICAL_SPACE_RE.search(raw or "")
        ):
            skip_first_spelling_word = True
        previous_prose[path] = (number, raw)
        export_text = text.replace("__CITATION__", "kaynak").replace("__REF__", "öğe")
        text_export.append(f"{rel}:{number}: {export_text}")
        if is_structural_latex(raw):
            continue
        check_text = re.sub(r"\b\S+@\S+\.\S+\b", "e-posta", text)
        check_text = re.sub(r"https?://\S+|www\.\S+", "adres", check_text)
        if any(token in raw for token in MOJIBAKE):
            append_finding(rel, number, "Türkçe karakter bozulması olabilir.", raw.strip())
        if any(token in raw for token in PLACEHOLDERS):
            append_finding(rel, number, "Örnek/yer tutucu metin kalmış olabilir.", raw.strip())
        if re.search(r"[!?.,;:]{2,}", check_text):
            append_finding(rel, number, "Art arda noktalama işareti var.", raw.strip())
        for pattern, message in COMMON_SUGGESTIONS:
            if pattern.search(check_text):
                if "Noktalama işaretinden önce" in message and not has_source_space_before_punctuation(raw):
                    continue
                if "yinelenen" in message:
                    repeated = re.search(r"\b(\w+)\s+\1\b", check_text, re.I)
                    if repeated and repeated.group(1).casefold() in {"ayrı", "tek", "bir", "hemen", "yavaş", "sık", "ara", "zaman", "parça"}:
                        continue
                append_finding(rel, number, message, raw.strip())
        for message in sentence_warnings(check_text):
            append_finding(rel, number, message, raw.strip())
        for message in guideline_writing_rule_warnings(raw, check_text, rel=rel, decimal_separator=decimal_separator):
            append_finding(rel, number, message, raw.strip())
        spelling_lang = spelling_language_for_path(rel, language)
        if Path(rel).name == "tez.tex":
            continue
        spelling_text = check_text
        if not str(spelling_lang).lower().startswith("en"):
            for pattern, _base_phrase in FOREIGN_TECHNICAL_PHRASE_PATTERNS_TR:
                spelling_text = pattern.sub(" teknik terim ", spelling_text)
        if not str(spelling_lang).lower().startswith("en") and looks_like_legacy_wrapped_turkish_line(raw, check_text):
            continue
        dictionary_key = "en" if str(spelling_lang).lower().startswith("en") else "tr"
        if dictionary_key not in dictionary_cache:
            dictionary_cache[dictionary_key] = load_dictionary(dictionary_key, workdir=workdir)
            dictionary = dictionary_cache[dictionary_key]
        allow_uppercase_suggestions = str(rel) == "tez.tex" and raw.strip().startswith("\\")
        personal_words = review_user_words(settings, spelling_lang)
        for message in spelling_warnings(
            spelling_text,
            dictionary,
            spelling_lang,
            allow_uppercase_suggestions=allow_uppercase_suggestions,
            personal_words=personal_words,
            skip_first_word=skip_first_spelling_word,
        ):
            append_finding(rel, number, message, raw.strip())
    return findings, text_export


def analyze_tex_structure(workdir, only_files=None):
    findings = []
    env_stack = []
    file_scope = normalized_file_scope(only_files)
    for name in SIGNATURE_FILES:
        if file_scope is not None and Path(name).as_posix() not in file_scope:
            continue
        path = workdir / name
        if not path.exists() or path.suffix.lower() != ".tex":
            continue
        rel = path.relative_to(workdir)
        brace_stack = []
        ignored_env_stack = []
        dollar_open = None
        for number, raw in enumerate(read_text(path).splitlines(), start=1):
            code = re.sub(r"(?<!\\)%.*", "", raw)
            stripped_code = code.strip()
            begin_match = re.search(r"\\begin\{([^{}]+)\}", code)
            end_match = re.search(r"\\end\{([^{}]+)\}", code)
            if begin_match and begin_match.group(1) in STRUCTURE_IGNORED_ENVS:
                ignored_env_stack.append(begin_match.group(1))
                continue
            if ignored_env_stack:
                if end_match and end_match.group(1) == ignored_env_stack[-1]:
                    ignored_env_stack.pop()
                continue
            if stripped_code.startswith(r"\texorpdfstring"):
                continue
            math_heavy = bool(re.search(r"[_^&]|\\(?:frac|left|right|nonumber|hline|sqrt|sum|int)\b", code))
            escaped = False
            for char in code:
                if escaped:
                    escaped = False
                    continue
                if char == "\\":
                    escaped = True
                    continue
                if char == "{":
                    brace_stack.append((rel, number, raw.strip()))
                elif char == "}":
                    if brace_stack:
                        brace_stack.pop()
                    elif not math_heavy:
                        findings.append((rel, number, "Fazladan kapanan küme parantezi olabilir.", raw.strip()))
                        break
            dollars = len(re.findall(r"(?<!\\)\$", code))
            if dollars % 2:
                if dollar_open is None:
                    dollar_open = (rel, number, raw.strip())
                else:
                    dollar_open = None
            for match in re.finditer(r"\\begin\{([^{}]+)\}", code):
                env = match.group(1)
                if env not in STRUCTURE_IGNORED_ENVS:
                    env_stack.append((env, rel, number, raw.strip()))
            for match in re.finditer(r"\\end\{([^{}]+)\}", code):
                env = match.group(1)
                if env in STRUCTURE_IGNORED_ENVS:
                    continue
                if not env_stack:
                    findings.append((rel, number, f"\\end{{{env}}} için eşleşen \\begin bulunamadı.", raw.strip()))
                else:
                    last_env, last_rel, last_number, _last_raw = env_stack.pop()
                    if last_env != env:
                        findings.append((rel, number, f"\\end{{{env}}}, açık \\begin{{{last_env}}} ile eşleşmiyor.", raw.strip()))
                        env_stack.append((last_env, last_rel, last_number, _last_raw))
        if dollar_open is not None:
            rel_open, number_open, raw_open = dollar_open
            findings.append((rel_open, number_open, "Açılan $ matematik modu dosya sonunda kapanmamış olabilir.", raw_open))
    for env, rel, number, raw in env_stack:
        findings.append((rel, number, f"\\begin{{{env}}} açılmış ancak \\end{{{env}}} bulunamadı.", raw))
    return findings


def write_tex_structure_report(workdir, findings):
    report_dir = Path(workdir) / "raporlar"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = report_dir / "tex-on-kontrol-raporu.md"
    lines = [
        "# TeX Ön Kontrol Raporu",
        "",
        "Bu rapor LaTeX kaynaklarında temel kodlama sorunlarını arar: küme parantezi, `$` matematik modu ve `begin/end` eşleşmeleri.",
        "",
        f"- Bulgu sayısı: {len(findings)}",
        "",
    ]
    if findings:
        for rel, number, message, raw in findings:
            lines.append(f"- `{rel}:{number}` - {message}")
            if raw:
                lines.append(f"  - Kod: `{raw[:220]}`")
    else:
        lines.append("Temel TeX ön kontrolünde belirgin sorun bulunmadı.")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


PDF_MOJIBAKE_PATTERNS = [
    re.compile(r"Ã[^\s]*"),
    re.compile(r"Ä[^\s]*"),
    re.compile(r"Å[^\s]*"),
    re.compile(r"�"),
]


def analyze_pdf_unicode(pdf_path):
    if not pdf_path.exists():
        return []
    process = subprocess.run(
        ["pdftotext", "-enc", "UTF-8", str(pdf_path), "-"],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    issues = []
    for page_index, page_text in enumerate((process.stdout or "").split("\f"), start=1):
        for line_number, line in enumerate(page_text.splitlines(), start=1):
            matches = []
            for pattern in PDF_MOJIBAKE_PATTERNS:
                matches.extend(match.group(0) for match in pattern.finditer(line))
            if matches:
                issues.append((page_index, line_number, sorted(set(matches)), line.strip()))
    return issues


def write_pdf_unicode_report(workdir, issues):
    report = workdir / "pdf-unicode-raporu.md"
    lines = [
        "# PDF Unicode / Karakter Bozulması Raporu",
        "",
        "Bu rapor PDF metninde `Ã`, `Ä`, `Å`, `�` gibi karakter bozulması belirtilerini arar.",
        "",
        f"- Bulgu sayısı: {len(issues)}",
        "",
    ]
    if issues:
        for page, line, tokens, text in issues[:300]:
            lines.append(f"- Sayfa {page}, satır {line} - {', '.join(tokens[:8])}")
            lines.append(f"  - Metin: `{text[:220]}`")
    else:
        lines.append("PDF metninde belirgin Unicode/encoding bozulması bulunmadı.")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def latex_note_escape(text):
    replacements = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "%": r"\%",
        "&": r"\&",
        "#": r"\#",
        "_": r"\_",
        "$": r"\$",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    value = text
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def is_annotatable_line(raw):
    stripped = raw.strip()
    if not stripped:
        return False
    if is_structural_latex(raw):
        return False
    if stripped.startswith((
        "\\chapter",
        "\\section",
        "\\subsection",
        "\\subsubsection",
        "\\item",
        "\\caption",
        "\\textbf",
        "\\begin",
        "\\end",
    )):
        return False
    return True


def issue_patterns_for_message(message):
    patterns = []
    if "Türkçe karakter bozulması" in message:
        patterns.extend(re.escape(token) for token in MOJIBAKE)
    if "Örnek/yer tutucu" in message or "Örnek/placeholder" in message:
        patterns.extend(re.escape(token) for token in PLACEHOLDERS)
    if "fazla boşluk" in message:
        patterns.append(r"[ \t]{2,}")
    if "Art arda noktalama" in message:
        patterns.append(r"[!?.,;:]{2,}")
    if "her şey" in message:
        patterns.append(r"\bher\s+şey\b")
    if "birçok" in message:
        patterns.append(r"\bbir\s+çok\b")
    if "hiçbir" in message:
        patterns.append(r"\bhiç\s+bir\b")
    if "ya da" in message and "`yada`" in message:
        patterns.append(r"\byada\b")
    if "`veya da`" in message:
        patterns.append(r"\bveya\s+da\b")
    if "Noktalama işaretinden önce" in message:
        patterns.append(r"\s+([,.;:!?])")
    if "Noktalama işaretinden sonra" in message:
        patterns.append(r"(?<!\d)([,.;:!?])(?=[^\s}\]\d])")
    if "yinelenen sözcük" in message:
        patterns.append(r"\b(\w+)\s+\1\b")
    if "Kalın yazı" in message:
        patterns.append(r"\\textbf\s*\{[^{}]*\}")
    if "Altı çizili" in message:
        patterns.append(r"\\underline\s*\{[^{}]*\}")
    foreign_match = re.search(r"yabancı teknik terim.*?: `([^`]+)`", message, re.I)
    if foreign_match:
        patterns.append(re.escape(foreign_match.group(1)))
    if "renkli yazı" in message:
        patterns.append(r"\\(?:textcolor|color|hl)\b(?:\{[^{}]*\}){0,2}")
    if "Yüzde işareti" in message:
        patterns.append(r"\\%\s+\d+|\d+\s+\\%|%\s+\d+|\d+\s+%")
    if "Ondalık sayı" in message:
        patterns.append(r"(?<![\w\\])\d+[\.,]\d+(?![\w])")
    if "Sayı ile birim" in message:
        patterns.append(r"(?<![\w\\])\d+(?:[,.]\d+)?(?:cm|mm|m|km|kg|g|mg|L|mL|ml|s|dk|sn|Hz|kHz|MHz|Pa|kPa|MPa|N|J|W|V|A)\b")
    if "Derece/sıcaklık" in message:
        patterns.append(r"\d+\s*°\s*C")
    return patterns


def highlight_issue_fragments(raw, messages):
    highlighted = raw
    changed = False
    for message in messages:
        for pattern in issue_patterns_for_message(message):
            regex = re.compile(pattern, re.I)

            def repl(match):
                nonlocal changed
                changed = True
                text = match.group(0)
                return r"{\color{red} " + text + "}"

            highlighted, count = regex.subn(repl, highlighted, count=1)
            if count:
                break
    return highlighted, changed


def annotate_line(raw, messages):
    note = " / ".join(dict.fromkeys(messages))
    note = latex_note_escape(note[:260])
    highlighted, changed = highlight_issue_fragments(raw, messages)
    if changed:
        body = highlighted
    else:
        body = r"{\color{red} " + raw + "}"
    return (
        r"\marginpar{\raggedright\tiny\textcolor{red}{YD: " + note + r"}}"
        + body
    )


def write_annotated_sources(source_workdir, review_workdir, findings):
    by_file_line = {}
    for rel, number, message, _raw in findings:
        by_file_line.setdefault(Path(rel), {}).setdefault(number, []).append(message)

    annotated_count = 0
    skipped_count = 0
    for rel, line_messages in by_file_line.items():
        source = source_workdir / rel
        target = review_workdir / rel
        if not source.exists() or not target.exists():
            skipped_count += len(line_messages)
            continue
        lines = read_text(target).splitlines()
        updated = []
        for number, raw in enumerate(lines, start=1):
            messages = line_messages.get(number)
            if messages and is_annotatable_line(raw):
                updated.append(annotate_line(raw, messages))
                annotated_count += 1
            else:
                updated.append(raw)
                if messages:
                    skipped_count += 1
        target.write_text("\n".join(updated) + "\n", encoding="utf-8")
    return annotated_count, skipped_count


def build_review_pdf(review_workdir, fast=False):
    if fast and shutil.which("xelatex"):
        command = ["xelatex", "-synctex=1", "-interaction=nonstopmode", "tez.tex"]
        log_name = "yazim-denetimi-pdf-hizli-derleme.log"
    else:
        command = ["latexmk", "-xelatex", "-synctex=1", "-interaction=nonstopmode", "tez.tex"]
        log_name = "yazim-denetimi-pdf-derleme.log"
    process = subprocess.run(
        command,
        cwd=str(review_workdir),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    (review_workdir / log_name).write_text(process.stdout or "", encoding="utf-8")
    return process.returncode


def source_signature(source_workdir, findings):
    payload = []
    for name in SIGNATURE_FILES:
        path = source_workdir / name
        if path.exists():
            stat = path.stat()
            payload.append([name, stat.st_mtime_ns, stat.st_size])
    payload.extend([
        str(rel),
        number,
        message,
        hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest(),
    ] for rel, number, message, raw in findings)
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=list)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def create_annotated_pdf(source_workdir, findings, reuse=False, fast=False):
    cache_root = Path(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()) / "InonuFBEThesisPanel" / "review-cache"
    work_hash = hashlib.sha1(str(source_workdir.resolve()).encode("utf-8", errors="ignore")).hexdigest()[:12]
    review_workdir = cache_root / f"{work_hash}-{source_workdir.name}-yazim-denetimi-onizleme"
    signature = source_signature(source_workdir, findings)
    manifest = review_workdir / "yazim-denetimi-onizleme.json"
    review_pdf = review_workdir / "tez.pdf"
    build_mode = "fast" if fast else "full"
    if reuse and review_pdf.exists() and manifest.exists():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
        cached_mode = data.get("build_mode", "full")
        if data.get("signature") == signature and (cached_mode == build_mode or (fast and cached_mode == "full")):
            return {
                "review_workdir": review_workdir,
                "review_pdf": review_pdf,
                "annotated_count": data.get("annotated_count", 0),
                "skipped_count": data.get("skipped_count", 0),
                "return_code": data.get("return_code", 0),
                "build_mode": cached_mode,
                "reused": True,
            }
    ignore_names = {
        "teslim",
        ".tez-gui-yedekler",
        "yazim-denetimi-pdf-onizleme",
        "_gui_pdf_pages",
        review_workdir.name,
    }
    ignore_suffixes = {
        ".aux", ".bbl", ".bcf", ".blg", ".fdb_latexmk", ".fls", ".lof",
        ".log", ".lot", ".out", ".run.xml", ".synctex", ".toc", ".xdv",
    }

    def ignore(_dir, names):
        ignored = set()
        for name in names:
            path = Path(name)
            if name in ignore_names or path.suffix.lower() in ignore_suffixes or name.endswith(".synctex.gz"):
                ignored.add(name)
        return ignored

    if review_workdir.exists():
        for root, dirs, files in os.walk(source_workdir):
            root_path = Path(root)
            rel_root = root_path.relative_to(source_workdir)
            ignored = ignore(root_path, dirs + files)
            dirs[:] = [name for name in dirs if name not in ignored]
            target_root = review_workdir / rel_root
            target_root.mkdir(parents=True, exist_ok=True)
            for name in files:
                if name in ignored:
                    continue
                source_path = root_path / name
                target_path = target_root / name
                if target_path.exists():
                    try:
                        source_stat = source_path.stat()
                        target_stat = target_path.stat()
                        if source_stat.st_size == target_stat.st_size and source_stat.st_mtime_ns == target_stat.st_mtime_ns:
                            continue
                    except OSError:
                        pass
                shutil.copy2(source_path, target_path)
    else:
        shutil.copytree(source_workdir, review_workdir, ignore=ignore)
    annotated_count, skipped_count = write_annotated_sources(source_workdir, review_workdir, findings)
    return_code = build_review_pdf(review_workdir, fast=fast)
    manifest.write_text(json.dumps({
        "signature": signature,
        "build_mode": build_mode,
        "annotated_count": annotated_count,
        "skipped_count": skipped_count,
        "return_code": return_code,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "review_workdir": review_workdir,
        "review_pdf": review_workdir / "tez.pdf",
        "annotated_count": annotated_count,
        "skipped_count": skipped_count,
        "return_code": return_code,
        "build_mode": build_mode,
        "reused": False,
    }


def write_reports(workdir, findings, text_export, annotation=None, language="tr"):
    workdir = Path(workdir)
    report_dir = workdir / "raporlar"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = report_dir / "yazim-denetimi-raporu.md"
    ai_prompt = report_dir / "ai-yazim-denetimi-istegi.md"
    summary_json = report_dir / REVIEW_SUMMARY_FILE
    dictionary = load_dictionary("en" if str(language).lower().startswith("en") else "tr", workdir=workdir)
    settings = load_review_settings(workdir)
    word_count = sum(len(settings.get("user_words", {}).get(lang, [])) for lang in ("tr", "en"))
    ignored_count = len(settings.get("ignored_findings", []))

    category_counts = {}
    file_counts = {}
    message_counts = {}
    current_keys = set()
    for rel, number, message, raw in findings:
        category = finding_category(message)
        category_counts[category] = category_counts.get(category, 0) + 1
        rel_text = str(rel).replace("\\", "/")
        file_counts[rel_text] = file_counts.get(rel_text, 0) + 1
        kind = finding_kind(message)
        message_counts[kind] = message_counts.get(kind, 0) + 1
        current_keys.add(finding_stable_key(rel, number, message, raw))

    previous_keys = set()
    previous_total = None
    if summary_json.exists():
        try:
            previous_data = json.loads(read_text(summary_json))
            previous_keys = {str(item) for item in previous_data.get("finding_keys", [])}
            previous_total = int(previous_data.get("total", 0))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            previous_keys = set()
            previous_total = None
    resolved_count = len(previous_keys - current_keys) if previous_keys else 0
    new_count = len(current_keys - previous_keys) if previous_keys else len(current_keys)

    lines = [
        "# Yazım ve Dilbilgisi Ön Denetim Raporu",
        "",
        "Bu rapor yerel kural tabanlı ve sözlük destekli ön denetimdir. Ayrıca tez yazım kılavuzunda öğrencinin metin yazarken dikkat etmesi beklenen noktalama, sayı-birim, yüzde, renk ve vurgu kullanımı gibi kurallar için ön uyarılar üretir. Gelişmiş yapay zekâ incelemesi için aşağıdaki `ai-yazim-denetimi-istegi.md` dosyası kullanılabilir.",
        "",
        f"- Bulgu sayısı: {len(findings)}",
        f"- Önceki denetime göre: {resolved_count} bulgu giderilmiş/yok sayılmış, {new_count} yeni veya devam eden bulgu",
        f"- Sözlük durumu: {dictionary_status(dictionary, language)}",
        f"- Kişisel sözlük/yok say: {word_count} kelime, {ignored_count} yok sayma kuralı",
        "",
    ]
    if category_counts:
        lines.extend(["## Toplu Özet", ""])
        lines.append("### Bulgu Türleri")
        lines.append("")
        for category in ["Kılavuz yazım kuralı", "Sözlük uyarıları", "Noktalama", "Yer tutucu", "TeX ön kontrol", "PDF karakter bozulması", "İçerik", "Diğer"]:
            count = category_counts.get(category, 0)
            if count:
                lines.append(f"- {category}: {count}")
        lines.append("")
        lines.append("### Dosyaya Göre")
        lines.append("")
        for rel_text, count in sorted(file_counts.items(), key=lambda item: (-item[1], item[0].casefold())):
            lines.append(f"- `{rel_text}`: {count}")
        lines.append("")
        frequent = sorted(message_counts.items(), key=lambda item: (-item[1], item[0]))[:8]
        if frequent:
            lines.append("### En Sık Görülen Bulgular")
            lines.append("")
            for message, count in frequent:
                lines.append(f"- {count} kez: {message}")
            lines.append("")
    if annotation:
        lines.extend([
            "## PDF Üzerinde İşaretli Önizleme",
            "",
            f"- Önizleme klasörü: `{annotation['review_workdir']}`",
            f"- İşaretli PDF: `{annotation['review_pdf']}`",
            f"- PDF içinde işaretlenen satır sayısı: {annotation['annotated_count']}",
            f"- PDF içine güvenle işlenemeyen/raporda kalan satır sayısı: {annotation['skipped_count']}",
            f"- Derleme çıkış kodu: {annotation['return_code']}",
            "",
        ])
    if findings:
        lines.append("## Bulgular")
        lines.append("")
        for rel, number, message, raw in findings:
            lines.append(f"- `{rel}:{number}` - {message}")
            if raw:
                lines.append(f"  - Metin: `{raw[:220]}`")
    else:
        lines.append("Otomatik ön denetimde belirgin sorun bulunmadı.")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    summary_payload = {
        "created_at": datetime_now_iso(),
        "total": len(findings),
        "resolved_since_previous": resolved_count,
        "new_or_continuing": new_count,
        "category_counts": category_counts,
        "file_counts": file_counts,
        "finding_keys": sorted(current_keys),
        "personal_words": word_count,
        "ignored_findings": ignored_count,
        "previous_total": previous_total,
    }
    summary_json.write_text(json.dumps(summary_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    prompt = [
        "# Yapay Zekâ Destekli Yazım Denetimi İsteği",
        "",
        "Aşağıdaki tez metnini akademik Türkçe açısından inceleyin. Yazım, noktalama, anlatım bozukluğu, gereksiz tekrar, çok uzun cümle ve terminoloji tutarlılığı için öneriler verin. LaTeX komutlarını değiştirmeyin; önerileri dosya ve satır numarasıyla listeleyin.",
        "",
        "```text",
        *text_export,
        "```",
        "",
    ]
    ai_prompt.write_text("\n".join(prompt), encoding="utf-8")
    return report, ai_prompt


def main():
    parser = argparse.ArgumentParser(description="Tez metni icin yerel yazim ve dilbilgisi on denetimi yapar.")
    parser.add_argument("--workdir", default=".", help="Tez calisma klasoru.")
    parser.add_argument("--annotate-pdf", action="store_true", help="Bulgulari ayri bir kopyada PDF uzerinde renkli isaretler.")
    args = parser.parse_args()
    workdir = Path(args.workdir).resolve()
    findings, text_export = analyze(workdir)
    annotation = create_annotated_pdf(workdir, findings) if args.annotate_pdf else None
    report, ai_prompt = write_reports(workdir, findings, text_export, annotation)
    print(f"Rapor yazildi: {report}")
    print(f"AI inceleme istegi yazildi: {ai_prompt}")
    print(f"Bulgu sayisi: {len(findings)}")
    if annotation:
        print(f"Isaretli PDF klasoru: {annotation['review_workdir']}")
        print(f"Isaretli PDF: {annotation['review_pdf']}")
        print(f"PDF isaretleme: {annotation['annotated_count']} satir, atlanan: {annotation['skipped_count']}, derleme kodu: {annotation['return_code']}")


if __name__ == "__main__":
    main()
