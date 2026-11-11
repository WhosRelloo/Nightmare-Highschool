--[[
	NpcVoice (shared config). ReplicatedStorage.Config.NpcVoice  (NH core add-on for the Map place, 1.78.3)

	The NPCs' voices: four sets of synthesized syllables (art/audio/npc-voice/make_npc_voice.py, a small formant
	speech synthesizer), uploaded to the Nightmare Highschool group. Controllers.World.NpcLook plays a set chosen by the
	NPC's NHVoiceSet attribute, picks each syllable from the letters of the line, and pitches it by the NPC's NHVoice.
	An empty id falls back to Roblox's built-in tick.

	  Boy        teenage boys (the Map's male students)
	  Girl       teenage girls (the Map's female students)
	  Enemy      delinquents, beasts' handlers, anyone hostile: lower, rougher
	  Authority  teachers, the hall monitor, staff: deep, steady, clear

	Pacing, so it never gets annoying: at most MaxSyllables per line (then the bubble stays silent), at most MaxVoices
	NPCs voicing at once near you (the nearest first), quiet, and gone past Range studs.
]]

local function set()
	return { A = ``; E = ``; I = ``; O = ``; U = ``; Uh = ``; Ma = ``; Ta = ``; Ka = ``; Hum = `` }
end

return {
	Sets = {
		Boy = set();
		Girl = set();
		Enemy = set();
		Authority = set();
	};
	Volume = 0.34;        -- each syllable (before the game's Effects volume)
	Range = 45;           -- studs: quieter with distance, silent past this
	MaxSyllables = 10;    -- per line
	MaxVoices = 2;        -- NPCs voicing at once near you
	Gap = 0.105;          -- seconds between syllables (Authority speaks a little slower)
}
