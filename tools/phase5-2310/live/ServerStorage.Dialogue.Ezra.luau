-- Ezra Vale, Vigil Captain. Found in the Library Archive.
local Template = require(script.Parent.LeaderTemplate)

return Template({
	PathHub = { Path = `Academic`; Tier = 3; Text = `Honor Student now. The Vigil notices names like yours.` }; -- (2.31) Standing Paths
	Intro = `Shh. The Archive is closed after hours, which is exactly why we're here. Ezra Vale. I keep the Vigil.`;
	About = `The Vigil keeps the lamps lit. We read what this school files away, and we keep watch when the halls go dark. Pass your classes and come to Night Study, and people here will learn your name. Skipping class won't help you.`;
	Lore = `The bell in the east wing rings at hours nobody scheduled. We write every one down. One day the pattern will mean something.`;
	Hostile = `We have nothing to say to each other. The door is behind you.`;
	Apology = `...Fine. Everyone gets one bad night.`;
	Insulted = `Then go burn your candle with the Court. Mind the door on your way out.`;
	Joined = `Then take a candle. Keep it lit, and keep your eyes open. Welcome to the Vigil.`;
	LeaveConfirm = `Leaving? Your candle goes out with you, and so does half of what you've earned here. You're sure?`;
	Left = `Then I hope you never need us.`;

	Hub = {
		Hostile = `You've got nerve showing your face in here.`;
		Rival = `Keep your voice down and your hands where I can see them.`;
		Acquaintance = `Need something? Keep it quiet.`;
		Friendly = `Good to see you. The candles are holding tonight.`;
		Trusted = `There you are. I saved you a seat by the lamp.`;
	};
	HubMember = function(ctx)
		return `{ctx.Rank()}. Anything to report from the halls?`
	end;

	Join = {
		RivalMember = `You wear the Court's colours and you want a seat at this table? Cut ties with Vesper first.`;
		NotNoticed = `Nobody here knows your name yet. Pass a few classes, sit in on Night Study, then ask me again.`;
		Initiation = function(ctx)
			return `Show me you can do the work. {ctx.Faction.Initiation.Text} Then we'll talk.`
		end;
		Cooldown = `You walked out on us. Give it a day before you knock again.`;
		AlreadyMember = `You're already one of us.`;
	};

	Mission = function(ctx, Count)
		local M = ctx.MissionDef
		return `{M.Name}. {M.Text} You've managed {Count} of 3 today.`
	end;
	MissionDone = `You already earned your Lamplighter title. The lamps burn brighter for it.`;

	Ask = {
		About = `What is the Vigil?`;
		Join = `I want in.`;
		Work = `Any work for me?`;
		Lore = `Seen anything strange lately?`;
		Sorry = `About last time... I'm sorry.`;
		Insult = `Your candle club is a joke.`;
		Leave = `I'm done with the Vigil.`;
		Bye = `See you around.`;
	};
})
