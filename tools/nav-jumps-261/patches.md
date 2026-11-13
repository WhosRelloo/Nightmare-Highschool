# 2.6.1: students stop hopping (both places)

## `ServerScriptService.Services.AI.Nav` (NH Combat Test and the Map, byte-identical)

The whole file is `Nav.luau` here. The 2.6.1 changes, each marked `(2.6.1)` in the source:

- `lipAhead(Self, Toward, Feet)` (new): a real step at the feet. Something at 0.35 studs up within radius + 1.6, whose
  top 0.4 studs past its front edge is 0.3 to 1.8 studs up (probed from 2.2 studs up, so anything taller is skipped),
  with 4 studs clear above it.
- `riseAt(P, Feet)` (new): the ground under a waypoint (`Nav.Floor(P, 2.5)`) minus the feet. Waypoints sit about 0.9
  studs over the floor.
- `stepUp(Self, Points, I, Feet)` (new): jump a Jump waypoint only if the ground there or at the next waypoint is over
  0.8 studs up, or 0.3 to 0.8 with `lipAhead`.
- `GoTo`:
  - the smoother resets `Best`/`Since` when it skips ahead;
  - reaching a Jump waypoint jumps only if `stepUp`;
  - the "jump the waypoint's ledge" line uses `riseAt(W.Position, Feet) > 0.8` (it was `W.Position.Y > Feet.Y + 0.8`);
  - stuck `Escalate == 1` jumps only if `riseAt(W.Position, Feet) > 0.3 and lipAhead(...)`, otherwise it sidesteps.

Backup: `ServerStorage.NH_Backup.NavJump_pre.Nav` (both places).

## `ServerScriptService.Services.Features.Schedules` (NH Combat Test only)

In `Local.Class`, replace

```lua
	local Front = (Chair:GetPivot() * CFrame.new(0, 0, 2.5)).Position
	Local.WalkTo(S, Job, Local.Floor(Front) or Front)
```

with

```lua
	local Front = (Chair:GetPivot() * CFrame.new(0, 0, 2.5)).Position
	-- (2.6.1) stand on the floor by the chair. Rows are 5 studs apart, so in the back rows 2.5 studs behind a chair is
	-- the top of the desk behind it: students were sent to stand on it, and the planner jumped them up there. Then the
	-- aisle beside the chair (halfway to the next column of chairs) is used.
	local Goal = Local.Floor(Front)
	local Low = Chair:GetPivot().Position.Y + 0.6
	if not Goal or Goal.Y > Low then
		for _, Off in { 3, -3 } do
			local F = Local.Floor((Chair:GetPivot() * CFrame.new(Off, 0, 0.8)).Position)
			if F and F.Y <= Low then Goal = F break end
		end
	end
	Local.WalkTo(S, Job, Goal or Front)
```

Backup: `ServerStorage.NH_Backup.NavJump_pre.Schedules` (NH Combat Test).
