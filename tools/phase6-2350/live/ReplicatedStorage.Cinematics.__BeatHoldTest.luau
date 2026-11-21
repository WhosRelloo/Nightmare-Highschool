--[[
	__BeatHoldTest (2.35.0, task 8 fix round 1, Hidden). tools/phase6-2350/checks/beatcheck.lua's cut: a 2 s shot, then
	Hold, a 14 s walk-and-talk beat that crouches you and blocks sprinting, then a 2 s closing shot. Its Config Length is
	6 s, so the server's Length + TimeoutPad (11 s) would end it mid-beat if beats were timed (spec §4.3: they aren't).
]]
local Def = { Set = `BusStop`; Seamless = true }
function Def.Build(Ctx)
	local Me = Ctx.Self
	return { start = `Open`;
		segments = {
			Open = { next = `Hold`; shots = {
				{ name = `Open`; dur = 2; subject = Me; noise = `calm`;
				  camera = { frame = { size = `MS`; yaw = 160; pitch = 6; lens = 35 } } };
			} };
			Hold = { beat = { rig = `Follow`; frame = { low = true }; move = { crouch = true; sprint = false };
				lines = { { on = `start`; who = `You`; text = `Quiet. Very quiet.` } };
				ends = { on = `t:14`; next = `Close` } } };
			Close = { shots = {
				{ name = `Close`; dur = 2; subject = Me; noise = `calm`;
				  camera = { frame = { size = `MS`; yaw = 170; pitch = 8; lens = 35 } } };
			} };
		} }
end
return Def
