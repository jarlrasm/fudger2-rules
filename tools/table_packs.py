"""Writes the built-in random table libraries.

The genre packs (fantasy, sci-fi, modern) work in any system. The DnD
encounter tables link creatures of the SRD library by name, and the script
stops if one of those names is missing there.

    python3 tools/table_packs.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CREDIT = "Written for Fudger."


def numbered(results, dice=None):
    size = len(results)
    return {"dice": dice or f"1d{size}", "entries": [dict(entry, **{"from": i + 1, "to": i + 1}) for i, entry in enumerate(results)]}


def ranged(dice, results):
    return {"dice": dice, "entries": [dict(entry, **{"from": low, "to": high}) for (low, high), entry in results]}


def text(value):
    return {"text": value}


def table(name, description, definition, secret=False):
    return {"type": "Tables", "name": name, "description": description, "images": {}, "rulesets": [],
            "table": dict(definition, **({"secret": True} if secret else {}))}


def library(name, description, items):
    return {"name": name, "description": f"{description} {CREDIT}", "url": "", "gamemaster": "", "entities": items}


def texts(values):
    return [text(value) for value in values]


def link(name, value=None):
    return dict({"table": {"name": name}}, **({"text": value} if value else {}))


FANTASY = library("Fantasy tables", "Random tables for fantasy adventures: weather, travel, taverns, rumours, people and trinkets.", [
    table("Fantasy weather", "Today's weather in a temperate land.", ranged("2d6", [
        ((2, 2), text("A storm with thunder; travel is slow and dangerous")),
        ((3, 4), text("Cold rain all day")),
        ((5, 6), text("Grey skies and a steady wind")),
        ((7, 8), text("Clear and mild")),
        ((9, 10), text("Warm sun, a light breeze")),
        ((11, 11), text("Thick fog until noon")),
        ((12, 12), text("Strange weather: a red sky, warm snow or a sudden hush")),
    ])),
    table("Travel encounters", "Who or what the travellers meet on the road.", numbered([
        text("A merchant with a broken cart wheel, offering a discount for help"),
        text("Pilgrims singing on their way to a shrine"),
        text("A toll gate run by [[1d4+1]] bored guards"),
        text("A messenger on a tired horse, in a great hurry"),
        text("Tracks leaving the road, fresh and heavy"),
        text("A wandering tinker who knows the local gossip"),
        link("Fantasy weather", "The weather turns:"),
        link("Fantasy people", "A traveller going the same way:"),
    ]), secret=True),
    table("Tavern events", "Something happening in the tavern tonight.", numbered(texts([
        "A card game turns into an argument about cheating",
        "A bard plays a song about one of the characters, with the facts wrong",
        "The cook runs out of everything except stew",
        "A stranger pays for everyone's drinks and leaves at once",
        "Two old friends meet again and drink far too much",
        "A notice goes up offering a reward for a lost dog",
        "The floor gives way under a heavy table",
        "A local champion challenges anyone to arm wrestling",
        "Someone recognises a character from somewhere they would rather forget",
        "A traveller sells maps; one of them looks real",
        "The landlord asks for help with noises in the cellar",
        "A wedding party arrives and takes over the place",
    ]))),
    table("Rumours", "What people are saying. Some of it is true.", numbered(texts([
        "The old mill is haunted by the miller's apprentice",
        "The baron owes money to someone dangerous",
        "Wolves have been seen walking on two legs at night",
        "A ship came in with no crew, only cargo",
        "The well in the square grants wishes, if you give it silver",
        "Someone is buying up all the graveyard plots",
        "The priest was seen meeting a hooded figure at midnight",
        "There is gold in the hills, if you know where to dig",
        "A dragon was seen over the mountains last winter",
        "The new tax collector is not who he says he is",
    ])), secret=True),
    table("Fantasy people", "A quick person to meet: who they are and what stands out.", numbered([
        link("Quirks", "A tired farmer."),
        link("Quirks", "A cheerful guard."),
        link("Quirks", "A sharp-eyed merchant."),
        link("Quirks", "A young scholar."),
        link("Quirks", "An old soldier."),
        link("Quirks", "A wandering priest."),
    ])),
    table("Quirks", "One thing that makes a person stand out.", numbered(texts([
        "Hums when nervous", "Never makes eye contact", "Collects buttons", "Laughs too loudly",
        "Speaks in proverbs", "Is missing two fingers and tells a different story each time",
        "Always eating something", "Is very polite and very rude in the same sentence",
        "Wears far too much perfume", "Keeps a pet mouse in a pocket", "Whispers everything",
        "Hates the colour green", "Tells everyone about their dreams", "Is terrified of birds",
        "Counts things out loud", "Has a scar they are proud of", "Owes money to everyone",
        "Asks a question in answer to every question", "Quotes a famous poet badly", "Is always cold",
    ]))),
    table("Trinkets", "A small odd thing found in a pocket, a drawer or a pile of bones.", numbered(texts([
        "A key with no lock to fit it", "A tooth with a word carved on it", "A tin soldier with one leg",
        "A pressed flower in wax paper", "A ring too small for any finger", "A letter that was never sent",
        "A glass eye", "A tiny bell that makes no sound", "A map of a town that does not exist",
        "A wooden coin", "A lock of silver hair tied with red thread", "A dice that always rolls six for its owner",
        "A seashell that smells of smoke", "A child's drawing of a monster", "A brass compass that points west",
        "A broken mirror shard", "A stone that is always warm", "A recipe for soup in an unknown language",
        "A feather as long as an arm", "A candle stub that relights itself once",
    ]))),
])

SCIFI = library("Sci-fi tables", "Random tables for science fiction: ship trouble, stations, salvage, aliens and contacts.", [
    table("Ship trouble", "What goes wrong aboard the ship.", numbered(texts([
        "Life support smells of burnt coffee and nobody knows why",
        "The navigation computer insists on a different route",
        "A coolant leak in the engine room",
        "The airlock cycles on its own at night",
        "A stowaway is hiding in the cargo bay",
        "Gravity flickers for [[1d6]] seconds every hour",
        "The comms pick up a signal that sounds like the crew",
        "A fuse box fails; half the lights go out",
    ])), secret=True),
    table("Station rumours", "What people say in the bars of a space station.", numbered(texts([
        "A mining company found something it is not reporting",
        "The station's AI has started asking questions",
        "A ship docked last week and nobody has seen its crew",
        "Pirates are paying good money for navigation codes",
        "Docking fees are going up again, and someone is pocketing the difference",
        "A long-lost colony ship has been sighted near the gas giant",
        "The medical bay is selling something that is not medicine",
        "The security chief can be bought, but not cheaply",
    ])), secret=True),
    table("Salvage", "What turns up in a wreck or a cargo crate.", numbered(texts([
        "[[2d6]] crates of ration bars", "A damaged but working scanner", "A sealed data core",
        "Spare parts worth a good price", "A space suit with a name tag and a hole", "A frozen pet in a stasis box",
        "Encrypted credit chips", "A crate of weapons with no serial numbers", "A star map with one system circled",
        "A crew log that stops in the middle of a sentence",
    ]))),
    table("Alien features", "What stands out about an alien someone meets.", numbered(texts([
        "Speaks only in questions", "Changes colour with its mood", "Has a smell that means something rude",
        "Is very small and very loud", "Moves only when nobody is watching", "Carries its elders in a jar",
        "Thinks humans are a kind of pet", "Collects human songs", "Sleeps standing up, in the middle of conversations",
        "Is three beings that share one name", "Finds handshakes deeply offensive", "Pays for everything in stories",
    ]))),
    table("Contacts", "Someone in a port who might help, for a price.", numbered([
        link("Alien features", "A fixer who knows every dock worker."),
        text("A tired customs officer close to retiring"),
        text("A ship mechanic who works for parts, not money"),
        text("A smuggler with a fast ship and slow payments"),
        text("A journalist chasing a story about a mining company"),
        link("Station rumours", "A bartender who hears everything:"),
    ])),
    table("Deep space encounters", "What the sensors pick up between the stars.", numbered([
        text("A distress beacon on an old frequency"),
        text("A drifting freighter, lights on, no answer"),
        text("[[1d3]] fighters closing fast without a transponder"),
        text("A comet with a strange metal core"),
        text("A patrol ship that wants to inspect the cargo"),
        link("Ship trouble", "Nothing outside, but:"),
        link("Salvage", "A field of debris:"),
        text("Silence. Sensors show nothing at all, which should be impossible"),
    ]), secret=True),
])

MODERN = library("Modern tables", "Random tables for modern-day games: streets, weather, people, news and odd finds.", [
    table("Street encounters", "What happens on a city street.", numbered(texts([
        "A cyclist nearly runs someone over and keeps going",
        "A street musician plays a song that seems meant for the characters",
        "A car alarm goes off; nobody comes",
        "Someone hands out flyers for a missing person",
        "A delivery driver is lost and asks for directions",
        "Two police officers are questioning a shopkeeper",
        "A phone rings in a phone booth",
        "A dog follows the characters for two blocks, then vanishes",
        "Someone is filming the characters from across the street",
        "A fight breaks out outside a bar",
    ])), secret=True),
    table("Modern weather", "Today's weather in town.", ranged("2d6", [
        ((2, 3), text("A thunderstorm; power cuts here and there")),
        ((4, 5), text("Drizzle and grey skies")),
        ((6, 8), text("Mild and cloudy")),
        ((9, 10), text("Bright and sunny")),
        ((11, 11), text("A heatwave; everyone is short-tempered")),
        ((12, 12), text("Fog so thick the streetlights stay on all day")),
    ])),
    table("Modern people", "Someone the characters meet.", numbered(texts([
        "A night-shift nurse who has seen everything",
        "A teenager who knows every shortcut in town",
        "A retired detective who still keeps files",
        "A taxi driver with opinions about everything",
        "A shop owner behind on rent",
        "A lawyer who answers the phone at three in the morning",
        "A city clerk who can find any record, for a favour",
        "A neighbour who watches the street all day",
    ]))),
    table("News headlines", "What the papers and feeds are saying today.", numbered(texts([
        "Local factory to close after 60 years",
        "Strange lights over the reservoir",
        "Mayor denies knowing anything about the missing funds",
        "Animals at the zoo restless for a week",
        "Third break-in at the museum this month; nothing taken",
        "Power company blames birds for the outages",
        "Famous author returns to hometown",
        "Road closed for 'routine maintenance', no end date given",
    ]))),
    table("Things in a drawer", "What turns up in a desk, a glovebox or a coat pocket.", numbered(texts([
        "A key card for a building nobody mentions", "A receipt for something expensive, paid in cash",
        "A photo with one face scratched out", "A burner phone with one number saved", "A ticket stub for a show years ago",
        "A handwritten list of names, some crossed out", "A pawn shop ticket", "A child's drawing with a strange symbol",
        "Pills in an unlabelled bottle", "A business card with only a phone number",
    ]))),
])

ENCOUNTERS = [
    ("Forest encounters", "Who or what the party meets in the woods.", [
        ("Wolf", "1d4+1"), ("Giant Spider", "1"), ("Bandit", "1d6+1"), ("Brown Bear", "1"), ("Dryad", "1"),
        ("Owlbear", "1"), ("Elk", "1d6"), ("Goblin Warrior", "1d6+2"), ("Werewolf", "1"), ("Awakened Tree", "1"),
        ("Green Hag", "1"),
    ]),
    ("Swamp encounters", "Who or what the party meets in a swamp or marsh.", [
        ("Giant Frog", "1d4"), ("Crocodile", "1d3"), ("Swarm of Insects", "1d2"), ("Lizard", "1d6"), ("Shambling Mound", "1"),
        ("Will-o'-Wisp", "1"), ("Giant Toad", "1d2"), ("Ghoul", "1d4"), ("Constrictor Snake", "1"), ("Stirge", "2d4"),
        ("Troll", "1"),
    ]),
    ("Hill encounters", "Who or what the party meets in hills and highlands.", [
        ("Hill Giant", "1"), ("Goblin Warrior", "2d4"), ("Hobgoblin Warrior", "1d6+1"), ("Giant Eagle", "1d2"), ("Ogre", "1d2"),
        ("Gnoll Warrior", "1d6"), ("Griffon", "1"), ("Bandit", "2d4"), ("Giant Goat", "1d4"), ("Worg", "1d3"),
        ("Manticore", "1"),
    ]),
    ("Dungeon encounters", "What the party meets in a dungeon's halls.", [
        ("Skeleton", "1d6+1"), ("Zombie", "1d4+1"), ("Giant Rat", "2d4"), ("Gelatinous Cube", "1"), ("Kobold Warrior", "2d4"),
        ("Mimic", "1"), ("Ochre Jelly", "1"), ("Ghoul", "1d4"), ("Rust Monster", "1"), ("Shadow", "1d3"),
        ("Gibbering Mouther", "1"),
    ]),
    ("Road encounters", "Who the party meets on a road between towns.", [
        ("Commoner", "1d6"), ("Guard", "1d4+2"), ("Bandit", "1d6+2"), ("Noble", "1"), ("Priest Acolyte", "1d4"),
        ("Knight", "1"), ("Bandit Captain", "1"), ("Spy", "1"), ("Mastiff", "1d4"), ("Tough", "1d4+1"),
        ("Cultist", "1d6"),
    ]),
]


def encounter_tables(srd):
    known = {entity["name"] for entity in srd["entities"] if entity["type"] == "Creature"}
    missing = [f"{name}: {creature}" for name, _, rows in ENCOUNTERS for creature, _ in rows if creature not in known]
    if missing:
        sys.exit("Not in the SRD library: " + ", ".join(missing))
    tables = [table(name, description, numbered([{"item": {"name": creature}, "count": count} for creature, count in rows] + [{"again": 2}]), secret=True)
              for name, description, rows in ENCOUNTERS]
    return library("DnD encounter tables", "Random encounters by terrain, using the creatures of the SRD 5.2.1 library. A 12 rolls twice.", tables)


def write(path, data):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    print(f"{path}: {len(data['entities'])} tables")


def main():
    for target, data in [("systems/tables/fantasy.json", FANTASY), ("systems/tables/scifi.json", SCIFI), ("systems/tables/modern.json", MODERN)]:
        write(target, {**data, "url": "/" + target})
    srd = json.load(open(ROOT / "systems/DND/dndsrd2024.json"))
    write("systems/DND/encounters.json", {**encounter_tables(srd), "url": "/systems/DND/encounters.json"})


if __name__ == "__main__":
    main()
