# -*- coding: utf-8 -*-
# Filmquiz
# IT('s) Possible 
# 2026.11.08
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

FILM_WISSEN = [
('Der Pate','Francis Ford Coppola','Marlon Brando',1972,'Drama'),
('Der Pate II','Francis Ford Coppola','Al Pacino',1974,'Drama'),
('Apocalypse Now','Francis Ford Coppola','Martin Sheen',1979,'Kriegsfilm'),
('Taxi Driver','Martin Scorsese','Robert De Niro',1976,'Drama'),
('GoodFellas','Martin Scorsese','Ray Liotta',1990,'Krimi'),
('The Wolf of Wall Street','Martin Scorsese','Leonardo DiCaprio',2013,'Komödie'),
('Departed – Unter Feinden','Martin Scorsese','Leonardo DiCaprio',2006,'Thriller'),
('Pulp Fiction','Quentin Tarantino','John Travolta',1994,'Krimi'),
('Kill Bill','Quentin Tarantino','Uma Thurman',2003,'Action'),
('Django Unchained','Quentin Tarantino','Jamie Foxx',2012,'Western'),
('Inglourious Basterds','Quentin Tarantino','Christoph Waltz',2009,'Kriegsfilm'),
('Reservoir Dogs','Quentin Tarantino','Harvey Keitel',1992,'Krimi'),
('Der weiße Hai','Steven Spielberg','Roy Scheider',1975,'Thriller'),
('E.T. – Der Außerirdische','Steven Spielberg','Henry Thomas',1982,'Science-Fiction'),
('Schindlers Liste','Steven Spielberg','Liam Neeson',1993,'Drama'),
('Jurassic Park','Steven Spielberg','Sam Neill',1993,'Abenteuer'),
('Indiana Jones','Steven Spielberg','Harrison Ford',1981,'Abenteuer'),
('Der Soldat James Ryan','Steven Spielberg','Tom Hanks',1998,'Kriegsfilm'),
('Catch Me If You Can','Steven Spielberg','Leonardo DiCaprio',2002,'Krimi'),
('Zurück in die Zukunft','Robert Zemeckis','Michael J. Fox',1985,'Science-Fiction'),
('Forrest Gump','Robert Zemeckis','Tom Hanks',1994,'Drama'),
('Cast Away','Robert Zemeckis','Tom Hanks',2000,'Abenteuer'),
('Titanic','James Cameron','Leonardo DiCaprio',1997,'Drama'),
('Avatar – Aufbruch nach Pandora','James Cameron','Sam Worthington',2009,'Science-Fiction'),
('Terminator','James Cameron','Arnold Schwarzenegger',1984,'Science-Fiction'),
('Terminator 2','James Cameron','Arnold Schwarzenegger',1991,'Action'),
('Aliens – Die Rückkehr','James Cameron','Sigourney Weaver',1986,'Science-Fiction'),
('The Dark Knight','Christopher Nolan','Christian Bale',2008,'Action'),
('Inception','Christopher Nolan','Leonardo DiCaprio',2010,'Science-Fiction'),
('Interstellar','Christopher Nolan','Matthew McConaughey',2014,'Science-Fiction'),
('Oppenheimer','Christopher Nolan','Cillian Murphy',2023,'Drama'),
('Memento','Christopher Nolan','Guy Pearce',2000,'Thriller'),
('Dunkirk','Christopher Nolan','Fionn Whitehead',2017,'Kriegsfilm'),
('Gladiator','Ridley Scott','Russell Crowe',2000,'Action'),
('Alien','Ridley Scott','Sigourney Weaver',1979,'Science-Fiction'),
('Blade Runner','Ridley Scott','Harrison Ford',1982,'Science-Fiction'),
('Der Marsianer','Ridley Scott','Matt Damon',2015,'Science-Fiction'),
('Black Hawk Down','Ridley Scott','Josh Hartnett',2001,'Kriegsfilm'),
('Thelma & Louise','Ridley Scott','Geena Davis',1991,'Drama'),
('Mad Max','George Miller','Mel Gibson',1979,'Action'),
('Mad Max: Fury Road','George Miller','Tom Hardy',2015,'Action'),
('Matrix','Lana und Lilly Wachowski','Keanu Reeves',1999,'Science-Fiction'),
('Cloud Atlas','Lana und Lilly Wachowski','Tom Hanks',2012,'Science-Fiction'),
('V wie Vendetta','James McTeigue','Natalie Portman',2005,'Action'),
('Fight Club','David Fincher','Brad Pitt',1999,'Thriller'),
('Sieben','David Fincher','Morgan Freeman',1995,'Thriller'),
('The Social Network','David Fincher','Jesse Eisenberg',2010,'Drama'),
('Gone Girl','David Fincher','Ben Affleck',2014,'Thriller'),
('Zodiac','David Fincher','Jake Gyllenhaal',2007,'Krimi'),
('The Revenant','Alejandro González Iñárritu','Leonardo DiCaprio',2015,'Abenteuer'),
('Birdman','Alejandro González Iñárritu','Michael Keaton',2014,'Drama'),
('Babel','Alejandro González Iñárritu','Brad Pitt',2006,'Drama'),
('Gravity','Alfonso Cuarón','Sandra Bullock',2013,'Science-Fiction'),
('Harry Potter und der Stein der Weisen','Chris Columbus','Daniel Radcliffe',2001,'Fantasy'),
('Harry Potter und die Kammer des Schreckens','Chris Columbus','Daniel Radcliffe',2002,'Fantasy'),
('Harry Potter und der Gefangene von Askaban','Alfonso Cuarón','Daniel Radcliffe',2004,'Fantasy'),
('Harry Potter und der Feuerkelch','Mike Newell','Daniel Radcliffe',2005,'Fantasy'),
('Harry Potter und der Orden des Phönix','David Yates','Daniel Radcliffe',2007,'Fantasy'),
('Harry Potter und die Heiligtümer des Todes 2','David Yates','Daniel Radcliffe',2011,'Fantasy'),
('Der Herr der Ringe: Die Gefährten','Peter Jackson','Elijah Wood',2001,'Fantasy'),
('Der Herr der Ringe: Die zwei Türme','Peter Jackson','Elijah Wood',2002,'Fantasy'),
('Der Herr der Ringe: Die Rückkehr des Königs','Peter Jackson','Elijah Wood',2003,'Fantasy'),
('Der Hobbit: Eine unerwartete Reise','Peter Jackson','Martin Freeman',2012,'Fantasy'),
('King Kong','Peter Jackson','Naomi Watts',2005,'Abenteuer'),
('Braindead','Peter Jackson','Timothy Balme',1992,'Horror'),
('Fluch der Karibik','Gore Verbinski','Johnny Depp',2003,'Abenteuer'),
('Rango','Gore Verbinski','Johnny Depp',2011,'Animation'),
('The Ring','Gore Verbinski','Naomi Watts',2002,'Horror'),
('Pirates of the Caribbean 2','Gore Verbinski','Johnny Depp',2006,'Abenteuer'),
('Iron Man','Jon Favreau','Robert Downey Jr.',2008,'Action'),
('The Jungle Book','Jon Favreau','Neel Sethi',2016,'Abenteuer'),
('Avengers: Endgame','Anthony und Joe Russo','Robert Downey Jr.',2019,'Action'),
('Avengers: Infinity War','Anthony und Joe Russo','Robert Downey Jr.',2018,'Action'),
('Captain America: The Winter Soldier','Anthony und Joe Russo','Chris Evans',2014,'Action'),
('Guardians of the Galaxy','James Gunn','Chris Pratt',2014,'Science-Fiction'),
('The Suicide Squad','James Gunn','Margot Robbie',2021,'Action'),
('Superman','Richard Donner','Christopher Reeve',1978,'Action'),
('Batman','Tim Burton','Michael Keaton',1989,'Action'),
('Batman Begins','Christopher Nolan','Christian Bale',2005,'Action'),
('Joker','Todd Phillips','Joaquin Phoenix',2019,'Drama'),
('Wonder Woman','Patty Jenkins','Gal Gadot',2017,'Action'),
('Spider-Man','Sam Raimi','Tobey Maguire',2002,'Action'),
('Spider-Man: No Way Home','Jon Watts','Tom Holland',2021,'Action'),
('Deadpool','Tim Miller','Ryan Reynolds',2016,'Action'),
('Logan','James Mangold','Hugh Jackman',2017,'Action'),
('X-Men','Bryan Singer','Hugh Jackman',2000,'Science-Fiction'),
('The Sixth Sense','M. Night Shyamalan','Bruce Willis',1999,'Thriller'),
('Signs','M. Night Shyamalan','Mel Gibson',2002,'Science-Fiction'),
('The Village','M. Night Shyamalan','Bryce Dallas Howard',2004,'Thriller'),
('Unbreakable','M. Night Shyamalan','Bruce Willis',2000,'Thriller'),
('The Truman Show','Peter Weir','Jim Carrey',1998,'Drama'),
('Die Truman Show','Peter Weir','Jim Carrey',1998,'Drama'),
('Der Club der toten Dichter','Peter Weir','Robin Williams',1989,'Drama'),
('Rain Man','Barry Levinson','Dustin Hoffman',1988,'Drama'),
('Good Morning, Vietnam','Barry Levinson','Robin Williams',1987,'Komödie'),
('Mrs. Doubtfire','Chris Columbus','Robin Williams',1993,'Komödie'),
('Kevin – Allein zu Haus','Chris Columbus','Macaulay Culkin',1990,'Komödie'),
('Harry und Sally','Rob Reiner','Billy Crystal',1989,'Komödie'),
('Stand by Me','Rob Reiner','River Phoenix',1986,'Drama'),
('Eine Frage der Ehre','Rob Reiner','Tom Cruise',1992,'Drama'),
('Pretty Woman','Garry Marshall','Julia Roberts',1990,'Romanze'),
('Notting Hill','Roger Michell','Hugh Grant',1999,'Romanze'),
('Tatsächlich... Liebe','Richard Curtis','Hugh Grant',2003,'Romanze'),
('Vier Hochzeiten und ein Todesfall','Mike Newell','Hugh Grant',1994,'Komödie'),
('Bridget Jones – Schokolade zum Frühstück','Sharon Maguire','Renée Zellweger',2001,'Komödie'),
('Mamma Mia!','Phyllida Lloyd','Meryl Streep',2008,'Musical'),
('La La Land','Damien Chazelle','Ryan Gosling',2016,'Musical'),
('Whiplash','Damien Chazelle','Miles Teller',2014,'Drama'),
('The Greatest Showman','Michael Gracey','Hugh Jackman',2017,'Musical'),
('Bohemian Rhapsody','Bryan Singer','Rami Malek',2018,'Drama'),
('Elvis','Baz Luhrmann','Austin Butler',2022,'Drama'),
('Moulin Rouge!','Baz Luhrmann','Nicole Kidman',2001,'Musical'),
('Romeo + Julia','Baz Luhrmann','Leonardo DiCaprio',1996,'Romanze'),
('Der Schuh des Manitu','Michael Herbig','Michael Herbig',2001,'Komödie'),
('(T)Raumschiff Surprise','Michael Herbig','Michael Herbig',2004,'Komödie'),
('Keinohrhasen','Til Schweiger','Til Schweiger',2007,'Komödie'),
('Honig im Kopf','Til Schweiger','Dieter Hallervorden',2014,'Drama'),
('Fack ju Göhte','Bora Dagtekin','Elyas M Barek',2013,'Komödie'),
('Türkisch für Anfänger','Bora Dagtekin','Josefine Preuß',2012,'Komödie'),
('Das Leben der Anderen','Florian Henckel von Donnersmarck','Ulrich Mühe',2006,'Drama'),
('Der Untergang','Oliver Hirschbiegel','Bruno Ganz',2004,'Drama'),
('Lola rennt','Tom Tykwer','Franka Potente',1998,'Thriller'),
('Good Bye, Lenin!','Wolfgang Becker','Daniel Brühl',2003,'Komödie'),
('Das Boot','Wolfgang Petersen','Jürgen Prochnow',1981,'Kriegsfilm'),
('Die Welle','Dennis Gansel','Jürgen Vogel',2008,'Drama'),
('Who Am I – Kein System ist sicher','Baran bo Odar','Tom Schilling',2014,'Thriller'),
('Das Wunder von Bern','Sönke Wortmann','Louis Klamroth',2003,'Drama'),
('Metropolis','Fritz Lang','Brigitte Helm',1927,'Science-Fiction'),
('Nosferatu','F. W. Murnau','Max Schreck',1922,'Horror'),
('Das Cabinet des Dr. Caligari','Robert Wiene','Werner Krauss',1920,'Horror'),
('Die Feuerzangenbowle','Helmut Weiss','Heinz Rühmann',1944,'Komödie'),
('Pappa ante Portas','Vicco von Bülow','Loriot',1991,'Komödie'),
('Ödipussi','Vicco von Bülow','Loriot',1988,'Komödie'),
]

def _filmfragen():
    """Erzeugt vier unterschiedliche Wissensfragen pro Film."""
    felder = [
        ('Wer führte bei „%s“ Regie?', 1),
        ('Wer spielt die Hauptrolle in „%s“?', 2),
        ('In welchem Jahr erschien „%s“?', 3),
        ('Welches Genre hat „%s“?', 4),
    ]
    pools = [
        sorted(set(x[1] for x in FILM_WISSEN)),
        sorted(set(x[2] for x in FILM_WISSEN)),
        sorted(set(str(x[3]) for x in FILM_WISSEN)),
        sorted(set(x[4] for x in FILM_WISSEN)),
    ]
    fragen = []
    for film in FILM_WISSEN:
        titel = film[0]
        for frage, feld in felder:
            richtig = str(film[feld])
            pool = [x for x in pools[feld - 1] if x != richtig]
            falsch = random.sample(pool, 3)
            fragen.append((frage % titel, richtig, falsch[0], falsch[1], falsch[2]))
    return fragen


FRAGEN.extend(_filmfragen())
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
