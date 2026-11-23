local P = game.Players.LocalPlayer
local PG = P.PlayerGui
local Seal = require(game.ReplicatedStorage.UI.Theme).Images.Seal
local Fails, Seen = {}, {}
local function Ok(C, W) if not C then table.insert(Fails, W) end end
local function Shown(G) local X = G while X and X:IsA("GuiObject") do if not X.Visible then return false end X = X.Parent end return true end
local function Rect(L)
	local B, P0, S = L.TextBounds, L.AbsolutePosition, L.AbsoluteSize
	local X = if L.TextXAlignment == Enum.TextXAlignment.Left then P0.X elseif L.TextXAlignment == Enum.TextXAlignment.Right then P0.X + S.X - B.X else P0.X + (S.X - B.X) / 2
	local Y = if L.TextYAlignment == Enum.TextYAlignment.Top then P0.Y elseif L.TextYAlignment == Enum.TextYAlignment.Bottom then P0.Y + S.Y - B.Y else P0.Y + (S.Y - B.Y) / 2
	return X, Y, X + B.X, Y + B.Y
end
local function Lum(C) local function f(v) return if v <= 0.03928 then v / 12.92 else ((v + 0.055) / 1.055) ^ 2.4 end return 0.2126 * f(C.R) + 0.7152 * f(C.G) + 0.0722 * f(C.B) end
for _, Name in { "Notifications", "NHCompass", "Dialogue", "NHEvidenceWall", "QuestJournal", "NHTopBar" } do
	local G = PG:FindFirstChild(Name)
	if not (G and G.Enabled) then continue end
	local Texts = {}
	for _, L in G:GetDescendants() do
		if (L:IsA("ImageLabel") or L:IsA("ImageButton")) and Shown(L) then Ok(L.Image ~= Seal, Name .. ": Seal at " .. L:GetFullName()) end
		if (L:IsA("TextLabel") or L:IsA("TextButton")) and L.Text ~= "" and Shown(L) and L.TextTransparency < 0.9 then
			Ok(L.TextSize >= 20, L:GetFullName() .. " size " .. L.TextSize) Ok(L.TextFits, L:GetFullName() .. " doesn't fit")
			local x0, y0, x1, y1 = Rect(L)
			for _, O in Texts do if x0 < O[3] - 2 and O[1] < x1 - 2 and y0 < O[4] - 2 and O[2] < y1 - 2 then table.insert(Fails, "overlap: " .. L:GetFullName() .. " / " .. O[5]) end end
			table.insert(Texts, { x0, y0, x1, y1, L:GetFullName() })
			local A = L.Parent
			while A and A:IsA("GuiObject") and A:GetAttribute("QcBox") == nil do A = A.Parent end
			if A and A:IsA("GuiObject") then
				local b = string.split(A:GetAttribute("QcBox"), ",")
				local ax, ay, aw, ah = A.AbsolutePosition.X, A.AbsolutePosition.Y, A.AbsoluteSize.X, A.AbsoluteSize.Y
				Ok(x0 >= ax + tonumber(b[1]) * aw - 2 and x1 <= ax + tonumber(b[3]) * aw + 2 and y0 >= ay + tonumber(b[2]) * ah - 2 and y1 <= ay + tonumber(b[4]) * ah + 2, "outside its art box: " .. L:GetFullName())
				local Bg = A:GetAttribute("QcBg")
				if typeof(Bg) == "Color3" then
					local l1, l2 = Lum(L.TextColor3), Lum(Bg)
					local R = (math.max(l1, l2) + 0.05) / (math.min(l1, l2) + 0.05)
					Ok(R >= (if L.TextSize > 22 then 3 else 4.5), ("contrast %.1f: %s"):format(R, L:GetFullName()))
				end
			end
		end
	end
	table.insert(Seen, Name .. " " .. #Texts)
end
return (#Fails == 0 and "PASS qc_fit (" or "FAIL qc_fit (") .. table.concat(Seen, ", ") .. ")\n" .. table.concat(Fails, "\n")
