-- nursecheck (phase6-strafes T5 round C, Server, Play): the Nurse at her post in the Infirmary, and the region box.
local B = game.ServerStorage:FindFirstChild("NHGestureProbe")
if not B then return "FAIL no NHGestureProbe" end
local Fails = {}
local N = B:Invoke("NurseAt")
local Room = workspace.School:FindFirstChild("Infirmary")
local Zone = Room and Room:FindFirstChild("Zone")
if not Zone then return "FAIL no School.Infirmary.Zone" end
if not N.Pos then return "FAIL the Nurse isn't spawned" end
local L = Zone.CFrame:PointToObjectSpace(N.Pos)
if math.abs(L.X) > Zone.Size.X / 2 or math.abs(L.Z) > Zone.Size.Z / 2 then table.insert(Fails, "the Nurse is outside the Infirmary zone: " .. tostring(N.Pos)) end
local Post
for _, D in workspace:GetDescendants() do if D:IsA("BasePart") and D:GetAttribute("NpcPost") == "Nurse" then Post = D break end end
if not Post then table.insert(Fails, "no NpcPost = Nurse")
elseif (Vector3.new(N.Pos.X, 0, N.Pos.Z) - Vector3.new(Post.Position.X, 0, Post.Position.Z)).Magnitude > 3 then table.insert(Fails, "the Nurse is more than 3 studs from her post") end
local Box = workspace:FindFirstChild("Regions") and workspace.Regions:FindFirstChild("Infirmary")
if not (Box and Box:GetAttribute("RegionId") == "Infirmary") then table.insert(Fails, "no Regions.Infirmary box") end
return #Fails == 0 and "PASS nursecheck" or ("FAIL nursecheck\n" .. table.concat(Fails, "\n"))
