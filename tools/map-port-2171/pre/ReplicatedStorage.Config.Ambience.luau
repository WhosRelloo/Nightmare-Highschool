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

return Ambience
