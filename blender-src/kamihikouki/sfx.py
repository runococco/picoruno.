# Game sound effects for kamihikouki.html, played on GM instruments (FluidSynth + FluidR3_GM, MIT) instead of UI clicks.
# python3 sfx.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, n, E, one_shot
OUT = sys.argv[1] if len(sys.argv) > 1 else 'sfx'
os.makedirs(OUT, exist_ok=True)

def make(name, bpm, build, peak=.85):
    s = Song(bpm); build(s); one_shot(s, f'{OUT}/{name}', 112, peak)
    for ext in ('.mid', '.wav', '_raw.wav'):
        try: os.remove(f'{OUT}/{name}{ext}')
        except OSError: pass

def star(s):   # sparkly two-note ping (celesta + glockenspiel)
    s.prog(0, 8); s.prog(1, 9); s.cc(0, 91, 60); s.cc(1, 91, 60)
    s.note(0, 0, E, n('E6'), 110); s.note(0, E // 2, E * 2, n('B6'), 118)
    s.note(1, E // 2, E * 2, n('B6'), 70)
def wind(s):   # a soft gust swelling up (seashore noise + breath)
    s.prog(0, 122); s.prog(1, 121); s.cc(0, 7, 110); s.cc(1, 7, 90)
    s.note(0, 0, 2 * E, n('C5'), 110); s.note(1, 0, 2 * E, n('G5'), 80)
def crash(s):  # paper plane bumps: woody thud + small rattle
    s.prog(0, 116); s.prog(1, 115); s.cc(0, 91, 30)
    s.note(0, 0, 2 * E, n('G2'), 110); s.note(1, 0, E, n('C5'), 100); s.note(1, E // 2, E, n('G4'), 80)
    s.note(9, 0, E, 41, 90)
def start(s):  # throw: whoosh + harp glissando up
    s.prog(0, 122); s.prog(1, 46); s.cc(1, 91, 60)
    s.note(0, 0, E, n('E5'), 120)
    for i, p in enumerate(['G4', 'B4', 'D5', 'G5', 'B5', 'D6']): s.note(1, i * E // 4, 2 * E, n(p), 70 + i * 8)
def mile(s):   # every 100 m: little bell fanfare
    s.prog(0, 14); s.prog(1, 9); s.cc(0, 91, 60)
    for i, p in enumerate(['G5', 'B5', 'D6']): s.note(0, i * E // 2, 3 * E, n(p), 96); s.note(1, i * E // 2, E, n(p) + 12, 60)
def tap(s):    # soft wooden click
    s.prog(0, 115); s.note(0, 0, E // 2, n('E5'), 96)

for nm, bpm, fn in (('star', 160, star), ('wind', 120, wind), ('crash', 120, crash), ('start', 140, start), ('mile', 150, mile), ('tap', 120, tap)):
    make(nm, bpm, fn)
    print(nm)
