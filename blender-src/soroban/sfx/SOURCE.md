# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (C D E G A) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| pachi.mp3 | Kenney Impact Sounds | impactWood_light_002.ogg | pitched -0.64 semitones |
| pachi2.mp3 | Kenney Impact Sounds | impactWood_light_004.ogg | pitched -0.68 semitones |
| clear.mp3 | Kenney Impact Sounds | impactPlank_medium_001.ogg | pitched +0.47 semitones |
| ok.mp3 | Kenney Interface Sounds | confirmation_002.ogg | unpitched / unchanged |
| q.mp3 | Kenney Interface Sounds | select_002.ogg | unpitched / unchanged |
| tick.mp3 | Kenney Interface Sounds | tick_002.ogg | unpitched / unchanged |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
