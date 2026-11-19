local cam = workspace.CurrentCamera
cam.CameraType = Enum.CameraType.Scriptable
local t = Vector3.new(4009.56,-355.55,3992.48)
cam.CFrame = CFrame.lookAt(t + Vector3.new(-4.2, 1.6, 1.2), t + Vector3.new(0, 0.5, 0))
return "cam at register"
