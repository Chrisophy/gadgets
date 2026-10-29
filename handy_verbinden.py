# -*- coding: utf-8 -*-
"""Handy verbinden: Kachel mit der Adresse, unter der MovieScout im Heimnetz erreichbar ist.

Gedacht für den Fernseher oder PC: Die Adresse steht groß in der Kachel (und im Bildschirmschoner), das Handy muss im
selben WLAN sein und sie im Browser öffnen. Mit „Teilen im WLAN“ (Einstellungen) legst du zusätzlich ein Passwort fest.
"""
import socket
import sys

EXT_ID = 'handy_verbinden'
EXT_NAME = 'Handy verbinden'
EXT_DESCRIPTION = 'Kachel mit der WLAN-Adresse von MovieScout - zum Abtippen am Handy.'
EXT_LINKS = [('Adresse anzeigen', 'adresse')]
_api = None


def _port():
    a = sys.argv
    for i, x in enumerate(a):
        if x == '--port' and i + 1 < len(a) and a[i + 1].isdigit():
            return int(a[i + 1])
        if x.startswith('--port=') and x[7:].isdigit():
            return int(x[7:])
    return 8000


def _ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(1)
        s.connect(('10.255.255.255', 1))          # sendet nichts, wählt nur die passende Netzwerkkarte
        ip = s.getsockname()[0]
    except OSError:
        ip = ''
    finally:
        s.close()
    return '' if ip.startswith('127.') else ip


def adresse():
    ip = _ip()
    return 'http://%s:%d/ui/' % (ip, _port()) if ip else ''


def widget():
    url = adresse()
    if not url:
        return {'icon': '📵', 'text': 'kein WLAN', 'sub': 'Keine Heimnetz-Adresse gefunden'}
    return {'text': url.replace('http://', '').replace('/ui/', ''), 'sub': 'Am Handy im selben WLAN im Browser öffnen',
            'lines': [url]}


def register(api):
    global _api
    _api = api
    api.widget('Handy verbinden', widget, ttl=120, icon='📱')
    api.route('adresse', lambda req: {'url': adresse(), 'port': _port()})
