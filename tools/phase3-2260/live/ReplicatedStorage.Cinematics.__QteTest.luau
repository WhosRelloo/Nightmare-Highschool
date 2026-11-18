-- A test cut for the interactive director (TestBridge / harness only; never in a quest). The Task 3 graph.
local Def = { Set = `Hall`; Actors = { { Name = `Self`; From = `Self`; Mark = `HallLook`; Pose = `Stand` } } }
Def.Graph = { start = `A`; segments = {
	A = { len = 3; prompt = { kind = `Press`; at = 1; beat = 0.6; slow = 0.3; on = { Perfect = `B`; Good = `B`; Miss = `C` } } };
	B = { len = 2; next = `D` }; C = { len = 2; next = `D` };
	D = { len = 3; prompt = { kind = `Mash`; at = 0.5; dur = 1.6; rate = 7; slow = 0.5; on = { Win = `E`; Lose = `E` } } };
	E = { len = 1 } } }
function Def.Build(Ctx)
	local function hold(Name, Dur, Dist)
		return { name = Name; dur = Dur; subject = Ctx.Mark(`HallLook`);
			camera = { keys = { { t = 0; pos = Ctx.Pos(`HallCam`); look = Ctx.Pos(`HallLook`); lens = 35 },
				{ t = Dur; pos = Ctx.Pos(`HallCam`) + Ctx.CF(`HallCam`).LookVector * Dist; look = Ctx.Pos(`HallLook`); lens = 35 } } }; noise = false }
	end
	return { segments = {
		-- (2.26.0) an actor plays a game clip through the toolkit's anim event, and an existing effect is emitted on it
		A = { shots = { (function()
				local S = hold(`A`, 3, 1)
				-- clips go in a shot's events (the toolkit's anim event: slow-motion and hitstop apply to them)
				S.events = { { t = 0.2; anim = { rig = Ctx.Actor(`Self`); id = Ctx.GameClip(`Weapons.Fist.Moves.Shove`) } } }
				return S
			end)() }; events = {
			{ t = 0.4; fx = { template = `CombatFX.Flashstep`; at = Ctx.Actor(`Self`); part = `Torso`; count = 12 } };
		} }; B = { shots = { hold(`B`, 2, 2) } }; C = { shots = { hold(`C`, 2, 2) } };
		D = { shots = { hold(`D`, 3, 1) } }; E = { shots = { hold(`E`, 1, 0.5) } } } }
end
return Def
