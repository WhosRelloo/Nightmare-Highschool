--[[
	BeastGaze (client). StarterPlayerScripts.Controllers.World.BeastGaze          (beasts kit; docs/Beasts.md)
	Some beasts freeze while a student is looking at them (the Night Stalker's Freeze, Config.Beasts Freeze). The server
	can't see your camera, so while one of those beasts is near, this sends where you're looking a few times a second
	(ReplicatedStorage.NHBeastGaze). Nothing is sent when none is around.
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local Shared = {}

local SEND_EVERY = 0.2
local NEAR = 90

function Shared.OnStart()
	task.spawn(function()
		local Remote = ReplicatedStorage:WaitForChild(`NHBeastGaze`, 60)
		if not Remote then return end
		local Player = Players.LocalPlayer
		while true do
			task.wait(SEND_EVERY)
			local Cam = workspace.CurrentCamera
			local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`)
			local Live = workspace:FindFirstChild(`Live`)
			local Folder = Live and Live:FindFirstChild(`NHBeasts`)
			if Cam and Root and Folder then
				local Near = false
				for _, M in Folder:GetChildren() do
					local R = M:IsA(`Model`) and M:GetAttribute(`NHFreezeOnGaze`) and M:FindFirstChild(`HumanoidRootPart`)
					if R and (R.Position - Root.Position).Magnitude <= NEAR then Near = true break end
				end
				if Near then Remote:FireServer(Cam.CFrame.Position, Cam.CFrame.LookVector) end
			end
		end
	end)
end

return Shared
