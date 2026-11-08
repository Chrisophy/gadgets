# -*- coding: utf-8 -*-
# Piraten Jagd
# IT('s) Possible 
# 2026.11.08
"""Piraten Jagd: Schiffe-Arena für bis zu 4 Spieler im Haus - jeder an seinem Gerät (Fernseher, Handy, Tablet) oder gegen Bots.

Öffnen: Erweiterungsliste -> Piraten Jagd -> „Piraten Jagd öffnen“ (auf dem Gerät, auf dem die Engine läuft). Mitspieler in anderen
Räumen öffnen die Adresse, die im Spiel steht (http://<IP>:<Port>/api/x/piratenjagd/index) - bei Android-Geräten zuerst „Teilen“
einschalten und sich mit dem Passwort anmelden (siehe Anleitung). Name eingeben (OK am Namensfeld), „Mitspielen“.
Steuerung: Fernbedienung/Tastatur: links/rechts lenken, OK (Enter/Leertaste) feuert, Pfeil hoch/runter wechselt den Schuss:
Breitseite (je eine Kugel nach links und rechts) oder Bugkanone (eine Kugel geradeaus, weiter und schneller).
Touch: Knöpfe ◄ ► zum Lenken, 🔥 zum Feuern, ↔/↑ wechselt den Schuss. Das Schiff fährt von selbst.
Ziel: Wer zuerst die eingestellte Zahl an Schiffen versenkt hat, gewinnt. Kisten im Wasser bringen Munition und Reparatur.
Inseln sind Mauern und Deckung. Versenkte Schiffe tauchen nach wenigen Sekunden wieder auf. Keine Gewalt: nur Wasser, Holz und Seifenblasen.
Das Spiel läuft in der Engine (60 Schritte pro Sekunde); die Geräte melden Lenkung/Feuer und holen den Stand.
"""
import math
import random
import threading
import time

EXT_ID = 'piratenjagd'
EXT_GUEST = True               # Gäste aus „Teilen im WLAN“ (mit Passwort) dürfen mitspielen - braucht MovieScout ab 2.38.0
EXT_NAME = 'Piraten Jagd'
EXT_DESCRIPTION = 'Schiffe-Arena für bis zu 4 Spieler im Heimnetz (Fernseher, Handy) oder gegen Bots - Fernbedienung und Touch.'
EXT_LINKS = [('Piraten Jagd', 'index')]
EXT_SETTINGS = [
    {'key': 'ziel', 'label': 'Gewonnen hat, wer … Schiffe versenkt hat', 'type': 'number', 'default': 5, 'min': 2, 'max': 20},
    {'key': 'bots', 'label': 'Bot-Stärke (1 leicht, 2 mittel, 3 schwer)', 'type': 'number', 'default': 2, 'min': 1, 'max': 3},
]

W, H = 1000.0, 625.0           # Spielfeld
SHIP_R, BALL_R = 16.0, 4.0
V = 100.0                      # Fahrt (px/s)
TURN = 2.1                     # Drehung (rad/s)
BALL_V, BALL_LIFE = 330.0, 1.05
COOLDOWN = 0.7
BUG_V, BUG_LIFE, BUG_COOLDOWN = 1.15, 1.2, 0.55   # Bugkanone: schneller, weiter, schneller nachgeladen
MAX_AMMO, START_AMMO = 9, 6
HP = 3
TIMEOUT = 10.0
FARBEN = ['#e5484d', '#3e8bff', '#f5c518', '#30c46b']
BOTNAMEN = ['Käpt’n Blubb', 'Rotbart', 'Piratin Pia', 'Kuddel']

ARENEN = [
    {'name': 'Ruhige Bucht', 'inseln': [(500, 312, 70), (250, 165, 42), (750, 460, 42)]},
    {'name': 'Archipel', 'inseln': [(300, 300, 52), (700, 300, 52), (500, 130, 38), (500, 495, 38), (160, 330, 28), (840, 295, 28), (500, 312, 24)]},
    {'name': 'Totenkopf-Insel', 'inseln': [(500, 312, 112), (270, 470, 36), (730, 155, 36), (240, 175, 28), (760, 450, 28)]},
]
SPAWNS = [(90, 90), (910, 90), (910, 535), (90, 535)]

_api = None
_lock = threading.RLock()
_thread = None
S = {}


def neu():
    return {'status': 'wartet', 'seats': [None] * 4, 'ships': {}, 'balls': [], 'pick': [], 'ev': [], 'evid': 0, 'arena': 0,
            'start': 0.0, 'sieger': '', 'pick_t': 0.0, 'heart_t': 0.0, 'pid': 0}


S.update(neu())


def _ziel():
    try:
        return max(2, min(20, int(_api.get('ziel') or 5)))
    except Exception:                                          # noqa: BLE001
        return 5


def _botstaerke():
    try:
        return max(1, min(3, int(_api.get('bots') or 2)))
    except Exception:                                          # noqa: BLE001
        return 2


def _event(s, t, x=0.0, y=0.0):
    s['evid'] += 1
    s['ev'].append([s['evid'], t, round(x), round(y)])
    del s['ev'][:-40]


def _winkel(a):
    while a > math.pi:
        a -= 2 * math.pi
    while a < -math.pi:
        a += 2 * math.pi
    return a


def _inseln(s):
    return ARENEN[s['arena'] % len(ARENEN)]['inseln']


def _spawnwinkel(i):
    x, y = SPAWNS[i]
    return math.atan2(H / 2 - y, W / 2 - x)


def _neues_schiff(i):
    x, y = SPAWNS[i]
    return {'x': float(x), 'y': float(y), 'a': _spawnwinkel(i), 'w': 0.0, 'v': V, 'hp': HP, 'ammo': START_AMMO, 'cd': 0.0,
            'inv': 2.0, 'dead': 0.0, 'hit': 0.0, 'score': 0}


def _frei_ort(s, abstand=60.0):
    """Zufälliger Platz im Wasser (nicht auf Inseln, nicht nah an Schiffen)."""
    for _ in range(60):
        x, y = random.uniform(60, W - 60), random.uniform(60, H - 60)
        if any(math.hypot(x - ix, y - iy) < ir + 34 for ix, iy, ir in _inseln(s)):
            continue
        if any(sh['dead'] <= 0 and math.hypot(x - sh['x'], y - sh['y']) < abstand for sh in s['ships'].values()):
            continue
        return x, y
    return W / 2, 40.0


def _respawn(s, i):
    sh = s['ships'][i]
    best, bd = SPAWNS[i], -1.0
    for x, y in SPAWNS:
        ds = [math.hypot(x - o['x'], y - o['y']) for j, o in s['ships'].items() if j != i and o['dead'] <= 0]
        d = min(ds) if ds else 9999.0
        if d > bd:
            best, bd = (x, y), d
    sh.update(x=float(best[0]), y=float(best[1]), a=math.atan2(H / 2 - best[1], W / 2 - best[0]), hp=HP, ammo=max(sh['ammo'], START_AMMO - 1),
              cd=0.0, inv=2.0, dead=0.0, hit=0.0)


def _start_spiel(s, jetzt):
    s['ships'] = {i: _neues_schiff(i) for i, seat in enumerate(s['seats']) if seat}
    s['balls'], s['pick'] = [], []
    s['status'], s['start'], s['sieger'] = 'start', jetzt + 3.0, ''
    s['pick_t'], s['heart_t'] = jetzt + 2.0, jetzt + 8.0
    _event(s, 'horn')


# ----------------------------------------------------------------------------- Bots
def _bot_eingabe(s, i, sh):
    st = _botstaerke()
    ziele = [o for j, o in s['ships'].items() if j != i and o['dead'] <= 0]
    inseln = _inseln(s)
    a = sh['a']
    ziel = None
    if ziele:
        ziel = min(ziele, key=lambda o: math.hypot(o['x'] - sh['x'], o['y'] - sh['y']))
    ziel_winkel = a
    if sh['ammo'] <= 1 and s['pick']:
        k = [p for p in s['pick'] if p[0] == 'a'] or s['pick']
        p = min(k, key=lambda q: math.hypot(q[1] - sh['x'], q[2] - sh['y']))
        ziel_winkel = math.atan2(p[2] - sh['y'], p[1] - sh['x'])
    elif sh['hp'] <= 1 and any(p[0] == 'h' for p in s['pick']):
        p = [p for p in s['pick'] if p[0] == 'h'][0]
        ziel_winkel = math.atan2(p[2] - sh['y'], p[1] - sh['x'])
    elif ziel:
        dx, dy = ziel['x'] - sh['x'], ziel['y'] - sh['y']
        d = math.hypot(dx, dy)
        peil = math.atan2(dy, dx)
        if d > 330:
            ziel_winkel = peil
        elif d < 110:
            ziel_winkel = peil + math.pi
        else:                                                   # Breitseite: quer zum Gegner fahren
            seite = peil - math.pi / 2 if abs(_winkel(peil - math.pi / 2 - a)) < abs(_winkel(peil + math.pi / 2 - a)) else peil + math.pi / 2
            ziel_winkel = seite
    # Hindernisse voraus
    for dist in (55.0, 110.0):
        px, py = sh['x'] + math.cos(a) * dist, sh['y'] + math.sin(a) * dist
        hindernis = None
        for ix, iy, ir in inseln:
            if math.hypot(px - ix, py - iy) < ir + 26:
                hindernis = (ix, iy)
                break
        if hindernis is None and (px < 40 or px > W - 40 or py < 40 or py > H - 40):
            hindernis = (W / 2, H / 2)
            ziel_winkel = math.atan2(H / 2 - sh['y'], W / 2 - sh['x'])
            break
        if hindernis:
            weg = math.atan2(sh['y'] - hindernis[1], sh['x'] - hindernis[0])
            ziel_winkel = a + (1.2 if _winkel(weg - a) > 0 else -1.2)
            break
    diff = _winkel(ziel_winkel - a)
    steer = max(-1.0, min(1.0, diff * 3.0))
    if abs(diff) < 0.05:
        steer = 0.0
    steer *= (0.7, 0.9, 1.0)[st - 1]
    feuer = False
    if ziel and sh['ammo'] > 0 and sh['cd'] <= 0:
        dx, dy = ziel['x'] - sh['x'], ziel['y'] - sh['y']
        d = math.hypot(dx, dy)
        d_rel = _winkel(math.atan2(dy, dx) - a)
        fehler = min(abs(d_rel - math.pi / 2), abs(d_rel + math.pi / 2))
        tol = (0.30, 0.18, 0.10)[st - 1]
        if d < 300 and fehler < tol and random.random() < (0.05, 0.12, 0.3)[st - 1]:
            feuer = True
    return steer, feuer


# ----------------------------------------------------------------------------- Spielschritt
def _schuss(s, i, sh, modus='b'):
    if modus == 'v':                                           # Bugkanone: eine Kugel geradeaus
        w = sh['a']
        v = V + BALL_V * BUG_V
        s['balls'].append({'x': sh['x'] + math.cos(w) * (SHIP_R + 6), 'y': sh['y'] + math.sin(w) * (SHIP_R + 6),
                           'vx': math.cos(w) * v, 'vy': math.sin(w) * v, 'life': BALL_LIFE * BUG_LIFE, 'o': i})
        sh['ammo'] -= 1
        sh['cd'] = BUG_COOLDOWN
        _event(s, 'boom', sh['x'], sh['y'])
        return
    for seite in (1, -1):
        w = sh['a'] + seite * math.pi / 2
        vx = math.cos(sh['a']) * V + math.cos(w) * BALL_V
        vy = math.sin(sh['a']) * V + math.sin(w) * BALL_V
        s['balls'].append({'x': sh['x'] + math.cos(w) * (SHIP_R + 2), 'y': sh['y'] + math.sin(w) * (SHIP_R + 2), 'vx': vx, 'vy': vy,
                           'life': BALL_LIFE, 'o': i})
    sh['ammo'] -= 1
    sh['cd'] = COOLDOWN
    _event(s, 'boom', sh['x'], sh['y'])


def _sieg(name):
    try:
        d = _api.get('siege', {})
        d = d if isinstance(d, dict) else {}
        d[name] = int(d.get(name, 0)) + 1
        _api.set('siege', d)
    except Exception:                                          # noqa: BLE001
        pass


def _gleiten(sh, nx, ny, dt):
    """Stößt ein Schiff an Insel oder Rand, dreht es sanft in Richtung Küstenlinie: es rutscht daran entlang statt festzuhängen."""
    n = math.hypot(nx, ny) or 1.0
    t1 = math.atan2(nx / n, -ny / n)
    t = t1 if abs(_winkel(t1 - sh['a'])) < abs(_winkel(t1 + math.pi - sh['a'])) else _winkel(t1 + math.pi)
    sh['a'] = _winkel(sh['a'] + _winkel(t - sh['a']) * min(1.0, 5.0 * dt))


def schritt(s, dt, jetzt):
    inseln = _inseln(s)
    for i, sh in s['ships'].items():
        seat = s['seats'][i]
        if seat is None:
            continue
        sh['cd'] = max(0.0, sh['cd'] - dt)
        sh['inv'] = max(0.0, sh['inv'] - dt)
        sh['hit'] = max(0.0, sh['hit'] - dt)
        if sh['dead'] > 0:
            sh['dead'] -= dt
            sh['v'], sh['w'] = 0.0, 0.0
            if sh['dead'] <= 0:
                _respawn(s, i)
            continue
        if seat.get('bot'):
            steer, feuer = _bot_eingabe(s, i, sh)
        else:
            steer = seat['steer']
            feuer = bool(seat['fire_t'] and jetzt - seat['fire_t'] < 0.25)
        if feuer and sh['ammo'] > 0 and sh['cd'] <= 0:
            _schuss(s, i, sh, seat.get('modus', 'b'))
            seat['fire_t'] = 0.0
        sh['w'] = steer * TURN
        sh['v'] = V
        sh['a'] = _winkel(sh['a'] + sh['w'] * dt)
        sh['x'] += math.cos(sh['a']) * V * dt
        sh['y'] += math.sin(sh['a']) * V * dt
    lebende = [(i, sh) for i, sh in s['ships'].items() if sh['dead'] <= 0]
    for n, (i, a) in enumerate(lebende):                       # Schiffe stoßen sich weich ab
        for j, b in lebende[n + 1:]:
            dx, dy = b['x'] - a['x'], b['y'] - a['y']
            d = math.hypot(dx, dy) or 0.001
            if d < SHIP_R * 2:
                p = (SHIP_R * 2 - d) / 2
                a['x'] -= dx / d * p
                a['y'] -= dy / d * p
                b['x'] += dx / d * p
                b['y'] += dy / d * p
                a['a'] = _winkel(a['a'] + 2.6 * dt)             # beide drehen nach rechts: aneinander vorbei statt festhängen
                b['a'] = _winkel(b['a'] + 2.6 * dt)
    for sh in s['ships'].values():                             # Inseln und Rand sind Mauern (zuletzt, damit nichts darin landet)
        if sh['dead'] > 0:
            continue
        for _ in range(2):
            for ix, iy, ir in inseln:
                dx, dy = sh['x'] - ix, sh['y'] - iy
                d = math.hypot(dx, dy) or 0.001
                m = ir + SHIP_R
                if d < m:
                    sh['x'], sh['y'] = ix + dx / d * m, iy + dy / d * m
                    _gleiten(sh, dx / d, dy / d, dt)
            nx = ny = 0.0
            if sh['x'] < SHIP_R: nx = 1.0
            elif sh['x'] > W - SHIP_R: nx = -1.0
            if sh['y'] < SHIP_R: ny = 1.0
            elif sh['y'] > H - SHIP_R: ny = -1.0
            sh['x'] = max(SHIP_R, min(W - SHIP_R, sh['x']))
            sh['y'] = max(SHIP_R, min(H - SHIP_R, sh['y']))
            if nx or ny:
                _gleiten(sh, nx, ny, dt)
    rest = []
    for b in s['balls']:
        b['x'] += b['vx'] * dt
        b['y'] += b['vy'] * dt
        b['life'] -= dt
        if b['life'] <= 0 or not (0 <= b['x'] <= W and 0 <= b['y'] <= H):
            if b['life'] > 0:
                continue
            _event(s, 'splash', b['x'], b['y'])
            continue
        if any(math.hypot(b['x'] - ix, b['y'] - iy) < ir for ix, iy, ir in inseln):
            _event(s, 'splash', b['x'], b['y'])
            continue
        getroffen = False
        for j, sh in s['ships'].items():
            if j == b['o'] or sh['dead'] > 0 or sh['inv'] > 0:
                continue
            if math.hypot(b['x'] - sh['x'], b['y'] - sh['y']) < SHIP_R + BALL_R:
                sh['hp'] -= 1
                sh['hit'] = 0.3
                getroffen = True
                if sh['hp'] <= 0:
                    sh['hp'], sh['dead'] = 0, 3.0
                    _event(s, 'sink', sh['x'], sh['y'])
                    o = s['ships'].get(b['o'])
                    if o is not None:
                        o['score'] += 1
                else:
                    _event(s, 'hit', sh['x'], sh['y'])
                break
        if not getroffen:
            rest.append(b)
    s['balls'] = rest
    for sh in lebende:                                         # Kisten einsammeln
        sh = sh[1]
        if sh['dead'] > 0:
            continue
        for p in list(s['pick']):
            if math.hypot(p[1] - sh['x'], p[2] - sh['y']) < SHIP_R + 12:
                if p[0] == 'a':
                    sh['ammo'] = min(MAX_AMMO, sh['ammo'] + 4)
                else:
                    sh['hp'] = min(HP, sh['hp'] + 1)
                s['pick'].remove(p)
                _event(s, 'pick', p[1], p[2])
    if jetzt >= s['pick_t'] and sum(1 for p in s['pick'] if p[0] == 'a') < 3:
        x, y = _frei_ort(s)
        s['pick'].append(['a', x, y])
        s['pick_t'] = jetzt + 4.0
    if jetzt >= s['heart_t'] and not any(p[0] == 'h' for p in s['pick']):
        x, y = _frei_ort(s)
        s['pick'].append(['h', x, y])
        s['heart_t'] = jetzt + 14.0
    ziel = _ziel()
    for i, sh in s['ships'].items():
        if sh['score'] >= ziel:
            s['status'] = 'ende'
            seat = s['seats'][i] or {}
            s['sieger'] = seat.get('name', '?')
            if seat and not seat.get('bot'):
                _sieg(seat['name'])
            _event(s, 'win')
            break


def _aufraeumen(s, jetzt):
    for i, seat in enumerate(s['seats']):
        if seat and not seat.get('bot') and jetzt - seat['last'] > TIMEOUT:
            s['seats'][i] = None
            s['ships'].pop(i, None)
    if not any(seat and not seat.get('bot') for seat in s['seats']):      # nur Bots: nichts läuft weiter
        s['seats'] = [None] * 4
        s['ships'] = {}
        if s['status'] != 'wartet':
            s.update(status='wartet', balls=[], pick=[], sieger='')
    if s['status'] in ('start', 'laeuft') and sum(1 for x in s['seats'] if x) < 2:
        s.update(status='wartet', balls=[], pick=[], sieger='', ships={})


def _loop():
    global _thread
    letzte = time.time()
    leer_seit = None
    while True:
        time.sleep(1 / 60.0)
        jetzt = time.time()
        dt = min(0.05, jetzt - letzte)
        letzte = jetzt
        with _lock:
            s = S
            _aufraeumen(s, jetzt)
            if s['status'] == 'start' and jetzt >= s['start']:
                s['status'] = 'laeuft'
            if s['status'] == 'laeuft':
                schritt(s, dt, jetzt)
            if not any(s['seats']):
                leer_seit = leer_seit or jetzt
                if jetzt - leer_seit > 20:
                    _thread = None
                    S.clear()
                    S.update(neu())
                    return
            else:
                leer_seit = None


def _sicherstellen():
    global _thread
    with _lock:
        if _thread is None or not _thread.is_alive():
            _thread = threading.Thread(target=_loop, name='piratenjagd', daemon=True)
            _thread.start()


def _sicht(s):
    jetzt = time.time()
    k = max(0.0, s['start'] - jetzt) if s['status'] == 'start' else 0.0
    ar = ARENEN[s['arena'] % len(ARENEN)]
    schiffe = []
    for i, sh in s['ships'].items():
        seat = s['seats'][i]
        if not seat:
            continue
        schiffe.append({'i': i, 'name': seat['name'], 'bot': bool(seat.get('bot')), 'x': round(sh['x'], 1), 'y': round(sh['y'], 1),
                        'a': round(sh['a'], 3), 'v': sh['v'], 'w': round(sh['w'], 2), 'hp': sh['hp'], 'ammo': sh['ammo'],
                        'score': sh['score'], 'inv': round(sh['inv'], 2), 'dead': round(sh['dead'], 2), 'hit': round(sh['hit'], 2)})
    sitze = [{'i': i, 'name': x['name'], 'bot': bool(x.get('bot'))} if x else None for i, x in enumerate(s['seats'])]
    return {'status': s['status'], 'countdown': round(k, 1), 'ziel': _ziel(), 'sieger': s['sieger'], 'w': W, 'h': H,
            'arena': {'idx': s['arena'] % len(ARENEN), 'name': ar['name'], 'inseln': [list(x) for x in ar['inseln']], 'n': len(ARENEN)},
            'ships': schiffe, 'seats': sitze, 'frei': sum(1 for x in s['seats'] if x is None),
            'balls': [[round(b['x'], 1), round(b['y'], 1), round(b['vx'], 1), round(b['vy'], 1)] for b in s['balls']],
            'pick': [[p[0], round(p[1]), round(p[2])] for p in s['pick']], 'ev': s['ev'][-12:], 'evid': s['evid'], 'farben': FARBEN}


PAGE = r"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="ms-game"><meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no"><title>Piraten Jagd</title>
<style>
:root{--bg:#0b1722;--fg:#eaf2f8;--mut:#93a8bd;--card:#142636;--acc:#ffc94d}
*{box-sizing:border-box}body{margin:0;height:100vh;height:100dvh;overflow:hidden;background:var(--bg);color:var(--fg);font:clamp(14px,2.3vmin,26px)/1.35 system-ui,sans-serif;display:flex;flex-direction:column;align-items:center;gap:8px;padding:8px;-webkit-user-select:none;user-select:none;overscroll-behavior:none;touch-action:manipulation}
#top{width:min(98vw,calc((100vh - 12em)*1.6));width:min(98vw,calc((100dvh - 12em)*1.6));display:flex;gap:8px;justify-content:space-between}
.chip{flex:1;min-width:0;background:var(--card);border-radius:12px;padding:.25em .6em;border-bottom:4px solid var(--c);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.chip b{color:var(--c)}.chip.me{outline:2px solid var(--c)}.chip.off{opacity:.35}
#cvw{position:relative;width:min(98vw,calc((100vh - 12em)*1.6));width:min(98vw,calc((100dvh - 12em)*1.6));aspect-ratio:1000/625}
canvas{display:block;width:100%;height:100%;border-radius:12px;background:#1b6b8f}
#msg{position:absolute;inset:0;display:grid;place-items:center;text-align:center;background:rgba(4,12,20,.66);border-radius:12px;padding:12px;font-size:1.25em}
#msg small{display:block;color:var(--mut);font-size:.7em;margin-top:.3em}
#lobby{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;align-items:center}
input{font:inherit;padding:.45em .8em;border-radius:12px;border:2px solid var(--mut);background:var(--card);color:var(--fg);width:11em}
button{font:inherit;color:var(--fg);background:var(--card);border:4px solid transparent;border-radius:14px;padding:.5em .9em;cursor:pointer}button.f,button:focus{outline:none;border-color:var(--acc)}
#pad{display:none;width:min(98vw,calc((100vh - 12em)*1.6));width:min(98vw,calc((100dvh - 12em)*1.6));justify-content:space-between;align-items:center}
#pad .g{display:flex;gap:12px;touch-action:none}#pad .g button{pointer-events:none}#pad button{position:relative;font-size:2.4em;min-width:2.1em;min-height:1.6em;padding:.1em .3em;touch-action:none}#pad button.on{background:#25506c;border-color:var(--acc)}
#pad #bf::after,#pad #bm::after{content:"";position:absolute;inset:-3vh}
#pad .r{display:flex;gap:12px;align-items:flex-end}#pad #bm{font-size:1.8em;min-width:1.7em}input.f{border-color:var(--acc)}
@media (pointer:coarse){#pad.show{display:flex}}
@media not all and (pointer:coarse){body.playing #top,body.playing #cvw{width:min(98vw,calc((100vh - 5.5em)*1.6));width:min(98vw,calc((100dvh - 5.5em)*1.6))}}
body.playing #lobby{display:none}@media (pointer:coarse){body.playing #lobby{display:flex}}
/* Handy quer: Spielfläche groß in der Mitte, Lenken ganz links, Feuer ganz rechts, Aufhören unter dem Schließen-X */
@media (pointer:coarse) and (orientation:landscape){
body{padding:4px;gap:4px}
#top,#cvw{width:min(calc(100vw - 2*(34vh + 2vw)),calc((100vh - 5.4em)*1.6));width:min(calc(100vw - 2*(34vh + 2vw)),calc((100dvh - 5.4em)*1.6))}
#pad.show{position:fixed;left:0;right:0;bottom:0;width:auto;pointer-events:none;padding:0 2vw 3vh;align-items:flex-end}
#pad button{pointer-events:auto;width:15.5vh;height:15.5vh;min-width:0;min-height:0;padding:0;font-size:min(8vh,2.6em);display:grid;place-items:center}
#pad .r{gap:2.5vh}#pad #bm{width:11vh;height:11vh;font-size:min(6vh,2em)}
#pad .g{gap:1.5vh;pointer-events:auto;padding:10vh 2vh 3vh 2vw;margin:-10vh -2vh -3vh -2vw}#pad .g button{pointer-events:none}
/* alle Menü-Knöpfe als Spalte rechts (unter dem Schließen-X), nie unten abgeschnitten */
#lobby{position:fixed;right:.5vw;top:max(56px,13vh);width:calc(34vh + 1vw);flex-direction:column;flex-wrap:nowrap;align-items:stretch;justify-content:flex-start;gap:5px;max-height:calc(100vh - max(56px,13vh) - 22vh);max-height:calc(100dvh - max(56px,13vh) - 22vh);overflow-y:auto}
#lobby input{width:100%;padding:.3em .5em}
#lobby button{font-size:.85em;padding:.35em .4em;white-space:normal;line-height:1.2}
}
#snd{position:absolute;right:6px;top:6px;padding:.1em .4em;font-size:.9em;background:rgba(0,0,0,.35);border-radius:10px}
</style></head><body>
<div id="top"></div>
<div id="cvw"><canvas id="cv" width="1000" height="625"></canvas><div id="msg"></div><button id="snd" aria-label="Ton an/aus">🔊</button></div>
<div id="pad"><div class="g"><button id="bl" aria-label="Links">◄</button><button id="br" aria-label="Rechts">►</button></div><div class="r"><button id="bm" aria-label="Schuss wechseln">↔</button><button id="bf" aria-label="Feuer">🔥</button></div></div>
<div id="lobby"><input id="nm" maxlength="16" placeholder="Dein Name (OK = tippen)" autocomplete="off" enterkeyhint="done">
<button id="bj">Mitspielen</button><button id="bgo" style="display:none">Los!</button><button id="bbot" style="display:none">Bot dazu</button><button id="bbw" style="display:none">Bot weg</button><button id="bar" style="display:none">Arena</button><button id="bn" style="display:none">Nochmal</button><button id="bq" style="display:none">Aufhören</button><button id="bx">✕ Beenden</button></div>
<script>
"use strict";
const $=(s)=>document.querySelector(s), W=1000, H=625;
let me=null, st=null, stT=0, steer=0, keyL=0, keyR=0, padL=0, padR=0, fire=false, btn=0, lastEv=0, muted=false;
let modus='b',modusT=0,addr='';
try{$('#nm').value=localStorage.getItem('pj.name')||'';muted=localStorage.getItem('pj.mute')==='1'}catch(e){}
if(!$('#nm').value)$('#nm').value='Pirat '+(10+Math.floor(Math.random()*90));
const QS=new URLSearchParams(location.search),GTOK=QS.get('share')||QS.get('token')||'',GH=GTOK?{'X-Share':GTOK}:{};
/* Adresse für Mitspieler in anderen Räumen (nur auf dem Gerät mit der Engine): mit Teilen-Passwort, damit ein Aufruf genügt */
(async()=>{try{const l=await (await fetch('/api/lan',{headers:GH})).json(),sh=await (await fetch('/api/share/status',{headers:GH})).json();
  if(l&&l.ip&&l.port&&sh.role==='host'){const u='http://'+l.ip+':'+l.port+'/api/x/piratenjagd/index';
    addr=sh.enabled&&sh.password?u+'?share='+encodeURIComponent(sh.password):u+' (auf Android-Geräten vorher „Teilen“ einschalten)'}}catch(e){}})();
$('#snd').textContent=muted?'🔇':'🔊';
async function post(p,b){const r=await fetch(p,{method:'POST',headers:Object.assign({'Content-Type':'application/json'},GH),body:JSON.stringify(b||{})});return r.json()}
const auth=()=>({platz:me.platz,token:me.token});
/* ---------- Ton (alles selbst erzeugt) ---------- */
let ac=null;
function audio(){if(!ac){try{ac=new (window.AudioContext||window.webkitAudioContext)()}catch(e){}}if(ac&&ac.state==='suspended')ac.resume();return ac}
function noise(d,f,type,vol,t0){const a=ac,n=Math.floor(a.sampleRate*d),b=a.createBuffer(1,n,a.sampleRate),c=b.getChannelData(0);for(let i=0;i<n;i++)c[i]=(Math.random()*2-1)*(1-i/n);
  const s=a.createBufferSource(),fl=a.createBiquadFilter(),g=a.createGain();s.buffer=b;fl.type=type;fl.frequency.value=f;g.gain.setValueAtTime(vol,t0);g.gain.exponentialRampToValueAtTime(.001,t0+d);s.connect(fl);fl.connect(g);g.connect(a.destination);s.start(t0)}
function tone(f0,f1,d,vol,type,t0){const a=ac,o=a.createOscillator(),g=a.createGain();o.type=type||'sine';o.frequency.setValueAtTime(f0,t0);o.frequency.exponentialRampToValueAtTime(Math.max(20,f1),t0+d);g.gain.setValueAtTime(vol,t0);g.gain.exponentialRampToValueAtTime(.001,t0+d);o.connect(g);g.connect(a.destination);o.start(t0);o.stop(t0+d+.02)}
function sound(t){if(muted)return;const a=audio();if(!a)return;const n=a.currentTime;
  if(t==='boom'){noise(.4,500,'lowpass',.5,n);tone(110,40,.35,.5,'sine',n)}
  else if(t==='hit'){noise(.14,1200,'bandpass',.5,n);tone(240,120,.12,.3,'triangle',n)}
  else if(t==='sink'){tone(420,70,.9,.3,'sine',n);noise(.5,300,'lowpass',.3,n)}
  else if(t==='pick'){tone(660,660,.12,.25,'sine',n);tone(990,990,.18,.25,'sine',n+.1)}
  else if(t==='splash'){noise(.1,2500,'highpass',.15,n)}
  else if(t==='horn'){tone(196,190,.5,.2,'sawtooth',n);tone(294,290,.5,.15,'sawtooth',n)}
  else if(t==='win'){[523,659,784,1046].forEach((f,i)=>tone(f,f,.25,.25,'triangle',n+i*.16))}}
$('#snd').onclick=(e)=>{e.stopPropagation();muted=!muted;$('#snd').textContent=muted?'🔇':'🔊';try{localStorage.setItem('pj.mute',muted?'1':'0')}catch(e2){}};
/* ---------- Menü ---------- */
async function join(){audio();const name=($('#nm').value||'Pirat '+(10+Math.floor(Math.random()*90))).trim().slice(0,16);try{localStorage.setItem('pj.name',name)}catch(e){}const r=await post('beitreten',{name});if(r.error){$('#msg').innerHTML=r.error;return}me=r}
async function leave(){if(me){await post('verlassen',auth());me=null}}
$('#bj').onclick=join;$('#bq').onclick=leave;
function closeGame(){try{if(window.parent!==window){window.parent.history.back();return}}catch(e){}if(history.length>1)history.back();else location.href='/ui/'}
$('#bx').onclick=closeGame;
function toggleModus(){modus=modus==='b'?'v':'b';modusT=performance.now();$('#bm').textContent=modus==='b'?'↔':'↑';sound('pick')}
$('#bgo').onclick=()=>me&&post('los',auth());$('#bbot').onclick=()=>me&&post('bot',Object.assign(auth(),{an:true}));$('#bbw').onclick=()=>me&&post('bot',Object.assign(auth(),{an:false}));
$('#bar').onclick=()=>me&&post('arena',auth());$('#bn').onclick=()=>me&&post('nochmal',auth());
function sheet(){return ['bj','nm','bgo','bbot','bbw','bar','bn','bq','bx'].map(i=>$('#'+i)).filter(b=>b.style.display!=='none')}
function focusBtn(){const L=sheet();btn=Math.max(0,Math.min(btn,L.length-1));L.forEach((b,i)=>b.classList.toggle('f',i===btn))}
const playing=()=>me&&st&&(st.status==='laeuft'||st.status==='start');
function fireNow(){fire=true;setTimeout(()=>{fire=false},120)}
document.addEventListener('keydown',e=>{const k=e.key,inp=document.activeElement.tagName==='INPUT';
  if(playing()){
    if(k==='ArrowLeft'||k==='a'||k==='A'){e.preventDefault();keyL=1}
    else if(k==='ArrowRight'||k==='d'||k==='D'){e.preventDefault();keyR=1}
    else if(k==='ArrowUp'||k==='ArrowDown'||k==='w'||k==='W'||k==='s'||k==='S'){e.preventDefault();toggleModus()}
    else if(k==='Enter'||k==='Select'||k===' '||e.keyCode===23||e.keyCode===66){e.preventDefault();audio();fireNow()}
    else if(k==='Escape'||k==='Backspace'||k==='GoBack'||k==='BrowserBack'){e.preventDefault();leave()}
    return}
  const step=(d)=>{const L=sheet();btn=(btn+d+L.length)%L.length;focusBtn()};
  if(inp){                                       /* im Namensfeld gehört alles dem Feld, außer Fertig / Hoch / Runter / Zurück */
    if(k==='Enter'){e.preventDefault();document.activeElement.blur();$('#bj').click()}
    else if(k==='Escape'||k==='GoBack'||k==='BrowserBack'){e.preventDefault();document.activeElement.blur()}
    else if(k==='ArrowUp'||k==='ArrowDown'){e.preventDefault();document.activeElement.blur();step(k==='ArrowUp'?-1:1)}
    return}
  const L=sheet(),cur=L[Math.min(btn,L.length-1)];
  if(k==='ArrowLeft'||k==='ArrowUp'){e.preventDefault();step(-1)}
  else if(k==='ArrowRight'||k==='ArrowDown'){e.preventDefault();step(1)}
  else if(k==='Enter'||k==='Select'||e.keyCode===23||e.keyCode===66){e.preventDefault();audio();
    if(cur&&cur.tagName==='INPUT'){cur.focus();cur.click();try{cur.setSelectionRange(cur.value.length,cur.value.length)}catch(x){}}else if(cur)cur.click()}
  else if(k==='Escape'||k==='Backspace'||k==='GoBack'||k==='BrowserBack'){e.preventDefault();if(me)leave();else closeGame()}
  else if(cur&&cur.tagName==='INPUT'&&k.length===1&&!e.ctrlKey&&!e.metaKey&&!e.altKey){cur.focus()}
  else if(k==='m'||k==='M'){$('#snd').click()}});
document.addEventListener('keyup',e=>{const k=e.key;if(k==='ArrowLeft'||k==='a'||k==='A')keyL=0;if(k==='ArrowRight'||k==='d'||k==='D')keyR=0});
window.addEventListener('blur',()=>{keyL=keyR=padL=padR=0});
/* Lenken: ganze Lenkfläche (inkl. Lücke und Rand) zählt, links/rechts nach Fingerposition; Finger wird festgehalten, Danebentippen stoppt nicht */
(function(){const g=document.querySelector('#pad .g'),bl=$('#bl'),br=$('#br');let pid=null;
  function upd(e){const a=bl.getBoundingClientRect(),c=br.getBoundingClientRect(),R=e.clientX>(a.right+c.left)/2;padL=R?0:1;padR=R?1:0;bl.classList.toggle('on',!R);br.classList.toggle('on',R)}
  function end(e){if(e.pointerId!==pid)return;pid=null;padL=padR=0;bl.classList.remove('on');br.classList.remove('on')}
  g.addEventListener('pointerdown',e=>{if(pid!==null)return;e.preventDefault();pid=e.pointerId;try{g.setPointerCapture(pid)}catch(x){}audio();upd(e)});
  g.addEventListener('pointermove',e=>{if(e.pointerId===pid){e.preventDefault();upd(e)}});
  ['pointerup','pointercancel','lostpointercapture'].forEach(t=>g.addEventListener(t,end))})();
$('#bm').addEventListener('pointerdown',e=>{e.preventDefault();audio();toggleModus()});
/* Feuer: gedrückt halten = Dauerfeuer (Abklingzeit regelt der Server) */
(function(){const bf=$('#bf');let fp=null,ft=null;
  bf.addEventListener('pointerdown',e=>{e.preventDefault();if(fp!==null)return;fp=e.pointerId;try{bf.setPointerCapture(fp)}catch(x){}audio();fireNow();bf.classList.add('on');ft=setInterval(fireNow,300)});
  const end=e=>{if(e.pointerId!==fp)return;fp=null;clearInterval(ft);bf.classList.remove('on')};
  ['pointerup','pointercancel','lostpointercapture'].forEach(t=>bf.addEventListener(t,end))})();
/* ---------- Zeichnen ---------- */
const cv=$('#cv'),x=cv.getContext('2d');let parts=[],trail={};
function addParts(kind,px,py){const n=kind==='sink'?26:(kind==='hit'?14:(kind==='boom'?10:8));
  for(let i=0;i<n;i++){const a=Math.random()*6.283,s=(kind==='boom'?30:60)+Math.random()*90;parts.push({k:kind,x:px,y:py,vx:Math.cos(a)*s,vy:Math.sin(a)*s-(kind==='sink'?40:0),l:.6+Math.random()*.6,m:1.1})}}
function evs(){if(!st)return;for(const e of st.ev){if(e[0]<=lastEv)continue;lastEv=e[0];sound(e[1]);if(e[1]!=='horn'&&e[1]!=='win')addParts(e[1],e[2],e[3])}lastEv=Math.max(lastEv,st.evid||0)}
function ship(sh,col,mine,t){x.save();x.translate(sh.px,sh.py);x.rotate(sh.pa);x.scale(1.3,1.3);
  const blink=sh.inv>0&&Math.floor(t*8)%2===0;if(blink)x.globalAlpha=.45;
  x.fillStyle='rgba(0,0,0,.18)';x.beginPath();x.ellipse(2,4,22,10,0,0,7);x.fill();
  x.fillStyle=sh.hit>0?'#fff':'#7a4a22';x.beginPath();x.moveTo(24,0);x.quadraticCurveTo(14,-12,-16,-11);x.lineTo(-20,-6);x.lineTo(-20,6);x.lineTo(-16,11);x.quadraticCurveTo(14,12,24,0);x.fill();
  x.fillStyle='#b27a3f';x.beginPath();x.moveTo(18,0);x.quadraticCurveTo(10,-7,-14,-7);x.lineTo(-14,7);x.quadraticCurveTo(10,7,18,0);x.fill();
  x.fillStyle=col;x.beginPath();x.moveTo(20,0);x.quadraticCurveTo(12,-9,-17,-8.5);x.lineTo(-17,-6.5);x.quadraticCurveTo(12,-7,20,0);x.fill();
  x.beginPath();x.moveTo(20,0);x.quadraticCurveTo(12,9,-17,8.5);x.lineTo(-17,6.5);x.quadraticCurveTo(12,7,20,0);x.fill();
  x.fillStyle=col;x.fillRect(2,-13,4,26);x.fillRect(-10,-10,4,20);
  x.fillStyle='#fff';x.fillRect(3,-12,2,24);x.fillRect(-9,-9,2,18);
  x.fillStyle='#111';x.beginPath();x.arc(-18,0,3,0,7);x.fill();
  x.restore();
  if(mine){x.strokeStyle='rgba(255,255,255,.8)';x.lineWidth=2;x.setLineDash([4,5]);x.beginPath();x.arc(sh.px,sh.py,27,0,7);x.stroke();x.setLineDash([])}}
function island(ix,iy,ir,n){x.fillStyle='#e6d49a';x.beginPath();x.arc(ix,iy,ir+9,0,7);x.fill();x.fillStyle='#4aa05a';x.beginPath();x.arc(ix,iy,ir,0,7);x.fill();
  x.fillStyle='#3a8a4a';for(let k=0;k<4;k++){const a=k*1.7+n,d=ir*.45;x.beginPath();x.arc(ix+Math.cos(a)*d,iy+Math.sin(a)*d,ir*.32,0,7);x.fill()}
  x.fillStyle='#6b4a2a';x.fillRect(ix-2,iy-ir*.3,4,ir*.35);x.fillStyle='#2f7a3c';x.beginPath();x.arc(ix,iy-ir*.32,ir*.28,0,7);x.fill()}
function draw(){const t=performance.now()/1000;x.clearRect(0,0,W,H);
  const g=x.createLinearGradient(0,0,0,H);g.addColorStop(0,'#2a86ad');g.addColorStop(1,'#1a6288');x.fillStyle=g;x.fillRect(0,0,W,H);
  x.strokeStyle='rgba(255,255,255,.10)';x.lineWidth=2;for(let r=0;r<10;r++){x.beginPath();for(let c=0;c<=W;c+=20){const yy=r*66+20+Math.sin(c/55+t*1.2+r)*5;c?x.lineTo(c,yy):x.moveTo(c,yy)}x.stroke()}
  if(!st)return;const dt=Math.min(.15,(performance.now()-stT)/1000);
  st.arena.inseln.forEach((s,i)=>island(s[0],s[1],s[2],i));
  for(const p of st.pick){const bob=Math.sin(t*3+p[1])*2;x.save();x.translate(p[1],p[2]+bob);
    if(p[0]==='a'){x.fillStyle='#8a5a2b';x.fillRect(-11,-9,22,18);x.fillStyle='#d9a441';x.fillRect(-11,-2,22,4);x.fillStyle='#222';x.beginPath();x.arc(0,0,5,0,7);x.fill()}
    else{x.fillStyle='#e5484d';x.beginPath();x.moveTo(0,10);x.bezierCurveTo(-18,-4,-8,-16,0,-6);x.bezierCurveTo(8,-16,18,-4,0,10);x.fill()}x.restore()}
  for(const sh of st.ships){const k=sh.i;if(sh.dead>0)continue;const tr=trail[k]=trail[k]||[];sh.px=sh.x+Math.cos(sh.a)*sh.v*dt;sh.py=sh.y+Math.sin(sh.a)*sh.v*dt;sh.pa=sh.a+sh.w*dt;
    if(!tr.length||Math.hypot(tr[tr.length-1][0]-sh.px,tr[tr.length-1][1]-sh.py)>9){tr.push([sh.px,sh.py,t]);if(tr.length>14)tr.shift()}
    for(const q of tr){const a=Math.max(0,1-(t-q[2])/1.4);x.fillStyle='rgba(255,255,255,'+(.35*a)+')';x.beginPath();x.arc(q[0],q[1],3+4*(1-a),0,7);x.fill()}}
  for(const sh of st.ships){if(sh.dead>0)continue;ship(sh,st.farben[sh.i],me&&me.platz===sh.i,t)}
  const mine0=me&&st.ships.find(s=>s.i===me.platz);
  for(const b of st.balls){const bx=b[0]+b[2]*dt,by=b[1]+b[3]*dt;x.fillStyle='#1b1b1b';x.beginPath();x.arc(bx,by,5,0,7);x.fill();x.fillStyle='rgba(255,255,255,.6)';x.beginPath();x.arc(bx-1.5,by-1.5,1.6,0,7);x.fill()}
  const df=1/60;parts=parts.filter(p=>(p.l-=df)>0);for(const p of parts){p.x+=p.vx*df;p.y+=p.vy*df;p.vx*=.96;p.vy*=.96;const a=Math.max(0,p.l/p.m);
    if(p.k==='sink'){x.strokeStyle='rgba(255,255,255,'+a+')';x.lineWidth=2;x.beginPath();x.arc(p.x,p.y,4+3*(1-a),0,7);x.stroke()}
    else if(p.k==='boom'){x.fillStyle='rgba(230,230,230,'+(.5*a)+')';x.beginPath();x.arc(p.x,p.y,6+10*(1-a),0,7);x.fill()}
    else if(p.k==='hit'){x.fillStyle='rgba(255,'+(160+Math.floor(80*a))+',60,'+a+')';x.beginPath();x.arc(p.x,p.y,3+3*a,0,7);x.fill()}
    else{x.fillStyle='rgba(220,240,255,'+a+')';x.beginPath();x.arc(p.x,p.y,2.5,0,7);x.fill()}}
  if(mine0&&mine0.dead<=0){const ax=mine0.px,ay=mine0.py,ca=Math.cos(mine0.pa),sa=Math.sin(mine0.pa);x.save();x.strokeStyle='rgba(255,255,255,.55)';x.lineWidth=2;x.setLineDash([3,7]);x.beginPath();
    if(modus==='v'){x.moveTo(ax+ca*34,ay+sa*34);x.lineTo(ax+ca*190,ay+sa*190)}else{for(const q of [1,-1]){x.moveTo(ax-sa*q*30,ay+ca*q*30);x.lineTo(ax-sa*q*95,ay+ca*q*95)}}
    x.stroke();x.restore()}
  if(performance.now()-modusT<1400&&modusT){x.save();x.globalAlpha=Math.min(1,(1400-(performance.now()-modusT))/500);x.fillStyle='rgba(0,0,0,.45)';x.fillRect(W/2-170,H-70,340,44);x.fillStyle='#fff';x.font='bold 26px system-ui';x.textAlign='center';x.fillText(modus==='b'?'Breitseite ↔ links + rechts':'Bugkanone ↑ geradeaus',W/2,H-40);x.restore()}
  /* eigenes Schiff versenkt: Hinweis */
  const mine=mine0;if(mine&&mine.dead>0){x.fillStyle='rgba(0,0,0,.35)';x.fillRect(0,H/2-34,W,68);x.fillStyle='#fff';x.font='bold 34px system-ui';x.textAlign='center';x.fillText('Versenkt! Neues Schiff in '+Math.ceil(mine.dead)+' …',W/2,H/2+12)}}
function ui(){if(!st)return;const top=$('#top');const html=[];
  for(let i=0;i<4;i++){const seat=st.seats[i],sh=st.ships.find(s=>s.i===i);
    if(!seat){html.push('<div class="chip off" style="--c:'+st.farben[i]+'">frei</div>');continue}
    const hp=sh?('❤'.repeat(Math.max(0,sh.hp))+'<span style="opacity:.25">'+'❤'.repeat(Math.max(0,3-sh.hp))+'</span>'):'',am=sh?' ●'+sh.ammo:'',sc=sh?' <b>'+sh.score+'</b>':'';
    html.push('<div class="chip'+(me&&me.platz===i?' me':'')+'" style="--c:'+st.farben[i]+'"><b>'+(seat.bot?'🤖':'⚓')+'</b> '+seat.name.replace(/[<>&]/g,'')+sc+'<br>'+hp+am+'</div>')}
  top.innerHTML=html.join('');
  const m=$('#msg');let t='';const humans=st.seats.filter(s=>s&&!s.bot).length,count=st.seats.filter(Boolean).length;
  if(!me)t=st.status==='laeuft'?'':(st.frei?'Plätze frei: '+st.frei+'<small>Name eingeben und „Mitspielen“ · '+st.arena.name+' · Sieger: wer zuerst '+st.ziel+' Schiffe versenkt</small>':'Alle Plätze besetzt<small>Du schaust zu</small>');
  else if(st.status==='wartet')t='Piraten Jagd<small>Arena: '+st.arena.name+' · Sieger: wer zuerst '+st.ziel+' Schiffe versenkt · '+count+' von 4 Plätzen belegt'+(count<2?' – „Bot dazu“ oder auf Mitspieler warten':'')+'</small>'+(st.frei&&addr?'<small style="word-break:break-all">Mitspieler im WLAN öffnen: '+addr+'</small>':'');
  else if(st.status==='start')t='Anker lichten! '+Math.ceil(st.countdown)+'<small>Du bist '+['Rot','Blau','Gelb','Grün'][me.platz]+' · links/rechts lenken, OK feuert, hoch/runter wechselt den Schuss · Handy quer = größeres Bild</small>';
  else if(st.status==='ende')t='🏆 '+st.sieger+' gewinnt!<small>OK = Nochmal</small>';
  m.innerHTML=t;m.style.display=t?'grid':'none';
  const wait=me&&st.status==='wartet',end=me&&st.status==='ende';
  $('#bj').style.display=me?'none':'';$('#nm').style.display=me?'none':'';$('#bq').style.display=me?'':'none';$('#bx').style.display=me?'none':'';
  $('#bgo').style.display=wait&&count>=2?'':'none';$('#bbot').style.display=wait&&count<4?'':'none';$('#bbw').style.display=wait&&count>humans?'':'none';
  $('#bar').style.display=wait?'':'none';$('#bar').textContent='Arena: '+st.arena.name;$('#bn').style.display=end?'':'none';
  $('#pad').classList.toggle('show',!!playing());document.body.classList.toggle('playing',!!playing());focusBtn()}
async function poll(){let wait=me?33:150;
  try{steer=(keyR||padR)-(keyL||padL);const f=fire;fire=false;
    const r=me?await post('tick',Object.assign(auth(),{steer,fire:f,modus})):await (await fetch('zustand',{headers:GH})).json();
    if(r.error==='weg'){me=null}else if(r.status){st=r;stT=performance.now();evs()}}catch(e){wait=500}
  draw();ui();setTimeout(poll,wait)}
(function frame(){draw();requestAnimationFrame(frame)})();
window.PJ={state:()=>({me,st}),steer:(v)=>{keyL=v<0?1:0;keyR=v>0?1:0}};
poll();
</script></body></html>"""


def register(api):
    global _api
    _api = api

    def post_only(fn):
        def wrap(req):
            if req.method != 'POST':
                return ({'error': 'Nur per POST'}, 405)
            return fn(req.json if isinstance(req.json, dict) else {})
        return wrap

    def platz_pruefen(d):
        try:
            k = int(d.get('platz'))
        except (TypeError, ValueError):
            return None, None
        seat = S['seats'][k] if 0 <= k < 4 else None
        if seat is None or seat.get('bot') or seat['token'] != d.get('token'):
            return None, None
        return k, seat

    def beitreten(d):
        name = str(d.get('name') or 'Spieler').strip()[:16] or 'Spieler'
        with _lock:
            frei = [i for i, x in enumerate(S['seats']) if x is None]
            if not frei:                                       # ein Bot macht Platz
                bots = [i for i, x in enumerate(S['seats']) if x and x.get('bot')]
                if not bots:
                    return ({'error': 'Alle vier Plätze sind besetzt - du kannst zuschauen.'}, 409)
                S['seats'][bots[-1]] = None
                S['ships'].pop(bots[-1], None)
                frei = [bots[-1]]
            k = frei[0]
            if any(x and x['name'] == name and not x.get('bot') for x in S['seats']):
                name = name[:13] + ' 2'
            tok = '%016x' % random.getrandbits(64)
            S['seats'][k] = {'name': name, 'token': tok, 'last': time.time(), 'bot': False, 'steer': 0, 'fire_t': 0.0}
            if S['status'] in ('start', 'laeuft'):
                S['ships'][k] = _neues_schiff(k)
                S['ships'][k]['dead'] = 0.5
        _sicherstellen()
        return {'platz': k, 'token': tok, 'name': name}

    def tick(d):
        with _lock:
            k, seat = platz_pruefen(d)
            if seat is None:
                return {'error': 'weg'}
            seat['last'] = time.time()
            try:
                seat['steer'] = max(-1.0, min(1.0, float(d.get('steer') or 0)))
            except (TypeError, ValueError):
                seat['steer'] = 0
            if d.get('fire'):
                seat['fire_t'] = time.time()
                seat['modus'] = 'v' if d.get('modus') == 'v' else 'b'
            return _sicht(S)

    def los(d):
        with _lock:
            k, seat = platz_pruefen(d)
            if seat is None:
                return ({'error': 'weg'}, 403)
            if S['status'] == 'wartet' and sum(1 for x in S['seats'] if x) >= 2:
                _start_spiel(S, time.time())
        return {'ok': True}

    def bot(d):
        with _lock:
            k, seat = platz_pruefen(d)
            if seat is None:
                return ({'error': 'weg'}, 403)
            if S['status'] != 'wartet':
                return {'ok': False}
            if d.get('an'):
                frei = [i for i, x in enumerate(S['seats']) if x is None]
                if frei:
                    i = frei[0]
                    benutzt = {x['name'] for x in S['seats'] if x}
                    name = next((n for n in BOTNAMEN if n not in benutzt), 'Bot %d' % (i + 1))
                    S['seats'][i] = {'name': name, 'token': '', 'last': time.time(), 'bot': True, 'steer': 0, 'fire_t': 0.0}
            else:
                bots = [i for i, x in enumerate(S['seats']) if x and x.get('bot')]
                if bots:
                    S['seats'][bots[-1]] = None
        return {'ok': True}

    def arena(d):
        with _lock:
            k, seat = platz_pruefen(d)
            if seat is None:
                return ({'error': 'weg'}, 403)
            if S['status'] == 'wartet':
                S['arena'] = (S['arena'] + 1) % len(ARENEN)
        return {'ok': True}

    def verlassen(d):
        with _lock:
            k, seat = platz_pruefen(d)
            if seat is not None:
                S['seats'][k] = None
                S['ships'].pop(k, None)
        return {'ok': True}

    def nochmal(d):
        with _lock:
            k, seat = platz_pruefen(d)
            if seat is None:
                return ({'error': 'weg'}, 403)
            if S['status'] == 'ende':
                S.update(status='wartet', balls=[], pick=[], sieger='', ships={})
        return {'ok': True}

    def zustand(req):
        with _lock:
            return _sicht(S)

    def widget():
        with _lock:
            n = [x['name'] for x in S['seats'] if x and not x.get('bot')]
            if S['status'] in ('start', 'laeuft'):
                return {'icon': '🏴‍☠️', 'text': 'Piraten Jagd läuft', 'sub': '%d Schiffe auf See' % sum(1 for x in S['seats'] if x)}
            if n:
                return {'icon': '🏴‍☠️', 'text': 'Piraten Jagd: %s wartet' % n[0][:20], 'sub': 'Mitspielen: Erweiterungsliste -> Piraten Jagd öffnen'}
        siege = _api.get('siege', {}) or {}
        if siege:
            top = max(siege.items(), key=lambda kv: kv[1])
            return {'icon': '🏴‍☠️', 'text': 'Piraten Jagd', 'sub': 'Meiste Siege: %s (%d)' % top}
        return {'icon': '🏴‍☠️', 'text': 'Piraten Jagd', 'sub': 'Bis zu 4 Schiffe im Haus - jetzt starten'}

    api.route('index', lambda req: PAGE)
    for name, fn in (('beitreten', beitreten), ('tick', tick), ('los', los), ('bot', bot), ('arena', arena), ('verlassen', verlassen), ('nochmal', nochmal)):
        api.route(name, post_only(fn))
    api.route('zustand', zustand)
    api.route('siege', lambda req: _api.get('siege', {}) or {})
    api.widget('Piraten Jagd', widget, ttl=5, icon='🏴‍☠️')
