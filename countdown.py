# -*- coding: utf-8 -*-
"""Countdown: Tage bis zu Urlaub, Geburtstagen und anderen Terminen - als Kachel auf der Startseite.

Die Termine stehen in den Einstellungen, einer pro Zeile:
    Urlaub am Meer; 2027-07-12            einmaliger Termin (JJJJ-MM-TT oder TT.MM.JJJJ)
    Hochzeitstag; 14.06.                  jedes Jahr am 14.6.
    Anna; 03.05.1990; j                   jährlich, mit Alter („wird 36“)
Die Kachel zeigt den nächsten Termin groß und die zwei danach darunter.
"""
import re
from datetime import date

EXT_ID = 'countdown'
EXT_NAME = 'Countdown'
EXT_DESCRIPTION = 'Kachel „Noch X Tage“ für Urlaub, Geburtstage und Termine (einmalig oder jährlich, mit Alter).'
EXT_SETTINGS = [
    {'key': 'termine', 'label': 'Termine (einer pro Zeile)', 'type': 'textarea', 'default': '',
     'hint': 'Name; Datum   - z. B.  Urlaub; 2027-07-12   |   Hochzeitstag; 14.06.   |   Anna; 03.05.1990; j  (jährlich mit Alter)'},
]
_api = None
_RX = re.compile(r'^\s*(?:(\d{4})-(\d{1,2})-(\d{1,2})|(\d{1,2})\.(\d{1,2})\.(\d{4})?)\s*$')


def parse(text):
    """Zeilen -> Liste von {'name', 'm', 'd', 'y' (oder None), 'jaehrlich', 'alter'}; kaputte Zeilen werden übersprungen."""
    out = []
    for line in str(text or '').splitlines():
        parts = [p.strip() for p in line.split(';')]
        if len(parts) < 2 or not parts[0]:
            continue
        m = _RX.match(parts[1])
        if not m:
            continue
        if m.group(1):
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        else:
            d, mo = int(m.group(4)), int(m.group(5))
            y = int(m.group(6)) if m.group(6) else None
        flag = (parts[2].lower() if len(parts) > 2 else '')
        yearly = y is None or flag in ('j', 'jaehrlich', 'jährlich', 'ja')
        try:
            date(y or 2000, mo, d)                       # 2000 ist ein Schaltjahr: 29.2. bleibt erlaubt
        except ValueError:
            continue
        out.append({'name': parts[0][:60], 'm': mo, 'd': d, 'y': y, 'jaehrlich': yearly, 'alter': y is not None and yearly})
    return out


def _on(year, e):
    try:
        return date(year, e['m'], e['d'])
    except ValueError:                                   # 29.2. in Nicht-Schaltjahren -> 28.2.
        return date(year, 2, 28)


def kommende(termine, heute):
    """Sortierte Liste (Datum, Eintrag, Alter oder None) ab heute; vergangene einmalige Termine entfallen."""
    out = []
    for e in termine:
        if e['jaehrlich']:
            d = _on(heute.year, e)
            if d < heute:
                d = _on(heute.year + 1, e)
            out.append((d, e, (d.year - e['y']) if e['alter'] else None))
        else:
            d = date(e['y'], e['m'], e['d'])
            if d >= heute:
                out.append((d, e, None))
    return sorted(out, key=lambda x: (x[0], x[1]['name']))


def wann(d, heute):
    n = (d - heute).days
    return 'heute!' if n == 0 else 'morgen' if n == 1 else '%d Tage' % n


def zeile(x, heute):
    d, e, alter = x
    return '%s: %s, %d.%d.%s' % (e['name'], wann(d, heute), d.day, d.month, (' (wird %d)' % alter) if alter else '')


def widget():
    heute = date.today()
    k = kommende(parse(_api.get('termine')), heute)
    if not k:
        return {'icon': '⏳', 'text': 'Keine Termine', 'sub': 'Einstellungen der Erweiterung „Countdown“'}
    d, e, alter = k[0]
    return {'icon': '🎂' if alter else '⏳', 'text': wann(d, heute), 'sub': e['name'] + ((' wird %d' % alter) if alter else ''),
            'lines': [zeile(x, heute) for x in k[1:3]]}


def register(api):
    global _api
    _api = api
    api.widget('Countdown', widget, ttl=600, icon='⏳')
    api.route('liste', lambda req: {'termine': [{'name': e['name'], 'datum': d.isoformat(), 'tage': (d - date.today()).days, 'alter': a}
                                                for d, e, a in kommende(parse(api.get('termine')), date.today())]})
