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

1. Read `rules.json` and a similar existing system. Learn the game from its rules (an SRD or quickstart where there is one), not from memory: how a roll is read (sum, pool, roll-under, ladder), what counts as a critical, how damage and healing work, how initiative goes, and what a creature's stat block holds. Note what is open content and under which licence before planning libraries or PDFs (see [Licences](reference.md#licences-and-credits)).
2. Write the file(s). Start with `#include "/systems/common.frules"` if you need `compare`, `nameAndDescription` or `entityTypeDescription`. Make each sheet look similar to the game's official character sheet: the same sections in the same order and places, the same field names and groupings, and a similar feel (colours, fonts, borders) through custom CSS where the system has it. A player who knows the paper sheet should find things where they expect them. Copy the layout and look, not the official artwork or logos. Build the stylesheet on `systems/sheet.css` (see Styling a sheet in reference.md), and look at the result: a sheet with only colours set looks nothing like the paper one.
3. Define one `system` at the top level, and point `characters`, `creatures` and every name in `secondaryTypes` at a `ruleset`.
4. Register a new system (or extension) in `rules.json`, with `tags` and, when it ships open content, `credits` (see [The rules.json entry](reference.md#the-rulesjson-entry)). If it has `nameSettings`, list the same setting names there as `"nameSettings"`.
5. For names, add the files from `names/` that fit the setting to `libraries`, and pick or write `nameSettings` (see [Name generators](reference.md#name-generators)).
6. Write a play guide, `guide.md` next to the system's files, and point to it with `"guide"` in the system's (or extension's) `rules.json` entry. It tells an AI gamemaster how to play: how rolls are judged, combat, damage and healing, and which sheet fields matter. Use your own words, and keep it short. The MCP's `get_rules` tool serves it.
7. Validate by parsing (see below). Fix and repeat until it passes.
8. Test the rolls and sheets in the app's `tests/NewSystemsTests.elm` (see [Test rolls](#test-rolls)), and render both sheets to look at them.
9. Write a sample character and make the sheet image shown in the create campaign dialog (see [Sheet image](#sheet-image)).
10. Go through the checklist below.

## Checklist for a complete system

A system that only parses is a draft. Before calling it done, check each of these, or say why the game has none:

- **Both sheets.** `characters` laid out like the official sheet; `creatures` like the book's stat block, compact, with only what a GM needs at the table. Extra entity types (ships, vehicles, factions) where the game has sheets for them.
- **Every roll does what the game does**, with outcome words, criticals, margins or successes in the result, `ask` for difficulties only the GM knows, and `Push` where the game lets you reroll (see [Results](reference.md#results-with-an-outcome-and-pushing)).
- **Initiative**: a rolled `Initiative` field, `initiativeDeck` for card initiative, or `initiativeRolls`, and `initiativeCompare` in the game's order.
- **Battlemap actions** for every attack, with `reach` and `range` in the system's `distanceUnit`, and `squareSize` where the game uses a grid.
- **Indicators** for conditions, wounds and down states, in the shared colours.
- **`important`** in each ruleset's `rulesetConfiguration`: what the GM needs in the session sidebar.
- **`editable = live`** on everything that changes in play (HP, stress, conditions, ammo, resources), and a heal or reset `button` where the game has rests.
- **Library types** in `secondaryTypes` for the game's gear, spells, powers or moves, with `filters` and `sortedBy`, and a built-in library of open content where the licence allows (check it with `tools/check_library.py`).
- **`quickdice`** with the game's dice, **`hints`** for the create campaign dialog, and **`guide.md`**, kept in step with each other.
- **Name settings** that fit the world.
- **`description`** on main stats, and `reference` only to pages you have checked in a shipped PDF.
- **A sheet image**: `sheet-sample.json` with a believable character, and the `sheet.webp` and `"sheetImage"` the app's `sheet-image.py` makes from it.

## Test rolls

Parsing doesn't show that a roll gives the right result. The app's `Web/tests/NewSystemsTests.elm` has one `describe` per system, built from helpers that load a system from the corpus:

```elm
describe "Vaesen"
    [ sheetsDraw vaesen [ "characters", "creatures" ]
    , rollShows vaesen "vaesenRoll (3)" 0 [ [ 6, 2, 6 ] ] "2 successes"
    , offersPush vaesen "vaesenRoll (2)" 0 [ [ 1, 2 ] ] True
    , askedShows pf1e "pf1Attack (19)" 5 15 [ [ 19 ] ] "24 vs AC 15: Critical threat"
    , valueIs vaesen "characterTable.Skills.Agility.Pool" (Number 3)
    ]
```

- `sheetsDraw` fails on any "not supported" cell, which catches field types and references that parse but don't render.
- `rollShows location expression baseline throws expected` rolls an expression as if each dice group came up with the given numbers, one list per group, and compares the result's text. `askedShows` adds the asked number, `unsetShows` leaves it unset, and `asks` checks the prompt's label.
- `offersPush` and `pushSets` check the push button and the sheet changes it makes. `valueIs` checks a computed value on a fresh character.
- Buttons are tested in `Web/tests/RestButtonsTests.elm`: `clicks location entityType before buttonName expected` sets the `before` values, clicks the button in the play view, and checks the updates it sends.

Test the edges the game cares about: a critical, a fumble, exactly the target, zero dice, an empty optional group, and a push after a partial success. The expression is added to the system as `testRoll` or `testValue`, so those names are taken. Add the system's location as a constant next to the others. Run it with `./test.sh tests/NewSystemsTests.elm`, with `RULES_DIR` from a worktree. The tests are app-repo commits, on their own branch.

Give the main stats a `description` (hover text). Give them a `reference` only where you have checked the page in a PDF the system ships: `python3 -I tools/sheet_references.py <book>.pdf "Heading@first-last" ...` prints the pages where a heading stands on its own line. Don't write page numbers from memory. If many fields share one page, put the reference on their section only.

## Sheet image

The create campaign dialog shows a picture of each system's character sheet, filled in, next to the system list. It comes from `sheet-sample.json` next to the system's rules, drawn by the app's `Web/sheet-image.py`, which writes `sheet.webp` beside the sample and sets `"sheetImage"` in the system's `rules.json` entry. Commit all three.

```bash
cd /home/jarl/Development/fudger2/Web
./sheet-image.py --rules <worktree>/systems --dump <folder>     # the fields to fill in
./sheet-image.py --rules <worktree>/systems <folder> ...        # draw these systems
./sheet-image.py --rules <worktree>/systems                     # redraw every system with a sample
```

A system is named by its folder in `systems/` or its `rules.json` name. The sample sets values the way the MCP's `create_entity` does, with the names `--dump` (and `describe_sheet`) list. Nested objects and dotted names both work, enums by name, rows as lists:

```json
{
  "values": {
    "Investigator": { "Occupation": "Journalist", "Age": 34 },
    "Characteristics": { "STR.Value": 45, "INT.Value": 80 },
    "Other Skills": { "Photography": { "Value": 45 } },
    "Talents": [ { "Name": "Stealthy", "Description": "Once per day, become invisible." } ]
  },
  "secondary": {
    "Weapons": [ { "name": "Longsword" }, { "name": ".32 Revolver", "values": { "Stats": { "Damage": "1d8" } } } ]
  }
}
```

- `secondary` adds library items by type. An item named as in the system's built-in library takes its data from there, and its `values` change that data. Other items are built from their `values` alone.
- Values are set one at a time, in the sample's order, so set a field before the ones whose choices depend on it (DnD's class before its subclass).
- A value the sheet doesn't have, or that is out of range, stops that system with the error. So does a sheet that doesn't draw; the page's console errors are printed with it.

Make the character believable for the game: a real class or career at a low-to-middle level, stats that add up, skills that fit, a few wounds or spent resources, gear from the built-in library, and short lines of background in the game's voice. Fill every section a player would fill; leave computed fields alone. Then read the picture, at least the top and anything that looks empty, like any rendered sheet.

## Validate

The Elm test suite parses every system listed in `rules.json`, resolving `#include`s, and reports the line and column of the first parse error:

```bash
cd /home/jarl/Development/fudger2/Web && ./test.sh tests/RulesCorpusTests.elm
```

For name generators and settings, also run `./test.sh tests/NameLibrariesTests.elm tests/NameSettingsTests.elm`. They make names for every variant of every file in `names/`, check that every setting points at a `Names` item and variant the system ships, and that `rules.json` lists the same settings.

The test lives in the fudger2 app repo, runs in Docker, and reads this repo's `systems/` by default (override with `RULES_DIR`). To check a draft without touching `rules.json`, copy `common.frules` and the draft into a scratch folder laid out like `systems/` with its own `rules.json`, and point `RULES_DIR` at it. Includes are resolved by path starting with `/systems/`, so keep the same paths.

From a nested worktree, the test can't find the rules on its own: set `RULES_DIR` to the worktree's `systems/`.

For a built-in library, `python3 tools/check_library.py <system>.frules <library>.json` checks that every item names a type and ruleset the system has, and that every table and field it fills in exists. Libraries made by a script in `tools/` (`srd2024.py`, `cepheus_import.py` and the `*_import.py` files) are fixed in the script and regenerated, not edited by hand.

`Web/sheet-image.py` (see [Sheet image](#sheet-image)) also renders a sheet from a worktree. An older preview: `~/claude-sheet-preview/render.py /systems/<system>/<file>.frules [characters|creatures]` renders it headless to a PNG in `~/claude-sheet-preview/shots/`. It reads the main checkout in `/home/jarl/Development/fudger2-rules`, not a worktree, and needs its server on 127.0.0.1:8766. `~/claude-sheet-preview/all.py <system>/<file> ...` renders several at once. The preview predates asked rolls and shows them as plain numbers, so check those in the tests instead. Read the PNG: look for empty blocks, cut-off text, rows that don't line up, and a layout that doesn't match the paper sheet.

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
- **An `editable = live` field shows an input, not a roll button.** Keep the stored number editable and put the roll on a separate computed field next to it (`Roll = modifier { value = Current  valuedice = ... }`).
- **`description` must be a literal string.** The app doesn't evaluate it, so a field template's description can't depend on its parameters; give a shared template generic text, or put per-key text in the section's `descriptions`.
- **Button targets must match how the field is stored.** Integers, strings and bools are stored at `(root.Table.Field)`, slots and clocks at `(root.Table.Field.realvalue)`, and keyvalues rows at `(root.Table.Key.Field)`. A radio-group bool also stores the picked name under the group: set `(root.Table.group)` too. List rows can't be targets. Use `root.` paths, and add `editable = live` so the button shows in play.
- **One button update per line.** Inside `updates { }`, a value that ends in a bare name followed by the next target on the same line, `(a) = 'Max HP'  (b) = 0`, parses as a call `'Max HP' (b)`, and the second update is lost.
- **A bool read by a rule needs `default = false`.** An unset bool without a default has no value to read, so a button that copies it stores nothing useful.
- **Ship types are called `Spaceships`.** Name generators offer ship names to the `Spaceships` kind, so an extra entity type called Starships gets no ship names.
