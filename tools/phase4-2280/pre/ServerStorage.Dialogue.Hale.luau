-- Mr. Hale, homeroom teacher, Room 102 (2.24.0). Orientation: reporting to him opens his question about the roll call
-- (the Decision "RollCallName"; any answer completes it, the choice is remembered, nothing is locked by it).
-- Chapter One rule: he won't talk about Room 102 or the name on his register.
local Template = require(script.Parent.GiverTemplate)

local function asking(ctx)
	local Obj = ctx.Objective(`Orientation`)
	return Obj ~= nil and Obj.Id == `Answer`
end

local Tree = Template({
	Greeting = function(ctx)
		local Said = ctx.Decided(`RollCallName`)
		if Said == `Heard` then return `You again. Hearing anything else I should know about?` end
		if Said == `Asked` then return `Settled in? Good. Don't go asking the office about old registers.` end
		return `Register's done. If you're after sympathy, the infirmary is down the hall.`
	end;
	Bye = `Back row. Don't be late twice.`;
	Talk = {
		{ Ask = `What's Room 102 like after dark?`;
		  Answer = `Locked. Like every other room. Next question.` };
		{ Ask = `How long have you taught here?`;
		  Answer = `Long enough to stop counting the bells. That was a joke. Mostly.` };
	};
	Extra = {
		{ Text = `About the roll call this morning...`; If = asking; Next = `RC_Ask` };
		{ Text = `Who sat at the empty desk?`;
		  If = function(ctx) return ctx.Decided(`RollCallName`) ~= nil end; Next = `RC_Desk` };
	};
	Nodes = {
		RC_Ask = {
			Text = `You. New one. Back row. When I read the last name this morning... did you hear anyone answer?`;
			Choices = {
				{ Text = `Nobody answered.`; Do = function(ctx) ctx.Decide(`RollCallName`, `Nobody`) return `RC_Nobody` end };
				{ Text = `Who's Mira Holt?`; Do = function(ctx) ctx.Decide(`RollCallName`, `Asked`) return `RC_Asked` end };
				{ Text = `I thought I heard someone.`; Do = function(ctx) ctx.Decide(`RollCallName`, `Heard`) return `RC_Heard` end };
			};
		};
		RC_Nobody = {
			Text = `No. Nobody did. Good. Your seat is in the back row, beside the empty one. Go and find it.`;
			Choices = { { Text = `Yes, sir.` } };
		};
		RC_Asked = {
			Text = `A name on an old register. The office hasn't caught up. That's all it is. Back row, beside the empty desk. Go.`;
			Choices = { { Text = `...Right.` } };
		};
		RC_Heard = {
			Text = `...Did you. Then you hear better than I do. Back row. The seat beside the empty one. Sit down.`;
			Choices = { { Text = `Okay.` } };
		};
		RC_Desk = {
			Text = `Nobody you need to worry about. It's a desk. Sit at your own.`;
			Choices = { { Text = `Sure.`; Next = `Hub` }, { Text = `Bye.` } };
		};
	};
})

-- reporting to him (the Talk stage completes as you open the conversation) goes straight to his question
local BaseStart = Tree.Start
Tree.Start = function(ctx)
	if asking(ctx) then return `RC_Ask` end
	return BaseStart(ctx)
end

return Tree
