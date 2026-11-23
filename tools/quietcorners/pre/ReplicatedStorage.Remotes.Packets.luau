
---| Services |---

local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

---| Modules |---

local UpdateState = require(ReplicatedStorage.Functions.UpdateState)
local Packet = require(script.Packet)

---| Type Annotation |---

type		Argumants = { Distance: number? } & any
export type Packet = Packet.Packet

---| Packets |---

local Packets = {

	--| Data Packets |--

	Start = Packet(`Start`);

	SetState = Packet(`SetState`, Packet.Any :: UpdateState.PlayerData);
	UpdateState = Packet(`UpdateState`, Packet.Any :: UpdateState.StateAction);

	--| Combat Packets |--

	Replicate = Packet(`Replicate`, Packet.Characters, Packet.Characters, Packet.Any :: Argumants);
	AirCombat = Packet(`AirCombat`, Packet.Any):Response(Packet.Boolean);

	--| Downed Packets (reliable: one-shot requests) |--

	Carry = Packet(`Carry`);
	Grip = Packet(`Grip`);

	--| UI Packets |--

	Notify = Packet(`Notify`, Packet.Any);

	--| Class activities (reliable) |--

	ActivityEvent = Packet(`ActivityEvent`, Packet.Any);   -- server -> client: Start / Update / Result
	ActivityAction = Packet(`ActivityAction`, Packet.Any); -- client -> server: { Id, Action, Data }

	--| Dialogue + social (reliable) |--

	DialogueEvent = Packet(`DialogueEvent`, Packet.Any);   -- server -> client: Node / Close
	DialogueAction = Packet(`DialogueAction`, Packet.Any); -- client -> server: { Id, Choice } or { Id, Close = true }
	SocialAction = Packet(`SocialAction`, Packet.Any);     -- client -> server: { Action = "EquipTitle", Title }
	QuestAction = Packet(`QuestAction`, Packet.Any);       -- client -> server: Track / Abandon / Link / Deduce

	--| Others Packets |--

	Loaded = game:IsLoaded();
}

Packets.AirCombat.ResponseTimeout = 15

return Packets
