--[[
	Report Card (client). Controllers.Gui.StatsPanel   (M, or the top bar's Record button; replaces the old record)
	Three kit panels side by side:
	  Report Card   your name, race and tier, level and EXP, points to spend, and your three stats (Might, Grit, Wits)
	                with what each point gives and a +1 button
	  Abilities     what all of it adds up to in a fight and in class: damage, toughness, health, guard, stealth,
	                night power, healing, and every EXP bonus (a StatSheet)
	  Record        takedowns, attendance, discipline, and where your bonuses come from (clan, race, traits, gear,
	                snack) (a StatSheet)
	Data: ReplicatedStorage.NHProgress (Get / Spend / Updated) and your profile (StateController).
	API: Toggle(on?), IsOpen()
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local Config = require(ReplicatedStorage.Config.Progression)

local Player = Players.LocalPlayer
local Theme = Kit.Theme
local C = Theme.Colors
local Fonts = Theme.Fonts
local GOOD = Color3.fromRGB(150, 205, 140)
local BAD = Color3.fromRGB(235, 120, 110)

local Shared = {}
local Local = {}
local Ui = nil
local Sheet = nil
local Busy = false

function Local.Remote(Name: string)
	local F = ReplicatedStorage:FindFirstChild(`NHProgress`)
	return F and F:FindFirstChild(Name)
end

-- the record half of the sheet (Progression.Sheet adds Name, Attendance, Discipline, Classes)
function Local.Profile()
	return Sheet and Sheet.Record or nil
end

function Local.Label(Parent: Instance, Text: string, Size: number, Props)
	local T = Kit.Text({ Text = Text; TextSize = Size; TextColor3 = C.Text; TextWrapped = true;
		TextXAlignment = Enum.TextXAlignment.Left; TextYAlignment = Enum.TextYAlignment.Top; Parent = Parent })
	for K, V in Props or {} do T[K] = V end
	return T
end

function Local.Pct(V: number?, Invert: boolean?): (string, Color3)
	V = V or 0
	if Invert then V = -V end
	if math.abs(V) < 1e-4 then return `\u{2014}`, C.TextDim end
	local P = math.abs(V) * 100
	local Num = if P < 9.95 and math.abs(P - math.floor(P + 0.5)) > 0.05 then string.format(`%.1f`, P) else tostring(math.floor(P + 0.5))
	return `{if V > 0 then `+` else `\u{2212}`}{Num}%`, if V > 0 then GOOD else BAD
end

function Local.Build()
	local G = Instance.new(`ScreenGui`)
	G.Name = `NHReportCard`
	G.ResetOnSpawn = false
	G.DisplayOrder = 12
	G.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	G.Enabled = false
	G.Parent = Player:WaitForChild(`PlayerGui`)
	Kit.AutoScale(G)
	local Row = Instance.new(`Frame`)
	Row.Name = `Row`
	Row.BackgroundTransparency = 1
	Row.AnchorPoint = Vector2.new(0.5, 0.5)
	Row.Position = UDim2.fromScale(0.5, 0.5)
	Row.Size = UDim2.fromOffset(1120, 620)
	Row.Parent = G
	local _, MainApi = Kit.Panel({ title = `Report Card`; Name = `Main`; Position = UDim2.fromOffset(0, 0); Size = UDim2.fromOffset(420, 620); Parent = Row })
	Ui = { Gui = G; Row = Row; Main = MainApi.Content }
end

function Local.Clear(Parent: Instance)
	for _, Ch in Parent:GetChildren() do if not Ch:IsA(`UIBase`) then Ch:Destroy() end end
end

function Local.Spend(StatId: string)
	if Busy then return end
	local R = Local.Remote(`Spend`)
	if not R then return end
	Busy = true
	local Ok, Done, New = pcall(R.InvokeServer, R, StatId, 1)
	Busy = false
	if Ok and Done and typeof(New) == `table` then
		Sheet = New
		pcall(Kit.PlaySound, `Confirm`)
		Local.Render()
	else
		pcall(Kit.PlaySound, `Reject`)
	end
end

function Local.RenderMain(Profile)
	local B = Ui.Main
	Local.Clear(B)
	local S = Sheet
	local Name = (Profile and Profile.Name ~= `` and Profile.Name) or Player.DisplayName
	Local.Label(B, Name, 30, { Font = Fonts.Title; Position = UDim2.fromOffset(10, 4); Size = UDim2.new(1, -20, 0, 36) })
	local R = S.RaceInfo
	local RaceLine = if R then `{R.Sub ~= `` and R.Sub or R.Race}  \u{00B7}  {R.Race}  \u{00B7}  {R.TierName or `Tier {R.Tier}`}` else (S.Race or `Human`)
	Local.Label(B, string.upper(RaceLine), 14, { Font = Fonts.Title; TextColor3 = if R and Theme.Rarity[R.Rarity] then Theme.Rarity[R.Rarity] else C.Gold;
		Position = UDim2.fromOffset(10, 42); Size = UDim2.new(1, -20, 0, 18) })
	Kit.Divider({ Position = UDim2.fromOffset(10, 64); Size = UDim2.new(1, -20, 0, 16); Parent = B })
	-- level + EXP
	Local.Label(B, `Level`, 16, { TextColor3 = C.TextDim; Position = UDim2.fromOffset(10, 88); Size = UDim2.fromOffset(80, 20) })
	Local.Label(B, tostring(S.Level), 40, { Font = Fonts.Title; TextColor3 = C.Gold; Position = UDim2.fromOffset(10, 106); Size = UDim2.fromOffset(90, 44) })
	local Frac = if S.Next > 0 then S.Exp / S.Next else 1
	Kit.Bar({ fraction = Frac; color = C.Gold; caption = if S.Next > 0 then `{S.Exp} / {S.Next} EXP` else `MAX LEVEL`; height = 22;
		Position = UDim2.fromOffset(104, 116); Size = UDim2.new(1, -116, 0, 22); Parent = B })
	local PtsCol = if S.Points > 0 then C.Crimson else C.TextDim
	Local.Label(B, if S.Points > 0 then `<b>{S.Points}</b> point{S.Points == 1 and `` or `s`} to spend` else `No points to spend  \u{00B7}  you get {Config.PointsPerLevel} each level`, 17,
		{ RichText = true; TextColor3 = PtsCol; Position = UDim2.fromOffset(10, 158); Size = UDim2.new(1, -20, 0, 22) })
	-- the three stats
	local Y = 186
	for _, St in Config.Stats do
		local _, CardApi = Kit.Panel({ Name = `Stat`; ornament = `thin`; Position = UDim2.fromOffset(4, Y); Size = UDim2.new(1, -8, 0, 104); Parent = B })
		local Cb = CardApi.Content
		local Val = S.Stats[St.Id] or 0
		Local.Label(Cb, St.Name, 24, { Font = Fonts.Title; Position = UDim2.fromOffset(6, 0); Size = UDim2.new(1, -150, 0, 28) })
		Local.Label(Cb, `{Val} / {Config.MaxStat}`, 18, { Font = Fonts.Title; TextColor3 = C.Gold; TextXAlignment = Enum.TextXAlignment.Right;
			AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -78, 0, 4); Size = UDim2.fromOffset(90, 24) })
		Local.Label(Cb, `<i>{St.Text}</i>`, 15, { RichText = true; TextColor3 = C.TextDim; Position = UDim2.fromOffset(6, 30); Size = UDim2.new(1, -84, 0, 20) })
		Local.Label(Cb, `Each point: {Config.Describe(St.Per)}`, 14, { TextColor3 = GOOD; Position = UDim2.fromOffset(6, 50); Size = UDim2.new(1, -84, 0, 34) })
		Kit.Button({ text = `+1`; style = `gold`; enabled = S.Points > 0 and Val < Config.MaxStat; Size = UDim2.fromOffset(64, 40);
			AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, -4, 0.5, 0); Parent = Cb; onClick = function() Local.Spend(St.Id) end })
		Y += 110
	end
	Local.Label(B, `<b>M</b>  Close`, 14, { RichText = true; TextColor3 = C.TextDim; Position = UDim2.new(0, 10, 1, -22); Size = UDim2.new(1, -20, 0, 18) })
end

function Local.Abilities()
	local E = Sheet.Effects or {}
	local function row(Label, Key, Invert)
		local T, Col = Local.Pct(E[Key], Invert)
		return { Label, T, Col }
	end
	local Health = 100 + math.floor(E.MaxHealth or 0)
	local Regen = E.LowHealthRegen or 0
	return {
		{ header = `In a fight`; rows = {
			{ `Max health`, tostring(Health), if Health > 100 then GOOD else C.Text };
			row(`Damage`, `DamageDealt`);
			row(`Toughness`, `DamageTaken`, true);
			row(`Guard`, `PostureGain`, true);
			row(`Night power`, `NightPower`);
			row(`Full-moon power`, `FullMoonPower`);
			row(`Damage by day`, `DamageByDay`);
			row(`Vs. the undead`, `DamageVsUndead`);
			row(`Vs. monsters`, `DamageVsMonster`);
			{ `Badly hurt`, if Regen > 0 then `{string.format(`%g`, math.floor((1 + Regen * 5) * 10 + 0.5) / 10)} HP/s` else `\u{2014}`, if Regen > 0 then GOOD else C.TextDim };
			{ `Second chance`, if (E.DailyRevive or 0) > 0 then `Once a day` else `\u{2014}`, if (E.DailyRevive or 0) > 0 then GOOD else C.TextDim };
		} };
		{ header = `Sneaking`; rows = {
			row(`Stealth`, `Stealth`, true);
		} };
		{ header = `EXP bonuses`; rows = {
			row(`All EXP`, `AllExp`); row(`Class`, `ClassExp`); row(`Quest`, `QuestExp`); row(`Combat`, `CombatExp`);
			row(`Social`, `SocialExp`); row(`Stealth`, `StealthExp`); row(`Sport`, `SportExp`);
			row(`School hours`, `SchoolExp`); row(`At night`, `NightExp`);
		} };
	}
end

function Local.Record(Profile)
	local A = Profile and Profile.Attendance or {}
	local T = A.Totals or {}
	local D = Profile and Profile.Discipline or {}
	local Levels = { Clear = 0; Warning = 1; Detention = 2; Probation = 3; Suspension = 4 }
	local Lv = D.Level or `Clear`
	local Passes = 0
	for _, Cl in (Profile and Profile.Classes) or {} do Passes += (typeof(Cl) == `table` and Cl.Passes) or 0 end
	-- where it comes from: wrapped lines appended under the sheet (Local.AppendSources), a sheet row would cut them off
	local Sources = {}
	local function src(Label, Text, Col) if Text and Text ~= `` then table.insert(Sources, { Label, Text, Col or GOOD }) end end
	if Sheet.Clan then src(`Clan {Sheet.Clan}`, Sheet.ClanText) end
	if Sheet.RaceInfo then
		src(if Sheet.RaceInfo.Passive ~= `` then Sheet.RaceInfo.Passive else `Race`, Sheet.RaceInfo.Strengths)
		if Sheet.RaceInfo.Drawbacks and Sheet.RaceInfo.Drawbacks ~= `` then src(`Drawback`, Sheet.RaceInfo.Drawbacks, BAD) end
	end
	for _, Tr in Sheet.Traits or {} do src(Tr.Name, Tr.Text) end
	src(`Gear`, Sheet.GearText)
	src(`Snack`, Sheet.SnackText)
	Local.SourceLines = Sources
	return {
		{ header = `Fights`; rows = {
			{ `Students downed`, tostring(Sheet.Kills or 0) };
			{ `NPCs downed`, tostring(Sheet.NPCKills or Profile and Profile.NPCKills or 0) };
		} };
		{ header = `Attendance`; rows = {
			{ `Present`, tostring(T.Present or 0), GOOD };
			{ `Tardy`, tostring(T.Tardy or 0) };
			{ `Absent`, tostring(T.Absent or 0), if (T.Absent or 0) > 0 then BAD else C.Text };
			{ `Streak (best)`, `{A.Streak or 0} ({A.BestStreak or 0})` };
			{ `Lessons passed`, tostring(Passes) };
		} };
		{ header = `Discipline`; rows = {
			{ label = `Record`; pips = { filled = Levels[Lv] or 0; total = 4; color = C.Crimson } };
			{ `Standing`, Lv, if Lv == `Clear` then GOOD else BAD };
			{ `Points`, tostring(D.Points or 0) };
			{ `Detentions owed`, tostring(D.DetentionsOwed or 0) };
		} };
		{ header = `Where it comes from`; rows = {} };
	}
end

function Local.Render()
	if not (Ui and Sheet) then return end
	local Profile = Local.Profile()
	Local.RenderMain(Profile)
	for _, N in { `Abilities`, `Record` } do
		local Old = Ui.Row:FindFirstChild(N)
		if Old then Old:Destroy() end
	end
	local A = Kit.StatSheet({ title = `Abilities`; sections = Local.Abilities(); rowHeight = 24 })
	A.Name = `Abilities`
	A.Position = UDim2.fromOffset(432, 0)
	A.Size = UDim2.fromOffset(336, 620)
	A.Parent = Ui.Row
	local R = Kit.StatSheet({ title = `Record`; sections = Local.Record(Profile); rowHeight = 24 })
	R.Name = `Record`
	R.Position = UDim2.fromOffset(780, 0)
	R.Size = UDim2.fromOffset(340, 620)
	R.Parent = Ui.Row
	Local.AppendSources(R)
end

function Local.AppendSources(Sheet: Instance)
	local Rows = Sheet:FindFirstChild(`Rows`, true)
	if not Rows then return end
	local Lines = Local.SourceLines or {}
	if #Lines == 0 then Lines = { { `Nothing yet`, ``, C.TextDim } } end
	for I, L in Lines do
		local T = Kit.Text({ Text = `<b>{L[1]}</b>` .. (if L[2] ~= `` then `  <font color="#{L[3]:ToHex()}">{L[2]}</font>` else ``);
			TextSize = 15; TextWrapped = true; RichText = true; TextYAlignment = Enum.TextYAlignment.Top;
			AutomaticSize = Enum.AutomaticSize.Y; Size = UDim2.new(1, -8, 0, 18); LayoutOrder = 10000 + I; Parent = Rows })
		local Pad = Instance.new(`UIPadding`)
		Pad.PaddingLeft = UDim.new(0, 6)
		Pad.PaddingBottom = UDim.new(0, 4)
		Pad.Parent = T
	end
end

function Shared.IsOpen(): boolean return Ui ~= nil and Ui.Gui.Enabled end

function Shared.Toggle(On: boolean?)
	if not Ui then Local.Build() end
	if On == nil then On = not Ui.Gui.Enabled end
	if On and Player:GetAttribute(`InMainMenu`) == true then return end
	if On then
		local R = Local.Remote(`Get`)
		if R then
			local Ok, S = pcall(R.InvokeServer, R)
			if Ok and typeof(S) == `table` then Sheet = S end
		end
		if not Sheet then return end
		Local.Render()
		pcall(Kit.PlaySound, `Tick`)
	end
	Ui.Gui.Enabled = On
end

function Shared.OnStart()
	task.spawn(function()
		local F = ReplicatedStorage:WaitForChild(`NHProgress`, 30)
		if not F then return end
		F:WaitForChild(`Updated`).OnClientEvent:Connect(function(S)
			if typeof(S) ~= `table` then return end
			Sheet = S
			if Ui and Ui.Gui.Enabled then Local.Render() end
		end)
	end)
	task.spawn(function()
		while true do
			task.wait(0.5)
			if Ui and Ui.Gui.Enabled and Player:GetAttribute(`InMainMenu`) == true then Ui.Gui.Enabled = false end
		end
	end)
end

return Shared
