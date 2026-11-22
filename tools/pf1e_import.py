"""Builds the Pathfinder 1st edition library from PSRD-Data.

PSRD-Data (https://github.com/devonjones/PSRD-Data) holds the Pathfinder
Reference Document, Paizo's Open Game Content, as SQLite databases. This uses
the Core Rulebook (book-cr.db) and Bestiary (book-b1.db).

    python3 tools/pf1e_import.py <dir with book-cr.db and book-b1.db> systems/pf1e/pf1e.json
"""

import html
import json
import re
import sqlite3
import sys
from pathlib import Path

RAW = Path(sys.argv[1])
OUT = sys.argv[2]
SYSTEM = "Pathfinder1e"


def text(fragment):
    if not fragment:
        return ""
    fragment = re.sub(r"<(b|strong)>(.*?)</\1>", r"**\2**", fragment, flags=re.S)
    fragment = re.sub(r"<(i|em)>(.*?)</\1>", r"*\2*", fragment, flags=re.S)
    fragment = re.sub(r"<li>", "\n- ", fragment)
    fragment = re.sub(r"</p>|<br\s*/?>|</tr>|</h\d>", "\n\n", fragment)
    fragment = re.sub(r"</t[dh]>", " | ", fragment)
    fragment = re.sub(r"<[^>]+>", "", fragment)
    fragment = html.unescape(re.sub(r"&(mdash|ndash|times)(?!;)", r"&\1;", fragment)).replace("–", "-").replace("—", "-").replace("×", "x")
    fragment = re.sub(r"\*\*\s*\*\*", "", fragment)
    fragment = re.sub(r"[ \t]+", " ", fragment)
    fragment = re.sub(r"\n\s*\n\s*(\n\s*)+", "\n\n", fragment)
    return fragment.strip()


def cell(fragment):
    value = text(fragment).strip("* ")
    return "" if value == "-" else value


def entity(kind, name, description, ruleset, values):
    return {
        "type": kind,
        "name": name,
        "description": description,
        "images": {},
        "rulesets": [{"system": SYSTEM, "implementation": {ruleset: values}}],
    }


def descendants(db, section_id):
    left, right = db.execute("select lft, rgt from sections where section_id = ?", (section_id,)).fetchone()
    return db.execute("select section_id, type, name, coalesce(body, description) from sections where lft > ? and rgt < ? order by lft", (left, right)).fetchall()


def full_text(db, section_id, body, skip=()):
    parts = [text(body)] if body else []
    for _, kind, name, child in descendants(db, section_id):
        if name in skip or kind in ("table",):
            continue
        if child:
            parts.append((f"**{name}** " if name else "") + text(child))
    return "\n\n".join(p for p in parts if p)


def table_rows(db, section_id):
    body = db.execute("select body from sections where section_id = ?", (section_id,)).fetchone()[0]
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S):
        yield re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)


def item_descriptions(db):
    found = {}
    for name, body in db.execute("select name, body from sections where type = 'item'"):
        found[name.lower()] = text(body)
    return found


def weapons(db):
    descriptions = item_descriptions(db)
    table = db.execute("select section_id from sections where type = 'table' and name = 'Table: Weapons' order by section_id").fetchone()[0]
    category, group = "Simple", ""
    for cells in table_rows(db, table):
        first = cell(cells[0])
        if first.endswith("Weapons") and len(cells) > 1:
            category = first.split()[0]
            continue
        if len(cells) == 1:
            group = first.replace(" Weapons", "").replace(" Attacks", "").lower()
            continue
        if len(cells) < 9:
            continue
        if group == "unarmed":
            proficiency = "Unarmed" if first.lower().startswith("unarmed") else f"{category} light melee"
        elif group == "ranged":
            proficiency = f"{category} ranged"
        elif group == "ammunition":
            continue
        else:
            proficiency = f"{category} {group}"
        name = first.split("<sup>")[0].strip()
        yield entity("Weapons", name, descriptions.get(name.lower(), ""), "pf1Weapon", {"Stats": {
            "Proficiency": proficiency,
            "Dmg S": cell(cells[2]),
            "Dmg M": cell(cells[3]),
            "Critical": cell(cells[4]),
            "Range": cell(cells[5]),
            "Type": cell(cells[7]),
            "Special": cell(cells[8]),
            "Cost": cell(cells[1]),
            "Weight": cell(cells[6]),
        }})


def armor(db):
    descriptions = item_descriptions(db)
    table = db.execute("select section_id from sections where type = 'table' and name = 'Table: Armor and Shields' order by section_id").fetchone()[0]
    kind = "Light"
    for cells in table_rows(db, table):
        if len(cells) == 1:
            label = cell(cells[0]).lower()
            kind = "Shield" if "shield" in label else "Light" if "light" in label else "Medium" if "medium" in label else "Heavy" if "heavy" in label else kind
            continue
        if len(cells) < 9:
            continue
        name = cell(cells[0])
        yield entity("Armor", name, descriptions.get(name.lower(), ""), "pf1Armor", {"Stats": {
            "Type": kind,
            "Armor Bonus": cell(cells[2]).lstrip("+"),
            "Max Dex": cell(cells[3]).lstrip("+"),
            "Check Penalty": cell(cells[4]) or "0",
            "Spell Failure": cell(cells[5]),
            "Speed": cell(cells[6]) + (" / " + cell(cells[7]) if cell(cells[7]) else ""),
            "Cost": cell(cells[1]),
            "Weight": cell(cells[8]),
        }})


SLOTS = {"ring": "Ring", "neck": "Neck", "body": "Body", "feet": "Feet", "head": "Head", "shoulders": "Shoulders", "headband": "Headband",
         "belt": "Belt", "chest": "Chest", "eyes": "Eyes", "hands": "Hands", "wrists": "Wrists", "rod": "Rod", "staff": "Staff", "wand": "Wand"}


def items(db):
    query = """select s.section_id, s.name, s.subtype, s.body, d.aura, d.slot, d.cl, d.price, d.weight
               from sections s join item_details d using(section_id) where s.type = 'item' and d.aura is not null"""
    for section_id, name, subtype, body, aura, slot, cl, price, weight in db.execute(query):
        yield entity("Equipment", name, full_text(db, section_id, body), "pf1Item", {"Stats": {
            "Slot": slot or SLOTS.get(subtype or "", "") or "none",
            "Aura": aura or "",
            "CL": cl or "",
            "Price": price or "",
            "Weight": cell(weight or ""),
        }})


def spells(db):
    query = """select s.section_id, s.name, s.body, d.school, d.subschool_text, d.descriptor_text, d.level_text, d.component_text,
                      d.casting_time, d.range, d.duration, d.saving_throw, d.spell_resistance
               from sections s join spell_details d using(section_id) where s.type = 'spell'"""
    for section_id, name, body, school, subschool, descriptor, level, components, casting, rng, duration, save, resistance in db.execute(query):
        school_text = (school or "").capitalize() + (f" ({subschool})" if subschool else "") + (f" [{descriptor}]" if descriptor else "")
        yield entity("Spells", name, full_text(db, section_id, body), "pf1Spell", {"Stats": {
            "School": school_text,
            "Level": (level or "").replace(":", ""),
            "Casting Time": casting or "",
            "Components": components or "",
            "Range": rng or "",
            "Duration": duration or "",
            "Saving Throw": save or "",
            "Spell Resistance": resistance or "",
        }})


def feats(db):
    types = {}
    for section_id, kind in db.execute("select section_id, feat_type from feat_types"):
        types.setdefault(section_id, []).append(kind)
    for section_id, name, description in db.execute("select section_id, name, description from sections where type = 'feat'"):
        prerequisites = ""
        parts = [text(description)] if description else []
        for _, kind, child_name, child in descendants(db, section_id):
            if child_name == "Prerequisites" or child_name == "Prerequisite":
                prerequisites = text(child).rstrip(".")
            elif child:
                parts.append(f"**{child_name}** {text(child)}")
        yield entity("Feats", name, "\n\n".join(parts), "pf1Feat", {"Stats": {
            "Type": ", ".join(types.get(section_id, ["General"])),
            "Prerequisites": prerequisites,
        }})


def first_int(value, fallback=0):
    found = re.search(r"-?\d+", value or "")
    return int(found.group()) if found else fallback


def attacks(value):
    rows = []
    for part in re.split(r",\s*(?![^()]*\))|\bor\b", value or ""):
        part = part.strip()
        found = re.match(r"(.*?)\s*([+-]\d+)(?:/[+-]\d+)*\s*(?:touch\s*)?\((.*)\)", part)
        if found:
            rows.append({"Name": found.group(1).strip(), "Attack": int(found.group(2)), "Damage": found.group(3).strip()})
    return rows


def creatures(db):
    columns = [row[1] for row in db.execute("pragma table_info(creature_details)")]
    query = "select s.section_id, s.name, s.description, s.body, d.* from sections s join creature_details d using(section_id) where s.type = 'creature'"
    for row in db.execute(query):
        section_id, name, description, body = row[:4]
        d = dict(zip(columns, row[4:]))
        ac = d["ac"] or ""
        notes = full_text(db, section_id, body)
        yield entity("Creature", name, text(description) + ("\n\n" + notes if notes else ""), "creatureTable", {
            "Stats": {
                "CR": d["cr"] or "",
                "XP": first_int(d["xp"]),
                "Alignment": d["alignment"] or "",
                "Size": d["size"] or "Medium",
                "Type": (d["creature_type"] or "") + (f" ({d['creature_subtype']})" if d["creature_subtype"] else ""),
                "Initiative": first_int(d["init"]),
                "Perception": first_int((re.search(r"Perception\s*([+-]\d+)", d["senses"] or "") or [None, "0"])[1]),
                "Senses": d["senses"] or "",
            },
            "Defense": {
                "AC": first_int(ac, 10),
                "Touch": first_int((re.search(r"touch\s*(\d+)", ac) or [None, "10"])[1]),
                "Flat footed": first_int((re.search(r"flat-footed\s*(\d+)", ac) or [None, "10"])[1]),
                "Max HP": first_int(d["hp"], 1),
                "HP": first_int(d["hp"], 1),
                "Fortitude": first_int(d["fortitude"]),
                "Reflex": first_int(d["reflex"]),
                "Will": first_int(d["will"]),
                "Defensive abilities": d["defensive_abilities"] or "",
                "DR": d["dr"] or "",
                "Immune": d["immune"] or "",
                "Resist": d["resist"] or "",
                "SR": first_int(d["sr"]),
                "Weaknesses": d["weaknesses"] or "",
            },
            "Offense": {
                "Speed": d["speed"] or "",
                "Space": d["space"] or "5 ft.",
                "Reach": d["reach"] or "5 ft.",
                "Special attacks": d["special_attacks"] or "",
            },
            "Attacks": attacks(d["melee"]),
            "Ranged attacks": attacks(d["ranged"]),
            "Statistics": {
                "Str": first_int(d["strength"]),
                "Dex": first_int(d["dexterity"]),
                "Con": first_int(d["constitution"]),
                "Int": first_int(d["intelligence"]),
                "Wis": first_int(d["wisdom"]),
                "Cha": first_int(d["charisma"]),
                "BAB": first_int(d["base_attack"]),
                "CMB": first_int(d["cmb"]),
                "CMD": first_int(d["cmd"], 10),
            },
            "Notes": {
                "Feats": d["feats"] or "",
                "Skills": d["skills"] or "",
                "Languages": d["languages"] or "",
                "Special qualities": d["special_qualities"] or "",
                "Ecology": "; ".join(x for x in [d["environment"], d["organization"], d["treasure"]] if x),
            },
        })


core = sqlite3.connect(RAW / "book-cr.db")
bestiary = sqlite3.connect(RAW / "book-b1.db")
entities = [*weapons(core), *armor(core), *items(core), *spells(core), *feats(core), *creatures(bestiary)]
entities.sort(key=lambda e: (e["type"], e["name"]))
library = {
    "name": "Pathfinder 1e core (OGL)",
    "description": "Weapons, armor, magic items, spells and feats from the Pathfinder Roleplaying Game Core Rulebook and monsters from the Bestiary, Open Game Content under the Open Game License v1.0a. Converted from PSRD-Data (https://github.com/devonjones/PSRD-Data). See the LICENSE file next to this library.",
    "url": "/systems/pf1e/pf1e.json",
    "gamemaster": "",
    "entities": entities,
}
json.dump(library, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(len(entities), "items:", {kind: sum(1 for e in entities if e["type"] == kind) for kind in sorted({e["type"] for e in entities})})
