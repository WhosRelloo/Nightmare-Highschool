local inst = game
for part in string.gmatch("ServerScriptService.Services.Social.Pranks", "[^%.]+") do inst = inst:FindFirstChild(part) end
local s = inst.Source
local a = 1 * 25000 + 1
if a > #s then return "<<EOF>>" end
return s:sub(a, a + 24999) .. "<<CHUNK>>"