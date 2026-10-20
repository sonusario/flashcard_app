"""Makes an Anki package the default deck set of flashcards.html.

The app imports the package embedded in flashcards.html the first time it
starts, and again whenever "Add Default Decks" is pressed on the main menu.
Since flashcards.html is a single self-contained file, the package is stored
inside it as base64 text, in <script id="bundled-deck">.

Usage:
    python3 tools/embed_deck.py "CompTIA Security+ SY0-701 (Combined).apkg" [flashcards.html]
"""
import base64
import html
import os
import re
import sys
import zipfile


def main() -> None:
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    package = sys.argv[1]
    page = sys.argv[2] if len(sys.argv) == 3 else os.path.join(os.path.dirname(__file__), '..', 'flashcards.html')

    if not zipfile.is_zipfile(package):
        sys.exit(f'{package} is not an Anki package (.apkg is a zip archive).')
    names = zipfile.ZipFile(package).namelist()
    if not any(name.startswith('collection.anki2') for name in names):
        sys.exit(f'{package} does not contain an Anki collection.')

    with open(package, 'rb') as file:
        encoded = base64.b64encode(file.read()).decode('ascii')
    lines = '\n'.join(encoded[i:i + 120] for i in range(0, len(encoded), 120))

    with open(page, encoding='utf-8') as file:
        text = file.read()
    pattern = re.compile(r'(<script id="bundled-deck" type="application/octet-stream" data-name=")[^"]*(">)[\s\S]*?(</script>)')
    if len(pattern.findall(text)) != 1:
        sys.exit(f'{page} has no <script id="bundled-deck"> to replace.')
    name = html.escape(os.path.basename(package), quote=True)
    text = pattern.sub(lambda m: f'{m.group(1)}{name}{m.group(2)}\n{lines}\n{m.group(3)}', text)

    with open(page, 'w', encoding='utf-8') as file:
        file.write(text)
    print(f'Embedded {os.path.basename(package)} ({os.path.getsize(package):,} bytes) in {page}.')


if __name__ == '__main__':
    main()
