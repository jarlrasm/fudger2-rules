import json
import re
import sys
from collections import Counter
from pathlib import Path

RAW = Path(sys.argv[1])
OUT = sys.argv[2]
# The content.en folder of https://github.com/daegalus/csrd, for cyphers,
# artifacts, equipment and creatures.
CSRD = Path(sys.argv[3])
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


HINT = re.compile(r"\{\{< hint (\w+) >\}\} \{\{< columns2 >\}\} (.+?) \{\{< /columns2 >\}\}")
FIELD = re.compile(r"^\*\*([^*:]+):\*\*:?\s*(.*)$")


def clean(text):
    text = re.sub(r"\{\{<[^>]*>\}\}", "", text)
    text = re.sub(r"(?<=\w)---(?=\w)", "—", text.replace("\\*", "*"))
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def blocks(path):
    """Each heading or stat-block banner in a file, with the lines under it."""
    result, current = [], None
    for line in path.read_text(encoding="utf-8").replace("\r", "").split("\n"):
        hint = HINT.search(line)
        heading = re.match(r"^(#{1,4})\s+(.+?)\s*$", line) or re.match(r"^()\*\*([A-Z][A-Z0-9 ,()/'’-]+)\*\*\s*$", line)
        if hint or heading or line.strip() == "-----":
            if current:
                result.append(current)
            current = None
            if hint:
                current = {"kind": hint.group(1), "parts": [p.strip() for p in hint.group(2).split("<--->")], "lines": []}
            elif heading:
                current = {"kind": "heading", "depth": len(heading.group(1)), "parts": [heading.group(2)], "lines": []}
        elif current:
            current["lines"].append(line)
    if current:
        result.append(current)
    return result


def fields(lines):
    """The **Field:** paragraphs of a block, and the text that is not one."""
    found, rest, key = {}, [], None
    for line in lines:
        match = FIELD.match(line.strip())
        if match:
            key = match.group(1).strip()
            found[key] = match.group(2).strip()
        elif key and line.strip() and not line.startswith("|"):
            found[key] += "\n\n" + line.strip()
        elif not key:
            rest.append(line)
        elif line.startswith("|"):
            found[key] += "\n" + line
    return {k: clean(v) for k, v in found.items()}, clean("\n".join(rest))


def number(text):
    found = re.search(r"\d+", text or "")
    return int(found.group()) if found else 0


def title(name):
    return name[0].upper() + name[1:] if name else name


def proper(name, listed):
    """A heading's name, cased as the d100 tables list it. Some headings are
    in capitals, and some lost their first letter to a drop cap."""
    for known in listed:
        if known.lower() == name.lower():
            return title(known)
    for known in listed:
        if known.lower()[1:] == name.lower():
            return title(known)
    return title(name.title() if name.isupper() else name)


def table_names(text, heading):
    """The names in the d100 table under a heading of the cyphers chapter."""
    part = text.split(heading, 1)[1].split("\n## ", 1)[0]
    return {re.sub(r"\s+", " ", row[1]).strip().lower() for row in re.findall(r"^\|\s*([\d–-]+)\s*\|\s*(.+?)\s*\|", part, re.M)}


def cyphers():
    text = (CSRD / "05-game-mastering" / "03-cyphers.md").read_text(encoding="utf-8")
    subtle, fantastic = table_names(text, "## Subtle Cypher Table"), table_names(text, "## Fantastic Cypher Table")
    paths = [CSRD / "05-game-mastering" / "03-cyphers.md"] + sorted((CSRD / "04-genres").glob("*.md"))
    listed = set()
    for path in paths:
        listed |= {re.sub(r"\s+", " ", n).strip() for n in re.findall(r"^\|\s*[\d–-]+\s*\|\s*([^|(]+?)\s*[|(]", path.read_text(encoding="utf-8"), re.M)}
    result, seen = [], set()
    for path in paths:
        for block in blocks(path):
            found, rest = fields(block["lines"])
            if block["kind"] != "heading" or "Level" not in found or "Effect" not in found or "Depletion" in found:
                continue
            name = proper(block["parts"][0], listed)
            if name.lower() in seen or name.endswith("Cyphers"):
                continue
            seen.add(name.lower())
            kind = "Subtle" if name.lower() in subtle else "Fantastic" if name.lower() in fantastic else "Manifest"
            description = "\n\n".join(x for x in [rest, found["Effect"]] + [f"**{k}:** {v}" for k, v in found.items() if k not in ("Level", "Effect", "Form")] if x)
            result.append(entity("Cyphers", name, description, {"cypherStats": {"Stats": {"Level": found["Level"], "Form": found.get("Form", ""), "Kind": kind}}}))
    return result


def item(name, description, kind, damage="", armor="", range_="", price=""):
    return entity("Equipment", name, description, {"equipmentStats": {"Stats": {"Kind": kind, "Damage": damage, "Armor": armor, "Range": range_, "Price": price}}})


def equipment():
    path = CSRD / "02-creating-your-character" / "06-equipment.md"
    text = path.read_text(encoding="utf-8")
    descriptions = {}
    for name, body in re.findall(r"^\*\*([^*]+?):\*\*\s*(.+)$", text, re.M):
        descriptions[name.strip().lower()] = body.strip()
    result, seen, kind, group = [], set(), "Gear", ""

    def describe(name):
        plain = re.sub(r"\s*\(.*?\)", "", name).strip().lower()
        return descriptions.get(plain) or descriptions.get(plain.split(",")[0]) or ""

    for line in text.split("\n"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.startswith("|") else []
        if not cells or set(cells[0]) <= set("- "):
            continue
        header = cells[0].lower()
        if re.match(r"(light|medium|heavy) (weapons|armor)", header):
            kind = " ".join(header.split()[:2]).replace("weapons", "weapon").capitalize()
            continue
        if header in ("item", "armor", "weapon"):
            kind = "Gear" if header == "item" else ""
            continue
        if not kind or len(cells) < 2:
            continue
        name = cells[0].replace("\\*", "").strip()
        if kind == "Gear" and not cells[1]:
            group = re.sub(r"\s*\(.*?\)", "", name)
            continue
        if name in ("Good", "Common", "Poor"):
            name = f"{group}, {name.lower()}"
        if name.lower() in seen:
            continue
        seen.add(name.lower())
        if kind.endswith("weapon"):
            damage = {"Light": "2", "Medium": "4", "Heavy": "6"}[kind.split()[0]]
            notes = cells[2] if len(cells) > 2 else ""
            range_ = re.search(r"(immediate|short|long) range", notes.lower())
            description = "\n\n".join(x for x in [describe(name), notes] if x)
            result.append(item(name, description, kind, damage=damage, range_=range_.group(1).capitalize() if range_ else "", price=cells[1].replace("–", "")))
        elif kind.endswith("armor"):
            result.append(item(name, describe(name), kind if name != "Shield" else "Gear", armor=cells[1].replace("\\*", "*"), price=cells[-1]))
        else:
            result.append(item(name, describe(name), "Gear", price=cells[1]))
    for block in blocks(CSRD / "04-genres" / "03-scifi.md"):
        if block["kind"] != "debug" or len(block["parts"]) < 3:
            continue
        name = title(block["parts"][0])
        if name.lower() in seen:
            continue
        seen.add(name.lower())
        result.append(item(name, f"*{title(block['parts'][1])}.*\n\n" + clean("\n".join(block["lines"])), "Gear", price=block["parts"][2]))
    return result + artifacts(seen)


def artifacts(seen):
    paths = sorted((CSRD / "04-genres").glob("*.md")) + sorted((CSRD / "05-game-mastering").glob("*.md"))
    result = []
    for path in paths:
        for block in blocks(path):
            found, rest = fields(block["lines"])
            if block["kind"] != "heading" or "Depletion" not in found or "Effect" not in found:
                continue
            name = title(block["parts"][0].title() if block["parts"][0].isupper() else block["parts"][0])
            if name.lower() in seen:
                continue
            seen.add(name.lower())
            lines = [f"**Level:** {found.get('Level', '')}", f"**Form:** {found['Form']}" if "Form" in found else "", rest, found["Effect"]]
            lines += [f"**{k}:** {v}" for k, v in found.items() if k not in ("Level", "Form", "Effect")]
            result.append(item(name, "\n\n".join(x for x in lines if x), "Artifact"))
    return result


NOTES = {"Modifications": "Modifications", "Combat": "Combat", "Interaction": "Interaction", "Use": "Use", "Loot": "Loot", "GM intrusion": "GM Intrusion", "GM intrusions": "GM Intrusion", "GM Intrusion": "GM Intrusion"}


def creatures():
    paths = [CSRD / "05-game-mastering" / "01-creatures.md", CSRD / "05-game-mastering" / "02-npcs.md"] + sorted((CSRD / "04-genres").glob("*.md"))
    result, seen = [], set()
    for path in paths:
        for block in blocks(path):
            if block["kind"] != "danger" or len(block["parts"]) < 2 or block["parts"][0] == "Level":
                continue
            found, rest = fields(block["lines"])
            if "Health" not in found:
                continue
            name = block["parts"][0]
            if name.lower() in seen:
                continue
            seen.add(name.lower())
            notes = {}
            for key, target in NOTES.items():
                if key in found:
                    notes[target] = found[key]
            extra = [f"**{k}:** {v}" for k, v in found.items() if k not in NOTES and k not in ("Health", "Damage Inflicted", "Armor", "Movement")]
            stats = {
                "Level": number(block["parts"][1]),
                "Health": number(found["Health"]),
                "Damage": number(found.get("Damage Inflicted")),
                "Armor": number(found.get("Armor")),
                "Movement": found.get("Movement", ""),
            }
            result.append(entity("Creature", name, "\n\n".join(x for x in [rest] + extra if x), {"creatureTable": {"Stats": stats, "Notes": notes}}))
    return result


library = {
    "name": "Cypher System Reference Document",
    "description": "Abilities, descriptors, foci, cyphers, artifacts, equipment and creatures from the Cypher System Reference Document. Compatible with the Cypher System. This product is an independent production and is not affiliated with Monte Cook Games, LLC. It is published under the Cypher System Open License, found at http://csol.montecookgames.com. CYPHER SYSTEM and its logo are trademarks of Monte Cook Games, LLC in the U.S.A. and other countries. Converted from https://github.com/Obsidian-TTRPG-Community/Cypher-SRD-Markdown and https://github.com/daegalus/csrd.",
    "url": URL,
    "gamemaster": "",
    "entities": abilities() + options() + cyphers() + equipment() + creatures(),
}

json.dump(library, open(OUT, "w"), ensure_ascii=False, indent=1)
print(len(library["entities"]), "entities:", dict(Counter(e["type"] for e in library["entities"])))
