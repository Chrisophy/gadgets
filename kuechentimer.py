# -*- coding: utf-8 -*-
"""Küchen-Timer: mehrere Timer für alle Geräte im Haus, mit Alarm im Familienchat.

So geht es: Erweiterungsliste -> Küchen-Timer -> „Timer öffnen“. Dort ein Preset antippen (Ei, Nudeln, Tee …) oder eigene Minuten
eintippen. Laufende Timer erscheinen als Kachel auf der Startseite (und im Bildschirmschoner). Ist ein Timer abgelaufen,
schreibt MovieScout eine Nachricht in den Familienchat und die geöffnete Seite piept. Timer überleben einen Neustart.
"""
import html
import threading
import time
import uuid

EXT_ID = 'kuechentimer'
EXT_NAME = 'Küchen-Timer'
EXT_DESCRIPTION = 'Mehrere Timer mit Kachel und Alarm im Familienchat - von jedem Gerät bedienbar.'
EXT_LINKS = [('Timer öffnen', 'index')]
EXT_SETTINGS = [
    {'key': 'chat', 'label': 'Alarm in den Familienchat schreiben', 'type': 'bool', 'default': True},
    {'key': 'presets', 'label': 'Presets (Name; Minuten, eine pro Zeile)', 'type': 'textarea',
     'default': 'Ei weich; 5\nEi hart; 9\nNudeln; 10\nTee; 4\nPizza; 12'},
]

MAX_MIN = 24 * 60
_api = None
_lock = threading.Lock()
_timers = {}                      # id -> threading.Timer


def presets(text):
    out = []
    for line in str(text or '').splitlines():
        name, _, m = line.rpartition(';')
        try:
            m = float(m.strip().replace(',', '.'))
        except ValueError:
            continue
        if 0 < m <= MAX_MIN:
            out.append((name.strip() or '%g min' % m, m))
    return out


def liste():
    rows = _api.get('timer', [])
    return rows if isinstance(rows, list) else []


def _speichern(rows):
    _api.set('timer', rows)


def _fertig(tid):
    with _lock:
        rows = liste()
        hit = next((r for r in rows if r['id'] == tid and not r.get('fertig')), None)
        if not hit:
            return
        hit['fertig'] = True
        _speichern(rows)
        _timers.pop(tid, None)
    if _api.get('chat') is not False:
        try:
            _api.chat('⏰ %s ist fertig!' % hit['name'])
        except Exception:                             # noqa: BLE001 - Chat darf den Timer nicht kaputtmachen
            pass


def _plane(r):
    rest = r['ende'] - time.time()
    t = threading.Timer(max(0, rest), _fertig, args=(r['id'],))
    t.daemon = True
    _timers[r['id']] = t
    t.start()


def starten(name, minuten):
    try:
        m = float(str(minuten).replace(',', '.'))
    except ValueError:
        return None
    if not 0 < m <= MAX_MIN:
        return None
    r = {'id': uuid.uuid4().hex[:8], 'name': str(name or '').strip()[:40] or '%g min' % m, 'ende': time.time() + m * 60, 'fertig': False}
    with _lock:
        rows = [x for x in liste() if not x.get('fertig') or time.time() - x['ende'] < 3600][-19:]
        rows.append(r)
        _speichern(rows)
        _plane(r)
    return r


def stoppen(tid):
    with _lock:
        rows = liste()
        keep = [r for r in rows if r['id'] != tid]
        t = _timers.pop(tid, None)
        if t:
            t.cancel()
        _speichern(keep)
        return len(keep) != len(rows)


def fmt(sek):
    sek = max(0, int(sek))
    return '%d:%02d:%02d' % (sek // 3600, sek % 3600 // 60, sek % 60) if sek >= 3600 else '%d:%02d' % (sek // 60, sek % 60)


_PAGE = """<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Küchen-Timer</title>
<style>body{font:20px system-ui;background:#10131a;color:#eee;max-width:640px;margin:auto;padding:16px}
button{font:inherit;padding:14px 18px;margin:4px;border:0;border-radius:10px;background:#2a3350;color:#fff}button:focus,button:hover{outline:3px solid #8ab4ff}
.t{display:flex;justify-content:space-between;align-items:center;background:#1b2133;border-radius:10px;padding:10px 14px;margin:8px 0}
.t b{font-size:1.6em}.f{background:#5a2330}input{font:inherit;padding:12px;width:5em;border-radius:8px;border:0}</style>
<h1>⏲️ Küchen-Timer</h1><div id="p">__PRESETS__</div>
<p><input id="n" type="number" min="1" step="any" placeholder="Min"> <button onclick="go('',n.value)">Starten</button></p><div id="l"></div>
<script>
const B=location.pathname.replace(/\\/index$/,'/')+'';const Q=location.search;let T=[],off=0,piep={};
function url(p){return B+p+Q+(Q?'&':'?')+'_=1'}
function go(name,m){if(!(+m>0))return;fetch(url('start'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,minuten:+m})}).then(load)}
function stop(id){fetch(url('stop'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})}).then(load)}
function f(s){s=Math.max(0,s|0);const h=s/3600|0,m=s%3600/60|0,x=s%60;return(h?h+':'+String(m).padStart(2,'0'):m)+':'+String(x).padStart(2,'0')}
function beep(){try{const c=new AudioContext();[0,.3,.6].forEach(t=>{const o=c.createOscillator();o.connect(c.destination);o.frequency.value=880;o.start(c.currentTime+t);o.stop(c.currentTime+t+.2)})}catch(e){}}
function load(){fetch(url('liste')).then(r=>r.json()).then(j=>{T=j.timer;off=j.jetzt-Date.now()/1000;draw()})}
function draw(){const now=Date.now()/1000+off;l.innerHTML='';T.forEach(t=>{const r=t.ende-now,d=r<=0;if(d&&!piep[t.id]){piep[t.id]=1;beep()}
const e=document.createElement('div');e.className='t'+(d?' f':'');e.innerHTML='<span></span><b></b><button>✕</button>';e.children[0].textContent=t.name;e.children[1].textContent=d?'Fertig!':f(r);e.children[2].onclick=()=>stop(t.id);l.append(e)})}
load();setInterval(draw,1000);setInterval(load,15000);
</script>"""


def register(api):
    global _api
    _api = api
    for r in liste():                                 # nach einem Neustart weiterlaufen lassen
        if not r.get('fertig'):
            _plane(r)

    def seite(req):
        btn = ''.join('<button onclick="go(%s,%g)">%s · %g min</button>' % (
            html.escape(repr(n), quote=True), m, html.escape(n), m) for n, m in presets(api.get('presets')))
        return _PAGE.replace('__PRESETS__', btn)

    def _post(req):
        try:
            return req.json or {}
        except Exception:                             # noqa: BLE001
            return {}

    def start(req):
        j = _post(req)
        r = starten(j.get('name'), j.get('minuten'))
        return ({'ok': True, 'timer': r}, 200) if r else ({'error': 'Ungültige Minuten'}, 400)

    def stop(req):
        return {'ok': stoppen(str(_post(req).get('id') or ''))}

    def liste_route(req):
        return {'timer': liste(), 'jetzt': time.time()}

    def widget():
        run = sorted((r for r in liste() if not r.get('fertig') and r['ende'] > time.time()), key=lambda r: r['ende'])
        if not run:
            return None
        return {'icon': '⏲️', 'text': '%s %s' % (run[0]['name'][:20], fmt(run[0]['ende'] - time.time())),
                'sub': '%d Timer läuft' % len(run) if len(run) == 1 else '%d Timer laufen' % len(run),
                'lines': ['%s %s' % (r['name'], fmt(r['ende'] - time.time())) for r in run[1:5]]}

    api.route('index', seite)
    api.route('start', start)
    api.route('stop', stop)
    api.route('liste', liste_route)
    api.widget('Timer', widget, ttl=20, id='timer', icon='⏲️')
