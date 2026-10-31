# -*- coding: utf-8 -*-
"""Später ansehen – gemeinsame Merkliste für MovieScout.

Filme und Serien über die Titel-Info vormerken. Die Liste wird in der Engine
gespeichert und ist damit auf allen verbundenen Geräten derselben Engine verfügbar.
Einträge können entfernt oder mit ihrem Original-Eintrag in den Familienchat
geschickt werden.
"""
import html
import threading
import time
import uuid

EXT_ID = 'spaeter_ansehen'
EXT_NAME = 'Später ansehen'
EXT_DESCRIPTION = 'Gemeinsame Merkliste: Titel vormerken, verwalten und mit abspielbarem Eintrag in den Familienchat schicken.'
EXT_LINKS = [('Merkliste öffnen', 'index')]
EXT_SETTINGS = [
    {'key': 'max_eintraege', 'label': 'Maximale Anzahl Einträge', 'type': 'number',
     'default': 300, 'min': 20, 'max': 2000},
    {'key': 'kachel_zeilen', 'label': 'Zusätzliche Titel in der Kachel', 'type': 'number',
     'default': 2, 'min': 0, 'max': 5},
    {'key': 'chat_absender', 'label': 'Absender im Familienchat', 'type': 'text',
     'default': '🎬 Später ansehen'},
]

_api = None
_lock = threading.RLock()
_STORE_KEY = 'merkliste'


def _rows():
    data = _api.get(_STORE_KEY, [])
    if not isinstance(data, list):
        return []
    # Alte oder beschädigte Datensätze nicht in die Oberfläche übernehmen.
    return [r for r in data if isinstance(r, dict) and r.get('id') and r.get('title')]


def _save(rows):
    limit = max(20, min(2000, int(_api.get('max_eintraege') or 300)))
    _api.set(_STORE_KEY, rows[-limit:])


def _title(item):
    title = str(item.get('title') or item.get('name') or 'Unbenannter Titel').strip()
    parent = str(item.get('parent_title') or '').strip()
    if parent and parent.lower() not in title.lower():
        title = parent + ' – ' + title
    return title[:240]


def _add(item):
    if not isinstance(item, dict):
        _api.fail('Der Titel konnte nicht übernommen werden.')
    item = dict(item)
    title = _title(item)
    url = str(item.get('url') or '')
    provider_id = str(item.get('provider_id') or item.get('provider') or '')
    key = provider_id + '|' + (url or title).lower()

    with _lock:
        rows = _rows()
        for row in rows:
            old = row.get('item') if isinstance(row.get('item'), dict) else {}
            old_key = str(old.get('provider_id') or old.get('provider') or '') + '|' + (
                str(old.get('url') or row.get('title') or '').lower())
            if old_key == key:
                return False, row
        row = {
            'id': uuid.uuid4().hex[:12],
            'title': title,
            'provider': str(item.get('provider_name') or item.get('provider') or provider_id)[:100],
            'year': str(item.get('year') or '')[:8],
            'added': int(time.time()),
            'item': item,
        }
        rows.append(row)
        _save(rows)
    return True, row


def _page(req):
    return r"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark light">
<title>Später ansehen – MovieScout</title>
<style>
:root{color-scheme:dark;--bg:#0b0f17;--fg:#e8edf5;--mut:#91a0b4;--card:#151e2b;--line:#29384b;--acc:#398ee8;--bad:#d65b65}
@media(prefers-color-scheme:light){:root{color-scheme:light;--bg:#f2f5f9;--fg:#172333;--mut:#617084;--card:#fff;--line:#dce3ec;--acc:#176bc2;--bad:#bd3544}}
*{box-sizing:border-box}body{margin:0;padding:20px 16px 60px;background:var(--bg);color:var(--fg);font:16px/1.45 system-ui,sans-serif;max-width:850px;margin-inline:auto}
header{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
h1{font-size:1.45rem;margin:4px 0}.muted{color:var(--mut)}#count{font-size:.9rem;color:var(--mut)}
.card{display:flex;align-items:center;gap:12px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:13px;margin:10px 0}
.info{min-width:0;flex:1}.name{font-weight:650;overflow-wrap:anywhere}.meta{font-size:.85rem;color:var(--mut);margin-top:3px}
.actions{display:flex;gap:7px;flex-wrap:wrap}
button{font:inherit;border:0;border-radius:10px;padding:9px 12px;background:var(--acc);color:white;cursor:pointer}
button.secondary{background:transparent;color:var(--fg);border:1px solid var(--line)}
button.danger{background:transparent;color:var(--bad);border:1px solid var(--line)}
#empty{padding:30px 16px;text-align:center;border:1px dashed var(--line);border-radius:14px;color:var(--mut);margin-top:16px}
#status{min-height:1.5em;color:var(--mut);font-size:.9rem;margin:12px 2px}
@media(max-width:520px){.card{align-items:flex-start;flex-wrap:wrap}.info{flex-basis:100%}.actions{width:100%}.actions button{flex:1}}
</style></head><body>
<header><div><h1>🎬 Später ansehen</h1><div class="muted">Deine gemeinsame MovieScout-Merkliste</div></div><div id="count">Lade …</div></header>
<div id="list"></div><div id="empty" hidden>Noch keine Titel vorgemerkt.<br>Öffne die Info eines Films oder einer Folge und tippe auf „＋ Später ansehen“.</div>
<div id="status" role="status"></div>
<script>
const $=id=>document.getElementById(id);
async function call(path,data){
  const opt=data===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)};
  const r=await fetch(path,opt);let d={};try{d=await r.json()}catch(_){}
  if(!r.ok)throw new Error(d.error||'Aktion fehlgeschlagen');return d;
}
function el(tag,cls,text){const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e}
function button(label,cls,fn){const b=el('button',cls,label);b.type='button';b.onclick=fn;return b}
async function draw(){
  try{
    const d=await call('liste');const rows=d.eintraege||[];const root=$('list');root.textContent='';
    $('count').textContent=rows.length+' Titel';
    $('empty').hidden=rows.length!==0;
    rows.forEach(r=>{
      const card=el('article','card');const info=el('div','info');
      info.append(el('div','name',r.title));
      info.append(el('div','meta',[r.year,r.provider,new Date(r.added*1000).toLocaleDateString('de-DE')].filter(Boolean).join(' · ')));
      const actions=el('div','actions');
      actions.append(button('💬 In Chat teilen','secondary',async()=>{
        try{await call('teilen',{id:r.id});$('status').textContent='Titel wurde in den Familienchat geschickt.'}
        catch(e){$('status').textContent=e.message}
      }));
      actions.append(button('✕ Entfernen','danger',async()=>{
        try{await call('entfernen',{id:r.id});$('status').textContent='Titel entfernt.';await draw()}
        catch(e){$('status').textContent=e.message}
      }));
      card.append(info,actions);root.append(card);
    });
  }catch(e){$('status').textContent=e.message}
}
draw();
</script></body></html>"""


def register(api):
    global _api
    _api = api

    def post_only(fn):
        def wrapped(req):
            if req.method != 'POST':
                return ({'error': 'Nur per POST'}, 405)
            data = req.json if isinstance(req.json, dict) else {}
            return fn(data)
        return wrapped

    def add_from_info(item):
        added, row = _add(item)
        if added:
            return 'Für später vorgemerkt: %s' % row['title']
        return 'Bereits vorgemerkt: %s' % row['title']

    def liste(req):
        rows = sorted(_rows(), key=lambda r: -int(r.get('added') or 0))
        return {'eintraege': [
            {'id': r['id'], 'title': r['title'], 'provider': r.get('provider', ''),
             'year': r.get('year', ''), 'added': int(r.get('added') or 0)}
            for r in rows
        ]}

    def entfernen(data):
        rid = str(data.get('id') or '')
        with _lock:
            rows = _rows()
            new = [r for r in rows if r.get('id') != rid]
            if len(new) == len(rows):
                return ({'error': 'Eintrag nicht gefunden.'}, 404)
            _save(new)
        return {'ok': True}

    def teilen(data):
        rid = str(data.get('id') or '')
        row = next((r for r in _rows() if r.get('id') == rid), None)
        if not row:
            return ({'error': 'Eintrag nicht gefunden.'}, 404)
        item = row.get('item')
        if not isinstance(item, dict):
            return ({'error': 'Für diesen Eintrag ist kein abspielbarer Titel gespeichert.'}, 400)
        try:
            api.chat('🎬 Für später vorgemerkt: %s' % row['title'],
                     item=item, author=api.get('chat_absender') or None)
        except Exception as exc:
            api.log('Chat-Weitergabe fehlgeschlagen: %s' % exc, 'warning')
            return ({'error': 'Familienchat ist nicht verfügbar oder die Nachricht konnte nicht gesendet werden.'}, 503)
        return {'ok': True}

    def widget():
        rows = sorted(_rows(), key=lambda r: -int(r.get('added') or 0))
        if not rows:
            return {'icon': '🎬', 'text': 'Merkliste leer', 'sub': 'Titel-Info → ＋ Später ansehen'}
        count = len(rows)
        first = rows[0]
        n = max(0, min(5, int(api.get('kachel_zeilen') or 2)))
        extra = [r['title'] for r in rows[1:1 + n]]
        return {'icon': '🎬', 'text': first['title'][:42],
                'sub': '%d %s vorgemerkt' % (count, 'Titel' if count != 1 else 'Titel'),
                'lines': extra}

    api.route('index', _page)
    api.route('liste', liste)
    api.route('entfernen', post_only(entfernen))
    api.route('teilen', post_only(teilen))
    api.widget('Später ansehen', widget, ttl=20, icon='🎬')
    api.item_action('＋ Später ansehen', add_from_info, needs='url')
