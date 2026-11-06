# BGM + jingles for ochiba.html: a cosy autumn-garden tune (nylon guitar, flute, pizzicato, glockenspiel),
# rendered with FluidSynth / FluidR3_GM.   python3 music.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, melody, n, E, loop_render, one_shot

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 96
A = ['F#5:3 E5:1 D5:2 E5:2', 'F#5:2 A5:2 B5:4', 'A5:3 F#5:1 E5:2 D5:2', 'E5:6 r:2',
     'F#5:3 E5:1 D5:2 E5:2', 'F#5:2 A5:2 D6:4', 'B5:2 A5:2 F#5:2 E5:2', 'D5:6 r:2']
B = ['B5:3 A5:1 G5:2 A5:2', 'A5:2 F#5:2 E5:4', 'F#5:3 E5:1 C#5:2 E5:2', 'D5:2 F#5:2 B5:4',
     'B5:3 A5:1 G5:2 B5:2', 'A5:2 D6:2 C#6:4', 'B5:2 A5:2 F#5:2 E5:2', 'D5:8']
CH = {'D': ['D3', 'A3', 'D4', 'F#4'], 'Bm': ['B2', 'F#3', 'B3', 'D4'], 'G': ['G2', 'D3', 'G3', 'B3'], 'A': ['A2', 'E3', 'A3', 'C#4'],
      'Em': ['E3', 'B3', 'E4', 'G4'], 'F#m': ['F#2', 'C#3', 'F#3', 'A3']}
RA = ['D', 'Bm', 'G', 'A', 'D', 'Bm', 'Em', 'A']
RB = ['G', 'A', 'F#m', 'Bm', 'G', 'A', 'Em', 'D']

def setup(s):
    s.prog(0, 73); s.prog(1, 24); s.prog(2, 45); s.prog(3, 9); s.prog(4, 71)   # flute, nylon gtr, pizz, glock, clarinet
    for ch, v in ((0, 96), (1, 92), (2, 80), (3, 56), (4, 70), (9, 60)): s.cc(ch, 7, v)
    for ch, r in ((0, 60), (1, 40), (2, 30), (3, 70), (4, 50)): s.cc(ch, 91, r)
    s.cc(1, 10, 54); s.cc(3, 10, 80); s.cc(4, 10, 40)

def backing(s, t0, roots, shaker=True):
    for b, r in enumerate(roots):
        bt = t0 + b * 8 * E; c = CH[r]
        for k, idx in enumerate((0, 1, 2, 3, 2, 1, 2, 3)): s.note(1, bt + k * E, 2 * E, n(c[idx]), 66 if k % 2 else 74)
        s.note(2, bt, 2 * E, n(c[0]) - 12, 80); s.note(2, bt + 4 * E, 2 * E, n(c[1]) - 12, 70)
        if shaker:
            for k in range(8): s.note(9, bt + k * E, E // 2, 82, 50 if k % 2 else 36)

def bgm():
    s = Song(BPM); setup(s); t = 0
    t1 = melody(s, 0, t, A, 90, 0, 0.92); backing(s, t, RA, False)
    t2 = melody(s, 0, t1, A, 96, 0, 0.92); melody(s, 3, t1, ['r:6 D6:2', 'r:8', 'r:6 A5:2', 'r:8'] * 2, 70); backing(s, t1, RA)
    t3 = melody(s, 4, t2, B, 88, 0, 0.92); melody(s, 0, t2, B, 70, 1, 0.5); backing(s, t2, RB)
    print('bgm seconds', loop_render(s, t3, BPM, f'{OUT}/bgm', 80, 0.8))

def jingles():
    s = Song(120); setup(s)   # time up: lighting the fire
    melody(s, 0, 0, ['D5:1 F#5:1 A5:1 D6:1 C#6:1 A5:1 D6:6'], 100); melody(s, 3, 0, ['r:6 A6:6'], 70)
    for k, c in enumerate(['D3', 'A3', 'D4', 'F#4', 'A4']): s.note(1, k * E // 2, 8 * E, n(c), 80)
    one_shot(s, f'{OUT}/finish')
    s = Song(140); setup(s)   # found a nut
    melody(s, 3, 0, ['A5:1 D6:1 F#6:1 A6:3'], 96)
    one_shot(s, f'{OUT}/found')
    s = Song(110); setup(s)   # yakiimo is ready: warm clarinet + guitar strum
    melody(s, 4, 0, ['A4:2 D5:2 F#5:2 E5:1 D5:5'], 96)
    for k, c in enumerate(['D3', 'A3', 'D4', 'F#4', 'A4', 'D5']): s.note(1, k * E // 3, 10 * E, n(c), 84)
    s.note(3, 6 * E, 4 * E, n('D7'), 60)
    one_shot(s, f'{OUT}/ready')

def wind():
    s = Song(100); s.prog(0, 122); s.prog(1, 121); s.cc(0, 7, 110); s.cc(1, 7, 80); s.cc(0, 91, 60)
    s.note(0, 0, 6 * E, n('D5'), 100); s.note(1, E, 4 * E, n('A5'), 70)
    one_shot(s, f'{OUT}/wind', 96, 0.7)

if __name__ == '__main__':
    if len(sys.argv) > 2: globals()[sys.argv[2]]()
    else: bgm(); jingles(); wind()
