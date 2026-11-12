--[[
	Chatter (client). Controllers.World.Chatter   (owner, 2026-11-03: "random voice lines, but don't crowd the screen")
	Now and then an NPC near you says something in a small speech bubble: students, teachers, coaches, the hall
	monitor, the night custodian, the lunch lady, delinquents. Lines fit who they are (and a few change after dark).
	Students in a clique (attribute Clique, Config.Cliques) say their clique's lines about half the time (1.20).
	1.27: if the clique likes or dislikes you (your CliqueTier_<Id> attribute), they mostly say that clique's reaction
	lines to you instead; and fight lines from the server (NHCliques.Say: taunts, rallies) show as bubbles right away.

	Kept quiet on purpose:
	  - at most 2 bubbles on screen at once, and a new one only every 7 to 14 s
	  - only NPCs within 38 studs, on screen and not behind a wall
	  - the same NPC won't speak again for 40 s
	  - nothing in the main menu, while a dialogue is open, or in cinematic view (it hides every gui anyway)
	Each bubble is local to you (nothing is sent over the network): the kit's ink panel with a gold hairline and an
	italic Garamond line, fading in and out. Reduce Motion: no rise, just a fade.
]]

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local TweenService = game:GetService(`TweenService`)

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local SchoolTime = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`SchoolTime`))
local Cliques = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`Cliques`)) -- each clique's own lines (1.20)

local Player = Players.LocalPlayer
local Theme = Kit.Theme
local C = Theme.Colors

local MAX_ON_SCREEN = 2
local RANGE = 38
local GAP = { 7, 14 }       -- seconds between new lines
local PER_NPC = 40          -- seconds before the same NPC speaks again
local FOLDERS = { `Live`, `NHSchedule`, `NHAmbient`, `NHConcession` }
local CLIQUE_KINDS = { Student = true; Delinquent = true; Gym = true; Thinker = true; Slacker = true; Detention = true } -- not staff

local LINES = {
	Student = {
		`Did you finish the chemistry homework?`, `I swear the portraits moved again.`, `Detention's in Room 106, right?`,
		`Who keeps carving names in the desks?`, `I heard the Archive's off limits after dark.`, `Lunch better not be stew again.`,
		`Don't look at the hall monitor. Just walk.`, `My locker smells like candle wax.`, `Are you going to the match?`,
		`The bell's always a minute late.`, `The east wing gives me chills.`, `I'm so tired of History.`,
		`Who's the new kid?`, `Ravens are winning this year.`,
	};
	StudentNight = {
		`We shouldn't be out this late.`, `Did you hear that howl?`, `The moon's huge tonight.`, `Walk faster.`,
		`I hate the halls after dark.`, `Something's moving by the boiler.`,
	};
	Teacher = {
		`Walk, don't run.`, `Homework on my desk by morning.`, `Mind the bell.`, `Back to class, all of you.`,
		`Who left this candle burning?`, `Ink on the floors again...`,
	};
	Coach = {
		`Hustle!`, `Again! From the top!`, `Eyes up, hands ready.`, `Hydrate, then run it back.`,
		`That's a tryout, not a nap.`, `Hold the line!`,
	};
	Monitor = {
		`Passes, please.`, `Keep it moving.`, `No loitering.`, `I'm watching you.`, `Walk. Don't run.`, `Where's your next class?`,
	};
	Custodian = {
		`Mind the wet floor.`, `Same mess every night...`, `The boiler's restless.`, `Lights out soon.`, `Who tracked mud in here?`,
	};
	Lunch = {
		`Next!`, `Stew or bread?`, `Hot plates, careful.`, `No cutting the line.`, `Exact change, please.`,
	};
	Delinquent = {
		`What are you looking at?`, `Lost, first-year?`, `This is our lot.`, `Keep walking.`, `Got any yen?`, `Wrong turn, kid.`,
	};
	Gym = { `...nineteen... twenty...`, `Feel the burn.`, `One more set.`, `Coach is watching.` };
	Napping = { `Zzz...`, `Five more minutes...`, `mm... not now...` };
	Barber = { `Hold still.`, `Just a trim?`, `You've got a cowlick.` };
	Detention = { `I didn't even do anything.`, `How long is this?`, `I'm writing lines till midnight.` };
	Slacker = { `Don't tell anyone I'm in here.`, `Best sofa in the building.` };
	Thinker = { `Hmm...`, `There's a pattern here somewhere.`, `Quiet, I'm thinking.` };
}

-- who's speaking (by name, folder and attributes)
local function kindOf(M: Model): string?
	local N = M.Name
	if N == `Parry` or N == `Attacking` or N:find(`Dummy`) or M:GetAttribute(`NHWatcher`) then return nil end
	if N:find(`^Delinquent`) or M:GetAttribute(`NHDelinquent`) then return `Delinquent` end
	if N:find(`^Coach`) then return `Coach` end
	if N == `Hall Monitor` then return `Monitor` end
	if N:find(`Custodian`) then return `Custodian` end
	if M.Parent and M.Parent.Name == `NHConcession` then return `Lunch` end
	if N:find(`^Mr%.`) or N:find(`^Mrs%.`) or N:find(`^Ms%.`) then return `Teacher` end
	if M.Parent and M.Parent.Name == `NHAmbient` then
		if N:find(`up kid`) or N == `Gym regular` then return `Gym` end
		if N:find(`Napping`) then return `Napping` end
		if N == `Barber` then return `Barber` end
		if N:find(`Detention`) then return `Detention` end
		if N:find(`slacker`) then return `Slacker` end
		if N == `Thinker` then return `Thinker` end
	end
	return `Student`
end

local function night(): boolean
	local Clock = ReplicatedStorage:FindFirstChild(`SchoolClock`)
	local Epoch = Clock and Clock:GetAttribute(`Epoch`)
	if typeof(Epoch) ~= `number` then return false end
	local Ok, S = pcall(SchoolTime.GetState, Epoch, workspace:GetServerTimeNow())
	local H = Ok and S and S.MinuteOfDay and S.MinuteOfDay / 60
	return H ~= nil and (H >= 20 or H < 6)
end

local Shared = {}
local Local = {}
local Spoke = {} :: { [Model]: number }
local Showing = {} :: { [BillboardGui]: boolean }
local NextAt = 0
local Gui: Folder? = nil -- (billboards go in a Folder: a BillboardGui inside a ScreenGui doesn't render)

function Local.Count(): number
	local N = 0
	for B in Showing do if B.Parent then N += 1 else Showing[B] = nil end end
	return N
end

function Local.Candidates(): { { Model: Model, Kind: string } }
	local Char = Player.Character
	local Root = Char and Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	local Cam = workspace.CurrentCamera
	if not (Root and Cam) then return {} end
	local Out = {}
	local Now = os.clock()
	for _, FName in FOLDERS do
		local F = workspace:FindFirstChild(FName)
		for _, M in (F and F:GetChildren()) or {} do
			local Head = M:IsA(`Model`) and M:FindFirstChild(`Head`) :: BasePart?
			local Hum = Head and M:FindFirstChildOfClass(`Humanoid`)
			-- (1.86.2) students with the NPC brain (NHBrain) say their own lines, with voices (Controllers.World.NpcLook)
			if Head and Hum and Hum.Health > 0 and not M:GetAttribute(`Downed`) and not M:GetAttribute(`NHBrain`) and not Players:GetPlayerFromCharacter(M)
				and (Head.Position - Root.Position).Magnitude < RANGE and not (Spoke[M] and Now - Spoke[M] < PER_NPC) then
				local Kind = kindOf(M)
				local _, OnScreen = Cam:WorldToViewportPoint(Head.Position)
				if Kind and OnScreen then
					-- not behind a wall: a ray from the camera to the head that hits nothing solid on the way
					local RP = RaycastParams.new()
					RP.FilterType = Enum.RaycastFilterType.Exclude
					RP.FilterDescendantsInstances = { Char, M }
					RP.RespectCanCollide = true
					local Dir = Head.Position - Cam.CFrame.Position
					if not workspace:Raycast(Cam.CFrame.Position, Dir, RP) then table.insert(Out, { Model = M; Kind = Kind }) end
				end
			end
		end
	end
	return Out
end

-- the bubbles' folder in PlayerGui (made again whenever it's gone: a respawn clears PlayerGui of anything but
-- ScreenGuis with ResetOnSpawn off, and a BillboardGui inside a ScreenGui doesn't render)
function Local.Folder(): Folder?
	if Gui and Gui.Parent then return Gui end
	local PG = Player:FindFirstChild(`PlayerGui`)
	if not PG then return nil end
	local G = PG:FindFirstChild(`NHChatter`) or Instance.new(`Folder`)
	G.Name = `NHChatter`
	G.Parent = PG
	Gui = G
	return G
end

function Local.Bubble(Head: BasePart, Text: string)
	local Gui = Local.Folder()
	if not Gui then return end
	local Reduced = false
	pcall(function() Reduced = Kit.ReducedMotion() end)
	local B = Instance.new(`BillboardGui`)
	B.Name = `NHChatter`
	B.Adornee = Head
	B.Size = UDim2.fromOffset(230, 60)
	-- above the head; above the name tag too, for NPCs that wear one (the cast's tags sit right over the head)
	local Tagged = false
	for _, D in (Head.Parent and Head.Parent:GetDescendants()) or {} do
		if D:IsA(`BillboardGui`) and D.Name ~= `NHChatter` and D.Enabled then Tagged = true break end
	end
	B.StudsOffset = Vector3.new(0, if Tagged then 4.3 else 2.7, 0)
	B.MaxDistance = RANGE + 8
	B.LightInfluence = 0
	B.ResetOnSpawn = false
	local Panel = Instance.new(`Frame`)
	Panel.AnchorPoint = Vector2.new(0.5, 1)
	Panel.Position = UDim2.new(0.5, 0, 1, if Reduced then 0 else 6)
	Panel.Size = UDim2.fromOffset(0, 0)
	Panel.AutomaticSize = Enum.AutomaticSize.XY
	Panel.BackgroundColor3 = C.Ink
	Panel.BackgroundTransparency = 1
	Panel.Parent = B
	local Corner = Instance.new(`UICorner`)
	Corner.CornerRadius = UDim.new(0, 8)
	Corner.Parent = Panel
	local Stroke = Instance.new(`UIStroke`)
	Stroke.Color = C.GoldDeep
	Stroke.Thickness = 1
	Stroke.Transparency = 1
	Stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	Stroke.Parent = Panel
	local Pad = Instance.new(`UIPadding`)
	Pad.PaddingLeft, Pad.PaddingRight = UDim.new(0, 10), UDim.new(0, 10)
	Pad.PaddingTop, Pad.PaddingBottom = UDim.new(0, 5), UDim.new(0, 6)
	Pad.Parent = Panel
	local L = Instance.new(`TextLabel`)
	L.BackgroundTransparency = 1
	L.AutomaticSize = Enum.AutomaticSize.XY
	L.Size = UDim2.fromOffset(0, 0)
	local F = Font.fromEnum(Theme.Fonts.Body)
	F.Style = Enum.FontStyle.Italic
	L.FontFace = F
	L.TextSize = 16
	L.TextColor3 = C.Text
	L.TextTransparency = 1
	L.TextWrapped = false
	L.Text = Text
	L.Parent = Panel
	local Max = Instance.new(`UISizeConstraint`)
	Max.MaxSize = Vector2.new(210, 200)
	Max.Parent = L
	L.TextWrapped = true
	B.Parent = Gui
	Showing[B] = true
	local function tw(I, T, P) TweenService:Create(I, TweenInfo.new(T, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), P):Play() end
	tw(Panel, 0.25, { BackgroundTransparency = 0.18; Position = UDim2.new(0.5, 0, 1, 0) })
	tw(Stroke, 0.25, { Transparency = 0.4 })
	tw(L, 0.25, { TextTransparency = 0 })
	local Hold = math.clamp(2.2 + #Text * 0.05, 2.6, 5)
	task.delay(Hold, function()
		if not B.Parent then return end
		tw(Panel, 0.4, { BackgroundTransparency = 1 })
		tw(Stroke, 0.4, { Transparency = 1 })
		tw(L, 0.4, { TextTransparency = 1 })
		task.delay(0.45, function() B:Destroy() Showing[B] = nil end)
	end)
end

function Local.Cinematic(): boolean
	local Ok, On = pcall(function()
		return require(script.Parent.Parent:WaitForChild(`Gui`):WaitForChild(`Cinematic`)).IsOn()
	end)
	return Ok and On == true
end

function Local.Step()
	if Player:GetAttribute(`InMainMenu`) == true or Player:GetAttribute(`InDialogue`) == true then return end
	if Local.Cinematic() then return end
	local Now = os.clock()
	if Now < NextAt or Local.Count() >= MAX_ON_SCREEN then return end
	local List = Local.Candidates()
	NextAt = Now + GAP[1] + math.random() * (GAP[2] - GAP[1])
	if #List == 0 then return end
	local Pick = List[math.random(1, #List)]
	local Kind = Pick.Kind
	if Kind == `Student` and night() and math.random() < 0.6 then Kind = `StudentNight` end
	local Pool = LINES[Kind] or LINES.Student
	local Clique = Pick.Model:GetAttribute(`Clique`)
	local Def = Clique and Cliques.Defs[Clique]
	if Def and CLIQUE_KINDS[Pick.Kind] then
		-- (1.27) how this clique feels about you picks the line most of the time (Neutral keeps their usual talk)
		local Tier = Player:GetAttribute(`CliqueTier_{Clique}`)
		local React = Def.Reactions and Tier and Def.Reactions[Tier]
		if React and math.random() < 0.7 then
			Pool = React
		elseif Def.Lines and math.random() < 0.5 then
			Pool = Def.Lines
		end
	end
	Spoke[Pick.Model] = Now
	Local.Bubble(Pick.Model.Head, Pool[math.random(1, #Pool)])
end

function Shared.OnStart()
	Player:WaitForChild(`PlayerGui`)
	Local.Folder()
	task.spawn(function()
		local F = ReplicatedStorage:WaitForChild(`NHCliques`, 60)
		local Say = F and F:WaitForChild(`Say`, 30)
		if not Say then return end
		Say.OnClientEvent:Connect(function(Model, Text)
			if typeof(Model) ~= `Instance` or typeof(Text) ~= `string` or Local.Cinematic() then return end
			local Head = Model:FindFirstChild(`Head`)
			if Head and Head:IsA(`BasePart`) then
				Spoke[Model] = os.clock()
				pcall(Local.Bubble, Head, Text)
			end
		end)
	end)
	NextAt = os.clock() + 6
	task.spawn(function()
		while true do
			task.wait(1)
			local Ok, Err = pcall(Local.Step)
			if not Ok then warn(`[Chatter] {Err}`) task.wait(5) end
			-- forget speakers that are gone
			for M in Spoke do if not M.Parent then Spoke[M] = nil end end
		end
	end)
end

return Shared
