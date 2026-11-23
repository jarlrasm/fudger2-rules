# Usage: fate_import.py <fate-srd-markdown skill files> <out.json> <fate-srd-content fate-core.md> [<folder of Evil Hat's OGL SRD .html files>]
# The skill folder holds one <skill>.md per skill (markdown/fate-core/<skill>/index.md, renamed).
import html
import json
import re
import sys
from pathlib import Path

RAW = Path(sys.argv[1])
OUT = sys.argv[2]
# docs/markdown/fate-core.md from https://github.com/fate-srd/fate-srd-content,
# for the example extras.
CORE = Path(sys.argv[3])
# Evil Hat's OGL SRDs as HTML, for the example stunts and powers of the
# toolkits and settings.
OGL = Path(sys.argv[4]) if len(sys.argv) > 4 else None
SOURCES = {
    "venturecitySRD-OGL.html": "Venture City",
    "FST-SRD-OGL.html": "Fate System Toolkit",
    "SailsSRD-OGL.html": "Sails Full of Stars",
    "NoSkillOGL.html": "Three Rocketeers: No-Skill Swashbuckling",
    "Fate-Adversary-Toolkit-SRD-Source-OGL.html": "Fate Adversary Toolkit",
    "AtomicSRD-OGL.html": "Atomic Robo",
    "FrontierSpiritOGL.html": "Frontier Spirit",
}
NOT_STUNTS = {"costs", "permissions", "recovery", "example", "note", "special", "trigger", "effect", "attack", "defend", "overcome",
              "create an advantage", "create advantage", "skills", "aspects", "stunts", "stress", "consequences", "refresh",
              "high concept", "trouble", "benefit", "facilities", "help", "strings", "time", "key"}
SKILLS = ["Athletics", "Burglary", "Contacts", "Crafts", "Deceive", "Drive", "Empathy", "Fight", "Investigate", "Lore", "Notice",
          "Physique", "Provoke", "Rapport", "Resources", "Shoot", "Stealth", "Will"]
SMALL = {"of", "the", "a", "an", "and", "to", "in", "with", "on", "for", "from", "or", "at", "by"}
RULE = re.compile(r"\+\d|once per|refresh|weapon:\s*\d|armor:\s*\d|fate point|you can|you may|you gain|gain an|instead of|stress box|consequence", re.I)
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


def html_lines(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"<script.*?</script>|<style.*?</style>", "", text, flags=re.S)
    text = re.sub(r"</(p|h[1-6]|li|tr|div)>|<br\s*/?>", "\n", text)
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    return [line.strip() for line in text.split("\n") if line.strip()]


def srd_stunts(taken):
    """Example stunts and powers written as "Name: what it does" in the
    toolkits and settings: a title-case name, and text with a rule in it."""
    result = []
    for file, source in SOURCES.items():
        seen = set()
        for line in html_lines(OGL / file):
            found = re.match(r"^([A-Z][A-Za-z’'\-]*(?: [A-Za-z’'\-]+){0,5}):\s+(.{25,})$", line)
            if not found:
                continue
            name, text = found.groups()
            if name.lower() in NOT_STUNTS or name in SKILLS or not RULE.search(text):
                continue
            if any(w[0].islower() and w.lower() not in SMALL for w in name.split()[1:]) or name.lower() in seen:
                continue
            seen.add(name.lower())
            skill = next((k for k in SKILLS if re.search(rf"\b{k}\b", text)), "")
            unique = name if name.lower() not in taken else f"{name} ({source})"
            taken.add(unique.lower())
            result.append(
                {
                    "type": "Stunts",
                    "name": unique,
                    "description": f"*From the {source} SRD.*\n\n{text.strip()}",
                    "images": {},
                    "rulesets": [{"system": SYSTEM, "implementation": {"stuntStats": {"Stats": {"Skill": skill, "Cost": ""}}}}],
                }
            )
    return result


library = {
    "name": "Fate Core stunts and extras",
    "description": "The example stunts for each skill, and the example extras, in the Fate Core System Reference Document by Evil Hat Productions, licensed under the Creative Commons Attribution 3.0 Unported licence (https://creativecommons.org/licenses/by/3.0/). Converted from https://github.com/brunobord/fate-srd-markdown and https://github.com/fate-srd/fate-srd-content. This work is based on Fate Core System, products of Evil Hat Productions, LLC, developed, authored, and edited by Leonard Balsera, Brian Engard, Jeremy Keller, Ryan Macklin, Mike Olson, Clark Valentine, Amanda Valentine, Fred Hicks, and Rob Donoghue, and licensed for our use under the Creative Commons Attribution 3.0 Unported license.",
    "url": URL,
    "gamemaster": "",
    "entities": [stunt for path in sorted(RAW.glob("*.md")) for stunt in stunts(path)] + extras(),
}

if OGL:
    library["entities"] += srd_stunts({e["name"].lower() for e in library["entities"]})
    library["name"] = "Fate stunts and extras"
    library["description"] += " The example stunts and powers of the Fate System Toolkit, Fate Adversary Toolkit, Venture City, Sails Full of Stars, Three Rocketeers, Atomic Robo and Frontier Spirit SRDs are from Evil Hat's OGL versions of those SRDs, Open Game Content under the Open Game License v1.0a; see LICENSE-fate.md."
json.dump(library, open(OUT, "w"), ensure_ascii=False, indent=1)
print(len(library["entities"]), "entities")
