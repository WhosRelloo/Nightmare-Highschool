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
		Hostile = { `Reading over my shoulder? Back off.`, `Step back. This page isn't for you.`, `Too close. You're in my margins.` };
		Respected = { `Lean in. You should see this page.`, `Closer is fine. Keep your voice down.`, `Here, hold the lamp for me.` };
		Any = { `You're in my light.`, `A little room? I'm cross-referencing.`, `You're standing on my notes.`, `Mind the candle, please.` };
	};
	Shoved = {
		Hostile = { `You'll find that in your permanent record.`, `That's going in your file.`, `Shove me again. The ink's still wet.` };
		Any = { `My notes! You scattered my notes!`, `Hey! Those were in order.`, `Was that necessary?`, `I'll remember that. I remember everything.` };
	};
	FightSeen = {
		Hostile = { `Go on. Give me something to write.`, `Every swing goes in the record.`, `Go on. Prove your file right.` };
		Wary = { `Witnessed. Dated. Filed.`, `I'm noting who threw first.`, `This is why we keep records.` };
		Any = { `Somebody note the time.`, `Mind the shelves! Mind the shelves!`, `Who started it? I need it for the record.`, `I've got a pencil. Make it legible.` };
		Friendly = { "Go on, {Name}! I'll write it up kindly.", `I'll say you were provoked. Officially.`, `Good form! Very, um, scholarly.` };
		Respected = { `The lamps are with you, Keeper.`, "{Name}'s holding the line! Hold it!", `Keep them off the records, Keeper!` };
	};
	Flee = { Any = { `Save the ledgers! Grab the ledgers!`, `Grab the charter and run!`, `Lamps out, go, go!`, `I'll finish my notes from a distance.` } };
	Transformed = {
		Hostile = { `So that's what you are. I knew it.`, `The 1893 sketches were right about you.`, `Stay back. I have a lamp and a pen.` };
		Wary = { `Hold still. I'm writing this down.`, `Don't come closer. Just... pose.`, `Eyes, teeth, claws... got it.` };
		Any = { `Is that in the bestiary? It should be.`, `Fascinating. Terrifying. Mostly fascinating.`, `There's a sketch of that in the 1893 files.`, `Nobody believes the records. Look!` };
		Respected = { `Keeper? Is that you? Hold still. I'm sketching.`, "{Name}, that's the creature from the charter!", `Even like that, the lamps know you.` };
	};
	Night = {
		Hostile = { `Out after dark? Of course you are.`, `The lamps see you. So do we.`, `The night shift has your file too.` };
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
			Hostile = { `Human, and still trouble.`, `Being ordinary won't keep you off the list.`, `Human. The only clean line in your file.` };
			Wary = { `Human. Then why are you down here?`, `Humans don't usually come to the stacks.`, `Human, are you? We'll check the rolls.` };
			Any = { `Human. Rarer here than the records say.`, `No marks on you. Interesting.`, `Human? Keep a lamp lit. Trust me.` };
			Friendly = { `Human and curious. Our favourite kind.`, `Humans make the best archivists. Steady.`, `A human who reads. Rare. Welcome.` };
			Respected = { `Human, and a Keeper. The charter allows it.`, `No fangs, no fur, all nerve. Keeper.`, "{Name}. Proof a human can hold the line." };
		};
		Priest = {
			Hostile = { `Holy, and still on our list.`, `Pray all you like. The file stays open.`, `Blessed? The records disagree.` };
			Wary = { `A priest in the stacks. Why?`, `Priest. Don't bless the ledgers.`, `Your order kept its own records once.` };
			Any = { `A priest. The charter mentions your order.`, `Read old Latin? We've a page for you.`, `Priest-born. Your family's in our books.` };
			Friendly = { `A priest! Help me read this old Latin?`, `Bless the lamps? They could use it.`, "{Name}, your order's crest is in 1893." };
			Respected = { `Keeper and priest. The archive is safe.`, `Bless the charter for us, Keeper?`, `A holy Keeper. The founders would approve.` };
		};
		Vampire = {
			Hostile = { "Vampire. {Rival} wants you back.", `Vampire. Your kind tore out page forty.`, `We have files on your whole family.` };
			Wary = { `Vampire. Cold hands off the vellum.`, `Vampire. Which side of 1893 were you on?`, `We know where the old families stood.` };
			Any = { `Vampire. You'd remember 1893, wouldn't you?`, `Vampire. Which of the old families?`, `You must have seen this place built.` };
			Friendly = { `Vampire? Tell me what 1893 was really like.`, "{Name}, your family's page is a good one.", `Not every vampire sides with the Parlor.` };
			Respected = { `A vampire Keeper. The Parlor must hate it.`, `Keeper. Your memory beats our ledgers.`, `Keeper. You remember what the pages forgot.` };
		};
		Werewolf = {
			Hostile = { `Werewolf. Your moon dates are on file.`, `We know which nights you go missing.`, `Half the gaps in our records are your kind.` };
			Wary = { `Werewolf. Shed on these papers and you're done.`, `Werewolf. Mind the paper, it tears.`, `We keep the lunar tables. We see you.` };
			Any = { `Werewolf. The lunar tables are for you.`, `Werewolf. We chart the moon here too.`, `Werewolf. Bet you'd sniff out a lost page.` };
			Friendly = { `Werewolf! Want to read the moon tables?`, "{Name}, good nose. Smell any old paper?", `We'll mark your full moons. Kindly.` };
			Respected = { `Keeper. We'll keep the lamps lit at moonrise.`, `A wolf on watch. The archive sleeps easy.`, "{Name}. The charter has a page for wolves." };
		};
		Ghoul = {
			Hostile = { `Ghoul. Don't chew the parchment.`, `Ghoul. Keep out of the old registers.`, `I checked. You're not on any roll call.` };
			Wary = { `Ghoul. Gloves on near the vellum.`, `You smell like the old crypt files.`, `Ghoul. Are you in the burial ledgers?` };
			Any = { `You'd make a fine archivist. Very still.`, `Ghoul. The burial rolls are well kept.`, `Ghoul. You keep late hours, like us.` };
			Friendly = { "{Name}, you'd love the burial rolls.", `Ghoul? Patient with old paper, I bet.`, `A ghoul reader. You'll outlast the dust.` };
			Respected = { `Keeper. Nobody guards the crypt files better.`, `A ghoul Keeper. Patient as the ledgers.`, `The crypt records are yours, Keeper.` };
		};
		Wraith = {
			Hostile = { `Wraith. Stop drifting through the files.`, `We know you're the one moving the pages.`, `Even ghosts get a file here.` };
			Wary = { `Wraith. Did you walk through the stacks again?`, `Don't drift where I can't see you.`, `Wraith. Things go missing when you're near.` };
			Any = { `Wraith. Were you a student here once?`, `Your name might be in the old rolls.`, `Wraith. Quiet as the stacks. Fitting.` };
			Friendly = { "{Name}, help me find your old class photo?", `A wraith who reads. You're welcome here.`, `Wraith? You'd know where the lost pages went.` };
			Respected = { `Keeper. You've walked these halls longest.`, `A wraith Keeper. The stacks feel you.`, "{Name}. Tell us what the records got wrong." };
		};
	};
	Hurt = {
		Hostile = { `Hurt? Should've stayed out of trouble.`, `Injured. I'll add it to the file.`, `Limping. The archive isn't a hospital.` };
		Wary = { `You look rough. Who did it? For the record.`, `Hurt? Not my business. Still, see the nurse.`, `Sit. Don't touch anything, but sit.` };
		Any = { `You look awful. The nurse is past the archive.`, `Lean on the shelf. Carefully.`, `Who did this? I'll want it on paper.` };
		Friendly = { "{Name}! Sit. I'll fetch the nurse.", `Easy. Lean on me, not the shelf.`, "Who did this, {Name}? I want names." };
		Respected = { `Keeper! Someone get the kit!`, "Names, {Name}. Give me names.", `Rest in the reading room. We'll keep watch.` };
	};
	Outfit = {
		FullLook = {
			Hostile = { `Our colours don't make you one of us.`, `A Vigil vest won't close your file.`, `Dressed as us? We'll watch you closer.` };
			Wary = { `Dressed like us. Let's see if it sticks.`, `The vest fits. The rest we'll see.`, `Nice try. You still sign the ledger.` };
			Any = { "{Clique}'s colours. Thinking of joining?", `Charcoal and khaki. Very archive.`, `You'd blend right into the stacks.` };
			Friendly = { "Look at you. {Clique} would be proud.", `Now you look like a reader.`, `Ink-stain ready. Good.` };
			Respected = { `Keeper, in full colours. The lamps approve.`, "{Clique} looks good on you, Keeper.", `There's the look. The archive's own.` };
		};
		RivalLook = {
			Hostile = { "Crimson? {Rival} sent you, then.", `Crimson. You've picked your side, then.`, `Crimson in the stacks. Bold, for a spy.`, `Out. The Parlor's that way.` };
			Wary = { "{Rival}'s colours? We'll mark that.", `Crimson. Whose side are you on?`, `That vest came from the Parlor.` };
			Any = { `Crimson? Careful who sees you in that.`, "{Rival} later, is it? Careful.", `That's Parlor crimson. We notice.` };
			Friendly = { `You, in crimson? Undercover, I hope.`, `Crimson? Tell me you're spying for us.`, `Did they make you wear that? Blink twice.` };
			Respected = { `Keeper, in crimson? Clever disguise.`, `Inside the Parlor? Bring us their ledgers.`, `Crimson suits a spy. Report later.` };
		};
		Likes = {
			Hostile = { "Nice {Piece}. Pity about the rest of you.", "Even you can't ruin a good {Piece}.", "Where'd you get that {Piece}? Honestly." };
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
