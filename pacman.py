# -*- coding: utf-8 -*-
"""TV Spielfilm: Echte Programmdaten, Sender & Abendprogramm (A-Z, Multi-Column Grid)."""

import urllib.request
import xml.etree.ElementTree as ET
import re
import html

EXT_ID = 'tv_spielfilm'
EXT_NAME = 'TV Spielfilm'
EXT_DESCRIPTION = 'Echtes TV-Programm: Jetzt & ab 20:00 Uhr (A-Z, Multi-Column Grid).'
EXT_LINKS = [('TV Zeitschrift öffnen', 'index')]
EXT_SETTINGS = []

_api = None

def _fetch_rss(url):
    """Lädt und parst TV Spielfilm RSS-Feeds inklusive Sender- und Zeitextraktion."""
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        items = []
        for item in root.findall('.//item'):
            raw_title = item.find('title').text if item.find('title') is not None else 'Kein Titel'
            desc_elem = item.find('description')
            pubDate_elem = item.find('pubDate')
            
            clean_desc = html.unescape(re.sub('<.*?>', '', desc_elem.text)) if desc_elem is not None else 'Keine Details verfügbar.'
            
            # Sender und Uhrzeit aus dem Titel extrahieren
            time_match = re.search(r'(\d{2}:\d{2})', raw_title)
            time_str = time_match.group(1) if time_match else (pubDate_elem.text[17:22] if pubDate_elem is not None and len(pubDate_elem.text) >= 22 else '--:--')
            
            # Sender filtern
            channel_str = 'TV'
            title_clean = raw_title
            parts = [p.strip() for p in raw_title.split('|')]
            if len(parts) >= 3:
                time_str = parts[0]
                channel_str = parts[1]
                title_clean = " | ".join(parts[2:])
            elif len(parts) == 2:
                channel_str = parts[0]
                title_clean = parts[1]

            items.append({
                'title': title_clean,
                'channel': channel_str,
                'desc': clean_desc,
                'time': time_str
            })
        return items
    except Exception:
        return []

def _render_cards(items, fallback_msg="Keine Sendungen gefunden."):
    """Sortiert die Liste alphabetisch nach Titel und generiert die HTML-Cards."""
    if not items:
        return f'<div class="card"><div class="card-body"><p>{fallback_msg}</p></div></div>'

    # Alphabetisch sortieren nach Titel (Groß-/Kleinschreibung ignorieren)
    sorted_items = sorted(items, key=lambda x: x['title'].lower())

    html_out = ""
    for item in sorted_items:
        search_blob = html.escape((item['title'] + ' ' + item['channel'] + ' ' + item['desc']).lower())
        html_out += f"""
        <div class="card" data-search="{search_blob}">
            <div class="card-header">
                <span class="channel-badge">{html.escape(item['channel'])}</span>
                <span class="time-badge">{html.escape(item['time'])} Uhr</span>
            </div>
            <div class="card-body">
                <h3>{html.escape(item['title'])}</h3>
                <details class="spoiler-details">
                    <summary>Details anzeigen</summary>
                    <p>{html.escape(item['desc'])}</p>
                </details>
            </div>
        </div>
        """
    return html_out

def register(api):
    global _api
    _api = api

    def get_live_page(request):
        # Alle relevanten Feeds abrufen
        tipps = _fetch_rss('https://www.tvspielfilm.de/tv-programm/rss/tipps.xml')
        jetzt = _fetch_rss('https://www.tvspielfilm.de/tv-programm/rss/jetzt.xml')
        primetime = _fetch_rss('https://www.tvspielfilm.de/tv-programm/rss/heute2015.xml')

        # Bereich 1: Jetzt im TV
        jetzt_html = _render_cards(jetzt, "Keine aktuellen Sendedaten verfügbar.")

        # Bereich 2: Alles ab 20:00 Uhr zusammenstellen, Duplikate filtern
        combined_evening = tipps + primetime + jetzt
        seen = set()
        abend_pool = []
        
        for item in combined_evening:
            if item['time'] >= '20:00' or item['time'].startswith('20:') or item['time'].startswith('21:') or item['time'].startswith('22:') or item['time'].startswith('23:'):
                identifier = (item['channel'], item['title'])
                if identifier not in seen:
                    seen.add(identifier)
                    abend_pool.append(item)

        if not abend_pool:
            abend_pool = tipps

        abend_html = _render_cards(abend_pool, "Keine Programmdaten für den Abend verfügbar.")

        page_content = f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>TV Spielfilm - Live</title>
<style>
  :root {{
    --primary-red: #e50914;
    --dark-bg: #10131a;
    --card-bg: #1a1f2c;
    --panel2: #222a3b;
    --border: #30394e;
    --text-main: #f1f3f8;
    --text-muted: #9da6b7;
    --accent-blue: #007acc;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; user-select: none; -webkit-user-select: none; }}
  body {{
    background-color: var(--dark-bg);
    color: var(--text-main);
    font-family: system-ui, sans-serif;
    padding-bottom: 40px;
  }}
  header {{
    background: linear-gradient(135deg, #b8000a, var(--primary-red));
    padding: 12px;
    text-align: center;
    box-shadow: 0 4px 10px rgba(0,0,0,0.5);
  }}
  header h1 {{ font-size: 18px; font-weight: 900; text-transform: uppercase; }}
  header p {{ font-size: 11px; color: #ffcccc; margin-top: 1px; }}
  
  .search-container {{
    padding: 10px 15px;
    background: var(--card-bg);
    border-bottom: 1px solid var(--border);
    max-width: 100%;
    margin: 0 auto;
  }}
  .search-input {{
    width: 100%;
    max-width: 600px;
    margin: 0 auto;
    display: block;
    padding: 9px 14px;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--panel2);
    color: #fff;
    font-size: 14px;
    outline: none;
  }}
  .search-input:focus {{ border-color: var(--primary-red); }}

  .nav-tabs {{
    display: flex; padding: 10px 15px; background: var(--card-bg); gap: 10px; border-bottom: 1px solid var(--border);
    justify-content: center;
  }}
  .tab {{
    flex: 1;
    max-width: 250px;
    background: var(--panel2); border: 1px solid var(--border); color: var(--text-main); padding: 8px 14px; border-radius: 20px; font-size: 13px; cursor: pointer; font-weight: 600; text-align: center;
  }}
  .tab.active {{ background: var(--primary-red); border-color: var(--primary-red); }}
  
  .container {{ padding: 15px; max-width: 1600px; margin: 0 auto; }}
  .tab-content {{ display: none; }}
  .tab-content.active {{ 
    display: grid; 
    grid-template-columns: 1fr;
    gap: 15px;
  }}

  /* Responsive Multi-Column Layout für Querformat / größere Bildschirme */
  @media (min-width: 768px) {{
    .tab-content.active {{
      grid-template-columns: repeat(2, 1fr);
    }}
  }}
  @media (min-width: 1024px) {{
    .tab-content.active {{
      grid-template-columns: repeat(3, 1fr);
    }}
  }}
  @media (min-width: 1400px) {{
    .tab-content.active {{
      grid-template-columns: repeat(4, 1fr);
    }}
  }}
  
  .card {{
    background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  .card-header {{
    background: var(--panel2); padding: 10px 15px; display: flex; justify-content: space-between; align-items: center; font-size: 13px; color: var(--text-muted); border-bottom: 1px solid var(--border);
  }}
  .channel-badge {{ background: var(--accent-blue); color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; text-transform: uppercase; }}
  .time-badge {{ background: var(--primary-red); color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }}
  .card-body {{ padding: 15px; }}
  .card-body h3 {{ font-size: 16px; margin-bottom: 8px; color: var(--text-main); }}
  
  .spoiler-details {{
    background: var(--panel2);
    border-radius: 8px;
    padding: 8px 12px;
    border: 1px solid var(--border);
  }}
  .spoiler-details summary {{
    cursor: pointer;
    font-size: 13px;
    color: #60a5fa;
    font-weight: 600;
  }}
  .spoiler-details p {{
    font-size: 13px;
    color: var(--text-muted);
    line-height: 1.4;
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid var(--border);
  }}
</style>
</head>
<body oncontextmenu="return false">

  <header>
    <h1>TV Spielfilm Live</h1>
    <p>Aktuelle Programmdaten & Abendprogramm (A-Z)</p>
  </header>

  <div class="search-container">
    <input type="text" id="searchInput" class="search-input" placeholder="🔍 Sendungen oder Sender filtern..." onkeyup="filterCards()">
  </div>

  <div class="nav-tabs">
    <button class="tab active" onclick="switchTab(event, 'jetzt')">⚡ Jetzt im TV</button>
    <button class="tab" onclick="switchTab(event, 'abend')">🌙 Ab 20:00 Uhr</button>
  </div>

  <div class="container">
    <div id="jetzt" class="tab-content active">{jetzt_html}</div>
    <div id="abend" class="tab-content">{abend_html}</div>
  </div>

  <script>
    "use strict";

    function switchTab(evt, tabId) {{
      document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
      document.getElementById(tabId).classList.add('active');
      evt.currentTarget.classList.add('active');
      filterCards();
    }}

    function filterCards() {{
      const query = document.getElementById('searchInput').value.toLowerCase();
      const activeTab = document.querySelector('.tab-content.active');
      const cards = activeTab.querySelectorAll('.card');

      cards.forEach(card => {{
        const text = card.getAttribute('data-search') || '';
        if (text.includes(query)) {{
          card.style.display = 'flex';
        }} else {{
          card.style.display = 'none';
        }}
      }});
    }}
  </script>
</body>
</html>
"""
        return page_content

    api.route('index', get_live_page)

def on_load():
    pass
