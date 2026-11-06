# BGM and jingles for imohori.html (FluidSynth + FluidR3_GM).  python3 music.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, melody, n, E, loop_render, one_shot

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 120
# G major pentatonic (G A B D E): a bouncy harvest tune, marimba + ocarina over pizzicato and soft drums
A = ['D5:1 r:1 B4:1 D5:1 E5:2 D5:2', 'B4:2 A4:2 G4:4', 'A4:1 r:1 B4:1 D5:1 E5:1 D5:1 B4:2', 'A4:6 r:2',
     'D5:1 r:1 E5:1 G5:1 E5:2 D5:2', 'B4:2 D5:2 E5:4', 'D5:1 B4:1 A4:1 G4:1 A4:2 B4:2', 'G4:6 r:2']
B = ['G5:2 E5:1 D5:1 E5:2 G5:2', 'A5:4 G5:4', 'E5:1 D5:1 B4:1 D5:1 E5:2 D5:2', 'B4:6 r:2',
     'G5:2 A5:1 G5:1 E5:2 D5:2', 'E5:4 D5:2 B4:2', 'A4:1 B4:1 D5:1 E5:1 D5:2 A4:2', 'G4:6 r:2']
ROOT = ['G', 'Em', 'C', 'D', 'G', 'C', 'D', 'G'] * 2
CH = {'G': ['G1', 'D2', 'G2', 'B2'], 'Em': ['E2', 'B2', 'E3', 'G3'], 'C': ['C2', 'G2', 'C3', 'E3'], 'D': ['D2', 'A2', 'D3', 'F#3']}

def setup(s):
    s.prog(0, 12); s.prog(1, 79); s.prog(2, 45); s.prog(3, 32)   # marimba, ocarina, pizzicato, acoustic bass
    for ch, v in ((0, 96), (1, 66), (2, 64), (3, 84), (9, 56)): s.cc(ch, 7, v)
    for ch, r in ((0, 40), (1, 60), (2, 40), (3, 20), (9, 30)): s.cc(ch, 91, r)
    s.cc(1, 10, 44); s.cc(2, 10, 84)

def backing(s, t0, roots):
    for b, r in enumerate(roots):
        bt = t0 + b * 8 * E; c = CH[r]
        for k in (0, 4): s.note(3, bt + k * E, E * 2, n(c[0]) + 12, 86)
        for k in (2, 6): s.note(3, bt + k * E, E, n(c[1]) + 12, 68)
        for k in (1, 3, 5, 7): s.note(2, bt + k * E, E, n(c[2]) + 12, 56); s.note(2, bt + k * E, E, n(c[3]) + 12, 50)
        for k in range(8):
            if k in (0, 4): s.note(9, bt + k * E, E, 36, 66)
            if k in (2, 6): s.note(9, bt + k * E, E, 76, 58)
            if k in (3, 7): s.note(9, bt + k * E, E // 2, 77, 36)

def bgm():
    s = Song(BPM); setup(s)
    t1 = melody(s, 0, 0, A, 92, 0, 0.55); backing(s, 0, ROOT[:8])
    t2 = melody(s, 1, t1, B, 80, 0, 0.85); melody(s, 0, t1, ['r:8'] * 3 + ['r:4 D6:1 E6:1 G6:2'] + ['r:8'] * 3 + ['r:4 B5:1 D6:1 G6:2'], 70); backing(s, t1, ROOT[8:])
    print('bgm seconds', loop_render(s, t2, BPM, f'{OUT}/bgm', 80, 0.6))

def oneshots():
    s = Song(160); setup(s)   # a chain of potatoes pops out
    melody(s, 0, 0, ['D6:1 G6:2'], 100)
    one_shot(s, f'{OUT}/pop')
    s = Song(150); setup(s)   # golden potato
    melody(s, 0, 0, ['D5:1 E5:1 G5:1 A5:1 B5:1 D6:3'], 96); melody(s, 1, 0, ['r:4 G5:1 B5:1 D6:2'], 70)
    one_shot(s, f'{OUT}/gold')
    s = Song(120); setup(s)   # the vine snaps
    melody(s, 0, 0, ['E5:1 D5:1 B4:1 A4:1 G4:3'], 90)
    one_shot(s, f'{OUT}/oops')
    s = Song(110); setup(s)   # game over
    melody(s, 1, 0, ['D5:2 B4:2 A4:2 G4:4'], 88); melody(s, 0, 0, ['r:6 G4:1 D5:1 G5:4'], 76)
    one_shot(s, f'{OUT}/over')

if __name__ == '__main__':
    bgm(); oneshots()
