# -*- coding: utf-8 -*-
"""Himmel: Sonnenauf- und -untergang, Tageslänge und Mondphase - offline berechnet, als Kachel.

Stelle in den Einstellungen deinen Ort ein (Breiten-/Längengrad, z. B. aus Google Maps: Rechtsklick auf den Ort).
Die Zeiten gelten in der Zeitzone des Geräts, auf dem die Engine läuft. Genauigkeit: wenige Minuten.
"""
import math
from datetime import date, datetime, timedelta, timezone

EXT_ID = 'himmel'
EXT_NAME = 'Himmel'
EXT_DESCRIPTION = 'Kachel mit Sonnenauf-/-untergang, Tageslänge und Mondphase (offline berechnet).'
EXT_SETTINGS = [
    {'key': 'breite', 'label': 'Breitengrad', 'type': 'number', 'default': 51.2277, 'min': -66, 'max': 66, 'hint': 'Nord positiv. Standard: Düsseldorf.'},
    {'key': 'laenge', 'label': 'Längengrad', 'type': 'number', 'default': 6.7735, 'min': -180, 'max': 180, 'hint': 'Ost positiv.'},
]
_api = None
SYNODISCH = 29.530588853
NEUMOND_0 = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
PHASEN = [('🌑', 'Neumond'), ('🌒', 'zunehmende Sichel'), ('🌓', 'erstes Viertel'), ('🌔', 'zunehmender Mond'),
          ('🌕', 'Vollmond'), ('🌖', 'abnehmender Mond'), ('🌗', 'letztes Viertel'), ('🌘', 'abnehmende Sichel')]


def sonne_ut(tag, breite, laenge, aufgang=True):
    """Aufgang/Untergang als UTC-Stunden (0-24) oder None (Polartag/-nacht). Almanac-Algorithmus, Zenit 90,833°."""
    n = tag.timetuple().tm_yday
    lh = laenge / 15.0
    t = n + ((6 if aufgang else 18) - lh) / 24.0
    m = 0.9856 * t - 3.289
    rad = math.radians
    l = (m + 1.916 * math.sin(rad(m)) + 0.020 * math.sin(rad(2 * m)) + 282.634) % 360
    ra = math.degrees(math.atan(0.91764 * math.tan(rad(l)))) % 360
    ra += math.floor(l / 90) * 90 - math.floor(ra / 90) * 90
    ra /= 15.0
    sin_dec = 0.39782 * math.sin(rad(l))
    cos_dec = math.cos(math.asin(sin_dec))
    cos_h = (math.cos(rad(90.833)) - sin_dec * math.sin(rad(breite))) / (cos_dec * math.cos(rad(breite)))
    if cos_h > 1 or cos_h < -1:
        return None
    h = (360 - math.degrees(math.acos(cos_h))) if aufgang else math.degrees(math.acos(cos_h))
    h /= 15.0
    tt = h + ra - 0.06571 * t - 6.622
    return (tt - lh) % 24


def lokal(tag, ut):
    """UTC-Stunden -> lokale Uhrzeit (Zeitzone des Rechners, inkl. Sommerzeit)."""
    if ut is None:
        return None
    base = datetime(tag.year, tag.month, tag.day, tzinfo=timezone.utc)
    return (base + timedelta(hours=ut)).astimezone()


def mond(zeit):
    """(Phase 0..1, Beleuchtung in Prozent, Emoji, Name) für einen Zeitpunkt (aware datetime)."""
    f = (((zeit - NEUMOND_0).total_seconds() / 86400.0) % SYNODISCH) / SYNODISCH
    hell = round((1 - math.cos(2 * math.pi * f)) / 2 * 100)
    emoji, name = PHASEN[int(f * 8 + 0.5) % 8]
    return f, hell, emoji, name


def naechster(zeit, ziel):
    """Nächster Zeitpunkt (aware) mit Phase `ziel` (0 = Neumond, 0.5 = Vollmond)."""
    k = math.floor((zeit - NEUMOND_0).total_seconds() / 86400.0 / SYNODISCH)
    for i in (0, 1, 2):
        t = NEUMOND_0 + timedelta(days=(k + i + ziel) * SYNODISCH)
        if t > zeit:
            return t
    return zeit


def widget():
    breite, laenge = float(_api.get('breite')), float(_api.get('laenge'))
    heute = date.today()
    auf, unter = lokal(heute, sonne_ut(heute, breite, laenge, True)), lokal(heute, sonne_ut(heute, breite, laenge, False))
    jetzt = datetime.now(timezone.utc)
    _, hell, emoji, name = mond(jetzt)
    voll = naechster(jetzt, 0.5).astimezone()
    neu = naechster(jetzt, 0.0).astimezone()
    if auf is None or unter is None:
        return {'icon': '🌌', 'text': 'Polartag/-nacht', 'sub': '%s %s · %d %%' % (emoji, name, hell)}
    laenge_min = int((unter - auf).total_seconds() // 60)
    return {'icon': '🌅', 'text': '↑ %s  ↓ %s' % (auf.strftime('%H:%M'), unter.strftime('%H:%M')),
            'sub': '%s %s · %d %% beleuchtet' % (emoji, name, hell),
            'lines': ['Tageslänge: %d h %02d min' % divmod(laenge_min, 60),
                      'Nächster Vollmond: %s' % voll.strftime('%d.%m.'), 'Nächster Neumond: %s' % neu.strftime('%d.%m.')]}


def register(api):
    global _api
    _api = api
    api.widget('Himmel', widget, ttl=900, icon='🌅')
    api.route('heute', lambda req: {'mond': dict(zip(('phase', 'hell', 'emoji', 'name'), mond(datetime.now(timezone.utc)))),
                                    'sonne_ut': [sonne_ut(date.today(), float(api.get('breite')), float(api.get('laenge')), a) for a in (True, False)]})
