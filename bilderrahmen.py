# -*- coding: utf-8 -*-
"""Bilderrahmen: eigene Fotos im Bildschirmschoner (statt oder zusätzlich zu den Titelbildern).

So geht es: In den Einstellungen einen Ordner mit Fotos eintragen (Ordner auf dem Gerät, auf dem MovieScout läuft, z. B.
/home/ich/Bilder/Urlaub oder D:\\Fotos) und/oder Bildadressen (https://…), eine pro Zeile. Der Bildschirmschoner mischt diese
Bilder unter die Titelbilder.
Die Seite „Alle Bilder ansehen“ zeigt eine Übersicht. Nur Dateien .jpg .jpeg .png .gif .webp bis 15 MB aus genau diesem Ordner werden ausgeliefert.
"""
import html
import os
import random
import re

EXT_ID = 'bilderrahmen'
EXT_NAME = 'Bilderrahmen'
EXT_DESCRIPTION = 'Eigene Fotos (Ordner oder Adressen) laufen im Bildschirmschoner mit.'
EXT_LINKS = [('Alle Bilder ansehen', 'index')]
EXT_SETTINGS = [
    {'key': 'ordner', 'label': 'Foto-Ordner', 'type': 'text', 'default': '', 'hint': 'Ordner auf dem Gerät mit der Engine (Unterordner werden mitgelesen).'},
    {'key': 'adressen', 'label': 'Bildadressen (eine pro Zeile)', 'type': 'textarea', 'default': ''},
    {'key': 'anzahl', 'label': 'Bilder pro Durchgang', 'type': 'number', 'default': 25, 'min': 5, 'max': 40},
]

EXT = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
MAX_FILE = 15 * 1024 * 1024
_api = None


def dateien():
    root = str(_api.get('ordner') or '').strip()
    out = []
    if root and os.path.isdir(root):
        root = os.path.realpath(root)
        for d, _dirs, files in os.walk(root):
            for f in files:
                if f.lower().endswith(EXT):
                    out.append(os.path.relpath(os.path.join(d, f), root).replace(os.sep, '/'))
            if len(out) > 5000:
                break
    return sorted(out)


def adressen():
    return [u.strip() for u in str(_api.get('adressen') or '').splitlines() if re.match(r'https?://', u.strip(), re.I)]


def lesen(rel):
    """Datei aus dem Foto-Ordner lesen; None, wenn nicht erlaubt (Pfad außerhalb, falscher Typ, zu groß)."""
    root = str(_api.get('ordner') or '').strip()
    if not root or not rel or not rel.lower().endswith(EXT):
        return None
    root = os.path.realpath(root)
    p = os.path.realpath(os.path.join(root, rel))
    if os.path.commonpath([root, p]) != root or not os.path.isfile(p) or os.path.getsize(p) > MAX_FILE:
        return None
    with open(p, 'rb') as fh:
        return fh.read()


def register(api):
    global _api
    _api = api

    def widget():
        n = max(5, int(api.get('anzahl') or 25))
        pool = ['/api/x/%s/bild?f=%s' % (EXT_ID, __import__('urllib.parse').parse.quote(f)) for f in dateien()] + adressen()
        if not pool:
            return None
        random.shuffle(pool)
        return {'bilder': pool[:n]}

    def bild(req):
        data = lesen(req.query.get('f', ''))
        if data is None:
            return ({'error': 'Bild nicht gefunden'}, 404)
        return data

    def seite(req):
        from urllib.parse import quote
        fs = dateien()
        imgs = ['/api/x/%s/bild?f=%s' % (EXT_ID, quote(f)) for f in fs[:300]] + adressen()
        tok = req.query.get('token', '')
        suffix = ('&token=' + quote(tok)) if tok else ''
        cells = ''.join('<img loading="lazy" src="%s%s">' % (html.escape(u, quote=True), suffix if u.startswith('/api/') else '') for u in imgs)
        return ('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                '<title>Bilder</title><style>body{background:#10131a;color:#eee;font:18px system-ui;margin:0;padding:12px}'
                'div{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:8px}img{width:100%%;height:140px;object-fit:cover;border-radius:6px}</style>'
                '<h1>🖼️ Bilderrahmen</h1><p>%d Bilder</p><div>%s</div>' % (len(imgs), cells))

    api.widget('Bilder', widget, ttl=600, id='bilder', icon='🖼️')
    api.route('bild', bild)
    api.route('index', seite)
    api.route('probe', lambda req: {'n': len(dateien()) + len(adressen())})
