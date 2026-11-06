# Song + chart for mochitsuki.html. The chart comes from the same timeline as the music, so taps line up exactly.
# python3 music.py <outdir>   -> song.mp3, chart.json, finish.mp3
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
from gm import Song, melody, n, E, TPB, render, read, write, normalize, mp3, one_shot, SR
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else 'audio'
os.makedirs(OUT, exist_ok=True)
BPM = 112
BAR = 8 * E
INTRO = 2   # bars of count-in

# chart: one string per bar, 8 eighth-slots. P = pound (tap), H = the partner's paw (do NOT tap), . = rest
EASY = ['P.H.P.H.'] * 6 + ['P.H.PPH.', 'P.H.P...']
MID = ['P.P.H...', 'P.H.P.H.', 'PP..H...', 'P.H.PPH.', 'P.P.H...', 'P..PH...', 'P.H.P.H.', 'PPH.P...']
HARD = ['PPH.PPH.', 'P.P.H.P.', 'PPPPH...', 'P.H.P.HP', 'P..PH.P.', 'PPH.PPH.', 'P.PPH.P.', 'PPPPH.P.']
CHART = EASY + MID + HARD
OUTRO = 2

MEL = ['G5:2 A5:2 B5:2 D6:2', 'E6:2 D6:2 B5:4', 'A5:2 B5:2 D6:2 B5:2', 'A5:2 G5:2 E5:4',
       'G5:2 A5:2 B5:2 D6:2', 'E6:2 G6:2 E6:2 D6:2', 'B5:2 D6:2 A5:2 B5:2', 'G5:8']
MEL2 = ['D6:1 E6:1 D6:2 B5:2 A5:2', 'G5:2 A5:2 B5:4', 'E6:1 D6:1 B5:2 A5:2 B5:2', 'D6:4 E6:4',
        'G6:2 E6:2 D6:2 B5:2', 'A5:2 B5:2 D6:4', 'E6:2 D6:2 B5:2 A5:2', 'G5:8']

def setup(s):
    s.prog(0, 107)  # koto
    s.prog(1, 106)  # shamisen
    s.prog(2, 116)  # taiko
    s.prog(3, 77)   # shakuhachi
    s.prog(4, 33)   # bass (fingered) for weight
    for ch, v in ((0, 104), (1, 92), (2, 100), (3, 80), (4, 70), (9, 96)): s.cc(ch, 7, v)
    for ch, r in ((0, 50), (1, 25), (3, 60)): s.cc(ch, 91, r)
    s.cc(1, 10, 44); s.cc(3, 10, 80)

def song():
    s = Song(BPM); setup(s)
    t0 = INTRO * BAR
    # intro: taiko roll + wood-block count-in on the last 4 beats
    for k in range(8): s.note(2, k * E, E, n('C3'), 70 + k * 6)
    for k in range(4): s.note(9, BAR + k * 2 * E, E, 76, 110)
    nbars = len(CHART)
    events = []
    for b, pat in enumerate(CHART):
        bt = t0 + b * BAR
        for k, ch in enumerate(pat):
            tt = bt + k * E
            if ch == 'P': events.append({'t': tt, 'k': 'P'})
            elif ch == 'H':
                events.append({'t': tt, 'k': 'H'}); s.note(9, tt, E, 77, 92)        # low wood block = the partner's "はいっ"
        # backing: shamisen on the off-beats, taiko heartbeat, bass drone
        for k in range(4):
            s.note(1, bt + k * 2 * E + E, E // 2, n('G3'), 70); s.note(1, bt + k * 2 * E + E, E // 2, n('D4'), 64)
        s.note(2, bt, E, n('C3'), 84); s.note(2, bt + 4 * E, E, n('C3'), 70)
        s.note(4, bt, 3 * E, n('G1'), 80); s.note(4, bt + 4 * E, 3 * E, n('D2'), 74)
        if b >= 8: s.note(9, bt + 6 * E, E // 2, 42, 50); s.note(9, bt + 2 * E, E // 2, 42, 50)
    # melody: koto through the easy part, shakuhachi joins in the middle, both in the last part
    melody(s, 0, t0, MEL, 92, 0, 0.9)
    melody(s, 0, t0 + 8 * BAR, MEL2, 96, 0, 0.9); melody(s, 3, t0 + 8 * BAR, MEL2, 70, -1, 0.95)
    melody(s, 0, t0 + 16 * BAR, MEL, 100, 0, 0.85); melody(s, 3, t0 + 16 * BAR, MEL, 76, 0, 0.95)
    # outro
    te = t0 + nbars * BAR
    melody(s, 0, te, ['G5:1 B5:1 D6:1 G6:5', 'r:8'], 104)
    s.note(2, te, E, n('C3'), 110); s.note(2, te + E, E, n('C3'), 110); s.note(2, te + 2 * E, 2 * E, n('C3'), 120)
    s.note(4, te, 6 * E, n('G1'), 90)
    s.save(f'{OUT}/song.mid'); render(f'{OUT}/song.mid', f'{OUT}/song_raw.wav')
    a = read(f'{OUT}/song_raw.wav')
    nz = np.where(np.abs(a).max(1) > 0.002)[0]; a = a[:nz[-1] + 1]
    write(normalize(a, 0.85), f'{OUT}/song.wav'); mp3(f'{OUT}/song.wav', f'{OUT}/song.mp3', 96)
    sec = lambda tick: tick / TPB * 60 / BPM
    chart = {'bpm': BPM, 'beat': 60 / BPM, 'start': sec(t0), 'end': sec(te), 'length': len(a) / SR,
             'notes': [{'t': round(sec(e['t']), 4), 'k': e['k']} for e in events]}
    json.dump(chart, open(f'{OUT}/chart.json', 'w'))
    print('song', len(a) / SR, 's,', sum(1 for e in events if e['k'] == 'P'), 'pounds,', sum(1 for e in events if e['k'] == 'H'), 'paws')

def finish():
    s = Song(120); setup(s)
    melody(s, 0, 0, ['D6:1 E6:1 G6:2 E6:1 G6:1 A6:4'], 104)
    melody(s, 3, 0, ['r:4 B5:6'], 76)
    for k in range(4): s.note(2, k * E, E, n('C3'), 100 + k * 6)
    s.note(2, 4 * E, 4 * E, n('C3'), 127)
    one_shot(s, f'{OUT}/finish')

if __name__ == '__main__':
    song(); finish()

def pound():
    s = Song(120); setup(s)
    s.note(2, 0, E, n('G2'), 127); s.note(9, 0, E // 2, 36, 120)   # taiko + kick = a heavy "ぺったん"
    one_shot(s, f'{OUT}/pound', 128, 0.95)

if __name__ == '__main__' and len(sys.argv) > 2 and sys.argv[2] == 'pound':
    pound()
