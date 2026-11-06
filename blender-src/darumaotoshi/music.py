# BGM and jingles for darumaotoshi.html (FluidSynth + FluidR3_GM).  python3 music.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, melody, n, E, loop_render, one_shot

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 116
# F major pentatonic (F G A C D): a relaxed autumn-veranda tune, shamisen + flute over pizzicato and soft drums
A = ['C5:1 r:1 A4:1 C5:1 D5:2 C5:2', 'A4:2 G4:2 F4:4', 'G4:1 r:1 A4:1 C5:1 D5:1 C5:1 A4:2', 'G4:6 r:2',
     'C5:1 r:1 D5:1 F5:1 D5:2 C5:2', 'A4:2 C5:2 D5:4', 'C5:1 A4:1 G4:1 F4:1 G4:2 A4:2', 'F4:6 r:2']
B = ['F5:2 D5:1 C5:1 D5:2 F5:2', 'G5:4 F5:4', 'D5:1 C5:1 A4:1 C5:1 D5:2 C5:2', 'A4:6 r:2',
     'F5:2 G5:1 F5:1 D5:2 C5:2', 'D5:4 C5:2 A4:2', 'G4:1 A4:1 C5:1 D5:1 C5:2 G4:2', 'F4:6 r:2']
ROOT = ['F', 'Dm', 'Bb', 'C', 'F', 'Bb', 'C', 'F'] * 2
CH = {'F': ['F2', 'C3', 'F3', 'A3'], 'Dm': ['D2', 'A2', 'D3', 'F3'], 'Bb': ['Bb1', 'F2', 'Bb2', 'D3'], 'C': ['C2', 'G2', 'C3', 'E3']}

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
    t2 = melody(s, 1, t1, B, 80, 0, 0.85); melody(s, 0, t1, ['r:8'] * 3 + ['r:4 C6:1 D6:1 F6:2'] + ['r:8'] * 3 + ['r:4 A5:1 C6:1 F6:2'], 70); backing(s, t1, ROOT[8:])
    print('bgm seconds', loop_render(s, t2, BPM, f'{OUT}/bgm', 80, 0.6))

def oneshots():
    s = Song(160); setup(s)   # perfect hit
    melody(s, 0, 0, ['C6:1 F6:2'], 100)
    one_shot(s, f'{OUT}/perfect')
    s = Song(150); setup(s)   # stage clear
    melody(s, 0, 0, ['C5:1 D5:1 F5:1 G5:1 A5:1 C6:3'], 96); melody(s, 1, 0, ['r:4 F5:1 A5:1 C6:2'], 70)
    one_shot(s, f'{OUT}/clear')
    s = Song(120); setup(s)   # topple
    melody(s, 0, 0, ['D5:1 C5:1 A4:1 G4:1 F4:3'], 90)
    one_shot(s, f'{OUT}/topple')
    s = Song(110); setup(s)   # game over
    melody(s, 1, 0, ['C5:2 A4:2 G4:2 F4:4'], 88); melody(s, 0, 0, ['r:6 F4:1 C5:1 F5:4'], 76)
    one_shot(s, f'{OUT}/over')

if __name__ == '__main__':
    bgm(); oneshots()
