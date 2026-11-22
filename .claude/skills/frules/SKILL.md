---
name: frules
description: Write, extend or fix Fudger game system rules in the .frules language (the files in fudger2-rules/systems that define character sheets, creatures, library item types, dice and calculations for a tabletop RPG system), and the name generators in systems/names. Use when the user asks to add a new game system, add or change fields on a character/creature sheet, add a secondary/library type, write formulas or dice rolls, add an extension, add or change name generators or name settings, or fix a .frules parse error.
---

# Writing frules

`.frules` files describe a tabletop RPG system for Fudger: which entity types exist, what their sheets look like, which fields players can edit, and how values and dice rolls are calculated. Rules live in `systems/` in this repo, and each system is registered in `systems/rules.json`. They are parsed by the Elm code in the sibling app repo, `/home/jarl/Development/fudger2/Web/GameSystemParser/src`, and rendered by `/home/jarl/Development/fudger2/Web/src/Sheet`.

Read [reference.md](reference.md) for the full language before writing anything non-trivial. Look at an existing system that resembles the one you are building:

- `Fudge/fudge.frules` — small, complete; enums, slots with overflow, a heal button, secondary item lists, an extension
- `edge/edge.frules` — minimal; custom dice roll, keyvalues with custom value types
- `DND/` — split across many files; library lookups, computed values, regex bonuses, advantage/disadvantage rolls, conditional visibility
- `starwars/sw.frules` — extra entity types (spaceships), custom CSS, one name setting
- `names/*.json` and `names/settings.frules` — name generators (library items of type `Names`) and shared name settings

## Workflow

1. Read `rules.json` and a similar existing system.
2. Write the file(s). Start with `#include "/systems/common.frules"` if you need `compare`, `nameAndDescription` or `entityTypeDescription`. Make each sheet look similar to the game's official character sheet: the same sections in the same order and places, the same field names and groupings, and a similar feel (colours, fonts, borders) through custom CSS where the system has it. A player who knows the paper sheet should find things where they expect them. Copy the layout and look, not the official artwork or logos. Build the stylesheet on `systems/sheet.css` (see Styling a sheet in reference.md), and look at the result: a sheet with only colours set looks nothing like the paper one.
3. Define one `system` at the top level, and point `characters`, `creatures` and every name in `secondaryTypes` at a `ruleset`.
4. Register a new system (or extension) in `rules.json`. If it has `nameSettings`, list the same setting names there as `"nameSettings"`.
5. For names, add the files from `names/` that fit the setting to `libraries`, and pick or write `nameSettings` (see [Name generators](reference.md#name-generators)).
6. Write a play guide, `guide.md` next to the system's files, and point to it with `"guide"` in the system's (or extension's) `rules.json` entry. It tells an AI gamemaster how to play: how rolls are judged, combat, damage and healing, and which sheet fields matter. Use your own words, and keep it short. The MCP's `get_rules` tool serves it.
7. Validate by parsing (see below). Fix and repeat until it passes.

## Validate

The Elm test suite parses every system listed in `rules.json`, resolving `#include`s, and reports the line and column of the first parse error:

```bash
cd /home/jarl/Development/fudger2/Web && ./test.sh tests/RulesCorpusTests.elm
```

For name generators and settings, also run `./test.sh tests/NameLibrariesTests.elm tests/NameSettingsTests.elm`. They make names for every variant of every file in `names/`, check that every setting points at a `Names` item and variant the system ships, and that `rules.json` lists the same settings.

The test lives in the fudger2 app repo, runs in Docker, and reads this repo's `systems/` by default (override with `RULES_DIR`). To check a draft without touching `rules.json`, copy `common.frules` and the draft into a scratch folder laid out like `systems/` with its own `rules.json`, and point `RULES_DIR` at it. Includes are resolved by path starting with `/systems/`, so keep the same paths.

From a nested worktree, the test can't find the rules on its own: set `RULES_DIR` to the worktree's `systems/`.

For a built-in library, `python3 tools/check_library.py <system>.frules <library>.json` checks that every item names a type and ruleset the system has, and that every table and field it fills in exists. Libraries made by a script in `tools/` (`srd2024.py`, `cepheus_import.py` and the `*_import.py` files) are fixed in the script and regenerated, not edited by hand.

To see a sheet, `~/claude-sheet-preview/render.py /systems/<system>/<file>.frules [characters|creatures]` renders it headless to a PNG in `~/claude-sheet-preview/shots/`. It reads the main checkout in `/home/jarl/Development/fudger2-rules`, not a worktree, and needs its server on 127.0.0.1:8766.

Rules that use an engine feature not yet in production need the app deployed first. Say so in the commit message.

Parsing only proves the syntax. Names that don't resolve and values of the wrong type fail silently at runtime (a blank cell, `0`, or "X not supported"), so double-check every reference against the table it points to.

## Gotchas that break files

- **No comments.** The language has no comment syntax. Don't add any.
- **No `#include` text in strings**, and put every `#include` at the top of the file. The include resolver looks for `#include` anywhere in the file. Other `#` characters, such as colours like `"#d64545"`, are fine.
- **Bare names are letters and digits only.** No `_` or `-`. Anything else needs single quotes: `'Very hurt'`. Quoted names allow only letters, digits and spaces.
- **Strings use double quotes and have no escapes.** A string can't contain `"`. Backslashes are kept as-is, which is handy for regexes.
- **Operators:** `+ - * /`, `==`, `!=`, `>`, `<`, `>=`, `<=`, `and`, `or`, and the functions `not`, `mod` and `abs`. These need the app from branch `claude/rpg-engine-features` or later. `if` and `switch` always need `else`.
- **Every function is called as `f (a, b)`**, including the built-in `max` and `min`.
- **A call at the top level must have its `(` on the same line as the function name.** Inside parentheses, newlines are fine.
- **Same-named definitions merge.** Two `characterTable = ruleset {...}` blocks combine their fields, and two lists concatenate. This is how extensions and multi-file systems add to a base system, but it also means an accidental duplicate name silently merges.
- **Don't name a parameter after a field option it sets.** In `strike (reach) = custom { Hit = modifier { reach = reach } }` or `roll (sides) = ([dice { sides = sides }], ...)` the name on the right means the option itself, and the sheet or the roll loops forever. Use another name, such as `reachFeet` or `dieSize`.
- **`otherLibararyTypes` is spelled with the typo.** The code reads that exact name.
- **Don't add to a shared name setting.** Merging into `fantasyNameSetting` from one system would change it for all of them, and its lists would add up. Write your own `nameSetting` instead.
- **Name generators are JSON, not frules.** `#` and quotes are fine there, and names must be original, not taken from published settings.
- **`toInt` of text with a unit is `0`.** `toInt ("30 m")` and `toInt ("Range 80")` both give 0, so ranges read that way silently become "next to the target". Take the first number with `firstNumber (text) = bonusWithValue ([[text]], "^[^0-9]*([0-9]+)")`.
- **A dice group with no dice still shows its label.** For an optional extra die (advantage, a bonus or penalty die), give the group `label = ""` when it is off, or chat names the wrong mode. Its `rolls` is then empty, so check `count (rolls) == 0` before reading `first`.
- **Only `custom` and `table` work as parameterless field types.** `attr = custom { ... }` used as `Str = attr {}` is fine, but `die = string { ... }` or `stat = modifier { ... }` used the same way draws "string not supported". Write those fields out, or make them a field template with a parameter.
- **A roll's dice list must be literal in the roll pair.** `([dice {...}, dice {...}], lambda)` parses; a function that returns the dice list does not. Put the choices in the dice' `number` and `sides` instead, and use one roll function with flags.
- **Don't define `testRoll` or `testValue`.** The tests in the app add those names to the system, and a same-named function merges with them.
- **Quoted names can't hold `-`, `(` or `)`.** `'Flat-footed'` and `'Dmg (M)'` fail to parse, and the error points at the start of the ruleset, not the field.
- **Ship types are called `Spaceships`.** Name generators offer ship names to the `Spaceships` kind, so an extra entity type called Starships gets no ship names.
