"""Builds the 13th Age library from the 13th Age Archmage Engine SRD.

The Archmage Engine (https://pelgranepress.com/media/SRD/13thAgeArchmageEngineSRD.pdf)
is Fire Opal Media's and Pelgrane Press's System Reference Document for 13th
Age, the 13th Age Bestiary and 13 True Ways, licensed under the Open Game
License v1.0a. Its game mechanics are Open Game Content; proper names,
dialogue, plots and the like are Product Identity. This takes the monster
stat blocks (game mechanics only, without the flavour text) from the Monster
Reference chapter.

    python3 tools/archmage_import.py 13thAgeArchmageEngineSRD.pdf systems/13thage/13thage.json
"""

import json
import re
import subprocess
import sys

PDF = sys.argv[1]
OUT = sys.argv[2]
SYSTEM = "ThirteenthAge"
URL = "/systems/13thage/13thage.json"
# The Monster Reference chapter, by the PDF's own page numbers.
FIRST, LAST = 368, 673
SIZES = {"normal": "Normal", "large": "Large", "huge": "Huge", "double-strength": "Large", "triple-strength": "Huge"}
ROLES = {"archer", "blocker", "caster", "leader", "mook", "spoiler", "troop", "wrecker"}
DEFENSE = re.compile(r"(?:\s+(AC|PD|MD|HP)\s+(\d+)|\s{2,}(AC|PD|MD|HP)\s*(\d*))\s*$")
ATTACK = re.compile(r"^(?:(R|C|M or R): )?(.+?) \+(\d+)(?: vs\. (AC|PD|MD)\b)?(.*?)—\s*(.*)$")
ATTACK_START = re.compile(r"^(?:(R|C|M or R): )?[^:]+? \+\d+(?: vs\. (AC|PD|MD)\b|\s*—)")
TRIGGER = re.compile(r"^(Natural [^:]{1,40}|Miss|Hit|Limited use|Quick use|Special|Each failed save|First failed save|Second failed save|Third failed save|Failed save|Hit vs\.[^:]*|Critical hit)[^:]{0,30}:")


def lines():
    text = subprocess.run(["pdftotext", "-layout", "-f", str(FIRST), "-l", str(LAST), PDF, "-"], capture_output=True, text=True, check=True).stdout
    for page, page_text in enumerate(text.split("\f"), FIRST):
        for line in page_text.split("\n"):
            if line.startswith("13th Age Archmage Engine, version") or line.startswith("Copyright ©"):
                continue
            yield page, line.rstrip()


def is_name(line, following):
    """A monster's name is a line at the margin with its size on the next line."""
    if not line or line[0].isspace() or len(line) > 60:
        return False
    nxt = next((f for f in following if f.strip()), "")
    return nxt.startswith(" ") and nxt.split()[0].lower() in SIZES and "Initiative" in nxt


def blocks():
    pages, all_lines = zip(*lines())
    i = 0
    while i < len(all_lines):
        if is_name(all_lines[i], all_lines[i + 1:i + 3]):
            name, page, body = all_lines[i].strip(), pages[i], []
            i += 1
            while i < len(all_lines) and not (all_lines[i] and not all_lines[i][0].isspace()):
                body.append(all_lines[i])
                i += 1
            yield name, page, body
        else:
            i += 1


def split(body):
    """The left column (size, level, role, type), the defenses on the right,
    and the paragraphs of the middle column."""
    left, defenses, paragraphs, gap = [], {}, [], True
    for line in body:
        if not line.strip():
            gap = True
            continue
        found = DEFENSE.search(line)
        if found:
            key, value = (found.group(1), found.group(2)) if found.group(1) else (found.group(3), found.group(4))
            if value:
                defenses[key] = int(value)
            line = line[:found.start()]
        if line.startswith(" ") and not line.startswith("   ") and line.strip():
            parts = re.split(r"\s{2,}", line.strip(), maxsplit=1)
            left.append(parts[0])
            line = parts[1] if len(parts) > 1 else ""
        text = line.strip()
        if not text:
            continue
        if gap or TRIGGER.match(text) or ATTACK_START.match(text) or text == "Nastier Specials" or not paragraphs:
            paragraphs.append(text)
        else:
            joiner = "" if paragraphs[-1].endswith("-") and not paragraphs[-1].endswith(" -") else " "
            paragraphs[-1] += joiner + text
        gap = text == "Nastier Specials"
    return left, defenses, paragraphs


def monster(name, page, body):
    left, defenses, paragraphs = split(body)
    size, level, role, kind = "Normal", 0, "Troop", []
    for token in left:
        lower = token.lower()
        found = re.match(r"(\d+)(?:st|nd|rd|th)?\s+level", lower)
        if lower in SIZES:
            size = SIZES[lower]
            strength = token if lower.endswith("strength") else ""
        elif found:
            level = int(found.group(1))
        elif lower.strip("[]") in ROLES:
            role = lower.strip("[]").capitalize()
        else:
            kind.append(token)
    initiative, attacks, abilities, nastier = 0, [], [], False
    for text in paragraphs:
        found = re.match(r"Initiative:\s*([+-]?\d+)", text)
        attack = ATTACK.match(text)
        if found:
            initiative = int(found.group(1))
        elif text == "Nastier Specials":
            nastier = True
        elif attack and not nastier:
            prefix = {"R": "Ranged: ", "C": "Close: ", "M or R": "Melee or ranged: "}.get(attack.group(1) or "", "")
            target = attack.group(5).strip()
            attacks.append({
                "Name": prefix + attack.group(2).strip() + (f" {target}" if target else ""),
                "Attack": int(attack.group(3)),
                "Defense": attack.group(4) or "AC",
                "Hit": attack.group(6).strip(),
                "Triggers": "",
            })
        elif TRIGGER.match(text) and attacks and not nastier:
            attacks[-1]["Triggers"] = (attacks[-1]["Triggers"] + " " + text).strip()
        else:
            label, _, rest = text.partition(":")
            if rest and len(label) < 60:
                abilities.append({"Name": ("Nastier: " if nastier else "") + label.strip(), "Description": rest.strip()})
            elif abilities:
                abilities[-1]["Description"] += "\n\n" + text
            else:
                abilities.append({"Name": "Note", "Description": text})
    kind_text = " ".join(kind).replace("& ", "& ").strip()
    missing = "" if defenses else "\n\nThe SRD leaves out this monster's defenses and hit points."
    summary = f"*{size} level {level} {role.lower()}{(' [' + kind_text.lower() + ']') if kind_text else ''}*"
    return {
        "type": "Creature",
        "name": name,
        "description": summary + missing,
        "images": {},
        "rulesets": [{
            "system": SYSTEM,
            "implementation": {
                "monsterTable": {
                    "Monster": {
                        "Level": level,
                        "Size": size,
                        "Role": role,
                        "Type": kind_text,
                        "Initiative": initiative,
                        **{key: defenses[source] for key, source in [("AC", "AC"), ("PD", "PD"), ("MD", "MD"), ("Max HP", "HP"), ("HP", "HP")] if source in defenses},
                    },
                    "Attacks": attacks,
                    "Abilities": abilities,
                }
            },
        }],
        "references": [{"document": "srd", "page": page}],
    }


seen, entities = set(), []
for name, page, body in blocks():
    if name.lower() in seen:
        continue
    seen.add(name.lower())
    entities.append(monster(name, page, body))

library = {
    "name": "13th Age Archmage Engine",
    "description": "Monsters from the 13th Age Archmage Engine SRD (version 3.0) by Fire Opal Media and Pelgrane Press, game mechanics only, Open Game Content under the Open Game License v1.0a. See LICENSE-13thage.md next to this library.",
    "url": URL,
    "gamemaster": "",
    "documents": [{"key": "srd", "name": "13th Age Archmage Engine SRD", "url": "/systems/13thage/13thAgeArchmageEngineSRD.pdf", "public": True}],
    "entities": entities,
}
json.dump(library, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(entities), "monsters")
