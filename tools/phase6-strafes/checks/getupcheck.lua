-- getupcheck (phase6-strafes T5 round C, Server, Play): the get-up reaction (Downed.OnRecovered -> Gestures.GetUp).
local B = game.ServerStorage:FindFirstChild("NHGestureProbe")
if not B then return "FAIL no NHGestureProbe" end
local Fails, Notes = {}, {}
local L = B:Invoke("Students")
local I
for _, S in L do if S.Alive and not B:Invoke("State", S.I).Seated then I = S.I break end end
if not I then return "FAIL no student with a body" end
B:Invoke("Near", I, 8)
local R = B:Invoke("DownRecover", I)
table.insert(Notes, game:GetService("HttpService"):JSONEncode(R))
if R.CanBeDowned then
	if not (R.Gesture and (R.Gesture == "Dizzy" or R.Gesture:find("^InjuredHurt_"))) then table.insert(Fails, "no get-up gesture after Recover: " .. tostring(R.Gesture)) end
	if not R.Reacting then table.insert(Fails, "not Reacting during the get-up") end
	if not R.Sick then table.insert(Fails, "SickUntil not set") end
else
	-- scheduled students can't be downed in every state: drive the hook directly
	R = B:Invoke("GetUp", I)
	if not R.Name then table.insert(Fails, "GetUp played nothing") end
	local St = B:Invoke("State", I)
	if not (St.Reacting and St.Sick) then table.insert(Fails, "GetUp: Reacting/Sick not set") end
	table.insert(Notes, "CanBeDowned false: Gestures.GetUp driven directly: " .. tostring(R.Name))
end
task.wait(8.5)
local St = B:Invoke("State", I)
if St.Reacting then table.insert(Fails, "still Reacting after 8.5 s") end
return (#Fails == 0 and "PASS getupcheck" or ("FAIL getupcheck\n" .. table.concat(Fails, "\n"))) .. "\n" .. table.concat(Notes, "\n")
