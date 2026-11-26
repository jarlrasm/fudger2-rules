"""Builds the Pathfinder 2e or Starfinder 2e library from the Foundry VTT pf2e packs.

Only items whose publication is licensed ORC and comes from a core rulebook are
used; the packs also hold material Foundry may use under its own agreement with
Paizo, which is left out.

    python3 tools/pf2_import.py pf2e <foundry checkout>/packs/pf2e systems/pf2e/pf2e.json
    python3 tools/pf2_import.py sf2e <foundry checkout>/packs/sf2e systems/sf2e/sf2e.json
"""

import html
import json
import re
import sys
from pathlib import Path

GAME = sys.argv[1]
RAW = Path(sys.argv[2])
OUT = sys.argv[3]

SETTINGS = {
    "pf2e": {
        "system": "Pathfinder2e",
        "url": "/systems/pf2e/pf2e.json",
        "weapon": "pf2Weapon",
        "books": ["Pathfinder Player Core", "Pathfinder Player Core 2", "Pathfinder GM Core", "Pathfinder Monster Core"],
        "bestiary": "pathfinder-monster-core",
        "name": "Pathfinder 2e core rulebooks (ORC)",
    },
    "sf2e": {
        "system": "Starfinder2e",
        "url": "/systems/sf2e/sf2e.json",
        "weapon": "sf2Weapon",
        "books": ["Starfinder Player Core", "Starfinder Tech Core", "Starfinder Alien Core"],
        "bestiary": "alien-core-bestiary",
        "name": "Starfinder 2e core rulebooks (ORC)",
    },
}[GAME]

DAMAGE_TYPES = {"bludgeoning": "B", "piercing": "P", "slashing": "S"}
FEAT_TYPES = {"ancestry": "Ancestry", "class": "Class", "general": "General", "skill": "Skill", "archetype": "Archetype"}


def records(pack, books=None):
    for path in sorted((RAW / pack).rglob("*.json")):
        record = json.load(open(path, encoding="utf-8"))
        if not isinstance(record, dict) or "system" not in record:
            continue
        publication = record["system"].get("publication") or record["system"].get("details", {}).get("publication") or {}
        if publication.get("license") == "ORC" and publication.get("title") in (books or SETTINGS["books"]):
            yield record


def inline(match):
    kind, inner, label = match.group(1), match.group(2), match.group(4)
    if label:
        return label
    if kind == "UUID":
        return inner.split(".")[-1]
    if kind == "Damage":
        return re.sub(r"[\[\]()]", " ", inner).replace("  ", " ").strip()
    if kind == "Check":
        parts = dict(p.split(":", 1) for p in inner.split("|") if ":" in p)
        return " ".join(x for x in [f"DC {parts['dc']}" if "dc" in parts else "", "basic" if parts.get("basic") == "true" else "", parts.get("type", "").capitalize()] if x)
    if kind == "Template":
        parts = dict(p.split(":", 1) for p in inner.split("|") if ":" in p)
        return f"{parts.get('distance', '')}-foot {parts.get('type', '')}".strip("- ")
    return inner


def text(value):
    value = value or ""
    value = re.sub(r"@(\w+)\[((?:[^\[\]]|\[[^\]]*\])*)\](\{([^}]*)\})?", inline, value)
    value = re.sub(r"\[\[/\w+ ([^\]]+)\]\](\{([^}]*)\})?", lambda m: m.group(3) or m.group(1), value)
    value = re.sub(r"<li>", "\n- ", value)
    value = re.sub(r"</(p|h\d|ul|ol|table|tr)>|<hr ?/?>|<br ?/?>", "\n\n", value)
    value = re.sub(r"<strong>|</strong>", "**", value)
    value = re.sub(r"<em>|</em>", "*", value)
    value = html.unescape(re.sub(r"<[^>]+>", "", value))
    value = re.sub(r"\b(?:PF2E|SF2E)\.[\w.]+", "", value)
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+\n", "\n", value)).strip()


def description(record):
    system = record["system"]
    return text((system.get("description") or {}).get("value") or system.get("details", {}).get("publicNotes", ""))


def traits(record):
    return ", ".join((record["system"].get("traits") or {}).get("value") or [])


def price(record):
    value = ((record["system"].get("price") or {}).get("value")) or {}
    return " ".join(f"{amount} {coin}" for coin, amount in value.items() if amount) if isinstance(value, dict) else str(value)


def bulk(record):
    value = (record["system"].get("bulk") or {}).get("value")
    return "L" if value == 0.1 else ("" if value in (None, 0) else str(value))


def level(record):
    return int(((record["system"].get("level") or {}).get("value")) or 0)


def entity(type_, record, implementation):
    return {
        "type": type_,
        "name": record["name"],
        "description": description(record),
        "images": {},
        "rulesets": [{"system": SETTINGS["system"], "implementation": implementation}],
    }


def spells():
    for r in records("spells"):
        s = r["system"]
        defense = (s.get("defense") or {}).get("save") or {}
        area = s.get("area") or {}
        yield entity(
            "Spells",
            r,
            {
                "pf2Spell": {
                    "Stats": {
                        "Rank": int((s.get("level") or {}).get("value") or 1),
                        "Traditions": ", ".join((s.get("traits") or {}).get("traditions") or []),
                        "Traits": traits(r),
                        "Cast": str((s.get("time") or {}).get("value") or ""),
                        "Range": (s.get("range") or {}).get("value") or "",
                        "Area": f"{area.get('value')}-foot {area.get('type')}" if area.get("value") else "",
                        "Targets": (s.get("target") or {}).get("value") or "",
                        "Defense": (("basic " if defense.get("basic") else "") + (defense.get("statistic") or "").capitalize()).strip(),
                        "Duration": (s.get("duration") or {}).get("value") or "",
                        "Heightened": "",
                    }
                }
            },
        )


def feats():
    for r in records("feats"):
        s = r["system"]
        actions = (s.get("actions") or {}).get("value")
        action_type = (s.get("actionType") or {}).get("value") or ""
        yield entity(
            "Feats",
            r,
            {
                "pf2Feat": {
                    "Stats": {
                        "Type": FEAT_TYPES.get(s.get("category"), (s.get("category") or "").capitalize()),
                        "Level": level(r),
                        "Traits": traits(r),
                        "Prerequisites": ", ".join(p.get("value", "") for p in (s.get("prerequisites") or {}).get("value") or []),
                        "Actions": f"{actions} action" + ("s" if actions and actions > 1 else "") if action_type == "action" and actions else action_type,
                    }
                }
            },
        )


def weapon(r):
    s = r["system"]
    damage = s.get("damage") or {}
    damage_type = damage.get("damageType") or ""
    return entity(
        "Weapons",
        r,
        {
            SETTINGS["weapon"]: {
                "Stats": {
                    "Category": (s.get("category") or "simple").capitalize(),
                    "Damage": f"{damage.get('dice', 1)}{damage.get('die', '')}" if damage.get("die") else "",
                    "Damage Type": DAMAGE_TYPES.get(damage_type, damage_type),
                    "Range": str(s.get("range") or ""),
                    **({"Reload": str((s.get("reload") or {}).get("value") or "")} if SETTINGS["weapon"] == "pf2Weapon" else {"Magazine": str((s.get("ammo") or {}).get("capacity") or ""), "Usage": str((s.get("expend") or "") or "")}),
                    "Hands": (s.get("usage") or {}).get("value", ""),
                    "Bulk": bulk(r),
                    "Traits": traits(r),
                    "Item Bonus": str(((s.get("runes") or {}).get("potency")) or ""),
                    "Group": s.get("group") or "",
                    "Level": str(level(r)),
                    "Price": price(r),
                }
            }
        },
    )


def armor(r):
    s = r["system"]
    shield = r["type"] == "shield"
    return entity(
        "Armor",
        r,
        {
            "pf2Armor": {
                "Stats": {
                    "Category": "Shield" if shield else (s.get("category") or "light").capitalize(),
                    "AC Bonus": str(s.get("acBonus") or ""),
                    "Dex Cap": "" if shield else str(s.get("dexCap") if s.get("dexCap") is not None else ""),
                    "Strength": str(s.get("strength") or ""),
                    "Check Penalty": str(s.get("checkPenalty") or ""),
                    "Speed Penalty": str(s.get("speedPenalty") or ""),
                    "Bulk": bulk(r),
                    "Traits": traits(r) + (f", Hardness {s.get('hardness')}, HP {(s.get('hp') or {}).get('max')}" if shield else ""),
                    "Level": str(level(r)),
                    "Price": price(r),
                }
            }
        },
    )


def item(r):
    if GAME == "sf2e" and "augmentation" in traits(r):
        return entity("Augmentations", r, {"augmentationStats": {"Stats": {"Level": level(r), "System": "", "Traits": traits(r), "Price": price(r)}}})
    return entity(
        "Equipment",
        r,
        {"pf2Item": {"Stats": {"Level": level(r), "Bulk": bulk(r), "Traits": traits(r), "Usage": (r["system"].get("usage") or {}).get("value", ""), "Price": price(r)}}},
    )


def equipment():
    for r in records("equipment"):
        if r["type"] == "weapon":
            yield weapon(r)
        elif r["type"] in ("armor", "shield"):
            yield armor(r)
        else:
            yield item(r)


def options():
    for pack, kind in [("ancestries", "Ancestry"), ("heritages", "Heritage"), ("backgrounds", "Background"), ("classes", "Class")]:
        for r in records(pack):
            s = r["system"]
            boosts = s.get("boosts") or {}
            yield entity(
                "Character Options",
                r,
                {
                    "pf2Option": {
                        "Stats": {
                            "Kind": kind,
                            "HP": str(s.get("hp") or ""),
                            "Key Attribute": ", ".join((s.get("keyAbility") or {}).get("value") or []).upper(),
                            "Boosts": "; ".join(", ".join(b.get("value") or []).upper() for b in boosts.values()) if isinstance(boosts, dict) else "",
                            "Traits": traits(r),
                        }
                    }
                },
            )


def signed(n):
    return f"+{n}" if n >= 0 else str(n)


def trait_number(traits, prefix):
    for trait in traits:
        if trait.startswith(prefix) and trait[len(prefix):].isdigit():
            return int(trait[len(prefix):])
    return 0


def strike_traits(traits):
    increment = trait_number(traits, "range-increment-")
    flat = trait_number(traits, "range-")
    ranged = bool(increment or flat)
    return {
        "Agile": "agile" in traits,
        "Ranged": ranged,
        "Range": increment or (flat + 5) // 6,
        "Reach": trait_number(traits, "reach-") or 5,
    }


def creature(r):
    s = r["system"]
    attributes = s.get("attributes") or {}
    saves = s.get("saves") or {}
    strikes = []
    abilities = []
    spells_known = []
    for i in r.get("items", []):
        if i["type"] == "melee":
            damage = " plus ".join(f"{d.get('damage')} {d.get('damageType', '')}".strip() for d in (i["system"].get("damageRolls") or {}).values())
            traits = (i["system"].get("traits") or {}).get("value") or []
            strikes.append({"Name": i["name"], "Strike": int((i["system"].get("bonus") or {}).get("value") or 0), "Damage": damage} | strike_traits(traits))
        elif i["type"] == "action":
            abilities.append(f"**{i['name']}.** {text((i['system'].get('description') or {}).get('value'))}")
        elif i["type"] == "spell":
            spells_known.append(i["name"])
    hp = (attributes.get("hp") or {}).get("max") or 1
    skills = ", ".join(f"{name.capitalize()} {signed(v.get('base') or v.get('value') or 0)}" for name, v in (s.get("skills") or {}).items())
    resist = lambda key: ", ".join(f"{x.get('type')} {x.get('value', '')}".strip() for x in attributes.get(key) or [])
    return {
        "type": "Creature",
        "name": r["name"],
        "description": text((s.get("details") or {}).get("publicNotes")),
        "images": {},
        "rulesets": [
            {
                "system": SETTINGS["system"],
                "implementation": {
                    "pf2Creature": {
                        "Stats": {
                            "Level": int(((s.get("details") or {}).get("level") or {}).get("value") or 0),
                            "Traits": ", ".join((s.get("traits") or {}).get("value") or []),
                            "Perception": int((s.get("perception") or {}).get("mod") or 0),
                            "AC": int((attributes.get("ac") or {}).get("value") or 10),
                            "Fortitude": int((saves.get("fortitude") or {}).get("value") or 0),
                            "Reflex": int((saves.get("reflex") or {}).get("value") or 0),
                            "Will": int((saves.get("will") or {}).get("value") or 0),
                            "Max HP": int(hp),
                            "HP": int(hp),
                            "Speed": int((attributes.get("speed") or {}).get("value") or 0),
                            "Immunities": ", ".join(x.get("type", "") for x in attributes.get("immunities") or []),
                            "Resistances": resist("resistances"),
                            "Weaknesses": resist("weaknesses"),
                        },
                        "Strikes": strikes,
                        "Notes": {"Skills": skills, "Abilities": "\n\n".join(abilities), "Spells": ", ".join(spells_known)},
                    }
                },
            }
        ],
    }


def creatures():
    for r in records(SETTINGS["bestiary"]):
        if r["type"] == "npc":
            yield creature(r)


library = {
    "name": SETTINGS["name"],
    "description": "Material from Paizo's core rulebooks, used under the ORC License (Open RPG Creative License, https://paizo.com/orclicense). Converted from the Foundry VTT pf2e system's data (https://github.com/foundryvtt/pf2e). Only content the data marks as ORC-licensed is included; Paizo's Reserved Material is not part of this licence grant. See the LICENSE file next to this library.",
    "url": SETTINGS["url"],
    "gamemaster": "",
    "entities": list(spells()) + list(feats()) + list(equipment()) + list(options()) + list(creatures()),
}

json.dump(library, open(OUT, "w"), ensure_ascii=False)
print(len(library["entities"]), "entities")
