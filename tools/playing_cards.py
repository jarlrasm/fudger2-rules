"""Draws the standard playing cards as SVG and writes the decks that use them.

Run from the repo root: python3 tools/playing_cards.py
It writes systems/cards/images/*.svg and systems/cards/standard.json.
"""
import json
import os

OUT = "systems/cards"
URL = "/systems/cards"
W, H = 250, 350
RED, BLACK = "#c8102e", "#1b1b1b"
GOLD, SKIN, PAPER = "#d9a520", "#f4dcb8", "#fffdf8"
FONT = "Georgia, 'Times New Roman', serif"

RANKS = [("2", "2"), ("3", "3"), ("4", "4"), ("5", "5"), ("6", "6"), ("7", "7"), ("8", "8"), ("9", "9"), ("10", "10"),
         ("J", "Jack"), ("Q", "Queen"), ("K", "King"), ("A", "Ace")]
SUITS = [("C", "Clubs", BLACK), ("D", "Diamonds", RED), ("H", "Hearts", RED), ("S", "Spades", BLACK)]

# Each suit drawn in a 100 by 100 box.
SUIT_PATHS = {
    "H": '<path d="M50 92C22 68 2 50 2 27C2 12 14 2 28 2C39 2 46 9 50 19C54 9 61 2 72 2C86 2 98 12 98 27C98 50 78 68 50 92Z"/>',
    "D": '<path d="M50 2L86 50L50 98L14 50Z"/>',
    "S": '<path d="M50 2C36 26 2 40 2 63C2 77 13 86 25 86C34 86 41 81 46 74C45 85 40 93 31 98L69 98C60 93 55 85 54 74C59 81 66 86 75 86C87 86 98 77 98 63C98 40 64 26 50 2Z"/>',
    "C": '<circle cx="50" cy="27" r="22"/><circle cx="25" cy="60" r="22"/><circle cx="75" cy="60" r="22"/>'
         '<circle cx="50" cy="55" r="12"/><path d="M46 58C45 78 40 91 31 98L69 98C60 91 55 78 54 58Z"/>',
}

# Where the pips go on number cards, as (x, y); pips below the middle are drawn upside down.
COL_L, COL_M, COL_R = 82, 125, 168
PIPS = {
    "2": [(COL_M, 78), (COL_M, 272)],
    "3": [(COL_M, 78), (COL_M, 175), (COL_M, 272)],
    "4": [(COL_L, 78), (COL_R, 78), (COL_L, 272), (COL_R, 272)],
    "5": [(COL_L, 78), (COL_R, 78), (COL_M, 175), (COL_L, 272), (COL_R, 272)],
    "6": [(COL_L, 78), (COL_R, 78), (COL_L, 175), (COL_R, 175), (COL_L, 272), (COL_R, 272)],
    "7": [(COL_L, 78), (COL_R, 78), (COL_M, 126), (COL_L, 175), (COL_R, 175), (COL_L, 272), (COL_R, 272)],
    "8": [(COL_L, 78), (COL_R, 78), (COL_M, 126), (COL_L, 175), (COL_R, 175), (COL_M, 224), (COL_L, 272), (COL_R, 272)],
    "9": [(COL_L, 78), (COL_R, 78), (COL_L, 143), (COL_R, 143), (COL_M, 175), (COL_L, 207), (COL_R, 207), (COL_L, 272), (COL_R, 272)],
    "10": [(COL_L, 78), (COL_R, 78), (COL_M, 110), (COL_L, 143), (COL_R, 143), (COL_L, 207), (COL_R, 207), (COL_M, 240), (COL_L, 272), (COL_R, 272)],
}


def svg(body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
            f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="{PAPER}" stroke="#bbb" stroke-width="2"/>'
            f'{body}</svg>\n')


def pip(suit, x, y, size, color, flip=False):
    scale = size / 100
    turn = f" rotate(180 50 50)" if flip else ""
    return f'<g fill="{color}" transform="translate({x - size / 2} {y - size / 2}) scale({scale}){turn}">{SUIT_PATHS[suit]}</g>'


def corners(label, suit, color):
    size = 30 if len(label) == 1 else 26
    spacing = ' letter-spacing="-3"' if len(label) > 1 else ""
    index = (f'<text x="24" y="42" font-family="{FONT}" font-weight="bold" font-size="{size}" fill="{color}" text-anchor="middle"{spacing}>{label}</text>'
             + pip(suit, 24, 60, 20, color))
    return index + f'<g transform="rotate(180 {W / 2} {H / 2})">{index}</g>'


def number_card(rank, suit, color):
    pips = "".join(pip(suit, x, y, 42, color, y > H / 2) for x, y in PIPS[rank])
    return svg(corners(rank, suit, color) + pips)


def ace(suit, color):
    flourish = f'<circle cx="125" cy="175" r="70" fill="none" stroke="{color}" stroke-width="2" stroke-dasharray="2 6" opacity="0.6"/>'
    return svg(corners("A", suit, color) + flourish + pip(suit, 125, 175, 96, color))


def headwear(rank, color):
    if rank == "K":
        return (f'<path d="M100 98L98 66L112 82L125 60L138 82L152 66L150 98Z" fill="{GOLD}" stroke="#7a5a10" stroke-width="2"/>'
                f'<circle cx="125" cy="60" r="4" fill="{color}"/><circle cx="98" cy="66" r="3" fill="{color}"/><circle cx="152" cy="66" r="3" fill="{color}"/>')
    if rank == "Q":
        return (f'<path d="M101 100C96 120 92 140 96 152L108 150C104 136 106 118 108 104Z" fill="#6b3d1f"/>'
                f'<path d="M149 100C154 120 158 140 154 152L142 150C146 136 144 118 142 104Z" fill="#6b3d1f"/>'
                f'<path d="M104 94L108 78L117 88L125 74L133 88L142 78L146 94Z" fill="{GOLD}" stroke="#7a5a10" stroke-width="2"/>'
                f'<circle cx="125" cy="80" r="3.5" fill="{color}"/>')
    return (f'<path d="M100 98C100 78 112 70 125 70C140 70 152 78 152 98Z" fill="{color}" stroke="#222" stroke-width="1.5"/>'
            f'<rect x="96" y="94" width="60" height="8" rx="3" fill="{GOLD}"/>'
            f'<path d="M148 92C160 74 172 62 186 58C178 70 166 82 152 96Z" fill="#fff" stroke="#888" stroke-width="1"/>')


def face_half(rank, suit, color):
    """The top half of a court card; the bottom half is the same, turned round."""
    robe = (f'<path d="M66 175C70 150 86 134 106 130L144 130C164 134 180 150 184 175Z" fill="{color}"/>'
            f'<path d="M80 175C84 158 92 148 104 144L104 175Z" fill="{GOLD}" opacity="0.85"/>'
            f'<path d="M170 175C166 158 158 148 146 144L146 175Z" fill="{GOLD}" opacity="0.85"/>'
            f'<path d="M106 130L125 160L144 130Z" fill="#fff" stroke="#999" stroke-width="1"/>')
    head = (f'<circle cx="125" cy="112" r="21" fill="{SKIN}" stroke="#8a6a4a" stroke-width="1.5"/>'
            f'<circle cx="117" cy="110" r="2.2" fill="#222"/><circle cx="133" cy="110" r="2.2" fill="#222"/>'
            f'<path d="M118 121Q125 126 132 121" fill="none" stroke="#8a4a3a" stroke-width="1.6"/>')
    beard = '<path d="M106 116C108 136 118 142 125 142C132 142 142 136 144 116C138 126 112 126 106 116Z" fill="#8a8a8a"/>' if rank == "K" else ""
    sign = pip(suit, 70, 64, 24, color)
    figure = f'<g transform="translate(125 175) scale(1.12) translate(-125 -175)">{robe + head + beard + headwear(rank, color)}</g>'
    return figure + sign


def court(rank, suit, color):
    half = face_half(rank, suit, color)
    frame = (f'<rect x="48" y="40" width="154" height="270" rx="6" fill="#fbf1dc" stroke="{color}" stroke-width="3"/>'
             f'<clipPath id="f"><rect x="48" y="40" width="154" height="270" rx="6"/></clipPath>')
    figure = f'<g clip-path="url(#f)">{half}<g transform="rotate(180 {W / 2} {H / 2})">{half}</g></g>'
    line = f'<line x1="48" y1="175" x2="202" y2="175" stroke="{color}" stroke-width="2"/>'
    return svg(corners(rank, suit, color) + frame + figure + line)


def joker(color, accent):
    letters = "".join(f'<text x="22" y="{40 + i * 22}" font-family="{FONT}" font-weight="bold" font-size="20" fill="{color}" text-anchor="middle">{c}</text>'
                      for i, c in enumerate("JOKER"))
    side = letters + f'<g transform="rotate(180 {W / 2} {H / 2})">{letters}</g>'
    hat = (f'<path d="M90 150C84 118 62 98 46 96C70 108 86 126 96 148Z" fill="{accent}"/>'
           f'<path d="M110 146C108 108 116 78 125 62C134 78 142 108 140 146Z" fill="{color}"/>'
           f'<path d="M160 150C166 118 188 98 204 96C180 108 164 126 154 148Z" fill="{accent}"/>'
           f'<circle cx="46" cy="96" r="7" fill="{GOLD}"/><circle cx="125" cy="62" r="7" fill="{GOLD}"/><circle cx="204" cy="96" r="7" fill="{GOLD}"/>'
           f'<path d="M86 150Q125 136 164 150L164 160Q125 146 86 160Z" fill="{GOLD}"/>')
    head = (f'<circle cx="125" cy="188" r="32" fill="{SKIN}" stroke="#8a6a4a" stroke-width="1.5"/>'
            f'<path d="M108 182Q113 176 118 182" fill="none" stroke="#222" stroke-width="2.4"/>'
            f'<path d="M132 182Q137 176 142 182" fill="none" stroke="#222" stroke-width="2.4"/>'
            f'<path d="M106 198Q125 220 144 198" fill="none" stroke="{RED}" stroke-width="3"/>'
            f'<circle cx="125" cy="192" r="4" fill="{RED}"/>')
    collar = "".join(f'<path d="M{x} 226L{x + 15} 258L{x + 30} 226Z" fill="{color if i % 2 == 0 else accent}"/>'
                     for i, x in enumerate(range(80, 170, 30)))
    return svg(side + hat + head + collar + f'<circle cx="125" cy="292" r="5" fill="{GOLD}"/>')


def back():
    lattice = ('<pattern id="p" width="20" height="20" patternUnits="userSpaceOnUse">'
               '<path d="M10 0L20 10L10 20L0 10Z" fill="none" stroke="#e8c770" stroke-width="1.2"/>'
               '<circle cx="10" cy="10" r="1.6" fill="#e8c770"/></pattern>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"><defs>{lattice}</defs>'
            f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="{PAPER}" stroke="#bbb" stroke-width="2"/>'
            f'<rect x="14" y="14" width="{W - 28}" height="{H - 28}" rx="8" fill="#7a1424"/>'
            f'<rect x="14" y="14" width="{W - 28}" height="{H - 28}" rx="8" fill="url(#p)"/>'
            f'<rect x="20" y="20" width="{W - 40}" height="{H - 40}" rx="6" fill="none" stroke="#e8c770" stroke-width="2"/>'
            f'<circle cx="125" cy="175" r="46" fill="#7a1424" stroke="#e8c770" stroke-width="3"/>'
            + "".join(pip(s, x, y, 26, "#e8c770") for s, x, y in [("S", 125, 150), ("H", 150, 175), ("C", 100, 175), ("D", 125, 200)])
            + '</svg>\n')


def write(name, content):
    with open(f"{OUT}/images/{name}.svg", "w", encoding="utf-8") as f:
        f.write(content)
    return f"{URL}/images/{name}.svg"


def card(name, image):
    return {"name": name, "text": "", "copies": 1, "image": image, "fullImage": True}


def main():
    os.makedirs(f"{OUT}/images", exist_ok=True)
    plain = []
    for label, rank in RANKS:
        for code, suit, color in SUITS:
            if label == "A":
                content = ace(code, color)
            elif label in "JQK":
                content = court(label, code, color)
            else:
                content = number_card(label, code, color)
            plain.append(card(f"{rank} of {suit}", write(f"{label}{code}", content)))
    jokers = [card("Red Joker", write("joker-red", joker(RED, GOLD))),
              card("Black Joker", write("joker-black", joker(BLACK, "#777")))]
    back_url = write("back", back())
    settings = {"whoDraws": "anyone", "drawTo": "hand", "gmSeesHands": True}

    def deck(name, description, cards):
        return {"type": "Decks", "name": name, "description": description, "images": {back_url: "image/svg+xml"},
                "mainImage": back_url, "rulesets": [], "cards": cards, "settings": settings}

    library = {
        "name": "Playing cards",
        "description": "Standard French-suited playing cards: a 52-card deck, and a 54-card deck with a red and a black Joker.",
        "url": f"{URL}/standard.json",
        "gamemaster": "",
        "entities": [
            deck("52-card deck", "A standard deck: Ace, 2 to 10, Jack, Queen and King in clubs, diamonds, hearts and spades.", plain),
            deck("54-card deck", "A standard deck with two Jokers, one red and one black.", plain + jokers),
        ],
    }
    with open(f"{OUT}/standard.json", "w", encoding="utf-8") as f:
        json.dump(library, f, indent=1, ensure_ascii=False)
        f.write("\n")


main()
