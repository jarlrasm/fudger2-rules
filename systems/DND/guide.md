# Playing D&D 5e

These rules follow the System Reference Document 5.2.1, which is in the built-in library as a PDF.

## Checks
Roll 1d20, add a modifier, and compare with a Difficulty Class (DC): 5 very easy, 10 easy, 15 medium, 20 hard, 25 very hard, 30 nearly impossible. Meeting the DC succeeds. Each check and save asks for the DC, and each attack for the target's AC. Leave it blank when only the GM knows it, and the roll shows just the total.

- **Ability checks** use the ability's modifier from Ability scores, plus the proficiency bonus when the character is proficient in the skill.
- **Saving throws** resist harm and use the Saving throws on the sheet.
- **Advantage** rolls two d20 and keeps the higher, **disadvantage** keeps the lower. Use the Roll selector on the sheet, or hold Shift or Ctrl when rolling.

## Combat
1. Call initiative. Everyone rolls d20 plus Dexterity modifier, and turns go from highest to lowest.
2. On a turn a creature can move up to its Speed and take one action (Attack, Dash, Dodge, Disengage, Help, Hide, Ready, Cast a spell, Use an object), and possibly a bonus action.
3. An attack rolls d20 plus the attack bonus against the target's Armor Class. A natural 20 is a critical hit and doubles the damage dice. A natural 1 always misses.
4. Damage comes off Hitpoints (Current). At 0 hit points a character falls unconscious and makes death saving throws. A creature usually dies.

Battlemap squares are 5 feet (1.5 m), so a Speed of 30 ft (9 m) is 6 squares. New maps start at 5 ft a square, or 1.5 m in a campaign whose Distances setting is m. Reach and range follow the map's unit either way.

## Movement
Speed on the sheet is per turn, usually 30 ft (9 m) for characters. The campaign's Distances setting picks feet or metres for the sheet's Speed and creature reach. With 5 ft squares that is Speed ÷ 5 squares (6 for 30 ft).
- Movement can be split around the action, such as moving 10 ft, attacking, then moving 20 ft.
- The Dash action gives the Speed again, so 12 squares for 30 ft.
- Difficult terrain costs 2 squares of movement per square.
- Standing up from prone costs half the Speed. Climbing and swimming cost double, unless the creature has a climb or swim speed.
- Leaving a square next to an enemy lets it make an opportunity attack, unless the mover takes Disengage.
- Diagonals count as one square (5 ft).

## Equipment
Weapons, armour and other items have an Equipped box, ticked when they are added. Only equipped items count: Armour Class uses the best equipped armour, Attacks lists equipped weapons, and bonuses written in a description (such as a Shield's +2 AC or a +1 weapon) apply only while the item is equipped. Untick armour the character takes off to sleep, or a weapon left behind, instead of removing it.

## Levels and subclasses
Most classes pick a subclass at level 3, under Subclass in the Class block. The list has the subclasses for the class in the campaign's libraries. Custom lets the player name their own subclass and write its features under Custom subclass features. GMs can add more subclasses as Subclasses library items, each naming its class.

The Leveling block appears when the character is owed something: XP enough for a new level, a subclass to choose, or feats to pick. Feats come from the origin feat of the background, Human's Versatile trait, and class and subclass levels (Ability Score Improvement, Fighting Style and Epic Boon count as feats). In the editor it also reminds the player which ability score increases they have, and which features the current level gave.

## Spells
Spell attacks under Spells lists every spell the character knows that makes a spell attack, rolling the spell attack bonus. Spell saves lists the spells that call for a saving throw, with the ability and the save DC: the target rolls that save. Both can be used on a token within the spell's range (Touch is 5 ft, Self has no limit). Damage and effects are in the spell's description.

## Conditions
Tick conditions under Conditions on characters and creatures, and Effects sums up what they do. Set conditions, Exhaustion, Concentrating and Down (0 hit points) also show as badges on the battlemap token, and the gamemaster can set or clear them there too. Exhaustion counts from 0 to 6: each level gives -2 to every d20 roll on the sheet and -5 ft Speed, and 6 is death. Write the spell being concentrated on under Concentration, and clear it when the caster takes damage and fails a Constitution save (DC 10 or half the damage, whichever is higher), is incapacitated, or casts another concentration spell. Heroic Inspiration under Basics lets the player reroll one die and use the new result.

## Rests
A short rest lets a character spend hit dice to heal. A long rest restores all hit points and most resources, and removes one level of Exhaustion.

## Money
Coins under Equipment counts copper, silver, electrum, gold and platinum pieces. 10 cp = 1 sp, 10 sp = 1 gp, 2 ep = 1 gp and 10 gp = 1 pp.

## Creatures
Creatures have a Challenge rating and an XP value. A fight's difficulty comes from an XP budget: each character adds a budget for Low, Moderate and High by their level (at level 3: 150, 225 and 400), and the creatures' XP is spent against it. More than the High budget is Deadly. create_encounter and get_entity on an encounter give this rating as difficulty, and the gamemaster sees it on the encounter page. The built-in library has the SRD monsters, spells and equipment, including adventuring gear, tools, mounts and vehicles, and the SRD magic items with their rarity and attunement (filter Other items by Category or Rarity). Use them with library_items in create_encounter.
