import json
import sys

RAW = sys.argv[1]
OUT = sys.argv[2]
SYSTEM = "DungeonWorld"
URL = "/systems/dungeonworld/dungeonworld.json"

data = json.load(open(f"{RAW}/game_data_basic.json"))

RANGE_TAGS = {"hand", "close", "reach", "near", "far"}
STATS = {"str": "STR", "dex": "DEX", "con": "CON", "int": "INT", "wis": "WIS", "cha": "CHA"}


def entity(type_, name, description, implementation):
    return {
        "type": type_,
        "name": name,
        "description": (description or "").strip(),
        "images": {},
        "rulesets": [{"system": SYSTEM, "implementation": implementation}],
    }


def stat_of(description):
    lowered = (description or "").lower()
    for key, stat in STATS.items():
        if f"roll+{key}" in lowered:
            return stat
    return ""


def tag_text(tag):
    if isinstance(tag, dict):
        return ", ".join(f"{value} {key}" if key in ("weight", "coins", "uses", "ammo") else f"{key} {value}" for key, value in tag.items())
    return str(tag)


def move(m, class_name, level):
    return entity(
        "Moves",
        m["name"],
        m.get("description", ""),
        {
            "moveStats": {
                "Stats": {
                    "Class": class_name,
                    "Level": level,
                    "Stat": stat_of(m.get("description")),
                    "Requires": m.get("requires", "") or m.get("replaces", "") or "",
                }
            }
        },
    )


def moves():
    result = [move(m, "Basic", "Basic") for m in data["basic_moves"]]
    result += [move(m, "Special", "Special") for m in data["special_moves"]]
    for c in data["classes"].values():
        for m in c.get("race_moves", []):
            result.append(move({**m, "name": f"{c['name']}: {m['name']}"}, c["name"], "Starting"))
        result += [move(m, c["name"], "Starting") for m in c.get("starting_moves", [])]
        result += [move(m, c["name"], "2-5") for m in c.get("advanced_moves_1", [])]
        result += [move(m, c["name"], "6-10") for m in c.get("advanced_moves_2", [])]
    return result


def kind_of(item):
    names = {t if isinstance(t, str) else next(iter(t)) for t in item.get("tags", [])}
    if names & RANGE_TAGS or any(isinstance(t, dict) and "damage" in t for t in item.get("tags", [])):
        return "Weapon"
    if any(isinstance(t, dict) and "armor" in t for t in item.get("tags", [])):
        return "Armor"
    if "applied" in names or "dangerous" in names and "poison" in item["name"].lower():
        return "Poison"
    return "Gear"


def tag_value(item, key):
    for t in item.get("tags", []):
        if isinstance(t, dict) and key in t:
            return str(t[key])
    return ""


def equipment():
    return [
        entity(
            "Equipment",
            e["name"],
            e.get("description", ""),
            {
                "equipmentStats": {
                    "Stats": {
                        "Kind": kind_of(e),
                        "Tags": ", ".join(tag_text(t) for t in e.get("tags", []) if not (isinstance(t, dict) and ("coins" in t or "weight" in t))),
                        "Weight": tag_value(e, "weight"),
                        "Cost": tag_value(e, "coins"),
                    }
                }
            },
        )
        for e in data["equipment"].values()
    ]


def classes():
    result = []
    for c in data["classes"].values():
        alignments = "\n".join(f"**{a['name']}:** {a['description']}" for a in c.get("alignments_list", []))
        races = "\n".join(f"**{m['name']}:** {m['description']}" for m in c.get("race_moves", []))
        looks = "\n".join(", ".join(group) for group in c.get("looks", []))
        description = "\n\n".join(part for part in [c.get("description", ""), "**Looks**\n\n" + looks if looks else "", "**Starting gear:** " + c.get("starting_gear", "") if c.get("starting_gear") else ""] if part)
        result.append(
            entity(
                "Classes",
                c["name"],
                description,
                {
                    "classStats": {
                        "Stats": {
                            "Base HP": str(c.get("base_hp", "")),
                            "Damage": c.get("damage", ""),
                            "Base Load": str(c.get("load", "")),
                            "Races": races,
                            "Alignments": alignments,
                            "Bonds": "\n".join(c.get("bonds", [])),
                        }
                    }
                },
            )
        )
    return result


def monster_stats(m):
    stats = {"Tags": ", ".join(t for t in m.get("tags", []) if t), "Instinct": m.get("instinct", "")}
    if "hp" in m:
        stats["Max HP"] = m["hp"]
        stats["HP"] = m["hp"]
    if "armor" in m:
        stats["Armor"] = m["armor"]
    attacks = m.get("attacks", [])
    if attacks:
        attack = attacks[0]
        stats["Damage"] = attack.get("damage", "")
        tags = ", ".join(str(t) for t in attack.get("tags", []) if t)
        stats["Attack"] = f"{attack.get('name', '')} ({tags})" if tags else attack.get("name", "")
    return stats


def monsters():
    return [
        entity(
            "Creature",
            m["name"],
            m.get("description", ""),
            {
                "creatureTable": {
                    "Monster": monster_stats(m),
                    "Notes": {"Moves": "\n".join(f"- {x}" for x in m.get("moves", []) if x), "Description": m.get("description", "")},
                }
            },
        )
        for m in data["monsters"].values()
        if "name" in m
    ]


library = {
    "name": "Dungeon World",
    "description": "Moves, classes, equipment and monsters from Dungeon World by Sage LaTorra and Adam Koebel, licensed under the Creative Commons Attribution 3.0 Unported licence (https://creativecommons.org/licenses/by/3.0/). Converted from the Dungeon World Data project (https://github.com/Vindexus/DungeonWorldData). Monsters that data gives no HP, armor or attack for keep the sheet defaults.",
    "url": URL,
    "gamemaster": "",
    "entities": moves() + equipment() + classes() + monsters(),
}

json.dump(library, open(OUT, "w"), ensure_ascii=False, indent=1)
print(len(library["entities"]), "entities")
