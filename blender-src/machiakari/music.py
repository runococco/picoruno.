# BGM + jingles for machiakari.html: a slow music-box waltz rendered with FluidSynth / FluidR3_GM.
# python3 music.py <outdir>
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, melody, n, E, loop_render, one_shot

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 84
BAR = 6 * E   # 3/4 in eighths

CH = {'C': ['C3', 'G3', 'E4'], 'Am': ['A2', 'E3', 'C4'], 'F': ['F2', 'C3', 'A3'], 'G': ['G2', 'D3', 'B3'],
      'Em': ['E2', 'B2', 'G3'], 'Dm': ['D2', 'A2', 'F3'], 'G7': ['G2', 'D3', 'F3']}
PROG = ['C', 'Am', 'F', 'G', 'C', 'Em', 'F G', 'C', 'F', 'C', 'Dm', 'G', 'Em', 'Am', 'Dm G7', 'C']
MEL = ['E5:2 G5:2 C6:2', 'B5:2 A5:2 E5:2', 'F5:2 A5:2 C6:2', 'B5:4 G5:2', 'E5:2 G5:2 C6:2', 'D6:2 B5:2 G5:2',
       'A5:2 G5:1 F5:1 D5:2', 'C5:6', 'A5:2 C6:2 A5:2', 'G5:2 E5:2 C5:2', 'F5:2 A5:2 D6:2', 'B5:4 D6:2',
       'E6:2 D6:2 B5:2', 'C6:2 A5:2 E5:2', 'F5:2 A5:1 G5:1 B5:2', 'C6:6']

def setup(s):
    s.prog(0, 10)   # music box
    s.prog(1, 46)   # harp
    s.prog(2, 49)   # slow strings
    s.prog(3, 45)   # pizzicato
    s.prog(4, 8)    # celesta
    for ch, v in ((0, 104), (1, 84), (2, 52), (3, 76), (4, 70)): s.cc(ch, 7, v)
    for ch, r in ((0, 70), (1, 70), (2, 90), (3, 50), (4, 80)): s.cc(ch, 91, r)
    s.cc(1, 10, 44); s.cc(2, 10, 70); s.cc(4, 10, 84)

def backing(s, t0, prog, strings=True):
    t = t0
    for spec in prog:
        cs = spec.split(); seg = BAR // len(cs)
        for k, c in enumerate(cs):
            tones = CH[c]; tt = t + k * seg
            s.note(3, tt, E, n(tones[0]) - 12 if n(tones[0]) > 40 else n(tones[0]), 80)
            # harp: rolling arpeggio up the chord, one note per eighth
            arp = [tones[0], tones[1], tones[2], tones[1]] if len(cs) == 2 else [tones[0], tones[1], tones[2], tones[1] , tones[2], tones[1]]
            for i, p in enumerate(arp[: seg // E]):
                s.note(1, tt + i * E, int(E * 1.8), n(p) + 12, 58 if i else 70)
            if strings:
                for p in tones: s.note(2, tt, seg - 10, n(p) + 12, 40)
        t += BAR
    return t

def bgm():
    s = Song(BPM); setup(s)
    t = 0
    t1 = melody(s, 0, t, MEL, 92, 0, 0.95); backing(s, t, PROG, strings=False)
    t2 = melody(s, 0, t1, MEL, 96, 0, 0.95)
    backing(s, t1, PROG)
    # a soft celesta echo an octave up in the second half of the second pass
    melody(s, 4, t1 + 8 * BAR, MEL[8:], 50, 1, 0.6)
    secs = loop_render(s, t2, BPM, f'{OUT}/bgm', 80, 0.78)
    print('bgm seconds', secs)

def jingles():
    s = Song(100); setup(s)
    melody(s, 4, 0, ['C5:1 E5:1 G5:1 C6:1 E6:1 G6:3'], 100)
    melody(s, 1, 0, ['C4:1 G4:1 C5:1 E5:1 G5:1 C6:3'], 80)
    melody(s, 0, 2 * E, ['r:3 G6:3'], 70)
    for p in CH['C']: s.note(2, 0, 8 * E, n(p) + 12, 50)
    one_shot(s, f'{OUT}/clear')
    s = Song(92); setup(s)
    melody(s, 0, 0, ['E5:1 G5:1 C6:2 B5:1 C6:1 D6:2 E6:6'], 100)
    melody(s, 4, 0, ['r:4 G5:2 B5:2 C6:6'], 70, 1)
    melody(s, 1, 0, ['C4:1 E4:1 G4:1 C5:1 G3:1 B3:1 D4:1 G4:1 C4:1 E4:1 G4:1 C5:1 E5:1 G5:1'], 76)
    for i, c in enumerate(['C', 'G', 'C']):
        for p in CH[c]: s.note(2, i * 4 * E, (4 if i < 2 else 8) * E, n(p) + 12, 52)
    one_shot(s, f'{OUT}/finish')

if __name__ == '__main__':
    bgm(); jingles()
