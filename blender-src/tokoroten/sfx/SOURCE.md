# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (F G A# C D) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| push.mp3 | UI SFX library | rubber/drag-start | pitched -0.69 semitones |
| plop.mp3 | UI SFX library | organic/drop | pitched +0.03 semitones |
| good.mp3 | Kenney Interface Sounds | confirmation_002.ogg | unpitched / unchanged |
| perfect.mp3 | UI SFX library | organic/success | pitched +0.02 semitones |
| spill.mp3 | Kenney Impact Sounds | footstep_carpet_002.ogg | unpitched / unchanged |
| miss.mp3 | Kenney Interface Sounds | minimize_002.ogg | unpitched / unchanged |
| reload.mp3 | Kenney Impact Sounds | impactWood_light_002.ogg | pitched -0.64 semitones |
| bowl.mp3 | Kenney Impact Sounds | impactPlate_light_001.ogg | unpitched / unchanged |
| lost.mp3 | UI SFX library | soft/warning | pitched -1.18 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
