-- Builds ServerStorage.NHHomes.Dorm from the dorm kit (props batch 34). Old stand-in -> ServerStorage.NH_Backup.
local SS=game.ServerStorage
local P=SS.NHProps
local Homes=SS.NHHomes
local Old=Homes:FindFirstChild("Dorm")
local Bk=SS:FindFirstChild("NH_Backup") or Instance.new("Folder",SS) Bk.Name="NH_Backup"
if Old and Old:GetAttribute("NHStandIn") then
  local prev=Bk:FindFirstChild("NHHomes_DormStandIn") if prev then prev:Destroy() end
  Old.Name="NHHomes_DormStandIn" Old.Parent=Bk
elseif Old then Old:Destroy() end

local M=Instance.new("Model") M.Name="Dorm"
M:SetAttribute("NHDormKit","batch34")
local F=-0.1                     -- floor top (Spawn sits on it)
local function R(d) return CFrame.Angles(0,math.rad(d),0) end
local function put(tpl,cf,name,state,parent)
  local c=P[tpl]:Clone()
  c:SetAttribute("NHBuildKit",nil)
  c.Name=name or tpl
  c:PivotTo(cf)
  if state then c:SetAttribute("NHHomeState",state) end
  c.Parent=parent or M
  return c
end
local Shell=Instance.new("Model") Shell.Name="Shell" Shell.Parent=M
-- shell: interior x -10..10, z -8..2, walls 0.5 thick (origin = plaster centre), 12 tall from y -0.4
local W=-0.4
for _,x in ipairs({-5,5}) do
  put("DormFloor",CFrame.new(x,W,-3),"Floor"..(x<0 and "L" or "R"),nil,Shell)
  put("DormCeiling",CFrame.new(x,10.7,-3),"Ceiling"..(x<0 and "L" or "R"),nil,Shell)
end
put("DormWall",CFrame.new(-5,W,-8.25)*R(180),"WallBackL",nil,Shell)
put("DormWallWindow",CFrame.new(5,W,-8.25)*R(180),"WallBackWindow",nil,Shell)
put("DormWall",CFrame.new(-10.25,W,-3)*R(-90),"WallLeft",nil,Shell)
put("DormWall",CFrame.new(10.25,W,-3)*R(90),"WallRight",nil,Shell)
put("DormWallDoor",CFrame.new(-5,W,2.25),"WallFrontDoor",nil,Shell)
put("DormWall",CFrame.new(5,W,2.25),"WallFrontR",nil,Shell)

-- the door in the opening (a classroom door with its door behaviour stripped: it never opens, the Exit prompt is the way out)
local D=P.ClassroomDoor:Clone()
for _,t in ipairs(game.CollectionService:GetTags(D)) do game.CollectionService:RemoveTag(D,t) end
for k in pairs(D:GetAttributes()) do D:SetAttribute(k,nil) end
D.Name="Door" D:ScaleTo(P.ClassroomDoor:GetScale()*5.1/4.692) D:PivotTo(CFrame.new(-5,F,2.25)) D.Parent=M

local Exit=Instance.new("Part") Exit.Name="Exit" Exit.Anchored=true Exit.CanCollide=false Exit.CanTouch=false
Exit.Transparency=1 Exit.Size=Vector3.new(4,7,0.4) Exit.CFrame=CFrame.new(-5,F+3.5,1.5)*R(180) Exit.Parent=M
local Sp=Instance.new("Part") Sp.Name="Spawn" Sp.Anchored=true Sp.CanCollide=false Sp.CanTouch=false Sp.CanQuery=false
Sp.Transparency=1 Sp.Size=Vector3.new(2,0.2,2) Sp.CFrame=CFrame.new(-3.8,0,0.6) Sp.Parent=M

-- light
local CL=put("DormCeilingLight",CFrame.new(0,11.3-2.75,-3),"CeilingLight")
local G=CL:FindFirstChild("DormCeilingLight_Glow")
G:SetAttribute("NHHomeLight",true)
local L=Instance.new("PointLight") L.Brightness=1.6 L.Range=26 L.Color=Color3.fromRGB(255,214,160) L.Shadows=true L.Parent=G

-- furniture
local Bed=CFrame.new(-7.57,F,-3.71)*R(180)
put("DormBed",Bed,"BedMade","Spotless,Tidy,LivedIn")
put("DormBedUnmade",Bed,"BedUnmade","Slipping,Wreck")
local Desk=CFrame.new(5,F,-6.62)*R(180)
put("DormDesk",Desk,"Desk")
local Chair=CFrame.new(5,F,-4.55)
put("DormChair",Chair,"Chair")
put("JacketOnChair",Chair,"JacketOnChair","LivedIn")
put("ClothesOnChair",Chair,"ClothesOnChair","Slipping,Wreck")
local DT=F+2.95
local Lamp=put("DormDeskLamp",CFrame.new(3.25,DT,-6.0)*R(160),"DeskLamp")
local LG=Lamp:FindFirstChild("DormDeskLamp_Glow")
LG:SetAttribute("NHHomeLight",true)
local LL=Instance.new("PointLight") LL.Brightness=0.7 LL.Range=9 LL.Color=Color3.fromRGB(255,206,150) LL.Shadows=false LL.Parent=LG
put("DormBookStack",CFrame.new(6.2,DT,-5.95)*R(195),"BookStack","LivedIn,Slipping")
put("CoffeeCup",CFrame.new(7.0,DT,-5.85)*R(200),"CoffeeCup","LivedIn,Slipping,Wreck")
local Ward=CFrame.new(8.58,F,-1.2)*R(90)
put("DormWardrobe",Ward,"Wardrobe","Spotless,Tidy,LivedIn,Slipping")
put("DormWardrobeOpen",Ward,"WardrobeOpen","Wreck")
local Shelf=CFrame.new(-1.0,4.4,-7.4)*R(180)
put("DormShelfFull",Shelf,"ShelfFull","Spotless,Tidy")
put("DormShelfSparse",Shelf,"ShelfSparse","LivedIn,Slipping")
put("DormShelfEmpty",Shelf,"ShelfEmpty","Wreck")
local Plant=CFrame.new(-1.0,F,-5.95)*R(180)
put("DormPlantHealthy",Plant,"PlantHealthy","Spotless,Tidy,LivedIn")
put("DormPlantWilting",Plant,"PlantWilting","Slipping")
put("DormPlantDead",Plant,"PlantDead","Wreck")
put("DormRug",CFrame.new(0.5,F,-2.0),"Rug")
-- the left wall above the bed (plaster face x = -10; wall pieces hang from their back face)
local LW=R(-90)
put("CertificateHonourRoll",CFrame.new(-10,6.1,-6.0)*LW,"Certificate1","Spotless")
put("CertificateDeansList",CFrame.new(-10,6.1,-3.7)*LW,"Certificate2","Spotless")
put("CertificatePerfectAttendance",CFrame.new(-10,6.1,-1.4)*LW,"Certificate3","Spotless")
put("OverdueNotices",CFrame.new(-10,5.6,-3.7)*LW,"OverdueNotices","Wreck")
-- trophy shelf over the bed's head, on the back wall; spots on its top (kit: (+-0.75 / +-2.25, top 1.0, -0.05))
local TS=CFrame.new(-6.8,6.3,-7.42)*R(180)
local Tr=put("TrophyShelf",TS,"TrophyShelf","Spotless,Tidy")
for K,x in ipairs({0.75,-0.75,2.25,-2.25}) do
  local s=Instance.new("Part") s.Name="TrophySpot"..K s.Anchored=true s.CanCollide=false s.CanTouch=false s.CanQuery=false
  s.Transparency=1 s.Size=Vector3.new(0.4,0.1,0.4) s.CFrame=TS*CFrame.new(x,0.95,0.05) s.Parent=Tr
end
-- the mess
put("PaperScatter",CFrame.new(1.7,F+0.06,-2.1)*R(15),"PaperScatter","Slipping,Wreck")
put("PizzaBoxes",CFrame.new(-1.4,F+0.06,-2.7)*R(-25),"PizzaBoxes","Wreck")
put("ClothesPile",CFrame.new(3.6,F,-0.3)*R(30),"ClothesPile","Wreck")
put("EmptyCans",CFrame.new(6.6,F,-2.7)*R(70),"EmptyCans","Wreck")

for _,d in ipairs(M:GetDescendants()) do if d:IsA("BasePart") then d.Anchored=true end end
M.WorldPivot=CFrame.new()
M.Parent=Homes
local n=0 for _,d in ipairs(M:GetDescendants()) do if d:IsA("BasePart") then n+=1 end end
return "Dorm built: "..n.." parts"
