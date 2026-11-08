local SS = game:GetService("SerializationService")
local HS = game:GetService("HttpService")
local F = game.ServerStorage._RacePack
local names = {} for _, m in ipairs(F:GetChildren()) do table.insert(names, m.Name) end table.sort(names)
local parts = {} for _, n in ipairs(names) do table.insert(parts, F[n].Source) end
local j = table.concat(parts)
assert(#j == 503988, "length " .. #j)
local buf = HS:JSONDecode(j)
local inst = SS:DeserializeInstancesAsync(buf)
local SSS, PS = game.ServerScriptService, game.StarterPlayer.StarterPlayerScripts
local dest = {
  NHRaceCosmetics = { game.ServerStorage, true },
  NHLineage = { SSS, true },
  RaceCosmetics = { SSS.Services.Player, false },
  TailSway = { PS.Controllers.Character, false },
  Bloodline = { PS.Controllers.Gui, false },
}
local out = {}
-- refuse if any name is taken
for _, i in ipairs(inst) do
  local d = dest[i.Name]
  local parent = d and d[1]
  if i.Name == "NightSight" then parent = i:IsA("ModuleScript") and (i.Source:find("Night sight %(server%)") and SSS.Services.Features or PS.Controllers.Character) end
  assert(parent, "no destination for " .. i.Name)
  assert(not parent:FindFirstChild(i.Name), i.Name .. " already exists in " .. parent:GetFullName())
end
for _, i in ipairs(inst) do
  local d = dest[i.Name]
  local parent = d and d[1]
  local tag = d and d[2]
  if i.Name == "NightSight" then parent = i.Source:find("Night sight %(server%)") and SSS.Services.Features or PS.Controllers.Character end
  if tag then i:SetAttribute("NHCore", true) end
  i.Parent = parent
  table.insert(out, i:GetFullName() .. (i:IsA("LuaSourceContainer") and (" " .. #i.Source) or (" " .. #i:GetDescendants() .. " desc")))
end
F:Destroy()
return table.concat(out, "\n")
