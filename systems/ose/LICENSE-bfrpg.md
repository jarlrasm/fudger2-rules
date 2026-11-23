# Basic Fantasy content

`bfrpg.json` contains monsters, spells, weapons, armour and equipment from the *Basic Fantasy Role-Playing Game Core Rules*, 4th edition (release 128), Copyright © 2006-2023 Chris Gonnerman, licensed under the Creative Commons Attribution-ShareAlike 4.0 International licence (https://creativecommons.org/licenses/by-sa/4.0/). The original is free at https://www.basicfantasy.org.

The text comes from the Quarto edition at https://github.com/jmhimara/bfrpg and was converted with `tools/bfrpg_import.py`. The changes: monster Armor Class is converted from ascending to descending Armour Class, THAC0 and average hit points are worked out from the Hit Dice, saving throws are abbreviated (Fighter: 4 becomes F4), and the text is reformatted. Under the ShareAlike terms, `bfrpg.json` is licensed under CC BY-SA 4.0 too.

Basic Fantasy is a different game from Old-School Essentials, and this library is not affiliated with Necrotic Gnome or with the Basic Fantasy project.

`Basic-Fantasy-RPG-Rules-r142-text.pdf` is the *Basic Fantasy Role-Playing Game Core Rules*, 4th edition, release 142, Copyright © 2006-2025 Chris Gonnerman, with every raster image removed (with Ghostscript's `-dFILTERIMAGE`). The book's text, maps, floorplans, diagrams, charts and forms are licensed under CC BY-SA 4.0, but most of its artwork belongs to the original artists and may not be redistributed, so it has been taken out; any raster maps and diagrams went with it. Nothing else was changed. Under the ShareAlike terms this PDF is also licensed under CC BY-SA 4.0. The library's items link to its pages (`tools/pdf_references.py`, with the monster headings from `tools/bfrpg_import.py`). The library's text is from release 128 and may differ slightly from release 142.
