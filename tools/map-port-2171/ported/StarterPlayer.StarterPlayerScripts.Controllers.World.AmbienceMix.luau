--[[
	AmbienceMix (client). Controllers.World.AmbienceMix   (ambience foundations 1 and 3, 2.16.0;
	docs/Environment-Ambience-Concepts.md)

	The mixer. Every ambient sound goes through one of four SoundGroups under the Music & Ambience volume:
	  SoundService.NH_Master.NH_Music.NH_Ambience
	    Bed      the zone's loop (Controllers.World.Soundscape)
	    Weather  the rain (Controllers.World.KitFx)
	    Spot     3D loops on tagged props (Controllers.World.AmbientSounds)
	    OneShot  the random one-shots (Controllers.World.AmbientSounds)
	Ambience never hides a fight: while you're combat-tagged (the CombatTagUntil attribute) all of NH_Ambience
	ducks to Config.Ambience.Mix.DuckTo (about -6 dB), fast in (Attack) and slow back (Release).
	Cutscenes keep the bed but drop the close layers: in cinematic view (Gui.Cinematic) or a talk shot
	(Gui.Dialogue's NHTalkDof), Spot and OneShot fade out, so there's no hole in the sound.

	Room reverb (concept 3): SoundService.AmbientReverb follows where you stand. The place you're in
	(Functions.RegionBoxes) picks it from Config.Ambience.Reverb; with no place, the soundscape's bed does
	(Config.Ambience.ReverbByBed). The main menu has none. ReplicatedStorage attribute NHReverbOff switches it off.
	Region boxes are hidden on this client (so the Map's boxes, lined up to be placed, never show in game).
	Status for testing: Shared.Status().
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local SoundService = game:GetService(`SoundService`)
local Lighting = game:GetService(`Lighting`)

local Config = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`Ambience`))
local RegionBoxes = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`RegionBoxes`))

local Player = Players.LocalPlayer
local Shared = {}
local Local = {}

local LAYERS = { `Bed`, `Weather`, `Spot`, `OneShot` }
local Groups = {} :: { [string]: SoundGroup }
local Root = nil :: SoundGroup?
local State = { Duck = 1, Close = 1, Reverb = `NoReverb`, Region = nil :: string?, Combat = false, Cutscene = false }

-- the NH_Music group is made by UI.Settings when the settings load; wait for it, then hang ours under it
function Local.Build(): boolean
	local Master = SoundService:FindFirstChild(`NH_Master`)
	local Music = Master and Master:FindFirstChild(`NH_Music`)
	if not (Music and Music:IsA(`SoundGroup`)) then return false end
	local A = Music:FindFirstChild(`NH_Ambience`) :: SoundGroup?
	if not A then
		A = Instance.new(`SoundGroup`)
		A.Name = `NH_Ambience`
		A.Volume = 1
		A.Parent = Music
	end
	Root = A
	for _, Name in LAYERS do
		local G = A:FindFirstChild(Name) :: SoundGroup?
		if not G then
			G = Instance.new(`SoundGroup`)
			G.Name = Name
			G.Volume = 1
			G.Parent = A
		end
		Groups[Name] = G
	end
	return true
end

-- the group an ambient sound should play through (nil until the settings have made the volume groups)
function Shared.Group(Name: string): SoundGroup?
	if not Root or not Root.Parent then
		if not Local.Build() then return nil end
	end
	return Groups[Name]
end

function Local.Cutscene(): boolean
	if Lighting:FindFirstChild(`NHTalkDof`) then return true end
	local Gui = script.Parent.Parent:FindFirstChild(`Gui`)
	local Cine = Gui and Gui:FindFirstChild(`Cinematic`)
	if not Cine then return false end
	local Ok, On = pcall(function() return require(Cine).IsOn() end)
	return Ok and On == true
end

function Local.Approach(Cur: number, Target: number, Dt: number, Up: number, Down: number): number
	local T = if Target < Cur then Down else Up
	if T <= 0 then return Target end
	return Target + (Cur - Target) * math.exp(-Dt * 4.6 / T) -- 99% of the way in T seconds
end

function Local.Where(): Vector3?
	local Char = Player.Character
	local Hrp = Char and Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if Hrp then return Hrp.Position end
	local Cam = workspace.CurrentCamera
	return Cam and Cam.CFrame.Position
end

function Local.Soundscape(): string?
	local M = script.Parent:FindFirstChild(`Soundscape`)
	if not M then return nil end
	local Ok, S = pcall(function() return require(M).Status() end)
	return if Ok and S then S.Where else nil
end

function Local.PickReverb(): string
	if ReplicatedStorage:GetAttribute(`NHReverbOff`) == true then return `NoReverb` end
	if Player:GetAttribute(`InMainMenu`) == true then return `NoReverb` end
	local P = Local.Where()
	if not P then return `NoReverb` end
	local Region = RegionBoxes.At(P)
	State.Region = Region
	local Bed = Local.Soundscape()
	-- a classroom's own zone (the soundscape's bed) is more exact than the hall around it
	local Pick = (Bed and Config.ReverbByZone[Bed]) or (Region and Config.Reverb[Region]) or (Bed and Config.ReverbByBed[Bed])
	return Pick or `NoReverb`
end

function Local.HideBoxes()
	local F = workspace:FindFirstChild(`Regions`)
	if not F then return end
	local function hide(B: Instance)
		if B:IsA(`BasePart`) then B.LocalTransparencyModifier = 1 end
		for _, D in B:GetDescendants() do
			if D:IsA(`SurfaceGui`) or D:IsA(`BillboardGui`) or D:IsA(`SelectionBox`) or D:IsA(`Highlight`) then
				(D :: any).Enabled = false
			end
		end
	end
	for _, B in F:GetChildren() do hide(B) end
	F.ChildAdded:Connect(hide)
end

function Shared.OnStart()
	task.spawn(function()
		while not Local.Build() do task.wait(0.5) end
	end)
	task.spawn(function()
		local F = workspace:WaitForChild(`Regions`, 30)
		if F then Local.HideBoxes() end
	end)
	local Mix = Config.Mix
	local Acc = 0
	RunService.Heartbeat:Connect(function(Dt)
		if not Root or not Root.Parent then return end
		-- ducking: combat-tagged = the ambience steps back
		local Until = Player:GetAttribute(`CombatTagUntil`)
		State.Combat = typeof(Until) == `number` and Until > workspace:GetServerTimeNow()
		if ReplicatedStorage:GetAttribute(`NHAmbienceDuckOff`) == true then State.Combat = false end
		State.Duck = Local.Approach(State.Duck, if State.Combat then Mix.DuckTo else 1, Dt, Mix.Release, Mix.Attack)
		Root.Volume = State.Duck
		Acc += Dt
		if Acc < 0.25 then return end
		local Step = Acc
		Acc = 0
		-- cutscenes: the close layers fade, the bed and the weather stay
		State.Cutscene = Local.Cutscene()
		State.Close = Local.Approach(State.Close, if State.Cutscene then 0 else 1, Step, Mix.CutsceneFade, Mix.CutsceneFade)
		Groups.Spot.Volume = State.Close
		Groups.OneShot.Volume = State.Close
		-- the room's reverb
		local R = Local.PickReverb()
		if R ~= State.Reverb then
			local Ok = pcall(function() SoundService.AmbientReverb = (Enum.ReverbType :: any)[R] end)
			State.Reverb = if Ok then R else State.Reverb
		end
	end)
end

function Shared.Status()
	return { Duck = math.floor(State.Duck * 100) / 100; Close = math.floor(State.Close * 100) / 100; Combat = State.Combat;
		Cutscene = State.Cutscene; Region = State.Region; Reverb = State.Reverb; Live = SoundService.AmbientReverb.Name;
		Groups = Root ~= nil }
end

return Shared
