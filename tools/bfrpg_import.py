"""Builds a B/X compatible library for Old-School Essentials from Basic Fantasy.

The Basic Fantasy Role-Playing Game, 4th edition, by Chris Gonnerman and
contributors, is licensed under the Creative Commons Attribution-ShareAlike
4.0 International licence. Its text is read from the Quarto edition at
https://github.com/jmhimara/bfrpg (4th edition, release 128), which has the
same licence. Basic Fantasy uses ascending Armor Class; the library gives
OSE's descending Armour Class (19 minus the ascending value), and THAC0 from
the monster attack table by Hit Dice.

    python3 tools/bfrpg_import.py <bfrpg checkout> systems/ose/bfrpg.json [headings.json]
"""

import json
import re
import sys
from pathlib import Path

RAW = Path(sys.argv[1])
OUT = sys.argv[2]
# Where to write each monster's heading in the book, for tools/pdf_references.py --aliases.
HEADINGS = sys.argv[3] if len(sys.argv) > 3 else None
headings = {}
SYSTEM = "OldSchoolEssentials"
URL = "/systems/ose/bfrpg.json"
SAVES = {"fighter": "F", "magic-user": "MU", "cleric": "C", "thief": "T", "normal man": "NH"}
# Monster THAC0 by Hit Dice, as in B/X: up to 1 HD, then each step up to the next whole HD.
THAC0 = [(1, 19), (2, 18), (3, 17), (4, 16), (5, 15), (6, 14), (7, 13), (9, 12), (11, 11), (13, 10), (15, 9), (17, 8), (19, 7), (21, 6)]


def entity(type_, name, description, ruleset, values):
    return {
        "type": type_,
        "name": name,
        "description": description.strip(),
        "images": {},
        "rulesets": [{"system": SYSTEM, "implementation": {ruleset: {"Stats": values} if "Stats" not in values else values}}],
    }


def clean(text):
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\{[#.][^}]*\}", "", text)
    text = re.sub(r"\^([^^]*)\^", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^:::.*$", "", text, flags=re.M).replace("†", "")
    text = re.sub(r"(?<=\S)\n(?=[^\n|#*-])", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def first_int(text, fallback=0):
    found = re.search(r"\d+", text or "")
    return int(found.group()) if found else fallback


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def hit_dice(text):
    """The number of Hit Dice, whether it has a plus, and the average hit points."""
    fixed = re.search(r"\((\d+)d(\d+) hit points?\)", text)
    if fixed:
        return 0.5, False, max(1, int(int(fixed.group(1)) * (int(fixed.group(2)) + 1) / 2))
    if text.strip().startswith("½"):
        return 0.5, False, 2
    found = re.search(r"(\d+)\s*(?:\+\s*(\d+))?", text)
    if not found:
        return 1, False, 4
    dice, plus = int(found.group(1)), int(found.group(2) or 0)
    return dice, bool(plus), max(1, int(dice * 4.5) + plus)


def thac0(dice, plus):
    level = dice + (0.5 if plus else 0)
    for most, value in THAC0:
        if level <= most:
            return value
    return 5


def save_as(text):
    found = re.match(r"\s*([A-Za-z -]+?)\s*:?\s*(\d+)?\s*$", (text or "").replace("Normal Man", "normal man"))
    if not found:
        return text or ""
    return SAVES.get(found.group(1).strip().lower(), found.group(1).strip()) + (found.group(2) or "")


def attacks(number, damage):
    names = [a.strip() for a in re.split(r"/|,| or ", number or "") if a.strip() and a.strip().lower() not in ("special", "same")]
    damages = [d.strip() for d in re.split(r"/| or ", damage or "") if d.strip()]
    if names and len(names) == len(damages):
        return [{"Name": re.sub(r"^\d+\s+", "", n), "Attack": 0, "Damage": d} for n, d in zip(names, damages)]
    return [{"Name": number or "Attack", "Attack": 0, "Damage": damage or ""}]


def monsters():
    text = (RAW / "monstersAll.qmd").read_text(encoding="utf-8")
    result, seen = [], set()
    for chunk in text.split('<div class="monster"')[1:]:
        chunk = chunk.split('<div class="text-end">')[0]
        rows = [cells(line) for line in chunk.split("\n") if line.startswith("|")]
        rows = [r for r in rows if not set("".join(r)) <= set("-: ")]
        if len(rows) < 3:
            continue
        names = rows[0][1:]
        stats = {}
        for row in rows[1:]:
            label, values, last = row[0].rstrip(":").replace("\xa0", " "), [], ""
            for value in row[1:] + [""] * (len(names) - len(row) + 1):
                value = value.strip()
                if re.fullmatch(r"[–-]\s*same\s*[–-]", value.lower()) or not value:
                    value = last
                value = re.sub(r"^[–-]\s*|\s*[–-]$", "", value)
                values.append(value)
                last = value
            stats[label] = values
        prose = clean("\n".join(line for line in chunk.split("\n") if not line.startswith("|") and not line.startswith("## ") and not line.startswith(" data-tag") and "data-tag" not in line))
        heading = re.search(r"^#{2,4} (.+)$", chunk, re.M)
        for i, name in enumerate(names):
            name = clean(name).replace("*", "").strip()
            if heading:
                headings[name] = [clean(heading.group(1)).replace("*", "").strip()]
            if not name or name.lower() in seen:
                continue
            seen.add(name.lower())
            get = lambda key: (stats.get(key) or [""] * len(names))[i] if i < len(stats.get(key) or []) else ""
            dice, plus, hp = hit_dice(get("Hit Dice"))
            ascending = first_int(get("Armor Class"), 11)
            head = f"*Armor Class {get('Armor Class')} (ascending), Hit Dice {get('Hit Dice')}.*"
            result.append(entity("Creature", name, head + "\n\n" + prose, "creatureTable", {
                "Stats": {
                    "Armour Class": 19 - ascending,
                    "Hit Dice": get("Hit Dice"),
                    "Attacks": get("No. of Attacks"),
                    "Max HP": hp,
                    "HP": hp,
                    "THAC0": thac0(dice, plus),
                    "Movement": get("Movement"),
                    "Saves As": save_as(get("Save As")),
                    "Morale": first_int(get("Morale"), 7),
                    "XP": first_int(get("XP").replace(",", ""), 0),
                    "Number Appearing": get("No. Appearing"),
                    "Treasure Type": get("Treasure Type"),
                },
                "Attacks": attacks(get("No. of Attacks"), get("Damage")),
            }))
    return result


def spells():
    text = (RAW / "allSpells.qmd").read_text(encoding="utf-8")
    result, seen = [], set()
    for block in re.split(r"^## ", text, flags=re.M)[1:]:
        title, _, body = block.partition("\n")
        body = body.replace("Magic User", "Magic-User")
        name = title.strip()
        if name.startswith("Level") or not body.strip():
            continue
        classes = re.search(r"^((?:Cleric|Magic-User) \d+(?:, (?:Cleric|Magic-User) \d+)*)\s*$", body, re.M)
        if not classes:
            continue
        lists = re.findall(r"(Cleric|Magic-User) (\d+)", classes.group(1))
        range_ = re.search(r"^Range:\s*(.+)$", body, re.M)
        duration = re.search(r"^Duration:\s*(.+)$", body, re.M)
        description = re.sub(r"^(Range|Duration):.*$|^((?:Cleric|Magic-User) \d+(?:, (?:Cleric|Magic-User) \d+)*)\s*$", "", body, flags=re.M)
        description = clean(description.split("\n# ")[0].split("<div")[0])
        reversible = name.endswith("*")
        name = name.rstrip("*").strip()
        if name.lower() in seen:
            continue
        seen.add(name.lower())
        head = f"*{', '.join(f'{c} {l}' for c, l in lists)}{', reversible' if reversible else ''}.*"
        result.append(entity("Spells", name, head + "\n\n" + description, "spellStats", {
            "Class": lists[0][0],
            "Level": int(lists[0][1]),
            "Duration": duration.group(1).strip() if duration else "",
            "Range": range_.group(1).strip() if range_ else "",
            "Reversible": reversible,
        }))
    return result


def equipment():
    text = (RAW / "equipment.qmd").read_text(encoding="utf-8")
    explanations = {}
    explained = text.split("### Equipment Explanations", 1)[1].split("\n## ", 1)[0]
    for paragraph in explained.split("\n\n"):
        for name in re.findall(r"\*\*([^*]+?)\*\*", paragraph):
            explanations.setdefault(name.strip().lower(), clean(paragraph))
    ranges = {}
    section, result, seen = "", [], set()
    for line in text.split("\n"):
        if line.startswith("#"):
            section = line.strip("# ").split("{")[0].strip()
            continue
        if not line.startswith("|"):
            continue
        row = cells(line)
        if set("".join(row)) <= set("-: ") or row[0] in ("Item", "Weapon", "Armor Type") or row[0].startswith("**"):
            continue
        if section == "Missile Weapon Ranges" and len(row) >= 4:
            ranges[row[0].lower()] = row[1:4]
    for line in text.split("\n"):
        if line.startswith("#"):
            section = line.strip("# ").split("{")[0].strip()
            continue
        if not line.startswith("|"):
            continue
        row = cells(line)
        if set("".join(row)) <= set("-: ") or row[0] in ("Item", "Weapon", "Armor Type") or row[0].startswith("**"):
            continue
        name = clean(row[0]).replace("†", "")
        if name.lower() in seen or name in ("No Armor",):
            continue
        key = name.lower()
        description = next((explanations[k] for k in [key, key.split(",")[0], key.split(" (")[0], key.split(",")[0].rstrip("s")] if k in explanations), "")
        if section == "Misc. Equipment":
            seen.add(name.lower())
            result.append(entity("Equipment", name, description, "equipmentStats", {"Weight": row[2], "Cost": row[1]}))
        elif section == "Weapons" and len(row) >= 5 and row[1]:
            seen.add(name.lower())
            short, medium, long_ = ranges.get(name.lower(), ["", "", ""])
            size = {"S": "Small", "M": "Medium", "L": "Large"}.get(row[2], "")
            result.append(entity("Weapons", name, description, "weaponStats", {
                "Damage": row[4],
                "Attack Bonus": "",
                "Qualities": ", ".join(x for x in [size, "Missile" if short else ""] if x),
                "Short Range": short,
                "Medium Range": medium,
                "Long Range": long_,
                "Weight": row[3],
                "Cost": row[1],
            }))
        elif section == "Armor and Shields" and len(row) >= 4:
            seen.add(name.lower())
            ac = row[3] if row[3].startswith("+") else f"{19 - first_int(row[3], 11)} [{row[3]}]"
            result.append(entity("Armour", name, description, "armourStats", {"AC": ac, "Weight": row[2], "Cost": row[1]}))
    return result


entities = monsters() + spells() + equipment()
library = {
    "name": "Basic Fantasy (B/X compatible)",
    "description": "Monsters, spells, weapons, armour and equipment from the Basic Fantasy Role-Playing Game Core Rules, 4th edition, Copyright © 2006-2023 Chris Gonnerman, licensed under the Creative Commons Attribution-ShareAlike 4.0 International licence (https://creativecommons.org/licenses/by-sa/4.0/). Basic Fantasy is a different game from Old-School Essentials, but its monsters and spells follow the same B/X rules; Armor Class is converted to descending AC. Converted from https://github.com/jmhimara/bfrpg. See LICENSE-bfrpg.md next to this library.",
    "url": URL,
    "gamemaster": "",
    "entities": entities,
}
json.dump(library, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if HEADINGS:
    json.dump(headings, open(HEADINGS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(entities), "entities:", {t: sum(1 for e in entities if e["type"] == t) for t in sorted({e["type"] for e in entities})})
