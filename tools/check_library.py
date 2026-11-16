"""Checks a built-in library against the rules it is for.

Every item must name the system, a type the system has, and a ruleset the
system defines, and every table and field it fills in must exist in that
ruleset. A name that does not match fails silently in the app (the value is
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
    for match in re.finditer(r"^([A-Za-z0-9]+|'[A-Za-z0-9 ]+')\s*(?:\([^)]*\))?\s*=\s*([A-Za-z0-9]*)\s*\n?\s*\{", text, re.M):
        depth, i = 1, match.end()
        while depth and i < len(text):
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        result.setdefault(match.group(1).strip("'"), []).append((match.group(2), text[match.end():i - 1]))
    return result


def field_names(body):
    return set(n.strip("'") for n in re.findall(r"(?:^|\s)([A-Za-z0-9]+|'[A-Za-z0-9 ]+')\s*=", body))


def main(rules_path, library_path):
    text = source("/" + str(Path(rules_path).resolve().relative_to(ROOT)))
    found = blocks(text)
    systems = [name for name, defs in found.items() if any(kind == "system" for kind, _ in defs)]
    system_body = "".join(body for name in systems for kind, body in found[name] if kind == "system")
    types = set(re.findall(r'"([^"]+)"', " ".join(re.findall(r"(?:secondaryTypes|otherLibararyTypes)\s*=\s*\[([^\]]*)\]", system_body)))) | {"Creature", "Decks", "Names"}
    library = json.load(open(library_path))
    problems = []
    for item in library["entities"]:
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
                for table, fields in tables.items():
                    if table not in known:
                        problems.append(f"{item['name']}: {name} has no {table}")
                    elif isinstance(fields, dict):
                        for field in fields:
                            if field not in known:
                                problems.append(f"{item['name']}: {name}.{table} has no {field}")
    for problem in sorted(set(problems))[:40]:
        print(problem)
    print(f"{len(library['entities'])} items, {len(set(problems))} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
