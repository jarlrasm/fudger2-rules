---
name: frules
description: Write, extend or fix Fudger game system rules in the .frules language (the files in fudger2-rules/systems that define character sheets, creatures, library item types, dice and calculations for a tabletop RPG system). Use when the user asks to add a new game system, add or change fields on a character/creature sheet, add a secondary/library type, write formulas or dice rolls, add an extension, or fix a .frules parse error.
---

# Writing frules

`.frules` files describe a tabletop RPG system for Fudger: which entity types exist, what their sheets look like, which fields players can edit, and how values and dice rolls are calculated. Rules live in `systems/` in this repo, and each system is registered in `systems/rules.json`. They are parsed by the Elm code in the sibling app repo, `/home/jarl/Development/fudger2/Web/GameSystemParser/src`, and rendered by `/home/jarl/Development/fudger2/Web/src/Sheet`.

Read [reference.md](reference.md) for the full language before writing anything non-trivial. Look at an existing system that resembles the one you are building:

- `Fudge/fudge.frules` — small, complete; enums, slots with overflow, a heal button, secondary item lists, an extension
- `edge/edge.frules` — minimal; custom dice roll, keyvalues with custom value types
- `DND/` — split across many files; library lookups, computed values, regex bonuses, advantage/disadvantage rolls, conditional visibility
- `starwars/sw.frules` — extra entity types (spaceships), custom CSS

## Workflow

1. Read `rules.json` and a similar existing system.
2. Write the file(s). Start with `#include "/systems/common.frules"` if you need `compare`, `max (list)`, `nameAndDescription` or `entityTypeDescription`.
3. Define one `system` at the top level, and point `characters`, `creatures` and every name in `secondaryTypes` at a `ruleset`.
4. Register a new system (or extension) in `rules.json`.
5. Validate by parsing (see below). Fix and repeat until it passes.

## Validate

The Elm test suite parses every system listed in `rules.json`, resolving `#include`s, and reports the line and column of the first parse error:

```bash
cd /home/jarl/Development/fudger2/Web && ./test.sh tests/RulesCorpusTests.elm
```

The test lives in the fudger2 app repo, runs in Docker, and reads this repo's `systems/` by default (override with `RULES_DIR`). To check a draft without touching `rules.json`, copy `common.frules` and the draft into a scratch folder laid out like `systems/` with its own `rules.json`, and point `RULES_DIR` at it. Includes are resolved by path starting with `/systems/`, so keep the same paths.

Parsing only proves the syntax. Names that don't resolve and values of the wrong type fail silently at runtime (a blank cell, `0`, or "X not supported"), so double-check every reference against the table it points to.

## Gotchas that break files

- **No comments.** The language has no comment syntax. Don't add any.
- **No `#` in strings**, and put every `#include` at the top of the file. The include resolver stops at the first `#` that isn't an `#include`.
- **Bare names are letters and digits only.** No `_` or `-`. Anything else needs single quotes: `'Very hurt'`. Quoted names allow only letters, digits and spaces.
- **Strings use double quotes and have no escapes.** A string can't contain `"`. Backslashes are kept as-is, which is handy for regexes.
- **Operators:** `+ - * /`, `==`, `>`, `<`. There is no `>=`, `<=`, `!=`, `and`, `or` or `not`; nest `if`s instead. `if` always needs `else`.
- **`max a b` and `min a b`** take two operands without commas. `max (a, b)` parses but calls a function named `max` instead, and the one in `common.frules` takes a single list: `max ([a, b])`. Every other function is called as `f (a, b)`.
- **A call at the top level must have its `(` on the same line as the function name.** Inside parentheses, newlines are fine.
- **Same-named definitions merge.** Two `characterTable = ruleset {...}` blocks combine their fields, and two lists concatenate. This is how extensions and multi-file systems add to a base system, but it also means an accidental duplicate name silently merges.
- **`otherLibararyTypes` is spelled with the typo.** The code reads that exact name.
