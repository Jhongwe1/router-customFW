# Block 13 — `R5-5`: a read-only MTD device of mine, driven by programmed I/O

**Written 2026-09-07, forty-first segment, at the desk, before power.**
`R5-5`'s bench half. The desk half is done and its artefacts are frozen (§1).

🔄 **THE DIRECTORY NAME WAS A PREDICTION AND IT WAS WRONG.** The card was
written into `bench/2026-09-08` on the assumption that the operator would next
have the board on the 8th. 量 2026-09-07, forty-second segment, three sides —
Git Bash `2026-09-07 16:59:06 +0800`, Windows `16:59:11 +08:00`, WSL
`16:59:17 +0800`, all Monday — and the seating is scheduled for **this
evening**, so the directory is `bench/2026-09-07` and §4.4 is expanded against
that name. `RUNSHEET.md` § "Three rules about the card's lifecycle, 2026-09-06"
rules 1 and 3 own that procedure and it is not copied here.

🔴 **The rename is not finished until the numbers agree.** `cardnum`'s
`expansion-*` rows count the expansion's lines **by a regex with the directory
inside it**, and `cells-fence` counts the fence the same way, so a rename that
misses lines is a red row at the desk rather than a wrong path at the bench.

**Freeze order, and it is not optional**: `tools/spec-check.py` green **first**,
then `cardcheck commands`, `cardcheck numbers`, then `check-predictions` — which
must read `0 of N` for a card whose captures do not exist yet. The freeze
paragraph is the **last** edit, so every capture under this directory is newer
than the file that predicted it.

🔴 **AND A STEP THAT WAS NOT IN THAT LIST UNTIL TODAY, BECAUSE THIS CARD
NEARLY SHIPPED WITH AN ID THE TREE CANNOT PRODUCE.** `RECIPE_ID` is a sha256
over **every file under `config/`** — comments included. The image was built,
staged and written into §1; then a one-line **comment** was edited in
`config/rlxfw-src/…/rtl819x-spi.c`, and the recipe moved from `e0028cc8` to
`3b589390`. Nothing warned: the build script's own comment knows a `config/`
edit moves `RECIPE_ID`, but frames it as *rebuild cost* — nobody had written
down that it also invalidates a frozen card's identity assertion, which is the
one number on the card the board itself checks.

**So the freeze order gains a step, before all the others**: re-derive
`RECIPE_ID` from the current `config/` (`rlxfw-kbuild.sh <cell> --dry-run`
prints it without staging anything) and compare it against §1. If they differ,
the image is stale and must be rebuilt — not the card edited. ⚠️ **This is
prose, and this repository's own lesson is that a rule in prose is not a rule**;
a checker for it is carried forward rather than claimed.

---

## 0. What this block is, in one paragraph

`rtl819x-spi` 1.0 registers a read-only `mtd_info` at `late_initcall` and reads
this unit's flash by issuing **real SPI transactions** through `SFCSR`/`SFDR` —
the same registers the vendor's driver uses, which is what makes this the first
driver in the gate that does not have its peripheral to itself. One traversal
computes a sha256 over `H601`'s complement **inside the kernel** (`D1`) and
compares the same bytes against the memory-mapped window (`D3`). Four cells are
controls that must fire: a deliberate byte corruption, a forced restore
mismatch, a refused write, and a KAT. **Nothing here writes flash and nothing
here happens without a `/proc` write.**

---

## 1. The image, staged and pinned

| | |
|---|---|
| uploadable image | `$FWRE_WORK/rebuild/bench-only/r55-20260907/rlxfw-r55-20260907.bin` |
| bytes | **1,039,360** |
| sha256 | `cc4e75194ff927a83e46c8b5901161f438028e12029c2c5419a15fe8f228e50a` |
| `RECIPE_ID` | `fce0af22` → **the board must print `RLXFW-ID0=FCE0AF22`** |
| `vmlinux` | 4,013,779 bytes, sha256-16 `5e63b426e59c3a04`, kept beside the image |
| `System.map` | 374,809 bytes, sha256-16 `8430039aa444f9df`, kept beside the image |
| build cell | `r55b` — 🔴 **and that cell is CONTAMINATED**, see §1.1. `r55a` was the first attempt and is stale: its recipe was `e0028cc8`, invalidated by a post-build comment edit under `config/` |

### 1.1 🔴 The build cell must not be reused, and the reason is a control that fired

After every artefact above was copied out, cell `r55b` was rebuilt with
`make CONFIG_MTD_RTL819X_WRITE=y` — **`D4`'s positive control**. That build
succeeded and put `rtl819x_spi_write_page` (`801a8a20`),
`rtl819x_spi_erase_sector` (`801a8a38`) and `rtl819x_spi_write_init`
(`802bbf10`) into that tree's `System.map`, which made `rlxfw-marks.py verify`
go **red** on `MK5` with *"must be 0 here: this symbol is in the map, so the
conditional TU WAS built"*.

**So the cell's `vmlinux` and `System.map` are no longer the shipped ones.** The
three files in `bench-only/r55-20260907/` are, and they are what §1 pins.

🟢 **`D4` is therefore proved with a control that can fail**: the shipped map
has the symbol **0** times and `verify` is green; the control map has it and
`verify` is red. Without the second half, `absent:` would be a rule that never
fires.

---

## 2. What is being claimed, and what would refute it

| | claim | refuted by |
|---|---|---|
| `D1` | sha256 over `[0,0x6000) ∪ [0x8000,0x400000)`, **4,186,112 bytes**, equals `a9916fd8…4ce3cba` (`FLS-24`) | any other digest with `digest_bytes 4186112` and `h601_hashed 0` |
| `D2` | the 8,192 bytes left out are a **rule**, not a failure | nothing here; their verification stays in the `FLR` bracket, which does not run this seating |
| `D3` | the PIO read and the `0xBD000000` read agree over **all 4,194,304 bytes** | `cmp_first_diff` ≥ 0 |
| `D4` | rlxfw contributes no flash-write code to this image | already settled at the desk, §1.1. ⚠️ It does **not** say this image cannot write flash — the vendor's path is here and always has been (`FW-44`) |
| `REG-38` | `SFCR` under Linux is `FFC00000` (divisor 16), **not** `REG-13`'s loader-prompt `3FC00000` (divisor 4) | `C1-P` reading `3FC00000`, or anything else. 讀 → 量 either way |

🔴 **`D3` is only evidence because the two paths are different at the
CONTROLLER, not merely in the source.** `FW-34` Group F measured the window
serving a single-word read as its own transaction — stride 4 and stride 1,024
both 30,354 ticks, `R = 1.0000`, **no buffering**. Without that, `equal` would
be compatible with the controller handing back the same buffered data twice.
*(The frozen DoD cited the other half of `FW-34` — the 4 MiB `wc -lc` — and that
reading goes through the PIO path, so it cannot license the window. `FW-43`.)*

🟢 **And `C1-VF`'s MMIO pass is a first in its own right.** The closing audit found that `FLS-11` and `MAP-12` rest their `量` on that same 4 MiB reading, so both are now re-pointed at `probe3` Group F — which is **bare metal**. **Nothing has ever read this window under Linux.** `C1-V4` is therefore the first, at 4 KiB, and `C1-VF` the first past a kilobyte. If they disagree with the PIO pass, that is a finding about the window and not about this driver, and the ladder is built so the 4 KiB rung says so before the 4 MiB one runs.

---

## 3. Predictions written before power

| mark / field | predicted | why |
|---|---|---|
| boot capture bytes | **1,318** | `R5-4`'s 1,184 plus this driver's eight marks, computed from the mark strings: `S0`/`S7` 10 bytes each, `S1`–`S6` 19 each = **134** |
| `RLXFW-ID0` | `FCE0AF22` | `RECIPE_ID`, compiled in, typed by nobody |
| `S1` | `FFC00000` | `REG-38`. **One of two genuine coin-tosses in this block**, and the other is `S3`. Both are 讀 out of the vendor's compiled code and both disagree with what `REG-13` measured at the loader prompt |
| `S2` | `0BA08000` | `REG-13`'s `SFCR2`, unchanged since the loader |
| `S3` | **`C8000000`** | 🟢 **sharpened from a hedge to an exact value, 讀 from the artefact.** The last `SFCSR` write before this driver reads it is `SFCSR_CS_H(0, 0, IOWIDTH_SINGLE)` — `ComSrlCmd_ComRead` ends with exactly that call (`801a35fc`, with `a1` and `a2` both zeroed), and `spi_regist`'s last act is `pfRead(chip, 0, 4, buf)` which goes through it. `SFCSR_CS_H` builds `lui 0xc800` = `SPI_CSB(3) \| SPI_RDY(1)`, with `LEN` and `IO_WIDTH` both 0. 🔴 **So this differs from `REG-13`'s loader-prompt `D8050000` (`LEN`=01, `CMD_BYTE`=`0x05`) — a SECOND 讀 → 量 in the same mark set, and a second coin-toss** |
| `S4` | `00000000` | the three FIPS 180-2 vectors pass |
| `S5` | `00000000` | `add_mtd_device` returns 0 |
| `S6` | `00000002` | two vendor partitions register first at `device_initcall`; mine is `late_initcall` |
| `/proc/mtd` | `mtd2: 00400000 00001000 "rtl819x-spi-pio"` | ditto |
| `wc -c < /dev/mtd2ro` | `4194304` | the whole chip through **my** read path |
| `d1_sha256` | `a9916fd8…4ce3cba` | `FLS-24`, re-derived two ways at the desk |
| `cmp_equal` / `cmp_first_diff` | `1` / `-1` | `D3` |
| `digest_bytes` / `h601_skipped` / `h601_hashed` | `4186112` / `8192` / **`0`** | the H601 guard. **The digests print only because the third is 0** |
| `n_writes` | **`0`** throughout | the number this driver exists to keep at zero |

---

## 4. The cells

### 4.1 The two invocations, and the conventions

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0`,
`OUT` = `--out bench/2026-09-07/`.

`LOOP` = `/usr/bin/python3 tools/looprun.py --mode bench --out-dir
bench/2026-09-07 --skip S2,S3,S4 --recipe-override fce0af22 --image
$FWRE_WORK/rebuild/bench-only/r55-20260907/rlxfw-r55-20260907.bin
--image-sha256 cc4e75194ff927a83e46c8b5901161f438028e12029c2c5419a15fe8f228e50a`

That leaves five bench stages and one desk assert: `S5` rescue, `S5b` burnflag,
`S6` upload, `S6b` staged-head read-back, `S7` boot, `S8` assert.

🔴 **`--skip S2,S3` is necessary, not a convenience** — `S3` assembles from the
tree `S2` stages and nothing carries that path when `S2` is skipped
(`notes/dev-loop.md` §10.3); skipping `S2` is also what makes
`--recipe-override` **required** rather than decorative. **`--skip S4` is
chosen**: every reset in this card is the `Cn-A` cell, before `looprun` starts.

🔴 Warm resets use `busybox reboot -f`, **with the `-f`** — `FW-37`.
🔴 `ping` ignores `-c` on this image (`NET-26`); no cell asks for a count.
🔴 Eleven busybox symlinks exist; anything else is `busybox <name>`. `wc` is
not one of them, so `C1-SZ` types `busybox wc`.
🔴 **Every capture carries a terminator** (`--seconds` or `--idle`);
`console-capture.py` refuses one that does not.
🔴 **No cell may contain a `'`.** Every command is typed inside a
single-quoted `--send` argument, and a shell cannot nest single quotes: a
payload written `echo 'verify 4096' > /proc/rtl819x-spi` closes the argument at
the second quote and reaches `argparse` as `echo verify` plus a stray
positional. §4.3's ladder was written with those inner quotes, so the board
would have run **`verify`** — the whole 4 MiB — where the rung asks for 4 KiB.
`echo verify 4096` writes the same bytes and needs no quoting.

⚠️ **This paragraph may not show the flag and the quote together.**
`cardcheck commands` finds a card's commands by that exact pattern, so an
*illustration* of it becomes a command the tool then tries to look up in the
image — 量, this card, first run: `36 command(s)` with one of them the ellipsis
character.

### 4.2 The rule

| capture | typed | expect | 🔴 stop if |
|---|---|---|---|
| **`Cn-A`** cold (n=1 only) | `CAP OUT Cn-A --esc 150 --esc-period 0.002 --seconds 165` | operator presses power inside the window; loader banner, then `<RealTek>` | no `<RealTek>` → the window was missed and the board is running the **vendor** firmware. Power-cycle and repeat |
| **`Cn-A`** warm (n≥2) | `CAP OUT Cn-A --send 'busybox reboot -f' --esc-after 8 --esc-period 0.002 --seconds 12` | echo, reset, `<RealTek>` | no reset → the shell is gone; power-cycle |
| **`Cn-*`** | `LOOP --cell Cn` | the board prints `RLXFW-ID0=FCE0AF22` | the burn-flag read-back is anything but `00000000` → **nothing is uploaded**, not skippable |
| **`Cn-P`** | `CAP OUT Cn-P --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 20` | §3's field table | `added 0` → read `add_rc`. **`n_writes` ≠ 0 → stop the block** |

### 4.3 Boot 1's ladder, smallest act first

The order is the point: four bytes before four megabytes, and every control
before the measurement it controls.

| cell | typed | expect | 🔴 stop if |
|---|---|---|---|
| `C1-M` | `cat /proc/mtd` | `mtd2: 00400000 00001000 "rtl819x-spi-pio"` | `mtd2` is not mine → **every mtd2 cell below is void**; do not run them |
| `C1-SZ` | `busybox wc -c < /dev/mtd2ro` | `4194304` | any other size → `add_mtd_device` took a different index; `C1-M` and this disagree and the block stops |
| `C1-EA` | `echo x > /dev/mtd2ro` | `Permission denied` | anything else → the odd-minor refusal did not fire on my device |
| `C1-TW` | `echo trywrite > /proc/rtl819x-spi ; cat /proc/rtl819x-spi` | `S-TRYW=00000001`, `n_write_refused 2`, `n_writes 0` | `0` → L2 did not refuse. **Stop the block** |
| `C1-WD` | `echo wedge > /proc/rtl819x-spi ; cat /proc/rtl819x-spi` | `S-WEDGE=00000001`, `n_state_bad 1`, `wedged 0` after | `0` → the restore guard cannot fire, so its zeros mean nothing. **Every later cell's `n_state_bad 0` is void** |
| `C1-PR` | `echo probe > /proc/rtl819x-spi ; cat /proc/rtl819x-spi` | `S-PROBE=00000000`, `n_xfer` +1, `n_pio_bytes 4` | non-zero rc → the first four bytes did not read. **Stop; do not escalate** |
| `C1-V4` | `echo verify 4096 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi` | `cmp_bytes 4096`, `cmp_equal 1`, digests printed (`h601_hashed 0`) | `cmp_first_diff ≥ 0` at 4 KiB → the two paths disagree in the first page; **stop and record, do not escalate** |
| `C1-V64` | `echo verify 65536 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi` | `cmp_bytes 65536`, `cmp_equal 1`, `h601_skipped 8192` | as above |
| `C1-VF` | `echo verify > /proc/rtl819x-spi ; cat /proc/rtl819x-spi` | **`D1` and `D3`**: `cmp_bytes 4194304`, `cmp_equal 1`, `digest_bytes 4186112`, `h601_hashed 0`, `d1_match 1` | `d1_match 0` with `cmp_equal 1` → both paths agree with each other and disagree with the dump, which is a **flash** finding and not a driver finding |
| `C1-NG` | `echo corrupt 1048576 > /proc/rtl819x-spi ; echo verify > /proc/rtl819x-spi ; cat /proc/rtl819x-spi` | **the negative control**: `cmp_first_diff 1048576`, `d1_match 0` | either does not move → `equal`/`match` are what a tool that cannot fail prints. **Every `D1`/`D3` result above is void** |
| `C1-NF` | `echo corrupt off > /proc/rtl819x-spi ; echo verify > /proc/rtl819x-spi ; cat /proc/rtl819x-spi` | back to `cmp_equal 1`, `d1_match 1` | does not come back → the corruption was not the only difference |
| `C1-F` | `cat /proc/rtl819x-spi` | the final dump: `n_writes 0`, `n_state_bad 1` (from `C1-WD` alone), `n_state_foreign` recorded | `n_state_foreign` ≠ 0 → **something else moved the controller between my transactions**, which is the isolation experiment `notes/spi-mtd-driver.md` §4 names |

⚠️ **`C1-VF` takes seconds, not milliseconds.** `FW-45`: the watchdog is armed
and petted from the vendor's TC0 handler at 100 Hz, and the driver holds a
mutex — not a spinlock — with `cond_resched()` per 4 KiB chunk, so the pet
still runs. If the board resets during `C1-VF`, that is a finding about
`FW-45` and the block stops.

### 4.3a 🔴 A mark and a field are printed by two different functions

量, from the driver's own source rather than from this card's prose:
`rtl819x_spi_write_proc()` prints **marks** and nothing else — `S-PROBE`,
`S-WEDGE`, `S-TRYW`, and `S-VRC`/`S-VDIFF`/`S-VD1` for a verify. Every other
name this card quotes — `cmp_bytes`, `cmp_equal`, `cmp_first_diff`,
`digest_bytes`, `h601_skipped`, `h601_hashed`, `d1_sha256`, `d1_match`,
`d1_d3_agree`, `n_writes`, `n_write_refused`, `n_state_bad`, `n_state_foreign`,
`n_xfer`, `n_pio_bytes`, `wedged`, `corrupt_at` — comes out of
`rtl819x_spi_read_proc()`, which only runs on a `cat`.

**As first written, eight of this ladder's twelve cells typed only an `echo`
and carried expectations no `echo` can show.** That is `bench/2026-09-06c`'s
defect ④ — *"four cells that type only `echo` and carry expectations they
cannot show"* — with eight instead of four, in the card written two days after
it was recorded. Every state-changing cell now ends with `cat /proc/rtl819x-spi`
in the same `--send`, which is `B1-U`'s shape from that same card.

### 4.3b 🔴 Four cells go SILENT for seconds, so they carry `--seconds` ALONE

`--idle N` ends a capture after N seconds of quiet. A 4 MiB traversal is quiet.

| cell | what is silent | 量 it rests on |
|---|---|---|
| `C1-SZ` | 4,194,304 B through my `mtd->read` | `FW-34`: **0.92–1.01 MB/s** over exactly this many bytes → **4.2–4.6 s** |
| `C1-VF` `C1-NG` `C1-NF` | the same, **plus** 4,194,304 B through `0xBD000000`, plus two sha256 over 4,186,112 B | window leg: `probe3` Group F, 2.075 µs/word → **2.2 s** at the loader's divisor, and `REG-38` says Linux clocks SPI **4× slower**, so **≤ 8.7 s**. sha256 on this core is 推. **Sum ≈ 16 s, upper bound ~30 s** |

So `C1-SZ` gets `--seconds 60` and the three full-verify cells get
`--seconds 120` — 4× to 7× the estimate, with **no `--idle` at all**. This is
`bench/2026-09-06c`'s `B2-BTN2` rule reaching a case it was not written for:
there the silence was a `sleep 6`, here it is the driver working. Wall time is
free; a lost `C1-VF` is the block's headline.

⚠️ **The 4× is carried from `REG-38`, which is 讀 and not 量** — `S1` is the
cell that settles it. If the window leg is *not* divided, these cells finish
sooner and nothing is harmed; the terminator is deliberately wide enough for
either answer.

### 4.4 The expansion — one line per cell, and it is what gets typed

§4.2 is the RULE and §4.3 the ladder; this is both applied. It exists because a
parameterised row is invisible to the checker: **量 2026-09-07, before this
section was written, `cardcheck commands` read `2 command(s)` for this card's
32 cells.** Seating 14's card showed `6 commands for 24 cells` and was expanded
to 29; this one was worse because §4.3's `typed` column is not in `--send` form
at all, so the tool could not see a single rung of the ladder.

量, generated from one list rather than typed, and cross-checked in **both**
directions against §5's fence by `cardnum`'s `expansion-*` and `cells-fence`
rows. Longest `--send` payload **98** characters, **0** at or over
`console-capture.py`'s 128-byte refusal, **0** containing a `'`.

量 after: **`34 command(s)`, all 34 invocable**. ⚠️ **34 is not 32 and the
difference is not a defect**: the expansion holds **31** — every cell but the
cold `C1-A`, which sends nothing — §4.2's rule table holds **2**, and the
**1** left over is the literal string inside `cardnum`'s `expansion-warm`
regex, which the tool cannot tell from a command. It tokenises to `busybox`,
which is declared, so it passes for the right reason by accident. Said here
because a reader comparing `34` with `32 cells` would otherwise have to
rediscover it.

```
#-- boot 1, cold: the operator presses power inside this window
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C1-A --esc 150 --esc-period 0.002 --seconds 165
/usr/bin/python3 tools/looprun.py --mode bench --cell C1 --out-dir bench/2026-09-07 --skip S2,S3,S4 --recipe-override fce0af22 --image /home/key/fwre-work/rebuild/bench-only/r55-20260907/rlxfw-r55-20260907.bin --image-sha256 cc4e75194ff927a83e46c8b5901161f438028e12029c2c5419a15fe8f228e50a
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C1-P --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 20
#-- boot 1 only: the ladder, smallest act first.  Every cell that changes state ends with a `cat`, because a mark and a field are printed by two different functions (4.3a).
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C1-M --send 'cat /proc/mtd' --idle 3 --seconds 20
#-- 4 MiB through MY read path: SILENT for 4.2-4.6 s (FW-34), so --seconds ALONE.  --idle 3 would end the capture inside it.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C1-SZ --send 'busybox wc -c < /dev/mtd2ro' --seconds 60
#-- the three guards, each with the cat that shows its counters
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C1-EA --send 'echo x > /dev/mtd2ro' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C1-TW --send 'echo trywrite > /proc/rtl819x-spi ; cat /proc/rtl819x-spi' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C1-WD --send 'echo wedge > /proc/rtl819x-spi ; cat /proc/rtl819x-spi' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C1-PR --send 'echo probe > /proc/rtl819x-spi ; cat /proc/rtl819x-spi' --idle 3 --seconds 20
#-- the ladder proper: 4 KiB, then 64 KiB, then 4 MiB
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C1-V4 --send 'echo verify 4096 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C1-V64 --send 'echo verify 65536 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi' --idle 3 --seconds 30
#-- 4 MiB PIO + 4 MiB window + two sha256: ~16 s of silence, upper bound ~30 s.  --seconds ALONE, and 120 is 4x the bound.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C1-VF --send 'echo verify > /proc/rtl819x-spi ; cat /proc/rtl819x-spi' --seconds 120
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C1-NG --send 'echo corrupt 1048576 > /proc/rtl819x-spi ; echo verify > /proc/rtl819x-spi ; cat /proc/rtl819x-spi' --seconds 120
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C1-NF --send 'echo corrupt off > /proc/rtl819x-spi ; echo verify > /proc/rtl819x-spi ; cat /proc/rtl819x-spi' --seconds 120
#-- the final dump: n_state_foreign is the isolation reading
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C1-F --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 20
#-- boots 2..10: warm.  They carry only -A and -P: the ten boots are the DoD's, and what the driver DOES is exercised once, above, where the ladder can be stopped at any rung.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C2-A --send 'busybox reboot -f' --esc-after 8 --esc-period 0.002 --seconds 12
/usr/bin/python3 tools/looprun.py --mode bench --cell C2 --out-dir bench/2026-09-07 --skip S2,S3,S4 --recipe-override fce0af22 --image /home/key/fwre-work/rebuild/bench-only/r55-20260907/rlxfw-r55-20260907.bin --image-sha256 cc4e75194ff927a83e46c8b5901161f438028e12029c2c5419a15fe8f228e50a
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C2-P --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C3-A --send 'busybox reboot -f' --esc-after 8 --esc-period 0.002 --seconds 12
/usr/bin/python3 tools/looprun.py --mode bench --cell C3 --out-dir bench/2026-09-07 --skip S2,S3,S4 --recipe-override fce0af22 --image /home/key/fwre-work/rebuild/bench-only/r55-20260907/rlxfw-r55-20260907.bin --image-sha256 cc4e75194ff927a83e46c8b5901161f438028e12029c2c5419a15fe8f228e50a
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C3-P --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C4-A --send 'busybox reboot -f' --esc-after 8 --esc-period 0.002 --seconds 12
/usr/bin/python3 tools/looprun.py --mode bench --cell C4 --out-dir bench/2026-09-07 --skip S2,S3,S4 --recipe-override fce0af22 --image /home/key/fwre-work/rebuild/bench-only/r55-20260907/rlxfw-r55-20260907.bin --image-sha256 cc4e75194ff927a83e46c8b5901161f438028e12029c2c5419a15fe8f228e50a
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C4-P --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C5-A --send 'busybox reboot -f' --esc-after 8 --esc-period 0.002 --seconds 12
/usr/bin/python3 tools/looprun.py --mode bench --cell C5 --out-dir bench/2026-09-07 --skip S2,S3,S4 --recipe-override fce0af22 --image /home/key/fwre-work/rebuild/bench-only/r55-20260907/rlxfw-r55-20260907.bin --image-sha256 cc4e75194ff927a83e46c8b5901161f438028e12029c2c5419a15fe8f228e50a
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C5-P --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C6-A --send 'busybox reboot -f' --esc-after 8 --esc-period 0.002 --seconds 12
/usr/bin/python3 tools/looprun.py --mode bench --cell C6 --out-dir bench/2026-09-07 --skip S2,S3,S4 --recipe-override fce0af22 --image /home/key/fwre-work/rebuild/bench-only/r55-20260907/rlxfw-r55-20260907.bin --image-sha256 cc4e75194ff927a83e46c8b5901161f438028e12029c2c5419a15fe8f228e50a
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C6-P --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C7-A --send 'busybox reboot -f' --esc-after 8 --esc-period 0.002 --seconds 12
/usr/bin/python3 tools/looprun.py --mode bench --cell C7 --out-dir bench/2026-09-07 --skip S2,S3,S4 --recipe-override fce0af22 --image /home/key/fwre-work/rebuild/bench-only/r55-20260907/rlxfw-r55-20260907.bin --image-sha256 cc4e75194ff927a83e46c8b5901161f438028e12029c2c5419a15fe8f228e50a
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C7-P --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C8-A --send 'busybox reboot -f' --esc-after 8 --esc-period 0.002 --seconds 12
/usr/bin/python3 tools/looprun.py --mode bench --cell C8 --out-dir bench/2026-09-07 --skip S2,S3,S4 --recipe-override fce0af22 --image /home/key/fwre-work/rebuild/bench-only/r55-20260907/rlxfw-r55-20260907.bin --image-sha256 cc4e75194ff927a83e46c8b5901161f438028e12029c2c5419a15fe8f228e50a
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C8-P --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C9-A --send 'busybox reboot -f' --esc-after 8 --esc-period 0.002 --seconds 12
/usr/bin/python3 tools/looprun.py --mode bench --cell C9 --out-dir bench/2026-09-07 --skip S2,S3,S4 --recipe-override fce0af22 --image /home/key/fwre-work/rebuild/bench-only/r55-20260907/rlxfw-r55-20260907.bin --image-sha256 cc4e75194ff927a83e46c8b5901161f438028e12029c2c5419a15fe8f228e50a
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C9-P --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C10-A --send 'busybox reboot -f' --esc-after 8 --esc-period 0.002 --seconds 12
/usr/bin/python3 tools/looprun.py --mode bench --cell C10 --out-dir bench/2026-09-07 --skip S2,S3,S4 --recipe-override fce0af22 --image /home/key/fwre-work/rebuild/bench-only/r55-20260907/rlxfw-r55-20260907.bin --image-sha256 cc4e75194ff927a83e46c8b5901161f438028e12029c2c5419a15fe8f228e50a
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-07/C10-P --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 20
```

### 4.5 The numbers this card states, and where each is re-derived FROM

🔴 **Every row names a FROZEN artefact or this card itself.** `RUNSHEET.md`'s
lifecycle rule 2: seating 14's card pointed `cardnum` rows at a live source
file and went red the next time that driver was edited, for a reason that had
nothing to do with the seating. The three files beside the image never move.

⚠️ **`d1_sha256` is deliberately NOT here.** It is a digest over a *subset* of
the flash dump — `H601`'s complement — which `cardnum` has no expression for,
and the dump may not be committed. It is 量 already, as `SPEC.md` `FLS-24`.

```cardnum
img-bytes	1039360	size /home/key/fwre-work/rebuild/bench-only/r55-20260907/rlxfw-r55-20260907.bin
img-sha16	cc4e75194ff927a8	sha256-16 /home/key/fwre-work/rebuild/bench-only/r55-20260907/rlxfw-r55-20260907.bin
vmlinux-bytes	4013779	size /home/key/fwre-work/rebuild/bench-only/r55-20260907/vmlinux
vmlinux-sha16	5e63b426e59c3a04	sha256-16 /home/key/fwre-work/rebuild/bench-only/r55-20260907/vmlinux
map-bytes	374809	size /home/key/fwre-work/rebuild/bench-only/r55-20260907/System.map
map-sha16	8430039aa444f9df	sha256-16 /home/key/fwre-work/rebuild/bench-only/r55-20260907/System.map
d4-write-page	0	count /home/key/fwre-work/rebuild/bench-only/r55-20260907/System.map ^[0-9a-f]{8} [a-zA-Z] rtl819x_spi_write_page$
d4-erase-sector	0	count /home/key/fwre-work/rebuild/bench-only/r55-20260907/System.map ^[0-9a-f]{8} [a-zA-Z] rtl819x_spi_erase_sector$
d4-write-init	0	count /home/key/fwre-work/rebuild/bench-only/r55-20260907/System.map ^[0-9a-f]{8} [a-zA-Z] rtl819x_spi_write_init$
map-late-initcall	1	count /home/key/fwre-work/rebuild/bench-only/r55-20260907/System.map ^[0-9a-f]{8} t __initcall_rtl819x_spi_init7$
map-add-mtd-device	1	count /home/key/fwre-work/rebuild/bench-only/r55-20260907/System.map ^[0-9a-f]{8} [A-Za-z] add_mtd_device$
map-vendor-pio	1	count /home/key/fwre-work/rebuild/bench-only/r55-20260907/System.map ^[0-9a-f]{8} [A-Za-z] mtd_spi_read$
map-shash-final	1	count /home/key/fwre-work/rebuild/bench-only/r55-20260907/System.map ^[0-9a-f]{8} [A-Za-z] crypto_shash_final$
expansion-captures	32	count bench/2026-09-07/PREDICTIONS-B14-block13.md ^/usr/bin/python3 tools/console-capture[.]py capture .*--out bench/2026-09-07/C[0-9]+-
expansion-loops	10	count bench/2026-09-07/PREDICTIONS-B14-block13.md ^/usr/bin/python3 tools/looprun[.]py --mode bench --cell C[0-9]+ --out-dir
expansion-cold	1	count bench/2026-09-07/PREDICTIONS-B14-block13.md --out bench/2026-09-07/C[0-9]+-A --esc 150
expansion-warm	9	count bench/2026-09-07/PREDICTIONS-B14-block13.md --out bench/2026-09-07/C[0-9]+-A --send 'busybox reboot -f'
expansion-silent	4	count bench/2026-09-07/PREDICTIONS-B14-block13.md -{2}send '[^']*' --seconds [0-9]+$
cells-fence	32	count bench/2026-09-07/PREDICTIONS-B14-block13.md ^bench/2026-09-07/C[0-9]+-[A-Z0-9]+$
send-over-127	0	count bench/2026-09-07/PREDICTIONS-B14-block13.md -{2}send '[^']{128,}'
send-inner-quote	0	count bench/2026-09-07/PREDICTIONS-B14-block13.md ^/usr/bin/python3 .*-{2}send '[^']*'[^ ]
```

🔴 **`expansion-silent` and `send-inner-quote` are the two rows that turn this
card's two worst defects into arithmetic.** The first counts the cells that
carry `--seconds` with no `--idle` and requires exactly **4**; the second
requires **0** expansion lines whose `--send` payload closes early. Both were
real: as first written, four cells would have had their captures ended inside a
4 MiB traversal, and `C1-V4`/`C1-V64` would have run the **whole chip** instead
of their rung.

---

## 5. The fence

```cells
bench/2026-09-07/C1-A
bench/2026-09-07/C1-P
bench/2026-09-07/C1-M
bench/2026-09-07/C1-SZ
bench/2026-09-07/C1-EA
bench/2026-09-07/C1-TW
bench/2026-09-07/C1-WD
bench/2026-09-07/C1-PR
bench/2026-09-07/C1-V4
bench/2026-09-07/C1-V64
bench/2026-09-07/C1-VF
bench/2026-09-07/C1-NG
bench/2026-09-07/C1-NF
bench/2026-09-07/C1-F
bench/2026-09-07/C2-A
bench/2026-09-07/C2-P
bench/2026-09-07/C3-A
bench/2026-09-07/C3-P
bench/2026-09-07/C4-A
bench/2026-09-07/C4-P
bench/2026-09-07/C5-A
bench/2026-09-07/C5-P
bench/2026-09-07/C6-A
bench/2026-09-07/C6-P
bench/2026-09-07/C7-A
bench/2026-09-07/C7-P
bench/2026-09-07/C8-A
bench/2026-09-07/C8-P
bench/2026-09-07/C9-A
bench/2026-09-07/C9-P
bench/2026-09-07/C10-A
bench/2026-09-07/C10-P
```

**32 cells.** Boots 2–10 are warm resets and carry only `-A` and `-P`: the ten
boots are for the DoD's *ten boots without an oops*, and the thing the driver
does is exercised once, on boot 1, where the ladder can be stopped at any rung.

---

## 6. What this block cannot establish, written now

1. **The other 8,192 bytes.** `D2` is a rule. The `FLR` bracket does not run
   this seating, so the flash bracket stays **1,024 / 4,194,304 = 0.0244 %**.
2. **Layer L3.** `mtdchar.c:94`'s `!MTD_WRITEABLE` refusal has never fired
   anywhere in this project — every vendor partition sets the flag — and
   observing it needs an **even** char minor over my device, which
   `mkinitramfs.py` refuses to declare and is right to. `C1-TW` observes L2,
   the layer behind it. L3 stays 讀.
3. **That my transaction is the fastest available.** It is the vendor's order
   at Fast Read with one dummy byte. Nothing here times anything.
4. **Anything about `SFDR2`.** Still unread, deliberately.

---

## 7. 🔒 FROZEN — 2026-09-07, forty-second segment, before power

**This paragraph is the last edit to this file.** Every capture under
`bench/2026-09-07/` is newer than it, which is what
`tools/check-predictions.py` reads. Corrections after this go in a new
`CORRECTIONS-block13.md`, never in here — `RUNSHEET.md`'s lifecycle rule 1.

The freeze order ran in the order it is written in, and every step is a
reading rather than a claim:

| step | 量 |
|---|---|
| `RECIPE_ID` re-derived from the live `config/` | **`fce0af22`**, equal to §1. Three sources: the by-hand formula, the build's own `manifest.tsv`, and §1. **No rebuild needed** |
| `tools/spec-check.py` | **rc 0, 0 findings** — run FIRST, so that fixing it cannot destroy the mtime evidence the freeze creates |
| `cardcheck commands` | **34 of 34 invocable** |
| `cardcheck numbers` | **21 of 21 re-derived** |
| `check-predictions` | **`0 of 32`** — the correct answer for a card whose seating has not happened |

🔴 **Eight defects were found between writing and freezing, and only one of
them was visible to CI.** They are listed because seven of the eight are in
classes this repository had already recorded, and a card that is merely fixed
teaches nothing:

1. An unescaped `|` inside a code span in §3's `S3` row — `spec-check` `C8`.
   The only one CI could see, and it went red on GitHub. Second instance in one
   day. The desk sweep missed it because the card was **committed while the
   sweep was running**, which changed the tracked-file population `spec-check`
   reads without changing any file's content.
2. The `cells` fence was `bench/2026-09-06c`'s **malformed shape, copied** —
   several prefixes per line and no directory separator. `check-predictions`
   refused with rc 2 (`N8` and `N9`). Unrepaired, it would have printed a
   number that reads exactly like the correct pre-seating answer.
3. No `cardnum` fence at all: `cardcheck numbers` refused with rc 2.
4. §4.4 unwritten, so `cardcheck commands` read **`2 command(s)`** for 32
   cells — worse than seating 14's `6 for 24`, because §4.3's `typed` column is
   not in `--send` form and the tool could not see the ladder at all.
5. §4.3 typed `echo 'verify 4096' > …`. Inner single quotes cannot survive a
   single-quoted `--send`, and the board would have run the **whole 4 MiB**
   where the rung asks for 4 KiB — silently, and looking like a pass.
6. **Eight** cells typed only an `echo` and carried expectations only a `cat`
   can print. `bench/2026-09-06c` recorded that defect with four.
7. **Four** cells go silent for seconds while the driver reads 4 MiB, and
   carried `--idle 3`, which ends a capture inside the silence. This is
   `B2-BTN2`'s rule reaching a case it was not written for.
8. The directory name was a prediction and it was wrong; §0 has the
   measurement.

⚠️ **Seven of the eight were found by running the tools, not by re-reading the
card**, and the eighth — the ellipsis that `cardcheck commands` reported as a
command — was created by the paragraph written to explain defect 5. An
illustration of a pattern the tool matches becomes an instance of it.
