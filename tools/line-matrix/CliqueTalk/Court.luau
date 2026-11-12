-- CliqueTalk.Court: old money and velvet manners; "darling", "how common", and the night belongs to them (the line matrix)
return {
	Greet = {
		Hostile = { `Oh. It's you. How disappointing.`, `Don't speak. You'll only make it worse.`, `We remember everything, darling.`, `Someone show this one the door.` };
		Wary = { `And who let you in?`, `Hm. Keep your hands off the silver.`, "{Name}, isn't it? We'll see.", `Mind your manners. Everyone's watching.` };
		Neutral = { `Charmed, I suppose.`, `Oh. Hello. Do I know your family?`, `Mind the hem, please.`, `You may approach.` };
		Friendly = { "{Name}, darling! Come, sit.", `Oh, good. Someone with manners.`, "{Name}! You look almost expensive.", `Darling, you simply must hear this.` };
		Respected = { "{Name}. The Parlor's been dull without you.", `Make room. Our favourite has arrived.`, `Someone fetch the good china. It's you.`, "Vesper asked after you, {Name}." };
	};
	Bump = { Any = { `Excuse you. This coat costs more than you.`, `Do watch where you're going, darling.`, `Ugh. You've creased me.`, `Hands off the velvet.` } };
	Crowded = {
		Hostile = { `Back. You're breathing my air.`, `Closer and I'll have you removed.`, `Distance, please. I can smell the Commons.` };
		Respected = { `Sit closer, darling. Gossip's better quiet.`, `Lean in. You'll want to hear this.`, `Closer. We don't shout in the Parlor.` };
		Any = { `Darling, personal space is free.`, `A little room. I'm not public property.`, `You're crushing the silk.`, `Do you mind? This is couture.` };
	};
	Shoved = {
		Hostile = { `You'll pay for that. Literally.`, `Touch me again. I dare you, darling.`, `Daddy's lawyers will hear about this.` };
		Any = { `Did you just put your hands on me?`, `How dare you. In public, too.`, `My cuffs! You've ruined my cuffs.`, `Ugh. Has nobody taught you manners?` };
	};
	FightSeen = {
		Hostile = { `Oh, do lose. It would make my evening.`, `Brawling. How terribly common.`, `I do hope they ruin your shirt.` };
		Wary = { `Fists? How very Back Lot of you.`, `Keep it away from the drapes.`, `This is why we don't invite you.` };
		Any = { `Ugh, brawling. In this light?`, `Ten silver on the one with better shoes.`, `Someone's having a vulgar evening.`, `Do it quietly, at least.` };
		Friendly = { `Darling, keep your chin up. Literally.`, "Ten silver on {Name}. Don't disappoint.", `Make it look effortless, sweetie.` };
		Respected = { "Teach them manners, {Name}!", `The Court is watching. Make it elegant.`, `Finish it, darling. We have reservations.` };
	};
	Flee = { Any = { `Not in these shoes! Move!`, `Somebody bring the car round!`, `I'm not running. I'm leaving briskly.`, `Someone save the silver!` } };
	Transformed = {
		Hostile = { `Even as a beast, you're common.`, `Keep that thing off the carpet.`, `Fur? On the furniture? Absolutely not.` };
		Wary = { `Charming. Does it shed?`, `Stay back. This is silk.`, `Someone ring for the groundskeeper.` };
		Any = { `Oh, how dramatic. I approve.`, `The dark does suit you.`, `How positively feral, darling.`, `Now that's an entrance.` };
		Respected = { `Darling, you're terrifying. I adore it.`, "{Name}, that look? Iconic.", `The night belongs to us. Tonight, to you.` };
	};
	Night = {
		Hostile = { `After dark, you're on our ground.`, `Out late? The night isn't yours, darling.`, `Dark suits us. It doesn't suit you.` };
		Wary = { `Out after dark? How brave. How unwise.`, `The night has rules. Learn them quickly.`, `Keep to the lamps, darling. Ours is the dark.` };
		Any = { `Finally. The sun's gone. Bliss.`, `Ah, the good hours. At last.`, `Night at last. Everyone's prettier.`, `Evening, darling. Now it gets interesting.` };
		Friendly = { "Come out with us tonight, {Name}.", `The Parlor opens properly now. Coming?`, `Darling, the night's young. So are we.` };
		Respected = { "The night is ours, {Name}. Yours too.", `Darling. The Parlor waited up for you.`, `Wear silver. We're going out.` };
	};
	FullMoon = {
		Hostile = { `Full moon. Do try to get lost.`, `The moon won't save you from us.`, `Full moon. Walk home alone, darling.` };
		Any = { `A full moon. Simply divine.`, `Moonlight and silver. Perfection.`, `Full moon. The dogs will be howling.`, `Best night of the month, darling.` };
		Friendly = { "Full moon, {Name}. Wear something dark.", `Walk with us under the moon, darling.`, `The moon's out. So is the good silver.` };
		Respected = { `Full moon, darling. The Court rides out.`, "Stay close, {Name}. Tonight's ours.", `The moon's full and so is our table.` };
	};
	Race = {
		Human = {
			Hostile = { `Human and rude. Truly the full set.`, `Run home, little human.`, `Human. That explains the manners.` };
			Any = { `Human. How quaint.`, `Human? Well, someone has to be.`, `A human. Warm hands. How novel.` };
		};
		Priest = {
			Hostile = { `Wave that cross at me again. Go on.`, `Pious and poor. A classic.`, `Take your hymns elsewhere.` };
			Any = { `A priest. Please don't bless the furniture.`, `Holy types never get invited twice.`, `Priest. Put the cross away, darling.` };
		};
		Vampire = {
			Hostile = { `Vampire, and still not good enough.`, `Even your fangs look cheap.`, `A vampire without manners. Shameful.` };
			Friendly = { "A fellow night owl. Do sit, {Name}.", `Fangs and manners. How rare.`, `One of the old names? Welcome, darling.` };
			Any = { `Vampire. Which family, darling?`, `Fangs, at least. That's a start.`, `A vampire. You'd look divine in crimson.` };
		};
		Werewolf = {
			Hostile = { `Off the carpet, mutt.`, `Sit. Stay. Leave.`, `Muddy paws stay outside, darling.` };
			Any = { `Werewolf. Please don't shed.`, `Did someone let the dog in?`, `Werewolf. Is the Den missing you?` };
		};
		Ghoul = {
			Hostile = { `Ghoul. Stay away from the buffet.`, `Keep your hands off the canapes.`, `You make the whole room look dated.` };
			Any = { `Ghoul. Have you tried moisturiser?`, `Darling, you look positively vintage.`, `A ghoul. Grey is in this season.` };
		};
		Wraith = {
			Hostile = { `Drift elsewhere, darling.`, `Haunt somebody poorer.`, `There's no guest list for ghosts.` };
			Any = { `A wraith. So mysterious. So pale.`, `Darling, you're see-through. Daring.`, `Wraith. Haunting the Parlor again?` };
		};
	};
	Hurt = {
		Hostile = { `Hurt? How tragic. Truly. Anyway.`, `You look dreadful. It suits you.`, `Someone finally taught you manners.` };
		Wary = { `You look dreadful, darling. Go away.`, `Don't faint on the carpet.`, `The nurse is that way. Off you go.` };
		Any = { `Oh, darling, you look ghastly.`, `Do sit before you fall over.`, `Who ruined your evening?` };
		Friendly = { "{Name}! Sit. Someone fetch the nurse.", `Who did this? I'll have them ruined.`, `Darling, lean on me. Mind the silk.` };
		Respected = { "Who did this, {Name}? They'll regret it.", `Bring a chair! Our favourite is hurt.`, `The Court looks after its own. Sit.` };
	};
	Outfit = {
		FullLook = {
			Hostile = { `Our crimson won't hide what you are.`, `Wearing our colours? The nerve.`, `Crimson doesn't buy a seat at our table.` };
			Wary = { `Crimson. Well. It's a start.`, `The vest fits. The manners don't yet.`, `Trying very hard, aren't we?` };
			Any = { "Dressed like {Clique}. Ambitious.", `Crimson and black. You've been studying.`, `Not bad. The cuffs need work.` };
			Friendly = { `Crimson suits you, darling. Fully.`, "{Name}, you look like money tonight.", `Now that's dressing for the Parlor.` };
			Respected = { `Darling, you look like old money.`, `Vesper would approve. I approve.`, "Crimson and silver, {Name}. Perfection." };
		};
		RivalLook = {
			Hostile = { "Dressed like {Rival}? Pass.", `A cardigan. In my presence.`, `Back to your dusty little library.` };
			Wary = { `Charcoal? Are you in mourning?`, "Did {Rival} dress you? It shows.", `That cardigan has seen things. Dull things.` };
			Any = { `Oh dear. Library chic.`, `You smell of lamp oil and old books.`, `Is that a vest or a cry for help?` };
			Friendly = { `Darling, no. Burn the cardigan.`, `You're too pretty to dress like a ledger.`, "Not you too, {Name}. Not the cardigan." };
			Respected = { `Darling, spying on the bookworms? Clever.`, `Infiltrating the Archive? Report back.`, `Only you could make charcoal work.` };
		};
		Likes = {
			Hostile = { "Nice {Piece}. Stolen, I assume.", "The {Piece} is lovely. You're not.", "That {Piece} deserves better company." };
			Any = { "Now that {Piece} looks expensive.", "The {Piece}. Finally, some taste.", "Where did you get that {Piece}? Tell me.", `You dressed with intent. Lovely.` };
		};
		Mocks = {
			Hostile = { "The {Piece}. Of course. How common.", "Even the {Piece} looks embarrassed.", `Library jumble sale, was it?` };
			Friendly = { "Darling, lose the {Piece}. Please.", "The {Piece}? We'll pretend we didn't see.", `I'll buy you something better. Hush.` };
			Any = { "The {Piece}? Did you walk here?", "Darling, the {Piece}. Why?", `How common.`, "Is the {Piece} for work? You poor thing." };
		};
	};
	DressCode = {
		Hostile = { `Crimson, darling. Or the door.`, `Not in those rags. Not ever.`, `The Parlor has standards. You aren't one.` };
		Wary = { `No crimson, no seat. House rules.`, `Change first. Then we'll talk.`, `The Parlor dresses for dinner. Do try.` };
		Any = { `Members wear crimson. Come back in it.`, `Not dressed for the Parlor, I'm afraid.`, `Mind the dress code, darling.` };
		Friendly = { `Darling, I'd let you in. Not in that.`, "Crimson, {Name}. Then come sit.", `Change, sweetie. I'll save you a seat.` };
		Respected = { `Even you, darling. Crimson first.`, `Rules keep the riff-raff out. Humour us.`, `Pop on the crimson. We'll wait.` };
	};
}
