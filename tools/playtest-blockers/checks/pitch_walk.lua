-- pitch_walk (playtest-blockers, Server, Play, run_live.py): the soccer pitch and the practice field can be walked into.
-- The ball-only walls (collision group SportBallWall) must stop the ball and nothing else: every other group a
-- character, NPC or ragdoll can be in is non-collidable with them, and the player walks from outside the pitch's
-- north gap to the centre spot, and from outside the practice field to its middle.
local PS = game:GetService(`PhysicsService`)
local P = game.Players:GetPlayers()[1]
local C = P.Character
local H = C:FindFirstChildOfClass(`Humanoid`)
local R = C:FindFirstChild(`HumanoidRootPart`)
local Bad = {}
for _, G in PS:GetRegisteredCollisionGroups() do
	local Want = G.name == `SportBall`
	if G.name ~= `SportBallWall` and PS:CollisionGroupsAreCollidable(`SportBallWall`, G.name) ~= Want then
		table.insert(Bad, `SportBallWall vs {G.name} = {tostring(not Want)}`)
	end
end
local Groups = {}
for _, Pt in C:GetDescendants() do if Pt:IsA(`BasePart`) then Groups[Pt.CollisionGroup] = true end end
local G = {}
for K in Groups do table.insert(G, K) end

local Home = R.CFrame
local function walk(From: Vector3, To: Vector3, Label: string)
	C:PivotTo(CFrame.lookAt(From, Vector3.new(To.X, From.Y, To.Z)))
	task.wait(0.6)
	local T0 = os.clock()
	local Best = math.huge
	while os.clock() - T0 < 20 do
		if script:GetAttribute(`Stop`) then break end
		H:MoveTo(To)
		local D = (Vector3.new(R.Position.X, To.Y, R.Position.Z) - To).Magnitude
		Best = math.min(Best, D)
		if D < 4 then return string.format(`%s %.1fs`, Label, os.clock() - T0) end
		task.wait(0.25)
	end
	table.insert(Bad, string.format(`%s: stuck %.1f studs short at %s`, Label, Best, tostring(R.Position)))
	return nil
end
-- the pitch's north gap (the low wall leaves x -203..-195 open at z 101); start 10 studs outside it
local A = walk(Vector3.new(-199, 4.5, 90), Vector3.new(-199, 4.5, 112), `pitch gap`)
local A2 = A and walk(R.Position, Vector3.new(-160, 4.5, 145), `pitch centre`)
-- the practice field (x -222..-128, z 198..244): in from its south side, past the old ball-only wall line
local B = walk(Vector3.new(-175, 4.5, 252), Vector3.new(-175, 4.5, 221), `practice`)
C:PivotTo(Home)
if #Bad > 0 then return `FAIL ` .. table.concat(Bad, `; `) end
return `PASS walked in: {A}, {A2}, {B}; character groups {table.concat(G, `,`)} all pass the ball walls`
