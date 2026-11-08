# -*- coding: utf-8 -*-
# MovieGotchi
# IT('s) Possible 
# 2026.11.08
"""MovieGotchi: Dein virtuelles Haustier für MovieScout."""

EXT_ID = 'moviegotchi'
EXT_NAME = 'MovieGotchi'
EXT_DESCRIPTION = 'Kümmere dich um dein eigenes virtuelles Haustier im Tamagotchi-Stil.'
EXT_LINKS = [('MovieGotchi', 'index')]
EXT_SETTINGS = []

_api = None


def register(api):
    global _api
    _api = api

    def seite(req):
        return r'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<meta name="theme-color" content="#101827">
<title>MovieGotchi</title>

<style>
*{box-sizing:border-box}
html,body{
    height:100%;
    margin:0;
    overflow:hidden;
    background:radial-gradient(ellipse at top,#263b58,#101827 65%);
    color:#f4f7fb;
    font-family:system-ui,Arial,sans-serif;
}
button,input{font:inherit}
button{
    border:0;
    border-radius:8px;
    padding:6px 8px;
    background:#30445f;
    color:white;
    font-weight:700;
    cursor:pointer;
    touch-action:manipulation;
}
button:active{transform:scale(.97)}
button:disabled{opacity:.35}

.app{
    max-width:700px;
    height:100%;
    margin:auto;
    padding:6px 10px;
    display:flex;
    flex-direction:column;
    justify-content:space-between;
    gap:4px;
}

.top{display:flex;justify-content:space-between;align-items:center;flex-shrink:0}
.brand{font-size:16px;font-weight:900}
.brand span{color:#ffd166}
.coins{
    background:#2a3548;
    border:1px solid #46536a;
    border-radius:15px;
    padding:2px 8px;
    color:#ffd166;
    font-weight:900;
    font-size:12px;
}

.card{
    background:linear-gradient(145deg,#202f45,#172335);
    border:1px solid #34445d;
    border-radius:10px;
    padding:6px 10px;
    flex-shrink:0;
}

.pet-card{text-align:center;position:relative;overflow:hidden}
.pet-card::before{
    content:"";
    position:absolute;
    inset:0 0 auto;
    height:3px;
    background:linear-gradient(90deg,#64b5f6,#65d69a,#ffd166,#ff8fab);
}
.pet-name{font-size:15px;font-weight:900;margin:0}
.stage{font-size:10px;color:#aab8ca}
.pet-scene{
    height:70px;
    display:flex;
    align-items:center;
    justify-content:center;
    position:relative;
    background:radial-gradient(ellipse at 50% 80%,#395273,transparent 55%);
    margin-top:2px;
}
.pet{
    font-size:48px;
    animation:bob 2.4s ease-in-out infinite;
}
@keyframes bob{
    0%,100%{transform:translateY(0) rotate(-2deg)}
    50%{transform:translateY(-3px) rotate(2deg)}
}
.bubble{
    position:absolute;
    top:4px;
    right:4px;
    background:white;
    color:#23334a;
    border-radius:10px;
    padding:2px 6px;
    font-size:10px;
    font-weight:800;
}
.notice{font-size:10px;color:#aab8ca;margin-top:1px}
.section-title{font-size:11px;font-weight:900;margin:0 0 4px}

.status{
    display:grid;
    grid-template-columns:repeat(3,minmax(0,1fr));
    gap:4px;
}
.stat{background:#111d2c;border-radius:8px;padding:4px 6px}
.stat-head{
    display:flex;
    justify-content:space-between;
    font-size:10px;
    color:#aab8ca;
    margin-bottom:2px;
}
.stat-head b{color:white}
.bar{height:4px;background:#34445a;border-radius:6px;overflow:hidden}
.fill{height:100%;border-radius:6px}
.gold{background:linear-gradient(90deg,#e6a83a,#ffe18b)}
.pink{background:linear-gradient(90deg,#dc6d9a,#ffb0c9)}
.blue{background:linear-gradient(90deg,#438fe0,#7ac8ff)}
.red{background:linear-gradient(90deg,#d84f5b,#ff9292)}

.inventory{
    display:flex;
    justify-content:center;
    gap:12px;
    margin-top:5px;
    padding-top:4px;
    border-top:1px solid #34445d;
    font-size:10px;
    color:#c3d0df;
}
.inventory b{color:#ffd166}

.actions{
    display:grid;
    grid-template-columns:repeat(6,minmax(0,1fr));
    gap:4px;
}
.action{
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    gap:1px;
    background:#263951;
    border:1px solid #3c526e;
    padding:4px 2px;
    border-radius:8px;
}
.action .emoji{font-size:16px}
.action small{font-size:8px;color:#c3d0df}
.action.primary{background:linear-gradient(145deg,#285c75,#234b68)}

.tabs{display:flex;gap:4px;flex-shrink:0}
.tab{
    flex:1;
    padding:4px;
    font-size:10px;
    background:#1c2a3d;
    color:#aab8ca;
    border-radius:8px;
    border:none;
    cursor:pointer;
    text-align:center;
}
.tab.active{background:#355271;color:white}

.panel{display:none}
.panel.active{display:block}

.shop-grid{
    display:grid;
    grid-template-columns:repeat(2,minmax(0,1fr));
    gap:4px;
}
.shop-item{
    background:#142235;
    border:1px solid #34445d;
    border-radius:8px;
    padding:4px 6px;
    display:flex;
    align-items:center;
    gap:4px;
}
.shop-item .emoji{font-size:16px}
.shop-item div{flex:1;min-width:0}
.shop-item b{display:block;font-size:10px}
.shop-item small{font-size:9px;color:#aab8ca}
.shop-item button{padding:2px 6px;font-size:9px}

.log{
    font-size:10px;
    color:#aab8ca;
    max-height:45px;
    overflow:auto;
}
.log div{border-bottom:1px solid rgba(255,255,255,0.05);padding:1px 0}

.rename{display:flex;gap:4px}
.rename input{
    flex:1;
    min-width:0;
    background:#111d2c;
    color:white;
    border:1px solid #42536a;
    border-radius:8px;
    padding:4px 6px;
    font-size:11px;
}

.footer{text-align:center;color:#71839a;font-size:9px;flex-shrink:0}

.overlay{
    position:fixed;
    inset:0;
    background:rgba(8,14,24,0.85);
    display:none;
    align-items:center;
    justify-content:center;
    padding:10px;
    z-index:5;
}
.overlay.show{display:flex}
.dialog{
    width:min(280px,100%);
    background:#1d2b40;
    border:1px solid #50617a;
    border-radius:12px;
    padding:10px;
    text-align:center;
}
.dialog .big{font-size:35px}
.dialog h2{margin:2px 0;font-size:14px}
.dialog p{color:#aab8ca;font-size:10px;margin:4px 0}

@media(max-height:600px){
    .app{gap:2px;padding:3px 8px}
    .pet-scene{height:48px}
    .pet{font-size:38px}
    .card{padding:4px 8px}
    .section-title{margin-bottom:2px}
    .action{padding:2px}
    .action .emoji{font-size:14px}
}
</style>
</head>

<body>
<div class="app">

<header class="top">
    <div class="brand">🍿 Movie<span>Gotchi</span></div>
    <div class="coins">🪙 <span id="coins">20</span></div>
</header>

<section class="card pet-card">
    <div class="pet-name" id="petName">Mochi</div>
    <div class="stage" id="stage">Ei · Tag 1</div>
    <div class="pet-scene">
        <div class="bubble" id="bubble">Hi!</div>
        <div class="pet" id="pet">🥚</div>
    </div>
    <div class="notice" id="petMood">Ich fühle mich wohl!</div>
</section>

<section class="card">
    <h3 class="section-title">Zustand</h3>
    <div class="status" id="stats"></div>
    <div class="inventory">
        <span>🍎 Futter: <b id="foodCount">2</b></span>
        <span>💊 Medizin: <b id="medicineCount">1</b></span>
    </div>
</section>

<section class="card">
    <h3 class="section-title">Aktionen</h3>
    <div class="actions">
        <button class="action primary" data-action="feed"><span class="emoji">🍎</span>Füttern<small>Sättigung</small></button>
        <button class="action" data-action="play"><span class="emoji">🎾</span>Spielen<small>Freude</small></button>
        <button class="action" data-action="clean"><span class="emoji">🧼</span>Putzen<small>Sauber</small></button>
        <button class="action" data-action="medicine"><span class="emoji">💊</span>Medizin<small>Gesund</small></button>
        <button class="action" data-action="sleep"><span class="emoji">🌙</span>Schlafen<small>Energie</small></button>
        <button class="action" data-action="love"><span class="emoji">❤️</span>Kuscheln<small>Zuneig.</small></button>
    </div>
</section>

<div class="tabs">
    <button class="tab active" data-tab="home">🏠 Zuhause</button>
    <button class="tab" data-tab="shop">🛍️ Laden</button>
    <button class="tab" data-tab="profile">📋 Profil</button>
</div>

<section class="card panel active" id="panel-home">
    <h3 class="section-title">Protokoll</h3>
    <div class="log" id="log"></div>
</section>

<section class="card panel" id="panel-shop">
    <h3 class="section-title">Laden</h3>
    <div class="shop-grid" id="shop"></div>
</section>

<section class="card panel" id="panel-profile">
    <h3 class="section-title">Profil & Neustart</h3>
    <div class="rename">
        <input id="nameInput" maxlength="16" placeholder="Neuer Name">
        <button id="renameBtn">Ändern</button>
    </div>
    <button id="resetBtn" style="background:#663b48;margin-top:4px;width:100%;padding:4px;font-size:11px;">Neues Ei starten</button>
</section>

<div class="footer">MovieGotchi</div>
</div>

<div class="overlay" id="overlay">
    <div class="dialog">
        <div class="big" id="dialogEmoji">🥚</div>
        <h2 id="dialogTitle">MovieGotchi</h2>
        <p id="dialogText"></p>
        <button id="dialogOk" style="width:100%;margin-top:6px;padding:4px;font-size:11px;">Weiter</button>
    </div>
</div>

<script>
(function(){
'use strict';

const KEY='moviescout_moviegotchi_v3';

const defaults=()=>({
    name:'Mochi',
    age:0,
    coins:20,
    hunger:82,
    happy:85,
    health:100,
    clean:90,
    energy:90,
    affection:65,
    sleeping:false,
    dead:false,
    last:Date.now(),
    inventory:{food:2,medicine:1},
    log:['Dein Ei ist geschlüpft!']
});

let state;

try{
    state=JSON.parse(localStorage.getItem(KEY))||defaults();
}catch(e){
    state=defaults();
}

function normalizeState(){
    const d=defaults();

    if(!state||typeof state!=='object'||Array.isArray(state)){
        state=d;
    }

    Object.keys(d).forEach(k=>{
        if(state[k]===undefined)state[k]=d[k];
    });

    if(!state.inventory||typeof state.inventory!=='object'){
        state.inventory={food:2,medicine:1};
    }

    if(!Array.isArray(state.log))state.log=[];
    if(typeof state.name!=='string')state.name='Mochi';

    ['age','coins','hunger','happy','health','clean','energy','affection'].forEach(k=>{
        const n=Number(state[k]);
        state[k]=Number.isFinite(n)?n:d[k];
    });

    state.age=Math.max(0,state.age);
    state.coins=Math.max(0,Math.floor(state.coins));

    state.inventory.food=Math.max(0,Math.floor(Number(state.inventory.food)||0));
    state.inventory.medicine=Math.max(0,Math.floor(Number(state.inventory.medicine)||0));

    ['hunger','happy','health','clean','energy','affection'].forEach(k=>{
        state[k]=clamp(state[k]);
    });

    state.last=Number(state.last);
    if(!Number.isFinite(state.last)||state.last<=0){
        state.last=Date.now();
    }

    state.sleeping=!!state.sleeping;
    state.dead=!!state.dead;

    state.name=state.name.trim().slice(0,16)||'Mochi';
    state.log=state.log.slice(0,4);
}

function clamp(n){
    return Math.max(0,Math.min(100,Number(n)||0));
}

function save(){
    try{
        localStorage.setItem(KEY,JSON.stringify(state));
    }catch(e){}
}

function addLog(s){
    state.log.unshift(
        new Date().toLocaleTimeString('de-DE',{
            hour:'2-digit',
            minute:'2-digit'
        })+' – '+s
    );

    state.log=state.log.slice(0,4);
}

function stageInfo(){
    if(state.age<1)return {name:'Ei',emoji:'🥚'};
    if(state.age<2)return {name:'Baby',emoji:'🐣'};
    if(state.age<5)return {name:'Kind',emoji:'🐤'};
    if(state.age<10)return {name:'Teenager',emoji:'🐥'};
    return {name:'Erwachsen',emoji:'🐱'};
}

/*
 * Spielzeit:
 * 1 Stunde = 4 Simulationsschritte zu je 15 Minuten.
 * Dadurch werden auch kleine Änderungen exakt gespeichert.
 */
function simulate(hours){
    const steps=Math.max(1,Math.ceil(hours*4));
    const step=hours/steps;

    for(let i=0;i<steps;i++){
        if(state.dead)break;

        state.age+=step/24;

        // Grundversorgung
        state.hunger=clamp(state.hunger-step*2.5);
        state.happy=clamp(state.happy-step*1.0);
        state.clean=clamp(state.clean-step*1.2);
        state.affection=clamp(state.affection-step*0.5);

        // Energie abhängig vom Schlafzustand
        if(state.sleeping){
            state.energy=clamp(state.energy+step*15);
        }else{
            state.energy=clamp(state.energy-step*2);
        }

        // Kritische Versorgung belastet die Gesundheit.
        let critical=0;

        if(state.hunger<12)critical++;
        if(state.clean<8)critical++;
        if(state.energy<5)critical++;
        if(state.happy<5)critical++;

        if(critical>=2){
            state.health=clamp(state.health-step*3);
        }else if(critical===1){
            state.health=clamp(state.health-step*1.5);
        }else if(
            state.hunger>40&&
            state.clean>35&&
            state.energy>25&&
            state.happy>30
        ){
            // Bei guter Pflege erholt sich die Gesundheit langsam.
            state.health=clamp(state.health+step*0.35);
        }

        if(state.health<=0){
            state.dead=true;
            state.sleeping=false;
            addLog('Dein MovieGotchi ist gestorben.');
        }
    }
}

function applyTime(){
    const now=Date.now();
    const previous=Number(state.last)||now;

    // Maximal 72 Stunden nachholen.
    const elapsed=Math.max(0,Math.min(72,(now-previous)/3600000));

    if(elapsed>0&&!state.dead){
        simulate(elapsed);
    }

    state.last=now;
    save();
}

function el(id){
    return document.getElementById(id);
}

function escapeHtml(s){
    return String(s).replace(/[&<>"']/g,c=>({
        '&':'&amp;',
        '<':'&lt;',
        '>':'&gt;',
        '"':'&quot;',
        "'":'&#39;'
    }[c]));
}

function stageLabel(){
    const st=stageInfo();
    return st.name+' · Tag '+(Math.floor(state.age)+1);
}

function render(){
    const st=stageInfo();

    el('petName').textContent=state.name;
    el('stage').textContent=stageLabel();

    el('pet').textContent=
        state.dead?'🪦':
        state.sleeping?'😴':
        st.emoji;

    let mood='Ich fühle mich wohl!';

    if(state.dead)mood='Neustart nötig.';
    else if(state.sleeping)mood='Zzz... Ich schlafe.';
    else if(state.hunger<20)mood='Ich habe großen Hunger!';
    else if(state.clean<20)mood='Ich brauche ein Bad!';
    else if(state.energy<20)mood='Ich bin sehr müde!';
    else if(state.health<40)mood='Mir geht es nicht gut.';
    else if(state.happy<25)mood='Mir ist langweilig!';
    else if(state.affection<20)mood='Ich vermisse dich!';

    el('bubble').textContent=
        state.dead?'RIP':
        state.sleeping?'Zzz':
        state.hunger<20?'Hunger':
        state.energy<20?'Müde':
        'Hi';

    el('petMood').textContent=mood;
    el('coins').textContent=state.coins;

    const data=[
        ['Sättigung',state.hunger,'🍎','gold'],
        ['Freude',state.happy,'😊','pink'],
        ['Gesundh.',state.health,'❤️','red'],
        ['Sauber',state.clean,'🧼','blue'],
        ['Energie',state.energy,'⚡','gold'],
        ['Zuneig.',state.affection,'💕','pink']
    ];

    el('stats').innerHTML=data.map(x=>{
        const value=Math.round(x[1]);

        return '<div class="stat">'+
            '<div class="stat-head"><span>'+x[2]+' '+x[0]+'</span><b>'+value+'%</b></div>'+
            '<div class="bar"><div class="fill '+x[3]+'" style="width:'+clamp(x[1])+'%"></div></div>'+
            '</div>';
    }).join('');

    el('foodCount').textContent=state.inventory.food;
    el('medicineCount').textContent=state.inventory.medicine;

    el('log').innerHTML=state.log.map(x=>
        '<div>'+escapeHtml(x)+'</div>'
    ).join('');

    el('nameInput').value=state.name;

    document.querySelectorAll('[data-action]').forEach(b=>{
        b.disabled=state.dead||
            (state.sleeping&&b.dataset.action!=='sleep');
    });

    renderShop();
}

function popup(title,msg,emoji,callback){
    el('dialogTitle').textContent=title;
    el('dialogText').textContent=msg;
    el('dialogEmoji').textContent=emoji;
    el('overlay').classList.add('show');

    el('dialogOk').onclick=()=>{
        el('overlay').classList.remove('show');
        if(callback)callback();
    };
}

function act(action){
    // Erst die vergangene Zeit berechnen, dann die Aktion ausführen.
    applyTime();

    if(state.dead){
        render();
        return;
    }

    if(state.sleeping&&action!=='sleep'){
        popup('MovieGotchi schläft','Wecke dein Haustier zuerst auf.','😴');
        return;
    }

    switch(action){

        case 'feed':
            if(state.inventory.food<=0){
                popup('Kein Futter','Kaufe zuerst neues Futter im Laden.','🍎');
                return;
            }

            if(state.hunger>=95){
                popup('Schon satt','Dein MovieGotchi hat momentan keinen Hunger.','😊');
                return;
            }

            state.inventory.food--;
            state.hunger=clamp(state.hunger+35);
            state.happy=clamp(state.happy+5);
            addLog('Gefüttert. +35 Sättigung.');
            break;

        case 'play':
            if(state.energy<10){
                popup('Zu müde','Dein MovieGotchi braucht Schlaf.','😴');
                return;
            }

            state.happy=clamp(state.happy+18);
            state.energy=clamp(state.energy-10);
            state.hunger=clamp(state.hunger-3);
            state.coins+=3;

            addLog('Gespielt! +3 Münzen.');
            break;

        case 'clean':
            if(state.clean>=95){
                popup('Alles sauber','Dein MovieGotchi braucht gerade kein Bad.','🧼');
                return;
            }

            state.clean=clamp(state.clean+35);
            state.happy=clamp(state.happy+3);
            addLog('Gebadet und geputzt.');
            break;

        case 'medicine':
            if(state.health>=95){
                popup('Alles bestens','Dein MovieGotchi braucht keine Medizin.','💚');
                return;
            }

            if(state.inventory.medicine<=0){
                popup('Keine Medizin','Du kannst Medizin im Laden kaufen.','💊');
                return;
            }

            state.inventory.medicine--;
            state.health=clamp(state.health+35);
            addLog('Medizin gegeben. +35 Gesundheit.');
            break;

        case 'sleep':
            state.sleeping=!state.sleeping;
            addLog(state.sleeping?'Geht schlafen.':'Ist wieder wach.');
            break;

        case 'love':
            state.affection=clamp(state.affection+18);
            state.happy=clamp(state.happy+8);
            addLog('Gekuschelt.');
            break;

        default:
            return;
    }

    save();
    render();
}

const items=[
    ['food','🍎','Futter','8 🪙',8],
    ['medicine','💊','Medizin','10 🪙',10]
];

function renderShop(){
    el('shop').innerHTML=items.map(i=>
        '<div class="shop-item">'+
        '<span class="emoji">'+i[1]+'</span>'+
        '<div><b>'+i[2]+'</b><small>'+i[3]+'</small></div>'+
        '<button data-buy="'+i[0]+'" '+(state.dead||state.coins<i[4]?'disabled':'')+'>Kaufen</button>'+
        '</div>'
    ).join('');

    el('shop').querySelectorAll('[data-buy]').forEach(b=>{
        b.onclick=()=>buy(b.dataset.buy);
    });
}

function buy(id){
    applyTime();

    const item=items.find(i=>i[0]===id);

    if(!item||state.dead)return;

    const cost=item[4];

    if(state.coins<cost){
        popup('Zu wenig Münzen','Spiele eine Runde und verdiene Münzen!','🪙');
        render();
        return;
    }

    state.coins-=cost;
    state.inventory[id]=(state.inventory[id]||0)+1;

    addLog(item[2]+' gekauft.');

    save();
    render();

    popup('Erfolg',item[2]+' wurde ins Inventar gelegt.','🛍️');
}

document.querySelectorAll('[data-action]').forEach(b=>{
    b.addEventListener('click',()=>act(b.dataset.action));
});

document.querySelectorAll('[data-tab]').forEach(b=>{
    b.addEventListener('click',()=>{
        document.querySelectorAll('.tab').forEach(x=>
            x.classList.toggle('active',x===b)
        );

        document.querySelectorAll('.panel').forEach(x=>
            x.classList.toggle('active',x.id==='panel-'+b.dataset.tab)
        );
    });
});

el('renameBtn').onclick=()=>{
    applyTime();

    if(state.dead)return;

    const name=el('nameInput').value.trim().slice(0,16);

    if(name){
        state.name=name;
        addLog('Umbenannt: '+name);
        save();
        render();
    }
};

el('resetBtn').onclick=()=>{
    popup(
        'Neues Ei?',
        'Wirklich von vorne beginnen? Dein aktueller Spielstand geht verloren.',
        '🥚',
        ()=>{
            state=defaults();
            save();
            render();
        }
    );
};

normalizeState();
applyTime();
render();

setInterval(()=>{
    if(!state.dead){
        applyTime();
        render();
    }
},60000);

})();
</script>
</body>
</html>'''

    def widget():
        return {
            'icon': '🥚',
            'text': 'MovieGotchi',
            'sub': 'Virtuelles Haustier'
        }

    api.route('index', seite)
    api.widget('MovieGotchi', widget, ttl=60, icon='🥚')


def on_load():
    pass
