# Packs the desk background, five washi paper tiles and audio into origami.html. python3 build.py <render-dir> <out-html>
import sys, io, base64, json, re, os
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
src, out = sys.argv[1], sys.argv[2]
def enc(im, q=84):
    b = io.BytesIO(); im.convert('RGB').save(b, 'JPEG', quality=q, optimize=True, progressive=True) if im.mode == 'RGB' else im.save(b, 'WEBP', quality=q, method=6)
    return f'data:image/{"jpeg" if im.mode == "RGB" else "webp"};base64,' + base64.b64encode(b.getvalue()).decode()
art = {'bg': enc(Image.open(f'{src}/bg.png').convert('RGB'), 80)}
for k in ['ichimatsu', 'seigaiha', 'sakura', 'shima', 'back']: art['pp_' + k] = enc(Image.open(f'{src}/pp_{k}.png').convert('RGB'), 86)
scene = {}
def a64(p): return 'data:audio/mpeg;base64,' + base64.b64encode(open(p, 'rb').read()).decode()
aud = {k: a64(f'{HERE}/sfx/{k}.mp3') for k in ['pick', 'fold', 'crease', 'undo', 'nope', 'match', 'star', 'start']}
for k in ['bgm', 'levelup', 'over', 'best']: aud[k] = a64(f'{HERE}/audio/{k}.mp3')
s = open(f'{HERE}/game.html', encoding='utf-8').read()
js = 'const ART=' + json.dumps(art, separators=(',', ':')) + ',LAYER={},SCENE=' + json.dumps(scene, separators=(',', ':')) + ';'
s, n = re.subn(r'/\*ART\*/.*?/\*/ART\*/', lambda m: '/*ART*/' + js + '/*/ART*/', s, flags=re.S); assert n == 1
ja = 'const AUD=' + json.dumps(aud, separators=(',', ':')) + ';'
s, n = re.subn(r'/\*AUDIO\*/.*?/\*/AUDIO\*/', lambda m: '/*AUDIO*/' + ja + '/*/AUDIO*/', s, flags=re.S); assert n == 1
open(out, 'w', encoding='utf-8').write(s)
print('art', len(js) // 1024, 'KB  audio', len(ja) // 1024, 'KB  total', len(s) // 1024, 'KB')
