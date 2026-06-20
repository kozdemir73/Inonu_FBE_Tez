import argparse
import re
import unicodedata
from pathlib import Path


ENTRY_RE = re.compile(r"@(?P<type>\w+)\s*\{\s*(?P<key>[^,\s]+)\s*,(?P<body>.*?)(?=^\s*@|\Z)", re.S | re.M)
FIELD_RE = re.compile(r"(?P<name>\w+)\s*=\s*(?P<value>\{(?:[^{}]|\{[^{}]*\})*\}|\"[^\"]*\"|[^,\n]+)\s*,?", re.S)


def read_text(path):
    for encoding in ("utf-8-sig", "utf-8", "cp1254", "latin-1"):
        try:
            return Path(path).read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return Path(path).read_text(errors="replace")


def clean_field(value):
    value = value.strip().rstrip(",").strip()
    if (value.startswith("{") and value.endswith("}")) or (value.startswith('"') and value.endswith('"')):
        value = value[1:-1]
    return re.sub(r"\s+", " ", value).strip()


def parse_entries(path):
    text = read_text(path)
    entries = []
    for match in ENTRY_RE.finditer(text):
        fields = {}
        for field in FIELD_RE.finditer(match.group("body")):
            fields[field.group("name").lower()] = clean_field(field.group("value"))
        entries.append({
            "type": match.group("type"),
            "key": match.group("key"),
            "fields": fields,
            "raw": match.group(0).strip(),
        })
    return entries


def first_author_surname(author):
    first = re.split(r"\s+and\s+|&| ve ", author or "", maxsplit=1, flags=re.I)[0].strip()
    if "," in first:
        surname = first.split(",", 1)[0]
    else:
        first = re.sub(r"^(?:[A-Z]\.)+", "", first).strip()
        parts = first.split()
        surname = parts[-1] if parts else ""
    surname = re.sub(r"[^A-Za-zÇĞİÖŞÜçğıöşü-]", "", surname)
    surname = ascii_key_part(surname)
    return surname[:1].upper() + surname[1:]


def ascii_key_part(value):
    mapping = str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")
    value = value.translate(mapping)
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Za-z0-9-]", "", value)


def base_key(entry):
    fields = entry["fields"]
    surname = first_author_surname(fields.get("author") or fields.get("editor"))
    year_match = re.search(r"\d{4}", fields.get("year", "") or fields.get("date", ""))
    if not surname or not year_match:
        return ""
    return f"{surname}{year_match.group(0)}"


def assign_standard_keys(entries):
    counts = {}
    result = {}
    for entry in entries:
        base = base_key(entry)
        if not base:
            result[entry["key"]] = ""
            continue
        count = counts.get(base, 0)
        counts[base] = count + 1
        suffix = "" if count == 0 else chr(ord("a") + count - 1)
        result[entry["key"]] = base + suffix
    return result


def format_entry(entry, key):
    fields = entry["fields"]
    order = ["author", "editor", "year", "date", "title", "journaltitle", "journal", "booktitle", "publisher", "volume", "number", "pages", "doi", "url"]
    lines = [f"@{entry['type']}{{{key},"]
    used = set()
    for name in order:
        if name in fields:
            lines.append(f"  {name} = {{{fields[name]}}},")
            used.add(name)
    for name in sorted(fields):
        if name not in used:
            lines.append(f"  {name} = {{{fields[name]}}},")
    lines.append("}")
    return "\n".join(lines)


def lint_entries(entries):
    standard = assign_standard_keys(entries)
    issues = []
    for entry in entries:
        fields = entry["fields"]
        missing = [name for name in ("author", "year", "title") if not fields.get(name)]
        if missing:
            issues.append((entry["key"], "Eksik alan: " + ", ".join(missing)))
        expected = standard.get(entry["key"])
        if expected and entry["key"] != expected:
            issues.append((entry["key"], f"Anahtar önerisi: {expected}"))
    return issues, standard


def merge_pool(source_bib, pool_bib):
    source_entries = parse_entries(source_bib)
    pool_path = Path(pool_bib)
    pool_entries = parse_entries(pool_path) if pool_path.exists() else []
    all_entries = pool_entries + source_entries
    standard = assign_standard_keys(all_entries)
    existing_fingerprints = {
        (entry["fields"].get("author", "").casefold(), entry["fields"].get("year", ""), entry["fields"].get("title", "").casefold())
        for entry in pool_entries
    }
    merged = []
    for entry in source_entries:
        fingerprint = (entry["fields"].get("author", "").casefold(), entry["fields"].get("year", ""), entry["fields"].get("title", "").casefold())
        if fingerprint in existing_fingerprints:
            continue
        merged.append(entry)
        existing_fingerprints.add(fingerprint)
    if not merged:
        return 0
    pool_path.parent.mkdir(parents=True, exist_ok=True)
    entries = pool_entries + merged
    keys = assign_standard_keys(entries)
    text = "\n\n".join(format_entry(entry, keys.get(entry["key"]) or entry["key"]) for entry in entries) + "\n"
    pool_path.write_text(text, encoding="utf-8")
    return len(merged)


def main():
    parser = argparse.ArgumentParser(description="BibTeX kaynaklarını denetler ve bölüm havuzuna aktarır.")
    parser.add_argument("bib", help="Denetlenecek .bib dosyası")
    parser.add_argument("--pool", help="Birleştirilecek bölüm havuzu .bib dosyası")
    args = parser.parse_args()
    entries = parse_entries(args.bib)
    issues, standard = lint_entries(entries)
    print(f"Kaynak sayısı: {len(entries)}")
    for key, message in issues:
        print(f"- {key}: {message}")
    if args.pool:
        added = merge_pool(args.bib, args.pool)
        print(f"Havuza eklenen yeni kaynak: {added}")


if __name__ == "__main__":
    main()
