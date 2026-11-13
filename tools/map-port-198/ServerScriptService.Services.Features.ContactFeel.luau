--[[
	ContactFeel (server). Services.Features.ContactFeel  (contact feel, 2026-11-12; client: Controllers.World.ContactFeel)

	The client feels a bump into a background student on its own character and reports it here:
	ReplicatedStorage.NHContact.Impact:FireServer(StudentModel, Speed, Direction). A report counts only when:
	  * the model is a live brain student (NHBrain, in the workspace, alive, not down);
	  * the player is alive, not down, and their root is within REACH of the student (flat). Their position here lags
	    what their client saw (replication: measured 3.5 studs behind at 13 studs/s in Studio), so a moving player
	    gets LAG seconds (plus their ping) of the speed the server itself saw on top, as long as the student is ahead
	    of them along the way they were going. That speed comes from the client's replicated velocity, so it is
	    capped by the server's own WalkSpeed for them (x 1.1 + 2);
	  * they've sent no more than RATE reports in the last second;
	  * Speed and Direction are sane numbers (Direction is a unit vector: longer than 2 is refused). Speed is cut to what the server itself saw them move at lately
	    (StudentBrain.Nudges.TopSpeed, over its 0.6 s ram memory) plus SLACK.
	Anything else is dropped without a word. A good report goes to StudentBrain.Contact, which remembers the hit and
	makes the student react to how hard it was.
]]

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

-- (Map place, 1.98.0) the Map's own students: Features.MapStudents and its Nudges
local Brain = require(ServerScriptService.Services.Features.MapStudents)
local Nudges = require(ServerScriptService.Services.Features.MapStudents.Nudges)

local Shared = {}
local Local = {}

local REACH = 4        -- studs (flat) between the roots
local LAG = 0.35       -- s of the server-seen speed added to REACH, plus the player's ping (up to MAX_PING)
local MAX_PING = 0.4   -- s
local AHEAD = 0.3      -- past REACH, the student must be this far ahead (dot) along the reported direction
local RATE = 4         -- reports a second
local SLACK = 2        -- studs/s over the server's own top speed
local MAX_SPEED = 80   -- nobody runs faster than this

local Sent = {} :: { [Player]: { number } }

local function flat(V: Vector3): Vector3
	return Vector3.new(V.X, 0, V.Z)
end

local function finite(N: number): boolean
	return N == N and N > -math.huge and N < math.huge
end

local function down(M: Model, H: Humanoid?): boolean
	return not H or H.Health <= 0 or H:GetAttribute(`Downed`) == true or M:GetAttribute(`Downed`) == true
		or M:GetAttribute(`DownedUntil`) ~= nil
end

function Local.OnImpact(P: Player, Model: any, Speed: any, Dir: any)
	if typeof(Model) ~= `Instance` or not Model:IsA(`Model`) or Model:GetAttribute(`NHBrain`) ~= true then return end
	if not Model:IsDescendantOf(workspace) then return end
	if typeof(Speed) ~= `number` or not finite(Speed) or typeof(Dir) ~= `Vector3` then return end
	if not (finite(Dir.X) and finite(Dir.Y) and finite(Dir.Z)) or Dir.Magnitude > 2 then return end

	local Now = os.clock()
	local List = Sent[P] or {}
	Sent[P] = List
	while List[1] and Now - List[1] > 1 do table.remove(List, 1) end
	if #List >= RATE then return end
	table.insert(List, Now)

	local Char = P.Character
	local Hum = Char and Char:FindFirstChildOfClass(`Humanoid`)
	local Root = Char and Char:FindFirstChild(`HumanoidRootPart`)
	if not (Char and Root and Root:IsA(`BasePart`)) or down(Char, Hum) then return end
	local SRoot = Model:FindFirstChild(`HumanoidRootPart`)
	if not (SRoot and SRoot:IsA(`BasePart`)) or down(Model, Model:FindFirstChildOfClass(`Humanoid`)) then return end

	Speed = math.clamp(Speed, 0, MAX_SPEED)
	-- the replicated velocity is the client's word: no faster than the server lets them walk
	local Allowed = (if Hum then Hum.WalkSpeed else 16) * 1.1 + 2
	local Seen = math.min(math.max(Nudges.TopSpeed(P), flat(Root.AssemblyLinearVelocity).Magnitude), Allowed, MAX_SPEED)
	Speed = math.min(Speed, Seen + SLACK)
	local Ping = 0
	pcall(function() Ping = math.clamp(P:GetNetworkPing(), 0, MAX_PING) end)
	local Rel = flat(SRoot.Position - Root.Position)
	if Rel.Magnitude > REACH + Seen * (LAG + Ping) then return end
	local Way = flat(Dir)
	if Rel.Magnitude > REACH and (Way.Magnitude < 0.1 or Rel.Unit:Dot(Way.Unit) < AHEAD) then return end
	if math.abs(Root.Position.Y - SRoot.Position.Y) > 5 then return end

	Brain.Contact(P, Model, Speed, flat(Dir)) -- MapStudents.Contact
end

function Shared.OnStart()
	local F = ReplicatedStorage:FindFirstChild(`NHContact`) or Instance.new(`Folder`)
	F.Name = `NHContact`
	local R = F:FindFirstChild(`Impact`) or Instance.new(`RemoteEvent`)
	R.Name = `Impact`
	R.Parent = F
	F.Parent = ReplicatedStorage
	R.OnServerEvent:Connect(function(P, Model, Speed, Dir)
		local Ok, Err = pcall(Local.OnImpact, P, Model, Speed, Dir)
		if not Ok then warn(`[ContactFeel] {Err}`) end
	end)
	Players.PlayerRemoving:Connect(function(P) Sent[P] = nil end)
end

return Shared
