--[[ (2.31) Standing Paths (docs/expansion/14-Progression-and-Identity.md §3.1). Read by Services.Player.Paths.
	Each tier: Name, Title (granted through Reputation.AwardTitle; tier 1 grants none), Need = { { Text, Test(F) } }, all
	of which must pass. F is the facts snapshot Paths.Facts builds:
	  Subjects = { [Subject] = class level 1..5 }, BestStreak, BestCard (the best kept report card's average: A+ 6, A 5,
	  B 4, C 3, D 2, F 1, none 0), Rep = { Popularity, Intimidation, Trust, Academics } (0..100), Met (rostered classmates
	  met), CliqueTiers = { [CliqueId] = tier name }, FactionRank (best rank index, 1 Outsider .. 5 Inner Circle),
	  Takedowns (Kills + NPCKills), Showdowns (clique leaders beaten), ClubRank (Rookie .. Captain), Orientation,
	  AfterHours, FileKept (booleans), LineageTier, and Tally = { DuelWins, Champion, Beasts, Escapes, Superlatives }. ]]
local Paths = {}

local function atLeast(F, Level: number): number
	local N = 0
	for _, L in F.Subjects do if L >= Level then N += 1 end end
	return N
end
local function cliques(F, Tiers: { string }): number
	local N = 0
	for _, T in F.CliqueTiers do if table.find(Tiers, T) then N += 1 end end
	return N
end
local function need(Text: string, Test) return { Text = Text; Test = Test } end
local CLUB = { Rookie = 1; Starter = 2; Varsity = 3; Captain = 4 }

Paths.Order = { `Academic`, `Social`, `Combat`, `Athletic`, `Supernatural` }
Paths.Tally = { `DuelWins`, `Champion`, `Beasts`, `Escapes`, `Superlatives`, `MatchWins` } -- (2.33) MatchWins: ranked club games won
Paths.Subjects = 4

Paths.Paths = {
	Academic = { Tiers = {
		{ Name = `Freshman Nobody`; Need = {} };
		{ Name = `Recognized Student`; Title = `Recognized Student`; Need = {
			need(`2 subjects at level 2`, function(F) return atLeast(F, 2) >= 2 end);
			need(`a 3-day attendance streak`, function(F) return F.BestStreak >= 3 end) } };
		{ Name = `Honor Student`; Title = `Honor Student`; Unlock = { Accessory = `path-academic-pin` }; Need = {
			need(`3 subjects at level 4`, function(F) return atLeast(F, 4) >= 3 end);
			need(`a B report card`, function(F) return F.BestCard >= 4 end);
			need(`a 10-day attendance streak`, function(F) return F.BestStreak >= 10 end) } };
		{ Name = `Academic Elite`; Title = `Academic Elite`; Need = {
			need(`every subject at level 5`, function(F) return atLeast(F, 5) >= Paths.Subjects end);
			need(`an A report card`, function(F) return F.BestCard >= 5 end);
			need(`Academics 50`, function(F) return F.Rep.Academics >= 50 end) } };
	} };
	Social = { Tiers = {
		{ Name = `Unknown`; Need = {} };
		{ Name = `Recognized`; Title = `Recognized`; Need = {
			need(`meet 5 classmates`, function(F) return F.Met >= 5 end) } };
		{ Name = `Popular`; Title = `Popular`; Unlock = { Uniform = `path-rolled-sleeves` }; Need = {
			need(`meet 12 classmates`, function(F) return F.Met >= 12 end);
			need(`Popularity 25`, function(F) return F.Rep.Popularity >= 25 end);
			need(`Friendly with 2 cliques`, function(F) return cliques(F, { `Friendly`, `Respected` }) >= 2 end) } };
		{ Name = `Influential`; Title = `Influential`; Need = {
			need(`Member of a faction`, function(F) return F.FactionRank >= 3 end);
			need(`Popularity 50`, function(F) return F.Rep.Popularity >= 50 end);
			need(`Respected by a clique`, function(F) return cliques(F, { `Respected` }) >= 1 end) } };
		{ Name = `School Legend`; Title = `School Legend`; Need = {
			need(`a faction's Inner Circle`, function(F) return F.FactionRank >= 5 end);
			need(`Popularity 80`, function(F) return F.Rep.Popularity >= 80 end);
			need(`meet all 24 classmates`, function(F) return F.Met >= 24 end);
			need(`win a weekly superlative`, function(F) return F.Tally.Superlatives >= 1 end) } };
	} };
	Combat = { Tiers = {
		{ Name = `Beginner`; Need = {} };
		{ Name = `Street Fighter`; Title = `Street Fighter`; Need = {
			need(`5 takedowns`, function(F) return F.Takedowns >= 5 end) } };
		{ Name = `Enforcer`; Title = `Enforcer`; Unlock = { Uniform = `path-loose-tie` }; Need = {
			need(`25 takedowns`, function(F) return F.Takedowns >= 25 end);
			need(`win 3 duels`, function(F) return F.Tally.DuelWins >= 3 end);
			need(`Intimidation 25`, function(F) return F.Rep.Intimidation >= 25 end) } };
		{ Name = `Notorious`; Title = `Notorious`; Unlock = { Accessory = `path-knuckle-wraps` }; Need = {
			need(`75 takedowns`, function(F) return F.Takedowns >= 75 end);
			need(`win a clique showdown`, function(F) return F.Showdowns >= 1 end);
			need(`3 beasts`, function(F) return F.Tally.Beasts >= 3 end);
			need(`Intimidation 50`, function(F) return F.Rep.Intimidation >= 50 end) } };
		{ Name = `Feared`; Title = `Feared`; Need = {
			need(`150 takedowns`, function(F) return F.Takedowns >= 150 end);
			need(`beat the Ring's champion`, function(F) return F.Tally.Champion >= 1 end);
			need(`Intimidation 80`, function(F) return F.Rep.Intimidation >= 80 end) } };
	} };
	Athletic = { Tiers = { -- exactly the sports club rank (Config.Sports), never recomputed
		{ Name = `Rookie`; Need = {} };
		{ Name = `Starter`; Title = `Starter`; Need = { need(`Starter in your club`, function(F) return (CLUB[F.ClubRank] or 1) >= 2 end) } };
		{ Name = `Varsity`; Title = `Varsity`; Unlock = { Uniform = `varsity-jacket` }; Need = { need(`Varsity in your club`, function(F) return (CLUB[F.ClubRank] or 1) >= 3 end) } };
		{ Name = `Captain`; Title = `Captain`; Need = { need(`Captain of your club`, function(F) return (CLUB[F.ClubRank] or 1) >= 4 end) } };
	} };
	Supernatural = { Tiers = {
		{ Name = `Unaware`; Need = {} };
		{ Name = `Uneasy`; Title = `Uneasy`; Need = {
			need(`finish Orientation, or meet a beast`, function(F) return F.Orientation or F.Tally.Beasts >= 1 end) } };
		{ Name = `Initiated`; Title = `Initiated`; Unlock = { Uniform = `path-worn-blazer` }; Need = {
			need(`finish After Hours`, function(F) return F.AfterHours end);
			need(`lineage tier 2, or 5 beasts`, function(F) return F.LineageTier >= 2 or F.Tally.Beasts >= 5 end) } };
		{ Name = `Keeper of Secrets`; Title = `Keeper of Secrets`; Unlock = { Accessory = `path-silver-sigil` }; Need = {
			need(`keep the file in After Hours`, function(F) return F.FileKept end);
			need(`lineage tier 3, or 10 beasts`, function(F) return F.LineageTier >= 3 or F.Tally.Beasts >= 10 end) } };
	} };
}

-- the lines that mention a student by tier (Services.World.Broadcast), tier 4 and up
Paths.Mention = "Congratulations to {Name}, now {Article} {Tier}." -- (a plain string: {Name} is filled by Paths, not interpolated)

return Paths
