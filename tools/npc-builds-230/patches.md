# 2.3.0 NPC builds: the live edits

`NpcBuilds.luau` here is the whole of the new `ReplicatedStorage.Config.NpcBuilds` (byte-identical to NH Combat Test's).
The other scripts got only the targeted edits below. Pre-edit copies are in NH Combat Test's
`ServerStorage.NH_Backup.NpcBuilds_pre220` (Appearance, Schedules, AmbientNpcs).

## ReplicatedStorage.UI.Appearance (both places)

1. In the NPC height block of the `ApplyTo` height wrapper, right after
   `local scale = Heights.Scale(nil, (seed % 9973) / 9973)`:

```lua
			-- (2.3.0) a student with a build (Config.NpcBuilds: by clique and personality) is that height
			local want = character:GetAttribute("NHHeightWant")
			if type(want) == "number" and want == want then
				scale = math.clamp(want, 0.86, 1.22)
			end
```

2. A new wrapper between the height wrapper's `end` and `function Appearance.StartServer()`:

```lua
-- (2.3.0) an NPC's posture (Config.NpcBuilds: the joints' C1) is taken off while its look is built and scaled, then put
-- back, so the height's scale and stretch never act on it
do
	local rawApply = Appearance.ApplyTo
	Appearance.ApplyTo = function(character, data)
		if not character:GetAttribute("NHPostureOn") then
			return rawApply(character, data)
		end
		local NpcBuilds = require(ReplicatedStorage:WaitForChild("Config"):WaitForChild("NpcBuilds"))
		NpcBuilds.ClearPosture(character)
		local ok, r = pcall(rawApply, character, data)
		if character.Parent then
			NpcBuilds.SetPosture(character, true)
		end
		if not ok then
			error(r, 0)
		end
		return r
	end
end
```

3. The Map only: `local NPC_HEIGHT = { NHSchedule = true, NHAmbient = true, NHStudents = true }` (MapStudents' folder;
   before 2.3.0 the Map's students had no height at all).

## ServerScriptService.Services.Features.Schedules (NH Combat Test)

- Requires: `local NpcBuilds = require(ReplicatedStorage.Config.NpcBuilds)` after `CliqueConfig`.
- `Local.Pose`: after the loop that stops the other tracks,
  `if S.Model then NpcBuilds.SetPosture(S.Model, Name == nil) end` (posture while standing / walking; straight while
  seated, leaning or eating).
- `Local.Spawn`, after the `Clique` attribute: when `S.Build`, set `NHHeightWant` (height), `NHPosture` (torso degrees)
  and `NHBuild` (`NpcBuilds.Describe`).
- `Local.Spawn`, after `ApplyTo` and the collision loop: `S.Up = Root.Size.Y / 2 + Hum.HipHeight + Leg.Size.Y` and
  `S.Stride = Leg.Size.Y / 1.8` from the scaled `Left Leg`, then `NpcBuilds.SetPosture(M, true)`.
- `Idle:Play(0.1, 1, S.Build and S.Build.Idle or 1)`.
- The `Running` handler: `Walk:AdjustSpeed(Speed / (WALK_PACE * (S.Stride or 1)))`, and the same for `RUN_PACE`.
- `Shared.OnStart`: `local Build = NpcBuilds.Roll("Schedule|" .. I, Clique, Female)`; `Look.Body =
  NpcBuilds.BodyFor(Appearance, Female, Build)`; the student's `Bravery`, `Social`, `Speed` come from the build (they
  were `math.random`) and `Build = Build` is stored on the student.

## ServerScriptService.Services.Features.AmbientNpcs (NH Combat Test)

In `Local.Spawn`'s look, after the `RandomPiece` calls: the clique from `Config.Cliques.Npcs[Name]` (else Ordinary),
`NpcBuilds.Roll("Ambient|<Name>|<x>,<z>", Clique, Female)`, `Look.Body = NpcBuilds.BodyFor(...)`, and the model's
`NHHeightWant` and `NHBuild`. No posture (they're doing reps, sitting or napping).

## ServerScriptService.Services.Features.MapStudents (the Map)

See `docs/NPC-Builds.md` ("The Map"): the same as Schedules, with the Map's own `rollLook`, `spawn` and `pose`.
