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
}
