--[[
	NpcBuilds (shared config). ReplicatedStorage.Config.NpcBuilds          (2.3.0, owner: "I want the NPC's to have random
	heights, etc. based on their respective cliques and personalities.")

	Every student NPC gets a build from its clique and its personality, rolled from a stable key, so the same student has
	the same height, body, posture and pace every time they spawn:
	  Height    a scale on a normal R6 (Config.Heights: 1.00 = 5'9"), inside the clique's range (girls 0.03 shorter),
	            never outside the Human range 0.86..1.22 (1.22 is the doorway ceiling)
	  Body      a UI.Appearance body type (its Build and Step) by the clique's weights, in the student's own gender
	  Bravery   0..1, Brave >= 0.5, Timid under it (StudentBrain lines, Senses)      } each clique leans its own way
	  Social    0..1, Social >= 0.5, Shy under it (StudentBrain lines, view range)    }
	  Torso     posture: degrees the upper body (torso, head and arms together) leans forward from the hips; - = stands
	            tall, chest out and chin up
	  Pace      walk-speed multiplier; Speed the student's stroll in studs/s (Schedules' S.Speed)
	  Idle      the idle clip's tempo: lively (Social) or subdued (Shy)
	A Timid student hunches, head down, and walks slower; a Brave one stands tall and walks with purpose.

	Posture is put on the joints' C1 (RootJoint and the hips), so the clips, NpcLook's head turns (Neck.C0) and
	ContactFeel's lean (RootJoint.C0) still work on top of it. The upper body pivots at the hip line and the legs are
	turned back, so the feet, the hips (seating) and the legs don't move. The head never tilts on its own: measured
	with every barber hair, even 2 degrees of head-on-torso tilt pushes the long hairs into the back or chest (0.02
	studs), while the whole upper body leaning keeps them clear of the legs at any angle. Students sit, lean and eat with
	no posture (Schedules' Local.Pose takes it off).

	Used by Services.Features.Schedules (class students) and Services.Features.AmbientNpcs (heights and bodies; no
	posture: they're doing reps, sitting or napping). UI.Appearance builds the height (the model's NHHeightWant).
]]

local NpcBuilds = {}

NpcBuilds.MinHeight, NpcBuilds.MaxHeight = 0.86, 1.22 -- the Human range (Config.Heights.Races.Human)
NpcBuilds.FemaleHeight = -0.03
NpcBuilds.BaseSpeed = 6.0 -- about the old random stroll's middle (5.4 .. 7.0)
-- 7.2 x StudentBrain's hurry (1.35) stays under 10, where Schedules switches to the run clip
NpcBuilds.MinSpeed, NpcBuilds.MaxSpeed = 4.8, 7.2

-- Height { shortest, tallest }; Bravery / Social { low, high }; Torso the clique's own posture (degrees);
-- Pace its walk; Bodies { Build, Step, Weight } (UI.Appearance.Bodies: Average 0, Skinny 1, Conditioned 1-2, Heavy 1-2)
NpcBuilds.Cliques = {
	-- jocks: the tallest and broadest, chest out, a quick stride
	Athletes = { Height = { 1.02, 1.20 }; Bravery = { 0.50, 0.90 }; Social = { 0.50, 0.95 }; Torso = -1; Pace = 1.08;
		Bodies = { { `Conditioned`, 1, 5 }, { `Conditioned`, 2, 4 }, { `Average`, 0, 1 } } };
	-- wolf-blooded bullies: rangy (tall and long, lean or wiry), a forward prowl
	Pack = { Height = { 1.00, 1.18 }; Bravery = { 0.55, 0.95 }; Social = { 0.40, 0.85 }; Torso = 1; Pace = 1.04;
		Bodies = { { `Skinny`, 1, 5 }, { `Conditioned`, 1, 4 }, { `Average`, 0, 1 } } };
	-- the night elite: upright and poised, chin up, unhurried
	Court = { Height = { 0.96, 1.12 }; Bravery = { 0.45, 0.85 }; Social = { 0.55, 0.95 }; Torso = -3; Pace = 0.94;
		Bodies = { { `Average`, 0, 5 }, { `Skinny`, 1, 3 }, { `Conditioned`, 1, 2 } } };
	-- greasers: a slouch, a slow swagger, some heavy-set
	Delinquents = { Height = { 0.94, 1.12 }; Bravery = { 0.50, 0.90 }; Social = { 0.30, 0.80 }; Torso = 2; Pace = 0.96;
		Bodies = { { `Average`, 0, 4 }, { `Heavy`, 1, 3 }, { `Conditioned`, 1, 2 }, { `Heavy`, 2, 1 } } };
	-- scholars: bookish, a little stooped over their notes
	Vigil = { Height = { 0.92, 1.08 }; Bravery = { 0.30, 0.70 }; Social = { 0.15, 0.60 }; Torso = 2; Pace = 1.00;
		Bodies = { { `Average`, 0, 6 }, { `Skinny`, 1, 3 }, { `Heavy`, 1, 1 } } };
	-- the faithful: upright, most of them average
	Choir = { Height = { 0.90, 1.06 }; Bravery = { 0.25, 0.75 }; Social = { 0.40, 0.90 }; Torso = -1; Pace = 0.98;
		Bodies = { { `Average`, 0, 6 }, { `Skinny`, 1, 2 }, { `Heavy`, 1, 2 } } };
	-- regulars: slighter, and mostly timid
	Ordinary = { Height = { 0.87, 1.04 }; Bravery = { 0.10, 0.60 }; Social = { 0.30, 0.80 }; Torso = 1; Pace = 1.00;
		Bodies = { { `Average`, 0, 5 }, { `Skinny`, 1, 4 }, { `Heavy`, 1, 1 } } };
	-- artists: the slightest, hunched from the back rows
	Ink = { Height = { 0.86, 1.02 }; Bravery = { 0.25, 0.75 }; Social = { 0.15, 0.70 }; Torso = 2; Pace = 0.97;
		Bodies = { { `Skinny`, 1, 6 }, { `Average`, 0, 4 } } };
}
NpcBuilds.Default = `Ordinary`

-- personality on top of the clique (per point away from 0.5): a Timid student (0.1) hunches about 5 degrees more and
-- walks 10% slower, a Brave one (0.9) stands about 5 degrees taller and walks 10% faster.
-- The clamp keeps the torso's bottom edge within 0.06 studs of the leg tops (0.5 x sin 7 degrees).
NpcBuilds.Personality = { TorsoPerBravery = -12; HeightPerBravery = 0.04; PacePerBravery = 0.24 }
NpcBuilds.TorsoClamp = { -5, 7 }

-- a stable number for a key (the same string always gives the same seed)
function NpcBuilds.Seed(Key: string): number
	local H = 5381
	for I = 1, #Key do
		H = (H * 33 + string.byte(Key, I)) % 2147483647
	end
	return H
end

local function between(R: Random, Range: { number }, Mid: boolean?): number
	local T = if Mid then (R:NextNumber() + R:NextNumber()) / 2 else R:NextNumber() -- Mid: most land near the middle
	return Range[1] + (Range[2] - Range[1]) * T
end

local function weighted(R: Random, List)
	local Total = 0
	for _, E in List do Total += E[3] end
	local X = R:NextNumber() * Total
	for _, E in List do
		X -= E[3]
		if X <= 0 then return E end
	end
	return List[#List]
end

-- the build for one student: Key is stable for that student (e.g. "Schedule|4"), Clique an id in Config.Cliques
function NpcBuilds.Roll(Key: string, Clique: string?, Female: boolean?)
	local C = NpcBuilds.Cliques[Clique or ``] or NpcBuilds.Cliques[NpcBuilds.Default]
	local R = Random.new(NpcBuilds.Seed(`{Key}|{Clique or NpcBuilds.Default}`))
	local P = NpcBuilds.Personality
	local B = {}
	B.Clique = if NpcBuilds.Cliques[Clique or ``] then Clique else NpcBuilds.Default
	B.Bravery = math.floor(between(R, C.Bravery) * 100 + 0.5) / 100
	B.Social = math.floor(between(R, C.Social) * 100 + 0.5) / 100
	local Height = between(R, C.Height, true) + (B.Bravery - 0.5) * P.HeightPerBravery
	if Female then Height += NpcBuilds.FemaleHeight end
	B.Height = math.clamp(Height, NpcBuilds.MinHeight, NpcBuilds.MaxHeight)
	local Body = weighted(R, C.Bodies)
	B.Build, B.Step = Body[1], Body[2]
	B.Torso = math.clamp(C.Torso + (B.Bravery - 0.5) * P.TorsoPerBravery + (R:NextNumber() - 0.5), NpcBuilds.TorsoClamp[1], NpcBuilds.TorsoClamp[2])
	R:NextNumber() -- (kept so the rolls after it stay the same)
	B.Pace = C.Pace * (1 + (B.Bravery - 0.5) * P.PacePerBravery)
	-- longer legs stroll a little faster (taller students aren't slower)
	B.Speed = math.clamp(NpcBuilds.BaseSpeed * B.Pace * B.Height ^ 0.35 * (0.97 + R:NextNumber() * 0.06), NpcBuilds.MinSpeed, NpcBuilds.MaxSpeed)
	B.Idle = 0.85 + B.Social * 0.3
	return B
end

-- the body index for a build (UI.Appearance passed in; a place without body types keeps the gender's base body)
function NpcBuilds.BodyFor(Appearance, Female: boolean, B): number?
	if not (Appearance and Appearance.BodyFor) then return nil end
	return Appearance.BodyFor(if Female then `Female` else `Male`, B.Build, B.Step)
end

-- "Athletes | 6'4\" Conditioned 2 | brave 0.81 social 0.62 | torso -4.0 | speed 7.04" (the model's NHBuild)
function NpcBuilds.Describe(B): string
	local In = math.floor(B.Height * 69 + 0.5)
	return string.format(`%s | %d'%d" %s %d | brave %.2f social %.2f | torso %.1f | speed %.2f`, B.Clique,
		In // 12, In % 12, B.Build, B.Step, B.Bravery, B.Social, B.Torso, B.Speed)
end

---| posture |---
-- The model's NHPosture (degrees the upper body leans forward) is the student's posture; NHPostureOn is what's on the
-- joints now. The C1s before the posture are kept on the joints (NHPreC1) while it's on, and put back exactly.
local JOINTS = { { `HumanoidRootPart`, `RootJoint` }, { `Torso`, `Right Hip` }, { `Torso`, `Left Hip` } }
local function joints(M: Model)
	local Out = {}
	for _, J in JOINTS do
		local P = M:FindFirstChild(J[1])
		local X = P and P:FindFirstChild(J[2])
		if not (X and X:IsA(`Motor6D`)) then return nil end
		Out[J[2]] = X
	end
	return Out
end

function NpcBuilds.ClearPosture(M: Model)
	local J = joints(M)
	if J then
		for _, X in J do
			local Pre = X:GetAttribute(`NHPreC1`)
			if typeof(Pre) == `CFrame` then X.C1 = Pre end
			X:SetAttribute(`NHPreC1`, nil)
		end
	end
	M:SetAttribute(`NHPostureOn`, nil)
end

-- On: the student's own posture; false: standing straight (seated, leaning, eating)
function NpcBuilds.SetPosture(M: Model, On: boolean)
	local Want = M:GetAttribute(`NHPosture`)
	if not On or type(Want) ~= `number` or Want ~= Want or math.abs(Want) < 0.05 then Want = nil end
	if Want then Want = math.clamp(Want, NpcBuilds.TorsoClamp[1], NpcBuilds.TorsoClamp[2]) end
	local Now = M:GetAttribute(`NHPostureOn`)
	if Want == Now then return end
	NpcBuilds.ClearPosture(M)
	if not Want then return end
	local J = joints(M)
	local T = M:FindFirstChild(`Torso`)
	if not (J and T and T:IsA(`BasePart`)) then return end
	for _, X in J do X:SetAttribute(`NHPreC1`, X.C1) end
	-- the torso (with the head and arms on it) pitched forward Want degrees about the middle of its bottom edge (the hip
	-- line), in the torso's space
	local Q = Vector3.new(0, -T.Size.Y / 2, 0)
	local Rot = CFrame.new(Q) * CFrame.Angles(-math.rad(Want), 0, 0) * CFrame.new(-Q)
	J.RootJoint.C1 = Rot:Inverse() * J.RootJoint.C1
	-- the legs turned back, so they and the feet stay where they were (the hips sit on the pivot line)
	for _, N in { `Right Hip`, `Left Hip` } do
		local H = J[N]
		H.C1 = H.C1 * H.C0:Inverse() * Rot * H.C0
	end
	M:SetAttribute(`NHPostureOn`, Want)
end

return NpcBuilds
