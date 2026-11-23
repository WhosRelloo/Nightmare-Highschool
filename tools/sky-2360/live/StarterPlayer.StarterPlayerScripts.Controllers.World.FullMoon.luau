--[[
	Full-moon night (client). Controllers.World.FullMoon   VFX P2-1 (vault: Docs/VFX-Design-Bible.md, audit World D / Quests C14)

	From 20:00 on a full-moon night (ReplicatedStorage.Lineage.IsFullMoon: every 4th night, the same rule that
	boosts night powers and EXP):
		- the moon swells (Sky.MoonAngularSize 11 -> 18 over 20 s, 3 s with reduced motion)
		- (2.36, sky-2360) the moonlit look is Config.DayCycle.Moon.Full, applied by World.DayCycle (one grade for every moon);
		  this no longer writes NHMoonGrade, so the Werewolf/Vampire-only stronger grade is gone
		- once a night: a Moment banner "The moon is full"
		- Werewolves: a 3 s silver edge at the screen borders
	Everything eases back at dawn (06:00), and steps aside while the main menu is up.

	Testing: set the LocalPlayer attribute NHMoonPreview = true to force it on (false/nil to let the clock decide).
]]

local Lighting = game:GetService(`Lighting`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local TweenService = game:GetService(`TweenService`)

local Player = Players.LocalPlayer
local Lineage = require(ReplicatedStorage:WaitForChild(`Lineage`))
local SchoolTime = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`SchoolTime`))
local Fx = require(script.Parent.Parent:WaitForChild(`Fx`))

local MOON_FULL = 18
local SWELL = 20
local SILVER = Color3.fromRGB(214, 222, 236)
-- (2.36) the full-moon grade moved to Config.DayCycle.Moon.Full

local Shared = {}
local State = { On = false; BaseSize = nil :: number?; Grade = nil :: ColorCorrectionEffect?; Announced = {} :: { [number]: boolean } }

local function sky(): Sky?
	return Lighting:FindFirstChildOfClass(`Sky`)
end

-- returns (isFullMoon, nightNumber)
function Shared.Now(): (boolean, number?)
	local Preview = Player:GetAttribute(`NHMoonPreview`)
	if Preview == true then return true, -1 end
	local Clock = ReplicatedStorage:FindFirstChild(`SchoolClock`)
	local Epoch = Clock and Clock:GetAttribute(`Epoch`)
	if typeof(Epoch) ~= `number` then return false, nil end
	local Ok, S = pcall(SchoolTime.GetState, Epoch, workspace:GetServerTimeNow())
	if not Ok or not S then return false, nil end
	local Night = if S.Hour < 6 then S.Day - 1 else S.Day
	return Lineage.IsFullMoon(S.Day, S.Hour), Night
end

local function strongRace(): boolean
	local R = Player:GetAttribute(`Race`)
	return R == `Werewolf` or R == `Vampire`
end

local function tween(I: Instance, T: number, Props)
	local Tw = TweenService:Create(I, TweenInfo.new(T, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), Props)
	Tw:Play()
	return Tw
end

-- 3 s silver glow along the screen edges (Werewolves feel the moon)
function Shared.SilverEdge()
	local G = Instance.new(`ScreenGui`)
	G.Name = `NHMoonEdge`
	G.IgnoreGuiInset = true
	G.DisplayOrder = 4
	G.ResetOnSpawn = false
	local Peak = 0.78 -- 1 - 0.22 alpha: an "edges only" Moment (style guide caps it at 0.25)
	local Strips = {}
	for _, Side in { { Vector2.new(0, 0), UDim2.new(1, 0, 0.16, 0), 90 }, { Vector2.new(0, 1), UDim2.new(1, 0, 0.16, 0), -90 },
		{ Vector2.new(0, 0), UDim2.new(0.12, 0, 1, 0), 0 }, { Vector2.new(1, 0), UDim2.new(0.12, 0, 1, 0), 180 } } do
		local F = Instance.new(`Frame`)
		F.AnchorPoint = Side[1]
		F.Position = UDim2.fromScale(Side[1].X, Side[1].Y)
		F.Size = Side[2]
		F.BorderSizePixel = 0
		F.BackgroundColor3 = SILVER
		F.BackgroundTransparency = 1
		local Gr = Instance.new(`UIGradient`)
		Gr.Rotation = Side[3]
		Gr.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(1, 1) })
		Gr.Parent = F
		F.Parent = G
		table.insert(Strips, F)
	end
	G.Parent = Player:WaitForChild(`PlayerGui`)
	local Up = if Fx.Reduced() then 0.6 else 0.9
	for _, F in Strips do tween(F, Up, { BackgroundTransparency = Peak }) end
	task.delay(Up + 1.2, function()
		for _, F in Strips do tween(F, 0.9, { BackgroundTransparency = 1 }) end
		task.delay(1, function() G:Destroy() end)
	end)
end

function Shared.Announce()
	local Ok, Moments = pcall(require, script.Parent.Parent:WaitForChild(`Gui`):WaitForChild(`Moments`))
	if not Ok or not Moments.Banner then return end
	Moments.Banner({
		Caption = `Nightfall`;
		Title = `The moon is full`;
		Text = if strongRace() then `Your blood answers it. Night powers run high until dawn.` else `Night powers run high until dawn.`;
		Color = Color3.fromRGB(214, 176, 190);
		Icon = `IconBannerFullMoon`;
		Hold = 3.2;
	})
end

function Shared.Enter(Night: number?)
	if State.On then return end
	State.On = true
	local S = sky()
	if S then
		State.BaseSize = State.BaseSize or S.MoonAngularSize
		local Swell = if Fx.Reduced() then 3 else SWELL
		tween(S, Swell, { MoonAngularSize = MOON_FULL })
	end
	-- (2.36, sky-2360) no grade of its own any more: Config.DayCycle.Moon.Full (World.DayCycle) is the full-moon look
	-- once a night (and once a session for the preview)
	local Key = Night or -2
	if not State.Announced[Key] then
		State.Announced[Key] = true
		-- (1.41) a crimson or blue moon brings its own banner (Controllers.World.MoonPhases)
		if not workspace:GetAttribute(`NHMoonEventTonight`) then task.delay(1.5, Shared.Announce) end
		if Player:GetAttribute(`Race`) == `Werewolf` then task.delay(2, Shared.SilverEdge) end
	end
end

function Shared.Leave()
	if not State.On then return end
	State.On = false
	local S = sky()
	if S and State.BaseSize then tween(S, if Fx.Reduced() then 3 else 8, { MoonAngularSize = State.BaseSize }) end
end

function Shared.OnStart()
	task.spawn(function()
		while true do
			local Full, Night = Shared.Now()
			local InMenu = Player:GetAttribute(`InMainMenu`) == true
			if Full and not InMenu then Shared.Enter(Night) elseif State.On then Shared.Leave() end
			task.wait(1)
		end
	end)
	-- (2.36) a grade left by an older build of this controller in a running session
	local Old = Lighting:FindFirstChild(`NHMoonGrade`)
	if Old then Old:Destroy() end
end

return Shared
