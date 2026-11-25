"""Builds the Basic Roleplaying library from Chaosium's ORC content document.

Chaosium publishes the text of Basic Roleplaying: Universal Game Engine as the
"Basic Roleplaying ORC Content Document" under the ORC License, as PDF and RTF at
https://www.chaosium.com/content/orclicense/BasicRoleplaying-ORC-Content-Document.rtf
This reads the RTF (its tables keep their cells there) and takes every weapon
table of the Equipment chapter and every creature of the Creatures chapter that
has a full stat block.

    python3 -I tools/brp_import.py BasicRoleplaying-ORC-Content-Document.rtf systems/brp/brp.json
"""

import json
import re
import sys
from pathlib import Path

SOURCE = Path(sys.argv[1])
OUT = sys.argv[2]
SYSTEM = "BasicRoleplaying"

SKIP = {"fonttbl", "colortbl", "stylesheet", "info", "pict", "header", "footer", "listtable", "listoverridetable",
        "themedata", "colorschememapping", "latentstyles", "datastore", "xmlnstbl", "rsidtbl", "generator",
        "mmathPr", "pgdsctbl", "object", "shppict", "nonshppict", "fldinst"}

TOKEN = re.compile(r"\\([a-zA-Z]+)(-?\d+)? ?|\\'([0-9a-fA-F]{2})|\\(.)|([{}])|([^\\{}\r\n]+)|[\r\n]+")


def rtf_text(data):
    """Plain text of an RTF document: paragraphs on lines, table cells separated by tabs, superscripts left out."""
    out, stack = [], []
    skip, sup, uc, pending = False, False, 1, 0
    for word, arg, hexc, sym, brace, text in TOKEN.findall(data):
        if brace == "{":
            stack.append((skip, uc, sup))
            continue
        if brace == "}":
            skip, uc, sup = stack.pop() if stack else (False, 1, False)
            continue
        if skip:
            continue
        if word:
            if word in SKIP:
                skip = True
            elif word in ("super", "up") and arg != "0":
                sup = True
            elif word in ("nosupersub", "plain") or (word == "up" and arg == "0"):
                sup = False
            elif word == "uc":
                uc = int(arg or 1)
            elif word == "u":
                pending = uc
                if not sup:
                    code = int(arg)
                    out.append(chr(code + 65536 if code < 0 else code))
            elif word in ("par", "line", "sect", "page", "row"):
                out.append("\n")
            elif word == "cell":
                out.append("\t")
            elif word == "tab":
                out.append(" ")
            elif word == "emdash":
                out.append("—")
            elif word == "endash":
                out.append("–")
            elif word in ("lquote", "rquote"):
                out.append("'")
            elif word in ("ldblquote", "rdblquote"):
                out.append('"')
            elif word == "bullet":
                out.append("•")
            continue
        if hexc:
            if pending:
                pending -= 1
            elif not sup:
                out.append(bytes([int(hexc, 16)]).decode("cp1252", errors="replace"))
            continue
        if sym:
            if sym == "*":
                skip = True
            elif sym in "\\{}" and not sup:
                out.append(sym)
            elif sym == "~":
                out.append(" ")
            continue
        if text:
            if pending:
                cut = min(pending, len(text))
                text, pending = text[cut:], pending - cut
            if not sup:
                out.append(text)
    plain = "".join(out)
    plain = re.sub(r"\n+\t", "\t", plain)
    return re.sub(r"\t\n", "\n", plain).replace("\u00a0", " ")


def entity(kind, name, description, ruleset, values):
    return {"type": kind, "name": name, "description": description, "images": {},
            "rulesets": [{"system": SYSTEM, "implementation": {ruleset: values}}]}


COLUMNS = {"Skill": "Skill", "Base": "Base", "Dmg": "Damage", "Attk": "Attacks", "Special": "Special", "Range": "Range",
           "Rng": "Range", "Hands": "Hands", "HP": "Weapon HP", "Parry": "Parry", "STR/DEX": "STR and DEX",
           "Mal": "Malfunction", "Value": "Value", "SIZ/Enc": "SIZ or ENC", "RF": "Rate of Fire", "ENC": "SIZ or ENC"}


def weapons(lines):
    found, seen = [], set()
    for i, line in enumerate(lines):
        cells = line.split("\t")
        if cells[0] != "Weapon" or len(cells) < 6 or cells[1] != "Skill":
            continue
        header = [re.sub(r"\d+$", "", c.strip()) for c in cells]
        category = next((lines[k].strip() for k in range(i - 1, max(0, i - 4), -1) if lines[k].strip() and "\t" not in lines[k] and len(lines[k]) < 40), "Other")
        category = category.replace("Meleee Waapons", "Melee Weapons")
        for row in lines[i + 1:]:
            parts = [c.strip() for c in row.split("\t")]
            if len(parts) < 4 or not parts[0] or parts[0] == "Weapon":
                break
            name = parts[0]
            stats = {"Category": category}
            for column, value in zip(header[1:], parts[1:]):
                field = COLUMNS.get(column)
                if field and value and value != "—":
                    stats[field] = value
            key = (name, category)
            if key in seen:
                continue
            seen.add(key)
            found.append(entity("Weapons", name, "", "brpWeapon", {"Stats": stats}))
    return found


def number(text):
    match = re.search(r"\d+", text or "")
    return int(match.group(0)) if match else 0


def creatures(lines):
    starts = [i for i, l in enumerate(lines) if l.startswith("STR\tCON\tSIZ")]
    found = []
    previous_end = 0
    blocks = []
    for index in starts:
        name_at = index - 1
        while name_at > previous_end and (len(lines[name_at]) > 40 or lines[name_at].rstrip().endswith((".", ":", ")")) or "\t" in lines[name_at] or not lines[name_at].strip()):
            name_at -= 1
        blocks.append((name_at, index))
        previous_end = index
    for n, (name_at, index) in enumerate(blocks):
        end = blocks[n + 1][0] if n + 1 < len(blocks) else len(lines)
        name = lines[name_at].strip()
        if name in ("Hybrid Form", "Wolf Form"):
            name = "Werewolf, " + name
        names = lines[index].split("\t")
        rolled = "D" in lines[index + 1]
        averages = lines[index + (2 if rolled else 1)].split("\t")
        stats = {c.strip(): number(v) for c, v in zip(names, averages) if c.strip() in ("STR", "CON", "SIZ", "INT", "POW", "DEX", "CHA")}
        body = [l.strip() for l in lines[index + (3 if rolled else 2):end] if l.strip()]
        if not any(l.startswith("Move") for l in body) and n + 1 < len(blocks):
            later = blocks[n + 1][1]
            later_end = blocks[n + 2][0] if n + 2 < len(blocks) else len(lines)
            body += [l.strip() for l in lines[later + 3:later_end] if l.strip()]
        text = "\n".join(body)
        move = re.search(r"Move:\s*([^\t\n]*)", text)
        hp = re.search(r"Hit Points:?\s*(\d+)", text)
        dm = re.search(r"Damage Modifier:\s*([^\t\n]*)", text)
        armor = re.search(r"Armor:?\s*([^\t\n]*)", text)
        attacks = []
        for k, line in enumerate(body):
            if line.startswith("•") or (k > 0 and body[k - 1].startswith("Attacks")):
                for attack in re.finditer(r"([A-Z][\w/' -]*(?:\([^)]*\))?)\s+(\d+)%,\s*([0-9]+D[0-9]+[^ (;,]*)", line.lstrip("• ")):
                    attacks.append({"Name": attack.group(1).strip(), "Chance": int(attack.group(2)), "Damage": attack.group(3)})
        skills = re.search(r"Skills:\s*([^\n]*)", text)
        powers = re.search(r"Powers:\s*([^\n]*)", text)
        description = " ".join(l.strip() for l in lines[name_at + 1:index] if l.strip())
        notes = [l for l in body if not re.match(r"^(Move|Damage Modifier|Attacks|Skills|Powers|•)", l)]
        stats.update({
            "Hit Points": number(hp.group(1)) if hp else 0,
            "Move": move.group(1).strip() if move else "",
            "Damage Modifier": dm.group(1).strip() if dm else "None",
            "Armor": armor.group(1).strip() if armor else "0",
            "Power Points": stats.get("POW", 0),
        })
        found.append(entity("Creature", name, description, "creatureTable", {
            "Stats": stats,
            "Attacks": attacks,
            "Notes": {"Skills": skills.group(1).strip() if skills else "", "Powers": powers.group(1).strip() if powers else "",
                      "Description": "\n\n".join(notes)},
        }))
    return found


lines = rtf_text(SOURCE.read_text(encoding="latin-1")).splitlines()
chapter = next(i for i, l in enumerate(lines) if l.strip() == "11. Creatures")
library = {
    "name": "Basic Roleplaying",
    "description": "Weapons and creatures from Basic Roleplaying: Universal Game Engine (Chaosium Inc.), from the Basic Roleplaying ORC Content Document, licensed under the ORC License. See LICENSE-brp.md.",
    "url": "/systems/brp/brp.json",
    "gamemaster": "",
    "entities": weapons(lines[:chapter]) + creatures(lines[chapter:]),
}
Path(OUT).write_text(json.dumps(library, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
counts = {}
for e in library["entities"]:
    counts[e["type"]] = counts.get(e["type"], 0) + 1
print(counts)
