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
	-- (2.30) Night FM's voices (the owner's clips, art/sfx/NightFM): the station's host, the hall monitors' bulletins, the
	-- PSA and the lore. World.Broadcast.Voice picks one when you tune in (the Station tab), then the next after VoiceGap
	-- seconds of music while you stay tuned. Id 0 = not uploaded yet: that clip is skipped. From/To are hours, a [From, To)
	-- window that may wrap past midnight.
	Voice = {
		FirstTune = { Id = 0; Len = 28; Who = `Night FM`; Title = `You're listening to Night FM` }; -- the first time you ever tune in after dark
		WelcomeBack = { Id = 0; Len = 16; Who = `Night FM`; Title = `And we're back` }; -- your first tune-in of a later night
		PSA = { Id = 0; Len = 23; Who = `Public service`; Title = `Stay inside, stay out of trouble`; From = 20; To = 23 };
		Hello = { Id = 0; Len = 10; Who = `Night FM`; Title = `A special hello`; From = 21; To = 3 };
		Quiet = { Id = 0; Len = 15; Who = `Night FM`; Title = `A suspiciously quiet day`; From = 15; To = 3; QuietOnly = true }; -- only with no campus report today
		Lore1 = { Id = 0; Len = 33; Who = `Night FM`; Title = `About Mira Holt`; From = 23; To = 3 };
		Lore2 = { Id = 0; Len = 20; Who = `Night FM`; Title = `The photograph from 1887`; From = 23; To = 3 };
		SignOff = { Id = 0; Len = 18; Who = `Night FM`; Title = `Signing off`; From = 2.5; To = 3 }; -- the last half hour
		HallMonitor1 = { Id = 0; Len = 19; Who = `Hall monitor`; Title = `The dress code remains in effect`; From = 6; To = 12 };
		Afternoon = { Id = 0; Len = 16; Who = `Night FM`; Title = `The afternoon is rolling along`; From = 12; To = 18 };
		HallMonitor2 = { Id = 0; Len = 19; Who = `Hall monitor`; Title = `After hours, the halls are patrolled`; From = 15; To = 21 };
	};
	VoiceGap = 45;
}
