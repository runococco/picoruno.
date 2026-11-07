# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (D E G A B) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| brush.mp3 | Kenney Rpg Audio | cloth1.ogg | unpitched / unchanged |
| lift.mp3 | Kenney Rpg Audio | cloth2.ogg | unpitched / unchanged |
| hana.mp3 | UI SFX library | organic/achievement | pitched +1.18 semitones |
| maru.mp3 | UI SFX library | organic/success | pitched -0.98 semitones |
| sankaku.mp3 | UI SFX library | soft/notification | pitched +0.80 semitones |
| stamp.mp3 | Kenney Impact Sounds | impactWood_light_003.ogg | pitched -0.82 semitones |
| next.mp3 | Kenney Rpg Audio | bookFlip2.ogg | unpitched / unchanged |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
