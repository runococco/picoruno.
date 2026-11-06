# Packs renders + audio into bento.html (ART/AUDIO markers in game.html).
# python3 build.py <render-dir> <out-html>
import sys, io, base64, json, re, os
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
src, out = sys.argv[1], sys.argv[2]
PIECES = ['tomato','broccoli','karaage','octo','potesara','tamago','salmon','wiener','ebi','hamburg','rice22','rice23','karaage3']
SIZES = [(3,3),(4,3),(4,4),(5,4),(5,5)]
def url(name, scale=1.0, q=84, mode='webp'):
    im = Image.open(f'{src}/{name}')
    if scale != 1.0: im = im.resize((round(im.width*scale), round(im.height*scale)), Image.LANCZOS)
    b = io.BytesIO()
    if mode == 'jpeg': im.convert('RGB').save(b, 'JPEG', quality=q, optimize=True, progressive=True); mt = 'jpeg'
    else: im.save(b, 'WEBP', quality=q, method=6); mt = 'webp'
    return f'data:image/{mt};base64,' + base64.b64encode(b.getvalue()).decode()
art = {}
for p in PIECES: art['p_'+p] = url(f'p_{p}.png', 0.85, 86)
for w,h in SIZES:
    art[f'box{w}x{h}'] = url(f'box{w}x{h}.png', 0.7, 82)
    art[f'lid{w}x{h}'] = url(f'lid{w}x{h}.png', 0.7, 82)
art['table'] = url('table.png', 1.0, 80, 'jpeg')
def a64(path): return 'data:audio/mpeg;base64,' + base64.b64encode(open(path,'rb').read()).decode()
aud = {k: a64(f'{HERE}/sfx/{k}.mp3') for k in ['pick','place','place2','turn','bad','lid','start','hint','drop']}
for k in ['bgm','clear','finish']: aud[k] = a64(f'{HERE}/audio/{k}.mp3')
s = open(f'{HERE}/game.html', encoding='utf-8').read()
js = 'const ART=' + json.dumps(art, separators=(',',':')) + ';'
s, n = re.subn(r'/\*ART\*/.*?/\*/ART\*/', lambda m: '/*ART*/' + js + '/*/ART*/', s, flags=re.S); assert n == 1
ja = 'const AUD=' + json.dumps(aud, separators=(',',':')) + ';'
s, n = re.subn(r'/\*AUDIO\*/.*?/\*/AUDIO\*/', lambda m: '/*AUDIO*/' + ja + '/*/AUDIO*/', s, flags=re.S); assert n == 1
open(out, 'w', encoding='utf-8').write(s)
print('art', len(js)//1024, 'KB  audio', len(ja)//1024, 'KB  total', len(s)//1024, 'KB')
