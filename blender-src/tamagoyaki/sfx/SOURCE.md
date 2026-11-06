# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (F G A C D) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| pour.mp3 | UI SFX library | organic/drop | pitched +0.03 semitones |
| pop.mp3 | UI SFX library | organic/snap | pitched -0.10 semitones |
| hole.mp3 | UI SFX library | soft/warning | pitched -1.18 semitones |
| roll.mp3 | Kenney Rpg Audio | cloth2.ogg | unpitched / unchanged |
| good.mp3 | Kenney Interface Sounds | glass_002.ogg | pitched +0.98 semitones |
| bad.mp3 | Kenney Impact Sounds | impactSoft_medium_001.ogg | pitched -0.39 semitones |
| cut.mp3 | Kenney Rpg Audio | knifeSlice.ogg | unpitched / unchanged |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
