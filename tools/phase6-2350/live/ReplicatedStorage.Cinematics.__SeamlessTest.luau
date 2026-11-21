--[[
	__SeamlessTest (2.35.0, Hidden). The camera seam check's cut (tools/phase6-2350/checks/camcheck.lua): 8 s, two shots
	staged near the player, then one back to a gameplay-like angle; the player's own character is the actor.
]]
local Def = { Set = `BusStop`; Seamless = true }
function Def.Build(Ctx)
	local Me = Ctx.Self
	-- (fix round 1) a grade, so camcheck sees it ease in over the glide and out over the blend
	return { grade = { contrast = 0.15; saturation = -0.3; brightness = -0.03; tint = { 0.92, 0.95, 1 }; bloom = { intensity = 0.6 };
		exposure = -0.25 }; shots = {
		{ name = `Over shoulder`; dur = 3; subject = Me; noise = `calm`; dof = true;
		  camera = { frame = { size = `MS`; yaw = 160; pitch = 6; lens = 35 }; to = { size = `MCU` }; ease = `inout` } };
		{ name = `Side`; dur = 3; subject = Me; noise = `tense`; dof = true;
		  camera = { frame = { size = `MCU`; yaw = 110; pitch = 2; lens = 50 } } };
		{ name = `Back to you`; dur = 2; subject = Me; noise = `calm`;
		  camera = { frame = { size = `MS`; yaw = 180; pitch = 10; lens = 35 } } };
	} }
end
return Def
