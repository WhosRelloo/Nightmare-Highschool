-- Accessories (Kit B) for Services.Features.Fx: a staff tool used stamps NHAdminFlare (server time) on the staff
-- member's character, so the regalia's crimson sigil halo flares for a moment (Controllers.Character.AccessoryFx).
-- Set in VeilMove: when staff travel as their flock (Opts.Admin), and when they move a student (Opts.By). An invisible
-- staff member's move shows nothing, so no flare there. NH Combat Test, Edit (applied 2026-11-11). Re-runnable.
local M = game.ServerScriptService.Services.Features.Fx
local S = M.Source
if string.find(S, "NHAdminFlare", 1, true) then
	return "already patched"
end
local report = {}
local function once(a, b, label)
	local i = string.find(S, a, 1, true)
	assert(i, "not found: " .. label)
	assert(not string.find(S, a, i + 1, true), "found twice: " .. label)
	S = string.sub(S, 1, i - 1) .. b .. string.sub(S, i + #a)
	table.insert(report, "ok " .. label)
end
once([=[--                  member's small swirl of birds ("TpEscort")
]=], [=[--                  member's small swirl of birds ("TpEscort")
-- A staff tool used (Admin, or By a staff member) stamps NHAdminFlare (server time) on that staff member's character:
-- the regalia's crimson sigil halo flares for a moment (Controllers.Character.AccessoryFx).
]=], "doc")
once([=[		if Char:GetAttribute(`NHInvisible`) == true then -- invisible staff: no tell-tale effect at all]=],
	[=[		if Char:GetAttribute(`NHInvisible`) == true then -- invisible staff: no tell-tale effect at all (no flare either)]=], "invisible")
once([=[		fireEnds(Root.Position, Target.Position, C.Radius or 150, `TpFlock`,]=], [=[		Char:SetAttribute(`NHAdminFlare`, workspace:GetServerTimeNow())
		fireEnds(Root.Position, Target.Position, C.Radius or 150, `TpFlock`,]=], "flock")
once([=[	if EStyle and not (By.Character and By.Character:GetAttribute(`NHInvisible`) == true) then
]=], [=[	if EStyle and not (By.Character and By.Character:GetAttribute(`NHInvisible`) == true) then
		if By.Character then By.Character:SetAttribute(`NHAdminFlare`, workspace:GetServerTimeNow()) end
]=], "escort")
game:GetService("ScriptEditorService"):UpdateSourceAsync(M, function() return S end)
return table.concat(report, "\n")
