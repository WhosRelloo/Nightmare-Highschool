--[[
	Racial grips (2.2.0): the N-key race finisher on a downed body. Shared by the server (Misc.RaceAction,
	Features.Downed, Features.RaceAction) and the client (World.RaceGripFx).

	Every Kind is a paired animation authored on two R6 rigs in one space (tools/racial-grips): the victim is
	welded to the gripper's HumanoidRootPart at `Offset` for the whole clip, so hands stay on the body.
	Ids marked PENDING are filled in when the owner publishes the group-owned clips and uploads the art and audio;
	until then Studio registers ServerStorage.NH_GripAnims.<Clip> as a temporary preview id,
	and live servers fall back to the old clip with no victim animation.
]]

local function deg(y) return CFrame.Angles(0, math.rad(y), 0) end

return {
	-- race -> Kind. Sub-races share their base race's grip and get a richer effect (see Rich / Signature).
	-- live servers with an unpublished clip keep the old behaviour (no victim clip, no weld)
	Fallback = {
		BloodDrain = `rbxassetid://134503729182597`; EatBody = `rbxassetid://79651374323565`;
		Maul = `rbxassetid://79651374323565`; SoulSiphon = `rbxassetid://105788745618289`;
		Exorcise = `rbxassetid://105788745618289`; Stake = `rbxassetid://105788745618289`;
	};

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
			Gripper = `rbxassetid://0`; Victim = `rbxassetid://0`; -- PENDING owner publish (GripVampire / GripVampireVictim)
			Length = 3.0;
			Offset = CFrame.new(0, 0, -2.8);
			Beats = { Grab = 0.4; Bite = 0.95; Drink = { 1.2, 1.6, 2.0 }; Release = 2.3; Finish = 2.6 };
			Color = Color3.fromRGB(244, 214, 222); -- pale rose-white life thread (never red: no blood)
			Accent = Color3.fromRGB(200, 40, 60);  -- the vampire's eyes / rim only
		};
		EatBody = { -- Ghoul: owner's Eat Body clip + a new victim
			VictimClip = `GripGhoulVictim`; -- ServerStorage.NH_GripAnims (Studio preview until published)
			Name = `Eat Body`;
			Gripper = `rbxassetid://79651374323565`; Victim = `rbxassetid://0`; -- victim PENDING (GripGhoulVictim)
			Length = 3.5;
			Offset = CFrame.new(0, 0, -1.95) * deg(90);
			Beats = { Crack = 0.15; Cage = 0.3; Feed = { 0.45, 0.85, 1.45, 1.85, 2.45 }; Crumble = 3.3; Finish = 3.3 };
			Color = Color3.fromRGB(143, 191, 106);  -- sickly grave green
			Accent = Color3.fromRGB(228, 222, 208); -- bone
		};
		Maul = { -- Werewolf
			Clip = `GripWerewolf`; VictimClip = `GripWerewolfVictim`; -- ServerStorage.NH_GripAnims (Studio preview until published)
			Name = `Maul`;
			Gripper = `rbxassetid://0`; Victim = `rbxassetid://0`; -- PENDING (GripWerewolf / GripWerewolfVictim)
			Length = 2.8;
			Offset = CFrame.new(0, 0, -2.6) * deg(90);
			Beats = { Snarl = 0.1; Pounce = 0.42; Swipe = { 0.65, 0.95, 1.25 }; Haul = 1.6; Howl = 2.12; Finish = 2.12 };
			Color = Color3.fromRGB(221, 227, 238);  -- silver claw streaks
			Accent = Color3.fromRGB(255, 176, 60);  -- amber eyes
		};
		SoulSiphon = { -- Wraith
			Clip = `GripWraith`; VictimClip = `GripWraithVictim`; -- ServerStorage.NH_GripAnims (Studio preview until published)
			Name = `Soul Siphon`;
			Gripper = `rbxassetid://0`; Victim = `rbxassetid://0`; -- PENDING (GripWraith / GripWraithVictim)
			Length = 3.0;
			Offset = CFrame.new(0, 0, -2.5) * deg(90);
			Beats = { Frost = 0.0; Palm = 0.6; Pull = 0.72; Yank = 2.25; Absorb = 2.5; Finish = 2.85 };
			Color = Color3.fromRGB(170, 216, 255);
			Accent = Color3.fromRGB(191, 230, 255);
		};
		Exorcise = { -- Priest (only the unholy can be exorcised)
			Clip = `GripPriest`; VictimClip = `GripPriestVictim`; -- ServerStorage.NH_GripAnims (Studio preview until published)
			Name = `Exorcism`;
			Gripper = `rbxassetid://0`; Victim = `rbxassetid://0`; -- PENDING (GripPriest / GripPriestVictim)
			Length = 3.2;
			Offset = CFrame.new(0, 0, -2.5) * deg(-90);
			Beats = { Seal = 0.48; Cross = 0.85; Spasm = { 1.1, 1.6, 2.0 }; Strike = 2.45; Finish = 2.45 };
			Color = Color3.fromRGB(235, 205, 120);  -- candle gold
			Accent = Color3.fromRGB(12, 10, 16);    -- ink darkness
			UnholyOnly = true;
		};
		Stake = { -- Human: Hunter's Stake (works on any body; ash only on monsters)
			Clip = `GripHuman`; VictimClip = `GripHumanVictim`; -- ServerStorage.NH_GripAnims (Studio preview until published)
			Name = `Hunter's Stake`;
			Gripper = `rbxassetid://0`; Victim = `rbxassetid://0`; -- PENDING (GripHuman / GripHumanVictim)
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

	-- custom audio (art/sfx/racial-grips, tools/sfx/racial_grips.py): PENDING owner upload
	Sounds = {
		BloodDrain = `rbxassetid://0`; EatBody = `rbxassetid://0`; Maul = `rbxassetid://0`; SoulSiphon = `rbxassetid://0`;
		Exorcise = `rbxassetid://0`; Stake = `rbxassetid://0`; StakeAsh = `rbxassetid://0`;
		VictimHeartbeat = `rbxassetid://0`; FinishSting = `rbxassetid://0`;
		BatsGold = `rbxassetid://0`; DoubleShock = `rbxassetid://0`; CageTall = `rbxassetid://0`;
		FrostCrown = `rbxassetid://0`; TwinBell = `rbxassetid://0`; Crater = `rbxassetid://0`;
	};

	-- custom textures (art/vfx/grips, make_grip_sprites.py): PENDING owner upload; nil/0 falls back to the nh_* set
	Textures = {
		PriestRunes = `rbxassetid://0`; LifeThread = `rbxassetid://0`; InkSmoke = `rbxassetid://0`; InkTendril = `rbxassetid://0`;
		ClawSlash = `rbxassetid://0`; SlashSpark = `rbxassetid://0`; FrostFloor = `rbxassetid://0`; GraveCracks = `rbxassetid://0`;
		GraveCracksGlow = `rbxassetid://0`; Ash = `rbxassetid://0`; GoldDust = `rbxassetid://0`; SoulStreak = `rbxassetid://0`;
		Shockwave = `rbxassetid://0`; MoonHalo = `rbxassetid://0`; DemonShape = `rbxassetid://0`;
		-- already in the game (tier-up set)
		Sigil = { Vampire = `rbxassetid://71155214984713`; Werewolf = `rbxassetid://99971445815793`; Ghoul = `rbxassetid://79334903644638`;
			Wraith = `rbxassetid://98004675393234`; Human = `rbxassetid://85671257624535`; Priest = `rbxassetid://101056836189271` };
		Bats = `rbxassetid://92253632642153`; Feather = `rbxassetid://129780603815518`; Claws = `rbxassetid://121739065632043`;
		Streak = `rbxassetid://85345386625602`; Spore = `rbxassetid://74644103733948`; Frost = `rbxassetid://92233090974100`;
		Godray = `rbxassetid://77357987513961`;
	};
}
