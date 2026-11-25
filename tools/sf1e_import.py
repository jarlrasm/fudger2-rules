"""Builds the Starfinder 1st edition library from the Foundry VTT Starfinder system.

The Foundry Starfinder system (https://github.com/foundryvtt-starfinder/foundryvtt-starfinder)
keeps its compendium items as one JSON file each under src/items, released as
Open Game Content under the Open Game License v1.0a (its OGL file). This takes
only the items whose source is the Starfinder Core Rulebook ("CRB"): weapons,
armor, other equipment, spells and feats, and the creatures of Alien Archive 1
("AA1"). A creature's skill bonuses are read from its ranks, which hold the
stat block's total in this data.

    python3 -I tools/sf1e_import.py <checkout>/src/items systems/sf1e/sf1e.json
"""

import html
import json
import re
import sys
from pathlib import Path

ITEMS = Path(sys.argv[1])
OUT = sys.argv[2]
SYSTEM = "Starfinder1e"

WEAPON_TYPES = {
    "basicM": "Basic melee",
    "advancedM": "Advanced melee",
    "smallA": "Small arm",
    "longA": "Longarm",
    "heavy": "Heavy weapon",
    "sniper": "Sniper",
    "grenade": "Grenade",
    "special": "Special",
    "solarian": "Special",
}

DAMAGE_TYPES = [
    ("acid", "A"), ("cold", "C"), ("electricity", "E"), ("fire", "F"), ("sonic", "So"),
    ("bludgeoning", "B"), ("piercing", "P"), ("slashing", "S"), ("radiation", "radiation"), ("nonlethal", "nonlethal"),
]

SCHOOLS = {
    "abj": "Abjuration", "con": "Conjuration", "div": "Divination", "enc": "Enchantment",
    "evo": "Evocation", "ill": "Illusion", "nec": "Necromancy", "trs": "Transmutation", "uni": "Universal",
}

CLASSES = [("myst", "Mystic"), ("tech", "Technomancer"), ("wysh", "Witchwarper"), ("precog", "Precog")]

ARMOR_TYPES = {"light": "Light", "heavy": "Heavy", "power": "Powered"}

EQUIPMENT_KINDS = {
    "technological": "Technological", "magic": "Magic", "hybrid": "Hybrid", "augmentation": "Augmentation",
    "consumable": "Consumable", "goods": "Goods", "ammunition": "Ammunition", "upgrade": "Armor upgrade",
    "fusion": "Weapon fusion", "shield": "Shield", "weaponAccessory": "Weapon accessory", "container": "Container",
}


def text(fragment):
    if not fragment:
        return ""
    fragment = re.sub(r"@\w+\[[^\]]*\]\{([^}]*)\}", r"\1", fragment)
    fragment = re.sub(r"@\w+\[([^\]]*)\]", lambda m: m.group(1).split(".")[-1], fragment)
    fragment = re.sub(r"\[\[/r\s*([^\]]*)\]\]", r"\1", fragment)
    fragment = re.sub(r"<(b|strong)>(.*?)</\1>", r"**\2**", fragment, flags=re.S)
    fragment = re.sub(r"<(i|em)>(.*?)</\1>", r"*\2*", fragment, flags=re.S)
    fragment = re.sub(r"<li>", "\n- ", fragment)
    fragment = re.sub(r"</p>|<br\s*/?>|</tr>|</h\d>|<hr\s*/?>", "\n\n", fragment)
    fragment = re.sub(r"</t[dh]>", " | ", fragment)
    fragment = re.sub(r"<[^>]+>", "", fragment)
    fragment = html.unescape(fragment).replace("–", "-").replace("—", "-").replace("×", "x").replace("’", "'")
    fragment = re.sub(r"\*\*\s*\*\*", "", fragment)
    fragment = re.sub(r"[ \t]+", " ", fragment)
    fragment = re.sub(r"\n\s*\n\s*(\n\s*)+", "\n\n", fragment)
    return fragment.strip()


def entity(kind, name, description, ruleset, values):
    return {
        "type": kind,
        "name": name,
        "description": description,
        "images": {},
        "rulesets": [{"system": SYSTEM, "implementation": {ruleset: {"Stats": values}}}],
    }


def items(folder):
    for path in sorted((ITEMS / folder).glob("*.json")):
        item = json.loads(path.read_text())
        if isinstance(item, dict) and "system" in item and str(item["system"].get("source", "")).startswith(("CRB", "Core Rulebook")):
            yield item


def number(value):
    return "" if value in (None, "", 0, "0") else str(value)


def price(value):
    return "" if not value else str(value)


def damage(system):
    parts = []
    for part in system.get("damage", {}).get("parts", []):
        kinds = [code for name, code in DAMAGE_TYPES if (part.get("types") or {}).get(name)]
        parts.append((part.get("formula") or "") + (" " + " & ".join(kinds) if kinds else ""))
    return "; ".join(p.strip() for p in parts if p.strip())


def weapon_range(system):
    rng = system.get("range") or {}
    value = rng.get("value")
    if value and str(value) not in ("0", ""):
        return str(value) + " ft."
    return ""


def properties(system):
    names = []
    for key, value in (system.get("properties") or {}).items():
        if isinstance(value, dict) and value.get("value"):
            names.append(key + (" " + value["extension"] if value.get("extension") else ""))
        elif value is True:
            names.append(key)
    return ", ".join(names)


def weapon(item):
    s = item["system"]
    critical = s.get("critical") or {}
    usage = s.get("usage") or {}
    capacity = s.get("capacity") or {}
    return entity("Weapons", item["name"], text(s["description"]["value"]), "sf1Weapon", {
        "Category": WEAPON_TYPES.get(s.get("weaponType"), "Special"),
        "Level": number(s.get("level")) or "0",
        "Price": price(s.get("price")),
        "Damage": damage(s),
        "Target": (s.get("actionTarget") or "").upper() if s.get("actionTarget") in ("eac", "kac") else "",
        "Range": weapon_range(s),
        "Critical": critical.get("effect") or "",
        "Capacity": number(capacity.get("max")),
        "Usage": number(usage.get("value")) + ((" per " + usage["per"]) if usage.get("value") and usage.get("per") else ""),
        "Bulk": str(s.get("bulk") or ""),
        "Special": properties(s),
    })


def upgrade_slots(system):
    for storage in (system.get("container") or {}).get("storage", []):
        if storage.get("subtype") == "armorUpgrade":
            return str(storage.get("amount", ""))
    return ""


def armor(item):
    s = item["system"]
    a = s["armor"]
    return entity("Armor", item["name"], text(s["description"]["value"]), "sf1Armor", {
        "Type": ARMOR_TYPES.get(a.get("type"), "Light"),
        "Level": number(s.get("level")) or "0",
        "Price": price(s.get("price")),
        "EAC Bonus": str(a.get("eac") or 0),
        "KAC Bonus": str(a.get("kac") or 0),
        "Max Dex": "" if a.get("dex") in (None, "") else str(a.get("dex")),
        "Check Penalty": str(a.get("acp") or 0),
        "Speed Adjustment": number(a.get("speedAdjust")),
        "Upgrade Slots": upgrade_slots(s),
        "Bulk": str(s.get("bulk") or ""),
    })


def equipment(item):
    s = item["system"]
    usage = s.get("usage") or {}
    capacity = s.get("capacity") or {}
    return entity("Equipment", item["name"], text(s["description"]["value"]), "sf1Item", {
        "Kind": EQUIPMENT_KINDS.get(item["type"], "Equipment"),
        "Level": number(s.get("level")) or "0",
        "Price": price(s.get("price")),
        "Bulk": str(s.get("bulk") or ""),
        "Capacity": number(capacity.get("max")),
        "Usage": number(usage.get("value")) + ((" per " + usage["per"]) if usage.get("value") and usage.get("per") else ""),
    })


def spell_range(system):
    rng = system.get("range") or {}
    units = rng.get("units") or ""
    if units == "ft":
        return str(rng.get("value", "")) + " ft."
    return {"close": "Close (25 ft. + 5 ft./2 levels)", "medium": "Medium (100 ft. + 10 ft./level)", "long": "Long (400 ft. + 40 ft./level)",
            "touch": "Touch", "personal": "Personal", "planetary": "Planetary", "system": "System-wide", "plane": "Plane", "unlimited": "Unlimited", "none": ""}.get(units, units)


def duration(system):
    d = system.get("duration") or {}
    units = d.get("units") or ""
    value = d.get("value") or ""
    if units in ("", "instantaneous"):
        return "Instantaneous" if units else ""
    return (str(value) + " " if value else "") + units


def save_text(system):
    save = system.get("save") or {}
    kind = {"fort": "Fortitude", "reflex": "Reflex", "will": "Will"}.get(save.get("type") or "", "")
    return (kind + " " + (save.get("descriptor") or "")).strip() if kind else "None"


def target(system):
    t = (system.get("target") or {}).get("value") or ""
    area = system.get("area") or {}
    if area.get("value"):
        return (str(area.get("value")) + " " + (area.get("units") or "") + " " + (area.get("shape") or "")).strip()
    return str(t)


def spell(item):
    s = item["system"]
    classes = [label + " " + str(s.get("level", 0)) for key, label in CLASSES if (s.get("allowedClasses") or {}).get(key)]
    activation = s.get("activation") or {}
    casting = ((str(activation.get("cost")) + " ") if activation.get("cost") else "") + (activation.get("type") or "")
    return entity("Spells", item["name"], text(s["description"]["value"]), "sf1Spell", {
        "Level": ", ".join(classes),
        "School": SCHOOLS.get(s.get("school"), s.get("school") or ""),
        "Casting Time": casting.replace("action", "standard action") if casting.endswith(" action") and casting.startswith("1 ") else casting,
        "Range": spell_range(s),
        "Targets": target(s),
        "Duration": duration(s),
        "Saving Throw": save_text(s),
        "Spell Resistance": "Yes" if s.get("sr") else "No",
    })


def feat(item):
    s = item["system"]
    description = s["description"]["value"]
    found = re.search(r"Prerequisites?\s*</strong>\s*:?\s*(.*?)</p>", description, flags=re.S) or re.search(r"Prerequisites?:\s*</strong>\s*(.*?)</p>", description, flags=re.S)
    return entity("Feats", item["name"], text(description), "sf1Feat", {
        "Combat": "Yes" if (s.get("details") or {}).get("combat") else "No",
        "Prerequisites": text(found.group(1)).strip(" :.") if found else "",
    })


SKILLS = {
    "acr": "Acrobatics", "ath": "Athletics", "blu": "Bluff", "com": "Computers", "cul": "Culture", "dip": "Diplomacy",
    "dis": "Disguise", "eng": "Engineering", "int": "Intimidate", "lsc": "Life Science", "med": "Medicine",
    "mys": "Mysticism", "per": "Perception", "phs": "Physical Science", "pil": "Piloting", "pro": "Profession",
    "sen": "Sense Motive", "sle": "Sleight of Hand", "ste": "Stealth", "sur": "Survival",
}

XP = {"1/8": 50, "1/6": 65, "1/4": 100, "1/3": 135, "1/2": 200, "1": 400, "2": 600, "3": 800, "4": 1200, "5": 1600,
      "6": 2400, "7": 3200, "8": 4800, "9": 6400, "10": 9600, "11": 12800, "12": 19200, "13": 25600, "14": 38400,
      "15": 51200, "16": 76800, "17": 102400, "18": 153600, "19": 204800, "20": 307200, "21": 409600, "22": 614400,
      "23": 819200, "24": 1228800, "25": 1638400}


def challenge(value):
    for fraction, number in (("1/8", 0.125), ("1/6", 1 / 6), ("1/4", 0.25), ("1/3", 1 / 3), ("1/2", 0.5)):
        if abs(float(value or 0) - number) < 0.01:
            return fraction
    return str(int(float(value or 0)))


def signed(n):
    return ("+" if n >= 0 else "") + str(n)


def speed(attributes):
    sp = attributes.get("speed") or {}
    parts = [f"{sp['land']['base']} ft."] if (sp.get("land") or {}).get("base") else []
    for key, label in (("burrowing", "burrow"), ("climbing", "climb"), ("flying", "fly"), ("swimming", "swim")):
        if (sp.get(key) or {}).get("base"):
            parts.append(f"{label} {sp[key]['base']} ft.")
    return ", ".join(parts) or "0 ft."


def trait(traits, key):
    value = traits.get(key) or {}
    return ", ".join([*(v for v in value.get("value", []) if isinstance(v, str)), *([value["custom"]] if value.get("custom") else [])])


def creature_attack(weapon):
    s = weapon["system"]
    critical = (s.get("critical") or {}).get("effect") or ""
    return {"Name": weapon["name"], "Attack": int(s.get("attackBonus") or 0), "Damage": damage(s) + (f"; critical {critical}" if critical else "")}


def creature(actor):
    s = actor["system"]
    d = s["details"]
    a = s["attributes"]
    t = s["traits"]
    cr = challenge(d.get("cr"))
    weapons = [i for i in actor.get("items", []) if i["type"] == "weapon"]
    abilities = [i for i in actor.get("items", []) if i["type"] == "feat"]
    skills = ", ".join(f"{SKILLS.get(k, k)} {signed(v.get('ranks', 0) + v.get('misc', 0))}" for k, v in s.get("skills", {}).items() if v.get("enabled"))
    gear = ", ".join(i["name"] for i in actor.get("items", []) if i["type"] not in ("weapon", "feat", "spell"))
    perception = s.get("skills", {}).get("per", {})
    return {
        "type": "Creature",
        "name": actor["name"],
        "description": text(d.get("biography", {}).get("value", "")),
        "images": {},
        "rulesets": [{"system": SYSTEM, "implementation": {"creatureTable": {
            "Stats": {
                "CR": cr,
                "XP": XP.get(cr, 0),
                "Alignment": d.get("alignment") or "N",
                "Size": (t.get("size") or "medium").capitalize(),
                "Type": (d.get("type") or "") + (f" ({d['subtype']})" if d.get("subtype") else ""),
                "Initiative": int((a.get("init") or {}).get("value") or 0),
                "Perception": int(perception.get("ranks", 0) + perception.get("misc", 0)) if perception.get("enabled") else 0,
                "Senses": t.get("senses") or "",
            },
            "Defense": {
                "Max HP": int((a.get("hp") or {}).get("max") or 1),
                "HP": int((a.get("hp") or {}).get("max") or 1),
                "EAC": int((a.get("eac") or {}).get("base") or 10),
                "KAC": int((a.get("kac") or {}).get("base") or 10),
                "Fort": int((a.get("fort") or {}).get("base") or 0),
                "Ref": int((a.get("reflex") or {}).get("base") or 0),
                "Will": int((a.get("will") or {}).get("base") or 0),
                "Immunities": trait(t, "ci") + (", " if trait(t, "ci") and trait(t, "di") else "") + trait(t, "di"),
                "Weaknesses": trait(t, "dv"),
                "SR": int(t.get("sr") or 0),
            },
            "Offense": {"Speed": speed(a)},
            "Attacks": [creature_attack(w) for w in weapons if w["system"].get("actionType") == "mwak"],
            "Ranged attacks": [creature_attack(w) for w in weapons if w["system"].get("actionType") == "rwak"],
            "Statistics": {k.capitalize(): int((s["abilities"].get(k) or {}).get("base") or 0) for k in ("str", "dex", "con", "int", "wis", "cha")},
            "Notes": {
                "Skills": skills,
                "Languages": trait(t, "languages"),
                "Gear": gear,
                "Special abilities": "\n\n".join(f"**{i['name']}** " + text((i["system"].get("description") or {}).get("value", "")) for i in abilities),
                "Ecology": "; ".join(x for x in [d.get("environment"), d.get("organization")] if x),
            },
        }}}],
    }


def main():
    entities = []
    for item in items("equipment"):
        if item["type"] == "weapon":
            entities.append(weapon(item))
        elif item["type"] == "equipment" and item["system"].get("armor"):
            entities.append(armor(item))
        elif item["type"] in EQUIPMENT_KINDS:
            entities.append(equipment(item))
    entities += [spell(i) for i in items("spells")]
    entities += [feat(i) for i in items("feats") if i["type"] == "feat"]
    for path in sorted((ITEMS / "alien-archives").glob("*.json")):
        actor = json.loads(path.read_text())
        if isinstance(actor, dict) and str(actor.get("system", {}).get("details", {}).get("source", "")).startswith("AA1"):
            entities.append(creature(actor))
    seen = set()
    unique = []
    for e in sorted(entities, key=lambda e: (e["type"], e["name"].lower())):
        if (e["type"], e["name"]) not in seen:
            seen.add((e["type"], e["name"]))
            unique.append(e)
    library = {
        "name": "Starfinder 1e core (OGL)",
        "description": "Weapons, armor, equipment, spells and feats from the Starfinder Roleplaying Game Core Rulebook and creatures from Starfinder Alien Archive, Open Game Content under the Open Game License v1.0a. Converted from the Foundry VTT Starfinder system (https://github.com/foundryvtt-starfinder/foundryvtt-starfinder). See the LICENSE file next to this library.",
        "url": "/systems/sf1e/sf1e.json",
        "gamemaster": "",
        "entities": unique,
    }
    Path(OUT).write_text(json.dumps(library, indent=1, ensure_ascii=False) + "\n")
    counts = {}
    for e in unique:
        counts[e["type"]] = counts.get(e["type"], 0) + 1
    print(counts)


main()
