-- Ms. Sallow (2.28). Mathematics, Room 102. Exact, dry; keeps a ruler she never uses.
local Template = require(script.Parent.GiverTemplate)

return Template({
	Greeting = `You're early, or you're late. Which?`;
	Bye = `Mind the margins.`;
	Talk = {
		{ Ask = `What are we doing in class?`; Answer = `Proofs. Everything in this school wants proving.` };
		{ Ask = `Why do you carry a ruler?`; Answer = `Lines should be straight. Very little here is.` };
		{ Ask = `Did you teach Mira Holt?`; Answer = `The register says I didn't. The register is usually right.` };
	};
})
