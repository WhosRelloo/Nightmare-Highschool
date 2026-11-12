-- CliqueTalk.Athletes: the varsity Ravens; loud, clipped, all coach, laps, hydration and the team (the line matrix)
return {
	Greet = {
		Hostile = { `Bench warmer. Move.`, `You again? Coach warned us about you.`, `Sideline's that way. Live there.`, "Nobody picked you, {Name}. Nobody will.", `You're in my lane. Get out of it.` };
		Wary = { `You lost? The gym's not a hallway.`, `Trying out, or just standing there?`, "{Name}. Sign-up sheet's by the door.", `Hm. Didn't see you at practice.` };
		Neutral = { `Yo. You catch the game Friday?`, `Hey. Got a spare water bottle?`, `Sup. Don't step on the free-throw line.`, `Hey. Already ran five miles today.` };
		Friendly = { "{Name}! Good hustle yesterday.", `Hey! You coming to the game?`, "Up top, {Name}!", `There you are! Stretch with us?` };
		Respected = { "Team's here! {Name}!", `MVP in the building!`, "Captain says you're in, {Name}. Suit up.", `Make a hole! Starter coming through!`, "{Name}! Saved you the good ball." };
	};
	Bump = { Any = { `Whoa, watch the shoulder!`, `Eyes up, eyes up!`, `Easy! I've got the ball bag.`, `That's a yellow card, buddy.`, `Oof. Nice block. Wrong sport.` } };
	Crowded = {
		Hostile = { `Back up. You're in my zone.`, `Man-to-man's for the court. Back off.`, `Too close. I'm calling a foul.` };
		Respected = { `Huddle up. Here's the play.`, `Closer. Coach can't hear this part.`, `Squeeze in. The bench has room for you.` };
		Any = { `Give me some room, I'm stretching.`, `Personal space. Arm's length. Go.`, `Hey, I'm mid-rep here.`, `You're in my warm-up space.` };
	};
	Shoved = {
		Hostile = { `Oh, you want contact? Okay.`, `That's flagrant. I don't forget fouls.`, `I bench twice your weight. Try again.` };
		Any = { `Hey! Ref! Did you see that?`, `Whoa! Illegal shove!`, `Not cool. Not cool at all.`, `Watch the knee, it just healed!` };
	};
	FightSeen = {
		Hostile = { "And {Name} fumbles! Classic.", `Big swing, no follow-through. Sad.`, `Zero footwork. Zero. Painful to watch.` };
		Wary = { `Keep it off the court, guys!`, `Somebody call it. Is that a foul?`, `Not in the gym! We just waxed it!` };
		Any = { `Left hook! Ooh, right on the bell!`, `It's a brawl at midcourt, folks!`, `Keep score! Somebody keep score!`, `Two technicals. Both of them. Easy.` };
		Friendly = { "Go, {Name}! Keep your guard up!", `Elbows in! Elbows in! Nice!`, `That's the form! Breathe, then swing!` };
		Respected = { "{Name} with the takedown! What a play!", `MVP! MVP! MVP!`, "The crowd's going wild for {Name}!", `That's our starter! Finish it!` };
	};
	Flee = { Any = { `Coach! COACH!`, `Everybody to the locker room!`, `Sprint drill! This is NOT a drill!`, `Leave the gear! Just run!`, `Good thing I do cardio. Bye!` } };
	Transformed = {
		Hostile = { `Grew a few feet? Still can't catch.`, `Big doesn't mean good. Ask any lineman.`, `Scary? You still run like a walk-on.` };
		Wary = { `Uh... is that allowed in the gym?`, `Okay. Nobody tackle that.`, `Back away slow. Don't spook it.` };
		Any = { `Whoa. What's that thing's forty time?`, `Scouts would sign that in a heartbeat.`, `Now THAT'S a defensive lineman.`, `Somebody get that thing a jersey.` };
		Respected = { "{Name}?! Dude. You're on offence.", `Beast mode. Literally. Let's go!`, `The Ravens never had a mascot this good.`, "{Name}, Coach is gonna lose his mind." };
	};
	Night = {
		Hostile = { `Night practice is closed. Go home.`, `No field lights for you. Beat it.`, `Out late? Hope you can sprint.` };
		Wary = { `Late. You training, or lurking?`, `Field lights are off. Why are you here?`, `Curfew's soon. Don't make me report you.` };
		Any = { `Night drills. The floodlights are on.`, `Late run. Gotta make weight.`, `Stay where the floodlights reach.`, `Night games are the best games.` };
		Friendly = { "Night run, {Name}? I'll pace you.", `Lights are on at the track. Coming?`, `Late practice. Coach brought snacks.` };
		Respected = { `Track's lit. Saved you a lane.`, "{Name}! Night scrimmage. You're starting.", `Captain wants you at night drills.` };
	};
	FullMoon = {
		Hostile = { `Full moon. Hope you're fast.`, `Moon's up. Nobody's waiting for you.`, `Full moon and you're alone. Bad play.` };
		Any = { `Full moon. Practice is cancelled.`, `Moon's full. Nobody runs the woods loop.`, `Full moon. Stretch, hydrate, stay in.`, `Moon's full. The field's not safe.` };
		Friendly = { "Full moon, {Name}. Run with a buddy.", `Stick with the team tonight. Moon's up.`, `Full moon. Buddy system. You're mine.` };
		Respected = { `Full moon. The team walks you home.`, "Full moon. We've got your back, {Name}.", `Moon's up. Ravens stick together.` };
	};
	Race = {
		Human = {
			Hostile = { `Human? Then you've got no excuse. Move.`, `No fangs, no claws, no game.`, `Human. Easiest tackle of my life.` };
			Wary = { `Human. Can you even keep up?`, `Human, huh? Bet you gas out early.`, `Human. Don't get hurt on my court.` };
			Any = { `Human. Fair fight, at least.`, `Human? Hydrate. You need it most.`, `Human. Old-school athlete.` };
			Friendly = { `Human and fast? You'd make varsity.`, `Human! No powers, all hustle. Nice.`, `Humans train harder. It shows.` };
			Respected = { "{Name}. All human. All heart.", `No claws, no fangs, still MVP.`, `You make the rest of us look lazy.` };
		};
		Priest = {
			Hostile = { `Pray all you want. Still benched.`, `Holy? Bless your terrible footwork.`, `A priest. Go chant somewhere else.` };
			Wary = { `Priest. Don't bless the other team.`, `No praying on the free-throw line.`, `Priest, huh. Can you even run?` };
			Any = { `A priest. Bless the game ball?`, `Priest? Say one for our season.`, `Priest. Got a prayer for my knee?` };
			Friendly = { `Bless the bus before the away game?`, `A priest on the team? Lucky us.`, "{Name}, pray for a win Friday?" };
			Respected = { `Our priest! We haven't lost since.`, `Team chaplain! Bless the huddle!`, "{Name}'s blessing beats any pep talk." };
		};
		Vampire = {
			Hostile = { `Vampire? Try a day game. Oh, wait.`, `Pale and slow. Bad combo.`, `Vampire. Stuck in the shade forever.` };
			Wary = { `Vampire. Keep those fangs off my water.`, `Vampire. Night scrimmages only, huh?`, `Cold hands. Don't spot me.` };
			Any = { `Vampire. You'd be great at night games.`, `Vampire. Ever tried night hurdles?`, `Vampire? Bet you never get tired.` };
			Friendly = { `Vampire! Join the night league!`, `Fangs as a mouthguard? Genius.`, "{Name}, you'd own the night relay." };
			Respected = { `Our vampire! Undefeated after dark.`, `Night games are yours. Nobody's faster.`, "{Name}. Fastest thing on the night track." };
		};
		Werewolf = {
			Hostile = { `Werewolf. Don't shed on the mats.`, `Werewolf. Keep your fur off my bench.`, `Werewolf. Fetch is a sport, I guess.` };
			Wary = { `Werewolf. Please don't chew the ball.`, `Werewolf. Full moon's not a sick day.`, `Werewolf. Claws off the court, okay?` };
			Any = { `Werewolf. Bet your sprint time is wild.`, `Werewolf. Ever tried the long jump?`, `Werewolf. Great stamina, I bet.` };
			Friendly = { `Werewolf! Come run the woods loop!`, `Werewolf? You'd crush the relay.`, "{Name}, tryouts are Monday. Be there." };
			Respected = { `Our wolf! The Rovers won't come near us.`, `Werewolf on the line. Undefeated.`, "{Name}. Best mascot. Best player." };
		};
		Ghoul = {
			Hostile = { `Ghoul. You look like you lost already.`, `Ghoul. Even the sub bench says no.`, `Grey and slow. Hard pass.` };
			Wary = { `Ghoul. Don't sit on my towel.`, `Ghoul. You hydrating? Like, at all?`, `Ghoul. Did you skip every warm-up?` };
			Any = { `Ghoul. Bet you never pull a muscle.`, `Ghoul. Nothing hurts you, huh?`, `Ghoul. Tough as an old goalpost.` };
			Friendly = { `Ghoul? You'd be a wall on defence.`, "{Name}, you never get tired. Teach me.", `Ghoul goalie. Nobody's scoring on you.` };
			Respected = { `Our ghoul! The unbreakable wall!`, "{Name}. Hasn't missed a game in years.", `Nothing stops you. Nothing. Respect.` };
		};
		Wraith = {
			Hostile = { `Wraith. Ghosting practice again?`, `Wraith. Floating isn't running.`, `Wraith. Go haunt the art kids.` };
			Wary = { `Wraith. Don't sneak up on me mid-rep.`, `Wraith. Is that offside? Can you be?`, `Wraith. Stop drifting onto the field.` };
			Any = { `Wraith. You'd be a ghost on the wing.`, `Wraith. Silent footsteps. Nice.`, `Wraith. Do you even sweat?` };
			Friendly = { `Wraith! Nobody can mark you. Ever.`, "{Name}, play wing. They'll never see you.", `Wraith on our side? Unfair. Love it.` };
			Respected = { `Our wraith! Untouchable. Literally.`, "{Name}. The ghost on the wing. Legend.", `Can't block what you can't catch. Unreal.` };
		};
	};
	Hurt = {
		Hostile = { `Hurt? Should've stretched.`, `Limping? Good. Stay benched.`, `Ice it. Somewhere else.` };
		Wary = { `Walk it off. Over there, maybe.`, `You're limping. Don't play on that.`, `Hurt? Sit before you tear something.` };
		Any = { `You okay? You look winded.`, `Shake it out. The nurse is past the gym.`, `Ice and water. Trust me.` };
		Friendly = { "Easy, {Name}. Sit. I've got ice.", `Hey, hey. Drink some water. Breathe.`, `Who did that? Point. I'll handle it.` };
		Respected = { `Medic! Our starter's down!`, "{Name}'s hurt! Somebody get Coach!", `Sit. We'll cover your laps. Rest.` };
	};
	Outfit = {
		FullLook = {
			Hostile = { `The jacket doesn't make you varsity.`, `Nice kit. You still can't play.`, `You bought the look. Not the hustle.` };
			Wary = { `Dressed for tryouts? We'll see.`, `Kit's right. Now show me a lap.`, `Joggers on. Can you actually run?` };
			Any = { `Full kit. Somebody's trying out.`, "{Clique} would sign you on looks alone.", `Varsity look. Now get varsity legs.` };
			Friendly = { `Now you look like a teammate!`, "{Name}, full kit! Suit up Friday?", `Looking game-ready. Love it.` };
			Respected = { `Full kit, MVP. Ravens forever.`, `That's how a starter dresses.`, "{Clique} look good on you, {Name}." };
		};
		RivalLook = {
			Hostile = { "{Rival} sent you? The paint's still wet.", `All black? Off to sulk in the studio?`, "{Rival}'s errand kid. Get lost." };
			Wary = { `Charcoal vest. You with the paint kids?`, `All black. You one of the art crowd?`, "{Rival}'s colours in my gym? Hm." };
			Any = { `Whoa. Very... art class.`, `Black on black. Going to a poetry slam?`, "{Rival}'s look, here? Brave." };
			Friendly = { `Undercover in the studio? Smart.`, "{Name}, no! Not the artsy kids!", `Black's not your colour. Trust me.` };
			Respected = { `Spying on the paint kids? Legend.`, `Even in black, you're varsity to us.`, `Find out who did the gym doors.` };
		};
		Likes = {
			Hostile = { "Nice {Piece}. Wasted on you.", "The {Piece}'s varsity. You're not.", "Where'd you steal that {Piece}?" };
			Any = { "Ooh, the {Piece}! Team spirit!", "That {Piece}? Game-day ready.", "Okay, the {Piece} is solid.", "The {Piece}! Now you look like us." };
		};
		Mocks = {
			Hostile = { "The {Piece}. Of course. Nerd.", "The {Piece} gets benched. So do you.", "Keep that {Piece} off my court." };
			Friendly = { "Ditch the {Piece}. You're one of us.", "The {Piece}? Bro. No.", `I'll pretend I didn't see that.` };
			Any = { "The {Piece}? Can you even run in that?", "Drop the {Piece}. Pick up a ball.", "Is the {Piece} for extra credit?", `Is that homework? On purpose?` };
		};
	};
	DressCode = {
		Hostile = { `The gym's for the team. You're not it.`, `No jacket, no court. Especially you.`, `Out. Team only. Bench is outside.` };
		Wary = { `Gym's for the team. Get a jacket.`, `Team kit only past the bleachers.`, `No jersey, no entry. Coach's rules.` };
		Any = { `Locker room's team only. Kit up.`, `Varsity jacket or gym shirt. Rules.`, `Suit up first. Then we'll talk.` };
		Friendly = { `Grab a jacket and you're in. Promise.`, "{Name}, kit up! Then come warm up.", `So close. Joggers and a jacket, go.` };
		Respected = { `Even starters wear the kit. Go.`, `Coach would bench me. Kit up, then in.`, `Jacket on, Captain's orders. Then in.` };
	};
}
