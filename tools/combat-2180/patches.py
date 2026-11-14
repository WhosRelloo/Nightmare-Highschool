WEAP = "ReplicatedStorage.Config.Weapons"
AIR = "ServerStorage.Packages.AirCombat"
IN = "StarterPlayer.StarterPlayerScripts.Controllers.Character.InputController.Combat.M1"
PRED = "StarterPlayer.StarterPlayerScripts.Controllers.Character.InputController.Combat.M1.Predict"

EDITS = [
    # --- every fist swing plays its whole clip, at its own speed (owner: "I want the whole animation to play out") ---
    (WEAP, """		-- the owner's Fist animations have no Hit/EndLag keyframes: contact times read off the keyframes (fastest limb)
		Markers = {
			["rbxassetid://75262630901232"] = { Hit = 0.42; EndLag = 0.52 };
			["rbxassetid://93727306716155"] = { Hit = 0.27; EndLag = 0.40 };
			["rbxassetid://77050950909273"] = { Hit = 0.35; EndLag = 0.47 };
			["rbxassetid://138087015993934"] = { Hit = 0.38; EndLag = 0.50 };
			["rbxassetid://137090091936227"] = { Hit = 0.33; EndLag = 0.67 }; -- running straight (clip keyframe "Hit" 0.33)
			["rbxassetid://105679347584694"] = { Hit = 0.66; EndLag = 0.80 }; -- slam lands 0.60-0.68 (scrubbed in Play)""",
     """		-- the owner's Fist animations have no Hit/EndLag keyframes: contact times read off the keyframes (fastest limb)
		-- (2.18.0) the owner: "I want the whole animation to play out". A swing's EndLag is now the end of its clip
		-- (less 0.02 s, so the marker still fires while it plays): the next swing starts when this one has finished,
		-- instead of cutting it off 0.06-0.18 s early. Clip lengths: M1 0.58 / 0.57 / 0.57 / 0.57, running 1.00, air 0.98.
		Markers = {
			["rbxassetid://75262630901232"] = { Hit = 0.42; EndLag = 0.56 };
			["rbxassetid://93727306716155"] = { Hit = 0.27; EndLag = 0.55 };
			["rbxassetid://77050950909273"] = { Hit = 0.35; EndLag = 0.55 };
			["rbxassetid://138087015993934"] = { Hit = 0.38; EndLag = 0.55 };
			["rbxassetid://137090091936227"] = { Hit = 0.33; EndLag = 0.98 }; -- running straight (clip keyframe "Hit" 0.33)
			["rbxassetid://105679347584694"] = { Hit = 0.66; EndLag = 0.96 }; -- slam lands 0.60-0.68 (scrubbed in Play)"""),
    (WEAP, """		Model = nil; -- hands only

		AnimationSpeed = 1.15;""", """		Model = nil; -- hands only

		AnimationSpeed = 1; -- (2.18.0) was 1.15: the owner's clips play at the speed they were animated"""),
    # --- client prediction off by default: every swing comes from the server, start to finish ---
    (PRED, """	Off switch: ReplicatedStorage attribute NHPredictOff = true.""",
     """	(2.18.0) OFF by default: the owner wants every swing to play out whole ("forget about that quick stuff"), so the
	server's swing is the one everyone sees. Turn it back on with the ReplicatedStorage attribute NHPredictOn = true.
	Off switch (when on): ReplicatedStorage attribute NHPredictOff = true."""),
    (PRED, """	if ReplicatedStorage:GetAttribute(`NHPredictOff`) == true then return nil end""",
     """	if ReplicatedStorage:GetAttribute(`NHPredictOn`) ~= true then return nil end -- (2.18.0) off unless switched on
	if ReplicatedStorage:GetAttribute(`NHPredictOff`) == true then return nil end"""),
    # --- air combat: face the one you launched before every air swing ---
    (IN, """	Humanoid:SetStateEnabled(Enum.HumanoidStateType.Jumping, false)
""", """	-- (2.18.0) in air combat, turn to face the one you launched before each swing: a mouse player has no aim assist up
	-- there (LockOn.Core.Assist only turns to a locked target), so air hits 2-4 used to swing at empty air
	local function FaceAirTarget()
		if not TagService:HasTag(Character, `InAir`) then return end
		local Root = Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
		local Live = workspace:FindFirstChild(`Live`)
		if not (Root and Live) then return end
		local Best, BestD = nil, 14
		for _, M in Live:GetChildren() do
			local R = M ~= Character and M:FindFirstChild(`HumanoidRootPart`) :: BasePart?
			if R and TagService:HasTag(M, `InAir`) then
				local D = (R.Position - Root.Position).Magnitude
				if D < BestD then Best, BestD = R, D end
			end
		end
		if Best then
			Root.CFrame = CFrame.lookAt(Root.Position, Vector3.new(Best.Position.X, Root.Position.Y, Best.Position.Z))
		end
	end

	Humanoid:SetStateEnabled(Enum.HumanoidStateType.Jumping, false)
"""),
    (IN, """		local Flags = if Pressed then 0 else 2""", """		pcall(FaceAirTarget) -- (2.18.0)
		local Flags = if Pressed then 0 else 2"""),
]


# --- AirCombat.Reposition: keep the pair on the line of the attack, in fist reach, facing each other ---
REPOS_NEW = """-- (2.18.0) After an air hit, push the target a little further along the line of the attack and bring the attacker
-- in behind it, inside fist reach, both facing each other. It used to push the target back along ITS OWN facing and
-- move the attacker 5.5 studs toward where the target had been: after the first air hit the target ended up about 5
-- studs to the side, air hits 2-4 whiffed, and the 3-hit downslam finisher (the air crit) never came.
local AIR_PUSH = 2.5 -- studs the target is knocked along the attack each air hit
local AIR_GAP = 3.6  -- studs between the two after it (M1 reach is about 5.8: Offset 2.8 + half the 6-stud box)

function AirCombat.Reposition(User: Model, Target: Model, TargetOffset: number?, UserOffset: number?)
	local TargetRoot = Target:FindFirstChild(`HumanoidRootPart`)
	local UserRoot = User:FindFirstChild(`HumanoidRootPart`)

	if not TargetRoot or not UserRoot then return end

	if not TagService:HasTag(User, `InAir`) or not TagService:HasTag(Target, `InAir`) then
		return
	end

	local TargetAerial = BodyPositionModule.GetByTag(Target, `AerialPosition`)
	local UserAerial = BodyPositionModule.GetByTag(User, `AerialPosition`)

	if not TargetAerial or not UserAerial then
		return
	end

	TargetAerial.LastChanged = os.clock()
	TargetAerial.Timeout = 2.5

	UserAerial.LastChanged = os.clock()
	UserAerial.Timeout = 2.5

	TagService:AddTag(User, `InAir`, 3)
	TagService:AddTag(Target, `InAir`, 3)

	-- the line of the attack, flat
	local Dir = (TargetRoot.Position - UserRoot.Position) * Vector3.new(1, 0, 1)
	if Dir.Magnitude < 0.5 then Dir = UserRoot.CFrame.LookVector * Vector3.new(1, 0, 1) end
	if Dir.Magnitude < 1e-3 then return end
	Dir = Dir.Unit

	-- a wall behind the target shortens the push (never through it)
	local Push = TargetOffset or AIR_PUSH
	local Params = bLua.Paramaters('Map')
	local Wall = workspace:Raycast(TargetRoot.Position, Dir * (Push + 2), Params)
	if Wall then Push = math.max(0, (Wall.Position - TargetRoot.Position).Magnitude - 2) end

	local Y = TargetAerial.Position.Y
	local T = TargetRoot.Position + Dir * Push
	local U = T - Dir * (UserOffset or AIR_GAP)
	TargetAerial.Position = Vector3.new(T.X, Y, T.Z)
	UserAerial.Position = Vector3.new(U.X, Y, U.Z)

	-- face each other, so the next swing (and the target's reaction) points the right way
	TargetRoot.CFrame = CFrame.lookAt(TargetRoot.Position, TargetRoot.Position - Dir)
	UserRoot.CFrame = CFrame.lookAt(UserRoot.Position, UserRoot.Position + Dir)
end"""


def _repos_old(src):
    a = src.index("function AirCombat.Reposition(")
    b = src.index("\nreturn AirCombat", a)
    return src[a:b].rstrip("\n")


import os
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pre", AIR + ".luau"), encoding="utf-8", newline="").read()
EDITS.append((AIR, _repos_old(_src), REPOS_NEW))
