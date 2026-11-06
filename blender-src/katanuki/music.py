# BGM and jingles for katanuki.html (FluidSynth + FluidR3_GM).  python3 music.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, melody, n, E, loop_render, one_shot

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 112
# F major pentatonic (F G A C D): a festival-night stall tune, shamisen + flute over pizzicato and brushes
A = ['C6:1 r:1 A5:1 C6:1 D6:2 C6:2', 'A5:2 G5:2 F5:4', 'G5:1 r:1 A5:1 C6:1 D6:1 C6:1 A5:2', 'G5:6 r:2',
     'C6:1 r:1 D6:1 F6:1 D6:2 C6:2', 'A5:2 C6:2 D6:4', 'C6:1 A5:1 G5:1 F5:1 G5:2 A5:2', 'F5:6 r:2']
B = ['F6:2 D6:1 C6:1 D6:2 F6:2', 'G6:4 F6:4', 'D6:1 C6:1 A5:1 C6:1 D6:2 C6:2', 'A5:6 r:2',
     'F6:2 G6:1 F6:1 D6:2 C6:2', 'D6:4 C6:2 A5:2', 'G5:1 A5:1 C6:1 D6:1 C6:2 G5:2', 'F5:6 r:2']
ROOT = ['F', 'Dm', 'Bb', 'C', 'F', 'Bb', 'C', 'F'] * 2
CH = {'F': ['F1', 'C2', 'F2', 'A2'], 'Dm': ['D2', 'A2', 'D3', 'F3'], 'Bb': ['A#1', 'F2', 'A#2', 'D3'], 'C': ['C2', 'G2', 'C3', 'E3']}

def setup(s):
    s.prog(0, 106); s.prog(1, 73); s.prog(2, 45); s.prog(3, 32)   # shamisen, flute, pizzicato, acoustic bass
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
    t2 = melody(s, 1, t1, B, 80, 0, 0.85); melody(s, 0, t1, ['r:8'] * 3 + ['r:4 C7:1 D7:1 F7:2'] + ['r:8'] * 3 + ['r:4 A6:1 C7:1 F7:2'], 70); backing(s, t1, ROOT[8:])
    print('bgm seconds', loop_render(s, t2, BPM, f'{OUT}/bgm', 80, 0.6))

def oneshots():
    s = Song(150); setup(s)   # a shape popped out
    melody(s, 0, 0, ['C6:1 D6:1 F6:2'], 96)
    one_shot(s, f'{OUT}/clear')
    s = Song(150); setup(s)   # popped out without a single crack
    melody(s, 0, 0, ['C6:1 D6:1 F6:1 G6:1 A6:1 C7:3'], 96); melody(s, 1, 0, ['r:4 F6:1 A6:1 C7:2'], 70)
    one_shot(s, f'{OUT}/clean')
    s = Song(110); setup(s)   # stall closing
    melody(s, 1, 0, ['C6:2 A5:2 G5:2 F5:4'], 88); melody(s, 0, 0, ['r:6 F5:1 C6:1 F6:4'], 76)
    one_shot(s, f'{OUT}/over')
    s = Song(150); setup(s)   # new best
    melody(s, 0, 0, ['F6:1 G6:1 A6:1 C7:1 D7:1 F7:3'], 96)
    one_shot(s, f'{OUT}/best')

if __name__ == '__main__':
    bgm(); oneshots()
