# -*- coding: utf-8 -*-
# Sprachsuche
# IT('s) Possible 
# 2026.11.08
"""Sprachsuche als Gadget: ein Tipp auf die Kachel startet die Spracheingabe von MovieScout.

Für Geräte mit Mikrofon (Handy, Tablet, Fernbedienung mit Mikrofon). Die Kachel erscheint im Schnellzugriff der Startseite
und lässt sich im Desktop-Look über das Startmenü (Gadgets) auf die Arbeitsfläche legen. Einsetzen: diese Datei in den Ordner
userData/user/extensions/ kopieren (oder in der Erweiterungsliste hinzufügen) und aktivieren. Es gibt keine Einstellungen.
Ohne Mikrofon fragt MovieScout den Suchbegriff wie gewohnt per Tastatur ab.
"""
EXT_ID = 'sprachsuche'
EXT_NAME = 'Sprachsuche'
EXT_DESCRIPTION = 'Kachel zum Starten der Spracheingabe (Mikrofon) - auch für Looks ohne Kopfzeile.'
EXT_LINKS = [('Sprachsuche starten', 'index')]

_PAGE = ('<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
         '<title>Sprachsuche</title><style>body{margin:0;min-height:100vh;display:flex;flex-direction:column;align-items:center;'
         'justify-content:center;gap:16px;background:#0b1220;color:#e8edf7;font:18px system-ui,sans-serif;text-align:center}'
         'button{font:inherit;padding:14px 28px;border-radius:14px;border:0;background:#3b82f6;color:#fff}</style>'
         '<div style="font-size:64px">🎤</div><div id="m">Sprachsuche startet …</div>'
         '<button id="b" hidden onclick="go()">Sprachsuche starten</button>'
         '<script>function go(){var a=window.MovieScoutApp;'
         'if(a&&typeof a.startVoice==="function"){try{a.startVoice()}catch(e){}setTimeout(function(){history.back()},150);return true}'
         'try{var p=parent;p.voiceListen();p.closeTopLayer();return true}'
         'catch(e){document.getElementById("m").textContent="Bitte das Mikrofon der Oberfläche benutzen.";'
         'document.getElementById("b").hidden=false;return false}}go();</script></html>')


def register(api):
    api.route('index', lambda req: _PAGE)
    api.widget('Sprachsuche', lambda: {'icon': '🎤', 'sub': 'Mikrofon'}, ttl=3600, icon='🎤')
