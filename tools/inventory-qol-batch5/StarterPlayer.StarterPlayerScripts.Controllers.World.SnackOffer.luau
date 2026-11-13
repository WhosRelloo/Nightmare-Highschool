--[[
	SnackOffer (client). Controllers.World.SnackOffer  (inventory QOL batch 5, 2026-11-12)

	Hold a snack (a food or drink from your hotbar) near a student and an "Offer <snack>" prompt (E) shows on them. They
	take it, or don't, in their clique's voice; a food their clique loves is worth standing once a day
	(Services.Features.Inventory.Feed, StudentBrain.Fed). One prompt, moved to the nearest student within reach.
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local Items = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`Items`))

local Player = Players.LocalPlayer
local REACH = 9

local Shared = {}
local Local = {}
local Prompt: ProximityPrompt? = nil
local Target: Model? = nil
local HeldId: string? = nil

-- the snack in your hand (a hotbar snack that isn't an empty pin)
function Local.Held(): string?
	local Char = Player.Character
	for _, T in (Char and Char:GetChildren()) or {} do
		if T:IsA(`Tool`) and not T:GetAttribute(`NHEmpty`) then
			local Id = T:GetAttribute(`NHItem`)
			local It = Id and Items.ById[Id]
			if It and (It.Kind == `Heal` or It.Kind == `Buff`) then return Id end
		end
	end
	return nil
end

-- the nearest living student within reach
function Local.Nearest(): Model?
	local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`)
	if not (Root and Root:IsA(`BasePart`)) then return nil end
	local Params = OverlapParams.new()
	Params.FilterType = Enum.RaycastFilterType.Exclude
	Params.FilterDescendantsInstances = { Player.Character }
	local Best, Dist = nil, REACH
	local Seen = {}
	for _, Part in workspace:GetPartBoundsInRadius(Root.Position, REACH, Params) do
		local M = Part:FindFirstAncestorOfClass(`Model`)
		while M and not M:GetAttribute(`NHBrain`) and M.Parent ~= workspace do M = M.Parent and M.Parent:FindFirstAncestorOfClass(`Model`) or nil end
		if M and M:GetAttribute(`NHBrain`) and not Seen[M] then
			Seen[M] = true
			local Them = M:FindFirstChild(`HumanoidRootPart`)
			local Hum = M:FindFirstChildOfClass(`Humanoid`)
			if Them and Hum and Hum.Health > 0 then
				local D = (Them.Position - Root.Position).Magnitude
				if D < Dist then Best, Dist = M, D end
			end
		end
	end
	return Best
end

function Local.Prompt(): ProximityPrompt
	if Prompt then return Prompt end
	local P = Instance.new(`ProximityPrompt`)
	P.Name = `NHOffer`
	P.KeyboardKeyCode = Enum.KeyCode.E
	P.GamepadKeyCode = Enum.KeyCode.ButtonX
	P.HoldDuration = 0.35
	P.MaxActivationDistance = REACH
	P.RequiresLineOfSight = false
	P.Style = Enum.ProximityPromptStyle.Custom -- the game's own prompt look
	P.ObjectText = `Student`
	P.Triggered:Connect(function()
		local F = ReplicatedStorage:FindFirstChild(`NHInventory`)
		local R = F and F:FindFirstChild(`Feed`)
		if R and Target and HeldId then pcall(R.InvokeServer, R, Target, HeldId) end
	end)
	Prompt = P
	return P
end

function Local.Step()
	local Id = Local.Held()
	local M = Id and Local.Nearest() or nil
	local P = Local.Prompt()
	if not (Id and M) then
		P.Enabled = false
		P.Parent = nil
		Target, HeldId = nil, nil
		return
	end
	local Root = M:FindFirstChild(`HumanoidRootPart`)
	if P.Parent ~= Root then P.Parent = Root end
	Target, HeldId = M, Id
	P.ActionText = `Offer {Items.ById[Id].Name}`
	P.Enabled = true
end

function Shared.OnStart()
	task.spawn(function()
		while true do
			pcall(Local.Step)
			task.wait(0.2)
		end
	end)
end

return Shared
