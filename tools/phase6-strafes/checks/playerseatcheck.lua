-- playerseatcheck (phase6-strafes T5 round C, Server, Play): players sit on the bleachers too.
local B = game.ServerStorage:FindFirstChild("NHGestureProbe")
if not B then return "FAIL no NHGestureProbe" end
local R = B:Invoke("SitBleacher")
local Fails = {}
if not (R.Ok and R.Prompt) then table.insert(Fails, "sit: " .. game:GetService("HttpService"):JSONEncode(R)) end
local S = B:Invoke("Stand")
if S.Seated then table.insert(Fails, "still seated after jumping") end
return #Fails == 0 and ("PASS playerseatcheck " .. tostring(R.Seat)) or ("FAIL playerseatcheck\n" .. table.concat(Fails, "\n"))
