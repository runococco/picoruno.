# Sound effects source

Effects are CC0 1.0 (public domain) sounds: Kenney sound packs (https://kenney.nl, mirrored in github.com/series-ai/jam-ready-assets)
and the UI SFX library (github.com/romainsimon/uisfx via npm `@wubbleai/community-sfx`). No attribution or fee required.
Pitched sounds are tuned by `common/sfxbuild.py` to the nearest note of the BGM key (G A B D E) so they never clash with the music.

| file | pack | original | change |
|---|---|---|---|
| pour.mp3 | UI SFX library | organic/drop | pitched -0.97 semitones |
| scoop.mp3 | UI SFX library | organic/snap | pitched -1.10 semitones |
| flip.mp3 | Kenney Impact Sounds | impactMetal_light_002.ogg | pitched +0.78 semitones |
| take.mp3 | Kenney Impact Sounds | impactPlate_light_001.ogg | unpitched / unchanged |
| coin.mp3 | Kenney Rpg Audio | handleCoins.ogg | unpitched / unchanged |
| burn.mp3 | Kenney Impact Sounds | impactSoft_medium_001.ogg | pitched -1.39 semitones |
| start.mp3 | Kenney Interface Sounds | confirmation_001.ogg | pitched +0.02 semitones |

BGM, jingles (happy / perfect / sad / finish) and the sizzle loop: original (music.py), FluidSynth + FluidR3_GM (MIT).
