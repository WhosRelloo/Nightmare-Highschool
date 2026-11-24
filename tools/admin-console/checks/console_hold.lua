-- (Edit) Cards.Hold: a danger Run fires only after a full 0.8 s hold on a live button. Destroying the button (or an
-- ancestor, as a redraw does) mid-hold, or letting go, never fires it. Cards.Holding is set only while a hold runs.
local G = game.StarterPlayer.StarterPlayerScripts.Controllers.Gui
local Root = G:FindFirstChild("StaffConsole")
local Mod = Root and Root:FindFirstChild("Cards")
if not Mod then return "FAIL StaffConsole.Cards missing" end
local C = require(Mod:Clone())
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end
local function rig()
	local Holder = Instance.new("Frame")
	Holder.Parent = workspace -- parented so "Button.Parent ~= nil" is a real test; Studio Edit never shows it
	local B = Instance.new("TextButton")
	B.Parent = Holder
	local Ring = Instance.new("ImageLabel") Ring.Parent = B
	local N = { Fired = 0 }
	local H = C.Hold(B, Ring, false, function() N.Fired += 1 end)
	return Holder, B, H, N
end
-- control: a full hold fires once (proves the tween runs here)
local Holder, B, H, N = rig()
H.Begin() Eq(C.Holding, true, "holding during a hold")
task.wait(1.1)
Eq(N.Fired, 1, "full hold fires once") Eq(C.Holding, false, "holding cleared on completion")
Holder:Destroy()
-- the button destroyed mid-hold
Holder, B, H, N = rig()
H.Begin() task.wait(0.3) B:Destroy() task.wait() -- Destroying may be a deferred signal
Eq(C.Holding, false, "holding cleared when the button goes")
task.wait(1.0)
Eq(N.Fired, 0, "destroyed button never fires")
Holder:Destroy()
-- an ancestor destroyed mid-hold (the redraw case: Dyn goes)
Holder, B, H, N = rig()
H.Begin() task.wait(0.3) Holder:Destroy()
task.wait(1.0)
Eq(N.Fired, 0, "destroyed ancestor never fires") Eq(C.Holding, false, "holding cleared (ancestor)")
-- unparented without Destroy (Parent = nil) mid-hold: (b) catches it at completion
Holder, B, H, N = rig()
H.Begin() task.wait(0.3) B.Parent = nil
task.wait(1.0)
Eq(N.Fired, 0, "unparented button never fires") Eq(C.Holding, false, "holding cleared (unparented)")
Holder:Destroy() B:Destroy()
-- let go early
Holder, B, H, N = rig()
H.Begin() task.wait(0.3) H.Stop()
Eq(C.Holding, false, "holding cleared on let go")
task.wait(1.0)
Eq(N.Fired, 0, "let go early never fires")
Holder:Destroy()
-- the console closes mid-hold (CancelHold)
Holder, B, H, N = rig()
H.Begin() task.wait(0.3) C.CancelHold()
Eq(C.Holding, false, "holding cleared on close")
task.wait(1.0)
Eq(N.Fired, 0, "closed mid-hold never fires")
Holder:Destroy()
if #Fails > 0 then return "FAIL console_hold " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS console_hold (full hold fires; destroy, ancestor destroy, unparent, let go, close never fire)"
