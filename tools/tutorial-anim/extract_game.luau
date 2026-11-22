-- tools/tutorial-anim/extract_game.luau (Edit mode): a game animation sampled at 30 fps on a standard R6 dummy -> JSON
local FROM, TO = __FROM__, __TO__ -- frame window (the CLI truncates output at 30000 chars: extract in chunks)
local PATH = "__PATH__" -- e.g. Default.Movement.CrouchWalk, under ReplicatedStorage.Assets.Animations
local Players, Http = game:GetService("Players"), game:GetService("HttpService")
local A = game.ReplicatedStorage.Assets.Animations
for Part in PATH:gmatch("[^%.]+") do A = A[Part] end
local D = Players:CreateHumanoidModelFromDescription(Instance.new("HumanoidDescription"), Enum.HumanoidRigType.R6)
D:PivotTo(CFrame.new(0, 600, 0))
D.HumanoidRootPart.Anchored = true
D.Parent = workspace
local An = D.Humanoid:FindFirstChildOfClass("Animator")
local T = An:LoadAnimation(A)
T.Looped = true
T:Play(0)
local T0 = os.clock()
while T.Length == 0 and os.clock() - T0 < 15 do task.wait(0.1) end
local M = { Torso = D.HumanoidRootPart.RootJoint, Head = D.Torso.Neck, ["Left Arm"] = D.Torso["Left Shoulder"],
	["Right Arm"] = D.Torso["Right Shoulder"], ["Left Leg"] = D.Torso["Left Hip"], ["Right Leg"] = D.Torso["Right Hip"] }
local Frames = {}
local N = math.max(1, math.floor(T.Length * 30 + 0.5))
for F = FROM, math.min(TO, N) do
	T.TimePosition = math.min(F / 30, T.Length - 1e-3)
	An:StepAnimations(0)
	local Row = { t = F / 30 }
	for Name, Motor in M do local C = { Motor.Transform:GetComponents() }
		for I, V in C do C[I] = math.round(V * 1e6) / 1e6 end
		Row[Name] = C end
	table.insert(Frames, Row)
end
D:Destroy()
return Http:JSONEncode({ path = PATH; length = T.Length; frames = Frames; n = N })
