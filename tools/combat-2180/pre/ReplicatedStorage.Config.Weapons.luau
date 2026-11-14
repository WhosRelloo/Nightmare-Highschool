
---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

---| Type Annotation |---

type		GripLocation = 'Left Arm' | 'Right Arm'
type		DamageType = 'Blunt' | 'Blood'


export type Weapon = {

	--| Stats |--

	Damage: number | NumberRange;
	MaxCombo: number;
	Posture: number?;

	DamageType: DamageType;
	Size: Vector3;

	M2Damage: number;
	Type: 'Hands' | 'Blade' | 'Guns';

	--| Properties |--

	Animations: { M1: { Animation }; M2: Animation; AerialM2: Animation; RunningM1: Animation; AerialM1: Animation; Block: Animation; Parry: Animation };
	Model: { Handle: (Model & { Handle: Motor6D }); Back: (Model & { Torso: Motor6D }); Grip: GripLocation };

	AnimationSpeed: number?;


}

local ClawsM1 = ReplicatedStorage.Assets.Animations.Weapons[`Claws`].M1
local FistM1 = ReplicatedStorage.Assets.Animations.Weapons[`Fist`].M1

---| Weapons Config |---

return {



	-- Claws (2026-11-01, owner's idle/walk + skills; attacks borrow the Fist set until Claws clips exist)
	[`Claws`] = {
		Damage = 3.5;
		MaxCombo = 4;
		Posture = 10;

		DamageType = `Slash`;
		Size = vector.create(5.5, 8, 6.5);

		M2Damage = 8;
		Type = `Hands`;

		Offset = CFrame.new(0, 0, -3.1); -- a little more reach than bare fists
		RunningAttack = { Lunge = 46; DamageMult = 1.5; Posture = 14; Stun = 1; Knockback = { Velocity = 40; Duration = 0.2 } };
		AerialAttack = { DiveAt = 0.56; Dive = 70; Offset = CFrame.new(0, -4.5, -2.4); Size = vector.create(7, 13, 7); DamageMult = 1.4; Posture = 18; Stun = 1.1; Knockback = { Velocity = 28; Duration = 0.2; UpVector = -1 } };

		Animations = {
			M1 = { ClawsM1[`1`], ClawsM1[`2`], ClawsM1[`3`], ClawsM1[`4`] };
			M2 = ReplicatedStorage.Assets.Animations.Weapons[`Claws`].M2;
			AerialM2 = ReplicatedStorage.Assets.Animations.Weapons[`Claws`].AerialM2;
			RunningM1 = ReplicatedStorage.Assets.Animations.Weapons[`Claws`].RunningM1;
			AerialM1 = ReplicatedStorage.Assets.Animations.Weapons[`Claws`].AerialM1;

			Block = ReplicatedStorage.Assets.Animations.Weapons[`Claws`].Block;
			Parry = ReplicatedStorage.Assets.Animations.Weapons[`Claws`].ParryAttempt;
		};

		Model = nil;

		AnimationSpeed = 1.2; -- quicker than fists
	};

	-- Fists (2026-11-01, owner's animations): quick blunt strikes, no weapon model.
	[`Fist`] = {
		-- the owner's Fist animations have no Hit/EndLag keyframes: contact times read off the keyframes (fastest limb)
		Markers = {
			["rbxassetid://75262630901232"] = { Hit = 0.42; EndLag = 0.52 };
			["rbxassetid://93727306716155"] = { Hit = 0.27; EndLag = 0.40 };
			["rbxassetid://77050950909273"] = { Hit = 0.35; EndLag = 0.47 };
			["rbxassetid://138087015993934"] = { Hit = 0.38; EndLag = 0.50 };
			["rbxassetid://137090091936227"] = { Hit = 0.33; EndLag = 0.67 }; -- running straight (clip keyframe "Hit" 0.33)
			["rbxassetid://105679347584694"] = { Hit = 0.66; EndLag = 0.80 }; -- slam lands 0.60-0.68 (scrubbed in Play)
			["rbxassetid://80262616372750"] = { Hit = 0.43; EndLag = 0.85 };
			["rbxassetid://106967014880853"] = { Hit = 0.40; EndLag = 1.10 };
		};
		Offset = CFrame.new(0, 0, -2.8); -- shorter reach than a blade (Katana uses -3.5)
		-- running attack: you carry your sprint into a lunging straight (burst at 0.32 s)
		RunningAttack = { Lunge = 42; DamageMult = 1.6; Posture = 18; Stun = 1; Knockback = { Velocity = 45; Duration = 0.2 } };
		-- downslam: hang through the wind-up, dive at 0.56 s, the fist lands at 0.66 s
		AerialAttack = { DiveAt = 0.56; Dive = 70; Offset = CFrame.new(0, -4.5, -2.2); Size = vector.create(7, 13, 7); DamageMult = 1.4; Posture = 20; Stun = 1.2; Knockback = { Velocity = 30; Duration = 0.2; UpVector = -1 } };

		Damage = 3;
		MaxCombo = 4;
		Posture = 12;

		DamageType = `Blunt`;
		Size = vector.create(5, 8, 6);

		M2Damage = 8;
		Type = `Hands`;

		Animations = {
			M1 = { FistM1[`1`], FistM1[`2`], FistM1[`3`], FistM1[`4`] }; -- in combo order (GetChildren has none)
			M2 = ReplicatedStorage.Assets.Animations.Weapons[`Fist`].M2;
			AerialM2 = ReplicatedStorage.Assets.Animations.Weapons[`Fist`].AerialM2;
			RunningM1 = ReplicatedStorage.Assets.Animations.Weapons[`Fist`].RunningM1;
			AerialM1 = ReplicatedStorage.Assets.Animations.Weapons[`Fist`].AerialM1;

			Block = ReplicatedStorage.Assets.Animations.Weapons[`Fist`].Block;
			Parry = ReplicatedStorage.Assets.Animations.Weapons[`Fist`].ParryAttempt;
		};

		Model = nil; -- hands only

		AnimationSpeed = 1.15;
	};

	[`Katana`] = {

		--| Stats |--

		Damage = 4;
		MaxCombo = 4;
		Posture = 15;

		DamageType = `Blood`;
		Size = vector.create(6, 10, 7);

		M2Damage = 10;
		Type = `Blade`;

		--| Properties |--

		Animations = {
			M1 = (function() -- (combat audit) in combo order: GetChildren has none, so the swings could come out shuffled
				local L = ReplicatedStorage.Assets.Animations.Weapons[`Katana`].M1:GetChildren()
				table.sort(L, function(A, B)
					local X, Y = tonumber(A.Name), tonumber(B.Name)
					if X and Y then return X < Y end
					return A.Name < B.Name
				end)
				return L
			end)();
			M2 = ReplicatedStorage.Assets.Animations.Weapons[`Katana`].M2;
			AerialM2 = ReplicatedStorage.Assets.Animations.Weapons[`Katana`].AerialM2;
			RunningM1 = ReplicatedStorage.Assets.Animations.Weapons["Katana"].RunningM1;
			AerialM1 = ReplicatedStorage.Assets.Animations.Weapons[`Katana`].AerialM1;

			Block = ReplicatedStorage.Assets.Animations.Weapons["Katana"].Block;
			Parry = ReplicatedStorage.Assets.Animations.Weapons["Katana"].ParryAttempt;
		};

		Model = {
			Handle = ReplicatedStorage.Assets.Weapons[`Katana`].Handle;
			Back = ReplicatedStorage.Assets.Weapons[`Katana`].Back;
			Grip = `Right Arm`;

		};


		AnimationSpeed = 1.3;
	};

} :: { [string]: Weapon }
