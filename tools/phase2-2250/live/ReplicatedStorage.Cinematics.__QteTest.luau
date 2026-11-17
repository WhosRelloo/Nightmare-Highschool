-- A test cut for the interactive director (TestBridge / harness only; never in a quest). The Task 3 graph.
local Def = { Set = `Hall` }
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
		A = { shots = { hold(`A`, 3, 1) } }; B = { shots = { hold(`B`, 2, 2) } }; C = { shots = { hold(`C`, 2, 2) } };
		D = { shots = { hold(`D`, 3, 1) } }; E = { shots = { hold(`E`, 1, 0.5) } } } }
end
return Def
