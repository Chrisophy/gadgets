# -*- coding: utf-8 -*-
"""Flaschendrehen Orakel: Eine stylische Flasche als Kompassnadel (180° TV / 360° Mobil)."""

EXT_ID = 'flaschendrehen'
EXT_NAME = 'Flaschendrehen'
EXT_DESCRIPTION = 'Eine drehbare Flasche als Orakel für den Filmabend mit 180° (TV) und 360° (Mobil) Modus.'
EXT_LINKS = [('Flaschendrehen starten', 'index')]

_api = None

def register(api):
    global _api
    _api = api

    def seite(req):
        return r'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no">
<title>Flaschendrehen Orakel</title>
<style>
:root{
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
*{box-sizing:border-box;user-select:none}
body{
  margin:0; min-height:100vh; background:var(--bg); color:var(--text);
  font:clamp(15px,2.5vmin,20px)/1.4 system-ui,sans-serif;
  display:flex; flex-direction:column; align-items:center; justify-content:center; overflow:hidden;
}
header{position:absolute;top:15px;text-align:center;z-index:10}
header h1{color:var(--text);margin:0 0 2px;font-size:1.5em;}
header p{color:var(--muted);margin:0;font-size:0.8em}

.controls{
  position:absolute;top:75px;display:flex;gap:10px;z-index:10;
  background:var(--panel);padding:6px 14px;border-radius:20px;border:1px solid var(--border);
}
.controls label{font-size:0.8em;color:var(--muted);display:flex;align-items:center;gap:4px;cursor:pointer}
.controls input{accent-color:var(--accent)}

#stage{position:relative;width:280px;height:280px;display:flex;align-items:center;justify-content:center;margin-top:30px}
.compass-base{position:absolute;width:260px;height:260px;border:2px dashed var(--border);border-radius:50%}
.bottle-pivot{position:absolute;width:60px;height:240px;transform-origin:30px 120px;transition:transform 3.5s cubic-bezier(0.15, 0.85, 0.35, 1);cursor:pointer}

.btn-box{position:absolute;bottom:25px;display:flex;gap:12px;z-index:10}
button{
  font:inherit;font-weight:bold;background:var(--blue-success);color:white;border:0;
  border-radius:12px;padding:.6em 1.4em;cursor:pointer;border:1px solid var(--border);
  transition:background 0.2s, transform 0.1s;
}
button:active{transform:scale(0.96)}
button:hover{background:var(--accent-hover)}

#info{
  position:absolute;bottom:85px;font-size:0.95em;color:var(--accent);font-weight:bold;
  text-align:center;z-index:10;min-height:1.4em;
}
</style>
</head>
<body>
<header><h1>Flaschendrehen</h1><p>Wer ist heute dran mit ... ?</p></header>

<div class="controls">
  <label><input type="radio" name="mode" value="tv" checked> TV-Modus (180°)</label>
  <label><input type="radio" name="mode" value="mobile"> Mobil-Modus (360°)</label>
</div>

<div id="info">Bereit zum Drehen!</div>

<div id="stage">
  <div class="compass-base"></div>
  <div class="bottle-pivot" id="bottle" onclick="spin()">
    <svg width="60" height="240" viewBox="0 0 60 240" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M22 10H38V50H22V10Z" fill="url(#glass)" stroke="#3b82f6" stroke-width="1.5" opacity="0.8"/>
      <path d="M20 6H40V12H20V6Z" fill="#2563eb" rx="2"/>
      <path d="M22 50C22 50 12 70 12 110V210C12 221 20 228 30 228C40 228 48 221 48 210V110C48 70 38 50 38 50H22Z" fill="url(#glass)" stroke="#3b82f6" stroke-width="2"/>
      <path d="M18 75C18 75 16 110 18 160" stroke="white" stroke-width="3" stroke-linecap="round" opacity="0.4"/>
      <defs>
        <linearGradient id="glass" x1="12" y1="10" x2="48" y2="228" gradientUnits="userSpaceOnUse">
          <stop stop-color="#3b82f6" stop-opacity="0.3"/>
          <stop offset="0.5" stop-color="#1a1f2c" stop-opacity="0.9"/>
          <stop offset="1" stop-color="#2563eb" stop-opacity="0.5"/>
        </linearGradient>
      </defs>
    </svg>
  </div>
</div>

<div class="btn-box">
  <button onclick="spin()">🎲 Flasche drehen</button>
</div>

<script>
"use strict";
let currentAngle = 0;
let isSpinning = false;

function spin(){
  if(isSpinning) return;
  isSpinning = true;
  document.getElementById('info').textContent = "Die Flasche rotiert...";
  
  const mode = document.querySelector('input[name="mode"]:checked').value;
  const bottle = document.getElementById('bottle');
  
  const extraSpins = (Math.floor(Math.random() * 4) + 3) * 360; 
  let finalTargetAngle = 0;
  
  if(mode === 'tv') {
    finalTargetAngle = Math.random() * 180 + 90;
  } else {
    finalTargetAngle = Math.random() * 360;
  }
  
  const currentBase = currentAngle - (currentAngle % 360);
  let nextAngle = currentBase + extraSpins + finalTargetAngle;
  
  if(nextAngle - currentAngle < 360 * 3) {
    nextAngle += 360;
  }
  
  currentAngle = nextAngle;
  bottle.style.transform = `rotate(${currentAngle}deg)`;
  
  setTimeout(() => {
    isSpinning = false;
    document.getElementById('info').textContent = "🎯 Treffer! Du bist dran mit ...!";
  }, 3500);
}
</script>
</body>
</html>
'''

    def widget():
        return {'icon': '🍾', 'text': 'Flaschendrehen', 'sub': 'Flaschendrehen Orakel'}

    api.route('index', seite)
    api.widget('Flaschendrehen', widget, ttl=60, icon='🍾')
