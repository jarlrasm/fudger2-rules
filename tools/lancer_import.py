"""Builds the Lancer library from lancer-data.

lancer-data (https://github.com/massif-press/lancer-data) is Massif Press's
JSON data for the LANCER Core Book, the data COMP/CON uses, published under
the GPL-3.0-or-later licence. This takes the mech weapons, systems, weapon
mods and frames.

    python3 tools/lancer_import.py <lancer-data/lib> systems/lancer/lancer.json
"""

import html
import json
import re
import sys
from pathlib import Path

RAW = Path(sys.argv[1])
OUT = sys.argv[2]
SYSTEM = "Lancer"
URL = "/systems/lancer/lancer.json"
MOUNTS = {"Auxiliary": "Aux", "Main": "Main", "Heavy": "Heavy", "Superheavy": "Superheavy"}
TYPES = {"Melee", "CQB", "Rifle", "Launcher", "Cannon", "Nexus"}
SIZES = {0.5: "1/2", 1: "1", 2: "2", 3: "3"}


def load(name):
    return json.load(open(RAW / f"{name}.json", encoding="utf-8"))


TAGS = {tag["id"]: tag["name"] for tag in load("tags")}


def text(fragment):
    fragment = re.sub(r"<br\s*/?>|</p>|</li>", "\n\n", fragment or "")
    fragment = re.sub(r"<li>", "- ", fragment)
    fragment = re.sub(r"<(b|strong)>(.*?)</\1>", r"**\2**", fragment, flags=re.S)
    fragment = re.sub(r"<(i|em)>(.*?)</\1>", r"*\2*", fragment, flags=re.S)
    fragment = html.unescape(re.sub(r"<[^>]+>", "", fragment))
    return re.sub(r"\n{3,}", "\n\n", fragment).strip()


def tags(values):
    names = []
    for tag in values or []:
        name = TAGS.get(tag["id"], tag["id"])
        names.append(name.replace("{VAL}", str(tag.get("val", ""))).strip())
    return ", ".join(names)


def license_of(item):
    if item.get("source") == "GMS" or not item.get("license_level"):
        return "GMS"
    return f"{item.get('license', item.get('source', ''))} {item['license_level']}"


def actions(item):
    """Actions, deployables and bonuses that a weapon or system grants, as text."""
    parts = []
    for action in item.get("actions", []):
        if not isinstance(action, dict):
            continue
        head = f"**{action.get('name', '')}** ({action.get('activation', '')})".replace(" ()", "")
        parts.append(f"{head}: {text(action.get('detail', ''))}")
    for deployable in item.get("deployables", []):
        if text(deployable.get("detail", "")) == text(item.get("effect", "")):
            continue
        parts.append(f"**{deployable.get('name', '')}** ({deployable.get('type', 'Deployable')}): {text(deployable.get('detail', ''))}")
    return parts


def entity(type_, name, description, implementation):
    return {
        "type": type_,
        "name": name,
        "description": description.strip(),
        "images": {},
        "rulesets": [{"system": SYSTEM, "implementation": implementation}],
    }


def damage(values):
    return " + ".join(f"{d['val']} {d['type']}" for d in values or [])


def ranges(values):
    return ", ".join(f"{r['type']} {r['val']}" for r in values or [])


def weapons():
    result = []
    for weapon in load("weapons"):
        if weapon.get("mount") not in MOUNTS or weapon["id"].startswith("missing"):
            continue
        profiles = weapon.get("profiles") or [weapon]
        first = profiles[0]
        parts = [text(weapon.get("effect", "")), *actions(weapon)]
        if len(profiles) > 1:
            for profile in profiles:
                line = f"**{profile['name']}:** {ranges(profile.get('range'))}; {damage(profile.get('damage'))}"
                if profile.get("tags"):
                    line += f"; {tags(profile['tags'])}"
                if profile.get("effect"):
                    line += f". {text(profile['effect'])}"
                parts.append(line)
                parts += actions(profile)
        if weapon.get("on_hit"):
            parts.append(f"**On hit:** {text(weapon['on_hit'] if isinstance(weapon['on_hit'], str) else weapon['on_hit'].get('detail', ''))}")
        parts.append(f"*{text(weapon.get('description', ''))}*" if weapon.get("description") else "")
        result.append(
            entity(
                "Mech Weapons",
                weapon["name"].title() if weapon["name"].isupper() else weapon["name"],
                "\n\n".join(p for p in parts if p),
                {
                    "mechWeaponStats": {
                        "Stats": {
                            "Mount": MOUNTS[weapon["mount"]],
                            "Type": weapon.get("type") if weapon.get("type") in TYPES else "",
                            "Range": ranges(first.get("range")),
                            "Damage": damage(first.get("damage")),
                            "Tags": tags(first.get("tags") or weapon.get("tags")),
                            "License": license_of(weapon),
                        }
                    }
                },
            )
        )
    return result


def systems():
    result = []
    for system in load("systems") + [dict(m, mod=True) for m in load("mods")]:
        if system["id"].startswith("missing"):
            continue
        parts = [text(system.get("effect", "")), *actions(system)]
        if system.get("mod"):
            parts.insert(0, f"*Weapon mod for {', '.join(system.get('allowed_types') or system.get('allowed_sizes') or ['any weapon'])}.*")
        parts.append(f"*{text(system.get('description', ''))}*" if system.get("description") else "")
        result.append(
            entity(
                "Mech Systems",
                system["name"].title() if system["name"].isupper() else system["name"],
                "\n\n".join(p for p in parts if p),
                {"mechSystemStats": {"Stats": {"SP": str(system.get("sp", "")), "Tags": tags(system.get("tags")), "License": license_of(system)}}},
            )
        )
    return result


def frames():
    result = []
    for frame in load("frames"):
        if frame["id"].startswith("missing"):
            continue
        stats = frame["stats"]
        traits = "\n\n".join(f"**{t['name']}:** {text(t.get('description', ''))}" for t in frame.get("traits", []))
        core = frame.get("core_system", {})
        core_text = "\n\n".join(
            p
            for p in [
                f"**Core system: {core.get('name', '')}**",
                text(core.get("passive_effect", "")),
                f"**{core.get('active_name', '')}** ({core.get('activation', '')}): {text(core.get('active_effect', ''))}" if core.get("active_name") else "",
            ]
            if p
        )
        name = f"{frame['source']} {frame['name'].title() if frame['name'].isupper() else frame['name']}"
        description = "\n\n".join(
            p
            for p in [
                f"*{', '.join(frame.get('mechtype', []))}. Mounts: {', '.join(frame.get('mounts', []))}. License: {license_of(frame)}.*",
                text(frame.get("description", "")),
                core_text,
            ]
            if p
        )
        result.append(
            entity(
                "Mechs",
                name,
                description,
                {
                    "mechTable": {
                        "Mech": {"Frame": name, "Size": SIZES.get(stats["size"], "1")},
                        "Frame": {
                            "Frame HP": stats["hp"],
                            "Frame Evasion": stats["evasion"],
                            "Frame E Defense": stats["edef"],
                            "Frame Heat": stats["heatcap"],
                            "Frame Speed": stats["speed"],
                            "Frame Repair": stats["repcap"],
                            "Frame Sensors": stats["sensor_range"],
                            "Frame Tech Attack": stats["tech_attack"],
                            "Frame Save": stats["save"],
                            "System Points": stats["sp"],
                            "Armor": stats["armor"],
                            "Traits": traits,
                        },
                        "Combat": {"Size": SIZES.get(stats["size"], "1")},
                    }
                },
            )
        )
    return result


library = {
    "name": "LANCER Core",
    "description": "Mech frames, weapons, systems and weapon mods from the LANCER Core Book, converted from Massif Press's lancer-data (https://github.com/massif-press/lancer-data), published under the GPL-3.0-or-later licence. LANCER is copyright Massif Press. This is not an official LANCER product; it is published via the LANCER Third Party License.",
    "url": URL,
    "gamemaster": "",
    "entities": frames() + weapons() + systems(),
}

json.dump(library, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(library["entities"]), "entities:", {t: sum(1 for e in library["entities"] if e["type"] == t) for t in ["Mechs", "Mech Weapons", "Mech Systems"]})
