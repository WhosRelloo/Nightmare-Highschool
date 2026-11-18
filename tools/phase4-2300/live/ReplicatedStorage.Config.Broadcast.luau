--[[ (2.30) Broadcast wording (World.Broadcast). The PA speaks only of real state (doc 13 §5.2), at most once per school
	segment (emergencies aside). The station (Night FM "Midnight Broadcast") is on air 21:00 to 03:00. ]]
return {
	PA = {
		BeforeSchool = { "Good morning, students. Homeroom begins at eight. Do not be late; the register is kept." };
		Substitute = { "A substitute will cover {Subject} today. Mind your manners." };
		Lunch = { "The lunch period has begun. Mrs. Okada's stand is open by the west doors." };
		AfterSchool = { "Classes are dismissed. Clubs meet now. The building closes at ten." };
		Curfew = { "Curfew is now in force. All students to the dorms. The halls are patrolled." };
		Rumble = { "Students are to clear {Place} at once. Staff are on their way." };
	};
	Transmissions = {
		"...and the roll is read. Holt. Mira Holt. ...No answer. No answer. No answer.",
		"A voice on the static, very calm: 'Answer the bell, and you will be kept.'",
		"Somewhere under the music, a register being read. One name too many.",
		"Static, and a girl humming the school hymn a beat behind the choir.",
	};
	Kickers = { Announcement = `ANNOUNCEMENT`; IncidentReport = `CAMPUS REPORT`; CallerLine = `CALLER LINE`; Transmission = `TRANSMISSION` };
	MaxItems = 40;
	StationFrom = 21; StationTo = 3; -- hours (wraps past midnight)
	CurfewHour = 22;
	Chime = `rbxassetid://9114058995`; -- the desk bell (the kit's Confirm and Moments' Chime)
}
