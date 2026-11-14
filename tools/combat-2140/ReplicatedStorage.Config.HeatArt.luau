--[[
	HeatArt: the Heat meter's art (combat concept 18, 2.14.0), group 15981569 uploads from art/group-upload-fistgear.
	Controllers.Gui.HeatMeter draws the brazier from these; StateController Misc "Heat EX" uses Flare and Spark.
	While an id is empty the meter draws a plain stand-in (an ember disc), so it works before the upload.
	FillTop / FillBottom: where the coals sit in NHHeat_Fill.png, as fractions of its height (the fill rises between them).
]]
return {
	Frame = `rbxassetid://84687251212158`;   -- NHHeat_Frame.png
	Fill = `rbxassetid://123881595407515`;    -- NHHeat_Fill.png
	Glow = `rbxassetid://99798134898903`;    -- NHHeat_Glow.png
	Spark = `rbxassetid://127994272741499`;   -- NHHeat_Spark.png
	Flare = `rbxassetid://100020594492485`;   -- NHHeat_Flare.png
	FillTop = 0.133;   -- the flame tip, y 34 of 256
	FillBottom = 0.617; -- the coals' bottom, y 158 of 256
}
