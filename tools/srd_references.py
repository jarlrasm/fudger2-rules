import json
import re
import subprocess
import sys
from collections import Counter

# Adds the SRD 5.2.1 PDF to library JSON files and gives every item a
# reference to its page.
# Usage: srd_references.py systems/DND/SRD_CC_v5.2.1.pdf library.json...
# Page numbers printed in SRD 5.2.1 are the same as the PDF's own pages.

PDF = sys.argv[1]
LIBRARIES = sys.argv[2:]
DOCUMENT = {
    "key": "srd",
    "name": "SRD 5.2.1",
    "url": "/systems/DND/SRD_CC_v5.2.1.pdf",
    "public": True,
}
# The first page after the table of contents.
BODY = 5

# Where each type's headings start, as a table of contents entry, and the
# entry after the last page to search.
SECTIONS = {
    "Spells": ("Spell Descriptions", "Rules Glossary"),
    "Creature": ("Monsters A–Z", None),
    "Feats": ("Feat Descriptions", "Equipment"),
    "Melee weapons": ("Weapons", "Armor"),
    "Ranged weapons": ("Weapons", "Armor"),
    "Armour": ("Armor", "Tools"),
    "Other items": ("Armor", "Tools"),
}

# Types listed in tables, where a row starts with the item's name.
TABLES = {"Melee weapons", "Ranged weapons", "Armour", "Other items"}


def text(first=None, last=None):
    pages = ["-f", str(first), "-l", str(last)] if first else []
    out = subprocess.run(["pdftotext", *pages, PDF, "-"], capture_output=True, text=True, check=True)
    return out.stdout


def normal(name):
    name = name.replace("’", "'").replace("‘", "'").replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", name).strip().lower()


def contents():
    toc = {}
    for name, page in re.findall(r"([A-Z][^.\n]*?)\s*\.+\s*(\d+)", text(2, 4)):
        toc.setdefault(normal(name), int(page))
    return toc


def pages():
    return [[normal(line) for line in page.split("\n")] for page in text().split("\f")]


def first_page(book, wanted, first=BODY, last=10_000):
    for number, lines in enumerate(book, start=1):
        if first <= number < last and any(wanted(line) for line in lines):
            return number
    return None


def section_page(type_, wanted, toc, book):
    start, end = SECTIONS[type_]
    if normal(start) not in toc:
        return None
    return first_page(book, wanted, toc[normal(start)], toc[normal(end)] if end else 10_000)


def subclass_page(name, toc, book):
    match = re.fullmatch(r"(.+) \((.+)\)", name)
    if not match:
        return None
    sub = normal(match.group(2))
    pages = [page for entry, page in toc.items() if entry.endswith(sub)]
    heading = normal(match.group(1)) + " subclass:"
    return min(pages) if pages else first_page(book, lambda line: line.startswith(heading))


def page_of(entity, toc, book):
    name = normal(entity["name"])
    heading = lambda line: line == name
    found = None
    if entity["type"] in TABLES:
        found = section_page(entity["type"], lambda line: line == name or line.startswith(name + " "), toc, book)
    elif entity["type"] in SECTIONS:
        found = section_page(entity["type"], heading, toc, book)
    return found or toc.get(name) or subclass_page(entity["name"], toc, book) or first_page(book, heading)


def write(path, original, library):
    if original.startswith("{\n"):
        out = json.dumps(library, indent=1) + "\n"
    else:
        out = json.dumps(library, ensure_ascii=False)
    open(path, "w").write(out)


def main():
    toc = contents()
    book = pages()
    for path in LIBRARIES:
        original = open(path).read()
        library = json.loads(original)
        library["documents"] = [DOCUMENT]
        placed = Counter()
        missing = []
        for entity in library["entities"]:
            page = page_of(entity, toc, book)
            reference = {"document": DOCUMENT["key"]}
            if page:
                reference["page"] = page
                placed[entity["type"]] += 1
            else:
                missing.append(f"{entity['type']}: {entity['name']}")
            entity["references"] = [reference]
        write(path, original, library)
        print(path, dict(placed))
        for item in missing:
            print("  no page:", item)


main()
