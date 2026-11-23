--[[
	Race transformation forms (data). ReplicatedStorage.Config.Forms
	Spec: docs/superpowers/specs/2026-11-22-race-transformations-design.md (approved by the owner 2026-11-23).
	Read by ReplicatedStorage.Functions.Forms (Resolve), ReplicatedStorage.Lineage (the Look slots it adds) and
	Controllers.Character.FormParts (the pieces it clones from ReplicatedStorage.Assets.Forms).

	Owner rules (in the data, checked by tools/forms/checks/forms_pure.lua): students stay readable; no werewolf muzzle,
	no fur on the head, no Wraith lower-body cover, Wraith heads clear; no claws and no wing hooks on any race;
	sculpted geometry only. Humans and Priests have no form.

	Races[race].Directions[i]: Id ("1"/"2", the FormDirection Look), Name, Parts (its body pieces, welded to the R6
	parts, one fitted variant per body type: Assets.Forms.Bodies.<body>.<race letter><Id><Part>, e.g. W1Mantle; head
	pieces in Assets.Forms.NHFormHead), Wings / Horns (the direction's defaults, or nil).
	A race's WingStyles / HornStyles are what the Looks may pick; a direction's own style is Tier I, two more Tier II,
	the rest Tier III (Lineage builds the options from this table).
]]

local rgb = Color3.fromRGB

local Forms = {}

-- the wing skeleton's styles (art: art/characters/transformations/hqwing.py STYLES). Bones: Hum, Fore, D<n>a/D<n>b.
Forms.WingStyles = {
	Nocturne = { Name = "Nocturne"; Digits = 4; Membrane = true };
	Wyrm = { Name = "Wyrm"; Digits = 3; Membrane = true };
	Tattered = { Name = "Tattered"; Digits = 4; Membrane = true };
	Fallen = { Name = "Fallen"; Digits = 4; Feathers = true };
	Ossuary = { Name = "Ossuary"; Digits = 4; Tatters = true };
	Wraithveil = { Name = "Wraithveil"; Digits = 4; Membrane = true; Glow = true };
	Rime = { Name = "Rime"; Digits = 4; Membrane = true; Shards = true };
}

-- horns (art: hqwing.horns). Halo = the Sovereign's spiked halo (spins on the client)
Forms.HornStyles = {
	Ram = { Name = "Ram" };
	Demon = { Name = "Demon" };
	Wendigo = { Name = "Wendigo (antlers)" };
	Thorn = { Name = "Thorn crown" };
	Broken = { Name = "Broken" };
	Sovereign = { Name = "Sovereign"; Halo = true };
	Bull = { Name = "Bull" };
}

-- palettes tint the membrane / feathers; finishes tint bones, horns and tips (one SurfaceAppearance set each, ids in
-- Forms.Art once uploaded; until then the colours tint the base set)
Forms.Palettes = {
	Wine = { Name = "Wine"; Color = rgb(122, 20, 34) };
	Midnight = { Name = "Midnight"; Color = rgb(52, 60, 112) };
	Ashen = { Name = "Ashen"; Color = rgb(196, 190, 184) };
	Ember = { Name = "Ember"; Color = rgb(176, 70, 30) };
	Raven = { Name = "Raven"; Color = rgb(34, 36, 48) };
	Dove = { Name = "Dove"; Color = rgb(232, 230, 236) };
}
Forms.PaletteOrder = { "Wine", "Midnight", "Ashen", "Ember", "Raven", "Dove" }

Forms.Finishes = {
	Obsidian = { Name = "Obsidian"; Color = rgb(30, 28, 34) };
	Bone = { Name = "Bone"; Color = rgb(214, 204, 180) };
	Gilded = { Name = "Gilded"; Color = rgb(196, 156, 74) };
	Ivory = { Name = "Ivory"; Color = rgb(236, 230, 214) };
	Bloodstone = { Name = "Bloodstone"; Color = rgb(110, 16, 26) };
}
Forms.FinishOrder = { "Obsidian", "Bone", "Ivory", "Bloodstone", "Gilded" }

Forms.WingSizes = { Small = 0.8; Regular = 1; Grand = 1.2 }
Forms.SizeOrder = { "Regular", "Small", "Grand" }

-- the finish an added horn gets when the direction has no horns of its own
Forms.HornDefaults = { Finish = "Obsidian"; Tip = "Gilded" }

Forms.Races = {
	Vampire = {
		Directions = {
			{ Id = "1"; Name = "Nocturne"; Parts = {}; -- its long swept ears are the Vampire Ears Look
				Wings = { Style = "Nocturne"; Palette = "Wine"; Finish = "Obsidian" } };
			{ Id = "2"; Name = "Night Sovereign"; Parts = { "Spines" };
				Wings = { Style = "Wyrm"; Palette = "Wine"; Finish = "Bloodstone" };
				Horns = { Style = "Demon"; Finish = "Obsidian"; Tip = "Bloodstone" } };
		};
		WingStyles = { "Nocturne", "Wyrm", "Tattered", "Fallen" };
		HornStyles = { "Demon", "Ram", "Broken", "Sovereign", "Bull" };
	};
	Werewolf = {
		-- fur locks on the shoulders, forearms and shins (no head fur, no muzzle); the tail and ears are the race Looks
		Directions = {
			{ Id = "1"; Name = "Moonbound"; Parts = { "Mantle", "CuffL", "CuffR", "ShinL", "ShinR" }; Mantle = "Shoulders" };
			{ Id = "2"; Name = "Feral Lord"; Parts = { "Mantle", "Back", "ArmL", "ArmR", "Moon" }; Mantle = "Full" };
		};
	};
	Ghoul = {
		Directions = {
			{ Id = "1"; Name = "Ossuary"; Parts = { "Ribs", "Spine", "SpurL", "SpurR", "Jaw" };
				Wings = { Style = "Ossuary"; Palette = "Wine"; Finish = "Bone" };
				Horns = { Style = "Wendigo"; Finish = "Bone"; Tip = "Ivory" } };
			{ Id = "2"; Name = "Gravecloth"; Parts = { "WrapL", "WrapR", "Chest", "Moss", "Nails" };
				Horns = { Style = "Thorn"; Finish = "Obsidian"; Tip = "Bone" } };
		};
		WingStyles = { "Ossuary" };
		HornStyles = { "Wendigo", "Thorn", "Ram" };
	};
	Wraith = {
		-- head clear (no horns at all); legs and uniform show
		Directions = {
			{ Id = "1"; Name = "Hollow Shroud"; Parts = { "Capelet" };
				Wings = { Style = "Wraithveil"; Palette = "Midnight"; Finish = "Ivory" } };
			{ Id = "2"; Name = "Frost Revenant"; Parts = { "SpikeL", "SpikeR", "Chains", "Hang", "RimeL", "RimeR" };
				Wings = { Style = "Rime"; Palette = "Midnight"; Finish = "Ivory" } };
		};
		WingStyles = { "Wraithveil", "Rime", "Tattered" };
	};
}

-- uploaded art (filled once the owner imports the mesh set and textures; 0 = not yet, the client skips the piece)
Forms.Art = {}

return Forms
