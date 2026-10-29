# -*- coding: utf-8 -*-
"""Tetris: Steine stapeln, Reihen füllen - mit Fernbedienung und Touch spielbar, Rekord gilt für alle Geräte.

Öffnen: Erweiterungsliste -> Tetris -> „Tetris öffnen“.
Fernbedienung:  links/rechts = bewegen · runter = schneller · hoch = drehen · OK = Stein fallen lassen · Zurück = Pause
Touch:          nach links/rechts ziehen = bewegen · tippen = drehen · nach unten wischen = fallen lassen · Knöpfe unten
"""
import threading

EXT_ID = 'tetris'
EXT_NAME = 'Tetris'
EXT_DESCRIPTION = 'Tetris für Fernbedienung und Touch mit gemeinsamem Rekord und Kachel.'
EXT_LINKS = [('Tetris öffnen', 'index')]
_api = None
_lock = threading.Lock()

PAGE = r"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no"><title>Tetris</title>
<style>
:root{--bg:#0f141b;--fg:#e8edf3;--mut:#93a1b3;--card:#18202b;--acc:#4da3ff}
*{box-sizing:border-box}html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:clamp(15px,2.3vmin,24px)/1.35 system-ui,sans-serif;display:flex;justify-content:center;align-items:center;gap:18px;flex-wrap:wrap;-webkit-user-select:none;user-select:none;overscroll-behavior:none;padding:8px}
#wrap{position:relative;height:min(78vh,150vw);aspect-ratio:1/2;touch-action:none}
canvas{display:block;width:100%;height:100%;background:var(--card);border-radius:12px}
#side{display:flex;flex-direction:column;gap:10px;min-width:9em}
#side div{background:var(--card);border-radius:12px;padding:.5em .8em}#side b{display:block;font-size:1.5em;color:var(--acc)}
#nx{display:block;width:100%;aspect-ratio:1;background:transparent}
#msg{position:absolute;inset:0;display:none;place-items:center;text-align:center;background:rgba(5,8,13,.8);border-radius:12px;padding:12px;font-size:1.2em}
#msg.on{display:grid}#msg small{display:block;color:var(--mut);margin-top:.4em}
#pad{display:none;gap:8px;width:100%;justify-content:center}#pad button{flex:1;max-width:80px;font:inherit;font-size:1.4em;color:var(--fg);background:var(--card);border:0;border-radius:12px;padding:.5em 0}
@media (pointer:coarse){#pad{display:flex}}
</style></head><body>
<div id="wrap"><canvas id="cv" width="300" height="600"></canvas><div id="msg"></div></div>
<div id="side"><div>Punkte<b id="sc">0</b></div><div>Reihen<b id="ln">0</b></div><div>Stufe<b id="lv">1</b></div><div>Rekord<b id="bs">-</b></div>
<div>Nächster<canvas id="nx" width="120" height="120"></canvas></div><div id="pad"><button data-k="left">◀</button><button data-k="rot">⟳</button><button data-k="down">▼</button><button data-k="drop">⏬</button><button data-k="right">▶</button></div></div>
<script>
"use strict";
const $=(s)=>document.querySelector(s);
const W=10,H=20,COL=['#000','#4dd0e1','#ffd54f','#ba68c8','#81c784','#e57373','#64b5f6','#ffb74d'];
const SHAPES=[null,[[1,1,1,1]],[[1,1],[1,1]],[[0,1,0],[1,1,1]],[[0,1,1],[1,1,0]],[[1,1,0],[0,1,1]],[[1,0,0],[1,1,1]],[[0,0,1],[1,1,1]]];
function rotate(m){return m[0].map((_,i)=>m.map(r=>r[i]).reverse())}
function collide(b,m,x,y){for(let j=0;j<m.length;j++)for(let i=0;i<m[j].length;i++)if(m[j][i]){const bx=x+i,by=y+j;if(bx<0||bx>=W||by>=H)return true;if(by>=0&&b[by][bx])return true}return false}
function bag(rnd){const a=[1,2,3,4,5,6,7];for(let i=6;i>0;i--){const j=Math.floor((rnd||Math.random)()*(i+1));[a[i],a[j]]=[a[j],a[i]]}return a}
function spawn(g){const k=g.queue.length<2?g.queue.push(...bag(g.rnd)):0;const t=g.queue.shift();g.p={k:t,m:SHAPES[t].map(r=>r.slice()),x:Math.floor((W-SHAPES[t][0].length)/2),y:0};
  if(collide(g.b,g.p.m,g.p.x,g.p.y))g.over=true}
function newGame(rnd){const g={b:Array.from({length:H},()=>Array(W).fill(0)),queue:[],p:null,score:0,lines:0,level:1,over:false,paused:false,rnd:rnd};g.queue.push(...bag(rnd));spawn(g);return g}
function tryMove(g,dx,dy){if(g.over||g.paused)return false;if(!collide(g.b,g.p.m,g.p.x+dx,g.p.y+dy)){g.p.x+=dx;g.p.y+=dy;return true}return false}
function tryRotate(g){if(g.over||g.paused||g.p.k===2)return false;const m=rotate(g.p.m);for(const dx of [0,-1,1,-2,2])if(!collide(g.b,m,g.p.x+dx,g.p.y)){g.p.m=m;g.p.x+=dx;return true}return false}
function lock(g){g.p.m.forEach((r,j)=>r.forEach((v,i)=>{if(v&&g.p.y+j>=0)g.b[g.p.y+j][g.p.x+i]=g.p.k}));let n=0;for(let y=H-1;y>=0;y--){if(g.b[y].every(v=>v)){g.b.splice(y,1);g.b.unshift(Array(W).fill(0));n++;y++}}
  g.score+=[0,100,300,500,800][n]*g.level;g.lines+=n;g.level=1+Math.floor(g.lines/10);spawn(g);return n}
function tick(g){if(g.over||g.paused)return;if(!tryMove(g,0,1))lock(g)}
function softDrop(g){if(tryMove(g,0,1))g.score+=1;else tick(g)}
function hardDrop(g){if(g.over||g.paused)return;let n=0;while(tryMove(g,0,1))n++;g.score+=2*n;lock(g)}
function speed(g){return Math.max(90,800-(g.level-1)*70)}

let g=null,timer=null,best=null;
function cell(x,c,px,py,s){x.fillStyle=COL[c];x.fillRect(px+1,py+1,s-2,s-2)}
function draw(){const cv=$('#cv'),x=cv.getContext('2d'),s=cv.width/W;x.clearRect(0,0,cv.width,cv.height);
  for(let y=0;y<H;y++)for(let i=0;i<W;i++){if(g.b[y][i])cell(x,g.b[y][i],i*s,y*s,s);else{x.fillStyle='rgba(255,255,255,.04)';x.fillRect(i*s+s/2-1,y*s+s/2-1,2,2)}}
  if(!g.over){let gy=g.p.y;while(!collide(g.b,g.p.m,g.p.x,gy+1))gy++;x.globalAlpha=.25;g.p.m.forEach((r,j)=>r.forEach((v,i)=>{if(v)cell(x,g.p.k,(g.p.x+i)*s,(gy+j)*s,s)}));x.globalAlpha=1;
    g.p.m.forEach((r,j)=>r.forEach((v,i)=>{if(v)cell(x,g.p.k,(g.p.x+i)*s,(g.p.y+j)*s,s)}))}
  const nx=$('#nx').getContext('2d');nx.clearRect(0,0,120,120);const nm=SHAPES[g.queue[0]];const ns=24,ox=(120-nm[0].length*ns)/2,oy=(120-nm.length*ns)/2;nm.forEach((r,j)=>r.forEach((v,i)=>{if(v)cell(nx,g.queue[0],ox+i*ns,oy+j*ns,ns)}));
  $('#sc').textContent=g.score;$('#ln').textContent=g.lines;$('#lv').textContent=g.level}
function msg(h){const m=$('#msg');m.innerHTML=h;m.classList.toggle('on',!!h)}
async function loadBest(){try{const r=await (await fetch('punkte')).json();best=r.tetris==null?null:r.tetris}catch(e){}$('#bs').textContent=best==null?'-':best}
async function report(v){try{const r=await (await fetch('punkte',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({wert:v})})).json();best=r.tetris;$('#bs').textContent=best}catch(e){}}
function loop(){clearTimeout(timer);if(g.over)return;if(!g.paused){tick(g);after()}timer=setTimeout(loop,speed(g))}
function after(){draw();if(g.over){report(g.score);msg('Game Over<small>'+g.score+' Punkte · OK = nochmal</small>')}}
function start(){g=newGame();msg('');draw();loop()}
function act(k){if(!g)return;if(g.over){if(k==='drop')start();return}
  if(k==='pause'){g.paused=!g.paused;msg(g.paused?'Pause<small>Zurück oder OK = weiter</small>':'');return}
  if(g.paused){if(k==='drop'){g.paused=false;msg('')}return}
  if(k==='left')tryMove(g,-1,0);else if(k==='right')tryMove(g,1,0);else if(k==='down')softDrop(g);else if(k==='rot')tryRotate(g);else if(k==='drop')hardDrop(g);
  after()}
const KEYS={ArrowLeft:'left',ArrowRight:'right',ArrowDown:'down',ArrowUp:'rot',Enter:'drop',' ':'drop',Select:'drop',Escape:'pause',Backspace:'pause',GoBack:'pause',BrowserBack:'pause',p:'pause'};
document.addEventListener('keydown',e=>{const a=KEYS[e.key]||(e.keyCode===4?'pause':null);if(a){e.preventDefault();act(a)}});
document.querySelectorAll('#pad button').forEach(b=>b.addEventListener('click',()=>act(b.dataset.k)));
let sx=0,sy=0,lx=0,moved=false;const w=$('#wrap');
w.addEventListener('touchstart',e=>{sx=lx=e.touches[0].clientX;sy=e.touches[0].clientY;moved=false},{passive:true});
w.addEventListener('touchmove',e=>{e.preventDefault();const x=e.touches[0].clientX,step=w.clientWidth/W*1.2;while(x-lx>step){act('right');lx+=step;moved=true}while(lx-x>step){act('left');lx-=step;moved=true}},{passive:false});
w.addEventListener('touchend',e=>{const t=e.changedTouches[0],dx=t.clientX-sx,dy=t.clientY-sy;if(!moved&&Math.abs(dx)<14&&Math.abs(dy)<14){if(g.over||g.paused)act('drop');else act('rot')}else if(dy>70&&dy>Math.abs(dx)*1.5)act('drop')},{passive:true});
window.TT={newGame,collide,rotate,tryMove,tryRotate,lock,tick,hardDrop,softDrop,speed,state:()=>g,SHAPES};
loadBest();start();
</script></body></html>"""


def register(api):
    global _api
    _api = api

    def punkte(req):
        if req.method == 'POST':
            d = req.json if isinstance(req.json, dict) else {}
            try:
                wert = int(d.get('wert'))
            except (TypeError, ValueError):
                return ({'error': 'Wert fehlt'}, 400)
            if wert < 0 or wert > 100_000_000:
                return ({'error': 'Ungültiger Wert'}, 400)
            with _lock:
                b = api.get('rekorde', {})
                b = b if isinstance(b, dict) else {}
                if wert > b.get('tetris', -1):
                    b['tetris'] = wert
                    api.set('rekorde', b)
                return b
        b = api.get('rekorde', {})
        return b if isinstance(b, dict) else {}

    def widget():
        b = punkte(type('R', (), {'method': 'GET', 'json': {}})())
        return {'icon': '🧱', 'text': 'Tetris', 'sub': ('Rekord: %d Punkte' % b['tetris']) if 'tetris' in b else 'Noch kein Rekord - los geht’s!'}

    api.route('index', lambda req: PAGE)
    api.route('punkte', punkte)
    api.widget('Tetris', widget, ttl=60, icon='🧱')
