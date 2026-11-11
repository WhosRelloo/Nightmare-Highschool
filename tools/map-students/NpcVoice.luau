--[[
	NpcVoice (shared config). ReplicatedStorage.Config.NpcVoice  (NH core add-on for the Map place, 1.78.3)

	The NPCs' voices: four sets of synthesized syllables (art/audio/npc-voice/make_npc_voice.py, a small formant
	speech synthesizer), uploaded to the Nightmare Highschool group. Controllers.World.NpcLook plays a set chosen by the
	NPC's NHVoiceSet attribute, picks each syllable from the letters of the line, and pitches it by the NPC's NHVoice.
	A missing id falls back to Roblox's built-in tick.

	  Boy        teenage boys (the Map's male students)
	  Girl       teenage girls (the Map's female students)
	  Enemy      delinquents, beasts' handlers, anyone hostile: lower, rougher
	  Authority  teachers, the hall monitor, staff: deep, steady, clear

	Pacing, so it never gets annoying: at most MaxSyllables per line (then the bubble stays silent), at most MaxVoices
	NPCs voicing at once near you (the nearest first), quiet, and gone past Range studs.
]]

-- ids of the uploaded syllables (group 15981569, named NHVoice_<Set>_<Syllable>)
return {
	Sets = {
		Boy = { A = 131237050054388; E = 87156408598215; I = 129096454031327; O = 108395011977391; U = 74143210374563; Uh = 132570907808433; Ma = 129282736773827; Ta = 98047340140837; Ka = 92277825825270; Hum = 134852160933803 };
		Girl = { A = 138979039040625; E = 121091546292616; I = 95405231909329; O = 130419765906549; U = 111169301964485; Uh = 79879312675855; Ma = 134093241527408; Ta = 122140835776857; Ka = 76151155915516; Hum = 72782138333941 };
		Enemy = { A = 134094803287659; E = 131175326649533; I = 110709477106133; O = 119565651952716; U = 96299871731410; Uh = 101751178788255; Ma = 90165448712894; Ta = 90731378544651; Ka = 100704094834774; Hum = 126225310010798 };
		Authority = { A = 133090988385590; E = 73550303135302; I = 70492928392856; O = 133290063699722; U = 130706352610429; Uh = 108645578518299; Ma = 109670224144005; Ta = 103940842004450; Ka = 132233328121342; Hum = 127094415133369 };
	};
	Volume = 0.34;        -- each syllable (before the game's Effects volume)
	Range = 45;           -- studs: quieter with distance, silent past this
	MaxSyllables = 10;    -- per line
	MaxVoices = 2;        -- NPCs voicing at once near you
	Gap = 0.105;          -- seconds between syllables (Authority speaks a little slower)
}
