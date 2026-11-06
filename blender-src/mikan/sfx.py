# Soft in-key sounds for placing fruit (FluidSynth + FluidR3_GM, MIT). python3 sfx.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, n, E, one_shot
OUT = sys.argv[1] if len(sys.argv) > 1 else 'sfx'
def make(name, fn):
    s = Song(120); fn(s); one_shot(s, f'{OUT}/{name}', 112, .7)
    for ext in ('.mid', '.wav', '_raw.wav'):
        try: os.remove(f'{OUT}/{name}{ext}')
        except OSError: pass
def plate(s):   # fruit set down on the plate: two soft marimba notes in F major
    s.prog(0, 12); s.cc(0, 91, 50); s.note(0, 0, E, n('C5'), 80); s.note(0, E // 2, 2 * E, n('F5'), 88)
def nxt(s):     # next fruit rolls in from the basket: light wooden taps
    s.prog(0, 115); s.cc(0, 7, 90)
    for i, p in enumerate(['A5', 'F5', 'C5']): s.note(0, i * E // 3, E // 2, n(p), 70 - i * 10)
make('plate', plate); make('next', nxt); print('ok')
