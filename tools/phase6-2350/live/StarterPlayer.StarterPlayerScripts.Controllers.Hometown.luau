--!strict
--[[
	Hometown (client). StarterPlayer.StarterPlayerScripts.Controllers.Hometown   (2.35.0, spec 2026-11-20 §4.2)
	While you're in Wickfield (NHTutorial), every other player in it is hidden on your screen (parts, decals, name tag,
	sounds), and the cast (Biscuit, the parents, the watchman, the driver) is your own local copy, so each player's scenes
	and NPC states are private. Everything this module changes on a model is local to this client and is restored when
	NHTutorial clears: every original (sound volume NHVol, gui Enabled NHEn, name display NHDdt, a cast source's collide/query/touch NHCC/NHCQ/NHCT)
	is kept in an attribute the first time it's changed, and restored from it.
]]
local Players = game:GetService(`Players`)
local RunService = game:GetService(`RunService`)

local Player = Players.LocalPlayer
local Shared = {}
local Cast: { [string]: Model } = {}
local HiddenSources: { [Model]: boolean } = {}
-- a hidden model's watchers (fix round 1): parts, decals, sounds, tools and accessories that arrive after the hide are
-- hidden too. Keyed by model; disconnected on restore, on the model's removal and when NHTutorial clears.
local Watching: { [Model]: { RBXScriptConnection } } = {}
local Ghosts: { [Model]: boolean } = {} -- a cast source: also made untouchable (no collide / query / touch) while cast
local Conns: { RBXScriptConnection } = {}

-- one descendant hidden / restored (every original is kept in an attribute the first time it's changed; attributes set
-- on the client never replicate)
local function applyOne(D: Instance, Hide: boolean, Ghost: boolean)
	if D:IsA(`BasePart`) then
		D.LocalTransparencyModifier = if Hide then 1 else 0
		if Ghost then
			if Hide then
				if D:GetAttribute(`NHCC`) == nil then
					D:SetAttribute(`NHCC`, D.CanCollide); D:SetAttribute(`NHCQ`, D.CanQuery); D:SetAttribute(`NHCT`, D.CanTouch)
				end
				D.CanCollide = false; D.CanQuery = false; D.CanTouch = false
			elseif D:GetAttribute(`NHCC`) ~= nil then
				D.CanCollide = D:GetAttribute(`NHCC`) :: boolean
				D.CanQuery = D:GetAttribute(`NHCQ`) :: boolean
				D.CanTouch = D:GetAttribute(`NHCT`) :: boolean
				D:SetAttribute(`NHCC`, nil); D:SetAttribute(`NHCQ`, nil); D:SetAttribute(`NHCT`, nil)
			end
		end
	elseif D:IsA(`Decal`) then
		(D :: any).LocalTransparencyModifier = if Hide then 1 else 0
	elseif D:IsA(`Sound`) then
		if Hide then
			if D:GetAttribute(`NHVol`) == nil then D:SetAttribute(`NHVol`, D.Volume) end
			D.Volume = 0
		else
			local Was = D:GetAttribute(`NHVol`)
			if Was ~= nil then D.Volume = Was :: number; D:SetAttribute(`NHVol`, nil) end
		end
	elseif D:IsA(`BillboardGui`) then
		if Hide then
			if D:GetAttribute(`NHEn`) == nil then D:SetAttribute(`NHEn`, D.Enabled) end
			D.Enabled = false
		else
			local Was = D:GetAttribute(`NHEn`)
			if Was ~= nil then D.Enabled = Was :: boolean; D:SetAttribute(`NHEn`, nil) end
		end
	elseif D:IsA(`Humanoid`) then
		if Hide then
			if D:GetAttribute(`NHDdt`) == nil then D:SetAttribute(`NHDdt`, D.DisplayDistanceType.Value) end
			D.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
		else
			local Was = D:GetAttribute(`NHDdt`)
			if Was ~= nil then
				for _, E in Enum.HumanoidDisplayDistanceType:GetEnumItems() do if E.Value == Was then D.DisplayDistanceType = E end end
				D:SetAttribute(`NHDdt`, nil)
			end
		end
	end
end

local function unwatch(C: Model)
	local L = Watching[C]
	if not L then return end
	Watching[C] = nil
	Ghosts[C] = nil
	for _, Cn in L do Cn:Disconnect() end
end

local function hideCharacter(C: Model, Hide: boolean, Ghost: boolean?)
	local G = Ghost == true or Ghosts[C] == true
	for _, D in C:GetDescendants() do applyOne(D, Hide, G) end
	if Hide then
		if not Watching[C] then
			if G then Ghosts[C] = true end
			Watching[C] = {
				C.DescendantAdded:Connect(function(D)
					task.defer(function() if Watching[C] and D:IsDescendantOf(C) then applyOne(D, true, Ghosts[C] == true) end end)
				end);
				C.Destroying:Connect(function() unwatch(C) end);
			}
		end
	else
		unwatch(C)
	end
end
Shared.HideCharacter = hideCharacter
function Shared.WatchedForTests(): number
	local N = 0
	for _ in Watching do N += 1 end
	return N
end

function Shared.Hidden(Other: Player): boolean
	return Other ~= Player and Player:GetAttribute(`NHTutorial`) == true and Other:GetAttribute(`NHTutorial`) == true
end

function Shared.Cast(Name: string): Model?
	if Player:GetAttribute(`NHTutorial`) ~= true then return nil end
	if Cast[Name] and Cast[Name].Parent then return Cast[Name] end
	local H = workspace:FindFirstChild(`Hometown`)
	local Src = H and H:FindFirstChild(Name, true)
	if not (Src and Src:IsA(`Model`)) then return nil end
	local Folder = workspace:FindFirstChild(`NHHometownCast`) or Instance.new(`Folder`)
	Folder.Name = `NHHometownCast`
	Folder.Parent = workspace
	local M = Src:Clone()
	M.Parent = Folder
	hideCharacter(Src, true, true)
	HiddenSources[Src] = true
	Cast[Name] = M
	return M
end

function Shared.OnStart()
	table.insert(Conns, RunService.Heartbeat:Connect(function()
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
	end))
	table.insert(Conns, Player:GetAttributeChangedSignal(`NHTutorial`):Connect(function()
		if Player:GetAttribute(`NHTutorial`) == true then return end
		for _, Other in Players:GetPlayers() do
			if Other.Character and Other.Character:GetAttribute(`NHHiddenLocal`) then
				Other.Character:SetAttribute(`NHHiddenLocal`, false)
				hideCharacter(Other.Character, false)
			end
		end
		local F = workspace:FindFirstChild(`NHHometownCast`)
		if F then F:Destroy() end
		for Src in HiddenSources do hideCharacter(Src, false) end
		table.clear(HiddenSources)
		for C in table.clone(Watching) do hideCharacter(C, false) end -- anything still watched (a character that left the list)
		table.clear(Cast)
	end))
end

-- (tests) drops OnStart's connections (a test that calls OnStart in a second copy of the module)
function Shared.Stop()
	for _, Cn in Conns do Cn:Disconnect() end
	table.clear(Conns)
	for C in table.clone(Watching) do unwatch(C) end
end

return Shared
