# -*- coding: utf-8 -*-
"""Filmquiz: zehn Fragen rund ums Kino - mit Fernbedienung und Touch spielbar, Rekord gilt für alle Geräte.

Öffnen: Erweiterungsliste -> Filmquiz -> „Quiz starten“.
Fernbedienung: Pfeiltasten wählen die Antwort, OK bestätigt (oder Zifferntasten 1-4) · Touch: Antwort antippen.
Je schneller die richtige Antwort, desto mehr Punkte (100 bis 150). Eigene Fragen trägst du in den Einstellungen ein:
    Frage; richtige Antwort; falsch 1; falsch 2; falsch 3        (eine Frage pro Zeile)
"""
import random
import threading

EXT_ID = 'quiz'
EXT_NAME = 'Filmquiz'
EXT_DESCRIPTION = 'Filmquiz mit 40 Fragen für Fernbedienung und Touch, eigene Fragen möglich, gemeinsamer Rekord.'
EXT_LINKS = [('Quiz starten', 'index')]
EXT_SETTINGS = [
    {'key': 'anzahl', 'label': 'Fragen pro Runde', 'type': 'number', 'default': 10, 'min': 3, 'max': 30},
    {'key': 'zeit', 'label': 'Sekunden pro Frage', 'type': 'number', 'default': 15, 'min': 5, 'max': 60},
    {'key': 'eigene', 'label': 'Eigene Fragen (eine pro Zeile)', 'type': 'textarea', 'default': '',
     'hint': 'Frage; richtige Antwort; falsch 1; falsch 2; falsch 3   - mindestens eine falsche Antwort.'},
    {'key': 'nur_eigene', 'label': 'Nur eigene Fragen', 'type': 'bool', 'default': False},
]

FRAGEN = [
    ('Wer führte Regie bei „Der Pate“ (1972)?', 'Francis Ford Coppola', 'Martin Scorsese', 'Steven Spielberg', 'Brian De Palma'),
    ('In welchem Film sagt Darth Vader „Ich bin dein Vater“?', 'Das Imperium schlägt zurück', 'Eine neue Hoffnung', 'Die dunkle Bedrohung', 'Das Erwachen der Macht'),
    ('Wer führte Regie bei „Der weiße Hai“?', 'Steven Spielberg', 'George Lucas', 'James Cameron', 'Ridley Scott'),
    ('Wie viele Oscars gewann „Titanic“ (1997)?', '11', '7', '14', '5'),
    ('Wer spielt Captain Jack Sparrow in „Fluch der Karibik“?', 'Johnny Depp', 'Orlando Bloom', 'Brad Pitt', 'Geoffrey Rush'),
    ('Wie heißt der Junge mit der Blitznarbe?', 'Harry Potter', 'Percy Jackson', 'Frodo Beutlin', 'Peter Parker'),
    ('Welches Studio hat „Toy Story“ produziert?', 'Pixar', 'DreamWorks', 'Illumination', 'Studio Ghibli'),
    ('Wie viele Filme hat die Original-Trilogie „Der Herr der Ringe“?', '3', '2', '4', '5'),
    ('Wer spielt die Titelrolle in „Forrest Gump“?', 'Tom Hanks', 'Tom Cruise', 'Kevin Costner', 'Bill Murray'),
    ('Wer führte Regie bei „Pulp Fiction“?', 'Quentin Tarantino', 'Guy Ritchie', 'David Fincher', 'Robert Rodriguez'),
    ('Wie heißt die vergessliche blaue Fischdame in „Findet Nemo“?', 'Dorie', 'Marlin', 'Bruce', 'Gill'),
    ('Wer führte Regie bei „Inception“?', 'Christopher Nolan', 'Denis Villeneuve', 'Ridley Scott', 'Peter Jackson'),
    ('Welcher Schauspieler verkörpert Iron Man im Marvel-Universum?', 'Robert Downey Jr.', 'Chris Evans', 'Chris Hemsworth', 'Mark Ruffalo'),
    ('Wie heißt der graue Zauberer in „Der Herr der Ringe“?', 'Gandalf', 'Saruman', 'Dumbledore', 'Merlin'),
    ('Welches Tier ist Simba im „König der Löwen“?', 'Ein Löwe', 'Ein Tiger', 'Ein Gepard', 'Ein Leopard'),
    ('In welchem Film erlebt Bill Murray jeden Tag denselben Tag?', 'Und täglich grüßt das Murmeltier', 'Zurück in die Zukunft', 'Die Truman Show', 'Edge of Tomorrow'),
    ('In welchem Jahr kam der erste „Star Wars“-Film ins Kino?', '1977', '1969', '1983', '1991'),
    ('Welche Pille nimmt Neo in „Matrix“?', 'Die rote', 'Die blaue', 'Die grüne', 'Die weiße'),
    ('Wer führte Regie bei „Jurassic Park“ (1993)?', 'Steven Spielberg', 'Michael Crichton', 'Robert Zemeckis', 'Tim Burton'),
    ('Wie heißt der beste Freund von Harry Potter mit den roten Haaren?', 'Ron Weasley', 'Draco Malfoy', 'Neville Longbottom', 'Cedric Diggory'),
    ('Was will „E.T.“ am Ende?', 'Nach Hause telefonieren', 'Auf der Erde bleiben', 'Pizza essen', 'Den Präsidenten treffen'),
    ('In welchem Film singt Elsa „Lass jetzt los“?', 'Die Eiskönigin', 'Vaiana', 'Rapunzel', 'Die Schöne und das Biest'),
    ('Wer spielt die Hauptrolle in „Gladiator“ (2000)?', 'Russell Crowe', 'Mel Gibson', 'Brad Pitt', 'Gerard Butler'),
    ('Wer führte Regie bei „Psycho“?', 'Alfred Hitchcock', 'Stanley Kubrick', 'Orson Welles', 'Billy Wilder'),
    ('Wer führte Regie bei „Lola rennt“?', 'Tom Tykwer', 'Wim Wenders', 'Wolfgang Becker', 'Fatih Akin'),
    ('Wer führte Regie bei „Das Boot“?', 'Wolfgang Petersen', 'Roland Emmerich', 'Bernd Eichinger', 'Werner Herzog'),
    ('Wer führte Regie bei „Good Bye, Lenin!“?', 'Wolfgang Becker', 'Tom Tykwer', 'Dominik Graf', 'Caroline Link'),
    ('Welcher deutsche Film gewann 2007 den Auslands-Oscar?', 'Das Leben der Anderen', 'Die Fälscher', 'Nirgendwo in Afrika', 'Der Untergang'),
    ('Welches Auto ist die Zeitmaschine in „Zurück in die Zukunft“?', 'Ein DeLorean', 'Ein Ford Mustang', 'Ein Chevrolet Camaro', 'Ein Porsche 911'),
    ('Wer spielt Kevin in „Kevin - Allein zu Haus“?', 'Macaulay Culkin', 'Haley Joel Osment', 'Elijah Wood', 'Daniel Radcliffe'),
    ('Welchen Don spielt Marlon Brando in „Der Pate“?', 'Vito Corleone', 'Michael Corleone', 'Carlo Rizzi', 'Tom Hagen'),
    ('Wie heißt der Planet in „Avatar“ (2009)?', 'Pandora', 'Tatooine', 'Krypton', 'Arrakis'),
    ('Wie heißt die Heldin in „Die Schöne und das Biest“?', 'Belle', 'Aurora', 'Jasmin', 'Ariel'),
    ('Welche Sportart betreibt „Rocky“?', 'Boxen', 'Ringen', 'Eishockey', 'Football'),
    ('Wer drehte „Chihiros Reise ins Zauberland“?', 'Hayao Miyazaki', 'Makoto Shinkai', 'Mamoru Hosoda', 'Katsuhiro Otomo'),
    ('Wer spielte James Bond in „Casino Royale“ (2006)?', 'Daniel Craig', 'Pierce Brosnan', 'Roger Moore', 'Sean Connery'),
    ('Wer spielte in „Der Schuh des Manitu“ Abahachi und führte Regie?', 'Michael „Bully“ Herbig', 'Til Schweiger', 'Matthias Schweighöfer', 'Christian Ulmen'),
    ('Welches Ereignis steht im Mittelpunkt von „Das Wunder von Bern“?', 'Die Fußball-WM 1954', 'Der Mauerfall', 'Die Olympischen Spiele 1972', 'Die Wiedervereinigung'),
    ('Wer ist Schulleiter von Hogwarts in den ersten Harry-Potter-Filmen?', 'Albus Dumbledore', 'Gandalf', 'Severus Snape', 'Sirius Black'),
    ('Welcher Detektiv wohnt in der Baker Street 221B?', 'Sherlock Holmes', 'Hercule Poirot', 'Miss Marple', 'Philip Marlowe'),
]
_api = None
_lock = threading.Lock()


def eigene(text):
    """Zeilen 'Frage; richtig; falsch 1; ...' -> Liste von Tupeln. Kaputte Zeilen (zu wenig Felder, leer) werden übersprungen."""
    out = []
    for line in str(text or '').splitlines():
        teile = [t.strip() for t in line.split(';')]
        if len(teile) < 3 or not all(teile[:3]):
            continue
        out.append(tuple(t[:160] for t in teile[:5] if t))
    return out


def runde(n, eig=(), nur_eigene=False, rnd=random):
    """n zufällige Fragen mit gemischten Antworten: [{'f', 'a': [...], 'r': Index der richtigen}]."""
    pool = list(eig) if (eig and nur_eigene) else list(FRAGEN) + list(eig)
    rnd.shuffle(pool)
    out = []
    for q in pool[:max(1, n)]:
        a = list(q[1:])
        richtig = a[0]
        rnd.shuffle(a)
        out.append({'f': q[0], 'a': a, 'r': a.index(richtig)})
    return out


PAGE = r"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no"><title>Filmquiz</title>
<style>
:root{--bg:#0f141b;--fg:#e8edf3;--mut:#93a1b3;--card:#18202b;--acc:#4da3ff;--ok:#2e9d62;--bad:#d9534f}
*{box-sizing:border-box}body{margin:0;min-height:100vh;background:var(--bg);color:var(--fg);font:clamp(17px,2.8vmin,30px)/1.4 system-ui,sans-serif;display:flex;justify-content:center;padding:14px;-webkit-user-select:none;user-select:none}
main{width:min(96vw,960px)}header{display:flex;gap:14px;align-items:center;color:var(--mut)}header b{color:var(--fg)}header span:first-child{flex:1}
#bar{height:8px;background:var(--card);border-radius:4px;margin:10px 0;overflow:hidden}#bar i{display:block;height:100%;background:var(--acc);width:100%;transition:width .2s linear}
h1{font-size:1.35em;margin:.6em 0 .8em;min-height:2.6em}
#ans{display:grid;grid-template-columns:1fr 1fr;gap:12px}@media(max-width:560px){#ans{grid-template-columns:1fr}}
button{font:inherit;color:var(--fg);background:var(--card);border:4px solid transparent;border-radius:16px;padding:.9em 1em;text-align:left;cursor:pointer;min-height:3.2em}
button.f{border-color:var(--acc)}button.r{background:var(--ok)}button.w{background:var(--bad)}
#end{display:none;text-align:center;margin-top:8vh}#end b{display:block;font-size:2.4em;color:var(--acc)}#end button{text-align:center;margin-top:1em}
small{color:var(--mut)}
</style></head><body><main>
<header><span id="pr">Frage 0/0</span><span>Punkte: <b id="sc">0</b></span><span id="bs"></span></header>
<div id="bar"><i id="bi"></i></div>
<div id="q"><h1 id="fr"></h1><div id="ans"></div><p><small id="hint">Pfeiltasten + OK, Zifferntasten 1-4 oder antippen</small></p></div>
<div id="end"><h1 id="et"></h1><b id="es"></b><p id="er"></p><button id="again">Nochmal (OK)</button></div>
</main><script>
"use strict";
const $=(s)=>document.querySelector(s);
let Q=[],i=0,score=0,right=0,sel=0,locked=false,t0=0,TIME=15,timer=null,best=null,finished=false;
async function boot(){try{const r=await (await fetch('fragen')).json();Q=r.fragen;TIME=r.zeit||15}catch(e){$('#fr').textContent='Fragen konnten nicht geladen werden.';return}
  try{const b=await (await fetch('punkte')).json();best=b.quiz==null?null:b.quiz}catch(e){}
  $('#bs').textContent=best==null?'':'Rekord: '+best;i=0;score=0;right=0;finished=false;$('#end').style.display='none';$('#q').style.display='block';ask()}
function ask(){if(i>=Q.length)return done();const q=Q[i];locked=false;sel=0;$('#pr').textContent='Frage '+(i+1)+'/'+Q.length;$('#sc').textContent=score;$('#fr').textContent=q.f;
  const a=$('#ans');a.textContent='';q.a.forEach((t,k)=>{const b=document.createElement('button');b.textContent=(k+1)+'  '+t;b.onclick=()=>{sel=k;pick()};a.appendChild(b)});mark();
  t0=Date.now();clearInterval(timer);timer=setInterval(tickBar,100);tickBar()}
function left(){return Math.max(0,TIME-(Date.now()-t0)/1000)}
function tickBar(){const l=left();$('#bi').style.width=(100*l/TIME)+'%';if(l<=0&&!locked){locked=true;clearInterval(timer);reveal(-1)}}
function mark(){document.querySelectorAll('#ans button').forEach((b,k)=>b.classList.toggle('f',k===sel))}
function pick(){if(locked)return;locked=true;clearInterval(timer);const q=Q[i];const ok=sel===q.r;if(ok){score+=100+Math.round(50*left()/TIME);right++}reveal(sel)}
function reveal(k){const q=Q[i],bs=document.querySelectorAll('#ans button');bs[q.r].classList.add('r');if(k>=0&&k!==q.r)bs[k].classList.add('w');$('#sc').textContent=score;
  $('#hint').textContent=k===-1?'Zeit abgelaufen - OK für die nächste Frage':(k===q.r?'Richtig! OK für die nächste Frage':'Leider falsch - OK für die nächste Frage');setTimeout(()=>{if(locked&&!finished&&Q[i]===q)next()},1600)}
function next(){i++;$('#hint').textContent='Pfeiltasten + OK, Zifferntasten 1-4 oder antippen';ask()}
async function done(){finished=true;clearInterval(timer);$('#q').style.display='none';$('#end').style.display='block';$('#et').textContent=right+' von '+Q.length+' richtig';$('#es').textContent=score+' Punkte';
  try{const b=await (await fetch('punkte',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({wert:score})})).json();const neu=best==null||score>best;best=b.quiz;$('#er').textContent=neu?'🏆 Neuer Rekord!':'Rekord: '+best}catch(e){}
  $('#again').classList.add('f')}
document.addEventListener('keydown',e=>{const k=e.key;
  if(finished){if(k==='Enter'||k===' '){e.preventDefault();boot()}return}
  if(k>='1'&&k<='4'&&!locked&&Q[i]&&+k<=Q[i].a.length){sel=+k-1;mark();pick();return}
  if(k==='Enter'||k===' '||k==='Select'){e.preventDefault();if(locked){next_();}else pick();return}
  if(locked)return;const n=Q[i].a.length;
  if(k==='ArrowRight'||k==='ArrowLeft'){e.preventDefault();const t=sel^1;if(t<n)sel=t;mark()}
  else if(k==='ArrowDown'||k==='ArrowUp'){e.preventDefault();const t=(sel+2)%4;if(t<n)sel=t;else sel=(sel+1)%n;mark()}});
function next_(){if(locked&&!finished)next()}
$('#again').onclick=boot;
window.QZ={state:()=>({i,score,right,sel,locked,finished,n:Q.length})};
boot();
</script></body></html>"""


def register(api):
    global _api
    _api = api

    def fragen(req):
        n = int(api.get('anzahl') or 10)
        return {'fragen': runde(n, eigene(api.get('eigene')), bool(api.get('nur_eigene'))), 'zeit': int(api.get('zeit') or 15)}

    def punkte(req):
        if req.method == 'POST':
            d = req.json if isinstance(req.json, dict) else {}
            try:
                wert = int(d.get('wert'))
            except (TypeError, ValueError):
                return ({'error': 'Wert fehlt'}, 400)
            if wert < 0 or wert > 1_000_000:
                return ({'error': 'Ungültiger Wert'}, 400)
            with _lock:
                b = api.get('rekorde', {})
                b = b if isinstance(b, dict) else {}
                if wert > b.get('quiz', -1):
                    b['quiz'] = wert
                    api.set('rekorde', b)
                return b
        b = api.get('rekorde', {})
        return b if isinstance(b, dict) else {}

    def widget():
        b = punkte(type('R', (), {'method': 'GET', 'json': {}})())
        return {'icon': '🎬', 'text': 'Filmquiz', 'sub': ('Rekord: %d Punkte' % b['quiz']) if 'quiz' in b else 'Teste dein Kinowissen'}

    api.route('index', lambda req: PAGE)
    api.route('fragen', fragen)
    api.route('punkte', punkte)
    api.widget('Filmquiz', widget, ttl=60, icon='🎬')
