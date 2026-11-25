-- factions_play (chat-factions-ui, Client, Play): the rebuilt Factions panel. Toggle(true) opens it with every section,
-- the bars end at their values, the pips match each rank, Equip sends SocialAction, Toggle(false) hides it, and with
-- reduced motion everything is at its end state at once.
local P = game.Players.LocalPlayer
local F = require(P.PlayerScripts.Controllers.Gui.FactionsPanel)
local SC = require(P.PlayerScripts.Controllers.StateController)
local Cfg = require(game.ReplicatedStorage.Config.Factions)
local T = F.ForTests
if not T then return "FAIL no FactionsPanel.ForTests" end
local Fails, Notes = {}, {}
local function Ok(Cond, What) if not Cond then table.insert(Fails, What) end end

local function checkBody(Body: Instance, Label: string)
	local Profile = SC.GetProfile(false)
	local Social = Profile and Profile.Social or {}
	for _, N in { "Reputation", "Vigil", "CrimsonCourt", "Titles", "Rumours" } do
		Ok(Body:FindFirstChild(N, true) ~= nil, Label .. ": missing " .. N)
	end
	for _, D in Body:GetDescendants() do
		if D.Name == "Bar" and D:GetAttribute("Value") ~= nil and D:FindFirstChild("Fill") then
			local Want = math.clamp(D:GetAttribute("Value"), 0, 1)
			Ok(math.abs(D.Fill.Size.X.Scale - Want) < 0.002, ("%s: a bar at %.3f, want %.3f"):format(Label, D.Fill.Size.X.Scale, Want))
		end
	end
	for _, Id in { "Vigil", "CrimsonCourt" } do
		local Card = Body:FindFirstChild(Id, true)
		local Pips = Card and Card:FindFirstChild("Pips")
		local Rank = Social.Factions and Social.Factions[Id] and Social.Factions[Id].Rank or "Outsider"
		local Want = 1
		for I, R in Cfg.Ranks do if R.Name == Rank then Want = I end end
		local Lit, All = 0, 0
		if Pips then
			for _, Q in Pips:GetChildren() do
				if Q:IsA("Frame") then
					All += 1
					if Q.BackgroundColor3 == Cfg.Factions[Id].Color then Lit += 1 end
				end
			end
		end
		Ok(All == #Cfg.Ranks, ("%s: %s has %d pips, want %d"):format(Label, Id, All, #Cfg.Ranks))
		Ok(Lit == Want, ("%s: %s pips lit %d, rank %s wants %d"):format(Label, Id, Lit, Rank, Want))
	end
end

-- 1. animated open: once it has settled, everything is at its end state
F.Toggle(true)
task.wait(3)
local U = T.Ui()
if not U then return "FAIL the panel isn't built" end
Ok(U.Panel.Visible, "Toggle(true) left it hidden")
checkBody(U.Body, "animated")

-- 2. Equip sends SocialAction (the send is caught, not passed on)
local Packets = require(game.ReplicatedStorage.Remotes.Packets)
local Got = nil
local Hooked, Old = pcall(function() return Packets.SocialAction.Fire end)
if Hooked and pcall(function() Packets.SocialAction.Fire = function(_, D) Got = D end end) then
	T.Equip("Night Owl", false)
	Packets.SocialAction.Fire = Old
	Ok(Got and Got.Action == "EquipTitle" and Got.Title == "Night Owl", "Equip didn't send EquipTitle")
	T.Equip("Night Owl", true)
else
	table.insert(Notes, "Equip not checked: Packets.SocialAction can't be hooked")
end

-- 3. close
F.Toggle(false)
task.wait(0.5)
Ok(not U.Panel.Visible, "Toggle(false) left it showing")

-- 4. reduced motion: open again, everything at its end state at once
local WasReduced = P:GetAttribute("NHReducedMotion")
P:SetAttribute("NHReducedMotion", true)
F.Toggle(true)
checkBody(U.Body, "reduced")
F.Toggle(false)
P:SetAttribute("NHReducedMotion", WasReduced)
Ok(not U.Panel.Visible, "reduced Toggle(false) left it showing")
return (if #Fails == 0 then "PASS factions_play" else "FAIL " .. table.concat(Fails, "; ")) .. (if #Notes > 0 then " | " .. table.concat(Notes, "; ") else "")
