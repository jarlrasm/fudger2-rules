import json
import sys

OUT = sys.argv[1]
SYSTEM = "MutantsAndMasterminds"
URL = "/systems/mutants/mutants.json"

EFFECTS = [
    ("Affliction", "Attack", "Standard", "Close", "Instant", "1 per rank", "Imposes conditions that worsen with each degree of failure on a resistance check against 10 + rank, chosen from three tiers such as dazed, stunned and incapacitated."),
    ("Burrowing", "Movement", "Free", "Personal", "Sustained", "1 per rank", "Move through the ground at your burrowing speed, leaving a tunnel or not as you choose."),
    ("Communication", "Sensory", "Free", "Rank", "Sustained", "4 per rank", "Talk with others over a distance set by rank through a chosen medium, such as radio or thought."),
    ("Comprehend", "Sensory", "None", "Personal", "Permanent", "2 per rank", "Understand and be understood: languages, animals, machines, objects or spirits."),
    ("Concealment", "Sensory", "Free", "Personal", "Sustained", "2 per rank", "Hide from one or more senses, up to total invisibility from every sense at high rank."),
    ("Create", "Control", "Standard", "Ranged", "Sustained", "2 per rank", "Form solid objects with Toughness equal to rank and a volume set by rank."),
    ("Damage", "Attack", "Standard", "Close", "Instant", "1 per rank", "Harm a target, who resists with Toughness against 15 + rank."),
    ("Deflect", "Defense", "Standard", "Ranged", "Instant", "1 per rank", "Block ranged attacks against yourself or others with a check using your rank."),
    ("Elongation", "General", "Free", "Personal", "Sustained", "1 per rank", "Stretch your body to reach further, by a distance set by rank."),
    ("Enhanced Trait", "General", "Free", "Personal", "Sustained", "As the trait", "Raise an ability, defence, skill or advantage above what you bought for it."),
    ("Environment", "Control", "Standard", "Rank", "Sustained", "1 or 2 per rank", "Change the conditions around you: cold, heat, impeded movement, light, or visibility."),
    ("Extra Limbs", "General", "None", "Personal", "Permanent", "1 per rank", "Additional arms, tentacles or tails that let you hold and act with more."),
    ("Feature", "General", "None", "Personal", "Permanent", "1 per rank", "A minor ability or advantage worth one point each, such as a hidden compartment or a quick change."),
    ("Flight", "Movement", "Free", "Personal", "Sustained", "2 per rank", "Fly through the air at a speed set by rank."),
    ("Growth", "General", "Free", "Personal", "Sustained", "2 per rank", "Grow larger: more Strength, Stamina and mass, but easier to hit and harder to hide."),
    ("Healing", "General", "Standard", "Close", "Instant", "2 per rank", "Remove damage conditions and other harm from yourself or someone you touch."),
    ("Illusion", "Control", "Standard", "Perception", "Sustained", "1 to 5 per rank", "Make false sensory images that observers must see through with Insight or Perception."),
    ("Immortality", "Defense", "None", "Personal", "Permanent", "2 per rank", "Come back from death after a time that shortens with rank."),
    ("Immunity", "Defense", "None", "Personal", "Permanent", "1 per rank", "Ignore certain effects or conditions entirely, from a single poison up to all Fortitude effects."),
    ("Insubstantial", "General", "Free", "Personal", "Sustained", "5 per rank", "Take a less solid form: fluid, gas, energy or fully incorporeal at the highest rank."),
    ("Leaping", "Movement", "Free", "Personal", "Instant", "1 per rank", "Jump great distances, set by rank."),
    ("Luck Control", "Control", "Reaction", "Perception", "Instant", "3 per rank", "Spend hero points on others, force rerolls, or deny luck to your foes."),
    ("Mind Reading", "Sensory", "Standard", "Perception", "Sustained", "2 per rank", "Read a target's thoughts on an opposed check against Will, learning more with each degree."),
    ("Morph", "General", "Free", "Personal", "Sustained", "5 per rank", "Change your appearance, from one other look at rank 1 to any form at higher ranks."),
    ("Move Object", "Control", "Standard", "Ranged", "Sustained", "2 per rank", "Lift and move things at range as if with Strength equal to rank."),
    ("Movement", "Movement", "Free", "Personal", "Sustained", "2 per rank", "Special ways of moving, such as wall-crawling, water-walking, slithering or dimension travel."),
    ("Nullify", "Attack", "Standard", "Ranged", "Instant", "1 per rank", "Cancel other powers with an opposed check of your rank against theirs."),
    ("Protection", "Defense", "None", "Personal", "Permanent", "1 per rank", "Add rank to Toughness."),
    ("Quickness", "General", "Free", "Personal", "Sustained", "1 per rank", "Do routine tasks much faster than normal."),
    ("Regeneration", "Defense", "None", "Personal", "Permanent", "1 per rank", "Recover from damage conditions every few rounds instead of over hours."),
    ("Remote Sensing", "Sensory", "Free", "Rank", "Sustained", "1 to 5 per rank", "Move your senses to a distant place, set by rank."),
    ("Senses", "Sensory", "None", "Personal", "Permanent", "1 per rank", "Heightened or unusual senses: darkvision, detect, radio, tracking, danger sense and more."),
    ("Shrinking", "General", "Free", "Personal", "Sustained", "2 per rank", "Grow smaller: harder to hit and see, but weaker."),
    ("Speed", "Movement", "Free", "Personal", "Sustained", "1 per rank", "Run faster, at a speed set by rank."),
    ("Summon", "Control", "Standard", "Close", "Sustained", "2 per rank", "Call up a minion with power points set by rank."),
    ("Swimming", "Movement", "Free", "Personal", "Sustained", "1 per rank", "Swim at a speed set by rank."),
    ("Teleport", "Movement", "Move", "Rank", "Instant", "2 per rank", "Vanish and reappear somewhere else within a distance set by rank."),
    ("Transform", "Control", "Standard", "Close", "Sustained", "2 to 5 per rank", "Change one thing into another, with mass set by rank and the breadth of what you can change set by cost."),
    ("Variable", "General", "Standard", "Personal", "Sustained", "7 per rank", "A pool of 5 power points per rank that you can spend on different traits as the situation needs."),
    ("Weaken", "Attack", "Standard", "Close", "Instant", "1 per rank", "Lower a trait of the target by your degrees of success on an opposed resistance check."),
]

ADVANTAGES = [
    ("Accurate Attack", "Combat", "", "Trade effect for accuracy: up to -5 on effect rank for up to +5 to attack."),
    ("All-out Attack", "Combat", "", "Trade active defences for attack: up to -5 to Dodge and Parry for up to +5 to attack."),
    ("Chokehold", "Combat", "", "A successful grab can start suffocating the target."),
    ("Close Attack", "Combat", "Ranked", "+1 to close attacks per rank."),
    ("Defensive Attack", "Combat", "", "Trade attack for defence: up to -5 to attack for up to +5 to Dodge and Parry."),
    ("Defensive Roll", "Combat", "Ranked", "+1 to Toughness per rank, lost when you are vulnerable or defenceless."),
    ("Evasion", "Combat", "Ranked", "+2 to Dodge against area effects per rank."),
    ("Fast Grab", "Combat", "", "Make a free grab check after a successful unarmed attack."),
    ("Favored Environment", "Combat", "", "+2 to attack or defence in one kind of environment, such as underwater or in the air."),
    ("Grabbing Finesse", "Combat", "", "Use Dexterity instead of Strength for grabbing, and stay unhindered while grabbing."),
    ("Improved Aim", "Combat", "", "Double the bonus from aiming."),
    ("Improved Critical", "Combat", "Ranked", "Score a critical hit on one more natural roll per rank with one attack."),
    ("Improved Defense", "Combat", "", "+2 to active defences when you take the defend action."),
    ("Improved Disarm", "Combat", "", "Disarm without suffering a counter-disarm."),
    ("Improved Grab", "Combat", "", "Grab with one arm and stay free to act."),
    ("Improved Hold", "Combat", "", "Your grabs are harder to escape."),
    ("Improved Initiative", "Combat", "Ranked", "+4 to initiative per rank."),
    ("Improved Smash", "Combat", "", "Smash held objects without suffering a counter-attack."),
    ("Improved Trip", "Combat", "", "Trip without suffering a counter-trip."),
    ("Improvised Weapon", "Combat", "Ranked", "Use Close Combat with improvised weapons and add +1 damage per rank."),
    ("Move-by Action", "Combat", "", "Move both before and after your standard action."),
    ("Power Attack", "Combat", "", "Trade accuracy for effect: up to -5 to attack for up to +5 to effect rank."),
    ("Precise Attack", "Combat", "Ranked", "Ignore cover or concealment penalties for one kind of attack per rank."),
    ("Prone Fighting", "Combat", "", "Suffer no penalty for fighting while prone."),
    ("Quick Draw", "Combat", "", "Draw a weapon as a free action."),
    ("Ranged Attack", "Combat", "Ranked", "+1 to ranged attacks per rank."),
    ("Redirect", "Combat", "", "After a missed attack against you, trick the attacker into hitting someone else."),
    ("Set-up", "Combat", "Ranked", "Pass the benefit of a successful interaction skill to an ally."),
    ("Takedown", "Combat", "Ranked", "After taking out a minion, make a free attack on another nearby minion."),
    ("Throwing Mastery", "Combat", "Ranked", "+1 damage with thrown weapons per rank."),
    ("Uncanny Dodge", "Combat", "", "You are never caught by surprise."),
    ("Weapon Bind", "Combat", "", "Disarm an opponent who misses you with a melee weapon."),
    ("Weapon Break", "Combat", "", "Smash an opponent's weapon when you block or are attacked."),
    ("Beginner's Luck", "Fortune", "", "Spend a hero point to gain 5 temporary ranks in a skill you lack."),
    ("Inspire", "Fortune", "Ranked", "Spend a hero point to give allies a bonus on checks equal to your rank."),
    ("Leadership", "Fortune", "", "Spend a hero point to remove a dazed, fatigued or stunned condition from an ally."),
    ("Luck", "Fortune", "Ranked", "Reroll a die once per rank per session."),
    ("Seize Initiative", "Fortune", "", "Spend a hero point to act first in the initiative order."),
    ("Ultimate Effort", "Fortune", "", "Spend a hero point to treat a check of one kind as a natural 20."),
    ("Assessment", "General", "", "Use Insight to learn an opponent's combat bonuses."),
    ("Benefit", "General", "Ranked", "Wealth, status, rank or other perks, one per rank."),
    ("Diehard", "General", "", "Stabilise automatically when dying."),
    ("Eidetic Memory", "General", "", "Remember everything you have seen or heard."),
    ("Equipment", "General", "Ranked", "5 points of equipment per rank."),
    ("Extraordinary Effort", "General", "", "Gain two benefits from extra effort, at the cost of being exhausted afterwards."),
    ("Fearless", "General", "", "Immune to fear effects."),
    ("Great Endurance", "General", "", "+5 on checks to resist the environment and keep going."),
    ("Instant Up", "General", "", "Stand up from prone as a free action."),
    ("Interpose", "General", "", "Take an attack meant for an ally once per round."),
    ("Minion", "General", "Ranked", "A follower built on 15 power points per rank."),
    ("Second Chance", "General", "Ranked", "Reroll a failed check against one hazard, once per rank."),
    ("Sidekick", "General", "Ranked", "A sidekick built on 5 power points per rank."),
    ("Teamwork", "General", "", "+5 when you support team checks."),
    ("Trance", "General", "", "Enter a deathlike trance that slows your bodily functions."),
    ("Agile Feint", "Skill", "", "Feint with Acrobatics or movement speed instead of Deception."),
    ("Animal Empathy", "Skill", "", "Use interaction skills on animals without penalty."),
    ("Artificer", "Skill", "", "Use Expertise: Magic to make temporary magical devices."),
    ("Attractive", "Skill", "Ranked", "+2 to Deception and Persuasion with those who find you attractive, per rank."),
    ("Connected", "Skill", "", "Call in favours from people you know."),
    ("Contacts", "Skill", "", "Make an initial Investigation check for gathering information in one minute."),
    ("Daze", "Skill", "Ranked", "Use Deception or Intimidation to daze an opponent."),
    ("Fascinate", "Skill", "Ranked", "Use an interaction skill to hold others' attention."),
    ("Favored Foe", "Skill", "", "+2 to checks against one type of opponent."),
    ("Hide in Plain Sight", "Skill", "", "Hide while observed, without needing cover."),
    ("Improvised Tools", "Skill", "", "Ignore the penalty for working without tools."),
    ("Inventor", "Skill", "", "Use Technology to make temporary inventions."),
    ("Jack-of-all-trades", "Skill", "", "Use any skill untrained."),
    ("Languages", "Skill", "Ranked", "Speak more languages: one at rank 1, then doubling with each rank."),
    ("Ritualist", "Skill", "", "Use Expertise: Magic to perform rituals."),
    ("Skill Mastery", "Skill", "Ranked", "Take routine checks with one skill per rank, even under pressure."),
    ("Startle", "Skill", "", "Use Intimidation to feint."),
    ("Taunt", "Skill", "", "Use Deception to demoralise."),
    ("Tracking", "Skill", "", "Use Perception to follow tracks."),
    ("Well-informed", "Skill", "", "Make an immediate Investigation or Persuasion check to know something about a person, place or thing."),
]


def entity(type_, name, description, implementation):
    return {
        "type": type_,
        "name": name,
        "description": description,
        "images": {},
        "rulesets": [{"system": SYSTEM, "implementation": implementation}],
    }


effects = [
    entity("Effects", name, text, {"effectStats": {"Stats": {"Type": kind, "Action": action, "Range": range_, "Duration": duration, "Cost": cost}}})
    for name, kind, action, range_, duration, cost, text in EFFECTS
]

advantages = [
    entity("Advantages", name, text, {"advantageStats": {"Stats": {"Type": kind, "Ranked": ranked}}})
    for name, kind, ranked, text in ADVANTAGES
]

library = {
    "name": "Mutants and Masterminds effects and advantages",
    "description": "Power effects and advantages of the Mutants and Masterminds 3rd edition Hero's Handbook, Open Game Content under the Open Game License 1.0a (see LICENSE-mutants.md), summarised in short. Mutants and Masterminds is a trademark of Green Ronin Publishing; this library is not affiliated with Green Ronin Publishing.",
    "url": URL,
    "gamemaster": "",
    "entities": effects + advantages,
}

with open(f"{OUT}/mutants.json", "w") as f:
    json.dump(library, f, indent=1, ensure_ascii=False)
    f.write("\n")
