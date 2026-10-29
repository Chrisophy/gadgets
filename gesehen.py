# -*- coding: utf-8 -*-
"""Gesehen-Haken: Filme und Folgen, die du fertig geschaut hast, bekommen vorn ein ✓.

So geht es: Wird eine Wiedergabe bis fast zum Ende geschaut (Standard: 90 %), merkt sich die Erweiterung den Titel.
In allen Listen steht dann vor dem Titel ein ✓. In der Titel-Info gibt es außerdem den Knopf „✓ Gesehen / Ungesehen“,
um von Hand umzuschalten. Die Haken gelten für alle Geräte, die diese Engine benutzen.
Neue Haken erscheinen sofort (die Zwischenspeicher der Listen werden dafür geleert).
"""
import threading
import time

EXT_ID = 'gesehen'
EXT_NAME = 'Gesehen-Haken'
EXT_DESCRIPTION = 'Setzt vor fertig geschaute Filme und Folgen ein ✓; Knopf zum Umschalten in der Titel-Info.'
EXT_LINKS = [('Gesehen-Liste', 'liste')]
EXT_SETTINGS = [
    {'key': 'schwelle', 'label': 'Als gesehen zählt ab … % der Laufzeit', 'type': 'number', 'default': 90, 'min': 50, 'max': 100},
    {'key': 'zeichen', 'label': 'Zeichen vor dem Titel', 'type': 'text', 'default': '✓'},
]

MAX_SEEN = 20000
_api = None
_lock = threading.Lock()


def _mark():
    return (str(_api.get('zeichen') or '✓').strip() or '✓') + ' ' if _api else '✓ '


def _key(pid, item):
    return '%s|%s|%s|%s' % (pid or item.get('provider_id') or '', item.get('url') or str(item.get('title') or '').lstrip('✓ ').strip(),
                            item.get('season') or '', item.get('episode') or '')


def _seen():
    d = _api.get('seen', {})
    return d if isinstance(d, dict) else {}


def _forget_lists():
    """Zwischenspeicher der Listen leeren, damit die Haken sofort sichtbar werden."""
    try:
        from engine import registry as R
        R._LIST_C.clear()
    except Exception:                                  # noqa: BLE001 - nur Komfort
        pass


def _set(item, value, title=None):
    with _lock:
        d = _seen()
        k = _key('', item)
        if value:
            d[k] = {'t': int(time.time()), 'title': (title or item.get('parent_title') or item.get('title') or '')[:120]}
            if len(d) > MAX_SEEN:
                for old in sorted(d, key=lambda x: d[x].get('t', 0))[:len(d) - MAX_SEEN]:
                    d.pop(old, None)
        else:
            d.pop(k, None)
        _api.set('seen', d)
    _forget_lists()


def on_stop(item, info):
    if _api is None:
        return
    try:
        pos, dur = float(info.get('position') or 0), float(info.get('duration') or 0)
    except (TypeError, ValueError):
        return
    schwelle = float(_api.get('schwelle') or 90) / 100.0
    if info.get('finished') or (dur > 0 and pos / dur >= schwelle):
        _set(item, True)


def process_items(provider_id, items):
    if _api is None:
        return None
    d = _seen()
    if not d:
        return None
    mark = _mark()
    out = []
    for it in items:
        if it.get('kind') == 'play' and _key(provider_id, it) in d and not str(it.get('title') or '').startswith(mark):
            it = dict(it, title=mark + str(it.get('title') or ''))
        out.append(it)
    return out


def register(api):
    global _api
    _api = api

    def toggle(item):
        item = dict(item)
        k = _key('', item)
        if k in _seen():
            _set(item, False)
            return 'Wieder ungesehen: %s' % item.get('title')
        _set(item, True)
        return 'Als gesehen markiert: %s' % item.get('title')

    def liste(req):
        from html import escape
        rows = sorted(_seen().values(), key=lambda v: -v.get('t', 0))[:300]
        lis = ''.join('<li>%s <small>%s</small></li>' % (escape(r.get('title', '')), time.strftime('%d.%m.%Y', time.localtime(r.get('t', 0)))) for r in rows)
        return ('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Gesehen</title>'
                '<style>body{font:16px/1.5 system-ui;margin:0;padding:18px;max-width:700px;margin-inline:auto;background:#0f141b;color:#e8edf3}small{color:#93a1b3}</style>'
                '<h1>✓ Gesehen (%d)</h1><ol>%s</ol>' % (len(_seen()), lis or '<p>Noch nichts.</p>'))

    api.route('liste', liste)
    api.route('status', lambda req: {'count': len(_seen())})
    api.item_action('✓ Gesehen / Ungesehen', toggle, needs='url')
