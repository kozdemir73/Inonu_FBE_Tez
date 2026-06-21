import filecmp
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


TEMPLATE_DIR_NAME = "inonu-fbe-tez-sablonu-2025"
CORE_TEMPLATE_FILES = [
    "inonutez.cls",
    "kabul-onay.tex",
]
EXPECTED_SYMBOLS_TABULAR = r"\begin{tabular}{@{}p{3cm}l@{}}"
SIMPLE_SUPPORT_MACROS = {
    "ondalikayirici": "nokta",
    "sayfaduzeni": "tek",
}
CONTENT_MACROS = {
    "tesekkur": "tesekkur",
    "onsoz": "onsoz",
    "ozet": "ozet",
    "summary": "abstract",
    "sembollistesi": "semboller",
    "kisaltmalistesi": "kisaltmalar",
    "ozgecmis": "ozgecmis",
}


@dataclass
class RepairItem:
    severity: str
    file: str
    message: str
    changed: bool = False


def read_text(path):
    return Path(path).read_text(encoding="utf-8-sig", errors="replace")


def write_text(path, text):
    Path(path).write_text(text, encoding="utf-8", newline="")


def canonical_template_dir():
    return Path(__file__).resolve().parent / TEMPLATE_DIR_NAME


def parse_two_macro_arguments(line, macro):
    start = line.find("\\" + macro)
    if start < 0:
        return None
    pos = start + len(macro) + 1
    values = []
    while pos < len(line) and len(values) < 2:
        while pos < len(line) and line[pos].isspace():
            pos += 1
        if pos >= len(line) or line[pos] not in "{[":
            return None
        opener = line[pos]
        pos += 1
        current = []
        while pos < len(line):
            char = line[pos]
            if char in "}]" and (pos == 0 or line[pos - 1] != "\\"):
                values.append("".join(current))
                pos += 1
                break
            current.append(char)
            pos += 1
        else:
            return None
    return values if len(values) == 2 else None


def repair_yazar_macro(workdir, dry_run=False):
    path = Path(workdir) / "tez.tex"
    if not path.exists():
        return []
    lines = read_text(path).splitlines()
    changed = False
    items = []
    for index, line in enumerate(lines):
        if not re.match(r"\s*\\yazar\b", line):
            continue
        args = parse_two_macro_arguments(line, "yazar")
        if args is None:
            items.append(RepairItem("UYARI", "tez.tex", r"\yazar{Ad}{SOYAD} satırı okunamadı; kullanıcı bilgileri belirsiz olduğu için otomatik onarılmadı."))
            continue
        repaired = r"\yazar{" + args[0].strip() + "}{" + args[1].strip() + "}"
        if line.strip() != repaired:
            lines[index] = repaired
            changed = True
            severity = "ONARILACAK" if dry_run else "ONARILDI"
            items.append(RepairItem(severity, "tez.tex", r"\yazar makro iskeleti düzeltildi; ad ve soyad içeriği korundu.", True))
    if changed and not dry_run:
        write_text(path, "\n".join(lines) + "\n")
    return items


def repair_symbols_tabular(workdir, dry_run=False):
    path = Path(workdir) / "simgeler-ve-kisaltmalar.tex"
    if not path.exists():
        return []
    text = read_text(path)
    items = []
    begin_pattern = re.compile(r"\\begin\{tabular\}\{[^{}\n]*(?:\{[^{}\n]*\}[^{}\n]*)*\}")
    match = begin_pattern.search(text)
    if not match:
        items.append(RepairItem("UYARI", path.name, "Simgeler ve kısaltmalar tablosunun başlangıcı bulunamadı; elle kontrol edilmeli."))
        return items
    if match.group(0) != EXPECTED_SYMBOLS_TABULAR:
        text = text[:match.start()] + EXPECTED_SYMBOLS_TABULAR + text[match.end():]
        severity = "ONARILACAK" if dry_run else "ONARILDI"
        items.append(RepairItem(severity, path.name, "Simgeler ve kısaltmalar tablosunun sütun kalıbı şablondaki güvenli değere döndürüldü.", True))
    if r"\end{tabular}" not in text:
        text = text.rstrip() + "\n\\end{tabular}\n"
        severity = "ONARILACAK" if dry_run else "ONARILDI"
        items.append(RepairItem(severity, path.name, "Eksik tabular kapanışı eklendi.", True))
    if any(item.changed for item in items) and not dry_run:
        write_text(path, text)
    return items


def repair_simple_macro_order(workdir, dry_run=False):
    path = Path(workdir) / "tez.tex"
    if not path.exists():
        return []
    text = read_text(path)
    original = text
    values = {}
    for macro, default in SIMPLE_SUPPORT_MACROS.items():
        match = re.search(rf"\\{macro}\s*\{{([^{{}}]*)\}}", text)
        values[macro] = match.group(1).strip() if match else default
        support = rf"\providecommand{{\{macro}}}[1]{{}}"
        text = re.sub(rf"^\s*{re.escape(support)}\s*$\r?\n?", "", text, flags=re.M)
        text = re.sub(rf"^\s*\\{macro}\s*\{{[^{{}}]*\}}\s*$\r?\n?", "", text, flags=re.M)
    block_lines = []
    for macro in SIMPLE_SUPPORT_MACROS:
        block_lines.append(rf"\providecommand{{\{macro}}}[1]{{}}")
    for macro in SIMPLE_SUPPORT_MACROS:
        block_lines.append(rf"\{macro}{{{values[macro]}}}")
    block = "\n".join(block_lines) + "\n\n"
    text = re.sub(
        r"(\\documentclass\[[^\]]*\]\{inonutez\}\s*)",
        lambda match: match.group(1) + "\n" + block,
        text,
        count=1,
    )
    if text != original:
        if not dry_run:
            write_text(path, text)
        severity = "ONARILACAK" if dry_run else "ONARILDI"
        return [RepairItem(severity, "tez.tex", r"Destek makroları doğru sıraya alındı: önce \providecommand, sonra seçilen değerler.", True)]
    return []


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
        if stripped in {r"\begin{document}", r"\end{document}", r"\\", r"\raggedleft"}:
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip() + "\n"


def ensure_content_macro(text, macro, include_target):
    replacement = rf"\{macro}" + r"{\input{" + include_target + r"}}"
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if re.match(rf"\s*\\{macro}\b", line):
            lines[index] = replacement
            return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    marker = r"\etikbeyan"
    for index, line in enumerate(lines):
        if marker in line:
            lines.insert(index + 1, replacement)
            return "\n".join(lines) + "\n"
    for index, line in enumerate(lines):
        if r"\begin{document}" in line:
            lines.insert(index, replacement)
            return "\n".join(lines) + "\n"
    lines.append(replacement)
    return "\n".join(lines) + "\n"


def ensure_empty_macro(text, macro):
    replacement = rf"\{macro}" + "{}"
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if re.match(rf"\s*\\{macro}\b", line):
            lines[index] = replacement
            return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    return text


def repair_embedded_document_inputs(workdir, dry_run=False):
    workdir = Path(workdir)
    tex_path = workdir / "tez.tex"
    if not tex_path.exists():
        return []
    text = read_text(tex_path)
    original = text
    items = []
    for macro, stem in CONTENT_MACROS.items():
        source = workdir / f"{stem}.tex"
        target_stem = f"{stem}_body"
        target = workdir / f"{target_stem}.tex"
        include_target = f"{target_stem}.tex" if target.exists() else f"{stem}.tex"
        if source.exists():
            source_text = read_text(source)
            if "\\documentclass" in source_text or "\\begin{document}" in source_text:
                body = extract_document_body(source_text)
                if not dry_run:
                    write_text(target, body)
                include_target = f"{target_stem}.tex"
                severity = "ONARILACAK" if dry_run else "ONARILDI"
                items.append(RepairItem(severity, target.name, f"{source.name} tam belge olduğu için yalnız gövde metni çıkarıldı.", True))
        if macro == "ozgecmis" and not (workdir / include_target).exists() and (workdir / "ozgecmis_body.tex").exists():
            include_target = "ozgecmis_body.tex"
        if (workdir / include_target).exists():
            text = ensure_content_macro(text, macro, include_target)
        elif macro in {"kisaltmalistesi", "sembollistesi"}:
            text = ensure_empty_macro(text, macro)
    if text != original:
        if not dry_run:
            write_text(tex_path, text)
        severity = "ONARILACAK" if dry_run else "ONARILDI"
        items.append(RepairItem(severity, "tez.tex", "Önsöz/özet/abstract/özgeçmiş girişleri gövde dosyalarına yönlendirildi.", True))
    return items


def repair_chapter_inputs(workdir, dry_run=False):
    path = Path(workdir) / "tez.tex"
    if not path.exists():
        return []
    lines = read_text(path).splitlines()
    updated = []
    removed = 0
    for line in lines:
        match = re.match(r"\s*\\input\{?(bolum\d+)\.tex\}?\s*$", line)
        if match and (Path(workdir) / f"{match.group(1)}.tex").exists():
            removed += 1
            continue
        updated.append(line)
    if removed:
        if not dry_run:
            write_text(path, "\n".join(updated) + "\n")
        severity = "ONARILACAK" if dry_run else "ONARILDI"
        return [RepairItem(severity, "tez.tex", f"Tam belge bölüm dosyaları için {removed} doğrudan input satırı kaldırıldı; includedocskip satırları kullanılacak.", True)]
    return []


def split_author_value(value):
    value = re.sub(r"\s*&\s*", " and ", value.strip())
    value = re.sub(r"\s+ve\s+", " and ", value, flags=re.I)
    chunks = re.split(r"\s+and\s+", value) if re.search(r"\s+and\s+", value) else [value]
    authors = []
    for chunk in chunks:
        chunk = chunk.strip().strip(",")
        if not chunk:
            continue
        authors.extend(split_comma_author_chunk(chunk))
    return authors


def split_comma_author_chunk(value):
    parts = [part.strip().strip(",") for part in value.split(",") if part.strip().strip(",")]
    if len(parts) <= 2:
        return [value.strip().strip(",")]
    authors = []
    index = 0
    while index < len(parts):
        surname = parts[index]
        if index + 1 < len(parts) and is_initial_or_given_name(parts[index + 1]):
            authors.append(f"{surname}, {parts[index + 1]}")
            index += 2
        else:
            authors.append(surname)
            index += 1
    return authors


def is_initial_or_given_name(value):
    value = value.strip()
    return bool(re.match(r"^[A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜçğıöşü.\s-]*\.?$", value))


def normalize_author_value(value):
    authors = split_author_value(value)
    return " and ".join(authors)


def repair_bibliography(workdir, dry_run=False):
    items = []
    for path in sorted(Path(workdir).glob("*.bib")):
        text = read_text(path)
        original = text

        def author_repl(match):
            value = match.group(1)
            fixed = normalize_author_value(value)
            return "author = {" + fixed + "}"

        text = re.sub(r"author\s*=\s*\{([^{}]*(?:&|,\s*[^{}]*,| ve )[^{}]*)\}", author_repl, text, flags=re.I)
        text = re.sub(r"month\s*=\s*([A-Za-z]+)\s*,", lambda match: "month = {" + match.group(1) + "},", text, flags=re.I)
        if text != original:
            if not dry_run:
                write_text(path, text)
            severity = "ONARILACAK" if dry_run else "ONARILDI"
            items.append(RepairItem(severity, path.name, "BibTeX yazar ayırıcıları ve çıplak ay adları Biber uyumlu biçime getirildi.", True))
    return items


def repair_core_template_files(workdir, baseline_dir=None, dry_run=False):
    workdir = Path(workdir)
    baseline_dir = Path(baseline_dir) if baseline_dir else canonical_template_dir()
    items = []
    if workdir.resolve() == baseline_dir.resolve():
        return items
    for rel in CORE_TEMPLATE_FILES:
        source = baseline_dir / rel
        target = workdir / rel
        if not source.exists() or not target.exists():
            continue
        if filecmp.cmp(source, target, shallow=False):
            continue
        if not dry_run:
            shutil.copy2(source, target)
        severity = "ONARILACAK" if dry_run else "ONARILDI"
        items.append(RepairItem(severity, rel, "Şablon çekirdek dosyası güncel şablondaki güvenli kopyayla eşitlendi.", True))
    localtexmf_cls = workdir / "system" / "localtexmf" / "tex" / "latex" / "inonutez.cls"
    source_cls = baseline_dir / "inonutez.cls"
    if source_cls.exists() and localtexmf_cls.exists() and not filecmp.cmp(source_cls, localtexmf_cls, shallow=False):
        if not dry_run:
            shutil.copy2(source_cls, localtexmf_cls)
        severity = "ONARILACAK" if dry_run else "ONARILDI"
        items.append(RepairItem(severity, str(localtexmf_cls.relative_to(workdir)), "Eski localtexmf şablon kopyası güncel inonutez.cls ile eşitlendi.", True))
    return items


def repair_workdir(workdir, baseline_dir=None, dry_run=False):
    workdir = Path(workdir)
    items = []
    items.extend(repair_simple_macro_order(workdir, dry_run=dry_run))
    items.extend(repair_embedded_document_inputs(workdir, dry_run=dry_run))
    items.extend(repair_chapter_inputs(workdir, dry_run=dry_run))
    items.extend(repair_bibliography(workdir, dry_run=dry_run))
    items.extend(repair_yazar_macro(workdir, dry_run=dry_run))
    items.extend(repair_symbols_tabular(workdir, dry_run=dry_run))
    items.extend(repair_core_template_files(workdir, baseline_dir=baseline_dir, dry_run=dry_run))
    if not items:
        items.append(RepairItem("OK", ".", "Korunan şablon iskeletinde onarım gerektiren bir sorun bulunmadı.", False))
    return items


def items_to_text(items):
    return "\n".join(f"[{item.severity}] {item.file}: {item.message}" for item in items)
