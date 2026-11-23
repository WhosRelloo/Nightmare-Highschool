local P = game.Players.LocalPlayer
local Probe = P.PlayerGui:FindFirstChild("NHQuietProbe")
if not Probe then return "FAIL no NHQuietProbe" end
local Root = P.Character and P.Character:FindFirstChild("HumanoidRootPart")
if not Root then return "FAIL no character" end
local Fails = {}
local function Ok(C, W) if not C then table.insert(Fails, W) end end
local Parts = {}
for I, D in { 5, 7 } do -- (S3) the engine did not show a prompt at 9 studs in this place; 7 shows both
	local Part = Instance.new("Part") Part.Anchored = true Part.CanCollide = false Part.Transparency = 1 Part.Size = Vector3.one
	Part.CFrame = Root.CFrame * CFrame.new(I == 1 and -2 or 2, 0, -D) Part.Name = "QcPromptTest" .. I Part.Parent = workspace
	local Pr = Instance.new("ProximityPrompt") Pr.ActionText = I == 1 and "Open" or "Read" Pr.ObjectText = "Mathematics · Room 12"
	Pr.MaxActivationDistance = 15 Pr.RequiresLineOfSight = false Pr.HoldDuration = 1 Pr.Exclusivity = Enum.ProximityPromptExclusivity.AlwaysShow Pr.Parent = Part
	table.insert(Parts, Part)
end
task.wait(1.2)
local L = Probe:Invoke("Prompts")
local Near, Far
for _, E in L do if E.Name == "Open" then Near = E elseif E.Name == "Read" then Far = E end end
Ok(Near and Near.Nearest and Near.Cap and Near.Tag and not Near.Pip, "nearest shows cap and tag")
Ok(Far and not Far.Nearest and Far.Pip and not Far.Tag, "the other shows a pip only")
Ok(Near and Near.ActionSize >= 22 and Near.ObjectSize >= 20 and Near.Fits, "text sizes/fit")
-- the hold fill rises
local Pr = Parts[1]:FindFirstChildOfClass("ProximityPrompt")
Pr:InputHoldBegin() task.wait(0.5)
local Board = nil
for _, B in P.PlayerGui:GetChildren() do if B.Name == "NHPrompt" and B.Adornee == Parts[1] then Board = B end end
local Well = Board and Board:FindFirstChild("Well", true)
Ok(Well and Well.Size.Y.Scale > 0.2 and Well.Size.Y.Scale < 0.9, "fill mid-hold " .. tostring(Well and Well.Size.Y.Scale))
Pr:InputHoldEnd()
for _, Part in Parts do Part:Destroy() end
return #Fails == 0 and "PASS qc_prompts" or ("FAIL\n" .. table.concat(Fails, "\n"))
