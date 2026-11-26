"""Builds systems/fate/extensions/venturecity.json from the Venture City SRD.

    python3 -I tools/venturecity_import.py systems/fate/Venture-City-SRD.pdf systems/fate/extensions/venturecity.json
"""

import json
import re
import subprocess
import sys

PDF = sys.argv[1]
OUT = sys.argv[2]

POWERS = ["Animal Control", "Creature Summoning", "Disguise", "Duplication", "Elasticity", "Energy Absorption", "Energy Blast", "Flight", "Gadgeteering", "Harm", "Healing", "Illusion", "Influence", "Invisibility", "Item Summoning", "Material Mimic", "Natural Weapon", "Machine Control", "Plant Control", "Phasing", "Power Amplification", "Power Nullification", "Power Replication", "Precognition", "Regeneration", "Shape-Shifting", "Shielding", "Slowing", "Super Agility", "Super Intelligence", "Super Senses", "Super Speed", "Super Strength", "Super Toughness", "Telekinesis", "Telepathy", "Teleportation", "Wall-Crawling", "Weather Control"]
THEMES = ["Corruption", "Electricity Projection", "Fire Projection", "Frost Projection", "Shadow Projection", "Super-Form", "Technology"]

SKILLS = {
    "Animal Control": "Rapport",
    "Disguise": "Deceive",
    "Energy Absorption": "Physique",
    "Energy Blast": "Shoot",
    "Flight": "Athletics",
    "Gadgeteering": "Crafts",
    "Healing": "Will",
    "Illusion": "Deceive",
    "Influence": "Rapport",
    "Invisibility": "Stealth",
    "Item Summoning": "Will",
    "Material Mimic": "Physique",
    "Natural Weapon": "Fight",
    "Machine Control": "Empathy",
    "Plant Control": "Empathy",
    "Phasing": "Burglary",
    "Power Replication": "Fight",
    "Precognition": "Notice",
    "Shape-Shifting": "Will",
    "Shielding": "Will",
    "Slowing": "Shoot",
    "Super Agility": "Athletics",
    "Super Intelligence": "Will",
    "Super Senses": "Investigate",
    "Super Speed": "Athletics",
    "Super Strength": "Physique",
    "Telekinesis": "Will",
    "Telepathy": "Empathy, Investigate, Notice",
    "Wall-Crawling": "Athletics",
    "Weather Control": "Will",
}

HEADERS = {"Enhancements": "Enhancements", "Common Power Synergies": "Synergies", "Improved Special Effect": "Improved", "Improved Special Effects": "Improved", "Drawbacks": "Drawbacks", "Collateral Damage Effects": "Collateral"}

text = subprocess.run(["pdftotext", "-layout", PDF, "-"], capture_output=True, text=True, check=True).stdout
pages = text.split("\f")
lines = []
for number, page in enumerate(pages, 1):
    for line in page.split("\n"):
        lines.append((number, line.rstrip()))

start = next(i for i, (_, l) in enumerate(lines) if l.strip() == "Powers Catalog")
end = next(i for i, (_, l) in enumerate(lines) if l.strip().startswith("Appendix I"))
lines = lines[start + 1:end]

names = set(POWERS + THEMES)
entries = []
current = None
section = None
for i, (page, line) in enumerate(lines):
    s = line.strip()
    if s == "Power Themes":
        continue
    if s in names and (current is None or section is not None):
        current = {"name": s, "page": page, "kind": "Power theme" if s in THEMES else "Power", "intro": [], "Enhancements": [], "Synergies": [], "Improved": [], "Drawbacks": [], "Collateral": []}
        entries.append(current)
        section = None
        continue
    if s in HEADERS:
        section = HEADERS[s]
        continue
    if current is None:
        continue
    current["intro" if section is None else section].append(line)


def paragraphs(raw, by_name):
    result = []
    for line in raw:
        s = line.strip().replace("Stunning Blow:When", "Stunning Blow: When")
        if not s:
            if result and result[-1] != "":
                result.append("")
            continue
        starts = by_name and re.match(r"^[“\"]?[A-Z][^:]{0,40}:\s", s) and not result_continues(result)
        if len(result) >= 2 and result[-1] == "" and re.match(r"[a-z]", s):
            result.pop()
            result[-1] = join(result[-1], s)
        elif not result or result[-1] == "" or starts:
            if result and result[-1] == "":
                result.pop()
            result.append(s)
        else:
            result[-1] = join(result[-1], s)
    return [p for p in result if p]


def result_continues(result):
    return bool(result) and result[-1] != "" and not re.search(r"[.!?…”)]$", result[-1])


def join(a, b):
    if a.endswith("-") and not a.endswith(" -"):
        return a + b
    if a.endswith("—") or a.endswith("…"):
        return a + b
    return a + " " + b


def names_aspect(paragraph):
    last = re.split(r"[.!?;:]\s+", paragraph.rstrip(".!)"))[-1]
    return any(re.match(r"[A-Z]", w) for w in last.split()[1:])


def drawbacks(raw):
    result = []
    previous = 200
    for line in raw:
        s = line.strip()
        if not s:
            continue
        if not result or (re.search(r"[.!)]$", result[-1]) and re.match(r"[A-Z]", s) and names_aspect(result[-1])):
            result.append(s)
        else:
            result[-1] = join(result[-1], s)
        previous = len(line)
    return result


def clean(text):
    return text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')


library = {
    "name": "Venture City powers",
    "description": "The powers catalog and power themes of the Venture City SRD, by Evil Hat Productions: each power with its basic form, enhancements, common synergies, improved special effects, drawbacks and collateral damage effects. Open Game Content under the Open Game License v1.0a (Appendix I of the PDF); see LICENSE-fate.md. Fate is a trademark of Evil Hat Productions, LLC.",
    "url": "/systems/fate/extensions/venturecity.json",
    "gamemaster": "",
    "documents": [{"key": "Venture-City-SRD", "name": "Venture City SRD (OGL)", "url": "/systems/fate/Venture-City-SRD.pdf", "public": True}],
    "entities": [],
}

for e in entries:
    intro = paragraphs(e["intro"], False)
    description = "\n\n".join(clean(p) for p in intro)
    enh = paragraphs(e["Enhancements"], True)
    syn = paragraphs(e["Synergies"], True)
    imp = paragraphs(e["Improved"], True)
    dra = drawbacks(e["Drawbacks"])
    col = paragraphs(e["Collateral"], True)
    stats = {
        "Kind": e["kind"],
        "Skill": SKILLS.get(e["name"], ""),
        "Enhancements": "\n\n".join(clean(p) for p in enh),
        "Synergies": "\n\n".join(clean(p) for p in syn),
        "Improved Special Effect": "\n\n".join(clean(p) for p in imp),
        "Drawbacks": "\n\n".join(clean(p) for p in dra),
        "Collateral Damage": "\n\n".join(clean(p) for p in col),
    }
    library["entities"].append({
        "type": "Powers",
        "name": e["name"],
        "description": description,
        "images": {},
        "references": [{"document": "Venture-City-SRD", "page": e["page"]}],
        "rulesets": [{"system": "FateCore", "implementation": {"ventureStats": {"Stats": stats}}}],
    })

missing = names - {e["name"] for e in entries}
print("missing", missing, file=sys.stderr)
json.dump(library, open(OUT, "w"), indent=1, ensure_ascii=False)
open(OUT, "a").write("\n")
