--[[
	Lines (server). Services.Features.MapStudents.Lines  (NH core add-on for the Map place, 2026-11-10)

	Everything the Map's background students say. Owner: "Give the NPC's a lot more voicelines, more variety, etc. I
	want them to feel as alive as possible."

	Pools are plain lists. A few have personality variants (Brave / Timid, Social / Shy). Lines.Pick (below) never
	repeats a student's recent lines and avoids a line someone else said in the last 40 s.
	Chats are short exchanges between two students standing together: "A" and "B" take turns (B is the partner).
	{Day} becomes the day's name, {Period} the current part of the day, {Moon} the moon phase.
	No gore: the owner's Roblox account was warned once over blood, so a downed student is "out cold", never worse.
]]

local Lines = {}

---| reactions |---

Lines.Flee = {
	Brave = { `Whoa, whoa!`, `Not near me!`, `Take it outside!`, `Okay, I'm out.`, `Seriously? Here?`, `Somebody's getting expelled.`,
		`I'm not getting hit for you.`, `Back it up!`, `Not today.` };
	Timid = { `Whoa!`, `Not again...`, `Nope. Nope.`, `Someone get a teacher!`, `I didn't see anything!`, `Run!`, `Oh no, oh no...`,
		`Mom said this school was safe.`, `Why is it always near me?` };
}
Lines.FleeNight = { `Not after dark...`, `This is why you don't stay out late.`, `The Vigil's never around when you need them.`, `It's too dark for this.` }
Lines.Monster = {
	Brave = { `Put that away. Your face, I mean.`, `Cool. Very scary. Stay over there.`, `I've seen worse in the cafeteria.`, `Okay, that's new.` };
	Timid = { `What IS that?`, `Stay back...`, `Oh no.`, `Is that... a student?`, `Please don't eat me.`, `I'm calling the Vigil.`, `That's not normal. That's NOT normal.` };
}
Lines.MonsterFullMoon = { `It's the full moon... of course it is.`, `Full moon. Should've stayed home.`, `Don't look it in the eyes.` }
Lines.Body = { `Is he okay?!`, `Someone's out cold over there.`, `Should we get the nurse?`, `Don't touch them.`, `Not my business. Not my business.`, `They're breathing... right?` }
Lines.Gawk = {
	Brave = { `Ooh, here we go.`, `Five yen on the tall one.`, `Somebody's losing a tooth.`, `Oh, that's gonna leave a mark.`, `Hit him back!`,
		`Best thing all week.`, `Someone record this.`, `Is this the Ring now?` };
	Timid = { `Oh no, a fight...`, `Should we stop them?`, `I'm not watching. I'm totally not watching.`, `Someone's going to get detention.`,
		`Why do they always fight here?`, `I hope the hall monitor's coming.` };
}
Lines.Relief = { `...Is it over?`, `Okay. Breathe.`, `That was way too close.`, `I need a minute.`, `Did that just happen?`, `Every single week.`, `I'm fine. I'm fine.`, `Note to self: walk the long way.` }
Lines.MakeWay = { `Watch it!`, `Whoa, sorry.`, `Excuse you.`, `Easy!`, `Someone's in a hurry.`, `Look where you're going!`, `Hallway's big enough for two.`, `Rude.` }
Lines.Sprint = { `No running in the halls!`, `Slow down!`, `Where's the fire?`, `Late for something?`, `Show-off.` }
Lines.Space = {
	Social = { `Uh... hi?`, `Personal space?`, `Can I help you?`, `You're kind of close.`, `Little room, please.`, `We're not that close yet.`, `Do I owe you money?` };
	Shy = { `...`, `Um.`, `S-sorry.`, `I'll just... move.` };
}
Lines.Shy = { `...`, `I should go.`, `Um. Bye.`, `I'm not here.`, `Please stop looking at me.` }
Lines.Followed = { `Are you following me?`, `...okay.`, `Can I help you?`, `Stop following me.`, `I'm walking faster now.` }
Lines.FollowedAgain = { `Seriously, stop following me.`, `I'll tell a teacher.`, `This is getting weird.`, `Go away!`, `I know you're there.` }
Lines.Stared = { `Something on my face?`, `What?`, `Take a picture, it lasts longer.`, `You're staring.`, `...Hello?`, `Do I know you?` }
Lines.Heard = {
	Door = { `Did you hear that?`, `Who's there?`, `Just a door. Just a door.`, `That door creaks every time.` };
	DoorNight = { `Who's in there this late?`, `Did that door just open by itself?`, `Nope. Not checking.`, `It's probably the wind.` };
	Fight = { `What was that?`, `Sounds like a fight.`, `Someone's getting jumped.`, `Not again...` };
}

---| greetings |---

Lines.Greet = {
	Morning = { `Morning.`, `Hey. Too early, right?`, `Morning. Did you finish the homework?`, `Morning. Coffee first, talk later.`, `Up early, huh?`, `Morning! You're keen.` };
	Day = { `Hey.`, `Hi.`, `Sup.`, `Hey there.`, `Oh, hi.`, `How's it going?`, `You new here?`, `Nice day for it.` };
	Evening = { `Evening.`, `Still here?`, `Hey. Long day, huh?`, `Heading home soon?`, `Evening. Don't stay out too late.` };
	Night = { `What are you doing out this late?`, `You shouldn't be out here at night.`, `Night. Stay in the light.`, `Hey... careful out here.`, `Late night, huh?` };
	FullMoon = { `Full moon tonight. Be careful.`, `You feel that? Full moon.`, `Don't go near the oaks tonight.`, `Full moon. Watch the wolves.` };
	NewMoon = { `No moon tonight. Darkest night of the month.`, `New moon. Can't see a thing.` };
	Again = { `Hey, you again.`, `Back already?`, `Oh, it's you.`, `We keep running into each other.`, `Hi again!`, `Hey! Good to see you.` };
	Often = { `You're always around, huh?`, `Are we friends now?`, `My favourite stranger.`, `Okay, at this point we're basically friends.` };
	Wary = { `You're the one who started that fight...`, `Keep your distance.`, `I saw what you did.`, `Stay away from me.`, `Not you again.` };
	Race = {
		Vampire = { `Is it just me, or is it colder near you?`, `Nice fangs. Real?`, `You're very pale. You eating okay?` };
		Werewolf = { `Nice ears.`, `Is that a tail?`, `You smell like the woods.` };
		Ghoul = { `You look... tired.`, `Did you sleep at all?`, `You're kind of grey today.` };
		Wraith = { `I didn't hear you come up.`, `You walk really quietly.`, `Were you always here?` };
		Priest = { `Bless you. Or whatever you say.`, `Oh good, someone holy.`, `Keep that cross handy.` };
	};
}

---| muttering alone |---

Lines.Mutter = {
	BeforeSchool = { `First bell soon...`, `Did I bring my notes?`, `Five more minutes of sleep. That's all I wanted.`, `Why is it so cold?`,
		`I swear the gate groans louder every morning.`, `Homework... homework... where's my homework?`, "{Day} again." };
	Class = { `I'm late. I'm so late.`, `If I sneak in at the back, maybe...`, "Is it {Period} already?", `I really don't want to go in there.`,
		`They won't miss me for five minutes.`, `I forgot my textbook.` };
	Passing = { `Which room was it again?`, `So many stairs.`, `Ugh, this hallway goes on forever.`, `Who keeps moving the classrooms?`, `Left, then right... or right?` };
	Break = { `Finally, a break.`, `I'm starving.`, `Is the concession stand open?`, `Ten minutes isn't a break.`, `Where is everyone?` };
	Lunch = { `What's for lunch?`, `I bet it's mystery meat again.`, `I'm so hungry I could eat a textbook.`, `Who took my seat?` };
	AfterSchool = { `Free at last.`, `Practice or home... practice or home...`, `I should study. I won't.`, `Is the Ring open tonight?`, `Coach is going to kill me.` };
	Evening = { `Getting dark already.`, `I should head home.`, `The oaks look creepier at dusk.`, `Mom's going to ask where I've been.` };
	Night = { `I shouldn't be out here.`, `Was that a howl?`, `The lights here are useless.`, `Something's watching me. I can feel it.`, `Keep walking. Don't look back.` };
	FullMoon = { `Full moon... stay inside.`, `I can hear them out past the gate.`, `Why does the moon look red?`, `Count the windows. Keep calm.` };
	Monday = { `Mondays should be illegal.`, `Whole week ahead. Great.` };
	Friday = { `Friday. Finally.`, `Weekend's so close I can taste it.` };
	Weekend = { `Why am I at school on a weekend?`, `Nobody's here. It's kind of nice.` };
}

Lines.Phone = { `Ugh, no signal.`, `Who texts at this hour?`, `Night FM's playing that song again.`, `Five missed calls from Mom.`,
	`The Gazette posted again.`, `Battery's dying.`, `Hah. Nice.`, `Seriously?`, `Group chat's on fire.`, `Who even is this number?` }
Lines.Yawn = { `*yawns*`, `*yaaawn*`, `So tired...`, `Need. Sleep.`, `Five more minutes...` }

---| little conversations |---
-- When: parts of the day it fits (any if missing). Night = true: only after dark. Moon = "Full": only at a full moon.

Lines.Chats = {
	-- school life
	{ `A: Did you do the Chemistry homework?`, `B: There was Chemistry homework?`, `A: ...We're doomed.` },
	{ `A: I think the Maths teacher hates me.`, `B: He hates everyone.`, `A: He hates me more.` },
	{ `A: Room 102 is freezing today.`, `B: Room 102 is always freezing.`, `A: I swear the radiators are fake.` },
	{ `A: Did you see the timetable change?`, `B: Again? They do it every week.` },
	{ `A: I fell asleep in History again.`, `B: Did anyone notice?`, `A: The teacher took a photo.` },
	{ "A: Test on {Day}.", `B: Which test?`, `A: All of them, apparently.` },
	{ `A: I got detention.`, `B: For what?`, `A: Breathing too loud, I think.` },
	{ `A: Is the library open?`, `B: Only if you want the librarian to stare at you.` },
	{ `A: My locker's jammed again.`, `B: Kick it. Bottom left. Works every time.` },
	{ `A: Report cards come out soon.`, `B: Don't remind me.` },
	{ `A: The headmaster walked past me today.`, `B: Did he say anything?`, `A: He just... looked. For a long time.` },
	-- food
	{ When = { `Lunch`, `Break` }; `A: What did you get?`, `B: Something brown.`, `A: Lucky.` },
	{ When = { `Lunch`, `Break` }; `A: The concession stand ran out of drinks.`, `B: Again?`, `A: Someone bought fifty.` },
	{ When = { `Lunch`, `Break` }; `A: Want half my sandwich?`, `B: What's in it?`, `A: ...I'd rather not say.` },
	-- people
	{ `A: Pip's been acting weird.`, `B: Pip's always weird.`, `A: Weirder.` },
	{ `A: Dex says he can get anything delivered.`, `B: Anything?`, `A: For a price.` },
	{ `A: Did you see Rhys at practice?`, `B: Captain of everything, that guy.` },
	{ `A: The choir sang in the chapel last night.`, `B: Nobody was in the chapel last night.`, `A: ...Exactly.` },
	{ `A: Wren drew something on my notebook.`, `B: Ink Club?`, `A: It moved when I wasn't looking.` },
	{ `A: Sable told my fortune.`, `B: What did she say?`, `A: She just said "soon". Just... "soon".` },
	{ `A: Coach Varga made us run laps in the rain.`, `B: Night Ravens train in anything.` },
	{ `A: The Vigil's recruiting again.`, `B: Hunting monsters for extra credit? Pass.` },
	{ `A: I saw someone from the Crimson Court.`, `B: In daylight?`, `A: Under a very big umbrella.` },
	{ `A: Bruno's running fights at the Ring tonight.`, `B: You going?`, `A: As a spectator. Obviously.` },
	-- rumours and the school
	{ `A: Did you hear about the student who vanished?`, `B: Which one?`, `A: That's the scary part.` },
	{ `A: The oaks moved again.`, `B: Trees don't move.`, `A: These ones do.` },
	{ `A: They say the east wing has a room that isn't on the map.`, `B: Every school says that.`, `A: Ours is true.` },
	{ `A: My phone keeps picking up Night FM on its own.`, `B: Turn it off.`, `A: It IS off.` },
	{ `A: Somebody keeps leaving notes in my locker.`, `B: Love letters?`, `A: They just say "behind you".` },
	{ `A: The clock tower was an hour slow yesterday.`, `B: Or we were an hour fast.` },
	{ `A: I heard there's a tunnel under the gym.`, `B: Who told you that?`, `A: The tunnel did. Kidding. ...Mostly.` },
	{ `A: The Gazette ran another story about the beasts.`, `B: Fake news.`, `A: Then why are they shutting the gate early?` },
	-- night and the moon
	{ Night = true; `A: We should go inside.`, `B: Five more minutes.`, `A: That's what the last kid said.` },
	{ Night = true; `A: Did you hear that?`, `B: Hear what?`, `A: ...Nothing. Never mind.` },
	{ Night = true; `A: Why do the lamps flicker out here?`, `B: Bad wiring.`, `A: Right. Wiring.` },
	{ Moon = `Full`; `A: Full moon tonight.`, `B: Don't. I've got a werewolf in my maths class.`, `A: Does he bite?`, `B: Only during tests.` },
	{ Moon = `Full`; `A: Stay away from the gate tonight.`, `B: Why?`, `A: Full moon. The beasts get bold.` },
	-- everyday
	{ `A: You going to the game?`, `B: Which one?`, `A: Ravens versus Rovers.`, `B: Rovers in three.` },
	{ `A: Nice board. Where'd you get it?`, `B: The school store. Took me a month of yen.` },
	{ `A: I've got so much homework.`, `B: Do it on the bus.`, `A: We don't have a bus.` },
	{ `A: What's the plan after school?`, `B: Sleep.`, `A: Solid plan.` },
	{ `A: Did you text me?`, `B: No.`, `A: Then who keeps texting me from your number?` },
	{ `A: I like your shoes.`, `B: Thanks, they're stolen.`, `A: ...What?`, `B: Kidding.` },
	{ `A: I can't wait to graduate.`, `B: Does anyone actually graduate here?`, `A: ...Good question.` },
	{ When = { `BeforeSchool` }; `A: You look tired.`, `B: I was up all night.`, `A: Studying?`, `B: Hiding.` },
	{ When = { `AfterSchool`, `Evening` }; `A: Finally done.`, `B: Until tomorrow.`, `A: Let me have this.` },
	{ When = { `AfterSchool`, `Evening` }; `A: Walk home together?`, `B: Yeah. Safer in twos.` },
}

---| picking |---

local RecentGlobal = {} :: { [string]: number }

-- fill in {Day}, {Period}, {Moon}
function Lines.Fill(Text: string, Ctx: { [string]: any }?): string
	local C = Ctx or {}
	return (Text:gsub("{(%w+)}", function(K)
		local V = C[K]
		return if V ~= nil then tostring(V) else "{" .. K .. "}"
	end))
end

-- a line from a pool the student hasn't said lately, and nobody's said in the last 40 s if there's a choice
function Lines.Pick(S, Pool: { string }, Ctx: { [string]: any }?): string?
	if not Pool or #Pool == 0 then return nil end
	S.Recent = S.Recent or {}
	local Now = os.clock()
	local Fresh, Okay = {}, {}
	for _, L in Pool do
		local Mine = table.find(S.Recent, L) ~= nil
		local Theirs = (RecentGlobal[L] or -1e9) > Now - 40
		if not Mine and not Theirs then table.insert(Fresh, L) end
		if not Mine then table.insert(Okay, L) end
	end
	local From = if #Fresh > 0 then Fresh elseif #Okay > 0 then Okay else Pool
	local L = From[math.random(1, #From)]
	table.insert(S.Recent, L)
	if #S.Recent > 12 then table.remove(S.Recent, 1) end
	RecentGlobal[L] = Now
	return Lines.Fill(L, Ctx)
end

-- a variant of a pool by personality: Brave / Timid, or Social / Shy
function Lines.ByNature(S, Pool: any, Kind: string): { string }
	if typeof(Pool) ~= `table` then return {} end
	if Kind == `Brave` then return if S.Bravery >= 0.5 then (Pool.Brave or Pool) else (Pool.Timid or Pool) end
	if Kind == `Social` then return if S.Social >= 0.45 then (Pool.Social or Pool) else (Pool.Shy or Pool) end
	return Pool
end

-- a chat that fits now (or nil)
function Lines.PickChat(S, Ctx: { [string]: any }): { string }?
	local Fits = {}
	for _, C in Lines.Chats do
		if typeof(C) == `table` then
			local Ok = true
			if C.When and not table.find(C.When, Ctx.Kind) then Ok = false end
			if C.Night and not Ctx.Night then Ok = false end
			if C.Moon and Ctx.Moon ~= C.Moon then Ok = false end
			if Ok then table.insert(Fits, C) end
		end
	end
	if #Fits == 0 then return nil end
	S.RecentChats = S.RecentChats or {}
	local Fresh = {}
	for _, C in Fits do if not table.find(S.RecentChats, C) and (RecentGlobal[C[1]] or -1e9) < os.clock() - 120 then table.insert(Fresh, C) end end
	local From = if #Fresh > 0 then Fresh else Fits
	local C = From[math.random(1, #From)]
	table.insert(S.RecentChats, C)
	if #S.RecentChats > 8 then table.remove(S.RecentChats, 1) end
	RecentGlobal[C[1]] = os.clock()
	return C
end

return Lines
