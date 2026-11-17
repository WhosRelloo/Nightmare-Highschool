-- The Night Custodian (2.24.0). Sweeps the main hallway by day; after hours he's the Records Office watcher
-- (Config.Stealth). His face is never seen (NpcLooks Faceless). Few words; he never answers a question straight.
local Template = require(script.Parent.GiverTemplate)

return Template({
	Greeting = `...Mind the floor. It's wet.`;
	Bye = `Mm.`;
	Talk = {
		{ Ask = `Did you know Mira Holt?`;
		  Answer = `Names come. Names go. I sweep up after.` };
		{ Ask = `What's kept in the Records Office?`;
		  Answer = `Records. Locked by day. After dark, more locked.` };
		{ Ask = `Why can't I see your face?`;
		  Answer = `Light's poor in these halls. Always has been.` };
		{ Ask = `Do you ring the bell?`;
		  Answer = `Nobody rings that bell.` };
	};
})
