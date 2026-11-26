# Mausritter library licence

`mausritter.json` holds the gear, weapons, armour, treasure, magic swords, spells and creatures of the **Mausritter System Reference Document** by Isaac Williams (Losing Games).

- Source: https://mausritter.com/srd/mausritter-srd-2.3.1.md, "Mausritter SRD Version 2.3.1, SRD Last Updated 2026/02/21", fetched 2026-11-26 (SHA-256 06a68c16125dad61d8734725ea123d43e178eae14e53bafd764792853e9a1677).
- Licence: the SRD states "The text of the Mausritter System Reference Document (SRD) is licensed under Creative Commons Attribution 4.0 International (CC BY 4.0)" (https://creativecommons.org/licenses/by/4.0/). The Mausritter book, its illustrations and other material outside the SRD are not covered, and none of it is used here.
- Changes: converted to Fudger library items by `tools/mausritter_import.py`. Weapon classes are split into one item per example weapon; background starting items, tools, light sources, clothing, ammunition, armour, treasure and magic swords become items with their price, slots, usage dots, class and damage in fields; each spell's effect and recharge are moved into fields; each creature's stat block is split into fields, with its attacks as rows, its wants as the description, and its variant table in its notes. The five Condition cards (Exhausted, Frightened, Hungry, Injured, Drained) are written by Fudger in our own words; they are not SRD text.
- Attribution, as the SRD asks:

> This work is based on [Mausritter](https://mausritter.com), a product of Losing Games and Isaac Williams, and is licensed for use under the [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) licence.

Fudger is not an official Mausritter product and is not endorsed by Losing Games or Games Omnivorous. Fudger's own rules, sheet, icons and guide for Mausritter (`mausritter.frules`, `mausritter.css`, the SVG icons and `guide.md`) are written in our own words and are not part of the converted text.
