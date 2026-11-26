-- slots_client_edit (electives Task 3): every server reader of Classes.Periods goes through Classes.For (or IsElectiveSlot).
local Bad = {}
for _, Path in { "StarterPlayer.StarterPlayerScripts.Controllers.Gui.ClockHud", "StarterPlayer.StarterPlayerScripts.Controllers.Gui.Moments", "StarterPlayer.StarterPlayerScripts.Controllers.Gui.Timetable",
		"StarterPlayer.StarterPlayerScripts.Controllers.Gui.Phone", "StarterPlayer.StarterPlayerScripts.Controllers.Gui.KitUi" } do
	local N = game for S in Path:gmatch("[^%.]+") do N = N:FindFirstChild(S) end
	local Src = N.Source
	for Line in Src:gmatch("[^\n]+") do
		if Line:find("Classes.Periods[", 1, true) and not Line:find("-- base", 1, true) then table.insert(Bad, Path .. ": " .. Line) end
	end
	if not (Src:find("Classes.For(", 1, true) or Src:find("Classes.IsElectiveSlot(", 1, true)) then table.insert(Bad, Path .. ": never asks Classes.For") end
	local Ok, Err = loadstring(Src)
	if not Ok then table.insert(Bad, Path .. ": parse: " .. tostring(Err)) end
end
if #Bad > 0 then return "FAIL\n" .. table.concat(Bad, "\n") end
return "PASS slots_client_edit"
