# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (C D E G A) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| hit.mp3 | Kenney Impact Sounds | impactWood_medium_002.ogg | pitched +0.44 semitones |
| clean.mp3 | Kenney Impact Sounds | impactWood_light_001.ogg | pitched +0.25 semitones |
| land.mp3 | Kenney Impact Sounds | impactPlank_medium_001.ogg | pitched +0.47 semitones |
| wobble.mp3 | Kenney Rpg Audio | creak1.ogg | unpitched / unchanged |
| fall.mp3 | Kenney Impact Sounds | impactWood_heavy_003.ogg | pitched -0.19 semitones |
| slide.mp3 | Kenney Interface Sounds | scroll_002.ogg | pitched +0.51 semitones |
| charge.mp3 | Kenney Interface Sounds | tick_002.ogg | unpitched / unchanged |
| good.mp3 | Kenney Interface Sounds | confirmation_002.ogg | unpitched / unchanged |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
