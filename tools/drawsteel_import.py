"""Builds the Draw Steel monster library from the Steel Compendium.

The Steel Compendium (https://github.com/SteelCompendium/data-bestiary-json)
publishes the stat blocks of the Draw Steel Monsters book as JSON under the
DRAW STEEL Creator License. This was built from commit f8968fe of that repo.

    python3 tools/drawsteel_import.py <data-bestiary-json>/Monsters/statblocks.json systems/drawsteel/drawsteel.json
"""

import json
import re
import sys

RAW = sys.argv[1]
OUT = sys.argv[2]
SYSTEM = "DrawSteel"
URL = "/systems/drawsteel/drawsteel.json"
ORGANIZATIONS = {"Minion", "Horde", "Platoon", "Elite", "Leader", "Solo"}
ROLES = {"Ambusher", "Artillery", "Brute", "Controller", "Defender", "Harrier", "Hexer", "Mount", "Support"}


def number(text, fallback=0):
    found = re.search(r"-?\d+", str(text or ""))
    return int(found.group()) if found else fallback


def effect_text(effect):
    name = effect.get("name")
    cost = f" ({effect['cost']})" if effect.get("cost") else ""
    text = effect.get("effect", "")
    return f"**{name}{cost}:** {text}" if name else text


def ability(feature):
    effects = feature.get("effects", [])
    rolled = next((e for e in effects if e.get("roll")), {})
    head = ", ".join(x for x in [feature.get("ability_type"), feature.get("cost"), ", ".join(feature.get("keywords", []))] if x)
    rest = [effect_text(e) for e in effects if e is not rolled]
    if feature.get("trigger"):
        rest.insert(0, f"**Trigger:** {feature['trigger']}")
    return {
        "Name": feature["name"],
        "Type": feature.get("usage", ""),
        "Distance": feature.get("distance", ""),
        "Target": feature.get("target", ""),
        "Bonus": number(rolled.get("roll"), 0),
        "Tier 1": rolled.get("tier1", ""),
        "Tier 2": rolled.get("tier2", ""),
        "Tier 3": rolled.get("tier3", ""),
        "Effect": "\n\n".join(x for x in ([f"*{head}*"] if head else []) + rest if x),
    }


def monster(m):
    words = (m.get("roles") or ["Platoon"])[0].split()
    organization = next((w for w in words if w in ORGANIZATIONS), "")
    role = next((w for w in words if w in ROLES), "")
    features = m.get("features", [])
    traits = [{"Name": f["name"], "Description": "\n\n".join(effect_text(e) for e in f.get("effects", []))} for f in features if f["feature_type"] == "trait"]
    abilities = [ability(f) for f in features if f["feature_type"] == "ability"]
    lines = [f"*Level {m['level']} {' '.join(words).lower()}, {', '.join(m.get('ancestry', []))}. EV {m['ev']}.*"]
    if m.get("with_captain"):
        lines.append(f"**With captain:** {m['with_captain']}")
    stats = {
        "Level": m["level"],
        "Organization": organization,
        "Keywords": ", ".join(m.get("ancestry", [])),
        "EV": number(m["ev"]),
        "Max Stamina": number(m["stamina"], 1),
        "Stamina": number(m["stamina"], 1),
        "Speed": m.get("speed", 5),
        "Size": m.get("size", "1M"),
        "Stability": m.get("stability", 0),
        "Free strike": m.get("free_strike", 0),
        "Immunity": ", ".join(m.get("immunities") or []),
        "Weakness": ", ".join(m.get("weaknesses") or []),
        "Movement": m.get("movement", "") or "",
    }
    if role:
        stats["Role"] = role
    return {
        "type": "Creature",
        "name": m["name"],
        "description": "\n\n".join(lines),
        "images": {},
        "rulesets": [{
            "system": SYSTEM,
            "implementation": {
                "monsterTable": {
                    "Monster": stats,
                    "Characteristics": {c.capitalize(): m.get(c, 0) for c in ["might", "agility", "reason", "intuition", "presence"]},
                    "Abilities": abilities,
                    "Traits": traits,
                }
            },
        }],
    }


data = json.load(open(RAW, encoding="utf-8"))["monsters"]
seen, entities = set(), []
for m in data:
    if m["name"].lower() not in seen:
        seen.add(m["name"].lower())
        entities.append(monster(m))

library = {
    "name": "Draw Steel monsters",
    "description": "Monster stat blocks from the Draw Steel Monsters book, converted from the Steel Compendium (https://github.com/SteelCompendium/data-bestiary-json). This is an independent product published under the DRAW STEEL Creator License and is not affiliated with MCDM Productions, LLC. DRAW STEEL © 2024 MCDM Productions, LLC.",
    "url": URL,
    "gamemaster": "",
    "entities": entities,
}
json.dump(library, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(entities), "monsters")
