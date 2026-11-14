--[[
	Beasts (shared config). ReplicatedStorage.Config.Beasts      (design: docs/superpowers/specs/2026-11-05-beasts-design.md)
	One entry per beast, run by Services.Features.Beasts. The wolves (Features.WildWolves) are separate and untouched.

	Each beast:
	  Model        the template's name in ServerStorage.NHBeasts (an Animations folder inside it holds its clips)
	  Health, WalkSpeed, RunSpeed, Sight (studs it spots a student from), Leash (studs from home before it gives up)
	  Roam         how far from its lair it wanders at night
	  Sighted      a clip it plays once when it first spots you (a fair warning before the fight)
	  StunGuard    seconds after a stun wears off when hits can't stun it again or call off its attack (no stun-lock)
	  Spawn        Max at once, Respawn (s), Lair (the Beast attribute on NHBeastLair parts), Fallback (a School part
	               when no lair is tagged yet)
	  Reward       Exp (Combat), Yen, Trophy { Id (Config.Items), Chance }
	  Pattern      the fixed, learnable order it attacks in (move names), looping
	  Moves        what each move does:
	    Melee  Clip, Range (from the mouth), Damage, WindUp (s standing still first), HitAt (s into the clip), Rest
	    Breath Clip, Tell (the Kanji, s), Range, Angle (cone half-angle, degrees), Duration, Tick, Damage per tick, Rest
	    Leap   Clip, Tell, Min, Max (studs it leaps from), Damage, Recover (it stands panting: your opening), Rest;
	           optional Arc (studs it bounds up; negative swoops down), Dur (s in the air), Through (studs it carries on past you)
	    Screech Clip, Tell, ScreechAt (s into the clip), Range, Angle (cone half-angle), Damage, Stun (s), Rest
	    Hop    Clip (it springs back), Rest
	    Grab   Clip, Tell, LungeAt, Lunge (studs), Range, Hold (s), Damage, Rest, Miss (the opening after a miss)
	    Spit   Clip, Tell, SpitAt (s into the clip), Range, Speed (studs/s), Radius, Damage, Slow (s of the Slow state), Rest
	  Freeze       (optional) it can't move while a student looks at it: Angle (degrees off the centre of their view),
	               Range (studs); needs a clear line of sight (Controllers.World.BeastGaze reports where students look)
	  Ambush       (optional) it waits buried: Range (a student this near wakes it), Clip, Tell, Rise, Depth, Damage, Radius
	               (the burst hits anyone this close), Rest, Reburrow (s before it digs back in once alone)
	               From = `Above`: it hangs Height studs up on a silk thread instead (lower under a ceiling) and drops;
	               it plays its Hang clip while it waits
	  Special = true: the move gets the Kanji warning (StateController.Indicators.BeastTell). Normal attacks get none
	  (owner, 2026-11-05). Every special is followed by an opening (Rest / Recover) so the fight can be won.
]]
local Beasts = {}

Beasts.Night = { From = 19.5; To = 5.5 } -- the same hours as the wolves
Beasts.TurnStale = 3 -- an attacker that stops making progress gives up its turn (no deadlocks)

Beasts.Defs = {
	Hellhound = {
		Name = `Hellhound`; Model = `Hellhound`;
		Health = 180; WalkSpeed = 9; RunSpeed = 21; Sight = 60; Leash = 110; Roam = 12; -- Roam 12: it stays in the boiler yard
		Sighted = `Howl`;
		StunGuard = 2; -- s after a stun when hits can't stun it or call off its attack (no stun-lock); a posture break still does
		Spawn = { Max = 1; Respawn = 240; Lair = `Hellhound`; Fallback = `BoilerYard` };
		Reward = { Exp = 160; Yen = 60; Trophy = { Id = `EmberTooth`; Chance = 0.15 } };
		Pattern = { `Bite`, `Bite2`, `FireBreath`, `Bite`, `Hop`, `Pounce` };
		Moves = {
			Bite = { Kind = `Melee`; Clip = `Attack1`; Range = 5.5; Damage = 8; WindUp = 0.4; HitAt = 0.3; Rest = 0.7 };
			Bite2 = { Kind = `Melee`; Clip = `Attack2`; Range = 6; Damage = 10; WindUp = 0.4; HitAt = 0.32; Rest = 0.9 };
			FireBreath = { Kind = `Breath`; Clip = `Attack2`; Special = true; Tell = 0.9; Range = 15; Angle = 24; Duration = 1.4;
				Tick = 0.2; Damage = 3; Rest = 1.8 };
			Hop = { Kind = `Hop`; Clip = `JumpBack`; Rest = 1.0 };
			Pounce = { Kind = `Leap`; Clip = `Pounce`; Special = true; Tell = 0.95; Min = 12; Max = 22; Damage = 14; Recover = 1.8;
				Rest = 2.4 };
		};
	};
}

-- the Grave Ghoul (1.57): waits buried in its grave and bursts out at you (Ambush / Emerge), rakes with its claws, and
-- lunges to grab you (a special: the Kanji first; a friend's hit breaks the hold; a miss leaves it stumbling)
Beasts.Defs.GraveGhoul = {
	Name = `Grave Ghoul`; Model = `GraveGhoul`;
	Health = 110; WalkSpeed = 10; RunSpeed = 19; Sight = 45; Leash = 90; Roam = 10;
	StunGuard = 1.5;
	Ambush = { Range = 16; Clip = `Emerge`; Tell = 1.0; Rise = 0.6; Depth = 6.5; Damage = 8; Radius = 6; Rest = 0.8; Reburrow = 14 };
	Spawn = { Max = 2; Respawn = 180; Lair = `GraveGhoul` };
	Reward = { Exp = 90; Yen = 35; Trophy = { Id = `GraveLocket`; Chance = 0.15 } };
	Pattern = { `Swipe`, `Swipe2`, `Swipe`, `Grab` };
	Moves = {
		Swipe = { Kind = `Melee`; Clip = `Attack1`; Range = 4.5; Damage = 7; WindUp = 0.3; HitAt = 0.4; Rest = 0.6 };
		Swipe2 = { Kind = `Melee`; Clip = `Attack2`; Range = 5; Damage = 9; WindUp = 0.35; HitAt = 0.44; Rest = 0.8 };
		Grab = { Kind = `Grab`; Clip = `Grab`; Special = true; Tell = 0.9; LungeAt = 0.33; Lunge = 5; Range = 3.5; Hold = 1.0;
			Damage = 14; Rest = 1.4; Miss = 2.4 };
	};
}

-- the Night Stalker (1.59): tall and slow, and it can't move while anyone is looking at it (Freeze): turn your back and
-- it closes in. Two long swipes, then Reach (a special: the Kanji first), a spear of an arm from far off, then an opening.
Beasts.Defs.NightStalker = {
	Name = `Night Stalker`; Model = `NightStalker`;
	Health = 130; WalkSpeed = 9; RunSpeed = 20; Sight = 60; Leash = 100; Roam = 14;
	StunGuard = 1.8;
	Freeze = { Angle = 32; Range = 70 }; -- frozen while it's within this many degrees of a student's view, in clear sight
	Spawn = { Max = 1; Respawn = 240; Lair = `NightStalker` };
	Reward = { Exp = 120; Yen = 45; Trophy = { Id = `StalkerBone`; Chance = 0.15 } };
	Pattern = { `Sweep`, `Chop`, `Reach` };
	Moves = {
		Sweep = { Kind = `Melee`; Clip = `Attack1`; Range = 6; Damage = 9; WindUp = 0.35; HitAt = 0.5; Rest = 0.8 };
		Chop = { Kind = `Melee`; Clip = `Attack2`; Range = 6; Damage = 11; WindUp = 0.4; HitAt = 0.55; Rest = 0.9 };
		Reach = { Kind = `Melee`; Clip = `Reach`; Special = true; WindUp = 0.9; Range = 11; Damage = 13; HitAt = 0.62; Rest = 1.9 };
	};
}

-- the Bone Spider (1.60): small, fast and fragile. It hangs on a silk thread over its lair (Ambush From = Above) and
-- drops on whoever walks under it; alone again, it climbs its thread back up. Two fang strikes, then WebSpit (a special:
-- the Kanji first), a glob of silk at where you stood that slows you, then an opening.
Beasts.Defs.BoneSpider = {
	Name = `Bone Spider`; Model = `BoneSpider`;
	Health = 65; WalkSpeed = 12; RunSpeed = 22; Sight = 45; Leash = 80; Roam = 10;
	StunGuard = 1.2;
	Ambush = { From = `Above`; Height = 13; Range = 9; Clip = `Drop`; Tell = 0.8; Rise = 0.45; Damage = 7; Radius = 5; Rest = 0.8;
		Reburrow = 12 };
	Spawn = { Max = 2; Respawn = 150; Lair = `BoneSpider` };
	Reward = { Exp = 70; Yen = 28; Trophy = { Id = `SpiderFang`; Chance = 0.15 } };
	Pattern = { `Fang`, `Fang2`, `Fang`, `WebSpit` };
	Moves = {
		Fang = { Kind = `Melee`; Clip = `Attack1`; Range = 4; Damage = 6; WindUp = 0.25; HitAt = 0.42; Rest = 0.5 };
		Fang2 = { Kind = `Melee`; Clip = `Attack2`; Range = 4.5; Damage = 8; WindUp = 0.3; HitAt = 0.44; Rest = 0.7 };
		WebSpit = { Kind = `Spit`; Clip = `WebSpit`; Special = true; Tell = 0.8; SpitAt = 0.68; Range = 32; Speed = 60; Radius = 2.6;
			Damage = 4; Slow = 2.5; Rest = 1.6 };
	};
}

-- the Crypt Bat (1.61): a red-eyed bat with torn crimson wings that hovers about chest-high (it flies on its HipHeight).
-- Two claw rakes, then Dive (a special: the Kanji first), a swoop down through you, and later Screech (a special), a
-- shriek that stuns everyone in front of it. Each is followed by an opening. Weak alone; they come in pairs.
Beasts.Defs.CryptBat = {
	Name = `Crypt Bat`; Model = `CryptBat`;
	Health = 50; WalkSpeed = 13; RunSpeed = 24; Sight = 50; Leash = 90; Roam = 14;
	StunGuard = 1.0;
	Spawn = { Max = 2; Respawn = 150; Lair = `CryptBat` };
	Reward = { Exp = 60; Yen = 24; Trophy = { Id = `BatClaw`; Chance = 0.15 } };
	Pattern = { `Rake`, `Rake2`, `Dive`, `Rake`, `Screech` };
	Moves = {
		Rake = { Kind = `Melee`; Clip = `Attack1`; Range = 4; Damage = 5; WindUp = 0.25; HitAt = 0.46; Rest = 0.5 };
		Rake2 = { Kind = `Melee`; Clip = `Attack2`; Range = 4; Damage = 6; WindUp = 0.25; HitAt = 0.42; Rest = 0.6 };
		Dive = { Kind = `Leap`; Clip = `Dive`; Special = true; Tell = 0.85; Min = 8; Max = 20; Arc = -2.6; Dur = 0.6; Through = 6;
			Damage = 10; Recover = 1.4; Rest = 2.0 };
		Screech = { Kind = `Screech`; Clip = `Screech`; Special = true; Tell = 0.9; ScreechAt = 0.52; Range = 14; Angle = 40;
			Damage = 3; Stun = 1.0; Rest = 1.8 };
	};
}

function Beasts.IsNight(ClockTime: number): boolean
	return ClockTime >= Beasts.Night.From or ClockTime < Beasts.Night.To
end

return Beasts
