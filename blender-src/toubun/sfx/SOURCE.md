# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (C D E G A) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| zaku.mp3 | Kenney Impact Sounds | impactWood_light_002.ogg | pitched -0.64 semitones |
| zaku2.mp3 | Kenney Impact Sounds | impactWood_light_004.ogg | pitched -0.68 semitones |
| spread.mp3 | Kenney Rpg Audio | cloth1.ogg | unpitched / unchanged |
| perfect.mp3 | UI SFX library | organic/achievement | pitched -0.82 semitones |
| good.mp3 | UI SFX library | organic/success | pitched -0.98 semitones |
| meh.mp3 | UI SFX library | soft/notification | pitched -1.20 semitones |
| next.mp3 | Kenney Interface Sounds | pluck_001.ogg | pitched +0.03 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
