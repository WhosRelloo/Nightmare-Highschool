# Delinquents clique audit (Bruno Vance / Back Lot / rival Ordinary)

Read-only audit, studio "NH Combat Test" (d4d1c2a6-...). Live modules read in full: Social.Cliques, CliqueFights,
CliquePranks, CliqueShowdowns, CliqueMembership, CliqueEvents, Config.Cliques, Features.Delinquents, School.HallMonitor,
plus Discipline (AddViolation / ReportIncident, L150-228), Quests.Quests (Matches / Progress, L560-610) and the
Delinquents entries of Config.Quests (L435-458, L605-637, L805-815, L970-1005).

Note on sources: partway through, the studio switched into a Play session (the grep began returning
Players.WhosRello.PlayerScripts..., and ServerScriptService was no longer visible). I did not start Play and did not stop
it. Three supporting reads therefore came from repo snapshots (E:\Nightmare-Highschool\Studio\...), not from live code:
Quests.Duels (champion ring = CombatAllowed), Social.Reputation (Get/Sync/AwardTitle), Player.Data
(GetProfile returns Profile.Data). Each finding says which source it relies on.

## Findings

### F1. A responding hall monitor that sees a helper ends the scuffle as "Monitor" without arriving. HIGH, CONFIRMED
- CliqueFights L404-411: 4 s into a scuffle on school grounds, `HM.Respond(Venue, function() ... Local.EndScuffle(Ev, "Monitor") end)`.
- HallMonitor L412-441 (OnDamage): any player hit, seen by *any* active monitor. If Distance > RecognizeRange and
  `M.State ~= "Chase"`, it calls `Local.StartChase(M, Player, "Fighting")`. That includes the monitor in the `Respond` state.
- HallMonitor L206-213 (SetState): `if M.State == "Respond" and State ~= "Respond" and M.RespondDone then ... task.defer(Done)`.
- Scenario: Delinquents vs Ordinary scuffle at the Commons (Regions.Commons Kind = School, so OnSchoolGrounds is true)
  during Break, Lunch or AfterSchool. The player is doing JobDelinquents1 or DareDelinquents2 and punches an Ordinary
  fighter. The monitor walking over sees the hit from more than RecognizeRange away, so it switches to Chase. SetState
  then defers RespondDone, and EndScuffle(Ev, "Monitor") runs with Winner = nil. Result: no HelpWin (+10), no
  `Quests.Progress(P, "Scuffle", ...)` and no turf win. On top of that, the monitor chases the helper and books
  Fighting on a catch.

### F2. Fighting violations for clique fights the game asks you to take part in. HIGH, CONFIRMED
- HallMonitor.OnDamage (L412-441) has no exemption for clique fighters (`NHCliqueFighter` is set at CliqueFights L206
  and nothing reads it), scuffles, rumbles, turf confrontations or prank stops. The only exemption is a `CombatAllowed`
  zone (L421, L144-155).
- Only showdowns add a CombatAllowed zone (CliqueShowdowns L195-215). Bruno's ring champion (CliqueDelinquents2) is also
  covered (repo snapshot of Duels, L7: the ring is tagged CombatAllowed).
- Scenarios:
  - (a) Rumble day: everyone gets the text "Pick a side" (CliqueEvents L93). The rumble is held at the Commons during
    AfterSchool, which is a DutyKind (Config.Discipline L62). At 60 s, CliqueFights L780-790 sends a monitor *to the venue*.
    The monitor arrives, says "Break it up", and goes back to Patrol (HallMonitor L314-323), but the rumble continues.
    Every hit a helper lands within RecognizeRange becomes a recognised Fighting violation (L431-436 -> Discipline L223-224).
  - (b) Scuffle at the Commons while doing JobDelinquents1 or DareDelinquents2 (see F1).
  - (c) Guard Duty (JobDelinquents3) asks you to put the Ordinary prankster down. That hit is booked if a monitor can
    see it (whether a patrol route sees the Back Lot needs a runtime check: PLAUSIBLE for (c)).
  - (d) A turf confrontation started at the Commons (F4), when you fight back.

### F3. The hostile PVE "Delinquent" crews count as Delinquents members: defending yourself costs Delinquents standing, and backup fights its own clique. MED, CONFIRMED (code path)
- Features.Delinquents L42-46, L145: the crews are named `Delinquent` / `Delinquent Brute` / `Gang Leader`, with AggroRange 26.
  They "pick fights", and the header says they are beatable by a new student and pay EXP/Yen.
- Config.Cliques L109: `[Delinquent] = Delinquents; [Delinquent Brute] = Delinquents`. Social.Cliques L211-215 and
  L330-336 tag them with `Clique = Delinquents` when they appear in Live.
- Social.Cliques L368-377: downing one gives `Add(P, Delinquents, -8)` (and +2 Ordinary through RivalShare). There is no check
  for who started the fight.
- Consequences:
  - A new student grinding these crews (the intended PVE loop) drops toward Hostile with the Delinquents: 7 downs from 0
    reach -56. That starts Back Lot confrontations (CliqueFights L327-357) and Bruno's daily Foe challenge
    (CliqueShowdowns L403-409). Ignoring the challenge then sets NoShow and NHGrudge (L418-424).
  - A Delinquents *member* or Respected player who defends against a crew loses 8 per down. One down at 60-67 drops them
    below Respected, so `CliqueReward_Delinquents` clears (Cliques L113-115) and the 25% Boards perk is lost
    (Config.Cliques L439-447).
  - CliqueFights.Backup L608-611: `local Mine = Fighters[Attacker]` only recognises event fighters. For a PVE Delinquent
    attacker `Mine` is nil, so a Delinquents member (NHClique, L614: backup anywhere) or reward holder gets two
    "Back Lot Tough" Delinquents spawned to fight the Delinquent crew. The member's crew (CliqueMembership L285-286) also
    turns on them. Fix: compare against `Attacker:GetAttribute("Clique") == Id`.
  - `Gang Leader` is not in Config.Cliques.Npcs, so downing one changes nothing (LOW, inconsistent with the doc's
    "Downing a Delinquent gives The Ordinary +2").
- PLAUSIBLE part: whether the AI targets Delinquents members/allies (AI targeting was not read). The standing loss
  applies whenever they fight.

### F4. Delinquents members are jumped at the Commons at any hour, including during a rumble, on school grounds. MED, CONFIRMED
- CliqueFights L341-342: `if Mine and Config.Defs[Id].Rival == Mine then Hostile = true`. Ordinary's rival is Delinquents,
  so a Delinquents member who lingers 8 s at the Commons is confronted by 2 Ordinary fighters, every 120 s.
- TurfStep (L327-357) has no school-segment check (Class included) and no check for a live scuffle or rumble. The Commons is
  also the rumble venue (Config.Cliques Events.RumbleVenue = Ordinary, L418) and a School region. A member who joins a
  Delinquents vs Ordinary rumble therefore also gets a private turf confrontation, and fighting back is booked (F2).

### F5. Winning Bruno's showdown can lower your Delinquents standing. LOW-MED, CONFIRMED
- The showdown leader and ring are spawned with `Clique = Delinquents` (CliqueShowdowns L177; ring via SpawnFighter, CliqueFights L205).
  Downing them triggers Social.Cliques L368-377: -8 each.
- On a win, CliqueShowdowns L310-311 only tops up `if Cur < 60`.
- Scenario (Friend path; needs >= 20, Q2 done): at 72, the player downs Bruno (-8 -> 64) plus one joined backup (-8 -> 56).
  The win then tops up to 60, so the player ends 12 lower than they started. At 80 with only Bruno downed, they end at 72.
  The win also gives the Ordinary +2 per down.

### F6. The showdown is won whenever the leader is "Out", no matter who did it. MED, CONFIRMED (third party) / PLAUSIBLE (grip/despawn)
- CliqueShowdowns L269: `if F.Out(Ev.Leader) then Local.End(Ev, "Won")`. CliqueFights.Out (L135-140) is true for no
  parent, health <= 0, Downed, **Carried or Gripped**.
- A second player can beat Bruno for you. Nothing restricts damage to Ev.Player, and Backup/Crew are only suppressed for
  the challenger (NHShowdown). Any despawn of the leader model also counts as a win. Whether a standing NPC can be
  Gripped or Carried depends on the combat code (not read).

### F7. Guard Duty (JobDelinquents3) sends its prank only once and does not wait for the player. MED, CONFIRMED
- CliqueMembership L297-302 -> CliquePranks.GuardDuty L659-670: 30 s after the job starts it calls
  `NpcPrank(Ordinary, Delinquents)` and returns after the first success. It never checks whether the player is near the Back Lot.
- NpcPrank finishes in PrankTime (6 s) after the walk (L489-521). If the player isn't there, the prank lands and the job's
  guaranteed prank is spent. After that, only random PrankTick picks can complete it: 1 of 8 ordered pairs, every 360 s,
  only in Break/Lunch/AfterSchool/Evening, and only when a player is within 120 studs (L539-557).
- GuardDuty also gives up after 20 tries x 15 s if both Back Lot spots already hold a mess (FreeSpot L156-165). Messes
  stay until cleaned or 6 AM, so the job can be dead for the day.

### F8. Commons scuffles rarely produce a winner during duty segments. MED, PLAUSIBLE (timing)
- Respond is sent 4 s in (CliqueFights L405) at ChaseSpeed, from up to 260 studs. A 2v2/3v3 between 75-HP fighters
  (L183, L213-215) likely outlasts the walk, so the scuffle ends as "Monitor" with no winner. Only Back Lot scuffles
  (Regions.BackLot Kind = Turf, so no Respond) and Evening scuffles reliably pay `Scuffle` progress.
  JobDelinquents1 needs 2 wins in one day.
- Related LOW: Local.Wanted (L650-664) only speeds up scuffles for a leader's *quest 2* whose first objective is
  Scuffle. Delinquents Q2 is `Defeat RingChampion` (Config.Quests L455-457), so JobDelinquents1 and DareDelinquents2 get no
  speed-up.

### F9. Downs are paid after a scuffle or rumble has ended. LOW, CONFIRMED
- OnHit checks `Scuffle == Ev` / `Rumble == Ev` (L492), but OnDowned (L503-517) only checks `Info.Leaving`.
- EndScuffle delays Leave by 1.5 s (0.4 s for Monitor) (L478-480), and EndRumble by 1.2 s (L927-929). A fighter downed in
  that window still pays HelpDown (+6) with no live event.

### F10. Clique standing is written to the profile outside UpdateState. LOW, CONFIRMED (code) / PLAUSIBLE (impact)
- Social.Cliques L41-47: `Social.Cliques = Config.Sanitize(Social.Cliques)` replaces the table on *every* Get.
  L66-89 (Add) mutates it, but never calls Reputation.Sync or `Data.UpdateState`.
- Repo snapshot of Player.Data: GetProfile returns `Profile.Data`, so the value still saves through ProfileService. The
  PlayerData state the client holds (Packets.SetState / SetSocial) goes stale until something else calls Rep.Sync, such as
  Showdowns/Membership Save or AwardTitle. Any client UI that reads PlayerData.Social.Cliques instead of NHCliques.Get
  shows old standing. This breaks the house rule that writes go through PlayerData.UpdateState.

### F11. Smaller issues (LOW)
- Prank-triggered confront ignores duel and showdown state: CliquePranks L626-628 calls `F.Confront(P, Victim, -80)`
  without the Dueling/NHShowdown/Protected checks that TurfStep applies (CliqueFights L333-334).
- Mess cleaning can be farmed between two players: Local.Clean (CliquePranks L299-308) pays +3 to anyone except the mess's
  ByPlayer. Two players with kits can trade pranks and cleans; each prank costs the pranker -15 with the victims.
- Crew not dismissed while Slot is nil: CliqueMembership L385 skips CrewStep when `Slot == nil`, so a crew spawned
  earlier is never dismissed if the player goes back to the menu and Slot clears. PLAUSIBLE: depends on whether the menu
  clears Slot.
- `Local.TestAs[P]` (CliqueMembership L400-404) is never cleared on PlayerRemoving (Studio-test path only).
- Lieutenant bonus is checked after quest rewards: CliqueMembership L304 checks Rank after the job's own +6 has been
  added. A player at 84-89 who crosses 90 on completion gets the 1.5x bonus on that same job.

### Remotes checked (no client-trust issues found)
- NHCliques.Get (RF, Cliques L320-324): no input, rate-limited, read-only.
- NHCliques.Leave (RF, CliqueMembership L364-373): no input; two presses within 6 s.
- NHCliques.Today (RF, CliqueEvents L181-189): no input, read-only.
- NHCliques.Changed / Say (RE): server-to-client only; there is no OnServerEvent anywhere in these modules.
- Prank, Keep watch, Clean and Scrub are server-side ProximityPrompts. PlayerPrank re-checks the distance (<= 10), the kit
  and the reserved/messed spot (CliquePranks L579-602).
- Boards discount: PriceFactor is computed server-side in Skateboard (repo snapshot L247-248) from server-set player
  attributes. That is fine.

### Leaks checked
- Player-keyed tables are cleared on PlayerRemoving: CliqueFights Cooldown/Linger/Backups (L1010; Confronts clears
  itself in its loop L305), Membership Crews/CrewDown/LeaveAsk/LastCall, Events LastCall, Cliques Last, HallMonitor
  Caught/LastFightReport, Showdowns Pending (never filled).
- Fighter, Greeted and Said tables are model-keyed and pruned.
- Only TestAs (F11) leaks.

## Hook points for a "delinquent reputation" expansion
- Signals:
  - Features.Downed.OnDowned / OnDamage (used by Cliques, CliqueFights, CliqueMembership, HallMonitor).
  - AI.NPCDefeated (Features.Delinquents L195).
  - Quests.Started / Completed (CliqueMembership L357-359).
  - HallMonitor.Escaped / Caught, and HallMonitor.CatchFilter (a settable function, as the Vigil pass uses).
  - Discipline.ViolationAdded / LevelChanged / DetentionServed.
  - Reputation.Changed / RelationshipChanged.
  - Duels.Won / ChampionDefeated / ChampionWon.
  - Gap: Social.Cliques.Add fires no server signal. Add one, e.g. `Cliques.StandingChanged(P, Id, Old, New, Reason)`.
- Event callbacks: CliqueFights.SpawnFighter Event tables with `Kind` plus `OnHit` / `OnDowned` (CliqueFights L491, L508;
  CliquePranks L465-481).
- Player attributes: `CliqueTier_Delinquents`, `CliqueReward_Delinquents`, `NHClique`, `NHCliqueRank`,
  `NHGrudge_Delinquents`, `NHKing`, `NHShowdown`, `Dueling`, `Perk_Unseen`, `DisciplineLevel`.
- NPC attributes: `Clique`, `NHCliqueFighter` (event kind), `NHCrewOf`, `NHShowdownLeader`, `QuestTarget`,
  `NHDelinquent` (PVE role), `Role`.
- Workspace attributes: `NHScuffleAt`, `NHRumble`, `NHTurfHolder_Delinquents`, `NHTurf_BackLot`.
- Mess attributes: `Victim`, `By`, `ByPlayer`, `Kind`. Desk attributes: `NHDeskTag`, `NHDeskBy`.
- Config.Cliques:
  - Defs.Delinquents: Tier, LeaderTier, Fighter, Reactions, Lines, Quests, Titles, Perk (`Boards`, 0.25), SignatureLook,
    Slogan, Challenge/Call/Beaten/Gloat/Crown, Joined/Betrayed/Greet, Taste.
  - Standing (DownedMember, RivalShare), Npcs (the name -> clique map), Fights, Events, Showdown, Membership.
  - PriceFactor(Player, Shop), Tier(), EventDay().
- Config.Quests: entries with `Rewards.Cliques`, `Requires.Clique`, `Job`, `Dare`, `Showdown`. Objective types handled
  in Quests.Local.Matches (Quests.Quests L560-590).
- Saved data (PlayerData profile via Social.Reputation.Get):
  - `Social.Cliques`
  - `Social.Showdowns` {Won, Tried, Challenged, NoShow, FoeQuest, King}
  - `Social.Membership` {Id, Since, Betrayed}
  - Persist through `Reputation.Sync` -> `UpdateState SetSocial`.
- Read APIs: CliqueFights.State() / Turf() / Rumble() / Feuds(), CliquePranks.State(), CliqueShowdowns.Summary(),
  CliqueMembership.Summary(), CliqueEvents.Today().
- Remotes folder ReplicatedStorage.NHCliques: Get, Changed, Say, Leave, Today. A new RF or RE fits here.
