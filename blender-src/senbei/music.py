# BGM and jingles for senbei.html (FluidSynth + FluidR3_GM).  python3 music.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, melody, n, E, loop_render, one_shot

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 108
# D yo-scale (D E G A B): a street-stall tune on koto with shakuhachi answering, over marimba and a light bass
A = ['D6:1 E6:1 G6:2 A6:2 G6:2', 'E6:1 D6:1 B5:2 D6:4', 'G6:1 A6:1 B6:2 A6:1 G6:1 E6:2', 'D6:6 r:2',
     'B6:2 A6:1 G6:1 A6:2 E6:2', 'G6:1 E6:1 D6:2 B5:4', 'D6:1 E6:1 G6:1 A6:1 G6:2 E6:2', 'D6:6 r:2']
B = ['A5:4 B5:2 D6:2', 'E6:4 D6:4', 'B5:2 A5:2 G5:2 A5:2', 'E5:6 r:2',
     'A5:4 D6:2 E6:2', 'G6:4 E6:2 D6:2', 'B5:2 A5:2 E5:2 G5:2', 'D5:6 r:2']
ROOT = ['D', 'G', 'D', 'A', 'G', 'D', 'A', 'D'] * 2
CH = {'D': ['D2', 'A2', 'D3', 'A3'], 'G': ['G1', 'D2', 'G2', 'D3'], 'A': ['A1', 'E2', 'A2', 'E3']}

def setup(s):
    s.prog(0, 107); s.prog(1, 77); s.prog(2, 12); s.prog(3, 32)   # koto, shakuhachi, marimba, acoustic bass
    for ch, v in ((0, 96), (1, 48), (2, 64), (3, 76), (9, 44)): s.cc(ch, 7, v)
    for ch, r in ((0, 60), (1, 60), (2, 40), (3, 20), (9, 30)): s.cc(ch, 91, r)
    s.cc(1, 10, 44); s.cc(2, 10, 84)

def backing(s, t0, roots):
    for b, r in enumerate(roots):
        bt = t0 + b * 8 * E; c = CH[r]
        for k in (0, 4): s.note(3, bt + k * E, E * 2, n(c[0]) + 12, 80)
        for k in (1, 3, 5, 7): s.note(2, bt + k * E, E, n(c[2]) + 12, 54); s.note(2, bt + k * E, E, n(c[3]) + 12, 48)
        for k in range(8):
            if k in (2, 6): s.note(9, bt + k * E, E, 37, 40)
            s.note(9, bt + k * E, E // 2, 42, 26)

def bgm():
    s = Song(BPM); setup(s)
    t1 = melody(s, 0, 0, A, 92, 0, 0.5); backing(s, 0, ROOT[:8])
    t2 = melody(s, 1, t1, B, 84, 0, 0.85); melody(s, 0, t1, ['r:8'] * 3 + ['r:4 G6:1 A6:1 B6:2'] + ['r:8'] * 3 + ['r:4 E6:1 D6:1 D6:2'], 70); backing(s, t1, ROOT[8:])
    print('bgm seconds', loop_render(s, t2, BPM, f'{OUT}/bgm', 80, 0.6))

def oneshots():
    s = Song(140); setup(s)   # a new record pile
    melody(s, 2, 0, ['D6:1 E6:1 A6:1 D7:3'], 90); melody(s, 1, 0, ['r:2 A5:1 D6:3'], 64)
    one_shot(s, f'{OUT}/levelup')
    s = Song(100); setup(s)   # out of hearts
    melody(s, 2, 0, ['A6:2 G6:2 E6:2 D6:4'], 84); melody(s, 1, 0, ['r:6 A5:1 D6:1 D5:4'], 64)
    one_shot(s, f'{OUT}/over')
    s = Song(140); setup(s)   # new best
    melody(s, 2, 0, ['D6:1 E6:1 G6:1 A6:1 B6:1 D7:3'], 92)
    one_shot(s, f'{OUT}/best')

if __name__ == '__main__':
    bgm(); oneshots()
