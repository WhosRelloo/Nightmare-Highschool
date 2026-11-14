
---| Services |---

local RunService = game:GetService(`RunService`)
local PacketStorage = script:WaitForChild(`PacketStorage`)

---| Packets |---

local Packet = require(script.Parent.Packets.Packet)
local UnPackets = {

	--| Combat |--

	Feint = Packet(`Feint`);
	Slide = Packet(`Slide`);
	Crouch = Packet(`Crouch`, Packet.Actions); -- "Activate" (hold) / "Release" (Services.Player.Crouch)

	M1 = Packet(`M1`, Packet.Boolean8);
	M2 = Packet(`M2`, Packet.Boolean8);

	Uppercut = Packet(`Uppercut`);

	Dodge = Packet(`Dodge`, Packet.MoveVector);
	Sprint = Packet(`Sprint`, Packet.Actions);

	Block = Packet(`Block`, Packet.Actions);
	Equip = Packet(`Equip`);

	Jump = Packet(`Jump`);
	Action = Packet(`Action`, Packet.String);
}

---| Un-Packets Serializer |---

-- Inputs that carry state (press / release) go over a reliable RemoteEvent: a dropped "Release" on an
-- unreliable remote left sprint, block or crouch stuck on (Known bug #13). One-shot presses (attacks,
-- dodge, feint) stay unreliable: a lost packet there is just a missed press.
local RELIABLE = { Sprint = true; Block = true; Crouch = true; Equip = true }
local RATE_LIMIT = 15 -- events per second per player per input (a human can't press faster)
local Recent = setmetatable({}, { __mode = `k` }) :: { [Player]: { [string]: { Start: number, Count: number } } }

for _, Packet: Packet.Packet in UnPackets do

	if RunService:IsServer() then
		local UnPacket = Instance.new(if RELIABLE[Packet.Name] then `RemoteEvent` else `UnreliableRemoteEvent`)
		UnPacket.Name = Packet.Name
		UnPacket.Parent = PacketStorage

		UnPacket.OnServerEvent:Connect(function(Player: Player, ...)
			-- rate limit (Known bug #14): at most RATE_LIMIT events a second per player per input; the rest are dropped
			local Now = os.clock()
			local Seen = Recent[Player]
			if not Seen then Seen = {} Recent[Player] = Seen end
			local Entry = Seen[Packet.Name]
			if not Entry or Now - Entry.Start >= 1 then Entry = { Start = Now; Count = 0 } Seen[Packet.Name] = Entry end
			Entry.Count += 1
			if Entry.Count > RATE_LIMIT then return end
			Packet.OnServerEvent:Fire(
				Player,
				Packet:Deserialize(...)
			)

		end)

		Packet.Fire = function(Packet: Packet.Packet, ...)
			UnPacket:FireAllClients( Packet:Serialize(...) )
		end

		Packet.FireClient = function(Packet: Packet.Packet, Player: Player, ...)
			UnPacket:FireClient(
				Player,
				Packet:Serialize(...)
			)

		end
	else
		local UnPacket = PacketStorage:WaitForChild(Packet.Name)

		UnPacket.OnClientEvent:Connect(function(...)
			Packet.OnClientEvent:Fire( Packet:Deserialize(...) )

		end)

		Packet.Fire = function(Packet: Packet.Packet, ...)
			UnPacket:FireServer( Packet:Serialize(...) )

		end

	end
end

return UnPackets
