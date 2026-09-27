# CORRECTIONS — the power cycle after midnight: group A from `A-B`, `R6b-10`'s regression, arm II

Written 2026-09-28, in segment 115, after the runs. It records where this directory departs from
its three cards (`CELLS-A.md`, `RUN-r6b10.md`, `RUN-armII.md`) and nothing else. Sources: the
captures here and the run records `$FWRE_WORK/rebuild/s115/r6b8c-cells/run/A-2026-09-28/` and
`$FWRE_WORK/rebuild/s115/run10/2026-09-28/` (`rc.tsv`, one transcript per line). Times are local
(+0800), from each capture's `.meta.json` and the transcripts' stamps.

1. **One power cycle, no power action.** This directory continues `NET-25` boot 10's power
   cycle (`bench/2026-09-27n/`, caught at 23:54:12); its captures began between 00:05:33 and 00:28:00.
   In order: group A from `A-B` (00:05:31–00:13:33, all eleven invocations rc 0, ending at the
   loader prompt; why it is here: `bench/2026-09-27d/CORRECTIONS-8c-A.md`); then
   `RUN-r6b10.md` on `r6b10y`, lines `y-line0` and `y-line1`; then `RUN-armII.md` on `r6b10n`,
   lines `n-line0`, `n-line1`, `n-line2` and `n-line2b`. `y-line2`, `n-line3` and `n-line4` did
   not run.
2. **The first `y-line1` stopped at `Y1-ARP`** (00:13:58–00:14:02, rc 3): 量 `arping` sent 4
   and received 0, and the line's gate wants at least one reply. The board was at the loader
   prompt `A-Z`'s reboot left, with no `IPCONFIG` typed since that reset, and the loader answers
   ARP only after `IPCONFIG` (`NET-95`). Nothing was uploaded. So that the re-run could write
   the card's own names, that capture `Y1-ARP.log` was renamed `X-Y1ARP0.log`, and the tail
   watch the line opened, `X-Y1` (00:14:02–00:14:04, ended on the loader prompt), was renamed
   `X-Y1W0.*`; the line's transcript is `y-line1.r0-arpgate.log` in the run record.
3. **`X-ARP2` and `X-ARP3` are off-card.** The main session typed `IPCONFIG 10.1.1.1` (reply
   `Now your Target IP is 10.1.1.1`) at 00:14:38 (`X-ARP2`), before `y-line1` ran again
   (00:16:01–00:21:08, rc 0, `Y1-ARP` 4 of 4), and at 00:21:25 (`X-ARP3`), before `n-line1`
   (00:21:34–00:22:58, rc 0, `M1-ARP` 4 of 4). No card names either.
4. **`M5-REF`'s `--until` could not match** (`n-line2`, 00:23:32–00:23:44, rc 3). The cell sent
   `echo phyif all > /proc/rtl819x-switch ; cat /proc/rtl819x-switch`; 量 all 2,298 bytes
   arrived within 0.684 s, and the capture ran to its `--seconds 10.0`. The pattern wants the
   shell prompt straight after the `TCR7` line's line end, and the refused write's echo,
   `phyif al` (`FW-41`), sits between the two. `cardrun` stopped at the cell's first gate,
   `gate:until`, so its other three were not evaluated; the capture holds
   `phyif unlocked 0 ok 0 stored 0 already 0 refused 1 idfail 0 rbfail 0` and `n_writes 0`, and
   no banner, no loader prompt and no `Linux version`. The defect is the card's pattern.
5. **The watch `X-M2`** (00:23:44–00:27:00, ended by `stopwatch.sh`): 量 9,160 bytes, 9,156 of
   them BEL, no banner and no loader prompt; the CR the tool writes on interrupt drew `# `.
   `X-M1` (00:22:58–00:23:27, ended the same way) holds 1,287 BEL in 1,291 bytes; no other
   capture in this directory holds a BEL. `X-M2.timing`'s first read is 0.017 s after the
   capture's start, and no two reads are more than 0.081 s apart: the console never went
   quiet. The main session said during the run that `X-M2` read no bytes for about 89 s; that
   was its own instrument error, retracted: it read the size of `X-M2.log` from Windows while
   the capture was still writing it from WSL, and that view read 0 bytes until later (the
   board's `jiffies` also advanced at 100.002/s through the span, `M5-REF.log` → `M5-PHY.log`).
   The BELs are the shell answering the watch's ESC stream, as in `X-M1`.
6. **`n-line2b` resumed arm II** (00:27:11–00:28:03, rc 0): `n-line2.sh` with its item list
   cut to begin at `M5-UNL`, dropping `M5-REF` and its four gates (`gate:until`, the no-reset
   `grep`, the `phyif … refused 1 …` `grep`, `n_writes 0`). Its line name `n-line2` became
   `n-line2b` and its watch `X-M2` became `X-M3`, which did not start because the line ended on
   `MZ-RB`'s prompt gate. Everything else is verbatim: `diff n-line2.sh n-line2b.sh` is those
   six lines, and `mk-line2b.py`, which wrote it (both in `$FWRE_WORK/rebuild/s115/r6b10/`),
   refuses unless what precedes `M5-UNL` starts with `M5-REF` and names it five times, the
   cell and its four gates. `M5-REF` was not run again.
7. **No file was withheld** from this directory: `tools/audit-bench-log.py` over its `.log` and
   `.json` files and `tools/flashwin.py scan` over the directory read 0 hits on 2026-09-28.
