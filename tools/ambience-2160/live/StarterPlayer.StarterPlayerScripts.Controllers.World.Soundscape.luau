--[[
	Zone soundscape (client). Controllers.World.Soundscape   VFX catalog P2-3. Data: Config.Ambience.Beds / ZoneBed.

	One ambience bed plays at a time and crossfades (Config.Ambience.Crossfade seconds) when the bed changes:
	  * inside a RoomId zone part (workspace.School.*.Zone, the Archive, the Boiler Yard, a classroom): that zone's bed
	  * in no zone but in the halls (over a Config.Ambience.IndoorFloors floor, or under a roof): Indoor
	  * open sky: Outdoor
	and each bed has a day and a night sound (night from Config.Ambience.NightFrom to NightTo on the school clock).
	Played through the Music & Ambience volume (SoundService.NH_Master.NH_Music). Silent in the main menu.
	Expose a status for testing: Shared.Status().
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local SoundService = game:GetService(`SoundService`)
local TweenService = game:GetService(`TweenService`)

local Config = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`Ambience`))
local SchoolTime = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`SchoolTime`))
local RegionBoxes = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`RegionBoxes`)) -- (2.16.0)

local Player = Players.LocalPlayer
local Shared = {}

local Zones = {} :: { BasePart }
local Current = nil :: { Key: string, Sound: Sound }?
local LastWhere = `-`

local function hour(): number?
	local Clock = ReplicatedStorage:FindFirstChild(`SchoolClock`)
	local Epoch = Clock and Clock:GetAttribute(`Epoch`)
	if not Epoch then return nil end
	local Ok, State = pcall(SchoolTime.GetState, Epoch, workspace:GetServerTimeNow())
	return if Ok and State then State.MinuteOfDay / 60 else nil
end

local function night(): boolean
	local H = hour()
	return H ~= nil and (H >= Config.NightFrom or H < Config.NightTo)
end

-- zone parts stream in and out (StreamingEnabled), so keep the list live instead of reading it once
-- (Config.Ambience.IndoorFloors: the hall floors of the roofless greybox count as indoors)
local Floors = {} :: { BasePart }

local function addZone(D: Instance)
	if not D:IsA(`BasePart`) then return end
	if D:GetAttribute(`RoomId`) then
		if not table.find(Zones, D) then table.insert(Zones, D) end
	elseif D.Parent and Config.IndoorFloors[D.Parent.Name] and not table.find(Floors, D) then
		table.insert(Floors, D)
	end
end

local function removeZone(D: Instance)
	local I = table.find(Zones, D :: any)
	if I then table.remove(Zones, I) end
	I = table.find(Floors, D :: any)
	if I then table.remove(Floors, I) end
end

local function watchZones(School: Instance)
	School.DescendantAdded:Connect(addZone)
	School.DescendantRemoving:Connect(removeZone)
	for _, D in School:GetDescendants() do addZone(D) end
end

local function inBox(Part: BasePart, P: Vector3): boolean
	local L = Part.CFrame:PointToObjectSpace(P)
	local H = Part.Size / 2
	return math.abs(L.X) <= H.X and math.abs(L.Y) <= H.Y + 2 and math.abs(L.Z) <= H.Z
end

local Params = RaycastParams.new()
Params.FilterType = Enum.RaycastFilterType.Exclude

local function where(P: Vector3): string
	for _, Z in Zones do
		if Z.Parent and inBox(Z, P) then
			return Config.ZoneBed[Z:GetAttribute(`RoomId`)] or `Indoor`
		end
	end
	-- (2.16.0) the place's own bed, from its region box (the Map has region boxes, no zone parts)
	local Region = Config.RegionBed and RegionBoxes.At(P)
	if Region and Config.RegionBed[Region] then return Config.RegionBed[Region] end
	for _, F in Floors do
		local L = F.CFrame:PointToObjectSpace(P)
		local H = F.Size / 2
		if math.abs(L.X) <= H.X and math.abs(L.Z) <= H.Z and L.Y >= -1 and L.Y <= Config.IndoorHeight then
			return `Indoor`
		end
	end
	-- anything with a roof over it is indoors too
	local Ignore = { Player.Character }
	local FxFolder = workspace:FindFirstChild(`NHFx`)
	if FxFolder then table.insert(Ignore, FxFolder) end
	Params.FilterDescendantsInstances = Ignore
	local Hit = workspace:Raycast(P + Vector3.new(0, 2, 0), Vector3.new(0, 80, 0), Params)
	return if Hit then `Indoor` else `Outdoor`
end

local function group(): SoundGroup?
	-- (2.16.0) through the ambience mixer's Bed group (Controllers.World.AmbienceMix), so fights duck it
	local Mix = script.Parent:FindFirstChild(`AmbienceMix`)
	if Mix then
		local Ok, G = pcall(function() return require(Mix).Group(`Bed`) end)
		if Ok and G then return G end
	end
	local Master = SoundService:FindFirstChild(`NH_Master`)
	local G = Master and Master:FindFirstChild(`NH_Music`)
	return if G and G:IsA(`SoundGroup`) then G else nil
end

local function fadeOut(S: Sound)
	local T = TweenService:Create(S, TweenInfo.new(Config.Crossfade, Enum.EasingStyle.Sine), { Volume = 0 })
	T.Completed:Connect(function() S:Destroy() end)
	T:Play()
end

local function play(Key: string?)
	if Current and Current.Key == Key then return end
	local BedName, Time = string.match(Key or ``, `^(%w+):(%w+)$`)
	local Bed = BedName and Config.Beds[BedName]
	local Id = Bed and Bed[Time]
	-- same loop (the boiler by day and night, the halls and a classroom): keep it playing, ease to the new level
	if Current and Id and Current.Sound.SoundId == `rbxassetid://{Id}` then
		Current.Key = Key :: string
		TweenService:Create(Current.Sound, TweenInfo.new(Config.Crossfade, Enum.EasingStyle.Sine), { Volume = Bed.Volume }):Play()
		return
	end
	if Current then fadeOut(Current.Sound) Current = nil end
	if not Id then return end
	local S = Instance.new(`Sound`)
	S.Name = `NHAmbience{BedName}{Time}`
	S.SoundId = `rbxassetid://{Id}`
	S.Looped = true
	S.Volume = 0
	S.SoundGroup = group()
	S.Parent = SoundService
	S:Play()
	TweenService:Create(S, TweenInfo.new(Config.Crossfade, Enum.EasingStyle.Sine), { Volume = Bed.Volume }):Play()
	Current = { Key = Key, Sound = S }
end

function Shared.OnStart()
	task.spawn(function()
		local School = workspace:WaitForChild(`School`, 60)
		if School then watchZones(School) end
	end)
	local Acc = 0
	RunService.Heartbeat:Connect(function(Dt)
		Acc += Dt
		if Acc < 0.75 then return end
		Acc = 0
		if Player:GetAttribute(`InMainMenu`) == true then play(nil) LastWhere = `menu` return end
		local Cam = workspace.CurrentCamera
		local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
		local P = (Root and Root.Position) or (Cam and Cam.CFrame.Position)
		if not P then return end
		LastWhere = where(P)
		play(`{LastWhere}:{if night() then `Night` else `Day`}`)
		if Current then
			local G = group()
			if G and Current.Sound.SoundGroup ~= G then Current.Sound.SoundGroup = G end
		end
	end)
end

function Shared.Status()
	return { Where = LastWhere; Playing = Current and Current.Key; SoundId = Current and Current.Sound.SoundId;
		Loaded = Current and Current.Sound.IsLoaded; Volume = Current and Current.Sound.Volume }
end

return Shared
