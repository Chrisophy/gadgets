# -*- coding: utf-8 -*-
"""Zufallsfilm: „Was schauen wir heute?“ - ein Menüpunkt, der ein paar zufällige Filme aus deinen Quellen vorschlägt.

So geht es: Auf der Startseite die Kachel „🎲 Zufall“ öffnen. Die Erweiterung wählt eine Quelle, geht einen Ordner
tiefer (Filme, Kategorien …) und zeigt dir ein paar abspielbare Titel. Nochmal öffnen = neue Auswahl.
Mit „Nur diese Quellen“ legst du fest, woher die Vorschläge kommen (Teil des Namens genügt, leer = alle aktiven).
Ordner, die nach Suche, Seitenwechsel oder Serien aussehen, werden übersprungen.
"""
import random
import re
import time

EXT_ID = 'zufall'
EXT_NAME = 'Zufallsfilm'
EXT_DESCRIPTION = 'Kachel „🎲 Zufall“: ein paar zufällige Titel aus deinen Quellen - gegen das ewige Suchen.'
EXT_SETTINGS = [
    {'key': 'anzahl', 'label': 'Wie viele Vorschläge', 'type': 'number', 'default': 6, 'min': 1, 'max': 30},
    {'key': 'quellen', 'label': 'Nur diese Quellen', 'type': 'text', 'default': '',
     'hint': 'Komma-getrennt, Teil des Namens genügt. Leer = alle aktiven Quellen.'},
    {'key': 'serien', 'label': 'Serien-Ordner auch erlauben', 'type': 'bool', 'default': False},
    {'key': 'tiefe', 'label': 'Wie tief in die Ordner schauen (1-3)', 'type': 'number', 'default': 2, 'min': 1, 'max': 3},
]

_SKIP = re.compile(r'such|search|seite|weiter|next|zur(ü|ue)ck|back|a-z|^[a-z0-9#]$|cache|einstellung|login|anmeld|\b(?:tv|live|radio)\b', re.I)
_SERIES = re.compile(r'serie|staffel|season|folge|episod|anime|doku', re.I)
_api = None


def _words(text):
    return [w.strip().lower() for w in str(text or '').replace(';', ',').split(',') if w.strip()]


def _sources():
    want = _words(_api.get('quellen'))
    provs = _api.providers()
    if want:
        provs = [p for p in provs if any(w in (p['id'] + ' ' + p['name']).lower() for w in want)]
    random.shuffle(provs)
    return provs


def _plays(pid, folder, depth, budget, serien):
    """Abspielbare Einträge unterhalb eines Ordners einsammeln (höchstens `budget[0]` Abrufe)."""
    if budget[0] <= 0:
        return []
    budget[0] -= 1
    try:
        items = _api.open(pid, folder, fresh=False)
    except Exception:                                  # noqa: BLE001 - eine kaputte Quelle darf den Rest nicht stoppen
        return []
    plays = [i for i in items if i.get('kind') == 'play' and not i.get('episode')]
    if len(plays) >= 3:
        return plays
    if depth <= 0:
        return plays
    folders = [i for i in items if i.get('kind') == 'folder' and not _SKIP.search(i.get('title') or '')
               and (serien or not _SERIES.search(i.get('title') or '') and i.get('next_func') not in ('get_seasons', 'get_episodes'))]
    random.shuffle(folders)
    out = list(plays)
    for f in folders[:3]:
        out += _plays(pid, f, depth - 1, budget, serien)
        if len(out) >= 12 or budget[0] <= 0:
            break
    return out


def vorschlaege():
    n = max(1, int(_api.get('anzahl') or 6))
    depth = max(1, min(3, int(_api.get('tiefe') or 2)))
    serien = bool(_api.get('serien'))
    t0, found, seen = time.time(), [], set()
    for p in _sources()[:6]:
        pool = _plays(p['id'], {}, depth, [8], serien)
        random.shuffle(pool)
        for it in pool:
            k = (it.get('provider_id'), it.get('url'), it.get('title'))
            if k in seen:
                continue
            seen.add(k)
            found.append(it)
            if len(found) >= n * 2:
                break
        if len(found) >= n * 2 or time.time() - t0 > 25:
            break
    random.shuffle(found)
    return found[:n]


def register(api):
    global _api
    _api = api

    def menu():
        res = vorschlaege()
        if not res:
            api.fail('Keine Vorschläge gefunden. Prüfe, ob Quellen aktiv sind (oder die Einstellung „Nur diese Quellen“).')
        return res

    api.menu('🎲 Zufall', menu, ttl=0)
    api.route('probe', lambda req: {'n': len(vorschlaege())})
