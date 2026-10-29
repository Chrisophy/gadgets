# -*- coding: utf-8 -*-
"""Pong im Netzwerk: zwei Geräte im Haus spielen gegeneinander - oder einer gegen den Computer.

Öffnen: Erweiterungsliste -> Pong -> „Pong öffnen“ (auf beiden Geräten). Name eingeben, „Mitspielen“ wählen.
Wer zuerst da ist, bekommt links, der Zweite rechts. Ist noch niemand da: „Gegen Computer“. Weitere Geräte können zuschauen.
Fernbedienung: hoch/runter bewegt den Schläger · Touch/Maus: Finger bzw. Zeiger auf dem Spielfeld verschieben.
Wer zuerst die eingestellte Punktzahl erreicht (Standard 7), gewinnt; die Siege werden pro Name gezählt.
Das Spiel läuft in der Engine (60 Bilder pro Sekunde); die Geräte fragen den Stand ab und melden ihren Schläger.
"""
import random
import threading
import time

EXT_ID = 'pong'
EXT_NAME = 'Pong'
EXT_DESCRIPTION = 'Pong für zwei Geräte im Heimnetz (oder gegen den Computer) - Fernbedienung und Touch, Siegerliste.'
EXT_LINKS = [('Pong öffnen', 'index')]
EXT_SETTINGS = [
    {'key': 'ziel', 'label': 'Gewonnen hat, wer … Punkte erreicht', 'type': 'number', 'default': 7, 'min': 1, 'max': 21},
    {'key': 'tempo', 'label': 'Spieltempo (1 = normal)', 'type': 'number', 'default': 1, 'min': 0.5, 'max': 3},
]

B, H = 800.0, 500.0            # Spielfeld
PH, BALL = 90.0, 10.0          # Schlägerhöhe, Ballradius
PX = 30.0                      # Abstand der Schläger vom Rand
TIMEOUT = 10.0                 # so lange darf ein Gerät schweigen, bevor sein Platz frei wird
GRUND = 340.0                  # Ballgeschwindigkeit (px/s)
MAX_V = 900.0
_api = None
_lock = threading.RLock()
_thread = None
S = {}


def neu():
    return {'status': 'wartet', 'seats': {'links': None, 'rechts': None}, 'score': [0, 0], 'ball': [B / 2, H / 2], 'v': [0.0, 0.0],
            'pad': [0.5, 0.5], 'start': 0.0, 'sieger': '', 'letzte_aktion': time.time(), 'serve': 1, 'gezaehlt': False}


S.update(neu())


def aufschlag(s, richtung):
    """Ball in die Mitte, Richtung +1 (nach rechts) oder -1 (nach links), leicht schräg."""
    s['ball'] = [B / 2, H / 2]
    w = random.uniform(-0.45, 0.45)
    v = GRUND * float(_tempo())
    s['v'] = [richtung * v, w * v]


def _tempo():
    try:
        return max(0.5, min(3.0, float(_api.get('tempo') or 1))) if _api else 1.0
    except (TypeError, ValueError):
        return 1.0


def _ziel():
    try:
        return max(1, min(21, int(_api.get('ziel') or 7))) if _api else 7
    except (TypeError, ValueError):
        return 7


def schritt(s, dt, ziel=7):
    """Ein Physikschritt. Gibt 'punkt', 'ende' oder None zurück. Reine Funktion auf dem Zustand (testbar)."""
    x, y = s['ball']
    vx, vy = s['v']
    x += vx * dt
    y += vy * dt
    if y < BALL:
        y, vy = BALL, abs(vy)
    elif y > H - BALL:
        y, vy = H - BALL, -abs(vy)
    for seite, face in ((0, PX + 12), (1, B - PX - 12)):
        py = s['pad'][seite] * H
        trifft = abs(y - py) <= PH / 2 + BALL
        if seite == 0 and vx < 0 and x - BALL <= face and x + BALL > PX and trifft:
            x = face + BALL
            vx = min(MAX_V, abs(vx) * 1.07)
            vy += (y - py) / (PH / 2) * 260
        elif seite == 1 and vx > 0 and x + BALL >= face and x - BALL < B - PX and trifft:
            x = face - BALL
            vx = -min(MAX_V, abs(vx) * 1.07)
            vy += (y - py) / (PH / 2) * 260
    vy = max(-MAX_V, min(MAX_V, vy))
    s['ball'], s['v'] = [x, y], [vx, vy]
    if x < -BALL * 2 or x > B + BALL * 2:
        gewinner = 1 if x < 0 else 0
        s['score'][gewinner] += 1
        s['serve'] = 1 if gewinner == 0 else -1                # Aufschlag zum Verlierer hin
        if s['score'][gewinner] >= ziel:
            return 'ende'
        return 'punkt'
    return None


def _namen(s):
    return [(s['seats'][k] or {}).get('name', '') for k in ('links', 'rechts')]


def _bewege_computer(s, dt):
    for i, k in enumerate(('links', 'rechts')):
        seat = s['seats'][k]
        if seat and seat.get('bot'):
            ziel_y = s['ball'][1] / H if ((i == 1 and s['v'][0] > 0) or (i == 0 and s['v'][0] < 0)) else 0.5
            d = ziel_y - s['pad'][i]
            gr = 0.62 * _tempo() * dt                          # etwas langsamer als der Ball: schlagbar
            s['pad'][i] += max(-gr, min(gr, d))
            s['pad'][i] = max(PH / 2 / H, min(1 - PH / 2 / H, s['pad'][i]))


def _aufraeumen(s, jetzt):
    for k in ('links', 'rechts'):
        seat = s['seats'][k]
        if seat and not seat.get('bot') and jetzt - seat['last'] > TIMEOUT:
            s['seats'][k] = None
    menschen = [k for k in ('links', 'rechts') if s['seats'][k] and not s['seats'][k].get('bot')]
    if not menschen:                                           # Computer ohne Mensch spielt nicht weiter
        for k in ('links', 'rechts'):
            s['seats'][k] = None
    if s['status'] in ('start', 'laeuft') and not (s['seats']['links'] and s['seats']['rechts']):
        s['status'] = 'wartet'
        s['score'] = [0, 0]


def _loop():
    global _thread
    letzte = time.time()
    leer_seit = None
    while True:
        time.sleep(1 / 60.0)
        jetzt = time.time()
        dt = min(0.05, jetzt - letzte)
        letzte = jetzt
        with _lock:
            s = S
            _aufraeumen(s, jetzt)
            if s['status'] == 'wartet' and s['seats']['links'] and s['seats']['rechts']:
                s['status'], s['start'], s['score'] = 'start', jetzt + 3.0, [0, 0]
            if s['status'] == 'start' and jetzt >= s['start']:
                s['status'] = 'laeuft'
                aufschlag(s, random.choice((-1, 1)))
            if s['status'] == 'laeuft':
                _bewege_computer(s, dt)
                r = schritt(s, dt, _ziel())
                if r == 'punkt':
                    aufschlag(s, s['serve'])
                elif r == 'ende':
                    s['status'] = 'ende'
                    i = 0 if s['score'][0] > s['score'][1] else 1
                    seat = s['seats']['links' if i == 0 else 'rechts']
                    s['sieger'] = (seat or {}).get('name', '?')
                    if seat and not seat.get('bot'):
                        _sieg(seat['name'])
            if not any(S['seats'].values()):
                leer_seit = leer_seit or jetzt
                if jetzt - leer_seit > 20:
                    _thread = None
                    S.update(neu())
                    return
            else:
                leer_seit = None


def _sieg(name):
    try:
        d = _api.get('siege', {})
        d = d if isinstance(d, dict) else {}
        d[name] = int(d.get(name, 0)) + 1
        _api.set('siege', d)
    except Exception:                                          # noqa: BLE001
        pass


def _sicherstellen():
    global _thread
    with _lock:
        if _thread is None or not _thread.is_alive():
            _thread = threading.Thread(target=_loop, name='pong', daemon=True)
            _thread.start()


def _sicht(s):
    k = 0.0
    if s['status'] == 'start':
        k = max(0.0, s['start'] - time.time())
    return {'status': s['status'], 'ball': [s['ball'][0] / B, s['ball'][1] / H], 'pad': list(s['pad']), 'score': list(s['score']),
            'namen': _namen(s), 'ziel': _ziel(), 'sieger': s['sieger'], 'countdown': round(k, 1), 'ph': PH / H, 'bd': BALL / B,
            'frei': [k2 for k2 in ('links', 'rechts') if not s['seats'][k2]]}


PAGE = r"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no"><title>Pong</title>
<style>
:root{--bg:#0f141b;--fg:#e8edf3;--mut:#93a1b3;--card:#18202b;--acc:#4da3ff}
*{box-sizing:border-box}body{margin:0;height:100vh;height:100dvh;overflow:hidden;background:var(--bg);color:var(--fg);font:clamp(16px,2.6vmin,28px)/1.4 system-ui,sans-serif;display:flex;flex-direction:column;align-items:center;gap:10px;padding:10px;-webkit-user-select:none;user-select:none;overscroll-behavior:none}
#top{width:min(96vw,calc((100vh - 8.5em)*1.6));width:min(96vw,calc((100dvh - 8.5em)*1.6));display:flex;justify-content:space-between;gap:10px;color:var(--mut)}#top b{color:var(--fg);font-size:1.4em}
#cvw{position:relative;width:min(96vw,calc((100vh - 8.5em)*1.6));width:min(96vw,calc((100dvh - 8.5em)*1.6));aspect-ratio:8/5;touch-action:none}canvas{display:block;width:100%;height:100%;background:var(--card);border-radius:12px}
#msg{position:absolute;inset:0;display:grid;place-items:center;text-align:center;background:rgba(5,8,13,.72);border-radius:12px;padding:14px}
#msg small{display:block;color:var(--mut)}
#lobby{display:flex;gap:10px;flex-wrap:wrap;justify-content:center;align-items:center}
input{font:inherit;padding:.5em .8em;border-radius:12px;border:2px solid var(--mut);background:var(--card);color:var(--fg);width:11em}
button{font:inherit;color:var(--fg);background:var(--card);border:4px solid transparent;border-radius:14px;padding:.55em 1em;cursor:pointer}button.f,button:focus{outline:none;border-color:var(--acc)}
</style></head><body>
<div id="top"><span><b id="n0">-</b> <b id="s0">0</b></span><span id="info"></span><span><b id="s1">0</b> <b id="n1">-</b></span></div>
<div id="cvw"><canvas id="cv" width="800" height="500"></canvas><div id="msg"></div></div>
<div id="lobby"><input id="nm" maxlength="16" placeholder="Dein Name" autocomplete="off"><button id="bj">Mitspielen</button><button id="bc" style="display:none">Gegen Computer</button><button id="bl" style="display:none">Aufhören</button></div>
<script>
"use strict";
const $=(s)=>document.querySelector(s);
let me=null,st=null,y=0.5,vy=0,sending=false,lastT=performance.now(),btn=0;
try{$('#nm').value=localStorage.getItem('pong.name')||''}catch(e){}
async function post(p,b){const r=await fetch(p,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b||{})});return r.json()}
async function join(){const name=($('#nm').value||'Spieler').trim().slice(0,16);try{localStorage.setItem('pong.name',name)}catch(e){}const r=await post('beitreten',{name});if(r.error){$('#msg').innerHTML=r.error;return}me=r;y=0.5}
async function leave(){if(me){await post('verlassen',{platz:me.platz,token:me.token});me=null}}
$('#bj').onclick=join;$('#bl').onclick=leave;$('#bc').onclick=async()=>{if(me)await post('computer',{platz:me.platz,token:me.token})};
function sheet(){const L=['bj','bc','bl'].map(i=>$('#'+i)).filter(b=>b.style.display!=='none');return L}
document.addEventListener('keydown',e=>{const k=e.key;
  if(k==='ArrowUp'||k==='ArrowDown'){if(me){e.preventDefault();vy=k==='ArrowUp'?-1.1:1.1}}
  else if(k==='ArrowLeft'||k==='ArrowRight'){if(!me){const L=sheet();btn=(btn+(k==='ArrowRight'?1:-1)+L.length)%L.length;L.forEach((b,i)=>b.classList.toggle('f',i===btn))}}
  else if((k==='Enter'||k==='Select')&&document.activeElement.tagName!=='INPUT'){e.preventDefault();if(me&&st&&st.status==='ende')post('nochmal',{platz:me.platz,token:me.token});else{const L=sheet();const b=L[Math.min(btn,L.length-1)]||$('#bj');b.click()}}
  else if(k==='Escape'||k==='Backspace'&&document.activeElement.tagName!=='INPUT'){if(me){e.preventDefault();leave()}}});
document.addEventListener('keyup',e=>{if(e.key==='ArrowUp'||e.key==='ArrowDown')vy=0});
const cvw=$('#cvw');
function pointer(cy){const r=cvw.getBoundingClientRect();y=Math.max(0,Math.min(1,(cy-r.top)/r.height))}
cvw.addEventListener('touchstart',e=>{pointer(e.touches[0].clientY)},{passive:true});
cvw.addEventListener('touchmove',e=>{e.preventDefault();pointer(e.touches[0].clientY)},{passive:false});
cvw.addEventListener('mousemove',e=>{if(me)pointer(e.clientY)});
cvw.addEventListener('click',()=>{if(me&&st&&st.status==='ende')post('nochmal',{platz:me.platz,token:me.token})});
function draw(){const cv=$('#cv'),x=cv.getContext('2d');x.clearRect(0,0,800,500);x.fillStyle='#18202b';x.fillRect(0,0,800,500);
  x.strokeStyle='rgba(255,255,255,.18)';x.setLineDash([10,14]);x.lineWidth=3;x.beginPath();x.moveTo(400,0);x.lineTo(400,500);x.stroke();x.setLineDash([]);
  if(!st)return;const ph=st.ph*500;x.fillStyle='#e8edf3';
  [[30,st.pad[0]],[800-30-12,st.pad[1]]].forEach((p,i)=>{x.fillStyle=(me&&me.platz===(i?'rechts':'links'))?'#4da3ff':'#e8edf3';x.fillRect(p[0],p[1]*500-ph/2,12,ph)});
  if(st.status==='laeuft'){x.fillStyle='#ffd54f';x.beginPath();x.arc(st.ball[0]*800,st.ball[1]*500,10,0,7);x.fill()}}
function ui(){if(!st)return;$('#n0').textContent=st.namen[0]||'-';$('#n1').textContent=st.namen[1]||'-';$('#s0').textContent=st.score[0];$('#s1').textContent=st.score[1];
  $('#info').textContent='bis '+st.ziel+' Punkte';const m=$('#msg');let t='';
  if(!me){t=st.frei.length?'Frei: '+st.frei.join(' / ')+'<small>Name eingeben und „Mitspielen“</small>':(st.status==='laeuft'?'':'Beide Plätze besetzt<small>Du schaust zu</small>')}
  else if(st.status==='wartet')t='Warte auf Mitspieler …<small>oder „Gegen Computer“ wählen</small>';
  else if(st.status==='start')t='Gleich geht’s los: '+Math.ceil(st.countdown)+'<small>Du bist '+(me.platz==='links'?'links':'rechts')+' (blau)</small>';
  else if(st.status==='ende')t='🏆 '+st.sieger+' gewinnt!<small>OK oder tippen = Revanche</small>';
  m.innerHTML=t;m.style.display=t?'grid':'none';
  $('#bj').style.display=me?'none':'';$('#nm').style.display=me?'none':'';$('#bl').style.display=me?'':'none';$('#bc').style.display=(me&&st.status==='wartet')?'':'none'}
async function poll(){const now=performance.now(),dt=(now-lastT)/1000;lastT=now;if(me&&vy)y=Math.max(0,Math.min(1,y+vy*dt));
  try{const r=me?await post('tick',{platz:me.platz,token:me.token,y}):await (await fetch('zustand')).json();
    if(r.error==='weg'){me=null}else if(r.status){st=r}}catch(e){}
  draw();ui();setTimeout(poll,me?33:120)}
window.PG={state:()=>({me,st,y}),setY:(v)=>{y=v}};
poll();
</script></body></html>"""


def register(api):
    global _api
    _api = api

    def post_only(fn):
        def wrap(req):
            if req.method != 'POST':
                return ({'error': 'Nur per POST'}, 405)
            return fn(req.json if isinstance(req.json, dict) else {})
        return wrap

    def platz_pruefen(d):
        k = d.get('platz')
        seat = S['seats'].get(k) if k in ('links', 'rechts') else None
        if seat is None or seat.get('bot') or seat['token'] != d.get('token'):
            return None, None
        return k, seat

    def beitreten(d):
        name = str(d.get('name') or 'Spieler').strip()[:16] or 'Spieler'
        with _lock:
            frei = [k for k in ('links', 'rechts') if S['seats'][k] is None]
            if not frei:
                return ({'error': 'Beide Plätze sind besetzt - du kannst zuschauen.'}, 409)
            k = frei[0]
            tok = '%016x' % random.getrandbits(64)
            if any(S['seats'][o] and S['seats'][o].get('name') == name and not S['seats'][o].get('bot') for o in ('links', 'rechts')):
                name = name[:13] + ' 2'
            S['seats'][k] = {'name': name, 'token': tok, 'last': time.time(), 'bot': False}
            S['pad'][0 if k == 'links' else 1] = 0.5
        _sicherstellen()
        return {'platz': k, 'token': tok, 'name': name}

    def tick(d):
        with _lock:
            k, seat = platz_pruefen(d)
            if seat is None:
                return {'error': 'weg'}
            seat['last'] = time.time()
            try:
                y = float(d.get('y'))
            except (TypeError, ValueError):
                y = 0.5
            lo = PH / 2 / H
            S['pad'][0 if k == 'links' else 1] = max(lo, min(1 - lo, y))
            return _sicht(S)

    def computer(d):
        with _lock:
            k, seat = platz_pruefen(d)
            if seat is None:
                return ({'error': 'weg'}, 403)
            andere = 'rechts' if k == 'links' else 'links'
            if S['seats'][andere] is None:
                S['seats'][andere] = {'name': 'Computer', 'token': '', 'last': time.time(), 'bot': True}
        return {'ok': True}

    def verlassen(d):
        with _lock:
            k, seat = platz_pruefen(d)
            if seat is not None:
                S['seats'][k] = None
                if S['status'] != 'wartet':
                    S['status'], S['score'], S['sieger'] = 'wartet', [0, 0], ''
        return {'ok': True}

    def nochmal(d):
        with _lock:
            k, seat = platz_pruefen(d)
            if seat is None:
                return ({'error': 'weg'}, 403)
            if S['status'] == 'ende':
                S['status'], S['score'], S['sieger'] = 'wartet', [0, 0], ''
        return {'ok': True}

    def zustand(req):
        with _lock:
            return _sicht(S)

    def widget():
        with _lock:
            s = S
            n = [x for x in _namen(s) if x]
            if s['status'] == 'laeuft' or s['status'] == 'start':
                return {'icon': '🏓', 'text': 'Pong läuft', 'sub': '%s %d : %d %s' % (_namen(s)[0], s['score'][0], s['score'][1], _namen(s)[1])}
            if n:
                return {'icon': '🏓', 'text': 'Pong: %s wartet' % n[0][:20], 'sub': 'Mitspielen: Erweiterungsliste -> Pong öffnen'}
        siege = _api.get('siege', {}) or {}
        if siege:
            top = max(siege.items(), key=lambda kv: kv[1])
            return {'icon': '🏓', 'text': 'Pong', 'sub': 'Meiste Siege: %s (%d)' % top}
        return {'icon': '🏓', 'text': 'Pong', 'sub': 'Zwei Geräte, ein Spiel - jetzt starten'}

    api.route('index', lambda req: PAGE)
    api.route('beitreten', post_only(beitreten))
    api.route('tick', post_only(tick))
    api.route('computer', post_only(computer))
    api.route('verlassen', post_only(verlassen))
    api.route('nochmal', post_only(nochmal))
    api.route('zustand', zustand)
    api.route('siege', lambda req: _api.get('siege', {}) or {})
    api.widget('Pong', widget, ttl=5, icon='🏓')
