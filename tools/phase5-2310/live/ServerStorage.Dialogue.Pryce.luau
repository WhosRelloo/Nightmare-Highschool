-- Mr. Pryce (2.28). English, Room 104. Theatrical; reads the register as if it were a play; kind to the quiet ones.
local Template = require(script.Parent.GiverTemplate)

return Template({
	PathGreeting = { Path = `Social`; Tier = 3; Text = `Ah, the star of the corridor! Enter to applause.` }; -- (2.31) Standing Paths
	Greeting = `Ah! Enter, stage left.`;
	Bye = `Exit, pursued by homework.`;
	Talk = {
		{ Ask = `What are we reading?`; Answer = `Ghost stories. This term they're the only honest kind.` };
		{ Ask = `Why do you read the register like that?`; Answer = `Every name deserves to be said properly. Some only get the once.` };
		{ Ask = `Any advice?`; Answer = `Speak up in class. The quiet ones get forgotten here.` };
	};
})
