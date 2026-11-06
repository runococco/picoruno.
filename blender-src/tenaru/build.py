# Packs the Blender outputs (GLBs + baked textures) into tenaru.html between the ASSETS markers.
# python3 build.py <glb-dir> <tex-dir> <html>
import sys, io, base64, json, re
from PIL import Image
glb, tex, html = sys.argv[1], sys.argv[2], sys.argv[3]

def jpg(path, q, size=None, gray=False):
    im = Image.open(path)
    im = im.convert('L' if gray else 'RGB')
    if size: im = im.resize((size, size), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, 'JPEG', quality=q, optimize=True, progressive=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()

A = {'tex': {}}
for n in ['floor', 'wall', 'wains', 'ceil', 'board', 'metal', 'wood']:
    A['tex'][n + '_c'] = jpg(f'{tex}/{n}_c.png', 80)
    A['tex'][n + '_n'] = jpg(f'{tex}/{n}_n.png', 82)
    if n in ('floor', 'wains', 'metal', 'wood'):
        A['tex'][n + '_r'] = jpg(f'{tex}/{n}_r.png', 70, 256, gray=True)
for n in ['tenaga', 'props']:
    A[n] = base64.b64encode(open(f'{glb}/{n}.glb', 'rb').read()).decode()
js = 'window.ASSETS=' + json.dumps(A, separators=(',', ':')) + ';'
s = open(html, encoding='utf-8').read()
s, k = re.subn(r'/\*ASSETS\*/.*?/\*/ASSETS\*/', lambda m: '/*ASSETS*/' + js + '/*/ASSETS*/', s, flags=re.S)
assert k == 1, 'markers not found'
open(html, 'w', encoding='utf-8').write(s)
print('asset bytes', len(js))
