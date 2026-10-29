# -*- coding: utf-8 -*-
"""Statistik: wie viel wurde geschaut? (Woche, Monat, Jahr, Lieblingstitel und -quellen)

Die Erweiterung zählt mit, wenn eine Wiedergabe endet, und rechnet daraus die ungefähre Sehzeit aus.
Zu sehen ist das Ergebnis als Kachel „Diese Woche“ auf der Startseite (und im Bildschirmschoner) und auf der
Seite „Meine Statistik“ (Erweiterungsliste -> Statistik -> Meine Statistik).
Hinweis: Die Zahlen gelten für die ganze Engine, also für alle Geräte, die sie benutzen. Gespeichert wird nur Titel,
Quelle, Zeitpunkt und Dauer - nichts verlässt dein Gerät.
"""
import threading
import time
from datetime import datetime, timedelta
from html import escape

EXT_ID = 'statistik'
EXT_NAME = 'Statistik'
EXT_DESCRIPTION = 'Zählt die Sehzeit: Kachel „Diese Woche“ und Seite mit Monat, Jahr, Lieblingstiteln und Quellen.'
EXT_LINKS = [('Meine Statistik', 'index')]
EXT_SETTINGS = [
    {'key': 'aktiv', 'label': 'Wiedergaben mitzählen', 'type': 'bool', 'default': True},
    {'key': 'min_sek', 'label': 'Erst ab … Sekunden zählen', 'type': 'number', 'default': 60, 'min': 0, 'max': 3600,
     'hint': 'Kurzes Reinschauen (Vorschau, Probieren) soll die Zahlen nicht verfälschen.'},
    {'key': 'ziel', 'label': 'Wochenziel in Stunden (0 = keins)', 'type': 'number', 'default': 0, 'min': 0, 'max': 200},
]

MAX_LOG = 5000
_api = None
_starts = {}
_lock = threading.Lock()


def _key(item):
    return '%s|%s|%s|%s' % (item.get('provider_id') or '', item.get('url') or item.get('title') or '',
                            item.get('season') or '', item.get('episode') or '')


def _clean_title(t):
    t = str(t or '').strip()
    return t[2:].strip() if t.startswith('✓ ') else t


def on_play(item, info):
    if _api is None:
        return
    with _lock:
        now = time.time()
        for k in [k for k, v in _starts.items() if now - v > 43200]:
            _starts.pop(k, None)
        _starts[_key(item)] = now


def on_stop(item, info):
    if _api is None or not _api.get('aktiv'):
        return
    now = time.time()
    with _lock:
        start = _starts.pop(_key(item), None)
    try:
        pos = float(info.get('position') or 0)
        dur = float(info.get('duration') or 0)
    except (TypeError, ValueError):
        pos = dur = 0
    sec = (now - start) if start else pos          # lief die Engine neu, bleibt nur die Position
    if dur > 0:
        sec = min(sec, dur)
    sec = int(min(sec, 43200))
    if sec < max(1, int(_api.get('min_sek') or 0)):
        return
    parent = _clean_title(item.get('parent_title'))
    title = _clean_title(item.get('title')) or 'Unbekannt'
    entry = {'t': int(now), 'sec': sec, 'title': parent or title,
             'ep': title if parent else '', 'p': item.get('provider') or item.get('provider_id') or '?',
             'k': 'serie' if (parent or item.get('season') or item.get('episode')) else 'film'}
    with _lock:
        log = _api.get('log', [])
        if not isinstance(log, list):
            log = []
        log.append(entry)
        _api.set('log', log[-MAX_LOG:])


def _fmt(sec):
    sec = int(sec)
    h, m = divmod(sec // 60, 60)
    if h:
        return '%d h %02d min' % (h, m)
    return '%d min' % m


def _sums(log, now=None):
    now = now or datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week0 = (today - timedelta(days=today.weekday())).timestamp()
    month0 = today.replace(day=1).timestamp()
    year0 = today.replace(month=1, day=1).timestamp()
    out = {'week': 0, 'month': 0, 'year': 0, 'all': 0, 'n_week': 0, 'n_all': len(log)}
    for e in log:
        t, s = e.get('t', 0), e.get('sec', 0)
        out['all'] += s
        if t >= year0:
            out['year'] += s
        if t >= month0:
            out['month'] += s
        if t >= week0:
            out['week'] += s
            out['n_week'] += 1
    return out


def _days(log, n=14, now=None):
    now = now or datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    names = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
    rows = []
    for i in range(n - 1, -1, -1):
        d0 = today - timedelta(days=i)
        a, b = d0.timestamp(), (d0 + timedelta(days=1)).timestamp()
        rows.append({'label': '%s %d.%d.' % (names[d0.weekday()], d0.day, d0.month),
                     'sec': sum(e['sec'] for e in log if a <= e.get('t', 0) < b)})
    return rows


def _top(log, field, n=5):
    acc = {}
    for e in log:
        k = e.get(field) or '?'
        a = acc.setdefault(k, [0, 0])
        a[0] += e.get('sec', 0)
        a[1] += 1
    return [{'name': k, 'sec': v[0], 'n': v[1]} for k, v in sorted(acc.items(), key=lambda kv: -kv[1][0])[:n]]


def _data():
    log = _api.get('log', [])
    log = log if isinstance(log, list) else []
    kinds = {'film': 0, 'serie': 0}
    for e in log:
        kinds[e.get('k') if e.get('k') in kinds else 'film'] += e.get('sec', 0)
    return {'sums': _sums(log), 'days': _days(log), 'titles': _top(log, 'title'), 'sources': _top(log, 'p'), 'kinds': kinds,
            'count': len(log)}


def _page(req):
    d = _data()
    s = d['sums']
    peak = max([x['sec'] for x in d['days']] + [1])
    ziel = float(_api.get('ziel') or 0)

    def card(label, sec, sub=''):
        return '<div class="c"><b>%s</b><span>%s</span><i>%s</i></div>' % (escape(_fmt(sec)), escape(label), escape(sub))

    bars = ''.join('<div class="d"><div class="b" style="height:%d%%" title="%s"></div><span>%s</span></div>'
                   % (max(2, round(100 * x['sec'] / peak)) if x['sec'] else 0, escape(_fmt(x['sec'])), escape(x['label'].split(' ')[0]))
                   for x in d['days'])

    def lst(rows):
        if not rows:
            return '<p class="m">Noch nichts gezählt.</p>'
        return '<ol>' + ''.join('<li>%s <small>%s · %d×</small></li>' % (escape(str(r['name'])), escape(_fmt(r['sec'])), r['n']) for r in rows) + '</ol>'

    goal = ''
    if ziel > 0:
        pct = min(100, round(100 * s['week'] / (ziel * 3600)))
        goal = '<p class="m">Wochenziel %g h: %d %% erreicht.</p><div class="g"><div style="width:%d%%"></div></div>' % (ziel, pct, pct)
    total = d['kinds']['film'] + d['kinds']['serie']
    share = ('Filme %d %% · Serien %d %%' % (round(100 * d['kinds']['film'] / total), round(100 * d['kinds']['serie'] / total))) if total else ''
    return ('<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Meine Statistik</title><style>'
            ':root{--bg:#0f141b;--fg:#e8edf3;--mut:#93a1b3;--card:#18202b;--acc:#4da3ff}'
            '@media(prefers-color-scheme:light){:root{--bg:#f4f6f9;--fg:#18202b;--mut:#5d6b7c;--card:#fff;--acc:#1b6fd1}}'
            'body{margin:0;padding:18px 16px 60px;background:var(--bg);color:var(--fg);font:16px/1.45 system-ui,sans-serif;max-width:760px;margin-inline:auto}'
            'h1{font-size:1.4rem;margin:.2em 0 .6em}h2{font-size:1.05rem;margin:1.6em 0 .4em}'
            '.row{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px}'
            '.c{background:var(--card);border-radius:12px;padding:12px 14px;display:flex;flex-direction:column}'
            '.c b{font-size:1.35rem;color:var(--acc)}.c span{font-weight:600}.c i{color:var(--mut);font-style:normal;font-size:.85rem}'
            '.chart{display:flex;gap:4px;align-items:flex-end;height:120px;background:var(--card);border-radius:12px;padding:10px 8px 6px}'
            '.d{flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;height:100%;gap:4px}'
            '.b{width:100%;background:var(--acc);border-radius:4px 4px 0 0;min-height:0}.d span{font-size:.7rem;color:var(--mut)}'
            'ol{padding-left:1.3em;margin:.2em 0}li{margin:.25em 0}small,.m{color:var(--mut)}'
            '.g{height:10px;background:var(--card);border-radius:5px;overflow:hidden}.g div{height:100%;background:var(--acc)}'
            'button{font:inherit;padding:8px 14px;border-radius:10px;border:1px solid var(--mut);background:transparent;color:var(--fg);margin-top:22px}'
            '</style><h1>📊 Meine Statistik</h1>'
            '<div class="row">' + card('Diese Woche', s['week'], '%d Wiedergaben' % s['n_week']) + card('Dieser Monat', s['month'])
            + card('Dieses Jahr', s['year']) + card('Insgesamt', s['all'], '%d Wiedergaben' % s['n_all']) + '</div>' + goal +
            '<h2>Letzte 14 Tage</h2><div class="chart">' + bars + '</div>'
            '<h2>Lieblingstitel</h2>' + lst(d['titles']) + '<h2>Quellen</h2>' + lst(d['sources'])
            + ('<p class="m">' + escape(share) + '</p>' if share else '') +
            '<p class="m">Die Sehzeit ist eine Schätzung (Pausen zählen mit). Gezählt wird für alle Geräte, die diese Engine benutzen.</p>'
            '<button onclick="if(confirm(\'Alle gezählten Wiedergaben löschen?\'))fetch(\'reset\',{method:\'POST\'}).then(()=>location.reload())">Statistik zurücksetzen</button>'
            '</html>')


def register(api):
    global _api
    _api = api

    def widget():
        s = _sums(api.get('log', []) if isinstance(api.get('log', []), list) else [])
        ziel = float(api.get('ziel') or 0)
        lines = []
        if ziel > 0:
            lines.append('Ziel %g h: %d %%' % (ziel, min(100, round(100 * s['week'] / (ziel * 3600)))))
        return {'text': _fmt(s['week']), 'sub': 'geschaut diese Woche · %d Wiedergaben' % s['n_week'],
                'lines': lines + ['Monat: ' + _fmt(s['month']), 'Jahr: ' + _fmt(s['year'])]}

    def reset(req):
        if req.method != 'POST':
            return ({'error': 'Nur per POST'}, 405)
        api.set('log', [])
        return {'ok': True}

    api.route('index', _page)
    api.route('daten', lambda req: _data())
    api.route('reset', reset)
    api.widget('Diese Woche', widget, ttl=300, icon='📊')
