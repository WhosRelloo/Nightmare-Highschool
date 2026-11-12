-- CliqueTalk.Delinquents: Back Lot greasers; turf, "keep walking", dodging the hall monitor, threats left unsaid (the line matrix)
return {
	Greet = {
		Hostile = { `Nice teeth. Keep 'em.`, `Keep walking. Don't make me say it twice.`, "{Name}. You got some nerve showing up.", `Wrong lot. Wrong day. Wrong kid.`, `Bruno knows your face now. Bad luck.` };
		Wary = { `Who sent you? The monitor?`, `Hands outta your pockets. Slow.`, "{Name}, right? Haven't decided on you.", `Easy. Say what you want and go.` };
		Neutral = { `'Sup. Mind the boards.`, `Hey. Seen the hall monitor around?`, `Yeah, hi. Don't scuff the shoes.`, `Huh. Nice day to skip, huh?` };
		Friendly = { "{Name}! Pull up a crate.", `Hey, you. Want a go on the ramp?`, "{Name}. You good? Anybody bugging you?", `Look who it is. Lot's been too quiet.` };
		Respected = { "Lot's yours too, {Name}.", `Make room. Real one coming through.`, "{Name}! Bruno saved you the good crate.", `Anybody gives you grief, they answer to us.`, `Boss. Lot's swept and quiet for you.` };
	};
	Bump = { Any = { `You lost?`, `Walk around, pal.`, `Hey. Eyes front.`, `Scuff these shoes and we got problems.`, `Bump me again. See what happens.` } };
	Crowded = {
		Hostile = { `Back up. Three steps. Now.`, `You're breathing on my jacket. Don't.`, `Any closer and we're gonna have words.` };
		Respected = { `Scoot in. You gotta hear this one.`, `Pull up close. This one's not for monitors.`, `Get in the huddle. Plan's for tonight.` };
		Any = { `Little room. I'm fixing my hair.`, `Personal bubble, pal. Respect it.`, `You're on my shoes. Literally on 'em.`, `Back up. You're blocking the sun.` };
	};
	Shoved = {
		Hostile = { `Oh, now you did it.`, `That's the last free one you get.`, `Push me again. Go ahead. Try it.` };
		Respected = { `Whoa, easy. We're on the same side.`, `Okay, okay. You got arms. Noted.`, `Ha! Fair. I was in your way.` };
		Any = { `Hey! Hands off the leather!`, `Who taught you manners? Nobody?`, `You push like a hall monitor.`, `My shoes! You stepped on my shoes!` };
	};
	FightSeen = {
		Hostile = { `Go on. Lose already.`, `Swing like that on the Lot? Cute.`, `Don't stop on my account. Keep losing.` };
		Wary = { `Not on the Lot. The monitor's coming.`, `Take it past the fence, both of you.`, `Somebody keep lookout. This is loud.` };
		Any = { `Fight! Fight! ...Wait, who's winning?`, `Circle up! Give 'em room!`, `Ooh. That one's gonna sting tomorrow.`, `Fists up, chin down! C'mon!`, `Now THIS is a lunch break.` };
		Friendly = { "Chin down, {Name}! Like I showed you!", `Don't back up! Make 'em back up!`, `Watch the left! The left!` };
		Respected = { "Lot's behind you, {Name}!", `Nobody steps in. This one's theirs.`, `Finish it. We'll handle the monitor.` };
	};
	Flee = { Any = { `Cheese it! Over the fence!`, `Scatter! Meet at the bike racks!`, `Leave the boards! Leave 'em!`, `Nope! Lot's closed! Go, go, go!`, `Bruno! BRUNO! We gotta move!` } };
	Transformed = {
		Hostile = { `Big and ugly. Still on my lot.`, `Grow all you want. Lot's still ours.`, `Scary face. Seen worse in detention.` };
		Wary = { `Okay. Nobody make any sudden moves.`, `Easy... easy. We're cool. Right?`, `Uh, Bruno? We got a situation.` };
		Any = { `Whoa. That's a new look.`, `Okay, that's actually kinda tough.`, `Okay. Nobody's telling anyone about this.`, `Huh. Didn't know you had that in you.` };
		Respected = { "{Name}?! Remind me never to cross you.", `Now THAT'S Back Lot muscle.`, `Lot just got a lot scarier. Love it.`, `Nobody's touching our turf now.` };
	};
	Night = {
		Hostile = { `Lot's ours after dark. Remember that.`, `Out late? Walk faster. Way faster.`, `Streetlamp's out. Funny how that works.` };
		Wary = { `Late. You following somebody?`, `Who's out at this hour? Oh. You.`, `Night watch. Say who you are.` };
		Any = { `Night's when the Lot wakes up.`, `Streetlamps on. Collars up.`, `Monitor's gone home. Lot's open.`, `Cold night. Good jacket weather.` };
		Friendly = { "Late one, {Name}? Walk with us.", `Grab a crate. We're out till curfew.`, `Night ride? Grab a board.` };
		Respected = { `Night's ours. You call the play.`, "{Name}, the crew's out. Lead the way.", `Whole Lot's yours till sunrise.` };
	};
	FullMoon = {
		Hostile = { `Full moon. Nobody's walking you home.`, `Moon's full. Lot's not your friend tonight.`, `Full moon. Lot looks after its own. Not you.` };
		Any = { `Full moon. Even Bruno stays in.`, `Moon's full. Keep off the back fence.`, `Full moon. Lot gets weird. Stay sharp.`, `Moon's up. Something's howling past the fence.` };
		Friendly = { "Full moon, {Name}. Stick with us.", `Moon's up. You walk with the crew.`, `Nobody walks alone tonight. Lot rule.` };
		Respected = { `Full moon. We got your back. All night.`, "Stay close, {Name}. Lot's watching out.", `Moon's up. Nobody gets near you.` };
	};
	Race = {
		Human = {
			Hostile = { `Human. Nothing special. Keep walking.`, `Human. The Commons is that way.`, `Plain old human. Easy pickings.` };
			Wary = { `Human? Long way from the Commons.`, `Human. Sure you can handle the Lot?`, `Human. Don't go crying to the monitor.` };
			Any = { `Human, huh. Takes nerve to come down here.`, `Human. No claws. Gotta be quick, then.`, `Just human? Respect the hustle.` };
			Friendly = { `Human and tough. My kinda kid.`, `Human? Don't need fangs to run the Lot.`, "{Name}. Human, and still nobody's mark." };
			Respected = { `Human, and the whole Lot listens. Ha.`, "{Name}'s proof you don't need claws.", `Human? Toughest one on the Lot.` };
		};
		Priest = {
			Hostile = { `Holy roller. Lot ain't a church. Out.`, `Priest. Save the sermon. Walk.`, `Bless yourself on the way out, priest.` };
			Wary = { `Priest. Don't go blessing my jacket.`, `A priest out here? Who confessed?`, `Priest. We didn't do it. Whatever it was.` };
			Any = { `Priest, huh. Got a prayer for my grades?`, `Priest. Put in a good word for me.`, `Priest. Lot could use a blessing.` };
			Friendly = { `Priest! Bless my board. It needs it.`, "{Name}, say one for us. We need it.", `Holy and tough? I like it.` };
			Respected = { `Our priest. Even Bruno minds his mouth.`, "{Name}. Chaplain of the Back Lot. Ha!", `Nobody swears near you. House rule.` };
		};
		Vampire = {
			Hostile = { `Vampire. Fangs don't scare the Lot.`, `Vampire. Go sulk in a coffin.`, `Vampire. Sun's up soon. Tick tock.` };
			Wary = { `Vampire. Keep the fangs to yourself.`, `Vampire. Stay where I can see you.`, `Vampire. Don't get any ideas.` };
			Any = { `Vampire. Up all night? Same.`, `Vampire. Leather and night. You fit.`, `Vampire. Bet you never get caught out.` };
			Friendly = { `Vampire! Night shift on the Lot's yours.`, "{Name}, the fangs are a good look.", `Vampire? You'd own the Lot after dark.` };
			Respected = { `Our vampire. Night's yours, chief.`, "{Name}. Nobody runs the dark like you.", `Fangs on our side. Lot sleeps easy.` };
		};
		Werewolf = {
			Hostile = { `Werewolf. Go chase cars somewhere else.`, `Werewolf. Lot's not your den.`, `Werewolf. Growl at me. See what happens.` };
			Wary = { `Werewolf. Keep the claws in your pockets.`, `Werewolf. You twitchy tonight, or what?`, `Werewolf. Don't chew the tyres.` };
			Any = { `Werewolf. Bet you hear the monitor coming.`, `Werewolf. Good nose for trouble, huh?`, `Werewolf. Best lookout on the Lot, I bet.` };
			Friendly = { `Werewolf! Come ride the ramp with us.`, "{Name}. Leather and fur. Tough look.", `Werewolf? You'd scare off anybody.` };
			Respected = { `Our wolf. Nobody messes with the Lot now.`, "{Name}. Lot's got teeth now. Yours.", `Run the Lot with us tonight, wolf.` };
		};
		Ghoul = {
			Hostile = { `Ghoul. Lot's no graveyard. Beat it.`, `Ghoul. You smell like the bins.`, `Ghoul. Shuffle off. Slowly, I guess.` };
			Wary = { `Ghoul. Don't eat off my tray.`, `Ghoul. Hands where I can see 'em.`, `Ghoul. You creep up on everybody?` };
			Any = { `Ghoul. Nothing fazes you, huh?`, `Ghoul. Tough as an old boot.`, `Ghoul. Seen a lot of detentions, I bet.` };
			Friendly = { `Ghoul? Nobody pushes you around.`, "{Name}. Unshakable. Respect.", `Ghoul. You'd win any staring contest.` };
			Respected = { `Our ghoul. Unbreakable. Lot's proud.`, "{Name}. Toughest hide on the Lot.", `Nobody's lasted longer on the Lot.` };
		};
		Wraith = {
			Hostile = { `Wraith. Drift off my lot.`, `Wraith. Go haunt the Commons instead.`, `Wraith. Sneaking up on me? Bad move.` };
			Wary = { `Wraith. Quit floating behind me.`, `Wraith. Were you listening? Were you?`, `Wraith. You're giving me chills. Quit it.` };
			Any = { `Wraith. Monitor never sees you, huh?`, `Wraith. Walls don't stop you. Handy.`, `Wraith. Quietest one on the Lot.` };
			Friendly = { `Wraith! Best lookout ever. Nobody sees you.`, "{Name}, scout the hall for us?", `Wraith? Teach me to walk that quiet.` };
			Respected = { `Our wraith. Lot's eyes and ears.`, "{Name}. Ghost of the Back Lot. Legend.", `Nobody hears you coming. Perfect.` };
		};
	};
	Hurt = {
		Hostile = { `Hurt? Should've kept walking.`, `Limping off my lot. Good.`, `Ouch. Next time, pick a different lot.` };
		Wary = { `You look rough. Not my problem.`, `Hurt? Nurse is that way. Go.`, `Who got you? ...Not that I care.` };
		Any = { `You look beat. Sit on the crate.`, `Shake it off. The Lot don't do tears.`, `Rough day? Nurse is past the gym.` };
		Friendly = { "Name 'em, {Name}. We'll have a word.", `Sit down. I got gum and a bandage.`, `Easy. Lean on me. Lot's got you.` };
		Respected = { `Somebody hit one of ours? Find 'em.`, "{Name}'s hurt. Nobody leaves till we know who.", `Sit. Bruno's handling it personally.` };
	};
	Outfit = {
		FullLook = {
			Hostile = { `Dressing like the Lot don't make you Lot.`, `Nice costume. You're still not one of us.`, `Looks right. You still ain't us.` };
			Wary = { `You're dressed for it. Now earn it.`, `Huh. Somebody's been studying us.`, `Look's right. Let's see if you scare.` };
			Any = { "{Clique} noticed the look. Nice.", `Now you look like trouble.`, `Sharp. Real Back Lot.` };
			Friendly = { `Now you look like you belong out here.`, "{Name}, lookin' like trouble. Good.", `That's the look. Shoes next.` };
			Respected = { `Now that's how the Lot dresses.`, "{Clique} never looked better, {Name}.", `Lot royalty. Dressed the part.` };
		};
		RivalLook = {
			Hostile = { `Tucked-in shirt on my lot? Bold.`, "{Rival} send you? Go back and stay.", `Picture-day clean. Wrong lot, pal.` };
			Wary = { `Dressed like a Commons kid. Why?`, "{Rival} sent a spy? Cute.", `All neat and pressed. You lost?` };
			Any = { `Whoa. Very... hall monitor.`, `Ironed creases? Out here?`, `Commons clothes, on the Lot? Huh.` };
			Friendly = { "{Name}, no. Not the Commons look.", `Who ironed you? Untuck something.`, `Undercover with the goody-goodies?` };
			Respected = { `Spying on the Commons? Smart.`, `Even neat and pressed, you're Lot.`, `Undercover? Find where Pip hides the snacks.` };
		};
		Likes = {
			Hostile = { "The {Piece}? Wasted on you.", "Where'd you lift the {Piece}?", "Even the {Piece} can't toughen you up." };
			Any = { "Okay. The {Piece}. Now we're talking.", "The {Piece}? Real Back Lot.", "Ooh, the {Piece}. Bruno'd approve.", "With the {Piece}? You mean business." };
		};
		Mocks = {
			Hostile = { "Be a shame if that {Piece} went missing.", "Keep the {Piece} off my lot.", "The {Piece}? Gonna report me too?" };
			Friendly = { "The {Piece}? Who made you wear that?", "Lose the {Piece}. I won't tell anyone.", `Ugh. You're better than that. C'mon.` };
			Any = { "The {Piece}? What are you, a monitor?", "Who wears the {Piece} on purpose?", "The {Piece}. Real tough. Real tough.", "Did your mom pick out the {Piece}?" };
		};
	};
	DressCode = {
		Hostile = { `This lot's ours. You don't look it.`, `Turn around. You ain't dressed for here.`, `Out. Come back looking like you mean it.` };
		Wary = { `Lot rules. Dress like us or walk.`, `Can't come back here looking like that.`, `Look the part first. Then we'll talk.` };
		Any = { `Members only past the fence. Dress for it.`, `Back Lot look, or back the way you came.`, `No Lot gear, no entry. Simple.` };
		Friendly = { `Almost. Lose the neat stuff and come in.`, "{Name}, dress like us and you're in.", `Swap the shirt and I'll hold the gate.` };
		Respected = { `Even you dress Lot back here. Rules.`, `Bruno's rule, not mine. Change, then in.`, `Throw on the Lot gear. Crate's yours.` };
	};
}
