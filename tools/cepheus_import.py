"""Builds the Traveller equipment library from the Cepheus Engine SRD (OGL 1.0a)."""

import json
import re
import sys
from pathlib import Path

RAW = Path(sys.argv[1])
OUT = sys.argv[2]
SYSTEM = "Traveller"
URL = "/systems/traveller/cepheus.json"

RANGE_METRES = {"pistol": "50", "shotgun": "50", "assault weapon": "250", "rifle": "500", "rocket": "5000", "thrown": "12"}

text = (RAW / "book1" / "equipment.md").read_text(encoding="utf-8")


def unlink(cell):
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", cell).replace("\\", "").strip()


def tables():
    """Each Markdown table with the heading it is under."""
    heading, rows, header, result = "", [], None, []
    for line in text.split("\n") + [""]:
        if line.startswith("#"):
            heading = line.lstrip("#").strip()
        if line.strip().startswith("|"):
            cells = [unlink(c) for c in line.strip().strip("|").split("|")]
            if header is None:
                header = cells
            elif not all(set(c) <= set("-: ") for c in cells):
                rows.append(dict(zip(header, cells)))
        elif header is not None:
            result.append((heading, header, rows))
            header, rows = None, []
    return result


def descriptions():
    """Bold-named paragraphs, such as **Ablat:** text."""
    return {name.strip(): body.strip() for name, body in re.findall(r"^\*\*([^*]+?):?\*\*:?\s*(.+)$", text, re.M)}


def entity(type_, name, description, implementation):
    return {
        "type": type_,
        "name": name,
        "description": description,
        "images": {},
        "rulesets": [{"system": SYSTEM, "implementation": implementation}],
    }


def range_of(text_):
    for key, metres in RANGE_METRES.items():
        if key in text_.lower():
            return metres
    return ""


def build():
    found = descriptions()
    result = []
    for heading, header, rows in tables():
        if "Weapon" in header and ("Damage" in header or "Dmg" in header) and "Radius" not in header:
            melee = "melee" in heading.lower()
            for row in rows:
                name = row["Weapon"]
                result.append(
                    entity(
                        "Weapons",
                        name,
                        found.get(name, ""),
                        {
                            "weaponStats": {
                                "Stats": {
                                    "Skill": "Melee" if melee else ("Heavy Weapons" if "heavy" in heading.lower() else "Gun Combat"),
                                    "TL": row.get("TL", ""),
                                    "Range": "" if melee else range_of(row.get("Range", "")),
                                    "Damage": row.get("Damage", row.get("Dmg", "")),
                                    "Magazine": "",
                                    "Traits": ", ".join(f"{key} {row[key]}" for key in ["RoF", "Type", "Recoil", "LL"] if row.get(key) and row.get(key) != "—"),
                                    "Mass": row.get("Wgt", ""),
                                    "Cost": row.get("Cost", ""),
                                }
                            }
                        },
                    )
                )
        elif header[:1] == ["Armor"]:
            for row in rows:
                name = row["Armor"]
                result.append(
                    entity(
                        "Armour",
                        name,
                        found.get(name, ""),
                        {"armourStats": {"Stats": {"Protection": row.get("AR", ""), "TL": row.get("TL", ""), "Rad": "", "Mass": row.get("Wgt", ""), "Cost": row.get("Cost", "")}}},
                    )
                )
        elif "TL" in header and any(h.startswith("Cost") for h in header) and header[0] not in ("Vehicle", "Weapon"):
            cost_key = next(h for h in header if h.startswith("Cost"))
            for row in rows:
                name = row[header[0]]
                extra = ", ".join(f"{h}: {row[h]}" for h in header[1:] if h not in ("TL", cost_key, "Wgt") and row.get(h))
                result.append(
                    entity(
                        "Equipment",
                        name,
                        "\n\n".join(part for part in [f"*{heading}*", extra, found.get(name, "")] if part),
                        {"equipmentStats": {"Stats": {"TL": row.get("TL", ""), "Mass": row.get("Wgt", ""), "Cost": row[cost_key]}}},
                    )
                )
    return result


library = {
    "name": "Cepheus Engine equipment",
    "description": "Weapons, armour and equipment from the Cepheus Engine System Reference Document, Open Game Content under the Open Game License 1.0a (see LICENSE-cepheus.md). Cepheus Engine and Samardan Press are the trademarks of Jason \"Flynn\" Kemp; this library is not affiliated with Jason \"Flynn\" Kemp or Samardan Press. Converted from https://github.com/orffen/cepheus-srd.",
    "url": URL,
    "gamemaster": "",
    "entities": build(),
}

json.dump(library, open(OUT, "w"), ensure_ascii=False, indent=1)
print(len(library["entities"]), "entities")
