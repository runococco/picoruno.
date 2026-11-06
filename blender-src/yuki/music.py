# BGM and jingles for yukidaruma.html (FluidSynth + FluidR3_GM).  python3 music.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, melody, n, E, loop_render, one_shot

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 104
# F major pentatonic (F G A C D): a snowy morning, music box + celesta over pizzicato, sleigh bells
A = ['C5:2 D5:2 F5:2 G5:2', 'A5:4 G5:2 F5:2', 'D5:2 F5:2 G5:2 F5:2', 'C5:6 r:2',
     'D5:2 F5:2 A5:2 C6:2', 'A5:3 G5:1 F5:4', 'G5:2 A5:2 G5:2 D5:2', 'F5:6 r:2']
B = ['A5:2 C6:2 A5:2 G5:2', 'F5:4 D5:4', 'G5:2 A5:2 C6:2 D6:2', 'C6:6 r:2',
     'D6:2 C6:2 A5:2 G5:2', 'A5:3 G5:1 F5:4', 'D5:2 F5:2 G5:2 A5:2', 'F5:6 r:2']
ROOT = ['F', 'Bb', 'Dm', 'C', 'Bb', 'F', 'Gm', 'F', 'F', 'Dm', 'Bb', 'C', 'Bb', 'F', 'C', 'F']
CH = {'F': ['F2', 'C3', 'F3', 'A3', 'C4'], 'Bb': ['Bb1', 'F2', 'Bb2', 'D3', 'F3'], 'Dm': ['D2', 'A2', 'D3', 'F3', 'A3'],
      'C': ['C2', 'G2', 'C3', 'E3', 'G3'], 'Gm': ['G1', 'D2', 'G2', 'Bb2', 'D3']}

def setup(s):
    s.prog(0, 10); s.prog(1, 8); s.prog(2, 48); s.prog(3, 45)   # music box, celesta, strings, pizz
    for ch, v in ((0, 96), (1, 64), (2, 44), (3, 86), (9, 54)): s.cc(ch, 7, v)
    for ch, r in ((0, 60), (1, 70), (2, 80), (3, 40), (9, 40)): s.cc(ch, 91, r)
    s.cc(1, 10, 84); s.cc(3, 10, 50)

def backing(s, t0, roots):
    for b, r in enumerate(roots):
        bt = t0 + b * 8 * E; c = CH[r]
        for k, idx in enumerate((0, 2, 1, 2)): s.note(3, bt + k * 2 * E, E, n(c[idx]) + 12, 84 if k == 0 else 66)
        s.note(2, bt, 8 * E, n(c[3]) + 12, 44); s.note(2, bt, 8 * E, n(c[4]) + 12, 40)
        for k in range(4): s.note(1, bt + k * 2 * E + E, E, n(c[2 + k % 3]) + 24, 50)
        for k in range(8): s.note(9, bt + k * E, E // 2, 83, 46 if k % 2 else 60)   # sleigh bells

def bgm():
    s = Song(BPM); setup(s)
    t1 = melody(s, 0, 0, A, 92, 0, 0.9); backing(s, 0, ROOT[:8])
    t2 = melody(s, 0, t1, B, 94, 0, 0.9); backing(s, t1, ROOT[8:])
    print('bgm seconds', loop_render(s, t2, BPM, f'{OUT}/bgm', 80, 0.8))

def jingles():
    s = Song(150); setup(s)   # snowman done
    melody(s, 0, 0, ['C6:1 D6:1 F6:1 A6:1 C7:4'], 96); melody(s, 1, 0, ['F5:1 A5:1 C6:1 F6:5'], 70)
    s.note(9, 0, E, 83, 80); s.note(9, 4 * E, E, 81, 70)
    one_shot(s, f'{OUT}/done')
    s = Song(140); setup(s)   # perfect balance
    melody(s, 0, 0, ['F6:1 G6:1 A6:1 C7:1 D7:1 F7:4'], 96); melody(s, 1, 0, ['r:1 A5:1 C6:1 F6:6'], 72)
    s.note(9, 0, E, 81, 90)
    one_shot(s, f'{OUT}/perfect')
    s = Song(96); setup(s)    # time up
    melody(s, 0, 0, ['A5:2 G5:2 F5:6'], 92); melody(s, 1, 0, ['r:2 C6:1 D6:1 F6:1 G6:1 A6:6'], 70)
    for k, c in enumerate(['F2', 'C3', 'F3', 'A3', 'C4']): s.note(3, k * E // 2, 10 * E, n(c) + 12, 80)
    one_shot(s, f'{OUT}/finish')

if __name__ == '__main__':
    bgm(); jingles()
