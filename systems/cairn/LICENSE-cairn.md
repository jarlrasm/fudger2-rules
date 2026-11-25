# Cairn library licence

`cairn.json` holds the items, spellbooks, relics and monsters of **Cairn 2nd edition** by Yochai Gal.

- Source: https://github.com/yochaigal/cairn, commit 4180f390d62c3f1d0faab17762381f3b5dba3261 (2026-11-19), files `second-edition/players-guide/marketplace.md`, `second-edition/wardens-guide/spellbooks.md`, `second-edition/wardens-guide/reliquary.md` and `second-edition/wardens-guide/bestiary.md`.
- Licence: the project's README states "The full text is licensed under CC-BY-SA 4.0" (https://creativecommons.org/licenses/by-sa/4.0/). The repository's GPL-3.0 licence file covers the website code, not the game text.
- Changes: converted to Fudger library items by `tools/cairn_import.py`. Weapon rows that list several weapons are split into one item each; prices, damage, armor, bulky and petty are moved into fields; each spellbook's quirk is split from its effect; relic charges and recharge conditions are moved into fields; each monster's stat line is split into fields, with the first bullet as its description and all bullets as its traits.
- Attribution: Cairn by Yochai Gal, licensed under CC BY-SA 4.0. This adaptation is shared under the same licence, CC BY-SA 4.0.

Fudger's own rules, sheet and guide for Cairn (`cairn.frules`, `cairn.css`, `guide.md`) are written in our own words and are not part of the converted text.
