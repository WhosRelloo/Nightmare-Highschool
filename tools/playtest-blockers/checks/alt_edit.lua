-- alt_edit (playtest-blockers, Edit): Left Alt belongs to shift lock only.
-- Settings reserves it and lists it under Fixed Keys, a saved rebind onto it is refused for every action,
-- ShiftLockKey binds the mouse-lock switch to it, and no other script in the place names it.
local Settings = require(game.ReplicatedStorage.UI.Settings)
local Bad = {}
if Settings.ReservedKeys.LeftAlt ~= `Shift lock` then table.insert(Bad, `ReservedKeys.LeftAlt = {tostring(Settings.ReservedKeys.LeftAlt)}`) end
local Listed = false
for _, Row in Settings.FixedKeys do if Row[1] == `Shift lock` and Row[2] == `Left Alt` then Listed = true end end
if not Listed then table.insert(Bad, `FixedKeys has no "Shift lock / Left Alt" row`) end
for Action in Settings.Defaults.Keys do
	local Out = Settings.Sanitize({ Keys = { [Action] = `LeftAlt` } })
	if Out.Keys[Action] == `LeftAlt` then table.insert(Bad, `a saved {Action} = LeftAlt is kept`) end
end
local Mine = { [`ReplicatedStorage.UI.Settings`] = true; [`ReplicatedStorage.UI.Components`] = true; -- (the key-cap label "Alt")
	[`StarterPlayer.StarterPlayerScripts.Controllers.Character.ShiftLockKey`] = true;
	[`StarterPlayer.StarterPlayerScripts.Controllers.Gui.ShiftLockCursor`] = true }
local Others = {}
for _, Root in { game.ReplicatedStorage, game.ServerScriptService, game.StarterPlayer, game.StarterGui, game.ReplicatedFirst, game.Workspace } do
	for _, S in Root:GetDescendants() do
		if S:IsA(`LuaSourceContainer`) and not Mine[S:GetFullName()] and string.find(S.Source, `LeftAlt`, 1, true) then
			table.insert(Others, S:GetFullName())
		end
	end
end
if #Others > 0 then table.insert(Bad, `other scripts name LeftAlt: {table.concat(Others, `, `)}`) end
local SLK = game.StarterPlayer.StarterPlayerScripts.Controllers.Character.ShiftLockKey.Source
if not string.find(SLK, "local KEYS = `LeftAlt`", 1, true) then table.insert(Bad, `ShiftLockKey is not on LeftAlt`) end
if not game.StarterPlayer.EnableMouseLockOption then table.insert(Bad, `EnableMouseLockOption is off`) end
if #Bad > 0 then return `FAIL ` .. table.concat(Bad, `; `) end
return `PASS Left Alt = Shift lock only (reserved, listed, refused for {#(function() local n = {} for k in Settings.Defaults.Keys do table.insert(n, k) end return n end)()} rebindable actions, no other script names it)`
