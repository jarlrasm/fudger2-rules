"""Turns a Word document into plain HTML for printing to PDF, keeping the text,
bold and italics, headings and tables, and leaving out images.

Built for the Cypher System Reference Document, whose headings have no
heading style: a short line in capitals becomes a heading, as does a short
line that is all bold.

    python3 tools/docx_to_html.py Cypher-System-Reference-Document.docx out.html "Cypher System Reference Document"
    chromium --headless --no-pdf-header-footer --print-to-pdf=out.pdf file:///path/to/out.html
"""

import html
import re
import sys
import zipfile

SOURCE, OUT, TITLE = sys.argv[1], sys.argv[2], sys.argv[3]

STYLE = """
body { font-family: Georgia, serif; font-size: 10.5pt; line-height: 1.35; margin: 0; }
h1 { font-size: 20pt; margin: 0 0 12pt; }
h2 { font-size: 13pt; margin: 14pt 0 4pt; page-break-after: avoid; }
h3 { font-size: 11pt; margin: 10pt 0 3pt; page-break-after: avoid; }
p { margin: 0 0 5pt; }
table { border-collapse: collapse; margin: 4pt 0 8pt; font-size: 9.5pt; }
td { border: 1px solid #999; padding: 2pt 4pt; vertical-align: top; }
"""


def run_text(run):
    text = "".join(html.unescape(t) for t in re.findall(r"<w:t[^>]*>([^<]*)</w:t>", run))
    if "<w:tab/>" in run:
        text = text or " "
    if not text:
        return "", False
    bold = bool(re.search(r"<w:b/>|<w:b w:val=\"(1|true|on)\"/>", run))
    italic = bool(re.search(r"<w:i/>|<w:i w:val=\"(1|true|on)\"/>", run))
    out = html.escape(text)
    if italic:
        out = f"<i>{out}</i>"
    if bold:
        out = f"<b>{out}</b>"
    return out, bold


def paragraph(p):
    parts, all_bold = [], True
    for run in re.findall(r"<w:r[ >].*?</w:r>", p, re.S):
        text, bold = run_text(run)
        if text.strip():
            all_bold = all_bold and bold
        parts.append(text)
    body = "".join(parts).strip()
    plain = re.sub(r"<[^>]+>", "", body)
    return body, plain, all_bold and bool(plain)


def block(p):
    body, plain, bold = paragraph(p)
    if not plain:
        return ""
    if len(plain) < 70 and plain.upper() == plain and re.search(r"[A-Z]", plain):
        return f"<h2>{html.escape(plain.title() if len(plain) > 3 else plain)}</h2>"
    if len(plain) < 70 and bold:
        return f"<h3>{body}</h3>"
    return f"<p>{body}</p>"


def table(t):
    rows = []
    for row in re.findall(r"<w:tr[ >].*?</w:tr>", t, re.S):
        cells = []
        for cell in re.findall(r"<w:tc>.*?</w:tc>", row, re.S):
            text = "<br>".join(paragraph(p)[0] for p in re.findall(r"<w:p[ >].*?</w:p>", cell, re.S))
            cells.append(f"<td>{text}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return "<table>" + "".join(rows) + "</table>"


document = zipfile.ZipFile(SOURCE).read("word/document.xml").decode("utf-8")
body = document.split("<w:body>", 1)[1]
out = []
for match in re.finditer(r"<w:tbl>.*?</w:tbl>|<w:p[ >].*?</w:p>|<w:p/>", body, re.S):
    chunk = match.group(0)
    out.append(table(chunk) if chunk.startswith("<w:tbl>") else block(chunk))

page = f'<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title><style>{STYLE}</style></head><body><h1>{html.escape(TITLE)}</h1>\n' + "\n".join(o for o in out if o) + "\n</body></html>\n"
open(OUT, "w", encoding="utf-8").write(page)
print(len(out), "blocks")
