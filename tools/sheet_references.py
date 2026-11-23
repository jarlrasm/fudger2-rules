import re
import subprocess
import sys

# Prints the PDF pages where each term stands alone on a line, as a heading
# or a table row does, so sheet references can be checked instead of guessed.
# Usage: sheet_references.py book.pdf "Armor Class" "Hit Points" ...
# A term can be "Heading@first-last" to search only those pages.

PDF = sys.argv[1]


def normal(text):
    text = text.replace("’", "'").replace("‘", "'").replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text).strip().lower()


out = subprocess.run(["pdftotext", "-layout", PDF, "-"], capture_output=True, text=True, check=True).stdout
pages = [[normal(part) for line in page.split("\n") for part in re.split(r"\s{3,}", line) if part.strip()] for page in out.split("\f")]

for arg in sys.argv[2:]:
    term, _, span = arg.partition("@")
    first, _, last = span.partition("-")
    first = int(first) if first else 1
    last = int(last) if last else len(pages)
    wanted = normal(term)
    found = [number for number in range(first, last + 1) if any(line == wanted or line.startswith(wanted + ".") or line.startswith(wanted + " [") for line in pages[number - 1])]
    print(f"{term}\t{', '.join(map(str, found)) or '-'}")
