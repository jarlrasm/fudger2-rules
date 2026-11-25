"""Builds the Ars Magica 5th edition spell library from the Open License text.

Atlas Games released the text of Ars Magica 5th Edition under the Creative
Commons Attribution-ShareAlike 4.0 International license (https://atlas-games.com/openarm).
OriginalMadman keeps a checked Markdown version of the core rulebook at
https://github.com/OriginalMadman/Ars-Magica-Open-License (CC BY-SA 4.0). This
reads its "reviewed/Ars Magica 5e - Core Rules.md" and takes every formulaic
and ritual spell of the Spells chapter: a level-five heading, the Arts and
level, Range, Duration and Target, any requisites, and the text with its
level breakdown.

    python3 -I tools/arm5_import.py "<checkout>/reviewed/Ars Magica 5e - Core Rules.md" systems/arm5/arm5.json
"""

import json
import re
import sys
from pathlib import Path

SOURCE = Path(sys.argv[1])
OUT = sys.argv[2]
SYSTEM = "ArsMagica"
COMMIT = "5384ec89ff2c9c201157b1df346f5d84b9452272"

TECHNIQUES = {"Cr": "Creo", "In": "Intellego", "Mu": "Muto", "Pe": "Perdo", "Re": "Rego"}
FORMS = {"An": "Animal", "Aq": "Aquam", "Au": "Auram", "Co": "Corpus", "He": "Herbam", "Ig": "Ignem",
         "Im": "Imaginem", "Me": "Mentem", "Te": "Terram", "Vi": "Vim"}

ARTS = re.compile(r"^(Cr|In|Mu|Pe|Re)(An|Aq|Au|Co|He|Ig|Im|Me|Te|Vi) (\d+|Gen)<br>$")
RDT = re.compile(r"^R:\s*(.*?)[,;]?\s*D:\s*(.*?)[,;]?\s*T:\s*(.*?)<br>$")


def clean(line):
    line = re.sub(r"<!--.*?-->", "", line)
    line = re.sub(r"<a id=\"[^\"]*\"></a>", "", line)
    line = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", line)
    line = line.replace("<br>", "")
    line = re.sub(r"\*\*([^*]*)\*\*", r"\1", line)
    line = re.sub(r"\*([^*]*)\*", r"\1", line)
    return line.strip()


def spells(lines):
    found = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("##### ") and i + 2 < len(lines) and ARTS.match(lines[i + 1]):
            name = clean(lines[i][6:])
            technique, form, level = ARTS.match(lines[i + 1]).groups()
            rdt = RDT.match(lines[i + 2])
            if not rdt:
                raise SystemExit("No R/D/T line for " + name)
            target = rdt.group(3).strip()
            ritual = target.endswith(", Ritual") or target.endswith(" Ritual")
            target = re.sub(r",?\s*Ritual$", "", target)
            j = i + 3
            requisites = ""
            if lines[j].startswith("Req:"):
                requisites = clean(lines[j][4:])
                j += 1
            text = []
            while j < len(lines) and not lines[j].startswith("#"):
                text.append(clean(lines[j]))
                j += 1
            description = re.sub(r"\n{3,}", "\n\n", "\n".join(text)).strip()
            found.append({
                "type": "Spells",
                "name": name,
                "description": description,
                "images": {},
                "rulesets": [{"system": SYSTEM, "implementation": {"arm5Spell": {"Stats": {
                    "Arts": technique + form,
                    "Technique": TECHNIQUES[technique],
                    "Form": FORMS[form],
                    "Level": level,
                    "Range": rdt.group(1).strip(),
                    "Duration": rdt.group(2).strip(),
                    "Target": target,
                    "Requisites": requisites,
                    "Ritual": "Yes" if ritual else "No",
                }}}}],
            })
            i = j
        else:
            i += 1
    return found


def main():
    entities = spells(SOURCE.read_text().split("\n"))
    library = {
        "name": "Ars Magica 5th edition spells (CC BY-SA)",
        "description": "The " + str(len(entities)) + " formulaic and ritual spells of the Ars Magica Fifth Edition core rulebook. Based on the material for Ars Magica, ©1993–2024, licensed by Trident, Inc. d/b/a Atlas Games®, under the Creative Commons Attribution-ShareAlike 4.0 International license (CC BY-SA 4.0). Converted from the Markdown text at https://github.com/OriginalMadman/Ars-Magica-Open-License; this library is shared under the same licence. See LICENSE-arm5.md next to it.",
        "url": "/systems/arm5/arm5.json",
        "gamemaster": "",
        "entities": entities,
    }
    Path(OUT).write_text(json.dumps(library, indent=1, ensure_ascii=False) + "\n")
    print(len(entities), "spells")


main()
