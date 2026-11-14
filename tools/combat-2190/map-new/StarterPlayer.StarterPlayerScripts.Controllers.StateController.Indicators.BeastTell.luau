--[[
	BeastTell (client indicator, StarterPlayerScripts.Controllers.StateController.Indicators.BeastTell)
	A beast's special-attack warning: the game's critical-attack Kanji (ReplicatedStorage.Assets.Effects.CombatFX.Heavy, the
	same one students see before a critical) over the beast's head, with the critical glow and ring and the Critical sound.
	  * Only special attacks get it (the Hellhound's Pounce and FireBreath, and each beast's unique moves). Normal attacks
	    get no Kanji (owner, 2026-11-05); they come in the beast's fixed, learnable pattern.
	  * Beasts never get an outline (the owner ruled it out).
	The server sends it with
	  Packets.Replicate:Fire(`Indicators`, `BeastTell`, { User = BeastModel })
	It's scaled to the beast's height, so a bat's is small and a gargoyle's is large.
]]
local Debris = game:GetService(`Debris`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local EmitManager = require(ReplicatedStorage.Functions.EmitManager)

local STUDENT_HEIGHT = 5.5
local KEEP = { Kanji = true; Glow = true; Ring = true }

local function scaled(ns: NumberSequence, k: number): NumberSequence
	local out = {}
	for _, p in ns.Keypoints do table.insert(out, NumberSequenceKeypoint.new(p.Time, p.Value * k, p.Envelope * k)) end
	return NumberSequence.new(out)
end

return function(_Character: Model, Paramaters: { User: Model, At: Vector3? })
	local User = Paramaters.User
	if typeof(User) ~= `Instance` or not User:IsA(`Model`) or not User.Parent then return end
	local Root = User:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if not Root then return end

	local BoxCF, BoxSize = User:GetBoundingBox()
	local k = math.clamp(BoxSize.Y / STUDENT_HEIGHT * 1.25, 0.9, 3) * 1.35

	-- over the head (the head bone or part if it has one; a long beast's middle is no good), just clear of the top
	local Head = User:FindFirstChild(`head`, true) or User:FindFirstChild(`Head`, true)
	local HeadPos = if Head and Head:IsA(`Bone`) then Head.TransformedWorldCFrame.Position
		elseif Head and Head:IsA(`BasePart`) then Head.Position
		else Root.Position
	local Top = BoxCF.Position.Y + BoxSize.Y / 2 + 0.6 * k
	-- At (optional): a world spot to show it over instead, e.g. a buried ghoul's grave
	local Where = if typeof(Paramaters.At) == `Vector3` then Paramaters.At else Vector3.new(HeadPos.X, Top, HeadPos.Z)
	local At = Root.CFrame:PointToObjectSpace(Where)

	local Fx = ReplicatedStorage.Assets.Effects.CombatFX.Heavy:Clone()
	local Point = Fx:FindFirstChildOfClass(`Attachment`)
	for _, E in Fx:GetDescendants() do
		if E:IsA(`ParticleEmitter`) then
			if KEEP[E.Name] then E.Size = scaled(E.Size, k) else E:Destroy() end
		end
	end
	if Point then Point.Position = At end
	Fx.CFrame = Root.CFrame
	Fx.Weld.C0, Fx.Weld.C1 = CFrame.identity, CFrame.identity -- the effect part sits exactly on the root (its own weld is turned)
	Fx.Weld.Part0 = Fx
	Fx.Weld.Part1 = Root
	Fx.Parent = workspace:FindFirstChild(`Visuals`) or workspace

	EmitManager.Emit(Fx:GetDescendants(), true)
	Debris:AddItem(Fx, 1.2)

	local Sound = ReplicatedStorage.Assets.Sounds.Default:FindFirstChild(`Critical`)
	if Sound then EmitManager.CloneSound(Sound, Root) end
end
