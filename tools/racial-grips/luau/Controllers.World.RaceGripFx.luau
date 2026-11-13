--[[
	RaceGripFx (client, 2.2.0): the VFX, sound and camera for the six racial grips (N on a downed body).
	Started by World.RaceActionFx when the server's "RaceAction" Fx arrives with a Kind from Config.RaceGrips.
	Beats are the clip times in Config.RaceGrips.Kinds[Kind].Beats (the clips were authored to them).

	Rules (VFX bible + owner): no blood or gore anywhere (no red liquid, nothing comes off the victim's body),
	client-only and pooled under workspace.NHFx, shake via Fx.Shake (NHShakeScale), flashes via Fx.Flash
	(NHReducedFlash caps them), particle counts via Fx.Count (NHFxQuality). Everything stops if the grip is
	cancelled (the gripper's GripEndsAt changes).
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local TweenService = game:GetService(`TweenService`)
local Lighting = game:GetService(`Lighting`)
local Debris = game:GetService(`Debris`)

local Cfg = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`RaceGrips`))
local Player = Players.LocalPlayer

local Shared = {}
local Fx -- Controllers.Fx (set in Init)

local function id(s: string?): string?
	if not s or s == `rbxassetid://0` or s == `` then return nil end
	return s
end
local TEX = Cfg.Textures
local function tex(name: string, fallback: string?): string
	return id(TEX[name]) or fallback or Fx.Tex.Wisp
end

---| small builders (all local, parented under workspace.NHFx and cleaned by the run's trash list) |---

local function fxFolder(): Folder
	local F = workspace:FindFirstChild(`NHFx`)
	if not F then
		F = Instance.new(`Folder`)
		F.Name = `NHFx`
		F.Parent = workspace
	end
	return F
end

local function part(cf: CFrame, size: Vector3?): BasePart
	local P = Instance.new(`Part`)
	P.Name = `GripFx`
	P.Size = size or Vector3.new(0.2, 0.2, 0.2)
	P.Transparency = 1
	P.Anchored, P.CanCollide, P.CanQuery, P.CanTouch, P.CastShadow = true, false, false, false, false
	P.CFrame = cf
	P.Parent = fxFolder()
	return P
end

local function ns(points: { { number } }): NumberSequence
	local K = {}
	for _, p in points do table.insert(K, NumberSequenceKeypoint.new(p[1], p[2], p[3] or 0)) end
	return NumberSequence.new(K)
end

-- a looping emitter on an attachment (Rate is scaled by quality); returns it so the run can stop it
local function emitter(parent: Instance, o: { [string]: any }): ParticleEmitter
	local E = Instance.new(`ParticleEmitter`)
	E.Texture = o.Texture or Fx.Tex.Smoke
	E.Color = if typeof(o.Color) == `ColorSequence` then o.Color else ColorSequence.new(o.Color or Color3.new(1, 1, 1))
	E.Size = if typeof(o.Size) == `NumberSequence` then o.Size else ns({ { 0, o.Size or 0.5 }, { 1, (o.Size or 0.5) * 1.6 } })
	E.Transparency = o.Transparency or ns({ { 0, 1 }, { 0.15, 0.35 }, { 0.75, 0.6 }, { 1, 1 } })
	E.Lifetime = if typeof(o.Lifetime) == `number` then NumberRange.new(o.Lifetime) else (o.Lifetime or NumberRange.new(0.8, 1.4))
	E.Speed = if typeof(o.Speed) == `number` then NumberRange.new(o.Speed) else (o.Speed or NumberRange.new(0.5, 1.5))
	E.SpreadAngle = Vector2.new(o.Spread or 25, o.Spread or 25)
	E.Acceleration = o.Accel or Vector3.zero
	E.Drag = o.Drag or 1
	E.LightEmission = o.LightEmission or 0.3
	E.LightInfluence = o.LightInfluence or 0.4
	E.EmissionDirection = o.Direction or Enum.NormalId.Top
	E.Rotation = NumberRange.new(0, 360)
	E.RotSpeed = o.RotSpeed or NumberRange.new(-30, 30)
	E.ZOffset = o.ZOffset or 0
	if o.Flipbook then
		E.FlipbookLayout = Enum.ParticleFlipbookLayout[o.Flipbook]
		E.FlipbookMode = Enum.ParticleFlipbookMode[o.FlipMode or `OneShot`]
	end
	E.Rate = Fx.Count(o.Rate or 10)
	E.Parent = parent
	return E
end

local function burst(parent: Instance, o: { [string]: any }, n: number)
	local E = emitter(parent, o)
	E.Rate = 0
	E:Emit(Fx.Count(n))
	Debris:AddItem(E, (E.Lifetime.Max or 1) + 0.3)
end

-- a flat decal disc on the floor (soft art only) that the run can spin, grow and fade
local function floorDisc(pos: Vector3, image: string, color: Color3, size: number, alpha: number?): (BasePart, { Decal })
	local P = part(CFrame.new(pos) * CFrame.Angles(0, math.random() * math.pi * 2, 0), Vector3.new(size, 0.05, size))
	local decals = {}
	for _, face in { Enum.NormalId.Top, Enum.NormalId.Bottom } do
		local D = Instance.new(`Decal`)
		D.Texture = image
		D.Color3 = color
		D.Face = face
		D.Transparency = 1
		D.Parent = P
		table.insert(decals, D)
	end
	local target = alpha or 0.25
	for _, D in decals do TweenService:Create(D, TweenInfo.new(0.35, Enum.EasingStyle.Quint), { Transparency = target }):Play() end
	return P, decals
end

local function fadeOut(P: Instance?, t: number)
	if not P or not P.Parent then return end
	for _, D in P:GetDescendants() do
		if D:IsA(`Decal`) or D:IsA(`Texture`) then TweenService:Create(D, TweenInfo.new(t, Enum.EasingStyle.Sine), { Transparency = 1 }):Play()
		elseif D:IsA(`ParticleEmitter`) then D.Enabled = false
		elseif D:IsA(`Beam`) then D.Enabled = false
		elseif D:IsA(`PointLight`) then TweenService:Create(D, TweenInfo.new(t), { Brightness = 0 }):Play() end
	end
	if P:IsA(`BasePart`) and P.Transparency < 1 then TweenService:Create(P, TweenInfo.new(t), { Transparency = 1 }):Play() end
	Debris:AddItem(P, t + 1.5)
end

local function beam(a0: Attachment, a1: Attachment, o: { [string]: any }): Beam
	local B = Instance.new(`Beam`)
	B.Attachment0, B.Attachment1 = a0, a1
	B.Texture = o.Texture
	B.TextureMode = Enum.TextureMode.Wrap
	B.TextureLength = o.Length or 2
	B.TextureSpeed = o.Speed or 1.5
	B.Color = ColorSequence.new(o.Color or Color3.new(1, 1, 1))
	B.Transparency = o.Transparency or ns({ { 0, 0.7 }, { 0.5, 0.15 }, { 1, 0.7 } })
	B.Width0, B.Width1 = o.Width0 or 0.6, o.Width1 or 0.4
	B.LightEmission = o.LightEmission or 0.8
	B.FaceCamera = true
	B.Segments = 16
	B.CurveSize0, B.CurveSize1 = o.Curve0 or 0, o.Curve1 or 0
	B.Parent = a0.Parent
	return B
end

local function light(parent: Instance, color: Color3, brightness: number, range: number): PointLight
	local L = Instance.new(`PointLight`)
	L.Color, L.Range, L.Shadows = color, range, false
	L.Brightness = 0
	L.Parent = parent
	TweenService:Create(L, TweenInfo.new(0.3), { Brightness = brightness * Fx.FlashScale() }):Play()
	return L
end

local function attachTo(model: Model?, partName: string, offset: Vector3?): Attachment?
	local P = model and model:FindFirstChild(partName) :: BasePart?
	if not P then return nil end
	local A = Instance.new(`Attachment`)
	A.Name = `GripFxAtt`
	A.Position = offset or Vector3.zero
	A.Parent = P
	return A
end

local function sound(idName: string, parent: Instance?, volume: number?, looped: boolean?): Sound?
	local sid = id(Cfg.Sounds[idName])
	if not sid or not parent then return nil end
	local S = Instance.new(`Sound`)
	S.SoundId = sid
	S.Volume = volume or 0.9
	S.Looped = looped == true
	S.RollOffMinDistance, S.RollOffMaxDistance = 8, 90
	S.Parent = parent
	S:Play()
	if not looped then Debris:AddItem(S, 8) end
	return S
end

local function floorY(at: Vector3, ignore: { Instance }): number
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = ignore
	local hit = workspace:Raycast(at + Vector3.new(0, 2, 0), Vector3.new(0, -12, 0), params)
	return if hit then hit.Position.Y + 0.04 else at.Y - 2.9
end

local function torsoPos(m: Model?): Vector3?
	local T = m and (m:FindFirstChild(`Torso`) or m:FindFirstChild(`HumanoidRootPart`)) :: BasePart?
	return T and T.Position
end

-- a pallor that creeps over a body (Highlight fill, no outline), returned so the run can clear it
local function pallor(m: Model?, color: Color3, toAlpha: number, t: number): Highlight?
	if not m then return nil end
	local H = Instance.new(`Highlight`)
	H.Name = `GripPallor`
	H.FillColor = color
	H.FillTransparency = 1
	H.OutlineTransparency = 1
	H.DepthMode = Enum.HighlightDepthMode.Occluded
	H.Adornee = m
	H.Parent = m
	TweenService:Create(H, TweenInfo.new(t, Enum.EasingStyle.Sine), { FillTransparency = toAlpha }):Play()
	return H
end

-- a translucent copy of a body (the soul / the demon), pieces updated by the caller every frame
local function ghostOf(m: Model, color: Color3, material: Enum.Material, alpha: number): { [BasePart]: BasePart }
	local out = {}
	for _, n in { `Head`, `Torso`, `Left Arm`, `Right Arm`, `Left Leg`, `Right Leg` } do
		local src = m:FindFirstChild(n) :: BasePart?
		if src then
			local P = part(src.CFrame, src.Size * 1.03)
			P.Material = material
			P.Color = color
			P.Transparency = 1
			TweenService:Create(P, TweenInfo.new(0.4), { Transparency = alpha }):Play()
			out[src] = P
		end
	end
	return out
end

---| camera beats for the gripper's own screen (hit-stop feel + push-in; all reduced by the settings) |---

local function camPunch(strength: number, fovDrop: number)
	Fx.Shake(strength, 0.35)
	if Fx.Reduced() then return end
	local Cam = workspace.CurrentCamera
	if not Cam then return end
	local f0 = Cam.FieldOfView
	TweenService:Create(Cam, TweenInfo.new(0.06, Enum.EasingStyle.Quad), { FieldOfView = f0 - fovDrop }):Play()
	task.delay(0.12, function()
		TweenService:Create(Cam, TweenInfo.new(0.45, Enum.EasingStyle.Sine), { FieldOfView = f0 }):Play()
	end)
end

---| the victim's own screen: edges darken, the colour drains, a slowing heartbeat |---

local function victimScreen(run, len: number)
	local CC = Instance.new(`ColorCorrectionEffect`)
	CC.Name = `NHGripVictim`
	CC.Parent = Lighting
	TweenService:Create(CC, TweenInfo.new(len * 0.8, Enum.EasingStyle.Sine), { Saturation = -0.75, Brightness = -0.08, Contrast = 0.1 }):Play()
	table.insert(run.trash, CC)
	Fx.Veil(len * 0.7, 0.15, 0.6, Color3.fromRGB(7, 6, 10))
	local hb = sound(`VictimHeartbeat`, workspace.CurrentCamera, 0.8, true)
	if hb then
		table.insert(run.trash, hb)
		TweenService:Create(hb, TweenInfo.new(len, Enum.EasingStyle.Linear), { PlaybackSpeed = 0.7 }):Play()
	end
end

---| per-race sequences. Each gets run = { k, g (gripper), v (victim), t0, rich, sig, trash, at(t, fn) } |---

local Seq = {}

Seq.BloodDrain = function(run)
	local k, g, v = run.k, run.g, run.v
	local C, A = k.Color, k.Accent
	local vt = torsoPos(v) or g:GetPivot().Position
	local sig, sigD = floorDisc(Vector3.new(vt.X, floorY(vt, { g, v }), vt.Z), TEX.Sigil.Vampire, A, 1, 0.55)
	table.insert(run.trash, sig)
	TweenService:Create(sig, TweenInfo.new(0.6, Enum.EasingStyle.Quint), { Size = Vector3.new(9, 0.05, 9) }):Play()
	-- the vampire's eyes / rim
	local rim = Instance.new(`Highlight`)
	rim.FillTransparency, rim.OutlineColor, rim.OutlineTransparency = 1, A, 0.55
	rim.DepthMode = Enum.HighlightDepthMode.Occluded
	rim.Adornee, rim.Parent = g, g
	table.insert(run.trash, rim)
	local eye = attachTo(g, `Head`, Vector3.new(0, 0.15, -0.5))
	if eye then table.insert(run.trash, eye) light(eye, A, 1.2, 4) end
	run.at(k.Beats.Bite, function()
		-- a storm of bats wheels around both bodies, hiding the bite
		local cen = attachTo(v, `Torso`, Vector3.new(0, 1, 0))
		if not cen then return end
		table.insert(run.trash, cen)
		local bats = emitter(cen, { Texture = TEX.Bats; Flipbook = `Grid4x4`; FlipMode = `Loop`; Color = if run.sig == `BatsGold` then Color3.fromRGB(235, 205, 120) else Color3.fromRGB(26, 20, 30);
			Size = ns({ { 0, 0.5 }, { 0.5, 0.9 }, { 1, 0.4 } }); Lifetime = NumberRange.new(0.9, 1.6); Speed = NumberRange.new(5, 9); Spread = 180;
			Drag = 2.5; LightEmission = 0; LightInfluence = 1; Rate = if run.rich then 60 else 42; RotSpeed = NumberRange.new(-200, 200);
			Transparency = ns({ { 0, 1 }, { 0.1, 0 }, { 0.85, 0 }, { 1, 1 } }) })
		bats.Acceleration = Vector3.new(0, 2, 0)
		run.batsEmitter = bats
		task.delay(0.5, function() if bats.Parent then bats.Rate = Fx.Count(14) end end)
		sound(if run.sig == `BatsGold` then `BatsGold` else ``, cen)
		-- the life thread: neck -> mouth
		local a0 = attachTo(v, `Head`, Vector3.new(0.3, -0.5, 0))
		local a1 = attachTo(g, `Head`, Vector3.new(0, -0.2, -0.45))
		if a0 and a1 then
			table.insert(run.trash, a0) table.insert(run.trash, a1)
			beam(a0, a1, { Texture = tex(`LifeThread`, Fx.Tex.Wisp); Color = C; Width0 = 0.35; Width1 = 0.18; Speed = 2.6; Length = 1.2;
				Curve0 = 0.6; Curve1 = -0.4 })
			emitter(a0, { Texture = Fx.Tex.Wisp; Color = C; Size = 0.25; Lifetime = 0.6; Speed = NumberRange.new(1.5, 2.5); Spread = 30;
				Rate = 14; LightEmission = 0.9 })
		end
		local p = pallor(v, Color3.fromRGB(150, 150, 160), 0.55, 1.6)
		if p then table.insert(run.trash, p) end
	end)
	for _, t in k.Beats.Drink do
		run.at(t, function()
			-- each swallow: the rim pulses, a soft rose ring under the pair
			TweenService:Create(rim, TweenInfo.new(0.08), { OutlineTransparency = 0.05 }):Play()
			task.delay(0.12, function() if rim.Parent then TweenService:Create(rim, TweenInfo.new(0.4), { OutlineTransparency = 0.55 }):Play() end end)
			local p = torsoPos(v)
			if p then Fx.Ring(Vector3.new(p.X, floorY(p, { g, v }), p.Z), C, 5, nil, 0.5) end
			if run.mine then Fx.Shake(0.25, 0.15) end
		end)
	end
	run.at(k.Beats.Release, function()
		if run.batsEmitter then run.batsEmitter.Rate = 0 end
		local c = attachTo(v, `Torso`)
		if c then
			table.insert(run.trash, c)
			burst(c, { Texture = TEX.Bats; Flipbook = `Grid4x4`; FlipMode = `Loop`; Color = Color3.fromRGB(26, 20, 30); Size = 0.7;
				Lifetime = NumberRange.new(0.8, 1.3); Speed = NumberRange.new(10, 16); Spread = 180; LightEmission = 0; LightInfluence = 1 },
				if run.rich then 40 else 26)
		end
	end)
	run.at(k.Beats.Finish, function()
		local p = torsoPos(v)
		if p then Fx.Ring(Vector3.new(p.X, floorY(p, { g, v }), p.Z), A, 10, nil, 0.7) end
	end)
end

Seq.EatBody = function(run)
	local k, g, v = run.k, run.g, run.v
	local C, B = k.Color, k.Accent
	local vt = torsoPos(v) or g:GetPivot().Position
	local fy = floorY(vt, { g, v })
	local ground = Vector3.new(vt.X, fy, vt.Z)
	run.at(k.Beats.Crack, function()
		local cr = floorDisc(ground, tex(`GraveCracks`, TEX.Sigil.Ghoul), if id(TEX.GraveCracks) then Color3.new(1, 1, 1) else Color3.fromRGB(30, 28, 26), 1, 0.05)
		table.insert(run.trash, cr)
		TweenService:Create(cr, TweenInfo.new(0.35, Enum.EasingStyle.Quint), { Size = Vector3.new(10, 0.05, 10) }):Play()
		local glow = floorDisc(ground + Vector3.new(0, 0.02, 0), tex(`GraveCracksGlow`, TEX.Sigil.Ghoul), C, 1, 0.35)
		table.insert(run.trash, glow)
		TweenService:Create(glow, TweenInfo.new(0.5, Enum.EasingStyle.Quint), { Size = Vector3.new(10, 0.05, 10) }):Play()
		local base = part(CFrame.new(ground))
		table.insert(run.trash, base)
		local a = Instance.new(`Attachment`) a.Parent = base
		emitter(a, { Texture = Fx.Tex.Fog; Color = Color3.fromRGB(110, 130, 96); Size = ns({ { 0, 2 }, { 1, 5 } }); Lifetime = NumberRange.new(1.6, 2.4);
			Speed = NumberRange.new(0.6, 1.4); Spread = 80; Direction = Enum.NormalId.Top; Accel = Vector3.new(0, -0.2, 0); Rate = 9;
			Transparency = ns({ { 0, 1 }, { 0.25, 0.7 }, { 0.8, 0.8 }, { 1, 1 } }); LightEmission = 0.1 })
		emitter(a, { Texture = TEX.Spore; Color = C; Size = 0.18; Lifetime = NumberRange.new(1.5, 2.5); Speed = NumberRange.new(0.3, 0.9);
			Spread = 70; Accel = Vector3.new(0, 0.4, 0); Rate = if run.rich then 20 else 12; LightEmission = 0.7 })
		burst(a, { Texture = Fx.Tex.Smoke; Flipbook = `Grid4x4`; Color = Color3.fromRGB(70, 64, 58); Size = 1.4; Lifetime = 0.9;
			Speed = NumberRange.new(3, 6); Spread = 80; Direction = Enum.NormalId.Top; LightEmission = 0 }, 14)
		Fx.Light(ground + Vector3.new(0, 0.5, 0), C, 1.6, 12, 3)
		if run.mine then camPunch(0.4, 3) end
	end)
	-- the cage: bone spikes rise out of the EARTH around the pair (never from the body)
	run.at(k.Beats.Cage, function()
		local spikeSrc = ReplicatedStorage:FindFirstChild(`NHEvolveFX`) and ReplicatedStorage.NHEvolveFX:FindFirstChild(`BoneSpike`)
		local n = if run.sig == `CageTall` then 10 else 8
		local tall = if run.sig == `CageTall` then 1.5 else 1
		for i = 1, n do
			local ang = (i / n) * math.pi * 2 + math.random() * 0.3
			local pos = ground + Vector3.new(math.cos(ang) * 3.4, 0, math.sin(ang) * 3.4)
			local P: BasePart
			if spikeSrc and spikeSrc:IsA(`BasePart`) then
				P = spikeSrc:Clone()
				P.Anchored, P.CanCollide, P.CanQuery, P.CanTouch = true, false, false, false
				P.Size = P.Size * (0.8 + math.random() * 0.4) * tall
				P.Parent = fxFolder()
			else
				P = part(CFrame.new(pos), Vector3.new(0.35, 2.6 * tall, 0.35))
				P.Transparency = 0
				P.Color = B
				P.Material = Enum.Material.SmoothPlastic
			end
			local lean = CFrame.Angles(math.rad(-18 - math.random() * 14), 0, 0)
			local up = CFrame.lookAt(pos, ground) * CFrame.Angles(0, math.pi, 0) * lean
			local h = P.Size.Y
			P.CFrame = up * CFrame.new(0, -h, 0)
			table.insert(run.trash, P)
			task.delay(i * 0.04, function()
				if P.Parent then TweenService:Create(P, TweenInfo.new(0.45, Enum.EasingStyle.Back), { CFrame = up * CFrame.new(0, h * 0.45, 0) }):Play() end
			end)
		end
	end)
	for _, t in k.Beats.Feed do
		run.at(t, function()
			-- dry grave dirt and grit kick up off the FLOOR beside the body (nothing comes off the body itself)
			local p = torsoPos(v)
			if not p then return end
			local b = part(CFrame.new(p.X + (math.random() - 0.5) * 2, fy + 0.1, p.Z + (math.random() - 0.5) * 2))
			table.insert(run.trash, b)
			local a = Instance.new(`Attachment`) a.Parent = b
			burst(a, { Texture = Fx.Tex.Shards; Flipbook = `Grid2x2`; Color = Color3.fromRGB(92, 84, 72); Size = 0.18; Lifetime = 0.6;
				Speed = NumberRange.new(3, 6); Spread = 50; Accel = Vector3.new(0, -25, 0); LightEmission = 0 }, 8)
			burst(a, { Texture = Fx.Tex.Smoke; Flipbook = `Grid4x4`; Color = Color3.fromRGB(80, 74, 66); Size = 0.9; Lifetime = 0.7;
				Speed = NumberRange.new(1, 2.5); Spread = 90; LightEmission = 0 }, 5)
			if run.mine then Fx.Shake(0.3, 0.15) end
		end)
	end
	run.at(1.0, function()
		local p = pallor(v, Color3.fromRGB(120, 140, 110), 0.6, 2)
		if p then table.insert(run.trash, p) end
	end)
	run.at(k.Beats.Crumble, function()
		for _, P in run.trash do
			if typeof(P) == `Instance` and P:IsA(`BasePart`) and P.Name ~= `GripFx` then
				TweenService:Create(P, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { CFrame = P.CFrame * CFrame.new(0, -P.Size.Y, 0) }):Play()
			end
		end
		local b = part(CFrame.new(ground))
		table.insert(run.trash, b)
		local a = Instance.new(`Attachment`) a.Parent = b
		burst(a, { Texture = Fx.Tex.Smoke; Flipbook = `Grid4x4`; Color = B; Size = 1.6; Lifetime = 1.1; Speed = NumberRange.new(2, 5);
			Spread = 90; LightEmission = 0 }, 18)
	end)
end

Seq.Maul = function(run)
	local k, g, v = run.k, run.g, run.v
	local C, A = k.Color, k.Accent
	local eyes = attachTo(g, `Head`, Vector3.new(0, 0.15, -0.5))
	if eyes then table.insert(run.trash, eyes) light(eyes, A, 1.4, 5) end
	local rim = Instance.new(`Highlight`)
	rim.FillTransparency, rim.OutlineColor, rim.OutlineTransparency = 1, A, 0.7
	rim.DepthMode = Enum.HighlightDepthMode.Occluded
	rim.Adornee, rim.Parent = g, g
	table.insert(run.trash, rim)
	run.at(k.Beats.Pounce, function()
		local p = torsoPos(v)
		if not p then return end
		local fy = floorY(p, { g, v })
		local b = part(CFrame.new(p.X, fy, p.Z))
		table.insert(run.trash, b)
		local a = Instance.new(`Attachment`) a.Parent = b
		burst(a, { Texture = Fx.Tex.Smoke; Flipbook = `Grid4x4`; Color = Color3.fromRGB(110, 100, 90); Size = 1.4; Lifetime = 0.8;
			Speed = NumberRange.new(4, 8); Spread = 85; LightEmission = 0 }, 12)
		if run.mine then camPunch(0.6, 4) end
	end)
	for i, t in k.Beats.Swipe do
		run.at(t, function()
			local p = torsoPos(v)
			if not p then return end
			-- three silver rake streaks across the chest, fur tufts and dust; nothing from the body
			local side = if i % 2 == 1 then 1 else -1
			local cf = CFrame.new(p + Vector3.new(0, 1.2, 0)) * CFrame.Angles(0, math.rad(side * 35), math.rad(side * -40))
			local P = part(cf, Vector3.new(4.5, 0.05, 4.5))
			local D = Instance.new(`Decal`)
			D.Texture = tex(`ClawSlash`, TEX.Claws)
			D.Color3 = C
			D.Face = Enum.NormalId.Top
			D.Transparency = 0
			D.Parent = P
			local D2 = D:Clone() D2.Face = Enum.NormalId.Bottom D2.Parent = P
			TweenService:Create(P, TweenInfo.new(0.22, Enum.EasingStyle.Quint), { Size = Vector3.new(5.5, 0.05, 5.5) }):Play()
			fadeOut(P, 0.25)
			local a = Instance.new(`Attachment`) a.Parent = P
			burst(a, { Texture = tex(`SlashSpark`, Fx.Tex.Shards); Flipbook = `Grid2x2`; Color = C; Size = 0.6; Lifetime = 0.25;
				Speed = NumberRange.new(6, 12); Spread = 60; LightEmission = 1 }, 6)
			burst(a, { Texture = TEX.Feather; Flipbook = `Grid4x4`; Color = Color3.fromRGB(96, 84, 74); Size = 0.35;
				Lifetime = NumberRange.new(0.7, 1.2); Speed = NumberRange.new(3, 6); Spread = 120; Accel = Vector3.new(0, -6, 0);
				LightEmission = 0; LightInfluence = 1; RotSpeed = NumberRange.new(-180, 180) }, if run.rich then 10 else 6)
			if run.mine then camPunch(0.5 + i * 0.12, 2 + i) end
		end)
	end
	run.at(k.Beats.Howl, function()
		local gp = g:FindFirstChild(`Head`) :: BasePart?
		if not gp then return end
		-- a pale moon rises behind the wolf, god-rays, a dust shockwave (bigger on a full moon or for an Alpha)
		local back = gp.CFrame * CFrame.new(0, 2.5, 3.5)
		local bb = Instance.new(`BillboardGui`)
		bb.Size = UDim2.fromScale(7, 7)
		bb.LightInfluence = 0
		bb.AlwaysOnTop = false
		local img = Instance.new(`ImageLabel`)
		img.BackgroundTransparency = 1
		img.Size = UDim2.fromScale(1, 1)
		img.Image = tex(`MoonHalo`, TEX.Godray)
		img.ImageColor3 = if id(TEX.MoonHalo) then Color3.new(1, 1, 1) else Color3.fromRGB(226, 232, 245)
		img.ImageTransparency = 1
		img.Parent = bb
		local P = part(back)
		bb.Adornee = P
		bb.Parent = P
		table.insert(run.trash, P)
		TweenService:Create(img, TweenInfo.new(0.5, Enum.EasingStyle.Quint), { ImageTransparency = 0.15 }):Play()
		TweenService:Create(P, TweenInfo.new(0.7, Enum.EasingStyle.Quint), { CFrame = back * CFrame.new(0, 1, 0) }):Play()
		local fullMoon = false
		pcall(function() fullMoon = require(ReplicatedStorage.Lineage).IsFullMoon() end)
		local ringSize = if fullMoon or run.sig == `DoubleShock` then 18 else 13
		local fp = g:GetPivot().Position
		local gy = floorY(fp, { g, v })
		Fx.Ring(Vector3.new(fp.X, gy, fp.Z), Color3.fromRGB(207, 200, 186), ringSize, nil, 0.6)
		if run.sig == `DoubleShock` then
			task.delay(0.22, function() Fx.Ring(Vector3.new(fp.X, gy, fp.Z), Color3.fromRGB(226, 232, 245), ringSize + 6, nil, 0.7) end)
			sound(`DoubleShock`, gp)
		end
		local b = part(CFrame.new(fp.X, gy, fp.Z))
		table.insert(run.trash, b)
		local a = Instance.new(`Attachment`) a.Parent = b
		burst(a, { Texture = Fx.Tex.Smoke; Flipbook = `Grid4x4`; Color = Color3.fromRGB(150, 140, 126); Size = 1.8; Lifetime = 1.0;
			Speed = NumberRange.new(8, 14); Spread = 88; Direction = Enum.NormalId.Top; Drag = 4; LightEmission = 0 }, 22)
		if run.mine then camPunch(0.9, 5) end
	end)
end

Seq.SoulSiphon = function(run)
	local k, g, v = run.k, run.g, run.v
	local C = k.Color
	local vt = torsoPos(v) or g:GetPivot().Position
	local fy = floorY(vt, { g, v })
	local frost = floorDisc(Vector3.new(vt.X, fy, vt.Z), tex(`FrostFloor`, TEX.Frost), Color3.fromRGB(191, 230, 255), 1, 0.15)
	table.insert(run.trash, frost)
	TweenService:Create(frost, TweenInfo.new(1.2, Enum.EasingStyle.Sine), { Size = Vector3.new(11, 0.05, 11) }):Play()
	local cold = Instance.new(`ColorCorrectionEffect`)
	cold.Name = `NHGripCold`
	cold.Parent = Lighting
	if run.near then TweenService:Create(cold, TweenInfo.new(1.0), { Saturation = -0.45, TintColor = Color3.fromRGB(220, 235, 255) }):Play() end
	table.insert(run.trash, cold)
	local soul, soulConn
	run.at(k.Beats.Palm, function()
		local p = torsoPos(v)
		if p then Fx.Ring(Vector3.new(p.X, fy, p.Z), C, 7, nil, 0.45) end
		if run.mine then camPunch(0.35, 2) end
	end)
	run.at(k.Beats.Pull, function()
		if not v then return end
		-- the soul: a translucent copy of the victim drawn up toward the wraith's palm, stretching as it rises
		soul = ghostOf(v, C, Enum.Material.ForceField, 0.35)
		for _, P in soul do table.insert(run.trash, P) end
		local hand = g:FindFirstChild(`Right Arm`) :: BasePart?
		local aHand = attachTo(g, `Right Arm`, Vector3.new(0, -1, 0))
		local aChest = attachTo(v, `Torso`, Vector3.new(0, 0, -0.5))
		if aHand and aChest then
			table.insert(run.trash, aHand) table.insert(run.trash, aChest)
			beam(aChest, aHand, { Texture = tex(`SoulStreak`, Fx.Tex.Wisp); Color = C; Width0 = 1.4; Width1 = 0.4; Speed = -2.2; Length = 2.5 })
			emitter(aHand, { Texture = Fx.Tex.Wisp; Color = C; Size = 0.4; Lifetime = 0.7; Speed = NumberRange.new(0.5, 1.2); Rate = 18; LightEmission = 1 })
			light(aHand, C, 1.6, 9)
		end
		local t0 = os.clock()
		soulConn = RunService.RenderStepped:Connect(function()
			local K = math.clamp((os.clock() - t0) / (k.Beats.Yank - k.Beats.Pull), 0, 1)
			local top = hand and (hand.CFrame * CFrame.new(0, -1, 0)).Position
			for src, P in soul do
				if src.Parent and top then
					local lift = K * K * (3 - 2 * K)
					local cf = src.CFrame
					P.CFrame = cf:Lerp(CFrame.new(top) * cf.Rotation, lift * 0.55) * CFrame.new(0, math.sin(os.clock() * 9 + src.Size.X) * 0.05, 0)
				end
			end
		end)
		table.insert(run.conns, soulConn)
	end)
	run.at(k.Beats.Yank, function()
		if soulConn then soulConn:Disconnect() end
		-- torn free: the soul spirals into the fist, then the chest
		local hand = g:FindFirstChild(`Right Arm`) :: BasePart?
		if soul and hand then
			for src, P in soul do
				local goal = (hand.CFrame * CFrame.new(0, -1, 0)).Position
				TweenService:Create(P, TweenInfo.new(0.3, Enum.EasingStyle.Quint, Enum.EasingDirection.In),
					{ CFrame = CFrame.new(goal) * CFrame.Angles(0, math.random() * 6, 0), Size = P.Size * 0.15, Transparency = 0.9 }):Play()
			end
		end
		Fx.Flash(Color3.fromRGB(220, 238, 255), 0.18, 0.25)
		if run.mine then camPunch(0.8, 5) end
	end)
	run.at(k.Beats.Absorb, function()
		local gt = torsoPos(g)
		if gt then Fx.Light(gt, C, 2, 12, 0.7) end
		if run.sig == `FrostCrown` then
			local h = g:FindFirstChild(`Head`) :: BasePart?
			if h then
				local a = attachTo(g, `Head`, Vector3.new(0, 0.9, 0))
				if a then
					table.insert(run.trash, a)
					burst(a, { Texture = TEX.Frost; Flipbook = `Grid2x2`; Color = Color3.fromRGB(200, 236, 255); Size = 0.5; Lifetime = 1.2;
						Speed = NumberRange.new(0.5, 1.5); Spread = 30; LightEmission = 0.8 }, 16)
					sound(`FrostCrown`, h)
				end
			end
		end
	end)
	run.at(k.Beats.Finish, function()
		local b = part(CFrame.new(vt.X, fy, vt.Z))
		table.insert(run.trash, b)
		local a = Instance.new(`Attachment`) a.Parent = b
		burst(a, { Texture = TEX.Frost; Flipbook = `Grid2x2`; Color = Color3.fromRGB(200, 236, 255); Size = 0.5; Lifetime = 0.8;
			Speed = NumberRange.new(6, 11); Spread = 80; Accel = Vector3.new(0, -14, 0); LightEmission = 0.5 }, 26)
		Fx.Ring(Vector3.new(vt.X, fy, vt.Z), C, 12, nil, 0.6)
		TweenService:Create(cold, TweenInfo.new(0.6), { Saturation = 0, TintColor = Color3.new(1, 1, 1) }):Play()
	end)
end

Seq.Exorcise = function(run)
	local k, g, v = run.k, run.g, run.v
	local C, Ink = k.Color, k.Accent
	local vt = torsoPos(v) or g:GetPivot().Position
	local fy = floorY(vt, { g, v })
	local ground = Vector3.new(vt.X, fy, vt.Z)
	local seal, column, possession
	run.at(k.Beats.Seal, function()
		seal = floorDisc(ground, tex(`PriestRunes`, TEX.Sigil.Priest), C, 1, 0.2)
		table.insert(run.trash, seal)
		TweenService:Create(seal, TweenInfo.new(0.6, Enum.EasingStyle.Quint), { Size = Vector3.new(if run.rich then 12 else 10, 0.05, if run.rich then 12 else 10) }):Play()
		local spin = RunService.RenderStepped:Connect(function(dt) if seal.Parent then seal.CFrame *= CFrame.Angles(0, dt * 0.35, 0) end end)
		table.insert(run.conns, spin)
		Fx.Light(ground + Vector3.new(0, 1, 0), C, 1.5, 12, k.Length - k.Beats.Seal)
	end)
	run.at(k.Beats.Cross, function()
		-- the gilded cross and halo over the raised hand, a god-ray column from above with gold dust in it
		local hand = g:FindFirstChild(`Right Arm`) :: BasePart?
		local evo = ReplicatedStorage:FindFirstChild(`NHEvolveFX`)
		local cross = evo and evo:FindFirstChild(`GildedCross`)
		if hand then
			local at = (hand.CFrame * CFrame.new(0, -1.6, 0)).Position
			local P: BasePart
			if cross and cross:IsA(`BasePart`) then
				P = cross:Clone()
				P.Anchored, P.CanCollide, P.CanQuery, P.CanTouch = true, false, false, false
				P.Size = P.Size * (0.9 / math.max(P.Size.Y, 0.1)) * (if run.sig == `TwinBell` then 1.4 else 1.1)
				P.Parent = fxFolder()
			else
				P = part(CFrame.new(at), Vector3.new(0.15, 1.1, 0.15))
				P.Transparency = 0
				P.Material = Enum.Material.Neon
				P.Color = C
			end
			P.CFrame = CFrame.new(at)
			table.insert(run.trash, P)
			local follow = RunService.RenderStepped:Connect(function()
				if hand.Parent and P.Parent then P.CFrame = CFrame.new((hand.CFrame * CFrame.new(0, -1.7, 0)).Position) * CFrame.Angles(0, os.clock() * 0.6, 0) end
			end)
			table.insert(run.conns, follow)
			local a = Instance.new(`Attachment`) a.Parent = P
			emitter(a, { Texture = tex(`GoldDust`, Fx.Tex.Ember); Flipbook = if id(TEX.GoldDust) then `Grid2x2` else nil; Color = C; Size = 0.2;
				Lifetime = NumberRange.new(0.8, 1.4); Speed = NumberRange.new(0.3, 1); Spread = 180; Rate = 16; LightEmission = 1 })
			light(a, C, 1.4, 8)
		end
		column = part(CFrame.new(ground + Vector3.new(0, 7, 0)), Vector3.new(0.2, 0.2, 0.2))
		table.insert(run.trash, column)
		local a0 = Instance.new(`Attachment`) a0.Position = Vector3.new(0, 7, 0) a0.Parent = column
		local a1 = Instance.new(`Attachment`) a1.Position = Vector3.new(0, -7, 0) a1.Parent = column
		beam(a0, a1, { Texture = TEX.Godray; Color = C; Width0 = 2.5; Width1 = if run.rich then 7 else 5.5; Speed = 0.4; Length = 14;
			Transparency = ns({ { 0, 1 }, { 0.3, 0.6 }, { 1, 0.75 } }) })
		local ad = Instance.new(`Attachment`) ad.Parent = column
		emitter(ad, { Texture = tex(`GoldDust`, Fx.Tex.Ember); Flipbook = if id(TEX.GoldDust) then `Grid2x2` else nil; Color = C; Size = 0.15;
			Lifetime = NumberRange.new(2, 3); Speed = NumberRange.new(1, 2); Spread = 30; Direction = Enum.NormalId.Bottom; Rate = 12; LightEmission = 1 })
		-- the possession fights back: ink smoke boils off and dark tendrils claw at the light
		local va = attachTo(v, `Torso`)
		if va then
			table.insert(run.trash, va)
			possession = emitter(va, { Texture = tex(`InkSmoke`, Fx.Tex.Smoke); Flipbook = `Grid4x4`; Color = if id(TEX.InkSmoke) then Color3.new(1, 1, 1) else Ink; Size = ns({ { 0, 1 }, { 1, 2.6 } });
				Lifetime = NumberRange.new(0.8, 1.3); Speed = NumberRange.new(1, 2.5); Spread = 50; Rate = 18; LightEmission = 0; LightInfluence = 1;
				Transparency = ns({ { 0, 1 }, { 0.15, 0.2 }, { 0.8, 0.5 }, { 1, 1 } }) })
			local tp = attachTo(v, `Head`)
			local tq = attachTo(g, `Left Arm`, Vector3.new(0, -0.6, 0))
			if tp and tq and id(TEX.InkTendril) then
				table.insert(run.trash, tp) table.insert(run.trash, tq)
				beam(tp, tq, { Texture = TEX.InkTendril; Color = Color3.new(1, 1, 1); Width0 = 0.8; Width1 = 0.2; Speed = 3; Length = 1.5;
					Curve0 = 1.2; Curve1 = -0.8; LightEmission = 0; Transparency = ns({ { 0, 0.2 }, { 1, 0.6 } }) })
			end
		end
	end)
	for _, t in k.Beats.Spasm do
		run.at(t, function()
			local va = attachTo(v, `Torso`)
			if va then
				table.insert(run.trash, va)
				burst(va, { Texture = tex(`InkSmoke`, Fx.Tex.Smoke); Flipbook = `Grid4x4`; Color = if id(TEX.InkSmoke) then Color3.new(1, 1, 1) else Ink; Size = 1.6; Lifetime = 0.7;
					Speed = NumberRange.new(3, 6); Spread = 70; LightEmission = 0; LightInfluence = 1 }, 8)
			end
			if run.mine then Fx.Shake(0.4, 0.2) end
		end)
	end
	run.at(k.Beats.Strike, function()
		if possession then possession.Enabled = false end
		-- the demon is torn up out of the body and burns away into embers; a white-gold flash, a shockwave, the bell
		local p = torsoPos(v)
		if p then
			local cf = CFrame.new(p + Vector3.new(0, 1.5, 0))
			local P = part(cf)
			table.insert(run.trash, P)
			local bb = Instance.new(`BillboardGui`)
			bb.Size = UDim2.fromScale(6, 6)
			bb.LightInfluence = 0
			bb.Adornee = P
			bb.Parent = P
			local img = Instance.new(`ImageLabel`)
			img.BackgroundTransparency = 1
			img.Size = UDim2.fromScale(1, 1)
			img.Image = tex(`DemonShape`, Fx.Tex.Smoke)
			img.ImageColor3 = if id(TEX.DemonShape) then Color3.new(1, 1, 1) else Color3.fromRGB(10, 8, 14)
			img.ImageTransparency = 0.05
			img.Parent = bb
			TweenService:Create(P, TweenInfo.new(0.7, Enum.EasingStyle.Quint), { CFrame = cf * CFrame.new(0, 5, 0) }):Play()
			TweenService:Create(img, TweenInfo.new(0.7, Enum.EasingStyle.Sine), { ImageTransparency = 1 }):Play()
			local a = Instance.new(`Attachment`) a.Parent = P
			burst(a, { Texture = Fx.Tex.Ember; Color = Color3.fromRGB(255, 196, 110); Size = 0.25; Lifetime = NumberRange.new(0.6, 1.2);
				Speed = NumberRange.new(3, 8); Spread = 60; Accel = Vector3.new(0, 4, 0); LightEmission = 1 }, if run.rich then 50 else 34)
			Fx.Ring(Vector3.new(p.X, fy, p.Z), C, if run.rich then 18 else 14, nil, 0.6)
			if Fx.Near(p, 50) then Fx.Flash(Color3.fromRGB(255, 246, 220), 0.35, 0.45) end
			Fx.Light(p, Color3.fromRGB(255, 240, 210), 2, 12, 0.6)
			if run.sig == `TwinBell` then sound(`TwinBell`, P) end
		end
		if run.mine then camPunch(1, 6) end
	end)
end

Seq.Stake = function(run)
	local k, g, v = run.k, run.g, run.v
	local C, Ash = k.Color, k.Accent
	local stake
	run.at(k.Beats.Knee, function()
		local p = torsoPos(v)
		if p then
			local fy = floorY(p, { g, v })
			local b = part(CFrame.new(p.X, fy, p.Z))
			table.insert(run.trash, b)
			local a = Instance.new(`Attachment`) a.Parent = b
			burst(a, { Texture = Fx.Tex.Smoke; Flipbook = `Grid4x4`; Color = Color3.fromRGB(120, 112, 100); Size = 1.1; Lifetime = 0.7;
				Speed = NumberRange.new(3, 6); Spread = 85; LightEmission = 0 }, 10)
		end
		if run.mine then camPunch(0.45, 3) end
	end)
	run.at(k.Beats.Stake, function()
		-- the stake: a dark wooden spike in the right hand with a silver-bound grip and a glint
		local hand = g:FindFirstChild(`Right Arm`) :: BasePart?
		if not hand then return end
		local m = Instance.new(`Model`)
		m.Name = `GripStake`
		local shaft = part(hand.CFrame, Vector3.new(0.22, 1.7, 0.22))
		shaft.Transparency, shaft.Color, shaft.Material = 0, Color3.fromRGB(70, 48, 32), Enum.Material.Wood
		shaft.Parent = m
		local tip = Instance.new(`WedgePart`)
		tip.Anchored, tip.CanCollide, tip.CanQuery, tip.CanTouch, tip.CastShadow = true, false, false, false, false
		tip.Size = Vector3.new(0.22, 0.45, 0.22)
		tip.Color, tip.Material = Color3.fromRGB(78, 54, 36), Enum.Material.Wood
		tip.Parent = m
		local band = part(hand.CFrame, Vector3.new(0.26, 0.18, 0.26))
		band.Transparency, band.Color, band.Material = 0, Color3.fromRGB(200, 206, 214), Enum.Material.Metal
		band.Parent = m
		m.Parent = fxFolder()
		table.insert(run.trash, m)
		local conn = RunService.RenderStepped:Connect(function()
			if not hand.Parent then return end
			local base = hand.CFrame * CFrame.new(0, -1.05, 0) * CFrame.Angles(math.rad(-90), 0, 0) -- held in the fist, point forward/down the arm
			shaft.CFrame = base * CFrame.new(0, -0.45, 0)
			band.CFrame = base * CFrame.new(0, 0.2, 0)
			tip.CFrame = base * CFrame.new(0, -1.52, 0) * CFrame.Angles(math.pi, 0, 0)
		end)
		table.insert(run.conns, conn)
		stake = band
		local a = Instance.new(`Attachment`) a.Parent = band
		burst(a, { Texture = tex(`SlashSpark`, Fx.Tex.Shards); Flipbook = `Grid2x2`; Color = C; Size = 0.7; Lifetime = 0.3; Speed = 0.5;
			Spread = 10; LightEmission = 1 }, 2)
		Fx.Light(band.Position, C, 1.2, 6, 0.5)
		local p = torsoPos(g)
		if p then
			local d = floorDisc(Vector3.new(p.X, floorY(p, { g, v }), p.Z), TEX.Sigil.Human, C, 1, 0.45)
			table.insert(run.trash, d)
			TweenService:Create(d, TweenInfo.new(0.4, Enum.EasingStyle.Quint), { Size = Vector3.new(6, 0.05, 6) }):Play()
			task.delay(0.6, function() fadeOut(d, 0.5) end)
		end
	end)
	run.at(k.Beats.Raise, function()
		if stake then
			local a = Instance.new(`Attachment`) a.Parent = stake
			burst(a, { Texture = tex(`SlashSpark`, Fx.Tex.Shards); Flipbook = `Grid2x2`; Color = C; Size = 0.9; Lifetime = 0.3; Speed = 0.3;
				Spread = 10; LightEmission = 1 }, 2)
		end
	end)
	run.at(k.Beats.Strike, function()
		local p = torsoPos(v)
		if not p then return end
		local fy = floorY(p, { g, v })
		local b = part(CFrame.new(p.X, fy, p.Z))
		table.insert(run.trash, b)
		local a = Instance.new(`Attachment`) a.Parent = b
		burst(a, { Texture = Fx.Tex.Smoke; Flipbook = `Grid4x4`; Color = Color3.fromRGB(150, 140, 126); Size = 1.6; Lifetime = 0.9;
			Speed = NumberRange.new(5, 10); Spread = 88; Drag = 3; LightEmission = 0 }, 18)
		Fx.Ring(Vector3.new(p.X, fy, p.Z), C, if run.sig == `Crater` then 14 else 9, nil, 0.45)
		if run.sig == `Crater` then
			local cr = floorDisc(Vector3.new(p.X, fy, p.Z), tex(`GraveCracks`, TEX.Sigil.Human), if id(TEX.GraveCracks) then Color3.new(1, 1, 1) else Color3.fromRGB(40, 38, 36), 6, 0.1)
			table.insert(run.trash, cr)
			sound(`Crater`, b)
		end
		if run.monster then
			-- no wound: the monster's body flashes pale and grey ash lifts off it and drifts away
			local p2 = pallor(v, Color3.fromRGB(220, 216, 208), 0.25, 0.25)
			if p2 then table.insert(run.trash, p2) end
			local va = attachTo(v, `Torso`)
			if va then
				table.insert(run.trash, va)
				emitter(va, { Texture = tex(`Ash`, Fx.Tex.Smoke); Flipbook = `Grid4x4`; Color = Ash; Size = ns({ { 0, 0.5 }, { 1, 1.2 } });
					Lifetime = NumberRange.new(1.2, 2); Speed = NumberRange.new(0.5, 1.5); Spread = 60; Accel = Vector3.new(0, 1.5, 0);
					Rate = 26; LightEmission = 0; LightInfluence = 1 })
			end
			sound(`StakeAsh`, v and v:FindFirstChild(`Torso`))
		end
		if run.mine then camPunch(1, 6) end
	end)
end

---| runner |---

local Active: { [Model]: any } = {}

local function stop(run, fade: number)
	if run.done then return end
	run.done = true
	for _, c in run.conns do pcall(function() c:Disconnect() end) end
	for _, th in run.threads do pcall(task.cancel, th) end
	for _, x in run.trash do
		if typeof(x) == `Instance` and x.Parent then
			if x:IsA(`Highlight`) then
				TweenService:Create(x, TweenInfo.new(fade), { FillTransparency = 1, OutlineTransparency = 1 }):Play()
				Debris:AddItem(x, fade + 0.1)
			elseif x:IsA(`ColorCorrectionEffect`) then
				TweenService:Create(x, TweenInfo.new(fade), { Saturation = 0, Brightness = 0, Contrast = 0, TintColor = Color3.new(1, 1, 1) }):Play()
				Debris:AddItem(x, fade + 0.1)
			elseif x:IsA(`Sound`) then
				TweenService:Create(x, TweenInfo.new(fade), { Volume = 0 }):Play()
				Debris:AddItem(x, fade + 0.1)
			elseif x:IsA(`Attachment`) then
				fadeOut(x, fade)
				Debris:AddItem(x, fade + 1.5)
			else
				fadeOut(x, fade)
			end
		end
	end
	if Active[run.g] == run then Active[run.g] = nil end
end

-- Data: { Kind, To = gripper Model, Victim = Model?, Until = server time the grip ends, Sub = sub-race id?, VictimRace = race id? }
function Shared.Play(Data): boolean
	local k = Cfg.Kinds[Data.Kind]
	local g = Data.To
	if not k or not Seq[Data.Kind] or typeof(g) ~= `Instance` then return false end
	local v = Data.Victim
	if Active[g] then stop(Active[g], 0.2) end
	local gp = g:GetPivot().Position
	if not Fx.Near(gp, 150) then return true end
	local now = workspace:GetServerTimeNow()
	local t0 = (Data.Until or (now + k.Length)) - k.Length
	local run = {
		k = k; g = g; v = v; t0 = t0; trash = {}; conns = {}; threads = {}; done = false;
		rich = Cfg.Rich[Data.Sub or ``] == true; sig = Cfg.Signature[Data.Sub or ``];
		mine = g == Player.Character; victimMe = v ~= nil and v == Player.Character;
		near = Fx.Near(gp, 40);
		monster = Data.VictimRace ~= nil and Data.VictimRace ~= `Human` and Data.VictimRace ~= `Priest`;
	}
	function run.at(t: number, fn)
		local wait = (t0 + t) - workspace:GetServerTimeNow()
		local th = task.delay(math.max(0, wait), function()
			if run.done then return end
			local ok, err = pcall(fn)
			if not ok then warn(`[RaceGripFx] {Data.Kind} beat {t}: {err}`) end
		end)
		table.insert(run.threads, th)
	end
	Active[g] = run
	-- the race's own sound cue, aligned to the clip start; the sub-race extra on its beat
	local vt = v and v:FindFirstChild(`Torso`) or g:FindFirstChild(`Torso`)
	local cue = sound(Data.Kind, vt)
	if cue then
		cue.TimePosition = math.max(0, now - t0)
		table.insert(run.trash, cue)
	end
	if run.victimMe then victimScreen(run, k.Length) end
	if run.mine and not Fx.Reduced() then
		local Cam = workspace.CurrentCamera
		if Cam then
			local f0 = Cam.FieldOfView
			TweenService:Create(Cam, TweenInfo.new(k.Length * 0.6, Enum.EasingStyle.Sine), { FieldOfView = f0 - 6 }):Play()
			run.at(k.Length, function() TweenService:Create(Cam, TweenInfo.new(0.6, Enum.EasingStyle.Sine), { FieldOfView = f0 }):Play() end)
		end
		run.at(k.Beats.Finish, function() sound(`FinishSting`, workspace.CurrentCamera, 0.7) end)
	end
	local ok, err = pcall(Seq[Data.Kind], run)
	if not ok then warn(`[RaceGripFx] {Data.Kind}: {err}`) end
	-- stop when the grip ends or is cancelled (GripEndsAt cleared or replaced)
	local untilAt = Data.Until
	table.insert(run.conns, g:GetAttributeChangedSignal(`GripEndsAt`):Connect(function()
		if g:GetAttribute(`GripEndsAt`) ~= untilAt then stop(run, 0.35) end
	end))
	run.at(k.Length + 0.6, function() stop(run, 0.8) end)
	return true
end

function Shared.Handles(Kind: string?): boolean
	return Kind ~= nil and Seq[Kind] ~= nil and Cfg.Kinds[Kind] ~= nil
end

function Shared.Init(FxModule)
	Fx = FxModule
end

return Shared
