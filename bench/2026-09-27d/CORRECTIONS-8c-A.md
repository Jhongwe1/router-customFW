# CORRECTIONS — 8c-cells group A in `bench/2026-09-27d/` (card `CELLS-A.md`)

Written 2026-09-28, in segment 115, after the runs. It records where this directory departs from
its card and nothing else. Sources: the captures here and the run record
`$FWRE_WORK/rebuild/s115/r6b8c-cells/run/A/` (`a8c.out`, `rc.tsv`). Times are local (+0800),
from each capture's `.meta.json`.

1. **What ran here.** The power-on was caught at the loader prompt at 18:01 (`S-PRE` 18:01:17,
   `S-CATCH` 18:01:26). Group A started from that prompt at 20:09:24: invocation `A-L`, all 27
   cells (`AL-TTY` … `AL-R26`), each rc 0, to 20:09:39.
2. **`A-B` stopped at `looprun` S5c.** `AB-FL` ran (rc 0). `A1Q` (20:09:40–20:09:44) passed S5
   (`AUTOBURN 0`, `LOADADDR 80500000` and `IPCONFIG 10.1.1.1`, each accepted:
   `A1Q-rescue.json`) and S5b (the `AUTOBURN` word read back `00000000`: `A1Q-ab2`), and failed
   S5c's `P-b`: 量 the loader did not answer ARP, and the host's entry for 10.1.1.1 stayed
   `INCOMPLETE` (`A1Q.log`, `A1Q.stages.tsv`), 2 h 8 min after the catch. Nothing was uploaded.
   The invocation exited rc 3, and the driver's tail watch `X-W1` (20:09:44–20:09:46) ended on
   the loader prompt with no banner before it. Why the loader did not answer ARP after an
   accepted `IPCONFIG` is undetermined.
3. **Why the rest of group A is in `bench/2026-09-28/`.** Group A did not resume on this power
   cycle, which ended with the owner's power-off before `NET-25`'s boot 1 (that boot's board-off
   pre-flight, `bench/2026-09-27e/B-PRE`, ran at 23:37:58). It resumed from `A-B` at 00:05:31 on
   2026-09-28, on boot 10's power cycle, with no power action after that boot, so its captures
   belong to that power cycle's directory and date: `bench/2026-09-28/`. They were written
   through `a8c.sh --dir bench/2026-09-28 --from A-B`; the card that ran is this `CELLS-A.md`
   with `bench/2026-09-27d` replaced by `bench/2026-09-28` on 323 lines, proved by replacing it
   back, and its copy is `bench/2026-09-28/CELLS-A.md`.
4. **What that leaves here.** `A-L` ran only on this power cycle, so the loader-inherited
   column comes from this one and every later invocation from boot 10's. `AB-FL` and `A1Q` ran
   in both directories; no cell after `A1Q` has a capture here.
5. **No file was withheld** from this directory: `tools/audit-bench-log.py` over its `.log` and
   `.json` files and `tools/flashwin.py scan` over the directory read 0 hits on 2026-09-28.
