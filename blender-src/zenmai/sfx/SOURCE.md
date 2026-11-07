# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (C D E G A) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| wind.mp3 | Kenney Rpg Audio | metalClick.ogg | unpitched / unchanged |
| go.mp3 | Kenney Rpg Audio | metalLatch.ogg | unpitched / unchanged |
| step.mp3 | Kenney Interface Sounds | tick_001.ogg | unpitched / unchanged |
| bump.mp3 | Kenney Impact Sounds | impactTin_medium_001.ogg | pitched -0.06 semitones |
| cup.mp3 | Kenney Impact Sounds | impactGlass_light_001.ogg | pitched +0.56 semitones |
| fall.mp3 | Kenney Impact Sounds | impactWood_heavy_001.ogg | pitched -0.94 semitones |
| score.mp3 | Kenney Interface Sounds | confirmation_002.ogg | unpitched / unchanged |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
