import json
import re
import sys
from pathlib import Path

RAW = Path(sys.argv[1])
OUT = sys.argv[2]
SYSTEM = "CypherSystem"
URL = "/systems/cypher/cypher.json"
TIERS = {"First": "1", "Second": "2", "Third": "3", "Fourth": "4", "Fifth": "5", "Sixth": "6"}


def entity(type_, name, description, implementation):
    return {
        "type": type_,
        "name": name,
        "description": description.strip(),
        "images": {},
        "rulesets": [{"system": SYSTEM, "implementation": implementation}],
    }


def parts(path):
    text = path.read_text(encoding="utf-8").replace("\r", "")
    front, body = "", text
    if text.startswith("---"):
        _, front, body = text.split("---", 2)
    title = re.search(r"^#\s+(.+)$", body, re.M)
    body = body[title.end():] if title else body
    body = re.sub(r"^\*\*(Cost|Type)\*\*:.*$", "", body, flags=re.M)
    return front, (title.group(1).strip() if title else path.stem.replace("-", " ")), re.sub(r"\n{3,}", "\n\n", body).strip()


def abilities():
    result = []
    for path in sorted((RAW / "Abilities").rglob("*.md")):
        front, name, body = parts(path)
        cost = re.search(r"^cost:\s*(.+)$", front, re.M) or re.search(r"\*\*Points\*\*:\s*(.+)$", body, re.M)
        cost_text = cost.group(1).strip() if cost else ""
        body = re.sub(r"^\*\*Points\*\*:.*$\n?", "", body, flags=re.M).strip()
        pool = next((p for p in ["Might", "Speed", "Intellect"] if p in cost_text), "")
        tier = re.search(r"Cypher/Type/(\w+)/", front)
        enabler = "Enabler" in front
        result.append(
            entity(
                "Abilities",
                name,
                body,
                {
                    "abilityStats": {
                        "Stats": {
                            "Cost": "" if cost_text in ("None", "") else cost_text,
                            "Pool": pool,
                            "Tier": TIERS.get(tier.group(1), "") if tier else "",
                            "Action": not enabler,
                            "Enabler": enabler,
                        }
                    }
                },
            )
        )
    return result


def options():
    result = []
    for folder, kind in [("Descriptors", "Descriptor"), ("Foci", "Focus")]:
        for path in sorted((RAW / folder).rglob("*.md")):
            _, name, body = parts(path)
            result.append(entity("Character Options", name, body, {"typeStats": {"Stats": {"Kind": kind, "Pools": "", "Edges": "", "Benefits": ""}}}))
    return result


library = {
    "name": "Cypher System Reference Document",
    "description": "Abilities, descriptors and foci from the Cypher System Reference Document. Compatible with the Cypher System. This product is an independent production and is not affiliated with Monte Cook Games, LLC. It is published under the Cypher System Open License, found at http://csol.montecookgames.com. CYPHER SYSTEM and its logo are trademarks of Monte Cook Games, LLC in the U.S.A. and other countries. Converted from https://github.com/Obsidian-TTRPG-Community/Cypher-SRD-Markdown.",
    "url": URL,
    "gamemaster": "",
    "entities": abilities() + options(),
}

json.dump(library, open(OUT, "w"), ensure_ascii=False, indent=1)
print(len(library["entities"]), "entities")
