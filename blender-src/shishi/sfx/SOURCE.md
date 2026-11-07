# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (D E G A B) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| clack.mp3 | Kenney Impact Sounds | impactWood_heavy_002.ogg | pitched -0.36 semitones |
| pour.mp3 | UI SFX library | organic/drop | pitched -0.97 semitones |
| slide.mp3 | Kenney Rpg Audio | cloth2.ogg | unpitched / unchanged |
| flap.mp3 | Kenney Rpg Audio | cloth3.ogg | unpitched / unchanged |
| scare.mp3 | Kenney Interface Sounds | pluck_001.ogg | pitched +0.03 semitones |
| close.mp3 | Kenney Interface Sounds | maximize_003.ogg | unpitched / unchanged |
| lost.mp3 | UI SFX library | soft/warning | pitched +0.82 semitones |
| miss.mp3 | Kenney Interface Sounds | minimize_002.ogg | unpitched / unchanged |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
