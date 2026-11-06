# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (D E F# A B) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| flick.mp3 | Kenney Interface Sounds | click_002.ogg | unpitched / unchanged |
| clink.mp3 | Kenney Impact Sounds | impactGlass_light_001.ogg | pitched +0.56 semitones |
| take.mp3 | Kenney Interface Sounds | glass_002.ogg | pitched -0.02 semitones |
| miss.mp3 | UI SFX library | soft/warning | pitched +0.82 semitones |
| fall.mp3 | Kenney Impact Sounds | impactSoft_medium_002.ogg | pitched +0.21 semitones |
| clear.mp3 | Kenney Interface Sounds | glass_006.ogg | pitched +0.31 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (levelup / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
