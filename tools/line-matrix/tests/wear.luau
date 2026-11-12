-- NHWear stamping (NH Combat Test, Edit mode, run with execute_luau): dress a dummy rig, read its NHWear
-- data.Acc is the look's comma-list STRING of Config.Accessories ids (not a table).
-- A fresh copy of UI.Appearance is required from inside UI (so script.Parent's sibling modules resolve and an earlier
-- cached require of the old source isn't reused), destroyed after the apply.
local Players = game:GetService("Players")
local UI = game.ReplicatedStorage.UI
local Copy = UI.Appearance:Clone()
Copy.Name = "AppearanceNHWearTest"
Copy.Parent = UI
local OkReq, A = pcall(require, Copy)
if not OkReq then Copy:Destroy() return "ERROR: require " .. tostring(A) end
local Rig = Players:CreateHumanoidModelFromDescription(Instance.new("HumanoidDescription"), Enum.HumanoidRigType.R6)
Rig.Name = "NHWearTest"
Rig.Parent = workspace
local Ok, Err = pcall(A.ApplyTo, Rig, { Uniform = "varsity-jacket", Bottoms = "striped-joggers", Acc = "hat-top,collar-ruff", HairId = 0 })
local Got = Rig:GetAttribute("NHWear")
Rig:Destroy()
Copy:Destroy()
if not Ok then return "ERROR: " .. tostring(Err) end
local Want = "varsity-jacket|striped-joggers|hat-top,collar-ruff"
return if Got == Want then "PASS " .. Got else "FAIL got " .. tostring(Got) .. ", want " .. Want
