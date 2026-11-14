--[[
	The Hellhound's fire (ModuleScript, ReplicatedStorage.Beasts.HellhoundFX)   (beasts kit; design: docs/superpowers/specs/2026-11-05-beasts-design.md)

	HellhoundFX.Apply(model) dresses a Hellhound (the wolf rig scaled up, ServerStorage.NHBeasts.Hellhound) in fire, on its
	bones so it all moves with the animations:
	  - a fire mane down the neck and back (none on the head), smoke rising off it, embers drifting up;
	  - a burning tail;
	  - flames licking at every paw;
	  - burning eyes (the only fire on the head), a faint glow from the throat and a heat glow in its body
	    (no outline: the owner ruled it out).
	The fire is the game's own: the burning status's two flame emitters (ReplicatedStorage.Assets.Effects.Status.FlameStatus),
	cloned and scaled per bone; the sparks are the guard break's, the smoke uses the down-smoke's texture.
	HellhoundFX.Breath(model, on) turns its fire-breath jet (from the snout) on or off. Every emitter is named HoundFX_*,
	so Apply can run again.
]]
local HellhoundFX = {}

local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local Effects = ReplicatedStorage:WaitForChild(`Assets`):WaitForChild(`Effects`)
local FIRE = `rbxassetid://13209151224`          -- the burning status's flame
local SMOKE = `rbxassetid://8527116276`          -- the down-smoke
local SPARK = `rbxassetid://8114157061`          -- the guard break's sparks

local HOT = ColorSequence.new({
	ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 236, 160)),
	ColorSequenceKeypoint.new(0.35, Color3.fromRGB(255, 132, 34)),
	ColorSequenceKeypoint.new(0.75, Color3.fromRGB(210, 46, 12)),
	ColorSequenceKeypoint.new(1, Color3.fromRGB(70, 12, 6)),
})

local function seq(a, b, c)
	if c then return NumberSequence.new({ NumberSequenceKeypoint.new(0, a), NumberSequenceKeypoint.new(0.5, b), NumberSequenceKeypoint.new(1, c) }) end
	return NumberSequence.new({ NumberSequenceKeypoint.new(0, a), NumberSequenceKeypoint.new(1, b) })
end

local function emitter(parent: Instance, name: string, props)
	local old = parent:FindFirstChild(`HoundFX_{name}`)
	if old then old:Destroy() end
	local e = Instance.new(`ParticleEmitter`)
	e.Name = `HoundFX_{name}`
	for k, v in props do e[k] = v end
	e.Parent = parent
	return e
end

local function scaled(ns: NumberSequence, k: number): NumberSequence
	local out = {}
	for _, p in ns.Keypoints do table.insert(out, NumberSequenceKeypoint.new(p.Time, p.Value * k, p.Envelope * k)) end
	return NumberSequence.new(out)
end

-- the burning status's two flame emitters, cloned onto a bone, scaled by `size` (1 = a burning student) at `rate` x their own.
-- Dimmed (the flame core to half, the soft glow to a quarter): a whole body of them at full brightness blows out under the
-- game's night bloom.
local DIM = { 0.5, 0.25 }
local function flames(parent, name, size, rate, rise)
	local src = Effects:FindFirstChild(`Status`) and Effects.Status:FindFirstChild(`FlameStatus`)
	local k = 0
	for _, e in (src and src:GetChildren()) or {} do
		if e:IsA(`ParticleEmitter`) then
			k += 1
			local old = parent:FindFirstChild(`HoundFX_{name}{k}`)
			if old then old:Destroy() end
			local c = e:Clone()
			c.Name = `HoundFX_{name}{k}`
			c.Size = scaled(e.Size, size)
			c.Acceleration = e.Acceleration * math.sqrt(size) * (rise or 1)
			c.Rate = e.Rate * rate
			c.Brightness = e.Brightness * (DIM[k] or 0.5)
			c.Enabled = true
			c.Parent = parent
		end
	end
end

local function light(parent, name, color, range, brightness)
	local old = parent:FindFirstChild(`HoundFX_{name}`)
	if old then old:Destroy() end
	local l = Instance.new(`PointLight`)
	l.Name = `HoundFX_{name}`
	l.Color, l.Range, l.Brightness, l.Shadows = color, range, brightness, false
	l.Parent = parent
	return l
end

function HellhoundFX.Apply(model: Model)
	local function bone(n) return model:FindFirstChild(n, true) end
	-- the fire mane: one continuous run of flame along the back, rising off the skin, biggest at the neck. Six points (on
	-- each spine bone and halfway to the next), each an Attachment under its bone so it moves with the animations.
	-- Placed with the hound upright at rest (templates are built that way); `lift` is the skin's height over the spine.
	local SPINE = { `upperspine`, `middlespine`, `lowerspine`, `tailstart` }
	local MANE = { -- { bone index, fraction to the next bone, lift, size }
		{ 1, 0.0, 1.0, 1.35 }; { 1, 0.5, 1.05, 1.3 }; { 2, 0.0, 0.75, 1.2 }; { 2, 0.5, 0.62, 1.1 }; { 3, 0.0, 0.48, 1.0 }; { 3, 0.5, 0.34, 0.9 };
	}
	for i, m in MANE do
		local b, nxt = bone(SPINE[m[1]]), bone(SPINE[m[1] + 1])
		if b and nxt then
			local pt = b:FindFirstChild(`HoundFX_ManePt{i}`) or Instance.new(`Attachment`)
			pt.Name = `HoundFX_ManePt{i}`
			pt.Parent = b
			pt.WorldPosition = b.WorldPosition:Lerp(nxt.WorldPosition, m[2]) + Vector3.new(0, m[3] * 0.85, 0)
			flames(pt, `Mane`, m[4], 0.75, 0.7)
		end
	end
	-- smoke and embers rising off it (no fire on the head: the owner ruled it out)
	for _, n in { `upperspine`, `middlespine`, `lowerspine` } do
		local b = bone(n)
		if b then
			local old = b:FindFirstChild(`HoundFX_Mane1`) if old then old:Destroy() end   -- the old one-per-bone mane
			old = b:FindFirstChild(`HoundFX_Mane2`) if old then old:Destroy() end
			emitter(b, `Embers`, {
				Texture = SPARK; Color = HOT; LightEmission = 1; LightInfluence = 0; Size = seq(0.14, 0.02);
				Lifetime = NumberRange.new(1.0, 1.8); Rate = 8; Speed = NumberRange.new(1.5, 3.5); SpreadAngle = Vector2.new(60, 60);
				Acceleration = Vector3.new(0, 2.5, 0); Drag = 0.6;
			})
			if n ~= `lowerspine` then
				emitter(b, `Smoke`, {
					Texture = SMOKE; Color = ColorSequence.new(Color3.fromRGB(40, 30, 28), Color3.fromRGB(18, 14, 14)); LightInfluence = 0.4;
					Size = seq(1.2, 3.2); Transparency = seq(0.72, 0.85, 1); Lifetime = NumberRange.new(1.4, 2.4); Rate = 4;
					Speed = NumberRange.new(0.5, 1.2); SpreadAngle = Vector2.new(25, 25); Acceleration = Vector3.new(0, 3.5, 0);
					Rotation = NumberRange.new(-180, 180); RotSpeed = NumberRange.new(-25, 25);
				})
			end
		end
	end
	-- the burning tail
	for n, s in { middletail = 0.95; tailend = 1.35 } do
		local b = bone(n)
		if b then flames(b, `Tail`, s, 1.1, 0.75) end
	end
	-- flames at the paws
	for _, n in { `l.frontpaw`, `r.frontpaw`, `l.lowerpaw`, `r.lowerpaw` } do
		local b = bone(n)
		if b then
			flames(b, `Paw`, 0.8, 0.7)
			light(b, `PawGlow`, Color3.fromRGB(255, 96, 30), 5, 0.6)
		end
	end
	-- the eyes burn: a steady ember core and a small flicker of the game's flame (the only fire on the head)
	for _, n in { `l.eye`, `r.eye` } do
		local b = bone(n)
		if b then
			emitter(b, `EyeCore`, {
				Texture = FIRE; Color = HOT; LightEmission = 1; LightInfluence = 0; Size = seq(0.34, 0.26, 0.0);
				Transparency = seq(0.0, 0.15, 1); Lifetime = NumberRange.new(0.12, 0.2); Rate = 40; Speed = NumberRange.new(0, 0);
				LockedToPart = true; Rotation = NumberRange.new(-180, 180); RotSpeed = NumberRange.new(-120, 120); ZOffset = 0.6;
			})
			flames(b, `Eye`, 0.22, 0.6)
			light(b, `EyeGlow`, Color3.fromRGB(255, 110, 30), 3, 1.6)
		end
	end
	-- a faint glow from the throat
	local jaw = bone(`jaw`)
	if jaw then light(jaw, `Throat`, Color3.fromRGB(255, 92, 24), 7, 1.2) end
	-- a heat glow from the body (no outline: any old rim Highlight is removed)
	local mid = bone(`middlespine`)
	if mid then light(mid, `Heat`, Color3.fromRGB(255, 104, 34), 14, 1.4) end
	local hl = model:FindFirstChild(`HoundFX_Rim`)
	if hl then hl:Destroy() end
	-- the fire breath, built in and off: a point at the tip of the snout aimed out of the face (the snout bone itself
	-- points down), under the snout bone so the jet follows the head. Breath() switches it.
	local snout, head = bone(`snout`), bone(`head`)
	if snout and head then
		local fwd = (snout.WorldPosition - head.WorldPosition) * Vector3.new(1, 0, 1)
		fwd = if fwd.Magnitude > 0.01 then fwd.Unit else model:GetPivot().LookVector
		local pt = snout:FindFirstChild(`HoundFX_BreathPt`) or Instance.new(`Attachment`)
		pt.Name = `HoundFX_BreathPt`
		pt.Parent = snout
		local at = snout.WorldPosition + fwd * 0.5
		pt.WorldCFrame = CFrame.lookAt(at, at + fwd)
		local old = snout:FindFirstChild(`HoundFX_Breath`) if old then old:Destroy() end
		emitter(pt, `Breath`, {
			Texture = FIRE; Color = HOT; LightEmission = 1; LightInfluence = 0; Brightness = 1.6; Size = seq(0.5, 2.4, 3.4);
			Transparency = seq(0.05, 0.35, 1); Lifetime = NumberRange.new(0.42, 0.55); Rate = 120; Speed = NumberRange.new(26, 32);
			SpreadAngle = Vector2.new(12, 12); EmissionDirection = Enum.NormalId.Front; Drag = 1.6; Rotation = NumberRange.new(-180, 180);
			RotSpeed = NumberRange.new(-200, 200); Acceleration = Vector3.new(0, 4, 0); Enabled = false;
		})
	end
end

-- the fire-breath jet on or off (FireBreath move: about 14 studs of flame in a narrow cone)
function HellhoundFX.Breath(model: Model, on: boolean)
	local pt = model:FindFirstChild(`HoundFX_BreathPt`, true)
	local e = pt and pt:FindFirstChild(`HoundFX_Breath`)
	if e then e.Enabled = on end
end

return HellhoundFX
