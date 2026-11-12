--[[
	Lunch trays (client). Controllers.World.TrayFx                          (props batch 54, 2026-11-12)
	Server: Services.Features.Tray (it poses both shoulders through their C0 and welds the tray to the torso).

	A character carrying a tray (tag NHTrayHolder) keeps both posed shoulders still against the walk, run, jump and idle
	clips: after the animations run, their Transform is cleared, like the kit's holds (World.KitFx). While a tray clip
	that moves the arms plays (NHTrayAnim), the shoulders are left to it. Players and NPCs alike, within MAX_DIST.
]]
local CollectionService = game:GetService(`CollectionService`)
local RunService = game:GetService(`RunService`)

local Shared = {}
local Local = {}

local MAX_DIST = 150

function Local.Steady()
	local Cam = workspace.CurrentCamera
	local Eye = Cam and Cam.CFrame.Position or Vector3.zero
	for _, Char in CollectionService:GetTagged(`NHTrayHolder`) do
		if not Char:IsA(`Model`) or Char:GetAttribute(`NHTrayAnim`) then continue end
		local Torso = Char:FindFirstChild(`Torso`) :: BasePart?
		if not Torso or (Torso.Position - Eye).Magnitude > MAX_DIST then continue end
		for _, Side in { `Right Shoulder`, `Left Shoulder` } do
			local M = Torso:FindFirstChild(Side)
			if M and M:IsA(`Motor6D`) then M.Transform = CFrame.identity end
		end
	end
end

function Shared.OnStart()
	RunService.PreSimulation:Connect(function()
		local Ok, Err = pcall(Local.Steady)
		if not Ok then warn(`[TrayFx] {Err}`) end
	end)
end

return Shared
