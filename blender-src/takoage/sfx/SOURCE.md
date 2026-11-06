# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (D E F# A B) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| pop.mp3 | UI SFX library | organic/snap | pitched -1.10 semitones |
| gold.mp3 | Kenney Interface Sounds | glass_006.ogg | pitched +0.31 semitones |
| gust.mp3 | UI SFX library | dreamy/swipe | pitched +0.57 semitones |
| bonk.mp3 | Kenney Impact Sounds | impactSoft_medium_001.ogg | pitched -1.39 semitones |
| snap.mp3 | Kenney Rpg Audio | clothBelt2.ogg | unpitched / unchanged |
| reel.mp3 | Kenney Ui Audio | click3.ogg | unpitched / unchanged |
| meow.mp3 | UI SFX library | rubber/notification | pitched -0.45 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (snapped / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT). The wind is generated in the browser from filtered noise.
