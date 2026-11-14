--[[
	Crypt Crush. Controllers.Gui.PhoneGames.Crypt   (run by Controllers.Gui.PhoneGames; rules in PhoneGames.CryptBoard)
	An 8x8 crypt slab of runes in six kinds, each its own colour and shape: a crimson blood drop, a gold candle, a
	violet square, a bone cross, a blue quill and a green skull-bell. Tap a rune then a neighbour (or drag it
	onto one) to swap them; only swaps that line up three or more stick. Lines clear, the runes above fall and new
	ones drop in, and every cascade multiplies the points. A line of four leaves a sigil (a ringed rune: when it
	clears, so do its row and column); a line of five leaves a wax seal (swap it with any rune to clear that whole
	colour). 30 moves a run; when no move is left the runes reshuffle.
]]
local Board = require(script.Parent:WaitForChild(`CryptBoard`))

local Crypt = {}
Crypt.Name = `Crypt Crush`
Crypt.HowTo = `Swap neighbouring runes to line up three or more. Four makes a sigil, five a seal. You have 30 moves.`
Crypt.Over = `The crypt seals shut`

local MOVES = 30
local RUNES = {
	{ Image = `IconDrop`; Tint = Color3.fromRGB(232, 56, 72); Scale = 0.74 },
	{ Image = `IconCandle`; Tint = Color3.fromRGB(244, 198, 92); Scale = 0.8 },
	{ Image = `Pip`; Tint = Color3.fromRGB(178, 112, 246); Scale = 0.54; Rotation = 45 },
	{ Image = `IconCross`; Tint = Color3.fromRGB(240, 234, 214); Scale = 0.74 },
	{ Image = `IconNib`; Tint = Color3.fromRGB(96, 164, 250); Scale = 0.74 },
	{ Image = `Bell`; Tint = Color3.fromRGB(118, 210, 122); Scale = 0.8 },
}
Crypt.Runes = RUNES

function Crypt.New(Ctx)
	local new = Ctx.new
	local Kit = Ctx.Kit
	local C = Ctx.Theme.Colors
	local Self = {}
	local St = nil

	function Self:Stop()
		if St then
			if St.Scene then St.Scene:Destroy() end
			if St.MovesBox then St.MovesBox:Destroy() end
		end
		St = nil
	end

	local function at(R: number, Col: number): UDim2
		return UDim2.fromOffset((Col - 0.5) * St.Cell, (R - 0.5) * St.Cell)
	end

	function Self:View(P, R: number, Col: number)
		local Cell = St.Cell
		local V = new(`Frame`, { Name = `Rune`; BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0.5); Position = at(R, Col); Size = UDim2.fromOffset(Cell, Cell); ZIndex = 2 }, St.Pieces)
		new(`UIScale`, {}, V)
		if P.S == `Seal` then
			Kit.Image(`Glow`, { AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(1.35, 1.35); ImageColor3 = Color3.fromRGB(255, 210, 120); ImageTransparency = 0.3; ScaleType = Enum.ScaleType.Stretch; ZIndex = 1; Parent = V })
			Kit.Image(`IconCryptRune`, { AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(0.92, 0.92); ImageColor3 = Color3.new(1, 1, 1); ZIndex = 2; Parent = V })
			-- (the rune's own crimson gem marks the centre)
			return V
		end
		local Rune = RUNES[P.K] or RUNES[1]
		local Scale = Rune.Scale
		if P.S == `Sigil` then
			Kit.Image(`Glow`, { AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(1.3, 1.3); ImageColor3 = Rune.Tint; ImageTransparency = 0.35; ScaleType = Enum.ScaleType.Stretch; ZIndex = 1; Parent = V })
			Kit.Image(`OrbRing`, { AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(1, 1); ImageColor3 = Color3.fromRGB(240, 212, 130); ZIndex = 2; Parent = V })
			Scale *= 0.78
		end
		Kit.Image(Rune.Image, { Name = `Icon`; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(Scale, Scale); Rotation = Rune.Rotation or 0; ImageColor3 = Rune.Tint; ZIndex = 3; Parent = V })
		return V
	end

	function Self:Rebuild(Fade: boolean?)
		for _, V in St.Views do V:Destroy() end
		St.Views = {}
		for R = 1, St.G.N do
			for Col = 1, St.G.N do
				local P = St.G.Cells[R][Col]
				if P then
					local V = Self:View(P, R, Col)
					St.Views[P.Id] = V
					if Fade and not Ctx.Reduced() then
						local Sc = V:FindFirstChildOfClass(`UIScale`)
						Sc.Scale = 0.2
						Ctx.tween(Sc, 0.25 + (R + Col) * 0.012, { Scale = 1 }, Enum.EasingStyle.Back)
					end
				end
			end
		end
	end

	function Self:Reset()
		Self:Stop()
		local W, H = Ctx.Size()
		local Cell = math.floor(math.min(W - 28, H - 190) / 8)
		local Span = Cell * 8
		local Bx, By = math.floor((W - Span) / 2), 66
		local Scene = new(`Frame`, { Name = `Crypt`; BackgroundColor3 = Color3.new(1, 1, 1); BorderSizePixel = 0; Size = UDim2.fromScale(1, 1) }, Ctx.Field)
		new(`UIGradient`, { Rotation = 90; Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(12, 10, 16)), ColorSequenceKeypoint.new(1, Color3.fromRGB(30, 22, 34)) }) }, Scene)
		new(`ImageLabel`, { BackgroundTransparency = 1; Image = Ctx.Theme.Images.PanelBg; ImageColor3 = Color3.fromRGB(70, 60, 80); ImageTransparency = 0.6; ScaleType = Enum.ScaleType.Tile; TileSize = UDim2.fromOffset(200, 200); Size = UDim2.fromScale(1, 1); ZIndex = 1 }, Scene)
		-- the slab: dark stone, a gilt rim, a well for every cell
		local Slab = new(`Frame`, { Name = `Slab`; BackgroundColor3 = Color3.fromRGB(18, 14, 22); BorderSizePixel = 0; Position = UDim2.fromOffset(Bx - 8, By - 8); Size = UDim2.fromOffset(Span + 16, Span + 16); ZIndex = 2 }, Scene)
		new(`UICorner`, { CornerRadius = UDim.new(0, 12) }, Slab)
		new(`UIStroke`, { Color = C.GoldDeep; Thickness = 1.5; Transparency = 0.15 }, Slab)
		local Grain = new(`ImageLabel`, { BackgroundTransparency = 1; Image = Ctx.Theme.Images.PanelBg; ImageColor3 = C.PanelTint; ImageTransparency = 0.45; ScaleType = Enum.ScaleType.Tile; TileSize = UDim2.fromOffset(160, 160); Size = UDim2.fromScale(1, 1); ZIndex = 0 }, Slab)
		new(`UICorner`, { CornerRadius = UDim.new(0, 12) }, Grain)
		local Grid = new(`Frame`, { Name = `Grid`; BackgroundTransparency = 1; ClipsDescendants = true; Position = UDim2.fromOffset(8, 8); Size = UDim2.fromOffset(Span, Span); ZIndex = 2 }, Slab)
		for R = 1, 8 do
			for Col = 1, 8 do
				Kit.Image(`SlotBg`, { AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromOffset((Col - 0.5) * Cell, (R - 0.5) * Cell); Size = UDim2.fromOffset(Cell - 2, Cell - 2);
					ScaleType = Enum.ScaleType.Stretch; ImageColor3 = if (R + Col) % 2 == 0 then Color3.fromRGB(78, 68, 88) else Color3.fromRGB(64, 56, 74); ZIndex = 1; Parent = Grid })
			end
		end
		local Sel = new(`Frame`, { Name = `Selected`; BackgroundColor3 = C.Gold; BackgroundTransparency = 0.82; BorderSizePixel = 0; AnchorPoint = Vector2.new(0.5, 0.5); Size = UDim2.fromOffset(Cell - 2, Cell - 2); Visible = false; ZIndex = 2 }, Grid)
		new(`UICorner`, { CornerRadius = UDim.new(0, 6) }, Sel)
		new(`UIStroke`, { Color = C.Gold; Thickness = 2 }, Sel)
		local Pieces = new(`Frame`, { Name = `Pieces`; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1); ZIndex = 3 }, Grid)
		local Fx = new(`Frame`, { Name = `Fx`; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1); ZIndex = 4 }, Grid)
		-- below the slab: the rules in a line, and the cascade call
		local Low = By + Span + 16
		Kit.Text({ Text = `Line up <font color="#ebcd78">4</font> for a sigil (clears its row and column), <font color="#ebcd78">5</font> for a seal (swap it to clear a colour).`;
			TextSize = 14; TextWrapped = true; TextColor3 = Color3.fromRGB(205, 196, 186); TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(20, Low); Size = UDim2.new(1, -40, 0, 40); ZIndex = 3; Parent = Scene })
		local Call = Kit.Text({ Text = ``; Font = Enum.Font.Fantasy; TextSize = 26; TextColor3 = Color3.fromRGB(255, 214, 120); TextStrokeTransparency = 0.25; TextXAlignment = Enum.TextXAlignment.Center;
			AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 0, Low + 48); Size = UDim2.fromOffset(260, 34); TextTransparency = 1; ZIndex = 3; Parent = Scene })
		-- moves left, in the HUD
		local Box = new(`Frame`, { Name = `Moves`; BackgroundTransparency = 1; Position = UDim2.fromOffset(12, 8); Size = UDim2.fromOffset(80, 44); ZIndex = 9 }, Ctx.Hud)
		Kit.Text({ Text = `MOVES`; Font = Enum.Font.Fantasy; TextSize = 12; TextColor3 = Color3.fromRGB(214, 178, 112); TextXAlignment = Enum.TextXAlignment.Left; Size = UDim2.new(1, 0, 0, 14); Parent = Box })
		local MovesLabel = Kit.Text({ Text = tostring(MOVES); Font = Enum.Font.Fantasy; TextSize = 24; TextColor3 = C.Text; TextXAlignment = Enum.TextXAlignment.Left; Position = UDim2.fromOffset(0, 14); Size = UDim2.new(1, 0, 0, 28); Parent = Box })
		local Rng = Random.new()
		St = { Scene = Scene; Grid = Grid; Pieces = Pieces; Fx = Fx; SelFrame = Sel; Call = Call; MovesBox = Box; MovesLabel = MovesLabel;
			Cell = Cell; Bx = Bx; By = By; Rng = Rng; G = Board.New(Rng); Views = {}; Moves = MOVES; Busy = false; Done = true; Running = false; Sel = nil; Down = nil }
		Self:Rebuild(false)
	end

	function Self:Start()
		if not St then return end
		St.Moves = MOVES
		St.MovesLabel.Text = tostring(MOVES)
		St.Done = false
		St.Running = true
	end

	function Self:Highlight()
		local Sel = St.Sel
		St.SelFrame.Visible = Sel ~= nil
		if Sel then St.SelFrame.Position = at(Sel[1], Sel[2]) end
	end

	function Self:CellAt(P: Vector2)
		local Col = math.floor((P.X - St.Bx) / St.Cell) + 1
		local R = math.floor((P.Y - St.By) / St.Cell) + 1
		if R < 1 or R > St.G.N or Col < 1 or Col > St.G.N then return nil end
		return { R, Col }
	end

	function Self:Say(Text: string)
		St.Call.Text = Text
		St.Call.TextTransparency = 0
		St.Call.TextStrokeTransparency = 0.25
		Ctx.tween(St.Call, 0.8, { TextTransparency = 1, TextStrokeTransparency = 1 }, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
	end

	-- pop the cleared runes, flash the blasts, stamp in the new specials, score
	function Self:Show(S, Result): boolean
		local Reduced = Ctx.Reduced()
		for _, Cl in Result.Cleared do
			local V = S.Views[Cl.Piece.Id]
			S.Views[Cl.Piece.Id] = nil
			if V then
				if not Reduced then Ctx.tween(V:FindFirstChildOfClass(`UIScale`), 0.16, { Scale = 1.35 }) end
				for _, Im in V:GetChildren() do if Im:IsA(`ImageLabel`) then Ctx.tween(Im, 0.16, { ImageTransparency = 1 }) end end
				task.delay(0.18, function() V:Destroy() end)
			end
		end
		for _, B in Result.Blasts do
			if B.Kind == `Cross` then
				for _, Line in { { UDim2.fromOffset(S.Cell * 4, (B.R - 0.5) * S.Cell), UDim2.fromOffset(S.Cell * 8, S.Cell * 0.7) }, { UDim2.fromOffset((B.C - 0.5) * S.Cell, S.Cell * 4), UDim2.fromOffset(S.Cell * 0.7, S.Cell * 8) } } do
					local F = new(`Frame`, { BackgroundColor3 = Color3.fromRGB(255, 220, 140); BackgroundTransparency = 0.35; BorderSizePixel = 0; AnchorPoint = Vector2.new(0.5, 0.5); Position = Line[1]; Size = Line[2]; ZIndex = 1 }, S.Fx)
					Ctx.tween(F, 0.35, { BackgroundTransparency = 1 })
					task.delay(0.36, function() F:Destroy() end)
				end
			else
				local G = Kit.Image(`Glow`, { AnchorPoint = Vector2.new(0.5, 0.5); Position = at(B.R, B.C); Size = UDim2.fromOffset(S.Cell * 2, S.Cell * 2); ImageColor3 = Color3.fromRGB(255, 220, 150); ImageTransparency = 0.2; ScaleType = Enum.ScaleType.Stretch; ZIndex = 1; Parent = S.Fx })
				Ctx.tween(G, 0.45, { Size = if Reduced then G.Size else UDim2.fromOffset(S.Cell * 9, S.Cell * 9), ImageTransparency = 1 })
				task.delay(0.46, function() G:Destroy() end)
			end
		end
		for _, Cr in Result.Created do
			local V = Self:View(Cr.Piece, Cr.R, Cr.C)
			S.Views[Cr.Piece.Id] = V
			local Sc = V:FindFirstChildOfClass(`UIScale`)
			if Reduced then
				for _, Im in V:GetChildren() do if Im:IsA(`ImageLabel`) then local T = Im.ImageTransparency Im.ImageTransparency = 1 Ctx.tween(Im, 0.2, { ImageTransparency = T }) end end
			else
				Sc.Scale = 1.8
				Ctx.tween(Sc, 0.25, { Scale = 1 }, Enum.EasingStyle.Back)
			end
		end
		if #Result.Created > 0 then Ctx.Sound(`Stamp`, 0.45) end
		if #Result.Blasts > 0 then Ctx.Sound(`Boom`, 0.25, 1.4) end
		Ctx.Sound(`Tick`, 0.35, 1 + math.min(Result.Chain, 6) * 0.12)
		Ctx.Add(Result.Points)
		if Result.Chain >= 2 then Self:Say(`Chain \u{00D7}{Result.Chain}`) end
		return Ctx.Wait(0.2)
	end

	-- everything slides to its cell; new runes drop in from above the slab
	function Self:Drop(S, Spawned): boolean
		for _, Sp in Spawned do
			local V = Self:View(Sp.Piece, Sp.From, Sp.C)
			S.Views[Sp.Piece.Id] = V
		end
		for R = 1, S.G.N do
			for Col = 1, S.G.N do
				local P = S.G.Cells[R][Col]
				local V = P and S.Views[P.Id]
				if V and V.Position ~= at(R, Col) then Ctx.tween(V, 0.2, { Position = at(R, Col) }, Enum.EasingStyle.Quad, Enum.EasingDirection.In) end
			end
		end
		return Ctx.Wait(0.22)
	end

	function Self:Turn(S, A, B)
		local G = S.G
		local P, Q = Board.Get(G, A[1], A[2]), Board.Get(G, B[1], B[2])
		if not (P and Q) then return end
		local VA, VB = S.Views[P.Id], S.Views[Q.Id]
		local Seal = Board.IsSeal(P) or Board.IsSeal(Q)
		local Valid = Seal or Board.CanSwap(G, A, B)
		if VA then Ctx.tween(VA, 0.14, { Position = at(B[1], B[2]) }) end
		if VB then Ctx.tween(VB, 0.14, { Position = at(A[1], A[2]) }) end
		if not Ctx.Wait(0.15) then return end
		if not Valid then
			if VA then Ctx.tween(VA, 0.14, { Position = at(A[1], A[2]) }) end
			if VB then Ctx.tween(VB, 0.14, { Position = at(B[1], B[2]) }) end
			Ctx.Sound(`Reject`, 0.4)
			Ctx.Wait(0.15)
			return
		end
		Board.Swap(G, A, B)
		S.Moves -= 1
		S.MovesLabel.Text = tostring(S.Moves)
		S.MovesLabel.TextColor3 = if S.Moves <= 5 then Color3.fromRGB(235, 110, 120) else C.Text
		local Result = if Seal then Board.SealBurst(G, A, B, 1) else Board.Resolve(G, { A, B }, 1)
		local Chain = 1
		while Result do
			if not Self:Show(S, Result) then return end
			local _, Spawned = Board.Collapse(G, S.Rng)
			if not Self:Drop(S, Spawned) then return end
			Chain += 1
			Result = Board.Resolve(G, nil, Chain)
		end
		if not Board.HasMoves(G) then
			Self:Say(`The runes shift`)
			Board.Shuffle(G, S.Rng)
			Self:Rebuild(true)
			if not Ctx.Wait(0.4) then return end
		end
		if S.Moves <= 0 then
			S.Done = true
			if Ctx.Wait(0.5) then Ctx.Over() end
		end
	end

	function Self:Attempt(A, B)
		local S = St
		if not S or S.Busy or S.Done then return end
		S.Sel = nil
		S.Down = nil
		Self:Highlight()
		if not Board.InBounds(S.G, B) then return end
		S.Busy = true
		task.spawn(function()
			local Ok, Err = pcall(Self.Turn, Self, S, A, B)
			if not Ok then warn(`Crypt Crush: {Err}`) end
			S.Busy = false
		end)
	end

	function Self:Step(_Dt: number) end

	function Self:Press(P: Vector2)
		if not (St and St.Running) or St.Busy or St.Done then return end
		local Cell = Self:CellAt(P)
		if not Cell then St.Sel = nil Self:Highlight() return end
		local Sel = St.Sel
		if Sel and Board.Adjacent(Sel, Cell) then Self:Attempt(Sel, Cell) return end
		if Sel and Sel[1] == Cell[1] and Sel[2] == Cell[2] then
			St.Sel = nil
			St.Down = nil
		else
			St.Sel = Cell
			St.Down = { Cell = Cell; P = P }
			Ctx.Sound(`Tick`, 0.2, 1.8)
		end
		Self:Highlight()
	end

	function Self:Move(P: Vector2)
		if not (St and St.Down) or St.Busy or St.Done then return end
		local D = P - St.Down.P
		if D.Magnitude < St.Cell * 0.45 then return end
		local A = St.Down.Cell
		local B = if math.abs(D.X) > math.abs(D.Y) then { A[1], A[2] + (if D.X > 0 then 1 else -1) } else { A[1] + (if D.Y > 0 then 1 else -1), A[2] }
		Self:Attempt(A, B)
	end

	function Self:Release(_P: Vector2?)
		if St then St.Down = nil end
	end

	return Self
end

return Crypt
