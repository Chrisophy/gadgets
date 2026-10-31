# -*- coding: utf-8 -*-
"""Fun Gadgets Suite: Interaktive Couch-Tools, Zufallsgeneratoren, Snack-Picker und Orakel.
"""

EXT_ID = 'fun_gadgets'
EXT_NAME = 'Fun Gadgets Suite'
EXT_DESCRIPTION = 'Interaktive Couch-Tools für den Filmabend: Zufalls-Filmtipp, Snack-Berater, Binge-Rechner, Duell und Orakel.'
EXT_LINKS = [('Gadgets öffnen', 'index')]

PAGE = r"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no"><title>Fun Gadgets</title>
<style>
:root{--bg:#0f141b;--fg:#e8edf3;--mut:#93a1b3;--card:#18202b;--acc:#ffb703;--acc2:#4da3ff}
*{box-sizing:border-box}body{margin:0;min-height:100vh;background:var(--bg);color:var(--fg);font:clamp(16px,2.5vmin,24px)/1.4 system-ui,sans-serif;display:flex;justify-content:center;padding:16px}
main{width:min(96vw,700px)}header{text-align:center;margin-bottom:20px}header h1{color:var(--acc);margin:0 0 6px;font-size:1.8em}header p{color:var(--mut);margin:0;font-size:.9em}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}@media(max-width:540px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:3px solid transparent;border-radius:16px;padding:18px;cursor:pointer;transition:transform .1s,border-color .1s;display:flex;flex-direction:column;justify-content:space-between}
.card:hover,.card:focus{border-color:var(--acc2);outline:none;transform:translateY(-2px)}
.card h2{font-size:1.15em;margin:0 0 8px;color:var(--fg)}
.card p{font-size:.85em;color:var(--mut);margin:0}
#resBox{margin-top:20px;background:var(--card);border:2px solid var(--acc);border-radius:16px;padding:20px;text-align:center;display:none}
#resBox.on{display:block}#resTitle{color:var(--acc);font-size:1.2em;margin-bottom:8px;font-weight:bold}
#resText{font-size:1.1em;margin-bottom:14px}
button.close{font:inherit;background:#2a3350;color:var(--fg);border:0;border-radius:10px;padding:.5em 1.2em;cursor:pointer}
</style></head><body><main>
<header><h1>🚀 MovieScout Fun Gadgets</h1><p>Dein Assistent für den perfekten Filmabend auf der Couch</p></header>
<div class="grid">
  <div class="card" tabindex="0" onclick="run('random')"><div><h2>🎲 Zufalls-Filmtipp</h2><p>Wählt spontan einen Top-Film aus.</p></div></div>
  <div class="card" tabindex="0" onclick="run('snack')"><div><h2>🍿 Snack & Getränk</h2><p>Was passt zu deinem Filmabend?</p></div></div>
  <div class="card" tabindex="0" onclick="run('binge')"><div><h2>⏱️ Binge-Rechner</h2><p>Wann schläfst du heute ein?</p></div></div>
  <div class="card" tabindex="0" onclick="run('duell')"><div><h2>⚔️ Fernbedienungs-Duell</h2><p>Wer darf heute aussuchen?</p></div></div>
  <div class="card" tabindex="0" onclick="run('trash')"><div><h2>🎬 B-Movie Plot-Generator</h2><p>Erstelle absurde Trash-Ideen.</p></div></div>
  <div class="card" tabindex="0" onclick="run('oracle')"><div><h2>🔮 Magisches Orakel</h2><p>Soll ich diesen Film gucken?</p></div></div>
</div>
<div id="resBox"><div id="resTitle"></div><div id="resText"></div><button class="close" onclick="hideRes()">Schließen</button></div>
</main><script>
"use strict";
const DATA={
  random:{title:"🎲 Zufalls-Filmtipp",items:[
    "✨ Inception (Sci-Fi-Meisterwerk)", "✨ Interstellar (Gänsehaut-Kino)", "✨ Shrek (Der ultimative Animations-Klassiker)", 
    "✨ Pulp Fiction (Kult-Krimi)", "✨ Matrix (Sci-Fi-Action)", "✨ Der Pate (Mafia-Epos)"
  ]},
  snack:{title:"🍿 Snack- & Getränke-Empfehlung",items:[
    "🍿 Klassisches süß-salziges Popcorn mit extra Butter", "🧀 Nachos mit warmem Käsedip und Jalapeños", 
    "🍕 Tiefkühlpizza um 23:00 Uhr (Der Binge-Klassiker)", "🍏 Apfelscheiben mit Erdnussbutter (Versuch, gesund zu bleiben)"
  ]},
  binge:{title:"⏱️ Binge-Rechner",items:[
    "⏰ Aktueller Stand: Wenn du jetzt 3 Folgen á 45 Min schaust, ist es ca. 02:15 Uhr morgens. Viel Glück morgen bei der Arbeit!",
    "⏰ 1 langer Blockbuster (140 Min) -> Schlafenszeit ca. 00:20 Uhr. Vernünftig und machbar!",
    "⏰ Open-End Binge-Modus: Du wirst bereuen, um 6 Uhr aufstehen zu müssen."
  ]},
  duell:{title:"⚔️ Fernbedienungs-Duell",items:[
    "🏆 Gewinner der Fernbedienung: **Person A (Couch-Chef)**! Keine Wiederrede erlaubt.", 
    "🏆 Gewinner der Fernbedienung: **Person B (Snack-Master)**! Der Chef hat heute Sendepause."
  ]},
  trash:{title:"🎬 B-Movie Plot-Generator",items:[
    "🦈 Ein pensionierter Hai-Züchter kämpft auf dem Mond gegen mutierte Riesen-Bohnen!",
    "👵 Eine cybernetische Oma verteidigt eine Schweizer Disko gegen Weltraum-Piraten auf E-Scootern!",
    "⏰ Ein vergesslicher Zeitreisender landet im Supermarkt und rettet die Kassiererin vor Klonschafen!"
  ]},
  oracle:{title:"🔮 Magisches Film-Orakel",items:[
    "🔮 Ja! Der Film ist ein absolutes Meisterwerk. Unbedingt anmachen.",
    "🔮 Nein, verschwende deine Zeit nicht. Geh lieber früher schlafen.",
    "🔮 Nur, wenn du genug Popcorn und Knabberzeug im Haus hast.",
    "🔮 Die Sterne sagen: Nach 20 Minuten schläfst du auf dem Sofa ein."
  ]}
};
function run(key){
  const d=DATA[key];if(!d)return;
  const pick=d.items[Math.floor(Math.random()*d.items.length)];
  document.getElementById('resTitle').textContent=d.title;
  document.getElementById('resText').innerHTML=pick;
  document.getElementById('resBox').classList.add('on');
}
function hideRes(){document.getElementById('resBox').classList.remove('on');}
</script></body></html>"""

def register(api):
    api.route('index', lambda req: PAGE)
