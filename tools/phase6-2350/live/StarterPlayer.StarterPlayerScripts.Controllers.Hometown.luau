--!strict
--[[
	Hometown (client). StarterPlayer.StarterPlayerScripts.Controllers.Hometown   (2.35.0, spec 2026-11-20 §4.2)
	While you're in Wickfield (NHTutorial), every other player in it is hidden on your screen (parts, decals, name tag,
	sounds), and the cast (Biscuit, the parents, the watchman, the driver) is your own local copy, so each player's scenes
	and NPC states are private. Everything this module changes on a model is local to this client and is restored when
	NHTutorial clears: sound volumes are kept in NHVol and decal transparencies in NHTr (set when hiding, never overwritten
	while hidden).
]]
local Players = game:GetService(`Players`)
local RunService = game:GetService(`RunService`)

local Player = Players.LocalPlayer
local Shared = {}
local Cast: { [string]: Model } = {}
local HiddenSources: { [Model]: boolean } = {}

local function hideCharacter(C: Model, Hide: boolean)
	for _, D in C:GetDescendants() do
		if D:IsA(`BasePart`) then
			D.LocalTransparencyModifier = if Hide then 1 else 0
		elseif D:IsA(`Decal`) then
			-- (a Decal has no LocalTransparencyModifier) hide through Transparency, keeping the original
			if Hide then
				if D:GetAttribute(`NHTr`) == nil then D:SetAttribute(`NHTr`, D.Transparency) end
				D.Transparency = 1
			else
				local Was = D:GetAttribute(`NHTr`)
				if Was ~= nil then D.Transparency = Was :: number; D:SetAttribute(`NHTr`, nil) end
			end
		elseif D:IsA(`Sound`) then
			if Hide then
				if D:GetAttribute(`NHVol`) == nil then D:SetAttribute(`NHVol`, D.Volume) end
				D.Volume = 0
			else
				local Was = D:GetAttribute(`NHVol`)
				if Was ~= nil then D.Volume = Was :: number; D:SetAttribute(`NHVol`, nil) end
			end
		elseif D:IsA(`BillboardGui`) then
			D.Enabled = not Hide
		end
	end
	local Hum = C:FindFirstChildOfClass(`Humanoid`)
	if Hum then Hum.DisplayDistanceType = if Hide then Enum.HumanoidDisplayDistanceType.None else Enum.HumanoidDisplayDistanceType.Viewer end
end
Shared.HideCharacter = hideCharacter

function Shared.Hidden(Other: Player): boolean
	return Other ~= Player and Player:GetAttribute(`NHTutorial`) == true and Other:GetAttribute(`NHTutorial`) == true
end

function Shared.Cast(Name: string): Model?
	if Cast[Name] and Cast[Name].Parent then return Cast[Name] end
	local H = workspace:FindFirstChild(`Hometown`)
	local Src = H and H:FindFirstChild(Name, true)
	if not (Src and Src:IsA(`Model`)) then return nil end
	local Folder = workspace:FindFirstChild(`NHHometownCast`) or Instance.new(`Folder`)
	Folder.Name = `NHHometownCast`
	Folder.Parent = workspace
	local M = Src:Clone()
	M.Parent = Folder
	hideCharacter(Src, true)
	HiddenSources[Src] = true
	Cast[Name] = M
	return M
end

function Shared.OnStart()
	RunService.Heartbeat:Connect(function()
		if Player:GetAttribute(`NHTutorial`) ~= true then return end
		for _, Other in Players:GetPlayers() do
			local C = Other.Character
			if C and Other ~= Player then
				local Want = Shared.Hidden(Other)
				if C:GetAttribute(`NHHiddenLocal`) ~= Want then
					C:SetAttribute(`NHHiddenLocal`, Want)
					hideCharacter(C, Want)
				end
			end
		end
	end)
	Player:GetAttributeChangedSignal(`NHTutorial`):Connect(function()
		if Player:GetAttribute(`NHTutorial`) == true then return end
		for _, Other in Players:GetPlayers() do
			if Other.Character and Other.Character:GetAttribute(`NHHiddenLocal`) then
				Other.Character:SetAttribute(`NHHiddenLocal`, false)
				hideCharacter(Other.Character, false)
			end
		end
		local F = workspace:FindFirstChild(`NHHometownCast`)
		if F then F:Destroy() end
		for Src in HiddenSources do if Src.Parent then hideCharacter(Src, false) end end
		table.clear(HiddenSources)
		table.clear(Cast)
	end)
end

return Shared
