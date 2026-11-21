--[[ (2.36) The Bell Tower HUD art: art/group-upload-belltower, group 15981569, baked by art/ui/hud/make_belltower.py.
	An id of 0 means "not uploaded yet". The HUD then draws that piece's kit fallback (Functions.BellTower.Image).
	Slices: 9-slice centres in source pixels and the SliceScale that draws them at the HUD's design size. ]]
local Art = {
	Dial = 0;
	DialHand = 0;
	TowerPlate = 0;
	Seal = 0;
	SealBroken = 0;
	Slip = 0;
	LeadCard = 0;
	PipEmpty = 0;
	PipFang = 0;
}
Art.Slices = {
	TowerPlate = { Center = Rect.new(60, 60, 540, 140); Scale = 0.5 };
	LeadCard = { Center = Rect.new(140, 130, 880, 250); Scale = 0.47 };
	Slip = { Center = Rect.new(90, 40, 380, 110); Scale = 0.68 };
}
return Art
