# -*- coding: utf-8 -*-
"""Minispiele: Snake, 2048 und Memory - mit Fernbedienung (Pfeiltasten + OK) und per Touch (Wischen/Tippen) spielbar.

Öffnen: Erweiterungsliste -> Minispiele -> „Minispiele öffnen“ (im Browser des Geräts; am Fernseher mit der Fernbedienung).
Bedienung:  Pfeiltasten / D-Pad = steuern · OK/Enter = auswählen, pausieren, neu starten · Zurück/Esc = ins Menü.
            Touch: wischen (Snake, 2048), tippen (Memory, Knöpfe).
Die Rekorde werden in der Engine gespeichert und gelten für alle Geräte im Haus. Die Kachel „Minispiele“ zeigt sie an.
"""
import threading

EXT_ID = 'minispiele'
EXT_NAME = 'Minispiele'
EXT_DESCRIPTION = 'Snake, 2048 und Memory für Fernbedienung und Touch - mit gemeinsamen Rekorden und Kachel.'
EXT_LINKS = [('Minispiele öffnen', 'index')]

SPIELE = {'snake': 'hoch', '2048': 'hoch', 'memory': 'niedrig'}      # hoch = mehr ist besser, niedrig = weniger (Züge)
_api = None
_lock = threading.Lock()

PAGE = r"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no"><title>Minispiele</title>
<style>
:root{--bg:#0f141b;--fg:#e8edf3;--mut:#93a1b3;--card:#18202b;--acc:#4da3ff;--bad:#ff6b6b;--ok:#4cd08a}
*{box-sizing:border-box}html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:clamp(16px,2.4vmin,26px)/1.4 system-ui,sans-serif;display:flex;flex-direction:column;align-items:center;-webkit-user-select:none;user-select:none;overscroll-behavior:none}
header{width:min(94vw,92vh);display:flex;align-items:center;gap:12px;padding:10px 0}
header h1{font-size:1.2em;margin:0;flex:1}header .s{color:var(--mut);white-space:nowrap}
button{font:inherit;color:var(--fg);background:var(--card);border:3px solid transparent;border-radius:14px;padding:.5em 1em;cursor:pointer}
button:focus,button.f{outline:none;border-color:var(--acc)}
#menu{display:grid;gap:14px;width:min(80vw,70vh);margin-top:6vh}#menu button{padding:.9em 1em;font-size:1.3em;text-align:left}#menu small{display:block;color:var(--mut);font-size:.65em}
#stage{width:min(94vw,calc(100vh - 150px));aspect-ratio:1;position:relative;touch-action:none}
canvas{width:100%;height:100%;background:var(--card);border-radius:14px;display:block}
.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:2.2%;height:100%;background:#0b1016;padding:2.2%;border-radius:14px}
.t{display:grid;place-items:center;border-radius:10px;background:var(--card);font-weight:700;font-size:clamp(20px,6vmin,56px);transition:transform .08s}
.t[data-v="2"]{background:#2b3a4f}.t[data-v="4"]{background:#34506f}.t[data-v="8"]{background:#d98a3d}.t[data-v="16"]{background:#e2702f}
.t[data-v="32"]{background:#e2552f}.t[data-v="64"]{background:#e0322f}.t[data-v="128"]{background:#cdb24a}.t[data-v="256"]{background:#c7b02a}
.t[data-v="512"]{background:#bfae12}.t[data-v="1024"]{background:#b6a500}.t[data-v="2048"]{background:#4cd08a;color:#052}
.c{cursor:pointer;font-size:clamp(24px,8vmin,72px)}.c.o,.c.d{background:#27415f}.c.d{opacity:.45}.c.cur{outline:4px solid var(--acc)}
#msg{position:absolute;inset:0;display:none;place-items:center;text-align:center;background:rgba(5,8,13,.78);border-radius:14px;padding:16px;font-size:1.3em}
#msg.on{display:grid}#msg small{display:block;color:var(--mut);margin-top:.4em}
#pad{display:none;grid-template-columns:repeat(3,1fr);gap:8px;width:min(60vw,200px);margin:10px 0}#pad button{padding:.5em}
@media (pointer:coarse){#pad.snake{display:grid}}
</style></head><body>
<header><h1 id="ti">🎮 Minispiele</h1><span class="s" id="sc"></span><button id="bm" style="display:none">☰ Menü</button></header>
<div id="menu">
  <button data-g="snake">🐍 Snake<small id="r-snake"></small></button>
  <button data-g="2048">🔢 2048<small id="r-2048"></small></button>
  <button data-g="memory">🃏 Memory<small id="r-memory"></small></button>
  <small style="color:var(--mut)">Fernbedienung: Pfeile + OK · Touch: tippen und wischen</small>
</div>
<div id="stage" style="display:none"><canvas id="cv" width="540" height="540"></canvas><div class="g4" id="grid" style="display:none"></div><div id="msg"></div></div>
<div id="pad"><span></span><button data-d="up">▲</button><span></span><button data-d="left">◀</button><button data-d="down">▼</button><button data-d="right">▶</button></div>
<script>
"use strict";
const $=(s)=>document.querySelector(s);
const DIRS={up:[0,-1],down:[0,1],left:[-1,0],right:[1,0]};
const KEYDIR={ArrowUp:'up',ArrowDown:'down',ArrowLeft:'left',ArrowRight:'right',w:'up',s:'down',a:'left',d:'right'};
const BACK=['Escape','Backspace','GoBack','BrowserBack'];
let mode='menu',cur=null,timer=null,best={},menuIdx=0;

/* ---------- Rekorde (in der Engine gespeichert) ---------- */
async function loadBest(){try{const r=await fetch('punkte');best=await r.json()}catch(e){best={}}drawBest()}
function bestText(g){const b=best[g];if(b==null)return 'Noch kein Rekord';return g==='memory'?'Rekord: '+b+' Züge':'Rekord: '+b}
function drawBest(){['snake','2048','memory'].forEach(g=>{const e=$('#r-'+g);if(e)e.textContent=bestText(g)})}
async function report(g,v){try{const r=await fetch('punkte',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({spiel:g,wert:v})});best=await r.json();drawBest()}catch(e){}}

/* ---------- Snake ---------- */
function snakePlace(s,rnd){const free=[];const o=new Set(s.body.map(c=>c[0]+','+c[1]));for(let y=0;y<s.n;y++)for(let x=0;x<s.n;x++)if(!o.has(x+','+y))free.push([x,y]);return free.length?free[Math.floor((rnd||Math.random)()*free.length)]:null}
function snakeNew(rnd){const n=18,m=n>>1;const s={n,body:[[m,m],[m-1,m],[m-2,m]],dir:[1,0],queue:[],food:null,score:0,over:false,paused:false};s.food=snakePlace(s,rnd);return s}
function snakeTurn(s,name){const d=DIRS[name];if(!d)return;const last=s.queue.length?s.queue[s.queue.length-1]:s.dir;if(d[0]===-last[0]&&d[1]===-last[1])return;if(d[0]===last[0]&&d[1]===last[1])return;if(s.queue.length<2)s.queue.push(d)}
function snakeStep(s,rnd){if(s.over)return s;if(s.queue.length)s.dir=s.queue.shift();const h=s.body[0],n=s.n;const nx=(h[0]+s.dir[0]+n)%n,ny=(h[1]+s.dir[1]+n)%n;const eat=!!s.food&&nx===s.food[0]&&ny===s.food[1];const tail=eat?s.body:s.body.slice(0,-1);if(tail.some(c=>c[0]===nx&&c[1]===ny)){s.over=true;return s}s.body.unshift([nx,ny]);if(eat){s.score++;s.food=snakePlace(s,rnd)}else s.body.pop();return s}
function snakeDraw(s){const cv=$('#cv'),x=cv.getContext('2d'),c=cv.width/s.n;x.clearRect(0,0,cv.width,cv.height);x.fillStyle='#18202b';x.fillRect(0,0,cv.width,cv.height);
  if(s.food){x.fillStyle='#ff6b6b';x.beginPath();x.arc((s.food[0]+.5)*c,(s.food[1]+.5)*c,c*.38,0,7);x.fill()}
  s.body.forEach((p,i)=>{x.fillStyle=i?'#4cd08a':'#9dffc8';x.fillRect(p[0]*c+1,p[1]*c+1,c-2,c-2)})}
function snakeLoop(){clearTimeout(timer);if(mode!=='snake')return;const s=cur;if(!s.over&&!s.paused){snakeStep(s);snakeDraw(s);setScore('Punkte: '+s.score);if(s.over){report('snake',s.score);msg('Game Over<small>'+s.score+' Punkte · OK = nochmal · Zurück = Menü</small>')}}
  timer=setTimeout(snakeLoop,Math.max(70,160-s.score*4))}
function snakeStart(){cur=snakeNew();msg('');snakeDraw(cur);setScore('Punkte: 0');snakeLoop()}

/* ---------- 2048 ---------- */
function slide(line){const a=line.filter(v=>v);let gained=0;const out=[];for(let i=0;i<a.length;i++){if(a[i+1]===a[i]){out.push(a[i]*2);gained+=a[i]*2;i++}else out.push(a[i])}while(out.length<line.length)out.push(0);return{line:out,gained}}
function lines4(dir){const L=[];for(let i=0;i<4;i++){const idx=[];for(let j=0;j<4;j++){const k=dir==='left'?[i,j]:dir==='right'?[i,3-j]:dir==='up'?[j,i]:[3-j,i];idx.push(k[0]*4+k[1])}L.push(idx)}return L}
function move2048(g,dir){let moved=false,gain=0;for(const idx of lines4(dir)){const r=slide(idx.map(i=>g.b[i]));r.line.forEach((v,j)=>{if(g.b[idx[j]]!==v){moved=true;g.b[idx[j]]=v}});gain+=r.gained}g.score+=gain;return moved}
function can2048(g){return['left','right','up','down'].some(d=>move2048({b:g.b.slice(),score:0},d))}
function add2048(g,rnd){const free=[];g.b.forEach((v,i)=>{if(!v)free.push(i)});if(!free.length)return;g.b[free[Math.floor((rnd||Math.random)()*free.length)]]=(rnd||Math.random)()<.9?2:4}
function new2048(rnd){const g={b:Array(16).fill(0),score:0,over:false};add2048(g,rnd);add2048(g,rnd);return g}
function draw2048(g){const el=$('#grid');el.textContent='';g.b.forEach(v=>{const t=document.createElement('div');t.className='t';t.dataset.v=v;t.textContent=v||'';el.appendChild(t)});setScore('Punkte: '+g.score)}
function turn2048(name){const g=cur;if(g.over||!DIRS[name])return;if(move2048(g,name)){add2048(g);draw2048(g);if(!can2048(g)){g.over=true;report('2048',g.score);msg('Keine Züge mehr<small>'+g.score+' Punkte · OK = nochmal · Zurück = Menü</small>')}}}
function start2048(){cur=new2048();msg('');draw2048(cur)}

/* ---------- Memory ---------- */
const EMOJI=['🎬','🍿','🎭','📺','🎞️','⭐','🎥','🎟️'];
function memNew(rnd){const r=rnd||Math.random;const a=EMOJI.concat(EMOJI).map(e=>({e,open:false,done:false}));for(let i=a.length-1;i>0;i--){const j=Math.floor(r()*(i+1));[a[i],a[j]]=[a[j],a[i]]}return{cards:a,first:null,lock:false,moves:0,cursor:0,t0:Date.now(),won:false}}
function memFlip(m,i,after){const c=m.cards[i];if(m.lock||m.won||!c||c.open||c.done)return false;c.open=true;if(m.first===null){m.first=i;return true}
  m.moves++;const f=m.cards[m.first];if(f.e===c.e){f.done=c.done=true;m.first=null;m.won=m.cards.every(x=>x.done)}else{m.lock=true;const a=m.first;m.first=null;const back=()=>{f.open=false;c.open=false;m.lock=false;if(after)after()};if(after===false)back();else setTimeout(back,750)}return true}
function memDraw(m){const el=$('#grid');el.textContent='';m.cards.forEach((c,i)=>{const t=document.createElement('div');t.className='t c'+(c.open?' o':'')+(c.done?' d':'')+(i===m.cursor?' cur':'');t.textContent=(c.open||c.done)?c.e:'❓';t.onclick=()=>{m.cursor=i;memAct()};el.appendChild(t)});setScore('Züge: '+m.moves)}
function memAct(){const m=cur;if(m.won){memStart();return}memFlip(m,m.cursor,()=>memDraw(m));memDraw(m);if(m.won){report('memory',m.moves);msg('Geschafft!<small>'+m.moves+' Züge in '+Math.round((Date.now()-m.t0)/1000)+' s · OK = nochmal · Zurück = Menü</small>')}}
function memMove(name){const m=cur,d=DIRS[name];if(!d)return;let x=m.cursor%4+d[0],y=Math.floor(m.cursor/4)+d[1];x=(x+4)%4;y=(y+4)%4;m.cursor=y*4+x;memDraw(m)}
function memStart(){cur=memNew();msg('');memDraw(cur)}

/* ---------- Gemeinsames ---------- */
function setScore(t){$('#sc').textContent=t}
function msg(html){const m=$('#msg');m.innerHTML=html;m.classList.toggle('on',!!html)}
function show(g){mode=g;clearTimeout(timer);const game=g!=='menu';$('#menu').style.display=game?'none':'grid';$('#stage').style.display=game?'block':'none';$('#bm').style.display=game?'':'none';
  $('#cv').style.display=g==='snake'?'block':'none';$('#grid').style.display=(g==='2048'||g==='memory')?'grid':'none';$('#pad').className=g==='snake'?'snake':'';
  $('#ti').textContent=g==='snake'?'🐍 Snake':g==='2048'?'🔢 2048':g==='memory'?'🃏 Memory':'🎮 Minispiele';setScore('');msg('');
  if(g==='snake')snakeStart();else if(g==='2048')start2048();else if(g==='memory')memStart();else{markMenu();loadBest()}}
function markMenu(){document.querySelectorAll('#menu button').forEach((b,i)=>b.classList.toggle('f',i===menuIdx));const b=document.querySelectorAll('#menu button')[menuIdx];if(b)b.focus()}
function over(){return cur&&(cur.over||cur.won)}
function direction(name){if(mode==='snake'){if(!cur.over)snakeTurn(cur,name)}else if(mode==='2048')turn2048(name);else if(mode==='memory')memMove(name);else if(mode==='menu'){menuIdx=(menuIdx+(name==='down'||name==='right'?1:-1)+3)%3;markMenu()}}
function ok(){if(mode==='menu'){show(['snake','2048','memory'][menuIdx]);return}
  if(mode==='snake'){if(cur.over)snakeStart();else{cur.paused=!cur.paused;msg(cur.paused?'Pause<small>OK = weiter</small>':'')}}
  else if(mode==='2048'){if(cur.over)start2048()}else if(mode==='memory')memAct()}
document.addEventListener('keydown',e=>{const k=e.key.length===1?e.key.toLowerCase():e.key;
  if(KEYDIR[k]){e.preventDefault();direction(KEYDIR[k])}
  else if(k==='Enter'||k===' '||k==='Select'){e.preventDefault();ok()}
  else if(BACK.includes(k)||e.keyCode===4){if(mode!=='menu'){e.preventDefault();show('menu')}}});
/* Touch: wischen */
let tx=0,ty=0;const st=$('#stage');
st.addEventListener('touchstart',e=>{tx=e.touches[0].clientX;ty=e.touches[0].clientY},{passive:true});
st.addEventListener('touchend',e=>{const t=e.changedTouches[0],dx=t.clientX-tx,dy=t.clientY-ty;if(Math.max(Math.abs(dx),Math.abs(dy))<24){if(mode!=='memory'&&over())ok();else if(mode==='snake'&&cur.paused)ok();return}
  if(mode==='memory')return;direction(Math.abs(dx)>Math.abs(dy)?(dx>0?'right':'left'):(dy>0?'down':'up'))},{passive:true});
st.addEventListener('touchmove',e=>e.preventDefault(),{passive:false});
document.querySelectorAll('#menu button').forEach((b,i)=>b.onclick=()=>{menuIdx=i;ok()});
document.querySelectorAll('#pad button').forEach(b=>b.onclick=()=>direction(b.dataset.d));
$('#bm').onclick=()=>show('menu');
window.MS={slide,move2048,can2048,snakeNew,snakeStep,snakeTurn,memNew,memFlip,state:()=>({mode,cur})};
show('menu');
</script></body></html>"""


def _vergleich(spiel, neu, alt):
    return alt is None or (neu > alt if SPIELE[spiel] == 'hoch' else neu < alt)


def register(api):
    global _api
    _api = api

    def punkte(req):
        if req.method == 'POST':
            d = req.json if isinstance(req.json, dict) else {}
            spiel = str(d.get('spiel') or '')
            try:
                wert = int(d.get('wert'))
            except (TypeError, ValueError):
                return ({'error': 'Wert fehlt'}, 400)
            if spiel not in SPIELE or wert < 0 or wert > 10_000_000:
                return ({'error': 'Unbekanntes Spiel oder ungültiger Wert'}, 400)
            with _lock:
                best = api.get('rekorde', {})
                best = best if isinstance(best, dict) else {}
                if _vergleich(spiel, wert, best.get(spiel)) and not (spiel == 'memory' and wert < 8):
                    best[spiel] = wert
                    api.set('rekorde', best)
                return best
        b = api.get('rekorde', {})
        return b if isinstance(b, dict) else {}

    def widget():
        b = punkte(type('R', (), {'method': 'GET', 'json': {}})())
        if not b:
            return {'icon': '🎮', 'text': 'Minispiele', 'sub': 'Snake · 2048 · Memory - noch keine Rekorde'}
        teile = []
        if 'snake' in b:
            teile.append('🐍 %d' % b['snake'])
        if '2048' in b:
            teile.append('🔢 %d' % b['2048'])
        if 'memory' in b:
            teile.append('🃏 %d Züge' % b['memory'])
        return {'icon': '🎮', 'text': 'Rekorde', 'sub': ' · '.join(teile)}

    api.route('index', lambda req: PAGE)
    api.route('punkte', punkte)
    api.widget('Minispiele', widget, ttl=60, icon='🎮')
