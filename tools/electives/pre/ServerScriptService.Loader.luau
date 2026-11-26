local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local Chrono = require(ReplicatedStorage.Packages.chrono)
Chrono.Start()


local ModuleLoader = require(ReplicatedStorage.ModuleLoader)

ModuleLoader()
