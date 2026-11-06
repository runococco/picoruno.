# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (G A B D E) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| catch.mp3 | Kenney Impact Sounds | impactGlass_light_002.ogg | pitched +1.16 semitones |
| flee.mp3 | Kenney Rpg Audio | cloth1.ogg | unpitched / unchanged |
| gold.mp3 | Kenney Interface Sounds | glass_006.ogg | pitched +1.31 semitones |
| plop.mp3 | UI SFX library | zen/drop | pitched -1.48 semitones |
| meow.mp3 | UI SFX library | rubber/notification | pitched -0.45 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM and jingles (sync / over / best): original (music.py), FluidSynth + FluidR3_GM (MIT). The river murmur is generated in the browser from filtered noise.
