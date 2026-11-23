-- idcheck (phase6-strafes, Client VM, Play): every published gesture id (Config.Gestures Id / Ids[bucket]) and the two square strafes
-- (Config.Locomotion.Ids) load from group 15981569 with Length > 0, matching the baked Len within 0.05 s and the Loop flag.
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local G = require(RS.Config.Gestures)
local L = require(RS.Config.Locomotion)
local Hum = Players.LocalPlayer.Character:WaitForChild("Humanoid")
local Animator = Hum:WaitForChild("Animator")
local Fails, N, Rows = {}, 0, {}
local function probe(name, id, len, loop)
	N += 1
	if not id or id == 0 then table.insert(Fails, name .. " id 0") return end
	local A = Instance.new("Animation"); A.AnimationId = "rbxassetid://" .. id
	local ok, T = pcall(function() return Animator:LoadAnimation(A) end)
	if not ok or not T then table.insert(Fails, name .. " load failed " .. tostring(T)) return end
	local t0 = os.clock()
	while T.Length == 0 and os.clock() - t0 < 8 do task.wait(0.05) end
	if T.Length == 0 then table.insert(Fails, name .. " Length 0 (not loaded / no access)")
	else
		if len and math.abs(T.Length - len) > 0.05 then table.insert(Fails, string.format("%s len %.3f want %.3f", name, T.Length, len)) end
		if loop ~= nil and T.Looped ~= loop then table.insert(Fails, name .. " looped " .. tostring(T.Looped)) end
	end
	T:Destroy(); A:Destroy()
end
for base, c in G.Clips do
	if c.Ids then
		for b, id in c.Ids do probe(base .. "_" .. b, id, c.Len, c.Loop) end
	else
		probe(base, c.Id, c.Len, c.Loop)
	end
end
probe("StrafeLeftSquare", L.Ids.StrafeLeftSquare, nil, true)
probe("StrafeRightSquare", L.Ids.StrafeRightSquare, nil, true)
return (#Fails == 0 and "IDCHECK OK " or "IDCHECK FAIL ") .. N .. " ids\n" .. table.concat(Fails, "\n")
