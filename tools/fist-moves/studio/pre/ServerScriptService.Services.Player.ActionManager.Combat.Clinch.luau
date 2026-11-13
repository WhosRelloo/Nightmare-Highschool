--[[
	Clinch (server): fist moveset 2.10, concept 8. M1 while holding block (ActionManager's M1 handler routes it here, and it
	cancels the block): a short grab that goes through a guard and a parry window but loses to any attack. Someone
	winding up their own swing isn't caught, and their swing lands on you instead. Caught: a knee to the gut, 4 damage,
	+25 posture (a posture break if that fills it), doubled over with a 1 s stun. A dodge's i-frames still slip it.
	Stand-in clip until the owner's own: the Fist M2 (its leg drives up and forward), played a little faster.
]]
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerStorage = game:GetService(`ServerStorage`)

local AnimMarkers = require(ServerStorage.Packages.AnimMarkers)
local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local TrackService = require(ReplicatedStorage.Packages.TrackService)
local DamageLogic = require(ServerStorage.Packages.DamageLogic)
local HitBoxService = require(ServerStorage.Packages.HitBox)

local CLINCH_COOLDOWN = 3
local REACH = 0.14 -- seconds in, when the hands close
local SPEED = 1.25

return {
	Priority = `High`; -- above the block it starts from

	Activate = function(self)
		local Humanoid = self.Character:FindFirstChildWhichIsA(`Humanoid`)
		local Root = Humanoid and Humanoid.RootPart
		if not Root then return end
		self:Cooldown(`Clinch`, CLINCH_COOLDOWN)

		local Track = TrackService.Play(ReplicatedStorage.Assets.Animations.Weapons.Fist.M2, self.Character, `Attack`, 0.05)
		Track:SetPriority(Enum.AnimationPriority.Action4)
		Track:SetSpeed(SPEED)
		self.Track = Track
		local Rate = (Track.Track and Track.Track.Speed) or SPEED
		if Rate <= 0 then Rate = 1 end
		local KneeAt = math.max(REACH + 0.1, (AnimMarkers.Time(Track, `Hit`) or 0.47) / Rate)
		local Total = math.max(KneeAt + 0.3, (AnimMarkers.Time(Track, `EndLag`) or 0.8) / Rate)
		StateManager.CreateState(self.Character, `Attacking`, Total)
		StateManager.CreateState(self.Character, `Freeze`, Total)

		task.wait(REACH)
		local HitBox = HitBoxService.New()
		HitBox.CFrame = Root
		HitBox.Size = vector.create(4.5, 7, 4.5)
		HitBox.Offset = CFrame.new(0, 0, -2.3)
		HitBox.Params = OverlapParams.new()
		HitBox.Params.FilterType = Enum.RaycastFilterType.Exclude
		HitBox.Params.FilterDescendantsInstances = { self.Character }
		local Victim = nil
		for _, Part in HitBox:GetCast() or {} do
			local M = Part and Part:FindFirstAncestorOfClass(`Model`)
			local H = M and M:FindFirstChildWhichIsA(`Humanoid`)
			if H and H.Health > 0 and M ~= self.Character then Victim = M break end
		end
		HitBox:Destroy()

		-- loses to any attack: a target still winding up its own swing isn't caught
		local Wu = Victim and Victim:GetAttribute(`NHWindupUntil`)
		if Victim and typeof(Wu) == `number` and workspace:GetServerTimeNow() < Wu and StateManager.HasState(Victim, `Attacking`) then Victim = nil end
		if not Victim then
			task.wait(math.max(0, Total - REACH))
			return
		end

		-- caught: the guard drops and they're held until the knee lands
		pcall(function() require(script.Parent.Parent).CancelAction(Victim, `Block`) end)
		StateManager.CreateState(Victim, `Stun`, KneeAt - REACH + 0.1)
		task.wait(KneeAt - REACH)

		local DamageData = {
			Character = self.Character; Target = Victim;
			Damage = 4; StunLocked = false;
			States = { Stun = 1 };
			LinearVelocity = { Velocity = 10; Duration = 0.15 };
			IgnoreStates = { Block = true; Parry = true };
			React = `1`; Tag = `CLINCH`; Heavy = true;
		}
		if DamageLogic.Processed(DamageData) then
			DamageLogic.TakeAction(DamageData)
			local H = Victim:FindFirstChildWhichIsA(`Humanoid`)
			if H and H.Health > 0 then
				local P = (H:GetAttribute(`Posture`) or 0) + 25 * (Victim:GetAttribute(`NH_PostureGain`) or 1)
				if P >= 100 then DamageLogic.PostureBreak(DamageData) else H:SetAttribute(`Posture`, P) end
			end
		end
		task.wait(math.max(0, Total - KneeAt))
	end;

	OnCancel = function(self)
		if self.Track then self.Track:Destroy() self.Track = nil end
		StateManager.RemoveAllStates(self.Character, `Attacking`)
		StateManager.RemoveAllStates(self.Character, `Freeze`)
	end;

	Conditions = function(self)
		local Humanoid = self.Character:FindFirstChildWhichIsA(`Humanoid`)
		if not (Humanoid and Humanoid:GetAttribute(`Equip`)) then return false end
		return not StateManager.HasState(self.Character, { `Stun`, `ParryStun`, `Ragdoll`, `Paralyzed`, `SkillInUse` })
	end;

	Class = `Attack`;
}
