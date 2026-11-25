"""Builds the D&D 3.5 library from the Revised (v3.5) System Reference Document.

srd-v3.5-md (https://github.com/olimot/srd-v3.5-md, commit c7f30a0) holds the
v3.5 SRD, Wizards of the Coast's Open Game Content, as Markdown with HTML
tables. This uses the weapon, armor and goods tables of
basic-rules-and-legal/equipment.md, the rings, rods, staffs and wondrous items
of magic-items/, the spells of spells/spells-*.md, the feats of
basic-rules-and-legal/feats.md and monsters/monster-feats.md, and the monster
stat blocks of monsters/ (not the epic or psionic ones). True dragons, whose
statistics are given as age tables rather than stat blocks, are left out.

    python3 -I tools/dnd35_import.py <srd-v3.5-md dir> systems/dnd35/dnd35.json
"""

import html
import json
import re
import sys
from pathlib import Path

RAW = Path(sys.argv[1])
OUT = sys.argv[2]
SYSTEM = "DnD35"
SIZES = ["Fine", "Diminutive", "Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan", "Colossal"]
GOODS = ["Adventuring Gear", "Special Substances and Items", "Tools and Skill Kits", "Clothing"]
MAGIC = [("magic-items-iii-potions-rings-and-rods.md", "Ring Descriptions", "Ring"),
         ("magic-items-iii-potions-rings-and-rods.md", "Rod Descriptions", "Rod"),
         ("magic-items-iv-scrolls-staffs-and-wands.md", "Staff Descriptions", "Staff"),
         ("magic-items-v-wondrous-items.md", "Wondrous Item Descriptions", "")]
MAGIC_NAMES = {"Ram": "the Ram", "Python": "the Python", "Viper": "the Viper"}
SPELL_FIELDS = ["School", "Level", "Casting Time", "Components", "Range", "Duration", "Saving Throw", "Spell Resistance"]
LABELS = {"Hit Dice", "Initiative", "Speed", "Armor Class", "Base Attack/Grapple", "Attack", "Full Attack", "Space/Reach", "Special Attacks",
          "Special Qualities", "Saves", "Abilities", "Skills", "Feats", "Environment", "Organization", "Challenge Rating", "Treasure",
          "Alignment", "Advancement", "Level Adjustment"}
LABEL_FIXES = {"AC": "Armor Class", "Special Qualitiy": "Special Qualities", "Component": "Components"}
ALIASES = {
    "flail": "flail or heavy flail", "flail, heavy": "flail or heavy flail", "unarmed strike": "strike, unarmed",
    "shield, light": "shield, heavy or light", "shield, heavy": "shield, heavy or light",
    "spiked shield, light": "spiked shield, heavy or light", "spiked shield, heavy": "spiked shield, heavy or light",
    "crossbow, repeating heavy": "crossbow, repeating", "crossbow, repeating light": "crossbow, repeating",
    "shield, light wooden": "shield, light, wooden or steel", "shield, light steel": "shield, light, wooden or steel",
    "shield, heavy wooden": "shield, heavy, wooden or steel", "shield, heavy steel": "shield, heavy, wooden or steel",
    "manacles": "manacles and manacles, masterwork", "manacles, masterwork": "manacles and manacles, masterwork",
    "holy symbol, wooden": "holy symbol, silver or wooden", "holy symbol, silver": "holy symbol, silver or wooden",
    "musical instrument, common": "musical instrument, common or masterwork",
    "musical instrument, masterwork": "musical instrument, common or masterwork",
    "vial, ink or potion": "vial", "bolts, crossbow": "bolts",
}


def dashes(value):
    return value.replace("–", "-").replace("−", "-").replace("\xa0", " ")


def text(fragment):
    if not fragment:
        return ""
    fragment = re.sub(r"<sup>(.*?)</sup>", r"\1", fragment, flags=re.S)
    fragment = re.sub(r"<(b|strong)>(.*?)</\1>", r"**\2**", fragment, flags=re.S)
    fragment = re.sub(r"<(i|em)>(.*?)</\1>", r"*\2*", fragment, flags=re.S)
    fragment = re.sub(r"<li>", "\n- ", fragment)
    fragment = re.sub(r"</p>|<br\s*/?>|</tr>|</h\d>|</caption>", "\n\n", fragment)
    fragment = re.sub(r"</t[dh]>", " | ", fragment)
    fragment = re.sub(r"<[^>]+>", "", fragment)
    fragment = dashes(html.unescape(fragment))
    fragment = re.sub(r"(?<![\w\\*])_(?=\S)(.+?)(?<=\S)_(?![\w*])", r"*\1*", fragment)
    fragment = re.sub(r"\\([^*_])", r"\1", fragment)
    fragment = re.sub(r"\*\*\s*\*\*", "", fragment)
    fragment = re.sub(r"[ \t]+", " ", fragment)
    fragment = re.sub(r" *\| *\n", "\n", fragment)
    fragment = re.sub(r"\n\s*\n\s*(\n\s*)+", "\n\n", fragment)
    return fragment.strip()


def plain(fragment):
    value = re.sub(r"<sup>.*?</sup>", "", fragment or "", flags=re.S)
    value = re.sub(r"\\(.)", r"\1", re.sub(r"(?<!\\)[*_]|<[^>]+>", "", value))
    value = re.sub(r"\s+", " ", dashes(html.unescape(value))).strip()
    return "" if value in ("—", "-") else value


def entity(kind, name, description, ruleset, values):
    return {
        "type": kind,
        "name": name.replace("’", "'"),
        "description": description,
        "images": {},
        "rulesets": [{"system": SYSTEM, "implementation": {ruleset: values}}],
    }


def blocks(path):
    """Headings, paragraphs and tables of a Markdown file, in order."""
    result = []
    for chunk in re.split(r"\n\s*\n", path.read_text(encoding="utf-8")):
        chunk = chunk.strip()
        heading = re.match(r"(#+) (.*)", chunk)
        if heading:
            result.append(("h", len(heading.group(1)), heading.group(2).strip()))
        elif chunk.startswith("<table"):
            result.append(("table", 0, chunk))
        elif chunk:
            result.append(("p", 0, chunk))
    return result


def section(found, title):
    """The blocks under the heading named title, up to the next heading as high."""
    start = next(i for i, (kind, _, value) in enumerate(found) if kind == "h" and plain(value) == title)
    level = found[start][1]
    end = next((i for i in range(start + 1, len(found)) if found[i][0] == "h" and found[i][1] <= level), len(found))
    return found[start + 1:end]


def paragraph(block):
    kind, level, value = block
    return f"**{plain(value)}**" if kind == "h" else text(value)


def entries(found):
    """Bold "**Name:** text" paragraphs and the paragraphs after them, by lowercase name."""
    result, name = {}, None
    for block in found:
        label = re.match(r"\*\*(.+?):?\*\*:?\s*(.*)", block[2], re.S) if block[0] == "p" else None
        if label:
            name = key(plain(label.group(1)).rstrip(":"))
            result[name] = [text(label.group(2))]
        elif block[0] == "h":
            name = None
        elif name:
            result[name].append(paragraph(block))
    return {name: "\n\n".join(p for p in parts if p) for name, parts in result.items()}


def key(name):
    return name.lower().replace("’", "'").strip()


def look_up(descriptions, name, *parents):
    name = key(name)
    for candidate in (name, re.sub(r"\s*\(.*?\)", "", name), ALIASES.get(name, ""), ALIASES.get(re.sub(r"\s*\(.*?\)", "", name), ""), *map(key, parents)):
        if candidate in descriptions:
            return descriptions[candidate]
    return ""


def caption_table(found, caption):
    return next(value for kind, _, value in found if kind == "table" and f"<caption>{caption}</caption>" in value)


def table_rows(table):
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.S):
        yield re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)


def indented(fragment):
    return html.unescape(fragment).startswith("\xa0" * 4)


def first(values, pattern):
    return next((v for v in values if re.search(pattern, v)), "")


def weapon_rows(equipment):
    category, group, parent = "Simple", "", ""
    for cells in table_rows(caption_table(equipment, "Table: Weapons")):
        label = plain(cells[0])
        if label.endswith("Weapons") and len(cells) > 1:
            category = label.split()[0]
        elif len(cells) == 1:
            if not label[:1].isdigit():
                group = label.replace(" Weapons", "").replace(" Attacks", "").lower()
        else:
            values = [plain(c) for c in cells[1:]]
            notes = set(re.findall(r"<sup>(\d)</sup>", "".join(cells)))
            if indented(cells[0]):
                yield "ammunition", parent, label, values, notes
            else:
                parent = label
                yield category, group, label, values, notes


def weapons(equipment):
    descriptions = entries(section(equipment, "Weapon Descriptions"))
    for category, group, name, values, notes in weapon_rows(equipment):
        if category == "ammunition":
            continue
        if group == "unarmed":
            proficiency = "Unarmed" if name.lower().startswith("unarmed") else f"{category} light melee"
        else:
            proficiency = f"{category} {group}"
        description = look_up(descriptions, name)
        rest = values[3:]
        rng = first(rest, r"^\d+ ft\.$")
        special = [label for label, present in [
            ("Reach", "4" in notes or re.search(r"has reach|a reach weapon", description)),
            ("Thrown", group != "ranged" and rng),
            ("Double", "5" in notes),
            ("Nonlethal", "3" in notes),
        ] if present]
        yield entity("Weapons", name, description, "dnd35Weapon", {"Stats": {
            "Proficiency": proficiency,
            "Dmg S": values[1],
            "Dmg M": values[2],
            "Critical": first(rest, r"x\d|^\d+-\d+/"),
            "Range": rng,
            "Type": first(rest, r"^[A-Z][a-z]+( (and|or) [a-z]+)?$"),
            "Special": ", ".join(special),
            "Cost": values[0],
            "Weight": first(rest, r"lb\.|^special$"),
        }})


def item(name, description, price, weight, aura="", cl=""):
    return entity("Equipment", name, description, "dnd35Item", {"Stats": {"Slot": "", "Aura": aura, "CL": cl, "Price": price, "Weight": weight}})


def ammunition(equipment):
    descriptions = entries(section(equipment, "Weapon Descriptions"))
    for category, parent, name, values, _ in weapon_rows(equipment):
        if category == "ammunition":
            yield item(name, look_up(descriptions, name), values[0], first(values[1:], r"lb\."))


def armor(equipment):
    descriptions = entries(section(equipment, "Armor Descriptions"))
    kind = "Light"
    for cells in table_rows(caption_table(equipment, "Table: Armor and Shields")):
        name = plain(cells[0])
        if len(cells) < 9 or name[:1].isdigit() or name in ("", "Armor"):
            continue
        values = [plain(c) for c in cells[1:]]
        if not values[0]:
            kind = name.split()[0].rstrip("s").replace("Extra", "Extras")
            continue
        description = look_up(descriptions, name)
        if kind == "Extras":
            yield item(name, description, values[0], values[7])
            continue
        yield entity("Armor", name, description, "dnd35Armor", {"Stats": {
            "Type": kind,
            "Armor Bonus": values[1].lstrip("+"),
            "Max Dex": values[2].lstrip("+"),
            "Check Penalty": values[3] or "0",
            "Spell Failure": values[4],
            "Speed": "/".join(v for v in values[5:7] if v),
            "Cost": values[0],
            "Weight": values[7],
        }})


def goods(equipment):
    descriptions = {name: entries(section(equipment, name)) for name in GOODS}
    group, parent = "", ""
    for cells in table_rows(caption_table(equipment, "Table: Goods and Services")):
        name = plain(cells[0])
        if len(cells) < 3 or name in ("Item", "Service"):
            continue
        cost, weight = plain(cells[1]), plain(cells[2])
        if not cost and not weight:
            group = name
        elif group in GOODS:
            if indented(cells[0]):
                name, parents = f"{parent}, {name[0].lower()}{name[1:]}", [parent]
            else:
                parent, parents = name, []
            if cost:
                yield item(name, look_up(descriptions[group], name, *parents), cost, weight)


TRAILER = re.compile(r"^(Faint|Moderate|Strong|Overwhelming)[^;\n]*; CL ")


def trailer(line):
    line = plain(line)
    part = lambda label: (re.search(label + r"[_:]? ([^;]*?)\s*(?:;|$)", line) or [None, ""])[1]
    price = (part("Price") or part("Cost")).rstrip(".")
    weight = re.sub(r"\blb$", "lb.", part("Weight").rstrip("."))
    return {"Aura": line.split(";")[0].strip(), "CL": part("CL").rstrip("."), "Price": price, "Weight": weight}


def magic_items():
    for filename, title, prefix in MAGIC:
        name, parts, found = None, [], []
        for block in section(blocks(RAW / "magic-items" / filename), title):
            if found and found[-1][0] == "p" and TRAILER.match(found[-1][2]) and found[-1][2].rstrip("_* ").endswith(",") and block[0] == "p":
                found[-1] = ("p", 0, found[-1][2] + " " + block[2])
            else:
                found.append(block)
        for block in found:
            label = re.match(r"\*\*(.+?):?\*\*:?\s*(.*)", block[2], re.S) if block[0] == "p" else None
            if block[0] == "p" and TRAILER.match(block[2]) and name:
                stats = trailer(block[2])
                full = name if not prefix or prefix.lower() in name.lower().split() else f"{prefix} of {name}"
                yield item(full, "\n\n".join(p for p in parts if p), stats["Price"], stats["Weight"], stats["Aura"], stats["CL"])
                name, parts = None, []
            elif label:
                name, parts = plain(label.group(1)).rstrip(":"), [text(label.group(2))]
                name = MAGIC_NAMES.get(name, name)
            elif name:
                parts.append(paragraph(block))


def spells():
    for path in sorted((RAW / "spells").glob("spells-*.md")):
        found = blocks(path)
        starts = [i for i, (kind, level, _) in enumerate(found) if kind == "h" and level == 2]
        for start, end in zip(starts, starts[1:] + [len(found)]):
            name = plain(found[start][2])
            if "(Spell Name)" in name:
                continue
            stats, top, body = dict.fromkeys(SPELL_FIELDS, ""), [], []
            for index, block in enumerate(found[start + 1:end]):
                label = re.match(r"\*\*(.+?):\*\*\s*(.*)", block[2], re.S) if block[0] == "p" and not body else None
                if index == 0 and block[0] == "p" and not label:
                    stats["School"] = plain(block[2])
                elif label:
                    field = LABEL_FIXES.get(label.group(1), label.group(1))
                    if field in SPELL_FIELDS:
                        stats[field] = plain(label.group(2))
                    else:
                        top.append(f"**{field}:** {text(label.group(2))}")
                else:
                    body.append(paragraph(block))
            yield entity("Spells", name, "\n\n".join(p for p in top + body if p), "dnd35Spell", {"Stats": stats})


def feats(path, level):
    found = blocks(path)
    starts = [i for i, (kind, lv, value) in enumerate(found) if kind == "h" and lv == level and "<small>" in value]
    for start in starts:
        end = next((i for i in range(start + 1, len(found)) if found[i][0] == "h" and found[i][1] <= level), len(found))
        heading = re.match(r"(.*?)\s*<small>\[(.*?)\]</small>", found[start][2])
        name = plain(heading.group(1))
        if name == "Feat Name":
            continue
        prerequisites, parts = "", []
        for block in found[start + 1:end]:
            label = re.match(r"\*\*Prerequisites?:\*\*\s*(.*)", block[2], re.S) if block[0] == "p" else None
            if label:
                prerequisites = plain(label.group(1)).rstrip(".")
            else:
                parts.append(paragraph(block))
        yield entity("Feats", name, "\n\n".join(p for p in parts if p), "dnd35Feat", {"Stats": {
            "Type": ", ".join(t.strip() for t in heading.group(2).split(",")),
            "Prerequisites": prerequisites,
        }})


def first_int(value, fallback=0):
    found = re.search(r"-?\d+", (value or "").replace("+", ""))
    return int(found.group()) if found else fallback


def found_int(pattern, value, fallback=0):
    found = re.search(pattern, value or "", re.I)
    return int(found.group(1)) if found else fallback


def top_split(value, separator):
    parts, depth, start, i = [], 0, 0, 0
    while i < len(value):
        depth += {"(": 1, ")": -1}.get(value[i], 0)
        match = re.compile(separator).match(value, i) if depth == 0 else None
        if match and match.end() > i:
            parts.append(value[start:i])
            start = i = match.end()
            continue
        i += 1
    return [p.strip() for p in parts + [value[start:]] if p.strip()]


def weapon_ranges(equipment):
    ranges = {}
    for category, group, name, values, _ in weapon_rows(equipment):
        feet = first_int(first(values[3:], r"^\d+ ft\.$"))
        if feet:
            words = key(name).split(", ")
            ranges[" ".join(words)] = ranges[" ".join(reversed(words))] = feet
    return ranges


def attacks(value, ranges):
    rows = []
    for alternative in top_split(value, r"\s+or\s+"):
        for part in top_split(alternative, r",?\s+and\s+|[,;]\s*"):
            found = re.match(r"(.*?)\s*([+-]\d+)(?:/[+-]\d+)*\s+(melee|ranged)(?:\s+touch)?\s*\((.*)\)", part)
            swarm = re.match(r"(Swarm)\s*\((.*)\)", part, re.I)
            if swarm:
                rows.append({"Name": swarm.group(1), "Attack": 0, "Damage": swarm.group(2).strip(), "Range ft": 0})
            if not found:
                continue
            name, damage = found.group(1).strip(), found.group(4).strip()
            feet = 0
            if found.group(3) == "ranged":
                weapon = re.sub(r"\s*\(.*?\)|^\d+\s+", "", key(name))
                matches = [k for k in ranges if re.search(r"(^|\s)" + re.escape(k) + "s?$", weapon)]
                feet = found_int(r"(\d+)\s*ft\.", damage) or (ranges[max(matches, key=len)] if matches else 60)
            rows.append({"Name": name, "Attack": int(found.group(2)), "Damage": damage, "Range ft": feet})
    return rows


def stat_block(table):
    """The rows of a stat block, by label, one value per column, and the column names."""
    rows, header, names = {}, [], []
    previous = None
    for cells in table_rows(table):
        label = plain(cells[0]).strip()
        values = [plain(c) for c in cells[1:]]
        if not label and not rows:
            header.append(values)
            continue
        if not label:
            if previous:
                rows[previous] = [" ".join(v for v in pair if v) for pair in zip(rows[previous], values + [""] * len(rows[previous]))]
            continue
        name, _, extra = label.partition(":")
        name = LABEL_FIXES.get(name.strip(), name.strip())
        if name in LABELS:
            rows[name] = ([extra.strip()] if extra.strip() else []) + values
            previous = name
        elif previous:
            rows[previous] = [f"{a} {label}".strip() for a in rows[previous][:1]] + rows[previous][1:]
    if len(header) > 1:
        names = header[0]
    return rows, header[-1] if header else [], names


def creature_text(found, start):
    """Description and special abilities from the section the stat block at start is in."""
    anchor = next(i for i in range(start, -1, -1) if found[i][0] == "h" and plain(found[i][2]) != "Combat")
    level = found[anchor][1]
    end = next((i for i in range(anchor + 1, len(found)) if found[i][0] == "h" and found[i][1] <= level), len(found))
    description, abilities, combat, parent = [], [], 0, ""
    for kind, lv, value in found[anchor + 1:end]:
        if kind == "h" and combat and lv <= combat:
            combat = 0
        if kind == "h" and plain(value) == "Combat":
            combat = lv
            if parent:
                abilities.append(f"**{parent}**")
            continue
        if kind == "h":
            parent = plain(value)
        if kind == "table" and "Hit Dice" in value:
            continue
        (abilities if combat else description).append(paragraph((kind, lv, value)))
    return "\n\n".join(p for p in description if p), "\n\n".join(p for p in abilities if p)


def creatures(ranges):
    for path in sorted((RAW / "monsters").glob("monsters-*.md")):
        found = blocks(path)
        for index, (kind, _, table) in enumerate(found):
            if kind != "table" or "Hit Dice" not in table:
                continue
            rows, kinds, names = stat_block(table)
            if "Hit Dice" not in rows or "Saves" not in rows:
                continue
            description, abilities = creature_text(found, index)
            columns = len(rows["Hit Dice"])
            if not names:
                heading = next(plain(found[i][2]) for i in range(index, -1, -1) if found[i][0] == "h" and plain(found[i][2]) != "Combat")
                names = [heading] if columns == 1 else [f"{heading} {n + 1}" for n in range(columns)]
            for column, name in enumerate(names[:columns]):
                get = lambda label: (rows.get(label, []) + [""] * columns)[column]
                size, _, kind_text = (kinds + [""] * columns)[column].partition(" ")
                space = re.match(r"(.*?ft\.)\s*/\s*(.*)", get("Space/Reach")) or [None, "5 ft.", "5 ft."]
                base = get("Base Attack/Grapple").split("/")
                qualities, ac, abilities_row = get("Special Qualities"), get("Armor Class"), get("Abilities")
                yield entity("Creature", name, description, "creatureTable", {
                    "Stats": {
                        "Size": size if size in SIZES else "Medium",
                        "Type": kind_text.strip() if size in SIZES else f"{size} {kind_text}".strip(),
                        "Hit Dice": get("Hit Dice"),
                        "CR": get("Challenge Rating"),
                        "Initiative": first_int(get("Initiative")),
                        "Speed": get("Speed"),
                        "Space": space[1],
                        "Reach": space[2],
                        "Alignment": get("Alignment") or ("Always neutral" if kind_text.split(" (")[0] in ("Animal", "Vermin") else ""),
                    },
                    "Defense": {
                        "AC": first_int(ac, 10),
                        "Touch": found_int(r"touch\s*(\d+)", ac, 10),
                        "Flat footed": found_int(r"flat-footed\s*(\d+)", ac, 10),
                        "Max HP": found_int(r"\((\d+) hp\)", get("Hit Dice"), 1),
                        "HP": found_int(r"\((\d+) hp\)", get("Hit Dice"), 1),
                        "Fortitude": found_int(r"Fort\s*([+-]?\d+)", get("Saves")),
                        "Reflex": found_int(r"Ref\s*([+-]?\d+)", get("Saves")),
                        "Will": found_int(r"Will\s*([+-]?\d+)", get("Saves")),
                        "Damage reduction": (re.search(r"damage reduction ([^,;]+)", qualities, re.I) or [None, ""])[1].strip(),
                        "Spell resistance": found_int(r"spell resistance (\d+)", qualities),
                    },
                    "Offense": {
                        "Base Attack": first_int(base[0]),
                        "Grapple": first_int(base[1] if len(base) > 1 else ""),
                        "Special Attacks": get("Special Attacks"),
                    },
                    "Attacks": attacks(get("Full Attack") or get("Attack"), ranges),
                    "Statistics": {stat: found_int(stat + r"\s*(\d+)", abilities_row) for stat in ["Str", "Dex", "Con", "Int", "Wis", "Cha"]},
                    "Notes": {
                        "Special Qualities": qualities,
                        "Skills": get("Skills"),
                        "Feats": get("Feats"),
                        "Environment": get("Environment"),
                        "Organization": get("Organization"),
                        "Treasure": get("Treasure"),
                        "Advancement": get("Advancement"),
                        "Level Adjustment": get("Level Adjustment"),
                        "Special abilities": abilities,
                    },
                })


def unique(entities):
    seen, result = set(), []
    for e in entities:
        if (e["type"], e["name"].lower()) not in seen:
            seen.add((e["type"], e["name"].lower()))
            result.append(e)
    return result


equipment = blocks(RAW / "basic-rules-and-legal" / "equipment.md")
entities = unique([
    *weapons(equipment), *armor(equipment), *goods(equipment), *ammunition(equipment), *magic_items(), *spells(),
    *feats(RAW / "basic-rules-and-legal" / "feats.md", 3), *feats(RAW / "monsters" / "monster-feats.md", 2),
    *creatures(weapon_ranges(equipment)),
])
entities.sort(key=lambda e: (e["type"], e["name"]))
library = {
    "name": "D&D 3.5 SRD (OGL)",
    "description": "Weapons, armor, adventuring gear, rings, rods, staffs, wondrous items, spells, feats and monsters from the Revised (v3.5) System Reference Document by Wizards of the Coast, Open Game Content under the Open Game License v1.0a. Converted from srd-v3.5-md (https://github.com/olimot/srd-v3.5-md). See the LICENSE file next to this library.",
    "url": "/systems/dnd35/dnd35.json",
    "gamemaster": "",
    "entities": entities,
}
json.dump(library, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(len(entities), "items:", {kind: sum(1 for e in entities if e["type"] == kind) for kind in sorted({e["type"] for e in entities})})
