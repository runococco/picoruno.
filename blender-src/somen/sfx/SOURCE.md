# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (G A B D E) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| hashi.mp3 | Kenney Impact Sounds | impactWood_light_002.ogg | pitched -0.64 semitones |
| get.mp3 | UI SFX library | organic/drop | pitched -0.97 semitones |
| plop.mp3 | UI SFX library | zen/drop | pitched -1.48 semitones |
| whiff.mp3 | UI SFX library | soft/swipe | pitched +0.67 semitones |
| bad.mp3 | Kenney Interface Sounds | back_003.ogg | pitched +0.09 semitones |
| meow.mp3 | UI SFX library | rubber/notification | pitched -0.45 semitones |
| bonus.mp3 | Kenney Interface Sounds | glass_002.ogg | pitched -0.02 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (combo / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT). Water noise is generated in the browser from filtered noise.
