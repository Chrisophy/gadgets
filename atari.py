# -*- coding: utf-8 -*-
# Atari 2600
# IT('s) Possible 
# 2026.11.09
"""Atari-2600-Konsole: spielt Atari-2600-Spiele (.a26/.bin/.rom oder .zip) im Gerät - mit Fernbedienung, Tastatur, Gamepad und Touch-Tasten.

Der Emulator ist „atari2600“ von Monte Ohrt (MIT-Lizenz, https://github.com/mohrt/atari2600): zyklengenaue 6507-CPU, TIA, RIOT und die gängigen
Modul-Formate (2K, 4K, F8, F6, F4, EF, FE, E0, E7, 3F, 3E, FA, UA, 0840, CV, auch mit Superchip). Er ist unten in dieser Datei mitgeliefert.
Spiele (ROMs) gehören nicht dazu: Du brauchst eigene, rechtmäßig erworbene Sicherungskopien deiner Module.

Öffnen: Erweiterungsliste -> Atari 2600 -> „Atari 2600 öffnen“. Spiel suchen: Ordner auf dem Gerät durchsuchen (Pfeiltasten + OK, Zurück = eine Ebene
höher) oder „Spiel hochladen“ (Handy/PC) - hochgeladene Spiele liegen im Ordner „Meine Spiele“. Zuletzt gespielte Spiele stehen oben.

Steuerung (Fernbedienung/Tastatur):  Pfeile = Joystick · OK/Enter/X/Leertaste/⏯ = Feuer · ⏩/S = Reset (Spiel starten) · ⏪/A = Select (Spielwahl) ·
Zurück oder Menü-Taste (≡) = Menü (Weiter, Stand speichern/laden, Reset/Select drücken, Mehr Einstellungen, Zurück zur Liste) · Zurück im Menü verlässt das Gadget
(der Stand wird beim Öffnen des Menüs und alle 20 s automatisch gesichert; „Stand laden“ holt ihn zurück).
Mehr Einstellungen (je Spiel gemerkt): Tempo, Controller (Joystick/Paddle), Schwierigkeit links/rechts, Farbe/Schwarz-Weiß, Flimmer-Glättung,
Modul-Typ (falls ein Spiel nicht startet), „Zwei Tasten“ (Richtung + Feuer gleichzeitig auch mit Fernbedienungen, die nur eine Taste auf einmal senden).
Viele Spiele starten erst nach „Reset drücken“ oder Feuer; manche wollen vorher mit „Select drücken“ eine Variante wählen.
Touch: Knöpfe auf dem Bildschirm.
"""
import base64
import hashlib
import json
import zipfile
import zlib
from pathlib import Path

EXT_ID = 'atari'
EXT_NAME = 'Atari 2600'
EXT_DESCRIPTION = 'Atari-2600-Spiele (.a26/.bin/.rom/.zip) abspielen - Fernbedienung, Gamepad und Touch. Eigene Spiele nötig (nicht enthalten).'
EXT_LINKS = [('Atari 2600', 'index')]
EXT_SETTINGS = [
    {'key': 'gamepad', 'label': 'Gamepad-Schnittstelle des Browsers nutzen (nur PC/Handy mit Controller; am Fernseher AUS lassen: sie nimmt die Pfeiltasten weg)', 'type': 'bool', 'default': False},
]
MAX_ROM = 512 * 1024
MAX_STATE = 6 * 1024 * 1024
_EXT = ('.a26', '.bin', '.rom')
_api = None

# --- Oberfläche (HTML/JS) ---
_PAGE = r'''<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no"><title>Atari 2600</title>
<style>
:root{--bg:#0d1017;--pn:#161b26;--ink:#eef1f7;--mut:#8b94a7;--ac:#e5484d;--ln:#262d3d}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;height:100%;background:var(--bg);color:var(--ink);font:18px/1.35 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;overflow:hidden}
#lst{position:fixed;inset:0;display:flex;flex-direction:column;padding:18px 22px 12px;max-width:900px;margin:0 auto}
h1{margin:0 0 2px;font-size:26px} .sub{color:var(--mut);font-size:15px;margin-bottom:10px;word-break:break-all}
#rows{flex:1;overflow:auto;padding:2px 2px 8px}
.it{display:flex;align-items:center;gap:12px;width:100%;text-align:left;background:var(--pn);color:var(--ink);border:2px solid transparent;border-radius:12px;padding:11px 14px;margin:0 0 7px;font:inherit;cursor:pointer}
.it.on{border-color:var(--ac);background:#202738}
.it .i{font-size:22px;width:30px;text-align:center;flex:none} .it .t{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap} .it .m{color:var(--mut);font-size:14px;flex:none}
#hint{color:var(--mut);font-size:14px;padding-top:6px;border-top:1px solid var(--ln);display:flex;gap:14px;align-items:center;flex-wrap:wrap}
#hint label{background:var(--pn);border:1px solid var(--ln);border-radius:10px;padding:6px 12px;cursor:pointer;color:var(--ink)}
#hint input{display:none} #msg{color:#ffb4b4;min-height:1.3em;font-size:15px}
#game{position:fixed;inset:0;background:#000;display:none;align-items:center;justify-content:center}
#cv{background:#000;image-rendering:pixelated;image-rendering:crisp-edges;width:100vw;height:75vw;max-height:100vh}
#menu{position:fixed;inset:0;background:rgba(5,8,14,.82);display:none;align-items:center;justify-content:center;z-index:5}
#menu .box{background:var(--pn);border:1px solid var(--ln);border-radius:16px;padding:14px;min-width:min(420px,90vw);max-height:96vh;overflow:auto}
#menu h2{margin:0 0 8px;font-size:19px} #menu .it{justify-content:center;padding:8px 14px;margin-bottom:5px;font-size:17px}
#tc{position:fixed;inset:0;pointer-events:none;display:none;z-index:3}
.tb{position:absolute;pointer-events:auto;touch-action:none;user-select:none;-webkit-user-select:none;border-radius:50%;background:rgba(255,255,255,.14);border:2px solid rgba(255,255,255,.35);color:#fff;font-weight:700;display:flex;align-items:center;justify-content:center;font-size:20px}
.tb.d{background:rgba(255,255,255,.3)} .tb.sq{border-radius:12px;font-size:14px}
</style></head><body>
<div id="lst"><h1>🕹 Atari 2600</h1><div class="sub" id="where"></div><div id="rows"></div><div id="msg"></div>
<div id="hint"><span>↑ ↓ wählen · OK öffnet · Zurück: eine Ebene höher</span><label>Spiel hochladen<input id="up" type="file" accept=".a26,.bin,.rom,.zip"></label></div></div>
<div id="game"><canvas id="cv" width="160" height="216"></canvas><button id="fz" aria-label="Spiel" style="position:absolute;inset:0;opacity:0;border:0;background:none;outline:0"></button>
<div id="tc"><div class="tb" id="b_u" style="left:70px;bottom:150px;width:58px;height:58px">▲</div><div class="tb" id="b_d" style="left:70px;bottom:28px;width:58px;height:58px">▼</div><div class="tb" id="b_l" style="left:10px;bottom:89px;width:58px;height:58px">◀</div><div class="tb" id="b_r" style="left:130px;bottom:89px;width:58px;height:58px">▶</div>
<div class="tb" id="b_f" style="right:30px;bottom:70px;width:92px;height:92px">Feuer</div>
<div class="tb sq" id="b_sel" style="left:calc(50% - 90px);bottom:14px;width:80px;height:34px">Select</div><div class="tb sq" id="b_rst" style="left:calc(50% + 10px);bottom:14px;width:80px;height:34px">Reset</div><div class="tb sq" id="b_m" style="right:14px;top:12px;width:70px;height:34px">Menü</div></div>
<div id="menu"><div class="box"><h2 id="mt">Menü</h2><div id="mi"></div></div></div></div>
<script>/*ATARI*/</script>
<script>
(function(){'use strict';
const $=s=>document.querySelector(s),QS=new URLSearchParams(location.search),GTOK=QS.get('share')||QS.get('token')||'',GH=GTOK?{'X-Share':GTOK}:{};
const J=async(u,o)=>{const r=await fetch(u,Object.assign({headers:GH},o||{}));let d=null;try{d=await r.clone().json()}catch(e){}if(!r.ok)throw new Error((d&&d.error)||('Fehler '+r.status));return d!==null?d:r};
function closeGame(){try{if(window.parent!==window){window.parent.history.back();return}}catch(e){}if(history.length>1)history.back();else location.href='/ui/'}
let mode='browse',cfg={},cur={path:'',parent:'',entries:[]},sel=0,stack=[];
const rows=$('#rows'),msg=$('#msg');
const say=t=>{msg.textContent=t||''};
function icon(e){return e.dir?'📁':e.zuletzt?'🕹':'👾'}
function size(n){return n>1048576?(n/1048576).toFixed(1)+' MB':n>1024?Math.round(n/1024)+' KB':''}
function paint(){
  $('#where').textContent=cur.path||'Zuletzt gespielt · Ordner auf diesem Gerät';
  const list=[];if(cur.path)list.push({up:1,name:'⬆ eine Ebene höher'});
  list.push(...cur.entries);cur.list=list;
  rows.replaceChildren(...list.map((e,i)=>{const b=document.createElement('button');b.className='it'+(i===sel?' on':'');
    b.innerHTML='<span class="i"></span><span class="t"></span><span class="m"></span>';
    b.children[0].textContent=e.up?'':icon(e);b.children[1].textContent=e.name;b.children[2].textContent=e.dir||e.up?'':size(e.size||0);
    b.onclick=()=>{sel=i;open(e)};b.onfocus=()=>{sel=i;rows.querySelectorAll('.it').forEach((x,k)=>x.classList.toggle('on',k===i))};return b}));
  if(!list.length)rows.innerHTML='<p class="sub">Hier liegen keine Atari-Spiele (.a26, .bin, .rom oder .zip). Mit „Spiel hochladen“ lässt sich eine Datei hinzufügen.</p>';
  const on=rows.children[sel];if(on){on.scrollIntoView({block:'nearest'});try{on.focus({preventScroll:true})}catch(e){}}
}
async function browse(path,keep){say('');try{const d=await J('browse?path='+encodeURIComponent(path||''));cur={path:d.path||'',parent:d.parent||'',entries:d.entries||[]};sel=keep||0;paint()}catch(e){say(e.message)}}
function open(e){if(e.up){up();return}if(e.dir){stack.push(cur.path);browse(e.path)}else play(e.path,e.name.replace(/\.(a26|bin|rom|zip)$/i,''))}
function up(){if(!cur.path){closeGame();return}browse(cur.parent&&cur.parent!==cur.path?cur.parent:'')}
/* ---------- Emulator ---------- */
const A=window.atari,cv=$('#cv'),cx=cv.getContext('2d');
let M=null,P=null,FW=null,TD=null,tvNow='ntsc',pal=A.PALETTES.ntsc,img=null,b32=null,prev=null,newFrame=false,debt=0,raf=0,lastT=0,paused=false,speed=1,romPath='',romName='',romImg=null,curScheme='',actx=null,proc=null;
let S={sp:1,ctl:'auto',scheme:'auto',color:1,ld:0,rd:0},phos=false;try{phos=localStorage.getItem('a26_ph')==='1'}catch(e){}
const RING=16384,MASK=RING-1,AL=new Float32Array(RING);let aw=0,ar=0,pre=true;
const fill=()=>(aw-ar)&MASK;
function audioStart(){
  try{const AC=window.AudioContext||window.webkitAudioContext;if(!AC)return;if(!actx)actx=new AC();if(actx.state==='suspended')actx.resume();
    if(!proc){proc=actx.createScriptProcessor(2048,0,2);proc.onaudioprocess=e=>{const o0=e.outputBuffer.getChannelData(0),o1=e.outputBuffer.getChannelData(1);
      if(pre&&fill()>=1200)pre=false;
      for(let i=0;i<o0.length;i++){if(!pre&&ar!==aw){o0[i]=o1[i]=AL[ar];ar=(ar+1)&MASK}else{pre=true;o0[i]=0;o1[i]=0}}};proc.connect(actx.destination)}}catch(e){actx=null;proc=null}}
function wake(){try{if(actx&&actx.state==='suspended')actx.resume()}catch(e){}}
function audioStop(){try{if(proc){proc.disconnect();proc.onaudioprocess=null}if(actx)actx.close()}catch(e){}proc=null;actx=null;aw=ar=0;pre=true}
function pushAudio(s){if(!proc||!actx||actx.state!=='running')return;for(let i=0;i<s.length;i++){if(fill()>6000)break;AL[aw]=s[i]*.7;aw=(aw+1)&MASK}}
function audioRates(){if(M)M.tia.audio.setRates(M.audioClockHz*speed,actx?actx.sampleRate:48000)}
function layout(){const r=160*A.PIXEL_ASPECT[tvNow]/(FW?FW.lines:216),w=Math.min(innerWidth,innerHeight*r);cv.style.width=w+'px';cv.style.height=(w/r)+'px'}
addEventListener('resize',layout);
function resizeScreen(){const n=FW.lines;cv.width=160;cv.height=n;img=cx.createImageData(160,n);b32=new Uint32Array(img.data.buffer);prev=new Uint32Array(b32.length);layout()}
function useTv(tv,force){if(tv===tvNow&&!force&&img)return;tvNow=tv;M.setTv(tv);FW.setTv(tv);pal=A.PALETTES[tv];resizeScreen();audioRates()}
let lastPx=null,lastInfo=null;
function frameDone(px,info){
  const d=TD.update(info);if(d&&d!==tvNow)useTv(d);
  FW.update(info);lastPx=px;lastInfo=info;newFrame=true}
/* Nur das jeweils letzte fertige Bild eines Durchlaufs wird in Farben umgesetzt (spart Arbeit, wenn mehrere Bilder auf einmal fertig werden). */
function convert(){
  const px=lastPx,W=160,top=FW.top,n=FW.lines,fl=lastInfo.lines;
  for(let y=0;y<n;y++){const sy=top+y;if(sy>=fl)break;const o=y*W,so=sy*W;
    if(phos){for(let x=0;x<W;x++){const c=pal[px[so+x]],b=prev[o+x];b32[o+x]=((((c&0xfefefe)>>>1)+((b&0xfefefe)>>>1))|0xff000000)>>>0;prev[o+x]=c}}
    else{for(let x=0;x<W;x++){b32[o+x]=pal[px[so+x]]}}}}
function loadSet(name){S={sp:1,ctl:'auto',scheme:'auto',color:1,ld:0,rd:0};try{Object.assign(S,JSON.parse(localStorage.getItem('a26:'+name)||'{}'))}catch(e){}speed=S.sp>=.5&&S.sp<=1?S.sp:1}
function saveSet(){try{S.sp=speed;localStorage.setItem('a26:'+romName,JSON.stringify(S))}catch(e){}}
function applyCtl(){const g=A.guessControllers(romImg);P.setType(0,S.ctl==='joystick'?'joystick':S.ctl==='paddles'?'paddles':g[0]);P.setType(1,g[1])}
function applySw(){P.switches.color=!!S.color;P.switches.leftDifficultyA=!!S.ld;P.switches.rightDifficultyA=!!S.rd}
function insertCart(){curScheme=S.scheme==='auto'?A.detectScheme(romImg):S.scheme;M.insertCartridge(A.createCartridge(romImg,curScheme));TD.reset();FW.reset();debt=0;applyCtl();applySw();useTv('ntsc',true)}
async function play(path,name){
  say('Lade …');
  try{const r=await J('rom?path='+encodeURIComponent(path));const image=new Uint8Array(await r.arrayBuffer());
    if(!image.length||image.length>524288)throw new Error('Das sieht nicht nach einem Atari-2600-Modul aus.');
    stopRun();audioStart();loadSet(name);romImg=image;romPath=path;romName=name;
    M=new A.Atari2600();P=new A.ControllerPorts(M);FW=new A.FrameWindow('ntsc');TD=new A.TvDetector();M.tia.onFrame=frameDone;tvNow='';img=null;
    insertCart();
    mode='game';$('#lst').style.display='none';$('#game').style.display='flex';paused=false;lastT=0;say('');layout();
    if(matchMedia('(pointer:coarse)').matches)$('#tc').style.display='block';
    raf=requestAnimationFrame(loop);pushTrap();try{window.focus();$('#fz').focus()}catch(x){}}
  catch(e){stopRun();mode='browse';$('#game').style.display='none';$('#lst').style.display='flex';say(e.message)}}
function loop(t){raf=requestAnimationFrame(loop);if(paused||!M){lastT=0;return}
  if(!lastT){lastT=t;return}const el=Math.min(t-lastT,100);lastT=t;
  try{P.update(el);debt+=el*speed*M.clockHz/1000;if(debt>0)debt-=M.runCycles(debt)}catch(e){stopRun();say('Fehler im Spiel: '+e.message);back2list();return}
  pushAudio(M.tia.audio.takeSamples());
  if(newFrame){convert();cx.putImageData(img,0,0);newFrame=false}}
function stopRun(){if(raf)cancelAnimationFrame(raf);raf=0;M=null;P=null;audioStop();$('#tc').style.display='none';for(const k in H)H[k]=false}
function back2list(){stopRun();menuHide();mode='browse';$('#game').style.display='none';$('#lst').style.display='flex';paint()}
/* ---------- Zurück-Taste des Geräts ----------
   Im Spiel liegt ein eigener Verlaufseintrag bereit: Zurück (Android: Schritt im Verlauf) öffnet das Menü. Zurück im Menü verlässt das Gadget. */
let trap=0;
function pushTrap(){if(trap)return;try{history.pushState({a26:1},'');trap=1}catch(e){}}
addEventListener('popstate',()=>{if(!trap)return;trap=0;
  if(mode==='game')menuShow();else if(mode==='menu')closeGame();else if(mode==='browse')up()});
/* ---------- Tempo ---------- */
const SPEEDS=[1,.9,.83,.75];
function cycleSpeed(){const i=SPEEDS.findIndex(x=>Math.abs(x-speed)<.015);speed=SPEEDS[(i+1)%SPEEDS.length];audioRates();saveSet()}
/* ---------- Tasten ---------- */
const H={U:false,D:false,L:false,R:false,F:false,RST:false,SEL:false};
function push(){if(!P)return;P.players[0].set('rc',{dirs:(H.U?1:0)|(H.D?2:0)|(H.L?4:0)|(H.R?8:0),fire:!!H.F});P.switches.buttons.set('rc',!!H.RST,!!H.SEL)}
function press(b,on){if(H[b]===on)return;H[b]=on;push()}
function release(){for(const b in kt)delete kt[b];Object.keys(relT).forEach(b=>{clearTimeout(relT[b]);delete relT[b]});Object.keys(latched).forEach(b=>delete latched[b]);Object.keys(H).forEach(b=>{H[b]=false});push()}
/* Zwei Tasten auf der Fernbedienung (nur auf Wunsch): Richtung kurz vor Feuer losgelassen -> bleibt gehalten, bis Feuer losgelassen wird (höchstens 0,7 s). */
let combo=false;try{combo=localStorage.getItem('a26_combo')==='1'}catch(e){}
const DIRS=['U','D','L','R'],relT={},latched={};
function dirUp(b){if(!combo){press(b,false);return}clearTimeout(relT[b]);relT[b]=setTimeout(()=>{delete relT[b];if(!latched[b])press(b,false)},110)}
function otherDown(){for(const b of DIRS)if(relT[b]){clearTimeout(relT[b]);delete relT[b];latched[b]=true;setTimeout(()=>{if(latched[b]){delete latched[b];press(b,false)}},700)}}
function releaseLatch(){for(const b of DIRS){clearTimeout(relT[b]);delete relT[b];if(latched[b]){delete latched[b];press(b,false)}}}
function dirDown(b){for(const d of DIRS){clearTimeout(relT[d]);delete relT[d];if(latched[d]){delete latched[d];if(d!==b)press(d,false)}}press(b,true)}
function keyDown(b){if(DIRS.includes(b)){dirDown(b);return}otherDown();press(b,true)}
function keyUp(b){if(DIRS.includes(b)){dirUp(b);return}press(b,false);releaseLatch()}
const KMAP=(e)=>{const k=e.key,c=e.keyCode,cd=e.code,blank=(k==='Unidentified'||k==='');
  if(k==='ArrowUp'||cd==='ArrowUp'||blank&&c===38)return'U';if(k==='ArrowDown'||cd==='ArrowDown'||blank&&c===40)return'D';if(k==='ArrowLeft'||cd==='ArrowLeft'||blank&&c===37)return'L';if(k==='ArrowRight'||cd==='ArrowRight'||blank&&c===39)return'R';
  if(k==='Enter'||k==='Select'||c===23||c===66||k==='x'||k==='X'||k===' ')return'F';
  if(k==='z'||k==='Z'||k==='y'||k==='Y'||k==='MediaPlayPause'||c===85||c===179||k==='MediaPlay'||k==='MediaPause')return'F';
  if(k==='s'||k==='S'||k==='Tab'||k==='MediaFastForward'||c===90&&k!=='z'&&k!=='Z')return'RST';
  if(k==='a'||k==='A'||k==='Shift'||c===109||k==='MediaRewind'||c===89&&k!=='y'&&k!=='Y')return'SEL';if(c===96||c===100||c===97||c===99)return'F';if(c===108)return'RST';return''};
const isMenuKey=e=>e.key==='Home'||e.key==='BrowserHome'||e.key==='ContextMenu'||e.keyCode===3||e.keyCode===82||e.key==='m'||e.key==='M';
const isBack=e=>e.key==='Escape'||e.key==='Backspace'||e.key==='GoBack'||e.key==='BrowserBack'||e.keyCode===4;
addEventListener('blur',()=>{release()});document.addEventListener('visibilitychange',()=>{if(document.hidden)release()});document.addEventListener('focusout',e=>{if(!e.relatedTarget&&mode==='game')setTimeout(()=>{if(!document.hasFocus())release()},50)});
addEventListener('keydown',e=>{
  if(mode==='browse'){const n=(cur.list||[]).length;
    if(e.key==='ArrowDown'){e.preventDefault();if(n){sel=(sel+1)%n;paint()}}else if(e.key==='ArrowUp'){e.preventDefault();if(n){sel=(sel+n-1)%n;paint()}}
    else if(e.key==='Enter'||e.key==='Select'||e.keyCode===23||e.keyCode===66){e.preventDefault();if(cur.list&&cur.list[sel])open(cur.list[sel])}
    else if(isBack(e)){e.preventDefault();up()}return}
  if(mode==='menu'){e.preventDefault();const n=mitems.length;
    if(e.key==='ArrowDown'){msel=(msel+1)%n;menuPaint()}else if(e.key==='ArrowUp'){msel=(msel+n-1)%n;menuPaint()}
    else if(e.key==='Enter'||e.key==='Select'||e.keyCode===23||e.keyCode===66){const x=mitems[msel];x.go();if(mode==='menu'&&x.lab&&mitems[msel]===x)menuPaint()}else if(isMenuKey(e)||isBack(e)){menuHide()}return}
  if(mode==='game'){wake();
    if(isMenuKey(e)||isBack(e)){e.preventDefault();menuShow();return}
    const b=KMAP(e);if(!b)return;e.preventDefault();kt[b]=performance.now();if(e.repeat)rep[b]=1;keyDown(b)}});
document.addEventListener('keyup',e=>{if(mode!=='game')return;const b=KMAP(e);if(!b)return;e.preventDefault();delete kt[b];keyUp(b)});
/* Sicherung gegen verlorene „Taste losgelassen“-Meldungen (Figur rennt dann endlos): Sendet eine Fernbedienung beim Gedrückthalten Wiederholungen, gilt eine Taste
   als losgelassen, wenn länger als 0,7 s keine mehr kommt. Fernbedienungen ohne Wiederholungen bleiben unberührt. */
const kt={},rep={};setInterval(()=>{const now=performance.now();for(const b in kt)if(rep[b]&&now-kt[b]>700){delete kt[b];keyUp(b)}},150);
/* Gamepad-Schnittstelle: nur auf Wunsch (Einstellung); am Fernseher AUS lassen, sie nimmt dem Android-WebView die Pfeiltasten weg. */
let gpPrev={};function gpStart(){setInterval(()=>{if(mode!=='game'||!navigator.getGamepads)return;const g=[...navigator.getGamepads()].find(x=>x&&x.connected&&x.mapping==='standard');if(!g)return;
  const bt=i=>!!(g.buttons[i]&&g.buttons[i].pressed),ax=(i,s)=>g.axes[i]*s>.5;
  const st={F:bt(0)||bt(1)||bt(2)||bt(3),SEL:bt(8),RST:bt(9),U:bt(12)||ax(1,-1),D:bt(13)||ax(1,1),L:bt(14)||ax(0,-1),R:bt(15)||ax(0,1)},home=bt(16);
  for(const k in st)if(st[k]!==!!gpPrev[k])press(k,st[k]);if(home&&!gpPrev.home)menuShow();
  gpPrev=Object.assign({},st,{home})},16)}
/* Touch */
[['b_u','U'],['b_d','D'],['b_l','L'],['b_r','R'],['b_f','F'],['b_sel','SEL'],['b_rst','RST']].forEach(([id,b])=>{const el=$('#'+id);
  const on=v=>e=>{e.preventDefault();if(v){try{el.setPointerCapture(e.pointerId)}catch(x){}el.classList.add('d')}else el.classList.remove('d');press(b,v)};
  el.addEventListener('pointerdown',on(true));el.addEventListener('pointerup',on(false));el.addEventListener('pointercancel',on(false))});
$('#b_m').addEventListener('pointerdown',e=>{e.preventDefault();menuShow()});
addEventListener('touchstart',()=>{wake();if(mode==='game')$('#tc').style.display='block'},{passive:true});addEventListener('pointerdown',wake);
/* ---------- Speichern: Zustand als JSON (Bytefelder als Base64) ---------- */
function b64(u){let s='';for(let i=0;i<u.length;i+=8192)s+=String.fromCharCode.apply(null,u.subarray(i,i+8192));return btoa(s)}
function unb64(t){const s=atob(t),u=new Uint8Array(s.length);for(let i=0;i<s.length;i++)u[i]=s.charCodeAt(i);return u}
function snap(){const m=M.saveState();return JSON.stringify({a26:1,tv:m.tv,sch:curScheme,sp:speed,state:m.state},(k,v)=>ArrayBuffer.isView(v)&&!(v instanceof DataView)?{$t:v.constructor.name,d:b64(new Uint8Array(v.buffer,v.byteOffset,v.byteLength))}:v)}
function unsnap(txt){return JSON.parse(txt,(k,v)=>v&&typeof v==='object'&&v.$t?new window[v.$t](unb64(v.d).buffer):v)}
function restore(d){if(d.sch&&d.sch!==curScheme){S.scheme=d.sch;insertCart()}M.loadState({tv:d.tv,state:d.state});useTv(d.tv,true);if(d.sp>=.5&&d.sp<=1){speed=d.sp;audioRates()}debt=0;newFrame=false}
async function saveState(){try{await J('state?path='+encodeURIComponent(romPath),{method:'POST',body:snap()});return 'Stand gespeichert.'}catch(e){return 'Speichern nicht möglich: '+e.message}}
async function loadState(){try{let d=await J('state?path='+encodeURIComponent(romPath)),was='Stand geladen.';if(!d||!d.a26){d=await J('state?slot=auto&path='+encodeURIComponent(romPath));was='Letzten Stand geladen (automatisch gesichert).'}if(!d||!d.a26)return 'Es gibt noch keinen gespeicherten Stand.';restore(unsnap(JSON.stringify(d)));return was}catch(e){return 'Kein gespeicherter Stand.'}}
/* ---------- Menü ---------- */
let mitems=[],msel=0;
const onoff=v=>v?'an':'aus';
function menuShow(){if(!M)return;autosave();release();paused=true;mode='menu';msel=0;menuMain();$('#menu').style.display='flex'}
const tap=b=>{menuHide();press(b,true);setTimeout(()=>press(b,false),160)};
function menuMain(){const act=(f)=>async()=>{const r=await f();menuHide(r)};
  $('#mt').textContent=romName+' · '+curScheme;msel=0;
  mitems=[{t:'▶ Weiter',go:()=>menuHide()},{t:'💾 Stand speichern',go:act(saveState)},{t:'📂 Stand laden',go:act(loadState)},
    {t:'🔄 Reset drücken (Spiel starten)',go:()=>tap('RST')},{t:'Select drücken (Spielwahl)',go:()=>tap('SEL')},
    {t:'⚙ Mehr Einstellungen …',go:()=>{menuMore(0)}},{t:'↩ Zurück zur Liste',go:()=>back2list()}];menuPaint()}
function menuMore(keep){
  const tv=()=>speed<.99?Math.round(speed*100)+' %':'100 %';
  mitems=[{lab:()=>'🐢 Tempo: '+tv(),go:()=>{cycleSpeed()}},
    {lab:()=>'🎮 Controller: '+(S.ctl==='auto'?'automatisch ('+P.types[0]+')':S.ctl==='joystick'?'Joystick':'Paddle (Drehregler)'),go:()=>{S.ctl=S.ctl==='auto'?'joystick':S.ctl==='joystick'?'paddles':'auto';applyCtl();saveSet()}},
    {lab:()=>'Schwierigkeit links: '+(S.ld?'A':'B'),go:()=>{S.ld=S.ld?0:1;applySw();saveSet()}},
    {lab:()=>'Schwierigkeit rechts: '+(S.rd?'A':'B'),go:()=>{S.rd=S.rd?0:1;applySw();saveSet()}},
    {lab:()=>'📺 Bild: '+(S.color?'Farbe':'Schwarz-Weiß'),go:()=>{S.color=S.color?0:1;applySw();saveSet()}},
    {lab:()=>'✨ Flimmer-Glättung: '+onoff(phos),go:()=>{phos=!phos;try{localStorage.setItem('a26_ph',phos?'1':'0')}catch(e){}}},
    {lab:()=>'🧩 Modul-Typ: '+(S.scheme==='auto'?'automatisch ('+curScheme+')':S.scheme)+' (startet neu)',go:()=>{const L=['auto'].concat(A.SCHEMES),i=L.indexOf(S.scheme);S.scheme=L[(i+1)%L.length];saveSet();insertCart();menuHide('Modul-Typ: '+curScheme)}},
    {lab:()=>'🎛 Zwei Tasten (Fernbedienung): '+onoff(combo),go:()=>{combo=!combo;try{localStorage.setItem('a26_combo',combo?'1':'0')}catch(e){}if(!combo)releaseLatch()}},
    {t:'‹ zurück',go:()=>{$('#mt').textContent=romName;menuMain()}}];
  $('#mt').textContent='Einstellungen';msel=keep||0;menuPaint()}
function menuPaint(){const m=$('#mi');mitems.forEach(x=>{if(x.lab)x.t=x.lab()});
  m.replaceChildren(...mitems.map((x,i)=>{const b=document.createElement('button');b.className='it'+(i===msel?' on':'');b.textContent=x.t;
    b.onclick=()=>{msel=i;x.go();if(mode==='menu'&&x.lab)menuPaint()};b.onfocus=()=>{msel=i;m.querySelectorAll('.it').forEach((y,k)=>y.classList.toggle('on',k===i))};return b}));const f=m.children[msel];if(f)try{f.focus({preventScroll:true})}catch(e){}}
function menuHide(note){$('#menu').style.display='none';if(mode==='menu'){mode='game';paused=false;lastT=0;pushTrap();try{$('#fz').focus()}catch(e){}}if(typeof note==='string'&&note){const t=document.createElement('div');t.textContent=note;t.style.cssText='position:fixed;top:14px;left:50%;transform:translateX(-50%);background:#161b26;color:#fff;padding:8px 16px;border-radius:10px;z-index:9;font-size:16px';document.body.appendChild(t);setTimeout(()=>t.remove(),1800)}}
/* Auto-Sicherung alle 20 s (Zurück beendet das Spiel sofort, beim Verlassen reicht die Zeit nicht für größere Daten). */
let asBusy=false;function autosave(){if(!M||!romPath||asBusy)return;asBusy=true;let body;try{body=snap()}catch(e){asBusy=false;return}
  fetch('state?slot=auto&path='+encodeURIComponent(romPath),{method:'POST',body,headers:GH}).catch(()=>{}).then(()=>{asBusy=false})}
setInterval(()=>{if(mode==='game'&&!document.hidden)autosave()},20000);document.addEventListener('visibilitychange',()=>{if(document.hidden)autosave()});
/* Upload */
$('#up').onchange=async e=>{const f=e.target.files[0];if(!f)return;say('Lade hoch …');
  try{if(f.size>8388608)throw new Error('Datei zu groß.');await J('upload?name='+encodeURIComponent(f.name),{method:'POST',body:await f.arrayBuffer()});say('Hinzugefügt: '+f.name);browse(cur.path||'')}catch(x){say(x.message)}e.target.value=''};
(async()=>{try{cfg=await J('config')}catch(e){}if(cfg.gamepad)gpStart();browse('')})();
window.__a26={get m(){return M},get p(){return P},get mode(){return mode},get speed(){return speed},get tv(){return tvNow},play,browse,snap,restore,unsnap};
})();
</script></body></html>
'''

# --- atari2600 (MIT, Copyright (c) 2026 Monte Ohrt), gebündelt und gepackt ---
_B64 = (
    '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'
)


def _dirs():
    try:
        from engine import system as S
        base = Path(S.USER_DIR)
    except Exception:                                          # noqa: BLE001
        base = Path.home() / '.moviescout'
    roms, saves = base / 'roms' / 'atari', base / 'atari_saves'
    for d in (roms, saves):
        try:
            d.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
    return roms, saves


def _err(text, code=400):
    return ({'error': text}, code)


def _is_rom_name(n):
    return str(n).lower().endswith(_EXT + ('.zip',))


def _rom_bytes(path):
    """Spiel lesen: Datei direkt oder das erste Modul (.a26/.bin/.rom) in einer .zip. Größe 1 Byte bis 512 KB."""
    p = Path(path)
    if not p.is_file() or not _is_rom_name(p.name):
        raise ValueError('Das ist keine Atari-Datei (.a26, .bin, .rom oder .zip).')
    if p.name.lower().endswith('.zip'):
        if p.stat().st_size > MAX_ROM * 4:
            raise ValueError('Datei zu groß.')
        with zipfile.ZipFile(p) as z:
            names = [i for i in z.infolist() if i.filename.lower().endswith(_EXT) and not i.is_dir()
                     and not Path(i.filename).name.startswith('.')]
            names.sort(key=lambda i: (_EXT.index(Path(i.filename).suffix.lower()), i.filename.lower()))
            if not names:
                raise ValueError('In dieser .zip liegt kein Atari-Modul (.a26, .bin, .rom).')
            if names[0].file_size > MAX_ROM:
                raise ValueError('Spiel zu groß.')
            data = z.read(names[0])
    else:
        if p.stat().st_size > MAX_ROM:
            raise ValueError('Datei zu groß für ein Atari-2600-Modul (höchstens 512 KB).')
        data = p.read_bytes()
    if not data or len(data) > MAX_ROM:
        raise ValueError('Das ist kein gültiges Atari-2600-Modul.')
    return data


def _id(path):
    return hashlib.sha1(str(path).encode('utf-8')).hexdigest()[:20]


def register(api):
    global _api
    _api = api
    js = zlib.decompress(base64.b64decode(''.join(_B64))).decode('utf-8')
    page = _PAGE.replace('/*ATARI*/', js)
    roms_dir, saves_dir = _dirs()

    def config(req):
        return {'roms': str(roms_dir), 'gamepad': bool(api.get('gamepad'))}

    def browse(req):
        path = str(req.query.get('path') or '')
        try:
            from engine import medialib as ML
        except Exception:                                      # noqa: BLE001
            return _err('Der Dateibrowser fehlt in dieser MovieScout-Version.')
        if not path:
            out = []
            for z in (api.get('zuletzt') or [])[:8]:
                if Path(z).is_file():
                    out.append({'name': Path(z).stem, 'path': z, 'dir': False, 'size': Path(z).stat().st_size, 'zuletzt': True})
            out.append({'name': 'Meine Spiele (hochgeladen)', 'path': str(roms_dir), 'dir': True})
            for r in ML.roots():
                out.append({'name': r['name'], 'path': r['path'], 'dir': True})
            return {'path': '', 'parent': '', 'entries': out}
        try:
            d = ML.listdir(path)
        except Exception as e:                                 # noqa: BLE001
            return _err(str(e))
        ent = []
        for e in d['entries']:
            if e.get('dir'):
                ent.append(e)
            elif _is_rom_name(e['name']):
                # große .bin/.rom-Dateien sind keine Atari-Module (Firmware, Abbilder ...)
                if not str(e['name']).lower().endswith('.zip') and int(e.get('size') or 0) > MAX_ROM:
                    continue
                ent.append(e)
        return {'path': d['path'], 'parent': d.get('parent', ''), 'entries': ent}

    def rom(req):
        path = str(req.query.get('path') or '')
        try:
            data = _rom_bytes(path)
        except (ValueError, OSError, zipfile.BadZipFile) as e:
            return _err(str(e))
        z = [x for x in (api.get('zuletzt') or []) if x != path]
        api.set('zuletzt', ([path] + z)[:8])
        return data

    def upload(req):
        if req.method != 'POST':
            return _err('Nur per POST', 405)
        name = ''.join(c for c in Path(str(req.query.get('name') or 'spiel.bin')).name if c.isalnum() or c in ' ._-()')[:80] or 'spiel.bin'
        if not _is_rom_name(name):
            return _err('Nur .a26, .bin, .rom oder .zip.')
        data = req.body or b''
        if not data or len(data) > (MAX_ROM * 4 if name.lower().endswith('.zip') else MAX_ROM):
            return _err('Datei leer oder zu groß (Atari-Module sind höchstens 512 KB).')
        target = roms_dir / name
        n = 1
        while target.exists():
            n += 1
            target = roms_dir / ('%s (%d)%s' % (Path(name).stem, n, Path(name).suffix))
        target.write_bytes(data)
        return {'ok': True, 'path': str(target)}

    def state(req):
        path = str(req.query.get('path') or '')
        if not path:
            return _err('Spiel fehlt.')
        f = saves_dir / (_id(path) + ('.auto' if req.query.get('slot') == 'auto' else '') + '.json')
        if req.method == 'POST':
            if len(req.body or b'') > MAX_STATE:
                return _err('Stand zu groß.')
            try:
                json.loads(req.body.decode('utf-8'))
            except Exception:                                  # noqa: BLE001
                return _err('Ungültiger Stand.')
            f.write_bytes(req.body)
            return {'ok': True}
        if not f.is_file():
            return {}
        return json.loads(f.read_text('utf-8'))

    def widget():
        n = len([p for p in roms_dir.iterdir() if _is_rom_name(p.name)]) if roms_dir.is_dir() else 0
        z = api.get('zuletzt') or []
        return {'icon': '🕹', 'text': 'Atari 2600',
                'sub': ('Zuletzt: %s' % Path(z[0]).stem[:40]) if z else ('%d Spiele hochgeladen' % n if n else 'Spiele auswählen und loslegen')}

    api.route('index', lambda req: page)
    for name, fn in (('config', config), ('browse', browse), ('rom', rom), ('upload', upload), ('state', state)):
        api.route(name, fn)
    api.widget('Atari 2600', widget, ttl=30, icon='🕹')
