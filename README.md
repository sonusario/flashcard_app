# flashcard_app

**Live:** [https://sonusario.github.io/flashcard_app/](https://sonusario.github.io/flashcard_app/)

`flashcards.html` is a single-file web version of the Godot 4 Flashcards project (Part 5: Anki import). Open it in any current browser. It needs no server, no install and no network connection.

- **Cards first.** A card can be in any number of decks, or none. Deleting a deck keeps its cards. Editing a shared card from one deck can keep the change in that deck only (copy-on-write) or apply it everywhere.
- **Managing many cards at once.** In the card browser:
  - Click a card to select it. Ctrl+click (⌘+click on a Mac) or a row's checkbox adds or removes one card. Shift+click selects a range, and the header checkbox or Ctrl+A (⌘A) selects every card shown.
  - **Change Decks…** adds the selected cards to decks or takes them out. **Delete N Cards** deletes them.
  - **Delete All Cards…** empties the deck. Cards that other decks hold are only taken out of this deck, unless you choose to delete them too.
  - **Delete Deck…** can also delete the deck's cards. Cards that another deck holds are always kept.
- **Loose Cards.** Cards that are in no deck appear under **Loose Cards**, which you can browse and review like any deck.
- **Rich content.** Cards are written in markdown and can include images (from a file, a drawing or the clipboard) and audio (from a file or the microphone).
- **Spaced repetition.** Reviews use Leitner levels on golden-ratio intervals (1, 2, 3, 4, 7, 11, 18… days), buckets of 7, first looks, "review later", and optional time limits that give each level 20% of the time left.
- **Anki import.** Imports `.apkg` files from current and older versions of Anki, including Zstandard-compressed collections, cloze and reversed cards, and media. Importing the same deck twice adds nothing.

On first launch, the app starts with a small sample deck. The repository also holds `CompTIA Security+ SY0-701 (Combined).apkg`, which you can load with **Import Anki Deck…**. It has 5,613 cards in 8 decks: the five exam domains, Ports and Protocols, Key Terms, and Acronyms. Large collections stay fast because the card browser draws its rows in pages as you scroll.

`CompTIA Security+ SY0-701 (Short Answer).apkg` holds the same 5,613 cards reframed so that every back is at most one sentence and any detail sits on the front. Cloze cards become one question per blank with only the missing words on the back, key terms are flipped so the definition is the question, and practice questions answer with just the correct choice. It imports into its own decks, so it can sit alongside the original. `tools/build_short_answer_deck.py` rebuilds it from the combined deck.

**About** on the main menu links to this repository and the project hub, and lists the changes merged into `main`.

Data is stored in the browser (IndexedDB), separately for each browser and device. Use **Back Up…** on the main menu to save everything, including media, as one JSON file, and **Restore…** to load it again.

Review keys: <kbd>Space</kbd> shows or flips the card, <kbd>1</kbd> is "Didn't get it.", <kbd>2</kbd> is "Got it!" or "Complete First Look", <kbd>L</kbd> is "Review later", and <kbd>E</kbd> edits the card being reviewed (the edit is saved to the card, which keeps its progress and its place in the review, and the time spent editing does not count against the time limit).

Zstandard decompression uses [fzstd](https://github.com/101arrowz/fzstd) 0.1.1 (MIT License), included inline.
