--[[
	Downed / Carry / Grip settings (shared so the client HUD can read ranges).

	Combat damage that would kill a character downs them instead. A downed character
	gets back up after DownedDuration unless someone grips (executes) them first.
]]

return {
	Enabled = true;
	NPCsCanBeDowned = true;       -- AI NPCs and dummies get downed instead of dying

	DownedHealth = 1;             -- health kept while downed
	DownedDuration = 15;          -- seconds until a downed character gets back up
	RecoverHealthFraction = 0.25; -- health on getting up (fraction of MaxHealth)

	CrawlSpeed = 4;               -- downed characters can crawl at this WalkSpeed
	CrawlMinSpeed = 0.75;         -- horizontal speed (studs/s) that switches idle -> crawl animation
	Animations = {
		Idle = `rbxassetid://135755197014043`;    -- downed idle (looped)
		Crawl = `rbxassetid://104405049546114`;   -- downed crawl (looped)
		-- carry revamp (owner's animations, 2026-11-01): idle and run for both sides, swapped by the carrier's speed
		Carry = `rbxassetid://125991799022390`;     -- IdleCarrier
		CarryRun = `rbxassetid://74994161301403`;   -- RunCarrier
		Carried = `rbxassetid://97775250868736`;    -- IdleCarried
		CarriedRun = `rbxassetid://115962071473492`; -- RunCarried
	};

	-- Where the carried body's root is held, relative to the carrier's Torso
	-- (x = right, y = up, z = back). The Carried animation drapes the body itself,
	-- so this stays upright. (playtest-blockers, 2026-11-25) Re-tuned for the carry revamp's clips: IdleCarrier
	-- raises the RIGHT arm over the body and wraps the left across the front (a fireman's carry), and IdleCarried
	-- lifts the body's torso about (1.8, 1.7, -0.2) off this point. The old (-1.3, 2.0, 0.6) was made for the earlier
	-- left-shoulder clip and floated the body upside down above the carrier's head. Now the body's torso lies on the
	-- right shoulder (about 1.6 up), the legs hang in front into the left arm. Scaled with the carrier's size.
	CarryOffset = CFrame.new(-0.5, -0.1, 0.65);

	CarryRange = 8;               -- studs from the downed character
	CarryWalkSpeed = 8;           -- (locomotion-pace, was 12) under the walk (Config.Locomotion.Speeds.Walk 10)
	CarryRunAt = 4;               -- studs/s: above this the run pair plays
	DropOnCarrierHit = true;      -- carrier drops the body when damaged

	GripRange = 8;
	GripDuration = 2.5;           -- fallback grip length if the grip animation can't load
	GripUsesAnimationLength = true; -- the kill lands when the gripper's animation ends

	-- Paired grip animations, picked by the gripper's weapon (Default if no match).
	GripAnimations = {
		Fist = {
			Gripper = `rbxassetid://113535146305250`;  -- Fist Grip
			Victim = `rbxassetid://82121099763038`;   -- Fist Grip (Victim)
		};
		Claws = {
			Gripper = `rbxassetid://113535146305250`;  -- Fist Grip (claws share it)
			Victim = `rbxassetid://82121099763038`;
		};
		Katana = {
			Gripper = `rbxassetid://89687789815973`;  -- Katana Grip
			Victim = `rbxassetid://127090783290737`;  -- Katana Grip (Victim)
		};
	};
	DefaultGripWeapon = `Katana`;

	-- Where the victim is placed relative to the gripper's root for the paired animation.
	-- Default: 3 studs in front, facing the gripper. Adjust to match how the animations were made.
	-- (playtest-blockers) The victim is now HELD here (welded, server-owned) for the whole grip, as racial grips
	-- already were, so a downed player can't crawl out of the execution and the pair stays lined up.
	GripVictimOffset = CFrame.new(0, 0, -3) * CFrame.Angles(0, math.pi, 0);

	RequestCooldown = 0.4;        -- per-player rate limit on carry/grip requests
}
