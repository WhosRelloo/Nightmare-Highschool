--[[
	RaceAction (server): rewards + visuals for the N-key race actions (ActionManager.Misc.RaceAction).
	Fires on Downed.OnExecuted(Gripper, Target, Kind) when Kind is a race action.
]]
local Players = game:GetService(`Players`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local Shared = {}

local HEAL = { EatBody = 0.35; BloodDrain = 0.3; SoulSiphon = 0.3; Exorcise = 0.2; Maul = 0.35; Stake = 0.2 } -- (2.2.0) Maul, Stake
local FEED = { EatBody = 30; BloodDrain = 30; SoulSiphon = 25; Exorcise = 0; Maul = 30; Stake = 0 }

function Shared.OnStart()
	local Downed = require(ServerScriptService.Services.Features.Downed)
	local Fx = require(ServerScriptService.Services.Features.Fx)
	-- visuals while it plays: the grip starts (GripEndsAt set) with a race Kind
	Downed.OnExecuted:Connect(function(Gripper: Model, Target: Model, Kind: string?)
		if not Kind or not HEAL[Kind] then return end
		local P = Players:GetPlayerFromCharacter(Gripper)
		local Hum = Gripper:FindFirstChildWhichIsA(`Humanoid`)
		if Hum and Hum.Health > 0 then Hum.Health = math.min(Hum.MaxHealth, Hum.Health + Hum.MaxHealth * HEAL[Kind]) end
		if P and FEED[Kind] > 0 then
			pcall(function() require(ServerScriptService.Services.Player.Evolution).Feed(P, FEED[Kind], Kind) end)
		end
		local Pos = Target:GetPivot().Position
		pcall(Fx.FireNear, Pos, 150, `RaceAction`, { Kind = Kind; From = Target; To = Gripper; Finish = true })
	end)
	-- the start of the action (for the channel visuals): watch GripEndsAt on characters
	local function hook(Char: Model)
		Char:GetAttributeChangedSignal(`GripEndsAt`):Connect(function()
			local Ends = Char:GetAttribute(`GripEndsAt`)
			local Kind = Char:GetAttribute(`NHRaceActionKind`)
			if Ends and Kind then
				-- (2.2.0) the victim (GrippedBy) and the sub-race drive the client's racial-grip VFX
				local Victim
				for _, M in workspace.Live:GetChildren() do
					if M:GetAttribute(`GrippedBy`) == Char.Name then Victim = M break end
				end
				local P = Players:GetPlayerFromCharacter(Char)
				local VP = Victim and Players:GetPlayerFromCharacter(Victim)
				pcall(Fx.FireNear, Char:GetPivot().Position, 150, `RaceAction`, { Kind = Kind; To = Char; Until = Ends; Victim = Victim;
					Sub = P and P:GetAttribute(`SubRace`); VictimRace = (VP and VP:GetAttribute(`Race`)) or (Victim and Victim:GetAttribute(`Race`)) or `Human` })
			end
		end)
	end
	local function onPlayer(P: Player)
		P.CharacterAdded:Connect(hook)
		if P.Character then hook(P.Character) end
	end
	Players.PlayerAdded:Connect(onPlayer)
	for _, P in Players:GetPlayers() do onPlayer(P) end
end

return Shared
