-- CliqueTalk.Ordinary: the Commons' nervous regulars; heads down, home before dark, strength in numbers, moon rumours (the line matrix)
return {
	Greet = {
		Hostile = { `Please just go away.`, `Oh no. Not you. Not today.`, "{Name}. We don't want any trouble.", `Okay. Everyone stay calm. It's them.`, `We're not scared! ...Much. Leave.` };
		Wary = { `Uh. Hi. You're not starting anything?`, `Oh! Hi. Didn't see you there.`, "{Name}... hi. Just passing through?", `Hey. Um. We're just sitting here.` };
		Neutral = { `Hi! Long day, huh?`, `Hey. Do you know if it's going to rain?`, `Hi. Did you hear about last night?`, `Oh, hey. Sit anywhere. Not that chair.` };
		Friendly = { "{Name}! Want half my sandwich?", `Oh good, a friendly face!`, "Hey {Name}! Walk me to class?", `Hi! We saved you a seat. Sort of.` };
		Respected = { "{Name}! Everybody, it's {Name}!", `You stood up for us. Thanks.`, `Pip said you'd come! Sit, sit!`, "{Name}! We made you a card. It's bad.", `Our hero! Want the good pudding cup?` };
	};
	Bump = { Any = { `Oh! Sorry, sorry. My fault.`, `Eep! My books!`, `Sorry! I wasn't looking. Were you?`, `Oops. Was that you or me?`, `Whoa! Okay. Nobody panic.` } };
	Crowded = {
		Hostile = { `Could you... not stand so close?`, `Back up a bit? I'm already nervous.`, `Um. Too close. Way too close.` };
		Respected = { `Squish in! There's room on the bench.`, `Sit with us! Strength in numbers.`, `Closer! You're our lucky charm.` };
		Any = { `Oh. Hi. You're kind of in my bubble.`, `Little room? I get nervous.`, `Can you scoot? Just a little?`, `I need to breathe. Bit of room?` };
	};
	Shoved = {
		Hostile = { `Okay! Okay. I'm going. I'm going.`, `Why would you DO that?`, `Pip! Pip, they shoved me!` };
		Any = { `Ow! Hey! What did I do?`, `Hey! I'm telling the monitor!`, `Whoa! Rude. Really rude.`, `Ow. I was just standing here.` };
	};
	FightSeen = {
		Hostile = { `Oh good. Maybe they'll be busy for a while.`, `Please lose. Quietly. Far away.`, `This is exactly why we sit inside.` };
		Wary = { `Not near the lunch tables, please!`, `Somebody get a teacher! A real one!`, `Everybody back up. Slowly.` };
		Any = { `Oh no oh no oh no.`, `Somebody stop them! Not me, though.`, `I can't look. Tell me when it's over.`, `This is going in my diary.`, `Is this normal? This isn't normal.` };
		Friendly = { "Be careful, {Name}! Guard up!", `You've got this! I think! Do you?`, `Duck! Ducking is good!` };
		Respected = { "Go, {Name}! For the Commons!", `Everyone, cheer! Quietly! No, loudly!`, `You're doing it! You're actually doing it!` };
	};
	Flee = { Any = { `Run! Don't look back! Okay, I looked!`, `I KNEW I should've gone home early!`, `Everybody hold hands! No, run! RUN!`, `This is it! Tell my mom I said hi!`, `Not again! Why is it always again?!` } };
	Transformed = {
		Hostile = { `Nope. Nope. Absolutely not. Bye.`, `Please don't. Please don't. Please don't.`, `Stay back! We taste awful! Ask anyone!` };
		Wary = { `Okay. Nobody scream. I'm screaming.`, `Was that... always in there?`, `Back away slowly. Is slowly right?` };
		Any = { `The rumours were TRUE?!`, `I told you! I TOLD you about this place!`, `Is it bad if I faint? I'm fainting.`, `Okay. That's it. I'm transferring.`, `Mom said this school was normal!` };
		Respected = { "{Name}? Okay. Okay. Still our friend.", `You're still you in there? Blink twice?`, `Scary, sure, but OUR kind of scary.` };
	};
	Night = {
		Hostile = { `It's dark. Go home. Far, far away.`, `You, out here? Great. Even worse night.`, `Don't follow us. We're walking in a group.` };
		Wary = { `Why are you out after dark?`, `It's late. You heard the stories, right?`, `Are you... following us? Please say no.` };
		Any = { `It's getting dark. I should be home.`, `Walk in groups after dark. Always.`, `Did you hear that? Tell me you heard that.`, `Stay under the lamps. Mom's rule.` };
		Friendly = { "{Name}! Walk with our group tonight?", `It's dark! Let's go together. Safer.`, `Got a torch? I've got two. Here.` };
		Respected = { `You're walking with us? Really? Thank you!`, "With {Name} here, the dark's fine. Mostly.", `Okay, I feel braver now. Slightly.` };
	};
	FullMoon = {
		Hostile = { `Full moon AND you? Worst night ever.`, `Full moon. Go be somewhere else.`, `Moon's up. Keep away from us. Please.` };
		Any = { `Is it true about the full moon? Is it?`, `Full moon. Lock the doors. Twice.`, `My cousin says the oaks howl tonight.`, `Full moon. I'm sleeping in my shoes.`, `Don't look at it. Don't look at the moon.` };
		Friendly = { "Full moon, {Name}. Walk with our group?", `Stick together tonight. Promise?`, `Full moon. Be home before midnight, okay?` };
		Respected = { `Full moon, but you're here. We're okay.`, "{Name}, walk with us? Just to the lamps?", `Strength in numbers. And you. Mostly you.` };
	};
	Race = {
		Human = {
			Hostile = { `Human? Then you should know better.`, `Human, and still picking on us?`, `You're one of us. Act like it.` };
			Wary = { `Human? Okay. Prove it. Kidding! Kind of.`, `You're human? Really? Promise?`, `Human. Okay. Phew. I think.` };
			Any = { `Oh, another human. Hi!`, `Human? Same! Graduate alive, right?`, `Human. Want to join our study group?` };
			Friendly = { `A human! Sit with us, there's snacks.`, "{Name}, human and nice. Rare here!", `Humans stick together. Right?` };
			Respected = { `Human, and braver than all of them.`, "{Name}. Proof we can make it here.", `You're human like us. And look at you!` };
		};
		Priest = {
			Hostile = { `Priest. Please bless us from over there.`, `Priest. We don't need a sermon. Bye.`, `Holy or not, leave us alone.` };
			Wary = { `A priest? Is something... coming?`, `Priest. Is this place haunted? Be honest.`, `Priest. Should we be worried? We're worried.` };
			Any = { `A priest! Oh, that's reassuring.`, `Priest. Bless my locker? It's haunted.`, `Priest. Any tips for the full moon?` };
			Friendly = { `A priest! Bless the Commons, please!`, "{Name}, say a prayer for my test?", `Priest friend! Best kind of friend.` };
			Respected = { `Our priest! We sleep better now.`, "{Name}. You make the Commons feel safe.", `Bless us all? We'll take any help.` };
		};
		Vampire = {
			Hostile = { `Vampire. Please stay over there.`, `Vampire. We keep garlic in our lunch.`, `Vampire. Go away. We're all very loud.` };
			Wary = { `Vampire. You're not hungry, right?`, `Vampire. Um. Nice... teeth.`, `Vampire. I'll just... sit over here.` };
			Any = { `A vampire! Do you... sleep at all?`, `Vampire. Do mirrors really not work?`, `Vampire. Is it weird being up all day?` };
			Friendly = { `A nice vampire! Mom won't believe me.`, "{Name}, you're my favourite vampire.", `Vampire friend! Sit with us at lunch?` };
			Respected = { `Our vampire! Nothing bites us now.`, "{Name}. Fangs on our side. Amazing.", `With you here, the night's less scary.` };
		};
		Werewolf = {
			Hostile = { `Werewolf. Please don't. Just don't.`, `Werewolf. Go home before moonrise.`, `Werewolf. Stay on your side of the hall.` };
			Wary = { `Werewolf. Is it... soon? The moon?`, `Werewolf. Should I be standing here?`, `Werewolf. Nice ears. Please stay calm.` };
			Any = { `Werewolf! Is the moon thing true?`, `Werewolf. Does it hurt? The changing?`, `Werewolf. You must hear everything.` };
			Friendly = { `Werewolf friend! Warn us before moonrise?`, "{Name}, you're the nicest werewolf ever.", `Werewolf? You'd keep the others away.` };
			Respected = { `Our werewolf! Nothing scares us now.`, "{Name}. Fluffy hero of the Commons.", `With you, full moons feel almost okay.` };
		};
		Ghoul = {
			Hostile = { `Ghoul. Stay away from our lunch.`, `Ghoul. We're not snacks. Please go.`, `Ghoul. Stop staring at us. Please.` };
			Wary = { `Ghoul. You're... not hungry, right?`, `Ghoul. Don't follow us. We walk fast.`, `Ghoul. Um. Is that my sandwich?` };
			Any = { `A ghoul! What's your favourite class?`, `Ghoul. You're so calm. How?`, `Ghoul. Do you ever get scared?` };
			Friendly = { `Ghoul friend! Want my apple?`, "{Name}, nothing rattles you. Teach me.", `Ghoul? You're calmer than all of us.` };
			Respected = { `Our ghoul! Steadiest friend we have.`, "{Name}. Nothing scares you. Inspiring.", `Stand with us? We feel braver.` };
		};
		Wraith = {
			Hostile = { `Wraith. Please stop appearing like that.`, `Wraith. Go haunt someone else.`, `Wraith. I know you're there. Go away.` };
			Wary = { `Wraith! Don't DO that! My heart!`, `Wraith. How long were you standing there?`, `Wraith. Are you... in the wall right now?` };
			Any = { `A wraith! Can you go through doors?`, `Wraith. You're so quiet. How?`, `Wraith. Is it cold, floating around?` };
			Friendly = { `Wraith friend! Warn me before you appear?`, "{Name}, scout the dark hall for us?", `Wraith? Best friend for a haunted school.` };
			Respected = { `Our wraith! Watching over the Commons.`, "{Name}. Our guardian ghost. Really.", `You see everything. Thanks for looking out.` };
		};
	};
	Hurt = {
		Hostile = { `You're hurt? Okay. Um. Sit over there.`, `Oh no. Um. Nurse is that way. Bye.`, `Hurt? That's... bad. Please don't blame us.` };
		Wary = { `Are you okay? Don't fall on me.`, `You're hurt. Was it the Back Lot?`, `I have a bandage. I'll just... throw it.` };
		Any = { `Oh no, you're hurt! Sit down!`, `Nurse! Somebody get the nurse!`, `I have bandages. I always have bandages.` };
		Friendly = { "{Name}! Sit. I have bandages and juice.", `Who did this? I'll... tell someone!`, `Lean on me. Slowly. I've got you.` };
		Respected = { `Our hero's hurt! Everyone, help!`, "{Name}, sit. We'll bring the nurse here.", `Rest. Pip's getting ice. And cookies.` };
	};
	Outfit = {
		FullLook = {
			Hostile = { `Dressing like us won't make us trust you.`, `Our colours? You? Why?`, `Nice try. We still know who you are.` };
			Wary = { `Oh. You're dressed like us. Huh.`, `Neat and tidy. Are you... joining?`, `Our look? Is this a trick?` };
			Any = { "{Clique} would be so proud!", `Neat, pressed, sensible. Perfect.`, `You look like you'd get home by dark.` };
			Friendly = { `You look just like us! Yay!`, "{Name}! Matching! Picture time!", `Sensible shoes too? Perfect.` };
			Respected = { `Our look, but brave. I love it.`, "{Name}, in Commons colours! Best day.", `Now everyone knows you're with us.` };
		};
		RivalLook = {
			Hostile = { `Back Lot clothes. Just... leave.`, "{Rival} sent you? Tell them no thanks.", `Dressed like them. We knew it.` };
			Wary = { `Are you... with the Back Lot now?`, `That look makes me nervous.`, "{Rival} dressed you? Um. Why?" };
			Any = { `Oh. That's very... Back Lot.`, `That outfit scares me a little.`, `Is that a Back Lot thing? It's loud.` };
			Friendly = { "{Name}! No! Not the Back Lot look!", `Did they make you wear that? Oh no.`, `Please change. You're scaring Pip.` };
			Respected = { `Undercover on the Lot? So brave.`, `Even dressed like them, you're ours.`, `Spying for us? Careful out there!` };
		};
		Likes = {
			Hostile = { "The {Piece}? Okay. Still, please go.", "Nice {Piece}. Doesn't mean we trust you.", "The {Piece} is nice. You're still scary." };
			Any = { "Ooh, the {Piece}! So sensible.", "The {Piece}! I have that exact one!", "Love the {Piece}. Very practical.", "Where'd you get the {Piece}? I want one." };
		};
		Mocks = {
			Hostile = { "The {Piece}? Oh. Oh no.", "That {Piece} scares me. So do you.", "Please keep the {Piece} away from me." };
			Friendly = { "The {Piece}? Are you okay? Really?", "Maybe leave the {Piece} at home?", "You don't need the {Piece}. Promise." };
			Any = { "The {Piece}? That's... a lot.", "Is the {Piece} really necessary?", "Um. The {Piece}. Why?", "That {Piece} gives me the creeps." };
		};
	};
	DressCode = {
		Hostile = { `The Commons is for us. You know that.`, `Members only. Please don't make it weird.`, `Sorry, not you. Not in that.` };
		Wary = { `Commons clothes only past here.`, `Um, there's a dress code. Neat, please.`, `Tuck in and come back? Sorry.` };
		Any = { `Commons is for... well, us. Sorry.`, `Neat and tidy to sit here. Pip's rule.`, `Members only. It's a whole thing.` };
		Friendly = { `Almost! Tuck in and come sit!`, "{Name}, wear something neat and sit!", `I'd wave you in, but rules. Sorry!` };
		Respected = { `Even heroes tuck in. Pip insists.`, `Rules are rules. Change, then sit!`, `We'll save your seat. Change quick!` };
	};
	Fed = {
		Loved = { Any = { "{Snack}! You're so nice. Thank you!", `Oh wow, my favourite. Thanks!`, "{Snack}? You just made my day.", `Best thing that's happened all week.` } };
		Liked = { Any = { "{Snack}? Oh, thank you!", `That's really kind. Thanks.`, `You didn't have to! Thanks.` } };
		Refuse = { Hostile = { `Um, no. I don't trust you.`, `Please just leave me alone.` }; Wary = { `Oh, um, I'm okay, thanks.`, `My mum says no food from strangers.` } };
	};
}
