"""Builds the Worlds Without Number library from the game's CC0 SRD.

Kevin Crawford and Sine Nomine Publishing released the Worlds Without Number
System Reference Document v1.0 (13 March 2024) under CC0 1.0 Universal. Its
introduction lists VTTs among the uses it covers. The PDF is sold free on
DriveThruRPG; this reads the Markdown transcription SRD.md from
https://github.com/klrkdekira/wwn-system-json (commit on main, data dedicated
to CC0) and writes weapons, armor, gear, foci, spells, arts, faction assets
and the example creature stat lines.

    python3 -I tools/wwn_import.py SRD.md systems/wwn/wwn.json
"""

import json
import re
import sys
from pathlib import Path

SOURCE = Path(sys.argv[1]).read_text(encoding="utf-8")
OUT = sys.argv[2]
SYSTEM = "WorldsWithoutNumber"
LINES = SOURCE.splitlines()


def clean(value):
    value = value.replace("<br>", " ")
    value = re.sub(r"\*\*([^*]*)\*\*", r"\1", value)
    value = re.sub(r"_([^_]+)_", r"\1", value)
    value = value.replace("’", "'").replace("‘", "'").replace("“", "'").replace("”", "'").replace('"', "'")
    value = value.replace("—", " - ").replace("–", "-").replace("\\#", "#")
    return re.sub(r"\s+", " ", value).strip()


def entity(kind, name, description, ruleset, values):
    return {
        "type": kind,
        "name": name,
        "description": description,
        "images": {},
        "rulesets": [{"system": SYSTEM, "implementation": {ruleset: values}}],
    }


def section(start_pattern):
    start = next(i for i, l in enumerate(LINES) if re.match(start_pattern, l))
    level = len(re.match(r"^(#+)", LINES[start]).group(1))
    out = []
    for line in LINES[start + 1:]:
        m = re.match(r"^(#+) ", line)
        if m and len(m.group(1)) <= level:
            break
        out.append(line)
    return out


def rows(lines):
    found = []
    for line in lines:
        if line.startswith("|") and not re.match(r"^\|\s*:?-", line):
            found.append([clean(c) for c in line.strip()[1:-1].split("|")])
    return found[1:]


TRAITS = {
    "2H": "Two-handed.", "AP": "Armor piercing: ignores non-magical armor and shields for hit rolls.",
    "FX": "Fixed: needs a fixed position and five minutes to set up.",
    "L": "Long: reaches 10 feet.", "LL": "Less lethal: foes brought to 0 HP can be left alive.",
    "N": "Numerous: five count as one Readied item.",
    "PM": "Precisely murderous: an extra -1 on the Execution save, and double damage even if it is saved.",
    "R": "Reload: a Move action to reload, On Turn with Shoot-1.", "S": "Subtle: easily hidden.",
    "SR": "Slow reload: a Main Action to reload.", "SS": "Single shot: ten rounds to reload.",
    "T": "Throwable: thrown to its range, with no Shock when thrown.",
}


def weapons():
    out = []
    for r in rows(section(r"^#### 3\.4\.2")):
        name, dmg, shock, attr, rng, traits, cost, enc = r
        if name.startswith("Unarmed"):
            continue
        codes = [t.strip() for t in traits.split(",") if t.strip()]
        skill = "Stab" if rng == "-" or "T" in codes else "Shoot"
        if name.startswith("Throwing"):
            skill = "Shoot"
        desc = " ".join(TRAITS[c] for c in codes if c in TRAITS)
        out.append(entity("Weapons", name, desc, "wwnWeapon", {"Stats": {
            "Skill": skill, "Damage": dmg, "Shock": shock, "Attribute": attr.upper(),
            "Range": "" if rng == "-" else rng, "Traits": traits, "Cost": cost, "Enc": enc}}))
    return out


def armor():
    out = []
    category = "Light"
    notes = {
        "Light": "Light armor.",
        "Medium": "Medium armor: its encumbrance is a penalty on physical Sneak checks.",
        "Heavy": "Heavy armor: its encumbrance is a penalty on Sneak and Exert checks.",
        "Shield": "Shield: base AC as listed, or +1 AC over equal or better armor. Ignores the first Shock each round.",
    }
    for r in rows(section(r"^##### Armor$")):
        name = r[0]
        if name.endswith("Armors") or name == "Shields":
            category = "Shield" if name == "Shields" else name.split()[0]
            continue
        if name == "No Armor":
            continue
        desc = notes[category]
        if name == "Grand Plate":
            desc += " Immune to non-magical melee and thrown weapons unless two-handed, Shock AC 16 or more, or while grappled."
        if name == "War Shirt":
            desc += " Charms and tokens of war-luck; it still hinders spellcasting."
        out.append(entity("Armor", name, desc, "wwnArmor", {"Stats": {
            "Category": category, "AC": int(r[1]), "Cost": r[2], "Enc": r[3]}}))
    return out


def gear():
    out = []
    for name, cost, enc in rows(section(r"^#### Adventuring Gear")):
        notes = []
        if "*" in enc:
            notes.append("Effectively weightless in modest numbers.")
        if "§" in enc:
            notes.append("Doesn't count for encumbrance while worn.")
        if "#" in enc:
            notes.append("Can be bundled in threes for the same encumbrance.")
        value = re.sub(r"[*§#\\]", "", enc).strip()
        out.append(entity("Gear", name, " ".join(notes), "wwnGear", {"Stats": {"Cost": cost, "Enc": value or "0"}}))
    return out


def foci():
    out = []
    current = None
    body = []

    def flush():
        if not current:
            return
        text = clean(" ".join(body))
        parts = re.split(r"Level (\d): ", text)
        intro = parts[0].strip()
        levels = {parts[i]: parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}
        stats = {"Level 1": levels.get("1", ""), "Level 2": levels.get("2", "")}
        out.append(entity("Foci", current, intro, "wwnFocus", {"Stats": stats}))

    for line in section(r"^#### 1\.6\.1"):
        if line.startswith("##### "):
            flush()
            current = clean(line[6:])
            body = []
        elif current:
            body.append(line)
    flush()
    return out


def spells():
    out = []
    for pattern, tradition in [(r"^### 4\.4\.0", "High Magic"), (r"^### 4\.5\.0", "Elementalist"), (r"^### 4\.6\.0", "Necromancer")]:
        current = None
        body = []
        for line in section(pattern) + ["#### End (Level 0)"]:
            m = re.match(r"^#### (.+) \(Level (\d)\)", line)
            if m:
                if current:
                    out.append(entity("Spells", current[0], clean(" ".join(body)), "wwnSpell", {"Stats": {"Level": current[1], "Tradition": tradition}}))
                current = (clean(m.group(1)), int(m.group(2)))
                body = []
            elif current:
                body.append(line)
    return out


ART = re.compile(r"^([A-Z][A-Za-z'’ -]{2,40}): (.+)$")


def arts():
    out = []
    seen = set()
    for i, line in enumerate(LINES):
        m = re.match(r"^##### 1\.5\.\d+\.1 (.+) Arts$", line)
        if not m:
            continue
        tradition = m.group(1)
        for art in LINES[i + 1:]:
            if art.startswith("#### "):
                break
            a = ART.match(art.strip())
            if not a or a.group(1).startswith(("Level", "Partial", "Full", "Note")):
                continue
            name = clean(a.group(1))
            if (tradition, name) in seen:
                continue
            seen.add((tradition, name))
            out.append(entity("Arts", name, clean(a.group(2)), "wwnArt", {"Stats": {"Tradition": tradition}}))
    return out


def assets():
    texts = {}
    for pattern in [r"^### 6\.8\.0", r"^### 6\.9\.0", r"^### 6\.10\.0"]:
        for line in section(pattern):
            a = ART.match(line.strip())
            if a:
                texts[clean(a.group(1)).lower()] = clean(a.group(2))
    out = []
    for pattern in [r"^### 6\.8\.0", r"^### 6\.9\.0", r"^### 6\.10\.0"]:
        rating = 0
        kind = ""
        for r in rows(section(pattern)):
            m = re.match(r"^(Cunning|Force|Wealth) (\d)$", r[0])
            if m:
                kind, rating = m.group(1), int(m.group(2))
                continue
            if len(r) != 7:
                print("skipped asset row", r, file=sys.stderr)
                continue
            name, cost, hp, magic, attack, counter, qualities = r
            out.append(entity("Assets", name, texts.get(name.lower(), ""), "wwnAsset", {"Stats": {
                "Attribute": kind, "Rating": rating, "Cost": int(cost), "HP": int(hp), "Magic": magic,
                "Attack": attack, "Counter": counter, "Qualities": qualities}}))
    return out


def creatures():
    out = []
    group = ""
    for line in section(r"^### 5\.1\.0"):
        h = re.match(r"^#### (.+)", line)
        if h:
            group = clean(h.group(1))
            continue
        if not line.startswith("|") or line.startswith("| Type") or line.startswith("|---"):
            continue
        r = [clean(c) for c in line.strip().strip("|").split("|")]
        name, hd, ac, atk, dmg, shock, move, ml, inst, skill, save = r
        attacks = 1
        am = re.match(r"^([+-]?\d+)(?: x(\d))?$", atk)
        if am.group(2):
            attacks = int(am.group(2))
        hdn = int(hd)
        note = group + " (example stat line)." + (" Its AC comes from the armor it wears." if ac.endswith("a") else "")
        out.append(entity("Creature", name, note, "creatureTable", {"Stats": {
            "HD": hdn, "Max HP": max(1, round(hdn * 4.5)), "HP": max(1, round(hdn * 4.5)),
            "AC": int(ac.rstrip("a")), "Atk": int(am.group(1)), "Attacks": attacks, "Dmg": dmg, "Shock": shock,
            "Move": move.replace("'", " ft"), "ML": int(ml), "Inst": int(inst), "Skill": int(skill),
            "Save": int(save.rstrip("+"))}}))
    return out


library = {
    "name": "Worlds Without Number SRD",
    "description": "Weapons, armor, gear, foci, spells, arts, faction assets and example stat lines from the Worlds Without Number System Reference Document v1.0 by Kevin Crawford (Sine Nomine Publishing, 2024), which is dedicated to the public domain under CC0 1.0 Universal. Converted from the Markdown transcription at https://github.com/klrkdekira/wwn-system-json. Not an official Sine Nomine product.",
    "entities": weapons() + armor() + gear() + foci() + spells() + arts() + assets() + creatures(),
}
Path(OUT).write_text(json.dumps(library, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
counts = {}
for e in library["entities"]:
    counts[e["type"]] = counts.get(e["type"], 0) + 1
print(counts)
