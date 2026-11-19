-- Vesper Crane, Regent of the Crimson Court. Found in the Boiler Yard.
local Template = require(script.Parent.LeaderTemplate)

return Template({
	PathHub = { Path = `Combat`; Tier = 3; Text = `Enforcer. The Court has been hearing your name.` }; -- (2.31) Standing Paths
	Intro = `Well. A new face in the Boiler Yard. Vesper Crane. The Court sees everything that happens after dark... and most of what happens before it.`;
	About = `The Crimson Court runs this place when the lights go out. We mark our walls and we make the hall monitors look slow. Paint a sigil without being seen, give a monitor the slip, put someone on the floor. That's how you rise.`;
	Lore = `The basement doors lock from the inside. Every night. Nobody on staff has a key. Funny, isn't it?`;
	Hostile = `Nothing to discuss. Walk away while you still can.`;
	Apology = `Cute. I'll let it slide. Once.`;
	Insulted = `Careful. People who talk like that find a sigil on their locker.`;
	Joined = `Then you're ours. Wear the crimson, and never apologise for it.`;
	LeaveConfirm = `Walking out on the Court? Half of what you've earned stays here with me. Sure?`;
	Left = `Run along, then. The night remembers.`;

	Hub = {
		Hostile = `You've got a death wish, wandering down here.`;
		Rival = `Smells like candle wax. What do you want?`;
		Acquaintance = `Make it quick. The boilers get loud.`;
		Friendly = `Ah, you again. Pull up a crate.`;
		Trusted = `My favourite troublemaker. Sit.`;
	};
	HubMember = function(ctx)
		return `{ctx.Rank()}. Bring me good news.`
	end;

	Join = {
		RivalMember = `Still got Vigil wax on your sleeves? Blow out their candle first.`;
		NotNoticed = `Nobody's whispering your name yet. Give them a reason to.`;
		Initiation = function(ctx)
			return `Prove it. {ctx.Faction.Initiation.Text} The marked walls are all over campus.`
		end;
		Cooldown = `You left. Come crawling back tomorrow, maybe.`;
		AlreadyMember = `You're already wearing our colours.`;
	};

	Mission = function(ctx, Count)
		local M = ctx.MissionDef
		return `{M.Name}. {M.Text} This period: {Count} of 3.`
	end;
	MissionDone = `Night Prowler. I keep hearing your name in the halls. Good.`;

	Ask = {
		About = `What is the Crimson Court?`;
		Join = `I want in.`;
		Work = `Got a job for me?`;
		Lore = `Heard any rumours?`;
		Sorry = `About last time... my bad.`;
		Insult = `You're just kids playing vampire.`;
		Leave = `I'm leaving the Court.`;
		Bye = `Later.`;
	};
})
