--[[
	The Strikethrough (Chapter One's finale, 2.26.0). ReplicatedStorage.Cinematics.Strikethrough, played by
	Controllers.Cine as After Hours' Fight stage. Interactive: four prompts, 16 paths, about 30 s.
	Doc: docs/expansion/12-Interactive-Cutscenes.md (spec section 6).

	The beat: after hours you come back to Room 102 for Mira's file. The bell rings at the wrong hour, ink seeps out of
	her desk, and a faded student from the 1893 roll rises out of it: the Strikethrough. It lunges (dodge LEFT), comes
	again (SHOVE on the beat), fights you for the file (MASH), and you end it with one charged blow (HOLD, release on
	the seal). Every miss branches and the scene goes on; the file can be kept or torn (flag FileKept), which COLLECTED
	shows.

	Clips (Config.CineClips): the game's own where one fits (Uptilt, Fist RunningM1, Parried, Clinch, Posture Break,
	Fist M2) and the group's uploads (Tug, Shatter, YouTugPull). Hit times are noted at each use.

	Marks in workspace.NHCineSets.Strike (each place has its own):
	  You, LungeTo          you at Mira's desk (chair side); where its lunge lands, an arm's length from you
	  Rise, RiseLow         where it stands (the board side of the desk), and under the floor there (it rises)
	  DodgeTo, ThrownTo     your dodge (your left, +X here) and where its hit throws you (into the back-row desks)
	  TugYou, TugIt         the tug of war, across the desk
	  File, Desk            the file on Mira's desk; the desk (a desk-sized part: the shove moves the real desk)
	  Wide                  the establishing camera (aimed at the desk)
	  Bell                  attribute BellPart = the bell part's full name
	The action line runs You <-> It along the room's length. Every shot stays on one side of it: you are shot from your
	left (positive yaw), it from its right (negative yaw).
]]

local Def = {
	Set = `Strike`;
	Clock = 0.3; -- after hours, just past midnight (on this screen only)
	Actors = {
		{ Name = `You`; From = `Self`; Mark = `You`; Pose = `Stand` };
		{ Name = `It`; From = `Template:Strikethrough`; Mark = `RiseLow`; Pose = `Stand`; Display = `???`; Faceless = true };
	};
}

Def.Graph = { start = `Arrive`; segments = {
	Arrive = { len = 7.0; next = `Lunge` };
	Lunge = { len = 3.2; prompt = { kind = `Direction`; at = 2.1; dur = 0.9; slow = 0.12; options = { `Left`, `Right` }; answer = `Left`; label = `DODGE`;
		on = { Right = `Dodge`; Wrong = `Thrown` } } };
	Dodge = { len = 1.6; next = `Again` };
	Thrown = { len = 2.2; next = `Again` };
	Again = { len = 2.8; prompt = { kind = `Press`; at = 1.6; beat = 0.5; slow = 0.2; label = `SHOVE`; on = { Perfect = `Shove`; Good = `Shove`; Miss = `Grabbed` } } };
	Shove = { len = 1.8; next = `Tug` };
	Grabbed = { len = 2.0; next = `Tug` };
	Tug = { len = 3.0; prompt = { kind = `Mash`; at = 0.6; dur = 2.2; rate = 7; touchRate = 5; slow = 0.5; flag = `FileKept`;
		on = { Win = `Kept`; Lose = `Torn` } } };
	Kept = { len = 1.6; next = `Finisher` };
	Torn = { len = 1.8; next = `Finisher` };
	Finisher = { len = 3.0; prompt = { kind = `Hold`; at = 0.8; zoneAt = 1.1; zone = 0.15; slow = 0.3; label = `HOLD, RELEASE ON THE SEAL`;
		on = { Hit = `Shatter`; Miss = `Fade` } } };
	Shatter = { len = 3.2; next = `Still` };
	Fade = { len = 3.6; next = `Still` };
	Still = { len = 3.0 };
} }

local PAPER = Color3.fromRGB(214, 200, 168)
local INK = Color3.fromRGB(18, 14, 22)

function Def.Build(Ctx)
	-- a subject that's missing (no template in this place) falls back to its mark, so the framing still holds
	local function subj(A, Mark) return Ctx.Actor(A) or Ctx.Mark(Mark) end
	local You = function() return subj(`You`, `You`) end
	local It = function() return subj(`It`, `Rise`) end
	local Rig = function(N) return Ctx.Actor(N) end
	local Clip, Game = Ctx.Clip, Ctx.GameClip

	-- the file on Mira's desk (as COLLECTED shows it): a manila folder, the record on top
	local FileCF = Ctx.CF(`File`)
	local Folder = Ctx.Prop(`FileFolder`, { Size = Vector3.new(2.3, 0.06, 3.0); CFrame = FileCF * CFrame.new(0, 0.03, 0);
		Color = Color3.fromRGB(176, 140, 82); Material = Enum.Material.SmoothPlastic })
	local Page = Ctx.Prop(`FilePage`, { Size = Vector3.new(2.7, 0.02, 2.0); CFrame = FileCF * CFrame.new(0.05, 0.07, -0.04) * CFrame.Angles(0, math.rad(-92.5), 0);
		Color = PAPER; Material = Enum.Material.SmoothPlastic })
	-- the half that tears off (Torn): sits over the page's far half until it flies
	local Half = Ctx.Prop(`FileHalf`, { Size = Vector3.new(1.35, 0.021, 2.0); CFrame = Page.CFrame * CFrame.new(0.675, 0.002, 0);
		Color = PAPER; Material = Enum.Material.SmoothPlastic })
	-- one cold light over the desk: the only light on the fight besides the moon
	-- moonlight from high on the open side, wide enough for both of you and the desk (the room is near black after hours)
	local Lamp = Ctx.Prop(`FightLight`, { Size = Vector3.one * 0.2; Transparency = 1;
		CFrame = CFrame.lookAt(FileCF.Position + Vector3.new(0, 8.5, 0) + (-Ctx.CF(`You`).RightVector) * 3, FileCF.Position) })
	local Light = Instance.new(`SpotLight`)
	Light.Face, Light.Angle, Light.Range, Light.Brightness = Enum.NormalId.Front, 110, 24, 4
	Light.Color, Light.Shadows = Color3.fromRGB(176, 192, 255), true
	Light.Parent = Lamp
	-- a cold backlight on the board wall behind it: the pale figure stands out against it
	local Back = Ctx.Prop(`BackLight`, { Size = Vector3.one * 0.2; Transparency = 1; CFrame = Ctx.CF(`Rise`) * CFrame.new(0, 5.4, 3.7) })
	local BackLight = Instance.new(`PointLight`)
	BackLight.Range, BackLight.Brightness, BackLight.Color, BackLight.Shadows = 11, 2.2, Color3.fromRGB(150, 170, 255), false
	BackLight.Parent = Back

	-- the real desk and chair props (the scene's own meshes, nearest the marks), moved on this screen only and put back
	local function nearest(Name: string, At: Vector3, Within: number): BasePart?
		local Best, Dist = nil, Within
		for _, D in workspace:GetDescendants() do
			if D:IsA(`BasePart`) and D.Name == Name then
				local M = (D.Position - At).Magnitude
				if M < Dist then Best, Dist = D, M end
			end
		end
		return Best
	end
	local DeskCF = Ctx.CF(`Desk`)
	local DeskMesh = nearest(`StudentDesk`, DeskCF.Position, 1.5)
	local Chair = nearest(`StudentChair`, (Ctx.CF(`You`) * CFrame.new(0, 1.7, -1.5)).Position, 2)

	-- the camera's side of the line (+X here): the You mark's left
	local YouCF = Ctx.CF(`You`)
	local Side = -YouCF.RightVector -- your left
	local DeskTop = DeskCF.Position + Vector3.new(0, 1.3, 0)

	local function fade(Model: Model?, Dur: number, KillAt: number)
		if not Model then return end
		local TS = game:GetService(`TweenService`)
		for _, P in Model:GetDescendants() do
			if P:IsA(`BasePart`) then
				TS:Create(P, TweenInfo.new(Dur, Enum.EasingStyle.Sine, Enum.EasingDirection.In), { LocalTransparencyModifier = 1 }):Play()
			end
		end
		task.delay(KillAt, function()
			for _, E in Model:GetDescendants() do if E:IsA(`ParticleEmitter`) then E.Enabled = false end end
		end)
	end

	-- the exchange in profile: both bodies side on from the open side (+X here), centred between You and LungeTo,
	-- kept inside the east wall. (A framed full shot on you alone was too tight to hold it.)
	local Mid = (Ctx.Pos(`You`) + Ctx.Pos(`LungeTo`)) / 2
	local Profile = { keys = {
		{ t = 0; pos = Mid + Side * 5.6 + Vector3.new(0, 3.7, 0); look = Mid + Vector3.new(0, 3.6, 0); lens = 24 };
		{ t = 2; pos = Mid + Side * 5.3 + Vector3.new(0, 3.6, 0); look = Mid + Vector3.new(0, 3.6, 0); lens = 24 };
	} }

	local segments = {}

	-- Arrive: the room at night, the file, the ink.
	segments.Arrive = {
		shots = {
			{ name = `Night room`; dur = 3.0; subject = Ctx.Mark(`Desk`); fadeIn = 0.8;
				camera = { keys = {
					{ t = 0; pos = Ctx.Pos(`Wide`); look = DeskTop; lens = 28 };
					{ t = 3.0; pos = Ctx.Pos(`Wide`) + (DeskTop - Ctx.Pos(`Wide`)).Unit; look = DeskTop; lens = 28 };
				} };
				noise = { preset = `handheld_wide_mild`; gain = 0.3 } };
			{ name = `The file`; dur = 2.2; subject = Page;
				camera = { keys = {
					{ t = 0; pos = (FileCF * CFrame.new(0.4, 5.6, 3.2)).Position; look = (FileCF * CFrame.new(0, 0, 0.1)).Position; lens = 50 };
					{ t = 2.2; pos = (FileCF * CFrame.new(0.3, 5.0, 2.8)).Position; look = (FileCF * CFrame.new(0, 0, 0.2)).Position; lens = 50 };
				}; ease = `inout` };
				noise = { preset = `handheld_tele_mild`; gain = 0.25 }; dof = { at = Page } };
			-- low on the desk from your side: the ink comes up through its far edge
			{ name = `Seep`; dur = 1.8; subject = Ctx.Mark(`Desk`);
				camera = { frame = { size = `CU`; yaw = 35; pitch = -6; lens = 65 } };
				noise = { preset = `handheld_tele_mild`; gain = 0.3 }; dof = true };
		};
		events = {
			{ t = 0; place = { who = `It`; to = `RiseLow` } };
			{ t = 0.4; look = { who = `You`; at = `File` } };
			{ t = 3.5; bell = { volume = 0.5; speed = 0.5 } }; -- the wrong hour
			{ t = 5.4; fx = { template = `CombatFX.DownSmoke`; at = Ctx.Mark(`Desk`); color = INK; count = 16 } };
			{ t = 5.4; sound = { id = `rbxassetid://9125602882`; volume = 0.3; speed = 0.6 } }; -- the Archive's choral tone, low
			-- Mira's chair is knocked aside as it comes (the lunge needs the room)
			{ t = 6.2; move = { part = Chair; to = Chair and (Chair.CFrame * CFrame.new(0, 0, 0) + Side * -2.1) * CFrame.Angles(0, math.rad(24), 0); dur = 0.25 } };
		};
	}

	-- Lunge: it rises out of the desk into an upward strike (Uptilt, Hit 0.50), then lunges (Fist RunningM1, Hit 0.33).
	segments.Lunge = {
		shots = {
			-- low in the open aisle beside Mira's desk, looking up past its edge as it comes up (dutch)
			{ name = `It rises`; dur = 2.1; subject = It();
				camera = { keys = {
					-- just over the desk top (lower and the desk's edge fills the frame)
					{ t = 0; pos = (Ctx.CF(`You`) * CFrame.new(-3.2, 2.8, -0.6)).Position; look = Ctx.Pos(`Rise`, Vector3.new(0, 2.4, 0)); lens = 28; roll = -8 };
					{ t = 2.1; pos = (Ctx.CF(`You`) * CFrame.new(-3.2, 2.9, -0.4)).Position; look = Ctx.Pos(`Rise`, Vector3.new(0, 3.6, 0)); lens = 28; roll = -6 };
				}; ease = `out` };
				noise = { preset = `handheld_wide_mild`; gain = 0.4 }; dof = true;
				events = {
					{ t = 0.0; anim = { rig = Rig(`It`); id = Clip(`StrikeRise`) } };
					{ t = 0.5; shake = { strength = 0.4; dur = 0.35 } };
				} };
			-- profile on you as it comes: the scene slows on the prompt (dodge LEFT, it lunges from its right)
			{ name = `The lunge`; dur = 1.1; subject = You();
				camera = Profile; -- both bodies side on, from the open side
				noise = `auto`; dof = true;
				events = { { t = 0.0; anim = { rig = Rig(`It`); id = Clip(`StrikeLunge`) } } } };
		};
		events = {
			{ t = 0.0; walk = { who = `It`; to = `Rise`; dur = 0.5 } };
			{ t = 0.5; fx = { template = `CombatFX.Guardbreak`; at = Ctx.Mark(`Rise`); color = INK } };
			{ t = 0.6; look = { who = `You`; at = `It` } };
			{ t = 2.15; fx = { template = `CombatFX.Flashstep`; at = Rig(`It`) or Ctx.Mark(`Rise`); color = INK } };
			{ t = 2.15; walk = { who = `It`; to = `LungeTo`; dur = 0.35 } };
		};
	}

	-- Dodge: you slip left; it overshoots and recoils (Parried 1).
	segments.Dodge = {
		shots = {
			{ name = `Slip`; dur = 1.6; subject = You();
				camera = { frame = { size = `MS`; yaw = 40; pitch = 2; lens = 40 }; follow = `track` };
				noise = `auto`; dof = true;
				events = {
					{ t = 0.0; anim = { rig = Rig(`You`); id = Game(`Movement.Dash.LeftVector`) } };
					{ t = 0.1; anim = { rig = Rig(`It`); id = Clip(`StrikeRecoil`) } };
				} };
		};
		events = {
			{ t = 0.0; walk = { who = `You`; to = `DodgeTo`; dur = 0.35 } };
			{ t = 0.0; walk = { who = `It`; to = `LungeTo`; dur = 0.15 } };
			{ t = 0.0; fx = { template = `MovementFX.DashFX`; at = Rig(`You`) or Ctx.Mark(`You`) } };
			{ t = 0.4; look = { who = `You`; at = `It` } };
		};
	}

	-- Thrown: the lunge lands (Fist RunningM1 played again, Hit 0.33); you're thrown into the back-row desks.
	segments.Thrown = {
		shots = {
			{ name = `Thrown`; dur = 1.4; subject = You(); flash = { t = 0.33; dur = 0.05 };
				camera = Profile; -- both bodies side on, from the open side
				noise = `auto`; dof = true;
				events = {
					{ t = 0.0; anim = { rig = Rig(`It`); id = Clip(`StrikeLunge`) } };
					{ t = 0.33; hitstop = 0.12 };
					{ t = 0.33; shake = { strength = 0.7; dur = 0.4 } };
					{ t = 0.33; anim = { rig = Rig(`You`); id = Game(`Default.Knockback`) } };
					{ t = 0.85; anim = { rig = Rig(`You`); id = Game(`Weapons.Fist.Movement.Land`) } };
				} };
			{ name = `Into the desks`; dur = 0.8; subject = You();
				camera = { frame = { size = `WS`; yaw = 60; pitch = -4; lens = 28 } };
				noise = { preset = `handheld_wide_mild`; gain = 0.4 } };
		};
		events = {
			{ t = 0.0; walk = { who = `It`; to = `LungeTo`; dur = 0.3 } };
			{ t = 0.33; fx = { template = `HitType.Blunt`; at = Rig(`You`) or Ctx.Mark(`You`) } };
			{ t = 0.33; walk = { who = `You`; to = `ThrownTo`; dur = 0.45 } };
		};
	}

	-- Again: it comes back at you (the lunge at 0.8 speed lands on the prompt's beat). SHOVE on the beat.
	segments.Again = {
		shots = {
			{ name = `It comes again`; dur = 2.8; subject = It();
				camera = { keys = {
					{ t = 0; pos = (YouCF * CFrame.new(-1.6, 4.6, 3.2)).Position; look = Ctx.Pos(`Rise`, Vector3.new(0, 3.9, 0)); lens = 35 };
					{ t = 2.8; pos = (YouCF * CFrame.new(-1.3, 4.4, 2.6)).Position; look = Ctx.Pos(`LungeTo`, Vector3.new(0, 3.9, 0)); lens = 35 };
				}; ease = `inout` };
				noise = { preset = `handheld_normal_mild`; gain = 0.35 }; dof = { at = It() };
				events = { { t = 1.65; anim = { rig = Rig(`It`); id = Clip(`StrikeLunge`); speed = 0.8 } } } };
		};
		events = {
			{ t = 0.0; place = { who = `You`; to = `You` } };
			{ t = 0.0; place = { who = `It`; to = `Rise` } };
			{ t = 0.0; look = { who = `You`; at = `It` } };
			{ t = 1.65; walk = { who = `It`; to = `LungeTo`; dur = 0.5 } };
		};
	}

	-- Shove: you shove it back into the desk (Shove; it staggers: Posture Break). The desk slides.
	segments.Shove = {
		shots = {
			{ name = `Shove`; dur = 1.8; subject = You(); flash = { t = 0.2; dur = 0.05 };
				camera = Profile; -- both bodies side on, from the open side
				noise = `auto`; dof = true;
				events = {
					{ t = 0.0; anim = { rig = Rig(`You`); id = Game(`Weapons.Fist.Moves.Shove`) } };
					{ t = 0.2; hitstop = 0.1 };
					{ t = 0.2; shake = { strength = 0.5; dur = 0.35 } };
					{ t = 0.2; anim = { rig = Rig(`It`); id = Clip(`StrikeStagger`) } };
				} };
		};
		events = {
			{ t = 0.18; move = { part = DeskMesh; to = DeskMesh and DeskMesh.CFrame + DeskCF.LookVector * 1.6; dur = 0.18 } };
			{ t = 0.2; fx = { template = `HitType.Blunt`; at = Rig(`It`) or Ctx.Mark(`LungeTo`) } };
			{ t = 0.2; walk = { who = `It`; to = `Rise`; dur = 0.4 } };
		};
	}

	-- Grabbed: it gets your arm (Clinch, Hit 0.37).
	segments.Grabbed = {
		shots = {
			{ name = `Grabbed`; dur = 2.0; subject = You();
				camera = { frame = { size = `MCU`; yaw = 30; pitch = 2; lens = 50 } };
				noise = `auto`; dof = true;
				events = {
					{ t = 0.3; anim = { rig = Rig(`It`); id = Clip(`StrikeGrab`) } };
					{ t = 0.67; shake = { strength = 0.5; dur = 0.35 } };
					{ t = 0.67; anim = { rig = Rig(`You`); id = Game(`Default.Hit.2`) } };
				} };
		};
		events = { { t = 0.0; place = { who = `It`; to = `LungeTo` } } };
	}

	-- Tug: both of you on the file across the desk. MASH.
	segments.Tug = {
		shots = {
			{ name = `Tug of war`; dur = 3.0; subject = Page;
				camera = { keys = {
					-- high and behind your shoulder, so it faces us across the desk and the file sits between you
					{ t = 0; pos = DeskTop + Side * 4.2 + YouCF.LookVector * -5.5 + Vector3.new(0, 5.4, 0); look = DeskTop + YouCF.LookVector * 0.8 + Vector3.new(0, 1.1, 0); lens = 24 };
					{ t = 3.0; pos = DeskTop + Side * 4.0 + YouCF.LookVector * -5.1 + Vector3.new(0, 5.2, 0); look = DeskTop + YouCF.LookVector * 0.8 + Vector3.new(0, 1.1, 0); lens = 24 };
				} };
				noise = { preset = `handheld_normal_mild`; gain = 0.3 };
				events = {
					{ t = 0.0; anim = { rig = Rig(`You`); id = Clip(`YouTugPull`); looped = true } };
					{ t = 0.0; anim = { rig = Rig(`It`); id = Clip(`StrikeTug`); looped = true } };
				} };
		};
		events = {
			{ t = 0.0; place = { who = `You`; to = `TugYou` } };
			{ t = 0.0; place = { who = `It`; to = `TugIt` } };
			{ t = 0.0; look = { who = `You`; at = `File` } };
		};
	}

	-- Kept: the file holds; it's thrown off (Parried 1).
	segments.Kept = {
		shots = {
			{ name = `The file holds`; dur = 1.6; subject = Page;
				camera = { keys = {
					{ t = 0; pos = (FileCF * CFrame.new(1.6, 3.0, 2.6)).Position; look = FileCF.Position; lens = 50 };
					{ t = 1.6; pos = (FileCF * CFrame.new(1.3, 2.6, 2.2)).Position; look = FileCF.Position; lens = 50 };
				} };
				noise = { preset = `handheld_tele_mild`; gain = 0.3 }; dof = { at = Page };
				events = { { t = 0.1; anim = { rig = Rig(`It`); id = Clip(`StrikeRecoil`) } } } };
		};
		events = {
			{ t = 0.1; fx = { template = `CombatFX.Flashstep`; at = Rig(`It`) or Ctx.Mark(`TugIt`); color = INK } };
			{ t = 0.1; walk = { who = `It`; to = `Rise`; dur = 0.3 } };
		};
	}

	-- Torn: the page tears; half of it goes with the thing.
	segments.Torn = {
		shots = {
			{ name = `Torn`; dur = 1.8; subject = Page;
				camera = { keys = {
					{ t = 0; pos = (FileCF * CFrame.new(1.6, 3.0, 2.6)).Position; look = FileCF.Position; lens = 50 };
					{ t = 1.8; pos = (FileCF * CFrame.new(1.4, 2.7, 2.3)).Position; look = FileCF.Position; lens = 50 };
				} };
				noise = { preset = `handheld_tele_mild`; gain = 0.3 }; dof = { at = Page };
				events = { { t = 0.2; shake = { strength = 0.3; dur = 0.25 } } } };
		};
		events = {
			{ t = 0.2; move = { part = Half; to = Half.CFrame + Ctx.CF(`TugIt`).LookVector * -3.2 + Vector3.new(0, 1.6, 0); dur = 0.5 } };
			{ t = 0.2; fx = { template = `HitType.Slash`; at = Page; color = PAPER } };
			{ t = 0.2; sound = { id = `rbxassetid://9119907907`; volume = 0.3; speed = 1.4 } };
			{ t = 0.7; call = function() Half.Transparency = 1 end };
		};
	}

	-- Finisher: you draw back the heavy (Fist M2, held in its wind-up). HOLD, release on the seal.
	segments.Finisher = {
		shots = {
			{ name = `Charge`; dur = 3.0; subject = You();
				camera = { frame = { size = `MCU`; yaw = 30; pitch = 1; lens = 85 }; to = { size = `MCU`; yaw = 26; lens = 65 }; ease = `inout` };
				noise = { preset = `handheld_tele_mild`; gain = 0.3 }; dof = true;
				events = { { t = 0.8; anim = { rig = Rig(`You`); id = Clip(`YouFinisher`); speed = 0.05 } } } };
		};
		events = {
			{ t = 0.0; place = { who = `You`; to = `You` } };
			{ t = 0.0; place = { who = `It`; to = `LungeTo` } };
			{ t = 0.0; look = { who = `You`; at = `It` } };
		};
	}

	-- Shatter: the blow lands (Fist M2 strikes at 0.43); it comes apart in ink and pages (the group's StrikeShatter).
	segments.Shatter = {
		shots = {
			{ name = `Release`; dur = 0.6; subject = You(); flash = { t = 0.43; dur = 0.05 };
				camera = Profile; -- both bodies side on, from the open side
				noise = `auto`; dof = true;
				events = {
					{ t = 0.0; anim = { rig = Rig(`You`); id = Clip(`YouFinisher`) } };
					{ t = 0.43; hitstop = 0.18 };
					{ t = 0.43; shake = { strength = 1.0; dur = 0.5 } };
					{ t = 0.43; anim = { rig = Rig(`It`); id = Clip(`StrikeShatter`) } };
				} };
			{ name = `Pages`; dur = 2.6; subject = It();
				-- low and wide from the open side: it comes apart against the dark room
				camera = { keys = {
					-- low, side on to both of you, on its side of the middle (inside the east wall, 5.8 studs out)
					{ t = 0; pos = Mid + Side * 5.6 + YouCF.LookVector * 0.9 + Vector3.new(0, 1.7, 0); look = Ctx.Pos(`LungeTo`, Vector3.new(0, 3.2, 0)); lens = 20 };
					{ t = 2.6; pos = Mid + Side * 5.3 + YouCF.LookVector * 0.9 + Vector3.new(0, 1.6, 0); look = Ctx.Pos(`LungeTo`, Vector3.new(0, 3.0, 0)); lens = 20 };
				} };
				noise = { preset = `handheld_wide_mild`; gain = 0.3 };
				events = { { t = 0.0; timescale = { scale = 0.35; dur = 1.6 } } } };
		};
		events = {
			{ t = 0.43; fx = { template = `CombatFX.Guardbreak`; at = Rig(`It`) or Ctx.Mark(`LungeTo`); color = INK; count = 20 } };
			{ t = 0.45; fx = { template = `CombatFX.Guardbreak`; at = Rig(`It`) or Ctx.Mark(`LungeTo`); color = PAPER; count = 14 } };
			{ t = 0.6; call = function() fade(Ctx.Actor(`It`), 1.2, 1.4) end };
		};
	}

	-- Fade: it doesn't break; it fades out on its own, and the bell stops.
	segments.Fade = {
		shots = {
			{ name = `It fades`; dur = 3.6; subject = It();
				camera = { frame = { size = `MS`; yaw = -25; pitch = 2; lens = 45 } };
				noise = { preset = `handheld_normal_mild`; gain = 0.25 }; dof = true;
				events = { { t = 0.0; anim = { rig = Rig(`It`); id = Clip(`StrikeShatter`); speed = 0.6 } } } };
		};
		events = {
			{ t = 0.0; place = { who = `It`; to = `Rise` } };
			{ t = 0.2; sound = { id = `rbxassetid://9113584435`; volume = 0.2; speed = 0.5 } }; -- the bell, far off, cut short
			{ t = 0.4; call = function() fade(Ctx.Actor(`It`), 2.5, 2.6) end };
		};
	}

	-- Still: the empty room; your back to us at the desk.
	segments.Still = {
		shots = {
			{ name = `Silence`; dur = 3.0; subject = Ctx.Mark(`Desk`);
				camera = { keys = {
					-- the back corner on the open side (the south wall is 3.9 studs behind the You mark)
					{ t = 0; pos = (YouCF * CFrame.new(-5.6, 5.9, 3.1)).Position; look = DeskTop; lens = 22 };
					{ t = 3.0; pos = (YouCF * CFrame.new(-5.4, 6.2, 3.3)).Position; look = DeskTop; lens = 22 };
				}; ease = `inout` };
				noise = false };
		};
		events = {
			{ t = 0.0; place = { who = `You`; to = `You` } };
			{ t = 0.5; look = { who = `You`; at = `File` } };
		};
	}

	return {
		segments = segments;
		grade = { contrast = 0.18; saturation = -0.32; tint = { 190, 205, 255 }; bloom = { intensity = 0.45; size = 30; threshold = 0.96 } };
	}
end

return Def
