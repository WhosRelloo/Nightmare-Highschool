-- 2.1.0 typing guard installer (Studio edit mode, execute_luau). Same script for both places.
-- Backs up every script it changes (<Name>_pre210) before touching it, checks the guard module's checksum,
-- and refuses to run twice (each change is skipped if it is already there).
local BACKUP = if game.ServerStorage:FindFirstChild("NHCore") then game.ServerStorage.NHCore.Backups else game.ServerStorage.NH_Backup
local IS_MAP = game.ServerStorage:FindFirstChild("NHCore") ~= nil
local CS = game:GetService("CollectionService")
local TYPING_SRC = [==[<<TYPING>>]==]
local TYPING_LEN, TYPING_SUM = 1919, 2521284098

local function sum(s)
	local h = 0
	for i = 1, #s do h = (h * 31 + string.byte(s, i)) % 4294967296 end
	return h
end
local report = {}
local function backup(m)
	local name = m.Name .. "_pre210"
	if BACKUP:FindFirstChild(name) then return end
	local c = m:Clone()
	c.Name = name
	c:SetAttribute("From", m:GetFullName())
	c:SetAttribute("Checksum", sum(m.Source))
	c.Parent = BACKUP
	if IS_MAP then CS:AddTag(c, "NHCore") end
end
local function setSource(m, s)
	backup(m)
	m.Source = s
	table.insert(report, m:GetFullName() .. " -> " .. #s .. "/" .. sum(s))
end

-- 1. the guard module, next to Keybinds
assert(#TYPING_SRC == TYPING_LEN and sum(TYPING_SRC) == TYPING_SUM, "Typing checksum mismatch: " .. #TYPING_SRC .. " " .. sum(TYPING_SRC))
local Bind = game.ReplicatedStorage.Packages.Bind
local T = Bind:FindFirstChild("Typing")
if not T then
	T = Instance.new("ModuleScript")
	T.Name = "Typing"
	T.Source = TYPING_SRC
	T.Parent = Bind
	if IS_MAP then CS:AddTag(T, "NHCore") end
	table.insert(report, "created " .. T:GetFullName())
elseif T.Source ~= TYPING_SRC then
	setSource(T, TYPING_SRC)
end

-- 2. Keybinds: every combat key stops while typing (Ended still runs, so a held key lets go)
local KB = Bind.Keybinds
local s = KB.Source
if not s:find("Typing", 1, true) then
	local a = "local KeyBinds = require(script.Config)\n"
	assert(s:find(a, 1, true), "Keybinds: no Config require")
	s = s:gsub(a:gsub("%p", "%%%0"), a .. "local Typing = require(script.Parent:WaitForChild('Typing')) -- (2.1.0) no keybinds while typing\n", 1)
	local b = "UserInputService.InputBegan:Connect(function(inputObject, processedEvent)\n"
	assert(s:find(b, 1, true), "Keybinds: no InputBegan")
	s = s:gsub(b:gsub("%p", "%%%0"), b .. "\t-- (2.1.0) typing in any text box, the chat bar included, presses no game key\n\tif Typing.Blocks(inputObject) then\n\t\treturn\n\tend\n", 1)
	setSource(KB, s)
end

-- 3. every controller that asked UserInputService:GetFocusedTextBox() asks the guard instead
local REQ = "local Typing = require(game:GetService(`ReplicatedStorage`):WaitForChild(`Packages`):WaitForChild(`Bind`):WaitForChild(`Typing`)) -- (2.1.0) one \"is the player typing?\" for every key"
for _, d in ipairs(game.StarterPlayer.StarterPlayerScripts.Controllers:GetDescendants()) do
	if d:IsA("ModuleScript") and d.Name ~= "Chat" then
		local src = d.Source
		local n1 = select(2, src:gsub("UserInputService:GetFocusedTextBox%(%)", ""))
		local n2 = select(2, src:gsub("game:GetService%(`UserInputService`%):GetFocusedTextBox%(%)", ""))
		if n1 + n2 > 0 and not src:find("local Typing = ", 1, true) then
			src = src:gsub("game:GetService%(`UserInputService`%):GetFocusedTextBox%(%)", "Typing.Active()")
			src = src:gsub("UserInputService:GetFocusedTextBox%(%)", "Typing.Active()")
			local decl = src:match("\n(local UserInputService%s*=%s*game:GetService%([^\n]-%)[^\n]*)\n")
			if decl then
				local i, j = src:find("\n" .. decl .. "\n", 1, true)
				src = src:sub(1, j) .. REQ .. "\n" .. src:sub(j + 1)
			else
				-- no UserInputService local: put it after the first line that isn't a comment
				local i, j = src:find("\nlocal [^\n]*\n")
				assert(i, d:GetFullName() .. ": nowhere to put the require")
				src = src:sub(1, j) .. REQ .. "\n" .. src:sub(j + 1)
			end
			setSource(d, src)
		end
	end
end

-- 4. Evolution's "Space skips the cutscene" listened to every key, even typed ones
local Evo = game.StarterPlayer.StarterPlayerScripts.Controllers:FindFirstChild("Evolution", true)
if Evo and Evo.Source:find("local Typing = ", 1, true) and not Evo.Source:find("(2.1.0) a typed space", 1, true) then
	local src = Evo.Source
	local ind, line = src:match("\n(%s*)(C2 = UserInputService%.InputBegan:Connect%(function%(I%))\n")
	if line then
		src = src:gsub(line:gsub("%p", "%%%0") .. "\n", line .. "\n" .. ind .. "\tif Typing.Active() then return end -- (2.1.0) a typed space isn't a skip\n", 1)
		setSource(Evo, src)
	else
		table.insert(report, "Evolution: skip line not found (left as is)")
	end
end

return table.concat(report, "\n")
