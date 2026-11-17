import json
import re
import sys

RAW = sys.argv[1]
OUT = sys.argv[2]
SYSTEM = "Ironsworn"
URL = "/systems/ironsworn/ironsworn.json"

data = json.load(open(f"{RAW}/datasworn/classic/classic.json"))

RANKS = {1: "Troublesome", 2: "Dangerous", 3: "Formidable", 4: "Extreme", 5: "Epic"}


def plain(text):
    text = re.sub(r"\[([^\]]+)\]\(id:[^)]+\)", r"\1", text or "")
    return text.strip()


def frules_text(text):
    return plain(text).replace('"', "'").replace("\n", " ").replace("#", "")


def entity(type_, name, description, implementation):
    return {
        "type": type_,
        "name": name,
        "description": plain(description),
        "images": {},
        "rulesets": [{"system": SYSTEM, "implementation": implementation}],
    }


def roll_stats(move):
    stats = []
    for condition in (move.get("trigger") or {}).get("conditions") or []:
        for option in condition.get("roll_options") or []:
            name = option.get("stat") or option.get("condition_meter") or ""
            if name and name.capitalize() not in stats:
                stats.append(name.capitalize())
    return ", ".join(stats)


ROLL_TYPES = {"action_roll": "Action roll", "progress_roll": "Progress roll", "special_track": "Progress roll", "no_roll": "No roll"}


def moves():
    result = []
    for category in data["moves"].values():
        for move in category["contents"].values():
            result.append(entity("Moves", move["name"], move.get("text", ""), {
                "moveStats": {"Stats": {
                    "Category": category["name"],
                    "Roll": ROLL_TYPES.get(move.get("roll_type"), "No roll"),
                    "Stats": roll_stats(move),
                }}
            }))
    return result


def asset_text(asset):
    parts = []
    if asset.get("requirement"):
        parts.append(plain(asset["requirement"]))
    for ability in asset.get("abilities", []):
        mark = "[x]" if ability.get("enabled") else "[ ]"
        parts.append(f"- {mark} {plain(ability['text'])}")
    return "\n\n".join(parts)


def asset_health(asset):
    for control in (asset.get("controls") or {}).values():
        if control.get("field_type") == "condition_meter":
            return str(control.get("max", ""))
    return ""


def assets():
    result = []
    for category in data["assets"].values():
        for asset in category["contents"].values():
            result.append(entity("Assets", asset["name"], asset_text(asset), {
                "assetStats": {"Stats": {
                    "Category": asset.get("category", category["name"]),
                    "Health": asset_health(asset),
                }}
            }))
    return result


def foes():
    result = []
    for category in data["npcs"].values():
        for npc in category["contents"].values():
            result.append(entity("Creature", npc["name"], npc.get("description", ""), {
                "creatureTable": {
                    "Foe": {"Rank": RANKS.get(npc.get("rank"), "Dangerous"), "Nature": npc.get("nature", "")},
                    "Notes": {
                        "Features": "\n".join(plain(x) for x in npc.get("features", [])),
                        "Drives": "\n".join(plain(x) for x in npc.get("drives", [])),
                        "Tactics": "\n".join(plain(x) for x in npc.get("tactics", [])),
                        "Quest Starter": plain(npc.get("quest_starter", "")),
                    },
                }
            }))
    return result


ORACLES = [
    ("oracleAction", ["action_and_theme", "action"]),
    ("oracleTheme", ["action_and_theme", "theme"]),
    ("oracleRegion", ["place", "region"]),
    ("oracleLocation", ["place", "location"]),
    ("oracleCoastalLocation", ["place", "coastal_waters_location"]),
    ("oracleLocationDescriptor", ["place", "descriptor"]),
    ("oracleSettlementTrouble", ["settlement", "trouble"]),
    ("oracleSettlementPrefix", ["settlement", "quick_name", "prefix"]),
    ("oracleSettlementSuffix", ["settlement", "quick_name", "suffix"]),
    ("oracleCharacterRole", ["character", "role"]),
    ("oracleCharacterGoal", ["character", "goal"]),
    ("oracleCharacterDescriptor", ["character", "descriptor"]),
    ("oracleIronlanderNameA", ["name", "ironlander", "a"]),
    ("oracleIronlanderNameB", ["name", "ironlander", "b"]),
    ("oracleElfName", ["name", "elf"]),
    ("oracleCombatAction", ["turning_point", "combat_action"]),
    ("oracleMysticBacklash", ["turning_point", "mystic_backlash"]),
    ("oraclePlotTwist", ["turning_point", "major_plot_twist"]),
    ("oraclePayThePrice", ["moves", "pay_the_price"]),
]


def oracle_table(path):
    node = data["oracles"][path[0]]
    for key in path[1:-1]:
        node = node["collections"][key]
    return node["contents"][path[-1]]


def oracle_list(table):
    entries = [""] * 100
    for row in table["rows"]:
        if row.get("min") is None:
            continue
        for roll in range(row["min"], row["max"] + 1):
            entries[roll - 1] = frules_text(row.get("text", ""))
    return entries


def oracles_frules():
    lines = []
    for name, path in ORACLES:
        entries = oracle_list(oracle_table(path))
        lines.append(f"{name} = [" + ", ".join(f'"{e}"' for e in entries) + "]")
        lines.append("")
    return "\n".join(lines)


library = {
    "name": "Ironsworn",
    "description": "Moves, assets and foes from the Ironsworn Rulebook and the Ironsworn Assets Master Set by Shawn Tomkin, licensed under the Creative Commons Attribution 4.0 International licence (https://creativecommons.org/licenses/by/4.0/). Converted from the Datasworn project (https://github.com/rsek/datasworn).",
    "url": URL,
    "gamemaster": "",
    "entities": moves() + assets() + foes(),
}

with open(f"{OUT}/ironsworn.json", "w") as f:
    json.dump(library, f, indent=1, ensure_ascii=False)
    f.write("\n")

with open(f"{OUT}/oracles.frules", "w") as f:
    f.write(oracles_frules())
