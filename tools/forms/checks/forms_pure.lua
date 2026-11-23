-- forms_pure (race transformations, Task 1): Config.Forms, Functions.Forms and the Lineage Look slots. Edit VM, pure.
local RS = game:GetService("ReplicatedStorage")
local okF, Forms = pcall(require, RS.Functions:FindFirstChild("Forms"))
local okC, Cfg = pcall(require, RS.Config:FindFirstChild("Forms"))
local okL, Lineage = pcall(require, RS.Lineage)
if not (okF and okC and okL) then return "FAIL modules: Functions.Forms " .. tostring(okF) .. ", Config.Forms " .. tostring(okC) .. ", Lineage " .. tostring(okL) end
local Fails, N = {}, 0
local function Ok(C, What) N += 1 if not C then table.insert(Fails, What) end end
local function has(list, v) return table.find(list or {}, v) ~= nil end

-- the Look slots per race
local VS, WS, GS, RS_ = Lineage.LookSlots.Vampire, Lineage.LookSlots.Werewolf, Lineage.LookSlots.Ghoul, Lineage.LookSlots.Wraith
for _, S in { "FormDirection", "WingStyle", "WingPalette", "WingFinish", "WingSize", "HornStyle", "HornFinish", "HornTip" } do Ok(has(VS, S), "Vampire slot " .. S) end
Ok(has(VS, "Ears"), "Vampire keeps Ears")
Ok(has(WS, "FormDirection") and not has(WS, "WingStyle") and not has(WS, "HornStyle"), "Werewolf: direction only, no wings or horns")
Ok(has(WS, "Fur") and has(WS, "Tail"), "Werewolf keeps Fur and Tail")
Ok(has(GS, "WingStyle") and has(GS, "HornStyle"), "Ghoul: wings and horns")
Ok(has(RS_, "WingStyle") and not has(RS_, "HornStyle"), "Wraith: wings, no horns (heads clear)")
Ok(Lineage.LookSlots.Human == nil or not has(Lineage.LookSlots.Human, "FormDirection"), "Humans stay untransformed")
Ok(Lineage.SlotNames.WingStyle ~= nil and Lineage.SlotNames.FormDirection ~= nil, "slot names")

-- allowed styles (spec §6) and tiers (I defaults, II two more, III the rest)
Ok(Lineage.LookOption("Vampire", "WingStyle", "Fallen") ~= nil, "Vampire may wear Fallen")
Ok(Lineage.LookOption("Ghoul", "WingStyle", "Nocturne") == nil, "Ghoul may not wear Nocturne")
Ok(Lineage.LookOption("Wraith", "WingStyle", "Rime") ~= nil, "Wraith may wear Rime")
Ok(Lineage.LookOption("Vampire", "HornStyle", "Wendigo") == nil, "Vampire may not wear Wendigo")
Ok(Lineage.LookOption("Ghoul", "HornStyle", "Thorn") ~= nil, "Ghoul may wear Thorn")
Ok(Lineage.LookOption("Vampire", "WingStyle", "Auto").Tier == 1, "Auto is Tier I")
Ok(Lineage.LookOption("Vampire", "WingStyle", "Wyrm").Tier == 1, "a direction's default style is Tier I")
Ok(Lineage.LookOption("Vampire", "WingStyle", "Tattered").Tier == 2 and Lineage.LookOption("Vampire", "WingStyle", "Fallen").Tier == 2, "two more at Tier II")
Ok(Lineage.LookOption("Vampire", "HornStyle", "Bull").Tier == 3, "the rest at Tier III")
Ok(Lineage.LookOption("Vampire", "FormDirection", "2").Tier == 1, "both directions at Tier I")
for _, Opts in Lineage.Looks.Vampire do Ok(Opts[1].Tier == 1, "every slot's first option is Tier I") end

-- ResolveLooks falls back to the first Tier I option above your tier
local R1 = Lineage.ResolveLooks({ Race = "Vampire", Tier = 1, Looks = { WingStyle = "Fallen", FormDirection = "2" } })
Ok(R1.WingStyle.Id == "Auto", "Tier I with Fallen saved resolves to Auto, got " .. tostring(R1.WingStyle.Id))
Ok(R1.FormDirection.Id == "2", "direction kept")
local R3 = Lineage.ResolveLooks({ Race = "Vampire", Tier = 3, Looks = { WingStyle = "Fallen" } })
Ok(R3.WingStyle.Id == "Fallen", "Tier III keeps Fallen")

-- Forms.Resolve: the concrete pieces
local function ids(race, looks) return Forms.Resolve(race, looks) end
local V1 = ids("Vampire", {})
Ok(V1 and V1.Direction == "1" and V1.Wings and V1.Wings.Style == "Nocturne" and V1.Wings.Palette == "Wine" and V1.Wings.Finish == "Obsidian", "V1 defaults")
Ok(V1 and V1.Horns == nil, "V1 has no horns by default")
local V2 = ids("Vampire", { FormDirection = "2" })
Ok(V2.Wings.Style == "Wyrm" and V2.Wings.Finish == "Bloodstone" and V2.Horns and V2.Horns.Style == "Demon" and V2.Horns.Tip == "Bloodstone", "V2 defaults")
local VC = ids("Vampire", { FormDirection = "1", WingStyle = "Fallen", WingPalette = "Raven", WingSize = "Grand", HornStyle = "Ram" })
Ok(VC.Wings.Style == "Fallen" and VC.Wings.Palette == "Raven" and math.abs(VC.Wings.Scale - 1.2) < 1e-6, "custom wings")
Ok(VC.Horns and VC.Horns.Style == "Ram" and VC.Horns.Finish ~= nil and VC.Horns.Tip ~= nil, "added horns get default finishes")
Ok(ids("Vampire", { FormDirection = "2", HornStyle = "None" }).Horns == nil, "None removes horns")
local G2 = ids("Ghoul", { FormDirection = "2" })
Ok(G2.Wings == nil and G2.Horns and G2.Horns.Style == "Thorn", "G2: no wings, the Thorn crown")
local G1 = ids("Ghoul", {})
Ok(G1.Wings and G1.Wings.Style == "Ossuary" and G1.Horns and G1.Horns.Style == "Wendigo", "G1: Ossuary wings, Wendigo antlers")
local W2 = ids("Werewolf", { FormDirection = "2" })
Ok(W2.Wings == nil and W2.Horns == nil and has(W2.Parts, "Mantle"), "W2: mantle, no wings or horns")
local R2 = ids("Wraith", { FormDirection = "2" })
Ok(R2.Wings.Style == "Rime" and R2.Horns == nil, "R2: Rime, head clear")
Ok(ids("Human", {}) == nil and ids("Priest", {}) == nil, "Humans and Priests: no form")
local Bad = ids("Ghoul", { WingStyle = "Nocturne", FormDirection = "9" })
Ok(Bad.Direction == "1" and Bad.Wings.Style == "Ossuary", "bad ids fall back to the defaults")

-- the owner's rules, in the data
local function walk(t, seen)
	seen = seen or {}
	if seen[t] then return true end
	seen[t] = true
	for k, v in t do
		local s = string.lower(tostring(k) .. " " .. (if type(v) == "string" then v else ""))
		if s:find("claw") or s:find("muzzle") or s:find("hood") then return false, s end
		if type(v) == "table" then local ok, w = walk(v, seen) if not ok then return false, w end end
	end
	return true
end
local Clean, Word = walk(Cfg)
Ok(Clean, "Config.Forms names no claw, muzzle or hood: " .. tostring(Word))
-- every style a race allows has a palette/finish table and a size
for _, S in { "Nocturne", "Wyrm", "Tattered", "Fallen", "Ossuary", "Wraithveil", "Rime" } do Ok(Cfg.WingStyles[S] ~= nil, "wing style " .. S) end
for _, S in { "Ram", "Demon", "Wendigo", "Thorn", "Broken", "Sovereign", "Bull" } do Ok(Cfg.HornStyles[S] ~= nil, "horn style " .. S) end
Ok(Cfg.WingSizes.Small == 0.8 and Cfg.WingSizes.Regular == 1 and Cfg.WingSizes.Grand == 1.2, "wing sizes")

return #Fails == 0 and ("PASS forms_pure (" .. N .. " checks)") or ("FAIL forms_pure\n" .. table.concat(Fails, "\n"))
