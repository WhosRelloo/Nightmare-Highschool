E = "ServerScriptService.Services.Player.ActionManager.Combat.Ender"
C = "ServerScriptService.Services.Player.ActionManager.Combat.Clinch"
M = "ServerScriptService.Services.Player.ActionManager.Combat.M1"

EDITS = [
    # ---------------- Ender: the bespoke clips (Fist.Moves), stand-ins while their ids are empty
    (E, """	Stand-in clips until the owner's own: Fist M1.3 (the hook) and Fist M1.4 (both arms drive forward).
]]""", """	(2.12) Bespoke clips: Fist.Moves.BodyBlow / Fist.Moves.Shove, at speed 1. Each starts on its M1's pose (M1.3 at 0.40 s,
	M1.1 at 0.45 s) and ends on the fist idle, slides included. Hit / EndLag are keyframe names (AnimMarkers). While a
	Moves id is empty (not published yet) the old stand-in plays: Fist M1.3 / M1.4 at the Speed below.
]]"""),
    (E, """	BodyBlow = { Clip = `3`; Speed = 0.95;""", """	BodyBlow = { Anim = `BodyBlow`; Clip = `3`; Speed = 0.95;"""),
    (E, """	Shove = { Clip = `4`; Speed = 1.1;""", """	Shove = { Anim = `Shove`; Clip = `4`; Speed = 1.1;"""),
    (E, """local function Cleanup(self)""", """-- the bespoke clip at speed 1, or the stand-in at its speed while the bespoke one isn't published
local function Clip(Def)
	local Fist = ReplicatedStorage.Assets.Animations.Weapons.Fist
	local Moves = Fist:FindFirstChild(`Moves`)
	local A = Moves and Moves:FindFirstChild(Def.Anim)
	if A and A.AnimationId ~= `` then return A, 1 end
	return Fist.M1[Def.Clip], Def.Speed
end

local function Cleanup(self)"""),
    (E, """		local Track = TrackService.Play(ReplicatedStorage.Assets.Animations.Weapons.Fist.M1[Def.Clip], self.Character, `Attack`, 0.05)
		Track:SetPriority(Enum.AnimationPriority.Action4)
		Track:SetSpeed(Def.Speed)""", """		local Anim, Speed = Clip(Def)
		-- the bespoke clip starts on the swing's committed pose; the short fade covers an ender thrown a little early or late
		local Track = TrackService.Play(Anim, self.Character, `Attack`, Speed == 1 and 0.08 or 0.05)
		Track:SetPriority(Enum.AnimationPriority.Action4)
		Track:SetSpeed(Speed)"""),
    (E, """		local Rate = (Track.Track and Track.Track.Speed) or Def.Speed""", """		local Rate = (Track.Track and Track.Track.Speed) or Speed"""),

    # ---------------- Clinch: FistClinch + FistClinchVictim, the victim put where the hands close
    (C, """	Stand-in clip until the owner's own: the Fist M2 (its leg drives up and forward), played a little faster.
]]""", """	(2.12) Bespoke clips: Fist.Moves.Clinch (speed 1: grab 0.14, knee Hit 0.367, EndLag 0.70) and, on the one caught,
	Fist.Moves.ClinchVictim (yanked in, folds over the knee, staggers back; tagged Stun so the next hit's react replaces
	it). The pair was authored 2.9 studs apart, face to face, so a caught victim is set there (unless a wall is in the
	way) and the knee's own hit react is skipped. While the Moves ids are empty the old stand-in plays (Fist M2 at 1.25).
]]"""),
    (C, """local CLINCH_COOLDOWN = 3
local REACH = 0.14 -- seconds in, when the hands close
local SPEED = 1.25
""", """local CLINCH_COOLDOWN = 3
local REACH = 0.14 -- seconds in, when the hands close
local SPEED = 1.25 -- the stand-in's
local PAIR_GAP = 2.9 -- studs: root to root at the grab, as the bespoke pair was authored

-- the bespoke attacker and victim clips, or nil while they aren't published
local function Bespoke()
	local Moves = ReplicatedStorage.Assets.Animations.Weapons.Fist:FindFirstChild(`Moves`)
	local A, V = Moves and Moves:FindFirstChild(`Clinch`), Moves and Moves:FindFirstChild(`ClinchVictim`)
	if A and V and A.AnimationId ~= `` and V.AnimationId ~= `` then return A, V end
	return nil
end

-- the victim's root PAIR_GAP in front of the attacker, facing them, at its own height; skipped if a wall is between
local function PlaceVictim(Root: BasePart, Victim: Model, Ignore: { Instance })
	local VRoot = Victim:FindFirstChild(`HumanoidRootPart`)
	if not (VRoot and VRoot:IsA(`BasePart`)) or VRoot.Anchored then return end
	local Look = Root.CFrame.LookVector * vector.create(1, 0, 1)
	if Look.Magnitude < 1e-3 then return end
	Look = Look.Unit
	local Params = RaycastParams.new()
	Params.FilterType = Enum.RaycastFilterType.Exclude
	Params.FilterDescendantsInstances = Ignore
	if workspace:Raycast(Root.Position, Look * (PAIR_GAP + 0.6), Params) then return end
	local At = Root.Position + Look * PAIR_GAP
	At = vector.create(At.X, VRoot.Position.Y, At.Z)
	Victim:PivotTo(CFrame.lookAt(At, At - Look) * VRoot.CFrame:Inverse() * Victim:GetPivot())
	VRoot.AssemblyLinearVelocity = Vector3.zero
end
"""),
    (C, """		local Track = TrackService.Play(ReplicatedStorage.Assets.Animations.Weapons.Fist.M2, self.Character, `Attack`, 0.05)
		Track:SetPriority(Enum.AnimationPriority.Action4)
		Track:SetSpeed(SPEED)
		self.Track = Track
		local Rate = (Track.Track and Track.Track.Speed) or SPEED""", """		local Anim, VictimAnim = Bespoke()
		local Speed = Anim and 1 or SPEED
		local Track = TrackService.Play(Anim or ReplicatedStorage.Assets.Animations.Weapons.Fist.M2, self.Character, `Attack`, Anim and 0.08 or 0.05)
		Track:SetPriority(Enum.AnimationPriority.Action4)
		Track:SetSpeed(Speed)
		self.Track = Track
		local Rate = (Track.Track and Track.Track.Speed) or Speed"""),
    (C, """		-- caught: the guard drops and they're held until the knee lands
		pcall(function() require(script.Parent.Parent).CancelAction(Victim, `Block`) end)
		StateManager.CreateState(Victim, `Stun`, KneeAt - REACH + 0.1)
		task.wait(KneeAt - REACH)
""", """		-- caught: the guard drops and they're held until the knee lands
		pcall(function() require(script.Parent.Parent).CancelAction(Victim, `Block`) end)
		StateManager.CreateState(Victim, `Stun`, KneeAt - REACH + 0.1)
		if VictimAnim then
			PlaceVictim(Root, Victim, { self.Character, Victim })
			pcall(function()
				TrackService.StopTaggedTracks(Victim, `Stun`, 0.06)
				local VT = TrackService.Play(VictimAnim, Victim, `Stun`, 0.06)
				VT:SetPriority(Enum.AnimationPriority.Action4)
				self.VictimTrack = VT
			end)
		end
		task.wait(KneeAt - REACH)
		self.VictimTrack = nil -- the knee landed: from here the victim clip plays out on its own
"""),
    (C, """			IgnoreStates = { Block = true; Parry = true };
			React = `1`; Tag = `CLINCH`; Heavy = true;
		}""", """			IgnoreStates = { Block = true; Parry = true };
			React = `1`; Tag = `CLINCH`; Heavy = true;
			NoAnimation = VictimAnim ~= nil; -- the victim clip already folds them over the knee
		}"""),
    (C, """	OnCancel = function(self)
		if self.Track then self.Track:Destroy() self.Track = nil end""", """	OnCancel = function(self)
		if self.Track then self.Track:Destroy() self.Track = nil end
		-- interrupted before the knee: let the caught one go instead of folding over nothing
		if self.VictimTrack then pcall(function() self.VictimTrack:Stop(0.15) end) self.VictimTrack = nil end"""),

    # ---------------- M1: an ender/clinch clip still settling past its EndLag fades out under the next swing
    (M, """		local Track = TrackService.Play(Config.Animations.M1[NewCombo], self.Character, `Attack`, 0)
		Track:SetPriority(Enum.AnimationPriority.Action3)
""", """		-- (2.12) the bespoke ender / clinch clips (Action4) keep settling after their EndLag: fade one out under this swing
		local Moves = ReplicatedStorage.Assets.Animations.Weapons.Fist:FindFirstChild(`Moves`)
		local Animator = Moves and self.Character:FindFirstChildWhichIsA(`Animator`, true)
		if Animator then
			for _, T in Animator:GetPlayingAnimationTracks() do
				if T.Animation and T.Animation.Parent == Moves then T:Stop(0.12) end
			end
		end
		local Track = TrackService.Play(Config.Animations.M1[NewCombo], self.Character, `Attack`, 0)
		Track:SetPriority(Enum.AnimationPriority.Action3)
"""),
]
