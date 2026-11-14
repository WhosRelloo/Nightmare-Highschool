
---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local RunService = game:GetService(`RunService`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)

---| Type Annotation |---

type 		HitBoxSizeProperties = 'Size' | 'Radius'
type 		HitBoxShape = 'BoxHandleAdornment' | 'SphereHandleAdornment'

export type HitBoxConnection = SignalPlus.Connection
export type HitBoxProperties = {

	---| HitBox Properties |---

	Shape: Enum.PartType; -- only block rn
	Offset: CFrame;

	Size: Vector3;
	CFrame: CFrame | BasePart;

	Prediction: boolean;
	CFrameDotCheck: boolean;

	---| HitBox Theme |---

	HitBoxVisible: boolean;
	HitBoxDetection: 'Default' | 'HitOnce';

	HitBoxColor: Color3;
	HitBoxTransparency: number;

	---| HitBox Data |---

	HitBox: BoxHandleAdornment | SphereHandleAdornment;
	Params: OverlapParams;

	Touched: SignalPlus.Signal<BasePart, Humanoid?>;
	HitList: { (Humanoid & BasePart & Model) ?};

	Go: (self: HitBoxProperties) -> ( HitBoxProperties );
	GetCast: (self: HitBoxProperties) -> { Model }?;

	Destroy: (self: HitBoxProperties) -> ();
}

---| HitBox Services |---

local HitBoxShapes = { [Enum.PartType.Ball] = `SphereHandleAdornment`; [Enum.PartType.Block] = `BoxHandleAdornment`; } :: { [Enum.PartType]: HitBoxShape }
local HitBoxProperties = { [Enum.PartType.Ball] = `Radius`; [Enum.PartType.Block] = `Size`; } :: { [Enum.PartType]: HitBoxSizeProperties }


local Local = {}
local Shared = {}
Shared.__index = Shared


function Shared.New(): HitBoxProperties
	local self = setmetatable({}, Shared) :: HitBoxProperties

	---| HitBox Properties |---

	self.Shape = Enum.PartType.Block
	self.Offset = CFrame.new(0, 0, 0)

	self.CFrame = CFrame.new(0, 0, 0)
	self.Size = vector.create(0, 0, 0)

	self.Prediction = false
	self.CFrameDotCheck = false

	---| HitBox Theme |---

	self.HitBoxVisible = if RunService:IsStudio() then true else false
	self.HitBoxDetection = `Default`

	self.HitBoxColor = Color3.new(1, 0, 0)
	self.HitBoxTransparency = .8

	---| HitBox Data |---

	self.Params = OverlapParams.new()
	self.Touched = SignalPlus()

	self.HitList = { }

	return self
end

function Shared.Go(self: HitBoxProperties) -- s

	local PredictedCFrame = Local.Predict(.2, self.CFrame)

	local HitBoxShape = Local.GetShape(self.Shape)
	local BaseCFrame = PredictedCFrame or Local.GetBaseCFrame(self.CFrame)

	local Direction = workspace.Visuals.HitBoxes
	local HitBoxProperty = Local.GetProperty(self.Shape)

	if not self.HitBox and self.HitBoxVisible then
		self.HitBox = Instance.new(HitBoxShape, Direction)
		self.HitBox.Name = `HitBox |{time()}|`

		self.HitBox.Color3 = self.HitBoxColor
		self.HitBox.Transparency = self.HitBoxTransparency

		self.HitBox[HitBoxProperty] = self.Size
		self.HitBox.CFrame = BaseCFrame * self.Offset

		self.HitBox.Adornee = workspace.Terrain

	elseif self.HitBoxVisible then
		self.HitBox.CFrame = BaseCFrame * self.Offset

	end

	local HitList = Local.CastShape(self.Shape, BaseCFrame * self.Offset, self.Size, self.Params)
	if not HitList then return self end

	for _, A in pairs(HitList) do
		local Character = A:FindFirstAncestorOfClass(`Model`) or A.Parent :: Model
		local Humanoid: Humanoid? = Character:FindFirstChildOfClass(`Humanoid`)

		if self.HitBoxDetection == `Default` then
			if not Humanoid then
				continue
			end

			if Humanoid:GetState() == Enum.HumanoidStateType.Dead then
				continue
			end

			if table.find(self.HitList, Humanoid) then
				continue
			end


			table.insert(self.HitList, Humanoid)
			self.Touched:Fire(A, Humanoid)
		end

		if self.HitBoxDetection == `HitOnce` then
			if not Humanoid then
				continue
			end

			if Humanoid:GetState() == Enum.HumanoidStateType.Dead then
				continue
			end	

			self.Touched:Fire(A, Humanoid)
			self:Destroy()
			break
		end

	end

	return self
end

function Shared.GetCast(self: HitBoxProperties): { Model }?
	local PredictedCFrame = Local.Predict(.2, self.CFrame)

	local HitBoxShape = Local.GetShape(self.Shape)
	local BaseCFrame = PredictedCFrame or Local.GetBaseCFrame(self.CFrame)

	local Direction = workspace.Visuals.HitBoxes
	local HitBoxProperty = Local.GetProperty(self.Shape)

	if not self.HitBox and self.HitBoxVisible then
		self.HitBox = Instance.new(HitBoxShape, Direction)
		self.HitBox.Name = `HitBox |{time()}|`

		self.HitBox.Color3 = self.HitBoxColor
		self.HitBox.Transparency = self.HitBoxTransparency

		self.HitBox[HitBoxProperty] = self.Size
		self.HitBox.CFrame = BaseCFrame * self.Offset

		self.HitBox.Adornee = workspace.Terrain

	elseif self.HitBoxVisible then
		self.HitBox.CFrame = BaseCFrame * self.Offset

	end

	local HitList = Local.CastShape(self.Shape, BaseCFrame * self.Offset, self.Size, self.Params)
	if not HitList then return end

	for Index, A in pairs(HitList) do
		local Character = A:FindFirstAncestorOfClass(`Model`) or A.Parent :: Model
		local Humanoid: Humanoid? = Character:FindFirstChildOfClass(`Humanoid`)

		if not Humanoid then
			HitList[Index] = nil
			continue
		end

		if self.HitBoxDetection == `HitOnce` then
			return { A };
		end
	end

	return HitList
end

function Shared.Destroy(self: HitBoxProperties)
	if self.HitBox then
		pcall(function() self.HitBox:Destroy() end)
		self.HitBox = nil
	end

	if self.Touched then
		pcall(function() self.Touched:Destroy() end)
		self.Touched = nil
	end

	if self.HitList then
		table.clear(self.HitList)
		self.HitList = nil
	end

	if self.Params then
		self.Params = nil
	end
end

function Local.CastShape(Shape: Enum.PartType, BaseCFrame: CFrame, Size: Vector3 | number, Params: OverlapParams): { BasePart? }
	local HitList : { BasePart? }

	if Shape == Enum.PartType.Block then
		HitList = workspace:GetPartBoundsInBox(BaseCFrame, Size, Params)
		return HitList
	elseif Shape == Enum.PartType.Ball then
		return 
	end

	return HitList
end

function Local.Predict(Time: number, Part: BasePart): CFrame?
	if typeof(Part) ~= `BasePart` then return end

	if Time <= 0 then
		return 
	end

	local Constant: number = 1 / Time
	local Velocity = Part.AssemblyLinearVelocity

	local PredictedPosition = Part.Position + Velocity * Time
	local PredictedCFrame = CFrame.new(PredictedPosition) * (Part.CFrame - Part.Position)

	return PredictedCFrame
end

function Local.GetBaseCFrame(Point: Instance | CFrame): CFrame
	return if typeof(Point) == `Instance` then Point.CFrame else Point :: CFrame
end

function Local.GetProperty(PartType: Enum.PartType): HitBoxSizeProperties
	return HitBoxProperties[PartType]
end

function Local.GetShape(PartType: Enum.PartType): HitBoxShape
	return HitBoxShapes[PartType]
end

return Shared
