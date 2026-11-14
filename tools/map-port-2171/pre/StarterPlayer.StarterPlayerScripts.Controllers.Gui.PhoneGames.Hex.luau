--[[
	Hex Slash. Controllers.Gui.PhoneGames.Hex   (run by Controllers.Gui.PhoneGames)
	Cursed relics are tossed up from below the altar in arcs: wax candles, blood drops, gold wax seals, quills
	and skull-bells. Press and drag across the stage to slash: a short crimson trail follows the pointer, and any
	relic the stroke passes through while it's moving fast enough splits in two (+1). Three or more relics in one
	stroke is a combo (+1 more for each). A relic that falls back out of sight unslashed snuffs one of your three
	candles. The pale holy cross is not for you: slash it and the run ends in a white flash (a soft one with
	Reduce Motion or Reduce Flashing). Throws come faster and fuller as the run goes on.
]]
local Hex = {}
Hex.Name = `Hex Slash`
Hex.HowTo = `Press and drag to slash the cursed relics. Don't let them fall, and never strike the holy cross.`
Hex.Over = `The candles burn out`

local GRAVITY = 560
local SIZE = 54
local HIT_R = 24 -- a relic's slash radius
local SLASH_SPEED = 380 -- px/s: slower strokes don't cut
local TRAIL = 16
local LIVES = 3
local RELICS = {
	{ Image = `IconCandle`; Tint = Color3.fromRGB(242, 228, 196) },
	{ Image = `IconDrop`; Tint = Color3.fromRGB(214, 44, 62) },
	{ Image = `Seal`; Tint = Color3.fromRGB(235, 200, 110) },
	{ Image = `IconNib`; Tint = Color3.fromRGB(176, 196, 236) },
	{ Image = `Bell`; Tint = Color3.fromRGB(206, 196, 176) },
}
local CROSS = { Image = `IconCross`; Tint = Color3.fromRGB(240, 246, 255); Bomb = true }

-- does the segment A->B pass within R of the point P?
local function nearSegment(A: Vector2, B: Vector2, P: Vector2, R: number): boolean
	local AB = B - A
	local L2 = AB:Dot(AB)
	local T = if L2 > 0 then math.clamp((P - A):Dot(AB) / L2, 0, 1) else 0
	return (A + AB * T - P).Magnitude <= R
end
Hex.NearSegment = nearSegment

-- the wave plan at time T: seconds until the next throw, how many relics, the chance each one is a cross
function Hex.Plan(T: number): (number, number, number)
	local Gap = math.max(0.7, 1.5 - T * 0.012)
	local Count = math.min(5, 1 + math.floor(math.min(T, 80) / 20))
	local Bomb = if T < 8 then 0 else math.min(0.24, 0.1 + T * 0.002)
	return Gap, Count, Bomb
end

function Hex.New(Ctx)
	local new = Ctx.new
	local Kit = Ctx.Kit
	local Self = {}
	local Rng = Random.new()
	local St = nil

	function Self:Stop()
		if St and St.Scene then St.Scene:Destroy() end
		if St and St.LifeRow then St.LifeRow:Destroy() end
		St = nil
	end

	function Self:Reset()
		Self:Stop()
		local W, H = Ctx.Size()
		local Scene = new(`Frame`, { Name = `Hex`; BackgroundColor3 = Color3.new(1, 1, 1); BorderSizePixel = 0; Size = UDim2.fromScale(1, 1) }, Ctx.Field)
		new(`UIGradient`, { Rotation = 90; Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(10, 6, 12)), ColorSequenceKeypoint.new(0.55, Color3.fromRGB(34, 8, 18)), ColorSequenceKeypoint.new(1, Color3.fromRGB(60, 12, 22)) }) }, Scene)
		-- the altar: a faint wax seal pressed into the dark, slate grain, a gilt rail and a row of vigil lights
		Kit.Image(`Seal`, { AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.46); Size = UDim2.fromOffset(W * 0.8, W * 0.8); ImageColor3 = Color3.fromRGB(120, 24, 34); ImageTransparency = 0.86; ZIndex = 1; Parent = Scene })
		new(`ImageLabel`, { BackgroundTransparency = 1; Image = Ctx.Theme.Images.PanelBg; ImageColor3 = Color3.fromRGB(70, 40, 56); ImageTransparency = 0.7; ScaleType = Enum.ScaleType.Tile; TileSize = UDim2.fromOffset(200, 200); Size = UDim2.fromScale(1, 1); ZIndex = 1 }, Scene)
		local Rail = new(`Frame`, { BackgroundColor3 = Color3.fromRGB(26, 8, 14); BorderSizePixel = 0; Position = UDim2.fromOffset(0, H - 34); Size = UDim2.new(1, 0, 0, 34); ZIndex = 2 }, Scene)
		new(`Frame`, { BackgroundColor3 = Color3.fromRGB(150, 112, 50); BackgroundTransparency = 0.35; BorderSizePixel = 0; Size = UDim2.new(1, 0, 0, 2) }, Rail)
		for I = 1, 7 do
			local X = W * (I - 0.5) / 7
			Kit.Image(`Glow`, { AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromOffset(X, H - 30); Size = UDim2.fromOffset(34, 34); ImageColor3 = Color3.fromRGB(255, 170, 80); ImageTransparency = 0.55; ScaleType = Enum.ScaleType.Stretch; ZIndex = 3; Parent = Scene })
			Kit.Image(`IconCandle`, { AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.fromOffset(X, H - 4); Size = UDim2.fromOffset(18, 26); ImageColor3 = Color3.fromRGB(200, 180, 150); ImageTransparency = 0.25; ZIndex = 3; Parent = Scene })
		end
		local Relics = new(`Frame`, { Name = `Relics`; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1); ZIndex = 4 }, Scene)
		local Bits = new(`Frame`, { Name = `Bits`; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1); ZIndex = 5 }, Scene)
		local TrailLayer = new(`Frame`, { Name = `Trail`; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1); ZIndex = 6 }, Scene)
		-- lives: three small candles in the corner (in the HUD, so they show only during a run)
		local LifeRow = new(`Frame`, { Name = `Lives`; BackgroundTransparency = 1; Position = UDim2.fromOffset(12, 14); Size = UDim2.fromOffset(90, 30); ZIndex = 9 }, Ctx.Hud)
		local Lives = {}
		for I = 1, LIVES do
			Kit.Image(`Glow`, { Name = `Glow{I}`; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromOffset(12 + (I - 1) * 26, 8); Size = UDim2.fromOffset(26, 26); ImageColor3 = Color3.fromRGB(255, 170, 80); ImageTransparency = 0.4; ScaleType = Enum.ScaleType.Stretch; ZIndex = 1; Parent = LifeRow })
			Lives[I] = Kit.Image(`IconCandle`, { AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.fromOffset(12 + (I - 1) * 26, 2); Size = UDim2.fromOffset(20, 26); ImageColor3 = Color3.fromRGB(242, 228, 196); ZIndex = 2; Parent = LifeRow })
		end
		St = { Scene = Scene; W = W; H = H; Relics = {}; Bits = {}; Trail = {}; RelicLayer = Relics; BitLayer = Bits; TrailLayer = TrailLayer;
			LifeRow = LifeRow; LifeIcons = Lives; Lives = LIVES; T = 0; Next = 0.8; Queue = {}; Running = false; Dead = false; DeadT = 0;
			Down = false; Last = nil; LastT = 0; Combo = 0; LastCut = 0; ComboAt = nil; Over = nil }
		St.Tip = Kit.Image(`Glow`, { AnchorPoint = Vector2.new(0.5, 0.5); Size = UDim2.fromOffset(26, 26); ImageColor3 = Color3.fromRGB(255, 90, 100); ImageTransparency = 0.35; ScaleType = Enum.ScaleType.Stretch; Visible = false; ZIndex = 2; Parent = TrailLayer })
		-- a few relics drift on the title card
		for I = 1, 3 do
			local R = Self:Make(RELICS[I + 1], W * (0.25 + 0.25 * (I - 1)), H * 0.5 + (I % 2) * 40)
			R.Vx, R.Vy, R.Idle = 0, 0, true
			R.F.Rotation = (I - 2) * 14
		end
	end

	function Self:Make(Kind, X: number, Y: number)
		local F = new(`Frame`, { BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromOffset(X, Y); Size = UDim2.fromOffset(SIZE, SIZE); ZIndex = if Kind.Bomb then 2 else 1 }, St.RelicLayer)
		if Kind.Bomb then -- a pale warning halo so the cross reads at a glance
			Kit.Image(`Glow`, { AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(1.7, 1.7); ImageColor3 = Color3.fromRGB(200, 220, 255); ImageTransparency = 0.35; ScaleType = Enum.ScaleType.Stretch; ZIndex = 1; Parent = F })
		else
			Kit.Image(`Glow`, { AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(1.3, 1.3); ImageColor3 = Kind.Tint; ImageTransparency = 0.8; ScaleType = Enum.ScaleType.Stretch; ZIndex = 1; Parent = F })
		end
		local Icon = Kit.Image(Kind.Image, { Name = `Icon`; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(1, 1); ImageColor3 = Kind.Tint; ZIndex = 2; Parent = F })
		local R = { F = F; Icon = Icon; Kind = Kind; X = X; Y = Y; Vx = 0; Vy = 0; Spin = 0; Cut = false; Rose = false }
		table.insert(St.Relics, R)
		return R
	end

	function Self:Throw(Kind)
		local W, H = St.W, St.H
		local X0 = Rng:NextNumber(46, W - 46)
		local Y0 = H + 34
		local Apex = Rng:NextNumber(H * 0.14, H * 0.46)
		local Vy = -math.sqrt(2 * GRAVITY * (Y0 - Apex))
		local Air = 2 * -Vy / GRAVITY
		local Tx = Rng:NextNumber(56, W - 56)
		local R = Self:Make(Kind, X0, Y0)
		R.Vx, R.Vy = (Tx - X0) / Air, Vy
		R.Spin = Rng:NextNumber(-220, 220)
		R.F.Rotation = Rng:NextNumber(0, 360)
		return R
	end

	function Self:Start()
		if not St then return end
		for _, R in St.Relics do R.F:Destroy() end
		table.clear(St.Relics)
		St.Running = true
	end

	function Self:Lose()
		if St.Lives <= 0 then return end
		local Icon = St.LifeIcons[St.Lives]
		if Icon then
			Ctx.tween(Icon, 0.3, { ImageTransparency = 0.75, ImageColor3 = Color3.fromRGB(110, 100, 100) })
			local G = St.LifeRow:FindFirstChild(`Glow{St.Lives}`)
			if G then Ctx.tween(G, 0.3, { ImageTransparency = 1 }) end
		end
		St.Lives -= 1
		Ctx.Sound(`Reject`, 0.6)
		if St.Lives <= 0 then Self:End(nil) end
	end

	function Self:End(Title: string?)
		if St.Dead then return end
		St.Dead = true
		St.DeadT = 0
		St.Over = Title
		Self:Release(nil)
	end

	-- a clean cut: two halves of the relic's art (clipped frames) fly apart along the stroke's normal and fade
	function Self:Split(R, Dir: Vector2)
		R.Cut = true
		R.F.Visible = false
		local Horizontal = math.abs(Dir.X) >= math.abs(Dir.Y) -- a sideways stroke cuts top from bottom
		for Side = 0, 1 do
			local Clip = new(`Frame`, { BackgroundTransparency = 1; ClipsDescendants = true; AnchorPoint = Vector2.new(0.5, 0.5);
				Size = if Horizontal then UDim2.fromOffset(SIZE, SIZE / 2) else UDim2.fromOffset(SIZE / 2, SIZE); ZIndex = 1 }, St.BitLayer)
			local Art = Kit.Image(R.Kind.Image, { AnchorPoint = Vector2.new(0.5, 0.5); Size = UDim2.fromOffset(SIZE, SIZE); ImageColor3 = R.Kind.Tint; Rotation = R.F.Rotation; ZIndex = 1; Parent = Clip })
			local Sign = if Side == 0 then -1 else 1
			local Off = if Horizontal then Vector2.new(0, Sign * SIZE / 4) else Vector2.new(Sign * SIZE / 4, 0)
			-- the art sits so its centre is the relic's centre: shift it back inside the clip
			Art.Position = UDim2.new(0.5, -Off.X, 0.5, -Off.Y)
			local Push = Off.Unit * 150
			table.insert(St.Bits, { F = Clip; Art = Art; X = R.X + Off.X; Y = R.Y + Off.Y; Vx = R.Vx * 0.5 + Push.X; Vy = math.min(R.Vy, 0) * 0.4 + Push.Y - 60; Life = 0; Max = 0.7 })
		end
		if not Ctx.Reduced() then
			local Burst = Kit.Image(`Glow`, { AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromOffset(R.X, R.Y); Size = UDim2.fromOffset(60, 60); ImageColor3 = R.Kind.Tint; ImageTransparency = 0.2; ScaleType = Enum.ScaleType.Stretch; ZIndex = 2; Parent = St.BitLayer })
			Ctx.tween(Burst, 0.3, { Size = UDim2.fromOffset(110, 110), ImageTransparency = 1 })
			task.delay(0.32, function() Burst:Destroy() end)
		end
	end

	function Self:Slash(R, Dir: Vector2)
		Self:Split(R, Dir)
		if R.Kind.Bomb then
			-- the holy cross: a white flash, and the run is over
			local Soft = Ctx.Reduced() or Ctx.ReducedFlash()
			local Flash = new(`Frame`, { BackgroundColor3 = Color3.fromRGB(255, 252, 240); BackgroundTransparency = if Soft then 0.75 else 0; BorderSizePixel = 0; Size = UDim2.fromScale(1, 1); ZIndex = 9 }, St.Scene)
			Ctx.tween(Flash, if Soft then 0.4 else 0.7, { BackgroundTransparency = 1 })
			Ctx.Sound(`Boom`, 0.7)
			Self:End(`You struck the holy cross`)
			return
		end
		St.Combo += 1
		St.LastCut = St.T
		St.ComboAt = Vector2.new(R.X, R.Y)
		Ctx.Add(1)
		Ctx.Sound(`Tick`, 0.35, 1.3 + math.min(St.Combo, 6) * 0.1)
	end

	function Self:Combo()
		local N = St.Combo
		St.Combo = 0
		if N < 3 or St.Dead then return end
		Ctx.Add(N)
		Ctx.Sound(`Confirm`, 0.45, 1.1)
		local At = St.ComboAt or Vector2.new(St.W / 2, St.H / 2)
		local L = Kit.Text({ Text = `Combo \u{00D7}{N}  +{N}`; Font = Enum.Font.Fantasy; TextSize = 22; TextColor3 = Color3.fromRGB(255, 214, 120); TextStrokeTransparency = 0.2; TextXAlignment = Enum.TextXAlignment.Center;
			AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromOffset(math.clamp(At.X, 80, St.W - 80), math.clamp(At.Y, 60, St.H - 60)); Size = UDim2.fromOffset(180, 30); ZIndex = 8; Parent = St.Scene })
		if Ctx.Reduced() then
			Ctx.tween(L, 0.9, { TextTransparency = 1, TextStrokeTransparency = 1 })
		else
			Ctx.tween(L, 0.9, { Position = L.Position - UDim2.fromOffset(0, 40), TextTransparency = 1, TextStrokeTransparency = 1 })
		end
		task.delay(0.95, function() L:Destroy() end)
	end

	function Self:Segment(A: Vector2, B: Vector2)
		local Seg = nil
		if #St.Trail >= TRAIL then
			Seg = table.remove(St.Trail, 1)
		else
			local F = new(`Frame`, { BackgroundColor3 = Color3.fromRGB(220, 40, 60); BorderSizePixel = 0; AnchorPoint = Vector2.new(0.5, 0.5); ZIndex = 1 }, St.TrailLayer)
			new(`UICorner`, { CornerRadius = UDim.new(1, 0) }, F)
			Seg = { F = F }
		end
		local D = B - A
		local Mid = (A + B) / 2
		Seg.Len = D.Magnitude + 4
		Seg.Life = 0
		Seg.F.Position = UDim2.fromOffset(Mid.X, Mid.Y)
		Seg.F.Rotation = math.deg(math.atan2(D.Y, D.X))
		Seg.F.Size = UDim2.fromOffset(Seg.Len, 6)
		Seg.F.BackgroundTransparency = 0.05
		table.insert(St.Trail, Seg)
	end

	function Self:Step(Dt: number)
		if not (St and St.Running) then return end
		St.T += Dt
		-- the trail fades and thins
		for _, Seg in St.Trail do
			Seg.Life += Dt
			local A = math.clamp(Seg.Life / 0.2, 0, 1)
			Seg.F.BackgroundTransparency = 0.05 + A * 0.95
			Seg.F.Size = UDim2.fromOffset(Seg.Len, 6 * (1 - A * 0.7))
		end
		-- halves fall and fade
		local I = 1
		while I <= #St.Bits do
			local B = St.Bits[I]
			B.Life += Dt
			B.Vy += GRAVITY * Dt
			B.X += B.Vx * Dt
			B.Y += B.Vy * Dt
			B.F.Position = UDim2.fromOffset(B.X, B.Y)
			B.Art.ImageTransparency = math.clamp(B.Life / B.Max, 0, 1)
			if B.Life >= B.Max then B.F:Destroy() table.remove(St.Bits, I) else I += 1 end
		end
		if St.Dead then
			St.DeadT += Dt
			if St.DeadT > 0.9 and not St.Done then St.Done = true Ctx.Over(St.Over) end
			return
		end
		-- a combo closes when the stroke rests
		if St.Combo > 0 and St.T - St.LastCut > 0.5 then Self:Combo() end
		-- throws
		St.Next -= Dt
		if St.Next <= 0 then
			local Gap, Count, Bomb = Hex.Plan(St.T)
			St.Next = Gap + Count * 0.12
			local Crosses = 0
			for K = 1, Count do
				local IsBomb = Crosses == 0 and K > 1 and Rng:NextNumber() < Bomb
				if Count == 1 and St.T > 8 and Rng:NextNumber() < Bomb * 0.5 then IsBomb = true end
				if IsBomb then Crosses += 1 end
				table.insert(St.Queue, { At = (K - 1) * 0.12; Kind = if IsBomb then CROSS else RELICS[Rng:NextInteger(1, #RELICS)] })
			end
		end
		I = 1
		while I <= #St.Queue do
			local Q = St.Queue[I]
			Q.At -= Dt
			if Q.At <= 0 then Self:Throw(Q.Kind) table.remove(St.Queue, I) else I += 1 end
		end
		-- relics fly
		I = 1
		while I <= #St.Relics do
			local R = St.Relics[I]
			R.Vy += GRAVITY * Dt
			R.X += R.Vx * Dt
			R.Y += R.Vy * Dt
			if R.Y < St.H then R.Rose = true end
			R.F.Position = UDim2.fromOffset(R.X, R.Y)
			R.F.Rotation += R.Spin * Dt
			if R.Cut then
				R.F:Destroy()
				table.remove(St.Relics, I)
			elseif R.Vy > 0 and R.Y > St.H + SIZE then
				R.F:Destroy()
				table.remove(St.Relics, I)
				if not R.Kind.Bomb and R.Rose then Self:Lose() end
				if St.Dead then return end
			else
				I += 1
			end
		end
	end

	function Self:Press(P: Vector2)
		if not (St and St.Running) or St.Dead then return end
		St.Down = true
		St.Last = P
		St.LastT = os.clock()
		St.Tip.Visible = true
		St.Tip.Position = UDim2.fromOffset(P.X, P.Y)
	end

	function Self:Move(P: Vector2)
		if not (St and St.Down and St.Last) or St.Dead then return end
		local Now = os.clock()
		local D = P - St.Last
		local Dist = D.Magnitude
		if Dist < 2 then return end
		local Speed = Dist / math.max(Now - St.LastT, 1 / 240)
		Self:Segment(St.Last, P)
		St.Tip.Position = UDim2.fromOffset(P.X, P.Y)
		if Speed >= SLASH_SPEED then
			for _, R in St.Relics do
				if not R.Cut and nearSegment(St.Last, P, Vector2.new(R.X, R.Y), HIT_R) then
					Self:Slash(R, D)
					if St.Dead then break end
				end
			end
		end
		St.Last = P
		St.LastT = Now
	end

	function Self:Release(_P: Vector2?)
		if not St then return end
		St.Down = false
		St.Last = nil
		St.Tip.Visible = false
		if St.Combo > 0 then Self:Combo() end
	end

	return Self
end

return Hex
