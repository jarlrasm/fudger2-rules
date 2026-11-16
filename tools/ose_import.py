"""Builds the OSE library from the Old-School Essentials SRD in Markdown.

Only content outside the Player Characters and Adventuring sections is used
(spells, monsters and magic items), as the Old-School Essentials third-party
license asks. The library is not shipped: Necrotic Gnome's current SRD says its
material is not open content, so check the licence of your copy before running this.
"""

import json
import re
import sys
from pathlib import Path

RAW = Path(sys.argv[1])
OUT = sys.argv[2]
SYSTEM = "OldSchoolEssentials"
URL = "/systems/ose/ose.json"


def entity(type_, name, description, implementation):
    return {
        "type": type_,
        "name": name,
        "description": description.strip(),
        "images": {},
        "rulesets": [{"system": SYSTEM, "implementation": implementation}],
    }


def title_and_body(path):
    text = path.read_text(encoding="utf-8").replace("\r", "")
    match = re.match(r"#\s+(.+)\n", text)
    return (match.group(1).strip(), text[match.end():].strip()) if match else (path.stem.replace("_", " "), text)


def number(text, fallback=0):
    found = re.search(r"-?\d+", text or "")
    return int(found.group()) if found else fallback


def clean(text):
    text = re.sub(r"^-{3,}\s*$", "", text, flags=re.M)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def spells():
    result = []
    for folder, class_name in [("Cleric_Spells", "Cleric"), ("Magic-User_Spells", "Magic-User")]:
        for path in sorted((RAW / "4_Magic" / folder).glob("*.md")):
            name, body = title_and_body(path)
            level = number(re.search(r"\*(\d)\w* Level", body).group(1)) if re.search(r"\*(\d)\w* Level", body) else 1
            duration = re.search(r"\*\*Duration:\*\*\s*(.+)", body)
            range_ = re.search(r"\*\*Range:\*\*\s*(.+)", body)
            result.append(
                entity(
                    "Spells",
                    re.sub(r"\s*\((MU|C)\)$", "", name),
                    clean(body),
                    {
                        "spellStats": {
                            "Stats": {
                                "Class": class_name,
                                "Level": level,
                                "Duration": duration.group(1).strip() if duration else "",
                                "Range": range_.group(1).strip() if range_ else "",
                                "Reversible": "Reversed" in body,
                            }
                        }
                    },
                )
            )
    return result


def table_rows(body):
    rows = {}
    for line in body.split("\n"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 2 and cells[0] and not set(cells[0]) <= set("-: "):
            rows[cells[0]] = cells[1]
    return rows


def descending(text):
    return number(text, 9)


def saves(text):
    found = dict(re.findall(r"([DWPBS])(\d+)", text or ""))
    saves_as = re.search(r"\(([^)]*)\)", text or "")
    return found, saves_as.group(1) if saves_as else ""


def monsters():
    result = []
    for path in sorted((RAW / "7_Monsters" / "Monster_Stats").glob("*.md")):
        name, body = title_and_body(path)
        rows = table_rows(body)
        if "Armor Class" not in rows:
            continue
        found, saves_as = saves(rows.get("Saving Throws"))
        hit_points = re.search(r"\((\d+)\s*hp\)", rows.get("Hit Dice", ""))
        description = clean("\n".join(line for line in body.split("\n") if not line.strip().startswith("|")))
        result.append(
            entity(
                "Creature",
                name,
                description,
                {
                    "creatureTable": {
                        "Stats": {
                            "Armour Class": descending(rows.get("Armor Class")),
                            "Hit Dice": re.sub(r"\s*\(.*?\)", "", rows.get("Hit Dice", "")).strip(),
                            "Attacks": rows.get("Attacks", ""),
                            "Max HP": int(hit_points.group(1)) if hit_points else 4,
                            "HP": int(hit_points.group(1)) if hit_points else 4,
                            "THAC0": number(rows.get("THAC0"), 19),
                            "Movement": rows.get("Movement", ""),
                            "Saves As": saves_as,
                            "Morale": number(rows.get("Morale"), 7),
                            "Alignment": rows.get("Alignment", ""),
                            "XP": number(rows.get("XP"), 0),
                            "Number Appearing": rows.get("Number Appearing", ""),
                            "Treasure Type": rows.get("Treasure Type", ""),
                        },
                        "Saving Throws": {key: int(found[key]) for key in "DWPBS" if key in found},
                        "Notes": {"Special Abilities": description},
                    }
                },
            )
        )
    return result


def magic_items():
    result = []
    for folder in ["Potions", "Rings", "Rods_Staves_Wands", "Miscellaneous"]:
        for path in sorted((RAW / "8_Treasures" / folder).glob("*.md")):
            name, body = title_and_body(path)
            result.append(entity("Equipment", name, clean(body), {"equipmentStats": {"Stats": {"Weight": "", "Cost": ""}}}))
    return result


library = {
    "name": "Old-School Essentials SRD",
    "description": "Spells, monsters and magic items from the Old-School Essentials System Reference Document, Open Game Content under the Open Game License 1.0a (see LICENSE-ose.md). Converted from the Markdown SRD at https://github.com/oldmanumby/ose.srd. Old-School Essentials is a trademark of Necrotic Gnome. The trademark and Old-School Essentials logo are used with permission of Necrotic Gnome, under license.",
    "url": URL,
    "gamemaster": "",
    "entities": spells() + monsters() + magic_items(),
}

json.dump(library, open(OUT, "w"), ensure_ascii=False, indent=1)
print(len(library["entities"]), "entities")
