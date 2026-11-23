-- Nurse Agatha Thorne, the Infirmary (phase6-strafes; spec §6.3-6.4). Brisk, kind underneath, has seen everything this
-- school does to its students and writes none of it down. "Get patched up" calls Services.Features.Infirmary.Treat
-- (the minimal, pluggable treatment; the coming injury system replaces its rules).
local ServerScriptService = game:GetService("ServerScriptService")
local Template = require(script.Parent.GiverTemplate)

local function hurt(ctx): boolean
	local C = ctx.Player.Character
	local H = C and C:FindFirstChildOfClass("Humanoid")
	return H ~= nil and (H.Health < H.MaxHealth * 0.5 or C:GetAttribute("NHWounded") == true)
end

local function treat(ctx)
	task.spawn(function()
		pcall(function() require(ServerScriptService.Services.Features.Infirmary).Treat(ctx.Player) end)
	end)
	return "Treating"
end

return Template({
	Greeting = function(ctx)
		if hurt(ctx) then return "You don't look good. Sit down before you fall down." end
		local St = nil
		pcall(function() St = require(ServerScriptService.Services.School.SchoolClock).GetState() end)
		local Hour = St and St.Hour or 12
		if Hour < 10 then return "Early for trouble. What is it?" end
		if Hour >= 15 then return "Last patient of the day, I hope. What happened?" end
		return "Infirmary. Sit, don't bleed on the sheets."
	end;
	Bye = "Off you go. Try not to come back.";
	Talk = {
		{ Ask = "What happens to students here?";
		  Answer = "Bruises, mostly. Sprains. Nightmares. I treat the first two." };
		{ Ask = "Do you write any of it down?";
		  Answer = "The headmaster prefers a tidy register. So, no." };
		{ Ask = "Why are both beds made up?";
		  Answer = "Because someone always comes in after dark. Always." };
	};
	Extra = {
		{ Text = "Can you patch me up?"; Next = "Patch" };
	};
	Nodes = {
		Patch = {
			Text = "Hold still and don't fuss.";
			Choices = { { Text = "Okay."; Do = treat }, { Text = "Never mind."; Next = "Hub" } };
		};
		Treating = {
			Text = "There we are. Keep it clean.";
			Choices = { { Text = "Thanks." } };
		};
	};
})
