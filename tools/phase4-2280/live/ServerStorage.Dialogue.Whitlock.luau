-- Dr. Whitlock (2.28). History, Room 105. The school's own historian: knows the False Explanation by heart, believes it.
local Template = require(script.Parent.GiverTemplate)

return Template({
	Greeting = `History is happening, you know. Sit down for it.`;
	Bye = `Mind the dates.`;
	Talk = {
		{ Ask = `How old is the school?`; Answer = `Founded 1887. A fire at the north gate that same year. Tragic. Well documented.` };
		{ Ask = `What happened to the students in the fire?`; Answer = `Transferred. It's all in the records. Every one of them.` };
		{ Ask = `Who's in the old painting?`; Answer = `The Class of 1887. All present and accounted for.` };
	};
})
