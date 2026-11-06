# BGM and jingles for tombo.html (FluidSynth + FluidR3_GM).  python3 music.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, melody, n, E, loop_render, one_shot

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 88
# D major pentatonic (D E F# A B): an autumn evening walk, flute + celesta over strings and pizzicato
A = ['A4:3 B4:1 D5:2 E5:2', 'F#5:4 E5:2 D5:2', 'B4:3 A4:1 B4:2 D5:2', 'E5:6 r:2',
     'F#5:3 E5:1 D5:2 B4:2', 'A4:4 B4:2 D5:2', 'E5:3 D5:1 B4:2 E5:2', 'D5:6 r:2']
B = ['B5:4 A5:2 F#5:2', 'A5:4 F#5:2 E5:2', 'D5:3 E5:1 F#5:2 A5:2', 'B5:6 r:2',
     'A5:3 F#5:1 E5:2 D5:2', 'E5:4 F#5:2 A5:2', 'F#5:3 E5:1 D5:2 E5:2', 'D5:6 r:2']
ROOT = ['D', 'Bm', 'G', 'A', 'D', 'G', 'Em', 'D', 'G', 'D', 'Bm', 'A', 'D', 'Em', 'A', 'D']
CH = {'D': ['D2', 'A2', 'D3', 'F#3', 'A3'], 'Bm': ['B1', 'F#2', 'B2', 'D3', 'F#3'], 'G': ['G1', 'D2', 'G2', 'B2', 'D3'],
      'A': ['A1', 'E2', 'A2', 'C#3', 'E3'], 'Em': ['E2', 'B2', 'E3', 'G3', 'B3']}

def setup(s):
    s.prog(0, 73); s.prog(1, 8); s.prog(2, 48); s.prog(3, 45); s.prog(4, 46)   # flute, celesta, strings, pizz, harp
    for ch, v in ((0, 88), (1, 70), (2, 46), (3, 84), (4, 66)): s.cc(ch, 7, v)
    for ch, r in ((0, 60), (1, 70), (2, 80), (3, 40), (4, 60)): s.cc(ch, 91, r)
    s.cc(1, 10, 84); s.cc(4, 10, 44)

def backing(s, t0, roots):
    for b, r in enumerate(roots):
        bt = t0 + b * 8 * E; c = CH[r]
        s.note(3, bt, E, n(c[0]) + 12, 86); s.note(3, bt + 3 * E, E, n(c[1]) + 12, 66); s.note(3, bt + 4 * E, E, n(c[2]), 76); s.note(3, bt + 6 * E, E, n(c[1]) + 12, 62)
        s.note(2, bt, 8 * E, n(c[3]) + 12, 46); s.note(2, bt, 8 * E, n(c[4]) + 12, 42)
        for k, idx in enumerate((2, 3, 4, 3)): s.note(4, bt + k * 2 * E + E, E * 2, n(c[idx]) + 12, 56)

def bgm():
    s = Song(BPM); setup(s)
    t1 = melody(s, 0, 0, A, 84, 0, 0.92); backing(s, 0, ROOT[:8])
    melody(s, 1, 0, ['r:6 D6:1 E6:1', 'r:8', 'r:6 F#6:1 A6:1', 'r:8'] * 2, 58)
    t2 = melody(s, 0, t1, B, 86, 0, 0.92); backing(s, t1, ROOT[8:])
    melody(s, 1, t1, ['r:4 A6:1 F#6:1 E6:1 D6:1', 'r:8'] * 4, 56)
    print('bgm seconds', loop_render(s, t2, BPM, f'{OUT}/bgm', 80, 0.8))

def jingles():
    s = Song(150); setup(s)   # caught one: little rising celesta + harp
    melody(s, 1, 0, ['D6:1 F#6:1 A6:1 D7:3'], 92); melody(s, 4, 0, ['D5:1 A5:1 D6:4'], 70)
    one_shot(s, f'{OUT}/catch')
    s = Song(160); setup(s)   # dizzy: a wobbly downward celesta curl
    melody(s, 1, 0, ['B6:1 A6:1 F#6:1 A6:1 F#6:1 E6:1 D6:2'], 76)
    one_shot(s, f'{OUT}/dizzy')
    s = Song(120); setup(s)   # the rare oniyanma appears
    melody(s, 4, 0, ['A5:1 B5:1 D6:1 E6:1 F#6:1 A6:3'], 84); melody(s, 2, 0, ['D4:8'], 60)
    one_shot(s, f'{OUT}/rare')
    s = Song(84); setup(s)    # time up: evening bell-ish cadence
    melody(s, 0, 0, ['F#5:2 E5:2 D5:6'], 88); melody(s, 1, 0, ['r:2 A5:1 B5:1 D6:1 E6:1 F#6:6'], 70)
    for k, c in enumerate(['D3', 'A3', 'D4', 'F#4', 'A4']): s.note(4, k * E // 2, 10 * E, n(c), 72)
    one_shot(s, f'{OUT}/finish')

if __name__ == '__main__':
    bgm(); jingles()
