# Nightmare Highschool

A Roblox school-life action RPG set in a cursed high school after dark. Races are Human, Priest and Vampire, the currency is Yen, and the interaction key is **E**. All content is original.

This repo holds the project's **changelogs, update posts and design docs**. The game itself is built in Roblox Studio, in the NH Combat Test dev place.

| Path | What |
|---|---|
| [`CHANGELOG.md`](CHANGELOG.md) | Full changelog, newest first |
| [`updates/discord/`](updates/discord/) | Discord update posts, ready to paste (each under 2000 characters) |
| [`docs/`](docs/) | Design and build docs: combat, school clock, attendance and discipline, classes, factions, quests, the UI kit |
| [`art/dev-products/`](art/dev-products/) | Icons for the Spin Shop's Developer Products (512 px, upload them on the Creator Dashboard); generator in [`tools/dev-products/`](tools/dev-products/) |
| [`tools/vfx/`](tools/vfx/) | Blender (Cycles) script that renders the main menu's VFX sprites (volumetric smoke flipbook, plasma, crystal shards, embers, mist), plus `make_soft_vfx.py`: soft-edged tendril, shard and film-grain textures |
| [`tools/ui-textures/`](tools/ui-textures/) | Python scripts that generate the UI kit's original gothic textures, with PBR lighting baked in (`pip install pillow numpy`) |

![UI kit preview](docs/img/ui-kit-preview.jpg)

## Latest update
**The bell rings (2026-10-31):** a school bell and period card, a "Spotted!" alert when a hall monitor chases you, and banners for quests, clues, level-ups, purchases and respawns. See [`CHANGELOG.md`](CHANGELOG.md), [`docs/VFX-Design-Bible.md`](docs/VFX-Design-Bible.md) and [the Discord post](updates/discord/2026-10-31-the-bell-rings.md).
