# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (E F# G# B C#) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| slap.mp3 | Kenney Impact Sounds | impactSoft_medium_001.ogg | pitched +0.61 semitones |
| take.mp3 | Kenney Impact Sounds | impactPlate_light_001.ogg | unpitched / unchanged |
| foul.mp3 | Kenney Interface Sounds | back_003.ogg | pitched +0.09 semitones |
| turn.mp3 | Kenney Rpg Audio | bookFlip2.ogg | unpitched / unchanged |
| meow.mp3 | UI SFX library | rubber/notification | pitched -1.45 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched -0.98 semitones |

BGM and jingles (got / win / lose / over): original (music.py), FluidSynth + FluidR3_GM (MIT). Reading-card lines are original.
