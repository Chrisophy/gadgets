# -*- coding: utf-8 -*-
# App-Leiste
# IT('s) Possible
# 2026.11.13
"""MovieScout-Erweiterung: App-Leiste - deine Android-Apps unten in einer Leiste, nach oben ziehen zeigt alle.

Öffnen: Erweiterungsliste -> App-Leiste -> „App-Leiste öffnen“.
Unten steht eine Leiste mit deinen Lieblings-Apps und den zuletzt gestarteten. Links/rechts wischen blättert,
nach oben ziehen (oder Pfeil hoch / „Alle Apps“) zeigt alle installierten Apps. Antippen oder OK startet die App.
Lange drücken (Touch) oder OK gedrückt halten (Fernbedienung) legt eine App in die Leiste oder nimmt sie wieder heraus (★).
Fernbedienung: Pfeile bewegen, OK startet, im Fenster „Alle Apps“ schließt „▼ Schließen“ (oder Zurück) und ein Buchstabe springt zur App.

Läuft nur in der MovieScout-App für Android (dort liegen die Funktionen zum Auflisten und Starten von Apps). Am PC kommt ein Hinweis.
Es wird nichts nach außen gesendet; gemerkt werden nur Lieblinge und zuletzt gestartete Apps auf dem Gerät.
"""
import re

EXT_ID = 'apps'
EXT_NAME = 'App-Leiste'
EXT_DESCRIPTION = '📱 Deine Android-Apps in einer Leiste unten (wischen), nach oben ziehen zeigt alle Apps. Mit Fernbedienung und Touch.'
EXT_LINKS = [('App-Leiste öffnen', 'index')]
EXT_SETTINGS = [
    {'key': 'anzahl', 'label': 'Apps in der Leiste', 'type': 'number', 'default': 8, 'min': 3, 'max': 20,
     'hint': 'Lieblinge (★) stehen immer in der Leiste; der Rest wird mit zuletzt gestarteten Apps aufgefüllt.'},
]

_api = None
_PKG = re.compile(r'^[A-Za-z0-9._]{1,200}$')


def _q(req, key):
    v = (req.query or {}).get(key, '')
    return str(v[0] if isinstance(v, (list, tuple)) and v else v or '').strip()


def _liste(key):
    v = _api.get(key)
    return [p for p in v if isinstance(p, str) and _PKG.match(p)] if isinstance(v, list) else []


def _anzahl():
    try:
        return max(3, min(20, int(_api.get('anzahl') or 8)))
    except (TypeError, ValueError):
        return 8


PAGE = r"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no"><title>App-Leiste</title>
<style>
:root{--bg:#0f141b;--fg:#e8edf3;--mut:#93a1b3;--card:#18202b;--acc:#4da3ff}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{height:100%}
body{margin:0;background:radial-gradient(120% 90% at 50% 0%,#1b2736 0%,var(--bg) 70%);color:var(--fg);font:clamp(14px,2.2vmin,24px)/1.3 system-ui,sans-serif;display:flex;flex-direction:column;overflow:hidden;user-select:none;-webkit-user-select:none}
#top{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:.2em;min-height:0;text-align:center;padding:0 4vw}
#clock{font-size:clamp(48px,16vmin,190px);font-weight:200;letter-spacing:.02em;line-height:1}
#date{color:var(--mut);font-size:1.15em}
#msg{min-height:1.6em;text-align:center;color:var(--mut);padding:0 4vw .5em}
#msg.err{color:#ff9b9b}
#hint{text-align:center;color:var(--mut);font-size:.85em;padding:0 4vw .4em}
#bar{padding:0 0 1.2vmin}
#grip{width:clamp(48px,8vmin,90px);height:5px;border-radius:3px;background:#3a475a;margin:0 auto 1.2vmin}
#dock{display:flex;gap:clamp(8px,2vmin,22px);overflow-x:auto;overflow-y:hidden;padding:1vmin 4vw 1.4vmin;scrollbar-width:none;touch-action:pan-x;justify-content:safe center}
#dock::-webkit-scrollbar,#grid::-webkit-scrollbar{display:none}
.app{flex:0 0 auto;width:clamp(76px,13vmin,150px);text-align:center;cursor:pointer;border-radius:16px;padding:.5em .2em .4em;border:3px solid transparent;position:relative;outline:none}
.app .ic{width:clamp(52px,9.5vmin,104px);height:clamp(52px,9.5vmin,104px);margin:0 auto .35em;border-radius:22%;background:#2a3748 center/cover no-repeat;display:flex;align-items:center;justify-content:center;font-size:1.7em;font-weight:600;color:#cfe0f5}
.app .nm{font-size:.82em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.app.f{border-color:var(--acc);background:#1d2836}
.app .st{position:absolute;right:.4em;top:.2em;color:#ffd24d;font-size:.95em;text-shadow:0 0 4px #000}
.app.all .ic{background:#233246;color:var(--acc);font-size:2em}
#drawer{position:fixed;inset:0;background:#0b0f15;transform:translateY(100%);transition:transform .22s ease;visibility:hidden;display:flex;flex-direction:column;z-index:5}
#drawer.open{transform:none;visibility:visible}
#dh{display:flex;align-items:center;gap:1em;padding:1.4vmin 3vw}
#dh h1{margin:0;font-size:1.2em;font-weight:600}
#close{cursor:pointer;border-radius:14px;padding:.5em 1.1em;background:var(--card);border:3px solid transparent}
#close.f{border-color:var(--acc)}
#dh small{color:var(--mut);margin-left:auto}
#grid{flex:1;overflow-y:auto;display:grid;grid-template-columns:repeat(auto-fill,minmax(clamp(88px,14vmin,150px),1fr));align-content:start;gap:.6vmin;padding:.5vmin 3vw 3vmin;-webkit-overflow-scrolling:touch}
#grid .app{width:auto}
</style></head><body>
<div id="top"><div id="clock"></div><div id="date"></div></div>
<div id="msg"></div>
<div id="hint">Nach oben ziehen oder Pfeil hoch: alle Apps · Lange drücken oder OK halten: ★ in die Leiste</div>
<div id="bar"><div id="grip"></div><div id="dock"></div></div>
<div id="drawer"><div id="dh"><div id="close" tabindex="-1">▼ Schließen</div><h1>Alle Apps</h1><small id="cnt"></small></div><div id="grid"></div></div>
<script>
"use strict";
const $=s=>document.querySelector(s);
let APP=null;try{APP=window.MovieScoutApp||null}catch(e){}
const OK=!!(APP&&typeof APP.listApps==='function');
let apps=[],favs=[],recent=[],maxN=8,zone='dock',curDock=0,curDraw=1,lp=false,lpT=0,msgT=0,sig='';
const icons=new Map(),queue=[];
const dock=$('#dock'),grid=$('#grid'),drawer=$('#drawer'),closeBtn=$('#close');
function el(t,c,x){const e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e}
function say(t,err){const m=$('#msg');m.textContent=t||'';m.className=err?'err':'';clearTimeout(msgT);if(t&&!err)msgT=setTimeout(()=>{m.textContent=''},3500)}
function tile(a){const d=el('div','app');d.dataset.pkg=a.pkg;
  const ic=el('div','ic',(a.label||'?').trim().charAt(0).toUpperCase());d.append(ic,el('div','nm',a.label||a.pkg));
  if(favs.includes(a.pkg))d.append(el('span','st','★'));
  if(icons.has(a.pkg))paint(ic,icons.get(a.pkg));else queue.push(a.pkg);
  return d}
function paint(ic,src){if(src){ic.style.backgroundImage='url("'+src+'")';ic.textContent=''}}
async function pump(){if(pump.on)return;pump.on=true;
  while(queue.length){const p=queue.shift();if(icons.has(p))continue;let s='';try{s=APP.appIcon(p)||''}catch(e){}
    icons.set(p,s);document.querySelectorAll('.app[data-pkg="'+p+'"] .ic').forEach(ic=>paint(ic,s));
    await new Promise(r=>setTimeout(r,4))}
  pump.on=false}
function dockApps(){const by=new Map(apps.map(a=>[a.pkg,a])),out=[];
  for(const p of favs){const a=by.get(p);if(a&&!out.includes(a))out.push(a)}
  for(const p of recent){if(out.length>=maxN)break;const a=by.get(p);if(a&&!out.includes(a))out.push(a)}
  return out}
function renderDock(keepPkg){dock.replaceChildren();
  for(const a of dockApps())dock.append(tile(a));
  const all=el('div','app all');all.append(el('div','ic','▲'),el('div','nm','Alle Apps'));dock.append(all);
  if(keepPkg){const i=[...dock.children].findIndex(x=>x.dataset.pkg===keepPkg);if(i>=0)curDock=i}
  curDock=Math.min(curDock,dock.children.length-1);if(zone==='dock')mark();pump()}
function renderGrid(){grid.replaceChildren();for(const a of apps)grid.append(tile(a));$('#cnt').textContent=apps.length+' Apps';pump()}
function list(){return zone==='dock'?[...dock.children]:[closeBtn,...grid.children]}
function cur(){return zone==='dock'?curDock:curDraw}
function mark(){document.querySelectorAll('.f').forEach(x=>x.classList.remove('f'));const L=list(),i=cur(),e=L[i];if(!e)return;e.classList.add('f');
  try{e.scrollIntoView({block:'nearest',inline:'center'})}catch(x){}}
function go(i){const L=list();i=Math.max(0,Math.min(L.length-1,i));if(zone==='dock')curDock=i;else curDraw=i;mark()}
function cols(){const t=[...grid.children];if(t.length<2)return 1;const y=t[0].offsetTop;let n=0;for(const x of t){if(x.offsetTop!==y)break;n++}return Math.max(1,n)}
function openDrawer(){if(!OK||zone==='drawer')return;if(!grid.children.length)renderGrid();zone='drawer';drawer.classList.add('open');curDraw=Math.min(Math.max(1,curDraw),grid.children.length);mark()}
function closeDrawer(){if(zone!=='drawer')return;zone='dock';drawer.classList.remove('open');mark()}
function launch(pkg){let r;try{r=APP.launchApp(pkg)}catch(e){r=false}
  if(r===false){say('Diese App lässt sich nicht starten (nicht mehr installiert?).',true);return}
  recent=[pkg,...recent.filter(x=>x!==pkg)].slice(0,20);fetch('start?pkg='+encodeURIComponent(pkg)).catch(()=>{});
  if(zone==='drawer')closeDrawer();renderDock(pkg)}
async function fav(pkg){try{const j=await (await fetch('fav?pkg='+encodeURIComponent(pkg))).json();favs=j.favs||[];
    say(favs.includes(pkg)?'★ In der Leiste':'Aus der Leiste genommen');
    document.querySelectorAll('.st').forEach(x=>x.remove());
    document.querySelectorAll('.app[data-pkg]').forEach(d=>{if(favs.includes(d.dataset.pkg))d.append(el('span','st','★'))});
    renderDock(pkg)}catch(e){say('Das ging nicht.',true)}}
function activate(e){if(!e)return;if(e===closeBtn)return closeDrawer();if(e.classList.contains('all'))return openDrawer();if(e.dataset.pkg)launch(e.dataset.pkg)}
function hold(e){if(e&&e.dataset&&e.dataset.pkg){lp=true;fav(e.dataset.pkg)}}
document.addEventListener('keydown',e=>{if(e.ctrlKey||e.altKey||e.metaKey||!OK)return;const k=e.key,L=list(),i=cur();
  if(k==='Enter'||k===' '){e.preventDefault();if(!e.repeat){lp=false;clearTimeout(lpT);const t=L[i];lpT=setTimeout(()=>hold(t),650)}return}
  if(k==='ArrowLeft'){e.preventDefault();go(i-1)}
  else if(k==='ArrowRight'){e.preventDefault();go(i+1)}
  else if(k==='ArrowUp'){e.preventDefault();if(zone==='dock')openDrawer();else if(i>0)go(i<=cols()?0:i-cols())}
  else if(k==='ArrowDown'){e.preventDefault();if(zone==='drawer'){if(i===0)go(1);else{const n=i+cols();if(n<L.length)go(n);else if(L[L.length-1].offsetTop>L[i].offsetTop)go(L.length-1)}}}
  else if((k==='Escape'||k==='Backspace'||k==='GoBack'||k==='BrowserBack')&&zone==='drawer'){e.preventDefault();e.stopPropagation();closeDrawer()}
  else if(zone==='drawer'&&k.length===1&&/\S/.test(k)){const c=k.toLowerCase(),T=[...grid.children];
    for(let s=1;s<=T.length;s++){const j=(Math.max(0,i-1)+s)%T.length;if(((apps[j]||{}).label||'').trim().toLowerCase().startsWith(c)){go(j+1);break}}}
},true);
document.addEventListener('keyup',e=>{if((e.key==='Enter'||e.key===' ')&&OK){e.preventDefault();clearTimeout(lpT);if(!lp)activate(list()[cur()]);lp=false}},true);
/* Touch und Maus: Tippen startet, lange drücken = Liebling */
let pd=null;
function bind(box){
  box.addEventListener('pointerdown',e=>{const t=e.target.closest('.app');if(!t)return;pd={x:e.clientX,y:e.clientY};lp=false;clearTimeout(lpT);lpT=setTimeout(()=>hold(t),650)});
  box.addEventListener('pointermove',e=>{if(pd&&(Math.abs(e.clientX-pd.x)>10||Math.abs(e.clientY-pd.y)>10)){clearTimeout(lpT);pd=null}});
  for(const n of ['pointerup','pointercancel'])box.addEventListener(n,()=>{clearTimeout(lpT);pd=null});
  box.addEventListener('click',e=>{const t=e.target.closest('.app');if(!t)return;if(lp){lp=false;return}
    const L=[...box.children];const j=L.indexOf(t);if(box===dock)curDock=j;else curDraw=j+1;zone=box===dock?'dock':'drawer';mark();activate(t)});
  box.addEventListener('contextmenu',e=>e.preventDefault())}
bind(dock);bind(grid);
closeBtn.addEventListener('click',closeDrawer);
let t0=null;
document.addEventListener('touchstart',e=>{const t=e.touches[0];t0={x:t.clientX,y:t.clientY,top:grid.scrollTop}},{passive:true});
document.addEventListener('touchend',e=>{if(!t0)return;const t=e.changedTouches[0],dx=t.clientX-t0.x,dy=t.clientY-t0.y,s=t0;t0=null;
  if(Math.abs(dy)<60||Math.abs(dy)<Math.abs(dx)*1.5)return;
  if(zone==='dock'&&dy<0)openDrawer();else if(zone==='drawer'&&dy>0&&s.top<=0&&grid.scrollTop<=0)closeDrawer()},{passive:true});
function clock(){const d=new Date();$('#clock').textContent=String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0');
  try{$('#date').textContent=d.toLocaleDateString('de-DE',{weekday:'long',day:'numeric',month:'long'})}catch(e){}}
clock();setInterval(clock,10000);
function read(){let a=[];try{a=JSON.parse(APP.listApps()||'[]')}catch(e){}
  a=a.filter(x=>x&&typeof x.pkg==='string');const s=JSON.stringify(a.map(x=>x.pkg));if(s===sig)return false;sig=s;apps=a;return true}
async function start(){
  if(!OK){$('#hint').hidden=true;$('#dock').hidden=true;$('#grip').hidden=true;say('Die App-Leiste zeigt die Apps deines Geräts und läuft nur in der MovieScout-App für Android.',true);return}
  try{const d=await (await fetch('daten')).json();favs=d.favs||[];recent=d.zuletzt||[];maxN=d.anzahl||8}catch(e){}
  read();if(!apps.length)say('Keine Apps gefunden.',true);
  renderDock();mark();
  window.addEventListener('focus',()=>{if(read()){renderDock();grid.replaceChildren();if(zone==='drawer')renderGrid()}})}
start();
</script></body></html>
"""


def register(api):
    global _api
    _api = api

    def daten(req):
        return {'favs': _liste('favs'), 'zuletzt': _liste('zuletzt'), 'anzahl': _anzahl()}

    def fav(req):
        pkg = _q(req, 'pkg')
        if not _PKG.match(pkg):
            return ({'error': 'Ungültige App'}, 400)
        f = _liste('favs')
        f = [p for p in f if p != pkg] if pkg in f else f + [pkg]
        api.set('favs', f[:60])
        return {'favs': f[:60]}

    def start(req):
        pkg = _q(req, 'pkg')
        if not _PKG.match(pkg):
            return ({'error': 'Ungültige App'}, 400)
        api.set('zuletzt', ([pkg] + [p for p in _liste('zuletzt') if p != pkg])[:20])
        return {'ok': True}

    def widget():
        n = len(_liste('favs'))
        return {'icon': '📱', 'text': 'Apps', 'sub': ('%d Lieblinge in der Leiste' % n) if n else 'Leiste öffnen, Apps starten'}

    api.route('index', lambda req: PAGE)
    api.route('daten', daten)
    api.route('fav', fav)
    api.route('start', start)
    api.widget('App-Leiste', widget, ttl=60, icon='📱')
