# -*- coding: utf-8 -*-
# Minigolf
# IT('s) Possible 
# 2026.11.08
"""Minigolf: 18 Bahnen in 3D-Perspektive, Joystick + ein Schlag-Knopf, Münzen, freischaltbare Bälle, Speicherstand.
Läuft komplett lokal (HTML5-Canvas, keine externen Dateien)."""

EXT_ID = 'minigolf'
EXT_NAME = 'Minigolf'
EXT_DESCRIPTION = 'Arcade-Minigolf mit 18 Bahnen: Windmühlen, Wasser, Brücken, Tunnel, Gefälle, Eis und Sand. Joystick zielt, Knopf halten = Kraft, loslassen = Schlag.'
EXT_LINKS = [('Minigolf spielen', 'index')]
EXT_SETTINGS = []


def register(api):
    api.route('index', lambda req: PAGE)
    api.widget('Minigolf', lambda: {'text': 'Minigolf', 'sub': '18 Bahnen', 'icon': '⛳'}, ttl=3600, icon='⛳')


def on_load():
    pass


PAGE = r"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>Minigolf</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;-webkit-user-select:none;user-select:none;-webkit-tap-highlight-color:transparent}
#joy,#pw,canvas,#hud{touch-action:none}
html,body{height:100%;background:#1b1530;color:#fff;font-family:"Trebuchet MS",system-ui,sans-serif;overflow:hidden}
#app{height:100dvh;display:flex;flex-direction:column}
#hud{display:flex;gap:8px;align-items:center;justify-content:space-between;padding:6px 66px 6px 8px;background:#2a2148;border-bottom:3px solid #120d26;flex-wrap:wrap;font-weight:800;font-size:14px;min-height:44px}
.chip{background:#fff;color:#2a2148;border-radius:14px;padding:3px 10px;border:2px solid #120d26;box-shadow:0 2px 0 #120d26;white-space:nowrap}
.chip b{color:#e8452c}
#hud button,.btn{background:#ffcf3a;color:#2a2148;border:3px solid #120d26;border-radius:16px;padding:6px 14px;font:800 15px "Trebuchet MS",system-ui,sans-serif;box-shadow:0 4px 0 #120d26;cursor:pointer}
.btn:active,#hud button:active{transform:translateY(3px);box-shadow:0 1px 0 #120d26}
.btn.big{font-size:19px;padding:10px 26px}.btn.alt{background:#7fe08a}.btn.red{background:#ff7a6a}.btn:disabled{opacity:.45;box-shadow:none}
#stage{flex:1;min-height:0;position:relative}
canvas{position:absolute;inset:0;width:100%;height:100%;display:block}
#joy{position:absolute;left:max(14px,env(safe-area-inset-left));bottom:14px;width:132px;height:132px;border-radius:50%;background:rgba(255,255,255,.22);border:4px solid rgba(255,255,255,.7);display:none}
#knob{position:absolute;left:38px;top:38px;width:56px;height:56px;border-radius:50%;background:#ffcf3a;border:4px solid #120d26;box-shadow:0 3px 0 #120d26}
#pw{position:absolute;right:max(14px,env(safe-area-inset-right));bottom:14px;width:132px;height:132px;border-radius:50%;background:#ff5a4a;border:5px solid #120d26;box-shadow:0 6px 0 #120d26;display:none;font:900 20px "Trebuchet MS",system-ui;align-items:center;justify-content:center;text-align:center;overflow:hidden}
#pw i{position:absolute;left:0;right:0;bottom:0;height:0;background:#ffe24a;opacity:.85}
#pw span{position:relative;z-index:2;text-shadow:0 2px 0 #120d26}
#ov{position:absolute;inset:0;background:rgba(18,13,38,.84);display:none;flex-direction:column;align-items:center;justify-content:center;gap:10px;padding:12px;text-align:center;overflow:auto;z-index:5}
#ov h1{font-size:34px;color:#ffcf3a;text-shadow:0 4px 0 #120d26;letter-spacing:1px}
#ov h2{font-size:24px;color:#ffcf3a;text-shadow:0 3px 0 #120d26}
#ov p{color:#d8d0f0;font-size:15px;max-width:520px}
.row{display:flex;gap:10px;flex-wrap:wrap;justify-content:center}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(92px,1fr));gap:7px;max-width:640px;width:100%}
.cell{background:#fff;color:#2a2148;border:3px solid #120d26;border-radius:12px;padding:5px 2px;font-weight:800;font-size:12px;cursor:pointer;line-height:1.2}
.cell b{display:block;font-size:17px}.cell.lock{opacity:.5}
.skins{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;max-width:520px;width:100%}
.skin{background:#fff;color:#2a2148;border:3px solid #120d26;border-radius:14px;padding:6px 2px;font-weight:800;font-size:12px;cursor:pointer}
.skin.sel{outline:4px solid #ffcf3a}.skin canvas{position:static;width:44px;height:44px;margin:0 auto 2px}
.card{background:#fff;color:#2a2148;border:4px solid #120d26;border-radius:20px;padding:14px 22px;box-shadow:0 6px 0 #120d26;min-width:260px}
.card .big{font-size:36px;font-weight:900;color:#e8452c}
table.sc{border-collapse:collapse;margin:8px auto;font-size:12px}table.sc td{border:1px solid #2a2148;padding:2px 5px;min-width:24px}
@media (orientation:landscape) and (max-height:520px){#ov h1{font-size:26px}#joy,#pw{width:118px;height:118px}#knob{left:31px;top:31px}}
</style></head><body>
<div id="app">
 <div id="hud"><span class="chip" id="hh">Bahn <b>1</b>/18</span><span class="chip" id="hp">Par <b>3</b></span><span class="chip" id="hs">Schläge <b>0</b></span><span class="chip" id="ht">Gesamt <b>0</b></span><span class="chip" id="hc">🪙 <b>0</b></span><button id="bm">Menü</button></div>
 <div id="stage"><canvas id="cv"></canvas>
  <div id="joy"><div id="knob"></div></div>
  <div id="pw"><i></i><span>SCHLAG<br><small>halten</small></span></div>
  <div id="ov"></div>
 </div>
</div>
<script>
(()=>{"use strict";
const TAU=Math.PI*2,BR=5,DT=1/120,TILT=.66,hyp=Math.hypot,$=id=>document.getElementById(id);
const cv=$('cv'),cx=cv.getContext('2d');
/* ---------------- Geometrie ---------------- */
function inPoly(p,x,y){let c=false;for(let i=0,j=p.length-2;i<p.length;j=i,i+=2){const xi=p[i],yi=p[i+1],xj=p[j],yj=p[j+1];if((yi>y)!==(yj>y)&&x<(xj-xi)*(y-yi)/(yj-yi)+xi)c=!c}return c}
function segNear(px,py,x1,y1,x2,y2){const dx=x2-x1,dy=y2-y1,l=dx*dx+dy*dy;let t=l?((px-x1)*dx+(py-y1)*dy)/l:0;t=t<0?0:t>1?1:t;const qx=x1+dx*t,qy=y1+dy*t;return[qx,qy,hyp(px-qx,py-qy)]}
const rp=(x,y,w,h)=>[x,y,x+w,y,x+w,y+h,x,y+h];
function ribbon(pts,w){const n=pts.length,L=[],R=[],h=w/2,nr=(a,b)=>{const dx=b[0]-a[0],dy=b[1]-a[1],l=hyp(dx,dy);return[-dy/l,dx/l]};
 for(let i=0;i<n;i++){let m;if(i===0)m=nr(pts[0],pts[1]),m=[m[0]*h,m[1]*h];else if(i===n-1)m=nr(pts[n-2],pts[n-1]),m=[m[0]*h,m[1]*h];
  else{const a=nr(pts[i-1],pts[i]),b=nr(pts[i],pts[i+1]),k=h/(1+a[0]*b[0]+a[1]*b[1]);m=[(a[0]+b[0])*k,(a[1]+b[1])*k]}
  L.push(pts[i][0]+m[0],pts[i][1]+m[1]);R.unshift(pts[i][0]-m[0],pts[i][1]-m[1])}
 return L.concat(R)}
function oct(x,y,r,n){const o=[];for(let i=0;i<n;i++){const a=TAU*(i+.5)/n;o.push(x+Math.cos(a)*r,y+Math.sin(a)*r)}return o}
function rectPts(r){const[x,y,w,h,a]=r;if(!a)return[[x,y],[x+w,y],[x+w,y+h],[x,y+h]];const cx_=x+w/2,cy_=y+h/2,c=Math.cos(a),s=Math.sin(a);
 return[[-w/2,-h/2],[w/2,-h/2],[w/2,h/2],[-w/2,h/2]].map(([u,v])=>[cx_+u*c-v*s,cy_+u*s+v*c])}
/* ---------------- Bahnen (Welt 400x400, y nach unten = zum Betrachter) ---------------- */
const HOLES=[
{n:'Gerade aus',par:2,tee:[200,330],cup:[200,80],poly:rp(150,40,100,320)},
{n:'Der Knick',par:3,tee:[100,320],cup:[300,100],poly:ribbon([[80,320],[300,320],[300,80]],80),zones:[{k:'sand',t:'e',x:300,y:205,rx:30,ry:20}]},
{n:'Teichbrücke',par:3,tee:[200,340],cup:[200,70],poly:rp(110,30,180,340),zones:[{k:'water',t:'r',x:110,y:150,w:180,h:100},{k:'bridge',t:'r',x:185,y:140,w:30,h:120}]},
{n:'Kleine Mühle',par:3,tee:[200,340],cup:[200,60],poly:rp(130,30,140,340),mills:[{x:200,y:200,len:60,w:1.3,arms:2}]},
{n:'Sandkasten',par:3,tee:[200,330],cup:[200,80],poly:rp(60,40,280,320),zones:[{k:'sand',t:'e',x:200,y:200,rx:80,ry:55}],bumpers:[[130,120,14],[270,120,14]]},
{n:'Schiefe Ebene',par:3,tee:[110,330],cup:[110,70],poly:rp(60,40,280,320),zones:[{k:'water',t:'r',x:270,y:120,w:70,h:160},{k:'slope',t:'r',x:60,y:120,w:280,h:160,ax:80,ay:0}],blocks:[[175,300,60,12]]},
{n:'Pilzring',par:3,tee:[200,320],cup:[200,80],poly:oct(200,200,160,8),bumpers:[[200,200,44]]},
{n:'Tunnelblick',par:3,tee:[200,335],cup:[200,70],poly:rp(100,40,200,320),blocks:[[100,192,200,16]],portals:[{a:[150,260],b:[250,150],dir:[-.53,-.85]}]},
{n:'Zickzack',par:4,tee:[200,340],cup:[200,75],poly:rp(70,40,260,320),blocks:[[70,296,200,14],[130,206,200,14],[70,116,200,14]]},
{n:'Sumpfbrücken',par:4,tee:[200,340],cup:[200,60],poly:rp(70,30,260,340),zones:[{k:'water',t:'r',x:70,y:100,w:260,h:70},{k:'water',t:'r',x:70,y:230,w:260,h:70},{k:'bridge',t:'r',x:250,y:222,w:30,h:86},{k:'bridge',t:'r',x:120,y:92,w:30,h:86}]},
{n:'Pendeluhr',par:3,tee:[200,340],cup:[200,60],poly:rp(140,30,120,340),swings:[{px:140,py:150,len:100,base:0,amp:1.0,w:2,ph:0},{px:260,py:260,len:100,base:Math.PI,amp:1.0,w:2,ph:1.6}]},
{n:'Eisbahn',par:4,tee:[200,320],cup:[200,80],poly:rp(60,50,280,300),zones:[{k:'ice',t:'r',x:60,y:50,w:280,h:300}],bumpers:[[140,200,16],[260,200,16],[200,130,16]]},
{n:'Die Schlange',par:4,tee:[110,330],cup:[300,110],poly:ribbon([[90,330],[310,330],[310,220],[90,220],[90,110],[310,110]],64),sliders:[{w:12,h:34,ax:130,ay:220,bx:270,by:220,T:3.6}]},
{n:'Spielzeugbrücke',par:4,tee:[110,335],cup:[110,70],poly:rp(60,40,280,320),zones:[{k:'water',t:'r',x:60,y:170,w:280,h:70},{k:'bridge',t:'r',x:270,y:162,w:30,h:86}],sliders:[{w:46,h:12,ax:90,ay:110,bx:290,by:110,T:3.2}],blocks:[[160,290,50,50]]},
{n:'Doppelmühle',par:4,tee:[200,340],cup:[150,65],poly:rp(70,30,260,340),mills:[{x:145,y:250,len:56,w:1.5,arms:4},{x:255,y:130,len:56,w:-1.8,arms:4}],zones:[{k:'sand',t:'e',x:300,y:300,rx:28,ry:22},{k:'sand',t:'e',x:100,y:95,rx:26,ry:20}]},
{n:'Rutschbahn',par:3,tee:[200,340],cup:[200,60],poly:rp(130,30,140,340),zones:[{k:'water',t:'r',x:130,y:120,w:60,h:100},{k:'slope',t:'r',x:130,y:120,w:140,h:100,ax:-100,ay:0},{k:'boost',t:'r',x:150,y:270,w:100,h:30,dx:0,dy:-1}]},
{n:'Röhrenlabyrinth',par:3,tee:[200,335],cup:[110,85],poly:rp(70,40,260,320),blocks:[[70,236,260,14],[70,126,260,14]],portals:[{a:[130,290],b:[290,190],dir:[-.97,.24]},{a:[110,185],b:[290,80],dir:[-1,0]}]},
{n:'Das Schloss',par:5,tee:[200,355],cup:[200,90],poly:rp(50,20,300,360),zones:[{k:'water',t:'r',x:120,y:40,w:160,h:120},{k:'land',t:'r',x:145,y:55,w:110,h:80},{k:'bridge',t:'r',x:185,y:128,w:30,h:44}],mills:[{x:200,y:250,len:50,w:1.4,arms:2}],sliders:[{w:60,h:12,ax:90,ay:310,bx:310,by:310,T:3.4}],bumpers:[[90,190,14],[310,190,14]]}
];
const THEMES=[
{name:'Sonnenwiese',sky:['#6fcbff','#e8f9ff'],plate:'#66c352',plate2:'#74cf60',slab:'#8a5a34',fw:'#4fd163',fw2:'#63df76',wt:'#fff8e8',wf:'#dccdb0',ws:'#c9b894'},
{name:'Zauberwald',sky:['#74609c','#cdb3e4'],plate:'#4f9eea',plate2:'#5aaaf5',slab:'#5a3a82',fw:'#f0c488',fw2:'#f9d9a8',wt:'#ffffff',wf:'#ead9c2',ws:'#d3bea5'},
{name:'Spielzimmer',sky:['#ee9356','#ffdca4'],plate:'#8a3dc6',plate2:'#9648d2',slab:'#5c2090',fw:'#3fd953',fw2:'#55e668',wt:'#3ccb4d',wf:'#1f9132',ws:'#17782a'}];
const SKINS=[
{n:'Klassik',cost:0,c1:'#ffffff',c2:'#c9c9d6',p:'plain'},
{n:'Tomate',cost:30,c1:'#ff7060',c2:'#b92418',p:'plain'},
{n:'Zitrone',cost:30,c1:'#ffec6a',c2:'#d9a600',p:'plain'},
{n:'Himmel',cost:50,c1:'#ffffff',c2:'#9bbcd9',p:'stripe',pc:'#2f8cff'},
{n:'Bonbon',cost:70,c1:'#ffb6dd',c2:'#d86aa6',p:'dots',pc:'#ffffff'},
{n:'Stern',cost:90,c1:'#8d6bff',c2:'#4326b3',p:'star',pc:'#ffe24a'},
{n:'Minze',cost:110,c1:'#aaf5e0',c2:'#35b79a',p:'check',pc:'#ffffff'},
{n:'Feuer',cost:150,c1:'#ffd23a',c2:'#e8301a',p:'stripe',pc:'#ff5a1a'},
{n:'Regenbogen',cost:200,c1:'#ffffff',c2:'#bbbbbb',p:'rainbow'},
{n:'Gold',cost:300,c1:'#fff2a0',c2:'#c28a00',p:'gold'}];
/* ---------------- Bahn aufbauen ---------------- */
function rng(s){s>>>=0;return()=>{s=(s+0x6D2B79F5)>>>0;let t=s;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return((t^t>>>14)>>>0)/4294967296}}
function zin(z,x,y){return z.t==='r'?(x>=z.x&&x<=z.x+z.w&&y>=z.y&&y<=z.y+z.h):(((x-z.x)/z.rx)**2+((y-z.y)/z.ry)**2<=1)}
let L=null;
function buildLevel(i){
 const d=HOLES[i],th=THEMES[Math.floor(i/6)],poly=d.poly,R=rng(777+i*131);
 const o={i,d,th,poly,tee:d.tee,cup:d.cup,segs:[],circ:[],pieces:[],zones:(d.zones||[]).slice(),mills:d.mills||[],swings:d.swings||[],sliders:d.sliders||[],portals:d.portals||[],coins:[],decor:[]};
 let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;
 for(let k=0;k<poly.length;k+=2){x0=Math.min(x0,poly[k]);x1=Math.max(x1,poly[k]);y0=Math.min(y0,poly[k+1]);y1=Math.max(y1,poly[k+1])}
 o.plate=[x0-34,y0-34,x1+34,y1+34];
 const T=7;
 for(let k=0;k<poly.length;k+=2){
  const ax=poly[k],ay=poly[k+1],bx=poly[(k+2)%poly.length],by=poly[(k+3)%poly.length],len=hyp(bx-ax,by-ay);if(len<.01)continue;
  const ux=(bx-ax)/len,uy=(by-ay)/len;let nx=uy,ny=-ux;
  if(inPoly(poly,(ax+bx)/2+nx*2,(ay+by)/2+ny*2)){nx=-nx;ny=-ny}
  o.segs.push({x1:ax,y1:ay,x2:bx,y2:by,th:0});
  const n=Math.ceil(len/36);
  for(let s=0;s<n;s++){const a=s/n,b=(s+1)/n,px=ax+(bx-ax)*a,py=ay+(by-ay)*a,qx=ax+(bx-ax)*b,qy=ay+(by-ay)*b,e=T*.7;
   o.pieces.push({k:(py+qy)/2+T/2,pts:[[px,py],[qx,qy],[qx+nx*T+ux*e,qy+ny*T+uy*e],[px+nx*T-ux*e,py+ny*T-uy*e]],h:11,kind:'wall'})}
 }
 const addBlock=(r,h,kind)=>{const p=rectPts(r);for(let k=0;k<4;k++){const a=p[k],b=p[(k+1)%4];o.segs.push({x1:a[0],y1:a[1],x2:b[0],y2:b[1],th:0})}
  o.pieces.push({k:p.reduce((s,q)=>s+q[1],0)/4,pts:p,h,kind})};
 (d.blocks||[]).forEach(r=>addBlock(r,13,'block'));
 o.zones.filter(z=>z.k==='bridge').forEach(z=>{if(z.h>z.w){addBlock([z.x-4,z.y,4,z.h],6,'rail');addBlock([z.x+z.w,z.y,4,z.h],6,'rail')}else{addBlock([z.x,z.y-4,z.w,4],6,'rail');addBlock([z.x,z.y+z.h,z.w,4],6,'rail')}});
 (d.bumpers||[]).forEach(b=>o.circ.push({x:b[0],y:b[1],r:b[2],e:1.05,kick:1,vis:'bumper'}));
 o.mills.forEach(m=>o.circ.push({x:m.x,y:m.y,r:7,e:.5,vis:'hub'}));
 // Münzen (3 pro Bahn, deterministisch)
 const nearSeg=(x,y)=>{let m=1e9;for(const s of o.segs)m=Math.min(m,segNear(x,y,s.x1,s.y1,s.x2,s.y2)[2]);return m};
 const badZone=(x,y)=>{let w=false,safe=false;for(const z of o.zones){if(zin(z,x,y)){if(z.k==='water')w=true;if(z.k==='bridge'||z.k==='land')safe=true}}return w&&!safe};
 for(let tries=0;tries<600&&o.coins.length<3;tries++){const x=x0+R()*(x1-x0),y=y0+R()*(y1-y0);
  if(!inPoly(poly,x,y)||nearSeg(x,y)<18||badZone(x,y))continue;
  if(hyp(x-o.cup[0],y-o.cup[1])<34||hyp(x-o.tee[0],y-o.tee[1])<34)continue;
  if(o.mills.some(m=>hyp(x-m.x,y-m.y)<m.len+10)||o.circ.some(c=>hyp(x-c.x,y-c.y)<c.r+16)||o.portals.some(p=>hyp(x-p.a[0],y-p.a[1])<24||hyp(x-p.b[0],y-p.b[1])<24))continue;
  if(o.coins.some(c=>hyp(x-c.x,y-c.y)<60))continue;
  o.coins.push({x,y,got:false})}
 // Dekoration auf der Bodenplatte, außerhalb der Bahn
 const kinds=[['tree','bush','flower','flower'],['ftree','mush','plant','mush'],['cube','toyball','cube','star']][Math.floor(i/6)],pal=[['#2fa84a','#46c35f','#7bd957'],['#7a4de8','#e44a8c','#18b8a8','#f2a21a'],['#ff5a4a','#3a8cff','#ffcf3a','#3ad06a']][Math.floor(i/6)];
 const P0=o.plate;
 for(let tries=0;tries<400&&o.decor.length<30;tries++){const x=P0[0]+6+R()*(P0[2]-P0[0]-12),y=P0[1]+6+R()*(P0[3]-P0[1]-12);
  if(inPoly(poly,x,y)||nearSeg(x,y)<20)continue;
  if(o.decor.some(q=>hyp(q.x-x,q.y-y)<20))continue;
  const kd=kinds[Math.floor(R()*kinds.length)],tall=kd==='tree'||kd==='ftree'?64:kd==='cube'||kd==='star'?34:0;let hid=false;
  for(let dy=6;dy<=tall&&!hid;dy+=8)for(let dx=-20;dx<=20;dx+=10)if(inPoly(poly,x+dx,y-dy)){hid=true;break}
  if(hid)continue;
  o.decor.push({x,y,k:kd,c:pal[Math.floor(R()*pal.length)],c2:pal[Math.floor(R()*pal.length)],s:.8+R()*.5,ph:R()*TAU})}
 L=o;return o}
/* ---------------- Physik ---------------- */
const B={x:0,y:0,vx:0,vy:0,rot:0,sx:0,sy:0,lx:0,ly:0,sq:0,z:0,vis:1,sc:1};
const G={state:'menu',t:0,time:0,strokes:0,aim:-Math.PI/2,charging:false,ct:0,pw:0,keys:{},mode:'round',hole:0,scores:[],coinsHole:0,tube:null,parts:[],trail:[],bounce:0};
let dyn=[];
function dynSegs(t){dyn.length=0;
 for(const m of L.mills){const n=m.arms||2;for(let k=0;k<n;k++){const a=m.w*t+k*TAU/n,c=Math.cos(a),s=Math.sin(a);dyn.push({x1:m.x,y1:m.y,x2:m.x+c*m.len,y2:m.y+s*m.len,th:2.6,rot:1,om:m.w,px:m.x,py:m.y})}}
 for(const s of L.swings){const a=s.base+s.amp*Math.sin(s.w*t+s.ph),om=s.amp*s.w*Math.cos(s.w*t+s.ph);dyn.push({x1:s.px,y1:s.py,x2:s.px+Math.cos(a)*s.len,y2:s.py+Math.sin(a)*s.len,th:2.6,rot:1,om,px:s.px,py:s.py})}
 for(const s of L.sliders){const ph=TAU*t/s.T,u=.5-.5*Math.cos(ph),du=.5*Math.sin(ph)*TAU/s.T,cxs=s.ax+(s.bx-s.ax)*u,cys=s.ay+(s.by-s.ay)*u,vx=(s.bx-s.ax)*du,vy=(s.by-s.ay)*du,hw=s.w/2,hh=s.h/2;
  const q=[[cxs-hw,cys-hh],[cxs+hw,cys-hh],[cxs+hw,cys+hh],[cxs-hw,cys+hh]];
  for(let k=0;k<4;k++){const a=q[k],b=q[(k+1)%4];dyn.push({x1:a[0],y1:a[1],x2:b[0],y2:b[1],th:0,vx,vy})}}
 return dyn}
function sliderPos(s,t){const u=.5-.5*Math.cos(TAU*t/s.T);return[s.ax+(s.bx-s.ax)*u,s.ay+(s.by-s.ay)*u]}
function bounce(nx,ny,vox,voy,e,kick){
 const rvx=B.vx-vox,rvy=B.vy-voy,vn=rvx*nx+rvy*ny;if(vn>=0)return;
 let ox=rvx-(1+e)*vn*nx,oy=rvy-(1+e)*vn*ny;
 if(kick){const sp=hyp(ox,oy);if(sp<kick){const k=sp>1?kick/sp:0;if(k){ox*=k;oy*=k}else{ox=nx*kick;oy=ny*kick}}}
 B.vx=ox+vox;B.vy=oy+voy;const imp=-vn;if(imp>40){G.bounce=Math.min(1,imp/400);if(imp>70)snd('bounce',Math.min(1,imp/450))}}
function collideAll(){
 for(let it=0;it<3;it++){let hit=false;
  for(const list of [L.segs,dyn])for(const s of list){
   const q=segNear(B.x,B.y,s.x1,s.y1,s.x2,s.y2),R=BR+(s.th||0);
   if(q[2]<R){let nx,ny;if(q[2]>1e-4){nx=(B.x-q[0])/q[2];ny=(B.y-q[1])/q[2]}else{const l=hyp(s.x2-s.x1,s.y2-s.y1)||1;nx=-(s.y2-s.y1)/l;ny=(s.x2-s.x1)/l}
    B.x=q[0]+nx*R;B.y=q[1]+ny*R;let vox=0,voy=0;
    if(s.rot){vox=-s.om*(q[1]-s.py);voy=s.om*(q[0]-s.px)}else if(s.vx!==undefined){vox=s.vx;voy=s.vy}
    bounce(nx,ny,vox,voy,.82);hit=true}}
  for(const c of L.circ){const dx=B.x-c.x,dy=B.y-c.y,d=hyp(dx,dy),R=BR+c.r;if(d<R){const nx=d>1e-4?dx/d:1,ny=d>1e-4?dy/d:0;B.x=c.x+nx*R;B.y=c.y+ny*R;bounce(nx,ny,0,0,c.e,c.kick?150:0);if(c.kick)c.pulse=1;hit=true}}
  if(!hit)break}}
function surface(x,y){const s={drag:1.05,cf:42,ax:0,ay:0,water:false,safe:false,boost:null,sand:false,ice:false};
 for(const z of L.zones)if(zin(z,x,y)){switch(z.k){case'sand':s.drag=4.5;s.cf=130;s.sand=true;break;case'ice':s.drag=.16;s.cf=5;s.ice=true;break;case'slope':s.ax+=z.ax;s.ay+=z.ay;break;case'boost':s.boost=z;break;case'water':s.water=true;break;case'bridge':case'land':s.safe=true;break}}
 return s}
function stepBall(dt){
 const sf=surface(B.x,B.y);let sp=hyp(B.vx,B.vy);
 if(sp>0){const ns=Math.max(0,sp*Math.exp(-sf.drag*dt)-sf.cf*dt);const k=ns/sp;B.vx*=k;B.vy*=k;sp=ns}
 B.vx+=sf.ax*dt;B.vy+=sf.ay*dt;
 if(sf.boost){B.vx+=sf.boost.dx*1100*dt;B.vy+=sf.boost.dy*1100*dt;const s2=hyp(B.vx,B.vy);if(s2>400){B.vx*=400/s2;B.vy*=400/s2}}
 B.x+=B.vx*dt;B.y+=B.vy*dt;collideAll();
 if(!inPoly(L.poly,B.x,B.y)){B.x=B.lx;B.y=B.ly;B.vx*=-.4;B.vy*=-.4}else{B.lx=B.x;B.ly=B.y}
 sp=hyp(B.vx,B.vy);B.rot+=sp*dt/BR;
 if(sp>25&&G.time%.03<DT*1.01)G.trail.push({x:B.x,y:B.y,a:1});
 const s2=surface(B.x,B.y);
 if(s2.water&&!s2.safe){G.state='drown';G.t=0;snd('splash');splash(B.x,B.y);return}
 for(const p of L.portals){if(hyp(B.x-p.a[0],B.y-p.a[1])<11){G.state='tube';G.t=0;G.tube={p,sp:Math.min(320,Math.max(140,sp*.9))};snd('tube');return}}
 for(const c of L.coins)if(!c.got&&hyp(B.x-c.x,B.y-c.y)<13){c.got=true;G.coinsHole++;snd('coin');sparkle(c.x,c.y,'#ffd23a',10)}
 const cd=hyp(B.x-L.cup[0],B.y-L.cup[1]);
 if(cd<20&&sp<170){const k=520*dt/Math.max(cd,3);B.vx+=(L.cup[0]-B.x)*k;B.vy+=(L.cup[1]-B.y)*k}
 if(cd<8&&sp<330){G.state='sink';G.t=0;snd('sink');confetti(L.cup[0],L.cup[1]);return}
 const acc=hyp(s2.ax,s2.ay);
 if(sp<7&&(acc<s2.cf*.8)&&!s2.boost){B.vx=B.vy=0;restBall()}}
function restBall(){B.sx=B.x;B.sy=B.y;if(G.strokes>=10){finishHole(true);return}G.state='aim';G.t=0}
function shoot(ang,pw){if(G.state!=='aim')return false;pw=Math.max(.05,Math.min(1,pw));const v=80+pw*520;B.vx=Math.cos(ang)*v;B.vy=Math.sin(ang)*v;B.sx=B.x;B.sy=B.y;G.strokes++;G.state='roll';G.t=0;G.bounce=.5;snd('hit',pw);hudUpd();return true}
function physics(dt){
 G.time+=dt;dynSegs(G.time);
 if(G.state==='roll')stepBall(dt);
 else if(G.state==='sink'){G.t+=dt;const k=Math.min(1,G.t/.5);B.x+=(L.cup[0]-B.x)*Math.min(1,dt*14);B.y+=(L.cup[1]-B.y)*Math.min(1,dt*14);B.z=-9*k;B.sc=1-.5*k;B.vis=1-k*.9;if(G.t>.9)finishHole(false)}
 else if(G.state==='drown'){G.t+=dt;B.z=-12*Math.min(1,G.t*2);B.vis=Math.max(0,1-G.t*1.4);if(G.t>.9){B.x=B.sx;B.y=B.sy;B.lx=B.x;B.ly=B.y;B.vx=B.vy=0;B.z=0;B.vis=1;B.sc=1;G.strokes++;G.state='aim';G.t=0;hudUpd();toast('Wasser! +1 Strafschlag')}}
 else if(G.state==='tube'){G.t+=dt;B.vis=0;if(G.t>.45){const p=G.tube.p,dl=hyp(p.dir[0],p.dir[1]);B.x=p.b[0];B.y=p.b[1];B.lx=B.x;B.ly=B.y;B.vx=p.dir[0]/dl*G.tube.sp;B.vy=p.dir[1]/dl*G.tube.sp;B.vis=1;G.state='roll';G.t=0;snd('tube2');sparkle(B.x,B.y,'#7fe0ff',8);B.x+=p.dir[0]/dl*13;B.y+=p.dir[1]/dl*13}}
 else if(G.state==='aim'){B.vis=1;B.z=0}
 for(const c of L.circ)if(c.pulse)c.pulse=Math.max(0,c.pulse-dt*5);
 G.bounce=Math.max(0,G.bounce-dt*3.5);
 for(const q of G.trail)q.a-=dt*3;G.trail=G.trail.filter(q=>q.a>0);
 for(const p of G.parts){p.x+=p.vx*dt;p.y+=p.vy*dt;p.z+=p.vz*dt;p.vz-=p.g*dt;p.life-=dt;if(p.z<0&&p.bounce){p.z=0;p.vz*=-.4}}
 G.parts=G.parts.filter(p=>p.life>0)}
function splash(x,y){for(let i=0;i<16;i++){const a=Math.random()*TAU,s=30+Math.random()*60;G.parts.push({x,y,z:2,vx:Math.cos(a)*s,vy:Math.sin(a)*s*.6,vz:90+Math.random()*80,g:320,life:.8,c:'#bfe8ff',r:2.4})}}
function sparkle(x,y,c,n){for(let i=0;i<n;i++){const a=Math.random()*TAU,s=20+Math.random()*50;G.parts.push({x,y,z:8,vx:Math.cos(a)*s,vy:Math.sin(a)*s*.6,vz:40+Math.random()*60,g:160,life:.6,c,r:2})}}
function confetti(x,y){const cs=['#ff5a4a','#ffcf3a','#3ad06a','#3a8cff','#e44a8c'];for(let i=0;i<46;i++){const a=Math.random()*TAU,s=30+Math.random()*90;G.parts.push({x,y,z:6,vx:Math.cos(a)*s,vy:Math.sin(a)*s*.7,vz:120+Math.random()*140,g:260,life:1.6,c:cs[i%5],r:2.6,bounce:1})}}
/* ---------------- Kamera ---------------- */
const CAM={S:1,OX:0,OY:0,CXW:200,BY:0,BH:400};let CW=300,CH=300,DPR=1,GL=null,GLc=null;
function P(x,y,z){const t=(y-CAM.BY)/CAM.BH,f=.86+.28*t;z=z||0;return[CAM.OX+CAM.S*(x-CAM.CXW)*f,CAM.OY+CAM.S*((y-CAM.BY)*TILT-z*.9*f),CAM.S*f]}
function fitCam(){
 CW=Math.max(100,cv.clientWidth);CH=Math.max(100,cv.clientHeight);DPR=Math.min(2,window.devicePixelRatio||1);cv.width=Math.round(CW*DPR);cv.height=Math.round(CH*DPR);
 if(!L)return;const land=CW>CH*1.05,ar={x:6,y:6,w:CW-12,h:CH-12-(land?0:156)},pl=L.plate;
 CAM.CXW=(pl[0]+pl[2])/2;CAM.BY=pl[1];CAM.BH=pl[3]-pl[1];CAM.S=1;CAM.OX=0;CAM.OY=0;
 let a=1e9,b=-1e9,c=1e9,d=-1e9;
 for(const q of [[pl[0],pl[1],44],[pl[2],pl[1],44],[pl[0],pl[3],-16],[pl[2],pl[3],-16]]){const p=P(q[0],q[1],q[2]);a=Math.min(a,p[0]);b=Math.max(b,p[0]);c=Math.min(c,p[1]);d=Math.max(d,p[1])}
 const S=Math.min(ar.w/(b-a),ar.h/(d-c));CAM.S=S;CAM.OX=ar.x+ar.w/2-S*(a+b)/2;CAM.OY=ar.y+ar.h/2-S*(c+d)/2;
 GL=document.createElement('canvas');GL.width=cv.width;GL.height=cv.height;GLc=GL.getContext('2d');buildGround()}
/* ---------------- Zeichenhelfer ---------------- */
function path(c,pts,z){c.beginPath();for(let i=0;i<pts.length;i++){const p=P(pts[i][0],pts[i][1],z);i?c.lineTo(p[0],p[1]):c.moveTo(p[0],p[1])}c.closePath()}
function flat(f){const o=[];for(let i=0;i<f.length;i+=2)o.push([f[i],f[i+1]]);return o}
function ellPts(x,y,rx,ry,n){const o=[];for(let i=0;i<(n||36);i++){const a=TAU*i/(n||36);o.push([x+Math.cos(a)*rx,y+Math.sin(a)*ry])}return o}
function zonePts(z){return z.t==='r'?[[z.x,z.y],[z.x+z.w,z.y],[z.x+z.w,z.y+z.h],[z.x,z.y+z.h]]:ellPts(z.x,z.y,z.rx,z.ry)}
function prism(c,pts,h,top,front,side,ol){
 const n=pts.length;let mx=0,my=0;pts.forEach(p=>{mx+=p[0];my+=p[1]});mx/=n;my/=n;
 for(let k=0;k<n;k++){const a=pts[k],b=pts[(k+1)%n];let nx=b[1]-a[1],ny=-(b[0]-a[0]);if((a[0]-mx)*nx+(a[1]-my)*ny<0){nx=-nx;ny=-ny}
  if(ny<=0)continue;const pa=P(a[0],a[1],0),pb=P(b[0],b[1],0),qa=P(a[0],a[1],h),qb=P(b[0],b[1],h);
  c.beginPath();c.moveTo(pa[0],pa[1]);c.lineTo(pb[0],pb[1]);c.lineTo(qb[0],qb[1]);c.lineTo(qa[0],qa[1]);c.closePath();c.fillStyle=Math.abs(nx)>Math.abs(ny)*1.2?side:front;c.fill();c.strokeStyle=ol||'rgba(18,13,38,.55)';c.lineWidth=1.3;c.stroke()}
 path(c,pts,h);c.fillStyle=top;c.fill();c.strokeStyle=ol||'rgba(18,13,38,.55)';c.lineWidth=1.3;c.stroke()}
function cyl(c,x,y,r,h,top,side,hole){const b=P(x,y,0),t=P(x,y,h),rx=r*b[2],ry=r*CAM.S*TILT;
 c.fillStyle=side;c.strokeStyle='rgba(18,13,38,.6)';c.lineWidth=1.3;
 c.beginPath();c.ellipse(b[0],b[1],rx,ry,0,0,TAU);c.fill();c.stroke();
 c.fillRect(b[0]-rx,t[1],rx*2,b[1]-t[1]);c.beginPath();c.moveTo(b[0]-rx,t[1]);c.lineTo(b[0]-rx,b[1]);c.moveTo(b[0]+rx,t[1]);c.lineTo(b[0]+rx,b[1]);c.stroke();
 c.beginPath();c.ellipse(b[0],b[1],rx,ry,0,0,Math.PI);c.fill();c.stroke();
 c.fillStyle=top;c.beginPath();c.ellipse(t[0],t[1],rx,ry,0,0,TAU);c.fill();c.stroke();
 if(hole){c.fillStyle=hole;c.beginPath();c.ellipse(t[0],t[1],rx*.62,ry*.62,0,0,TAU);c.fill()}}
function shadow(c,x,y,r,a){const p=P(x,y,0);c.fillStyle='rgba(18,13,38,'+(a||.25)+')';c.beginPath();c.ellipse(p[0]+r*p[2]*.25,p[1]+r*CAM.S*.12,r*p[2]*1.05,r*CAM.S*TILT*.9,0,0,TAU);c.fill()}
function star5(c,x,y,r){c.beginPath();for(let i=0;i<10;i++){const a=-Math.PI/2+i*Math.PI/5,rr=i%2?r*.45:r;c.lineTo(x+Math.cos(a)*rr,y+Math.sin(a)*rr)}c.closePath()}
/* ---------------- Ball ---------------- */
function drawBall(c,x,y,r,sk,rot){
 c.save();c.translate(x,y);
 let g=c.createRadialGradient(-r*.35,-r*.4,r*.1,0,0,r);g.addColorStop(0,sk.c1);g.addColorStop(1,sk.c2);
 c.fillStyle=g;c.beginPath();c.arc(0,0,r,0,TAU);c.fill();
 c.save();c.beginPath();c.arc(0,0,r,0,TAU);c.clip();c.rotate(rot||0);const pc=sk.pc||'#fff';c.fillStyle=pc;
 if(sk.p==='stripe'){c.fillRect(-r,-r*.28,r*2,r*.56)}
 else if(sk.p==='dots'){for(const[u,v]of[[.45,.2],[-.4,.5],[-.1,-.5],[.2,-.2],[-.6,-.1]]){c.beginPath();c.arc(u*r,v*r,r*.18,0,TAU);c.fill()}}
 else if(sk.p==='star'){star5(c,0,0,r*.62);c.fill()}
 else if(sk.p==='check'){c.fillRect(0,0,r,r);c.fillRect(-r,-r,r,r)}
 else if(sk.p==='rainbow'){['#ff4a4a','#ffb43a','#ffe84a','#4ad05a','#3a8cff','#a64aff'].forEach((col,i)=>{c.fillStyle=col;c.fillRect(-r,-r+i*r/3,r*2,r/3+.5)})}
 else if(sk.p==='gold'){c.fillStyle='rgba(255,255,255,.55)';c.fillRect(-r,-r*.1,r*2,r*.12);c.fillRect(-r*.1,-r,r*.12,r*2)}
 c.restore();
 g=c.createRadialGradient(-r*.3,-r*.35,r*.05,0,0,r);g.addColorStop(0,'rgba(255,255,255,.75)');g.addColorStop(.35,'rgba(255,255,255,0)');g.addColorStop(.75,'rgba(0,0,0,0)');g.addColorStop(1,'rgba(18,13,38,.38)');
 c.fillStyle=g;c.beginPath();c.arc(0,0,r,0,TAU);c.fill();
 c.strokeStyle='#120d26';c.lineWidth=Math.max(1.2,r*.12);c.beginPath();c.arc(0,0,r,0,TAU);c.stroke();c.restore()}
/* ---------------- Bodenebene (zwischengespeichert) ---------------- */
function buildGround(){
 const g=GLc,th=L.th,pl=L.plate;g.setTransform(DPR,0,0,DPR,0,0);g.clearRect(0,0,CW,CH);g.lineJoin='round';
 // Platte: Seitenwände + Oberseite mit Kacheln
 const q=[[pl[0],pl[3]],[pl[2],pl[3]]];let a=P(q[0][0],q[0][1],0),b=P(q[1][0],q[1][1],0),a2=P(q[0][0],q[0][1],-16),b2=P(q[1][0],q[1][1],-16);
 g.fillStyle=th.slab;g.strokeStyle='#120d26';g.lineWidth=2;g.beginPath();g.moveTo(a[0],a[1]);g.lineTo(b[0],b[1]);g.lineTo(b2[0],b2[1]);g.lineTo(a2[0],a2[1]);g.closePath();g.fill();g.stroke();
 const ls=P(pl[0],pl[1],0),lb=P(pl[0],pl[3],0),lb2=P(pl[0],pl[3],-16);g.fillStyle='rgba(0,0,0,.25)';g.beginPath();g.moveTo(ls[0],ls[1]);g.lineTo(lb[0],lb[1]);g.lineTo(lb2[0],lb2[1]);g.stroke();
 path(g,[[pl[0],pl[1]],[pl[2],pl[1]],[pl[2],pl[3]],[pl[0],pl[3]]],0);g.fillStyle=th.plate;g.fill();g.stroke();
 g.save();path(g,[[pl[0],pl[1]],[pl[2],pl[1]],[pl[2],pl[3]],[pl[0],pl[3]]],0);g.clip();g.fillStyle=th.plate2;
 for(let y=pl[1],j=0;y<pl[3];y+=40,j++)for(let x=pl[0]+(j%2)*40,i=0;x<pl[2];x+=80){path(g,[[x,y],[x+40,y],[x+40,y+40],[x,y+40]],0);g.fill()}g.restore();
 // Bahn
 const fw=flat(L.poly);path(g,fw,0);g.fillStyle=th.fw;g.fill();
 g.save();path(g,fw,0);g.clip();g.fillStyle=th.fw2;
 for(let y=pl[1]-(pl[1]%40),j=0;y<pl[3];y+=40,j++){if(j%2)continue;path(g,[[pl[0],y],[pl[2],y],[pl[2],y+20],[pl[0],y+20]],0);g.fill()}
 // Zonen: Reihenfolge Wasser, Land, Brücke, Rest
 const order={water:0,land:1,bridge:2,sand:3,ice:3,slope:3,boost:3},zs=L.zones.slice().sort((p,q)=>order[p.k]-order[q.k]),R=rng(55+L.i);
 for(const z of zs){const pts=zonePts(z);
  if(z.k==='water'){path(g,pts,0);g.fillStyle='#38aefc';g.fill();g.strokeStyle='#bfeaff';g.lineWidth=3;g.stroke();path(g,pts,0);g.save();g.clip();g.strokeStyle='rgba(255,255,255,.25)';g.lineWidth=2;
   for(let k=0;k<26;k++){const x=pl[0]+R()*(pl[2]-pl[0]),y=pl[1]+R()*(pl[3]-pl[1]),p=P(x,y,0);g.beginPath();g.ellipse(p[0],p[1],10*p[2],3*p[2],0,0,Math.PI);g.stroke()}g.restore()}
  else if(z.k==='land'){path(g,pts,0);g.fillStyle=th.fw;g.fill();g.strokeStyle='#f2e3b0';g.lineWidth=4;g.stroke();g.strokeStyle='#d6c389';g.lineWidth=1.5;g.stroke()}
  else if(z.k==='bridge'){const vert=z.h>z.w;path(g,pts,0);g.fillStyle='#8a5326';g.fill();
   const n=Math.floor((vert?z.h:z.w)/6);for(let k=0;k<n;k++){const a0=k*6;const pp=vert?[[z.x,z.y+a0+.5],[z.x+z.w,z.y+a0+.5],[z.x+z.w,z.y+a0+5.3],[z.x,z.y+a0+5.3]]:[[z.x+a0+.5,z.y],[z.x+a0+5.3,z.y],[z.x+a0+5.3,z.y+z.h],[z.x+a0+.5,z.y+z.h]];path(g,pp,0);g.fillStyle=k%2?'#c98a45':'#d89a55';g.fill()}
   path(g,pts,0);g.strokeStyle='#120d26';g.lineWidth=1.5;g.stroke()}
  else if(z.k==='sand'){path(g,pts,0);g.fillStyle='#f4d88f';g.fill();g.strokeStyle='#d8b565';g.lineWidth=2.5;g.stroke();path(g,pts,0);g.save();g.clip();g.fillStyle='rgba(176,130,50,.45)';
   for(let k=0;k<70;k++){const x=(z.x||0)+(R()-.5)*(z.rx||z.w)*2,y=(z.y||0)+(R()-.5)*(z.ry||z.h)*2,p=P(x,y,0);g.beginPath();g.arc(p[0],p[1],1.2*p[2],0,TAU);g.fill()}g.restore()}
  else if(z.k==='ice'){path(g,pts,0);g.fillStyle='rgba(190,240,255,.88)';g.fill();path(g,pts,0);g.save();g.clip();g.strokeStyle='rgba(255,255,255,.8)';g.lineWidth=2;
   for(let k=0;k<22;k++){const x=z.x+R()*z.w,y=z.y+R()*z.h,p=P(x,y,0),p2=P(x+24,y-10,0);g.beginPath();g.moveTo(p[0],p[1]);g.lineTo(p2[0],p2[1]);g.stroke()}g.restore();path(g,pts,0);g.strokeStyle='#8fd0ee';g.lineWidth=2;g.stroke()}
  else if(z.k==='slope'){path(g,pts,0);g.fillStyle='rgba(20,90,40,.2)';g.fill();g.strokeStyle='rgba(20,90,40,.45)';g.lineWidth=2;g.setLineDash([6,5]);g.stroke();g.setLineDash([])}
  else if(z.k==='boost'){path(g,pts,0);g.fillStyle='rgba(255,226,90,.75)';g.fill();g.strokeStyle='#e0a800';g.lineWidth=2;g.stroke()}}
 g.restore();
 // Fairway-Rand und Loch, Abschlag
 path(g,fw,0);g.strokeStyle='rgba(18,13,38,.5)';g.lineWidth=1.5;g.stroke();
 const cp=P(L.cup[0],L.cup[1],0);g.fillStyle='#1a1020';g.strokeStyle='#f4efe0';g.lineWidth=2.2;g.beginPath();g.ellipse(cp[0],cp[1],8*cp[2],8*CAM.S*TILT,0,0,TAU);g.fill();g.stroke();
 const tp=P(L.tee[0],L.tee[1],0);g.fillStyle='rgba(255,255,255,.75)';g.strokeStyle='rgba(18,13,38,.5)';g.lineWidth=1.5;g.beginPath();g.ellipse(tp[0],tp[1],12*tp[2],12*CAM.S*TILT,0,0,TAU);g.fill();g.stroke()}
/* ---------------- Bild pro Frame ---------------- */
function drawDecor(c,d){
 const p=P(d.x,d.y,0),k=p[2],s=d.s*CAM.S*k,t=G.time;
 const sw=Math.sin(t*1.6+d.ph)*.6;
 c.lineJoin='round';c.strokeStyle='rgba(18,13,38,.6)';c.lineWidth=1.2;
 const blob=(x,y,r,col)=>{c.fillStyle=col;c.beginPath();c.arc(x,y,r,0,TAU);c.fill();c.stroke()};
 if(d.k==='tree'){shadow(c,d.x,d.y,9*d.s);c.strokeStyle='#5a3a1a';c.lineWidth=4*s/2;c.beginPath();c.moveTo(p[0],p[1]);c.lineTo(p[0],p[1]-18*s);c.stroke();c.strokeStyle='rgba(18,13,38,.6)';c.lineWidth=1.2;
  blob(p[0]+sw,p[1]-30*s,13*s,d.c);blob(p[0]-5*s+sw,p[1]-26*s,8*s,'rgba(255,255,255,.18)')}
 else if(d.k==='bush'){shadow(c,d.x,d.y,9*d.s);blob(p[0]-5*s,p[1]-4*s,7*s,d.c);blob(p[0]+4*s,p[1]-5*s,8*s,d.c)}
 else if(d.k==='flower'){c.strokeStyle='#2b8a3a';c.lineWidth=1.5;c.beginPath();c.moveTo(p[0],p[1]);c.lineTo(p[0]+sw,p[1]-9*s);c.stroke();c.strokeStyle='rgba(18,13,38,.6)';c.lineWidth=1;
  for(let i=0;i<5;i++){const a=i*TAU/5;blob(p[0]+sw+Math.cos(a)*3.2*s,p[1]-9*s+Math.sin(a)*3.2*s,2.6*s,d.c2)}blob(p[0]+sw,p[1]-9*s,2*s,'#ffe24a')}
 else if(d.k==='ftree'){shadow(c,d.x,d.y,8*d.s);c.strokeStyle='#3a2a58';c.lineWidth=3.5*s/1.2;c.beginPath();c.moveTo(p[0],p[1]);c.quadraticCurveTo(p[0]+5*s,p[1]-18*s,p[0]+sw*2,p[1]-34*s);c.stroke();c.strokeStyle='rgba(18,13,38,.6)';c.lineWidth=1.2;
  blob(p[0]+sw*2,p[1]-40*s,12*s,d.c);blob(p[0]-8*s+sw*2,p[1]-34*s,8*s,d.c2);blob(p[0]+9*s+sw*2,p[1]-35*s,7*s,d.c)}
 else if(d.k==='mush'){shadow(c,d.x,d.y,8*d.s);c.fillStyle='#fff3dd';c.fillRect(p[0]-2.6*s,p[1]-10*s,5.2*s,10*s);c.strokeRect(p[0]-2.6*s,p[1]-10*s,5.2*s,10*s);
  c.fillStyle='#ee3b3b';c.beginPath();c.ellipse(p[0],p[1]-10*s,9*s,7*s,0,Math.PI,TAU);c.fill();c.stroke();c.fillStyle='#fff';[[-4,-13],[3,-15],[5,-11]].forEach(q=>{c.beginPath();c.arc(p[0]+q[0]*s,p[1]+q[1]*s,1.5*s,0,TAU);c.fill()})}
 else if(d.k==='plant'){c.fillStyle='#ffd23a';for(let i=-2;i<=2;i++){c.beginPath();c.moveTo(p[0]+i*2.5*s,p[1]);c.lineTo(p[0]+i*4*s+sw,p[1]-(14-Math.abs(i)*2.2)*s);c.lineTo(p[0]+i*2.5*s+3*s,p[1]);c.closePath();c.fill();c.stroke()}}
 else if(d.k==='cube'){const h=9*d.s,pts=[[d.x-h,d.y-h],[d.x+h,d.y-h],[d.x+h,d.y+h],[d.x-h,d.y+h]];shadow(c,d.x,d.y,12*d.s,.2);prism(c,pts,h*1.7,d.c,d.c2,d.c)}
 else if(d.k==='toyball'){shadow(c,d.x,d.y,9*d.s);const r=8*s;c.fillStyle=d.c;c.beginPath();c.arc(p[0],p[1]-r,r,0,TAU);c.fill();c.stroke();c.fillStyle=d.c2;c.beginPath();c.arc(p[0],p[1]-r,r,.3,1.9);c.fill();c.beginPath();c.arc(p[0],p[1]-r,r,0,TAU);c.stroke()}
 else if(d.k==='star'){shadow(c,d.x,d.y,7*d.s);c.fillStyle='#ffd23a';star5(c,p[0],p[1]-12*s,10*s);c.fill();c.stroke()}
}
function armQuad(m,a,len,hw,z){const c=Math.cos(a),s=Math.sin(a),nx=-s*hw,ny=c*hw;return[[m.x+nx,m.y+ny],[m.x+c*len+nx,m.y+s*len+ny],[m.x+c*len-nx,m.y+s*len-ny],[m.x-nx,m.y-ny]]}
function flatQuad(c,q,z,col){path(c,q,z);c.fillStyle=col;c.fill();c.strokeStyle='rgba(18,13,38,.7)';c.lineWidth=1.2;c.stroke()}
function buildItems(){
 const it=[],c=cx;
 for(const w of L.pieces){const kind=w.kind,th=L.th;it.push({k:w.k,f:()=>{if(kind==='rail')prism(c,w.pts,w.h,'#d89a55','#8a5a2a','#7a4a1f');else if(kind==='block')prism(c,w.pts,w.h,th.wt,th.wf,th.ws);else prism(c,w.pts,w.h,th.wt,th.wf,th.ws)}})}
 for(const d of L.decor)it.push({k:d.y,f:()=>drawDecor(c,d)});
 for(const b of L.circ){if(b.vis==='bumper')it.push({k:b.y,f:()=>{const pu=b.pulse||0;shadow(c,b.x,b.y,b.r);cyl(c,b.x,b.y,b.r*(1+pu*.12),10+pu*3,'#ff7ab8','#c93a82');const p=P(b.x,b.y,10+pu*3);c.fillStyle='rgba(255,255,255,.7)';c.beginPath();c.arc(p[0]-b.r*p[2]*.25,p[1]-b.r*CAM.S*.1,b.r*p[2]*.18,0,TAU);c.fill()}})}
 for(const m of L.mills){
  it.push({k:m.y+1,f:()=>{shadow(c,m.x,m.y,10);cyl(c,m.x,m.y,8.5,16,'#d94a3a','#efdcb4');
    const t=P(m.x,m.y,16),ap=P(m.x,m.y,30);c.fillStyle='#d94a3a';c.strokeStyle='rgba(18,13,38,.7)';c.lineWidth=1.3;c.beginPath();c.moveTo(t[0]-9.5*t[2],t[1]);c.lineTo(ap[0],ap[1]);c.lineTo(t[0]+9.5*t[2],t[1]);c.closePath();c.fill();c.stroke()}});
  const n=m.arms||2;
  for(let k=0;k<n;k++)it.push({k:m.y+Math.sin(m.w*G.time+k*TAU/n)*m.len*.5+2,f:()=>{const a=m.w*G.time+k*TAU/n,q=armQuad(m,a,m.len,2.6);flatQuad(c,armQuad(m,a,m.len,2.6),0,'rgba(18,13,38,.18)');
    flatQuad(c,q,10,'#fff');const q2=armQuad({x:m.x+Math.cos(a)*m.len*.45,y:m.y+Math.sin(a)*m.len*.45},a,m.len*.55,2.6);flatQuad(c,q2,10,k%2?'#3a8cff':'#e8452c')}})}
 for(const s of L.swings){
  it.push({k:s.py,f:()=>{shadow(c,s.px,s.py,7);cyl(c,s.px,s.py,5.5,14,'#ffcf3a','#c98a00')}});
  it.push({k:s.py+10,f:()=>{const a=s.base+s.amp*Math.sin(s.w*G.time+s.ph),m={x:s.px,y:s.py};flatQuad(c,armQuad(m,a,s.len,2.6),0,'rgba(18,13,38,.18)');flatQuad(c,armQuad(m,a,s.len,2.6),10,'#fff');
    flatQuad(c,armQuad({x:s.px+Math.cos(a)*s.len*.5,y:s.py+Math.sin(a)*s.len*.5},a,s.len*.5,2.6),10,'#e8452c');
    const e=P(s.px+Math.cos(a)*s.len,s.py+Math.sin(a)*s.len,10);c.fillStyle='#ffcf3a';c.strokeStyle='rgba(18,13,38,.7)';c.beginPath();c.arc(e[0],e[1],4.5*e[2],0,TAU);c.fill();c.stroke()}})}
 for(const s of L.sliders)it.push({k:s.ay,f:()=>{const p=sliderPos(s,G.time),hw=s.w/2,hh=s.h/2,pts=[[p[0]-hw,p[1]-hh],[p[0]+hw,p[1]-hh],[p[0]+hw,p[1]+hh],[p[0]-hw,p[1]+hh]];
   shadow(c,p[0],p[1],Math.max(hw,hh)*.9,.18);prism(c,pts,12,'#ffb23a','#e8452c','#c4331c')}});
 L.portals.forEach(pt=>{
  it.push({k:pt.a[1],f:()=>{shadow(c,pt.a[0],pt.a[1],13);cyl(c,pt.a[0],pt.a[1],12,9,'#4aa8ff','#2b78c9','#0c1e3a')}});
  it.push({k:pt.b[1],f:()=>{shadow(c,pt.b[0],pt.b[1],13);cyl(c,pt.b[0],pt.b[1],12,9,'#ffa23a','#c9701a','#3a1c06')}})});
 for(const k of L.coins)if(!k.got)it.push({k:k.y,f:()=>{const bob=Math.sin(G.time*3+k.x)*1.5,p=P(k.x,k.y,10+bob),w=Math.abs(Math.cos(G.time*3.2+k.y*.1)),r=5.6*p[2];shadow(c,k.x,k.y,5,.18);
   c.fillStyle='#ffd23a';c.strokeStyle='#8a5a00';c.lineWidth=1.4;c.beginPath();c.ellipse(p[0],p[1],Math.max(1,r*w),r,0,0,TAU);c.fill();c.stroke();
   if(w>.35){c.fillStyle='#fff3a0';c.beginPath();c.ellipse(p[0],p[1],r*w*.45,r*.5,0,0,TAU);c.fill()}}});
 it.push({k:L.cup[1],f:()=>{const b=P(L.cup[0],L.cup[1],0),t=P(L.cup[0],L.cup[1],36);c.strokeStyle='#f4efe0';c.lineWidth=2.4*CAM.S*.6+1;c.beginPath();c.moveTo(b[0],b[1]);c.lineTo(t[0],t[1]);c.stroke();
   c.fillStyle='#ff3b3b';c.strokeStyle='rgba(18,13,38,.8)';c.lineWidth=1.3;c.beginPath();c.moveTo(t[0],t[1]);
   for(let i=1;i<=4;i++)c.lineTo(t[0]+i*5*t[2],t[1]+4*t[2]+Math.sin(G.time*5-i)*2.2*t[2]);for(let i=4;i>=0;i--)c.lineTo(t[0]+i*5*t[2],t[1]+13*t[2]+Math.sin(G.time*5-i)*2.2*t[2]);c.closePath();c.fill();c.stroke()}});
 it.push({k:B.y,f:()=>drawBallItem(c)});
 return it}
function drawBallItem(c){
 if(B.vis<=0.01)return;const sk=SKINS[S_.skin]||SKINS[0],p=P(B.x,B.y,BR+B.z),r=BR*p[2]*B.sc,a=Math.max(0,B.vis);
 c.globalAlpha=a;if(B.z>-3)shadow(c,B.x,B.y,BR*B.sc,.28*a);
 const sq=G.bounce*.18;c.save();c.translate(p[0],p[1]);c.scale(1+sq,1-sq);drawBall(c,0,0,r,sk,B.rot);c.restore();c.globalAlpha=1;
 const cl=G.club,age=cl?G.time-cl.t0:9;
 if(G.state==='aim'||age<.22){let d=null;if(age<.22)d=cl.d0*(1-Math.min(1,age/.09));else d=7+G.pw*28;
  const ang=age<.22?cl.a:G.aim,dx=Math.cos(ang),dy=Math.sin(ang),hx=B.x-dx*(BR+2+d),hy=B.y-dy*(BR+2+d),h0=P(hx,hy,3),h1=P(hx,hy,32);
  c.strokeStyle='#c9ccd8';c.lineWidth=2.6*CAM.S*.55+.6;c.lineCap='round';c.beginPath();c.moveTo(h0[0],h0[1]);c.lineTo(h1[0],h1[1]-4);c.stroke();
  const e1=P(hx-dy*5,hy+dx*5,3),e2=P(hx+dy*5,hy-dx*5,3);c.strokeStyle='#e8452c';c.lineWidth=4.6*CAM.S*.55+.8;c.beginPath();c.moveTo(e1[0],e1[1]);c.lineTo(e2[0],e2[1]);c.stroke();c.lineCap='butt'}}
function drawAim(c){
 if(G.state!=='aim')return;const pw=G.pw,len=pw>0?30+pw*160:76,dx=Math.cos(G.aim),dy=Math.sin(G.aim);
 const col=pw<.5?'#ffe24a':pw<.8?'#ffa13a':'#ff4a3a';c.globalAlpha=pw>0?1:.65;
 for(let d=16;d<len;d+=11){const p=P(B.x+dx*d,B.y+dy*d,.5),r=(1.6+d/len*1.6)*p[2]*.9;c.fillStyle='#fff';c.strokeStyle='#120d26';c.lineWidth=1;c.beginPath();c.arc(p[0],p[1],r+.6,0,TAU);c.fill();c.stroke();c.fillStyle=col;c.beginPath();c.arc(p[0],p[1],r,0,TAU);c.fill()}
 const e=P(B.x+dx*len,B.y+dy*len,.5),f=P(B.x+dx*(len+14),B.y+dy*(len+14),.5),nx=P(B.x+dx*len-dy*6,B.y+dy*len+dx*6,.5),ny=P(B.x+dx*len+dy*6,B.y+dy*len-dx*6,.5);
 c.fillStyle=col;c.strokeStyle='#120d26';c.lineWidth=1.6;c.beginPath();c.moveTo(f[0],f[1]);c.lineTo(nx[0],nx[1]);c.lineTo(ny[0],ny[1]);c.closePath();c.fill();c.stroke();c.globalAlpha=1}
function drawOverlays(c){
 const R=rng(9+L.i);
 for(const z of L.zones){
  if(z.k==='water'){for(let k=0;k<7;k++){const x=z.x+R()*(z.w||1),y=z.y+R()*(z.h||1);if(z.t!=='r')continue;if(L.zones.some(q=>(q.k==='bridge'||q.k==='land')&&zin(q,x,y)))continue;
    const ph=(G.time*.6+k*.37)%1,p=P(x,y,0);c.strokeStyle='rgba(255,255,255,'+(.7*(1-ph))+')';c.lineWidth=1.6;c.beginPath();c.ellipse(p[0],p[1],(4+ph*12)*p[2],(1.4+ph*4)*CAM.S*TILT,0,0,TAU);c.stroke()}}
  else if(z.k==='slope'||z.k==='boost'){const dx=z.k==='slope'?z.ax:z.dx,dy=z.k==='slope'?z.ay:z.dy,l=hyp(dx,dy),ux=dx/l,uy=dy/l,sp=z.k==='slope'?36:26,off=(G.time*(z.k==='slope'?22:70))%sp;
   c.fillStyle=z.k==='slope'?'rgba(255,255,255,.55)':'rgba(255,255,255,.95)';c.strokeStyle='rgba(18,13,38,.45)';c.lineWidth=1;
   for(let u=z.x+sp/2;u<z.x+z.w;u+=sp)for(let v=z.y+sp/2;v<z.y+z.h;v+=sp){const x=u+ux*off-(ux>0?sp/2:0)*0,y=v+uy*off;if(x<z.x+3||x>z.x+z.w-3||y<z.y+3||y>z.y+z.h-3)continue;
    const a=P(x+ux*6,y+uy*6,.4),b=P(x-ux*4-uy*6,y-uy*4+ux*6,.4),d=P(x-ux*4+uy*6,y-uy*4-ux*6,.4),e=P(x-ux*1,y-uy*1,.4);c.beginPath();c.moveTo(a[0],a[1]);c.lineTo(b[0],b[1]);c.lineTo(e[0],e[1]);c.lineTo(d[0],d[1]);c.closePath();c.fill();c.stroke()}}}
 for(const pt of L.portals){const dl=hyp(pt.dir[0],pt.dir[1]),ux=pt.dir[0]/dl,uy=pt.dir[1]/dl,a=P(pt.b[0]+ux*22,pt.b[1]+uy*22,.4),b=P(pt.b[0]+ux*14-uy*5,pt.b[1]+uy*14+ux*5,.4),d=P(pt.b[0]+ux*14+uy*5,pt.b[1]+uy*14-ux*5,.4);
  c.fillStyle='rgba(255,162,58,.9)';c.strokeStyle='rgba(18,13,38,.6)';c.lineWidth=1;c.beginPath();c.moveTo(a[0],a[1]);c.lineTo(b[0],b[1]);c.lineTo(d[0],d[1]);c.closePath();c.fill();c.stroke()}
 for(const q of G.trail){const p=P(q.x,q.y,.3);c.fillStyle='rgba(255,255,255,'+Math.max(0,q.a*.5)+')';c.beginPath();c.arc(p[0],p[1],BR*.55*p[2]*q.a,0,TAU);c.fill()}}
let clouds=[{x:.1,y:.12,s:1,v:6},{x:.55,y:.06,s:1.3,v:4},{x:.85,y:.2,s:.8,v:8},{x:.3,y:.3,s:.7,v:5}];
function render(){
 const c=cx;c.setTransform(DPR,0,0,DPR,0,0);const th=L.th;
 let g=c.createLinearGradient(0,0,0,CH);g.addColorStop(0,th.sky[0]);g.addColorStop(1,th.sky[1]);c.fillStyle=g;c.fillRect(0,0,CW,CH);
 c.fillStyle='rgba(255,255,255,.6)';for(const k of clouds){const x=((k.x*CW+G.time*k.v)%(CW+160))-80,y=k.y*CH,w=60*k.s;c.beginPath();c.ellipse(x,y,w,w*.32,0,0,TAU);c.ellipse(x-w*.5,y+w*.08,w*.55,w*.24,0,0,TAU);c.ellipse(x+w*.55,y+w*.1,w*.5,w*.22,0,0,TAU);c.fill()}
 if(GL)c.drawImage(GL,0,0,CW,CH);
 drawOverlays(c);drawAim(c);
 const items=buildItems();items.sort((a,b)=>a.k-b.k);for(const i of items)i.f();
 for(const p of G.parts){const q=P(p.x,p.y,p.z);c.fillStyle=p.c;c.globalAlpha=Math.min(1,p.life*2);c.beginPath();c.arc(q[0],q[1],p.r*q[2]*1.2,0,TAU);c.fill();c.globalAlpha=1}}
/* ---------------- Speicherstand ---------------- */
let S_={};
try{S_=JSON.parse(localStorage.getItem('mg_save_v1')||'{}')||{}}catch(e){S_={}}
S_.coins|=0;S_.owned=Array.isArray(S_.owned)?S_.owned:[0];if(!S_.owned.includes(0))S_.owned.push(0);S_.skin=S_.skin|0;S_.best=S_.best||{};S_.bestRound=S_.bestRound|0;if(S_.snd===undefined)S_.snd=true;S_.round=S_.round||null;
function save(){try{localStorage.setItem('mg_save_v1',JSON.stringify(S_))}catch(e){}}
/* ---------------- Sound ---------------- */
let AC=null;
function ac(){if(AC===null){try{AC=new(window.AudioContext||window.webkitAudioContext)()}catch(e){AC=false}}if(AC&&AC.state==='suspended')AC.resume().catch(()=>{});return AC}
function tone(f,d,type,vol,to,delay){const a=ac();if(!a)return;const t=a.currentTime+(delay||0),o=a.createOscillator(),g=a.createGain();o.type=type||'sine';o.frequency.setValueAtTime(f,t);if(to)o.frequency.exponentialRampToValueAtTime(to,t+d);
 g.gain.setValueAtTime(vol,t);g.gain.exponentialRampToValueAtTime(.0008,t+d);o.connect(g);g.connect(a.destination);o.start(t);o.stop(t+d+.02)}
function noise(d,vol,fq,delay){const a=ac();if(!a)return;const t=a.currentTime+(delay||0),n=Math.floor(a.sampleRate*d),b=a.createBuffer(1,n,a.sampleRate),x=b.getChannelData(0);for(let i=0;i<n;i++)x[i]=(Math.random()*2-1)*(1-i/n);
 const s=a.createBufferSource(),f=a.createBiquadFilter(),g=a.createGain();s.buffer=b;f.type='lowpass';f.frequency.value=fq||1800;g.gain.value=vol;s.connect(f);f.connect(g);g.connect(a.destination);s.start(t)}
function snd(k,v){if(!S_.snd||G.sim)return;v=v||1;
 switch(k){case'hit':noise(.09,.5*v+.1,2400);tone(190,.12,'triangle',.35*v+.1,90);break;case'bounce':tone(420+Math.random()*120,.07,'square',.12*v,260);break;
  case'splash':noise(.5,.5,1200);tone(500,.25,'sine',.2,150);break;case'sink':[523,659,784,1047].forEach((f,i)=>tone(f,.22,'triangle',.3,0,i*.09));break;
  case'coin':tone(988,.07,'square',.14);tone(1319,.16,'square',.14,0,.07);break;case'tube':tone(300,.4,'sawtooth',.14,90);break;case'tube2':tone(120,.25,'sawtooth',.14,500);break;
  case'win':[523,659,784,1047,1319].forEach((f,i)=>tone(f,.3,'triangle',.3,0,i*.11));break;case'click':tone(660,.05,'square',.12);break;case'buy':[784,988,1319].forEach((f,i)=>tone(f,.2,'triangle',.3,0,i*.08));break;case'no':tone(160,.2,'sawtooth',.2,110);break}}
/* ---------------- Oberfläche ---------------- */
const ov=$('ov'),joy=$('joy'),knob=$('knob'),pwb=$('pw');
let toastEl=null,toastT=0;
function toast(m){if(G.sim)return;if(!toastEl){toastEl=document.createElement('div');toastEl.style.cssText='position:absolute;left:50%;top:10px;transform:translateX(-50%);background:#fff;color:#2a2148;border:3px solid #120d26;border-radius:16px;padding:6px 16px;font-weight:800;box-shadow:0 3px 0 #120d26;z-index:4;pointer-events:none;transition:opacity .3s;white-space:nowrap';$('stage').appendChild(toastEl)}
 toastEl.textContent=m;toastEl.style.opacity=1;clearTimeout(toastT);toastT=setTimeout(()=>{toastEl.style.opacity=0},2200)}
const parSum=n=>HOLES.slice(0,n).reduce((s,h)=>s+h.par,0);
const fmtD=d=>d===0?'±0':d>0?'+'+d:String(d);
function hudUpd(){if(!L)return;const done=G.scores.length,tot=G.scores.reduce((s,v)=>s+v,0)-parSum(done);
 $('hh').innerHTML='Bahn <b>'+(G.hole+1)+'</b>/18';$('hp').innerHTML='Par <b>'+L.d.par+'</b>';$('hs').innerHTML='Schläge <b>'+G.strokes+'</b>';
 $('ht').innerHTML='Gesamt <b>'+(G.mode==='round'?fmtD(tot):'–')+'</b>';$('hc').innerHTML='🪙 <b>'+S_.coins+'</b>'}
function showOv(html){ov.innerHTML=html;ov.style.display='flex';joy.style.display=pwb.style.display='none';G.charging=false;G.pw=0}
function hideOv(){ov.style.display='none';joy.style.display=pwb.style.display='block';pwb.style.display='flex'}
const label=(st,par)=>st===1?'Hole-in-One!':st-par<=-3?'Albatros!':st-par===-2?'Eagle!':st-par===-1?'Birdie!':st===par?'Par':st-par===1?'Bogey':st-par===2?'Doppel-Bogey':'+'+(st-par);
function menu(){G.state='menu';const r=S_.round;
 showOv('<h1>⛳ MINIGOLF</h1><p>Joystick: Richtung einstellen · Knopf halten: Kraft aufbauen · loslassen: Schlag.<br>Tastatur: ◀ ▶ drehen, ▲ aufs Loch zielen, Leertaste halten &amp; loslassen.</p><div class="row">'+
  (r?'<button class="btn big alt" data-a="cont">▶ Weiter (Bahn '+(r.hole+1)+')</button>':'')+'<button class="btn big" data-a="new">Neue Runde</button></div><div class="row"><button class="btn" data-a="holes">Einzelne Bahn</button><button class="btn" data-a="skins">⚪ Bälle</button><button class="btn" data-a="snd">Ton: '+(S_.snd?'an':'aus')+'</button></div>'+
  '<p>🪙 '+S_.coins+' Münzen · Beste Runde: '+(S_.bestRound?S_.bestRound+' Schläge ('+fmtD(S_.bestRound-parSum(18))+')':'–')+'</p>')}
function holesMenu(){let h='<h2>Einzelne Bahn</h2><div class="grid">';HOLES.forEach((d,i)=>{const b=S_.best[i];h+='<div class="cell" data-a="hole" data-i="'+i+'"><b>'+(i+1)+'</b>'+d.n+'<br>Par '+d.par+' · '+(b?'Best '+b:'–')+'</div>'});
 showOv(h+'</div><button class="btn" data-a="menu">Zurück</button>')}
function skinsMenu(){showOv('<h2>Bälle</h2><p>🪙 '+S_.coins+' Münzen – tippen zum Wählen oder Kaufen</p><div class="skins" id="sk"></div><button class="btn" data-a="menu">Zurück</button>');const w=$('sk');
 SKINS.forEach((s,i)=>{const d=document.createElement('div'),own=S_.owned.includes(i);d.className='skin'+(S_.skin===i?' sel':'');d.dataset.a='skin';d.dataset.i=i;const c=document.createElement('canvas');c.width=c.height=88;drawBall(c.getContext('2d'),44,44,34,s,.6);
  d.appendChild(c);d.appendChild(document.createTextNode(s.n));d.appendChild(document.createElement('br'));d.appendChild(document.createTextNode(own?(S_.skin===i?'✔ aktiv':'frei'):'🪙 '+s.cost));if(!own&&S_.coins<s.cost)d.style.opacity=.55;w.appendChild(d)})}
function startHole(i){G.hole=i;buildLevel(i);Object.assign(B,{x:L.tee[0],y:L.tee[1],vx:0,vy:0,rot:0,sx:L.tee[0],sy:L.tee[1],lx:L.tee[0],ly:L.tee[1],sq:0,z:0,vis:1,sc:1});
 G.strokes=0;G.coinsHole=0;G.state='aim';G.pw=0;G.charging=false;G.parts=[];G.trail=[];G.club=null;G.aim=Math.atan2(L.cup[1]-L.tee[1],L.cup[0]-L.tee[0]);fitCam();hideOv();hudUpd();
 toast('Bahn '+(i+1)+': '+L.d.n+' · Par '+L.d.par)}
function startRound(cont){if(!cont||!S_.round){S_.round={hole:0,scores:[]};save()}G.mode='round';G.scores=S_.round.scores.slice();startHole(S_.round.hole)}
function finishHole(gaveUp){
 const st=Math.min(10,G.strokes),par=L.d.par,d=st-par;let earn=5+G.coinsHole*2+(st===1?40:d<=-3?30:d===-2?20:d===-1?10:d===0?5:d===1?2:0);if(gaveUp)earn=G.coinsHole*2;
 if(G.sim){G.state='done';G.result={st,gaveUp};return}
 G.state='card';S_.coins+=earn;if(!gaveUp&&(!S_.best[G.hole]||st<S_.best[G.hole]))S_.best[G.hole]=st;
 if(G.mode==='round'){G.scores.push(st);S_.round={hole:G.hole+1,scores:G.scores.slice()}}save();hudUpd();if(!gaveUp)snd('win');
 const last=G.mode==='round'&&G.hole>=17;
 showOv('<div class="card"><div class="big">'+(gaveUp?'Aufgegeben':label(st,par))+'</div><p style="color:#2a2148">'+L.d.n+'<br>Schläge: <b>'+st+'</b> · Par '+par+' ('+fmtD(d)+')</p><p style="color:#2a2148">🪙 +'+earn+(G.coinsHole?' (davon '+G.coinsHole+' eingesammelt)':'')+'</p>'+
  (G.mode==='round'?'<p style="color:#2a2148">Gesamt: <b>'+fmtD(G.scores.reduce((s,v)=>s+v,0)-parSum(G.scores.length))+'</b> nach '+G.scores.length+' Bahnen</p>':'')+'</div><div class="row"><button class="btn big alt" data-a="next">'+(last?'Ergebnis':G.mode==='round'?'Nächste Bahn ▶':'Menü')+'</button></div>')}
function roundEnd(){const tot=G.scores.reduce((s,v)=>s+v,0),pr=parSum(18),d=tot-pr,bonus=d<=-5?150:d<=0?80:d<=10?30:10;S_.coins+=bonus;const nb=!S_.bestRound||tot<S_.bestRound;if(nb)S_.bestRound=tot;S_.round=null;save();hudUpd();snd('win');
 let t='<table class="sc"><tr>';G.scores.forEach((s,i)=>{t+='<td>'+(i+1)+'</td>'+(i===8?'</tr><tr>':'')});t+='</tr><tr>';G.scores.forEach((s,i)=>{const dd=s-HOLES[i].par;t+='<td style="background:'+(dd<0?'#9be89b':dd===0?'#fff':'#ffb0a0')+'"><b>'+s+'</b></td>'+(i===8?'</tr><tr>':'')});t+='</tr></table>';
 showOv('<h1>🏆 Runde geschafft!</h1><div class="card"><div class="big">'+tot+' Schläge</div><p style="color:#2a2148">Par '+pr+' → <b>'+fmtD(d)+'</b>'+(nb?' · 🎉 neue Bestleistung!':'')+'</p>'+t+'<p style="color:#2a2148">🪙 Bonus +'+bonus+'</p></div><div class="row"><button class="btn big" data-a="new">Neue Runde</button><button class="btn" data-a="menu">Menü</button></div>')}
ov.addEventListener('click',e=>{const t=e.target.closest('[data-a]');if(!t)return;const a=t.dataset.a;ac();snd('click');
 if(a==='new')startRound(false);else if(a==='cont')startRound(true);else if(a==='holes')holesMenu();else if(a==='skins')skinsMenu();else if(a==='menu')menu();
 else if(a==='snd'){S_.snd=!S_.snd;save();menu()}
 else if(a==='hole'){G.mode='single';G.scores=[];startHole(+t.dataset.i)}
 else if(a==='next'){if(G.mode==='round'){if(G.hole>=17)roundEnd();else startHole(G.hole+1)}else menu()}
 else if(a==='skin'){const i=+t.dataset.i,s=SKINS[i];if(S_.owned.includes(i)){S_.skin=i;save();skinsMenu()}else if(S_.coins>=s.cost){S_.coins-=s.cost;S_.owned.push(i);S_.skin=i;save();snd('buy');skinsMenu()}else snd('no')}});
$('bm').onclick=()=>{ac();menu()};
/* ---------------- Eingabe ---------------- */
let ptrSeen=false;addEventListener('pointerdown',()=>{ptrSeen=true},true);
function bindHold(el,down,move,up){let id=null,tid=null;
 el.addEventListener('pointerdown',e=>{e.preventDefault();id=e.pointerId;try{el.setPointerCapture(id)}catch(_){}down(e)});
 addEventListener('pointermove',e=>{if(e.pointerId===id)move(e)});
 const end=c=>e=>{if(e.pointerId===id){id=null;up(e,c)}};addEventListener('pointerup',end(false));addEventListener('pointercancel',end(true));
 const pt=t=>({clientX:t.clientX,clientY:t.clientY});               // Ersatz für Systeme ohne Pointer-Events: Touch-Ereignisse
 el.addEventListener('touchstart',e=>{if(ptrSeen||tid!==null)return;e.preventDefault();const t=e.changedTouches[0];tid=t.identifier;down(pt(t))},{passive:false});
 el.addEventListener('touchmove',e=>{if(ptrSeen||tid===null)return;e.preventDefault();for(const t of e.changedTouches)if(t.identifier===tid)move(pt(t))},{passive:false});
 const te=c=>e=>{if(ptrSeen||tid===null)return;for(const t of e.changedTouches)if(t.identifier===tid){tid=null;up(pt(t),c)}};el.addEventListener('touchend',te(false));el.addEventListener('touchcancel',te(true))}
function joyMove(e){const r=joy.getBoundingClientRect(),dx=e.clientX-(r.left+r.width/2),dy=e.clientY-(r.top+r.height/2),d=hyp(dx,dy),m=r.width*.3,k=d>m?m/d:1;knob.style.transform='translate('+dx*k+'px,'+dy*k+'px)';if(d>r.width*.1&&G.state==='aim')G.aim=Math.atan2(dy,dx)}
bindHold(joy,e=>{ac();joyMove(e)},joyMove,()=>{knob.style.transform=''});
function chargeStart(){if(G.state!=='aim'||ov.style.display!=='none'||G.charging)return;ac();G.charging=true;G.ct=0;G.pw=0}
function chargeEnd(){if(!G.charging)return;G.charging=false;const pw=G.pw;G.pw=0;pwb.firstChild.style.height='0';if(G.state!=='aim'||pw<.02)return;G.club={t0:G.time,d0:7+pw*28,a:G.aim};shoot(G.aim,pw)}
bindHold(pwb,()=>chargeStart(),()=>{},(e,cancel)=>{if(cancel){G.charging=false;G.pw=0;pwb.firstChild.style.height='0'}else chargeEnd()});
addEventListener('keydown',e=>{const k=e.key;
 if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown',' ','Enter'].includes(k)){e.preventDefault()}
 if(ov.style.display!=='none'){if(k==='Enter'||k===' '){const b=ov.querySelector('.btn.big')||ov.querySelector('.btn');if(b&&!e.repeat)b.click()}return}
 if(k==='ArrowUp'&&G.state==='aim')G.aim=Math.atan2(L.cup[1]-B.y,L.cup[0]-B.x);
 if((k===' '||k==='Enter')&&!e.repeat)chargeStart();
 if(k==='Escape')menu();G.keys[k]=1});
addEventListener('keyup',e=>{delete G.keys[e.key];if(e.key===' '||e.key==='Enter')chargeEnd()});
/* ---------------- Hauptschleife ---------------- */
let last=0,acc=0;
function frame(t){requestAnimationFrame(frame);const dt=Math.min(.05,(t-last)/1000||0);last=t;
 if(!L)return;
 if(G.state==='aim'&&ov.style.display==='none'){const kk=G.keys,sp=2.4*dt*(kk.Shift?.3:1);if(kk.ArrowLeft||kk.a)G.aim-=sp;if(kk.ArrowRight||kk.d)G.aim+=sp}
 if(G.charging){G.ct+=dt;G.pw=.5-.5*Math.cos(G.ct*TAU/1.9);pwb.firstChild.style.height=(G.pw*100)+'%'}
 acc+=dt;while(acc>=DT){physics(DT);acc-=DT}
 render()}
window.addEventListener('resize',()=>{fitCam()});
new ResizeObserver(()=>fitCam()).observe($('stage'));
window.MG={HOLES,SKINS,G,B,get L(){return L},get S(){return S_},startHole,physics,shoot,buildLevel,fitCam,render,menu,finishHole,startRound,zin,surface,
 snap(){return{B:{...B},time:G.time,strokes:G.strokes,got:L.coins.map(c=>c.got),cg:G.coinsHole}},
 restore(s){Object.assign(B,s.B);G.time=s.time;G.strokes=s.strokes;L.coins.forEach((c,i)=>c.got=s.got[i]);G.coinsHole=s.cg;G.state='aim';G.charging=false;G.parts=[];G.trail=[]}};
startHole(0);menu();requestAnimationFrame(frame);
})();
</script></body></html>
"""
