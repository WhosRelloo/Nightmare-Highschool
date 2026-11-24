local N = game for _, S in {"ServerScriptService", "Services", "School", "SchoolClock"} do N = N and N:FindFirstChild(S) end
if not N then return "MISSING" end
local S = N.Source local a = 1 local b = math.min(a + 8000, #S + 1)
while b <= #S and (S:byte(b) >= 128 and S:byte(b) < 192) do b += 1 end
return game:GetService("HttpService"):JSONEncode({ S = S:sub(a, b - 1), B = b })