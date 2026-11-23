--[[
	Notifications (client)
	Toast stack at the top-center of the screen. Fed by Packets.Notify from the server.
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local TweenService = game:GetService(`TweenService`)

---| Modules |---

local Packets = require(ReplicatedStorage.Remotes.Packets)
local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`)) -- NH UI kit

local Player = Players.LocalPlayer
local MAX_TOASTS = 4

local KIND_COLORS = Kit.ToastColors -- Info / Good / Warning / Bad

local Local = {}
local Shared = {}

function Local.CreateGui(): Frame
	local Gui = Instance.new(`ScreenGui`)
	Kit.AutoScale(Gui) -- scale toasts like every other kit screen
	Gui.Name = `Notifications`
	Gui.ResetOnSpawn = false
	Gui.DisplayOrder = 10

	local Holder = Instance.new(`Frame`)
	Holder.Name = `Holder`
	Holder.AnchorPoint = Vector2.new(0.5, 0)
	Holder.Position = UDim2.new(0.5, 0, 0, 72) -- below the top-centre compass
	Holder.Size = UDim2.new(0, 380, 0, 300)
	Holder.BackgroundTransparency = 1
	Holder.Parent = Gui

	local Layout = Instance.new(`UIListLayout`)
	Layout.SortOrder = Enum.SortOrder.LayoutOrder
	Layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	Layout.Padding = UDim.new(0, 6)
	Layout.Parent = Holder

	Gui.Parent = Player:WaitForChild(`PlayerGui`)
	return Holder
end

local Order = 0

function Local.Show(Holder: Frame, Data)
	Order += 1

	local Toasts = {}
	for _, Child in Holder:GetChildren() do
		if Child:IsA(`Frame`) and Child.Name == `Toast` then table.insert(Toasts, Child) end
	end
	table.sort(Toasts, function(A, B) return A.LayoutOrder < B.LayoutOrder end)
	while #Toasts >= MAX_TOASTS do -- the oldest fades out instead of popping
		local Old = table.remove(Toasts, 1)
		Old.Name = `Evicting`
		Kit.FadeOut(Old, 0.15).Completed:Connect(function() Old:Destroy() end)
	end

	-- Kind: Info / Good / Warning / Bad, or Milestone (level-up, quest complete, faction join / rank,
	-- purchases): a gold toast whose seal stamps in, with a shimmer across the title.
	local Kind = Data.Kind
	local Accent = KIND_COLORS[Kind] or KIND_COLORS.Info

	local Toast, Api = Kit.Toast({
		title = Data.Title or ``; text = Data.Text; color = Accent; kind = Kind;
		Name = `Toast`; LayoutOrder = Order;
	})
	Toast.Parent = Holder
	if Api and Api.Play then Api:Play() end

	task.delay(Data.Duration or (if Kind == `Milestone` then 6 else 4), function()
		if not Toast.Parent then return end
		local Fade = Kit.FadeOut(Toast, 0.3)
		Fade.Completed:Wait()
		Toast:Destroy()
	end)
end

function Shared.OnStart()
	local Holder = Local.CreateGui()
	Packets.Notify.OnClientEvent:Connect(function(Data)
		if typeof(Data) ~= `table` then return end
		Local.Show(Holder, Data)
	end)
end

return Shared
