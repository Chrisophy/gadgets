# -*- coding: utf-8 -*-
"""MovieScout Platformer: 20 abwechslungsreiche Level, 5 Leben, Schieß-Geister (ab Lvl 8) & Hüpf-Geister (ab Lvl 11).
"""

EXT_ID = 'jump_n_run'
EXT_NAME = 'Retro Jump & Run (20 Level)'
EXT_DESCRIPTION = '20 einzigartige Level, 5 Leben, Spezial-Gegner ab Level 8 & 11.'
EXT_LINKS = [('Spiel starten', 'index')]

PAGE = r"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no"><title>MovieScout Jump & Run</title>
<style>
:root {
  --bg: #090b10;
  --fg: #ffffff;
  --mut: #a0aec0;
  --card: #121624;
  --violet: #8a2be2;
  --violet-dark: #5b18a3;
  --blue: #3b82f6;
  --blue-light: #60a5fa;
  --cyan: #06b6d4;
  --danger: #ef4444;
}

* {
  box-sizing: border-box;
  -webkit-user-select: none;
  user-select: none;
  -webkit-touch-callout: none;
}

html, body {
  height: 100%;
  margin: 0;
  overflow: hidden;
  background-color: var(--bg);
  color: var(--fg);
  font: clamp(12px, 2vmin, 18px)/1.3 system-ui, -apple-system, sans-serif;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  touch-action: manipulation;
}

#brand {
  font-size: 1.15em;
  font-weight: 900;
  color: #ffffff;
  letter-spacing: 1.5px;
  margin-bottom: 3px;
  text-shadow: 0 0 10px var(--blue);
}
#brand span { color: var(--blue-light); }

#ui {
  display: flex;
  justify-content: space-between;
  width: min(96vw, 800px);
  padding: 5px 12px;
  font-weight: bold;
  font-size: 0.9em;
  color: var(--blue-light);
  background: var(--card);
  border: 1px solid var(--violet-dark);
  border-radius: 10px 10px 0 0;
}

#ui span b { color: #ffffff; }

#stage {
  position: relative;
  width: min(96vw, 800px);
  aspect-ratio: 16/9;
  background: #0d111d;
  border: 2px solid var(--violet);
  border-radius: 0 0 12px 12px;
  overflow: hidden;
  box-shadow: 0 0 20px rgba(138, 43, 226, 0.25);
}

canvas {
  width: 100%;
  height: 100%;
  display: block;
}

#msg {
  position: absolute;
  inset: 0;
  display: none;
  place-items: center;
  text-align: center;
  background: rgba(9, 11, 16, 0.94);
  padding: 16px;
}

#msg.on { display: grid; }
#msg h1 { color: var(--blue-light); margin: 0 0 10px; text-shadow: 0 0 10px var(--violet); }
#msg p { margin: 0 0 16px; color: var(--mut); }

.btn {
  font: inherit;
  background: linear-gradient(135deg, var(--violet), var(--blue));
  color: #fff;
  border: 0;
  border-radius: 10px;
  padding: .6em 1.4em;
  cursor: pointer;
  font-weight: bold;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

#pad {
  display: none;
  gap: 8px;
  margin-top: 8px;
  width: min(96vw, 800px);
  justify-content: center;
}

#pad button {
  font: inherit;
  font-size: 1.1em;
  font-weight: bold;
  padding: .45em 0.85em;
  background: var(--card);
  color: var(--fg);
  border: 2px solid var(--violet);
  border-radius: 12px;
  touch-action: none;
}

#pad button:active {
  background: var(--violet);
  border-color: var(--blue-light);
}

@media (pointer: coarse) { #pad { display: flex; } }
</style></head><body oncontextmenu="return false;">

<div id="brand">🎬 Movie<span>Scout</span> Arcade</div>
<div id="ui">
  <span>Lvl: <b id="lvl">1</b>/20</span>
  <span>❤️ Leben: <b id="lives">5</b></span>
  <span>Münzen: <b id="coins">0</b></span>
  <span>Ammo: <b id="ammo">5</b></span>
  <span>Punkte: <b id="score">0</b></span>
</div>
<div id="stage">
  <canvas id="cv" width="800" height="450"></canvas>
  <div id="msg"></div>
</div>
<div id="pad">
  <button id="btn-left">◀</button>
  <button id="btn-jump">▲ JUMP</button>
  <button id="btn-fire">💥 SCHUSS</button>
  <button id="btn-right">▶</button>
</div>

<script>
"use strict";
const cv = document.getElementById('cv'), ctx = cv.getContext('2d');
const W = 800, H = 450;
let level = 1, score = 0, totalCoins = 0, lives = 5, ammo = 5, gameState = 'play';

const p = { x: 50, y: 350, w: 22, h: 32, vx: 0, vy: 0, grounded: false, dir: 1 };
const keys = { left: false, right: false, up: false };

let enemies = [];
let bullets = [];
let enemyBullets = [];
let ammoBoxes = [];

// 20 extrem abwechslungsreiche Level-Layouts
function getLevel(lvl) {
  let plt = [];
  let cns = [];
  let spk = [];
  let enms = [];
  let ammos = [];
  let goal = { x: 740, y: 370, w: 30, h: 50 };

  // Basis-Boden mit Lücken je nach Level
  if (lvl === 3 || lvl === 7 || lvl === 12 || lvl === 17) {
    plt.push([0, 420, 250, 30], [350, 420, 180, 30], [600, 420, 200, 30]); // Lücken im Boden
  } else if (lvl === 5 || lvl === 10 || lvl === 15 || lvl === 20) {
    plt.push([0, 420, 150, 30], [250, 420, 150, 30], [500, 420, 100, 30], [680, 420, 120, 30]);
  } else {
    plt.push([0, 420, 800, 30]); // Solider Boden
  }

  // 20 Einzigartige Level-Architekturen
  switch(lvl) {
    case 1:
      plt.push([150, 330, 100, 18], [320, 250, 100, 18], [500, 170, 120, 18]);
      cns.push([190, 290], [360, 210], [550, 130]);
      enms.push({ x: 340, y: 214, minX: 320, maxX: 400, dir: 1, w: 22, h: 26, alive: true, type: 'normal' });
      ammos.push({ x: 530, y: 130, collected: false });
      break;
    case 2:
      plt.push([100, 340, 80, 18], [250, 270, 80, 18], [400, 200, 80, 18], [580, 130, 100, 18]);
      cns.push([130, 300], [280, 230], [430, 160]);
      enms.push({ x: 260, y: 234, minX: 250, maxX: 310, dir: 1, w: 22, h: 26, alive: true, type: 'normal' });
      ammos.push({ x: 420, y: 160, collected: false });
      break;
    case 3:
      plt.push([120, 320, 90, 18], [280, 240, 90, 18], [460, 180, 100, 18], [630, 260, 90, 18]);
      cns.push([150, 280], [310, 200], [500, 140]);
      spk.push([260, 404, 80, 16]);
      enms.push({ x: 480, y: 144, minX: 460, maxX: 540, dir: 1, w: 22, h: 26, alive: true, type: 'normal' });
      break;
    case 4:
      plt.push([80, 350, 70, 18], [200, 280, 70, 18], [320, 210, 70, 18], [440, 140, 70, 18], [580, 220, 100, 18]);
      cns.push([100, 310], [220, 240], [340, 170], [460, 100]);
      ammos.push({ x: 610, y: 180, collected: false });
      enms.push({ x: 330, y: 174, minX: 320, maxX: 370, dir: 1, w: 22, h: 26, alive: true, type: 'normal' });
      break;
    case 5:
      plt.push([140, 320, 80, 18], [280, 230, 120, 18], [480, 160, 100, 18]);
      cns.push([170, 280], [320, 190], [520, 120], [600, 380]);
      spk.push([160, 404, 80, 16], [420, 404, 70, 16]);
      enms.push({ x: 300, y: 194, minX: 280, maxX: 380, dir: 1, w: 22, h: 26, alive: true, type: 'normal' });
      break;
    case 6:
      plt.push([100, 340, 100, 18], [280, 280, 100, 18], [460, 220, 100, 18], [620, 150, 100, 18]);
      cns.push([130, 300], [310, 240], [490, 180]);
      ammos.push({ x: 310, y: 240, collected: false });
      enms.push({ x: 480, y: 184, minX: 460, maxX: 540, dir: -1, w: 22, h: 26, alive: true, type: 'normal' });
      break;
    case 7:
      plt.push([80, 300, 90, 18], [240, 220, 90, 18], [400, 150, 90, 18], [580, 240, 110, 18]);
      cns.push([110, 260], [270, 180], [430, 110]);
      spk.push([260, 404, 80, 16], [540, 404, 100, 16]);
      enms.push({ x: 420, y: 114, minX: 400, maxX: 470, dir: 1, w: 22, h: 26, alive: true, type: 'normal' });
      break;
    case 8: // AB HIER: SCHIESSENDE ROTE GEISTER!
      goal.y = 100;
      plt.push([120, 340, 100, 18], [300, 260, 120, 18], [500, 160, 120, 18]);
      cns.push([150, 300], [340, 220], [540, 120]);
      enms.push({ x: 330, y: 224, minX: 300, maxX: 400, dir: 1, w: 22, h: 26, alive: true, type: 'shooter' });
      ammos.push({ x: 160, y: 300, collected: false });
      break;
    case 9:
      plt.push([100, 330, 80, 18], [240, 250, 80, 18], [380, 180, 80, 18], [520, 110, 120, 18]);
      cns.push([130, 290], [270, 210], [410, 140]);
      spk.push([320, 404, 150, 16]);
      enms.push({ x: 550, y: 74, minX: 520, maxX: 620, dir: -1, w: 22, h: 26, alive: true, type: 'shooter' });
      break;
    case 10:
      plt.push([150, 320, 90, 18], [300, 240, 90, 18], [450, 170, 90, 18], [600, 240, 90, 18]);
      cns.push([180, 280], [330, 200], [480, 130]);
      enms.push({ x: 320, y: 204, minX: 300, maxX: 370, dir: 1, w: 22, h: 26, alive: true, type: 'shooter' });
      enms.push({ x: 470, y: 134, minX: 450, maxX: 520, dir: -1, w: 22, h: 26, alive: true, type: 'shooter' });
      ammos.push({ x: 180, y: 280, collected: false });
      break;
    case 11: // AB HIER: HÜPFENDE GEISTER!
      plt.push([100, 340, 100, 18], [280, 270, 100, 18], [460, 200, 120, 18], [630, 130, 90, 18]);
      cns.push([130, 300], [310, 230], [500, 160]);
      enms.push({ x: 480, y: 164, minX: 460, maxX: 550, dir: 1, w: 22, h: 26, alive: true, type: 'jumper' });
      break;
    case 12:
      goal.y = 120;
      plt.push([120, 310, 90, 18], [270, 230, 90, 18], [430, 160, 100, 18], [600, 220, 100, 18]);
      cns.push([150, 270], [300, 190], [460, 120]);
      spk.push([220, 404, 100, 16]);
      enms.push({ x: 450, y: 124, minX: 430, maxX: 510, dir: -1, w: 22, h: 26, alive: true, type: 'shooter' });
      enms.push({ x: 290, y: 194, minX: 270, maxX: 340, dir: 1, w: 22, h: 26, alive: true, type: 'jumper' });
      break;
    case 13:
      plt.push([80, 350, 70, 18], [180, 280, 70, 18], [280, 210, 70, 18], [380, 140, 70, 18], [500, 200, 120, 18]);
      cns.push([100, 310], [200, 240], [300, 170], [400, 100]);
      ammos.push({ x: 200, y: 240, collected: false });
      enms.push({ x: 390, y: 104, minX: 380, maxX: 430, dir: 1, w: 22, h: 26, alive: true, type: 'jumper' });
      break;
    case 14:
      plt.push([120, 320, 100, 18], [280, 240, 100, 18], [460, 170, 100, 18], [620, 250, 90, 18]);
      cns.push([150, 280], [310, 200], [490, 130]);
      enms.push({ x: 300, y: 204, minX: 280, maxX: 360, dir: -1, w: 22, h: 26, alive: true, type: 'shooter' });
      enms.push({ x: 480, y: 134, minX: 460, maxX: 530, dir: 1, w: 22, h: 26, alive: true, type: 'jumper' });
      break;
    case 15:
      plt.push([100, 340, 90, 18], [250, 260, 90, 18], [400, 180, 90, 18], [550, 110, 120, 18]);
      cns.push([130, 300], [280, 220], [430, 140]);
      spk.push([180, 404, 80, 16], [480, 404, 90, 16]);
      enms.push({ x: 420, y: 144, minX: 400, maxX: 470, dir: 1, w: 22, h: 26, alive: true, type: 'jumper' });
      break;
    case 16:
      plt.push([140, 330, 90, 18], [300, 250, 100, 18], [480, 170, 100, 18], [630, 230, 90, 18]);
      cns.push([170, 290], [330, 210], [510, 130]);
      ammos.push({ x: 330, y: 210, collected: false });
      enms.push({ x: 500, y: 134, minX: 480, maxX: 560, dir: -1, w: 22, h: 26, alive: true, type: 'shooter' });
      enms.push({ x: 320, y: 214, minX: 300, maxX: 380, dir: 1, w: 22, h: 26, alive: true, type: 'jumper' });
      break;
    case 17:
      goal.y = 100;
      plt.push([100, 310, 80, 18], [230, 230, 80, 18], [360, 150, 90, 18], [520, 220, 120, 18]);
      cns.push([130, 270], [260, 190], [390, 110]);
      spk.push([280, 404, 120, 16]);
      enms.push({ x: 380, y: 114, minX: 360, maxX: 430, dir: 1, w: 22, h: 26, alive: true, type: 'shooter' });
      enms.push({ x: 250, y: 194, minX: 230, maxX: 290, dir: -1, w: 22, h: 26, alive: true, type: 'jumper' });
      break;
    case 18:
      plt.push([120, 340, 100, 18], [280, 270, 100, 18], [440, 200, 100, 18], [600, 130, 100, 18]);
      cns.push([150, 300], [310, 230], [470, 160]);
      ammos.push({ x: 150, y: 300, collected: false });
      enms.push({ x: 460, y: 164, minX: 440, maxX: 520, dir: 1, w: 22, h: 26, alive: true, type: 'shooter' });
      enms.push({ x: 300, y: 234, minX: 280, maxX: 360, dir: -1, w: 22, h: 26, alive: true, type: 'jumper' });
      break;
    case 19:
      plt.push([90, 350, 80, 18], [200, 280, 80, 18], [310, 210, 80, 18], [420, 140, 80, 18], [560, 200, 130, 18]);
      cns.push([110, 310], [220, 240], [330, 170], [440, 100]);
      spk.push([280, 404, 150, 16]);
      enms.push({ x: 440, y: 104, minX: 420, maxX: 480, dir: 1, w: 22, h: 26, alive: true, type: 'shooter' });
      enms.push({ x: 330, y: 174, minX: 310, maxX: 370, dir: -1, w: 22, h: 26, alive: true, type: 'jumper' });
      break;
    case 20: // BOSS-LEVEL
      goal.y = 80;
      plt.push([100, 330, 100, 18], [260, 250, 100, 18], [420, 170, 100, 18], [600, 120, 100, 18]);
      cns.push([130, 290], [290, 210], [450, 130], [640, 80]);
      spk.push([150, 404, 100, 16], [450, 404, 120, 16]);
      enms.push({ x: 280, y: 214, minX: 260, maxX: 340, dir: 1, w: 22, h: 26, alive: true, type: 'shooter' });
      enms.push({ x: 440, y: 134, minX: 420, maxX: 500, dir: -1, w: 22, h: 26, alive: true, type: 'jumper' });
      enms.push({ x: 620, y: 84, minX: 600, maxX: 680, dir: 1, w: 22, h: 26, alive: true, type: 'shooter' });
      ammos.push({ x: 130, y: 290, collected: false });
      break;
  }

  return { plt, cns, spk, enms, ammos, goal };
}

let curLvl = getLevel(level);

function resetPlayer() {
  p.x = 40; p.y = 350; p.vx = 0; p.vy = 0;
}

function loadLevel(l) {
  level = l;
  curLvl = getLevel(level);
  curLvl.cnsCollected = new Array(curLvl.cns.length).fill(false);
  enemies = curLvl.enms.map(e => ({ ...e, vy: 0, shootTimer: Math.random() * 80 }));
  ammoBoxes = curLvl.ammos.map(a => ({ ...a }));
  enemyBullets = [];
  resetPlayer();
  document.getElementById('lvl').textContent = level;
}

function fireBullet() {
  if (ammo > 0) {
    ammo--;
    document.getElementById('ammo').textContent = ammo;
    bullets.push({ x: p.x + (p.dir > 0 ? p.w : -10), y: p.y + 12, vx: p.dir * 8, w: 10, h: 4 });
  }
}

function update() {
  if (gameState !== 'play') return;

  if (keys.left) { p.vx = -4.5; p.dir = -1; }
  else if (keys.right) { p.vx = 4.5; p.dir = 1; }
  else p.vx *= 0.7;

  if (keys.up && p.grounded) {
    p.vy = -11.5;
    p.grounded = false;
  }

  p.vy += 0.55;
  p.x += p.vx;
  p.y += p.vy;

  p.grounded = false;

  curLvl.plt.forEach(b => {
    if (p.x < b[0] + b[2] && p.x + p.w > b[0] && p.y < b[1] + b[3] && p.y + p.h > b[1]) {
      if (p.vy > 0 && p.y + p.h - p.vy <= b[1] + 6) {
        p.y = b[1] - p.h;
        p.vy = 0;
        p.grounded = true;
      }
    }
  });

  if (p.x < 0) p.x = 0;
  if (p.x + p.w > W) p.x = W - p.w;
  if (p.y > H) loseLife();

  // Spieler-Schüsse aktualisieren
  bullets.forEach((b, idx) => {
    b.x += b.vx;
    if (b.x < 0 || b.x > W) bullets.splice(idx, 1);
    else {
      enemies.forEach(e => {
        if (e.alive && b.x < e.x + e.w && b.x + b.w > e.x && b.y < e.y + e.h && b.y + b.h > e.y) {
          e.alive = false;
          bullets.splice(idx, 1);
          score += 250;
          document.getElementById('score').textContent = score;
        }
      });
    }
  });

  // Gegner-Schüsse aktualisieren
  enemyBullets.forEach((eb, idx) => {
    eb.x += eb.vx;
    if (eb.x < 0 || eb.x > W) enemyBullets.splice(idx, 1);
    else if (p.x < eb.x + eb.w && p.x + p.w > eb.x && p.y < eb.y + eb.h && p.y + p.h > eb.y) {
      enemyBullets.splice(idx, 1);
      loseLife();
    }
  });

  // Geister-Logik (Bewegung, Hüpfen, Schießen)
  enemies.forEach(e => {
    if (!e.alive) return;
    
    // Horizontale Bewegung
    e.x += 1.2 * e.dir;
    if (e.x < e.minX || e.x > e.maxX) e.dir *= -1;

    // Hüpf-Verhalten ab Level 11
    if (e.type === 'jumper') {
      e.vy = (e.vy || 0) + 0.4;
      e.y += e.vy;
      // Finde Plattform unter dem Geist
      curLvl.plt.forEach(b => {
        if (e.x + e.w > b[0] && e.x < b[0] + b[2] && e.y + e.h >= b[1] && e.y + e.h - e.vy <= b[1] + 6) {
          e.y = b[1] - e.h;
          e.vy = -7; // Hüpft hoch
        }
      });
    }

    // Schuss-Verhalten ab Level 8 bei Schützen
    if (e.type === 'shooter') {
      e.shootTimer = (e.shootTimer || 0) + 1;
      if (e.shootTimer > 90) { // ca. alle 1.5 Sekunden
        e.shootTimer = 0;
        let sDir = p.x < e.x ? -1 : 1;
        enemyBullets.push({ x: e.x, y: e.y + 10, vx: sDir * 4, w: 8, h: 4 });
      }
    }

    // Kollision Spieler mit Geist
    if (p.x < e.x + e.w && p.x + p.w > e.x && p.y < e.y + e.h && p.y + p.h > e.y) {
      // Draufspringen tötet den Geist immer!
      if (p.vy > 0 && p.y + p.h - p.vy <= e.y + 12) {
        e.alive = false;
        p.vy = -8;
        score += 300;
        document.getElementById('score').textContent = score;
      } else {
        loseLife();
      }
    }
  });

  // Munition aufsammeln
  ammoBoxes.forEach(a => {
    if (!a.collected && Math.hypot(p.x + p.w/2 - a.x, p.y + p.h/2 - a.y) < 22) {
      a.collected = true;
      ammo += 3;
      document.getElementById('ammo').textContent = ammo;
    }
  });

  curLvl.spk.forEach(s => {
    if (p.x < s[0] + s[2] && p.x + p.w > s[0] && p.y < s[1] + s[3] && p.y + p.h > s[1]) {
      loseLife();
    }
  });

  curLvl.cns.forEach((c, idx) => {
    if (!curLvl.cnsCollected[idx] && Math.hypot(p.x + p.w/2 - c[0], p.y + p.h/2 - c[1]) < 22) {
      curLvl.cnsCollected[idx] = true;
      totalCoins++;
      score += 100;
      document.getElementById('coins').textContent = totalCoins;
      document.getElementById('score').textContent = score;
    }
  });

  const g = curLvl.goal;
  if (p.x < g.x + g.w && p.x + p.w > g.x && p.y < g.y + g.h && p.y + p.h > g.y) {
    if (level < 20) {
      loadLevel(level + 1);
    } else {
      winGame();
    }
  }
}

function loseLife() {
  lives--;
  document.getElementById('lives').textContent = lives;
  if (lives <= 0) {
    gameState = 'over';
    showMsg('💀 GAME OVER', `Du hast alle Leben verloren!<br>Erreichte Punkte: ${score}`);
  } else {
    resetPlayer();
  }
}

function winGame() {
  gameState = 'win';
  showMsg('🏆 GEWONNEN!', `Du hast alle 20 Level gemeistert!<br>Gesamtpunkte: ${score}`);
}

function showMsg(title, html) {
  const m = document.getElementById('msg');
  m.innerHTML = `<h1>${title}</h1><p>${html}</p><button class="btn" onclick="restart()">Nochmal spielen (OK)</button>`;
  m.classList.add('on');
}

function restart() {
  document.getElementById('msg').classList.remove('on');
  score = 0; totalCoins = 0; lives = 5; ammo = 5;
  document.getElementById('coins').textContent = 0;
  document.getElementById('lives').textContent = 5;
  document.getElementById('ammo').textContent = 5;
  document.getElementById('score').textContent = 0;
  bullets = [];
  enemyBullets = [];
  gameState = 'play';
  loadLevel(1);
}

function draw() {
  ctx.clearRect(0, 0, W, H);

  // Plattformen
  ctx.fillStyle = '#1e2638';
  ctx.strokeStyle = '#8a2be2';
  ctx.lineWidth = 2;
  curLvl.plt.forEach(b => {
    ctx.fillRect(b[0], b[1], b[2], b[3]);
    ctx.strokeRect(b[0], b[1], b[2], b[3]);
  });

  // Stacheln
  ctx.fillStyle = '#ef4444';
  curLvl.spk.forEach(s => {
    ctx.fillRect(s[0], s[1], s[2], s[3]);
  });

  // Geister-Gegner (Blau = Normal/Hüpfer, Rot = Schütze)
  enemies.forEach(e => {
    if (!e.alive) return;
    ctx.fillStyle = (e.type === 'shooter') ? '#ef4444' : '#06b6d4';
    ctx.beginPath();
    ctx.arc(e.x + e.w/2, e.y + 10, 11, Math.PI, 0, false);
    ctx.lineTo(e.x + e.w, e.y + e.h);
    ctx.lineTo(e.x, e.y + e.h);
    ctx.fill();
    // Augen
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(e.x + 4, e.y + 6, 3, 3);
    ctx.fillRect(e.x + 13, e.y + 6, 3, 3);
  });

  // Münzen
  ctx.fillStyle = '#06b6d4';
  ctx.shadowColor = '#06b6d4';
  ctx.shadowBlur = 8;
  curLvl.cns.forEach((c, idx) => {
    if (!curLvl.cnsCollected[idx]) {
      ctx.beginPath();
      ctx.arc(c[0], c[1], 8, 0, Math.PI * 2);
      ctx.fill();
    }
  });

  // Munitionskisten
  ammoBoxes.forEach(a => {
    if (!a.collected) {
      ctx.fillStyle = '#8a2be2';
      ctx.fillRect(a.x - 8, a.y - 8, 16, 16);
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(a.x - 3, a.y - 3, 6, 6);
    }
  });
  ctx.shadowBlur = 0;

  // Schüsse Spieler
  ctx.fillStyle = '#60a5fa';
  bullets.forEach(b => ctx.fillRect(b.x, b.y, b.w, b.h));

  // Schüsse Gegner
  ctx.fillStyle = '#ef4444';
  enemyBullets.forEach(eb => ctx.fillRect(eb.x, eb.y, eb.w, eb.h));

  // Ziel (Tür)
  const g = curLvl.goal;
  ctx.fillStyle = '#8a2be2';
  ctx.fillRect(g.x, g.y, g.w, g.h);
  ctx.fillStyle = '#60a5fa';
  ctx.fillRect(g.x + 4, g.y + 4, g.w - 8, g.h - 8);

  // Spieler-Männlein
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(p.x + 5, p.y, 12, 10);
  ctx.fillStyle = '#3b82f6';
  ctx.fillRect(p.x + 3, p.y + 10, 16, 14);
  ctx.fillStyle = '#60a5fa';
  ctx.fillRect(p.x + 4, p.y + 24, 5, 8);
  ctx.fillRect(p.x + 13, p.y + 24, 5, 8);
}

function loop() {
  update();
  draw();
  requestAnimationFrame(loop);
}

// Steuerung
document.addEventListener('keydown', e => {
  const k = e.key;
  if (k === 'ArrowLeft' || k === 'a') keys.left = true;
  if (k === 'ArrowRight' || k === 'd') keys.right = true;
  if (k === 'ArrowUp' || k === 'w') keys.up = true;
  if (k === 'Enter' || k === ' ') {
    if (gameState === 'win' || gameState === 'over') { restart(); }
    else { fireBullet(); }
  }
});

document.addEventListener('keyup', e => {
  const k = e.key;
  if (k === 'ArrowLeft' || k === 'a') keys.left = false;
  if (k === 'ArrowRight' || k === 'd') keys.right = false;
  if (k === 'ArrowUp' || k === 'w') keys.up = false;
});

function bindTouch(id, actionType, isKey) {
  const btn = document.getElementById(id);
  const start = (e) => {
    e.preventDefault();
    if (isKey) keys[actionType] = true;
    else fireBullet();
  };
  const end = (e) => {
    e.preventDefault();
    if (isKey) keys[actionType] = false;
  };
  
  btn.addEventListener('touchstart', start, { passive: false });
  btn.addEventListener('touchend', end, { passive: false });
  btn.addEventListener('mousedown', start);
  btn.addEventListener('mouseup', end);
}

bindTouch('btn-left', 'left', true);
bindTouch('btn-right', 'right', true);
bindTouch('btn-jump', 'up', true);

const fireBtn = document.getElementById('btn-fire');
fireBtn.addEventListener('touchstart', (e) => { e.preventDefault(); fireBullet(); }, { passive: false });
fireBtn.addEventListener('mousedown', (e) => { e.preventDefault(); fireBullet(); });

loadLevel(1);
loop();
</script></body></html>"""

def register(api):
    api.route('index', lambda req: PAGE)
