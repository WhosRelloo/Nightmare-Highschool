--[[
	Prologue: Roll Call (Chapter One opens). ReplicatedStorage.Cinematics.Prologue, played by Controllers.Cine.
	About 31 s (Config.Cine.Cuts.Prologue.Length). Doc: docs/expansion/04-Cinematic-Framework.md, 11-Phase1-Plan.md.

	The beat: the bell rings over the hallway on your first morning; you hurry to Room 102 with the other late ones; Mr.
	Hale reads the register; you answer to your own name; he reads "Holt. Mira Holt." and nobody answers. The empty
	back-row desk, the chapter's one dolly zoom. He frowns, moves on. You get up, and the camera lands behind your
	shoulder where you now stand (the server put your real character on the Arrive mark).

	Staged only from marks in workspace.NHCineSets.RollCall (each place has its own, so the cut ports unchanged):
	  EntranceCam / EntranceLook   the opening still wide's camera and aim (the hallway mouth, looking down the hall)
	  HallA1..3 -> HallB1..3       where the late students start and where they're heading (the classroom door)
	  BackCam / BackLook           Room 102 from the back corner, across the back row to the teacher
	  HaleMark                     Mr. Hale, standing at his desk, facing the class
	  SeatSelf, SeatS1..S4         seat tops (Seat = true): you, and the four classmates who answer the roll
	  MiraChair, MiraDesk          the empty back-row seat beside yours, and her desk (a desk-sized Part: the shot's subject)
	  Arrive                       on the floor in the aisle beside your seat: where you stand at the end (the server
	                               moves your real character here before the cut starts)
	  Bell                         attribute BellPart = the bell part's full name (it swings on the ring)
	The line runs Hale <-> the back row. Every coverage shot stays on one side of it: Hale is shot from his left
	(positive yaw), the back row from its right (negative yaw).
]]

local HALE_SPEAKS = Color3.fromRGB(196, 160, 112)

local Def = {
	Set = `RollCall`;
	Clock = 7.9; -- first period, a little before eight (on this screen only)
	Actors = {
		{ Name = `Hale`; From = { `Npc:Hale`; `Watcher:StaffRoom` }; Mark = `HaleMark`; Pose = `Stand`; Display = `Mr. Hale`; Color = HALE_SPEAKS };
		{ Name = `Self`; From = `Self`; Mark = `HallA1`; Pose = `Stand` };
		{ Name = `S1`; From = { `Ambient`; `Npc:Pip` }; Mark = `HallA2`; Pose = `Stand`; Display = `Student` };
		{ Name = `S2`; From = { `Ambient`; `Npc:Dex` }; Mark = `HallA3`; Pose = `Stand`; Display = `Student` };
		{ Name = `S3`; From = { `Ambient`; `Npc:Bruno` }; Mark = `SeatS3`; Pose = `Sit`; Display = `Student` };
		{ Name = `S4`; From = { `Ambient`; `Npc:Lucien` }; Mark = `SeatS4`; Pose = `Sit`; Display = `Student` };
	};
}

function Def.Build(Ctx)
	local Hale = Ctx.Actor(`Hale`)
	local Self = Ctx.Actor(`Self`)
	local Desk = Ctx.Mark(`MiraDesk`)
	-- a subject that's missing (no Hale in this server) falls back to his mark, so the framing still holds
	local function subj(A, Mark) return Ctx.Actor(A) or Ctx.Mark(Mark) end

	-- the register in Hale's hand: dark leather, held up to read
	-- held at chest height, tipped toward him, so his face stays clear above it
	Ctx.Hold(`Hale`, `Register`, Vector3.new(1.3, 0.16, 1.7), Color3.fromRGB(58, 34, 28), CFrame.new(0, -1.1, -0.45) * CFrame.Angles(math.rad(-48), 0, 0))

	-- the dolly zoom's aim (the desk top and the empty chair behind it) and its direction (yaw 8 off the desk's facing,
	-- 28 degrees down), in the desk mark's own frame so it ports with the mark
	local DeskCF = Ctx.CF(`MiraDesk`)
	-- (the mark faces the board, local -Z; the chair is behind it, local +Z)
	local DeskFocus = (DeskCF * CFrame.new(0, 0.7, 0.6)).Position
	local DeskDir = DeskCF:VectorToWorldSpace(Vector3.new(math.sin(math.rad(8)) * math.cos(math.rad(28)), math.sin(math.rad(28)), -math.cos(math.rad(8)) * math.cos(math.rad(28))))

	local First = Ctx.First
	local Full = Ctx.Name

	local shots = {
		-- 1. The bell. A still wide at 22 mm down the hallway as it rings; the late ones break into a hurry.
		{ name = `Bell, the hallway`; dur = 3.4; subject = subj(`Self`, `HallA1`); fadeIn = 0.8;
			camera = { keys = {
				{ t = 0; pos = Ctx.Pos(`EntranceCam`); look = Ctx.Pos(`EntranceLook`); lens = 22 };
				{ t = 3.4; pos = Ctx.Pos(`EntranceCam`, Vector3.new(0, -0.25, 0)) + Ctx.CF(`EntranceCam`).LookVector * 0.8; look = Ctx.Pos(`EntranceLook`); lens = 22 };
			} };
			noise = { preset = `handheld_wide_mild`; gain = 0.35 } };
		-- 2. Hurry. Track your own student down the hall to the door (from their right, the side the door is on).
		-- from your left, the open side of the hall (the classroom wall is on your right); the others are ahead of you
		{ name = `Hurry`; dur = 3.6; subject = subj(`Self`, `HallA1`);
			camera = { frame = { size = `MWS`; yaw = 58; pitch = 4; lens = 35 }; to = { size = `MS`; yaw = 36; pitch = 2 }; ease = `inout`; follow = `track` };
			noise = `auto`; dof = true };
		-- 3. Room 102 from the back corner: the class sits, Hale reads the register.
		{ name = `Room 102, the back`; dur = 4.2; subject = subj(`Hale`, `HaleMark`);
			camera = { keys = {
				{ t = 0; pos = Ctx.Pos(`BackCam`); look = Ctx.Pos(`BackLook`); lens = 28 };
				{ t = 4.2; pos = Ctx.Pos(`BackCam`) + (Ctx.Pos(`BackLook`) - Ctx.Pos(`BackCam`)).Unit * 1.2; look = Ctx.Pos(`BackLook`); lens = 28 };
			} };
			noise = { preset = `handheld_normal_mild`; gain = 0.3 }; dof = { at = subj(`Hale`, `HaleMark`) } };
		-- 4. Hale, medium: the names go by.
		{ name = `Hale reads`; dur = 2.8; subject = subj(`Hale`, `HaleMark`);
			camera = { frame = { size = `MS`; yaw = 18; pitch = 3; lens = 50 } }; noise = `auto`; dof = true };
		-- 5. You answer to your name.
		{ name = `You answer`; dur = 2.4; subject = subj(`Self`, `SeatSelf`);
			camera = { frame = { size = `MCU`; yaw = -28; pitch = 2; lens = 50 } }; noise = `auto`; dof = true };
		-- 6. Hale reads on: "Holt." A breath. "Mira Holt." The camera creeps in on him.
		{ name = `Holt`; dur = 3.2; subject = subj(`Hale`, `HaleMark`);
			-- side pinned: on "auto" the eyes jumped from the right third to centre mid-push (a sudden pan)
			camera = { frame = { size = `MCU`; yaw = 16; pitch = 2; lens = 65; side = `right` }; to = { size = `CU`; yaw = 12; side = `right` }; ease = `inout` };
			noise = { preset = `handheld_tele_mild`; gain = 0.3 }; dof = true };
		-- 7. Silence. His eyeline: the empty desk in the back row. The chapter's one dolly zoom (85 -> 30 mm at a
		--    constant size, so the room opens out behind the desk while the desk holds still).
		{ name = `The empty desk`; dur = 4.8; subject = Desk;
			-- sizes are multiples of the subject's height: on a 2.5-stud desk a full shot (1.2x) frames the desk and its empty
			-- chair; CU (0.28x) would put the lens on the desktop
			-- from Hale's side of the room, looking down over the seated heads at 28 degrees. A true dolly zoom as keys:
			-- one direction, the distance scaled with the lens (85 mm at 12.6 studs -> 30 mm at 4.45), so the desk and
			-- its empty chair hold their size while the room opens out behind them
			camera = { keys = {
				{ t = 0; pos = DeskFocus + DeskDir * 12.6; look = DeskFocus; lens = 85 };
				{ t = 4.8; pos = DeskFocus + DeskDir * 4.45; look = DeskFocus; lens = 30 };
			}; ease = `smooth` };
			noise = false; dof = { at = Desk } };
		-- 8. Hale looks up from the register, frowns, and moves on.
		{ name = `Moving on`; dur = 3.0; subject = subj(`Hale`, `HaleMark`);
			camera = { frame = { size = `MCU`; yaw = 22; pitch = 1; lens = 50 } }; noise = `auto`; dof = true };
		-- 9. You get up. The camera lands behind your shoulder, where play picks up.
		-- over your shoulder at what you're facing: Hale at his desk (your next stop)
		{ name = `Behind you`; dur = 3.6; subject = subj(`Hale`, `HaleMark`);
			camera = { keys = {
				-- Arrive is in the aisle about 8.5 studs in front of the back wall: the camera pulls back to just inside it
				{ t = 0; pos = (Ctx.CF(`Arrive`) * CFrame.new(2.6, 3.3, 4.6)).Position; look = (Ctx.CF(`Arrive`) * CFrame.new(0, 2.6, -6)).Position; lens = 35 };
				{ t = 3.6; pos = (Ctx.CF(`Arrive`) * CFrame.new(1.4, 5.0, 7.8)).Position; look = (Ctx.CF(`Arrive`) * CFrame.new(0, 3.4, -8)).Position; lens = 36 };
			}; ease = `inout` };
			noise = { preset = `handheld_normal_mild`; gain = 0.25 } };
	}

	-- shot starts (the events are on the cut's clock)
	local T = {}
	local At = 0
	for I, S in shots do T[I] = At At += S.dur end

	local events = {
		-- 1 / 2: the bell, the hurry
		{ t = 0.35; bell = {} };
		{ t = 0.2; walk = { who = `S1`; to = `HallB2`; dur = 5.2 } };
		{ t = 0.5; walk = { who = `S2`; to = `HallB3`; dur = 5.0 } };
		{ t = 0.9; walk = { who = `Self`; to = `HallB1`; dur = 5.4 } };
		{ t = 1.2; card = { title = `Chapter One`; sub = `The Empty Desk`; dur = 2.2 } };
		{ t = T[2] + 1.1; look = { who = `Self`; at = `HallB1` } };
		-- 3: everyone seated (a cut hides the move); Hale reading
		{ t = T[3]; place = { who = `Self`; to = `SeatSelf`; pose = `SitHands` } };
		{ t = T[3]; place = { who = `S1`; to = `SeatS1`; pose = `Sit` } };
		{ t = T[3]; place = { who = `S2`; to = `SeatS2`; pose = `SitHands` } };
		{ t = T[3]; look = { who = `Self`; at = `Hale` } };
		{ t = T[3]; pose = { who = `Hale`; name = `Read`; speed = 100 } };
		{ t = T[3] + 0.6; say = { who = `Hale`; text = `Abernathy.`; dur = 1.1 } };
		{ t = T[3] + 1.5; say = { who = `S3`; text = `Here.`; dur = 0.9 } };
		{ t = T[3] + 1.6; look = { who = `S3`; at = `Hale` } };
		{ t = T[3] + 2.3; say = { who = `Hale`; text = `Carrow.`; dur = 1.0 } };
		{ t = T[3] + 3.2; say = { who = `S4`; text = `Present.`; dur = 0.9 } };
		-- 4
		{ t = T[4] + 0.3; say = { who = `Hale`; text = `Fitch.`; dur = 0.9 } };
		{ t = T[4] + 1.1; say = { who = `S1`; text = `Here, sir.`; dur = 1.0 } };
		{ t = T[4] + 1.9; say = { who = `Hale`; text = function() return `{Full}.` end; dur = 1.2 } };
		-- 5: you
		{ t = T[5] + 0.45; say = { who = `Self`; name = First; text = `Here.`; dur = 1.2 } };
		{ t = T[5] + 0.4; pose = { who = `Self`; name = { RS = 1.0; LS = 0.9; Lean = 0.1; Pitch = -0.04 }; speed = 5 } };
		-- 6: Holt
		{ t = T[6] + 0.3; say = { who = `Hale`; text = `Holt.`; dur = 1.1 } };
		{ t = T[6] + 1.9; say = { who = `Hale`; text = `Mira Holt.`; dur = 1.3 } };
		-- 7: nobody answers. The Archive's faint choral tone, pitched down, under the silence.
		{ t = T[7] + 0.2; sound = { id = `rbxassetid://9125602882`; volume = 0.3; speed = 0.8 } };
		{ t = T[7] + 0.4; look = { who = `Self`; at = `MiraDesk` } };
		-- 8: he looks up, frowns, moves on
		{ t = T[8]; pose = { who = `Hale`; name = { RS = 0.7; LS = 0.55; Pitch = -0.02; Lean = 0.02 }; speed = 3 } };
		{ t = T[8]; look = { who = `Hale`; at = `MiraDesk`; speed = 3 } };
		{ t = T[8] + 1.2; say = { who = `Hale`; text = `...Moving on.`; expr = `frown`; dur = 1.3 } };
		{ t = T[8] + 2.2; look = { who = `Hale`; at = false } };
		{ t = T[8] + 2.2; pose = { who = `Hale`; name = `Read`; speed = 4 } };
		{ t = T[8] + 2.4; say = { who = `Hale`; text = `Price.`; dur = 0.8 } };
		-- 9: you stand up into the aisle
		{ t = T[9] + 0.15; look = { who = `Self`; at = false } };
		-- out of the chair sideways into the aisle, then forward to where play picks up (never through the desk)
		{ t = T[9] + 0.3; walk = { who = `Self`; to = `Aisle`; dur = 0.8; pose = `Stand`; speed = 7 } };
		{ t = T[9] + 1.15; walk = { who = `Self`; to = `Arrive`; dur = 1.3 } };
	}

	return { shots = shots; events = events; duration = At;
		grade = { contrast = 0.1; saturation = -0.12; tint = { 255, 236, 212 }; bloom = { intensity = 0.5; size = 40; threshold = 0.95 } } }
end

return Def
