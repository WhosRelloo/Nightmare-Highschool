
---| Type Annotation |---

export type PlayerData = {
	
	---| Currencies |---
	
	Yen: number;
	
	---| Stats |---
	
	Weapon: string;
	Armory: { [string]: any };   -- (armory) { Owned = { [class] = true }, V } classes bought at the armory; Fist is always owned (Config.Armory)
	Vow: 'None' | 'Fists' | 'Storms';

	---| Combat Record |---

	Kills: number;     -- players executed with a grip
	NPCKills: number;  -- NPCs executed with a grip

	---| School |---

	Attendance: {
		Totals: { Present: number, Tardy: number, LeftEarly: number, Absent: number, Excused: number };
		Streak: number;          -- classes in a row without Absent / Left Early
		BestStreak: number;
		LastRecordedKey: string; -- guards against recording one class period twice
		Recent: { any };         -- newest first, capped (Config.Classes.Attendance.RecentLimit)
		InProgress: any;         -- the class period being tracked right now (false when none)
	};

	Classes: { [string]: { Level: number, Passes: number, BestGrade: string, LastRewardKey: string } }; -- per subject

	---| Social |---

	Social: {
		Factions: { [string]: any };       -- per faction: Standing, Member, Flags, Missions, ...
		Reputation: { [string]: number };  -- Popularity, Intimidation, Trust, Academics
		Relationships: { [string]: any };  -- per important NPC: Value, Met
		Titles: { string };
		Title: string;                     -- equipped title ("" = none)
	};

	---| Quests |---

	Quests: {
		Active: { [string]: any };  -- per quest: Stage, Counts, Items, Deadline, Data
		Done: { [string]: number }; -- quest -> in-game day completed
		Failed: { [string]: string }; -- quest -> reason (can be retried)
		Cases: { [string]: any };   -- per case: Clues, Insights, Solved
		Tracked: string;
	};

	Discipline: {
		Points: number;
		Level: string;           -- Clear | Warning | Detention | Probation | Suspension
		DetentionsOwed: number;
		DetentionsServed: number;
		ProbationUntilDay: number;  -- in-game day index; -1 = none
		SuspendedUntilDay: number;  -- in-game day index; -1 = none
		LastDecayDay: number;       -- -1 = not started
		HeldPoints: number?;        -- (2.7.3) points from violations during a suspension, added back when it ends
		Recent: { any };         -- newest first
	};

	---| Client preferences & cosmetics (UI kit) |---
	-- Stored sparse: ReplicatedStorage.UI.Settings / UI.Appearance .Sanitize fill the defaults.

	Settings: { [string]: any };    -- volumes, FOV, shake, UI scale, toggles, Keys = { [action]: keyName }
	Appearance: { [string]: any };  -- cosmetic only: LookStyle, skin/hair/eye colours (index or Hex), HairId, Eyes, EyeSet, Uniform, UseAvatar, Created

	---| Lineage (server-rolled; players never choose) |---
	Lineage: { [string]: any };     -- { Race, SubRace, Traits = { id }, Spins = { Race, Variant, Trait } } - ReplicatedStorage.Lineage
	LastPlayed: number;  -- os.time() of the last Enter School (the menu's CONTINUE)
	LastJoined: { [string]: any };  -- { Name, PlaceId, JobId, At } of the last campus joined

	---| Identity (Services.Player.Identity) |---
	Identity: { [string]: any };    -- { First, Clan, Spins, Pity, Rolls, NameChanges, Locked } - clan is server-rolled
	Purchases: { string };          -- recent Robux receipt ids already granted (Services.Player.Purchases), newest last
	Known: { [string]: boolean };   -- students whose name you know, "<UserId>:<Slot>" (Services.Social.Strangers)
	Progress: { [string]: any };    -- { Level, Exp, Points, Stats = { Might, Grit, Wits }, FatedDay } (Services.Player.Progression)
	Sports: { [string]: any };      -- { Club, ClubExp, Record = { [sport] = { W, L } }, Drills } (Services.Sports.Clubs; Config.Sports.Sanitize)
	Inventory: { [string]: any };
	Regions: { [string]: any };     -- { Found = { [RegionId] = true } } (Services.Features.Regions; Config.Regions.Sanitize)
	Arcade: { [string]: any };      -- { Best = { Wisp, Hex, Crypt } } phone arcade bests (Services.Features.PhoneGames)
	Housing: { [string]: any };     -- { Owned, Current, CutOff, DStreak } homes and Mom & Dad's cut-off (Services.Features.Homes)
	Training: { [string]: any };    -- (training 1.81) { Arms/Torso/Legs = { Level, Xp, Path, Sore, SoreAt }, Fed, LastTrained, Day, Streak, Best, ... } (Services.Features.Training; Config.Training.Sanitize)
	Body: { [string]: any };        -- (hunger 1.0) { Hunger, LastTick, Reserve, Race, V } (Services.Features.Body; Config.Body.Sanitize)
	Phone: { [string]: any };       -- { History = { transfers }, Recent = { audio ids } } (Services.Features.Phone)   -- { Items = { [id] = count }, Pinned = { id } } (Services.Features.Inventory; Config.Items.Sanitize)
	
}


local DEFAULT_PLAYER_DATA: PlayerData = {
	
	---| Currencies |---

	Yen = 0;

	---| Stats |---

	Weapon = `Fist`; -- (armory) every student starts on Fist; the katana is bought at the armory (Config.Armory)
	Armory = {};
	Vow = `None`;

	---| Combat Record |---

	Kills = 0;
	NPCKills = 0;

	---| School |---

	Attendance = {
		Totals = { Present = 0; Tardy = 0; LeftEarly = 0; Absent = 0; Excused = 0 };
		Streak = 0;
		BestStreak = 0;
		LastRecordedKey = ``;
		Recent = {};
		InProgress = false;
	};

	Classes = {};

	Social = {
		Factions = {};
		Reputation = { Popularity = 0; Intimidation = 0; Trust = 0; Academics = 0 };
		Relationships = {};
		Titles = {};
		Title = ``;
	};

	Quests = {
		Active = {};
		Done = {};
		Failed = {};
		Cases = {};
		Tracked = ``;
	};

	Discipline = {
		Points = 0;
		Level = `Clear`;
		DetentionsOwed = 0;
		DetentionsServed = 0;
		ProbationUntilDay = -1;
		SuspendedUntilDay = -1;
		LastDecayDay = -1;
		Recent = {};
	};

	Settings = {};
	Appearance = {};
	LastPlayed = 0;
	LastJoined = {};
	Lineage = {};
	Identity = {};
	Purchases = {};
	Known = {};
	Progress = {};
	Sports = {};
	Inventory = {};
	Phone = {};
	Regions = {};
	Arcade = {};
	Housing = {};
	Training = {};
	Body = {};
}


local Shared = {}

Shared.DEFAULT_PLAYER_DATA = DEFAULT_PLAYER_DATA

return Shared
