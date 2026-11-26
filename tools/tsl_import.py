"""Builds the Thirsty Sword Lesbians library from the Sapphic Reference Document.

April Kit Walsh and Evil Hat Productions publish the text of Thirsty Sword
Lesbians as the Sapphic Reference Document at https://poweredbylesbians.com/srd/
under CC BY-SA 4.0 (with the additional terms on
https://poweredbylesbians.com/license/). This reads the saved HTML of the basic
moves page and the nine playbook pages and writes the basic moves, every
playbook move, playbook feature move and Truth of Heart and Blade, and the
nine playbooks with their stat columns, aesthetics and features. Only the
format changes; the moves keep the SRD's own words, and the commentary and
examples of play are left out.

Save the pages first, one file each, named after the last part of the URL:

    mkdir srd && cd srd
    curl -sL -o basic-moves.html https://poweredbylesbians.com/srd/basic-moves/
    for p in beast chosen devoted infamous nature-witch scoundrel seeker spooky-witch trickster; do
        curl -sL -o $p.html https://poweredbylesbians.com/srd/playbooks/$p/
    done
    cd .. && python3 -I tools/tsl_import.py srd systems/tsl/tsl.json
"""

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

SOURCE = Path(sys.argv[1])
OUT = sys.argv[2]
SYSTEM = "ThirstySwordLesbians"
PLAYBOOKS = ["beast", "chosen", "devoted", "infamous", "nature-witch", "scoundrel", "seeker", "spooky-witch", "trickster"]
STATS = ["Daring", "Grace", "Heart", "Wit", "Spirit"]


class Blocks(HTMLParser):
    """The article as a list of (tag, depth, text, mark) blocks; mark is
    "check" or "box" for a paragraph that starts with a move's tick box."""

    def __init__(self):
        super().__init__()
        self.blocks = []
        self.current = None
        self.depth = 0
        self.skip = 0
        self.inside = False
        self.cells = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("script", "style", "nav", "svg", "footer"):
            self.skip += 1
        if tag == "article" or (tag == "main"):
            self.inside = True
        if self.skip or not self.inside:
            return
        if tag in ("ul", "ol"):
            self.depth += 1
        if tag == "tr":
            self.flush()
            self.cells = []
        if tag in ("h1", "h2", "h3", "h4", "h5", "p", "li", "td", "th"):
            self.flush()
            self.current = [tag, self.depth, [], None]
        if tag == "i" and self.current is not None and "fa-square" in attrs.get("class", ""):
            self.current[3] = "check" if "square-check" in attrs["class"] else "box"
        if tag in ("strong", "b") and self.current is not None:
            self.current[2].append("**")
        if tag == "br" and self.current is not None:
            self.current[2].append(" ")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "svg", "footer"):
            self.skip -= 1
            return
        if self.skip or not self.inside:
            return
        if tag in ("strong", "b") and self.current is not None:
            self.current[2].append("**")
        if tag in ("h1", "h2", "h3", "h4", "h5", "p", "li", "td", "th"):
            self.flush()
        if tag == "tr":
            self.blocks.append(("tr", self.depth, " / ".join(self.cells), None))
            self.cells = []
        if tag in ("ul", "ol"):
            self.depth -= 1
        if tag in ("article", "main"):
            self.flush()
            self.inside = False

    def handle_data(self, data):
        if self.skip or not self.inside:
            return
        if self.current is None:
            if data.strip():
                self.current = ["p", self.depth, [], None]
            else:
                return
        self.current[2].append(data)

    def flush(self):
        if self.current is None:
            return
        tag, depth, parts, mark = self.current
        text = clean("".join(parts))
        if tag in ("td", "th"):
            self.cells.append(text)
        elif text or mark:
            self.blocks.append((tag, depth, text, mark))
        self.current = None


def clean(value):
    value = value.replace("’", "'").replace("‘", "'").replace("“", "'").replace("”", "'")
    value = value.replace("—", " - ").replace("–", "-").replace(" ", " ").replace('"', "'")
    value = re.sub(r"\*\*\s*\*\*", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def blocks_of(name):
    parser = Blocks()
    parser.feed((SOURCE / (name + ".html")).read_text(encoding="utf-8"))
    parser.flush()
    return parser.blocks


def tracks(blocks):
    """A track drawn as a list, such as Feral 0 1 2 3 4, becomes one line."""
    out = []
    i = 0
    while i < len(blocks):
        tag, depth, text, mark = blocks[i]
        j = i + 1
        while j < len(blocks) and blocks[j][0] == "li" and re.fullmatch(r"[0-9]+", blocks[j][2]):
            j += 1
        if tag == "li" and j - i > 2:
            out.append(("p", 0, "**" + text + ":** " + " ".join(b[2] for b in blocks[i + 1:j]), None))
            i = j
        else:
            out.append(blocks[i])
            i += 1
    return out


def as_markdown(blocks):
    lines = []
    for tag, depth, text, _ in tracks(blocks):
        if tag == "li" or tag == "tr":
            lines.append("  " * max(0, depth - 1) + "- " + text)
        else:
            if lines and not lines[-1].startswith(" ") and lines[-1] != "":
                lines.append("")
            lines.append(text)
    return "\n".join(lines).strip()


def stats_of(text):
    found = [s for s in STATS if re.search(r"\+\s*\**" + s, text)]
    if re.search(r"\+\s*\**Conditions", text):
        found.append("Conditions")
    return ", ".join(found)


def entity(kind, name, description, ruleset, stats):
    return {
        "type": kind,
        "name": name,
        "description": description,
        "images": {},
        "rulesets": [{"system": SYSTEM, "implementation": {ruleset: {"Stats": stats}}}],
    }


def move(name, description, playbook, kind, starting):
    return entity("Moves", name, description, "moveStats", {
        "Playbook": playbook,
        "Kind": kind,
        "Stat": stats_of(description),
        "Starting": starting,
    })


BASIC_GROUPS = {"Danger Moves": "Basic", "Heartstring Moves": "Basic", "Recovery Moves": "Basic", "Special Moves": "Special"}


def basic_moves():
    blocks = blocks_of("basic-moves")
    out = []
    group = None
    name = None
    body = []
    listed = False

    def finish():
        if name:
            out.append(move(name.replace(" (Reactive Move)", ""), as_markdown(body), "Basic", BASIC_GROUPS[group], True))

    for tag, depth, text, mark in blocks:
        if tag == "h2":
            finish()
            name = None
            group = text if text in BASIC_GROUPS else None
        elif tag == "h3" and group:
            finish()
            name, body, listed = text, [], False
        elif tag in ("h4", "h5"):
            finish()
            name = None
        elif name:
            if tag == "li":
                listed = True
                body.append((tag, depth, text, mark))
            elif listed and len(text) > 160:
                finish()
                name = None
            else:
                body.append((tag, depth, text, mark))
    finish()
    return out


MOVE_START = re.compile(r"^\*\*([^*]+?):?\*\*:?\s*(.*)$")
SECTION_KIND = {"Playbook Moves": "Playbook", "Truths of Heart and Blade": "Truth"}


def playbook(slug):
    blocks = blocks_of(slug)
    title = next(text for tag, _, text, _ in blocks if tag == "h1")
    sections = []
    current = ("", [])
    for block in blocks:
        if block[0] == "h2":
            sections.append(current)
            current = (block[2], [])
        else:
            current[1].append(block)
    sections.append(current)

    intro = [b for b in sections[0][1] if b[0] != "h1" and b[2] not in ("Thirsty Sword Lesbians SRD", "Game Rules", "Licensing")]
    archetypes = [b[2] for b in intro if b[0] == "li"]
    summary = [b[2] for b in intro if b[0] == "p" and "Example Archetypes" not in b[2]]
    sets = {}
    aesthetics = []
    features = []
    moves = []
    for heading, body in sections[1:]:
        if heading == "Aesthetics":
            aesthetics = [b[2] for b in body if b[0] == "li"]
        elif heading == "Stats":
            for b in body:
                cells = b[2].split(" / ")
                if b[0] == "tr" and cells[0] in STATS and len(cells) == 3:
                    sets[cells[0]] = (cells[1], cells[2])
        elif heading.startswith("Playing the"):
            continue
        else:
            kind = SECTION_KIND.get(heading, "Feature")
            plain = []
            name = None
            mbody = []
            starting = False

            def finish():
                if name:
                    moves.append(move(name, as_markdown(mbody), title, kind, starting))

            for tag, depth, text, mark in body:
                m = MOVE_START.match(text) if tag == "p" else None
                if m and (mark or kind != "Feature"):
                    finish()
                    name, mbody = clean(m.group(1)).rstrip(":"), [("p", 0, m.group(2), None)]
                    starting = mark == "check" or kind == "Truth" or kind == "Feature"
                elif name and (tag == "li" or (tag == "p" and len(text) < 200 and not text.startswith("("))):
                    mbody.append((tag, depth, text, mark))
                elif name and tag == "p" and text.startswith("("):
                    finish()
                    name = None
                    plain.append((tag, depth, text, mark))
                elif name and tag == "p":
                    mbody.append((tag, depth, text, mark))
                else:
                    plain.append((tag, depth, text, mark))
            finish()
            if kind == "Feature" and plain:
                features.append("**" + heading + "**\n\n" + as_markdown(plain))

    column1 = ", ".join(s + " " + sets[s][0] for s in STATS if s in sets)
    column2 = ", ".join(s + " " + sets[s][1] for s in STATS if s in sets)
    starting_moves = ", ".join(m["name"] for m in moves if m["rulesets"][0]["implementation"]["moveStats"]["Stats"]["Kind"] == "Playbook" and m["rulesets"][0]["implementation"]["moveStats"]["Stats"]["Starting"])
    description = "\n\n".join(summary + ["**Example archetypes:** " + ", ".join(archetypes)] + features)
    item = entity("Playbooks", title, description, "playbookStats", {
        "Column 1": column1,
        "Column 2": column2,
        "Aesthetics": "\n".join("- " + a for a in aesthetics),
        "Starting move": starting_moves,
        "Feature": ", ".join(f.split("**")[1] for f in features),
    })
    return item, moves


def main():
    entities = basic_moves()
    playbooks = []
    for slug in PLAYBOOKS:
        item, moves = playbook(slug)
        playbooks.append(item)
        entities.extend(moves)
    entities.extend(playbooks)
    library = {
        "name": "Sapphic Reference Document",
        "description": "The basic moves, the nine playbooks and every playbook move from the Sapphic Reference Document of the Thirsty Sword Lesbians roleplaying game (https://poweredbylesbians.com/srd/), designed by April Kit Walsh and published by Evil Hat Productions, LLC, used under its open licence (CC BY-SA 4.0, https://creativecommons.org/licenses/by-sa/4.0/, with the terms at poweredbylesbians.com). Converted with tools/tsl_import.py, changing format only; commentary and examples of play are left out. This library is offered under the same licence.",
        "url": "/systems/tsl/tsl.json",
        "gamemaster": "",
        "entities": entities,
    }
    Path(OUT).write_text(json.dumps(library, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(len([e for e in entities if e["type"] == "Moves"]), "moves,", len(playbooks), "playbooks")


main()
