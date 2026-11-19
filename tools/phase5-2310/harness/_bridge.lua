local H = game:GetService("HttpService")
local P = game.Players:GetPlayers()[1]
local ok, r = game.ServerStorage.NHTestBridge:Invoke("RecognitionTest")
local okj, j = pcall(H.JSONEncode, H, { ok = ok; result = r })
return okj and j or tostring(r)