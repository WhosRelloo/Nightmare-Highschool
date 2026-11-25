-- phonecheck (phase6-infirmary, Server, Play): a walking call has a phone in the hand, and it goes when the walk ends.
local B = game.ServerStorage:FindFirstChild("NHInfirmaryProbe")
local G = game.ServerStorage:FindFirstChild("NHGestureProbe")
if not (B and G) then return "FAIL no probes" end
local H = game:GetService("HttpService")
local Fails, Notes = {}, {}
local function Ok(C, W) if not C then table.insert(Fails, W) end end
local I
for _, S in G:Invoke("Students") do if S.Alive and not G:Invoke("State", S.I).Seated then I = S.I break end end
if not I then return "FAIL no student with a body" end
G:Invoke("Near", I, 10) task.wait(0.5)
local R = B:Invoke("Phone", I)
Ok(R.Ok and R.InModel and R.Grip, "phone not in the hand: " .. H:JSONEncode(R))
Ok(R.Second, "a second phone was made while one is held")
B:Invoke("PhoneOff", I)
R = B:Invoke("Walk", I)
Ok(R.Ok, "no phone seen while walking: " .. H:JSONEncode(R))
Ok(R.Gone, "the phone stayed after the walk")
table.insert(Notes, "walk " .. H:JSONEncode(R))
if #Fails > 0 then return "FAIL " .. table.concat(Fails, "; ") .. " | " .. table.concat(Notes, "; ") end
return "PASS phonecheck: " .. table.concat(Notes, "; ")
