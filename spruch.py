# -*- coding: utf-8 -*-
"""Spruch des Tages: ein Gedanke zum Tag als Kachel (jeden Tag ein anderer) - mit eigenen Sprüchen erweiterbar.

Die mitgelieferten Sprüche sind Klassiker und Sprichwörter. Eigene Sprüche trägst du in den Einstellungen ein
(einer pro Zeile, am Ende gern „ - Name“). Mit „Nur eigene Sprüche“ kommen nur deine dran, z. B. Familiensprüche.
"""
from datetime import date

EXT_ID = 'spruch'
EXT_NAME = 'Spruch des Tages'
EXT_DESCRIPTION = 'Kachel mit einem Spruch pro Tag (Klassiker und Sprichwörter) - mit eigenen Sprüchen erweiterbar.'
EXT_SETTINGS = [
    {'key': 'eigene', 'label': 'Eigene Sprüche (einer pro Zeile)', 'type': 'textarea', 'default': '',
     'hint': 'z. B.  Wer rastet, der rostet. - Oma Gerda'},
    {'key': 'nur_eigene', 'label': 'Nur eigene Sprüche', 'type': 'bool', 'default': False},
]
SPRUECHE = [
    ('Habe Mut, dich deines eigenen Verstandes zu bedienen!', 'Immanuel Kant'),
    ('Der Mensch ist nur da ganz Mensch, wo er spielt.', 'Friedrich Schiller'),
    ('Es ist nicht genug zu wissen, man muss auch anwenden; es ist nicht genug zu wollen, man muss auch tun.', 'Johann Wolfgang von Goethe'),
    ('Man sieht nur mit dem Herzen gut. Das Wesentliche ist für die Augen unsichtbar.', 'Antoine de Saint-Exupéry'),
    ('Ohne Musik wäre das Leben ein Irrtum.', 'Friedrich Nietzsche'),
    ('Es gibt nichts Gutes, außer man tut es.', 'Erich Kästner'),
    ('Nichts ist so beständig wie der Wandel.', 'Heraklit'),
    ('Der Klügere gibt nach - eine traurige Wahrheit.', 'Marie von Ebner-Eschenbach'),
    ('Ein Buch ist ein Spiegel: Wenn ein Affe hineinschaut, kann kein Apostel heraussehen.', 'Georg Christoph Lichtenberg'),
    ('Es ist ein Brauch von alters her: Wer Sorgen hat, hat auch Likör.', 'Wilhelm Busch'),
    ('Wer kämpft, kann verlieren. Wer nicht kämpft, hat schon verloren.', 'Bertolt Brecht'),
    ('Wo man singt, da lass dich ruhig nieder, böse Menschen haben keine Lieder.', 'Johann Gottfried Seume'),
    ('Ich weiß, dass ich nichts weiß.', 'Sokrates'),
    ('Alles Gescheite ist schon gedacht worden; man muss nur versuchen, es noch einmal zu denken.', 'Johann Wolfgang von Goethe'),
    ('Morgenstund hat Gold im Mund.', 'Sprichwort'),
    ('Ohne Fleiß kein Preis.', 'Sprichwort'),
    ('Aller Anfang ist schwer.', 'Sprichwort'),
    ('Gut Ding will Weile haben.', 'Sprichwort'),
    ('Übung macht den Meister.', 'Sprichwort'),
    ('Lachen ist die beste Medizin.', 'Sprichwort'),
    ('Wer rastet, der rostet.', 'Sprichwort'),
    ('Aufgeschoben ist nicht aufgehoben.', 'Sprichwort'),
    ('In der Ruhe liegt die Kraft.', 'Sprichwort'),
    ('Ende gut, alles gut.', 'Sprichwort'),
    ('Wer wagt, gewinnt.', 'Sprichwort'),
    ('Geteilte Freude ist doppelte Freude.', 'Sprichwort'),
    ('Kleinvieh macht auch Mist.', 'Sprichwort'),
    ('Ein Lächeln kostet nichts und bringt viel.', 'Sprichwort'),
]
_api = None


def eigene(text):
    out = []
    for line in str(text or '').splitlines():
        line = line.strip()
        if not line:
            continue
        if ' - ' in line:
            s, a = line.rsplit(' - ', 1)
            out.append((s.strip(), a.strip()))
        else:
            out.append((line, ''))
    return out


def waehle(heute, eig, nur_eigene):
    pool = (eig if (eig and nur_eigene) else SPRUECHE + eig)
    return pool[heute.toordinal() % len(pool)]


def widget():
    s, a = waehle(date.today(), eigene(_api.get('eigene')), bool(_api.get('nur_eigene')))
    return {'icon': '💬', 'text': (a or 'Spruch des Tages')[:40], 'sub': s[:120]}


def register(api):
    global _api
    _api = api
    api.widget('Spruch des Tages', widget, ttl=1800, icon='💬')
    api.route('heute', lambda req: dict(zip(('spruch', 'autor'), waehle(date.today(), eigene(api.get('eigene')), bool(api.get('nur_eigene'))))))
