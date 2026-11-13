# (1.99.0) masks keep their eye holes on the eyes at any hair fit: NHHairScale = "Radial" (UI.AccessoryWear)
# Usage: python port5/patch_wear.py <in.luau> <out.luau>
import io, sys


class M:
    def __init__(self, s): self.s = s

    def rep(self, a, b):
        assert self.s.count(a) == 1, ('count', self.s.count(a), a[:90])
        self.s = self.s.replace(a, b)


m = M(io.open(sys.argv[1], encoding='utf-8', newline='').read())
m.rep('''              still worn, at the "*" fit, and the hair isn't tucked round it (it may pass through). "*" = any other hair.''',
'''              still worn, at the "*" fit, and the hair isn't tucked round it (it may pass through). "*" = any other hair.
	  NHHairScale "Radial" on the face masks (1.99.0): a hair fit k scales the mask out round the head's vertical axis
	              (across and front-to-back, not up or down), the way acc_hairfit.py measures masks, so the eye holes
	              stay on the painted eyes whatever hair is worn. Scaled about the headband (NHSeat), a mask at k 1.11
	              (the "*" fit) slid 0.06 studs down the face.''')
m.rep('''	if MountKey == `Head` and (HK ~= 1 or HZ ~= 0) then -- the hair fit: scale about the headband centre, then lift
		local Piv = Vector3.new(0, Seat, 0)
		Pos = Piv + (Pos - Piv) * HK + Vector3.new(0, HZ, 0)
	end
	local Off = CFrame.new(Pos.X * K, Pos.Y * K, Pos.Z * K * D) * Fit.Rotation
	local P = Tpl:Clone()
	K *= HK
	P.Size = Vector3.new(P.Size.X * K, P.Size.Y * K, P.Size.Z * K * D)''',
'''	local Radial = MountKey == `Head` and Tpl:GetAttribute(`NHHairScale`) == `Radial` -- a mask (see NHHairScale)
	if Radial and (HK ~= 1 or HZ ~= 0) then -- the hair fit: out round the head's axis, the eye holes kept level
		Pos = Vector3.new(Pos.X * HK, Pos.Y + HZ, Pos.Z * HK)
	elseif MountKey == `Head` and (HK ~= 1 or HZ ~= 0) then -- the hair fit: scale about the headband centre, then lift
		local Piv = Vector3.new(0, Seat, 0)
		Pos = Piv + (Pos - Piv) * HK + Vector3.new(0, HZ, 0)
	end
	local Off = CFrame.new(Pos.X * K, Pos.Y * K, Pos.Z * K * D) * Fit.Rotation
	local P = Tpl:Clone()
	local KY = K -- a radial fit leaves the height alone
	K *= HK
	if not Radial then KY = K end
	P.Size = Vector3.new(P.Size.X * K, P.Size.Y * KY, P.Size.Z * K * D)''')
m.rep('''	local Scale = function(V: Vector3) return Vector3.new(V.X * K, V.Y * K, V.Z * K * D) end''',
      '''	local Scale = function(V: Vector3) return Vector3.new(V.X * K, V.Y * KY, V.Z * K * D) end''')
io.open(sys.argv[2], 'w', encoding='utf-8', newline='').write(m.s)
print('ok', sys.argv[2])
