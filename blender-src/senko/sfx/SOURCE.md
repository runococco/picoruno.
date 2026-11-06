# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (C D E G A) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| pachi.mp3 | Kenney Interface Sounds | tick_002.ogg | unpitched / unchanged |
| furin.mp3 | Kenney Interface Sounds | glass_006.ogg | pitched +1.31 semitones |
| drop.mp3 | UI SFX library | soft/drop | pitched +0.51 semitones |
| light.mp3 | UI SFX library | dreamy/swipe | pitched +0.57 semitones |
| phase.mp3 | Kenney Interface Sounds | pluck_002.ogg | pitched +0.93 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
