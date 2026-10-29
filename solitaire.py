# -*- coding: utf-8 -*-
"""Solitaire (Klondike): Karten-Patience für Fernbedienung und Touch - mit Rückgängig, Auto-Ablage und Bestwerten.

Öffnen: Erweiterungsliste -> Solitaire -> „Solitaire öffnen“.
Touch:          Stapel antippen = ziehen · Karte antippen = aufnehmen, dann Ziel antippen · dieselbe Karte nochmal = auf die Ablage
Fernbedienung:  Pfeile = Cursor · OK = ziehen / aufnehmen / ablegen · Hoch/Runter in einer Spalte = mehrere Karten wählen
                Zurück = Aufnahme abbrechen · Knopfzeile ganz oben: Rückgängig, Auto, Neu
Tastatur:       Z = rückgängig · A = Auto-Ablage · N = neues Spiel
In den Einstellungen: 1 oder 3 Karten ziehen. Nicht jedes Blatt ist lösbar - dafür gibt es „Neu“.
"""
import threading

EXT_ID = 'solitaire'
EXT_NAME = 'Solitaire'
EXT_DESCRIPTION = 'Klondike-Solitaire für Fernbedienung und Touch, mit Rückgängig und Bestwerten.'
EXT_LINKS = [('Solitaire öffnen', 'index')]
EXT_SETTINGS = [
    {'key': 'ziehen', 'label': 'Karten pro Zug vom Stapel', 'type': 'select', 'default': '1', 'options': [['1', 'Eine Karte (leichter)'], ['3', 'Drei Karten (klassisch)']]},
]
_api = None
_lock = threading.Lock()

PAGE = r"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no"><title>Solitaire</title>
<style>
:root{--bg:#0d2a1f;--fg:#e8f3ec;--mut:#8fb5a1;--card:#143a2b;--acc:#ffd54f}
*{box-sizing:border-box}html,body{height:100%;margin:0}
body{background:var(--bg);color:var(--fg);font:clamp(14px,2.4vmin,22px)/1.3 system-ui,sans-serif;display:flex;flex-direction:column;overflow:hidden;-webkit-user-select:none;user-select:none;overscroll-behavior:none}
#bar{display:flex;gap:8px;align-items:center;padding:6px 10px;flex:none;padding-right:64px}
#bar button{font:inherit;color:var(--fg);background:var(--card);border:3px solid transparent;border-radius:12px;padding:.35em .8em;cursor:pointer}
#bar button.f,#bar button:focus{outline:none;border-color:var(--acc)}
#info{margin-left:auto;color:var(--mut)}
#bar button{white-space:nowrap}@media (max-width:480px){#bar{gap:5px;padding-left:6px}#bar button{padding:.3em .5em}#info{font-size:.8em;white-space:nowrap}}
#cvw{position:relative;flex:1;min-height:0;touch-action:none}
canvas{position:absolute;inset:0;width:100%;height:100%;display:block}
#msg{position:absolute;inset:0;display:none;place-items:center;text-align:center;background:rgba(3,15,10,.82);padding:14px;font-size:1.3em}
#msg.on{display:grid}#msg small{display:block;color:var(--mut);margin-top:.5em}
#msg button{font:inherit;margin-top:1em;color:#0d2a1f;background:var(--acc);border:0;border-radius:12px;padding:.5em 1.2em}
</style></head><body>
<div id="bar"><button id="bu" data-a="undo">↶ Zurück</button><button id="ba" data-a="auto">⚡ Auto</button><button id="bn" data-a="new">🔄 Neu</button><span id="info"></span></div>
<div id="cvw"><canvas id="cv"></canvas><div id="msg"></div></div>
<script>
"use strict";
const $=(s)=>document.querySelector(s);
const SUIT='♠♣♥♦',RANK=['','A','2','3','4','5','6','7','8','9','10','J','Q','K'];
const red=(c)=>c.s>=2;
/* ---------- Spiellogik (rein, ohne Oberfläche) ---------- */
function mulberry(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}}
function deck(){const d=[];for(let s=0;s<4;s++)for(let r=1;r<=13;r++)d.push({r,s,up:false});return d}
function shuffle(d,rnd){for(let i=d.length-1;i>0;i--){const j=Math.floor(rnd()*(i+1));[d[i],d[j]]=[d[j],d[i]]}return d}
function deal(rnd,draw){const d=shuffle(deck(),rnd);const g={tab:[],found:[[],[],[],[]],stock:[],waste:[],draw:draw===3?3:1,moves:0,won:false};
  for(let i=0;i<7;i++){const p=[];for(let j=0;j<=i;j++){const c=d.pop();c.up=j===i;p.push(c)}g.tab.push(p)}g.stock=d;return g}
function canTab(c,p){if(!p.length)return c.r===13;const t=p[p.length-1];return t.up&&t.r===c.r+1&&red(t)!==red(c)}
function canFound(g,c){return g.found[c.s].length===c.r-1}
function cardsFrom(g,f){
  if(f.t==='waste')return g.waste.length?[g.waste[g.waste.length-1]]:null;
  if(f.t==='found'){const p=g.found[f.i];return p.length?[p[p.length-1]]:null}
  if(f.t==='tab'){const p=g.tab[f.i],k=f.k||1;if(!p||k<1||k>p.length)return null;const cs=p.slice(p.length-k);return cs.every((c)=>c.up)?cs:null}
  return null}
function legal(g,f,to){const cs=cardsFrom(g,f);if(!cs)return false;
  if(to.t==='found')return cs.length===1&&f.t!=='found'&&canFound(g,cs[0]);
  if(to.t==='tab'){if(f.t==='tab'&&f.i===to.i)return false;return canTab(cs[0],g.tab[to.i])}
  return false}
function doMove(g,f,to){if(!legal(g,f,to))return false;const cs=cardsFrom(g,f);
  if(f.t==='waste')g.waste.pop();else if(f.t==='found')g.found[f.i].pop();
  else{const p=g.tab[f.i];p.splice(p.length-cs.length,cs.length);if(p.length&&!p[p.length-1].up)p[p.length-1].up=true}
  if(to.t==='found')g.found[cs[0].s].push(cs[0]);else g.tab[to.i].push(...cs);
  g.moves++;g.won=g.found.every((p)=>p.length===13);return true}
function drawStock(g){
  if(g.stock.length){for(let n=0;n<g.draw&&g.stock.length;n++){const c=g.stock.pop();c.up=true;g.waste.push(c)}}
  else if(g.waste.length){while(g.waste.length){const c=g.waste.pop();c.up=false;g.stock.push(c)}}
  else return false;
  g.moves++;return true}
function autoOne(g){const src=[{t:'waste'}];for(let i=0;i<7;i++)src.push({t:'tab',i,k:1});
  for(const f of src){const cs=cardsFrom(g,f);if(cs&&canFound(g,cs[0])){doMove(g,f,{t:'found',i:cs[0].s});return true}}return false}
/* ---------- Oberfläche ---------- */
let g=null,hist=[],held=null,cur={row:1,col:0,k:1},t0=0,tEnd=0,cfgDraw=1,reported=false,seed=null,flash=0;
const cv=$('#cv'),x=cv.getContext('2d');let L={};
function maxK(i){const p=g.tab[i];let k=0;for(let j=p.length-1;j>=0&&p[j].up;j--)k++;return k}
function snap(){hist.push(JSON.stringify(g));if(hist.length>300)hist.shift()}
function newGame(sd,draw){seed=sd==null?Math.floor(Math.random()*4294967296):sd;g=deal(mulberry(seed),draw||cfgDraw);hist=[];held=null;cur={row:1,col:0,k:1};t0=0;tEnd=0;reported=false;$('#msg').classList.remove('on');layout();paint()}
function started(){if(!t0)t0=Date.now()}
function act(fn){snap();started();if(!fn()){hist.pop();flash=Date.now();paint();return false}held=null;after();return true}
function after(){if(g.won&&!tEnd){tEnd=Date.now();win()}paint()}
function undo(){if(!hist.length||g.won)return;const s=JSON.parse(hist.pop());g=s;held=null;paint()}
function autoAll(){snap();started();let n=0;while(autoOne(g)&&!g.won)n++;if(g.won)n++;if(!n){hist.pop();flash=Date.now()}held=null;after()}
function secs(){return t0?Math.floor(((tEnd||Date.now())-t0)/1000):0}
function fmt(s){return Math.floor(s/60)+':'+String(s%60).padStart(2,'0')}
async function win(){const s=secs();$('#msg').innerHTML='🎉 Gewonnen!<small>'+g.moves+' Züge · '+fmt(s)+'</small><button id="bw">Neues Spiel</button>';$('#msg').classList.add('on');$('#bw').onclick=()=>newGame();
  if(!reported){reported=true;try{await fetch('punkte',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({zuege:g.moves,sekunden:s})})}catch(e){}}}
/* Layout: alle Maße aus der Fensterbreite/-höhe */
function layout(){const r=$('#cvw').getBoundingClientRect(),dpr=window.devicePixelRatio||1;cv.width=Math.round(r.width*dpr);cv.height=Math.round(r.height*dpr);x.setTransform(dpr,0,0,dpr,0,0);
  const W=r.width,H=r.height;let ch=Math.min(W/7.9*1.4,H/3.9),cw=ch/1.4;const gap=cw*.12,tw=7*cw+6*gap,ox=(W-tw)/2,oy=Math.max(4,cw*.08);
  L={W,H,cw,ch,gap,ox,oy,ty:oy+ch+gap*1.5,colX:(i)=>ox+i*(cw+gap)}}
function offsets(p){const avail=L.H-L.ty-L.ch-4;let d=0,u=0;for(let i=0;i<p.length-1;i++)p[i].up?u++:d++;
  let dd=L.ch*.16,du=L.ch*.3;const need=d*dd+u*du;if(need>avail&&need>0){const f=Math.max(.35,avail/need);dd*=f;du*=f}
  const o=[];let y=0;for(let i=0;i<p.length;i++){o.push(y);y+=p[i].up?du:dd}return o}
/* Rechtecke aller Stellen, zum Zeichnen und für Berührungen */
function rects(){const R=[];R.push({t:'stock',x:L.colX(0),y:L.oy,w:L.cw,h:L.ch});R.push({t:'waste',x:L.colX(1),y:L.oy,w:L.cw,h:L.ch});
  for(let i=0;i<4;i++)R.push({t:'found',i,x:L.colX(3+i),y:L.oy,w:L.cw,h:L.ch});
  for(let i=0;i<7;i++){const p=g.tab[i],o=offsets(p);R.push({t:'tab',i,x:L.colX(i),y:L.ty,w:L.cw,h:p.length?o[p.length-1]+L.ch:L.ch,o});}
  return R}
function rr(px,py,w,h,r){x.beginPath();x.moveTo(px+r,py);x.arcTo(px+w,py,px+w,py+h,r);x.arcTo(px+w,py+h,px,py+h,r);x.arcTo(px,py+h,px,py,r);x.arcTo(px,py,px+w,py,r);x.closePath()}
function drawCard(c,px,py,sel){const w=L.cw,h=L.ch,r=w*.1;
  if(!c.up){rr(px,py,w,h,r);x.fillStyle='#1d4f8f';x.fill();x.strokeStyle='#0c2a52';x.lineWidth=2;x.stroke();rr(px+w*.1,py+w*.1,w*.8,h-w*.2,r*.6);x.strokeStyle='rgba(255,255,255,.35)';x.lineWidth=1.5;x.stroke();return}
  rr(px,py,w,h,r);x.fillStyle=sel?'#fff6c8':'#f6f4ee';x.fill();x.strokeStyle='#222';x.lineWidth=1.5;x.stroke();
  x.fillStyle=red(c)?'#c62828':'#1b1b1b';x.textBaseline='top';x.textAlign='left';x.font='bold '+Math.round(w*.3)+'px system-ui,sans-serif';
  x.fillText(RANK[c.r]+SUIT[c.s],px+w*.07,py+w*.05);
  x.textAlign='center';x.textBaseline='middle';x.font=Math.round(w*.55)+'px system-ui,sans-serif';x.fillText(SUIT[c.s],px+w/2,py+h*.62)}
function slot(px,py,label){rr(px,py,L.cw,L.ch,L.cw*.1);x.strokeStyle='rgba(255,255,255,.25)';x.lineWidth=2;x.stroke();if(label){x.fillStyle='rgba(255,255,255,.3)';x.textAlign='center';x.textBaseline='middle';x.font=Math.round(L.cw*.5)+'px system-ui,sans-serif';x.fillText(label,px+L.cw/2,py+L.ch/2)}}
function isHeld(f){return held&&held.t===f.t&&(held.i===undefined||held.i===f.i)}
function paint(){if(!g)return;x.clearRect(0,0,L.W,L.H);
  slot(L.colX(0),L.oy,g.waste.length?'↻':'');if(g.stock.length)drawCard({up:false},L.colX(0),L.oy);
  slot(L.colX(1),L.oy);if(g.waste.length){const n=Math.min(g.draw,g.waste.length);for(let j=0;j<n;j++){const c=g.waste[g.waste.length-n+j];const sh=(n>1?j*L.cw*.22:0);drawCard(c,L.colX(1)+sh,L.oy,held&&held.t==='waste'&&j===n-1)}}
  for(let i=0;i<4;i++){slot(L.colX(3+i),L.oy,SUIT[i]);const p=g.found[i];if(p.length)drawCard(p[p.length-1],L.colX(3+i),L.oy,held&&held.t==='found'&&held.i===i)}
  for(let i=0;i<7;i++){const p=g.tab[i],o=offsets(p);if(!p.length)slot(L.colX(i),L.ty,'K');
    p.forEach((c,j)=>{const sel=held&&held.t==='tab'&&held.i===i&&j>=p.length-held.k;drawCard(c,L.colX(i),L.ty+o[j]-(sel?L.ch*.06:0),sel)})}
  cursorBox();if(Date.now()-flash<400)setTimeout(paint,420);$('#info').textContent='Züge '+g.moves+' · '+fmt(secs())+(g.draw===3?' · 3er':'');
  document.querySelectorAll('#bar button').forEach((b)=>b.classList.remove('f'));if(cur.row===-1)document.querySelectorAll('#bar button')[cur.col].classList.add('f')}
function cursorBox(){if(cur.row===-1)return;let px,py,w=L.cw,h=L.ch;
  if(cur.row===0){px=L.colX(cur.col);py=L.oy}
  else{const p=g.tab[cur.col],o=offsets(p);px=L.colX(cur.col);const k=Math.min(cur.k,Math.max(1,p.length));if(p.length){const j=p.length-k;py=L.ty+o[j];h=o[p.length-1]-o[j]+L.ch}else py=L.ty}
  x.strokeStyle=Date.now()-flash<400?'#ff5252':'#ffd54f';x.lineWidth=4;rr(px-3,py-3,w+6,h+6,L.cw*.12);x.stroke()}
/* Bedienung */
function whereCursor(){if(cur.row===0){if(cur.col===0)return{t:'stock'};if(cur.col===1)return{t:'waste'};if(cur.col>=3)return{t:'found',i:cur.col-3};return null}return{t:'tab',i:cur.col}}
function okAt(pos,k){
  if(pos.t==='stock'){held=null;act(()=>drawStock(g));return}
  if(!held){
    if(pos.t==='waste'&&g.waste.length)held={t:'waste'};
    else if(pos.t==='found'&&g.found[pos.i].length)held={t:'found',i:pos.i};
    else if(pos.t==='tab'){const p=g.tab[pos.i];if(p.length){const kk=Math.min(k||1,maxK(pos.i));if(kk>=1)held={t:'tab',i:pos.i,k:kk}}}
    if(!held)flash=Date.now();paint();return}
  const f=held;const same=(f.t===pos.t&&(pos.i===undefined||f.i===pos.i));
  if(same){const cs=cardsFrom(g,f);if(cs&&cs.length===1&&f.t!=='found'&&canFound(g,cs[0])){act(()=>doMove(g,f,{t:'found',i:cs[0].s}));return}held=null;paint();return}
  if(pos.t==='waste'){held=null;paint();return}
  if(!act(()=>doMove(g,f,pos))){held=null;paint()}}
function key(e){const k=e.key;
  if(k==='z'||k==='Z'){undo();e.preventDefault();return}if(k==='a'||k==='A'){autoAll();e.preventDefault();return}if(k==='n'||k==='N'){newGame();e.preventDefault();return}
  if(k==='Escape'||k==='Backspace'){if(held){held=null;paint();e.preventDefault()}return}
  if(!g||(g.won&&$('#msg').classList.contains('on'))){if(k==='Enter'||k===' '){newGame();e.preventDefault()}return}
  if(k==='ArrowLeft'||k==='ArrowRight'){const d=k==='ArrowLeft'?-1:1;const n=cur.row===-1?3:7;let c=cur.col+d;if(cur.row===0&&c===2)c+=d;if(c<0||c>=n)return;cur.col=c;cur.k=1;paint();e.preventDefault();return}
  if(k==='ArrowUp'){if(cur.row===1){const m=maxK(cur.col);if(cur.k<m)cur.k++;else{cur.row=0;if(cur.col===2)cur.col=1}}else if(cur.row===0){cur.row=-1;cur.col=Math.min(cur.col,2)}paint();e.preventDefault();return}
  if(k==='ArrowDown'){if(cur.row===-1){cur.row=0;cur.col=Math.min(cur.col,6);if(cur.col===2)cur.col=3}else if(cur.row===0){cur.row=1;cur.k=1}else if(cur.k>1)cur.k--;paint();e.preventDefault();return}
  if(k==='Enter'||k===' '){e.preventDefault();if(cur.row===-1){press(['undo','auto','new'][cur.col]);return}okAt(whereCursor(),cur.k)}}
function press(a){if(a==='undo')undo();else if(a==='auto')autoAll();else if(a==='new')newGame()}
document.addEventListener('keydown',key);
document.querySelectorAll('#bar button').forEach((b)=>b.addEventListener('click',()=>press(b.dataset.a)));
cv.addEventListener('pointerdown',(e)=>{if(!g||(g.won&&$('#msg').classList.contains('on')))return;const r=cv.getBoundingClientRect(),px=e.clientX-r.left,py=e.clientY-r.top;
  const R=rects();for(let n=R.length-1;n>=0;n--){const s=R[n];if(px<s.x||px>s.x+s.w||py<s.y||py>s.y+s.h)continue;
    if(s.t==='tab'){const p=g.tab[s.i];let idx=-1;for(let j=p.length-1;j>=0;j--){const top=L.ty+s.o[j];const h=j===p.length-1?L.ch:s.o[j+1]-s.o[j];if(py>=top&&py<=top+h){idx=j;break}}
      const k=idx>=0&&p[idx].up?p.length-idx:0;
      if(held&&held.t==='tab'&&held.i===s.i&&k>=1&&k!==held.k){held.k=k;cur={row:1,col:s.i,k};paint()}
      else if(held){cur={row:1,col:s.i,k:1};okAt({t:'tab',i:s.i})}
      else if(k>=1){cur={row:1,col:s.i,k};okAt({t:'tab',i:s.i},k)}}
    else{cur=s.t==='stock'?{row:0,col:0,k:1}:s.t==='waste'?{row:0,col:1,k:1}:{row:0,col:3+s.i,k:1};okAt(s.t==='found'?{t:'found',i:s.i}:{t:s.t},1)}
    e.preventDefault();return}});
window.addEventListener('resize',()=>{layout();paint()});
setInterval(()=>{if(g&&t0&&!tEnd)$('#info').textContent='Züge '+g.moves+' · '+fmt(secs())+(g.draw===3?' · 3er':'')},1000);
async function boot(){try{const c=await (await fetch('konfig')).json();cfgDraw=c.ziehen===3?3:1}catch(e){}
  const q=new URLSearchParams(location.search);const sd=q.get('seed');layout();newGame(sd!==null&&sd!==''?+sd:null,q.get('draw')==='3'?3:cfgDraw)}
window.SOL={state:()=>g,cursor:()=>cur,held:()=>held,seed:()=>seed,deal,mulberry,canTab,canFound,legal,doMove,drawStock,autoOne,cardsFrom,newGame,rects:()=>rects(),layout:()=>L,hist:()=>hist.length};
boot();
</script></body></html>"""


def register(api):
    global _api
    _api = api

    def draw_n():
        return 3 if str(api.get('ziehen') or '1') == '3' else 1

    def punkte(req):
        if req.method == 'POST':
            d = req.json if isinstance(req.json, dict) else {}
            try:
                zuege, sek = int(d.get('zuege')), int(d.get('sekunden'))
            except (TypeError, ValueError):
                return ({'error': 'Werte fehlen'}, 400)
            if not (0 < zuege < 100000 and 0 <= sek < 10_000_000):
                return ({'error': 'Ungültige Werte'}, 400)
            with _lock:
                b = api.get('rekorde', {})
                b = b if isinstance(b, dict) else {}
                b['siege'] = int(b.get('siege', 0)) + 1
                if zuege < b.get('zuege', 10 ** 9):
                    b['zuege'] = zuege
                if sek < b.get('sekunden', 10 ** 9):
                    b['sekunden'] = sek
                api.set('rekorde', b)
                return b
        b = api.get('rekorde', {})
        return b if isinstance(b, dict) else {}

    def widget():
        b = punkte(type('R', (), {'method': 'GET', 'json': {}})())
        if not b.get('siege'):
            return {'icon': '🃏', 'text': 'Solitaire', 'sub': 'Noch kein Spiel gewonnen - los geht’s!'}
        s = b['sekunden']
        return {'icon': '🃏', 'text': 'Solitaire', 'sub': '%d gewonnen · Best: %d Züge, %d:%02d' % (b['siege'], b['zuege'], s // 60, s % 60)}

    api.route('index', lambda req: PAGE)
    api.route('konfig', lambda req: {'ziehen': draw_n()})
    api.route('punkte', punkte)
    api.widget('Solitaire', widget, ttl=60, icon='🃏')
