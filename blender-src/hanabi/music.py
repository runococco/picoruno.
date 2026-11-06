# BGM + jingles for hanabi.html: a hushed summer-night tune (koto, shakuhachi, soft pad), FluidSynth / FluidR3_GM.
# python3 music.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, melody, n, E, loop_render, one_shot

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 72
# in-scale flavour on A (A Bb D E F): soft, a little wistful
KOTO = ['A4:1 E5:1 F5:1 E5:1 A5:2 E5:2', 'D5:1 A4:1 Bb4:1 A4:1 D5:4', 'A4:1 E5:1 F5:1 A5:1 Bb5:2 A5:2', 'F5:1 E5:1 D5:1 Bb4:1 A4:4']
SHAKU = ['r:8', 'r:4 E5:4', 'F5:6 E5:2', 'D5:4 A4:4', 'A5:6 F5:2', 'E5:4 D5:4', 'E5:6 F5:1 E5:1', 'A4:8']

def setup(s):
    s.prog(0, 107)  # koto
    s.prog(1, 77)   # shakuhachi
    s.prog(2, 89)   # warm pad
    s.prog(3, 33)   # bass
    for ch, v in ((0, 92), (1, 72), (2, 44), (3, 58), (9, 40)): s.cc(ch, 7, v)
    for ch, r in ((0, 70), (1, 80), (2, 90)): s.cc(ch, 91, r)
    s.cc(0, 10, 50); s.cc(1, 10, 80)

def bgm():
    s = Song(BPM); setup(s); t = 0
    for rep in range(3):
        t0 = t
        for b, bar in enumerate(KOTO * 2):
            melody(s, 0, t0 + b * 8 * E, [bar], 78 if rep == 0 else 84, -1 if b % 2 else 0, .95)
        if rep >= 1: melody(s, 1, t0, SHAKU, 70 + rep * 4, 0, .95)
        for b in range(8):
            root = ['A2', 'D3', 'A2', 'F2'][b % 4]
            for p in (0, 7, 12): s.note(2, t0 + b * 8 * E, 8 * E, n(root) + p + 12, 40)
            s.note(3, t0 + b * 8 * E, 6 * E, n(root) - 12, 60)
            if rep >= 2: s.note(9, t0 + b * 8 * E + 4 * E, E, 75, 30)   # claves, very soft
        t = t0 + 8 * 8 * E
    print('bgm seconds', loop_render(s, t, BPM, f'{OUT}/bgm', 64, 0.7))

def jingles():
    s = Song(96); setup(s)   # burned to the end
    melody(s, 0, 0, ['A4:1 E5:1 A5:1 Bb5:1 A5:4'], 96); melody(s, 1, 2 * E, ['E5:6'], 74)
    for p in ('A3', 'E4', 'A4'): s.note(2, 0, 8 * E, n(p), 60)
    one_shot(s, f'{OUT}/burnout')
    s = Song(80); setup(s)   # result
    melody(s, 0, 0, ['E5:1 F5:1 A5:2 E5:1 D5:1 A4:4'], 96); melody(s, 1, 0, ['r:2 A5:8'], 66)
    for p in ('D3', 'A3', 'F4'): s.note(2, 0, 6 * E, n(p), 56)
    s.note(3, 0, 8 * E, n('D2'), 70)
    one_shot(s, f'{OUT}/finish')

if __name__ == '__main__':
    bgm(); jingles()
