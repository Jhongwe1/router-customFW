# CORRECTIONS — 8c-cells group B, `NET-25` boot 10 (card `CELLS-B10.md`)

Written 2026-09-28, in segment 115, after the run. It records where this directory departs from
its card and nothing else. Sources: the captures here and the run record
`$FWRE_WORK/rebuild/s115/r6b8c-cells/run/B10/`. Times are local (+0800), from each capture's
`.meta.json`.

1. **The late prep, at the owner's request.** `b8c.sh prep` refuses from 23:52 to midnight,
   because a power cycle's captures belong to its directory's date. This boot was prepped at
   23:53:46, inside that window, through `$FWRE_WORK/rebuild/s115/r6b8c-cells/tools/b8c-late.sh`:
   a copy of `b8c.sh` that differs in one line, which moves the refusal's start to 23:58. The
   card was generated and passed `cardcheck commands` (0 refused) at 23:53:51. The board-off
   pre-flight `B-PRE` ran at 23:54:08, the catch `B-CATCH` opened at 23:54:12, and the closing
   reboot `B-RB` ended on the loader prompt at 23:55:16. Every capture here is dated 2026-09-27.
2. **`X-ARP1` is off-card.** At 23:55:54 the main session typed `IPCONFIG 10.1.1.1` at that
   prompt (`X-ARP1`, reply `Now your Target IP is 10.1.1.1`) and then ran a host `arping` of
   10.1.1.1, whose output is in no file here. No card names `X-ARP1`.
3. **The power cycle continues in `bench/2026-09-28/`**: no power action followed this boot
   (`bench/2026-09-28/CORRECTIONS-A-r6b10-armII.md`).
4. **No file was withheld** from this directory: `tools/audit-bench-log.py` over its `.log` and
   `.json` files and `tools/flashwin.py scan` over the directory read 0 hits on 2026-09-28.
