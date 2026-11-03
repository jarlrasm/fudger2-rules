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

Built-in references: `character`, `campaign`, `live`, `editor`, `none` (used as option values), `secondary` (the entity's attached library items), `library` (the campaign library).

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
| `cssFiles` | Extra stylesheets |
| `description` | Text shown for the system |

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
```

- `valueType = nameAndDescription`: name plus description rows.
- `valueType = custom { fields }`: one column per field.
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
  "image": "/systems/Fudge/fudge.jpeg",
  "description": "Simple Fudge rules",
  "extensions": [
    { "name": "Spells", "location": "/systems/Fudge/extensions/spells.frules", "description": "Simple rule-less spells" }
  ]
}
```

A large system can be split into files that the entry file pulls in with `#include` (see `DND/DND.frules`). Each file can add to `characterTable` and the merge puts it together.

## Library data

`library.'TypeName'` is a list of `{ name, data }` for every library item of that type in the campaign. `data` holds the item's ruleset values, e.g. `x.data.classStats.Stats.HitDie`. See `DND/Generated/CharacterClasses.frules` for turning library items into records with `map`.
