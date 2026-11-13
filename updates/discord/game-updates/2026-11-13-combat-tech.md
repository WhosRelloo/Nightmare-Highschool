# Snappier fights (2.13.0)

**Nightmare Highschool dev update, 2026-11-13**

- **Your punches start the instant you click.** Before, every swing waited for the server first, so the higher your
  ping, the laggier it felt. Now your character swings straight away, and the server keeps up behind the scenes.
- **Hits land where you saw them.** If someone sidesteps on the server a split second before your fist connects, but
  your screen still showed them in front of you, the hit counts. There's a hard limit, so laggy players can't punch
  people who are long gone.
- **Under the hood.** A new combat log lets us measure every exchange (inputs, swings, hits, blocks, parries) to tune
  fights properly. We also fixed an old hitbox bug.
