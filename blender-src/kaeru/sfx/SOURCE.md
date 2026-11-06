# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (A B C# E F#) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| jump.mp3 | UI SFX library | rubber/swipe | pitched -0.12 semitones |
| land.mp3 | UI SFX library | organic/drop | pitched -0.97 semitones |
| land2.mp3 | UI SFX library | organic/snap | pitched +0.90 semitones |
| sink.mp3 | UI SFX library | soft/warning | pitched +0.82 semitones |
| pull.mp3 | UI SFX library | rubber/drag-start | pitched +0.31 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched -0.98 semitones |

BGM, croak, splash and jingles (gulp / lotus / over): original (music.py), FluidSynth + FluidR3_GM (MIT).
