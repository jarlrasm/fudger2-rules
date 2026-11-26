"""Builds the Mausritter library from the game's open SRD.

Isaac Williams and Losing Games publish the Mausritter System Reference
Document under Creative Commons Attribution 4.0 International, as Markdown at
https://mausritter.com/srd/mausritter-srd-2.3.1.md. This reads its gear,
weapons, armour, treasure, magic swords, spells and creatures and writes
items, spells and creatures. The five common Conditions are written in our
own words, since the SRD names them without listing their cards.

    python3 -I tools/mausritter_import.py mausritter-srd-2.3.1.md systems/mausritter/mausritter.json
"""

import json
import re
import sys
from pathlib import Path

SOURCE = Path(sys.argv[1]).read_text(encoding="utf-8")
OUT = sys.argv[2]
SYSTEM = "Mausritter"
VERSION = "2.3.1"


def clean(value):
    value = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"\*\*([^*]*)\*\*", r"\1", value)
    value = value.replace("’", "'").replace("—", "-").replace("–", "-")
    return re.sub(r"\s+", " ", value).strip()


def entity(kind, name, description, ruleset, stats):
    return {
        "type": kind,
        "name": name,
        "description": description,
        "images": {},
        "rulesets": [{"system": SYSTEM, "implementation": {ruleset: stats}}],
    }


def section(title, level):
    lines = SOURCE.splitlines()
    marker = "#" * level + " " + title
    start = next(i for i, l in enumerate(lines) if l.strip() == marker)
    out = []
    for line in lines[start + 1:]:
        m = re.match(r"^(#+) ", line)
        if m and len(m.group(1)) <= level:
            break
        out.append(line)
    return "\n".join(out)


def subsections(markdown, level):
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


def table_rows(markdown):
    rows = []
    for line in markdown.splitlines():
        if line.startswith("|") and not re.match(r"^\|\s*:?-", line):
            rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return rows[1:] if rows else []


def item(name, description, kind, slots=1, usage=3, cost="", klass="", damage="", armour="", carried=""):
    stats = {"Kind": kind, "Slots": slots, "Usage": usage}
    if klass:
        stats["Class"] = klass
    if damage:
        stats["Damage"] = damage
    if armour:
        stats["Armour"] = armour
    if carried:
        stats["Carried in"] = carried
    if cost:
        stats["Cost"] = cost
    return {"name": name, "description": description, "stats": stats}


def items():
    found = {}

    def add(entry):
        key = entry["name"].lower()
        if key in found:
            old = found[key]
            old["stats"] = {**entry["stats"], **old["stats"]}
            if entry["stats"].get("Cost") and old["stats"].get("Cost") != entry["stats"]["Cost"]:
                old["stats"]["Cost"] = old["stats"]["Cost"] + " (" + entry["stats"]["Cost"] + " as " + entry["stats"]["Kind"].lower() + ")"
        else:
            found[key] = entry

    weapons = section("Melee weapons", 3) + "\n" + section("Ranged weapons", 3)
    for name, lines in subsections(weapons, 4):
        body = "\n".join(lines)
        damage = re.search(r"\*\*(d\d+(?:/d\d+)?) damage\*\*", body).group(1)
        wield = re.search(r"Wielded in: (.*)", body).group(1).strip()
        special = re.search(r"Special rule: (.*)", body)
        cost = re.search(r"Cost: (\d+p)", body)
        klass = name.strip()
        slots = 2 if wield == "Both paws" else 1
        text = "Wielded in: " + wield + "." + (" " + clean(special.group(1)) if special else "")
        example = re.search(r"Example: (.*)", body)
        names = [n.strip() for n in example.group(1).split(",")] if example else ["Improvised weapon"]
        for n in names:
            add(item(n[0].upper() + n[1:], text, "Weapon", slots, 3, cost.group(1) if cost else "1p", klass, damage, carried=wield))
    for row in table_rows(section("Weapons and armour", 2)):
        m = re.match(r"\*\*(.+?)\*\* \((.+)\)", row[0])
        if m and "weapon" not in m.group(1).lower():
            klass = m.group(1)
            for n in [x.strip() for x in m.group(2).split(",") if x.strip() != "etc."]:
                if klass in ("Light", "Medium", "Heavy", "Light ranged", "Heavy ranged"):
                    damage = {"Light": "d6", "Medium": "d6/d8", "Heavy": "d10", "Light ranged": "d6", "Heavy ranged": "d8"}[klass]
                    wield = {"Light": "Main paw/off paw", "Medium": "Main paw/both paws", "Heavy": "Both paws", "Light ranged": "Main paw", "Heavy ranged": "Both paws"}[klass]
                    add(item(n[0].upper() + n[1:], "Wielded in: " + wield + ".", "Weapon", 2 if wield == "Both paws" else 1, 3, row[1], klass, damage, carried=wield))
    for name, lines in subsections(section("Ammunition", 3), 4):
        body = "\n".join(lines)
        cost = re.search(r"Cost: (\d+p)", body).group(1)
        n = clean(name.split(",")[0])
        add(item(n, "Carried in a body slot. Mark usage after a fight in which it was used, on 4-6.", "Ammunition", 1, 3, cost, carried="Body slot"))
    for name, lines in subsections(section("Armour", 2), 3):
        body = "\n".join(lines)
        worn = re.search(r"Worn in: (.*)", body).group(1).strip()
        cost = re.search(r"Cost: (\d+p)", body).group(1)
        add(item(name, "Prevents 1 damage. Worn in: " + worn + ".", "Armour", 2, 3, cost, name, armour="1", carried=worn))
    for row in table_rows(section("Tools, mouse made", 2)):
        add(item(clean(row[0]), "Mouse made, available in most mouse settlements.", "Tool", 1, 3, row[1]))
    for row in table_rows(section("Tools, human made", 2)):
        add(item(clean(row[0]), "Human made, available in mouse settlements near human populations.", "Tool", 1, 3, row[1]))
    for row in table_rows(section("Light sources", 2)):
        name = clean(row[0])
        six = "six usage dots" in name
        name = re.sub(r"\s*\(has six usage dots\)", "", name)
        desc = "Provides light. Mark usage every 6 Turns."
        if name.startswith("Lantern"):
            desc += " Refilled with oil."
        if name.startswith("Electric"):
            desc += " Recharged with batteries; six usage dots."
        kind = "Light" if not name.startswith(("Oil", "Batteries")) else "Tool"
        add(item(name, desc if kind == "Light" else "Refill for a lantern.", kind, 1, 6 if six else 3, row[1]))
    for row in table_rows(section("Clothing", 2)):
        name = clean(row[0])
        add(item(name + (" clothes" if name in ("Poor", "Standard", "Noble") else ""), "Clothing.", "Clothing", 1, 3, row[1]))
    wields = {"Light": "Main paw/off paw", "Medium": "Main paw/both paws", "Heavy": "Both paws"}
    for row in table_rows(section("Backgrounds", 2)):
        background = clean(row[2])
        for cell in row[3:5]:
            text = clean(cell)
            if text.startswith(("Spell:", "Hireling:")) or "IOU" in text:
                continue
            m = re.match(r"^(.*?) \((Light|Medium|Heavy), (d\d+(?:/d\d+)?)\)$", text)
            a = re.match(r"^(.*?) \((Light|Heavy) armour\)$", text)
            r = re.match(r"^(.*?) \(as rations\)$", text)
            if m:
                name, klass, damage = m.groups()
                key = name.lower()
                if key in found:
                    found[key]["stats"].update({"Class": klass, "Damage": damage, "Carried in": wields[klass]})
                else:
                    add(item(name, "Wielded in: " + wields[klass] + ".", "Weapon", 2 if klass == "Heavy" else 1, 3, "", klass, damage, carried=wields[klass]))
            elif a:
                name, klass = a.groups()
                add(item(name, klass + " armour: prevents 1 damage.", "Armour", 2, 3, "", klass + " armour", armour="1"))
            elif r:
                add(item(r.group(1), "Eaten as rations.", "Food", 1, 3, ""))
            elif text.lower() not in found:
                add(item(text, "Starting item of the " + background.lower() + " background.", "Tool", 1, 3, ""))
    add(item("Rations", "Food for the road. Mark usage after a meal; eating one and resting a Watch heals all HP.", "Food", 1, 3, "5p"))
    add(item("Pip purse", "Holds 250 pips. Pips past the first 250 take a slot per 250.", "Tool", 1, 0, ""))
    treasure = section("Treasure tables", 3)
    for block in re.split(r"\n(?=\| d6)", treasure):
        header = block.strip().splitlines()[0] if block.strip() else ""
        m = re.match(r"\|\s*d6\s*\|\s*(.+?)\s*\|", header)
        if not m:
            continue
        group = m.group(1)
        for row in table_rows(block):
            text = clean(row[1])
            tm = re.match(r"^(.*?) \((.*)\)$", text)
            if group in ("Valuable treasure", "Large treasure") and tm:
                name, detail = tm.groups()
                slots = re.search(r"(\d+) slots", detail)
                cost = re.search(r"(\d+p)", detail)
                add(item(name, group + ".", "Treasure", int(slots.group(1)) if slots else 1, 3, cost.group(1) if cost else ""))
            elif group == "Trinkets" and tm:
                name, detail = tm.groups()
                if "make up" not in detail:
                    add(item(name, detail[0].upper() + detail[1:] + ".", "Treasure", 1, 3, ""))
            elif group == "Unusual treasure":
                um = re.match(r"^(.*?) \((.*)\)$", text)
                if um:
                    add(item(um.group(1), "Unusual treasure: " + um.group(2) + ".", "Treasure", 1, 3, ""))
    swords = section("Magic swords", 2)
    rule = "Magic swords only mark usage when a 6 is rolled. Roll its class: d6, 1-4 Medium, 5 Light, 6 Heavy. 1-in-6 is cursed."
    for row in table_rows("| d10" + swords.split("| d10")[1].split("### Cursed")[0]):
        name = clean(row[1])
        add(item("Magic sword (" + name[0].lower() + name[1:] + ")" if not name.startswith("Intricate Fae") else "Magic sword (intricate Fae design)", clean(row[2]) + ". " + rule, "Magic sword", 1, 3, "", "Medium", "d6/d8", carried="Main paw/both paws"))
    return [entity("Items", e["name"], e["description"], "mrItem", {"Stats": e["stats"]}) for e in found.values()]


def spells():
    found = []
    for row in table_rows(section("List of spells", 2)):
        found.append(entity("Spells", clean(row[1]), clean(row[2]), "mrSpell", {"Stats": {"Roll": int(row[0]), "Effect": clean(row[2]), "Recharge": clean(row[3])}}))
    return found


STAT_HEAD = re.compile(r"^(\d+)\s*hp, STR (\d+), DEX (\d+), WIL (\d+)(?:, Armour (\d+))?$")


def attacks(text):
    found = []
    for part in re.split(r",| or ", text):
        part = part.strip()
        m = re.match(r"^d(\d+) ([^(]+?)\s*(?:\((.*)\))?$", part)
        if not m:
            continue
        die, name, note = m.groups()
        target = "STR"
        if note:
            t = re.search(r"damages (STR|DEX|WIL)", note)
            if t:
                target = t.group(1)
        found.append({"Name": name, "Die": int(die), "Damages": target, "Ranged": name in ("bow", "sling", "crossbow")})
    return found


def creatures():
    found = []
    for name, lines in subsections(section("List of creatures", 2), 3):
        body = "\n".join(lines)
        block = re.search(r":::statblock\n(.*?)\n:::", body, re.S).group(1)
        stat_lines = [clean(l) for l in block.splitlines() if l.strip()]
        warband = any(l == "Warband scale" for l in stat_lines)
        stat_lines = [l for l in stat_lines if l != "Warband scale"]
        head = STAT_HEAD.match(stat_lines[0])
        hp, strength, dex, wil, armour = head.groups()
        attack_line = next((l for l in stat_lines if l.startswith("Attacks:")), "")
        critical = next((l[len("Critical damage:"):].strip() for l in stat_lines if l.startswith("Critical damage:")), "")
        special = [l for l in stat_lines[1:] if not l.startswith(("Attacks:", "Critical damage:"))]
        attack_text = attack_line[len("Attacks:"):].strip()
        non_dice = [p.strip() for p in re.split(r",| or ", attack_text) if p.strip() and not re.match(r"^d\d+", p.strip())]
        wants = re.search(r"\*\*Wants\*\* (.*)", body)
        variants = []
        for title, vlines in subsections(body, 4):
            entries = [clean(re.sub(r"^\d+\.\s*", "", l)) for l in vlines if re.match(r"^\d+\.", l.strip())]
            variants.append(title + ": " + "; ".join(entries) + ".")
        notes = special + ["Also: " + ", ".join(non_dice) + "." if non_dice else ""]
        found.append(entity("Creature", clean(name), "Wants " + clean(wants.group(1)) + "." if wants else "", "creatureTable", {
            "Stats": {"HP": int(hp), "Max HP": int(hp), "Armour": int(armour or 0), "Warband scale": warband, "STR": int(strength), "DEX": int(dex), "WIL": int(wil)},
            "Attacks": attacks(attack_text),
            "Notes": {
                "Critical damage": critical,
                "Special": "\n".join([n for n in notes if n] + variants),
                "Wants": clean(wants.group(1)) if wants else "",
            },
        }))
    return found


CONDITIONS = [
    ("Exhausted", "Worn out by travel without rest, bad weather or hard work. It fills a slot.", "After a long rest."),
    ("Frightened", "Shaken by fear. It fills a slot, and the mouse will not move closer to what frightened it.", "After a short rest."),
    ("Hungry", "A day without food. It fills a slot.", "After a meal."),
    ("Injured", "Hurt by critical damage. It fills a slot; STR and DEX saves are made with disadvantage.", "After a full rest."),
    ("Drained", "Spent by a miscast. It fills a slot; WIL saves are made with disadvantage.", "After a full rest."),
]


def conditions():
    return [entity("Conditions", n, e, "mrCondition", {"Stats": {"Effect": e, "Clear": c}}) for n, e, c in CONDITIONS]


library = {
    "name": "Mausritter",
    "description": "Gear, weapons, armour, treasure, magic swords, spells and creatures from the Mausritter System Reference Document " + VERSION + " by Isaac Williams and Losing Games, licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Converted from https://mausritter.com/srd/. The Condition cards are written by Fudger. This work is based on Mausritter, a product of Losing Games and Isaac Williams.",
    "url": "/systems/mausritter/mausritter.json",
    "gamemaster": "",
    "entities": items() + spells() + creatures() + conditions(),
}

Path(OUT).write_text(json.dumps(library, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
counts = {}
for e in library["entities"]:
    counts[e["type"]] = counts.get(e["type"], 0) + 1
print(counts)
