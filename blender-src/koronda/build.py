# Packs the park background, it-cat and walking-cat sprites and audio into koronda.html. python3 build.py <render-dir> <out-html>
import sys, io, base64, json, re, os
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
src, out = sys.argv[1], sys.argv[2]
art, layer = {}, {}
def enc(im, q=84, jpeg=False):
    b = io.BytesIO()
    if jpeg: im.convert('RGB').save(b, 'JPEG', quality=q, optimize=True, progressive=True); mt = 'jpeg'
    else: im.save(b, 'WEBP', quality=q, method=6); mt = 'webp'
    return f'data:image/{mt};base64,' + base64.b64encode(b.getvalue()).decode()
scene = json.load(open(f'{src}/scene.json'))

_bg = Image.open(f'{src}/bg.png').convert('RGBA'); art['bg'] = enc(Image.alpha_composite(Image.new('RGBA', _bg.size, (178, 214, 246, 255)), _bg), 82, True)
for name in ['oni_back', 'oni_front'] + [f'cat_{c}_{p}' for c in ('tora', 'shiro', 'kuro', 'saba') for p in 'abf']: art[name] = enc(Image.open(f'{src}/{name}.png').convert('RGBA'), 90)
def a64(p): return 'data:audio/mpeg;base64,' + base64.b64encode(open(p, 'rb').read()).decode()
aud = {k: a64(f'{HERE}/sfx/{k}.mp3') for k in ['step', 'turn', 'caught', 'touch', 'mora', 'meow', 'start']}
for k in ['bgm', 'win', 'lose', 'over', 'best']: aud[k] = a64(f'{HERE}/audio/{k}.mp3')
s = open(f'{HERE}/game.html', encoding='utf-8').read()
js = 'const ART=' + json.dumps(art, separators=(',', ':')) + ',LAYER=' + json.dumps(layer) + ',SCENE=' + json.dumps(scene) + ';'
s, n = re.subn(r'/\*ART\*/.*?/\*/ART\*/', lambda m: '/*ART*/' + js + '/*/ART*/', s, flags=re.S); assert n == 1
ja = 'const AUD=' + json.dumps(aud, separators=(',', ':')) + ';'
s, n = re.subn(r'/\*AUDIO\*/.*?/\*/AUDIO\*/', lambda m: '/*AUDIO*/' + ja + '/*/AUDIO*/', s, flags=re.S); assert n == 1
open(out, 'w', encoding='utf-8').write(s)
print('art', len(js) // 1024, 'KB  audio', len(ja) // 1024, 'KB  total', len(s) // 1024, 'KB')
