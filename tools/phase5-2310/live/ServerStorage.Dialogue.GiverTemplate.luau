--[[
	Shared tree for ordinary students who give quests (no saved relationship).
	L = {
		Greeting = string | fn(ctx),
		PathGreeting = { Path, Tier, Text }?,   -- (2.31) said first once the student has that Standing Path tier
		Talk = { { Ask, Answer } },            -- small talk
		Extra = { choice, ... }?,              -- NPC-specific replies (may use If / Do)
		Nodes = { [id] = node }?,              -- nodes those replies lead to
		Bye = string,
	}
]]

local QuestChoices = require(script.Parent.QuestChoices)

return function(L)
	local Nodes = {}
	local QuestMenu = QuestChoices(Nodes, `Hub`)
	local Bye = { Text = L.Bye or `See you.` }

	for Id, Node in L.Nodes or {} do Nodes[Id] = Node end

	local TalkChoices = {}
	for Index, Pair in L.Talk or {} do
		Nodes[`Talk{Index}`] = { Text = Pair.Answer; Choices = { { Text = `Huh.`; Next = `Hub` }, Bye } }
		table.insert(TalkChoices, { Text = Pair.Ask; Next = `Talk{Index}` })
	end

	-- (1.35) clique leaders (the joinable six): "I want to join you." / "I'm out." (Social.CliqueMembership)
	local Refuse = {
		NotRespected = `Earn it first. Come back when my people respect you.`;
		NotBeaten = `Respect's one thing. You haven't beaten me yet. Ask me for a showdown.`;
		OtherClique = `You already run with another crowd. Leave them first.`;
		AlreadyMember = `You're already one of us.`;
	}
	for Code, Line in Refuse do Nodes[`CJ_{Code}`] = { Text = Line; Choices = { { Text = `Fair enough.`; Next = `Hub` }, Bye } } end
	Nodes.CJ_Unknown = { Text = `...Not now.`; Choices = { { Text = `Okay.`; Next = `Hub` }, Bye } }
	Nodes.CJ_Joined = { Text = function(ctx) return ctx.CliqueLine(`Joined`) or `Welcome.` end; Choices = { { Text = `Thanks.`; Next = `Hub` }, Bye } }
	Nodes.CJ_Confirm = {
		Text = `You want out? You know what that means. Walk away now and we're done. For good.`;
		Choices = {
			{ Text = `I'm sure. I'm out.`; Do = function(ctx) return if ctx.CliqueLeave() then `CJ_Left` else `Hub` end };
			{ Text = `Forget I said anything.`; Next = `Hub` };
		};
	}
	Nodes.CJ_Left = { Text = function(ctx) return ctx.CliqueLine(`Betrayed`) or `Get out.` end; Choices = { Bye } }
	local MemberChoices = {
		{
			Text = `I want to join you.`;
			If = function(ctx) return ctx.Joinable and ctx.Joinable() and not ctx.CliqueMember() end;
			Do = function(ctx)
				local Ok, Code = ctx.CliqueCanJoin()
				if Ok then return if ctx.CliqueJoin() then `CJ_Joined` else `Hub` end
				return if Nodes[`CJ_{Code}`] then `CJ_{Code}` else `CJ_Unknown`
			end;
		};
		{ Text = `I'm out.`; If = function(ctx) return ctx.Joinable and ctx.Joinable() and ctx.CliqueMember() end; Next = `CJ_Confirm` };
	}

	Nodes.Hub = {
		Text = function(ctx) -- (2.31) a Standing Path line first, once the student has earned it
			local PG = L.PathGreeting
			if PG and ctx.PathTier and ctx.PathTier(PG.Path) >= PG.Tier then return PG.Text end
			if typeof(L.Greeting) == `function` then return L.Greeting(ctx) end
			return L.Greeting
		end;
		Choices = function(ctx)
			local List = {}
			for _, Choice in QuestMenu.Choices(ctx) do table.insert(List, Choice) end
			for _, Choice in MemberChoices do table.insert(List, Choice) end
			for _, Choice in L.Extra or {} do table.insert(List, Choice) end
			for _, Choice in TalkChoices do table.insert(List, Choice) end
			table.insert(List, Bye)
			return List
		end;
	}

	return {
		Start = function(ctx)
			return QuestMenu.Start(ctx) or `Hub`
		end;
		Nodes = Nodes;
	}
end
