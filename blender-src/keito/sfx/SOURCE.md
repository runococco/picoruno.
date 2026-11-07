# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (D E F# A B) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| grab.mp3 | Kenney Rpg Audio | cloth1.ogg | unpitched / unchanged |
| put.mp3 | Kenney Rpg Audio | cloth2.ogg | unpitched / unchanged |
| untie.mp3 | UI SFX library | organic/check | pitched -1.04 semitones |
| clear.mp3 | UI SFX library | organic/achievement | pitched +1.18 semitones |
| skip.mp3 | Kenney Interface Sounds | minimize_002.ogg | unpitched / unchanged |
| tick.mp3 | UI SFX library | soft/notification | pitched +0.80 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
