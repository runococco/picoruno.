# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (A B C# E F#) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| clash.mp3 | Kenney Impact Sounds | impactMetal_light_002.ogg | pitched -0.22 semitones |
| clang.mp3 | Kenney Impact Sounds | impactMetal_medium_001.ogg | pitched -1.00 semitones |
| dash.mp3 | UI SFX library | dreamy/swipe | pitched +0.57 semitones |
| launch.mp3 | Kenney Impact Sounds | impactWood_light_002.ogg | pitched +1.36 semitones |
| fall.mp3 | Kenney Impact Sounds | impactWood_heavy_001.ogg | pitched -0.94 semitones |
| out.mp3 | Kenney Impact Sounds | impactPlank_medium_000.ogg | pitched +0.20 semitones |
| tick.mp3 | Kenney Interface Sounds | click_002.ogg | unpitched / unchanged |
| meow.mp3 | UI SFX library | rubber/notification | pitched -1.45 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched -0.98 semitones |

BGM and jingles (win / lose / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT).
