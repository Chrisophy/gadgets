Python

# -*- coding: utf-8 -*-
"""Pacman Arcade: 10 Level, blinkende Power-Taler und Querformat-Steuerung."""

EXT_ID = 'pacman_arcade'
EXT_NAME = 'Pacman'
EXT_DESCRIPTION = 'Pacman mit 10 Leveln, Power-Talern und Arcade-Steuerung.'
EXT_LINKS = [('Spiel starten', 'index')]
EXT_SETTINGS = []

_api = None

def register(api):
    global _api
    _api = api

    def seite(req):
        return r'''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>MovieScout - Pacman</title>
<style>
:root {
  --bg:#10131a;
  --panel:#1a1f2c;
  --panel2:#222a3b;
  --border:#30394e;
  --text:#f1f3f8;
  --muted:#9da6b7;
  --accent:#3b82f6;
}
* {
  box-sizing:border-box;
  user-select:none;
  -webkit-user-select:none;
  -webkit-touch-callout:none;
}
html,body {
  width:100%;
  height:100%;
  margin:0;
  overflow:hidden;
  background:var(--bg);
  color:var(--text);
  font-family:system-ui,sans-serif;
  touch-action:manipulation;
}
#game-layout {
  width:100%;
  height:100dvh;
  display:flex;
  align-items:stretch;
}
#play-area {
  width:70%;
  height:100%;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  padding:5px;
  min-width:0;
  min-height:0;
}
#brand {
  font-size:clamp(12px,2.2vh,21px);
  font-weight:900;
  letter-spacing:1.5px;
  margin-bottom:4px;
}
#ui {
  width:min(100%,600px);
  display:flex;
  justify-content:space-around;
  flex-wrap:wrap;
  gap:4px;
  padding:5px;
  background:var(--panel);
  border:1px solid var(--border);
  border-radius:9px 9px 0 0;
  font-size:clamp(10px,1.6vh,15px);
  font-weight:bold;
}
#ui b {color:#60a5fa;}
#stage {
  position:relative;
  width:min(100%,calc(100dvh - 65px));
  max-height:calc(100dvh - 65px);
  aspect-ratio:1/1;
  background:#000;
  border:1px solid var(--border);
  border-radius:0 0 10px 10px;
  overflow:hidden;
}
canvas {
  display:block;
  width:100%;
  height:100%;
}
#msg {
  position:absolute;
  inset:0;
  display:none;
  place-items:center;
  text-align:center;
  background:rgba(10,14,24,.94);
  padding:12px;
  z-index:5;
}
#msg.on {display:grid;}
#msg h1 {
  font-size:clamp(17px,4vw,30px);
  margin:0 0 8px;
  color:#facc15;
}
#msg p {
  font-size:clamp(11px,2vw,17px);
  color:var(--text);
  margin:0 0 14px;
}
.btn {
  font:inherit;
  font-weight:bold;
  color:white;
  background:var(--accent);
  border:1px solid var(--border);
  border-radius:10px;
  padding:9px 18px;
}
#side-panel {
  width:30%;
  height:100%;
  min-width:0;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  gap:clamp(8px,2vh,20px);
  padding:8px;
  background:var(--panel);
  border-left:1px solid var(--border);
}
#side-title {
  font-size:clamp(11px,2vw,19px);
  font-weight:900;
  text-align:center;
}
#power-info {
  text-align:center;
  font-size:clamp(9px,1.5vw,13px);
  color:#facc15;
  line-height:1.5;
}
#pad {
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  grid-template-rows:repeat(3,minmax(0,1fr));
  width:min(100%,190px);
  aspect-ratio:1/1;
  gap:5px;
}
#pad button {
  font-size:clamp(17px,4vw,29px);
  font-weight:bold;
  background:#283349;
  color:white;
  border:1px solid #465575;
  border-radius:12px;
  touch-action:none;
  padding:0;
}
#pad button:active {
  background:var(--accent);
  transform:scale(.95);
}
#btn-up {grid-column:2;grid-row:1;}
#btn-left {grid-column:1;grid-row:2;}
#btn-down {grid-column:2;grid-row:2;}
#btn-right {grid-column:3;grid-row:2;}
#legend {
  text-align:center;
  color:var(--muted);
  font-size:clamp(9px,1.4vw,12px);
  line-height:1.6;
}
#legend strong {color:#facc15;}

@media (orientation:portrait) {
  #game-layout {
    flex-direction:column;
  }
  #play-area {
    width:100%;
    height:72%;
    flex:1;
  }
  #stage {
    width:min(96vw,calc(72dvh - 45px));
    max-height:calc(72dvh - 45px);
  }
  #side-panel {
    width:100%;
    height:auto;
    min-height:0;
    flex:0 0 auto;
    flex-direction:row;
    justify-content:space-around;
    border-left:0;
    border-top:1px solid var(--border);
    padding:5px 10px;
    gap:8px;
  }
  #side-title {display:none;}
  #pad {
    width:min(38vw,135px);
    flex-shrink:0;
  }
  #power-info {max-width:100px;}
  #legend {display:none;}
}
</style>
</head>
<body oncontextmenu="return false">

<div id="game-layout">

  <section id="play-area">
    <div id="brand">🟡 PAC-MAN ARCADE</div>

    <div id="ui">
      <span>Score: <b id="score">0</b></span>
      <span>❤️ <b id="lives">3</b></span>
      <span>Level: <b id="level">1</b></span>
      <span>👻 <b id="ghost-count">4</b></span>
    </div>

    <div id="stage">
      <canvas id="cv" width="400" height="400"></canvas>
      <div id="msg"></div>
    </div>
  </section>

  <aside id="side-panel">
    <div id="side-title">🎮 STEUERUNG</div>

    <div id="power-info">
      🪙 Vier Power-Taler<br>
      <strong>5 Sekunden Geisterjagd!</strong>
    </div>

    <div id="pad">
      <button id="btn-up">▲</button>
      <button id="btn-left">◀</button>
      <button id="btn-down">▼</button>
      <button id="btn-right">▶</button>
    </div>

    <div id="legend">
      🟡 Pac-Man<br>
      🔵 Geister fressbar<br>
      <strong>🪙 Power-Taler</strong><br>
      Pfeiltasten / Steuerkreuz
    </div>
  </aside>

</div>

<script>
"use strict";

const cv = document.getElementById('cv');
const ctx = cv.getContext('2d');

const S = 20;
const SIZE = 20;

const mapGrid = [
  [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
  [1,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,1],
  [1,0,1,1,0,1,1,1,0,1,1,0,1,1,1,0,1,1,0,1],
  [1,0,1,1,0,1,1,1,0,1,1,0,1,1,1,0,1,1,0,1],
  [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
  [1,0,1,1,0,1,0,1,1,1,1,1,1,0,1,0,1,1,0,1],
  [1,0,0,0,0,1,0,0,0,1,1,0,0,0,1,0,0,0,0,1],
  [1,1,1,1,0,1,1,1,2,1,1,2,1,1,1,0,1,1,1,1],
  [2,2,2,1,0,1,2,2,2,2,2,2,2,2,1,0,1,2,2,2],
  [1,1,1,1,0,1,2,1,1,2,2,1,1,2,1,0,1,1,1,1],
  [2,2,2,2,0,2,2,1,2,2,2,2,1,2,2,0,2,2,2,2],
  [1,1,1,1,0,1,2,1,1,1,1,1,1,2,1,0,1,1,1,1],
  [2,2,2,1,0,1,2,2,2,2,2,2,2,2,1,0,1,2,2,2],
  [1,1,1,1,0,1,2,1,1,1,1,1,1,2,1,0,1,1,1,1],
  [1,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,1],
  [1,0,1,1,0,1,1,1,0,1,1,0,1,1,1,0,1,1,0,1],
  [1,0,0,1,0,0,0,0,0,2,2,0,0,0,0,0,1,0,0,1],
  [1,1,0,1,0,1,0,1,1,1,1,1,1,0,1,0,1,0,1,1],
  [1,0,0,0,0,1,0,0,0,1,1,0,0,0,1,0,0,0,0,1],
  [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
];

const coinPositions = [
  {x:1,y:1},
  {x:18,y:1},
  {x:1,y:18},
  {x:18,y:18}
];

const directions = [
  {x:0,y:-1},
  {x:0,y:1},
  {x:-1,y:0},
  {x:1,y:0}
];

let map = [];
let coins = [];
let score = 0;
let lives = 3;
let level = 1;
let gameState = 'play';
let powerUntil = 0;
let levelTransition = false;

let pacman = {
  x:9*S,
  y:16*S,
  dir:{x:0,y:0},
  nextDir:{x:0,y:0},
  speed:2
};

let ghosts = [];

const ghostColors = [
  '#ef4444',
  '#ec4899',
  '#06b6d4',
  '#f97316'
];

function rotateGrid(source, turns, mirror) {
  let result = source.map(row => row.slice());

  if (mirror) {
    result = result.map(row => row.slice().reverse());
  }

  for (let t=0; t<turns; t++) {
    const rotated = Array.from({length:SIZE}, () => Array(SIZE).fill(1));

    for (let y=0; y<SIZE; y++) {
      for (let x=0; x<SIZE; x++) {
        rotated[x][SIZE-1-y] = result[y][x];
      }
    }

    result = rotated;
  }

  return result;
}

function createLevel() {
  const variant = (level-1)%8;
  map = rotateGrid(mapGrid, variant%4, variant>=4);

  // Startposition und Geisterhaus sicher begehbar halten.
  const safeCells = [
    [9,16],[10,16],
    [9,8],[10,8],
    [9,9],[10,9],
    [9,10],[10,10]
  ];

  for (const [x,y] of safeCells) {
    map[y][x] = 2;
  }

  // Vier Power-Taler in den Ecken.
  coins = coinPositions.map(p => ({
    x:p.x,
    y:p.y,
    active:true
  }));

  for (const c of coins) {
    map[c.y][c.x] = 2;
  }

  const ghostSpeed = [2,2,2,2,4,4,4,4,5,5][Math.min(level-1,9)];

  ghosts = [
    {x:9*S,y:8*S,color:ghostColors[0],dir:{x:0,y:1},speed:ghostSpeed,dead:false},
    {x:10*S,y:8*S,color:ghostColors[1],dir:{x:0,y:1},speed:ghostSpeed,dead:false},
    {x:9*S,y:10*S,color:ghostColors[2],dir:{x:0,y:-1},speed:ghostSpeed,dead:false},
    {x:10*S,y:10*S,color:ghostColors[3],dir:{x:0,y:-1},speed:ghostSpeed,dead:false}
  ];

  resetPositions();
  powerUntil = 0;
  levelTransition = false;
  gameState = 'play';
  updateHUD();
}

function resetPositions() {
  pacman.x = 9*S;
  pacman.y = 16*S;
  pacman.dir = {x:0,y:0};
  pacman.nextDir = {x:0,y:0};

  const positions = [
    [9,8],[10,8],[9,10],[10,10]
  ];

  ghosts.forEach((g,i) => {
    g.x = positions[i][0]*S;
    g.y = positions[i][1]*S;
    g.dir = {x:0,y:1};
    g.dead = false;
  });
}

function updateHUD() {
  document.getElementById('score').textContent = score;
  document.getElementById('lives').textContent = lives;
  document.getElementById('level').textContent = level;

  document.getElementById('ghost-count').textContent =
    ghosts.filter(g => !g.dead).length;
}

function isAligned(entity) {
  return entity.x%S === 0 && entity.y%S === 0;
}

function canMove(x,y,dir) {
  if (!dir.x && !dir.y) return false;

  if (x%S === 0 && y%S === 0) {
    const tx = x/S + dir.x;
    const ty = y/S + dir.y;

    if (tx<0 || tx>=SIZE || ty<0 || ty>=SIZE) {
      return false;
    }

    return map[ty][tx] !== 1;
  }

  return true;
}

function checkLevelComplete() {
  for (let y=0;y<SIZE;y++) {
    for (let x=0;x<SIZE;x++) {
      if (map[y][x]===0) return false;
    }
  }

  return coins.every(c => !c.active);
}

function nextLevel() {
  if (gameState !== 'levelup') return;

  level++;

  if (level > 10) {
    gameState = 'finished';
    showMsg(
      '🏆 MEISTER!',
      'Du hast alle 10 Level geschafft!<br>Punkte: '+score
    );
    return;
  }

  createLevel();
}

function completeLevel() {
  if (gameState !== 'play') return;

  gameState = 'levelup';

  showMsg(
    '🏆 LEVEL '+level+' GESCHAFFT!',
    'Alle Pellets und Power-Taler eingesammelt!<br>Weiter geht es mit Level '+(level+1)
  );

  setTimeout(() => {
    nextLevel();
  },1500);
}

function collectItems() {
  const gx = Math.floor((pacman.x+S/2)/S);
  const gy = Math.floor((pacman.y+S/2)/S);

  if (gx<0 || gx>=SIZE || gy<0 || gy>=SIZE) return;

  if (map[gy][gx]===0) {
    map[gy][gx]=2;
    score+=10;
    updateHUD();
  }

  for (const c of coins) {
    if (c.active && gx===c.x && gy===c.y) {
      c.active=false;
      score+=50;

      // Jeder Taler aktiviert den Power-Modus für fünf Sekunden.
      powerUntil=Date.now()+5000;

      updateHUD();
    }
  }

  if (checkLevelComplete()) {
    completeLevel();
  }
}

function updatePacman() {
  if (isAligned(pacman)) {
    if (pacman.nextDir.x || pacman.nextDir.y) {
      if (canMove(pacman.x,pacman.y,pacman.nextDir)) {
        pacman.dir={...pacman.nextDir};
      }
    }
  }

  if (canMove(pacman.x,pacman.y,pacman.dir)) {
    pacman.x+=pacman.dir.x*pacman.speed;
    pacman.y+=pacman.dir.y*pacman.speed;
  }

  collectItems();
}

function updateGhost(g) {
  if (g.dead) return;

  if (isAligned(g)) {
    let validDirs = directions.filter(d => {
      const tx=g.x/S+d.x;
      const ty=g.y/S+d.y;

      return tx>=0 && tx<SIZE &&
             ty>=0 && ty<SIZE &&
             map[ty][tx]!==1 &&
             !(d.x===-g.dir.x && d.y===-g.dir.y);
    });

    if (validDirs.length===0) {
      validDirs=directions.filter(d => {
        const tx=g.x/S+d.x;
        const ty=g.y/S+d.y;

        return tx>=0 && tx<SIZE &&
               ty>=0 && ty<SIZE &&
               map[ty][tx]!==1;
      });
    }

    if (validDirs.length>0) {
      const px=pacman.x;
      const py=pacman.y;

      // Im Power-Modus fliehen die Geister.
      validDirs.sort((a,b) => {
        const da=Math.hypot(g.x+a.x*S-px,g.y+a.y*S-py);
        const db=Math.hypot(g.x+b.x*S-px,g.y+b.y*S-py);

        return Date.now()<powerUntil ? db-da : da-db;
      });

      // Etwas Zufall sorgt für abwechslungsreiche Bewegung.
      if (Math.random()<0.35) {
        g.dir=validDirs[Math.floor(Math.random()*validDirs.length)];
      } else {
        g.dir=validDirs[0];
      }
    }
  }

  if (canMove(g.x,g.y,g.dir)) {
    g.x+=g.dir.x*g.speed;
    g.y+=g.dir.y*g.speed;
  }
}

function checkCollisions() {
  const frightened=Date.now()<powerUntil;

  for (const g of ghosts) {
    if (g.dead) continue;

    const distance=Math.hypot(
      pacman.x-g.x,
      pacman.y-g.y
    );

    if (distance<S*0.7) {
      if (frightened) {
        // Geist bleibt für den Rest des Levels verschwunden.
        g.dead=true;
        score+=200;
        updateHUD();
      } else {
        lives--;
        updateHUD();

        if (lives<=0) {
          gameState='over';

          showMsg(
            '💀 GAME OVER',
            'Pac-Man wurde gefangen!<br>Punkte: '+score
          );
          return;
        }

        powerUntil=0;
        resetPositions();
        return;
      }
    }
  }
}

function update() {
  if (gameState!=='play') return;

  updatePacman();

  if (gameState!=='play') return;

  for (const g of ghosts) {
    updateGhost(g);
  }

  checkCollisions();
  updateHUD();
}

function drawMaze() {
  ctx.fillStyle='#000';
  ctx.fillRect(0,0,400,400);

  for (let y=0;y<SIZE;y++) {
    for (let x=0;x<SIZE;x++) {
      if (map[y][x]===1) {
        ctx.fillStyle='#222a3b';
        ctx.fillRect(x*S,y*S,S,S);

        ctx.strokeStyle='#3b82f6';
        ctx.lineWidth=1;
        ctx.strokeRect(x*S,y*S,S,S);
      } else if (map[y][x]===0) {
        ctx.fillStyle='#f1f3f8';
        ctx.beginPath();
        ctx.arc(x*S+S/2,y*S+S/2,3,0,Math.PI*2);
        ctx.fill();
      }
    }
  }
}

function drawCoins() {
  const now=Date.now();
  const blink=Math.sin(now/120)>0;

  for (const c of coins) {
    if (!c.active) continue;

    const x=c.x*S+S/2;
    const y=c.y*S+S/2;

    ctx.save();

    ctx.shadowColor='#facc15';
    ctx.shadowBlur=blink?20:8;

    ctx.fillStyle=blink?'#fff176':'#eab308';
    ctx.beginPath();
    ctx.arc(x,y,blink?8:6,0,Math.PI*2);
    ctx.fill();

    ctx.shadowBlur=0;
    ctx.strokeStyle='#fff7ae';
    ctx.lineWidth=2;
    ctx.beginPath();
    ctx.arc(x,y,blink?8:6,0,Math.PI*2);
    ctx.stroke();

    ctx.restore();
  }
}

function drawPacman() {
  const cx=pacman.x+S/2;
  const cy=pacman.y+S/2;

  let angle=0;

  if (pacman.dir.x===-1) angle=Math.PI;
  if (pacman.dir.y===-1) angle=-Math.PI/2;
  if (pacman.dir.y===1) angle=Math.PI/2;

  const mouth=(Math.sin(Date.now()/65)+1)*0.22;

  ctx.fillStyle='#eab308';
  ctx.beginPath();
  ctx.moveTo(cx,cy);
  ctx.arc(
    cx,cy,S/2-2,
    angle+mouth,
    angle+Math.PI*2-mouth
  );
  ctx.closePath();
  ctx.fill();
}

function drawGhost(g) {
  if (g.dead) return;

  const cx=g.x+S/2;
  const cy=g.y+S/2;
  const frightened=Date.now()<powerUntil;

  ctx.fillStyle=frightened?'#2563eb':g.color;

  ctx.beginPath();
  ctx.arc(cx,cy-2,S/2-2,Math.PI,0,false);
  ctx.lineTo(cx+S/2-2,cy+S/2-2);

  for (let i=0;i<3;i++) {
    ctx.lineTo(
      cx+S/2-2-(i+1)*(S-4)/3,
      cy+S/2-2+(i%2===0?0:4)
    );
  }

  ctx.lineTo(cx-S/2+2,cy+S/2-2);
  ctx.closePath();
  ctx.fill();

  // Augen
  ctx.fillStyle='white';

  ctx.beginPath();
  ctx.arc(cx-4,cy-2,3,0,Math.PI*2);
  ctx.arc(cx+4,cy-2,3,0,Math.PI*2);
  ctx.fill();

  ctx.fillStyle=frightened?'#fff':'#111827';

  ctx.beginPath();
  ctx.arc(cx-4,cy-2,1.5,0,Math.PI*2);
  ctx.arc(cx+4,cy-2,1.5,0,Math.PI*2);
  ctx.fill();

  if (frightened && powerUntil-Date.now()<1500) {
    ctx.fillStyle='#fff';
    ctx.font='bold 10px sans-serif';
    ctx.textAlign='center';
    ctx.fillText('!',cx,cy-13);
  }
}

function drawPowerTimer() {
  if (Date.now()>=powerUntil) return;

  const remaining=Math.max(0,(powerUntil-Date.now())/1000);

  ctx.fillStyle='#2563eb';
  ctx.fillRect(5,5,90,17);

  ctx.fillStyle='white';
  ctx.font='bold 11px sans-serif';
  ctx.textAlign='center';
  ctx.fillText('POWER '+remaining.toFixed(1)+'s',50,17);
}

function draw() {
  drawMaze();
  drawCoins();
  drawPacman();

  for (const g of ghosts) {
    drawGhost(g);
  }

  drawPowerTimer();
}

function loop() {
  update();
  draw();
  requestAnimationFrame(loop);
}

function showMsg(title,html) {
  const m=document.getElementById('msg');

  m.innerHTML=
    '<div><h1>'+title+'</h1><p>'+html+'</p>'+
    (gameState==='over'||gameState==='finished'
      ?'<button class="btn" onclick="restart()">Nochmal spielen</button>'
      :'')+
    '</div>';

  m.classList.add('on');
}

function restart() {
  score=0;
  lives=3;
  level=1;

  document.getElementById('msg').classList.remove('on');

  createLevel();
}

function setDir(x,y) {
  pacman.nextDir={x,y};
}

const KEYS={
  ArrowLeft:()=>setDir(-1,0),
  ArrowRight:()=>setDir(1,0),
  ArrowUp:()=>setDir(0,-1),
  ArrowDown:()=>setDir(0,1),
  Enter:()=>{if(gameState==='over'||gameState==='finished')restart();},
  ' ':()=>{if(gameState==='over'||gameState==='finished')restart();}
};

document.addEventListener('keydown',e=>{
  const action=KEYS[e.key];

  if(action) {
    e.preventDefault();
    action();
  }
});

function bindTouch(id,x,y) {
  const btn=document.getElementById(id);

  btn.addEventListener('pointerdown',e=>{
    e.preventDefault();
    setDir(x,y);
  },{passive:false});
}

bindTouch('btn-left',-1,0);
bindTouch('btn-right',1,0);
bindTouch('btn-up',0,-1);
bindTouch('btn-down',0,1);

createLevel();
loop();

</script>
</body>
</html>
'''

    def widget():
        return {
            'icon':'🟡',
            'text':'Pacman',
            'sub':'10 Level · Power-Taler · Arcade'
        }

    api.route('index', seite)
    api.widget('Pacman', widget, ttl=60, icon='🟡')
