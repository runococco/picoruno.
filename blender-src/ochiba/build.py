# Packs the Blender sprites + audio into ochiba.html. python3 build.py <render-dir> <out-html>
import sys, io, base64, json, re, os
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
src, out = sys.argv[1], sys.argv[2]
meta = json.load(open(f'{src}/meta.json'))
art, spr = {}, {}
def enc(im, q=84, jpeg=False):
    b = io.BytesIO()
    if jpeg: im.convert('RGB').save(b, 'JPEG', quality=q, optimize=True, progressive=True); mt = 'jpeg'
    else: im.save(b, 'WEBP', quality=q, method=6); mt = 'webp'
    return f'data:image/{mt};base64,' + base64.b64encode(b.getvalue()).decode()
art['bg'] = enc(Image.open(f'{src}/bg.png'), 82, True)
SC = {'broom': .6, 'cat': .8, 'cat_awake': .8, 'branch': 1.0, 'imo': .6, 'yakiimo': .7, 'donguri': .45, 'kuri': .45, 'matsu': .45}
for name in ['momiji_r', 'momiji_o', 'momiji_y', 'ichou', 'sakura', 'kaki'] + list(SC):
    im = Image.open(f'{src}/{name}.png').convert('RGBA')
    sc = SC.get(name, .4)
    im = im.resize((max(1, round(im.width * sc)), max(1, round(im.height * sc))), Image.LANCZOS)
    art[name] = enc(im, 86); spr[name] = meta[name]
spr['fire'] = meta['fire']; spr['stones'] = meta['stones']
def a64(p): return 'data:audio/mpeg;base64,' + base64.b64encode(open(p, 'rb').read()).decode()
aud = {k: a64(f'{HERE}/sfx/{k}.mp3') for k in ['sweep1', 'sweep2', 'sweep3', 'swish', 'flutter', 'cat', 'crack1', 'crack2', 'start', 'pile']}
for k in ['bgm', 'finish', 'found', 'ready', 'wind']: aud[k] = a64(f'{HERE}/audio/{k}.mp3')
s = open(f'{HERE}/game.html', encoding='utf-8').read()
js = 'const ART=' + json.dumps(art, separators=(',', ':')) + ',SPR=' + json.dumps(spr) + ';'
s, n = re.subn(r'/\*ART\*/.*?/\*/ART\*/', lambda m: '/*ART*/' + js + '/*/ART*/', s, flags=re.S); assert n == 1
ja = 'const AUD=' + json.dumps(aud, separators=(',', ':')) + ';'
s, n = re.subn(r'/\*AUDIO\*/.*?/\*/AUDIO\*/', lambda m: '/*AUDIO*/' + ja + '/*/AUDIO*/', s, flags=re.S); assert n == 1
open(out, 'w', encoding='utf-8').write(s)
print('art', len(js) // 1024, 'KB  audio', len(ja) // 1024, 'KB  total', len(s) // 1024, 'KB')
