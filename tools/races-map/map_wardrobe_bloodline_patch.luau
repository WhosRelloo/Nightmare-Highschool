local W = game.StarterPlayer.StarterPlayerScripts.Controllers.Gui.Wardrobe
local s = W.Source
assert(not s:find("Local.BloodlineTab", 1, true), "already patched")
local function rep(old, new)
  local a, b = s:find(old, 1, true)
  assert(a, "missing: " .. old:sub(1, 70))
  assert(not s:find(old, b + 1, true), "twice: " .. old:sub(1, 70))
  s = s:sub(1, a - 1) .. new .. s:sub(b + 1)
end
rep("local TABS = { `Look`, `Face`, `Hair`, `Outfit` }", "local TABS = { `Look`, `Face`, `Hair`, `Outfit`, `Bloodline` } -- (Map, 1.65) Bloodline: the full game's tab (Controllers.Gui.Bloodline)")
rep("local Build = ({ Local.LookTab, Local.FaceTab, Local.HairTab, Local.OutfitTab })[Tab]", "local Build = ({ Local.LookTab, Local.FaceTab, Local.HairTab, Local.OutfitTab, Local.BloodlineTab })[Tab]")
rep("function Local.Render()", [[-- (Map, 1.65) the Bloodline tab: race, variant, tier, the race and variant spins, the passive, traits and race looks.
-- The Map has no creator or Student Record, so the full game's Controllers.Gui.Bloodline is shown here instead. Race is
-- still rolled by the server (ReplicatedStorage.Lineage, started by ServerScriptService.NHLineage); nothing is saved.
function Local.BloodlineTab()
	local Ok, Bloodline = pcall(require, script.Parent:WaitForChild(`Bloodline`, 5))
	if not (Ok and Bloodline) then Local.Note(`The bloodline isn't available here.`) return end
	Bloodline.Build({
		Section = Local.Section; Note = Local.Note; Next = Local.Next; Options = Ui.Options;
		-- a plain row (the Bloodline tab places its own children), unlike the wardrobe's horizontal rows
		Row = function(Height: number)
			local Row = Instance.new(`Frame`)
			Row.Name = `Row`
			Row.BackgroundTransparency = 1
			Row.Size = UDim2.new(1, -8, 0, Height)
			Row.LayoutOrder = Local.Next()
			Row.Parent = Ui.Options
			return Row
		end;
		Status = function(Text: string, Color: Color3?)
			if not Ui then return end
			Ui.Status.Text = Text
			Ui.Status.TextColor3 = Color or C.TextDim
		end;
		Render = Local.Render; OpenTab = Shared.OpenTab;
	})
end

function Local.Render()]])
local f, e = loadstring(s)
assert(f, e)
W.Source = s
return "wardrobe ok " .. #s
