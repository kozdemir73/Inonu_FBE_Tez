import json
import html
import importlib.util
import os
import queue
import re
import shutil
import subprocess
import sys
import textwrap
import threading
import tkinter as tk
import types
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, font as tkfont, messagebox, ttk

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageTk

import yazim_denetimi
import sablon_koruma


ROOT = Path(__file__).resolve().parent
LOCAL_OUTPUT_ROOT = ROOT.parent


def resolve_git_executable():
    found = shutil.which("git")
    if found:
        return found
    candidates = [
        Path(os.environ.get("ProgramFiles", "")) / "Git" / "cmd" / "git.exe",
        Path(os.environ.get("ProgramFiles", "")) / "Git" / "bin" / "git.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Git" / "cmd" / "git.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Git" / "bin" / "git.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Git" / "cmd" / "git.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Git" / "bin" / "git.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def read_app_version():
    try:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        return version or "v0.8"
    except OSError:
        return "v0.8"


APP_VERSION = read_app_version()
TEMPLATES = {
    "Birleşik İnönü FBE 2025": ROOT / "inonu-fbe-tez-sablonu-2025",
}
INFO_INPUT_ROLES = [
    ("onsoz", "Önsöz", "onsoz"),
    ("simgelervekisaltmalar", "Simgeler ve Kısaltmalar dizini", "simgeler-kisaltmalar"),
    ("ozet", "Özet", "ozet"),
    ("summary", "Abstract", "summary"),
    ("etikbeyan", "Etik beyan", "etik"),
]
CHAPTER_INPUT_ROLES = [(f"bolum{i}", f"Bölüm {i}", f"bolum{i}") for i in range(1, 7)]
TEX_INPUT_ROLES = INFO_INPUT_ROLES + CHAPTER_INPUT_ROLES
DEGREE_DISPLAY = {"tr": {"yukseklisans": "Yüksek Lisans", "doktora": "Doktora"}, "en": {"yukseklisans": "Master's", "doktora": "PhD"}}
DEGREE_VALUE = {label: key for labels in DEGREE_DISPLAY.values() for key, label in labels.items()}
CITATION_DISPLAY = {"tr": {"apa": "APA 7", "num": "Numaralı"}, "en": {"apa": "APA 7", "num": "Numbered"}}
CITATION_VALUE = {label: key for labels in CITATION_DISPLAY.values() for key, label in labels.items()}
THESIS_LANGUAGE_DISPLAY = {"tr": {"turkce": "Türkçe", "ingilizce": "İngilizce"}, "en": {"turkce": "Turkish", "ingilizce": "English"}}
DECIMAL_SEPARATOR_DISPLAY = {"tr": {"virgul": "Virgül (3,14)", "nokta": "Nokta (3.14)"}, "en": {"virgul": "Comma (3,14)", "nokta": "Point (3.14)"}}
DECIMAL_SEPARATOR_VALUE = {label: key for labels in DECIMAL_SEPARATOR_DISPLAY.values() for key, label in labels.items()}
PAGE_LAYOUT_DISPLAY = {"tr": {"tek": "Tek taraflı", "cift": "Çift taraflı"}, "en": {"tek": "One-sided", "cift": "Two-sided"}}
PAGE_LAYOUT_VALUE = {label: key for labels in PAGE_LAYOUT_DISPLAY.values() for key, label in labels.items()}
DEFAULT_DEPARTMENT = "Matematik"
DEFAULT_CITATION_STYLE = "num"
DEPARTMENT_OPTIONS = [
    "Biyoloji",
    "Fizik",
    "Kimya",
    "Matematik",
    "Moleküler Biyoloji ve Genetik",
    "Bilgisayar Mühendisliği",
    "Biyomedikal Mühendisliği",
    "Elektrik Elektronik Mühendisliği",
    "Gıda Mühendisliği",
    "İnşaat Mühendisliği",
    "Kimya Mühendisliği",
    "Maden Mühendisliği",
    "Makine Mühendisliği",
    "Yazılım Mühendisliği",
    "Peyzaj Mimarlığı",
    "Enerji Bilimi ve Teknolojileri",
    "İş Sağlığı ve Güvenliği",
    "Uygulamalı Bilimler ve Teknoloji",
]
DEPARTMENT_EN = {
    "Biyoloji": "Department of Biology",
    "Fizik": "Department of Physics",
    "Kimya": "Department of Chemistry",
    "Matematik": "Department of Mathematics",
    "Moleküler Biyoloji ve Genetik": "Department of Molecular Biology and Genetics",
    "Bilgisayar Mühendisliği": "Department of Computer Engineering",
    "Biyomedikal Mühendisliği": "Department of Biomedical Engineering",
    "Elektrik Elektronik Mühendisliği": "Department of Electrical and Electronics Engineering",
    "Gıda Mühendisliği": "Department of Food Engineering",
    "İnşaat Mühendisliği": "Department of Civil Engineering",
    "Kimya Mühendisliği": "Department of Chemical Engineering",
    "Maden Mühendisliği": "Department of Mining Engineering",
    "Makine Mühendisliği": "Department of Mechanical Engineering",
    "Yazılım Mühendisliği": "Department of Software Engineering",
    "Peyzaj Mimarlığı": "Department of Landscape Architecture",
    "Enerji Bilimi ve Teknolojileri": "Department of Energy Science and Technologies",
    "İş Sağlığı ve Güvenliği": "Department of Occupational Health and Safety",
    "Uygulamalı Bilimler ve Teknoloji": "Department of Applied Sciences and Technology",
}
PROGRAM_TR = {name: f"{name} Programı" for name in DEPARTMENT_OPTIONS}
PROGRAM_EN = {name: value.replace("Department of ", "") + " Programme" for name, value in DEPARTMENT_EN.items()}
DEFAULT_FORM_PLACEHOLDERS = {
    "anabilimdali_tr": "",
    "anabilimdali_en": "",
    "program_tr": "",
    "program_en": "",
}
UI = {
    "tr": {
        "title": "İnönü FBE Tez Asistanı",
        "subtitle": "LaTeX tez hazırlama, akıllı denetim ve teslim süreçlerini tek panelden yönetin.",
        "thesis_language": "Tez dili",
        "source_style": "Tez stili",
        "degree": "Tez türü",
        "decimal_separator": "Ondalık ayırıcı",
        "page_layout": "Sayfa düzeni",
        "engine": "Derleme motoru",
        "language": "Arayüz",
        "theme": "Tema",
        "spine": "Sırt kapak",
        "info_tab": "Tez Bilgileri",
        "cover_tab": "Kapak ve Tez Kimliği",
        "approval_tab": "Kabul-Onay ve Jüri",
        "missing_tab": "Teslim Kontrolü",
        "system_tab": "Sistem",
        "run_tab": "TeX ve Yazım",
        "preview_cover": "Kapak Önizleme",
        "preview_approval": "Kabul-Onay Önizleme",
        "work_folder": "Çalışma klasörü",
        "choose_folder": "Seç",
    },
    "en": {
        "title": "Inonu FBE Thesis Assistant",
        "subtitle": "Manage LaTeX thesis preparation, smart checks and delivery from one panel.",
        "thesis_language": "Thesis language",
        "source_style": "Thesis style",
        "degree": "Degree",
        "decimal_separator": "Decimal mark",
        "page_layout": "Page layout",
        "engine": "Build engine",
        "language": "Interface",
        "theme": "Theme",
        "spine": "Spine cover",
        "info_tab": "Thesis Details",
        "cover_tab": "Cover and Thesis Identity",
        "approval_tab": "Approval and Jury",
        "missing_tab": "Delivery Checks",
        "system_tab": "System",
        "run_tab": "TeX and Writing",
        "preview_cover": "Cover Preview",
        "preview_approval": "Approval Preview",
        "work_folder": "Working folder",
        "choose_folder": "Choose",
    },
}
TOOLTIPS = {
    "tr": {
        "read": "tez.tex dosyasındaki mevcut kapak bilgilerini forma aktarır.",
        "save_json": "Formdaki bilgileri kaydeder ve tez.tex dosyasına güvenli biçimde yazar.",
        "safe_write": "Formdaki bilgileri kaydeder ve tez.tex dosyasına güvenli biçimde yazar.",
        "autosave": "Değişiklikleri kısa aralıklarla otomatik olarak tez-bilgileri.json ve tez.tex dosyalarına kaydeder.",
        "undo": "Formdaki son otomatik kayıt değişikliğini geri alır.",
        "redo": "Geri alınan son değişikliği yeniden uygular.",
        "preview": "tez.tex dosyasını değiştirmeden yazılacak farkları gösterir.",
        "open_folder": "Seçili tez çalışma klasörünü açar.",
        "choose_folder": "Üzerinde çalışılacak tez klasörünü seçer.",
        "missing_report": "Eksik-bilgiler.md raporunu üretir ve tıklanabilir eksik listesini gösterir.",
        "check": "Derleme ve uygunluk kontrollerini çalıştırır.",
        "diagnostics": "LaTeX derleme hatalarını logdan okuyup dosya, satır ve çözüm önerisiyle listeler.",
        "package": "Teslim paketi klasörünü hazırlar.",
        "clean": "Derleme sırasında oluşan ara dosyaları temizler.",
        "open_pdf": "Üretilen PDF/teslim klasörünü açar.",
        "convert_legacy": "Eski şablonla hazırlanmış tez klasörünü yeni şablonlu ayrı bir çalışma klasörüne dönüştürür.",
        "ai_declaration": "Üretken Yapay Zekâ Beyanı metnini hazırlar veya düzenler.",
        "writing_check": "Tez metni için yerel yazım ön denetimi yapar ve işaretli PDF önizlemesi üretir.",
        "guideline_check": "PDF çıktısını tez yazım kılavuzunun ölçülebilir kurallarına göre denetler.",
        "theorem_envs": "defs.tex içindeki teorem, ispat/kanıt ve benzeri matematik ortamlarını düzenler.",
        "update_app": "GitHub üzerinden güvenli güncelleme kontrolü yapar; yerel değişiklik varsa dosyaları ezmeden raporlar.",
        "spine_cover": "PDF ve teslim paketi oluşturulurken sırt kapağı da hazırlansın.",
    },
    "en": {
        "read": "Loads the current cover data from tez.tex into the form.",
        "save_json": "Saves the form data and safely writes it into tez.tex.",
        "safe_write": "Saves the form data and safely writes it into tez.tex.",
        "autosave": "Automatically saves changes to tez-bilgileri.json and tez.tex after a short delay.",
        "undo": "Reverts the last automatically saved form change.",
        "redo": "Reapplies the last reverted form change.",
        "preview": "Shows the changes that would be written without editing tez.tex.",
        "open_folder": "Opens the selected thesis working folder.",
        "choose_folder": "Chooses the thesis folder to work on.",
        "missing_report": "Creates eksik-bilgiler.md and shows a clickable missing-information list.",
        "check": "Runs build and compliance checks.",
        "diagnostics": "Reads LaTeX build errors from the log and lists file, line and suggested fixes.",
        "package": "Prepares the delivery package folder.",
        "clean": "Cleans intermediate files created during builds.",
        "open_pdf": "Opens the generated PDF/delivery folder.",
        "convert_legacy": "Converts an old-template thesis folder into a separate new-template working folder.",
        "ai_declaration": "Prepares or edits the generative AI declaration text.",
        "writing_check": "Creates a local writing pre-check and an annotated PDF preview for the thesis text.",
        "guideline_check": "Checks the PDF output against measurable thesis-guide rules.",
        "theorem_envs": "Edits theorem, proof and related mathematical environments in defs.tex.",
        "update_app": "Checks GitHub for a safe update and reports without overwriting local changes.",
        "spine_cover": "Also prepares the spine cover during PDF and delivery steps.",
    },
}
THEMES = {
    "Açık": {"bg": "#FFFFFF", "panel": "#FFFFFF", "line": "#DDE7EA", "soft_line": "#EAF1F3", "fg": "#17343A", "muted": "#6B6D67", "accent": "#14697A", "accent_dark": "#7A642E", "alt": "#F8FAFA", "text_bg": "#FBFBF9", "input_bg": "#FCFAF5", "text_fg": "#17343A"},
    "Koyu": {"bg": "#101820", "panel": "#16232C", "line": "#36505A", "soft_line": "#243943", "fg": "#E7F0F2", "muted": "#A9BBC1", "accent": "#39AFC0", "accent_dark": "#78D4DE", "alt": "#1D2E38", "text_bg": "#16232C", "input_bg": "#10252E", "text_fg": "#E7F0F2"},
}

PLACEHOLDER_PATTERNS = [
    "123456789", "Varsa Unvan", "Department Name", "Programme Name",
    "TEZ.IN SAVUNULDU", "MONTH YEAR", "GG/AA/YYYY", "YYYY/KK",
    "Ad{\\i} SOYADI", "Adı SOYADI", "Name SURNAME", "TEZ \\c{S}ABLONU",
    "TEZ ŞABLONU", "INONU UNIVERSITY THESIS TEMPLATE", "Öğrenci Adı",
    "Öğrenci Soyadı", "Tez Başlığı", "Thesis Title", "Anabilim Dalı Adı",
    "Program Adı", "Prof. Dr. Adı SOYADI", "Prof. Dr. Name SURNAME",
]

LATEX_SPECIAL_CHARS = {
    "\\": "\\textbackslash{}",
    "{": "\\{",
    "}": "\\}",
    "#": "\\#",
    "$": "\\$",
    "%": "\\%",
    "&": "\\&",
    "_": "\\_",
    "~": "\\textasciitilde{}",
    "^": "\\textasciicircum{}",
}

LATEX_TO_TEXT = [
    ("{\\i}", "ı"), ("\\.I", "İ"), ("\\u{g}", "ğ"), ("\\u{G}", "Ğ"),
    ('\\"u', "ü"), ('\\"U', "Ü"), ('\\"o', "ö"), ('\\"O', "Ö"),
    ("\\c{s}", "ş"), ("\\c{S}", "Ş"), ("\\c{c}", "ç"), ("\\c{C}", "Ç"),
    ("\\{", "{"), ("\\}", "}"), ("\\#", "#"), ("\\$", "$"),
    ("\\%", "%"), ("\\&", "&"), ("\\_", "_"),
]

MONTHS = [
    ("Ocak", "January"),
    ("Şubat", "February"),
    ("Mart", "March"),
    ("Nisan", "April"),
    ("Mayıs", "May"),
    ("Haziran", "June"),
    ("Temmuz", "July"),
    ("Ağustos", "August"),
    ("Eylül", "September"),
    ("Ekim", "October"),
    ("Kasım", "November"),
    ("Aralık", "December"),
]
TR_MONTHS = [month[0] for month in MONTHS]
EN_MONTHS = [month[1] for month in MONTHS]


def compact_month_key(value):
    compact = re.sub(r"\s+", "", value.strip().casefold())
    normalized = unicodedata.normalize("NFKD", compact)
    ascii_like = "".join(char for char in normalized if not unicodedata.combining(char))
    return ascii_like.replace("ı", "i")


MONTH_COMPACT_LOOKUP = {compact_month_key(name): index for index, name in enumerate(TR_MONTHS + EN_MONTHS)}
TITLE_TRANSLATIONS = [
    (re.compile(r"\bProf\.\s*Dr\.", re.I), "Prof. Dr."),
    (re.compile(r"\bDoç\.\s*Dr\.", re.I), "Assoc. Prof. Dr."),
    (re.compile(r"\bDoc\.\s*Dr\.", re.I), "Assoc. Prof. Dr."),
    (re.compile(r"\bDr\.\s*Öğr\.\s*Üyesi\b", re.I), "Assist. Prof. Dr."),
    (re.compile(r"\bDr\.\s*Ogr\.\s*Uyesi\b", re.I), "Assist. Prof. Dr."),
    (re.compile(r"\bÖğr\.\s*Gör\.\s*Dr\.", re.I), "Lect. Dr."),
    (re.compile(r"\bOgr\.\s*Gor\.\s*Dr\.", re.I), "Lect. Dr."),
    (re.compile(r"\bArş\.\s*Gör\.", re.I), "Res. Assist."),
    (re.compile(r"\bArs\.\s*Gor\.", re.I), "Res. Assist."),
]
INSTITUTION_TRANSLATIONS = {
    "İnönü Üniversitesi": "İnönü University",
    "Inonu Universitesi": "İnönü University",
    "Inonu University": "İnönü University",
}
THEOREM_BLOCK_START = "% BEGIN TEZ_GUI_THEOREM_ENVIRONMENTS"
THEOREM_BLOCK_END = "% END TEZ_GUI_THEOREM_ENVIRONMENTS"
APA_SUPPORT_START = "% BEGIN TEZ_GUI_APA_SUPPORT"
APA_SUPPORT_END = "% END TEZ_GUI_APA_SUPPORT"
THEOREM_STYLES = ["plain", "definition", "remark"]
THEOREM_COUNTER_WITHIN = {"chapter", "section", "subsection"}
DEFAULT_THEOREM_ROWS = [
    {"style": "plain", "env": "theorem", "title": "Teorem", "counter": "section"},
    {"style": "plain", "env": "lemma", "title": "Lemma", "counter": "theorem"},
    {"style": "plain", "env": "proposition", "title": "Önerme", "counter": "theorem"},
    {"style": "plain", "env": "corollary", "title": "Sonuç", "counter": "theorem"},
    {"style": "definition", "env": "definition", "title": "Tanım", "counter": "theorem"},
    {"style": "definition", "env": "example", "title": "Örnek", "counter": "theorem"},
    {"style": "definition", "env": "problem", "title": "Problem", "counter": "theorem"},
    {"style": "remark", "env": "remark", "title": "Uyarı", "counter": "theorem"},
]
SKIP_FORM_KEYS = {
    "tarih_tr", "tarih_en", "tarih_kucuk_tr", "tarih_kucuk_en",
    "tezverme_tr", "tezverme_en", "savunma_tr", "savunma_en", "kurul_tarih",
}
DATE_FORM_KEYS = {"tarih_tr", "tezverme_tr", "savunma_tr", "kurul_tarih"}
JURY_EXTRA_KEYS = {"juri4", "juri4_kurum", "juri5", "juri5_kurum"}
AUTO_DERIVED_KEYS = {
    "anabilimdali_en",
    "danisman_en", "danisman_kurum_en",
    "esdanisman_en", "esdanisman_kurum_en",
}
FORMAT_HINTS = {
    "ad": "Öğrenci Adı",
    "soyad": "Öğrenci Soyadı",
    "ogrencino": "Yalnız rakam",
    "unvan": "Varsa unvan/mezuniyet bilgisi",
    "anabilimdali_tr": "",
    "anabilimdali_en": "Anabilim dalından otomatik doldurulur",
    "program_tr": "Anabilim dalından otomatik doldurulur",
    "program_en": "Anabilim dalından otomatik doldurulur",
    "baslik1": "Tez Başlığı 1. Satır",
    "baslik2": "Gerekliyse 2. satır",
    "baslik3": "Gerekliyse 3. satır",
    "title1": "Thesis Title Line 1",
    "title2": "2nd line if necessary",
    "title3": "3rd line if necessary",
    "danisman_tr": "Prof. Dr. Adı SOYADI",
    "danisman_kurum_tr": "İnönü Üniversitesi",
    "danisman_en": "Danışmandan otomatik doldurulur",
    "danisman_kurum_en": "Danışman kurumundan otomatik doldurulur",
    "esdanisman_tr": "Varsa eş danışman",
    "esdanisman_kurum_tr": "Varsa eş danışman kurumu",
    "esdanisman_en": "Eş danışmandan otomatik doldurulur",
    "esdanisman_kurum_en": "Eş danışman kurumundan otomatik doldurulur",
    "kapakyili": "Örnek: 2026",
    "oy": "Örnek: oy birliği",
    "kurul_no": "Örnek: 2026/12",
    "mudur": "Prof. Dr. Süleyman KÖYTEPE",
    "juri1": "Jüri 1 Adı SOYADI",
    "juri1_kurum": "Jüri 1 Kurumu",
    "juri2": "Jüri 2 Adı SOYADI",
    "juri2_kurum": "Jüri 2 Kurumu",
    "juri3": "Jüri 3 Adı SOYADI",
    "juri3_kurum": "Jüri 3 Kurumu",
    "juri4": "Jüri 4 Adı SOYADI",
    "juri4_kurum": "Jüri 4 Kurumu",
    "juri5": "Jüri 5 Adı SOYADI",
    "juri5_kurum": "Jüri 5 Kurumu",
    "anahtarkelimeler": "Örnek: Optimizasyon, Modelleme, LaTeX",
    "keywords": "Example: Optimization, Modelling, LaTeX",
    "bap_proje_no": "Örnek: FBA-2026-1234; BAP desteği yoksa boş bırakın.",
}
FORMAT_HINTS_EN = {
    "ad": "Student Name",
    "soyad": "SURNAME",
    "ogrencino": "Digits only",
    "unvan": "Optional title",
    "anabilimdali_tr": "",
    "anabilimdali_en": "Filled automatically from department",
    "program_tr": "Filled automatically from department",
    "program_en": "Filled automatically from department",
    "baslik1": "Turkish title line 1",
    "baslik2": "Turkish title line 2",
    "baslik3": "Turkish title line 3",
    "title1": "English title line 1",
    "title2": "English title line 2",
    "title3": "English title line 3",
    "kapakyili": "Example: 2026",
    "kapaksehri": "Example: MALATYA",
    "oy": "Select unanimous / majority",
    "kurul_no": "Example: 2026/12",
    "mudur": "Default director name",
    "danisman_tr": "Prof. Dr. Adı SOYADI",
    "danisman_kurum_tr": "İnönü Üniversitesi",
    "danisman_en": "Filled automatically from advisor",
    "danisman_kurum_en": "Filled automatically from advisor institution",
    "esdanisman_tr": "Co-advisor if any",
    "esdanisman_kurum_tr": "Co-advisor institution if any",
    "esdanisman_en": "Filled automatically from co-advisor",
    "esdanisman_kurum_en": "Filled automatically from co-advisor institution",
    "anahtarkelimeler": "Example: Optimizasyon, Modelleme, LaTeX",
    "keywords": "Example: Optimization, Modelling, LaTeX",
    "bap_proje_no": "Example: FBA-2026-1234; leave blank if not supported.",
}
TEX_TOOL_GROUPS = {
    "Matematik": [
        ("Σ", r"\sum ", "Toplam"), ("Π", r"\prod ", "Çarpım"), ("∫", r"\int ", "İntegral"), ("∮", r"\oint ", "Kapalı integral"),
        ("∂", r"\partial ", "Kısmi türev"), ("∇", r"\nabla ", "Nabla"), ("√", r"\sqrt{|}", "Karekök"), ("ⁿ√", r"\sqrt[|]{}", "n. kök"),
        ("a/b", r"\frac{|}{}", "Kesir"), ("xⁿ", r"^{|}", "Üst indis"), ("xₙ", r"_{|}", "Alt indis"), ("xₙⁿ", r"_{|}^{}", "Alt/üst indis"),
        ("lim", r"\lim_{|} ", "Limit"), ("min", r"\min_{|} ", "Minimum"), ("max", r"\max_{|} ", "Maksimum"), ("log", r"\log ", "Logaritma"),
        ("sin", r"\sin ", "Sinüs"), ("cos", r"\cos ", "Kosinüs"), ("tan", r"\tan ", "Tanjant"), ("exp", r"\exp ", "Üstel"),
        ("∞", r"\infty ", "Sonsuz"), ("∀", r"\forall ", "Her"), ("∃", r"\exists ", "Vardır"), ("∄", r"\nexists ", "Yoktur"),
        ("∈", r"\in ", "Elemanıdır"), ("∉", r"\notin ", "Elemanı değildir"), ("∅", r"\emptyset ", "Boş küme"), ("∩", r"\cap ", "Kesişim"),
        ("∪", r"\cup ", "Birleşim"), ("⊂", r"\subset ", "Alt küme"), ("⊆", r"\subseteq ", "Alt/eşit küme"), ("⊃", r"\supset ", "Üst küme"),
        ("⊇", r"\supseteq ", "Üst/eşit küme"), ("ℕ", r"\mathbb{N}", "Doğal sayılar"), ("ℤ", r"\mathbb{Z}", "Tam sayılar"), ("ℚ", r"\mathbb{Q}", "Rasyonel"),
        ("ℝ", r"\mathbb{R}", "Reel"), ("ℂ", r"\mathbb{C}", "Kompleks"), ("( )", r"\left( |\right)", "Parantez"), ("[ ]", r"\left[ |\right]", "Köşeli parantez"),
        ("{ }", r"\left\{ |\right\}", "Küme parantezi"), ("| |", r"\left| |\right|", "Mutlak değer"), ("eq", "\\begin{equation}\n|\n\\end{equation}", "Denklem"),
    ],
    "Yunan": [
        ("α", r"\alpha ", "alpha"), ("β", r"\beta ", "beta"), ("γ", r"\gamma ", "gamma"), ("δ", r"\delta ", "delta"),
        ("ε", r"\varepsilon ", "epsilon"), ("ζ", r"\zeta ", "zeta"), ("η", r"\eta ", "eta"), ("θ", r"\theta ", "theta"),
        ("ϑ", r"\vartheta ", "vartheta"), ("ι", r"\iota ", "iota"), ("κ", r"\kappa ", "kappa"), ("λ", r"\lambda ", "lambda"),
        ("μ", r"\mu ", "mu"), ("ν", r"\nu ", "nu"), ("ξ", r"\xi ", "xi"), ("π", r"\pi ", "pi"),
        ("ϖ", r"\varpi ", "varpi"), ("ρ", r"\rho ", "rho"), ("ϱ", r"\varrho ", "varrho"), ("σ", r"\sigma ", "sigma"),
        ("ς", r"\varsigma ", "varsigma"), ("τ", r"\tau ", "tau"), ("υ", r"\upsilon ", "upsilon"), ("φ", r"\varphi ", "varphi"),
        ("ϕ", r"\phi ", "phi"), ("χ", r"\chi ", "chi"), ("ψ", r"\psi ", "psi"), ("ω", r"\omega ", "omega"),
        ("Γ", r"\Gamma ", "Gamma"), ("Δ", r"\Delta ", "Delta"), ("Θ", r"\Theta ", "Theta"), ("Λ", r"\Lambda ", "Lambda"),
        ("Ξ", r"\Xi ", "Xi"), ("Π", r"\Pi ", "Pi"), ("Σ", r"\Sigma ", "Sigma"), ("Υ", r"\Upsilon ", "Upsilon"),
        ("Φ", r"\Phi ", "Phi"), ("Ψ", r"\Psi ", "Psi"), ("Ω", r"\Omega ", "Omega"),
    ],
    "İlişkiler": [
        ("=", "=", "Eşit"), ("≠", r"\neq ", "Eşit değil"), ("<", "<", "Küçük"), (">", ">", "Büyük"),
        ("≤", r"\leq ", "Küçük/eşit"), ("≥", r"\geq ", "Büyük/eşit"), ("≪", r"\ll ", "Çok küçük"), ("≫", r"\gg ", "Çok büyük"),
        ("≈", r"\approx ", "Yaklaşık"), ("≃", r"\simeq ", "Benzer/eşit"), ("≅", r"\cong ", "Kongruent"), ("≡", r"\equiv ", "Denk"),
        ("∼", r"\sim ", "Benzer"), ("∝", r"\propto ", "Orantılı"), ("⊥", r"\perp ", "Dik"), ("∥", r"\parallel ", "Paralel"),
        ("∣", r"\mid ", "Böler"), ("∤", r"\nmid ", "Bölmez"), ("⊢", r"\vdash ", "vdash"), ("⊨", r"\models ", "models"),
        ("≺", r"\prec ", "Öncelenir"), ("≻", r"\succ ", "Ardıllanır"), ("⪯", r"\preceq ", "Öncelenir/eşit"), ("⪰", r"\succeq ", "Ardıllanır/eşit"),
        ("⊆", r"\subseteq ", "Alt küme/eşit"), ("⊇", r"\supseteq ", "Üst küme/eşit"), ("⊄", r"\nsubseteq ", "Alt küme değil"), ("⊅", r"\nsupseteq ", "Üst küme değil"),
    ],
    "Oklar": [
        ("←", r"\leftarrow ", "Sol ok"), ("→", r"\rightarrow ", "Sağ ok"), ("↔", r"\leftrightarrow ", "Çift yönlü ok"), ("⇐", r"\Leftarrow ", "Kalın sol ok"),
        ("⇒", r"\Rightarrow ", "Kalın sağ ok"), ("⇔", r"\Leftrightarrow ", "Kalın çift yönlü"), ("↦", r"\mapsto ", "Mapsto"), ("↩", r"\hookleftarrow ", "Hook left"),
        ("↪", r"\hookrightarrow ", "Hook right"), ("↗", r"\nearrow ", "Kuzeydoğu"), ("↘", r"\searrow ", "Güneydoğu"), ("↙", r"\swarrow ", "Güneybatı"),
        ("↖", r"\nwarrow ", "Kuzeybatı"), ("↑", r"\uparrow ", "Yukarı"), ("↓", r"\downarrow ", "Aşağı"), ("↕", r"\updownarrow ", "Yukarı/aşağı"),
        ("⇑", r"\Uparrow ", "Kalın yukarı"), ("⇓", r"\Downarrow ", "Kalın aşağı"), ("⇕", r"\Updownarrow ", "Kalın yukarı/aşağı"),
        ("⟵", r"\longleftarrow ", "Uzun sol"), ("⟶", r"\longrightarrow ", "Uzun sağ"), ("⟷", r"\longleftrightarrow ", "Uzun çift"),
        ("⟸", r"\Longleftarrow ", "Uzun kalın sol"), ("⟹", r"\Longrightarrow ", "Uzun kalın sağ"), ("⟺", r"\Longleftrightarrow ", "Uzun kalın çift"),
    ],
    "İşlemler": [
        ("±", r"\pm ", "Artı/eksi"), ("∓", r"\mp ", "Eksi/artı"), ("×", r"\times ", "Çarpı"), ("÷", r"\div ", "Bölü"),
        ("·", r"\cdot ", "Nokta çarpım"), ("∗", r"\ast ", "Asterisk"), ("⋆", r"\star ", "Star"), ("∘", r"\circ ", "Bileşke"),
        ("∙", r"\bullet ", "Bullet"), ("⊕", r"\oplus ", "Oplus"), ("⊖", r"\ominus ", "Ominus"), ("⊗", r"\otimes ", "Otimes"),
        ("⊘", r"\oslash ", "Oslash"), ("⊙", r"\odot ", "Odot"), ("∧", r"\wedge ", "Ve"), ("∨", r"\vee ", "Veya"),
        ("¬", r"\neg ", "Değil"), ("⊻", r"\veebar ", "Xor"), ("∴", r"\therefore ", "Dolayısıyla"), ("∵", r"\because ", "Çünkü"),
    ],
    "Latin": [
        ("Ç", r"\c{C}", "Ç"), ("ç", r"\c{c}", "ç"), ("Ğ", r"\u{G}", "Ğ"), ("ğ", r"\u{g}", "ğ"),
        ("İ", r"\.{I}", "İ"), ("ı", r"\i{}", "ı"), ("Ö", r"\"{O}", "Ö"), ("ö", r"\"{o}", "ö"),
        ("Ş", r"\c{S}", "Ş"), ("ş", r"\c{s}", "ş"), ("Ü", r"\"{U}", "Ü"), ("ü", r"\"{u}", "ü"),
        ("Á", r"\'{A}", "Á"), ("á", r"\'{a}", "á"), ("É", r"\'{E}", "É"), ("é", r"\'{e}", "é"),
        ("Ñ", r"\~{N}", "Ñ"), ("ñ", r"\~{n}", "ñ"), ("Ø", r"\O{}", "Ø"), ("ø", r"\o{}", "ø"),
        ("Æ", r"\AE{}", "Æ"), ("æ", r"\ae{}", "æ"), ("Œ", r"\OE{}", "Œ"), ("œ", r"\oe{}", "œ"),
    ],
    "Biçim": [
        ("B", r"\textbf{|}", "Kalın"), ("I", r"\textit{|}", "İtalik"), ("U", r"\underline{|}", "Altı çizili"), ("em", r"\emph{|}", "Vurgu"),
        ("sf", r"\textsf{|}", "Sans serif"), ("tt", r"\texttt{|}", "Daktilo"), ("rm", r"\textrm{|}", "Roman"), ("sc", r"\textsc{|}", "Küçük büyük harf"),
        ("hat", r"\hat{|}", "Şapka"), ("bar", r"\bar{|}", "Üst çizgi"), ("vec", r"\vec{|}", "Vektör"), ("dot", r"\dot{|}", "Nokta"),
        ("tilde", r"\tilde{|}", "Tilde"), ("overline", r"\overline{|}", "Uzun üst çizgi"),
    ],
    "Tez": [
        ("cite", r"\cite{|}", "Kaynak atfı"), ("pcite", r"\parencite{|}", "Parantezli atıf"), ("tcite", r"\textcite{|}", "Metin içi atıf"),
        ("ref", r"\ref{|}", "Gönderme"), ("eqref", r"\eqref{|}", "Denklem göndermesi"), ("pageref", r"\pageref{|}", "Sayfa göndermesi"),
        ("label", r"\label{|}", "Etiket"), ("url", r"\url{|}", "URL"), ("%", r"\%", "Yüzde"), ("_", r"\_", "Alt çizgi"),
        ("&", r"\&", "Ve işareti"), ("#", r"\#", "Kare"), ("$", r"\$", "Dolar"), ("{}", r"\{| \}", "Süslü parantez"),
        ("Şekil", r"Şekil~\ref{|}", "Şekil göndermesi"), ("Tablo", r"Tablo~\ref{|}", "Tablo göndermesi"), ("Denklem", r"Denklem~\eqref{|}", "Denklem göndermesi"),
    ],
}
SECTION_NOTES = {
    "Başlık": {
        "tr": "Tez başlığı, tez önerisinde verilen başlık ile tamamen aynı olmalıdır",
        "en": "The thesis title must match the title approved in the thesis proposal exactly",
    }
}
SECTION_LABEL_EN = {
    "Öğrenci": "Student",
    "Program": "Programme",
    "Başlık": "Title",
    "Anahtar Kelimeler": "Keywords",
    "Danışman": "Advisor",
    "Tarih ve Karar": "Date and Decision",
    "Jüri": "Jury",
}
FIELD_LABEL_EN = {
    "ad": "Name",
    "soyad": "Surname",
    "ogrencino": "Student No",
    "unvan": "Title/graduation note if any",
    "anabilimdali_tr": "Department (Turkish)",
    "anabilimdali_en": "Department (English)",
    "program_tr": "Programme (Turkish)",
    "program_en": "Programme (English)",
    "baslik1": "Turkish Title Line 1",
    "baslik2": "Turkish Title Line 2",
    "baslik3": "Turkish Title Line 3",
    "title1": "English Title Line 1",
    "title2": "English Title Line 2",
    "title3": "English Title Line 3",
    "anahtarkelimeler": "Turkish Keywords",
    "keywords": "English Keywords",
    "danisman_tr": "Advisor (Turkish)",
    "danisman_kurum_tr": "Advisor Institution (Turkish)",
    "danisman_en": "Advisor (English)",
    "danisman_kurum_en": "Advisor Institution (English)",
    "bap_proje_no": "BAP Project No",
    "esdanisman_tr": "Co-advisor (Turkish)",
    "esdanisman_kurum_tr": "Co-advisor Institution (Turkish)",
    "esdanisman_en": "Co-advisor (English)",
    "esdanisman_kurum_en": "Co-advisor Institution (English)",
    "tarih_tr": "Defense Month/Year",
    "tezverme_tr": "Thesis Submission Date",
    "savunma_tr": "Defense Date",
    "kapakyili": "Cover Year",
    "kapaksehri": "Cover City",
    "oy": "Vote Status",
    "kurul_tarih": "Executive Board Date",
    "kurul_no": "Executive Board Decision No",
    "mudur": "Institute Director",
    "juri1": "Jury 1", "juri1_kurum": "Jury 1 Institution",
    "juri2": "Jury 2", "juri2_kurum": "Jury 2 Institution",
    "juri3": "Jury 3", "juri3_kurum": "Jury 3 Institution",
    "juri4": "Jury 4", "juri4_kurum": "Jury 4 Institution",
    "juri5": "Jury 5", "juri5_kurum": "Jury 5 Institution",
}

FIELDS = [
    ("Öğrenci", [
        ("ad", "Ad", "yazar", 0),
        ("soyad", "Soyad", "yazar", 1),
        ("ogrencino", "Öğrenci No", "ogrencino", 0),
        ("unvan", "Varsa unvan/mezuniyet bilgisi", "unvan", 0),
    ]),
    ("Program", [
        ("anabilimdali_tr", "Anabilim Dalı", "anabilimdali", 0),
        ("anabilimdali_en", "Department", "anabilimdali", 1),
        ("program_tr", "Program", "programi", 0),
        ("program_en", "Programme", "programi", 1),
    ]),
    ("Başlık", [
        ("baslik1", "Türkçe Başlık 1. Satır", "baslik", 0),
        ("baslik2", "Türkçe Başlık 2. Satır", "baslik", 1),
        ("baslik3", "Türkçe Başlık 3. Satır", "baslik", 2),
        ("title1", "İngilizce Başlık 1. Satır", "title", 0),
        ("title2", "İngilizce Başlık 2. Satır", "title", 1),
        ("title3", "İngilizce Başlık 3. Satır", "title", 2),
    ]),
    ("Anahtar Kelimeler", [
        ("anahtarkelimeler", "Anahtar Kelimeler", "anahtarkelimeler", 0),
        ("keywords", "Keywords", "keywords", 0),
    ]),
    ("Danışman", [
        ("danisman_tr", "Danışman", "tezyoneticisi", 0),
        ("danisman_kurum_tr", "Danışman Kurumu", "tezyoneticisi", 1),
        ("danisman_en", "Advisor", "tezyoneticisiENG", 0),
        ("danisman_kurum_en", "Advisor Institution", "tezyoneticisiENG", 1),
        ("bap_proje_no", "BAP Proje No", "bapdestegi", 0),
        ("esdanisman_tr", "Eş Danışman", "esdanismani", 0),
        ("esdanisman_kurum_tr", "Eş Danışman Kurumu", "esdanismani", 1),
        ("esdanisman_en", "Co-advisor", "esdanismaniENG", 0),
        ("esdanisman_kurum_en", "Co-advisor Institution", "esdanismaniENG", 1),
    ]),
    ("Tarih ve Karar", [
        ("tarih_tr", "Savunma Ay/Yıl", "tarih", 0),
        ("tarih_en", "Defense Month/Year", "tarih", 1),
        ("tarih_kucuk_tr", "Savunma ay/yıl küçük yazım", "tarihKucuk", 0),
        ("tarih_kucuk_en", "Defense month/year lower", "tarihKucuk", 1),
        ("tezverme_tr", "Tez Verme Tarihi", "tezvermetarih", 0),
        ("tezverme_en", "Thesis Submission Date", "tezvermetarih", 1),
        ("savunma_tr", "Savunma Tarihi", "tezsavunmatarih", 0),
        ("savunma_en", "Defense Date", "tezsavunmatarih", 1),
        ("kapakyili", "Kapak Yılı", "kapakyili", 0),
        ("kapaksehri", "Kapak Şehri", "kapaksehri", 0),
        ("oy", "Oy Durumu", "oy", 0),
        ("kurul_tarih", "Yönetim Kurulu Tarihi", "yonetimkurulukarar", 0),
        ("kurul_no", "Yönetim Kurulu Karar No", "yonetimkurulukarar", 1),
        ("mudur", "Enstitü Müdürü", "EnstituMuduru", 0),
    ]),
    ("Jüri", [
        ("juri1", "Jüri 1", "juriBir", 0), ("juri1_kurum", "Jüri 1 Kurum", "juriBir", 1),
        ("juri2", "Jüri 2", "juriIki", 0), ("juri2_kurum", "Jüri 2 Kurum", "juriIki", 1),
        ("juri3", "Jüri 3", "juriUc", 0), ("juri3_kurum", "Jüri 3 Kurum", "juriUc", 1),
        ("juri4", "Jüri 4", "juriDort", 0), ("juri4_kurum", "Jüri 4 Kurum", "juriDort", 1),
        ("juri5", "Jüri 5", "juriBes", 0), ("juri5_kurum", "Jüri 5 Kurum", "juriBes", 1),
    ]),
]


def latex_escape(text):
    value = re.sub(r"\s+", " ", text.strip())
    return "".join(LATEX_SPECIAL_CHARS.get(char, char) for char in value)


def latex_to_text(text):
    value = str(text or "").strip()
    for old, new in LATEX_TO_TEXT:
        value = value.replace(old, new)
    value = value.replace("\\textbackslash{}", "\\")
    return re.sub(r"\s+", " ", value).strip()


def normalize_program_compare(value):
    text = latex_to_text(value or "")
    text = unicodedata.normalize("NFKD", text.casefold())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    replacements = {
        "anabilim dali": "", "ana bilim dali": "", "abd": "",
        "programi": "", "program": "", "bolumu": "", "bolum": "", ".": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"[^a-z0-9]+", "", text)


def program_same_as_department(program, department):
    p = normalize_program_compare(program)
    d = normalize_program_compare(department)
    if not p or not d:
        return True
    return p == d or p in d or d in p


def ensure_program_suffix_tr(value):
    text = normalize_punctuation_spacing(latex_to_text(value or ""))
    if not text:
        return ""
    return text if re.search(r"\bProgramı\b$", text, flags=re.I) else text + " Programı"


def ensure_program_suffix_en(value):
    text = normalize_punctuation_spacing(latex_to_text(value or ""))
    if not text:
        return ""
    return text if re.search(r"\bProgramme\b$", text, flags=re.I) else text + " Programme"


def translate_program_to_english(value):
    text = normalize_punctuation_spacing(latex_to_text(value or ""))
    if not text:
        return ""
    for tr_name, en_name in DEPARTMENT_EN.items():
        if program_same_as_department(text, tr_name):
            return PROGRAM_EN.get(tr_name, en_name.replace("Department of ", "") + " Programme")
    text = re.sub(r"\bProgramı\b$", "", text, flags=re.I).strip()
    return ensure_program_suffix_en(text)


def parse_day_month_year(text):
    value = latex_to_text(text)
    match = re.search(r"(\d{1,2})\s+([A-Za-zÇĞİÖŞÜçğıöşü ]+?)\s+(\d{4})", value)
    if not match:
        return "", TR_MONTHS[0], ""
    month = compact_month_key(match.group(2))
    index = MONTH_COMPACT_LOOKUP.get(month, 0)
    if index >= 12:
        index -= 12
    return match.group(1).zfill(2), TR_MONTHS[index], match.group(3)


def parse_month_year(text):
    value = latex_to_text(text)
    match = re.search(r"([A-Za-zÇĞİÖŞÜçğıöşü ]+?)\s+(\d{4})", value)
    if not match:
        return TR_MONTHS[0], ""
    month = compact_month_key(match.group(1))
    index = MONTH_COMPACT_LOOKUP.get(month, 0)
    if index >= 12:
        index -= 12
    return TR_MONTHS[index], match.group(2)


def format_date_pair(day, month, year):
    index = TR_MONTHS.index(month) if month in TR_MONTHS else 0
    day = day.zfill(2) if day else ""
    return [f"{day} {TR_MONTHS[index]} {year}".strip(), f"{day} {EN_MONTHS[index]} {year}".strip()]


def replace_marked_block(text, start_marker, end_marker, block_text):
    pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.S)
    if pattern.search(text):
        return pattern.sub(lambda _match: block_text.strip(), text)
    return text.rstrip() + "\n\n" + block_text.strip() + "\n"


def managed_block_or_text(text, start_marker, end_marker):
    pattern = re.compile(re.escape(start_marker) + r"(.*?)" + re.escape(end_marker), re.S)
    match = pattern.search(text)
    return match.group(1) if match else text


def parse_theorem_config(text):
    body = managed_block_or_text(text, THEOREM_BLOCK_START, THEOREM_BLOCK_END)
    proof_label = "Kanıt" if "Kanıt" in body else "İspat"
    rows = []
    current_style = "plain"
    for raw_line in body.splitlines():
        line = raw_line.strip()
        style_match = re.match(r"\\theoremstyle\{([^{}]+)\}", line)
        if style_match:
            current_style = style_match.group(1).strip()
            continue
        match = re.match(r"\\newtheorem\{([^{}]+)\}(?:\[([^\]]+)\])?\{([^{}]+)\}(?:\[([^\]]+)\])?", line)
        if not match:
            continue
        env, shared_counter, title, within_counter = match.groups()
        rows.append({
            "style": current_style if current_style in THEOREM_STYLES else "plain",
            "env": env.strip(),
            "title": title.strip(),
            "counter": (shared_counter or within_counter or "").strip(),
        })
    return rows or [row.copy() for row in DEFAULT_THEOREM_ROWS], proof_label


def theorem_rows_to_latex(rows, proof_label="İspat"):
    proof_label = "Kanıt" if proof_label == "Kanıt" else "İspat"
    lines = [
        THEOREM_BLOCK_START,
        r"\usepackage{amsthm}",
        r"\makeatletter",
        rf"\renewcommand{{\proofname}}{{\if@Ingilizce Proof\else {proof_label}\fi}}",
        r"\makeatother",
    ]
    current_style = None
    for row in rows:
        style = row.get("style", "plain") if row.get("style") in THEOREM_STYLES else "plain"
        env = row.get("env", "").strip()
        title = row.get("title", "").strip()
        counter = row.get("counter", "").strip()
        if not env or not title:
            continue
        if style != current_style:
            lines.append(fr"\theoremstyle{{{style}}}")
            current_style = style
        if counter in THEOREM_COUNTER_WITHIN:
            lines.append(fr"\newtheorem{{{env}}}{{{title}}}[{counter}]")
        elif counter:
            lines.append(fr"\newtheorem{{{env}}}[{counter}]{{{title}}}")
        else:
            lines.append(fr"\newtheorem{{{env}}}{{{title}}}")
    lines.append(THEOREM_BLOCK_END)
    return "\n".join(lines)


def apa_support_latex():
    return "\n".join([
        APA_SUPPORT_START,
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
        APA_SUPPORT_END,
    ])


def ensure_defs_apa_support(defs_path):
    text = yazim_denetimi.read_text(defs_path) if defs_path.exists() else ""
    if "style=apa" in text and "\\addbibresource" in text:
        return
    defs_path.write_text(replace_marked_block(text, APA_SUPPORT_START, APA_SUPPORT_END, apa_support_latex()), encoding="utf-8")


def days_in_month(month, year):
    if not year.isdigit() or len(year) != 4:
        return 31
    index = (TR_MONTHS.index(month) if month in TR_MONTHS else 0) + 1
    if index == 2:
        year_number = int(year)
        return 29 if (year_number % 4 == 0 and (year_number % 100 != 0 or year_number % 400 == 0)) else 28
    return 30 if index in (4, 6, 9, 11) else 31


def parse_macro_args(line):
    args = []
    i = 0
    while i < len(line):
        if line[i] != "{":
            i += 1
            continue
        depth = 1
        start = i + 1
        i += 1
        while i < len(line) and depth:
            if line[i] == "{":
                depth += 1
            elif line[i] == "}":
                depth -= 1
            i += 1
        args.append(line[start:i - 1])
    return args


def remove_latex_comments(text):
    """Remove LaTeX comments while preserving escaped percent signs and line breaks."""
    cleaned_lines = []
    for line in text.splitlines():
        out = []
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == "\\":
                if i + 1 < len(line):
                    out.append(line[i:i + 2])
                    i += 2
                    continue
            if ch == "%":
                break
            out.append(ch)
            i += 1
        cleaned_lines.append("".join(out))
    return "\n".join(cleaned_lines)


def parse_macro_args_from(text, start):
    args = []
    i = start
    while i < len(text):
        while i < len(text) and text[i].isspace():
            i += 1
        if i >= len(text) or text[i] != "{":
            break
        depth = 1
        arg_start = i + 1
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
        args.append(text[arg_start:i - 1])
    return args


def read_macros(tex_path):
    macros = {}
    text = tex_path.read_text(encoding="utf-8", errors="ignore")
    # Eski şablonda danışman vb. makrolar satır sonunda % açıklama ile bölünebiliyor.
    # Yorumları kaldırınca sonraki satırdaki {..}{..}{..} argümanları da okunur.
    text_no_comments = remove_latex_comments(text)
    for match in re.finditer(r"(?m)^\s*\\([A-Za-z]+)\s*\{", text_no_comments):
        macros[match.group(1)] = parse_macro_args_from(text_no_comments, match.end() - 1)
    return normalize_legacy_macros(macros)


def nonempty_args(values):
    return [latex_to_text(v) for v in (values or []) if latex_to_text(v)]


def split_legacy_title_args(values):
    args = nonempty_args(values)
    if not args:
        return ["", "", ""]
    return (args + ["", "", ""])[:3]


def normalize_legacy_macros(macros):
    """Map legacy İnönü thesis macros to the current GUI macro shape."""
    out = {key: list(value) for key, value in macros.items()}

    # Eski şablonda Türkçe büyük başlık \baslik içinde, İngilizce başlık ise \title içinde.
    if "baslik" in out:
        tr_lines = split_legacy_title_args(out.get("baslik", []))
        out["baslik"] = tr_lines
    if "title" in out:
        en_lines = split_legacy_title_args(out.get("title", []))
        out["title"] = en_lines
    else:
        for alt in ("baslikENG", "tezbasligiENG", "ingilizcebaslik", "englishTitle", "englishtitle"):
            if alt in out:
                out["title"] = split_legacy_title_args(out.get(alt, []))
                break

    # Eski \anahtarkelimeler{TR}{EN} -> yeni anahtarkelimeler + keywords.
    if "anahtarkelimeler" in out:
        vals = out.get("anahtarkelimeler", [])
        if len(vals) >= 2:
            out["anahtarkelimeler"] = [vals[0]]
            out["keywords"] = [vals[1]]
    for alt in ("keywords", "anahtarKelimelerENG", "keyWords", "Keyword", "Keywords"):
        if alt in out and not out.get("keywords"):
            out["keywords"] = [out[alt][0]] if out[alt] else [""]

    # Eski \tezyoneticisi{tr unvan}{tr ad}{tr kurum}{en unvan}{en ad}{en kurum}
    vals = out.get("tezyoneticisi", [])
    if len(vals) >= 6:
        out["tezyoneticisi"] = [f"{latex_to_text(vals[0])} {latex_to_text(vals[1])}".strip(), vals[2]]
        out["tezyoneticisiENG"] = [f"{latex_to_text(vals[3])} {latex_to_text(vals[4])}".strip(), vals[5]]
    elif len(vals) == 3:
        out["tezyoneticisi"] = [f"{latex_to_text(vals[0])} {latex_to_text(vals[1])}".strip(), vals[2]]

    # Eski eş danışman biçimi de benzer olabiliyor.
    for legacy_name, new_tr, new_en in (("esdanismani", "esdanismani", "esdanismaniENG"), ("ikincitezdanismani", "ikincitezdanismani", "ikincitezdanismaniENG")):
        vals = out.get(legacy_name, [])
        if len(vals) >= 6:
            out[new_tr] = [f"{latex_to_text(vals[0])} {latex_to_text(vals[1])}".strip(), vals[2]]
            out[new_en] = [f"{latex_to_text(vals[3])} {latex_to_text(vals[4])}".strip(), vals[5]]
        elif len(vals) == 3:
            out[new_tr] = [f"{latex_to_text(vals[0])} {latex_to_text(vals[1])}".strip(), vals[2]]

    return out

def macro_line(name, values):
    parts = []
    for value in values:
        compact = re.sub(r"\s+", " ", str(value).strip())
        parts.append("{" + compact + "}")
    return "\\" + name + "".join(parts)


def macro_end_line(lines, start_index):
    depth = 0
    started = False
    for index in range(start_index, len(lines)):
        line = lines[index]
        pos = 0
        while pos < len(line):
            char = line[pos]
            if char == "\\":
                pos += 2
                continue
            if char == "{":
                depth += 1
                started = True
            elif char == "}":
                depth -= 1
                if started and depth <= 0:
                    return index
            pos += 1
    return start_index


def orphan_continuation_end(lines, end_index):
    index = end_index
    while index + 1 < len(lines):
        nxt = lines[index + 1].strip()
        if not nxt or re.match(r"^\\[A-Za-z]+", nxt):
            break
        if nxt.endswith("}"):
            index += 1
            continue
        break
    return index


def write_macros_to_tex(tex_path, macros):
    if not tex_path.exists():
        return 0
    macro_names = [
        "yazar", "ogrencino", "unvan", "anabilimdali", "programi", "tarih",
        "tarihKucuk", "tezyoneticisi", "tezyoneticisiENG", "esdanismani",
        "esdanismaniENG", "bapdestegi", "baslik", "title", "anahtarkelimeler",
        "keywords", "tezvermetarih", "tezsavunmatarih", "kapakyili", "kapaksehri",
        "oy", "yonetimkurulukarar", "juriBir", "juriIki", "juriUc", "juriDort",
        "juriBes", "EnstituMuduru",
    ]
    lines = tex_path.read_text(encoding="utf-8").splitlines()
    changes = 0
    index = 0
    while index < len(lines):
        changed = False
        for macro in macro_names:
            if re.match(rf"^\s*\\{re.escape(macro)}\s*\{{", lines[index]) and macro in macros:
                new_line = macro_line(macro, macros[macro])
                end_index = orphan_continuation_end(lines, macro_end_line(lines, index))
                old_block = "\n".join(lines[index:end_index + 1]).strip()
                if old_block != new_line:
                    lines[index:end_index + 1] = [new_line]
                    changes += 1
                changed = True
                break
        index += 1 if not changed else 1
    if changes:
        tex_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return changes


def tex_input_command(filename):
    return r"\input{" + filename.replace("\\", "/") + "}"


def replace_input_macro(text, macro, filename):
    command = "\\" + macro
    replacement = command + "{" + tex_input_command(filename) + "}"
    pattern = re.compile(rf"(?m)^\s*\\{re.escape(macro)}\s*\{{\s*\\input(?:\{{[^{{}}]+\}}|\s+[^{{}}\s]+)\s*\}}.*$")
    if pattern.search(text):
        return pattern.sub(lambda _match: replacement, text, count=1)
    return text


def update_tex_inputs(tex_path, selections):
    if not tex_path.exists():
        return 0
    original = tex_path.read_text(encoding="utf-8")
    text = original
    for macro, _label, _hint in INFO_INPUT_ROLES:
        filename = selections.get(macro, "").strip()
        if filename:
            target_macro = "sembollistesi" if macro == "simgelervekisaltmalar" else macro
            text = replace_input_macro(text, target_macro, filename)
            if macro == "simgelervekisaltmalar":
                text = re.sub(
                    r"(?m)^\s*\\kisaltmalistesi\s*\{.*?\}\s*$",
                    lambda _match: r"\kisaltmalistesi{}",
                    text,
                    count=1,
                )

    chapter_files = [selections.get(role, "").strip() for role, _label, _hint in CHAPTER_INPUT_ROLES]
    chapter_files = [name for name in chapter_files if name]
    if chapter_files:
        chapter_block = "\n".join(tex_input_command(name) for name in chapter_files)
        lines = text.splitlines()
        begin_index = next((i for i, line in enumerate(lines) if r"\begin{document}" in line), -1)
        start = end = None
        if begin_index >= 0:
            for i in range(begin_index + 1, len(lines)):
                stripped = lines[i].strip()
                if re.match(r"^\\input(?:\{[^{}]+\.tex\}|\s+[^{}\s]+\.tex)\s*$", stripped):
                    if start is None:
                        start = i
                    end = i
                    continue
                if start is not None:
                    break
                if stripped.startswith(r"\makeatletter") or "references" in stripped.lower():
                    break
        if start is not None and end is not None:
            lines[start:end + 1] = chapter_block.splitlines()
            text = "\n".join(lines)
        elif begin_index >= 0:
            lines[begin_index + 1:begin_index + 1] = chapter_block.splitlines()
            text = "\n".join(lines)

    if text != original:
        tex_path.write_text(text.rstrip() + "\n", encoding="utf-8")
        return 1
    return 0


def natural_tex_sort_key(path):
    parts = re.split(r"(\d+)", path.name.lower())
    return [int(part) if part.isdigit() else part for part in parts]


def tex_file_hint(path):
    name = path.stem.lower()
    if name in {"defs_legacy_original", "defs_legacy", "defs_original"}:
        return ""
    if any(token in name for token in ("sembol", "symbol", "simge", "kisalt", "kısalt")):
        return "simgelervekisaltmalar"
    match = re.search(r"bolum\s*([1-6])|bölüm\s*([1-6])|chapter\s*([1-6])", name)
    if match:
        number = next(group for group in match.groups() if group)
        return f"bolum{number}"
    match = re.search(r"^b(?:olum|ölüm)?([1-6])$", name)
    if match:
        return f"bolum{match.group(1)}"
    try:
        sample = path.read_text(encoding="utf-8", errors="ignore")[:5000].lower()
    except OSError:
        sample = ""
    text = name + "\n" + sample
    if "summary" in text or "abstract" in text:
        return "summary"
    if "ozet" in text or "özet" in text:
        return "ozet"
    if "kisalt" in text or "kısalt" in text or "sembol" in text or "simge" in text:
        return "simgelervekisaltmalar"
    if "onsoz" in text or "önsöz" in text:
        return "onsoz"
    if "etik" in text:
        return "etikbeyan"
    match = re.search(r"bolum\s*([1-6])|bölüm\s*([1-6])|chapter\s*([1-6])", text)
    if match:
        number = next(group for group in match.groups() if group)
        return f"bolum{number}"
    return ""


def tex_mapping_candidate(path):
    name = path.name.lower()
    excluded = {
        "tez.tex", "defs.tex", "defs_legacy_original.tex", "defs_legacy.tex",
        "sirt-kapak.tex", "inonutez.cls", "swp-standalone-begin.tex",
        "swp-standalone-end.tex",
    }
    if name in excluded:
        return False
    if name.endswith((".bak.tex", ".backup.tex", ".orig.tex", "_original.tex")):
        return False
    return True


class ToolTip:
    def __init__(self, widget, text_getter, delay=650, placement="below"):
        self.widget = widget
        self.text_getter = text_getter
        self.delay = delay
        self.placement = placement
        self.after_id = None
        self.window = None
        widget.bind("<Enter>", self.schedule, add="+")
        widget.bind("<Leave>", self.hide, add="+")
        widget.bind("<ButtonPress>", self.hide, add="+")

    def schedule(self, _event=None):
        self.hide()
        self.after_id = self.widget.after(self.delay, self.show)

    def show(self):
        self.after_id = None
        text = self.text_getter() if callable(self.text_getter) else str(self.text_getter)
        if not text:
            return
        self.window = tk.Toplevel(self.widget)
        self.window.wm_overrideredirect(True)
        label = tk.Label(
            self.window,
            text=text,
            justify="left",
            bg="#FFF9D7",
            fg="#17343A",
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=5,
            font=("Segoe UI", 9),
            wraplength=520,
        )
        label.pack()
        self.window.update_idletasks()
        x = self.widget.winfo_rootx() + 8
        if self.placement == "above":
            y = self.widget.winfo_rooty() - self.window.winfo_reqheight() - 8
        else:
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        screen_w = self.widget.winfo_screenwidth()
        screen_h = self.widget.winfo_screenheight()
        tooltip_w = self.window.winfo_reqwidth()
        tooltip_h = self.window.winfo_reqheight()
        if x + tooltip_w > screen_w - 12:
            x = max(8, screen_w - tooltip_w - 12)
        if y + tooltip_h > screen_h - 48:
            y = max(8, self.widget.winfo_rooty() - tooltip_h - 8)
        self.window.wm_geometry(f"+{max(8, x)}+{max(8, y)}")

    def hide(self, _event=None):
        if self.after_id is not None:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
        if self.window is not None:
            self.window.destroy()
            self.window = None


def read_degree(tex_path):
    if not tex_path.exists():
        return None
    text = tex_path.read_text(encoding="utf-8")
    match = re.search(r"\\documentclass\[([^\]]*)\]\{inonutez\}", text)
    if not match:
        return None
    options = [option.strip() for option in match.group(1).split(",")]
    if "doktora" in options or "Doktora" in options:
        return "doktora"
    if "yukseklisans" in options or "Yüksek Lisans" in options:
        return "yukseklisans"
    return None


def write_degree(tex_path, degree):
    text = tex_path.read_text(encoding="utf-8")

    def replace(match):
        options = [option.strip() for option in match.group(1).split(",") if option.strip()]
        options = [option for option in options if option not in ("yukseklisans", "doktora", "Yüksek Lisans", "Doktora")]
        options.append(degree)
        return "\\documentclass[" + ",".join(options) + "]{inonutez}"

    new_text, count = re.subn(r"\\documentclass\[([^\]]*)\]\{inonutez\}", replace, text, count=1)
    if count:
        tex_path.write_text(new_text, encoding="utf-8")
    return bool(count)


def read_citation_style(tex_path):
    if not tex_path.exists():
        return DEFAULT_CITATION_STYLE
    text = tex_path.read_text(encoding="utf-8")
    match = re.search(r"\\documentclass\[([^\]]*)\]\{inonutez\}", text)
    if not match:
        return DEFAULT_CITATION_STYLE
    options = [option.strip() for option in match.group(1).split(",")]
    return "num" if "num" in options else "apa"


def read_thesis_language(tex_path):
    if not tex_path.exists():
        return "turkce"
    text = tex_path.read_text(encoding="utf-8")
    match = re.search(r"\\documentclass\[([^\]]*)\]\{inonutez\}", text)
    if not match:
        return "turkce"
    options = [option.strip() for option in match.group(1).split(",")]
    return "ingilizce" if "ingilizce" in options else "turkce"


def write_citation_style(tex_path, style):
    text = tex_path.read_text(encoding="utf-8")

    def replace(match):
        options = [option.strip() for option in match.group(1).split(",") if option.strip()]
        options = [option for option in options if option not in ("apa", "num")]
        options.append(style)
        return "\\documentclass[" + ",".join(options) + "]{inonutez}"

    new_text, count = re.subn(r"\\documentclass\[([^\]]*)\]\{inonutez\}", replace, text, count=1)
    if count:
        tex_path.write_text(new_text, encoding="utf-8")
        if style == "apa":
            ensure_defs_apa_support(tex_path.parent / "defs.tex")
    return bool(count)


def write_thesis_language(tex_path, language):
    text = tex_path.read_text(encoding="utf-8")

    def replace(match):
        options = [option.strip() for option in match.group(1).split(",") if option.strip()]
        options = [option for option in options if option not in ("turkce", "ingilizce")]
        options.append(language)
        return "\\documentclass[" + ",".join(options) + "]{inonutez}"

    new_text, count = re.subn(r"\\documentclass\[([^\]]*)\]\{inonutez\}", replace, text, count=1)
    if count:
        tex_path.write_text(new_text, encoding="utf-8")
    return bool(count)


def read_decimal_separator(tex_path):
    if not tex_path.exists():
        return "nokta"
    text = tex_path.read_text(encoding="utf-8")
    match = re.search(r"\\ondalikayirici\s*\{([^{}]+)\}", text)
    if not match:
        return "nokta"
    value = match.group(1).strip().casefold()
    return "nokta" if value in {"nokta", "point", "dot", "."} else "virgul"


def write_simple_macro(tex_path, macro, value):
    text = tex_path.read_text(encoding="utf-8")
    support = rf"\providecommand{{\{macro}}}[1]{{}}"
    replacement = rf"\{macro}" + "{" + value + "}"
    pattern = rf"\\{re.escape(macro)}\s*\{{[^{{}}]*\}}"
    text = re.sub(rf"^\s*{re.escape(support)}\s*$\r?\n?", "", text, flags=re.M)
    text = re.sub(rf"^\s*{pattern}\s*$\r?\n?", "", text, flags=re.M)
    block = support + "\n" + replacement + "\n"
    new_text = re.sub(
        r"(\\documentclass\[[^\]]*\]\{inonutez\}\s*)",
        lambda match: match.group(1) + block,
        text,
        count=1,
    )
    if new_text != text:
        tex_path.write_text(new_text, encoding="utf-8")
        return True
    return False


def write_decimal_separator(tex_path, separator):
    return write_simple_macro(tex_path, "ondalikayirici", separator)


def read_page_layout(tex_path):
    if not tex_path.exists():
        return "tek"
    text = tex_path.read_text(encoding="utf-8")
    match = re.search(r"\\documentclass\[([^\]]*)\]\{inonutez\}", text)
    if not match:
        return "tek"
    options = [option.strip() for option in match.group(1).split(",")]
    return "cift" if "onluarkali" in options else "tek"


def write_page_layout(tex_path, layout):
    text = tex_path.read_text(encoding="utf-8")
    support = r"\providecommand{\sayfaduzeni}[1]{}"
    if support not in text:
        text = re.sub(
            r"(\\documentclass\[[^\]]*\]\{inonutez\}\s*)",
            lambda match: match.group(1) + support + "\n",
            text,
            count=1,
        )

    def replace(match):
        options = [option.strip() for option in match.group(1).split(",") if option.strip()]
        options = [option for option in options if option not in ("onluarkali",)]
        if layout == "cift":
            options.append("onluarkali")
        return "\\documentclass[" + ",".join(options) + "]{inonutez}"

    new_text, count = re.subn(r"\\documentclass\[([^\]]*)\]\{inonutez\}", replace, text, count=1)
    if count:
        new_text = re.sub(r"\\sayfaduzeni\s*\{[^{}]*\}", rf"\\sayfaduzeni{{{layout}}}", new_text, count=1)
        if r"\sayfaduzeni" not in new_text:
            new_text = re.sub(
                r"(\\documentclass\[[^\]]*\]\{inonutez\}\s*)",
                lambda match: match.group(1) + rf"\sayfaduzeni{{{layout}}}" + "\n",
                new_text,
                count=1,
            )
        tex_path.write_text(new_text, encoding="utf-8")
    return bool(count)


def detect_tools():
    names = ["latexmk", "xelatex", "pdflatex", "biber", "bibtex", "pdftotext", "pdfinfo", "pdffonts", "powershell"]
    return {name: shutil.which(name) for name in names}


def is_english_thesis_label(value):
    normalized = (value or "").strip().casefold()
    return normalized.endswith("ngilizce") or normalized == "english"


def is_template_placeholder(value):
    return any(pattern in (value or "") for pattern in PLACEHOLDER_PATTERNS)


def tr_title_case(value):
    lower_map = str.maketrans({"I": "ı", "İ": "i"})
    upper_map = {"i": "İ", "ı": "I"}
    words = []
    for word in re.split(r"(\s+)", value):
        if not word or word.isspace():
            words.append(word)
            continue
        first = word[0]
        rest = word[1:].translate(lower_map).lower()
        words.append(upper_map.get(first, first.upper()) + rest)
    return "".join(words)


def tr_upper(value):
    return (value or "").translate(str.maketrans({
        "i": "İ", "ı": "I", "ş": "Ş", "ğ": "Ğ", "ü": "Ü", "ö": "Ö", "ç": "Ç",
    })).upper()


def normalize_punctuation_spacing(value):
    value = re.sub(r"\s+([.,;:!?])", r"\1", value or "")
    value = re.sub(r"([.,;:!?])(?=\S)", r"\1 ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_person_name(value, lang="tr"):
    text = normalize_punctuation_spacing(latex_to_text(value or ""))
    replacements = [
        (r"\bprof\s*\.\s*dr\s*\.", "Prof. Dr."),
        (r"\bdoç\s*\.\s*dr\s*\.", "Doç. Dr."),
        (r"\bdoc\s*\.\s*dr\s*\.", "Doç. Dr."),
        (r"\bdr\s*\.\s*öğr\s*\.\s*üyesi\b", "Dr. Öğr. Üyesi"),
        (r"\bdr\s*\.\s*ogr\s*\.\s*uyesi\b", "Dr. Öğr. Üyesi"),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.I)
    protected = {}
    for index, title in enumerate(["Prof. Dr.", "Doç. Dr.", "Dr. Öğr. Üyesi"]):
        token = f"§{index}§"
        text = text.replace(title, token)
        protected[token] = title

    def smart_case_word(match):
        word = match.group(0)
        if not word:
            return word
        if len(word) == 1:
            return tr_upper(word) if lang == "tr" else word.upper()
        # Preserve intentionally uppercase surnames and already mixed-case names.
        if any(char.isupper() for char in word[1:]):
            return word
        return tr_title_case(word) if lang == "tr" else word.title()

    text = re.sub(r"[A-Za-zÇĞİÖŞÜçğıöşü]+", smart_case_word, text)
    for token, title in protected.items():
        text = text.replace(token, title)
    return normalize_punctuation_spacing(text)


def ui_lang_key(value):
    return "en" if value == "English" else "tr"


class ThesisManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{UI['tr']['title']} {APP_VERSION}")
        self.geometry("1420x840")
        self.minsize(860, 560)

        self.template_var = tk.StringVar(value="Birleşik İnönü FBE 2025")
        self.work_dir_var = tk.StringVar(value=str(TEMPLATES["Birleşik İnönü FBE 2025"]))
        self.citation_var = tk.StringVar(value=CITATION_DISPLAY["tr"][DEFAULT_CITATION_STYLE])
        self.degree_var = tk.StringVar(value="Yüksek Lisans")
        self.decimal_separator_var = tk.StringVar(value=DECIMAL_SEPARATOR_DISPLAY["tr"]["nokta"])
        self.page_layout_var = tk.StringVar(value=PAGE_LAYOUT_DISPLAY["tr"]["tek"])
        self.engine_var = tk.StringVar(value="xelatex")
        self.thesis_language_var = tk.StringVar(value="Türkçe")
        self.lang_var = tk.StringVar(value="Türkçe")
        self.theme_var = tk.StringVar(value="Açık")
        self.with_spine_var = tk.BooleanVar(value=True)
        self.autosave_var = tk.BooleanVar(value=True)
        self.last_saved_var = tk.StringVar(value="Henüz kaydedilmedi")
        self.vars = {}
        self.date_vars = {}
        self.field_widgets = {}
        self.missing_targets = []
        self.placeholder_entries = {}
        self.text_entries = []
        self.combo_entries = []
        self.tex_entry_keys = {}
        self.active_tex_entry = None
        self.tex_tool_buttons_frame = None
        self.tex_palette_popup = None
        self.tex_palette_cache = {}
        self.tex_palette_warm_after_id = None
        self.tex_floating_toolbar = None
        self.tex_floating_after_id = None
        self.tex_floating_entry = None
        self.placeholder_active_keys = set()
        self.radio_buttons = []
        self.soft_group_frames = []
        self.themed_canvases = []
        self.ui_labels = {}
        self.notebook_tabs = []
        self.logo_image = None
        self.app_icon_image = None
        self.autosave_check = None
        self.update_buttons = []
        self.update_check_running = False
        self.update_available = False
        self.update_status_text = ""
        self.zemberek_install_running = False
        self.zemberek_install_prompted = False
        self.preview_logo_images = {}
        self.preview_after_id = None
        self.preview_deferred = False
        self.main_canvas_sync_after_id = None
        self.button_images = {}
        self.tooltips = []
        self.output_queue = queue.Queue()
        self.running = False
        self.run_paned = None
        self.diag_editor_panel = None
        self.diag_editor_visible = False
        self.diag_editor_text = None
        self.diag_editor_path = None
        self.diag_editor_open_button = None
        self.diag_editor_save_button = None
        self.diag_editor_undo_button = None
        self.diag_editor_redo_button = None
        self.diag_line_numbers_var = tk.BooleanVar(value=True)
        self.diag_editor_line_numbers = None
        self.diag_syntax_after_id = None
        self.diag_bookmarks = {}
        self.diag_inline_suggestion_popup = None
        self.diag_inline_suggestion_window = None
        self.diag_split_toggle = None
        self.diag_last_editor_args = None
        self.diag_editor_status_var = tk.StringVar(value="")
        self.diag_editor_title_var = tk.StringVar(value="Düzeltme")
        self.diag_suggestions_frame = None
        self.busy_buttons = []
        self.dashboard_cards = {}
        self.dashboard_hint_vars = {}
        self.dashboard_vars = {}
        self.next_action_key = None
        self.next_action_title_var = tk.StringVar(value="")
        self.next_action_detail_var = tk.StringVar(value="")
        self.next_action_button_var = tk.StringVar(value="Başlat")
        self.workflow_step_vars = {}
        self.workflow_step_frames = {}
        self.workflow_step_title_labels = {}
        self.workflow_step_status_labels = {}
        self.loading_form = False
        self.autosave_after_id = None
        self.undo_stack = []
        self.redo_stack = []
        self.last_autosave_data = None
        self.last_synced_jury_advisor = ""
        self.syncing_advisor_jury = False
        self.thesis_language_box = None
        self.degree_box = None
        self.citation_box = None
        self.decimal_separator_box = None
        self.page_layout_box = None
        self.preferred_tex_editor = None
        self.auto_derived_values = {}
        self.active_canvas = None
        self._load_window_icon()

        self._build_ui()
        self.load_from_tez()
        if hasattr(self, "missing_list"):
            self.refresh_missing()
        self.after(600, self.refresh_system)
        self.after(2500, self.check_zemberek_installation)
        self.after(8000, self._warm_writing_dictionary)
        self.after(20000, self.schedule_update_check)
        self.after(100, self._drain_output)
        self.bind_all("<Button-1>", self._maybe_close_floating_tex_tools, add="+")
        self.bind_all("<Button-1>", self._maybe_clear_form_focus, add="+")

    @property
    def template_dir(self):
        path = Path(self.work_dir_var.get()).expanduser()
        return path if path else TEMPLATES[self.template_var.get()]

    def _warm_writing_dictionary(self):
        workdir = self.template_dir

        def worker():
            try:
                yazim_denetimi.load_dictionary("tr", workdir=workdir)
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def check_zemberek_installation(self):
        if self.zemberek_install_prompted or self.zemberek_install_running:
            return
        self.zemberek_install_prompted = True
        dictionary = yazim_denetimi.load_dictionary("tr", workdir=self.template_dir)
        if getattr(dictionary, "zemberek", None):
            return
        packages = []
        if importlib.util.find_spec("pkg_resources") is None:
            packages.append("setuptools<81")
        if importlib.util.find_spec("zemberek") is None:
            packages.append("zemberek-python")
        if not packages:
            self.status.configure(text="Zemberek kurulu, ancak bu oturumda aktifleşmedi")
            return
        if not messagebox.askyesno(
            "Zemberek Türkçe sözlük",
            "Türkçe Zemberek morfoloji sözlüğü bu Python ortamında aktif değil.\n\n"
            "Yazım denetiminin Türkçe ekleri daha sağlıklı değerlendirebilmesi için "
            f"`{' '.join(packages)}` paketi indirilsin ve kurulsun mu?",
        ):
            return
        self.install_zemberek_package(packages)

    def install_zemberek_package(self, packages=None):
        if self.zemberek_install_running:
            return
        packages = packages or ["setuptools<81", "zemberek-python"]
        self.zemberek_install_running = True
        self.status.configure(text="Zemberek kuruluyor...")
        self.zemberek_progress_window = tk.Toplevel(self)
        self.zemberek_progress_window.title("Zemberek kuruluyor")
        self.zemberek_progress_window.geometry("560x180")
        self.zemberek_progress_window.transient(self)
        self.zemberek_progress_window.resizable(False, False)
        ttk.Label(self.zemberek_progress_window, text="Türkçe Zemberek sözlüğü hazırlanıyor", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14, pady=(14, 4))
        progress_var = tk.StringVar(value="Paket yöneticisi başlatılıyor...")
        ttk.Label(self.zemberek_progress_window, textvariable=progress_var, wraplength=520).pack(anchor="w", padx=14, pady=(0, 8))
        progress = ttk.Progressbar(self.zemberek_progress_window, mode="indeterminate", length=520)
        progress.pack(fill="x", padx=14, pady=(0, 8))
        detail = tk.Text(self.zemberek_progress_window, height=4, wrap="word", font=("Consolas", 8))
        detail.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        detail.insert("end", "Kurulum internet hızına göre birkaç dakika sürebilir.\n")
        detail.configure(state="disabled")
        progress.start(12)

        def post_progress(text):
            def apply():
                if not getattr(self, "zemberek_progress_window", None) or not self.zemberek_progress_window.winfo_exists():
                    return
                progress_var.set(text)
                detail.configure(state="normal")
                detail.insert("end", text + "\n")
                detail.see("end")
                detail.configure(state="disabled")
            self.after(0, apply)

        def worker():
            command = [sys.executable, "-m", "pip", "install", *packages]
            post_progress("İndirilecek/kurulacak paketler: " + ", ".join(packages))
            try:
                process = subprocess.Popen(command, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
                lines = []
                assert process.stdout is not None
                for line in process.stdout:
                    line = line.strip()
                    if line:
                        lines.append(line)
                        if any(key in line.lower() for key in ("collecting", "downloading", "installing", "successfully", "requirement")):
                            post_progress(line)
                return_code = process.wait(timeout=30)
                ok = return_code == 0
                details = "\n".join(lines)
            except Exception as exc:
                ok = False
                details = str(exc)
            self.after(0, lambda: self.finish_zemberek_install(ok, details[-2000:]))

        threading.Thread(target=worker, daemon=True).start()

    def finish_zemberek_install(self, ok, details):
        self.zemberek_install_running = False
        window = getattr(self, "zemberek_progress_window", None)
        if window and window.winfo_exists():
            window.destroy()
        self.zemberek_progress_window = None
        if ok:
            yazim_denetimi.DICTIONARY_CACHE.clear()
            yazim_denetimi.ZEMBEREK_ENGINE = None
            yazim_denetimi.ZEMBEREK_LOAD_ATTEMPTED = False
            yazim_denetimi.ZEMBEREK_LOAD_ERROR = ""
            dictionary = yazim_denetimi.load_dictionary("tr", workdir=self.template_dir)
            if getattr(dictionary, "zemberek", None):
                self.status.configure(text="Zemberek aktif")
            else:
                self.status.configure(text="Zemberek kurulu, yeniden başlatma gerekli")
            if messagebox.askyesno(
                "Zemberek kuruldu",
                "Zemberek paketi kuruldu. Türkçe yazım denetiminin aktif olması için GUI yeniden başlatılsın mı?",
            ):
                os.execl(sys.executable, sys.executable, *sys.argv)
        else:
            self.status.configure(text="Zemberek kurulamadı")
            messagebox.showwarning(
                "Zemberek kurulamadı",
                "Zemberek otomatik kurulamadı. İnternet bağlantısı veya Python paket yöneticisi kontrol edilmeli.\n\n"
                f"Ayrıntı:\n{details}",
            )

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.main_canvas = tk.Canvas(self, highlightthickness=0)
        self.main_canvas.grid(row=0, column=0, sticky="nsew")
        self.themed_canvases.append(self.main_canvas)
        self.main_y_scroll = ttk.Scrollbar(self, orient="vertical", command=self.main_canvas.yview)
        self.main_y_scroll.grid(row=0, column=1, sticky="ns")
        self.main_x_scroll = ttk.Scrollbar(self, orient="horizontal", command=self.main_canvas.xview)
        self.main_x_scroll.grid(row=1, column=0, sticky="ew")
        self.main_canvas.configure(
            yscrollcommand=lambda first, last, sb=self.main_y_scroll: self._sync_scrollbar(sb, first, last),
            xscrollcommand=lambda first, last, sb=self.main_x_scroll: self._sync_scrollbar(sb, first, last),
        )
        container = ttk.Frame(self.main_canvas)
        self.main_container = container
        self.main_canvas_window = self.main_canvas.create_window((0, 0), window=container, anchor="nw")
        container.bind("<Configure>", self._sync_main_canvas)
        self.main_canvas.bind("<Configure>", self._sync_main_canvas)
        self.main_canvas.bind("<Enter>", lambda _event, c=self.main_canvas: self._bind_mousewheel(c))

        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        top = ttk.Frame(container, padding=(12, 6))
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)

        self.logo_label = ttk.Label(top)
        self.logo_label.grid(row=0, column=0, sticky="w", padx=(0, 18))
        self._load_logo()

        title_box = ttk.Frame(top)
        title_box.grid(row=0, column=1, sticky="ew", padx=(0, 18), pady=(22, 0))
        self.ui_labels["title"] = ttk.Label(title_box, text=f"{UI['tr']['title']}  {APP_VERSION}", font=("Segoe UI", 17, "bold"))
        self.ui_labels["title"].pack(anchor="center")
        self.ui_labels["subtitle"] = ttk.Label(title_box, text=UI["tr"]["subtitle"])
        self.ui_labels["subtitle"].pack(anchor="center", pady=(2, 0))

        controls = ttk.Frame(top, style="Card.TFrame", padding=(4, 0))
        controls.grid(row=0, column=2, sticky="e")
        controls.columnconfigure(0, weight=1)

        interface_group = tk.Frame(controls, bg=THEMES[self.theme_var.get()]["panel"], highlightbackground=THEMES[self.theme_var.get()]["soft_line"], highlightthickness=1, bd=0, padx=8, pady=6)
        interface_group.grid(row=0, column=0, columnspan=2, sticky="e")
        thesis_group = tk.Frame(controls, bg=THEMES[self.theme_var.get()]["panel"], highlightbackground=THEMES[self.theme_var.get()]["soft_line"], highlightthickness=1, bd=0, padx=10, pady=6)
        thesis_group.grid(row=2, column=0, columnspan=2, sticky="e", pady=(8, 0))
        thesis_group.columnconfigure(0, weight=1)
        thesis_group.columnconfigure(1, weight=1)
        self.soft_group_frames.extend([interface_group, thesis_group])
        thesis_left = ttk.Frame(thesis_group, style="Card.TFrame")
        thesis_left.grid(row=0, column=0, sticky="nw")

        self.ui_labels["language"] = ttk.Label(interface_group, text=UI["tr"]["language"], style="Card.TLabel")
        self.ui_labels["language"].grid(row=0, column=0, sticky="w")
        lang_buttons = ttk.Frame(interface_group, style="Card.TFrame")
        lang_buttons.grid(row=0, column=1, sticky="w", padx=(8, 0), pady=2)
        for label, value in (("TR", "Türkçe"), ("EN", "English")):
            rb = tk.Radiobutton(lang_buttons, text=label, value=value, variable=self.lang_var, command=self.apply_language, font=("Segoe UI", 9), borderwidth=0, highlightthickness=0)
            rb.pack(side="left", padx=(0, 8))
            self.radio_buttons.append(rb)

        self.ui_labels["theme"] = ttk.Label(interface_group, text=UI["tr"]["theme"], style="Card.TLabel")
        self.ui_labels["theme"].grid(row=0, column=2, sticky="w", padx=(18, 0))
        theme_buttons = ttk.Frame(interface_group, style="Card.TFrame")
        theme_buttons.grid(row=0, column=3, sticky="w", padx=(8, 0), pady=2)
        for label, value in (("Light", "Açık"), ("Dark", "Koyu")):
            rb = tk.Radiobutton(theme_buttons, text=label, value=value, variable=self.theme_var, command=self.apply_theme, font=("Segoe UI", 9), borderwidth=0, highlightthickness=0)
            rb.pack(side="left", padx=(0, 8))
            self.radio_buttons.append(rb)

        self.update_button = ttk.Button(interface_group, text="Güncelle", image=self._button_icon("update"), compound="left", style="Tiny.TButton", command=self.run_safe_update)
        self.update_button.grid(row=0, column=4, sticky="w", padx=(8, 0), pady=1)
        self.update_buttons.append(self.update_button)
        self._add_tooltip(self.update_button, "update_app")
        self.busy_buttons.append(self.update_button)

        self.ui_labels["thesis_language"] = ttk.Label(thesis_left, text=UI["tr"]["thesis_language"], style="Card.TLabel")
        self.ui_labels["thesis_language"].grid(row=0, column=0, sticky="w")
        self.thesis_language_box = ttk.Combobox(thesis_left, textvariable=self.thesis_language_var, values=list(THESIS_LANGUAGE_DISPLAY["tr"].values()), state="readonly", width=14)
        self.thesis_language_box.grid(row=0, column=1, sticky="w", padx=(8, 0), pady=2)
        self.thesis_language_box.bind("<<ComboboxSelected>>", lambda _event: self.on_thesis_language_change())
        self.combo_entries.append(self.thesis_language_box)

        self.engine_var.set("xelatex")

        self.ui_labels["source_style"] = ttk.Label(thesis_left, text=UI["tr"]["source_style"], style="Card.TLabel")
        self.ui_labels["source_style"].grid(row=0, column=2, sticky="w", padx=(18, 0))
        self.citation_box = ttk.Combobox(thesis_left, textvariable=self.citation_var, values=list(CITATION_DISPLAY["tr"].values()), state="readonly", width=14)
        self.citation_box.grid(row=0, column=3, padx=(8, 0), pady=2)
        self.citation_box.bind("<<ComboboxSelected>>", lambda _event: self.on_citation_change())
        self.combo_entries.append(self.citation_box)

        self.spine_check = ttk.Checkbutton(thesis_left, text=UI["tr"]["spine"], variable=self.with_spine_var, style="Card.TCheckbutton")
        self.spine_check.grid(row=0, column=4, sticky="w", padx=(14, 0), pady=2)
        self._add_tooltip(self.spine_check, "spine_cover")

        self.ui_labels["degree"] = ttk.Label(thesis_left, text=UI["tr"]["degree"], style="Card.TLabel")
        self.ui_labels["degree"].grid(row=1, column=0, sticky="w")
        self.degree_box = ttk.Combobox(thesis_left, textvariable=self.degree_var, values=list(DEGREE_DISPLAY["tr"].values()), state="readonly", width=14)
        self.degree_box.grid(row=1, column=1, padx=(8, 0), pady=2)
        self.degree_box.bind("<<ComboboxSelected>>", lambda _event: self.on_degree_change())
        self.combo_entries.append(self.degree_box)

        self.ui_labels["decimal_separator"] = ttk.Label(thesis_left, text=UI["tr"]["decimal_separator"], style="Card.TLabel")
        self.ui_labels["decimal_separator"].grid(row=1, column=2, sticky="w", padx=(18, 0))
        self.decimal_separator_box = ttk.Combobox(thesis_left, textvariable=self.decimal_separator_var, values=list(DECIMAL_SEPARATOR_DISPLAY["tr"].values()), state="readonly", width=14)
        self.decimal_separator_box.grid(row=1, column=3, sticky="w", padx=(8, 0), pady=2)
        self.decimal_separator_box.bind("<<ComboboxSelected>>", lambda _event: self.on_decimal_separator_change())
        self.combo_entries.append(self.decimal_separator_box)

        self.ui_labels["page_layout"] = ttk.Label(thesis_left, text=UI["tr"]["page_layout"], style="Card.TLabel")
        self.ui_labels["page_layout"].grid(row=1, column=4, sticky="w", padx=(18, 0))
        self.page_layout_box = ttk.Combobox(thesis_left, textvariable=self.page_layout_var, values=list(PAGE_LAYOUT_DISPLAY["tr"].values()), state="readonly", width=12)
        self.page_layout_box.grid(row=1, column=5, sticky="w", padx=(8, 0), pady=2)
        self.page_layout_box.bind("<<ComboboxSelected>>", lambda _event: self.on_page_layout_change())
        self.combo_entries.append(self.page_layout_box)

        work_box = ttk.Frame(thesis_group, style="Card.TFrame")
        work_box.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(7, 0))
        work_box.columnconfigure(1, weight=1)
        self.ui_labels["work_folder"] = ttk.Label(work_box, text=UI["tr"].get("work_folder", "Çalışma klasörü"), style="Card.TLabel")
        self.ui_labels["work_folder"].grid(row=0, column=0, sticky="w")
        self.work_dir_entry = ttk.Entry(work_box, textvariable=self.work_dir_var, state="readonly", width=36)
        self.work_dir_entry.grid(row=0, column=1, sticky="ew", padx=(8, 4))
        self.choose_folder_button = ttk.Button(work_box, text=UI["tr"].get("choose_folder", "Seç"), image=self._button_icon("folder"), compound="left", style="Tiny.TButton", width=5, command=self.select_work_dir)
        self.choose_folder_button.grid(row=0, column=2, sticky="e")
        self._add_tooltip(self.choose_folder_button, "choose_folder")
        # Eski tez dönüştürme ana sekmede yer alır; üst araç çubuğunda düğme gösterilmez.

        self.notebook = ttk.Notebook(container)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self.info_tab = ttk.Frame(self.notebook, padding=10)
        self.missing_tab = ttk.Frame(self.notebook, padding=10)
        self.system_tab = ttk.Frame(self.notebook, padding=10)
        self.run_tab = ttk.Frame(self.notebook, padding=10)
        self.legacy_tab = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.info_tab, text=UI["tr"]["info_tab"])
        self.notebook.add(self.missing_tab, text=UI["tr"]["missing_tab"])
        self.notebook.add(self.system_tab, text=UI["tr"]["system_tab"])
        self.notebook.add(self.run_tab, text=UI["tr"]["run_tab"])
        self.notebook.add(self.legacy_tab, text="Eski Tez Dönüştürücü")
        self.notebook_tabs = [(self.info_tab, "info_tab"), (self.missing_tab, "missing_tab"), (self.system_tab, "system_tab"), (self.run_tab, "run_tab")]

        self._build_info_tab()
        self._build_missing_tab()
        self._build_system_tab()
        self._build_run_tab()
        self._build_legacy_tab()
        self.apply_theme()

    def _load_window_icon(self):
        icon_png = ROOT / "tez_asistani_icon.png"
        icon_ico = ROOT / "tez_asistani_icon.ico"
        try:
            if sys.platform.startswith("win") and icon_ico.exists():
                self.iconbitmap(default=str(icon_ico))
            if icon_png.exists():
                image = Image.open(icon_png).convert("RGBA").resize((32, 32), Image.LANCZOS)
                self.app_icon_image = ImageTk.PhotoImage(image)
                self.iconphoto(True, self.app_icon_image)
        except Exception:
            pass

    def _load_logo(self):
        dark = self.theme_var.get() == "Koyu"
        logo_name = "iu_fbe_logo_yatay_dark.png" if dark else "iu_fbe_logo_yatay.png"
        logo_path = ROOT / logo_name
        if not logo_path.exists():
            logo_path = ROOT / "iu_fbe_logo_yatay.png"
        if logo_path.exists():
            image = Image.open(logo_path).convert("RGBA")
            bg = Image.new("RGBA", image.size, image.getpixel((0, 0)))
            diff = ImageChops.difference(image, bg)
            bbox = diff.getbbox()
            if bbox:
                image = image.crop(bbox)
            target_width = 360
            if image.width > target_width:
                ratio = target_width / image.width
                image = image.resize((target_width, max(1, int(image.height * ratio))), Image.LANCZOS)
            self.logo_image = ImageTk.PhotoImage(image)
            self.logo_label.configure(image=self.logo_image)

    def select_work_dir(self):
        folder = filedialog.askdirectory(
            title="Tez çalışma klasörü seç",
            initialdir=str(self.template_dir if self.template_dir.exists() else ROOT),
        )
        if not folder:
            return
        selected = Path(folder)
        self.work_dir_var.set(str(selected))
        if not (selected / "tez.tex").exists():
            messagebox.showwarning("tez.tex bulunamadı", "Seçilen klasörde tez.tex yok. Bu klasörü önce uyarlanmış tez klasörü olarak hazırlayın.")
            return
        self.load_from_tez()
        self.refresh_missing()
        self.refresh_system()
        self.update_preview()
        self.after(250, lambda path=selected: self.open_tex_file_mapping_dialog(path, auto=True))

    def scan_tex_file_suggestions(self, folder):
        tex_files = sorted(
            [
                path for path in Path(folder).glob("*.tex")
                if tex_mapping_candidate(path)
            ],
            key=natural_tex_sort_key,
        )
        suggestions = {role: "" for role, _label, _hint in TEX_INPUT_ROLES}
        used = set()
        for path in tex_files:
            hint = tex_file_hint(path)
            if hint in suggestions and not suggestions[hint]:
                suggestions[hint] = path.name
                used.add(path.name)
        chapter_candidates = [path for path in tex_files if path.name not in used and re.search(r"\\chapter\s*\{", path.read_text(encoding="utf-8", errors="ignore")[:5000])]
        for index, path in enumerate(chapter_candidates[:6], start=1):
            role = f"bolum{index}"
            if not suggestions.get(role):
                suggestions[role] = path.name
                used.add(path.name)
        return tex_files, suggestions

    def open_tex_file_mapping_dialog(self, folder=None, auto=False):
        folder = Path(folder or self.template_dir)
        tex_path = folder / "tez.tex"
        if not tex_path.exists():
            return
        tex_files, suggestions = self.scan_tex_file_suggestions(folder)
        if auto and len(tex_files) <= 1:
            return
        window = tk.Toplevel(self)
        window.title("TeX Dosyalarını Tanı")
        window.transient(self)
        window.geometry("620x520")
        window.columnconfigure(0, weight=1)
        window.rowconfigure(1, weight=1)

        header = ttk.Frame(window, padding=(12, 10, 12, 6))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="Klasördeki TeX dosyalarını tez bölümleriyle eşleştir", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        desc_label = ttk.Label(
            header,
            text="Önerileri değiştirebilir veya kullanılmayacak satırları boş bırakabilirsiniz. Kaydet seçimi tez.tex içindeki input satırlarına yazar.",
            justify="left",
            wraplength=560,
        )
        desc_label.pack(anchor="w", fill="x", pady=(4, 0))
        window.bind("<Configure>", lambda event, label=desc_label: label.configure(wraplength=max(260, event.width - 36)), add="+")

        body = ttk.Frame(window, padding=(12, 0, 12, 0))
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)
        canvas = tk.Canvas(body, highlightthickness=0)
        y_scroll = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
        x_scroll = ttk.Scrollbar(body, orient="horizontal", command=canvas.xview)
        canvas.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        canvas.configure(
            yscrollcommand=lambda first, last, sb=y_scroll: self._sync_scrollbar(sb, first, last),
            xscrollcommand=lambda first, last, sb=x_scroll: self._sync_scrollbar(sb, first, last),
        )
        inner = ttk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(canvas_window, width=max(event.width, inner.winfo_reqwidth())))
        canvas.bind("<Enter>", lambda _event, c=canvas: self._bind_mousewheel(c))

        ttk.Label(inner, text="Tez alanı", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 4))
        ttk.Label(inner, text="Dosya", font=("Segoe UI", 9, "bold")).grid(row=0, column=1, sticky="ew", pady=(0, 4))
        values = [""] + [path.name for path in tex_files]
        role_vars = {}
        for row, (role, label, _hint) in enumerate(TEX_INPUT_ROLES, start=1):
            ttk.Label(inner, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
            var = tk.StringVar(value=suggestions.get(role, ""))
            combo = ttk.Combobox(inner, textvariable=var, values=values, state="readonly", width=42)
            combo.grid(row=row, column=1, sticky="ew", pady=3)
            role_vars[role] = var
        inner.columnconfigure(1, weight=1)

        footer = ttk.Frame(window, padding=(12, 8, 12, 12))
        footer.grid(row=2, column=0, sticky="ew")
        status_var = tk.StringVar(value=f"{len(tex_files)} TeX dosyası bulundu.")
        ttk.Label(footer, textvariable=status_var).pack(side="left")

        def save_mapping():
            selections = {role: var.get().strip() for role, var in role_vars.items()}
            try:
                changed = update_tex_inputs(tex_path, selections)
                status_var.set("tez.tex güncellendi." if changed else "Değişiklik yok.")
                self.load_from_tez()
                self.refresh_missing()
                self.update_preview()
                window.after(500, window.destroy)
            except Exception as exc:
                messagebox.showerror("TeX dosyaları kaydedilemedi", str(exc), parent=window)

        ttk.Button(footer, text="Kaydet", image=self._button_icon("save", "primary"), compound="left", style="Primary.TButton", command=save_mapping).pack(side="right", padx=(6, 0))
        ttk.Button(footer, text="Kapat", command=window.destroy).pack(side="right")
        self.after_idle(lambda: (self._sync_scrollbar(y_scroll, *canvas.yview()), self._sync_scrollbar(x_scroll, *canvas.xview())))

    def _build_legacy_tab(self):
        self.legacy_tab.columnconfigure(0, weight=1)
        box = ttk.LabelFrame(self.legacy_tab, text="Eski şablonla hazırlanmış tezi yeni şablona dönüştür", padding=14)
        box.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        box.columnconfigure(0, weight=1)
        ttk.Label(
            box,
            text="Eski tez klasörünü seçin. Orijinal klasör değiştirilmez; dönüştürülen kopya repo dışındaki donusturulen_tezler klasörüne yazılır.",
            wraplength=780,
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))
        btn = ttk.Button(box, text="Eski Tezi Dönüştür", image=self._button_icon("convert"), compound="left", command=self.convert_legacy_thesis)
        btn.grid(row=1, column=0, sticky="w")
        self._add_tooltip(btn, "convert_legacy")
        self.busy_buttons.append(btn)

    def _build_info_tab(self):
        self.info_tab.columnconfigure(0, weight=5)
        self.info_tab.columnconfigure(1, weight=2)
        self.info_tab.rowconfigure(0, weight=1)
        left = ttk.Frame(self.info_tab)
        right = ttk.Frame(self.info_tab, padding=(10, 0, 0, 0))
        left.grid(row=0, column=0, sticky="nsew")
        right.grid(row=0, column=1, sticky="nsew")

        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        self.form_notebook = ttk.Notebook(left)
        self.form_notebook.grid(row=0, column=0, sticky="nsew")

        self.cover_form_tab = ttk.Frame(self.form_notebook, padding=(4, 2))
        self.approval_form_tab = ttk.Frame(self.form_notebook, padding=(4, 2))
        self.ai_form_tab = ttk.Frame(self.form_notebook, padding=(8, 8))
        self.form_notebook.add(self.cover_form_tab, text=UI["tr"]["cover_tab"])
        self.form_notebook.add(self.approval_form_tab, text=UI["tr"]["approval_tab"])
        self.form_notebook.add(self.ai_form_tab, text="ÜYZ Beyanı")

        self._build_form_pages()
        self._build_ai_declaration_tab()
        self.form_notebook.bind("<<NotebookTabChanged>>", lambda _event: self.show_active_preview())
        self.on_degree_change()

        actions = ttk.Frame(left)
        actions.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        tex_group = tk.Frame(actions, bg=THEMES[self.theme_var.get()]["panel"], highlightbackground=THEMES[self.theme_var.get()]["soft_line"], highlightthickness=1, bd=0, padx=4, pady=3)
        tex_group.pack(side="left", padx=(0, 6))
        self.soft_group_frames.append(tex_group)
        ttk.Label(tex_group, text="tez.tex", style="Card.TLabel").pack(side="left", padx=(2, 5))
        read_btn = ttk.Button(tex_group, text="Oku", image=self._button_icon("read"), compound="left", style="Mini.TButton", width=5, command=self.load_from_tez)
        read_btn.pack(side="left", padx=1)
        self._add_tooltip(read_btn, "read", placement="above")
        save_cluster = tk.Frame(tex_group, bg=THEMES[self.theme_var.get()]["panel"], bd=0, width=104, height=32)
        save_cluster.pack(side="left", padx=(2, 1))
        save_cluster.pack_propagate(False)
        self.soft_group_frames.append(save_cluster)
        save_btn = ttk.Button(save_cluster, text="Kaydet", image=self._button_icon("save", "primary"), compound="left", style="PrimaryMini.TButton", width=8, command=self.save_and_apply_to_tez)
        save_btn.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._add_tooltip(save_btn, "safe_write", placement="above")
        self.busy_buttons.append(save_btn)
        colors = THEMES[self.theme_var.get()]
        def toggle_autosave(_event=None):
            self.autosave_var.set(not self.autosave_var.get())
            self.render_autosave_check()

        autosave_check = tk.Canvas(
            save_cluster,
            width=13,
            height=13,
            bg=colors["panel"],
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        autosave_check.place(x=5, y=5, width=13, height=13)
        autosave_check.bind("<Button-1>", toggle_autosave)
        self.autosave_check = autosave_check
        self._add_tooltip(autosave_check, "autosave", placement="above")
        self.render_autosave_check()
        ttk.Label(tex_group, textvariable=self.last_saved_var, style="Card.TLabel").pack(side="left", padx=(6, 2))
        undo_btn = ttk.Button(actions, text="Geri Al", image=self._button_icon("undo"), compound="left", style="Mini.TButton", width=8, command=self.undo_form_change)
        undo_btn.pack(side="left", padx=2)
        self._add_tooltip(undo_btn, "undo", placement="above")
        redo_btn = ttk.Button(actions, text="Yinele", image=self._button_icon("redo"), compound="left", style="Mini.TButton", width=7, command=self.redo_form_change)
        redo_btn.pack(side="left", padx=2)
        self._add_tooltip(redo_btn, "redo", placement="above")
        theorem_btn = ttk.Button(actions, text="Ortamlar", image=self._button_icon("theorem"), compound="left", style="Mini.TButton", width=10, command=self.edit_theorem_environments)
        theorem_btn.pack(side="left", padx=3)
        self._add_tooltip(theorem_btn, "theorem_envs", placement="above")
        open_btn = ttk.Button(actions, text="Klasör", image=self._button_icon("folder"), compound="left", style="Mini.TButton", width=8, command=lambda: os.startfile(self.template_dir))
        open_btn.pack(side="right", padx=3)
        self._add_tooltip(open_btn, "open_folder", placement="above")

        self._build_tex_tools(left)
        self._build_preview_panel(right)

    def _ai_declaration_templates(self):
        return {
            "Kullanılmadı": (
                "Bu tez çalışmasının hazırlanmasında bilimsel etik ilkelere ve akademik dürüstlük kurallarına uyduğumu; "
                "yararlandığım tüm kaynakları metin içinde ve kaynaklar bölümünde uygun biçimde gösterdiğimi beyan ederim.\n\n"
                "Bu tez çalışmasında üretken yapay zekâ tabanlı araç kullanılmamıştır."
            ),
            "Kullanıldı - öneri metni": (
                "Bu tez çalışmasının hazırlanmasında bilimsel etik ilkelere ve akademik dürüstlük kurallarına uyduğumu; "
                "yararlandığım tüm kaynakları metin içinde ve kaynaklar bölümünde uygun biçimde gösterdiğimi beyan ederim.\n\n"
                "Bu tez çalışmasında üretken yapay zekâ tabanlı araçlar; dil ve yazım denetimi, anlatımın sadeleştirilmesi, "
                "metin tutarlılığının gözden geçirilmesi ve kaynak gösterimi dışındaki biçimsel önerilerin değerlendirilmesi amacıyla "
                "danışman bilgisi dahilinde sınırlı olarak kullanılmıştır. Üretken yapay zekâ çıktıları doğrudan bilimsel bulgu, analiz, "
                "sonuç veya kaynak yerine kullanılmamış; tüm akademik sorumluluk ve nihai değerlendirme tez yazarına ait olacak şekilde "
                "kontrol edilmiştir."
            ),
            "Özel metin": "",
        }

    def _ai_declaration_path(self):
        return self.template_dir / "etik-beyan.tex"

    def _load_ai_declaration_text(self):
        path = self._ai_declaration_path()
        if path.exists():
            return path.read_text(encoding="utf-8")
        return self._ai_declaration_templates()["Kullanılmadı"]

    def _build_ai_declaration_tab(self):
        self.ai_form_tab.columnconfigure(0, weight=1)
        self.ai_form_tab.rowconfigure(2, weight=1)
        ttk.Label(
            self.ai_form_tab,
            text="Üretken Yapay Zekâ Beyanı",
            font=("Segoe UI", 11, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            self.ai_form_tab,
            text="Bu metin etik-beyan.tex dosyasına kaydedilir ve tez.tex içindeki etik beyan girişine bağlanır. Hazır metinlerden birini seçebilir veya metni doğrudan düzenleyebilirsiniz.",
            wraplength=760,
            justify="left",
        ).grid(row=1, column=0, sticky="ew", pady=(4, 8))

        editor_frame = ttk.Frame(self.ai_form_tab)
        editor_frame.grid(row=2, column=0, sticky="nsew")
        editor_frame.columnconfigure(0, weight=1)
        editor_frame.rowconfigure(1, weight=1)
        top = ttk.Frame(editor_frame)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(top, text="Beyan türü").pack(side="left")
        self.ai_mode_var = tk.StringVar(value="Kullanılmadı")
        mode_box = ttk.Combobox(top, textvariable=self.ai_mode_var, state="readonly", values=list(self._ai_declaration_templates()), width=24)
        mode_box.pack(side="left", padx=(8, 8))
        ttk.Button(top, text="Şablonu Uygula", image=self._button_icon("apply"), compound="left", style="Mini.TButton", command=self.apply_ai_declaration_template).pack(side="left")
        ttk.Button(top, text="Kaydet", image=self._button_icon("save", "primary"), compound="left", style="PrimaryMini.TButton", command=self.save_ai_declaration).pack(side="right")

        text_frame = ttk.Frame(editor_frame)
        text_frame.grid(row=1, column=0, sticky="nsew")
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        self.ai_declaration_text = tk.Text(text_frame, wrap="word", height=16, font=("Segoe UI", 10), undo=True)
        self.ai_declaration_text.grid(row=0, column=0, sticky="nsew")
        y_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.ai_declaration_text.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        self.ai_declaration_text.configure(yscrollcommand=lambda first, last, sb=y_scroll: self._sync_scrollbar(sb, first, last))
        self.ai_declaration_text.insert("1.0", self._load_ai_declaration_text())
        self.ai_declaration_text.bind("<<Modified>>", self.on_ai_declaration_modified)
        mode_box.bind("<<ComboboxSelected>>", lambda _event: self.apply_ai_declaration_template())

    def apply_ai_declaration_template(self):
        if not hasattr(self, "ai_declaration_text"):
            return
        value = self._ai_declaration_templates().get(self.ai_mode_var.get(), "")
        if not value:
            return
        self.ai_declaration_text.delete("1.0", "end")
        self.ai_declaration_text.insert("1.0", value)
        self.ai_declaration_text.edit_modified(True)
        self.update_ai_preview()

    def on_ai_declaration_modified(self, _event=None):
        if not hasattr(self, "ai_declaration_text") or not self.ai_declaration_text.edit_modified():
            return
        self.ai_declaration_text.edit_modified(False)
        self.update_ai_preview()

    def save_ai_declaration(self):
        if not hasattr(self, "ai_declaration_text"):
            return
        content = self.ai_declaration_text.get("1.0", "end").strip() + "\n"
        self._ai_declaration_path().write_text(content, encoding="utf-8")
        self.ensure_etik_macro()
        self.last_saved_var.set("ÜYZ beyanı kaydedildi: " + datetime.now().strftime("%d.%m.%Y %H:%M"))
        self.update_ai_preview()
        self.refresh_missing()

    def _build_tex_tools(self, parent):
        self.tex_tool_buttons_frame = None

    def render_autosave_check(self):
        canvas = getattr(self, "autosave_check", None)
        if canvas is None:
            return
        colors = THEMES[self.theme_var.get()]
        bg = colors["panel"]
        border = colors["accent_dark"]
        tick = colors["accent"]
        canvas.configure(bg=bg)
        canvas.delete("all")
        canvas.create_rectangle(1, 1, 12, 12, fill=bg, outline=border, width=1)
        if self.autosave_var.get():
            canvas.create_line(3, 7, 6, 10, 11, 3, fill=tick, width=2, capstyle="round", joinstyle="round")

    def refresh_tex_tool_buttons(self):
        if self.tex_tool_buttons_frame is None:
            return
        for child in self.tex_tool_buttons_frame.winfo_children():
            child.destroy()
        for group in TEX_TOOL_GROUPS:
            button = ttk.Button(
                self.tex_tool_buttons_frame,
                text=group,
                width=max(6, min(len(group) + 1, 11)),
                style="Tiny.TButton",
                command=lambda name=group: self.open_tex_palette(name),
            )
            button.pack(side="left", padx=(0, 3))
            self.tooltips.append(ToolTip(button, lambda name=group: f"{name} paletini aç", placement="above"))

    def close_tex_palette(self):
        popup = getattr(self, "tex_palette_popup", None)
        if popup is not None:
            try:
                if popup.winfo_exists():
                    popup.withdraw()
            except tk.TclError:
                pass
        self.tex_palette_popup = None

    def clear_tex_palette_cache(self):
        if getattr(self, "tex_palette_warm_after_id", None):
            try:
                self.after_cancel(self.tex_palette_warm_after_id)
            except tk.TclError:
                pass
            self.tex_palette_warm_after_id = None
        self.tex_palette_popup = None
        for popup in list(getattr(self, "tex_palette_cache", {}).values()):
            try:
                if popup.winfo_exists():
                    popup.destroy()
            except tk.TclError:
                pass
        self.tex_palette_cache = {}

    def close_floating_tex_toolbar(self):
        if getattr(self, "tex_floating_after_id", None):
            try:
                self.after_cancel(self.tex_floating_after_id)
            except tk.TclError:
                pass
            self.tex_floating_after_id = None
        self.close_tex_palette()
        toolbar = getattr(self, "tex_floating_toolbar", None)
        if toolbar is not None:
            try:
                if toolbar.winfo_exists():
                    toolbar.destroy()
            except tk.TclError:
                pass
        self.tex_floating_toolbar = None
        self.tex_floating_entry = None

    def show_floating_tex_toolbar(self, entry):
        self.tex_floating_after_id = None
        try:
            if entry is None or not entry.winfo_exists() or not self.winfo_exists():
                return
        except tk.TclError:
            return
        old_toolbar = getattr(self, "tex_floating_toolbar", None)
        if old_toolbar is not None:
            try:
                if old_toolbar.winfo_exists():
                    self.tex_floating_entry = entry
                    self.position_floating_tex_toolbar(old_toolbar, entry)
                    old_toolbar.lift()
                    return
            except tk.TclError:
                pass
        colors = THEMES[self.theme_var.get()]
        toolbar = tk.Toplevel(self)
        self.tex_floating_toolbar = toolbar
        toolbar.overrideredirect(True)
        toolbar.transient(self)
        toolbar.configure(bg=colors["accent"])
        frame = tk.Frame(toolbar, bg=colors["panel"], padx=5, pady=4)
        frame.pack(fill="both", expand=True, padx=1, pady=1)
        ttk.Label(frame, text="TeX", style="Card.TLabel", font=("Segoe UI", 8, "bold")).pack(side="left", padx=(0, 5))
        for group in TEX_TOOL_GROUPS:
            button = ttk.Button(frame, text=group, width=max(5, min(len(group) + 1, 10)), style="Tiny.TButton")
            button.configure(command=lambda name=group, anchor=button: self.open_tex_palette(name, anchor=anchor))
            button.pack(side="left", padx=(0, 2))
        ttk.Button(frame, text="x", width=2, style="Tiny.TButton", command=self.close_floating_tex_toolbar).pack(side="left", padx=(4, 0))
        toolbar.update_idletasks()
        self.tex_floating_entry = entry
        self.position_floating_tex_toolbar(toolbar, entry)
        toolbar.lift()
        toolbar.bind("<Escape>", lambda _event: self.close_floating_tex_toolbar())

    def position_floating_tex_toolbar(self, toolbar, entry):
        if toolbar is None or entry is None:
            return
        screen_w = toolbar.winfo_screenwidth()
        screen_h = toolbar.winfo_screenheight()
        app_top = self.winfo_rooty()
        app_bottom = app_top + self.winfo_height()
        lower_limit = min(screen_h - 48, app_bottom - 8)
        upper_limit = max(8, app_top + 8)
        below_y = entry.winfo_rooty() + entry.winfo_height() + 4
        toolbar_h = toolbar.winfo_height()
        if below_y + toolbar_h <= lower_limit:
            y = below_y
        else:
            y = max(upper_limit, entry.winfo_rooty() - toolbar_h - 4)
        x = entry.winfo_rootx()
        if x + toolbar.winfo_width() > screen_w - 12:
            x = max(8, screen_w - toolbar.winfo_width() - 12)
        if x < 8:
            x = 8
        toolbar.geometry(f"+{x}+{y}")
        toolbar.update_idletasks()

    def warm_tex_palettes(self):
        groups = [group for group in TEX_TOOL_GROUPS if group not in self.tex_palette_cache]
        self._warm_tex_palette_groups(groups)

    def _warm_tex_palette_groups(self, groups):
        if not groups:
            self.tex_palette_warm_after_id = None
            return
        group = groups[0]
        try:
            anchor = self.tex_floating_toolbar or self
            self.open_tex_palette(group, anchor=anchor, show=False)
        except tk.TclError:
            pass
        self.tex_palette_warm_after_id = self.after(90, lambda rest=groups[1:]: self._warm_tex_palette_groups(rest))

    def open_tex_palette(self, group, anchor=None, show=True):
        items = TEX_TOOL_GROUPS.get(group, [])
        if not items:
            return
        anchor = anchor or self.tex_floating_toolbar or self
        cached = self.tex_palette_cache.get(group)
        if cached is not None:
            try:
                if cached.winfo_exists():
                    if show:
                        self.close_tex_palette()
                        self.tex_palette_popup = cached
                        cached.deiconify()
                        self.position_tex_palette(cached, anchor)
                        cached.lift()
                    return
            except tk.TclError:
                self.tex_palette_cache.pop(group, None)
        if show:
            self.close_tex_palette()
        colors = THEMES[self.theme_var.get()]
        popup = tk.Toplevel(self)
        self.tex_palette_popup = popup
        self.tex_palette_cache[group] = popup
        popup.title(group)
        popup.transient(self)
        popup.configure(bg=colors["panel"])
        popup.resizable(True, True)
        popup.columnconfigure(0, weight=1)
        popup.rowconfigure(1, weight=1)
        popup.protocol("WM_DELETE_WINDOW", self.close_tex_palette)
        if not show:
            popup.withdraw()
        header = tk.Frame(popup, bg=colors["panel"], padx=6, pady=4)
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text=group, style="Card.TLabel", font=("Segoe UI", 9, "bold")).pack(side="left")
        body = ttk.Frame(popup, style="Card.TFrame")
        body.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)
        canvas = tk.Canvas(body, width=420, height=min(340, max(96, ((len(items) + 7) // 8) * 34)), bg=colors["panel"], highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        y_scroll = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll = ttk.Scrollbar(body, orient="horizontal", command=canvas.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")
        inner = ttk.Frame(canvas, style="Card.TFrame")
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(
            yscrollcommand=lambda first, last, sb=y_scroll: self._sync_scrollbar(sb, first, last),
            xscrollcommand=lambda first, last, sb=x_scroll: self._sync_scrollbar(sb, first, last),
        )

        def sync(_event=None):
            canvas.update_idletasks()
            canvas.itemconfigure(window_id, width=max(inner.winfo_reqwidth(), 1))
            canvas.configure(scrollregion=canvas.bbox("all"))
            self._sync_scrollbar(y_scroll, *canvas.yview())
            self._sync_scrollbar(x_scroll, *canvas.xview())

        inner.bind("<Configure>", sync)
        columns = 8 if len(items) > 16 else 6
        for index, (label, snippet, tip) in enumerate(items):
            row, col = divmod(index, columns)
            btn = ttk.Button(
                inner,
                text=label,
                width=5,
                style="Tiny.TButton",
                command=lambda value=snippet: (self.insert_tex_snippet(value), self.close_tex_palette()),
            )
            btn.grid(row=row, column=col, padx=1, pady=1, sticky="nsew")

        if show:
            self.position_tex_palette(popup, anchor, inner=inner, header=header, canvas=canvas)
            popup.lift()
        else:
            self.position_tex_palette(popup, anchor, inner=inner, header=header, canvas=canvas)
            popup.withdraw()
            self.tex_palette_popup = None
        popup.bind("<Escape>", lambda _event: self.close_tex_palette())

    def position_tex_palette(self, popup, anchor, inner=None, header=None, canvas=None):
        if popup is None or anchor is None:
            return
        popup.update_idletasks()
        screen_w = popup.winfo_screenwidth()
        screen_h = popup.winfo_screenheight()
        if inner is not None and header is not None and canvas is not None:
            max_w = max(280, min(720, screen_w - 32))
            max_h = max(180, min(520, screen_h - 96))
            inner_w = max(inner.winfo_reqwidth(), 240)
            inner_h = max(inner.winfo_reqheight(), 80)
            canvas_w = min(inner_w, max_w - 24)
            canvas_h = min(inner_h, max_h - header.winfo_reqheight() - 28)
            canvas.configure(width=canvas_w, height=max(96, canvas_h))
            popup.update_idletasks()

        x = anchor.winfo_rootx()
        below_y = anchor.winfo_rooty() + anchor.winfo_height() + 2
        app_top = self.winfo_rooty()
        app_bottom = app_top + self.winfo_height()
        lower_limit = min(screen_h - 48, app_bottom - 8)
        upper_limit = max(8, app_top + 8)
        popup_h = popup.winfo_height()
        space_below = lower_limit - below_y
        space_above = anchor.winfo_rooty() - upper_limit
        if space_below < popup_h and space_above > space_below:
            y = max(upper_limit, anchor.winfo_rooty() - popup_h - 2)
        else:
            y = min(below_y, max(upper_limit, lower_limit - popup_h))
        if x + popup.winfo_width() > screen_w - 12:
            x = max(8, screen_w - popup.winfo_width() - 12)
        if x < 8:
            x = 8
        popup.geometry(f"+{x}+{y}")

    def register_tex_entry(self, key, entry):
        self.tex_entry_keys[entry] = key
        entry.bind("<FocusIn>", lambda _event, w=entry: self._set_active_tex_entry(w), add="+")
        entry.bind("<Button-1>", lambda _event, w=entry: self._set_active_tex_entry(w), add="+")

    def _is_descendant_of(self, widget, parent):
        if widget is None or parent is None:
            return False
        try:
            while widget is not None:
                if widget == parent:
                    return True
                widget = widget.master
        except tk.TclError:
            return False
        return False

    def _maybe_close_floating_tex_tools(self, event):
        toolbar = getattr(self, "tex_floating_toolbar", None)
        palette = getattr(self, "tex_palette_popup", None)
        entry = getattr(self, "tex_floating_entry", None)
        try:
            toolbar_open = toolbar is not None and toolbar.winfo_exists()
            palette_open = palette is not None and palette.winfo_exists() and palette.winfo_viewable()
        except tk.TclError:
            toolbar_open = False
            palette_open = False
        if not toolbar_open and not palette_open:
            return
        widget = getattr(event, "widget", None)
        if widget in self.tex_entry_keys:
            return
        if entry is not None and self._is_descendant_of(widget, entry):
            return
        if toolbar_open and self._is_descendant_of(widget, toolbar):
            return
        if palette_open and self._is_descendant_of(widget, palette):
            return
        self.close_floating_tex_toolbar()

    def _maybe_clear_form_focus(self, event):
        widget = getattr(event, "widget", None)
        if widget is None:
            return
        try:
            if widget.winfo_toplevel() is not self:
                return
        except tk.TclError:
            return
        if widget in self.tex_entry_keys:
            return
        if any(widget == entry or self._is_descendant_of(widget, entry) for entry, _placeholder in self.placeholder_entries.values()):
            return
        try:
            if isinstance(widget, (tk.Entry, ttk.Entry, ttk.Combobox, tk.Text)):
                return
        except tk.TclError:
            return
        for key in list(self.placeholder_entries):
            self._set_placeholder(key)
        try:
            self.focus_set()
        except tk.TclError:
            pass

    def _set_active_tex_entry(self, entry):
        self.active_tex_entry = entry
        if getattr(self, "tex_floating_after_id", None):
            try:
                self.after_cancel(self.tex_floating_after_id)
            except tk.TclError:
                pass
        self.tex_floating_after_id = self.after(80, lambda w=entry: self.show_floating_tex_toolbar(w))

    def _target_tex_entry(self):
        focused = self.focus_get()
        if focused in self.tex_entry_keys:
            self.active_tex_entry = focused
            return focused
        if self.active_tex_entry is not None and self.active_tex_entry.winfo_exists():
            return self.active_tex_entry
        return None

    def insert_tex_snippet(self, snippet):
        entry = self._target_tex_entry()
        if entry is None:
            messagebox.showinfo("TeX aracı", "Önce başlık, anahtar kelime veya benzeri bir metin alanına tıklayın.")
            return
        key = self.tex_entry_keys.get(entry)
        if key:
            self._clear_placeholder(key)
        try:
            selection_start = entry.index("sel.first")
            selection_end = entry.index("sel.last")
            selected_text = entry.get()[selection_start:selection_end]
        except tk.TclError:
            selection_start = entry.index("insert")
            selection_end = selection_start
            selected_text = ""

        marker_index = snippet.find("|")
        if marker_index >= 0:
            insert_text = snippet.replace("|", selected_text)
            cursor_offset = marker_index + len(selected_text)
        else:
            insert_text = snippet
            cursor_offset = len(insert_text)

        entry.delete(selection_start, selection_end)
        entry.insert(selection_start, insert_text)
        entry.icursor(selection_start + cursor_offset)
        entry.focus_set()

    def _add_tooltip(self, widget, key, placement="below"):
        def text_for(k=key):
            text = TOOLTIPS["en" if self.lang_var.get() == "English" else "tr"].get(k, "")
            if k == "update_app" and self.update_status_text:
                return f"{self.update_status_text}\n{text}"
            return text
        self.tooltips.append(ToolTip(widget, text_for, placement=placement))

    def _button_icon(self, kind, tone="normal"):
        colors = THEMES[self.theme_var.get()]
        icon_color = colors["accent_dark"] if tone == "primary" else colors["accent"]
        cache_key = (kind, icon_color)
        if cache_key in self.button_images:
            return self.button_images[cache_key]
        mdl2 = self._mdl2_icon(kind, icon_color)
        if mdl2 is not None:
            self.button_images[cache_key] = mdl2
            return mdl2
        scale = 3
        image = Image.new("RGBA", (18 * scale, 18 * scale), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        accent = icon_color
        white = "#ffffff"

        def box(x0, y0, x1, y1, **kwargs):
            draw.rectangle((x0 * scale, y0 * scale, x1 * scale, y1 * scale), **kwargs)

        def line(points, **kwargs):
            draw.line([(x * scale, y * scale) for x, y in points], **kwargs)

        width = max(2, 2 * scale)
        accent = icon_color
        if kind == "save":
            draw.rounded_rectangle((3 * scale, 2 * scale, 15 * scale, 16 * scale), radius=2 * scale, fill=accent)
            box(5, 4, 13, 8, fill=white)
            box(11, 4, 13, 7, fill=accent)
            box(6, 11, 12, 15, fill=white)
        elif kind == "write":
            draw.rounded_rectangle((3 * scale, 2 * scale, 15 * scale, 16 * scale), radius=2 * scale, fill=accent)
            box(5, 4, 13, 8, fill=white)
            box(11, 4, 13, 7, fill=accent)
            box(6, 11, 12, 15, fill=white)
            line([(5, 13), (12, 13)], fill=accent, width=scale)
        elif kind == "undo":
            draw.arc((4 * scale, 4 * scale, 15 * scale, 15 * scale), start=80, end=330, fill=accent, width=width)
            draw.polygon([(4 * scale, 8 * scale), (4 * scale, 3 * scale), (8 * scale, 6 * scale)], fill=accent)
        elif kind == "redo":
            draw.arc((3 * scale, 4 * scale, 14 * scale, 15 * scale), start=210, end=100, fill=accent, width=width)
            draw.polygon([(14 * scale, 8 * scale), (14 * scale, 3 * scale), (10 * scale, 6 * scale)], fill=accent)
        elif kind == "refresh":
            draw.arc((3 * scale, 3 * scale, 15 * scale, 15 * scale), start=35, end=310, fill=accent, width=width)
            draw.polygon([(15 * scale, 4 * scale), (16 * scale, 9 * scale), (11 * scale, 8 * scale)], fill=accent)
        elif kind == "apply":
            draw.rounded_rectangle((3 * scale, 3 * scale, 14 * scale, 15 * scale), radius=2 * scale, outline=accent, width=width)
            line([(5, 10), (8, 13), (14, 6)], fill=accent, width=width)
        elif kind == "check":
            draw.ellipse((2 * scale, 2 * scale, 16 * scale, 16 * scale), outline=accent, width=width)
            line([(5, 10), (8, 13), (13, 6)], fill=accent, width=width)
        elif kind == "missing":
            draw.polygon([(9 * scale, 2 * scale), (16 * scale, 15 * scale), (2 * scale, 15 * scale)], outline=accent, fill=None)
            draw.line([(9 * scale, 6 * scale), (9 * scale, 11 * scale)], fill=accent, width=width)
            draw.ellipse((8 * scale, 13 * scale, 10 * scale, 15 * scale), fill=accent)
        elif kind == "package":
            draw.polygon([(4 * scale, 6 * scale), (9 * scale, 3 * scale), (14 * scale, 6 * scale), (9 * scale, 9 * scale)], outline=accent, fill=None)
            draw.polygon([(4 * scale, 6 * scale), (9 * scale, 9 * scale), (9 * scale, 16 * scale), (4 * scale, 13 * scale)], outline=accent, fill=None)
            draw.polygon([(14 * scale, 6 * scale), (9 * scale, 9 * scale), (9 * scale, 16 * scale), (14 * scale, 13 * scale)], outline=accent, fill=None)
        elif kind == "declaration":
            draw.rounded_rectangle((4 * scale, 2 * scale, 13 * scale, 16 * scale), radius=1 * scale, outline=accent, width=width)
            line([(7, 6), (11, 6)], fill=accent, width=scale)
            line([(7, 9), (11, 9)], fill=accent, width=scale)
            line([(10, 14), (16, 8)], fill=accent, width=width)
            draw.polygon([(15 * scale, 7 * scale), (17 * scale, 5 * scale), (16 * scale, 9 * scale)], fill=accent)
        elif kind == "spell":
            draw.ellipse((2 * scale, 2 * scale, 11 * scale, 11 * scale), outline=accent, width=width)
            line([(10, 10), (15, 15)], fill=accent, width=width)
            draw.line([(5 * scale, 10 * scale), (7 * scale, 5 * scale), (9 * scale, 10 * scale)], fill=accent, width=scale)
            draw.line([(6 * scale, 8 * scale), (8 * scale, 8 * scale)], fill=accent, width=scale)
        elif kind == "smart_spell":
            try:
                letter_font = ImageFont.truetype("segoeuib.ttf", 8 * scale)
                badge_font = ImageFont.truetype("segoeuib.ttf", 5 * scale)
            except Exception:
                letter_font = ImageFont.load_default()
                badge_font = ImageFont.load_default()
            draw.ellipse((1 * scale, 2 * scale, 11 * scale, 12 * scale), outline=accent, width=width)
            line([(10, 11), (15, 16)], fill=accent, width=width)
            draw.text((4 * scale, 2 * scale), "ğ", font=letter_font, fill=accent)
            draw.polygon(
                [
                    (13 * scale, 1 * scale),
                    (15 * scale, 5 * scale),
                    (18 * scale, 6 * scale),
                    (15 * scale, 8 * scale),
                    (14 * scale, 12 * scale),
                    (11 * scale, 9 * scale),
                    (8 * scale, 10 * scale),
                    (11 * scale, 6 * scale),
                ],
                fill="#F29F05",
            )
            draw.rounded_rectangle((9 * scale, 0, 18 * scale, 6 * scale), radius=2 * scale, fill="#EAF7EA", outline="#F29F05", width=scale)
            draw.text((10 * scale, 0), "AI", font=badge_font, fill=accent)
        elif kind == "clean":
            draw.rectangle((5 * scale, 6 * scale, 14 * scale, 16 * scale), outline=accent, width=width)
            line([(4, 5), (15, 5)], fill=accent, width=width)
            line([(7, 3), (12, 3)], fill=accent, width=width)
            line([(8, 8), (8, 14)], fill=accent, width=scale)
            line([(11, 8), (11, 14)], fill=accent, width=scale)
        elif kind == "pdf_folder":
            draw.rounded_rectangle((2 * scale, 6 * scale, 15 * scale, 15 * scale), radius=2 * scale, fill=accent)
            box(4, 4, 9, 7, fill=accent)
            draw.rectangle((9 * scale, 2 * scale, 16 * scale, 10 * scale), fill=white, outline=accent, width=scale)
            line([(10, 5), (15, 5)], fill=accent, width=scale)
            line([(10, 8), (14, 8)], fill=accent, width=scale)
        elif kind == "theorem":
            try:
                font = ImageFont.truetype("consola.ttf", 15 * scale)
            except Exception:
                font = ImageFont.load_default()
            draw.text((2 * scale, 0), "{", font=font, fill=accent)
            draw.text((11 * scale, 0), "}", font=font, fill=accent)
            line([(7, 9), (11, 9)], fill=accent, width=scale)
        elif kind == "smart_tex":
            try:
                font = ImageFont.truetype("consola.ttf", 14 * scale)
                badge_font = ImageFont.truetype("segoeuib.ttf", 5 * scale)
            except Exception:
                font = ImageFont.load_default()
                badge_font = ImageFont.load_default()
            draw.text((1 * scale, 1 * scale), "{", font=font, fill=accent)
            draw.text((8 * scale, 1 * scale), "}", font=font, fill=accent)
            draw.polygon(
                [
                    (13 * scale, 2 * scale),
                    (15 * scale, 6 * scale),
                    (18 * scale, 7 * scale),
                    (15 * scale, 9 * scale),
                    (14 * scale, 14 * scale),
                    (11 * scale, 10 * scale),
                    (7 * scale, 11 * scale),
                    (10 * scale, 7 * scale),
                ],
                fill="#F29F05",
            )
            draw.rounded_rectangle((10 * scale, 0, 18 * scale, 6 * scale), radius=2 * scale, fill="#EAF7EA", outline="#F29F05", width=scale)
            draw.text((11 * scale, 0), "AI", font=badge_font, fill=accent)
        elif kind == "convert":
            draw.rounded_rectangle((2 * scale, 3 * scale, 9 * scale, 13 * scale), radius=1 * scale, outline=accent, width=scale)
            draw.rounded_rectangle((9 * scale, 5 * scale, 16 * scale, 15 * scale), radius=1 * scale, outline=accent, width=scale)
            line([(7, 9), (13, 9)], fill=accent, width=width)
            draw.polygon([(13 * scale, 6 * scale), (16 * scale, 9 * scale), (13 * scale, 12 * scale)], fill=accent)
        elif kind == "update":
            arrow_width = max(3, 2 * scale)
            if tone == "primary":
                draw.arc((4 * scale, 4 * scale, 14 * scale, 14 * scale), start=205, end=355, fill=accent, width=arrow_width)
                draw.polygon([(14 * scale, 5 * scale), (16 * scale, 9 * scale), (12 * scale, 9 * scale)], fill=accent)
                draw.arc((4 * scale, 4 * scale, 14 * scale, 14 * scale), start=25, end=175, fill=accent, width=arrow_width)
                draw.polygon([(4 * scale, 13 * scale), (2 * scale, 9 * scale), (6 * scale, 9 * scale)], fill=accent)
            else:
                draw.ellipse((1 * scale, 1 * scale, 17 * scale, 17 * scale), fill=accent, outline=accent)
                draw.arc((4 * scale, 4 * scale, 14 * scale, 14 * scale), start=205, end=355, fill=white, width=arrow_width)
                draw.polygon([(14 * scale, 5 * scale), (16 * scale, 9 * scale), (12 * scale, 9 * scale)], fill=white)
                draw.arc((4 * scale, 4 * scale, 14 * scale, 14 * scale), start=25, end=175, fill=white, width=arrow_width)
                draw.polygon([(4 * scale, 13 * scale), (2 * scale, 9 * scale), (6 * scale, 9 * scale)], fill=white)
        elif kind == "update_ready":
            arrow_width = max(3, 2 * scale)
            draw.arc((4 * scale, 4 * scale, 14 * scale, 14 * scale), start=205, end=355, fill=accent, width=arrow_width)
            draw.polygon([(14 * scale, 5 * scale), (16 * scale, 9 * scale), (12 * scale, 9 * scale)], fill=accent)
            draw.arc((4 * scale, 4 * scale, 14 * scale, 14 * scale), start=25, end=175, fill=accent, width=arrow_width)
            draw.polygon([(4 * scale, 13 * scale), (2 * scale, 9 * scale), (6 * scale, 9 * scale)], fill=accent)
            draw.ellipse((11 * scale, 1 * scale, 18 * scale, 8 * scale), fill="#F29F05", outline="#B96B00", width=scale)
        elif kind == "preview":
            draw.ellipse((3 * scale, 3 * scale, 12 * scale, 12 * scale), outline=accent, width=width)
            draw.ellipse((6 * scale, 6 * scale, 9 * scale, 9 * scale), fill=accent)
            line([(11, 11), (15, 15)], fill=accent, width=width)
        elif kind == "folder":
            draw.rounded_rectangle((3 * scale, 6 * scale, 15 * scale, 15 * scale), radius=2 * scale, fill=accent)
            box(5, 4, 10, 7, fill=accent)
        elif kind == "read":
            draw.rounded_rectangle((3 * scale, 3 * scale, 14 * scale, 15 * scale), radius=2 * scale, outline=accent, width=width)
            line([(6, 7), (12, 7)], fill=accent, width=scale)
            line([(6, 10), (12, 10)], fill=accent, width=scale)
            line([(6, 13), (10, 13)], fill=accent, width=scale)
        else:
            draw.rounded_rectangle((3 * scale, 6 * scale, 15 * scale, 15 * scale), radius=2 * scale, fill=accent)
            box(5, 4, 10, 7, fill=accent)
        image = image.resize((22, 22) if kind == "update" else (18, 18), Image.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        self.button_images[cache_key] = photo
        return photo

    def _mdl2_icon(self, kind, color):
        glyphs = {
            "save": "\uE74E",
            "write": "\uE74E",
            "undo": "\uE7A7",
            "redo": "\uE7A6",
            "preview": "\uE721",
            "folder": "\uE8B7",
            "read": "\uE8E5",
        }
        glyph = glyphs.get(kind)
        font_path = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "segmdl2.ttf"
        if not glyph or not font_path.exists():
            return None
        try:
            font = ImageFont.truetype(str(font_path), 16)
            image = Image.new("RGBA", (22, 22), (255, 255, 255, 0))
            draw = ImageDraw.Draw(image)
            bbox = draw.textbbox((0, 0), glyph, font=font)
            x = (22 - (bbox[2] - bbox[0])) / 2 - bbox[0]
            y = (22 - (bbox[3] - bbox[1])) / 2 - bbox[1]
            draw.text((x, y), glyph, font=font, fill=color)
            return ImageTk.PhotoImage(image)
        except Exception:
            return None

    def _sync_scrollbar(self, scrollbar, first, last):
        scrollbar.set(first, last)
        try:
            full_range = float(first) <= 0 and float(last) >= 1
        except (TypeError, ValueError):
            full_range = False
        if full_range:
            scrollbar.grid_remove()
        else:
            scrollbar.grid()

    def _sync_main_canvas(self, _event=None):
        if not hasattr(self, "main_canvas"):
            return
        if self.main_canvas_sync_after_id is not None:
            return
        self.main_canvas_sync_after_id = self.after_idle(self._apply_main_canvas_sync)

    def _apply_main_canvas_sync(self):
        self.main_canvas_sync_after_id = None
        if not hasattr(self, "main_canvas"):
            return
        req_width = self.main_container.winfo_reqwidth()
        req_height = self.main_container.winfo_reqheight()
        canvas_width = max(self.main_canvas.winfo_width(), 1)
        canvas_height = max(self.main_canvas.winfo_height(), 1)
        self.main_canvas.itemconfigure(self.main_canvas_window, width=max(req_width, canvas_width), height=max(req_height, canvas_height))
        self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        if hasattr(self, "main_y_scroll"):
            self._sync_scrollbar(self.main_y_scroll, *self.main_canvas.yview())
            self._sync_scrollbar(self.main_x_scroll, *self.main_canvas.xview())

    def _build_form_pages(self):
        cover_sections = {
            "Öğrenci": None,
            "Program": None,
            "Başlık": None,
            "Danışman": None,
            "Anahtar Kelimeler": None,
        }
        approval_sections = {
            "Tarih ve Karar": None,
            "Jüri": None,
        }
        self._build_scroll_form(self.cover_form_tab, cover_sections)
        self._build_scroll_form(self.approval_form_tab, approval_sections)

    def _build_scroll_form(self, parent, section_filter):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        canvas = tk.Canvas(parent, highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        self.themed_canvases.append(canvas)
        y_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        x_scrollbar = ttk.Scrollbar(parent, orient="horizontal", command=canvas.xview)
        x_scrollbar.grid(row=1, column=0, sticky="ew")
        canvas.configure(
            yscrollcommand=lambda first, last, sb=y_scrollbar: self._sync_scrollbar(sb, first, last),
            xscrollcommand=lambda first, last, sb=x_scrollbar: self._sync_scrollbar(sb, first, last),
        )
        inner = ttk.Frame(canvas)
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        def sync_canvas(_event=None, c=canvas, w=window_id, child=inner):
            c.update_idletasks()
            req_width = max(child.winfo_reqwidth(), 760)
            req_height = child.winfo_reqheight()
            view_width = max(c.winfo_width() - 4, 1)
            view_height = max(c.winfo_height() - 4, 1)
            c.itemconfigure(w, width=max(req_width, view_width), height=max(req_height, view_height))
            c.configure(scrollregion=c.bbox("all"))
            self._sync_scrollbar(y_scrollbar, *c.yview())
            self._sync_scrollbar(x_scrollbar, *c.xview())
        inner.bind("<Configure>", sync_canvas)
        canvas.bind("<Configure>", sync_canvas)
        canvas.bind("<Enter>", lambda _event, c=canvas: self._bind_mousewheel(c))
        canvas.bind("<Leave>", lambda _event, c=self.main_canvas: self._bind_mousewheel(c))

        row = 0
        for section, fields in FIELDS:
            if section not in section_filter:
                continue
            allowed = section_filter[section]
            visible_fields = [field for field in fields if allowed is None or field[0] in allowed]
            section_title = SECTION_LABEL_EN.get(section, section) if self.lang_var.get() == "English" else section
            note = SECTION_NOTES.get(section, {}).get("en" if self.lang_var.get() == "English" else "tr")
            top_pad = 2 if row == 0 else 8
            header_frame = ttk.Frame(inner)
            header_frame.grid(row=row, column=0, columnspan=6, sticky="w", pady=(top_pad, 3))
            ttk.Label(header_frame, text=section_title + ("  " if note else ""), font=("Segoe UI", 12, "bold")).pack(side="left")
            if note:
                ttk.Label(header_frame, text=f"({note})", font=("Segoe UI", 9, "italic"), foreground=THEMES[self.theme_var.get()]["accent"]).pack(side="left")
            row += 1
            rows = self._pair_fields(visible_fields)
            for left_field, right_field in rows:
                next_row = self._add_field_pair(inner, row, left_field, right_field)
                row = next_row
        inner.columnconfigure(1, weight=1)
        inner.columnconfigure(4, weight=1)

    def _pair_fields(self, fields):
        visible = [field for field in fields if field[0] not in SKIP_FORM_KEYS or field[0] in DATE_FORM_KEYS]
        by_key = {field[0]: field for field in visible}
        used = set()
        pairs = []
        preferred_pairs = [
            ("ad", "soyad"), ("ogrencino", "unvan"),
            ("anabilimdali_tr", "anabilimdali_en"), ("program_tr", "program_en"),
            ("baslik1", "title1"), ("baslik2", "title2"), ("baslik3", "title3"),
            ("danisman_tr", "danisman_en"), ("danisman_kurum_tr", "danisman_kurum_en"),
            ("bap_proje_no", None),
            ("esdanisman_tr", "esdanisman_en"), ("esdanisman_kurum_tr", "esdanisman_kurum_en"),
            ("anahtarkelimeler", "keywords"),
            ("tarih_tr", "tezverme_tr"), ("savunma_tr", "kurul_tarih"),
            ("kapakyili", "kapaksehri"), ("oy", "kurul_no"), ("mudur", None),
            ("juri1", "juri1_kurum"), ("juri2", "juri2_kurum"), ("juri3", "juri3_kurum"),
            ("juri4", "juri4_kurum"), ("juri5", "juri5_kurum"),
        ]
        english_first = is_english_thesis_label(self.thesis_language_var.get())
        for left_key, right_key in preferred_pairs:
            if left_key not in by_key:
                continue
            left = by_key[left_key]
            right = by_key.get(right_key) if right_key else None
            used.add(left_key)
            if right_key:
                used.add(right_key)
            if english_first and right is not None and (left_key.endswith("_tr") or left_key.startswith("baslik") or left_key == "anahtarkelimeler"):
                pairs.append((right, left))
            else:
                pairs.append((left, right))
        for field in visible:
            if field[0] not in used:
                pairs.append((field, None))
        return pairs

    def _add_field_pair(self, parent, row, left_field, right_field):
        self._add_field_cell(parent, row, left_field, 0)
        if right_field is not None:
            self._add_field_cell(parent, row, right_field, 3)
        return row + 1

    def _add_field_cell(self, parent, row, field, start_col):
        key, label, _macro, _index = field
        if key in ("tarih_tr", "tezverme_tr", "savunma_tr", "kurul_tarih"):
            self._add_date_row(parent, row, key, label, start_col)
        else:
            self._add_text_row(parent, row, key, label, start_col)

    def _add_text_row(self, parent, row, key, label, start_col=0):
        label = FIELD_LABEL_EN.get(key, label) if self.lang_var.get() == "English" else label
        label_widget = ttk.Label(parent, text=label, style="Field.TLabel")
        label_widget.grid(row=row, column=start_col, sticky="w", padx=(12, 6), pady=2)
        var = self.vars.setdefault(key, tk.StringVar())
        self._trace_var(var)
        if key == "anabilimdali_tr":
            entry = ttk.Combobox(parent, textvariable=var, values=DEPARTMENT_OPTIONS, state="readonly", width=22)
            entry.bind("<<ComboboxSelected>>", lambda _event, k=key: (self._mark_manual_value(k), self.on_department_select()))
            self.combo_entries.append(entry)
        elif key == "oy":
            entry = ttk.Combobox(parent, textvariable=var, values=["Oy birliği", "Oy çokluğu"], state="readonly", width=22)
            entry.bind("<<ComboboxSelected>>", lambda _event, k=key: self._mark_manual_value(k))
            self.combo_entries.append(entry)
        elif key in AUTO_DERIVED_KEYS:
            width = 24
            entry = tk.Entry(parent, textvariable=var, width=width, relief="flat", borderwidth=0, highlightthickness=1, state="readonly")
            self.text_entries.append(entry)
        else:
            width = 24
            entry = tk.Entry(parent, textvariable=var, width=width, relief="flat", borderwidth=0, highlightthickness=1)
            self.text_entries.append(entry)
            self.register_tex_entry(key, entry)
        self._install_placeholder(key, entry)
        entry.grid(row=row, column=start_col + 1, sticky="ew", pady=2)
        hint = ttk.Label(parent, text="", foreground="#666666")
        hint.grid(row=row, column=start_col + 2, sticky="w", padx=(2, 0), pady=2)
        self.field_widgets[key] = (label_widget, entry, hint)

    def _install_placeholder(self, key, entry):
        placeholder = self._placeholder_for(key)
        if not placeholder:
            return
        self.placeholder_entries[key] = (entry, placeholder)
        if key not in AUTO_DERIVED_KEYS:
            entry.bind("<FocusIn>", lambda _event, k=key: self._clear_placeholder(k))
        entry.bind("<FocusOut>", lambda _event, k=key: self._on_field_focus_out(k))
        self._set_placeholder(key)

    def _on_field_focus_out(self, key):
        if not self.loading_form:
            self.normalize_one_field(key, include_focused=True)
            if key not in AUTO_DERIVED_KEYS:
                self.sync_derived_fields(force=True)
            self.update_preview()
        self._set_placeholder(key)

    def _set_placeholder(self, key):
        entry, placeholder = self.placeholder_entries.get(key, (None, ""))
        if entry is None:
            return
        var = self.vars.get(key)
        if var is not None and not var.get().strip():
            var.set(placeholder)
            self.placeholder_active_keys.add(key)
            self._configure_placeholder_color(entry, True)

    def _clear_placeholder(self, key):
        entry, placeholder = self.placeholder_entries.get(key, (None, ""))
        var = self.vars.get(key)
        if entry is not None and var is not None and key in self.placeholder_active_keys and var.get() == placeholder:
            var.set("")
            self.placeholder_active_keys.discard(key)
            self._configure_placeholder_color(entry, False)

    def _mark_manual_value(self, key):
        entry, _placeholder = self.placeholder_entries.get(key, (None, ""))
        self.placeholder_active_keys.discard(key)
        if entry is not None:
            self._configure_placeholder_color(entry, False)

    def _refresh_placeholders(self):
        for key in self.placeholder_entries:
            entry, old_placeholder = self.placeholder_entries[key]
            new_placeholder = self._placeholder_for(key)
            if new_placeholder != old_placeholder:
                var = self.vars.get(key)
                if var is not None and key in self.placeholder_active_keys and var.get() == old_placeholder:
                    var.set("")
                self.placeholder_entries[key] = (entry, new_placeholder)
            self._set_placeholder(key)

    def _placeholder_for(self, key):
        hints = FORMAT_HINTS_EN if self.lang_var.get() == "English" else FORMAT_HINTS
        if key in hints:
            return hints[key]
        for _section, fields in FIELDS:
            for field_key, label, _macro, _index in fields:
                if field_key == key:
                    return FIELD_LABEL_EN.get(key, label) if self.lang_var.get() == "English" else label
        return ""

    def _configure_placeholder_color(self, entry, is_placeholder):
        colors = THEMES[self.theme_var.get()]
        try:
            kwargs = {"fg": colors["muted"] if is_placeholder else colors["text_fg"]}
            if str(entry.cget("state")) == "readonly":
                kwargs["readonlybackground"] = colors["input_bg"]
            entry.configure(**kwargs)
        except tk.TclError:
            pass

    def _field_value(self, key):
        var = self.vars.get(key)
        value = var.get().strip() if var is not None else ""
        placeholder = self.placeholder_entries.get(key, (None, None))[1]
        if key in self.placeholder_active_keys and placeholder:
            if value == placeholder:
                return ""
            self.placeholder_active_keys.discard(key)
        return value

    def _field_output_value(self, key):
        var = self.vars.get(key)
        value = var.get().strip() if var is not None else ""
        placeholder = self.placeholder_entries.get(key, (None, None))[1]
        if placeholder and key in self.placeholder_active_keys and value == placeholder:
            return ""
        return value

    def _field_has_manual_value(self, key):
        value = self._field_value(key)
        return bool(value) and not any(pattern in value for pattern in PLACEHOLDER_PATTERNS)

    def sync_programme_fields(self):
        program_tr = self._field_value("program_tr")
        department_tr = self._field_value("anabilimdali_tr")
        program_en_var = self.vars.get("program_en")
        if program_en_var is None:
            return
        if not program_tr or program_same_as_department(program_tr, department_tr):
            if not self._field_has_manual_value("program_en") or program_same_as_department(self._field_value("program_en"), self._field_value("anabilimdali_en")):
                program_en_var.set("")
                self.placeholder_active_keys.discard("program_en")
                self._set_placeholder("program_en")
            return
        current_en = self._field_value("program_en")
        last_auto = self.auto_derived_values.get("program_en", "")
        derived = translate_program_to_english(program_tr)
        if not current_en or current_en == last_auto or any(pattern in current_en for pattern in PLACEHOLDER_PATTERNS):
            program_en_var.set(derived)
            self.auto_derived_values["program_en"] = derived

    def translate_person_title(self, value):
        result = normalize_person_name(value or "", "tr")
        for pattern, replacement in TITLE_TRANSLATIONS:
            result = pattern.sub(replacement, result)
        return re.sub(r"\s+", " ", result).strip()

    def translate_institution(self, value):
        result = latex_to_text(value or "")
        for source, target in INSTITUTION_TRANSLATIONS.items():
            if result.casefold() == source.casefold():
                return target
        result = re.sub(r"\bÜniversitesi\b", "University", result)
        result = re.sub(r"\bUniversitesi\b", "University", result)
        return re.sub(r"\s+", " ", result).strip()

    def _auto_fill_if_empty(self, key, value):
        var = self.vars.get(key)
        if var is None or not value:
            return
        if not self._field_has_manual_value(key):
            var.set(value)

    def sync_derived_fields(self, force=False, normalize_focused=False):
        pairs = [
            ("danisman_tr", "danisman_en", self.translate_person_title),
            ("danisman_kurum_tr", "danisman_kurum_en", self.translate_institution),
            ("esdanisman_tr", "esdanisman_en", self.translate_person_title),
            ("esdanisman_kurum_tr", "esdanisman_kurum_en", self.translate_institution),
        ]
        previous_loading = self.loading_form
        self.loading_form = True
        try:
            if normalize_focused:
                self.normalize_form_values(include_focused=True)
            for source_key, target_key, translator in pairs:
                source_value = self._field_value(source_key)
                target_var = self.vars.get(target_key)
                if not target_var:
                    continue
                derived = translator(source_value)
                current = self._field_value(target_key)
                last_auto = self.auto_derived_values.get(target_key, "")
                should_update = force or target_key in AUTO_DERIVED_KEYS or not current or current == last_auto or any(pattern in current for pattern in PLACEHOLDER_PATTERNS)
                if should_update:
                    target_var.set(derived)
                    self._mark_manual_value(target_key)
                    self.auto_derived_values[target_key] = derived
        finally:
            self.loading_form = previous_loading

    def _field_normalizers(self):
        return {
            "soyad": lambda value: tr_upper(normalize_punctuation_spacing(value)),
            "kapaksehri": lambda value: tr_upper(normalize_punctuation_spacing(value)),
            "danisman_tr": lambda value: normalize_person_name(value, "tr"),
            "esdanisman_tr": lambda value: normalize_person_name(value, "tr"),
            "juri1": lambda value: normalize_person_name(value, "tr"),
            "juri2": lambda value: normalize_person_name(value, "tr"),
            "juri3": lambda value: normalize_person_name(value, "tr"),
            "juri4": lambda value: normalize_person_name(value, "tr"),
            "juri5": lambda value: normalize_person_name(value, "tr"),
            "danisman_kurum_tr": normalize_punctuation_spacing,
            "esdanisman_kurum_tr": normalize_punctuation_spacing,
            "baslik1": normalize_punctuation_spacing,
            "baslik2": normalize_punctuation_spacing,
            "baslik3": normalize_punctuation_spacing,
            "title1": normalize_punctuation_spacing,
            "title2": normalize_punctuation_spacing,
            "title3": normalize_punctuation_spacing,
            "anahtarkelimeler": normalize_punctuation_spacing,
            "keywords": normalize_punctuation_spacing,
        }

    def normalize_one_field(self, key, include_focused=False):
        normalizer = self._field_normalizers().get(key)
        if normalizer is None:
            return
        var = self.vars.get(key)
        if var is None:
            return
        entry = self.placeholder_entries.get(key, (None, None))[0]
        if not include_focused and entry is not None and self.focus_get() == entry:
            return
        value = var.get()
        placeholder = self.placeholder_entries.get(key, (None, None))[1]
        if key in self.placeholder_active_keys and value == placeholder:
            return
        if key in self.placeholder_active_keys:
            self.placeholder_active_keys.discard(key)
        if not value.strip():
            return
        normalized = normalizer(value)
        if normalized and normalized != value:
            var.set(normalized)

    def normalize_form_values(self, include_focused=False):
        normalizers = self._field_normalizers()
        focused = self.focus_get()
        for key in normalizers:
            entry = self.placeholder_entries.get(key, (None, None))[0]
            if not include_focused and entry is not None and focused == entry:
                continue
            self.normalize_one_field(key, include_focused=True)

    def _on_mousewheel(self, event):
        canvas = getattr(self, "active_canvas", None)
        if canvas is None or not canvas.winfo_exists():
            return None
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def _on_shift_mousewheel(self, event):
        canvas = getattr(self, "active_canvas", None)
        if canvas is None or not canvas.winfo_exists():
            return None
        canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def _on_widget_shift_mousewheel(self, event, widget):
        if hasattr(widget, "xview_scroll"):
            widget.xview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"
        return None

    def _release_canvas_mousewheel(self, _event=None):
        self.active_canvas = None
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Shift-MouseWheel>")

    def _bind_mousewheel(self, canvas):
        self.active_canvas = canvas
        self.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind_all("<Shift-MouseWheel>", self._on_shift_mousewheel)

    def _add_date_row(self, parent, row, key, label, start_col=0):
        label = FIELD_LABEL_EN.get(key, label) if self.lang_var.get() == "English" else label
        label_widget = ttk.Label(parent, text=label, style="Field.TLabel")
        label_widget.grid(row=row, column=start_col, sticky="w", padx=(12, 6), pady=2)
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=start_col + 1, sticky="ew", pady=2)
        if key == "tarih_tr":
            month_var = tk.StringVar(value=TR_MONTHS[0])
            year_var = tk.StringVar()
            month_box = ttk.Combobox(frame, textvariable=month_var, values=TR_MONTHS, state="readonly", width=10)
            month_box.pack(side="left")
            self.combo_entries.append(month_box)
            ttk.Entry(frame, textvariable=year_var, width=8).pack(side="left", padx=(6, 0))
            self.date_vars["defense_month_year"] = {"month": month_var, "year": year_var}
        else:
            day_var = tk.StringVar()
            month_var = tk.StringVar(value=TR_MONTHS[0])
            year_var = tk.StringVar()
            ttk.Entry(frame, textvariable=day_var, width=4).pack(side="left")
            month_box = ttk.Combobox(frame, textvariable=month_var, values=TR_MONTHS, state="readonly", width=10)
            month_box.pack(side="left", padx=6)
            self.combo_entries.append(month_box)
            ttk.Entry(frame, textvariable=year_var, width=8).pack(side="left")
            date_name = {"tezverme_tr": "submission", "savunma_tr": "defense", "kurul_tarih": "board"}[key]
            self.date_vars[date_name] = {"day": day_var, "month": month_var, "year": year_var}
            self._trace_var(day_var)
        self._trace_var(month_var)
        self._trace_var(year_var)
        hint = ttk.Label(parent, text="", foreground="#666666")
        hint.grid(row=row, column=start_col + 2, sticky="w", padx=(2, 0), pady=2)
        self.field_widgets[key] = (label_widget, frame, hint)

    def _trace_var(self, var):
        if getattr(var, "_tez_gui_traced", False):
            return
        var.trace_add("write", lambda *_args: self._on_form_change())
        var._tez_gui_traced = True

    def _on_form_change(self):
        if not self.loading_form and not self.syncing_advisor_jury:
            self._sync_advisor_to_jury()
            self.sync_programme_fields()
            self.sync_derived_fields()
        self.update_preview()
        if self.loading_form:
            return
        self._schedule_autosave()

    def _sync_advisor_to_jury(self):
        if self.syncing_advisor_jury:
            return
        advisor = self._field_value("danisman_tr")
        advisor_inst = self._field_value("danisman_kurum_tr")
        jury = self.vars.get("juri1")
        jury_inst = self.vars.get("juri1_kurum")
        self.syncing_advisor_jury = True
        try:
            if advisor and jury is not None:
                current = self._field_value("juri1")
                if (not current or current == self.last_synced_jury_advisor) and current != advisor:
                    jury.set(advisor)
                self.last_synced_jury_advisor = advisor
            if advisor_inst and jury_inst is not None:
                current_inst = self._field_value("juri1_kurum")
                if not current_inst:
                    jury_inst.set(advisor_inst)
        finally:
            self.syncing_advisor_jury = False

    def _schedule_autosave(self):
        if not self.autosave_var.get():
            return
        if self.autosave_after_id is not None:
            self.after_cancel(self.autosave_after_id)
        self.autosave_after_id = self.after(900, self.autosave_json)

    def autosave_json(self):
        self.autosave_after_id = None
        try:
            data = self.form_to_macros(normalize_focused=False)
            if data == self.last_autosave_data:
                return
            if self.last_autosave_data:
                self.undo_stack.append(self.last_autosave_data)
                self.undo_stack = self.undo_stack[-20:]
                self.redo_stack = []
            path = self.template_dir / "tez-bilgileri.json"
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            self.write_selected_class_options()
            write_macros_to_tex(self.template_dir / "tez.tex", data)
            self.last_autosave_data = data
            self.last_saved_var.set("Otomatik kaydedildi: " + datetime.now().strftime("%d.%m.%Y %H:%M"))
            self.refresh_missing()
        except Exception as exc:
            self.last_saved_var.set(f"Otomatik kayıt yapılamadı: {exc}")

    def undo_form_change(self):
        if not self.undo_stack:
            messagebox.showinfo("Geri Al", "Geri alınacak kayıt bulunamadı.")
            return
        data = self.undo_stack.pop()
        current = self.form_to_macros()
        self.redo_stack.append(current)
        self.redo_stack = self.redo_stack[-20:]
        self.loading_form = True
        try:
            self.macros_to_form(data)
            self.last_autosave_data = data
            self.last_saved_var.set("Geri alındı")
            self.refresh_missing()
        finally:
            self.loading_form = False
        self.update_preview()

    def redo_form_change(self):
        if not self.redo_stack:
            messagebox.showinfo("Yinele", "Yinelenecek kayıt bulunamadı.")
            return
        data = self.redo_stack.pop()
        current = self.form_to_macros()
        self.undo_stack.append(current)
        self.undo_stack = self.undo_stack[-20:]
        self.loading_form = True
        try:
            self.macros_to_form(data)
            self.last_autosave_data = data
            self.last_saved_var.set("Yinelendi")
            self.refresh_missing()
        finally:
            self.loading_form = False
        self.update_preview()

    def _build_preview_panel(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)
        self.preview_title = ttk.Label(parent, text=UI["tr"]["preview_cover"], font=("Segoe UI", 12, "bold"))
        self.preview_title.grid(row=0, column=0, sticky="w")
        self.preview_cover = ttk.Notebook(parent)
        self.preview_outer_tab = ttk.Frame(self.preview_cover)
        self.preview_inner_tab = ttk.Frame(self.preview_cover)
        self.preview_cover.add(self.preview_outer_tab, text="Dış kapak")
        self.preview_cover.add(self.preview_inner_tab, text="İç kapak")
        self.preview_outer_canvas = tk.Canvas(self.preview_outer_tab, highlightthickness=0)
        self.preview_inner_canvas = tk.Canvas(self.preview_inner_tab, highlightthickness=0)
        self.preview_approval = tk.Canvas(parent, highlightthickness=0)
        self.preview_ai = tk.Text(parent, wrap="word", font=("Segoe UI", 10), height=12, bd=0, padx=12, pady=12)
        for canvas in (self.preview_outer_canvas, self.preview_inner_canvas):
            canvas.pack(fill="both", expand=True)
        for canvas in (self.preview_outer_canvas, self.preview_inner_canvas, self.preview_approval):
            canvas.bind("<Configure>", lambda _event: self.schedule_update_preview())
        self.preview_ai.configure(state="disabled")
        self.preview_cover.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        self.preview_approval.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        self.preview_ai.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        self.preview_cover.bind("<<NotebookTabChanged>>", lambda _event: self.show_active_preview(), add="+")
        self.schedule_update_preview()
        self.show_active_preview()

    def _value(self, key):
        return self._field_value(key)

    def _date_text(self, key):
        values = self.date_vars.get(key, {})
        if key == "defense_month_year":
            month = values.get("month", tk.StringVar(value=TR_MONTHS[0])).get()
            year = values.get("year", tk.StringVar()).get().strip()
            if not year:
                return ""
            return f"{month} {year}".strip()
        day = values.get("day", tk.StringVar()).get().strip()
        month = values.get("month", tk.StringVar(value=TR_MONTHS[0])).get()
        year = values.get("year", tk.StringVar()).get().strip()
        if not day and not year:
            return ""
        return " ".join(part for part in [day, month, year] if part)

    def update_preview(self):
        self.preview_after_id = None
        if getattr(self, "loading_form", False):
            self.preview_deferred = True
            return
        if not hasattr(self, "preview_cover"):
            return
        title = "\n".join(part for part in [self._value("baslik1"), self._value("baslik2"), self._value("baslik3")] if part) or "[Tez başlığı]"
        student = " ".join(part for part in [self._value("ad"), self._value("soyad")] if part) or "[Öğrenci adı soyadı]"
        department = self._department_tex_value(display=False)
        program_raw = self._field_value("program_tr")
        program = "" if program_same_as_department(program_raw, self._field_value("anabilimdali_tr")) else ensure_program_suffix_tr(program_raw)
        degree = "DOKTORA" if DEGREE_VALUE.get(self.degree_var.get(), "yukseklisans") == "doktora" else "YÜKSEK LİSANS"
        degree_en = "DOCTORAL DISSERTATION" if degree == "DOKTORA" else "MASTER OF SCIENCE DISSERTATION"
        advisor = self._value("danisman_tr") or "[Danışman]"
        cover_year = self._value("kapakyili") or "[Yıl]"
        city = self._value("kapaksehri") or "Malatya"
        jury_limit = 5 if DEGREE_VALUE.get(self.degree_var.get(), "yukseklisans") == "doktora" else 3
        jury_lines = []
        for index in range(1, jury_limit + 1):
            name = self._value(f"juri{index}") or f"[Jüri {index}]"
            institution = self._value(f"juri{index}_kurum")
            jury_lines.append(f"{index}. {name}" + (f" - {institution}" if institution else ""))
        data = {
            "title": title,
            "student": student,
            "department": department,
            "program": program,
            "degree": degree,
            "degree_en": degree_en,
            "advisor": advisor,
            "bap": self._value("bap_proje_no"),
            "cover_year": cover_year,
            "city": city.upper(),
            "student_no": self._value("ogrencino"),
            "defense_date": self._date_text("defense") or "[Savunma tarihi]",
            "vote": self._value("oy") or "[oy birliği/çokluğu]",
            "board": self._date_text("board") or "[tarih]",
            "board_no": self._value("kurul_no") or "[karar no]",
            "director": self._value("mudur") or "[Müdür]",
            "jury": jury_lines,
        }
        self._draw_cover_preview(self.preview_outer_canvas, data, outer=True)
        self._draw_cover_preview(self.preview_inner_canvas, data, outer=False)
        self._draw_approval_preview(self.preview_approval, data)
        self.update_ai_preview()

    def schedule_update_preview(self, delay=180):
        if getattr(self, "loading_form", False):
            self.preview_deferred = True
            return
        if not hasattr(self, "preview_cover"):
            return
        if self.preview_after_id:
            try:
                self.after_cancel(self.preview_after_id)
            except tk.TclError:
                pass
        self.preview_after_id = self.after(delay, self.update_preview)

    def _preview_logo(self, max_width):
        cache_key = (self.theme_var.get(), max_width)
        if cache_key in self.preview_logo_images:
            return self.preview_logo_images[cache_key]
        logo_path = ROOT / "iu_fbe_logo.png"
        if not logo_path.exists():
            logo_path = ROOT / "iu_fbe_logo_yatay.png"
        if not logo_path.exists():
            return None
        image = Image.open(logo_path).convert("RGBA")
        bg = Image.new("RGBA", image.size, image.getpixel((0, 0)))
        bbox = ImageChops.difference(image, bg).getbbox()
        if bbox:
            image = image.crop(bbox)
        ratio = min(max_width / image.width, 1)
        image = image.resize((max(1, int(image.width * ratio)), max(1, int(image.height * ratio))), Image.LANCZOS)
        self.preview_logo_images[cache_key] = ImageTk.PhotoImage(image)
        return self.preview_logo_images[cache_key]

    def _page_box(self, canvas):
        canvas.delete("all")
        colors = THEMES[self.theme_var.get()]
        canvas.configure(bg=colors["panel"])
        width = max(canvas.winfo_width(), 360)
        height = max(canvas.winfo_height(), 500)
        page_h = height - 26
        page_w = min(width - 26, int(page_h * 0.707))
        page_h = min(page_h, int(page_w / 0.707))
        x0 = (width - page_w) // 2
        y0 = (height - page_h) // 2
        canvas.create_rectangle(x0 + 2, y0 + 2, x0 + page_w + 2, y0 + page_h + 2, fill=colors["alt"], outline=colors["alt"])
        canvas.create_rectangle(x0, y0, x0 + page_w, y0 + page_h, fill="#ffffff", outline=colors["soft_line"])
        return x0, y0, page_w, page_h

    def _canvas_text(self, canvas, x, y, text, size=9, weight="normal", width=320, fill="#111111", anchor="n", justify="center"):
        return canvas.create_text(x, y, text=text, font=("Times New Roman", size, weight), width=width, fill=fill, anchor=anchor, justify=justify)

    def _draw_cover_preview(self, canvas, data, outer=True):
        x0, y0, page_w, page_h = self._page_box(canvas)
        center = x0 + page_w / 2
        body_w = page_w - 58
        logo = self._preview_logo(max(74, int(page_w * 0.34)))
        if logo:
            canvas.create_image(center, y0 + page_h * 0.09, image=logo, anchor="n")
        y = y0 + page_h * 0.31
        title = "\n".join(textwrap.wrap(data["title"].upper(), width=44)) if "\n" not in data["title"] else data["title"].upper()
        self._canvas_text(canvas, center, y, title, 9, "bold", body_w)
        y += page_h * 0.18
        self._canvas_text(canvas, center, y, f"{data['degree']} TEZİ", 10, "bold", body_w)
        if outer:
            y += page_h * 0.045
            self._canvas_text(canvas, center, y, data["degree_en"], 6, "bold", body_w)
        y += page_h * 0.08
        self._canvas_text(canvas, center, y, data["student"], 10, "bold", body_w)
        if not outer:
            y += page_h * 0.055
            self._canvas_text(canvas, center, y, data["student_no"], 8, "normal", body_w)
        y += page_h * 0.08
        details = [data["department"], data["program"]]
        self._canvas_text(canvas, center, y, "\n".join(part for part in details if part), 8, "normal", body_w)
        if not outer:
            y += page_h * 0.085
            self._canvas_text(canvas, center, y, f"Danışman: {data['advisor']}", 8, "normal", body_w)
            if data.get("bap"):
                y += page_h * 0.055
                self._canvas_text(canvas, center, y, f"Bu Araştırma İnönü Üniversitesi Bilimsel Araştırma Projeleri Birimi tarafından {data['bap']} proje numarası ile desteklenmiştir.", 7, "normal", body_w)
        footer_h = max(28, int(page_h * 0.055))
        footer_y = y0 + page_h - footer_h - 16
        if outer:
            band_color = "#f5b000" if DEGREE_VALUE.get(self.degree_var.get(), "yukseklisans") == "doktora" else "#007381"
            canvas.create_rectangle(x0, footer_y, x0 + page_w, footer_y + footer_h, fill=band_color, outline="")
            self._canvas_text(canvas, center, footer_y + footer_h / 2, f"{data['city']}, {data['cover_year']}", 10, "bold", body_w, fill="#ffffff", anchor="center")
        else:
            self._canvas_text(canvas, center, y0 + page_h * 0.91, f"{data['city']} - {data['cover_year']}", 9, "bold", body_w)

    def _draw_approval_preview(self, canvas, data):
        x0, y0, page_w, page_h = self._page_box(canvas)
        center = x0 + page_w / 2
        body_w = page_w - 54
        logo = self._preview_logo(max(60, int(page_w * 0.22)))
        if logo:
            canvas.create_image(center, y0 + page_h * 0.06, image=logo, anchor="n")
        y = y0 + page_h * 0.18
        self._canvas_text(canvas, center, y, "KABUL VE ONAY", 12, "bold", body_w)
        y += page_h * 0.10
        approval_text = (
            f"Öğrenci: {data['student']}\n\n"
            f"Tez Başlığı: {data['title'].replace(chr(10), ' / ')}\n\n"
            f"Savunma Tarihi: {data['defense_date']}\n"
            f"Oy Durumu: {data['vote']}"
        )
        self._canvas_text(canvas, center, y, approval_text, 8, "normal", body_w)
        y += page_h * 0.25
        self._canvas_text(canvas, center, y, "Jüri:", 9, "bold", body_w)
        y += page_h * 0.045
        self._canvas_text(canvas, center, y, "\n".join(data["jury"]), 8, "normal", body_w)
        self._canvas_text(
            canvas,
            center,
            y0 + page_h * 0.80,
            f"Yönetim Kurulu: {data['board']} / {data['board_no']}\nEnstitü Müdürü: {data['director']}",
            8,
            "normal",
            body_w,
        )

    def show_active_preview(self):
        if not hasattr(self, "preview_cover"):
            return
        selected = self.form_notebook.select()
        if selected == str(self.cover_form_tab):
            active_cover = self.preview_cover.select()
            if active_cover == str(self.preview_inner_tab):
                title = "İç Kapak Önizlemesi"
            else:
                title = "Dış Kapak Önizlemesi"
            self.preview_title.configure(text=title)
            self.preview_approval.grid_remove()
            self.preview_ai.grid_remove()
            self.preview_cover.grid()
        elif selected == str(getattr(self, "ai_form_tab", "")):
            self.preview_title.configure(text="ÜYZ Beyanı Önizlemesi")
            self.preview_cover.grid_remove()
            self.preview_approval.grid_remove()
            self.preview_ai.grid()
            self.update_ai_preview()
        else:
            self.preview_title.configure(text=UI["en" if self.lang_var.get() == "English" else "tr"]["preview_approval"])
            self.preview_cover.grid_remove()
            self.preview_ai.grid_remove()
            self.preview_approval.grid()
        self.update_preview()

    def update_ai_preview(self):
        if not hasattr(self, "preview_ai"):
            return
        if hasattr(self, "ai_declaration_text"):
            content = self.ai_declaration_text.get("1.0", "end").strip()
        else:
            content = self._load_ai_declaration_text().strip()
        if not content:
            content = "Üretken Yapay Zekâ Beyanı metni henüz hazırlanmadı."
        self.preview_ai.configure(state="normal")
        self.preview_ai.delete("1.0", "end")
        self.preview_ai.insert("1.0", content)
        self.preview_ai.configure(state="disabled")

    def _department_tex_value(self, display=True):
        value = self._value("anabilimdali_tr")
        if not value:
            return ""
        if value in DEPARTMENT_OPTIONS and display:
            return value
        if value in DEPARTMENT_OPTIONS:
            return f"{value} Anabilim Dalı"
        return value

    def citation_key_for_department(self, department):
        return DEFAULT_CITATION_STYLE if department == DEFAULT_DEPARTMENT else "apa"

    def _set_citation_key(self, key):
        lang = ui_lang_key(self.lang_var.get())
        self.citation_var.set(CITATION_DISPLAY[lang].get(key, CITATION_DISPLAY[lang][DEFAULT_CITATION_STYLE]))

    def sync_citation_style_for_department(self):
        selected = self._value("anabilimdali_tr") or DEFAULT_DEPARTMENT
        self._set_citation_key(self.citation_key_for_department(selected))

    def sync_department_fields(self):
        selected = self._value("anabilimdali_tr")
        if selected not in DEPARTMENT_EN:
            for key in ("anabilimdali_en", "program_tr", "program_en"):
                var = self.vars.get(key)
                if var is not None:
                    var.set("")
                self.placeholder_active_keys.discard(key)
                self._set_placeholder(key)
            self.sync_citation_style_for_department()
            return
        if selected in DEPARTMENT_EN and "anabilimdali_en" in self.vars:
            self.vars["anabilimdali_en"].set(DEPARTMENT_EN[selected])
            self._mark_manual_value("anabilimdali_en")
        # Program alanı anabilim dalından otomatik doldurulmaz; kullanıcı farklı program yazarsa girer.
        for key in ("program_tr", "program_en"):
            current = self._field_value(key)
            if not current or program_same_as_department(current, selected):
                var = self.vars.get(key)
                if var is not None:
                    var.set("")
                self.placeholder_active_keys.discard(key)
                self._set_placeholder(key)
        self.sync_citation_style_for_department()

    def on_department_select(self):
        self.sync_department_fields()
        self.update_preview()

    def on_thesis_language_change(self, rebuild=True):
        if rebuild and hasattr(self, "form_notebook"):
            existing = self.form_to_macros() if self.vars else None
            self.loading_form = True
            try:
                self.close_floating_tex_toolbar()
                for tab in (self.cover_form_tab, self.approval_form_tab):
                    for child in tab.winfo_children():
                        child.destroy()
                self.field_widgets = {}
                self.date_vars = {}
                self.placeholder_entries = {}
                self.text_entries = []
                self.tex_entry_keys = {}
                self.active_tex_entry = None
                self.themed_canvases = []
                self._build_form_pages()
                if existing:
                    self.macros_to_form(existing)
                self._apply_defaults()
                self.on_degree_change()
                self.apply_theme()
                self.show_active_preview()
            finally:
                self.loading_form = False
        self.update_preview()

    def _apply_defaults(self):
        self._set_placeholder("anabilimdali_tr")
        self._set_placeholder("anabilimdali_en")
        self._set_placeholder("program_tr")
        self._set_placeholder("program_en")
        self.sync_department_fields()
        mudur = self.vars.get("mudur")
        mudur_value = self._field_value("mudur")
        if mudur is not None and (not mudur_value or any(pattern in mudur_value for pattern in PLACEHOLDER_PATTERNS)):
            mudur.set("Prof. Dr. Süleyman KÖYTEPE")
        oy = self.vars.get("oy")
        oy_value = self._field_value("oy")
        if oy is not None and (not oy_value or "oy birliği" in oy_value.lower()):
            oy.set("Oy birliği")
        self.sync_derived_fields()

    def apply_language(self):
        existing = self.form_to_macros() if hasattr(self, "form_notebook") and self.vars else None
        lang = "en" if self.lang_var.get() == "English" else "tr"
        data = UI[lang]
        self._sync_option_display(lang)
        self.title(f"{data['title']} {APP_VERSION}")
        self.ui_labels["title"].configure(text=f"{data['title']}  {APP_VERSION}")
        for key, widget in self.ui_labels.items():
            if key == "title":
                continue
            if key in data:
                widget.configure(text=data[key])
        self.spine_check.configure(text=data["spine"])
        if hasattr(self, "choose_folder_button"):
            self.choose_folder_button.configure(text=data.get("choose_folder", "Seç"))
        for tab, key in self.notebook_tabs:
            self.notebook.tab(tab, text=data[key])
        if hasattr(self, "form_notebook"):
            self.close_floating_tex_toolbar()
            self.form_notebook.tab(self.cover_form_tab, text=data["cover_tab"])
            self.form_notebook.tab(self.approval_form_tab, text=data["approval_tab"])
            if hasattr(self, "ai_form_tab"):
                self.form_notebook.tab(self.ai_form_tab, text="ÜYZ Beyanı")
            for tab in (self.cover_form_tab, self.approval_form_tab):
                for child in tab.winfo_children():
                    child.destroy()
            self.field_widgets = {}
            self.date_vars = {}
            self.placeholder_entries = {}
            self.text_entries = []
            self.tex_entry_keys = {}
            self.active_tex_entry = None
            self.themed_canvases = []
            self._build_form_pages()
            if existing:
                self.macros_to_form(existing)
            self._apply_defaults()
            self.on_degree_change()
            self.apply_theme()
            self.show_active_preview()

    def _sync_option_display(self, lang):
        degree_key = DEGREE_VALUE.get(self.degree_var.get(), "yukseklisans")
        citation_key = CITATION_VALUE.get(self.citation_var.get(), "apa")
        thesis_key = "ingilizce" if is_english_thesis_label(self.thesis_language_var.get()) else "turkce"
        decimal_key = DECIMAL_SEPARATOR_VALUE.get(self.decimal_separator_var.get(), "nokta")
        page_layout_key = PAGE_LAYOUT_VALUE.get(self.page_layout_var.get(), "tek")
        degree_values = list(DEGREE_DISPLAY[lang].values())
        citation_values = list(CITATION_DISPLAY[lang].values())
        thesis_values = list(THESIS_LANGUAGE_DISPLAY[lang].values())
        decimal_values = list(DECIMAL_SEPARATOR_DISPLAY[lang].values())
        page_layout_values = list(PAGE_LAYOUT_DISPLAY[lang].values())
        if self.degree_box is not None:
            self.degree_box.configure(values=degree_values)
        if self.citation_box is not None:
            self.citation_box.configure(values=citation_values)
        if self.thesis_language_box is not None:
            self.thesis_language_box.configure(values=thesis_values)
        if self.decimal_separator_box is not None:
            self.decimal_separator_box.configure(values=decimal_values)
        if self.page_layout_box is not None:
            self.page_layout_box.configure(values=page_layout_values)
        self.degree_var.set(DEGREE_DISPLAY[lang].get(degree_key, degree_values[0]))
        self.citation_var.set(CITATION_DISPLAY[lang].get(citation_key, citation_values[0]))
        self.thesis_language_var.set(THESIS_LANGUAGE_DISPLAY[lang].get(thesis_key, thesis_values[0]))
        self.decimal_separator_var.set(DECIMAL_SEPARATOR_DISPLAY[lang].get(decimal_key, decimal_values[0]))
        self.page_layout_var.set(PAGE_LAYOUT_DISPLAY[lang].get(page_layout_key, page_layout_values[0]))

    def apply_theme(self):
        self.clear_tex_palette_cache()
        colors = THEMES[self.theme_var.get()]
        self.configure(bg=colors["bg"])
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(".", background=colors["bg"], foreground=colors["fg"], fieldbackground=colors["text_bg"], font=("Segoe UI", 9))
        style.configure("TFrame", background=colors["bg"])
        style.configure("Card.TFrame", background=colors["panel"], bordercolor=colors["soft_line"], relief="flat", borderwidth=0)
        style.configure("TLabel", background=colors["bg"], foreground=colors["fg"], font=("Segoe UI", 9))
        style.configure("Card.TLabel", background=colors["panel"], foreground=colors["fg"], font=("Segoe UI", 9))
        style.configure("Field.TLabel", background=colors["bg"], foreground=colors["accent_dark"], font=("Segoe UI", 9, "bold"))
        input_bg = colors.get("input_bg", colors["text_bg"])
        style.configure("TEntry", fieldbackground=input_bg, foreground=colors["text_fg"], insertcolor=colors["text_fg"], font=("Segoe UI", 10))
        style.configure("TCombobox", fieldbackground=input_bg, background=colors["panel"], foreground=colors["text_fg"], arrowcolor=colors["fg"], bordercolor=colors["soft_line"], lightcolor=colors["soft_line"], darkcolor=colors["soft_line"])
        style.map("TCombobox", fieldbackground=[("readonly", input_bg)], foreground=[("readonly", colors["text_fg"])], selectbackground=[("readonly", input_bg)], selectforeground=[("readonly", colors["text_fg"])])
        style.configure("TNotebook", background=colors["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", padding=(10, 5), background=colors["panel"], foreground=colors["fg"], font=("Segoe UI", 9, "bold"))
        style.map(
            "TNotebook.Tab",
            background=[("selected", colors["accent"])],
            foreground=[("selected", "#ffffff")],
            padding=[("selected", (15, 8)), ("!selected", (10, 5))],
            expand=[("selected", (2, 2, 2, 0))],
        )
        style.configure("TButton", padding=(6, 2), background=colors["panel"], foreground=colors["fg"], bordercolor=colors["line"], font=("Segoe UI", 9))
        style.configure("Soft.TButton", padding=(6, 2), background=colors["panel"], foreground=colors["fg"], bordercolor=colors["line"], font=("Segoe UI", 9))
        style.configure("Mini.TButton", padding=(4, 1), background=colors["panel"], foreground=colors["fg"], bordercolor=colors["line"], font=("Segoe UI", 9))
        style.configure("Tiny.TButton", padding=(4, 1), background=colors["panel"], foreground=colors["fg"], bordercolor=colors["line"], font=("Segoe UI", 9))
        style.configure("Primary.TButton", padding=(6, 2), background=colors["panel"], foreground=colors["fg"], bordercolor=colors["line"], font=("Segoe UI", 9, "bold"))
        style.configure("PrimaryMini.TButton", padding=(4, 1), background=colors["panel"], foreground=colors["fg"], bordercolor=colors["line"], font=("Segoe UI", 9, "bold"))
        style.configure("UpdateReady.TButton", padding=(6, 2), background="#EAF7EA", foreground=colors["fg"], bordercolor="#F29F05", font=("Segoe UI", 9, "bold"))
        style.map(
            "TButton",
            background=[("disabled", colors["panel"]), ("pressed", colors["accent"]), ("active", colors["alt"])],
            foreground=[("disabled", colors["muted"]), ("pressed", "#ffffff"), ("active", colors["fg"])],
            bordercolor=[("active", colors["accent"])],
        )
        style.map("Soft.TButton", background=[("disabled", colors["panel"]), ("active", colors["alt"])], foreground=[("disabled", colors["muted"]), ("active", colors["fg"])], bordercolor=[("active", colors["accent"])])
        style.map("Mini.TButton", background=[("disabled", colors["panel"]), ("active", colors["alt"])], foreground=[("disabled", colors["muted"]), ("active", colors["fg"])], bordercolor=[("active", colors["accent"])])
        style.map("Tiny.TButton", background=[("disabled", colors["panel"]), ("active", colors["alt"])], foreground=[("disabled", colors["muted"]), ("active", colors["fg"])], bordercolor=[("active", colors["accent"])])
        style.map("Primary.TButton", background=[("disabled", colors["panel"]), ("active", colors["alt"])], foreground=[("disabled", colors["muted"]), ("active", colors["fg"])], bordercolor=[("active", colors["accent"])])
        style.map("PrimaryMini.TButton", background=[("disabled", colors["panel"]), ("active", colors["alt"])], foreground=[("disabled", colors["muted"]), ("active", colors["fg"])], bordercolor=[("active", colors["accent"])])
        style.map("UpdateReady.TButton", background=[("disabled", "#EAF7EA"), ("pressed", "#DDF0DD"), ("active", "#F2FAF2")], foreground=[("disabled", colors["muted"]), ("active", colors["fg"])], bordercolor=[("active", "#F29F05")])
        style.configure("TCheckbutton", background=colors["bg"], foreground=colors["fg"])
        style.configure("Card.TCheckbutton", background=colors["panel"], foreground=colors["fg"])
        style.configure("Switch.TCheckbutton", background=colors["bg"], foreground=colors["fg"], font=("Segoe UI", 9))
        for frame in self.soft_group_frames:
            frame.configure(bg=colors["panel"], highlightbackground=colors["soft_line"], highlightcolor=colors["soft_line"])
        for key, widgets in self.field_widgets.items():
            if len(widgets) == 3:
                widgets[2].configure(foreground=colors["muted"])
        if self.autosave_check is not None:
            self.render_autosave_check()
        for name in ("system_text", "output", "missing_list", "preview_ai"):
            widget = getattr(self, name, None)
            if widget is not None:
                widget.configure(bg=colors["text_bg"], fg=colors["text_fg"])
        for canvas in self.themed_canvases:
            canvas.configure(bg=colors["bg"])
        for entry in self.text_entries:
            entry.configure(bg=input_bg, fg=colors["text_fg"], insertbackground=colors["text_fg"], highlightbackground=colors["soft_line"], highlightcolor=colors["accent"], font=("Segoe UI", 10))
        self.render_update_buttons()
        for rb in self.radio_buttons:
            try:
                parent_bg = rb.master.cget("bg")
            except tk.TclError:
                parent_bg = colors["panel"]
            rb.configure(bg=parent_bg, fg=colors["fg"], activebackground=parent_bg, activeforeground=colors["accent"], selectcolor=colors["accent"] if self.theme_var.get() == "Koyu" else parent_bg)
        for key, (entry, _placeholder) in self.placeholder_entries.items():
            self._configure_placeholder_color(entry, key in self.placeholder_active_keys)
        try:
            self.option_add("*TCombobox*Listbox.background", input_bg)
            self.option_add("*TCombobox*Listbox.foreground", colors["text_fg"])
            self.option_add("*TCombobox*Listbox.selectBackground", colors["accent"])
            self.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
        except tk.TclError:
            pass
        self._load_logo()
        self.update_preview()
        if getattr(self, "dashboard_vars", None):
            self.update_dashboard_status()

    def _build_missing_tab(self):
        self.missing_tab.columnconfigure(0, weight=1)
        self.missing_tab.rowconfigure(4, weight=1)
        dashboard = ttk.Frame(self.missing_tab)
        dashboard.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        for index in range(4):
            dashboard.columnconfigure(index, weight=1)
        for index, (key, title, icon) in enumerate([
            ("missing", "Eksikler", "missing"),
            ("control", "Kontrol", "check"),
            ("reports", "Raporlar", "read"),
            ("delivery", "Teslim", "package"),
        ]):
            card = tk.Frame(dashboard, bg=THEMES[self.theme_var.get()]["panel"], highlightbackground=THEMES[self.theme_var.get()]["soft_line"], highlightthickness=1, bd=0, padx=8, pady=6)
            card.grid(row=0, column=index, sticky="ew", padx=(0, 6 if index < 3 else 0))
            self.soft_group_frames.append(card)
            self.dashboard_cards[key] = card
            self.dashboard_vars[key] = tk.StringVar(value="Hazırlanıyor")
            self.dashboard_hint_vars[key] = tk.StringVar(value="")
            title_label = ttk.Label(card, text=title, image=self._button_icon(icon), compound="left", style="Card.TLabel", font=("Segoe UI", 9, "bold"))
            title_label.pack(anchor="w")
            status_label = ttk.Label(card, textvariable=self.dashboard_vars[key], style="Card.TLabel", font=("Segoe UI", 9))
            status_label.pack(anchor="w", pady=(3, 0))
            hint_label = ttk.Label(card, textvariable=self.dashboard_hint_vars[key], style="Card.TLabel", font=("Segoe UI", 8))
            hint_label.pack(anchor="w", pady=(2, 0))
            for widget in (card, title_label, status_label, hint_label):
                widget.bind("<Button-1>", lambda _event, k=key: self.handle_dashboard_card(k))
                widget.bind("<Enter>", lambda _event, w=card: w.configure(cursor="hand2"))
                widget.bind("<Leave>", lambda _event, w=card: w.configure(cursor=""))
        self.next_action_frame = tk.Frame(
            self.missing_tab,
            bg=THEMES[self.theme_var.get()]["panel"],
            highlightbackground=THEMES[self.theme_var.get()]["accent"],
            highlightthickness=1,
            bd=0,
            padx=10,
            pady=8,
        )
        self.next_action_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self.soft_group_frames.append(self.next_action_frame)
        self.next_action_frame.columnconfigure(1, weight=1)
        self.next_action_icon = ttk.Label(self.next_action_frame, image=self._button_icon("check"), style="Card.TLabel")
        self.next_action_icon.grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 8))
        ttk.Label(self.next_action_frame, textvariable=self.next_action_title_var, style="Card.TLabel", font=("Segoe UI", 10, "bold")).grid(row=0, column=1, sticky="w")
        ttk.Label(self.next_action_frame, textvariable=self.next_action_detail_var, style="Card.TLabel").grid(row=1, column=1, sticky="w")
        self.next_action_button = ttk.Button(
            self.next_action_frame,
            textvariable=self.next_action_button_var,
            image=self._button_icon("check", "primary"),
            compound="left",
            style="Primary.TButton",
            command=self.run_next_action,
        )
        self.next_action_button.grid(row=0, column=2, rowspan=2, sticky="e", padx=(8, 0))
        self.busy_buttons.append(self.next_action_button)
        self.workflow_frame = ttk.Frame(self.missing_tab)
        self.workflow_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        for index, (key, title, icon) in enumerate([
            ("info", "Bilgiler", "apply"),
            ("missing", "Eksikler", "missing"),
            ("control", "Kontrol", "check"),
            ("writing", "Yazım", "spell"),
            ("delivery", "Teslim", "package"),
        ]):
            self.workflow_frame.columnconfigure(index, weight=1)
            step = tk.Frame(
                self.workflow_frame,
                bg=THEMES[self.theme_var.get()]["panel"],
                highlightbackground=THEMES[self.theme_var.get()]["soft_line"],
                highlightthickness=1,
                bd=0,
                padx=8,
                pady=5,
            )
            step.grid(row=0, column=index, sticky="ew", padx=(0, 5 if index < 4 else 0))
            self.soft_group_frames.append(step)
            self.workflow_step_frames[key] = step
            self.workflow_step_vars[key] = tk.StringVar(value="Bekliyor")
            title_label = ttk.Label(step, text=title, image=self._button_icon(icon), compound="left", style="Card.TLabel", font=("Segoe UI", 9, "bold"))
            title_label.pack(anchor="w")
            status_label = ttk.Label(step, textvariable=self.workflow_step_vars[key], style="Card.TLabel", font=("Segoe UI", 8))
            status_label.pack(anchor="w", pady=(2, 0))
            self.workflow_step_title_labels[key] = title_label
            self.workflow_step_status_labels[key] = status_label
            for widget in (step, title_label, status_label):
                widget.bind("<Button-1>", lambda _event, k=key: self.handle_workflow_step(k))
                widget.bind("<Enter>", lambda _event, w=step: w.configure(cursor="hand2"))
                widget.bind("<Leave>", lambda _event, w=step: w.configure(cursor=""))
        ttk.Label(self.missing_tab, text="Eksikler anlaşılır açıklamalarla burada görünür. Bilgileri doldurdukça liste azalır.").grid(row=3, column=0, sticky="w")
        list_frame = ttk.Frame(self.missing_tab)
        list_frame.grid(row=4, column=0, sticky="nsew", pady=8)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        self.missing_list = tk.Listbox(list_frame, font=("Segoe UI", 10))
        self.missing_list.grid(row=0, column=0, sticky="nsew")
        missing_y = ttk.Scrollbar(list_frame, orient="vertical", command=self.missing_list.yview)
        missing_y.grid(row=0, column=1, sticky="ns")
        missing_x = ttk.Scrollbar(list_frame, orient="horizontal", command=self.missing_list.xview)
        missing_x.grid(row=1, column=0, sticky="ew")
        self.missing_list.configure(
            yscrollcommand=lambda first, last, sb=missing_y: self._sync_scrollbar(sb, first, last),
            xscrollcommand=lambda first, last, sb=missing_x: self._sync_scrollbar(sb, first, last),
        )
        self.missing_list.bind("<Enter>", self._release_canvas_mousewheel)
        self.missing_list.bind("<Leave>", lambda _event, c=self.main_canvas: self._bind_mousewheel(c))
        self.missing_list.bind("<Shift-MouseWheel>", lambda event, w=self.missing_list: self._on_widget_shift_mousewheel(event, w))
        self.after_idle(lambda: (self._sync_scrollbar(missing_y, *self.missing_list.yview()), self._sync_scrollbar(missing_x, *self.missing_list.xview())))
        self.missing_list.bind("<Double-Button-1>", self.focus_missing_target)
        controls = ttk.Frame(self.missing_tab)
        controls.grid(row=5, column=0, sticky="ew")
        ttk.Button(controls, text="Yenile", image=self._button_icon("refresh"), compound="left", style="Soft.TButton", command=self.refresh_missing).pack(side="left")
        missing_btn = ttk.Button(controls, text="Eksik Raporu", image=self._button_icon("missing"), compound="left", style="Soft.TButton", command=self.run_missing_report)
        missing_btn.pack(side="left", padx=6)
        self.busy_buttons.append(missing_btn)
        quick_check = ttk.Button(controls, text="Kontrol", image=self._button_icon("check", "primary"), compound="left", style="Primary.TButton", command=self.run_check)
        quick_check.pack(side="left", padx=6)
        self.busy_buttons.append(quick_check)
        package_btn = ttk.Button(controls, text="Teslim Paketi", image=self._button_icon("package", "primary"), compound="left", style="Primary.TButton", command=self.run_package)
        package_btn.pack(side="left", padx=6)
        self.busy_buttons.append(package_btn)
        ttk.Button(controls, text="PDF Klasörü", image=self._button_icon("pdf_folder"), compound="left", style="Soft.TButton", command=self.open_delivery).pack(side="left", padx=6)

    def _build_system_tab(self):
        self.system_tab.columnconfigure(0, weight=1)
        self.system_tab.rowconfigure(1, weight=1)
        ttk.Label(self.system_tab, text="Bilgisayardaki TeX araçları").grid(row=0, column=0, sticky="w")
        system_frame = ttk.Frame(self.system_tab)
        system_frame.grid(row=1, column=0, sticky="nsew", pady=8)
        system_frame.columnconfigure(0, weight=1)
        system_frame.rowconfigure(0, weight=1)
        self.system_text = tk.Text(system_frame, height=18, wrap="none", font=("Consolas", 10))
        self.system_text.grid(row=0, column=0, sticky="nsew")
        system_y = ttk.Scrollbar(system_frame, orient="vertical", command=self.system_text.yview)
        system_y.grid(row=0, column=1, sticky="ns")
        system_x = ttk.Scrollbar(system_frame, orient="horizontal", command=self.system_text.xview)
        system_x.grid(row=1, column=0, sticky="ew")
        self.system_text.configure(
            yscrollcommand=lambda first, last, sb=system_y: self._sync_scrollbar(sb, first, last),
            xscrollcommand=lambda first, last, sb=system_x: self._sync_scrollbar(sb, first, last),
        )
        self.system_text.bind("<Enter>", self._release_canvas_mousewheel)
        self.system_text.bind("<Leave>", lambda _event, c=self.main_canvas: self._bind_mousewheel(c))
        self.system_text.bind("<Shift-MouseWheel>", lambda event, w=self.system_text: self._on_widget_shift_mousewheel(event, w))
        self.after_idle(lambda: (self._sync_scrollbar(system_y, *self.system_text.yview()), self._sync_scrollbar(system_x, *self.system_text.xview())))
        system_buttons = ttk.Frame(self.system_tab)
        system_buttons.grid(row=2, column=0, sticky="w")
        ttk.Button(system_buttons, text="Yenile", image=self._button_icon("refresh"), compound="left", style="Soft.TButton", command=self.refresh_system).pack(side="left")
        ttk.Button(system_buttons, text="Şablonu Onar", image=self._button_icon("check"), compound="left", style="Soft.TButton", command=self.run_template_repair).pack(side="left", padx=6)

    def run_template_repair(self):
        workdir = self.template_dir
        preview = sablon_koruma.repair_workdir(workdir, dry_run=True)
        preview_text = sablon_koruma.items_to_text(preview)
        changed_count = sum(1 for item in preview if item.changed)
        if changed_count == 0:
            messagebox.showinfo("Şablon koruma", preview_text)
            self.output_queue.put("\n== Şablon Koruma ==\n" + preview_text + "\n")
            return
        if not messagebox.askyesno(
            "Şablon koruma",
            "Korunan şablon iskeletinde onarılabilecek sorunlar bulundu.\n\n"
            f"{preview_text}\n\n"
            "Onarım uygulansın mı?",
        ):
            return
        items = sablon_koruma.repair_workdir(workdir, dry_run=False)
        text = sablon_koruma.items_to_text(items)
        self.output_queue.put("\n== Şablon Koruma ==\n" + text + "\n")
        messagebox.showinfo("Şablon koruma", text)
        self.load_from_tez()
        self.refresh_missing()
        self.update_preview()

    def _build_run_tab(self):
        self.run_tab.columnconfigure(0, weight=1)
        self.run_tab.rowconfigure(1, weight=1)
        buttons = ttk.Frame(self.run_tab)
        buttons.grid(row=0, column=0, sticky="ew")
        for label, command, icon, style_name, tooltip_key in [
            ("Akıllı TeX Tanılama", self.run_latex_diagnostics, "smart_tex", "Soft.TButton", "diagnostics"),
            ("Akıllı Yazım Denetimi", self.run_writing_check, "smart_spell", "Soft.TButton", "writing_check"),
            ("Kılavuz Uygunluk Denetimi", self.run_guideline_pdf_check, "preview", "Soft.TButton", "guideline_check"),
            ("Temizle", self.run_clean, "clean", "Soft.TButton", "clean"),
        ]:
            icon_tone = "primary" if style_name.startswith("Primary") else "normal"
            btn = ttk.Button(buttons, text=label, image=self._button_icon(icon, icon_tone), compound="left", style=style_name, command=command)
            btn.pack(side="left", padx=3)
            self._add_tooltip(btn, tooltip_key)
            if command in {self.run_missing_report, self.run_check, self.run_latex_diagnostics, self.run_package, self.run_clean}:
                self.busy_buttons.append(btn)

        self.run_paned = ttk.PanedWindow(self.run_tab, orient="horizontal")
        self.run_paned.grid(row=1, column=0, sticky="nsew", pady=8)
        self.run_paned.bind("<Configure>", lambda _event: self.position_diagnostic_split_toggle(), add="+")
        self.run_paned.bind("<B1-Motion>", lambda _event: self.position_diagnostic_split_toggle(), add="+")
        self.run_paned.bind("<ButtonRelease-1>", lambda _event: self.position_diagnostic_split_toggle(), add="+")
        output_frame = ttk.Frame(self.run_paned)
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        self.output = tk.Text(output_frame, wrap="word", font=("Consolas", 9))
        self.output.grid(row=0, column=0, sticky="nsew")
        output_y = ttk.Scrollbar(output_frame, orient="vertical", command=self.output.yview)
        output_y.grid(row=0, column=1, sticky="ns")
        self.output.configure(
            yscrollcommand=lambda first, last, sb=output_y: self._sync_scrollbar(sb, first, last),
        )
        self.output.bind("<Enter>", self._release_canvas_mousewheel)
        self.output.bind("<Leave>", lambda _event, c=self.main_canvas: self._bind_mousewheel(c))
        self.after_idle(lambda: self._sync_scrollbar(output_y, *self.output.yview()))
        self.run_paned.add(output_frame, weight=3)

        self.diag_editor_panel = ttk.Frame(self.run_paned, padding=(6, 0, 0, 0))
        self.diag_editor_panel.columnconfigure(0, weight=1)
        self.diag_editor_panel.rowconfigure(1, weight=1)
        editor_header = ttk.Frame(self.diag_editor_panel)
        editor_header.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        editor_header.columnconfigure(0, weight=1)
        ttk.Label(editor_header, textvariable=self.diag_editor_title_var, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w")
        self.diag_editor_undo_button = ttk.Button(editor_header, text="Geri", image=self._button_icon("undo"), compound="left", style="Tiny.TButton", state="disabled", width=6)
        self.diag_editor_undo_button.grid(row=0, column=1, sticky="e", padx=(4, 0))
        self.diag_editor_redo_button = ttk.Button(editor_header, text="Yinele", image=self._button_icon("redo"), compound="left", style="Tiny.TButton", state="disabled", width=7)
        self.diag_editor_redo_button.grid(row=0, column=2, sticky="e", padx=(4, 0))
        self.diag_editor_open_button = ttk.Button(editor_header, text="Aç", image=self._button_icon("folder"), compound="left", style="Tiny.TButton", state="disabled", width=5)
        self.diag_editor_open_button.grid(row=0, column=3, sticky="e", padx=(4, 0))
        self.diag_editor_save_button = ttk.Button(editor_header, text="Kaydet", image=self._button_icon("save", "primary"), compound="left", style="PrimaryMini.TButton", state="disabled", width=7)
        self.diag_editor_save_button.grid(row=0, column=4, sticky="e", padx=(4, 0))
        self.diag_editor_body = ttk.Frame(self.diag_editor_panel)
        self.diag_editor_body.grid(row=1, column=0, sticky="nsew")
        self.diag_editor_body.columnconfigure(0, weight=0)
        self.diag_editor_body.columnconfigure(1, weight=1)
        self.diag_editor_body.rowconfigure(0, weight=1)
        self.diag_editor_visible = False
        self.diag_split_toggle = tk.Button(
            self.run_tab,
            text="›",
            width=1,
            relief="flat",
            bd=0,
            padx=0,
            pady=0,
            highlightthickness=0,
            font=("Segoe UI", 8, "bold"),
            command=self.toggle_diagnostic_editor_panel,
            cursor="hand2",
        )
        ToolTip(self.diag_split_toggle, lambda: "Düzeltme panelini gizle" if self.diag_editor_visible else "Düzeltme panelini göster", delay=350)
        self.diag_split_toggle.place_forget()
        bottom = ttk.Frame(self.run_tab)
        bottom.grid(row=2, column=0, sticky="ew")
        self.status = ttk.Label(bottom, text="Hazır", font=("Segoe UI", 9, "bold"))
        self.status.pack(side="left")
        self.busy_progress = ttk.Progressbar(bottom, mode="indeterminate", length=180)
        self.busy_progress.pack(side="right")
        self.busy_progress.pack_forget()

    def on_template_change(self):
        self.load_from_tez()
        if hasattr(self, "missing_list"):
            self.refresh_missing()
        self.refresh_system()

    def on_citation_change(self):
        self.update_preview()

    def on_decimal_separator_change(self):
        self.update_preview()

    def on_page_layout_change(self):
        self.update_preview()

    def on_degree_change(self):
        show_extra_jury = DEGREE_VALUE.get(self.degree_var.get(), "yukseklisans") == "doktora"
        for key in JURY_EXTRA_KEYS:
            widgets = self.field_widgets.get(key)
            if not widgets:
                continue
            for widget in widgets:
                if show_extra_jury:
                    widget.grid()
                else:
                    widget.grid_remove()
        if hasattr(self, "missing_list"):
            self.refresh_missing()

    def form_to_macros(self, normalize_focused=False):
        self.sync_derived_fields(force=normalize_focused, normalize_focused=normalize_focused)
        macros = {}
        for _section, fields in FIELDS:
            for key, _label, macro, index in fields:
                if key in SKIP_FORM_KEYS:
                    continue
                values = macros.setdefault(macro, [])
                while len(values) <= index:
                    values.append("")
                raw_value = self._field_output_value(key)
                if key == "anabilimdali_tr":
                    if raw_value in DEPARTMENT_OPTIONS:
                        raw_value = f"{raw_value} Anabilim Dalı"
                elif key == "program_tr":
                    dept_value = self._field_value("anabilimdali_tr")
                    raw_value = "" if program_same_as_department(raw_value, dept_value) else ensure_program_suffix_tr(raw_value)
                elif key == "program_en":
                    dept_value = self._field_value("anabilimdali_en")
                    raw_value = "" if program_same_as_department(raw_value, dept_value) else ensure_program_suffix_en(raw_value)
                values[index] = latex_escape(raw_value)
        date_macros = self.date_macros()
        macros.update(date_macros)
        return macros

    def macros_to_form(self, macros):
        for _section, fields in FIELDS:
            for key, _label, macro, index in fields:
                if key in SKIP_FORM_KEYS:
                    continue
                values = macros.get(macro, [])
                value = values[index] if index < len(values) else ""
                if is_template_placeholder(value):
                    value = ""
                if key == "anabilimdali_tr" and value.endswith(" Anabilim Dalı"):
                    candidate = value[:-len(" Anabilim Dalı")]
                    if candidate in DEPARTMENT_OPTIONS:
                        value = candidate
                value_text = latex_to_text(value)
                if key in DEFAULT_FORM_PLACEHOLDERS and value_text == DEFAULT_FORM_PLACEHOLDERS[key]:
                    value_text = ""
                if key == "program_tr" and program_same_as_department(value_text, latex_to_text(macros.get("anabilimdali", [""])[0] if macros.get("anabilimdali") else self._field_value("anabilimdali_tr"))):
                    value_text = ""
                if key == "program_en" and program_same_as_department(value_text, latex_to_text(macros.get("anabilimdali", ["", ""])[1] if len(macros.get("anabilimdali", [])) > 1 else self._field_value("anabilimdali_en"))):
                    value_text = ""
                self.vars[key].set(value_text)
        self._refresh_placeholders()
        self.macros_to_dates(macros)

    def date_macros(self):
        result = {}
        defense = self.date_vars.get("defense_month_year", {})
        month = defense.get("month", tk.StringVar(value=TR_MONTHS[0])).get()
        year = defense.get("year", tk.StringVar()).get().strip()
        if year:
            index = TR_MONTHS.index(month) if month in TR_MONTHS else 0
            result["tarih"] = [f"{TR_MONTHS[index].upper()} {year}", f"{EN_MONTHS[index].upper()} {year}"]
            result["tarihKucuk"] = [f"{TR_MONTHS[index].lower()} {year}", f"{EN_MONTHS[index].lower()} {year}"]

        for key, macro in [("submission", "tezvermetarih"), ("defense", "tezsavunmatarih")]:
            values = self.date_vars.get(key, {})
            day = values.get("day", tk.StringVar()).get().strip()
            month = values.get("month", tk.StringVar(value=TR_MONTHS[0])).get()
            year = values.get("year", tk.StringVar()).get().strip()
            if day or year:
                result[macro] = [latex_escape(value) for value in format_date_pair(day, month, year)]

        board = self.date_vars.get("board", {})
        board_day = board.get("day", tk.StringVar()).get().strip()
        board_month = board.get("month", tk.StringVar(value=TR_MONTHS[0])).get()
        board_year = board.get("year", tk.StringVar()).get().strip()
        board_no = self._field_value("kurul_no")
        if board_day or board_year or board_no:
            board_date = format_date_pair(board_day, board_month, board_year)[0]
            result["yonetimkurulukarar"] = [latex_escape(board_date), latex_escape(board_no)]
        return result

    def macros_to_dates(self, macros):
        tarih = macros.get("tarih", [""])
        month, year = parse_month_year(tarih[0] if tarih else "")
        if "defense_month_year" in self.date_vars:
            self.date_vars["defense_month_year"]["month"].set(month)
            self.date_vars["defense_month_year"]["year"].set(year)
        for key, macro in [("submission", "tezvermetarih"), ("defense", "tezsavunmatarih")]:
            values = macros.get(macro, [""])
            day, month, year = parse_day_month_year(values[0] if values else "")
            if key in self.date_vars:
                self.date_vars[key]["day"].set(day)
                self.date_vars[key]["month"].set(month)
                self.date_vars[key]["year"].set(year)
        board_values = macros.get("yonetimkurulukarar", ["", ""])
        day, month, year = parse_day_month_year(board_values[0] if board_values else "")
        if "board" in self.date_vars:
            self.date_vars["board"]["day"].set(day)
            self.date_vars["board"]["month"].set(month)
            self.date_vars["board"]["year"].set(year)
        if len(board_values) > 1 and "kurul_no" in self.vars:
            self.vars["kurul_no"].set(latex_to_text(board_values[1]))

    def load_from_tez(self):
        tex_path = self.template_dir / "tez.tex"
        if tex_path.exists():
            self.loading_form = True
            self.preview_deferred = False
            try:
                self.macros_to_form(read_macros(tex_path))
                degree = read_degree(tex_path)
                if degree:
                    self.degree_var.set(DEGREE_DISPLAY["tr"].get(degree, "Yüksek Lisans"))
                self.citation_var.set(CITATION_DISPLAY["tr"].get(read_citation_style(tex_path), "APA 7"))
                self.thesis_language_var.set("İngilizce" if read_thesis_language(tex_path) == "ingilizce" else "Türkçe")
                self.decimal_separator_var.set(DECIMAL_SEPARATOR_DISPLAY["tr"].get(read_decimal_separator(tex_path), DECIMAL_SEPARATOR_DISPLAY["tr"]["nokta"]))
                self.page_layout_var.set(PAGE_LAYOUT_DISPLAY["tr"].get(read_page_layout(tex_path), PAGE_LAYOUT_DISPLAY["tr"]["tek"]))
                self._sync_option_display(ui_lang_key(self.lang_var.get()))
                self._apply_defaults()
                self.last_autosave_data = self.form_to_macros()
                self.undo_stack = []
            finally:
                self.loading_form = False
            self.on_degree_change()
            self.on_thesis_language_change()
            self.preview_deferred = False
            self.update_preview()

    def save_json(self, notify=True, normalize_focused=True):
        if not self.validate_form():
            return False
        data = self.form_to_macros(normalize_focused=normalize_focused)
        path = self.template_dir / "tez-bilgileri.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self.last_autosave_data = data
        self.last_saved_var.set("Güncellendi: " + datetime.now().strftime("%d.%m.%Y %H:%M"))
        if notify:
            messagebox.showinfo("Kaydedildi", f"Bilgiler kaydedildi:\n{path}")
        self.refresh_missing()
        return True

    def save_and_apply_to_tez(self, confirm=False):
        if confirm and not messagebox.askyesno("tez.tex'e yaz", "Bilgiler tez.tex dosyasına güvenli biçimde yazılsın mı?"):
            return
        if not self.save_json(notify=False):
            return
        self.create_backup_snapshot()
        self.write_selected_class_options()
        self.run_command(self.template_dir, self.ps("tez-bilgileri-uygula.ps1", "-Config", ".\\tez-bilgileri.json"), "Bilgiler kaydediliyor")

    def apply_to_tez(self):
        self.save_and_apply_to_tez(confirm=True)

    def create_backup_snapshot(self):
        backup_dir = self.template_dir / ".tez-gui-yedekler"
        backup_dir.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        for filename in ("tez.tex", "tez-bilgileri.json", "sirt-kapak.tex"):
            source = self.template_dir / filename
            if source.exists():
                shutil.copy2(source, backup_dir / f"{stamp}-{filename}")

    def preview_changes(self):
        if not self.save_json(notify=False):
            return
        self.run_command(self.template_dir, self.ps("tez-bilgileri-uygula.ps1", "-Config", ".\\tez-bilgileri.json", "-WhatIf"), "Ön izleme")

    def validate_form(self):
        errors = []
        for label, key, require_day in [
            ("Savunma ay/yıl", "defense_month_year", False),
            ("Tez verme tarihi", "submission", True),
            ("Savunma tarihi", "defense", True),
            ("Yönetim Kurulu tarihi", "board", True),
        ]:
            values = self.date_vars.get(key, {})
            year = values.get("year", tk.StringVar()).get().strip()
            day = values.get("day", tk.StringVar()).get().strip()
            month = values.get("month", tk.StringVar(value=TR_MONTHS[0])).get()
            if not year and not day:
                continue
            if not year.isdigit() or len(year) != 4:
                errors.append(f"{label}: yıl 4 haneli olmalı. Örnek: 2026")
            if require_day:
                if not day.isdigit():
                    errors.append(f"{label}: gün sayı olmalı. Örnek: 21")
                elif year.isdigit() and len(year) == 4:
                    day_number = int(day)
                    max_day = days_in_month(month, year)
                    if day_number < 1 or day_number > max_day:
                        errors.append(f"{label}: {month} {year} için gün 1-{max_day} aralığında olmalı.")
        student_no = self._field_value("ogrencino")
        if student_no and not student_no.isdigit():
            errors.append("Öğrenci No: yalnız rakam girilmeli.")
        cover_year = self._field_value("kapakyili")
        if cover_year and (not cover_year.isdigit() or len(cover_year) != 4):
            errors.append("Kapak yılı: 4 haneli yıl girilmeli. Örnek: 2026")
        if errors:
            messagebox.showwarning("Düzeltilmesi gereken alanlar", "\n".join(errors))
            return False
        return True

    def write_selected_class_options(self):
        degree = DEGREE_VALUE.get(self.degree_var.get(), "yukseklisans")
        citation_style = CITATION_VALUE.get(self.citation_var.get(), "apa")
        thesis_language = "ingilizce" if is_english_thesis_label(self.thesis_language_var.get()) else "turkce"
        decimal_separator = DECIMAL_SEPARATOR_VALUE.get(self.decimal_separator_var.get(), "nokta")
        page_layout = PAGE_LAYOUT_VALUE.get(self.page_layout_var.get(), "tek")
        main_tex = self.template_dir / "tez.tex"
        if main_tex.exists() and read_citation_style(main_tex) != citation_style:
            subprocess.run(self.ps("temizle.ps1"), cwd=str(self.template_dir), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for filename in ["tez.tex", "sirt-kapak.tex"]:
            path = self.template_dir / filename
            if path.exists():
                write_degree(path, degree)
                write_citation_style(path, citation_style)
                write_thesis_language(path, thesis_language)
                write_decimal_separator(path, decimal_separator)
                write_page_layout(path, page_layout)

    def current_missing_items(self):
        macros = self.form_to_macros()
        friendly = [
            ("Öğrenci numarası girilmeli", macros.get("ogrencino", [""])[0], "ogrencino"),
            ("Türkçe tez başlığı gerçek başlık olmalı", " ".join(macros.get("baslik", [])), "baslik1"),
            ("İngilizce tez başlığı gerçek başlık olmalı", " ".join(macros.get("title", [])), "title1"),
            ("Anabilim dalı ve program bilgisi doldurulmalı", " ".join(macros.get("anabilimdali", []) + macros.get("programi", [])), "anabilimdali_tr"),
            ("Savunma ayı/yılı ve tarih bilgileri doldurulmalı", " ".join(macros.get("tarih", []) + macros.get("tezsavunmatarih", [])), "tarih_tr"),
            ("Yönetim Kurulu tarihi ve karar numarası doldurulmalı", " ".join(macros.get("yonetimkurulukarar", [])), "kurul_tarih"),
            ("Danışman ve jüri adları gerçek bilgilerle değiştirilmeli", " ".join(macros.get("tezyoneticisi", []) + macros.get("juriBir", []) + macros.get("juriIki", [])), "danisman_tr"),
            ("Enstitü Müdürü bilgisi teyit edilmeli", " ".join(macros.get("EnstituMuduru", [])), "mudur"),
        ]
        items = []
        for label, value, target in friendly:
            if any(pattern in value for pattern in PLACEHOLDER_PATTERNS):
                items.append({"label": label, "target": target})
        return items

    def refresh_missing(self):
        self.missing_list.delete(0, "end")
        self.missing_targets = []
        items = self.current_missing_items()
        for item in items:
            self.missing_list.insert("end", item["label"])
            self.missing_targets.append(item["target"])
        if not items:
            self.missing_list.insert("end", "Otomatik taramada eksik veya örnek olarak bırakılmış bilgi bulunmadı.")
            self.missing_list.insert("end", "Yine de jüri, tarih, karar numarası ve kapak taşmaları PDF üzerinden kontrol edilmeli.")
            self.missing_targets.extend([None, None])
        self.update_dashboard_status(items)

    def _status_tone_color(self, tone):
        colors = THEMES[self.theme_var.get()]
        if self.theme_var.get() == "Koyu":
            palette = {
                "ok": "#42B883",
                "warn": "#D99A3D",
                "bad": "#D95F5F",
                "info": colors["accent"],
                "pending": colors["soft_line"],
            }
        else:
            palette = {
                "ok": "#2F855A",
                "warn": "#B7791F",
                "bad": "#B83232",
                "info": colors["accent"],
                "pending": colors["soft_line"],
            }
        return palette.get(tone, colors["soft_line"])

    def update_dashboard_status(self, missing_items=None):
        if not getattr(self, "dashboard_vars", None):
            return
        if missing_items is None:
            missing_items = self.current_missing_items()

        def set_card(key, text, hint, tone="info"):
            self.dashboard_vars[key].set(text)
            self.dashboard_hint_vars[key].set(hint)
            card = self.dashboard_cards.get(key)
            if card is not None:
                card.configure(highlightbackground=self._status_tone_color(tone), highlightthickness=2 if tone in {"bad", "warn"} else 1)

        missing_count = len(missing_items)
        set_card(
            "missing",
            "Eksik yok" if missing_count == 0 else f"{missing_count} otomatik eksik",
            "Listeye bak" if missing_count == 0 else "İlk eksik alana git",
            "ok" if missing_count == 0 else "warn",
        )

        data = self.load_control_report_data()
        if data:
            fail = int(data.get("Fail", 0) or 0)
            warning = int(data.get("Warning", 0) or 0)
            manual = int(data.get("Manual", 0) or 0)
            if fail:
                control_text = f"{fail} FAIL, {warning} uyarı"
                control_tone = "bad"
            elif warning or manual:
                control_text = f"{warning} uyarı, {manual} manuel"
                control_tone = "warn"
            else:
                control_text = "Temiz görünüyor"
                control_tone = "ok"
            control_hint = "Özeti aç"
        else:
            control_text = "Henüz çalışmadı"
            control_tone = "info"
            control_hint = "Kontrolü başlat"
        set_card("control", control_text, control_hint, control_tone)

        report_files = [
            self.template_dir / "eksik-bilgiler.md",
            self.template_dir / "kontrol-raporu.md",
            self.template_dir / "yazim-denetimi-raporu.md",
        ]
        ready_reports = [path for path in report_files if path.exists()]
        set_card(
            "reports",
            f"{len(ready_reports)} rapor hazır" if ready_reports else "Rapor yok",
            "Raporları göster" if ready_reports else "Önce rapor üret",
            "info" if ready_reports else "warn",
        )

        delivery_dir = self.template_dir / "teslim"
        if delivery_dir.exists():
            pdf_count = len(list(delivery_dir.glob("*.pdf")))
            delivery_text = f"{pdf_count} PDF hazır" if pdf_count else "Klasör hazır"
            delivery_hint = "Klasörü aç"
            delivery_tone = "ok"
        elif (self.template_dir / "tez.pdf").exists():
            delivery_text = "Ana PDF var"
            delivery_hint = "Teslim sekmesine git"
            delivery_tone = "info"
        else:
            delivery_text = "Henüz yok"
            delivery_hint = "Teslim paketi hazırla"
            delivery_tone = "warn"
        set_card("delivery", delivery_text, delivery_hint, delivery_tone)
        self.update_next_action(missing_items, data)
        self.update_workflow_steps(missing_items, data)

    def update_workflow_steps(self, missing_items=None, control_data=None):
        if not getattr(self, "workflow_step_vars", None):
            return
        if missing_items is None:
            missing_items = self.current_missing_items()
        if control_data is None:
            control_data = self.load_control_report_data()

        missing_count = len(missing_items)
        fail = warning = manual = 0
        if control_data:
            fail = int(control_data.get("Fail", 0) or 0)
            warning = int(control_data.get("Warning", 0) or 0)
            manual = int(control_data.get("Manual", 0) or 0)
        control_clean = bool(control_data) and not fail and not warning and not manual
        writing_ready = (self.template_dir / "yazim-denetimi-raporu.md").exists()
        delivery_ready = (self.template_dir / "teslim").exists()

        if missing_count:
            info_status = f"{missing_count} eksik"
            info_tone = "warn"
            missing_status = "Tamamla"
            missing_tone = "warn"
        else:
            info_status = "Tamam"
            info_tone = "ok"
            missing_status = "Eksik yok"
            missing_tone = "ok"

        if missing_count:
            control_status = "Bekliyor"
            control_tone = "pending"
        elif not control_data:
            control_status = "Çalıştır"
            control_tone = "info"
        elif fail:
            control_status = f"{fail} FAIL"
            control_tone = "bad"
        elif warning or manual:
            control_status = f"{warning + manual} uyarı"
            control_tone = "warn"
        else:
            control_status = "Temiz"
            control_tone = "ok"

        if not control_clean:
            writing_status = "Bekliyor"
            writing_tone = "pending"
        elif writing_ready:
            writing_status = "Rapor var"
            writing_tone = "ok"
        else:
            writing_status = "Yazımı aç"
            writing_tone = "info"

        if delivery_ready:
            delivery_status = "Hazır"
            delivery_tone = "ok"
        elif not control_clean:
            delivery_status = "Bekliyor"
            delivery_tone = "pending"
        else:
            delivery_status = "Hazırla"
            delivery_tone = "info"

        states = {
            "info": (info_status, info_tone),
            "missing": (missing_status, missing_tone),
            "control": (control_status, control_tone),
            "writing": (writing_status, writing_tone),
            "delivery": (delivery_status, delivery_tone),
        }
        colors = THEMES[self.theme_var.get()]
        for key, (status, tone) in states.items():
            self.workflow_step_vars[key].set(status)
            frame = self.workflow_step_frames.get(key)
            if frame is not None:
                frame.configure(
                    highlightbackground=self._status_tone_color(tone),
                    highlightthickness=2 if tone in {"bad", "warn", "info"} else 1,
                )
            title_label = self.workflow_step_title_labels.get(key)
            status_label = self.workflow_step_status_labels.get(key)
            if title_label is not None:
                title_label.configure(foreground=colors["muted"] if tone == "pending" else colors["fg"])
            if status_label is not None:
                status_label.configure(foreground=self._status_tone_color(tone) if tone != "pending" else colors["muted"])

    def determine_next_action(self, missing_items=None, control_data=None):
        if missing_items is None:
            missing_items = self.current_missing_items()
        if missing_items:
            first = missing_items[0]
            return {
                "key": "missing",
                "title": "Sonraki adım: eksik bilgileri tamamlayın",
                "detail": first["label"],
                "button": "İlk Eksik Alana Git",
                "icon": "missing",
                "tone": "warn",
            }

        if control_data is None:
            control_data = self.load_control_report_data()
        if not control_data:
            return {
                "key": "control_run",
                "title": "Sonraki adım: son kontrolü çalıştırın",
                "detail": "Eksik alan görünmüyor; derleme ve teslim kontrolleri henüz çalışmadı.",
                "button": "Kontrolü Başlat",
                "icon": "check",
                "tone": "info",
            }

        fail = int(control_data.get("Fail", 0) or 0)
        warning = int(control_data.get("Warning", 0) or 0)
        manual = int(control_data.get("Manual", 0) or 0)
        if fail:
            return {
                "key": "control_summary",
                "title": "Sonraki adım: FAIL satırlarını düzeltin",
                "detail": f"{fail} FAIL var; kontrol özeti sizi ilgili hedeflere götürebilir.",
                "button": "Kontrol Özeti",
                "icon": "check",
                "tone": "bad",
            }
        if warning or manual:
            return {
                "key": "control_summary",
                "title": "Sonraki adım: uyarıları gözden geçirin",
                "detail": f"{warning} uyarı ve {manual} manuel kontrol maddesi var.",
                "button": "Kontrol Özeti",
                "icon": "check",
                "tone": "warn",
            }

        writing_report = self.template_dir / "yazim-denetimi-raporu.md"
        if not writing_report.exists():
            return {
                "key": "writing",
                "title": "Sonraki adım: yazım denetimi yapın",
                "detail": "Kontrol temiz görünüyor; tez metni için yazım ön denetimi henüz yok.",
                "button": "Yazımı Aç",
                "icon": "spell",
                "tone": "info",
            }

        delivery_dir = self.template_dir / "teslim"
        if not delivery_dir.exists():
            return {
                "key": "package",
                "title": "Sonraki adım: teslim paketini hazırlayın",
                "detail": "Kontrol ve raporlar hazır; teslim klasörü henüz üretilmedi.",
                "button": "Teslim Paketi",
                "icon": "package",
                "tone": "info",
            }

        return {
            "key": "reports",
            "title": "Sonraki adım: son teslimi gözden geçirin",
            "detail": "Temel otomatik adımlar tamam; raporları ve teslim klasörünü son kez kontrol edin.",
            "button": "Raporları Göster",
            "icon": "read",
            "tone": "ok",
        }

    def update_next_action(self, missing_items=None, control_data=None):
        if not hasattr(self, "next_action_button"):
            return
        action = self.determine_next_action(missing_items, control_data)
        self.next_action_key = action["key"]
        self.next_action_title_var.set(action["title"])
        self.next_action_detail_var.set(action["detail"])
        self.next_action_button_var.set(action["button"])
        self.next_action_icon.configure(image=self._button_icon(action["icon"]))
        self.next_action_button.configure(image=self._button_icon(action["icon"], "primary"))
        self.next_action_frame.configure(highlightbackground=self._status_tone_color(action["tone"]))

    def run_next_action(self):
        key = self.next_action_key
        if key == "missing":
            self.handle_dashboard_card("missing")
        elif key == "control_run":
            self.run_check()
        elif key == "control_summary":
            self.handle_dashboard_card("control")
        elif key == "writing":
            self.run_writing_check()
        elif key == "package":
            self.notebook.select(self.run_tab)
            self.run_package()
        elif key == "reports":
            self.show_reports_overview()
        else:
            self.notebook.select(self.run_tab)

    def handle_workflow_step(self, key):
        if key == "info":
            self.notebook.select(self.info_tab)
            return
        if key == "missing":
            self.handle_dashboard_card("missing")
            return
        if key == "control":
            self.handle_dashboard_card("control")
            return
        if key == "writing":
            self.run_writing_check()
            return
        if key == "delivery":
            self.handle_dashboard_card("delivery")
            return

    def handle_dashboard_card(self, key):
        if key == "missing":
            items = self.current_missing_items()
            self.refresh_missing()
            self.notebook.select(self.missing_tab)
            if items:
                self.missing_list.selection_clear(0, "end")
                self.missing_list.selection_set(0)
                self.missing_list.see(0)
                self.focus_form_field(items[0]["target"])
            else:
                self.missing_list.focus_set()
            return
        if key == "control":
            if self.load_control_report_data():
                self.notebook.select(self.run_tab)
                self.show_control_report_summary()
            else:
                self.run_check()
            return
        if key == "reports":
            self.show_reports_overview()
            return
        if key == "delivery":
            delivery_dir = self.template_dir / "teslim"
            if delivery_dir.exists():
                os.startfile(delivery_dir)
            else:
                self.notebook.select(self.run_tab)
                self.output.delete("1.0", "end")
                self.output.insert("end", "Teslim paketi henüz hazır değil.\n")
                self.output.insert("end", "Teslim Paketi düğmesiyle PDF ve teslim klasörü üretilebilir.\n")
            return

    def show_reports_overview(self):
        self.notebook.select(self.run_tab)
        colors = THEMES[self.theme_var.get()]
        self.output.delete("1.0", "end")
        self.output.tag_configure("reports_title", font=("Segoe UI", 11, "bold"), foreground=colors["fg"])
        self.output.tag_configure("reports_section", font=("Segoe UI", 10, "bold"), foreground=colors["accent_dark"])
        self.output.tag_configure("reports_muted", foreground=colors["muted"])
        reports = [
            ("Eksik Bilgi Raporu", self.template_dir / "eksik-bilgiler.md", self.run_missing_report),
            ("Kontrol Raporu", self.template_dir / "kontrol-raporu.md", self.run_check),
            ("Yazım Denetimi Raporu", self.template_dir / "yazim-denetimi-raporu.md", self.run_writing_check),
            ("Kılavuz Uygunluk Raporu", self.template_dir / "tez_kilavuz_uygunluk_rapor.md", self.run_guideline_pdf_check),
        ]
        self.output.insert("end", "Raporlar\n", "reports_title")
        self.output.insert("end", "Hazır raporlar tıklanarak açılabilir; eksik olanlar ilgili işlemle üretilebilir.\n\n", "reports_muted")
        for title, path, action in reports:
            self.output.insert("end", f"{title}: ", "reports_section")
            if path.exists():
                self.insert_output_link(path.name, lambda p=path: self.open_text_file_at_line(p), "report_file")
                self.output.insert("end", f"  ({datetime.fromtimestamp(path.stat().st_mtime).strftime('%d.%m.%Y %H:%M')})\n", "reports_muted")
            else:
                self.output.insert("end", "hazır değil  ", "reports_muted")
                self.insert_output_link("üret", action, "report_action")
                self.output.insert("end", "\n")
        self.output.see("1.0")

    def focus_form_field(self, key):
        if not key or key not in self.field_widgets:
            return False
        self.notebook.select(self.info_tab)
        if key in {"tarih_tr", "tezverme_tr", "savunma_tr", "kurul_tarih", "kurul_no", "mudur", "juri1", "juri1_kurum", "juri2", "juri2_kurum", "juri3", "juri3_kurum", "juri4", "juri4_kurum", "juri5", "juri5_kurum"}:
            self.form_notebook.select(self.approval_form_tab)
        else:
            self.form_notebook.select(self.cover_form_tab)
        widget = self.field_widgets[key][1]
        target = widget
        children = widget.winfo_children() if hasattr(widget, "winfo_children") else []
        if children:
            target = children[0]
        self.after(80, lambda w=target: (w.focus_set(), getattr(w, "select_range", lambda *_args: None)(0, "end")))
        return True

    def focus_missing_target(self, _event=None):
        selection = self.missing_list.curselection()
        if not selection:
            return
        index = selection[0]
        if index >= len(self.missing_targets):
            return
        self.focus_form_field(self.missing_targets[index])

    def parse_missing_report_rows(self, report_path):
        report_path = Path(report_path)
        rows = []
        manual = []
        if not report_path.exists():
            return rows, manual
        try:
            lines = report_path.read_text(encoding="utf-8-sig").splitlines()
        except OSError:
            return rows, manual
        in_manual = False
        label_targets = {
            "Ogrenci numarasi": "ogrencino",
            "Varsa mezuniyet/unvan bilgisi": "unvan",
            "Anabilim dali / department": "anabilimdali_tr",
            "Program adi / programme": "program_tr",
            "Savunma ayi/yili": "tarih_tr",
            "Enstitu Yonetim Kurulu tarihi ve karar numarasi": "kurul_tarih",
            "Danisman/juri/Enstitu Muduru adlari": "danisman_tr",
            "Turkce ve Ingilizce tez basligi": "baslik1",
            "Ozgecmis ad soyad": None,
        }
        display_labels = {
            "Ogrenci numarasi": "Öğrenci numarası",
            "Varsa mezuniyet/unvan bilgisi": "Mezuniyet / unvan bilgisi",
            "Anabilim dali / department": "Anabilim dalı / department",
            "Program adi / programme": "Program adı / programme",
            "Savunma ayi/yili": "Savunma ayı / yılı",
            "Enstitu Yonetim Kurulu tarihi ve karar numarasi": "Enstitü Yönetim Kurulu tarihi ve karar numarası",
            "Danisman/juri/Enstitu Muduru adlari": "Danışman, jüri veya Enstitü Müdürü adları",
            "Turkce ve Ingilizce tez basligi": "Türkçe ve İngilizce tez başlığı",
            "Ozgecmis ad soyad": "Özgeçmiş ad soyad",
        }
        for index, line in enumerate(lines):
            if line.startswith("## Elle teyit"):
                in_manual = True
                continue
            if line.startswith("## ") and in_manual:
                in_manual = False
            match = re.match(r"- \[ \] (.*?) - ([^:]+):(\d+)", line)
            if match:
                label, filename, line_number = match.groups()
                excerpt = ""
                if index + 1 < len(lines):
                    excerpt = re.sub(r"^\s*-\s*", "", lines[index + 1]).strip()
                rows.append({
                    "label": display_labels.get(label, label),
                    "target": label_targets.get(label),
                    "path": self.template_dir / filename,
                    "line": int(line_number),
                    "excerpt": excerpt,
                })
            elif in_manual and line.startswith("- [ ] "):
                manual.append(line[6:].strip())
        return rows, manual

    def configure_output_link(self, tag):
        colors = THEMES[self.theme_var.get()]
        self.output.tag_configure(tag, foreground=colors["accent"], underline=True)
        self.output.tag_bind(tag, "<Enter>", lambda _event: self.output.configure(cursor="hand2"))
        self.output.tag_bind(tag, "<Leave>", lambda _event: self.output.configure(cursor=""))

    def insert_output_link(self, text, callback, tag_prefix):
        counter = getattr(self, "output_link_counter", 0) + 1
        self.output_link_counter = counter
        tag = f"{tag_prefix}_{counter}"
        self.output.mark_set("insert", "end-1c")
        start = self.output.index("insert")
        self.output.insert("insert", text)
        end = self.output.index("insert")
        self.output.tag_add(tag, start, end)
        self.configure_output_link(tag)
        self.output.tag_bind(tag, "<Button-1>", lambda _event: callback())

    def show_missing_report_summary(self, report_path, exit_code):
        report_path = Path(report_path)
        report_rows, manual_items = self.parse_missing_report_rows(report_path)
        form_items = self.current_missing_items()
        colors = THEMES[self.theme_var.get()]
        self.output.delete("1.0", "end")
        self.output.tag_configure("missing_title", font=("Segoe UI", 11, "bold"), foreground=colors["fg"])
        self.output.tag_configure("missing_section", font=("Segoe UI", 10, "bold"), foreground=colors["accent_dark"])
        self.output.tag_configure("missing_muted", foreground=colors["muted"])
        self.output.insert("end", "Eksik Bilgi Raporu\n", "missing_title")
        self.output.insert("end", "Markdown raporu: ")
        if report_path.exists():
            self.insert_output_link(report_path.name, lambda p=report_path: self.open_text_file_at_line(p), "missing_report")
        else:
            self.output.insert("end", str(report_path))
        self.output.insert("end", "\n")
        if exit_code not in (0, None):
            self.output.insert("end", f"Rapor komutu çıkış kodu: {exit_code}\n", "missing_muted")
        self.output.insert("end", "\n")

        rows_to_show = report_rows
        if not rows_to_show and form_items:
            rows_to_show = [{"label": item["label"], "target": item["target"], "path": None, "line": None, "excerpt": ""} for item in form_items]

        if rows_to_show:
            self.output.insert("end", "Düzeltilmesi gerekenler\n", "missing_section")
            for number, row in enumerate(rows_to_show, 1):
                self.output.insert("end", f"{number}. {row['label']}  ")
                if row.get("target"):
                    self.insert_output_link("forma git", lambda key=row["target"]: self.focus_form_field(key), "missing_form")
                    self.output.insert("end", "  ")
                if row.get("path") and row.get("line"):
                    self.insert_output_link(f"{row['path'].name}:{row['line']}", lambda p=row["path"], line=row["line"]: self.open_text_file_at_line(p, line), "missing_file")
                self.output.insert("end", "\n")
                if row.get("excerpt"):
                    self.output.insert("end", f"   {textwrap.shorten(row['excerpt'], width=150, placeholder='...')}\n", "missing_muted")
            self.output.insert("end", "\n")
        else:
            self.output.insert("end", "Otomatik taramada eksik veya örnek olarak bırakılmış bilgi bulunmadı.\n\n")

        if manual_items:
            self.output.insert("end", "Elle teyit edilecekler\n", "missing_section")
            for item in manual_items[:8]:
                self.output.insert("end", f"- {item}\n")
            if len(manual_items) > 8:
                self.output.insert("end", f"- ... {len(manual_items) - 8} madde daha markdown raporunda.\n", "missing_muted")
            self.output.insert("end", "\n")

        self.output.insert("end", "Raporu yeniden üretmek için formu kaydedip bu düğmeye tekrar basabilirsiniz.\n", "missing_muted")
        self.output.see("1.0")
        self.update_dashboard_status(form_items)

    def refresh_system(self):
        tools = detect_tools()
        lines = []
        for name, path in tools.items():
            lines.append(f"{name:10} : {'Bulundu - ' + path if path else 'Bulunamadi'}")
        lines.append("")
        if tools.get("xelatex"):
            lines.append("Derleme motoru: XeLaTeX. Calibri ve Türkçe karakter uyumu için şablonda sabit kullanılır.")
            self.engine_var.set("xelatex")
        elif tools.get("pdflatex"):
            lines.append("XeLaTeX bulunamadı. Şablon Calibri uyumu için XeLaTeX gerektirir; TeX Live/MiKTeX kurulumunu kontrol edin.")
            self.engine_var.set("xelatex")
        else:
            lines.append("LaTeX derleyici bulunamadı. TeX Live/MiKTeX kurulumu gerekir.")
        self.system_text.delete("1.0", "end")
        self.system_text.insert("end", "\n".join(lines))
        self.update_dashboard_status()

    def run_safe_update(self):
        script = ROOT / "guncelle.ps1"
        if script.exists():
            if self.running:
                messagebox.showwarning("İşlem sürüyor", "Devam eden işlem bitmeden yeni işlem başlatılamaz.")
                return
            self.running = True
            self.start_busy_feedback("Güncelleme denetleniyor")
            self.output.delete("1.0", "end")
            self.output.insert("end", "== Güncelleme denetimi ==\n")
            self.output.insert("end", "Yeni sürümde nelerin değiştiği okunuyor. Dosyalara henüz dokunulmadı.\n")
            self.output.see("end")
            self.notebook.select(self.run_tab)
            self.update_idletasks()

            def worker():
                command = [
                    "powershell",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script),
                    "-Workdir",
                    str(self.template_dir),
                    "-CheckOnly",
                ]
                try:
                    result = subprocess.run(
                        command,
                        cwd=str(ROOT),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=90,
                    )
                    output = result.stdout or ""
                    code = result.returncode
                except Exception as exc:
                    output = f"Güncelleme denetimi çalıştırılamadı: {exc}"
                    code = 2
                self.output_queue.put(("__UPDATE_CHECK_DONE__", code, output))

            threading.Thread(target=worker, daemon=True).start()
            return
        messagebox.showinfo(
            "Güncelleme hazır değil",
            "Güvenli internet güncellemesi için bu klasöre guncelle.ps1 betiği veya sürüm adresi tanımı eklenmeli.\n\n"
            "Bu düğme tez dosyalarını bozmadan yalnızca şablon/GUI dosyalarını güncelleyecek şekilde ayrıldı.",
        )

    def schedule_update_check(self):
        if self.update_available:
            return
        self.check_for_remote_update()
        self.after(10 * 60 * 1000, self.schedule_update_check)

    def check_for_remote_update(self):
        if self.update_check_running:
            return
        script = ROOT / "guncelle.ps1"
        if not script.exists():
            self.update_available = False
            self.update_status_text = "Güncelleme betiği bulunamadı."
            self.render_update_buttons()
            return
        self.update_check_running = True

        def worker():
            available = False
            status = ""
            try:
                result = subprocess.run(
                    [
                        "powershell",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(script),
                        "-Workdir",
                        str(self.template_dir),
                        "-CheckOnly",
                    ],
                    cwd=str(ROOT),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=45,
                )
                output = result.stdout or ""
                repaired = self._repair_mojibake(output)
                if result.returncode == 0 and "Durum: Güncelleme hazır." in repaired:
                    available = True
                    status = "Yeni sürüm hazır. Yüklemeden önce değişiklik özeti gösterilecek."
                elif "Durum: Panel zaten güncel." in repaired:
                    status = "Güncel."
                elif "Neden:" in repaired:
                    reason = next((line.strip() for line in repaired.splitlines() if line.strip().startswith("Neden:")), "")
                    status = reason or "Güncelleme denetimi tamamlandı; yeni sürüm bulunamadı."
            except Exception:
                status = ""
            self.output_queue.put(("__UPDATE_STATUS__", available, status))

        threading.Thread(target=worker, daemon=True).start()

    def apply_update_status(self, available, status):
        self.update_check_running = False
        self.update_available = bool(available)
        self.update_status_text = status or ""
        self.render_update_buttons()

    def render_update_buttons(self):
        for button in getattr(self, "update_buttons", []):
            try:
                if not button.winfo_exists():
                    continue
                if self.update_available:
                    button.configure(text="Güncelleme hazır", style="UpdateReady.TButton", image=self._button_icon("update_ready"))
                else:
                    if button is getattr(self, "update_button", None):
                        button.configure(text="Güncelle", style="Tiny.TButton", image=self._button_icon("update"))
                    else:
                        button.configure(text="Güncelle", style="Primary.TButton", image=self._button_icon("update", "primary"))
            except tk.TclError:
                continue

    def _extract_update_report_path(self, output):
        match = re.search(r"Rapor:\s*(.+)", output or "")
        if not match:
            return None
        path = Path(match.group(1).strip().strip('"'))
        return path if path.exists() else None

    def _repair_mojibake(self, text):
        if not text or not any(marker in text for marker in ("Ã", "Ä", "Å")):
            return text
        for encoding in ("cp1252", "latin1", "cp1254"):
            try:
                repaired = text.encode(encoding).decode("utf-8")
            except UnicodeError:
                continue
            if repaired.count("Ã") + repaired.count("Ä") + repaired.count("Å") < text.count("Ã") + text.count("Ä") + text.count("Å"):
                return repaired
        return text

    def _short_update_summary(self, output, limit=1800):
        report_path = self._extract_update_report_path(output)
        text = ""
        if report_path:
            try:
                text = report_path.read_text(encoding="utf-8-sig")
            except OSError:
                text = output or ""
        else:
            text = output or ""
        text = self._repair_mojibake(text)
        text = text.strip()
        if len(text) > limit:
            text = text[:limit].rstrip() + "\n\n..."
        return text, report_path

    def handle_update_check_done(self, code, output):
        self.running = False
        self.stop_busy_feedback()
        self.output.insert("end", output or "")
        self.output.insert("end", f"\n[Denetim bitti] Çıkış kodu: {code}\n")
        self.output.see("end")
        summary, report_path = self._short_update_summary(output)
        if code != 0 or "Durum: Güncelleme hazır." not in (output or ""):
            title = "Güncelleme uygulanmadı" if code else "Güncelleme bilgisi"
            messagebox.showinfo(title, summary or "Güncelleme için uygulanacak yeni bir sürüm bulunamadı.")
            if code == 0:
                self.update_available = False
                self.render_update_buttons()
            return
        if messagebox.askyesno("Yeni sürüm hazır", f"{summary}\n\nBu güncellemeyi şimdi yüklemek ister misiniz?"):
            script = ROOT / "guncelle.ps1"
            self.run_command(
                ROOT,
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script), "-Workdir", str(self.template_dir)],
                "Şablon ve GUI güncelleme",
                on_complete=self.finish_safe_update,
            )
        elif report_path:
            self.status.configure(text=f"Güncelleme bekliyor. Rapor: {report_path.name}")

    def finish_safe_update(self, code):
        self.refresh_system()
        if code == 0:
            self.update_available = False
            self.render_update_buttons()
            if messagebox.askyesno("Güncelleme tamamlandı", "Güncelleme tamamlandı. Panel yeni sürümle yeniden başlatılsın mı?"):
                self.restart_app()
        else:
            messagebox.showwarning(
                "Güncelleme tamamlanmadı",
                "Güncelleme uygulanamadı veya eski duruma geri dönüldü. Ayrıntı için alttaki güncelleme raporuna bakabilirsiniz.",
            )

    def restart_app(self):
        try:
            subprocess.Popen([sys.executable, str(Path(__file__).resolve())], cwd=str(ROOT))
            self.destroy()
        except Exception as exc:
            messagebox.showwarning("Yeniden başlatılamadı", f"Panel otomatik yeniden başlatılamadı:\n{exc}")

    def ps(self, script, *args):
        return ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(self.template_dir / script), *args]

    def run_missing_report(self):
        report_path = self.template_dir / "eksik-bilgiler.md"
        self.run_command(
            self.template_dir,
            self.ps("eksik-bilgiler.ps1"),
            "Eksik Bilgi Raporu",
            on_complete=lambda code, path=report_path: self.show_missing_report_summary(path, code),
        )

    def run_check(self):
        args = ["-Engine", self.engine_var.get(), "-Report"]
        if self.with_spine_var.get():
            args.append("-WithSpine")
        self.run_command(
            self.template_dir,
            self.ps("kontrol.ps1", *args),
            "Kontrol",
            output_mode="control",
            on_complete=self.show_control_report_summary,
        )

    def run_package(self):
        args = ["-Engine", self.engine_var.get()]
        if self.with_spine_var.get():
            args.append("-WithSpine")
        self.run_command(self.template_dir, self.ps("teslim-hazirla.ps1", *args), "Teslim paketi")

    def run_latex_diagnostics(self, on_complete=None):
        if self.running:
            messagebox.showwarning("İşlem sürüyor", "Devam eden işlem bitmeden yeni işlem başlatılamaz.")
            return
        self.close_diagnostic_suggestion_popup()
        tex_path = self.template_dir / "tez.tex"
        if not tex_path.exists():
            messagebox.showerror("tez.tex bulunamadı", f"Beklenen ana dosya yok:\n{tex_path}")
            return
        engine = self.engine_var.get() or "xelatex"
        command = [engine, "-interaction=nonstopmode", "-file-line-error", "-synctex=1", "tez.tex"]
        self.running = True
        self.start_busy_feedback("Akıllı Derleme Tanılama")
        self.notebook.select(self.run_tab)
        self.output.delete("1.0", "end")
        self.output.insert("end", "== Akıllı Derleme Tanılama ==\n")
        self.output.insert("end", "LaTeX derlemesi hata satırlarını yakalayacak biçimde başlatıldı.\n")
        self.output.insert("end", "Sonuçlar tamamlanınca burada tıklanabilir özet olarak gösterilecek.\n")
        self.output.see("end")
        self.update_idletasks()

        def finish_diagnostics(exit_code):
            self.show_latex_diagnostics_summary(exit_code)
            if callable(on_complete):
                on_complete(exit_code)

        def worker():
            code = None
            captured = []
            try:
                process = subprocess.Popen(command, cwd=str(self.template_dir), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
                assert process.stdout is not None
                for line in process.stdout:
                    captured.append(line)
                code = process.wait()
                log_text = ""
                log_path = self.template_dir / "tez.log"
                if log_path.exists():
                    try:
                        log_text = log_path.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        log_text = ""
                findings = self.parse_latex_diagnostics("".join(captured), log_text)
                self.write_latex_diagnostics_reports(findings, code, "".join(captured))
            except Exception as exc:
                self.output_queue.put(f"\n[HATA] Akıllı tanılama çalıştırılamadı: {exc}\n")
            finally:
                self.output_queue.put(("__DONE__", code, finish_diagnostics))

        threading.Thread(target=worker, daemon=True).start()

    def run_clean(self):
        self.run_command(self.template_dir, self.ps("temizle.ps1"), "Ara dosyaları temizle")

    def run_writing_check(self):
        self.open_writing_review_window()

    def run_guideline_pdf_check(self):
        workdir = Path(self.template_dir)
        pdf_path = workdir / "tez.pdf"
        checker_path = ROOT.parent / "Tez PDF Kılavuz Ön Denetim Raporu" / "pdf_tez_uygunluk_deneticisi_v3.py"

        self.notebook.select(self.run_tab)
        self.output.delete("1.0", "end")
        self.output.insert("end", "== Kılavuz Uygunluk Denetimi ==\n")
        if not pdf_path.exists():
            self.output.insert("end", "tez.pdf bulunamadı. Önce PDF oluşturun veya teslim/kontrol işlemini çalıştırın.\n")
            self.output.insert("end", f"Beklenen PDF: {pdf_path}\n")
            self.output.see("end")
            return
        if not checker_path.exists():
            self.output.insert("end", f"Denetçi script bulunamadı: {checker_path}\n")
            self.output.see("end")
            return

        self.output.insert("end", "PDF kılavuz ölçütlerine göre inceleniyor...\n")
        self.output.insert("end", "Başlık, şekil/tablo, satır aralığı, yaklaşık boş satır/Enter ve marjin bilgileri raporlanacak.\n")
        self.output.see("end")

        def finish(result):
            self.output.insert("end", "\n")
            if isinstance(result, Exception):
                self.output.insert("end", f"[HATA] Kılavuz denetimi çalıştırılamadı: {result}\n")
                self.output.see("end")
                return
            out_pdf, out_json, out_md = result
            self.output.insert("end", "Denetim tamamlandı.\n")
            self.output.insert("end", "İşaretli PDF: ")
            self.insert_output_link(Path(out_pdf).name, lambda p=Path(out_pdf): self.open_external_file(p), "report_file")
            self.output.insert("end", f"  ({out_pdf})\n")
            self.output.insert("end", "Markdown rapor: ")
            self.insert_output_link(Path(out_md).name, lambda p=Path(out_md): self.open_text_file_at_line(p), "report_file")
            self.output.insert("end", f"  ({out_md})\n")
            self.output.insert("end", f"JSON veri: {out_json}\n")
            try:
                data = json.loads(Path(out_json).read_text(encoding="utf-8"))
                author_findings = [
                    finding
                    for page in data.get("pages", [])
                    for finding in page.get("rule_findings", [])
                    if finding.get("owner") == "author" and finding.get("status") in {"check", "tolerance"}
                ]
                template_findings = [
                    finding
                    for page in data.get("pages", [])
                    for finding in page.get("rule_findings", [])
                    if finding.get("owner") == "template" and finding.get("status") in {"check", "tolerance"}
                ]
            except Exception:
                author_findings = []
                template_findings = []
            self.output.insert("end", "\nÖğrenci/yazar kontrolündeki bulgular:\n")
            if author_findings:
                for finding in author_findings[:20]:
                    self.output.insert("end", f"- Sayfa {finding.get('page')}: {finding.get('title')} - {finding.get('message')}\n")
                if len(author_findings) > 20:
                    self.output.insert("end", f"... {len(author_findings) - 20} bulgu daha Markdown raporunda.\n")
            else:
                self.output.insert("end", "- Bu kapsamda kontrol gerektiren bulgu yok.\n")
            self.output.insert("end", f"\nŞablon/biçim ayarıyla ilgili bulgu sayısı: {len(template_findings)}\n")
            self.output.insert("end", "\nBu denetim iki alanı ayırır: öğrencinin tez yazarken düzeltebileceği kılavuz ihlalleri ve şablonun otomatik uygulaması gereken biçim kuralları.\n")
            self.output.see("end")

        def python_candidates():
            seen = set()
            candidates = [
                sys.executable,
                shutil.which("python"),
                shutil.which("py"),
                "python",
                Path(os.environ.get("LOCALAPPDATA", "")) / "Python" / "pythoncore-3.14-64" / "python.exe",
                Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Python" / "Python314" / "python.exe",
                Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Python" / "Python313" / "python.exe",
            ]
            for candidate in candidates:
                if not candidate:
                    continue
                if isinstance(candidate, Path) and not candidate.exists():
                    continue
                key = str(candidate).lower()
                if key in seen:
                    continue
                seen.add(key)
                yield str(candidate)

        def find_python_with_pymupdf():
            for python_exe in python_candidates():
                cmd = [python_exe, "-c", "import fitz"]
                if Path(python_exe).name.lower() == "py":
                    cmd = [python_exe, "-3", "-c", "import fitz"]
                try:
                    probe = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", timeout=10)
                except (OSError, subprocess.SubprocessError):
                    continue
                if probe.returncode == 0:
                    return python_exe
            return None

        def worker():
            try:
                python_exe = find_python_with_pymupdf()
                if not python_exe:
                    raise RuntimeError(
                        "PyMuPDF/fitz modülü bulunamadı. Komut satırında `python -m pip install pymupdf` çalıştırıp tekrar deneyin."
                    )
                runner = (
                    "import importlib.util,json,sys\n"
                    "from pathlib import Path\n"
                    "checker=Path(sys.argv[1]); pdf=Path(sys.argv[2]); outdir=Path(sys.argv[3])\n"
                    "spec=importlib.util.spec_from_file_location('tez_pdf_kilavuz_denetici', checker)\n"
                    "module=importlib.util.module_from_spec(spec)\n"
                    "spec.loader.exec_module(module)\n"
                    "out=module.analyze_pdf(pdf, out_dir=outdir, auto_open=False)\n"
                    "print(json.dumps([str(item) for item in out], ensure_ascii=True))\n"
                )
                cmd = [python_exe, "-c", runner, str(checker_path), str(pdf_path), str(workdir)]
                if Path(python_exe).name.lower() == "py":
                    cmd = [python_exe, "-3", "-c", runner, str(checker_path), str(pdf_path), str(workdir)]
                completed = subprocess.run(
                    cmd,
                    cwd=str(ROOT.parent),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=180,
                )
                if completed.returncode != 0:
                    raise RuntimeError((completed.stderr or completed.stdout or "Denetçi çıktı üretmeden kapandı.").strip())
                payload = None
                for line in reversed((completed.stdout or "").splitlines()):
                    line = line.strip()
                    if line.startswith("[") and line.endswith("]"):
                        payload = json.loads(line)
                        break
                if not payload or len(payload) != 3:
                    raise RuntimeError(f"Denetçi çıktısı okunamadı: {completed.stdout.strip()}")
                result = tuple(Path(item) for item in payload)
            except Exception as exc:
                result = exc
            self.after(0, lambda: finish(result))

        threading.Thread(target=worker, daemon=True).start()

    def run_tex_precheck(self):
        findings = yazim_denetimi.analyze_tex_structure(self.template_dir)
        report = yazim_denetimi.write_tex_structure_report(self.template_dir, findings)
        self.notebook.select(self.run_tab)
        self.output.delete("1.0", "end")
        self.output.insert("end", "== TeX Ön Kontrol ==\n")
        if findings:
            for rel, number, message, raw in findings[:80]:
                self.output.insert("end", f"{rel}:{number} - {message}\n")
                if raw:
                    self.output.insert("end", f"  {raw[:180]}\n")
            if len(findings) > 80:
                self.output.insert("end", f"... {len(findings) - 80} bulgu daha raporda.\n")
        else:
            self.output.insert("end", "Temel TeX ön kontrolünde belirgin sorun bulunmadı.\n")
        self.output.insert("end", f"Rapor: {report}\n")
        self.output.see("end")

    def render_pdf_pages(self, pdf_path, output_dir, dpi=120):
        output_dir.mkdir(parents=True, exist_ok=True)
        marker = output_dir / "render-cache.json"
        cached_pages = sorted(
            output_dir.glob("page-*.png"),
            key=lambda path: int(re.search(r"-(\d+)\.png$", path.name).group(1)) if re.search(r"-(\d+)\.png$", path.name) else 0,
        )
        if marker.exists() and cached_pages:
            try:
                cache = json.loads(marker.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                cache = {}
            pdf_stat = pdf_path.stat()
            if cache.get("dpi") == dpi and cache.get("pdf_mtime_ns") == pdf_stat.st_mtime_ns and cache.get("pdf_size") == pdf_stat.st_size:
                return cached_pages
        for old_page in cached_pages:
            old_page.unlink()
        command = ["pdftoppm", "-png", "-r", str(dpi), str(pdf_path), str(output_dir / "page")]
        result = subprocess.run(
            command,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        pages = sorted(
            output_dir.glob("page-*.png"),
            key=lambda path: int(re.search(r"-(\d+)\.png$", path.name).group(1)) if re.search(r"-(\d+)\.png$", path.name) else 0,
        )
        if result.returncode != 0 or not pages:
            raise RuntimeError(result.stdout.strip() or "PDF sayfaları görsele dönüştürülemedi.")
        pdf_stat = pdf_path.stat()
        marker.write_text(json.dumps({
            "dpi": dpi,
            "pdf_mtime_ns": pdf_stat.st_mtime_ns,
            "pdf_size": pdf_stat.st_size,
        }), encoding="utf-8")
        return pages

    def extract_pdf_word_boxes(self, pdf_path, output_dir):
        bbox_path = output_dir / "pdf-words-bbox.html"
        marker = output_dir / "bbox-cache.json"
        should_extract = True
        if bbox_path.exists() and marker.exists():
            try:
                cache = json.loads(marker.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                cache = {}
            pdf_stat = pdf_path.stat()
            should_extract = not (cache.get("pdf_mtime_ns") == pdf_stat.st_mtime_ns and cache.get("pdf_size") == pdf_stat.st_size)
        if should_extract:
            result = subprocess.run(
                ["pdftotext", "-bbox", "-enc", "UTF-8", str(pdf_path), str(bbox_path)],
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            if result.returncode != 0 or not bbox_path.exists():
                return []
            pdf_stat = pdf_path.stat()
            marker.write_text(json.dumps({"pdf_mtime_ns": pdf_stat.st_mtime_ns, "pdf_size": pdf_stat.st_size}), encoding="utf-8")
        pages = []
        try:
            root = ET.parse(bbox_path).getroot()
            page_nodes = root.findall(".//{http://www.w3.org/1999/xhtml}page")
        except ET.ParseError:
            page_nodes = []
        for page_node in page_nodes:
            page = {
                "width": float(page_node.attrib.get("width", "0") or 0),
                "height": float(page_node.attrib.get("height", "0") or 0),
                "words": [],
            }
            for word_node in page_node.findall("{http://www.w3.org/1999/xhtml}word"):
                text = "".join(word_node.itertext()).strip()
                if not text:
                    continue
                page["words"].append({
                    "text": text,
                    "norm": self._normalize_pdf_word(text),
                    "x0": float(word_node.attrib.get("xMin", "0") or 0),
                    "y0": float(word_node.attrib.get("yMin", "0") or 0),
                    "x1": float(word_node.attrib.get("xMax", "0") or 0),
                    "y1": float(word_node.attrib.get("yMax", "0") or 0),
                })
            pages.append(page)
        if pages:
            return pages
        content = bbox_path.read_text(encoding="utf-8", errors="ignore")
        for page_match in re.finditer(r"<page\s+([^>]*)>(.*?)</page>", content, re.S | re.I):
            page_attrs = self._html_attrs(page_match.group(1))
            page = {
                "width": float(page_attrs.get("width", "0") or 0),
                "height": float(page_attrs.get("height", "0") or 0),
                "words": [],
            }
            for word_match in re.finditer(r"<word\s+([^>]*)>(.*?)</word>", page_match.group(2), re.S | re.I):
                attrs = self._html_attrs(word_match.group(1))
                text = html.unescape(re.sub(r"<[^>]+>", "", word_match.group(2))).strip()
                if not text:
                    continue
                page["words"].append({
                    "text": text,
                    "norm": self._normalize_pdf_word(text),
                    "x0": float(attrs.get("xmin", "0") or 0),
                    "y0": float(attrs.get("ymin", "0") or 0),
                    "x1": float(attrs.get("xmax", "0") or 0),
                    "y1": float(attrs.get("ymax", "0") or 0),
                })
            pages.append(page)
        return pages

    def _html_attrs(self, attr_text):
        return {key.casefold(): value for key, value in re.findall(r'([A-Za-z]+)="([^"]*)"', attr_text)}

    def _normalize_pdf_word(self, value):
        value = value.casefold()
        replacements = str.maketrans({"ı": "i", "İ": "i", "ş": "s", "ğ": "g", "ü": "u", "ö": "o", "ç": "c"})
        value = value.translate(replacements)
        return re.sub(r"[^a-z0-9]+", "", value)

    def locate_findings_in_pdf(self, findings, pdf_pages, page_hints=None):
        locations = []
        search_start = 0
        page_hints = page_hints or []
        for index, (_rel, _number, message, raw) in enumerate(findings):
            page_hint = None
            page_match = re.match(r"PDF_PAGE:(\d+)\n", str(raw))
            if page_match:
                page_hint = max(int(page_match.group(1)) - 1, 0)
                raw = re.sub(r"^PDF_PAGE:\d+\n", "", str(raw), count=1)
            elif index < len(page_hints) and page_hints[index]:
                page_hint = page_hints[index].get("page")
            queries = self._finding_pdf_queries(message, raw)
            location = None
            if str(_rel) == "__pdf_unicode__":
                start_page = page_hint if page_hint is not None else max(int(_number) - 1, 0)
            elif page_hint is not None:
                start_page = page_hint
            elif message.startswith("TeX ön kontrol:"):
                start_page = 0
            else:
                start_page = search_start
            exact_page = page_hint is not None
            allow_single_fallback = "PDF Unicode" not in message
            for query in queries:
                location = self._find_pdf_word_sequence(
                    pdf_pages,
                    query,
                    start_page,
                    exact_page=exact_page,
                    allow_single_fallback=allow_single_fallback,
                )
                if location:
                    break
            locations.append(self._expand_pdf_line_location(location, pdf_pages) if location else None)
            if locations[-1] and start_page == search_start:
                search_start = locations[-1]["page"]
        return locations

    def _finding_pdf_queries(self, message, raw):
        text = yazim_denetimi.strip_latex(raw)
        word_re = r"[\wçğıöşüÇĞİÖŞÜ]+"
        candidates = []
        weak_candidates = []
        if "PDF Unicode" in message:
            raw_text = re.sub(r"^PDF_PAGE:\d+\n", "", str(raw), count=1)
            context_words = [
                self._normalize_pdf_word(word)
                for word in re.findall(word_re, re.sub(r"\S*[ÃÄÅ�]\S*", " ", raw_text))
            ]
            stop_words = {"pdf", "sayfa", "sekil", "şekil", "cizelge", "çizelge", "problem"}
            context_words = [word for word in context_words if len(word) >= 3 and word not in stop_words]
            if len(context_words) >= 3:
                candidates.append(context_words[:10])
                for index in range(0, max(len(context_words) - 3, 0)):
                    slice_words = context_words[index:index + 5]
                    if len(slice_words) >= 3:
                        candidates.append(slice_words)
            for token in re.findall(r"\S*[ÃÄÅ�]\S*", raw_text):
                normalized = self._normalize_pdf_word(token)
                if len(normalized) >= 4:
                    candidates.append([normalized])
            if candidates:
                candidates.append([
                    self._normalize_pdf_word(token)
                    for token in re.findall(r"\S*[ÃÄÅ�]\S*", raw_text)
                    if len(self._normalize_pdf_word(token)) >= 4
                ])
                unique = []
                seen = set()
                for candidate in candidates:
                    candidate = [word for word in candidate if word]
                    key = tuple(candidate)
                    if candidate and key not in seen:
                        seen.add(key)
                        unique.append(candidate)
                return unique
        if "Art arda noktalama" in message:
            for match in re.finditer(rf"({word_re})([!?.,;:]{{2,}})({word_re})?", text):
                before = self._normalize_pdf_word(match.group(1))
                after = self._normalize_pdf_word(match.group(3) or "")
                if before and after:
                    candidates.append([before, after])
                    candidates.append(["".join([before, after])])
                elif before:
                    candidates.append([before])
        if "Noktalama işaretinden sonra" in message:
            for cluster in re.finditer(rf"{word_re}(?:[,.;:!?]{word_re})+", text):
                parts = [self._normalize_pdf_word(word) for word in re.findall(word_re, cluster.group(0))]
                parts = [part for part in parts if part]
                if len(parts) >= 2:
                    candidates.append(["".join(parts)])
                    candidates.append(parts)
            for match in re.finditer(rf"({word_re})([,.;:!?])(?=({word_re}))", text):
                before = self._normalize_pdf_word(match.group(1))
                after = self._normalize_pdf_word(match.group(3))
                if before and after:
                    if before in {"prof", "dr", "doc", "doç"} or after in {"dr", "prof"}:
                        continue
                    candidates.append([before, after])
                    start = max(0, match.start() - 70)
                    end = min(len(text), match.end() + 70)
                    window_words = [self._normalize_pdf_word(word) for word in re.findall(word_re, text[start:end])]
                    window_words = [word for word in window_words if len(word) > 1]
                    if len(window_words) >= 3:
                        candidates.append(window_words[:7])
        elif "Noktalama işaretinden önce" in message:
            command_contexts = re.finditer(
                r"(.{0,180}?)(\\(?:cite[tp]?|parencite|textcite|autocite|ref)\{[^{}]*\})(?=\s*[,.;:!?]|\s|$)",
                str(raw),
                re.I,
            )
            for command_context in command_contexts:
                before_words = [
                    self._normalize_pdf_word(word)
                    for word in re.findall(word_re, yazim_denetimi.strip_latex(command_context.group(1)))
                ]
                before_words = [word for word in before_words if len(word) > 1]
                if len(before_words) >= 2:
                    candidates.append(before_words[-8:])
                    candidates.append(before_words[-5:])
            for match in re.finditer(rf"({word_re})\s+([,.;:!?])", text):
                before = self._normalize_pdf_word(match.group(1))
                if before:
                    if before in {"kaynak", "oge"}:
                        weak_candidates.append([before])
                    else:
                        candidates.append([before])
        elif "yinelenen sözcük" in message:
            match = re.search(rf"\b({word_re})\s+\1\b", text, re.I)
            if match:
                word = self._normalize_pdf_word(match.group(1))
                candidates.append([word, word])
                candidates.append([word])
        plain_words = [self._normalize_pdf_word(word) for word in re.findall(word_re, text)]
        plain_words = [word for word in plain_words if len(word) > 1]
        if plain_words:
            candidates.append(plain_words[:8])
            for index in range(0, max(len(plain_words) - 4, 0)):
                slice_words = plain_words[index:index + 5]
                if any(len(word) >= 7 for word in slice_words):
                    candidates.append(slice_words)
        candidates.extend(weak_candidates)
        unique = []
        seen = set()
        for candidate in candidates:
            candidate = [word for word in candidate if word]
            key = tuple(candidate)
            if candidate and key not in seen:
                seen.add(key)
                unique.append(candidate)
        return unique

    def locate_findings_with_synctex(self, findings, review_workdir, pdf_pages):
        pdf_path = Path(review_workdir) / "tez.pdf"
        locations = []
        for rel, number, _message, _raw in findings:
            if str(rel) == "__pdf_unicode__":
                locations.append(None)
                continue
            source_path = Path(review_workdir) / rel
            location = self._synctex_location(source_path, number, pdf_path)
            if location and 0 <= location["page"] < len(pdf_pages):
                locations.append(location)
            else:
                locations.append(None)
        return locations

    def _synctex_location(self, source_path, line_number, pdf_path):
        if not shutil.which("synctex") or not source_path.exists() or not pdf_path.exists():
            return None
        result = subprocess.run(
            ["synctex", "view", "-i", f"{line_number}:1:{source_path}", "-o", str(pdf_path)],
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=str(pdf_path.parent),
        )
        if result.returncode != 0:
            return None
        records = []
        current = {}
        for raw_line in result.stdout.splitlines():
            line = raw_line.strip()
            if not line:
                if current:
                    records.append(current)
                    current = {}
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                current[key.strip().lower()] = value.strip()
        if current:
            records.append(current)
        best = None
        for record in records:
            try:
                page = int(float(record.get("page", "0"))) - 1
                x = float(record.get("x", record.get("h", "0")))
                y = float(record.get("y", record.get("v", "0")))
                width = max(float(record.get("width", "0") or 0), 80.0)
                height = max(float(record.get("height", "0") or 0), 12.0)
            except ValueError:
                continue
            if page >= 0 and (best is None or y < best["y0"]):
                best = {"page": page, "x0": x, "y0": y, "x1": x + width, "y1": y + height}
        return best

    def _find_pdf_word_sequence(self, pdf_pages, query, search_start=0, exact_page=False, allow_single_fallback=True):
        if not query:
            return None
        if exact_page:
            page_order = [search_start] if 0 <= search_start < len(pdf_pages) else []
        else:
            page_order = list(range(search_start, len(pdf_pages))) + list(range(0, min(search_start, len(pdf_pages))))
        min_len = min(len(query), 6)
        for size in range(min_len, 1, -1):
            for query_index in range(0, len(query) - size + 1):
                needle = query[query_index:query_index + size]
                found = self._find_pdf_words(pdf_pages, page_order, needle)
                if found:
                    return found
        if allow_single_fallback:
            for word in sorted({word for word in query if len(word) >= 5}, key=len, reverse=True):
                found = self._find_pdf_words(pdf_pages, page_order, [word])
                if found:
                    return found
        return None

    def _find_pdf_words(self, pdf_pages, page_order, needle):
        size = len(needle)
        for page_index in page_order:
            words = pdf_pages[page_index]["words"]
            haystack = [word["norm"] for word in words]
            for index in range(0, max(len(haystack) - size + 1, 0)):
                joined_haystack = "".join(haystack[index:index + size])
                joined_needle = "".join(needle)
                single_word_match = size > 1 and index < len(haystack) and joined_needle in haystack[index]
                if haystack[index:index + size] == needle or joined_haystack == joined_needle or single_word_match:
                    match_len = 1 if single_word_match else size
                    match = words[index:index + match_len]
                    return {
                        "page": page_index,
                        "x0": min(word["x0"] for word in match),
                        "y0": min(word["y0"] for word in match),
                        "x1": max(word["x1"] for word in match),
                        "y1": max(word["y1"] for word in match),
                    }
        return None

    def _expand_pdf_line_location(self, location, pdf_pages):
        if not location or not (0 <= location["page"] < len(pdf_pages)):
            return location
        words = pdf_pages[location["page"]]["words"]
        line_words = [
            word for word in words
            if abs(word["y0"] - location["y0"]) <= 3.5 or abs(word["y1"] - location["y1"]) <= 3.5
        ]
        if not line_words:
            return location
        return {
            "page": location["page"],
            "x0": min(word["x0"] for word in line_words),
            "y0": min(word["y0"] for word in line_words),
            "x1": max(word["x1"] for word in line_words),
            "y1": max(word["y1"] for word in line_words),
        }

    def _source_caption_block(self, review_workdir, rel, line_number):
        source_path = Path(review_workdir) / rel
        if not source_path.exists():
            return None
        lines = yazim_denetimi.read_text(source_path).splitlines()
        index = max(int(line_number) - 1, 0)
        if index >= len(lines) or "\\caption" not in lines[index]:
            return None
        start = index
        block_lines = [lines[index]]
        balance = lines[index].count("{") - lines[index].count("}")
        look = index + 1
        while balance > 0 and look < min(len(lines), index + 10):
            block_lines.append(lines[look])
            balance += lines[look].count("{") - lines[look].count("}")
            look += 1
        label = None
        for raw in block_lines + lines[look:min(len(lines), look + 8)]:
            match = re.search(r"\\label\{([^{}]+)\}", raw)
            if match:
                label = match.group(1)
                break
        env = None
        for back in range(index, max(-1, index - 80), -1):
            if "\\begin{table" in lines[back] or "\\begin{longtable" in lines[back]:
                env = "table"
                break
            if "\\begin{figure" in lines[back]:
                env = "figure"
                break
        caption_text = yazim_denetimi.strip_latex(" ".join(block_lines))
        number = None
        kind = env
        if label:
            for aux_path in Path(review_workdir).glob("*.aux"):
                aux_text = yazim_denetimi.read_text(aux_path)
                aux_match = re.search(rf"\\newlabel\{{{re.escape(label)}\}}\{{\{{([^{{}}]+)\}}\{{[^{{}}]*\}}.*?\{{([^{{}}.]+)\.", aux_text)
                if aux_match:
                    number = aux_match.group(1)
                    kind = aux_match.group(2) or kind
                    break
        return {
            "kind": kind,
            "number": number,
            "caption_text": caption_text,
            "label": label,
        }

    def locate_caption_source_in_pdf(self, finding, review_workdir, pdf_pages, preferred_page=None):
        rel, number, _message, _raw = finding
        info = self._source_caption_block(review_workdir, rel, number)
        if not info:
            return None
        words = [
            self._normalize_pdf_word(word)
            for word in re.findall(r"[\wçğıöşüÇĞİÖŞÜâîûÂÎÛ'-]+", info["caption_text"])
        ]
        stop_words = {"icin", "için", "ve", "ile", "tam", "olan", "the", "and", "for"}
        words = [word for word in words if len(word) >= 3 and word not in stop_words]
        candidates = []
        kind = info.get("kind")
        object_words = ["cizelge", "tablo", "table"] if kind == "table" else ["sekil", "figure"]
        normalized_number = self._normalize_pdf_word(info.get("number") or "")
        if normalized_number:
            for object_word in object_words:
                candidates.append([object_word, normalized_number])
            if words:
                candidates.append([normalized_number] + words[:5])
        if len(words) >= 3:
            candidates.append(words[:8])
            for index in range(0, max(len(words) - 3, 0)):
                candidates.append(words[index:index + 5])
        page_order = []
        if preferred_page is not None and 0 <= preferred_page < len(pdf_pages):
            # SyncTeX may point to a nearby float/table block instead of the
            # final caption line, especially with [ptbh] placements. Search a
            # wider neighbourhood before falling back to the whole document.
            page_order.extend(range(max(0, preferred_page - 5), min(len(pdf_pages), preferred_page + 6)))
        body_pages = [index for index in range(len(pdf_pages)) if index >= 10 and index not in page_order]
        front_pages = [index for index in range(len(pdf_pages)) if index < 10 and index not in page_order]
        page_order.extend(body_pages)
        page_order.extend(front_pages)
        for candidate in candidates:
            candidate = [word for word in candidate if word]
            if len(candidate) < 2:
                continue
            found = self._find_pdf_words(pdf_pages, page_order, candidate)
            if found:
                return self._expand_pdf_line_location(found, pdf_pages)
        return None

    def edit_writing_review_settings(self, parent=None, on_saved=None):
        workdir = self.template_dir
        colors = THEMES[self.theme_var.get()]
        settings = yazim_denetimi.load_review_settings(workdir)
        window = tk.Toplevel(parent or self)
        window.title("Yazım Denetimi Sözlüğü")
        window.geometry("820x520")
        window.minsize(680, 420)
        window.configure(bg=colors["bg"])
        window.columnconfigure(0, weight=1)
        window.columnconfigure(1, weight=1)
        window.rowconfigure(1, weight=1)

        ttk.Label(
            window,
            text="Kişisel sözlük ve yok say listesi",
            font=("Segoe UI", 11, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(12, 6))

        words_frame = ttk.Frame(window)
        words_frame.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=6)
        words_frame.columnconfigure(0, weight=1)
        words_frame.rowconfigure(2, weight=1)
        ttk.Label(words_frame, text="Kişisel sözlük").grid(row=0, column=0, sticky="w")
        add_row = ttk.Frame(words_frame)
        add_row.grid(row=1, column=0, sticky="ew", pady=(5, 6))
        add_row.columnconfigure(1, weight=1)
        lang_var = tk.StringVar(value="tr")
        ttk.Combobox(add_row, textvariable=lang_var, values=["tr", "en"], state="readonly", width=5).grid(row=0, column=0, sticky="w")
        word_var = tk.StringVar(value="")
        word_entry = ttk.Entry(add_row, textvariable=word_var)
        word_entry.grid(row=0, column=1, sticky="ew", padx=6)
        word_list = tk.Listbox(words_frame, font=("Segoe UI", 9), activestyle="none")
        word_list.grid(row=2, column=0, sticky="nsew")
        word_scroll = ttk.Scrollbar(words_frame, orient="vertical", command=word_list.yview)
        word_scroll.grid(row=2, column=1, sticky="ns")
        word_list.configure(yscrollcommand=word_scroll.set)

        ignore_frame = ttk.Frame(window)
        ignore_frame.grid(row=1, column=1, sticky="nsew", padx=(6, 12), pady=6)
        ignore_frame.columnconfigure(0, weight=1)
        ignore_frame.rowconfigure(1, weight=1)
        ttk.Label(ignore_frame, text="Yok sayılan bulgular").grid(row=0, column=0, sticky="w")
        ignore_list = tk.Listbox(ignore_frame, font=("Segoe UI", 9), activestyle="none")
        ignore_list.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        ignore_y = ttk.Scrollbar(ignore_frame, orient="vertical", command=ignore_list.yview)
        ignore_y.grid(row=1, column=1, sticky="ns", pady=(5, 0))
        ignore_x = ttk.Scrollbar(ignore_frame, orient="horizontal", command=ignore_list.xview)
        ignore_x.grid(row=2, column=0, sticky="ew")
        ignore_list.configure(yscrollcommand=ignore_y.set, xscrollcommand=ignore_x.set)

        status_var = tk.StringVar(value=str(workdir / yazim_denetimi.REVIEW_SETTINGS_FILE))

        def current_words():
            user_words = settings.setdefault("user_words", {})
            return user_words.setdefault(lang_var.get(), [])

        def refresh_words():
            word_list.delete(0, "end")
            for item in current_words():
                word_list.insert("end", item)

        def refresh_ignored():
            ignore_list.delete(0, "end")
            for item in settings.get("ignored_findings", []):
                ignore_list.insert("end", item)

        def save_settings(message="Kaydedildi."):
            yazim_denetimi.save_review_settings(workdir, settings)
            status_var.set(message)
            if callable(on_saved):
                on_saved()

        def add_word():
            clean = word_var.get().strip().strip("'’")
            if not clean:
                return
            words = current_words()
            if clean.casefold() not in {item.casefold() for item in words}:
                words.append(clean)
                words.sort(key=str.casefold)
                save_settings(f"Kişisel sözlüğe eklendi: {clean}")
            word_var.set("")
            refresh_words()

        def remove_word():
            selection = word_list.curselection()
            if not selection:
                return
            words = current_words()
            index = selection[0]
            if index < len(words):
                removed = words.pop(index)
                save_settings(f"Kişisel sözlükten silindi: {removed}")
                refresh_words()

        def remove_ignored():
            selection = ignore_list.curselection()
            if not selection:
                return
            ignored = settings.setdefault("ignored_findings", [])
            index = selection[0]
            if index < len(ignored):
                ignored.pop(index)
                save_settings("Yok sayma kuralı silindi.")
                refresh_ignored()

        def clear_ignored():
            if not settings.get("ignored_findings"):
                return
            if not messagebox.askyesno("Yok say listesini temizle", "Tüm yok sayma kuralları silinsin mi?", parent=window):
                return
            settings["ignored_findings"] = []
            save_settings("Yok say listesi temizlendi.")
            refresh_ignored()

        ttk.Button(add_row, text="Ekle", image=self._button_icon("save"), compound="left", style="Soft.TButton", command=add_word).grid(row=0, column=2, sticky="e")
        word_entry.bind("<Return>", lambda _event: add_word())
        lang_var.trace_add("write", lambda *_args: refresh_words())

        word_buttons = ttk.Frame(words_frame)
        word_buttons.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(word_buttons, text="Seçileni Sil", image=self._button_icon("clean"), compound="left", style="Soft.TButton", command=remove_word).pack(side="left")

        ignore_buttons = ttk.Frame(ignore_frame)
        ignore_buttons.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(ignore_buttons, text="Seçileni Sil", image=self._button_icon("clean"), compound="left", style="Soft.TButton", command=remove_ignored).pack(side="left")
        ttk.Button(ignore_buttons, text="Tümünü Temizle", image=self._button_icon("clean"), compound="left", style="Soft.TButton", command=clear_ignored).pack(side="left", padx=6)

        bottom = ttk.Frame(window)
        bottom.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=(4, 12))
        ttk.Label(bottom, textvariable=status_var).pack(side="left", fill="x", expand=True)
        ttk.Button(bottom, text="Kapat", style="Soft.TButton", command=window.destroy).pack(side="right")

        refresh_words()
        refresh_ignored()
        word_entry.focus_set()

    def open_writing_review_window(self):
        workdir = self.template_dir
        colors = THEMES[self.theme_var.get()]
        window = tk.Toplevel(self)
        window.title("Yazım Denetimi ve PDF Önizleme")
        window.geometry("1320x740")
        window.minsize(980, 620)
        window.resizable(True, True)
        window.configure(bg=colors["bg"])
        window.columnconfigure(0, weight=3)
        window.columnconfigure(1, weight=4)
        window.rowconfigure(1, weight=1)
        window.pdf_images = []
        window.pdf_highlight = None
        window.pdf_locations = []
        window.pdf_zoom = 1.15
        window.selected_finding_index = None
        window.pdf_page_paths = []
        window.review_running = False
        window.suggestion_popup = None
        window.resolved_finding_keys = set()
        window.suggestion_cache = {}
        window.bind("<Button-1>", lambda _event: window.lift(), add="+")

        def set_scrollbar(scrollbar, first, last):
            scrollbar.set(first, last)
            try:
                scrollbar.state(["disabled"] if float(first) <= 0.0 and float(last) >= 1.0 else ["!disabled"])
            except (tk.TclError, ValueError):
                pass

        header = ttk.Frame(window)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(10, 6))
        header.columnconfigure(1, weight=1)
        title = ttk.Label(header, text="Yazım Denetimi", font=("Segoe UI", 13, "bold"))
        title.grid(row=0, column=0, sticky="w")
        status_var = tk.StringVar(value="İşaretli PDF hazırlanıyor...")
        ttk.Label(header, textvariable=status_var).grid(row=0, column=1, sticky="e")

        left = tk.Frame(window, bg=colors["panel"], highlightbackground=colors["soft_line"], highlightthickness=1, bd=0)
        left.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=(0, 10))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)
        source_title_var = tk.StringVar(value="TeX kaynak kodu")
        ttk.Label(left, textvariable=source_title_var).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 4))

        source_frame = ttk.Frame(left)
        source_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 8))
        source_frame.columnconfigure(1, weight=1)
        source_frame.rowconfigure(0, weight=1)
        line_numbers = tk.Text(source_frame, width=5, padx=4, takefocus=0, borderwidth=0, state="disabled", wrap="none", font=("Consolas", 9))
        line_numbers.grid(row=0, column=0, sticky="ns")
        source_text = tk.Text(source_frame, wrap="none", font=("Consolas", 9), undo=True)
        source_text.grid(row=0, column=1, sticky="nsew")
        source_scroll = ttk.Scrollbar(source_frame, orient="vertical", command=lambda *args: (source_text.yview(*args), line_numbers.yview(*args)))
        source_scroll.grid(row=0, column=2, sticky="ns")
        def sync_source_scroll(first, last):
            set_scrollbar(source_scroll, first, last)
            line_numbers.yview_moveto(first)
        source_text.configure(yscrollcommand=sync_source_scroll)
        x_scroll = ttk.Scrollbar(source_frame, orient="horizontal", command=source_text.xview)
        x_scroll.grid(row=1, column=1, sticky="ew")
        source_text.configure(xscrollcommand=lambda first, last: set_scrollbar(x_scroll, first, last))

        right = tk.Frame(window, bg=colors["panel"], highlightbackground=colors["soft_line"], highlightthickness=1, bd=0)
        right.grid(row=1, column=1, sticky="nsew", padx=(6, 12), pady=(0, 10))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        pdf_header = ttk.Frame(right)
        pdf_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))
        pdf_header.columnconfigure(0, weight=1)
        ttk.Label(pdf_header, text="PDF önizleme").grid(row=0, column=0, sticky="w")
        zoom_label_var = tk.StringVar(value="115%")
        ttk.Button(pdf_header, text="-", width=3, style="Tiny.TButton", command=lambda: change_zoom(-0.15)).grid(row=0, column=1, padx=(4, 0))
        ttk.Label(pdf_header, textvariable=zoom_label_var).grid(row=0, column=2, padx=4)
        ttk.Button(pdf_header, text="+", width=3, style="Tiny.TButton", command=lambda: change_zoom(0.15)).grid(row=0, column=3)
        pdf_canvas = tk.Canvas(right, bg=colors["alt"], highlightthickness=0)
        pdf_canvas.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        pdf_scroll = ttk.Scrollbar(right, orient="vertical", command=pdf_canvas.yview)
        pdf_scroll.grid(row=1, column=1, sticky="ns", pady=(0, 10))
        pdf_xscroll = ttk.Scrollbar(right, orient="horizontal", command=pdf_canvas.xview)
        pdf_xscroll.grid(row=2, column=0, sticky="ew", padx=10)
        pdf_canvas.configure(
            yscrollcommand=lambda first, last: set_scrollbar(pdf_scroll, first, last),
            xscrollcommand=lambda first, last: set_scrollbar(pdf_xscroll, first, last),
        )
        findings_label_var = tk.StringVar(value="PDF işaretleri hazırlanıyor...")
        findings_controls = ttk.Frame(right)
        findings_controls.grid(row=3, column=0, sticky="ew", padx=10)
        findings_controls.columnconfigure(0, weight=1)
        ttk.Label(findings_controls, textvariable=findings_label_var).grid(row=0, column=0, sticky="w")
        filter_var = tk.StringVar(value="Tümü")
        filter_combo = ttk.Combobox(
            findings_controls,
            textvariable=filter_var,
            values=["Tümü", "Kılavuz yazım kuralı", "Sözlük uyarıları", "Noktalama", "Yer tutucu", "TeX ön kontrol", "PDF karakter bozulması", "İçerik", "Diğer"],
            state="readonly",
            width=24,
        )
        filter_combo.grid(row=0, column=1, sticky="e", padx=(8, 0))
        findings_frame = ttk.Frame(right)
        findings_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=(4, 10))
        findings_frame.columnconfigure(0, weight=1)
        findings_list = ttk.Treeview(
            findings_frame,
            columns=("location", "category", "summary"),
            show="headings",
            height=5,
            selectmode="browse",
        )
        findings_list.heading("location", text="Yer")
        findings_list.heading("category", text="Tür")
        findings_list.heading("summary", text="Kısa açıklama")
        findings_list.column("location", width=145, minwidth=95, stretch=False)
        findings_list.column("category", width=135, minwidth=95, stretch=False)
        findings_list.column("summary", width=360, minwidth=180, stretch=True)
        findings_list.grid(row=0, column=0, sticky="ew")
        findings_scroll = ttk.Scrollbar(findings_frame, orient="vertical", command=findings_list.yview)
        findings_scroll.grid(row=0, column=1, sticky="ns")
        findings_xscroll = ttk.Scrollbar(findings_frame, orient="horizontal", command=findings_list.xview)
        findings_xscroll.grid(row=1, column=0, sticky="ew")
        findings_list.configure(
            yscrollcommand=lambda first, last: set_scrollbar(findings_scroll, first, last),
            xscrollcommand=lambda first, last: set_scrollbar(findings_xscroll, first, last),
        )
        finding_detail = tk.Text(
            findings_frame,
            height=4,
            wrap="word",
            font=("Segoe UI", 9),
            bg=colors["input_bg"],
            fg=colors["text_fg"],
            relief="flat",
            padx=8,
            pady=6,
        )
        finding_detail.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        finding_detail.configure(state="disabled")

        def sync_line_numbers(_event=None):
            line_numbers.configure(state="normal")
            line_numbers.delete("1.0", "end")
            end_line = int(source_text.index("end-1c").split(".")[0])
            line_numbers.insert("1.0", "\n".join(str(i) for i in range(1, end_line + 1)))
            line_numbers.configure(state="disabled")

        current_source = {"path": None, "dirty": False, "loading": False}

        def refresh_source_title():
            path = current_source.get("path")
            if path:
                try:
                    rel_name = Path(path).relative_to(workdir)
                except ValueError:
                    rel_name = Path(path).name
                marker = " *" if current_source.get("dirty") else ""
                source_title_var.set(f"TeX kaynak kodu - {rel_name}{marker}")

        def on_source_modified(_event=None):
            if source_text.edit_modified():
                if not current_source.get("loading") and current_source.get("path"):
                    current_source["dirty"] = True
                    refresh_source_title()
                source_text.edit_modified(False)
            sync_line_numbers()

        def save_current_source(show_status=True):
            path = current_source.get("path")
            if not path:
                if show_status:
                    status_var.set("Kaydedilecek TeX dosyası seçili değil.")
                return False
            Path(path).write_text(source_text.get("1.0", "end-1c"), encoding="utf-8")
            current_source["dirty"] = False
            refresh_source_title()
            if show_status:
                status_var.set(f"Kaydedildi: {Path(path).name}")
            return True

        def undo_source_edit():
            try:
                source_text.edit_undo()
                source_text.edit_modified(True)
                status_var.set("Geri alındı.")
            except tk.TclError:
                status_var.set("Geri alınacak değişiklik yok.")

        def redo_source_edit():
            try:
                source_text.edit_redo()
                source_text.edit_modified(True)
                status_var.set("Yinelendi.")
            except tk.TclError:
                status_var.set("Yinelenecek değişiklik yok.")

        def issue_source_span(raw, message):
            raw = str(raw or "")
            for token in re.findall(r"`([^`]+)`", str(message or "")):
                if not token:
                    continue
                start = raw.casefold().find(token.casefold())
                if start >= 0:
                    return start, start + len(token)
            if "Örnek/yer tutucu" in str(message) or "Örnek/placeholder" in str(message):
                for token in yazim_denetimi.PLACEHOLDERS:
                    start = raw.casefold().find(token.casefold())
                    if start >= 0:
                        return start, start + len(token)
            for pattern in yazim_denetimi.issue_patterns_for_message(str(message or "")):
                match = re.search(pattern, raw, re.I)
                if match:
                    return match.start(), match.end()
            return None

        def finding_key(rel, number, message, raw):
            token_match = re.search(r"`([^`]+)`", str(message or ""))
            token = token_match.group(1).casefold() if token_match else ""
            if not token:
                span = issue_source_span(raw, message)
                token = str(raw or "")[span[0]:span[1]].casefold() if span else str(message or "").casefold()
            return str(rel), int(number), token

        def center_source_on(line, column=0):
            source_text.update_idletasks()
            end_line = max(int(source_text.index("end-1c").split(".")[0]), 1)
            target_line = max(int(line or 1), 1)
            target_column = max(int(column or 0), 0)
            visible_lines = max(int(source_text.winfo_height() / max(tkfont.Font(font=source_text.cget("font")).metrics("linespace"), 1)), 1)
            source_text.yview_moveto(max(target_line - visible_lines // 2, 0) / max(end_line, 1))
            source_text.see(f"{target_line}.{target_column}")
            try:
                raw_line = source_text.get(f"{target_line}.0", f"{target_line}.end")
                char_width = max(tkfont.Font(font=source_text.cget("font")).measure("0"), 1)
                visible_cols = max(int(source_text.winfo_width() / char_width), 1)
                start_col = max(target_column - max(visible_cols // 3, 4), 0)
                source_text.xview_moveto(start_col / max(len(raw_line), visible_cols, 1))
            except tk.TclError:
                pass
            line_numbers.yview_moveto(source_text.yview()[0])

        def tag_line_findings(rel_for_key, line, selected_message=None, selected_raw=None):
            current_line_raw = source_text.get(f"{line}.0", f"{line}.end")
            selected_key = finding_key(rel_for_key, line, selected_message, selected_raw) if selected_message is not None else None
            first_start = None
            for rel, number, message, raw in current_findings:
                if str(rel) != str(rel_for_key) or int(number) != int(line):
                    continue
                if finding_key(rel, number, message, raw) in window.resolved_finding_keys:
                    continue
                span = issue_source_span(current_line_raw, message) or issue_source_span(raw, message)
                if not span:
                    continue
                start, end = span
                tag = "active_issue_token" if finding_key(rel, number, message, raw) == selected_key else "other_issue_token"
                source_text.tag_add(tag, f"{line}.{start}", f"{line}.{end}")
                if first_start is None:
                    first_start = start
                if tag == "active_issue_token":
                    first_start = start
            source_text.tag_raise("other_issue_token")
            source_text.tag_raise("active_issue_token")
            return first_start

        def load_source(path, line=None, message=None, raw=None, recenter=True):
            same_open_source = current_source.get("path") and Path(current_source["path"]) == Path(path)
            if current_source.get("dirty") and current_source.get("path") and not same_open_source:
                save_current_source(show_status=False)
            if same_open_source:
                source_text.tag_remove("active_issue", "1.0", "end")
                source_text.tag_remove("active_issue_token", "1.0", "end")
                source_text.tag_remove("other_issue_token", "1.0", "end")
            else:
                content = yazim_denetimi.read_text(path) if path.exists() else ""
                current_source["path"] = path if path.exists() else None
                current_source["dirty"] = False
                current_source["loading"] = True
                if current_source["path"]:
                    refresh_source_title()
                else:
                    source_title_var.set(f"TeX kaynak kodu - {path.name}")
                source_text.delete("1.0", "end")
                source_text.insert("1.0", content)
                current_source["loading"] = False
                source_text.edit_modified(False)
            sync_line_numbers()
            source_text.tag_configure("active_issue", background="#FFF7CC" if self.theme_var.get() != "Koyu" else "#4D4319")
            source_text.tag_configure("active_issue_token", background="#D97706" if self.theme_var.get() != "Koyu" else "#F59E0B", foreground="#FFFFFF" if self.theme_var.get() != "Koyu" else "#111111")
            source_text.tag_configure("other_issue_token", background="#FBBF24" if self.theme_var.get() != "Koyu" else "#8A5A00", foreground="#111111" if self.theme_var.get() != "Koyu" else "#ffffff")
            source_text.tag_remove("sel", "1.0", "end")
            if line:
                rel_for_key = str(path.relative_to(workdir) if path.exists() else path)
                if finding_key(rel_for_key, line, message, raw) in window.resolved_finding_keys:
                    return
                source_text.tag_add("active_issue", f"{line}.0", f"{line}.end")
                start = tag_line_findings(rel_for_key, line, message, raw)
                if start is not None:
                    if recenter:
                        center_source_on(line, start)
                    else:
                        line_numbers.yview_moveto(source_text.yview()[0])
                    source_text.mark_set("insert", f"{line}.{start}")
                else:
                    if recenter:
                        center_source_on(line, 0)

        def show_pdf_only_finding(page, line, message, raw):
            raw = re.sub(r"^PDF_PAGE:\d+\n", "", str(raw), count=1)
            current_source["path"] = None
            current_source["dirty"] = False
            current_source["loading"] = True
            source_title_var.set("PDF bulgusu - TeX satırı otomatik eşleşmedi")
            source_text.delete("1.0", "end")
            source_text.insert(
                "1.0",
                "Bu bulgu PDF metninden yakalandı.\n\n"
                f"Sayfa: {page}\n"
                f"PDF satırı: {line}\n"
                f"Bulgu: {message}\n\n"
                "PDF'deki işaretli yeri kontrol edin. Kaynak satırı otomatik eşleşmezse metni TeX dosyalarında aratabilirsiniz.\n\n"
                f"PDF metni:\n{raw}\n",
            )
            current_source["loading"] = False
            source_text.edit_modified(False)
            sync_line_numbers()

        def resolve_unicode_source(pdf_text):
            def source_for_label(label):
                for name in yazim_denetimi.TEXT_FILES:
                    path = workdir / name
                    if not path.exists():
                        continue
                    lines = yazim_denetimi.read_text(path).splitlines()
                    for index, raw in enumerate(lines):
                        if f"\\label{{{label}}}" in raw:
                            for back in range(index, max(-1, index - 25), -1):
                                if "\\caption" in lines[back] or "\\textbf" in lines[back]:
                                    return Path(name), back + 1
                            return Path(name), index + 1
                return None

            numbered = re.search(r"(?:\S*ekil|\S*izelge)\s+(\d+\.\d+)", pdf_text, re.I)
            if numbered:
                number = numbered.group(1)
                kind = "figure" if "ekil" in numbered.group(0).casefold() else "table"
                label_match = None
                for aux_path in workdir.glob("*.aux"):
                    aux_text = yazim_denetimi.read_text(aux_path)
                    label_match = re.search(rf"\\newlabel\{{([^{{}}]+)\}}\{{\{{{re.escape(number)}\}}.*?\{{{kind}\.", aux_text)
                    if label_match:
                        break
                if label_match:
                    resolved = source_for_label(label_match.group(1))
                    if resolved:
                        return resolved
            list_page = re.search(r"\.{3,}\s*(\d+)\s*$", pdf_text)
            if list_page:
                page_number = list_page.group(1)
                labels = []
                for aux_path in workdir.glob("*.aux"):
                    aux_text = yazim_denetimi.read_text(aux_path)
                    kind_hint = "figure" if re.search(r"grafik|boyutlu|şekil|sekil", pdf_text, re.I) else None
                    for match in re.finditer(rf"\\newlabel\{{([^{{}}]+)\}}\{{\{{[^{{}}]+\}}\{{{page_number}\}}.*?\{{([^{{}}.]+)\.", aux_text):
                        if not kind_hint or match.group(2) == kind_hint:
                            labels.append(match.group(1))
                for label in labels:
                    resolved = source_for_label(label)
                    if resolved:
                        return resolved
            cleaned = re.sub(r"[ÃÄÅ�]+\S*", " ", pdf_text)
            cleaned = re.sub(r"\.{3,}\s*\d+\s*$", " ", cleaned)
            wanted = [
                self._normalize_pdf_word(word)
                for word in re.findall(r"[\wçğıöşüÇĞİÖŞÜâîûÂÎÛ'-]{4,}", cleaned)
            ]
            stop_words = {"sekil", "şekil", "cizelge", "çizelge", "problem", "icin", "için", "tam", "ve", "olan"}
            wanted = [word for word in wanted if word and word not in stop_words and not word.isdigit()]
            if not wanted:
                return None
            best = (0, None, None)
            for name in yazim_denetimi.TEXT_FILES:
                path = workdir / name
                if not path.exists():
                    continue
                lines = yazim_denetimi.read_text(path).splitlines()
                index = 0
                while index < len(lines):
                    raw = lines[index]
                    if "\\caption" not in raw and "\\textbf" not in raw and "\\section" not in raw:
                        index += 1
                        continue
                    start = index + 1
                    block_lines = [raw]
                    balance = raw.count("{") - raw.count("}")
                    look = index + 1
                    while balance > 0 and look < min(len(lines), index + 8):
                        block_lines.append(lines[look])
                        balance += lines[look].count("{") - lines[look].count("}")
                        look += 1
                    block_text = yazim_denetimi.strip_latex(" ".join(block_lines))
                    source_words = {
                        self._normalize_pdf_word(word)
                        for word in re.findall(r"[\wçğıöşüÇĞİÖŞÜâîûÂÎÛ'-]{4,}", block_text)
                    }
                    score = sum(1 for word in wanted if word in source_words)
                    if score > best[0]:
                        best = (score, Path(name), start)
                    index = max(look, index + 1)
            threshold = 2 if len(wanted) <= 4 else 3
            if best[0] >= threshold:
                return best[1], best[2]
            return None

        def select_finding(_event=None):
            selected_index = selected_finding_index_from_list()
            if selected_index is None:
                return
            if selected_index >= len(current_findings):
                return
            window.selected_finding_index = selected_index
            rel, number, _message, _raw = current_findings[selected_index]
            set_finding_detail(finding_location_text(rel, number), finding_category(_message), _message, _raw)
            location = window.pdf_locations[selected_index] if selected_index < len(window.pdf_locations) else None
            if location and getattr(window, "pdf_page_positions", None):
                draw_pdf_highlight(location)
                target_y = location.get("canvas_y0", window.pdf_page_positions[location["page"]][1])
                _x0, _y0, _x1, canvas_height = pdf_canvas.bbox("all") or (0, 0, 1, 1)
                pdf_canvas.yview_moveto(max(target_y - 140, 0) / max(canvas_height, 1))
            elif window.pdf_highlight:
                pdf_canvas.delete(window.pdf_highlight)
                window.pdf_highlight = None
            if str(rel) == "__pdf_unicode__":
                show_pdf_only_finding(number, 0, _message, _raw)
            else:
                load_source(workdir / rel, number, _message, _raw)
                window.after(250, show_selected_issue_suggestions)
            pdf_canvas.focus_set()

        def open_source_for_selected():
            index = selected_finding_index_from_list()
            if index is None:
                index = window.selected_finding_index
            if index is None or index >= len(current_findings):
                return
            rel, number, _message, _raw = current_findings[index]
            if str(rel) == "__pdf_unicode__":
                show_pdf_only_finding(number, 0, _message, _raw)
            else:
                load_source(workdir / rel, number, _message, _raw)
            source_text.focus_set()

        def clicked_issue_range(index):
            for tag in ("active_issue_token", "other_issue_token"):
                ranges = source_text.tag_ranges(tag)
                for start, end in zip(ranges[0::2], ranges[1::2]):
                    if source_text.compare(start, "<=", index) and source_text.compare(index, "<", end):
                        return str(start), str(end)
            return None

        def finding_index_for_range(start, end):
            line = int(str(source_text.index(start)).split(".", 1)[0])
            token = source_text.get(start, end).casefold()
            for index, (rel, number, message, raw) in enumerate(current_findings):
                if str(rel) == "__pdf_unicode__" or int(number) != line:
                    continue
                token_match = re.search(r"`([^`]+)`", str(message or ""))
                if token_match and token_match.group(1).casefold() == token:
                    return index
                current_line_raw = source_text.get(f"{number}.0", f"{number}.end")
                span = issue_source_span(current_line_raw, message) or issue_source_span(raw, message)
                if span and current_line_raw[span[0]:span[1]].casefold() == token:
                    return index
            return None

        def selected_issue_range_for_click(index):
            if window.selected_finding_index is None or window.selected_finding_index >= len(current_findings):
                return None
            rel, number, message, raw = current_findings[window.selected_finding_index]
            if str(rel) == "__pdf_unicode__":
                return None
            try:
                click_line = int(str(source_text.index(index)).split(".", 1)[0])
            except (tk.TclError, ValueError):
                return None
            if click_line != int(number):
                return None
            span = issue_source_span(raw, message)
            current_line_raw = source_text.get(f"{number}.0", f"{number}.end")
            span = issue_source_span(current_line_raw, message) or span
            if not span:
                return None
            start, end = span
            return f"{number}.{start}", f"{number}.{end}"

        def preserve_case(original, suggestion):
            if original.isupper():
                return suggestion.upper()
            if original[:1].isupper():
                return suggestion[:1].upper() + suggestion[1:]
            return suggestion

        def suggestions_for_issue(word, message, rel, default_language=None):
            suggestions = []
            for item in re.findall(r"Öneri:\s*`([^`]+)`", str(message or "")):
                suggestions.append(item)
            lang = yazim_denetimi.spelling_language_for_path(rel, default_language or "tr")
            try:
                dictionary = yazim_denetimi.load_dictionary(lang, workdir=workdir)
                for item in dictionary.suggest(word, limit=8):
                    suggestions.append(str(item))
                best = yazim_denetimi.spelling_suggestion(word, dictionary, cutoff=0.90, lang=lang)
                if best:
                    suggestions.append(best)
            except Exception:
                pass
            cleaned = []
            seen = {word.casefold()}
            for item in suggestions:
                item = str(item).strip()
                key = item.casefold()
                if item and key not in seen:
                    seen.add(key)
                    cleaned.append(preserve_case(word, item))
            return cleaned[:8]

        def cached_suggestions_for_issue(word, message, rel, number, raw, default_language=None):
            key = finding_key(rel, number, message, raw)
            if key in window.suggestion_cache:
                return window.suggestion_cache[key]
            suggestions = []
            for item in re.findall(r"Öneri:\s*`([^`]+)`", str(message or "")):
                suggestions.append(preserve_case(word, item))
            message_text = str(message or "")
            raw_word = str(word or "")
            if "Kılavuz yazım kuralı" in message_text:
                if "Kalın yazı" in message_text:
                    match = re.match(r"\\textbf\s*\{(.*)\}\s*$", raw_word, re.S)
                    if match:
                        suggestions.append(match.group(1))
                if "Altı çizili" in message_text:
                    match = re.match(r"\\underline\s*\{(.*)\}\s*$", raw_word, re.S)
                    if match:
                        suggestions.append(match.group(1))
                if "Noktalama işaretinden önce" in message_text:
                    suggestions.append(raw_word.strip())
                if "Noktalama işaretinden sonra" in message_text and raw_word in ",.;:!?":
                    suggestions.append(raw_word + " ")
            cleaned = []
            seen = {word.casefold()}
            for item in suggestions:
                item = str(item).strip()
                if item and item.casefold() not in seen:
                    seen.add(item.casefold())
                    cleaned.append(item)
            window.suggestion_cache[key] = cleaned[:8]
            return window.suggestion_cache[key]

        def mark_selected_finding_resolved(note="Düzeltildi; kaydedip önizleyin."):
            if window.selected_finding_index is not None and window.selected_finding_index < len(current_findings):
                rel, number, _message, _raw = current_findings[window.selected_finding_index]
                window.resolved_finding_keys.add(finding_key(rel, number, _message, _raw))
                refresh_findings_list(keep_selected=True)
                set_finding_detail(f"{rel}:{number}", "Düzeltildi", note)
            source_text.tag_remove("active_issue_token", "1.0", "end")
            source_text.tag_remove("active_issue", "1.0", "end")
            source_text.tag_remove("other_issue_token", "1.0", "end")
            if window.selected_finding_index is not None and window.selected_finding_index < len(current_findings):
                rel, number, _message, _raw = current_findings[window.selected_finding_index]
                remaining_start = tag_line_findings(rel, number)
                if remaining_start is not None:
                    source_text.tag_add("active_issue", f"{number}.0", f"{number}.end")

        def replace_issue_text(start, end, replacement):
            source_text.delete(start, end)
            source_text.insert(start, replacement)
            mark_selected_finding_resolved()
            current_source["dirty"] = True
            refresh_source_title()
            status_var.set("Düzeltme uygulandı. Kaydet veya Kaydet ve Önizle.")

        def add_issue_word_to_dictionary(word, rel, number, message, raw):
            lang = yazim_denetimi.spelling_language_for_path(rel, "en" if is_english_thesis_label(self.thesis_language_var.get()) else "tr")
            added = yazim_denetimi.add_user_word(workdir, word, lang=lang)
            close_suggestion_popup()
            if added:
                window.suggestion_cache.pop(finding_key(rel, number, message, raw), None)
                mark_selected_finding_resolved("Kişisel sözlüğe eklendi; kaydedip önizleyin.")
                status_var.set(f"Kişisel sözlüğe eklendi: {word}")
            else:
                status_var.set(f"Kelime kişisel sözlükte zaten var: {word}")

        def ignore_selected_issue(rel, number, message, raw):
            added = yazim_denetimi.add_ignored_finding(workdir, rel, number, message, raw)
            close_suggestion_popup()
            if added:
                mark_selected_finding_resolved("Yok sayıldı; kaydedip önizleyin.")
                status_var.set("Bu bulgu bundan sonra yok sayılacak.")
            else:
                mark_selected_finding_resolved("Zaten yok sayılıyor; kaydedip önizleyin.")
                status_var.set("Bu bulgu yok sayma listesinde zaten var.")

        def close_suggestion_popup():
            popup = getattr(window, "suggestion_popup", None)
            if popup and popup.winfo_exists():
                popup.destroy()
            window.suggestion_popup = None

        def show_issue_suggestions(event):
            if getattr(window, "suppress_suggestion_popup", False):
                return
            click_index = source_text.index(f"@{event.x},{event.y}")
            issue_range = clicked_issue_range(click_index) or selected_issue_range_for_click(click_index)
            if not issue_range or window.selected_finding_index is None or window.selected_finding_index >= len(current_findings):
                return
            clicked_finding_index = finding_index_for_range(*issue_range)
            if clicked_finding_index is not None and clicked_finding_index != window.selected_finding_index:
                window.selected_finding_index = clicked_finding_index
                select_list_row_for_finding(clicked_finding_index)
                rel, number, message, raw = current_findings[clicked_finding_index]
                load_source(workdir / rel, number, message, raw, recenter=False)
                current_line_raw = source_text.get(f"{number}.0", f"{number}.end")
                span = issue_source_span(current_line_raw, message) or issue_source_span(raw, message)
                if span:
                    source_text.mark_set("insert", f"{number}.{span[0]}")
                issue_range = clicked_issue_range(source_text.index(f"@{event.x},{event.y}")) or selected_issue_range_for_click(source_text.index(f"@{event.x},{event.y}"))
                if not issue_range:
                    return "break"
            rel, _number, message, _raw = current_findings[window.selected_finding_index]
            if str(rel) == "__pdf_unicode__":
                return
            if finding_key(rel, _number, message, _raw) in window.resolved_finding_keys:
                close_suggestion_popup()
                return "break"
            start, end = issue_range
            word = source_text.get(start, end).strip()
            if not word:
                return
            close_suggestion_popup()
            popup = tk.Frame(source_frame, bg=colors["soft_line"])
            window.suggestion_popup = popup
            body = tk.Frame(popup, bg=colors["panel"], highlightbackground=colors["accent"], highlightthickness=1, bd=0)
            body.pack(fill="both", expand=True, padx=1, pady=1)
            list_bg = colors["input_bg"] if self.theme_var.get() != "Koyu" else colors["alt"]
            fg = colors["text_fg"]
            default_language = "en" if is_english_thesis_label(self.thesis_language_var.get()) else "tr"

            def position_popup():
                source_text.update_idletasks()
                popup.update_idletasks()
                word_box = source_text.bbox(start)
                popup_w = popup.winfo_reqwidth()
                popup_h = popup.winfo_reqheight()
                if word_box:
                    x, y, _w, h = word_box
                    base_x = source_text.winfo_x()
                    base_y = source_text.winfo_y()
                    frame_w = max(source_frame.winfo_width(), source_text.winfo_width())
                    frame_h = max(source_frame.winfo_height(), source_text.winfo_height())
                    px = min(max(base_x + x, 4), max(frame_w - popup_w - 4, 4))
                    below_y = base_y + y + h + 10
                    above_y = base_y + y - popup_h - 10
                    if below_y + popup_h <= frame_h - 4:
                        py = below_y
                    else:
                        py = max(4, above_y)
                else:
                    px = min(max(source_text.winfo_x() + event.x + 8, 4), max(source_frame.winfo_width() - popup_w - 4, 4))
                    py = min(max(source_text.winfo_y() + event.y + 18, 4), max(source_frame.winfo_height() - popup_h - 4, 4))
                popup.place(x=int(px), y=int(py))
                popup.lift()

            def apply_suggestion(value):
                close_suggestion_popup()
                replace_issue_text(start, end, value)

            def manual_edit():
                close_suggestion_popup()
                source_text.focus_set()
                source_text.tag_remove("sel", "1.0", "end")
                source_text.mark_set("insert", start)
                source_text.tag_add("sel", start, end)

            def fill_popup(suggestions):
                if not popup.winfo_exists() or getattr(window, "suggestion_popup", None) is not popup:
                    return
                for child in body.winfo_children():
                    child.destroy()
                is_guideline = "Kılavuz yazım kuralı" in str(message or "")
                if suggestions:
                    for suggestion in suggestions:
                        item_text = f"Kuralı uygula: {suggestion}" if is_guideline else suggestion
                        item = tk.Label(body, text=item_text, anchor="w", bg=list_bg, fg=fg, padx=12, pady=5, font=("Segoe UI", 9))
                        item.pack(fill="x")
                        item.bind("<Enter>", lambda _event, w=item: w.configure(bg=colors["accent"], fg="#ffffff"))
                        item.bind("<Leave>", lambda _event, w=item: w.configure(bg=list_bg, fg=fg))
                        item.bind("<Button-1>", lambda _event, value=suggestion: apply_suggestion(value))
                else:
                    no_suggestion = "Bu kural otomatik düzeltilemiyor" if is_guideline else "Sözlük önerisi yok"
                    tk.Label(body, text=no_suggestion, anchor="w", bg=list_bg, fg=colors["muted"], padx=12, pady=5, font=("Segoe UI", 9)).pack(fill="x")
                tk.Frame(body, bg=colors["soft_line"], height=1).pack(fill="x", padx=6, pady=(4, 2))
                if "Sözlükte bulunmayan" in str(message or ""):
                    add_word = tk.Label(body, text="Sözlüğe ekle", anchor="w", bg=colors["panel"], fg=colors["accent"], padx=12, pady=6, font=("Segoe UI", 9, "bold"))
                    add_word.pack(fill="x")
                    add_word.bind("<Enter>", lambda _event: add_word.configure(bg=colors["alt"]))
                    add_word.bind("<Leave>", lambda _event: add_word.configure(bg=colors["panel"]))
                    add_word.bind("<Button-1>", lambda _event: add_issue_word_to_dictionary(word, rel, _number, message, _raw))
                ignore = tk.Label(body, text="Doğru, bunu yoksay", anchor="w", bg=colors["panel"], fg=colors["accent"], padx=12, pady=6, font=("Segoe UI", 9, "bold"))
                ignore.pack(fill="x")
                ignore.bind("<Enter>", lambda _event: ignore.configure(bg=colors["alt"]))
                ignore.bind("<Leave>", lambda _event: ignore.configure(bg=colors["panel"]))
                ignore.bind("<Button-1>", lambda _event: ignore_selected_issue(rel, _number, message, _raw))
                manual = tk.Label(body, text="Elle düzenle", anchor="w", bg=colors["panel"], fg=colors["accent"], padx=12, pady=6, font=("Segoe UI", 9, "bold"))
                manual.pack(fill="x")
                manual.bind("<Enter>", lambda _event: manual.configure(bg=colors["alt"]))
                manual.bind("<Leave>", lambda _event: manual.configure(bg=colors["panel"]))
                manual.bind("<Button-1>", lambda _event: manual_edit())
                popup.update_idletasks()
                position_popup()

            tk.Label(body, text="Öneriler hazırlanıyor...", anchor="w", bg=list_bg, fg=colors["muted"], padx=12, pady=6, font=("Segoe UI", 9)).pack(fill="x")
            tk.Frame(body, bg=colors["soft_line"], height=1).pack(fill="x", padx=6, pady=(4, 2))
            manual = tk.Label(body, text="Elle düzenle", anchor="w", bg=colors["panel"], fg=colors["accent"], padx=12, pady=6, font=("Segoe UI", 9, "bold"))
            manual.pack(fill="x")
            manual.bind("<Enter>", lambda _event: manual.configure(bg=colors["alt"]))
            manual.bind("<Leave>", lambda _event: manual.configure(bg=colors["panel"]))
            manual.bind("<Button-1>", lambda _event: manual_edit())

            popup.bind("<Escape>", lambda _event: close_suggestion_popup())
            position_popup()
            fill_popup(cached_suggestions_for_issue(word, message, rel, _number, _raw, default_language=default_language))
            return "break"

        def show_issue_suggestions_after_click(event):
            if getattr(window, "suggestion_popup", None):
                return
            return show_issue_suggestions(event)

        def show_selected_issue_suggestions(_event=None):
            ranges = source_text.tag_ranges("active_issue_token")
            if not ranges:
                return
            bbox = source_text.bbox(ranges[0])
            if not bbox:
                source_text.see(ranges[0])
                source_text.update_idletasks()
                bbox = source_text.bbox(ranges[0])
            if not bbox:
                return
            x, y, width, height = bbox
            fake_event = types.SimpleNamespace(
                x=x + max(width // 2, 2),
                y=y + max(height // 2, 2),
                x_root=source_text.winfo_rootx() + x + max(width // 2, 2),
                y_root=source_text.winfo_rooty() + y + max(height // 2, 2),
            )
            return show_issue_suggestions(fake_event)

        def change_zoom(delta):
            window.pdf_zoom = min(2.4, max(0.65, window.pdf_zoom + delta))
            zoom_label_var.set(f"{int(round(window.pdf_zoom * 100))}%")
            if window.pdf_page_paths:
                selected_index = window.selected_finding_index
                show_pdf_pages(window.pdf_page_paths)
                if selected_index is not None and select_list_row_for_finding(selected_index):
                    select_finding()

        def show_pdf_pages(pages):
            pdf_canvas.delete("all")
            window.pdf_images.clear()
            window.pdf_page_paths = list(pages)
            window.pdf_page_positions = []
            window.pdf_page_layouts = []
            window.pdf_highlight = None
            y = 14
            available_width = max(pdf_canvas.winfo_width() - 34, 420)
            for index, page in enumerate(pages, start=1):
                image = Image.open(page)
                base_ratio = min(1.0, available_width / image.width)
                ratio = base_ratio * window.pdf_zoom
                if ratio != 1:
                    image = image.resize((int(image.width * ratio), int(image.height * ratio)), Image.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                window.pdf_images.append(photo)
                x = max((available_width - image.width) // 2 + 12, 12)
                window.pdf_page_positions.append((index, y))
                pdf_canvas.create_text(16, y, text=f"Sayfa {index}", anchor="nw", fill=colors["muted"], font=("Segoe UI", 9, "bold"))
                y += 20
                window.pdf_page_layouts.append({"x": x, "y": y, "width": image.width, "height": image.height})
                pdf_canvas.create_rectangle(x - 1, y - 1, x + image.width + 1, y + image.height + 1, outline=colors["soft_line"], fill="#ffffff")
                pdf_canvas.create_image(x, y, image=photo, anchor="nw")
                y += image.height + 18
            pdf_canvas.configure(scrollregion=(0, 0, available_width + 40, y))

        def scroll_pdf(event):
            if event.delta:
                pdf_canvas.yview_scroll(int(-event.delta / 120), "units")
            return "break"

        def shift_scroll_pdf(event):
            if event.delta:
                pdf_canvas.xview_scroll(int(-event.delta / 120), "units")
            return "break"

        def draw_pdf_highlight(location):
            if window.pdf_highlight:
                pdf_canvas.delete(window.pdf_highlight)
                window.pdf_highlight = None
            page_index = location.get("page")
            if page_index is None or page_index >= len(window.pdf_page_layouts):
                return
            layout = window.pdf_page_layouts[page_index]
            page = window.pdf_pages_meta[page_index] if page_index < len(window.pdf_pages_meta) else None
            if not page or not page.get("width") or not page.get("height"):
                return
            sx = layout["width"] / page["width"]
            sy = layout["height"] / page["height"]
            pad = 3
            x0 = layout["x"] + location["x0"] * sx - pad
            y0 = layout["y"] + location["y0"] * sy - pad
            x1 = layout["x"] + location["x1"] * sx + pad
            y1 = layout["y"] + location["y1"] * sy + pad
            if y1 - y0 < 12:
                y1 = y0 + 12
            if x1 - x0 < 18:
                x1 = x0 + 18
            location["canvas_y0"] = y0
            window.pdf_highlight = pdf_canvas.create_rectangle(
                x0, y0, x1, y1,
                fill="",
                outline="#C17F00",
                width=3,
                tags=("pdf_highlight",),
            )
            pdf_canvas.tag_raise(window.pdf_highlight)

        button_bar = ttk.Frame(window)
        button_bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 12))
        update_pdf_button = ttk.Button(button_bar, text="Kaydet ve Önizle", image=self._button_icon("preview", "primary"), compound="left", style="Primary.TButton", command=lambda: build_review())
        update_pdf_button.pack(side="left")
        save_button = ttk.Button(button_bar, text="Kaydet", image=self._button_icon("save"), compound="left", style="Soft.TButton", command=lambda: save_current_source())
        save_button.pack(side="left", padx=(6, 0))
        ttk.Button(button_bar, text="Geri Al", image=self._button_icon("undo"), compound="left", style="Soft.TButton", command=undo_source_edit).pack(side="left", padx=(6, 0))
        ttk.Button(button_bar, text="Yinele", image=self._button_icon("redo"), compound="left", style="Soft.TButton", command=redo_source_edit).pack(side="left", padx=(6, 0))
        ttk.Button(button_bar, text="Sözlük", image=self._button_icon("spell"), compound="left", style="Soft.TButton", command=lambda: self.edit_writing_review_settings(window)).pack(side="left", padx=(6, 0))
        ttk.Button(button_bar, text="Rapor", image=self._button_icon("preview"), compound="left", style="Soft.TButton", command=lambda: os.startfile(workdir / "yazim-denetimi-raporu.md")).pack(side="left")
        ttk.Button(button_bar, text="Kapat", style="Soft.TButton", command=window.destroy).pack(side="right")

        current_findings = []
        displayed_finding_indices = []
        annotation_data = {}

        def finding_category(message):
            return yazim_denetimi.finding_category(message)

        def findings_summary(findings):
            counts = {}
            for _rel, _number, message, _raw in findings:
                category = finding_category(message)
                counts[category] = counts.get(category, 0) + 1
            order = ["Kılavuz yazım kuralı", "Sözlük uyarıları", "Noktalama", "Yer tutucu", "TeX ön kontrol", "PDF karakter bozulması", "İçerik", "Diğer"]
            return ", ".join(f"{name}: {counts[name]}" for name in order if counts.get(name))

        def filter_accepts_finding(finding):
            selected = filter_var.get() or "Tümü"
            return selected == "Tümü" or finding_category(finding[2]) == selected

        def clear_findings_table(message=""):
            findings_list.delete(*findings_list.get_children())
            set_finding_detail("", "", message)

        def set_finding_detail(location, category, message, raw=""):
            finding_detail.configure(state="normal")
            finding_detail.delete("1.0", "end")
            if message:
                prefix = f"{location} | {category}\n" if location or category else ""
                finding_detail.insert("1.0", f"{prefix}{message}")
                if raw:
                    finding_detail.insert("end", f"\n\nKaynak satır:\n{raw}")
            finding_detail.configure(state="disabled")

        def short_finding_message(message):
            value = re.sub(r"\s*Referans:.*?(?=\s+Öneri:|$)", "", str(message or ""))
            value = re.sub(r"\s*Öneri:.*$", "", value).strip()
            value = value.replace("Kılavuz yazım kuralı: ", "")
            return value[:150] + ("..." if len(value) > 150 else "")

        def finding_location_text(rel, number):
            if str(rel) == "__pdf_unicode__":
                return f"PDF s.{number}"
            return f"{Path(rel).name}:{number}"

        def select_list_row_for_finding(finding_index):
            iid = str(finding_index)
            if iid not in findings_list.get_children(""):
                return False
            findings_list.selection_set(iid)
            findings_list.focus(iid)
            findings_list.see(iid)
            return True

        def selected_finding_index_from_list():
            selection = findings_list.selection()
            if not selection:
                return None
            try:
                index = int(selection[0])
            except (TypeError, ValueError):
                return None
            if index not in displayed_finding_indices:
                return None
            return index

        def refresh_findings_list(select_first=False, keep_selected=True):
            nonlocal displayed_finding_indices
            previous_index = window.selected_finding_index if keep_selected else None
            displayed_finding_indices = [
                index for index, finding in enumerate(current_findings)
                if filter_accepts_finding(finding)
            ]
            findings_list.delete(*findings_list.get_children())
            for index in displayed_finding_indices:
                rel, number, message, _raw = current_findings[index]
                findings_list.insert(
                    "",
                    "end",
                    iid=str(index),
                    values=(finding_location_text(rel, number), finding_category(message), short_finding_message(message)),
                )
            if not current_findings:
                set_finding_detail("", "", "Bulgu yok. Otomatik ön denetim temiz görünüyor.")
            elif not displayed_finding_indices:
                set_finding_detail("", "", "Bu filtrede bulgu yok.")
            summary = findings_summary(current_findings)
            filter_note = "" if filter_var.get() == "Tümü" else f" ({filter_var.get()} filtresi)"
            findings_label_var.set(f"{len(current_findings)} bulgu{filter_note}. {summary}" if summary else f"{len(current_findings)} bulgu{filter_note}.")
            if previous_index is not None and select_list_row_for_finding(previous_index):
                return True
            if select_first and displayed_finding_indices:
                select_list_row_for_finding(displayed_finding_indices[0])
                return True
            return False

        def formatted_finding(rel, number, message):
            if str(rel) == "__pdf_unicode__":
                return f"PDF sayfa {number} - {message}"
            return f"{rel}:{number} - {message}"

        filter_combo.bind("<<ComboboxSelected>>", lambda _event: (refresh_findings_list(select_first=True, keep_selected=False), select_finding()))

        def cached_report_findings():
            report_path = workdir / "yazim-denetimi-raporu.md"
            if not report_path.exists():
                return []
            findings = []
            pending = None
            for line in yazim_denetimi.read_text(report_path).splitlines():
                match = re.match(r"- `([^`:]+):(\d+)` - (.+)", line)
                if match:
                    if pending:
                        findings.append(pending)
                    pending = [Path(match.group(1)), int(match.group(2)), match.group(3).strip(), ""]
                    continue
                raw_match = re.match(r"\s+- Metin: `(.+)`", line)
                if raw_match and pending:
                    pending[3] = raw_match.group(1)
            if pending:
                findings.append(pending)
            return [tuple(item) for item in findings]

        def report_is_fresh():
            report_path = workdir / "yazim-denetimi-raporu.md"
            if not report_path.exists():
                return False
            report_mtime = report_path.stat().st_mtime_ns
            settings_path = workdir / yazim_denetimi.REVIEW_SETTINGS_FILE
            if settings_path.exists() and settings_path.stat().st_mtime_ns > report_mtime:
                return False
            for name in yazim_denetimi.SIGNATURE_FILES:
                path = workdir / name
                if path.exists() and path.stat().st_mtime_ns > report_mtime:
                    return False
            return True

        def cached_annotation_from_report():
            report_path = workdir / "yazim-denetimi-raporu.md"
            if not report_path.exists():
                return {}
            data = {}
            for line in yazim_denetimi.read_text(report_path).splitlines():
                match = re.match(r"- Önizleme klasörü: `(.+)`", line)
                if match:
                    data["review_workdir"] = Path(match.group(1))
                match = re.match(r"- İşaretli PDF: `(.+)`", line)
                if match:
                    data["review_pdf"] = Path(match.group(1))
                match = re.match(r"- PDF içinde işaretlenen satır sayısı: (\d+)", line)
                if match:
                    data["annotated_count"] = int(match.group(1))
                match = re.match(r"- PDF içine güvenle işlenemeyen/raporda kalan satır sayısı: (\d+)", line)
                if match:
                    data["skipped_count"] = int(match.group(1))
                match = re.match(r"- Derleme çıkış kodu: (-?\d+)", line)
                if match:
                    data["return_code"] = int(match.group(1))
            if data.get("review_pdf") and Path(data["review_pdf"]).exists():
                data["review_workdir"] = data.get("review_workdir") or Path(data["review_pdf"]).parent
                data.setdefault("annotated_count", 0)
                data.setdefault("skipped_count", 0)
                data.setdefault("return_code", 0)
                data["reused"] = True
                return data
            return {}

        def is_pdf_annotation_finding(finding):
            rel, _number, message, _raw = finding
            message = str(message or "")
            return (
                str(rel) != "__pdf_unicode__"
                and not message.startswith("TeX ön kontrol:")
                and not message.startswith("PDF Unicode")
            )

        def unresolved_review_findings(findings):
            remaining = []
            for rel, number, message, raw in findings:
                if finding_key(rel, number, message, raw) in window.resolved_finding_keys:
                    continue
                remaining.append((Path(rel), int(number), message, raw))
            return remaining

        def annotation_findings_for_preview(findings):
            return [finding for finding in findings if is_pdf_annotation_finding(finding)]

        def choose_pdf_locations(findings, synctex_locations, text_locations):
            pdf_locations = []
            for finding, sync_loc, text_loc in zip(findings, synctex_locations, text_locations):
                rel, _number, message, _raw = finding
                source_resolved = str(rel) != "__pdf_unicode__"
                if "Ana metinde manuel dikey boşluk" in message:
                    pdf_locations.append(None)
                    continue
                if "PDF Unicode" in message and source_resolved:
                    caption_loc = self.locate_caption_source_in_pdf(
                        finding,
                        annotation_data.get("review_workdir", workdir),
                        window.pdf_pages_meta if getattr(window, "pdf_pages_meta", None) else [],
                        preferred_page=sync_loc["page"] if sync_loc else None,
                    )
                    pdf_locations.append(caption_loc or sync_loc or text_loc)
                elif "Kılavuz yazım kuralı" in message:
                    pdf_locations.append(text_loc)
                elif sync_loc and text_loc and abs(sync_loc["page"] - text_loc["page"]) >= 3:
                    pdf_locations.append(sync_loc)
                else:
                    pdf_locations.append(text_loc or sync_loc)
            return pdf_locations

        def apply_cached_report():
            nonlocal current_findings
            cached = cached_report_findings()
            if not cached:
                return False
            current_findings = cached
            window.pdf_locations = [None] * len(current_findings)
            window.suggestion_cache = {}
            first_source = next((workdir / rel for rel, _number, _message, _raw in current_findings if str(rel) != "__pdf_unicode__"), workdir / "tez.tex")
            load_source(first_source if first_source.exists() else workdir / "tez.tex")
            if refresh_findings_list(select_first=True, keep_selected=False):
                select_finding()
            return True

        def load_cached_preview(run_id, cached_annotation):
            nonlocal annotation_data
            def fail():
                if not window.winfo_exists() or getattr(window, "review_run_id", None) != run_id:
                    return
                status_var.set("Cache önizleme yüklenemedi; Kaydet ve Önizle ile yeniden üretin.")
                window.review_running = False
                window.configure(cursor="")
                update_pdf_button.state(["!disabled"])
                save_button.state(["!disabled"])

            try:
                pdf_path = Path(cached_annotation.get("review_pdf", ""))
                if not pdf_path.exists():
                    window.after(0, fail)
                    return False
                preview_dir = Path(cached_annotation["review_workdir"]) / "_gui_pdf_pages"
                pages = self.render_pdf_pages(pdf_path, preview_dir, dpi=120)
                pdf_pages_meta = self.extract_pdf_word_boxes(pdf_path, preview_dir)
                synctex_locations = self.locate_findings_with_synctex(current_findings, cached_annotation["review_workdir"], pdf_pages_meta)
                text_locations = self.locate_findings_in_pdf(current_findings, pdf_pages_meta, page_hints=synctex_locations)
                result = {
                    "pages": pages,
                    "pdf_pages_meta": pdf_pages_meta,
                    "pdf_locations": choose_pdf_locations(current_findings, synctex_locations, text_locations),
                }
            except Exception:
                try:
                    window.after(0, fail)
                except tk.TclError:
                    pass
                return False

            def apply():
                nonlocal annotation_data
                if not window.winfo_exists() or getattr(window, "review_run_id", None) != run_id:
                    return
                annotation_data = cached_annotation
                window.pdf_pages_meta = result["pdf_pages_meta"]
                window.pdf_locations = result["pdf_locations"]
                show_pdf_pages(result["pages"])
                if current_findings:
                    select_finding()
                status_var.set(f"PDF önizleme hazır: {len(result['pages'])} sayfa, cache kullanıldı.")
                findings_label_var.set(f"{len(current_findings)} bulgu. Cache kullanıldı; kaynak değişirse Kaydet ve Önizle ile yenilenir.")
                window.review_running = False
                window.configure(cursor="")
                update_pdf_button.state(["!disabled"])
                save_button.state(["!disabled"])

            window.after(0, apply)
            return True

        def build_preview_payload(preview_findings, annotation_findings, fast=False):
            preview_findings = list(preview_findings)
            annotation_findings = list(annotation_findings)
            new_annotation_data = yazim_denetimi.create_annotated_pdf(
                workdir,
                annotation_findings,
                reuse=True,
                fast=fast,
            )
            pdf_path = new_annotation_data.get("review_pdf")
            if not pdf_path or not Path(pdf_path).exists():
                raise RuntimeError("İşaretli PDF üretilemedi. Ayrıntılar derleme log dosyasında.")
            preview_dir = Path(new_annotation_data["review_workdir"]) / "_gui_pdf_pages"
            pages = self.render_pdf_pages(Path(pdf_path), preview_dir, dpi=120)
            pdf_pages_meta = self.extract_pdf_word_boxes(Path(pdf_path), preview_dir)
            synctex_locations = self.locate_findings_with_synctex(preview_findings, new_annotation_data["review_workdir"], pdf_pages_meta)
            text_locations = self.locate_findings_in_pdf(preview_findings, pdf_pages_meta, page_hints=synctex_locations)
            return {
                "ok": True,
                "annotation_data": new_annotation_data,
                "current_findings": preview_findings,
                "pages": pages,
                "pdf_pages_meta": pdf_pages_meta,
                "pdf_locations": choose_pdf_locations(preview_findings, synctex_locations, text_locations),
            }

        def apply_fast_preview_result(done_run_id, result):
            nonlocal current_findings, annotation_data
            if not window.winfo_exists() or getattr(window, "review_run_id", None) != done_run_id:
                return
            if not result.get("ok"):
                status_var.set("Hızlı önizleme hazırlanamadı; tam denetim arka planda sürüyor.")
                return
            annotation_data = result["annotation_data"]
            current_findings = result["current_findings"]
            window.pdf_pages_meta = result["pdf_pages_meta"]
            window.pdf_locations = result["pdf_locations"]
            first_source = next((workdir / rel for rel, _number, _message, _raw in current_findings if str(rel) != "__pdf_unicode__"), workdir / "tez.tex")
            load_source(first_source if first_source.exists() else workdir / "tez.tex")
            show_pdf_pages(result["pages"])
            if refresh_findings_list(select_first=True, keep_selected=False):
                select_finding()
            window.configure(cursor="")
            mode_label = "hızlı derleme" if annotation_data.get("build_mode") == "fast" else "cache"
            status_var.set(f"Hızlı önizleme hazır: {len(result['pages'])} sayfa, {annotation_data['annotated_count']} işaretli satır ({mode_label}). Tam denetim arka planda yenileniyor...")

        def build_suggestion_cache(findings, language):
            cache = {}
            dictionaries = {}
            for rel, number, message, raw in findings:
                if str(rel) == "__pdf_unicode__" or "Sözlükte bulunmayan" not in str(message):
                    continue
                span = issue_source_span(raw, message)
                if not span:
                    continue
                word = str(raw or "")[span[0]:span[1]].strip()
                if not word:
                    continue
                lang = yazim_denetimi.spelling_language_for_path(rel, language)
                if lang not in dictionaries:
                    dictionaries[lang] = yazim_denetimi.load_dictionary(lang, workdir=workdir)
                suggestions = []
                for item in re.findall(r"Öneri:\s*`([^`]+)`", str(message or "")):
                    suggestions.append(item)
                dictionary = dictionaries[lang]
                try:
                    for item in dictionary.suggest(word, limit=8):
                        suggestions.append(str(item))
                    best = yazim_denetimi.spelling_suggestion(word, dictionary, cutoff=0.90, lang=lang)
                    if best:
                        suggestions.append(best)
                except Exception:
                    pass
                cleaned = []
                seen = {word.casefold()}
                for item in suggestions:
                    item = str(item).strip()
                    if item and item.casefold() not in seen:
                        seen.add(item.casefold())
                        cleaned.append(preserve_case(word, item))
                cache[finding_key(rel, number, message, raw)] = cleaned[:8]
            return cache

        def set_loading_state():
            current_source["path"] = None
            current_source["dirty"] = False
            current_source["loading"] = True
            source_title_var.set("TeX kaynak kodu - denetim hazırlanıyor")
            source_text.delete("1.0", "end")
            source_text.insert(
                "1.0",
                "Yazım denetimi çalışıyor...\n\n"
                "1. TeX kaynakları ve sözlükler taranıyor.\n"
                "2. İşaretli PDF önizleme hazırlanıyor.\n"
                "3. PDF metni ve kaynak satırları eşleştiriliyor.\n\n"
                "Sonuç geldiğinde bu alan seçili bulgunun bulunduğu TeX satırına geçecek.",
            )
            current_source["loading"] = False
            source_text.edit_modified(False)
            source_text.xview_moveto(0)
            sync_line_numbers()
            pdf_canvas.delete("all")
            pdf_canvas.create_text(
                24,
                24,
                text=(
                    "PDF önizleme hazırlanıyor...\n\n"
                    "Derleme ve sayfa görselleri arka planda üretiliyor.\n"
                    "Bulgular hazır olduğunda seçili satır PDF ve TeX tarafında birlikte gösterilecek."
                ),
                anchor="nw",
                fill=colors["muted"],
                font=("Segoe UI", 10),
                width=620,
            )
            pdf_canvas.configure(scrollregion=(0, 0, 680, 220))
            findings_label_var.set("Bulgular hazırlanıyor...")
            clear_findings_table("Denetim sonuçları bekleniyor...")

        def build_review():
            nonlocal current_findings, annotation_data
            if window.review_running:
                return
            source_was_dirty = bool(current_source.get("dirty"))
            changed_source_rel = None
            if source_was_dirty and current_source.get("path"):
                try:
                    changed_source_rel = Path(current_source["path"]).relative_to(workdir)
                except ValueError:
                    changed_source_rel = None
            if source_was_dirty and not save_current_source(show_status=False):
                return
            quick_preview_requested = bool(current_findings) and (source_was_dirty or bool(window.resolved_finding_keys))
            quick_preview_findings = unresolved_review_findings(current_findings) if quick_preview_requested else []
            quick_annotation_findings = annotation_findings_for_preview(quick_preview_findings) if quick_preview_requested else []
            window.review_running = True
            window.review_run_id = getattr(window, "review_run_id", 0) + 1
            run_id = window.review_run_id
            language = "en" if is_english_thesis_label(self.thesis_language_var.get()) else "tr"
            if not quick_preview_requested:
                window.suggestion_cache = {}
            window.configure(cursor="watch")
            update_pdf_button.state(["disabled"])
            save_button.state(["disabled"])
            status_var.set("Hızlı önizleme hazırlanıyor..." if quick_preview_requested else "Yazım denetimi başlatıldı...")
            cached_annotation = cached_annotation_from_report()
            if not quick_preview_requested and current_findings and report_is_fresh() and cached_annotation:
                status_var.set("Kaynak değişmemiş; son denetim ve PDF önizleme cache'den yükleniyor...")
                findings_label_var.set(f"{len(current_findings)} bulgu. Cache yükleniyor...")
                threading.Thread(target=lambda: load_cached_preview(run_id, cached_annotation), daemon=True).start()
                return
            if quick_preview_requested:
                pdf_canvas.delete("all")
                pdf_canvas.create_text(
                    24,
                    24,
                    text="Hızlı PDF önizleme hazırlanıyor...\n\nMevcut bulgulardan düzeltilenler çıkarıldı. Tam yazım denetimi arka planda kesin sonucu yenileyecek.",
                    anchor="nw",
                    fill=colors["muted"],
                    font=("Segoe UI", 10),
                    width=620,
                )
                pdf_canvas.configure(scrollregion=(0, 0, 680, 180))
                findings_label_var.set(f"{len(quick_preview_findings)} bulgu. Hızlı önizleme hazırlanıyor...")
            elif current_findings:
                pdf_canvas.delete("all")
                pdf_canvas.create_text(
                    24,
                    24,
                    text="Canlı denetim arka planda yenileniyor...\n\nSon rapor solda gösteriliyor. Yeni sonuçlar hazır olunca liste tazelenecek.",
                    anchor="nw",
                    fill=colors["muted"],
                    font=("Segoe UI", 10),
                    width=620,
                )
                pdf_canvas.configure(scrollregion=(0, 0, 680, 180))
            else:
                set_loading_state()

            def post_status(text):
                try:
                    window.after(0, lambda: status_var.set(text) if window.winfo_exists() and getattr(window, "review_run_id", None) == run_id else None)
                except tk.TclError:
                    pass

            def apply_text_result(done_run_id, result):
                nonlocal current_findings
                if not window.winfo_exists() or getattr(window, "review_run_id", None) != done_run_id:
                    return
                window.resolved_finding_keys.clear()
                current_findings = result["current_findings"]
                window.suggestion_cache = result.get("suggestion_cache", {})
                window.pdf_locations = [None] * len(current_findings)
                first_source = next((workdir / rel for rel, _number, _message, _raw in current_findings if str(rel) != "__pdf_unicode__"), workdir / "tez.tex")
                load_source(first_source if first_source.exists() else workdir / "tez.tex")
                if refresh_findings_list(select_first=True, keep_selected=False):
                    select_finding()

            def worker():
                try:
                    if quick_preview_requested:
                        post_status("Hızlı PDF önizleme hazırlanıyor...")
                        try:
                            preview_findings = quick_preview_findings
                            annotation_findings = quick_annotation_findings
                            if changed_source_rel is not None:
                                post_status(f"Değişen dosya hızlı denetleniyor: {changed_source_rel}")
                                quick_writing_findings, _quick_text_export = yazim_denetimi.analyze(
                                    workdir,
                                    language=language,
                                    only_files=[changed_source_rel],
                                )
                                quick_tex_findings = [
                                    (rel, number, f"TeX ön kontrol: {message}", raw)
                                    for rel, number, message, raw in yazim_denetimi.analyze_tex_structure(workdir, only_files=[changed_source_rel])
                                ]
                                changed_key = Path(changed_source_rel).as_posix()
                                unchanged_findings = [
                                    finding
                                    for finding in quick_preview_findings
                                    if str(finding[0]) == "__pdf_unicode__" or Path(finding[0]).as_posix() != changed_key
                                ]
                                preview_findings = quick_writing_findings + quick_tex_findings + unchanged_findings
                                annotation_findings = annotation_findings_for_preview(preview_findings)
                            quick_result = build_preview_payload(
                                preview_findings,
                                annotation_findings,
                                fast=True,
                            )
                        except Exception as quick_exc:
                            quick_result = {"ok": False, "error": quick_exc}
                        try:
                            window.after(0, lambda result=quick_result: apply_fast_preview_result(run_id, result))
                        except tk.TclError:
                            pass
                        post_status("Tam yazım denetimi arka planda yenileniyor...")
                    post_status("TeX kaynakları ve sözlükler taranıyor...")
                    writing_findings, text_export = yazim_denetimi.analyze(workdir, language=language)
                    spell_status = yazim_denetimi.dictionary_status(yazim_denetimi.load_dictionary(language, workdir=workdir), language)
                    post_status("TeX ön kontrolü çalışıyor...")
                    tex_findings = [
                        (rel, number, f"TeX ön kontrol: {message}", raw)
                        for rel, number, message, raw in yazim_denetimi.analyze_tex_structure(workdir)
                    ]
                    initial_findings = writing_findings + tex_findings
                    post_status("Sözcük önerileri hazırlanıyor...")
                    suggestion_cache = build_suggestion_cache(initial_findings, language)
                    try:
                        window.after(0, lambda: apply_text_result(run_id, {
                            "current_findings": initial_findings,
                            "suggestion_cache": suggestion_cache,
                        }))
                    except tk.TclError:
                        pass
                    post_status("İşaretli PDF hazırlanıyor...")
                    new_annotation_data = yazim_denetimi.create_annotated_pdf(workdir, writing_findings, reuse=True)
                    pdf_path = new_annotation_data.get("review_pdf")
                    if not pdf_path or not Path(pdf_path).exists():
                        raise RuntimeError("İşaretli PDF üretilemedi. Ayrıntılar yazim-denetimi-pdf-derleme.log dosyasında.")
                    post_status("PDF metni ve kaynak satırları eşleştiriliyor...")
                    unicode_issues = yazim_denetimi.analyze_pdf_unicode(Path(pdf_path))
                    yazim_denetimi.write_pdf_unicode_report(workdir, unicode_issues)
                    unicode_findings = []
                    for page, _line, tokens, text in unicode_issues:
                        resolved = resolve_unicode_source(text)
                        rel, source_line = resolved if resolved else (Path("__pdf_unicode__"), page)
                        unicode_findings.append((
                            rel,
                            source_line,
                            "PDF Unicode/karakter bozulması: " + ", ".join(tokens[:5]),
                            f"PDF_PAGE:{page}\n{text}",
                        ))
                    all_findings = writing_findings + unicode_findings + tex_findings
                    yazim_denetimi.write_reports(workdir, all_findings, text_export, new_annotation_data, language=language)
                    preview_dir = Path(new_annotation_data["review_workdir"]) / "_gui_pdf_pages"
                    post_status("PDF sayfaları görsele dönüştürülüyor...")
                    pages = self.render_pdf_pages(Path(pdf_path), preview_dir, dpi=120)
                    pdf_pages_meta = self.extract_pdf_word_boxes(Path(pdf_path), preview_dir)
                    synctex_locations = self.locate_findings_with_synctex(all_findings, new_annotation_data["review_workdir"], pdf_pages_meta)
                    text_locations = self.locate_findings_in_pdf(all_findings, pdf_pages_meta, page_hints=synctex_locations)
                    pdf_locations = []
                    for finding, sync_loc, text_loc in zip(all_findings, synctex_locations, text_locations):
                        rel, _number, message, _raw = finding
                        source_resolved = str(rel) != "__pdf_unicode__"
                        if "Ana metinde manuel dikey boşluk" in message:
                            pdf_locations.append(None)
                            continue
                        if "PDF Unicode" in message and source_resolved:
                            caption_loc = self.locate_caption_source_in_pdf(
                                finding,
                                new_annotation_data["review_workdir"],
                                pdf_pages_meta,
                                preferred_page=sync_loc["page"] if sync_loc else None,
                            )
                            pdf_locations.append(caption_loc or sync_loc or text_loc)
                        elif "Kılavuz yazım kuralı" in message:
                            pdf_locations.append(text_loc)
                        elif sync_loc and text_loc and abs(sync_loc["page"] - text_loc["page"]) >= 3:
                            pdf_locations.append(sync_loc)
                        else:
                            pdf_locations.append(text_loc or sync_loc)
                    result = {
                        "ok": True,
                        "annotation_data": new_annotation_data,
                        "current_findings": all_findings,
                        "pages": pages,
                        "pdf_pages_meta": pdf_pages_meta,
                        "pdf_locations": pdf_locations,
                        "suggestion_cache": suggestion_cache,
                        "unicode_issues": unicode_issues,
                        "tex_findings": tex_findings,
                        "spell_status": spell_status,
                    }
                except Exception as exc:
                    result = {"ok": False, "error": exc}
                try:
                    window.after(0, lambda: apply_review_result(run_id, result))
                except tk.TclError:
                    pass

            def apply_review_result(done_run_id, result):
                nonlocal current_findings, annotation_data
                if not window.winfo_exists() or getattr(window, "review_run_id", None) != done_run_id:
                    return
                try:
                    if not result.get("ok"):
                        status_var.set("PDF önizleme hazırlanamadı.")
                        clear_findings_table("Denetim tamamlanamadı.")
                        pdf_canvas.delete("all")
                        pdf_canvas.create_text(20, 20, text=str(result.get("error")), anchor="nw", fill="#B00020", font=("Segoe UI", 10), width=640)
                        return
                    annotation_data = result["annotation_data"]
                    window.resolved_finding_keys.clear()
                    current_findings = result["current_findings"]
                    window.suggestion_cache = result.get("suggestion_cache", {})
                    window.pdf_pages_meta = result["pdf_pages_meta"]
                    window.pdf_locations = result["pdf_locations"]
                    first_source = next((workdir / rel for rel, _number, _message, _raw in current_findings if str(rel) != "__pdf_unicode__"), workdir / "tez.tex")
                    load_source(first_source if first_source.exists() else workdir / "tez.tex")
                    show_pdf_pages(result["pages"])
                    if refresh_findings_list(select_first=True, keep_selected=False):
                        select_finding()
                    unicode_note = f", {len(result['unicode_issues'])} Unicode uyarısı" if result["unicode_issues"] else ""
                    tex_note = f", {len(result['tex_findings'])} TeX ön kontrol bulgusu" if result["tex_findings"] else ""
                    status_var.set(f"PDF önizleme hazır: {len(result['pages'])} sayfa, {annotation_data['annotated_count']} işaretli satır{unicode_note}{tex_note}. {result['spell_status']}")
                finally:
                    window.review_running = False
                    window.configure(cursor="")
                    update_pdf_button.state(["!disabled"])
                    save_button.state(["!disabled"])

            threading.Thread(target=worker, daemon=True).start()

        findings_list.bind("<Double-Button-1>", open_source_for_selected)
        findings_list.bind("<<TreeviewSelect>>", select_finding)
        pdf_canvas.bind("<Double-Button-1>", lambda _event: open_source_for_selected())
        pdf_canvas.bind("<MouseWheel>", scroll_pdf)
        pdf_canvas.bind("<Shift-MouseWheel>", shift_scroll_pdf)
        right.bind("<MouseWheel>", scroll_pdf)
        right.bind("<Shift-MouseWheel>", shift_scroll_pdf)
        pdf_canvas.tag_bind("pdf_highlight", "<Button-1>", lambda _event: open_source_for_selected())
        pdf_canvas.tag_bind("pdf_highlight", "<Double-Button-1>", lambda _event: open_source_for_selected())
        source_text.bind("<Button-1>", lambda _event: close_suggestion_popup(), add="+")
        source_text.bind("<ButtonRelease-1>", show_issue_suggestions_after_click, add="+")
        source_text.tag_bind("active_issue_token", "<Button-1>", lambda _event: close_suggestion_popup())
        source_text.tag_bind("active_issue_token", "<ButtonRelease-1>", show_issue_suggestions_after_click)
        source_text.tag_bind("other_issue_token", "<Button-1>", lambda _event: close_suggestion_popup())
        source_text.tag_bind("other_issue_token", "<ButtonRelease-1>", show_issue_suggestions_after_click)
        source_text.bind("<<Modified>>", on_source_modified)
        source_text.bind("<KeyRelease>", sync_line_numbers)
        pdf_canvas.bind("<Configure>", lambda _event: pdf_canvas.configure(scrollregion=pdf_canvas.bbox("all") or (0, 0, 1, 1)))
        apply_cached_report()
        window.after(100, build_review)

    def edit_ai_declaration(self):
        if hasattr(self, "ai_form_tab"):
            self.notebook.select(self.info_tab)
            self.form_notebook.select(self.ai_form_tab)
            self.show_active_preview()
            if hasattr(self, "ai_declaration_text"):
                self.ai_declaration_text.focus_set()
            return
        window = tk.Toplevel(self)
        window.title("Üretken Yapay Zekâ Beyanı")
        window.geometry("760x560")
        window.transient(self)
        window.columnconfigure(0, weight=1)
        window.rowconfigure(2, weight=1)
        ttk.Label(window, text="Beyan türü").grid(row=0, column=0, sticky="w", padx=12, pady=(12, 4))
        mode_var = tk.StringVar(value="Kullanılmadı")
        mode_box = ttk.Combobox(window, textvariable=mode_var, state="readonly", values=["Kullanılmadı", "Kullanıldı - öneri metni", "Özel metin"], width=28)
        mode_box.grid(row=1, column=0, sticky="w", padx=12)
        text = tk.Text(window, wrap="word", height=18, font=("Segoe UI", 10))
        text.grid(row=2, column=0, sticky="nsew", padx=12, pady=10)
        button_bar = ttk.Frame(window)
        button_bar.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 12))

        templates = {
            "Kullanılmadı": (
                "Bu tez çalışmasının hazırlanmasında bilimsel etik ilkelere ve akademik dürüstlük kurallarına uyduğumu; "
                "yararlandığım tüm kaynakları metin içinde ve kaynaklar bölümünde uygun biçimde gösterdiğimi beyan ederim.\n\n"
                "Bu tez çalışmasında üretken yapay zekâ tabanlı araç kullanılmamıştır."
            ),
            "Kullanıldı - öneri metni": (
                "Bu tez çalışmasının hazırlanmasında bilimsel etik ilkelere ve akademik dürüstlük kurallarına uyduğumu; "
                "yararlandığım tüm kaynakları metin içinde ve kaynaklar bölümünde uygun biçimde gösterdiğimi beyan ederim.\n\n"
                "Bu tez çalışmasında üretken yapay zekâ tabanlı araçlar; dil ve yazım denetimi, anlatımın sadeleştirilmesi, "
                "metin tutarlılığının gözden geçirilmesi ve kaynak gösterimi dışındaki biçimsel önerilerin değerlendirilmesi amacıyla "
                "danışman bilgisi dahilinde sınırlı olarak kullanılmıştır. Üretken yapay zekâ çıktıları doğrudan bilimsel bulgu, analiz, "
                "sonuç veya kaynak yerine kullanılmamış; tüm akademik sorumluluk ve nihai değerlendirme tez yazarına ait olacak şekilde "
                "kontrol edilmiştir."
            ),
            "Özel metin": "",
        }

        current_path = self.template_dir / "etik-beyan.tex"
        current_text = current_path.read_text(encoding="utf-8") if current_path.exists() else templates["Kullanılmadı"]
        text.insert("1.0", current_text)

        def apply_template(_event=None):
            value = templates.get(mode_var.get(), "")
            if value:
                text.delete("1.0", "end")
                text.insert("1.0", value)

        def save_declaration():
            content = text.get("1.0", "end").strip() + "\n"
            current_path.write_text(content, encoding="utf-8")
            self.ensure_etik_macro()
            messagebox.showinfo("Kaydedildi", f"Üretken Yapay Zekâ Beyanı kaydedildi:\n{current_path}")
            window.destroy()

        mode_box.bind("<<ComboboxSelected>>", apply_template)
        ttk.Button(button_bar, text="Şablonu Uygula", command=apply_template).pack(side="left")
        ttk.Button(button_bar, text="Kaydet", style="Primary.TButton", command=save_declaration).pack(side="right")
        ttk.Button(button_bar, text="Vazgeç", command=window.destroy).pack(side="right", padx=8)

    def edit_theorem_environments(self):
        defs_path = self.template_dir / "defs.tex"
        defs_text = yazim_denetimi.read_text(defs_path) if defs_path.exists() else ""
        rows, proof_label = parse_theorem_config(defs_text)
        rows_data = [row.copy() for row in rows]

        window = tk.Toplevel(self)
        window.title("Teorem Ortamları")
        window.geometry("900x560")
        window.minsize(760, 460)
        window.transient(self)
        window.columnconfigure(0, weight=1)
        window.rowconfigure(1, weight=1)

        top = ttk.Frame(window)
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        ttk.Label(top, text="İspat adı").pack(side="left")
        proof_var = tk.StringVar(value=proof_label)
        proof_box = ttk.Combobox(top, textvariable=proof_var, values=["İspat", "Kanıt"], state="readonly", width=10)
        proof_box.pack(side="left", padx=(8, 18))
        status_var = tk.StringVar(value=str(defs_path))
        ttk.Label(top, textvariable=status_var).pack(side="left", fill="x", expand=True)

        table_frame = ttk.Frame(window)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        tree = ttk.Treeview(table_frame, columns=("style", "env", "title", "counter"), show="headings", selectmode="browse")
        tree.heading("style", text="Tür")
        tree.heading("env", text="Ortam")
        tree.heading("title", text="Başlık")
        tree.heading("counter", text="Sayaç")
        tree.column("style", width=120, stretch=False)
        tree.column("env", width=150, stretch=False)
        tree.column("title", width=260, stretch=True)
        tree.column("counter", width=140, stretch=False)
        tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=scroll.set)

        edit = ttk.Frame(window)
        edit.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 8))
        edit.columnconfigure(3, weight=1)
        style_var = tk.StringVar(value="plain")
        env_var = tk.StringVar()
        title_var = tk.StringVar()
        counter_var = tk.StringVar()
        ttk.Label(edit, text="Tür").grid(row=0, column=0, sticky="w")
        ttk.Combobox(edit, textvariable=style_var, values=THEOREM_STYLES, state="readonly", width=12).grid(row=1, column=0, sticky="ew", padx=(0, 8))
        ttk.Label(edit, text="Ortam").grid(row=0, column=1, sticky="w")
        ttk.Entry(edit, textvariable=env_var, width=18).grid(row=1, column=1, sticky="ew", padx=(0, 8))
        ttk.Label(edit, text="Başlık").grid(row=0, column=2, sticky="w")
        ttk.Entry(edit, textvariable=title_var, width=24).grid(row=1, column=2, sticky="ew", padx=(0, 8))
        ttk.Label(edit, text="Sayaç").grid(row=0, column=3, sticky="w")
        ttk.Entry(edit, textvariable=counter_var).grid(row=1, column=3, sticky="ew")

        def refresh_tree(select_index=None):
            tree.delete(*tree.get_children())
            for index, row in enumerate(rows_data):
                tree.insert("", "end", iid=str(index), values=(row.get("style", ""), row.get("env", ""), row.get("title", ""), row.get("counter", "")))
            if select_index is not None and 0 <= select_index < len(rows_data):
                tree.selection_set(str(select_index))
                tree.see(str(select_index))

        def selected_index():
            selection = tree.selection()
            if not selection:
                return None
            try:
                return int(selection[0])
            except ValueError:
                return None

        def fill_fields(_event=None):
            index = selected_index()
            if index is None or index >= len(rows_data):
                return
            row = rows_data[index]
            style_var.set(row.get("style", "plain"))
            env_var.set(row.get("env", ""))
            title_var.set(row.get("title", ""))
            counter_var.set(row.get("counter", ""))

        def clean_field(value):
            return re.sub(r"\s+", " ", value.strip())

        def add_or_update():
            env = env_var.get().strip()
            title = clean_field(title_var.get())
            counter = counter_var.get().strip()
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", env):
                messagebox.showwarning("Ortam adı", "Ortam adı harf ile başlamalı; harf, rakam ve alt çizgi içermeli.")
                return
            if not title or any(char in title for char in "{}"):
                messagebox.showwarning("Başlık", "Başlık boş olmamalı ve süslü parantez içermemeli.")
                return
            if counter and not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", counter):
                messagebox.showwarning("Sayaç", "Sayaç boş olabilir veya geçerli bir ortam/sayaç adı olmalı.")
                return
            row = {"style": style_var.get(), "env": env, "title": title, "counter": counter}
            index = selected_index()
            existing_index = next((i for i, item in enumerate(rows_data) if item.get("env") == env), None)
            if index is not None and index < len(rows_data):
                rows_data[index] = row
                refresh_tree(index)
            elif existing_index is not None:
                rows_data[existing_index] = row
                refresh_tree(existing_index)
            else:
                rows_data.append(row)
                refresh_tree(len(rows_data) - 1)
            status_var.set("Değişiklik var; kaydedilmedi.")

        def delete_selected():
            index = selected_index()
            if index is None or index >= len(rows_data):
                return
            del rows_data[index]
            refresh_tree(min(index, len(rows_data) - 1) if rows_data else None)
            status_var.set("Değişiklik var; kaydedilmedi.")

        def load_defaults():
            rows_data[:] = [row.copy() for row in DEFAULT_THEOREM_ROWS]
            proof_var.set("İspat")
            refresh_tree(0)
            fill_fields()
            status_var.set("Varsayılanlar yüklendi; kaydedilmedi.")

        def save_defs():
            if not rows_data:
                messagebox.showwarning("Ortam yok", "En az bir teorem ortamı tanımlanmalı.")
                return
            current_text = yazim_denetimi.read_text(defs_path) if defs_path.exists() else ""
            block = theorem_rows_to_latex(rows_data, proof_var.get())
            defs_path.write_text(replace_marked_block(current_text, THEOREM_BLOCK_START, THEOREM_BLOCK_END, block), encoding="utf-8")
            status_var.set(f"Kaydedildi: {defs_path.name}")
            self.refresh_system()

        def open_defs():
            if not defs_path.exists():
                save_defs()
            if defs_path.exists():
                self.open_text_file_at_line(defs_path)

        buttons = ttk.Frame(window)
        buttons.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 12))
        ttk.Button(buttons, text="Ekle/Güncelle", image=self._button_icon("write"), compound="left", style="Soft.TButton", command=add_or_update).pack(side="left")
        ttk.Button(buttons, text="Sil", image=self._button_icon("undo"), compound="left", style="Soft.TButton", command=delete_selected).pack(side="left", padx=6)
        ttk.Button(buttons, text="Varsayılanlar", style="Soft.TButton", command=load_defaults).pack(side="left")
        ttk.Button(buttons, text="defs.tex Aç", image=self._button_icon("folder"), compound="left", style="Soft.TButton", command=open_defs).pack(side="left", padx=6)
        ttk.Button(buttons, text="Kaydet", image=self._button_icon("save", "primary"), compound="left", style="Primary.TButton", command=save_defs).pack(side="right")
        ttk.Button(buttons, text="Kapat", style="Soft.TButton", command=window.destroy).pack(side="right", padx=(0, 8))

        tree.bind("<<TreeviewSelect>>", fill_fields)
        refresh_tree(0)
        fill_fields()

    def ensure_etik_macro(self):
        tex_path = self.template_dir / "tez.tex"
        if not tex_path.exists():
            return
        text = tex_path.read_text(encoding="utf-8")
        replacement = r"\etikbeyan{\input etik-beyan.tex}"
        if re.search(r"\\etikbeyan\s*\{", text):
            new_text, _count = re.subn(r"\\etikbeyan\s*\{(?:[^{}]|\\.|(?:\{[^{}]*\}))*\}", replacement, text, count=1)
        else:
            new_text = text.replace(r"\begin{document}", replacement + "\n\n" + r"\begin{document}", 1)
        tex_path.write_text(new_text, encoding="utf-8")

    def find_source_tez(self, source_root):
        source_root = Path(source_root)
        direct = source_root / "tez.tex"
        if direct.exists():
            return direct
        matches = list(source_root.rglob("tez.tex"))
        return matches[0] if matches else None

    def apply_legacy_metadata_to_converted(self, source_root, converted_dir):
        source_tex = self.find_source_tez(source_root)
        target_tex = Path(converted_dir) / "tez.tex"
        if not source_tex or not target_tex.exists():
            return 0
        legacy = read_macros(source_tex)
        if not legacy:
            return 0
        current = read_macros(target_tex)
        for macro in (
            "yazar", "ogrencino", "unvan", "anabilimdali", "programi",
            "baslik", "title", "anahtarkelimeler", "keywords",
            "tezyoneticisi", "tezyoneticisiENG", "esdanismani", "esdanismaniENG",
            "ikincitezdanismani", "ikincitezdanismaniENG", "bapdestegi",
            "kapakyili", "kapaksehri", "tarih", "tarihKucuk",
        ):
            if macro in legacy and any(latex_to_text(v) for v in legacy[macro]):
                current[macro] = legacy[macro]
        return write_macros_to_tex(target_tex, current)

    def resolve_converted_dir(self, output_root, reported_target=None):
        output_root = Path(output_root)
        if reported_target:
            reported = Path(reported_target)
            if reported.exists():
                return reported.parent if reported.name.lower() == "tez.tex" else reported
        direct = output_root / "tez.tex"
        if direct.exists():
            return output_root
        matches = sorted(output_root.rglob("tez.tex"), key=lambda item: (len(item.parts), str(item)))
        return matches[0].parent if matches else output_root

    def convert_legacy_thesis(self):
        folder = filedialog.askdirectory(
            title="Eski tez klasörü seç",
            initialdir=str(ROOT),
        )
        if not folder:
            return
        source = Path(folder)
        if not (source / "tez.tex").exists() and not any(source.rglob("tez.tex")):
            messagebox.showwarning("tez.tex bulunamadı", "Seçilen klasörde veya alt klasörlerinde tez.tex bulunamadı.")
            return
        report_stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        safe_name = re.sub(r"[^0-9A-Za-zÇĞİÖŞÜçğıöşü_.-]+", "-", source.name).strip("-_.") or "tez"
        output_root = LOCAL_OUTPUT_ROOT / "donusturulen_tezler" / f"{safe_name}-{report_stamp}"
        self.last_legacy_source = source
        report_json = output_root / "donusum-raporu.json"
        report_md = output_root / "donusum-raporu.md"
        command = [
            sys.executable,
            str(ROOT / "adapt_sample_theses.py"),
            "--source", str(source),
            "--output", str(output_root),
            "--report-json", str(report_json),
            "--report-md", str(report_md),
        ]
        self.run_command(
            ROOT,
            command,
            "Eski tez yeni şablona dönüştürülüyor",
            on_complete=lambda code, out=output_root, report=report_json: self.finish_legacy_conversion(code, out, report),
        )

    def finish_legacy_conversion(self, exit_code, output_root, report_json):
        output_root = Path(output_root)
        report_json = Path(report_json)
        if not report_json.exists():
            if output_root.exists():
                os.startfile(output_root)
            messagebox.showwarning(
                "Dönüşüm sonucu okunamadı",
                f"Dönüşüm komutu bitti ama rapor bulunamadı.\n\nÇıktı klasörü:\n{output_root}",
            )
            return
        try:
            data = json.loads(report_json.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            messagebox.showwarning("Dönüşüm raporu okunamadı", str(exc))
            return

        results = data.get("results", [])
        ok_results = [item for item in results if item.get("ok") and item.get("target")]
        report_md = output_root / "donusum-raporu.md"
        if not ok_results:
            if output_root.exists():
                os.startfile(output_root)
            messagebox.showwarning(
                "Dönüşüm tamamlanamadı",
                f"Uyarlanan tez bulunamadı. Ayrıntı için raporu kontrol edin:\n{report_md}",
            )
            return

        if len(ok_results) == 1:
            converted_dir = self.resolve_converted_dir(output_root, ok_results[0].get("target"))
            if (converted_dir / "tez.tex").exists():
                try:
                    self.apply_legacy_metadata_to_converted(getattr(self, "last_legacy_source", output_root), converted_dir)
                except Exception as exc:
                    self.log(f"[UYARI] Eski tez bilgileri aktarılırken sorun oluştu: {exc}")
                self.work_dir_var.set(str(converted_dir))
                self.load_from_tez()
                self.refresh_missing()
                self.refresh_system()
                self.update_preview()
                self.notebook.select(self.info_tab)
                os.startfile(converted_dir)
                status = "tamamlandı" if exit_code == 0 else "kısmen tamamlandı"
                messagebox.showinfo(
                    "Dönüşüm " + status,
                    f"Yeni çalışma klasörü seçildi:\n{converted_dir}\n\nRapor:\n{report_md}",
                )
                return

        if output_root.exists():
            os.startfile(output_root)
        messagebox.showinfo(
            "Dönüşüm tamamlandı",
            f"{len(ok_results)} tez dönüştürüldü. Çıktı klasörü açıldı:\n{output_root}\n\nRapor:\n{report_md}",
        )

    def _latex_diag_path(self, raw_path):
        raw_path = str(raw_path or "").strip().strip("\"'").replace("\\", "/")
        if raw_path.startswith("./"):
            raw_path = raw_path[2:]
        if not raw_path:
            return None
        path = Path(raw_path)
        if not path.is_absolute():
            path = self.template_dir / raw_path
        try:
            return path.resolve()
        except OSError:
            return path

    def _latex_diag_excerpt(self, path, line):
        if not path or not line or not Path(path).exists():
            return ""
        try:
            lines = Path(path).read_text(encoding="utf-8-sig", errors="replace").splitlines()
        except OSError:
            return ""
        if 1 <= int(line) <= len(lines):
            return lines[int(line) - 1].strip()
        return ""

    def _latex_input_target(self, path, line):
        if not path or not line or not Path(path).exists():
            return None
        try:
            lines = Path(path).read_text(encoding="utf-8-sig", errors="replace").splitlines()
        except OSError:
            return None
        if not (1 <= int(line) <= len(lines)):
            return None
        raw = lines[int(line) - 1]
        match = re.search(r"\\(?:input|include)\s*(?:\{([^{}]+)\}|([^\s{}]+))", raw)
        if not match:
            return None
        name = (match.group(1) or match.group(2) or "").strip()
        if not name:
            return None
        target = Path(name)
        if target.suffix == "":
            target = target.with_suffix(".tex")
        if not target.is_absolute():
            target = Path(path).parent / target
        return target if target.exists() else None

    def _latex_first_brace_imbalance(self, path):
        if not path or not Path(path).exists():
            return None
        try:
            lines = Path(path).read_text(encoding="utf-8-sig", errors="replace").splitlines()
        except OSError:
            return None
        stack = []
        for line_no, raw in enumerate(lines, start=1):
            escaped = False
            for index, char in enumerate(raw):
                if char == "\\" and not escaped:
                    escaped = True
                    continue
                if char == "%" and not escaped:
                    break
                if char == "{" and not escaped:
                    stack.append((line_no, index))
                elif char == "}" and not escaped:
                    if stack:
                        stack.pop()
                    else:
                        return line_no, index
                escaped = False
        return stack[-1] if stack else None

    def _latex_refine_target(self, message, path=None, line=None):
        text = str(message or "")
        if not path or not line:
            return path, line, None, text
        input_target = self._latex_input_target(path, line)
        if input_target and re.search(r"File ended while scanning|Runaway argument|forgotten a `?}'?|Paragraph ended before", text, re.I):
            suspect = self._latex_first_brace_imbalance(input_target)
            suspect_line, suspect_column = suspect if suspect else (1, None)
            refined = f"{text} Muhtemel kaynak: {input_target.name} içinde kapanmamış süslü parantez."
            return input_target, suspect_line, suspect_column, refined
        return path, line, None, text

    def _latex_diag_hint(self, message, category):
        text = str(message or "")
        if r"\@ynthm" in text:
            return "Bu genellikle \\newtheorem tanımı veya bir makro argümanı bozulunca görünür. Hatanın gösterdiği satırdaki süslü parantezleri ve hemen çağrılan dosyayı kontrol edin."
        if "has an extra }" in text or "doesn't seem to match anything" in text:
            return "Fazladan kapanış süslü parantezi var ya da önceki satırlarda açılan/kapanan parantez dengesi bozulmuş. Aynı satırdaki komut argümanlarını ve bir önceki satırı birlikte kontrol edin."
        if "Paragraph ended before" in text:
            return "Bir komutun argümanı paragraf bitmeden kapanmamış olabilir. En sık neden: eksik `}`, komut içinde boş satır veya yanlış yazılmış komut."
        if "Undefined control sequence" in text:
            return "LaTeX bu komutu tanımıyor. Komut adı yanlış yazılmış olabilir; örneğin \\caption yerine \\capton gibi. Komut doğruysa gerekli paket yüklenmemiş olabilir."
        if "Missing $ inserted" in text:
            return "Matematik sembolü metin içinde kullanılmış olabilir; gerekirse $...$ içine alın."
        if "Runaway argument" in text:
            return "Açılan süslü parantez kapanmamış veya komut argümanı eksik kalmış olabilir."
        if "File ended while scanning" in text:
            return "Genellikle bir alt dosyada kapanmayan süslü parantezden kaynaklanır; gösterilen dosyada ilgili komut satırını kontrol edin."
        if "There's no line here to end" in text:
            return "Genellikle uygun olmayan yerde \\\\ satır sonu komutu kullanılınca oluşur; çoğu zaman şablon veya sayfa makrosundaki satır sonu temizlenmelidir."
        if "File" in text and "not found" in text:
            return "Dosya adı, uzantı veya klasör yolunu kontrol edin; Türkçe karakter/boşluk kaynaklı olabilir."
        if "Citation" in text:
            return "Atıf anahtarı kaynaklar.bib içinde var mı ve bibtex/biber çalışıyor mu kontrol edin."
        if "Reference" in text:
            return "İlgili \\label tanımlı mı, adı doğru mu ve derleme en az iki kez yapıldı mı kontrol edin."
        if text.startswith("Underfull"):
            return "Bu çoğunlukla estetik dizgi bilgisidir; PDF görüntüsü kötü değilse tek tek müdahale etmek gerekmez."
        if text.startswith("Overfull"):
            return "Metin veya nesne satır/kutu dışına taşıyor olabilir; önce PDF'de görünür taşma var mı kontrol edin."
        if category == "Taşma":
            return "Satır veya kutu taşması var; uzun formül, URL, tablo ya da kesilemeyen kelime olabilir."
        if category == "Tablo":
            return "Tablo sütun sayısı, & ayırıcıları ve satır sonundaki \\\\ işaretlerini birlikte kontrol edin."
        if category == "SWP":
            return "Scientific WorkPlace bu satırı içe aktarırken değiştirmiş veya bazı TeX aksan/paragraf parçalarını atlamış olabilir. Bölüm dosyasını kaydetmeden önce satırı TeX editöründe kontrol edin."
        if category == "Paket":
            return "Paket mesajındaki komutu veya paket seçeneklerini kontrol edin."
        return "İlgili satırı açıp çevresindeki komut/parantez dengesini kontrol edin."

    def _latex_count_tabular_columns(self, spec):
        cleaned = re.sub(r"@\{[^{}]*\}", "", spec or "")
        cleaned = re.sub(r"!\{[^{}]*\}", "", cleaned)
        total = 0
        index = 0
        while index < len(cleaned):
            repeat = re.match(r"\*\{(\d+)\}\{([^{}]+)\}", cleaned[index:])
            if repeat:
                total += int(repeat.group(1)) * self._latex_count_tabular_columns(repeat.group(2))
                index += repeat.end()
                continue
            if cleaned[index] in "lcrX":
                total += 1
            elif cleaned[index] in "pmb" and index + 1 < len(cleaned) and cleaned[index + 1] == "{":
                total += 1
                depth = 0
                while index < len(cleaned):
                    if cleaned[index] == "{":
                        depth += 1
                    elif cleaned[index] == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    index += 1
            index += 1
        return total

    def _latex_count_unescaped_ampersands(self, raw):
        count = 0
        escaped = False
        for char in raw:
            if char == "\\" and not escaped:
                escaped = True
                continue
            if char == "%" and not escaped:
                break
            if char == "&" and not escaped:
                count += 1
            escaped = False
        return count

    def _latex_static_table_findings(self):
        findings = []
        for tex_path in sorted(self.template_dir.glob("*.tex")):
            try:
                lines = tex_path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
            except OSError:
                continue
            index = 0
            while index < len(lines):
                begin_match = re.search(r"\\begin\{tabular\}\{([^{}]+)\}", lines[index])
                if not begin_match:
                    index += 1
                    continue
                begin_line = index + 1
                expected_cols = self._latex_count_tabular_columns(begin_match.group(1))
                row_columns = []
                last_row_without_break = None
                look = index + 1
                while look < len(lines):
                    raw = lines[look]
                    stripped = raw.strip()
                    if re.search(r"\\end\{tabular\}", raw):
                        break
                    if stripped and not stripped.startswith("%"):
                        amp_count = self._latex_count_unescaped_ampersands(raw)
                        if amp_count:
                            cols = amp_count + 1
                            row_columns.append((look + 1, cols, raw.rstrip()))
                            if not re.search(r"\\\\\s*(?:%.*)?$", raw):
                                last_row_without_break = (look + 1, raw.rstrip())
                        elif re.match(r"\\hline\b", stripped) and last_row_without_break:
                            line_no, previous = last_row_without_break
                            findings.append({
                                "severity": "HATA",
                                "category": "Tablo",
                                "file": str(tex_path),
                                "line": line_no,
                                "column": max(len(previous), 0),
                                "message": f"Tablo satırı \\\\ ile bitmemiş olabilir; sonraki \\hline bu yüzden {look + 1}. satırda hata veriyor.",
                                "hint": self._latex_diag_hint("", "Tablo"),
                                "excerpt": previous.strip(),
                            })
                            last_row_without_break = None
                    look += 1
                if expected_cols and row_columns:
                    max_cols = max(cols for _line, cols, _raw in row_columns)
                    if max_cols != expected_cols:
                        findings.append({
                            "severity": "HATA",
                            "category": "Tablo",
                            "file": str(tex_path),
                            "line": begin_line,
                            "column": lines[index].find(begin_match.group(1)),
                            "message": f"Tabular sütun tanımı {expected_cols} sütun gösteriyor, fakat satırlarda {max_cols} sütun kullanılmış. Sütun tanımı veya & sayısı uyumsuz.",
                            "hint": self._latex_diag_hint("", "Tablo"),
                            "excerpt": lines[index].strip(),
                        })
                index = max(look + 1, index + 1)
        return findings

    def _latex_static_swp_findings(self):
        findings = []
        suspicious_patterns = [
            (
                re.compile(r"\\i\s+\{\}"),
                "SWP, noktasız i komutunu `\\i {}` biçimine ayırmış görünüyor. `\\i{}` olarak kalmalı.",
            ),
            (
                re.compile(r"\\[cCuU]\s+\{"),
                "SWP, aksan komutu ile argüman arasına boşluk koymuş olabilir. `\\c{s}` veya `\\u{g}` biçimi korunmalı.",
            ),
            (
                re.compile(r"\\(?:c|u|\"|\.|\^)\{[^{}%]*%\s*$"),
                "Satır TeX aksan komutunun içinde `%` ile bölünmüş görünüyor. SWP bu satırı açarken paragraf/parça silebilir.",
            ),
            (
                re.compile(r"(?<!\\)%\s*$"),
                "Satır sonunda `%` var. Bu işaret SWP'de paragraf parçasının silinmiş görünmesine (`DELETED PARAGRAPH`) yol açabilir; gerçek yorum değilse kaldırın.",
            ),
            (
                re.compile(r"\\i\s*$"),
                "`\\i` komutu satır sonunda yalnız kalmış. SWP veya LaTeX sonraki parçayı yanlış bağlayabilir; `\\i{}` kullanın.",
            ),
            (
                re.compile(r"\\AtBeginDocument\b|\\IfFileExists\b|\\phantomsection\b|\\input\{tcilatex\}"),
                "Bu yardımcı LaTeX komutu Scientific WorkPlace içe aktarımında `deleted paragraph` veya yorum/parça silme uyarısına yol açabilir. Bölüm dosyalarında sade tutulmalı.",
            ),
            (
                re.compile(r"^%TCIDATA\{LastRevised=|^%TCIDATA\{<META NAME=\"GraphicsSave\"", re.I),
                "Dosya Scientific WorkPlace tarafından yeniden kaydedilmiş görünüyor. SWP kaydı satırları/aksan komutlarını değiştirdiyse dosyayı TeX tanılama ile tekrar kontrol edin.",
            ),
        ]
        for tex_path in sorted(self.template_dir.glob("bolum*.tex")):
            try:
                lines = tex_path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
            except OSError:
                continue
            for line_no, raw in enumerate(lines, start=1):
                stripped = raw.lstrip()
                if stripped.startswith("%"):
                    if stripped.startswith("%TCIDATA{LastRevised=") or stripped.startswith("%TCIDATA{<META NAME=\"GraphicsSave\""):
                        message = "Dosya Scientific WorkPlace tarafından yeniden kaydedilmiş görünüyor. SWP kaydı satırları/aksan komutlarını değiştirdiyse dosyayı TeX tanılama ile tekrar kontrol edin."
                        findings.append({
                            "severity": "UYARI",
                            "category": "SWP",
                            "file": str(tex_path),
                            "line": line_no,
                            "column": raw.find("%TCIDATA"),
                            "message": message,
                            "hint": self._latex_diag_hint(message, "SWP"),
                            "excerpt": raw.strip(),
                        })
                    continue
                for pattern, message in suspicious_patterns:
                    match = pattern.search(raw)
                    if not match:
                        continue
                    findings.append({
                        "severity": "UYARI",
                        "category": "SWP",
                        "file": str(tex_path),
                        "line": line_no,
                        "column": match.start(),
                        "message": message,
                        "hint": self._latex_diag_hint(message, "SWP"),
                        "excerpt": raw.strip(),
                    })
                    break
        return findings

    def parse_latex_diagnostics(self, stdout_text, log_text=""):
        combined = "\n".join(part for part in [stdout_text or "", log_text or ""] if part)
        lines = combined.splitlines()
        findings = []
        seen = set()
        current_file = self.template_dir / "tez.tex"

        def add(severity, category, message, path=None, line=None):
            path = Path(path) if path else None
            if path and not path.exists():
                path = None
            line_value = int(line) if str(line or "").isdigit() else None
            path, line_value, column_value, message = self._latex_refine_target(message, path, line_value)
            compact_message = re.sub(r"\s+", " ", str(message)).strip()
            key = (severity, category, str(path or ""), line_value or 0, compact_message)
            if key in seen:
                return
            seen.add(key)
            findings.append({
                "severity": severity,
                "category": category,
                "file": str(path) if path else "",
                "line": line_value,
                "column": column_value,
                "message": compact_message,
                "hint": self._latex_diag_hint(compact_message, category),
                "excerpt": self._latex_diag_excerpt(path, line_value),
            })

        file_line_re = re.compile(r"^(?P<file>(?:\.?[\\/])?[^:\n]+?\.(?:tex|bib|sty|cls)):(?P<line>\d+):\s*(?P<msg>.+)$")
        stack_file_re = re.compile(r"\((?:\.\/)?([^()\s]+?\.(?:tex|bib|sty|cls))")
        citation_re = re.compile(r"LaTeX Warning:\s*(Citation|Reference)\s+`([^']+)'[^\n]*?input line\s+(\d+)", re.I)
        box_re = re.compile(r"^(Overfull|Underfull)\s+\\[hv]box.*?lines?\s+(\d+)(?:--(\d+))?", re.I)
        file_not_found_re = re.compile(r"(?:LaTeX Error:\s*)?File\s+`?([^'`\s]+)'?\s+not found", re.I)

        for index, raw in enumerate(lines):
            for file_match in stack_file_re.finditer(raw):
                candidate = self._latex_diag_path(file_match.group(1))
                if candidate and candidate.suffix.lower() in {".tex", ".bib", ".sty", ".cls"}:
                    current_file = candidate

            match = file_line_re.match(raw.strip())
            if match:
                path = self._latex_diag_path(match.group("file"))
                msg = match.group("msg").strip()
                category = "Paket" if path and path.suffix.lower() in {".sty", ".cls"} else "Derleme"
                add("HATA", category, msg, path, match.group("line"))
                continue

            if raw.startswith("! "):
                msg = raw[2:].strip()
                line_number = None
                for next_raw in lines[index + 1:index + 6]:
                    line_match = re.match(r"l\.(\d+)\s*(.*)", next_raw.strip())
                    if line_match:
                        line_number = int(line_match.group(1))
                        if line_match.group(2).strip():
                            msg = f"{msg} | {line_match.group(2).strip()}"
                        break
                category = "Paket" if msg.lower().startswith("package") else "Derleme"
                add("HATA", category, msg, current_file, line_number)
                continue

            citation_match = citation_re.search(raw)
            if citation_match:
                kind, key, line = citation_match.groups()
                add("UYARI", "Atıf/Referans", f"{kind} tanımsız olabilir: {key}", current_file, line)
                continue

            box_match = box_re.match(raw.strip())
            if box_match:
                kind, first_line, _last_line = box_match.groups()
                if kind.lower() == "underfull":
                    add("BİLGİ", "Dizgi", raw.strip(), current_file, first_line)
                else:
                    add("UYARI", "Taşma", raw.strip(), current_file, first_line)
                continue

            missing_match = file_not_found_re.search(raw)
            if missing_match:
                add("HATA", "Eksik dosya", raw.strip(), current_file, None)

        static_table_findings = self._latex_static_table_findings()
        static_swp_findings = self._latex_static_swp_findings()
        if static_table_findings:
            table_paths = {str(item.get("file", "")) for item in static_table_findings}
            cascade_re = re.compile(r"Misplaced \\noalign|\\hrule|Missing number|Illegal unit of measure|Extra alignment tab", re.I)
            findings = [
                item for item in findings
                if not (
                    item.get("file") in table_paths
                    and item.get("category") == "Derleme"
                    and cascade_re.search(item.get("message", ""))
                )
            ]

        for item in static_table_findings + static_swp_findings:
            compact_message = re.sub(r"\s+", " ", str(item.get("message", ""))).strip()
            key = (item.get("severity"), item.get("category"), item.get("file", ""), item.get("line") or 0, compact_message)
            if key in seen:
                continue
            seen.add(key)
            findings.append(item)

        return findings

    def write_latex_diagnostics_reports(self, findings, exit_code, raw_output):
        json_path = self.template_dir / "akilli-derleme-tanilama.json"
        md_path = self.template_dir / "akilli-derleme-tanilama.md"
        payload = {
            "GeneratedAt": datetime.now().isoformat(timespec="seconds"),
            "ExitCode": exit_code,
            "Count": len(findings),
            "Findings": findings,
        }
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        raw_path = self.template_dir / "akilli-derleme-tanilama-cikti.log"
        raw_path.write_text(raw_output or "", encoding="utf-8", errors="replace")
        lines = [
            "# Akıllı Derleme Tanılama",
            "",
            f"- Çıkış kodu: {exit_code}",
            f"- Bulgu sayısı: {len(findings)}",
            "",
        ]
        if findings:
            for index, item in enumerate(findings, start=1):
                file_text = ""
                if item.get("file"):
                    try:
                        rel = Path(item["file"]).relative_to(self.template_dir)
                    except ValueError:
                        rel = Path(item["file"]).name
                    if item.get("line") and item.get("column") is not None:
                        file_text = f" ({rel}:{item.get('line')}.{item.get('column')})"
                    elif item.get("line"):
                        file_text = f" ({rel}:{item.get('line')})"
                    else:
                        file_text = f" ({rel})"
                lines.extend([
                    f"## {index}. {item.get('severity')} - {item.get('category')}{file_text}",
                    "",
                    item.get("message", ""),
                    "",
                    f"Öneri: {item.get('hint', '')}",
                    "",
                ])
                if item.get("excerpt"):
                    lines.extend(["```tex", item["excerpt"], "```", ""])
        else:
            lines.extend(["Belirgin LaTeX derleme hatası yakalanmadı.", ""])
        lines.extend([f"Ham çıktı: `{raw_path.name}`", ""])
        md_path.write_text("\n".join(lines), encoding="utf-8")

    def show_latex_diagnostics_summary(self, exit_code=None):
        json_path = self.template_dir / "akilli-derleme-tanilama.json"
        md_path = self.template_dir / "akilli-derleme-tanilama.md"
        colors = THEMES[self.theme_var.get()]
        self.output.delete("1.0", "end")
        self.output.tag_configure("diag_title", font=("Segoe UI", 11, "bold"), foreground=colors["fg"])
        self.output.tag_configure("diag_section", font=("Segoe UI", 10, "bold"), foreground=colors["accent_dark"])
        self.output.tag_configure("diag_muted", foreground=colors["muted"])
        self.output.insert("end", "Akıllı Derleme Tanılama\n", "diag_title")
        if not json_path.exists():
            self.output.insert("end", "Tanılama raporu oluşturulamadı.\n", "diag_section")
            if exit_code is not None:
                self.output.insert("end", f"Çıkış kodu: {exit_code}\n", "diag_muted")
            self.output.see("1.0")
            return
        try:
            data = json.loads(json_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            self.output.insert("end", f"Rapor okunamadı: {exc}\n", "diag_section")
            self.output.see("1.0")
            return

        findings = data.get("Findings", [])
        error_count = sum(1 for item in findings if item.get("severity") == "HATA")
        warning_count = sum(1 for item in findings if item.get("severity") == "UYARI")
        info_count = sum(1 for item in findings if item.get("severity") == "BİLGİ")
        if error_count:
            status_text = f"{error_count} hata, {warning_count} uyarı, {info_count} bilgi"
        elif warning_count:
            status_text = f"Kritik hata yok; {warning_count} uyarı, {info_count} bilgi"
        else:
            status_text = f"Kritik hata yok; {info_count} dizgi bilgisi"
        self.output.insert("end", f"Durum: {status_text} (çıkış kodu {data.get('ExitCode', exit_code)})\n")
        self.output.insert("end", "Rapor: ")
        if md_path.exists():
            self.insert_output_link(md_path.name, lambda p=md_path: self.open_text_file_at_line(p), "diag_report")
        else:
            self.output.insert("end", str(json_path))
        self.output.insert("end", "\n\n")
        if not findings:
            self.output.insert("end", "Belirgin LaTeX derleme hatası yakalanmadı.\n", "diag_section")
            self.output.insert("end", "PDF yine oluşmadıysa ham çıktı dosyasını ve paket kurulumunu kontrol etmek gerekir.\n", "diag_muted")
            self.output.see("1.0")
            return

        for severity in ("HATA", "UYARI", "BİLGİ"):
            items = [item for item in findings if item.get("severity") == severity]
            if not items:
                continue
            self.output.insert("end", f"{severity} ({len(items)})\n", "diag_section")
            for index, item in enumerate(items[:30], start=1):
                self.output.insert("end", f"{index}. [{item.get('category')}] {textwrap.shorten(item.get('message', ''), width=135, placeholder='...')}")
                path = Path(item["file"]) if item.get("file") else None
                if path and path.exists():
                    self.output.insert("end", "  ")
                    label = self.describe_control_target(path, item.get("line"))
                    if item.get("column") is not None:
                        label = f"{label}.{item.get('column')}"
                    self.insert_output_link(
                        f"aç: {label}",
                        lambda p=path, line=item.get("line"), column=item.get("column"), finding=item: self.open_diagnostic_editor(p, line, column, finding),
                        "diag_action",
                    )
                self.output.insert("end", "\n")
                if item.get("hint"):
                    self.output.insert("end", f"   Öneri: {item['hint']}\n", "diag_muted")
                if item.get("excerpt"):
                    self.output.insert("end", f"   {textwrap.shorten(item['excerpt'], width=150, placeholder='...')}\n", "diag_muted")
            if len(items) > 30:
                self.output.insert("end", f"- ... {len(items) - 30} bulgu daha markdown raporunda.\n", "diag_muted")
            self.output.insert("end", "\n")
        self.output.see("1.0")

    def hide_diagnostic_editor(self):
        if not self.run_paned or not self.diag_editor_panel:
            return
        self.close_diagnostic_suggestion_popup()
        try:
            panes = set(self.run_paned.panes())
            if str(self.diag_editor_panel) in panes:
                self.run_paned.forget(self.diag_editor_panel)
        except tk.TclError:
            pass
        self.diag_editor_visible = False
        self.position_diagnostic_split_toggle()

    def show_diagnostic_editor_panel(self):
        if not self.run_paned or not self.diag_editor_panel:
            return
        try:
            panes = set(self.run_paned.panes())
            if str(self.diag_editor_panel) not in panes:
                self.run_paned.add(self.diag_editor_panel, weight=2)
        except tk.TclError:
            pass
        self.diag_editor_visible = True
        self.position_diagnostic_split_toggle()

    def toggle_diagnostic_editor_panel(self):
        if self.diag_editor_visible:
            self.hide_diagnostic_editor()
            return
        if self.diag_last_editor_args:
            self.open_diagnostic_editor(*self.diag_last_editor_args)
        else:
            self.show_diagnostic_editor_panel()

    def position_diagnostic_split_toggle(self):
        button = getattr(self, "diag_split_toggle", None)
        paned = getattr(self, "run_paned", None)
        if not button or not paned:
            return
        try:
            paned.update_idletasks()
            colors = THEMES[self.theme_var.get()]
            button.configure(
                text="›" if self.diag_editor_visible else "‹",
                bg=colors["accent_dark"],
                fg="#FFFFFF",
                activebackground=colors["accent"],
                activeforeground="#FFFFFF",
            )
            paned_x = paned.winfo_x()
            paned_y = paned.winfo_y()
            paned_w = paned.winfo_width()
            paned_h = paned.winfo_height()
            if paned_w <= 1 or paned_h <= 1:
                button.place_forget()
                return
            if self.diag_editor_visible and len(paned.panes()) > 1:
                try:
                    sash_x, _sash_y = paned.sashpos(0), 0
                except tk.TclError:
                    sash_x = int(paned_w * 0.55)
                x = paned_x + int(sash_x) - 4
            else:
                x = paned_x + paned_w - 8
            y = paned_y + max(28, paned_h // 2 - 18)
            button.place(x=max(0, x), y=max(0, y), width=8, height=34)
            button.lift()
        except tk.TclError:
            pass

    def close_diagnostic_suggestion_popup(self):
        popup = getattr(self, "diag_inline_suggestion_popup", None)
        if popup is not None:
            try:
                if popup.winfo_exists():
                    popup.destroy()
            except tk.TclError:
                pass
        self.diag_inline_suggestion_popup = None
        inline = getattr(self, "diag_inline_suggestion_window", None)
        if inline is not None:
            try:
                if inline.winfo_exists():
                    inline.destroy()
            except tk.TclError:
                pass
        self.diag_inline_suggestion_window = None

    def _center_text_target(self, text_widget, line=None, column=None):
        if not line:
            return
        text_widget.update_idletasks()
        target_line = max(int(line), 1)
        target_column = max(int(column or 0), 0)
        total_lines = max(int(text_widget.index("end-1c").split(".")[0]), 1)
        font_obj = tkfont.Font(font=text_widget.cget("font"))
        visible_lines = max(int(text_widget.winfo_height() / max(font_obj.metrics("linespace"), 1)), 1)
        y_fraction = max((target_line - max(visible_lines // 2, 1)) / max(total_lines, 1), 0)
        text_widget.yview_moveto(min(y_fraction, 1.0))
        raw_line = text_widget.get(f"{target_line}.0", f"{target_line}.end")
        visible_cols = max(int(text_widget.winfo_width() / max(font_obj.measure("0"), 1)), 1)
        start_col = max(target_column - max(visible_cols // 2, 6), 0)
        x_fraction = start_col / max(len(raw_line), visible_cols, 1)
        text_widget.xview_moveto(min(x_fraction, 1.0))
        text_widget.mark_set("insert", f"{target_line}.{target_column}")
        text_widget.see(f"{target_line}.{target_column}")

    def refresh_diag_line_numbers_visibility(self):
        numbers = getattr(self, "diag_editor_line_numbers", None)
        text_widget = getattr(self, "diag_editor_text", None)
        if numbers is None or text_widget is None:
            return
        if self.diag_line_numbers_var.get():
            numbers.grid()
            self.refresh_diag_line_numbers()
        else:
            numbers.grid_remove()

    def refresh_diag_line_numbers(self, _event=None):
        numbers = getattr(self, "diag_editor_line_numbers", None)
        text_widget = getattr(self, "diag_editor_text", None)
        if numbers is None or text_widget is None:
            return
        if not self.diag_line_numbers_var.get():
            return
        try:
            end_line = int(text_widget.index("end-1c").split(".")[0])
            bookmarks = self.diag_bookmarks.get(str(getattr(self, "diag_editor_path", "") or ""), set())
            numbers.configure(state="normal")
            numbers.delete("1.0", "end")
            numbers.insert("1.0", "\n".join((f"● {i}" if i in bookmarks else f"  {i}") for i in range(1, end_line + 1)))
            numbers.configure(state="disabled")
            numbers.yview_moveto(text_widget.yview()[0])
        except tk.TclError:
            pass

    def toggle_diag_line_numbers(self):
        self.diag_line_numbers_var.set(not self.diag_line_numbers_var.get())
        self.refresh_diag_line_numbers_visibility()

    def current_diag_line_from_event(self, event):
        widget = getattr(event, "widget", None)
        text_widget = getattr(self, "diag_editor_text", None)
        if text_widget is None:
            return None
        try:
            if widget is self.diag_editor_line_numbers:
                return int(widget.index(f"@{event.x},{event.y}").split(".")[0])
            return int(text_widget.index(f"@{event.x},{event.y}").split(".")[0])
        except (tk.TclError, ValueError, AttributeError):
            try:
                return int(text_widget.index("insert").split(".")[0])
            except (tk.TclError, ValueError):
                return None

    def set_diag_bookmark(self, line):
        if not line or not self.diag_editor_path:
            return
        marks = self.diag_bookmarks.setdefault(str(self.diag_editor_path), set())
        if line in marks:
            marks.remove(line)
        else:
            marks.add(line)
        self.refresh_diag_line_numbers()

    def goto_diag_bookmark(self, direction=1):
        text_widget = getattr(self, "diag_editor_text", None)
        if text_widget is None or not self.diag_editor_path:
            return
        marks = sorted(self.diag_bookmarks.get(str(self.diag_editor_path), set()))
        if not marks:
            return
        try:
            current = int(text_widget.index("insert").split(".")[0])
        except (tk.TclError, ValueError):
            current = 1
        if direction >= 0:
            target = next((line for line in marks if line > current), marks[0])
        else:
            target = next((line for line in reversed(marks) if line < current), marks[-1])
        self._center_text_target(text_widget, target, 0)

    def show_diag_line_context_menu(self, event):
        line = self.current_diag_line_from_event(event)
        menu = tk.Menu(self, tearoff=False)
        if self.diag_line_numbers_var.get():
            menu.add_command(label="Satır numaralarını gizle", command=self.toggle_diag_line_numbers)
        else:
            menu.add_command(label="Satır numaralarını göster", command=self.toggle_diag_line_numbers)
        menu.add_separator()
        marks = self.diag_bookmarks.get(str(getattr(self, "diag_editor_path", "") or ""), set())
        if line in marks:
            menu.add_command(label=f"Bookmark kaldır ({line})", command=lambda l=line: self.set_diag_bookmark(l))
        else:
            menu.add_command(label=f"Bookmark koy ({line})", command=lambda l=line: self.set_diag_bookmark(l))
        menu.add_command(label="Sonraki bookmark", command=lambda: self.goto_diag_bookmark(1), state="normal" if marks else "disabled")
        menu.add_command(label="Önceki bookmark", command=lambda: self.goto_diag_bookmark(-1), state="normal" if marks else "disabled")
        menu.add_command(label="Bookmarkları temizle", command=lambda: (marks.clear(), self.refresh_diag_line_numbers()), state="normal" if marks else "disabled")
        menu.tk_popup(event.x_root, event.y_root)
        return "break"

    def diagnostic_finding_still_exists(self, path, line=None, column=None):
        report = self.template_dir / "akilli-derleme-tanilama.json"
        if not report.exists():
            return False
        try:
            data = json.loads(report.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return False
        try:
            target = Path(path).resolve()
        except OSError:
            target = Path(path)
        for item in data.get("Findings", []):
            item_file = item.get("file")
            if not item_file:
                continue
            try:
                same_file = Path(item_file).resolve() == target
            except OSError:
                same_file = str(item_file) == str(path)
            if not same_file:
                continue
            if line is not None and item.get("line") != line:
                continue
            if column is not None and item.get("column") is not None and item.get("column") != column:
                continue
            return True
        return False

    def clear_resolved_diag_highlight(self, path, line=None, column=None):
        text_widget = getattr(self, "diag_editor_text", None)
        if text_widget is None:
            return
        if self.diagnostic_finding_still_exists(path, line, column):
            return
        try:
            text_widget.tag_remove("target_line", "1.0", "end")
            text_widget.tag_remove("target_char", "1.0", "end")
            self.close_diagnostic_suggestion_popup()
            self.diag_editor_title_var.set(f"{Path(path).name} - seçili hata düzeltildi")
        except tk.TclError:
            pass

    def configure_tex_syntax_tags(self, text_widget):
        if self.theme_var.get() == "Koyu":
            command = "#79B8FF"
            section = "#9CDCFE"
            env = "#C586C0"
            option = "#D7BA7D"
            comment = "#6A9955"
            math = "#CE9178"
        else:
            command = "#005CC5"
            section = "#004E8A"
            env = "#7A3E9D"
            option = "#8A5A00"
            comment = "#5E7D36"
            math = "#8F3F2B"
        text_widget.tag_configure("tex_command", foreground=command)
        text_widget.tag_configure("tex_section", foreground=section, font=("Consolas", 10, "bold"))
        text_widget.tag_configure("tex_environment", foreground=env, font=("Consolas", 10, "bold"))
        text_widget.tag_configure("tex_option", foreground=option)
        text_widget.tag_configure("tex_comment", foreground=comment)
        text_widget.tag_configure("tex_math", foreground=math)

    def apply_tex_syntax_highlighting(self, text_widget):
        try:
            for tag in ("tex_command", "tex_section", "tex_environment", "tex_option", "tex_comment", "tex_math"):
                text_widget.tag_remove(tag, "1.0", "end")
            lines = text_widget.get("1.0", "end-1c").splitlines()
            section_re = re.compile(r"\\(?:chapter|section|subsection|subsubsection|paragraph|subparagraph)\b")
            env_re = re.compile(r"\\(?:begin|end)\s*\{[^{}]+\}")
            command_re = re.compile(r"\\[A-Za-zçğıöşüÇĞİÖŞÜ@]+")
            option_re = re.compile(r"\[[^\[\]]+\]|\{[^{}\n]{1,80}\}")
            math_re = re.compile(r"\$[^$\n]*\$|\\\(|\\\)|\\\[|\\\]")
            for row, raw in enumerate(lines, start=1):
                comment_at = None
                escaped = False
                for idx, char in enumerate(raw):
                    if char == "%" and not escaped:
                        comment_at = idx
                        break
                    escaped = char == "\\" and not escaped
                    if char != "\\":
                        escaped = False
                code_part = raw if comment_at is None else raw[:comment_at]
                for match in option_re.finditer(code_part):
                    text_widget.tag_add("tex_option", f"{row}.{match.start()}", f"{row}.{match.end()}")
                for match in math_re.finditer(code_part):
                    text_widget.tag_add("tex_math", f"{row}.{match.start()}", f"{row}.{match.end()}")
                for match in command_re.finditer(code_part):
                    tag = "tex_section" if section_re.match(match.group(0)) else "tex_command"
                    text_widget.tag_add(tag, f"{row}.{match.start()}", f"{row}.{match.end()}")
                for match in env_re.finditer(code_part):
                    text_widget.tag_add("tex_environment", f"{row}.{match.start()}", f"{row}.{match.end()}")
                if comment_at is not None:
                    text_widget.tag_add("tex_comment", f"{row}.{comment_at}", f"{row}.end")
        except tk.TclError:
            pass

    def schedule_diag_syntax_highlight(self, text_widget):
        if self.diag_syntax_after_id:
            try:
                self.after_cancel(self.diag_syntax_after_id)
            except tk.TclError:
                pass
        self.diag_syntax_after_id = self.after(180, lambda w=text_widget: (self.apply_tex_syntax_highlighting(w), self.refresh_diag_line_numbers()))

    def _diagnostic_suggestion_specs(self, text_widget, line_number, column=None, finding=None):
        specs = []
        if not line_number:
            return specs
        try:
            line_number = int(line_number)
        except (TypeError, ValueError):
            return specs
        raw_line = text_widget.get(f"{line_number}.0", f"{line_number}.end")

        def replace_range(start, end, value, label):
            return (label, "replace", start, end, value)

        def insert_at(index, value, label):
            return (label, "insert", index, index, value)

        if re.search(r"\\begin\{(?:figure|table)\}\[[^\]]*e[^\]]*\]", raw_line):
            match = re.search(r"\\begin\{(?:figure|table)\}\[([^\]]*)\]", raw_line)
            if match:
                old_opts = match.group(1)
                new_opts = old_opts.replace("e", "")
                new_opts = new_opts or "ht"
                specs.append(replace_range(f"{line_number}.{match.start(1)}", f"{line_number}.{match.end(1)}", new_opts, f"Geçersiz e konumunu kaldır: [{new_opts}]"))

        width_match = re.search(r"\b(width)\s+([0-9.]+[a-zA-Z]+)", raw_line)
        if width_match:
            specs.append(replace_range(f"{line_number}.{width_match.start()}", f"{line_number}.{width_match.end()}", f"width={width_match.group(2)}", "width 230pt yazımını width=230pt yap"))

        typo_map = {
            r"\\capton": ("\\caption", r"\capton komutunu \caption yap"),
            r"\\lable": ("\\label", r"\lable komutunu \label yap"),
            r"\\refe": ("\\ref", r"\refe komutunu \ref yap"),
        }
        for pattern, (replacement, label) in typo_map.items():
            match = re.search(pattern, raw_line)
            if match:
                specs.append(replace_range(f"{line_number}.{match.start()}", f"{line_number}.{match.end()}", replacement, label))

        tabular_match = re.search(r"\\begin\{tabular\}\{([^{}]+)\}", raw_line)
        if tabular_match:
            row_counts = []
            look = line_number + 1
            last_line = int(text_widget.index("end-1c").split(".")[0])
            while look <= last_line:
                candidate = text_widget.get(f"{look}.0", f"{look}.end")
                if re.search(r"\\end\{tabular\}", candidate):
                    break
                stripped = candidate.strip()
                if stripped and not stripped.startswith("\\") and "&" in candidate:
                    row_counts.append(candidate.count("&") + 1)
                look += 1
            if row_counts:
                max_cols = max(row_counts)
                current_cols = self._latex_count_tabular_columns(tabular_match.group(1))
                if max_cols and max_cols != current_cols:
                    specs.append(replace_range(f"{line_number}.{tabular_match.start(1)}", f"{line_number}.{tabular_match.end(1)}", "c" * max_cols, f"Sütun tanımını {'c' * max_cols} yap"))

        chapter_label_match = re.search(r"(\\(?:chapter|section|subsection|subsubsection)\{[^{}\n]*)(\\label\{)", raw_line)
        if chapter_label_match:
            specs.append(insert_at(f"{line_number}.{chapter_label_match.start(2)}", "}", r"\label öncesine } ekle"))

        if "&" in raw_line and not raw_line.rstrip().endswith(r"\\") and not raw_line.lstrip().startswith("\\"):
            specs.append(insert_at(f"{line_number}.end", r" \\", r"Satır sonuna \\ ekle"))

        return specs

    def _render_diagnostic_suggestions(self, text_widget, line_number, column=None, finding=None):
        self.close_diagnostic_suggestion_popup()
        specs = self._diagnostic_suggestion_specs(text_widget, line_number, column, finding)
        if not specs:
            return
        colors = THEMES[self.theme_var.get()]
        editor_bg = text_widget.cget("bg")
        editor_fg = text_widget.cget("fg")
        frame = tk.Frame(text_widget, bg=editor_bg, highlightbackground=colors["accent"], highlightthickness=1, bd=0, padx=4, pady=4)
        self.diag_inline_suggestion_window = frame
        tk.Label(frame, text="Düzeltme önerileri", font=("Segoe UI", 9, "bold"), bg=editor_bg, fg=editor_fg).pack(anchor="w")

        def apply_spec(spec):
            _label, action, start, end, value = spec
            try:
                text_widget.edit_separator()
            except tk.TclError:
                pass
            if action == "replace":
                text_widget.delete(start, end)
                text_widget.insert(start, value)
                text_widget.mark_set("insert", f"{start}+{len(value)}c")
            else:
                text_widget.insert(start, value)
                text_widget.mark_set("insert", f"{start}+{len(value)}c")
            try:
                text_widget.edit_separator()
            except tk.TclError:
                pass
            self.diag_editor_status_var.set("Öneri uygulandı; kaydetmek için Kaydet'e basın.")
            self.close_diagnostic_suggestion_popup()
            text_widget.focus_set()

        for spec in specs[:4]:
            ttk.Button(frame, text=spec[0], style="Tiny.TButton", command=lambda s=spec: apply_spec(s)).pack(anchor="w", fill="x", pady=1)

        text_widget.update_idletasks()
        frame.update_idletasks()
        target_index = f"{int(line_number)}.{max(int(column or 0), 0)}"
        bbox = text_widget.bbox(target_index)
        if bbox:
            x, y, _w, h = bbox
            local_x = x + 8
            local_y = y + h + 4
        else:
            local_x = 16
            local_y = 28
        popup_w = frame.winfo_reqwidth()
        popup_h = frame.winfo_reqheight()
        max_x = max(4, text_widget.winfo_width() - popup_w - 18)
        local_x = min(max(4, local_x), max_x)
        if local_y + popup_h > text_widget.winfo_height() - 8:
            local_y = max(4, (bbox[1] if bbox else 0) - popup_h - 4)
        frame.place(x=local_x, y=local_y)
        frame.lift()

    def open_diagnostic_editor(self, path, line=None, column=None, finding=None):
        path = Path(path)
        if not path.exists():
            messagebox.showwarning("Dosya bulunamadı", str(path))
            return
        self.diag_last_editor_args = (path, line, column, finding)
        self.show_diagnostic_editor_panel()
        self.close_diagnostic_suggestion_popup()
        for child in self.diag_editor_body.winfo_children():
            child.destroy()
        colors = THEMES[self.theme_var.get()]
        if self.theme_var.get() == "Koyu":
            editor_bg, editor_fg, select_bg, select_fg, inactive_select_bg = "#1F2426", "#E9ECE8", "#345F8C", "#FFFFFF", "#2B3E4A"
        else:
            editor_bg, editor_fg, select_bg, select_fg, inactive_select_bg = "#FFF8E1", "#102830", "#8FB9E8", "#061A24", "#D6E4F5"
        line_numbers = tk.Text(self.diag_editor_body, width=5, padx=4, takefocus=0, borderwidth=0, state="disabled", wrap="none", font=("Consolas", 10), bg="#F2EBD4" if self.theme_var.get() != "Koyu" else "#171D20", fg=THEMES[self.theme_var.get()]["muted"])
        line_numbers.grid(row=0, column=0, sticky="ns")
        text = tk.Text(self.diag_editor_body, wrap="none", font=("Consolas", 10), undo=True, bg=editor_bg, fg=editor_fg, insertbackground=editor_fg, selectbackground=select_bg, selectforeground=select_fg, inactiveselectbackground=inactive_select_bg)
        text.grid(row=0, column=1, sticky="nsew")
        y_scroll = ttk.Scrollbar(self.diag_editor_body, orient="vertical", command=lambda *args: (text.yview(*args), line_numbers.yview(*args)))
        y_scroll.grid(row=0, column=2, sticky="ns")
        x_scroll = ttk.Scrollbar(self.diag_editor_body, orient="horizontal", command=text.xview)
        x_scroll.grid(row=1, column=1, sticky="ew")
        text.configure(
            yscrollcommand=lambda first, last, sb=y_scroll: (sb.set(first, last), line_numbers.yview_moveto(first)),
            xscrollcommand=x_scroll.set,
        )
        text.insert("1.0", yazim_denetimi.read_text(path))
        text.edit_modified(False)
        try:
            text.edit_reset()
        except tk.TclError:
            pass
        self.diag_editor_text = text
        self.diag_editor_line_numbers = line_numbers
        self.diag_editor_path = path
        self.configure_tex_syntax_tags(text)
        self.apply_tex_syntax_highlighting(text)
        self.refresh_diag_line_numbers_visibility()
        location = f":{line}" + (f".{column}" if column is not None else "") if line else ""
        self.diag_editor_title_var.set(f"{path.name}{location}")
        self.diag_editor_status_var.set("")
        if line:
            target_column = max(int(column or 0), 0)
            text.tag_configure("target_line", background="#F3E3A3" if self.theme_var.get() != "Koyu" else "#6A5B1C")
            text.tag_add("target_line", f"{line}.0", f"{line}.end")
            if column is not None:
                text.tag_configure("target_char", background="#C97900" if self.theme_var.get() != "Koyu" else "#B87720", foreground="#101820")
                text.tag_add("target_char", f"{line}.{target_column}", f"{line}.{target_column + 1}")
        def save_embedded_file():
            try:
                path.write_text(text.get("1.0", "end-1c"), encoding="utf-8")
            except OSError as exc:
                messagebox.showerror("Kaydedilemedi", str(exc))
                return
            text.edit_modified(False)
            self.diag_editor_title_var.set(f"{path.name} kaydedildi; tanılama çalışıyor")
            self.close_diagnostic_suggestion_popup()
            self.run_latex_diagnostics(on_complete=lambda _code, p=path, ln=line, col=column: self.clear_resolved_diag_highlight(p, ln, col))

        def undo_embedded_edit():
            try:
                text.edit_undo()
                self.diag_editor_status_var.set("Son değişiklik geri alındı.")
            except tk.TclError:
                pass
            text.focus_set()

        def redo_embedded_edit():
            try:
                text.edit_redo()
                self.diag_editor_status_var.set("Geri alınan değişiklik yinelendi.")
            except tk.TclError:
                pass
            text.focus_set()

        def on_click(event):
            index = text.index(f"@{event.x},{event.y}")
            clicked_line = int(index.split(".")[0])
            self._render_diagnostic_suggestions(text, clicked_line, int(index.split(".")[1]), finding)

        text.bind("<Button-1>", on_click, add="+")
        text.bind("<Button-3>", self.show_diag_line_context_menu, add="+")
        line_numbers.bind("<Button-3>", self.show_diag_line_context_menu, add="+")
        text.bind("<KeyRelease>", lambda _event, w=text: (self.refresh_diag_line_numbers(), self.schedule_diag_syntax_highlight(w)), add="+")
        text.bind("<MouseWheel>", lambda _event: self.refresh_diag_line_numbers(), add="+")
        if self.diag_editor_open_button:
            self.diag_editor_open_button.configure(state="normal", command=lambda p=path: self.open_external_file(p))
        if self.diag_editor_save_button:
            self.diag_editor_save_button.configure(state="normal", command=save_embedded_file)
        if self.diag_editor_undo_button:
            self.diag_editor_undo_button.configure(state="normal", command=undo_embedded_edit)
        if self.diag_editor_redo_button:
            self.diag_editor_redo_button.configure(state="normal", command=redo_embedded_edit)

        def after_open():
            self._center_text_target(text, line, column)
            self._render_diagnostic_suggestions(text, line, column, finding)

        self.after(100, after_open)
        self.notebook.select(self.run_tab)

    def load_control_report_data(self):
        report_json = self.template_dir / "kontrol-raporu.json"
        if not report_json.exists():
            return None
        try:
            return json.loads(report_json.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return None

    def open_control_report(self):
        report = self.template_dir / "kontrol-raporu.md"
        if report.exists():
            os.startfile(report)
            return
        messagebox.showinfo("Kontrol raporu yok", "Önce Kontrol Et düğmesiyle rapor üretin.")

    def control_message_target(self, message):
        message = str(message or "")
        match = re.search(r"([\w.-]+\.tex):(\d+)", message)
        if match:
            path = self.template_dir / match.group(1)
            if path.exists():
                return path, int(match.group(2))
        label_match = re.search(r"\b(?:fig|tab|table|eq):[\w:.-]+", message)
        if label_match:
            label = label_match.group(0)
            for tex_path in self.template_dir.glob("*.tex"):
                try:
                    lines = yazim_denetimi.read_text(tex_path).splitlines()
                except OSError:
                    continue
                for index, raw in enumerate(lines, start=1):
                    if f"\\label{{{label}}}" in raw:
                        return tex_path, index
        if re.search(r"\blabel icermiyor\b", message, re.I):
            for tex_path in self.template_dir.glob("*.tex"):
                try:
                    lines = yazim_denetimi.read_text(tex_path).splitlines()
                except OSError:
                    continue
                for index, raw in enumerate(lines, start=1):
                    if re.search(r"\\begin\{(figure|table|equation|align|gather|multline)\*?\}", raw):
                        block = "\n".join(lines[index - 1:min(len(lines), index + 12)])
                        if "\\label{" not in block:
                            return tex_path, index
        if re.search(r"\bbib kayitlari\b", message, re.I):
            bib_path = self.template_dir / "kaynaklar.bib"
            if bib_path.exists():
                key_match = re.search(r"olabilir:\s*([^,\s]+)", message)
                if key_match:
                    wanted = key_match.group(1).strip()
                    try:
                        for index, raw in enumerate(yazim_denetimi.read_text(bib_path).splitlines(), start=1):
                            if re.match(rf"\s*@\w+\s*\{{\s*{re.escape(wanted)}\s*,", raw):
                                return bib_path, index
                    except OSError:
                        pass
                return bib_path, 1
        file_match = re.search(r"([\w.-]+\.(?:tex|bib|log|md|pdf))", message)
        if file_match:
            path = self.template_dir / file_match.group(1)
            if not path.exists():
                return None, None
            if path.suffix.lower() == ".tex":
                return path, 1
            return path, None
        if re.search(r"\bbib\b|kaynak", message, re.I):
            bib_path = self.template_dir / "kaynaklar.bib"
            if bib_path.exists():
                return bib_path, 1
        return None, None

    def describe_control_target(self, path, line=None):
        if not path:
            return ""
        path = Path(path)
        try:
            rel = path.relative_to(self.template_dir)
        except ValueError:
            rel = path.name
        return f"{rel}:{line}" if line else str(rel)

    def control_message_action(self, message):
        message = str(message or "")
        if re.search(r"Ana PDF bulunamadi|Once tez\.tex derlenmeli|tez\.log bulunamadi|log kontrolu yapilamadi", message, re.I):
            path = self.template_dir / "tez.tex"
            if path.exists():
                return {
                    "kind": "external",
                    "path": path,
                    "line": None,
                    "label": "Derle: tez.tex",
                    "hint": "TeXworks/WinEdt ile açılır; derleme buradan yapılabilir.",
                }
        if re.search(r"sirt-kapak\.pdf bulunamadi", message, re.I):
            path = self.template_dir / "sirt-kapak.tex"
            if path.exists():
                return {
                    "kind": "external",
                    "path": path,
                    "line": None,
                    "label": "Derle: sirt-kapak.tex",
                    "hint": "TeXworks/WinEdt ile açılır; sırt kapak buradan derlenebilir.",
                }
        path, line = self.control_message_target(message)
        if not path:
            return None
        path = Path(path)
        text_like = path.suffix.lower() in {".tex", ".bib", ".log", ".md", ".txt", ".json"}
        return {
            "kind": "internal" if text_like else "external",
            "path": path,
            "line": line,
            "label": self.describe_control_target(path, line),
            "hint": "Kaynak satırı yerleşik düzenleyicide açılır." if text_like else "Dosya varsayılan uygulamayla açılır.",
        }

    def open_control_action(self, action):
        if not action:
            return False
        if action["kind"] == "external":
            self.open_external_file(action["path"])
        else:
            self.open_text_file_at_line(action["path"], action.get("line"))
        return True

    def find_tex_editors(self):
        candidates = []

        def add_editor(name, path):
            if not path:
                return
            exe = Path(path)
            if not exe.exists():
                return
            key = str(exe.resolve()).casefold()
            if any(item["key"] == key or item["name"] == name for item in candidates):
                return
            candidates.append({"name": name, "path": exe, "key": key})

        add_editor("TeXworks", shutil.which("texworks") or shutil.which("TeXworks"))
        texlive_root = Path("C:/texlive")
        if texlive_root.exists():
            for pattern in ("*/bin/windows/texworks.exe", "*/tlpkg/texworks/texworks.exe"):
                try:
                    for path in texlive_root.glob(pattern):
                        add_editor("TeXworks", path)
                except OSError:
                    pass
        for path in [
            shutil.which("WinEdt"),
            Path("C:/Program Files/WinEdt Team/WinEdt 11/WinEdt.exe"),
            Path("C:/Program Files/WinEdt Team/WinEdt 10/WinEdt.exe"),
            Path("C:/Program Files (x86)/WinEdt Team/WinEdt 11/WinEdt.exe"),
            Path("C:/Program Files (x86)/WinEdt Team/WinEdt 10/WinEdt.exe"),
        ]:
            add_editor("WinEdt", path)
        return candidates

    def choose_tex_editor(self, editors):
        if self.preferred_tex_editor:
            for editor in editors:
                if editor["key"] == self.preferred_tex_editor.get("key"):
                    return editor
        if len(editors) == 1:
            self.preferred_tex_editor = editors[0]
            return editors[0]

        colors = THEMES[self.theme_var.get()]
        choice = {"editor": None}
        dialog = tk.Toplevel(self)
        dialog.title("TeX editörü seç")
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(bg=colors["bg"])
        dialog.resizable(False, False)
        ttk.Label(
            dialog,
            text="Bu TeX kaynağı Scientific WorkPlace yerine uygun bir LaTeX editörüyle açılmalı.",
            wraplength=460,
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))
        ttk.Label(dialog, text="Bu seçim uygulama açık kaldığı sürece hatırlanır.").grid(row=1, column=0, sticky="w", padx=14, pady=(0, 10))
        buttons = ttk.Frame(dialog)
        buttons.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))

        def set_choice(editor):
            choice["editor"] = editor
            self.preferred_tex_editor = editor
            dialog.destroy()

        for editor in editors:
            ttk.Button(
                buttons,
                text=editor["name"],
                image=self._button_icon("read"),
                compound="left",
                style="Soft.TButton",
                command=lambda item=editor: set_choice(item),
            ).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Vazgeç", style="Soft.TButton", command=dialog.destroy).pack(side="right")
        dialog.update_idletasks()
        x = self.winfo_rootx() + max((self.winfo_width() - dialog.winfo_width()) // 2, 80)
        y = self.winfo_rooty() + max((self.winfo_height() - dialog.winfo_height()) // 2, 80)
        dialog.geometry(f"+{x}+{y}")
        self.wait_window(dialog)
        return choice["editor"]

    def open_external_file(self, path):
        path = Path(path)
        if not path.exists():
            messagebox.showwarning("Dosya bulunamadı", str(path))
            return
        if path.suffix.lower() in {".tex", ".sty", ".cls"}:
            editors = self.find_tex_editors()
            if not editors:
                messagebox.showinfo(
                    "TeX editörü bulunamadı",
                    "TeXworks veya WinEdt bulunamadı. Dosyayı bu penceredeki yerleşik düzenleyicide değiştirebilirsiniz.",
                )
                return
            editor = self.choose_tex_editor(editors)
            if not editor:
                return
            try:
                subprocess.Popen([str(editor["path"]), str(path)], cwd=str(path.parent))
            except OSError as exc:
                messagebox.showerror("Editör açılamadı", str(exc))
            return
        try:
            os.startfile(path)
        except OSError as exc:
            messagebox.showerror("Dosya açılamadı", str(exc))

    def open_text_file_at_line(self, path, line=None, column=None):
        path = Path(path)
        if not path.exists():
            messagebox.showwarning("Dosya bulunamadı", str(path))
            return
        if path.suffix.lower() not in {".tex", ".bib", ".log", ".md", ".txt", ".json"}:
            self.open_external_file(path)
            return
        colors = THEMES[self.theme_var.get()]
        window = tk.Toplevel(self)
        window.transient(self)
        location = ""
        if line:
            location = f":{line}" + (f".{column}" if column is not None else "")
        base_title = f"{path.name}{location}"
        window.title(base_title)
        window.geometry("920x620")
        window.minsize(720, 460)
        window.configure(bg=colors["bg"])
        window.columnconfigure(0, weight=1)
        window.rowconfigure(0, weight=1)
        frame = ttk.Frame(window)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        text = tk.Text(frame, wrap="none", font=("Consolas", 10), undo=True)
        if self.theme_var.get() == "Koyu":
            editor_bg = "#1F2426"
            editor_fg = "#E9ECE8"
            select_bg = "#334D66"
            inactive_select_bg = "#2B3E4A"
        else:
            editor_bg = "#FFF8E1"
            editor_fg = "#102830"
            select_bg = "#C7D7EE"
            inactive_select_bg = "#D8E1EF"
        text.configure(
            bg=editor_bg,
            fg=editor_fg,
            insertbackground=editor_fg,
            selectbackground=select_bg,
            selectforeground=editor_fg,
            inactiveselectbackground=inactive_select_bg,
        )
        text.grid(row=0, column=0, sticky="nsew")
        y_scroll = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll = ttk.Scrollbar(frame, orient="horizontal", command=text.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")
        text.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        try:
            opened_mtime = path.stat().st_mtime
        except OSError:
            opened_mtime = None
        opened_mtime_ref = [opened_mtime]
        suppress_modified = [True]
        text.insert("1.0", yazim_denetimi.read_text(path))
        text.edit_modified(False)
        window.after_idle(lambda: suppress_modified.__setitem__(0, False))
        target_info = ""
        target_range = [None, None]
        if line:
            target_column = max(int(column or 0), 0)
            target = f"{line}.{target_column}"
            text.tag_configure("target_line", background="#F3E3A3" if self.theme_var.get() != "Koyu" else "#6A5B1C")
            text.tag_add("target_line", f"{line}.0", f"{line}.end")
            if column is not None:
                text.tag_configure("target_char", background="#C97900" if self.theme_var.get() != "Koyu" else "#B87720", foreground="#101820")
                target_end = f"{line}.{target_column + 1}"
                text.tag_add("target_char", target, target_end)
                target_range[:] = [target, target_end]
                target_char = text.get(target, f"{line}.{target_column + 1}") or " "
                target_info = f" | Şüpheli karakter: {target_char!r}, satır {line}, sütun {target_column + 1}"
            text.mark_set("insert", target)
            text.see(target)
        status_var = tk.StringVar(value=str(path) + target_info)

        def clear_modified_flag():
            suppress_modified[0] = True
            text.edit_modified(False)
            window.after_idle(lambda: suppress_modified.__setitem__(0, False))

        def refocus_editor():
            if window.winfo_exists():
                window.lift()
                text.focus_set()

        def center_target_position():
            if not line or not window.winfo_exists():
                return
            window.update_idletasks()
            target_line = max(int(line), 1)
            target_column = max(int(column or 0), 0)
            total_lines = max(int(text.index("end-1c").split(".")[0]), 1)
            font_obj = tkfont.Font(font=text.cget("font"))
            visible_lines = max(int(text.winfo_height() / max(font_obj.metrics("linespace"), 1)), 1)
            y_fraction = max((target_line - max(visible_lines // 2, 1)) / max(total_lines, 1), 0)
            text.yview_moveto(min(y_fraction, 1.0))
            raw_line = text.get(f"{target_line}.0", f"{target_line}.end")
            visible_cols = max(int(text.winfo_width() / max(font_obj.measure("0"), 1)), 1)
            start_col = max(target_column - max(visible_cols // 2, 6), 0)
            x_fraction = start_col / max(len(raw_line), visible_cols, 1)
            text.xview_moveto(min(x_fraction, 1.0))
            text.mark_set("insert", f"{target_line}.{target_column}")
            text.see(f"{target_line}.{target_column}")

        def replace_range(start, end, value):
            text.delete(start, end)
            text.insert(start, value)
            text.mark_set("insert", f"{start}+{len(value)}c")
            status_var.set("Öneri uygulandı; kaydetmek için Kaydet'e basın.")

        def insert_text_at(index, value):
            text.insert(index, value)
            text.mark_set("insert", f"{index}+{len(value)}c")
            status_var.set("Öneri uygulandı; kaydetmek için Kaydet'e basın.")

        def diagnostic_suggestions_for_line(line_number):
            suggestions = []
            if not line_number:
                return suggestions
            raw_line = text.get(f"{line_number}.0", f"{line_number}.end")
            tabular_match = re.search(r"\\begin\{tabular\}\{([^{}]+)\}", raw_line)
            if tabular_match:
                row_counts = []
                look = line_number + 1
                while look <= int(text.index("end-1c").split(".")[0]):
                    candidate = text.get(f"{look}.0", f"{look}.end")
                    if re.search(r"\\end\{tabular\}", candidate):
                        break
                    stripped = candidate.strip()
                    if stripped and not stripped.startswith("\\") and "&" in candidate:
                        row_counts.append(candidate.count("&") + 1)
                    look += 1
                if row_counts:
                    max_cols = max(row_counts)
                    current_spec = tabular_match.group(1)
                    current_cols = self._latex_count_tabular_columns(current_spec)
                    if max_cols and max_cols != current_cols:
                        start = f"{line_number}.{tabular_match.start(1)}"
                        end = f"{line_number}.{tabular_match.end(1)}"
                        suggestions.append((
                            f"Sütun tanımını {'c' * max_cols} yap",
                            lambda s=start, e=end, v=("c" * max_cols): replace_range(s, e, v),
                        ))
            chapter_label_match = re.search(r"(\\(?:chapter|section|subsection|subsubsection)\{[^{}\n]*)(\\label\{)", raw_line)
            if chapter_label_match:
                insert_at = f"{line_number}.{chapter_label_match.start(2)}"
                suggestions.append((
                    "\\label öncesine } ekle",
                    lambda idx=insert_at: insert_text_at(idx, "}"),
                ))
            if "&" in raw_line and not raw_line.rstrip().endswith(r"\\") and not raw_line.lstrip().startswith("\\"):
                insert_at = f"{line_number}.end"
                suggestions.append((
                    "Satır sonuna \\\\ ekle",
                    lambda idx=insert_at: insert_text_at(idx, r" \\"),
                ))
            return suggestions

        def show_diagnostic_suggestions(event):
            if not line:
                return
            click_index = text.index(f"@{event.x},{event.y}")
            on_target = False
            if target_range[0] and target_range[1]:
                on_target = text.compare(click_index, ">=", target_range[0]) and text.compare(click_index, "<=", target_range[1])
            if not on_target and int(click_index.split(".")[0]) != int(line):
                return
            suggestions = diagnostic_suggestions_for_line(int(line))
            if not suggestions:
                return
            menu = tk.Menu(window, tearoff=False)
            for label, command in suggestions:
                menu.add_command(label=label, command=command)
            menu.tk_popup(event.x_root, event.y_root)
            return "break"

        def on_modified(_event=None):
            if suppress_modified[0]:
                text.edit_modified(False)
                return
            if text.edit_modified():
                window.title(base_title + " *")
                status_var.set("Değişiklik var; kaydedilmedi.")
                text.edit_modified(False)

        def reload_disk_text(disk_text):
            suppress_modified[0] = True
            text.delete("1.0", "end")
            text.insert("1.0", disk_text)
            text.edit_modified(False)
            window.after_idle(lambda: suppress_modified.__setitem__(0, False))
            try:
                opened_mtime_ref[0] = path.stat().st_mtime
            except OSError:
                opened_mtime_ref[0] = None
            window.title(base_title)
            status_var.set("Diskteki güncel dosya yeniden yüklendi." + target_info)
            refocus_editor()

        def save_file():
            editor_text = text.get("1.0", "end-1c")
            try:
                current_mtime = path.stat().st_mtime
            except OSError:
                current_mtime = None
            if opened_mtime_ref[0] is not None and current_mtime is not None and current_mtime != opened_mtime_ref[0]:
                disk_text = yazim_denetimi.read_text(path)
                if disk_text != editor_text:
                    decision = messagebox.askyesnocancel(
                        "Dosya dışarıda değişmiş",
                        "Bu dosya WinEdt veya başka bir programda değiştirilmiş görünüyor.\n\n"
                        "Evet: bu penceredeki metni kaydet ve diskteki farklı hali ez.\n"
                        "Hayır: diskteki güncel hali bu pencereye yeniden yükle.\n"
                        "İptal: hiçbir şey yapma.",
                        parent=window,
                    )
                    if decision is None:
                        refocus_editor()
                        return
                    if decision is False:
                        reload_disk_text(disk_text)
                        return
            try:
                path.write_text(editor_text, encoding="utf-8")
            except OSError as exc:
                messagebox.showerror("Kaydedilemedi", str(exc), parent=window)
                refocus_editor()
                return
            try:
                opened_mtime_ref[0] = path.stat().st_mtime
            except OSError:
                opened_mtime_ref[0] = None
            window.title(base_title)
            status_var.set(f"Kaydedildi: {path.name}")
            clear_modified_flag()
            try:
                is_template_tex = path.suffix.lower() == ".tex" and path.resolve().is_relative_to(self.template_dir.resolve())
            except (OSError, ValueError):
                is_template_tex = False
            if is_template_tex:
                status_var.set(f"Kaydedildi: {path.name}; tanılama yeniden çalışıyor.")
                def close_editor_after_diagnostics(_exit_code=None):
                    self.notebook.select(self.run_tab)
                    self.deiconify()
                    self.lift()
                    self.focus_force()
                    if window.winfo_exists():
                        window.destroy()

                def rerun_and_show_results():
                    self.run_latex_diagnostics(on_complete=close_editor_after_diagnostics)

                self.after(120, rerun_and_show_results)
            else:
                refocus_editor()

        text.bind("<<Modified>>", on_modified)
        text.bind("<Button-1>", show_diagnostic_suggestions, add="+")
        window.after(90, center_target_position)
        buttons = ttk.Frame(window)
        buttons.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        ttk.Button(buttons, text="Editörde Aç", image=self._button_icon("folder"), compound="left", style="Soft.TButton", command=lambda: self.open_external_file(path)).pack(side="left")
        ttk.Label(buttons, textvariable=status_var).pack(side="left", fill="x", expand=True, padx=10)
        ttk.Button(buttons, text="Kaydet", image=self._button_icon("save", "primary"), compound="left", style="Primary.TButton", command=save_file).pack(side="right", padx=(6, 0))
        ttk.Button(buttons, text="Kapat", style="Soft.TButton", command=window.destroy).pack(side="right")

    def show_control_report_summary(self, exit_code=None):
        data = self.load_control_report_data()
        colors = THEMES[self.theme_var.get()]
        report_md = self.template_dir / "kontrol-raporu.md"
        report_json = self.template_dir / "kontrol-raporu.json"
        self.output.delete("1.0", "end")
        self.output.tag_configure("control_title", font=("Segoe UI", 11, "bold"), foreground=colors["fg"])
        self.output.tag_configure("control_section", font=("Segoe UI", 10, "bold"), foreground=colors["accent_dark"])
        self.output.tag_configure("control_muted", foreground=colors["muted"])
        self.output.insert("end", "Kontrol Özeti\n", "control_title")
        if not data:
            self.output.insert("end", "Kontrol raporu okunamadı.\n", "control_section")
            self.output.insert("end", f"Beklenen rapor: {report_json}\n", "control_muted")
            if exit_code not in (0, None):
                self.output.insert("end", f"Çıkış kodu: {exit_code}\n", "control_muted")
            self.output.see("1.0")
            return

        self.output.insert("end", f"Durum: {data.get('Fail', 0)} FAIL, {data.get('Warning', 0)} UYARI, {data.get('Manual', 0)} MANUEL\n")
        self.output.insert("end", "Rapor: ")
        report_path = report_md if report_md.exists() else report_json
        if report_path.exists():
            self.insert_output_link(report_path.name, lambda p=report_path: self.open_text_file_at_line(p), "control_report")
        else:
            self.output.insert("end", str(report_path))
        self.output.insert("end", "\n")
        if exit_code not in (0, None):
            self.output.insert("end", "FAIL satırı varsa kontrol komutunun başarısız kodla dönmesi beklenir.\n", "control_muted")
        self.output.insert("end", "\n")

        grouped = {"FAIL": [], "UYARI": [], "MANUEL": [], "OK": []}
        for item in data.get("Results", []):
            status = str(item.get("Status", "")).upper()
            message = str(item.get("Message", "")).strip()
            grouped.setdefault(status, []).append(message)

        section_info = [
            ("FAIL", "Önce düzeltilmesi gerekenler", None),
            ("UYARI", "Gözden geçirilecek uyarılar", None),
            ("MANUEL", "Elle kontrol edilecekler", None),
            ("OK", "Temiz geçenler", 8),
        ]
        for status, title, limit in section_info:
            messages = grouped.get(status, [])
            if not messages:
                continue
            shown = messages[:limit] if limit else messages
            self.output.insert("end", f"{title} ({len(messages)})\n", "control_section")
            for index, message in enumerate(shown, 1):
                self.output.insert("end", f"{index}. {textwrap.shorten(message, width=150, placeholder='...')}")
                action = self.control_message_action(message)
                if action:
                    self.output.insert("end", "  ")
                    self.insert_output_link(f"aç: {action['label']}", lambda item=action: self.open_control_action(item), "control_action")
                self.output.insert("end", "\n")
                if action and status != "OK":
                    self.output.insert("end", f"   {action['hint']}\n", "control_muted")
            if limit and len(messages) > limit:
                self.output.insert("end", f"- ... {len(messages) - limit} satır daha raporda.\n", "control_muted")
            self.output.insert("end", "\n")

        self.output.insert("end", "Ayrıntılı markdown raporu üstteki rapor bağlantısından açılabilir.\n", "control_muted")
        self.output.see("1.0")
        self.update_dashboard_status()

    def format_control_report(self, cwd, exit_code, raw_output=None):
        cwd = Path(cwd)
        report_json = cwd / "kontrol-raporu.json"
        report_md = cwd / "kontrol-raporu.md"
        if not report_json.exists():
            raw = "".join(raw_output or [])
            return (
                "\n-- Kontrol raporu okunamadı --\n"
                f"Çıkış kodu: {exit_code}\n"
                f"Beklenen dosya: {report_json}\n\n"
                "Ham çıktı:\n"
                f"{raw}\n"
            )
        try:
            data = json.loads(report_json.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            return f"\n-- Kontrol raporu okunamadı --\n{exc}\nRapor: {report_json}\n"

        results = data.get("Results", [])
        groups = {"FAIL": [], "UYARI": [], "MANUEL": [], "OK": []}
        for item in results:
            status = str(item.get("Status", "")).upper()
            message = str(item.get("Message", "")).strip()
            groups.setdefault(status, []).append(message)

        lines = [
            "",
            "== Kontrol Özeti ==",
            f"Durum: {data.get('Fail', 0)} FAIL, {data.get('Warning', 0)} UYARI, {data.get('Manual', 0)} MANUEL",
            f"Klasör: {data.get('Folder', cwd)}",
            f"Rapor: {report_md if report_md.exists() else report_json}",
            "",
        ]

        def append_numbered(items):
            for index, message in enumerate(items, start=1):
                prefix = f"{index}. "
                wrapped = textwrap.fill(
                    message,
                    width=112,
                    initial_indent=prefix,
                    subsequent_indent=" " * len(prefix),
                    break_long_words=False,
                    break_on_hyphens=False,
                )
                lines.extend(wrapped.splitlines())

        def append_bullets(items):
            for message in items:
                wrapped = textwrap.fill(
                    message,
                    width=112,
                    initial_indent="- ",
                    subsequent_indent="  ",
                    break_long_words=False,
                    break_on_hyphens=False,
                )
                lines.extend(wrapped.splitlines())

        section_info = [
            ("FAIL", "Önce düzeltilmesi gerekenler"),
            ("UYARI", "Gözden geçirilecek uyarılar"),
            ("MANUEL", "Elle kontrol edilecekler"),
        ]
        for status, title in section_info:
            items = groups.get(status, [])
            if not items:
                continue
            lines.append(f"-- {title} ({len(items)}) --")
            append_numbered(items)
            lines.append("")

        ok_items = groups.get("OK", [])
        if ok_items:
            lines.append(f"-- Temiz geçen kontroller ({len(ok_items)}) --")
            append_bullets(ok_items[:8])
            if len(ok_items) > 8:
                lines.append(f"- ... {len(ok_items) - 8} OK satırı daha raporda.")
            lines.append("")

        if exit_code != 0:
            lines.append("Not: FAIL satırı olduğu için kontrol komutu başarısız kodla döndü; bu beklenen bir davranıştır.")
        lines.append("Kontrol tamamlanınca sonuçlar alt pencerede tıklanabilir özet olarak gösterilir.")
        lines.append("")
        return "\n".join(lines)

    def start_busy_feedback(self, label):
        self.status.configure(text=f"Çalışıyor: {label}")
        self.configure(cursor="watch")
        if hasattr(self, "busy_progress"):
            self.busy_progress.pack(side="right")
            self.busy_progress.start(12)
        self._busy_button_states = {}
        for button in getattr(self, "busy_buttons", []):
            try:
                if not button.winfo_exists():
                    continue
                was_disabled = button.instate(["disabled"])
                self._busy_button_states[button] = was_disabled
                if not was_disabled:
                    button.state(["disabled"])
            except tk.TclError:
                continue
        self.update_idletasks()

    def stop_busy_feedback(self):
        if hasattr(self, "busy_progress"):
            self.busy_progress.stop()
            self.busy_progress.pack_forget()
        self.configure(cursor="")
        for button, was_disabled in getattr(self, "_busy_button_states", {}).items():
            try:
                if button.winfo_exists() and not was_disabled:
                    button.state(["!disabled"])
            except tk.TclError:
                continue
        self._busy_button_states = {}
        self.status.configure(text="Hazır")

    def run_command(self, cwd, command, label, output_mode="live", on_complete=None):
        if self.running:
            messagebox.showwarning("İşlem sürüyor", "Devam eden işlem bitmeden yeni işlem başlatılamaz.")
            return
        self.running = True
        self.start_busy_feedback(label)
        self.output.delete("1.0", "end")
        self.output.insert("end", f"== {label} ==\n")
        self.output.insert("end", "İşlem başladı. Uzun tezlerde bu adım birkaç dakika sürebilir; bitince sonuçlar burada güncellenecek.\n")
        if output_mode == "control":
            self.output.insert("end", "Kontrol çalışıyor; sonuçlar tamamlanınca okunaklı özet olarak gösterilecek.\n")
        self.output.see("end")
        self.notebook.select(self.run_tab)
        self.update_idletasks()

        def worker():
            captured_output = []
            code = None
            try:
                process = subprocess.Popen(command, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
                assert process.stdout is not None
                for line in process.stdout:
                    if output_mode == "control":
                        captured_output.append(line)
                    else:
                        self.output_queue.put(line)
                code = process.wait()
                if output_mode == "control" and not callable(on_complete):
                    self.output_queue.put(self.format_control_report(cwd, code, captured_output))
                self.output_queue.put(f"\n[İşlem bitti] Çıkış kodu: {code}\n")
            except Exception as exc:
                self.output_queue.put(f"\n[HATA] {exc}\n")
            finally:
                self.output_queue.put(("__DONE__", code, on_complete))

        threading.Thread(target=worker, daemon=True).start()

    def _drain_output(self):
        try:
            while True:
                item = self.output_queue.get_nowait()
                if isinstance(item, tuple) and item and item[0] == "__UPDATE_STATUS__":
                    _marker, available, status = item
                    self.apply_update_status(available, status)
                elif isinstance(item, tuple) and item and item[0] == "__UPDATE_CHECK_DONE__":
                    _marker, exit_code, output = item
                    self.handle_update_check_done(exit_code, output)
                elif item == "__DONE__" or (isinstance(item, tuple) and item and item[0] == "__DONE__"):
                    self.running = False
                    self.refresh_missing()
                    if isinstance(item, tuple):
                        _marker, exit_code, on_complete = item
                        if callable(on_complete):
                            try:
                                on_complete(exit_code)
                            except Exception as exc:
                                self.output.insert("end", f"\n[HATA] Tamamlanma işlemi başarısız: {exc}\n")
                                self.output.see("end")
                    self.stop_busy_feedback()
                else:
                    self.output.insert("end", str(item))
                    self.output.see("end")
        except queue.Empty:
            pass
        self.after(100, self._drain_output)

    def open_delivery(self):
        folder = self.template_dir / "teslim"
        if folder.exists():
            os.startfile(folder)
        else:
            messagebox.showinfo("Teslim klasörü yok", "Henüz teslim paketi oluşturulmamış.")


if __name__ == "__main__":
    ThesisManager().mainloop()
