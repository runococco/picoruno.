# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (C D F G A) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| wood.mp3 | Kenney Impact Sounds | impactWood_heavy_001.ogg | pitched -0.94 semitones |
| water.mp3 | UI SFX library | organic/drop | pitched +0.03 semitones |
| water2.mp3 | UI SFX library | zen/drop | pitched -0.48 semitones |
| good.mp3 | UI SFX library | organic/success | pitched -0.98 semitones |
| hot.mp3 | UI SFX library | soft/notification | pitched -1.20 semitones |
| change.mp3 | Kenney Interface Sounds | maximize_003.ogg | unpitched / unchanged |
| tick.mp3 | Kenney Interface Sounds | pluck_001.ogg | pitched +1.03 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
