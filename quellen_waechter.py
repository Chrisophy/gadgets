# -*- coding: utf-8 -*-
"""Quellen-Wächter: sagt im Familienchat Bescheid, wenn eine Quelle ausfällt - und wenn sie wieder läuft.

Die Engine prüft ihre Quellen ohnehin regelmäßig im Hintergrund (Diagnose). Der Wächter schaut dort nur nach und
belastet die Seiten nicht zusätzlich. Eine Quelle gilt als ausgefallen, wenn sie länger als die eingestellte Zeit
durchgehend leer oder fehlerhaft ist. Pro Ausfall kommt genau eine Meldung, nach der Erholung eine zweite.
"""
import threading
import time
from html import escape

EXT_ID = 'quellen_waechter'
EXT_NAME = 'Quellen-Wächter'
EXT_DESCRIPTION = 'Meldet im Familienchat, wenn eine Quelle länger ausfällt - und wenn sie wieder läuft.'
EXT_LINKS = [('Zustand der Quellen', 'index')]
EXT_SETTINGS = [
    {'key': 'ab_minuten', 'label': 'Als ausgefallen melden nach … Minuten', 'type': 'number', 'default': 60, 'min': 0, 'max': 1440},
    {'key': 'chat', 'label': 'Meldungen in den Familienchat schreiben', 'type': 'bool', 'default': True},
    {'key': 'erholung', 'label': 'Auch melden, wenn eine Quelle wieder läuft', 'type': 'bool', 'default': True},
    {'key': 'absender', 'label': 'Absender im Chat', 'type': 'text', 'default': '🩺 Quellen-Wächter'},
]

_api = None
_lock = threading.Lock()


def _snapshot():
    from engine import registry as R
    out = []
    for pid, p in list(R.REGISTRY.items()):
        if not getattr(p, 'enabled', False):
            continue
        h = R.HEALTH.get(pid) or {}
        out.append({'id': pid, 'name': getattr(p, 'name', pid), 'status': h.get('status') or 'unknown',
                    'since': h.get('bad_since'), 'error': h.get('error') or '', 'checked': h.get('checked') or 0})
    return out


def pruefen():
    """Gesundheitsstand lesen, Meldungen schreiben. Gibt die Zahl der gesendeten Meldungen zurück."""
    now = time.time()
    limit = float(_api.get('ab_minuten') or 0) * 60
    sent = 0
    with _lock:
        known = _api.get('known', {})
        known = known if isinstance(known, dict) else {}
        for s in _snapshot():
            was_down = bool(known.get(s['id']))
            bad = s['status'] in ('error', 'empty') and s['since'] and now - s['since'] >= limit
            if bad and not was_down:
                known[s['id']] = int(now)
                sent += _say('⚠️ %s ist ausgefallen: %s' % (s['name'], s['error'] or 'keine Antwort'))
            elif was_down and s['status'] == 'ok':
                known.pop(s['id'], None)
                if _api.get('erholung'):
                    sent += _say('✅ %s läuft wieder.' % s['name'])
        _api.set('known', known)
        _api.set('last', int(now))
    return sent


def _say(text):
    _api.set('log', (_api.get('log', []) or [])[-49:] + [{'t': int(time.time()), 'text': text}])
    if not _api.get('chat'):
        return 1
    try:
        _api.chat(text, author=_api.get('absender') or None)
    except Exception as e:                           # noqa: BLE001 - Chat nicht bereit: später erneut versuchen reicht nicht, aber nichts kaputt machen
        _api.log('Chat nicht erreichbar: %s' % e, 'warning')
    return 1


def register(api):
    global _api
    _api = api

    def page(req):
        rows = ''
        icons = {'ok': '✅', 'empty': '⚠️', 'error': '❌', 'unknown': '❔'}
        for s in sorted(_snapshot(), key=lambda x: (x['status'] == 'ok', x['name'].lower())):
            since = time.strftime('%d.%m. %H:%M', time.localtime(s['since'])) if s['since'] else ''
            rows += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (icons.get(s['status'], '❔'), escape(s['name']), escape(since), escape(s['error']))
        log = ''.join('<li>%s - %s</li>' % (time.strftime('%d.%m. %H:%M', time.localtime(e['t'])), escape(e['text'])) for e in reversed(api.get('log', []) or []))
        return ('<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Quellen</title>'
                '<style>body{font:15px/1.45 system-ui;margin:0;padding:18px;max-width:900px;margin-inline:auto;background:#0f141b;color:#e8edf3}'
                'td,th{padding:6px 8px;border-bottom:1px solid #2a3442;text-align:left}small{color:#93a1b3}</style>'
                '<h1>🩺 Zustand der Quellen</h1><table><tr><th></th><th>Quelle</th><th>Gestört seit</th><th>Grund</th></tr>%s</table>'
                '<h2>Letzte Meldungen</h2><ul>%s</ul></html>' % (rows, log or '<li><small>Noch keine.</small></li>'))

    api.route('index', page)
    api.route('jetzt', lambda req: {'gesendet': pruefen()} if req.method == 'POST' else ({'error': 'Nur per POST'}, 405))
    api.every(15, pruefen, name='Quellen ansehen', first_delay=120)
