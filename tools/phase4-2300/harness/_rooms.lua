local Sched = require(game.ServerScriptService.Services.Features.Schedules)
local c = {}
for _, R in Sched.Debug() do local a = tostring(R.Activity or "-") c[a] = (c[a] or 0) + 1 end
local t = {} for k, v in c do table.insert(t, k .. " " .. v) end table.sort(t)
return table.concat(t, ", ")
