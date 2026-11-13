# (2.0.0) a line's attitude goes with it to the clients (NHSayMood), for the talking face (Controllers.Character.FaceTalk)
import io, sys
s = io.open(sys.argv[1], encoding='utf-8', newline='').read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:70]); s = s.replace(a, b)
rep('''local function bubble(S, Text: string)
	S.SaidAt = os.clock()
	S.Model:SetAttribute(`NHSay`, Text)''', '''local function bubble(S, Text: string, Mood: string?)
	S.SaidAt = os.clock()
	-- (2.0.0) the line's attitude (Hostile, Wary, Respected...): the clients' talking face takes its expression from it
	-- (Controllers.Character.FaceTalk); nil = from the student's mood or the words
	S.Model:SetAttribute(`NHSayMood`, Mood)
	S.Model:SetAttribute(`NHSay`, Text)''')
rep('''	local Ok, Text = pcall(Talk.Pick, S, Moment, Pl, O)
	if Ok and Text then
		bubble(S, Text)''', '''	local Ok, Text = pcall(Talk.Pick, S, Moment, Pl, O)
	if Ok and Text then
		bubble(S, Text, O.Attitude)''')
io.open(sys.argv[2], 'w', encoding='utf-8', newline='').write(s)
print('ok')
