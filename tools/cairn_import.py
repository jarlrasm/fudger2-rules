"""Builds the Cairn 2nd edition library from the game's open text.

Yochai Gal publishes the text of Cairn under the Creative Commons
Attribution-ShareAlike 4.0 International license, as Markdown at
https://github.com/yochaigal/cairn. This reads the second edition's
marketplace, spellbooks, reliquary and bestiary and writes items, spellbooks,
relics and monsters.

    python3 -I tools/cairn_import.py <checkout>/second-edition systems/cairn/cairn.json
"""

import json
import re
import sys
from pathlib import Path

SOURCE = Path(sys.argv[1])
OUT = sys.argv[2]
SYSTEM = "Cairn"
COMMIT = "4180f390d62c3f1d0faab17762381f3b5dba3261"


def text(path):
    return (SOURCE / path).read_text(encoding="utf-8")


def clean(value):
    value = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"\*\*([^*]*)\*\*", r"\1", value)
    value = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"\1", value)
    return re.sub(r"\s+", " ", value).strip()


def entity(kind, name, description, ruleset, stats):
    return {
        "type": kind,
        "name": name,
        "description": description,
        "images": {},
        "rulesets": [{"system": SYSTEM, "implementation": {ruleset: stats}}],
    }


def table_rows(markdown):
    for line in markdown.splitlines():
        if line.startswith("|") and not re.match(r"^\|\s*:?-", line):
            yield [cell.strip() for cell in line.strip().strip("|").split("|")]


def sections(markdown, level):
    current = None
    for line in markdown.splitlines():
        if line.startswith("#" * level + " ") and not line.startswith("#" * (level + 1)):
            if current:
                yield current
            current = (line[level + 1:].strip(), [])
        elif current:
            current[1].append(line)
    if current:
        yield current


ITEM_KINDS = {"Armor": "Armor", "Weapons": "Weapon", "Transport": "Transport", "Upkeep & Recovery": "Service",
              "Hirelings (per day)": "Hireling", "Gear": "Gear"}


def items():
    found = []
    for title, lines in sections(text("players-guide/marketplace.md"), 2):
        kind = ITEM_KINDS.get(title)
        if not kind:
            continue
        for row in table_rows("\n".join(lines)):
            if len(row) < 2 or row[0].startswith("**"):
                continue
            label, cost = clean(row[0]), clean(row[1])
            notes = re.search(r"\(([^)]*)\)", label)
            name = re.sub(r"\s*\([^)]*\)", "", label).strip()
            details = notes.group(1) if notes else ""
            stats = {"Kind": kind, "Cost": cost}
            damage = re.search(r"(d\d+) damage", details)
            if damage:
                stats["Damage"] = damage.group(1)
            armor = re.search(r"(\+?\d) Armor", details)
            if armor:
                stats["Armor"] = armor.group(1)
            uses = re.search(r"(\d+) uses", details)
            if uses:
                stats["Uses"] = uses.group(1)
            if "bulky" in details or "bulky" in label:
                stats["Bulky"] = True
            if "petty" in details or "petty" in label:
                stats["Petty"] = True
            if kind == "Weapon":
                for weapon in [w.strip() for w in name.split(",") if w.strip() and w.strip() != "etc."]:
                    found.append(entity("Items", weapon, label, "cairnItem", {"Stats": dict(stats)}))
            else:
                found.append(entity("Items", name, label if details else "", "cairnItem", {"Stats": stats}))
    return found


def spellbooks():
    found = []
    for row in table_rows(text("wardens-guide/spellbooks.md")):
        if len(row) < 3 or not re.match(r"^\*\*\d+\*\*$", row[0]):
            continue
        name = clean(row[1])
        body = row[2]
        quirk = re.search(r"_([^_]+)_\s*\.?\s*$", body)
        effect = clean(body[:quirk.start()] if quirk else body)
        found.append(entity("Spellbooks", name, effect, "cairnSpell", {"Stats": {"Book quirk": clean(quirk.group(1)) if quirk else ""}}))
    return found


def relics():
    found = []
    for title, lines in sections(text("wardens-guide/reliquary.md"), 2):
        parts = [p.strip() for p in title.split(",")]
        name = clean(parts[0])
        extra = [clean(p) for p in parts[1:]]
        die = re.search(r"\s*\((d\d+)\)$", name)
        if die:
            name = name[:die.start()]
            extra.insert(0, die.group(1) + " damage")
        charges = ", ".join(e for e in extra if "charge" in e or "use" in e)
        others = [e for e in extra if e not in charges.split(", ")]
        bullets = [clean(re.sub(r"^\s*-\s*", "", l)) for l in lines if l.strip().startswith("-")]
        recharge = [b[len("Recharge:"):].strip() for b in bullets if b.startswith("Recharge:")]
        body = [b for b in bullets if not b.startswith("Recharge:")]
        if others:
            body.insert(0, ", ".join(others) + ".")
        found.append(entity("Relics", name, "\n\n".join(body), "cairnRelic", {"Stats": {"Charges": charges, "Recharge": " ".join(recharge)}}))
    return found


STAT_LINE = re.compile(r"^(\d+) HP(?:, (\d+) Armor)?, (\d+) STR, (\d+) DEX, (\d+) WIL(?:, (.*))?$")


def monsters():
    markdown = text("wardens-guide/bestiary.md")
    groups = {}
    for row in table_rows(markdown):
        if len(row) >= 3 and re.match(r"^\*\*\d+\*\*$", row[0]):
            for monster in row[2].split(","):
                groups.setdefault(monster.strip(), clean(row[1]))
    found = []
    for name, lines in sections(markdown, 2):
        stat = next((STAT_LINE.match(l.strip()) for l in lines if STAT_LINE.match(l.strip())), None)
        if not stat:
            continue
        hp, armor, strength, dex, wil, attacks = stat.groups()
        attacks = clean(attacks or "")
        die = re.search(r"\((?:[^()]*?)(d\d+)", attacks)
        bullets = [clean(re.sub(r"^\s*-\s*", "", l)) for l in lines if l.strip().startswith("-")]
        found.append(entity("Creature", clean(name), " ".join(bullets[:1]), "creatureTable", {
            "Stats": {"HP": int(hp), "Armor": int(armor or 0), "Group": groups.get(clean(name), ""), "STR": int(strength), "DEX": int(dex), "WIL": int(wil)},
            "Attack": {"Attacks": attacks, "Damage": die.group(1) if die else "d4"},
            "Notes": {"Traits": "\n".join("- " + b for b in bullets)},
        }))
    return found


library = {
    "name": "Cairn",
    "description": "Items, spellbooks, relics and the bestiary of Cairn 2nd edition by Yochai Gal, licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/). Converted from https://github.com/yochaigal/cairn (commit " + COMMIT[:7] + ") and shared under the same licence.",
    "url": "/systems/cairn/cairn.json",
    "gamemaster": "",
    "entities": items() + spellbooks() + relics() + monsters(),
}

Path(OUT).write_text(json.dumps(library, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
counts = {}
for e in library["entities"]:
    counts[e["type"]] = counts.get(e["type"], 0) + 1
print(counts)
