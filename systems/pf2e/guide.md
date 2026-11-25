# Playing Pathfinder 2nd edition (Remaster)

## Rolling
A check is **d20 + modifier** against a DC. The modifier is an attribute modifier plus a proficiency bonus (Trained 2, Expert 4, Master 6, Legendary 8, each plus the character's level; Untrained adds nothing) plus item and circumstance bonuses, minus penalties. Each check asks for the DC (Strikes ask for the target's AC) and names its degree of success. Leave it blank when only the GM knows it, and the roll shows just the total.

- **Four degrees:** beat the DC by 10 or more for a **critical success**; meet it for a **success**; miss it for a **failure**; miss it by 10 or more for a **critical failure**. A natural 20 moves the result one degree up, a natural 1 one degree down.
- **Fortune** rolls twice and keeps the higher, **misfortune** the lower (Shift and Ctrl).
- Frightened and sickened values come off every check automatically, and off-guard takes 2 from AC.
- Typical DCs by level: 15 at level 1, 20 at level 5, 27 at level 10, 34 at level 15, 40 at level 20. Simple DCs: trained 15, expert 20, master 30, legendary 40.

## Encounters
A fight's threat comes from an XP budget for four characters: Trivial 40, Low 60, Moderate 80, Severe 120 and Extreme 160, with 10, 20, 20, 30 and 40 more or less for each character above or below four. A creature of the party's level costs 40 XP, from 10 at four levels below to 160 at four levels above. create_encounter and get_entity on an encounter give this rating as difficulty, and the gamemaster sees it on the encounter page.

Roll **Initiative** (usually Perception) to join the tracker. Each turn has **three actions** and one reaction.

1. **Strike** with a weapon from the Strikes list. The second Strike in a turn takes the **multiple attack penalty** (−5, or −4 for agile weapons), the third −10 (−8): pick 2nd or 3rd on the Attack slider before rolling.
2. A critical hit doubles the damage.
3. At 0 HP a creature falls **unconscious** and gains **dying 1** (dying 2 from a critical). Each turn it makes a recovery check (flat DC 10 + dying). At dying 4 it dies. Recovering from dying adds 1 to **wounded**, which adds to dying next time.
4. **Hero Points**: spend one to reroll a check, or all of them to avoid death.

## Exploration and downtime
Outside encounters, characters choose exploration activities (Scout, Search, Avoid Notice and so on). Resting 8 hours restores HP equal to CON modifier × level and refreshes spells.

## Style
Heroic fantasy with tactical fights. Teamwork matters: flanking, helping, and setting up allies for critical hits.
