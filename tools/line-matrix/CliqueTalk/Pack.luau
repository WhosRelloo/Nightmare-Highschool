-- CliqueTalk.Pack: the Den's wolf-hearted bruisers; the moon, scent, nerves and "first-year" (the line matrix)
return {
	Greet = {
		Hostile = { `Smell that? Nerves.`, `Wrong hallway, first-year.`, "{Name}. You always walk this jumpy?", `Moon's getting fat. Your luck's getting thin.`, `Heh. Somebody's sweating.` };
		Wary = { `I can smell you from here. What do you want?`, `Hm. New scent. Who do you run with?`, "{Name}. Hold on. I'm deciding about you.", `You're twitchy. Why so twitchy?` };
		Neutral = { `Hey. Moon's coming up fat this week.`, `Yo. You smell like toast.`, `'Sup. Mind the claw marks on the bench.`, `Hey. Smells like rain later.` };
		Friendly = { "{Name}! You smell like a friend.", `Hey, you. Coming out to the Den?`, "{Name}! Grab a log. Fire's going.", `There you are. Pack missed your scent.` };
		Respected = { `Run with us tonight.`, "{Name}. Pack. Always Pack.", `Make room. Alpha coming through.`, "{Name}! Dex saved you the warm spot.", `Den's yours. Just say the word.` };
	};
	Bump = { Any = { `Watch it, first-year.`, `I smelled you coming. Still walked into me?`, `Bump a wolf? Bold.`, `Easy! I almost growled.` } };
	Crowded = {
		Hostile = { `Back up. I don't like your scent.`, `Too close. My hackles are up.`, `One more step and I start growling.` };
		Respected = { `Get in close. Pack sticks together.`, `Shoulder to shoulder. Like a real pack.`, `Closer. This stays in the Den.` };
		Any = { `Room, please. I run warm.`, `Give me space. I'm itchy today.`, `Personal space. Wolves need it too.`, `You're crowding me. My ears hate that.` };
	};
	Shoved = {
		Hostile = { `Shove a wolf? Brave. Also dumb.`, `Do that again. I dare you.`, `Okay. Now my hackles are up.` };
		Respected = { `Ha! Rough-housing? I'm in.`, `Okay, okay. That's a real shove.`, `Heh. Good shove. Pack-strong.` };
		Any = { `Hey! Paws off!`, `Whoa! Who taught you to shove?`, `Rude. I'm the one who does the shoving.`, `Hey! I just brushed this flannel.` };
	};
	FightSeen = {
		Hostile = { `Go on. Somebody's losing. Loudly.`, `Sloppy. A first-year swings better.`, `Keep going. You're all bark.` };
		Wary = { `Not near the Den. Take it outside.`, `Easy. Nobody wake Dex.`, `Ears up. Teacher's coming.` };
		Any = { `Ring! Make a ring!`, `Ooh. Somebody just lost their nerve.`, `Awoo! Here we go!`, `Who's alpha here? Let's see.`, `Loud. I like loud.` };
		Friendly = { "Low and fast, {Name}! Like a wolf!", `Circle 'em! Don't stand still!`, `Growl first! Swing second!` };
		Respected = { "{Name}'s got the moon on their side!", `Pack! Howl for 'em!`, `Nobody cuts in. Alpha's working.` };
	};
	Flee = { Any = { `Back to the Den! Go!`, `Split up! Meet at the oaks!`, `Tails down, feet fast! Move!`, `Nope! Even wolves know when to run!`, `Into the trees! Don't look back!` } };
	Transformed = {
		Hostile = { `Spooky. Doesn't make you Pack.`, `New look? Cute. Still not Pack.`, `Changed? Still a first-year underneath.` };
		Wary = { `Easy... easy. Let's all stay calm.`, `Whoa. Okay. Is that still you in there?`, `Nobody stare. Nobody move.` };
		Any = { `Now THAT is a change.`, `Huh. So that's what you've been hiding.`, `Heh. That's a new look.`, `Those eyes. Okay. Respect.` };
		Respected = { "{Name}?! Okay. Terrifying. Love it.", `Ha! That's one of ours!`, `Even Dex looks nervous.`, `Stay like that a while. Please.` };
	};
	Night = {
		Hostile = { `Night's ours. You're just visiting.`, `Late, first-year. Every shadow's got ears.`, `Dark out. Hope you brought a lamp. Heh.` };
		Wary = { `Out late. What's your business?`, `Night air carries. I heard you coming.`, `Late. Keep to the lamps, stranger.` };
		Any = { `Night air. Smell the pines?`, `Finally. The good hours.`, `Hear that? Something's out past the oaks.`, `Night. My ears work better now.` };
		Friendly = { "{Name}! Fire's lit at the Den. Come sit.", `Pull up a log. Night's young.`, `Moon's coming. Wait with us.` };
		Respected = { `Night belongs to the Pack. And you.`, "{Name}, lead the run. We'll follow.", `Den fire's yours. Warmest spot.` };
	};
	FullMoon = {
		Hostile = { `Full moon. Your nerves are SO loud.`, `Full moon. Bad night to be you.`, `Moon's full. You feel it too, right? Heh.` };
		Any = { `Full moon. Feel that? Everything's louder.`, `AWOOOO! ...Sorry. Couldn't help it.`, `Big silver moon. Every hair's standing up.`, `Smell the moon? No? Shame.` };
		Friendly = { "Full moon, {Name}. Howl with us.", `Moon's up! Run the field with us!`, `Tonight you're honorary Pack. Howl!` };
		Respected = { `Full moon. Lead the howl, alpha.`, "{Name}, the moon's yours tonight.", `Whole Pack runs behind you tonight.`, `Silver moon, silver night. Pack's yours.` };
	};
	Race = {
		Human = {
			Hostile = { `Human. All nerves, no nose.`, `Human. Blunt teeth, blunt nose.`, `Human. Your nose is just for show, huh?` };
			Wary = { `Human. Don't stare at the moon too long.`, `Human. Don't wander off the path.`, `Human. Why are you this close to the Den?` };
			Any = { `Human. No fur, no fangs. Brave.`, `Human, huh? Smell anything useful?`, `Human. Sharp ears for a first-year.` };
			Friendly = { `Human, and you didn't flinch. Nice.`, "{Name}. Human nose, wolf heart.", `Humans can run with us. Just keep up.` };
			Respected = { `Human, and the Pack follows you. Ha.`, "{Name}. No fur needed. Still alpha.", `Human? You've got the heart of a wolf.` };
		};
		Priest = {
			Hostile = { `Priest. You smell like candle wax.`, `Priest. Save the blessing. We don't want it.`, `Priest. Chapel's the other way. Keep going.` };
			Wary = { `Priest. Keep the incense away from my nose.`, `Priest. Don't bless me. I'll sneeze.`, `Priest. You with the choir kids?` };
			Any = { `Priest, huh. Not all of you sing, right?`, `Priest. Your lot never comes to the Den.`, `Priest. You're calmer than you look.` };
			Friendly = { `A priest at the bonfire? I like you.`, "{Name}. Holy, and good company.", `Priest! Bless the bonfire for us?` };
			Respected = { `Our priest. Even the moon's polite now.`, "{Name}. Only priest the Pack trusts.", `A priest in the Den. Dex says it's fine.` };
		};
		Vampire = {
			Hostile = { `Vampire. Cold and quiet. Not our kind.`, `Vampire. The Den's no crypt. Out.`, `Vampire. Brood somewhere else.` };
			Wary = { `Vampire. You smell like a cold cellar.`, `Vampire. Wolves and bats don't mix.`, `Vampire. What are you doing near the Den?` };
			Any = { `Vampire. Night folk, like us.`, `Vampire. You hear the moon too?`, `Vampire. Bet you never sleep either.` };
			Friendly = { `Vampire! Night runner. Join us.`, "{Name}. Fangs and fur get along fine.", `Vampire? Best night company there is.` };
			Respected = { `Our vampire. The night's twice ours now.`, "{Name}. Fangs on the Pack's side. Good.", `Vampire and Pack. Nobody tests that.` };
		};
		Werewolf = {
			Hostile = { `Werewolf, and not Pack? Shameful.`, `Werewolf. Lone wolf, huh? Stay lone.`, `Werewolf. You smell like the wrong den.` };
			Wary = { `Werewolf. Which den are you from?`, `Werewolf. Lone wolves make me twitchy.`, `Werewolf. Show me you're one of us.` };
			Any = { `Werewolf! Kin. Come sit.`, `Werewolf. You smell like home.`, `Werewolf. Feel the moon tugging?` };
			Friendly = { `Kin! The Den's always open to you.`, "{Name}! Wolf to wolf. Welcome.", `Werewolf! Run with us at moonrise.` };
			Respected = { `Kin. The whole Pack bows its head.`, "{Name}. Truest wolf in the Den.", `Our wolf. Our kin. Our alpha.` };
		};
		Ghoul = {
			Hostile = { `Ghoul. You smell like wet gravestones.`, `Ghoul. Don't track grave dirt in here.`, `Ghoul. Den's for the living. Shoo.` };
			Wary = { `Ghoul. Your scent makes my nose itch.`, `Ghoul. Don't lurk by the fire.`, `Ghoul. Quiet type. I don't trust quiet.` };
			Any = { `Ghoul. You'd outlast a winter in the woods.`, `Ghoul. Nothing spooks you, huh?`, `Ghoul. Steady nerves. Rare round here.` };
			Friendly = { `Ghoul! Sit by the fire. Warm up.`, "{Name}. Steady as an old oak.", `Ghoul? Best one to have on watch.` };
			Respected = { `Our ghoul. Nothing gets past you.`, "{Name}. Calmest heart in the Den.", `Ghoul on watch. The Pack sleeps sound.` };
		};
		Wraith = {
			Hostile = { `Wraith. No scent at all. Creepy.`, `Wraith. Drift out of the Den.`, `Wraith. Quit sneaking up on wolves.` };
			Wary = { `Wraith. I can't smell you. I hate that.`, `Wraith. How long have you been there?`, `Wraith. Make some noise. Please.` };
			Any = { `Wraith. Do you ever sleep?`, `Wraith. Even my ears missed you.`, `Wraith. Quietest thing in the woods.` };
			Friendly = { `Wraith! Best scout. No scent trail.`, "{Name}. Sneak up on Dex. Please.", `Wraith? Even the owls can't hear you.` };
			Respected = { `Our wraith. The Pack's shadow.`, "{Name}. The Den's silent guardian.", `You're the quiet in our howl.` };
		};
	};
	Hurt = {
		Hostile = { `Hurt? Should've kept your head down.`, `Limping? Pack doesn't coddle.`, `Hurt. Should've stayed out of the woods.` };
		Wary = { `Limping. Not Pack business.`, `Hurt? Nurse is that way. Go on.`, `Who got you? ...I'm just asking.` };
		Any = { `You look wrecked. Sit down.`, `Easy. Shake it off like a wet wolf.`, `Hurt? Go see the nurse. Fast.` };
		Friendly = { "{Name}! Sit. I'll get the nurse.", `Lean on me. Pack carries its own.`, `Who did it? The Pack wants to know.` };
		Respected = { `Somebody hurt our alpha? Pack! Up!`, "{Name}, rest. We'll stand watch.", `Nobody touches you again. Pack's word.` };
	};
	Outfit = {
		FullLook = {
			Hostile = { `Forest green won't fool my nose.`, `Dressed like Pack. Smells like a first-year.`, `Clothes are easy. The howl's harder.` };
			Wary = { `Forest green, huh. Earn it.`, `Looks Pack. Let's see you run Pack.`, `Somebody's been studying the Den.` };
			Any = { `Forest green. You'd vanish in the trees.`, "{Clique}'s colours. Suits you.", `Green from head to toe. Den-ready.` };
			Friendly = { `Now you look like you belong in the Den.`, "{Name}! Forest green! Howl for it!", `That's the look. Now the howl.` };
			Respected = { `Alpha in Pack green. Perfect.`, "{Clique}'s finest, {Name}. Look at you.", `Pack green on you? Den's proud.` };
		};
		RivalLook = {
			Hostile = { "{Rival} sent you? You smell like candles.", `Ivory and black? In the Den? Out.`, `All buttoned up like a hymn book. Out.` };
			Wary = { `Ivory and black. You a choir kid?`, "{Rival}'s colours. Why?", `Choir clothes near the Den? Explain.` };
			Any = { `Whoa. Very... hymn practice.`, `Ivory and black? You look like a candle.`, `Dressed for choir practice?` };
			Friendly = { "{Name}, no. Not the choir look.", `Who buttoned you up? Loosen up.`, `Undercover at the chapel? Smart.` };
			Respected = { `Undercover at choir? Learn their songs.`, `Even in ivory, you're Pack.`, `Choir disguise? Ha. Nobody'd guess.` };
		};
		Likes = {
			Hostile = { "Nice {Piece}. Still smells like nerves.", "The {Piece} is Pack. You're not.", "Who gave you the {Piece}? Not us." };
			Any = { "The {Piece}! Now you smell like the Den.", "Ooh. The {Piece}. Very wolf.", "The {Piece}? Moon-approved.", "With the {Piece}, you could run with us." };
		};
		Mocks = {
			Hostile = { "The {Piece}? In the Den? Really?", "Keep that {Piece} out of the Den.", "The {Piece}. Go sing somewhere else." };
			Friendly = { "The {Piece}? Did the choir get to you?", "Lose the {Piece}. It makes my nose itch.", `Ugh. Very chapel. You're Pack, remember.` };
			Any = { "The {Piece}? Bit holy for the Den.", "Is the {Piece} for choir practice?", "The {Piece}. Smells like a hymn book.", "The {Piece}? You look ready to sing." };
		};
	};
	DressCode = {
		Hostile = { `Den smells like us. You don't.`, `Not in that. Not ever. Turn around.`, `Out. Come back smelling like pine.` };
		Wary = { `Den's for the Pack. Dress like it.`, `Green first. Then we'll talk.`, `Can't come in like that. Rules.` };
		Any = { `Forest green past the fire. Pack rule.`, `No green, no Den. Simple.`, `Pack colours, or you wait outside.` };
		Friendly = { `Almost. Throw on some green and come in.`, "{Name}, wear the green and sit with us.", `Swap the top and I'll save you a log.` };
		Respected = { `Even Dex wears the green. Pack rule.`, `Rules are rules. Green, then in.`, `Throw on the green. Fire's waiting.` };
	};
}
