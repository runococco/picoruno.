# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (A# C D F G) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| drip.mp3 | UI SFX library | glass/drop | pitched +1.23 semitones |
| pat.mp3 | UI SFX library | soft/press | pitched -0.98 semitones |
| splash.mp3 | UI SFX library | organic/drop | pitched +0.03 semitones |
| meow.mp3 | UI SFX library | rubber/notification | pitched -0.45 semitones |
| gust.mp3 | UI SFX library | dreamy/swipe | pitched -1.43 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (bonus / rainbow / soaked / over): original (music.py), FluidSynth + FluidR3_GM (MIT). Rain noise is generated in the browser from filtered noise.
