# the face strips without seams, and drawn under see-through accessories (UI.Appearance).
# Usage: python port4/patch_face.py <in.luau> <out.luau>
import io, sys


class M:
    def __init__(self, s): self.s = s

    def rep(self, a, b):
        assert self.s.count(a) == 1, ('count', self.s.count(a), a[:90])
        self.s = self.s.replace(a, b)


m = M(io.open(sys.argv[1], encoding='utf-8', newline='').read())
m.rep('''local FACE_STRIPS = 12    -- strips around the curve (each spans ~8 degrees: no visible facets)
local FACE_LIFT = 0.006   -- studs off the skin (just enough to never z-fight)''',
'''local FACE_STRIPS = 12    -- strips around the curve (each spans ~8 degrees: no visible facets)
local FACE_LIFT = 0.006   -- studs off the skin (just enough to never z-fight)
-- (1.99.0) the seams (the owner's "little slit" across the eyes and brows): Roblox draws a SurfaceGui's canvas onto its
-- part with a light, half-see-through fringe along the canvas's edges. The strips' canvases ended exactly where the art
-- did, so every joint between two strips drew that fringe across the eyes and brows (12 thin vertical lines; 1024 / 12 =
-- 85.33 also put the joints between texels). Now each strip draws its own slice of the art on whole texels, one canvas
-- pixel per texel, inside a canvas FACE_MARGIN texels wider on each side; the margins hold no art, so the fringe falls
-- on nothing, and the neighbouring strips overlap there. The art itself reaches FACE_OVERLAP texel into the next strip's
-- slice, so no hairline can open between the two.
local FACE_MARGIN = 3     -- transparent texels round each strip's art (its canvas edges)
local FACE_OVERLAP = 1    -- texels of art each strip shares with the next one (on its right)
-- (1.99.0) faces over see-through accessories: Roblox draws the face's SurfaceGuis and alpha-blended pieces (the
-- mourning and fascinator veils, the lace mask) in one transparent pass sorted by each part's distance, so a thin strip
-- on the skin sorted nearer than a veil in front of it and the face was drawn over the veil. Each strip is now as deep as
-- the head (its Front face, where the face is drawn, stays on the skin), so it sorts from the head's middle and anything
-- worn in front of the face is drawn after it. Opaque pieces were never affected (the depth test hides the face).
local FACE_VERSION = 7    -- strips built by this layout (an older face plate is rebuilt)''')
m.rep('''	if shell and shell:IsA("Folder") and math.abs((shell:GetAttribute("W") or 0) - W) < 1e-4
		and math.abs((shell:GetAttribute("R") or 0) - R) < 1e-4 then''',
'''	if shell and shell:IsA("Folder") and math.abs((shell:GetAttribute("W") or 0) - W) < 1e-4
		and math.abs((shell:GetAttribute("R") or 0) - R) < 1e-4 and shell:GetAttribute("V") == FACE_VERSION then''')
m.rep('''	shell:SetAttribute("W", W)
	shell:SetAttribute("R", R)
	local r = R + FACE_LIFT
	local span = W / R
	local step = span / FACE_STRIPS
	local chord = 2 * r * math.sin(step / 2)
	local inset = r * math.cos(step / 2) -- each flat strip is a chord: its edges touch radius r, never poke past it
	for i = 0, FACE_STRIPS - 1 do
		local theta = ((i + 0.5) / FACE_STRIPS - 0.5) * span -- image left (u = 0) sits on the head's +X side
		local p = Instance.new("Part")
		p.Name = "Strip" .. (i + 1)
		p.Transparency = 1
		p.CanCollide, p.CanQuery, p.CanTouch, p.Massless = false, false, false, true
		p.CastShadow = false
		p.Size = Vector3.new(chord, W, 0.01)
		p.CFrame = head.CFrame * CFrame.Angles(0, theta, 0) * CFrame.new(0, 0, -inset)
		local w = Instance.new("WeldConstraint")
		w.Part0, w.Part1 = head, p
		w.Parent = p
		local sg = Instance.new("SurfaceGui")
		sg.Name = FACE_GUI
		sg.Face = Enum.NormalId.Front
		sg.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		sg.PixelsPerStud = 1024 / W
		sg.LightInfluence = 1
		sg.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
		sg:SetAttribute("Slice", i)
		sg.Parent = p
		p.Parent = shell
	end''',
'''	shell:SetAttribute("W", W)
	shell:SetAttribute("R", R)
	shell:SetAttribute("V", FACE_VERSION)
	local r = R + FACE_LIFT
	local span = W / R
	local function angleAt(u) -- the angle round the head of texel column u (image left, u = 0, on the head's +X side)
		return (u / 1024 - 0.5) * span
	end
	for i = 0, FACE_STRIPS - 1 do
		-- the art this strip draws (its slice on whole texels, a texel into the next one) and its canvas (the art plus
		-- a transparent margin each side)
		local u0, u1 = math.round(i * 1024 / FACE_STRIPS), math.round((i + 1) * 1024 / FACE_STRIPS)
		if i < FACE_STRIPS - 1 then u1 += FACE_OVERLAP end
		local c0, c1 = u0 - FACE_MARGIN, u1 + FACE_MARGIN
		local a0, a1 = angleAt(c0), angleAt(c1)
		local half = (a1 - a0) / 2
		local chord = 2 * r * math.sin(half)
		local inset = r * math.cos(half) -- each flat strip is a chord: its edges touch radius r, never poke past it
		local perStud = (c1 - c0) / chord -- canvas pixels (texels) per stud
		local depth = 2 * R -- the head's depth: the strip's centre sits at the head's middle (see FACE_VERSION)
		local p = Instance.new("Part")
		p.Name = "Strip" .. (i + 1)
		p.Transparency = 1
		p.CanCollide, p.CanQuery, p.CanTouch, p.Massless = false, false, false, true
		p.CastShadow = false
		p.Size = Vector3.new(chord, W, depth)
		-- the Front (-Z) face, where the face is drawn, stays where the 0.01-thick strip's was: at the chord, 0.005 out
		p.CFrame = head.CFrame * CFrame.Angles(0, (a0 + a1) / 2, 0) * CFrame.new(0, 0, -inset - 0.005 + depth / 2)
		local w = Instance.new("WeldConstraint")
		w.Part0, w.Part1 = head, p
		w.Parent = p
		local sg = Instance.new("SurfaceGui")
		sg.Name = FACE_GUI
		sg.Face = Enum.NormalId.Front
		sg.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		sg.PixelsPerStud = perStud
		sg.LightInfluence = 1
		sg.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
		sg:SetAttribute("Slice", i)
		sg:SetAttribute("Art0", u0)
		sg:SetAttribute("Art1", u1)
		sg:SetAttribute("Canvas0", c0)
		sg:SetAttribute("Canvas1", c1)
		sg.Parent = p
		p.Parent = shell
	end''')
m.rep('''		local slice = 1024 / FACE_STRIPS
		for _, sg in ipairs(shell:GetDescendants()) do
			if sg:IsA("SurfaceGui") then
				sg:ClearAllChildren()
				local i = sg:GetAttribute("Slice") or 0''',
'''		local slice = 1024 / FACE_STRIPS
		for _, sg in ipairs(shell:GetDescendants()) do
			if sg:IsA("SurfaceGui") then
				sg:ClearAllChildren()
				local i = sg:GetAttribute("Slice") or 0
				-- this strip's art and canvas, in texels (see FACE_MARGIN)
				local art0 = sg:GetAttribute("Art0") or i * slice
				local art1 = sg:GetAttribute("Art1") or (i + 1) * slice
				local can0 = sg:GetAttribute("Canvas0") or art0
				local can1 = sg:GetAttribute("Canvas1") or art1
				local canW = math.max(1, can1 - can0)''')
m.rep('''					im.BackgroundTransparency = 1
					im.Size = UDim2.fromScale(1, 1)''',
'''					im.BackgroundTransparency = 1
					im.Size = UDim2.fromScale((art1 - art0) / canW, 1) -- one texel per canvas pixel
					im.Position = UDim2.fromScale((art0 - can0) / canW, 0) -- inside the transparent margins''')
m.rep('''					im.ImageRectOffset = Vector2.new(i * slice, 0)
					im.ImageRectSize = Vector2.new(slice, 1024)''',
'''					im.ImageRectOffset = Vector2.new(art0, 0)
					im.ImageRectSize = Vector2.new(art1 - art0, 1024)''')
io.open(sys.argv[2], 'w', encoding='utf-8', newline='').write(m.s)
print('ok', sys.argv[2])
