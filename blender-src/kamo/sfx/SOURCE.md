# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (F G A C D) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| join.mp3 | UI SFX library | glass/select | pitched +0.57 semitones |
| deliver.mp3 | UI SFX library | organic/success | pitched -0.98 semitones |
| big.mp3 | UI SFX library | organic/achievement | pitched -0.82 semitones |
| bonk.mp3 | Kenney Impact Sounds | impactWood_medium_002.ogg | pitched +0.44 semitones |
| scatter.mp3 | Kenney Interface Sounds | minimize_003.ogg | unpitched / unchanged |
| paddle.mp3 | UI SFX library | organic/drop | pitched +0.03 semitones |
| hatch.mp3 | UI SFX library | soft/notification | pitched -1.20 semitones |
| warn.mp3 | UI SFX library | soft/warning | pitched -1.18 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
