# BGM and jingles for takoage.html (FluidSynth + FluidR3_GM).  python3 music.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, melody, n, E, loop_render, one_shot

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 104
# D major pentatonic (D E F# A B): a bright winter-sky tune, koto + flute over pizzicato, bass and light drums
A = ['A5:2 B5:1 A5:1 F#5:2 E5:2', 'D5:2 E5:2 F#5:4', 'A5:1 A5:1 B5:1 D6:1 B5:2 A5:2', 'F#5:6 r:2',
     'A5:2 B5:1 D6:1 E6:2 D6:2', 'B5:2 A5:2 F#5:4', 'E5:1 F#5:1 A5:1 B5:1 A5:2 E5:2', 'D5:6 r:2']
B = ['D6:2 E6:1 D6:1 B5:2 A5:2', 'B5:4 D6:4', 'E6:1 D6:1 B5:1 A5:1 F#5:2 A5:2', 'B5:6 r:2',
     'D6:2 E6:1 F#6:1 E6:2 D6:2', 'B5:2 D6:2 E6:4', 'D6:1 B5:1 A5:1 F#5:1 E5:2 F#5:2', 'D5:6 r:2']
ROOT = ['D', 'Bm', 'G', 'A', 'D', 'G', 'A', 'D'] * 2
CH = {'D': ['D2', 'A2', 'D3', 'F#3'], 'Bm': ['B1', 'F#2', 'B2', 'D3'], 'G': ['G1', 'D2', 'G2', 'B2'], 'A': ['A1', 'E2', 'A2', 'C#3']}

def setup(s):
    s.prog(0, 107); s.prog(1, 73); s.prog(2, 45); s.prog(3, 32)   # koto, flute, pizzicato, acoustic bass
    for ch, v in ((0, 96), (1, 70), (2, 64), (3, 84), (9, 56)): s.cc(ch, 7, v)
    for ch, r in ((0, 40), (1, 50), (2, 40), (3, 20), (9, 30)): s.cc(ch, 91, r)
    s.cc(1, 10, 44); s.cc(2, 10, 84)

def backing(s, t0, roots):
    for b, r in enumerate(roots):
        bt = t0 + b * 8 * E; c = CH[r]
        for k in (0, 4): s.note(3, bt + k * E, E * 2, n(c[0]) + 12, 86)
        for k in (2, 6): s.note(3, bt + k * E, E, n(c[1]) + 12, 68)
        for k in (1, 3, 5, 7): s.note(2, bt + k * E, E, n(c[2]) + 12, 56); s.note(2, bt + k * E, E, n(c[3]) + 12, 50)
        for k in range(8):
            if k in (0, 4): s.note(9, bt + k * E, E, 36, 70)
            if k in (2, 6): s.note(9, bt + k * E, E, 37, 50)
            s.note(9, bt + k * E, E // 2, 42, 34)

def bgm():
    s = Song(BPM); setup(s)
    t1 = melody(s, 0, 0, A, 92, 0, 0.5); backing(s, 0, ROOT[:8])
    t2 = melody(s, 1, t1, B, 84, 0, 0.85); melody(s, 0, t1, ['r:8'] * 3 + ['r:4 A6:1 B6:1 D7:2'] + ['r:8'] * 3 + ['r:4 F#6:1 A6:1 D7:2'], 70); backing(s, t1, ROOT[8:])
    print('bgm seconds', loop_render(s, t2, BPM, f'{OUT}/bgm', 80, 0.6))

def oneshots():
    s = Song(110); setup(s)   # the string snapped, the kite floats away
    melody(s, 1, 0, ['A5:1 F#5:1 E5:1 D5:3'], 84); melody(s, 0, 0, ['r:2 B5:1 A5:3'], 66)
    one_shot(s, f'{OUT}/snapped')
    s = Song(100); setup(s)   # reel the kite home
    melody(s, 0, 0, ['A5:2 F#5:2 E5:2 D5:4'], 88); melody(s, 1, 0, ['r:6 A5:1 D6:1 F#6:4'], 72)
    one_shot(s, f'{OUT}/over')
    s = Song(140); setup(s)   # new best
    melody(s, 0, 0, ['D6:1 E6:1 F#6:1 A6:1 B6:1 D7:3'], 92)
    one_shot(s, f'{OUT}/best')

if __name__ == '__main__':
    bgm(); oneshots()
