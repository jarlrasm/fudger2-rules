import json
import re
import sys

RAW = sys.argv[1]
OUT = sys.argv[2]
SYSTEM = "DND5e"


def load(name):
    data = json.load(open(f"{RAW}/{name}.json"))["results"]
    return [x for x in data if x["document"]["key"] == "srd-2024"]


def clean(text):
    if not text:
        return ""
    lines = []
    for line in text.replace("\r", "").split("\n"):
        stripped = line.strip()
        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if all(re.fullmatch(r":?-*:?", c) for c in cells):
                continue
            if not any(cells):
                continue
            lines.append(" | ".join(cells))
        else:
            lines.append(line.rstrip())
    text = "\n".join(lines)
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def entity(type_, name, description, implementation):
    return {
        "type": type_,
        "name": name,
        "description": description,
        "rulesets": [{"system": SYSTEM, "implementation": implementation}],
    }


def ordinal(n):
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")


CASTING_TIMES = {
    "action": "Action",
    "bonus-action": "Bonus Action",
    "reaction": "Reaction",
    "1minute": "1 minute",
    "10minutes": "10 minutes",
    "1hour": "1 hour",
    "8hours": "8 hours",
    "12hours": "12 hours",
    "24hours": "24 hours",
}


def spells():
    result = []
    for s in sorted(load("spells"), key=lambda x: x["name"]):
        casting = CASTING_TIMES.get(s["casting_time"], s["casting_time"])
        if s["casting_time"] == "reaction" and s.get("reaction_condition"):
            casting += ", " + s["reaction_condition"]
        if s["ritual"]:
            casting += " or Ritual"
        components = []
        if s["verbal"]:
            components.append("V")
        if s["somatic"]:
            components.append("S")
        if s["material"]:
            components.append(f"M ({s['material_specified']})" if s.get("material_specified") else "M")
        duration = s["duration"][:1].upper() + s["duration"][1:]
        if s["concentration"]:
            duration = "Concentration, up to " + s["duration"]
        school = s["school"]["name"]
        classes = ", ".join(c["name"] for c in s["classes"])
        if s["level"] == 0:
            header = f"*{school} Cantrip ({classes})*"
        else:
            header = f"*Level {s['level']} {school} ({classes})*"
        parts = [header, clean(s["desc"])]
        if s.get("higher_level"):
            label = "Cantrip Upgrade." if s["level"] == 0 else "Using a Higher-Level Spell Slot."
            parts.append(f"{label} {clean(s['higher_level'])}")
        stats = {
            "level": s["level"],
            "Casting time": casting,
            "Range": s["range_text"] or "",
            "Components": ", ".join(components),
            "Duration": duration,
        }
        result.append(entity("Spells", s["name"], "\n\n".join(parts), {"spellStats": {"Stats": stats}, "secondary": {}}))
    return result


RANGED = {
    "Blowgun", "Hand Crossbow", "Heavy Crossbow", "Light Crossbow", "Longbow",
    "Musket", "Pistol", "Shortbow", "Sling", "Dart",
}


def fmt_weight(item):
    if not item or item.get("weight") in (None, ""):
        return ""
    w = float(item["weight"])
    if w == 0:
        return "-"
    text = f"{w:g}"
    return f"{text} lb."


def fmt_cost(item):
    if not item or item.get("cost") in (None, ""):
        return ""
    c = float(item["cost"])
    if c >= 1:
        return f"{c:g} GP"
    if c >= 0.1:
        return f"{c * 10:g} SP"
    return f"{c * 100:g} CP"


def weapons(items):
    result = []
    for w in sorted(load("weapons"), key=lambda x: x["name"]):
        item = items.get(w["key"])
        props = []
        mastery = None
        for p in sorted(w["properties"], key=lambda p: p["property"]["name"]):
            prop = p["property"]
            if prop["type"] == "Mastery":
                mastery = prop
                continue
            props.append(f"{prop['name']} ({p['detail']})" if p["detail"] else prop["name"])
        damage = f"{w['damage_dice']} {w['damage_type']['name'].lower()}"
        kind = ("Simple" if w["is_simple"] else "Martial") + (" Ranged" if w["name"] in RANGED else " Melee") + " Weapon"
        parts = [f"*{kind}*"]
        cost = fmt_cost(item)
        if cost:
            parts.append(f"Cost: {cost}")
        if mastery:
            parts.append(f"Mastery: {mastery['name']}. {clean(mastery['desc'])}")
        stats = {"Damage": damage, "Weight": fmt_weight(item), "Properties": ", ".join(props)}
        type_ = "Ranged weapons" if w["name"] in RANGED else "Melee weapons"
        result.append(entity(type_, w["name"], "\n\n".join(parts), {"secondary": {}, "weaponStats": {"Stats": stats}}))
    return result


def armour(items):
    result = []
    for a in sorted(load("armor"), key=lambda x: x["ac_base"]):
        item = items.get(a["key"])
        if a["name"] == "Shield":
            desc = "*Shield*\n\nShield gives +2 AC bonus. You gain the benefit of a Shield only if you have training with it."
            cost = fmt_cost(item)
            if cost:
                desc += f"\n\nCost: {cost}. Weight: {fmt_weight(item)}"
            result.append(entity("Other items", "Shield", desc, {}))
            continue
        stats = {
            "AC": a["ac_base"],
            "Minimum strength": a["strength_score_required"] or 0,
            "Stealth disadvantage": a["grants_stealth_disadvantage"],
            "Weight": fmt_weight(item),
        }
        if not a["ac_add_dexmod"]:
            stats["Max dex modifier"] = 0
        elif a["ac_cap_dexmod"] is not None:
            stats["Max dex modifier"] = a["ac_cap_dexmod"]
        parts = [f"*{a['category'].capitalize()} Armor*", f"Armor Class: {a['ac_display']}"]
        if a["strength_score_required"]:
            parts.append(f"Strength: {a['strength_score_required']}")
        cost = fmt_cost(item)
        if cost:
            parts.append(f"Cost: {cost}")
        result.append(entity("Armour", a["name"], "\n".join(parts), {"armourStats": {"Stats": stats}}))
    return result


def feats():
    result = []
    for f in sorted(load("feats"), key=lambda x: x["name"]):
        parts = [f"*{f['type']} Feat" + (f" (Prerequisite: {f['prerequisite']})*" if f.get("prerequisite") else "*")]
        if f.get("desc"):
            parts.append(clean(f["desc"]))
        for b in f["benefits"]:
            parts.append(clean(b["desc"]))
        result.append(entity("Feats", f["name"], "\n\n".join(parts), {"featStats": {"Type": f["type"]}}))
    return result


def species():
    result = []
    for s in sorted(load("species"), key=lambda x: x["name"]):
        features = [
            {"Name": t["name"], "Description": clean(t["desc"])}
            for t in sorted(s["traits"], key=lambda t: t["order"] or 0)
        ]
        stats = {"Features": features, "Subraces": []}
        result.append(entity("Races", s["name"], clean(s.get("desc", "")), {"raceStats": {"Stats": stats}}))
    return result


ABILITY = {
    "Strength": "Str", "Dexterity": "Dex", "Constitution": "Con",
    "Intelligence": "Int", "Wisdom": "Wis", "Charisma": "Cha",
}

SPELLCASTING = {
    "Bard": "Charisma", "Cleric": "Wisdom", "Druid": "Wisdom", "Paladin": "Charisma",
    "Ranger": "Wisdom", "Sorcerer": "Charisma", "Warlock": "Charisma", "Wizard": "Intelligence",
}

SKIP_FEATURES = {"PROFICIENCY_BONUS", "SPELL_SLOTS", "CLASS_TABLE_DATA"}


def class_features(c, level_offset_name=None):
    out = []
    for f in c["features"]:
        if f["feature_type"] in SKIP_FEATURES:
            continue
        levels = [g["level"] for g in f["gained_at"]]
        level = min(levels) if levels else 1
        out.append({"Level": level, "Name": f["name"], "Description": clean(f["desc"])})
    columns = []
    for f in c["features"]:
        if f["feature_type"] != "CLASS_TABLE_DATA" or not f["data_for_class_table"]:
            continue
        rows = sorted(f["data_for_class_table"], key=lambda r: r["level"])
        steps = []
        last = None
        for r in rows:
            if r["column_value"] != last:
                steps.append(f"level {r['level']}: {r['column_value']}")
                last = r["column_value"]
        columns.append(f"{f['name']}: " + ", ".join(steps))
    if columns:
        out.append({"Level": 1, "Name": f"{c['name']} Features Table", "Description": "\n".join(columns)})
    out.sort(key=lambda x: (x["Level"], 0 if x["Name"].startswith("Core ") else 1, x["Name"]))
    return out


def spell_levels(c):
    table = {str(s): {"levels": {str(l): {"Number of spells": 0} for l in range(1, 21)}} for s in range(1, 10)}
    found = False
    pact_slots = {}
    pact_level = {}
    for f in c["features"]:
        if f["feature_type"] == "SPELL_SLOTS":
            m = re.match(r"(\d)", f["name"])
            if not m:
                continue
            for row in f["data_for_class_table"]:
                value = int(row["column_value"]) if row["column_value"].strip().isdigit() else 0
                table[m.group(1)]["levels"][str(row["level"])]["Number of spells"] = value
                found = True
        if f["feature_type"] == "CLASS_TABLE_DATA" and f["name"] == "Spell Slots":
            pact_slots = {r["level"]: int(r["column_value"]) for r in f["data_for_class_table"]}
        if f["feature_type"] == "CLASS_TABLE_DATA" and f["name"] == "Slot Level":
            pact_level = {r["level"]: int(re.match(r"\d", r["column_value"]).group(0)) for r in f["data_for_class_table"]}
    for level, slots in pact_slots.items():
        table[str(pact_level[level])]["levels"][str(level)]["Number of spells"] = slots
        found = True
    return table if found else {}


def classes():
    raw = load("classes")
    base = {c["name"]: c for c in raw if not c["subclass_of"]}
    subs = [c for c in raw if c["subclass_of"]]
    result = []

    def make(name, c, features):
        stats = {
            "HitDie": int(c["hit_dice"].lstrip("Dd")),
            "SavingThrows": [{"Attr": ABILITY[s["name"]]} for s in c["saving_throws"]],
            "SpellcastingAbilityModifier": SPELLCASTING.get(c["name"], "None"),
            "Features": features,
            "Spellevels": spell_levels(c),
        }
        return entity("Classes", name, clean(c.get("desc", "")), {"classStats": {"Stats": stats}})

    for name in sorted(base):
        c = base[name]
        result.append(make(name, c, class_features(c)))
    for s in sorted(subs, key=lambda x: x["name"]):
        parent = base[s["subclass_of"]["name"]]
        features = class_features(parent) + class_features(s)
        features.sort(key=lambda x: (x["Level"], 0 if x["Name"].startswith("Core ") else 1))
        result.append(make(f"{parent['name']} ({s['name']})", parent, features))
    return result


SKILLS = {
    "acrobatics": "Acrobatics", "animal_handling": "Animal Handling", "arcana": "Arcana",
    "athletics": "Athletics", "deception": "Deception", "history": "History", "insight": "Insight",
    "intimidation": "Intimidation", "investigation": "Investigation", "medicine": "Medicine",
    "nature": "Nature", "perception": "Perception", "performance": "Performance",
    "persuasion": "Persuasion", "religion": "Religion", "sleight_of_hand": "Sleight of Hand",
    "stealth": "Stealth", "survival": "Survival",
}

ABILITY_KEYS = {
    "strength": "Str", "dexterity": "Dex", "constitution": "Con",
    "intelligence": "Int", "wisdom": "Wis", "charisma": "Cha",
}


def cr_text(cr):
    return {0.125: "1/8", 0.25: "1/4", 0.5: "1/2"}.get(cr, f"{cr:g}")


def action_name(a):
    name = a["name"]
    limit = a.get("usage_limits")
    if limit:
        if limit["type"] == "PER_DAY" and "/Day" not in name:
            name += f" ({limit['param']}/Day)"
        elif limit["type"] in ("RECHARGE_ON_ROLL", "RECHARGE") and "Recharge" not in name:
            p = limit["param"]
            name += " (Recharge 6)" if p == 6 else f" (Recharge {p}-6)"
    if a.get("limited_to_form") and "Only" not in name:
        name += f" ({a['limited_to_form']})"
    if a["action_type"] == "LEGENDARY_ACTION" and (a.get("legendary_action_cost") or 1) > 1:
        name += f" (Costs {a['legendary_action_cost']} Actions)"
    return name


def creatures():
    result = []
    for c in sorted(load("creatures"), key=lambda x: x["name"]):
        speed = c["speed"]
        unit = "ft."
        speeds = [f"{speed.get('walk', 0)} {unit}"]
        for kind in ["burrow", "climb", "fly", "swim"]:
            if speed.get(kind):
                text = f"{kind.capitalize()} {speed[kind]} {unit}"
                if kind == "fly" and speed.get("hover"):
                    text += " (hover)"
                speeds.append(text)
        senses = []
        for key, label in [("blindsight_range", "Blindsight"), ("darkvision_range", "Darkvision"),
                           ("tremorsense_range", "Tremorsense"), ("truesight_range", "Truesight")]:
            if c.get(key):
                senses.append(f"{label} {c[key]:g} ft.")
        ri = c["resistances_and_immunities"]
        imm_cond = ", ".join(d["name"] for d in ri["condition_immunities"])
        immunities = "; ".join(x for x in [", ".join(d["name"] for d in ri["damage_immunities"]), imm_cond] if x)
        resistances = ", ".join(d["name"] for d in ri["damage_resistances"])
        xp = f"{c['experience_points']:,}" if c.get("experience_points") is not None else "0"
        basics = {
            "Armor Class": c["armor_class"],
            "Initiative": c["initiative_bonus"] if c.get("initiative_bonus") is not None else c["modifiers"]["dexterity"],
            "Speed": ", ".join(speeds),
            "Immunities": immunities,
            "Resistances": resistances,
            "Gear": "",
            "Senses": ", ".join(senses),
            "Passive Perception": c["passive_perception"],
            "Languages": c["languages"]["as_string"] or "None",
            "Challenge": f"{cr_text(c['challenge_rating'])} ({xp} XP)",
        }
        traits = [{"Name": t["name"], "Description": clean(t["desc"])} for t in c["traits"]]
        if ri["damage_vulnerabilities"]:
            traits.insert(0, {"Name": "Vulnerabilities", "Description": ", ".join(d["name"] for d in ri["damage_vulnerabilities"])})
        lists = {"ACTION": [], "BONUS_ACTION": [], "REACTION": [], "LEGENDARY_ACTION": []}
        for a in sorted(c["actions"], key=lambda a: a["order_in_statblock"] or 0):
            lists[a["action_type"]].append({"Name": action_name(a), "Description": clean(a["desc"])})
        table = {
            "Basics": basics,
            "Hitpoints": {"Current": c["hit_points"], "Max": c["hit_points"]},
            "Ability scores": {ABILITY_KEYS[k]: {"Score": v} for k, v in c["ability_scores"].items()},
            "Saving throws": {ABILITY_KEYS[k]: {"Modifier": v} for k, v in c["saving_throws_all"].items()},
            "Skills": {SKILLS[k]: {"Modifier": v} for k, v in c["skill_bonuses_all"].items()},
            "Traits": traits,
            "Actions": lists["ACTION"],
            "Bonus Actions": lists["BONUS_ACTION"],
            "Reactions": lists["REACTION"],
            "Legendary Actions": lists["LEGENDARY_ACTION"],
        }
        hp = f"HP {c['hit_points']} ({c['hit_dice']})" if c.get("hit_dice") else ""
        ac = f"AC {c['armor_class']}" + (f" ({c['armor_detail']})" if c.get("armor_detail") else "")
        desc = f"*{c['size']['name']} {c['type']['name']}, {c['alignment'].title() if c.get('alignment') else 'Unaligned'}*"
        desc += "\n" + ", ".join(x for x in [ac, hp] if x)
        result.append({
            "type": "Creature",
            "name": c["name"],
            "description": desc,
            "images": {},
            "rulesets": [{"system": SYSTEM, "implementation": {"creatureTable": table, "secondary": {}}}],
        })
    return result


def main():
    raw_items = json.load(open(f"{RAW}/items.json"))["results"]
    items = {}
    for i in raw_items:
        if i["document"]["key"] != "srd-2024":
            continue
        if i.get("weapon"):
            items[i["weapon"]["key"]] = i
        if i.get("armor"):
            items[i["armor"]["key"]] = i
        items.setdefault(i["key"], i)
    entities = (
        spells() + creatures() + weapons(items) + armour(items) + feats() + species() + classes()
    )
    library = {
        "name": "DND SRD 5.2",
        "description": "D&D 2024 (5.5) System Reference Document 5.2. Converted from the Open5e API (https://open5e.com). This work includes material from the System Reference Document 5.2 by Wizards of the Coast LLC, licensed under CC-BY-4.0.",
        "url": "/systems/DND/dndsrd2024.json",
        "gamemaster": "",
        "entities": entities,
    }
    json.dump(library, open(OUT, "w"), ensure_ascii=False)


main()
