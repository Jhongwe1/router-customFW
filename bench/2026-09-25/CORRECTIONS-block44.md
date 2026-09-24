# CORRECTIONS — block 44, seating 40

Every departure from the frozen card `PREDICTIONS-B46-block44.md`, and every
defect found in it, each written before what it describes was done. The card
itself is **not edited** — `check-predictions` reads its mtime.

---

## § 1 `Z0-HCG` refused; `Z0-HCG2` runs as § 3.8 declares — written 00:1x, before it

**What happened.** `I1b` stopped at `Z0-HCG`'s first gate, 00:05:55. The report
read `tick check: AGREE over 50 pair(s), worst -0.573 ppm, strong: the kernel's
rate is off nominal here` — the gate requires `vacuous` — and `steps: timerfd 0`.
Its 60 s window (RAW 1539.3–1599.3) held `tick` 9937, then 9817, then **10834 from
RAW 1549.9 to 1575.2** — the kernel's clock 8.34 % fast, the default `maxslewrate`
of `chronyd` (83,333 ppm) — then 10001, with `freq` −27.3…−9.9 ppm. Measured from
the rows, RAW 1549.907 → 1557.537 advanced MONOTONIC 8.2668 s in 7.6302 s, 1.0834.
`timesyncd` had been stopped at 00:03:13 (`Z0-TSD`), so the writer is 推 WSL's own
`chronyd` (`CLK-38`), which follows the Windows clock. That clock had just woken
from 9.5 h of suspend: `w32tm /query /status /verbose` read *Phase Offset*
0.3208324 s, *State Machine* 1 (Hold), *Last Sync Error* 2 (only stale time data)
at 00:06:39 and the same at 00:07:58. **No power** (§ 3.8, § 6).

**What runs now, as § 3.8 wrote it before power.** The same line once more, as the
declared off-card cell `Z0-HCG2`, no sooner than ten minutes after the refusal
(00:15:55): `Z0-HCG`'s line from § 5 with `Z0-HCG2` as its name and `HCL` expanded
as § 5 defines it, run as `cardrun` runs a `HOST` cell (`bash -c` from the
repository root, stdout and stderr to `bench/2026-09-25/Z0-HCG2.log`, opened
exclusively). `cardrun` runs only fenced cells, so `$FWRE_WORK/rebuild/s110/hcg2.py`
lifts that line and `Z0-HCG`'s two gates from the card itself and applies the gates
as `cardrun` applies `grep=` (CRs removed, `re.search`, `re.M`). `timesyncd` stays
stopped and `I0` keeps logging meanwhile.

**Prediction, written before it runs.** 推 **it permits.** From RAW 1575.2 to
1845.2 (00:05:31–00:10:01) `Z0-HC` holds 52 `adj` rows, every one `tick` 10001,
`freq` −99.84…−2.23 ppm: an implied rate of +0.2…+97.8 ppm, inside the 1e-4 that
`tick_check` calls nominal, and no `step` row. **Refuted by** a `strong` or
`DISAGREE` tick check, or a step. The margin is one-sided and thin: a `freq` of 0 or
above at `tick` 10001 is past 100 ppm, and the closest row so far was 2.2 ppm from it.

**Then.** If it permits: `I2`, press 1, as § 6. If it refuses: no power; `I9` runs
(`Z9-HCX?`, `Z9-HCR?`, `Z9-TSD`), and the owner decides the day.

**What this already says about § 3.8's 推**, stated before any press so it cannot be
read afterwards: *"from 100 s after `Z0-TSD` on, no `step` row and every `linux`
row `tick=10000`"* is refuted — the rows read `tick` 10001 from RAW 1575.2 on, and
10834 before that. The containment § 3.8 wrote for exactly this applies unchanged:
every window whose rows show a tick other than 10,000, or `freq` beyond ±100 ppm, is
named, and every host-timer interval inside it is published as affected. At
+0.2…+97.8 ppm that is at most 1 ms in a 10 s interval; the boot captures are
stamped on RAW and are not affected.

**Outcome** (a reading, added after it ran): `Z0-HCG2` permitted, 00:18:37 —
`tick check: AGREE over 52 pair(s), worst +0.452 ppm, vacuous`, `steps: timerfd 0`.
The 推 held.

---

## § 2 `P2-MB0` refused on its digest; the map is unchanged — written 02:0x, before resuming

**What happened.** `I-P2` stopped at `P2-MB0`'s first gate, 02:01:30: the section
digest read `1de86c73eef9cb75…`, not `0927be41e91fe4bd…`. The stop interrupted
`P2-HP` (`ENDED P2-HP rc=0`). The board is at rlxfw's shell, powered.

**Why, measured** (`$FWRE_WORK/rebuild/s110/mapverify.sh`, `mapdiff.py`):
`P2-M0.log` is 3,009 B and ends `map_lines 32` with no line terminator;
`P1-M0.log` is 3,013 B and ends `map_lines 32\r\n# `. Both captures stopped on
`--until` matched at offset 2997; the four bytes after the match reached P1's
capture and not P2's. `--until` does not read on for 50 ms after its match: the
match is recorded inside `drain(0.05)`, which reads only to the end of the 50 ms
window it is in, and the loop then stops — anywhere from 0 to 50 ms (讀
`tools/console-capture.py`, `drain` and the loop that calls it; a subagent's
reading, checked against the code). The card's `MB` pipeline, run
verbatim, gives `1de86c73…` on `P2-M0.log` as captured, **`0927be41…` on a
scratch copy with `\r\n` appended** (outside the repository; nothing in `bench/`
is touched), and `0927be41…` on `P1-M0.log`. The section's 34 lines are byte-
identical to P1-M0's and to seating A's `P3-M0`; outside it only `map_jiffies`
differs (1300 → 1301). `P2-MB0`'s second and third gates, applied from the card
as `cardrun` applies them, both match: `DIFFER 000000` (the expected group 0) and
`31 same, 1 DIFFER, 0 scope, 0 extra, 0 missing`. **No flash group read
differently from P1-M0's**; the refusal is the instrument's, not the flash's —
the `MB` digest includes the final line's terminator, which `--until`'s drain
does not guarantee.

**What runs now, as § 6's stop table says for a map gate**: the rlxfw press
finishes `--from` its next cell, `P2-HPX`, with the transcript
`$FWRE_WORK/rebuild/s110/run-I-P2-r2.log` (the first run's log is kept as it is).
`P2-HPX`'s `pkill` finds the probe already ended; its `hpstop` gate reads the
record's last line as it stands.

**What does not run until the owner has read this** (§ 6, `P2` stop-loss): any
vendor boot — `I-V4`…`I-V7`, `I-M2`. The owner's reading and ruling are recorded
below when given, before `I-V4` runs or does not.

**Outcome of the resumption** (a reading): `I-P2 --from P2-HPX` ran to `ALL ITEMS
DONE`, 02:04:07 — `hpstop` read the record's last line, `stop … reason=SIGINT` at
RAW 8534.865 (the runner's own stop); `P2-ICMP` 20 of 20 at every size; `P2-TK1`
captured. The owner was then asked to power off.

**The owner's ruling**, 2026-09-25 ~02:0x, after reading this section: **continue
`V4`–`V7` and `M2`.** `P3`'s map brackets them as the card planned. If `P3-MB0`
refuses the same way, the same stop-table rule applies and the owner reads it
again; nothing about the gate is changed.
