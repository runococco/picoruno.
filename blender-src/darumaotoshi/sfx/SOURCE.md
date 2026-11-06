# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (F G A C D) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| hit.mp3 | Kenney Impact Sounds | impactWood_heavy_001.ogg | pitched -0.94 semitones |
| knock.mp3 | Kenney Impact Sounds | impactWood_medium_002.ogg | pitched +0.44 semitones |
| land.mp3 | Kenney Impact Sounds | impactWood_light_001.ogg | pitched +0.25 semitones |
| tok.mp3 | Kenney Impact Sounds | impactWood_light_003.ogg | pitched +0.18 semitones |
| wobble.mp3 | UI SFX library | soft/warning | pitched -1.18 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (perfect / clear / topple / over): original (music.py), FluidSynth + FluidR3_GM (MIT).
