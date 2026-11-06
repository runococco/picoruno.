# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (F G A C D) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| pop.mp3 | UI SFX library | soft/drop | pitched -1.49 semitones |
| blow.mp3 | UI SFX library | dreamy/swipe | pitched +0.57 semitones |
| pass.mp3 | Kenney Interface Sounds | glass_002.ogg | pitched +0.98 semitones |
| gold.mp3 | Kenney Interface Sounds | glass_006.ogg | pitched -0.69 semitones |
| fit.mp3 | Kenney Impact Sounds | impactGlass_medium_004.ogg | pitched -0.34 semitones |
| puff.mp3 | UI SFX library | soft/press | pitched -0.98 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
