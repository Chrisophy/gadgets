# -*- coding: utf-8 -*-
# Gerät
# IT('s) Possible 
# 2026.11.08
"""MovieScout-Erweiterung (mitgeliefert): Gerät – zeigt die Hardware-Ausstattung des Geräts, auf dem MovieScout läuft.

Kachel „Gerät“ auf der Startseite (und im Bildschirmschoner) und die Seite „Mein Gerät“ (Erweiterungsliste -> Gerät).
Die Seite zeigt Gerät, Prozessor, Arbeitsspeicher, Speicherplatz, Android-Version, Bildschirm, Video-/Ton-Formate
(mit Hardware-Beschleunigung), Widevine und Netz. Mit „Kopieren“ lässt sich alles als Text weitergeben (z. B. für Fehlermeldungen).
Alles wird nur angezeigt – nichts verlässt das Gerät.
"""
import json
from html import escape
from pathlib import Path

EXT_ID = 'geraet'
EXT_NAME = 'Gerät'
EXT_DESCRIPTION = 'Zeigt die Hardware deines Geräts: Chipset, Kerne, Arbeitsspeicher, Speicher, Bildschirm, Videoformate, Widevine.'
EXT_LINKS = [('Mein Gerät', 'index')]

_api = None


def _gb(n):
    n = float(n or 0)
    if n <= 0:
        return ''
    return ('%.1f GB' % (n / 1024 ** 3)).replace('.', ',') if n >= 1024 ** 3 else '%d MB' % round(n / 1024 ** 2)


def _version():
    """Versionsnummer der App (VERSION-Datei neben dem Ordner engine/)."""
    try:
        from engine import hwinfo
        return (Path(hwinfo.__file__).resolve().parent.parent / 'VERSION').read_text(encoding='utf-8').strip()
    except Exception:                                    # noqa: BLE001
        return ''


def _data():
    from engine import hwinfo
    try:
        from kodi_runtime import paths
        data_dir = paths.DATA_DIR
    except Exception:                                    # noqa: BLE001
        data_dir = None
    return hwinfo.collect(_version(), data_dir)


def _sections(d):
    """Abschnitte [(Titel, [(Name, Wert), …]), …] - nur Zeilen mit Inhalt."""
    dv, cpu, ram, st, os_ = d['device'], d['cpu'], d['ram'], d['storage'], d['os']
    model = ' '.join(x for x in (dv['brand'], dv['model']) if x)
    if dv['brand'] and dv['model'] and dv['model'].lower().startswith(dv['brand'].lower()):
        model = dv['model']
    sec = []
    sec.append(('Gerät', [
        ('Modell', model), ('Hersteller', dv['manufacturer'] if dv['manufacturer'].lower() != dv['brand'].lower() else ''),
        ('Bauart', 'Fernseher / TV-Box' if dv['tv'] else ('Handy / Tablet' if d['android'] else 'Computer')),
        ('Plattform', dv['board']),
    ]))
    ghz = ('%.2f GHz' % cpu['ghz']).replace('.', ',') if cpu['ghz'] else ''
    sec.append(('Prozessor', [
        ('Chipset', cpu['chipset']), ('Kerne', str(cpu['cores']) if cpu['cores'] else ''), ('Höchster Takt', ghz),
        ('Architektur', cpu['arch']), ('Unterstützte Befehlssätze', ', '.join(cpu['abis'])),
        ('Grafik', d['gpu']['egl'] or d['gpu']['vulkan']),
    ]))
    used = ''
    if ram['total'] and ram['free']:
        used = '%d %% belegt' % round(100 * (ram['total'] - ram['free']) / ram['total'])
    mem = [('Arbeitsspeicher (RAM)', _gb(ram['total'])), ('Davon frei', (_gb(ram['free']) + ('  ·  ' + used if used else '')) if ram['free'] else '')]
    for key, name in (('shared', 'Interner Speicher'), ('app', 'Speicher der App')):
        s = st.get(key)
        if s:
            mem.append((name, '%s gesamt  ·  %s frei' % (_gb(s['total']), _gb(s['free']))))
            if key == 'shared':
                break
    sec.append(('Speicher', mem))
    up = d['uptime']
    upt = ('%d Std. %d Min.' % (up // 3600, up % 3600 // 60) if up >= 3600 else '%d Min.' % (up // 60)) if up else ''
    sec.append(('System', [
        ('Android', ('Android %s' % dv['android'] + (' (API %s)' % dv['sdk'] if dv['sdk'] else '')) if dv['android'] else ''),
        ('Sicherheits-Patch', dv['patch']), ('Systemstand', dv['build']),
        ('Betriebssystem', os_['platform'] if not d['android'] else ''), ('Kernel', os_['kernel']),
        ('Läuft seit Neustart', upt), ('MovieScout', d['app']['version']), ('Python (Engine)', os_['python']),
    ]))
    b = d.get('battery')
    if b:
        sec.append(('Akku', [('Ladestand', '%d %%' % b['percent']), ('Status', 'wird geladen' if b['charging'] else 'Batteriebetrieb')]))
    return [(t, [(k, v) for k, v in rows if v]) for t, rows in sec if any(v for _, v in rows)]


_CSS = (
    ':root{--bg:#0f141b;--fg:#e8edf3;--mut:#93a1b3;--card:#18202b;--acc:#4da3ff;--ok:#4cc38a;--no:#e5645c}'
    '@media(prefers-color-scheme:light){:root{--bg:#f4f6f9;--fg:#18202b;--mut:#5d6b7c;--card:#fff;--acc:#1b6fd1;--ok:#1a8a56;--no:#c0392b}}'
    '*{box-sizing:border-box}body{margin:0;padding:18px 16px 70px;background:var(--bg);color:var(--fg);font:16px/1.45 system-ui,sans-serif;max-width:820px;margin-inline:auto}'
    'h1{font-size:1.4rem;margin:.2em 0 .2em}h2{font-size:1.05rem;margin:1.5em 0 .4em;color:var(--acc)}'
    '.card{background:var(--card);border-radius:12px;padding:4px 14px}'
    '.r{display:flex;justify-content:space-between;gap:16px;padding:9px 0;border-bottom:1px solid rgba(128,128,128,.18)}'
    '.r:last-child{border-bottom:0}.r span{color:var(--mut);flex:0 0 42%}.r b{font-weight:600;text-align:right;word-break:break-word}'
    '.ok{color:var(--ok)}.no{color:var(--no)}.m{color:var(--mut);font-size:.9rem}'
    'button{font:inherit;padding:10px 18px;border-radius:10px;border:1px solid var(--mut);background:transparent;color:var(--fg);margin:22px 8px 0 0}'
    'button:focus{outline:3px solid var(--acc)}'
)

_JS = r'''
const $ = (id) => document.getElementById(id);
const put = (id, v, cls) => { const e = $(id); if (!e) return; e.textContent = v; e.className = cls || ''; };
const row = (box, name, val, cls) => { const r = document.createElement('div'); r.className = 'r'; const s = document.createElement('span'); s.textContent = name;
  const b = document.createElement('b'); b.textContent = val; if (cls) b.className = cls; r.append(s, b); $(box).append(r); return b; };
const SECTIONS = [];
function note(title, name, val) { let s = SECTIONS.find((x) => x[0] === title); if (!s) SECTIONS.push(s = [title, []]); s[1].push([name, val]); }

function screenInfo() {
  const w = Math.round(screen.width * (devicePixelRatio || 1)), h = Math.round(screen.height * (devicePixelRatio || 1));
  const big = Math.max(w, h), small = Math.min(w, h);
  const cls = big >= 7680 ? ' (8K)' : big >= 3800 ? ' (4K)' : big >= 2500 ? ' (WQHD)' : big >= 1900 ? ' (Full-HD)' : big >= 1200 ? ' (HD)' : '';
  const out = [['Auflösung', big + ' × ' + small + cls], ['Skalierung', String(Math.round((devicePixelRatio || 1) * 100) / 100) + '×'], ['Farbtiefe', (screen.colorDepth || '?') + ' Bit']];
  try { if (matchMedia('(dynamic-range: high)').matches) out.push(['HDR', 'ja']); else out.push(['HDR', 'nein / nicht gemeldet']); } catch (e) {}
  try { if (matchMedia('(color-gamut: p3)').matches) out.push(['Farbraum', 'Wide Gamut (P3)']); } catch (e) {}
  return out;
}

async function codec(name, mime, vid) {
  const cap = navigator.mediaCapabilities;
  const tests = vid ? [[3840, 2160, '4K'], [1920, 1080, 'bis Full-HD']] : [[0, 0, '']];
  let best = null;
  for (const [w, h, lab] of tests) {
    try {
      let ok = false, eff = false;
      if (cap && cap.decodingInfo) {
        const cfg = vid ? { type: 'file', video: { contentType: mime, width: w, height: h, bitrate: w > 2000 ? 25e6 : 8e6, framerate: 30 } }
                        : { type: 'file', audio: { contentType: mime, channels: 2, bitrate: 192000, samplerate: 48000 } };
        const r = await cap.decodingInfo(cfg); ok = !!r.supported; eff = !!r.powerEfficient;
      } else { ok = !!(window.MediaSource && MediaSource.isTypeSupported(mime)) || !!document.createElement('video').canPlayType(mime); }
      if (ok) { best = [lab, eff]; break; }
    } catch (e) {}
  }
  if (!best) return [name, 'nicht unterstützt', 'no'];
  const t = [best[0], vid ? (best[1] ? 'Hardware' : 'Software') : ''].filter(Boolean).join(' · ');
  return [name, t || 'ja', 'ok'];
}

async function widevine() {
  try { const a = window.MovieScoutApp; if (a && a.nativeWidevineLevel) { const l = String(a.nativeWidevineLevel() || '').toUpperCase(); if (l) return l === 'L1' ? 'Hardware (L1) – höchste Stufe' : l === 'L2' ? 'Hardware, eingeschränkt (L2)' : l === 'L3' ? 'nur Software (L3)' : 'nicht vorhanden'; } } catch (e) {}
  if (!window.isSecureContext || !navigator.requestMediaKeySystemAccess) return 'nicht prüfbar';
  for (const [rob, txt] of [['HW_SECURE_ALL', 'Hardware (L1) – höchste Stufe'], ['HW_SECURE_CRYPTO', 'Hardware, eingeschränkt (L2)'], ['SW_SECURE_CRYPTO', 'nur Software (L3)']]) {
    try { await Promise.race([navigator.requestMediaKeySystemAccess('com.widevine.alpha', [{ initDataTypes: ['cenc'], videoCapabilities: [{ contentType: 'video/mp4; codecs="avc1.42E01E"', robustness: rob }] }]), new Promise((_, no) => setTimeout(no, 2500))]); return txt; } catch (e) {}
  }
  return 'nicht vorhanden';
}

async function boot() {
  for (const [n, v] of screenInfo()) { row('sec-screen', n, v); note('Bildschirm', n, v); }
  try { const c = document.createElement('canvas').getContext('webgl'); const x = c && c.getExtension('WEBGL_debug_renderer_info');
    if (x) { const g = c.getParameter(x.UNMASKED_RENDERER_WEBGL); if (g) { row('sec-screen', 'Grafikchip', g); note('Bildschirm', 'Grafikchip', g); } } } catch (e) {}
  const V = [['H.264 (AVC)', 'video/mp4; codecs="avc1.640033"', 1], ['H.265 (HEVC)', 'video/mp4; codecs="hvc1.1.6.L153.B0"', 1], ['VP9', 'video/webm; codecs="vp09.00.50.08"', 1],
    ['AV1', 'video/mp4; codecs="av01.0.12M.08"', 1], ['AAC', 'audio/mp4; codecs="mp4a.40.2"', 0], ['Dolby Digital (AC-3)', 'audio/mp4; codecs="ac-3"', 0],
    ['Dolby Digital Plus (E-AC-3)', 'audio/mp4; codecs="ec-3"', 0], ['Opus', 'audio/webm; codecs="opus"', 0]];
  for (const [n, m, v] of V) { const [a, b, c] = await codec(n, m, v); row('sec-codec', a, b, c); note('Video & Ton', a, b); }
  const w = await widevine(); row('sec-codec', 'Widevine (geschützte Streams)', w, /Hardware/.test(w) ? 'ok' : ''); note('Video & Ton', 'Widevine', w);
  const nc = navigator.connection || {};
  const net = [['Verbindung', ({ wifi: 'WLAN', ethernet: 'LAN', cellular: 'Mobilfunk' })[nc.type] || (nc.effectiveType ? 'online (' + nc.effectiveType + ')' : (navigator.onLine ? 'online' : 'offline'))]];
  if (nc.downlink) net.push(['Geschätzte Geschwindigkeit', nc.downlink + ' Mbit/s']);
  if (nc.rtt) net.push(['Antwortzeit', nc.rtt + ' ms']);
  for (const [n, v] of net) { row('sec-net', n, v); note('Netz', n, v); }
  if (!$('sec-akku') ) return;
  try { const b = await navigator.getBattery(); $('akkuw').hidden = false;
    row('sec-akku', 'Ladestand', Math.round(b.level * 100) + ' %'); row('sec-akku', 'Status', b.charging ? 'wird geladen' : 'Batteriebetrieb'); } catch (e) {}
}

function text() {
  let t = 'MovieScout – Gerät\n';
  for (const [title, rows] of SERVER.concat(SECTIONS)) { t += '\n' + title + '\n'; for (const [k, v] of rows) t += '  ' + k + ': ' + v + '\n'; }
  return t;
}
function copy() {
  const t = text(), done = () => { $('cp').textContent = 'Kopiert ✓'; setTimeout(() => { $('cp').textContent = 'Alles kopieren'; }, 2500); };
  const fb = () => { const a = document.createElement('textarea'); a.value = t; document.body.append(a); a.select(); try { document.execCommand('copy'); done(); } catch (e) { $('cp').textContent = 'Kopieren nicht möglich'; } a.remove(); };
  if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(t).then(done, fb); else fb();
}
$('cp').onclick = copy;
boot();
'''


def _page(req):
    d = _data()
    secs = _sections(d)

    def block(title, rows, box=''):
        body = ''.join('<div class="r"><span>%s</span><b>%s</b></div>' % (escape(k), escape(v)) for k, v in rows)
        return '<h2>%s</h2><div class="card"%s>%s</div>' % (escape(title), (' id="%s"' % box) if box else '', body)

    html = ''.join(block(t, r) for t, r in secs)
    if not d.get('battery'):
        html += '<div id="akkuw" hidden><h2>Akku</h2><div class="card" id="sec-akku"></div></div>'
    html += '<h2>Bildschirm</h2><div class="card" id="sec-screen"></div>'
    html += '<h2>Video &amp; Ton</h2><div class="card" id="sec-codec"></div>'
    html += '<p class="m">„Hardware“ heißt: Der Chip des Geräts entschlüsselt das Format selbst – das läuft flüssig und spart Akku. „Software“ geht auch, belastet aber den Prozessor (bei 4K auf schwachen Geräten kann es ruckeln).</p>'
    html += '<h2>Netz</h2><div class="card" id="sec-net"></div>'
    server = json.dumps(secs, ensure_ascii=False).replace('</', '<\\/')
    return ('<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Mein Gerät</title><style>' + _CSS + '</style><h1>📱 Mein Gerät</h1>'
            '<p class="m">Was in diesem Gerät steckt – und was es abspielen kann.</p>' + html +
            '<button id="cp">Alles kopieren</button><button onclick="location.reload()">Neu lesen</button>'
            '<script>const SERVER=' + server + ';' + _JS + '</script></html>')


def register(api):
    global _api
    _api = api

    def widget():
        try:
            d = _data()
        except Exception:                                # noqa: BLE001
            return None
        ram, cpu, dv = d['ram'], d['cpu'], d['device']
        text = _gb(ram['total']).replace(',0 ', ' ') + ' RAM' if ram['total'] else (cpu['chipset'] or 'Gerät')
        sub = ' · '.join(x for x in ((cpu['chipset'] or '').strip(), ('%d Kerne' % cpu['cores']) if cpu['cores'] else '') if x)
        lines = []
        model = ' '.join(x for x in (dv['brand'], dv['model']) if x)
        if model:
            lines.append(model)
        if ram['free']:
            lines.append('RAM frei: ' + _gb(ram['free']))
        sh = d['storage'].get('shared') or d['storage'].get('app')
        if sh:
            lines.append('Speicher frei: ' + _gb(sh['free']) + ' von ' + _gb(sh['total']))
        if dv['android']:
            lines.append('Android ' + dv['android'])
        return {'text': text, 'sub': sub, 'lines': lines}

    api.route('index', _page)
    api.route('daten', lambda req: _data())
    api.widget('Gerät', widget, ttl=120, icon='📱')
