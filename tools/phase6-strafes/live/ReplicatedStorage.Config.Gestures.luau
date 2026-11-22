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
	Talk = { Id = 0; Src = "Cinematic / NPC Gestures/Talking2_R6"; Len = 3.77; Loop = true; Priority = "Action" };
	TalkRant = { Id = 0; Src = "Cinematic / NPC Gestures/TalkingGoinCrazy_R6"; Len = 4.8; Loop = true; Priority = "Action" };
	Argue_A = { Id = 0; Src = "Cinematic / NPC Gestures/Standing Arguing_R6"; Len = 20.8; Loop = true; Priority = "Action" };
	Argue_B = { Id = 0; Src = "Cinematic / NPC Gestures/Standing Arguing2_R6"; Len = 20.8; Loop = true; Priority = "Action" };
	Point = { Id = 0; Src = "Cinematic / NPC Gestures/Pointing Forward_R6"; Len = 4.7; Loop = true; Priority = "Action" };
	PhoneTalk = { Id = 0; Src = "Cinematic / NPC Gestures/Talking On Phone_R6"; Len = 38.83; Loop = true; Priority = "Action" };
	PhoneTalk_Upper = { Id = 0; Src = "Cinematic / NPC Gestures/Talking On Phone_R6"; Len = 38.83; Loop = true; Priority = "Action"; Upper = true; Walking = true };
	PhonePace = { Id = 0; Src = "Cinematic / NPC Gestures/Pacing And Talking On A Phone_R6"; Len = 37.63; Loop = true; Priority = "Action" };
	PhonePaceWide = { Id = 0; Src = "Cinematic / NPC Gestures/Talking Phone Pacing_R6"; Len = 42.23; Loop = true; Priority = "Action" };
	PrayKneelIn = { Id = 0; Src = "Cinematic / NPC Gestures/Praying_R6"; Len = 4; Loop = false; Priority = "Action"; Buckets = { 80, 90, 100 }; OwnerVisual = "V3 provisional" };
	PrayLoop = { Id = 0; Src = "Cinematic / NPC Gestures/Praying_R6"; Len = 3; Loop = true; Priority = "Action"; Buckets = { 80, 90, 100 } };
	PrayStandUp = { Id = 0; Src = "Cinematic / NPC Gestures/Praying_R6"; Len = 3.5; Loop = false; Priority = "Action"; Buckets = { 80, 90, 100 } };
	KneelInspect = { Id = 0; Src = "Cinematic / NPC Gestures/Kneeling Inspecting_R6"; Len = 4.93; Loop = true; Priority = "Action"; Buckets = { 80, 90, 100 } };
	Inspect = { Id = 0; Src = "Interaction Anims/Inspecting_R6"; Len = 3.17; Loop = true; Priority = "Action" };
	ReachDown = { Id = 0; Src = "Cinematic / NPC Gestures/Reaching Down_R6"; Len = 3; Loop = true; Priority = "Action" };
	Rummage = { Id = 0; Src = "Interaction Anims/Rummaging_R6"; Len = 4.83; Loop = true; Priority = "Action" };
	Gather = { Id = 0; Src = "Interaction Anims/Gathering Objects_R6"; Len = 5.97; Loop = true; Priority = "Action"; Buckets = { 80, 90, 100 } };
	Shove_InPlace = { Id = 0; Src = "Cinematic / NPC Gestures/Shove Reaction_R6"; Len = 2.43; Loop = false; Priority = "Action2"; Carry = nil };
	ShoveSpin_InPlace = { Id = 0; Src = "Cinematic / NPC Gestures/Shoved Reaction With Spin_R6"; Len = 4.53; Loop = false; Priority = "Action2"; Carry = nil };
	InjuredIdle = { Id = 0; Src = "Injured Anims/Injured Idle_R6"; Len = 9.33; Loop = true; Priority = "Action" };
	InjuredHurt = { Id = 0; Src = "Injured Anims/Injured Hurting Idle_R6"; Len = 6.03; Loop = true; Priority = "Action"; Buckets = { 80, 90, 100 } };
	Dizzy = { Id = 0; Src = "Idle Anims/Dizzy Idle_R6"; Len = 4.27; Loop = true; Priority = "Action" };
	LayingIdle = { Id = 0; Src = "Idle Anims/Laying Idle_R6"; Len = 2.13; Loop = true; Priority = "Action"; Lying = true };
	CheerSeated_Upper = { Id = 0; Src = "Cinematic / NPC Gestures/Cheering While Sitting_R6"; Len = 4.33; Loop = true; Priority = "Action2"; Upper = true; Seated = true };
	Bored = { Id = 0; Src = "Idle Anims/Bored_R6"; Len = 10.67; Loop = true; Priority = "Action" };
	SadIdle = { Id = 0; Src = "Idle Anims/Sad Idle_R6"; Len = 2.67; Loop = true; Priority = "Action" };
	Duck = { Id = 0; Src = "Idle Anims/Ducking_R6"; Len = 1.53; Loop = false; Priority = "Action2" };
	OrcIdle = { Id = 0; Src = "Idle Anims/Orc Idle_R6"; Len = 5.33; Loop = true; Priority = "Action" };
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
