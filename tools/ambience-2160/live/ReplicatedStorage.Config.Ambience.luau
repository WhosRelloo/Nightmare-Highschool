--[[
	Ambience (data). ReplicatedStorage.Config.Ambience   VFX catalog P2-2 (lamps and ambient emitters) and P2-3 (zone soundscape)

	Everything here is cosmetic and drawn on the client (Controllers.World.Ambient, Controllers.World.Soundscape).
	World effects follow tags (VFX bible rule W1), never part names:
	  NHLamp            a lamp: its lights come on at dusk and go off at dawn (staggered), the part glows while lit
	  NHCandle          a flame: its light flickers softly (Reduce Flashing: barely)
	  NHAmbient:Dust    motes drifting in the air of the part's box (a room's zone part)
	  NHAmbient:Steam   steam rising from the part (pipes, chimney caps)
	  NHAmbient:Embers  embers rising from the part (the boiler's firebox)
	  NHAmbient:Fog     low fog in the part's box (removed on Low effects quality)
	Budgets (style guide, Ambient tier): at most 10 particles a second per emitter, at most 3 emitters running at
	once (the nearest ones on screen), only within 120 studs; Low effects quality halves every rate.

	Sounds are Roblox-licensed Pro Sound Effects loops (Creator Store, VFX decision D4), played as one bed at a time
	through the Music & Ambience volume, crossfading as you move between zones and from day to night.
]]
local Ambience = {}

Ambience.Range = 120          -- studs: emitters further than this from the camera never run
Ambience.MaxEmitters = 3      -- running at once (nearest, on screen)
Ambience.NightFrom = 18.5     -- school-clock hours: lamps on from dusk ...
Ambience.NightTo = 6.5        -- ... until dawn

-- particle textures (the same ones Controllers.Fx uses)
local EMBER, SMOKE, FOG = `rbxassetid://81521204867620`, `rbxassetid://98289186261003`, `rbxassetid://125674379224093`

-- one ambient kind per tagged part
Ambience.Emitters = {
	Dust = {
		Texture = EMBER; Rate = 6; Lifetime = NumberRange.new(5, 8); Speed = NumberRange.new(0.1, 0.35);
		Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.2, 0.09), NumberSequenceKeypoint.new(0.8, 0.09), NumberSequenceKeypoint.new(1, 0) });
		Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.3, 0.45), NumberSequenceKeypoint.new(0.7, 0.45), NumberSequenceKeypoint.new(1, 1) });
		Color = ColorSequence.new(Color3.fromRGB(255, 232, 196)); LightEmission = 0.4; Spread = 180;
		Accel = Vector3.new(0, 0.02, 0); Drag = 0.6; Volume = true;
	};
	Steam = {
		Texture = SMOKE; Flipbook = `Grid4x4`; Rate = 4; Lifetime = NumberRange.new(3, 5); Speed = NumberRange.new(1.2, 2.2);
		Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.6), NumberSequenceKeypoint.new(1, 3.4) });
		Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.15, 0.6), NumberSequenceKeypoint.new(1, 1) });
		Color = ColorSequence.new(Color3.fromRGB(214, 214, 222)); LightEmission = 0.05; Spread = 12;
		Accel = Vector3.new(0.4, 0.8, 0); Drag = 0.8; Up = true;
	};
	Embers = {
		Texture = EMBER; Rate = 8; Lifetime = NumberRange.new(1.6, 3); Speed = NumberRange.new(1.5, 3.5);
		Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.24), NumberSequenceKeypoint.new(0.7, 0.16), NumberSequenceKeypoint.new(1, 0) });
		Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(1, 0.6) });
		Color = ColorSequence.new(Color3.fromRGB(255, 186, 92), Color3.fromRGB(200, 60, 24)); LightEmission = 1; Spread = 28;
		Accel = Vector3.new(0, 1.2, 0); Drag = 0.4; Up = true; Rotation = true;
	};
	Fog = {
		Texture = FOG; Rate = 1.5; Lifetime = NumberRange.new(6, 8); Speed = NumberRange.new(0.2, 0.5);
		Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 6), NumberSequenceKeypoint.new(1, 10) });
		Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.4, 0.82), NumberSequenceKeypoint.new(1, 1) });
		Color = ColorSequence.new(Color3.fromRGB(150, 150, 186)); LightEmission = 0; Spread = 180;
		Accel = Vector3.new(0, 0, 0); Drag = 0.2; Volume = true; NightOnly = true; HighOnly = true;
	};
}

-- Sound beds. Zone = a RoomId zone part's id (workspace.School.*.Zone); Indoor = under a roof but in no zone
-- (the halls); Outdoor = open sky. Day / Night ids are rbxassetid numbers; Volume is the bed's own level.
local OUT_DAY, OUT_NIGHT = 9112777914, 9112764573     -- evening breeze and light insects / crickets at night
local HALL_DAY, HALL_NIGHT = 9116260218, 9118747853    -- distant students and paper handling / a low interior wind
local BOILER = 9112839511                              -- machine hum, turbine whine
local EERIE = 9125602882                               -- faint eerie choral tones (the Archive after dark)
Ambience.Beds = {
	Outdoor = { Day = OUT_DAY; Night = OUT_NIGHT; Volume = 0.35 };
	Indoor = { Day = HALL_DAY; Night = HALL_NIGHT; Volume = 0.22 };
	Classroom = { Day = HALL_DAY; Night = HALL_NIGHT; Volume = 0.14 };
	Archive = { Day = HALL_NIGHT; Night = EERIE; Volume = 0.2 };
	BoilerYard = { Day = BOILER; Night = BOILER; Volume = 0.26 };
}
-- which bed each RoomId zone uses (anything else falls back to Indoor)
Ambience.ZoneBed = {
	R101 = `Classroom`; R102 = `Classroom`; R103 = `Classroom`; R104 = `Classroom`; R105 = `Classroom`; R106 = `Classroom`;
	Archive = `Archive`; RiteArchive = `Archive`; BoilerYard = `BoilerYard`;
}
-- the halls: standing over a floor part of one of these School models (up to IndoorHeight studs above it) is Indoor.
-- The greybox halls have no roofs; once they do, the roof check in Soundscape covers them as well.
Ambience.IndoorFloors = { Hallway = true; HallwayExtension = true }
Ambience.IndoorHeight = 14
Ambience.Crossfade = 2.5      -- seconds

---| ambience foundations (2.16.0, docs/Environment-Ambience-Concepts.md 1-3) |---

-- the places with a bed of their own, used when no RoomId zone part covers you (the Map has region boxes, not zones)
Ambience.RegionBed = {
	R101 = `Classroom`; R102 = `Classroom`; R103 = `Classroom`; R104 = `Classroom`; R105 = `Classroom`; R106 = `Classroom`;
	Archive = `Archive`; Library = `Archive`; BoilerYard = `BoilerYard`;
}
-- (any other place: the roof check decides Indoor or Outdoor, as before)

-- the mixer (Controllers.World.AmbienceMix)
Ambience.Mix = {
	DuckTo = 0.5;        -- all ambience while combat-tagged (about -6 dB)
	Attack = 0.1;        -- seconds to duck
	Release = 1.5;       -- seconds to come back
	CutsceneFade = 0.5;  -- seconds for the spot sounds and one-shots to leave (and return) in a cutscene
}

-- room reverb (SoundService.AmbientReverb, an Enum.ReverbType name) by the place you're in
Ambience.Reverb = {
	MainHall = `StoneCorridor`; EastWing = `StoneCorridor`;
	R101 = `Room`; R102 = `Room`; R103 = `Room`; R104 = `Room`; R105 = `Room`; R106 = `Room`;
	Archive = `LivingRoom`; Library = `LivingRoom`; StaffRoom = `Room`; RecordsOffice = `StoneRoom`; Ring = `StoneRoom`;
	Chapel = `ConcertHall`; InkStudio = `Room`; CrimsonParlor = `LivingRoom`; Den = `Room`; Dorms = `LivingRoom`;
	Cafeteria = `Auditorium`; Gymnasium = `Arena`; BoilerYard = `SewerPipe`;
	Commons = `Plain`; Pitch = `Plain`; Field = `Plain`; PracticeLanes = `Plain`; BackLot = `Alley`;
	WestEdge = `Forest`; Graveyard = `Forest`; Grounds = `Plain`;
}
-- a RoomId zone's own bed is more exact than the place around it (a classroom inside the Main Hall's box)
Ambience.ReverbByZone = { Classroom = `Room`; Archive = `LivingRoom`; BoilerYard = `SewerPipe` }
-- no place at all: by the soundscape's bed (under a roof or open sky)
Ambience.ReverbByBed = { Indoor = `StoneCorridor`; Outdoor = `Plain` }

-- our own sounds (tools/sfx/ambience.py; art/sfx/ambience). The owner uploads the two sheets; 0 = not uploaded yet
Ambience.Sheets = {
	OneShots = 0;   -- NH_Ambience_OneShots.ogg (a one-shot every 4 s)
	Loops = 0;      -- NH_Ambience_Loops.ogg (a loop every 10 s)
}
-- each clip's place on its sheet (seconds); generated by `python tools/sfx/ambience.py --luau`
Ambience.Clips = {
	locker_slam = { Sheet = `OneShots`; Start = 0.0; Length = 2.0 };
	book_drop = { Sheet = `OneShots`; Start = 4.0; Length = 1.6 };
	door_far = { Sheet = `OneShots`; Start = 8.0; Length = 2.6 };
	steps_far = { Sheet = `OneShots`; Start = 12.0; Length = 3.2 };
	stone_tick = { Sheet = `OneShots`; Start = 16.0; Length = 1.2 };
	pipe_knock = { Sheet = `OneShots`; Start = 20.0; Length = 2.4 };
	wood_creak = { Sheet = `OneShots`; Start = 24.0; Length = 2.4 };
	keys_far = { Sheet = `OneShots`; Start = 28.0; Length = 2.8 };
	draught = { Sheet = `OneShots`; Start = 32.0; Length = 3.6 };
	chalk_tap = { Sheet = `OneShots`; Start = 36.0; Length = 1.8 };
	page_turn = { Sheet = `OneShots`; Start = 40.0; Length = 1.4 };
	chair_creak = { Sheet = `OneShots`; Start = 44.0; Length = 1.4 };
	desk_tap = { Sheet = `OneShots`; Start = 48.0; Length = 1.2 };
	bird_a = { Sheet = `OneShots`; Start = 52.0; Length = 2.2 };
	bird_b = { Sheet = `OneShots`; Start = 56.0; Length = 2.4 };
	town_bell = { Sheet = `OneShots`; Start = 60.0; Length = 3.75 };
	owl = { Sheet = `OneShots`; Start = 64.0; Length = 2.8 };
	crow = { Sheet = `OneShots`; Start = 68.0; Length = 2.4 };
	dog_far = { Sheet = `OneShots`; Start = 72.0; Length = 3.0 };
	gutter_drip = { Sheet = `OneShots`; Start = 76.0; Length = 2.4 };
	wind_gust = { Sheet = `OneShots`; Start = 80.0; Length = 3.75 };
	paper_rustle = { Sheet = `OneShots`; Start = 84.0; Length = 1.8 };
	book_thump = { Sheet = `OneShots`; Start = 88.0; Length = 2.0 };
	valve_hiss = { Sheet = `OneShots`; Start = 92.0; Length = 2.6 };
	furnace_clank = { Sheet = `OneShots`; Start = 96.0; Length = 2.6 };
	clock_tick = { Sheet = `Loops`; Start = 0.0; Length = 8.0; Loop = true };
	radiator_hum = { Sheet = `Loops`; Start = 10.0; Length = 8.0; Loop = true };
	vending_hum = { Sheet = `Loops`; Start = 20.0; Length = 8.0; Loop = true };
	candle_crackle = { Sheet = `Loops`; Start = 30.0; Length = 8.0; Loop = true };
	tap_drip = { Sheet = `Loops`; Start = 40.0; Length = 8.0; Loop = true };
	tube_buzz = { Sheet = `Loops`; Start = 50.0; Length = 8.0; Loop = true };
	fire_crackle = { Sheet = `Loops`; Start = 60.0; Length = 8.0; Loop = true };
}

-- spot sounds: a part tagged NHAmbientSound:<Kind> plays that loop in 3D (Controllers.World.AmbientSounds)
Ambience.Spots = {
	Clock = { Clip = `clock_tick`; Volume = 0.35; Min = 3; Range = 28 };
	Radiator = { Clip = `radiator_hum`; Volume = 0.25; Min = 3; Range = 24 };
	Vending = { Clip = `vending_hum`; Volume = 0.3; Min = 4; Range = 30 };
	Candles = { Clip = `candle_crackle`; Volume = 0.3; Min = 2; Range = 18 };
	Tap = { Clip = `tap_drip`; Volume = 0.35; Min = 3; Range = 24 };
	Tube = { Clip = `tube_buzz`; Volume = 0.18; Min = 3; Range = 22 };
	Fire = { Clip = `fire_crackle`; Volume = 0.45; Min = 4; Range = 40 };
}
Ambience.SpotMax = 6           -- spot sounds playing at once (the nearest)

-- one-shots: by the soundscape's bed and the time. Band = how far away (Ambience.Bands)
Ambience.OneShots = {
	Indoor = {
		Day = {
			{ Clip = `locker_slam`; Band = `Medium`; Volume = 0.35 }; { Clip = `book_drop`; Band = `Medium`; Volume = 0.35 };
			{ Clip = `door_far`; Band = `Far`; Volume = 0.3 }; { Clip = `steps_far`; Band = `Far`; Volume = 0.3 };
			{ Clip = `page_turn`; Band = `Close`; Volume = 0.2 };
		};
		Night = {
			{ Clip = `stone_tick`; Band = `Medium`; Volume = 0.3 }; { Clip = `pipe_knock`; Band = `Far`; Volume = 0.3 };
			{ Clip = `wood_creak`; Band = `Medium`; Volume = 0.3 }; { Clip = `keys_far`; Band = `Far`; Volume = 0.28 };
			{ Clip = `draught`; Band = `Sky`; Volume = 0.25 }; { Clip = `door_far`; Band = `Far`; Volume = 0.22 };
		};
	};
	Classroom = {
		Day = {
			{ Clip = `chalk_tap`; Band = `Close`; Volume = 0.3 }; { Clip = `page_turn`; Band = `Close`; Volume = 0.25 };
			{ Clip = `chair_creak`; Band = `Close`; Volume = 0.25 }; { Clip = `desk_tap`; Band = `Close`; Volume = 0.25 };
			{ Clip = `steps_far`; Band = `Far`; Volume = 0.18 };
		};
		Night = {
			{ Clip = `wood_creak`; Band = `Close`; Volume = 0.22 }; { Clip = `stone_tick`; Band = `Medium`; Volume = 0.22 };
			{ Clip = `desk_tap`; Band = `Medium`; Volume = 0.12 }; { Clip = `draught`; Band = `Sky`; Volume = 0.2 };
		};
	};
	Outdoor = {
		Day = {
			{ Clip = `bird_a`; Band = `Medium`; Volume = 0.3 }; { Clip = `bird_b`; Band = `Medium`; Volume = 0.3 };
			{ Clip = `crow`; Band = `Far`; Volume = 0.25 }; { Clip = `wind_gust`; Band = `Sky`; Volume = 0.3 };
			{ Clip = `town_bell`; Band = `Sky`; Volume = 0.18 };
		};
		Night = {
			{ Clip = `owl`; Band = `Far`; Volume = 0.3 }; { Clip = `dog_far`; Band = `Sky`; Volume = 0.2 };
			{ Clip = `crow`; Band = `Far`; Volume = 0.18 }; { Clip = `wind_gust`; Band = `Sky`; Volume = 0.3 };
			{ Clip = `gutter_drip`; Band = `Medium`; Volume = 0.25 };
		};
	};
	Archive = {
		Day = {
			{ Clip = `paper_rustle`; Band = `Medium`; Volume = 0.25 }; { Clip = `page_turn`; Band = `Close`; Volume = 0.2 };
			{ Clip = `book_thump`; Band = `Far`; Volume = 0.22 };
		};
		Night = {
			{ Clip = `paper_rustle`; Band = `Medium`; Volume = 0.25 }; { Clip = `book_thump`; Band = `Medium`; Volume = 0.25 };
			{ Clip = `wood_creak`; Band = `Medium`; Volume = 0.22 }; { Clip = `stone_tick`; Band = `Far`; Volume = 0.2 };
		};
	};
	BoilerYard = {
		Day = {
			{ Clip = `valve_hiss`; Band = `Medium`; Volume = 0.35 }; { Clip = `pipe_knock`; Band = `Medium`; Volume = 0.35 };
			{ Clip = `furnace_clank`; Band = `Medium`; Volume = 0.3 };
		};
	};
}
Ambience.OneShots.BoilerYard.Night = Ambience.OneShots.BoilerYard.Day
-- distance bands: Close and Medium play in 3D Min-Max studs from you; Far and Sky play flat (already mixed far)
Ambience.Bands = {
	Close = { Min = 6; Max = 16 };
	Medium = { Min = 18; Max = 40 };
	Far = { Flat = true; Gain = 0.8 };
	Sky = { Flat = true; Gain = 0.7 };
}
Ambience.OneShotGap = { 6, 20 }  -- seconds between one-shots (random)
Ambience.OneShotMax = 4          -- playing at once
Ambience.NoRepeat = 3            -- never one of the last 3 again

return Ambience
