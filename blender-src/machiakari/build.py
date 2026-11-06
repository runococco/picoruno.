# Packs renders + audio into machiakari.html (ART/AUDIO markers in game.html).
# python3 build.py <render-dir> <out-html>
import sys, io, base64, json, re, os
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
src, out = sys.argv[1], sys.argv[2]
def url(name, scale=1.0, q=84):
    im = Image.open(f'{src}/{name}')
    if scale != 1.0: im = im.resize((round(im.width*scale), round(im.height*scale)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, 'WEBP', quality=q, method=6)
    return 'data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode()
art = {}
for t in ['cottage','tall','round','shop','tower']:
    for s in ['on','off']: art[f'h_{t}_{s}'] = url(f'h_{t}_{s}.png')
for k in ['pine0','pine1','round0','round1']: art['t_'+k] = url(f't_{k}.png', 1.0, 82)
art['island'] = url('island.png', 1.0, 82)
art['islandMeta'] = json.load(open(f'{src}/island.json'))
def a64(p): return 'data:audio/mpeg;base64,' + base64.b64encode(open(p,'rb').read()).decode()
aud = {k: a64(f'{HERE}/sfx/{k}.mp3') for k in ['on','off','start','undo','retry','spark','hint']}
for k in ['bgm','clear','finish']: aud[k] = a64(f'{HERE}/audio/{k}.mp3')
s = open(f'{HERE}/game.html', encoding='utf-8').read()
js = 'const ART=' + json.dumps(art, separators=(',',':')) + ';'
s, n = re.subn(r'/\*ART\*/.*?/\*/ART\*/', lambda m: '/*ART*/' + js + '/*/ART*/', s, flags=re.S); assert n == 1
ja = 'const AUD=' + json.dumps(aud, separators=(',',':')) + ';'
s, n = re.subn(r'/\*AUDIO\*/.*?/\*/AUDIO\*/', lambda m: '/*AUDIO*/' + ja + '/*/AUDIO*/', s, flags=re.S); assert n == 1
open(out, 'w', encoding='utf-8').write(s)
print('art', len(js)//1024, 'KB  audio', len(ja)//1024, 'KB  total', len(s)//1024, 'KB')
