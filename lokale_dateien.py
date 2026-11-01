# -*- coding: utf-8 -*-
"""Lokale Dateien: Eigene Videos über einen interaktiven Ordner-Manager auswählen und abspielen.
"""
import os
import re
import html
import json
import urllib.parse
import xbmcvfs

EXT_ID = 'lokale_dateien'
EXT_NAME = 'Lokale Dateien'
EXT_DESCRIPTION = 'Eigene Videos vom Gerät über einen interaktiven Ordner-Browser auswählen und abspielen.'
EXT_LINKS = [('Mediathek öffnen', 'index')]
EXT_SETTINGS = [
    {
        'key': 'ordner', 
        'label': 'Medien-Ordner (optional manuell)', 
        'type': 'text', 
        'default': '', 
        'hint': 'Wird automatisch über den Ordner-Manager gesetzt oder kann hier eingetragen werden.'
    }
]

EXTENSIONS = ('.mp4', '.mkv', '.avi', '.mov', '.m4v', '.webm', '.flv', '.ts')
_api = None

def _get_config_path():
    try:
        profile = xbmcvfs.translatePath('special://profile/addon_data/plugin.video.moviescout/lokale_dateien_config.json')
        os.makedirs(os.path.dirname(profile), exist_ok=True)
        return profile
    except Exception:
        return 'lokale_dateien_config.json'

def _get_saved_root():
    root = str(_api.get('ordner') or '').strip()
    if not root or not os.path.isdir(root):
        try:
            cfg = _get_config_path()
            if os.path.exists(cfg):
                with open(cfg, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    root = data.get('ordner', '').strip()
        except Exception:
            pass
    return root if root and os.path.isdir(root) else ''

def _save_root(path):
    try:
        cfg = _get_config_path()
        with open(cfg, 'w', encoding='utf-8') as f:
            json.dump({'ordner': path}, f, ensure_ascii=False)
    except Exception:
        pass

def register(api):
    global _api
    _api = api

    def browse_route(req):
        path = req.query.get('path', '')
        if not path:
            roots = []
            if os.name == 'nt':
                import string
                for letter in string.ascii_uppercase:
                    drive = f"{letter}:\\"
                    if os.path.exists(drive):
                        roots.append({'name': f"Festplatte {drive}", 'path': drive})
            else:
                common_paths = [
                    ('/storage/emulated/0', 'Interner Speicher (Android)'),
                    ('/sdcard', 'SD-Card'),
                    (os.path.expanduser('~'), 'Benutzer-Verzeichnis (~)') ,
                    ('/media', 'Medien (/media)'),
                    ('/', 'Root (/)')
                ]
                for p, name in common_paths:
                    if os.path.exists(p) and os.path.isdir(p):
                        roots.append({'name': name, 'path': p})
            return {'directories': roots, 'current': ''}

        path = os.path.realpath(path)
        if not os.path.isdir(path):
            return {'error': 'Ungültiger Pfad'}

        dirs = []
        try:
            for entry in sorted(os.listdir(path)):
                full = os.path.join(path, entry)
                if os.path.isdir(full):
                    if entry.startswith('.'):
                        continue
                    dirs.append({'name': entry, 'path': full})
        except Exception as e:
            return {'error': str(e)}

        return {'directories': dirs, 'current': path}

    def set_root_route(req):
        path = req.query.get('path', '')
        if not path:
            _save_root('')
            return {'success': True}
        if os.path.isdir(path):
            _save_root(path)
            return {'success': True, 'path': path}
        return {'success': False, 'error': 'Ungültiger Ordner'}

    def media_list_route(req):
        root = _get_saved_root()
        if not root:
            return {'folders': [], 'files': []}
        sub = req.query.get('sub', '')
        target = os.path.realpath(os.path.join(root, sub))
        if os.path.commonpath([root, target]) != root:
            return {'folders': [], 'files': []}

        folders, files = [], []
        try:
            for entry in sorted(os.listdir(target)):
                full = os.path.join(target, entry)
                rel = os.path.relpath(full, root).replace(os.sep, '/')
                if os.path.isdir(full):
                    if not entry.startswith('.'):
                        folders.append({'name': entry, 'rel': rel})
                elif os.path.isfile(full) and entry.lower().endswith(EXTENSIONS):
                    size_mb = os.path.getsize(full) / (1024 * 1024)
                    files.append({'name': entry, 'path': full, 'size': f'{size_mb:.1f} MB'})
        except Exception:
            pass
        return {'folders': folders, 'files': files}

    def stream_route(req):
        fpath = req.query.get('f', '')
        if not fpath or not os.path.isfile(fpath):
            return ({'error': 'Datei nicht gefunden'}, 404)
        if not fpath.lower().endswith(EXTENSIONS):
            return ({'error': 'Dateiformat nicht erlaubt'}, 403)
        
        def iterfile():
            with open(fpath, 'rb') as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    yield chunk
        return iterfile()

    def seite(req):
        current_root = _get_saved_root()
        display_root_style = 'none' if current_root else 'block'
        display_media_style = 'block' if current_root else 'none'
        safe_current_root = html.escape(current_root)

        return """<!doctype html>
        <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
        <title>Lokale Dateien</title>
        <style>
            body { background: #10131a; color: #eee; font: 16px system-ui; margin: 0; padding: 20px; max-width: 900px; margin: auto; }
            h1 { font-size: 1.5rem; margin-bottom: 5px; }
            .card { background: #1a1f2c; padding: 16px; border-radius: 10px; margin-bottom: 16px; border: 1px solid #2a324a; }
            .btn { background: #ff007f; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: bold; border: none; cursor: pointer; display: inline-block; }
            .btn:hover { background: #e0006f; }
            .btn-sec { background: #2a324a; color: white; }
            .btn-sec:hover { background: #3a4463; }
            .grid { display: flex; flex-direction: column; gap: 8px; }
            .item { background: #22293d; padding: 12px 16px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; text-decoration: none; color: #eee; cursor: pointer; }
            .item:hover { background: #2a324a; }
            .path-bar { font-family: monospace; background: #10131a; padding: 10px; border-radius: 4px; color: #8ab4ff; margin-bottom: 12px; word-break: break-all; }
        </style>
        <h1>📂 Lokale Dateien & Ordner-Manager</h1>
        <p style="color: #aaa; margin-bottom: 20px;">Wähle deinen Medien-Ordner aus oder spiele vorhandene Videos ab.</p>

        <div class="card" id="selectorCard" style="display: """ + display_root_style + """;">
            <h3>🗂️ Ordner auf dem Gerät auswählen</h3>
            <p style="font-size: 0.9rem; color: #aaa;">Klicke dich durch das Dateisystem deines Geräts und wähle den gewünschten Film-Ordner aus:</p>
            <div class="path-bar" id="currentBrowsePath">Lade Speicherorte...</div>
            <div class="grid" id="browseList"></div>
            <div style="margin-top: 15px; display: flex; gap: 10px; flex-wrap: wrap;">
                <button class="btn" id="selectBtn" onclick="confirmFolder()" style="display:none;">✅ Diesen Ordner als Medien-Ordner festlegen</button>
                <button class="btn btn-sec" onclick="loadDirs('')" id="homeBtn" style="display:none;">🏠 Zu den Speicher-Roots</button>
            </div>
        </div>

        <div class="card" id="mediaCard" style="display: """ + display_media_style + """;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <strong>Aktiver Ordner:</strong>
                <button class="btn btn-sec" style="padding: 6px 12px; font-size: 0.85rem;" onclick="changeFolder()">🔄 Anderen Ordner wählen</button>
            </div>
            <div class="path-bar">""" + safe_current_root + """</div>
            <div class="grid" id="mediaList">Lade Mediendateien...</div>
        </div>

        <script>
        let selectedPath = "";
        let activeRoot = """ + json.dumps(current_root) + """;

        function loadDirs(path) {
            fetch('/api/x/lokale_dateien/browse?path=' + encodeURIComponent(path))
                .then(r => r.json())
                .then(data => {
                    if(data.error) {
                        alert(data.error);
                        return;
                    }
                    let list = document.getElementById('browseList');
                    let pathBar = document.getElementById('currentBrowsePath');
                    let selectBtn = document.getElementById('selectBtn');
                    let homeBtn = document.getElementById('homeBtn');
                    
                    pathBar.textContent = data.current || "Speicher-Roots auf dem Gerät";
                    homeBtn.style.display = data.current ? 'inline-block' : 'none';
                    
                    if(data.current) {
                        selectedPath = data.current;
                        selectBtn.style.display = 'inline-block';
                    } else {
                        selectedPath = "";
                        selectBtn.style.display = 'none';
                    }

                    let htmlContent = "";
                    if(data.current) {
                        let parentPath = data.current.split('/').slice(0, -1).join('/');
                        if(!parentPath && data.current.includes('\\\\')) {
                            parentPath = data.current.substring(0, data.current.lastIndexOf('\\\\'));
                        }
                        htmlContent += '<div class="item" onclick="loadDirs(\\\'' + parentPath.replace(/\\\\/g, '\\\\\\\\') + '\\\')">📁 <strong>.. (Übergeordneter Ordner)</strong></div>';
                    }

                    data.directories.forEach(d => {
                        let safePath = d.path.replace(/\\\\/g, '\\\\\\\\');
                        htmlContent += '<div class="item" onclick="loadDirs(\\\'' + safePath + '\\\')">📁 ' + d.name + '</div>';
                    });

                    if(data.directories.length === 0 && data.current) {
                        htmlContent += '<div style="padding: 10px; color: #888;">Keine Unterordner in diesem Verzeichnis. Du kannst diesen Ordner trotzdem auswählen!</div>';
                    }

                    list.innerHTML = htmlContent;
                });
        }

        function confirmFolder() {
            if(!selectedPath) return;
            fetch('/api/x/lokale_dateien/set_root?path=' + encodeURIComponent(selectedPath))
                .then(r => r.json())
                .then(data => {
                    if(data.success) {
                        location.reload();
                    } else {
                        alert("Fehler beim Speichern des Ordners.");
                    }
                });
        }

        function changeFolder() {
            fetch('/api/x/lokale_dateien/set_root?path=')
                .then(() => {
                    document.getElementById('selectorCard').style.display = 'block';
                    document.getElementById('mediaCard').style.display = 'none';
                    loadDirs('');
                });
        }

        function loadMediaFiles(subpath) {
            let url = '/api/x/lokale_dateien/media_list?sub=' + encodeURIComponent(subpath || '');
            fetch(url)
                .then(r => r.json())
                .then(data => {
                    let list = document.getElementById('mediaList');
                    let htmlContent = "";
                    
                    if(subpath) {
                        let parentPath = subpath.split('/').slice(0, -1).join('/');
                        htmlContent += '<div class="item" onclick="loadMediaFiles(\\\'' + parentPath + '\\\')">📁 <strong>.. (Zurück)</strong></div>';
                    }

                    (data.folders || []).forEach(f => {
                        htmlContent += '<div class="item" onclick="loadMediaFiles(\\\'' + f.rel + '\\\')">📁 ' + f.name + '</div>';
                    });

                    (data.files || []).forEach(file => {
                        let streamUrl = '/api/x/lokale_dateien/stream?f=' + encodeURIComponent(file.path);
                        htmlContent += '<div class="item" style="display: flex; justify-content: space-between; align-items: center;"><div>🎬 <strong>' + file.name + '</strong><br><small style="color:#8ab4ff">' + file.size + '</small></div><a class="btn" href="' + streamUrl + '" target="_blank">Abspielen</a></div>';
                    });

                    if((data.folders || []).length === 0 && (data.files || []).length === 0) {
                        htmlContent = '<p style="color:#aaa;">Keine unterstützten Mediendateien in diesem Ordner gefunden.</p>';
                    }

                    list.innerHTML = htmlContent;
                });
        }

        if(activeRoot) {
            loadMediaFiles('');
        } else {
            loadDirs('');
        }
        </script>
        """

    api.route('browse', browse_route)
    api.route('set_root', set_root_route)
    api.route('media_list', media_list_route)
    api.route('stream', stream_route)
    api.route('index', seite)
