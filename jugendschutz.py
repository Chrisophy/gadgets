# -*- coding: utf-8 -*-
"""Jugendschutz-Filter: blendet Einträge mit unerwünschten Wörtern im Titel aus - und auf Wunsch ganze Quellen.

So geht es: In den Einstellungen der Erweiterung stehen die Wörter (komma-getrennt). Es zählen ganze Wörter,
„Sex“ blendet also „Essex“ nicht aus. Ein * am Ende passt auf jedes Wortende: „erotik*“ trifft „Erotik“ und „Erotikfilme“.
Ganze Quellen blendest du über „Diese Quellen ausblenden“ aus (Teil des Namens genügt, z. B. „tube8“).
Die Seite „Was wurde ausgeblendet?“ zeigt zur Kontrolle, was der Filter zuletzt entfernt hat.
Wichtig: Der Filter gilt für alle Geräte, die diese Engine benutzen, und ist ein Hilfsmittel, kein Kopierschutz:
Wer Zugriff auf die Einstellungen hat, kann ihn ausschalten. Bereits zwischengespeicherte Listen (bis 10 Minuten)
zeigen nach einer Änderung noch den alten Stand - „Zwischenspeicher leeren“ hilft.
"""
import re
import threading
import time
from html import escape

EXT_ID = 'jugendschutz'
EXT_NAME = 'Jugendschutz-Filter'
EXT_DESCRIPTION = 'Blendet Titel mit unerwünschten Wörtern und ausgewählte Quellen aus; Kontrollseite zeigt, was entfernt wurde.'
EXT_LINKS = [('Was wurde ausgeblendet?', 'index')]
EXT_SETTINGS = [
    {'key': 'aktiv', 'label': 'Filter einschalten', 'type': 'bool', 'default': True},
    {'key': 'woerter', 'label': 'Unerwünschte Wörter', 'type': 'textarea',
     'default': 'erotik*, porn*, xxx, hentai, sexfilm*, fsk 18, ab 18, 18+, adult, nackt*',
     'hint': 'Komma-getrennt, Groß-/Kleinschreibung egal. Ganze Wörter; * am Ende = beliebige Fortsetzung.'},
    {'key': 'quellen', 'label': 'Diese Quellen ausblenden', 'type': 'text', 'default': '',
     'hint': 'Komma-getrennt, ein Teil des Namens genügt - z. B.  tube8, xvideos'},
    {'key': 'beschreibung', 'label': 'Auch die Beschreibung prüfen', 'type': 'bool', 'default': False,
     'hint': 'Strenger, blendet aber auch harmlose Filme aus, deren Inhaltsangabe ein Wort enthält.'},
]

MAX_HITS = 60
_api = None
_lock = threading.Lock()
_cache = {'raw': None, 'rx': None}


def _words(text):
    return [w.strip().lower() for w in str(text or '').replace(';', ',').replace('\n', ',').split(',') if w.strip()]


def _regex(raw):
    """Wörterliste -> ein Muster (zwischengemerkt, solange sich der Text nicht ändert)."""
    if _cache['raw'] == raw:
        return _cache['rx']
    parts = []
    for w in _words(raw):
        star = w.endswith('*')
        core = re.escape(w.rstrip('*').strip())
        if not core:
            continue
        parts.append(core + (r'\w*' if star else ''))
    rx = re.compile(r'(?<!\w)(?:' + '|'.join(parts) + r')(?!\w)', re.I) if parts else None
    _cache['raw'], _cache['rx'] = raw, rx
    return rx


def _log_hits(provider, rows):
    """rows = [(titel, grund)] - gesammelt in einem Zug gespeichert."""
    if not rows:
        return
    with _lock:
        hits = _api.get('hits', [])
        hits = hits if isinstance(hits, list) else []
        now = int(time.time())
        hits += [{'t': now, 'p': provider, 'title': str(t)[:120], 'why': w} for t, w in rows]
        _api.set('hits', hits[-MAX_HITS:])
        _api.set('count', int(_api.get('count', 0) or 0) + len(rows))


def process_items(provider_id, items):
    if _api is None or not _api.get('aktiv'):
        return None
    blocked_src = _words(_api.get('quellen'))
    if blocked_src:
        low = str(provider_id).lower()
        names = [low] + [str(p.get('name') or '').lower() for p in _api.providers() if p.get('id') == provider_id]
        if any(b in n for b in blocked_src for n in names):
            if items:
                _log_hits(provider_id, [('(%d Einträge)' % len(items), 'Quelle ausgeblendet')])
            return []
    rx = _regex(_api.get('woerter'))
    if rx is None:
        return None
    plot = bool(_api.get('beschreibung'))
    out, hits = [], []
    for it in items:
        text = str(it.get('title') or '')
        m = rx.search(text)
        if not m and plot:
            m = rx.search(str(it.get('plot') or ''))
        if m:
            hits.append((text, 'Wort: ' + m.group(0)))
            continue
        out.append(it)
    _log_hits(provider_id, hits)
    return out if hits else None


def register(api):
    global _api
    _api = api

    def page(req):
        hits = list(reversed(api.get('hits', []) or []))
        rows = ''.join('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
            time.strftime('%d.%m. %H:%M', time.localtime(h.get('t', 0))), escape(str(h.get('p', ''))), escape(h.get('title', '')), escape(h.get('why', '')))
            for h in hits)
        return ('<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                '<title>Jugendschutz</title><style>body{font:15px/1.45 system-ui;margin:0;padding:18px;max-width:900px;margin-inline:auto;background:#0f141b;color:#e8edf3}'
                'td,th{padding:6px 8px;border-bottom:1px solid #2a3442;text-align:left;vertical-align:top}small{color:#93a1b3}'
                'button{font:inherit;padding:8px 14px;border-radius:10px;border:1px solid #93a1b3;background:transparent;color:inherit;margin-top:16px}</style>'
                '<h1>🛡 Jugendschutz-Filter</h1><p>Filter: <b>%s</b> · bisher ausgeblendet: <b>%d</b> Einträge</p>'
                '<p><small>Zuletzt entfernt (höchstens %d, neueste oben):</small></p>'
                '<table><tr><th>Wann</th><th>Quelle</th><th>Titel</th><th>Grund</th></tr>%s</table>%s'
                '<button onclick="fetch(\'leeren\',{method:\'POST\'}).then(()=>location.reload())">Liste leeren</button></html>'
                % ('an' if api.get('aktiv') else 'aus', int(api.get('count', 0) or 0), MAX_HITS, rows, '' if rows else '<p>Noch nichts ausgeblendet.</p>'))

    def clear(req):
        if req.method != 'POST':
            return ({'error': 'Nur per POST'}, 405)
        api.set('hits', [])
        return {'ok': True}

    api.route('index', page)
    api.route('leeren', clear)
    api.route('status', lambda req: {'aktiv': bool(api.get('aktiv')), 'count': int(api.get('count', 0) or 0)})
