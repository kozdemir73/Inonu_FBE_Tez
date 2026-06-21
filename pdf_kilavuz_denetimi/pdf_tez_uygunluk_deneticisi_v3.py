import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import median

import fitz  # PyMuPDF

try:
    import tkinter as tk
    from tkinter import filedialog
except Exception:
    tk = None
    filedialog = None

# ============================================================
# Inonu Universitesi Lisansustu Tez Yazim Kilavuzu
# PDF Uygunluk On Denetim Araci - v2
#
# Not: Enstitu tarafindan onaylanmis resmi Word/LaTeX sablon
# bulunmadigi durumda referans, kilavuzdaki olculebilir kurallardir.
# ============================================================

DEFAULT_CONFIG = {
    "expected_page_width_cm": 21.0,
    "expected_page_height_cm": 29.7,
    "expected_margin_cm": 2.5,
    "expected_body_font_name": "Calibri",
    "expected_body_font_size": 11,
    "expected_line_spacing": 1.5,
    "expected_heading_after_pt": 16.5,
    "expected_subheading_before_pt": 12.0,
    "expected_subheading_after_pt": 6.0,
    "expected_caption_outer_pt": 12.0,
    "expected_caption_inner_pt": 6.0,
    "tol_spacing_pt": 5.0,
    "tol_page_cm": 0.1,
    "tol_margin_strict_cm": 0.1,
    "tol_margin_cm": 0.2,
    "tol_font_pt": 0.5,
    "body_band_top_cm": 2.0,
    "body_band_bottom_cm": 2.0,
    # Varsayilan: kılavuz marjinleri "en az" bosluk olarak yorumlanir.
    # Exact mode sadece resmi sablon varsa tercih edilmelidir.
    "margin_check_mode": "minimum",
    "detailed_pdf": False,
}

MAIN_HEADING_WORDS = {
    "GİRİŞ", "GENEL BİLGİLER", "KURAMSAL TEMELLER", "MATERYAL VE YÖNTEM",
    "MATERYAL VE METOT", "YÖNTEM", "BULGULAR", "TARTIŞMA", "SONUÇ",
    "SONUÇ VE ÖNERİLER", "KAYNAKÇA", "EKLER",
}

FRONT_MATTER_WORDS = {
    "ÖZET", "ABSTRACT", "TEŞEKKÜR", "TEŞEKKÜR VE ÖNSÖZ", "İÇİNDEKİLER", "ŞEKİLLER DİZİNİ",
    "TABLOLAR DİZİNİ", "SİMGELER VE KISALTMALAR", "KISALTMALAR",
}

VIS = {
    "compact_mode": True,
    "show_line_boxes": False,
    "show_font_labels": False,
    "show_blank_labels": False,
    "show_margins": True,
    "show_image_boxes": False,
    "show_summary_box": True,
    "max_summary_lines": 12,
    "font_label_size": 7.5,
    "blank_label_size": 9.0,
    "summary_label_size": 8.5,
    "font_normal": "DenetimArial",
    "font_bold": "DenetimArialBold",
    "font_normal_file": r"C:\Windows\Fonts\arial.ttf",
    "font_bold_file": r"C:\Windows\Fonts\arialbd.ttf",
    "color_line_box": (0, 0, 1),
    "color_image_box": (0.6, 0, 0.8),
    "color_font_label": (0.85, 0.05, 0.05),
    "color_blank_label": (1, 0.35, 0),
    "color_big_gap": (1, 0.45, 0),
    "color_margin": (0, 0.5, 0),
    "color_body_margin": (0, 0.65, 0.65),
    "color_summary_bg": (1, 1, 0.85),
    "color_summary_text": (0, 0.42, 0),
    "color_warning": (0.75, 0, 0),
    "color_rule_ok": (0, 0.45, 0.12),
    "color_rule_check": (0.78, 0.12, 0),
    "rule_label_size": 7.0,
    "left_margin_limit": 75,
    "right_margin_limit": 75,
    "min_text_length": 1,
    "min_distance_pt": 3,
    "max_distance_pt": 250,
    "min_blank_lines_to_show": 0.5,
}

PT_TO_CM = 2.54 / 72
CM_TO_PT = 72 / 2.54


def select_pdf_file():
    if tk is None or filedialog is None:
        return ""
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Analiz edilecek PDF dosyasini secin",
        filetypes=[("PDF dosyalari", "*.pdf")],
    )
    root.destroy()
    return file_path


def r0(value):
    if value is None:
        return ""
    return int(round(value))


def r1(value):
    if value is None:
        return ""
    return round(value, 1)


def cm1(value_pt):
    if value_pt is None:
        return ""
    return round(value_pt * PT_TO_CM, 1)


def approx_line_count(value_pt, cfg):
    nominal_line_pt = max(1.0, cfg["expected_body_font_size"] * cfg["expected_line_spacing"])
    return value_pt / nominal_line_pt


def gap_measure_label(value_pt, cfg):
    if value_pt is None:
        return ""
    return f"{cm1(value_pt)}cm/{r0(value_pt)}px/~{r1(approx_line_count(value_pt, cfg))} satır"


def pt_from_cm(value_cm):
    return value_cm * CM_TO_PT


def clean_font_name(font_name):
    if not font_name:
        return ""
    # PDF subset prefix example: ABCDEE+Calibri-Bold
    if "+" in font_name:
        return font_name.split("+", 1)[1]
    return font_name


def font_is_expected_like(font_name, expected_font):
    name = clean_font_name(font_name).lower().replace(" ", "")
    exp = expected_font.lower().replace(" ", "")
    # Carlito is metric-compatible with Calibri and often used by LaTeX/Linux.
    aliases = [exp]
    if exp == "calibri":
        aliases += ["carlito"]
    return any(alias in name for alias in aliases)


def text_width(text, fontsize, fontname=None):
    fontname = fontname or VIS["font_normal"]
    try:
        return fitz.get_text_length(text, fontname=fontname, fontsize=fontsize)
    except Exception:
        return len(text) * fontsize * 0.55


def ensure_pdf_font(page, fontname):
    font_file = None
    if fontname == VIS["font_normal"]:
        font_file = VIS.get("font_normal_file")
    elif fontname == VIS["font_bold"]:
        font_file = VIS.get("font_bold_file")
    if font_file and Path(font_file).exists():
        try:
            page.insert_font(fontname=fontname, fontfile=font_file)
            return fontname
        except Exception:
            pass
    return "helv" if fontname == VIS["font_normal"] else "hebo"


def safe_insert_text(page, x, y, text, fontsize, color, fontname=None):
    fontname = fontname or VIS["font_normal"]
    fontname = ensure_pdf_font(page, fontname)
    page_width = page.rect.width
    page_height = page.rect.height
    est_width = max(text_width(text, fontsize, fontname), len(text) * fontsize * 0.62)
    x = max(5, min(x, page_width - est_width - 5))
    y = max(12, min(y, page_height - 12))
    page.insert_text(fitz.Point(x, y), text, fontsize=fontsize, color=color, fontname=fontname)


def status_label(status):
    return {
        "ok": "uygun",
        "tolerance": "tolerans içinde",
        "check": "kontrol edilmeli",
        "unknown": "bilinmiyor",
    }.get(status, status)


def status_rank(status):
    return {"ok": 0, "tolerance": 1, "check": 2, "unknown": 1}.get(status, 2)


def combine_status(statuses):
    statuses = [s for s in statuses if s]
    if not statuses:
        return "unknown"
    return max(statuses, key=status_rank)


def combine_status_ignore_unknown(statuses):
    known = [s for s in statuses if s and s != "unknown"]
    if known:
        return combine_status(known)
    return "unknown"


def compare_expected(actual, expected, strict_tol, tol):
    if actual is None:
        return "unknown", None
    diff = actual - expected
    adiff = abs(diff)
    if adiff <= strict_tol:
        return "ok", diff
    if adiff <= tol:
        return "tolerance", diff
    return "check", diff


def get_body_font_size(lines, default_size):
    candidates = []
    for line in lines:
        size = line.get("size")
        if size is None:
            continue
        rounded = r0(size)
        # exclude very large headings; keep likely body and heading-like text
        if 8 <= rounded <= 14:
            candidates.append(rounded)
    if not candidates:
        return default_size
    return Counter(candidates).most_common(1)[0][0]


def estimate_blank_lines_from_visible_gap(visible_gap_pt, body_font_size, line_spacing):
    if visible_gap_pt is None or body_font_size is None:
        return None
    normal_line_height = body_font_size * line_spacing
    if normal_line_height <= 0:
        return None
    return visible_gap_pt / normal_line_height


def choose_side_label_position(page, line, label_width_estimate=105):
    page_width = page.rect.width
    left_space = line["x0"]
    right_space = page_width - line["x1"]
    y = line["y0"] + 2
    if right_space >= VIS["right_margin_limit"]:
        x = line["x1"] + 6
    elif left_space >= VIS["left_margin_limit"]:
        x = line["x0"] - label_width_estimate
    else:
        x = min(line["x1"] + 6, page_width - label_width_estimate) if right_space >= left_space else max(5, line["x0"] - label_width_estimate)
    x = max(5, min(x, page_width - label_width_estimate))
    return x, y


def choose_gap_label_position(page, previous, current, label_width_estimate=125):
    page_width = page.rect.width
    left_space = min(previous["x0"], current["x0"])
    right_space = page_width - max(previous["x1"], current["x1"])
    y_mid = (previous["y1"] + current["y0"]) / 2
    if right_space >= VIS["right_margin_limit"]:
        x = max(previous["x1"], current["x1"]) + 6
    elif left_space >= VIS["left_margin_limit"]:
        x = min(previous["x0"], current["x0"]) - label_width_estimate
    else:
        x = min(max(previous["x1"], current["x1"]) + 6, page_width - label_width_estimate) if right_space >= left_space else max(5, min(previous["x0"], current["x0"]) - label_width_estimate)
    x = max(5, min(x, page_width - label_width_estimate))
    return x, y_mid


def get_margin_values(page, objects):
    if not objects:
        return None
    page_width = page.rect.width
    page_height = page.rect.height
    min_x0 = min(obj["x0"] for obj in objects)
    max_x1 = max(obj["x1"] for obj in objects)
    min_y0 = min(obj["y0"] for obj in objects)
    max_y1 = max(obj["y1"] for obj in objects)
    return {
        "min_x0": min_x0,
        "max_x1": max_x1,
        "min_y0": min_y0,
        "max_y1": max_y1,
        "left": min_x0,
        "right": page_width - max_x1,
        "top": min_y0,
        "bottom": page_height - max_y1,
        "left_cm": cm1(min_x0),
        "right_cm": cm1(page_width - max_x1),
        "top_cm": cm1(min_y0),
        "bottom_cm": cm1(page_height - max_y1),
    }


def body_objects_without_header_footer(page, objects, cfg):
    if not objects:
        return []
    top_band = pt_from_cm(cfg["body_band_top_cm"])
    bottom_band = page.rect.height - pt_from_cm(cfg["body_band_bottom_cm"])
    filtered = []
    for obj in objects:
        cy = (obj["y0"] + obj["y1"]) / 2
        if top_band <= cy <= bottom_band:
            filtered.append(obj)
    return filtered or objects


def margin_side_status(value_cm, cfg):
    """
    Marjin kontrolu.

    Onayli resmi sablon olmadigi icin varsayilan yorum: kılavuzdaki marjin
    degeri minimum bosluk kabul edilir. Yani 2.5 cm bekleniyorsa 3.0 cm
    genellikle ihlal degil; 2.2 cm ise kontrol edilmelidir.

    cfg["margin_check_mode"] == "exact" yapilirsa 2.5 cm civarina gore
    iki yonlu tolerans kontrolu yapilir.
    """
    if value_cm is None:
        return "unknown", None
    expected = cfg["expected_margin_cm"]
    diff = value_cm - expected

    if cfg.get("margin_check_mode", "minimum") == "exact":
        status, diff = compare_expected(
            value_cm,
            expected,
            cfg["tol_margin_strict_cm"],
            cfg["tol_margin_cm"],
        )
        return status, diff

    # Minimum marjin yorumu: fazla bosluk sorun degildir.
    if value_cm >= expected - cfg["tol_margin_strict_cm"]:
        return "ok", diff
    if value_cm >= expected - cfg["tol_margin_cm"]:
        return "tolerance", diff
    return "check", diff


def margins_status_dict(margins, cfg):
    if not margins:
        return {}
    out = {}
    for side in ["left", "right", "top", "bottom"]:
        status, diff = margin_side_status(margins.get(f"{side}_cm"), cfg)
        out[side] = {"status": status, "diff_cm": None if diff is None else r1(diff)}
    return out


def draw_margin_info(page, objects, cfg):
    margins_all = get_margin_values(page, objects)
    if not margins_all:
        return None, None
    body_objs = body_objects_without_header_footer(page, objects, cfg)
    margins_body = get_margin_values(page, body_objs)

    # Full content area (text + images)
    page.draw_rect(
        fitz.Rect(margins_all["min_x0"], margins_all["min_y0"], margins_all["max_x1"], margins_all["max_y1"]),
        color=VIS["color_margin"],
        width=0.8,
    )
    # Estimated body area without header/footer band
    if margins_body and margins_body != margins_all:
        page.draw_rect(
            fitz.Rect(margins_body["min_x0"], margins_body["min_y0"], margins_body["max_x1"], margins_body["max_y1"]),
            color=VIS["color_body_margin"],
            width=0.5,
        )

    page_width, page_height = page.rect.width, page.rect.height
    min_x0, max_x1, min_y0, max_y1 = margins_all["min_x0"], margins_all["max_x1"], margins_all["min_y0"], margins_all["max_y1"]
    page.draw_line(fitz.Point(0, min_y0), fitz.Point(min_x0, min_y0), color=VIS["color_margin"], width=0.8)
    page.draw_line(fitz.Point(max_x1, min_y0), fitz.Point(page_width, min_y0), color=VIS["color_margin"], width=0.8)
    page.draw_line(fitz.Point(min_x0, 0), fitz.Point(min_x0, min_y0), color=VIS["color_margin"], width=0.8)
    page.draw_line(fitz.Point(min_x0, max_y1), fitz.Point(min_x0, page_height), color=VIS["color_margin"], width=0.8)
    return margins_all, margins_body


def collect_font_summary(lines):
    counts = Counter()
    for line in lines:
        counts[f"{line['font']} / {r0(line['size'])} pt"] += 1
    return [f"{key} ({count} satir)" for key, count in counts.most_common()]


def is_likely_body_text_line(text):
    """Filter out math/table/figure/page-number lines before body font checks."""
    text = (text or "").strip()
    if len(text) < 18:
        return False
    if re.fullmatch(r"[ivxlcdmIVXLCDM\d\.\-–—\s]+", text):
        return False
    lower = text.lower()
    if lower.startswith(("tablo ", "çizelge ", "sekil ", "şekil ", "figure ", "table ")):
        return False
    words = [w for w in re.split(r"\s+", text) if w]
    letters_only = [ch for ch in text if ch.isalpha()]
    uppercase_letters = [ch for ch in letters_only if ch.upper() == ch and ch.lower() != ch.upper()]
    if letters_only and len(words) <= 6 and len(uppercase_letters) / len(letters_only) > 0.75:
        return False
    caption_fragment_markers = (
        "tam çözüm",
        "analitik çözüm",
        "nümerik çözüm",
        "parametre değer",
        "karşılaştırılması",
        "gösterimi",
        "hata norm",
    )
    if len(text) < 95 and any(marker in lower for marker in caption_fragment_markers):
        return False
    letters = sum(1 for ch in text if ch.isalpha())
    digits = sum(1 for ch in text if ch.isdigit())
    spaces = sum(1 for ch in text if ch.isspace())
    symbols = len(text) - letters - digits - spaces
    if letters < 10:
        return False
    if symbols > letters * 0.55:
        return False
    math_markers = "∂∑∫∞≤≥≠≈∆αβγθλµνξπΩ"
    if any(ch in text for ch in math_markers) and letters < 35:
        return False
    if len(words) < 4:
        return False
    short_or_numeric = sum(1 for w in words if len(w) <= 2 or any(ch.isdigit() for ch in w))
    if short_or_numeric / len(words) > 0.55:
        return False
    return True


def page_text(lines):
    return " ".join(line.get("text", "") for line in lines).strip()


def is_page_number_text(text):
    return bool(re.fullmatch(r"[ivxlcdmIVXLCDM\d\.\-–—\s]+", (text or "").strip()))


def classify_page(lines, objects, font_check):
    text = page_text(lines)
    has_image = any(obj.get("type") == "image" for obj in objects)
    non_page_lines = [line for line in lines if not is_page_number_text(line.get("text", ""))]

    if not objects:
        return "blank"
    if not non_page_lines and not has_image:
        return "page_number_only"
    if "KABUL ONAY FORMU" in text:
        return "official_form"
    if font_check.get("body_candidate_line_count", 0) == 0:
        return "no_body_text"
    return "regular"


def page_kind_label(kind):
    return {
        "blank": "tamamen boş",
        "page_number_only": "sadece sayfa numarası",
        "official_form": "resmi form sayfası",
        "no_body_text": "gövde metni yok/şekil-tablo ağırlıklı",
        "regular": "normal",
    }.get(kind, kind)


def font_compliance(lines, cfg, body_font_size):
    # Likely body candidates: lines close to estimated body size and longer than 10 chars.
    candidates = []
    for line in lines:
        if line.get("size") is None:
            continue
        size_ok_band = abs(line["size"] - body_font_size) <= 0.75
        if size_ok_band and is_likely_body_text_line(line.get("text", "")):
            candidates.append(line)
    if not candidates:
        candidates = [line for line in lines if line.get("size") is not None and is_likely_body_text_line(line.get("text", ""))]

    total = len(candidates)
    expected_font_lines = [line for line in candidates if font_is_expected_like(line.get("font", ""), cfg["expected_body_font_name"])]

    def size_is_expected_like(line):
        if abs(line.get("size", 0) - cfg["expected_body_font_size"]) <= cfg["tol_font_pt"]:
            return True
        text = (line.get("text") or "").lower()
        math_in_body = any(marker in text for marker in ("l 2", "l ∞", "l∞", "∂", "≤", "≥", "ξ", "θ", "ν"))
        return math_in_body and font_is_expected_like(line.get("font", ""), cfg["expected_body_font_name"])

    expected_size_lines = [line for line in candidates if size_is_expected_like(line)]
    font_ratio = len(expected_font_lines) / total if total else None
    size_ratio = len(expected_size_lines) / total if total else None

    def ratio_status(ratio):
        if ratio is None:
            return "unknown"
        if ratio >= 0.95:
            return "ok"
        if ratio >= 0.85:
            return "tolerance"
        return "check"

    return {
        "body_candidate_line_count": total,
        "expected_font_line_count": len(expected_font_lines),
        "expected_size_line_count": len(expected_size_lines),
        "expected_font_ratio": None if font_ratio is None else r1(100 * font_ratio),
        "expected_size_ratio": None if size_ratio is None else r1(100 * size_ratio),
        "font_status": ratio_status(font_ratio),
        "size_status": ratio_status(size_ratio),
        "samples_non_expected_font": [line["text"][:80] for line in candidates if not font_is_expected_like(line.get("font", ""), cfg["expected_body_font_name"] )][:5],
        "samples_non_expected_size": [line["text"][:80] for line in candidates if not size_is_expected_like(line)][:5],
    }


def is_bold_line(line):
    return any(mark in (line.get("font") or "").lower() for mark in ("bold", "bd", "hebo", "cmbx"))


def clean_heading_text(text):
    return re.sub(r"\s+", " ", (text or "").strip())


def text_is_upper_like(text):
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return True
    upper_letters = sum(1 for ch in letters if ch == ch.upper())
    return upper_letters / max(len(letters), 1) >= 0.92


def cover_title_candidate(text):
    upper = text.upper()
    if len(text) < 8:
        return False
    blocked = (
        "T.C.", "ÜNİVERSİTESİ", "ENSTİTÜSÜ", "TEZİ", "THESIS", "DISSERTATION",
        "ANABİLİM", "PROGRAM", "MALATYA", "DANIŞMAN"
    )
    return text_is_upper_like(text) and not any(item in upper for item in blocked)


def cover_author_candidate(text):
    upper = text.upper()
    if not text_is_upper_like(text) or len(text.split()) < 2:
        return False
    blocked = (
        "TEZ", "THESIS", "DISSERTATION", "ÜNİVERSİTESİ", "ENSTİTÜSÜ", "ANABİLİM",
        "PROGRAM", "MALATYA", "DANIŞMAN", "BAŞLIĞI", "GEREKLİYSE"
    )
    if any(item in upper for item in blocked):
        return False
    return bool(re.search(r"[A-ZÇĞİÖŞÜ]{2,}\s+[A-ZÇĞİÖŞÜ]{2,}", upper))


def is_numbered_heading(text):
    text = clean_heading_text(text)
    return bool(
        re.match(r"^\d+(?:\.\d+){1,3}\.?\s+\S+", text)
        or re.match(r"^\d+\.\s+[A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜçğıöşü\s]{2,}", text)
    )


def heading_level(text):
    match = re.match(r"^(\d+(?:\.\d+){0,3})\.?\s+", clean_heading_text(text))
    if not match:
        return None
    return match.group(1).count(".") + 1


def is_main_heading_line(line):
    text = clean_heading_text(line.get("text", ""))
    normalized = text.upper()
    if normalized in MAIN_HEADING_WORDS and text == normalized:
        return True
    return (
        len(text) >= 4
        and len(text) <= 70
        and normalized == text
        and not is_page_number_text(text)
        and not re.search(r"\d", text)
        and (line.get("size") or 0) >= 13
    )


def page_part_label(part):
    return {
        "cover": "kapak/on sayfa",
        "official": "resmi form",
        "front": "on bolum",
        "main": "ana bilimsel bolum",
        "back": "arka bolum",
        "other": "diger",
    }.get(part, part)


def classify_document_part(page_no, lines, page_kind):
    text = page_text(lines).upper()
    if page_no <= 2:
        return "cover"
    if page_kind == "official_form":
        return "official"
    if any(word in text for word in FRONT_MATTER_WORDS):
        return "front"
    if "KAYNAKÇA" in text or "KAYNAKLAR" in text or "EKLER" in text:
        return "back"
    if any(is_main_heading_line(line) or is_numbered_heading(line.get("text", "")) for line in lines):
        return "main"
    return "other"


def content_lines_for_spacing(lines):
    out = []
    for line in lines:
        text = clean_heading_text(line.get("text", ""))
        if not text or is_page_number_text(text):
            continue
        if len(text) <= 2:
            continue
        out.append(line)
    return out


def spacing_summary(lines, body_font_size, cfg):
    candidates = content_lines_for_spacing(lines)
    if len(candidates) < 2:
        return {
            "line_height_pt": None,
            "line_step_pt": None,
            "line_spacing_ratio": None,
            "approx_blank_enter_avg": None,
            "approx_blank_enter_max": None,
            "large_gap_count": 0,
            "sample_gaps": [],
        }

    heights = [line["height"] for line in candidates if line.get("height")]
    steps = []
    gaps = []
    for previous, current in zip(candidates, candidates[1:]):
        top_to_top = current["y0"] - previous["y0"]
        visible_gap = max(0, current["y0"] - previous["y1"])
        if VIS["min_distance_pt"] <= top_to_top <= VIS["max_distance_pt"]:
            steps.append(top_to_top)
            blank_lines = estimate_blank_lines_from_visible_gap(
                visible_gap,
                body_font_size,
                cfg["expected_line_spacing"],
            )
            if blank_lines is not None:
                gaps.append({
                    "visible_gap_cm": cm1(visible_gap),
                    "approx_blank_enter": r1(blank_lines),
                    "before": previous["text"][:80],
                    "after": current["text"][:80],
                })

    line_height = median(heights) if heights else None
    line_step = median(steps) if steps else None
    normal_line_height = body_font_size * cfg["expected_line_spacing"] if body_font_size else None
    blank_values = [item["approx_blank_enter"] for item in gaps]
    large_gaps = [item for item in gaps if item["approx_blank_enter"] >= 0.7]
    return {
        "line_height_pt": None if line_height is None else r1(line_height),
        "line_step_pt": None if line_step is None else r1(line_step),
        "line_spacing_ratio": None if not line_step or not normal_line_height else r1(line_step / normal_line_height),
        "approx_blank_enter_avg": None if not blank_values else r1(sum(blank_values) / len(blank_values)),
        "approx_blank_enter_max": None if not blank_values else r1(max(blank_values)),
        "large_gap_count": len(large_gaps),
        "sample_gaps": large_gaps[:3],
    }


def check_heading_rules(page, lines, body_font_size, cfg):
    checks = []
    page_center = page.rect.width / 2
    top_limit = pt_from_cm(3.3)
    for line in lines:
        text = clean_heading_text(line.get("text", ""))
        if not text or is_page_number_text(text):
            continue
        size = line.get("size") or 0
        center_delta = abs(((line["x0"] + line["x1"]) / 2) - page_center)

        if is_main_heading_line(line):
            issues = []
            if text.upper() != text:
                issues.append("buyuk harf")
            if abs(size - 14) > 1.0:
                issues.append(f"14 pt yerine {r1(size)} pt")
            if not is_bold_line(line):
                issues.append("kalin degil")
            if center_delta > 35:
                issues.append("ortalama zayif")
            if line["y0"] > top_limit:
                issues.append("sayfa ust satirindan uzak")
            checks.append({
                "kind": "main_heading",
                "text": text[:90],
                "status": "ok" if not issues else "tolerance" if len(issues) <= 1 else "check",
                "notes": issues or ["ana baslik kurallari saglaniyor"],
            })
        elif is_numbered_heading(text):
            level = heading_level(text)
            issues = []
            if level and level > 4:
                issues.append("4. duzeyden ileri")
            if abs(size - cfg["expected_body_font_size"]) > 1.0:
                issues.append(f"11 pt yerine {r1(size)} pt")
            if not is_bold_line(line):
                issues.append("kalin degil")
            checks.append({
                "kind": "numbered_heading",
                "level": level,
                "text": text[:90],
                "status": "ok" if not issues else "tolerance" if len(issues) <= 1 else "check",
                "notes": issues or ["alt baslik kurallari saglaniyor"],
            })
    return checks[:8]


def check_caption_rules(lines):
    checks = []
    for idx, line in enumerate(lines):
        text = clean_heading_text(line.get("text", ""))
        low = text.lower()
        caption_type = None
        if re.match(r"^(şekil|sekil)\s+\d+", low):
            caption_type = "sekil"
        elif re.match(r"^(tablo|çizelge)\s+\d+", low):
            caption_type = "tablo"
        if not caption_type:
            continue
        issues = []
        if (line.get("size") or 0) < 9.5 or (line.get("size") or 0) > 12.5:
            issues.append(f"punto {r1(line.get('size') or 0)}")
        if idx > 0:
            gap_prev = max(0, line["y0"] - lines[idx - 1]["y1"])
            if gap_prev > 45:
                issues.append(f"once bosluk {cm1(gap_prev)} cm")
        if idx < len(lines) - 1:
            gap_next = max(0, lines[idx + 1]["y0"] - line["y1"])
            if gap_next > 45:
                issues.append(f"sonra bosluk {cm1(gap_next)} cm")
        checks.append({
            "kind": caption_type,
            "text": text[:90],
            "status": "ok" if not issues else "tolerance" if len(issues) <= 1 else "check",
            "notes": issues or ["sekil/tablo gosterimi kabul edilebilir"],
        })
    return checks[:8]


def structure_summary_texts(heading_checks, caption_checks, page_part):
    headings = Counter(item["status"] for item in heading_checks)
    captions = Counter(item["status"] for item in caption_checks)
    texts = []
    if page_part == "main" and heading_checks:
        status = "kontrol" if headings.get("check") else "tolerans" if headings.get("tolerance") else "uygun"
        texts.append(f"Basliklar: {status} ({len(heading_checks)} adet)")
    if caption_checks:
        status = "kontrol" if captions.get("check") else "tolerans" if captions.get("tolerance") else "uygun"
        texts.append(f"Sekil/tablo basligi: {status} ({len(caption_checks)} adet)")
    return texts


def spacing_rule_status(actual_pt, expected_pt, cfg):
    diff = actual_pt - expected_pt
    adiff = abs(diff)
    if adiff <= cfg["tol_spacing_pt"]:
        return "ok", diff
    if adiff <= cfg["tol_spacing_pt"] * 2:
        return "tolerance", diff
    return "check", diff


def add_rule(finding_list, page_no, rule_id, title, status, owner, message, location=None, actual=None, expected=None):
    finding_list.append({
        "page": page_no,
        "rule_id": rule_id,
        "title": title,
        "status": status,
        "owner": owner,
        "message": message,
        "location": location,
        "actual": actual,
        "expected": expected,
    })


def line_gap_pt(previous, current):
    return max(0, current["y0"] - previous["y1"])


def gap_location(previous, current):
    return {
        "x0": min(previous["x0"], current["x0"]),
        "x1": max(previous["x1"], current["x1"]),
        "y0": previous["y1"],
        "y1": current["y0"],
    }


def find_line_index(lines, target):
    for idx, line in enumerate(lines):
        if line is target:
            return idx
    return None


def check_cover_rules(page_no, lines, cfg):
    findings = []
    content = [line for line in content_lines_for_spacing(lines) if not is_page_number_text(line.get("text", ""))]
    if not content:
        return findings
    cover_specs = [
        ("cover_title", "Tez adı punto", lambda t: cover_title_candidate(t), 32),
        ("cover_author", "Öğrenci adı punto", lambda t: cover_author_candidate(t), 21),
        ("cover_degree", "Tez türü punto", lambda t: "YÜKSEK LİSANS TEZİ" in t.upper() or "DOKTORA TEZİ" in t.upper(), 26),
        ("cover_degree_en", "İngilizce tez türü punto", lambda t: "MASTER" in t.upper() or "DOCTORAL" in t.upper(), 15),
        ("cover_city_year", "Şehir/yıl punto", lambda t: bool(re.search(r"MALATYA\s*,?\s*\d{4}", t.upper())), 15),
    ]
    if page_no == 1:
        for rule_id, title, predicate, expected_size in cover_specs:
            for line in content:
                text = clean_heading_text(line.get("text", ""))
                if predicate(text):
                    size = line.get("size") or 0
                    status, diff = compare_expected(size, expected_size, cfg["tol_font_pt"], 1.5)
                    if rule_id in {"cover_title", "cover_author", "cover_degree", "cover_degree_en", "cover_city_year"} and not text_is_upper_like(text):
                        status = "check"
                    add_rule(
                        findings,
                        page_no,
                        rule_id,
                        title,
                        status,
                        "template",
                        f"{text[:45]}: {r1(size)} pt; beklenen {expected_size} pt; tüm harfler büyük",
                        location={"x0": line["x0"], "x1": line["x1"], "y0": line["y0"], "y1": line["y1"]},
                        actual=r1(size),
                        expected=expected_size,
                    )
                    break

    # The guide gives cover design through figures. Show measured gaps between every visible cover block.
    key_lines = []
    for line in content:
        text = clean_heading_text(line.get("text", ""))
        upper = text.upper()
        if page_no <= 2 and len(text) >= 2:
            key_lines.append(line)
            add_rule(
                findings,
                page_no,
                "cover_line_style",
                "Kapak satırı font/punto",
                "info",
                "template",
                f"{text[:35]}: {line.get('font','')} {r1(line.get('size') or 0)} pt{' kalın' if is_bold_line(line) else ''}",
                location={"x0": line["x0"], "x1": line["x1"], "y0": line["y0"], "y1": line["y1"]},
                actual=f"{r1(line.get('size') or 0)} pt{' bold' if is_bold_line(line) else ''}",
                expected="Kılavuz şekil düzeni",
            )
            continue
        if (
            "TEZİ" in upper
            or "THESIS" in upper
            or "DISSERTATION" in upper
            or re.search(r"MALATYA\s*,?\s*\d{4}", upper)
            or (upper == text and 2 <= len(text.split()) <= 4 and not any(word in upper for word in ("ÜNİVERSİTESİ", "ENSTİTÜSÜ", "ANABİLİM", "PROGRAM")))
            or "ANABİLİM" in upper
            or "PROGRAM" in upper
        ):
            key_lines.append(line)
    key_lines = sorted(key_lines, key=lambda item: item["y0"])[:18]
    for prev, curr in zip(key_lines, key_lines[1:]):
        gap_pt = line_gap_pt(prev, curr)
        if gap_pt < 8:
            continue
        add_rule(
            findings,
            page_no,
            "cover_visual_gap",
            "Kapak öğeleri arası boşluk",
            "info",
            "template",
            f"{prev['text'][:28]} -> {curr['text'][:28]}: {gap_measure_label(gap_pt, cfg)}",
            location=gap_location(prev, curr),
            actual=gap_measure_label(gap_pt, cfg),
            expected="Şekil 10/11 görsel düzeni",
        )
    return findings


def page_specific_guide_rules(page_no, lines, page_part):
    findings = []
    text = page_text(lines).upper()
    content = content_lines_for_spacing(lines)
    heading = content[0] if content else None

    def add_note(rule_id, title, message, line=None):
        add_rule(findings, page_no, rule_id, title, "info", "template", message, location=None, expected="Kılavuz ölçülebilir madde")

    if "İÇİNDEKİLER" in text:
        add_note(
            "toc_guide",
            "İçindekiler sayfası",
            "Başlık 14 punto kalın ortalı; sonra 1 satır boşluk; ön sayfalar, ana/alt başlıklar, kaynaklar ve ekler sayfa numarasıyla listelenir; 3. dereceden ileri başlık kullanılmaz.",
            heading,
        )
    if "ÖZET" in text or "ABSTRACT" in text:
        add_note(
            "abstract_guide",
            "Özet/Abstract sayfası",
            "Başlık 14 punto kalın ortalı; başlıktan ve tez başlığından sonra 1 satır boşluk; metin 11 punto; en çok 250 kelime; kaynak/şekil/tablo yok; anahtar kelimeler alfabetik olmalı.",
            heading,
        )
    if "SİMGELER" in text or "KISALTMALAR" in text:
        add_note(
            "symbols_guide",
            "Simgeler ve kısaltmalar",
            "Başlık 14 punto kalın ortalı; sonra 1 satır boşluk; dizin 1,25 cm içeriden başlar; satır aralığı 1,5; simge/kısaltmalar 11 punto kalın ve alfabetik olmalıdır.",
            heading,
        )
    if "ŞEKİLLER DİZİNİ" in text:
        add_note(
            "lof_guide",
            "Şekiller dizini",
            "Başlık 14 punto kalın ortalı; sonra 1 satır boşluk; satır aralığı 1,5; açıklamalar tez içindeki başlıklarla aynı olmalı ve taşan satır aynı hizadan devam etmelidir.",
            heading,
        )
    if "TABLOLAR DİZİNİ" in text or "TABLOLAR LİSTESİ" in text:
        add_note(
            "lot_guide",
            "Tablolar dizini",
            "Başlık 14 punto kalın ortalı; sonra 1 satır boşluk; satır aralığı 1,5; açıklamalar tez içindeki tablo başlıklarıyla aynı olmalı ve taşan satır aynı hizadan devam etmelidir.",
            heading,
        )
    if "KAYNAKLAR" in text or "KAYNAKÇA" in text:
        add_note(
            "references_guide",
            "Kaynaklar",
            "KAYNAKLAR başlığı 14 punto büyük harf kalın ortalı; sonra 1 satır boşluk; her kaynak ayrı paragraf, Calibri 11 punto ve 1,5 satır aralığı ile yazılmalıdır.",
            heading,
        )
    if page_part == "official":
        add_note(
            "approval_guide",
            "Kabul-onay formu",
            "Kalite formunun tablo, logo ve üst bilgi görünümü korunur; metinler resmi forma uygun yerleşmelidir.",
            heading,
        )
    return findings


def check_spacing_and_structure_rules(page, page_no, lines, page_part, heading_checks, caption_checks, cfg):
    findings = []
    content = content_lines_for_spacing(lines)
    findings.extend(page_specific_guide_rules(page_no, lines, page_part))
    if page_part == "cover":
        findings.extend(check_cover_rules(page_no, lines, cfg))
        return findings
    if page_part == "official":
        return findings

    index_by_id = {id(line): idx for idx, line in enumerate(content)}
    for check in heading_checks:
        text = check.get("text", "")
        line = next((item for item in content if clean_heading_text(item.get("text", "")) == text), None)
        if not line:
            continue
        if check.get("status") == "check":
            add_rule(
                findings,
                page_no,
                "heading_format",
                "Başlık biçimi",
                "check",
                "author",
                f"{text[:45]}: {', '.join(check.get('notes', []))}",
                location={"x0": line["x0"], "x1": line["x1"], "y0": line["y0"], "y1": line["y1"]},
            )
        idx = index_by_id.get(id(line))
        if idx is None:
            continue
        if check.get("kind") == "main_heading" and idx + 1 < len(content):
            gap_pt = line_gap_pt(line, content[idx + 1])
            status, diff = spacing_rule_status(gap_pt, cfg["expected_heading_after_pt"], cfg)
            add_rule(
                findings,
                page_no,
                "main_heading_after_gap",
                "Ana başlık sonrası boşluk",
                status,
                "template",
                f"{text[:40]} sonrası {gap_measure_label(gap_pt, cfg)}; beklenen yaklaşık 1 satır",
                location=gap_location(line, content[idx + 1]),
                actual=gap_measure_label(gap_pt, cfg),
                expected="1 satır",
            )
        if check.get("kind") == "numbered_heading":
            if idx > 0:
                gap_pt = line_gap_pt(content[idx - 1], line)
                status, diff = spacing_rule_status(gap_pt, cfg["expected_subheading_before_pt"], cfg)
                add_rule(
                    findings,
                    page_no,
                    "subheading_before_gap",
                    "Alt başlık öncesi boşluk",
                    status,
                    "template",
                    f"{text[:40]} öncesi {gap_measure_label(gap_pt, cfg)}; beklenen 12 nk",
                    location=gap_location(content[idx - 1], line),
                    actual=gap_measure_label(gap_pt, cfg),
                    expected="12 nk",
                )
            if idx + 1 < len(content):
                gap_pt = line_gap_pt(line, content[idx + 1])
                status, diff = spacing_rule_status(gap_pt, cfg["expected_subheading_after_pt"], cfg)
                add_rule(
                    findings,
                    page_no,
                    "subheading_after_gap",
                    "Alt başlık sonrası boşluk",
                    status,
                    "template",
                    f"{text[:40]} sonrası {gap_measure_label(gap_pt, cfg)}; beklenen 6 nk",
                    location=gap_location(line, content[idx + 1]),
                    actual=gap_measure_label(gap_pt, cfg),
                    expected="6 nk",
                )

    for cap in caption_checks:
        text = cap.get("text", "")
        line = next((item for item in content if clean_heading_text(item.get("text", "")) == text), None)
        if not line:
            continue
        if cap.get("status") == "check":
            add_rule(
                findings,
                page_no,
                "caption_format",
                "Şekil/tablo başlığı biçimi",
                "check",
                "author",
                f"{text[:45]}: {', '.join(cap.get('notes', []))}",
                location={"x0": line["x0"], "x1": line["x1"], "y0": line["y0"], "y1": line["y1"]},
            )
        idx = index_by_id.get(id(line))
        if idx is not None and idx + 1 < len(content):
            gap_pt = line_gap_pt(line, content[idx + 1])
            expected = cfg["expected_caption_inner_pt"] if cap.get("kind") == "tablo" else cfg["expected_caption_outer_pt"]
            status, diff = spacing_rule_status(gap_pt, expected, cfg)
            add_rule(
                findings,
                page_no,
                "caption_adjacent_gap",
                "Şekil/tablo başlığı boşluğu",
                status,
                "template",
                f"{text[:40]} sonrası {gap_measure_label(gap_pt, cfg)}",
                location=gap_location(line, content[idx + 1]),
                actual=gap_measure_label(gap_pt, cfg),
                expected=f"{expected:g} pt",
            )
    return findings


def draw_rule_annotations(page, rule_findings, cfg):
    for finding in rule_findings:
        always_show = finding.get("rule_id") in {
            "cover_visual_gap",
            "cover_line_style",
            "cover_title",
            "cover_author",
            "cover_degree",
            "cover_degree_en",
            "cover_city_year",
            "main_heading_after_gap",
            "subheading_before_gap",
            "subheading_after_gap",
            "caption_adjacent_gap",
        }
        if finding.get("owner") != "author" and not cfg.get("detailed_pdf") and not always_show:
            continue
        loc = finding.get("location")
        if not loc:
            continue
        status = finding.get("status")
        color = VIS["color_rule_check"] if status == "check" else VIS["color_rule_ok"]
        if status == "info":
            color = VIS["color_font_label"]
        y0, y1 = loc.get("y0"), loc.get("y1")
        if y0 is None or y1 is None or y1 <= y0:
            continue
        cover_point_rules = {"cover_line_style", "cover_title", "cover_author", "cover_degree", "cover_degree_en", "cover_city_year"}
        if finding.get("rule_id") == "cover_line_style":
            x = page.rect.width - 104
        else:
            x = min(max(loc.get("x1", 0) + 6, 8), page.rect.width - 210)
        y = (y0 + y1) / 2
        if finding.get("rule_id") not in cover_point_rules:
            page.draw_line(fitz.Point(loc.get("x0", 8), y), fitz.Point(min(loc.get("x1", page.rect.width - 8), page.rect.width - 8), y), color=color, width=0.6)
        label_title = {
            "cover_visual_gap": "Kapak boşluk",
            "cover_line_style": "Kapak satırı",
            "cover_title": "Tez adı punto",
            "cover_author": "Öğrenci adı punto",
            "cover_degree": "Tez türü punto",
            "cover_degree_en": "İng. tür punto",
            "cover_city_year": "Şehir/yıl punto",
            "toc_guide": "İçindekiler kuralı",
            "abstract_guide": "Özet kuralı",
            "symbols_guide": "Simgeler kuralı",
            "lof_guide": "Şekiller dizini kuralı",
            "lot_guide": "Tablolar dizini kuralı",
            "references_guide": "Kaynaklar kuralı",
            "approval_guide": "Kabul-onay kuralı",
            "main_heading_after_gap": "Ana başlık sonrası boşluk",
            "subheading_before_gap": "Alt başlık öncesi boşluk",
            "subheading_after_gap": "Alt başlık sonrası boşluk",
            "caption_adjacent_gap": "Şekil/tablo boşluk",
            "heading_format": "Başlık biçimi",
            "caption_format": "Şekil/tablo biçimi",
        }.get(finding.get("rule_id"), finding["title"])
        label_value = finding.get("actual") or finding.get("message", "")
        label = f"{label_title}: {label_value}"
        font_size = 5.8 if finding.get("rule_id") == "cover_line_style" else VIS["rule_label_size"]
        if finding.get("rule_id") == "cover_line_style":
            label = label_value
        safe_insert_text(page, x, y - 2, label[:58], font_size, color, VIS["font_bold"])


def rule_summary_texts(rule_findings):
    checks = [item for item in rule_findings if item.get("owner") == "author" and item.get("status") == "check"]
    tolerances = [item for item in rule_findings if item.get("owner") == "author" and item.get("status") == "tolerance"]
    template_checks = [item for item in rule_findings if item.get("owner") == "template" and item.get("status") in ("check", "tolerance")]
    measured = [item for item in rule_findings if item.get("status") == "info"]
    if checks:
        return [f"Kural ihlali: {len(checks)}", "İlk: " + checks[0]["title"][:36]]
    if tolerances:
        return [f"Kural tolerans: {len(tolerances)}"]
    if template_checks:
        return [f"Şablon boşluk/punto kontrolü: {len(template_checks)} bulgu", "Kapakta tez adı 32p, ad soyad 21p, tez türü 26/15p, şehir-yıl 15p olmalıdır."]
    if measured:
        cover_checks = [item for item in rule_findings if item.get("rule_id") in {"cover_title", "cover_author", "cover_degree", "cover_degree_en", "cover_city_year"}]
        if cover_checks:
            return [f"Kapak/ön sayfa ölçümü: {len(measured)} ölçüm", "Kapakta tez adı 32p, ad soyad 21p, tez türü 26/15p, şehir-yıl 15p gösterildi."]
        return [f"Kapak/ön sayfa ölçümü: {len(measured)} ölçüm"]
    return ["Kılavuz kuralı: uygun"]


def guide_summary_texts(rule_findings):
    labels = {
        "toc_guide": "İçindekiler: başlık 14p kalın ortalı; 1 satır boşluk; 3. düzeye kadar.",
        "abstract_guide": "Özet/Abstract: 14p başlık, 11p metin, 250 kelime, kaynak yok.",
        "symbols_guide": "Simgeler: 14p başlık; 1,25 cm girinti; 11p kalın, alfabetik.",
        "lof_guide": "Şekiller dizini: 14p başlık; 1,5 aralık; açıklama/sayfa no aynı hizada.",
        "lot_guide": "Tablolar dizini: 14p başlık; 1,5 aralık; açıklama/sayfa no aynı hizada.",
        "references_guide": "Kaynaklar: 14p başlık; 1 satır boşluk; 11p Calibri, 1,5 aralık.",
        "approval_guide": "Kabul-onay: resmi formun tablo, logo ve üst bilgi görünümü korunur.",
    }
    out = []
    seen = set()
    for finding in rule_findings:
        rule_id = finding.get("rule_id")
        if rule_id in labels and rule_id not in seen:
            out.append(labels[rule_id])
            seen.add(rule_id)
    return out


def draw_summary_box(page, margins_all, margins_body, font_summary, body_font_size, page_no, page_status, cfg, spacing=None, page_part=None, heading_checks=None, caption_checks=None, rule_findings=None):
    if not margins_all:
        return
    st = status_label(page_status).upper()
    mb = margins_body or margins_all
    spacing = spacing or {}
    page_part = page_part or "other"
    heading_checks = heading_checks or []
    caption_checks = caption_checks or []
    rule_findings = rule_findings or []
    summary_lines = [
        (f"Sayfa {page_no} - {st}", "title"),
        (f"Bölüm: {page_part_label(page_part)}", "normal"),
        (f"Gövde: sol {mb['left_cm']} | sağ {mb['right_cm']} cm", "normal"),
        (f"Gövde: üst {mb['top_cm']} | alt {mb['bottom_cm']} cm", "normal"),
        (f"Tüm içerik: alt {margins_all['bottom_cm']} cm (sayfa no dahil)", "normal"),
        ("Sayfa no alt bilgidir.", "normal"),
        ("Gövde marjini metinden ölçülür.", "normal"),
    ]
    if spacing.get("line_height_pt") is not None and cfg.get("detailed_pdf"):
        summary_lines.extend([
            (f"Satır yüksekliği: yaklaşık {spacing['line_height_pt']} pt", "normal"),
            (f"Satır aralığı: yaklaşık {spacing['line_spacing_ratio']}x", "normal"),
            (f"Boşluk/Enter: ort. {spacing['approx_blank_enter_avg']} | en çok {spacing['approx_blank_enter_max']}", "normal"),
        ])
    elif page_part in ("cover", "front", "official"):
        summary_lines.append(("Ön sayfa boşlukları sayfa üzerinde tek tek gösterilir.", "normal"))
    else:
        summary_lines.append(("Satır aralığı: ölçülemedi", "normal"))
    summary_lines.extend((text, "normal") for text in guide_summary_texts(rule_findings)[:2])
    summary_lines.extend((text, "normal") for text in structure_summary_texts(heading_checks, caption_checks, page_part))
    summary_lines.extend((text, "normal") for text in rule_summary_texts(rule_findings))

    if page_part in ("front", "back", "other") and spacing.get("large_gap_count"):
        summary_lines.append((f"Buyuk bosluk adedi: {spacing['large_gap_count']}", "normal"))
    if cfg.get("detailed_pdf"):
        summary_lines.extend([
            (f"Beklenen: marjin {cfg['expected_margin_cm']} cm; gövde {cfg['expected_body_font_name']} {cfg['expected_body_font_size']} pt", "normal"),
            (f"Boşluk hesabı: gövde {body_font_size} pt, aralık {cfg['expected_line_spacing']}", "normal"),
            ("Fontlar:", "title"),
        ])
        for item in font_summary[:4]:
            summary_lines.append((item, "fontline"))
    summary_lines = summary_lines[:VIS["max_summary_lines"]]

    if page_part != "cover" and not cfg.get("detailed_pdf"):
        structure_bits = structure_summary_texts(heading_checks, caption_checks, page_part)
        summary_lines = [
            (
                f"Sayfa {page_no} - {st} | Bölüm: {page_part_label(page_part)} | Gövde Ü/A {mb['top_cm']}/{mb['bottom_cm']} cm",
                "title",
            ),
            ("Sayfa no alt bilgidir; gövde marjini metin/şekil/tablo alanından ölçülür.", "normal"),
        ]
        if page_part in ("front", "back", "other") and spacing.get("large_gap_count"):
            summary_lines.append((f"Belirgin dikey boşluk: {spacing['large_gap_count']} yerde ölçüldü", "normal"))
        summary_lines.extend((item, "normal") for item in guide_summary_texts(rule_findings)[:2])
        summary_lines.extend((item, "normal") for item in structure_bits[:2])
        summary_lines.extend((item, "normal") for item in rule_summary_texts(rule_findings)[:2])

    x0, y0 = 8, 8
    pad_x, pad_y, line_gap = 8, 8, 3
    max_w = 0
    total_h = 0
    for text, style in summary_lines:
        fontname = VIS["font_bold"] if style in ("title", "fontline") else VIS["font_normal"]
        fontsize = VIS["summary_label_size"]
        max_w = max(max_w, text_width(text, fontsize, fontname))
        total_h += fontsize + line_gap
    if page_part != "cover" and not cfg.get("detailed_pdf"):
        box_width = page.rect.width - 16
    else:
        box_width = min(max(max_w + 2 * pad_x, page.rect.width * 0.42), page.rect.width - 16)
    box_height = min(total_h + 2 * pad_y - line_gap, page.rect.height - 16)
    body_top = (margins_body or margins_all).get("min_y0", margins_all.get("min_y0", 0))
    if page_part not in ("cover", "front", "main", "back", "other") and body_top < y0 + box_height + 12:
        y0 = max(8, page.rect.height - box_height - 8)
    rect = fitz.Rect(x0, y0, x0 + box_width, y0 + box_height)
    page.draw_rect(rect, color=VIS["color_margin"], fill=VIS["color_summary_bg"], width=0.8)

    current_y = y0 + pad_y + VIS["summary_label_size"]
    for text, style in summary_lines:
        fontname = VIS["font_bold"] if style in ("title", "fontline") else VIS["font_normal"]
        color = VIS["color_font_label"] if style == "fontline" else VIS["color_summary_text"]
        if style == "title" and page_status == "check":
            color = VIS["color_warning"]
        safe_insert_text(page, x0 + pad_x, current_y, text, VIS["summary_label_size"], color, fontname)
        current_y += VIS["summary_label_size"] + line_gap


def open_pdf_default_viewer(pdf_path):
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(pdf_path))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(pdf_path)], check=False)
        else:
            subprocess.run(["xdg-open", str(pdf_path)], check=False)
    except Exception as e:
        print(f"PDF otomatik acilamadi: {e}")


def extract_page_objects(page):
    data = page.get_text("dict")
    lines = []
    objects = []
    for block in data.get("blocks", []):
        block_type = block.get("type")
        if block_type == 0 and "lines" in block:
            for line in block["lines"]:
                text_parts, fonts, sizes = [], [], []
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if text:
                        text_parts.append(text)
                        fonts.append(clean_font_name(span.get("font", "")))
                        if span.get("size") is not None:
                            sizes.append(span.get("size"))
                if not text_parts:
                    continue
                text_line = " ".join(text_parts).strip()
                if len(text_line) < VIS["min_text_length"]:
                    continue
                unique_fonts = list(dict.fromkeys(fonts))
                font_text = ", ".join(unique_fonts)
                avg_size = sum(sizes) / len(sizes) if sizes else None
                x0, y0, x1, y1 = line["bbox"]
                obj = {
                    "type": "text",
                    "text": text_line,
                    "font": font_text,
                    "size": avg_size,
                    "x0": x0,
                    "y0": y0,
                    "x1": x1,
                    "y1": y1,
                    "height": y1 - y0,
                }
                lines.append(obj)
                objects.append(obj)
        elif block_type == 1:
            x0, y0, x1, y1 = block["bbox"]
            objects.append({"type": "image", "x0": x0, "y0": y0, "x1": x1, "y1": y1})
    lines.sort(key=lambda item: item["y0"])
    return lines, objects


def annotate_page(page, lines, margins_all, margins_body, body_font_size, cfg):
    previous = None
    gap_records = []
    for line in lines:
        if VIS["show_line_boxes"]:
            page.draw_rect(fitz.Rect(line["x0"], line["y0"], line["x1"], line["y1"]), color=VIS["color_line_box"], width=0.3)
        if VIS["show_font_labels"]:
            show_label = True
            if VIS["compact_mode"] and previous is not None:
                prev_label = f"{previous['font']} / {r0(previous['size'])} pt"
                curr_label = f"{line['font']} / {r0(line['size'])} pt"
                show_label = curr_label != prev_label
            if show_label:
                label = f"{line['font']} / {r0(line['size'])} pt"
                label_width = text_width(label, VIS["font_label_size"], VIS["font_bold"]) + 8
                x, y = choose_side_label_position(page, line, label_width)
                safe_insert_text(page, x, y, label, VIS["font_label_size"], VIS["color_font_label"], VIS["font_bold"])

        if previous is not None and VIS["show_blank_labels"]:
            visible_gap = max(0, line["y0"] - previous["y1"])
            top_to_top = line["y0"] - previous["y0"]
            if VIS["min_distance_pt"] <= top_to_top <= VIS["max_distance_pt"]:
                blank_lines = estimate_blank_lines_from_visible_gap(visible_gap, body_font_size, cfg["expected_line_spacing"])
                if blank_lines is not None and blank_lines >= VIS["min_blank_lines_to_show"]:
                    gap_cm = cm1(visible_gap)
                    rounded = round(blank_lines)
                    label = f"bosluk {gap_cm} cm | yakl. {rounded} satir"
                    color = VIS["color_big_gap"] if blank_lines >= 1.5 else VIS["color_blank_label"]
                    label_width = text_width(label, VIS["blank_label_size"], VIS["font_bold"]) + 8
                    x, y = choose_gap_label_position(page, previous, line, label_width)
                    safe_insert_text(page, x, y, label, VIS["blank_label_size"], color, VIS["font_bold"])
                    gap_records.append({
                        "between": [previous["text"][:100], line["text"][:100]],
                        "visible_gap_cm": gap_cm,
                        "approx_blank_lines": r1(blank_lines),
                    })
        previous = line
    return gap_records


def analyze_pdf(pdf_file, out_dir=None, cfg=None, auto_open=True):
    cfg = {**DEFAULT_CONFIG, **(cfg or {})}
    pdf_path = Path(pdf_file)
    if out_dir is None:
        out_dir = Path(__file__).resolve().parent
    else:
        out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_pdf = out_dir / f"{pdf_path.stem}_kilavuz_uygunluk_isaretli.pdf"
    out_json = out_dir / f"{pdf_path.stem}_kilavuz_uygunluk_rapor.json"
    out_md = out_dir / f"{pdf_path.stem}_kilavuz_uygunluk_rapor.md"

    doc = fitz.open(pdf_path)
    report = {
        "input_pdf": str(pdf_path),
        "output_pdf": str(out_pdf),
        "reference": "Inonu Universitesi Lisansustu Tez Yazim Kilavuzu; onayli Word/LaTeX sablon bulunmadigi icin kilavuzdaki olculebilir kurallar esas alinmistir.",
        "config": cfg,
        "method_note": "PDF metin ve gorsel nesne koordinatlari esas alinir. Marjinler sayfa kenari ile gorunen ilk/son nesne siniri arasidir. Font/punto PDF metin katmanindan alinir. Bosluk/satir analizi gorunen dikey mesafeye dayali yaklasik yorumdur; kaynak dosyada kac Enter kullanildigini kesin gostermez.",
        "pages": [],
    }

    for page_index, page in enumerate(doc, start=1):
        lines, objects = extract_page_objects(page)

        # draw image boxes after extracting objects so they don't affect extraction
        if VIS["show_image_boxes"]:
            for obj in objects:
                if obj.get("type") == "image":
                    page.draw_rect(fitz.Rect(obj["x0"], obj["y0"], obj["x1"], obj["y1"]), color=VIS["color_image_box"], width=0.8)

        body_font_size = get_body_font_size(lines, cfg["expected_body_font_size"])
        margins_all = margins_body = None
        if VIS["show_margins"]:
            margins_all, margins_body = draw_margin_info(page, objects, cfg)

        font_summary_list = collect_font_summary(lines)
        font_check = font_compliance(lines, cfg, body_font_size)

        page_w_cm = cm1(page.rect.width)
        page_h_cm = cm1(page.rect.height)
        w_status, w_diff = compare_expected(page_w_cm, cfg["expected_page_width_cm"], cfg["tol_page_cm"], cfg["tol_page_cm"])
        h_status, h_diff = compare_expected(page_h_cm, cfg["expected_page_height_cm"], cfg["tol_page_cm"], cfg["tol_page_cm"])

        margin_all_status = margins_status_dict(margins_all, cfg) if margins_all else {}
        margin_body_status = margins_status_dict(margins_body, cfg) if margins_body else {}

        page_kind = classify_page(lines, objects, font_check)
        margin_statuses = [v["status"] for v in (margin_body_status or margin_all_status).values()]
        if page_kind == "blank":
            page_status = "unknown"
        elif page_kind == "page_number_only":
            page_status = "check"
        elif page_kind == "official_form":
            page_status = combine_status_ignore_unknown([w_status, h_status])
        elif page_kind == "no_body_text":
            page_status = combine_status_ignore_unknown([w_status, h_status] + margin_statuses)
        else:
            pre_statuses = [w_status, h_status, font_check["font_status"], font_check["size_status"]]
            pre_statuses += margin_statuses
            page_status = combine_status(pre_statuses)

        page_part = classify_document_part(page_index, lines, page_kind)
        spacing = spacing_summary(lines, body_font_size, cfg)
        heading_checks = check_heading_rules(page, lines, body_font_size, cfg)
        caption_checks = check_caption_rules(lines)
        rule_findings = check_spacing_and_structure_rules(page, page_index, lines, page_part, heading_checks, caption_checks, cfg)
        rule_statuses = [
            item.get("status")
            for item in rule_findings
            if item.get("owner") == "author" and item.get("status") != "info"
        ]
        if rule_statuses:
            page_status = combine_status([page_status] + rule_statuses)
        draw_rule_annotations(page, rule_findings, cfg)

        if VIS["show_summary_box"]:
            draw_summary_box(
                page,
                margins_all,
                margins_body,
                font_summary_list,
                body_font_size,
                page_index,
                page_status,
                cfg,
                spacing=spacing,
                page_part=page_part,
                heading_checks=heading_checks,
                caption_checks=caption_checks,
                rule_findings=rule_findings,
            )

        gap_records = annotate_page(page, lines, margins_all, margins_body, body_font_size, cfg)

        page_record = {
            "page": page_index,
            "overall_status": page_status,
            "page_kind": page_kind,
            "page_part": page_part,
            "page_size_cm": {"width": page_w_cm, "height": page_h_cm},
            "page_size_check": {
                "expected_width_cm": cfg["expected_page_width_cm"],
                "expected_height_cm": cfg["expected_page_height_cm"],
                "width_status": w_status,
                "height_status": h_status,
                "width_diff_cm": r1(w_diff),
                "height_diff_cm": r1(h_diff),
            },
            "margins_all_cm": None,
            "margins_body_cm": None,
            "margins_all_check": margin_all_status,
            "margins_body_check": margin_body_status,
            "font_summary": dict(Counter({item.rsplit(" (", 1)[0]: int(item.rsplit("(", 1)[1].split()[0]) for item in font_summary_list}).most_common(10)) if font_summary_list else {},
            "body_font_size_estimate": body_font_size,
            "body_font_check": font_check,
            "spacing_check": spacing,
            "heading_checks": heading_checks,
            "caption_checks": caption_checks,
            "rule_findings": rule_findings,
            "gaps": gap_records[:25],
        }
        if margins_all:
            page_record["margins_all_cm"] = {k: margins_all[f"{k}_cm"] for k in ["left", "right", "top", "bottom"]}
        if margins_body:
            page_record["margins_body_cm"] = {k: margins_body[f"{k}_cm"] for k in ["left", "right", "top", "bottom"]}
        report["pages"].append(page_record)

    try:
        doc.save(out_pdf)
    except Exception as exc:
        if "Permission denied" not in str(exc) and "cannot remove file" not in str(exc):
            raise
        fallback_pdf = out_dir / f"{pdf_path.stem}_kilavuz_uygunluk_isaretli_{datetime.now().strftime('%Y%m%d-%H%M%S')}.pdf"
        doc.save(fallback_pdf)
        out_pdf = fallback_pdf
        report["output_pdf"] = str(out_pdf)
    doc.close()

    # Overall summary
    status_counts = Counter(p["overall_status"] for p in report["pages"])
    page_kind_counts = Counter(p["page_kind"] for p in report["pages"])
    page_part_counts = Counter(p.get("page_part", "other") for p in report["pages"])
    report["summary"] = {
        "page_count": len(report["pages"]),
        "status_counts": dict(status_counts),
        "page_kind_counts": dict(page_kind_counts),
        "page_part_counts": dict(page_part_counts),
        "blank_page_count": page_kind_counts.get("blank", 0),
        "page_number_only_count": page_kind_counts.get("page_number_only", 0),
        "overall_status": combine_status([p["overall_status"] for p in report["pages"]]),
    }

    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown_report(report, out_md)
    if auto_open:
        open_pdf_default_viewer(out_pdf)
    return out_pdf, out_json, out_md


def md_status(status):
    label = status_label(status)
    if status == "ok":
        return f"✅ {label}"
    if status == "tolerance":
        return f"⚠️ {label}"
    if status == "check":
        return f"❗ {label}"
    return f"? {label}"


def format_margin_status(check):
    if not check:
        return ""
    parts = []
    for side_tr, side in [("sol", "left"), ("sağ", "right"), ("üst", "top"), ("alt", "bottom")]:
        entry = check.get(side, {})
        diff = entry.get("diff_cm")
        diff_s = "" if diff is None else f" ({diff:+.1f})"
        parts.append(f"{side_tr}: {status_label(entry.get('status'))}{diff_s}")
    return "; ".join(parts)


def write_markdown_report(report, out_md):
    cfg = report["config"]
    lines = []
    lines.append("# Tez PDF Kılavuz Uygunluk Ön Denetim Raporu\n\n")
    lines.append(f"**Girdi PDF:** `{report['input_pdf']}`  \n")
    lines.append(f"**İşaretlenmiş PDF:** `{report['output_pdf']}`  \n")
    lines.append(f"**Genel durum:** {md_status(report['summary']['overall_status'])}\n\n")
    lines.append("## Esas alınan ölçülebilir kılavuz değerleri\n\n")
    lines.append("| Ölçüt | Beklenen değer | Tolerans |\n")
    lines.append("|---|---:|---:|\n")
    lines.append(f"| Sayfa boyutu | {cfg['expected_page_width_cm']} x {cfg['expected_page_height_cm']} cm | ±{cfg['tol_page_cm']} cm |\n")
    margin_rule = "en az" if cfg.get("margin_check_mode", "minimum") == "minimum" else "yaklaşık"
    lines.append(f"| Kenar boşluğu | {margin_rule} {cfg['expected_margin_cm']} cm | minimum modda fazla boşluk ihlal sayılmaz; eksik boşlukta tolerans ±{cfg['tol_margin_cm']} cm |\n")
    lines.append(f"| Ana/gövde yazı tipi | {cfg['expected_body_font_name']} | sayfa içi gövde adayı satırlarda oran kontrolü |\n")
    lines.append(f"| Ana/gövde punto | {cfg['expected_body_font_size']} pt | ±{cfg['tol_font_pt']} pt |\n")
    lines.append(f"| Satır/boşluk yorumu | {cfg['expected_line_spacing']} satır aralığı esaslı | yaklaşık |\n")
    lines.append("| Başlık ve şekil/tablo yorumu | Kılavuz s. 10-11, Şekil 3-5 ve başlık kuralları | PDF'den ölçülebilen hizalama, punto, kalınlık ve boşluk göstergeleri |\n\n")

    lines.append("## Yöntem notu\n\n")
    lines.append(
        "Bu ön denetim PDF içindeki metin ve görsel nesne koordinatlarına dayanır. "
        "Kenar boşluğu değerlendirmesinde ana ölçüt gövde metni ve şekil/tablo alanıdır; "
        "sayfa numarası alt bilgide yer aldığı için ayrıca gösterilir ve gövde alt marjiniyle aynı kabul edilmez. "
        "Matematiksel ifadelerde kullanılan özel matematik fontları Calibri zorunluluğu kapsamında ayrıca kusur olarak raporlanmaz; "
        "font kontrolü yalnızca ana/gövde metni aday satırlarına uygulanır. "
        "Satır aralığı ve boşluk ölçümleri PDF çıktısından yaklaşık olarak yorumlanır; kaynak dosyada kaç Enter veya manuel boşluk kullanıldığı PDF'den kesin belirlenemez. "
        "Başlık, şekil ve tablo kontrolleri kılavuzun 10-11. sayfalarındaki Şekil 3, Şekil 4, Şekil 5 ile başlık/alt başlık maddelerinin PDF'de ölçülebilen karşılıklarına göre raporlanır.\n\n"
    )

    lines.append("## Genel özet\n\n")
    sc = report["summary"]["status_counts"]
    kc = report["summary"].get("page_kind_counts", {})
    pc = report["summary"].get("page_part_counts", {})
    lines.append(f"- Toplam sayfa: **{report['summary']['page_count']}**\n")
    lines.append(f"- Uygun: **{sc.get('ok', 0)}**\n")
    lines.append(f"- Tolerans içinde: **{sc.get('tolerance', 0)}**\n")
    lines.append(f"- Kontrol edilmeli: **{sc.get('check', 0)}**\n")
    lines.append(f"- Bilinmiyor/ölçülemeyen: **{sc.get('unknown', 0)}**\n")
    lines.append(f"- Tamamen boş sayfa: **{kc.get('blank', 0)}**\n")
    lines.append(f"- Sadece sayfa numarası bulunan sayfa: **{kc.get('page_number_only', 0)}**\n")
    lines.append(f"- Gövde metni olmayan şekil/tablo ağırlıklı sayfa: **{kc.get('no_body_text', 0)}**\n")
    lines.append(f"- Resmi form sayfası: **{kc.get('official_form', 0)}**\n\n")
    lines.append("### Sayfa bölümü dağılımı\n\n")
    for part in ["cover", "official", "front", "main", "back", "other"]:
        if pc.get(part, 0):
            lines.append(f"- {page_part_label(part)}: **{pc.get(part, 0)}**\n")
    lines.append("\n")

    lines.append("## Kurul için kısa yorum\n\n")
    lines.append(
        "- Bu tez çıktısında tamamen boş sayfa ve yalnız sayfa numarası bulunan sayfa tespit edilmemiştir.\n"
        "- Üst marjinlerde 2.5 cm yerine 2.6-2.7 cm görülen sayfalar, kılavuzdaki kenar boşluğu şartı en az 2.5 cm olarak yorumlandığında ihlal değildir.\n"
        "- Alt marjinde 1.1 cm görünen değer, çoğu sayfada sayfa numarasının alt bilgi konumundan kaynaklanır; ana metin/gövde alt boşluğu ayrı hesaplanmıştır.\n"
        "- Şekil, tablo, kaynakça ve matematik yoğun sayfalarda PDF metin katmanının font/punto bilgisi yanıltıcı olabildiğinden, denetim ana gövde metni aday satırlarıyla sınırlandırılmıştır.\n"
        "- İşaretli PDF'de her sayfa için satır yüksekliği, yaklaşık satır aralığı ve yaklaşık boş satır/Enter bilgisi kısa özet olarak gösterilmiştir.\n"
        "- Ana bilimsel bölümlerde başlıkların; şekil ve tablo bulunan sayfalarda ise şekil/tablo başlıklarının kılavuzdaki ölçülebilir kurallara yakınlığı ayrıca özetlenmiştir.\n\n"
    )

    lines.append("## Satır aralığı, başlık ve şekil/tablo kontrolleri\n\n")
    lines.append("| Sayfa | Bölüm | Satır yüksekliği | Satır aralığı | Yakl. boş satır/Enter | Başlık özeti | Şekil/tablo özeti |\n")
    lines.append("|---:|---|---:|---:|---:|---|---|\n")
    for p in report["pages"]:
        sp = p.get("spacing_check") or {}
        heading_summary = ", ".join(structure_summary_texts(p.get("heading_checks", []), [], p.get("page_part"))) or "-"
        caption_summary = ", ".join(structure_summary_texts([], p.get("caption_checks", []), p.get("page_part"))) or "-"
        lines.append(
            f"| {p['page']} | {page_part_label(p.get('page_part'))} | "
            f"{sp.get('line_height_pt', '')} | {sp.get('line_spacing_ratio', '')} | "
            f"{sp.get('approx_blank_enter_max', '')} | {heading_summary} | {caption_summary} |\n"
        )
    lines.append("\n")

    all_rules = [finding for p in report["pages"] for finding in p.get("rule_findings", [])]
    author_rules = [item for item in all_rules if item.get("owner") == "author" and item.get("status") in ("check", "tolerance")]
    template_rules = [item for item in all_rules if item.get("owner") == "template" and item.get("status") in ("check", "tolerance")]
    measured_rules = [item for item in all_rules if item.get("status") == "info"]
    lines.append("## Kılavuz kural bulguları\n\n")
    lines.append(
        "Bulgular iki sorumluluk alanında gösterilir: öğrenci/yazar kontrolündeki içerik ve kullanım tercihleri ile şablonun otomatik uygulaması gereken biçim kuralları. "
        "Kapak gibi özel sayfalarda kılavuz şekillerinden görülebilen öğeler arası boşluklar ayrıca ölçüm bilgisi olarak verilir.\n\n"
    )
    lines.append(f"- Öğrenci/yazar kontrolündeki bulgu: **{len(author_rules)}**\n")
    lines.append(f"- Şablon kontrolündeki bulgu: **{len(template_rules)}**\n")
    lines.append(f"- Özel sayfa ölçüm bilgisi: **{len(measured_rules)}**\n\n")

    if author_rules:
        lines.append("### Öğrencinin kontrol edebileceği bulgular\n\n")
        lines.append("| Sayfa | Kural | Durum | Açıklama |\n")
        lines.append("|---:|---|---|---|\n")
        for item in author_rules[:80]:
            lines.append(f"| {item['page']} | {item['title']} | {md_status(item['status'])} | {item['message']} |\n")
        lines.append("\n")
    if template_rules:
        lines.append("### Şablon/biçim ayarıyla düzeltilmesi gereken bulgular\n\n")
        lines.append("| Sayfa | Kural | Durum | Açıklama |\n")
        lines.append("|---:|---|---|---|\n")
        for item in template_rules[:120]:
            lines.append(f"| {item['page']} | {item['title']} | {md_status(item['status'])} | {item['message']} |\n")
        lines.append("\n")
    if measured_rules:
        lines.append("### Özel sayfalarda ölçülen boşluklar\n\n")
        lines.append("| Sayfa | Ölçüm | Değer | Açıklama |\n")
        lines.append("|---:|---|---:|---|\n")
        for item in measured_rules[:60]:
            lines.append(f"| {item['page']} | {item['title']} | {item.get('actual', '')} | {item['message']} |\n")
        lines.append("\n")

    tolerance_pages = [p for p in report["pages"] if p["overall_status"] == "tolerance"]
    lines.append("## Tolerans içinde kalan sayfalar\n\n")
    if tolerance_pages:
        lines.append("| Sayfa | Tür | Gövde marjini (sol-sağ-üst-alt cm) | Açıklama |\n")
        lines.append("|---:|---|---|---|\n")
        for p in tolerance_pages:
            mb = p.get("margins_body_cm") or {}
            mb_s = "-".join(str(mb.get(k, "")) for k in ["left", "right", "top", "bottom"])
            note = "Ölçüm kabul edilebilir tolerans aralığında."
            if p.get("page_kind") == "no_body_text":
                note = "Şekil/tablo/kaynakça ağırlıklı sayfa; ana gövde metni sınırlı."
            lines.append(f"| {p['page']} | {page_kind_label(p.get('page_kind'))} | {mb_s} | {note} |\n")
        lines.append("\n")
    else:
        lines.append("Tolerans içinde kalan sayfa bulunmadı.\n\n")

    lines.append("## Sayfa bazlı teknik özet\n\n")
    lines.append("| Sayfa | Tür | Genel durum | Gövde marjini (sol-sağ-üst-alt cm) | Sayfa no dahil alt boşluk |\n")
    lines.append("|---:|---|---|---|---:|\n")
    for p in report["pages"]:
        ma = p.get("margins_all_cm") or {}
        mb = p.get("margins_body_cm") or {}
        mb_s = "-".join(str(mb.get(k, "")) for k in ["left", "right", "top", "bottom"])
        lines.append(f"| {p['page']} | {page_kind_label(p.get('page_kind'))} | {md_status(p['overall_status'])} | {mb_s} | {ma.get('bottom', '')} cm |\n")

    lines.append("\n## Kontrol gerektiren sayfalar\n\n")
    any_check = False
    for p in report["pages"]:
        if p["overall_status"] != "check":
            continue
        any_check = True
        lines.append(f"### Sayfa {p['page']}\n\n")
        lines.append(f"- Sayfa türü: {page_kind_label(p.get('page_kind'))}\n")
        lines.append(f"- Genel durum: {md_status(p['overall_status'])}\n")
        if p.get("margins_body_check"):
            lines.append(f"- Gövde marjini durumu: {format_margin_status(p['margins_body_check'])}\n")
        elif p.get("margins_all_check"):
            lines.append(f"- Tüm içerik marjini durumu: {format_margin_status(p['margins_all_check'])}\n")
        fc = p["body_font_check"]
        if fc["font_status"] == "check":
            lines.append(f"- Font kontrolü: {status_label(fc['font_status'])}; beklenen font oranı {fc['expected_font_ratio']}%. Örnekler: {', '.join(fc['samples_non_expected_font'][:3])}\n")
        if fc["size_status"] == "check":
            lines.append(f"- Punto kontrolü: {status_label(fc['size_status'])}; beklenen punto oranı {fc['expected_size_ratio']}%. Örnekler: {', '.join(fc['samples_non_expected_size'][:3])}\n")
        if p.get("gaps"):
            lines.append(f"- Önemli dikey boşluk kaydı: {len(p['gaps'])} adet. PDF üzerindeki cm değerleri esas alınmalıdır.\n")
        lines.append("\n")
    if not any_check:
        lines.append("Kontrol gerektiren sayfa bulunmadı.\n")

    lines.append("\n## Kısa açıklama\n\n")
    lines.append(
        "Bu rapor, şablonun tez yazım kılavuzuna ne kadar yaklaştığını göstermek için hazırlanmış teknik bir ölçüm çıktısıdır. Kenar boşlukları varsayılan olarak minimum boşluk şartı şeklinde yorumlanmıştır; fazla boşluk tek başına ihlal sayılmamıştır. "
        "Amaç, dönüştürülen tezlerde şablon kaynaklı biçim sorunlarını görünür kılmak ve şablonu kabul edilebilir toleranslarla kılavuza yaklaştırmaktır.\n"
    )
    out_md.write_text("".join(lines), encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(description="PDF tez yazim kilavuzu uygunluk on denetim araci")
    parser.add_argument("--pdf", help="Analiz edilecek PDF dosyasi. Verilmezse dosya secme penceresi acilir.")
    parser.add_argument("--out-dir", help="Cikti klasoru. Varsayilan: scriptin bulundugu klasor.")
    parser.add_argument("--no-open", action="store_true", help="Cikti PDF'yi otomatik acma.")
    parser.add_argument("--expected-margin", type=float, default=DEFAULT_CONFIG["expected_margin_cm"], help="Beklenen marjin cm.")
    parser.add_argument("--expected-font", default=DEFAULT_CONFIG["expected_body_font_name"], help="Beklenen govde font adi.")
    parser.add_argument("--expected-size", type=float, default=DEFAULT_CONFIG["expected_body_font_size"], help="Beklenen govde puntosu.")
    parser.add_argument("--line-spacing", type=float, default=DEFAULT_CONFIG["expected_line_spacing"], help="Bosluk yorumunda kullanilacak satir araligi.")
    parser.add_argument("--exact-margin", action="store_true", help="Marjinleri minimum deger yerine tam 2.5 cm civari olarak denetle. Resmi sablon yoksa genellikle kullanilmaz.")
    parser.add_argument("--detailed-pdf", action="store_true", help="PDF uzerinde satir kutusu, font etiketi ve ayrintili isaretleme goster.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    pdf_file = args.pdf or select_pdf_file()
    if not pdf_file:
        print("PDF secilmedi. Islem iptal edildi.")
        raise SystemExit
    cfg = {
        "expected_margin_cm": args.expected_margin,
        "expected_body_font_name": args.expected_font,
        "expected_body_font_size": args.expected_size,
        "expected_line_spacing": args.line_spacing,
        "margin_check_mode": "exact" if args.exact_margin else "minimum",
        "detailed_pdf": args.detailed_pdf,
    }
    if args.detailed_pdf:
        VIS["show_line_boxes"] = True
        VIS["show_font_labels"] = True
        VIS["show_blank_labels"] = True
        VIS["show_image_boxes"] = True
    out_pdf, out_json, out_md = analyze_pdf(pdf_file, out_dir=args.out_dir, cfg=cfg, auto_open=not args.no_open)
    print("Tamamlandi.")
    print(f"Cikti PDF: {out_pdf}")
    print(f"Rapor JSON: {out_json}")
    print(f"Rapor MD: {out_md}")
