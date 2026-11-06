# Packs the Blender sprites + audio into mikan.html. python3 build.py <render-dir> <out-html>
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
names = ['cat', 'mikan_skin', 'mikan_fruit', 'yuzu_skin', 'yuzu_fruit']
for t in ('mikan_strip', 'yuzu_strip'):
    im = Image.open(f'{src}/{t}.png').convert('RGBA'); im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS); art[t] = enc(im, 86)
for name in names:
    im = Image.open(f'{src}/{name}.png').convert('RGBA')
    sc = 1.0 if name != 'cat' else 0.9
    im = im.resize((max(1, round(im.width * sc)), max(1, round(im.height * sc))), Image.LANCZOS)
    art[name] = enc(im, 86); spr[name] = meta[name]
def a64(p): return 'data:audio/mpeg;base64,' + base64.b64encode(open(p, 'rb').read()).decode()
aud = {k: a64(f'{HERE}/sfx/{k}.mp3') for k in ['tick', 'tear', 'perfect', 'start', 'plate', 'next']}
for k in ['bgm', 'finish', 'hitokawa']: aud[k] = a64(f'{HERE}/audio/{k}.mp3')
s = open(f'{HERE}/game.html', encoding='utf-8').read()
js = 'const ART=' + json.dumps(art, separators=(',', ':')) + ',SPR=' + json.dumps(spr) + ';'
s, n = re.subn(r'/\*ART\*/.*?/\*/ART\*/', lambda m: '/*ART*/' + js + '/*/ART*/', s, flags=re.S); assert n == 1
ja = 'const AUD=' + json.dumps(aud, separators=(',', ':')) + ';'
s, n = re.subn(r'/\*AUDIO\*/.*?/\*/AUDIO\*/', lambda m: '/*AUDIO*/' + ja + '/*/AUDIO*/', s, flags=re.S); assert n == 1
open(out, 'w', encoding='utf-8').write(s)
print('art', len(js) // 1024, 'KB  audio', len(ja) // 1024, 'KB  total', len(s) // 1024, 'KB')
