--[[
	Anatomy (shared): the bench elective. Species are data; the engine (ServerStorage.Activities.AnatomyBench)
	walks Steps in order, then the Lift step until every non-Flag organ is placed on its Slot.
	Tools are on the roll in hotkey order. Seam: the plate seam as an ellipse in plate space (unit = plate radius).
]]
local Anatomy = {}

Anatomy.Tools = { `Key`, `Driver`, `Loupe`, `Scalpel`, `Tweezers` }
-- The bench's PBR chrome (art/ui/hud/out/anatomy, made by art/ui/hud/make_anatomy_ui.py): group image ids, 0 until the
-- owner imports them. A panel with an id draws the image; one at 0 keeps the plain iron panel.
Anatomy.UI = { Plate = 0; Procedure = 0; Specimen = 0; Seal = 0; Hold = 0; Tag = 0 }
Anatomy.Weights = { Accuracy = 0.6; Process = 0.25; Time = 0.15 }
Anatomy.SlipCost = 0.08        -- accuracy lost per slip (x2 under Crane's Inspection)
Anatomy.WrongToolCost = 0.15   -- process lost per use with the wrong tool or out of order
Anatomy.RecoilSeconds = 0.8    -- input ignored after a slip
Anatomy.TraceTolerance = 0.08  -- how far off the seam a trace point may be (fraction of the radius)
Anatomy.TraceCoverage = 0.9    -- share of the seam's angle a trace must sweep
Anatomy.UseInterval = 0.12     -- min seconds between counted Key/Driver turns

Anatomy.Species = {
	Frog = {
		Id = `Frog`; Name = `Clockwork Frog`; Latin = `Rana Horologica`; Level = 1; TimeLimit = 120; Par = 60; Plate = 99000128465951;
		FlagFrom = 4; Seam = { Rx = 1; Ry = 1.3 };
		Steps = {
			{ Id = `Unwind`; Tool = `Key`; Target = `SideKey`; Count = 8 };
			{ Id = `Trace`; Tool = `Scalpel`; Target = `Seam` };
			{ Id = `Pry`; Tool = `Driver`; Target = `Plate` };
			{ Id = `Lift`; Tool = `Tweezers`; Target = `Organ` };
		};
		Organs = {
			{ Id = `HeartPump`; Name = `Heart-pump`; Slot = `Heart` };
			{ Id = `Lungs`; Name = `Bellows lungs`; Slot = `Lungs` };
			{ Id = `GearGut`; Name = `Gear-gut`; Slot = `Gut` };
			{ Id = `FlagCog`; Name = `Loose cog`; Slot = `Flag`; Flag = true };
		};
	};
	Raven = {
		Id = `Raven`; Name = `Clockwork Raven`; Latin = `Corvus Mechanicus`; Level = 3; TimeLimit = 150; Par = 80; Plate = 124681137363813;
		FlagFrom = 4; Seam = { Rx = 1; Ry = 1.6 };
		Steps = {
			{ Id = `Unwind`; Tool = `Key`; Target = `SideKey`; Count = 8 };
			{ Id = `Unscrew`; Tool = `Driver`; Target = `WingPlate`; Count = 4 };
			{ Id = `Trace`; Tool = `Scalpel`; Target = `Seam` };
			{ Id = `Pry`; Tool = `Driver`; Target = `Plate` };
			{ Id = `Lift`; Tool = `Tweezers`; Target = `Organ` };
		};
		Organs = {
			{ Id = `HeartPump`; Name = `Heart-pump`; Slot = `Heart` };
			{ Id = `Lungs`; Name = `Bellows lungs`; Slot = `Lungs` };
			{ Id = `VoiceBox`; Name = `Voice-box`; Slot = `Voice` };
			{ Id = `WingSpring`; Name = `Wing spring`; Slot = `Wing` };
			{ Id = `FlagCog`; Name = `Loose cog`; Slot = `Flag`; Flag = true };
		};
	};
	Wyvern = {
		Id = `Wyvern`; Name = `Clockwork Wyvern`; Latin = `Draco Horologicus`; Level = 5; TimeLimit = 180; Par = 100; Plate = 100444371073403;
		FlagFrom = 4; Seam = { Rx = 1; Ry = 1.8 };
		Steps = {
			{ Id = `Unwind`; Tool = `Key`; Target = `SideKey`; Count = 12 };
			{ Id = `Inspect`; Tool = `Loupe`; Target = `HiddenSeam` };
			{ Id = `Trace`; Tool = `Scalpel`; Target = `Seam` };
			{ Id = `Pry`; Tool = `Driver`; Target = `Plate` };
			{ Id = `Lift`; Tool = `Tweezers`; Target = `Organ` };
		};
		Organs = {
			{ Id = `FireGland`; Name = `Fire-gland`; Slot = `Fire`; First = true };
			{ Id = `HeartA`; Name = `Fore heart`; Slot = `HeartA` };
			{ Id = `HeartB`; Name = `Aft heart`; Slot = `HeartB` };
			{ Id = `Lungs`; Name = `Bellows lungs`; Slot = `Lungs` };
			{ Id = `GearGut`; Name = `Gear-gut`; Slot = `Gut` };
			{ Id = `FlagCog`; Name = `Loose cog`; Slot = `Flag`; Flag = true };
		};
	};
}

function Anatomy.SpeciesFor(Level: number, Override: string?)
	if Override and Anatomy.Species[Override] then return Anatomy.Species[Override] end
	local Best = Anatomy.Species.Frog
	for _, S in Anatomy.Species do
		if S.Level <= Level and S.Level > Best.Level then Best = S end
	end
	return Best
end

-- Healer perk (Task 12). HealMult scales what a heal restores; ReviveMult scales how long a revive takes.
-- No game system reads them yet: there is no item heal and no player-to-player revive (see tools/electives/REPORT.md).
function Anatomy.HealMult(Level: number): number return 1 + 0.10 * (math.clamp(Level, 1, 5) - 1) end
function Anatomy.ReviveMult(Level: number): number return 1 - 0.08 * (math.clamp(Level, 1, 5) - 1) end

-- Mastery: every species at A or better grants the title and the accessory once.
Anatomy.Mastery = { Species = { `Frog`, `Raven`, `Wyvern` }; MinGrade = `A`; Title = `Anatomist`; Accessory = `anatomy-loupe-monocle` }

return Anatomy
