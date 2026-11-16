import json
import re
import sys

RAW = sys.argv[1]
OUT = sys.argv[2]
SYSTEM = "Daggerheart"
URL = "/systems/daggerheart/daggerheart.json"


def load(name):
    return json.load(open(f"{RAW}/{name}.json", encoding="utf-8-sig"))


def number(text, fallback=0):
    found = re.search(r"-?\d+", text or "")
    return int(found.group()) if found else fallback


def features(record, key="feature"):
    return "\n\n".join(f"**{f['name']}:** {f['text']}" for f in record.get(key, []) or [])


def entity(type_, name, description, implementation):
    return {
        "type": type_,
        "name": name,
        "description": description.strip(),
        "images": {},
        "rulesets": [{"system": SYSTEM, "implementation": implementation}],
    }


def weapons():
    return [
        entity(
            "Weapons",
            w["name"],
            features(w),
            {
                "weaponStats": {
                    "Stats": {
                        "Tier": number(w["tier"], 1),
                        "Slot": w["primary_or_secondary"],
                        "Trait": w["trait"],
                        "Range": w["range"],
                        "Damage": w["damage"].replace(" phy", "").replace(" mag", ""),
                        "Damage Type": "mag" if w["damage"].endswith("mag") else "phy",
                        "Burden": w["burden"],
                        "Feature": "; ".join(f"{f['name']}: {f['text']}" for f in w.get("feature", []) or []),
                    }
                }
            },
        )
        for w in load("weapons")
    ]


def armor():
    return [
        entity(
            "Armor",
            a["name"],
            features(a),
            {
                "armorStats": {
                    "Stats": {
                        "Tier": number(a["tier"], 1),
                        "Base Thresholds": a["base_thresholds"],
                        "Base Score": a["base_score"],
                        "Feature": "; ".join(f"{f['name']}: {f['text']}" for f in a.get("feature", []) or []),
                    }
                }
            },
        )
        for a in load("armor")
    ]


def domain_cards():
    return [
        entity(
            "Domain Cards",
            c["name"],
            c["text"],
            {
                "domainCardStats": {
                    "Stats": {
                        "Domain": c["domain"],
                        "Level": number(c["level"], 1),
                        "Type": c["type"],
                        "Recall Cost": number(c["recall"]),
                        "In Loadout": True,
                    }
                }
            },
        )
        for c in load("abilities")
    ]


def items():
    return [
        entity(kind_name, i["name"], i["description"], {"itemStats": {"Stats": {"Kind": kind, "Uses": ""}}})
        for source, kind, kind_name in [("items", "Item", "Items"), ("consumables", "Consumable", "Items")]
        for i in load(source)
    ]


def options():
    result = []
    for c in load("classes"):
        text = "\n\n".join(
            [
                c["description"],
                f"**Domains:** {c.get('domain_1', '')} and {c.get('domain_2', '')}. **Starting Evasion:** {c.get('evasion', '')}. **Starting HP:** {c.get('hp', '')}.",
                f"**Hope feature, {c.get('hope_feature_name', '')}:** {c.get('hope_feature_text', '')}",
                features(c),
                f"**Subclasses:** {c.get('subclass_1', '')}, {c.get('subclass_2', '')}. **Suggested traits:** {c.get('suggested_traits', '')}. **Suggested gear:** {c.get('suggested_primary', '')}, {c.get('suggested_secondary', '')}, {c.get('suggested_armor', '')}. **Class items:** {c.get('items', '')}.",
            ]
        )
        result.append(
            entity(
                "Character Options",
                c["name"],
                text,
                {
                    "optionStats": {
                        "Stats": {
                            "Kind": "Class",
                            "Domains": f"{c.get('domain_1', '')}, {c.get('domain_2', '')}",
                            "Starting Evasion": c["evasion"],
                            "Starting HP": c["hp"],
                            "Features": features(c),
                        }
                    }
                },
            )
        )
    for s in load("subclasses"):
        text = "\n\n".join(
            part
            for part in [
                s["description"],
                f"**Spellcast trait:** {s['spellcast_trait']}" if s.get("spellcast_trait") else "",
                "**Foundation**\n\n" + features(s, "foundation"),
                "**Specialization**\n\n" + features(s, "specialization"),
                "**Mastery**\n\n" + features(s, "mastery"),
            ]
            if part
        )
        result.append(entity("Character Options", s["name"], text, {"optionStats": {"Stats": {"Kind": "Subclass", "Domains": "", "Starting Evasion": "", "Starting HP": "", "Features": ""}}}))
    for kind, source in [("Ancestry", "ancestries"), ("Community", "communities")]:
        for a in load(source):
            text = "\n\n".join(part for part in [a["description"], a.get("note", ""), features(a)] if part)
            result.append(entity("Character Options", a["name"], text, {"optionStats": {"Stats": {"Kind": kind, "Domains": "", "Starting Evasion": "", "Starting HP": "", "Features": features(a)}}}))
    return result


def thresholds(text):
    parts = re.findall(r"\d+", text or "")
    return (int(parts[0]), int(parts[1])) if len(parts) >= 2 else (0, 0)


def adversaries():
    result = []
    for a in load("adversaries"):
        major, severe = thresholds(a.get("thresholds"))
        result.append(
            entity(
                "Creature",
                a["name"],
                a.get("description", ""),
                {
                    "creatureTable": {
                        "Stats": {
                            "Tier": number(a.get("tier"), 1),
                            "Type": (a.get("type") or "Standard").split(" ")[0],
                            "Difficulty": number(a.get("difficulty"), 10),
                            "Major Threshold": major,
                            "Severe Threshold": severe,
                            "HP Slots": number(a.get("hp"), 1),
                            "Stress Slots": number(a.get("stress"), 0),
                            "ATK": number(a.get("atk")),
                            "Attack": a.get("attack", ""),
                            "Range": a.get("range", ""),
                            "Damage": a.get("damage", ""),
                            "Motives": a.get("motives_and_tactics", ""),
                        },
                        "Features": {
                            "Features": features(a),
                            "Experiences": a.get("experience", "") or "",
                        },
                    }
                },
            )
        )
    return result


def environments():
    return [
        entity(
            "Environments",
            e["name"],
            e.get("description", ""),
            {
                "environmentStats": {
                    "Stats": {
                        "Tier": number(e.get("tier"), 1),
                        "Type": e.get("type", ""),
                        "Difficulty": number(e.get("difficulty"), 10),
                        "Impulses": e.get("impulses", ""),
                        "Potential Adversaries": e.get("potential_adversaries", ""),
                        "Features": features(e),
                    }
                }
            },
        )
        for e in load("environments")
    ]


library = {
    "name": "Daggerheart SRD",
    "description": "Material from the Daggerheart System Reference Document 1.0, © Critical Role, LLC, under the terms of the Darrington Press Community Gaming License (https://www.daggerheart.com/). Converted from the structured SRD at https://github.com/seansbox/daggerheart-srd. Daggerheart is a trademark of Critical Role, LLC; this library is not affiliated with or endorsed by Critical Role or Darrington Press.",
    "url": URL,
    "gamemaster": "",
    "entities": weapons() + armor() + domain_cards() + items() + options() + adversaries() + environments(),
}

json.dump(library, open(OUT, "w"), ensure_ascii=False, indent=1)
print(len(library["entities"]), "entities")
