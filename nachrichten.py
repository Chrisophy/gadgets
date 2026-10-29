# -*- coding: utf-8 -*-
"""Nachrichten & Podcasts: liest RSS-/Atom-Feeds (Nachrichten, Blogs, Podcasts, Video-Podcasts).

So geht es: In den Einstellungen unter „Feeds“ pro Zeile  Name; Adresse  eintragen. Beispiel:
    Tagesschau; https://www.tagesschau.de/index~rss2.xml
Dann gibt es
  - eine Kachel „Schlagzeile“ auf der Startseite (und im Bildschirmschoner) mit den neuesten Meldungen,
  - die Seite „Nachrichten lesen“ (Erweiterungsliste -> Nachrichten) mit allen Meldungen zum Lesen,
  - den Menüpunkt „📰 Nachrichten“: Feeds mit Audio/Video (Podcasts, Videos der Tagesschau …) lassen sich direkt abspielen.
Es werden nur Adressen mit http:// oder https:// gelesen; pro Feed höchstens 2 MB.
"""
import html
import re
import time
import urllib.request
import xml.etree.ElementTree as ET

EXT_ID = 'nachrichten'
EXT_NAME = 'Nachrichten & Podcasts'
EXT_DESCRIPTION = 'RSS-Reader: Kachel mit Schlagzeilen, Leseseite und abspielbare Podcasts/Videos aus beliebigen Feeds.'
EXT_LINKS = [('Nachrichten lesen', 'index')]
EXT_SETTINGS = [
    {'key': 'feeds', 'label': 'Feeds (einer pro Zeile)', 'type': 'textarea',
     'default': 'Tagesschau; https://www.tagesschau.de/index~rss2.xml',
     'hint': 'Name; Adresse   - Nachrichten, Blogs oder Podcasts. Podcasts mit Audio/Video sind direkt abspielbar.'},
    {'key': 'anzahl', 'label': 'Meldungen pro Feed', 'type': 'number', 'default': 15, 'min': 3, 'max': 50},
    {'key': 'zeilen', 'label': 'Zeilen in der Kachel', 'type': 'number', 'default': 4, 'min': 1, 'max': 8},
]

MAX_BYTES = 2 * 1024 * 1024
_api = None
_cache = {}                       # url -> (zeit, [eintraege])
_TTL = 600
_TAG = re.compile(r'<[^>]+>')


def feeds(text):
    """'Name; URL' je Zeile -> [(name, url)]; Zeilen ohne http(s)-Adresse werden ignoriert."""
    out = []
    for line in str(text or '').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        name, _, url = line.rpartition(';')
        url = url.strip()
        if not re.match(r'https?://', url, re.I):
            continue
        out.append((name.strip() or re.sub(r'^https?://(www\.)?', '', url).split('/')[0], url))
    return out


def _clean(t, n=400):
    t = html.unescape(_TAG.sub(' ', str(t or '')))
    return re.sub(r'\s+', ' ', t).strip()[:n]


def _local(tag):
    return tag.rsplit('}', 1)[-1].lower()


def parse(data):
    """RSS 2.0 / Atom -> Liste von {title, link, desc, date, media, mtype, image}."""
    root = ET.fromstring(data)
    out = []
    for el in root.iter():
        if _local(el.tag) not in ('item', 'entry'):
            continue
        e = {'title': '', 'link': '', 'desc': '', 'date': '', 'media': '', 'mtype': '', 'image': ''}
        for c in el:
            t = _local(c.tag)
            txt = (c.text or '').strip()
            if t == 'title':
                e['title'] = _clean(txt, 200)
            elif t == 'link':
                e['link'] = c.get('href') or txt if not e['link'] else e['link']
                if c.get('rel') == 'enclosure' and c.get('href') and not e['media']:
                    e['media'], e['mtype'] = c.get('href'), (c.get('type') or '')
            elif t in ('description', 'summary', 'encoded') and (not e['desc'] or t == 'summary'):
                e['desc'] = _clean(txt)
            elif t in ('pubdate', 'updated', 'published', 'date'):
                e['date'] = e['date'] or txt
            elif t in ('enclosure', 'content') and c.get('url') and not e['media']:
                ty = c.get('type') or ''
                if t == 'enclosure' or ty.startswith(('audio', 'video')) or c.get('medium') in ('audio', 'video'):
                    e['media'], e['mtype'] = c.get('url'), ty
                elif ty.startswith('image') and not e['image']:
                    e['image'] = c.get('url')
            elif t == 'thumbnail' and c.get('url') and not e['image']:
                e['image'] = c.get('url')
        if e['media'] and not e['mtype'].startswith(('audio', 'video')):
            if not re.search(r'\.(mp3|m4a|aac|ogg|opus|mp4|m4v|webm|mov)(\?|$)', e['media'], re.I):
                if e['mtype'].startswith('image') and not e['image']:
                    e['image'] = e['media']
                e['media'], e['mtype'] = '', ''
        if e['title']:
            out.append(e)
    return out


def _fetch(url):
    c = _cache.get(url)
    if c and time.time() - c[0] < _TTL:
        return c[1]
    req = urllib.request.Request(url, headers={'User-Agent': 'MovieScout/1.0 (RSS)', 'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*'})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('Feed zu groß')
    items = parse(data)
    _cache[url] = (time.time(), items)
    return items


def alle():
    """[(feedname, eintrag)] - neueste Feeds zuerst in Reihenfolge der Einstellung; Fehler pro Feed als eintrag mit 'fehler'."""
    n = max(1, int(_api.get('anzahl') or 15))
    res, errs = [], []
    for name, url in feeds(_api.get('feeds')):
        try:
            res.extend((name, e) for e in _fetch(url)[:n])
        except Exception as ex:                       # noqa: BLE001 - ein toter Feed darf die anderen nicht stoppen
            errs.append('%s: %s' % (name, str(ex)[:80]))
    return res, errs


def playable(name, e):
    return {'title': e['title'], 'provider_id': 'm3u_iptv', 'url': e['media'], 'next_func': 'get_hosters', 'is_playable': True,
            'kind': 'play', 'plot': (e['desc'] + '\n' if e['desc'] else '') + name, 'poster': e['image'], 'parent_title': name}


def register(api):
    global _api
    _api = api

    def menu():
        res, errs = alle()
        items = [playable(n, e) for n, e in res if e['media']]
        if not items:
            api.fail('Keine abspielbaren Beiträge. ' + ('; '.join(errs) if errs else
                     'Trage in den Einstellungen Podcast- oder Video-Feeds ein (Seite „Nachrichten lesen“ zeigt Textmeldungen).'))
        return items

    def widget():
        res, errs = alle()
        if not res:
            return {'icon': '📰', 'text': '', 'sub': errs[0] if errs else 'Keine Feeds eingetragen'} if (errs or not feeds(api.get('feeds'))) else None
        n = max(1, int(api.get('zeilen') or 4))
        return {'icon': '📰', 'text': res[0][1]['title'][:40], 'sub': res[0][0], 'lines': [e['title'] for _, e in res[1:n]]}

    def seite(req):
        res, errs = alle()
        rows = ''.join('<li><small>%s%s</small><br>%s%s</li>' % (
            html.escape(n), ' · ' + html.escape(e['date'][:25]) if e['date'] else '',
            ('<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>' % (html.escape(e['link'], quote=True), html.escape(e['title']))
             if re.match(r'https?://', e['link'] or '') else html.escape(e['title'])),
            ('<p>%s</p>' % html.escape(e['desc'])) if e['desc'] else '') for n, e in res)
        er = ''.join('<p class="e">⚠ %s</p>' % html.escape(x) for x in errs)
        return ('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                '<title>Nachrichten</title><style>body{font:18px system-ui;background:#10131a;color:#eee;max-width:760px;margin:auto;padding:16px}'
                'a{color:#8ab4ff}li{margin:0 0 18px;list-style:none}small{color:#9aa}p{margin:4px 0;color:#bbb}.e{color:#f99}ul{padding:0}</style>'
                '<h1>📰 Nachrichten</h1>%s<ul>%s</ul>%s' % (er, rows, '' if res else '<p>Keine Meldungen. Feeds in den Einstellungen eintragen.</p>'))

    api.menu('📰 Nachrichten', menu, ttl=300)
    api.widget('Schlagzeile', widget, ttl=900, id='schlagzeile', icon='📰')
    api.route('index', seite)
    api.route('probe', lambda req: {'n': len(alle()[0])})
