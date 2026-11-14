# frules language reference

Source of truth, in the fudger2 app repo at `/home/jarl/Development/fudger2`: `Web/GameSystemParser/src/GameSystemParser.elm` (syntax), `Expressions.elm` (evaluation and built-ins), `SystemMapper.elm` (merging), and `Web/src/Sheet/{Entity,View,Editor}.elm` (what each type renders as). If something here disagrees with the code, the code wins.

## File structure

A file is a list of assignments. Nothing else is allowed at the top level except `#include` lines.

```
#include "/systems/common.frules"

name = value
functionName (a, b) = expression
TypeName = constructor { field = value  other = value }
```

- `#include "/systems/path.frules"` splices that file's text in place. Paths are absolute from the rules server root. Includes can nest.
- Assignments inside `{ }` are separated by whitespace only. No commas, no semicolons.
- Line breaks are free everywhere except between a top-level function name and its `(`.

## Names

- Bare: letters and digits, e.g. `Str`, `characterTable`, `HitDie`.
- Quoted: `'Very hurt'`, `'Armor Class'`. Letters, digits and spaces only.
- Field names are what the sheet shows as labels, so use quoted names for anything with spaces.

## Values

| Kind | Syntax |
|---|---|
| Integer | `3`, `-2`, `+6` |
| String | `"Fair"` (no escapes, no `"` inside) |
| Bool | `true`, `false` |
| List | `["a", "b"]`, `[1d20, 1d6]`, `[]` |
| Dice | `1d20`, `2d6+1`, `3d6-2`, `4df` (Fudge dice). Max 50 dice. |
| Reference | `Str`, `Damage.Scratch`, `'Ability scores'.'Con'.Modifier` |
| Constructor | `typeName { assignments }` |

## Expressions

- Arithmetic: `+ - * /` (integer division), parentheses for grouping.
- Comparison: `==`, `>`, `<`. Returns a bool.
- Conditional: `if cond then a else b`. Chain with nested `if`s. `else` is required.
- Switch: `switch value case x then a case y then b else c`. Compares `value` to each case with `==` in order and returns the first match, or the `else` value. At least one `case` and the `else` are required. Cases can go on their own lines:

  ```
  Size = switch Category
      case "small" then 1
      case "medium" then 2
      else 3
  ```
- Function call: `f (a, b)`. A call with one argument is still `f (x)`.
- Lambda: `(x)->x.Name`, `(a, b)->a + b`. Parameters always in parentheses.
- Property access: `expr.field`, works on any record, e.g. `first (list).Name`.

### Defining functions

```
compare (item1, item2) =
    if item1 > item2 then -1 else if item1 < item2 then 1 else 0

boolToVisible (flag) = if flag then visible else none
```

A parameterless assignment like `fudgevalues = ["Terrible", "Poor"]` is a constant.

### Name resolution

A reference is looked up in the current table first, then each enclosing table, then the top level. So inside `Damage = table { ... }`, `Hurt.realvalue` refers to the sibling field, and `'Ability scores'.'Con'.Modifier` inside the character ruleset reaches across to another table. `characterTable` (the ruleset's own name) refers to the whole current entity, which is how DND passes the character into helper functions.

### Built-in functions

| Function | Does |
|---|---|
| `map (fn, list)` | Apply `fn` to each item |
| `filter (fn, list)` | Keep items where `fn` returns `true` |
| `fold (start, (acc, x)->..., list)` | Left fold |
| `sum (list)` | Sum of numbers |
| `max (a, b, ...)`, `min (a, b, ...)` | Largest or smallest number. Arguments can be numbers or lists of numbers: `max (0, hp - damage)`, `max (rolls)`. Missing values are skipped; with no numbers at all the result is 0 |
| `count (list)` | Length |
| `first (list)` | First item |
| `item (n, list)` | Item at index `n` (0-based) |
| `sort (list)` | Sort by number, ascending |
| `reverse (list)` | Reverse |
| `concat (list1, list2)` | Join two lists |
| `contains (text, part)` | `true` if `part` is in `text` |
| `toLower (text)` | Lower case |
| `split (separator, text)` | Split into a list of strings |
| `replace (old, new, text)` | Replace all |
| `toString (n)`, `toInt (text)` | Convert (bad numbers become `0`) |
| `toList (record)` | Record to list of `{Key, Value}` |
| `intValueFromEnumString (values, text)` | Index of `text` in the list `values` |
| `bonusFrom (listOfTextLists, regex, n)` | `n` if any text matches `regex`, else `0` |
| `bonusWithValue (listOfTextLists, regex)` | Sum of the numbers captured by `regex` across all texts |

Built-in references: `character`, `campaign`, `live`, `editor`, `none` (used as option values), `secondary` (the entity's attached library items), `library` (the campaign library), `cards` (the campaign's card decks, see [Card decks](#card-decks)).

From `common.frules`: `compare (a, b)`, `nameAndDescription (name, description)`, `entityTypeDescription (name, singular, forEncounters, image, secondaries)`.

## Dice

A field rolls when it has `valuedice`. The field's value becomes the baseline of the roll.

- Simple: `valuedice = 1d20`. Result is baseline + sum of rolls + dice bonus.
- Custom: a pair of a dice list and a lambda that gets `(baseline, throws)`. Each throw has `rolls` (a list of numbers) and `bonus`.

```
edgeRoll = ([2d6], ((baseline, throws)->
    sum (first (throws).rolls)))

advantage = ([1d20, 1d20], ((baseline, throws)->
    baseline + max (
        first (throws).bonus + sum (first (throws).rolls),
        item (1, throws).bonus + sum (item (1, throws).rolls))))
```

`valuedice` can be any expression, e.g. a function that picks a roll from the character's state (see `D20Roll` in `DND/Basics.frules`).

### Battlemap actions

A field with `action` is an action. In a running battle, whoever has the current initiative can click another token and use it on that token. Chat then shows "Bob used Sword on Orc and rolled 14".

- `action = melee` or `action = ranged`. A plain name and a string (`"melee"`) both work, so a function can pass the kind in as a parameter.
- `reach = <number>`: how far a melee action reaches, in the battlemap's unit (ft or m). Without it the target must be next to the user.
- `range = <number>`: how far a ranged action reaches. Without it there is no limit.
- An out-of-reach action is greyed out for players. The gamemaster can still use it.
- In a list row, the action is named after the row's `Name` and rolls the first rolled field in the row.
- In the sheet's meta view you can tick "Action" on any row or field to make it an action, or untick one the rules made. Those have no range limit, and a field without dice just says "Bob used Rope on Orc".

```
Tohit = modifier { value = tohit  valuedice = D20Roll (characterTable)  action = kind  reach = distance  range = distance }
```

`DND/Attacks.frules` passes `"melee"` with reach 5 (10 for weapons with Reach) or `"ranged"` with the first number after "Range" in the weapon's Properties.

A rolled field named `Initiative` (any case) feeds the encounter initiative tracker. A system that sets `initiativeRolls` (currently only Fudge) makes this a per-campaign list instead: the GM edits it in the campaign settings, starting from the system's list, and any attribute or skill whose name matches (any case) counts. The Call for initiative button then rolls the first enum `keyvalues` entry the character has from that list.

## The system

Exactly one top-level assignment uses the `system` constructor. Its name is the system's name in the app.

```
Fudge = system
{
    characters = characterTable
    creatures = characterTable
    'Ranged weapons' = weaponStats
    Armour = armourStats
    description = "Simple Fudge rules"
    secondaryTypes = ["Ranged weapons", "Armour", "Other items"]
    otherLibararyTypes = ["Classes"]
    extraEntityTypes = [entityTypeDescription ("Spaceships", "spaceship", true, "/systems/starwars/spaceship-entity.png", ["ShipWeapons"])]
    initiativeCompare (item1, item2) = compare (item1, item2)
    quickdice = [1d20, 1d6]
    cssFiles = ["/systems/starwars/starwars.css"]
}
```

| Field | Meaning |
|---|---|
| `characters`, `creatures` | Ruleset for player characters and for creatures (can be the same) |
| other named fields | A ruleset for each library type, keyed by its name |
| `secondaryTypes` | Library item types that can be attached to an entity. Names without a ruleset get just name and description. |
| `otherLibararyTypes` | Library-only types, not attached to entities (typo is required) |
| `extraEntityTypes` | Extra top-level entity types, built with `entityTypeDescription` |
| `initiativeRolls` | Optional. Makes initiative rolls a per-campaign setting with these names as the default, e.g. `["Dex", "Alertness"]`. Leave it out to use the `Initiative` field only. |
| `initiativeCompare (a, b)` | Sort order for initiative. Return `-1`, `0` or `1`. |
| `quickdice` | Dice buttons shown in sessions |
| `cssFiles` | Extra stylesheets, loaded for every campaign of the system. See [Styling a sheet](#styling-a-sheet). |
| `libraries` | Built-in libraries, as paths to JSON files in this repo, e.g. `["/systems/DND/dndsrd2024.json"]`. Every campaign of the system can use their items. |
| `nameSettings` | Optional. Which name generator suggests names for each type, see [Name settings](#name-settings). |
| `description` | Text shown for the system |

### Styling a sheet

A stylesheet in `cssFiles` can restyle the whole app by overriding the colour tokens on `:root` (see `starwars/starwars.css`), and the sheet through these classes:

| Class | On |
|---|---|
| `entityView` | The whole sheet |
| `entityTable` | Each block's wrapper `div`, holding `table > thead th` (the title) and `tbody` |
| `table-<name>` | The same `div`, named after the table: lowercased, spaces to `-`, other characters dropped. `'Ability scores'` is `table-ability-scores`, `'1st Level Spells'` is `table-1st-level-spells`. Nested tables get one too. |
| `wide`, `split2` to `split5` | Blocks with `size = wide` or `columns = N` |
| `namedescription` | Name cells that open a description |
| `slots`, `used`, `unused` | Slot trackers |
| `dicethrow` | Dice roll buttons |

Ship fonts and images next to the stylesheet and refer to them by their `/systems/...` path.

### PDFs

A library can hold PDFs, such as a rulebook, and its items can refer to a page in one. A reference shows on the item and opens the PDF at that page. A built-in library's PDF lives in this repo next to the library JSON file and is referred to by its `/systems/...` path:

```json
{
  "name": "DND SRD 5.2",
  "documents": [{ "key": "srd", "name": "SRD 5.2.1", "url": "/systems/DND/SRD_CC_v5.2.1.pdf", "public": true }],
  "entities": [{ "type": "Spells", "name": "Fireball", "references": [{ "document": "srd", "page": 131 }] }]
}
```

| Field | Meaning |
|---|---|
| `documents[].key` | What references in this library call the PDF |
| `documents[].public` | `true` lets players see the PDF and references to it. The default `false` keeps it for the GM. |
| `references[].page` | Optional: the PDF page to open at, counted from 1 |
| `references[].label` | Optional: text shown with the reference, such as `Stats` |

`tools/srd_references.py` adds `SRD_CC_v5.2.1.pdf` to `dndsrd2024.json` and finds each item's page in it. Run it again after regenerating the library.

### Card decks

Card decks are a library type called `Decks` that every system has, so they need no ruleset. A GM makes decks in their own libraries. A system ships decks by putting them in a built-in library listed in `libraries`. In a running session the GM adds a deck from the library. The server then shuffles it and keeps the draw pile, discard pile, table and each person's hand for the whole campaign.

A deck item in a library JSON file:

```json
{
  "type": "Decks",
  "name": "Deck of Many Things",
  "description": "How to use the deck.",
  "images": {},
  "rulesets": [],
  "cards": [{ "name": "Balance", "text": "What the card does.", "copies": 1, "image": "/uploads/..." }],
  "settings": { "whoDraws": "anyone", "drawTo": "table", "gmSeesHands": true }
}
```

| Field | Meaning |
|---|---|
| `images` | The item's images, `{ "url": "image/png" }`. The main image is the back of every card; with no images the backs show the Fudger logo. |
| `mainImage` | Optional: which of `images` is the main one. Without it the first by URL is. |
| `rulesets` | Always `[]`. Decks need none, but apps from before decks only read items that have it. |
| `cards` | `name` is required. `text` defaults to empty, `copies` to 1. `image` is an optional picture for the card's face. `fullImage: true` makes it cover the whole card, for card art with the name and text in it. |
| `settings.whoDraws` | `anyone` (the default) or `gamemaster` |
| `settings.drawTo` | Where a player's draw goes: `hand` (the default, kept secret) or `table` (face up for everyone) |
| `settings.gmSeesHands` | `true` (the default) lets the GM see every hand. Use `false` for games like poker, where the GM plays too. |

See `systems/DND/manythings.json`.

Each deck has a draw pile, a face-up discard pile, the table, a face-down pile (for folded and burnt cards) and a hand for each person. The GM can deal a number of cards to every player at once.

#### Reading cards in rules

`cards.'Deck name'` is what the person looking at the sheet may see of that deck. The server decides this, so rules never see hidden cards:

| Field | Value |
|---|---|
| `Name` | The deck's name |
| `Draw`, `FaceDown` | Number of cards in the draw pile and in the face-down pile |
| `Table`, `Discard` | Lists of cards, each with `Name` and `Text` |
| `Mine` | The viewer's own hand. On a player's sheet that is the player's hand, but on a sheet the GM looks at it is the GM's. |
| `Hands` | One entry per hand: `Player` (username), `Count`, and `Cards` (empty when the viewer may not see that hand) |

`cards` has no value outside a running session, or before a deck is added. Rules that use it should cope with a missing value. For example, a sheet field for Texas hold'em that passes the hole and community cards to `pokerRank`, a function the system would define itself:

```
'Best hand' = pokerRank(concat(map((c)->c.Name, cards.'Poker'.Mine), map((c)->c.Name, cards.'Poker'.Table)))
```

### Name generators

Name generators are a library type called `Names` that every system has, so they need no ruleset. A d20 button next to the name field of an entity or library item suggests names, and `/name` in the session chat shows names to whoever typed it. A system ships generators by listing their JSON files in `libraries`. The shared ones are in `systems/names/`: `norwegian.json`, `viking.json`, `chinese.json`, `fantasy.json` and `scifi.json`, plus one file per genre setting: `cyberpunk.json`, `gothic.json`, `cosmic.json`, `grimdark.json`, `oldworld.json`, `nightworld.json`, `desert.json`, `barbarian.json`, `wasteland.json`, `weirdwest.json`, `pirates.json`, `samurai.json` (romaji and kanji), `victorian.json`, `bluecollar.json`, `mythicgreece.json`, `arthurian.json`, `egypt.json`, `heroes.json`, `spies.json` and `faerie.json`. A `Names` item in a campaign's own library replaces a built-in one with the same name (any case).

A Names item in a library JSON file:

```json
{
  "type": "Names",
  "name": "Norwegian",
  "description": "Modern Norwegian names.",
  "images": {},
  "rulesets": [],
  "generator": {
    "kinds": ["Person", "Place"],
    "variants": ["Male", "Female", "Farm"],
    "parts": {
      "male": ["Ola:5", "Lars:4", "Magnus", "Håkon"],
      "female": ["Kari:5", "Ingrid", "Silje"],
      "surname": ["Hansen:6", "Olsen", "Haugen"],
      "father": ["Sigurd", "Olav"],
      "farm": { "syllables": [["Hau", "Bak", "Myr"], ["gen", "voll", "rud"]] }
    },
    "templates": {
      "Male": ["{male} {surname}:6", "{male} {farm}:3", "{male} {father|sen}:1"],
      "Female": ["{female} {surname}:6", "{female} {father|sdatter}:1"],
      "Farm": ["{farm}"]
    }
  }
}
```

| Field | Meaning |
|---|---|
| `generator.variants` | The variants a GM picks from, in order. The first is the default. Variants that aren't listed but have templates come after. |
| `generator.templates` | For each variant, a list of templates. One is picked at random, by weight. |
| `generator.parts` | Named parts that templates fill in, see below |
| `generator.kinds` | Optional. What the names are for: `Person` (characters and creatures), `Place` (locations), `Item` (library items), or an entity type name such as `Spaceships`. Without a name setting, the picker offers only the generators whose kinds fit, or all of them when none fit. |
| `generator.scripts` | Optional. Ways of writing the same names, e.g. `["Pinyin", "Characters"]`, or the five languages of `viking.json`. The first is the default. Words then hold one spelling per script, separated by `\|`: `"Wang\|王"`. |
| `generator.joiner` | Optional. Per script, what replaces the spaces in templates, e.g. `{ "Characters": "" }` |

Weights: any word or template can end in `:number`, e.g. `"Ola:5"`. The default is 1, and 0 means never. `{ "v": "Ola", "w": 5 }` works too.

A part is one of:

| Part | Example | Makes |
|---|---|---|
| Word list | `["Ola:5", "Lars"]` | One word, picked by weight |
| Syllables | `{ "syllables": [["Ae", "Syl"], "elfMid", ["ion", "riel"]], "count": [2, 4] }` | A word built from 2 to 4 syllables: the first from the first pool, the last from the last pool, the ones in between from the middle pools in turn. A pool is a list of words or the name of a word part. `count` defaults to the number of pools, at most 12. |
| Pattern | `{ "pattern": "LD-LD" }` | `L` is a random capital letter, `D` a digit, anything else stays as it is: `T4-Q9` |
| Sample names | `{ "markov": ["Gromdak", "Durgash", "Ushnak"], "order": 2, "length": [4, 9] }` | New names that sound like the samples. It learns which letter follows each `order` letters (1 to 4, default 2). `length` defaults to `[3, 12]`. Names that copy a sample are avoided. Use 10 or more samples. |

A template is text with `{part}` slots. Spaces are tidied, so an empty slot leaves no double space. Slot options go after the part name:

| Slot | Meaning |
|---|---|
| `{surname}` | Fill in the part |
| `{father\|sen}` | Add a suffix: `Sigurdsen` |
| `{clan\|cap}`, `{x\|lower}`, `{x\|upper}` | Capitalise, lower case, upper case |
| `{title?}` | Optional: left out half the time |
| `{title?\|cap}` | Options combine |

A slot naming a part that doesn't exist stays in the name as `{part}`, so mistakes show.

GMs can see a preview of every variant when they edit a Names item in a library. The test suite generates names for every variant and script of every file in `systems/names/` and fails on empty names or leftover `{`.

### Name settings

`nameSettings` says which generator a system uses for each of its types. A system with one world has one setting. A system with many worlds has several, and each campaign chooses one when it is created and can switch later in its settings. The first setting is the default. A campaign can also turn name suggestions off.

```
DND = system
{
    libraries = ["/systems/names/fantasy.json", "/systems/names/norwegian.json", "/systems/names/viking.json"]
    nameSettings = [
        nameSetting
        {
            name = "Classic fantasy"
            characters = generator { library = "Fantasy folk" variant = Class.Race }
            creatures = [generator { library = "Fantasy folk" variant = "Monster" }, generator { library = "Fantasy folk" variant = "Orc" }]
            Location = [generator { library = "Fantasy places" variant = "Village" }, generator { library = "Fantasy places" variant = "Tavern" }]
            'Melee weapons' = generator { library = "Fantasy things" variant = "Weapon" }
        },
        nameSetting
        {
            name = "Norse saga"
            characters = [generator { library = "Viking" variant = "Man" }, generator { library = "Viking" variant = "Woman" }]
            Location = generator { library = "Norwegian" variant = "Farm" }
        }
    ]
}
```

- Keys are type names: `characters`, `creatures`, `Location`, `Other`, an `extraEntityTypes` name, or a library type such as `'Melee weapons'`. Library creatures use `creatures`.
- A value is one `generator` or a list. A list shows as buttons in the picker, and the first is chosen when it opens.
- `library` is the name of a `Names` item. It must be in one of the system's `libraries`, or in the campaign's own libraries.
- `variant` is optional and is an expression. It is evaluated against the entity being named, in that type's ruleset, so `Class.Race` gives a D&D dwarf dwarf names. A result that isn't one of the generator's variants, an empty one (a new entity) or a missing `variant` uses the generator's first variant.
- Types a setting leaves out get the generators whose `kinds` fit, as when there is no setting.
- Lists merge, so an extension can add settings with its own `nameSettings = [...]`, listed in its own `rules.json` entry.
- `systems/names/settings.frules` has shared settings (`fantasyNameSetting`, `norseNameSetting`, `modernNorwayNameSetting`, `easternNameSetting`, `spaceNameSetting`, and one per genre file: `neonStreetsNameSetting`, `gothicHorrorNameSetting`, `cosmicHorrorNameSetting`, `grimdarkNameSetting`, `oldWorldNameSetting`, `nightWorldNameSetting`, `desertRealmsNameSetting`, `swordAndSorceryNameSetting`, `wastelandNameSetting`, `weirdWestNameSetting`, `highSeasNameSetting`, `feudalJapanNameSetting`, `gaslightNameSetting`, `blueCollarSpaceNameSetting`, `mythicGreeceNameSetting`, `arthurianNameSetting`, `ancientEgyptNameSetting`, `superheroesNameSetting`, `spyThrillerNameSetting`, `faerieCourtsNameSetting`). Include it and list the ones that fit: `nameSettings = [fantasyNameSetting, spaceNameSetting]`. Define your own setting rather than merging into a shared one, because same-named definitions merge and lists would add up.
- List the same setting names, in order, in the system's `rules.json` entry as `"nameSettings"`. The create campaign dialog reads them from there. For main systems a test fails when the two lists differ.

The campaign stores its choice in its configuration as `names`: `["Norse saga"]` for a setting, `[]` for off. Without it the campaign uses the first setting. An unknown name also falls back to the first.

## Rulesets

`ruleset { ... }` is the sheet for one entity type. Each field is a section of the sheet, normally a `table`, `keyvalues` or `list`.

`rulesetConfiguration = { ... }` (or `= configuration { ... }`) inside a ruleset sets library options:

```
rulesetConfiguration =
{
    defaultImage = "/images/spell.svg"
    sortedBy = sort { prefix = "Level" sort = Stats.level }
    filters = [
        filter { name = "Level" prefix = "Level" filter = Stats.level },
        filter { name = "Type" prefix = "" filter = split (",", Stats.Type) }
    ]
}
```

## Section types

### table

A labelled group of fields, one row per field.

```
Basics = table
{
    tableLayout = layout { columns = 2  rowTitle = hidden  size = wide }
    Fight = integer { default = 0  valuedice = 1d20 }
    Notes = string { multiline = true }
}
```

A field can also be a plain expression (`HitDie = hitDie (Class.Main.Name, Class.Main.Levels)`), which is shown read-only. Tables nest.

### keyvalues

A table where every row has the same value type, and the row names are keys.

```
Attributes = keyvalues
{
    singular = "Attribute"
    editablekeys = campaign
    keys = ["Str", "Dex", "Con", "Int"]
    valueType = enum
    {
        default = "Fair"
        possiblevalues = fudgevalues
        valuedice = 4df
    }
}
```

- `keys`: the starting keys.
- `editablekeys`: who can add or remove keys. `campaign` (the GM, per campaign) or `character` (the player, per character). Leave it out for fixed keys.
- `valueType = enum { default possiblevalues valuedice }`: a value picked from a list. Stored as the index, shown as the text.
- `valueType = custom { fields }`: each key gets those fields as columns.

### list

A list of entries the user adds.

```
Gifts = list { singular = "Gift"  editable = character  valueType = nameAndDescription }

'Melee weapons' = list
{
    source = secondary.'Melee weapons'
    singular = "Melee weapon"
    editable = character
    tableLayout = layout { }
}

Features = list { valueType = custom { Level = integer {}  Name = string {}  Description = string {} } }

Languages = list { singular = "Language"  editable = character  valueType = string }
```

- `valueType = nameAndDescription`: name plus description rows.
- `valueType = custom { fields }`: one column per field.
- `valueType = string`: one line of text per row, stored as a plain list of strings. `singular` is the placeholder. Enter adds the next row, and Backspace on an empty row removes it. Use `valueType = string { multiline = true }` for longer texts with formatting and `autocomplete` suggestions.
- `source = secondary.TypeName`: show library items of that type attached to the entity. Leave out `valueType`.
- `filter = expr`: for secondary lists, only show items where `expr` is true, e.g. `filter = spellStats.Stats.level == 1`.
- `autocomplete = listOfStrings`: suggestions when adding.

### custom

A group of fields shown together in one cell, e.g. a skill with a modifier and a rank.

```
Acrobatics = custom { Modifier = modifier { valuedice = 1d20 } }
```

### Your own section types

Any parameterless assignment that is a table can be used as a type:

```
hitpoints = table
{
    Current = integer { editable = live  default = Max }
    Max = integer { value = maxHitpoints (Class.Main.Name, Class.Main.Levels, 'Ability scores'.'Con'.Modifier)  editable = none }
}

characterTable = ruleset { Hitpoints = hitpoints {} }
```

## Field types

| Type | Options |
|---|---|
| `integer` | `default`, `minvalue`, `maxvalue`, `value` (computed, read-only), `valuedice`, `render` (text shown instead of the number; the editor then shows −/+ buttons around it), `step` (how much each −/+ click changes the stored number, default 1) |
| `modifier` | Like `integer`, shown with a sign (`+2`) |
| `string` | `default`, `multiline = true`, `keys = [...]` (dropdown), `bonus` |
| `bool` | `default`, `radiogroup = "name"` (bools sharing a group act as radio buttons) |
| `selector` | A slider with one position per option. `options = [...]` (the stored text, read with `==`), `default` (an option; unset reads as this), `labels = [...]` (shown text; the first and last sit at the slider ends), `colors = [...]` (`"red"`, `"white"`, `"green"`, `"blue"` or `""`), `hold = [...]` (`"Shift"`, `"Ctrl"`, `"Alt"` or `""`: holding that key picks the option while held). When the selected option is not the default, every dice roll whose dice change because of it is shown in that option's color. Usually `editable = live` and `save = nosave`. Example: `Roll = selector { options = ["Disadvantage", "Normal", "Advantage"] labels = ["Dis", "Normal", "Adv"] colors = ["red", "white", "green"] hold = ["Ctrl", "", "Shift"] default = "Normal" editable = live save = nosave }`, then `if char.Basics.Roll == "Advantage" then ...` |
| `slots` | Checkboxes. `number` (how many), `value` (computed fill), `allowedchange = increase` or `increaseAndClear`, `overflow = allow`, `overflowValue` (what spills into the next track). The stored count is `Name.realvalue`. |
| `button` | `onClick = updates { (Field.realvalue) = expr ... }`. Each line sets the field on the left. Targets are relative to the button's table; start a target with `root.` to reach any table of the entity, e.g. `(root.Hitpoints.Current) = Hitpoints.Max`. |

### Options on any section or field

| Option | Values |
|---|---|
| `editable` | `character` (default; the player edits in the editor), `campaign`, `live` (edited during play), `none` (never) |
| `visible` | `editor` (editor only), `live` (play view only), `none` (hidden), anything else is visible. Can be an expression, e.g. a function returning `visible` or `none`. |
| `tableLayout = layout { }` | `columns` (1 to 5), `rowTitle = hidden`, `size = wide` |
| `singular` | Label for one entry, used on add buttons |

`default` and `value` can reference other fields, e.g. `default = Max`.

## Extensions and multi-file systems

Assignments with the same name at the same level are merged: constructors combine their fields (recursively), and lists concatenate. An extension only needs the parts it adds:

```
Fudge = system { 'Spells' = spellStats  secondaryTypes = ["Spells"] }

spellStats = ruleset { rulesetConfiguration = { defaultImage = "/images/spell.svg" } }

characterTable = ruleset { Spells = list { source = secondary.Spells  singular = "Spell"  editable = character } }
```

Register it under its base system in `rules.json`:

```json
{
  "name": "Fudge",
  "location": "/systems/Fudge/fudge.frules",
  "description": "Simple Fudge rules",
  "extensions": [
    { "name": "Spells", "location": "/systems/Fudge/extensions/spells.frules", "description": "Simple rule-less spells" }
  ]
}
```

A large system can be split into files that the entry file pulls in with `#include` (see `DND/DND.frules`). Each file can add to `characterTable` and the merge puts it together.

## Library data

`library.'TypeName'` is a list of `{ name, data }` for every library item of that type in the campaign. `data` holds the item's ruleset values, e.g. `x.data.classStats.Stats.HitDie`. See `DND/Generated/CharacterClasses.frules` for turning library items into records with `map`.
