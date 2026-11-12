-- CliqueTalk.Vigil: hushed archivists by lamplight; records, the charter, missing pages, always watching (the line matrix)
return {
	Greet = {
		Hostile = { `Your file is getting thick.`, `Noted. Move along.`, `Don't touch anything on your way past.`, `The archive remembers what you did.`, "We wrote you down, {Name}. In ink." };
		Wary = { `Keep your hands where I can see them.`, `You're on a list. Not a good one yet.`, `We're still deciding about you.`, "{Name}. Signed the ledger, I hope?" };
		Neutral = { `Quiet, please. People are reading.`, `Seen any loose pages lying about?`, `Sign the ledger if you're staying.`, `Hello. Don't mind the lamp oil.` };
		Friendly = { "{Name}! Found anything odd lately?", `Ah, good. A reader. Come look at this.`, "Pull up a chair, {Name}. Bring a lamp.", `You're in the ledger. The good column.` };
		Respected = { "Keeper {Name}. The stacks are yours.", `There you are. We saved you the good lamp.`, `We found something. You'll want to see it.`, "{Name}. Close the door. We need to talk.", `Ezra's been asking for you, Keeper.` };
	};
	Bump = { Any = { `Careful! These are originals.`, `Mind the papers!`, `Watch it. I lost my place.`, `Oof. Pardon. I was reading.` } };
	Crowded = {
		Hostile = { `Reading over my shoulder? Back off.`, `Step back. This page isn't for you.`, `Too close. I'm writing that down.` };
		Respected = { `Lean in. You should see this page.`, `Closer is fine. Keep your voice down.`, `Here, hold the lamp for me.` };
		Any = { `You're in my light.`, `A little room? I'm cross-referencing.`, `You're standing on my notes.`, `Mind the candle, please.` };
	};
	Shoved = {
		Hostile = { `Assault. Dated, signed, filed.`, `That's going in your file.`, `Shove me again. The ink's still wet.` };
		Any = { `My notes! You scattered my notes!`, `Hey! Those were in order.`, `Was that necessary?`, `I'll remember that. I remember everything.` };
	};
	FightSeen = {
		Hostile = { `Go on. Give me something to write.`, `Every swing goes in the record.`, `There it is. Exactly as filed.` };
		Wary = { `Witnessed. Dated. Filed.`, `I'm noting who threw first.`, `This is why we keep records.` };
		Any = { `Somebody note the time.`, `Not near the archive! Not near the archive!`, `Who started it? I need it for the record.`, `I've got a pencil. Make it legible.` };
		Friendly = { "Go on, {Name}! I'll write it up kindly.", `I'll say you were provoked. Officially.`, `Good form! Very, um, scholarly.` };
		Respected = { `The lamps are with you, Keeper.`, "{Name}'s holding the line! Hold it!", `Keep them off the records, Keeper!` };
	};
	Flee = { Any = { `Save the ledgers! Grab the ledgers!`, `Not near the archive. Run!`, `Lamps out, go, go!`, `I'll finish my notes from a distance.` } };
	Transformed = {
		Hostile = { `So that's what you are. Noted.`, `I knew it. It's in the records.`, `Stay back. I have a lamp and a pen.` };
		Wary = { `Hold still. I'm writing this down.`, `Don't come closer. Just... pose.`, `Eyes, teeth, claws... noted.` };
		Any = { `Is that in the bestiary? It should be.`, `Fascinating. Terrifying. Mostly fascinating.`, `There's a sketch of that in the 1893 files.`, `Nobody believes the records. Look!` };
		Respected = { `Keeper? Is that you? Hold still. I'm sketching.`, "{Name}, that's the creature from the charter!", `Even like that, the lamps know you.` };
	};
	Night = {
		Hostile = { `Out after dark? That's noted.`, `The lamps see you. So do we.`, `The night shift has your file too.` };
		Wary = { `Late. What brings you to the stacks?`, `Night visitors get logged. Sign here.`, `Stay where the lamp can find you.` };
		Any = { `Keep a lamp near you. Always.`, `The records read differently at night.`, `Trim your wick. It's a long one.`, `Quiet. The building listens at night.` };
		Friendly = { "Night study, {Name}? Grab a lamp.", `Kettle's on. The real work starts now.`, `Stay. The best pages turn up after dark.` };
		Respected = { `Keeper. The night shift waited for you.`, "{Name}! We lit an extra lamp for you.", `We opened the locked drawer. Come see.` };
	};
	FullMoon = {
		Hostile = { `Full moon. Your record's about to grow.`, `Full moon. Try not to make the papers.`, `Moonlight won't hide you from us.` };
		Any = { `Full moon. Check the 1893 entries.`, `Every gap in the records? Full moon.`, `Moon's full. Lock the archive.`, `Full moon. I'm counting heads tonight.` };
		Friendly = { "Full moon, {Name}. Stay inside with us.", `Bring a lamp. Moonlight lies.`, `We're logging every howl. Join us?` };
		Respected = { `Keeper. We stand watch with you tonight.`, `The charter says hold the line tonight.`, `Full moon. The lamps are yours to light.` };
	};
	Race = {
		Human = {
			Hostile = { `Human, and still trouble. Noted.`, `Being ordinary won't keep you off the list.`, `Human. The only clean line in your file.` };
			Any = { `Human. Rarer here than the records say.`, `No marks on you. I'll write that down.`, `Human? Keep a lamp lit. Trust me.` };
		};
		Priest = {
			Hostile = { `Holy, and still on our list.`, `Pray all you like. The file stays open.`, `Blessed? The records disagree.` };
			Any = { `A priest. The charter mentions your kind.`, `Read old Latin? We've a page for you.`, `Priest-born. Your family's in our books.` };
		};
		Vampire = {
			Hostile = { "Vampire. Run along to {Rival}.", `Vampire. Your kind tore out page forty.`, `We have files on your whole family.` };
			Any = { `Vampire. You'd remember 1893, wouldn't you?`, `Cold hands. Don't touch the vellum.`, `Vampire. Which of the old families?` };
		};
		Werewolf = {
			Hostile = { `Werewolf. Your moon dates are on file.`, `Shed on these papers and you're done.`, `We know which nights you go missing.` };
			Any = { `Werewolf. The lunar tables are for you.`, `Werewolf. Mind the paper, it tears.`, `Half the gaps in our records are your kind.` };
		};
		Ghoul = {
			Hostile = { `Ghoul. Don't chew the parchment.`, `Ghoul. Keep out of the old registers.`, `I checked. You're not on any roll call.` };
			Any = { `Ghoul. Are you in the burial ledgers?`, `You smell like old paper. I mean it kindly.`, `You'd make a fine archivist. Very still.` };
		};
		Wraith = {
			Hostile = { `Wraith. Stop drifting through the files.`, `We know you're the one moving the pages.`, `Even ghosts get a file here.` };
			Any = { `Wraith. Were you a student here once?`, `Your name might be in the old rolls.`, `Did you walk through the stacks again?` };
		};
	};
	Hurt = {
		Hostile = { `Hurt? Should've stayed out of trouble.`, `Injured. I'll add it to the file.`, `Limping? That's in the record now.` };
		Wary = { `You look rough. Who did it? For the record.`, `Hurt? Not my business. Still. The nurse.`, `Sit. Don't touch anything, but sit.` };
		Any = { `You look awful. The nurse is past the archive.`, `Lean on the shelf. Carefully.`, `Who did this? I'll want it on paper.` };
		Friendly = { "{Name}! Sit. I'll fetch the nurse.", `Easy. Lean on me, not the shelf.`, "Who did this, {Name}? I want names." };
		Respected = { `Keeper! Someone get the kit!`, "Names, {Name}. Give me names.", `Rest in the reading room. We'll keep watch.` };
	};
	Outfit = {
		FullLook = {
			Hostile = { `Our colours don't make you one of us.`, `A Vigil vest won't close your file.`, `Dressed as us? We'll watch you closer.` };
			Wary = { `Dressed like us. Let's see if it sticks.`, `The vest fits. The rest we'll see.`, `Nice try. You still sign the ledger.` };
			Any = { "Dressed like {Clique}. Thinking of joining?", `Charcoal and khaki. Very archive.`, `You'd blend right into the stacks.` };
			Friendly = { "Look at you. Proper {Clique}.", `Now you look like a reader.`, `Ink-stain ready. Good.` };
			Respected = { `Keeper, in full colours. The lamps approve.`, "Spoken like {Clique}, and dressed like it.", `There's the look. The archive's own.` };
		};
		RivalLook = {
			Hostile = { "Crimson? Go back to {Rival}.", `Crimson. You've picked your side, then.`, `Crimson in the stacks. Bold, for a spy.`, `Out. The Parlor's that way.` };
			Wary = { "Dressed for {Rival}? We'll note that.", `Crimson. Whose side are you on?`, `That vest came from the Parlor.` };
			Any = { `Crimson? Careful who sees you in that.`, "Off to {Rival} later?", `That's Parlor crimson. We notice.` };
			Friendly = { `You, in crimson? Undercover, I hope.`, `Crimson? Tell me you're spying for us.`, `Did they make you wear that? Blink twice.` };
			Respected = { `Keeper, in crimson? Clever disguise.`, `Inside the Parlor? Bring us their ledgers.`, `Crimson suits a spy. Report later.` };
		};
		Likes = {
			Hostile = { "Nice {Piece}. Pity about the rest of you.", "Even you can't ruin a good {Piece}.", "Where'd you get that {Piece}? It's noted." };
			Any = { "The {Piece}. Now that's practical.", "Is that a real {Piece}? Let me look.", `A proper reader's kit. Good.`, "With that {Piece}, the stacks would have you." };
		};
		Mocks = {
			Friendly = { "Lose the {Piece}. You're better than that.", "The {Piece}? Did they get to you?", `All that frill. You're one of us, remember.` };
			Any = { "The {Piece}? In the stacks?", "That {Piece} came from the Parlor.", `Frills don't help you read.`, "Keep that {Piece} away from the lamps." };
		};
	};
	DressCode = {
		Hostile = { `The Archive is for the Vigil. Dress like it.`, `Not dressed like that. Not ever.`, `No colours, no entry. Especially you.` };
		Wary = { `Vest and charcoal, or you wait outside.`, `The Archive has rules. Read them.`, `Come back dressed for the stacks.` };
		Any = { `Archive's members only. Dress the part.`, `No vest, no stacks. Sorry.`, `Readers only. Charcoal and a vest.` };
		Friendly = { `Almost. Wear the vest and come in.`, "Put the vest on, {Name}, then come in.", `I'd let you in. The charter won't.` };
		Respected = { `Keeper or not, the charter wants a vest.`, `Rules are rules. Even for you. Vest.`, `The charter's strict. Dress, then come in.` };
	};
}
