# -*- coding: utf-8 -*-
# TV-Programm
# IT('s) Possible 
# 2026.11.08
"""TV-Programm: der volle Programmplan pro Sender (nicht nur „Jetzt“ und „Danach“).

So geht es: In den Einstellungen von MovieScout unter „Quellen & Listen“ die EPG-Adresse (XMLTV) eintragen - dieselbe, die
für M3U und Stalker-Portale genutzt wird. Erweiterungsliste -> TV-Programm -> „Programm öffnen“. Links stehen alle Sender mit
„Jetzt“ und „Danach“, ein Tipp (oder OK) auf einen Sender zeigt dessen Plan für die nächsten Stunden. Oben suchen, Lieblingssender
(Einstellung) stehen vorn. Hoch/Runter wählt, OK öffnet, Zurück/Esc geht zurück.
Der Guide enthält nur die Zeit von einer Stunde zurück bis etwa 36 Stunden voraus - mehr gibt es nicht anzuzeigen.
Die Sendernamen kommen aus dem Guide (ID, z. B. „ZDF.de“ wird zu „ZDF“).
"""
import re
import threading
import time
from datetime import datetime, timezone

EXT_ID = 'tvprogramm'
EXT_NAME = 'TV-Programm'
EXT_DESCRIPTION = 'Voller Programmplan pro Sender aus der EPG-Adresse (Jetzt, Danach und die nächsten Stunden).'
EXT_LINKS = [('TV-Programm', 'index')]
EXT_SETTINGS = [
    {'key': 'favoriten', 'label': 'Lieblingssender (Komma-getrennt)', 'type': 'text', 'default': 'Das Erste, ZDF, RTL, SAT.1, ProSieben',
     'hint': 'Ein Teil des Namens genügt. Diese Sender stehen in der Liste ganz oben.'},
]

_api = None
_NAMEN = {'url': '', 't': 0.0, 'map': {}, 'busy': False, 'fehler': ''}     # Kennung -> Anzeigename aus dem Guide
_NAMEN_TTL = 6 * 3600
_NLOCK = threading.Lock()


def _epg():
    from engine import epg as E
    return E


def _namen_holen(url):
    """Liest nur die <channel>-Einträge (Anzeigenamen) des Guides; Sendungen werden übersprungen."""
    import gzip
    import io
    import xml.etree.ElementTree as ET
    from resources.lib import multiquest
    r = multiquest.get(url, headers={'User-Agent': 'MovieScout'}, timeout=90)
    if r.status_code != 200:
        raise RuntimeError('HTTP %s' % r.status_code)
    data = r.content
    if url.lower().split('?')[0].endswith('.gz') or data[:2] == b'\x1f\x8b':
        try:
            data = gzip.decompress(data)
        except Exception:                                    # noqa: BLE001 - abgeschnitten: Lesbares behalten
            import zlib
            data = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(data)
    out = {}
    try:
        for _, el in ET.iterparse(io.BytesIO(data), events=('end',)):
            if el.tag == 'channel':
                cid = el.get('id') or ''
                names = [(d.text or '').strip() for d in el.findall('display-name') if (d.text or '').strip()]
                pick = next((n for n in names if not n.isdigit() and n != cid), '')
                if cid and pick:
                    out[cid] = pick
                el.clear()
            elif el.tag == 'programme':
                el.clear()
    except ET.ParseError:
        pass                                                 # abgeschnittene Datei: bis hierhin Gelesenes behalten
    return out


def _namen():
    """Anzeigenamen (zwischengespeichert, im Hintergrund geholt). Gibt (Zuordnung, lädt noch) zurück."""
    url = _epg().epg_url()
    with _NLOCK:
        stale = _NAMEN['url'] != url or time.time() - _NAMEN['t'] > _NAMEN_TTL
        if stale and not _NAMEN['busy']:
            _NAMEN['busy'] = True

            def work():
                try:
                    m, err = _namen_holen(url), ''
                except Exception as e:                       # noqa: BLE001 - ohne Namen zeigt die Liste die Kennungen
                    m, err = {}, str(e) or type(e).__name__
                with _NLOCK:
                    _NAMEN.update(url=url, t=time.time() if not err else time.time() - _NAMEN_TTL + 600, map=m, busy=False, fehler=err)
            threading.Thread(target=work, daemon=True).start()
        return _NAMEN['map'] if _NAMEN['url'] == url else {}, _NAMEN['busy']


def _label(cid, namen=None):
    if namen and namen.get(cid):
        return namen[cid]
    s = re.sub(r'\.[a-z]{2,3}$', '', str(cid), flags=re.I)
    s = re.sub(r'[._]+', ' ', s).strip()
    return s or str(cid)


def _hm(dt):
    return _epg()._local(dt).strftime('%H:%M')


def _day(dt):
    d = _epg()._local(dt).date()
    t = _epg()._local(datetime.now(timezone.utc)).date()
    delta = (d - t).days
    return 'Heute' if delta == 0 else 'Morgen' if delta == 1 else 'Gestern' if delta == -1 else d.strftime('%d.%m.')


def _favs():
    return [w.strip().lower() for w in str(_api.get('favoriten') or '').split(',') if w.strip()]


def senderliste():
    E = _epg()
    if not E.epg_url():
        return {'fehler': 'Keine EPG-Adresse eingetragen. Einstellungen, „Quellen & Listen“, EPG (XMLTV).'}
    epg = E.get(wait=False)
    if not epg:
        with E._LOCK:
            st = dict(E._EPG_STATE)
        if st.get('loading') or not st.get('error'):
            return {'laedt': True}
        return {'fehler': 'EPG konnte nicht geladen werden: %s' % st['error']}
    now = datetime.now(timezone.utc)
    favs = _favs()
    namen, laedt = _namen()
    out = []
    for cid, rows in epg['progs'].items():
        cur = nxt = None
        for i, (start, stop, title) in enumerate(rows):
            if start <= now < stop:
                cur = (title, stop, start)
                nxt = rows[i + 1][2] if i + 1 < len(rows) else ''
                break
            if start > now:
                nxt = title
                break
        name = _label(cid, namen)
        out.append({'id': cid, 'name': name, 'jetzt': cur[0] if cur else '', 'bis': _hm(cur[1]) if cur else '', 'danach': nxt or '',
                    'prozent': int(100 * (now - cur[2]).total_seconds() / max(1, (cur[1] - cur[2]).total_seconds())) if cur else 0,
                    'fav': any(f in name.lower() for f in favs)})
    out.sort(key=lambda r: (not r['fav'], (0, int(r['name'])) if r['name'].isdigit() else (1, r['name'].lower())))
    return {'sender': out, 'stand': int(time.time()), 'namen_laden': bool(laedt and not namen)}


def plan(cid):
    epg = _epg().get(wait=False)
    rows = (epg or {}).get('progs', {}).get(cid)
    if not rows:
        return {'fehler': 'Kein Plan für diesen Sender.'}
    now = datetime.now(timezone.utc)
    eintraege, last_day = [], ''
    for start, stop, title in rows:
        if stop <= now:
            continue
        day = _day(start)
        eintraege.append({'tag': day if day != last_day else '', 'von': _hm(start), 'bis': _hm(stop), 'titel': title or '(ohne Titel)',
                          'jetzt': start <= now < stop})
        last_day = day
    return {'name': _label(cid, _namen()[0]), 'plan': eintraege}


_PAGE = """<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TV-Programm</title>
<style>
:root{--bg:#0f141b;--card:#18202b;--line:#2a3442;--txt:#e8edf3;--mut:#93a1b3;--acc:#8ab4ff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:clamp(16px,2.4vmin,24px)/1.35 system-ui,sans-serif}
header{position:sticky;top:0;background:var(--bg);padding:12px 14px;border-bottom:1px solid var(--line);display:flex;gap:10px;align-items:center;z-index:2}
h1{margin:0;font-size:1.15em;flex:none}input{flex:1;min-width:0;font:inherit;padding:.45em .7em;border-radius:10px;border:1px solid var(--line);background:var(--card);color:inherit}
button,.row{font:inherit;color:inherit}main{padding:10px 14px 40px;max-width:900px;margin:auto}
.row{display:block;width:100%;text-align:left;background:var(--card);border:2px solid transparent;border-radius:12px;padding:.55em .8em;margin:6px 0;cursor:pointer}
.row:focus,.row:hover{outline:none;border-color:var(--acc)}.row.f b::before{content:"★ ";color:#f5c542}
.row b{display:block}.row span{color:var(--mut);display:block;font-size:.88em}.bar{height:4px;background:var(--line);border-radius:3px;margin-top:5px;overflow:hidden}.bar i{display:block;height:100%;background:var(--acc)}
.back{font:inherit;border:1px solid var(--line);background:var(--card);border-radius:10px;padding:.45em .9em;cursor:pointer}.back:focus{outline:none;border-color:var(--acc)}
.tag{margin:14px 0 4px;color:var(--acc);font-weight:700}.p{display:flex;gap:12px;padding:.45em .6em;border-bottom:1px solid var(--line)}.p time{flex:none;width:8.6em;white-space:nowrap;color:var(--mut)}
.p.j{background:#1f2c44;border-radius:8px;border:0}.p.j time{color:var(--acc);font-weight:700}.msg{padding:30px 10px;text-align:center;color:var(--mut)}
</style>
<header><button class="back" id="zur" style="display:none">◄ Zurück</button><h1 id="t">📺 TV-Programm</h1><input id="q" placeholder="Sender suchen" autocomplete="off"></header>
<main id="m"><div class="msg">Lädt …</div></main>
<script>
const M=document.getElementById('m'),Q=document.getElementById('q'),Z=document.getElementById('zur'),T=document.getElementById('t');
const B=location.pathname.replace(/index$/,'');const S=location.search;let L=[],view='liste',poll=0;
const u=p=>B+p+S+(S?'&':'?')+'_=1';
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
async function laden(){clearTimeout(poll);let d;try{d=await (await fetch(u('sender'))).json()}catch(e){M.innerHTML='<div class="msg">Keine Verbindung zur Engine.</div>';return}
  if(d.laedt){M.innerHTML='<div class="msg">Der Programmführer wird geladen … einen Moment.</div>';poll=setTimeout(laden,3000);return}
  if(d.fehler){M.innerHTML='<div class="msg">'+esc(d.fehler)+'</div>';return}
  L=d.sender;if(view==='liste')zeigeListe();poll=setTimeout(()=>{if(view==='liste'||d.namen_laden)laden()},d.namen_laden?4000:60000)}
function zeigeListe(keep){view='liste';Z.style.display='none';T.textContent='📺 TV-Programm';Q.style.display='';const f=Q.value.trim().toLowerCase();
  const rows=L.filter(r=>!f||r.name.toLowerCase().includes(f)).slice(0,300);
  M.innerHTML=rows.length?rows.map(r=>'<button class="row'+(r.fav?' f':'')+'" data-id="'+esc(r.id)+'"><b>'+esc(r.name)+'</b><span>'+(r.jetzt?'Jetzt: '+esc(r.jetzt)+' (bis '+esc(r.bis)+')':'Jetzt: –')+'</span>'+(r.danach?'<span>Danach: '+esc(r.danach)+'</span>':'')+(r.jetzt?'<div class="bar"><i style="width:'+r.prozent+'%"></i></div>':'')+'</button>').join(''):'<div class="msg">Kein Sender gefunden.</div>';
  M.querySelectorAll('.row').forEach(b=>b.onclick=()=>zeigePlan(b.dataset.id));
  if(keep){const k=[...M.querySelectorAll('.row')].find(b=>b.dataset.id===keep);if(k){k.focus();k.scrollIntoView({block:'center'})}}}
async function zeigePlan(id){let d;try{d=await (await fetch(u('plan')+'&id='+encodeURIComponent(id))).json()}catch(e){return}
  view='plan';window._last=id;Z.style.display='';Q.style.display='none';T.textContent=d.name||'Plan';
  if(d.fehler){M.innerHTML='<div class="msg">'+esc(d.fehler)+'</div>';return}
  M.innerHTML=d.plan.map(e=>(e.tag?'<div class="tag">'+esc(e.tag)+'</div>':'')+'<div class="p'+(e.jetzt?' j':'')+'"><time>'+esc(e.von)+'–'+esc(e.bis)+'</time><span>'+esc(e.titel)+'</span></div>').join('');
  const j=M.querySelector('.j');if(j)j.scrollIntoView({block:'center'});Z.focus()}
function zurueck(){if(view==='plan')zeigeListe(window._last)}
Z.onclick=zurueck;Q.oninput=()=>zeigeListe();
document.addEventListener('keydown',e=>{const k=e.key;
  if(k==='Escape'||k==='Backspace'&&document.activeElement!==Q||k==='GoBack'||k==='BrowserBack'){if(view==='plan'){e.preventDefault();zurueck()}return}
  if(document.activeElement===Q){if(k==='ArrowDown'){e.preventDefault();const f=M.querySelector('.row');if(f)f.focus()}return}
  if(k==='ArrowDown'||k==='ArrowUp'){const r=view==='liste'?[...M.querySelectorAll('.row')]:[];if(!r.length)return;e.preventDefault();
    const i=r.indexOf(document.activeElement);if(k==='ArrowUp'&&i<=0){Q.focus();return}r[Math.max(0,Math.min(r.length-1,i+(k==='ArrowDown'?1:-1)))].focus()}});
laden();
</script></html>"""


def register(api):
    global _api
    _api = api

    def seite(req):
        return _PAGE

    def sender(req):
        return senderliste()

    def plan_route(req):
        cid = str(req.query.get('id', ''))
        return plan(cid)

    def widget():
        try:
            n = int(_epg().get(wait=False).get('epg_channels', 0)) if _epg().epg_url() else 0
        except Exception:                                  # noqa: BLE001 - Kachel darf nie stören
            n = 0
        return {'icon': '📰', 'text': 'TV-Programm',
                'sub': ('%d Sender im Guide' % n) if n else ('Guide wird geladen …' if _epg().epg_url() else 'EPG-Adresse eintragen')}

    api.route('index', seite)
    api.route('sender', sender)
    api.route('plan', plan_route)
    api.widget('TV-Programm', widget, ttl=120, id='tvprogramm', icon='📰')
