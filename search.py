#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Alfred script filter: search Contacts.app for contacts with phone numbers.

Modes: call (FaceTime Audio), tel (iPhone), im (iMessage open), msg (iMessage send)

For 'call' mode, Enter → FaceTime Audio, Cmd+Enter → iPhone (tel://).
FaceTime capability is approximated by the phone label ('iPhone' label = likely capable).
"""

import sys
import json
import subprocess
import os
import time

DIR   = os.path.dirname(os.path.abspath(__file__))
BIN   = os.path.join(DIR, 'get_contacts')
CACHE = os.path.join(DIR, '.contacts_cache.json')
MAX_AGE = 300  # seconds

ICONS = {
    'call': '/System/Applications/FaceTime.app',
    'tel':  '/System/Applications/FaceTime.app',
    'im':   '/System/Applications/Messages.app',
    'msg':  '/System/Applications/Messages.app',
}

# Labels that suggest a number is registered with FaceTime
FACETIME_LABELS = {'iphone', 'apple', 'facetime'}


def fetch_contacts():
    r = subprocess.run([BIN], capture_output=True, text=True, timeout=15)
    contacts = []
    for line in r.stdout.splitlines():
        parts = line.split('\t')
        if len(parts) >= 2 and parts[1].strip():
            contacts.append({
                'name':  parts[0],
                'phone': parts[1],
                'label': parts[2] if len(parts) > 2 else '',
            })
    return contacts


def get_contacts():
    if os.path.exists(CACHE) and time.time() - os.path.getmtime(CACHE) < MAX_AGE:
        try:
            with open(CACHE) as f:
                return json.load(f)
        except Exception:
            pass
    contacts = fetch_contacts()
    try:
        with open(CACHE, 'w') as f:
            json.dump(contacts, f)
    except Exception:
        pass
    return contacts


def is_likely_facetime(label: str) -> bool:
    """Heuristic: phone labeled 'iPhone' is almost certainly FaceTime-capable."""
    return label.lower() in FACETIME_LABELS


def build_item(contact: dict, mode: str, icon: str) -> dict:
    raw_label = contact.get('label', '')
    # Strip Apple's internal label decoration e.g. "_$!<iPhone>!$_"
    label = raw_label.replace('_$!<', '').replace('>!$_', '').strip()
    phone = contact['phone']
    name  = contact['name']

    if mode == 'call':
        subtitle     = f'{label}: {phone}  —  FaceTime Audio' if label else f'{phone}  —  FaceTime Audio'
        cmd_subtitle = f'{label}: {phone}  —  Call via iPhone' if label else f'{phone}  —  Call via iPhone'
    else:
        subtitle     = f'{label}: {phone}' if label else phone
        cmd_subtitle = subtitle

    item = {
        'title':        name,
        'subtitle':     subtitle,
        'arg':          phone,
        'autocomplete': name,
        'icon':         {'type': 'fileicon', 'path': icon},
    }

    if mode == 'call':
        item['mods'] = {
            'cmd': {
                'subtitle': cmd_subtitle,
                'arg':      phone,
            }
        }

    return item


def main():
    mode  = sys.argv[1] if len(sys.argv) > 1 else 'call'
    query = sys.argv[2].lower() if len(sys.argv) > 2 else ''

    contacts = get_contacts()

    if query:
        contacts = [c for c in contacts
                    if query in c['name'].lower() or query in c['phone']]

    icon = ICONS.get(mode, '/System/Applications/FaceTime.app')

    items = [build_item(c, mode, icon) for c in contacts]

    if not items:
        msg = f'No contacts matching "{query}"' if query else 'No contacts with phone numbers'
        items = [{'title': 'No contacts found', 'subtitle': msg, 'valid': False}]

    print(json.dumps({'items': items}))


if __name__ == '__main__':
    main()
