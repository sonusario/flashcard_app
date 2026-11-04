#!/usr/bin/env python3
"""Builds "CompTIA Security+ SY0-701 (Short Answer).apkg" from the combined deck.

In the short-answer deck every back is at most one sentence; anything longer
lives on the front. Run from the repository root:

    python3 tools/build_short_answer_deck.py

How each kind of card is reframed:
- Cloze notes become one basic card per deletion. The front is the sentence
  with that deletion shown as [...] plus the note's extra text (with the
  answer masked); the back is only the deleted text.
- "Tough terms" (term -> long definition) are flipped: the definition is on
  the front and the term is the answer.
- Practice questions keep the question and choices on the front; the back is
  only the correct choice.
- Basic cards whose answer ran past one sentence are rewritten by hand below.
"""

import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import zipfile

SOURCE = 'CompTIA Security+ SY0-701 (Combined).apkg'
TARGET = 'CompTIA Security+ SY0-701 (Short Answer).apkg'
OLD_ROOT = 'CompTIA Security+ SY0-701'
NEW_ROOT = 'CompTIA Security+ SY0-701 (Short Answer)'
BASIC_MODEL = 1760701000001
CLOZE_MODEL = 1760701000002
ID_OFFSET = 1_000_000_000  # new note, card and deck ids stay clear of the original deck's

# Hand-rewritten basic cards: note id -> (new front or None to keep, new back).
REWRITES = {
    1792493543468: (None, 'False, because they are often used together to get both security and speed.'),
    1792493543481: (None, 'Generate a key pair, share the public key, encrypt with the public key, then decrypt with the private key.'),
    1792493543651: (None, 'False, because you can trust your own internal CA without buying trust from a third party.'),
    1792493543677: ('OCSP is universally supported today, true or false?<br><br>(Consider outdated browsers, and modern browsers that claim support.)',
                    'False, because older browsers lack it and some modern ones skip the checks they claim to perform.'),
    1792493543709: (None, 'Authentication of the sender, message integrity, and non-repudiation.'),
    1792493543717: (None, 'They issue certificates, validate identities, and revoke compromised certificates.'),
    1792493543721: (None, 'CA validation, cryptographic signatures, and expiration dates.'),
    1792493543723: (None, 'It closes security holes and improves system stability.'),
    1792493543727: (None, 'A claimed identity, credentials, verification, and an access decision.'),
    1792493543729: (None, 'Timestamps, user actions, and resource access details.'),
    1792493543735: (None, 'The current security state, the desired state, and industry standards such as NIST or ISO.'),
    1792493543755: (None, 'The Policy Enforcement Point (PEP), the Policy Decision Point (PDP), and the Policy Administrator.'),
    1792493543765: (None, 'It inspects traffic, applies policy, and acts as the security gateway.'),
    1792493543815: (None, 'Implementation risks, organizational impact, and approval viability.'),
    1792493543821: (None, 'Backout procedures, system backups, and restoration verification steps.'),
    1792493543837: (None, 'A full OS restart, a hardware power cycle, or a service/daemon reload.'),
    1792493543841: (None, 'Software patches, configuration changes, registry edits, and historical versions.'),
    1792493543873: (None, 'It uses asymmetric encryption to exchange a key, then symmetric encryption for the data.'),
    1792493543879: ('What prevents MITM attacks during key exchange?<br><br>(Diffie-Hellman alone creates a shared secret but does not stop a man-in-the-middle.)',
                    'Authenticating the exchange, for example with certificates or digital signatures.'),
    1792493543881: (None, 'Certificate Authorities, digital certificates, Registration Authorities, and certificate repositories.'),
    1792493543887: (None, 'Key exchange (asymmetric), session establishment, and data transfer (symmetric).'),
    1792493543893: (None, 'Client VPNs use SSL/TLS and site-to-site VPNs use IPsec.'),
    1792493543899: (None, 'Physical transfer, voice communication, and trusted couriers.'),
    1792493543903: (None, 'Full Disk Encryption (FDE) and file-level encryption such as EFS.'),
    1792493543907: (None, 'HTTPS (TLS), SSL VPN, and IPsec VPN.'),
    1792493543937: ('What is tokenization?<br><br>(The original data is kept securely in a vault, and the stand-in is meaningless if stolen.)',
                    'Replacing sensitive data with a token.'),
    1792493543945: (None, 'It generates random numbers, stores machine-specific keys, and supports full-disk encryption.'),
    1792493543947: (None, 'It stores keys for multiple servers, uses redundant hardware, and prevents unauthorized key access.'),
    1792493543949: (None, 'It can be hosted on-premises or in the cloud, separates keys from data, and logs key usage.'),
    1792493543951: (None, 'It runs independently of the main CPU, encrypts memory operations, and stores unchangeable keys.'),
    1792493543963: (None, 'Not reversible, unique for each input, and collision-resistant.'),
    1792493543979: (None, "Hash the message, then encrypt the hash with the sender's private key."),
    1792493543981: (None, "Decrypt the hash with the sender's public key, then compare it to the message's hash."),
    1792493543995: ("What is a self-signed certificate?<br><br>(Browsers don't trust these automatically, so they are mainly used internally or for testing.)",
                    'A certificate signed with its own private key instead of by a CA.'),
    1792493544011: (None, 'Record transactions, send the information to all participants, then group transactions into blocks.'),
    1792493544013: (None, 'Hash each block, reject blocks with invalid hashes, then distribute changes to the network.'),
    1792493544251: (None, 'Both, since a hacktivist may get inside an organization as well as attack from outside.'),
    1792493544361: (None, 'False, because multiple layers of defense are necessary.'),
    1792493545474: (None, 'Location, resources and funding, skill level, and motivations.'),
    1792493545542: (None, 'Tech support scams, government threats, and fraudulent credit offers.'),
    1792493545554: (None, 'To elicit sensitive information such as credit card numbers, or to commit identity theft.'),
    1792493545556: (None, 'Unsolicited contact, requests for sensitive data, claims of authority, and poor grammar or urgency.'),
    1792493545558: (None, 'Never share personal info, verify callers independently, monitor financial accounts, and educate teams.'),
    1792493545574: (None, 'Research the sites employees visit, compromise one, then wait for employees to visit and get infected.'),
    1792493545592: (None, 'Running as its own process, or injecting itself into a legitimate process that is already running.'),
    1792493545600: (None, "A malicious DLL is placed on the victim's storage and a running process is made to load it, so the code runs with that process's permissions."),
    1792493545656: (None, 'The vulnerability is discovered and disclosed to the vendor, who creates, tests and releases a patch that users then apply.'),
    1792493545710: (None, 'The victim follows a malicious link to a trusted site carrying hidden code, and their browser runs the script, which can send sensitive data to the attacker.'),
    1792493545962: ('What were the three major zero-day vulnerabilities found in Apple’s iOS/iPadOS in May 2023?<br><br>(All three were in WebKit.)',
                    'A sandbox escape, disclosure of sensitive information from memory, and arbitrary code execution.'),
    1792493546100: (None, 'The attacker sends fake ARP replies claiming to be the router, so the victim updates its ARP cache and sends traffic through the attacker.'),
    1792493546142: (None, 'The attacker intercepts the HTTPS redirect, keeps the victim on HTTP, and steals credentials as a man-in-the-middle.'),
    1792493547614: ("What's the disaster recovery advantage of backups?<br><br>(Think about recovering from malware, compared with reinstalling the OS.)",
                    'Faster system restoration.'),
    1792493550043: (None, 'What happened, what the timeline was, what worked or failed, and what should be improved.'),
    1792493551341: ('HIPAA originally capped civil fines at $100 per violation and $25,000 per year. What did the 2009 HITECH Act raise them to?',
                    'Tiers of up to $50,000 per violation and $1.5 million per year, now adjusted for inflation.'),
    1792493552453: (None, 'Mandatory Access Control, Media Access Control, or Message Authentication Code.'),
    1792493552545: (None, 'Privileged Access Management or Pluggable Authentication Modules.'),
    1792493552597: (None, 'Recovery Agent or Registration Authority.'),
    1792493552611: (None, 'Role-based Access Control or Rule-based Access Control.'),
    1792493552641: (None, 'Storage Area Network or Subject Alternative Name.'),
}

# Acronym cards whose back added CompTIA's own expansion: that note moves to the front.
COMPTIA_NOTE = re.compile(r"^(.*?)<br><i>CompTIA's acronym list: (.*?)</i>$")

BR = re.compile(r'<br\s*/?>', re.I)
CLOZE = re.compile(r'\{\{c(\d+)::([\s\S]*?)(?:::([\s\S]*?))?\}\}')


def text_of(html):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', BR.sub(' ', html))).replace('&nbsp;', ' ').strip()


def is_one_sentence(html):
    if BR.search(html) or '<li' in html or '<ul' in html:
        return False
    t = re.sub(r'^[A-F]\. ', '', text_of(html))  # a choice's letter, as in "D. ..."
    # A full stop, ? or ! followed by more text starts a second sentence ("e.g." and "i.e." excepted).
    t = re.sub(r'\b(e\.g|i\.e|vs|etc|U\.S)\.', 'X', t)
    return not re.search(r'[.!?]["”’)]?\s+\S', t)


def mask(text, answers):
    """Hides each answer (case-insensitively) in text, longest first."""
    for answer in sorted({a for a in answers if len(a) >= 3}, key=len, reverse=True):
        text = re.sub(r'(?<![\w])' + re.escape(answer) + r'(?![\w])', '[...]', text, flags=re.I)
    return text


def cloze_cards(text, extra, numbers):
    for n in numbers:
        answers = [m.group(2).strip() for m in CLOZE.finditer(text) if int(m.group(1)) == n]
        if not answers:
            continue

        def show(m):
            if int(m.group(1)) != n:
                return m.group(2)
            return '<b>[%s]</b>' % (m.group(3) or '...')

        front = CLOZE.sub(show, text).replace('(see back)', '(examples below)').strip()
        if extra.strip():
            front += '<br><br><i>%s</i>' % mask(extra.strip(), [text_of(a) for a in answers])
        back = ' … '.join(answers)
        yield front, back


def term_parts(term):
    term = text_of(term)
    parts = {term}
    m = re.match(r'^(.*?)\s*\((.*?)\)\s*$', term)
    if m:
        parts.update({m.group(1).strip(), m.group(2).strip()})
    for p in list(parts):
        parts.update(s.strip() for s in p.split('/'))
    return parts


def flip_term(term, definition):
    shown = mask(definition.strip(), term_parts(term))
    front = 'Which term matches this description?<br><br>' + shown
    back = text_of(term)
    return front, back


def mcq_back(back):
    m = re.match(r'Correct Answer:\s*(.*?)<br>', back)
    if not m:
        raise ValueError('no correct answer in: ' + back[:80])
    return m.group(1).strip()


def tags_of(note_tags):
    return [t for t in note_tags.split() if t]


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    work = tempfile.mkdtemp()
    with zipfile.ZipFile(os.path.join(root, SOURCE)) as z:
        z.extractall(work)
    db_path = os.path.join(work, 'collection.anki2')
    db = sqlite3.connect(db_path)

    notes = {r[0]: r for r in db.execute('select id, guid, mid, tags, flds from notes')}
    cards = db.execute('select id, nid, did, ord from cards order by id').fetchall()
    note_deck = {}
    note_ords = {}
    for cid, nid, did, ord_ in cards:
        note_deck.setdefault(nid, did)
        note_ords.setdefault(nid, []).append(ord_)

    out = []  # (source note id, deck id, tags, front, back)
    for nid in sorted(notes):
        _, guid, mid, tags, flds = notes[nid]
        fields = flds.split('\x1f')
        did = note_deck[nid]
        tag_list = tags_of(tags)
        if mid == CLOZE_MODEL:
            numbers = sorted(o + 1 for o in note_ords[nid])
            for front, back in cloze_cards(fields[0], fields[1], numbers):
                out.append((nid, did, tag_list, front, back))
            continue
        front, back = fields[0], fields[1]
        if 'type::mcq' in tag_list:
            back = mcq_back(back)
        elif 'source::daniellaurin-tough-terms' in tag_list:
            front, back = flip_term(front, back)
        elif nid in REWRITES:
            new_front, back = REWRITES[nid]
            front = new_front or front
        else:
            m = COMPTIA_NOTE.match(back)
            if m:
                front = "%s<br><br>(CompTIA's acronym list calls it “%s”; give the standard expansion.)" % (front, m.group(2))
                back = m.group(1)
        out.append((nid, did, tag_list, front, back))

    problems = [(n, b) for n, _, _, _, b in out if not is_one_sentence(b)]
    if problems:
        for n, b in problems:
            print('More than one sentence on the back of note %d: %r' % (n, b), file=sys.stderr)
        sys.exit(1)

    # Rewrite the collection: new decks, one basic note and one card per output.
    col = db.execute('select decks, models from col').fetchone()
    decks = json.loads(col[0])
    new_decks = {}
    for key, deck in decks.items():
        if deck['name'].startswith(OLD_ROOT):
            deck = dict(deck, id=deck['id'] + ID_OFFSET, name=NEW_ROOT + deck['name'][len(OLD_ROOT):])
        new_decks[str(deck['id'])] = deck
    models = json.loads(col[1])
    models = {k: v for k, v in models.items() if int(k) == BASIC_MODEL}
    models[str(BASIC_MODEL)]['did'] = models[str(BASIC_MODEL)].get('did', 1)
    db.execute('update col set decks = ?, models = ?', (json.dumps(new_decks), json.dumps(models)))
    db.execute('delete from notes')
    db.execute('delete from cards')
    db.execute('delete from revlog')
    db.execute('delete from graves')

    base = 1792500000000 + ID_OFFSET
    for i, (src, did, tag_list, front, back) in enumerate(out):
        nid = base + 2 * i
        cid = base + 2 * i + 1
        guid = hashlib.sha1(('short-answer:%d:%s' % (src, front)).encode()).hexdigest()[:10]
        sfld = text_of(front)
        csum = int(hashlib.sha1(sfld.encode()).hexdigest()[:8], 16)
        tags = ' %s type::short-answer ' % ' '.join(t for t in tag_list if not t.startswith('type::'))
        db.execute('insert into notes (id, guid, mid, mod, usn, tags, flds, sfld, csum, flags, data) values (?,?,?,?,?,?,?,?,?,0,"")',
                   (nid, guid, BASIC_MODEL, 1792500000, -1, tags, '\x1f'.join([front, back, '']), sfld, csum))
        db.execute('insert into cards (id, nid, did, ord, mod, usn, type, queue, due, ivl, factor, reps, lapses, left, odid, odue, flags, data) '
                   'values (?,?,?,0,?,-1,0,0,?,0,0,0,0,0,0,0,0,"")',
                   (cid, nid, did + ID_OFFSET, 1792500000, i + 1))
    db.commit()
    db.execute('vacuum')
    db.close()

    target = os.path.join(root, TARGET)
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(db_path, 'collection.anki2')
        z.writestr('media', '{}')
    shutil.rmtree(work)
    print('Wrote %s with %d cards.' % (TARGET, len(out)))


if __name__ == '__main__':
    main()
