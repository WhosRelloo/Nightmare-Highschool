local C=game.StarterPlayer.StarterPlayerScripts.Controllers.Character
assert(not C:FindFirstChild("Transformation"),"already there")
local src=[=====[--[[
	Transformation (client): T toggles your race's transformation (Services.Features.Transformation).
	While the character attribute Transformation is on (and you're not the full wolf), your movement pack is
	the claw stance (Assets.Animations.Transformation). As the wolf (WolfForm): click = bite, R = jump bite.
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local UserInputService = game:GetService(`UserInputService`)
local UnPackets = require(ReplicatedStorage.Remotes.UnPackets)

local Player = Players.LocalPlayer
local Shared = {}

local function controller()
	local Ok, AC = pcall(require, script.Parent.AnimationController)
	return Ok and AC and AC.Controller
end

local function restorePack(Char: Model)
	local AM = controller()
	if not AM then return end
	local Hum = Char:FindFirstChildWhichIsA(`Humanoid`)
	local W = Char:GetAttribute(`Weapon`)
	local Pack = (Hum and Hum:GetAttribute(`Equip`) and W and ReplicatedStorage.Assets.Animations.Weapons:FindFirstChild(W)) or ReplicatedStorage.Assets.Animations.Default
	pcall(function() AM:StopAllTracks():SetTracks(Pack.Movement):PlayTrack(`Idle`, 0.15) end)
end

local function onChar(Char: Model)
	Char:GetAttributeChangedSignal(`Transformation`):Connect(function()
		local On = Char:GetAttribute(`Transformation`)
		local AM = controller()
		if not AM then return end
		if On and not Char:GetAttribute(`WolfForm`) then
			pcall(function() AM:StopAllTracks():SetTracks(ReplicatedStorage.Assets.Animations.Transformation.Movement):PlayTrack(`Idle`, 0.15) end)
		elseif not On then
			restorePack(Char)
		end
	end)
end

function Shared.OnStart()
	Player.CharacterAdded:Connect(onChar)
	if Player.Character then onChar(Player.Character) end
	UserInputService.InputBegan:Connect(function(Input, Processed)
		if Processed or UserInputService:GetFocusedTextBox() then return end
		local Char = Player.Character
		if not Char then return end
		if Input.KeyCode == Enum.KeyCode.T then
			-- (audit) T is Bloodrush in a soccer match and "turn them" on the bite prompt; don't transform then
			if Player:GetAttribute(`InSport`) or Char:GetAttribute(`InSport`) then return end
			local Bite = Player:FindFirstChild(`PlayerGui`) and Player.PlayerGui:FindFirstChild(`NHBite`)
			if Bite and Bite:IsA(`ScreenGui`) and Bite.Enabled then return end
			UnPackets.Action:Fire(`Transform`)
		elseif Char:GetAttribute(`WolfForm`) then
			if Input.UserInputType == Enum.UserInputType.MouseButton1 then
				UnPackets.Action:Fire(`WolfBite`)
			elseif Input.KeyCode == Enum.KeyCode.R then
				UnPackets.Action:Fire(`WolfLeap`)
			end
		end
	end)
end

return Shared]=====]
local f,e=loadstring(src) assert(f,e)
local M=Instance.new("ModuleScript") M.Name="Transformation" M.Source=src M.Parent=C
local function h(x) local a,b=1,0 for i=1,#x do a=(a+x:byte(i))%65521 b=(b+a)%65521 end return b*65536+a end
return "added "..#src.." "..h(src)