--[[
	Lunch trays (shared). ReplicatedStorage.Config.Tray                     (props batch 54, 2026-11-12)
	Server: Services.Features.Tray. Client: Controllers.World.TrayFx.

	A lunch-tray meal (Config.Items.Lunch, the nine trays) is carried in both hands: equipping one poses both shoulders
	(their Motor6D C0, like the kit's holds) and welds the tray to the torso in front of the stomach, so the arms can move
	without the tray following one hand. TrayFx keeps the posed shoulders still against the walk, run and jump clips.
	  Eat        using the meal plays EatStand (the left hand keeps the tray, the right eats), or EatSit while seated
	  Sit        sitting down with a tray plays SitDown and sets it on the table in front (else on the lap); StandUp
	  Queue      standing still with a tray for IdleAfter seconds plays QueueIdle (looped) until you move
	  Spill      a hit (Spill.Damage health or more), being knocked down or ragdolled, or going down spills it:
	             Spill plays, the tray tumbles away and one is lost
	  Return     a part tagged NHTrayReturn gets a "Return tray" prompt: Return plays and the tray is put away
	  Grimace    items listed in Grimace (the mystery meat loaf) get a sniff and a grimace before the bite
	Clips are R6 KeyframeSequences in ServerStorage.NHTrayAnims (tools/tray/build_tray_anims.luau), published under the
	group; their ids are in Anims. A clip with no id (0) plays from there in Studio only; a live server skips it.
]]
local Tray = {}

Tray.Items = {
	KatsuCurry = true; ShoyuRamen = true; KaraageSet = true; MackerelSet = true; Omurice = true;
	WitchingStew = true; ShepherdsPie = true; PumpkinGratin = true; RavensRoast = true;
}
Tray.Grimace = { MeatLoaf = true }

-- the carry (fitted 2026-11-12 on a 0.9-scale R6 rig, the hands on the rims of the 1.97-wide tray): each shoulder's C0
-- turned from rest by { pitch forward, yaw inward } degrees; Offset is the tray's bottom centre in the torso's space for a
-- standard (2-tall) torso, scaled with the torso, its front (-Z) forward; Lap is the same with no table to set it on
Tray.Hold = { R = { 56, 20 }; L = { 56, 20 }; Offset = Vector3.new(0, -0.33, -1.33) }
Tray.Lap = Vector3.new(0, -0.5, -1.2)
Tray.TableReach = 2.6       -- how far in front of the seated torso a table top can be

-- published by the owner under the group (2026-11-12)
Tray.Anims = {
	EatStand = 137993046372635; EatSit = 128651307411808; Spill = 96358550026771; QueueIdle = 106349864053721;
	SitDown = 76779786863920; StandUp = 101237220265587; Return = 119806409148779; Grimace = 88611619309024;
}

Tray.Spill = { Damage = 3; Cooldown = 2 }
Tray.IdleAfter = 1.5

return Tray
