-- watchcheck (phase6-strafes T5 round C, Server, Play): a live Gymnasium match draws Athletes onto the bleachers, cheering.
local B = game.ServerStorage:FindFirstChild("NHGestureProbe")
if not B then return "FAIL no NHGestureProbe" end
local H = game:GetService("HttpService")
local Fails, Notes = {}, {}
local S = B:Invoke("StartMatch", "Gymnasium")
table.insert(Notes, "start: " .. H:JSONEncode(S))
local W = {}
local T0 = os.clock()
repeat task.wait(2) W = B:Invoke("Watchers") until #W > 0 or os.clock() - T0 > 45
table.insert(Notes, "watchers: " .. H:JSONEncode(W))
if #W == 0 then table.insert(Fails, "nobody sat on a bleacher seat within 45 s") end
B:Invoke("Score", "Gymnasium") task.wait(1)
W = B:Invoke("Watchers")
local Cheering = false
for _, X in W do if X.Gesture == "CheerSeated_Upper" then Cheering = true end end
if #W > 0 and not Cheering then table.insert(Fails, "no watcher cheered at the score") end
B:Invoke("EndMatch", "Gymnasium")
task.wait(12)
W = B:Invoke("Watchers")
if #W > 0 then table.insert(Fails, #W .. " still seated 12 s after the end") end
return (#Fails == 0 and "PASS watchcheck" or ("FAIL watchcheck\n" .. table.concat(Fails, "\n"))) .. "\n" .. table.concat(Notes, "\n")
