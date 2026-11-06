# Builds a game's sfx/ folder from sfx_map.json: CC0 sources (Kenney packs, UI SFX library), tuned to the BGM key.
# python3 sfxbuild.py <game-dir> <kenney-src-dir> <uisfx-sounds-dir>
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sfxkit import tune, analyse, NAMES
game, KEN, UIS = sys.argv[1:4]
cfg = json.load(open(os.path.join(game, 'sfx_map.json')))
keys = cfg['key']; rows = []
for name, (src, gain) in cfg['sounds'].items():
    kind, ref = src.split(':', 1)
    path = os.path.join(KEN, ref) if kind == 'kenney' else os.path.join(UIS, ref + '.mp3')
    info = analyse(path); r = tune(path, os.path.join(game, 'sfx', name + '.mp3'), set(keys), gain_db=gain, info=info)
    pack, file = (ref.split('__') if kind == 'kenney' else ('UI SFX library', ref))
    rows.append(f"| {name}.mp3 | {'Kenney ' + pack.replace('-', ' ').title() if kind == 'kenney' else pack} | {file} | {'pitched %+.2f semitones' % (12 * __import__('math').log2(r)) if abs(r - 1) > 1e-3 else 'unpitched / unchanged'} |")
    print(name, src, round(r, 3))
md = ['# Sound effects source', '',
      'Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)',
      'and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.',
      'Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (' + ' '.join(NAMES[k] for k in keys) + ') so they never clash with the music.', '',
      '| file | pack | original | change |', '|---|---|---|---|'] + rows
extra = cfg.get('extra')
if extra: md += ['', extra]
open(os.path.join(game, 'sfx', 'SOURCE.md'), 'w').write('\n'.join(md) + '\n')
open(os.path.join(game, 'sfx', 'LICENSE-AUDIO.txt'), 'w').write('All sound effects here are CC0 1.0 Universal (public domain dedication): https://creativecommons.org/publicdomain/zero/1.0/\nSources: Kenney (kenney.nl) and the UI SFX library (github.com/romainsimon/uisfx).\n')
