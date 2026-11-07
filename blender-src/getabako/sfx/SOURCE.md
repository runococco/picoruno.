# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (D E F# A B) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| open.mp3 | Kenney Impact Sounds | impactWood_light_001.ogg | pitched +0.25 semitones |
| close.mp3 | Kenney Impact Sounds | impactWood_light_003.ogg | pitched -0.82 semitones |
| match.mp3 | UI SFX library | organic/success | pitched -0.98 semitones |
| miss.mp3 | UI SFX library | soft/notification | pitched +0.80 semitones |
| clear.mp3 | UI SFX library | organic/achievement | pitched +1.18 semitones |
| peek.mp3 | Kenney Interface Sounds | pluck_001.ogg | pitched +0.03 semitones |
| next.mp3 | Kenney Interface Sounds | maximize_003.ogg | unpitched / unchanged |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
