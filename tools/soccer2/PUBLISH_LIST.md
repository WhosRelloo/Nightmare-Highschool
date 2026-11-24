# Soccer 2.0: clips for the owner to publish

The FIER clips play in Studio from `ReplicatedStorage.NHSoccerClips`, through temporary ids. A live server needs real
asset ids.

1. Publish each KeyframeSequence below to group 15981569 (right-click, Save to Roblox, Animation, the group as the
   creator). See `docs/Pipeline-Lessons.md` for group asset ids.
2. Put each id in `ReplicatedStorage.Config.Sports.SoccerAnims` as `Id = <number>` beside its `Clip`.
3. Tell Claude. The ids get checked through the itemconfiguration API in the built-in browser, then mirrored to
   `tools/soccer2/live/ReplicatedStorage.Config.Sports.luau`.

| NHSoccerClips name | Slot(s) | Loops |
|---|---|---|
| Strike Foward Jog_R6 | KickRun | no |
| KickSoccerball_Right | Kick | no |
| Soccer Pass_R6 | Pass | no |
| Scissor Kick_R6 | Volley | no |
| Soccer Spin_R6 | Dribble, Feint | no |
| Soccer Tackle_R6 | Tackle | no |
| Soccer Tackled_R6 | Tackled | no |
| Soccer Tackled2_R6 | Tackled2 | no |
| Soccer Trip_R6 | Trip | no |
| Fallen Idle_R6 | Fallen | yes |
| Goalkeeper Diving SaveLeft_R6 | KeeperDiveLeft | no |
| Goalkeeper Diving SaveRigh_R6 | KeeperDiveRight | no |
| Goalkeeper Catch_R6 | KeeperCatch | no |
| Goalkeeper CatchIdle_R6 | KeeperCatchIdle | yes |
| Goalkeeper Idle_R6 | KeeperIdle | yes |
| Goalkeeper StepLeft_R6 | KeeperStepLeft | yes |
| Goalkeeper StepRight_R6 | KeeperStepRight | yes |
| Soccer Idle_R6 | Idle | yes |
| Offensive Idle_R6 | IdleBall | yes |
| Jog Forward_R6 | Jog | yes |
| Jog Backward_R6 | JogBack | yes |
| Chip_R6 | Chip (2.1) | no |
| Stall Soccerball_R6 | Stall (2.1) | no |
| Soccer Penalty Kick_R6 | Penalty (2.2) | no |

`Kick Soccerball_R6` (the left-foot original) is baked too, but no slot uses it, so it doesn't need publishing.
