# -*- coding: utf-8 -*-
"""Flaschendrehen Orakel: Eine stylische Flasche als Kompassnadel (180° TV / 360° Mobil).
"""

EXT_ID = 'flaschendrehen'
EXT_NAME = 'Flaschendrehen'
EXT_DESCRIPTION = 'Eine drehbare Flasche als Orakel für den Filmabend mit 180° (TV) und 360° (Mobil) Modus.'
EXT_LINKS = [('Flaschendrehen starten', 'index')]

PAGE = r"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no"><title>Flaschendrehen Orakel</title>
<style>
:root{--bg:#090d16;--fg:#ffffff;--mut:#8fa3bf;--card:#131c2e;--acc:#00f0ff;--acc2:#ff007b}
*{box-sizing:border-box;user-select:none}
body{margin:0;min-height:100vh;background:var(--bg);color:var(--fg);font:clamp(15px,2.5vmin,20px)/1.4 system-ui,sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;overflow:hidden}

header{position:absolute;top:15px;text-align:center;z-index:10}
header h1{color:var(--acc);margin:0 0 2px;font-size:1.5em;text-shadow:0 0 10px rgba(0,240,255,0.4)}
header p{color:var(--mut);margin:0;font-size:0.8em}

.controls{position:absolute;top:75px;display:flex;gap:10px;z-index:10;background:var(--card);padding:6px 12px;border-radius:20px;border:1px solid rgba(0,240,255,0.2)}
.controls label{font-size:0.8em;color:var(--mut);display:flex;align-items:center;gap:4px;cursor:pointer}
.controls input{accent-color:var(--acc)}

#stage{position:relative;width:280px;height:280px;display:flex;align-items:center;justify-content:center;margin-top:30px}

/* Kompass-Basis / Kreis */
.compass-base{position:absolute;width:260px;height:260px;border:2px dashed rgba(0,240,255,0.25);border-radius:50%;box-shadow:0 0 30px rgba(0,240,255,0.05) inset}

/* Flaschen-Nadel (Drehpunkt in der exakten Mitte) */
.bottle-pivot{position:absolute;width:60px;height:240px;transform-origin:30px 120px;transition:transform 3.5s cubic-bezier(0.15, 0.85, 0.35, 1);cursor:pointer}

.btn-box{position:absolute;bottom:25px;display:flex;gap:12px;z-index:10}
button{font:inherit;font-weight:bold;background:linear-gradient(135deg,var(--acc),#0077ff);color:#000;border:0;border-radius:12px;padding:.6em 1.4em;cursor:pointer;box-shadow:0 4px 15px rgba(0,240,255,0.3)}
button:active{transform:scale(0.96)}

#info{position:absolute;bottom:85px;font-size:0.95em;color:var(--acc2);font-weight:bold;text-align:center;text-shadow:0 0 8px rgba(255,0,123,0.3);z-index:10;min-height:1.4em}
</style></head><body>
<header><h1>Flaschendrehen</h1><p>Wer ist heute dran mit ... ?</p></header>

<div class="controls">
  <label><input type="radio" name="mode" value="tv" checked> TV-Modus (180°)</label>
  <label><input type="radio" name="mode" value="mobile"> Mobil-Modus (360°)</label>
</div>

<div id="info">Bereit zum Drehen!</div>

<div id="stage">
  <div class="compass-base"></div>
  <div class="bottle-pivot" id="bottle" onclick="spin()">
    <!-- SVG Stylische Flasche -->
    <svg width="60" height="240" viewBox="0 0 60 240" fill="none" xmlns="http://www.w3.org/2000/svg">
      <!-- Flaschenhals -->
      <path d="M22 10H38V50H22V10Z" fill="url(#glass)" stroke="#00f0ff" stroke-width="1.5" opacity="0.8"/>
      <!-- Flaschendeckel -->
      <path d="M20 6H40V12H20V6Z" fill="#ff007b" rx="2"/>
      <!-- Flaschenkörper (Hauptteil) -->
      <path d="M22 50C22 50 12 70 12 110V210C12 221 20 228 30 228C40 228 48 221 48 210V110C48 70 38 50 38 50H22Z" fill="url(#glass)" stroke="#00f0ff" stroke-width="2"/>
      <!-- Lichtreflex auf der Flasche für echten Glas-Look -->
      <path d="M18 75C18 75 16 110 18 160" stroke="white" stroke-width="3" stroke-linecap="round" opacity="0.4"/>
      <defs>
        <linearGradient id="glass" x1="12" y1="10" x2="48" y2="228" gradientUnits="userSpaceOnUse">
          <stop stop-color="#00f0ff" stop-opacity="0.3"/>
          <stop offset="0.5" stop-color="#131c2e" stop-opacity="0.9"/>
          <stop offset="1" stop-color="#0077ff" stop-opacity="0.5"/>
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
    // TV-Modus (180°): Perfekte, gleichmäßige Verteilung im vorderen Halbkreis
    finalTargetAngle = Math.random() * 180 + 90;
  } else {
    // Mobil-Modus (360°): Voller Kreis
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
</script></body></html>"""

def widget():
    return {
        'text': 'Flaschendrehen',
        'sub': 'Wer ist heute dran mit ... ?',
        'lines': ['Tippen zum Starten auf der Couch']
    }

def register(api):
    api.widget('Flaschendrehen', widget, ttl=3600, icon='🍾')
    api.route('index', lambda req: PAGE)
