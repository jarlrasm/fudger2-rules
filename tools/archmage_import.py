"""Builds the 13th Age library from the 13th Age Archmage Engine SRD.

The Archmage Engine (https://pelgranepress.com/media/SRD/13thAgeArchmageEngineSRD.pdf)
is Fire Opal Media's and Pelgrane Press's System Reference Document for 13th
Age, the 13th Age Bestiary and 13 True Ways, licensed under the Open Game
License v1.0a. Its game mechanics are Open Game Content; proper names,
dialogue, plots and the like are Product Identity. This takes the monster
stat blocks (game mechanics only, without the flavour text) from the Monster
Reference chapter, the class spells, and the magic items. Spells and magic
items are found by their heading fonts, which pdftohtml reports.

    python3 tools/archmage_import.py 13thAgeArchmageEngineSRD.pdf systems/13thage/13thage.json
"""

import html
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


# Headings, by pdftohtml font size and colour.
CHAPTER = {("19", "#b76d0a"), ("24", "#b76d0a")}
SECTION = ("18", "#794807")
ENTRY = ("17", "#b76d0a")
CLASSES = ["Barbarian", "Bard", "Chaos Mage", "Cleric", "Commander", "Druid", "Fighter", "Monk", "Necromancer", "Occultist", "Paladin", "Ranger", "Rogue", "Sorcerer", "Wizard"]
CLASS_PAGES = (31, 318)
RACE_PAGES = (17, 30)
ONE_USE_PAGES = (677, 681)
ITEM_PAGES = (677, 711)
SPELL_TYPE = re.compile(r"^((Ranged|Close-quarters|Close|Melee)?\s*spell|Bardic song)$", re.I)
USAGE = re.compile(r"^(At-Will|Daily|Recharge.*|Once per battle.*|Cyclic.*|Twice per battle.*|Per battle.*)$", re.I)
FEAT = re.compile(r"^(Adventurer|Champion|Epic)( Feat| Tier)?s?$")


def xml_lines(first, last):
    """The text of the pages as lines, each with its page and heading font.
    Runs on one line (such as the "th" of "5th") are joined."""
    out = subprocess.run(["pdftohtml", "-xml", "-i", "-q", "-stdout", "-f", str(first), "-l", str(last), PDF], capture_output=True, text=True, check=True).stdout
    fonts = {m.group(1): (m.group(2), m.group(3)) for m in re.finditer(r'<fontspec id="(\d+)" size="(\d+)" family="[^"]*" color="([^"]*)"', out)}
    lines = []
    for page in out.split('<page number="')[1:]:
        number = int(page.split('"')[0])
        for m in re.finditer(r'<text top="(\d+)" left="\d+" width="\d+" height="\d+" font="(\d+)">(.*?)</text>', page):
            top, font, raw = int(m.group(1)), fonts[m.group(2)], m.group(3)
            italic = raw.startswith("<i>")
            text = html.unescape(re.sub(r"<b>(.*?)</b>", r"**\1**", raw))
            text = re.sub(r"</?i>", "", text)
            if text.startswith("13") and font[0] == "15" or text.startswith("Copyright ©") or (font[0] == "15" and "Archmage Engine, version" in text):
                continue
            if lines and lines[-1]["page"] == number and abs(lines[-1]["top"] - top) <= 6:
                lines[-1]["text"] += text
                continue
            lines.append({"page": number, "top": top, "font": font, "italic": italic, "text": text})
    for line in lines:
        line["text"] = re.sub(r"\s+", " ", line["text"]).strip()
        line["text"] = re.sub(r"\*\*\s*\*\*", "", line["text"])
        line["text"] = re.sub(r"\*\*([^*]*?)\s+\*\*", r"**\1** ", line["text"]).strip()
    return [l for l in lines if l["text"] and l["text"] not in ("th", "13")]


def paragraphs(texts):
    """Lines of running text joined into paragraphs: a new one starts at a field
    such as **Hit:**, a feat heading, or a line after a line that ends a sentence
    short of the margin."""
    result = []
    for text in texts:
        starts = text.startswith("**") or FEAT.match(text) or re.match(r"^\d+(st|nd|rd|th) level spell", text) or not result
        if starts or result[-1].endswith((".", ":", ")")) and len(result[-1]) < 60:
            result.append(text)
        else:
            result[-1] += ("" if result[-1].endswith("-") else " ") + text
    return result


def field(lines, name):
    found = next((l for l in lines if l.startswith(f"**{name}:**")), "")
    return found[len(name) + 5:].strip()


def spells():
    lines = xml_lines(*CLASS_PAGES)
    result, seen, klass, level = [], set(), "", 0
    i = 0
    while i < len(lines):
        line = lines[i]
        text = line["text"]
        if line["font"] in CHAPTER and text in CLASSES:
            klass, level = text, 0
        elif line["font"] == SECTION and re.search(r"Level (Spells|Songs|Battle Cries|Invocations)$|Level\+?\)$", text):
            found = re.match(r"(\d+)", text)
            level = int(found.group(1)) if found else level
        elif line["font"] == ENTRY and not FEAT.match(text) and any(SPELL_TYPE.match(l["text"]) for l in lines[i + 1:i + 3]):
            body, j = [], i + 1
            while j < len(lines):
                nxt = lines[j]
                heading = nxt["font"] in CHAPTER or nxt["font"] == SECTION or (nxt["font"] == ENTRY and not FEAT.match(nxt["text"]))
                if heading:
                    break
                body.append(("### " if nxt["font"] == ENTRY else "") + nxt["text"])
                j += 1
            name = text.rstrip(" .")
            stated = re.search(r"\s*\((\d+)(?:st|nd|rd|th) level\+?\)$", name)
            if stated:
                name = name[:stated.start()]
            spell_level = int(stated.group(1)) if stated else level
            key = (klass, name.lower())
            if klass and key not in seen:
                seen.add(key)
                head = [b for b in body[:4] if not b.startswith("**") and not b.startswith("###")]
                kind = next((h for h in head if SPELL_TYPE.match(h)), "")
                usage = next((h for h in head if USAGE.match(h)), "")
                action = next((h for h in head if h not in (kind, usage) and re.search(r"action", h, re.I) and len(h) < 60), "")
                text_lines = paragraphs([b for b in body if b not in (kind, usage, action) and not b.startswith("###")] )
                description = []
                for b in body:
                    if b in (kind, usage, action):
                        continue
                    if b.startswith("### "):
                        description.append("\n**" + b[4:] + "**")
                    else:
                        description.append(b)
                described = "\n\n".join(paragraphs([d.strip() for d in description if d.strip()]))
                summary = ", ".join(x for x in [kind, usage, action] if x)
                result.append({
                    "type": "Spells",
                    "name": name,
                    "description": f"*{klass}, level {spell_level}. {summary}.*\n\n{described}".strip(),
                    "images": {},
                    "rulesets": [{"system": SYSTEM, "implementation": {"spellStats": {"Stats": {
                        "Class": klass,
                        "Level": spell_level,
                        "Type": kind,
                        "Usage": usage,
                        "Action": action,
                        "Target": field(text_lines, "Target"),
                        "Attack": field(text_lines, "Attack"),
                    }}}}],
                    "references": [{"document": "srd", "page": line["page"]}],
                })
            i = j
            continue
        i += 1
    return result


def magic_items():
    lines = xml_lines(*ITEM_PAGES)
    start = next(i for i, l in enumerate(lines) if l["text"] == "Magic Item Descriptions")
    result, seen, slot, tier, default = [], set(), "", "", ""
    i = start + 1
    while i < len(lines):
        line = lines[i]
        text = line["text"]
        if line["font"] == SECTION:
            slot, tier, default = text, "", ""
        elif line["font"] == ENTRY and line["italic"] and text == "Default Bonus":
            body, j = [], i + 1
            while j < len(lines) and lines[j]["font"] not in (ENTRY, SECTION):
                body.append(lines[j]["text"])
                j += 1
            default = " ".join(body)
            i = j
            continue
        elif line["font"] == ENTRY and line["italic"] and FEAT.match(text):
            tier = FEAT.match(text).group(1)
        elif line["font"] == ENTRY and slot:
            body, j = [], i + 1
            while j < len(lines) and lines[j]["font"] not in (ENTRY, SECTION) and lines[j]["font"] not in CHAPTER:
                body.append(lines[j]["text"])
                j += 1
            name = text.rstrip(" .")
            if (slot, name.lower()) not in seen:
                seen.add((slot, name.lower()))
                described = " ".join(body)
                quirk = re.search(r"Quirk:\s*(.+?)\s*$", described)
                usage = re.search(r"\b(Recharge \d+\+|Daily|Once per battle|Once per day|At-Will)", described)
                result.append({
                    "type": "Magic Items",
                    "name": f"{name} ({slot.split(',')[0]})",
                    "description": "\n\n".join(x for x in [f"*{slot}, {tier.lower() or 'any'} tier.*", described, f"**Default bonus:** {default}" if default else ""] if x),
                    "images": {},
                    "rulesets": [{"system": SYSTEM, "implementation": {"magicItemStats": {"Stats": {
                        "Slot": slot,
                        "Tier": tier,
                        "Default bonus": default,
                        "Usage": usage.group(1) if usage else "",
                        "Quirk": quirk.group(1) if quirk else "",
                    }}}}],
                    "references": [{"document": "srd", "page": line["page"]}],
                })
            i = j
            continue
        i += 1
    return result


SUBHEAD = re.compile(r"^((Adventurer|Champion|Epic)( Feat| Tier)?s?|Feat Tiers|(Opening|Flow|Finishing) Attack\b.*|.* Costs)$")
POWER_SECTION = re.compile(r"^(\d+)(?:st|nd|rd|th) Level (Maneuvers|Commands|Tactics|Battle Cries|Powers)$|^(Adventure|Champion|Epic) Tier (Forms)$")
TALENT_SECTION = re.compile(r"Talents$|^Iconic Spells & Feats$|^Class Features?$|^Racial Power$|^General Feats$")
CANTRIP_PAGES = (302, 303)


def entries(lines, start=0):
    """Each entry heading with its body, the section and chapter it is in, and
    its page. Feat tiers and the attacks of a monk form are kept in the body."""
    chapter, section, i = "", "", start
    while i < len(lines):
        line = lines[i]
        if line["font"] in CHAPTER:
            chapter, section = line["text"], ""
        elif line["font"] == SECTION:
            section = line["text"]
        elif line["font"] == ENTRY and not SUBHEAD.match(line["text"]):
            body, j = [], i + 1
            while j < len(lines):
                nxt = lines[j]
                if nxt["font"] in CHAPTER or nxt["font"] == SECTION or (nxt["font"] == ENTRY and not SUBHEAD.match(nxt["text"])):
                    break
                body.append(("### " if nxt["font"] == ENTRY else "") + nxt["text"])
                j += 1
            yield {"name": line["text"].rstrip(" ."), "chapter": chapter, "section": section, "page": line["page"], "body": body}
            i = j
            continue
        i += 1


def described(body, skip=()):
    parts = []
    for b in body:
        if b in skip:
            continue
        parts.append("\n**" + b[4:] + "**" if b.startswith("### ") else b)
    return "\n\n".join(paragraphs([p.strip() for p in parts if p.strip()]))


def class_material():
    """Class powers, talents, class features, racial powers, general feats and
    wizard cantrips. Entries with a spell line are left to spells()."""
    powers, talents, cantrips, seen = [], [], [], set()
    lines = xml_lines(RACE_PAGES[0], CLASS_PAGES[1])
    for entry in entries(lines):
        body, name, section, chapter = entry["body"], entry["name"], entry["section"], entry["chapter"]
        head = [b for b in body[:4] if not re.match(r"^\*\*[^*]+:\*\*", b) and not b.startswith("###")]
        if any(SPELL_TYPE.match(h) for h in head[:2]):
            continue
        reference = [{"document": "srd", "page": entry["page"]}]
        klass = chapter if chapter in CLASSES else ""
        power = POWER_SECTION.match(section)
        if klass == "Wizard" and CANTRIP_PAGES[0] <= entry["page"] <= CANTRIP_PAGES[1] and body and re.search(r"\b(cantrip|spell)\b", body[0]):
            name = re.sub(r"\s*\(standard duration\)$", "", name)
            if ("cantrip", name.lower()) in seen:
                continue
            seen.add(("cantrip", name.lower()))
            cantrips.append({
                "type": "Spells", "name": name,
                "description": f"*Wizard cantrip.*\n\n{described(body)}",
                "images": {},
                "rulesets": [{"system": SYSTEM, "implementation": {"spellStats": {"Stats": {
                    "Class": "Wizard", "Level": 0, "Type": "Cantrip", "Usage": "Cantrip", "Action": "", "Target": "", "Attack": ""}}}}],
                "references": reference,
            })
        elif power and klass:
            level = int(power.group(1)) if power.group(1) else {"Adventure": 1, "Champion": 5, "Epic": 8}[power.group(3)]
            kind = (power.group(2) or power.group(4)).rstrip("s").replace("Battle Crie", "Battle cry")
            if (klass, name.lower()) in seen:
                continue
            seen.add((klass, name.lower()))
            kind_line = next((h for h in head if re.search(r"attack|action", h, re.I) and len(h) < 60), "")
            usage = next((h for h in head if USAGE.match(h.replace("**", ""))), "")
            text_lines = paragraphs([b for b in body if not b.startswith("###")])
            powers.append({
                "type": "Class Powers", "name": name,
                "description": f"*{klass} {kind.lower()}, level {level}.*\n\n{described(body, (kind_line, usage))}",
                "images": {},
                "rulesets": [{"system": SYSTEM, "implementation": {"classPowerStats": {"Stats": {
                    "Class": klass, "Kind": kind, "Level": level, "Type": kind_line, "Usage": usage.replace("**", ""),
                    "Trigger": field(text_lines, "Triggering Roll") or field(text_lines, "Trigger"),
                    "Attack": field(text_lines, "Attack")}}}}],
                "references": reference,
            })
        elif TALENT_SECTION.search(section) and body:
            if section == "Racial Power":
                kind, owner = "Racial power", chapter
            elif section == "General Feats":
                kind, owner = "General feat", ""
            elif section.startswith("Class Feature"):
                kind, owner = "Class feature", klass
            else:
                kind, owner = "Talent", klass
            if (kind == "Racial power" or klass) or kind == "General feat":
                key = (kind, owner, name.lower())
                if key in seen:
                    continue
                seen.add(key)
                label = f"{owner} {kind.lower()}" if owner else kind
                talents.append({
                    "type": "Talents and Feats", "name": name,
                    "description": f"*{label}.*\n\n{described(body)}",
                    "images": {},
                    "rulesets": [{"system": SYSTEM, "implementation": {"talentStats": {"Stats": {"Kind": kind, "Class": owner}}}}],
                    "references": reference,
                })
    return powers, talents, cantrips


def one_use_items():
    """Potions, oils and runes, with their cost tables."""
    result = []
    lines = xml_lines(*ONE_USE_PAGES)
    start = next(i for i, l in enumerate(lines) if l["text"] == "One-Use Items")
    end = next(i for i, l in enumerate(lines) if l["text"] == "True Magic Items")
    for entry in entries(lines[start:end]):
        if entry["section"] not in ("Potions", "Oils", "Runes") or not entry["body"]:
            continue
        slot = entry["section"].rstrip("s")
        result.append({
            "type": "Magic Items", "name": entry["name"],
            "description": f"*One-use item: {slot.lower()}.*\n\n{described(entry['body'])}",
            "images": {},
            "rulesets": [{"system": SYSTEM, "implementation": {"magicItemStats": {"Stats": {
                "Slot": f"One-use {slot.lower()}", "Tier": "", "Default bonus": "", "Usage": "One use", "Quirk": ""}}}}],
            "references": [{"document": "srd", "page": entry["page"]}],
        })
    return result


seen, entities = set(), []
for name, page, body in blocks():
    if name.lower() in seen:
        continue
    seen.add(name.lower())
    entities.append(monster(name, page, body))
powers, talents, cantrips = class_material()
entities += spells() + cantrips + powers + talents + magic_items() + one_use_items()

# Some classes share a spell or feature name; tell those apart by class.
names = {}
for e in entities:
    names[(e["type"], e["name"])] = names.get((e["type"], e["name"]), 0) + 1
for e in entities:
    owner = next(iter(e["rulesets"][0]["implementation"].values())).get("Stats", {}).get("Class", "")
    if names[(e["type"], e["name"])] > 1 and owner:
        e["name"] = f"{e['name']} ({owner})"

library = {
    "name": "13th Age Archmage Engine",
    "description": "Monsters, class spells, powers, talents and features, racial powers, feats and magic items from the 13th Age Archmage Engine SRD (version 3.0) by Fire Opal Media and Pelgrane Press, game mechanics only, Open Game Content under the Open Game License v1.0a. See LICENSE-13thage.md next to this library.",
    "url": URL,
    "gamemaster": "",
    "documents": [{"key": "srd", "name": "13th Age Archmage Engine SRD", "url": "/systems/13thage/13thAgeArchmageEngineSRD.pdf", "public": True}],
    "entities": entities,
}
json.dump(library, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(entities), "entities:", {t: sum(1 for e in entities if e["type"] == t) for t in ["Creature", "Spells", "Class Powers", "Talents and Feats", "Magic Items"]})
