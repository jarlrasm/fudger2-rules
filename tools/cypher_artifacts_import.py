"""Builds systems/cypher/extensions/artifacts.json from the Cypher SRD.

    pdftotext -layout systems/cypher/Cypher-System-Reference-Document.pdf csrd.txt
    python3 -I tools/cypher_artifacts_import.py csrd.txt systems/cypher/extensions/artifacts.json
"""

import re, sys, json
text = open(sys.argv[1]).read()
out_path = sys.argv[2]
lines = []
for pi, p in enumerate(text.split('\f')):
    for l in p.split('\n'):
        lines.append((pi + 1, l.rstrip()))

def genre(page):
    for lo, hi, g in [(270, 280, 'Any'), (300, 305, 'Fantasy'), (370, 399, 'Science fiction'), (400, 420, 'Superhero'),
                      (450, 462, 'Fairy tale'), (505, 515, 'Horror'), (520, 530, 'Post-apocalyptic'), (650, 670, 'Fantasy'),
                      (1100, 1120, 'Cyberpunk'), (1120, 1135, 'Weird West'), (1180, 1193, 'Modern fantasy'),
                      (1205, 1215, 'Horror'), (1275, 1285, 'Post-apocalyptic')]:
        if lo <= page <= hi:
            return g
    raise SystemExit(f'no genre for page {page}')

def join(parts):
    out = ''
    for i, p in enumerate(parts):
        if not p:
            continue
        if not out:
            out = p
        elif prev_short_end:
            out += '\n\n' + p
        else:
            out += ' ' + p
        prev_short_end = len(p) < 100 and p.endswith(('.', ':', ')'))
    return out

def clean_name(n):
    n = n.replace('™', '').replace('’', "'").strip()
    n = re.sub(r"'S\b", "'s", n)
    return re.sub(r'\s+', ' ', n)

def tidy(s):
    s = s.replace('‐', '-')
    return re.sub(r'\s+([,.])', r'\1', s)

items = {}
i = 0
while i < len(lines):
    pg, l = lines[i]
    if l.startswith('Level: '):
        j = i + 1
        while j < len(lines) and not lines[j][1].strip():
            j += 1
        if lines[j][1].startswith('Form: '):
            k = i - 1
            while k >= 0 and not lines[k][1].strip():
                k -= 1
            name, npage = clean_name(lines[k][1]), lines[k][0]
            form = lines[j][1][6:].strip()
            eff = []
            m = j + 1
            if ' Effect: ' in form:
                form, first = form.split(' Effect: ', 1)
                eff = [first.strip()]
            else:
                while m < len(lines) and not lines[m][1].startswith(('Effect:', 'Depletion:', 'Level:')):
                    form += ' ' + lines[m][1].strip(); m += 1
                if lines[m][1].startswith('Effect:'):
                    eff = [lines[m][1][7:].strip()]; m += 1
            if eff:
                while m < len(lines) and not lines[m][1].startswith(('Depletion:', 'Level:', 'Form:')):
                    eff.append(lines[m][1].strip()); m += 1
                if lines[m][1].startswith('Depletion:'):
                    dep = lines[m][1][10:].strip()
                    while (dep.count('(') > dep.count(')') or (len(lines[m][1]) > 110 and not dep.endswith(('.', ')')))) and m + 2 < len(lines) and lines[m + 1][1].strip() and not lines[m + 2][1].startswith('Level: '):
                        m += 1; dep += ' ' + lines[m][1].strip()
                    dep = re.sub(r'\b1d00\b', '1d100', dep.replace('–', '-').replace('‐', '-'))
                    key = name.lower()
                    if key not in items:
                        items[key] = dict(name=name, page=npage, level=lines[i][1][7:].strip(), form=tidy(form.strip()),
                                          effect=tidy(join(eff)), depletion=tidy(dep), genre=genre(npage))
    i += 1

entities = []
for it in sorted(items.values(), key=lambda x: x['name'].lower()):
    entities.append({
        "type": "Artifacts",
        "name": it['name'],
        "description": it['effect'],
        "images": {},
        "rulesets": [{"system": "CypherSystem", "implementation": {"artifactStats": {"Stats": {
            "Level": it['level'], "Form": it['form'], "Effect": it['effect'], "Depletion": it['depletion'], "Genre": it['genre']}}}}],
        "references": [{"document": "csrd", "page": it['page']}],
    })
lib = {
    "name": "Cypher System Artifacts",
    "description": "Artifacts from the genre chapters of the Cypher System Reference Document, each with its level, form, effect and depletion. Roll a found artifact's level when the group finds it. Compatible with the Cypher System. This product is an independent production and is not affiliated with Monte Cook Games, LLC. It is published under the Cypher System Open License, found at http://csol.montecookgames.com. CYPHER SYSTEM and its logo are trademarks of Monte Cook Games, LLC in the U.S.A. and other countries.",
    "url": "/systems/cypher/extensions/artifacts.json",
    "gamemaster": "",
    "documents": [{"key": "csrd", "name": "Cypher System Reference Document 2025-08-22", "url": "/systems/cypher/Cypher-System-Reference-Document.pdf", "public": True}],
    "entities": entities,
}
json.dump(lib, open(out_path, 'w'), indent=1, ensure_ascii=False)
open(out_path, 'a').write('\n')
import collections
print(len(entities), collections.Counter(e['rulesets'][0]['implementation']['artifactStats']['Stats']['Genre'] for e in entities))
