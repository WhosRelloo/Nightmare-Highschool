local cam = workspace.CurrentCamera
cam.CameraType = Enum.CameraType.Scriptable
local piv = CFrame.new(4000, -360, 4000)
cam.CFrame = CFrame.lookAt(piv:PointToWorldSpace(Vector3.new(5.5, 6.6, -4.2)), piv:PointToWorldSpace(Vector3.new(10, 6.0, -5.5)))
return "cam set"
