# -*- coding: utf-8 -*-
# NES-Konsole
# IT('s) Possible 
# 2026.11.09
"""NES-Konsole: spielt NES-Spiele (.nes oder .zip) im Gerät - mit Fernbedienung, Tastatur, Gamepad und Touch-Tasten.

Der Emulator ist „jsnes“ 2.1.0 (Apache-2.0, https://github.com/bfirsh/jsnes), unten in dieser Datei mitgeliefert. Spiele (ROMs) gehören nicht
dazu: Du brauchst eigene, rechtmäßig erworbene Sicherungskopien deiner Module.

Öffnen: Erweiterungsliste -> NES-Konsole -> „NES-Konsole öffnen“. Spiel suchen: Ordner auf dem Gerät durchsuchen (Pfeiltasten + OK, Zurück = eine Ebene
höher) oder „ROM hochladen“ (Handy/PC) - hochgeladene Spiele liegen im Ordner „Meine ROMs“. Zuletzt gespielte Spiele stehen oben.

Steuerung (Fernbedienung/Tastatur):  Pfeile = Steuerkreuz · OK/Enter/X = A · ⏯/Z/Y = B · ⏩/S = Start · ⏪/A = Select ·
Zurück oder Menü-Taste (≡) = Menü (Weiter, Stand speichern/laden, Start/Select drücken, Zurück zur Liste) · Zurück im Menü verlässt das Gadget
(der Stand wird beim Öffnen des Menüs und alle 20 s automatisch gesichert; „Stand laden“ holt ihn zurück).
Tempo: im Menü einstellbar (100/90/83/75 %), je Spiel gemerkt - PAL-Spiele (50 Hz) laufen sonst zu schnell. „Zwei Tasten“: Richtung + OK/B gleichzeitig auch mit Fernbedienungen, die nur eine Taste auf einmal senden.
Wer nur OK hat, stellt in den Einstellungen „OK-Taste“ auf „A und B“ oder nutzt im Menü „Start drücken“.
Touch: Knöpfe auf dem Bildschirm. Controller am Fernseher funktionieren über ihre Tasten (A/B/Start/Select).
"""
import base64
import hashlib
import io
import json
import time
import zipfile
import zlib
from pathlib import Path

EXT_ID = 'nes'
EXT_NAME = 'NES-Konsole'
EXT_DESCRIPTION = 'NES-Spiele (.nes/.zip) abspielen - Fernbedienung, Gamepad und Touch. Eigene Spiele nötig (nicht enthalten).'
EXT_LINKS = [('NES-Konsole', 'index')]
EXT_SETTINGS = [
    {'key': 'ok', 'label': 'OK-Taste der Fernbedienung', 'type': 'select', 'default': 'A',
     'options': [['A', 'A (Standard)'], ['B', 'B'], ['AB', 'A und B zusammen (für Fernbedienungen ohne weitere Tasten)']]},
    {'key': 'gamepad', 'label': 'Gamepad-Schnittstelle des Browsers nutzen (nur PC/Handy mit Controller; am Fernseher AUS lassen: sie nimmt die Pfeiltasten weg)', 'type': 'bool', 'default': False},
]
MAX_ROM = 8 * 1024 * 1024
MAX_STATE = 6 * 1024 * 1024
_api = None

# --- Oberfläche (HTML/JS) ---
_PAGE = r'''<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no"><title>NES-Konsole</title>
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
#cv{height:100%;max-width:100%;aspect-ratio:256/240;image-rendering:pixelated;image-rendering:crisp-edges;background:#000}
#menu{position:fixed;inset:0;background:rgba(5,8,14,.82);display:none;align-items:center;justify-content:center;z-index:5}
#menu .box{background:var(--pn);border:1px solid var(--ln);border-radius:16px;padding:16px;min-width:min(380px,88vw)}
#menu h2{margin:0 0 10px;font-size:20px} #menu .it{justify-content:center}
#tc{position:fixed;inset:0;pointer-events:none;display:none;z-index:3}
.tb{position:absolute;pointer-events:auto;touch-action:none;user-select:none;-webkit-user-select:none;border-radius:50%;background:rgba(255,255,255,.14);border:2px solid rgba(255,255,255,.35);color:#fff;font-weight:700;display:flex;align-items:center;justify-content:center;font-size:20px}
#hud{position:fixed;left:8px;top:8px;z-index:4;display:none;background:rgba(0,0,0,.72);color:#9aa3b5;border-radius:10px;padding:6px 10px;font:14px/1.3 ui-monospace,Menlo,monospace;pointer-events:none}#hud b{color:#555;font-weight:400;margin-right:6px}#hud b.on{color:#6ee7a0;font-weight:700}#hud i{font-style:normal;color:#e8c96a;display:block;margin-top:2px}
.tb.d{background:rgba(255,255,255,.3)} .tb.sq{border-radius:12px;font-size:14px}
</style></head><body>
<div id="lst"><h1>🎮 NES-Konsole</h1><div class="sub" id="where"></div><div id="rows"></div><div id="msg"></div>
<div id="hint"><span>↑ ↓ wählen · OK öffnet · Zurück: eine Ebene höher</span><label>ROM hochladen<input id="up" type="file" accept=".nes,.zip"></label></div></div>
<div id="game"><canvas id="cv" width="256" height="240"></canvas><button id="fz" aria-label="Spiel" style="position:absolute;inset:0;opacity:0;border:0;background:none;outline:0"></button>
<div id="tc"><div class="tb" id="b_u" style="left:70px;bottom:150px;width:58px;height:58px">▲</div><div class="tb" id="b_d" style="left:70px;bottom:28px;width:58px;height:58px">▼</div><div class="tb" id="b_l" style="left:10px;bottom:89px;width:58px;height:58px">◀</div><div class="tb" id="b_r" style="left:130px;bottom:89px;width:58px;height:58px">▶</div>
<div class="tb" id="b_b" style="right:96px;bottom:48px;width:68px;height:68px">B</div><div class="tb" id="b_a" style="right:18px;bottom:96px;width:68px;height:68px">A</div>
<div class="tb sq" id="b_sel" style="left:calc(50% - 90px);bottom:14px;width:80px;height:34px">Select</div><div class="tb sq" id="b_sta" style="left:calc(50% + 10px);bottom:14px;width:80px;height:34px">Start</div><div class="tb sq" id="b_m" style="right:14px;top:12px;width:70px;height:34px">Menü</div></div>
<div id="hud"></div>
<div id="menu"><div class="box"><h2 id="mt">Menü</h2><div id="mi"></div></div></div></div>
<script>window.__errs=[];addEventListener('error',function(e){window.__errs.push(String(e.message||'Fehler').slice(0,70)+' @'+(e.lineno||'?')+':'+(e.colno||'?'));});addEventListener('unhandledrejection',function(e){window.__errs.push('Zusage: '+String(e.reason&&e.reason.message||e.reason).slice(0,70))});</script>
<script>/*JSNES*/</script>
<script>
(function(){'use strict';
const $=s=>document.querySelector(s),QS=new URLSearchParams(location.search),GTOK=QS.get('share')||QS.get('token')||'',GH=GTOK?{'X-Share':GTOK}:{};
const J=async(u,o)=>{const r=await fetch(u,Object.assign({headers:GH},o||{}));let d=null;try{d=await r.clone().json()}catch(e){}if(!r.ok)throw new Error((d&&d.error)||('Fehler '+r.status));return d!==null?d:r};
function closeGame(){try{if(window.parent!==window){window.parent.history.back();return}}catch(e){}if(history.length>1)history.back();else location.href='/ui/'}
let mode='browse',cfg={ok:'A'},cur={path:'',parent:'',entries:[]},sel=0,stack=[];
const rows=$('#rows'),msg=$('#msg');
const say=t=>{msg.textContent=t||''};
function icon(e){return e.dir?'📁':e.zuletzt?'🕹':'🎮'}
function size(n){return n>1048576?(n/1048576).toFixed(1)+' MB':n>1024?Math.round(n/1024)+' KB':''}
function paint(){
  $('#where').textContent=cur.path||'Zuletzt gespielt · Ordner auf diesem Gerät';
  const list=[];if(cur.path)list.push({up:1,name:'⬆ eine Ebene höher'});
  list.push(...cur.entries);cur.list=list;
  rows.replaceChildren(...list.map((e,i)=>{const b=document.createElement('button');b.className='it'+(i===sel?' on':'');
    b.innerHTML='<span class="i"></span><span class="t"></span><span class="m"></span>';
    b.children[0].textContent=e.up?'':icon(e);b.children[1].textContent=e.name;b.children[2].textContent=e.dir||e.up?'':size(e.size||0);
    b.onclick=()=>{sel=i;open(e)};b.onfocus=()=>{sel=i;rows.querySelectorAll('.it').forEach((x,k)=>x.classList.toggle('on',k===i))};return b}));
  if(!list.length)rows.innerHTML='<p class="sub">Hier liegen keine NES-Spiele (.nes oder .zip). Mit „ROM hochladen“ lässt sich eine Datei hinzufügen.</p>';
  const on=rows.children[sel];if(on){on.scrollIntoView({block:'nearest'});try{on.focus({preventScroll:true})}catch(e){}}
}
async function browse(path,keep){say('');try{const d=await J('browse?path='+encodeURIComponent(path||''));cur={path:d.path||'',parent:d.parent||'',entries:d.entries||[]};sel=keep||0;paint()}catch(e){say(e.message)}}
function open(e){if(e.up){up();return}if(e.dir){stack.push(cur.path);browse(e.path)}else play(e.path,e.name.replace(/\.(nes|zip)$/i,''))}
function up(){if(!cur.path){closeGame();return}browse(cur.parent&&cur.parent!==cur.path?cur.parent:'')}
/* ---------- Emulator ---------- */
const cv=$('#cv'),cx=cv.getContext('2d'),img=cx.createImageData(256,240),b32=new Uint32Array(img.data.buffer);
let speed=1,nes=null,raf=0,lastT=0,acc=0,paused=false,romPath='',romName='',actx=null,proc=null;
const RING=16384,MASK=RING-1,AL=new Float32Array(RING),AR=new Float32Array(RING);let aw=0,ar=0;
const fill=()=>(aw-ar)&MASK;
function audioStart(){
  try{const AC=window.AudioContext||window.webkitAudioContext;if(!AC)return;if(!actx)actx=new AC();if(actx.state==='suspended')actx.resume();
    if(!proc){proc=actx.createScriptProcessor(2048,0,2);proc.onaudioprocess=e=>{const o0=e.outputBuffer.getChannelData(0),o1=e.outputBuffer.getChannelData(1);
      for(let i=0;i<o0.length;i++){if(ar!==aw){o0[i]=AL[ar];o1[i]=AR[ar];ar=(ar+1)&MASK}else{o0[i]=0;o1[i]=0}}};proc.connect(actx.destination)}}catch(e){actx=null;proc=null}}
function wake(){try{if(actx&&actx.state==='suspended')actx.resume()}catch(e){}}
function audioStop(){try{if(proc){proc.disconnect();proc.onaudioprocess=null}if(actx)actx.close()}catch(e){}proc=null;actx=null;aw=ar=0}
function sample(l,r){if(!proc||!actx||actx.state!=='running')return;const n=(aw+1)&MASK;if(n===ar)return;AL[aw]=l*.8;AR[aw]=r*.8;aw=n}
function bin(buf){const u=new Uint8Array(buf);let s='';for(let i=0;i<u.length;i+=8192)s+=String.fromCharCode.apply(null,u.subarray(i,i+8192));return s}
async function play(path,name){
  say('Lade …');
  try{const r=await J('rom?path='+encodeURIComponent(path));const data=bin(await r.arrayBuffer());
    stopRun();audioStart();
    nes=new jsnes.NES({onFrame:b=>{for(let i=0;i<61440;i++)b32[i]=0xff000000|b[i]},onAudioSample:sample,sampleRate:actx?actx.sampleRate:44100});
    nes.loadROM(data);romPath=path;romName=name;initSpeed();
    mode='game';$('#lst').style.display='none';$('#game').style.display='flex';paused=false;lastT=0;acc=0;say('');
    if(matchMedia('(pointer:coarse)').matches)$('#tc').style.display='block';
    raf=requestAnimationFrame(loop);pushTrap();try{window.focus();$('#fz').focus()}catch(x){}}
  catch(e){stopRun();mode='browse';$('#game').style.display='none';$('#lst').style.display='flex';
    say(/mapper/i.test(e.message)?'Dieses Spiel braucht eine Erweiterung des Moduls, die es noch nicht gibt ('+e.message+').':e.message)}}
function loop(t){raf=requestAnimationFrame(loop);if(paused||!nes){lastT=0;return}
  if(!lastT){lastT=t;return}acc+=Math.min(t-lastT,100);lastT=t;let n=0;
  if(proc&&actx&&actx.state==='running'){const f=fill();if(f>6144){acc=0}else if(f<1200&&acc<16.6/speed)acc=16.7/speed}
  const stp=16.64/speed;while(acc>=stp&&n<3){try{nes.frame()}catch(e){stopRun();say('Fehler im Spiel: '+e.message);back2list();return}acc-=stp;n++}
  if(n)cx.putImageData(img,0,0)}
function stopRun(){if(raf)cancelAnimationFrame(raf);raf=0;nes=null;audioStop();$('#tc').style.display='none'}
function back2list(){stopRun();menuHide();mode='browse';$('#game').style.display='none';$('#lst').style.display='flex';paint()}
/* ---------- Zurück-Taste des Geräts ----------
   Im Spiel liegt ein eigener Verlaufseintrag bereit: Zurück (Android: Schritt im Verlauf) öffnet das Menü. Zurück im Menü verlässt das Gadget (zurück zu
   MovieScout, der Stand wird beim Öffnen des Menüs gesichert). Wer im Menü „Weiter“ wählt, bekommt den Eintrag wieder. */
let trap=0;
function pushTrap(){if(trap)return;try{history.pushState({nes:1},'');trap=1}catch(e){}}
addEventListener('popstate',()=>{if(!trap)return;trap=0;
  if(mode==='game')menuShow();else if(mode==='menu')closeGame();else if(mode==='browse')up()});
/* ---------- Tempo ----------  (PAL-Spiele laufen mit 50 statt 60 Bildern: auf 60 Hz sind sie ein Fünftel zu schnell, die Musik fällt auf) */
const SPEEDS=[1,.9,.83,.75];
function applySpeed(){try{nes.setFramerate(60*speed)}catch(e){}}
function initSpeed(){let v=0;try{v=parseFloat(localStorage.getItem('nes_sp:'+romName))||0}catch(e){}
  if(!v){v=(nes.rom&&nes.rom.timingMode===1)?.83:1}speed=v;applySpeed()}
function cycleSpeed(){const i=SPEEDS.findIndex(x=>Math.abs(x-speed)<.015);speed=SPEEDS[(i+1)%SPEEDS.length];applySpeed();try{localStorage.setItem('nes_sp:'+romName,String(speed))}catch(e){}}
/* ---------- Zwei Tasten auf der Fernbedienung ----------
   Fernbedienungen senden meist nur eine Taste auf einmal: Wird die Richtung losgelassen, kurz bevor OK/B kommt, bleibt sie gedrückt, bis OK/B losgelassen wird. */
let combo=false;try{combo=localStorage.getItem('nes_combo')==='1'}catch(e){}
const DIRS=['U','D','L','R'],relT={},latched={};
function dirUp(b){if(!combo){press(b,false);return}clearTimeout(relT[b]);relT[b]=setTimeout(()=>{delete relT[b];if(!latched[b])press(b,false)},110)}
function otherDown(){for(const b of DIRS)if(relT[b]){clearTimeout(relT[b]);delete relT[b];latched[b]=true;setTimeout(()=>{if(latched[b]){delete latched[b];press(b,false)}},700)}}
function releaseLatch(){for(const b of DIRS){clearTimeout(relT[b]);delete relT[b];if(latched[b]){delete latched[b];press(b,false)}}}
function dirDown(b){for(const d of DIRS){clearTimeout(relT[d]);delete relT[d];if(latched[d]){delete latched[d];if(d!==b)press(d,false)}}press(b,true)}
function keyDown(b){if(DIRS.includes(b)){dirDown(b);return}otherDown();if(b==='OK')okPress(true);else press(b,true)}
function keyUp(b){if(DIRS.includes(b)){dirUp(b);return}if(b==='OK')okPress(false);else press(b,false);releaseLatch()}
/* ---------- Tasten ---------- */
const BT={A:0,B:1,SEL:2,STA:3,U:4,D:5,L:6,R:7};
const held={};
let hudOn=false,hudRaw='',keyN=0;
const CHR=((navigator.userAgent.match(/Chrome\/(\d+)/)||[])[1])||'?';
const HG=[['U','▲'],['D','▼'],['L','◀'],['R','▶'],['A','A'],['B','B'],['SEL','Sel'],['STA','Sta']];
function hud(){const h=$('#hud');h.style.display=hudOn?'block':'none';if(!hudOn)return;const ae=document.activeElement,er=(window.__errs||[]).slice(-2);
  h.innerHTML=HG.map(([b,g])=>'<b'+(held[b]?' class="on"':'')+'>'+g+'</b>').join('')+'<i>'+(hudRaw||'Taste drücken …')+'</i><i>Chrome '+CHR+' · '+mode+' · Fokus '+(ae?(ae.id||ae.tagName):'-')+' · Tasten '+keyN+'</i>'+(er.length?'<i style="color:#ff8a8a">'+er.join(' | ')+'</i>':'')}

function press(b,on){if(!nes)return;const k=BT[b];if(held[b]===on)return;held[b]=on;
  const set=x=>on?nes.buttonDown(1,x):nes.buttonUp(1,x);setTimeout(hud,0);
  if(b==='A'&&cfg.ok==='B'){set(1)}else set(k)}
function okPress(on){press('A',on);if(cfg.ok==='AB')press('B',on)}
function release(){for(const b in kt)delete kt[b];Object.keys(relT).forEach(b=>{clearTimeout(relT[b]);delete relT[b]});Object.keys(latched).forEach(b=>delete latched[b]);Object.keys(held).forEach(b=>press(b,false))}
const KMAP=(e)=>{const k=e.key,c=e.keyCode,cd=e.code,blank=(k==='Unidentified'||k==='');
  if(k==='ArrowUp'||cd==='ArrowUp'||blank&&c===38)return'U';if(k==='ArrowDown'||cd==='ArrowDown'||blank&&c===40)return'D';if(k==='ArrowLeft'||cd==='ArrowLeft'||blank&&c===37)return'L';if(k==='ArrowRight'||cd==='ArrowRight'||blank&&c===39)return'R';
  if(k==='Enter'||k==='Select'||c===23||c===66||k==='x'||k==='X')return'OK';
  if(k==='z'||k==='Z'||k==='y'||k==='Y'||k==='MediaPlayPause'||c===85||c===179||k==='MediaPlay'||k==='MediaPause')return'B';
  if(k==='s'||k==='S'||k==='Tab'||k==='MediaFastForward'||c===90&&k!=='z'&&k!=='Z')return'STA';
  if(k==='a'||k==='A'||k==='Shift'||c===109||k==='MediaRewind'||c===89&&k!=='y'&&k!=='Y')return'SEL';if(c===96||c===100)return'OK';if(c===97||c===99)return'B';if(c===108)return'STA';return''};
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
    else if(e.key==='Enter'||e.key==='Select'||e.keyCode===23||e.keyCode===66){mitems[msel].go()}else if(isMenuKey(e)||isBack(e)){menuHide()}return}
  if(mode==='game'){wake();
    if(isMenuKey(e)||isBack(e)){e.preventDefault();menuShow();return}
    const b=KMAP(e);if(!b)return;e.preventDefault();kt[b]=performance.now();if(e.repeat)rep[b]=1;keyDown(b)}});
document.addEventListener('keyup',e=>{if(mode!=='game')return;const b=KMAP(e);if(!b)return;e.preventDefault();delete kt[b];keyUp(b)});
/* Sicherung gegen verlorene „Taste losgelassen“-Meldungen (Figur rennt dann endlos): Sendet eine Fernbedienung beim Gedrückthalten Wiederholungen, gilt eine Taste
   als losgelassen, wenn länger als 0,7 s keine mehr kommt. Fernbedienungen ohne Wiederholungen bleiben unberührt. */
const kt={},rep={};setInterval(()=>{const now=performance.now();for(const b in kt)if(rep[b]&&now-kt[b]>700){delete kt[b];keyUp(b)}},150);
/* Gamepad-Schnittstelle: nur auf Wunsch (Einstellung). Wer navigator.getGamepads() abfragt, nimmt dem Android-WebView am Fernseher die Pfeiltasten weg:
   sie landen dann im Gamepad-Zweig statt als Tastenereignis. Controller am TV melden sich ohnehin als Tasten (siehe KMAP). */
let gpPrev={};function gpStart(){setInterval(()=>{if(mode==='browse'||!navigator.getGamepads)return;const g=[...navigator.getGamepads()].find(x=>x&&x.connected&&x.mapping==='standard');if(!g)return;
  const bt=i=>!!(g.buttons[i]&&g.buttons[i].pressed),ax=(i,s)=>g.axes[i]*s>.5;
  const st={A:bt(0)||bt(1),B:bt(2)||bt(3),SEL:bt(8),STA:bt(9),U:bt(12)||ax(1,-1),D:bt(13)||ax(1,1),L:bt(14)||ax(0,-1),R:bt(15)||ax(0,1)},home=bt(16);
  if(mode==='game'){for(const k in st)if(st[k]!==!!gpPrev[k]){if(k==='A')okPress(st[k]);else press(k,st[k])}if(home&&!gpPrev.home)menuShow()}
  gpPrev=Object.assign({},st,{home})},16)}
/* Touch */
[['b_u','U'],['b_d','D'],['b_l','L'],['b_r','R'],['b_a','OK'],['b_b','B'],['b_sel','SEL'],['b_sta','STA']].forEach(([id,b])=>{const el=$('#'+id);
  const on=v=>e=>{e.preventDefault();if(v){try{el.setPointerCapture(e.pointerId)}catch(x){}el.classList.add('d')}else el.classList.remove('d');if(b==='OK')okPress(v);else press(b,v)};
  el.addEventListener('pointerdown',on(true));el.addEventListener('pointerup',on(false));el.addEventListener('pointercancel',on(false))});
$('#b_m').addEventListener('pointerdown',e=>{e.preventDefault();menuShow()});
addEventListener('touchstart',()=>{wake();if(mode==='game')$('#tc').style.display='block'},{passive:true});addEventListener('pointerdown',wake);
/* ---------- Menü ---------- */
let mitems=[],msel=0;
async function saveState(){try{await J('state?path='+encodeURIComponent(romPath),{method:'POST',body:JSON.stringify(nes.toJSON())});return 'Stand gespeichert.'}catch(e){return 'Speichern nicht möglich: '+e.message}}
async function loadState(){try{let d=await J('state?path='+encodeURIComponent(romPath)),was='Stand geladen.';if(!d||!d.cpu){d=await J('state?slot=auto&path='+encodeURIComponent(romPath));was='Letzten Stand geladen (automatisch gesichert).'}if(!d||!d.cpu)return 'Es gibt noch keinen gespeicherten Stand.';nes.fromJSON(d);applySpeed();return was}catch(e){return 'Kein gespeicherter Stand.'}}
function menuShow(){if(!nes)return;autosave();release();paused=true;mode='menu';msel=0;$('#mt').textContent=romName;
  const act=(f)=>async()=>{const r=await f();menuHide(r)};
  mitems=[{t:'▶ Weiter',go:()=>menuHide()},{t:'💾 Stand speichern',go:act(saveState)},{t:'📂 Stand laden',go:act(loadState)},
    {t:'Start drücken',go:()=>{menuHide();press('STA',true);setTimeout(()=>press('STA',false),120)}},{t:'Select drücken',go:()=>{menuHide();press('SEL',true);setTimeout(()=>press('SEL',false),120)}},
    {t:'',tempoItem:1,go:()=>{cycleSpeed();tempoLabel();menuPaint()}},
    {t:'',comboItem:1,go:()=>{combo=!combo;try{localStorage.setItem('nes_combo',combo?'1':'0')}catch(e){}if(!combo)releaseLatch();tempoLabel();menuPaint()}},
    {t:'↩ Zurück zur Liste',go:()=>back2list()}];
  tempoLabel();$('#menu').style.display='flex';menuPaint()}
function tempoLabel(){const a=mitems.find(x=>x.tempoItem),c=mitems.find(x=>x.comboItem);if(a)a.t='🐢 Tempo: '+Math.round(speed*100)+' %'+(speed<.85&&speed>.8?' (PAL)':'');if(c)c.t='🎛 Zwei Tasten (Fernbedienung): '+(combo?'an':'aus')}
function menuPaint(){const m=$('#mi');m.replaceChildren(...mitems.map((x,i)=>{const b=document.createElement('button');b.className='it'+(i===msel?' on':'');b.textContent=x.t;b.onclick=()=>{msel=i;x.go()};b.onfocus=()=>{msel=i;m.querySelectorAll('.it').forEach((y,k)=>y.classList.toggle('on',k===i))};return b}));const f=m.children[msel];if(f)try{f.focus({preventScroll:true})}catch(e){}}
function menuHide(note){$('#menu').style.display='none';setTimeout(hud,0);if(mode==='menu'){mode='game';paused=false;lastT=0;pushTrap();try{$('#fz').focus()}catch(e){}}if(typeof note==='string'&&note){const t=document.createElement('div');t.textContent=note;t.style.cssText='position:fixed;top:14px;left:50%;transform:translateX(-50%);background:#161b26;color:#fff;padding:8px 16px;border-radius:10px;z-index:9;font-size:16px';document.body.appendChild(t);setTimeout(()=>t.remove(),1800)}}
/* Auto-Sicherung: Zurück beendet das Spiel sofort, dafür sichert die Seite alle 20 s im Hintergrund (beim Verlassen reicht die Zeit nicht für größere Daten). */
let asBusy=false;function autosave(){if(!nes||!romPath||asBusy)return;asBusy=true;let body;try{body=JSON.stringify(nes.toJSON())}catch(e){asBusy=false;return}
  fetch('state?slot=auto&path='+encodeURIComponent(romPath),{method:'POST',body,headers:GH}).catch(()=>{}).then(()=>{asBusy=false})}
setInterval(()=>{if(mode==='game'&&!document.hidden)autosave()},20000);document.addEventListener('visibilitychange',()=>{if(document.hidden)autosave()});
/* Upload */
$('#up').onchange=async e=>{const f=e.target.files[0];if(!f)return;say('Lade hoch …');
  try{if(f.size>8388608)throw new Error('Datei zu groß (höchstens 8 MB).');await J('upload?name='+encodeURIComponent(f.name),{method:'POST',body:await f.arrayBuffer()});say('Hinzugefügt: '+f.name);browse(cur.path||'')}catch(x){say(x.message)}e.target.value=''};
(async()=>{try{cfg=await J('config')}catch(e){}if(cfg.gamepad)gpStart();browse('')})();
window.__nes={get nes(){return nes},get mode(){return mode},play,browse};
})();
</script></body></html>
'''

# --- jsnes 2.1.0 (Apache-2.0, Copyright Ben Firshman und Mitwirkende), gebündelt und gepackt ---
_B64 = (
    'eNrsvetyG0eyP/idT9HD47WBEQgCvIu0ZgK8yOIMRfEQlIa0w4duAg2yLdwGDYiiPZrYT+fzxj82Yh9oH+C8w3mS/WVmXbsbQBOiPT7/tSMsCd'
    '1V2VVZWVlZeS11Jv3WOB70S+WfP4Sj4Pq69+LnT5Xr6xb+2tMv8XhUel/+Oe6U8Oa799+XR9F4MqLn9KsafRwORuNkjyD0XsjDFz+rp7s/f/q0'
    'B7h4VurpppVeeU/BMM/2Pi1Rs+XrqD8ePVR/TJa/f2GGZ/oN2pNuVP55qTXoJ+Pg9KgZvODhLfejhPqUq+2oE0664z3V5GAAcINuNxrpli3zJN'
    'VBfaQqUPGnfeRBsT/2lpaWPu3JuNUA5g/64OytGcpw8rmDlg5nFuZwOFmN++3oY37DhtMynNn0m7AXfRP140i3v8WDW3qQ2/z8zWvdcDTopZos'
    'tbphkvB6/bwUBNxjNGmNB6PSYDhOyvw0CMZ3cVKlB4AkT4Jg0H85wod3A0OOJTT/VDGvG5N2PGiGvWEXjfqTbte+ao7D8SR5O2yH4xkA9sPxOB'
    'o9nIe9v43ivIaqZdSbdAGoOZj027sBxh9pGAl//Zy/srFTq9UqwepqwA3Vu2CEl0HcD+5+0uCqVZ6qwAAVWQxMYmf+9zQmhQKDn6rCih7AhKco'
    '0/WbuSgwnzJfAgHiU/3onqiyRI/KztuheXuW9za0rxs5728d+qFGhp5Kua0w1oO7sH9LzYH3F38yI6xey/QOwtF4FLdvo5NB2I5GHpheLxzSd7'
    'D87vTMrnEpqr4rMzYvS2WNx7Vpr7z16QwTxv4BFngMwDXnk6D9w3AcmrG4q1p1l6m0fB6F7YdgPAi6mE8Q0g6qLvOkPlE3UNB5lETYDOO7KEge'
    'knHUw+MRPSt5O+YXWEVuEHeCksXuH17InMoGkS7m9eSrrVGEOb4Oh0O7RJ8cNIARjF8Ok4u4F2UXLAezzjRHYXIXtfG4E3aTyEXUBTDUoY7A5W'
    'BYZX4YJ0HY/hD2W+gS97txPwrCDjZ6EH3Abmc2fDNJggHGGdJuF0gl7FGiOVqTVd57q8NJcoc/MPNq0BDAre6g9Z7hAkb3vQYctu4ESqz4GzGR'
    'zmAEhtcb4iM3cTcePwT38fguiLGwijeM417cv8XQb+NWFQBkJnob/OyvhcKCuwqjwT0v4NFoBIaqHgfBMu244C7EcKVPNTgIu11DQRgXzRJkhx'
    '8gQzwfY4tVl/VuMKuXt6G+q39fZTR4+9BtsJbXANRY5c/wOutX3WgctB5a3SiR33KkCF1rEnffDO2bYepN6LwK9TtIFAZftB6lvT2LQEEuLboM'
    '4WLwKuyC+kDvNbcVr+zRx6g1ASsPmYCcdRaiUxTXgxADzGMP9BNFfD4YdIzbEe9sjwiToJRPeU53GSUmSUNWh1JJ71nzhQNCPdMrkxt9qQNI0h'
    'vIwgarOvuGH4CGSWSRzeDASiY341HYAsWG/Qf9/bA7YgZmNtnNA3+uFY5bdyuToTtkWgkhBru9wR4EUoUnghYH1HMyPOCnijLUlHMaOOzBTvou'
    'wqSxnO/2u2H/fdCJRxhYezKi/aWYAC0TeOlwiGfuGIkIiDoZH0cQi9r+4geB/9blQ/a/GyDlvfvok/n3pyBC8zRBHb5ugFK6mv53eWw8SNCEPJ'
    'zGdtzR8w66m2DOL4LX4fiuCpaSoelKsOOhlbcC9YwZmfjrawGCfz57ljd9tdiHg3FSWi/nz3P6chPozLp6m27lhRpAqtE1/uBl3w+Bwmem1a+6'
    'fkvu35+E0INSlDoQ7TFFIuKex6WjDEf1Trxnz/hQ42ndTMbjQf9wcN+nk8Dy1Yp645wNGc5r//191cIpqY7pb7wdPsUX3g6z8H9iKeD14AOfZh'
    '8rwUPqRPuDESHKgVwIUzJdVUBcov/H/FdXePWQ/uRL7HuNugU/+ZJZh13ENHjB2mcCt4IMQ7+Nxi/Pmka4kxOtD7p5EUCojKr4p3tignY8EcrI'
    'CI6MZYlTWueIWRB6SvSRlSDbeTWo4zpTnk22KRE4JeEN7uWduvCjp5HcRpEVQFJijpajp0idup/b1hmllgvpppCIaI2zoEs3MAg6dBbS6R3ieg'
    'ZGW7UypG2XBB/CbkzieptOkWRMrfRX2/Q1NSD1FdN117sLKNFaD7Xs3xR4GgLNFXSVgJa93swUsi2NGaSm5a5o/DomGREnn8Fc9dZ5evEwhChR'
    'zr3P0DBdmbvR/nEC8gzp+p2SZOlcCbHy/RWIev12OGoHdwO0FVGDrsI40sa0DgJK6QmCrRoRKYnR0hRkMRxBe9LCaf9P3KvVZ7CiY9yz37/6qR'
    'ocd3g5CbzAakHETUx3NIZ0Bekcl/moelsN1ukT5YrcqcygcdL2aDIkLwS9wUiNqzOK/j6BKNd94MOYaEbEp2TgjBIndgzBCovflbuaoORm0ulA'
    'XQNIwDtvFpp4if7wbm98WOom56aJQfV48Jfmm1OzQ9Q20rsBo1RLtOstmJbhcW7u2pu0hqXfErnsOpSTfj80vYc5vWnku84k0u+dA2PXOYrru7'
    'mXiXRvvo3nXSrSDT85eg3GWAc44Ca+YsnbVsBbir7Nv339SNVCo5+Zzea8Zr6f2nPO66Hfm1Hmvg7Ne+KC3rQt98u8AurKufh0x+0335sKay0P'
    '1tpUWGvfezwXyNcKU72jlR7VqkmVynO+mvRns4wVtQUgcikF4wQbTtS9AI2VfPGE/xG8rc3aGu5krQFd0cKbbvQLfGRJHTnAz1eJXCbppHr9pi'
    'mfhzY9DnG2loijnMetwV2w1qitQ18ZnF40D1g4GNDtiQDhzTa9OWucQElxEr+P+KYGqBUoGoLRBBfLHhgW3X94VrirjaIhHSJtMLdONKZ3twQq'
    'xLtxxMgPehF44UMF/BmdiLHf34XEtvEHN+pFYR/XNzpHI74XUxvi6sSHByNsuOGgzx3NBTf47//z/2YmyRrhuCXfXuEvRCuRul2zFkch6U2f2x'
    'NSKkp3UzLg8PF2G99J6COgILDWYRiPGJd4eNun2xLurZAFCdakH4OhB/UVHr6scDV4ieMq+siHQSVYPjlsLAclPtMbrdaE79eDUZkVKVF8ezcm'
    'QO2YmDvd8hWZEMAkuIla4QQXFOA8mQyZrqVPepgJ42HQZ1TRcbnMSkDGeoij5CPGvSajVD2XK9Q82/anaDRYGYa3DEm1DZ4Fl8uyLjipSDdxQW'
    't2G3+gsxPbaRx2cSoGa5tbuPBjVCBxbyJMVGhwfxe3RHcw6HTiVoxuTJzY3iClJKhv1vfwmQFajOiEDkKcn8uTvm69zHAYMDQbSQTwEPnuy3sM'
    'kxRO3GPSB9LaPN77waQLaQGKYAwUUk6XiLhq9gvWlYQs7Bij+AAVju8GWGZaP1K8yCE8la4IhULotBrdKKvIeXN28Obw6PqisX9yRJRE4P4okP'
    '7I1/NdRmVfk7qDueA+Clgs4s9Hbd5+44gkAztgJuLxHeskIN9HEWTU8YAgvSc5/CbCCCPatH21n9zh7SpcBPSQeO+KWiVX5wghV0+5dHzavP4j'
    'uMJbRrHSJkMnhC7vowcBZS/Rstl05+EdXbdBCGbwVelANOx8O0Xd9H3aBvgLdNIWAqIti3+XGoeH5zSg1Jfzh6cH5Hxg6piS+CcZ0x2Q2CP+J5'
    'syhcBggF09jCNSzCkOF5TqK+vlSmpEJOSZNaOVSRhyB2ZOTExpQhg6hNRbSG9aiabGo/RkK8ENDdjTuzUHPW9MCbgWNGl9IB6KNtX2/i7qp4aE'
    'FmywI1SlUN4aYSPz9sauFs6xTGxhObghO1Q4Si91CX3V+HlPE3/DvNoDOw5STcpY8IIZemusid757w4cTqh/0HFXqywsyCUotbJokPA5koKUmj'
    '52Aa44o8EQRyHuDPpASG1PYUZMPGEw7IZY1sHNjzRUaNtBdF1hOhWiJ1FTqimMwntv75ZqK2ubm7RV+ubwEBIiJpUQg8Ei3STgMXt0BWnHyZB0'
    'QASLLhE8U7CY95OhEtOT4AfgXsb3Q0VvVCbJPh3A3ZAUp6ygDQlKcheSYuD49F3j5PjwWmYa0AcBoUsUyYdv3OfLqeGsHVLrk4ZpgoUQTpJF+l'
    'eJuWe1iCBlaaCVqjrSCDMLfiXbFHdv3FtwTOODE3yJ14SvSj3WftFnfmBwp7s/BN0QmE6WWL/Nr8b3A/V12W52y9LF7WEwYV4ITOAzN/gH+iQ4'
    'g8VORnBucLR4EEipSCy4yoLfyhP+t8R3Wv+U/gW+oTFt9lx9PV84sCLGffhAl9ggGUatuPMgghhvjv6Sb2z6KjF8tkuHveI0AnQcklhoNgWvaA'
    'U0RVdyaPJZEnHlD8Ub1eBUS7Jksf2jb4QN1Ym53LA7ScywwKgA+TZOyLBQuiSD01VZiyWABSNuxFNs0biGg5gtEAmkLdFxywBc8syjRhYg1OHB'
    'pKjpMHt2rBAieJ8pNjQWKoVQ4J4neqOquSp5Iu4DaRHWBJj+4ElbJWVJk4YefssssLGuwD2C1BGv+JD7BsJq1O2wxC7mGWZPPBOMVo071noGCD'
    '4wFIV6QMlgMmqJjMiSOn+XTwcYbyZgEg9g75jPoK8tT5BP+q3upO0I7rQ0xM2SFVjbW+8fguX2pNd7YBpJlpXgpgVBEBu+1mOQ+mRiatOrdjoY'
    'h2rK4MG7wReXl3JtwIorMZwRRcz3i5cvgXu0cNqIEEyQ3GZoWA2Wv4XoG8gZF+tFgqaOxVrh21hVfcJ/AT1mjTc5/sUfssItT6XlkLRwZC0g8i'
    'hpS0LqY/VWSBTNFECk3AvZU0dui5Bcxc5WxyEcG7nfIqQJIfhuPB4mu6ur9/f3VYjR7ehDdTC6Xb2P38erkEavLcVeCxtSd2Lmyd+eibHGPTkN'
    'JswTvl4oVgBKwJwvL10o50cnAFP3wJxHXSalwINydoDrhDoNd3hOkO6hSQlKN4BOfLnsAj5+TeNb8wAf4+SM0d0H3B9YoZB1cwcnB5Xg/KJZCS'
    '4alx7Qxj65ZK17QBs3uP8SK5o6ZyakEgmCWiDxYB4cAOaGD9Ne+HJgKiJrWKYmu9WfPrlBbaam34vaJMHkjpSv/UZSYTkEV9Dg377YWCv7605W'
    'kC0Psln3ymU+Dkq033AbLAdfBtg3PjwynWxPgXc1E95VDjysEQ1wxwWo18gML3+NMMAUJBra81xIV3MgXbmQzs6Pjg8vj08PidbVnikdQyVBkm'
    'wFWDGQ9Onj4Qxs9yeNEQ/sm+aFhSubyIAt6yGmwBJUF2BFpMDUiAFTiL1ut5CGTLKnkHwWNFH6X7D1Yt120O8+lH8RIenYubf8GgISuLnRPrh3'
    'poqcb0DeBxKQB30+4FikIAFC5GBI+2GwvgJzGeGq18dp0IcAQVusEjQv8AewBkjjVhVHymuyUnj3MqXG4YORZFWMIS2tVUTJElnok0QOW+iD+U'
    '6le4q8LsMaKzHP3Anu7x78qw2fmIwBsKRxTKYK8o2lm+tQjh87HeafxDaMlsqqixhL6euio6Eq66PpiBrKDYAlK+JMdKwDcyT7wGEFaO7EwOPE'
    'uay7Mhca518+UsI/re9gBPmPxkMbOCXYQabj43WE42aEqytZpOXaAYMSKwWSh35Le7YYwcgIHW8ujnZ5FKJdJcXpKutISdcz6MVKR0Qkhtf7B4'
    'c4zCDfjR5WaIHapPCMcayXGcmsI6QRH5wcwiDaPDpMkQibf6KPMWmz6FI1uCWpgT5wGHS64S0b1DVe5BGvEw5AkSdJemocHqw29w9EVfeVkMNY'
    'PrpKn4Rg0WZHRkGx1UzQhRPnB2T7/mBlMCTFJ7kWsVTe6cbs5yLCEb77CClEWfFAaiuugGpEdrmBNSB/3pHA2MKJwB5sipsRHWFOVlahH0TwuG'
    'NpoYzUKM6Jy8vZCkdQVTgwhMkqGPhBMPbj8X2M6wb9VrBEZLPQXBDNEyuS0A8ehh14chd3oCyIOqRtx12AZJz//s//JUNhGthXkg735P2E7Utq'
    '5T5Z/8idU1aVlv/HSQ+LMNKyFOYICQqmlljdmSHO2aHtsxCiBBv6wbPjr1EfHgFU5VE48jo1reRCP/I6QUJzuxz9uxVL6IffBWZObPASn008Ef'
    'Quu92PL6zsQT/UIjAadoNToOv/Cl5XtyvBO/XPrUrwLf+z1ABhvIafBAjBhfj62Eof9MMfEMzIwGmpH90KFnMHdXpk5Q364YOAVjo7L0alB+Ts'
    'xIoa9MMHwvfZ1DCyMM7/auUL+kEwmrA639PdlPnnaDIEcZE/H4jo7ODZmlwdmHQqimQ+xCHJVC+PPNjvDqyMQT/88cG1ZtShYyJDI+8cIYJ+TO'
    'lHZIIWL83EXOqEQE5AhDzpBwE5oFaKyAgfXnveqxuq/aHTXnFUwWDJ43zg0ThCI+JfpFi4wdjKHlCilPqmAnrsALWohSqO7HTZAb2jvluq7zun'
    'r8EAd6HX5KM7Unuc+al2e2T+zQIVoYs7gCjaULeM6XSASkbdiuVW4A2eb0N1oXP6wQOQLxXgXAcs89eFxunHtO6XXieSnuvPVaerqZ2uaNqHEZ'
    'xJ2GzigDg8ooVfE4qmHwTCtNRAIFuRBcvtRsNdq6tul6lul3k9aKxra6rHVarHle6Bt5dvzp2OR2/OqaOQJv1wj4XoI3QaCTbsCl5MwzJLsjlz'
    'Pz7luQsR0w+CbFpOnfvxKc99U3W7THW7zOvBc99SPa5SPdy5/4UYhNP1L3LJFrL6iyKrt/0WWVtFEmae4vZoMr6EkugH9SCwLJ9ObqA7Jh2z4V'
    'HKzcTo+Eixwkchu1Q5gEnoBGChNvpBgNl66h7tjjnZ60s4W6+pvpe27+XUHoSz9brqcWV7XHk9SMShU93tyhhYF1I7URg4IYkF2BIRYMSm2hKU'
    'zmOAyooBpyRgOSBP39AyrAsR0g8CeTpwYgrIXOGS7Ztzwta6EBf9cMl2NrEibAS+zbI87BQOHrRMfxvtF9+YwIB6YiUeDobLLi86e8XfFgqlH6'
    'zdATxvpQbkIZfQt7yuPNEt1fXMdoV1Bt5ZyWCk5aD8/if8aaFX+iH9ITZniCTblT+9o7qe2a6ZTzv9KXiGNI9kdtaGEbWOFvT5Gzr714V06QeB'
    'lm4iDXo9g9IBkwORBQK86K9tfnDgwyQq26gpmOcuTCGvqUC3BWhNA+UAILYiufAv6DTckA1APxi+cq2k+XviBhGJQg47O/pDvWAxck2BamZA+W'
    'yBYJ3JsJrqYHSA4epCwGQr0A+WgVQ7TdZiKUhL/DcwLA7ujRRCIU8uYD6KNmTHNNVR1CRv9zwJhG5KaL2pWh+a1ovLH80jxviWAnlsQE6RPnir'
    'QrvvTeKC6H9D6J9+MAxq5aEDOyfD8ZoXxCM3dlTXS6fr5ZQOxCI3nqsOV06HK6cDU5dSY2KR+gmude6QoYKlG4MQMv0gMBeqYXrUl15H+v5mXX'
    'W8mtnxyu3I+sNNoUf64XVMhP0ppVf6m5eE302hPvrhdb1MXTS9jrQHNjdUx2ZOR+/Dbtcr/qaQGv3wul6lv/lLaOLeGkcbbQr+hfVxXyWesUp8'
    'YsTbiqxlpENR4kcrHrUm5HoWsm8Q20XYxK3s4+xWJ7ZA7DiI13AeUt4DU72S1PeUZs/TwbAS6J4UE19RDNhorIHlaQ5ZiieRnjU37M41CP7Idi'
    '9yyvkjr6TW4XkTY6iwaefqI41DgwR+Me2QPR+/R22+CoqarnnyBoSzTIoI1gBDDECstFhqIYegb5t4EkGi6FjlYNcbqNhxunKTQ3lCsYradgf9'
    'DT9nyz2oDlz34QAkCzMXdHVK99QDArvxDfshdx9YbRkatw6KzY70zlS+IMalinsX1R2diTcMeYJfE4O/tv5g15pM1YXrRhw3jCpmlTVI2j7p8o'
    'pSbIwoWukvGm5HzXNCR++mMGr6UWo0z8ui7IGeiHENuW8XOiAK3SC9xL8Bajn405+CuqdxohNnU5g1/XAMDgAkt0EEbpBLzJAUzgnUs9gZIhFw'
    'hEFGiXXOQxMmTj98kDI2SAsVORFh5590Y1xST1ffrR4ErM+T88rl0A3hXcLo6UepuU8mDQJ6qWeIBys8TQR60Z32gLTdQvt0RqnRl7314AhEfu'
    '+Kz3webClZveHI6g2mOk9iJ2cZgA370WCSdL3TScDI6dBsuMeZHm/qjArbK3LJXuGgSN6OAziUsxqOzdlgLeev/0ZUo/WKhE48baww6jyZ/fCA'
    '5MktdeM8EHmSrrhuX7qp80o03Ptak+hiSw4Z+lE6bu4LfdE10e1PAhCjw+1/zkLwlpw150oIJrHT7UnUkPnyOd8atuSoOT/XPc/9ntCvZnoKr9'
    'lSwgt+MMU1/W/SPSTb85y0a1tKZDkX7Rpdm9yedPFWPdHqNZkpxKaPy5D4L5DnG2BCva99ysShioy+dEs5/ua0rDToypdAjgnxOVDfItcDoVpR'
    'urC/KV+ZQpHiSMaFkp4CnhPy74MKXMxB7PSbRML96HtDMLtYu+OtsDsezot2m4NBndn/dZ9mr6Qu/KDZr5m5wXnufTwU84jhS/TS5UeYGsGQ/U'
    'k/CMa6hSGGC546+1Z4F1ga+PJbgKJzctl4et0j0AUEPRkPCRnw4O63jTuHMdSQ254ynehL6E00vo+IsHUIS6KMXYlsPWPR/jIo+e584QgBQrBS'
    '1sviZ0miwOHrAxXk0sK5Ds80cD+KY9VyJPtS3MU/kuCkQ5x7cdu1I2jviZbkfGCvT3H8ET8P7SbuHElk/0g4PEGmGiqPmSkmp2pwlLDnHB/j/Y'
    'E5W/lQ1VRB7mZEWMr5xT07zUnLXMajDr5Jbysmhh+lxqvLssPKmJMRLl89q3t3iVfEsrfXVEew7ItGU3UktsT9lGFYVgaP88Cw6V5dtvCj1Lxq'
    'lD1BP68Tcd5tdZHCj1Lz0uuUN+CTBnGB7U3F9Y9gONUDJhQQRB54Se3UL/FTrM5vPIq9ie7CD/Fg5NJsGCz3Qhz3yxLoGPZVaAFFPrAvPZMsn0'
    'ygWjj0TjrkxsQ2Q45oKHHgATlih+z9insY1jTqsfZlMorI0KjMNMIJQCAj3v288CoPQx9bKaHD5wVp3yvkpWb39AvynCkrdzuiMR6xdUdqkQ8w'
    'LsYkwSqJU05Ulq7uuUEwhBsVx2NgmyfgSyTXMpyqJ3UwppX0gh+ly0bDYhrj+4d0KivaokPdXSm+Am0Lv6YfpcbFpb9SPgzu/0vcSti4mwqe+Q'
    'XuJGk34JTvr3H2dW4QYAkcPyLes3Shcdz3SeYlz2dKP8X27z3EJaT8gEuet1zw1+OT1ebF2epfGq/ZezLsxd0HdRfJi2MoZx2JhemzFyLhyrBY'
    '7VuM1pI4yBp8oZbBqTFmz8SUp/Cgr+5XbLiOyWtT/Atocj+A/e4GK/UfmChCRcE8WmWYJC7JzryxiW3weSpTtRlaJ5SIR+13zNNI+xgLcx6R93'
    'woFqZg2fdfXg4iCj/V14u37KQQTvGFVqtbcu+VHA0rnRCxmbA/NllmKWZTXTcJF2XlVPhuh7Q9NBw5XXFSteHaIBFJLCSQ17Ha47GEpegRCziL'
    '1qg7FN3rX2AURXIsvlspB8FAO3sQyLGzpuYiRQELfAja2ICE5NvIUkUq7gbhidD/RnLR6xnnc3KN5VtYQDewrxIhJo6TnWPld71rwaoxDG9fab'
    '+0mOLHRpR74gc0hhA1HsfkGHDbx8nxg3ZMX3Le8aFJwloLwYLwg9Hss08WWTyb9MC2uwDA90vxdSG6vIl0INqNxB0kxEIhN4SsPW1TVD9BWu4x'
    '6ShIPfg2J3YbwVdEMNPjSBpIVwKNqMUlUpI3kf2LPap5w4KiySHe8FWP9pBCKlB7qMJuIbukCKawk90AT3QCjzWO5s+iSQH18CtZqYjjO94Rjh'
    '9EENQ+bj3f1R9WThX669rjsGJCVngsa95YKgJkcyaQb88qwVQg6xrI9jwgl9NHsmFG0p4JBN5vKSDrOUC25wIxQ5kB5Pk8IFfzgWzVZwIxHoiV'
    'HJxsmZHMAWL8DStZIJuBpKhjsSHrHpMxJdH31lIzJ8CPJqm1zZlAipHU+jwgRUhqrT0TSDGSWp8LpABJrT+fB6QASa3VZwIpRlLrc4AUJalZ7l'
    'L8oVrof6h54k/54CCF/HoOLdW2ZgKZSUubGkh9HpAZtGTwVotmT2cWLRkg9blAptPStkX+NLezcBGnMxrX85o3rv0Dn88gKKDAvr9JA2kuAKST'
    'AnL07wsAWU8BeX28AJB2Csjp0QJA6ikgZycLANlMAXm3yOpsp4E8dnUU6SknP7pAk2bbjZYNb0PS5GRPlQ3/08cXCxwIa62ZQObzcjX+qW54ss'
    'tTWDr/a+oAPJvOtJwN6rrNMRnseGA5oKUoWEuQaSCHCwDZTAM5XgDITRrIu0cCESwV9HujBAHjRLnXiXGHBtHyj1Q2YDxaVmltzgRSjDTb84AU'
    'kVVa7ZlAiskq7blACsgq7efzgBSQVVr1mUCKySrtOUAKyiqzHSTpQ5G/7Q9oxR5NS9HGTCDFaClqzQRSlM3Ndu/kBUpP+WqR7bMxE0ixKbdaM4'
    'EUnfI8d1T+lC8JossC4mR7HpAi4mQrmgmkmDjZngukkDhJHrl5Xrb09MpDX5j63uUCh8fOTgrI1UKHx0zf3tzL7YbP147IrP5oit/YnAmkGMVv'
    'zgNS5MDYaM8EUuzA2JwLpMCBsfl8HpACB8ZGfSaQYgfG5hwgBQ+Med7dzKh9LoAuC7CSzjwgRVhJFM0EUoyVdOYCKcRKyME9z2k9w0qindT3Fm'
    'ElrTSQxVjJdEd5mBJ1aC3kUArEMXG0yvFPZNEN/wj7y2OEN8MVtmYDkQjgSj4Qh3gXduLnW5YvFQDWI2lJ5Vct4u9P3wt91sHRt4/myeHmTCDF'
    'ePLNPCBFeHLYngmkGE++mQukAE++eT4PSAGeHNZnAinGk2/mACnIk2eEgfBQ11JfWUSCD7dmAilISPOAXBUhpGgmkIKENBfIHBrQmJ8aTsNDra'
    'W+sshFItyYCaQg5ucBKbSFWzOBFMT8XCCXhTA/PRpJjh1fHj9Jc+tCKvaNrZlAigkym/OAFBFkNqLZ0ykkyGzOBVJIkMmL2qoGXxw1dFCVMcCj'
    'paStlGyXSfzRJocTWNbPWWUOsr6Q4mbh5BzQrvO6SAh5T5Abg6ofw6kWKJX1g3h/30fKAU48GVX26ohSg1VF8+iTCL65gJy1/hRANp8CyPZTAG'
    'k/BZDoKYB0PheIkEVOwGDuDbjmCwXotgCrrm3OBFKMVdfnASnCqmvtmUCKser6XCAFpK3683lACkhbtfpMIMWkrfocIAWlrZygUo6vfNVYpTDN'
    'HpXuSIViVCgAdJUiMcVplwyRAkw7EVdt/h4JnuJchGRA4hRldUrGhrISK/hTErERDcONlB3wBJRKMabKNYRj7imcbsO/DGKoxfeSoctaGsjZAk'
    'C2UkBOHjESa+xPAzl7JBBVKm5e+Kp8zOdD6LSAILG2NRNIMUFifR6QIoLEWjR7OoUEifW5QAoJEvNjfYVm0iuwiCi3tTUTSLEV2J4HpMgKbEWz'
    'p1NoBbbnAim2AoiGzg9ktpG6KotSsOqoS4Sr+LcbwCq+DS020kCajwSimPIC4dOqiM0XR/sqbZcjjKKwFgWGjK1b9hRhlCXQJCOCatdeA/CLo+'
    'duQB7GWxbeHPnnI14sYl+7eQogmzOBFJNeOvOAFJFeovZMIMWkl85cIAWkl87zeUAKSC9RfSaQYtJLZw6QgtKLzRfAjNw/SZtHizhfdNJAFnG+'
    '2E4DOV5I3C+SKIAtbSkyvVhEUn8+D0gRWt9pzwRSjNafzwUyndbN6fb8+TwgV/OB7NRnAilG68/nAJlF6+6hMDX1A490K/WRRTSaz+cBKaLR3I'
    'lmAilq5Z+euII/spH6yCJqxOfzgBSi+NZMIEWnm03FwbPnAHMKZTHxmZRVQtVbifs2RTWDFL2mL2Aic8cCDCzcSQG5WsR7LDWS5kJeBCkgl40F'
    'gDxPA2kuAiSFk6vGQkwdAWw5eTvoMb83tQgTzmw/NZ2F3K6RKICjV7kAhBODiGpOw68SXVxPhDspLx2cTskU4QVH9lRmDpaXkc5cX8rd/BQqjh'
    'Y+xw8qArlX5dwQY1NHAqFMUpCHk+pw4R0GZJPTE22b3PQ6335V+55PzeEgIrsvJ6L1I+VEHTRxYFM72NAbyfBASghsOUnt4AV4ihohNYTTRUTV'
    'tc8FouZxfp7JJxGUeEJ/n8QjJPKXbBLsM67jccUavJUawfmCmDQ5KLIpKMxtQQz6qQ9mNmSxD+amofBTT2TNWOu+3SDFH4ud6eH2TCDFzp+wMx'
    'NIQQvUnOnMlaQZyLzpFDn4b+ZOp5AVcl5OED4U/Ek3F1rDne2ZQIqt4U5nJpCCAu+8kcxDv3Lvm5/MhPeejzz0Ko68HeORsz0TSDENVKszE0hB'
    '38g505m1Acx02vOmU0QX1r6ZN52r2WosBjIXJ8X8s4qmp+ErvY9C9F2AIqLtmUCKUUTUmQmkoIvbnOkUoojOvOkUoYjOzbzpFKCIzlycFNOOzk'
    '84xMKIj7zzk8YCtLC2PRNIMVpY68wEUlC5P2c6hWhhfd50itDC+s286RSghfW5OClGC/NTSLFYmELe+SK0sLU9E0gxWtjqzARS0MwwZzqFaGF7'
    '3nSK0ML2zbzpFKCF7bk4KUQLBZKC8U0nJXKdvFmAFmrbM4EUo4VaZyaQggG6c6ZTiBbq86ZThBbqN/OmU4AW6nNxUowW5qd544t3CnnnRwvQws'
    'b2TCDFaGGjMxNIQU+yOdMpRAub86ZThBY2b+ZNpwAtbM7FSTFayCa9k4R1+Ynv5Dbk2z8BYgF1yM7aUwB5/gRAWk8xkuhzgSiBfmb+QFOGMXRT'
    'Jgq79BXUgLOI89RcIEVyYzwFkM2nALL9FEDaTwGk8xRAahszgRTTZGw8BZCtpwBSnwekiF1m/SmAbD4FkO2nANJ+CiCdzwWiToa5CS9ZqZU6VV'
    '891uzJQDozgcy34uoRPy7TJn86dRa/ai746VnZOflDKQviq6tHmrv1h2Zl9OQPpSyzry4XmtGMLKBOElBRCd+kVMJHC6mEi2TD9O0LO2mTytFi'
    '9gVVSSA/gab/yTA118vH+lxT0jhJQUjpTlVauOPzfw8uHoacvgf/huf4+evGCRfV00+4kFpd/zw/ah5dcLU7mgNnnKOMu4MRipghAyKBDTiHLi'
    'UDRDv8yS35a69Dm+Sl9BZeczuN0YjqLSZcthT5e2NKp4vht1XRS8qsG3GxTTaV9Qf9FS62RvZqfLtsPwew/Ln7wAIuUeIc/FdWQ9ANqx0INSVS'
    'fVUowx6FK3IjakPJFEso5xkMpbTgMPiaSuENnz3TswsCev0jXg+DP7JUWttTL/QHvvsRGY0pC8zO9wQF2r6pLZ5Li6gztUUoLdrTW3SkxY1q8c'
    'kgnFZam/6TXYuD86NvVH1iNXTz9DLn2ZV9xq4EtBJNt2pFCjLvVfJD73RSvVTqfklFmel3xgMifNZg0avvpd9enx79LaeFOyZKWqV9GdKjumhc'
    'vG1yf5SpcggCXaVnid6ULbk2dTG2Xf0E1caxs15ef3t0/kZnuLcmW76oVLgwIPKQD5DsMkSsz9/oCPDsuuL/mBDpKVD0Q2p7ot23YkKNE95eMV'
    'WxbxP1V4NG/8FsAQ1HsqxK5tFUb8obRL7y5LD5YRC3VRUN2PvjhGpN9Cm5MZu8ZEROBQuW/SX5eRJ8iy+T/Z+9QiR9DuUCqVEsc71qEfny+gCm'
    '3asUBb2kfBLHDlcxz49PL47Oz9+eXWgGk32jltx/++bd0fnLkzd/ywBsSkp0/yEjmEG4T1HC9a0U8/Fhq+e531V1GNPPbFv7QjjvxeAVfGNlRD'
    '6ptkbIs8q4dKhUHr4gb4sksj2OjXcxKAv1cVscROb0i0d/P0clSnK8aNvu7mti8cQdEYBh4RJnj9q30Uo7Gkey7MN4iAoeVGqYkrpxIuxIO4OM'
    '4x4nsVe9DVmfnb2Fiy8BU2nj2cUolpIlyHaKalOU8R37ohefhzFV9gVBEj1rUBTNQf1RPQSHgZPBW5Lg4gNIyzpmDZEkDrZp5iUvOyahYQ3I5Y'
    'QS0+6aV4HMj+p4hVRwhNPW/td/rqFcClX56AikckVvQLsfVL57StGMv26pFgQnr29LkvD/+s+69tk4Pbq8EDgSnKK6UElhDe4mClTme5VN3+y2'
    'ryh0nova8JToBCJ04MxDRD3VIJBS8Bpfli6QAZaS1Le41jel0CUuYJjVSvBu/0QwwMq1P6GYB9azh0OYRq/QmqhkzO6AdjNoDWjNBI9YP/AVHM'
    'xRn2MPqJoYDZfGmqjBqiT6lp+Uaiu8uuWqhUh46owoyhBZj4fsZ0s0YqrZmwXBqf5x7CSoli/hmxYWTZD8kySdtFR99gbAuQmq01DzNQpaOagh'
    'tDj0ExscQXwaq1XCtO3ns/NXJOHhoK5xkDd1Cww4OANlYiCV4Db+QAOi7PVtVPmxG1Q72DhT+oKkmECKmESUBZ560siwjTBgmjGdBC3K4Cizk7'
    'ZhF1Gezvd1yOjAmTNVWOB5s1xmdjKQYEdLBfN6Ay6+YGCpOACM3/qYpVbzloO3dJkghaM0rc+rCUTTpGTgqvmcpNTXJmAjceRVw540C9UyAHbs'
    '9WSI3NjRaS9+w0wO46Za1THnEjcbRcPRCHEBOSSC2Qvj4W1iMUHBEB6cY6dOwBRIkGrOLwhWCqtmwxl2j9JhrfeJXVIRHAaWoVLyb1poJbKQho'
    '8mwYb8Sb9HVGEQrFJ+UMr65QEVo0K/5XJF10RXmUFUNQ3+UjV4yyhsZ+QOqb7CtFjhUEH6s9utqMTo+vD7IDy8E3GG84J08QZju8bYrvV+sfil'
    '6e5PEv903td0znnScVjQgNXmx8Eyohw0zp6u2tQ0UgzAmxjXOeJ5rdK0OP6RFxm4SKR989XHVI2vgWKzXAQFRU/M8TFJVMkTWpRUtRNHCOOnmM'
    'aBzMKV3BtUdJ25jpK/9VTDLq0BXBLbH6jeRDsNXkrpfLFRq29qWC0SEFYmQzAzkWhYV6x2Obte5g8vHE4OqOtkmDPA80mf+e8YMW5dAmTLyehC'
    'AW3iPx2uzewtCs/LkAWjV6Fy1CN+SXNvdQd0Z6FyYA+BntFW8ObtRQ1bQgQeTyhZa9TWv0q0XDMcjKiQBzVfwR9rZbmfCmcgqrbfII6QVDQoEW'
    'NYMhECwYXcLZTDErpeki4dg7zZJME/fG0jFBw1oCKWwkNmm33Ll1WxBCl7gtEuQ7pBgzLJ6MuosIPfg3a7bJZPRJV524d45TDuXwMD19iN1yLW'
    'XIsoaBf1uoVVJYj7VJTBvyyCsbcThQI7Wsts70MWBpVMVeF1Ubwr+GBOJXUsKDFRFlUq5llumk9w5kuNMQ/RGx4i4FZItJSqTSz5+FJAuiLHu/'
    '1u2H9Pr8pKHtWg6O1wOKmqPXSIzoqly2VqJNPFBKqaPG9lLQmOhpIZLRV7E7flPNFNV34g0c4OhGpUDLptoRyUztGyPDt447kjeRg/XR9jNPpz'
    '/bnjfnMcDTXePum8eXLUJDZGgEjaWYOKcwhgwSc9FAY00jYtrD2sftZjr9ll3iVa7ztyWjhNAFWcAGuImUySvOtsiWVfgzaDSX1igaqUxA4ZBq'
    'HgPDFnbeNeZHDNovqKkPFwQMz8TV+uSboOowOUrmWgBnsHuMWweGhguJ5ApEIn5XgLXpLgz7JbWrA1J3DfP4iKbOWU2IP83aWMqGG1XNOlkFSD'
    'tLiTep2Sqty3eYeV+97T+zhPPCBZdUH6sde8PTgd9F+HyXsq2WHu1oKIW6MKIgUsaeXKe9nx+GOhb04bT85YcpqLXsFXKHhNfP76DGWY9GuVgW'
    '3bU/yRepLKVO2ZXxDXDM975ZVfo+ppXElH5XC7iToDzmbdjj7Sw1i28kTkFcM3kb8B+n38f7VKxg+HS2UqrWHfAlHaUlB1lWuxyR3HMg2fdiEJ'
    'lTtQhcMuge35nP91hX/VkdfBWnUUIJocjZ8n5UlyLO464iMCREZ3tOn0qauuDKwCl9z3qPECDwVzSBlOUlpT5QKljN4zmBJVArxnOMmVXMrvyq'
    'rc0YSuTIRFOjus1BxrRSAtWuTV5ZESN96tUJ0kidaymLNbrkrdh4U2fdetLJ3Zd1QDnW9x7hE9Hjh3UiWuyK0txMHsF+wF97bMTmoCamYI00M0'
    'EnbsXJwIKenbVTmtiqHuXLgHHHX0AQqP9m5aZ6FO2UlfXdbzb1a24pRKV6hMdN6dii/+/fY0xs51vRQwOZESo0szt2bcO6haZY/YpixzjlxMl2'
    'lXfqBjLZbgKYZIlYlYBRS7igVPrTGggkLqcDc6MMi7SkUlcpfRZLAMiq1Z+P4059QQAskeGfZEwEgLHQiOzYKlFuzK1ZG+WHgqhPzLhRmVqwx1'
    'BgZ2qHmsw+R/0dNGSprZYZES1o4okApm5NFknigbw4gKyQMBu84LMz/3dPnDC+zcsgcgCG5Asu/3nEeffPgHXCONULqvqtVT9NlGmQUcU0o6te'
    'je+Xk8+nuJEZo6InmcGday7b5ODe6Tj4y1DDL4brmbHQI/t4f3Ewzh09Jv4KCfrslXw7ObD0dYD9fE4MUL0euXtSywvpY2NthrFwdl0s1T3d71'
    'rVPfJHytbQGtwpw7/dz7hOFDfZRwu8NN7A5l2npUy9K5+mOIcddKykoxokXlt2nRZKpGpagK5brda70k4GY6SgpTRp1TjOJQNSk59kIKveWHKt'
    'pWLUEoSmynTiTxtLODalBSZBYnzLO7JICZGnIStpp3m9GympRZhJEQF/2Yrhm6Tp6cQCi/iwnqzMn2NqM+CjFygLt9Z1AlfwFVIQ+3W1vwl7Ht'
    'oqhsJAg1GYUZUnS9hNhwABY9inHQlNxNRLV99/L0bgJkbwaVubY2ovj0BXs9hf1DjkV20X+CgopQ0bgroKQwKeSnkDWGvKUVsp1Y7t246LVJ9+'
    'OrcXyRgzYMV2sMxxlRFiAmVP5Xk7SRizirYzzWhasTpemEGMGiuCMVioTnVvSrOktAiwckua+/kzl+H/z5z6nqgvYywPAPWOg0JCCknWpDtQLZ'
    'B4KlJiqurTYkq4QpY9oK18WlGcd9uTOQ8pACzt2rx+i10Ir6Vo8X3SglZTmpntSQ1NJZ2xjnzezrEqkg8VhlzdbCmlGepOkVOi+qvT1CsdZoKN'
    'ZvynfQ0fqCldB+vKN0w6yQVmWubnR9LG2IUkMRH1nmP1xImGo6unuDv5kjQni7wtt+Phk31AYvSWw9EQqu/hMSaBzSPiJBKE10VIiVKInKWI4m'
    'vFjE2XEwGA2Qi07H1jng6rRs8qe5ayZTQnddpZMvdGWjCfG2ghFk7wej96y2EDMXFD/RCFXdfuAT/nT3B/CYGyppzCWPWTfFwNiL6Y/yCTOs9O'
    '6MZHNyubIqriICdANAsRF1gjN1QxHxy0CiaHvrxowDZtm50y2re5mpgzoQSb6FCwv7LBFJ71lRfSDZE6SHvTAK8yWpHWzw9hby+vEq/ETgwqEQ'
    'm7gSP3m6D9Wq9FR9UFwaQ33B6/N9fHKrPErgsDEkxetPoT2u9AazJ64WOvW2s9JhVtzEGL4lZ6ozyppIU+TDVA4ftfqiZbZ3D2EvFRcE5YfQWi'
    'pT2r1qWrh7gc6JQ057rzcmLtCO7OaJZp/ccddT4z7XW5SHvdDHSJTix1+zR5EvRkv73FsARhaAfqN57WGRXdvcypN1p09zLTXNY5igYsVSbdbL'
    'r0hjTiUG1FHheOdbmlYbxlspI3qQEOnpHctq03Cda0PVJmOxVN91QMmFXVQT2m4opYZnEH91ybvmkCuVWpk40VKJOmSnC0Qu13HhWX6lTnk+HQ'
    'Q+9E4VrWBxMIQb5S1ZW1SjNW98RW7Glvle20PPMPrFqX09RQYNXTzC36Tj+4E6FD01gJZzwsTDj5Ebp2+X+haugo8d7EZ6sE4eMUu3enmsL4Wb'
    'b8xkdnUBncTQx8XODrDql5kk79C5C05pROhw9HZPSS9/hcp2q32oU8uUf2WaSEsOOM6KrMFmhm9olb1dAdHGxtN4enXqGM4KDWFr6sly7MiFFf'
    'g5k4RCj6acNh7Rpg8e0dahPT+89PJW3UZja6DJEruy6TL5iCLXFEGf9LXsym7InEVYj0mcZ0gTDuK5TIEDNh0xYjnFPrWH2hyZ4OlIjMSBn4Zk'
    'JNgqegqmG6nu5T3ZMmZrKS+QqXhKU48GhM9Z32IxqnQ6RehpuyA9XTn01CTduTNobd2kJkKk1RxcbX8errafClfbLq6uHoOrnWnnhUbV6/TWW+'
    'gIsHYWEZz+9KdgJztMkqvkvbyBZz0rKtXDPHpAk3Ja88dLfYNbKvzekLqL7pla689bmLX36Y28fD8a9G+XfUhGMtA+ZqToEFftSV89A46M7FrW'
    'RjDlAeVDY6cTBQgyipKbnNWfygOUzJQFt4AA9fm8wiHnzHL9Y9ZilT1lq6MoqOfJuhnB+LIIQT8vRtBXOQRNeCE24KsnZjGFnd/Gbriauhset1'
    'BXT7RQV4XuZekL5Rm0KprxHesaZ8KpS+3KJbuLYRFU4IjsXI7oofWqpAR6E0E30krU+tYKWSsyagr4LI6gQdY+4gaiRxeHKRbtH/16SPMOfjk4'
    'zsajem3xg4O7pw+O3YxwMhyPNDPSA0mNg1RFPBANdM6BKxSeR1xmbAISxOW0KqWbmXas3tUUF3z9dbBT7EKfvtGfibp6CuWUK1eKchQFeE4LhC'
    'sXliUoKy+i/9k0lsBcJMMMLIKLrnNB5PK+nYLQ2ej8necQ6WS0JJpavHtyUKJ6jLrOYpl8qvoeE0lLY+xa0Sd9HyhQaR7lrgSfTlW4ydwgSM8a'
    'wkDXg8cZKenEXW0pdbIrnvJVYmQOEg++ePlSrrJG5ID3s8O9UmqbRB9nrt+YIWOVO591OT7Hm3+YcY5ztnIMTa8PMA7fxYrq89befVb2yHVv6q'
    'e5j0/2JflIEZbxycQcAUvQu5JQyEpo64UuCWBrH1/iPzEXyyg5+LJDm8PRr//i/xkNvbia/As+bQMW70X4RIGv9338mGrEIj0ImyPwTvxv7klD'
    'bwwEY2uIkXI7sqYVm14XvjfWwCDbhU0UrKT/wXoF0VaQOhmi5XMGs6d9RdlkoAwF1kbAWX+9wMdkmomg5NgHamIf4Ejtw4NyNrbkA1s3PKuxlj'
    'jikZ42NnHa2AJHUWtWLVFZ1x+03v0HzimqaqpR4xVKpkzRe5ItN7FGDGTGWkVGpFVkztOwVilzmuDRhGi4+jLhacD5vTrelInthTGCuHZjxTJ0'
    'QAevLXzgeRocjL2nY1np1fnrv3mo0JCUyk1ZAh3jiYQ4JBkTICdV1WvnBHt0tRKbrjx+VKHrfM9Lp0iAbS3hPbt23JK7AhBzx5oh3JZ0Lug+RU'
    'mRds/xqQJ1vNth38RY7DN0V4uTIQ9LjF5SoFeswbQm8Vj8+skG5AFiXIv/Po8t+jhkasD68J1PW8nUIAOuKjVKIteLGHIqxZv9c3tHeTqqxYXr'
    'A2fNZsc/pSCNTEGsSeI4/tqJismIgkJbEYb/ECRd3u6RmWLVswm5G3ymVeiP8p/3iJP3/TGvlXdRw2Fvc1x7Z1H2PHAEZMc9S8emP+NOz7zQ4r'
    '0lT8hxBdSS1/k/qLMcTGTaISeZWvDll7M60BhsD3atMs1zZCMvDLk+0zg0NWzZl4ZSMdSMkz/BhrQZ/Bk1zXbdTn68szhjQRbcpvHXM81UBLRx'
    '2XJlxVQ6ANUGH7VNHH8ByGpaplvEapdPV0gQOp+u0EgljkhXJKxOnYv788sZxJdCptttPlJzNfWLo2ytEMqQS3Euyppc5JULtdEpC9kvY/pUh4'
    'Y9NXLpXBPkXMxkVsDvAUGPZUWPuB6N/mILkLMLlS/WCiYddx5W/saxryWcdmVtRg3HFPDNkqWiNXX0J7s+nABpD4KXg1HqvNNWcJbVtYDuGK2c'
    'QFsHFP5jdwPPklVioZ9Co/hgdkxTG9uriPksV9Ng1qrW1UxMPUbHkdWWpDuvk/4kVt77b86Pvzk+Rb4GAXNDfvQlGRuf9GWlGhGPf3N6O+A2XH'
    'Cv3xwevzxGqgUJA/XbXhiLrMQi5ylP6VDW8goObFKKarNPCpldshhSlA+FQm/DPoqDkW9qH+BvTuf7EytTmXyAh+6k1y+nnHU9n1x7Ec4eREHu'
    'XkT0Q/CPf3jNgiC33VWRdk7ghNM27TqcZpEpu0ZJkTs5pPhEXp7ibuye63msV32S157fVeQYdr4sdAEvpPiW7XrigzSLS005DM1opEVBbjQdWO'
    'ZsLTCtRzmDrBc5CvYPCkhl++zHxg5NXHqEM8Ms5biWKyRm3cr9A03cYSleRiArpUIlSC3vpwXcB6bMsvn4WcL1efYc67/WHDcLzfHo3x8zR5MD'
    'KDU9IchfcwW3Cs3u+GLO7ObxisfJvI6wbZpupZuysDtNhJi1wYubrfORgdieRyx1P7oVZzcng1Rq1QUrvyZN7xSaKDLrPWai8HOcSdd/+DXp+n'
    'mhGZ6dPGaGcMqPiy7lrzbReqH7PwWvzNnBvnvzWmovUcxkyYsM0OYLnMHlvMZu29xWqZxcOb2dYK/y3lK6d04GMpmcHwTE7IiVy0esxLa/X2b0'
    '1znhQ1b5zsroKL/1yspCdrP8tXr3KKmAYmM7pDuaKhhYdvqrEuZasck2F5rsFPnAm+qvxk7rhaS9g5MC6yoBfiIDUYDfNAVTrRC9bRQb12HRcS'
    'GkIab4xryRZRIFzhnbZrGxHRcdm40WzxudyyyKjW+r2PjeFR2fId284eWrF2eMrpCoQsW95o+Ok0pGWmvCpR2tgm53ppp3Za7E5ytE6f78C+pD'
    'P0PZWUgiOji7XAifkpDhcjouL39rmJyBqefFMHX1GZi6mo6pq/85mForJJlRQb65mEJopIoEVbi6kcq/rMJSqk9RM5J2Wb5e3p1mbpml0Cqozi'
    'qmzCqmyprmu7KwGuvT466ln6HA8pRSK9ab4gkIbe4gi1BgvRgFXj6GAhUzUyS4m5WGLz1LwGUxvNjmxa02hbxR19aK4eDq8Ti4mo4D3+Ry9Tgc'
    'XD0CB4WcrtYKyadUyGkuDi7R6HW+La+iaiVQYqBcASLPvuQ4GP2H16I4uv41pr5CojXV1pyLUpOF8nfm/ttl7s9+e8x9sxgFXj6GAh/N3J/9a5'
    'n7VjEcXD0eB7OY+7Nne3ksXzks/isYfKHr4F+KXAf/wg5VAy7GoV1nd6coyNhNc8WdxIwhFrph/aV5vtgQwSDDD5LznhPp5EUQnkGxmHpPOqWE'
    'qmHs/pLqTnxbZyMjX4IKT1MiBXxPYuUEKbHNZoySFcKF5qQyL9kwS8lrB69ODlbSAcU2MzQHO/X4QPGgkc+EzgNtI2zYY44GqiOtdRpp67n7qO'
    'DH/GzOM4Nr16eqZh9FeYVurCeHjfmUdzIIPe2IyEBybO/OdGX6zfsurdeKYemyIJb0STIbQ5eL4GfBY+QzcFMvhpurR+Hmag5urhbBzYJHy2fg'
    'ptD96qQIXxenN0hjd8br7TFCcBGnuBwdZlp4yVcj5Xmj/OlPL2Z60PmSXo5X2++uRjNF+WlL85QeR49c3EJeQbkFjRb3SlgvdHunoq9zd9jpAA'
    'nHdICHJ/3e9nF1rxYZTaGLLxUInzsaW2C+mCqhmr2aZWKU0ioEz0Psqe5r07b4Z3DRQpe5s1cFsMpSriujaBF3ltBK2Co0zq1i4zwrOE5kbEeS'
    '5ITKO0n9t/zBPtZVoMBECt2Yzk4KIRxlAlyEs+9uzixSIiFVFCn9suLgjPnvFJv/WcH5ZxZyGhJMwT7KOcmFCEsONoqtXSGBHhFZ88d+jmIlHK'
    'Ul0gY73M8UOZ5A4tjzU4/ZpLIqSuZzvGN991gd5Rm6TOh3MeU37RH9r6OIBWSbhY7QGe7EtWIb+/zRG1suFU+6s7MLRVjennWR8K8d+e7tKa5f'
    '/33//k/fv3PJYtoVxNlf9d/wpi2kHDm/KODIdS66WRYdjDtXVQQMJVaQkwgl/DXSRfWR4sUsX89cicz6xDpt2HF0L+uBqOG90LkLfJoW5fPUJX'
    'qML+nGWjG0Nx+H9mRygxQNUB5HCu8pZD8p+hbFn8Si20GfNl8GQyo9pYa++7gglkL36+b+PFPuAmHSK9xpBdVFtVuTYgvlX8JVaV7UdU4Q9Zyw'
    'ay9O+zcSdf01+3vV4O9Vnxcp/VTegxuFdCLNIp5eVFlpvvdvIbvHxmaxUR0WG5X2/aXgyem+v8VGtlVsZMfFRmY9f5E6gVNByGFRMGBgxjgLKQ'
    'kQ0VtgnKzPcrUElJmctV+eIu5tn+NgiYEkFZ3Zo3Hyt8ZVU2pccUywzefPxjslCOVkVOYYZqolaeKbQ19UkqxIfr49mrsHy1QYbUftdB5mnRA4'
    'lV2lpGqBrT5frdd9Uyjn8dA5ZDhlzKDvf7z6v4VzyzR+5Ylsj1XAbewUI8nLoiSp7XSGHAsM9rLYUJ8XG+rV44Z6ZYe6W2CsV4XGulno5nnRKI'
    'BW1K7rJx1KIeNsdngrZJ3AM0bQaWGMv45KcLNeDAdXn4uDq1nGzn8xDgpJ1RfNx9ABS84mQ2VxSmieFXasQtMn9qzaLCQUX1w2HoEIzWoocVMB'
    'B9G8Af9qnmWbG8Xm31xs/h5N5GAAC+qFhxSPOtgsJPVdXD1+4a4evXBX/wJXuM1CsmXjZEF/BPG2QkYjyCqzY6O+fFycypezrivZux3phPbmW5'
    'xn4Gm7WH6ng2L5nXzjbTQeiyxHFxlQDWFuW4VNVwvOckFcPu60mIGfQoIWvlpYF/1LEdI0DPrKw1JGJTlVx5BvfChqesjJ4eC2/Q83pUPx1Sgk'
    'SzaKsGO6MTIPLl0y5TZQlyud3kgXMEEAZYWhJuQAeVoJvq0EB1w0ibM+nb65wDpSQiKpLw+9sAryLPP13QM4yzcSZXtvUTuYsile00XtetIfdJ'
    'BuMg6711I8I1maaim41BRi3B5WnioRx9zkc4/SvVw+PoZuq5hXYqOoV2KDFciXxf02PanMZ05P4NK5uMppq5Cw3mwUvgc2eDNcPu5y5bCn4vfC'
    'rWIRWQdnC8RFcsbwloorLdldVAkc09/vsTS/1UDJHGtWqgSQXV3ewqncunOj1bO+XL+ZcOGtQjeu4+YiEWW8LWDagdoQZ9Xv++J/WoxZkX1hlt'
    'ekjszdGFQYIU5urjGQrHNj7qbRrf/nmqnUDP73MVXN4CKF9BbnRfwa1bWFfeKYgZCAUJR3/M46fmnWMctRrPBdrbiTWGE+RFSSdzYXTvWcd0b/'
    'OtrfrUK6s/PzxiPv/KaOze+757e7e1JuWvN1dHNdtApvGS6JOUhvGO/IHo3Cwkf2M9N64QT8CsDvSfifJAn/DI5TzBPi5M2jUsYzv4GX7O/s5j'
    'cj5z/yQJ6e5bowU8H6L34M/+NfegwXc7s5P3qcCYd3xeXv2+Kzt0XRO+qiu2PKWZuKyCy8ES4/ayf8x790JxTz9vnrfgFV6YAyNN+5JXFnfLeQ'
    'uYVQ8Ijvst2EqMivw/3m8M0uKo9StQ5UQaKS8aK6Yj+zwQTufCucKqO6NNfRanF1+nYxdTrFXwalxqvL1cZlo/w4xTrfnr1UH14ZTFL+VFMZQ3'
    'JqkWRyhWTqg0Db4YIZRfCMbkVtuwXYqbCtCoRQfY5QqpppiKrAF7smYLO6wLjO8QjmSwkhxu4e0cLqSirWCfBRmUGKWL8yeE1URRZT2oyGrgdi'
    'GV7K+5Ew6tWMdNwgpZJepoJJP4rI7ZH8LHXpaKl75sIpkVnp8HWDs7x2UeiwHY0jLsFWfroK8XQM+WfPox0QqQ4j3zgw2AMeMEpxR4leSCknaO'
    'vHfaVq6fFXk0q6uCX1v4t/hCtLotAvJGPqYXNZ7y+D0qtn9fIyCm622PEVn8N2RyaZDGqu5UMXg1O4uB72Wi8j1D5DuAAhn6sDUkQCSrd1w77K'
    '+oOveK4IYO9Qgj4cwLOmGiY9VJUBiuGgvVFf2djYqhlIXLDt/M1rzJBmkTz0W37x2HYvPGSkHBM6soVhr9tqeAc8ZNwzUpJAbquv1RnAON6fJP'
    'J4z/tyche+45uePwQH9J+nW+CcVrvTW+EHaoGairRe2dp/gKz2ptNcPRMFx7VG1aA5nzplWXfrjBbyhBUAhQyI22vFmHWTmPVFo7l62WiWCzs7'
    'aX6NC3nzTNUglmwEcMpKMfEM086pXq7Z8m2XC/khmROOkSfnj4vyCJX/qeUxTSynrli1XSeDGx3IefJhdqOs/Vo7xXeVq32s1Ws1U6N2jm1adl'
    'mSt8vW8reZ8cXM31/mNW+s3H21yJZKPndLJYW3VLEYqFdXtKWaV43VZuOqoPxz9WjJ5//3m2j91z1uHvI2wnr+RrjK3wBXT0v4D59L+A+FCb9Y'
    '6NarSyb8y0ahs0QI//J3wn8s4W/8uoT/MY/wN/IJf4pkdfm0hP/xcwn/Y2HC3yzmWXdEhH8CIeqkcV4u5mNXCS5ZMCeBiW+dJeWGQvuheVb+xc'
    'h3qrqqlD2p53jRTvH7y88F5Ysgs/VFUxS/n6G6KObwfsoLedmYr7Zo0DgbmMjrxjfHnESLiPwY27gdw6YpEYPLvfA2bi2bgtZQJ4ziiNKHju+j'
    'qO+VeUBNz1FEVTypNnvpi1qtEnxxdIQ/Xr7E9XzcKleDt8zs8IAVEnRB6w0oxSmYB9QMrKrwIhLV3ZJrfZNHNdf4HoaUlNS7A35FCU8x0BXSDC'
    'ABaZs1S7j7Jb8cEc7wyXYVxSl9u1y+Upe0p/IznUE9hXTtJ5cNYQPwD9V0sNq4uFyAlgwdgUvgZaMqpx6vkqWmOEkmXEIXdPsrrVRegpXL7OOc'
    'pZyzmE+/fuof7agTIqCiyAL++c9/nlv/bYTaRJRS+Wg0Goxce8cP39AKtUYh0gtDoRb3sR/jdiDoDEKbqPiLL36W3L3V8aA5phO1VN8qf/qhYm'
    '0VPhF+oqFgV5JoJIXuZUAsQ0VDLgdMGpuw/2CVS6Ij4nqDLVK3QfhAqm5SOXHFZ9ILqd1NYAa9yNVoUdnfi2aF8pFUKL0b/YFbPqXGBovg/MNl'
    'BCdDnQq2teLpQEldKJ9mbtOGemxstI/0eVZTr/J5jGzLzbjfknBtmgVpFtsfUGhMhWkDWNwn5RRZZFgrLh1XKaXdKmXJKLPuIYmyE4dCkpVgoO'
    'qxBkbfQFHl4VAVWu6F6Ib/rc4SDildDJqQRqfMkOO6DF4EYSYPhy83wVHNnk9WdCEhqheznHo4QHzECyXlyDG2kieBlUGL65oGKNydMlWrBbKf'
    '2z96+QbWPTsfhcRkIKjHMN/tQwf43gLKqjGpN6xcvfg8jJOo3RgzcI2PLsmqnS7Vkna0mkrFLYpfwX6bZnYTdQeMV9TGVppk+oao5E9RELQdIf'
    '3IkptRm4xM2n7BGE92aam9ea5khsf4sXDuB5MuTjoQ1tgdDvjicmeC/CcRzzJZlqLeth/A0oqcR0QGLNjydtKB/DIeIEC9FqjELiWav6dZbh4t'
    'vHBoYc9tB1ZcHQ4nVUXnNICSQx5q638yO9zgbVdyjRtcBPdUO50uB/la6aB086B2Tz75w8x4G3FXIZMALARdQi4tXlPWyKiPVBHUBuMoVzQg0t'
    'uPerQvays8uOBDEtTVP0nMb1OKSos5+jBhTzOcJWN2US14ZyiE68bWRVeNL2rD0KM8gIQdLplkCR77qgbHYy6KPr4fsCc8hB8iLd0cpe0PzQfg'
    'EZxEf5+QyGOo+pFUCJCoTd+c3KwQdnnwu9Ooq5Re/DKwgO3WTpZMcXmZPnyKK0SyuNCCSXYnbZUIQmGDmBQS3kfdTjmFVViAN9Nk24uguBXMER'
    'aRiBI3aDCVhFNTxL1I6/w1EIiBODWRy2SMnck7fTiAWeG///N/mTUvYYpGUCmbw+TraV9XBLILlkhHh6VkUDEOzHFACfTN97E2g3HELl9oeYYF'
    '55v+WFnnwtFYm+JOjy4vgojt1RHQ2Qq73TShvcTkHLJWhxMTt2JNE2cnZBmihgNCCbtJmhOXbKWBMkvdU9Ye1x+zhW5jVYjB3QHkKEEY1luppP'
    'jwrtqNypiHvUVfXEoz4wpPRZi8RE72YSFyd0Y5jZgipjaTOSbxjz+DJP+wS01pyRf/MtvKB+XureCZLwnmY1VzVxqW/2naB2Vf7KtpErSIuok6'
    'pIfiFCspbFUz3zfkTneW0STay7RQJP0Cdjz456VvE0RCeLyrV7jq7oIxrS1xdNqKQv/Ex0Gomtyds4uGami+osmJ7gXtcNQGfPcokG+lTpaXmD'
    '7jwdbGcPsQ38RykpDm7D88jYRx+huVemA72tlkNyqOJ3+TagglZkkDupCOWEc2MuLM+dG74zdvm+7AKhp3luN8JhGruVlScZKsXZ8e/c3Vdpwd'
    'eKe5ky7Jbek8dsQ4qXBK89rnwFec0GB6G2K4vcOq3YejKEgNVH2oPTgd9F+HyXviWMe6SSarM6ttIqu2yck/Z+c1bSY5s8hpLrmm7Y9ME4dqUr'
    'vBTNEIS9ue2CPKytZwwu/36Qb+7IWn/EmDkO4q2928hvwVzuhHtWVYCEAMPuQhIkNYu6GWGw67D3zc4EoViuMIX+++ifoxKZ9xB5PCLiSdJ8rx'
    'QV31OhG/rchFC6cB33gq5uYU/IjKPElFVfJUoxNQHyKy/Sfib0L5oskpJSHBb+QNoBX2pWsrGrKBPjDOP8za2amLythEEMPbdK1K7lVVGvBnII'
    'YO/A9xGFxzEZzoQE+fVJPRCHRESSw+DOK2AMN8Wu8JH84YEpU6llxHoLXUg6iK6wT7zTEegpBTehEOKwINRM85PRL6yjXd6igNpRnDWZduZKWf'
    'otGAHUXuALWswDowBZYCPA8m3Udo7Dx0QlOmhdKC/uwSkhHYe6jpk9JQMBFNGfwTwfIG7cGkY1Y8k17MBJz9+q1BAtP4Aal6lFpc3A3dDdIE0W'
    'QxZZzwhyRFjvg0NA5p4vGkrwACBuSL9qOcHeTQRjU4AMWLlsJMmq88AkT3wD4Tsa2tKLCFJGm3vKZTifnnFMv38KChffllHpb0Vu9G/Vvo6P/k'
    '2nqM3spHj66aPns9FcPzvfg5WJsOXT7w6IrAkno0GnOCkA7xhBvKiaOWAC+hsXgYRmqnV5xLsVwcROYf8pbqMj6UE9f7CFdi5SyHjHXgmhApSR'
    '9A2PDu6MG7HbAy8ub6ySuJ0ZaR5mNB83NLTEchxsPkKac/+dxB/qKLGSunSQGu9UPCwqtBw0gm7KWmtrxcnhKj8ADFrMs9A2iheRE3wHzZXSlo'
    'iF6phRpo7yPOxHcz6b4XUDcP4jA1IsrsDgZDJQtFIV+6PEFQM9YGD51OjpJcy/QFdxTdxglVDSsHk0R0DisMblfmBHEzGYurjDcRW3KMCZw19t'
    'BnXOOieEDP3g6BMbfg2MgozNT+Cq3aLOBLvydi/1Fjp6RFOu2qxpaBCiXoUIzZzIfgszjW51wsZVdKFi4vijtsf9IasFYxYY3gkpcMkbUNKh0i'
    'xlsxAMiLXOaaEO5FM0F2E8WbPXanc41TKOhHusWV3R1z3nitTgsyClckaxQk4qiP47db3vWMJNjPd55chbpvQJXetDDBfWfsidudzvd703U8tr'
    '7hVMWOLs2mtrmZB8XPf9xIT+TAFUJWMa0KEW+FtJi4PrNK5wvq9Ky85OdgV5mAN2r19H2HiL9FRLQyGe5qIlH0zuoWELta2i+ou1qbAe0gWiEX'
    '1mS4Mh6stCXalbmhhuBknT4+/3eWbdOOyIyd0KLnJQ3hQPqX0taD/DtiqPbDZCjPc/TlQX7LYI6dG5Ozs5dDyaiTFadda9TWjdWtoagVc5ZTmP'
    'LcuNBI694ekdSoEpEKLFtk8FwfyzoLayCyYfdBO+H6mFeVChW1VmiFTC1CNWhmXDKNZBxTLvAoSruiDsnCOKD6hXro1c+oSEhSCFAtdw/Xopwj'
    'WKVWaNpOKrCXHKnGfDx9zc7b2nMG9iQb3NnM3omAjUtsa+WL9ZcvX4IjxSb1hFWk683Ex4SFU3JdqjN6esplQIJ5WblgijO38sYU01B1yQ30cJ'
    'iv4bmKdvjCYfi5nBBfycnBpp4ba7EGLM3ZSxSvQCme3CODO8OqTJ0xND7a9LGCs81CyT/kqoXXZIE1nrmMGZlZfcCVil+Sso++JEY3XeYzuJ2E'
    'uO6NI9FZ3mCmk3ESt611S5NDMCKJVYB5hMEc1GEupkOJ9zUuQU3e2SLnJpodKEiZ4qQCz4hLGMIqC0NsE3BFmmbYYf3v7pJSQK8E3+I8XeHICi'
    'XrfEGjZOJVSkjDIXFQ2X7KsrySDHFz9W/AgSpZ+mxt9dm6hXN2/g1fHktf7OizTY+LyCpRY9MRFbhqZoI5tD63xYagm8hM9Xj1jRYoVNXUgmLF'
    'I2SD1NZ/NFl+WppD6nOpdg69ipojDOpbK6RvkhNLGUeSCFmCiAX4hmFxSFJYXLL7neOTxHeFLWCprW1q937F0JXdgOVFtQr1LQwhc5XtDvayC1'
    'L36ho8SljrDnQTBx2fz+Snj6KkSvEqt7anExzN4mJK2m1bf58d4J6GBn9llOWPhfH366ItfT0VL8HZ91OxxKgL6t/4h9zslrQpsm8Ebe92WmUr'
    'lHcQKGOUdwhYOOpTlNA+UUzPbEx1crPyUg5t78AuQQJN3+m8wznnVJ5xGLvek5zwIMVA+T7D5jVoUcwOzlxwsnMvIArB4XPg2ex9CYiu9ko6wn'
    'CUCui0F7+ZjIeQTFyPhyUnub5Crpab+EdacGJ5SdbAF5gc9Ug+/h+F3MdKOliAzEZg3V96lRaVXqd/b8aJGUzhyT6ATNaKYjP49DRCut7uI7L3'
    'J+Pj0d9LpDzLKAjj0d/PpYlr2+TXpGuj2za3w2X3+vTNOWp6uHjwyxc5lj/y2xuAa3QHt6Xl8YD0eSBvfAysgQC/WH7Gw8nKBc54PMOjfnvBw2'
    'Ig5uTnqp+i01WDy66rhsOeZKRXjE3A6Bfkp7uCP+FtWnJlvTLfPmVbmEsr+VJh5b+3XlsYa8gea7cD2QaoOnQrobU9MkUo0jdE47oJk2sgvv69'
    'P0inhS7+NCUTeCon/OKylUIkF2P6Of1FD8bcQTwexXxTMxhmTsM4ri7NEkUYc26J3+bZ93u/tIi5srJiQmWJjUu4K6073jgC/Zu+yIja2Fkxve'
    'SGcEeUgdSqcds1X+8y1VCrST8eG3GUHDFC1xNtIKY3a8qHahH6Tg4rqaKq8wiFeYhWJYZZH4/kcn3TNVaNA9K40Z22+epjyiUSMSWriHHB/1f4'
    'v1lmE/lkHJkDOx75YeOQrc3SOeVfeMzKyg1DHozC3ThSB4iyKZrwY8GMFz8sVzwjhBuo8ByYDLXTt8bSYCTHWjbAuARbAO5QbTu8TNT8jZS4sY'
    'VyykS9XahTRZaJPjKCKxzy1tf4VeV4ONiJvsjoVJpqrmDN0yIFozT8cQIueJWxXUa6IgaMnXAhxTp0lXuruA9ZqmGozlIJEIS4tybiCBdCABq4'
    'RoB8LT/ZBmgT/JjwBlzyONm9Mnh9ZJcoDH/XGTAcyhopfwfHNyPph8PkDirBdPzNi+AO3sQ9MjIf6HuWjnJIAjLTdi0xm1B0pvGSor222DCMrb'
    'fs4hFOaSzWpkhZfNrZppsY45zeYuJMSWKTlZpkWPE48TzkcqKJfO4CNzw4LA8qlh7x34xAd0uJ7i5yJ7ReNUVunI1ZKMUBZzgwo3AzHZj0BpTy'
    'xtaVUha05H1M9iSHItiBwVNQOzIoe9Fx4gOR/CTRgTuHDZEraTnhqjSGy70ok0qsHv8xCQ5g0OxH3cPXIg6dR7ei1i1rl83EjIMIo8l7EAeUiT'
    'kgJfKdYg43kw7XpqD9NBw/+IKpgeMxZTv+cGwyAGCRODKEDP5UmQOmNZzo/finSBifAUU0pACQQQ1sE0+aaE67K514wKNW0YkTT++GIyxLf9K7'
    'Id0X5MiX8l+ZZDB4FthtENOys4+JYpzztNnQZ1wD9WQtnpJFwcqCf/AsF1bEU4chy7f8nyuwSbheyzXM88LimVVy/IFa/OMfAf1djZMjZYLGE3'
    'qASLuXLKL2Ww+0q2oFP60hV+H6KlRRsCOdFJQCStljtCNue3DPPJFO3YR4Wqmvt/rXASQDYaDjuPXeccVlFgt0srQ7IWcxbzoMSzlz4IX+4ohA'
    'oa31j8SqvunILLRHI6ivB6dIvpxbyieZnZ0I4JlpKcM6h11YBqqphl3NEtkkctM33qp2SDSvJOVjnEiiLH2FZbU4XNGGCUV8aIv7rnXktQ6Jqi'
    'sDLQerwQ7rExSnH6rP6Y77EzlM5P7LCBYU8Ii9pbKIE7//KONa7X5IyTiMDrtQhAJiYVHcLbnAV3csFrUlPoQFu+RgibOU94gle/BwHNGpTqOu'
    'MJkYLIbvFZ4NTay6uKiaTSS/z6LRAQHmANTU1kAIkIqSsO0vBi8JabpPiTp5CHtGYUO2pwk69XvKrssF6Y8r63jmt38mQ0hj7I85YLQwvQ+VOQ'
    'jJHl2Jcv2HsCuvyKsDSqF+xWQi0ocfcU/uuKSIIHROVZGJxdedjh1XJNBCpCADu7tKwnqoUwE5SYDE18p8jrvGBIMMnPa4NV9dvsc5cbusv2Bc'
    'gkAyZwevyE2fxDsyLoFc6Mx+wGKqYWyU+bCkaPBRZFMOWUW1Fr1xUonmRxJiKTsrswzylVMHJ9kDAjbJiDYtmX9oEHLJE7E6/kiV0bHZXcMDb2'
    'yVwYiOFFoVWT5l66gErq5blPFdx2xR+jGhzDvKQzMmftMhD2AIdSt1wSHP+uygbAidlpHdOdU3QGPrOpwafN0R19kjN+XTbMCM6ZAdExhfeW2B'
    'CEtVNCfNjfOwKN+QDyO95OnvOevuRsbLJHQiOtqF6pEaQ03lRi2pYZqnvkLRFd921T1wIzMmpkBL4pO+EBrIr+z4rXOrhgoyzwzmH95QarVOys'
    'mWZ2VATHHApSGkNNRrGW1PTmvVtm51Epj4Ac07Ek+ZuhDaWsrpUN6lUcot7UMD9C7sKi9ZxRI9pYdmbq/QyrjjeloA45as/Fi1J2ze1qzItY/F'
    'bbk5ui6sfGivswqLDKsDoz5ipVZZHbWuk5HxBnMArOlxyDWRnLKyloeyVbFw5EYqbNCJmkryfMlS7mMmfZwsgPa0EomKhjbFj1sMvrmeiqQYZZ'
    'Vjn8IdjXbR24gUW7O2a02yjiWv5JwjxA9AWYOUFsaTldK81g3m1GYN43in5BTeaXxZM+E7BAN1huFXjbRwkPfEH8701Pcv6snVcFUFDut1LFKp'
    'w6v55uFQ0Od4/3+OKmzRvks5kQVeR6btUjr2AKLKTipZhm2dbpxtlg1QqKeBKNpzRzjXXsfHRFj+fMWimH9zbY+PGMnNE4wkG/Qx23iYai8qaW'
    'aF7cE5ttHY7u4pCvhZM2r9ZnDb/o3hlqw2Prv81TeVv20K7jUTJCN52R+7DNFvhiA6vymCcIOfjJSt0k/gqK5ZVdi3EnQVJxJvSvXU2WuYG7Q4'
    'NotzMpHRH3u27AlSSzk5mHUa6lLJy3nxwimOVVbpyU3TTKwV3q9l3x8eHRzDrCiKlsxbCr3Cm43sG3hMvW0eHdLbzexbUxkAr7eyrznPBte8XD'
    'JetYzjxOA4GXubzmajTsY2F4ddgEnCAcZQgpKmGpf2QZsF9ZqKCP5WrUYO4lNVOvFlVT7iS/qD00P5VYFyothUpzUnT0gKv6bNeraNBLip9xvZ'
    '9xrXps1mto1b31MabWUb6fwm0sBmNTFhONFYewSya7VcakJtZJpw2AwujtoAAbVDifN1IH2H0rAG+6TC2whK++IUuEm3oAmH7kqGjugjVFrkFT'
    'a8e0hiqHDUp0TEFRisaGCXQtLA3/ZZR8+7h8agwk95lFaPj8EU1MwKhV3zZ/8Nguj1Pv/bJT9iRmxELUaH/3oS+vzlJ4wi5c9fmm9Or8/O35wd'
    'YU2Pmmj+HYNYhuC8LDrTZfeCpp8pVqp/uo4EzjNyH9A/jYON80CFcTpPTBz0csVqNpSzszRSeXp0H84T5P64cn80z9xfZwf+L+L4XuuLBnae/b'
    'IQh7xXlKCbm2WyD8zq5jxyv2RXzz6hpbK/iLDsL8UOMg98mGAq3g/3rRfxyg+/ZzlhPKDlL6UDCuUpEZHl1LTz+LERjswTScWi26I1brmDEXRg'
    'KkESaAo3JXxw6dPe0vV177tlWE+7ZA1d/v5FZ9JnbU5Jdaog5/YE9oWfl/QbXHGHDw1UxHk4kkhAHBajFj44ap0N8GHEGY7lT/4pESQySLKZlb'
    'jiHotG+Otr9X4vePYs1jOhvt8pABTYS+4hgP6dfIGfmLllR0WjEUgKf/hdTXDNh1QDnLh9DMoGNz9WxONLenLiLY7IIxkJb6v8hDRdcOVK7dG9'
    'KTPj7lU9v/jZMz0/Cx2NudV3sXLdkFfagY8//R218F7rgFAesPua1AmMg302BsLg9C6O7ksKXJl89vg1XgiqxGvI07QRiyDGj9dQRxNW5SIe91'
    'c4SNn1+JFk+toEyn2cwMSEA8cIWTCMjRIOYmxPyEFdohTlGxxCM3Y+qj3l1KirJCrYiNWMZ5nBkO9D9ClDIGobob27xuJd+SL4+dPev37d9cKm'
    'Vj21KmJxuSFdkxa4oE7xcErDYsQnnHYs7jwYHioatQG5AtzHFL0I5xDkL/tJgvR6JBng86yHKf2MctMfkIaB/6xWq5+UAskhPMpZl6U45Y32Z0'
    'VutM/0s127Sp+cPUoQ91xmleEyZJFJP9vLNneb2dd6p1OCAvVP+1Iogy5DA3mh+SIQPB4hGQ4mNoc5yvr9rCBUzEdArS+C6+tRyfJY0r9ICO6B'
    'Ac8EoiSA/bcXF6Czhq7q5T/e15dN/3Hz6OTogMSYtZx3F41zerWeffWWHNk2ss8P3/yN8LGZfXNy9JJgbWXfnB9/8+pCZ3ggkp2MbgakORyTdn'
    'IUDuM2+w/e3kJN2ljdF6OyqFQ5X1dwF3VhXU1idqjxPBegox+FBpbSD55CPGrQlXNMxgESV9uD2xvy4LbrxtzEH+fF2/P9N4zenb0pLwnJz/eK'
    'SGVMt/pYJy+qhvtjX/8YEy4a3i//3QWjxREFHL7ja5U0w6LUhMLE9dU5jxfZLnkMyQX5HR+z5Mudchi4GHEcOpkVcZHm0QYlnt5yWeeG6KhK8v'
    'vsMSppK3DJG6tI4p5lPnRFZxAxRT3hLs4Jznj5RcF8i8UfqaXmSyMHQhFpOO6QjGlvuObxfvaxYN/PTWJf7E97IWvivmXJS4Z2CJeJ0vvowdXk'
    '4ydfNuy+rvo0l8K7GZf183Xih+dB28+Dtp8HLWexAVwtd911+Z7+TYw9jfmCPffLmcWpp9y0BaXwl38qhHpJaJxp58zre60E45k93SoUH8K+N4'
    'T94ktXW3jpagsvXS0bUKPSeQw4TQAFczBLJw8U2UBj5yAQhgED25mWBcPgn+u14NVPSzpuOaHDYsyJVFGg5uVZMxVjwb70Kklq5hj4KtFurGR1'
    '5KRv8vmRzh3CJr0c7y9FOxCRnd/7Zc/JP4c3/CH9bM837AnYXIY7ixjdj/yZtwwpGVPM2f/IfsGP7D/mI59+3WupGax7O4VqeZXdPIsJYRcxLw'
    'wLXTg7Ipa59Ef2jKSmx1VRE8mX1KT1KQj6golJNaEh9fGQKSz3A2chTuJxttdQnq/k9VRiIZlNf15yFB6ioSNvM1GIXL9D6MDfzo8vjrT0pp43'
    'T5pn9PjgzdvTCy2/6Xf8pvbq2IhvGtj+SeP0ryK4pQSPfsozoM+uzH1yBrDKoH5bcou+GbIdetcRVeD03ByOaq/icc4Z2+rGw4vBxYcmuZbqU8'
    'tYL2L7iddiMi69hW13R2R8yAWk0V9RfrWA0HaUyR/AgNBJCUm2W4kq8dZqrqUhGZLn7ZTGdW6rh0FIJ7+iXf9DDeVsImb7Pf/lRW84873cmqI2'
    'Re6+U5c/V3Jhv0AJPVQY0iNZbbZopwSv4tWTAfxox9bzjuiHcqKyL+d93zoLkFMUJ6WgzDZ54YnGfSM25n2GXOXQYlpkbrjCeebTOQ8q9Ged/1'
    'znPzf5z62ydVQUt192Ylc5KajFmlgPblhxvVLTSmUKQOCPL9kKgCn3ZXB/bgKNUYuuvThzanQEcfizuP7/c6tW6yWO6EjB81CUnnA/H9vq1SEB'
    '47QliWPBo914dr6SJYLEI4Iar9AOj4DQVHXsf0qj8TqmjOKSLW/FWlIoQSPnRzS18lSinJxgmlVqTAiCr3t3BaGrSczeajeTsevFSmvMa0WVAM'
    'AqAx4U1fSL2aONPqdcDksfbigh6ksynFFdCqh+lbOyWb8xlQSLxdmE14h3NB/0oyL5RTDmJTdnoArc1JyBRQml+KLpDeQ1T9Hr15wMWUxwkm/y'
    '6ujHiU6cS/YmnpxQGTuvcKbysarErUwu8MEDF2vi0kL5EkprW3VOi0dp/FqyH8glRqrtiXBD24sdGUfM/mwSc7oE6a/f2QAL9dU6J3ZX3wlqJA'
    'VRsAIWZkhevJzB2snkDXjqqiv+wfqurMycKkqV1pUyh1qwDo/hRc1NzmjnTv467GoFuGrs7IRMV/HbPgVfOX5PlPCCsu87H+G3R/12OhmqmHjJ'
    'KYl13dnrlB4kpc+nU/uQ9IzZ93pmDfECO1coNxzVOEiJ9BC8ZHuWtlJAe+UM9Zrorv+O0WJ2K1Obnns1qL2APxORPjRfLyRpnAtBjgx1agmA5l'
    'Bih/GMuu983KGuOx/rW27Hm9szKayshQLpvI/r9S2c3kA56n0gDZQbI0EkP0Rw2PoLPpRq/nByoaohLQKRWh33WwYU0ZlmcMc6iJtg1NF9fc3D'
    '7sVNN80LSXhS32+431/T319D+Hhljf6B07myTv84wIjmLOuat6ytQXcwykMpv6APYskpWVgd/5hgZdde3I4icqzeeKG3r0HoOwoUjFFh6iGNzg'
    '/mDYHk5E9xAs3rA8IC6i/Mv/1VzwHnDNAHeQqQh/NAJsMDyE5D2dLe+FrqOYGSR4kT+EiZASPEJuysDOEW2yXcTHp9fOV0YHr6Q898x8Ws8639'
    'b+Z/Jpj6HZqkCmyWrygMsFmAwPMiEgAkdhtQOFIvcsiDve1dubPVH798lzrb8Szn0aucVhc5zS58QcBYQJ2PQhzKfBTPch69yml1kdMs59nLnL'
    '5Nf2zWs5NqKw04jw4VI6INyK6x7M06MmI7nVgJLyj0+cgriDMocd1E45G6s5ssR3zvHog9R3Vghd+N8RWw/bmaNR1W5JOrk0NzWWESkO4BXSqo'
    'QFcY3+qEC1pYOh1nePw7fyb3d5EzF2c1wPZG8U1WqF9fc6V/FTNnW62vSbO1zS1EboAxea1vH9ce1D9yzqoZXaafhc7szVk4lguuVQDzpDSGjs'
    '2ViIqRtGjtvTuZFhN8OqIs8/pgbdomK64DA1bkMiUQC9dh+yDcTJAJ6r0O7sSbHpHeG8jLpJhGSW1okVFunoKLd70L2GV2mbY2pJjeJZgHKibE'
    'fY800Odqep+raX0uLN5yuvHbY1IzcIg+ZzXmo5Nv6mUP0sGgOx3Q2yFHeSHn0o2KpmP25awxRPGXYIPTQbxDC3bN4Wal2mrd+f4d7g6zu79Ci5'
    '9wak4BADmE8pjIeTQFhMPnh7pxCkwiN/vL9Bn0bzXEl4+nLx11uprSKX/t8IbUCFY0tAIstBVtRWa7wfoaB7XjQroTJOr0+3//HzhDyVOyN5Wn'
    '3iYrRqaO6G7KHE8DUSH8ykN+a3OFNi+Ffjvxbvr00xuswmZIKQe/wtpHA47JizmhMBS64XG6gigxUX26bakXfiQXVnHVV9xE3QokzEt9z+HZBj'
    'DdhROcVOC3HDtjGkvicUqem3DuNXaKNIBtwv9oRb7pzAoGHpwHXbXrjQMYF8ZQmJPIc/p/kp0Qef5jh8DGg1aku01fXIpUNYOjv8C7tp90iEyT'
    'BTGfOUeA2xbqFiQAER9gThWKdB0vKAxZCnw5SyLRLkYRwegz9+RXOtRfd7inELgObyan5EEaY6Xaig7DdFRTyUvuZ7i1pIzgQH5pAI0Hgk9VtB'
    'qQi3k0Dg/Py5wsWMWtpD7lk4op8WNTBBjItCetOoLObUnhnR5lDRU6zF7MbFPEPq6YVVawnYlDfoD6E7eCI/uMqhymNlRwmilKZEL3FaItYdlO'
    'z5CyYT9iUgwkBo+0TaaiCi9le7Ub/qTXy8oTFTJlihFTjZHtG3YqqThc3p2cxoLuyu/FnwKZOlhKiTkfP+u0dEqcz6J0p7ILRkgWcEjMENF2Sa'
    'ZwNjoY4ISv7bk88QXplsee540nJgh7lhILmZ20tlGXjfKszme8MJ0cIDP3I6BQ5mp/V3qfr834dJ2sIIZeVR43S3mibWde5Qsd+k1WMEOJPtft'
    'vXc7p6m5iFBZssgXGwKW1QQvrhQ2HF+khbjN+pprx3ds+HiTZ7UXGGK2JzD0q5SpKqZGZYwV/mD09VxepbDU56d1b5Qb5b1C+kwB4JhNsiDS09'
    'zIm6QBYedpjDHg5JWA/v/hdPzFz/GnHzKT92RhPUjamrQjCERKly8zcYdMq13fyrEepEcvL/OmkAIsE4mzZVBgGXK/7BqQSt61QrXjqI3Ti+aB'
    'aqkbra5mmx2KiclpaeGpWgqiZcHNtl7ybjHp12ulWjnls57wmggNGTxXxZ/bEEfJvHFtr3ZZTK61NFWlU1tkMZdDhwaua7iV2HBjsSqV3Rt9Dx'
    'lcbLdd38CaIQ4TpTlrqefR0KepbjufRU0O30vNRzSyUQecVWCQIgOW1NrH9c4aEkvQ3zX+e82jgSldNh7fZefxXVrZLiZXhU1IUHymNQ1I/u7U'
    '5g9iQ7Wtqb83atYyOIWKKSYKsnH11Zvz42/fnF40Tq5fH5+f49fpN56/rXNZc/aOxwOFD3/HafJqe3mv6tNfrX1vw9NSr9bVKy8bZN78WUPr4G'
    'zD4Gxmr5bqtZPu5fjXzEDdO3K2O5iKOHNJ/ky01aejrfaZaNv5LLRtLIa2JhB1ctQ8OD86Op2COpT0IFMMTMgRJ+FTsJ6a6magr/bLUd3nIb32'
    'lEhfS0szLk7rC5HkU+3kjYVwuvGkhOxQZCOhFFLINTihq6JPlk++rdem43A96952yHODxloGxG74Uaiv1jrXiCtVqjg4mVOi/VrZbi4xeF6yOM'
    '5g8dV48JVqpEs5qV9S4dmG63FuRJVGgfNMZFHfkei5EdUgGqh/kG3SuGTlSBz0voi8YWDrwBz1BfqZwh3bpsWo6obsKteFPrQkyH/XVpXA0vmc'
    '0SPlDKFrsvgGcifSd4qV3Uvesapr5EjOOpXLy6Q0owRZOSOhhKO6hqbSvTkeFNUl1/PGFGdwPFN2M5k4xPn9htUrxnXFOBE4nitB6Z/rWzL2pM'
    'zpNUiREZKXPKVEI2cX+ZBX6idVvjzHsSVb3yzbSCffnQ2Jw6Az6aHz3WxMoXvr3IVESqjMTBih6oJjdvNk33DRdaYE8Vw7BQKr15+nZiP9eYhn'
    'IMOYNk7JH2IuLGRHsuWGSJOyMr2xbpi5d8IZQtbDEUbRl0fj3zqIbA2pqsXbLWiWMWVKYuUL5bi9sFvJtA1R8tSupEpRnKjtFt3VfEhlZwQITj'
    'jPpl21pXScmlfleslupZJfZ8zWs0aSzYkupmnqnlOfFod+6DpsJnzcdUvRBWdvSDFK+kadIldS91B2LmonPh64nZYQbFnxp+Y5Nc7wkXFyQ7pu'
    'R2lHWxO1DF4kZOq5VlbYP8o/MLNMxt1qlIYsp+YynDPlRX7JaW+K6f02x4HKiy+xXHtvipePDjGYRoKSZGEGEa5lqHCrXllKWR3A72JwkGR8SB'
    'XQlTeWm8hWbMlGw02fEadwRYN55ClVw/nQVQVMUo53IElJJ82U9l//uaaq7vxzbXXdy25ukiapROmR+NqpeuZOhWSvsPmSDYQBbPYku4NfGhdq'
    'pXyrkuoydcSIuaYaVSv6/NETLhhzL753zsbgEsWyNQyOXcWMR4LkFZ9pZajRbh23ULYPwKOzT0uP2Dvcz7fYTOtiXZz9btbMSIJXpwvJQ4sN2v'
    'Cli1izMpSWIjRMBzKKb8MSu0jFI2yp0Zkxlz1Kz28cav8Nv2RKhWbtOn3n4CtjPc2z4Hp6W8dI6z3PZ1qaBzTSOcOk5CbqlVOVYO8QMSVgVXpu'
    'riusyq6orcvJ1DjJGnV4sY5EF+SwTBYU4H39o2QSpVgOcIlXLEcmUtgMEhEtizhWqkJX9mRc5RWvpJeSnGA0K1IHSxx5ZZZZz5nPCbOuk8jxYI'
    '7bilCJLvciPpUmmCXrWelUadcMLFWg1OVnXHjNqbCEy0DYPRBPDeu18YyxaAUPrmxGFTJ3Je013q7cPDDe7nVRZw+PbNSiqfm2wzuF+H8+f/5/'
    'sKcDZ4SVwG/Bh8W0j2VjgDPIFhO32LmtORNVbynd6EDZ3hhfVrpVvMZOGll0YE768kv14g8pkc96v3DuHtMuVxRIv2VMfk25RJw39tMojVPXAq'
    'E7guyH12qmBrELMwXLAVLyt+vXTt9//CO1l9HVwFHpfXxxRbnxmEZ707XrRPbELYVSdFJAh1hMuXAS5IRSnLy+w4mbHBs/p8epMnn6109v2z5O'
    'lPWuDJk1d9HwQqE+u/yZG800qRI3hDhd9ZKAu7UuKSA57tvD8dNSZpIiMhUXljw5aeac1/ImPWt6rmzArdU06+W88TddZwEmiLyIBc+lgBI7M5'
    'vcf3PxykK6sU5HzCpS5nhVbFGX8VZHNrsoiBz0iLMWluh/k4FfUyDRNaAkDhJzNr5R+ZmdluYPaV/fFylWketfnNvILN9KsFbPfPnKcJnUEhaT'
    'jLzLyKelpalka6jJzB+8NfNR6xXoPXYDKsrTLv/I5jJe4cPPXOakWMUufZwhgx7b4pgU6p1Chcr5Xyu8Z4xXyGDsHJ0MNfp4B78PSpBBkoHU6+'
    'roq4rcTqCGqnpnmRs/w+UzbB1ulrlBMpJx1RY0o+SvNFbQZ92kSqUBmBT3H2Mu4GFLa+tNT7NV1Swh22ialowNSqwkLy9TbUl/PG+LQWJ2NGEe'
    'HOYpqrCFyReubtKK5XBSEVVJWAWCtW2l7sIbiw/oa6kLsfS0fHgqF/btqQsxQcKtvuC8oB2yO4uK6LqnL29yYWtXl+byUmfjGR2pt03UaBKIvV'
    'T4xZuEc+sioqw/33XLPR9y6l//1mEUbKQhMS7gKt+S7W3QlY7UcXe6ayNvUxiVyOehCcROUioxrZ3FXvW8FHfTFcAV+6jvpV/kBA794f9j7123'
    '2zqyNMH/fApY6bIBE4BwIwmRorwoirTUrVtRtNNutYoFEiCFNAkwCVASy1at/tUP0DNrzQPNm9STzL5FxN4RcQ4BWc7MmrKzygbPifuJ2LGv38'
    '6+CDU/+l/ESHtzCK1Yp2VW7GUqrKWXLIgWQQg0V5huivHzvB/gyAeZwYlTGu6I3WfEelZG69bo5alLM9gYUCKVucvV4m0h7MMK/lSYj+b6krNn'
    'wbcU9z/A/4aBOk0ZCJYTUuklkqpuLfh4Ypm+eIhBG1XX6FfgEgm+qChFc1o4ePG61WxuvDFbTsgpZviCK35v/8XBHjXpmiH4R2xYHGo7axuNbq'
    'dl2ljyEm8dhXWwF5EkMICyu76E18GaA5C9vx1/nbu3kxPyPcfPnpiQFL3ZJTAlBIxsZYroEtkCj1WBx9kWDnUTh9k2dJHHh2o9bvGOZhEc07uc'
    'jkdDxZ1dji9HXrLzDaE4ifJ9ZTQmpR1ECk2vgif0zLFzTXxD3nIOS97pXcL+tDlZ0K8J+5VUcvAcxnouyRCcX+joBIZ5gq6Raq/HhiPWBqKC8d'
    '14iJkQQkyWHG4OouXErM7lM7SEklSFY50kaHWGWBRNW2wxFZCspqr6ufanCteXvAk5omzMJw/P/OVEuqNw1UbcoxUFlG/vcDpiD3P5SqK9zHqW'
    'px9cu/fHruq8n/jTZZr72nnv2yZph7mdU7X0pyZckQY1Rf9jMwo0f9gmkRpGfvCx6zIMRnlfY7I0cg/n5vko2DZltVjgAUL503aLTiDk+xpTGi'
    'Oaa4ED/VI7Lu9c7Jqw7TFaQeUKNAItp3hXSy/5B+AtJCV286o1Y+KTcS2OjPlFbsCZYjldQjd2l821qFySHfKVS5WV39tq8ugSGy08hCFe3mQ3'
    'jA+TiDZiLgKA3Jev3rmEE1F4Qi3D9KeN2t49tQyRIJw2Mndm6LSCf4JtlBUTpCU9B2WQoP+GnWsjOko3o84KV7njAlShlrdttu5QIjpd91yZSF'
    'sImIrsInmMf/aNYLtxDg7xd/CgjTHXWbLB26ElFdZx64aPq5k4C0EeT65u4bLIiI6MFqFiSOCJ8LClZDA9sRHCxUrmjJTfUk70WoiL2iWh2CiM'
    '8OvaO6tSPVbUKB0zSdayjFV9a31cicUASbCZ9hiQF5JYlKqKdXAiNVIGTmPl8xLR8RocTymRFGlP+fDNGLzFMYqE3wlnwogVQPapSbg83jlXx8'
    'spA3DU/TG2xx1HzRQKon8Mbz/CvFl8TanwLRqa6D/odDNRVxpeEkfGE9MW40XAmNlg6tVwIm64DJnILWITbut5wardNNtGfbovjMVKqcUWVLGV'
    'KNl8Gbvf/L49AoIoO0G2Dajaqu1alnoEm5o2eVpq8PF3ETE42Rwn1q5AWnIX/57IGj7VOhnJIJeGFKzWFhWY19tWYkZl3S0iM0QzY76FIBUYmc'
    '5ZyApcthjM7cdD1brS9N+lKxc1/LrJcrmantQrZ6TLwpAyrVhqltl+DB6Vi7sDDFMQ85FwbxaZldBgyvmP4XhjQLzSEZKLV8GKCwZYRi3j2wbD'
    'TidQUv8YjEed9VayT3CxEqo15vDmVgP9pZhSwSH9ehYgoox5TuWz54yGAW2mRaTGmfg6/GdgKeo4VCGhsbCUo6c8FkXRxyFWFZXgYACBvFe4uy'
    'Le2yfRA8WrBPkVMTf894wvjJjB4K6RDfEXrvIIIz185p5VyhfvQeDTQqODXzLP6CO5TNrqzobrB/XNVb67EZrIREXK7N6Np9eRzOA1hZzV/L1n'
    'zgiRy1HhIK/rdIk045iC3Ko50RKlSwrezMN0pZoD20qqRmBD9C1aA/KLefhdRsYTLUK9QGvAFyhBuum0hUEZ7M4tOxWU6BhItWC0CbalhVQLM/'
    'HIEpbD6xOi3U7KBXICJW29S4c9vaQM5BUHUHFXI09QkOog4ukLAnzfT69+npFhhFcflh2jiI/BPH8KoxRYpOE/nGIj+OkVYEXFFWjcgnbHvNhm'
    '9L5QT1ZQrEglV6xRwQumrghPzVb7WCyzpEBYOuA64aRPp1FE95SFyyxVEu3fuVjiTHTt2AeUp1ynaTBur+ojtoflFC0QsWRMrwoNyLhNb7cXN5'
    'MdE32lEt5zCf5zYUNvidQX9sQbUzzdxcFEq8UdtafSKrdysOnm+1iiFpGY/aANcIKT4eSyt8I4q/QqR9vIcA57edWVRQHQmAF6pAYnICXcaqdK'
    'TliPrYHLuxq4DtcoZQofYET8T1lWpSq7FDR6niNBPakgXpHwVqecGKlg+xlUerhhFK9zn1j2nITjQFBESaMrrSpHkNyWuFWmpq2RZwHju3wpEd'
    'pjosDSZdTJ0ZQ4L60IxkVELTQYfYiHN+7eFE8+nOAE+2Xx+OtZxYvPJAygad25jtz9KTWSMJoWZ5pOwF24tZlSwbkuJXOWZn+I6ikvAC2P06Fq'
    'rpQQwlIyuDARvF0MT8lZiRhesvu0qOQ8czD5caOd0r5bKV8hpfusRphFZPglpHirdIiD490WMhkbgUuB/GGi0zNu/sDLxG9CMJcEsIRYLvJuIF'
    'fREnwXCxTkr3rlyqmkFw04IjoC0l8CGxuMCsoAcj1puHM9jNsCP+MYSES5fKPOjeFXjT6baVWAwANERnEGyQmVbN8H1bP4GCCDpHw6avCVbxSU'
    'MlZV6uxIQ0zuzjlwJXdpruQMY1ovvwTG0p9HEoxIibDnU9HzZzFbSCKVm84DhzT83T9UcDMIoUTAUpOY3sK+qV6+JeeVCDCpERvx3KpiYzNRaC'
    'rVpVbGhzayI0cqTrmOKHmJ3ynYJsmRbJtGdto1VNGKhPFV0cZslWLlCJJUCaRNKGHQeCPg0k3vTAtYnPhAgQ4k4Jk2Do+gMREUVVgL5SDp4FIV'
    'T8QPADASPlBQBaBLw8zpwOGgwIYDPgyA/c4Q54YhJkA+BP6bYValmozViUQBQgcMeEUBwM88sudiAya/ljPbr3Gckjomego3X2szusgRF1Y9Co'
    'NnvAdjbhSlnWmwHTX4HUYvFzZ4enp7i51kiNejkhFau2WuwW7U4JMJIZo16esSMG6zbAVuHXBvM9YJDQvaw+mXtpcoQpcdcNbXVKF98sGTKgVw'
    'nVxmfS1cfyF6U8VajOuVm5Bv2YODqs7C6X50NXiP9FmADgPM4SyKcFVJEyxmw+UVAlyJAWiz0FkZATXRUP4gF+DgXgLfDzJV5u1PZVV/kqq9Vs'
    'YDOQZEgg4y1ldeltdV2ySmf3bmVtwja/BPzkqR9NFrlfQx9g3ruZf38VEBs8BnWmi5fdxFdtFcyEbBgnOgVVnlnz7zkkubds3X1nBFfo81p/mX'
    'dxK7hR8akGCE5mt6tgW+gOiESWRzLgT8p7o+BX3/WDCxAUw7RBwBl8XemvRCnMaD2miMXMxkPHvrlEbqq6eZS379dSWSjQJoNjk6xwU0ejcWiG'
    'J0iKuGkCwNoT0TDG23DembCJr4jfsmN/abaGoHzkM39GHqWM19oX7eLz/olNQ00/GB5eBtMkDgI6e/YZBqcJ2eHSzs7Wz0CY1lLnY/+LRz4BL7'
    'rDz3/pdRL/B/fZ1yPinQASBZXi0EAFAl9W2C4sX1uElmFr4auJVwZ6TAapIC85cFMMmy6Qq4AZs8Op+XIJRcS0smiQhC6V6u3cLS3bR0SB4Qin'
    'XSYjZRAJf8CtFXEvD00Ew7bkaw1F3tdoqLnk7Miz+wWHgEKXUN28LYzZyiwUllLGkJxWodwE/Rf49BTHx8h1ijRHPpzKImz4oEhkJFasDZUrDU'
    'pY8M1wApJ6jrOifX2KUyq5RH6R447Qqz0HGiFRazSpLBSLz5C4zHIavDf/zv/0MxsCE7DNguw7QxNh4jZ0MouKj8IX5Xt4VtQFOSUka1BU/OVW'
    'MXhBOBKwOVQE3auBnNGQGFeE6VR0cH7zrtMyW2tz7NxdH/+JYS7ZDkTCY0aArjPpwyetdr1KCHkxEviR9tRcB1T1DgrFIjZ+gOC8K6Cwaek3FQ'
    'bO/YFUcHV1zuoxFHwmH2S9B0gGHTD1lEZG6GHPzBcPdhdHJNuxrNomTGA2JOU6CO8XoE7hPgC+QbUNw1KRq9XtCtGGm/zbKgniDZNKJsRNgjl2'
    'UoBDp57IT51OWROgRYdBQZZiqsyq0VevfKrDfVSAC/9xV6d3i4hU09gPeov8E5webBUFXUoYzRrqQqyD6Df3KzQgXADJjzQUUSBvI0xKYPc9DL'
    '0mlmgtbyA3LqV1pkCZMZ+JGIExXDpFz6JsmOU6/kMT620buG7123G+nQ00r70RB58Wp2vwggtl+MhmOgDGjbG1DKLb9ffWO0ONVR8wyQJlTWJN'
    'LXMGl7WnMhHYhuL9NA0349AG+4hvwqy1LQVsOxgjJccDvI7XTkdo64okFGP7i+zQxBeQ1fGA8cpp0enIlqkXBjHIqMfIGTt4i2PvMrFX9DBVlR'
    'FbAOSVowCNpJFXJfC4oi0R0uB7qR4kkFEfKdv9p1nHQT4L1eExgd4JV9RWigNVJqt4K4CciiPoFWhln4wgXZcQ8BzybU86kufS4uw+Ud6BxhqL'
    'X0JBwSyPH3VFk4M1AFKhW8EHyJ7qy8dQjpfneiShf3umfHyZ5Mm2g+De14BVCl1eBvX/XbulZ5N6u05TFesyuRHj1GJNHq/3yhnTnFmUVR7E2a'
    'I4Bb0ctZAhP4hVnikhXeV5fFprvV9EWJWG+nqE0FrRyqainlmLsYboKriWfZkxloZpuVFDzqR+PT08p2zmcwnaCDwCpanq0ib07bmRWGCNYgKR'
    'D821RnWbQjUnYW+HRSTlrSzDGgi99ldRQUd1nFVglEl7aZSn0QvIAUyfSUIVwrlT2siLZa903w3uXv2Cxa2wJMHCt0I08JrzZ5aOiD49mBuaZS'
    'QNnqosa33eZgnzy58PuzUFTpfIKo4lJwRaLHxlZJcq1SwSPKnFUqdpiUWKWSh0lqVSJcmLRUSsRQWRgmrEsocj85RlY74BVcjIcNGyZL9u3GSe'
    'LuzqZwF2GHZlvvFOd8vUjpTq5toSWXjjMOuVO+aQRU5QLtyMYEoekYFTKe+KQfynfMsZDso6azWbgdeH4TAvgORg36rUQZ6EpP2/gcGtcAuNCR'
    '6DDZx4ElmpcCu/QCFukF3HHynrbZl+xvGyltFnYhLXDuzXj+aJK2pJtPqZn7Y6nOp9ieZEHlYS/tibHImlsShC8mLWIAMhZlg1aBm7ReMVSHuB'
    'wK9gEVDL7fWkmoqWaUtg1aTp6VgrRba/ApcMV+daf/W+hls2JR7ZFZ8akGiRHedPLzgP1PJDWzK4T7FVllfuyeGl5vfnEZcxJqcCkqJPm3fMVO'
    'qk5XwkqKzbIMwStaj+AcSyk8/EqS+DJjjyKSC9EQjj6oOmAErpkqhuiDt5IF3rlbSZB3nFTB+BZPme7MPeQE0yRxTfEug+QFUA/jRLqJRJUcYb'
    'EBJK2emxPBlGQSED9G56fOu4USEnN+YegbhluN2CbsFVgmnwDKY8jPCbxju437Bqj1B9Dy0PCxAkNVkvHfimiKYB5BWu9dvJ2/R0lowL6ZpO0Z'
    'BgysKY2qTZb0ZpgDykE+tR0WqLOIMfPzZ0fljAxxPEJxl299Uiv57+WXDvkGUh3gap+zezFQp3bQW9ScwCUZjZ5h+pSvQ3acEbizQfYvEdZxVQ'
    'Q4ZFZ5tXfofd7HF2CyG0xGyJJ4LB6VoOZ3xQ2JaVQMcBnIn8qKQr4OKh5l81MgCU1rQfEnOirG6TUKIfTG8HJq3Wn41H2JMpFoA8OmL9TqrWh3'
    'XUo2t9FYqxDToWOYkUw57mArpNlGE4gDK5aOiEBV8T8odI5aRCRTOF982T6tbRUm1YYWbkur3V2nOBkBOYaNtN46vZwFgDp033eDD3lp+Ii79g'
    'uJdVeINdNFotaSutvBdTtUbY9CizGOXLzqmyLK3ENXFuyBIbfRbQvlDtL7v4ImnauUtGxYZhs4KSVKR96D7mv6qqEP6UZfFSdo/E0BKE4d+ygK'
    '7qh7YkgeNyAU465C+ZyuPFZvYPNA1DlygzLoicalURHBr91YhwFZv0h23dn0HUCStLiauOxWE1cwVY3MdTcYtDDikQ+GcTMSj+rb0UGrqqU03N'
    'qsSQCNsslCSTvrlfCuMQzvlWCcNyGmhRt8iCen0+jhotHQO5Uq5xlFdXrNhWNwmnEM5IGUmITSLfFfePJqC6qOLB4ojOjRzuEOMk2wo57CEhjG'
    'ws9JlPSeEyrmfIPHYso5K6cFXkLnqmtCvJTPF/mthYUVgcDLOLyv+eKQA+x13pTDPGQRZc9n+o5jvtU/EUE1rBjfJMkSJXF0DwxGVGF43TlzBR'
    'pdU3P1+AqqQBpNxZHjSiJqVAuO02Ylc5z4lFJtPnSA7neOSsjh+YjT1ddMIKVeUb/raGExZaEOhPMLLd59ZF5YsQhNJ8KzMV4AbF7UcGDc2P5+'
    '6FXa1ygJSuUl00YjbWbeTA82M66hNO+mn08gDTgWPGO6LVEx4l3naYYLAFVtnk/PxicUJAU+kFfTD+CuNo/CDThwlPvDlsypZ/RSF5EHpijUWN'
    'o+TNg3joKCtwkCQ9I7joXyms+mCYgnHC5lqVAUZ1oib7uUpjSNNg8GZPEBnoE8Ed88b6x+rprcTF+hQoUw0qwYia1/hX4bo25ORyU7AkpFGyLd'
    'AETJe63NLPwAGe51utkRxe4Vbni10/Vyw4Ihsp/sKB/aumKC+uQwmJ1OuSjgUF8RUHHRflophbLg8Tl2OcawyJ2diCHlSFAe1DC+uAJptRF4pV'
    'uK+DtzAdULdpPspOvRwntp8X0kijO9iz6u2N1jkeRzHNGfa5afm+YYoprKpuK4vOAERDInispNuUSpqWqib/h9rtLPegNl2D2VLvVu7oauR9HA'
    'vdAU7pJZEJdEJSLWWMp9OpSssiArPmGusa7ilVfSkFkO8uvRwQbvAUzTjgzCl/u7dRY0ffyKGOK/Nq3IGdW5hCX83J2vJbFe81xBlkVPN/Uqa6'
    'bh7J4UuS7L2WVEvAUO74r18Ss6ak7tvJWWP5D9y3hzyaCdHm2rYKIB4jWZ7j/hSW07D92PZQdzLT6UorHyy60OJHuQ8woJcJTHNOHAuLoKwZIi'
    'XP1tyI/HJbFb7ipzhsstFUHN6bVm1iAXhlnXHdsQ4RANnFolujbtFGL8aReljaI9xEELrmu/NvmOCUMwalI5TZUM62OB4vCL6FEpRV7fNIj4SG'
    '5p75AsLUIWXe1334uTFQqxd2GHoCqzYFfMXGPkOoEXmNkRDMb6nl40nfj9Q7H4XfqlzTq6mt4I1U0WNCqlzU/WE02X6mRL8cdRf32FrnygZfFV'
    '6RYFhXc3nyutfIOXdtTp2Z68ha62ldvZakBRZrliGMtSCMvSWPlboCtvg61MrSN5C0zGkfOWgxByCb+bQqoqidojc+xmadhclD7WUdj7kmUw1l'
    'q6QD9qGbhLbCeuXFuALG/kFEgvvf6quQiD9C6nZSCl2y0zzgcX+iU89R0zlMAVOupIlEkDUrPu7e87VYyY04CisMZqs2RF8c7qjk5P1ZIGUwuW'
    'fCht4YL8wHfqSgzaavvbjC115Z+wUtKXHoi/6N9l5LNEfLq9TZeSkD5WwW6x/tLP1P4Fh1bcZp8212U2bIwzf+R5xR9C2ZiI4Qbbh80bbTG1ya'
    'K3Jo8FbVc+BPynDj2137pZkDyZBIwvu/uwN+Hf+/ugc/TcMXeCLr+ipyLMSwUKR85K4IkkaDxzZ/GRKCF08IRv5nhjco7zObRFh0mN3AGmF+Bj'
    '7vAEXMzdvKLuiy87OLhmbvhjwZcBh3ZSM2y5AwiyAO8dSb4DlINLBMkSRPIhuNpJOYDkh0Vot+7iv3v07z79e7cCfnkVWib8u0XvWvSutetb+4'
    'HVzihtrDdAEboFLie4Dztsj7A2izSN4lJaQFmlmadc8ODJ8IM+h0FkRUuGEmqlKD0XaRb54bD7XQGKNTvdcmkr1EppRksMKvr4cypruJC4Jfbv'
    '656WmFpOdJSooVa8eezGqfCG0ftl5TMQExpJ5/T01Hj9lB/ksmNceogXNPNsZDQDn3DTLSNGfPL1lyWuGPYVUVck0T7NsBiojCej+0o86rhJK/'
    'qlcoaEcnCeWqBudPN+2Wbqhkw1PYfB7j4+cBSEWJ4hm65XDDyKMEOQwnQ8hNON3m8XYCeX5wIp6XQPRIhIPECvJIS0mCjPTurvxTPybzs/Z6I5'
    'Q6pAzsiVw3+Gl3elv3Ybsn0S0Aq5CkhVpdOA7e/Gj7/NMGCPyLuGTExy82adKRl7YTCh1d59e5XecMnF+F4k+lu+jb2WC7nLT2IPFzigZWew/O'
    'zmj2Ov1e6Zs4gWQFZtg2oSnTedARU0PNOKMmRWtR3z2Y5TUp5MLzEpGPljwMYJzdE1QY7gGIb+5Y8/4g7+8Uc2VsjGhN04x+ha1B4F0ELtp+w0'
    'WAOSugeXMxc58MKLqMvrlp45Ex38SnWLx6CZjmOevtHqFrItAQkvTpOVRngSyc94FenOMMpzS9mvprwTCvRdY9F3nW7lFVVSG/VTYbBl6impUK'
    'fiSa5c1MXjZ59DIuBZZa3dDd4pYBVBINvxnOP/iIG6y+qCywFQ8BqbyYLzBOwWsNfADgIzF+55F/lw6h3QiSHCktOhS2JSHVTugEPFHecRY6JQ'
    'AY/q+krsY2pzSsANN0VekuJfPLuZIIrBZPxvouT0PiLQOcJyVH4GkCApDrOAychFZQwKJ+yJe06Ym1dTuLXQohBcPc/HjJs9Z+BeN13oALi58e'
    'lNZefl9w2CjGkw+OmL7w9bkf50gR0OM8Z9fcQbuzyrG73jw+Wc5nEvHsG/6G+B1C7yn6fq/NG3bTv/BEwiu/58C9ujB656sEm4Ejb2dnDOBWeC'
    'Y22IFG/BmUaMCo6yEvMB7tAGCZJd+SKqqM7xIFIXIwU+vLjcCWqVvj1C5fqmja2VRbVNi+iaPk3TRFXDxHLzys3oE7RMJTqm8NmeBPhN8ibUrj'
    'scHzJgDpCFKnTuQLLQdJYRjtRciaBFq1k0UeefTSnGSqwoNmZPxsdnaoSuJMRVo3l6U3vXkGTHBgLAhINuV0EWw+YGErvnmwopVgR4dWYd606m'
    '4Bc4qvxIV9ZPGqEUby6XO3mK/ANeaOjh3vSh9Non4F1AQ6U3uDSkuwWT4CWj14aZhtVz60/2UHbUGMxUJno2gS9xd/J5hKb/RJ/yiMy7RzC7o/'
    'cuJcanZM4VC08B5/N72vqEqv5lRiiD3j2mA3jL6y3JGaE21mqCgRdE1unEix0q7/sS9sJbLI+Z9iPoINlsYadXSdhUVpEgd0roNOJ5SoLl2krs'
    'cRDLkq0WuBByVsF2VpHmC29X/p2LbzEWtYzMQSdkK/0Lyec94Kw4/pTGlxv7rbo3zxipJGWac1cncRNxIwDakcVLOs8TN96f9OrcujgbJBNSDJ'
    '/8Lh8ZMZE8VxnCasDau31uvMQbURN6gel6ppn8ZO69nYjKB3WKTyTuaqFjwD3rYRJaTHO/pF+zb7+mN5LF39J4Junuu+3i7gmGEQHecZeDg26y'
    'u+PGcw2tmkR2H4sXPLeEX9E274rXrWsS7ue1GKejyALN14o6sjCPGUjmlRh9ObeFYvwGonffouZws9JO7Q6fylglIuUtjNUtXJUzRRVZ8bRBqp'
    'SrErtUKVflzFNV9dcncVWFLFW+h4VYKmccy7JUkU5KC6VtzcHBWtKEYPw9bhve/6pZPFwSnl/2/WP/vpOvfxhs0rI+NIpOjlnFvS+tdLAVxToq'
    'o2SOV4XGqsdtAY/5Farz1tk45dWmNYk0ePk14f1Vsia0t0rWhPZVyZrwN75lTdRWy64Jf/vcmiyzIEA3DsExzyGMkteNWxajjKA3qJDgkPTKuN'
    'GIc4zjgHKZhHmTIi3upJmEZQfHqYRp9jqbtm4OFw9aa2Ui4LA9XS0aR87l0RKD1lb21Q+20Wg8+WYtJWoVwcjvJ20bOkdWh40yyNqiKD8NAONz'
    '3LFCro6qF9I2o2IOTIL4dbnshdNEk+ZVEog6AkPGW6LpxnAQOWI4VX7WAsqabooofC313rzRcuCfvc72c4+V1ecDq5lVziMDraIniw1wzQNlFO'
    '2edqza3tndWEHlh6PVyv4q2PatgkQRP223inXKXCvWJOdKtZNSiitKBtLLDqR3y0B6Cw2kt8xA+tmB9G8ZSH+hgfSXGchJdiAntwzkZKGBnBQM'
    'pKjpQZEBIc8OIkgmhCr+jLjmxMEi9XYb381pM7Mv71dyR7PJKaMXMHTkzvMCU0WAX+QV97B29V8F7NOwjmB9/sVxkfPpqznZ49rrtY//moDYCf'
    'VIrXcBtvq7a/A89THnYMC/vsIIWaGK2kPiGL04GVd2NEty6DQNGIBT35BKlqNAlfYE7VDcaEOGBt8CfQB+gE4fUjJ4sFOF9PPR8MGFV7K+UG4A'
    'DLV3qe5DJxif2rTmRlCD+DZqQo23Vn5ThqmQ9EdUaByjCjb8Y5VMViU9oaC/l6BZGmM0VQSgiUkwXSaTV8pdq16QYgu9uBwiSa6uq1fTPj6IrU'
    'zZNkNanCj3bfFYtjMDiOSh7DTJ7oSt1KmzXc1OJZ8mCd5+OmJ7lezG2XsQTdFuiRtyplO6pJvx2bPdtQpFYs9GoM9DdwFXk90sT5X2891MBV/M'
    'miupxXE6YWMdjzXjS1sKeq+2geCAl69QvRL56JUi79u4rBkyp75RYna12WuEr0OnsMnUd9GFsUso/ACls0j5Qm3w460IMrYYA1i9P4tKnKVlNA'
    'DHdgJNvLUS5TtFU+cTyusGcx9vqb/vw2jV3xZ5E+eomn3ti73heZ9m8V1VqW0/GfV0cZiJz7tnWolZEUAUMHgBdf3Rsbk+nkH2INLdK7hYmyXO'
    'H6f4KDw8i45B7iQrWB++GvE6Q9HqERtr/XtFPFRiKLeuPMPYgoztKB/YV9421gJFDdqHgwPXLLi/UHo+4/vh0qxXfQi0ufjk/pkFe2hxSniwns'
    '7EFCndwV2Kbl3ov0UeH9QZWUTH594kygGfeHU4f5HzMfhAAPnqgBvJZDxnVN+ZH2szMaXnF4L8SRHSg7WiwbaujgqllhR5uKGc9Y3r0vXVcx/p'
    'OaFla78OctxqJff78ZvI+ymbQazEF/ozdI3nbObz++CNTn81tCz5wCAnkIMvFpI0Rdu6aNBshGzMc7UN3d+6DAejuRL8l6Fyc72R+S/9HtWvDn'
    'CWF8E90KVCaoE02cDyNJUWgdI8PXRU2hPsby3BrmwWkXgkFNpAjn97VoR6gIMDnddxieqIm7wV+8YWcAUL8gWKqiVpWD8Hd7AAUWSeC42X2Pz1'
    'hEiM8Cuzc0oJjPmRHQlKc8PEmelKyY9rRugbz6Dv53CpbLgKSdAkGROoAcgvIGM9x7BVapiDVTEWGqzSlf6H9rq0HNpCuMq6LwereA4uwbOI3n'
    '6JtAjCfMeYPJWuO/b8nV42wIXhdMWmr/xyf4/dQjAcpgHpMCYS1cljAmcmcNrb63syTVTzLvxLhfYxIW+zf+7+Xp3TgVNAznjuMFpzqabgzjQU'
    'l0UcsYvgx6/7tpGswJV8QyPaf5TAaCLWmMsxCvNSkJBoj1YZyVUmVfb4Ay+Yl9fgTNMAvJMvvoBRgZHh/bC2ROwfLslKkr5Jw2TH+ZkSDzs0Z4'
    '36qcee576EDIISlH5xznn8mXJbRIIt1XVnGmR1TEKmTE7YmGTrRdxduaHJ3dHKlEwHbHvauV9l8wygb4QujXCCtTgPLpZxV6SnuK/DlfSmCdTx'
    '0BWq5lWnh/W83tQ8TxLJ7ofT9pW7PgLySxyioFmqTIqt78SVTjbk1dXgJsquheyy3Fuv8V9vMjpdgEFDFw7aKHeAAo7QMjq8kyp30V9rPCnLJl'
    'Yhoo8EHW8eWw4mi4YbmnI6loy9Ua1XvEI8M75PX3t+cTV82L/7PAu31Q4tgDIU1NXWqaXZTekm2/uAWiKkwAj3iZnIaAf5K430Lj4wHg3wV2AR'
    'TbKL7iHmArdFZBYcad6RT/Og0vvvD0NzVQpXWGvAIcaWtYO9zncqYEyAhuHSCBJM2exyythO6o4msuhTeMUtERYEzQj03Ywo5T2NwqiQUgjAz/'
    'lNmuiUyNrxGe6EF7IA6aclrxN5C1+J6iAndOZOWTVJJOq2Vz1NMep2Wz2ffTRDJYophVCLNPPptHAyfAr819bM6SIbNWxW34TlYIvypJo/LXnB'
    'npLj4A88n/+yrJqicqO9ECuvPGP+ITYu4VMSd/h6QrN0TtwJa/oBxP9GP5dgGRUKrXSpg1DV2K4k60gjanwooxdEgSDqZQBC+esgdbxJu6Jbdw'
    'vbRGUN/DfOQiPfVbHwRmORlKwoAeI1bofXWgYC/RDUWsUP8ybdHwXKk1+3gxCeXabUwBdtohy5X3juIE7gRstOJR0UO8icsx0311zJYuqlwzaK'
    '1mnplfr4G9au5PzkAh/ZwXIw9znqv465dh+NbhtjhJoSmYShanw8u2Lg41TsVa/LUJf0NyBlrJIf1k+UqIfVJJ7Hd+qRKPGr1sBgOlxhvIN4J3'
    'YMlix4JRhWMMrEvLN/uHfAEJQ40TonkQ/BE8yezoI23QcxTs+jpLt8awpIZ13AlcCUESwkLkZZNAKU6reWZu9VejvsfsZZdZ1PK5qPsKsl0yUr'
    'ESHL/+e+DcRs0NdRChKdS8nsPOfKjKq4x8H7kCaaJH3F07i6WuonUewpUejzEDRNgO3RSd/kFE3KmwGujHYt0jEVJU0r0YWquDEvhVBuTlS5gv'
    'lPwvMgNkICu0ZOa+iA5HgT8D5kIYYtbsTb42bkDIHGwy3Su+aQQHn/5xE3Uq8M7emxz64e/dT1Zd/4eOR8WCIPFvrQrZxDzA9FDjH6I4evZT/x'
    'b/zAyjoej7Vz+1ij6Db8FAOnv8C4aSW3lCvJrfsKYeYpXUFnt9X57u7jkFf++BrBIWHQAaOITKb/NrqaShCYSpozEUeRKL8vpiwBKNbYPxt8oG'
    'MMyRWdAEqwgvsSqYZh2m4UEKa9D1uF8s5hZNuQWEumsQSD0pdRuZA5jENTmfAeHRBm2SkQ97eVs/Mxk2WnwSMCGhCTlnDCh27+xEaWo9ZRWFho'
    'QKIQoMCuf/z7+89TAo245SLDtXZwYxbGlfODnF2dkCFku5LBKwM7V7842K4fhdpFcXCUOTF6VnXdqTC6Nxp6J0RwX08uQQgMelFPEp20CCuOEP'
    'wQCDaW+3nJQUZheON6OoMMoIhL6uz1p25MZ4SP5zMYuFQEpMMzkJZ8dSO1nk/FX2IGYSyE+GFShRPp5g44N/YxsSRGax1n8PLnnLgdzDsUqXIF'
    'fNbhKMZHWIJ4gLUiQRxdZKZKWUy4wNi8Rydx06dsSl4vjRwUtzQ4P4NZzt9e8DlFyGLUzqO5a8R8kcCXARnyULak2qsjIGi3FtbrQlAgJRKVy2'
    'KpLmKvYW6dk/ProThd+4WQJlVsAZKR6zMB7Sad4YTSuF3IzAJOG5Ezgs0hmCYke5V7mISc2tTrz3KAs1FuypIoBPgqRLl0wb///dvpbKSSRXx9'
    'FdAU3SeFLbcX4N0CeF1o7Tl9oZnZhOHlatu3cyB7i1aC4erGk2wu8Nd2Cm/07BYKV2IqaVBA4xTntou/CUZvKoPkAGZRfBjpJYeQ6rcoEbFuOE'
    'SWKnRkn9iDvJsCVnKA5XJ9ANVFVypOz67Nu8G0Q943YQQs0ERXNNknCLl19vP40rXjc4/RHa3pB/UAGUdJPpHU8MHoA6kp5s1F7hQPnPJWkgYx'
    'OrydIuPhViTGlEB6aysqoNpdMmYDgKjQ7RRfMGgryBDv3N51PagkyQmiWyYPfbznA4OWTT+SLR2uUir1eERp1bYreXsKGuD7GDKyvhVVnO2Tvt'
    'MkMfNr7GwOHIjDCAIOVJd8fe3XAGIDwTzRl4OcTq8ShOGquRZqPvIZ3UiITEwcQJ0jpJhyxG3Mu5WeSTxB3ieCGEwFVEZ6yBZ64ignIRjCsZxz'
    'VOUdl+vmzkqAXaa8N5whj3INEvbteMoR4TvgrzmjwO5ROCZVwqkdC7FcCUjGPZ9744KAGGlylClqMp00iPMlJ8y6TwGCZ+k9xKmfBeUGEnkwBF'
    'Byh590gvLgdkENP8/iBrh4GfRv3bIVnhUxX61uKOmur2d+E1x43E8SFOU93WxVy/hyL7UVkzWGxxo6IC5b9oeIggHyUb4PJm4g8VMt/oXfZerK'
    'kjx2/nbyo3hO7qzXoPJZ70oAINxKl+IG4+ksI05QPk74XmB3lgsEjo+rz8012nSzSfZB7BUp8AU5wa+E5HrAfExkWwShYTg9uXZ4rBL5v+lhpZ'
    '6DS/30Sl3UqE05RnYHD+kUtTQqw98LRoK5Gg2CQI7XL4CujSjUGq+TscA5h1RRysYcn5zmnWUgnXJ3rzj1yQ2sCMtwatxaLrTQbUjRAyO9i6Qa'
    'dlo4m2he2vS6JtiBZzdhewbrsdgLaBtnhGi1A6Ne9SbcrFzQPjwehcNbTYlBzXTLJ6DQxfrCCuaiUTYHwuppcN1uHt7MM5DQ1Qncaj24iC6UgK'
    'MChzk7zqkihAkrzdeMc5YE9U+Jm4eIQxcIlTFDt7IZsp1H2mf5J3Rwuo8xr4BRhJeT9hEgfWN0K/OYpHtF6CpVw9GCE3LN5LDkOPopJjCJWnzA'
    'g4ie3t/OD+rQTuma0+HCCChBEkkAghZXdRnYxvOvmUf6qWZwiuJh8EfLDoVfrZprPPFR0MfjfqWf5lWcXiK0M2sp4mu5Hk655/sAieFagM1tS0'
    '5RXZ1801u9qAmXqThCteerF2CiqLRqdQvjz+wh4wSdDa44BTfqlXx2EYcWccHaQoaJv8KMsWhvHcW66hsNMeQ9Y6iKgq4OqqYIj9rwecd8kR1X'
    'MGywcpyaaxZh9iL+aLVynJqxCs8nFo+UEKmZxEDxeunUyApXqBGDTCfu49zt1RyI83Qyim0QqGJzTkk6xR/yHvCRhpSHanpK/qF0reDMIrV9Tq'
    'aZG76LoHQscyMsUDweLyCT7m8w1xYSTPVl2LOUL1vSoBCp1HB0R9DeLLKyqlsrZ3pbkDlvF31UfYytNSDeUNsuprXA9AhTRn3AeNJgEi4rRVwC'
    'ZwWO1A+UTeuWz8knEf5P8mq9egp4/k8O93ZffP/8kF3k1nCLUJ66WpJJtThBl2moTkyecRw4hmH8TGzfDpEFP2hMRIdTquuNP2KtDSZhSU0e4V'
    'q/jaV4FS0QsA+bzA4GtZOyeVAzhEqGqhOT/yTR04AUbRTfTgp4+OLwcYVFigtO0W7TYEQKIHVIRBJ3V7ZPD/fzaGbS46LOO6wUp60YD86mE3TS'
    '9zwsnm9KietG7vzaxmBdq+vGQh4l1gz8aO5lOKOM4XXD2Ucz4okG7QLnneE1ZrUh3RdxNpi/b4yM6oya52eTEaYRfyfqJfeBklQfn8ac4j9aqK'
    'mGP1Y522wQgJS1BEWX6iQU6Xo4DU8z3In+iCInAphNxICvHc8XUwbovRsUITvnqE/BLTmfRrpGI4UzB5Uxg7uGbHHSj16+vZmRoa3baRCr47GI'
    'iDiL3gZKgh1u5qPhPEAO60E5O4UkY5fMzbnUVEExVKKUinWPX89M7glw2hyQlKPdfp2brsthUzaES8gvP+HolcjpNQT7TTFXESqdMEOg5kFbzd'
    '8uJi2hetJciLJv3KaRSlVRVuNjt1lUqgUpvf0+2V7w7ot0oIFrxCsJRWpnFchlHKpar+/iEBe+qFhP6hEkWbsC19NjyvHRLEr319oyUfc6YFIo'
    'OF+pKq8qwr3iAI2W0xyilWgXJym1mpwNks2QVejmdAQks+Z7Zud0StGyEpNxnLFz6YCbcIK5wdJcLdHoeADnkLhzrjXqx2cvr8ab5Op+ZedONp'
    'HjM6/swkR5Y4q9ndCyBt9Ih7jm/mkv0BikcRUAZNWOHhh5eqqz7loKENTZ7f7GG7zStfPq/5rbdTBIH85Vc9od73sdfF78tw3GbbS5DgBK6vVP'
    'decbqu7GH99U/t//JzAOTR8/lg+Um/lAuRMOlKPPkibJsOaHL9gvPrGl5kNbbo/oKY+MFA1xFMcTnqgebonisdRuxpm4/TpsVSQkyj+RCFCBM8'
    'GfmiKqICqCaXD++xBRVVOO0CsaIAsaypMwvoDxWYzEKoYDap3NBXGMgSLbDnnFSpOygj8tSq9FQGwpoVCaOIyiuhZopZ22go7cS7bSSVv5cckm'
    'um+UMyvlNAOfnv3zMUGwu1GBmnrDJGbhoogMlym6ninqKY0tupYrOjiH60AXdOBQHTVUisR1jeLRkzOa+toXR7GkMSX9D33DZeRDPHxrggsuEX'
    'dix3EbYtP/Wo1dNuVbPYziMQubTGIzs07OU3eFoXtYCM0F4YmYRMypTDGmX+O7r6PhDG+Y40DVW5uEPQDedPiXcl0haJ/jSTHhPSRqqEhwfztq'
    'jp0wt10E5fAmBhTiAkIk+A+WAhMaQc6wHJkRwjEk0Nl610sAsHnWsn9ST/ZRP1PCQimIcuBH+2R4Y//mfZvUEnpsn7uTY5+6o2efggcKYZTyXt'
    '/EhE5k3sO9iEZ7Iy1sk+fs6MqXXynwKS4NKtJev8rdl119ZTNk4qKbZU6her+v+qMhXqHGETSrT1EhhOCBrCK9ODQwHz3ISP13KYiwVo90XJB6'
    'wnnkVrkp9Dbbw9Qj0/kcZZ3cW9wZzdKjXHVzI/yyL/wRbrsj3FIwCJ68TC+xzvPrCz6G0gAoIUeZooW9qGbgTAoA+KZ6bL50eu4/zykGhJn8MU'
    'asemf6FcsvRnECfZ5e3uVVr7H04MkXU63xJEOOX7gUePB7H/suGl0SmBFqI6S8u/C+hRXbTODLXONo7Yk7yUYdFDXeCpCQhY3DIvcLw1kcEYTv'
    'v6p6+WRa6HsvpYdhjAvRRCgV1l1m3a/9rSjl56R2Ps7ahZDCVn3HXqaKGC1B89ThzJC9W6tXVX1SdOVoZyGAXWxhbJGa7dylcAC5Ooquw+UbnX'
    'u4fB1bjpbwV175L0aNW20hqNJ0ueHprmKjUqvufO+M54VTTiDlQUWqCeHjmmKHcBMq83usG6MKc0ow4JF4GHC/kARhMgPzIvbgtVZ49fJCRMsV'
    '18guH7llkR7XN+WDeviEGvQYz3DhpQaKCMoMLuoZJz3HwCcyg4mzGeY/owo7+TQ3Z22TMRkDNdqKk0Fbj8dzFEQa7a3k+U/yfOVWaVFAEJVLO7'
    'mkZVVdJCMWVSmXLK0TtDHpu2yAbvMA96OUSNa3ive/WD0JrsGpyApF1k+QQp30ubzk2bY1l5A2O6rmhwXrdFWd3ypZrCwhmi4glq5YCxNThLcD'
    'CgIbI72CQ4Rzot/ou3CDqVQNEfAOQQ0Akab6IF992O6srVWqXgs6nI5mk6/nfFqC4pwaquUbaDWbG3yez0en8wahUJ/ATC6tbyldSZyVwfsUeY'
    '1cFaXIXakEWxt2toU3qaJnrCmw8jnMtLjyOOpdXnkv0LqeRJjV7rn2VfgyfFeRI7os+6m2tjmz07ngjqvJNcOxxcOsb6YPYsyaTsTFmy4CTB8D'
    'CkJoEXzGgFZM6GuEczvnUNCwueYqqZx4NjGYBNAGVLbTEJ0QD6cTtJsqr4Vo+1z6Q61Cp7j8sWClMDaKlPb+dQALQuSnisB8D2vspWGdkMO9IM'
    'nA3CZHPIyZiZqgVnYUjSrB4FlIh2L1J00N3kO3HGt1btF0aDgu7vcG3XCIaoKDDvKXfbgt3d8fOL2TCaxScfjp5wg6GT8ojTo6zTDuG3BKqyIC'
    '3dRQryO/03rfbGv+XaP4HrlLs/UStzQ4vdddrXrlQz3wuRXWPrujdCts6acIxs2y5YXmytc3t0btteJFspo4qZ1IZeWfLZYV5BtWY+EN5fNqXj'
    'ZG6owlIlmgRJb7zUMike/Th1S21u7Npv9lRMePf4etabJQWrQ+2KePR+dAJWVf9JmwkzClmCvavaiwvIXEuzuChbM8725vbLpm4oJAT6mQSCCj'
    'DxgohAX5KkeXB7qH6QoeDd2Yq/FFTVce+a5fcya0dEXJJOUXlWwpP5asrEYvDGJC4B5RrbMqzcQWnEuJCLgU0INLA3rgddmU2tWzSkzloAqgwX'
    'yIMOBG5z86i9CPmIH1gz/SAoeJBRCiCQmG/IlUYy126YHwFJpi+PwcSZVyOIZk+CXWzfdzSJsZuIPUHvDREqR8I24+BW/vV9bbvV5UIDatZSU8'
    'WwM+RJNQJzzihHybN0wjfNlMOLuSs3hVtgpKOA2efu/O/5VdGfvfzKJ+LD3jL8GTA110r8lmrvnrbDwguo56JyfEPBuHNM5orxcuqe6zy1wBlM'
    'GYQbwqp9fgeg+VeLWD/z7iQWP8iPBGOYl5MHwH9kubhsWHG1YpFP0uRWbTv2viz8ONkW8rkCi06As/2aw8vHGuj87uT0oGZYUBLxWcCIXhT+fg'
    'w9OQOYKciPjTpMmfjy6rNQaHg73gvPPIN6/1+MmhT8bJsBCEmEE+GS4lmmczsWtaH98/arS0goSS/F6Cy9cAdV4kTyC7bcmxO6b1inxU0dnKp+'
    'KWkIUmX2IyMsFqoj+eZ7XZMyOX7sYlehK9lCiBpoKIYWg4EmJHqzmwwxLyZWMSC2SYI3BEkomKWgEOTxU/OAO5vFKaDqQc9g3QBAo+jJ5CgA/G'
    'dy6jy7AtLK/ViOovod/IKTbcyTVwhznFRjTx/7QqjiWM6P/AWo7fRSTPqo9LNscnxT7SwWCxJNpSIqCYVh9EhWouxCd/aOjjPthmmSZ/InaF1m'
    'kfOMeTJqpwP88DKBG4dBnDt3asaJJrJHQD5SUpv1lJ3yWH4cXxX+pBL/F3Fc/DiKwD0+uMlO1dVYJMI8v2jRNMPq9wy74k9EIoVJEQtq7Nfhox'
    'nJnkUOvf21FUHA4/4kX1miTMoQWYxOZXzRhzEu2bnHoiXrqM/PoZB8JybHYgbhUauAp6OIpdpBMdhlN08OCK94BCjoHYrMTsGKvCHBAWef8LPw'
    'cGj6mK7vSsGrKZMQ+IfgzMkDCUkQJJP3MW2QBMpBzyznZ9+sOA4KPfP6dcVf7dlkFfZ1zIciD6jBbUckOSgAWn6JhmF6XjWdJlRULm237kneWk'
    'PO3Rx6+Jcq4p6z6xxFYFvpKX3FwT97NOPn6+ZqoZPm9ZGVYOqmy9ImFLSGV2WDnWF0q+Q2FB7gPieX9UzG7ImapQuOJ8j1VCtr9L+f/YiRhdrV'
    'F2iVymcQ+EdhLUj2lk7KzF6/QiHFb5CKsKzLJGefQMCv3xbJcREUPqQO1xYHNzPM/B8UuGJG7oQYx9Jc8b255HJHGTmvqXbeGfFkg/qxHeBQ1a'
    'n4oQkOgq6pWZzHn/WIgvPsAO3ouG9MbO9zD2BAzQvNRkBPbMc60HylFLm4tuT0UpVnWHb/TafsEvys6Sl5lixRdCbKGTBqigyFfD7BhwpHQ6n4'
    'L94rOv80h4IHS0HPGEi4CGzi29SaEyUSFIagHQ6H0BuBJTBg8yURw6lomQbFg+dhGlJuLIyc4UH6zySHPiI0cynUKkziYg04CpsC26D2HC2hQS'
    '816wclImTXmExaoZWcGtlSLNTNpYqqVVWpqPC6hhSBVC0AScVQ/0F6grcMkAPXKSoPgRXgiHoPGsJSBYkJpQSwBEGUqywaoov5r2AXA5C106M2'
    'SNsZAynpX3vbmSZllrfeiYvEK39KTZHeZsstkLDeuZ5DDEHuMchp3uSTwKTwK4C0NSWhAE4ao3pMkFO4eOks57yRJwpMPC3UOjC3bfy8x9Y6m5'
    't+POewvPfSMz9/6Sc0+631h47v3M3I+Xmnsn7ry/8NyPM3M/WXLuSffHC8/9JDP306Xm3o07P1l47qfp3LutJeeedH+66Nxvz1lKHTHlFIfFWT'
    'UDCMgJY4O30JfUMuJhQWtOYSuBovP300D9BByfBPS4G2UWGmuzj4p1AS2KDXRRugHUOR0CWFEa/BAlAVJRjDAcTmcJTM0eOjdVcynnkQLL4hHW'
    '1lcI5LOSmDTzCTs/a7+4W3I9q2vzMy5Z8Fr95KG3P2XJPmu/ty5ZLnu9u7id1sDhHaJkwnt55vCtMToegaZvnAkC8YLeAatHJoCrEYc4ozxFzq'
    'KnXIUq90AwOiM4JocUNiafKkw3hG2VXezqsOjgHZ3y3qpJMcuDSQXfXguKQ1/gfoJdnAanzELUbVXFNnELYakZXWwl+4ncKMDd5Y1KzpnZEp8y'
    'BlTX3NJxQ3UcDTVD7rJbA28IuyW4cH5fRPeJgH2WMJlB7hrzlCltxK0sp/j9/YkMk5uRnf0Vhz/a3KWrpLftaGdW4wIbqta2Pttx8fGrpqisVX'
    'L9fcJqER8v2WOyPLHHNJg7OLKrgRoXYy4JnjhroQhUfIA6C1I4AGHZbbmmqtuVe+sY2NxtfQPagFwaAPYGICkZbSUzKIqeed12PWQacM2FrE+S'
    '20u2LQSXD2ce5dyPlYui7kVAA2U6AQ6QYTwojxn6giplc7AtY6U7IbAYCxKq/p0K2qV/Xg51gNRBDpCuZEPDKp4grc5JOGVbTYtU2p2deJL0CB'
    'K6EASv4ySySMgl5DVDWzvaNCHvt5PkiQsfugWOndcHccKGwNhR+Kjr9QS1261NLfprXJTkmv3pdcjdYQRLh4uj222bdg/9DkpaZWK9eMMd0/CO'
    '34ERCReNvWq5yiBPmQBequF0p9ka67kaFGZLkYXZOmu5OjBhUIGl5VVcb/HUu2bqP5Z9qx8XWlJ/bY1npJ7681skoEA8bwy9TDOhb63EnnPoJX'
    't5eS2B+a/RaEnswWrF6ZTB5Qf/8Wd1Pv1vr148jzl5BfzJsfxcCvtw0Ur0qqnze75+s5VlZy0pkTT0EYcbtaaYSP2s6UZrjxfV9bgFpcPgUmVj'
    'EMZFcbHuQb53WX6q7FcVJSwqS4+zYpIrwYkYuVyBCLXIAqZrZcdg3tkZLL1Q0bJEHfkXSTJnhZ+xWdyzx8Ar6fyTkfFxiOOTCg736OXBi5d7B4'
    'dPQMULu8anXSelJP11R1jQO8xn3vEN36kH2zx7aXEBss250mhsU78f6+eH+sVhaO7A2WL4Laq3fRvwh/79WD8/1C/0H/u62KvQ0Q+YhwLvozBR'
    'gbxx5fHR4cWlfUozBkluen6XsduC9YhrnR5NLsYvJj8cI6aOa0o7AYRnQLiVRV+XzT/H0UIWnvBgcnh8Hg36FHJfnE+vdGMBEEV3nXsa/FB0yf'
    'SZE8Gj1Xxy90VYuYfC6KDW5Qek/L46xn7QrnVPpoBK9PB69hStCNGzR+Cuc7MPzY3UB3g2vrqihAyygziZk3+qvx8/NOsoGqnQHLjzNczwZ8le'
    '8EcXcLueTUNQZQDCOb4en881lBEcEm4N7jJ0O1YtaWeuTYcUhkagAE9Gtw7BZCtwsIDKVZOBKh8oe0QZoso+0/hUYTROleVLygNXN6iC9CF16P'
    'pgiDjDdXIQXfgxfvTdCuPo/sZgqwPxxH0VvaPsProiMtqhx+9RCBBMIg+Az4WZ+XdV+d73f53Zv5UrsN5OsxPZGnByr+dgW/Z75WL86hqsLTBD'
    'X+POOzraL0eUeMM9pETQu+j6eUhGUl9YZwOKF2aHXSYO9JDg7gY6PfpwOQVsnyZkMB1AWgggzyCgwOW48nFr5ejo4vUd8lP+y+zOm+1TSC5MKW'
    '2kTh0ila7BCvnLygks+Ix5Xrw74NPPwG51ArKj53Z0HqvNCpEOB2tYaf3H//q/uivajZpsY+8r34M8099BybIKyQM0WN8YsrkBahNQuaHNfERv'
    'OTVi2kg/yOgzl6KvOotyT3jPiRu+LW/Yb+Img/0WtCw3dW9FfH3zRv9BWpzkblRVZxKxBZLuccewoXaSwRJo5K4ZoxX7hPN++OL3IW4fH1KuAt'
    '0hHEquSfZYrR63kaGvok/Fh1qNfaYwkqV63ElfkME8ydOVNJ9VokoSy5mDV1RfMtFCaqgDDXEAGYQ+tP3Pm/DzQyc8lZ9Dya/qAFw0HMGlxiA4'
    'hbso5J8Lz34QLyWpcjX2P4j241/aT3iIy9/YQD/L4QdxPqQ/bsLzGx/1/IvxXzQ8nW9MFaOJoyfF8MNW5HJFTl20BN7jUdfqVHgkDVU11L1Jur'
    'nhbm6Sbm64m5tOMgd+Sg8VfMjH4Ot6esz5bmUr13H93RNYTqVD+MJ+DLTRfKG/RehU2kQxcxgEsqH3CJqHrBkxZljJaV/sUKl8sNvyaSSIjlec'
    'PFj51U2b/7rPqxRDlLiFUJBtTrqNMERgnTAERDbfa5l+JmG1b5I9HzGaBqrex7wU+IMhr2tpQlORbl3D2JnYHnyLq3KIkkymMjrVA5ryfq3Qx4'
    '0SnsYzoJSscbmPBeDNUinK4pg8C1XcNmmYuDj3dNWkWf0Y2ww//2bc+GMz/pfYjI3Gb92MftOsbnuf+YIt6vaj36Bhz37CFg1D+GOP/kEwF9uj'
    'jcI9uvT2W+/+sf3+IJHL3NdB0X8YnF+Npl8r8/GLsQa/qzX4Rap7qeoWn4WYzQoJmaSjrSrhxkf4QydpGXgoBT5mVNpGHOTmUOys+ra3jNgs77'
    'BNbiwr4DPMcJDwwYpxN3hJLyTqP/e2iFjefz8eYpYFzuBTJ1OtmQS9h0HQf9Xo37pAMf6xZS2jKMrDf7QGYM4miEjC5+a/kVb08rD2ZqEa9BGM'
    'I3fRviEj7Q3UVnPD7aNbETN7URM8rtJGtLVejP2JHRb9xomQcozUP3FITs+GoCDNfDaYv21CVgX4Vlz0blIU1L9K0YDymIpEG2BaGaiXgEf/VS'
    'gy/kC7Hv7Q9FaV/OBKfnAlI8o8YBBgb1qsdmCEVWwZ8A9Q5PwraB9Q/dDdSmm+uhk6yc2Qvxs6mbsB9g2W4IWlLqXzDxFRv5FSJAv7Id7YUm7Z'
    'kFAm33oeN6k2hqtItlNcFzSakualk09mU4ADWE7CcCOnxAmfevLF40kL8fNFiRipE5lMUevJCZWX0moJGfM0KKZlcuM1lqBnonjOkzQzflAfOy'
    'OsIyTdjlJR+oKji8u3uqTWQIa28Fbag5IeMI/WDmOBnh++2pVhaSUqqIhhQ0A+AcjzNZUwhtsGBm4kax38H2RG/vCw1yIn9NaHnZb79RDwabuP'
    '8NcGvF2/Vxek2rWH/tc+/2r3ey3+1dlv869+b6fV52frG9xeu9Pr8K/1R+z6zK0U/9rtPVrb28Bf+/s9efZot7XX6cizjXUayyPo4R6NZb3f2n'
    'm0IaO693CXf631HrZlLDtu9P3dVpd/7Tzklju7fRnVTm+js8j49vv4Px7LzsPuLv/auNdv86+1h7trMtL+Po350X7v3j6NFMb+aF/W72FvX8a8'
    '13LP9robVLfV3e91aMwb/Yf9zh7+2lvb67T7/Az/Vzg++kd+dR7u8Zgfwv/cr0cy+ofrrtxul3/tbjxq8697O492+Fe/v/eI59uHUo9obzzs77'
    'v21vb7O7uu34eyQo9kheLxvdF7HvE8aZ96z2mnS8djMAADVbVVMwfh5c7TP87BH+fgv/Q50KV1ivR65QysRojRAlGG4JRxtT/AKwseux/H/EOF'
    'Fg/OTxjkeODw2x0CDEQQc3jpSIbgkghuWlZvxBcW8E70i0Rr/KU5KAP3zeY+DNADdJoJpiPAMc2cd5eMGvPzNb1i/iz38Ng+DH3hbRmGfYypEj'
    'n0Ana198zDOHPKlFelcaPxarMiyw2YCQdgZvuP//1/wER59TM4o35Hkb2rlYfAg9oG1n0DHdMA11BNYIu5BjZ8Az3TAJZM61OzK0slWPOuIn/a'
    'xaU/ciujjHRhDdIIzbD2rebGmvKkyz7/mGm1k2n16je32lui1bOCVrUJ1PNor/HXmyKeTsXW+sNDR2dTizbKuWq9l2ScOQlB1e6Gej1WKpgrK5'
    'pRQRAeYQdUoSoKaDJRhRF4lq9D+8XVOktqHedr4d5zlY6TSrnlUo57ONKz46rQo6IwEk3csAVtKKUvjB835owjq7XlmbHWVkn2n8yHiD+Bm0I6'
    'uYJZ+Aibm/FfcwK9bxveG0UAfsurs+OoDj5CEbe97jLP6jr8LYtr9XOV6FOmdbBKWlh/t7gPMu2vow6weibq2V8rx4Y7e8TyWMyh2ZVoxRul3Y'
    'bb3/0rEom4Sjuu0gVurIMVet1shU5cAW9eKL7RzhbvxsU32lx+7V62fC+ZQq/LFdr5CmtJBddDvvx6Un59g8q3ssU3kuK0OO2i8v24PLbe2ygq'
    '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'
    'G2A5mOBj4sZjjD+85fDgz3U80P4f8387oA=='
)


def _dirs():
    try:
        from engine import system as S
        base = Path(S.USER_DIR)
    except Exception:                                          # noqa: BLE001
        base = Path.home() / '.moviescout'
    roms, saves = base / 'roms' / 'nes', base / 'nes_saves'
    for d in (roms, saves):
        try:
            d.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
    return roms, saves


def _err(text, code=400):
    return ({'error': text}, code)


def _is_rom_name(n):
    return str(n).lower().endswith(('.nes', '.zip'))


def _rom_bytes(path):
    """Spiel lesen: .nes direkt oder erste .nes in einer .zip. Prüft die Kennung „NES“ und die Größe."""
    p = Path(path)
    if not p.is_file() or not _is_rom_name(p.name):
        raise ValueError('Das ist keine NES-Datei (.nes oder .zip).')
    if p.stat().st_size > MAX_ROM * 4:
        raise ValueError('Datei zu groß.')
    if p.name.lower().endswith('.zip'):
        with zipfile.ZipFile(p) as z:
            names = [i for i in z.infolist() if i.filename.lower().endswith('.nes') and not i.is_dir()]
            if not names:
                raise ValueError('In dieser .zip liegt keine .nes-Datei.')
            if names[0].file_size > MAX_ROM:
                raise ValueError('Spiel zu groß.')
            data = z.read(names[0])
    else:
        data = p.read_bytes()
    if data[:4] != b'NES\x1a' or len(data) > MAX_ROM:
        raise ValueError('Das ist keine gültige NES-Datei (Kennung fehlt).')
    return data


def _id(path):
    return hashlib.sha1(str(path).encode('utf-8')).hexdigest()[:20]


def register(api):
    global _api
    _api = api
    js = zlib.decompress(base64.b64decode(''.join(_B64))).decode('utf-8')
    page = _PAGE.replace('/*JSNES*/', js)
    roms_dir, saves_dir = _dirs()

    def config(req):
        return {'ok': str(api.get('ok') or 'A'), 'roms': str(roms_dir), 'gamepad': bool(api.get('gamepad'))}

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
            out.append({'name': 'Meine ROMs (hochgeladen)', 'path': str(roms_dir), 'dir': True})
            for r in ML.roots():
                out.append({'name': r['name'], 'path': r['path'], 'dir': True})
            return {'path': '', 'parent': '', 'entries': out}
        try:
            d = ML.listdir(path)
        except Exception as e:                                 # noqa: BLE001
            return _err(str(e))
        ent = [e for e in d['entries'] if e.get('dir') or _is_rom_name(e['name'])]
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
        name = ''.join(c for c in Path(str(req.query.get('name') or 'spiel.nes')).name if c.isalnum() or c in ' ._-()')[:80] or 'spiel.nes'
        if not _is_rom_name(name):
            return _err('Nur .nes oder .zip.')
        data = req.body or b''
        if len(data) > MAX_ROM:
            return _err('Datei zu groß (höchstens 8 MB).')
        if not name.lower().endswith('.zip') and data[:4] != b'NES\x1a':
            return _err('Das ist keine gültige NES-Datei.')
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
        n = len(list(roms_dir.glob('*.nes'))) + len(list(roms_dir.glob('*.zip')))
        z = api.get('zuletzt') or []
        return {'icon': '🎮', 'text': 'NES-Konsole',
                'sub': ('Zuletzt: %s' % Path(z[0]).stem[:40]) if z else ('%d Spiele hochgeladen' % n if n else 'Spiele auswählen und loslegen')}

    api.route('index', lambda req: page)
    for name, fn in (('config', config), ('browse', browse), ('rom', rom), ('upload', upload), ('state', state)):
        api.route(name, fn)
    api.widget('NES-Konsole', widget, ttl=30, icon='🎮')
