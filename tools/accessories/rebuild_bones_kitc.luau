if game.PlaceId ~= 98950102230473 then return "WRONG PLACE" end
local st = game.ReplicatedStorage.NHAccessories
local rep = {}
do local p = st:FindFirstChild("ScholarCoat") and st["ScholarCoat"]:FindFirstChild("ScholarCoatSkirt")
  if not p then table.insert(rep, "ScholarCoat.ScholarCoatSkirt missing") else
  for _, x in p:GetChildren() do if x:IsA("Bone") then x:Destroy() end end
  local B = {}
  B["Root"] = Instance.new("Bone") B["Root"].Name = "Root" B["Root"].CFrame = CFrame.new(-0.0000059, 1.3916264, -0.0000003, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["Root"].Parent = p
  B["F_LL"] = Instance.new("Bone") B["F_LL"].Name = "F_LL" B["F_LL"].CFrame = CFrame.new(-0.5000000, -1.0000000, 0.0000000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000) B["F_LL"].Parent = B["Root"]
  B["F_RL"] = Instance.new("Bone") B["F_RL"].Name = "F_RL" B["F_RL"].CFrame = CFrame.new(0.5000000, -1.0000000, 0.0000000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000) B["F_RL"].Parent = B["Root"]
  local n = 0 for _, x in p:GetDescendants() do if x:IsA("Bone") then n += 1 end end
  table.insert(rep, "ScholarCoat.ScholarCoatSkirt: " .. n .. " bones, skinned " .. tostring(p.HasSkinnedMesh)) end end
do local p = st:FindFirstChild("InvernessCoat") and st["InvernessCoat"]:FindFirstChild("InvernessCoatCape")
  if not p then table.insert(rep, "InvernessCoat.InvernessCoatCape missing") else
  for _, x in p:GetChildren() do if x:IsA("Bone") then x:Destroy() end end
  local B = {}
  B["Root"] = Instance.new("Bone") B["Root"].Name = "Root" B["Root"].CFrame = CFrame.new(0.0002511, -0.6106877, -0.0020569, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["Root"].Parent = p
  B["F_LA"] = Instance.new("Bone") B["F_LA"].Name = "F_LA" B["F_LA"].CFrame = CFrame.new(-1.5000000, 0.5000000, 0.0000000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000) B["F_LA"].Parent = B["Root"]
  B["F_RA"] = Instance.new("Bone") B["F_RA"].Name = "F_RA" B["F_RA"].CFrame = CFrame.new(1.5000000, 0.5000000, 0.0000000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000) B["F_RA"].Parent = B["Root"]
  local n = 0 for _, x in p:GetDescendants() do if x:IsA("Bone") then n += 1 end end
  table.insert(rep, "InvernessCoat.InvernessCoatCape: " .. n .. " bones, skinned " .. tostring(p.HasSkinnedMesh)) end end
do local p = st:FindFirstChild("InvernessCoat") and st["InvernessCoat"]:FindFirstChild("InvernessCoatSkirt")
  if not p then table.insert(rep, "InvernessCoat.InvernessCoatSkirt missing") else
  for _, x in p:GetChildren() do if x:IsA("Bone") then x:Destroy() end end
  local B = {}
  B["Root"] = Instance.new("Bone") B["Root"].Name = "Root" B["Root"].CFrame = CFrame.new(-0.0000069, 1.4166263, -0.0000009, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["Root"].Parent = p
  B["F_LL"] = Instance.new("Bone") B["F_LL"].Name = "F_LL" B["F_LL"].CFrame = CFrame.new(-0.5000000, -1.0000000, 0.0000000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000) B["F_LL"].Parent = B["Root"]
  B["F_RL"] = Instance.new("Bone") B["F_RL"].Name = "F_RL" B["F_RL"].CFrame = CFrame.new(0.5000000, -1.0000000, 0.0000000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000) B["F_RL"].Parent = B["Root"]
  local n = 0 for _, x in p:GetDescendants() do if x:IsA("Bone") then n += 1 end end
  table.insert(rep, "InvernessCoat.InvernessCoatSkirt: " .. n .. " bones, skinned " .. tostring(p.HasSkinnedMesh)) end end
do local p = st:FindFirstChild("RainCloak") and st["RainCloak"]:FindFirstChild("RainCloakSkirt")
  if not p then table.insert(rep, "RainCloak.RainCloakSkirt missing") else
  for _, x in p:GetChildren() do if x:IsA("Bone") then x:Destroy() end end
  local B = {}
  B["Root"] = Instance.new("Bone") B["Root"].Name = "Root" B["Root"].CFrame = CFrame.new(-0.0000086, 1.5665925, -0.0000035, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["Root"].Parent = p
  B["F_LL"] = Instance.new("Bone") B["F_LL"].Name = "F_LL" B["F_LL"].CFrame = CFrame.new(-0.5000000, -1.0000000, 0.0000000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000) B["F_LL"].Parent = B["Root"]
  B["F_RL"] = Instance.new("Bone") B["F_RL"].Name = "F_RL" B["F_RL"].CFrame = CFrame.new(0.5000000, -1.0000000, 0.0000000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000) B["F_RL"].Parent = B["Root"]
  local n = 0 for _, x in p:GetDescendants() do if x:IsA("Bone") then n += 1 end end
  table.insert(rep, "RainCloak.RainCloakSkirt: " .. n .. " bones, skinned " .. tostring(p.HasSkinnedMesh)) end end
do local p = st:FindFirstChild("LamplighterCoat") and st["LamplighterCoat"]:FindFirstChild("LamplighterCoatSkirt")
  if not p then table.insert(rep, "LamplighterCoat.LamplighterCoatSkirt missing") else
  for _, x in p:GetChildren() do if x:IsA("Bone") then x:Destroy() end end
  local B = {}
  B["Root"] = Instance.new("Bone") B["Root"].Name = "Root" B["Root"].CFrame = CFrame.new(-0.0000064, 1.6166264, -0.0000032, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["Root"].Parent = p
  B["F_LL"] = Instance.new("Bone") B["F_LL"].Name = "F_LL" B["F_LL"].CFrame = CFrame.new(-0.5000000, -1.0000000, 0.0000000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000) B["F_LL"].Parent = B["Root"]
  B["F_RL"] = Instance.new("Bone") B["F_RL"].Name = "F_RL" B["F_RL"].CFrame = CFrame.new(0.5000000, -1.0000000, 0.0000000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000) B["F_RL"].Parent = B["Root"]
  local n = 0 for _, x in p:GetDescendants() do if x:IsA("Bone") then n += 1 end end
  table.insert(rep, "LamplighterCoat.LamplighterCoatSkirt: " .. n .. " bones, skinned " .. tostring(p.HasSkinnedMesh)) end end
do local p = st:FindFirstChild("CadetCoat") and st["CadetCoat"]:FindFirstChild("CadetCoatSkirt")
  if not p then table.insert(rep, "CadetCoat.CadetCoatSkirt missing") else
  for _, x in p:GetChildren() do if x:IsA("Bone") then x:Destroy() end end
  local B = {}
  B["Root"] = Instance.new("Bone") B["Root"].Name = "Root" B["Root"].CFrame = CFrame.new(-0.0003058, 1.0916264, 0.0000961, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["Root"].Parent = p
  B["F_LL"] = Instance.new("Bone") B["F_LL"].Name = "F_LL" B["F_LL"].CFrame = CFrame.new(-0.5000000, -1.0000000, 0.0000000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000) B["F_LL"].Parent = B["Root"]
  B["F_RL"] = Instance.new("Bone") B["F_RL"].Name = "F_RL" B["F_RL"].CFrame = CFrame.new(0.5000000, -1.0000000, 0.0000000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000) B["F_RL"].Parent = B["Root"]
  local n = 0 for _, x in p:GetDescendants() do if x:IsA("Bone") then n += 1 end end
  table.insert(rep, "CadetCoat.CadetCoatSkirt: " .. n .. " bones, skinned " .. tostring(p.HasSkinnedMesh)) end end
do local p = st:FindFirstChild("ChesterfieldCoat") and st["ChesterfieldCoat"]:FindFirstChild("ChesterfieldCoatSkirt")
  if not p then table.insert(rep, "ChesterfieldCoat.ChesterfieldCoatSkirt missing") else
  for _, x in p:GetChildren() do if x:IsA("Bone") then x:Destroy() end end
  local B = {}
  B["Root"] = Instance.new("Bone") B["Root"].Name = "Root" B["Root"].CFrame = CFrame.new(-0.0000052, 1.4167147, -0.0000007, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["Root"].Parent = p
  B["F_LL"] = Instance.new("Bone") B["F_LL"].Name = "F_LL" B["F_LL"].CFrame = CFrame.new(-0.5000000, -1.0000000, 0.0000000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000) B["F_LL"].Parent = B["Root"]
  B["F_RL"] = Instance.new("Bone") B["F_RL"].Name = "F_RL" B["F_RL"].CFrame = CFrame.new(0.5000000, -1.0000000, 0.0000000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000) B["F_RL"].Parent = B["Root"]
  local n = 0 for _, x in p:GetDescendants() do if x:IsA("Bone") then n += 1 end end
  table.insert(rep, "ChesterfieldCoat.ChesterfieldCoatSkirt: " .. n .. " bones, skinned " .. tostring(p.HasSkinnedMesh)) end end
do local p = st:FindFirstChild("CardiganCoat") and st["CardiganCoat"]:FindFirstChild("CardiganCoatSkirt")
  if not p then table.insert(rep, "CardiganCoat.CardiganCoatSkirt missing") else
  for _, x in p:GetChildren() do if x:IsA("Bone") then x:Destroy() end end
  local B = {}
  B["Root"] = Instance.new("Bone") B["Root"].Name = "Root" B["Root"].CFrame = CFrame.new(-0.0002658, 1.3938379, 0.0021417, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["Root"].Parent = p
  B["F_LL"] = Instance.new("Bone") B["F_LL"].Name = "F_LL" B["F_LL"].CFrame = CFrame.new(-0.5000000, -1.0000000, 0.0000000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000) B["F_LL"].Parent = B["Root"]
  B["F_RL"] = Instance.new("Bone") B["F_RL"].Name = "F_RL" B["F_RL"].CFrame = CFrame.new(0.5000000, -1.0000000, 0.0000000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000) B["F_RL"].Parent = B["Root"]
  local n = 0 for _, x in p:GetDescendants() do if x:IsA("Bone") then n += 1 end end
  table.insert(rep, "CardiganCoat.CardiganCoatSkirt: " .. n .. " bones, skinned " .. tostring(p.HasSkinnedMesh)) end end
do local p = st:FindFirstChild("HuntingJacket") and st["HuntingJacket"]:FindFirstChild("HuntingJacketSkirt")
  if not p then table.insert(rep, "HuntingJacket.HuntingJacketSkirt missing") else
  for _, x in p:GetChildren() do if x:IsA("Bone") then x:Destroy() end end
  local B = {}
  B["Root"] = Instance.new("Bone") B["Root"].Name = "Root" B["Root"].CFrame = CFrame.new(-0.0003058, 0.9916264, 0.0339009, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["Root"].Parent = p
  B["F_LL"] = Instance.new("Bone") B["F_LL"].Name = "F_LL" B["F_LL"].CFrame = CFrame.new(-0.5000000, -1.0000000, 0.0000000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000) B["F_LL"].Parent = B["Root"]
  B["F_RL"] = Instance.new("Bone") B["F_RL"].Name = "F_RL" B["F_RL"].CFrame = CFrame.new(0.5000000, -1.0000000, 0.0000000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000) B["F_RL"].Parent = B["Root"]
  local n = 0 for _, x in p:GetDescendants() do if x:IsA("Bone") then n += 1 end end
  table.insert(rep, "HuntingJacket.HuntingJacketSkirt: " .. n .. " bones, skinned " .. tostring(p.HasSkinnedMesh)) end end
do local p = st:FindFirstChild("SmokingJacket") and st["SmokingJacket"]:FindFirstChild("SmokingJacketInner")
  if not p then table.insert(rep, "SmokingJacket.SmokingJacketInner missing") else
  for _, x in p:GetChildren() do if x:IsA("Bone") then x:Destroy() end end
  local B = {}
  B["Root"] = Instance.new("Bone") B["Root"].Name = "Root" B["Root"].CFrame = CFrame.new(0.0000000, -0.2950057, -0.5309708, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["Root"].Parent = p
  B["H0"] = Instance.new("Bone") B["H0"].Name = "H0" B["H0"].CFrame = CFrame.new(0.0460000, -0.0400000, 0.0000000, 0.9999434, 0.0075186, -0.0075184, 0.0075184, -0.9999715, -0.0000565, -0.0075186, 0.0000000, -0.9999717) B["H0"].Parent = B["Root"]
  B["C0_1"] = Instance.new("Bone") B["C0_1"].Name = "C0_1" B["C0_1"].CFrame = CFrame.new(0.0000000, -0.0000000, -0.0000000, 1.0000000, -0.0000000, 0.0000000, 0.0000000, 1.0000000, -0.0000000, -0.0000000, 0.0000000, 1.0000000) B["C0_1"].Parent = B["H0"]
  B["C0_2"] = Instance.new("Bone") B["C0_2"].Name = "C0_2" B["C0_2"].CFrame = CFrame.new(-0.0000000, 0.1489643, 0.0000000, 1.0000000, -0.0000000, 0.0000000, 0.0000000, 1.0000000, -0.0000000, -0.0000000, 0.0000000, 1.0000000) B["C0_2"].Parent = B["C0_1"]
  B["C0_3"] = Instance.new("Bone") B["C0_3"].Name = "C0_3" B["C0_3"].CFrame = CFrame.new(-0.0000000, 0.1436441, -0.0000000, 1.0000000, -0.0000000, 0.0000000, 0.0000000, 1.0000000, -0.0000000, -0.0000000, 0.0000000, 1.0000000) B["C0_3"].Parent = B["C0_2"]
  B["C0_4"] = Instance.new("Bone") B["C0_4"].Name = "C0_4" B["C0_4"].CFrame = CFrame.new(-0.0000000, 0.1330038, -0.0000000, 1.0000000, 0.0000000, -0.0000000, -0.0000000, 1.0000000, 0.0000000, 0.0000000, -0.0000000, 1.0000000) B["C0_4"].Parent = B["C0_3"]
  B["H1"] = Instance.new("Bone") B["H1"].Name = "H1" B["H1"].CFrame = CFrame.new(-0.0500000, -0.0400000, 0.0000000, 0.9999340, -0.0081298, 0.0081296, -0.0081295, -0.9999674, -0.0000661, 0.0081299, 0.0000000, -0.9999670) B["H1"].Parent = B["Root"]
  B["C1_1"] = Instance.new("Bone") B["C1_1"].Name = "C1_1" B["C1_1"].CFrame = CFrame.new(0.0000000, 0.0000000, 0.0000000, 1.0000000, -0.0000000, -0.0000001, 0.0000000, 1.0000000, 0.0000000, 0.0000001, -0.0000000, 1.0000000) B["C1_1"].Parent = B["H1"]
  B["C1_2"] = Instance.new("Bone") B["C1_2"].Name = "C1_2" B["C1_2"].CFrame = CFrame.new(0.0000000, 0.1377645, 0.0000000, 1.0000000, 0.0000000, -0.0000000, -0.0000000, 1.0000000, -0.0000000, 0.0000000, 0.0000000, 1.0000000) B["C1_2"].Parent = B["C1_1"]
  B["C1_3"] = Instance.new("Bone") B["C1_3"].Name = "C1_3" B["C1_3"].CFrame = CFrame.new(-0.0000000, 0.1328443, -0.0000000, 1.0000000, 0.0000000, -0.0000000, -0.0000000, 1.0000000, -0.0000000, 0.0000000, 0.0000000, 1.0000000) B["C1_3"].Parent = B["C1_2"]
  B["C1_4"] = Instance.new("Bone") B["C1_4"].Name = "C1_4" B["C1_4"].CFrame = CFrame.new(0.0000000, 0.1230040, 0.0000000, 1.0000000, -0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, -0.0000000, -0.0000000, 1.0000000) B["C1_4"].Parent = B["C1_3"]
  local n = 0 for _, x in p:GetDescendants() do if x:IsA("Bone") then n += 1 end end
  table.insert(rep, "SmokingJacket.SmokingJacketInner: " .. n .. " bones, skinned " .. tostring(p.HasSkinnedMesh)) end end
do local p = st:FindFirstChild("SmokingJacket") and st["SmokingJacket"]:FindFirstChild("SmokingJacketSkirt")
  if not p then table.insert(rep, "SmokingJacket.SmokingJacketSkirt missing") else
  for _, x in p:GetChildren() do if x:IsA("Bone") then x:Destroy() end end
  local B = {}
  B["Root"] = Instance.new("Bone") B["Root"].Name = "Root" B["Root"].CFrame = CFrame.new(-0.0003058, 0.8666264, 0.0000974, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["Root"].Parent = p
  B["F_LL"] = Instance.new("Bone") B["F_LL"].Name = "F_LL" B["F_LL"].CFrame = CFrame.new(-0.5000000, -1.0000000, 0.0000000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000) B["F_LL"].Parent = B["Root"]
  B["F_RL"] = Instance.new("Bone") B["F_RL"].Name = "F_RL" B["F_RL"].CFrame = CFrame.new(0.5000000, -1.0000000, 0.0000000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000) B["F_RL"].Parent = B["Root"]
  local n = 0 for _, x in p:GetDescendants() do if x:IsA("Bone") then n += 1 end end
  table.insert(rep, "SmokingJacket.SmokingJacketSkirt: " .. n .. " bones, skinned " .. tostring(p.HasSkinnedMesh)) end end
return table.concat(rep, string.char(10))
