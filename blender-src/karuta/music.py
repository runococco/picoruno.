# BGM and jingles for karuta.html (FluidSynth + FluidR3_GM).  python3 music.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, melody, n, E, loop_render, one_shot

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 96
# E major pentatonic (E F# G# B C#): a quiet new-year tatami-room tune, koto + shakuhachi-ish flute over pizzicato and brushes
A = ['B5:1 r:1 G#5:1 B5:1 C#6:2 B5:2', 'G#5:2 F#5:2 E5:4', 'F#5:1 r:1 G#5:1 B5:1 C#6:1 B5:1 G#5:2', 'F#5:6 r:2',
     'B5:1 r:1 C#6:1 E6:1 C#6:2 B5:2', 'G#5:2 B5:2 C#6:4', 'B5:1 G#5:1 F#5:1 E5:1 F#5:2 G#5:2', 'E5:6 r:2']
B = ['E6:2 C#6:1 B5:1 C#6:2 E6:2', 'F#6:4 E6:4', 'C#6:1 B5:1 G#5:1 B5:1 C#6:2 B5:2', 'G#5:6 r:2',
     'E6:2 F#6:1 E6:1 C#6:2 B5:2', 'C#6:4 B5:2 G#5:2', 'F#5:1 G#5:1 B5:1 C#6:1 B5:2 F#5:2', 'E5:6 r:2']
ROOT = ['E', 'C#m', 'A', 'B', 'E', 'A', 'B', 'E'] * 2
CH = {'E': ['E1', 'B1', 'E2', 'G#2'], 'C#m': ['C#2', 'G#2', 'C#3', 'E3'], 'A': ['A1', 'E2', 'A2', 'C#3'], 'B': ['B1', 'F#2', 'B2', 'D#3']}

def setup(s):
    s.prog(0, 107); s.prog(1, 77); s.prog(2, 45); s.prog(3, 32)   # koto, shakuhachi, pizzicato, acoustic bass
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
    t2 = melody(s, 1, t1, B, 80, 0, 0.85); melody(s, 0, t1, ['r:8'] * 3 + ['r:4 B6:1 C#7:1 E7:2'] + ['r:8'] * 3 + ['r:4 G#6:1 B6:1 E7:2'], 70); backing(s, t1, ROOT[8:])
    print('bgm seconds', loop_render(s, t2, BPM, f'{OUT}/bgm', 80, 0.6))

def oneshots():
    s = Song(160); setup(s)   # you took a card
    melody(s, 0, 0, ['B5:1 E6:2'], 100)
    one_shot(s, f'{OUT}/got')
    s = Song(150); setup(s)   # you win
    melody(s, 0, 0, ['B5:1 C#6:1 E6:1 F#6:1 G#6:1 B6:3'], 96); melody(s, 1, 0, ['r:4 E6:1 G#6:1 B6:2'], 70)
    one_shot(s, f'{OUT}/win')
    s = Song(120); setup(s)   # the cat took one
    melody(s, 0, 0, ['G#5:1 F#5:1 E5:2'], 84)
    one_shot(s, f'{OUT}/lose')
    s = Song(110); setup(s)   # the cat wins the match
    melody(s, 1, 0, ['B5:2 G#5:2 F#5:2 E5:4'], 88); melody(s, 0, 0, ['r:6 E5:1 B5:1 E6:4'], 76)
    one_shot(s, f'{OUT}/over')

if __name__ == '__main__':
    bgm(); oneshots()
