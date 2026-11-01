# -*- coding: utf-8 -*-
"""Fun Gadgets Suite: Interaktive Couch-Tools, Snack-Picker, B-Movie-Generator und Orakel."""

EXT_ID = 'fun_gadgets'
EXT_NAME = 'Fun Gadgets'
EXT_DESCRIPTION = 'Interaktive Couch-Tools mit Snack-Berater, Binge-Rechner, Fernbedienungs-Duell, B-Movie-Generator und magischem Orakel.'
EXT_LINKS = [('Gadgets öffnen', 'index')]

PAGE = r"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no">
<title>Fun Gadgets</title>
<style>
:root{
  --bg:#0f141b;
  --fg:#e8edf3;
  --mut:#93a1b3;
  --card:#18202b;
  --acc:#ffb703;
  --acc2:#4da3ff
}
*{box-sizing:border-box}
body{
  margin:0;
  min-height:100vh;
  background:var(--bg);
  color:var(--fg);
  font:clamp(13px,1.8vmin,18px)/1.3 system-ui,sans-serif;
  display:flex;
  justify-content:center;
  align-items:center;
  padding:12px
}
main{
  width:min(98vw,1000px);
  display:flex;
  flex-direction:column;
  max-height:96vh
}
header{text-align:center;margin-bottom:10px}
header h1{
  color:var(--acc);
  margin:0 0 2px;
  font-size:1.4em
}
header p{
  color:var(--mut);
  margin:0;
  font-size:.8em
}
.content-layout{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:12px;
  align-items:start;
  overflow:hidden
}
.grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:8px;
  max-height:75vh;
  overflow-y:auto;
  padding-right:4px
}
.card{
  background:var(--card);
  border:2px solid transparent;
  border-radius:10px;
  padding:10px 12px;
  cursor:pointer;
  transition:transform .1s,border-color .1s;
  display:flex;
  flex-direction:column;
  justify-content:center;
  min-height:75px
}
.card:hover,.card:focus{
  border-color:var(--acc2);
  outline:none;
  transform:translateY(-1px)
}
.card h2{
  font-size:.95em;
  margin:0 0 2px;
  color:var(--fg)
}
.card p{
  font-size:.75em;
  color:var(--mut);
  margin:0
}
#resBox{
  background:var(--card);
  border:2px solid var(--acc);
  border-radius:12px;
  padding:16px;
  text-align:center;
  display:flex;
  flex-direction:column;
  justify-content:center;
  align-items:center;
  height:100%;
  min-height:220px
}
#resBox.hidden{display:none}
#resTitle{
  color:var(--acc);
  font-size:1.1em;
  margin-bottom:10px;
  font-weight:bold
}
#resText{
  font-size:.95em;
  margin-bottom:12px;
  line-height:1.5;
  max-height:50vh;
  overflow-y:auto
}
button.close{
  font:inherit;
  background:#2a3350;
  color:var(--fg);
  border:0;
  border-radius:8px;
  padding:.4em 1em;
  cursor:pointer;
  font-size:.85em
}
button.close:active{transform:scale(.97)}
@media(max-width:700px){
  .content-layout{grid-template-columns:1fr}
  .grid{max-height:42vh}
  #resBox{min-height:180px}
}
</style>
</head>
<body>
<main>
<header>
  <h1>🤹 Fun Gadgets</h1>
  <p>Dein Assistent für den perfekten Filmabend auf der Couch</p>
</header>

<div class="content-layout">
  <div class="grid">

    <div class="card" tabindex="0" onclick="run('snack')">
      <div>
        <h2>🍿 Snack & Getränk</h2>
        <p>Was passt zu deinem Filmabend?</p>
      </div>
    </div>

    <div class="card" tabindex="0" onclick="run('binge')">
      <div>
        <h2>⏱️ Binge-Rechner</h2>
        <p>Wann schläfst du heute ein?</p>
      </div>
    </div>

    <div class="card" tabindex="0" onclick="run('duell')">
      <div>
        <h2>⚔️ Fernbedienungs-Duell</h2>
        <p>Wer darf heute aussuchen?</p>
      </div>
    </div>

    <div class="card" tabindex="0" onclick="run('trash')">
      <div>
        <h2>🎬 B-Movie Plot</h2>
        <p>Erstelle absurde Trash-Ideen.</p>
      </div>
    </div>

    <div class="card" tabindex="0" onclick="run('oracle')">
      <div>
        <h2>🔮 Magisches Orakel</h2>
        <p>Soll ich diesen Film gucken?</p>
      </div>
    </div>

  </div>

  <div>
    <div id="resBox" class="hidden">
      <div id="resTitle"></div>
      <div id="resText"></div>
      <button class="close" onclick="hideRes()">Schließen</button>
    </div>
  </div>
</div>
</main>

<script>
"use strict";

const DATA = {

snack:{
title:"🍿 Snack- & Getränke-Empfehlung",
items:[
"🍿 Popcorn! So viel, dass selbst das Sofa neidisch wird.",
"🧀 Nachos mit Käsedip. Kalorien zählen heute nicht, sie schauen mit.",
"🍕 Pizza um Mitternacht. Ernährung ist morgen wieder ein Thema.",
"🍫 Schokolade! Weil Glück manchmal eine quadratische Form hat.",
"🥨 Salzstangen und Gummibärchen. Die perfekte Geschmacksverwirrung.",
"🥤 Eiskalte Cola. Der Treibstoff eines echten Filmfans.",
"🍔 Burger und Pommes. Heute wird nicht gekleckert, heute wird gelebt.",
"🍇 Weintrauben. Damit wenigstens eine Sache gesund aussieht.",
"🌶️ Scharfe Chips. Der Film ist spannend, aber dein Mund noch mehr.",
"🍪 Kekse! Die kleinen Glücklichmacher mit Krümelgarantie.",
"🧋 Milchshake. Kalte Süße für heiße Action.",
"🥜 Erdnüsse. Klein, knusprig und schneller weg als gedacht.",
"🍓 Erdbeeren mit Schokolade. Luxus für den heimischen Kinosaal.",
"🥖 Knoblauchbrot. Danach braucht niemand mehr einen Dialog.",
"🍬 Saure Gummiwürmer. Gesichtsmuskeltraining inklusive.",
"🍟 Pommes! Der offizielle Treibstoff für Serienmarathons.",
"🧁 Muffins. Weil ein Filmabend auch Kuchen verdient.",
"🧊 Eistee mit Eiswürfeln. Erfrischung auf Hollywood-Niveau.",
"🥪 Sandwiches. Für Menschen, die Hunger nicht auf Pause setzen können.",
"🍌 Banane. Der Snack, der behauptet, er wäre vernünftig.",
"🍩 Donuts. Ein Loch im Bauch? Dafür gibt es eine Lösung!",
"🧀 Käsewürfel. Kleine Snacks, große Verantwortung.",
"🍿 Karamellpopcorn. Süß, klebrig und absolut unwiderstehlich.",
"🥛 Kakao. Für gemütliche Filme und nostalgische Gefühle.",
"🌮 Tacos. Heute wird es mexikanisch auf der Couch!",
"🍉 Wassermelone. Sommerfeeling selbst im November.",
"🍫 Schokoriegel. Einmal aufmachen, plötzlich ist die Packung leer.",
"🥨 Laugenbrezel. Tradition trifft Couch-Komfort.",
"🍋 Zitronenlimonade. Sauer macht lustig und wach.",
"🥔 Chips mit Paprika. Der Klassiker unter den Sofa-Sünden.",
"🍦 Eiscreme. Der Film darf warten, das Eis nicht.",
"🧇 Waffeln mit Puderzucker. Frühstück? Nein, Filmabend!",
"🥕 Gemüsesticks mit Dip. Dein Gewissen bekommt einen Snack.",
"🍞 Toast mit Käse. Einfach, schnell und verdammt lecker.",
"🍒 Kirschen. Der elegante Snack für große Filmkritiker.",
"🥤 Mineralwasser. Hydration ist auch im Binge-Modus wichtig.",
"🍰 Käsekuchen. Ein Stück Glück auf einem Teller.",
"🍕 Mini-Pizzen. Klein genug für einen Bissen, gefährlich genug für zwanzig.",
"🍮 Pudding. Der Nachtisch hat jetzt Hauptrollenstatus.",
"🥥 Kokoschips. Urlaubsfeeling ohne Kofferpacken.",
"🍎 Apfel mit Erdnussbutter. Fitnessstudio kann warten.",
"🧇 Waffelröllchen. Knuspern ist ausdrücklich erwünscht.",
"🍓 Fruchtjoghurt. Der gesunde Tarnanzug für Süßigkeiten.",
"🧀 Käsecracker. Knuspern bis zum Abspann.",
"🍫 Schokofondue. Heute wird getunkt statt diskutiert.",
"🥤 Orangensaft. Vitamin C gegen schlechte Filmkritiken.",
"🍿 XXL-Popcorn. Für Filme, die länger dauern als geplant.",
"🍪 Doppelkekse. Einer ist keiner. Zehn sind eine Portion.",
"🍔 Cheeseburger. Der Kühlschrank hat heute Überstunden.",
"🏆 Snack-Meister des Abends: Du! Die Küche erwartet dich."
]},

binge:{
title:"⏱️ Binge-Rechner",
items:[
"⏰ Nur noch eine Folge! Der berühmteste Selbstbetrug der Seriengeschichte.",
"🌙 Schlafenszeit? Dieses Wort wurde heute aus deinem Wörterbuch gestrichen.",
"📺 Du bist jetzt offiziell Bewohner des Serienuniversums.",
"🧟 Deine Augen werden langsam zu Zombie-Augen. Aber die nächste Folge läuft!",
"⏳ Zeit vergeht relativ. Besonders bei Cliffhangern.",
"😴 Dein Kissen vermisst dich. Deine Serie nicht.",
"🚨 Achtung: Morgenfrüh könnte dein Wecker zum Endgegner werden.",
"🍿 Eine Folge noch. Das haben wir alle schon einmal gehört.",
"🕛 Mitternacht? Nur eine Zahl auf deinem Bildschirm.",
"📺 Die Staffel ist fast durch. Deine Vernunft leider auch.",
"🧠 Dein Gehirn speichert gerade unnützes Serienwissen für die Ewigkeit.",
"⚡ Binge-Modus aktiviert. Realität wird vorübergehend pausiert.",
"🌅 Der Sonnenaufgang ist nur der Abspann der Nacht.",
"😎 Du brauchst keinen Schlaf. Du brauchst das Staffelfinale!",
"🛋️ Couch und Serie sind jetzt eine eingetragene Lebensgemeinschaft.",
"🔋 Deine Energieanzeige steht auf 5 Prozent. Die Fernbedienung auf 100.",
"🎬 Der Abspann läuft. Zeit für eine neue Folge!",
"🕰️ Die Uhr lügt. Es können unmöglich schon drei Stunden vergangen sein.",
"💤 Deine Augen blinzeln bereits in Zeitlupe.",
"📡 Schlafmodus nicht gefunden. Bitte später erneut versuchen.",
"🏆 Du hast 5 Folgen geschafft. Deine Couch gratuliert.",
"🚀 Noch eine Staffel und du erreichst den Serien-Olymp.",
"😈 Cliffhanger entdeckt! Schlafen ist jetzt technisch unmöglich.",
"☕ Morgen brauchst du Kaffee. Sehr viel Kaffee.",
"🧛 Du bist jetzt ein Nachtwesen mit WLAN-Verbindung.",
"📺 Die nächste Folge startet automatisch. Das System kennt dich.",
"🌌 Es ist spät. Aber das Universum hat noch 3 Folgen übrig.",
"🛌 Dein Bett hat eine Vermisstenanzeige aufgegeben.",
"🎭 Deine Serie hat mehr Drama als dein gesamter Alltag.",
"⏱️ Zeit für eine Pause? Dein Finger sagt Nein.",
"🤖 Autoplay-Funktion: 1, menschliche Selbstkontrolle: 0.",
"🌙 Die Nacht ist jung. Deine Augen sind alt.",
"📚 Du lernst heute mehr über fiktive Menschen als über echte.",
"🍕 Die nächste Folge braucht Nachschub. Kühlschrank voraus!",
"🔥 Staffelfinale in Sicht! Jetzt bloß nicht einschlafen.",
"😴 Du hast gerade die Handlung verpasst. Zurückspulen!",
"🛸 Du bist nicht müde. Du bist intergalaktisch unterhalten.",
"⚠️ Diese Serie kann zu chronischem Folgenklicken führen.",
"📺 Dein Fernseher fragt, ob du noch da bist. Ja, verdammt!",
"🧙 Die Magie der Serie hält dich wach. Das Kissen wartet.",
"🏃 Deine Schlafroutine hat gerade gekündigt.",
"🎮 Nur noch diese Folge. Danach wirklich. Vielleicht.",
"🌄 Guten Morgen! Du hast gerade versehentlich die Nacht durchgeschaut.",
"💤 Schlaf ist wichtig. Aber was ist mit der Auflösung des Krimis?",
"🧟 Du bist müde, aber die nächste Episode ist hungrig.",
"🕹️ Deine Lebenszeit wird gerade in Episoden umgerechnet.",
"🏅 Binge-Champion! Der Pokal ist ein Kissen mit Augenringen.",
"📺 Serienende? Nicht heute. Heute wird Geschichte geschaut.",
"🚨 Letzte Warnung: Dein Wecker hat bereits Verstärkung gerufen.",
"👑 Du bist der König der Couch. Die Nacht gehört dir!"
]},

duell:{
title:"⚔️ Fernbedienungs-Duell",
items:[
"🏆 Person A gewinnt! Die Fernbedienung gehört jetzt dem Couch-König.",
"👑 Person B regiert! Widerstand ist zwecklos.",
"🤝 Unentschieden! Beide müssen einen Film aussuchen, den keiner kennt.",
"🎲 Das Schicksal entscheidet: Wer zuerst blinzelt, verliert!",
"⚡ Person A gewinnt durch unschlagbare Couch-Aura.",
"🍿 Person B gewinnt. Bestechung durch Snacks war erfolgreich.",
"😂 Niemand gewinnt. Ihr schaut jetzt beide auf den Startbildschirm.",
"🥷 Die Fernbedienung wurde gestohlen. Der Täter sitzt auf dem Sofa.",
"🧠 Quizfrage: Wer kennt mehr Filmzitate? Der Gewinner bestimmt!",
"🪙 Münzwurf! Kopf ist König, Zahl ist Knecht.",
"🏅 Person A gewinnt wegen überlegener Popcorn-Technik.",
"👀 Person B gewinnt. Die Augen waren einfach überzeugender.",
"📺 Die Fernbedienung hat sich selbst zum Chef ernannt.",
"⚔️ Duell! Wer zuerst 'Was schauen wir?' sagt, verliert.",
"😈 Person A hat heimlich schon einen Film gestartet. Clever!",
"🎭 Person B gewinnt durch dramatischen Auftritt.",
"🍕 Wer die Pizza holt, darf heute aussuchen.",
"🥤 Wer das kälteste Getränk besitzt, bekommt die Macht.",
"🛋️ Derjenige mit der gemütlichsten Decke gewinnt.",
"🧙 Das Orakel bestimmt: Person A ist heute Filmminister.",
"🤖 Zufallsgenerator sagt: Person B. Beschwerde zwecklos.",
"🎬 Wer den besseren Filmtitel erfindet, gewinnt.",
"🏴‍☠️ Die Fernbedienung gehört demjenigen, der sie zuerst findet.",
"🔥 Person A gewinnt mit 100 Prozent Couch-Kompetenz.",
"💥 Person B gewinnt durch einen legendären Knopfdruck.",
"🕵️ Wer den letzten Film richtig errät, wird Fernbedienungs-Chef.",
"🏆 Beide gewinnen. Der Fernseher verliert durch Dauerbetrieb.",
"😂 Der Verlierer muss die Snacks nachfüllen.",
"👑 Person A bekommt die Macht. Person B bekommt die Rechnung.",
"⚡ Person B gewinnt im Blitzduell. Keine Revanche!",
"🎲 Noch eine Runde! Das war eindeutig manipuliert.",
"🧀 Derjenige mit dem größten Snack gewinnt automatisch.",
"🧠 Wer zuerst drei Schauspieler aufzählt, gewinnt.",
"🎥 Wer den besseren Filmabend verspricht, bekommt die Fernbedienung.",
"🦖 Person A gewinnt. Dinosaurier sind auf seiner Seite.",
"👽 Außerirdische haben entschieden: Person B!",
"🛑 Stopp! Erst muss der Abspann vom letzten Film geschaut werden.",
"🏅 Person A gewinnt durch legendäre Fernbedienungs-Fingerfertigkeit.",
"🎤 Wer das Filmzitat besser nachmacht, bekommt das Kommando.",
"🍿 Person B gewinnt. Popcorn-Bestechung nicht nachweisbar.",
"⚖️ Das Gericht entscheidet: 50 Prozent Mitbestimmung für jeden.",
"🚀 Person A übernimmt die Kontrolle über das Unterhaltungsraumschiff.",
"🌟 Person B darf wählen. Heute sind die Sterne günstig.",
"🥷 Beide greifen gleichzeitig zu. Fernbedienung im freien Fall!",
"😂 Der Hund oder die Katze darf entscheiden.",
"🧛 Wer länger wach bleibt, bekommt das letzte Wort.",
"🏆 Der Sieger darf aussuchen. Der Verlierer darf nicht meckern.",
"🎬 Person A gewinnt. Der Film ist bereits gestartet.",
"🔮 Das Schicksal spricht: Heute gibt es einen Kompromissfilm.",
"👑 Die Fernbedienung gehört dem Sofa. Ihr seid nur Gäste."
]},

trash:{
title:"🎬 B-Movie Plot-Generator",
items:[
"🦈 Ein pensionierter Hai-Züchter kämpft auf dem Mond gegen mutierte Killer-Bohnen!",
"👵 Eine Cyber-Oma verteidigt eine verlassene Disco gegen Weltraumpiraten auf E-Scootern!",
"🦖 Ninja-Dinosaurier übernehmen das Berliner U-Bahn-Netz!",
"👽 Aliens greifen die Erde an. Ihre einzige Schwäche: lauwarmer Kartoffelsalat!",
"🧟 Ein Zombie-Pirat übernimmt das Homeoffice und fordert mehr Urlaubstage!",
"🚗 Ein sprechender VW Golf rettet das Multiversum mit einem defekten Navigationsgerät!",
"🐙 Ein riesiger Oktopus wird Bürgermeister und verbietet trockene Socken!",
"🧀 Ein mutierter Käseblock entwickelt Weltherrschaftspläne!",
"🛸 Außerirdische landen in Bottrop und werden von einer Pommesbude besiegt!",
"🐔 Killer-Hühner aus dem Weltall greifen einen Campingplatz an!",
"🧙 Ein arbeitsloser Zauberer verwandelt alle Smartphones in Kartoffeln!",
"🦍 Ein Gorilla wird Geheimagent und kämpft gegen die Armee der sprechenden Toaster!",
"🧛 Ein Vampir zieht in eine Wohnung mit Solaranlage. Katastrophe vorprogrammiert!",
"🐌 Eine Riesenschnecke terrorisiert die Autobahn und fordert Mautfreiheit!",
"🤖 Ein Staubsaugerroboter entwickelt Gefühle und übernimmt die Weltherrschaft!",
"🦑 Ein Tintenfisch klaut sämtliche Kugelschreiber der Welt!",
"🛒 Ein Einkaufswagen wird zum Rennwagen und rast durch die Zeit!",
"🧟 Zombies entdecken Rabattaktionen und belagern einen Supermarkt!",
"🐧 Pinguine gründen eine Mafia und kontrollieren sämtliche Tiefkühltruhen!",
"🚀 Ein Astronaut landet auf dem Mars und findet dort einen Dönerladen!",
"🦆 Eine Armee mutierter Enten übernimmt die Weltnachrichten!",
"👾 Ein Videospiel-Bösewicht flüchtet in die reale Welt und bekommt einen Bürojob!",
"🦕 Ein Dinosaurier wird Influencer und zerstört versehentlich das Internet!",
"🍌 Eine Banane entwickelt Superkräfte und bekämpft die böse Obstmafia!",
"🧛 Ein Vampir verliert seine Zähne und muss sich als Zahnarzt durchschlagen!",
"🐈 Eine Katze hackt das Pentagon, weil ihr Futter verspätet geliefert wurde!",
"🧊 Ein Eiswürfel aus der Zukunft will die globale Erwärmung rückgängig machen!",
"🦾 Ein Toaster wird zum Cyborg und erklärt dem Frühstück den Krieg!",
"🐍 Eine Riesenschlange übernimmt eine Gartenzwerg-Fabrik!",
"🎃 Ein Kürbis wird zum Diktator und verbietet Halloween!",
"🦀 Eine Krabbe wird Boxweltmeister und kämpft gegen einen Staubsauger!",
"👨‍🚀 Ein Astronaut entdeckt auf dem Mond eine Filiale der Deutschen Post!",
"🛸 Aliens entführen einen Hausmeister, weil sie seinen Wischmopp für eine Superwaffe halten!",
"🦖 Ein T-Rex wird Busfahrer und verursacht den größten Stau der Erdgeschichte!",
"🐀 Ratten gründen eine Rockband und übernehmen die Musikindustrie!",
"🥔 Eine Kartoffel wird Präsident und verspricht kostenlose Pommes für alle!",
"🧟 Ein Zombie wird Fitnesscoach und trainiert die untoten Olympioniken!",
"🦜 Ein Papagei kennt sämtliche Staatsgeheimnisse und verlangt Lösegeld in Sonnenblumenkernen!",
"🦈 Ein Hai eröffnet eine Zahnarztpraxis für andere Haie!",
"🧙 Eine Hexe verliert ihren Besen und muss auf einem Elektroroller zur Arbeit!",
"🚂 Ein Geisterzug fährt nur noch zu Discountern und sammelt verlorene Einkaufschips!",
"👻 Ein Geist wird Influencer und erschreckt nur noch seine eigenen Follower!",
"🦍 Ein Affe wird Präsident eines intergalaktischen Fitnessstudios!",
"🐉 Ein Drache leidet unter Flugangst und wird Taxifahrer!",
"🪳 Riesenkakerlaken übernehmen ein Luxushotel und verlangen Zimmerservice!",
"🤖 Ein Roboter verliebt sich in eine Mikrowelle und startet eine verbotene Romanze!",
"🧛 Ein Vampir wird Nachtportier und muss sich gegen Sonnenaufgang wehren!",
"🐸 Ein Frosch wird zum König gekrönt und verbietet sämtliche Fliegenfallen!",
"🦉 Eine Eule wird Privatdetektiv und löst den Fall der verschwundenen Fernbedienung!",
"🌭 Eine mutierte Bratwurst übernimmt die Macht über das Universum!"
]},

oracle:{
title:"🔮 Magisches Film-Orakel",
items:[
"🔮 JA! Die Sterne stehen günstig. Mach den Film an!",
"🌑 NEIN! Heute ist dein Sofa stärker als dein Filmgeschmack.",
"✨ Die kosmische Antwort lautet: Absolut sehenswert!",
"🧙 Nur wenn du vorher genügend Snacks geopfert hast.",
"🌟 Das Universum empfiehlt eine Komödie. Lachen ist heute Pflicht!",
"👻 Die Geister sagen Ja. Aber lass das Licht an!",
"⚡ Ein klares JA! Die Fernbedienung zittert bereits vor Vorfreude.",
"🌧️ Nein. Heute ist ein Abend für Decke, Tee und Nichtstun.",
"🪄 Vielleicht. Wirf eine Münze und vertraue dem Zufall.",
"🔮 Ich sehe Popcorn in deiner Zukunft. Der Film ist zweitrangig.",
"🌌 Die Sterne flüstern: Dieser Film könnte dich überraschen.",
"😴 Nein. Dein Kissen hat andere Pläne mit dir.",
"🎬 JA! Dieser Film wurde vom Schicksal persönlich ausgewählt.",
"👽 Die Außerirdischen empfehlen ihn. Sie haben schließlich Geschmack.",
"🧠 Dein Bauchgefühl sagt Ja. Dein Verstand soll heute Urlaub machen.",
"🔥 Nur ansehen, wenn du bereit für absolute Begeisterung bist!",
"🕰️ Nicht jetzt. Der richtige Film kommt noch.",
"🎭 Das Orakel sieht Drama. Sehr viel Drama!",
"🍿 JA! Aber ohne Snacks wird das Schicksal ungemütlich.",
"💤 Die Antwort lautet Nein. Du bist bereits halb eingeschlafen.",
"🌠 Ein seltenes Zeichen: Heute passt einfach alles!",
"🧛 Nur nach Sonnenuntergang. Das Orakel ist ein Vampir.",
"🌀 Die Zeitlinien sind unklar. Versuch es mit einer Komödie.",
"👑 JA! Du bist bereit für einen königlichen Filmabend.",
"🦖 Nein! Heute brauchst du etwas ohne Dinosaurier.",
"💫 Die Magie sagt: Lass dich einfach überraschen.",
"🚀 JA! Anschnallen, der Filmabend hebt gleich ab!",
"🧩 Dieser Film wird Fragen aufwerfen. Viele Fragen.",
"🌙 Die Nacht ist jung. Das Orakel sagt Ja!",
"⚖️ 50 Prozent Ja, 50 Prozent Nein. Also eindeutig vielleicht.",
"🔔 Das Schicksal hat geklingelt. Es bringt einen guten Film mit.",
"🪐 Auf einem anderen Planeten wäre das ein Meisterwerk. Hier auch!",
"👀 Ich sehe eine Wendung, die du nicht kommen sehen wirst.",
"🧙 Die Filmgeister empfehlen: Heute lieber etwas Lustiges.",
"💥 JA! Explosionen, Spannung und Couch-Komfort erwarten dich.",
"🕯️ NEIN! Der Film hat eine dunkle Aura. Vielleicht morgen.",
"🎲 Das Orakel würfelt eine Sechs. Film starten!",
"🌈 Dein Abend wird großartig. Dieser Film könnte helfen.",
"🛋️ Dein Sofa sagt Ja. Und das Sofa hat immer recht.",
"😈 Das Orakel sagt Ja. Deine Schlafenszeit sagt Nein.",
"🦉 Weisheit des Tages: Ein schlechter Film ist eine gute Geschichte.",
"🔮 Die Zukunft ist verschwommen. Aber Popcorn ist deutlich sichtbar.",
"🌟 Heute ist ein perfekter Tag für einen Klassiker.",
"🎥 Das Orakel verlangt einen Film mit mindestens einer Explosion.",
"💀 NEIN! Dieser Film könnte deine Geduld auf die Probe stellen.",
"🏆 JA! Das könnte der beste Film des Abends werden.",
"🤖 Berechnung abgeschlossen: Unterhaltung dringend empfohlen!",
"🌌 Die Galaxie stimmt zu. Film ab!",
"🍀 Glückstag! Selbst ein zufälliger Film wird heute gut.",
"👑 Das letzte Wort hat das Orakel. Und das lautet: ANMACHEN!"
]}

};

function run(key){
  const d=DATA[key];
  if(!d)return;

  const pick=d.items[Math.floor(Math.random()*d.items.length)];

  document.getElementById('resTitle').textContent=d.title;
  document.getElementById('resText').textContent=pick;
  document.getElementById('resBox').classList.remove('hidden');
}

function hideRes(){
  document.getElementById('resBox').classList.add('hidden');
}

// Auch die Enter-Taste und Leertaste funktionieren auf den Gadget-Kacheln.
document.querySelectorAll('.card').forEach(card=>{
  card.addEventListener('keydown',event=>{
    if(event.key==='Enter'||event.key===' '){
      event.preventDefault();
      card.click();
    }
  });
});
</script>
</body>
</html>"""


def widget(req):
    return {
        'title': 'Fun Gadgets',
        'content': 'Fünf interaktive Couch-Gadgets mit 250 lustigen Sprüchen.'
    }


def register(api):
    api.widget('Fun Gadgets', widget, ttl=3600, icon='🤹‍♀️')
    api.route('index', lambda req: PAGE)
