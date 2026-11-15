# Playing D&D 5e

These rules follow the System Reference Document 5.2.1, which is in the built-in library as a PDF.

## Checks
Roll 1d20, add a modifier, and compare with a Difficulty Class (DC): 5 very easy, 10 easy, 15 medium, 20 hard, 25 very hard, 30 nearly impossible. Meeting the DC succeeds.

- **Ability checks** use the ability's modifier from Ability scores, plus the proficiency bonus when the character is proficient in the skill.
- **Saving throws** resist harm and use the Saving throws on the sheet.
- **Advantage** rolls two d20 and keeps the higher, **disadvantage** keeps the lower. Use the Roll selector on the sheet, or hold Shift or Ctrl when rolling.

## Combat
1. Call initiative. Everyone rolls d20 plus Dexterity modifier, and turns go from highest to lowest.
2. On a turn a creature can move up to its Speed and take one action (Attack, Dash, Dodge, Disengage, Help, Hide, Ready, Cast a spell, Use an object), and possibly a bonus action.
3. An attack rolls d20 plus the attack bonus against the target's Armor Class. A natural 20 is a critical hit and doubles the damage dice. A natural 1 always misses.
4. Damage comes off Hitpoints (Current). At 0 hit points a character falls unconscious and makes death saving throws. A creature usually dies.

Battlemap squares are 5 feet, so a Speed of 30 ft is 6 squares.

## Movement
Speed on the sheet is in feet per turn, usually 30 ft for characters. With 5 ft squares that is Speed ÷ 5 squares (6 for 30 ft).
- Movement can be split around the action, such as moving 10 ft, attacking, then moving 20 ft.
- The Dash action gives the Speed again, so 12 squares for 30 ft.
- Difficult terrain costs 2 squares of movement per square.
- Standing up from prone costs half the Speed. Climbing and swimming cost double, unless the creature has a climb or swim speed.
- Leaving a square next to an enemy lets it make an opportunity attack, unless the mover takes Disengage.
- Diagonals count as one square (5 ft).

## Equipment
Weapons, armour and other items have an Equipped box, ticked when they are added. Only equipped items count: Armour Class uses the best equipped armour, Attacks lists equipped weapons, and bonuses written in a description (such as a Shield's +2 AC or a +1 weapon) apply only while the item is equipped. Untick armour the character takes off to sleep, or a weapon left behind, instead of removing it.

## Rests
A short rest lets a character spend hit dice to heal. A long rest restores all hit points and most resources.

## Creatures
Creatures have a Challenge rating. A fair fight for four characters is about one creature of their level, or several weaker ones. The built-in library has the SRD monsters, spells and equipment. Use them with library_items in create_encounter.
