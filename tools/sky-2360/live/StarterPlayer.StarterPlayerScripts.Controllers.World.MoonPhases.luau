--[[
	Moon phases (client). Controllers.World.MoonPhases   (1.41; the full moon itself: Controllers.World.FullMoon)

	- The sky's moon wears tonight's phase (Lineage.MoonTextures, from workspace NHMoonPhase): full, waning, new, waxing.
	- A new-moon night is full of stars (Sky.StarCount raised) and gets a Moment banner once a night. (2.36, sky-2360) Its
	  darker, cooler look and the crimson / blue moons' looks are Config.DayCycle.Moon (World.DayCycle): this no longer
	  writes NHNewMoonGrade or NHMoonEventGrade.
	Steps aside on the main menu. Testing: LocalPlayer attribute NHMoonPhasePreview = "Full" | "Waning" | "New" | "Waxing"
	forces a phase (and night).
]]
local Lighting = game:GetService(`Lighting`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local TweenService = game:GetService(`TweenService`)

local Player = Players.LocalPlayer
local Lineage = require(ReplicatedStorage:WaitForChild(`Lineage`))
local Fx = require(script.Parent.Parent:WaitForChild(`Fx`))

-- (2.36) the new-moon and special-moon grades moved to Config.DayCycle.Moon
local OFF = { TintColor = Color3.new(1, 1, 1); Contrast = 0; Saturation = 0; Brightness = 0 }
local NEW_STARS = 5000
-- (1.41) the special full moons: their own grade on top of the full-moon one, and a banner
local EVENT_BANNER = {
	Crimson = { Title = `A crimson moon`; Color = Color3.fromRGB(226, 70, 80);
		Text = { Vampire = `The blood moon is yours. Your power rises until dawn.`; Ghoul = `The crimson light stirs your hunger.`;
			Wraith = `The crimson light stirs the restless dead.`; Default = `The Vampires' night. Stay in the lit halls.` } };
	Blue = { Title = `A blue moon`; Color = Color3.fromRGB(150, 190, 255);
		Text = { Priest = `A holy light. Your faith burns brighter until dawn.`; Human = `The living stand stronger tonight.`;
			Default = `A rare, cold light. Priests and the living stand stronger tonight.` } };
}

local Shared = {}
local State = { Phase = nil :: string?; Base = nil :: string?; BaseStars = nil :: number?; Grade = nil :: ColorCorrectionEffect?; Dark = false; Told = {} :: { [string]: boolean };
	Event = nil :: string?; EventGrade = nil :: ColorCorrectionEffect? }

local function sky(): Sky? return Lighting:FindFirstChildOfClass(`Sky`) end
local function tween(I: Instance, T: number, Props)
	local Tw = TweenService:Create(I, TweenInfo.new(T, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), Props)
	Tw:Play()
	return Tw
end

-- (phase, night, special moon or nil). The preview attribute takes "Crimson" / "Blue" too.
function Shared.Now(): (string, boolean, string?)
	local Pv = Player:GetAttribute(`NHMoonPhasePreview`)
	if typeof(Pv) == `string` and Lineage.MoonTextures[Pv] then
		if Lineage.MoonEvents[Pv] then return `Full`, true, Pv end
		return Pv, true, nil
	end
	return workspace:GetAttribute(`NHMoonPhase`) or `Full`, workspace:GetAttribute(`NHMoonNight`) == true, workspace:GetAttribute(`NHMoonEventTonight`)
end

function Shared.EventBanner(Event: string)
	local B = EVENT_BANNER[Event]
	local Ok, Moments = pcall(require, script.Parent.Parent:WaitForChild(`Gui`):WaitForChild(`Moments`))
	if not (B and Ok and Moments.Banner) then return end
	Moments.Banner({ Caption = `Nightfall`; Title = B.Title; Text = B.Text[Player:GetAttribute(`Race`) or ``] or B.Text.Default; Color = B.Color; Icon = if Event == `Blue` then `IconBannerBlueMoon` else `IconBannerCrimsonMoon`; Hold = 3.6 })
end

function Shared.Banner()
	local Ok, Moments = pcall(require, script.Parent.Parent:WaitForChild(`Gui`):WaitForChild(`Moments`))
	if not Ok or not Moments.Banner then return end
	Moments.Banner({
		Caption = `Nightfall`;
		Title = `The new moon rises`;
		Icon = `IconBannerNewMoon`;
		Text = if Player:GetAttribute(`Race`) == `Wraith` then `The dark belongs to you tonight.` else `The dark belongs to the Wraiths tonight.`;
		Color = Color3.fromRGB(170, 190, 230);
		Hold = 3.2;
	})
end

function Shared.Apply(Phase: string, Night: boolean, Event: string?)
	local S = sky()
	if S then
		State.Base = State.Base or S.MoonTextureId
		local Tex = Lineage.MoonTextures[Event or Phase]
		local Want = if typeof(Tex) == `string` and Tex ~= `` then Tex else State.Base
		if S.MoonTextureId ~= Want then S.MoonTextureId = Want end
	end
	-- the new-moon night: darker, cooler, more stars
	local Dark = Night and Phase == `New` and Player:GetAttribute(`InMainMenu`) ~= true
	if Dark ~= State.Dark then
		State.Dark = Dark
		if S then
			State.BaseStars = State.BaseStars or S.StarCount
			S.StarCount = if Dark then NEW_STARS else State.BaseStars
		end
		if Dark then
			local Key = tostring(workspace:GetAttribute(`NHMoonPhase`)) .. tostring(math.floor(workspace:GetServerTimeNow() / 600))
			if not State.Told[Key] then State.Told[Key] = true task.delay(1.5, Shared.Banner) end
		end
	end
	-- the special moon's night: its grade over the full-moon one, and its banner (World.FullMoon skips its own)
	local On = if Night and Player:GetAttribute(`InMainMenu`) ~= true then Event else nil
	if On ~= State.Event then
		State.Event = On
		if On then
			local Key = On .. tostring(math.floor(workspace:GetServerTimeNow() / 600))
			if not State.Told[Key] then State.Told[Key] = true task.delay(1.5, function() Shared.EventBanner(On) end) end
		end
	end
end

function Shared.OnStart()
	-- (2.36) grades left by an older build of this controller in a running session
	for _, N in { `NHNewMoonGrade`, `NHMoonEventGrade` } do
		local Old = Lighting:FindFirstChild(N)
		if Old then Old:Destroy() end
	end
	task.spawn(function()
		while true do
			local Ok, Phase, Night, Event = pcall(Shared.Now)
			if Ok then pcall(Shared.Apply, Phase, Night, Event) end
			task.wait(1)
		end
	end)
end

return Shared
