# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (C D E G A) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| wind.mp3 | UI SFX library | dreamy/swipe | pitched +0.57 semitones |
| tap.mp3 | UI SFX library | soft/press | pitched -0.98 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM, the five chime notes and jingles (ok / ng / over): original (music.py), FluidSynth + FluidR3_GM (MIT).
