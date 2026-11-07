# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (C D E G A) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| pull.mp3 | Kenney Rpg Audio | clothBelt.ogg | unpitched / unchanged |
| whir.mp3 | Kenney Rpg Audio | cloth3.ogg | unpitched / unchanged |
| good.mp3 | Kenney Interface Sounds | select_003.ogg | unpitched / unchanged |
| level.mp3 | Kenney Interface Sounds | confirmation_002.ogg | unpitched / unchanged |
| stop.mp3 | Kenney Interface Sounds | minimize_002.ogg | unpitched / unchanged |
| tick.mp3 | Kenney Interface Sounds | tick_002.ogg | unpitched / unchanged |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
