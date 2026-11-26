-- tools/electives/stage/anatomy_textures.lua (Edit; generated from stage/anatomy_image_ids.txt): one SurfaceAppearance per
-- baked piece of ReplicatedStorage.Anatomy.Models (group images, 2026-11-25). Glow and Glass pieces have no bake and
-- keep their Neon / Glass dress. Safe to run again: it reuses the SurfaceAppearance.
local TEXTURES = {
	AnatBenchSet_Candle = { Color = 89954020748774, Normal = 77159427460420, Rough = 132041031994957, Metal = 137881631290645 },
	AnatBenchSet_Desk = { Color = 113582167826708, Normal = 117595357775221, Rough = 99520602594512, Metal = 89167004362646 },
	AnatBenchSet_Roll = { Color = 100154236905932, Normal = 124034825853373, Rough = 87092845052720, Metal = 71809084864983 },
	AnatBenchSet_Tray = { Color = 72000009479711, Normal = 78546892743801, Rough = 93725558152849, Metal = 105031362556892 },
	AnatBenchSet_Wax = { Color = 84188839098780, Normal = 88478151012806, Rough = 113228818788076, Metal = 87622734570124 },
	AnatFrog_Body = { Color = 84929703478840, Normal = 91584804229515, Rough = 101653757571357, Metal = 90218204130109 },
	AnatFrog_FlagCog = { Color = 97149946144080, Normal = 99993790841065, Rough = 82200051419557, Metal = 122292589817118 },
	AnatFrog_GearGut = { Color = 125492131098730, Normal = 110713173954630, Rough = 131648817947709, Metal = 109985124555728 },
	AnatFrog_Head = { Color = 92954730629946, Normal = 127607458654902, Rough = 105496124829483, Metal = 96731462471767 },
	AnatFrog_HeartPump = { Color = 113630527475825, Normal = 87540155775925, Rough = 124730489219737, Metal = 138018791828055 },
	AnatFrog_Legs = { Color = 77632912848285, Normal = 77436592919672, Rough = 110763848418757, Metal = 93343237331445 },
	AnatFrog_Lungs = { Color = 72503552823692, Normal = 118559515534346, Rough = 136663828485461, Metal = 129929886082442 },
	AnatFrog_Mechanism = { Color = 124206735248718, Normal = 87861031263812, Rough = 139281615934663, Metal = 106543940695835 },
	AnatFrog_Plate = { Color = 140535283583646, Normal = 131895300742130, Rough = 78727238354379, Metal = 114790856333175 },
	AnatFrog_SideKey = { Color = 133924903026876, Normal = 86241126529841, Rough = 86903602487943, Metal = 94692453428771 },
	AnatRaven_Body = { Color = 85744288036308, Normal = 95450821553026, Rough = 103962798720384, Metal = 110937346935008 },
	AnatRaven_FlagCog = { Color = 132298099104786, Normal = 133825498607917, Rough = 79771840805468, Metal = 113790770386037 },
	AnatRaven_Head = { Color = 113323962044164, Normal = 95931702405133, Rough = 120831997568805, Metal = 127542932365304 },
	AnatRaven_HeartPump = { Color = 106083119924045, Normal = 101659931080887, Rough = 114815366048185, Metal = 127943579731033 },
	AnatRaven_Limbs = { Color = 74320345965296, Normal = 97678409714910, Rough = 109978862254762, Metal = 114880286439874 },
	AnatRaven_Lungs = { Color = 85824327343090, Normal = 103990897298149, Rough = 113772130433168, Metal = 109090235402426 },
	AnatRaven_Mechanism = { Color = 130782840263900, Normal = 100441884754696, Rough = 106710840594405, Metal = 109537422050130 },
	AnatRaven_Plate = { Color = 131485792857766, Normal = 131901073595036, Rough = 133918566077997, Metal = 92587127696188 },
	AnatRaven_SideKey = { Color = 96191764300863, Normal = 129164295665706, Rough = 122638951313230, Metal = 106374866000059 },
	AnatRaven_Tail = { Color = 87911403312893, Normal = 140490444097251, Rough = 86969298277815, Metal = 78237689666528 },
	AnatRaven_VoiceBox = { Color = 86036021909208, Normal = 76795348283356, Rough = 75773357276994, Metal = 108855457514213 },
	AnatRaven_WingPlate1 = { Color = 76895473967962, Normal = 81072705530425, Rough = 108656237292947, Metal = 121010334468897 },
	AnatRaven_WingPlate2 = { Color = 116564847617312, Normal = 101348174328446, Rough = 120764756270032, Metal = 118419995537475 },
	AnatRaven_WingPlate3 = { Color = 74544450914156, Normal = 74085682232748, Rough = 122040584508128, Metal = 87384600215323 },
	AnatRaven_WingPlate4 = { Color = 112448650239089, Normal = 101045746049432, Rough = 109274306302456, Metal = 76229717014925 },
	AnatRaven_WingSpring = { Color = 92512398281597, Normal = 82583459190059, Rough = 75255754018564, Metal = 88488851403266 },
	AnatToolDriver_Main = { Color = 80762328016800, Normal = 95724664133594, Rough = 88780192930192, Metal = 128144528422813 },
	AnatToolKey_Main = { Color = 104040097499169, Normal = 85027591152600, Rough = 77268899177102, Metal = 90965592726826 },
	AnatToolLoupe_Main = { Color = 80314373267331, Normal = 111271814916074, Rough = 104503064777551, Metal = 93736962693207 },
	AnatToolScalpel_Main = { Color = 124198219473832, Normal = 119319619177434, Rough = 91299937879656, Metal = 71964401902617 },
	AnatToolTweezers_Main = { Color = 116949672737614, Normal = 108032354426355, Rough = 90221745915116, Metal = 126996103448604 },
	AnatWyvern_Body = { Color = 120345532310024, Normal = 135257697362303, Rough = 73850798719507, Metal = 123415425818434 },
	AnatWyvern_FireGland = { Color = 118184067578324, Normal = 92315824141286, Rough = 74270953422237, Metal = 85602211200278 },
	AnatWyvern_FlagCog = { Color = 136378324654940, Normal = 132561655172247, Rough = 136246612857092, Metal = 115771365270593 },
	AnatWyvern_GearGut = { Color = 125437885316632, Normal = 90193129464214, Rough = 139848764388890, Metal = 85819006979448 },
	AnatWyvern_Head = { Color = 72500459166595, Normal = 138880047905405, Rough = 131574247703145, Metal = 129453967408046 },
	AnatWyvern_HeartA = { Color = 122054526991381, Normal = 90369265888586, Rough = 126975702218308, Metal = 95667289439719 },
	AnatWyvern_HeartB = { Color = 112197016685804, Normal = 76136687267473, Rough = 132962252819596, Metal = 135956304311581 },
	AnatWyvern_Limbs = { Color = 131863120119289, Normal = 75950613002163, Rough = 135650052376645, Metal = 126606383297074 },
	AnatWyvern_Lungs = { Color = 99481001780538, Normal = 87594471912199, Rough = 110001991828525, Metal = 94541978779349 },
	AnatWyvern_Mechanism = { Color = 113612213677800, Normal = 104293245375819, Rough = 103058624209608, Metal = 111012256390032 },
	AnatWyvern_Plate = { Color = 118779799098699, Normal = 136294921977330, Rough = 93251803910708, Metal = 122244451899124 },
	AnatWyvern_SideKey = { Color = 120451918886200, Normal = 109604911250616, Rough = 99412885203547, Metal = 122448017326134 },
	AnatWyvern_Tail = { Color = 125790508465588, Normal = 127426415169129, Rough = 92653331670342, Metal = 113032959262966 },
}
local n, miss = 0, {}
for _, M in game.ReplicatedStorage.Anatomy.Models:GetChildren() do
	for _, p in M:GetDescendants() do
		if p:IsA("MeshPart") then
			local t = TEXTURES["Anat" .. M.Name .. "_" .. p.Name]
			if t then
				local SA = p:FindFirstChildOfClass("SurfaceAppearance") or Instance.new("SurfaceAppearance")
				SA.ColorMap = "rbxassetid://" .. t.Color
				SA.NormalMap = "rbxassetid://" .. t.Normal
				SA.RoughnessMap = "rbxassetid://" .. t.Rough
				SA.MetalnessMap = "rbxassetid://" .. t.Metal
				SA.Parent = p
				p.Color = Color3.new(1, 1, 1)
				n += 1
			elseif not (p.Name:match("Glow$") or p.Name:match("Glass$")) then
				table.insert(miss, M.Name .. "." .. p.Name)
			end
		end
	end
end
return ("textured %d pieces of %d maps; no maps: %s"):format(n, 49, #miss > 0 and table.concat(miss, ", ") or "none")
