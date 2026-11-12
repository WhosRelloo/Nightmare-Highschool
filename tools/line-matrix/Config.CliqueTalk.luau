--[[
	CliqueTalk (Config). ReplicatedStorage.Config.CliqueTalk  (the line matrix)

	What students say, by clique, moment and attitude. One child module per clique (named exactly like the clique in
	Config.Cliques.Order) plus Generic, each returning { [Moment] = { [Attitude | "Any"] = { lines } } }.
	Race and Outfit nest one more level: Race[RaceName][Attitude], Outfit[Verdict][Attitude].
	Read by Services.AI.StudentBrain.Talk (see docs/Line-Matrix.md). No gore, no slurs, no innuendo; 60 characters max.
]]

local CliqueTalk = {}
for _, Child in script:GetChildren() do
	if Child:IsA(`ModuleScript`) then
		local Ok, Mod = pcall(require, Child)
		if Ok and typeof(Mod) == `table` then
			CliqueTalk[Child.Name] = Mod
		else
			warn(`[CliqueTalk] {Child.Name} did not load: {Mod}`)
		end
	end
end
return CliqueTalk
