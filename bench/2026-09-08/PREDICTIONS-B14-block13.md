# Block 13 — `R5-5`: a read-only MTD device of mine, driven by programmed I/O

**Written 2026-09-07, forty-first segment, at the desk, before power.**
`R5-5`'s bench half. The desk half is done and its artefacts are frozen (§1).

🔴 **THIS CARD IS NOT FROZEN AND ITS DIRECTORY NAME IS A PREDICTION.**
`bench/2026-09-08` names the day the power cycle is expected to happen, not a
day anything has been measured on. Before power: measure the date on all three
sides, and if it is not 2026-09-08, rename the directory and re-expand §4.3 —
`RUNSHEET.md` § "Three rules about the card's lifecycle, 2026-09-06" rules 1
and 3 are the owner of that procedure and it is not copied here.

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

### 4.1 Conventions, and the three that cost a cycle before

🔴 Warm resets use `busybox reboot -f`, **with the `-f`** — `FW-37`.
🔴 `ping` ignores `-c` on this image (`NET-26`); no cell asks for a count.
🔴 Eleven busybox symlinks exist; anything else is `busybox <name>`.
🔴 **Every capture carries a terminator** (`--seconds` or `--idle`);
`console-capture.py` refuses one that does not.

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
| `C1-TW` | `echo trywrite > /proc/rtl819x-spi` | `S-TRYW=00000001`, `n_write_refused 2`, `n_writes 0` | `0` → L2 did not refuse. **Stop the block** |
| `C1-WD` | `echo wedge > /proc/rtl819x-spi` | `S-WEDGE=00000001`, `n_state_bad 1`, `wedged 0` after | `0` → the restore guard cannot fire, so its zeros mean nothing. **Every later cell's `n_state_bad 0` is void** |
| `C1-PR` | `echo probe > /proc/rtl819x-spi` | `S-PROBE=00000000`, `n_xfer` +1, `n_pio_bytes 4` | non-zero rc → the first four bytes did not read. **Stop; do not escalate** |
| `C1-V4` | `echo 'verify 4096' > /proc/rtl819x-spi` | `cmp_bytes 4096`, `cmp_equal 1`, digests printed (`h601_hashed 0`) | `cmp_first_diff ≥ 0` at 4 KiB → the two paths disagree in the first page; **stop and record, do not escalate** |
| `C1-V64` | `echo 'verify 65536' > /proc/rtl819x-spi` | `cmp_bytes 65536`, `cmp_equal 1`, `h601_skipped 8192` | as above |
| `C1-VF` | `echo verify > /proc/rtl819x-spi` | **`D1` and `D3`**: `cmp_bytes 4194304`, `cmp_equal 1`, `digest_bytes 4186112`, `h601_hashed 0`, `d1_match 1` | `d1_match 0` with `cmp_equal 1` → both paths agree with each other and disagree with the dump, which is a **flash** finding and not a driver finding |
| `C1-NG` | `echo 'corrupt 1048576' > /proc/rtl819x-spi` then `echo verify` | **the negative control**: `cmp_first_diff 1048576`, `d1_match 0` | either does not move → `equal`/`match` are what a tool that cannot fail prints. **Every `D1`/`D3` result above is void** |
| `C1-NF` | `echo 'corrupt off' > /proc/rtl819x-spi` then `echo verify` | back to `cmp_equal 1`, `d1_match 1` | does not come back → the corruption was not the only difference |
| `C1-F` | `cat /proc/rtl819x-spi` | the final dump: `n_writes 0`, `n_state_bad 1` (from `C1-WD` alone), `n_state_foreign` recorded | `n_state_foreign` ≠ 0 → **something else moved the controller between my transactions**, which is the isolation experiment `notes/spi-mtd-driver.md` §4 names |

⚠️ **`C1-VF` takes seconds, not milliseconds.** `FW-45`: the watchdog is armed
and petted from the vendor's TC0 handler at 100 Hz, and the driver holds a
mutex — not a spinlock — with `cond_resched()` per 4 KiB chunk, so the pet
still runs. If the board resets during `C1-VF`, that is a finding about
`FW-45` and the block stops.

### 4.4 The expansion — one line per cell, and it is what gets typed

To be written at freeze, expanded from §4.2 and §4.3 and cross-checked in
**both** directions against §5's `cells` fence. It is not written now because
the directory name is still a prediction and every line carries it.

---

## 5. The fence

```cells
C1-A C1-P C1-M C1-SZ C1-EA C1-TW C1-WD C1-PR C1-V4 C1-V64 C1-VF C1-NG C1-NF C1-F
C2-A C2-P C3-A C3-P C4-A C4-P C5-A C5-P C6-A C6-P
C7-A C7-P C8-A C8-P C9-A C9-P C10-A C10-P
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
