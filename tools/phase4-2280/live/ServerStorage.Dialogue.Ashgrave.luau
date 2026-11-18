-- Headmaster Corvin Ashgrave (2.28). Keeps the Covenant; not a villain: believes the roll is the price of every
-- student's safety. Office hours by the Records Office door during class time.
local Template = require(script.Parent.GiverTemplate)

return Template({
	Greeting = `Shouldn't you be in class?`;
	Bye = `Attend. Always attend.`;
	Talk = {
		{ Ask = `What's in the Records Office?`; Answer = `Every student who ever answered the register. You're in there too.` };
		{ Ask = `Who was Mira Holt?`; Answer = `There is no Mira Holt on my roll. I'd remember.` };
		{ Ask = `Why does the bell ring at night?`; Answer = `Old buildings make old noises. Go to bed early, and you won't hear it.` };
	};
})
