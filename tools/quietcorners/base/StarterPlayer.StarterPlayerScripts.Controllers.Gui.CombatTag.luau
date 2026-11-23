--[[
	CombatTag (client). Controllers.Gui.CombatTag
	While the player attribute CombatTagUntil is in the future: the DANGER tag (art/ui/hud/hud_tag.png, a rusted padlock
	with a crimson skull keyhole, crossed chains, barbed wire) with a countdown. It stamps in, a crimson glow beats behind it
	like a heartbeat, the last 5 s flicker faster, then it fades out. Reduce Motion: no stamp or beat, just fades.
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local TweenService = game:GetService(`TweenService`)

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))

local Player = Players.LocalPlayer
local C = Kit.Theme.Colors
local TAG_IMAGE = `rbxassetid://139674642691954`

local Shared = {}
local Ui = nil
local Shown = false

local function reduced() return Player:GetAttribute(`NHReducedMotion`) == true end

local function build()
	local G = Instance.new(`ScreenGui`)
	G.Name = `NHCombatTag`
	G.ResetOnSpawn = false
	G.DisplayOrder = 6
	Kit.AutoScale(G)
	local Root = Instance.new(`Frame`)
	Root.Name = `Tag`
	Root.AnchorPoint = Vector2.new(0, 0.5)
	Root.Position = UDim2.new(0, 34, 0.3, 0)
	Root.Size = UDim2.fromOffset(170, 230)
	Root.BackgroundTransparency = 1
	Root.Visible = false
	Root.Parent = G
	local Glow = Kit.Image(`Glow`, { Name = `Glow`; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0.5, 0, 0, 80); Size = UDim2.fromOffset(230, 230); ImageColor3 = C.Crimson; ImageTransparency = 0.5; ZIndex = 1; Parent = Root })
	local Emblem = Instance.new(`ImageLabel`)
	Emblem.Name = `Emblem`
	Emblem.BackgroundTransparency = 1
	Emblem.Image = TAG_IMAGE
	Emblem.AnchorPoint = Vector2.new(0.5, 0.5)
	Emblem.Position = UDim2.new(0.5, 0, 0, 80)
	Emblem.Size = UDim2.fromOffset(160, 160)
	Emblem.ZIndex = 2
	Emblem.Parent = Root
	local Scale = Instance.new(`UIScale`)
	Scale.Parent = Emblem
	local Word = Kit.Text({ Name = `Danger`; Text = `DANGER`; Font = Kit.Theme.Fonts.Title; TextSize = 30; TextColor3 = C.Danger;
		TextXAlignment = Enum.TextXAlignment.Center; AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 0, 158); Size = UDim2.fromOffset(200, 34); ZIndex = 3; Parent = Root })
	Kit.Emboss(Word, Color3.fromRGB(90, 10, 16), 2)
	local Time = Kit.Text({ Name = `Time`; Text = `30s`; Font = Kit.Theme.Fonts.Title; TextSize = 20; TextColor3 = C.TextDim;
		TextXAlignment = Enum.TextXAlignment.Center; AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 0, 192); Size = UDim2.fromOffset(120, 24); ZIndex = 3; Parent = Root })
	G.Parent = Player:WaitForChild(`PlayerGui`)
	return { Gui = G; Root = Root; Glow = Glow; Emblem = Emblem; Scale = Scale; Word = Word; Time = Time }
end

local function show()
	if Shown then return end
	Shown = true
	Ui.Root.Visible = true
	Kit.FadeIn(Ui.Root, 0.2)
	if not reduced() then
		Ui.Scale.Scale = 1.6
		TweenService:Create(Ui.Scale, TweenInfo.new(0.28, Enum.EasingStyle.Back), { Scale = 1 }):Play()
		pcall(Kit.PlaySound, `Stamp`)
	end
end

local function hide()
	if not Shown then return end
	Shown = false
	local Out = Kit.FadeOut(Ui.Root, 0.45)
	if Out then
		Out.Completed:Once(function()
			if not Shown then
				Ui.Root.Visible = false
				-- FadeOut leaves everything transparent: rebuild so the next FadeIn has real targets
				Ui.Gui:Destroy()
				Ui = build()
			end
		end)
	else
		Ui.Root.Visible = false
	end
end

function Shared.OnStart()
	Ui = build()
	RunService.Heartbeat:Connect(function()
		local Until = Player:GetAttribute(`CombatTagUntil`)
		local Left = if typeof(Until) == `number` then Until - workspace:GetServerTimeNow() else 0
		local Busy = Player:GetAttribute(`InMainMenu`) == true
		if Left > 0 and not Busy then
			show()
			Ui.Time.Text = `{math.ceil(Left)}s`
			local T = os.clock()
			local Rate = if Left < 5 then 3.2 else 1.15 -- heartbeat; faster near the end
			local Beat = math.max(0, math.sin(T * math.pi * Rate)) ^ 6
			if not reduced() then
				Ui.Emblem.Rotation = math.sin(T * 1.3) * 1.5
				if Shown and Ui.Scale.Scale <= 1.01 then Ui.Scale.Scale = 1 + Beat * 0.05 end
			end
			Ui.Glow.ImageTransparency = 0.62 - Beat * 0.3
			Ui.Word.TextTransparency = if Left < 5 and math.sin(T * 18) > 0.6 then 0.45 else 0
		else
			hide()
		end
	end)
end

return Shared
