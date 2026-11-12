-- CliqueTalk.Ink: the Ink Studio's artists and pranksters; dry, theatrical, murals, brushes and revenge by glitter (the line matrix)
return {
	Greet = {
		Hostile = { `Sleep with one eye open.`, `Your locker's next. Just so you know.`, "{Name}. I mixed your colour. It's beige.", `You walked in and the room lost contrast.` };
		Wary = { `Who let a critic in?`, `Hm. You smell like gym mats.`, "{Name}. Here to look, or to judge?", `Step around the drop cloth. Slowly.` };
		Neutral = { `Oh. Hi. Don't mind the turpentine.`, `Hey. Got any spare charcoal?`, `Hi. Stand there. No, there. Good light.`, `Hey. Is this green too green?` };
		Friendly = { "{Name}! Come see what I ruined today.", `Oh, you! Tell me this is good.`, "{Name}, hold this brush. Don't ask.", `You've got paint on your sleeve. Iconic.` };
		Respected = { "Our muse! {Name}, the wall's ready.", `We're painting the gym. You in?`, `Wren saved you a brush. The good one.`, "{Name}! Sign the mural. You earned it." };
	};
	Bump = { Any = { `Careful! Wet sketchbook!`, `Whoa! You smudged my line.`, `The palette! Ugh, now it's all mud.`, `Oof. A happy accident. For you.` } };
	Crowded = {
		Hostile = { `Back up. You're blocking my light.`, `Too close. I can smell your deodorant.`, `You're in my composition. Leave it.` };
		Respected = { `Come closer. See the brushwork?`, `Lean in. This part's a secret.`, `Closer. You get the first look.` };
		Any = { `Negative space, please.`, `You're standing in my shot.`, `A little room. I'm mid-stroke.`, `You're casting a shadow on my page.` };
	};
	Shoved = {
		Hostile = { `Oh, that's going in the mural. Badly.`, `Shove me again. Glitter's coming.`, `Cute. Check your gym bag tonight.` };
		Any = { `My charcoal! It's everywhere now!`, `Rude. And bad composition.`, `Hey! I was mid-line!`, `You knocked my brushes. All of them.` };
	};
	FightSeen = {
		Hostile = { `Hold that pose. Losing suits you.`, `Lose slower. I'm still sketching.`, `Ooh, unflattering angle. Keep going.` };
		Wary = { `Don't swing near the easels!`, `Not near the wet wall, please!`, `This is why we can't have nice murals.` };
		Any = { `The drama! The lighting! Gorgeous.`, `Somebody get a sketch of this.`, `Finally, some movement in this school.`, `Wait, wait. Do that again, slower.` };
		Friendly = { "Go, {Name}! Very dynamic!", `Lovely form! Swing again, I missed it.`, `Chin up! It's your better angle.` };
		Respected = { "{Name}, you're our next mural. Win!", `That's a museum piece! Finish it!`, `Give them a final act! Big finish!` };
	};
	Flee = { Any = { `Save the canvases! Leave the people!`, `Grab the good brushes and go!`, `Not the mural! Run!`, `I'm a painter, not a sprinter!` } };
	Transformed = {
		Hostile = { `Finally, a version of you I'd paint.`, `Scary. Still beige, somehow.`, `Big and loud. So, an athlete.` };
		Wary = { `Don't. Move. I'm sketching from afar.`, `Please don't eat the easels.`, `Um. Is that permanent? Asking for a piece.` };
		Any = { `The silhouette! The menace! Stunning.`, `I need charcoal. All the charcoal.`, `That's an album cover. That's a cover.`, `I'm calling this one "Study in Panic".` };
		Respected = { "{Name}! You're the mural now.", `Muse! Don't move! I need this!`, `Even monstrous, you've got bone structure.` };
	};
	Night = {
		Hostile = { `Out late? So are we. And our ladder.`, `Night's when we work. Don't be the canvas.`, `Walk fast. The studio's watching tonight.` };
		Wary = { `Late. You're not a snitch, are you?`, `What are you doing near the gym doors?`, `If you saw nothing, keep seeing nothing.` };
		Any = { `Night shift. Best time for walls.`, `Moonlight makes everything look painted.`, `Bring a torch. The good walls are dark.`, `Night is just a big black canvas.` };
		Friendly = { "Coming out tonight, {Name}? Bring tape.", `Grab a roller. We're going out.`, `Lookout duty? You'd be perfect.` };
		Respected = { `Muse. Tonight's wall is all yours.`, "{Name}, the ladder's ready. Lead us.", `We waited. Can't start without you.` };
	};
	FullMoon = {
		Hostile = { `Full moon. Hope something chases you.`, `Full moon. Perfect night for revenge.`, `Moon's up. Check your locker at dawn.` };
		Any = { `Full moon. The light is unreal.`, `That moon. Somebody paint that moon.`, `Full moon silver. Can't mix it. Tried.`, `Full moon. The night murals glow.` };
		Friendly = { "Full moon, {Name}. Sketch it with me?", `Come paint the moon. It won't sit still.`, `Moon's out. Rooftop sketching, yes?` };
		Respected = { `Full moon. You lead the night crew.`, "{Name}, the moon's posing for you.", `Moon's full. The secret wall's open.` };
	};
	Race = {
		Human = {
			Hostile = { `Human. Plain canvas. No primer.`, `Human. How very... unvarnished.`, `Human, and boring on top of it.` };
			Wary = { `Human? Prove you're interesting.`, `A human. Bit of a blank page.`, `Human. Don't touch the turpentine.` };
			Any = { `Human. Classic subject. Hard to draw.`, `Human. Every art class starts with you.`, `Human. Hands are the hardest part.` };
			Friendly = { `Human? Hands like yours were made to draw.`, "{Name}, great human hands. Pose?", `Human and creative. Rarer than fangs.` };
			Respected = { `Human muse. The classics would weep.`, "{Name}. Proof humans can be art.", `No fangs needed. You're our masterpiece.` };
		};
		Priest = {
			Hostile = { `A priest. Here to paint over our murals?`, `Holy and dull. Like a pamphlet.`, `Priest. You'd whitewash everything.` };
			Wary = { `Priest. Don't bless the graffiti.`, `Priest. Some walls are art, not sins.`, `A priest in the studio. Hm.` };
			Any = { `Priest. Stained glass was art too.`, `Priest. Your chapel has great ceilings.`, `A priest. Sit for a portrait?` };
			Friendly = { `Priest! Help me paint a halo right?`, "{Name}, show me those chapel windows.", `Holy subjects are my favourite. Sit?` };
			Respected = { `Our patron saint of the studio!`, "{Name}. Every altarpiece needs a muse.", `Bless the mural? It deserves it.` };
		};
		Vampire = {
			Hostile = { `Vampire. No reflection, no portrait.`, `Vampire. Even mirrors pass on you.`, `Vampire. Very last-century, isn't it?` };
			Wary = { `Vampire. Mirrors in here. Awkward.`, `Vampire. Don't loom over my easel.`, `Vampire. Are you judging my shading?` };
			Any = { `Vampire. You'd pose all night, right?`, `Vampire. Pale is a gorgeous base coat.`, `A vampire. Pure chiaroscuro.` };
			Friendly = { `Vampire? I'll paint you. Mirrors can't.`, "{Name}, those cheekbones! Sit for me.", `Night owl! Come to the midnight sessions.` };
			Respected = { `Our vampire! The only portrait that matters.`, "{Name}. Centuries of style. Teach us.", `You've seen every art movement. Spill.` };
		};
		Werewolf = {
			Hostile = { `Werewolf. Don't shed in my paint tray.`, `Werewolf. So, basically an athlete.`, `Werewolf. Loud, hairy, no technique.` };
			Wary = { `Werewolf. No sniffing the turpentine.`, `Werewolf. Claws away from the canvas.`, `Werewolf. Wipe your feet. Please.` };
			Any = { `Werewolf. Your silhouette is incredible.`, `Werewolf. Do you howl in key?`, `Werewolf. Great texture. All that fur.` };
			Friendly = { `Werewolf! Pose by moonlight? Please?`, "{Name}, your fur is a whole palette.", `Werewolf? Best study for movement ever.` };
			Respected = { `Our wolf! The moon mural's about you.`, "{Name}. Wild, untamed, art. Literally.", `Our moonlit legend. The studio's honoured.` };
		};
		Ghoul = {
			Hostile = { `Ghoul. You look like dried gesso.`, `Ghoul. Keep your grey off my palette.`, `Ghoul. A still life, but worse.` };
			Wary = { `Ghoul. Don't snack on the clay.`, `Ghoul. Gloves, please. Near the paper.`, `Ghoul. You're... very still. Stop.` };
			Any = { `Ghoul. Grey is so underrated.`, `Ghoul. Perfect for a long sitting.`, `Ghoul. You'd make a great sculpture.` };
			Friendly = { "{Name}, your grey is so painterly.", `Ghoul? Best life-drawing model ever.`, `Ghoul. Never fidgets. I love that.` };
			Respected = { `Our ghoul! Patron of the long pose.`, "{Name}. Grey, timeless, gallery-ready.", `The studio's best model, back at last.` };
		};
		Wraith = {
			Hostile = { `Wraith. Faint, pale, forgettable.`, `Wraith. Even watercolour has more body.`, `Wraith. I'd paint you, but why?` };
			Wary = { `Wraith. Did you drift through my canvas?`, `Wraith. Stop floating behind me.`, `Wraith. Things smear when you pass.` };
			Any = { `Wraith. You're basically a watercolour.`, `Wraith. The translucency! Hard to paint.`, `Wraith. Haunting the studio? Fair.` };
			Friendly = { "{Name}, help us haunt the gym tonight?", `Wraith! Our best lookout. Silent.`, `Wraith? You'd look ghostly in charcoal.` };
			Respected = { `Our wraith! Glazes have nothing on you.`, "{Name}. The ghost in our best painting.", `You float through walls. We paint them.` };
		};
	};
	Hurt = {
		Hostile = { `Hurt? Very tragic. Very dramatic.`, `Limping? I'd paint it, but no.`, `Pain is art. Yours is just pain.` };
		Wary = { `You look awful. Sit away from the easels.`, `Hurt? The nurse isn't in this studio.`, `Ugh. Sit. Don't touch anything wet.` };
		Any = { `You look rough. Sit on the drop cloth.`, `Ouch. Need a rag? A stool?`, `Who did this? I want a sketch of them.` };
		Friendly = { "{Name}! Sit. I'll get the first-aid tin.", `Who did this? Their locker's mine.`, `Easy. Lean on me. Mind the paint.` };
		Respected = { `Muse down! Somebody get the nurse!`, "{Name}, name them. We'll do the rest.", `Rest. We'll prank them twice as hard.` };
	};
	Outfit = {
		FullLook = {
			Hostile = { `Black won't hide how beige you are.`, `Our colours. Your taste. Tragic.`, `Charcoal doesn't make you an artist.` };
			Wary = { `All black. Okay. Now do something.`, `The look's right. Got any ideas?`, `Dressed like us. Can you draw?` };
			Any = { "{Clique}'s look. You did your homework.", `Black and charcoal. Very studio.`, `You look like you smell of turpentine.` };
			Friendly = { `Now you look like a starving artist.`, "{Name}, all black! Very moody. Yes.", `Ink stains next. Then you're done.` };
			Respected = { "{Clique}'s finest, dressed for it.", `Muse in black. Nobody's looked better.`, `There's our legend. Studio-ready.` };
		};
		RivalLook = {
			Hostile = { `Sportswear. In my studio.`, `Smells like gym socks and rules.`, "{Rival} lent you that? Return it." };
			Wary = { `Track jacket? Are you scouting us?`, `Gym clothes, here? Who sent you?`, "{Rival} dressed you. It shows." };
			Any = { `Very... sporty. It's a choice.`, `Polyester. Wow. Bold.`, `Did you come straight from laps?` };
			Friendly = { "{Name}, no. Not the jock look.", `Take it off. I'll lend you a vest.`, `Is this a dare? Tell me it's a dare.` };
			Respected = { `Undercover with the jocks? Genius.`, `Wearing their kit? Steal their playbook.`, `Muse in a jersey. A prank in itself.` };
		};
		Likes = {
			Hostile = { "Nice {Piece}. Wasted on you, though.", "The {Piece} has more taste than you.", "Even you can't ruin that {Piece}." };
			Any = { "The {Piece}! Okay, I'm inspired.", "That {Piece}? Pure studio energy.", "Love the {Piece}. Let me sketch it.", "Where'd you find the {Piece}? Spill." };
		};
		Mocks = {
			Hostile = { "The {Piece}. Of course. Hall monitor.", "The {Piece}? Snitch accessories.", "Wear the {Piece} near our walls. Try it." };
			Friendly = { "Lose the {Piece}. You're better.", "The {Piece}? Who hurt you?", "The {Piece}? It's fine. We can fix you." };
			Any = { "The {Piece}? So... rules, then.", "Ugh, the {Piece}. So official.", "Is the {Piece} ironic? Please say yes.", "The {Piece}. Bold, in a boring way." };
		};
	};
	DressCode = {
		Hostile = { `Studio's for the Ink. You're very... clean.`, `No black, no entry. You especially.`, `Out. You'd ruin a wall just standing there.` };
		Wary = { `Studio rules. Black or charcoal.`, `Come back with some paint on you.`, `Not in those colours. Try black.` };
		Any = { `Members only. Dress like you've suffered.`, `Studio dress code: black, and stained.`, `Wear something black. Then knock.` };
		Friendly = { `Almost! Swap in some black and come in.`, "{Name}, wear a vest. Then grab a brush.", `I'd let you in. Wren wouldn't.` };
		Respected = { `Even muses dress the part. Black, please.`, `Wren says even you. Black, then in.`, `Throw on a vest. We'll wait for you.` };
	};
}
