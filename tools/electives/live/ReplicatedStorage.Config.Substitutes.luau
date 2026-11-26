--[[
	Substitute teachers (shared). ReplicatedStorage.Config.Substitutes   (1.47)

	Two or three school days a week (picked from the week number, so every server agrees), one random subject's class is
	covered for the whole day by one of four substitutes, standing at that room's teacher's desk. Nobody is warned: you
	find out when you walk in. Each substitute brings a rule (Rule), and sometimes (TwistChance; the Odd One always) a twist
	instead of the usual lesson:
	  Swap     another subject's minigame                  ("History? No, today we mix chemicals.")
	  Game     a minigame only substitutes run: CandleVigil, SeanceSequence
	  Errand   fetch something from elsewhere in the school and bring it back before the bell (counts as an A)

	Rule fields (all optional):
	  LevelOffset   the lesson runs this many levels harder (+) or easier (-)
	  TimeMult      the lesson's time limit is multiplied by this
	  YenMult       the Yen a pass pays is multiplied by this
	  DoubleOrNothing  { Grade = letter }: that grade or better pays YenMult x2, below it pays nothing (still graded)
	  Late          `Strict` (late arrivals are booked again: +1 Tardy) or `Lenient` (late counts as on time)
	  OnTimeExp     EXP for arriving on time to the covered class
]]

local Substitutes = {}

Substitutes.DaysPerWeek = { 2, 3 }      -- how many school days a week get a substitute (random between)
Substitutes.SchoolDays = 5              -- event days per school week (Monday..Friday, 6 AM rollovers)
Substitutes.Subjects = { `Mathematics`, `Chemistry`, `English`, `History`, `Anatomy` } -- (Electives) electives only on Tue/Thu

-- the minigames only substitutes run (ServerStorage.Activities.<Type>, Controllers.Gui.Activities.<Type>)
Substitutes.Games = {
	CandleVigil = { Type = `CandleVigil`; Title = `Candle Vigil`; Tagline = `Keep every candle burning. Click a guttering flame before it goes out.` };
	SeanceSequence = { Type = `SeanceSequence`; Title = `Seance Sequence`; Tagline = `Watch the sigils glow, then repeat the sequence. It grows each round.` };
}

-- errands: Region = Config.Regions id where the thing turns up; Prop = ServerStorage.NHProps template (a plain block if
-- missing); Text = what it is
Substitutes.Errands = {
	Watch = { Region = `StaffRoom`; Prop = `LostPocketWatch`; Text = `a pocket watch`; Place = `the Staff Room` };
	Sketchbook = { Region = `Archive`; Prop = `LostSketchbook`; Text = `a sketchbook`; Place = `the Archive` };
	Lunch = { Region = `Commons`; Prop = `LostLunchTin`; Text = `a lunch tin`; Place = `the Commons` };
	Hymnal = { Region = `Chapel`; Prop = `LostHymnal`; Text = `a hymnal`; Place = `the Chapel` };
	Scarf = { Region = `Gymnasium`; Prop = `LostScarf`; Text = `a striped scarf`; Place = `the Gymnasium` };
	Phone = { Region = `MainHall`; Prop = `LostPhone`; Text = `a cracked phone`; Place = `the Main Hall` };
}

Substitutes.Cast = {
	{
		Id = `Crane`; Name = `Mr. Thaddeus Crane`; Title = `The Stickler`; Color = Color3.fromRGB(150, 170, 200);
		Look = { Body = 1; Skin = 1; Uniform = `black-blazer`; Bottoms = `charcoal-slacks`; Eyes = 4; Brows = `furrowed`; Mouth = `flat`; HairId = 2689690284 };
		RuleName = `Strict Hours`;
		RuleText = `Late is a mark. Twice. Arrive on time and you'll be rewarded. The lesson runs one level harder, and pays a quarter more.`;
		Rule = { LevelOffset = 1; YenMult = 1.25; Late = `Strict`; OnTimeExp = 20 };
		TwistChance = 0.2; Twists = { `Swap`, `Errand`, `Specimen` }; Errands = { `Watch` };
		Lines = {
			Hello = { `Seats. Now. I am Mr. Crane, and I do not repeat myself.`, `Your teacher is indisposed. I am not.` };
			Pass = { `Adequate. I shall note it.`, `Precisely as expected of a student who pays attention.` };
			Fail = { `Disappointing, and noted.`, `I have seen sharper minds in a sock drawer.` };
			Errand = `My pocket watch. I left it in the Staff Room. Fetch it before the bell, and we'll call it an A.`;
		};
	};
	{
		Id = `Moth`; Name = `Miss Delphine Moth`; Title = `The Dreamer`; Color = Color3.fromRGB(205, 175, 235);
		Look = { Body = 2; Skin = 3; Uniform = `charcoal-cardigan`; Bottoms = `pleated-tartan-skirt`; Eyes = 6; Brows = `soft`; Mouth = `smile`; HairId = 1903448711 };
		RuleName = `Open Book`;
		RuleText = `Late is fine, dear, time is only a suggestion. Open books today: one level easier, for half the Yen.`;
		Rule = { LevelOffset = -1; YenMult = 0.5; Late = `Lenient` };
		TwistChance = 0.35; Twists = { `Swap`, `Game`, `Errand`, `Specimen` }; Errands = { `Sketchbook`, `Hymnal` };
		Lines = {
			Hello = { `Oh! Hello. I'm Miss Moth. Sit anywhere, the desks don't mind.`, `I dreamt I'd be teaching today. How lovely.` };
			Pass = { `Wonderful. You must have been dreaming of the answers too.`, `Look at you go.` };
			Fail = { `Never mind. Tomorrow is another dream.`, `Oh dear. Well, it was a nice try.` };
			Errand = `I've misplaced my sketchbook, I think I left it in the Archive. Or the Chapel? Be a darling and find it before the bell.`;
		};
	};
	{
		Id = `Lazzaro`; Name = `Signor Vittorio Lazzaro`; Title = `The Gambler`; Color = Color3.fromRGB(230, 190, 110);
		Look = { Body = 1; Skin = 4; Uniform = `crimson-court-vest`; Bottoms = `black-jeans`; Eyes = 2; Brows = `arched`; Mouth = `grin`; HairId = 3609301673 };
		Variants = {
			{
				RuleName = `Double or Nothing`;
				RuleText = `Double or nothing! A B or better pays double. Anything less, and the house keeps it all.`;
				Rule = { DoubleOrNothing = { Grade = `B` } };
			};
			{
				RuleName = `Speed Round`;
				RuleText = `Speed round! Less time on the clock, half again the pay. Fortune favours the quick.`;
				Rule = { TimeMult = 0.75; YenMult = 1.5 };
			};
		};
		TwistChance = 0.3; Twists = { `Swap`, `Game`, `Errand`, `Specimen` }; Errands = { `Lunch` };
		Lines = {
			Hello = { `Ciao! Signor Lazzaro. Today we play for stakes.`, `Your teacher owed me a favour. Now I owe you a lesson.` };
			Pass = { `The house pays out! Bravissimo.`, `A winner. I knew it from the moment you sat down.` };
			Fail = { `The house always wins, my friend.`, `Ah, so close. Next hand, eh?` };
			Errand = `A man cannot teach hungry. My lunch tin is in the Commons. Bring it before the bell and I'll mark you an A.`;
		};
	};
	{
		Id = `Hollow`; Name = `Mx. Ashgrove Hollow`; Title = `The Odd One`; Color = Color3.fromRGB(140, 210, 190);
		Look = { Body = 1; Skin = 2; Uniform = `vigil-vest`; Bottoms = `charcoal-slacks`; Eyes = 5; Brows = `straight`; Mouth = `smirk`; HairId = 1955434621 };
		RuleName = `Anything Goes`;
		RuleText = `The subject? I couldn't say. Today we do something else entirely.`;
		Rule = { YenMult = 1.25 };
		TwistChance = 1; Twists = { `Swap`, `Game`, `Game`, `Errand`, `Specimen` }; Errands = { `Hymnal`, `Scarf`, `Phone` };
		Lines = {
			Hello = { `Hello. Don't mind the timetable. It doesn't mind us.`, `I'm Hollow. Not your teacher. Close enough.` };
			Pass = { `Oh, that was interesting. You're interesting.`, `The candles approve.` };
			Fail = { `Hm. The sigils didn't like that.`, `Not today, then. Perhaps not ever. Who knows.` };
			Errand = `Something of mine wandered off. Go and find it, and bring it here before the bell. You'll know it when you see it.`;
		};
	};
}

Substitutes.ById = {}
for _, Sub in Substitutes.Cast do Substitutes.ById[Sub.Id] = Sub end

return Substitutes
