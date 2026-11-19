--[[ (2.32) Honours (docs/expansion/14-Progression-and-Identity.md §4.3): earned entries in the Permanent Record.
	Each: Id, Group, Name, Text (how it's earned, shown before and after), Test(F) on the facts Services.Player.Paths
	builds (see Config.Paths for the shared fields; Paths.Facts adds Passed, APlus, Streak, DetentionsServed,
	DaysClean, InClub, Trusted, Tuned, StrikeGrade). Hidden = a Secret: shown sealed until earned.
	Saved: PlayerData.Progress.Honours[Id] = the school day it was earned. Checked by Services.Player.Honours. ]]
local Honours = {}

local function atLeast(F, Level: number): number
	local N = 0
	for _, L in F.Subjects do if L >= Level then N += 1 end end
	return N
end
local function respected(F): boolean
	for _, T in F.CliqueTiers do if T == `Respected` then return true end end
	return false
end
local CLUB = { Rookie = 1; Starter = 2; Varsity = 3; Captain = 4 }

-- the groups, in the order the Record shows them (Icon = a RecIcon name)
Honours.Groups = {
	{ Id = `Academics`; Name = `Academics`; Icon = `Academics` };
	{ Id = `Conduct`; Name = `Conduct`; Icon = `Attendance` };
	{ Id = `Athletics`; Name = `Athletics`; Icon = `Athletics` };
	{ Id = `Combat`; Name = `Combat`; Icon = `Combat` };
	{ Id = `Society`; Name = `Society`; Icon = `Social` };
	{ Id = `Story`; Name = `Story`; Icon = `Story` };
	{ Id = `Secrets`; Name = `Secrets`; Icon = `Secret` };
}

Honours.List = {
	{ Id = `FirstPass`; Group = `Academics`; Name = `First Pass`; Text = `Pass any lesson.`; Test = function(F) return F.Passed >= 1 end };
	{ Id = `WellRounded`; Group = `Academics`; Name = `Well Rounded`; Text = `Pass a lesson in every subject.`; Test = function(F) return F.Passed >= 4 end };
	{ Id = `TopMarks`; Group = `Academics`; Name = `Top Marks`; Text = `Earn an A+ in a lesson.`; Test = function(F) return F.APlus end };
	{ Id = `Mastery`; Group = `Academics`; Name = `Mastery`; Text = `Reach level 5 in a subject.`; Test = function(F) return atLeast(F, 5) >= 1 end };
	{ Id = `HonorRoll`; Group = `Academics`; Name = `Honor Roll`; Text = `A report card averaging B or better.`; Test = function(F) return F.BestCard >= 4 end };

	{ Id = `Present`; Group = `Conduct`; Name = `Present and Correct`; Text = `A 5-day attendance streak.`; Test = function(F) return F.BestStreak >= 5 end };
	{ Id = `NeverLate`; Group = `Conduct`; Name = `Never Late`; Text = `A 30-day attendance streak.`; Test = function(F) return F.BestStreak >= 30 end };
	{ Id = `TimeServed`; Group = `Conduct`; Name = `Time Served`; Text = `Serve a detention.`; Test = function(F) return F.DetentionsServed >= 1 end };
	{ Id = `SlippedAway`; Group = `Conduct`; Name = `Slipped Away`; Text = `Get away from a hall monitor.`; Test = function(F) return F.Tally.Escapes >= 1 end };
	{ Id = `Spotless`; Group = `Conduct`; Name = `Spotless`; Text = `A 14-day streak with no violation in that time.`; Test = function(F) return F.Streak >= 14 and F.DaysClean >= 14 end };

	{ Id = `SignedUp`; Group = `Athletics`; Name = `Signed Up`; Text = `Join a sports club.`; Test = function(F) return F.InClub end };
	{ Id = `Starter`; Group = `Athletics`; Name = `Starter`; Text = `Reach Starter in your club.`; Test = function(F) return (CLUB[F.ClubRank] or 1) >= 2 end };
	{ Id = `Varsity`; Group = `Athletics`; Name = `Varsity`; Text = `Reach Varsity in your club.`; Test = function(F) return (CLUB[F.ClubRank] or 1) >= 3 end };
	{ Id = `Captain`; Group = `Athletics`; Name = `Captain`; Text = `Captain your club.`; Test = function(F) return (CLUB[F.ClubRank] or 1) >= 4 end };

	{ Id = `FirstTakedown`; Group = `Combat`; Name = `First Takedown`; Text = `Down someone in a fight.`; Test = function(F) return F.Takedowns >= 1 end };
	{ Id = `Duelist`; Group = `Combat`; Name = `Duelist`; Text = `Win a duel.`; Test = function(F) return F.Tally.DuelWins >= 1 end };
	{ Id = `RingChampion`; Group = `Combat`; Name = `Champion of the Ring`; Text = `Beat the Ring's champion.`; Test = function(F) return F.Tally.Champion >= 1 end };
	{ Id = `BeastHunter`; Group = `Combat`; Name = `Beast Hunter`; Text = `Bring down a beast.`; Test = function(F) return F.Tally.Beasts >= 1 end };
	{ Id = `Showdown`; Group = `Combat`; Name = `Showdown`; Text = `Beat a clique leader in a showdown.`; Test = function(F) return F.Showdowns >= 1 end };

	{ Id = `Introductions`; Group = `Society`; Name = `Introductions`; Text = `Meet 10 classmates.`; Test = function(F) return F.Met >= 10 end };
	{ Id = `AFriend`; Group = `Society`; Name = `A Friend`; Text = `Earn a classmate's trust.`; Test = function(F) return F.Trusted >= 1 end };
	{ Id = `InnerCircle`; Group = `Society`; Name = `Inner Circle`; Text = `Reach a faction's Inner Circle.`; Test = function(F) return F.FactionRank >= 5 end };
	{ Id = `Respected`; Group = `Society`; Name = `Respected`; Text = `Be Respected by a clique.`; Test = respected };
	{ Id = `Superlative`; Group = `Society`; Name = `Superlative`; Text = `Win a weekly superlative.`; Test = function(F) return F.Tally.Superlatives >= 1 end };

	{ Id = `RollCall`; Group = `Story`; Name = `Roll Call`; Text = `Finish Orientation.`; Test = function(F) return F.Orientation end };
	{ Id = `AfterHours`; Group = `Story`; Name = `After Hours`; Text = `Finish After Hours.`; Test = function(F) return F.AfterHours end };
	{ Id = `KeptFile`; Group = `Story`; Name = `Kept the File`; Text = `Finish After Hours with Mira's file whole.`; Test = function(F) return F.FileKept end };
	{ Id = `Evolved`; Group = `Story`; Name = `Evolved`; Text = `Reach your race's second tier.`; Test = function(F) return F.LineageTier >= 2 end };

	{ Id = `TunedIn`; Group = `Secrets`; Name = `Tuned In`; Text = `Hear Night FM's introduction.`; Hidden = true; Test = function(F) return F.Tuned end };
	{ Id = `Flawless`; Group = `Secrets`; Name = `Flawless`; Text = `An S on the Strikethrough.`; Hidden = true; Test = function(F) return F.StrikeGrade == `S` end };
}

Honours.ById = {}
for _, H in Honours.List do Honours.ById[H.Id] = H end

return Honours
