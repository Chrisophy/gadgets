# -*- coding: utf-8 -*-
"""Weltraumtunnel: Atari-Arcade mit zerstörbaren Balken und Gegnern."""

EXT_ID = 'weltraumtunnel'
EXT_NAME = 'Weltraumtunnel'
EXT_DESCRIPTION = 'Atari-Weltraumtunnel mit zerstörbaren Hindernissen und Gegnern.'
EXT_LINKS = [('Spiel starten', 'index')]

PAGE = r"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no">
<title>Weltraumtunnel</title>
<style>
:root {
  --bg:#05050a;
  --fg:#e0e0ff;
  --mut:#a0a0c0;
  --card:#121222;
  --acc:#d946ef;
  --danger:#ef4444;
}
* {
  box-sizing:border-box;
  -webkit-user-select:none;
  user-select:none;
  -webkit-touch-callout:none;
}
html,body {
  height:100%;
  margin:0;
  overflow:hidden;
  background:var(--bg);
  color:var(--fg);
  font:clamp(10px,1.5vmin,14px)/1.2 system-ui,sans-serif;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  touch-action:manipulation;
}
#brand {
  font-size:0.9em;
  font-weight:900;
  color:var(--acc);
  letter-spacing:1px;
  margin-bottom:4px;
  text-shadow:0 0 8px var(--acc);
}
#stage-wrap {
  position:relative;
  width:min(99vw, 1100px);
  background:#000;
  border:2px solid #3b3b60;
  border-radius:8px;
  overflow:hidden;
  box-shadow:0 0 20px rgba(217,70,239,.2);
  cursor:crosshair;
}
canvas {
  display:block;
  width:100%;
  height:auto;
  max-height:88vh;
  touch-action:none;
}
#msg {
  position:absolute;
  inset:0;
  display:none;
  place-items:center;
  text-align:center;
  background:rgba(5,5,10,.94);
  padding:12px;
}
#msg.on {display:grid}
#msg h1 {
  color:var(--danger);
  margin:0 0 6px;
  text-shadow:0 0 10px var(--danger);
  font-size:1.4em;
}
#msg p {margin:0 0 8px;color:#fff}
#msg small {
  display:block;
  color:var(--acc);
  margin-top:.3em;
}
</style>
</head>
<body oncontextmenu="return false">

<div id="brand">🚀 WELTRAUM-TUNNEL (ATARI STYLE)</div>

<div id="stage-wrap">
  <canvas id="cv" width="320" height="340"></canvas>
  <div id="msg"></div>
</div>

<script>
"use strict";

const cv=document.getElementById('cv');
const ctx=cv.getContext('2d');
const W=320,H=340;

let score=0;
let energy=100;
let shields=100;
let dTime=100;
let level=1;
let gameState='play';
let paused=false;

const ship={
  x:50,
  y:120,
  w:14,
  h:8,
  speedMultiplier:1
};

const keys={
  left:false,
  right:false,
  up:false,
  down:false
};

let tunnelOffset=0;
let obstacles=[];
let enemies=[];
let lasers=[];
let particles=[];
let spawnTimer=0;
let enemySpawnTimer=0;

// Touch/Maus Verfolgung
let isTouching=false;
let touchTargetX=null;
let touchTargetY=null;
let touchStartTime=0;

function getTunnelBounds(){
  const wave=
    Math.sin(tunnelOffset*.04)*25+
    Math.cos(tunnelOffset*.02)*12;

  return {
    ceiling:25+wave,
    floor:225+wave
  };
}

function resetGame(){
  score=0;
  energy=100;
  shields=100;
  dTime=100;
  level=1;

  ship.x=50;
  ship.y=120;
  ship.speedMultiplier=1;

  tunnelOffset=0;
  obstacles=[];
  enemies=[];
  lasers=[];
  particles=[];

  spawnTimer=0;
  enemySpawnTimer=0;

  keys.left=false;
  keys.right=false;
  keys.up=false;
  keys.down=false;

  isTouching=false;
  touchTargetX=null;
  touchTargetY=null;

  gameState='play';
  paused=false;

  hideMsg();
}

function fireLaser(){
  if(gameState!=='play'||paused||energy<=0)return;

  energy=Math.max(0,energy-2);

  lasers.push({
    x:ship.x+ship.w,
    y:ship.y+ship.h/2-1,
    vx:7,
    w:8,
    h:2
  });
}

function addExplosion(x,y,count,color){
  for(let i=0;i<count;i++){
    particles.push({
      x:x,
      y:y,
      vx:(Math.random()-.5)*4,
      vy:(Math.random()-.5)*4,
      life:12+Math.random()*10,
      color:color,
      size:1+Math.random()*2
    });
  }
}

function rectHit(a,b){
  return (
    a.x<b.x+b.w &&
    a.x+a.w>b.x &&
    a.y<b.y+b.h &&
    a.y+a.h>b.y
  );
}

function gameOver(){
  if(gameState!=='play')return;

  gameState='over';
  paused=false;

  showMsg(
    'GAME OVER',
    `Dein Schiff wurde zerstört!<br>
     Punkte: ${Math.floor(score)}
     <small>OK / TIPPEN = NOCHMAL SPIELEN</small>`
  );
}

function update(){
  if(gameState!=='play'||paused)return;

  // Touch / Maus Steuerung anwenden
  if(isTouching && touchTargetY!==null && touchTargetX!==null){
    const targetShipY = touchTargetY - ship.h/2;
    const targetShipX = Math.max(30, Math.min(160, touchTargetX - ship.w/2));
    
    ship.y += (targetShipY - ship.y) * 0.25;
    ship.x += (targetShipX - ship.x) * 0.25;
  } else {
    // Tastatur / Fernbedienung Bewegung
    if(keys.left){
      ship.speedMultiplier=Math.max(.4,ship.speedMultiplier-.03);
    }
    if(keys.right){
      ship.speedMultiplier=Math.min(2.2,ship.speedMultiplier+.03);
    }
    if(keys.up)ship.y-=3.5;
    if(keys.down)ship.y+=3.5;

    if(keys.left&&!keys.right){
      ship.x=Math.max(30,ship.x-2);
    }
    if(keys.right&&!keys.left){
      ship.x=Math.min(160,ship.x+2);
    }
  }

  const tunnelSpeed=
    (1.5+level*.2)*ship.speedMultiplier;

  tunnelOffset+=tunnelSpeed;

  const bounds=getTunnelBounds();
  const ceilingY=bounds.ceiling;
  const floorY=bounds.floor;

  // Tunnelbegrenzung
  if(ship.y<ceilingY){
    ship.y=ceilingY;
    shields=Math.max(0,shields-.4);
  }

  if(ship.y+ship.h>floorY){
    ship.y=floorY-ship.h;
    shields=Math.max(0,shields-.4);
  }

  dTime-=.03*ship.speedMultiplier;
  energy=Math.min(100,energy+.05);

  if(shields<=0||dTime<=0||energy<=0){
    gameOver();
    return;
  }

  // Hindernisse erzeugen
  spawnTimer++;

  if(spawnTimer>Math.max(35,80-level*4)){
    spawnTimer=0;

    const oHeight=60+Math.random()*30;
    const side=Math.random()<.5?'top':'bottom';

    obstacles.push({
      x:W,
      y:side==='top'?ceilingY:floorY-oHeight,
      w:12,
      h:oHeight,
      side:side,
      vx:tunnelSpeed
    });
  }

  // Gegner erzeugen
  enemySpawnTimer++;

  if(enemySpawnTimer>Math.max(50,120-level*5)){
    enemySpawnTimer=0;

    enemies.push({
      x:W+20,
      y:ceilingY+15+
         Math.random()*(floorY-ceilingY-35),
      w:14,
      h:8,
      vx:2.2+Math.random(),
      alive:true
    });
  }

  // Laser bewegen
  for(let i=lasers.length-1;i>=0;i--){
    const l=lasers[i];
    l.x+=l.vx;

    if(l.x>W){
      lasers.splice(i,1);
    }
  }

  // --------------------------------------------------
  // BALKEN: Treffer, Schrumpfen und Zerstörung
  // --------------------------------------------------

  for(let i=obstacles.length-1;i>=0;i--){
    const o=obstacles[i];

    o.x-=o.vx;

    if(o.side==='top'){
      o.y=ceilingY;
    }else{
      o.y=floorY-o.h;
    }

    // Laser prüfen
    for(let li=lasers.length-1;li>=0;li--){
      const l=lasers[li];

      if(!rectHit(l,o))continue;

      lasers.splice(li,1);
      score+=50;

      addExplosion(l.x, l.y, 3, '#c084fc');

      o.h*=.75;

      if(o.side==='bottom'){
        o.y=floorY-o.h;
      }else{
        o.y=ceilingY;
      }

      if(o.h<12){
        addExplosion(o.x+o.w/2, o.y+o.h/2, 10, '#c084fc');
        obstacles.splice(i,1);
        score+=100;
        break;
      }
    }

    if(i>=obstacles.length||obstacles[i]!==o){
      continue;
    }

    if(rectHit(ship,o)){
      obstacles.splice(i,1);

      shields=Math.max(0,shields-25);
      score=Math.max(0,score-50);

      addExplosion(ship.x+ship.w/2, ship.y+ship.h/2, 8, '#ef4444');

      if(shields<=0){
        gameOver();
        return;
      }

      continue;
    }

    if(o.x+o.w<0){
      obstacles.splice(i,1);
      score+=20*ship.speedMultiplier;

      if(score>level*1000){
        level++;
      }
    }
  }

  // --------------------------------------------------
  // GEGNER: Bewegung und Zerstörung
  // --------------------------------------------------

  for(let i=enemies.length-1;i>=0;i--){
    const e=enemies[i];
    e.x-=e.vx;

    let destroyed=false;

    for(let li=lasers.length-1;li>=0;li--){
      const l=lasers[li];

      if(!rectHit(l,e))continue;

      lasers.splice(li,1);
      enemies.splice(i,1);
      score+=250;

      addExplosion(e.x+e.w/2, e.y+e.h/2, 14, '#ef4444');
      destroyed=true;
      break;
    }

    if(destroyed)continue;

    if(rectHit(ship,e)){
      enemies.splice(i,1);
      shields=Math.max(0,shields-30);

      addExplosion(e.x+e.w/2, e.y+e.h/2, 12, '#ef4444');

      if(shields<=0){
        gameOver();
        return;
      }

      continue;
    }

    if(e.x+e.w<0){
      enemies.splice(i,1);
    }
  }

  // Partikel
  for(let i=particles.length-1;i>=0;i--){
    const p=particles[i];
    p.x+=p.vx;
    p.y+=p.vy;
    p.life--;

    if(p.life<=0){
      particles.splice(i,1);
    }
  }
}

function showMsg(title,html){
  const m=document.getElementById('msg');
  m.innerHTML=`
    <div>
      <h1>${title}</h1>
      <p>${html}</p>
    </div>
  `;
  m.classList.add('on');
}

function hideMsg(){
  document.getElementById('msg').classList.remove('on');
}

function draw(){
  ctx.fillStyle='#05050a';
  ctx.fillRect(0,0,W,H);

  const bounds=getTunnelBounds();
  const ceilingY=bounds.ceiling;
  const floorY=bounds.floor;

  // Hintergrundsterne
  ctx.fillStyle='rgba(255,255,255,.35)';

  for(let i=0;i<40;i++){
    const x=(i*137-tunnelOffset*1.5)%W;
    const y=(i*71)%240;

    ctx.fillRect(
      x<0?x+W:x,
      y+15,
      1.5,
      1.5
    );
  }

  // Decke
  ctx.fillStyle='#b45309';
  ctx.fillRect(0,0,W,ceilingY);
  ctx.fillStyle='#d97706';
  ctx.fillRect(0,ceilingY-4,W,4);

  // Boden
  ctx.fillStyle='#b45309';
  ctx.fillRect(0,floorY,W,H-65-floorY);
  ctx.fillStyle='#d97706';
  ctx.fillRect(0,floorY,W,4);

  // Hindernisse
  for(const o of obstacles){
    ctx.fillStyle='#9333ea';
    ctx.fillRect(o.x,o.y,o.w,o.h);

    ctx.fillStyle='#c084fc';
    ctx.fillRect(
      o.x+2,
      o.y+2,
      Math.max(0,o.w-4),
      Math.max(0,o.h-4)
    );

    ctx.fillStyle='#e9d5ff';
    ctx.fillRect(o.x+4,o.y+4,2,Math.max(0,o.h-8));
  }

  // Gegner
  for(const e of enemies){
    ctx.fillStyle='#ef4444';
    ctx.beginPath();
    ctx.moveTo(e.x,e.y+e.h/2);
    ctx.lineTo(e.x+e.w,e.y);
    ctx.lineTo(e.x+e.w,e.y+e.h);
    ctx.closePath();
    ctx.fill();

    ctx.fillStyle='#fecaca';
    ctx.fillRect(e.x+7,e.y+3,4,2);

    ctx.fillStyle='#f97316';
    ctx.fillRect(e.x+e.w,e.y+3,3,2);
  }

  // Laser
  ctx.fillStyle='#38bdf8';
  for(const l of lasers){
    ctx.shadowColor='#38bdf8';
    ctx.shadowBlur=8;
    ctx.fillRect(l.x,l.y,l.w,l.h);
  }
  ctx.shadowBlur=0;

  // Explosionen
  for(const p of particles){
    ctx.globalAlpha=Math.max(0,p.life/20);
    ctx.fillStyle=p.color;
    ctx.fillRect(p.x,p.y,p.size,p.size);
  }
  ctx.globalAlpha=1;

  // Spieler-Raumschiff
  ctx.fillStyle='#f472b6';
  ctx.beginPath();
  ctx.moveTo(ship.x+ship.w,ship.y+ship.h/2);
  ctx.lineTo(ship.x,ship.y);
  ctx.lineTo(ship.x,ship.y+ship.h);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle='#ffffff';
  ctx.fillRect(ship.x+6,ship.y+3,4,2);

  ctx.fillStyle='#38bdf8';
  ctx.fillRect(ship.x-3,ship.y+3,3,2);

  // HUD unten
  const hudY = 275;
  ctx.fillStyle='#1e1b4b';
  ctx.fillRect(0, hudY, W, 65);

  ctx.strokeStyle='#4338ca';
  ctx.lineWidth=2;
  ctx.strokeRect(0, hudY, W, 65);

  ctx.fillStyle='#ffffff';
  ctx.font='bold 9px sans-serif';
  ctx.fillText('LEVEL '+level, 10, hudY + 14);

  ctx.fillStyle='#e2e8f0';
  ctx.fillText('Score:', 130, hudY + 14);
  ctx.fillStyle='#d946ef';
  ctx.fillRect(165, hudY + 4, 140, 14);
  ctx.fillStyle='#000000';
  ctx.fillText(Math.floor(score), 170, hudY + 14);

  function drawMiniBar(label, val, x, y, color){
    val=Math.max(0,Math.min(100,val));
    ctx.fillStyle='#e2e8f0';
    ctx.font='bold 8px sans-serif';
    ctx.fillText(label, x, y + 8);

    ctx.fillStyle='#0f172a';
    ctx.fillRect(x + 42, y, 55, 9);
    ctx.strokeStyle='#64748b';
    ctx.strokeRect(x + 42, y, 55, 9);

    ctx.fillStyle=color;
    ctx.fillRect(x + 43, y + 1, Math.max(0, (val/100)*53), 7);
  }

  drawMiniBar('Energy', energy, 10, hudY + 28, '#8b5cf6');
  drawMiniBar('Shields', shields, 112, hudY + 28, shields>30?'#10b981':'#ef4444');
  drawMiniBar('D-TIME', dTime, 215, hudY + 28, '#06b6d4');
}

function loop(){
  update();
  draw();
  requestAnimationFrame(loop);
}

// Touch & Maus Event-Listener direkt auf dem Canvas
function getCanvasPos(e) {
  const rect = cv.getBoundingClientRect();
  const scaleX = W / rect.width;
  const scaleY = H / rect.height;
  return {
    x: (e.clientX - rect.left) * scaleX,
    y: (e.clientY - rect.top) * scaleY
  };
}

cv.addEventListener('pointerdown', e => {
  e.preventDefault();
  
  if(gameState==='over'){
    resetGame();
    return;
  }
  if(paused){
    paused=false;
    hideMsg();
    return;
  }

  isTouching = true;
  touchStartTime = Date.now();
  const pos = getCanvasPos(e);
  touchTargetX = pos.x;
  touchTargetY = pos.y;
});

cv.addEventListener('pointermove', e => {
  if(!isTouching) return;
  e.preventDefault();
  const pos = getCanvasPos(e);
  touchTargetX = pos.x;
  touchTargetY = pos.y;
});

const endPointer = e => {
  if(!isTouching) return;
  e.preventDefault();
  
  // Wenn es nur ein kurzer Tipp war (< 200ms), schieße Laser!
  if(Date.now() - touchStartTime < 200) {
    fireLaser();
  }
  
  isTouching = false;
  touchTargetX = null;
  touchTargetY = null;
};

cv.addEventListener('pointerup', endPointer);
cv.addEventListener('pointercancel', endPointer);

// Fernbedienung / Tastatur Steuerung
const KEYS={
  ArrowLeft:'left',
  ArrowRight:'right',
  ArrowUp:'up',
  ArrowDown:'down',
  Enter:'fire',
  ' ':'fire',
  Select:'fire',
  Escape:'pause',
  Backspace:'pause',
  GoBack:'pause',
  BrowserBack:'pause',
  p:'pause'
};

function act(k,isDown){
  if(k==='pause'&&isDown){
    if(gameState==='over'){
      resetGame();
      return;
    }
    if(gameState==='play'){
      paused=!paused;
      if(paused){
        showMsg('PAUSE', 'Spiel pausiert<small>Zurück oder OK = Weiter</small>');
      }else{
        hideMsg();
      }
    }
    return;
  }

  if(gameState==='over'){
    if(isDown&&(k==='fire'||k==='up'||k==='down'||k==='left'||k==='right')){
      resetGame();
    }
    return;
  }

  if(paused){
    if(isDown&&k==='fire'){
      paused=false;
      hideMsg();
    }
    return;
  }

  if(k==='left')keys.left=isDown;
  if(k==='right')keys.right=isDown;
  if(k==='up')keys.up=isDown;
  if(k==='down')keys.down=isDown;

  if(isDown&&k==='fire'){
    fireLaser();
  }
}

document.addEventListener('keydown',e=>{
  const a=KEYS[e.key]||(e.keyCode===4?'pause':null);
  if(a){
    e.preventDefault();
    act(a,true);
  }
});

document.addEventListener('keyup',e=>{
  const a=KEYS[e.key];
  if(a&&['left','right','up','down'].includes(a)){
    e.preventDefault();
    act(a,false);
  }
});

window.addEventListener('blur',()=>{
  keys.left=false;
  keys.right=false;
  keys.up=false;
  keys.down=false;
  isTouching=false;
});

resetGame();
loop();
</script>
</body>
</html>"""

def widget(req):
    return {
        'title': 'Weltraumtunnel',
        'content': 'Weltraumtunnel: Atari-Arcade mit zerstörbaren Balken und Gegnern.'
    }

def register(api):
    api.widget('Weltraumtunnel', widget, ttl=3600, icon='🚀')
    api.route('index', lambda req: PAGE)
    