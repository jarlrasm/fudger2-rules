"""Adds a PDF to a built-in library and gives each item a reference to the
page where its name stands on a line of its own (or on two lines, wrapped).

    python3 tools/pdf_references.py --pdf systems/daggerheart/Daggerheart-SRD.pdf \\
        --key srd --name "Daggerheart SRD 1.0" --url /systems/daggerheart/Daggerheart-SRD.pdf \\
        --pages "Weapons=60-75" systems/daggerheart/daggerheart.json

--pages limits where a type's items are looked for (PDF page numbers, as
pdftotext counts them). --prefix also accepts a line that starts with the
name, for items listed in table rows. Items found on no page keep a reference
to the document without a page. With --document-only the library only gets
the document. tools/srd_references.py does the same for the DnD SRD 5.2.1,
whose layout needs more rules.
"""

import argparse
import json
import re
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--pdf", required=True)
parser.add_argument("--key", required=True)
parser.add_argument("--name", required=True)
parser.add_argument("--url", required=True)
parser.add_argument("--pages", action="append", default=[], help="Type=first-last")
parser.add_argument("--prefix", action="append", default=[], help="a type whose items may start a line")
parser.add_argument("--document-only", action="store_true")
parser.add_argument("libraries", nargs="+")
args = parser.parse_args()


def normal(text):
    text = text.replace("’", "'").replace("‘", "'").replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text).strip().lower()


def pages():
    out = subprocess.run(["pdftotext", args.pdf, "-"], capture_output=True, text=True, check=True).stdout
    return [[normal(line) for line in page.split("\n") if line.strip()] for page in out.split("\f")]


def ranges():
    found = {}
    for spec in args.pages:
        kind, _, span = spec.rpartition("=")
        first, _, last = span.partition("-")
        found[kind] = (int(first), int(last or first))
    return found


def page_of(entity, book, limits):
    name = normal(entity["name"])
    first, last = limits.get(entity["type"], (1, len(book)))
    prefix = entity["type"] in args.prefix
    for number in range(first, min(last, len(book)) + 1):
        lines = book[number - 1]
        # A long name in a narrow column wraps onto the next line.
        for line in lines + [a + " " + b for a, b in zip(lines, lines[1:])]:
            if line == name or (prefix and line.startswith(name + " ")):
                return number
    return None


def write(path, original, library):
    if original.startswith("{\n"):
        out = json.dumps(library, indent=1, ensure_ascii=False) + "\n"
    else:
        out = json.dumps(library, ensure_ascii=False)
    open(path, "w", encoding="utf-8").write(out)


def main():
    book = [] if args.document_only else pages()
    limits = ranges()
    document = {"key": args.key, "name": args.name, "url": args.url, "public": True}
    for path in args.libraries:
        original = open(path, encoding="utf-8").read()
        library = json.loads(original)
        library["documents"] = [d for d in library.get("documents", []) if d["key"] != args.key] + [document]
        placed, missing = {}, []
        if not args.document_only:
            for entity in library["entities"]:
                page = page_of(entity, book, limits)
                reference = {"document": args.key}
                if page:
                    reference["page"] = page
                    placed[entity["type"]] = placed.get(entity["type"], 0) + 1
                else:
                    missing.append(f"{entity['type']}: {entity['name']}")
                others = [r for r in entity.get("references", []) if r.get("document") != args.key]
                entity["references"] = others + [reference]
        write(path, original, library)
        print(path, placed, f"{len(missing)} without a page")
        for item in missing[:40]:
            print("  no page:", item)


main()
