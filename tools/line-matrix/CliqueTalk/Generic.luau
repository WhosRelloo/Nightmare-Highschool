-- CliqueTalk.Generic: students without a clique, and the fallback for any clique cell left empty (the line matrix)
return {
	Greet = {
		Hostile = { `Get lost.`, `Not you.`, `Keep walking.`, `We're not friends.` };
		Wary = { `...Hey.`, `Oh. It's you.`, `What do you want?`, `Hm. Hi, I guess.` };
		Neutral = { `Hey.`, `Hi.`, `Sup.`, `How's it going?` };
		Friendly = { "Hey, {Name}!", `Oh good, it's you.`, "{Name}! What's up?", `Hey you. Good day?` };
		Respected = { "{Name}! Looking sharp.", `There's the legend.`, "Always good to see you, {Name}.", `Make way, everyone.` };
	};
	Bump = { Any = { `Watch it!`, `Whoa, sorry.`, `Excuse you.`, `Easy!` } };
	Crowded = { Any = { `Personal space?`, `Little room, please.`, `You're kind of close.`, `Can I help you?` } };
	Shoved = { Any = { `Hey! What was that?`, `Rude much?`, `Okay, ow.`, `Did you just shove me?` } };
	FightSeen = { Any = { `Ooh, here we go.`, `Somebody stop them!`, `I'm not watching. Okay, I'm watching.`, `Someone's getting detention.` } };
	Flee = { Any = { `Whoa, not near me!`, `Take it outside!`, `Nope. I'm out.`, `Someone get a teacher!` } };
	Transformed = { Any = { `What IS that?`, `Stay back...`, `Okay, that's new.`, `Please don't eat me.` } };
	Night = { Any = { `What are you doing out this late?`, `Stay in the light.`, `Late night, huh?`, `Careful out here.` } };
	FullMoon = { Any = { `Full moon tonight. Be careful.`, `You feel that? Full moon.`, `Don't go near the oaks tonight.` } };
	Race = {
		Human = { Any = { `Just a normal kid, huh? Lucky.`, `Human, huh? Welcome to the weird school.`, `Human? Stick close to the lamps.` } };
		Priest = { Any = { `Bless you. Or whatever you say.`, `Oh good, someone holy.`, `Keep that cross handy.` } };
		Vampire = { Any = { `Is it colder near you?`, `Nice fangs. Real?`, `Up all night again? You okay?` } };
		Werewolf = { Any = { `Nice ears.`, `Is that a tail?`, `You smell like the woods.` } };
		Ghoul = { Any = { `You look... tired.`, `Did you sleep at all?`, `You seem really calm today.` } };
		Wraith = { Any = { `I didn't hear you come up.`, `You walk really quietly.`, `Were you always here?` } };
	};
	Hurt = { Any = { `You okay? You look rough.`, `Go see the nurse.`, `Who did that to you?`, `Sit down before you fall down.` } };
	Outfit = {
		FullLook = { Any = { "{Clique}'s full look, huh?", "{Clique} would claim you in that.", "{Clique}'s colours? Bold." } };
		RivalLook = { Any = { "{Rival}'s colours? Here?", "{Rival}'s look? Brave.", "{Rival}'s look. People notice." } };
		Likes = { Any = { "Nice {Piece}.", "Where'd you get the {Piece}?", "Okay, the {Piece} is cool." } };
		Mocks = { Any = { "Is that a {Piece}? Really?", "Bold choice, the {Piece}.", "Hm. The {Piece}. Interesting." } };
	};
	DressCode = { Any = { `Members' corner. Dress the part.`, `Come back in our colours.`, `Not dressed like that, you're not.` } };
}
