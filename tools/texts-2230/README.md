# 2.23.0: Texts like a messaging app

`live/` is what is in NH Combat Test (place version 1152). `pre/` is the same two scripts before this change (also in `ServerStorage.NH_Backup.TextsApp_pre_20261117`).

- `StarterPlayer.StarterPlayerScripts.Controllers.Gui.Phone`: the Texts block (`Local.Texts` up to `-- Classmates`) and the header line.
- `ServerScriptService.Services.Features.Phone`: `Shared.Texts(P, MarkRead, From)` and the `Texts` remote (marks one sender read).

See `docs/Phone.md`, "Texts (2.23.0)".
