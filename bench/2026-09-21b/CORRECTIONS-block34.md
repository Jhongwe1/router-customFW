# CORRECTIONS — block 34, seating 32

The card (`PREDICTIONS-B36-block34.md`) is frozen and is never edited. Every
departure from it is recorded here, and § 0 is written **before** the
corrected cell is executed.

---

## § 0 The register-read cells need a leading `sleep 1`, and the precedent I cited already had one

**Written 2026-09-21T01:4x, before re-running.**

### What happened

`B5-REGa`…`B5-REGd` and `B6-REGa2` ran as carded and returned **interleaved**
output. 量, `B5-REGa.log`:

```
echo read 0xBB806100 4 >/proc/rtl865x/memory ; echo read 0xBB806cmd read
1
bb806100:  000412 00413   >	/	 p	 r	 o	 c	 /	 r
```

The kernel's `cmd read` and its hexdump line are interleaved character by
character with busybox ash's echo of the 91-character command line.

### Why, and the evidence that it is the FIFO and not the shell

The corruption has a **direction**: on every one of the five captures the
**last** read on the line is clean and the **first** is not. 量:

| capture | first read | last read |
|---|---|---|
| `B5-REGa` | `bb806100:  000412 00413` — corrupt | `bb806104:  00000000` — clean |
| `B5-REGb` | `bb806108:  /00p00r00o00c` — corrupt | `bb80610c:  00000000` — clean |
| `B5-REGc` | `bb806170:  0000t00l008` — corrupt | `bb804500:  000000F4` — clean |
| `B5-REGd` | `b8010020:   A145B 80>48/` — corrupt | `b8010000:  oC4r00y0000` — corrupt |
| `B6-REGa2` | `bb806100:  x00/12m00e13m` — corrupt | `bb806104:  00000000` — clean |

That direction is what a **drain** looks like and is not what a shell-parsing
fault would look like. 91 characters at 38400 8N1 is
`91 × 10 / 38400` = **23.7 ms** of echo still queued when the first `echo read`
completes, and `prom_putchar` fills a FIFO rather than the wire
(`CLAUDE.md`, `FW-...` / seating 17's `OVSEL` 0 result). The kernel's write
enters the same FIFO behind a partially drained echo.

⚠️ `B5-REGd`'s **second** read is corrupt too, which the drain story predicts
only if that line's echo was still draining at both writes — its payload is the
same 91 characters but its two kernel outputs are longer (`b8010020` and
`b8010000` both carry an ASCII column with high bytes). Recorded as a weakness
in the explanation rather than smoothed over.

### 🔴 The precedent I cited to license these cells already carried the fix

`bench/2026-09-17b/X28-LX28.log` — the capture quoted in the card's own § 4
predictions table as proof that vendor `/proc` output survives
`CONFIG_PRINTK=n` — sends:

```
sleep 1 ; echo read 0xBB804128 4 > /proc/rtl865x/memory
```

and returns `cmd read` + `bb804128:  000000E0` **clean**. **I copied the
command shape out of that capture and dropped the `sleep 1`.** The card is
wrong in exactly the way the evidence it rests on is right.

### The change, and the alternatives rejected

**Change**: every register-read cell becomes

```
sleep 1 ; echo read 0x<ADDR> 4 > /proc/rtl865x/memory
```

— **one** read per cell, 55 characters, matching `X28-LX28` verbatim except
for the address. The cell names in the card's `cells` fence do not change;
`B5-REGa` now reads `GDSR0` alone and the companions become `B5-REGa2`…, named
below.

**Rejected — two reads on one line with one leading `sleep`** (113 characters).
It would probably work, because the echo is drained before the first write.
Rejected because *probably* is the word: the direction evidence above shows the
race exists, and the only form this device has ever produced a clean reading
from is the one-read form. A cell is one-shot and there is no second chance to
learn that 113 characters was too many.

**Rejected — parse the interleaving out.** Two of the eight values are
recoverable by hand (`b8010000` → `C4000000`, `b8010020` → `A15B8048`) and six
are not cleanly separable. A reading that needs a human to disentangle it is
not a reading, and a card that quotes one would be quoting a reconstruction.

**Rejected — `--until 'bb[0-9a-f]{6}:'`.** It would end the capture at the
first match and lose the second read entirely, and it cannot fix corruption
that has already entered the stream.

### What this does NOT change

The card's § 3 rule 3 already forbids shell substitution and caps the line at
127 characters; this correction makes the lines **shorter**, so both still
hold. No prediction in § 4, § 6 or § 7 is altered — only the way the same
registers are asked for. The values in the table above are **not** used as
measurements; they are used as evidence about the instrument.

### The one value that is quoted forward, and why it is safe

`bb804500:  000000F4` — `SBFCR0`, the last read on its line, clean by the
direction rule, and confirmed by re-reading it in the corrected form below.
`0x000000F4` = **244**, which is `S_DSC_RUNOUT` (bits 9:0). 🔴 That is **not**
the 480 the vendor's `rtl865x_asicCom.c:1052` writes as `S_DSC_RUNOUT`'s
threshold — the live value on this die is 244, and the card's `H-POOL`
comparison is against **244**, not 480.

---

## § 1 Departures from the card, listed

The measurements themselves are in `RESULTS-block34.md`. This section lists
only where execution left the frozen card.

1. **`B5-REGa..d` and `B6-REGa2` were re-run** in the `sleep 1` one-read form
   under `-a2` names (§ 0). The carded names hold attempt 1 and are evidence
   about the **instrument**, not readings of the board.
2. 🔴 **The re-run was nearly lost to a swallowed refusal.** The first attempt
   reused the carded names with the tool's output sent to `/dev/null`;
   `console-capture.py` refuses to overwrite an existing output file, the
   refusal was discarded, and the grep that followed read the attempt-1 files.
   Five of nine printed rows were stale. `RESULTS` § 1. **No tool's stdout is
   redirected anywhere else in this block.**
3. **`D0-WEDGE` was not run.** The wedge arrived from `C-LADDER`'s first rung
   instead, which is a stronger experiment and one the card had pre-registered
   the meaning of. `RESULTS` § 2.
4. **`D2-REGa..d` ran as `-a2` names** for the reason in § 0, with the
   companion addresses added as `2`-suffixed names.
5. **Not run**: `C6-ASIC`, `D4-ASICW`, `D11-REGa/b`, `E2-PROC`, `E3-REGa/b`,
   `F5-FLOOD`, `F5-HOSTFLOOD`, `F6-POST`, `F7-REGa`, `F8-PING`. The first five
   were abandoned because the console backlog made each cost minutes and the
   register readings that mattered were already taken (`RESULTS` § 9); the
   `F5`–`F8` group is `D6` and is not attempted (`RESULTS` § 11).
6. **`G0-COLD`, `J0-COLD` and `J2-COLD` have no `.meta.json`.** They are ESC
   catch windows terminated by `pkill`; a SIGTERM kill loses the metadata while
   the `.log` and `.timing` survive, flushed per chunk. Declared here rather
   than left for a sweep to find.
7. **Three power cycles were spent, not one.** The first was already spent when
   the card was written. The second and third were **recoveries**, not
   experiments: on both occasions the shell had stopped executing and
   `busybox reboot -f` could not run (`RESULTS` § 8).
8. 🔴 **A byte count was read as a boot, and the guard is what caught it.** 量:
   after the second request to power-cycle, `J0-COLD` returned 7,792 bytes and
   that was taken as a boot. The uptime stamps inside it — `[914.38]`,
   `[915.45]`, `[920.29]` — **continue from `[839.10]` in the previous
   capture**, so the board had never lost power. `looprun` then stopped at `S5`
   with `rc=1` because there was no loader prompt, and **nothing was
   uploaded**. The test used afterwards is the presence of `Booting...` and
   `ramSize: 32M` and the absence of `Reboot Result from Watchdog Timeout!`,
   never a byte count.
9. 🔴 **The `--esc` register-read form in the card's § 4 predictions table was
   right about the precedent and wrong about the command.** The precedent
   (`bench/2026-09-17b/X28-LX28.log`) was quoted for its *output* and its
   `sleep 1` was dropped when its *command* was copied. § 0.
