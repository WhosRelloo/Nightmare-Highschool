
---| Services |---

local RunService = game:GetService(`RunService`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

---| Modules |---

local PlayerData = require(ReplicatedStorage.PlayerData)

---| Type Annotation |---

export type PlayerData = PlayerData.PlayerData

export type StateAction = 
	
	{
		type: 'UpdateYen';
		amount: number;
	} |
	{
		type: 'UpdateWeapon';
		weapon: string;
	} |
	{
		type: 'AddKill';
		victim: 'Player' | 'NPC';
	} |
	{
		type: 'SetAttendance';
		attendance: any;
	} |
	{
		type: 'SetDiscipline';
		discipline: any;
	} |
	{
		type: 'SetClasses';
		classes: any;
	} |
	{
		type: 'SetSocial';
		social: any;
	} |
	{
		type: 'SetQuests';
		quests: any;
	} |
	{
		type: 'SetSettings';    -- validated by ReplicatedStorage.UI.Settings.Sanitize on the server
		settings: any;
	} |
	{
		type: 'SetAppearance';  -- validated by ReplicatedStorage.UI.Appearance.Sanitize on the server
		appearance: any;
	} |
	{
		type: 'SetLastJoined';  -- written by the server directory on join
		lastJoined: any;
	} |
	{
		type: 'SetLastPlayed';   -- os.time() of the last Enter School (Services.Player.Slots: CONTINUE picks the newest)
		lastPlayed: number;
	} |
	{
		type: 'SetLineage';     -- server-rolled race / variant / traits / spins (ReplicatedStorage.Lineage)
		lineage: any;
	} |
	{
		type: 'SetIdentity';    -- first name + server-rolled clan (Services.Player.Identity)
		identity: any;
	} |
	{
		type: 'SetPurchases';   -- granted Robux receipt ids (Services.Player.Purchases)
		purchases: any;
	} |
	{
		type: 'SetKnown';       -- students whose name you know (Services.Social.Strangers)
		known: any;
	} |
	{
		type: 'SetProgress';    -- EXP, level, stat points (Services.Player.Progression)
		progress: any;
	} |
	{
		type: 'SetPhone';       -- wallet history and Night FM recents (Services.Features.Phone)
		phone: any;
	} |
	{
		type: 'SetRegions';     -- places found (Services.Features.Regions; Config.Regions.Sanitize)
		regions: any;
	} |
	{
		type: 'SetInventory';   -- snacks and hotbar pins (Services.Features.Inventory)
		inventory: any;
	} |
	{
		type: 'SetSports';     -- club, club EXP, records, drill bests (Services.Sports.Clubs)
		sports: any;
	} |
	{
		type: 'SetArcade';     -- the phone's arcade bests { Best = { [game] = n } } (Services.Features.PhoneGames)
		arcade: any;
	} |
	{
		type: 'SetTraining';   -- (training 1.81) the three training areas, streak and bests (Services.Features.Training; Config.Training.Sanitize)
		training: any;
	} |
	{
		type: 'SetHousing';    -- homes owned, the current one, Mom & Dad's cut-off (Services.Features.Homes; Config.Homes.Sanitize)
		housing: any;
	}

---| Update State |---

return function (PlayerData: PlayerData, Action: StateAction): boolean ?
	
	if Action.type == `UpdateYen` then
		PlayerData.Yen += Action.amount
		
	end
	
	if Action.type == `UpdateWeapon` then
		PlayerData.Weapon = Action.weapon
		
	end

	if Action.type == `SetAttendance` then
		PlayerData.Attendance = Action.attendance
	end

	if Action.type == `SetDiscipline` then
		PlayerData.Discipline = Action.discipline
	end

	if Action.type == `SetClasses` then
		PlayerData.Classes = Action.classes
	end

	if Action.type == `SetSocial` then
		PlayerData.Social = Action.social
	end

	if Action.type == `SetQuests` then
		PlayerData.Quests = Action.quests
	end

	if Action.type == `SetSettings` then
		PlayerData.Settings = Action.settings
	end

	if Action.type == `SetAppearance` then
		PlayerData.Appearance = Action.appearance
	end

	if Action.type == `SetLastPlayed` then
		PlayerData.LastPlayed = Action.lastPlayed
	end

	if Action.type == `SetLastJoined` then
		PlayerData.LastJoined = Action.lastJoined
	end

	if Action.type == `SetLineage` then
		PlayerData.Lineage = Action.lineage
	end

	if Action.type == `SetIdentity` then
		PlayerData.Identity = Action.identity
	end

	if Action.type == `SetPurchases` then
		PlayerData.Purchases = Action.purchases
	end

	if Action.type == `SetKnown` then
		PlayerData.Known = Action.known
	end

	if Action.type == `SetProgress` then
		PlayerData.Progress = Action.progress
	end

	if Action.type == `SetPhone` then
		PlayerData.Phone = Action.phone
	end

	if Action.type == `SetRegions` then
		PlayerData.Regions = Action.regions
	end

	if Action.type == `SetInventory` then
		PlayerData.Inventory = Action.inventory
	end

	if Action.type == `SetSports` then
		PlayerData.Sports = Action.sports
	end

	if Action.type == `SetArcade` then
		PlayerData.Arcade = Action.arcade
	end

	if Action.type == `SetHousing` then
		PlayerData.Housing = Action.housing
	end

	if Action.type == `SetTraining` then
		PlayerData.Training = Action.training
	end

	if Action.type == `AddKill` then
		if Action.victim == `Player` then
			PlayerData.Kills = (PlayerData.Kills or 0) + 1
		else
			PlayerData.NPCKills = (PlayerData.NPCKills or 0) + 1
		end
	end
	
end
