# Combat 2.8–2.14 ported to the Map (2.14.1)

**What changed on the Map** (placeId 111107083446202):
- 23 existing scripts were updated.
- 16 new scripts were added.
- Two asset folders were added, both tagged `NHCore`:
  - `ReplicatedStorage.Assets.Animations.Weapons.Fist.Moves`: the four bespoke clips, with their published ids.
  - `ReplicatedStorage.Assets.HandGear`: the three gear templates, built in Studio.

The Map's backup is `ServerStorage.NH_Backup.CombatPort_pre_20261113`.

## How the port was done
1. **Checksums.** `place_hashes.py` checksummed every script in both places. Each Map script that differed matched,
   byte for byte, an NH Combat Test backup taken just before one of the combat releases.
2. **Replay.** `chain.py` replayed each release's own edit lists in order (2.8 q8–q8c through 2.14 q14*) onto the
   Map's copies. All 139 edits applied cleanly.
3. **Check.** 21 of 23 results came out identical to NH Combat Test.
   - **Config.Armory:** the remaining difference is the asset ids, so it was taken from Combat Test.
   - **Config.Discipline:** it keeps only the Contraband line. The Delinquent session's 2.8.1 "Record" block is
     another session's work, waiting on the owner's OK, so it was left out.
4. **New scripts.** These were copied as they are in Combat Test. Every path they reference exists on the Map,
   except ones they create at runtime.
5. **Install.** `install.py` installed everything, uploading big scripts in chunks.

## Folders
| Folder | What |
| --- | --- |
| `.` | The ported versions of the 23 existing scripts. |
| `pre/` | The Map's versions from before the port. |
| `new/` | The 16 new scripts. |

## Not ported, on purpose
- **`School.HallMonitor`:** the Map has none, so brass-knuckle confiscation does nothing there yet.
- **`Studio.TestBridge`:** the Map has none, so the combat log has no bridge command there.
- **Other sessions' unported work** (hunger, delinquent 2.8.1): it's theirs, waiting on the owner.
