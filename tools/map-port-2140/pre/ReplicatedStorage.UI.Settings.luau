--!nonstrict
--[[
	NH Settings - per-player settings: schema, saving (server) and applying (client).

	Server  Settings.StartServer()   (ServerScriptService.NHSettings runs it)
	  Saved in the player's ProfileService data (PlayerData.Settings) via
	  Data.UpdateState({ type = "SetSettings" }). Requests come over ReplicatedStorage.NHSettings.Save
	  (made at runtime) and are validated (Sanitize) and rate-limited first.
	Client  Settings.Load()            fetch + apply (Controllers.Gui.SettingsMenu calls it)
	        Settings.Get(key) / Settings.Set(key, value) / Settings.SetKey(action, keyName)
	        Settings.Reset()           back to defaults
	        Settings.Changed           BindableEvent: (key, value)

	What each setting really does (all client-side):
	  MasterVolume / EffectsVolume / MusicVolume -> SoundGroups NH_Master > NH_Effects / NH_Music.
	      Sounds without a group are routed: Looped -> Music, everything else -> Effects.
	  FieldOfView   -> Camera.FieldOfView (ScreenFX.FOV returns to it after its zooms)
	  CameraShake   -> LocalPlayer attribute NHShakeScale, read by EmitManager.ShakeCamera
	  UIScale       -> Components.SetUserScale (multiplies every kit AutoScale)
	  ShowHud / ShowClock -> PlayerGui.KitHud / PlayerGui.ClockHud Enabled
	  ShowWeapon    -> (1.98.0) the server copies it to the player attribute NHShowWeapon when your settings load or
	                  save; every client then hides your put-away weapon if it's false (Controllers.World.WeaponVisibility)
	  Shadows       -> Lighting.GlobalShadows (local)
	  Vignette      -> PlayerGui.Vingette Enabled
	  ReducedFlashing -> LocalPlayer attribute NHReducedFlash (bool)    } read by the client FX toolbox
	  ReducedMotion   -> LocalPlayer attribute NHReducedMotion (bool)   } (Controllers.Fx) and any VFX
	  EffectsQuality  -> LocalPlayer attribute NHFxQuality "High"/"Low" } that flashes, moves or spawns a lot
	  CursorSize      -> LocalPlayer attribute NHCursorSize (px)      } read by Controllers.Gui.Cursor
	  AnimatedCursor  -> LocalPlayer attribute NHCursorAnimated (bool) }
	      Until the player changes them, ReducedMotion follows the device (GuiService.ReducedMotionEnabled)
	      and EffectsQuality follows Roblox's graphics level (levels 1-3 -> Low).
	  Keys[action]  -> InputController.Rebind(action, key)
]]

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Settings = {}
Settings.RemotesName = "NHSettings"

Settings.Defaults = {
	MasterVolume = 80,
	EffectsVolume = 100,
	MusicVolume = 70,
	FieldOfView = 70,
	CameraShake = 100,
	UIScale = 100,
	ShowHud = true,
	ShowClock = true,
	ShowWeapon = true, -- (1.98.0) your weapon on your back while it's put away (everyone sees the choice)
	Shadows = true,
	Vignette = true,
	ReducedFlashing = false,
	ReducedMotion = false, -- the client uses the device setting until the player picks
	EffectsQuality = "High", -- "High" | "Low"; the client uses the graphics level until the player picks
	CursorSize = 32,
	AnimatedCursor = true,
	ControllerButtons = "Auto", -- "Auto" | "Xbox" | "PlayStation": the button names hints show (Components.PadStyle)
	Keys = {
		Block = "F", Dodge = "Q", Sprint = "LeftShift", Slide = "LeftControl", -- hold: slide while sprinting, crouch otherwise
		M2 = "R", Feint = "MouseButton2", Carry = "V", Grip = "B",
	},
}

-- Numeric ranges (min, max, step)
Settings.Ranges = {
	MasterVolume = { 0, 100, 5 },
	EffectsVolume = { 0, 100, 5 },
	MusicVolume = { 0, 100, 5 },
	FieldOfView = { 60, 100, 1 },
	CameraShake = { 0, 100, 5 },
	UIScale = { 80, 120, 5 },
	CursorSize = { 24, 48, 4 },
}

-- Settings with a fixed set of string values
Settings.Choices = {
	EffectsQuality = { "High", "Low" },
	ControllerButtons = { "Auto", "Xbox", "PlayStation" },
}

-- Rebindable combat actions (ids are InputController / Bind.Keybinds.Config names)
Settings.KeyActions = {
	{ Id = "Block", Label = "Block" },
	{ Id = "Dodge", Label = "Dodge" },
	{ Id = "Sprint", Label = "Sprint" },
	{ Id = "Slide", Label = "Slide / Crouch" },
	{ Id = "M2", Label = "Heavy Attack" },
	{ Id = "Feint", Label = "Feint" },
	{ Id = "Carry", Label = "Carry" },
	{ Id = "Grip", Label = "Grip / Skateboard" },
}

-- Keys other systems own; they can't be taken by a rebind.
Settings.ReservedKeys = {
	-- menus (2026-11-02 key map: all on the right-hand side of the keyboard, away from WASD, combat and movement)
	Backquote = "Locker", Y = "Phone", P = "Options", M = "Report Card", L = "Factions", J = "Journal", U = "Study Group", K = "Wardrobe",
	Tab = "Player list", BackSlash = "Cinematic view", Escape = "Roblox menu", Slash = "Chat",
	-- world and character
	E = "Interact", G = "Introduce yourself", N = "Race action", T = "Transform", H = "Night sight", Z = "Skill", X = "Skill", C = "Skill",
	Period = "Emotes", I = "Camera zoom", O = "Camera zoom", Space = "Jump", LeftAlt = "Shift lock", MouseButton1 = "Light Attack",
	W = "Move", A = "Move", S = "Move", D = "Move", -- (audit) a combat key rebound onto W also fired on every step forward
	One = "Hotbar", Two = "Hotbar", Three = "Hotbar", Four = "Hotbar", Five = "Hotbar",
	Six = "Hotbar", Seven = "Hotbar", Eight = "Hotbar", Nine = "Hotbar",
}
Settings.FixedKeys = {
	{ "Interact", "E" }, { "Light Attack", "LMB" }, { "Jump", "Space" }, { "Hotbar", "1-9" },
	{ "Weapon skills", "Z / X / C" }, { "Race action", "N" }, { "Transform", "T" }, { "Night sight", "H" }, { "Introduce yourself", "G" },
	{ "Shift lock", "Left Alt" }, { "Emotes", "." },
	{ "Options", "P" }, { "Report Card", "M" }, { "Locker", "`" }, { "Phone", "Y" }, { "Study Group", "U" }, { "Journal", "J" }, { "Factions", "L" },
	{ "Students", "Tab" }, { "Wardrobe", "K" }, { "Cinematic view", "\\" },
}

local function deepCopy(t)
	local out = {}
	for k, v in pairs(t) do
		out[k] = type(v) == "table" and deepCopy(v) or v
	end
	return out
end
Settings.Copy = deepCopy

local function validKey(name)
	if type(name) ~= "string" or #name > 24 then
		return false
	end
	if name == "MouseButton2" or name == "MouseButton3" then
		return true
	end
	if string.sub(name, 1, 6) == "Button" or string.sub(name, 1, 4) == "DPad" or string.sub(name, 1, 10) == "Thumbstick" then
		return false -- controller buttons are fixed (Components.PadControls); these slots are keyboard / mouse keys
	end
	return pcall(function()
		return Enum.KeyCode[name]
	end)
end
Settings.ValidKey = validKey

-- Merge untrusted data onto defaults; clamp numbers, keep booleans, validate keys.
function Settings.Sanitize(data)
	local out = deepCopy(Settings.Defaults)
	if type(data) ~= "table" then
		return out
	end
	for key, def in pairs(Settings.Defaults) do
		local v = data[key]
		if key == "Keys" then
			if type(v) == "table" then
				-- 2026-11-01: Sprint moved from double-tap W to holding Left Shift; old saves on W move with it
				if v.Sprint == "W" then
					v = table.clone(v)
					v.Sprint = nil
				end
				for action, k in pairs(v) do
					if def[action] and validKey(k) and not Settings.ReservedKeys[k] then
						out.Keys[action] = k
					end
				end
				-- resolve accidental duplicates back to defaults
				local seen = {}
				for action, k in pairs(out.Keys) do
					if seen[k] then
						out.Keys[action] = def[action]
					end
					seen[out.Keys[action]] = true
				end
			end
		elseif type(def) == "number" then
			if type(v) == "number" and v == v then
				local r = Settings.Ranges[key]
				out[key] = r and math.clamp(v, r[1], r[2]) or v
			end
		elseif type(def) == "boolean" then
			if type(v) == "boolean" then
				out[key] = v
			end
		elseif type(def) == "string" then
			local choices = Settings.Choices[key]
			if type(v) == "string" and choices and table.find(choices, v) then
				out[key] = v
			end
		end
	end
	return out
end

--------------------------------------------------------------------------
-- server: validate the request, then save through ProfileService (Services.Player.Data)
--------------------------------------------------------------------------
function Settings.StartServer()
	assert(RunService:IsServer(), "Settings.StartServer must run on the server")
	if Settings._serverStarted then
		return
	end
	Settings._serverStarted = true
	local Data = require(game:GetService("ServerScriptService"):WaitForChild("Services"):WaitForChild("Player"):WaitForChild("Data"))
	local folder = ReplicatedStorage:FindFirstChild(Settings.RemotesName) or Instance.new("Folder")
	folder.Name = Settings.RemotesName
	local saveRE = folder:FindFirstChild("Save") or Instance.new("RemoteEvent")
	saveRE.Name = "Save"
	saveRE.Parent = folder
	folder.Parent = ReplicatedStorage

	local last = {}
	saveRE.OnServerEvent:Connect(function(p, data)
		local now = os.clock()
		if last[p] and now - last[p] < 0.5 then
			return -- rate limit
		end
		last[p] = now
		if not Data.GetProfile(p) then
			return
		end
		local clean = Settings.Sanitize(data)
		-- (audit) the device-derived settings are kept only when the player set them (the client leaves them out
		-- otherwise); Sanitize fills every default, which saved the device's value as if the player had chosen it
		for _, k in ipairs({ "ReducedMotion", "EffectsQuality" }) do
			if type(data) ~= "table" or data[k] == nil then
				clean[k] = nil
			end
		end
		Data.UpdateState(p, { type = "SetSettings", settings = clean })
		p:SetAttribute("NHShowWeapon", clean.ShowWeapon ~= false) -- (1.98.0) Controllers.World.WeaponVisibility
	end)
	-- (1.98.0) the saved choice, on joining and on every slot switch
	local function fromProfile(p, data)
		local s = type(data) == "table" and data.Settings
		p:SetAttribute("NHShowWeapon", not (type(s) == "table" and s.ShowWeapon == false))
	end
	if Data.ProfileLoaded then
		Data.ProfileLoaded:Connect(fromProfile)
	end
	for _, p in ipairs(Players:GetPlayers()) do
		local prof = Data.GetProfile(p)
		if prof then fromProfile(p, prof) end
	end
	Players.PlayerRemoving:Connect(function(p)
		last[p] = nil
	end)
end

--------------------------------------------------------------------------
-- client
--------------------------------------------------------------------------
Settings.Current = deepCopy(Settings.Defaults)
Settings.Changed = Instance.new("BindableEvent")

local groups
local function soundGroups()
	if groups then
		return groups
	end
	local SoundService = game:GetService("SoundService")
	local master = SoundService:FindFirstChild("NH_Master") or Instance.new("SoundGroup")
	master.Name = "NH_Master"
	master.Parent = SoundService
	local effects = master:FindFirstChild("NH_Effects") or Instance.new("SoundGroup")
	effects.Name = "NH_Effects"
	effects.Parent = master
	local music = master:FindFirstChild("NH_Music") or Instance.new("SoundGroup")
	music.Name = "NH_Music"
	music.Parent = master
	groups = { Master = master, Effects = effects, Music = music }
	local function route(s)
		if s:IsA("Sound") and s.SoundGroup == nil then
			s.SoundGroup = s.Looped and music or effects
		end
	end
	local function watch(root)
		for _, d in ipairs(root:GetDescendants()) do
			route(d)
		end
		root.DescendantAdded:Connect(function(d)
			if d:IsA("Sound") then
				task.defer(route, d) -- after the creator sets Looped / SoundGroup
			end
		end)
	end
	watch(workspace)
	watch(SoundService)
	local pg = Players.LocalPlayer and Players.LocalPlayer:FindFirstChild("PlayerGui")
	if pg then
		watch(pg)
	end
	return groups
end

local function inputController()
	local ps = Players.LocalPlayer:FindFirstChild("PlayerScripts")
	local m = ps and ps:FindFirstChild("Controllers") and ps.Controllers:FindFirstChild("Character") and ps.Controllers.Character:FindFirstChild("InputController")
	if not m then
		return nil
	end
	local ok, mod = pcall(require, m)
	return ok and mod or nil
end

local function setGuiEnabled(name, on)
	task.spawn(function()
		local pg = Players.LocalPlayer:WaitForChild("PlayerGui")
		local g = pg:WaitForChild(name, 15)
		if g and g:IsA("LayerCollector") then
			g.Enabled = on
		end
	end)
end

local Appliers = {
	MasterVolume = function(v) soundGroups().Master.Volume = v / 100 end,
	EffectsVolume = function(v) soundGroups().Effects.Volume = v / 100 end,
	MusicVolume = function(v) soundGroups().Music.Volume = v / 100 end,
	FieldOfView = function(v)
		local cam = workspace.CurrentCamera
		if cam then
			cam.FieldOfView = v
		end
	end,
	CameraShake = function(v) Players.LocalPlayer:SetAttribute("NHShakeScale", v / 100) end,
	UIScale = function(v)
		local Components = require(script.Parent:WaitForChild("Components"))
		if Components.SetUserScale then
			Components.SetUserScale(v / 100)
		end
	end,
	ShowHud = function(v) setGuiEnabled("KitHud", v) end,
	ShowClock = function(v) setGuiEnabled("ClockHud", v) end,
	Shadows = function(v) game:GetService("Lighting").GlobalShadows = v end,
	Vignette = function(v) setGuiEnabled("Vingette", v) end,
	ReducedFlashing = function(v) Players.LocalPlayer:SetAttribute("NHReducedFlash", v == true) end,
	ReducedMotion = function(v) Players.LocalPlayer:SetAttribute("NHReducedMotion", v == true) end,
	EffectsQuality = function(v) Players.LocalPlayer:SetAttribute("NHFxQuality", v == "Low" and "Low" or "High") end,
	CursorSize = function(v) Players.LocalPlayer:SetAttribute("NHCursorSize", v) end,
	AnimatedCursor = function(v) Players.LocalPlayer:SetAttribute("NHCursorAnimated", v ~= false) end,
	ControllerButtons = function(v) Players.LocalPlayer:SetAttribute("NHPadStyle", v) end,
	Keys = function(keys)
		task.spawn(function()
			-- InputController builds its binds in OnStart; wait until they exist.
			local ic
			local t0 = os.clock()
			repeat
				ic = inputController()
				if ic and ic.Binds and next(ic.Binds) then
					break
				end
				task.wait(0.25)
			until os.clock() - t0 > 15
			if not (ic and ic.Rebind) then
				warn("[Settings] InputController.Rebind not available; keybinds not applied")
				return
			end
			for action, k in pairs(keys) do
				ic.Rebind(action, k)
			end
		end)
	end,
}

function Settings.Apply(key)
	if key then
		local f = Appliers[key]
		if f then
			f(Settings.Current[key])
		end
		return
	end
	for k, f in pairs(Appliers) do
		local ok, err = pcall(f, Settings.Current[k])
		if not ok then
			warn("[Settings] apply " .. k .. " failed:", err)
		end
	end
end

local function remotes()
	return ReplicatedStorage:WaitForChild(Settings.RemotesName, 10)
end

-- Defaults that come from this device until the player sets them (never saved until they do).
local DEVICE_KEYS = { "ReducedMotion", "EffectsQuality" }
-- (audit) which of them the player really set (saved, or changed here); only those are sent when saving
local chosen = {}
function Settings.DeviceDefaults()
	local d = deepCopy(Settings.Defaults)
	pcall(function()
		local GuiService = game:GetService("GuiService")
		d.ReducedMotion = GuiService.ReducedMotionEnabled == true
	end)
	pcall(function()
		local q = UserSettings():GetService("UserGameSettings").SavedQualityLevel
		local n = tonumber(string.match(q.Name, "%d+"))
		d.EffectsQuality = (n and n <= 3) and "Low" or "High" -- Automatic counts as High
	end)
	return d
end
-- saved settings, with this device's defaults for anything the player never set
local function withDevice(saved)
	local out = Settings.Sanitize(saved)
	local dev = Settings.DeviceDefaults()
	for _, k in ipairs(DEVICE_KEYS) do
		if type(saved) ~= "table" or saved[k] == nil then
			out[k] = dev[k]
			chosen[k] = nil
		else
			chosen[k] = true
		end
	end
	return out
end

-- (2.1.3) settings changed in the main menu before a slot is loaded: the server has no profile to save them in (it
-- dropped them), and Load then replaced them with the slot's saved ones, so they were lost. Now they're kept here and
-- saved into the slot as soon as it loads (Load / the slot-switch watch below).
local unsaved = false
local scRef = nil
local saveToken = 0
local function queueSave()
	saveToken += 1
	local my = saveToken
	task.delay(1, function()
		if my ~= saveToken then
			return
		end
		if scRef and scRef.GetProfile(false) == nil then
			unsaved = true
			Settings.Changed:Fire("_pending", true)
			return
		end
		local f = remotes()
		if f then
			-- (audit) leave out the device defaults the player never set, so they keep following the device
			local out = Settings.Copy(Settings.Current)
			for _, k in ipairs(DEVICE_KEYS) do
				if not chosen[k] then
					out[k] = nil
				end
			end
			f:WaitForChild("Save"):FireServer(out)
		end
		Settings.Changed:Fire("_saved", true)
	end)
end

local function stateController()
	local ps = Players.LocalPlayer:WaitForChild("PlayerScripts")
	local m = ps:WaitForChild("Controllers"):WaitForChild("StateController", 15)
	local ok, mod = pcall(require, m)
	return ok and mod or nil
end
Settings.StateController = stateController

function Settings.Load()
	local sc = stateController()
	scRef = sc
	local profile = sc and sc.GetProfile(true)
	if unsaved then
		unsaved = false -- (2.1.3) changed in the main menu before this slot loaded: keep them and save them into it
		Settings.Apply()
		queueSave()
	else
		Settings.Current = withDevice(profile and profile.Settings)
		Settings.Apply()
	end
	-- save slots: the profile can be swapped after start (main menu picks a slot) - re-apply when it is
	if sc then
		task.spawn(function()
			local seen = profile
			while true do
				task.wait(1)
				local now = sc.GetProfile(false)
				if now and now ~= seen then
					seen = now
					if unsaved then
						unsaved = false -- (2.1.3) see Load
						queueSave()
					else
						Settings.Current = withDevice(now.Settings)
					end
					Settings.Apply()
				end
			end
		end)
	end
	workspace:GetPropertyChangedSignal("CurrentCamera"):Connect(function()
		Settings.Apply("FieldOfView")
	end)
	Players.LocalPlayer.CharacterAdded:Connect(function()
		task.wait(0.5)
		Settings.Apply("FieldOfView")
	end)
	Settings.Changed:Fire("_loaded", true)
	return Settings.Current
end

function Settings.Get(key)
	return Settings.Current[key]
end

function Settings.Set(key, value)
	if Settings.Defaults[key] == nil or key == "Keys" then
		return false
	end
	local patch = Settings.Copy(Settings.Current)
	patch[key] = value
	Settings.Current = Settings.Sanitize(patch)
	if table.find(DEVICE_KEYS, key) then
		chosen[key] = true -- (audit) now it is the player's choice
	end
	Settings.Apply(key)
	Settings.Changed:Fire(key, Settings.Current[key])
	queueSave()
	return true
end

-- Returns ok, message. keyName is a KeyCode name or "MouseButton2"/"MouseButton3".
function Settings.SetKey(action, keyName)
	if not Settings.Defaults.Keys[action] then
		return false, "Unknown action"
	end
	if not validKey(keyName) then
		return false, "That key can't be bound"
	end
	if Settings.ReservedKeys[keyName] then
		return false, keyName .. " is used by " .. Settings.ReservedKeys[keyName]
	end
	for other, k in pairs(Settings.Current.Keys) do
		if other ~= action and k == keyName then
			local label = other
			for _, a in ipairs(Settings.KeyActions) do
				if a.Id == other then
					label = a.Label
				end
			end
			return false, keyName .. " is already " .. label
		end
	end
	Settings.Current.Keys[action] = keyName
	local ic = inputController()
	if ic and ic.Rebind then
		ic.Rebind(action, keyName)
	end
	Settings.Changed:Fire("Keys", Settings.Current.Keys)
	queueSave()
	return true, "Bound " .. action .. " to " .. keyName
end

function Settings.Reset()
	table.clear(chosen) -- (audit) back to following the device
	Settings.Current = Settings.DeviceDefaults()
	Settings.Apply()
	Settings.Changed:Fire("_reset", true)
	queueSave()
end

return Settings
