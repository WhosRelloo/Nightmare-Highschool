local inst = game
for part in string.gmatch("StarterPlayer.StarterPlayerScripts.Controllers.Gui.CineUI", "[^%.]+") do inst = inst:FindFirstChild(part) end
local s = inst.Source
local a = 2 * 25000 + 1
if a > #s then return "<<EOF>>" end
return s:sub(a, a + 24999) .. "<<CHUNK>>"