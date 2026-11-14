--[[
	Day/night grade (client). Controllers.World.DayCycle   Config: ReplicatedStorage.Config.DayCycle

	The server only moves the sun (Services.School.SchoolClock writes Lighting.ClockTime). This blends the
	rest of the look by the school hour: dawn, day, dusk and a moody blue-violet night. Purely visual and
	local; it owns these properties and nothing else:
		Lighting: Ambient, OutdoorAmbient, Brightness, ExposureCompensation
		the Atmosphere: Density, Offset, Haze, Glare, Color, Decay
		the Bloom: Intensity
		its own ColorCorrectionEffect "NHDayGrade"
		the Sky's six Skybox faces and SkyboxOrientation, only once Config.DayCycle.Skies has ids (2.16): one painted
		sky per look, swapped under a short swell of haze at dusk and dawn (two skies can't blend). Never the moon
		texture, MoonAngularSize or StarCount (World.FullMoon / World.MoonPhases own those).

	It steps aside (suspends) while the main menu is up, because the menu sets its own grade. When it
	resumes it immediately rewrites its properties, puts the sun back at the real school time and
	re-applies the player's Shadows setting, so nothing from the menu's lighting snapshot is left over.

		DayCycle.Suspend(name) / DayCycle.Resume(name)   other client systems can take the lighting over
		DayCycle.Hour(): number                           the school hour (0..24) from the clock epoch
		DayCycle.LookAt(hour): table                      the blended look (for tests)
		DayCycle.SkyAt(hour): (string?, number)           the painted sky set and its turn at that hour (nil = the place's own)
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

local NUMBERS = { `Brightness`, `ExposureCompensation`, `Density`, `Offset`, `Haze`, `Glare`, `Bloom`, `GradeBrightness`, `Contrast`, `Saturation` }
local COLORS = { `Ambient`, `OutdoorAmbient`, `AtmosphereColor`, `Decay`, `Tint` }

local function smooth(x: number): number return x * x * (3 - 2 * x) end

function Shared.Hour(): number
	local Clock = ReplicatedStorage:FindFirstChild(`SchoolClock`)
	local Epoch = Clock and Clock:GetAttribute(`Epoch`)
	if typeof(Epoch) == `number` then
		local Ok, S = pcall(SchoolTime.GetState, Epoch, workspace:GetServerTimeNow())
		if Ok and S and typeof(S.Hour) == `number` then return S.Hour % 24 end
	end
	return Lighting.ClockTime % 24
end

function Shared.LookAt(Hour: number)
	local Keys = Config.Keys
	local A, B = Keys[1], Keys[#Keys]
	for I = 1, #Keys - 1 do
		if Hour >= Keys[I][1] and Hour <= Keys[I + 1][1] then A, B = Keys[I], Keys[I + 1] break end
	end
	local Span = B[1] - A[1]
	local T = if Span > 0 then smooth(math.clamp((Hour - A[1]) / Span, 0, 1)) else 0
	local Out = {}
	for _, K in NUMBERS do Out[K] = A[2][K] + (B[2][K] - A[2][K]) * T end
	for _, K in COLORS do Out[K] = A[2][K]:Lerp(B[2][K], T) end
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

function Shared.SkyAt(Hour: number): (string?, number)
	local Over = Player:GetAttribute(`NHSkyPreview`) or workspace:GetAttribute(`NHSky`)
	if typeof(Over) == `string` and faces(Over) then return Over, 0 end
	local Sched = Skies.Schedule
	local Pick = Sched[#Sched]
	for _, E in Sched do if Hour >= E[1] then Pick = E end end
	local Name, Turn = Pick[2], Pick[3] or 0
	if Name == `Night` and Skies.BlueMoon and faces(Skies.BlueMoon)
		and (Player:GetAttribute(`NHMoonPhasePreview`) == `Blue` or workspace:GetAttribute(`NHMoonEventTonight`) == `Blue`) then
		Name = Skies.BlueMoon
	end
	if not faces(Name) then return nil, 0 end
	return Name, Turn
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

local function write(Look)
	Lighting.Ambient = Look.Ambient
	Lighting.OutdoorAmbient = Look.OutdoorAmbient
	Lighting.Brightness = Look.Brightness
	Lighting.ExposureCompensation = Look.ExposureCompensation
	local Atm = Lighting:FindFirstChildOfClass(`Atmosphere`)
	if Atm then
		Atm.Density, Atm.Offset, Atm.Haze, Atm.Glare = Look.Density, Look.Offset, math.min(Look.Haze + SkyState.Boost, 10), Look.Glare
		Atm.Color, Atm.Decay = Look.AtmosphereColor, Look.Decay
	end
	local Bloom = Lighting:FindFirstChild(`Bloom`)
	if Bloom and Bloom:IsA(`BloomEffect`) then Bloom.Intensity = Look.Bloom end
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
	local Instant = not WasActive
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

function Shared.OnStart()
	if not Config.Enabled then return end
	Player:GetAttributeChangedSignal(`InMainMenu`):Connect(function()
		-- the menu restores its lighting snapshot as it closes; let it finish, then take over
		task.delay(0.2, step)
	end)
	-- the painted skies' faces, so a swap never shows an empty sky
	if anySky() then
		task.spawn(function()
			local Ids = {}
			for Name in Skies.Sets do
				local Set = faces(Name)
				if Set then for _, Id in Set do table.insert(Ids, Id) end end
			end
			pcall(ContentProvider.PreloadAsync, ContentProvider, Ids)
		end)
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
