# Inventory QOL batch 5: the taste book and feeding students.
INV = "ServerScriptService.Services.Features.Inventory"
ITEMS = "ReplicatedStorage.Config.Items"
BRAIN = "ServerScriptService.Services.AI.StudentBrain"
PROG = "ServerScriptService.Services.Player.Progression"
CT = "ReplicatedStorage.Config.CliqueTalk."

# the "Fed" moment for each clique's lines: Loved (a food the clique loves), Liked (any other), Refuse (won't take it).
# {Snack} is the snack's name. Lines with a {Key} are in double quotes (backticks interpolate in Luau).
FED = {
"Generic": '''	Fed = {
		Loved = { Any = { "Oh, {Snack}? You're the best.", "{Snack}! How did you know?", "You're sharing {Snack}? Legend.", `My favourite. Thank you!` } };
		Liked = { Any = { "{Snack}? Sure, thanks.", `Oh. Thanks!`, `That's nice of you.`, `Free food? I won't say no.` } };
		Refuse = { Hostile = { `I'm not taking anything from you.`, `Keep it.`, `Is it poisoned? No thanks.` }; Wary = { `Uh, no thanks.`, `I'm good. Really.`, `Why are you giving me food?` } };
	};
''',
"Vigil": '''	Fed = {
		Loved = { Any = { "{Snack}. Fuel for a long night in the stacks.", `You've been watching what we drink. Noted.`, "{Snack}. The archive thanks you.", `A scholar's snack. Thank you.` } };
		Liked = { Any = { "{Snack}? Thank you. I'll log it.", `Kind of you. Crumbs away from the books.`, `Thank you. Quietly, now.` } };
		Refuse = { Hostile = { `Records say you're trouble. No.`, `We don't take gifts from you.`, `Put it away.` }; Wary = { `I'd rather not. Not yet.`, `Hm. Why? No, thank you.` } };
	};
''',
"Court": '''	Fed = {
		Loved = { Any = { "{Snack}? Darling, you have taste.", `Oh, you remembered. How charming.`, "{Snack}. Finally, someone civilised.", `Now that's a proper gift.` } };
		Liked = { Any = { "{Snack}? How quaint. Thank you.", `Common, but sweet of you.`, `I'll accept it. Graciously.` } };
		Refuse = { Hostile = { `From you? I'd sooner starve.`, `Take it back. It's tacky.`, `The Court doesn't eat charity.` }; Wary = { `I don't take sweets from strangers.`, `Hm. Pass, thank you.` } };
	};
''',
"Athletes": '''	Fed = {
		Loved = { Any = { "{Snack}! Pre-game fuel. You're clutch.", `Carbs! You get it. Thanks!`, "{Snack}? That's a power play.", `Yes! Coach can't see, right?` } };
		Liked = { Any = { "{Snack}? Thanks, I'll burn it off.", `Cheers. Back to the drills.`, `Snack break! Thanks.` } };
		Refuse = { Hostile = { `Not from you. Off my court.`, `Nah. Benched.`, `Keep it. I'm cutting.` }; Wary = { `I'm on a diet plan. Sorry.`, `Coach says no gifts.` } };
	};
''',
"Ink": '''	Fed = {
		Loved = { Any = { "{Snack}? Inspiration, in edible form.", `You get artists. Thanks.`, "{Snack}! Fuel for a mural.", `Okay, you're my muse today.` } };
		Liked = { Any = { "{Snack}? Thanks. Paint fingers, though.", `Cheers. Don't tell the brushes.`, `Nice. I'll draw you later.` } };
		Refuse = { Hostile = { `Nope. Not from a blank canvas like you.`, `Keep it. I'm not hungry for you.` }; Wary = { `I'm good. Mid-sketch.`, `Uh, maybe later?` } };
	};
''',
"Delinquents": '''	Fed = {
		Loved = { Any = { "{Snack}? Alright. You're alright.", `Huh. You know the good stuff.`, "{Snack}. Okay, I owe you one.", `Respect. Real respect.` } };
		Liked = { Any = { "{Snack}? Sure. Didn't ask, but sure.", `Fine. Thanks, I guess.`, `Free's free.` } };
		Refuse = { Hostile = { `You trying to buy me off? Get lost.`, `Keep your snacks. Keep walking.`, `I don't eat from snitches.` }; Wary = { `What's the catch?`, `Nah. Not yet.` } };
	};
''',
"Ordinary": '''	Fed = {
		Loved = { Any = { "{Snack}! You're so nice. Thank you!", `Oh wow, my favourite. Thanks!`, "{Snack}? You just made my day.", `Best thing that's happened all week.` } };
		Liked = { Any = { "{Snack}? Oh, thank you!", `That's really kind. Thanks.`, `You didn't have to! Thanks.` } };
		Refuse = { Hostile = { `Um, no. I don't trust you.`, `Please just leave me alone.` }; Wary = { `Oh, um, I'm okay, thanks.`, `My mum says no food from strangers.` } };
	};
''',
"Pack": '''	Fed = {
		Loved = { Any = { "{Snack}! Now that's real food.", `Meat. You get the Pack. Thanks.`, "{Snack}? You can run with us tonight.", `Smells right. Thanks, pup.` } };
		Liked = { Any = { "{Snack}? It'll do. Thanks.", `Food's food. Cheers.`, `Not meat, but fine.` } };
		Refuse = { Hostile = { `I'd sooner hunt my own.`, `Keep it, prey.`, `You smell like trouble. No.` }; Wary = { `Not hungry. Not for that.`, `Hm. Sniffing it first. No.` } };
	};
''',
"Choir": '''	Fed = {
		Loved = { Any = { "{Snack}! Blessed, truly.", `Oh, how kind. A gift for the choir.`, "{Snack}? Heaven sent.", `Bless you. I mean it.` } };
		Liked = { Any = { "{Snack}? Thank you, kindly.", `Grace before eating. Thank you.`, `How generous of you.` } };
		Refuse = { Hostile = { `We'll pray for you. Keep it.`, `I can't accept that from you.`, `No. Not after what you've done.` }; Wary = { `I'm fasting, I'm afraid.`, `Perhaps another time.` } };
	};
''',
}

EDITS = [
# ---- Config.Items: what can be tasted, the milestones, each clique's favourite foods, and the save
(ITEMS, """-- (batch 54) a lunch period opens the lunch meals (ReplicatedStorage attribute NHLunchOpen = true)""",
        """-- (inventory QOL batch 5) the taste book: every food and drink you can eat (prank kits, trophies and the kit's
-- hidden buffs don't count). Each milestone gives a title and +1 max health for good (Inventory.TasteEffects).
function Items.Tasteable(): { any }
	local Out = {}
	for _, It in Items.List do if It.Kind == `Heal` or It.Kind == `Buff` then table.insert(Out, It) end end
	for _, It in Items.Lunch or {} do if It.Kind == `Heal` or It.Kind == `Buff` then table.insert(Out, It) end end
	return Out
end
Items.TasteMilestones = { { At = 10; Title = `Snacker` }; { At = 25; Title = `Refectory Regular` }; { At = `All`; Title = `Iron Stomach` } }

-- (inventory QOL batch 5) the foods each clique loves: feeding one to a member is worth standing (Inventory.Feed)
Items.CliqueFood = {
	Athletes = { `YakisobaBun`, `TakoyakiBoat`, `Bento`, `CurryBread`, `KaraageSet` };
	Choir = { `MoonCake`, `GreenTea`, `Dango`, `HolyLemonade`, `FruitCup` };
	Pack = { `Nikuman`, `YakitoriSkewers`, `MeatLoaf`, `KaraageSet`, `RavensRoast` };
	Vigil = { `CannedCoffee`, `BarleyTea`, `Senbei`, `KonpeitoStars`, `MisoSoup` };
	Court = { `CreamPuff`, `PuddingCup`, `StrawberryMilk`, `RedLantern`, `Omurice` };
	Delinquents = { `BlackCatCola`, `GraveCrisps`, `CupRamen`, `LicoriceWhips`, `ShoyuRamen` };
	Ordinary = { `Onigiri`, `MelonBread`, `MisoSoup`, `Popcorn`, `RiceBowl` };
	Ink = { `Taiyaki`, `BatGummies`, `MelonSoda`, `GhostMints`, `ChocolateBar` };
}

-- (batch 54) a lunch period opens the lunch meals (ReplicatedStorage attribute NHLunchOpen = true)"""),
(ITEMS, """	if typeof(Raw.Daily) == `table` and typeof(Raw.Daily.Day) == `number` then""",
        """	-- (inventory QOL batch 5) the taste book ({ [id] = true }) and today's fed cliques ({ Day = n, [clique] = true })
	if typeof(Raw.Tasted) == `table` then
		Out.Tasted = {}
		for Id, V in Raw.Tasted do if V == true and Items.ById[Id] and not Items.ById[Id].Hidden then Out.Tasted[Id] = true end end
	end
	if typeof(Raw.Fed) == `table` and typeof(Raw.Fed.Day) == `number` then
		Out.Fed = { Day = math.floor(Raw.Fed.Day) }
		for K, V in Raw.Fed do if K ~= `Day` and typeof(K) == `string` and #K <= 24 and V == true then Out.Fed[K] = true end end
	end
	if typeof(Raw.Daily) == `table` and typeof(Raw.Daily.Day) == `number` then"""),
# ---- Inventory: mark what you taste, the milestones, the bonus, feeding
(INV, """		Inv2.Items[Id] -= 1
		if Inv2.Items[Id] <= 0 then Inv2.Items[Id] = nil end
		Local.Save(P, Inv2)""", """		Inv2.Items[Id] -= 1
		if Inv2.Items[Id] <= 0 then Inv2.Items[Id] = nil end
		local Fresh = Local.MarkTasted(Inv2, It) -- (inventory QOL batch 5) the taste book
		Local.Save(P, Inv2)
		if Fresh then Local.TasteMilestone(P, Inv2) end"""),
(INV, """		HealReady = Cd.Heal or 0; -- server time""", """		HealReady = Cd.Heal or 0; -- server time
		Tasted = Inv.Tasted or {}; -- (inventory QOL batch 5) the taste book"""),
(INV, """-- (inventory QOL 1.94) Best food:""", """-- (inventory QOL batch 5) the taste book: the first time you eat or drink something it's ticked off. Returns true if
-- it was new.
function Local.MarkTasted(Inv, It): boolean
	if not (It and (It.Kind == `Heal` or It.Kind == `Buff`) and not It.Hidden) then return false end
	Inv.Tasted = Inv.Tasted or {}
	if Inv.Tasted[It.Id] then return false end
	Inv.Tasted[It.Id] = true
	return true
end

function Local.TasteCount(Inv): (number, number)
	local Have, Total = 0, 0
	for _, It in Items.Tasteable() do
		Total += 1
		if Inv.Tasted and Inv.Tasted[It.Id] then Have += 1 end
	end
	return Have, Total
end

-- how many milestones you've reached (each one is +1 max health and a title)
function Local.TasteReached(Inv): number
	local Have, Total = Local.TasteCount(Inv)
	local N = 0
	for _, M in Items.TasteMilestones do
		if Have >= (if M.At == `All` then Total else M.At) then N += 1 end
	end
	return N
end

-- a new taste: hand out any milestone just reached (the title, the health) and say so
function Local.TasteMilestone(P: Player, Inv)
	local Have, Total = Local.TasteCount(Inv)
	for _, M in Items.TasteMilestones do
		local At = if M.At == `All` then Total else M.At
		if Have == At then
			pcall(function() require(ServerScriptService.Services.Social.Reputation).AwardTitle(P, M.Title) end)
			Notifications.Notify(P, { Title = `Taste book: {Have} / {Total}`; Text = `"{M.Title}" earned, and +1 max health for good.`; Kind = `Good`; Duration = 6 })
			Local.Reapply(P)
		end
	end
end

-- the taste book's lasting bonus (Progression adds it in as its own source)
function Shared.TasteEffects(P: Player): { [string]: number }
	local Inv = Shared.Get(P)
	local N = Inv and Local.TasteReached(Inv) or 0
	return if N > 0 then { MaxHealth = N } else {}
end

-- (inventory QOL batch 5) feeding a student: they take a snack from your hands. A food their clique loves is worth +2
-- standing with that clique, once a day per clique. A student who can't stand you won't take it.
function Shared.Feed(P: Player, Model: any, Id: any): (boolean, string?)
	local It = typeof(Id) == `string` and Items.ById[Id]
	if not (It and (It.Kind == `Heal` or It.Kind == `Buff`)) then return false, `They can't eat that.` end
	local Inv = Shared.Get(P)
	if not Inv or (Inv.Items[Id] or 0) <= 0 then return false, `None left. Restock at the stand.` end
	if not (typeof(Model) == `Instance` and Model:IsA(`Model`) and Model:GetAttribute(`NHBrain`)) then return false, nil end
	local Root = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`)
	local Them = Model:FindFirstChild(`HumanoidRootPart`)
	local Hum = Model:FindFirstChildOfClass(`Humanoid`)
	if not (Root and Them and Hum and Hum.Health > 0) or (Root.Position - Them.Position).Magnitude > 12 then return false, `Get closer.` end
	local Ok, Verdict, Clique = pcall(function() return require(ServerScriptService.Services.AI.StudentBrain).Fed(P, Model, It) end)
	if not Ok or Verdict == nil then return false, nil end
	if Verdict == `Refuse` then
		Notifications.Notify(P, { Title = `They won't take it from you.`; Kind = `Info`; Duration = 3 })
		return false, `They won't take it from you.`
	end
	local Inv2 = Shared.Get(P)
	if not Inv2 or (Inv2.Items[Id] or 0) <= 0 then return false, nil end
	Inv2.Items[Id] -= 1
	if Inv2.Items[Id] <= 0 then Inv2.Items[Id] = nil end
	local Msg = `They took the {It.Name}.`
	if Verdict == `Loved` and Clique then
		local Day = Local.EventDay()
		if not (Inv2.Fed and Inv2.Fed.Day == Day) then Inv2.Fed = { Day = Day } end
		if not Inv2.Fed[Clique] then
			Inv2.Fed[Clique] = true
			pcall(function() require(ServerScriptService.Services.Social.Cliques).Add(P, Clique, 2, `Shared a snack`) end)
			local Def = require(ReplicatedStorage.Config.Cliques).Defs[Clique]
			Msg = `They loved the {It.Name}. +2 with {Def and Def.Name or Clique}.`
		else
			Msg = `They loved the {It.Name}. (Their clique's thanks already counted today.)`
		end
	end
	Local.Save(P, Inv2)
	Local.Anim(Hum) -- they eat it
	Notifications.Notify(P, { Title = Msg; Kind = if Verdict == `Loved` then `Good` else `Info`; Duration = 4 })
	return true, Msg
end

-- (inventory QOL 1.94) Best food:"""),
(INV, """	local UseBest = rf(`UseBest`) -- (inventory QOL 1.94)""", """	local UseBest = rf(`UseBest`) -- (inventory QOL 1.94)
	local Feed = rf(`Feed`) -- (inventory QOL batch 5)"""),
(INV, """	UseBest.OnServerInvoke = function(P) if limited(P) then return false, `One moment...` end return Shared.UseBest(P) end""",
      """	UseBest.OnServerInvoke = function(P) if limited(P) then return false, `One moment...` end return Shared.UseBest(P) end
	Feed.OnServerInvoke = function(P, Model, Id) if limited(P) then return false, `One moment...` end return Shared.Feed(P, Model, Id) end"""),
# ---- Progression: the taste book's bonus as its own source
(PROG, """		if next(B) then Local.Add(E, B) Sources.Snack = B end
	end)""", """		if next(B) then Local.Add(E, B) Sources.Snack = B end
	end)
	pcall(function() -- (inventory QOL batch 5) the taste book's milestones
		local T = require(game:GetService(`ServerScriptService`).Services.Features.Inventory).TasteEffects(Player)
		if next(T) then Local.Add(E, T) Sources.TasteBook = T end
	end)"""),
# ---- StudentBrain: a student takes (or refuses) a snack
(BRAIN, """function Brain.Contact(Pl: Player, Model: Model, Speed: number, Dir: Vector3): boolean""",
        """-- (inventory QOL batch 5) a player offers this student a snack (Features.Inventory.Feed). They turn to the player and
-- answer in their clique's voice (the "Fed" moment): Loved (their clique loves it), Liked, or Refuse (Hostile, or Wary
-- with no loved food). Returns the verdict and the student's clique, or nil if Model isn't a student.
function Brain.Fed(Pl: Player, Model: Model, It): (string?, string?)
	local S = nil
	for _, X in (Host and Host.Students and Host.Students()) or {} do
		if X.Model == Model then S = X break end
	end
	if not (S and S.Model and S.Root) then return nil end
	local Foods = S.Clique and Items.CliqueFood[S.Clique]
	local Loved = Foods ~= nil and table.find(Foods, It.Id) ~= nil
	local OkA, Attitude = pcall(Talk.Attitude, S, Pl)
	Attitude = if OkA then Attitude else `Neutral`
	local Verdict = if Attitude == `Hostile` or (Attitude == `Wary` and not Loved) then `Refuse` elseif Loved then `Loved` else `Liked`
	local Root = Pl.Character and Pl.Character:FindFirstChild(`HumanoidRootPart`)
	if Root then lookAt(S, Root.Position + Vector3.new(0, 1.5, 0), 3) end
	local C = ctx()
	C.Snack = It.Name
	sayMatrix(S, `Fed`, Pl, { Sub = Verdict; Ctx = C; Attitude = if Verdict == `Refuse` then Attitude else nil }, 0)
	return Verdict, S.Clique
end

function Brain.Contact(Pl: Player, Model: Model, Speed: number, Dir: Vector3): boolean"""),
]

# the brain needs Config.Items for the clique foods
EDITS.append((BRAIN, """local Lines = require(script:WaitForChild(`Lines`))""",
              """local Lines = require(script:WaitForChild(`Lines`))
local Items = require(game:GetService(`ReplicatedStorage`).Config.Items) -- (inventory QOL batch 5) the clique foods"""))

# the Fed lines go in just before each clique module's closing brace
for name, block in FED.items():
    EDITS.append(("CT_TAIL:" + name, None, block))
# Inventory QOL batch 5 (client): the Locker's Tastes tab.
LOCK = "StarterPlayer.StarterPlayerScripts.Controllers.Gui.Locker"
EDITS = [
(LOCK, """local TABS = { `All`, `Gear`, `Snacks`, `Boards`, `Kit` }""",
       """local TABS = { `All`, `Gear`, `Snacks`, `Boards`, `Kit`, `Tastes` } -- (inventory QOL batch 5) Tastes: the taste book"""),
(LOCK, """				equipped = Mine.Equipped == B.Id; order = B.Order })
		end
	end
""", """				equipped = Mine.Equipped == B.Id; order = B.Order })
		end
	end
	-- (inventory QOL batch 5) the taste book: everything you can eat or drink, ticked once you have
	if Tab == 6 then
		for _, It in Items.Tasteable() do
			table.insert(Out, { name = It.Name; rarity = It.Rarity; kind = `Taste`; id = It.Id; order = It.Order;
				tasted = State.Tasted ~= nil and State.Tasted[It.Id] == true })
		end
	end
"""),
(LOCK, """	local It = (E.kind == `Snack` or E.kind == `Trophy`) and Items.ById[E.id]""",
       """	local It = (E.kind == `Snack` or E.kind == `Trophy` or E.kind == `Taste`) and Items.ById[E.id]"""),
(LOCK, """			if Local.IsFav(E.id) then -- (inventory QOL 1.93) a starred item""",
       """			if E.kind == `Taste` then -- (inventory QOL batch 5) untasted: a dark silhouette; tasted: a gilt tick
				if E.tasted then
					Kit.Text({ Name = `Tick`; Text = `\\u{2713}`; Font = Fonts.Title; TextSize = 18; TextColor3 = C.Gold; TextXAlignment = Enum.TextXAlignment.Right;
						AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -6, 0, 2); Size = UDim2.fromOffset(20, 20); ZIndex = 9; Parent = Slot })
				else
					local V = Slot:FindFirstChild(`NHView`)
					if V and V:IsA(`ViewportFrame`) then V.ImageColor3 = Color3.new(0, 0, 0) V.ImageTransparency = 0.25 end
					Kit.Text({ Name = `Unknown`; Text = `?`; Font = Fonts.Title; TextSize = 26; TextColor3 = C.TextDim; TextXAlignment = Enum.TextXAlignment.Center;
						AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.45); Size = UDim2.fromOffset(30, 30); ZIndex = 9; Parent = Slot })
				end
			end
			if Local.IsFav(E.id) then -- (inventory QOL 1.93) a starred item"""),
(LOCK, """	`No everyday kit yet. MORROW & VANE and THE WICK & KETTLE sell it.`;""",
       """	`No everyday kit yet. MORROW & VANE and THE WICK & KETTLE sell it.`;
	`Nothing to taste yet.`;"""),
(LOCK, """	local Id = Selected.id
	local Have = State.Items[Id] or 0
""", """	local Id = Selected.id
	local Have = State.Items[Id] or 0
	-- (inventory QOL batch 5) the taste book: tasted or not, the count, and the next title
	if Selected.kind == `Taste` then
		local Got, Total, Next = 0, 0, nil
		for _, T in Items.Tasteable() do
			Total += 1
			if State.Tasted and State.Tasted[T.Id] then Got += 1 end
		end
		for _, M in Items.TasteMilestones do
			local At = if M.At == `All` then Total else M.At
			if Got < At then Next = `"{M.Title}" at {At}` break end
		end
		local Done = State.Tasted and State.Tasted[Id]
		Info.Text = (if Done then `Tasted` else `Not tasted yet`) .. `  \\u{00B7}  {Got} / {Total}  \\u{00B7}  `
			.. (if Next then `next: {Next}` else `every title earned`)
		if Done then Local.FavButton(A, Id, UDim2.new(1, 0, 0.5, 0)) end
		return
	end
"""),
]
