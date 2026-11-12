if game.PlaceId ~= 98950102230473 then return "WRONG PLACE" end
local st = game.ReplicatedStorage.NHAccessories
local rep = {}
local NL = string.char(10)
do local p = st:FindFirstChild("LongCoat") and st["LongCoat"]:FindFirstChild("LongCoatTailL")
  if not p then table.insert(rep, "LongCoat.LongCoatTailL missing") else
  for _, x in p:GetChildren() do if x:IsA("Bone") then x:Destroy() end end
  local B = {}
  B["Root"] = Instance.new("Bone") B["Root"].Name = "Root" B["Root"].CFrame = CFrame.new(0.0991058, 0.5757297, -0.0700001, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["Root"].Parent = p
  B["H0"] = Instance.new("Bone") B["H0"].Name = "H0" B["H0"].CFrame = CFrame.new(0.0000000, -0.0500000, -0.3996893, 0.9999635, -0.0059490, 0.0061375, -0.0061375, -0.9994956, 0.0311582, 0.0059489, -0.0311948, -0.9994958) B["H0"].Parent = B["Root"]
  B["C0_1"] = Instance.new("Bone") B["C0_1"].Name = "C0_1" B["C0_1"].CFrame = CFrame.new(0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, -0.0000000, 1.0000000, 0.0000001, -0.0000000, -0.0000001, 1.0000000) B["C0_1"].Parent = B["H0"]
  B["C0_2"] = Instance.new("Bone") B["C0_2"].Name = "C0_2" B["C0_2"].CFrame = CFrame.new(0.0000000, 0.3526779, 0.0000000, 0.9925221, -0.0832343, 0.0892865, 0.0868989, 0.9954935, -0.0379664, -0.0857240, 0.0454414, 0.9952821) B["C0_2"].Parent = B["C0_1"]
  B["C0_3"] = Instance.new("Bone") B["C0_3"].Name = "C0_3" B["C0_3"].CFrame = CFrame.new(0.0000000, 0.3549619, -0.0000000, 0.9787308, -0.1402342, 0.1497346, 0.1371254, 0.9900704, 0.0309405, -0.1525867, -0.0097500, 0.9882420) B["C0_3"].Parent = B["C0_2"]
  B["C0_4"] = Instance.new("Bone") B["C0_4"].Name = "C0_4" B["C0_4"].CFrame = CFrame.new(0.0000000, 0.3632289, 0.0000000, 0.9955938, 0.0682139, -0.0643422, -0.0666556, 0.9974355, 0.0260653, 0.0659552, -0.0216617, 0.9975875) B["C0_4"].Parent = B["C0_3"]
  B["H1"] = Instance.new("Bone") B["H1"].Name = "H1" B["H1"].CFrame = CFrame.new(0.0000000, -0.0500000, 0.0015535, 0.9999661, -0.0059456, 0.0056769, -0.0056768, -0.9989147, -0.0462305, 0.0059459, 0.0461967, -0.9989159) B["H1"].Parent = B["Root"]
  B["C1_1"] = Instance.new("Bone") B["C1_1"].Name = "C1_1" B["C1_1"].CFrame = CFrame.new(0.0000000, 0.0000000, 0.0000000, 1.0000000, -0.0000000, -0.0000000, 0.0000000, 1.0000000, -0.0000000, 0.0000000, 0.0000000, 1.0000000) B["C1_1"].Parent = B["H1"]
  B["C1_2"] = Instance.new("Bone") B["C1_2"].Name = "C1_2" B["C1_2"].CFrame = CFrame.new(0.0000000, 0.3528830, 0.0000000, 0.9935187, -0.0829470, 0.0777202, 0.0813546, 0.9964095, 0.0234422, -0.0793856, -0.0169674, 0.9966996) B["C1_2"].Parent = B["C1_1"]
  B["C1_3"] = Instance.new("Bone") B["C1_3"].Name = "C1_3" B["C1_3"].CFrame = CFrame.new(-0.0000000, 0.3546019, 0.0000000, 0.9813328, -0.1408076, 0.1309936, 0.1387821, 0.9900195, 0.0245119, -0.1331377, -0.0058747, 0.9910802) B["C1_3"].Parent = B["C1_2"]
  B["C1_4"] = Instance.new("Bone") B["C1_4"].Name = "C1_4" B["C1_4"].CFrame = CFrame.new(0.0000000, 0.3626466, 0.0000000, 0.9967621, 0.0535576, -0.0599744, -0.0558744, 0.9977280, -0.0376414, 0.0578222, 0.0408706, 0.9974899) B["C1_4"].Parent = B["C1_3"]
  B["H2"] = Instance.new("Bone") B["H2"].Name = "H2" B["H2"].CFrame = CFrame.new(0.0000000, -0.0500000, 0.4027963, 0.9999688, -0.0059069, 0.0052210, -0.0052212, -0.9924179, -0.1227976, 0.0059050, 0.1227665, -0.9923985) B["H2"].Parent = B["Root"]
  B["C2_1"] = Instance.new("Bone") B["C2_1"].Name = "C2_1" B["C2_1"].CFrame = CFrame.new(-0.0000000, 0.0000000, 0.0000000, 1.0000000, -0.0000000, -0.0000000, 0.0000000, 0.9999999, -0.0000001, 0.0000000, 0.0000001, 1.0000000) B["C2_1"].Parent = B["H2"]
  B["C2_2"] = Instance.new("Bone") B["C2_2"].Name = "C2_2" B["C2_2"].CFrame = CFrame.new(0.0000000, 0.3551931, 0.0000000, 0.9944874, -0.0810955, 0.0664702, 0.0754869, 0.9936914, 0.0829420, -0.0727771, -0.0774671, 0.9943351) B["C2_2"].Parent = B["C2_1"]
  B["C2_3"] = Instance.new("Bone") B["C2_3"].Name = "C2_3" B["C2_3"].CFrame = CFrame.new(-0.0000000, 0.3610864, -0.0000000, 0.9838769, -0.1388759, 0.1126920, 0.1377275, 0.9903074, 0.0179509, -0.1140926, -0.0021407, 0.9934678) B["C2_3"].Parent = B["C2_2"]
  B["C2_4"] = Instance.new("Bone") B["C2_4"].Name = "C2_4" B["C2_4"].CFrame = CFrame.new(0.0000000, 0.3685554, -0.0000000, 0.9977386, 0.0390198, -0.0547292, -0.0443282, 0.9940600, -0.0993961, 0.0505256, 0.1015974, 0.9935417) B["C2_4"].Parent = B["C2_3"]
  local n = 0 for _, x in p:GetDescendants() do if x:IsA("Bone") then n += 1 end end
  table.insert(rep, "LongCoat.LongCoatTailL: " .. n .. " bones, skinned " .. tostring(p.HasSkinnedMesh)) end end
do local p = st:FindFirstChild("LongCoat") and st["LongCoat"]:FindFirstChild("LongCoatTailR")
  if not p then table.insert(rep, "LongCoat.LongCoatTailR missing") else
  for _, x in p:GetChildren() do if x:IsA("Bone") then x:Destroy() end end
  local B = {}
  B["Root"] = Instance.new("Bone") B["Root"].Name = "Root" B["Root"].CFrame = CFrame.new(-0.0991058, 0.5757297, -0.0700001, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["Root"].Parent = p
  B["H0"] = Instance.new("Bone") B["H0"].Name = "H0" B["H0"].CFrame = CFrame.new(0.0000000, -0.0500000, -0.3996893, 0.9999635, 0.0059490, -0.0061375, 0.0061375, -0.9994956, 0.0311582, -0.0059489, -0.0311948, -0.9994958) B["H0"].Parent = B["Root"]
  B["C0_1"] = Instance.new("Bone") B["C0_1"].Name = "C0_1" B["C0_1"].CFrame = CFrame.new(-0.0000000, 0.0000000, 0.0000000, 1.0000000, -0.0000000, -0.0000000, 0.0000000, 1.0000000, 0.0000001, 0.0000000, -0.0000001, 1.0000000) B["C0_1"].Parent = B["H0"]
  B["C0_2"] = Instance.new("Bone") B["C0_2"].Name = "C0_2" B["C0_2"].CFrame = CFrame.new(-0.0000000, 0.3526779, 0.0000000, 0.9925221, 0.0832343, -0.0892865, -0.0868989, 0.9954935, -0.0379664, 0.0857240, 0.0454414, 0.9952821) B["C0_2"].Parent = B["C0_1"]
  B["C0_3"] = Instance.new("Bone") B["C0_3"].Name = "C0_3" B["C0_3"].CFrame = CFrame.new(-0.0000000, 0.3549619, -0.0000000, 0.9787308, 0.1402342, -0.1497346, -0.1371254, 0.9900704, 0.0309405, 0.1525867, -0.0097500, 0.9882420) B["C0_3"].Parent = B["C0_2"]
  B["C0_4"] = Instance.new("Bone") B["C0_4"].Name = "C0_4" B["C0_4"].CFrame = CFrame.new(-0.0000000, 0.3632289, 0.0000000, 0.9955938, -0.0682139, 0.0643422, 0.0666556, 0.9974355, 0.0260653, -0.0659552, -0.0216617, 0.9975875) B["C0_4"].Parent = B["C0_3"]
  B["H1"] = Instance.new("Bone") B["H1"].Name = "H1" B["H1"].CFrame = CFrame.new(0.0000000, -0.0500000, 0.0015535, 0.9999661, 0.0059456, -0.0056769, 0.0056768, -0.9989147, -0.0462305, -0.0059459, 0.0461967, -0.9989159) B["H1"].Parent = B["Root"]
  B["C1_1"] = Instance.new("Bone") B["C1_1"].Name = "C1_1" B["C1_1"].CFrame = CFrame.new(-0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, -0.0000000, 1.0000000, -0.0000000, -0.0000000, 0.0000000, 1.0000000) B["C1_1"].Parent = B["H1"]
  B["C1_2"] = Instance.new("Bone") B["C1_2"].Name = "C1_2" B["C1_2"].CFrame = CFrame.new(-0.0000000, 0.3528830, 0.0000000, 0.9935187, 0.0829470, -0.0777202, -0.0813546, 0.9964095, 0.0234422, 0.0793856, -0.0169674, 0.9966996) B["C1_2"].Parent = B["C1_1"]
  B["C1_3"] = Instance.new("Bone") B["C1_3"].Name = "C1_3" B["C1_3"].CFrame = CFrame.new(0.0000000, 0.3546019, 0.0000000, 0.9813328, 0.1408076, -0.1309936, -0.1387821, 0.9900195, 0.0245119, 0.1331377, -0.0058747, 0.9910802) B["C1_3"].Parent = B["C1_2"]
  B["C1_4"] = Instance.new("Bone") B["C1_4"].Name = "C1_4" B["C1_4"].CFrame = CFrame.new(-0.0000000, 0.3626466, 0.0000000, 0.9967621, -0.0535576, 0.0599744, 0.0558744, 0.9977280, -0.0376414, -0.0578222, 0.0408706, 0.9974899) B["C1_4"].Parent = B["C1_3"]
  B["H2"] = Instance.new("Bone") B["H2"].Name = "H2" B["H2"].CFrame = CFrame.new(0.0000000, -0.0500000, 0.4027963, 0.9999688, 0.0059069, -0.0052210, 0.0052212, -0.9924179, -0.1227976, -0.0059050, 0.1227665, -0.9923985) B["H2"].Parent = B["Root"]
  B["C2_1"] = Instance.new("Bone") B["C2_1"].Name = "C2_1" B["C2_1"].CFrame = CFrame.new(0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, -0.0000000, 0.9999999, -0.0000001, -0.0000000, 0.0000001, 1.0000000) B["C2_1"].Parent = B["H2"]
  B["C2_2"] = Instance.new("Bone") B["C2_2"].Name = "C2_2" B["C2_2"].CFrame = CFrame.new(-0.0000000, 0.3551931, 0.0000000, 0.9944874, 0.0810955, -0.0664702, -0.0754869, 0.9936914, 0.0829420, 0.0727771, -0.0774671, 0.9943351) B["C2_2"].Parent = B["C2_1"]
  B["C2_3"] = Instance.new("Bone") B["C2_3"].Name = "C2_3" B["C2_3"].CFrame = CFrame.new(0.0000000, 0.3610864, -0.0000000, 0.9838769, 0.1388759, -0.1126920, -0.1377275, 0.9903074, 0.0179509, 0.1140926, -0.0021407, 0.9934678) B["C2_3"].Parent = B["C2_2"]
  B["C2_4"] = Instance.new("Bone") B["C2_4"].Name = "C2_4" B["C2_4"].CFrame = CFrame.new(-0.0000000, 0.3685554, -0.0000000, 0.9977386, -0.0390198, 0.0547292, 0.0443282, 0.9940600, -0.0993961, -0.0505256, 0.1015974, 0.9935417) B["C2_4"].Parent = B["C2_3"]
  local n = 0 for _, x in p:GetDescendants() do if x:IsA("Bone") then n += 1 end end
  table.insert(rep, "LongCoat.LongCoatTailR: " .. n .. " bones, skinned " .. tostring(p.HasSkinnedMesh)) end end
do local p = st:FindFirstChild("Greatcoat") and st["Greatcoat"]:FindFirstChild("GreatcoatTailL")
  if not p then table.insert(rep, "Greatcoat.GreatcoatTailL missing") else
  for _, x in p:GetChildren() do if x:IsA("Bone") then x:Destroy() end end
  local B = {}
  B["Root"] = Instance.new("Bone") B["Root"].Name = "Root" B["Root"].CFrame = CFrame.new(0.1471943, 0.7775715, -0.1100000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["Root"].Parent = p
  B["H0"] = Instance.new("Bone") B["H0"].Name = "H0" B["H0"].CFrame = CFrame.new(0.0000000, -0.0500000, -0.3996952, 0.9998910, -0.0102436, 0.0106309, -0.0106310, -0.9992571, 0.0370470, 0.0102433, -0.0371559, -0.9992576) B["H0"].Parent = B["Root"]
  B["C0_1"] = Instance.new("Bone") B["C0_1"].Name = "C0_1" B["C0_1"].CFrame = CFrame.new(0.0000000, 0.0000000, 0.0000000, 1.0000000, -0.0000003, 0.0000003, 0.0000003, 0.9999999, -0.0000001, -0.0000003, 0.0000001, 1.0000000) B["C0_1"].Parent = B["H0"]
  B["C0_2"] = Instance.new("Bone") B["C0_2"].Name = "C0_2" B["C0_2"].CFrame = CFrame.new(-0.0000000, 0.4528364, 0.0000000, 0.9832263, -0.1239189, 0.1338294, 0.1295855, 0.9909693, -0.0344622, -0.1283503, 0.0512265, 0.9904050) B["C0_2"].Parent = B["C0_1"]
  B["C0_3"] = Instance.new("Bone") B["C0_3"].Name = "C0_3" B["C0_3"].CFrame = CFrame.new(0.0000000, 0.4584517, -0.0000000, 0.9819309, -0.1282588, 0.1391451, 0.1247976, 0.9916213, 0.0333576, -0.1422577, -0.0153899, 0.9897100) B["C0_3"].Parent = B["C0_2"]
  B["C0_4"] = Instance.new("Bone") B["C0_4"].Name = "C0_4" B["C0_4"].CFrame = CFrame.new(-0.0000000, 0.4707355, -0.0000000, 0.9909174, 0.0966936, -0.0934515, -0.0945342, 0.9951479, 0.0272752, 0.0956355, -0.0181931, 0.9952502) B["C0_4"].Parent = B["C0_3"]
  B["H1"] = Instance.new("Bone") B["H1"].Name = "H1" B["H1"].CFrame = CFrame.new(0.0000000, -0.0500000, 0.0015240, 0.9997972, -0.0146149, 0.0138582, -0.0138581, -0.9984866, -0.0532173, 0.0146162, 0.0530144, -0.9984889) B["H1"].Parent = B["Root"]
  B["C1_1"] = Instance.new("Bone") B["C1_1"].Name = "C1_1" B["C1_1"].CFrame = CFrame.new(-0.0000000, -0.0000000, 0.0000000, 1.0000000, -0.0000003, 0.0000002, 0.0000003, 1.0000000, -0.0000000, -0.0000002, 0.0000000, 1.0000000) B["C1_1"].Parent = B["H1"]
  B["C1_2"] = Instance.new("Bone") B["C1_2"].Name = "C1_2" B["C1_2"].CFrame = CFrame.new(-0.0000000, 0.4531858, -0.0000000, 0.9842988, -0.1299508, 0.1194516, 0.1256965, 0.9911573, 0.0425168, -0.1239204, -0.0268346, 0.9919293) B["C1_2"].Parent = B["C1_1"]
  B["C1_3"] = Instance.new("Bone") B["C1_3"].Name = "C1_3" B["C1_3"].CFrame = CFrame.new(0.0000000, 0.4587257, 0.0000000, 0.9845381, -0.1290578, 0.1184422, 0.1267142, 0.9915679, 0.0271410, -0.1209462, -0.0117130, 0.9925899) B["C1_3"].Parent = B["C1_2"]
  B["C1_4"] = Instance.new("Bone") B["C1_4"].Name = "C1_4" B["C1_4"].CFrame = CFrame.new(-0.0000000, 0.4714187, 0.0000000, 0.9925579, 0.0808273, -0.0910804, -0.0857528, 0.9949833, -0.0515230, 0.0864590, 0.0589500, 0.9945098) B["C1_4"].Parent = B["C1_3"]
  B["H2"] = Instance.new("Bone") B["H2"].Name = "H2" B["H2"].CFrame = CFrame.new(0.0000000, -0.0500000, 0.4027431, 0.9999099, -0.0101469, 0.0087955, -0.0087955, -0.9898269, -0.1420050, 0.0101468, 0.1419148, -0.9898257) B["H2"].Parent = B["Root"]
  B["C2_1"] = Instance.new("Bone") B["C2_1"].Name = "C2_1" B["C2_1"].CFrame = CFrame.new(-0.0000000, 0.0000000, 0.0000000, 1.0000000, -0.0000003, 0.0000002, 0.0000003, 1.0000000, -0.0000001, -0.0000002, 0.0000001, 1.0000000) B["C2_1"].Parent = B["H2"]
  B["C2_2"] = Instance.new("Bone") B["C2_2"].Name = "C2_2" B["C2_2"].CFrame = CFrame.new(0.0000000, 0.4571506, 0.0000000, 0.9884332, -0.1192958, 0.0936391, 0.1086372, 0.9877873, 0.1116866, -0.1058193, -0.1002221, 0.9893219) B["C2_2"].Parent = B["C2_1"]
  B["C2_3"] = Instance.new("Bone") B["C2_3"].Name = "C2_3" B["C2_3"].CFrame = CFrame.new(0.0000000, 0.4701508, 0.0000000, 0.9870197, -0.1267818, 0.0985826, 0.1256045, 0.9919157, 0.0180837, -0.1000782, -0.0054666, 0.9949645) B["C2_3"].Parent = B["C2_2"]
  B["C2_4"] = Instance.new("Bone") B["C2_4"].Name = "C2_4" B["C2_4"].CFrame = CFrame.new(0.0000000, 0.4811429, -0.0000000, 0.9954318, 0.0563889, -0.0770438, -0.0656986, 0.9900796, -0.1242017, 0.0692758, 0.1286960, 0.9892614) B["C2_4"].Parent = B["C2_3"]
  local n = 0 for _, x in p:GetDescendants() do if x:IsA("Bone") then n += 1 end end
  table.insert(rep, "Greatcoat.GreatcoatTailL: " .. n .. " bones, skinned " .. tostring(p.HasSkinnedMesh)) end end
do local p = st:FindFirstChild("Greatcoat") and st["Greatcoat"]:FindFirstChild("GreatcoatTailR")
  if not p then table.insert(rep, "Greatcoat.GreatcoatTailR missing") else
  for _, x in p:GetChildren() do if x:IsA("Bone") then x:Destroy() end end
  local B = {}
  B["Root"] = Instance.new("Bone") B["Root"].Name = "Root" B["Root"].CFrame = CFrame.new(-0.1471943, 0.7775715, -0.1100000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["Root"].Parent = p
  B["H0"] = Instance.new("Bone") B["H0"].Name = "H0" B["H0"].CFrame = CFrame.new(0.0000000, -0.0500000, -0.3996952, 0.9998910, 0.0102436, -0.0106309, 0.0106310, -0.9992571, 0.0370470, -0.0102433, -0.0371559, -0.9992576) B["H0"].Parent = B["Root"]
  B["C0_1"] = Instance.new("Bone") B["C0_1"].Name = "C0_1" B["C0_1"].CFrame = CFrame.new(0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000003, -0.0000003, -0.0000003, 0.9999999, -0.0000001, 0.0000003, 0.0000001, 1.0000000) B["C0_1"].Parent = B["H0"]
  B["C0_2"] = Instance.new("Bone") B["C0_2"].Name = "C0_2" B["C0_2"].CFrame = CFrame.new(0.0000000, 0.4528364, 0.0000000, 0.9832263, 0.1239189, -0.1338294, -0.1295855, 0.9909693, -0.0344622, 0.1283503, 0.0512265, 0.9904050) B["C0_2"].Parent = B["C0_1"]
  B["C0_3"] = Instance.new("Bone") B["C0_3"].Name = "C0_3" B["C0_3"].CFrame = CFrame.new(-0.0000000, 0.4584517, -0.0000000, 0.9819309, 0.1282588, -0.1391451, -0.1247976, 0.9916213, 0.0333576, 0.1422577, -0.0153899, 0.9897100) B["C0_3"].Parent = B["C0_2"]
  B["C0_4"] = Instance.new("Bone") B["C0_4"].Name = "C0_4" B["C0_4"].CFrame = CFrame.new(0.0000000, 0.4707355, -0.0000000, 0.9909174, -0.0966936, 0.0934515, 0.0945342, 0.9951479, 0.0272752, -0.0956355, -0.0181931, 0.9952502) B["C0_4"].Parent = B["C0_3"]
  B["H1"] = Instance.new("Bone") B["H1"].Name = "H1" B["H1"].CFrame = CFrame.new(0.0000000, -0.0500000, 0.0015240, 0.9997972, 0.0146149, -0.0138582, 0.0138581, -0.9984866, -0.0532173, -0.0146162, 0.0530144, -0.9984889) B["H1"].Parent = B["Root"]
  B["C1_1"] = Instance.new("Bone") B["C1_1"].Name = "C1_1" B["C1_1"].CFrame = CFrame.new(0.0000000, -0.0000000, 0.0000000, 1.0000000, 0.0000003, -0.0000002, -0.0000003, 1.0000000, -0.0000000, 0.0000002, 0.0000000, 1.0000000) B["C1_1"].Parent = B["H1"]
  B["C1_2"] = Instance.new("Bone") B["C1_2"].Name = "C1_2" B["C1_2"].CFrame = CFrame.new(0.0000000, 0.4531858, -0.0000000, 0.9842988, 0.1299508, -0.1194516, -0.1256965, 0.9911573, 0.0425168, 0.1239204, -0.0268346, 0.9919293) B["C1_2"].Parent = B["C1_1"]
  B["C1_3"] = Instance.new("Bone") B["C1_3"].Name = "C1_3" B["C1_3"].CFrame = CFrame.new(-0.0000000, 0.4587257, 0.0000000, 0.9845381, 0.1290578, -0.1184422, -0.1267142, 0.9915679, 0.0271410, 0.1209462, -0.0117130, 0.9925899) B["C1_3"].Parent = B["C1_2"]
  B["C1_4"] = Instance.new("Bone") B["C1_4"].Name = "C1_4" B["C1_4"].CFrame = CFrame.new(0.0000000, 0.4714187, 0.0000000, 0.9925579, -0.0808273, 0.0910804, 0.0857528, 0.9949833, -0.0515230, -0.0864590, 0.0589500, 0.9945098) B["C1_4"].Parent = B["C1_3"]
  B["H2"] = Instance.new("Bone") B["H2"].Name = "H2" B["H2"].CFrame = CFrame.new(0.0000000, -0.0500000, 0.4027431, 0.9999099, 0.0101469, -0.0087955, 0.0087955, -0.9898269, -0.1420050, -0.0101468, 0.1419148, -0.9898257) B["H2"].Parent = B["Root"]
  B["C2_1"] = Instance.new("Bone") B["C2_1"].Name = "C2_1" B["C2_1"].CFrame = CFrame.new(0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000003, -0.0000002, -0.0000003, 1.0000000, -0.0000001, 0.0000002, 0.0000001, 1.0000000) B["C2_1"].Parent = B["H2"]
  B["C2_2"] = Instance.new("Bone") B["C2_2"].Name = "C2_2" B["C2_2"].CFrame = CFrame.new(-0.0000000, 0.4571506, 0.0000000, 0.9884332, 0.1192958, -0.0936391, -0.1086372, 0.9877873, 0.1116866, 0.1058193, -0.1002221, 0.9893219) B["C2_2"].Parent = B["C2_1"]
  B["C2_3"] = Instance.new("Bone") B["C2_3"].Name = "C2_3" B["C2_3"].CFrame = CFrame.new(-0.0000000, 0.4701508, 0.0000000, 0.9870197, 0.1267818, -0.0985826, -0.1256045, 0.9919157, 0.0180837, 0.1000782, -0.0054666, 0.9949645) B["C2_3"].Parent = B["C2_2"]
  B["C2_4"] = Instance.new("Bone") B["C2_4"].Name = "C2_4" B["C2_4"].CFrame = CFrame.new(-0.0000000, 0.4811429, -0.0000000, 0.9954318, -0.0563889, 0.0770438, 0.0656986, 0.9900796, -0.1242017, -0.0692758, 0.1286960, 0.9892614) B["C2_4"].Parent = B["C2_3"]
  local n = 0 for _, x in p:GetDescendants() do if x:IsA("Bone") then n += 1 end end
  table.insert(rep, "Greatcoat.GreatcoatTailR: " .. n .. " bones, skinned " .. tostring(p.HasSkinnedMesh)) end end
do local p = st:FindFirstChild("Scarves") and st["Scarves"]:FindFirstChild("ScarfStripe")
  if not p then table.insert(rep, "Scarves.ScarfStripe missing") else
  for _, x in p:GetChildren() do if x:IsA("Bone") then x:Destroy() end end
  local B = {}
  B["Root"] = Instance.new("Bone") B["Root"].Name = "Root" B["Root"].CFrame = CFrame.new(0.0119665, 0.7601726, 0.0200749, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["Root"].Parent = p
  B["H0"] = Instance.new("Bone") B["H0"].Name = "H0" B["H0"].CFrame = CFrame.new(0.1320000, -0.1000000, -0.5970000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000) B["H0"].Parent = B["Root"]
  B["C0_1"] = Instance.new("Bone") B["C0_1"].Name = "C0_1" B["C0_1"].CFrame = CFrame.new(-0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000001, 0.0000000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, 1.0000000) B["C0_1"].Parent = B["H0"]
  B["C0_2"] = Instance.new("Bone") B["C0_2"].Name = "C0_2" B["C0_2"].CFrame = CFrame.new(0.0000000, 0.4025000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["C0_2"].Parent = B["C0_1"]
  B["C0_3"] = Instance.new("Bone") B["C0_3"].Name = "C0_3" B["C0_3"].CFrame = CFrame.new(0.0000000, 0.4025000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["C0_3"].Parent = B["C0_2"]
  B["C0_4"] = Instance.new("Bone") B["C0_4"].Name = "C0_4" B["C0_4"].CFrame = CFrame.new(0.0000000, 0.4025000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["C0_4"].Parent = B["C0_3"]
  B["H1"] = Instance.new("Bone") B["H1"].Name = "H1" B["H1"].CFrame = CFrame.new(-0.0430000, -0.1000000, -0.6500000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, -0.9999998, 0.0000000, -0.0000001, 0.0000000, -1.0000000) B["H1"].Parent = B["Root"]
  B["C1_1"] = Instance.new("Bone") B["C1_1"].Name = "C1_1" B["C1_1"].CFrame = CFrame.new(0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000001, 0.0000000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, 1.0000000) B["C1_1"].Parent = B["H1"]
  B["C1_2"] = Instance.new("Bone") B["C1_2"].Name = "C1_2" B["C1_2"].CFrame = CFrame.new(0.0000000, 0.3237500, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["C1_2"].Parent = B["C1_1"]
  B["C1_3"] = Instance.new("Bone") B["C1_3"].Name = "C1_3" B["C1_3"].CFrame = CFrame.new(0.0000000, 0.3237501, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["C1_3"].Parent = B["C1_2"]
  B["C1_4"] = Instance.new("Bone") B["C1_4"].Name = "C1_4" B["C1_4"].CFrame = CFrame.new(0.0000000, 0.3237501, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["C1_4"].Parent = B["C1_3"]
  local n = 0 for _, x in p:GetDescendants() do if x:IsA("Bone") then n += 1 end end
  table.insert(rep, "Scarves.ScarfStripe: " .. n .. " bones, skinned " .. tostring(p.HasSkinnedMesh)) end end
do local p = st:FindFirstChild("Scarves") and st["Scarves"]:FindFirstChild("ScarfViolet")
  if not p then table.insert(rep, "Scarves.ScarfViolet missing") else
  for _, x in p:GetChildren() do if x:IsA("Bone") then x:Destroy() end end
  local B = {}
  B["Root"] = Instance.new("Bone") B["Root"].Name = "Root" B["Root"].CFrame = CFrame.new(0.0119665, 0.7601726, 0.0200749, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["Root"].Parent = p
  B["H0"] = Instance.new("Bone") B["H0"].Name = "H0" B["H0"].CFrame = CFrame.new(0.1320000, -0.1000000, -0.5970000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000, 0.0000000, -0.0000001, 0.0000000, -1.0000000) B["H0"].Parent = B["Root"]
  B["C0_1"] = Instance.new("Bone") B["C0_1"].Name = "C0_1" B["C0_1"].CFrame = CFrame.new(-0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000001, 0.0000000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, 1.0000000) B["C0_1"].Parent = B["H0"]
  B["C0_2"] = Instance.new("Bone") B["C0_2"].Name = "C0_2" B["C0_2"].CFrame = CFrame.new(0.0000000, 0.4025000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["C0_2"].Parent = B["C0_1"]
  B["C0_3"] = Instance.new("Bone") B["C0_3"].Name = "C0_3" B["C0_3"].CFrame = CFrame.new(0.0000000, 0.4025000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["C0_3"].Parent = B["C0_2"]
  B["C0_4"] = Instance.new("Bone") B["C0_4"].Name = "C0_4" B["C0_4"].CFrame = CFrame.new(0.0000000, 0.4025000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["C0_4"].Parent = B["C0_3"]
  B["H1"] = Instance.new("Bone") B["H1"].Name = "H1" B["H1"].CFrame = CFrame.new(-0.0430000, -0.1000000, -0.6500000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, -0.9999998, 0.0000000, -0.0000001, 0.0000000, -1.0000000) B["H1"].Parent = B["Root"]
  B["C1_1"] = Instance.new("Bone") B["C1_1"].Name = "C1_1" B["C1_1"].CFrame = CFrame.new(0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000001, 0.0000000, 1.0000000, 0.0000000, -0.0000001, 0.0000000, 1.0000000) B["C1_1"].Parent = B["H1"]
  B["C1_2"] = Instance.new("Bone") B["C1_2"].Name = "C1_2" B["C1_2"].CFrame = CFrame.new(0.0000000, 0.3237500, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["C1_2"].Parent = B["C1_1"]
  B["C1_3"] = Instance.new("Bone") B["C1_3"].Name = "C1_3" B["C1_3"].CFrame = CFrame.new(0.0000000, 0.3237501, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["C1_3"].Parent = B["C1_2"]
  B["C1_4"] = Instance.new("Bone") B["C1_4"].Name = "C1_4" B["C1_4"].CFrame = CFrame.new(0.0000000, 0.3237501, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["C1_4"].Parent = B["C1_3"]
  local n = 0 for _, x in p:GetDescendants() do if x:IsA("Bone") then n += 1 end end
  table.insert(rep, "Scarves.ScarfViolet: " .. n .. " bones, skinned " .. tostring(p.HasSkinnedMesh)) end end
do local p = st:FindFirstChild("ChainedLedger") and st["ChainedLedger"]:FindFirstChild("Ledger")
  if not p then table.insert(rep, "ChainedLedger.Ledger missing") else
  for _, x in p:GetChildren() do if x:IsA("Bone") then x:Destroy() end end
  local B = {}
  B["Root"] = Instance.new("Bone") B["Root"].Name = "Root" B["Root"].CFrame = CFrame.new(0.0866206, 0.2480851, 0.0115184, 0.9863630, -0.1281984, -0.1032147, 0.1032147, 0.9702958, -0.2187984, 0.1281984, 0.2051615, 0.9702958) B["Root"].Parent = p
  B["Page1"] = Instance.new("Bone") B["Page1"].Name = "Page1" B["Page1"].CFrame = CFrame.new(0.0200526, -0.0000000, -0.0425077, 1.0000000, -0.0000008, -0.0000007, 0.0000009, 1.0000000, -0.0000001, 0.0000007, 0.0000001, 1.0000000) B["Page1"].Parent = B["Root"]
  B["Page2"] = Instance.new("Bone") B["Page2"].Name = "Page2" B["Page2"].CFrame = CFrame.new(0.0200526, -0.0000000, -0.0425077, 1.0000000, -0.0000008, -0.0000007, 0.0000009, 1.0000000, -0.0000001, 0.0000007, 0.0000001, 1.0000000) B["Page2"].Parent = B["Root"]
  B["Page3"] = Instance.new("Bone") B["Page3"].Name = "Page3" B["Page3"].CFrame = CFrame.new(0.0200526, -0.0000000, -0.0425077, 1.0000000, -0.0000008, -0.0000007, 0.0000009, 1.0000000, -0.0000001, 0.0000007, 0.0000001, 1.0000000) B["Page3"].Parent = B["Root"]
  B["Page4"] = Instance.new("Bone") B["Page4"].Name = "Page4" B["Page4"].CFrame = CFrame.new(0.0200526, -0.0000000, -0.0425077, 1.0000000, -0.0000008, -0.0000007, 0.0000009, 1.0000000, -0.0000001, 0.0000007, 0.0000001, 1.0000000) B["Page4"].Parent = B["Root"]
  B["Page5"] = Instance.new("Bone") B["Page5"].Name = "Page5" B["Page5"].CFrame = CFrame.new(0.0200526, -0.0000000, -0.0425077, 1.0000000, -0.0000008, -0.0000007, 0.0000009, 1.0000000, -0.0000001, 0.0000007, 0.0000001, 1.0000000) B["Page5"].Parent = B["Root"]
  B["Page6"] = Instance.new("Bone") B["Page6"].Name = "Page6" B["Page6"].CFrame = CFrame.new(0.0200526, -0.0000000, -0.0425077, 1.0000000, -0.0000008, -0.0000007, 0.0000009, 1.0000000, -0.0000001, 0.0000007, 0.0000001, 1.0000000) B["Page6"].Parent = B["Root"]
  local n = 0 for _, x in p:GetDescendants() do if x:IsA("Bone") then n += 1 end end
  table.insert(rep, "ChainedLedger.Ledger: " .. n .. " bones, skinned " .. tostring(p.HasSkinnedMesh)) end end
do local p = st:FindFirstChild("CrowMantle") and st["CrowMantle"]:FindFirstChild("MantleCrows")
  if not p then table.insert(rep, "CrowMantle.MantleCrows missing") else
  for _, x in p:GetChildren() do if x:IsA("Bone") then x:Destroy() end end
  local B = {}
  B["Root"] = Instance.new("Bone") B["Root"].Name = "Root" B["Root"].CFrame = CFrame.new(0.0003612, -0.2240345, -0.0569922, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["Root"].Parent = p
  B["H0"] = Instance.new("Bone") B["H0"].Name = "H0" B["H0"].CFrame = CFrame.new(0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["H0"].Parent = B["Root"]
  B["BodyA"] = Instance.new("Bone") B["BodyA"].Name = "BodyA" B["BodyA"].CFrame = CFrame.new(-0.8600000, 0.1528968, 0.0300000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["BodyA"].Parent = B["H0"]
  B["HeadA"] = Instance.new("Bone") B["HeadA"].Name = "HeadA" B["HeadA"].CFrame = CFrame.new(-0.0246999, 0.1320000, -0.1162039, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 0.9999999, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["HeadA"].Parent = B["BodyA"]
  B["LidLA"] = Instance.new("Bone") B["LidLA"].Name = "LidLA" B["LidLA"].CFrame = CFrame.new(-0.0501531, 0.1038400, -0.0370216, 0.9781476, 0.2079117, -0.0000000, -0.0000000, 0.0000000, -1.0000001, -0.2079117, 0.9781477, -0.0000002) B["LidLA"].Parent = B["HeadA"]
  B["LidRA"] = Instance.new("Bone") B["LidRA"].Name = "LidRA" B["LidRA"].CFrame = CFrame.new(0.0307592, 0.1038400, -0.0542200, -0.9781476, -0.2079121, -0.0000011, 0.0000011, 0.0000000, -0.9999999, 0.2079122, -0.9781472, 0.0000003) B["LidRA"].Parent = B["HeadA"]
  B["TailA"] = Instance.new("Bone") B["TailA"].Name = "TailA" B["TailA"].CFrame = CFrame.new(0.0283592, -0.0070400, 0.1334193, 0.2079118, -0.9781477, 0.0000000, -0.0000000, -0.0000000, -1.0000001, 0.9781477, 0.2079120, -0.0000001) B["TailA"].Parent = B["BodyA"]
  B["WingLA"] = Instance.new("Bone") B["WingLA"].Name = "WingLA" B["WingLA"].CFrame = CFrame.new(-0.0712316, 0.1496000, -0.0388388, 0.2079116, -0.9781476, -0.0000000, -0.0000000, 0.0000000, -1.0000000, 0.9781477, 0.2079116, -0.0000000) B["WingLA"].Parent = B["BodyA"]
  B["WingRA"] = Instance.new("Bone") B["WingRA"].Name = "WingRA" B["WingRA"].CFrame = CFrame.new(0.0492762, 0.1496000, -0.0644535, 0.2079116, -0.9781476, -0.0000000, -0.0000000, 0.0000000, -1.0000000, 0.9781477, 0.2079116, -0.0000000) B["WingRA"].Parent = B["BodyA"]
  B["BodyB"] = Instance.new("Bone") B["BodyB"].Name = "BodyB" B["BodyB"].CFrame = CFrame.new(0.8600001, 0.1528968, -0.0100000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["BodyB"].Parent = B["H0"]
  B["HeadB"] = Instance.new("Bone") B["HeadB"].Name = "HeadB" B["HeadB"].CFrame = CFrame.new(0.0327457, 0.1320000, -0.1141979, 1.0000000, 0.0000000, 0.0000000, 0.0000000, 0.9999999, 0.0000000, 0.0000000, 0.0000000, 1.0000000) B["HeadB"].Parent = B["BodyB"]
  B["LidLB"] = Instance.new("Bone") B["LidLB"].Name = "LidLB" B["LidLB"].CFrame = CFrame.new(-0.0269021, 0.1038400, -0.0562336, 0.9612616, -0.2756375, -0.0000000, -0.0000001, 0.0000000, -1.0000000, 0.2756375, 0.9612617, -0.0000001) B["LidLB"].Parent = B["HeadB"]
  B["LidRB"] = Instance.new("Bone") B["LidRB"].Name = "LidRB" B["LidRB"].CFrame = CFrame.new(0.0526134, 0.1038400, -0.0334329, -0.9612616, 0.2756380, 0.0000003, -0.0000003, 0.0000000, -1.0000000, -0.2756380, -0.9612615, 0.0000001) B["LidRB"].Parent = B["HeadB"]
  B["TailB"] = Instance.new("Bone") B["TailB"].Name = "TailB" B["TailB"].CFrame = CFrame.new(-0.0375969, -0.0070400, 0.1311161, -0.2756371, -0.9612620, -0.0000001, 0.0000000, 0.0000000, -1.0000001, 0.9612619, -0.2756370, 0.0000001) B["TailB"].Parent = B["BodyB"]
  B["WingLB"] = Instance.new("Bone") B["WingLB"].Name = "WingLB" B["WingLB"].CFrame = CFrame.new(-0.0446601, 0.1496000, -0.0677339, -0.2756376, -0.9612616, 0.0000001, 0.0000000, 0.0000000, -1.0000000, 0.9612616, -0.2756376, 0.0000000) B["WingLB"].Parent = B["BodyB"]
  B["WingRB"] = Instance.new("Bone") B["WingRB"].Name = "WingRB" B["WingRB"].CFrame = CFrame.new(0.0737674, 0.1496000, -0.0337754, -0.2756372, -0.9612616, 0.0000000, 0.0000000, 0.0000000, -1.0000000, 0.9612617, -0.2756372, 0.0000000) B["WingRB"].Parent = B["BodyB"]
  local n = 0 for _, x in p:GetDescendants() do if x:IsA("Bone") then n += 1 end end
  table.insert(rep, "CrowMantle.MantleCrows: " .. n .. " bones, skinned " .. tostring(p.HasSkinnedMesh)) end end
return table.concat(rep, NL)
