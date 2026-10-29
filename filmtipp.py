# -*- coding: utf-8 -*-
"""Filmtipp des Tages: schreibt einmal am Tag einen zufälligen Filmvorschlag in den Familienchat.

Tippen auf die Nachricht öffnet den Titel. Die Uhrzeit stellst du ein; verpasst die Engine sie (z. B. aus),
kommt der Tipp beim nächsten Start danach. „Jetzt posten“ löst sofort einen Tipp aus (POST an .../jetzt).
Ordner, die nach Suche, Seitenwechsel, Serien oder Live-TV aussehen, werden übersprungen.
"""
import random
import re
import time

EXT_ID = 'filmtipp'
EXT_NAME = 'Filmtipp des Tages'
EXT_DESCRIPTION = 'Postet täglich einen zufälligen Filmvorschlag aus deinen Quellen in den Familienchat.'
EXT_SETTINGS = [
    {'key': 'an', 'label': 'Täglichen Tipp posten', 'type': 'bool', 'default': True},
    {'key': 'stunde', 'label': 'Frühestens um … Uhr', 'type': 'number', 'default': 17, 'min': 0, 'max': 23},
    {'key': 'quellen', 'label': 'Nur diese Quellen', 'type': 'text', 'default': '', 'hint': 'Komma-getrennt, Teil des Namens genügt. Leer = alle.'},
    {'key': 'absender', 'label': 'Absender im Chat', 'type': 'text', 'default': '🎬 Filmtipp'},
]
_SKIP = re.compile(r'such|search|seite|weiter|next|zur(ü|ue)ck|back|a-z|^[a-z0-9#]$|cache|einstellung|login|anmeld|serie|staffel|season|folge|anime|\b(?:tv|live|radio)\b', re.I)
_api = None


def _words(text):
    return [w.strip().lower() for w in str(text or '').replace(';', ',').split(',') if w.strip()]


def _plays(pid, folder, depth, budget):
    if budget[0] <= 0:
        return []
    budget[0] -= 1
    try:
        items = _api.open(pid, folder, fresh=False)
    except Exception:                                  # noqa: BLE001
        return []
    plays = [i for i in items if i.get('kind') == 'play' and not i.get('episode')]
    if len(plays) >= 3 or depth <= 0:
        return plays
    folders = [i for i in items if i.get('kind') == 'folder' and not _SKIP.search(i.get('title') or '')]
    random.shuffle(folders)
    out = list(plays)
    for f in folders[:3]:
        out += _plays(pid, f, depth - 1, budget)
        if len(out) >= 10 or budget[0] <= 0:
            break
    return out


def tipp():
    want = _words(_api.get('quellen'))
    provs = _api.providers()
    if want:
        provs = [p for p in provs if any(w in (p['id'] + ' ' + p['name']).lower() for w in want)]
    random.shuffle(provs)
    for p in provs[:5]:
        pool = _plays(p['id'], {}, 2, [8])
        if pool:
            return random.choice(pool)
    return None


def jetzt(force=False):
    it = tipp()
    if not it:
        return 0
    _api.chat('Filmtipp des Tages: %s%s' % (it.get('title', '?'), (' (%s)' % it['year']) if it.get('year') else ''),
              item=it, author=_api.get('absender') or None)
    _api.set('letzter', time.strftime('%Y-%m-%d'))
    return 1


def pruefen():
    if not _api.get('an'):
        return
    heute = time.strftime('%Y-%m-%d')
    if _api.get('letzter') == heute or time.localtime().tm_hour < int(_api.get('stunde') or 0):
        return
    jetzt()


def register(api):
    global _api
    _api = api
    api.route('jetzt', lambda req: {'gepostet': jetzt(True)} if req.method == 'POST' else ({'error': 'Nur per POST'}, 405))
    api.every(30, pruefen, name='Tipp prüfen', first_delay=90)
