import json
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "systems/Gurps/gurpslite.json"
SYSTEM = "GURPSLite"

NOTICE = (
    "GURPS is a trademark of Steve Jackson Games, and its rules and art are copyrighted "
    "by Steve Jackson Games. All rights are reserved by Steve Jackson Games. This game aid "
    "is the original creation of the Fudger project and is released for free distribution, "
    "and not for resale, under the permissions granted in the Steve Jackson Games Online Policy."
)


def entity(type_, name, description, implementation):
    return {
        "type": type_,
        "name": name,
        "description": description,
        "rulesets": [{"system": SYSTEM, "implementation": implementation}],
    }


ADVANTAGES = [
    ("Absolute Direction", 5, False, "Mental", "You always know which way is north and can retrace any path you have followed in the last month. +3 to Navigation."),
    ("Acute Hearing", 2, True, "Physical", "+1 per level to Sense rolls for hearing."),
    ("Acute Taste and Smell", 2, True, "Physical", "+1 per level to Sense rolls for taste and smell."),
    ("Acute Touch", 2, True, "Physical", "+1 per level to Sense rolls for touch."),
    ("Acute Vision", 2, True, "Physical", "+1 per level to Sense rolls for sight."),
    ("Ambidexterity", 5, False, "Physical", "You use both hands equally well and suffer no penalty for using your off hand."),
    ("Animal Empathy", 5, False, "Mental", "You understand animals' motives and can tell when an animal is friendly or hostile. You never kill an animal without good reason."),
    ("Attractive", 4, False, "Physical", "Appearance. +1 to reactions from people who can see you."),
    ("Handsome", 12, False, "Physical", "Appearance (also called Beautiful). +4 to reactions from those attracted to your sex, +2 from everyone else."),
    ("Very Handsome", 16, False, "Physical", "Appearance (also called Very Beautiful). +6 to reactions from those attracted to your sex, +2 from everyone else."),
    ("Charisma", 5, True, "Mental", "+1 per level to reaction rolls from intelligent beings you actively interact with, and to Influence skills."),
    ("Clerical Investment", 5, False, "Social", "You are an ordained priest of a recognized religion, with the rights and duties that go with it. +1 to reactions from followers of your faith."),
    ("Combat Reflexes", 15, False, "Mental", "Extraordinary reactions in a fight. +1 to all active defenses, +2 to Fright Checks, +6 to recover from surprise, never freeze."),
    ("Common Sense", 10, False, "Mental", "The GM warns you (IQ roll) when you are about to do something foolish."),
    ("Danger Sense", 15, False, "Mental", "The GM rolls against your Perception in secret when you face an ambush or hidden danger. On a success you get a warning."),
    ("Daredevil", 15, False, "Mental", "Fortune favors you when you take needless risks: +1 to all skill rolls while doing so, and you may reroll critical failures."),
    ("Empathy", 15, False, "Mental", "You can sense what people are feeling. On an IQ roll you can tell a person's true intentions and whether they are lying."),
    ("Fit", 5, False, "Physical", "+1 to HT rolls to stay conscious, avoid death, resist disease and the like. You recover Fatigue Points twice as fast."),
    ("Very Fit", 15, False, "Physical", "+2 to HT rolls to stay conscious, avoid death, resist disease and the like. You lose Fatigue Points at half the normal rate and recover them twice as fast."),
    ("Hard to Kill", 2, True, "Physical", "+1 per level to HT rolls made to avoid death."),
    ("High Pain Threshold", 10, False, "Physical", "You never suffer shock penalties when injured, and get +3 to HT rolls to avoid being knocked down or stunned."),
    ("Language", 0, False, "Mental", "Speaking and writing a language other than your native one. Per medium (spoken or written): Broken 2, Accented 4, Native 6 points."),
    ("Luck", 15, False, "Mental", "Once per hour of play you may reroll a single roll twice and take the best of the three."),
    ("Extraordinary Luck", 30, False, "Mental", "As Luck, but usable once every 30 minutes of play."),
    ("Ridiculous Luck", 60, False, "Mental", "As Luck, but usable once every 10 minutes of play."),
    ("Magery", 5, True, "Supernatural", "You can sense and use magic. Magery 0 costs 5 points. Each further level costs 10 points and adds +1 to IQ when learning spells."),
    ("Night Vision", 1, True, "Physical", "Each level offsets 1 point of darkness penalty, up to -9."),
    ("Rapid Healing", 5, False, "Physical", "+5 to HT rolls to recover lost Hit Points and to recover from crippling injuries. Requires HT 10+."),
    ("Status", 5, True, "Social", "Your rank in society. Each level gives a +1 reaction bonus from those who recognize it."),
    ("Comfortable", 10, False, "Social", "Wealth. Starting money is twice the campaign average."),
    ("Wealthy", 20, False, "Social", "Wealth. Starting money is five times the campaign average."),
    ("Very Wealthy", 30, False, "Social", "Wealth. Starting money is twenty times the campaign average."),
    ("Filthy Rich", 50, False, "Social", "Wealth. Starting money is a hundred times the campaign average."),
    ("Voice", 10, False, "Physical", "A clear, resonant, attractive voice. +2 to Diplomacy, Fast-Talk, Performance, Public Speaking, Sex Appeal and Singing, and to reactions from those who hear you."),
]

DISADVANTAGES = [
    ("Bad Sight", -25, False, False, "Physical", "Nearsighted or farsighted. -6 to Vision rolls and penalties to tasks at the wrong range. Correctable with glasses at TL5+ (-10 points instead)."),
    ("Bad Temper", -10, False, True, "Mental", "You lose your temper in stressful situations and may say or do things you regret."),
    ("Berserk", -10, False, True, "Mental", "When badly hurt or provoked you may go berserk, attacking without regard for your own safety."),
    ("Bloodlust", -10, False, True, "Mental", "You want your foes dead and finish off fallen enemies unless you resist."),
    ("Code of Honor", -5, False, False, "Mental", "You follow a code of conduct even when it is risky. -5 to -15 points depending on how strict it is."),
    ("Cowardice", -10, False, True, "Mental", "You are very careful about your physical well-being and must resist to put yourself in danger."),
    ("Curious", -5, False, True, "Mental", "You cannot resist investigating anything interesting, even when it is unwise."),
    ("Delusions", -5, False, False, "Mental", "You believe something that is not true. -5 (minor), -10 (major) or -15 (severe)."),
    ("Duty", -5, False, False, "Social", "You are obliged to follow orders from an employer, leader or organization. Cost depends on how often duty calls: -2 to -15."),
    ("Enemies", -5, False, False, "Social", "Someone wants to harm you. Cost depends on the enemy's power and how often they appear."),
    ("Fanaticism", -15, False, False, "Mental", "You believe so strongly in a cause, country or religion that it rules your life."),
    ("Greed", -15, False, True, "Mental", "You lust for wealth and must resist any temptation that promises a payoff."),
    ("Gullibility", -10, False, True, "Mental", "You believe almost anything you are told. -3 to Merchant and to resisting Fast-Talk."),
    ("Hard of Hearing", -10, False, False, "Physical", "-4 to Hearing rolls and to understanding speech."),
    ("Honesty", -10, False, True, "Mental", "You obey the law and expect others to do the same."),
    ("Impulsiveness", -10, False, True, "Mental", "You act first and think later."),
    ("Intolerance", -5, False, False, "Mental", "You dislike people different from you. -5 for one group, -10 for everyone unlike you."),
    ("Jealousy", -10, False, False, "Mental", "You react badly to anyone who seems smarter, more attractive or better off than you."),
    ("Lecherousness", -15, False, True, "Mental", "You have an unusually strong desire for romance."),
    ("Low Pain Threshold", -10, False, False, "Physical", "Double shock penalties, -4 to resist pain and torture."),
    ("Miserliness", -10, False, True, "Mental", "You are reluctant to part with money and haggle over every cent."),
    ("Obsession", -5, False, True, "Mental", "You pursue a single goal above all else. -5 for a short-term goal, -10 for a long-term one."),
    ("Odious Personal Habit", -5, False, False, "Mental", "A habit that annoys others. -5, -10 or -15 for -1, -2 or -3 to reactions."),
    ("One Eye", -15, False, False, "Physical", "-3 to ranged attacks and -1 to melee attacks beyond reach 1. -1 to reactions unless hidden."),
    ("One Hand", -15, False, False, "Physical", "You cannot do things that need two hands; -4 to most tasks that normally use two."),
    ("Overconfidence", -5, False, True, "Mental", "You believe you are more capable than you are."),
    ("Pacifism", -15, False, False, "Mental", "You oppose violence. Reluctant Killer -5, Cannot Harm Innocents -10, Cannot Kill -15, Self-Defense Only -15, Total Nonviolence -30."),
    ("Phobia", -5, False, True, "Mental", "An irrational fear of something. Cost depends on how common the object of fear is."),
    ("Struggling", -10, False, False, "Social", "Wealth. Starting money is half the campaign average."),
    ("Poor", -15, False, False, "Social", "Wealth. Starting money is a fifth of the campaign average."),
    ("Dead Broke", -25, False, False, "Social", "Wealth. You have no job, no income and nothing but the clothes on your back."),
    ("Sense of Duty", -5, False, False, "Mental", "You feel responsible for a group and will never betray them. -2 (a friend) to -20 (all life)."),
    ("Shyness", -5, False, True, "Mental", "You are uncomfortable around strangers. Mild -5, Severe -10, Crippling -20."),
    ("Social Stigma", -5, False, False, "Social", "You belong to a group your society treats as inferior. -5 to -20."),
    ("Truthfulness", -5, False, True, "Mental", "You hate to lie, and are bad at it."),
    ("Unattractive", -4, False, False, "Physical", "Appearance. -1 to reactions."),
    ("Ugly", -8, False, False, "Physical", "Appearance. -2 to reactions."),
    ("Hideous", -16, False, False, "Physical", "Appearance. -4 to reactions."),
    ("Unluckiness", -10, False, False, "Mental", "Once per session, something goes wrong for you at the worst moment, as the GM decides."),
    ("Vow", -5, False, False, "Mental", "A sworn oath to do or not do something. -5 to -15 by how restrictive it is."),
    ("Wounded", -5, False, False, "Physical", "An open wound that never fully heals and is easy to aggravate."),
    ("Quirk", -1, False, False, "Mental", "A minor personal trait. You may take up to five, at -1 point each."),
]

MELEE = [
    ("Axe", "sw+2 cut", "1", "0U", "11", "Axe/Mace", "$50", "4 lb.", ""),
    ("Hatchet", "sw cut", "1", "0", "8", "Axe/Mace", "$40", "2 lb.", "Can be thrown."),
    ("Throwing Axe", "sw+2 cut", "1", "0U", "11", "Axe/Mace", "$60", "4 lb.", "Can be thrown."),
    ("Great Axe", "sw+3 cut", "1, 2", "0U", "12", "Two-Handed Axe/Mace", "$100", "8 lb.", "Two-handed. Unready after attacking."),
    ("Mace", "sw+3 cr", "1", "0U", "12", "Axe/Mace", "$50", "5 lb.", ""),
    ("Small Mace", "sw+2 cr", "1", "0U", "10", "Axe/Mace", "$35", "3 lb.", ""),
    ("Maul", "sw+4 cr", "1, 2", "0U", "13", "Two-Handed Axe/Mace", "$80", "12 lb.", "Two-handed. Unready after attacking."),
    ("Pick", "sw+1 imp", "1", "0U", "10", "Axe/Mace", "$70", "3 lb.", "May get stuck in the target."),
    ("Warhammer", "sw+3 imp", "1", "0U", "12", "Axe/Mace", "$100", "7 lb.", "May get stuck in the target."),
    ("Morningstar", "sw+3 cr", "1", "0F", "12", "Flail", "$80", "6 lb.", "Hard to block or parry."),
    ("Brass Knuckles", "thr cr", "C", "No", "-", "Boxing, Brawling or Karate", "$10", "0.25 lb.", ""),
    ("Punch", "thr-1 cr", "C", "0", "-", "Boxing, Brawling or Karate", "-", "-", "Unarmed."),
    ("Kick", "thr cr", "C, 1", "No", "-", "Brawling or Karate", "-", "-", "Unarmed. Roll at -2."),
    ("Blackjack", "thr cr", "C", "No", "7", "Brawling", "$20", "1 lb.", ""),
    ("Dagger", "thr-1 imp", "C", "-1", "5", "Knife", "$20", "0.25 lb.", "Can be thrown."),
    ("Large Knife", "sw-2 cut / thr imp", "C, 1 / C", "-1", "6", "Knife", "$40", "1 lb.", "Can be thrown."),
    ("Small Knife", "sw-3 cut / thr-1 imp", "C, 1 / C", "-1", "5", "Knife", "$30", "0.5 lb.", "Can be thrown."),
    ("Baton", "sw cr / thr cr", "1", "0", "6", "Shortsword", "$20", "1 lb.", ""),
    ("Shortsword", "sw cut / thr imp", "1", "0", "8", "Shortsword", "$400", "2 lb.", ""),
    ("Broadsword", "sw+1 cut / thr+1 cr", "1", "0", "10", "Broadsword", "$500", "3 lb.", ""),
    ("Thrusting Broadsword", "sw+1 cut / thr+2 imp", "1", "0", "10", "Broadsword", "$600", "3 lb.", ""),
    ("Light Club", "sw+1 cr / thr+1 cr", "1", "0", "10", "Broadsword", "$5", "3 lb.", ""),
    ("Bastard Sword", "sw+1 cut / thr+1 cr", "1, 2 / 2", "0U", "11", "Broadsword", "$650", "5 lb.", "One-handed. Use Two-Handed Sword skill with both hands for +1 damage."),
    ("Greatsword", "sw+3 cut / thr+2 imp", "1, 2 / 2", "0", "12", "Two-Handed Sword", "$800", "7 lb.", "Two-handed."),
    ("Rapier", "thr+1 imp", "1, 2", "0F", "9", "Rapier", "$500", "2.75 lb.", ""),
    ("Saber", "sw-1 cut / thr+1 imp", "1", "0F", "8", "Saber", "$700", "2 lb.", ""),
    ("Smallsword", "thr+1 imp", "1", "0F", "5", "Smallsword", "$400", "1.5 lb.", ""),
    ("Quarterstaff", "sw+2 cr / thr+2 cr", "1, 2", "+2", "7", "Staff", "$10", "4 lb.", "Two-handed."),
    ("Spear", "thr+2 imp", "1", "0", "9", "Spear", "$40", "4 lb.", "Can be thrown. Used two-handed: thr+3 imp, reach 1, 2."),
    ("Halberd", "sw+5 cut / sw+4 imp / thr+3 imp", "2, 3", "0U", "13", "Polearm", "$150", "12 lb.", "Two-handed. Unready after a swing."),
    ("Lance", "thr+3 imp", "4", "No", "12", "Lance", "$60", "6 lb.", "Used from horseback."),
    ("Whip", "sw-2 cr", "1-7", "-2U", "5", "Whip", "$20 per yard", "2 lb. per yard", "Reach equals length in yards."),
]

RANGED = [
    ("Short Bow", "thr imp", "1", "ST x10 / ST x15", "1", "1(2)", "7", "-6", "", "Bow", "$50", "2 lb.", "Two-handed."),
    ("Regular Bow", "thr+1 imp", "2", "ST x15 / ST x20", "1", "1(2)", "10", "-7", "", "Bow", "$100", "2 lb.", "Two-handed."),
    ("Longbow", "thr+2 imp", "3", "ST x15 / ST x20", "1", "1(2)", "11", "-8", "", "Bow", "$200", "3 lb.", "Two-handed."),
    ("Composite Bow", "thr+3 imp", "3", "ST x20 / ST x25", "1", "1(2)", "10", "-7", "", "Bow", "$900", "4 lb.", "Two-handed."),
    ("Crossbow", "thr+4 imp", "4", "ST x20 / ST x25", "1", "1(4)", "7", "-6", "", "Crossbow", "$150", "6 lb.", "Two-handed. ST and damage are the bow's own ST."),
    ("Pistol Crossbow", "thr+2 imp", "1", "ST x20 / ST x25", "1", "1(4)", "7", "-4", "", "Crossbow", "$150", "4 lb.", ""),
    ("Sling", "sw pi", "0", "ST x6 / ST x10", "1", "1(2)", "6", "-4", "", "Sling", "$20", "0.5 lb.", "Fires stones or lead bullets."),
    ("Thrown Dagger", "thr-1 imp", "0", "ST x0.5 / ST x1", "1", "T(1)", "5", "-1", "", "Thrown Weapon (Knife)", "$20", "0.25 lb.", ""),
    ("Thrown Large Knife", "thr imp", "0", "ST x0.8 / ST x1.5", "1", "T(1)", "6", "-2", "", "Thrown Weapon (Knife)", "$40", "1 lb.", ""),
    ("Thrown Hatchet", "sw cut", "2", "ST x1.5 / ST x2.5", "1", "T(1)", "8", "-2", "", "Thrown Weapon (Axe/Mace)", "$40", "2 lb.", ""),
    ("Thrown Throwing Axe", "sw+2 cut", "2", "ST x1 / ST x1.5", "1", "T(1)", "11", "-3", "", "Thrown Weapon (Axe/Mace)", "$60", "4 lb.", ""),
    ("Javelin", "thr+1 imp", "3", "ST x1.5 / ST x2.5", "1", "T(1)", "6", "-4", "", "Thrown Weapon (Spear)", "$30", "2 lb.", ""),
    ("Thrown Spear", "thr+3 imp", "2", "ST x1 / ST x1.5", "1", "T(1)", "9", "-6", "", "Thrown Weapon (Spear)", "$40", "4 lb.", ""),
    ("Small Revolver, .38", "2d-1 pi", "1", "120 / 1,500", "3", "5(3i)", "8", "-1", "2", "Guns (Pistol)", "$400", "1.5 lb.", ""),
    ("Large Revolver, .44M", "3d pi+", "2", "200 / 2,500", "3", "6(3i)", "11", "-3", "4", "Guns (Pistol)", "$900", "3.25 lb.", ""),
    ("Auto Pistol, 9mm", "2d+2 pi", "2", "150 / 1,850", "3", "15+1(3)", "9", "-2", "2", "Guns (Pistol)", "$600", "2.5 lb.", ""),
    ("Pump Shotgun, 12G", "1d+1 pi", "3", "50 / 125", "2x9", "7+1(2i)", "10", "-5", "1", "Guns (Shotgun)", "$240", "8 lb.", "Two-handed. Fires nine pellets per shot."),
    ("Hunting Rifle, .30-06", "7d pi", "5", "1,000 / 4,200", "1", "5+1(3)", "10", "-5", "2", "Guns (Rifle)", "$700", "9 lb.", "Two-handed."),
    ("Assault Rifle, 5.56mm", "5d pi", "5", "500 / 3,500", "12", "30+1(3)", "9", "-4", "2", "Guns (Rifle)", "$900", "9 lb.", "Two-handed. Full auto."),
]

ARMOUR = [
    ("Cloth Armor", "1", 0, "torso, groin", "$30", "6 lb.", "Padded cloth."),
    ("Leather Jacket", "1", 0, "torso, arms", "$50", "4 lb.", ""),
    ("Leather Armor", "2", 0, "torso, groin", "$100", "10 lb.", ""),
    ("Leather Leggings", "2", 0, "legs", "$60", "4 lb.", ""),
    ("Leather Helm", "2", 0, "skull, face", "$20", "3 lb.", ""),
    ("Leather Gloves", "2", 0, "hands", "$30", "0 lb.", ""),
    ("Boots", "2", 0, "feet", "$80", "3 lb.", ""),
    ("Light Scale Armor", "3", 0, "torso, groin", "$150", "15 lb.", ""),
    ("Scale Armor", "4", 0, "torso, groin", "$550", "35 lb.", ""),
    ("Mail Shirt", "4/2", 0, "torso", "$150", "16 lb.", "DR 2 against crushing."),
    ("Mail Hauberk", "4/2", 0, "torso, groin", "$230", "25 lb.", "DR 2 against crushing."),
    ("Mail Coif", "4/2", 0, "skull, neck", "$55", "4 lb.", "DR 2 against crushing."),
    ("Mail Leggings", "4/2", 0, "legs", "$110", "15 lb.", "DR 2 against crushing."),
    ("Steel Breastplate", "5", 0, "torso", "$500", "18 lb.", "Front only."),
    ("Steel Corselet", "6", 0, "torso, groin", "$1,300", "35 lb.", ""),
    ("Plate Arms", "6", 0, "arms", "$1,000", "20 lb.", ""),
    ("Plate Legs", "6", 0, "legs", "$1,100", "20 lb.", ""),
    ("Pot Helm", "4", 0, "skull", "$100", "5 lb.", ""),
    ("Greathelm", "7", 0, "skull, face, neck", "$340", "10 lb.", "-7 to Hearing and Vision rolls."),
    ("Gauntlets", "4", 0, "hands", "$100", "2 lb.", ""),
    ("Sollerets", "4", 0, "feet", "$150", "7 lb.", ""),
    ("Ballistic Vest", "12/5", 0, "torso", "$400", "2 lb.", "DR 5 against crushing and cutting. Concealable."),
    ("Buckler", "0", 1, "shield", "$25", "2 lb.", "Uses Shield (Buckler) skill."),
    ("Small Shield", "0", 1, "shield", "$40", "8 lb.", "DR 6, 30 HP."),
    ("Medium Shield", "0", 2, "shield", "$60", "15 lb.", "DR 7, 40 HP."),
    ("Large Shield", "0", 3, "shield", "$90", "25 lb.", "DR 9, 60 HP. -2 to Stealth."),
]

ITEMS = [
    ("Backpack, Small", "$60", "3 lb.", "Holds 40 lb. of gear."),
    ("Backpack, Frame", "$100", "10 lb.", "Holds 100 lb. of gear."),
    ("Bedroll", "$25", "7 lb.", ""),
    ("Blanket", "$20", "4 lb.", ""),
    ("Candle", "$5", "1 lb.", "Burns for 12 hours."),
    ("Crowbar", "$20", "3 lb.", "Can be used as a club."),
    ("Grapnel", "$20", "2 lb.", "Can be thrown up to ST x2 yards."),
    ("Lantern", "$20", "2 lb.", "Burns for 24 hours on a pint of oil."),
    ("Lamp Oil, 1 pint", "$2", "1 lb.", ""),
    ("Personal Basics", "$5", "1 lb.", "Utensils, toiletries, and the like. Without them you have -1 to Survival and similar rolls."),
    ("Pouch or Purse", "$10", "0.2 lb.", ""),
    ("Rope, 10 yards", "$5", "1.5 lb.", "Supports 300 lb."),
    ("Heavy Rope, 10 yards", "$25", "5 lb.", "Supports 1,100 lb."),
    ("Tent, One Person", "$50", "5 lb.", ""),
    ("Tent, Four Person", "$150", "30 lb.", ""),
    ("Torch", "$3", "1 lb.", "Burns for 1 hour."),
    ("Wineskin", "$10", "0.25 lb.", "Holds a gallon of liquid."),
    ("Lockpicks", "$50", "0.1 lb.", "Needed for Lockpicking without penalty."),
    ("First Aid Kit", "$50", "2 lb.", "+1 to First Aid."),
    ("Flashlight", "$10", "1 lb.", "Lights a 30-yard beam."),
    ("Binoculars", "$400", "2 lb.", "Magnifies distant objects."),
    ("Cell Phone", "$250", "0.25 lb.", ""),
    ("Laptop Computer", "$1,000", "5 lb.", ""),
]

SKILLS = [
    ("Acrobatics", "DX", "Hard", "DX-6"),
    ("Acting", "IQ", "Average", "IQ-5"),
    ("Animal Handling", "IQ", "Average", "IQ-5"),
    ("Area Knowledge", "IQ", "Easy", "IQ-4"),
    ("Armoury", "IQ", "Average", "IQ-5"),
    ("Axe/Mace", "DX", "Average", "DX-5"),
    ("Bow", "DX", "Average", "DX-5"),
    ("Boxing", "DX", "Average", "None"),
    ("Brawling", "DX", "Easy", "None"),
    ("Broadsword", "DX", "Average", "DX-5"),
    ("Camouflage", "IQ", "Easy", "IQ-4"),
    ("Carousing", "HT", "Easy", "HT-4"),
    ("Climbing", "DX", "Average", "DX-5"),
    ("Computer Operation", "IQ", "Easy", "IQ-4"),
    ("Computer Programming", "IQ", "Hard", "None"),
    ("Cooking", "IQ", "Average", "IQ-5"),
    ("Crossbow", "DX", "Easy", "DX-4"),
    ("Current Affairs", "IQ", "Easy", "IQ-4"),
    ("Diagnosis", "IQ", "Hard", "IQ-6"),
    ("Diplomacy", "IQ", "Hard", "IQ-6"),
    ("Disguise", "IQ", "Average", "IQ-5"),
    ("Driving", "DX", "Average", "DX-5, IQ-5"),
    ("Electronics Operation", "IQ", "Average", "IQ-5"),
    ("Engineer", "IQ", "Hard", "None"),
    ("Escape", "DX", "Hard", "DX-6"),
    ("Explosives", "IQ", "Average", "IQ-5"),
    ("Fast-Draw", "DX", "Easy", "None"),
    ("Fast-Talk", "IQ", "Average", "IQ-5"),
    ("First Aid", "IQ", "Easy", "IQ-4"),
    ("Fishing", "Per", "Easy", "Per-4"),
    ("Flail", "DX", "Hard", "DX-6"),
    ("Forgery", "IQ", "Hard", "IQ-5"),
    ("Gambling", "IQ", "Average", "IQ-5"),
    ("Guns", "DX", "Easy", "DX-4"),
    ("Hiking", "HT", "Average", "HT-5"),
    ("History", "IQ", "Hard", "IQ-6"),
    ("Holdout", "IQ", "Average", "IQ-5"),
    ("Interrogation", "IQ", "Average", "IQ-5"),
    ("Intimidation", "Will", "Average", "Will-5"),
    ("Jumping", "DX", "Easy", "None"),
    ("Karate", "DX", "Hard", "None"),
    ("Knife", "DX", "Easy", "DX-4"),
    ("Lance", "DX", "Average", "DX-5"),
    ("Law", "IQ", "Hard", "IQ-6"),
    ("Leadership", "IQ", "Average", "IQ-5"),
    ("Lockpicking", "IQ", "Average", "IQ-5"),
    ("Mathematics", "IQ", "Hard", "IQ-6"),
    ("Mechanic", "IQ", "Average", "IQ-5"),
    ("Merchant", "IQ", "Average", "IQ-5"),
    ("Musical Instrument", "IQ", "Hard", "None"),
    ("Naturalist", "IQ", "Hard", "IQ-6"),
    ("Navigation", "IQ", "Average", "IQ-5"),
    ("Observation", "Per", "Average", "Per-5"),
    ("Occultism", "IQ", "Average", "IQ-5"),
    ("Physician", "IQ", "Hard", "IQ-7"),
    ("Pickpocket", "DX", "Hard", "DX-6"),
    ("Piloting", "DX", "Average", "IQ-6"),
    ("Polearm", "DX", "Average", "DX-5"),
    ("Psychology", "IQ", "Hard", "IQ-6"),
    ("Public Speaking", "IQ", "Average", "IQ-5"),
    ("Rapier", "DX", "Average", "DX-5"),
    ("Research", "IQ", "Average", "IQ-5"),
    ("Riding", "DX", "Average", "DX-5"),
    ("Running", "HT", "Average", "HT-5"),
    ("Saber", "DX", "Average", "DX-5"),
    ("Savoir-Faire", "IQ", "Easy", "IQ-4"),
    ("Scrounging", "Per", "Easy", "Per-4"),
    ("Search", "Per", "Average", "Per-5"),
    ("Sex Appeal", "HT", "Average", "HT-3"),
    ("Shadowing", "IQ", "Average", "IQ-5"),
    ("Shield", "DX", "Easy", "DX-4"),
    ("Shortsword", "DX", "Average", "DX-5"),
    ("Singing", "HT", "Easy", "HT-4"),
    ("Sleight of Hand", "DX", "Hard", "None"),
    ("Sling", "DX", "Hard", "DX-6"),
    ("Smallsword", "DX", "Average", "DX-5"),
    ("Spear", "DX", "Average", "DX-5"),
    ("Staff", "DX", "Average", "DX-5"),
    ("Stealth", "DX", "Average", "DX-5, IQ-5"),
    ("Streetwise", "IQ", "Average", "IQ-5"),
    ("Surgery", "IQ", "Very Hard", "None"),
    ("Survival", "Per", "Average", "Per-5"),
    ("Swimming", "HT", "Easy", "HT-4"),
    ("Tactics", "IQ", "Hard", "IQ-6"),
    ("Teaching", "IQ", "Average", "IQ-5"),
    ("Thrown Weapon", "DX", "Easy", "DX-4"),
    ("Tracking", "Per", "Average", "Per-5"),
    ("Traps", "IQ", "Average", "IQ-5"),
    ("Two-Handed Axe/Mace", "DX", "Average", "DX-5"),
    ("Two-Handed Sword", "DX", "Average", "DX-5"),
    ("Whip", "DX", "Average", "DX-5"),
    ("Wrestling", "DX", "Average", "None"),
    ("Writing", "IQ", "Average", "IQ-5"),
]


def build():
    entities = []
    for name, points, per_level, kind, text in ADVANTAGES:
        entities.append(entity("Advantage", name, text, {
            "advantageStats": {"Stats": {"Points": points, "Per level": per_level, "Type": kind}}
        }))
    for name, points, per_level, self_control, kind, text in DISADVANTAGES:
        entities.append(entity("Disadvantage", name, text, {
            "disadvantageStats": {"Stats": {"Points": points, "Per level": per_level, "Self control": self_control, "Type": kind}}
        }))
    for name, damage, reach, parry, st, skill, cost, weight, notes in MELEE:
        entities.append(entity("Melee weapons", name, notes, {
            "meleeWeaponStats": {"Stats": {
                "Damage": damage, "Reach": reach, "Parry": parry, "ST": st,
                "Skill": skill, "Cost": cost, "Weight": weight, "Notes": notes,
            }}
        }))
    for name, damage, acc, range_, rof, shots, st, bulk, rcl, skill, cost, weight, notes in RANGED:
        entities.append(entity("Ranged weapons", name, notes, {
            "rangedWeaponStats": {"Stats": {
                "Damage": damage, "Acc": acc, "Range": range_, "RoF": rof, "Shots": shots,
                "ST": st, "Bulk": bulk, "Rcl": rcl, "Skill": skill, "Cost": cost,
                "Weight": weight, "Notes": notes,
            }}
        }))
    for name, dr, db, location, cost, weight, notes in ARMOUR:
        entities.append(entity("Armour", name, notes, {
            "armourStats": {"Stats": {
                "DR": dr, "DB": db, "Location": location, "Cost": cost, "Weight": weight, "Notes": notes,
            }}
        }))
    for name, cost, weight, text in ITEMS:
        entities.append(entity("Other items", name, text, {
            "itemStats": {"Stats": {"Cost": cost, "Weight": weight}}
        }))
    for name, attribute, difficulty, defaults in SKILLS:
        short = {"Easy": "E", "Average": "A", "Hard": "H", "Very Hard": "VH"}[difficulty]
        entities.append(entity("Skills", name, f"{attribute}/{short}. Defaults: {defaults}.", {
            "skillStats": {"Training": {"Points": 1}, "Stats": {"Attribute": attribute, "Difficulty": difficulty, "Defaults": defaults}}
        }))
    return {
        "name": "GURPS Lite",
        "description": "Advantages, disadvantages, skills and equipment from GURPS Lite (Fourth Edition). " + NOTICE,
        "url": "/systems/Gurps/gurpslite.json",
        "gamemaster": "",
        "entities": entities,
    }


json.dump(build(), open(OUT, "w"), separators=(",", ":"))
