# -*- coding: utf-8 -*-
# Pac-Man
# IT('s) Possible 
# 2026.11.08
"""Pac-Man: 20 abwechslungsreiche Level, Tunnel mit Wrap-around, vier+ Geister mit eigener Taktik."""

EXT_ID = 'pacman'
EXT_NAME = 'Pac-Man'
EXT_DESCRIPTION = 'Pac-Man mit 20 verschiedenen Leveln, Tunneln, Dunkel-Leveln und bis zu 6 Geistern. Pfeiltasten/WASD, Wischen oder Bildschirm-Kreuz.'
EXT_LINKS = [('Pac-Man spielen', 'index')]
EXT_SETTINGS = []


def register(api):
    api.route('index', lambda req: PAGE)
    api.widget('Pac-Man', lambda: {'text': 'Pac-Man', 'sub': '20 Level', 'icon': '👾'}, ttl=3600, icon='👾')


def on_load():
    pass


PAGE = r"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>Pac-Man</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;-webkit-user-select:none;user-select:none;-webkit-tap-highlight-color:transparent}
html,body{height:100%;background:#05060d;color:#f3f4fa;font-family:system-ui,sans-serif;overflow:hidden}
#app{height:100dvh;display:flex;flex-direction:column;align-items:center}
#hud{width:100%;padding-right:64px!important;display:flex;gap:10px;justify-content:space-between;align-items:center;padding:6px 10px;font-size:14px;font-weight:700;background:#0d1020;border-bottom:1px solid #263050;flex-wrap:wrap}
#hud span b{color:#ffd400}
#hud button{background:#222a3b;color:#fff;border:1px solid #30394e;border-radius:8px;padding:5px 10px;font-size:13px;cursor:pointer}
#main{flex:1;min-height:0;width:100%;display:flex;flex-direction:column;align-items:stretch}
#stage{flex:1;min-height:0;min-width:0;width:100%;display:flex;align-items:center;justify-content:center;position:relative}
canvas{display:block;background:#000;border-radius:6px}
#pad{align-self:center;display:none;grid-template-columns:repeat(3,56px);grid-template-rows:repeat(2,50px);gap:4px;padding:6px 0 10px}
#pad button{background:#222a3b;color:#fff;border:1px solid #3a4666;border-radius:10px;font-size:22px}
#pad .u{grid-column:2;grid-row:1}#pad .l{grid-column:1;grid-row:2}#pad .d{grid-column:2;grid-row:2}#pad .r{grid-column:3;grid-row:2}
@media (pointer:coarse){#pad{display:grid}}
@media (orientation:landscape){#main{flex-direction:row}#stage{width:auto}#pad{padding:0 18px;align-self:center;grid-template-columns:repeat(3,70px);grid-template-rows:repeat(2,70px);gap:6px}#pad button{font-size:28px}}
#ov{position:absolute;inset:0;background:rgba(5,6,13,.9);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;padding:12px;text-align:center;overflow:auto}
#ov h1{font-size:30px;color:#ffd400;letter-spacing:1px}
#ov p{color:#9da6b7;font-size:14px;max-width:520px}
#lv{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;max-width:560px;width:100%}
#lv button{background:#1a1f2c;color:#fff;border:2px solid #30394e;border-radius:10px;padding:6px 2px;font-size:11px;cursor:pointer;line-height:1.25}
#lv button b{display:block;font-size:16px;color:#ffd400}
#lv button.sel{border-color:#ffd400}
#lv button:disabled{opacity:.35;cursor:default}
.go{background:#e50914;color:#fff;border:0;border-radius:22px;padding:11px 30px;font-size:16px;font-weight:800;cursor:pointer}
label{font-size:13px;color:#9da6b7}
</style></head><body>
<div id="app">
 <div id="hud"><span>Level <b id="hl">1</b> <small id="hn"></small></span><span>Punkte <b id="hs">0</b></span><span>Leben <b id="hv">3</b></span><span>Rekord <b id="hh">0</b></span><span><button id="bp">Pause</button> <button id="bm">Menü</button></span></div>
 <div id="main"><div id="stage"><canvas id="cv"></canvas>
  <div id="ov"><h1 id="ot">PAC-MAN</h1><p id="om"></p><div id="lv"></div><label id="lal"><input type="checkbox" id="ca"> Alle 20 Level freischalten</label><button class="go" id="gb">Start</button></div>
 </div>
 <div id="pad"><button class="u" data-d="0">▲</button><button class="l" data-d="1">◀</button><button class="d" data-d="2">▼</button><button class="r" data-d="3">▶</button></div>
</div></div>
<script>
(()=>{"use strict";
const W=19,H=21,DIRS=[[0,-1],[-1,0],[0,1],[1,0]],PS=7.2;
// name, hue, braid, tunnel rows, ghosts, ghost speed, fright s, dark, power pellets
const CFG=[
['Anfang',220,.12,[9],3,.70,9,0,4],['Irrgarten',280,.04,[9],3,.74,8,0,4],['Doppeltunnel',160,.15,[5,15],4,.76,8,0,4],
['Nachtschicht',200,.10,[9],3,.76,8,1,4],['Tempo',30,.12,[3,9],4,.86,7,0,4],['Rudel',340,.12,[9],5,.78,7,0,6],
['Labyrinth',120,.00,[9],4,.80,7,0,4],['Offene Halle',190,.45,[5,15],4,.82,6,0,6],['Dreifachtunnel',50,.15,[3,9,17],4,.84,6,0,4],
['Schattenreich',270,.10,[9],4,.86,6,1,4],['Neon',320,.20,[5,13],4,.88,5,0,6],['Spinnennetz',90,.30,[7,15],5,.88,5,0,4],
['Blitzjagd',10,.12,[9],4,.95,5,0,6],['Gruselkeller',140,.06,[9],5,.88,4,1,4],['Geisterbahn',250,.25,[3,17],6,.88,4,0,6],
['Eisschloss',180,.10,[5,9,15],4,.92,3,0,4],['Wüste',40,.35,[9],5,.93,3,0,6],['Vulkan',0,.05,[7,13],5,.94,3,0,4],
['Finsternis',300,.15,[9],6,.94,2,1,4],['Finale',55,.18,[3,9,17],6,.96,2,1,6]
].map((a,i)=>({n:i+1,name:a[0],hue:a[1],braid:a[2],tun:a[3],gh:a[4],gs:a[5],fright:a[6],dark:!!a[7],pw:a[8],seed:101+(i+1)*7919}));
function rng(s){s>>>=0;return()=>{s=(s+0x6D2B79F5)>>>0;let t=s;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return((t^t>>>14)>>>0)/4294967296}}
function mkMaze(c){
 const R=rng(c.seed),g=Array.from({length:H},()=>Array(W).fill(1));
 const ex=(x,y)=>x>=3&&x<=4&&y>=4&&y<=5,vis=new Set(['0,0']);g[1][1]=0;
 const st=[[0,0]];
 while(st.length){const[cx,cy]=st[st.length-1],nb=[];
  for(const[dx,dy]of DIRS){const nx=cx+dx,ny=cy+dy;if(nx<0||nx>4||ny<0||ny>9||ex(nx,ny)||vis.has(nx+','+ny))continue;nb.push([nx,ny])}
  if(!nb.length){st.pop();continue}
  const[nx,ny]=nb[Math.floor(R()*nb.length)];vis.add(nx+','+ny);g[2*ny+1][2*nx+1]=0;g[cy+ny+1][cx+nx+1]=0;st.push([nx,ny])}
 for(let y=0;y<H;y++)for(let x=0;x<=9;x++)g[y][W-1-x]=g[y][x];
 const op=(x,y)=>{g[y][x]=0;g[y][W-1-x]=0};
 for(let y=1;y<H-1;y++)for(let x=1;x<=9;x++){
  if(!g[y][x]||(x%2)===(y%2))continue;
  const a=x%2?[x,y-1]:[x-1,y],b=x%2?[x,y+1]:[x+1,y];
  if(!g[a[1]][a[0]]&&!g[b[1]][b[0]]&&R()<c.braid)op(x,y)}
 for(let pass=0;pass<3;pass++)for(let cy=0;cy<10;cy++)for(let cx=0;cx<=4;cx++){
  const x=2*cx+1,y=2*cy+1;if(g[y][x])continue;let open=0;const cand=[];
  for(const[dx,dy]of DIRS){const wx=x+dx,wy=y+dy,fx=x+2*dx,fy=y+2*dy;
   if(!g[wy][wx])open++;else if(fx>=1&&fx<=W-2&&fy>=1&&fy<=H-2&&!g[fy][fx])cand.push([wx,wy])}
  if(open<2&&cand.length){const[wx,wy]=cand[Math.floor(R()*cand.length)];op(wx,wy)}}
 for(const ty of c.tun)for(let x=0;x<=2;x++)op(x,ty);
 for(let y=8;y<=12;y++)for(let x=7;x<=11;x++)g[y][x]=1;
 for(let y=9;y<=11;y++)for(let x=8;x<=10;x++)g[y][x]=0;
 g[8][9]=2;return g}
function mkPellets(g,c){
 const p=Array.from({length:H},()=>Array(W).fill(0));let n=0;
 for(let y=0;y<H;y++)for(let x=1;x<W-1;x++){if(g[y][x]!==0)continue;if(x>=8&&x<=10&&y>=9&&y<=11)continue;p[y][x]=1}
 p[15][9]=0;
 const pw=[[1,1],[17,1],[1,19],[17,19]];if(c.pw>=6)pw.push([1,9],[17,9]);
 for(const[x,y]of pw)p[y][x]=2;
 for(let y=0;y<H;y++)for(let x=0;x<W;x++)if(p[y][x])n++;
 return{p,n}}
// ---------- Zustand
let G=null;const cv=document.getElementById('cv'),cx=cv.getContext('2d');
const $=id=>document.getElementById(id);
let hi=0,unlocked=1,allOn=false;
try{hi=+localStorage.getItem('pm_hi')||0;unlocked=+localStorage.getItem('pm_un')||1;allOn=localStorage.getItem('pm_all')==='1'}catch(e){}
const wx=x=>(x%W+W)%W;
const passPac=(x,y)=>y>=0&&y<H&&G.g[y][wx(x)]===0;
const passGh=(x,y,door)=>{if(y<0||y>=H)return false;const v=G.g[y][wx(x)];return v===0||(v===2&&door)};
const bfsC={};
function bfsMap(tx,ty,door){const k=tx+','+ty+','+(door?1:0);if(bfsC[G.lvl+k])return bfsC[G.lvl+k];
 const d=new Int16Array(W*H).fill(9999);if(!passGh(tx,ty,door)){return bfsC[G.lvl+k]=d}
 d[ty*W+tx]=0;const q=[[tx,ty]];
 for(let i=0;i<q.length;i++){const[x,y]=q[i];for(const[dx,dy]of DIRS){const nx=wx(x+dx),ny=y+dy;if(!passGh(nx,ny,door)||d[ny*W+nx]<9999)continue;d[ny*W+nx]=d[y*W+x]+1;q.push([nx,ny])}}
 return bfsC[G.lvl+k]=d}
function newActors(){
 G.pac={tx:9,ty:15,dx:0,dy:0,p:0,mv:false};G.want=null;
 const sp=[[9,7],[9,10],[8,10],[10,10],[8,9],[10,9]];G.ghosts=[];
 for(let i=0;i<G.c.gh;i++){const[x,y]=sp[i];G.ghosts.push({i,tx:x,ty:y,dx:i?0:-1,dy:0,p:0,mv:false,state:i?'house':'run',t:i*2.4,fr:0})}
 G.mode='scatter';G.mi=0;G.mt=7;G.combo=0}
const SCH=[7,20,7,20,5,20,5,1e9];
function startLevel(n){
 const c=CFG[n-1];G.lvl=n;G.c=c;G.g=mkMaze(c);const pp=mkPellets(G.g,c);G.p=pp.p;G.dots=pp.n;
 newActors();G.phase='ready';G.t=1.6;G.flash=0;hud();fit()}
function newGame(n){G={score:0,lives:3,extra:1,time:0,phase:'menu'};startLevel(n)}
function hud(){$('hl').textContent=G.lvl;$('hn').textContent=G.c?'· '+G.c.name:'';$('hs').textContent=G.score;$('hv').textContent='♥'.repeat(Math.max(0,G.lives));$('hh').textContent=Math.max(hi,G.score)}
function add(n){G.score+=n;if(G.score>=G.extra*10000){G.extra++;G.lives++}if(G.score>hi){hi=G.score;try{localStorage.setItem('pm_hi',hi)}catch(e){}}hud()}
function eat(x,y){const v=G.p[y][x];if(!v)return;G.p[y][x]=0;G.dots--;
 if(v===1)add(10);else{add(50);G.combo=0;for(const gh of G.ghosts)if(gh.state==='run'||gh.state==='leave'){gh.fr=G.c.fright;if(gh.mv){gh.tx=wx(gh.tx+gh.dx);gh.ty+=gh.dy;gh.dx=-gh.dx;gh.dy=-gh.dy;gh.p=1-gh.p}}}
 if(G.dots<=0){G.phase='clear';G.t=2}}
function movePac(dt){const a=G.pac;let rem=PS*dt;const w=G.want;
 if(a.mv&&w&&(a.dx||a.dy)&&w[0]===-a.dx&&w[1]===-a.dy){a.tx=wx(a.tx+a.dx);a.ty+=a.dy;a.dx=-a.dx;a.dy=-a.dy;a.p=1-a.p}
 while(rem>1e-9){
  if(!a.mv){const w2=G.want;
   if(w2&&passPac(a.tx+w2[0],a.ty+w2[1])){a.dx=w2[0];a.dy=w2[1]}
   else if(!(a.dx||a.dy)||!passPac(a.tx+a.dx,a.ty+a.dy)){a.dx=0;a.dy=0;break}
   a.mv=true;a.p=0}
  const need=1-a.p;
  if(rem>=need){rem-=need;a.tx=wx(a.tx+a.dx);a.ty+=a.dy;a.p=0;a.mv=false;eat(a.tx,a.ty);if(G.phase!=='play')break}
  else{a.p+=rem;rem=0}}}
function ahead(n){const a=G.pac;return[a.tx+a.dx*n,a.ty+a.dy*n]}
function ghostDecide(gh){
 if(gh.state==='eat'&&gh.tx===9&&gh.ty===10){gh.state='leave';gh.fr=0}
 if(gh.state==='leave'&&gh.tx===9&&gh.ty===7)gh.state='run';
 const door=gh.state==='leave'||gh.state==='eat',opts=[];
 for(const d of DIRS)if(passGh(gh.tx+d[0],gh.ty+d[1],door))opts.push(d);
 let o2=opts.filter(d=>!((gh.dx||gh.dy)&&d[0]===-gh.dx&&d[1]===-gh.dy));if(!o2.length)o2=opts;
 if(!o2.length){gh.dx=gh.dy=0;return}
 const best=(list,dm)=>{let b=null,bv=1e9;for(const d of list){const v=dm[(gh.ty+d[1])*W+wx(gh.tx+d[0])];if(v<bv){bv=v;b=d}}return b||list[0]};
 let pick;
 if(door){const T=gh.state==='eat'?[9,10]:[9,7];pick=best(opts,bfsMap(T[0],T[1],true))}
 else if(gh.fr>0||(gh.i>=4&&Math.random()<.5))pick=o2[Math.floor(Math.random()*o2.length)];
 else{
  const P=G.pac,corner=[[17,1],[1,1],[17,19],[1,19]][gh.i%4];let T;
  if(G.mode==='scatter')T=corner;
  else if(gh.i===1)T=ahead(4);
  else if(gh.i===2){const a=ahead(2),b=G.ghosts[0];T=[2*a[0]-b.tx,2*a[1]-b.ty]}
  else if(gh.i===3)T=Math.hypot(P.tx-gh.tx,P.ty-gh.ty)>6?[P.tx,P.ty]:corner;
  else T=[P.tx,P.ty];
  T=[Math.max(1,Math.min(W-2,Math.round(T[0]))),Math.max(1,Math.min(H-2,Math.round(T[1])))];
  if(G.g[T[1]][T[0]]!==0)T=[P.tx,P.ty];
  pick=best(o2,bfsMap(T[0],T[1],false))}
 gh.dx=pick[0];gh.dy=pick[1]}
function moveGhost(gh,dt){
 if(gh.state==='house'){gh.t-=dt;if(gh.t<=0)gh.state='leave';return}
 const tun=G.c.tun.includes(gh.ty)&&(gh.tx<=2||gh.tx>=W-3);
 let rem=PS*G.c.gs*(gh.state==='eat'?2.4:gh.fr>0?.55:tun?.55:1)*dt;
 while(rem>1e-9){
  if(!gh.mv){ghostDecide(gh);if(!(gh.dx||gh.dy))break;gh.mv=true;gh.p=0}
  const need=1-gh.p;
  if(rem>=need){rem-=need;gh.tx=wx(gh.tx+gh.dx);gh.ty+=gh.dy;gh.p=0;gh.mv=false}
  else{gh.p+=rem;rem=0}}}
const pos=a=>[wx(a.tx+a.dx*a.p*(a.mv?1:0)),a.ty+a.dy*a.p*(a.mv?1:0)];
function dist(a,b){const A=pos(a),B=pos(b);let dx=Math.abs(A[0]-B[0]);dx=Math.min(dx,W-dx);return Math.hypot(dx,A[1]-B[1])}
function play(dt){
 G.time+=dt;
 if(!G.ghosts.some(g=>g.fr>0)){G.mt-=dt;if(G.mt<=0){G.mi=Math.min(G.mi+1,SCH.length-1);G.mt=SCH[G.mi];G.mode=G.mi%2?'chase':'scatter';
  for(const gh of G.ghosts)if(gh.state==='run'&&gh.mv){gh.tx=wx(gh.tx+gh.dx);gh.ty+=gh.dy;gh.dx=-gh.dx;gh.dy=-gh.dy;gh.p=1-gh.p}}}
 movePac(dt);if(G.phase!=='play')return;
 for(const gh of G.ghosts){if(gh.fr>0)gh.fr=Math.max(0,gh.fr-dt);moveGhost(gh,dt);
  if(gh.state==='house'||gh.state==='eat')continue;
  if(dist(G.pac,gh)<.6){
   if(gh.fr>0){gh.state='eat';gh.fr=0;add(200*Math.pow(2,Math.min(G.combo,3)));G.combo++}
   else{G.phase='dead';G.t=1.5;return}}}}
function update(dt){
 if(!G)return;
 if(G.phase==='ready'){G.t-=dt;if(G.t<=0)G.phase='play'}
 else if(G.phase==='play')play(dt);
 else if(G.phase==='dead'){G.t-=dt;if(G.t<=0){G.lives--;hud();if(G.lives<=0)over('GAME OVER','Punkte: '+G.score);else{newActors();G.phase='ready';G.t=1.3}}}
 else if(G.phase==='clear'){G.t-=dt;G.flash+=dt;if(G.t<=0){
   if(G.lvl>=20){over('GEWONNEN!','Alle 20 Level geschafft – '+G.score+' Punkte.')}
   else{unlock(G.lvl+1);startLevel(G.lvl+1)}}}}
function unlock(n){if(n>unlocked){unlocked=n;try{localStorage.setItem('pm_un',n)}catch(e){}}}
// ---------- Zeichnen
let cs=20,dpr=1;
function fit(){const st=$('stage'),pad=getComputedStyle($('pad')).display!=='none'?$('pad').offsetHeight:0;
 const aw=st.clientWidth-8,ah=st.clientHeight-8;cs=Math.max(8,Math.floor(Math.min(aw/W,ah/H)));dpr=window.devicePixelRatio||1;
 cv.style.width=cs*W+'px';cv.style.height=cs*H+'px';cv.width=cs*W*dpr;cv.height=cs*H*dpr;cx.setTransform(dpr,0,0,dpr,0,0)}
const GC=['#ff3030','#ffb0e0','#30e0ff','#ffa030','#60ff70','#c070ff'];
function drawActorWrap(x,y,fn){fn(x,y);if(x<.6)fn(x+W,y);if(x>W-1.6)fn(x-W,y)}
function draw(){
 if(!G)return;const c=G.c,h=c.hue;cx.clearRect(0,0,cs*W,cs*H);cx.fillStyle='#000';cx.fillRect(0,0,cs*W,cs*H);
 const fl=G.phase==='clear'&&Math.floor(G.flash*6)%2===1;
 const wf=fl?'#fff':`hsl(${h},55%,14%)`,we=fl?'#fff':`hsl(${h},90%,58%)`;
 for(let y=0;y<H;y++)for(let x=0;x<W;x++){const v=G.g[y][x];
  if(v===1){cx.fillStyle=wf;cx.fillRect(x*cs,y*cs,cs,cs);cx.strokeStyle=we;cx.lineWidth=Math.max(1.5,cs/9);cx.beginPath();
   for(let k=0;k<4;k++){const nx=x+DIRS[k][0],ny=y+DIRS[k][1];const open=ny>=0&&ny<H&&nx>=0&&nx<W&&G.g[ny][nx]!==1;if(!open)continue;
    const X=x*cs,Y=y*cs,e=cx.lineWidth/2;
    if(k===0){cx.moveTo(X,Y+e);cx.lineTo(X+cs,Y+e)}else if(k===2){cx.moveTo(X,Y+cs-e);cx.lineTo(X+cs,Y+cs-e)}
    else if(k===1){cx.moveTo(X+e,Y);cx.lineTo(X+e,Y+cs)}else{cx.moveTo(X+cs-e,Y);cx.lineTo(X+cs-e,Y+cs)}}
   cx.stroke()}
  else if(v===2){cx.fillStyle='#ffb0e0';cx.fillRect(x*cs,y*cs+cs*.4,cs,cs*.2)}
  const p=G.p[y][x];
  if(p===1){cx.fillStyle='#ffe8b0';cx.beginPath();cx.arc((x+.5)*cs,(y+.5)*cs,cs*.11,0,7);cx.fill()}
  else if(p===2&&Math.floor(G.time*4)%2===0||p===2&&G.phase!=='play'){cx.fillStyle='#ffe8b0';cx.beginPath();cx.arc((x+.5)*cs,(y+.5)*cs,cs*.3,0,7);cx.fill()}}
 // Pac-Man
 const P=G.pac,pp=pos(P);let face=P.dx<0?Math.PI:P.dy<0?-Math.PI/2:P.dy>0?Math.PI/2:P.dx>0?0:(G.face||0);G.face=face;
 let mouth=.1+.28*Math.abs(Math.sin(G.time*14));if(G.phase==='dead'){mouth=Math.min(Math.PI,(1.5-G.t)*2.2)}
 if(!(P.dx||P.dy)&&G.phase!=='dead')mouth=.25;
 if(!(G.phase==='dead'&&G.t<.1))drawActorWrap(pp[0],pp[1],(x,y)=>{cx.fillStyle='#ffd400';cx.beginPath();cx.moveTo((x+.5)*cs,(y+.5)*cs);cx.arc((x+.5)*cs,(y+.5)*cs,cs*.46,face+mouth,face+Math.PI*2-mouth);cx.closePath();cx.fill()});
 // Geister
 if(G.phase!=='dead')for(const gh of G.ghosts){const gp=pos(gh),eyes=gh.state==='eat',fr=gh.fr>0;
  const col=eyes?null:fr?(gh.fr<2&&Math.floor(G.time*6)%2?'#fff':'#2040ff'):GC[gh.i%6];
  drawActorWrap(gp[0],gp[1],(x,y)=>{const X=(x+.5)*cs,Y=(y+.5)*cs,r=cs*.44;
   if(col){cx.fillStyle=col;cx.beginPath();cx.arc(X,Y-r*.1,r,Math.PI,0);cx.lineTo(X+r,Y+r);
    for(let k=0;k<3;k++){cx.lineTo(X+r-(k*2+1)*r/3,Y+r*.6);cx.lineTo(X+r-(k+1)*2*r/3,Y+r)}cx.closePath();cx.fill()}
   cx.fillStyle='#fff';for(const s of[-1,1]){cx.beginPath();cx.arc(X+s*r*.38,Y-r*.2,r*.26,0,7);cx.fill()}
   cx.fillStyle=fr?'#c00':'#1030c0';for(const s of[-1,1]){cx.beginPath();cx.arc(X+s*r*.38+gh.dx*r*.12,Y-r*.2+gh.dy*r*.12,r*.12,0,7);cx.fill()}})}
 // Dunkel
 if(c.dark&&G.phase!=='clear'){const X=(pp[0]+.5)*cs,Y=(pp[1]+.5)*cs,gr=cx.createRadialGradient(X,Y,cs*1.2,X,Y,cs*4.2);
  gr.addColorStop(0,'rgba(0,0,0,0)');gr.addColorStop(1,'rgba(0,0,0,.97)');cx.fillStyle=gr;cx.fillRect(0,0,cs*W,cs*H)}
 if(G.phase==='ready'||G.phase==='clear'){cx.fillStyle=G.phase==='ready'?'#ffd400':'#fff';cx.font='bold '+Math.floor(cs*1.1)+'px system-ui';cx.textAlign='center';
  cx.fillText(G.phase==='ready'?'Level '+G.lvl+' – '+c.name:'Geschafft!',cs*W/2,cs*12.9);
  if(G.phase==='ready'&&c.dark){cx.font='bold '+Math.floor(cs*.8)+'px system-ui';cx.fillText('Dunkles Level',cs*W/2,cs*14.2)}}
 if(G.phase==='pause'){cx.fillStyle='rgba(0,0,0,.6)';cx.fillRect(0,0,cs*W,cs*H);cx.fillStyle='#fff';cx.font='bold '+cs*1.6+'px system-ui';cx.textAlign='center';cx.fillText('PAUSE',cs*W/2,cs*H/2)}}
// ---------- Menü
let sel=1;
function buildMenu(){const lv=$('lv');lv.innerHTML='';
 CFG.forEach(c=>{const b=document.createElement('button'),ok=allOn||c.n<=unlocked;b.disabled=!ok;if(c.n===sel)b.className='sel';
  b.innerHTML='<b>'+c.n+'</b>'+c.name+(c.dark?' 🌑':'');b.onclick=()=>{sel=c.n;buildMenu()};lv.appendChild(b)});
 $('ca').checked=allOn}
function showMenu(title,msg,lv){$('ot').textContent=title;$('om').textContent=msg;$('lv').style.display=lv?'grid':'none';$('lal').style.display=lv?'':'none';$('gb').textContent=lv?'Level '+sel+' starten':'Zum Menü';$('ov').style.display='flex';if(lv)buildMenu();if(G&&G.phase==='play'){G.prev='play';G.phase='menu'}}
let ovMode='menu';
function menu(){ovMode='menu';if(sel>(allOn?20:unlocked))sel=1;showMenu('PAC-MAN','Tunnel verbinden links und rechts. Wähle ein Level – 20 Level, ab Level 4 auch dunkel.',true)}
function over(t,m){G.phase='over';ovMode='over';showMenu(t,m,false)}
$('gb').onclick=()=>{if(ovMode==='over'){menu();return}$('ov').style.display='none';newGame(sel);G.phase='ready'};
$('ca').onchange=e=>{allOn=e.target.checked;try{localStorage.setItem('pm_all',allOn?'1':'0')}catch(x){}buildMenu()};
$('bm').onclick=()=>{menu()};
function pause(){if(!G)return;if(G.phase==='play'||G.phase==='ready'){G.pp=G.phase;G.phase='pause'}else if(G.phase==='pause')G.phase=G.pp||'play'}
$('bp').onclick=pause;
// ---------- Eingabe
function setWant(d){if(d>=0)G&&(G.want=DIRS[d])}
addEventListener('keydown',e=>{const k=e.key;let d=-1;
 if(k==='ArrowUp'||k==='w'||k==='W')d=0;else if(k==='ArrowLeft'||k==='a'||k==='A')d=1;else if(k==='ArrowDown'||k==='s'||k==='S')d=2;else if(k==='ArrowRight'||k==='d'||k==='D')d=3;
 if(d>=0){e.preventDefault();setWant(d);return}
 if(k==='p'||k==='P'||k==='Escape'){e.preventDefault();pause();return}
 if(k==='Enter'||k===' '){e.preventDefault();if($('ov').style.display!=='none')$('gb').click();else pause()}});
document.querySelectorAll('#pad button').forEach(b=>b.addEventListener('pointerdown',e=>{e.preventDefault();setWant(+b.dataset.d)}));
let ts=null;
cv.addEventListener('touchstart',e=>{const t=e.touches[0];ts=[t.clientX,t.clientY]},{passive:true});
cv.addEventListener('touchmove',e=>{if(!ts)return;const t=e.touches[0],dx=t.clientX-ts[0],dy=t.clientY-ts[1];
 if(Math.hypot(dx,dy)>24){setWant(Math.abs(dx)>Math.abs(dy)?(dx<0?1:3):(dy<0?0:2));ts=[t.clientX,t.clientY]}e.preventDefault()},{passive:false});
addEventListener('resize',fit);
let last=0;
function loop(t){const dt=Math.min(.05,(t-last)/1000||0);last=t;if(G&&$('ov').style.display==='none'){let r=dt;while(r>0){const s=Math.min(.02,r);update(s);r-=s}}draw();requestAnimationFrame(loop)}
window.PM={W,H,CFG,mkMaze,mkPellets,get G(){return G},newGame,update,startLevel,menu};
newGame(1);G.phase='menu';menu();fit();requestAnimationFrame(loop);
})();
</script></body></html>
"""
