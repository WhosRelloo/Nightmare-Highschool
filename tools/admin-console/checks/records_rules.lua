local Mod = game.ReplicatedStorage:FindFirstChild("Functions") and game.ReplicatedStorage.Functions:FindFirstChild("StaffRecords")
if not Mod then return "FAIL Functions.StaffRecords missing" end
local R = require(Mod:Clone())
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end

-- the record shape and the cap of 50
local Rec = R.Normalize(nil)
for _, L in { "Notes", "Warnings", "Bans", "Mutes", "Reports" } do Eq(typeof(Rec[L]), "table", "blank has " .. L) end
local N2 = R.Normalize({ Warnings = { { At = 5; By = 1 }, "junk", { By = 2 } }; Notes = "junk" })
Eq(#N2.Warnings, 1, "normalize keeps only entries with At") Eq(#N2.Notes, 0, "normalize drops a list that isn't a table")
for I = 1, 51 do R.Push(Rec, "Warnings", { At = I; By = 1; Reason = "w" .. I }) end
Eq(#Rec.Warnings, 50, "cap 50") Eq(Rec.Warnings[1].At, 2, "oldest dropped first") Eq(Rec.Warnings[50].At, 51, "newest last")

-- a mute's end time and whether it is still on
Eq(R.MuteUntil(10, 1000), 1600, "10 min") Eq(R.MuteUntil(60, 1000), 4600, "1 h")
Eq(R.MuteUntil(1440, 1000), 87400, "1 day") Eq(R.MuteUntil(0, 1000), 0, "until unmuted")
Eq(R.MuteOn({ At = 1000; Until = 1600 }, 1599), true, "on before the end")
Eq(R.MuteOn({ At = 1000; Until = 1600 }, 1600), false, "off at the end")
Eq(R.MuteOn({ At = 1000; Until = 0 }, 1e9), true, "until unmuted stays on")
Eq(R.MuteOn({ At = 1000; Until = 0; Lifted = { By = 1; At = 1100 } }, 1200), false, "lifted is off")
local M = R.Blank()
R.Push(M, "Mutes", { At = 1; By = 1; Until = 0; Lifted = { By = 1; At = 2 } })
R.Push(M, "Mutes", { At = 3; By = 1; Until = 700 })
Eq(R.OpenMute(M, 500) and R.OpenMute(M, 500).At, 3, "open mute found")
Eq(R.OpenMute(M, 800), nil, "an ended mute is not open")
Eq(R.MuteLabel({ At = 0; Until = 600 }), "10 min", "label 10 min")
Eq(R.MuteLabel({ At = 0; Until = 86400 }), "1 day", "label 1 day")
Eq(R.MuteLabel({ At = 0; Until = 0 }), "Until unmuted", "label until unmuted")

-- the unban rule
Eq(R.UnbanLevel({ Days = 0 }), 3, "permanent needs 3")
Eq(R.UnbanLevel({ Days = 7 }), 1, "7 days needs 1") Eq(R.UnbanLevel({ Days = 30 }), 1, "30 days needs 1")
Eq(R.UnbanLevel({ Days = 90 }), 2, "over 30 days needs 2")
Eq(R.UnbanLevel(nil), 3, "no ban on record counts as permanent")
local B = R.Blank()
R.Push(B, "Bans", { At = 10; By = 1; Days = 0; Lifted = { By = 1; At = 20 } })
R.Push(B, "Bans", { At = 30; By = 2; Days = 7 })
Eq(R.OpenBan(B) and R.OpenBan(B).At, 30, "the latest unlifted ban")
B.Bans[2].Lifted = { By = 1; At = 40 }
Eq(R.OpenBan(B), nil, "no open ban when all are lifted")
Eq(R.BanOn({ At = 0; Days = 7 }, 6 * 86400), true, "a 7-day ban is on at day 6")
Eq(R.BanOn({ At = 0; Days = 7 }, 8 * 86400), false, "and ended at day 8")
Eq(R.BanOn({ At = 0; Days = 0 }, 1e9), true, "permanent stays on")
Eq(R.BanOn({ At = 0; Days = 0; Lifted = { By = 1; At = 5 } }, 10), false, "lifted is off")

-- find and remove by At + By, and the text an entry shows
local F = R.Blank()
R.Push(F, "Notes", { At = 5; By = 1; Text = "a" }) R.Push(F, "Notes", { At = 5; By = 2; Text = "b" })
Eq(R.Find(F, "Notes", 5, 2), 2, "find by At and By")
local Gone = R.Remove(F, "Notes", 5, 2)
Eq(Gone and Gone.Text, "b", "remove returns the entry") Eq(#F.Notes, 1, "one left")
Eq(R.Remove(F, "Notes", 9, 9), nil, "a missing entry")
Eq(R.EntryText("Bans", { Days = 7; Reason = "spam" }), "7-day ban: spam", "ban text")
Eq(R.EntryText("Bans", { Days = 0 }), "Permanent ban", "permanent ban text")
Eq(R.EntryText("Mutes", { At = 0; Until = 3600; Reason = "caps" }), "Muted (1 h): caps", "mute text")
Eq(R.EntryText("Warnings", { Reason = "" }), "Warned", "empty warning text")
Eq(R.EntryText("Notes", { Text = "hi" }), "hi", "note text")

-- the summary line and the timeline
local S = R.Blank()
R.Push(S, "Warnings", { At = 1; By = 1; Reason = "a" }) R.Push(S, "Warnings", { At = 2; By = 1; Reason = "b" })
R.Push(S, "Warnings", { At = 3; By = 1; Reason = "c" })
R.Push(S, "Bans", { At = 4; By = 1; Days = 7; Lifted = { By = 1; At = 5 } })
R.Push(S, "Mutes", { At = 6; By = 1; Until = 1000 })
Eq(R.Summary(S, 10, function(T) return "@" .. T end), "3 warnings · 1 ban (lifted) · muted until @1000", "summary")
Eq(R.Summary(R.Blank(), 10), "No history", "empty summary")
local OnBan = R.Blank()
R.Push(OnBan, "Bans", { At = 0; By = 1; Days = 0 })
Eq(R.Summary(OnBan, 10), "1 ban (active)", "active ban summary")
local TL = R.Timeline(S)
Eq(#TL, 5, "timeline has every entry") Eq(TL[1].Kind, "Mute", "newest first") Eq(TL[5].Entry.Reason, "a", "oldest last")

-- log keys, the Test cutoff (day n-7), the entry shape, the cap of 2000
Eq(R.Day(86400 * 3 + 5), 3, "day number")
Eq(R.LogKey(3, "job"), "day_3_job", "log key") Eq(R.LogKey(3, "job", true), "test_day_3_job", "test log key")
Eq(R.IndexKey(3), "day_3", "index key") Eq(R.IndexKey(3, true), "test_day_3", "test index key")
Eq(R.TestCutoff(20), 13, "test cutoff n-7")
local E = R.LogEntry({ At = 9; Staff = "mod"; StaffId = 1; Action = "Warn"; Target = "kid"; TargetId = 2; Detail = string.rep("x", 200); Side = "Weird"; Ok = 1 })
Eq(#E.Detail, 120, "detail cut to 120") Eq(E.Side, "Moderate", "an unknown side is Moderate") Eq(E.Ok, false, "Ok must be true")
Eq(E.TargetId, 2, "target id kept") Eq(E.StaffId, 1, "staff id kept")
Eq(R.LogEntry({ Side = "Test"; Ok = true }).Side, "Test", "the Test side kept")
local Big = {}
for I = 1, 2005 do Big[I] = { At = I } end
local Capped = R.CapLog(Big)
Eq(#Capped, 2000, "log cap 2000") Eq(Capped[1].At, 6, "the oldest log entries dropped") Eq(Capped[2000].At, 2005, "the newest kept")
local Merged = R.MergeDay({ { { At = 1; Action = "a" }, { At = 3; Action = "c" } }, { { At = 2; Action = "b" }, { At = 3; Action = "d" } } })
Eq(Merged[1].Action, "d", "merge: newest first, the later list wins a tie") Eq(Merged[2].Action, "c", "then c") Eq(Merged[4].Action, "a", "oldest last")

-- filter and pages
local Row = { Staff = "Mod"; Target = "Kid"; TargetId = 123; Action = "Warn"; Side = "Moderate"; Ok = false }
Eq(R.LogMatch(Row, "", "All"), true, "all") Eq(R.LogMatch(Row, "mod", "All"), true, "staff name")
Eq(R.LogMatch(Row, "12", "All"), true, "target UserId") Eq(R.LogMatch(Row, "warn", "Refused"), true, "refused chip")
Eq(R.LogMatch(Row, "", "Test"), false, "test chip") Eq(R.LogMatch(Row, "", "Moderate"), true, "moderate chip")
Eq(R.LogMatch(Row, "zzz", "All"), false, "no match")
local Rows = {}
for I = 1, 120 do Rows[I] = I end
local Pg, P, Ps = R.Page(Rows, 3, 50)
Eq(#Pg, 20, "the last page has 20") Eq(P, 3, "page 3") Eq(Ps, 3, "3 pages")
Eq(select(2, R.Page(Rows, 9, 50)), 3, "page clamped") Eq(select(3, R.Page({}, 1, 50)), 1, "an empty day has one page")

-- prefs drop unknown ids
local Fv = R.CleanFavs({ "Warn", 5, "Gone", "Warn", string.rep("x", 41) }, { Warn = true; Goto = true })
Eq(#Fv, 1, "unknown, repeated and bad ids dropped") Eq(Fv[1], "Warn", "a known id kept")
Eq(#R.CleanFavs({ "A", "B" }, nil), 2, "no known set keeps strings") Eq(#R.CleanFavs("junk", nil), 0, "not a list")
Eq(R.CleanSide("Test"), "Test", "side kept") Eq(R.CleanSide("Nope"), nil, "bad side dropped")

if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS records_rules"
