--[[
	LagComp (server): combat concept 13 (2.13.0). Lag-compensated hits.

	A player's hit is judged against where the target was on that player's screen, not only where the server has it
	now. Every Heartbeat this records the root CFrame of every character in workspace.Live and every player's
	character (about 0.6 s of history). When a player's hitbox fires (HitBox:Go / GetCast), targets are also tested
	at their position Rewind seconds ago:
	  * a normal attack: the attacker's screen shows others about INTERP late (Roblox's and chrono's interpolation);
	  * a client-predicted swing (concept 12): the swing started on the attacker's screen a full round trip before the
	    server's hit frame, so the rewind adds the player's ping (Player:GetNetworkPing() is the round trip).
	The rewind is capped at MAX_REWIND, so a laggy player can't reach back further than that. NPC attackers aren't
	rewound. The current-position check still runs, so a hit counts if it lands now or on the attacker's screen.

	Off switch: ReplicatedStorage attribute NHLagCompOff = true.
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)

local HISTORY = 0.6 -- seconds kept per character
local INTERP = 0.1 -- what others' interpolation delays them by on a client (default replication ~0.1, chrono 0.08-0.1)
local MAX_REWIND = 0.3 -- the most a hit may reach back
-- sample points on an R6 body around its root (head, chest, hips, both sides, legs): a target counts when any is inside
local BODY_POINTS = {
	Vector3.new(0, 1.5, 0), Vector3.new(0, 0, 0), Vector3.new(0, -1, 0), Vector3.new(0, -2.5, 0),
	Vector3.new(1, 0.5, 0), Vector3.new(-1, 0.5, 0), Vector3.new(0.5, -2, 0), Vector3.new(-0.5, -2, 0),
}

local History = {} :: { [Model]: { { T: number, CF: CFrame } } }

local LagComp = {}

function LagComp.On(): boolean
	return ReplicatedStorage:GetAttribute(`NHLagCompOff`) ~= true
end

local function Track(Model: Model, Now: number)
	local Root = Model:FindFirstChild(`HumanoidRootPart`)
	if not (Root and Root:IsA(`BasePart`)) then return end
	local H = History[Model]
	if not H then H = {} History[Model] = H end
	table.insert(H, { T = Now, CF = Root.CFrame })
	while #H > 2 and Now - H[1].T > HISTORY do table.remove(H, 1) end
end

local Started = false
local function Start()
	if Started then return end
	Started = true
	RunService.Heartbeat:Connect(function()
		local Now = os.clock()
		local Live = workspace:FindFirstChild(`Live`)
		if Live then
			for _, M in Live:GetChildren() do
				if M:IsA(`Model`) then Track(M, Now) end
			end
		end
		for _, P in Players:GetPlayers() do
			local C = P.Character
			if C and not (Live and C.Parent == Live) then Track(C, Now) end
		end
		for M in History do
			if not M.Parent then History[M] = nil end
		end
	end)
end
Start()

-- the root CFrame Model had Ago seconds back (interpolated between recorded frames), or nil without history
function LagComp.CFrameAgo(Model: Model, Ago: number): CFrame?
	local H = History[Model]
	if not H or #H == 0 then return nil end
	local T = os.clock() - Ago
	if T <= H[1].T then return H[1].CF end
	for I = #H, 1, -1 do
		local A = H[I]
		if A.T <= T then
			local B = H[I + 1]
			if not B then return A.CF end
			return A.CF:Lerp(B.CF, (T - A.T) / math.max(B.T - A.T, 1e-4))
		end
	end
	return H[#H].CF
end

-- how far back to judge Attacker's hits (0 for NPCs or when off). Predicted: the swing was client-predicted.
function LagComp.Rewind(Attacker: Model?, Predicted: boolean?): number
	if not (Attacker and LagComp.On()) then return 0 end
	local Player = Players:GetPlayerFromCharacter(Attacker)
	if not Player then return 0 end
	local Ping = 0
	pcall(function() Ping = Player:GetNetworkPing() end)
	return math.clamp(INTERP + (if Predicted then Ping else 0), 0, MAX_REWIND)
end

local function Inside(Box: CFrame, Half: Vector3, Point: Vector3): boolean
	local L = Box:PointToObjectSpace(Point)
	return math.abs(L.X) <= Half.X and math.abs(L.Y) <= Half.Y and math.abs(L.Z) <= Half.Z
end

local function Excluded(Params: OverlapParams?, Model: Model): boolean
	if not Params then return false end
	if Params.FilterType ~= Enum.RaycastFilterType.Exclude then return true end -- Include lists aren't rewound
	for _, I in Params.FilterDescendantsInstances do
		if Model == I or Model:IsDescendantOf(I) then return true end
	end
	return false
end

-- characters whose body was inside the box (CFrame Box, Size) Ago seconds back, skipping Skip[model] and Params' excludes.
-- Returns { {Model, Root, Humanoid} }.
function LagComp.HitsAgo(Box: CFrame, Size: Vector3, Ago: number, Params: OverlapParams?, Skip: { [Model]: boolean }?)
	local Out = {}
	if Ago <= 0 then return Out end
	local Half = Size / 2
	local Reach = Half.Magnitude + 6
	for Model in History do
		if (Skip and Skip[Model]) or Excluded(Params, Model) then continue end
		local Hum = Model:FindFirstChildOfClass(`Humanoid`)
		local Root = Model:FindFirstChild(`HumanoidRootPart`)
		if not (Hum and Root) or Hum.Health <= 0 then continue end
		local Then = LagComp.CFrameAgo(Model, Ago)
		if not Then or (Then.Position - Box.Position).Magnitude > Reach then continue end
		for _, P in BODY_POINTS do
			if Inside(Box, Half, Then:PointToWorldSpace(P)) then
				table.insert(Out, { Model = Model, Root = Root, Humanoid = Hum })
				break
			end
		end
	end
	return Out
end

return LagComp
