# Shared sound-effect helper: analyse CC0 sound files (Kenney packs) and tune tonal ones to the key of a game's BGM,
# so effects never clash with the music. Pitch is shifted with ffmpeg (asetrate) to the nearest note of the key.
import subprocess, json, math, os, sys
import numpy as np
SR = 44100
NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def load(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)

def analyse(path):
    a = load(path)
    if not len(a): return None
    on = int(np.argmax(np.abs(a) > np.abs(a).max() * .2)); seg = a[on:on + int(SR * .35)]
    if len(seg) < 2048: seg = np.pad(seg, (0, 2048 - len(seg)))
    sp = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))); fr = np.fft.rfftfreq(len(seg), 1 / SR)
    band = (fr > 90) & (fr < 4200); s = sp[band]; f = fr[band]
    k = int(np.argmax(s)); f0 = float(f[k]); tonal = float(s[k] / (np.median(s) + 1e-9))
    midi = 69 + 12 * math.log2(f0 / 440)
    return {'dur': round(len(a) / SR, 3), 'f0': round(f0, 1), 'midi': round(midi, 2), 'note': NAMES[round(midi) % 12] + str(round(midi) // 12 - 1), 'tonal': round(tonal, 1)}

def tune(src, dst, key_pcs, tonal_thr=100, gain_db=0.0, kbps=96, info=None):
    """Write dst (mp3). If the sound is clearly pitched, shift it to the nearest pitch class in key_pcs."""
    info = info or analyse(src); ratio = 1.0
    if info and info['tonal'] >= tonal_thr:
        m = info['midi']; best = None
        for d in np.arange(-6, 6.01, 1):
            if round(m + d) % 12 in key_pcs:
                cand = (m + d) - m + (round(m + d) - (m + d))   # exact shift that lands on the tempered note
                if best is None or abs(cand) < abs(best): best = cand
        ratio = 2 ** (best / 12) if best is not None else 1.0
    af = f'asetrate={int(SR * ratio)},aresample={SR},volume={gain_db}dB'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-ac', '1', '-af', af, '-codec:a', 'libmp3lame', '-b:a', f'{kbps}k', dst], check=True)
    return ratio

if __name__ == '__main__':
    rows = {}
    for p in sorted(os.listdir(sys.argv[1])):
        r = analyse(os.path.join(sys.argv[1], p))
        if r: rows[p] = r
    json.dump(rows, open(sys.argv[2], 'w'), indent=0)
    for k, r in rows.items(): print(f"{k:55s} {r['dur']:5.2f}s tonal {r['tonal']:7.1f} {r['note']}")
