# Hit / judgement sounds for mochitsuki.html on GM instruments (FluidSynth + FluidR3_GM, MIT), all in the song's key (G pentatonic).
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

def best(s):    # つきたて！ koto pluck + glockenspiel sparkle
    s.prog(0, 107); s.prog(1, 9); s.cc(0, 91, 50); s.cc(1, 91, 70)
    s.note(0, 0, 2 * E, n('G5'), 120); s.note(0, 0, 2 * E, n('D6'), 100)
    s.note(1, E // 4, 2 * E, n('G6'), 90); s.note(1, E // 2, 2 * E, n('B6'), 80)
def great(s):   # もっちり: koto pluck
    s.prog(0, 107); s.cc(0, 91, 40); s.note(0, 0, 2 * E, n('D5'), 110); s.note(0, 0, 2 * E, n('G5'), 90)
def good(s):    # ぺたっ: soft wood block
    s.prog(0, 115); s.note(0, 0, E // 2, n('B4'), 90)
def miss(s):    # すかっ: muffled low taiko
    s.prog(0, 116); s.note(0, 0, E, n('D2'), 70)
def ouch(s):    # いたっ！ vibraslap + falling shamisen
    s.prog(0, 106); s.cc(0, 91, 20)
    s.note(9, 0, 2 * E, 58, 110)
    s.note(0, 0, E // 2, n('D5'), 110); s.note(0, E // 2, E, n('B4'), 100); s.note(0, E, E, n('G4'), 90)
def yoisho(s):  # every 10 combo: koto run up + taiko
    s.prog(0, 107); s.prog(1, 116); s.cc(0, 91, 50)
    for i, p in enumerate(['G5', 'A5', 'B5', 'D6', 'E6', 'G6']): s.note(0, i * E // 3, 2 * E, n(p), 90 + i * 5)
    s.note(1, 0, E, n('G2'), 110); s.note(1, 2 * E, E, n('G2'), 120)
def start(s):   # start: hyoshigi (wood clap) ×2 + koto chord
    s.prog(0, 115); s.prog(1, 107); s.cc(1, 91, 50)
    s.note(0, 0, E // 2, n('D5'), 120); s.note(0, E, E // 2, n('D5'), 120)
    for i, p in enumerate(['G4', 'D5', 'G5', 'B5']): s.note(1, 2 * E + i * E // 6, 3 * E, n(p), 100)

for nm, bpm, fn in (('best', 150, best), ('great', 150, great), ('good', 150, good), ('miss', 120, miss), ('ouch', 140, ouch), ('yoisho', 150, yoisho), ('start', 120, start)):
    make(nm, bpm, fn); print(nm)
