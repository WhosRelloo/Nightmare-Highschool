--[[
	Day/night look (client grade). ReplicatedStorage.Config.DayCycle
	Read by Controllers.World.DayCycle. Tune freely; the values blend smoothly between keyframes by hour.

	Approved look (VFX design bible D3): normal nights are a moody blue-violet that stays readable.
	"Night" starts at 20:00 to match night powers, EXP and the full moon (D6).
	Crimson "Nightmare Nights" come later as a school event (catalog P4-1); not handled here.

	Day = the place's own Edit lighting, so daytime looks exactly as before.
]]

local rgb = Color3.fromRGB

local Night = {
	-- as bright overall as the old default night (70,70,70), but blue-violet, so dark outfits stay readable
	Ambient = rgb(30, 28, 46); OutdoorAmbient = rgb(76, 70, 114); Brightness = 1.6; ExposureCompensation = 0.1;
	Density = 0.36; Offset = 0.1; Haze = 1.6; Glare = 0; AtmosphereColor = rgb(96, 90, 140); Decay = rgb(44, 36, 72);
	Bloom = 1.15;
	GradeBrightness = -0.02; Contrast = 0.1; Saturation = -0.15; Tint = rgb(212, 206, 255);
}

local Dawn = {
	Ambient = rgb(8, 8, 12); OutdoorAmbient = rgb(100, 86, 96); Brightness = 1.8; ExposureCompensation = 0;
	Density = 0.31; Offset = 0.2; Haze = 1.0; Glare = 0; AtmosphereColor = rgb(222, 190, 180); Decay = rgb(150, 120, 130);
	Bloom = 1.05;
	GradeBrightness = 0; Contrast = 0.03; Saturation = -0.04; Tint = rgb(255, 232, 222);
}

local Day = {
	Ambient = rgb(0, 0, 0); OutdoorAmbient = rgb(70, 70, 70); Brightness = 2; ExposureCompensation = 0;
	Density = 0.3; Offset = 0.25; Haze = 0; Glare = 0; AtmosphereColor = rgb(199, 199, 199); Decay = rgb(106, 112, 125);
	Bloom = 1;
	GradeBrightness = 0; Contrast = 0; Saturation = 0; Tint = rgb(255, 255, 255);
}

local Dusk = {
	Ambient = rgb(14, 10, 14); OutdoorAmbient = rgb(110, 82, 78); Brightness = 1.8; ExposureCompensation = 0;
	Density = 0.33; Offset = 0.2; Haze = 1.4; Glare = 0; AtmosphereColor = rgb(214, 160, 140); Decay = rgb(120, 76, 88);
	Bloom = 1.08;
	GradeBrightness = 0; Contrast = 0.05; Saturation = -0.05; Tint = rgb(255, 226, 210);
}

return {
	Enabled = true;
	UpdateSeconds = 0.2;   -- how often the grade is re-blended (the clock moves slowly)
	-- { hour, look }, sorted; the first and last wrap around midnight
	Keys = {
		{ 0, Night };
		{ 5.5, Night };
		{ 6.5, Dawn };
		{ 8, Day };
		{ 16.5, Day };
		{ 18.5, Dusk };
		{ 20, Night };
		{ 24, Night };
	};
	Looks = { Night = Night; Dawn = Dawn; Day = Day; Dusk = Dusk };

	-- (2.16) Painted skies, one per look (concept 58). Art: tools/vfx/make_skyboxes.py -> art/group-upload-skies
	-- (NHSky<Set>_<Face>.png). Fill a set's six ids once they are uploaded (a number or "rbxassetid://..."); a set with
	-- any id empty is skipped and the place's own Sky stays, so with every id empty this changes nothing at all.
	-- Only the six Skybox faces and SkyboxOrientation are written: the moon texture, its size and StarCount stay
	-- World.FullMoon's / World.MoonPhases'.
	Skies = {
		Enabled = true;
		SwapSeconds = 3;   -- two Sky layers can't blend: the haze swells over this long and the faces change at its peak
		SwapHaze = 1.2;    -- the extra Atmosphere.Haze at the peak of a swap
		-- { from hour, set, turn }: sorted; the last runs past midnight into the first. The swaps sit where the
		-- haze is already up (dusk and dawn). turn = SkyboxOrientation Y in degrees: dawn reuses the dusk faces,
		-- turned so the painted glow sits where the sun rises (+X) instead of where it sets (-X).
		Schedule = {
			{ 0, `Night` };
			{ 5.7, `Dusk`, -133 };
			{ 7.0, `Day` };
			{ 17.6, `Dusk` };
			{ 19.6, `Night` };
		};
		BlueMoon = `NightBlue`;   -- shown instead of Night on a blue-moon night (workspace NHMoonEventTonight = "Blue")
		-- workspace attribute NHSky = "Storm" (a set name) overrides the schedule, for weather or an admin;
		-- the LocalPlayer attribute NHSkyPreview does the same on one client, for testing.
		Sets = {
			-- group 15981569 uploads, 2026-11-13 (NHSky<Set>_<Face>)
			Day = { Bk = 103651333736497; Dn = 77333463665975; Ft = 119988626923704; Lf = 82325193338630; Rt = 98736878816049; Up = 96123202776655 };
			Dusk = { Bk = 130059050523371; Dn = 109620867877755; Ft = 134244672227710; Lf = 92637844935076; Rt = 123188875952160; Up = 104447967963998 };
			Night = { Bk = 125002822187171; Dn = 84581077978179; Ft = 111974113063539; Lf = 129398379328271; Rt = 103371164387111; Up = 71407617919019 };
			NightBlue = { Bk = 79114995657347; Dn = 125521770406965; Ft = 137444634128484; Lf = 139377898630563; Rt = 114576978634954; Up = 83837514923669 };
			Storm = { Bk = 140004647918133; Dn = 75870366649344; Ft = 138974617955349; Lf = 81795809687373; Rt = 128479768841317; Up = 127658888445040 };
		};
	};
}
