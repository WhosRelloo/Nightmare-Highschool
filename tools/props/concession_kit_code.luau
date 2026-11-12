--!nocheck
-- Props batch 54 (the concession consumables kit): the code hooks, patched in place in NH Combat Test. Safe to run again (each
-- script is skipped once it has its "(batch 54)" marker); each patched source is compile-checked before it is written.
--   Services.Features.Inventory  Local.Prop uses ReplicatedStorage.NHSnacks.<Id>.Handle (the modelled hand prop, any glass
--                                welded under it) when it's there, and MakeTool takes the prop's NHGrip attribute as the grip.
--   Controllers.Gui.Locker       Local.Model shows the same modelled prop in the stand's grid and the Backpack.
--   Services.Features.Concession the menu board lists the first eight regular items and "+ N more at the counter" (the
--                                buy menu scrolls; the board would overflow with the kit's 26 new snacks).
local SSS = game:GetService("ServerScriptService")
local SPS = game:GetService("StarterPlayer").StarterPlayerScripts
local report = {}

local function patch(script, edits)
	local src = script.Source
	if src:find("(batch 54)", 1, true) then table.insert(report, script.Name .. ": already patched") return end
	for _, e in edits do
		local i, j = src:find(e[1], 1, true)
		assert(i, script.Name .. ": anchor not found: " .. e[1]:sub(1, 60))
		assert(not src:find(e[1], j + 1, true), script.Name .. ": anchor not unique: " .. e[1]:sub(1, 60))
		src = src:sub(1, i - 1) .. e[2] .. src:sub(j + 1)
	end
	local ok, err = loadstring(src)
	assert(ok, script.Name .. " doesn't compile: " .. tostring(err))
	script.Source = src
	table.insert(report, script.Name .. ": patched, " .. #src .. " bytes")
end

patch(SSS.Services.Features.Inventory, {
	{ "function Local.Prop(It): BasePart\n\tlocal P = Instance.new(`Part`)",
		"function Local.Prop(It): BasePart\n"
		.. "\t-- (batch 54) the item's modelled hand prop (ReplicatedStorage.NHSnacks.<Id>.Handle, glass welded under it) when it's in\n"
		.. "\tlocal Lib = ReplicatedStorage:FindFirstChild(`NHSnacks`)\n"
		.. "\tlocal Tpl = Lib and Lib:FindFirstChild(It.Id)\n"
		.. "\tlocal Mesh = Tpl and Tpl:FindFirstChild(`Handle`)\n"
		.. "\tif Mesh then\n"
		.. "\t\tlocal H = Mesh:Clone()\n"
		.. "\t\tfor _, D in { H, table.unpack(H:GetDescendants()) } do\n"
		.. "\t\t\tif D:IsA(`BasePart`) then D.Anchored = false D.CanCollide, D.CanQuery, D.CanTouch, D.Massless = false, false, false, true end\n"
		.. "\t\tend\n"
		.. "\t\treturn H\n"
		.. "\tend\n"
		.. "\tlocal P = Instance.new(`Part`)" },
	{ "\tif It.Prop.Shape == `Can` or It.Prop.Shape == `Bottle` then T.GripRight",
		"\tif H:GetAttribute(`NHGrip`) then T.Grip = H:GetAttribute(`NHGrip`) -- (batch 54) the modelled prop's own grip\n"
		.. "\telseif It.Prop.Shape == `Can` or It.Prop.Shape == `Bottle` then T.GripRight" },
})

patch(SPS.Controllers.Gui.Locker, {
	{ "\tlocal It = Items.ById[Id]\n\tif not It then return nil end\n\tlocal P = Instance.new(`Part`)",
		"\tlocal It = Items.ById[Id]\n\tif not It then return nil end\n"
		.. "\t-- (batch 54) the item's modelled hand prop when it's in (ReplicatedStorage.NHSnacks.<Id>.Handle)\n"
		.. "\tlocal Lib = ReplicatedStorage:FindFirstChild(`NHSnacks`)\n"
		.. "\tlocal Tpl = Lib and Lib:FindFirstChild(Id)\n"
		.. "\tif Tpl and Tpl:FindFirstChild(`Handle`) then\n"
		.. "\t\tlocal M = Tpl:Clone() -- the whole model, so the glass (welded in the hand, not here) moves with it\n"
		.. "\t\tM:PivotTo(CFrame.Angles(0, math.rad(-25), 0))\n"
		.. "\t\treturn M\n"
		.. "\tend\n"
		.. "\tlocal P = Instance.new(`Part`)" },
})

patch(SSS.Services.Features.Concession, {
	{ "\t\tlocal Row = 0\n\t\tfor _, It in Items.List do\n\t\t\tif It.Special then continue end\n",
		"\t\tlocal Row, More = 0, 0\n\t\tfor _, It in Items.List do\n\t\t\tif It.Special then continue end\n"
		.. "\t\t\tif Row >= 8 then More += 1 continue end -- (batch 54) the board holds eight; the rest are on the counter's menu\n" },
	{ "\t\tlocal Y = 0.18 + Row * 0.078 + 0.01\n",
		"\t\tif More > 0 then\n"
		.. "\t\t\tLocal.Text(F, `+ {More} more at the counter`, Enum.Font.Garamond, GOLD, UDim2.fromScale(0.07, 0.18 + Row * 0.078), UDim2.fromScale(0.86, 0.06), Enum.TextXAlignment.Left)\n"
		.. "\t\t\tRow += 1\n"
		.. "\t\tend\n"
		.. "\t\tlocal Y = 0.18 + Row * 0.078 + 0.01\n" },
})

return table.concat(report, "\n")
