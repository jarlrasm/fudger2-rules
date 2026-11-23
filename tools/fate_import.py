# Usage: fate_import.py <fate-srd-markdown skill files> <out.json> <fate-srd-content fate-core.md>
# The skill folder holds one <skill>.md per skill (markdown/fate-core/<skill>/index.md, renamed).
import json
import re
import sys
from pathlib import Path

RAW = Path(sys.argv[1])
OUT = sys.argv[2]
# docs/markdown/fate-core.md from https://github.com/fate-srd/fate-srd-content,
# for the example extras.
CORE = Path(sys.argv[3])
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


def extras():
    """The example extras in the Extras chapter, headed "Extra: Name"."""
    result, current = [], None
    for line in CORE.read_text(encoding="utf-8").split("\n"):
        heading = re.match(r"^#+\s+(.*)$", line)
        if heading:
            if current:
                result.append(current)
            name = re.match(r"^(?:\*\*)?Extra(?:\*\*)?:\s*(.+)$", heading.group(1).strip())
            current = {"name": name.group(1).strip(), "lines": []} if name else None
        elif current:
            current["lines"].append(line)
    if current:
        result.append(current)
    entities = []
    for extra in result:
        text = "\n".join(extra["lines"])
        costs = re.search(r"^\*\*Costs\*\*:\s*(.+)$", text, re.M)
        body = re.sub(r"\n{3,}", "\n\n", re.sub(r"^ +", "", text, flags=re.M)).strip()
        entities.append(
            {
                "type": "Extras",
                "name": extra["name"],
                "description": body,
                "images": {},
                "rulesets": [{"system": SYSTEM, "implementation": {"extraStats": {"Stats": {"Aspects": "", "Skills": "", "Stunts": "", "Cost": re.sub(r"\s*\(.*?\)", "", costs.group(1)).strip() if costs else ""}}}}],
            }
        )
    return entities


library = {
    "name": "Fate Core stunts and extras",
    "description": "The example stunts for each skill, and the example extras, in the Fate Core System Reference Document by Evil Hat Productions, licensed under the Creative Commons Attribution 3.0 Unported licence (https://creativecommons.org/licenses/by/3.0/). Converted from https://github.com/brunobord/fate-srd-markdown and https://github.com/fate-srd/fate-srd-content. This work is based on Fate Core System, products of Evil Hat Productions, LLC, developed, authored, and edited by Leonard Balsera, Brian Engard, Jeremy Keller, Ryan Macklin, Mike Olson, Clark Valentine, Amanda Valentine, Fred Hicks, and Rob Donoghue, and licensed for our use under the Creative Commons Attribution 3.0 Unported license.",
    "url": URL,
    "gamemaster": "",
    "entities": [stunt for path in sorted(RAW.glob("*.md")) for stunt in stunts(path)] + extras(),
}

json.dump(library, open(OUT, "w"), ensure_ascii=False, indent=1)
print(len(library["entities"]), "entities")
