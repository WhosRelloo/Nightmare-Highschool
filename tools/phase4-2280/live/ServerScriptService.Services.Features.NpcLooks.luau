--[[
	NpcLooks (server). Services.Features.NpcLooks
	Gives a named NPC a full Nightmare High look through ReplicatedStorage.UI.Appearance (the same path the ambient
	students and delinquents use): face art (eyes, brows, mouth), skin, outfit and catalog hair. The quest characters,
	the Hall Monitor and the stealth watchers used to get only a hair on a recoloured rig, so they showed Roblox's
	default face.

		NpcLooks.Apply(Model, Spec)
			Spec: { Body = 1 | 2, Skin = n, Uniform = "<uniform id>", Bottoms = "<bottoms id>", Eyes = n,
			        Brows = "<brow style>", Mouth = "<mouth style>", HairId = assetId, HairColor = n?, HairHex = "RRGGBB"? }
		NpcLooks.Specs[key]   the cast's looks (keys: Config.Npcs ids, plus HallMonitor and the watcher names)
]]
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local Shared = {}

Shared.Specs = {
	-- Social.Npcs (Config.Npcs ids)
	Pip = { Body = 1; Skin = 2; Uniform = `navy-vest`; Bottoms = `uniform-trousers`; Eyes = 3; Brows = `soft`; Mouth = `smile`; HairId = 3576061351 };
	Ezra = { Body = 1; Skin = 1; Uniform = `vigil-vest`; Bottoms = `charcoal-slacks`; Eyes = 4; Brows = `straight`; Mouth = `flat`; HairId = 2680376026 };
	Vesper = { Body = 2; Skin = 1; Uniform = `crimson-court-vest`; Bottoms = `pleated-tartan-skirt`; Eyes = 5; Brows = `sharparch`; Mouth = `smirk`; HairId = 3612414364 };
	Varga = { Body = 1; Skin = 4; Uniform = `gym-pe-shirt`; Bottoms = `striped-joggers`; Eyes = 2; Brows = `flatthick`; Mouth = `frown`; HairId = 1852838120 };
	Mallory = { Body = 2; Skin = 3; Uniform = `gym-pe-shirt`; Bottoms = `khaki-shorts`; Eyes = 6; Brows = `arched`; Mouth = `smile`; HairId = 1903448711 };
	Dunmore = { Body = 1; Skin = 5; Uniform = `varsity-jacket`; Bottoms = `charcoal-slacks`; Eyes = 2; Brows = `furrowed`; Mouth = `flat`; HairId = 3609301673 };
	Dex = { Body = 1; Skin = 3; Uniform = `open-flannel`; Bottoms = `cargo-boots`; Eyes = 7; Brows = `angled`; Mouth = `grin`; HairId = 3379112107 };
	Bruno = { Body = 1; Skin = 4; Uniform = `leather-jacket`; Bottoms = `black-jeans`; Eyes = 2; Brows = `angry`; Mouth = `scowl`; HairId = 1848734696 };
	-- clique leaders (1.28)
	Rhys = { Body = 1; Skin = 3; Uniform = `varsity-jacket`; Bottoms = `striped-joggers`; Eyes = 2; Brows = `flatthick`; Mouth = `grin`; HairId = 1852838120 };
	Lucien = { Body = 1; Skin = 1; Uniform = `black-blazer`; Bottoms = `charcoal-slacks`; Eyes = 4; Brows = `straight`; Mouth = `flat`; HairId = 2680376026 };
	Wren = { Body = 2; Skin = 2; Uniform = `charcoal-vest`; Bottoms = `pleated-tartan-skirt`; Eyes = 5; Brows = `arched`; Mouth = `smirk`; HairId = 3612414364 };
	Sable = { Body = 2; Skin = 4; Uniform = `charcoal-cardigan`; Bottoms = `pleated-tartan-skirt`; Eyes = 6; Brows = `soft`; Mouth = `smirk`; HairId = 3432180024 }; -- (1.45) the seer
	-- staff
	HallMonitor = { Body = 1; Skin = 2; Uniform = `black-blazer`; Bottoms = `charcoal-slacks`; Eyes = 2; Brows = `furrowed`; Mouth = `frown`; HairId = 2689690284 };
	[`Mr. Hale`] = { Body = 1; Skin = 1; Uniform = `charcoal-cardigan`; Bottoms = `khaki-trousers`; Eyes = 4; Brows = `thick`; Mouth = `flat`; HairId = 3259670582 };
	Watcher = { Body = 1; Skin = 3; Uniform = `black-blazer`; Bottoms = `charcoal-slacks`; Eyes = 2; Brows = `straight`; Mouth = `frown` };
	-- (2.24.0) Phase 1 staff: Hale at his Room 102 desk (Config.Npcs Hale) wears the same look as the staff-room watcher.
	-- The Night Custodian's face is never seen (Faceless: no painted face, the head in shadow), at his day post and on watch.
	Hale = { Body = 1; Skin = 1; Uniform = `charcoal-cardigan`; Bottoms = `khaki-trousers`; Eyes = 4; Brows = `thick`; Mouth = `flat`; HairId = 3259670582 };
	[`Night Custodian`] = { Body = 1; Skin = 3; Uniform = `black-blazer`; Bottoms = `charcoal-slacks`; Eyes = 2; Brows = `straight`; Mouth = `frown`; HairId = 1940153034; Faceless = true };
	Custodian = { Body = 1; Skin = 3; Uniform = `black-blazer`; Bottoms = `charcoal-slacks`; Eyes = 2; Brows = `straight`; Mouth = `frown`; HairId = 1940153034; Faceless = true };
	-- (2.28) the subject teachers and the Headmaster (existing clothing ids and cast hair)
	Sallow = { Body = 2; Skin = 1; Uniform = `crest-blazer`; Bottoms = `wide-leg-trousers`; Eyes = 2; Brows = `straight`; Mouth = `flat`; HairId = 1903448711 };
	Pryce = { Body = 1; Skin = 3; Uniform = `victorian-waistcoat`; Bottoms = `trousers-chelsea`; Eyes = 4; Brows = `angled`; Mouth = `smile`; HairId = 3379112107 };
	Whitlock = { Body = 2; Skin = 2; Uniform = `cropped-cardigan`; Bottoms = `velvet-midi`; Eyes = 3; Brows = `soft`; Mouth = `flat`; HairId = 3432180024 };
	Ashgrave = { Body = 1; Skin = 1; Uniform = `wool-overcoat`; Bottoms = `charcoal-slacks`; Eyes = 2; Brows = `furrowed`; Mouth = `flat`; HairId = 3609301673 };
}

-- (2.24.0) a face nobody sees clearly: hide the painted face strips (now and whenever they're rebuilt) and put the head in shadow
function Shared.Shadow(Model: Model)
	local Head = Model:FindFirstChild(`Head`)
	if not (Head and Head:IsA(`BasePart`)) then return end
	Model:SetAttribute(`NHFaceless`, true)
	local function hide(D: Instance)
		if D:IsA(`SurfaceGui`) or D:IsA(`Decal`) then pcall(function() (D :: any).Enabled = false end) if D:IsA(`Decal`) then D.Transparency = 1 end end
	end
	for _, D in Head:GetDescendants() do hide(D) end
	Head.DescendantAdded:Connect(function(D) task.defer(hide, D) end)
	Head.Color = Color3.fromRGB(28, 26, 30)
end

local function styleIndex(List, Style: string?): number?
	if not Style then return nil end
	for I, X in List or {} do
		if type(X) == `table` and (X.Style == Style or X.Id == Style or X.Name == Style) then return I end
	end
	return nil
end

function Shared.Apply(Model: Model, Spec)
	if not (Model and Spec) then return false end
	local Ok, App = pcall(require, ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Appearance`))
	if not Ok then return false end
	local Look = App.Sanitize({})
	Look.Body = Spec.Body or 1
	Look.EyeSet = if (if Ok and App.IsFemale then App.IsFemale(Look) else Look.Body == 2) then 2 else 1
	Look.Skin = math.clamp(Spec.Skin or 2, 1, math.max(1, #App.Skins))
	Look.Uniform = (Spec.Uniform and App.IndexOf(App.Uniforms, Spec.Uniform)) or Look.Uniform
	Look.Bottoms = (Spec.Bottoms and App.IndexOf(App.BottomsList, Spec.Bottoms)) or Look.Bottoms
	Look.Eyes = math.clamp(Spec.Eyes or 2, 1, math.max(1, #App.Eyes))
	Look.Brows = styleIndex(App.Brows, Spec.Brows) or Look.Brows
	Look.Mouth = styleIndex(App.Mouths, Spec.Mouth) or Look.Mouth
	if Spec.HairId then Look.HairId = Spec.HairId end
	if Spec.HairColor then Look.HairColor = Spec.HairColor end
	if Spec.HairHex then Look.HairHex = Spec.HairHex end
	Look.Created = true
	Look._Idx = true
	local Done, Err = pcall(App.ApplyTo, Model, Look)
	if not Done then warn(`[NpcLooks] {Model.Name}: {Err}`) end
	if Spec.Faceless then Shared.Shadow(Model) end -- (2.24.0)
	return Done
end

return Shared
