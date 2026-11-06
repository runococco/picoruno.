# BGM and jingles for senko.html (FluidSynth + FluidR3_GM).  python3 music.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, melody, n, E, loop_render, one_shot

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 72
# C major pentatonic (C D E G A): a quiet summer night on the veranda, koto and flute over a soft string pad
A = ['E5:2 G5:2 A5:4', 'G5:2 E5:2 D5:4', 'E5:2 G5:2 C6:2 A5:2', 'G5:8',
     'A5:2 C6:2 D6:4', 'C6:2 A5:2 G5:4', 'E5:2 D5:2 E5:2 G5:2', 'C5:8']
B = ['G5:4 A5:2 G5:2', 'E5:4 D5:4', 'C5:2 D5:2 E5:2 G5:2', 'A5:8',
     'C6:4 A5:2 G5:2', 'A5:2 G5:2 E5:4', 'D5:2 E5:2 G5:2 D5:2', 'C5:8']
ROOT = ['C', 'Am', 'F', 'G', 'C', 'Am', 'G', 'C'] * 2
CH = {'C': ['C2', 'G2', 'C3', 'E3'], 'Am': ['A1', 'E2', 'A2', 'C3'], 'F': ['F1', 'C2', 'F2', 'A2'], 'G': ['G1', 'D2', 'G2', 'B2']}

def setup(s):
    s.prog(0, 107); s.prog(1, 73); s.prog(2, 49); s.prog(3, 32)   # koto, flute, string pad, acoustic bass
    for ch, v in ((0, 90), (1, 58), (2, 44), (3, 70), (9, 30)): s.cc(ch, 7, v)
    for ch, r in ((0, 70), (1, 80), (2, 90), (3, 30), (9, 40)): s.cc(ch, 91, r)
    s.cc(1, 10, 44); s.cc(2, 10, 84)

def backing(s, t0, roots):
    for b, r in enumerate(roots):
        bt = t0 + b * 8 * E; c = CH[r]
        s.note(3, bt, E * 4, n(c[0]) + 12, 72); s.note(3, bt + 4 * E, E * 4, n(c[1]) + 12, 60)
        s.note(2, bt, E * 8, n(c[2]) + 12, 40); s.note(2, bt, E * 8, n(c[3]) + 12, 36)
        s.note(9, bt + 4 * E, E, 76, 30)

def bgm():
    s = Song(BPM); setup(s)
    t1 = melody(s, 0, 0, A, 92, 0, 0.5); backing(s, 0, ROOT[:8])
    t2 = melody(s, 1, t1, B, 84, 0, 0.85); melody(s, 0, t1, ['r:8'] * 3 + ['r:4 D6:1 E6:1 G6:2'] + ['r:8'] * 3 + ['r:4 B5:1 D6:1 G6:2'], 70); backing(s, t1, ROOT[8:])
    print('bgm seconds', loop_render(s, t2, BPM, f'{OUT}/bgm', 80, 0.6))

def oneshots():
    s = Song(110); setup(s)   # a sparkler burned to the very end
    melody(s, 0, 0, ['C6:1 D6:1 E6:1 G6:3'], 90); melody(s, 1, 0, ['r:2 E6:1 G6:3'], 64)
    one_shot(s, f'{OUT}/levelup')
    s = Song(84); setup(s)   # all three sparklers done
    melody(s, 0, 0, ['G5:2 E5:2 D5:2 C5:4'], 84); melody(s, 1, 0, ['r:6 E5:1 G5:1 C6:4'], 60)
    one_shot(s, f'{OUT}/over')
    s = Song(120); setup(s)   # new best
    melody(s, 0, 0, ['E5:1 G5:1 A5:1 C6:1 D6:1 E6:3'], 92)
    one_shot(s, f'{OUT}/best')

if __name__ == '__main__':
    bgm(); oneshots()
