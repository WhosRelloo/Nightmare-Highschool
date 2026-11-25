-- patientcheck (phase6-infirmary, Server, Play): the ambient patient on bed 1 and the infirmary's place order.
local B = game.ServerStorage:FindFirstChild("NHInfirmaryProbe")
if not B then return "FAIL no NHInfirmaryProbe" end
local H = game:GetService("HttpService")
local Fails, Notes = {}, {}
local function Ok(C, W) if not C then table.insert(Fails, W) end end
local I0 = B:Invoke("Patient", "get")
table.insert(Notes, string.format("on its own: wanted %s shown %s", tostring(I0.Wanted), tostring(I0.Shown)))
if I0.Wanted then Ok(I0.Shown, "the Nurse is on duty and bed 1 is free, but no patient (loop)") end
local I = B:Invoke("Patient", "show")
Ok(I.Shown and I.Flag == true, "show: " .. H:JSONEncode(I))
Ok(I.Laid == true, "not laid")
if I.Head and I.Torso then
	local Hd, T = Vector3.new(table.unpack(I.Head)), Vector3.new(table.unpack(I.Torso))
	Ok(Hd.Z > T.Z + 0.8, string.format("head not toward the pillow (+z): head z %.2f torso z %.2f", Hd.Z, T.Z))
	Ok(math.abs(T.X - I.Bed[1]) < 0.6, string.format("torso off the bed's centre line: x %.2f vs %.2f", T.X, I.Bed[1]))
	Ok(math.abs(Hd.Y - T.Y) < 0.9, string.format("not lying flat: head y %.2f torso y %.2f", Hd.Y, T.Y))
	Ok(T.Y > I.Top and T.Y < I.Top + 1.4, string.format("torso height %.2f vs bedding top %.2f", T.Y, I.Top))
	table.insert(Notes, string.format("torso (%.2f, %.2f, %.2f) head (%.2f, %.2f, %.2f) top %.2f", T.X, T.Y, T.Z, Hd.X, Hd.Y, Hd.Z, I.Top))
end
local P = B:Invoke("Place")
Ok(P.Place == "DormBed_Infirmary2", "first place for a sick student should be bed 2, got " .. tostring(P.Place))
local Hide = B:Invoke("Patient", "hide")
Ok(not Hide.Shown and Hide.Flag == nil, "hide")
P = B:Invoke("Place")
Ok(P.Place == "DormBed_Infirmary2", "after hide: " .. tostring(P.Place))
B:Invoke("Patient", "show")
if #Fails > 0 then return "FAIL " .. table.concat(Fails, "; ") .. " | " .. table.concat(Notes, "; ") end
return "PASS patientcheck: " .. table.concat(Notes, "; ")
