--[[
	Investigation cases (shared). Clue text and the deduction question are public; which clues link
	up and the right answer live server-side in ServerStorage.QuestSecrets, so the client can't
	read the solution.

	Clues are found by using the quest object of the same id (Config.Quests.Objects[..].Clue), or
	granted by quests (Grants).
]]

return {
	EmptyDesk = {
		Name = `The Empty Desk`;
		Subject = `Mira Holt, Room 102, back row`;
		Clues = {
			LockerNote = { Name = `The locker note`; Where = `Locker 113`;
				Text = `"Room 102. Back row. Before they finish erasing her." No signature. The handwriting slants like it was written in a hurry.` };
			DeskCarving = { Name = `Carved initials`; Where = `Room 102, back-row desk`;
				Text = `"M.H." cut deep into the desk, and under it, smaller: DON'T ANSWER ROLL CALL.` };
			AttendanceSheet = { Name = `The homeroom register`; Where = `Room 101, teacher's desk`;
				Text = `Line 14 of the register has been scraped clean. The paper is thin there, but you can still feel the dent of a name: HOLT.` };
			ArchiveCard = { Name = `A borrowing card`; Where = `The Library Archive`;
				Text = `A card for "Register of Students, original copy", checked out to M. Holt the day before she stopped coming in. Stamped RETURNED TO RECORDS OFFICE.` };
			MiraFile = { Name = `Mira Holt's file`; Where = `The Records Office`;
				Text = `Her photo, her timetable, her grades. And one line in fresh red ink across the bottom: STATUS: COLLECTED.` };
		};
		Deduction = {
			Question = `Where is Mira Holt's original record kept?`;
			Options = { `The Library Archive`, `The Records Office`, `The Boiler Yard`, `Room 102` };
		};
	};
}
