--!strict
--[[ (phase6-strafes) Pure gesture picking (no services, no instances). Callers pass Config.Gestures tables.
	Pick(Cast, Hook, Ctx, Roll)   the first rule for Hook whose Who all match Ctx; Chance roll; weighted clip pick -> base name?
	Bucket(LegLen, Buckets)       the nearest leg-length bucket (percent of a 2-stud leg)
	Name(Base, Clip, LegLen)      Base, or Base .. "_" .. bucket for a bucketed clip
	Roll: () -> number in [0, 1). ]]
local G = {}

local function matches(Want: any, Have: any): boolean
	if typeof(Want) == "table" then
		for _, V in Want do if V == Have then return true end end
		return false
	end
	return Want == Have
end

function G.Rule(Cast: { any }, Hook: string, Ctx: { [string]: any }): any?
	for _, R in Cast do
		if R.Hook == Hook then
			local Ok = true
			for K, V in R.Who or {} do
				if not matches(V, Ctx[K]) then Ok = false break end
			end
			if Ok then return R end
		end
	end
	return nil
end

function G.Pick(Cast: { any }, Hook: string, Ctx: { [string]: any }, Roll: () -> number): string?
	local R = G.Rule(Cast, Hook, Ctx)
	if not R then return nil end
	if Roll() >= (R.Chance or 1) then return nil end
	local Total = 0
	for _, C in R.Clips do Total += C[2] end
	if Total <= 0 then return nil end
	local X = Roll() * Total
	for _, C in R.Clips do
		X -= C[2]
		if X < 0 then return C[1] end
	end
	return R.Clips[#R.Clips][1]
end

function G.Bucket(LegLen: number, Buckets: { number }): number
	local Pct = LegLen / 2 * 100
	local Best, BestD = Buckets[1], math.huge
	for _, B in Buckets do
		local D = math.abs(B - Pct)
		if D < BestD then Best, BestD = B, D end
	end
	return Best
end

function G.Name(Base: string, Clip: any, LegLen: number): string
	if Clip and Clip.Buckets then return Base .. "_" .. G.Bucket(LegLen, Clip.Buckets) end
	return Base
end

return G
