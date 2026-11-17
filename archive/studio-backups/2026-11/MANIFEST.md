# Studio backup archive, 2026-11-17 (NH Combat Test)

The owner approved the archive proposal in `docs/expansion/10-Phase0-Report.md` §4 ("Yes, archive them").

**How the files were made:**
- Each item was serialized in Studio with `SerializationService:SerializeInstancesAsync({ item })`, which writes the real binary `.rbxm` format.
- The files were copied out in 42 KB base64 pages, and each one was checked:
  - its size matches Studio's buffer exactly;
  - its checksum (h = (h·31 + byte) mod 2147483647) matches Studio's;
  - it starts with the `<roblox!` header.
- Only then were the items removed from the place.

**Where the files are:**
- The `.rbxm` files sit in this folder on the owner's machine. They're git-ignored, because they're large binaries.
- **Restore:** Studio → right-click the parent (ServerStorage, or Workspace) → **Insert from File…** → pick the `.rbxm`.

| File | Bytes | Checksum | Instances | Was at |
|---|---|---|---|---|
| ServerStorage__InertLiveDummies_Backup.rbxm | 567,816 | 1327986243 | 24,289 | ServerStorage._InertLiveDummies_Backup |
| ServerStorage__DummyNpcs_PreTrainingDummy_Backup.rbxm | 548,992 | 606796430 | 24,221 | ServerStorage._DummyNpcs_PreTrainingDummy_Backup |
| ServerStorage_Capes_Originals.rbxm | 540,553 | 1916868129 | 15,859 | ServerStorage.Capes_Originals |
| NH_Backup_Combat_preAudit_1102.rbxm | 622,269 | 1686963117 | 24,274 | ServerStorage.NH_Backup.Combat_preAudit_1102 |
| NH_Backup_HairImports_100x.rbxm | 748,360 | 157909300 | 5,030 | ServerStorage.NH_Backup.HairImports_100x |
| NH_Backup_Hair_v2_import_leftovers.rbxm | 132,333 | 660284397 | 3,862 | ServerStorage.NH_Backup.Hair_v2_import_leftovers |
| NH_Backup_Hair_v1.rbxm | 623,941 | 1572857447 | 1,274 | ServerStorage.NH_Backup.Hair_v1 |
| Workspace_NHPropsShowcase.rbxm | 18,208,342 | 937154856 | 6,955 | Workspace.NHPropsShowcase |
| Workspace_Vamp_Cape.rbxm | 173,669 | 497448041 | 5,154 | Workspace."Vamp Cape" |
| Workspace_Fur_Cape.rbxm | 216,893 | 582171902 | 5,828 | Workspace."Fur Cape" |
| Workspace_Rogue_Cape.rbxm | 207,596 | 2065812773 | 4,876 | Workspace."Rogue Cape" |
| Workspace_Crouch_Idle.rbxm | 55,372 | 1717455396 | 1,602 | Workspace."Crouch (Idle)" (KeyframeSequence) |
| Workspace_Crouch_walk.rbxm | 26,225 | 1162154264 | 649 | Workspace."Crouch walk" (KeyframeSequence) |
| Workspace_NHTEMP_SpiderParts.rbxm | 84,608 | 614912345 | 5 | Workspace.NHTEMP_SpiderParts |
| Workspace_NHTEMP_BatB.rbxm | 77,841 | 269280625 | 13 | Workspace.NHTEMP_BatB |

**Totals:** 15 files, 22.8 MB, 123,471 instances.

**The place after removal:**

| Where | Before | After |
|---|---|---|
| ServerStorage | 118,670 | 19,865 |
| Workspace | 45,102 | 20,020 |
| NH_Backup | 35,861 | 1,425 |

Some of these counts also include other sessions' edits made the same day.

**Kept:**
- `Workspace."Sean White"`: `Features.AmbientNpcs` takes the gym barbell from it.
- `MenuScene`: in use.
- Every `*_pre_202611*` backup folder.

**Checked before removal:**
- No script referenced any removed item by name. The game's capes load from `ReplicatedStorage.NHCapes`, so the three capes in the workspace were unused copies.

**Checked after removal:** a Play run started with no script errors, 24 NPCs spawned, and the slot, phone and strangers services were up.
