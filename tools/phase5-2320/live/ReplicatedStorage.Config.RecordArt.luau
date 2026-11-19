--[[ (2.32) The Permanent Record's art (art/group-upload-record, group 15981569; baked by art/ui/hud/make_record_ui.py).
	Read by Controllers.Gui.StatsPanel. 9-slice centres and scales are listed with each piece. ]]
local Art = {
	Button = 120020200073052;
	ButtonOn = 75021696687886;
	Card = 137593061986741;
	Close = 104835336910101;
	CoverGhoul = 88933349170879;
	CoverHuman = 118082432926309;
	CoverPriest = 71182325931402;
	CoverVampire = 111787881157672;
	CoverWerewolf = 132809827347529;
	CoverWraith = 79074301587789;
	Envelope = 71269410817571;
	Glint = 91916422685090;
	IconAcademics = 90403546963752;
	IconAthletics = 99760352366948;
	IconAttendance = 109974686346043;
	IconCheck = 118413744334921;
	IconClose = 77550041767285;
	IconCombat = 101081845378827;
	IconEntries = 139766993688053;
	IconFactions = 95608856054771;
	IconGrit = 128943458793284;
	IconHonours = 90482925948491;
	IconMight = 105511703637782;
	IconPaths = 77370154378904;
	IconPlus = 128521090250442;
	IconRaceGhoul = 97591479795185;
	IconRaceHuman = 119708117518293;
	IconRacePriest = 88492853806806;
	IconRaceVampire = 127676942086324;
	IconRaceWerewolf = 76740470139561;
	IconRaceWraith = 89205867092227;
	IconSecret = 83589795060977;
	IconSocial = 83572152136153;
	IconStory = 78593575785715;
	IconStudent = 114350468491040;
	IconSupernatural = 104022169295461;
	IconWits = 110942096587200;
	Ink = 132963083648486;
	Medal = 120584043581661;
	MedalDim = 127194915097582;
	Page = 126531895690023;
	Pip = 110286636027922;
	PipOn = 103441689220281;
	PlateGhoul = 70572758554518;
	PlateHuman = 134703198496636;
	PlatePriest = 118395216919172;
	PlateVampire = 100168489979328;
	PlateWerewolf = 80050138425835;
	PlateWraith = 112282888177498;
	Stamp = 94026768732507;
	TabAcademics = 128436401767663;
	TabAthletics = 113137102606317;
	TabAttendance = 76817937480571;
	TabCombat = 134719982385415;
	TabEntries = 88417804897489;
	TabFactions = 139538994395561;
	TabHonours = 100578854210725;
	TabOnAcademics = 98448002568771;
	TabOnAthletics = 98255895489387;
	TabOnAttendance = 99186160203118;
	TabOnCombat = 76139128736515;
	TabOnEntries = 76450876291493;
	TabOnFactions = 131638667265713;
	TabOnHonours = 106727301416046;
	TabOnPaths = 104644147132807;
	TabOnStudent = 121590021636675;
	TabPaths = 86372236302465;
	TabStudent = 107950507713484;
}

-- 9-slice settings: { Rect (source pixels), SliceScale }
Art.Slices = {
	Page = { Rect.new(80, 80, 688, 688), 0.5 }; Card = { Rect.new(56, 56, 264, 264), 0.5 }; Tab = { Rect.new(40, 40, 320, 52), 0.62 };
	Plate = { Rect.new(48, 48, 592, 62), 0.62 }; Button = { Rect.new(34, 34, 190, 38), 0.6 }; Stamp = { Rect.new(36, 36, 284, 74), 0.5 };
}
Art.Races = { `Human`, `Priest`, `Vampire`, `Werewolf`, `Ghoul`, `Wraith` }
Art.Sections = { `Student`, `Academics`, `Attendance`, `Athletics`, `Combat`, `Factions`, `Paths`, `Honours`, `Entries` }

function Art.Id(Name: string): string?
	local V = Art[Name]
	if typeof(V) == `string` then return V end -- (a local preview: rbxasset://)
	return if typeof(V) == `number` and V > 0 then `rbxassetid://` .. V else nil
end

return Art
