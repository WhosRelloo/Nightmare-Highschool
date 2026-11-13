--[[
	WeaponVisibility (client). Controllers.World.WeaponVisibility  (1.98.0)

	Owner: "Add an option to show your weapon or hide it". Settings > Interface > "Show Weapon When Put Away"
	(UI.Settings key ShowWeapon, saved with the rest of your settings). The server copies it to the player attribute
	NHShowWeapon (false = hidden), so every client knows each player's choice.

	This runs on every client and hides, for each player whose NHShowWeapon is false, the weapon they carry put away:
	the "Back" model on the torso (Character.Accessory.Weapons, made by ActionManager.General.Equip and
	Managers.EntityLoader; it holds a Motor6D named Torso). The weapon in your hand while it's out always shows.
	It hides with LocalTransparencyModifier (never the parts' own Transparency, so invisibility and other effects keep
	working) and switches the stowed weapon's trails, particles and lights off on this screen.
]]

local Players = game:GetService(`Players`)
local RunService = game:GetService(`RunService`)

local Shared = {}
local Local = {}

local Hidden = {} :: { [BasePart]: boolean }          -- parts kept at LocalTransparencyModifier 1
local Effects = {} :: { [Instance]: boolean }          -- effects switched off here, and whether they were on
local Watched = {} :: { [Player]: { RBXScriptConnection } }

-- the stowed weapon models on a character (the "Back" copies, with their Torso Motor6D)
function Local.Stowed(Char: Model): { Instance }
	local Out = {}
	local Acc = Char:FindFirstChild(`Accessory`)
	local Weapons = Acc and Acc:FindFirstChild(`Weapons`)
	for _, W in (Weapons and Weapons:GetChildren()) or {} do
		local J = W:FindFirstChild(`Torso`)
		if J and J:IsA(`Motor6D`) then table.insert(Out, W) end
	end
	return Out
end

local function isEffect(D: Instance): boolean
	return D:IsA(`ParticleEmitter`) or D:IsA(`Trail`) or D:IsA(`Beam`) or D:IsA(`Light`) or D:IsA(`Fire`) or D:IsA(`Smoke`) or D:IsA(`Sparkles`)
end

function Local.Hide(W: Instance)
	for _, D in { W, unpack(W:GetDescendants()) } do
		if D:IsA(`BasePart`) then
			Hidden[D] = true
			D.LocalTransparencyModifier = 1
		elseif D:IsA(`Decal`) then
			local X: any = D
			Hidden[X] = true
			X.LocalTransparencyModifier = 1
		elseif isEffect(D) and Effects[D] == nil then
			local E: any = D
			Effects[D] = E.Enabled
			E.Enabled = false
		end
	end
end

function Local.Show(W: Instance)
	for _, D in { W, unpack(W:GetDescendants()) } do
		local X: any = D
		if Hidden[X] then
			Hidden[X] = nil
			X.LocalTransparencyModifier = 0
		elseif Effects[D] ~= nil then
			X.Enabled = Effects[D]
			Effects[D] = nil
		end
	end
end

-- bring one player's character in line with their choice
function Local.Refresh(P: Player)
	local Char = P.Character
	if not Char then return end
	local Hide = P:GetAttribute(`NHShowWeapon`) == false
	for _, W in Local.Stowed(Char) do
		if Hide then Local.Hide(W) else Local.Show(W) end
	end
end

function Local.Watch(P: Player)
	if Watched[P] then for _, C in Watched[P] do C:Disconnect() end end
	local Conns = {}
	Watched[P] = Conns
	local function onChar(Char: Model)
		Local.Refresh(P)
		-- the stowed weapon is made again on every equip / put away, and a vow's effects attach to it later: catch
		-- anything that arrives under Accessory.Weapons (one refresh a frame at most)
		local Queued = false
		table.insert(Conns, Char.DescendantAdded:Connect(function(D)
			local Acc = Char:FindFirstChild(`Accessory`)
			local Weapons = Acc and Acc:FindFirstChild(`Weapons`)
			if Queued or not (Weapons and (D == Weapons or D:IsDescendantOf(Weapons))) then return end
			Queued = true
			task.defer(function() Queued = false Local.Refresh(P) end)
		end))
	end
	table.insert(Conns, P:GetAttributeChangedSignal(`NHShowWeapon`):Connect(function() Local.Refresh(P) end))
	table.insert(Conns, P.CharacterAdded:Connect(onChar))
	if P.Character then onChar(P.Character) end
end

function Shared.OnStart()
	for _, P in Players:GetPlayers() do Local.Watch(P) end
	Players.PlayerAdded:Connect(Local.Watch)
	Players.PlayerRemoving:Connect(function(P)
		for _, C in Watched[P] or {} do C:Disconnect() end
		Watched[P] = nil
	end)
	-- the camera's own transparency pass (zooming in) rewrites LocalTransparencyModifier on your character's parts:
	-- keep the hidden ones hidden after it, and forget parts that are gone
	RunService:BindToRenderStep(`NHWeaponVisibility`, Enum.RenderPriority.Camera.Value + 2, function()
		for D in Hidden do
			if D.Parent then
				if D.LocalTransparencyModifier ~= 1 then D.LocalTransparencyModifier = 1 end
			else
				Hidden[D] = nil
			end
		end
		for D in Effects do if not D.Parent then Effects[D] = nil end end
	end)
end

return Shared
