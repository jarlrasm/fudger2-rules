"""Checks a built-in library against the rules it is for.

Every item must name the system, a type the system has, and a ruleset the
system defines, and every table and field it fills in must exist in that
ruleset. Random tables (type Tables) must have valid dice and ranges, and
every item or table they link must be in the libraries the system lists. A name that does not match fails silently in the app (the value is
simply not shown), so this catches typos in import scripts.

    python3 tools/check_library.py systems/daggerheart/daggerheart.frules systems/daggerheart/daggerheart.json
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def source(path, seen=None):
    seen = seen or set()
    if path in seen:
        return ""
    seen.add(path)
    text = (ROOT / path.lstrip("/")).read_text()
    return re.sub(r'#include "([^"]+)"', lambda m: source(m.group(1), seen), text)


def blocks(text):
    """Top-level `name = constructor { ... }` blocks, by name."""
    result = {}
    for match in re.finditer(r"^\s*([A-Za-z0-9]+|'[A-Za-z0-9 ]+')\s*(?:\([^)]*\))?\s*=\s*([A-Za-z0-9]*)\s*\n?\s*\{", text, re.M):
        depth, i = 1, match.end()
        while depth and i < len(text):
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        result.setdefault(match.group(1).strip("'"), []).append((match.group(2), text[match.end():i - 1]))
    return result


def field_names(body):
    """Field names, and the keys a keyvalues table starts with."""
    names = set(n.strip("'") for n in re.findall(r"(?:^|\s)([A-Za-z0-9]+|'[A-Za-z0-9 ]+')\s*=", body))
    for keys in re.findall(r"\bkeys\s*=\s*\[([^\]]*)\]", body):
        names |= set(re.findall(r'"([^"]+)"', keys))
    return names


def open_tables(body):
    """Keyvalues tables whose keys the user adds, so any key is fine."""
    return set(n.strip("'") for n in re.findall(r"([A-Za-z0-9]+|'[A-Za-z0-9 ]+')\s*=\s*keyvalues\s*\{[^{}]*?\beditablekeys\b", body))


DICE = re.compile(r"^\s*(\d*)d(\d+)\s*(?:([+-])\s*(\d+))?\s*$", re.I)


def dice_range(dice):
    if dice.strip().lower() == "d66":
        return (11, 66)
    match = DICE.match(dice)
    if not match:
        return None
    count = int(match.group(1) or 1)
    bonus = int(match.group(4) or 0) * (-1 if match.group(3) == "-" else 1)
    return (count + bonus, count * int(match.group(2)) + bonus)


def table_problems(item, names):
    table = item.get("table")
    label = item["name"]
    if not isinstance(table, dict) or not table.get("entries"):
        return [f"{label}: a table needs entries"]
    entries = table["entries"]
    problems = [f"{label}: an entry needs text, an item, a table or again"
                for entry in entries if not any(key in entry for key in ("text", "item", "table", "again"))]
    if "dice" in table:
        found = dice_range(table["dice"])
        if not found:
            return problems + [f"{label}: dice {table['dice']} are not like 1d20, 2d6 or d66"]
        spans = sorted((entry.get("from"), entry.get("to")) for entry in entries)
        if not all(isinstance(low, int) and isinstance(high, int) and found[0] <= low <= high <= found[1] for low, high in spans):
            problems.append(f"{label}: every entry needs from and to between {found[0]} and {found[1]}")
        elif any(nxt[0] <= prev[1] for prev, nxt in zip(spans, spans[1:])):
            problems.append(f"{label}: entries overlap")
    for entry in entries:
        for kind in ("item", "table"):
            ref = entry.get(kind)
            if ref and ref.get("name", "").strip().lower() not in names[kind]:
                problems.append(f"{label}: no {kind} called {ref.get('name')} in the system's libraries")
    return problems


def linkable_names(system_body, library):
    paths = re.findall(r'"([^"]+\.json)"', " ".join(re.findall(r"(?<![A-Za-z])libraries\s*=\s*\[([^\]]*)\]", system_body)))
    entities = list(library["entities"])
    for path in paths:
        target = ROOT / path.lstrip("/")
        if target.exists():
            entities += json.load(open(target)).get("entities", [])
    return {"table": {e["name"].strip().lower() for e in entities if e.get("type") == "Tables"},
            "item": {e["name"].strip().lower() for e in entities if e.get("type") != "Tables"}}


def main(rules_path, library_path):
    text = source("/" + str(Path(rules_path).resolve().relative_to(ROOT)))
    found = blocks(text)
    systems = [name for name, defs in found.items() if any(kind == "system" for kind, _ in defs)]
    system_body = "".join(body for name in systems for kind, body in found[name] if kind == "system")
    types = set(re.findall(r'"([^"]+)"', " ".join(re.findall(r"(?:secondaryTypes|otherLibararyTypes)\s*=\s*\[([^\]]*)\]", system_body)))) | {"Creature", "Decks", "Names", "Tables"}
    types |= set(re.findall(r'"([^"]+)"', " ".join(re.findall(r"entityTypeDescription\s*\(([^)]*)\)", system_body))))
    library = json.load(open(library_path))
    problems = []
    names = linkable_names(system_body, library)
    for item in library["entities"]:
        if item["type"] == "Tables":
            problems += table_problems(item, names)
        if item["type"] not in types:
            problems.append(f"{item['name']}: type {item['type']} is not in the system")
        for ruleset in item.get("rulesets", []):
            if ruleset["system"] not in systems:
                problems.append(f"{item['name']}: system {ruleset['system']} is not {systems}")
            for name, tables in ruleset["implementation"].items():
                if name == "secondary":
                    continue
                if name not in found:
                    problems.append(f"{item['name']}: no ruleset {name}")
                    continue
                known = set().union(*(field_names(body) for _, body in found[name]))
                anykey = set().union(*(open_tables(body) for _, body in found[name]))
                for table, fields in tables.items():
                    if table not in known:
                        problems.append(f"{item['name']}: {name} has no {table}")
                    elif isinstance(fields, dict) and table not in anykey:
                        for field in fields:
                            if field not in known:
                                problems.append(f"{item['name']}: {name}.{table} has no {field}")
    for problem in sorted(set(problems))[:40]:
        print(problem)
    print(f"{len(library['entities'])} items, {len(set(problems))} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
