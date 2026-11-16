import json
import re
import sys

RAW = sys.argv[1]
OUT = sys.argv[2]
SYSTEM = "BladesInTheDark"
URL = "/systems/blades/blades.json"

lines = open(f"{RAW}/srd.md", encoding="utf-8").read().split("\n")


def section(start_heading, end_heading):
    """The lines after the heading `start_heading` up to the heading `end_heading`."""
    start = next(i for i, line in enumerate(lines) if line.strip() == start_heading)
    end = next(i for i in range(start + 1, len(lines)) if lines[i].strip() == end_heading)
    return lines[start + 1:end]


def entries(body):
    """Sub-entries headed by ### (or a stray ##) inside a section, with their text."""
    result, name, text = [], None, []
    for line in body:
        heading = re.match(r"^#{2,3}\s+(.*)$", line)
        if heading:
            if name:
                result.append((name, text))
            name, text = heading.group(1).strip(), []
        elif name:
            text.append(line)
    if name:
        result.append((name, text))
    return [(n, clean("\n".join(t))) for n, t in result if clean("\n".join(t))]


def clean(text):
    text = re.sub(r"^> ?", "", text, flags=re.M)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def entity(type_, name, description, implementation):
    return {
        "type": type_,
        "name": name,
        "description": description,
        "images": {},
        "rulesets": [{"system": SYSTEM, "implementation": implementation}],
    }


def abilities():
    body = section("## Special abilities", "## Character items")
    return [entity("Abilities", name, text, {"abilityStats": {"Stats": {"Playbook": "Scoundrel"}}}) for name, text in entries(body)]


def crew_abilities():
    body = section("## Crew special abilities", "# The Score")
    return [entity("Abilities", name, text, {"abilityStats": {"Stats": {"Playbook": "Crew"}}}) for name, text in entries(body)]


def entanglements():
    body = section("# Entanglements", "# Downtime activities")
    return [entity("Factions", f"Entanglement: {name}", text, {"factionStats": {"Stats": {"Tier": 0, "Hold": "", "Status": 0, "Turf": "", "Assets": ""}}}) for name, text in entries(body)]


library = {
    "name": "Blades in the Dark SRD",
    "description": "Special abilities, crew abilities and entanglements from the Blades in the Dark System Reference Document by John Harper (One Seven Design), licensed under the Creative Commons Attribution 3.0 Unported licence (https://creativecommons.org/licenses/by/3.0/). The SRD has generic examples rather than the named playbooks of the book. Converted from https://github.com/amazingrando/blades-in-the-dark-srd-content.",
    "url": URL,
    "gamemaster": "",
    "entities": abilities() + crew_abilities() + entanglements(),
}

json.dump(library, open(OUT, "w"), ensure_ascii=False, indent=1)
print(len(library["entities"]), "entities")
