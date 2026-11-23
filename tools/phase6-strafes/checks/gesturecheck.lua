-- gesturecheck (phase6-strafes T5 round C, Server, Play): StudentBrain.Gestures through ServerStorage.NHGestureProbe.
local B = game.ServerStorage:FindFirstChild("NHGestureProbe")
if not B then return "FAIL no NHGestureProbe" end
local H = game:GetService("HttpService")
local Fails, Notes = {}, {}
local function Ok(C, W) if not C then table.insert(Fails, W) end end
local L = B:Invoke("Students")
local I
for _, S in L do if S.Alive then I = S.I break end end
if not I then return "FAIL no student with a body (wait for the school day)" end
B:Invoke("Near", I, 6) task.wait(0.5)
local R = B:Invoke("Play", I, "Talk", false)
Ok(R.Ok and R.Gesture == "Talk", "Talk did not play: " .. H:JSONEncode(R))
task.wait(0.5)
local St = B:Invoke("State", I)
local Playing = false
for _, T in St.Tracks or {} do if T.W and T.W > 0.5 and T.P == "Action" then Playing = true end end
Ok(Playing, "no Action track playing on the student")
-- the far stop: a looping gesture ends once nobody is within 80 studs
B:Invoke("Away", 250) task.wait(2.2)
St = B:Invoke("State", I)
Ok(St.Gesture == nil, "far stop: still " .. tostring(St.Gesture))
-- the shove carry
B:Invoke("Near", I, 8) task.wait(0.5)
local P0 = B:Invoke("State", I).Pos
R = B:Invoke("Play", I, "Shove_InPlace", true)
Ok(R.Ok, "Shove_InPlace did not play")
task.wait(3)
local P1 = B:Invoke("State", I).Pos
local D = (P0 and P1) and (Vector3.new(P1.X, 0, P1.Z) - Vector3.new(P0.X, 0, P0.Z)).Magnitude or -1
table.insert(Notes, string.format("shove carry %.2f studs (7.24 in the open, less at a wall)", D))
Ok(D > 0.5 and D < 7.8, "carry distance " .. D)
table.insert(Notes, "active now " .. B:Invoke("Active").Active)
return (#Fails == 0 and "PASS gesturecheck" or ("FAIL gesturecheck\n" .. table.concat(Fails, "\n"))) .. "\n" .. table.concat(Notes, "\n")
