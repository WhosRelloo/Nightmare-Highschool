#!/bin/bash
# cam.sh <out.png> cx cy cz lx ly lz [fov] | cam.sh off   (Play: the client's shot camera, then a capture)
cd "$(dirname "$0")"
if [ "$1" = off ]; then sed "s/MODEV/off/;s/CX/0/;s/CY/0/;s/CZ/0/;s/LX/0/;s/LY/0/;s/LZ/1/;s/FOVV/70/" _cam.lua > _cam_now.lua
else sed "s/MODEV/on/;s/CX/$2/;s/CY/$3/;s/CZ/$4/;s/LX/$5/;s/LY/$6/;s/LZ/$7/;s/FOVV/${8:-60}/" _cam.lua > _cam_now.lua; fi
python -X utf8 -I E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py luau "placeId: 98950102230473" Client @_cam_now.lua
[ "$1" = off ] || python -X utf8 -I shot.py "$1"
