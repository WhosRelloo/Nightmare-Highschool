--[[ (phase6-strafes) NPC gestures: the clips, who plays what where, the caps, the get-up, the infirmary and the watch job.
	Spec: docs/superpowers/specs/2026-11-22-strafes-npc-gestures-design.md §2-§7. Server: Services.AI.StudentBrain.Gestures.
	Maths: Functions.Gestures (Pick, Bucket, Name).

	Clips[Base]: Id = the published id (group 15981569), 0 until the owner publishes ServerStorage.NHPublish.Gestures;
	  with 0, Studio plays ServerStorage.NHGestures["NHG_" .. Base (.. "_" .. bucket)] through RegisterKeyframeSequence and
	  live servers skip the gesture. Buckets = leg-length scale copies (80/90/100 % of a 2-stud leg). Ids for bucketed
	  clips are per bucket: Ids = { [80] = id, [90] = id, [100] = id }.
	  Src = the FIER ANIMATIONS source (read/copy only). Len / Carry / ContactPhase come from tools/phase6-strafes/anim/out/manifest.json.
	Cast: rules, first match wins (most specific first). Who keys must all equal Ctx[key] (a list = any of them).
]]
local C = {}

C.Clips = {
	Talk = { Id = 0; Src = "Cinematic / NPC Gestures/Talking2_R6"; Len = 3.767; Loop = true; Priority = "Action" };
	TalkRant = { Id = 0; Src = "Cinematic / NPC Gestures/TalkingGoinCrazy_R6"; Len = 4.8; Loop = true; Priority = "Action" };
	Argue_A = { Id = 0; Src = "Cinematic / NPC Gestures/Standing Arguing_R6"; Len = 20.8; Loop = true; Priority = "Action" };
	Argue_B = { Id = 0; Src = "Cinematic / NPC Gestures/Standing Arguing2_R6"; Len = 20.8; Loop = true; Priority = "Action" };
	Point = { Id = 0; Src = "Cinematic / NPC Gestures/Pointing Forward_R6"; Len = 4.7; Loop = true; Priority = "Action" };
	PhoneTalk = { Id = 0; Src = "Cinematic / NPC Gestures/Talking On Phone_R6"; Len = 38.833; Loop = true; Priority = "Action" };
	PhoneTalk_Upper = { Id = 0; Src = "Cinematic / NPC Gestures/Talking On Phone_R6"; Len = 38.833; Loop = true; Priority = "Action"; Upper = true; Walking = true };
	PhonePace = { Id = 0; Src = "Cinematic / NPC Gestures/Pacing And Talking On A Phone_R6"; Len = 37.633; Loop = true; Priority = "Action" };
	PhonePaceWide = { Id = 0; Src = "Cinematic / NPC Gestures/Talking Phone Pacing_R6"; Len = 42.233; Loop = true; Priority = "Action" };
	PrayKneelIn = { Id = 0; Src = "Cinematic / NPC Gestures/Praying_R6"; Len = 4.202; Loop = false; Priority = "Action"; Buckets = { 80, 90, 100 }; OwnerVisual = "V3 provisional" };
	PrayLoop = { Id = 0; Src = "Cinematic / NPC Gestures/Praying_R6"; Len = 3; Loop = true; Priority = "Action"; Buckets = { 80, 90, 100 } };
	PrayStandUp = { Id = 0; Src = "Cinematic / NPC Gestures/Praying_R6"; Len = 3.567; Loop = false; Priority = "Action"; Buckets = { 80, 90, 100 } };
	KneelInspect = { Id = 0; Src = "Cinematic / NPC Gestures/Kneeling Inspecting_R6"; Len = 4.933; Loop = true; Priority = "Action"; Buckets = { 80, 90, 100 } };
	Inspect = { Id = 0; Src = "Interaction Anims/Inspecting_R6"; Len = 3.167; Loop = true; Priority = "Action" };
	ReachDown = { Id = 0; Src = "Cinematic / NPC Gestures/Reaching Down_R6"; Len = 3; Loop = true; Priority = "Action" };
	Rummage = { Id = 0; Src = "Interaction Anims/Rummaging_R6"; Len = 4.833; Loop = true; Priority = "Action" };
	Gather = { Id = 0; Src = "Interaction Anims/Gathering Objects_R6"; Len = 5.967; Loop = true; Priority = "Action"; Buckets = { 80, 90, 100 } };
	Shove_InPlace = { Id = 0; Src = "Cinematic / NPC Gestures/Shove Reaction_R6"; Len = 2.433; Loop = false; Priority = "Action2"; Carry = { { 0, 0, 0, 0 }, { 0.1, 0, -0.3851, 0 }, { 0.2, 0, -0.7417, 0 }, { 0.3, 0, -1.0476, 0 }, { 0.4, 0, -1.3657, 0 }, { 0.5, 0, -1.725, 0 }, { 0.6, 0, -2.0813, 0 }, { 0.7, 0, -2.4122, 0 }, { 0.8, 0, -2.6859, 0 }, { 0.9, 0, -2.9517, 0 }, { 1, 0, -3.2184, 0 }, { 1.1, 0, -3.457, 0 }, { 1.2, 0, -3.6838, 0 }, { 1.3, 0, -3.9295, 0 }, { 1.4, 0, -4.1839, 0 }, { 1.5, 0, -4.4479, 0 }, { 1.6, 0, -4.7233, 0 }, { 1.7, 0, -5.0059, 0 }, { 1.8, 0, -5.297, 0 }, { 1.9, 0, -5.602, 0 }, { 2, 0, -5.9127, 0 }, { 2.1, 0, -6.1658, 0 }, { 2.2, 0, -6.435, 0 }, { 2.3, 0, -6.7603, 0 }, { 2.4, 0, -7.1155, 0 }, { 2.433, 0, -7.241, 0 } } };
	ShoveSpin_InPlace = { Id = 0; Src = "Cinematic / NPC Gestures/Shoved Reaction With Spin_R6"; Len = 4.533; Loop = false; Priority = "Action2"; Carry = { { 0, 0, 0, 0 }, { 0.1, 0, -0.3117, -0.5307 }, { 0.2, 0, -0.6067, -1.1548 }, { 0.3, 0, -0.8846, -2.3862 }, { 0.4, 0, -1.1609, -2.8741 }, { 0.5, 0, -1.4561, -3.2137 }, { 0.6, 0, -1.7302, -1.8692 }, { 0.7, 0, -2.0558, -2.3557 }, { 0.8, 0, -2.3852, -1.8187 }, { 0.9, 0, -2.6904, 1.6826 }, { 1, 0, -3.0066, 3.0188 }, { 1.1, 0, -3.34, 2.1909 }, { 1.2, 0, -3.6451, -8.3965 }, { 1.3, 0, -3.9312, -39.7226 }, { 1.4, 0, -4.0879, -87.2524 }, { 1.5, 0, -4.2416, -114.262 }, { 1.6, 0, -4.3973, -130.24 }, { 1.7, 0, -4.5744, -141.55 }, { 1.8, 0, -4.8251, -152.604 }, { 1.9, 0, -5.0731, -163.418 }, { 2, 0, -5.2026, -178.987 }, { 2.1, 0, -5.2118, -195.532 }, { 2.2, 0, -5.2678, -207.922 }, { 2.3, 0, -5.365, -211.112 }, { 2.4, 0, -5.4775, -208.648 }, { 2.5, 0, -5.5498, -205.697 }, { 2.6, 0, -5.6196, -203.123 }, { 2.7, 0, -5.6937, -200.563 }, { 2.8, 0, -5.7547, -198.254 }, { 2.9, 0, -5.7772, -196.314 }, { 3, 0, -5.7711, -192.719 }, { 3.1, 0, -5.7573, -190.37 }, { 3.2, 0, -5.7311, -190.493 }, { 3.3, 0, -5.6945, -191.2 }, { 3.4, 0, -5.6591, -192.697 }, { 3.5, 0, -5.632, -194.339 }, { 3.6, 0, -5.6095, -196.039 }, { 3.7, 0, -5.5947, -197.956 }, { 3.8, 0, -5.5942, -199.81 }, { 3.9, 0, -5.5893, -201.306 }, { 4, 0, -5.5938, -201.661 }, { 4.1, 0, -5.6008, -201.717 }, { 4.2, 0, -5.598, -201.574 }, { 4.3, 0, -5.5971, -201.344 }, { 4.4, 0, -5.5832, -201.142 }, { 4.5, 0, -5.5664, -201.078 }, { 4.533, 0, -5.5615, -201.15 } } };
	InjuredIdle = { Id = 0; Src = "Injured Anims/Injured Idle_R6"; Len = 9.333; Loop = true; Priority = "Action" };
	InjuredHurt = { Id = 0; Src = "Injured Anims/Injured Hurting Idle_R6"; Len = 6.033; Loop = true; Priority = "Action"; Buckets = { 80, 90, 100 } };
	Dizzy = { Id = 0; Src = "Idle Anims/Dizzy Idle_R6"; Len = 4.267; Loop = true; Priority = "Action" };
	LayingIdle = { Id = 0; Src = "Idle Anims/Laying Idle_R6"; Len = 2.133; Loop = true; Priority = "Action"; Lying = true };
	CheerSeated_Upper = { Id = 0; Src = "Cinematic / NPC Gestures/Cheering While Sitting_R6"; Len = 4.333; Loop = true; Priority = "Action2"; Upper = true; Seated = true };
	Bored = { Id = 0; Src = "Idle Anims/Bored_R6"; Len = 10.667; Loop = true; Priority = "Action" };
	SadIdle = { Id = 0; Src = "Idle Anims/Sad Idle_R6"; Len = 2.667; Loop = true; Priority = "Action" };
	Duck = { Id = 0; Src = "Idle Anims/Ducking_R6"; Len = 1.533; Loop = false; Priority = "Action2" };
	OrcIdle = { Id = 0; Src = "Idle Anims/Orc Idle_R6"; Len = 5.333; Loop = true; Priority = "Action" };
}

-- who plays what (spec §4). Hooks: Fidget, ChatSpeaker, ChatListener, Argue, Phone, PhoneWalk, Hangout, Locker, Post,
-- Confront, Gawk, Danger, ScuffleLoser, GetUp, Patient, Watch, Treat
C.Cast = {
	-- hangouts (Schedules.Linger, by clique)
	{ Hook = "Hangout"; Who = { Clique = "Choir" }; Clips = { { "PrayLoop", 1 } }; Chance = 0.6 };
	{ Hook = "Hangout"; Who = { Clique = "Vigil" }; Clips = { { "KneelInspect", 2 }, { "Inspect", 1 } }; Chance = 0.6 };
	{ Hook = "Hangout"; Who = { Clique = "Pack"; Moon = true }; Clips = { { "OrcIdle", 1 } }; Chance = 0.7 };
	{ Hook = "Hangout"; Who = { Clique = { "Court", "Delinquents" } }; Clips = { { "Bored", 1 } }; Chance = 0.4 };
	-- idle fidgets (StudentBrain.fidget)
	{ Hook = "Fidget"; Who = { Clique = "Athletes" }; Clips = { { "Point", 1 } }; Chance = 1; Weight = 0.12 };
	{ Hook = "Fidget"; Who = { Clique = { "Court", "Delinquents" } }; Clips = { { "Bored", 1 } }; Chance = 1; Weight = 0.15 };
	{ Hook = "Fidget"; Who = { Clique = "Ordinary" }; Clips = { { "Bored", 2 }, { "SadIdle", 1 } }; Chance = 1; Weight = 0.12 };
	{ Hook = "Fidget"; Who = { Clique = "Vigil" }; Clips = { { "Inspect", 1 } }; Chance = 1; Weight = 0.12 };
	{ Hook = "Fidget"; Who = { Clique = { "Ink", "Choir", "Pack" } }; Clips = { { "Bored", 1 } }; Chance = 1; Weight = 0.08 };
	-- chats (StudentBrain.chat)
	{ Hook = "ChatSpeaker"; Who = {}; Clips = { { "Talk", 3 }, { "TalkRant", 1 } }; Chance = 1 };
	{ Hook = "ChatListener"; Who = { Temper = "Shy" }; Clips = { { "SadIdle", 1 } }; Chance = 1 };
	{ Hook = "ChatListener"; Who = {}; Clips = { { "Bored", 1 } }; Chance = 0.6 };
	{ Hook = "Argue"; Who = {}; Clips = { { "Argue_A", 1 } }; Chance = 1 }; -- the partner plays Argue_B
	-- phones (fidgetPhone; Schedules.WalkTo while Passing)
	{ Hook = "Phone"; Who = { Space = "Wide" }; Clips = { { "PhonePaceWide", 1 }, { "PhonePace", 1 } }; Chance = 1 };
	{ Hook = "Phone"; Who = { Space = "Pace" }; Clips = { { "PhonePace", 1 }, { "PhoneTalk", 1 } }; Chance = 1 };
	{ Hook = "Phone"; Who = {}; Clips = { { "PhoneTalk", 1 } }; Chance = 1 };
	{ Hook = "PhoneWalk"; Who = {}; Clips = { { "PhoneTalk_Upper", 1 } }; Chance = 0.2 };
	-- places
	{ Hook = "Locker"; Who = {}; Clips = { { "Rummage", 1 } }; Chance = 0.5 };
	-- staff at their posts (Social.Npcs)
	{ Hook = "Post"; Who = { Npc = "Custodian" }; Clips = { { "Rummage", 2 }, { "Gather", 2 }, { "ReachDown", 1 } }; Chance = 1 };
	{ Hook = "Post"; Who = { Npc = "Nurse" }; Clips = { { "Inspect", 3 }, { "ReachDown", 1 }, { "KneelInspect", 1 } }; Chance = 1 };
	{ Hook = "Post"; Who = { Npc = "Ashgrave" }; Clips = { { "Inspect", 1 } }; Chance = 1 };
	{ Hook = "Post"; Who = { Npc = { "Hale", "Sallow", "Pryce", "Whitlock" } }; Clips = { { "Point", 1 }, { "Talk", 2 } }; Chance = 1 };
	{ Hook = "Post"; Who = { Npc = { "Varga", "Mallory", "Dunmore", "Rhys" } }; Clips = { { "Point", 1 } }; Chance = 1 };
	-- reactions
	{ Hook = "Confront"; Who = {}; Clips = { { "Point", 1 } }; Chance = 1 };
	{ Hook = "Gawk"; Who = {}; Clips = { { "TalkRant", 1 } }; Chance = 0.25 };
	{ Hook = "Danger"; Who = {}; Clips = { { "Duck", 1 } }; Chance = 1 };
	{ Hook = "ScuffleLoser"; Who = {}; Clips = { { "Shove_InPlace", 2 }, { "ShoveSpin_InPlace", 1 } }; Chance = 1 };
	{ Hook = "GetUp"; Who = {}; Clips = { { "Dizzy", 6 }, { "InjuredHurt", 4 } }; Chance = 1 };
	{ Hook = "Patient"; Who = { Spot = "Bed" }; Clips = { { "LayingIdle", 1 } }; Chance = 1 };
	{ Hook = "Patient"; Who = {}; Clips = { { "InjuredIdle", 1 }, { "Dizzy", 1 } }; Chance = 1 };
	{ Hook = "Watch"; Who = {}; Clips = { { "CheerSeated_Upper", 1 } }; Chance = 1 };
}

C.Caps = { MaxActive = 6; NearRange = 60; Cooldown = 20; StopFar = 80 };
C.GetUp = { Seconds = { 5, 8 } };
C.Infirmary = { VisitAfter = 3600; Stay = { 60, 120 }; Region = "Infirmary"; Zone = "Infirmary" };
C.Watch = { Rest = 0.25; Weight = 0.6; Speed = 0.8; Burst = 3; Others = 4; Practice = 0.3 };
C.PhoneWalk = 0.2;
C.PaceClear = { Pace = 2.5; Wide = 3.5 };
-- (owner defaults, 2026-11-22: confirm after playing) the Nurse treating a player. Infirmary.Care reads these; the coming
-- injury system replaces Care entirely (spec §6.4)
C.Treat = { Seconds = 3; Heal = "Full"; Cooldown = 180; Price = 0; Range = 8; CancelRange = 6; PlayerClip = "FirstAid" };

return C
