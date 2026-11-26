--[[
	History: "Match the Past" screen (memory game).
	Face-down index cards; tap two to flip them (a controller: D-pad and A). Match each event to its era. Cards only reveal
	their text when the server flips them, so the layout can't be read ahead of time.
]]

local TweenService = game:GetService(`TweenService`)

local Memory = {}
Memory.__index = Memory

function Memory.new(Content: Frame, Payload, Api)
	local self = setmetatable({ Api = Api; Content = Content; Cards = {}; Busy = false; Pairs = Payload.Pairs }, Memory)
	local Theme = Api.Theme

	self.Status = Api.Label(Content, {
		Font = Theme.HandFont; TextColor3 = Theme.ChalkDim; Size = UDim2.fromScale(1, 0.07);
		Text = `Find all {Payload.Pairs} pairs. Each event goes with its era.`;
	})

	local Grid = Instance.new(`Frame`)
	Grid.BackgroundTransparency = 1
	Grid.Position = UDim2.fromScale(0.02, 0.1)
	Grid.Size = UDim2.fromScale(0.96, 0.88)
	Grid.Parent = Content

	local Columns = Payload.Columns or 4
	local Rows = math.ceil(Payload.CardCount / Columns)
	local Layout = Instance.new(`UIGridLayout`)
	Layout.CellPadding = UDim2.fromScale(0.02, 0.03)
	Layout.CellSize = UDim2.fromScale(1 / Columns - 0.02, 1 / Rows - 0.03)
	Layout.SortOrder = Enum.SortOrder.LayoutOrder
	Layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	Layout.Parent = Grid

	for Index = 1, Payload.CardCount do
		local Card = Api.Button(Grid, `?`, {
			Name = `Card{Index}`; LayoutOrder = Index; Font = Theme.TitleFont; TextColor3 = Theme.ChalkYellow;
			Rotation = math.random(-15, 15) / 10;
		})
		local Limit = Instance.new(`UITextSizeConstraint`)
		Limit.MaxTextSize = 34
		Limit.Parent = Card

		-- face-down: the card back (IconCardBack) behind the "?"
		local Back = Instance.new(`ImageLabel`)
		Back.Name = `Back`
		Back.BackgroundTransparency = 1
		local SealId = Api.Theme.SealImage
		Back.Image = SealId or ``
		Back.ImageColor3 = Color3.new(1, 1, 1)
		Back.ImageTransparency = 0.15
		Back.AnchorPoint = Vector2.new(0.5, 0.5)
		Back.Position = UDim2.fromScale(0.5, 0.5)
		Back.Size = UDim2.fromScale(0.8, 0.8)
		local BackAspect = Instance.new(`UIAspectRatioConstraint`)
		BackAspect.Parent = Back
		Back.Parent = Card

		local Tag = Api.Label(Card, {
			Font = Theme.HandFont; TextColor3 = Theme.Ink; Position = UDim2.fromScale(0, -0.05); Size = UDim2.fromScale(1, 0.22);
			Visible = false; TextTransparency = 0.3;
		})
		Card.Activated:Connect(function() self:Flip(Index) end)
		Card:SetAttribute(`NHPadFirst`, true)
		self.Cards[Index] = { Button = Card; Tag = Tag; Limit = Limit; Back = Back; FaceUp = false; Matched = false }
	end

	Api.SetScore(`Pairs: 0/{Payload.Pairs}`)
	return self
end

function Memory:SetFace(Index: number, Text: string?, Kind: string?)
	local Theme = self.Api.Theme
	local Card = self.Cards[Index]
	if not Card then return end

	if Text then
		Card.FaceUp = true
		Card.Button.Text = Text
		Card.Button.Font = Theme.HandFont
		Card.Button.TextColor3 = Theme.Ink
		Card.Button.BackgroundColor3 = Theme.Paper
		Card.Limit.MaxTextSize = 22
		Card.Tag.Text = if Kind == `Era` then `ERA` else `EVENT`
		Card.Tag.Visible = true
		if Card.Back then Card.Back.Visible = false end
	else
		Card.FaceUp = false
		Card.Button.Text = `?`
		Card.Button.Font = Theme.TitleFont
		Card.Button.TextColor3 = Theme.ChalkYellow
		Card.Button.BackgroundColor3 = Theme.BoardDark
		Card.Limit.MaxTextSize = 34
		Card.Tag.Visible = false
		if Card.Back then Card.Back.Visible = true end
	end
	self.Api.Pop(Card.Button, 1.08)
end

function Memory:Flip(Index: number)
	local Card = self.Cards[Index]
	if self.Busy or not Card or Card.FaceUp or Card.Matched then return end
	self.Busy = true
	self.Api.Send(`Flip`, { Index = Index })
	-- Safety: never stay locked if a reply goes missing.
	local Token = {}
	self.BusyToken = Token
	task.delay(2, function() if self.BusyToken == Token then self.Busy = false end end)
end

function Memory:Update(Reply)
	local Theme = self.Api.Theme
	self.BusyToken = nil
	self:SetFace(Reply.Index, Reply.Text, Reply.Kind)

	if Reply.Stage == `First` then
		self.Busy = false
		return
	end

	local A, B = self.Cards[Reply.FirstIndex], self.Cards[Reply.Index]
	self.Api.SetScore(`Pairs: {Reply.Matched}/{self.Pairs}`)
	self.Status.Text = `Pairs {Reply.Matched}/{self.Pairs}  ·  Misses {Reply.Mistakes}`

	if Reply.Match then
		for _, Card in { A, B } do
			if Card then
				Card.Matched = true
				TweenService:Create(Card.Button, TweenInfo.new(0.25), { BackgroundColor3 = Color3.fromRGB(205, 240, 205) }):Play()
				self.Api.Pop(Card.Button, 1.15)
			end
		end
		self.Busy = false
		if self.Api.Sound then self.Api.Sound(`Correct`, Reply.Matched); self.Api.Burst(B and B.Button, true) end
	else
		if self.Api.Sound then self.Api.Sound(`Wrong`); self.Api.Burst(B and B.Button, false) end
		self.Api.Shake()
		task.delay(0.9, function()
			if self.Destroyed then return end
			self:SetFace(Reply.FirstIndex, nil)
			self:SetFace(Reply.Index, nil)
			self.Busy = false
		end)
	end
end

function Memory:Destroy()
	self.Destroyed = true
end

return Memory
