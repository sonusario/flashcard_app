#!/usr/bin/env python3
"""Builds "CompTIA Security+ SY0-701 (Three-Word Answers).apkg" from the combined deck.

Every back in this deck is at most three words, and each card asks about one
concept, worded so that the front leads to that short answer. Run from the
repository root:

    python3 tools/build_three_word_deck.py          # build the deck
    python3 tools/build_three_word_deck.py --todo   # list cards with no rewrite yet

It starts from the short-answer cards (see build_short_answer_deck.py) and then:
- keeps every card whose back is already three words or fewer;
- flips acronym cards with a long expansion, so the expansion is the
  question and the acronym is the answer;
- shortens "Name (ABBR)" term answers to the abbreviation;
- uses the hand rewrites in tools/three_word_rewrites.tsv for the rest.
  Each line there is: key <tab> front <tab> back. A front of "=" keeps the
  short-answer front, and a back of "-" leaves the card out (used where the
  card cannot be made into a three-word answer without losing its point,
  or where it would repeat another card).
Cards that end up asking the same thing as an earlier card (same answer and
nearly the same question) are left out, so the deck has no duplicates.
"""

import hashlib
import os
import re
import sqlite3
import sys
import tempfile
import zipfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_short_answer_deck as sa  # noqa: E402

TARGET = 'CompTIA Security+ SY0-701 (Three-Word Answers).apkg'
NEW_ROOT = 'CompTIA Security+ SY0-701 (Three-Word Answers)'
ID_OFFSET = 2_000_000_000
REWRITES = 'three_word_rewrites.tsv'
MAX_WORDS = 3


def words(html):
    t = sa.text_of(html)
    t = re.sub(r'^[A-F]\.\s+', '', t)
    return len(t.split())


def key_of(src, front):
    return hashlib.sha1(('short-answer:%d:%s' % (src, front)).encode()).hexdigest()[:10]


ACRONYM_Q = re.compile(r'^What does (.+?) stand for\?')
ABBR_LAST = re.compile(r'^(.*\S)\s*\(([^()]+)\)$')


def auto_rewrite(tags, front, back):
    """A rewrite that needs no hand work, or None."""
    text = sa.text_of(back)
    if 'source::ankiweb-acronym-list' in tags:
        m = ACRONYM_Q.match(sa.text_of(front))
        if m and words(m.group(1)) <= MAX_WORDS:
            return 'Which acronym stands for %s?' % back.strip(), m.group(1).strip()
    if 'source::daniellaurin-tough-terms' in tags:
        m = ABBR_LAST.match(text)
        if m:
            a, b = m.group(1).strip(), m.group(2).strip()
            # The abbreviation is the all-capitals part.
            short, long_ = (b, a) if re.fullmatch(r'[A-Z0-9/.\-]+v?\d*', b.replace(' ', '')) else (a, b)
            if words(short) <= MAX_WORDS and re.search(r'[A-Z]{2}', short):
                shown = sa.mask(front, [long_, short])
                return shown + '<br><br>(Answer with the abbreviation.)', short
    return None


def load_rewrites(path):
    rewrites = {}
    if not os.path.exists(path):
        return rewrites
    with open(path, encoding='utf-8') as f:
        for n, line in enumerate(f, 1):
            line = line.rstrip('\n')
            if not line.strip() or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) != 3:
                sys.exit('%s line %d: expected key, front and back separated by tabs' % (REWRITES, n))
            rewrites[parts[0]] = (parts[1], parts[2])
    return rewrites


def norm(html):
    t = sa.text_of(html).lower()
    t = re.sub(r'\[\.\.\.\]|\(answer with the abbreviation\.\)', ' ', t)
    return re.findall(r'[a-z0-9]+', t)


STOP = set('a an the of to in for and or is are what which does do that this with on by be as it its how why when who can'.split())


def same_question(a, b):
    sa_, sb = set(norm(a)) - STOP, set(norm(b)) - STOP
    if not sa_ or not sb:
        return norm(a) == norm(b)
    return len(sa_ & sb) / len(sa_ | sb) >= 0.75


def three_word_cards(db, rewrites, todo=None):
    out = []
    for src, did, tags, front, back in sa.short_answer_cards(db):
        key = key_of(src, front)
        if key in rewrites:
            new_front, new_back = rewrites[key]
            if new_back == '-':
                continue
            front = front if new_front == '=' else new_front
            back = new_back
        elif words(back) > MAX_WORDS:
            auto = auto_rewrite(tags, front, back)
            if auto:
                front, back = auto
            elif todo is not None:
                todo.append((key, tags, front, back))
                continue
        out.append((src, did, tags, front, back))

    # Leave out repeats: the same answer to (nearly) the same question.
    kept, by_answer, fronts = [], {}, set()
    for card in out:
        front, back = card[3], card[4]
        nf = ' '.join(norm(front))
        answer = ' '.join(norm(re.sub(r'^[A-F]\.\s+', '', sa.text_of(back))))
        if nf in fronts or any(same_question(front, f) for f in by_answer.get(answer, [])):
            continue
        fronts.add(nf)
        by_answer.setdefault(answer, []).append(front)
        kept.append(card)
    return kept


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rewrites = load_rewrites(os.path.join(root, 'tools', REWRITES))
    work = tempfile.mkdtemp()
    with zipfile.ZipFile(os.path.join(root, sa.SOURCE)) as z:
        z.extractall(work)
    db_path = os.path.join(work, 'collection.anki2')
    db = sqlite3.connect(db_path)

    todo = []
    out = three_word_cards(db, rewrites, todo)
    if '--todo' in sys.argv:
        for key, tags, front, back in todo:
            src = next((t[8:] for t in tags if t.startswith('source::')), '?')
            print('%s\t%s\t%s\t%s' % (key, src, re.sub(r'\s+', ' ', front.replace('\t', ' ')), sa.text_of(back)))
        print('%d cards still need a rewrite.' % len(todo), file=sys.stderr)
        return
    if todo:
        sys.exit('%d cards have a back longer than %d words and no rewrite; run with --todo to list them.' % (len(todo), MAX_WORDS))
    long_backs = [c for c in out if words(c[4]) > MAX_WORDS]
    if long_backs:
        for c in long_backs:
            print('Back longer than %d words: %r' % (MAX_WORDS, sa.text_of(c[4])), file=sys.stderr)
        sys.exit(1)
    sa.write_deck(db, db_path, work, out, os.path.join(root, TARGET), NEW_ROOT, 'three-word', 'three-word',
                  id_offset=ID_OFFSET)
    shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    main()
