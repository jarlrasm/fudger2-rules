import json
import re
import sys
from pathlib import Path

RAW = Path(sys.argv[1])
OUT = sys.argv[2]
SYSTEM = "FateCore"
URL = "/systems/fate/fatecore.json"


def stunts(path):
    skill = path.stem.capitalize()
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^## .*Stunts\s*$(.*?)(?=^#|\Z|^\s*\* \[)", text, re.M | re.S)
    if not match:
        return []
    result = []
    for name, description in re.findall(r"^\s*\* \*\*(.+?)\*\*\.?\s*(.+)$", match.group(1), re.M):
        result.append(
            {
                "type": "Stunts",
                "name": name.strip().rstrip("."),
                "description": description.strip(),
                "images": {},
                "rulesets": [{"system": SYSTEM, "implementation": {"stuntStats": {"Stats": {"Skill": skill, "Cost": "1 refresh"}}}}],
            }
        )
    return result


library = {
    "name": "Fate Core stunts",
    "description": "The example stunts for each skill in the Fate Core System Reference Document by Evil Hat Productions, licensed under the Creative Commons Attribution 3.0 Unported licence (https://creativecommons.org/licenses/by/3.0/). Converted from https://github.com/brunobord/fate-srd-markdown. This work is based on Fate Core System, products of Evil Hat Productions, LLC, developed, authored, and edited by Leonard Balsera, Brian Engard, Jeremy Keller, Ryan Macklin, Mike Olson, Clark Valentine, Amanda Valentine, Fred Hicks, and Rob Donoghue, and licensed for our use under the Creative Commons Attribution 3.0 Unported license.",
    "url": URL,
    "gamemaster": "",
    "entities": [stunt for path in sorted(RAW.glob("*.md")) for stunt in stunts(path)],
}

json.dump(library, open(OUT, "w"), ensure_ascii=False, indent=1)
print(len(library["entities"]), "entities")
