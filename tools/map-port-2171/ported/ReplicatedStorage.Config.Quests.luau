--[[
	Quest definitions (shared, data only: the journal reads the text, the server runs the rules).

	Quest fields
		Name, Category (Main | Side), Chapter?, Giver? (NpcId), Auto? (starts by itself when requirements
		are met), Summary, Offer / Accept / Thanks (giver lines), Requires = { Quests = {..}, NotMember = FactionId },
		Repeatable = "Daily"?, TimeLimit? (in-game minutes), StartItems? { Item },
		Stealth? = { Zone, Checkpoint = objective Id } (caught in that zone -> back to the checkpoint),
		Objectives = { ... }, Rewards = { Yen, Standing = {Faction=n}, Rep = {Category=n}, Relationship = {Npc=n}, Title },
		Next? (quest that starts when this one is done).

	Objectives run in order. Optional ones count any time the quest is active (they never block).
	Objective fields: Id, Type, Text, Count?, Optional?, Time? (set of segment kinds when it counts),
	and per type:
		Attend   (class recorded Present / Tardy)               Subject?
		Talk     (open a conversation)                          Npc or Npcs
		Interact (use a quest object)                           Object
		Collect  (search objects; one holds the item)            Objects, Item, Hidden? (random which one)
		Deliver  (talk to the NPC while holding the item)        Npc, Item
		Reach    (stand in a quest area)                        Area, Item? (must still hold it)
		Clues / Link / Deduce (investigation, see Config.Cases)  Case
		Defeat   (down a quest target in its fight)             Target
		Duel     (win a ring duel against another student)
		Lesson   (pass a class lesson)                          Subject?, MinGrade?
		Scuffle  (win a clique scuffle or rumble, 1.28)        Clique?
		Prank    (prank a clique's hangout, 1.33)               Victim?
	Job = true (1.35): a clique member's daily job (Clique = the clique): like a dare, but members only (Social.CliqueMembership).
		StopPrank (objective): put down a prankster at Victim's hangout (Social.CliquePranks).
	Showdown = <clique> (1.34): that leader's showdown (Social.CliqueShowdowns says who can start it and runs the fight).
	Dare = true (1.33): a clique leader's daily dare (Clique = the leader's clique). Only the leader's dare of the day can
	start; it's done for the in-game day (6 AM to 6 AM), and an unfinished one goes away at 6 AM (Services.Quests).
	Any objective may also have Grants = { Case, Clue } (clue added when it completes).
	Waypoint (journal + tracker marker) comes from Npc / Object / Area unless set: { Kind, Id }.

	Map contract (all found by attribute, so the real map just places parts):
		QuestObject = <Objects id>   QuestArea = <area id>   NpcPost = <npc id>
]]

local AFTER_HOURS = { Evening = true; Night = true }

return {
	Objects = {
		LockerNote      = { Action = `Read note`; Name = `Locker 113` };
		DeskCarving     = { Action = `Inspect`; Name = `Back-row desk`; Clue = { Case = `EmptyDesk`; Id = `DeskCarving` } };
		AttendanceSheet = { Action = `Inspect`; Name = `Homeroom register`; Clue = { Case = `EmptyDesk`; Id = `AttendanceSheet` } };
		ArchiveCard     = { Action = `Inspect`; Name = `Borrowing cards`; Clue = { Case = `EmptyDesk`; Id = `ArchiveCard` } };
		MiraFile        = { Action = `Take file`; Name = `Filing cabinet H`; Hold = 1.5 };
		AnswerKey       = { Action = `Swipe`; Name = `Answer key`; Hold = 1.2 };
		LostSpotA       = { Action = `Search`; Name = `Under the bleacher bench`; Hold = 0.8 };
		LostSpotB       = { Action = `Search`; Name = `Lost property bin`; Hold = 0.8 };
		LostSpotC       = { Action = `Search`; Name = `Behind the vending machine`; Hold = 0.8 };

		-- Bloodline rites (Races Phase 3). Placed by Studio/rite_props.luau; only players on that rite get a prompt.
		BloodFont   = { Action = `Drink`; Name = `Old stone font`; Hold = 2.0 };
		BloodLedger = { Action = `Take ledger`; Name = `Blood ledger`; Hold = 1.4 };
		HowlStack   = { Action = `Howl`; Name = `Boiler stack`; Hold = 2.5 };
		AshHeap     = { Action = `Dig`; Name = `Ash heap`; Hold = 2.5 };
		BoneCrate   = { Action = `Lie down`; Name = `Bone crate`; Hold = 3.0 };
		ColdMirror  = { Action = `Touch`; Name = `Cold mirror`; Hold = 1.5 };
		CrackedBell = { Action = `Toll`; Name = `Cracked bell`; Hold = 1.5 };
		ArchiveWard = { Action = `Carve ward`; Name = `Archive door`; Hold = 2.5 };
		OathIron    = { Action = `Swear`; Name = `Boiler iron`; Hold = 2.0 };
		VotiveA     = { Action = `Light`; Name = `Votive candle`; Hold = 1.0 };
		VotiveB     = { Action = `Light`; Name = `Votive candle`; Hold = 1.0 };
		VotiveC     = { Action = `Light`; Name = `Votive candle`; Hold = 1.0 };
		VigilStone  = { Action = `Keep vigil`; Name = `Ring stone`; Hold = 4.0 };

		-- clique leader quests (Cliques Phase 3, 1.28). Placed by Studio/clique_quest_props.luau (stand-ins).
		VigilLampA   = { Action = `Light lamp`; Name = `Archive lamp`; Hold = 1.2 };
		VigilLampB   = { Action = `Light lamp`; Name = `Hall lamp`; Hold = 1.2 };
		VigilLampC   = { Action = `Light lamp`; Name = `Stair lamp`; Hold = 1.2 };
		Page1893     = { Action = `Take page`; Name = `Loose page, 1893`; Hold = 1.6 };
		SnackCrate   = { Action = `Swipe crate`; Name = `Snack crate`; Hold = 1.8 };
		LunchMoneyA  = { Action = `Shake down`; Name = `Bench by the fountain`; Hold = 1.0 };
		LunchMoneyB  = { Action = `Shake down`; Name = `Notice board`; Hold = 1.0 };
		LunchMoneyC  = { Action = `Shake down`; Name = `Sundial`; Hold = 1.0 };
		ChoirVotiveA = { Action = `Light`; Name = `Chapel votive`; Hold = 1.0 };
		ChoirVotiveB = { Action = `Light`; Name = `Chapel votive`; Hold = 1.0 };
		ChoirVotiveC = { Action = `Light`; Name = `Chapel votive`; Hold = 1.0 };
		PaintShelf   = { Action = `Take paint`; Name = `Supply cupboard`; Hold = 1.2 };
		GymDoors     = { Action = `Tag doors`; Name = `Gym doors`; Hold = 3.0; Witness = `Vandalism` };
	};

	Items = {
		Package = { Name = `Sealed package`; Droppable = true };
		Charm = { Name = `Silver moon charm` };
		MiraFile = { Name = `Mira Holt's file` };
		AnswerKey = { Name = `Chemistry answer key`; Droppable = true };

		BloodLedger = { Name = `Blood ledger`; Droppable = true };

		Page1893 = { Name = `The missing page (1893)`; Droppable = true };
		Invitation = { Name = `Sealed invitation`; Droppable = true };
		SnackCrate = { Name = `Snack crate`; Droppable = true };
		HallPass = { Name = `Hall pass`; Droppable = true };
		PaintCan = { Name = `Can of red paint`; Droppable = true };
	};

	Quests = {
		---| Main story: Chapter 1 (provisional: the concept doc has no storyline yet) |---

		NewKid = {
			Name = `New Kid`; Category = `Main`; Chapter = 1; Auto = true;
			Summary = `First week at Nightmare Highschool. Learn the routine and meet the people who run the place after dark.`;
			Objectives = {
				{ Id = `Class`; Type = `Attend`; Text = `Attend a class (on time or a little late)` };
				{ Id = `Leader`; Type = `Talk`; Npcs = { `Ezra`, `Vesper` }; Text = `Meet a faction leader: Ezra (Library Archive) or Vesper (Boiler Yard)`; Waypoint = { Kind = `Npc`; Id = `Ezra` } };
				{ Id = `Note`; Type = `Interact`; Object = `LockerNote`; Grants = { Case = `EmptyDesk`; Clue = `LockerNote` }; Text = `Someone jammed a note into locker 113. Read it.` };
			};
			Rewards = { Yen = 15; Rep = { Popularity = 2 } };
			Next = `EmptyDesk`;
		};

		EmptyDesk = {
			Name = `The Empty Desk`; Category = `Main`; Chapter = 1;
			Summary = `A girl called Mira Holt sat in the back row of Room 102. Nobody remembers her clearly, and her name is vanishing from everything. Find out why.`;
			Requires = { Quests = { `NewKid` } };
			Objectives = {
				{ Id = `Clues`; Type = `Clues`; Case = `EmptyDesk`; Count = 4; Text = `Find clues about Mira Holt (Room 102, Room 101, the Archive)` };
				{ Id = `Link`; Type = `Link`; Case = `EmptyDesk`; Count = 2; Text = `Connect the clues on your evidence board (Journal, J)` };
				{ Id = `Deduce`; Type = `Deduce`; Case = `EmptyDesk`; Text = `Work out where her original record is kept` };
			};
			Rewards = { Yen = 25; Rep = { Trust = 3; Academics = 2 } };
			Next = `AfterHours`;
		};

		AfterHours = {
			Name = `After Hours`; Category = `Main`; Chapter = 1;
			Summary = `The originals are in the Records Office, and the night custodian locks it up every evening. Get in, get Mira's file, get out. Don't get seen.`;
			Requires = { Quests = { `EmptyDesk` } };
			Stealth = { Zone = `RecordsOffice`; Checkpoint = `File` };
			Objectives = {
				{ Id = `File`; Type = `Collect`; Objects = { `MiraFile` }; Item = `MiraFile`; Time = AFTER_HOURS; Grants = { Case = `EmptyDesk`; Clue = `MiraFile` }; Text = `After hours (5 PM onwards), sneak into the Records Office and take Mira's file` };
				{ Id = `Out`; Type = `Reach`; Area = `RecordsExit`; Item = `MiraFile`; Text = `Get out of the Records Office without being caught` };
			};
			Rewards = { Yen = 40; Rep = { Trust = 3 }; Title = `Night Owl` };
			Ending = `Mira's file has one line under her photo, in fresh red ink: STATUS: COLLECTED. End of Chapter 1 (to be continued).`;
		};

		---| Side quests |---

		SpecialDelivery = {
			Name = `Special Delivery`; Category = `Side`; Giver = `Dex`; Repeatable = `Daily`;
			Summary = `Dex runs packages around campus and doesn't ask what's in them. Get this one to Pip before it's late.`;
			Offer = `I've got a package for Pip, and I'm already three deliveries behind. Run it over for me? Thirty minutes, tops. And whatever you do, don't get knocked down holding it.`;
			Accept = `Legend. Don't shake it.`;
			Thanks = `Oh! Dex sent you? Thank you, thank you. Don't tell anyone what was in there.`;
			TimeLimit = 30;
			StartItems = { `Package` };
			Objectives = {
				{ Id = `Deliver`; Type = `Deliver`; Npc = `Pip`; Item = `Package`; Text = `Deliver the package to Pip in the hallway before time runs out (if you get downed you'll drop it)` };
			};
			Rewards = { Yen = 20; Rep = { Trust = 1 } };
		};

		LostAndFound = {
			Name = `Lost and Found`; Category = `Side`; Giver = `Pip`;
			Summary = `Pip lost a silver moon charm her grandmother gave her. She's sure it's somewhere on campus.`;
			Offer = `I lost my moon charm. My gran said it keeps the bad dreams away, and I've had nothing but bad dreams since. Could you look for it? I've been to the bleachers, the lost property bin and the vending machines.`;
			Accept = `Really? Thank you! Dex hears everything around here, if you want to ask him.`;
			Thanks = `My charm! You found it! I owe you. I really, really owe you.`;
			Objectives = {
				{ Id = `Ask`; Type = `Talk`; Npc = `Dex`; Optional = true; Text = `(Optional) Ask Dex if he's seen it` };
				{ Id = `Search`; Type = `Collect`; Objects = { `LostSpotA`, `LostSpotB`, `LostSpotC` }; Hidden = true; Item = `Charm`; Text = `Search the spots Pip mentioned` };
				{ Id = `Return`; Type = `Deliver`; Npc = `Pip`; Item = `Charm`; Text = `Give the charm back to Pip` };
			};
			Rewards = { Yen = 20; Rep = { Popularity = 2; Trust = 3 } };
		};

		KingOfTheRing = {
			Name = `King of the Ring`; Category = `Side`; Giver = `Bruno`;
			Summary = `Bruno keeps the ring behind the gym. Beat his champion and people will start getting out of your way.`;
			Offer = `New blood. You want respect here? Step into my ring and put my champion on the floor. Fair fight, one on one, nobody gets finished.`;
			Accept = `Ha! Tell me when you're ready and I'll call him out.`;
			Thanks = `Didn't think you had it in you. The ring remembers a winner.`;
			Objectives = {
				{ Id = `Beat`; Type = `Defeat`; Target = `RingChampion`; Text = `Talk to Bruno to call out the champion, then down him in the ring`; Waypoint = { Kind = `Npc`; Id = `Bruno` } };
			};
			Rewards = { Yen = 30; Rep = { Intimidation = 5; Popularity = 2 }; Title = `Ringleader` };
		};

		SettleIt = {
			Name = `Settle It in the Ring`; Category = `Side`; Giver = `Bruno`; Repeatable = `Daily`;
			Requires = { Quests = { `KingOfTheRing` } };
			Summary = `Got a problem with someone? Settle it properly: a one-on-one duel in Bruno's ring.`;
			Offer = `Got beef with someone? Don't do it in the halls, the monitors will eat you alive. Get them on the other pad in my ring and win. Fair and square.`;
			Accept = `Two pads, two fighters. First one down loses. Nobody gets gripped in my ring.`;
			Thanks = `Clean win. That's how it's done.`;
			Objectives = {
				{ Id = `Win`; Type = `Duel`; Text = `Win a duel against another student: both stand on the ring pads to start`; Waypoint = { Kind = `Area`; Id = `DuelRing` } };
			};
			Rewards = { Yen = 15; Rep = { Intimidation = 2 } };
		};

		RavensTryout = {
			Name = `Night Ravens Tryout`; Category = `Side`; Giver = `Varga`;
			Summary = `Coach Varga runs tryouts in the gymnasium. Show her you can shoot, then show her you can play.`;
			Offer = `Tryouts are simple. Run my Shootaround at the practice end: hit three spots before the clock runs out. Then get in a real game, start to finish. Do both and we'll talk.`;
			Accept = `Practice end, by the east wall. The lit spot is where you shoot from.`;
			Thanks = `Not bad. Not good yet, either. You've got a spot if you want it: just ask.`;
			Objectives = {
				{ Id = `Shoot`; Type = `Drill`; Drill = `Shootaround`; Text = `Pass the Shootaround drill in the gymnasium (3 spots or more)`; Waypoint = { Kind = `Npc`; Id = `Varga` } };
				{ Id = `Play`; Type = `SportMatch`; Sport = `Basketball`; Text = `Play a full basketball game (stand on a team pad by the scorer's table)`; Waypoint = { Kind = `Npc`; Id = `Varga` } };
			};
			Rewards = { Yen = 20; Rep = { Popularity = 3 } };
		};

		RoversTryout = {
			Name = `Grave Rovers Tryout`; Category = `Side`; Giver = `Mallory`;
			Summary = `Coach Mallory wants to see you hit a corner and survive a real match on the west pitch.`;
			Offer = `Tryouts: Target Practice on the practice ground, four corners before the clock runs out. Then a full match on the pitch. Do both.`;
			Accept = `Practice ground is south of the pitch. Shoot from behind the line.`;
			Thanks = `You'll do. The Rovers have a shirt for you if you want it.`;
			Objectives = {
				{ Id = `Targets`; Type = `Drill`; Drill = `TargetPractice`; Text = `Pass Target Practice south of the pitch (4 targets)`; Waypoint = { Kind = `Npc`; Id = `Mallory` } };
				{ Id = `Play`; Type = `SportMatch`; Sport = `Soccer`; Text = `Play a full soccer match (stand on a team pad on the halfway line)`; Waypoint = { Kind = `Npc`; Id = `Mallory` } };
			};
			Rewards = { Yen = 20; Rep = { Popularity = 3 } };
		};
		WardensTryout = {
			Name = `Iron Wardens Tryout`; Category = `Side`; Giver = `Dunmore`;
			Summary = `Coach Dunmore wants to see you catch on the run and hold up in a real game on the north field.`;
			Offer = `Tryouts: Route Runner on the practice lanes west of the field. The machine calls a route, you run it, you catch it. Six catches. Then a full game. Do both.`;
			Accept = `Practice lanes are west of the field, past the goalposts. Stand on the spot and the machine calls it.`;
			Thanks = `You held. That's a Warden. There's a helmet in the shed with your name on it.`;
			Objectives = {
				{ Id = `Routes`; Type = `Drill`; Drill = `RouteRunner`; Text = `Pass Route Runner on the practice lanes west of the field (6 catches)`; Waypoint = { Kind = `Npc`; Id = `Dunmore` } };
				{ Id = `Play`; Type = `SportMatch`; Sport = `Football`; Text = `Play a full football game (stand on a team pad on the south sideline)`; Waypoint = { Kind = `Npc`; Id = `Dunmore` } };
			};
			Rewards = { Yen = 20; Rep = { Popularity = 3 } };
		};

		AnswerKey = {
			Name = `The Answer Key`; Category = `Side`; Giver = `Vesper`;
			Requires = { NotMember = `Vigil` };
			Summary = `Vesper wants Mr. Hale's chemistry answer key from the staff room. Mr. Hale is always in there marking papers.`;
			Offer = `Hale keeps the chemistry answer key on his desk in the staff room, and he never leaves. Bring it to me without getting caught and the Court will remember it.`;
			Accept = `Stay low. Use the lockers if he turns around.`;
			Thanks = `Oh, that's perfect. Hale's going to lose his mind. Good work.`;
			Stealth = { Zone = `StaffRoom`; Checkpoint = `Swipe` };
			Objectives = {
				{ Id = `Swipe`; Type = `Collect`; Objects = { `AnswerKey` }; Item = `AnswerKey`; Text = `Sneak into the staff room and swipe the answer key from Mr. Hale's desk` };
				{ Id = `Out`; Type = `Reach`; Area = `StaffExit`; Item = `AnswerKey`; Text = `Get out of the staff room unseen` };
				{ Id = `Give`; Type = `Deliver`; Npc = `Vesper`; Item = `AnswerKey`; Text = `Bring the answer key to Vesper` };
			};
			Rewards = { Yen = 20; Standing = { CrimsonCourt = 10; Vigil = -5 }; Rep = { Popularity = 2 } };
		};

		---| Bloodline rites (Races Phase 3): started by Services.Player.Evolution when a race's hunger is full |---

		RiteVampire2 = {
			Name = `The Font Below`; Category = `Rite`; Requires = { Rite = { Race = `Vampire`; Tier = 2 } };
			Summary = `Something old waits under the Archive. Go after midnight and drink.`;
			Objectives = {
				{ Id = `Go`; Type = `Reach`; Area = `RiteArchive`; Time = { Night = true }; Text = `Go down to the Archive after dark` };
				{ Id = `Drink`; Type = `Interact`; Object = `BloodFont`; Time = { Night = true }; Text = `Drink from the old stone font` };
			};
		};
		RiteVampire3 = {
			Name = `The Blood Ledger`; Category = `Rite`; Requires = { Rite = { Race = `Vampire`; Tier = 3 } };
			Summary = `The school keeps a ledger of old blood. Take it from the Records Office unseen, then feed before dawn.`;
			Stealth = { Zone = `RecordsOffice`; Checkpoint = `Take` };
			Objectives = {
				{ Id = `Take`; Type = `Collect`; Objects = { `BloodLedger` }; Item = `BloodLedger`; Time = AFTER_HOURS; Text = `Take the blood ledger from the Records Office` };
				{ Id = `Out`; Type = `Reach`; Area = `RecordsExit`; Item = `BloodLedger`; Text = `Get out unseen` };
				{ Id = `Feed`; Type = `Execute`; Count = 1; Time = { Night = true }; Text = `Feed before dawn (finish someone with a grip)` };
			};
		};
		RiteWerewolf2 = {
			Name = `First Hunt`; Category = `Rite`; Requires = { Rite = { Race = `Werewolf`; Tier = 2 } };
			Summary = `The moon is full. Hunt.`;
			Objectives = {
				{ Id = `Hunt`; Type = `Execute`; Count = 3; Time = { Night = true }; FullMoon = true; Text = `On a full-moon night, take down 3 prey (grip finishes)` };
			};
		};
		RiteWerewolf3 = {
			Name = `The Ring at Moonrise`; Category = `Rite`; Requires = { Rite = { Race = `Werewolf`; Tier = 3 } };
			Summary = `Beat the ring's champion after dark, then howl from the boiler stack.`;
			Objectives = {
				{ Id = `Ring`; Type = `Defeat`; Target = `RingChampion`; Time = { Night = true }; Text = `Beat the ring champion after dark (talk to Bruno)` };
				{ Id = `Howl`; Type = `Interact`; Object = `HowlStack`; Time = { Night = true }; Text = `Howl from the boiler stack` };
			};
		};
		RiteGhoul2 = {
			Name = `Grave-eater`; Category = `Rite`; Requires = { Rite = { Race = `Ghoul`; Tier = 2 } };
			Summary = `Dig through the boiler ash for what's left, then feed.`;
			Objectives = {
				{ Id = `Dig`; Type = `Interact`; Object = `AshHeap`; Time = { Night = true }; Text = `Dig through the ash heap in the Boiler Yard at night` };
				{ Id = `Feed`; Type = `Execute`; Count = 1; Text = `Feed (finish someone with a grip)` };
			};
		};
		RiteGhoul3 = {
			Name = `Charnel Feast`; Category = `Rite`; Requires = { Rite = { Race = `Ghoul`; Tier = 3 } };
			Summary = `Feast three times in one night, then lie among the bones.`;
			Objectives = {
				{ Id = `Feast`; Type = `Execute`; Count = 3; Time = { Night = true }; Text = `Feed 3 times in one night` };
				{ Id = `Lie`; Type = `Interact`; Object = `BoneCrate`; Time = { Night = true }; Text = `Lie in the bone crate in the Archive` };
			};
		};
		RiteWraith2 = {
			Name = `Shroud`; Category = `Rite`; Requires = { Rite = { Race = `Wraith`; Tier = 2 } };
			Summary = `Slip past Mr. Hale and touch the cold mirror in the staff room.`;
			Stealth = { Zone = `StaffRoom`; Checkpoint = `Touch` };
			Objectives = {
				{ Id = `Touch`; Type = `Interact`; Object = `ColdMirror`; Text = `Touch the cold mirror in the staff room, unseen` };
				{ Id = `Out`; Type = `Reach`; Area = `StaffExit`; Text = `Get out unseen` };
			};
		};
		RiteWraith3 = {
			Name = `Dirge`; Category = `Rite`; Requires = { Rite = { Race = `Wraith`; Tier = 3 } };
			Summary = `Cross the Records Office after hours and toll the cracked bell.`;
			Stealth = { Zone = `RecordsOffice`; Checkpoint = `Toll` };
			Objectives = {
				{ Id = `Toll`; Type = `Interact`; Object = `CrackedBell`; Time = AFTER_HOURS; Text = `Toll the cracked bell in the Records Office, unseen` };
				{ Id = `Out`; Type = `Reach`; Area = `RecordsExit`; Text = `Get out unseen` };
			};
		};
		RiteHuman2 = {
			Name = `The Hunter's Mark`; Category = `Rite`; Requires = { Rite = { Race = `Human`; Tier = 2 } };
			Summary = `Carve a ward on the Archive door at night and keep watch until dawn.`;
			Objectives = {
				{ Id = `Carve`; Type = `Interact`; Object = `ArchiveWard`; Time = { Night = true }; Text = `Carve a ward on the Archive door at night` };
				{ Id = `Watch`; Type = `Reach`; Area = `RiteArchive`; Time = { Morning = true }; Text = `Be at the Archive at dawn` };
			};
		};
		RiteHuman3 = {
			Name = `Slayer's Oath`; Category = `Rite`; Requires = { Rite = { Race = `Human`; Tier = 3 } };
			Summary = `Prove yourself in the ring, then swear on the boiler iron.`;
			Objectives = {
				{ Id = `Ring`; Type = `Defeat`; Target = `RingChampion`; Text = `Beat the ring champion (talk to Bruno)` };
				{ Id = `Swear`; Type = `Interact`; Object = `OathIron`; Text = `Swear on the iron in the Boiler Yard` };
			};
		};
		RitePriest2 = {
			Name = `Exorcism`; Category = `Rite`; Requires = { Rite = { Race = `Priest`; Tier = 2 } };
			Summary = `Light the three votive candles in the Archive after dark.`;
			Objectives = {
				{ Id = `A`; Type = `Interact`; Object = `VotiveA`; Time = { Night = true }; Text = `Light the first votive candle (Archive, at night)` };
				{ Id = `B`; Type = `Interact`; Object = `VotiveB`; Time = { Night = true }; Text = `Light the second votive candle` };
				{ Id = `C`; Type = `Interact`; Object = `VotiveC`; Time = { Night = true }; Text = `Light the third votive candle` };
			};
		};
		RitePriest3 = {
			Name = `Sainthood`; Category = `Rite`; Requires = { Rite = { Race = `Priest`; Tier = 3 } };
			Summary = `Keep a vigil in the ring at dawn.`;
			Objectives = {
				{ Id = `Go`; Type = `Reach`; Area = `DuelRing`; Time = { Morning = true }; Text = `Go to the ring at dawn` };
				{ Id = `Vigil`; Type = `Interact`; Object = `VigilStone`; Time = { Morning = true }; Text = `Keep vigil at the ring stone` };
			};
		};
		---| Clique leader quests (Cliques Phase 3, 1.28) |---
		-- Two per leader. Quest 1 opens at Neutral standing (-10), quest 2 at Friendly (20) after quest 1. Finishing quest 2
		-- while Respected (60) unlocks the clique's reward (Social.Cliques). Rewards.Cliques raise standing (the rival
		-- loses a quarter). Scuffle objectives: win a scuffle for that clique (Social.CliqueFights reports it).
		CliqueVigil1 = {
			Name = `Lamplighter`; Category = `Clique`; Giver = `Ezra`;
			Requires = { Clique = { Id = `Vigil`; Min = -10 } };
			Summary = `Ezra wants the old lamps around the Archive lit after dark, the way the Vigil always kept them.`;
			Offer = `The lamps by the Archive have gone dark three nights running. Someone keeps putting them out. Light them for me, after dark.`;
			Accept = `Good. Don't let anyone see you're doing it for us.`;
			Thanks = `They're burning. Whoever's snuffing them will know we noticed.`;
			Objectives = {
				{ Id = `LampA`; Type = `Interact`; Object = `VigilLampA`; Time = AFTER_HOURS; Text = `After dark (5 PM on), light the lamp by the Archive door` };
				{ Id = `LampB`; Type = `Interact`; Object = `VigilLampB`; Time = AFTER_HOURS; Text = `Light the hall lamp` };
				{ Id = `LampC`; Type = `Interact`; Object = `VigilLampC`; Time = AFTER_HOURS; Text = `Light the stair lamp` };
				{ Id = `Back`; Type = `Talk`; Npc = `Ezra`; Text = `Tell Ezra the lamps are lit`; Waypoint = { Kind = `Npc`; Id = `Ezra` } };
			};
			Rewards = { Yen = 20; Cliques = { Vigil = 20 } };
		};
		CliqueVigil2 = {
			Name = `The Missing Page`; Category = `Clique`; Giver = `Ezra`;
			Requires = { Quests = { `CliqueVigil1` }; Clique = { Id = `Vigil`; Min = 20 } };
			Summary = `A page is missing from the school's 1893 records. Ezra thinks it's in the Records Office.`;
			Offer = `There's a page missing from 1893. The year the bell first rang by itself. I think the office has it. Bring it to me.`;
			Accept = `After hours. Quietly. If they catch you, you never met me.`;
			Thanks = `...So it's true. Keep this between us. You're one of the Vigil now, whether you like it or not.`;
			Objectives = {
				{ Id = `Take`; Type = `Collect`; Objects = { `Page1893` }; Item = `Page1893`; Time = AFTER_HOURS; Text = `After hours, find the missing page in the Records Office` };
				{ Id = `Bring`; Type = `Deliver`; Npc = `Ezra`; Item = `Page1893`; Text = `Bring the page to Ezra at the Archive (you'll drop it if you're downed)` };
			};
			Rewards = { Yen = 40; Cliques = { Vigil = 30 } };
		};
		CliqueCourt1 = {
			Name = `An Invitation`; Category = `Clique`; Giver = `Vesper`;
			Requires = { Clique = { Id = `Court`; Min = -10 } };
			Summary = `Vesper wants a sealed invitation delivered to Lucien Grey at the Chapel, quickly.`;
			Offer = `Be a dear and take this to Lucien at the Chapel. Don't open it. Don't dawdle. Don't drop it.`;
			Accept = `Run along.`;
			Thanks = `He took it? Delicious. You may be useful after all.`;
			TimeLimit = 40;
			StartItems = { `Invitation` };
			Objectives = {
				{ Id = `Deliver`; Type = `Deliver`; Npc = `Lucien`; Item = `Invitation`; Text = `Deliver the invitation to Lucien Grey at the Chapel before time runs out`; Waypoint = { Kind = `Npc`; Id = `Lucien` } };
				{ Id = `Back`; Type = `Talk`; Npc = `Vesper`; Text = `Tell Vesper it's done`; Waypoint = { Kind = `Npc`; Id = `Vesper` } };
			};
			Rewards = { Yen = 20; Cliques = { Court = 20 } };
		};
		CliqueCourt2 = {
			Name = `Bad Blood`; Category = `Clique`; Giver = `Vesper`;
			Requires = { Quests = { `CliqueCourt1` }; Clique = { Id = `Court`; Min = 20 } };
			Summary = `The Vigil have been sniffing around the Parlor. Fight for the Court the next time it comes to blows.`;
			Offer = `The Vigil think they can stare at us. Next time our people and theirs come to blows, be on the right side.`;
			Accept = `Make it memorable.`;
			Thanks = `Blood looks good on you. Welcome to the Court.`;
			Objectives = {
				{ Id = `Brawl`; Type = `Scuffle`; Clique = `Court`; Text = `Help the Court win a scuffle against the Vigil (put at least one down)` };
			};
			Rewards = { Yen = 40; Cliques = { Court = 30 } };
		};
		CliqueAthletes1 = {
			Name = `Warm-up`; Category = `Clique`; Giver = `Rhys`;
			Requires = { Clique = { Id = `Athletes`; Min = -10 } };
			Summary = `Captain Thorne wants to see you hit a target before he lets you near his team.`;
			Offer = `You want in with the team? Show me you can throw. Target Practice, south of the pitch. Then we'll talk.`;
			Accept = `Don't embarrass me.`;
			Thanks = `Not bad. Not bad at all. Stick around.`;
			Objectives = {
				{ Id = `Throw`; Type = `Drill`; Drill = `TargetPractice`; Text = `Pass Target Practice south of the pitch (4 targets)` };
				{ Id = `Back`; Type = `Talk`; Npc = `Rhys`; Text = `Report to Captain Thorne at the gym`; Waypoint = { Kind = `Npc`; Id = `Rhys` } };
			};
			Rewards = { Yen = 20; Cliques = { Athletes = 20 } };
		};
		CliqueAthletes2 = {
			Name = `Bench Them`; Category = `Clique`; Giver = `Rhys`;
			Requires = { Quests = { `CliqueAthletes1` }; Clique = { Id = `Athletes`; Min = 20 } };
			Summary = `The Ink Club painted the scoreboard. Captain Thorne wants them benched.`;
			Offer = `Those paint-sniffers drew on my scoreboard. Next time we go at it with the Ink Club, you're on my team.`;
			Accept = `Game face on.`;
			Thanks = `That's how it's done! You're varsity now.`;
			Objectives = {
				{ Id = `Brawl`; Type = `Scuffle`; Clique = `Athletes`; Text = `Help the Athletes win a scuffle against the Ink Club (put at least one down)` };
			};
			Rewards = { Yen = 40; Cliques = { Athletes = 30 } };
		};
		CliqueDelinquents1 = {
			Name = `Five-Finger Discount`; Category = `Clique`; Giver = `Bruno`;
			Requires = { Clique = { Id = `Delinquents`; Min = -10 } };
			Summary = `Bruno wants a crate of snacks swiped from behind the concession stand after hours.`;
			Offer = `Lunch lady leaves a crate out back of the stand at night. Bring it to me and nobody gets hurt. Probably.`;
			Accept = `Don't get caught. Or do, I don't care.`;
			Thanks = `Ha! Look at that. You've got sticky fingers, kid.`;
			Objectives = {
				{ Id = `Swipe`; Type = `Collect`; Objects = { `SnackCrate` }; Item = `SnackCrate`; Time = AFTER_HOURS; Text = `After hours, swipe the snack crate from behind the concession stand` };
				{ Id = `Bring`; Type = `Deliver`; Npc = `Bruno`; Item = `SnackCrate`; Text = `Bring the crate to Bruno (you'll drop it if you're downed)`; Waypoint = { Kind = `Npc`; Id = `Bruno` } };
			};
			Rewards = { Yen = 20; Cliques = { Delinquents = 20 } };
		};
		CliqueDelinquents2 = {
			Name = `The Lot's Champion`; Category = `Clique`; Giver = `Bruno`;
			Requires = { Quests = { `CliqueDelinquents1` }; Clique = { Id = `Delinquents`; Min = 20 } };
			Summary = `Bruno wants you to beat the ring champion. Then the Back Lot is yours too.`;
			Offer = `Want real respect on the Lot? Beat my champion. Say the word and I'll call him out.`;
			Accept = `Ring's waiting.`;
			Thanks = `You actually did it. The Lot's yours, pal. Anybody gives you trouble, they answer to us.`;
			Objectives = {
				{ Id = `Beat`; Type = `Defeat`; Target = `RingChampion`; Text = `Talk to Bruno to call out the champion, then down him in the ring`; Waypoint = { Kind = `Npc`; Id = `Bruno` } };
			};
			Rewards = { Yen = 40; Cliques = { Delinquents = 30 } };
		};
		CliquePack1 = {
			Name = `Lunch Money`; Category = `Clique`; Giver = `Dex`;
			Requires = { Clique = { Id = `Pack`; Min = -10 } };
			Summary = `Dex wants the first-years' hiding spots around the Commons shaken down.`;
			Offer = `The Ordinary stash their lunch money around the Commons. The fountain bench, the notice board, the sundial. Shake 'em down.`;
			Accept = `Fast. Before they notice.`;
			Thanks = `Heh. You've got teeth after all.`;
			Objectives = {
				{ Id = `ShakeA`; Type = `Interact`; Object = `LunchMoneyA`; Text = `Shake down the bench by the Commons fountain` };
				{ Id = `ShakeB`; Type = `Interact`; Object = `LunchMoneyB`; Text = `Shake down the Commons notice board` };
				{ Id = `ShakeC`; Type = `Interact`; Object = `LunchMoneyC`; Text = `Shake down the sundial` };
				{ Id = `Back`; Type = `Talk`; Npc = `Dex`; Text = `Bring Dex his cut`; Waypoint = { Kind = `Npc`; Id = `Dex` } };
			};
			Rewards = { Yen = 25; Cliques = { Pack = 20; Ordinary = -10 } };
		};
		CliquePack2 = {
			Name = `Raid the Chapel`; Category = `Clique`; Giver = `Dex`;
			Requires = { Quests = { `CliquePack1` }; Clique = { Id = `Pack`; Min = 20 } };
			Summary = `Dex wants the Choir taught a lesson. Fight for the Pack the next time they clash.`;
			Offer = `The choirboys keep waving crosses at us. Next time we hit the Chapel, you run with us.`;
			Accept = `Bare your teeth.`;
			Thanks = `You run with the Pack now. Nobody touches you.`;
			Objectives = {
				{ Id = `Brawl`; Type = `Scuffle`; Clique = `Pack`; Text = `Help the Pack win a scuffle against the Chapel Choir (put at least one down)` };
			};
			Rewards = { Yen = 40; Cliques = { Pack = 30 } };
		};
		CliqueOrdinary1 = {
			Name = `Hall Pass`; Category = `Clique`; Giver = `Pip`;
			Requires = { Clique = { Id = `Ordinary`; Min = -10 } };
			Summary = `Pip needs a forged hall pass taken to Coach Mallory before the bell, to save a friend from detention.`;
			Offer = `My friend's about to get detention for something she didn't do. Coach Mallory can fix it if he gets this pass in time. Please?`;
			Accept = `Thank you thank you thank you.`;
			Thanks = `You saved her! You're the best. Seriously.`;
			TimeLimit = 30;
			StartItems = { `HallPass` };
			Objectives = {
				{ Id = `Deliver`; Type = `Deliver`; Npc = `Mallory`; Item = `HallPass`; Text = `Get the hall pass to Coach Mallory at the pitch before time runs out`; Waypoint = { Kind = `Npc`; Id = `Mallory` } };
			};
			Rewards = { Yen = 20; Cliques = { Ordinary = 20 } };
		};
		CliqueOrdinary2 = {
			Name = `Stand Together`; Category = `Clique`; Giver = `Pip`;
			Requires = { Quests = { `CliqueOrdinary1` }; Clique = { Id = `Ordinary`; Min = 20 } };
			Summary = `The Delinquents keep pushing the Ordinary around. Pip wants you there when they finally push back.`;
			Offer = `We're done being pushed around. Next time the Delinquents start something at the Commons, we fight. Will you be there?`;
			Accept = `Strength in numbers!`;
			Thanks = `We did it! We actually did it. You're one of us. Always.`;
			Objectives = {
				{ Id = `Brawl`; Type = `Scuffle`; Clique = `Ordinary`; Text = `Help the Ordinary win a scuffle against the Delinquents (put at least one down)` };
			};
			Rewards = { Yen = 40; Cliques = { Ordinary = 30 } };
		};
		CliqueChoir1 = {
			Name = `Candles at Dusk`; Category = `Clique`; Giver = `Lucien`;
			Requires = { Clique = { Id = `Choir`; Min = -10 } };
			Summary = `Lucien asks you to light the Chapel votives at dusk.`;
			Offer = `The votives must be lit at dusk, every night, without fail. The others are rehearsing. Would you?`;
			Accept = `Mind the wax. And whatever you hear, keep lighting.`;
			Thanks = `Thank you. The Chapel feels safer tonight. So do I.`;
			Objectives = {
				{ Id = `LightA`; Type = `Interact`; Object = `ChoirVotiveA`; Time = AFTER_HOURS; Text = `After 5 PM, light the first Chapel votive` };
				{ Id = `LightB`; Type = `Interact`; Object = `ChoirVotiveB`; Time = AFTER_HOURS; Text = `Light the second votive` };
				{ Id = `LightC`; Type = `Interact`; Object = `ChoirVotiveC`; Time = AFTER_HOURS; Text = `Light the third votive` };
				{ Id = `Back`; Type = `Talk`; Npc = `Lucien`; Text = `Tell Lucien the candles are lit`; Waypoint = { Kind = `Npc`; Id = `Lucien` } };
			};
			Rewards = { Yen = 20; Cliques = { Choir = 20 } };
		};
		CliqueChoir2 = {
			Name = `Drive Them Out`; Category = `Clique`; Giver = `Lucien`;
			Requires = { Quests = { `CliqueChoir1` }; Clique = { Id = `Choir`; Min = 20 } };
			Summary = `The Pack keep coming for the Chapel. Lucien asks you to stand with the Choir.`;
			Offer = `The wolves will come again. When they do, stand with us. We're not as helpless as they think.`;
			Accept = `Faith, and fists.`;
			Thanks = `You stood with us. The Choir won't forget. Sing with us whenever you like.`;
			Objectives = {
				{ Id = `Brawl`; Type = `Scuffle`; Clique = `Choir`; Text = `Help the Chapel Choir win a scuffle against the Pack (put at least one down)` };
			};
			Rewards = { Yen = 40; Cliques = { Choir = 30 } };
		};
		CliqueInk1 = {
			Name = `Fresh Canvas`; Category = `Clique`; Giver = `Wren`;
			Requires = { Clique = { Id = `Ink`; Min = -10 } };
			Summary = `Wren needs red paint from the supply cupboard by Room 105.`;
			Offer = `We're out of red. The good red. There's a supply cupboard by Room 105. Borrow some. Permanently.`;
			Accept = `Don't spill it on your shoes.`;
			Thanks = `Perfect shade. You've got an eye.`;
			Objectives = {
				{ Id = `Take`; Type = `Collect`; Objects = { `PaintShelf` }; Item = `PaintCan`; Text = `Take a can of red paint from the supply cupboard by Room 105` };
				{ Id = `Bring`; Type = `Deliver`; Npc = `Wren`; Item = `PaintCan`; Text = `Bring the paint to Wren at the Ink Studio`; Waypoint = { Kind = `Npc`; Id = `Wren` } };
			};
			Rewards = { Yen = 20; Cliques = { Ink = 20 } };
		};
		CliqueInk2 = {
			Name = `Masterpiece`; Category = `Clique`; Giver = `Wren`;
			Requires = { Quests = { `CliqueInk1` }; Clique = { Id = `Ink`; Min = 20 } };
			Summary = `Wren wants the gym doors turned into art while the Athletes are at practice.`;
			Offer = `The gym doors are so... beige. Tag them while the jocks are at practice. After school. Then get back here before anyone sees.`;
			Accept = `Art waits for no one. Neither do hall monitors.`;
			Thanks = `IT'S BEAUTIFUL. You're an Ink Club legend now.`;
			Objectives = {
				{ Id = `Tag`; Type = `Interact`; Object = `GymDoors`; Time = { AfterSchool = true }; Text = `After school, tag the gym doors (a hall monitor who sees you books it as vandalism)` };
				{ Id = `Away`; Type = `Reach`; Area = `InkStudioQuest`; Text = `Get back to the Ink Studio` };
				{ Id = `Back`; Type = `Talk`; Npc = `Wren`; Text = `Tell Wren`; Waypoint = { Kind = `Npc`; Id = `Wren` } };
			};
			Rewards = { Yen = 40; Cliques = { Ink = 30; Athletes = -10 } };
		};



		---| Phase 6 (1.35): member jobs. Job = true: members only (Social.CliqueMembership); the leader's job of the day
		-- is one of three (Quests.JobFor), done for the event day, gone at 6 AM. |---
		JobAthletes1 = {
			Name = `Hold the Line`; Category = `Job`; Giver = `Rhys`; Job = true; Clique = `Athletes`; Repeatable = `Daily`;
			Summary = `Today's job for the Athletes.`;
			Offer = `Ink Club's been mouthing off. Win two fights for us today.`;
			Accept = `Good. Before dawn.`;
			Thanks = `That's what members are for.`;
			Objectives = {
				{ Id = `Brawl`; Type = `Scuffle`; Clique = `Athletes`; Count = 2; Text = `Win 2 scuffles or rumbles for the Athletes (put at least one down in each)` };
			};
			Rewards = { Yen = 25; Cliques = { Athletes = 6 } };
		};
		JobAthletes2 = {
			Name = `Payback`; Category = `Job`; Giver = `Rhys`; Job = true; Clique = `Athletes`; Repeatable = `Daily`;
			Summary = `Today's job for the Athletes.`;
			Offer = `Tag their studio. Twice. Show them whose school it is.`;
			Accept = `Good. Before dawn.`;
			Thanks = `That's what members are for.`;
			Objectives = {
				{ Id = `Prank`; Type = `Prank`; Victim = `Ink`; Count = 2; Text = `Prank the Ink Studio twice (prank kits from the concession stand)` };
			};
			Rewards = { Yen = 25; Cliques = { Athletes = 6 } };
		};
		JobAthletes3 = {
			Name = `Guard Duty`; Category = `Job`; Giver = `Rhys`; Job = true; Clique = `Athletes`; Repeatable = `Daily`;
			Summary = `Today's job for the Athletes.`;
			Offer = `The paint-sniffers are planning something at the gym. Stop them.`;
			Accept = `Good. Before dawn.`;
			Thanks = `That's what members are for.`;
			Objectives = {
				{ Id = `Guard`; Type = `StopPrank`; Victim = `Athletes`; Text = `The Ink Club are coming to prank the Gymnasium: stop them (put the prankster down)` };
			};
			Rewards = { Yen = 25; Cliques = { Athletes = 6 } };
		};
		JobDelinquents1 = {
			Name = `Hold the Line`; Category = `Job`; Giver = `Bruno`; Job = true; Clique = `Delinquents`; Repeatable = `Daily`;
			Summary = `Today's job for the Delinquents.`;
			Offer = `Ordinary kids are getting brave. Win us two fights today.`;
			Accept = `Good. Before dawn.`;
			Thanks = `That's what members are for.`;
			Objectives = {
				{ Id = `Brawl`; Type = `Scuffle`; Clique = `Delinquents`; Count = 2; Text = `Win 2 scuffles or rumbles for the Delinquents (put at least one down in each)` };
			};
			Rewards = { Yen = 25; Cliques = { Delinquents = 6 } };
		};
		JobDelinquents2 = {
			Name = `Payback`; Category = `Job`; Giver = `Bruno`; Job = true; Clique = `Delinquents`; Repeatable = `Daily`;
			Summary = `Today's job for the Delinquents.`;
			Offer = `Mess up the Commons for me. Twice.`;
			Accept = `Good. Before dawn.`;
			Thanks = `That's what members are for.`;
			Objectives = {
				{ Id = `Prank`; Type = `Prank`; Victim = `Ordinary`; Count = 2; Text = `Prank the Commons twice (prank kits from the concession stand)` };
			};
			Rewards = { Yen = 25; Cliques = { Delinquents = 6 } };
		};
		JobDelinquents3 = {
			Name = `Guard Duty`; Category = `Job`; Giver = `Bruno`; Job = true; Clique = `Delinquents`; Repeatable = `Daily`;
			Summary = `Today's job for the Delinquents.`;
			Offer = `Somebody's gonna try something at the Lot. Be there.`;
			Accept = `Good. Before dawn.`;
			Thanks = `That's what members are for.`;
			Objectives = {
				{ Id = `Guard`; Type = `StopPrank`; Victim = `Delinquents`; Text = `The Ordinary are coming to prank the Back Lot: stop them (put the prankster down)` };
			};
			Rewards = { Yen = 25; Cliques = { Delinquents = 6 } };
		};
		JobPack1 = {
			Name = `Hold the Line`; Category = `Job`; Giver = `Dex`; Job = true; Clique = `Pack`; Repeatable = `Daily`;
			Summary = `Today's job for the Pack.`;
			Offer = `The Choir need reminding who runs this place. Two fights. Win them.`;
			Accept = `Good. Before dawn.`;
			Thanks = `That's what members are for.`;
			Objectives = {
				{ Id = `Brawl`; Type = `Scuffle`; Clique = `Pack`; Count = 2; Text = `Win 2 scuffles or rumbles for the Pack (put at least one down in each)` };
			};
			Rewards = { Yen = 25; Cliques = { Pack = 6 } };
		};
		JobPack2 = {
			Name = `Payback`; Category = `Job`; Giver = `Dex`; Job = true; Clique = `Pack`; Repeatable = `Daily`;
			Summary = `Today's job for the Pack.`;
			Offer = `Stink up the Chapel. Twice.`;
			Accept = `Good. Before dawn.`;
			Thanks = `That's what members are for.`;
			Objectives = {
				{ Id = `Prank`; Type = `Prank`; Victim = `Choir`; Count = 2; Text = `Prank the Chapel twice (prank kits from the concession stand)` };
			};
			Rewards = { Yen = 25; Cliques = { Pack = 6 } };
		};
		JobPack3 = {
			Name = `Guard Duty`; Category = `Job`; Giver = `Dex`; Job = true; Clique = `Pack`; Repeatable = `Daily`;
			Summary = `Today's job for the Pack.`;
			Offer = `Choir kids are coming to the Den. Make them regret it.`;
			Accept = `Good. Before dawn.`;
			Thanks = `That's what members are for.`;
			Objectives = {
				{ Id = `Guard`; Type = `StopPrank`; Victim = `Pack`; Text = `The Chapel Choir are coming to prank the Den: stop them (put the prankster down)` };
			};
			Rewards = { Yen = 25; Cliques = { Pack = 6 } };
		};
		JobOrdinary1 = {
			Name = `Hold the Line`; Category = `Job`; Giver = `Pip`; Job = true; Clique = `Ordinary`; Repeatable = `Daily`;
			Summary = `Today's job for the Ordinary.`;
			Offer = `The Delinquents keep picking on us. Could you win two fights for us? Please?`;
			Accept = `Good. Before dawn.`;
			Thanks = `That's what members are for.`;
			Objectives = {
				{ Id = `Brawl`; Type = `Scuffle`; Clique = `Ordinary`; Count = 2; Text = `Win 2 scuffles or rumbles for the Ordinary (put at least one down in each)` };
			};
			Rewards = { Yen = 25; Cliques = { Ordinary = 6 } };
		};
		JobOrdinary2 = {
			Name = `Payback`; Category = `Job`; Giver = `Pip`; Job = true; Clique = `Ordinary`; Repeatable = `Daily`;
			Summary = `Today's job for the Ordinary.`;
			Offer = `Get the Back Lot back for what they did. Twice!`;
			Accept = `Good. Before dawn.`;
			Thanks = `That's what members are for.`;
			Objectives = {
				{ Id = `Prank`; Type = `Prank`; Victim = `Delinquents`; Count = 2; Text = `Prank the Back Lot twice (prank kits from the concession stand)` };
			};
			Rewards = { Yen = 25; Cliques = { Ordinary = 6 } };
		};
		JobOrdinary3 = {
			Name = `Guard Duty`; Category = `Job`; Giver = `Pip`; Job = true; Clique = `Ordinary`; Repeatable = `Daily`;
			Summary = `Today's job for the Ordinary.`;
			Offer = `I heard they're coming to mess up the Commons. Can you stop them?`;
			Accept = `Good. Before dawn.`;
			Thanks = `That's what members are for.`;
			Objectives = {
				{ Id = `Guard`; Type = `StopPrank`; Victim = `Ordinary`; Text = `The Delinquents are coming to prank the Commons: stop them (put the prankster down)` };
			};
			Rewards = { Yen = 25; Cliques = { Ordinary = 6 } };
		};
		JobChoir1 = {
			Name = `Hold the Line`; Category = `Job`; Giver = `Lucien`; Job = true; Clique = `Choir`; Repeatable = `Daily`;
			Summary = `Today's job for the Chapel Choir.`;
			Offer = `The Pack trouble us. Stand with us in two fights today.`;
			Accept = `Good. Before dawn.`;
			Thanks = `That's what members are for.`;
			Objectives = {
				{ Id = `Brawl`; Type = `Scuffle`; Clique = `Choir`; Count = 2; Text = `Win 2 scuffles or rumbles for the Chapel Choir (put at least one down in each)` };
			};
			Rewards = { Yen = 25; Cliques = { Choir = 6 } };
		};
		JobChoir2 = {
			Name = `Payback`; Category = `Job`; Giver = `Lucien`; Job = true; Clique = `Choir`; Repeatable = `Daily`;
			Summary = `Today's job for the Chapel Choir.`;
			Offer = `Return the Pack's filth to the Den. Twice.`;
			Accept = `Good. Before dawn.`;
			Thanks = `That's what members are for.`;
			Objectives = {
				{ Id = `Prank`; Type = `Prank`; Victim = `Pack`; Count = 2; Text = `Prank the Den twice (prank kits from the concession stand)` };
			};
			Rewards = { Yen = 25; Cliques = { Choir = 6 } };
		};
		JobChoir3 = {
			Name = `Guard Duty`; Category = `Job`; Giver = `Lucien`; Job = true; Clique = `Choir`; Repeatable = `Daily`;
			Summary = `Today's job for the Chapel Choir.`;
			Offer = `The Pack plan to desecrate the Chapel. Stop them.`;
			Accept = `Good. Before dawn.`;
			Thanks = `That's what members are for.`;
			Objectives = {
				{ Id = `Guard`; Type = `StopPrank`; Victim = `Choir`; Text = `The Pack are coming to prank the Chapel: stop them (put the prankster down)` };
			};
			Rewards = { Yen = 25; Cliques = { Choir = 6 } };
		};
		JobInk1 = {
			Name = `Hold the Line`; Category = `Job`; Giver = `Wren`; Job = true; Clique = `Ink`; Repeatable = `Daily`;
			Summary = `Today's job for the Ink Club.`;
			Offer = `The jocks need humbling. Win two fights for us.`;
			Accept = `Good. Before dawn.`;
			Thanks = `That's what members are for.`;
			Objectives = {
				{ Id = `Brawl`; Type = `Scuffle`; Clique = `Ink`; Count = 2; Text = `Win 2 scuffles or rumbles for the Ink Club (put at least one down in each)` };
			};
			Rewards = { Yen = 25; Cliques = { Ink = 6 } };
		};
		JobInk2 = {
			Name = `Payback`; Category = `Job`; Giver = `Wren`; Job = true; Clique = `Ink`; Repeatable = `Daily`;
			Summary = `Today's job for the Ink Club.`;
			Offer = `Redecorate the gym. Twice.`;
			Accept = `Good. Before dawn.`;
			Thanks = `That's what members are for.`;
			Objectives = {
				{ Id = `Prank`; Type = `Prank`; Victim = `Athletes`; Count = 2; Text = `Prank the Gymnasium twice (prank kits from the concession stand)` };
			};
			Rewards = { Yen = 25; Cliques = { Ink = 6 } };
		};
		JobInk3 = {
			Name = `Guard Duty`; Category = `Job`; Giver = `Wren`; Job = true; Clique = `Ink`; Repeatable = `Daily`;
			Summary = `Today's job for the Ink Club.`;
			Offer = `The jocks are coming for the Studio. Defend it.`;
			Accept = `Good. Before dawn.`;
			Thanks = `That's what members are for.`;
			Objectives = {
				{ Id = `Guard`; Type = `StopPrank`; Victim = `Ink`; Text = `The Athletes are coming to prank the Ink Studio: stop them (put the prankster down)` };
			};
			Rewards = { Yen = 25; Cliques = { Ink = 6 } };
		};
		---| Phase 5 (1.34): showdowns. Showdown = <clique>: Social.CliqueShowdowns decides who may start one (as a friend:
		-- Friendly and the leader's quest 2 done; as a foe: their challenge text today) and runs the fight. |---
		ShowdownVigil = {
			Name = `Showdown: Ezra Vale`; Category = `Clique`; Giver = `Ezra`; Showdown = `Vigil`; Clique = `Vigil`;
			Summary = `A one-on-one with Ezra Vale at the Archive, with the Vigil watching. Win and they'll respect you.`;
			Offer = `You want to test yourself against me? The records say you're capable. Let's see. The Archive. I'll be waiting.`;
			Accept = `The Archive. Don't be late.`;
			Thanks = `...Noted. Recorded. You've earned the Vigil's respect.`;
			Objectives = {
				{ Id = `Fight`; Type = `Defeat`; Target = `ShowdownVigil`; Text = `Go to the Archive and beat Ezra Vale (at half health their crew joins in; run and you forfeit)` };
			};
			Rewards = { Yen = 50 };
		};
		ShowdownCourt = {
			Name = `Showdown: Vesper Crane`; Category = `Clique`; Giver = `Vesper`; Showdown = `Court`; Clique = `Court`;
			Summary = `A one-on-one with Vesper Crane at the Crimson Parlor, with the Crimson Court watching. Win and they'll respect you.`;
			Offer = `A duel? How deliciously old-fashioned. Come to the Parlor, darling. Don't keep me waiting.`;
			Accept = `The Crimson Parlor. Don't be late.`;
			Thanks = `You... actually won. How tiresome. The Court bows to you.`;
			Objectives = {
				{ Id = `Fight`; Type = `Defeat`; Target = `ShowdownCourt`; Text = `Go to the Crimson Parlor and beat Vesper Crane (at half health their crew joins in; run and you forfeit)` };
			};
			Rewards = { Yen = 50 };
		};
		ShowdownAthletes = {
			Name = `Showdown: Captain Rhys Thorne`; Category = `Clique`; Giver = `Rhys`; Showdown = `Athletes`; Clique = `Athletes`;
			Summary = `A one-on-one with Captain Rhys Thorne at the Gymnasium, with the Athletes watching. Win and they'll respect you.`;
			Offer = `You want a shot at the captain? Fine. Gym, center court. Bring your A game.`;
			Accept = `The Gymnasium. Don't be late.`;
			Thanks = `Good game. Seriously. You've got the whole team's respect.`;
			Objectives = {
				{ Id = `Fight`; Type = `Defeat`; Target = `ShowdownAthletes`; Text = `Go to the Gymnasium and beat Captain Rhys Thorne (at half health their crew joins in; run and you forfeit)` };
			};
			Rewards = { Yen = 50 };
		};
		ShowdownDelinquents = {
			Name = `Showdown: Bruno Vance`; Category = `Clique`; Giver = `Bruno`; Showdown = `Delinquents`; Clique = `Delinquents`;
			Summary = `A one-on-one with Bruno Vance at the Back Lot, with the Delinquents watching. Win and they'll respect you.`;
			Offer = `You want to go a round with me? Ha! Back Lot. Don't chicken out.`;
			Accept = `The Back Lot. Don't be late.`;
			Thanks = `Okay, okay. You're the real deal. The Lot's got your back.`;
			Objectives = {
				{ Id = `Fight`; Type = `Defeat`; Target = `ShowdownDelinquents`; Text = `Go to the Back Lot and beat Bruno Vance (at half health their crew joins in; run and you forfeit)` };
			};
			Rewards = { Yen = 50 };
		};
		ShowdownPack = {
			Name = `Showdown: Dex Moreno`; Category = `Clique`; Giver = `Dex`; Showdown = `Pack`; Clique = `Pack`;
			Summary = `A one-on-one with Dex Moreno at the Den, with the Pack watching. Win and they'll respect you.`;
			Offer = `You think you can take the alpha? Come to the Den. Let's find out.`;
			Accept = `The Den. Don't be late.`;
			Thanks = `Heh. Okay. You're Pack now, whether you like it or not.`;
			Objectives = {
				{ Id = `Fight`; Type = `Defeat`; Target = `ShowdownPack`; Text = `Go to the Den and beat Dex Moreno (at half health their crew joins in; run and you forfeit)` };
			};
			Rewards = { Yen = 50 };
		};
		ShowdownOrdinary = {
			Name = `Showdown: Pip Larkin`; Category = `Clique`; Giver = `Pip`; Showdown = `Ordinary`; Clique = `Ordinary`;
			Summary = `A one-on-one with Pip Larkin at the Commons, with the Ordinary watching. Win and they'll respect you.`;
			Offer = `You want to... fight me? Okay. Okay! The Commons. I've been practising!`;
			Accept = `The Commons. Don't be late.`;
			Thanks = `I lost! But that was amazing! Everybody, they're one of us now!`;
			Objectives = {
				{ Id = `Fight`; Type = `Defeat`; Target = `ShowdownOrdinary`; Text = `Go to the Commons and beat Pip Larkin (at half health their crew joins in; run and you forfeit)` };
			};
			Rewards = { Yen = 50 };
		};
		ShowdownChoir = {
			Name = `Showdown: Lucien Grey`; Category = `Clique`; Giver = `Lucien`; Showdown = `Choir`; Clique = `Choir`;
			Summary = `A one-on-one with Lucien Grey at the Chapel, with the Chapel Choir watching. Win and they'll respect you.`;
			Offer = `You seek a trial? Very well. The Chapel. May the righteous prevail.`;
			Accept = `The Chapel. Don't be late.`;
			Thanks = `Truly, you were sent to test us. The Choir honours you.`;
			Objectives = {
				{ Id = `Fight`; Type = `Defeat`; Target = `ShowdownChoir`; Text = `Go to the Chapel and beat Lucien Grey (at half health their crew joins in; run and you forfeit)` };
			};
			Rewards = { Yen = 50 };
		};
		ShowdownInk = {
			Name = `Showdown: Wren Ashby`; Category = `Clique`; Giver = `Wren`; Showdown = `Ink`; Clique = `Ink`;
			Summary = `A one-on-one with Wren Ashby at the Ink Studio, with the Ink Club watching. Win and they'll respect you.`;
			Offer = `A fight? With me? How dramatic. Ink Studio. Make it a masterpiece.`;
			Accept = `The Ink Studio. Don't be late.`;
			Thanks = `Ugh. That was beautiful. You're one of us now.`;
			Objectives = {
				{ Id = `Fight`; Type = `Defeat`; Target = `ShowdownInk`; Text = `Go to the Ink Studio and beat Wren Ashby (at half health their crew joins in; run and you forfeit)` };
			};
			Rewards = { Yen = 50 };
		};
		---| Phase 4 (1.33): daily dares. Dare = true: a leader's dare of the day is one of these three, picked by the
		-- day (Quests.DareFor); the leader texts it in the morning (Social.CliqueEvents) or you ask in person. Gone at 6 AM. |---
		DareVigil1 = {
			Name = `Ink in the Parlor`; Category = `Dare`; Giver = `Ezra`; Dare = true; Clique = `Vigil`; Repeatable = `Daily`;
			Requires = { Clique = { Id = `Vigil`; Min = -10 } };
			Summary = `Today's dare from the Vigil: prank the Crimson Court at the Crimson Parlor.`;
			Offer = `The Court have been smug all week. Leave them something to remember us by. Quietly.`;
			Accept = `Before dawn. Don't let me down.`;
			Thanks = `They'll be scrubbing for hours. Well done.`;
			Objectives = {
				{ Id = `Prank`; Type = `Prank`; Victim = `Court`; Text = `Prank the Crimson Parlor (the Crimson Court): hold E on a prank spot there with a prank kit from the concession stand` };
			};
			Rewards = { Yen = 15; Cliques = { Vigil = 8 } };
		};
		DareVigil2 = {
			Name = `Hold the Stacks`; Category = `Dare`; Giver = `Ezra`; Dare = true; Clique = `Vigil`; Repeatable = `Daily`;
			Requires = { Clique = { Id = `Vigil`; Min = -10 } };
			Summary = `Today's dare from the Vigil: fight for them the next time they clash with the Crimson Court.`;
			Offer = `If the Court come for us again, I want you with us. Win it.`;
			Accept = `Before dawn. Don't let me down.`;
			Thanks = `That's the Vigil. Steady hands, sharp eyes.`;
			Objectives = {
				{ Id = `Brawl`; Type = `Scuffle`; Clique = `Vigil`; Text = `Help the Vigil win a scuffle or a rumble against the Crimson Court (put at least one down)` };
			};
			Rewards = { Yen = 20; Cliques = { Vigil = 10 } };
		};
		DareVigil3 = {
			Name = `Top Marks`; Category = `Dare`; Giver = `Ezra`; Dare = true; Clique = `Vigil`; Repeatable = `Daily`;
			Requires = { Clique = { Id = `Vigil`; Min = -10 } };
			Summary = `Today's dare from the Vigil: get a B or better in a lesson.`;
			Offer = `Scholars first. Get a B or better in a lesson today. Show them we read.`;
			Accept = `Before dawn. Don't let me down.`;
			Thanks = `A good grade. The records will show it.`;
			Objectives = {
				{ Id = `Grade`; Type = `Lesson`; MinGrade = `B`; Text = `Get a B or better in any lesson today` };
			};
			Rewards = { Yen = 10; Cliques = { Vigil = 6 } };
		};
		DareCourt1 = {
			Name = `Smudged Records`; Category = `Dare`; Giver = `Vesper`; Dare = true; Clique = `Court`; Repeatable = `Daily`;
			Requires = { Clique = { Id = `Court`; Min = -10 } };
			Summary = `Today's dare from the Crimson Court: prank the Vigil at the Archive.`;
			Offer = `The Vigil think their little archive is sacred. Make it... less so.`;
			Accept = `Before dawn. Don't let me down.`;
			Thanks = `Delicious. I could hear them gasp from here.`;
			Objectives = {
				{ Id = `Prank`; Type = `Prank`; Victim = `Vigil`; Text = `Prank the Archive (the Vigil): hold E on a prank spot there with a prank kit from the concession stand` };
			};
			Rewards = { Yen = 15; Cliques = { Court = 8 } };
		};
		DareCourt2 = {
			Name = `A Night to Remember`; Category = `Dare`; Giver = `Vesper`; Dare = true; Clique = `Court`; Repeatable = `Daily`;
			Requires = { Clique = { Id = `Court`; Min = -10 } };
			Summary = `Today's dare from the Crimson Court: fight for them the next time they clash with the Vigil.`;
			Offer = `Next time the Vigil square up to us, be there. And win, darling.`;
			Accept = `Before dawn. Don't let me down.`;
			Thanks = `Blood suits you. As always.`;
			Objectives = {
				{ Id = `Brawl`; Type = `Scuffle`; Clique = `Court`; Text = `Help the Crimson Court win a scuffle or a rumble against the Vigil (put at least one down)` };
			};
			Rewards = { Yen = 20; Cliques = { Court = 10 } };
		};
		DareCourt3 = {
			Name = `A Little Gloating`; Category = `Dare`; Giver = `Vesper`; Dare = true; Clique = `Court`; Repeatable = `Daily`; TimeLimit = 30; StartItems = { `Invitation` };
			Requires = { Clique = { Id = `Court`; Min = -10 } };
			Summary = `Today's dare from the Crimson Court: take Vesper's note to Ezra within thirty minutes.`;
			Offer = `Take this note to Ezra at the Archive. Thirty minutes. Don't read it.`;
			Accept = `Before dawn. Don't let me down.`;
			Thanks = `He read it? I'd have paid to see his face.`;
			Objectives = {
				{ Id = `Deliver`; Type = `Deliver`; Npc = `Ezra`; Item = `Invitation`; Text = `Deliver Vesper's note to Ezra at the Archive before time runs out`; Waypoint = { Kind = `Npc`; Id = `Ezra` } };
			};
			Rewards = { Yen = 10; Cliques = { Court = 6 } };
		};
		DareAthletes1 = {
			Name = `Paint the Painters`; Category = `Dare`; Giver = `Rhys`; Dare = true; Clique = `Athletes`; Repeatable = `Daily`;
			Requires = { Clique = { Id = `Athletes`; Min = -10 } };
			Summary = `Today's dare from the Athletes: prank the Ink Club at the Ink Studio.`;
			Offer = `The Ink Club tagged my bleachers. Return the favour. Studio, today.`;
			Accept = `Before dawn. Don't let me down.`;
			Thanks = `Ha! Taste of their own medicine.`;
			Objectives = {
				{ Id = `Prank`; Type = `Prank`; Victim = `Ink`; Text = `Prank the Ink Studio (the Ink Club): hold E on a prank spot there with a prank kit from the concession stand` };
			};
			Rewards = { Yen = 15; Cliques = { Athletes = 8 } };
		};
		DareAthletes2 = {
			Name = `Game Day`; Category = `Dare`; Giver = `Rhys`; Dare = true; Clique = `Athletes`; Repeatable = `Daily`;
			Requires = { Clique = { Id = `Athletes`; Min = -10 } };
			Summary = `Today's dare from the Athletes: fight for them the next time they clash with the Ink Club.`;
			Offer = `We fight the Ink Club next chance we get. You're starting. Win it.`;
			Accept = `Before dawn. Don't let me down.`;
			Thanks = `MVP! That's what I'm talking about.`;
			Objectives = {
				{ Id = `Brawl`; Type = `Scuffle`; Clique = `Athletes`; Text = `Help the Athletes win a scuffle or a rumble against the Ink Club (put at least one down)` };
			};
			Rewards = { Yen = 20; Cliques = { Athletes = 10 } };
		};
		DareAthletes3 = {
			Name = `Drills`; Category = `Dare`; Giver = `Rhys`; Dare = true; Clique = `Athletes`; Repeatable = `Daily`;
			Requires = { Clique = { Id = `Athletes`; Min = -10 } };
			Summary = `Today's dare from the Athletes: pass Target Practice.`;
			Offer = `No slacking. Pass Target Practice south of the pitch today.`;
			Accept = `Before dawn. Don't let me down.`;
			Thanks = `Good arm. Keep it up.`;
			Objectives = {
				{ Id = `Throw`; Type = `Drill`; Drill = `TargetPractice`; Text = `Pass Target Practice south of the pitch (4 targets)` };
			};
			Rewards = { Yen = 10; Cliques = { Athletes = 6 } };
		};
		DareDelinquents1 = {
			Name = `Commons Cleanup`; Category = `Dare`; Giver = `Bruno`; Dare = true; Clique = `Delinquents`; Repeatable = `Daily`;
			Requires = { Clique = { Id = `Delinquents`; Min = -10 } };
			Summary = `Today's dare from the Delinquents: prank the Ordinary at the Commons.`;
			Offer = `The Ordinary keep their Commons so tidy. Fix that for me.`;
			Accept = `Before dawn. Don't let me down.`;
			Thanks = `Ha! Look at 'em run around.`;
			Objectives = {
				{ Id = `Prank`; Type = `Prank`; Victim = `Ordinary`; Text = `Prank the Commons (the Ordinary): hold E on a prank spot there with a prank kit from the concession stand` };
			};
			Rewards = { Yen = 15; Cliques = { Delinquents = 8 } };
		};
		DareDelinquents2 = {
			Name = `Turf Talk`; Category = `Dare`; Giver = `Bruno`; Dare = true; Clique = `Delinquents`; Repeatable = `Daily`;
			Requires = { Clique = { Id = `Delinquents`; Min = -10 } };
			Summary = `Today's dare from the Delinquents: fight for them the next time they clash with the Ordinary.`;
			Offer = `Ordinary kids getting brave. Next scuffle, you're with us. We win.`;
			Accept = `Before dawn. Don't let me down.`;
			Thanks = `Not bad, kid. Not bad at all.`;
			Objectives = {
				{ Id = `Brawl`; Type = `Scuffle`; Clique = `Delinquents`; Text = `Help the Delinquents win a scuffle or a rumble against the Ordinary (put at least one down)` };
			};
			Rewards = { Yen = 20; Cliques = { Delinquents = 10 } };
		};
		-- (2.8.1) Bruno's work for suspended students (Requires.Suspended: Quests.CanStart)
		SuspendedDelinquents1 = {
			Name = `Muscle for Hire`; Category = `Clique`; Giver = `Bruno`; Clique = `Delinquents`; Repeatable = `Daily`;
			Requires = { Suspended = true };
			Summary = `Suspended? Bruno has work for you at the Back Lot.`;
			Offer = `Got yourself suspended, huh? Welcome to the real school. The Ordinary think the Lot's theirs now. Show 'em it isn't.`;
			Accept = `Next time they push, you push back harder.`;
			Thanks = `See? You're better at this than at math.`;
			Objectives = {
				{ Id = `Brawl`; Type = `Scuffle`; Clique = `Delinquents`; Text = `Win a scuffle or a rumble for the Delinquents (put at least one down)` };
			};
			Rewards = { Yen = 25; Cliques = { Delinquents = 8 } };
		};
		SuspendedDelinquents2 = {
			Name = `Day Off`; Category = `Clique`; Giver = `Bruno`; Clique = `Delinquents`; Repeatable = `Daily`;
			Requires = { Suspended = true };
			Summary = `Suspended? Leave the Ordinary a message at the Commons. Mind the hall monitor.`;
			Offer = `No classes for you today. Know who's in class? The Ordinary. Their Commons is wide open.`;
			Accept = `In and out. If the monitor sees a suspended kid on campus, you're done.`;
			Thanks = `Ha! And nobody can say you skipped class.`;
			Objectives = {
				{ Id = `Prank`; Type = `Prank`; Victim = `Ordinary`; Text = `Prank the Commons (the Ordinary) with a prank kit. During class the hall monitor books a suspended student on campus for Trespassing` };
			};
			Rewards = { Yen = 25; Cliques = { Delinquents = 8 } };
		};
		DareDelinquents3 = {
			Name = `Ring Time`; Category = `Dare`; Giver = `Bruno`; Dare = true; Clique = `Delinquents`; Repeatable = `Daily`;
			Requires = { Clique = { Id = `Delinquents`; Min = -10 } };
			Summary = `Today's dare from the Delinquents: win a duel in Bruno's ring.`;
			Offer = `Win a duel in my ring today. Anyone. Just win.`;
			Accept = `Before dawn. Don't let me down.`;
			Thanks = `That's the stuff. The ring remembers.`;
			Objectives = {
				{ Id = `Win`; Type = `Duel`; Text = `Win a duel against another student: both stand on the ring pads to start`; Waypoint = { Kind = `Area`; Id = `DuelRing` } };
			};
			Rewards = { Yen = 10; Cliques = { Delinquents = 6 } };
		};
		DarePack1 = {
			Name = `Stink Up the Chapel`; Category = `Dare`; Giver = `Dex`; Dare = true; Clique = `Pack`; Repeatable = `Daily`;
			Requires = { Clique = { Id = `Pack`; Min = -10 } };
			Summary = `Today's dare from the Pack: prank the Chapel Choir at the Chapel.`;
			Offer = `Those choir kids are too clean. Go make the Chapel smell like the Den.`;
			Accept = `Before dawn. Don't let me down.`;
			Thanks = `Heh. They're gonna be praying for fresh air.`;
			Objectives = {
				{ Id = `Prank`; Type = `Prank`; Victim = `Choir`; Text = `Prank the Chapel (the Chapel Choir): hold E on a prank spot there with a prank kit from the concession stand` };
			};
			Rewards = { Yen = 15; Cliques = { Pack = 8 } };
		};
		DarePack2 = {
			Name = `Pack Hunt`; Category = `Dare`; Giver = `Dex`; Dare = true; Clique = `Pack`; Repeatable = `Daily`;
			Requires = { Clique = { Id = `Pack`; Min = -10 } };
			Summary = `Today's dare from the Pack: fight for them the next time they clash with the Chapel Choir.`;
			Offer = `Choir thinks they're tough now. Next fight, you're with the Pack. Win it.`;
			Accept = `Before dawn. Don't let me down.`;
			Thanks = `Now THAT'S Pack blood.`;
			Objectives = {
				{ Id = `Brawl`; Type = `Scuffle`; Clique = `Pack`; Text = `Help the Pack win a scuffle or a rumble against the Chapel Choir (put at least one down)` };
			};
			Rewards = { Yen = 20; Cliques = { Pack = 10 } };
		};
		DarePack3 = {
			Name = `Tax Day`; Category = `Dare`; Giver = `Dex`; Dare = true; Clique = `Pack`; Repeatable = `Daily`;
			Requires = { Clique = { Id = `Pack`; Min = -10 } };
			Summary = `Today's dare from the Pack: shake down the notice board at the Commons.`;
			Offer = `The Commons owe us. Go shake down the notice board for me.`;
			Accept = `Before dawn. Don't let me down.`;
			Thanks = `Easy money. Good.`;
			Objectives = {
				{ Id = `Tax`; Type = `Interact`; Object = `LunchMoneyB`; Text = `Shake down the notice board at the Commons` };
			};
			Rewards = { Yen = 10; Cliques = { Pack = 6 } };
		};
		DareOrdinary1 = {
			Name = `Back at You`; Category = `Dare`; Giver = `Pip`; Dare = true; Clique = `Ordinary`; Repeatable = `Daily`;
			Requires = { Clique = { Id = `Ordinary`; Min = -10 } };
			Summary = `Today's dare from the Ordinary: prank the Delinquents at the Back Lot.`;
			Offer = `The Delinquents trashed our benches again. Could you... maybe... get them back? Just a little?`;
			Accept = `Before dawn. Don't let me down.`;
			Thanks = `Oh no, we're terrible. That was great.`;
			Objectives = {
				{ Id = `Prank`; Type = `Prank`; Victim = `Delinquents`; Text = `Prank the Back Lot (the Delinquents): hold E on a prank spot there with a prank kit from the concession stand` };
			};
			Rewards = { Yen = 15; Cliques = { Ordinary = 8 } };
		};
		DareOrdinary2 = {
			Name = `Stand Up`; Category = `Dare`; Giver = `Pip`; Dare = true; Clique = `Ordinary`; Repeatable = `Daily`;
			Requires = { Clique = { Id = `Ordinary`; Min = -10 } };
			Summary = `Today's dare from the Ordinary: fight for them the next time they clash with the Delinquents.`;
			Offer = `If the Delinquents come at us again, will you stand with us? Please win.`;
			Accept = `Before dawn. Don't let me down.`;
			Thanks = `We did it! You did it!`;
			Objectives = {
				{ Id = `Brawl`; Type = `Scuffle`; Clique = `Ordinary`; Text = `Help the Ordinary win a scuffle or a rumble against the Delinquents (put at least one down)` };
			};
			Rewards = { Yen = 20; Cliques = { Ordinary = 10 } };
		};
		DareOrdinary3 = {
			Name = `Perfect Attendance`; Category = `Dare`; Giver = `Pip`; Dare = true; Clique = `Ordinary`; Repeatable = `Daily`;
			Requires = { Clique = { Id = `Ordinary`; Min = -10 } };
			Summary = `Today's dare from the Ordinary: go to class.`;
			Offer = `Just go to class today. On time. It counts, I promise!`;
			Accept = `Before dawn. Don't let me down.`;
			Thanks = `See? Being normal is a superpower.`;
			Objectives = {
				{ Id = `Class`; Type = `Attend`; Text = `Attend a class today (on time or a little late)` };
			};
			Rewards = { Yen = 10; Cliques = { Ordinary = 6 } };
		};
		DareChoir1 = {
			Name = `A Stench in the Den`; Category = `Dare`; Giver = `Lucien`; Dare = true; Clique = `Choir`; Repeatable = `Daily`;
			Requires = { Clique = { Id = `Choir`; Min = -10 } };
			Summary = `Today's dare from the Chapel Choir: prank the Pack at the Den.`;
			Offer = `The Pack bring their filth to our doors. Return it to them, discreetly.`;
			Accept = `Before dawn. Don't let me down.`;
			Thanks = `May they learn humility. Thank you.`;
			Objectives = {
				{ Id = `Prank`; Type = `Prank`; Victim = `Pack`; Text = `Prank the Den (the Pack): hold E on a prank spot there with a prank kit from the concession stand` };
			};
			Rewards = { Yen = 15; Cliques = { Choir = 8 } };
		};
		DareChoir2 = {
			Name = `Righteous`; Category = `Dare`; Giver = `Lucien`; Dare = true; Clique = `Choir`; Repeatable = `Daily`;
			Requires = { Clique = { Id = `Choir`; Min = -10 } };
			Summary = `Today's dare from the Chapel Choir: fight for them the next time they clash with the Pack.`;
			Offer = `When the Pack come again, stand with the Choir. And prevail.`;
			Accept = `Before dawn. Don't let me down.`;
			Thanks = `Truly, you were sent to us.`;
			Objectives = {
				{ Id = `Brawl`; Type = `Scuffle`; Clique = `Choir`; Text = `Help the Chapel Choir win a scuffle or a rumble against the Pack (put at least one down)` };
			};
			Rewards = { Yen = 20; Cliques = { Choir = 10 } };
		};
		DareChoir3 = {
			Name = `Evensong`; Category = `Dare`; Giver = `Lucien`; Dare = true; Clique = `Choir`; Repeatable = `Daily`;
			Requires = { Clique = { Id = `Choir`; Min = -10 } };
			Summary = `Today's dare from the Chapel Choir: light a votive in the Chapel after 5 PM.`;
			Offer = `Light a votive in the Chapel after five. A small kindness, every day.`;
			Accept = `Before dawn. Don't let me down.`;
			Thanks = `Bless you. The candle burns for you.`;
			Objectives = {
				{ Id = `Light`; Type = `Interact`; Object = `ChoirVotiveA`; Time = AFTER_HOURS; Text = `After 5 PM, light a votive in the Chapel` };
			};
			Rewards = { Yen = 10; Cliques = { Choir = 6 } };
		};
		DareInk1 = {
			Name = `Redecorate`; Category = `Dare`; Giver = `Wren`; Dare = true; Clique = `Ink`; Repeatable = `Daily`;
			Requires = { Clique = { Id = `Ink`; Min = -10 } };
			Summary = `Today's dare from the Ink Club: prank the Athletes at the Gymnasium.`;
			Offer = `The gym is SO boring. Give the Athletes something to look at.`;
			Accept = `Before dawn. Don't let me down.`;
			Thanks = `Oh, it's hideous. I love it.`;
			Objectives = {
				{ Id = `Prank`; Type = `Prank`; Victim = `Athletes`; Text = `Prank the Gymnasium (the Athletes): hold E on a prank spot there with a prank kit from the concession stand` };
			};
			Rewards = { Yen = 15; Cliques = { Ink = 8 } };
		};
		DareInk2 = {
			Name = `Brush Fight`; Category = `Dare`; Giver = `Wren`; Dare = true; Clique = `Ink`; Repeatable = `Daily`;
			Requires = { Clique = { Id = `Ink`; Min = -10 } };
			Summary = `Today's dare from the Ink Club: fight for them the next time they clash with the Athletes.`;
			Offer = `Next time the jocks come for us, fight with us. Win, obviously.`;
			Accept = `Before dawn. Don't let me down.`;
			Thanks = `Art wins. As it should.`;
			Objectives = {
				{ Id = `Brawl`; Type = `Scuffle`; Clique = `Ink`; Text = `Help the Ink Club win a scuffle or a rumble against the Athletes (put at least one down)` };
			};
			Rewards = { Yen = 20; Cliques = { Ink = 10 } };
		};
		DareInk3 = {
			Name = `Art History`; Category = `Dare`; Giver = `Wren`; Dare = true; Clique = `Ink`; Repeatable = `Daily`;
			Requires = { Clique = { Id = `Ink`; Min = -10 } };
			Summary = `Today's dare from the Ink Club: pass any lesson.`;
			Offer = `Pass a lesson today. Any lesson. Artists need to know things too.`;
			Accept = `Before dawn. Don't let me down.`;
			Thanks = `Look at you, educated AND fabulous.`;
			Objectives = {
				{ Id = `Pass`; Type = `Lesson`; Text = `Pass any lesson today` };
			};
			Rewards = { Yen = 10; Cliques = { Ink = 6 } };
		};
	};
}

