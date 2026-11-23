--[[
	Day/night grade (client). Controllers.World.DayCycle   Config: ReplicatedStorage.Config.DayCycle   Docs: docs/Sky-and-Lighting.md

	The server only moves the sun (Services.School.SchoolClock writes Lighting.ClockTime). This blends the
	rest of the look by the school hour: dawn, morning, day, golden hour, dusk, night and the witching hours.
	Purely visual and local; it owns these properties and nothing else:
		Lighting: Ambient, OutdoorAmbient, Brightness, ExposureCompensation, ColorShift_Top/Bottom (2.36),
		          EnvironmentDiffuseScale, EnvironmentSpecularScale (2.36)
		the Atmosphere: Density, Offset, Haze, Glare, Color, Decay
		Terrain.Clouds (2.36, made if missing): Cover, Density, Color   (World.SkyMotion owns the wind)
		the Bloom: Intensity, Size, Threshold (2.36)
		the SunRays (2.36, made if missing): Intensity, Spread
		its own ColorCorrectionEffect "NHDayGrade"
		the Sky's six Skybox faces and SkyboxOrientation: one painted sky per slot, swapped under a short swell of haze
		(two skies can't blend). Never the moon texture, MoonAngularSize or StarCount (World.FullMoon / World.MoonPhases).

	(2.36, sky-2360) on top of the blended key:
		Season  workspace NHSeason = "Winter" | "Spring" | "Summer" | "Nightmare" (nil = Autumn; Studio test:
		        LocalPlayer NHSeasonPreview). Its Looks override fields by key name, Keys/Schedule replace the lists,
		        Skies maps a schedule slot to its own set.
		Moon    the night's moon modifier (Mul / Add / Set, scaled by NightWeight): the event moon (NHMoonEventTonight),
		        else the season's moon (Nightmare: Crimson), else the phase (NHMoonPhase). Its Sky replaces the Night
		        slot, unless the season paints its own night for its own moon. This is the one grade: World.FullMoon and
		        World.MoonPhases no longer write NHMoonGrade / NHNewMoonGrade / NHMoonEventGrade.
		Preload only the shown set and the next one (Skies.Preload = "ShownAndNext"), never all 19.

	It steps aside (suspends) while the main menu is up, because the menu sets its own grade. When it
	resumes it immediately rewrites its properties, puts the sun back at the real school time and
	re-applies the player's Shadows setting, so nothing from the menu's lighting snapshot is left over.

		DayCycle.Suspend(name) / DayCycle.Resume(name)   other client systems can take the lighting over
		DayCycle.HoldExposure(name, on)                   (2.35.0) only ExposureCompensation is left alone while held
		DayCycle.Hour(): number                           the school hour (0..24) from the clock epoch
		DayCycle.LookAt(hour): table                      the blended look with the season and moon (for tests)
		DayCycle.SkyAt(hour): (string?, number)           the painted sky set and its turn at that hour (nil = the place's own)
		DayCycle.Season(): string?  DayCycle.Moon(): string?  DayCycle.NightWeight(hour): number   (2.36)
		DayCycle.Active(): boolean                        (2.36) false while suspended (World.SkyMotion follows it)
]]

local Lighting = game:GetService(`Lighting`)
local Players = game:GetService(`Players`)
local ContentProvider = game:GetService(`ContentProvider`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local Player = Players.LocalPlayer
local Config = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`DayCycle`))
local SchoolTime = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`SchoolTime`))

local Shared = {}
local Holds = {} :: { [string]: boolean }
local ExposureHolds = {} :: { [string]: boolean } -- (2.35.0) Controllers.Cine: a seamless cut's graded exposure
local HeldHours = {} :: { [string]: number } -- (2.24.0) a cutscene set at another hour (Controllers.Cine: Def.Clock)
local SnapNext = false
local Grade: ColorCorrectionEffect? = nil
local WasActive = false

local FACES = { `Bk`, `Dn`, `Ft`, `Lf`, `Rt`, `Up` }
local Skies = Config.Skies
local SkyState = {
	Base = nil :: { [string]: any }?,  -- the place's own faces, put back when no painted set applies
	Shown = nil :: string?,             -- the key now on the Sky, "Set|turn" ("|0" = the place's own)
	From = 0, Boost = 0,                -- a swap in progress: when it started; the extra haze it adds right now
	Pending = nil :: string?,           -- the key the swap will put up at its peak
}
local Preloaded = {} :: { [string]: boolean } -- (2.36) sets already handed to PreloadAsync

-- (2.36) every field the blend knows; a key without a field (a 2.16 config) just skips it
local NUMBERS = { `Brightness`, `ExposureCompensation`, `Density`, `Offset`, `Haze`, `Glare`, `Bloom`, `GradeBrightness`, `Contrast`, `Saturation`,
	`EnvDiffuse`, `EnvSpecular`, `CloudCover`, `CloudDensity`, `BloomSize`, `BloomThreshold`, `SunRays`, `SunRaysSpread` }
local COLORS = { `Ambient`, `OutdoorAmbient`, `AtmosphereColor`, `Decay`, `Tint`, `ColorShiftTop`, `ColorShiftBottom`, `CloudColor` }

local function smooth(x: number): number return x * x * (3 - 2 * x) end

function Shared.Hour(): number
	for _, H in HeldHours do return H % 24 end -- (2.24.0) a cut's hour wins while it plays
	local Clock = ReplicatedStorage:FindFirstChild(`SchoolClock`)
	local Epoch = Clock and Clock:GetAttribute(`Epoch`)
	if typeof(Epoch) == `number` then
		local Ok, S = pcall(SchoolTime.GetState, Epoch, workspace:GetServerTimeNow())
		if Ok and S and typeof(S.Hour) == `number` then return S.Hour % 24 end
	end
	return Lighting.ClockTime % 24
end

---| Season and moon (2.36) |---

function Shared.Season(): string?
	local S = Player:GetAttribute(`NHSeasonPreview`) or workspace:GetAttribute(`NHSeason`)
	if typeof(S) == `string` and Config.Seasons and Config.Seasons[S] then return S end
	return nil
end

local function season(): { [string]: any }?
	local S = Shared.Season()
	return S and Config.Seasons[S] or nil
end

-- 0 by day, 1 at night: NightWeight.Rise ramps it up in the evening, Fall down in the morning
function Shared.NightWeight(Hour: number): number
	local W = Config.NightWeight
	if not W then return if Hour >= 20 or Hour < 5 then 1 else 0 end
	local R0, R1, F0, F1 = W.Rise[1], W.Rise[2], W.Fall[1], W.Fall[2]
	if Hour >= R1 or Hour < F0 then return 1 end
	if Hour >= R0 then return smooth((Hour - R0) / math.max(R1 - R0, 1e-3)) end
	if Hour < F1 then return 1 - smooth((Hour - F0) / math.max(F1 - F0, 1e-3)) end
	return 0
end

-- the night's moon modifier name: the preview, the event moon, the season's moon, then the phase
function Shared.Moon(): string?
	local Moons = Config.Moon
	if not Moons then return nil end
	local Pv = Player:GetAttribute(`NHMoonPhasePreview`)
	if typeof(Pv) == `string` and Moons[Pv] then return Pv end
	local Ev = workspace:GetAttribute(`NHMoonEventTonight`)
	if typeof(Ev) == `string` and Moons[Ev] then return Ev end
	local Se = season()
	if Se and typeof(Se.Moon) == `string` and Moons[Se.Moon] then return Se.Moon end
	local Ph = workspace:GetAttribute(`NHMoonPhase`)
	if typeof(Ph) == `string` and Moons[Ph] then return Ph end
	return nil
end

local function clamp01(x: number): number return math.clamp(x, 0, 1) end

-- Luau Color3 can't be added: channel-wise, clamped
local function addColor(C: Color3, A: Color3, W: number): Color3
	return Color3.new(clamp01(C.R + A.R * W), clamp01(C.G + A.G * W), clamp01(C.B + A.B * W))
end

local function applyMoon(Out: { [string]: any }, Mod: { [string]: any }?, W: number)
	if not Mod or W <= 0 then return end
	for K, M in Mod.Mul or {} do
		if typeof(Out[K]) == `number` then Out[K] = Out[K] * (1 + (M - 1) * W) end
	end
	for K, A in Mod.Add or {} do
		if typeof(Out[K]) == `number` and typeof(A) == `number` then Out[K] = Out[K] + A * W
		elseif typeof(Out[K]) == `Color3` and typeof(A) == `Color3` then Out[K] = addColor(Out[K], A, W) end
	end
	for K, S in Mod.Set or {} do
		if typeof(Out[K]) == `number` and typeof(S) == `number` then Out[K] = Out[K] + (S - Out[K]) * W
		elseif typeof(Out[K]) == `Color3` and typeof(S) == `Color3` then Out[K] = Out[K]:Lerp(S, W) end
	end
end

-- a key's look with the season's override for that key's name
local NameOf = {} :: { [any]: string }
for Name, Look in Config.Looks or {} do NameOf[Look] = Name end

local function lookFor(Look: { [string]: any }, Se: { [string]: any }?): { [string]: any }
	local Over = Se and Se.Looks and Se.Looks[NameOf[Look] or ``]
	if not Over then return Look end
	local Out = table.clone(Look)
	for K, V in Over do Out[K] = V end
	return Out
end

function Shared.LookAt(Hour: number)
	local Se = season()
	local Keys = (Se and Se.Keys) or Config.Keys
	local A, B = Keys[1], Keys[#Keys]
	for I = 1, #Keys - 1 do
		if Hour >= Keys[I][1] and Hour <= Keys[I + 1][1] then A, B = Keys[I], Keys[I + 1] break end
	end
	local Span = B[1] - A[1]
	local T = if Span > 0 then smooth(math.clamp((Hour - A[1]) / Span, 0, 1)) else 0
	local LA, LB = lookFor(A[2], Se), lookFor(B[2], Se)
	local Out = {}
	for _, K in NUMBERS do
		if typeof(LA[K]) == `number` and typeof(LB[K]) == `number` then Out[K] = LA[K] + (LB[K] - LA[K]) * T end
	end
	for _, K in COLORS do
		if typeof(LA[K]) == `Color3` and typeof(LB[K]) == `Color3` then Out[K] = LA[K]:Lerp(LB[K], T) end
	end
	local Moon = Shared.Moon()
	applyMoon(Out, Moon and Config.Moon[Moon] or nil, Shared.NightWeight(Hour))
	return Out
end

---| Painted skies |---

local function asset(Id: any): string?
	if typeof(Id) == `number` and Id > 0 then return `rbxassetid://{Id}` end
	if typeof(Id) ~= `string` or Id == `` then return nil end
	if Id:match(`^%d+$`) then return `rbxassetid://{Id}` end
	return Id
end

-- a set's six faces, or nil while any of them is missing
local function faces(Name: string?): { [string]: string }?
	local Set = Name and Skies and Skies.Sets and Skies.Sets[Name]
	if not Set then return nil end
	local Out = {}
	for _, F in FACES do
		local Id = asset(Set[F])
		if not Id then return nil end
		Out[F] = Id
	end
	return Out
end

local function anySky(): boolean
	if not (Skies and Skies.Enabled and Skies.Sets) then return false end
	for Name in Skies.Sets do if faces(Name) then return true end end
	return false
end

-- (2.36) a schedule slot's set: the moon's sky for the Night slot, then the season's own painting for the slot
local function mapSlot(Slot: string): string
	local Se = season()
	local Own = Se and Se.Skies and Se.Skies[Slot]
	if Slot == `Night` then
		local Moon = Shared.Moon()
		local MoonSky = Moon and Config.Moon[Moon] and Config.Moon[Moon].Sky
		-- the season paints its own night for its own moon (Nightmare's NightmareNight wins over NightCrimson)
		local SeasonMoon = Se ~= nil and Se.Moon == Moon
		if MoonSky and not (Own and SeasonMoon) and faces(MoonSky) then return MoonSky end
		if not Config.Moon and Skies.BlueMoon and (Player:GetAttribute(`NHMoonPhasePreview`) == `Blue`
			or workspace:GetAttribute(`NHMoonEventTonight`) == `Blue`) and faces(Skies.BlueMoon) then
			return Skies.BlueMoon -- a 2.16 config without Moon
		end
	end
	if Own and faces(Own) then return Own end
	return Slot
end

local function schedule(): { any }
	local Se = season()
	return (Se and Se.Schedule) or Skies.Schedule
end

function Shared.SkyAt(Hour: number): (string?, number)
	local Over = Player:GetAttribute(`NHSkyPreview`) or workspace:GetAttribute(`NHSky`)
	if typeof(Over) == `string` and faces(Over) then return Over, 0 end
	local Sched = schedule()
	local Pick = Sched[#Sched]
	for _, E in Sched do if Hour >= E[1] then Pick = E end end
	local Name, Turn = mapSlot(Pick[2]), Pick[3] or 0
	if not faces(Name) then return nil, 0 end
	return Name, Turn
end

-- (2.36) the set that follows the shown one in the schedule (the season and the moon applied)
local function nextSet(Hour: number): string?
	local Sched = schedule()
	local Idx = #Sched
	for I, E in Sched do if Hour >= E[1] then Idx = I end end
	local N = Sched[(Idx % #Sched) + 1]
	return N and mapSlot(N[2]) or nil
end

local function preload(Names: { string? })
	if Skies.Preload == false then return end
	local Ids = {}
	for _, Name in Names do
		if Name and not Preloaded[Name] then
			local Set = faces(Name)
			if Set then
				Preloaded[Name] = true
				for _, Id in Set do table.insert(Ids, Id) end
			end
		end
	end
	if #Ids > 0 then task.spawn(pcall, ContentProvider.PreloadAsync, ContentProvider, Ids) end
end

function Shared.Preloaded(): { string } -- (2.36) for tests: the sets handed to PreloadAsync so far
	local L = {}
	for Name in Preloaded do table.insert(L, Name) end
	table.sort(L)
	return L
end

local function putSky(Key: string)
	local S = Lighting:FindFirstChildOfClass(`Sky`)
	if not S then return end
	if not SkyState.Base then
		local B = { Turn = S.SkyboxOrientation }
		for _, F in FACES do B[F] = (S :: any)[`Skybox{F}`] end
		SkyState.Base = B
	end
	local Name, Turn = Key:match(`^(.-)|(.*)$`)
	local Set = faces(Name)
	local Src = Set or SkyState.Base :: any
	for _, F in FACES do (S :: any)[`Skybox{F}`] = Src[F] end
	S.SkyboxOrientation = if Set then Vector3.new(0, tonumber(Turn) or 0, 0) else SkyState.Base.Turn
	SkyState.Shown = Key
end

-- picks the sky for the hour; a change starts a swap (instant when Instant, e.g. on joining or leaving the menu)
local function stepSky(Hour: number, Instant: boolean)
	if not anySky() then SkyState.Boost = 0 return end
	local Name, Turn = Shared.SkyAt(Hour)
	preload({ Name, nextSet(Hour) })
	local Key = if Name then `{Name}|{Turn}` else `|0`
	if Instant or SkyState.Shown == nil then
		SkyState.Pending, SkyState.Boost = nil, 0
		if Key ~= SkyState.Shown then putSky(Key) end
		return
	end
	if not SkyState.Pending and Key ~= SkyState.Shown then
		SkyState.Pending, SkyState.From = Key, os.clock()
	end
	if SkyState.Pending then
		local Len = math.max(Skies.SwapSeconds or 3, 0.1)
		local T = (os.clock() - SkyState.From) / Len
		if T >= 0.5 and SkyState.Shown ~= SkyState.Pending then putSky(SkyState.Pending) end
		if T >= 1 then
			SkyState.Pending, SkyState.Boost = nil, 0
		else
			SkyState.Boost = math.sin(math.pi * T) * (Skies.SwapHaze or 1)
		end
	end
end

local function grade(): ColorCorrectionEffect
	if Grade and Grade.Parent then return Grade end
	local G = Lighting:FindFirstChild(`NHDayGrade`) :: ColorCorrectionEffect?
	if not G then
		G = Instance.new(`ColorCorrectionEffect`)
		G.Name = `NHDayGrade`
		G.Parent = Lighting
	end
	Grade = G
	return G :: ColorCorrectionEffect
end

local function active(): boolean
	if not Config.Enabled then return false end
	if Player:GetAttribute(`InMainMenu`) == true then return false end
	-- the menu still owns the lighting until it has restored its snapshot and removed its grade
	if Lighting:FindFirstChild(`NHMenuGrade`) then return false end
	for _ in Holds do return false end
	return true
end

function Shared.Active(): boolean return WasActive end

-- (2.36) Terrain.Clouds and the SunRays are made if the place has none
local function clouds(): Clouds?
	local T = workspace:FindFirstChildOfClass(`Terrain`)
	if not T then return nil end
	local C = T:FindFirstChildOfClass(`Clouds`)
	if not C then
		C = Instance.new(`Clouds`)
		C.Parent = T
	end
	return C
end

local function sunRays(): SunRaysEffect
	local S = Lighting:FindFirstChildOfClass(`SunRaysEffect`)
	if not S then
		S = Instance.new(`SunRaysEffect`)
		S.Name = `SunRays`
		S.Parent = Lighting
	end
	return S :: SunRaysEffect
end

local function write(Look)
	Lighting.Ambient = Look.Ambient
	Lighting.OutdoorAmbient = Look.OutdoorAmbient
	Lighting.Brightness = Look.Brightness
	if next(ExposureHolds) == nil then Lighting.ExposureCompensation = Look.ExposureCompensation end
	if Look.ColorShiftTop then Lighting.ColorShift_Top = Look.ColorShiftTop end
	if Look.ColorShiftBottom then Lighting.ColorShift_Bottom = Look.ColorShiftBottom end
	if Look.EnvDiffuse then Lighting.EnvironmentDiffuseScale = Look.EnvDiffuse end
	if Look.EnvSpecular then Lighting.EnvironmentSpecularScale = Look.EnvSpecular end
	local Atm = Lighting:FindFirstChildOfClass(`Atmosphere`)
	if Atm then
		Atm.Density, Atm.Offset, Atm.Haze, Atm.Glare = Look.Density, Look.Offset, math.min(Look.Haze + SkyState.Boost, 10), Look.Glare
		Atm.Color, Atm.Decay = Look.AtmosphereColor, Look.Decay
	end
	if Look.CloudCover then
		local C = clouds()
		if C then C.Cover, C.Density, C.Color = Look.CloudCover, Look.CloudDensity or C.Density, Look.CloudColor or C.Color end
	end
	local Bloom = Lighting:FindFirstChild(`Bloom`)
	if Bloom and Bloom:IsA(`BloomEffect`) then
		Bloom.Intensity = Look.Bloom
		if Look.BloomSize then Bloom.Size = Look.BloomSize end
		if Look.BloomThreshold then Bloom.Threshold = Look.BloomThreshold end
	end
	if Look.SunRays then
		local S = sunRays()
		S.Intensity, S.Spread = Look.SunRays, Look.SunRaysSpread or S.Spread
	end
	local G = grade()
	G.Enabled = true
	G.Brightness, G.Contrast, G.Saturation, G.TintColor = Look.GradeBrightness, Look.Contrast, Look.Saturation, Look.Tint
end

-- coming back from the menu (or another hold): the sun to the real school time, the player's Shadows setting back
local function handBack()
	pcall(function() Lighting.ClockTime = Shared.Hour() end)
	pcall(function()
		local Settings = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Settings`))
		if Settings.Apply then Settings.Apply(`Shadows`) end
	end)
end

local function step()
	local Now = active()
	if not Now then
		if WasActive and Grade then Grade.Enabled = false end -- the menu brings its own grade
		WasActive = false
		SkyState.Pending, SkyState.Boost = nil, 0 -- a half-done swap finishes instantly on the way back
		return
	end
	local Instant = not WasActive or SnapNext
	SnapNext = false
	if Instant then handBack() end
	WasActive = true
	local Hour = Shared.Hour()
	stepSky(Hour, Instant)
	write(Shared.LookAt(Hour))
end

function Shared.Suspend(Name: string)
	Holds[Name] = true
	step()
end

function Shared.Resume(Name: string)
	Holds[Name] = nil
	step()
end

-- (2.35.0, task 8 fix round 2) a seamless cut's grade owns ExposureCompensation while it plays (and eases it back over
-- its blend out); the grade, ambient, atmosphere and sky keep following the hour, so nothing pops. Releasing it doesn't
-- write at once: the next 0.2 s step does, from the exposure the cut eased back to (the same hour's value)
function Shared.HoldExposure(Name: string, On: boolean)
	ExposureHolds[Name] = if On then true else nil
end

-- (2.24.0) a cutscene set at another hour (the roll call's morning, COLLECTED's midnight): the whole look (light,
-- atmosphere, sky) follows that hour at once, and the sun is held there; HoldHour(Name, nil) snaps back to school time
function Shared.HoldHour(Name: string, Hour: number?)
	HeldHours[Name] = Hour
	SnapNext = true
	if Hour then pcall(function() Lighting.ClockTime = Hour end) else handBack() end
	step()
end

function Shared.OnStart()
	if not Config.Enabled then return end
	Player:GetAttributeChangedSignal(`InMainMenu`):Connect(function()
		-- the menu restores its lighting snapshot as it closes; let it finish, then take over
		task.delay(0.2, step)
	end)
	-- 2.16 preloaded every set; with Preload = "ShownAndNext" stepSky preloads the shown and next set as it goes
	if anySky() and Skies.Preload ~= `ShownAndNext` and Skies.Preload ~= false then
		local Names = {}
		for Name in Skies.Sets do table.insert(Names, Name) end
		preload(Names)
	end
	task.spawn(function()
		while true do
			pcall(step)
			-- a swap's haze swell is stepped smoothly; otherwise the slow clock needs few updates
			task.wait(if SkyState.Pending then 1 / 30 else (Config.UpdateSeconds or 0.2))
		end
	end)
end

return Shared
