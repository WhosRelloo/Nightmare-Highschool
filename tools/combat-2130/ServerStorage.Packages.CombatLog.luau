--[[
	CombatLog (server, Studio only): combat concept 14 (2.13.0). A trace of each exchange so tuning is measured, not
	guessed: input packets, actions starting or refused, hitbox checks (with the lag-compensation rewind), and what
	DamageLogic made of each hit (lands, blocked, parried, i-frames, counter-hit, posture).

	It records only inside Studio (RunService:IsStudio()). It does nothing in a live server.
	  Read:   ServerStorage.NHTestBridge:Invoke("CombatLog", 60)   -> ok, the last 60 lines
	  Clear:  ServerStorage.NHTestBridge:Invoke("CombatLogClear")
	  Print as it happens: workspace:SetAttribute("NHCombatLogPrint", true)   (each line prints with a [CL] prefix)
	  Pause:  workspace:SetAttribute("NHCombatLogOff", true)
	  NPC vs NPC too: workspace:SetAttribute("NHCombatLogNPCs", true)   (off by default: only lines involving a player)
	Times are server seconds since the log started (os.clock), to 1 ms.
]]
local Players = game:GetService(`Players`)
local RunService = game:GetService(`RunService`)

local MAX_LINES = 600
local STUDIO = RunService:IsStudio()

local Lines = {}
local T0 = os.clock()

local CombatLog = {}

function CombatLog.On(): boolean
	return STUDIO and workspace:GetAttribute(`NHCombatLogOff`) ~= true
end

function CombatLog.Now(): number
	return os.clock() - T0
end

-- does this line involve a player: by them, or (the text names one) to them?
local function InvolvesPlayer(Who: Instance? | string, Text: string?): boolean
	if typeof(Who) == `Instance` and Players:GetPlayerFromCharacter(Who) then return true end
	for _, P in Players:GetPlayers() do
		if Text and P.Character and string.find(Text, `-> ` .. P.Character.Name, 1, true) then return true end
	end
	return false
end

-- one line: when, who, what kind, then free text. NPC-only lines (dummies swinging at each other) are skipped
-- unless workspace attribute NHCombatLogNPCs is true.
function CombatLog.Log(Who: Instance? | string, Kind: string, Text: string?)
	if not CombatLog.On() then return end
	if workspace:GetAttribute(`NHCombatLogNPCs`) ~= true and not InvolvesPlayer(Who, Text) then return end
	local Name = if typeof(Who) == `Instance` then Who.Name elseif typeof(Who) == `string` then Who else `-`
	local Line = string.format(`%9.3f  %-16s %-9s %s`, os.clock() - T0, string.sub(Name, 1, 16), Kind, Text or ``)
	table.insert(Lines, Line)
	if #Lines > MAX_LINES then table.remove(Lines, 1) end
	if workspace:GetAttribute(`NHCombatLogPrint`) == true then print(`[CL] ` .. Line) end
end

function CombatLog.Get(Count: number?): string
	local N = math.clamp(math.floor(Count or 80), 1, MAX_LINES)
	local Out = {}
	for I = math.max(1, #Lines - N + 1), #Lines do table.insert(Out, Lines[I]) end
	return table.concat(Out, `\n`)
end

function CombatLog.Clear()
	table.clear(Lines)
	T0 = os.clock()
end

return CombatLog
