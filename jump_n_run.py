# -*- coding: utf-8 -*-
"""MovieScout Platformer: 20 Level, Gegner, Münzen und Fernbedienungssteuerung."""

EXT_ID = 'jump_n_run'
EXT_NAME = 'Jump & Run'
EXT_DESCRIPTION = '20 Level, 5 Leben, Schieß- und Hüpfgeister, Boss-Level.'
EXT_LINKS = [('Spiel starten', 'index')]

_api = None

def register(api):
    global _api
    _api = api

    def seite(req):
        return r'''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no">
<title>MovieScout Jump & Run</title>
<style>
:root {
  --bg:#10131a;
  --panel:#1a1f2c;
  --panel2:#222a3b;
  --border:#30394e;
  --text:#f1f3f8;
  --muted:#9da6b7;
  --accent:#3b82f6;
  --accent-hover:#2563eb;
  --blue-success:#3b82f6;
  --danger:#ef4444;
}
*{box-sizing:border-box;-webkit-user-select:none;user-select:none;-webkit-touch-callout:none}
html,body{
  height:100%;margin:0;overflow:hidden;background:var(--bg);color:var(--text);
  font:clamp(12px,2vmin,18px)/1.3 system-ui,sans-serif;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  touch-action:manipulation
}
#brand{font-size:1.15em;font-weight:900;color:var(--text);letter-spacing:1.5px;margin-bottom:3px;}
#ui{
  display:flex;justify-content:space-between;flex-wrap:wrap;
  width:min(96vw,800px);padding:5px 12px;font-weight:bold;font-size:.9em;
  color:var(--text);background:var(--panel);
  border:1px solid var(--border);border-radius:10px 10px 0 0;gap:5px
}
#ui span b{color:var(--accent)}
#stage{
  position:relative;width:min(96vw,800px);aspect-ratio:16/9;
  background:#000;border:1px solid var(--border);
  border-radius:0 0 12px 12px;overflow:hidden;
}
canvas{width:100%;height:100%;display:block}
#msg{
  position:absolute;inset:0;display:none;place-items:center;text-align:center;
  background:rgba(16,19,26,.94);padding:16px
}
#msg.on{display:grid}
#msg h1{color:var(--text);margin:0 0 10px;}
#msg p{margin:0 0 16px;color:var(--muted)}
.btn{
  font:inherit;background:var(--blue-success);
  color:#fff;border:0;border-radius:10px;padding:.6em 1.4em;
  cursor:pointer;font-weight:bold;border:1px solid var(--border);
}
.btn:hover{background:var(--accent-hover);}
#pad{display:none;gap:8px;margin-top:8px;width:min(96vw,800px);justify-content:center}
#pad button{
  font:inherit;font-size:1.1em;font-weight:bold;padding:.45em .85em;
  background:var(--panel);color:var(--text);border:1px solid var(--border);
  border-radius:12px;touch-action:none
}
#pad button:active{background:var(--accent);color:#fff;}
@media(pointer:coarse){#pad{display:flex}}
</style>
</head>
<body oncontextmenu="return false">

<div id="brand">🎬 MovieScout Arcade</div>
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

const cv=document.getElementById('cv');
const ctx=cv.getContext('2d');
const W=800,H=450;

let level=1,score=0,totalCoins=0,lives=5,ammo=5;
let gameState='play';
let levelTransition=false;

const p={
  x:50,y:350,w:22,h:32,vx:0,vy:0,
  grounded:false,dir:1,invulnerable:0
};

const keys={left:false,right:false,up:false};

let enemies=[];
let bullets=[];
let enemyBullets=[];
let ammoBoxes=[];
let curLvl=null;

function getLevel(lvl){
  const plt=[],cns=[],spk=[],enms=[],ammos=[];
  const goal={x:740,y:370,w:30,h:50};

  if([3,7,12,17].includes(lvl)){
    plt.push([0,420,250,30],[350,420,180,30],[600,420,200,30]);
  }else if([5,10,15,20].includes(lvl)){
    plt.push([0,420,150,30],[250,420,150,30],[500,420,100,30],[680,420,120,30]);
  }else{
    plt.push([0,420,800,30]);
  }

  const normal=(x,y,minX,maxX,dir=1,type='normal')=>({
    x,y,minX,maxX,dir,w:22,h:26,alive:true,type,vy:0,shootTimer:Math.random()*80
  });

  switch(lvl){
    case 1:
      plt.push([150,330,100,18],[320,250,100,18],[500,170,120,18]);
      cns.push([190,290],[360,210],[550,130]);
      enms.push(normal(340,214,320,400));
      ammos.push({x:530,y:130,collected:false});
      break;
    case 2:
      plt.push([100,340,80,18],[250,270,80,18],[400,200,80,18],[580,130,100,18]);
      cns.push([130,300],[280,230],[430,160]);
      enms.push(normal(260,234,250,310));
      ammos.push({x:420,y:160,collected:false});
      break;
    case 3:
      plt.push([120,320,90,18],[280,240,90,18],[460,180,100,18],[630,260,90,18]);
      cns.push([150,280],[310,200],[500,140]);
      spk.push([260,404,80,16]);
      enms.push(normal(480,144,460,540));
      break;
    case 4:
      plt.push([80,350,70,18],[200,280,70,18],[320,210,70,18],[440,140,70,18],[580,220,100,18]);
      cns.push([100,310],[220,240],[340,170],[460,100]);
      ammos.push({x:610,y:180,collected:false});
      enms.push(normal(330,174,320,370));
      break;
    case 5:
      plt.push([140,320,80,18],[280,230,120,18],[480,160,100,18]);
      cns.push([170,280],[320,190],[520,120],[600,380]);
      spk.push([160,404,80,16],[420,404,70,16]);
      enms.push(normal(300,194,280,380));
      break;
    case 6:
      plt.push([100,340,100,18],[280,280,100,18],[460,220,100,18],[620,150,100,18]);
      cns.push([130,300],[310,240],[490,180]);
      ammos.push({x:310,y:240,collected:false});
      enms.push(normal(480,184,460,540,-1));
      break;
    case 7:
      plt.push([80,300,90,18],[240,220,90,18],[400,150,90,18],[580,240,110,18]);
      cns.push([110,260],[270,180],[430,110]);
      spk.push([260,404,80,16],[540,404,100,16]);
      enms.push(normal(420,114,400,470));
      break;
    case 8:
      goal.y=100;
      plt.push([120,340,100,18],[300,260,120,18],[500,160,120,18]);
      cns.push([150,300],[340,220],[540,120]);
      enms.push(normal(330,224,300,400,1,'shooter'));
      ammos.push({x:160,y:300,collected:false});
      break;
    case 9:
      plt.push([100,330,80,18],[240,250,80,18],[380,180,80,18],[520,110,120,18]);
      cns.push([130,290],[270,210],[410,140]);
      spk.push([320,404,150,16]);
      enms.push(normal(550,74,520,620,-1,'shooter'));
      break;
    case 10:
      plt.push([150,320,90,18],[300,240,90,18],[450,170,90,18],[600,240,90,18]);
      cns.push([180,280],[330,200],[480,130]);
      enms.push(normal(320,204,300,370,1,'shooter'));
      enms.push(normal(470,134,450,520,-1,'shooter'));
      ammos.push({x:180,y:280,collected:false});
      break;
    case 11:
      plt.push([100,340,100,18],[280,270,100,18],[460,200,120,18],[630,130,90,18]);
      cns.push([130,300],[310,230],[500,160]);
      enms.push(normal(480,164,460,550,1,'jumper'));
      break;
    case 12:
      goal.y=120;
      plt.push([120,310,90,18],[270,230,90,18],[430,160,100,18],[600,220,100,18]);
      cns.push([150,270],[300,190],[460,120]);
      spk.push([220,404,100,16]);
      enms.push(normal(450,124,430,510,-1,'shooter'));
      enms.push(normal(290,194,270,340,1,'jumper'));
      break;
    case 13:
      plt.push([80,350,70,18],[180,280,70,18],[280,210,70,18],[380,140,70,18],[500,200,120,18]);
      cns.push([100,310],[200,240],[300,170],[400,100]);
      ammos.push({x:200,y:240,collected:false});
      enms.push(normal(390,104,380,430,1,'jumper'));
      break;
    case 14:
      plt.push([120,320,100,18],[280,240,100,18],[460,170,100,18],[620,250,90,18]);
      cns.push([150,280],[310,200],[490,130]);
      enms.push(normal(300,204,280,360,-1,'shooter'));
      enms.push(normal(480,134,460,530,1,'jumper'));
      break;
    case 15:
      plt.push([100,340,90,18],[250,260,90,18],[400,180,90,18],[550,110,120,18]);
      cns.push([130,300],[280,220],[430,140]);
      spk.push([180,404,80,16],[480,404,90,16]);
      enms.push(normal(420,144,400,470,1,'jumper'));
      break;
    case 16:
      plt.push([140,330,90,18],[300,250,100,18],[480,170,100,18],[630,230,90,18]);
      cns.push([170,290],[330,210],[510,130]);
      ammos.push({x:330,y:210,collected:false});
      enms.push(normal(500,134,480,560,-1,'shooter'));
      enms.push(normal(320,214,300,380,1,'jumper'));
      break;
    case 17:
      goal.y=100;
      plt.push([100,310,80,18],[230,230,80,18],[360,150,90,18],[520,220,120,18]);
      cns.push([130,270],[260,190],[390,110]);
      spk.push([280,404,120,16]);
      enms.push(normal(380,114,360,430,1,'shooter'));
      enms.push(normal(250,194,230,290,-1,'jumper'));
      break;
    case 18:
      plt.push([120,340,100,18],[280,270,100,18],[440,200,100,18],[600,130,100,18]);
      cns.push([150,300],[310,230],[470,160]);
      ammos.push({x:150,y:300,collected:false});
      enms.push(normal(460,164,440,520,1,'shooter'));
      enms.push(normal(300,234,280,360,-1,'jumper'));
      break;
    case 19:
      plt.push([90,350,80,18],[200,280,80,18],[310,210,80,18],[420,140,80,18],[560,200,130,18]);
      cns.push([110,310],[220,240],[330,170],[440,100]);
      spk.push([280,404,150,16]);
      enms.push(normal(440,104,420,480,1,'shooter'));
      enms.push(normal(330,174,310,370,-1,'jumper'));
      break;
    case 20:
      goal.y=80;
      plt.push([100,330,100,18],[260,250,100,18],[420,170,100,18],[600,120,100,18]);
      cns.push([130,290],[290,210],[450,130],[640,80]);
      spk.push([150,404,100,16],[450,404,120,16]);
      enms.push(normal(280,214,260,340,1,'shooter'));
      enms.push(normal(440,134,420,500,-1,'jumper'));
      enms.push(normal(620,84,600,680,1,'shooter'));
      ammos.push({x:130,y:290,collected:false});
      break;
  }

  return {plt,cns,spk,enms,ammos,goal,cnsCollected:[]};
}

function resetPlayer(){
  p.x=40;p.y=350;p.vx=0;p.vy=0;p.grounded=false;p.dir=1;p.invulnerable=60;
  keys.left=false;keys.right=false;keys.up=false;
}

function loadLevel(l){
  level=l;
  curLvl=getLevel(level);
  curLvl.cnsCollected=new Array(curLvl.cns.length).fill(false);
  enemies=curLvl.enms.map(e=>({...e}));
  ammoBoxes=curLvl.ammos.map(a=>({...a}));
  bullets=[];
  enemyBullets=[];
  resetPlayer();
  document.getElementById('lvl').textContent=level;
  levelTransition=false;
}

function updateHUD(){
  document.getElementById('lives').textContent=lives;
  document.getElementById('coins').textContent=totalCoins;
  document.getElementById('ammo').textContent=ammo;
  document.getElementById('score').textContent=score;
}

function fireBullet(){
  if(gameState!=='play'||ammo<=0)return;
  ammo--;
  bullets.push({
    x:p.x+(p.dir>0?p.w:-10),y:p.y+12,
    vx:p.dir*8,w:10,h:4
  });
  updateHUD();
}

function rectHit(a,b){
  return a.x<b.x+b.w&&a.x+a.w>b.x&&
         a.y<b.y+b.h&&a.y+a.h>b.y;
}

function loseLife(){
  if(gameState!=='play'||p.invulnerable>0)return;
  lives--;
  updateHUD();

  if(lives<=0){
    gameState='over';
    showMsg('💀 GAME OVER',`Du hast alle Leben verloren!<br>Punkte: ${score}`);
  }else{
    resetPlayer();
  }
}

function update(){
  if(gameState!=='play')return;

  if(p.invulnerable>0)p.invulnerable--;

  if(keys.left){p.vx=-4.5;p.dir=-1;}
  else if(keys.right){p.vx=4.5;p.dir=1;}
  else p.vx*=.7;

  if(keys.up&&p.grounded){
    p.vy=-11.5;
    p.grounded=false;
  }

  p.vy+=.55;
  p.x+=p.vx;
  p.y+=p.vy;
  p.grounded=false;

  for(const b of curLvl.plt){
    if(p.x<b[0]+b[2]&&p.x+p.w>b[0]&&
       p.y<b[1]+b[3]&&p.y+p.h>b[1]){
      if(p.vy>0&&p.y+p.h-p.vy<=b[1]+6){
        p.y=b[1]-p.h;
        p.vy=0;
        p.grounded=true;
      }
    }
  }

  if(p.x<0)p.x=0;
  if(p.x+p.w>W)p.x=W-p.w;
  if(p.y>H){loseLife();return;}

  for(let i=bullets.length-1;i>=0;i--){
    const b=bullets[i];
    b.x+=b.vx;
    let hit=false;

    for(const e of enemies){
      if(e.alive&&rectHit(b,e)){
        e.alive=false;
        score+=250;
        hit=true;
        break;
      }
    }

    if(hit||b.x<0||b.x>W)bullets.splice(i,1);
  }

  for(let i=enemyBullets.length-1;i>=0;i--){
    const eb=enemyBullets[i];
    eb.x+=eb.vx;
    if(eb.x<0||eb.x>W){
      enemyBullets.splice(i,1);
    }else if(rectHit(p,eb)){
      enemyBullets.splice(i,1);
      loseLife();
      if(gameState!=='play')return;
    }
  }

  for(const e of enemies){
    if(!e.alive)continue;

    e.x+=1.2*e.dir;
    if(e.x<e.minX){e.x=e.minX;e.dir=1;}
    if(e.x>e.maxX){e.x=e.maxX;e.dir=-1;}

    if(e.type==='jumper'){
      e.vy+=.4;
      e.y+=e.vy;
      for(const b of curLvl.plt){
        if(e.x+e.w>b[0]&&e.x<b[0]+b[2]&&
           e.y+e.h>=b[1]&&e.y+e.h-e.vy<=b[1]+6){
          e.y=b[1]-e.h;
          e.vy=-7;
        }
      }
    }

    if(e.type==='shooter'){
      e.shootTimer++;
      if(e.shootTimer>90){
        e.shootTimer=0;
        const dir=p.x<e.x?-1:1;
        enemyBullets.push({
          x:e.x+e.w/2,y:e.y+10,vx:dir*4,w:8,h:4
        });
      }
    }

    if(p.invulnerable===0&&rectHit(p,e)){
      if(p.vy>0&&p.y+p.h-p.vy<=e.y+12){
        e.alive=false;
        p.vy=-8;
        score+=300;
      }else{
        loseLife();
        if(gameState!=='play')return;
      }
    }
  }

  for(const a of ammoBoxes){
    if(!a.collected&&Math.hypot(p.x+p.w/2-a.x,p.y+p.h/2-a.y)<22){
      a.collected=true;
      ammo+=3;
    }
  }

  for(const s of curLvl.spk){
    if(rectHit(p,{x:s[0],y:s[1],w:s[2],h:s[3]})){
      loseLife();
      if(gameState!=='play')return;
    }
  }

  for(let i=0;i<curLvl.cns.length;i++){
    const c=curLvl.cns[i];
    if(!curLvl.cnsCollected[i]&&
       Math.hypot(p.x+p.w/2-c[0],p.y+p.h/2-c[1])<22){
      curLvl.cnsCollected[i]=true;
      totalCoins++;
      score+=100;
    }
  }

  if(!levelTransition&&rectHit(p,curLvl.goal)){
    levelTransition=true;
    if(level<20)loadLevel(level+1);
    else winGame();
  }

  updateHUD();
}

function showMsg(title,html,buttonText='Nochmal spielen (OK)'){
  const m=document.getElementById('msg');
  m.innerHTML=`<div><h1>${title}</h1><p>${html}</p>
  <button class="btn" onclick="restart()">${buttonText}</button></div>`;
  m.classList.add('on');
}

function showPause(){
  const m=document.getElementById('msg');
  m.innerHTML='<div><h1>⏸ PAUSE</h1><p>OK oder Schuss = Weiter</p><button class="btn" onclick="resumeGame()">Weiter</button></div>';
  m.classList.add('on');
}

function resumeGame(){
  if(gameState!=='paused')return;
  gameState='play';
  document.getElementById('msg').classList.remove('on');
}

function winGame(){
  gameState='win';
  showMsg('🏆 GEWONNEN!','Du hast alle 20 Level gemeistert!<br>Gesamtpunkte: '+score);
}

function restart(){
  score=0;totalCoins=0;lives=5;ammo=5;
  bullets=[];enemyBullets=[];
  gameState='play';
  document.getElementById('msg').classList.remove('on');
  updateHUD();
  loadLevel(1);
}

function draw(){
  ctx.clearRect(0,0,W,H);

  const grad=ctx.createLinearGradient(0,0,0,H);
  grad.addColorStop(0,'#161c2b');
  grad.addColorStop(1,'#10131a');
  ctx.fillStyle=grad;
  ctx.fillRect(0,0,W,H);

  ctx.fillStyle='rgba(255,255,255,.35)';
  for(let i=0;i<35;i++){
    const x=(i*137)%W,y=(i*71)%350;
    ctx.fillRect(x,y,2,2);
  }

  ctx.fillStyle='#222a3b';
  ctx.strokeStyle='#3b82f6';
  ctx.lineWidth=2;
  for(const b of curLvl.plt){
    ctx.fillRect(b[0],b[1],b[2],b[3]);
    ctx.strokeRect(b[0],b[1],b[2],b[3]);
  }

  for(const s of curLvl.spk){
    ctx.fillStyle='#ef4444';
    ctx.fillRect(s[0],s[1],s[2],s[3]);
    for(let x=s[0];x<s[0]+s[2];x+=12){
      ctx.beginPath();
      ctx.moveTo(x,s[1]);
      ctx.lineTo(x+6,s[1]-9);
      ctx.lineTo(x+12,s[1]);
      ctx.fill();
    }
  }

  for(const e of enemies){
    if(!e.alive)continue;
    ctx.fillStyle=e.type==='shooter'?'#ef4444':'#06b6d4';
    ctx.beginPath();
    ctx.arc(e.x+e.w/2,e.y+10,11,Math.PI,0,false);
    ctx.lineTo(e.x+e.w,e.y+e.h);
    ctx.lineTo(e.x,e.y+e.h);
    ctx.fill();
  }

  ctx.fillStyle='#3b82f6';
  ctx.shadowColor='#3b82f6';
  ctx.shadowBlur=8;
  for(let i=0;i<curLvl.cns.length;i++){
    const c=curLvl.cns[i];
    if(!curLvl.cnsCollected[i]){
      ctx.beginPath();
      ctx.arc(c[0],c[1],8,0,Math.PI*2);
      ctx.fill();
    }
  }
  ctx.shadowBlur=0;

  for(const a of ammoBoxes){
    if(!a.collected){
      ctx.fillStyle='#2563eb';
      ctx.fillRect(a.x-8,a.y-8,16,16);
    }
  }

  ctx.fillStyle='#60a5fa';
  for(const b of bullets)ctx.fillRect(b.x,b.y,b.w,b.h);
  ctx.fillStyle='#ef4444';
  for(const b of enemyBullets)ctx.fillRect(b.x,b.y,b.w,b.h);

  const g=curLvl.goal;
  ctx.fillStyle='#2563eb';
  ctx.fillRect(g.x,g.y,g.w,g.h);

  if(p.invulnerable===0||Math.floor(p.invulnerable/5)%2===0){
    ctx.fillStyle='#fff';
    ctx.fillRect(p.x+5,p.y,12,10);
    ctx.fillStyle='#3b82f6';
    ctx.fillRect(p.x+3,p.y+10,16,14);
  }

  ctx.fillStyle='rgba(241,243,248,.5)';
  ctx.font='bold 14px sans-serif';
  ctx.fillText('LEVEL '+level,15,25);
}

function loop(){
  update();
  draw();
  requestAnimationFrame(loop);
}

function act(k){
  if(k==='pause'){
    if(gameState==='play'){
      gameState='paused';
      showPause();
    }else if(gameState==='paused'){
      resumeGame();
    }
    return;
  }

  if(gameState==='paused'){
    if(k==='fire'||k==='jump')resumeGame();
    return;
  }

  if(gameState==='over'||gameState==='win'){
    if(k==='fire'||k==='jump')restart();
    return;
  }

  if(gameState!=='play')return;

  if(k==='left'){
    keys.left=true;
    keys.right=false;
    p.dir=-1;
  }else if(k==='right'){
    keys.right=true;
    keys.left=false;
    p.dir=1;
  }else if(k==='jump'){
    keys.up=true;
  }else if(k==='fire'){
    fireBullet();
  }
}

function release(k){
  if(k==='left')keys.left=false;
  else if(k==='right')keys.right=false;
  else if(k==='jump')keys.up=false;
}

const KEYS={
  ArrowLeft:'left',
  ArrowRight:'right',
  ArrowUp:'jump',
  ArrowDown:'fire',
  Enter:'fire',
  ' ':'fire',
  Select:'fire',
  Escape:'pause',
  Backspace:'pause',
  GoBack:'pause',
  BrowserBack:'pause',
  a:'left',
  d:'right',
  w:'jump'
};

document.addEventListener('keydown',e=>{
  const a=KEYS[e.key]||(e.keyCode===4?'pause':null);
  if(a){
    e.preventDefault();
    act(a);
  }
});

document.addEventListener('keyup',e=>{
  const a=KEYS[e.key];
  if(a)release(a);
});

window.addEventListener('blur',()=>{
  keys.left=false;
  keys.right=false;
  keys.up=false;
});

function bindTouch(id,actionType,isKey){
  const btn=document.getElementById(id);
  const start=e=>{
    e.preventDefault();
    if(isKey)act(actionType);
    else act('fire');
  };
  const end=e=>{
    e.preventDefault();
    if(isKey)release(actionType);
  };
  btn.addEventListener('touchstart',start,{passive:false});
  btn.addEventListener('touchend',end,{passive:false});
  btn.addEventListener('touchcancel',end,{passive:false});
  btn.addEventListener('mousedown',start);
  btn.addEventListener('mouseup',end);
  btn.addEventListener('mouseleave',end);
}

bindTouch('btn-left','left',true);
bindTouch('btn-right','right',true);
bindTouch('btn-jump','jump',true);
bindTouch('btn-fire','fire',false);

loadLevel(1);
updateHUD();
loop();
</script>
</body>
</html>
'''

    def widget():
        return {'icon': '🏃‍♂️', 'text': 'Jump & Run', 'sub': '20 Level Arcade-Abenteuer'}

    api.route('index', seite)
    api.widget('Jump & Run', widget, ttl=60, icon='🏃‍♂️')
