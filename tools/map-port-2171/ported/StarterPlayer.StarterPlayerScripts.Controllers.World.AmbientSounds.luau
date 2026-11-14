--[[
	AmbientSounds (client). Controllers.World.AmbientSounds   (ambience foundation 2, 2.16.0;
	docs/Environment-Ambience-Concepts.md)

	The two layers on top of the soundscape's bed (the research's three layers: bed, spot sounds, one-shots).
	Every sound is our own (tools/sfx/ambience.py), played from two uploaded sheets with PlaybackRegion /
	LoopRegion (Config.Ambience.Sheets and Clips). A sheet id of 0 means not uploaded yet: that layer stays silent.

	Spot sounds: a part (or attachment) tagged NHAmbientSound:<Kind> plays that kind's loop in 3D
	(Config.Ambience.Spots: Clock, Radiator, Vending, Candles, Tap, Tube, Fire). Only the nearest SpotMax within
	their own Range of you play; the rest are switched off (so a hall of clocks costs nothing). Each starts at a
	random point in its loop so two clocks never tick together.

	One-shots: every Gap seconds (random, Config.Ambience.OneShotGap) one sound from the current bed's list
	(Config.Ambience.OneShots[Bed].Day / Night, the soundscape's bed and time) plays somewhere around you, by its
	distance band: Close and Medium are 3D at a random spot that distance away, Far and Sky play flat and quiet
	(they're already mixed far). Each play varies pitch by ±5% and level by ±2 dB, never repeats one of the last
	NoRepeat, and at most OneShotMax play at once. None in the main menu; none while combat-tagged.
	Through the mixer: Spot and OneShot groups (Controllers.World.AmbienceMix), so cutscenes and fights duck them.
	Status for testing: Shared.Status(). Shared.PlayNow(Clip) plays one now (testing).
]]
local CollectionService = game:GetService(`CollectionService`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)

local Config = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`Ambience`))

local Player = Players.LocalPlayer
local Shared = {}
local Local = {}
local TAG = `NHAmbientSound:`

local Spots = {} :: { [Instance]: { Kind: string, Sound: Sound? } }
local Recent = {} :: { string }
local Playing = 0
local Played = 0
local LastClip = nil :: string?
local Rng = Random.new()

function Local.Mix(Layer: string): SoundGroup?
	local M = script.Parent:FindFirstChild(`AmbienceMix`)
	if not M then return nil end
	local Ok, G = pcall(function() return require(M).Group(Layer) end)
	return if Ok then G else nil
end

function Local.Sheet(Clip: string): (string?, any)
	local C = Config.Clips[Clip]
	local Id = C and Config.Sheets[C.Sheet]
	if not C or not Id or Id == 0 then return nil, nil end
	return `rbxassetid://{Id}`, C
end

-- a sound playing one clip of a sheet
function Local.ClipSound(Clip: string): Sound?
	local Id, C = Local.Sheet(Clip)
	if not Id then return nil end
	local S = Instance.new(`Sound`)
	S.Name = `NHAmb_{Clip}`
	S.SoundId = Id
	S.PlaybackRegionsEnabled = true
	S.PlaybackRegion = NumberRange.new(C.Start, C.Start + C.Length)
	if C.Loop then
		S.LoopRegion = NumberRange.new(C.Start, C.Start + C.Length)
		S.Looped = true
	end
	S.RollOffMode = Enum.RollOffMode.InverseTapered
	return S
end

function Local.Pos(): Vector3?
	local Cam = workspace.CurrentCamera
	return Cam and Cam.CFrame.Position
end

function Local.Busy(): boolean
	if Player:GetAttribute(`InMainMenu`) == true then return true end
	local Until = Player:GetAttribute(`CombatTagUntil`)
	return typeof(Until) == `number` and Until > workspace:GetServerTimeNow()
end

---| spot sounds |---

function Local.SpotPos(I: Instance): Vector3?
	if I:IsA(`BasePart`) then return I.Position end
	if I:IsA(`Attachment`) then return I.WorldPosition end
	if I:IsA(`Model`) then return I:GetPivot().Position end
	return nil
end

function Local.AddSpot(I: Instance, Kind: string)
	if not Config.Spots[Kind] or Spots[I] then return end
	Spots[I] = { Kind = Kind; Sound = nil }
end

function Local.RemoveSpot(I: Instance)
	local S = Spots[I]
	if S and S.Sound then S.Sound:Destroy() end
	Spots[I] = nil
end

function Local.StopSpot(S)
	if S.Sound then S.Sound:Destroy() S.Sound = nil end
end

function Local.StartSpot(I: Instance, S)
	local Def = Config.Spots[S.Kind]
	local Snd = Local.ClipSound(Def.Clip)
	if not Snd then return end
	Snd.Volume = Def.Volume
	Snd.RollOffMinDistance = Def.Min or 4
	Snd.RollOffMaxDistance = Def.Range
	Snd.SoundGroup = Local.Mix(`Spot`)
	local Holder = I
	if I:IsA(`Model`) then Holder = I.PrimaryPart or I:FindFirstChildWhichIsA(`BasePart`, true) or I end
	Snd.Parent = Holder
	local C = Config.Clips[Def.Clip]
	Snd.TimePosition = C.Start + Rng:NextNumber(0, C.Length * 0.95)
	Snd:Play()
	S.Sound = Snd
end

function Local.UpdateSpots()
	local P = Local.Pos()
	if not P or Player:GetAttribute(`InMainMenu`) == true then
		for _, S in Spots do Local.StopSpot(S) end
		return
	end
	local Near = {}
	for I, S in Spots do
		local Q = I.Parent and Local.SpotPos(I)
		local D = Q and (Q - P).Magnitude
		if D and D <= Config.Spots[S.Kind].Range then
			table.insert(Near, { I = I; S = S; D = D })
		else
			Local.StopSpot(S)
		end
	end
	table.sort(Near, function(A, B) return A.D < B.D end)
	for N, E in Near do
		if N <= Config.SpotMax then
			if not E.S.Sound or not E.S.Sound.Parent then Local.StartSpot(E.I, E.S) end
		else
			Local.StopSpot(E.S)
		end
	end
end

function Local.WatchTags()
	for Kind in Config.Spots do
		local Tag = TAG .. Kind
		CollectionService:GetInstanceAddedSignal(Tag):Connect(function(I) Local.AddSpot(I, Kind) end)
		CollectionService:GetInstanceRemovedSignal(Tag):Connect(Local.RemoveSpot)
		for _, I in CollectionService:GetTagged(Tag) do Local.AddSpot(I, Kind) end
	end
end

---| one-shots |---

function Local.Bed(): (string?, boolean)
	local M = script.Parent:FindFirstChild(`Soundscape`)
	if not M then return nil, false end
	local Ok, S = pcall(function() return require(M).Status() end)
	if not Ok or not S or type(S.Playing) ~= `string` then return nil, false end
	local Bed, Time = string.match(S.Playing, `^(%w+):(%w+)$`)
	return Bed, Time == `Night`
end

function Local.Pick(List): any?
	local Choices = {}
	for _, E in List do
		if not table.find(Recent, E.Clip) then table.insert(Choices, E) end
	end
	if #Choices == 0 then Choices = List end
	if #Choices == 0 then return nil end
	return Choices[Rng:NextInteger(1, #Choices)]
end

function Local.Play(E): boolean
	local Snd = Local.ClipSound(E.Clip)
	local P = Local.Pos()
	if not Snd or not P then return false end
	local Band = Config.Bands[E.Band or `Medium`] or Config.Bands.Medium
	Snd.Volume = (E.Volume or 0.3) * (Band.Gain or 1) * 10 ^ (Rng:NextNumber(-2, 2) / 20)
	Snd.PlaybackSpeed = 1 + Rng:NextNumber(-0.05, 0.05)
	Snd.SoundGroup = Local.Mix(`OneShot`)
	local Holder: Instance
	if Band.Flat then
		Holder = workspace.CurrentCamera or workspace -- flat: far and sky sounds are already mixed far away
		Snd.RollOffMaxDistance = 100000
	else
		local A = Instance.new(`Attachment`)
		A.Name = `NHAmbOneShot`
		local Ang = Rng:NextNumber(0, math.pi * 2)
		local Dist = Rng:NextNumber(Band.Min, Band.Max)
		A.WorldPosition = P + Vector3.new(math.cos(Ang) * Dist, Rng:NextNumber(-1, 5), math.sin(Ang) * Dist)
		A.Parent = workspace.Terrain
		A.WorldPosition = P + Vector3.new(math.cos(Ang) * Dist, Rng:NextNumber(-1, 5), math.sin(Ang) * Dist)
		Snd.RollOffMinDistance = Band.Min
		Snd.RollOffMaxDistance = Band.Max * 3
		Holder = A
	end
	Snd.Parent = Holder
	Snd:Play()
	Playing += 1
	Played += 1
	LastClip = E.Clip
	table.insert(Recent, E.Clip)
	while #Recent > Config.NoRepeat do table.remove(Recent, 1) end
	local C = Config.Clips[E.Clip]
	task.delay(C.Length / Snd.PlaybackSpeed + 0.3, function()
		Playing -= 1
		if Holder:IsA(`Attachment`) then Holder:Destroy() else Snd:Destroy() end
	end)
	return true
end

function Local.OneShotLoop()
	while true do
		local G = Config.OneShotGap
		task.wait(Rng:NextNumber(G[1], G[2]))
		if not Local.Busy() and Playing < Config.OneShotMax and ReplicatedStorage:GetAttribute(`NHOneShotsOff`) ~= true then
			local Bed, Night = Local.Bed()
			local Set = Bed and Config.OneShots[Bed]
			local List = Set and (if Night then Set.Night else Set.Day)
			local E = List and Local.Pick(List)
			if E then Local.Play(E) end
		end
	end
end

---| api |---

function Shared.OnStart()
	Local.WatchTags()
	local Acc = 0
	RunService.Heartbeat:Connect(function(Dt)
		Acc += Dt
		if Acc < 0.5 then return end
		Acc = 0
		Local.UpdateSpots()
	end)
	task.spawn(Local.OneShotLoop)
end

function Shared.PlayNow(Clip: string, Band: string?): boolean
	return Local.Play({ Clip = Clip; Band = Band or `Close`; Volume = 0.5 })
end

function Shared.Status()
	local Live, Total = 0, 0
	for _, S in Spots do
		Total += 1
		if S.Sound and S.Sound.Parent then Live += 1 end
	end
	local Bed, Night = Local.Bed()
	return { Spots = Total; SpotsPlaying = Live; OneShotsPlaying = Playing; OneShotsPlayed = Played; Last = LastClip;
		Bed = Bed; Night = Night; Sheets = Config.Sheets }
end

return Shared
