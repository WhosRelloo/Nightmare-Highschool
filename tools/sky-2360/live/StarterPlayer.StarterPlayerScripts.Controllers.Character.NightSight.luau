--[[
	Night sight (client). Controllers.Character.NightSight   server: Services.Features.NightSight

	Night races (Vampire, Werewolf, Ghoul, Wraith) press H to see in the dark. While it's on:
		- you: a personal light that lifts the dark around you, and a sharp, desaturated hunter's grade with a hint of
		  your race colour (ColorCorrectionEffect "NHNightSight"; DayCycle's own properties are never touched)
		- everyone: your eyes glow in your race colour. Each face strip gets an unlit SurfaceGui behind the face with
		  a copy of the iris; the normal iris is hidden, so the glow shows through the eye opening and blinks still
		  cover it. A small light at the eyes casts the colour on the face.
	The server owns the state (character attribute NightSight), so everyone sees it and only night races can use it.
]]

local Lighting = game:GetService(`Lighting`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local TweenService = game:GetService(`TweenService`)
local UserInputService = game:GetService(`UserInputService`)

local Player = Players.LocalPlayer
local KEY = Enum.KeyCode.H

local GLOW = {
	Vampire = Color3.fromRGB(255, 40, 60);    -- crimson
	Werewolf = Color3.fromRGB(255, 184, 40);  -- amber
	Ghoul = Color3.fromRGB(140, 255, 80);     -- acid green
	Wraith = Color3.fromRGB(150, 210, 255);   -- spectral ice blue
}

local Shared = {}
Shared.Colors = GLOW
local Own = { Grade = nil :: ColorCorrectionEffect?; Light = nil :: PointLight?; On = false }

local function tween(I: Instance, T: number, Props)
	local Tw = TweenService:Create(I, TweenInfo.new(T, Enum.EasingStyle.Sine), Props)
	Tw:Play()
	return Tw
end

local function raceOf(Char: Model): string?
	local P = Players:GetPlayerFromCharacter(Char)
	return (P and P:GetAttribute(`Race`)) or Char:GetAttribute(`Race`)
end

---| glowing eyes (every character with NightSight on) |---

local function setGlow(Char: Model, On: boolean)
	local Head = Char:FindFirstChild(`Head`)
	local Plate = Head and Head:FindFirstChild(`NHFacePlate`)
	local Color = GLOW[raceOf(Char) or ``] or GLOW.Vampire
	if Plate then
		for _, Strip in Plate:GetChildren() do
			local Face = Strip:FindFirstChild(`NHFace`)
			local Iris = Face and Face:FindFirstChild(`NHEyesIris`) :: ImageLabel?
			local Glow = Strip:FindFirstChild(`NHEyeGlow`) :: SurfaceGui?
			if On and Face and Iris then
				if not Glow then
					Glow = Instance.new(`SurfaceGui`)
					Glow.Name = `NHEyeGlow`
					Glow.Face = (Face :: SurfaceGui).Face
					Glow.CanvasSize = (Face :: SurfaceGui).CanvasSize
					Glow.SizingMode = (Face :: SurfaceGui).SizingMode
					Glow.PixelsPerStud = (Face :: SurfaceGui).PixelsPerStud
					Glow.ZOffset = (Face :: SurfaceGui).ZOffset - 1 -- under the face: the eye whites and lids sit on top
					Glow.LightInfluence = 0
					Glow.Brightness = 4
					Glow.ClipsDescendants = (Face :: SurfaceGui).ClipsDescendants
					local Copy = Iris:Clone()
					Copy.Name = `Iris`
					for _, C in Copy:GetChildren() do C:Destroy() end
					Copy.Parent = Glow
					Glow.Parent = Strip
				end
				local Copy = Glow:FindFirstChild(`Iris`) :: ImageLabel?
				if Copy then
					Copy.Image, Copy.Size, Copy.Position = Iris.Image, Iris.Size, Iris.Position
					Copy.ImageRectOffset, Copy.ImageRectSize = Iris.ImageRectOffset, Iris.ImageRectSize
					Copy.ImageColor3 = Color
					Copy.ImageTransparency = 0
				end
				if Iris:GetAttribute(`NHBaseT`) == nil then Iris:SetAttribute(`NHBaseT`, Iris.ImageTransparency) end
				Iris.ImageTransparency = 1
			else
				if Glow then Glow:Destroy() end
				if Iris and Iris:GetAttribute(`NHBaseT`) ~= nil then
					Iris.ImageTransparency = Iris:GetAttribute(`NHBaseT`)
					Iris:SetAttribute(`NHBaseT`, nil)
				end
			end
		end
	end
	-- a little light at the eyes
	local L = Head and Head:FindFirstChild(`NHEyeLight`) :: PointLight?
	if On and Head then
		if not L then
			local A = Head:FindFirstChild(`FaceFrontAttachment`) or Head
			L = Instance.new(`PointLight`)
			L.Name = `NHEyeLight`
			L.Range = 5
			L.Brightness = 1.6
			L.Shadows = false
			L.Parent = A
		end
		local Light = L :: PointLight
		Light.Color = Color
	elseif L then
		L:Destroy()
	elseif Head then
		local Stray = Head:FindFirstChild(`NHEyeLight`, true)
		if Stray then Stray:Destroy() end
	end
end

-- the face is rebuilt now and then (appearance changes, transformations), so keep the glow applied
local Watched = {} :: { [Model]: boolean }
local function watch(Char: Model)
	if Watched[Char] then return end
	Watched[Char] = true
	-- (1.41) a Werewolf's eyes also glow all through a full-moon night (NHMoonEyes, set by Services.Features.MoonPhases)
	local function sync() setGlow(Char, Char:GetAttribute(`NightSight`) == true or Char:GetAttribute(`NHMoonEyes`) == true) end
	Char:GetAttributeChangedSignal(`NightSight`):Connect(sync)
	Char:GetAttributeChangedSignal(`NHMoonEyes`):Connect(sync)
	-- a rebuilt face (new iris) picks the glow back up
	Char.DescendantAdded:Connect(function(D)
		if D.Name == `NHEyesIris` and (Char:GetAttribute(`NightSight`) == true or Char:GetAttribute(`NHMoonEyes`) == true) then task.defer(sync) end
	end)
	Char.AncestryChanged:Connect(function(_, Parent) if not Parent then Watched[Char] = nil end end)
	sync()
end

---| your own sight |---

local function ownOn(On: boolean)
	if Own.On == On then return end
	Own.On = On
	local Race = Player:GetAttribute(`Race`)
	local Color = GLOW[Race or ``] or GLOW.Vampire
	if On then
		local G = Own.Grade or Instance.new(`ColorCorrectionEffect`)
		G.Name = `NHNightSight`
		G.Brightness, G.Contrast, G.Saturation, G.TintColor = 0, 0, 0, Color3.new(1, 1, 1)
		G.Parent = Lighting
		Own.Grade = G
		tween(G, 0.35, { Brightness = 0.2; Contrast = 0.25; Saturation = -0.45; TintColor = Color3.new(1, 1, 1):Lerp(Color, 0.12) })
		local Char = Player.Character
		local Root = Char and Char:FindFirstChild(`HumanoidRootPart`)
		if Root then
			local L = Instance.new(`PointLight`)
			L.Name = `NHNightSightLight`
			L.Range = 70
			L.Brightness = 0
			L.Shadows = false
			L.Color = Color3.new(1, 1, 1):Lerp(Color, 0.2)
			L.Parent = Root
			Own.Light = L
			tween(L, 0.35, { Brightness = 0.9 })
		end
	else
		if Own.Grade then tween(Own.Grade, 0.3, { Brightness = 0; Contrast = 0; Saturation = 0; TintColor = Color3.new(1, 1, 1) }) end
		local L = Own.Light
		Own.Light = nil
		if L then tween(L, 0.3, { Brightness = 0 }) task.delay(0.35, function() L:Destroy() end) end
	end
end

function Shared.Toggle()
	local Remote = ReplicatedStorage:FindFirstChild(`NHNightSight`) :: RemoteEvent?
	local Char = Player.Character
	if not Remote or not Char then return end
	Remote:FireServer(not (Char:GetAttribute(`NightSight`) == true))
end

function Shared.OnStart()
	-- every character: glowing eyes
	local function hook(P: Player)
		if P.Character then watch(P.Character) end
		P.CharacterAdded:Connect(watch)
	end
	for _, P in Players:GetPlayers() do hook(P) end
	Players.PlayerAdded:Connect(hook)

	-- your own sight follows your character's attribute (the server decides)
	local function own(Char: Model)
		ownOn(false)
		Char:GetAttributeChangedSignal(`NightSight`):Connect(function() ownOn(Char:GetAttribute(`NightSight`) == true) end)
		ownOn(Char:GetAttribute(`NightSight`) == true)
	end
	if Player.Character then own(Player.Character) end
	Player.CharacterAdded:Connect(own)

	UserInputService.InputBegan:Connect(function(Input, Processed)
		if Processed or Input.KeyCode ~= KEY then return end
		if Player:GetAttribute(`InMainMenu`) == true then return end
		if not GLOW[Player:GetAttribute(`Race`) or ``] then return end
		Shared.Toggle()
	end)
end

return Shared
