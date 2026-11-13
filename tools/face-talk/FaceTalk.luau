--[[
	FaceTalk (client, 2.0.0): painted faces that talk.

	Owner: "I want you also to so create some talking facial expressions so the faces are super animated and talk when
	they type or speak"

	  * Who talks:
	      - a player who sends a chat message (TextChatService.MessageReceived): their face talks the message;
	      - a student who says a line (NHSay / NHSayAt on the model, the same signal Controllers.World.NpcLook uses
	        for the bubble and the voice): their face talks it, starting with the bubble and the voice.
	  * Mouth shapes (visemes), from the text, letter by letter (about 14 a second): vowels open the mouth (A / I wide
	    open, E wide, O round, U / W a pucker), M B P press the lips, F V put the teeth on the lip, L and TH show the
	    tongue, other consonants show the teeth together; spaces and commas close it, . ! ? close it a little longer,
	    and "..." holds it shut. Between lines the face's own mouth is back.
	  * Expressions: neutral, happy, angry, surprised, worried, smug. Each one has its own mouths, moves the brows
	    (every face strip's brow slice is moved to a curve and turned to its slope, so the brow bends smoothly) and
	    narrows the eyes (a squint lid at two levels, clipped to the eye's own outline). "!" and "?" lift the brows at
	    the end of a line. Blinks carry on (Controllers.Character.EyeBlink).
	      - a student: the line's attitude (NHSayMood: Hostile -> angry, Wary -> worried, Respected / Friendly ->
	        happy), else their mood (NHMood), else the text;
	      - a player: the text (":)" "lol" -> happy, ":(" "sorry" -> worried, ";)" -> smug, "?!" "what" "wow" ->
	        surprised, shouting in capitals -> angry).
	  * Left alone: a sewn or stitched race mouth stays shut; a transformed face keeps its form's mouth and eyes (the
	    brows still move); a face with no painted plate.
	  * Cheap: only faces within RANGE studs of the camera and in front of it animate (a line still runs out on time,
	    unseen); the frames only change images when the shape changes.
	Layers, per face strip (UI.Appearance's NHFacePlate SurfaceGuis): NHTalkMouth (the mouth atlas band, the face's
	own NHMouth hidden while it shows), NHTalkLid (over the eyes, tinted to the skin like EyeBlink's lids), NHTalkBrow
	(a copy of NHBrows, moved and turned; the original hidden). All of them go when the line ends, or the moment the
	face is rebuilt (UI.Appearance clears the strips).
	Art: ReplicatedStorage.UI.FaceTalkArt (tools/face-talk/build.py: atlases of mouth and lid bands).
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local TextChatService = game:GetService(`TextChatService`)

local UI = ReplicatedStorage:WaitForChild(`UI`)
local EyeArt = require(UI:WaitForChild(`EyeArt`))
local Art = require(UI:WaitForChild(`FaceTalkArt`))

local Shared = {}

local RANGE = 70        -- studs from the camera: nearer faces animate
local MAX_FACES = 10    -- at most this many talking faces animate at once (the nearest)
local CPS = 14          -- letters a second
local RAMP = 0.15       -- s: brows and lids ease in and out
local EMPH = 1.25       -- the brows' lift at the end of a "!" or "?" line
local SHUT = { race_stitched = true; race_sewn = true } -- mouths that stay shut

local Faces = {} :: { [Model]: any }

-- ------------------------------------------------------------------ text -> mouth shapes
function Shared.Visemes(Text: string): { { any } }
	local T = string.lower(Text)
	local Out = {}
	local Step = 1 / CPS
	local i, n = 1, #T
	local function add(V, D) table.insert(Out, { V, D }) end
	while i <= n do
		local c = string.sub(T, i, i)
		local two = string.sub(T, i, i + 1)
		if string.sub(T, i, i + 2) == `...` then add(`rest`, 0.6) i += 3 continue end
		if string.sub(T, i, i + 2) == "\u{2026}" then add(`rest`, 0.6) i += 3 continue end -- the ellipsis character (3 bytes)
		if two == `th` then add(`L`, Step) i += 2 continue end
		if two == `oo` or two == `ou` or two == `ew` then add(`UW`, Step * 1.6) i += 2 continue end
		if two == `ee` or two == `ea` then add(`E`, Step * 1.6) i += 2 continue end
		if c == `a` or c == `i` then add(`AI`, Step * 1.4)
		elseif c == `e` then add(`E`, Step * 1.3)
		elseif c == `o` then add(`O`, Step * 1.4)
		elseif c == `u` or c == `w` or c == `q` then add(`UW`, Step * 1.2)
		elseif c == `y` then
			local nx = string.sub(T, i + 1, i + 1)
			add(if nx == `` or not string.match(nx, `%a`) then `E` else `CONS`, Step)
		elseif c == `m` or c == `b` or c == `p` then add(`MBP`, Step)
		elseif c == `f` or c == `v` then add(`FV`, Step)
		elseif c == `l` then add(`L`, Step)
		elseif string.match(c, `%a`) or c == `#` then add(`CONS`, Step * 0.8) -- # = a filtered word: it still talks
		elseif string.match(c, `%d`) then add(`AI`, Step * 1.2)
		elseif c == ` ` then add(`rest`, Step * 0.6)
		elseif c == `,` or c == `;` or c == `:` then add(`rest`, 0.22)
		elseif c == `.` or c == `!` or c == `?` then add(`rest`, 0.32)
		end
		i += 1
	end
	local Merged = {}
	for _, E in Out do
		local Last = Merged[#Merged]
		if Last and Last[1] == E[1] then Last[2] += E[2] * 0.6 else table.insert(Merged, { E[1], E[2] }) end
	end
	table.insert(Merged, { `rest`, 0.3 })
	return Merged
end

-- ------------------------------------------------------------------ the expression a line carries
local ATTITUDE = { Hostile = `angry`; Wary = `worried`; Respected = `happy`; Friendly = `happy`; Admiring = `happy`;
	Smug = `smug`; Scared = `worried`; Surprised = `surprised`; Angry = `angry`; Happy = `happy` }
local MOOD = { Friendly = `happy`; Scared = `worried`; Uneasy = `worried`; Shy = `worried`; Wary = `worried`;
	Angry = `angry`; Hostile = `angry` }

-- Expr: an expression already known (a student's attitude or mood); else read from the text
function Shared.ExpressionOf(Text: string, Expr: string?): string
	if Expr and Art.Expr[Expr] then return Expr end
	local L = ` {string.lower(Text)} `
	local Letters, Caps = 0, 0
	for C in string.gmatch(Text, `%a`) do
		Letters += 1
		if string.match(C, `%u`) then Caps += 1 end
	end
	if Letters >= 4 and Caps / Letters > 0.7 then return `angry` end
	-- words match whole words ("hi" isn't in "this"); anything with a symbol matches as written (":)", "?!")
	local function has(...)
		for _, P in { ... } do
			if string.match(P, `^[%a ]+$`) then
				if string.find(L, `%f[%a]` .. P .. `%f[%A]`) then return true end
			elseif string.find(L, P, 1, true) then
				return true
			end
		end
		return false
	end
	if has(`shut up`, `get out`, `back off`, `go away`, `>:(`, `hate`, `stop it`) then return `angry` end
	if has(`?!`, `!?`, `wow`, `whoa`, `omg`, `what?`, `wait`, `no way`, `:o`) then return `surprised` end
	if has(`;)`, `heh`, `told you`, `obviously`, `of course`, `too easy`, `:p`) then return `smug` end
	if has(`:(`, `sorry`, `scared`, `help`, `uh oh`, `oh no`, `i think`, `maybe`) then return `worried` end
	if has(`:)`, `:d`, `lol`, `haha`, `xd`, `<3`, `thanks`, `thank you`, `yay`, `nice`, `welcome`, `hi`, `hey`, `!`) then
		return `happy`
	end
	if has(`...`) then return `worried` end -- trailing off, and nothing else to go on
	return `neutral`
end

-- ------------------------------------------------------------------ the face's parts
local function stripsOf(Plate: Instance)
	local Out = {}
	for _, SG in Plate:GetDescendants() do
		if SG:IsA(`SurfaceGui`) then table.insert(Out, SG) end
	end
	return Out
end

local function mouthKeyOf(Image: string): string?
	for K, V in EyeArt.MouthArt do
		if V == Image then return K end
	end
	return nil
end

-- what this face can do: lips (m / f), shut, transformed, the eye shape (for its lids)
local function survey(F)
	local Plate = F.Head:FindFirstChild(`NHFacePlate`)
	F.Plate = Plate
	F.Strips = Plate and stripsOf(Plate) or {}
	local Any = F.Strips[1]
	local Mouth = Any and Any:FindFirstChild(`NHMouth`)
	local Main = Any and Any:FindFirstChild(`NHEyesMain`)
	local Key = Mouth and mouthKeyOf(Mouth.Image)
	F.Form = (Any and Any:FindFirstChild(`NHFormFace`) ~= nil) or (Key ~= nil and not string.match(Key, `_[mf]$`) and
		not string.match(Key, `^race_`)) or F.Char:GetAttribute(`WolfForm`) == true
	F.Shut = Key ~= nil and SHUT[Key] == true
	F.NoMouth = Mouth == nil
	F.Lips = if Key and string.match(Key, `_f$`) then `f` else `m`
	F.Shape = Main and EyeArt.ShapeOfImage(Main.Image) or nil
	F.Version = Plate and Plate:GetAttribute(`V`)
end

local function clear(F)
	for _, SG in F.Strips or {} do
		if SG.Parent then
			for _, N in { `NHTalkMouth`, `NHTalkLid`, `NHTalkBrow` } do
				local X = SG:FindFirstChild(N)
				if X then X:Destroy() end
			end
			local M = SG:FindFirstChild(`NHMouth`)
			if M and M:GetAttribute(`NHTalkHid`) ~= nil then
				M.ImageTransparency = M:GetAttribute(`NHTalkHid`)
				M:SetAttribute(`NHTalkHid`, nil)
			end
			local B = SG:FindFirstChild(`NHBrows`)
			if B and B:GetAttribute(`NHTalkHid`) ~= nil then
				B.ImageTransparency = B:GetAttribute(`NHTalkHid`)
				B:SetAttribute(`NHTalkHid`, nil)
			end
		end
	end
	F.Shown = nil
	F.LidShown = nil
	F.BrowShown = nil
end

local function hide(L: ImageLabel)
	if L:GetAttribute(`NHTalkHid`) == nil then L:SetAttribute(`NHTalkHid`, L.ImageTransparency) end
	L.ImageTransparency = 1
end

-- a layer cut from an atlas band: same columns as Base (its strip's slice), rows Y0 .. Y0 + H of the face
local function bandLayer(SG: SurfaceGui, Base: ImageLabel, Name: string, Image: string, Row: number, Y0: number, H: number, Z: number)
	local L = SG:FindFirstChild(Name) :: ImageLabel?
	if not L then -- its place on the strip is set once; a new shape only changes the image and the band
		L = Instance.new(`ImageLabel`)
		L.Name = Name
		L.BackgroundTransparency = 1
		L.ImageRectSize = Vector2.new(Base.ImageRectSize.X, H)
		L.Size = UDim2.fromScale(Base.Size.X.Scale, H / 1024)
		L.Position = UDim2.fromScale(Base.Position.X.Scale, Y0 / 1024)
		L.ZIndex = Z
		L.Parent = SG
	end
	if L.Image ~= Image then L.Image = Image end
	L.ImageRectOffset = Vector2.new(Base.ImageRectOffset.X, Row)
	return L
end

local function showMouth(F, Vis: string)
	if F.Shut or F.Form or F.NoMouth then return end
	local Key = if Vis == `rest` and F.Expr == `neutral` then nil else `{F.Expr}/{Vis}/{F.Lips}`
	if Key == F.Shown then return end
	F.Shown = Key
	local Spot = Key and Art.Mouth.Keys[Key]
	for _, SG in F.Strips do
		local M = SG:FindFirstChild(`NHMouth`) :: ImageLabel?
		if not M then continue end
		if Spot then
			hide(M)
			bandLayer(SG, M, `NHTalkMouth`, Art.Mouth.Atlases[Spot[1] + 1], Spot[2], Art.Mouth.Y0, Art.Mouth.H, M.ZIndex)
		else
			local T = SG:FindFirstChild(`NHTalkMouth`)
			if T then T:Destroy() end
			if M:GetAttribute(`NHTalkHid`) ~= nil then
				M.ImageTransparency = M:GetAttribute(`NHTalkHid`)
				M:SetAttribute(`NHTalkHid`, nil)
			end
		end
	end
end

local function showLid(F, On: boolean)
	local E = Art.Expr[F.Expr]
	local Level = if E and E.Squint >= 0.33 then `Narrow` elseif E and E.Squint >= 0.15 then `Soft` else nil
	local Key = if On and Level and F.Shape and not F.Form then `{F.Shape}/{Level}` else nil
	if Key == F.LidShown then return end
	F.LidShown = Key
	local Spot = Key and Art.Lid.Keys[Key]
	for _, SG in F.Strips do
		local Main = SG:FindFirstChild(`NHEyesMain`) :: ImageLabel?
		if Spot and Main then
			local L = bandLayer(SG, Main, `NHTalkLid`, Art.Lid.Atlases[Spot[1] + 1], Spot[2], Art.Lid.Y0, Art.Lid.H, Main.ZIndex + 1)
			L.ImageColor3 = F.Head.Color
		else
			local T = SG:FindFirstChild(`NHTalkLid`)
			if T then T:Destroy() end
		end
	end
end

-- the brow's move (texels, + = down) at texel column X, for an expression at strength Amt
local function browDy(Kind: string, Amt: number, X: number): number
	local D = math.abs(X - 512)
	local Inner = math.clamp(1 - (D - 60) / 230, 0, 1)
	if Kind == `up` then return -Amt end
	if Kind == `inner_down` then return Amt * Inner - Amt * 0.3 end
	if Kind == `inner_up` then return -Amt * Inner + Amt * 0.15 end
	if Kind == `one_up` then return if X > 512 then -Amt else 0 end
	return 0
end

local function showBrows(F, K: number)
	local E = Art.Expr[F.Expr]
	local Kind, Amt = E and E.Brow or `flat`, (E and E.BrowAmt or 0) * K
	if F.Expr == `neutral` and F.Emph then Kind, Amt = `up`, 6 * K end
	local Sig = string.format(`%s%.1f`, Kind, Amt)
	if Sig == F.BrowShown then return end
	F.BrowShown = Sig
	local Flat = Kind == `flat` or math.abs(Amt) < 0.3
	local By = (Art.BrowY or 400) - 512
	for _, SG in F.Strips do
		local B = SG:FindFirstChild(`NHBrows`) :: ImageLabel?
		if not B then continue end
		local T = SG:FindFirstChild(`NHTalkBrow`) :: ImageLabel?
		if Flat then
			if T then T:Destroy() end
			if B:GetAttribute(`NHTalkHid`) ~= nil then
				B.ImageTransparency = B:GetAttribute(`NHTalkHid`)
				B:SetAttribute(`NHTalkHid`, nil)
			end
			continue
		end
		if not T then
			T = B:Clone()
			T.Name = `NHTalkBrow`
			T.Parent = SG
		end
		hide(B)
		T.ImageTransparency = B:GetAttribute(`NHTalkHid`) or 0
		local X0, W = B.ImageRectOffset.X, B.ImageRectSize.X
		local Xc = X0 + W / 2
		local Dy = browDy(Kind, Amt, Xc)
		local Slope = (browDy(Kind, Amt, Xc + 6) - browDy(Kind, Amt, Xc - 6)) / 12
		local Th = math.atan(Slope)
		-- turned about the brow (BrowY), not the label's middle: shift back what turning about the middle moves it
		local Dx = By * math.sin(Th)
		local DyRot = By * (1 - math.cos(Th))
		local CanW = W / math.max(B.Size.X.Scale, 1e-3) -- the canvas width in texels
		T.Rotation = math.deg(Th)
		T.Position = UDim2.fromScale(B.Position.X.Scale + Dx / CanW, (Dy + DyRot) / 1024)
	end
end

-- ------------------------------------------------------------------ talking
local function faceOf(Char: Model)
	local F = Faces[Char]
	local Head = Char:FindFirstChild(`Head`)
	if not (Head and Head:IsA(`BasePart`)) then return nil end
	if not F then
		F = { Char = Char; Head = Head }
		Faces[Char] = F
	end
	F.Head = Head
	return F
end

function Shared.Say(Char: Model?, Text: string?, Expr: string?)
	if not (Char and typeof(Text) == `string` and Text ~= ``) then return end
	local F = faceOf(Char)
	if not F then return end
	clear(F)
	survey(F)
	if not F.Plate then Faces[Char] = nil return end
	F.Expr = Shared.ExpressionOf(Text, Expr)
	F.Queue = Shared.Visemes(Text)
	local Total = 0
	for _, E in F.Queue do Total += E[2] end
	F.Total = Total
	F.T0 = os.clock()
	F.EmphLine = string.find(Text, `[!?]%s*$`) ~= nil
	F.Emph = false
end

local function finish(F)
	clear(F)
	Faces[F.Char] = nil
end

local function step()
	local Cam = workspace.CurrentCamera
	if not Cam then return end
	local Now = os.clock()
	-- the nearest MAX_FACES talking faces on screen are drawn; the rest run out their lines unseen
	local CamPos = Cam.CFrame.Position
	local Order = {}
	for Char, F in Faces do
		if F.Head and F.Head.Parent then table.insert(Order, { F, (F.Head.Position - CamPos).Magnitude }) end
	end
	table.sort(Order, function(A, B) return A[2] < B[2] end)
	local Rank = {}
	for I, E in Order do Rank[E[1]] = I end
	for Char, F in Faces do
		local T = Now - (F.T0 or Now)
		if not Char.Parent or not F.Head.Parent or T > (F.Total or 0) + RAMP then
			finish(F)
			continue
		end
		-- the face was rebuilt (new look, new plate): start its layers again
		local Plate = F.Head:FindFirstChild(`NHFacePlate`)
		local Gone = Plate ~= F.Plate or (F.Strips[1] and not F.Strips[1].Parent)
			or (F.Strips[1] and F.Strips[1]:FindFirstChild(`NHMouth`) == nil and not F.NoMouth)
		if Gone then
			clear(F)
			survey(F)
			if not F.Plate then finish(F) continue end
		end
		-- near and in front of the camera, or not drawn
		local V, OnScreen = Cam:WorldToViewportPoint(F.Head.Position)
		local Near = (F.Head.Position - CamPos).Magnitude <= RANGE and OnScreen and V.Z > 0 and (Rank[F] or 1) <= MAX_FACES
		if not Near then
			if F.Shown or F.LidShown or F.BrowShown then clear(F) end
			continue
		end
		-- which shape now
		local Acc, Vis = 0, `rest`
		for _, E in F.Queue do
			Acc += E[2]
			if T < Acc then Vis = E[1] break end
		end
		local Ending = T >= F.Total
		if Ending then Vis = `rest` end
		F.Emph = F.EmphLine and T > F.Total * 0.55
		-- ease the brows and lids in at the start and out at the end
		local K = math.clamp(T / RAMP, 0, 1) * math.clamp((F.Total + RAMP - T) / RAMP, 0, 1)
		if F.Emph then K *= EMPH end
		K = math.floor(K * 5 + 0.5) / 5 -- in fifths: a few image changes, not one a frame
		showMouth(F, if Ending then `rest` else Vis)
		showLid(F, K > 0.5)
		showBrows(F, K)
	end
end

-- ------------------------------------------------------------------ who talks
local function watchStudents(Name: string)
	task.spawn(function()
		local Folder = workspace:WaitForChild(Name, 120)
		if not Folder then return end
		local function add(M: Instance)
			if not M:IsA(`Model`) then return end
			M:GetAttributeChangedSignal(`NHSayAt`):Connect(function()
				local Text = M:GetAttribute(`NHSay`)
				-- the line's attitude (NHSayMood, StudentBrain's line matrix), else the student's mood, else the text
				local Att, Mood = M:GetAttribute(`NHSayMood`), M:GetAttribute(`NHMood`)
				local Expr = (typeof(Att) == `string` and ATTITUDE[Att]) or (typeof(Mood) == `string` and MOOD[Mood]) or nil
				Shared.Say(M, Text, Expr)
			end)
		end
		for _, M in Folder:GetChildren() do add(M) end
		Folder.ChildAdded:Connect(add)
	end)
end

function Shared.OnStart()
	-- players: every chat message this client receives (the speaker's own too)
	TextChatService.MessageReceived:Connect(function(Msg: TextChatMessage)
		local Src = Msg.TextSource
		local P = Src and Players:GetPlayerByUserId(Src.UserId)
		if P and P.Character then Shared.Say(P.Character, Msg.Text) end
	end)
	-- students: the line they say (UI bubble + voice: Controllers.World.NpcLook)
	for _, Name in { `NHStudents`, `NHSchedule` } do watchStudents(Name) end
	-- Studio tests only: NHTestSay on a character ("<text>" or "<expr>|<text>") talks it the way a chat message does
	if RunService:IsStudio() then
		local function hook(Char: Model)
			Char:GetAttributeChangedSignal(`NHTestSay`):Connect(function()
				local V = Char:GetAttribute(`NHTestSay`)
				if typeof(V) ~= `string` then return end
				local E, T = string.match(V, `^(%a+)|(.*)$`)
				if E and Art.Expr[E] then Shared.Say(Char, T, E) else Shared.Say(Char, V) end
			end)
		end
		local function onPlayer(P: Player)
			if P.Character then hook(P.Character) end
			P.CharacterAdded:Connect(hook)
		end
		for _, P in Players:GetPlayers() do onPlayer(P) end
		Players.PlayerAdded:Connect(onPlayer)
	end
	-- the atlases load up front, so the first line has its mouths
	task.spawn(function()
		local List = table.clone(Art.Mouth.Atlases)
		for _, Id in Art.Lid.Atlases do table.insert(List, Id) end
		-- a fetch can fail now and then: try those again (three tries)
		local CP = game:GetService(`ContentProvider`)
		local Want = List
		for _ = 1, 3 do
			local Failed = {}
			pcall(function()
				CP:PreloadAsync(Want, function(Id, Status)
					if Status == Enum.AssetFetchStatus.Failure then table.insert(Failed, Id) end
				end)
			end)
			if #Failed == 0 then break end
			Want = Failed
			task.wait(3)
		end
		-- and drawn once (1 px, all but invisible, for a few seconds): an atlas's first draw on a face can come out
		-- blank for a moment while the GPU takes it, and that moment is the start of someone's first line
		local Pg = Players.LocalPlayer:WaitForChild(`PlayerGui`, 30)
		if not Pg then return end
		local G = Instance.new(`ScreenGui`)
		G.Name = `NHFaceTalkWarm`
		G.ResetOnSpawn = false
		G.IgnoreGuiInset = true
		G.DisplayOrder = -100
		for k, Id in List do
			local I = Instance.new(`ImageLabel`)
			I.BackgroundTransparency = 1
			I.Image = Id
			I.ImageTransparency = 0.98
			I.Size = UDim2.fromOffset(1, 1)
			I.Position = UDim2.fromOffset(k, 0)
			I.Parent = G
		end
		G.Parent = Pg
		task.delay(4, function() G:Destroy() end)
	end)
	local Acc = 0
	RunService.Heartbeat:Connect(function(Dt)
		Acc += Dt
		if Acc < 1 / 30 then return end
		Acc = 0
		local Ok, Err = pcall(step)
		if not Ok then warn(`[FaceTalk] {Err}`) end
	end)
end

-- tests read this
function Shared.Debug(Char: Model)
	local F = Faces[Char]
	if not F then return nil end
	return { Expr = F.Expr; Shown = F.Shown; Lid = F.LidShown; Brow = F.BrowShown; Lips = F.Lips; Shape = F.Shape;
		Form = F.Form; Shut = F.Shut; Total = F.Total; Strips = #F.Strips }
end

return Shared
