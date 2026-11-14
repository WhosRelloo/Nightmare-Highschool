--[[
	Day/night grade (client). Controllers.World.DayCycle   Config: ReplicatedStorage.Config.DayCycle

	The server only moves the sun (Services.School.SchoolClock writes Lighting.ClockTime). This blends the
	rest of the look by the school hour: dawn, day, dusk and a moody blue-violet night. Purely visual and
	local; it owns these properties and nothing else:
		Lighting: Ambient, OutdoorAmbient, Brightness, ExposureCompensation
		the Atmosphere: Density, Offset, Haze, Glare, Color, Decay
		the Bloom: Intensity
		its own ColorCorrectionEffect "NHDayGrade"

	It steps aside (suspends) while the main menu is up, because the menu sets its own grade. When it
	resumes it immediately rewrites its properties, puts the sun back at the real school time and
	re-applies the player's Shadows setting, so nothing from the menu's lighting snapshot is left over.

		DayCycle.Suspend(name) / DayCycle.Resume(name)   other client systems can take the lighting over
		DayCycle.Hour(): number                           the school hour (0..24) from the clock epoch
		DayCycle.LookAt(hour): table                      the blended look (for tests)
]]

local Lighting = game:GetService(`Lighting`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local Player = Players.LocalPlayer
local Config = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`DayCycle`))
local SchoolTime = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`SchoolTime`))

local Shared = {}
local Holds = {} :: { [string]: boolean }
local Grade: ColorCorrectionEffect? = nil
local WasActive = false

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
		Atm.Density, Atm.Offset, Atm.Haze, Atm.Glare = Look.Density, Look.Offset, Look.Haze, Look.Glare
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
		return
	end
	if not WasActive then handBack() end
	WasActive = true
	write(Shared.LookAt(Shared.Hour()))
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
	task.spawn(function()
		while true do
			pcall(step)
			task.wait(Config.UpdateSeconds or 0.2)
		end
	end)
end

return Shared
