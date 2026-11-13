--[[
	Racial grips (2.2.0): the N-key race finisher on a downed body. Shared by the server (Misc.RaceAction,
	Features.Downed, Features.RaceAction) and the client (World.RaceGripFx).

	Every Kind is a paired animation authored on two R6 rigs in one space (tools/racial-grips): the victim is
	welded to the gripper's HumanoidRootPart at `Offset` for the whole clip, so hands stay on the body.
	All clips, sounds and textures are published under the group (2.7.2). A Kind whose id is ever reset to 0 falls
	back: Studio registers ServerStorage.NH_GripAnims.<Clip> as a temporary preview id, and live servers play the
	old clip with no victim animation.
]]

local function deg(y) return CFrame.Angles(0, math.rad(y), 0) end

return {
	-- live servers with an unpublished clip keep the old behaviour (no victim clip, no weld)
	Fallback = {
		BloodDrain = `rbxassetid://134503729182597`; EatBody = `rbxassetid://79651374323565`;
		Maul = `rbxassetid://79651374323565`; SoulSiphon = `rbxassetid://105788745618289`;
		Exorcise = `rbxassetid://105788745618289`; Stake = `rbxassetid://105788745618289`;
	};

	-- race -> Kind. Sub-races share their base race's grip and get a richer effect (see Rich / Signature).
	ByRace = {
		Vampire = `BloodDrain`;
		Ghoul = `EatBody`;
		Werewolf = `Maul`;
		Wraith = `SoulSiphon`;
		Priest = `Exorcise`;
		Human = `Stake`;
	};

	Kinds = {
		BloodDrain = { -- Vampire: The Kiss
			Clip = `GripVampire`; VictimClip = `GripVampireVictim`; -- ServerStorage.NH_GripAnims (Studio preview until published)
			Name = `The Kiss`;
			Gripper = `rbxassetid://107993999401669`; Victim = `rbxassetid://96341425239551`; -- GripVampire / GripVampireVictim
			Length = 3.0;
			Offset = CFrame.new(0, 0, -2.8);
			Beats = { Grab = 0.4; Bite = 0.95; Drink = { 1.2, 1.6, 2.0 }; Release = 2.3; Finish = 2.6 };
			Color = Color3.fromRGB(244, 214, 222); -- pale rose-white life thread (never red: no blood)
			Accent = Color3.fromRGB(200, 40, 60);  -- the vampire's eyes / rim only
		};
		EatBody = { -- Ghoul: owner's Eat Body clip + a new victim
			VictimClip = `GripGhoulVictim`; -- ServerStorage.NH_GripAnims (Studio preview until published)
			Name = `Eat Body`;
			Gripper = `rbxassetid://79651374323565`; Victim = `rbxassetid://80149989440354`; -- owner's Eat Body / GripGhoulVictim
			Length = 3.5;
			Offset = CFrame.new(0, 0, -1.95) * deg(90);
			Beats = { Crack = 0.15; Cage = 0.3; Feed = { 0.45, 0.85, 1.45, 1.85, 2.45 }; Crumble = 3.3; Finish = 3.3 };
			Color = Color3.fromRGB(143, 191, 106);  -- sickly grave green
			Accent = Color3.fromRGB(228, 222, 208); -- bone
		};
		Maul = { -- Werewolf
			Clip = `GripWerewolf`; VictimClip = `GripWerewolfVictim`;
			Name = `Maul`;
			Gripper = `rbxassetid://101763781821025`; Victim = `rbxassetid://129908973676695`; -- GripWerewolf / GripWerewolfVictim
			Length = 2.8;
			Offset = CFrame.new(0, 0, -2.6) * deg(90);
			Beats = { Snarl = 0.1; Pounce = 0.42; Swipe = { 0.65, 0.95, 1.25 }; Haul = 1.6; Howl = 2.12; Finish = 2.12 };
			Color = Color3.fromRGB(221, 227, 238);  -- silver claw streaks
			Accent = Color3.fromRGB(255, 176, 60);  -- amber eyes
		};
		SoulSiphon = { -- Wraith
			Clip = `GripWraith`; VictimClip = `GripWraithVictim`;
			Name = `Soul Siphon`;
			Gripper = `rbxassetid://114451912505513`; Victim = `rbxassetid://128597223296512`; -- GripWraith / GripWraithVictim
			Length = 3.0;
			Offset = CFrame.new(0, 0, -2.5) * deg(90);
			Beats = { Frost = 0.0; Palm = 0.6; Pull = 0.72; Yank = 2.25; Absorb = 2.5; Finish = 2.85 };
			Color = Color3.fromRGB(170, 216, 255);
			Accent = Color3.fromRGB(191, 230, 255);
		};
		Exorcise = { -- Priest (only the unholy can be exorcised)
			Clip = `GripPriest`; VictimClip = `GripPriestVictim`;
			Name = `Exorcism`;
			Gripper = `rbxassetid://94746575484403`; Victim = `rbxassetid://70954827262888`; -- GripPriest / GripPriestVictim
			Length = 3.2;
			Offset = CFrame.new(0, 0, -2.5) * deg(-90);
			Beats = { Seal = 0.48; Cross = 0.85; Spasm = { 1.1, 1.6, 2.0 }; Strike = 2.45; Finish = 2.45 };
			Color = Color3.fromRGB(235, 205, 120);  -- candle gold
			Accent = Color3.fromRGB(12, 10, 16);    -- ink darkness
			UnholyOnly = true;
		};
		Stake = { -- Human: Hunter's Stake (works on any body; ash only on monsters)
			Clip = `GripHuman`; VictimClip = `GripHumanVictim`;
			Name = `Hunter's Stake`;
			Gripper = `rbxassetid://117208142968598`; Victim = `rbxassetid://104763113655375`; -- GripHuman / GripHumanVictim
			Length = 2.6;
			Offset = CFrame.new(0, 0, -2.6) * deg(-90);
			Beats = { Knee = 0.3; Stake = 0.65; Raise = 1.82; Strike = 2.03; Finish = 2.03 };
			Color = Color3.fromRGB(221, 227, 238);  -- silver
			Accent = Color3.fromRGB(189, 184, 176); -- ash
		};
	};

	-- sub-races (Lineage ids) that get the richer effect; Signature = one extra piece for the top sub-races
	Rich = { Superhuman = true; GrandPriest = true; Pope = true; Nobleblood = true; RoyalVamp = true; Bloodmoon = true;
		Alpha = true; Ghast = true; CryptLord = true; Revenant = true; HollowKing = true };
	Signature = { RoyalVamp = `BatsGold`; Alpha = `DoubleShock`; CryptLord = `CageTall`; HollowKing = `FrostCrown`;
		Pope = `TwinBell`; Superhuman = `Crater` };

	-- custom audio (art/sfx/racial-grips, tools/sfx/racial_grips.py), group-owned
	Sounds = {
		BloodDrain = `rbxassetid://92545877023277`; EatBody = `rbxassetid://139460448791952`; Maul = `rbxassetid://112333092197218`;
		SoulSiphon = `rbxassetid://101530309925673`; Exorcise = `rbxassetid://75649149262886`; Stake = `rbxassetid://91932527605382`;
		StakeAsh = `rbxassetid://107556183805738`; VictimHeartbeat = `rbxassetid://79516731726335`; FinishSting = `rbxassetid://119363628587727`;
		BatsGold = `rbxassetid://87229649256353`; DoubleShock = `rbxassetid://82317334742868`; CageTall = `rbxassetid://97274368071371`;
		FrostCrown = `rbxassetid://135414858958756`; TwinBell = `rbxassetid://93188011504186`; Crater = `rbxassetid://98827068197944`;
	};

	-- custom textures (art/vfx/grips, make_grip_sprites.py), group-owned images; nil/0 falls back to the nh_* set
	Textures = {
		PriestRunes = `rbxassetid://86427592875730`; LifeThread = `rbxassetid://70663916409231`; InkSmoke = `rbxassetid://139241818344451`;
		InkTendril = `rbxassetid://121797275986676`; ClawSlash = `rbxassetid://116233543043659`; SlashSpark = `rbxassetid://139901521330113`;
		FrostFloor = `rbxassetid://86595479558163`; GraveCracks = `rbxassetid://108464434825289`; GraveCracksGlow = `rbxassetid://84993410533465`;
		Ash = `rbxassetid://83866785490014`; GoldDust = `rbxassetid://72044397615736`; SoulStreak = `rbxassetid://111839402872682`;
		Shockwave = `rbxassetid://78985335218670`; MoonHalo = `rbxassetid://93403285018268`; DemonShape = `rbxassetid://115902601611879`;
		-- already in the game (tier-up set)
		Sigil = { Vampire = `rbxassetid://71155214984713`; Werewolf = `rbxassetid://99971445815793`; Ghoul = `rbxassetid://79334903644638`;
			Wraith = `rbxassetid://98004675393234`; Human = `rbxassetid://85671257624535`; Priest = `rbxassetid://101056836189271` };
		Bats = `rbxassetid://92253632642153`; Feather = `rbxassetid://129780603815518`; Claws = `rbxassetid://121739065632043`;
		Streak = `rbxassetid://85345386625602`; Spore = `rbxassetid://74644103733948`; Frost = `rbxassetid://92233090974100`;
		Godray = `rbxassetid://77357987513961`;
	};
}
