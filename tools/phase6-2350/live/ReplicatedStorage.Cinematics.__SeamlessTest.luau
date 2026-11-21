--[[
	__SeamlessTest (2.35.0, Hidden). The camera seam check's cut (tools/phase6-2350/checks/camcheck.lua): Main is 8 s, two
	shots staged near the player, then one back to a gameplay-like angle; the player's own character is the actor. Then
	Walk, a 4 s walk-and-talk beat on the Follow rig (spec §3): controls on, the camera hands over from Main's last shot.
	Then Close, one 2.5 s shot the beat glides out into (the Garden-to-Fence path: shots, beat, shots). The segments form
	(doc 12 §3) without a prompt graph.
]]
local Def = { Set = `BusStop`; Seamless = true }
function Def.Build(Ctx)
	local Me = Ctx.Self
	-- (fix round 1) a grade, so camcheck sees it ease in over the glide and out over the blend
	local Main = {
		{ name = `Over shoulder`; dur = 3; subject = Me; noise = `calm`; dof = true;
		  camera = { frame = { size = `MS`; yaw = 160; pitch = 6; lens = 35 }; to = { size = `MCU` }; ease = `inout` } };
		{ name = `Side`; dur = 3; subject = Me; noise = `tense`; dof = true;
		  camera = { frame = { size = `MCU`; yaw = 110; pitch = 2; lens = 50 } } };
		{ name = `Back to you`; dur = 2; subject = Me; noise = `calm`;
		  camera = { frame = { size = `MS`; yaw = 180; pitch = 10; lens = 35 } } };
	}
	return { grade = { contrast = 0.15; saturation = -0.3; brightness = -0.03; tint = { 0.92, 0.95, 1 }; bloom = { intensity = 0.6 };
		exposure = -0.25 };
		start = `Main`;
		segments = {
			Main = { shots = Main; next = `Walk` };
			Walk = { beat = { rig = `Follow`; lines = { { on = `start`; who = `You`; text = `Test.` } }; ends = { on = `t:4`; next = `Close` } } };
			Close = { shots = {
				{ name = `Close`; dur = 2.5; subject = Me; noise = `calm`;
				  camera = { frame = { size = `MS`; yaw = 170; pitch = 8; lens = 35 } } };
			} };
		} }
end
return Def
