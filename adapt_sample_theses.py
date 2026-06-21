import argparse
import json
import re
import shutil
import sys
from pathlib import Path

import sablon_koruma


ROOT = Path(__file__).resolve().parent
SAMPLE_ROOT = ROOT / "sample_thesis"
TEMPLATE_DIR = ROOT / "inonu-fbe-tez-sablonu-2025"
OUTPUT_ROOT = ROOT / "sample_thesis_adapted"
REPORT_JSON = ROOT / "sample_thesis_adaptation_report.json"
REPORT_MD = ROOT / "sample_thesis_adaptation_report.md"

TR_MONTHS = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]
EN_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

TEXT_SUFFIXES = {".tex", ".bib", ".bst", ".cls", ".sty", ".ps1", ".md", ".json", ".txt"}
BUILD_SUFFIXES = {".aux", ".bbl", ".bcf", ".blg", ".fdb_latexmk", ".fls", ".lof", ".log", ".lot", ".out", ".run.xml", ".synctex", ".toc", ".xdv"}
SKIP_TEMPLATE_FILES = {
    "tez.pdf", "sirt-kapak.pdf", "kontrol-raporu.json", "kontrol-raporu.md",
    "eksik-bilgiler.md", "pilot-includedocskip-smoke.tex", "pilot-sw-doc.tex",
}
CONVERSION_SUPPORT_START = "% BEGIN TEZ_GUI_CONVERSION_SUPPORT"
CONVERSION_SUPPORT_END = "% END TEZ_GUI_CONVERSION_SUPPORT"


def read_text(path):
    for encoding in ("utf-8-sig", "utf-8", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def write_text(path, text):
    path.write_text(text, encoding="utf-8")


def display_path(path, base=ROOT):
    path = Path(path)
    try:
        return str(path.resolve().relative_to(Path(base).resolve()))
    except ValueError:
        return str(path)


def strip_comments(text):
    cleaned = []
    for line in text.splitlines():
        cut = len(line)
        for match in re.finditer("%", line):
            index = match.start()
            slash_count = 0
            j = index - 1
            while j >= 0 and line[j] == "\\":
                slash_count += 1
                j -= 1
            if slash_count % 2 == 0:
                cut = index
                break
        cleaned.append(line[:cut])
    return "\n".join(cleaned)


def parse_command(text, name):
    pattern = re.compile(rf"\\{re.escape(name)}(?![A-Za-z])")
    match = pattern.search(text)
    if not match:
        return []
    args = []
    i = match.end()
    while i < len(text):
        while i < len(text) and text[i].isspace():
            i += 1
        if i >= len(text) or text[i] != "{":
            break
        depth = 1
        start = i + 1
        i += 1
        while i < len(text) and depth:
            if text[i] == "\\":
                i += 2
                continue
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        args.append(text[start:i - 1].strip())
    return args


def all_commands(text, name):
    result = []
    for match in re.finditer(rf"\\{re.escape(name)}(?![A-Za-z])", text):
        args = []
        i = match.end()
        while i < len(text):
            while i < len(text) and text[i].isspace():
                i += 1
            if i >= len(text) or text[i] != "{":
                break
            depth = 1
            start = i + 1
            i += 1
            while i < len(text) and depth:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                i += 1
            args.append(text[start:i - 1].strip())
        result.append(args)
    return result


def macro_line(name, values):
    return "\\" + name + "".join("{" + value + "}" for value in values)


def latex_ref_exists(base, stem):
    path = base / stem
    if path.suffix:
        return path.exists()
    return path.with_suffix(".tex").exists()


def clean_title_args(values):
    values = [value for value in values if value]
    return (values + ["", "", ""])[:3]


def date_from_old(values):
    if len(values) >= 3 and values[0].isdigit() and values[1].isdigit() and values[2].isdigit():
        day = str(int(values[0]))
        month_index = max(1, min(12, int(values[1]))) - 1
        year = values[2]
        return f"{day} {TR_MONTHS[month_index]} {year}", f"{day} {EN_MONTHS[month_index]} {year}", TR_MONTHS[month_index], year
    if values:
        return values[0], values[1] if len(values) > 1 else values[0], "", ""
    return "", "", "", ""


def month_year_from_old(values):
    tr_date, en_date, tr_month, year = date_from_old(values)
    if tr_month and year:
        return f"{tr_month.upper()} {year}", f"{EN_MONTHS[TR_MONTHS.index(tr_month)].upper()} {year}", f"{tr_month} {year}", f"{EN_MONTHS[TR_MONTHS.index(tr_month)]} {year}"
    return "TEZİN SAVUNULDUĞU AY YIL", "MONTH YEAR OF DEFENSE", "Tezin savunulduğu ay yıl", "Month year of defense"


def advisor_macros(values):
    if len(values) >= 6:
        return [f"{values[0]} {values[1]}".strip(), values[2]], [f"{values[3]} {values[4]}".strip(), values[5]]
    if len(values) >= 2:
        return values[:2], values[:2]
    return ["", ""], ["", ""]


def split_keywords(values):
    if len(values) >= 2:
        return [values[0]], [values[1]]
    if len(values) == 1:
        return [values[0]], [""]
    return [""], [""]


def referenced_chapters(text, source_dir):
    refs = []
    for command in ("includedocskip", "input", "include"):
        for args in all_commands(text, command):
            if not args:
                continue
            ref = args[0].strip()
            stem = Path(ref).stem
            if re.match(r"^(bolum|ch)\d+", stem, re.I) and latex_ref_exists(source_dir, ref):
                refs.append((command, ref))
    seen = set()
    ordered = []
    for command, ref in refs:
        key = Path(ref).stem.lower()
        if key not in seen:
            seen.add(key)
            ordered.append(ref)
    if ordered:
        return ordered
    candidates = sorted(source_dir.glob("bolum*.tex")) + sorted(source_dir.glob("ch*.tex"))
    return [path.stem for path in candidates]


def custom_preamble(text):
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if (
            stripped.startswith("\\theoremstyle")
            or stripped.startswith("\\newtheorem")
            or stripped.startswith("\\newenvironment{proof}")
            or stripped.startswith("\\numberwithin")
            or stripped.startswith("\\renewcommand{\\theequation}")
            or stripped.startswith("\\providecommand")
            or stripped.startswith("\\DeclareGraphicsExtensions")
        ):
            lines.append(line)
    return "\n".join(lines)


def graphics_path_line(dest):
    image_suffixes = {".eps", ".pdf", ".png", ".jpg", ".jpeg"}
    dirs = []
    for path in dest.rglob("*"):
        if path.is_file() and path.suffix.lower() in image_suffixes:
            rel = path.parent.relative_to(dest).as_posix()
            if rel and rel not in dirs:
                dirs.append(rel)
    if not dirs:
        return ""
    return "\\graphicspath{" + "".join("{" + rel + "/}" for rel in dirs) + "}"


def copy_template_support(dest):
    for item in TEMPLATE_DIR.iterdir():
        if item.name in SKIP_TEMPLATE_FILES or item.suffix in BUILD_SUFFIXES:
            continue
        target = dest / item.name
        if item.is_dir():
            if item.name == "teslim":
                continue
            if target.exists():
                continue
            shutil.copytree(item, target)
        elif item.name == "tez.tex":
            continue
        elif item.suffix.lower() == ".bib" and target.exists():
            sample_target = target.with_name(f"{target.stem}_sablon_ornek{target.suffix}")
            if not sample_target.exists():
                shutil.copy2(item, sample_target)
            continue
        elif item.suffix.lower() == ".tex" and item.name not in {"defs.tex", "sirt-kapak.tex", "eklerkapak.tex", "etik-beyan.tex"}:
            continue
        elif item.suffix.lower() == ".tex" and target.exists():
            continue
        else:
            shutil.copy2(item, target)
    for logo_pattern in ("iu_fbe_logo*.*", "iu_logo.png", "iu_logo_yellow.png", "kabul-onay-logo.jpeg"):
        for logo in ROOT.glob(logo_pattern):
            shutil.copy2(logo, dest / logo.name)


def copy_or_make_bib(dest, old_bibliographies):
    stems = [stem.strip() for group in old_bibliographies for stem in ",".join(group).split(",") if stem.strip()]
    if not stems:
        stems = ["kaynaklar"] if (dest / "kaynaklar.bib").exists() else ["tez"]
    first = Path(stems[0]).stem
    src = dest / f"{first}.bib"
    if src.exists():
        target = dest / "kaynaklar.bib"
        if src.resolve() != target.resolve():
            shutil.copy2(src, target)
    elif not (dest / "kaynaklar.bib").exists():
        write_text(dest / "kaynaklar.bib", "")
    sanitize_apa_bib(dest / "kaynaklar.bib")
    return "kaynaklar"


def sanitize_apa_bib(path):
    if not path.exists():
        return
    text = read_text(path)
    replacements = {
        "Karakoç ,S.B.Gazi, Turabi, G., Başhan, A.": "Karakoç, S. Battal Gazi and Turabi, G. and Başhan, A.",
        "Richtmyer, R.D., Morton, K.W.": "Richtmyer, R. D. and Morton, K. W.",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    write_text(path, text)


def sanitize_legacy_defs(dest):
    defs = dest / "defs.tex"
    if not defs.exists():
        return
    original = read_text(defs)
    cleaned_lines = []
    removed_patterns = (
        r"\\usepackage(?:\[[^\]]*\])?\{fontenc\}",
        r"\\usepackage(?:\[[^\]]*\])?\{inputenc\}",
        r"\\usepackage(?:\[[^\]]*\])?\{mathptmx\}",
        r"\\usepackage(?:\[[^\]]*\])?\{times\}",
        r"\\usepackage(?:\[[^\]]*\])?\{fixltx2e\}",
        r"\\usepackage(?:\[[^\]]*\])?\{cite\}",
    )
    for line in original.splitlines():
        if re.search(r"\\usepackage(?:\[[^\]]*\])?\{hypenTR\}", line):
            cleaned_lines.append(r"\IfFileExists{hypenTR.sty}{\usepackage{hypenTR}}{}")
        elif any(re.search(pattern, line) for pattern in removed_patterns):
            cleaned_lines.append("% Uyarlama: XeLaTeX/fontspec ile çakıştığı için kaldırıldı: " + line)
        else:
            cleaned_lines.append(line)
    backup = dest / "defs_legacy_original.tex"
    if not backup.exists():
        write_text(backup, original)
    write_text(defs, "\n".join(cleaned_lines) + "\n")


def ensure_required_aliases(dest):
    if not (dest / "abstract.tex").exists() and (dest / "summary.tex").exists():
        shutil.copy2(dest / "summary.tex", dest / "abstract.tex")


def normalize_converted_figure_names(dest):
    for pdf in dest.rglob("*-eps-converted-to.pdf"):
        alias = pdf.with_name(pdf.name.replace("-eps-converted-to.pdf", ".pdf"))
        if not alias.exists():
            shutil.copy2(pdf, alias)


def apa_support_block():
    return [
        "% Kaynak stili documentclass icindeki apa veya num secenegi ile belirlenir.",
        r"\makeatletter",
        r"\if@APAStyle",
        r"  \usepackage[style=apa, backend=biber, sortcites=true, maxnames=20, minnames=1, dashed=false]{biblatex}",
        r"  \AtBeginBibliography{%",
        r"    \oneandonehalf",
        r"    \sffamily\normalsize\selectfont",
        r"    \setlength{\bibhang}{1.25cm}%",
        r"    \renewcommand*{\mkbibnamefamily}[1]{#1}%",
        r"    \renewcommand*{\mkbibnamegiven}[1]{#1}%",
        r"  }",
        r"  \addbibresource{kaynaklar.bib}",
        r"  \defbibheading{bibliography}{%",
        r"    \makeatletter",
        r"    \chapter*{\if@Ingilizce REFERENCES\else KAYNAKLAR\fi}",
        r"    \addtocontents{toc}{\protect\addvspace{-10pt}}",
        r"    \addcontentsline{toc}{chapter}{\bf{\if@Ingilizce REFERENCES\else KAYNAKLAR\fi}}",
        r"    \makeatother",
        r"    \sffamily\normalsize\selectfont",
        r"  }",
        r"\else",
        r"  \providecommand{\parencite}[1]{\cite{#1}}",
        r"  \providecommand{\textcite}[1]{\cite{#1}}",
        r"\fi",
        r"\makeatother",
    ]


def replace_or_append_marked_block(text, start_marker, end_marker, block_lines):
    block = "\n".join([start_marker, *[line for line in block_lines if line is not None], end_marker])
    pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.S)
    if pattern.search(text):
        return pattern.sub(lambda _match: block, text)
    return text.rstrip() + "\n\n" + block + "\n"


def write_conversion_defs(dest, graphicspath, preamble):
    defs = dest / "defs.tex"
    text = read_text(defs) if defs.exists() else "% Dönüşüm destek tanımları.\n"
    block = [
        "% Eski tez dönüşümü için ana tez.tex dışında tutulan preamble destekleri.",
        r"\usepackage{float}",
        r"\usepackage{changepage}",
        graphicspath,
        r"\providecommand{\shorthandoff}[1]{}",
        r"\providecommand{\shorthandon}[1]{}",
        r"\providecommand{\texorpdfstring}[2]{#1}",
        preamble,
        *apa_support_block(),
    ]
    write_text(defs, replace_or_append_marked_block(text, CONVERSION_SUPPORT_START, CONVERSION_SUPPORT_END, block))


def extract_document_body(text):
    begin = re.search(r"\\begin\{document\}", text)
    end = re.search(r"\\end\{document\}", text)
    if begin:
        text = text[begin.end():end.start()] if end and end.start() > begin.end() else text[begin.end():]
    elif end:
        text = text[:end.start()]
    cleaned = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("\\documentclass", "\\usepackage", "\\RequirePackage")):
            continue
        if stripped in {r"\begin{document}", r"\end{document}", r"\raggedleft", r"\\", r"\\"}:
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip() + "\n"


def build_new_tez(source_tex, dest):
    source_dir = source_tex.parent
    text = strip_comments(read_text(source_tex))
    docclass = re.search(r"\\documentclass\[([^\]]*)\]\{inonutez\}", text)
    options = [part.strip() for part in docclass.group(1).split(",")] if docclass else []
    degree = "doktora" if "doktora" in options else "yukseklisans"
    thesis_language = "ingilizce" if "ingilizce" in options else "turkce"

    yazar = (parse_command(text, "yazar") + ["", ""])[:2]
    ogrencino = (parse_command(text, "ogrencino") + [""])[0]
    anabilimdali = parse_command(text, "anabilimdali") or ["Matematik Anabilim Dalı", "Department of Mathematics"]
    if len(anabilimdali) == 1:
        anabilimdali.append("Department of Mathematics")
    programi = parse_command(text, "programi") or ["Matematik Programı", "Mathematics Programme"]
    danisman_tr, danisman_en = advisor_macros(parse_command(text, "tezyoneticisi"))
    if parse_command(text, "tezyoneticisiENG"):
        danisman_en = (parse_command(text, "tezyoneticisiENG") + ["", ""])[:2]
    esdanismani = (parse_command(text, "esdanismani") + ["", ""])[:2]
    esdanismani_eng = (parse_command(text, "esdanismaniENG") + ["", ""])[:2]
    baslik = clean_title_args(parse_command(text, "baslik") or parse_command(text, "kucukbaslik"))
    title = clean_title_args(parse_command(text, "title"))
    keywords_tr, keywords_en = split_keywords(parse_command(text, "anahtarkelimeler"))
    defense_values = parse_command(text, "tezsavunmatarih")
    defense_tr, defense_en, _, defense_year = date_from_old(defense_values)
    tarih_tr, tarih_en, tarih_kucuk_tr, tarih_kucuk_en = month_year_from_old(defense_values)
    submission_values = parse_command(text, "tezvermetarih")
    submission_tr, submission_en, _, _ = date_from_old(submission_values) if submission_values else (defense_tr, defense_en, "", "")
    oy = (parse_command(text, "oy") + ["oy birliği"])[0]
    if "/" in oy:
        oy = "oy birliği"
    mudur = (parse_command(text, "EnstituMuduru") + ["Prof. Dr. Süleyman KÖYTEPE"])[0]

    juri_lines = []
    for name in ("juriBir", "juriIki", "juriUc", "juriDort", "juriBes"):
        juri_lines.append(macro_line(name, (parse_command(text, name) + ["", ""])[:2]))

    chapters = referenced_chapters(text, source_dir)
    chapter_lines = []
    for ref in chapters:
        stem = Path(ref).with_suffix("").as_posix()
        chapter_lines.append(f"\\includedocskip{{{stem}}}")
    bibliography_stem = copy_or_make_bib(dest, all_commands(text, "bibliography"))
    preamble = custom_preamble(text)
    graphicspath = graphics_path_line(dest)
    write_conversion_defs(dest, graphicspath, preamble)

    sembol_file = "semboller" if (dest / "semboller.tex").exists() else ("sembol" if (dest / "sembol.tex").exists() else "")
    summary_file = "abstract" if (dest / "abstract.tex").exists() else ("summary" if (dest / "summary.tex").exists() else "")

    def include_expr(stem, body_copy=False):
        if not stem:
            return ""
        path = dest / f"{stem}.tex"
        if not path.exists():
            return ""
        body = read_text(path)
        if body_copy and ("\\documentclass" in body or "\\begin{document}" in body):
            body_name = f"{stem}_body"
            write_text(dest / f"{body_name}.tex", extract_document_body(body))
            return fr"\input{{{body_name}.tex}}"
        if "\\documentclass" in body or "\\begin{document}" in body:
            return fr"\includedocskip{{{stem}}}"
        return fr"\input{{{stem}.tex}}"

    lines = [
        "% Yeni Inonu FBE 2025 sablonuna otomatik pilot uyarlama.",
        "% Kaynak eski tez: " + display_path(source_tex),
        f"\\documentclass[{thesis_language},bez,fenbilimleri,{degree},num]{{inonutez}}",
        "",
        r"\providecommand{\ondalikayirici}[1]{}",
        r"\providecommand{\sayfaduzeni}[1]{}",
        r"\ondalikayirici{nokta}",
        r"\sayfaduzeni{tek}",
        "",
        macro_line("yazar", yazar),
        macro_line("ogrencino", [ogrencino]),
        macro_line("unvan", [""]),
        macro_line("anabilimdali", anabilimdali[:2]),
        macro_line("programi", programi[:2]),
        macro_line("tarih", [tarih_tr, tarih_en]),
        macro_line("tarihKucuk", [tarih_kucuk_tr, tarih_kucuk_en]),
        macro_line("tezyoneticisi", danisman_tr),
        macro_line("tezyoneticisiENG", danisman_en),
        macro_line("bapdestegi", [""]),
        macro_line("esdanismani", esdanismani),
        macro_line("esdanismaniENG", esdanismani_eng),
        macro_line("baslik", baslik),
        macro_line("title", title),
        macro_line("tezvermetarih", [submission_tr, submission_en]),
        macro_line("tezsavunmatarih", [defense_tr, defense_en]),
        macro_line("kapakyili", [defense_year or "2026"]),
        macro_line("kapaksehri", ["MALATYA"]),
        macro_line("oy", [oy]),
        macro_line("yonetimkurulukarar", ["", ""]),
        *juri_lines,
        macro_line("ithaf", [""]),
        macro_line("tesekkur", [include_expr("tesekkur", body_copy=True) or include_expr("onsoz", body_copy=True)]),
        macro_line("kisaltmalistesi", [r"\input{kisaltmalar.tex}" if (dest / "kisaltmalar.tex").exists() else ""]),
        macro_line("sembollistesi", [include_expr(sembol_file, body_copy=True)]),
        macro_line("ozet", [include_expr("ozet", body_copy=True)]),
        macro_line("summary", [include_expr(summary_file, body_copy=True)]),
        macro_line("anahtarkelimeler", keywords_tr),
        macro_line("keywords", keywords_en),
        macro_line("etikbeyan", [r"\input{etik-beyan.tex}" if (dest / "etik-beyan.tex").exists() else ""]),
        macro_line("ozgecmis", [include_expr("ozgecmis", body_copy=True)]),
        macro_line("EnstituMuduru", [mudur]),
        "",
        r"\input defs.tex" if (dest / "defs.tex").exists() else "",
        "",
        r"\begin{document}",
        "",
        "% Scientific WorkPlace/LyX uyumlu bolum dosyalari.",
        *chapter_lines,
        "",
        r"\makeatletter",
        r"\if@APAStyle",
        r"  \setlength\bibitemsep{0pt}",
        r"  \printbibliography[heading=bibliography]",
        r"\else",
        r"  \bibliographystyle{inonubib}",
        fr"  \bibliography{{{bibliography_stem}}}",
        r"\fi",
        r"\makeatother",
        "",
        r"\eklerkapak{}",
        r"\input eklerkapak.tex" if (dest / "eklerkapak.tex").exists() else "",
        r"\eklerbolum{0}",
        r"\chapter{EK-1 Özgeçmiş}",
        include_expr("ozgecmis", body_copy=True),
        r"\input ekler.tex" if (dest / "ekler.tex").exists() else "",
        r"\ozgecmissondabasmasin",
        r"\end{document}",
        "",
    ]
    write_text(dest / "tez.tex", "\n".join(line for line in lines if line is not None))
    return {
        "source": str(source_tex),
        "target": str(dest / "tez.tex"),
        "degree": degree,
        "thesis_language": thesis_language,
        "chapters": chapters,
        "bibliography": bibliography_stem,
    }


def adapt_one(source_tex):
    rel_dir = source_tex.parent.relative_to(SAMPLE_ROOT)
    dest = OUTPUT_ROOT / rel_dir
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source_tex.parent, dest, ignore=shutil.ignore_patterns("*.aux", "*.bbl", "*.bcf", "*.blg", "*.fdb_latexmk", "*.fls", "*.lof", "*.log", "*.lot", "*.out", "*.run.xml", "*.toc", "*.xdv", "*.synctex.gz"))
    copy_template_support(dest)
    sanitize_legacy_defs(dest)
    ensure_required_aliases(dest)
    normalize_converted_figure_names(dest)
    result = build_new_tez(source_tex, dest)
    try:
        repairs = sablon_koruma.repair_workdir(dest, baseline_dir=TEMPLATE_DIR, dry_run=False)
        result["repair_items"] = [
            {
                "severity": item.severity,
                "file": item.file,
                "message": item.message,
                "changed": item.changed,
            }
            for item in repairs
        ]
    except Exception as exc:
        result["repair_error"] = str(exc)
    return result


def parse_args():
    parser = argparse.ArgumentParser(description="Eski Inonu FBE tez klasorunu yeni sablona uyarlar.")
    parser.add_argument("--source", default=str(SAMPLE_ROOT), help="Eski tez klasoru veya tez.tex dosyasi")
    parser.add_argument("--output", default=str(OUTPUT_ROOT), help="Donusturulen tezlerin yazilacagi klasor")
    parser.add_argument("--report-json", default=str(REPORT_JSON), help="JSON donusum raporu")
    parser.add_argument("--report-md", default=str(REPORT_MD), help="Markdown donusum raporu")
    parser.add_argument("--template", default=str(TEMPLATE_DIR), help="Yeni sablon destek dosyalari klasoru")
    return parser.parse_args()


def find_source_theses(source):
    if source.is_file():
        if source.name.lower() != "tez.tex":
            raise SystemExit(f"Kaynak dosya tez.tex olmali: {source}")
        return source.parent, [source]
    if not source.exists():
        raise SystemExit(f"Kaynak klasor bulunamadi: {source}")
    return source, sorted(source.rglob("tez.tex"))


def main():
    global SAMPLE_ROOT, TEMPLATE_DIR, OUTPUT_ROOT, REPORT_JSON, REPORT_MD

    args = parse_args()
    source_arg = Path(args.source).expanduser().resolve()
    SAMPLE_ROOT, theses = find_source_theses(source_arg)
    TEMPLATE_DIR = Path(args.template).expanduser().resolve()
    OUTPUT_ROOT = Path(args.output).expanduser().resolve()
    REPORT_JSON = Path(args.report_json).expanduser().resolve()
    REPORT_MD = Path(args.report_md).expanduser().resolve()

    if not TEMPLATE_DIR.exists():
        raise SystemExit(f"Sablon klasoru bulunamadi: {TEMPLATE_DIR}")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)

    results = []
    for tex in theses:
        try:
            results.append({**adapt_one(tex), "ok": True, "error": ""})
        except Exception as exc:
            results.append({"source": str(tex), "target": "", "ok": False, "error": str(exc)})
    summary = {
        "source_root": str(SAMPLE_ROOT),
        "output_root": str(OUTPUT_ROOT),
        "adapted_count": sum(1 for item in results if item["ok"]),
        "failed_count": sum(1 for item in results if not item["ok"]),
        "total": len(results),
    }
    REPORT_JSON.write_text(json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8-sig")
    lines = [
        "# Eski Tez Dönüşüm Raporu",
        "",
        f"- Kaynak tez sayısı: {summary['total']}",
        f"- Uyarlanan tez sayısı: {summary['adapted_count']}",
        f"- Hata alan tez sayısı: {summary['failed_count']}",
        f"- Çıktı klasörü: `{OUTPUT_ROOT}`",
        "",
        "## Uyarlanan Tezler",
        "",
    ]
    for item in results:
        if item["ok"]:
            lines.append(f"- `{display_path(item['target'])}`: bölüm={len(item['chapters'])}, kaynakça={item['bibliography']}, stil=num")
            repairs = item.get("repair_items") or []
            changed_repairs = [repair for repair in repairs if repair.get("changed")]
            if changed_repairs:
                for repair in changed_repairs:
                    lines.append(f"  - Otomatik onarım: `{repair.get('file', '')}` - {repair.get('message', '')}")
            if item.get("repair_error"):
                lines.append(f"  - Onarım uyarısı: {item['repair_error']}")
        else:
            lines.append(f"- HATA `{display_path(item['source'])}`: {item['error']}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["adapted_count"] else 1


if __name__ == "__main__":
    sys.exit(main())
