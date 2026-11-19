--[[
	Shared dialogue tree for faction leaders. Each leader module passes its own lines (L) and
	gets back a full tree (see Services.Social.Dialogue for the format).

	L = {
		Intro, About, Lore, Hostile, Apology, Insulted, LeaveConfirm, Left, Joined,
		Hub = { Rival, Acquaintance, Friendly, Trusted, Hostile }, HubMember = fn(ctx),
		Join = { RivalMember, NotNoticed, Initiation = fn(ctx), Cooldown, AlreadyMember },
		Mission = fn(ctx, Count), MissionDone,
		Ask = { About, Join, Work, Lore, Sorry, Insult, Leave, Bye } -- player lines
	}
]]

local QuestChoices = require(script.Parent.QuestChoices)

return function(L)
	local Ask = L.Ask
	local Nodes = {}
	local QuestMenu = QuestChoices(Nodes, `Hub`)

	local function Back(Text: string?)
		return { Text = Text or `Back.`; Next = `Hub` }
	end
	local Bye = { Text = Ask.Bye }

	local function Friendly(ctx)
		local State = ctx.State()
		return State == `Friendly` or State == `Trusted` or ctx.Member()
	end

	Nodes.Intro = {
		Text = L.Intro;
		Choices = {
			{ Text = Ask.About; Next = `About` };
			{ Text = `Just looking around.`; Next = `Hub` };
		};
	}

	Nodes.Hub = {
		Text = function(ctx)
			if ctx.Member() then return L.HubMember(ctx) end
			return L.Hub[ctx.State()] or L.Hub.Acquaintance
		end;
		Choices = function(ctx)
			local List = table.clone(Nodes.Hub.Base)
			local Bye = table.remove(List) -- keep Goodbye last
			for _, Choice in QuestMenu.Choices(ctx) do table.insert(List, Choice) end
			table.insert(List, Bye)
			return List
		end;
		Base = {
			{ Text = Ask.About; Next = `About` };
			{
				Text = Ask.Join;
				If = function(ctx) return not ctx.Member() end;
				Do = function(ctx)
					local Ok, Code = ctx.CanJoin()
					if Ok then return if ctx.Join() then `Joined` else `Hub` end
					return `Join_{Code}`
				end;
			};
			{ Text = Ask.Work; If = function(ctx) return ctx.Member() end; Next = `Mission` };
			{ Text = Ask.Lore; If = Friendly; Next = `Lore` };
			{
				Text = Ask.Sorry;
				If = function(ctx) return ctx.Value() < 0 and ctx.Once(`Apology`) end;
				Do = function(ctx)
					ctx.UseOnce(`Apology`)
					ctx.Rel(8, `They accepted your apology.`)
					return `Apology`
				end;
			};
			{
				Text = Ask.Insult;
				If = function(ctx) return not ctx.Member() end;
				Do = function(ctx)
					ctx.Rel(-10, `You insulted them.`)
					return `Insulted`
				end;
			};
			{ Text = Ask.Leave; If = function(ctx) return ctx.Member() end; Next = `LeaveConfirm` };
			Bye;
		};
	}

	Nodes.About = { Text = L.About; Choices = { Back(`I see.`), Bye } }
	Nodes.Lore = { Text = L.Lore; Choices = { Back(`...Right.`), Bye } }
	Nodes.Apology = { Text = L.Apology; Choices = { Back(), Bye } }
	Nodes.Insulted = { Text = L.Insulted; Choices = { Bye } }
	Nodes.Joined = { Text = L.Joined; Choices = { Back(`Thank you.`), Bye } }

	for Code, Line in L.Join do
		Nodes[`Join_{Code}`] = { Text = Line; Choices = { Back(`Fine.`), Bye } }
	end
	Nodes.Join_Unknown = { Text = `...Not now.`; Choices = { Back(), Bye } }
	-- (1.35) one crowd at a time (Social.CliqueMembership)
	Nodes.Join_CliqueMember = Nodes.Join_CliqueMember or { Text = `You already run with another crowd. Come back when you've left them.`; Choices = { Back(`Fine.`), Bye } }

	Nodes.Mission = {
		Text = function(ctx)
			local Done, Count = ctx.MissionStatus()
			if Done then return L.MissionDone end
			return L.Mission(ctx, Count)
		end;
		Choices = { Back(`On it.`), Bye };
	}

	Nodes.LeaveConfirm = {
		Text = L.LeaveConfirm;
		Choices = {
			{ Text = `Yes. I'm out.`; Do = function(ctx) return if ctx.Leave() then `Left` else `Hub` end };
			Back(`No, forget it.`);
		};
	}
	Nodes.Left = { Text = L.Left; Choices = { Bye } }

	Nodes.Hostile = {
		Text = L.Hostile;
		Choices = {
			{
				Text = Ask.Sorry;
				If = function(ctx) return ctx.Once(`Apology`) end;
				Do = function(ctx)
					ctx.UseOnce(`Apology`)
					ctx.Rel(8, `They accepted your apology.`)
					return if ctx.State() == `Hostile` then `Hostile` else `Apology`
				end;
			};
			Bye;
		};
	}

	return {
		Start = function(ctx)
			local First = not ctx.Met()
			ctx.Meet()
			if First then return `Intro` end
			local Thanks = QuestMenu.Start(ctx)
			if Thanks then return Thanks end
			if ctx.State() == `Hostile` then return `Hostile` end
			return `Hub`
		end;
		Nodes = Nodes;
	}
end
