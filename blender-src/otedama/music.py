# BGM and jingles for otedama.html (FluidSynth + FluidR3_GM).  python3 music.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, melody, n, E, loop_render, one_shot

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 96
# G major pentatonic (G A B D E): a bouncy handball-song feel, shamisen + koto over pizzicato, bass and wood blocks
A = ['D6:1 D6:1 B5:1 D6:1 E6:2 D6:2', 'B5:1 A5:1 G5:2 A5:4', 'B5:1 B5:1 D6:1 B5:1 A5:2 G5:2', 'A5:2 B5:2 D6:4',
     'E6:1 E6:1 D6:1 E6:1 G6:2 E6:2', 'D6:1 B5:1 A5:2 B5:4', 'A5:1 B5:1 D6:1 B5:1 A5:2 E5:2', 'G5:6 r:2']
B = ['G6:2 E6:1 D6:1 E6:2 D6:2', 'B5:2 D6:2 E6:4', 'D6:1 E6:1 G6:1 E6:1 D6:2 B5:2', 'A5:6 r:2',
     'G6:2 E6:1 D6:1 B5:2 D6:2', 'E6:2 D6:2 B5:4', 'A5:1 B5:1 D6:1 E6:1 D6:2 A5:2', 'G5:6 r:2']
ROOT = ['G', 'Em', 'C', 'D', 'G', 'C', 'D', 'G'] * 2
CH = {'G': ['G1', 'D2', 'G2', 'B2'], 'Em': ['E1', 'B1', 'E2', 'G2'], 'C': ['C2', 'G2', 'C3', 'E3'], 'D': ['D2', 'A2', 'D3', 'F#3']}

def setup(s):
    s.prog(0, 106); s.prog(1, 107); s.prog(2, 45); s.prog(3, 32)   # shamisen, koto, pizzicato, acoustic bass
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
            if k in (2, 6): s.note(9, bt + k * E, E, 76, 58)
            if k in (3, 7): s.note(9, bt + k * E, E // 2, 77, 40)

def bgm():
    s = Song(BPM); setup(s)
    t1 = melody(s, 0, 0, A, 92, 0, 0.5); backing(s, 0, ROOT[:8])
    t2 = melody(s, 1, t1, B, 84, 0, 0.85); melody(s, 0, t1, ['r:8'] * 3 + ['r:4 D6:1 E6:1 G6:2'] + ['r:8'] * 3 + ['r:4 B5:1 D6:1 G6:2'], 70); backing(s, t1, ROOT[8:])
    print('bgm seconds', loop_render(s, t2, BPM, f'{OUT}/bgm', 80, 0.6))

def oneshots():
    s = Song(140); setup(s)   # one more beanbag joins
    melody(s, 0, 0, ['G5:1 B5:1 D6:1 G6:3'], 90); melody(s, 1, 0, ['r:2 D6:1 G6:3'], 70)
    one_shot(s, f'{OUT}/levelup')
    s = Song(100); setup(s)   # all fallen, a little bow
    melody(s, 1, 0, ['D6:2 B5:2 A5:2 G5:4'], 84); melody(s, 0, 0, ['r:6 G5:1 D6:1 G6:4'], 72)
    one_shot(s, f'{OUT}/over')
    s = Song(140); setup(s)   # new best
    melody(s, 0, 0, ['D6:1 E6:1 G6:1 A6:1 B6:1 D7:3'], 92)
    one_shot(s, f'{OUT}/best')

if __name__ == '__main__':
    bgm(); oneshots()
