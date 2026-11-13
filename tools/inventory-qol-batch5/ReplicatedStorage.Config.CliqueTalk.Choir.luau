-- CliqueTalk.Choir: the Chapel's candle-bearing singers; blessings, hymns, dusk practice and "something unholy" (the line matrix)
return {
	Greet = {
		Hostile = { `I'll pray for you. Briefly.`, `Begone. Gently, but begone.`, "{Name}. The candles dimmed. Coincidence?", `Bless your heart. Now leave.`, `Something unholy just walked in.` };
		Wary = { `Peace be with you. From a distance.`, `Hm. Something about you feels... off.`, "{Name}. Been to the chapel lately? No?", `We'll keep you in our prayers. Just in case.` };
		Neutral = { `Good day. Practice is at dusk.`, `Hello. Mind the wax on the floor.`, `Hi. Hum along if you know it.`, `Peace. Have you seen my hymnal?` };
		Friendly = { "Peace be with you, {Name}!", `Oh, good! Come hear our new hymn.`, "{Name}! You have such a kind soul.", `Hello, friend. Staying for the next hymn?` };
		Respected = { `The candles burn brighter for you.`, "{Name}! Blessings upon blessings.", `Make way. A friend of the Chapel.`, "Sing with us, {Name}. Front row.", `Lucien saved you a candle. The tall one.` };
	};
	Bump = { Any = { `Oh! Mind the hymnals!`, `Careful! The candle's lit!`, `Bless you. Now watch where you're going.`, `Pardon! I was mid-scale.`, `Ow. Forgiven. Mostly.` } };
	Crowded = {
		Hostile = { `Back. Your aura is giving me a headache.`, `Too close. I'm losing my note.`, `Kindly stand somewhere else. Far.` };
		Respected = { `Come closer. Share my hymnal.`, `Squeeze in. There's room in the pew.`, `Stand with us. We'll harmonise.` };
		Any = { `A little room? I'm warming up my voice.`, `Mind my candle, please.`, `Personal space is a blessing too.`, `Could you step back? I'm mid-hum.` };
	};
	Shoved = {
		Hostile = { `Forgiven. Not forgotten.`, `Peace. PEACE. I said peace.`, `Shove me again and I'll sing. Loudly.` };
		Respected = { `Oh! Spirited. Very spirited.`, `All right, all right. I'm moving.`, `Ha! I'll pray for my balance.` };
		Any = { `Hey! I nearly dropped the candle!`, `Was that necessary? Truly?`, `Saints preserve me, how rude.`, `My collar! You crumpled my collar!` };
	};
	FightSeen = {
		Hostile = { `Go on. I'll pray for the loser.`, `Brawling. How predictably unholy.`, `Fists in the hallway. How very you.` };
		Wary = { `Not near the chapel, please!`, `Peace! Someone keep the peace!`, `Mind the stained glass!` };
		Any = { `Oh, heavens. Somebody stop them.`, `I'll sing something calming. Hmmm...`, `Both of you, apologise after.`, `This calls for a very loud hymn.` };
		Friendly = { "Guard up, {Name}! We're praying for you!", `Stay steady! Breathe like in practice!`, `You've got the high ground! Keep it!` };
		Respected = { "{Name} fights with a blessing! Go!", `Sing, everyone! Battle hymn! Now!`, `Righteous! Absolutely righteous!` };
	};
	Flee = { Any = { `Back inside the chapel! Quickly!`, `Grab the candles! Leave the hymnals!`, `Sanctuary! SANCTUARY!`, `Run now, pray later!`, `I haven't finished the hymn!` } };
	Transformed = {
		Hostile = { `Begone! I have a hymnal and I'll use it!`, `Back! Back, foul thing! ...Please?`, `Begone! In the name of choir practice!` };
		Wary = { `Begone! ...Wait, are you still you?`, `Nobody panic. Hum something soothing.`, `Stay back. I'm holding a very holy candle.` };
		Any = { `Something uncanny! I KNEW it!`, `Begone! Kindly! With respect!`, `Begone, foul... oh. Hi. Still, begone.`, `Every candle just went out. Of course.` };
		Friendly = { `Oh! Still you. Just... different.`, `Friend? Blink twice if it's you.`, `Easy, friend. We'll hum you calm.` };
		Respected = { "{Name}? Even like that, you're blessed.", `A new shape. Same blessed soul.`, `We'll sing you back. Gently.` };
	};
	Night = {
		Hostile = { `Out after vespers? Of course you are.`, `The dark suits you. Not a compliment.`, `Night and you. Two things I avoid.` };
		Wary = { `It's late. Why aren't you indoors?`, `Stay where it's lit. Trust me.`, `Late. The bells rang an hour ago.` };
		Any = { `Dusk practice ran long again.`, `Light a candle. The dark's busy.`, `Hear that? Probably nothing. Probably.`, `Night hymns sound better. Spookier, too.` };
		Friendly = { "{Name}! Walk us back to the chapel?", `Late night? Take a candle. I've spares.`, `Stay for evening song. It's lovely.` };
		Respected = { `The candles waited up for you.`, "{Name}, lead the night procession?", `The night's safer with you here. Truly.` };
	};
	FullMoon = {
		Hostile = { `Moon's full. I'll pray for you twice.`, `Stay far from the chapel tonight.`, `Big moon, and here you are. Of course.` };
		Any = { `Bolt the chapel doors. It's that moon.`, `Full moon. The Pack will be howling all night.`, `Hymns at double volume tonight.`, `Every candle lit. It's that night.` };
		Friendly = { "Full moon, {Name}. Shelter in the chapel?", `Sing with us at evensong. Candles lit.`, `Hum with us. It helps. Truly.` };
		Respected = { `Stand with us at the doors tonight.`, "{Name}, the chapel's safest with you.", `Full moon, but you're here. We're blessed.` };
	};
	Race = {
		Human = {
			Hostile = { `Human. Ordinary, and still unruly.`, `Human. No excuse for those manners.`, `Human. You'd think you'd behave.` };
			Wary = { `Human. Are you sure? Truly?`, `Human. Then why did the candle flicker?`, `Human. Say a little prayer, just in case.` };
			Any = { `Human. Blessedly kind, I hope.`, `Human! A rare soul in these halls.`, `Human. A friendly face. Lovely.` };
			Friendly = { `Human and kind. A blessing.`, "{Name}, human and good-hearted.", `Humans make lovely altos. Join us!` };
			Respected = { `Human, and braver than any of us.`, "{Name}. Proof that kindness is enough.", `Human? Dearest of all of us.` };
		};
		Priest = {
			Hostile = { `Priest, and you act like that? Shameful.`, `A priest who skips practice. Tsk.`, `Priest. You disgrace the collar.` };
			Wary = { `Priest. Whose choir do you sing for?`, `Priest. Why aren't you with us?`, `Priest. Wandered off from the flock?` };
			Any = { `Priest! Kindred spirit. Come sing.`, `Priest. The chapel doors are open to you.`, `Priest. We should compare hymnals.` };
			Friendly = { `Priest! Join the choir. Please!`, "{Name}, we need your voice in the hymn.", `A priest! Blessings, kin.` };
			Respected = { `Priest and friend. The chapel is yours.`, "{Name}. Our brightest candle.", `Lead the blessing for us, kin.` };
		};
		Vampire = {
			Hostile = { `Vampire. The chapel's off limits.`, `Vampire. Garlic's in the soup. Fair warning.`, `Vampire. Step out of my candlelight.` };
			Wary = { `Vampire. Do the hymns bother you?`, `Vampire. Keep a polite distance.`, `Vampire. Why are you hovering by the door?` };
			Any = { `Vampire. You must know very old hymns.`, `Vampire. Do you mind the bells?`, `Vampire. Up late? So are we.` };
			Friendly = { `Vampire! There's room in the choir loft.`, "{Name}, you'd make a lovely bass.", `A gentle vampire. How lovely.` };
			Respected = { `A vampire, blessed by the Choir. Unheard of.`, "{Name}. Even the bells approve of you.", `Our vampire. We've moved the garlic.` };
		};
		Werewolf = {
			Hostile = { `Werewolf. The chapel has a no-shedding rule.`, `Werewolf. Go howl at the Den.`, `Werewolf. You're tracking leaves in. Out.` };
			Wary = { `Werewolf. Are you with the Pack?`, `Werewolf. Please don't growl during hymns.`, `Werewolf. Feeling restless?` };
			Any = { `Werewolf. Do bells hurt your ears?`, `Werewolf. Not all of you run with the Pack.`, `Werewolf. Lovely range on a howl, I bet.` };
			Friendly = { `A werewolf who sings! Wonderful!`, "{Name}, howl the low notes for us?", `Werewolf? You'd anchor the bass section.` };
			Respected = { `Werewolf, and our dearest friend.`, "{Name}. Proof the Pack is wrong.", `Our werewolf. Howls perfectly in tune.` };
		};
		Ghoul = {
			Hostile = { `Ghoul. Back to the graveyard, please.`, `Ghoul. You're chilling the whole pew.`, `Ghoul. Not in the nave. Out.` };
			Wary = { `Ghoul. Have you been blessed lately?`, `Ghoul. You're very still. It's unnerving.`, `Ghoul. Stay off the chapel steps.` };
			Any = { `Ghoul. Patient soul. Like a slow hymn.`, `Ghoul. Calm as a quiet evening.`, `Ghoul. Do you know the old evening hymns?` };
			Friendly = { `Ghoul! Sit with us. You're so calm.`, "{Name}, you'd be a steady baritone.", `Ghoul? There's a pew with your name.` };
			Respected = { `Our ghoul. Steady as the chapel bell.`, "{Name}. Calmest soul in the Choir.", `Ghoul and friend. Blessed twice.` };
		};
		Wraith = {
			Hostile = { `Wraith. Restless spirits belong outside.`, `Wraith. Stop floating through the pews.`, `Wraith. The candles go out when you pass.` };
			Wary = { `Wraith! Don't appear during a hymn!`, `Wraith. Are you... at peace?`, `Wraith. Please use the door.` };
			Any = { `Wraith. Shall we sing you a blessing?`, `Wraith. So quiet. Like a held note.`, `Wraith. The bells ring softer for you.` };
			Friendly = { `Wraith! Your echo would be lovely in here.`, "{Name}, haunt the choir loft with us?", `Wraith? Welcome. Doors optional.` };
			Respected = { `Our wraith. Guardian of the choir loft.`, "{Name}. Gentlest spirit in the halls.", `Blessed wraith. The candles lean to you.` };
		};
	};
	Hurt = {
		Hostile = { `Hurt? Do try to limp quietly.`, `Injured? The chapel isn't a clinic.`, `Hurt? I did warn you. Didn't I?` };
		Wary = { `You look hurt. Nurse is past the chapel.`, `Hurt? I'll light a candle. From here.`, `Sit. Carefully. Mind the pews.` };
		Any = { `Oh dear. Sit, sit. I'll fetch the nurse.`, `You're hurt! Someone, a blanket!`, `Rest. I'll hum something soothing.` };
		Friendly = { "{Name}! Sit. I'll pray AND fetch the nurse.", `Lean on me. Slowly. There we are.`, `Who did this? I'm very cross.` };
		Respected = { `Our friend is hurt! Fetch the nurse!`, "{Name}, rest in the pew. We'll keep watch.", `Bring water and the soft blanket. Now.` };
	};
	Outfit = {
		FullLook = {
			Hostile = { `Ivory and black won't save you.`, `Dressed for choir. Behaving otherwise.`, `The collar doesn't make the singer.` };
			Wary = { `Dressed like us. Now sing like us.`, `Ivory and black. Turning over a new leaf?`, `Hm. Very proper. Very suspicious.` };
			Any = { "{Clique}'s colours! How lovely.", `Ivory and black. Very chapel.`, `Pressed and proper. Practice-ready.` };
			Friendly = { `Now you look like you're in the Choir!`, "{Name}, in ivory! Front row for you.", `So proper! You look like a hymn sheet.` };
			Respected = { "{Clique}'s finest. Truly radiant.", `Our colours on you. A benediction.`, "{Name}, dressed for a solo. Perfect." };
		};
		RivalLook = {
			Hostile = { "{Rival} sent you? You smell like the woods.", `Forest green? In the chapel? Begone.`, `Pack green. The candles flinched.` };
			Wary = { `Forest green. Are you with the Den?`, "{Rival}'s colours. Explain yourself.", `You smell faintly of bonfire. Why?` };
			Any = { `Oh. Very... forest.`, `Forest green? Bold choice. Very bold.`, `Are those pine needles on you?` };
			Friendly = { "{Name}! Why do you smell like the Den?", `Let me fetch you something in ivory.`, `Forest green? We'll pray it washes out.` };
			Respected = { `Undercover in the Den? So brave.`, `Even in forest green, you're ours.`, `Spying on the Pack? Bless you.` };
		};
		Likes = {
			Hostile = { "The {Piece} is lovely. The attitude isn't.", "Nice {Piece}. Shame about the manners.", "The {Piece}? Did you borrow it?" };
			Any = { "The {Piece}! How blessed.", "Oh, the {Piece}. Practically glowing.", "The {Piece} catches the candlelight.", "With the {Piece}, you could sing with us." };
		};
		Mocks = {
			Hostile = { "The {Piece}? In the chapel? Truly?", "Keep that {Piece} out of the chapel.", "The {Piece}. I'll need more candles." };
			Friendly = { "The {Piece}? Oh, friend. No.", "Leave the {Piece} at the door?", "Let's bless the {Piece}. Or bin it." };
			Any = { "The {Piece}? That needs a blessing.", "The {Piece}? Bit grim, isn't it?", "Oh dear. The {Piece}.", "Did the {Piece} come with a curse?" };
		};
	};
	DressCode = {
		Hostile = { `Proper colours, or you wait outside.`, `Not dressed like that. Not in here.`, `Turn around. Try again in ivory.` };
		Wary = { `The chapel asks for proper dress.`, `Ivory and black, please. Then come in.`, `Come back dressed for practice.` };
		Any = { `Choir dress only past the doors.`, `Choir colours in the chapel, please.`, `No choir dress, no pews. Sorry.` };
		Friendly = { `Almost! Put on something ivory and come in.`, "{Name}, dress for choir and sit with us.", `I'd let you in. The candles wouldn't.` };
		Respected = { `Even our dearest wear the colours.`, `Lucien insists. Change, then come in.`, `Proper dress, then front row. Promise.` };
	};
	Fed = {
		Loved = { Any = { "{Snack}! Blessed, truly.", `Oh, how kind. A gift for the choir.`, "{Snack}? Heaven sent.", `Bless you. I mean it.` } };
		Liked = { Any = { "{Snack}? Thank you, kindly.", `Grace before eating. Thank you.`, `How generous of you.` } };
		Refuse = { Hostile = { `We'll pray for you. Keep it.`, `I can't accept that from you.`, `No. Not after what you've done.` }; Wary = { `I'm fasting, I'm afraid.`, `Perhaps another time.` } };
	};
}
