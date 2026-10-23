# flashcard_app

**Live:** [https://sonusario.github.io/flashcard_app/](https://sonusario.github.io/flashcard_app/)

`flashcards.html` is a single-file web version of the Godot 4 Flashcards project (Part 5: Anki import). Open it in any current browser. It needs no server, no install and no network connection.

- **Cards first.** A card can be in any number of decks, or none. Deleting a deck keeps its cards. Editing a shared card from one deck can keep the change in that deck only (copy-on-write) or apply it everywhere.
- **Rich content.** Cards are written in markdown and can include images (from a file, a drawing or the clipboard) and audio (from a file or the microphone).
- **Spaced repetition.** Reviews use Leitner levels on golden-ratio intervals (1, 2, 3, 4, 7, 11, 18… days), buckets of 7, first looks, "review later", and optional time limits that give each level 20% of the time left.
- **Anki import.** Imports `.apkg` files from current and older versions of Anki, including Zstandard-compressed collections, cloze and reversed cards, and media. Importing the same deck twice adds nothing.

On first launch, the app imports the bundled CompTIA Security+ SY0-701 acronym deck (328 cards).

Data is stored in the browser (IndexedDB), separately for each browser and device. Use **Back Up…** on the main menu to save everything, including media, as one JSON file, and **Restore…** to load it again.

Review keys: <kbd>Space</kbd> shows or flips the card, <kbd>1</kbd> is "Didn't get it.", <kbd>2</kbd> is "Got it!" or "Complete First Look", and <kbd>L</kbd> is "Review later".

Zstandard decompression uses [fzstd](https://github.com/101arrowz/fzstd) 0.1.1 (MIT License), included inline.
