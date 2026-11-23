#!/bin/bash
# round_b.sh (Quiet Corners S4, 2026-11-23): every round B check in order, after round_start.sh. The wall checks need a fresh
# EmptyDesk case (slot 2's is fully worked), so qc_wall_reset runs first; restore.py puts the real Quests back.
cd "$(dirname "$0")"
mk(){ printf 'local Probe = game.Players.LocalPlayer.PlayerGui.NHQuietProbe\n%s\nreturn "ok"\n' "$1" > _qcp.lua; python -X utf8 -I client.py _qcp.lua >/dev/null; }
for c in qc_dialogue qc_dialogue_real; do echo "== $c"; python -X utf8 -I client.py ../checks/$c.lua; done
echo "== reset"; python -X utf8 -I server.py ../checks/qc_wall_reset.lua
echo "== qc_wall_server"; python -X utf8 -I server.py ../checks/qc_wall_server.lua
sleep 2.5 # the client sync of the Erased insight, and LINK_COOLDOWN (1.5 s) before the wall pins its own pair
echo "== qc_wall"; python -X utf8 -I client.py ../checks/qc_wall.lua
echo "== qc_book"; python -X utf8 -I client.py ../checks/qc_book.lua
mk 'Probe:Invoke("Wall", "EmptyDesk") task.wait(1)'; echo "== fit wall"; python -X utf8 -I client.py ../checks/qc_fit.lua
mk 'Probe:Invoke("WallClose") task.wait(0.4) Probe:Invoke("Book", true) task.wait(1)'; echo "== fit book"; python -X utf8 -I client.py ../checks/qc_fit.lua
mk 'Probe:Invoke("Book", false) task.wait(0.4) Probe:Invoke("Dialogue", { Type = "Node"; Id = 9001; Speaker = "Odette Marsh"; Role = "second year"; Clique = "Ink"; Relationship = "Friendly"; Text = "You came back. Nobody comes back after their first night in Room 106."; Choices = { "What happened in Room 106?", "Maybe you could show me around?", "Pay her ¥10 to keep quiet", "Stay out of my way." }; Tones = { "Ask", "Kind", "Sly", "Threat" } }) task.wait(2.5)'
echo "== fit dialogue"; python -X utf8 -I client.py ../checks/qc_fit.lua
mk 'Probe:Invoke("DialogueClose")'
