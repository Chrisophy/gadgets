# -*- coding: utf-8 -*-
"""Feiertage: Kachel „Nächster Feiertag“ mit Countdown (gesetzliche Feiertage in Deutschland, ohne Internet).

Das Bundesland stellst du in den Einstellungen ein. Die Kachel zeigt auch die zwei Feiertage danach.
Praktisch für den Bildschirmschoner und für die Frage „Ist morgen frei?“.
"""
from datetime import date, timedelta

EXT_ID = 'feiertage'
EXT_NAME = 'Feiertage'
EXT_DESCRIPTION = 'Kachel „Nächster Feiertag“ mit Countdown für dein Bundesland (offline berechnet).'
LAENDER = [('BW', 'Baden-Württemberg'), ('BY', 'Bayern'), ('BE', 'Berlin'), ('BB', 'Brandenburg'), ('HB', 'Bremen'), ('HH', 'Hamburg'),
           ('HE', 'Hessen'), ('MV', 'Mecklenburg-Vorpommern'), ('NI', 'Niedersachsen'), ('NW', 'Nordrhein-Westfalen'),
           ('RP', 'Rheinland-Pfalz'), ('SL', 'Saarland'), ('SN', 'Sachsen'), ('ST', 'Sachsen-Anhalt'), ('SH', 'Schleswig-Holstein'), ('TH', 'Thüringen')]
EXT_SETTINGS = [{'key': 'land', 'label': 'Bundesland', 'type': 'select', 'default': 'NW', 'options': [[k, v] for k, v in LAENDER]}]
_api = None


def ostern(jahr):
    """Ostersonntag (Gauß-Algorithmus)."""
    a, b, c = jahr % 19, jahr // 100, jahr % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    monat, tag = divmod(h + l - 7 * m + 114, 31)
    return date(jahr, monat, tag + 1)


def feiertage(jahr, land):
    """{Datum: Name} der gesetzlichen Feiertage im Bundesland."""
    o = ostern(jahr)
    t = {date(jahr, 1, 1): 'Neujahr', o - timedelta(days=2): 'Karfreitag', o + timedelta(days=1): 'Ostermontag',
         date(jahr, 5, 1): 'Tag der Arbeit', o + timedelta(days=39): 'Christi Himmelfahrt', o + timedelta(days=50): 'Pfingstmontag',
         date(jahr, 10, 3): 'Tag der Deutschen Einheit', date(jahr, 12, 25): '1. Weihnachtstag', date(jahr, 12, 26): '2. Weihnachtstag'}
    if land in ('BW', 'BY', 'ST'):
        t[date(jahr, 1, 6)] = 'Heilige Drei Könige'
    if land in ('BE', 'MV'):
        t[date(jahr, 3, 8)] = 'Internationaler Frauentag'
    if land == 'BB':
        t[o] = 'Ostersonntag'
        t[o + timedelta(days=49)] = 'Pfingstsonntag'
    if land in ('BW', 'BY', 'HE', 'NW', 'RP', 'SL'):
        t[o + timedelta(days=60)] = 'Fronleichnam'
    if land == 'SL':
        t[date(jahr, 8, 15)] = 'Mariä Himmelfahrt'
    if land == 'TH':
        t[date(jahr, 9, 20)] = 'Weltkindertag'
    if land in ('BB', 'HB', 'HH', 'MV', 'NI', 'SN', 'ST', 'SH', 'TH'):
        t[date(jahr, 10, 31)] = 'Reformationstag'
    if land in ('BW', 'BY', 'NW', 'RP', 'SL'):
        t[date(jahr, 11, 1)] = 'Allerheiligen'
    if land == 'SN':
        d = date(jahr, 11, 22)
        while d.weekday() != 2:
            d -= timedelta(days=1)
        t[d] = 'Buß- und Bettag'
    return t


def naechste(heute, land, n=3):
    out = []
    for jahr in (heute.year, heute.year + 1):
        out += [(d, name) for d, name in feiertage(jahr, land).items() if d >= heute]
    return sorted(out)[:n]


def _tage(d, heute):
    n = (d - heute).days
    return 'heute' if n == 0 else 'morgen' if n == 1 else 'in %d Tagen' % n


WOCHE = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']


def widget():
    heute = date.today()
    land = (_api.get('land') if _api else None) or 'NW'
    liste = naechste(heute, land, 3)
    d, name = liste[0]
    return {'text': _tage(d, heute), 'sub': '%s, %s' % (name, '%s %d.%d.' % (WOCHE[d.weekday()], d.day, d.month)),
            'lines': ['%s: %s %d.%d.' % (n2, WOCHE[d2.weekday()], d2.day, d2.month) for d2, n2 in liste[1:]]}


def register(api):
    global _api
    _api = api
    api.widget('Nächster Feiertag', widget, ttl=3600, icon='🎉')
    api.route('liste', lambda req: {'land': api.get('land'), 'feiertage': [{'datum': d.isoformat(), 'name': n}
                                                                         for d, n in sorted(feiertage(date.today().year, api.get('land') or 'NW').items())]})
