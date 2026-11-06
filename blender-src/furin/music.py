# BGM, the five chime notes and jingles for furin.html (FluidSynth + FluidR3_GM).  python3 music.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, melody, n, E, loop_render, one_shot

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 84
NOTES = ['C6', 'D6', 'E6', 'G6', 'A6']   # C major pentatonic: any order of chimes stays consonant
# a soft summer-evening pad: harp arpeggios over strings, all in C major pentatonic, kept quiet so the chimes stay clear
ROOT = ['C', 'Am', 'F', 'G'] * 2
CH = {'C': ['C3', 'G3', 'C4', 'E4'], 'Am': ['A2', 'E3', 'A3', 'C4'], 'F': ['F2', 'C3', 'F3', 'A3'], 'G': ['G2', 'D3', 'G3', 'B3']}

def bgm():
    s = Song(BPM); s.prog(0, 46); s.prog(1, 49); s.prog(2, 32)   # harp, slow strings, acoustic bass
    for ch, v in ((0, 70), (1, 52), (2, 64)): s.cc(ch, 7, v)
    for ch, r in ((0, 70), (1, 90), (2, 30)): s.cc(ch, 91, r)
    for b, r in enumerate(ROOT):
        bt = b * 8 * E; c = CH[r]
        for k, idx in enumerate([0, 1, 2, 3, 2, 1, 2, 3]): s.note(0, bt + k * E, E * 2, n(c[idx]) + 12, 58 + (8 if k == 0 else 0))
        s.note(1, bt, 8 * E, n(c[1]), 50); s.note(1, bt, 8 * E, n(c[3]), 44)
        s.note(2, bt, 4 * E, n(c[0]), 70); s.note(2, bt + 4 * E, 4 * E, n(c[0]) + 7 if r != 'G' else n(c[0]), 60)
    print('bgm seconds', loop_render(s, len(ROOT) * 8 * E, BPM, f'{OUT}/bgm', 80, 0.5))

def oneshots():
    for i, nm in enumerate(NOTES):   # glass chime: glockenspiel + a soft celesta octave below
        s = Song(120); s.prog(0, 9); s.prog(1, 8); s.cc(0, 7, 110); s.cc(1, 7, 70); s.cc(0, 91, 80); s.cc(1, 91, 80)
        s.note(0, 0, E * 6, n(nm), 100); s.note(1, 0, E * 6, n(nm) - 12, 70)
        one_shot(s, f'{OUT}/chime{i}')
    s = Song(150); s.prog(0, 9); s.cc(0, 91, 70)   # round cleared
    melody(s, 0, 0, ['C6:1 E6:1 G6:1 C7:3'], 96)
    one_shot(s, f'{OUT}/ok')
    s = Song(100); s.prog(0, 11); s.cc(0, 91, 70)   # a wrong chime: gentle low vibraphone, still in key
    melody(s, 0, 0, ['E5:2 C5:4'], 80)
    one_shot(s, f'{OUT}/ng')
    s = Song(100); s.prog(0, 46); s.prog(1, 9); s.cc(0, 91, 80); s.cc(1, 91, 80)   # end
    melody(s, 0, 0, ['G5:2 E5:2 D5:2 C5:4'], 84); melody(s, 1, 0, ['r:6 C6:1 G6:1 C7:4'], 70)
    one_shot(s, f'{OUT}/over')

if __name__ == '__main__':
    bgm(); oneshots()
