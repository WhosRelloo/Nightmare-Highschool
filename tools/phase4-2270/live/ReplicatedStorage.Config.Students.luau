--[[ (2.27) The roster: 24 named students, 3 per clique (docs/expansion/13-Living-School.md §2.1, §8).
	Ids are save keys: never rename one. Temper picks greeting and introduction lines; Set is the timetable set
	(2.28). Bravery feeds NpcBuilds' personality. SkipChance (Delinquents): the chance per class period they skip (2.28). ]]
local List = {
	{ Id = `OdetteMarsh`; Name = `Odette Marsh`; Clique = `Choir`; Year = 3; Bravery = 0.3; Temper = `Warm`; Set = `A`;
		Bio = `First soprano. Swears the chapel organ plays one note after the hymn ends.` };
	{ Id = `SilasPenwright`; Name = `Silas Penwright`; Clique = `Choir`; Year = 2; Bravery = 0.5; Temper = `Cool`; Set = `B`;
		Bio = `Copies every hymn by hand, and keeps the pages nobody sings.` };
	{ Id = `AgnesLowe`; Name = `Agnes Lowe`; Clique = `Choir`; Year = 1; Bravery = 0.2; Temper = `Shy`; Set = `C`;
		Bio = `New to the Choir. Hums when she's frightened, which is often.` };
	{ Id = `CassiusRook`; Name = `Cassius Rook`; Clique = `Court`; Year = 4; Bravery = 0.8; Temper = `Sharp`; Set = `D`;
		Bio = `Vesper's right hand. Smiles at you the way a cat smiles at a bird.` };
	{ Id = `MargueriteDray`; Name = `Marguerite Dray`; Clique = `Court`; Year = 3; Bravery = 0.6; Temper = `Cool`; Set = `A`;
		Bio = `Collects favours like other people collect stamps.` };
	{ Id = `TeodorBlackwell`; Name = `Teodor Blackwell`; Clique = `Court`; Year = 2; Bravery = 0.5; Temper = `Sharp`; Set = `B`;
		Bio = `Old family, older manners. Never seen eating in daylight.` };
	{ Id = `ImogenHart`; Name = `Imogen Hart`; Clique = `Vigil`; Year = 3; Bravery = 0.8; Temper = `Cool`; Set = `C`;
		Bio = `Ezra's best tracker. Writes every patrol in a notebook she won't show anyone.` };
	{ Id = `FelixCorran`; Name = `Felix Corran`; Clique = `Vigil`; Year = 2; Bravery = 0.7; Temper = `Warm`; Set = `D`;
		Bio = `Joined the Vigil to be brave. Still working on it, loudly.` };
	{ Id = `NadiaStroud`; Name = `Nadia Stroud`; Clique = `Vigil`; Year = 4; Bravery = 0.9; Temper = `Sharp`; Set = `A`;
		Bio = `Has been on night watch so long she sleeps standing up.` };
	{ Id = `JuniperFenn`; Name = `Juniper Fenn`; Clique = `Ink`; Year = 2; Bravery = 0.4; Temper = `Wild`; Set = `B`;
		Bio = `Draws the school's corridors from memory, and some that aren't there.` };
	{ Id = `OttoKesler`; Name = `Otto Kesler`; Clique = `Ink`; Year = 3; Bravery = 0.3; Temper = `Cool`; Set = `C`;
		Bio = `Prints the Ink Club's zine. Knows which rumours are true and sells the rest.` };
	{ Id = `BeatrixLull`; Name = `Beatrix Lull`; Clique = `Ink`; Year = 1; Bravery = 0.5; Temper = `Warm`; Set = `D`;
		Bio = `Sable's newest student. Reads tea leaves badly and palms worse.` };
	{ Id = `MarcusAdeyemi`; Name = `Marcus Adeyemi`; Clique = `Athletes`; Year = 4; Bravery = 0.9; Temper = `Warm`; Set = `A`;
		Bio = `Sprinter. Says the north field is faster at night, and won't say why.` };
	{ Id = `TamsinRowe`; Name = `Tamsin Rowe`; Clique = `Athletes`; Year = 2; Bravery = 0.7; Temper = `Sharp`; Set = `B`;
		Bio = `Captain's pick for the Ravens. Plays like she's being chased.` };
	{ Id = `LeoBrandt`; Name = `Leo Brandt`; Clique = `Athletes`; Year = 3; Bravery = 0.6; Temper = `Cool`; Set = `C`;
		Bio = `Goalkeeper. Has never let in a goal after midnight.` };
	{ Id = `ClaraWebb`; Name = `Clara Webb`; Clique = `Ordinary`; Year = 1; Bravery = 0.3; Temper = `Warm`; Set = `D`;
		Bio = `Just wants to get through the term. The term has other ideas.` };
	{ Id = `SamPettigrew`; Name = `Sam Pettigrew`; Clique = `Ordinary`; Year = 2; Bravery = 0.4; Temper = `Shy`; Set = `A`;
		Bio = `Sits by the window in every class. Sometimes waves at nobody.` };
	{ Id = `HenryMoss`; Name = `Henry Moss`; Clique = `Ordinary`; Year = 3; Bravery = 0.5; Temper = `Cool`; Set = `B`;
		Bio = `Runs a quiet trade in homework. Cash, snacks or secrets.` };
	{ Id = `RonanFell`; Name = `Ronan Fell`; Clique = `Pack`; Year = 3; Bravery = 0.8; Temper = `Wild`; Set = `C`;
		Bio = `Howls at the full moon for a laugh. Mostly for a laugh.` };
	{ Id = `KitHarrow`; Name = `Kit Harrow`; Clique = `Pack`; Year = 2; Bravery = 0.6; Temper = `Warm`; Set = `D`;
		Bio = `Loyal to the Pack first, the school second, homework a distant fifth.` };
	{ Id = `MaeGorse`; Name = `Mae Gorse`; Clique = `Pack`; Year = 4; Bravery = 0.9; Temper = `Sharp`; Set = `A`;
		Bio = `Leads the Pack's night runs. Nobody has ever beaten her back to the dorms.` };
	{ Id = `JaxCalloway`; Name = `Jax Calloway`; Clique = `Delinquents`; Year = 3; Bravery = 0.8; Temper = `Wild`; Set = `B`; SkipChance = 0.2;
		Bio = `Has a detention record longer than his attendance record.` };
	{ Id = `NicoRuiz`; Name = `Nico Ruiz`; Clique = `Delinquents`; Year = 2; Bravery = 0.6; Temper = `Cool`; Set = `C`; SkipChance = 0.15;
		Bio = `Picks locks for practice. Has never been caught, which worries him.` };
	{ Id = `SloaneMercer`; Name = `Sloane Mercer`; Clique = `Delinquents`; Year = 4; Bravery = 0.7; Temper = `Sharp`; Set = `D`; SkipChance = 0.15;
		Bio = `Runs the Back Lot dice game. The house always wins; she is the house.` };
}
local ById = {}
for _, E in List do
	E.First = string.match(E.Name, `^(%S+)`)
	ById[E.Id] = E
end
return {
	List = List;
	ById = ById;
	Tempers = { `Warm`, `Cool`, `Sharp`, `Shy`, `Wild` };
	Sets = { `A`, `B`, `C`, `D` };
}
