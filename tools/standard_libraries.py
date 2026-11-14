import json
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "systems"


def entity(system, type_, name, description, implementation):
    return {
        "type": type_,
        "name": name,
        "description": description,
        "rulesets": [{"system": system, "implementation": implementation}] if implementation else [],
    }


def library(name, description, url, entities):
    return {"name": name, "description": description, "url": url, "gamemaster": "", "entities": entities}


def write(path, data):
    json.dump(data, open(f"{ROOT}/{path}", "w"), separators=(",", ":"))


def gifts(pairs):
    return [{"Name": n, "Description": d} for n, d in pairs]


FUDGE_MELEE = [
    ("Unarmed", 0, "Fists, feet and elbows."),
    ("Knife", 1, "Small and easy to hide."),
    ("Club", 1, "A heavy stick or cudgel."),
    ("Short sword", 2, "A light one-handed blade."),
    ("Mace", 2, "A flanged or spiked head on a short haft."),
    ("Spear", 2, "Can be thrown, and keeps a foe at a distance."),
    ("Broadsword", 3, "A heavy one-handed blade."),
    ("Battle axe", 3, "A heavy one-handed axe."),
    ("Greatsword", 4, "Two-handed."),
    ("Polearm", 4, "Two-handed, with reach."),
]

FUDGE_RANGED = [
    ("Sling", 1, "Cheap and light. Hurls stones."),
    ("Thrown dagger", 1, "A balanced blade for throwing."),
    ("Short bow", 2, "Two-handed. Fair range."),
    ("Long bow", 3, "Two-handed. Needs a Good Str to draw."),
    ("Crossbow", 3, "Two-handed. Slow to reload."),
    ("Pistol", 3, "A modern handgun."),
    ("Shotgun", 4, "Two-handed. Deadly up close, poor at range."),
    ("Rifle", 4, "Two-handed. Accurate at long range."),
]

FUDGE_ARMOUR = [
    ("Heavy clothing", 0, "Thick leather or wool. Turns a scratch now and then."),
    ("Leather armour", 1, "Light and quiet."),
    ("Chain mail", 2, "Noisy and heavy, but protects well."),
    ("Plate armour", 3, "Heavy. -1 to Dex-based skills."),
    ("Shield", 1, "Adds to defence while held."),
    ("Kevlar vest", 2, "Modern body armour. Best against bullets."),
]

FUDGE_ITEMS = [
    ("Rope", "Fifteen metres of hemp rope."),
    ("Torch", "Burns for about an hour."),
    ("Lantern", "Burns a flask of oil for several hours."),
    ("Healing kit", "Bandages and salves. A Good First Aid roll with it heals a Scratch."),
    ("Rations", "A week of dried food."),
    ("Thieves' tools", "Picks and wires for opening locks."),
    ("Backpack", "Holds a fair load of gear."),
    ("Flashlight", "A modern battery torch."),
]

FUDGE_CREATURES = [
    ("Bandit", "A desperate robber who would rather threaten than fight.",
     {"Str": "Fair", "Dex": "Fair", "Con": "Fair", "Int": "Mediocre"},
     {"Sword": "Fair", "Intimidation": "Good", "Stealth": "Fair"}, [], [("Greedy", "Runs when the loot is not worth it.")]),
    ("Guard", "A trained soldier on watch.",
     {"Str": "Good", "Dex": "Fair", "Con": "Good", "Int": "Fair"},
     {"Spear": "Good", "Shield": "Fair", "Perception": "Fair"}, [], [("Bored", "Easy to distract.")]),
    ("Knight", "An armoured warrior of noble birth.",
     {"Str": "Good", "Dex": "Fair", "Con": "Great", "Int": "Fair"},
     {"Sword": "Great", "Riding": "Good", "Etiquette": "Fair"}, [("Noble", "Respected and obeyed by commoners.")], [("Code of honour", "Will not strike an unarmed foe.")]),
    ("Wolf", "A lean grey hunter, usually in a pack.",
     {"Str": "Fair", "Dex": "Good", "Con": "Good", "Int": "Poor"},
     {"Bite": "Good", "Tracking": "Great", "Stealth": "Good"}, [("Keen nose", "Can follow a scent for days.")], []),
    ("Bear", "Huge and short-tempered.",
     {"Str": "Superb", "Dex": "Mediocre", "Con": "Great", "Int": "Poor"},
     {"Claws": "Good", "Bite": "Fair"}, [("Tough hide", "+1 to defence against damage.")], []),
    ("Giant rat", "A rat the size of a dog.",
     {"Str": "Poor", "Dex": "Good", "Con": "Fair", "Int": "Terrible"},
     {"Bite": "Fair", "Stealth": "Good"}, [], [("Cowardly", "Flees when hurt.")]),
    ("Goblin", "Small, sly and nasty.",
     {"Str": "Mediocre", "Dex": "Good", "Con": "Fair", "Int": "Mediocre"},
     {"Spear": "Fair", "Stealth": "Good", "Traps": "Fair"}, [("Darkvision", "Sees in the dark.")], [("Cowardly", "Fights only when the odds are good.")]),
    ("Orc warrior", "A brutal raider.",
     {"Str": "Great", "Dex": "Fair", "Con": "Good", "Int": "Mediocre"},
     {"Axe": "Good", "Intimidation": "Good"}, [("Darkvision", "Sees in the dark.")], [("Bloodthirsty", "Hard to talk down once fighting.")]),
    ("Skeleton", "Old bones stirred to obey.",
     {"Str": "Fair", "Dex": "Fair", "Con": "Good", "Int": "Terrible"},
     {"Sword": "Fair"}, [("Undead", "Feels no pain and needs no air.")], [("Brittle", "Blunt weapons get +1 damage.")]),
    ("Troll", "A towering brute that heals as you watch.",
     {"Str": "Superb", "Dex": "Mediocre", "Con": "Superb", "Int": "Poor"},
     {"Club": "Good", "Intimidation": "Great"}, [("Regeneration", "Heals one wound level each round unless burned.")], [("Hates fire", "Flees from open flame.")]),
    ("Dragon", "An ancient winged serpent. A campaign's worth of trouble.",
     {"Str": "Superb", "Dex": "Good", "Con": "Superb", "Int": "Great"},
     {"Claws": "Great", "Bite": "Great", "Fire breath": "Good", "Lore": "Superb"}, [("Scales", "+3 to defence against damage."), ("Flight", "Flies fast.")], [("Greed", "Cannot resist treasure.")]),
    ("Street thug", "A modern tough with a knife and a grudge.",
     {"Str": "Good", "Dex": "Fair", "Con": "Fair", "Int": "Mediocre"},
     {"Brawling": "Good", "Knife": "Fair", "Streetwise": "Fair"}, [], [("Hot-headed", "Picks fights.")]),
    ("Police officer", "A uniformed officer with a sidearm.",
     {"Str": "Fair", "Dex": "Fair", "Con": "Fair", "Int": "Fair"},
     {"Pistol": "Good", "Brawling": "Fair", "Driving": "Good", "Law": "Fair"}, [("Authority", "People tend to do as told.")], []),
]


def fudge():
    s = "Fudge"
    entities = []
    for name, damage, text in FUDGE_MELEE:
        entities.append(entity(s, "Melee weapons", name, text, {"weaponStats": {"Stats": {"Damage": damage}}}))
    for name, damage, text in FUDGE_RANGED:
        entities.append(entity(s, "Ranged weapons", name, text, {"weaponStats": {"Stats": {"Damage": damage}}}))
    for name, capacity, text in FUDGE_ARMOUR:
        entities.append(entity(s, "Armour", name, text, {"armourStats": {"Stats": {"Damage Capacity": capacity}}}))
    for name, text in FUDGE_ITEMS:
        entities.append(entity(s, "Other items", name, text, None))
    for name, text, attributes, skills, gs, fs in FUDGE_CREATURES:
        entities.append(entity(s, "Creature", name, text, {"characterTable": {
            "Attributes": attributes, "Skills": skills, "Gifts": gifts(gs), "Faults": gifts(fs),
        }}))
    return library(
        "Fudge basics",
        "Weapons, armour, gear and creatures for Fudge, written for Fudger. Damage is the weapon's offensive factor and Damage Capacity the armour's defensive factor. Fudge is a trademark of Grey Ghost Press.",
        "/systems/Fudge/fudge.json", entities)


EDGE_CREATURES = [
    ("Street hustler", "Always has something to sell, and always knows a guy.", "Fast-talking hustler", 4, [("Knows the back alleys", 3)], "Owes money to the wrong people", 2, 4, 2),
    ("Bouncer", "Big, calm and paid to keep trouble outside.", "Huge ex-wrestler", 4, [("Reads a crowd", 3)], "Soft spot for anyone in trouble", 4, 2, 2),
    ("Beat cop", "Underpaid and overworked, with a badge that opens some doors.", "Street cop", 3, [("Handgun", 3), ("Knows every snitch", 3)], "On the take", 3, 3, 2),
    ("Private eye", "Takes cases nobody else wants.", "Dogged investigator", 4, [("Picks locks", 3)], "Cannot let a case go", 3, 3, 2),
    ("Cult acolyte", "Smiling, devoted and much stronger than they look.", "True believer", 4, [("Chants that unsettle", 3)], "Will do anything the leader says", 2, 3, 3),
    ("Cult leader", "Charismatic, patient and half in contact with something else.", "Spellbinding preacher", 4, [("Strange visions", 4), ("Knows everyone's secrets", 3)], "Answers to something worse", 2, 4, 4),
    ("Conspiracy agent", "Dark suit, no name, earpiece.", "Trained operative", 4, [("Never seen twice", 3), ("Pistol", 3)], "Expendable to their masters", 3, 3, 2),
    ("Tourist", "Lost, sunburnt and taking photos of the wrong things.", "Wide-eyed visitor", 2, [("Expensive camera", 3)], "Wandered into something", 2, 2, 2),
    ("Mad scientist", "Brilliant, unwashed and three experiments past ethics.", "Fringe genius", 4, [("Builds odd gadgets", 4)], "Funded by people who want results", 2, 2, 3),
    ("Bodyguard", "Quiet, alert, and between you and the client.", "Close protection pro", 4, [("Spots a threat", 3)], "Loyal to a bad employer", 4, 2, 2),
    ("Street gang member", "Colours, attitude and a crew behind them.", "Gang tough", 3, [("Switchblade", 3)], "Proving themself to the gang", 3, 2, 2),
    ("Psychic", "Hears what people are thinking, whether they want to or not.", "Mind reader", 4, [("Sees glimpses of the future", 3)], "Never sleeps well", 2, 3, 4),
    ("Shapeshifter", "Wears other people's faces.", "Changes shape", 4, [("Mimics voices", 3)], "Forgets who they really are", 3, 3, 4),
    ("Thing from below", "Something that crawled out of the sewers and wants back in.", "Monstrous strength", 4, [("Sees in the dark", 3)], "Driven back by bright light", 4, 1, 4),
]


def edge():
    entities = []
    for name, text, main, main_score, sides, trouble, fight, sway, weird in EDGE_CREATURES:
        entities.append(entity("edge", "Creature", name, text, {"characterTable": {
            "Traits": {
                "Main trait": {main: {"Score": main_score}},
                "Side trait": {n: {"Score": v} for n, v in sides},
                "Trouble": {"Name": trouble},
            },
            "Basics": {"Fight": fight, "Sway": sway, "Weird": weird},
        }}))
    return library(
        "Over the Edge people",
        "Ready-made people and things for Over the Edge, written for Fudger. Scores are dice: 2 is ordinary, 3 good, 4 exceptional. Over the Edge is a trademark of Atlas Games.",
        "/systems/edge/edge.json", entities)


SW_RANGED = [
    ("Hold-out blaster", "3D", "6", "3-4/8/12", "Small and easy to hide."),
    ("Blaster pistol", "4D", "100", "3-10/30/120", "The everyday sidearm."),
    ("Heavy blaster pistol", "5D", "25", "3-7/25/50", "Hits hard but drains its pack fast."),
    ("Sporting blaster", "3D+1", "50", "3-10/30/60", "Light, for hunting and self-defence."),
    ("Blaster rifle", "5D", "100", "3-30/100/300", "Two-handed military weapon."),
    ("Blaster carbine", "5D", "100", "3-25/50/250", "Short rifle for close quarters."),
    ("Light repeating blaster", "6D", "50", "3-50/120/300", "Fires bursts. Needs a bipod or a strong gunner."),
    ("Bowcaster", "4D", "6", "3-10/30/50", "Fires explosive quarrels. Strength 4D to cock."),
    ("Thermal detonator", "10D", "1", "3-4/7/12", "Thrown grenade. Blast radius several metres."),
    ("Stun grenade", "5D stun", "1", "3-7/20/40", "Thrown. Stun damage only."),
    ("Slugthrower rifle", "4D", "8", "3-30/80/200", "Old-fashioned solid-shot rifle."),
]

SW_MELEE = [
    ("Knife", "STR+1D", "Easy to hide."),
    ("Club", "STR+1D", "A stick, pipe or stun-less baton."),
    ("Vibroblade", "STR+3D", "A vibrating blade that cuts through most armour."),
    ("Vibro-axe", "STR+3D+1", "Two-handed vibrating axe."),
    ("Force pike", "STR+2D", "A powered polearm favoured by elite guards."),
    ("Stun baton", "STR+1D stun", "Stun damage only."),
    ("Lightsaber", "5D", "An energy blade. Uses Lightsaber skill; Jedi add Control dice."),
]

SW_ARMOUR = [
    ("Padded flight suit", "+1 physical", "Pilot's suit with life support connections."),
    ("Blast vest", "+1 energy, +1D physical", "Covers the torso."),
    ("Trooper armour", "+2D physical, +1D energy", "Full armour. -1D to Dexterity skills."),
    ("Bounty hunter armour", "+1D+2 physical, +1D energy", "Hand-modified plates."),
    ("Combat jumpsuit", "+1D physical", "Light, padded and cheap."),
]

SW_ITEMS = [
    ("Medpac", "Single-use first aid kit. A First aid roll heals a wound level."),
    ("Comlink", "Personal radio. Range about 50 km, or orbit with a ship relay."),
    ("Macrobinoculars", "Electronic binoculars. +1D to Search at range."),
    ("Glow rod", "A bright hand light."),
    ("Breath mask", "An hour of air in thin or toxic atmospheres."),
    ("Datapad", "A handheld computer."),
    ("Restraining bolt", "Fitted to a droid, it stops the droid from running away."),
    ("Syntherope", "Fifty metres of thin, strong cord."),
    ("Tool kit", "+1D to repair skills."),
    ("Jet pack", "Short flights. Move 100 for a few minutes."),
]

SW_SHIP_WEAPONS = [
    ("Laser cannon", "Starship gunnery", "2D", "1-3/12/25", "100-300/1.2/2.5 km", "5D"),
    ("Twin laser cannon", "Starship gunnery", "2D", "1-3/12/25", "100-300/1.2/2.5 km", "6D"),
    ("Quad laser cannon", "Starship gunnery", "2D", "1-3/12/25", "100-300/1.2/2.5 km", "6D"),
    ("Ion cannon", "Starship gunnery", "1D", "1-3/7/36", "100-300/700/3.6 km", "4D ion"),
    ("Proton torpedo launcher", "Starship gunnery", "2D", "1/3/7", "50-100/300/700", "9D"),
    ("Concussion missile launcher", "Starship gunnery", "1D", "1/3/7", "50-100/300/700", "8D"),
    ("Turbolaser battery", "Capital ship gunnery", "2D", "3-15/35/75", "6-30/70/150 km", "5D capital"),
    ("Tractor beam projector", "Capital ship gunnery", "2D", "1-5/15/30", "2-10/30/60 km", "4D capital"),
]

SW_SHIPS = [
    ("Light freighter", "A battered cargo ship, the first home of many smugglers.",
     {"Type": "Light freighter", "Scale": "Starfighter", "Length": "27 m", "Skill": "Space transports", "crew": 2, "Maneuverability": "1D", "Space": 4, "Atmosphere": "280; 800 km/h", "Hull": "4D", "Shields": "1D", "Hyperdrive": "x2, backup x12"},
     ((10, "1D"), (25, "1D+2"), (40, "2D"), (2, "2D+2"))),
    ("Space fighter", "A fast single-seat fighter.",
     {"Type": "Space superiority fighter", "Scale": "Starfighter", "Length": "12 m", "Skill": "Starfighter piloting", "crew": 1, "Maneuverability": "3D", "Space": 9, "Atmosphere": "415; 1,200 km/h", "Hull": "2D", "Shields": "", "Hyperdrive": ""},
     ((20, "0D"), (40, "1D"), (60, "2D"), (25, "3D"))),
    ("Heavy fighter", "A rugged fighter with shields and a hyperdrive.",
     {"Type": "Multi-role fighter", "Scale": "Starfighter", "Length": "13 m", "Skill": "Starfighter piloting", "crew": 1, "Maneuverability": "2D", "Space": 7, "Atmosphere": "350; 1,000 km/h", "Hull": "4D", "Shields": "1D", "Hyperdrive": "x1"},
     ((25, "0D"), (50, "1D"), (75, "2D"), (3, "4D"))),
    ("Shuttle", "A passenger shuttle with folding wings.",
     {"Type": "Passenger shuttle", "Scale": "Starfighter", "Length": "20 m", "Skill": "Space transports", "crew": 2, "Maneuverability": "0D", "Space": 5, "Atmosphere": "295; 850 km/h", "Hull": "4D", "Shields": "1D+2", "Hyperdrive": "x1"},
     ((20, "0D"), (40, "1D"), (80, "1D+2"), (2, "2D"))),
    ("Bulk freighter", "A slow, huge hauler.",
     {"Type": "Bulk freighter", "Scale": "Capital", "Length": "180 m", "Skill": "Capital ship piloting", "crew": 12, "Maneuverability": "0D", "Space": 2, "Atmosphere": "", "Hull": "2D", "Shields": "", "Hyperdrive": "x3"},
     ((10, "0D"), (25, "1D"), (40, "1D"), (2, "1D"))),
    ("Patrol cutter", "A system patrol ship for customs and police.",
     {"Type": "Patrol ship", "Scale": "Starfighter", "Length": "35 m", "Skill": "Space transports", "crew": 4, "Maneuverability": "2D", "Space": 6, "Atmosphere": "330; 950 km/h", "Hull": "4D", "Shields": "2D", "Hyperdrive": "x2"},
     ((30, "1D"), (60, "2D"), (90, "2D+1"), (4, "3D"))),
    ("Light cruiser", "A small warship.",
     {"Type": "Light cruiser", "Scale": "Capital", "Length": "300 m", "Skill": "Capital ship piloting", "crew": 800, "Maneuverability": "1D", "Space": 4, "Atmosphere": "", "Hull": "4D", "Shields": "2D", "Hyperdrive": "x2"},
     ((40, "1D"), (80, "2D"), (120, "3D"), (5, "3D+2"))),
]

SW_FORCE = [
    ("Life detection", "Feel the presence of living beings nearby, and recognise ones you know.", {"Sense": "Very Easy"}, "", "One round", True),
    ("Life sense", "Sense one particular being you know, and roughly how far away they are.", {"Sense": "Very Easy"}, "Life detection", "One round", True),
    ("Magnify senses", "Sharpen sight, hearing and smell. Add the Sense dice to Search and Perception.", {"Sense": "Easy"}, "", "One round", True),
    ("Receptive telepathy", "Read the surface thoughts and feelings of someone nearby.", {"Sense": "Easy"}, "Life detection", "One minute", False),
    ("Sense Force", "Feel the strength of the Force in a place, and whether it is tainted by the dark side.", {"Sense": "Moderate"}, "", "One minute", False),
    ("Danger sense", "A warning moments before an attack. Roll Sense to avoid being surprised.", {"Sense": "Moderate"}, "Life detection", "One round", True),
    ("Accelerate healing", "Heal one wound level faster than normal while resting.", {"Control": "Easy"}, "", "One minute", False),
    ("Control pain", "Act as if unwounded. The wounds are still there.", {"Control": "Easy"}, "", "One round", True),
    ("Concentration", "Add the Control dice to one skill roll for a round of total focus.", {"Control": "Easy"}, "", "One round", False),
    ("Hibernation trance", "Slow the body almost to death, needing little air, food or water.", {"Control": "Difficult"}, "", "One minute", True),
    ("Absorb or dissipate energy", "Soak heat, cold, radiation or energy damage.", {"Control": "Moderate"}, "", "One round", True),
    ("Enhance attribute", "Add a die to one physical attribute for a few rounds.", {"Control": "Moderate"}, "", "One round", True),
    ("Telekinesis", "Move objects with the mind. Heavier objects are harder.", {"Alter": "Easy"}, "", "One round", True),
    ("Injure or kill", "A dark side power that harms a living being by touch.", {"Control": "Moderate", "Alter": "Difficult"}, "Life sense", "One round", False),
    ("Lightsaber combat", "Add the Sense dice to Lightsaber and to parrying blaster bolts.", {"Control": "Moderate", "Sense": "Easy"}, "", "One round", True),
    ("Affect mind", "Make a weak-willed being forget, see what is not there or believe a suggestion.", {"Control": "Moderate", "Sense": "Easy", "Alter": "Moderate"}, "Receptive telepathy", "One round", False),
    ("Projective telepathy", "Send words or feelings into another mind.", {"Control": "Easy", "Sense": "Easy"}, "Receptive telepathy", "One round", False),
]

SW_ATTRS = ["Dexterity", "Knowledge", "Mechanical", "Perception", "Strength", "Technical"]


def pips(code):
    dice, _, bonus = code.partition("D")
    return int(dice) * 3 + (int(bonus.lstrip("+")) if bonus else 0)


SW_CREATURES = [
    ("Trooper", "An armoured soldier of the oppressive empire.",
     ["3D", "1D", "1D", "2D", "2D", "1D"],
     {"Dexterity Skills": {"Blaster": "1D", "Dodge": "1D"}, "Strength Skills": {"Brawling": "1D"}}),
    ("Smuggler", "Fast ship, fast mouth, flexible morals.",
     ["3D", "2D", "3D+1", "3D", "2D+2", "2D"],
     {"Dexterity Skills": {"Blaster": "2D", "Dodge": "1D"}, "Mechanical Skills": {"Spaceship piloting": "2D", "Astrogation": "1D"}, "Perception Skills": {"Con": "1D"}, "Knowledge Skills": {"Streetwise": "1D"}}),
    ("Bounty hunter", "Hunts people for the price on their head.",
     ["3D+2", "2D", "2D+1", "3D", "3D", "2D"],
     {"Dexterity Skills": {"Blaster": "3D", "Dodge": "2D", "Grenade": "1D"}, "Perception Skills": {"Search": "2D", "Sneak": "1D"}, "Knowledge Skills": {"Streetwise": "2D"}}),
    ("Cantina thug", "Muscle for hire in a port town.",
     ["2D+2", "1D+2", "2D", "2D", "3D+1", "1D"],
     {"Dexterity Skills": {"Blaster": "1D", "Melee": "1D"}, "Strength Skills": {"Brawling": "2D"}}),
    ("Pirate", "A raider of the space lanes.",
     ["3D", "2D", "3D", "2D+1", "2D+2", "2D"],
     {"Dexterity Skills": {"Blaster": "1D+1"}, "Mechanical Skills": {"Gunnery": "1D", "Spaceship piloting": "1D"}, "Strength Skills": {"Brawling": "1D"}}),
    ("Rebel soldier", "A volunteer fighting the empire.",
     ["3D", "2D", "2D", "2D", "3D", "2D"],
     {"Dexterity Skills": {"Blaster": "1D", "Dodge": "1D", "Grenade": "1D"}, "Knowledge Skills": {"Survival": "1D"}}),
    ("Imperial officer", "Crisp uniform, cold manner.",
     ["2D", "3D", "2D", "3D", "2D", "2D"],
     {"Dexterity Skills": {"Blaster": "1D"}, "Knowledge Skills": {"Bureaucracy": "2D"}, "Perception Skills": {"Con": "1D"}}),
    ("Security droid", "A guard droid that follows its programming to the letter.",
     ["3D", "1D", "1D", "2D", "3D", "1D"],
     {"Dexterity Skills": {"Blaster": "2D"}, "Perception Skills": {"Search": "1D"}}),
    ("Dark Jedi", "A fallen Force user. Dangerous and cruel.",
     ["3D+1", "3D", "2D", "3D", "3D", "2D"],
     {"Dexterity Skills": {"Lightsaber": "3D", "Dodge": "2D"}, "Perception Skills": {"Con": "1D"}},
     {"Control": "3D", "Sense": "2D", "Alter": "2D"}),
    ("Hunting beast", "A large predator from a jungle world.",
     ["3D", "0D", "0D", "3D", "5D", "0D"],
     {"Perception Skills": {"Search": "1D", "Sneak": "1D"}, "Strength Skills": {"Brawling": "2D"}}),
]


def starwars():
    s = "Starwars"
    entities = []
    for name, damage, ammo, range_, text in SW_RANGED:
        entities.append(entity(s, "Ranged weapons", name, text, {"rangedWeaponStats": {"Stats": {"Damage": damage, "Ammo": ammo, "Range": range_}}}))
    for name, damage, text in SW_MELEE:
        entities.append(entity(s, "Melee weapons", name, text, {"meleeWeaponStats": {"Stats": {"Damage": damage}}}))
    for name, value, text in SW_ARMOUR:
        entities.append(entity(s, "Armour", name, text, {"armourStats": {"Stats": {"Armor Value": value}}}))
    for name, text in SW_ITEMS:
        entities.append(entity(s, "Other items", name, text, {"otherStats": {"Stats": {}}}))
    for name, skill, fire, space, atmosphere, damage in SW_SHIP_WEAPONS:
        entities.append(entity(s, "ShipWeapons", name, "", {"shipWeaponStats": {"Stats": {
            "Skill": skill, "Fire Control": fire, "Space Range": space, "Atmosphere Range": atmosphere, "Damage": damage}}}))
    for name, text, basics, sensors in SW_SHIPS:
        entities.append(entity(s, "Spaceships", name, text, {"spaceshipTable": {
            "Basics": basics,
            "Sensors": {k: {"Range": r, "Value": v} for k, (r, v) in zip(["Passive", "Scan", "Search", "Focus"], sensors)},
        }}))
    for name, text, difficulties, required, time, keep_up in SW_FORCE:
        entities.append(entity(s, "Force powers", name, text, {"forcePowerStats": {
            "Power": {k: ({"Used": True, "Difficulty": difficulties[k]} if k in difficulties else {"Used": False}) for k in ["Sense", "Control", "Alter"]},
            "Details": {"Effect": text, "Required Powers": required, "Time to Use": time, "Keep Up": keep_up},
        }}))
    for name, text, attributes, skills, *jedi in SW_CREATURES:
        implementation = {
            "Attributes": {a: {"Points": pips(v)} for a, v in zip(SW_ATTRS, attributes)},
            **{table: {k: {"Points": pips(v)} for k, v in values.items()} for table, values in skills.items()},
        }
        if jedi:
            implementation["General"] = {"Force sensitive": True}
            implementation["Jedi skills"] = {k: {"Points": pips(v)} for k, v in jedi[0].items()}
        entities.append(entity(s, "Creature", name, text, {"characterTable": implementation}))
    return library(
        "Star Wars d6 basics",
        "Weapons, armour, gear, ships, Force powers and people for the d6 Star Wars game, written for Fudger as a fan aid. Skill points are added on top of the attribute. Star Wars is a trademark of Lucasfilm Ltd.",
        "/systems/starwars/sw.json", entities)


TORG_MELEE = [
    ("Knife", 11, "STR+1", "", "Easy to hide."),
    ("Club", 7, "STR+1", "", "Any heavy stick, pipe or bat."),
    ("Spear", 7, "STR+2", "", "Can be thrown."),
    ("Short sword", 11, "STR+2", "", ""),
    ("Sword", 11, "STR+3", "", ""),
    ("Axe", 9, "STR+3", "", ""),
    ("Greatsword", 12, "STR+4", "", "Two-handed."),
    ("Mace", 9, "STR+3", "", ""),
    ("Stun baton", 22, "STR+2", "", "Stun: damage is Shock only."),
    ("Chainsaw", 21, "STR+5", "", "Loud. Unwieldy: -2 to Melee Weapons."),
]

TORG_RANGED = [
    ("Short bow", 8, "STR+2", 1, "10/25/40", "", "Two-handed."),
    ("Long bow", 11, "STR+3", 1, "25/60/100", "", "Two-handed."),
    ("Crossbow", 13, "13", 1, "20/50/80", "", "Takes a round to reload."),
    ("Light pistol", 21, "12", 10, "10/25/40", "", "Small and easy to hide."),
    ("Pistol", 21, "13", 15, "10/25/40", "", "A standard 9 mm handgun."),
    ("Heavy revolver", 21, "15", 6, "10/25/40", "", "Big-bore revolver."),
    ("Shotgun", 21, "15", 6, "10/25/40", "", "+2 damage at close range, -2 at long."),
    ("Submachine gun", 22, "13", 30, "10/25/40", "", "Burst fire."),
    ("Assault rifle", 22, "15", 30, "40/100/200", "", "Burst fire."),
    ("Hunting rifle", 21, "15", 5, "50/150/300", "", "Scoped."),
    ("Sniper rifle", 23, "17", 5, "100/300/800", "", "Scoped. Needs a braced shot."),
    ("Frag grenade", 21, "16", 1, "5/10/15", "", "Thrown. Blast hits everyone near the target."),
    ("Laser pistol", 26, "16", 20, "15/40/60", "", "High-tech energy weapon."),
]

TORG_ARMOUR = [
    ("Heavy clothing", 7, "+1", "", "Leather jacket or thick coat."),
    ("Leather armour", 7, "+2", "", "Light and quiet."),
    ("Chain mail", 11, "+3", "", "-1 to Dexterity skills."),
    ("Plate armour", 13, "+5", "", "-2 to Dexterity skills and Move."),
    ("Kevlar vest", 21, "+3", "", "Concealable body armour."),
    ("Tactical body armour", 22, "+4", "", "Plates over a vest. -1 to Dexterity skills."),
    ("Riot armour", 22, "+5", "", "With helmet and shield. -1 to Dexterity skills."),
]

TORG_SKILLS = {
    "Combat skills": ["Energy Weapons", "Fire Combat", "Heavy Weapons", "Melee Weapons", "Missile Weapons", "Unarmed Combat"],
    "Interaction skills": ["Intimidation", "Maneuver", "Taunt", "Trick"],
}

TORG_CREATURES = [
    ("Thug", "Hired muscle with a pistol and few scruples.",
     [8, 8, 7, 7, 9], 10, "10", 8, 1, {"Fire Combat": 9, "Melee Weapons": 10, "Unarmed Combat": 10, "Intimidation": 10, "Dodge": 9, "Streetwise": 9}, "Pistol, knife", []),
    ("Police officer", "A patrol officer doing a hard job.",
     [8, 8, 8, 8, 8], 10, "11 (3)", 8, 1, {"Fire Combat": 10, "Unarmed Combat": 9, "Intimidation": 9, "Dodge": 9, "Find": 9, "Land Vehicles": 10}, "Pistol, Kevlar vest, radio", []),
    ("Soldier", "A trained infantry soldier.",
     [8, 9, 8, 8, 9], 10, "13 (4)", 9, 2, {"Fire Combat": 12, "Heavy Weapons": 10, "Unarmed Combat": 10, "Maneuver": 10, "Dodge": 10, "Survival": 9}, "Assault rifle, tactical body armour", []),
    ("Elite commando", "Special forces. Quick, quiet and lethal.",
     [8, 10, 9, 9, 10], 11, "14 (4)", 11, 3, {"Fire Combat": 14, "Melee Weapons": 12, "Unarmed Combat": 13, "Maneuver": 12, "Dodge": 12, "Stealth": 13, "Find": 11}, "Submachine gun, knife, tactical body armour", []),
    ("Cultist", "A fervent follower of a dark faith.",
     [7, 8, 8, 9, 8], 10, "8", 9, 1, {"Melee Weapons": 9, "Intimidation": 10, "Faith": 11, "Willpower": 11, "Stealth": 9}, "Ritual dagger", []),
    ("Knight", "An armoured warrior from a realm of legends.",
     [9, 9, 8, 10, 10], 10, "15 (5)", 10, 3, {"Melee Weapons": 13, "Beast Riding": 12, "Intimidation": 11, "Faith": 11, "Maneuver": 10}, "Sword, plate armour, warhorse", [("Code of honour", "Will not strike a foe who has yielded.")]),
    ("Wolf", "A wild canine hunting in a pack.",
     [5, 9, 5, 7, 8], 14, "8", 7, 1, {"Unarmed Combat": 11, "Dodge": 11, "Find": 10, "Stealth": 11, "Tracking": 12}, "", [("Bite", "Damage STR+2."), ("Pack hunter", "+1 to attacks when an ally is also next to the target.")]),
    ("Bear", "Massive and very hard to put down.",
     [5, 8, 5, 7, 13], 12, "15", 12, 3, {"Unarmed Combat": 12, "Intimidation": 12, "Find": 9}, "", [("Claws", "Damage STR+2."), ("Thick hide", "Armour +2, already counted in Tough.")]),
    ("Walking dead", "A shambling corpse with a hunger for the living.",
     [3, 7, 4, 8, 10], 6, "12", 0, 2, {"Unarmed Combat": 10, "Intimidation": 11}, "", [("Bite", "Damage STR+1."), ("Undead", "Takes no Shock. Only wounds stop it."), ("Slow", "Cannot run.")]),
    ("Vampire", "An ancient predator in a fine coat.",
     [12, 11, 10, 11, 12], 12, "14", 14, 4, {"Unarmed Combat": 13, "Melee Weapons": 12, "Intimidation": 14, "Trick": 12, "Persuasion": 13, "Stealth": 13, "Willpower": 13}, "", [("Bite", "Damage STR+2 and drains blood."), ("Undead", "Takes no Shock from normal weapons."), ("Weakness", "Sunlight and holy symbols.")]),
    ("Giant reptile", "A scaled beast the size of a truck.",
     [4, 8, 4, 7, 15], 14, "19 (2)", 14, 4, {"Unarmed Combat": 12, "Intimidation": 13, "Find": 9}, "", [("Bite", "Damage STR+3."), ("Scales", "Armour +2.")]),
    ("Cyborg enforcer", "Chrome limbs, targeting eye and a corporate leash.",
     [7, 10, 8, 7, 11], 11, "15 (4)", 11, 2, {"Fire Combat": 13, "Energy Weapons": 12, "Unarmed Combat": 12, "Intimidation": 12, "Dodge": 10, "Computers": 9}, "Laser pistol, implanted armour", [("Cyber-arm", "Unarmed damage STR+2."), ("Targeting eye", "+1 to ranged attacks.")]),
    ("Sorcerer", "A spellcaster wielding power from another reality.",
     [9, 8, 12, 11, 7], 10, "7", 11, 1, {"Alteration": 12, "Conjuration": 13, "Divination": 11, "Melee Weapons": 9, "Willpower": 13, "Scholar": 13}, "Staff, spellbook", [("Spells", "Knows a handful of attack and defence spells.")]),
]


def torg():
    s = "TORG"
    entities = []
    for name, tech, damage, price, notes in TORG_MELEE:
        entities.append(entity(s, "Melee weapons", name, notes, {"meleeStats": {"Stats": {"Tech": tech, "Damage": damage, "Price": price, "Notes": notes}}}))
    for name, tech, damage, ammo, range_, price, notes in TORG_RANGED:
        entities.append(entity(s, "Ranged weapons", name, notes, {"rangedStats": {"Stats": {"Tech": tech, "Damage": damage, "Ammo": ammo, "Range": range_, "Price": price, "Notes": notes}}}))
    for name, tech, bonus, price, notes in TORG_ARMOUR:
        entities.append(entity(s, "Armour", name, notes, {"armourStats": {"Stats": {"Tech": tech, "Bonus": bonus, "Price": price, "Notes": notes}}}))
    for name, text, attributes, move, tough, shock, wounds, skills, equipment, specials in TORG_CREATURES:
        implementation = {
            "Attributes": {a: {"Score": v} for a, v in zip(["Charisma", "Dexterity", "Mind", "Spirit", "Strength"], attributes)},
            "Basics": {"Move": move, "Tough": tough, "Shock": shock, "Wounds": wounds},
            "Other": {"Equipment": equipment},
            "Special Abilities": gifts(specials),
        }
        for table in ["Combat skills", "Interaction skills", "Skills"]:
            values = {k: {"Modifier": v} for k, v in skills.items() if (k in TORG_SKILLS[table] if table in TORG_SKILLS else not any(k in ks for ks in TORG_SKILLS.values()))}
            if values:
                implementation[table] = values
        entities.append(entity(s, "Creature", name, text, {"creatureTable": implementation}))
    return library(
        "Torg Eternity basics",
        "Weapons, armour and opponents for Torg Eternity, written for Fudger as a fan aid. Values are close to the published ones but not copied from them: check them against your books. Skill values are totals. Torg Eternity is a trademark of Ulisses Spiele.",
        "/systems/torg/torg.json", entities)


MS_WEAPONS = [
    ("Unarmed", "", "Adjacent", "1d5", "", "Blunt Force", ""),
    ("Boarding Axe", "150cr", "Adjacent", "2d10", "", "Gore [+]", ""),
    ("Crowbar", "25cr", "Adjacent", "1d5", "", "Blunt Force [+]", "[+] on Strength checks to force doors open."),
    ("Hand Welder", "250cr", "Adjacent", "1d10", "", "Bleeding", "Also cuts through hull plating, slowly."),
    ("Scalpel", "50cr", "Adjacent", "1d5", "", "Bleeding [+]", ""),
    ("Stun Baton", "150cr", "Adjacent", "1d5", "", "Blunt Force", "Body save or be stunned for a round."),
    ("Vibechete", "1kcr", "Adjacent", "3d10", "", "Gore", "Loud when switched on."),
    ("Flare Gun", "25cr", "Long", "1d5", "2", "Fire [-]", "Bright flare, visible for kilometres."),
    ("Nail Gun", "150cr", "Close", "1d5", "32", "Bleeding", "A construction tool."),
    ("Rigging Gun", "350cr", "Close", "1d10", "1", "Gunshot [+]", "Fires a grapple on 100 m of cable."),
    ("Tranq Pistol", "250cr", "Close", "1", "6", "Blunt Force", "Body save or be unconscious for 1d10 rounds."),
    ("Foam Gun", "500cr", "Close", "1", "3", "Blunt Force", "Body save or be stuck in hardening foam."),
    ("Revolver", "500cr", "Close", "1d10+1", "6", "Gunshot", ""),
    ("Combat Shotgun", "1.4kcr", "Close", "4d10", "4", "Gunshot", "Spreads out: [-] at long range."),
    ("SMG", "1kcr", "Long", "2d10", "5", "Gunshot", "Burst fire."),
    ("Pulse Rifle", "2.4kcr", "Long", "3d10", "3", "Gunshot [+]", "Military rifle with an underslung grenade launcher."),
    ("Smart Rifle", "12kcr", "Extreme", "4d10", "3", "Gunshot [+]", "Tracks targets. Needs a harness."),
    ("Laser Cutter", "1.2kcr", "Long", "1d100", "6", "Bleeding [+]", "Two-handed. A round to recharge between shots."),
    ("Flamethrower", "4kcr", "Close", "1d10", "4", "Fire/Explosives [-]", "Body save or catch fire."),
    ("Frag Grenade", "400cr", "Close", "3d10", "1", "Explosive [-]", "Hits everyone Close to where it lands."),
]

MS_ARMOR = [
    ("Standard Crew Attire", "100cr", 1, "None", "Normal", "Jumpsuit and boots."),
    ("Vaccsuit", "10kcr", 3, "12 hrs", "[-]", "Includes short-range comms, headlamp and radiation shielding. Decompression within 1d5 rounds if punctured."),
    ("Hazard Suit", "4kcr", 5, "1 hr", "Normal", "Sealed against chemicals, heat and cold."),
    ("Standard Battle Dress", "2kcr", 7, "None", "Normal", "Light military armour."),
    ("Advanced Battle Dress", "12kcr", 10, "1 hr", "[-]", "Powered armour with comms and a sealed helmet."),
]

MS_EQUIPMENT = [
    ("Assorted Tools", "20cr", "Wrenches, spanners and the like."),
    ("Automed", "1.5kcr", "Five doses of nanobots. Heal 1d10 Health and stop bleeding."),
    ("Battery", "50cr", "High power. Runs a tool or light for a day."),
    ("Binoculars", "150cr", "With night vision."),
    ("Body Cam", "50cr", "Records and streams video."),
    ("Chemlight", "5cr", "Lasts a few hours. Five per pack."),
    ("Cybernetic Diagnostic Scanner", "2kcr", "Finds faults in androids and implants."),
    ("Electronic Tool Set", "650cr", "For repairing electronics."),
    ("Emergency Beacon", "2kcr", "A long-range distress signal."),
    ("Exoloader", "100kcr", "Powered loader frame for heavy lifting. [+] on Strength checks."),
    ("First Aid Kit", "75cr", "Bandages, splints and painkillers."),
    ("Flashlight", "30cr", "Bright handheld light."),
    ("Infrared Goggles", "1.5kcr", "See heat through darkness and smoke."),
    ("Jetpack", "75kcr", "Thrust for zero-g manoeuvres."),
    ("Lockpick Set", "40cr", "For mechanical locks."),
    ("Long-range Comms", "1kcr", "Reaches orbit and other ships."),
    ("Mag-boots", "350cr", "Walk on metal hulls in zero-g."),
    ("Medscanner", "8kcr", "Reads vital signs and finds what is wrong."),
    ("Mylar Blanket", "10cr", "Keeps body heat in."),
    ("Oxygen Tank", "50cr", "Two hours of air for a vaccsuit."),
    ("Pain Pills", "450cr", "Heal 1d10 Health. Addictive."),
    ("Personal Locator", "200cr", "Shows where its wearer is."),
    ("Radiation Pills", "200cr", "Reduces radiation damage."),
    ("Rebreather", "500cr", "Twenty minutes of air in a bad atmosphere."),
    ("Short-range Comms", "100cr", "Radio with about a kilometre of range."),
    ("Stimpak", "1kcr", "Heal 1d10 Health and wake an unconscious person. Stress +1."),
    ("Water Filter", "15cr", "Makes most water drinkable."),
]

MS_TRAITS = [
    ("Marine", "are handy in a fight, but whenever they Panic it may cause problems for the rest of the crew.",
     "+10 combat, +10 body save, +20 fear save, +1 max wounds", "Whenever you panic, every close friendly player must make a fear save.", "Military training, Athletics. Bonus: 1 Expert Skill OR 2 Trained Skills."),
    ("Teamster", "keep the ships running. Rough, practical and hard to rattle.",
     "+5 to all stats, +10 to all saves", "Once per session, you may take advantage on a panic check.", "Industrial equipment, Zero-G. Bonus: 1 Trained Skill AND 1 Expert Skill."),
    ("Android", "are synthetic people. Capable and precise, and deeply unsettling to the crew.",
     "+20 intellect, -10 to 1 stat, +60 fear save, +1 max wounds", "Fear saves made by close friendly players are at disadvantage.", "Linguistics, Computers, Mathematics. Bonus: 1 Expert Skill OR 2 Trained Skills."),
    ("Scientist", "know how the universe works, which makes it worse when it stops making sense.",
     "+10 intellect, +5 to 1 stat, +30 sanity save", "Whenever you fail a sanity save, every close friendly player gains 1 stress.", "1 Master Skill with an Expert and a Trained Skill leading to it. Bonus: 1 Trained Skill."),
]

MS_CREATURES = [
    ("Corporate Security", "A guard paid to protect company property, not you.", 35, "Stun Baton 1d5 or Revolver 1d10+1", 25, 3, 1, 15, ""),
    ("Pirate Raider", "Desperate, armed and looking for an easy score.", 40, "SMG 2d10", 30, 3, 1, 20, "Flees if half the crew go down."),
    ("Feral Crewmember", "Someone who was crew, before the ship got into their head.", 30, "Wrench 1d10", 20, 1, 1, 15, "Screams. Whoever hears it makes a fear save."),
    ("Hostile Android", "Its directives changed. Calm voice, no hesitation.", 50, "Strangle 2d10", 40, 3, 2, 25, "Feels no pain. Ignores the first wound effect."),
    ("Hull Rat Swarm", "Hundreds of chittering vermin in the walls.", 25, "Bites 1d5", 30, 0, 1, 20, "Only area damage hurts it properly."),
    ("Parasite Larva", "Small, fast and looking for a host.", 30, "Latch on, Body save or be implanted", 50, 0, 1, 5, "An implanted host births an adult in 1d10 hours."),
    ("Hunter Drone", "A security drone with outdated friend-or-foe tags.", 45, "Twin guns 2d10", 35, 5, 1, 20, "Can fly. Fooled by a spoofed ID."),
    ("Void Cultist", "Whispers about the gap between the stars.", 25, "Knife 1d5", 40, 1, 1, 10, "Close players make a sanity save when it speaks."),
    ("Stalker", "A tall, silent alien that hunts through the vents.", 65, "Claws 3d10", 55, 5, 3, 40, "Vanishes into the dark after each attack."),
    ("Abomination", "Flesh from many crew, fused together and still moving.", 55, "Crush 4d10", 30, 2, 4, 50, "Every player who sees it gains 1 stress."),
]


def mothership():
    s = "mothership"
    entities = []
    for name, cost, range_, damage, shots, wound, special in MS_WEAPONS:
        entities.append(entity(s, "Weapons", name, special, {"weaponStats": {"Stats": {
            "Cost": cost, "Range": range_, "Damage": damage, "Shots": shots or "N/A", "Wound": wound, "Special": special}}}))
    for name, cost, ap, o2, speed, special in MS_ARMOR:
        entities.append(entity(s, "Armor", name, special, {"armorStats": {"Stats": {"Cost": cost, "AP": ap, "O2": o2, "Speed": speed, "Special": special}}}))
    for name, cost, text in MS_EQUIPMENT:
        entities.append(entity(s, "Equipment", name, text, {"equipmentStats": {"Stats": {"Cost": cost}}}))
    for name, text, adjust, trauma, skills in MS_TRAITS:
        entities.append(entity(s, "Traits", name, f"{name}s {text}", {"traitStats": {"Stats": {"Adjust": adjust, "Trauma response": trauma, "Skills": skills}}}))
    for name, text, combat, attack, instinct, ap, wounds, health, special in MS_CREATURES:
        entities.append(entity(s, "Creature", name, text, {"creatureTable": {"Stats": {
            "Combat": combat, "Attack": attack, "Instinct": instinct, "AP": ap, "Wounds": wounds,
            "Current Wounds": 0, "Health": health, "Current Health": health, "Special": special}}}))
    return library(
        "Mothership basics",
        "Weapons, armour, equipment, classes and threats for Mothership, written for Fudger. This library is an independent production and is not affiliated with Tuesday Knight Games. It is published under the Mothership Third Party License. Mothership is copyright Tuesday Knight Games.",
        "/systems/mothership/mothership.json", entities)


write("Fudge/fudge.json", fudge())
write("edge/edge.json", edge())
write("starwars/sw.json", starwars())
write("torg/torg.json", torg())
write("mothership/mothership.json", mothership())
