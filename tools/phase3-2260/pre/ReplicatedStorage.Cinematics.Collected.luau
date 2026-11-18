--[[
	Collected (Chapter One ends). ReplicatedStorage.Cinematics.Collected, played by Controllers.Cine as the last stage of
	After Hours. About 13 s (Config.Cine.Cuts.Collected.Length).

	An insert of Mira's file, where "STATUS: COLLECTED" writes itself in red. A wide of the hallway at night: the Night
	Custodian stands at the far end, his face never seen. The bell rings once. Card: "End of Chapter One: The Empty Desk".

	Marks in workspace.NHCineSets.Hall:
	  File                 where the file lies (its top face is the page; front = the way the page reads)
	  HallCam / HallLook   the night wide's camera and aim, down the hallway
	  CustodianFar         the Custodian, far end of the hall, facing the camera
	  Bell                 attribute BellPart = the bell part's full name
]]

local Def = {
	Set = `Hall`;
	Clock = 0.2; -- just past midnight (on this screen only)
	Actors = {
		-- by day he's at his hallway post; after hours he's the Records Office watcher (Config.Npcs Custodian OffWhen)
		{ Name = `Custodian`; From = { `Npc:Custodian`; `Watcher:RecordsOffice` }; Mark = `CustodianFar`; Pose = `Stand`; Display = `Night Custodian`; Faceless = true };
	};
}

local PAPER = Color3.fromRGB(214, 200, 168)
local INK = Color3.fromRGB(46, 38, 32)
local RED = Color3.fromRGB(150, 22, 20)

function Def.Build(Ctx)
	-- the file: a manila folder with the record clipped on top
	local FileCF = Ctx.CF(`File`)
	local Folder = Ctx.Prop(`FileFolder`, { Size = Vector3.new(2.3, 0.06, 3.0); CFrame = FileCF * CFrame.new(0, 0.03, 0);
		Color = Color3.fromRGB(176, 140, 82); Material = Enum.Material.SmoothPlastic })
	-- the page is turned a quarter so its Top-face text reads upright from the camera's side (checked by capture)
	local Page = Ctx.Prop(`FilePage`, { Size = Vector3.new(2.7, 0.02, 2.0); CFrame = FileCF * CFrame.new(0.05, 0.07, -0.04) * CFrame.Angles(0, math.rad(-90 - 2.5), 0);
		Color = PAPER; Material = Enum.Material.SmoothPlastic })
	local Gui = Instance.new(`SurfaceGui`)
	Gui.Face = Enum.NormalId.Top
	Gui.CanvasSize = Vector2.new(400, 540)
	Gui.LightInfluence = 0.25 -- readable at midnight under the one warm light, still part of the scene
	Gui.Parent = Page
	-- one warm light over the desk (a torch beam on the file): the only light in the insert
	-- centred over the page and softer, so the red status line isn't washed out by the hot spot
	local Lamp = Ctx.Prop(`FileLight`, { Size = Vector3.new(0.2, 0.2, 0.2); Transparency = 1; CFrame = FileCF * CFrame.new(0, 3.0, 0.3) })
	local Light = Instance.new(`SpotLight`)
	Light.Face = Enum.NormalId.Bottom
	Light.Angle = 70
	Light.Range = 8
	Light.Brightness = 1.3
	Light.Color = Color3.fromRGB(255, 214, 160)
	Light.Shadows = true
	Light.Parent = Lamp
	local function line(Text: string, Y: number, Size: number, Font: Enum.Font, Color: Color3?)
		local L = Instance.new(`TextLabel`)
		L.BackgroundTransparency = 1
		L.Position = UDim2.fromOffset(34, Y)
		L.Size = UDim2.fromOffset(332, Size + 8)
		L.Font = Font
		L.TextSize = Size
		L.TextXAlignment = Enum.TextXAlignment.Left
		L.TextColor3 = Color or INK
		L.Text = Text
		L.Parent = Gui
		return L
	end
	line(`NIGHTMARE HIGHSCHOOL`, 26, 22, Enum.Font.Fondamento)
	line(`Student Record`, 54, 18, Enum.Font.Fondamento)
	line(`Name:  HOLT, Mira`, 120, 26, Enum.Font.SpecialElite)
	line(`Homeroom:  102 (Mr. Hale)`, 162, 22, Enum.Font.SpecialElite)
	line(`Seat:  back row`, 196, 22, Enum.Font.SpecialElite)
	line(`Attendance:  ............`, 230, 22, Enum.Font.SpecialElite)
	line(`STATUS:`, 330, 30, Enum.Font.SpecialElite)
	local Stamp = line(``, 370, 58, Enum.Font.SpecialElite, RED)
	Stamp.TextStrokeTransparency = 0.85
	Stamp.TextStrokeColor3 = RED

	local Custodian = Ctx.Actor(`Custodian`) or Ctx.Mark(`CustodianFar`)

	local shots = {
		-- 1. The insert: the file from above, a slow push as the word writes itself.
		{ name = `The file`; dur = 4.6; subject = Page; fadeIn = 0.6;
			camera = { keys = {
				-- the whole page in frame at first (~6.4 studs at 50 mm), a slow push toward the status line
				{ t = 0; pos = (FileCF * CFrame.new(0.4, 5.6, 3.2)).Position; look = (FileCF * CFrame.new(0, 0, 0.1)).Position; lens = 50 };
				{ t = 4.6; pos = (FileCF * CFrame.new(0.2, 4.2, 2.2)).Position; look = (FileCF * CFrame.new(0, 0, 0.35)).Position; lens = 50 };
			}; ease = `inout` };
			noise = { preset = `handheld_tele_mild`; gain = 0.25 }; dof = { at = Page } };
		-- 2. The hallway at night, very wide and still. He's at the far end. He doesn't move.
		{ name = `The hall at night`; dur = 5.4; subject = Custodian;
			camera = { keys = {
				{ t = 0; pos = Ctx.Pos(`HallCam`); look = Ctx.Pos(`HallLook`); lens = 24 };
				{ t = 5.4; pos = Ctx.Pos(`HallCam`) + Ctx.CF(`HallCam`).LookVector * 1.6; look = Ctx.Pos(`HallLook`); lens = 24 };
			} };
			noise = false };
		-- 3. Black, the card.
		{ name = `End card`; dur = 3.0; subject = Custodian; black = true;
			camera = { keys = { { t = 0; pos = Ctx.Pos(`HallCam`) + Ctx.CF(`HallCam`).LookVector * 1.6; look = Ctx.Pos(`HallLook`); lens = 24 } } };
			noise = false };
	}

	local events = {
		-- the word writes itself, letter by letter (a pen's pace, not a typewriter's)
		{ t = 1.5; call = function()
			local Word = `COLLECTED`
			for I = 1, #Word do
				if not Stamp.Parent then return end
				Stamp.Text = Word:sub(1, I)
				task.wait(0.13 + (if I == 1 then 0.1 else 0))
			end
		end };
		{ t = 0.4; sound = { id = `rbxassetid://9125602882`; volume = 0.25; speed = 0.75 } }; -- the Archive's choral tone
		{ t = 2.75; sound = { id = `rbxassetid://9119907907`; volume = 0.4; speed = 0.85 } }; -- the last letter lands (kit Stamp)
		-- the bell, once, as we hold on him
		{ t = 8.9; bell = { volume = 0.5; speed = 0.55 } };
		{ t = 10.0; veil = { alpha = 1; dur = 0.25 } };
		{ t = 10.1; card = { title = `End of Chapter One`; sub = `The Empty Desk`; dur = 2.7 } };
	}

	return { shots = shots; events = events; duration = 13.0; keepBlack = false;
		grade = { contrast = 0.16; saturation = -0.3; tint = { 196, 212, 255 }; bloom = { intensity = 0.4; size = 32; threshold = 0.97 } } }
end

return Def
