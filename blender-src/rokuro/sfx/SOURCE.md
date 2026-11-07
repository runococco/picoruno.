# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (C D E G A) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| squish.mp3 | Kenney Rpg Audio | cloth1.ogg | unpitched / unchanged |
| squish2.mp3 | Kenney Rpg Audio | cloth2.ogg | unpitched / unchanged |
| spin.mp3 | UI SFX library | dreamy/swipe | pitched +0.57 semitones |
| fire.mp3 | Kenney Impact Sounds | impactWood_heavy_001.ogg | pitched -0.94 semitones |
| great.mp3 | UI SFX library | organic/achievement | pitched -0.82 semitones |
| good.mp3 | UI SFX library | organic/success | pitched -0.98 semitones |
| meh.mp3 | UI SFX library | soft/notification | pitched -1.20 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
