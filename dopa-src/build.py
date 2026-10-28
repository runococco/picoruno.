#!/usr/bin/env python3
"""dopa-src/<slug>/{meta.json,game.js} + common/ → ../<slug>.html（1ファイル完結）"""
import json, sys, html, urllib.parse
from pathlib import Path
here = Path(__file__).parent
tpl = (here/'common/template.html').read_text()
css = (here/'common/engine.css').read_text()
eng = (here/'common/engine.js').read_text()

def favicon(m):
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='8' fill='{m['bg']}'/>"
           f"<circle cx='16' cy='17' r='10' fill='{m['accent']}' stroke='#5b4d45' stroke-width='2'/>"
           f"<circle cx='12.5' cy='16' r='1.6' fill='#5b4d45'/><circle cx='19.5' cy='16' r='1.6' fill='#5b4d45'/></svg>")
    return 'data:image/svg+xml,' + urllib.parse.quote(svg)

def build(slug):
    d = here/slug
    m = json.loads((d/'meta.json').read_text())
    m['slug'] = slug
    game = f"const META={json.dumps(m, ensure_ascii=False)};\n" + (d/'game.js').read_text()
    rep = {
        'TITLE': html.escape(m['title']), 'DESC': html.escape(m['desc']), 'OGDESC': html.escape(m.get('ogdesc', m['desc'])),
        'CATCH': html.escape(m['catch']), 'HOWTO': ''.join(f'<li>{html.escape(h)}</li>' for h in m['howto']),
        'BG': m['bg'], 'PANEL': m.get('panel', m['bg']), 'ACCENT': m['accent'], 'SLUG': slug, 'FAVICON': favicon(m),
        'CSS': css, 'ENGINE': eng, 'GAME': game,
    }
    out = tpl
    for k in ['CSS', 'ENGINE', 'GAME']:  # 大きいものは最後に
        pass
    for k, v in rep.items():
        if k in ('CSS', 'ENGINE', 'GAME'): continue
        out = out.replace('{{'+k+'}}', v)
    for k in ('CSS', 'ENGINE', 'GAME'):
        out = out.replace('{{'+k+'}}', rep[k])
    (here.parent/f'{slug}.html').write_text(out)
    print('built', slug, len(out))

slugs = sys.argv[1:] or sorted(p.name for p in here.iterdir() if (p/'meta.json').exists())
for s in slugs: build(s)
