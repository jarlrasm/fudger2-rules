"""Adds a PDF to a built-in library and gives each item a reference to the
page where its name stands on a line of its own (or on two lines, wrapped).

    python3 tools/pdf_references.py --pdf systems/daggerheart/Daggerheart-SRD.pdf \\
        --key srd --name "Daggerheart SRD 1.0" --url /systems/daggerheart/Daggerheart-SRD.pdf \\
        --pages "Weapons=60-75" systems/daggerheart/daggerheart.json

--pages limits where a type's items are looked for (PDF page numbers, as
pdftotext counts them). --prefix also accepts a line that starts with the
name (followed by a space, full stop or colon), for items listed in table
rows or run into their text. --label gives text that may stand before a
name, such as "Extra:". Items found on no page keep a reference
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
parser.add_argument("--label", action="append", default=[], help="Type=text that may stand before a name, such as Extras=Extra: ")
parser.add_argument("--entry", action="append", default=[], help="Type=regex that the text after a name (the rest of its line and the next line) must match, to tell an entry from a mention in a list")
parser.add_argument("--aliases", help="a JSON file of item name to other names to look for, such as the heading a variant is listed under")
parser.add_argument("--only", help="look only for items whose description contains this text, such as the source they came from")
parser.add_argument("--skip-missing", action="store_true", help="give no reference to items not found in this PDF")
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


ALIASES = json.load(open(args.aliases, encoding="utf-8")) if args.aliases else {}


ENTRIES = {spec.partition("=")[0]: re.compile(spec.partition("=")[2], re.I) for spec in args.entry}


def page_of(entity, book, limits):
    names = [entity["name"]] + ALIASES.get(entity["name"], [])
    entry = ENTRIES.get(entity["type"])
    if entry:
        for name in names:
            found = page_for(name, entity, book, limits, entry)
            if found:
                return found
    for name in names:
        found = page_for(name, entity, book, limits)
        if found:
            return found
    return None


def entry_at(lines, index, name, entry):
    """Whether the text after the name at this line looks like the entry
    itself rather than a mention in a list or table."""
    rest = lines[index][len(name):] if lines[index].startswith(name) else ""
    following = lines[index + 1] if index + 1 < len(lines) else ""
    return bool(entry.match(rest + "\n" + following))


def page_for(item_name, entity, book, limits, entry=None):
    name = normal(item_name)
    first, last = limits.get(entity["type"], (1, len(book)))
    prefix = entity["type"] in args.prefix
    labels = [normal(spec.partition("=")[2]) + " " for spec in args.label if spec.partition("=")[0] == entity["type"]]
    wanted = [name] + [label + name for label in labels]
    for number in range(first, min(last, len(book)) + 1):
        lines = book[number - 1]
        if entry:
            for index, line in enumerate(lines):
                if any(line.startswith(w) for w in wanted) and entry_at(lines, index, next(w for w in wanted if line.startswith(w)), entry):
                    return number
            continue
        # A long name in a narrow column wraps onto the next line.
        for line in lines + [a + " " + b for a, b in zip(lines, lines[1:])]:
            line = line.rstrip("*").rstrip()
            if line in wanted or (prefix and any(line.startswith(w + end) for w in wanted for end in (" ", ".", ":"))):
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
                if args.only and args.only not in entity.get("description", ""):
                    continue
                page = page_of(entity, book, limits)
                reference = {"document": args.key}
                if page:
                    reference["page"] = page
                    placed[entity["type"]] = placed.get(entity["type"], 0) + 1
                else:
                    missing.append(f"{entity['type']}: {entity['name']}")
                    if args.skip_missing:
                        continue
                others = [r for r in entity.get("references", []) if r.get("document") != args.key]
                entity["references"] = others + [reference]
        write(path, original, library)
        print(path, placed, f"{len(missing)} without a page")
        for item in missing[:40]:
            print("  no page:", item)


main()
