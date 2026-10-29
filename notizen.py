# -*- coding: utf-8 -*-
"""Notizzettel: gemeinsame Notizen und Einkaufsliste für alle Geräte im Haus.

Öffnen: Erweiterungsliste -> Notizen -> „Notizzettel öffnen“ (oder als Lesezeichen am Handy). Dort Notiz eintippen,
abhaken, anheften (📌) oder löschen. Die Kachel „Notizen“ auf der Startseite (und im Bildschirmschoner) zeigt die
angehefteten und offenen Notizen. In der Titel-Info gibt es den Knopf „📝 Auf den Notizzettel“ (z. B. „Film am Samstag“).
Alles liegt in der Engine, nichts geht ins Internet.
"""
import threading
import time
import uuid

EXT_ID = 'notizen'
EXT_NAME = 'Notizzettel'
EXT_DESCRIPTION = 'Gemeinsame Notizen/Einkaufsliste mit Kachel auf der Startseite und Knopf „Auf den Notizzettel“ in der Titel-Info.'
EXT_LINKS = [('Notizzettel öffnen', 'index')]
EXT_SETTINGS = [
    {'key': 'zeilen', 'label': 'Zeilen in der Kachel', 'type': 'number', 'default': 4, 'min': 1, 'max': 8},
]

MAX_NOTES = 300
MAX_LEN = 500
_api = None
_lock = threading.Lock()


def _all():
    d = _api.get('notizen', [])
    return d if isinstance(d, list) else []


def _save(rows):
    _api.set('notizen', rows[-MAX_NOTES:])


def hinzu(text, pinned=False):
    text = str(text or '').strip()[:MAX_LEN]
    if not text:
        _api.fail('Die Notiz ist leer.')
    with _lock:
        rows = _all()
        n = {'id': uuid.uuid4().hex[:8], 'text': text, 'done': False, 'pinned': bool(pinned), 't': int(time.time())}
        rows.append(n)
        _save(rows)
    return n


def _find(rows, nid):
    return next((r for r in rows if r.get('id') == nid), None)


def _sorted(rows):
    return sorted(rows, key=lambda r: (r.get('done', False), not r.get('pinned', False), -r.get('t', 0)))


def _page(req):
    return """<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Notizzettel</title><style>
:root{--bg:#0f141b;--fg:#e8edf3;--mut:#93a1b3;--card:#18202b;--acc:#4da3ff}
@media(prefers-color-scheme:light){:root{--bg:#f4f6f9;--fg:#18202b;--mut:#5d6b7c;--card:#fff;--acc:#1b6fd1}}
body{margin:0;padding:18px 16px 60px;background:var(--bg);color:var(--fg);font:17px/1.45 system-ui,sans-serif;max-width:640px;margin-inline:auto}
h1{font-size:1.4rem;margin:.2em 0 .6em}form{display:flex;gap:8px}input[type=text]{flex:1;font:inherit;padding:10px 12px;border-radius:10px;border:1px solid var(--mut);background:var(--card);color:var(--fg)}
button{font:inherit;padding:8px 14px;border-radius:10px;border:0;background:var(--acc);color:#fff;cursor:pointer}
button.l{background:transparent;color:var(--mut);padding:6px 8px}ul{list-style:none;padding:0;margin:14px 0}
li{display:flex;align-items:center;gap:8px;background:var(--card);border-radius:12px;padding:8px 10px;margin:6px 0}
li span{flex:1;word-break:break-word}li.d span{text-decoration:line-through;color:var(--mut)}li.p{outline:2px solid var(--acc)}
input[type=checkbox]{width:22px;height:22px}.m{color:var(--mut);font-size:.9rem}
</style><h1>📝 Notizzettel</h1>
<form id="f"><input type="text" id="t" maxlength="500" placeholder="Neue Notiz …" autocomplete="off"><button>Hinzufügen</button></form>
<ul id="l"></ul><p class="m" id="m"></p><button class="l" id="c">Erledigte entfernen</button>
<script>
const $=(i)=>document.getElementById(i);
async function call(p,b){const r=await fetch(p,{method:b?'POST':'GET',headers:{'Content-Type':'application/json'},body:b?JSON.stringify(b):undefined});if(!r.ok){let e='Fehler';try{e=(await r.json()).error||e}catch(_){}alert(e);throw new Error(e)}return r.json()}
function el(tag,cls,txt){const e=document.createElement(tag);if(cls)e.className=cls;if(txt!=null)e.textContent=txt;return e}
async function draw(){
  const d=await call('liste');const ul=$('l');ul.textContent='';
  d.notizen.forEach(n=>{
    const li=el('li',(n.done?'d ':'')+(n.pinned?'p':''));
    const cb=el('input');cb.type='checkbox';cb.checked=n.done;cb.onchange=async()=>{await call('aendern',{id:n.id,done:cb.checked});draw()};
    const sp=el('span','',n.text);
    const pin=el('button','l',n.pinned?'📌':'📍');pin.title='Anheften';pin.onclick=async()=>{await call('aendern',{id:n.id,pinned:!n.pinned});draw()};
    const del=el('button','l','✕');del.title='Löschen';del.onclick=async()=>{await call('loeschen',{id:n.id});draw()};
    li.append(cb,sp,pin,del);ul.append(li)});
  $('m').textContent=d.notizen.length?d.offen+' offen von '+d.notizen.length:'Noch keine Notizen.';
}
$('f').onsubmit=async(e)=>{e.preventDefault();const v=$('t').value.trim();if(!v)return;await call('neu',{text:v});$('t').value='';draw()};
$('c').onclick=async()=>{await call('aufraeumen',{});draw()};
draw();setInterval(draw,15000);
</script></html>"""


def register(api):
    global _api
    _api = api

    def post_only(fn):
        def wrap(req):
            if req.method != 'POST':
                return ({'error': 'Nur per POST'}, 405)
            return fn(req.json if isinstance(req.json, dict) else {})
        return wrap

    def liste(req):
        rows = _sorted(_all())
        return {'notizen': rows, 'offen': sum(1 for r in rows if not r.get('done'))}

    def neu(d):
        if not str(d.get('text') or '').strip():
            return ({'error': 'Die Notiz ist leer.'}, 400)
        return {'ok': True, 'notiz': hinzu(d.get('text'), d.get('pinned'))}

    def aendern(d):
        with _lock:
            rows = _all()
            r = _find(rows, d.get('id'))
            if r is None:
                return ({'error': 'Notiz nicht gefunden'}, 404)
            if 'done' in d:
                r['done'] = bool(d['done'])
            if 'pinned' in d:
                r['pinned'] = bool(d['pinned'])
            if 'text' in d and str(d['text']).strip():
                r['text'] = str(d['text']).strip()[:MAX_LEN]
            _save(rows)
        return {'ok': True}

    def loeschen(d):
        with _lock:
            rows = [r for r in _all() if r.get('id') != d.get('id')]
            _save(rows)
        return {'ok': True}

    def aufraeumen(d):
        with _lock:
            rows = [r for r in _all() if not r.get('done')]
            n = len(_all()) - len(rows)
            _save(rows)
        return {'ok': True, 'entfernt': n}

    def widget():
        rows = [r for r in _sorted(_all()) if not r.get('done')]
        if not rows:
            return {'icon': '📝', 'text': 'Notizzettel leer', 'sub': 'Erweiterungsliste -> Notizen -> Notizzettel öffnen'}
        n = max(1, int(api.get('zeilen') or 4))
        top = rows[0]
        return {'icon': '📌' if top.get('pinned') else '📝', 'text': top['text'][:40], 'sub': ('%d offen' % len(rows)),
                'lines': [r['text'] for r in rows[1:n]]}

    def knopf(item):
        t = str(item.get('title') or '').strip()
        if item.get('parent_title'):
            t = '%s - %s' % (item['parent_title'], t)
        src = item.get('provider') or ''
        hinzu('🎬 %s%s' % (t, ' (%s)' % src if src else ''))
        return 'Auf den Notizzettel gesetzt: %s' % t

    api.route('index', _page)
    api.route('liste', liste)
    api.route('neu', post_only(neu))
    api.route('aendern', post_only(aendern))
    api.route('loeschen', post_only(loeschen))
    api.route('aufraeumen', post_only(aufraeumen))
    api.widget('Notizen', widget, ttl=30, icon='📝')
    api.item_action('📝 Auf den Notizzettel', knopf, needs='title')
