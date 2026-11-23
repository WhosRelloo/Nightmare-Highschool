--[[ (2.36) The Bell Tower HUD art: art/group-upload-belltower, group 15981569, baked by art/ui/hud/make_belltower.py.
	An id of 0 means "not uploaded yet". The HUD then draws that piece's kit fallback (Functions.BellTower.Image).
	Slices: 9-slice centres in source pixels and the SliceScale that draws them at the HUD's design size. ]]
local Art = {
	Dial = 93892744369524;
	DialHand = 78039527171573;
	TowerPlate = 129283325483369;
	Seal = 133512351138579;
	SealBroken = 132264578552566;
	Slip = 118395926975311;
	LeadCard = 78392319140082;
	PipEmpty = 79927335523001;
	PipFang = 116823141480891;
	BellHollow = 73177035232417;    -- (2.37) R2
	BellTarnished = 132965538168678;
	BellLit = 82432772953626;
	BellGlow = 96913118397929;      -- greyscale halo, tinted Gold (the feathered re-upload)
	BellRail = 126038840460786;
}
Art.Slices = {
	TowerPlate = { Center = Rect.new(60, 60, 540, 140); Scale = 0.5 };
	LeadCard = { Center = Rect.new(140, 130, 880, 250); Scale = 0.47 };
	Slip = { Center = Rect.new(90, 40, 380, 110); Scale = 0.68 };
}
return Art
