# Packs renders + audio into kamihikouki.html. python3 build.py <render-dir> <out-html>
import sys, io, base64, json, re, os
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
src, out = sys.argv[1], sys.argv[2]
meta = json.load(open(f'{src}/meta.json'))
SCALE = {'plane': 0.8, 'star': 0.9}
def url(name, scale=0.55, q=84):
    im = Image.open(f'{src}/{name}.png')
    im = im.resize((max(2, round(im.width*scale)), max(2, round(im.height*scale))), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, 'WEBP', quality=q, method=6)
    return 'data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode()
art = {k: url(k, SCALE.get(k, 1.0)) for k in meta}
def a64(p): return 'data:audio/mpeg;base64,' + base64.b64encode(open(p,'rb').read()).decode()
aud = {k: a64(f'{HERE}/sfx/{k}.mp3') for k in ['star','wind','crash','start','mile','tap']}
for k in ['bgm','land','best']: aud[k] = a64(f'{HERE}/audio/{k}.mp3')
s = open(f'{HERE}/game.html', encoding='utf-8').read()
js = 'const ART=' + json.dumps(art, separators=(',',':')) + ',META=' + json.dumps(meta, separators=(',',':')) + ';'
s, n = re.subn(r'/\*ART\*/.*?/\*/ART\*/', lambda m: '/*ART*/' + js + '/*/ART*/', s, flags=re.S); assert n == 1
ja = 'const AUD=' + json.dumps(aud, separators=(',',':')) + ';'
s, n = re.subn(r'/\*AUDIO\*/.*?/\*/AUDIO\*/', lambda m: '/*AUDIO*/' + ja + '/*/AUDIO*/', s, flags=re.S); assert n == 1
open(out, 'w', encoding='utf-8').write(s)
print('art', len(js)//1024, 'KB  audio', len(ja)//1024, 'KB  total', len(s)//1024, 'KB')
