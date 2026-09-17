# Block 26 — the first Linux-state reading of a switch register on this device

**Frozen before power to these cells.** Seating 26, `bench/2026-09-17b/`,
**declared date 2026-09-17**. Same power cycle as blocks 24 and 25.

---

## 0. What this block is, and the number that makes it worth a boot

`R6-0`'s census, 量 2026-09-17: `grep -rl BB804 bench/` returns **41 files in
four directories, newest `bench/2026-08-25`**. **No word in `0xBB804xxx` has
ever been read under Linux on this device**, twenty-three seatings in, and the
mechanism is known — `FW-46` (this busybox has no `devmem`) and no driver of
mine touches the switch.

`R6-1`'s DoD says *"every register the census marked undetermined under Linux
is read at least once"*. Block 24 read them at the loader prompt. **This block
is the other half, and it is what makes block 24's numbers a contrast rather
than a list.**

### 0.1 The instrument, and it needs no new image

讀 `rtl865x_proc_debug.c:4115-4175`: `proc_mem_write()` runs `simple_strtol` on
the address and calls `memDump()`, with **no bounds check**. The entry is gated
on `CONFIG_RTL_DEBUG_TOOL`, which is a `default y` with no prompt string in
**rlxfw's own board template** (`NET-27`), so it is compiled into the image
already on disk. 🟢 **The vendor's own positive control**: `/bin/dw` on this
unit's stock rootfs is a 207-byte shell script whose entire body is
`echo read $1 4 > /proc/rtl865x/memory`.

🔴 **`CONFIG_PRINTK` is not set in this image, which could have killed it** —
but `memDump` was disassembled out of the real artefact and uses **nine
`jal panic_printk` and zero `jal printk`**, and 讀 `kernel.h:265-277` says
`printk` degrades to a no-op inline while `panic_printk` stays real. **So the
output reaches the console.** ⚠️ It reaches the **console**, not the writing
process's stdout, which is why every cell below captures rather than pipes.

### 0.2 🔴 Hazards, pre-registered

* **`read <a> 4` touches twenty bytes**, `a+0/4/8/12/16` — not sixteen. Every
  address below is chosen knowing that.
* 🔴 **`PSRP` bit 8 is read-to-clear** (`NET-11`, 量 ×4 including block 24's own
  `C10`→`C11`). `C1-LXSW28` consumes the latch. It is read **once**.
* 🔴 **`write <a> <d>` on the same file is an unbounded poke two characters away
  from `read`.** No cell here types `write`, and a `cardnum` row asserts it.
* The handler's buffer is `tmpbuf[64]`; every command below is under 64
  characters.

---

## 1. The boot

`looprun --mode bench` drives reset → rescue → burn-flag read-back → host link
→ upload → staged-head read-back → boot → assert, with no operator gap. Image
**`p11e`**, `RECIPE_ID` **`bb684eb0`**, nfjrom **1,072,128 bytes**, sha256
**`dc4fae0f53ad926e91b97a3b138b9289df51e179742086978b0087e982d6625b`**
(re-derived on this desk today, not copied).

🔴 **This is the point of no return for loader state, and it is deliberately
last.** `CLK-17`: `TC0CNT` reads 14,286,057 Hz at the prompt and 200,005 Hz
under Linux, so every loader-state question had to be asked first. Blocks 24
and 25 asked them.

⚠️ `looprun`'s own four captures are **outside this card's fence**: it asserts
over them itself and `S8` is its verdict, not this card's.

---

## 2. The predictions

### 2.1 🟢 The one that makes this a contrast — `C1-LXSW28`

`PSRP0`–`PSRP4` at `0xBB804128`. **Predict `PSRP3` = `000010F9`** and the other
four `000010E0`, **identical to block 24's `C11-PS0b` two hours earlier at the
loader prompt**, because the cable has not moved and `NET-30` measured that this
peer's link does not drop.

> **否證** — if `PSRP3` differs, then either the vendor driver reprograms port
> status (which it cannot; it is a status register), or the link changed across
> the boot. Either is a finding.

⚠️ Bit 8 may be **1** here: the boot resets the switch, and a reset plus
re-negotiation is exactly the `LinkDownEventFlag` event `NET-11` describes. A
`000011F9` is **not** a refutation of the prediction above; the prediction is
about bits 7:0 other than bit 8.

### 2.2 The ones that are expected to MOVE, and that is the measurement

| cell | address | loader-state (量, block 24) | under Linux |
|---|---|---|---|
| `C2-LXSW00` | `0xBB804000` `MACCR` | `804A0185` | 推 — **changes**; the vendor driver's `rtl865x_initAsicL2()` reconfigures the MAC |
| `C3-LXSW100` | `0xBB804100` `PITCR`+`PCRP0`–`3` | `00000000 007F0039 047F0039 087F0039` | 推 — `PCRP` changes; `PITCR` stays `00000000` (`NET-19`: the strap branch that sets bit 0 does not run on this board) |
| `C4-LXSWA08` | `0xBB804A08` `PVCR0`–`3` | `00080008` ×4 | 🔴 推 — **changes**, because the vendor driver sets up VLANs and `NET-04` records `vid 8` for the WAN port and `vid 9` for the other four. **`PVCR0` is the register `R6-6` is about, and if it does not move, `R6-6`'s whole premise about where PVID lives is wrong** |
| `C5-LXSW234` | `0xBB804234` `MEMCR` | `00007F7F` | 推 — unchanged. If it moves, the second `0x7F` in bits 15:8 is software-written and block 24's 推 about two port masks gains a mechanism |

> 🔴 **否證, and it applies to the whole block** — if **every** register reads
> exactly what the loader left, then either this `/proc` path is not reaching
> the hardware, or the vendor driver does not touch the switch core at all.
> **`C1`'s `PSRP3` is what separates those two**: a `000010F9` that matches the
> loader proves the path reads real hardware, because that value is not
> something a broken path would invent.

### 2.3 `C6-PORT` — the same file, the same power cycle

`cat /proc/rtl865x/port_status`. **Predict 585 bytes**, and `Port3 … LinkUp |
NWay Mode Enabled … Speed 100M`, `CPUPort … NWay Mode Disabled … Speed 1G`,
five ports `LinkDown` — byte-identical to `bench/2026-09-17/C2-PORT.log`.

🟢 That capture is what `NET-31` records, and it came from a **different**
seating. Taking it again in the same power cycle as block 24's loader-side
`PSRP` read turns an eighteen-field cross-state agreement into one that does
not span a power cycle.

### 2.4 `C7-M0` — the flash bracket, and today it is not free any more

`echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map`.

**Predict byte-identical to `bench/2026-09-10/C1-M0`**, digest `b3d3d7d0…`,
which `SPEC.md` `FLS-26` records as agreeing across four maps and two seatings.

🔴 **This seating has something those did not**: the vendor firmware executed on
this part for about five minutes this morning (block 24 § 0.3, 量 by the ESC
echo signature). `FLS-26`'s attribution bracket is exactly the instrument for
that interval, and `CLAUDE.md`'s sixteenth update already named this cell as the
zero-cost closure. **A difference here is this seating's most important
result and it would not be about my code.**

---

## 3. The guards

* **Zero flash writes.** No `FLW`, no `EW`, no `EB`, no burn. `AUTOBURN` is set
  to `0` by `looprun`'s `S5` **because an upload requires it**, and `S5b`
  aborts unless `0x8040D4A0` reads `00000000` — two sources, which is what
  `C-6` measured disagreeing once.
* 🔴 **No `write` to `/proc/rtl865x/memory`.** Asserted by a `cardnum` row.
* Every `--send` is under 64 characters and single-quoted, with no `"`, no
  backtick and no `$`.
* Every cell carries `--seconds`. No cell uses `--idle` shorter than a `sleep`
  it contains, because no cell contains a `sleep`.

---

## 4. What this block does NOT claim

1. It does not show my driver doing anything. Every reading here is taken
   **through the vendor's** `rtl819x` and its `/proc`, which is the point: it
   is the **contrast** `R6-1` needs, not a driver result.
2. A register that moves is not a register I understand. This block records
   values, not field semantics.
3. It does not close `FLS-26`'s ledger — 99.61 % proven identical, 0.195 %
   proven different, 0.195 % undetermined stands. `map 0` covers group 0.
4. It says nothing about `CPU-45`, which block 25 answered at the prompt.

---

## 5. The cells

```
#-- H+L. reset -> rescue -> burnflag -> hostlink -> upload -> staged head -> boot -> assert, no operator gap.
/usr/bin/python3 tools/looprun.py --mode bench --cell p11e --out-dir bench/2026-09-17b --port /dev/ttyUSB0 --host 10.1.1.1 --skip S2,S3 --recipe-override bb684eb0 --image /home/key/fwre-work/rebuild/bench-only/p11e-work-20260917/p11e-20260917/kroot/rtkload/nfjrom --image-sha256 dc4fae0f53ad926e91b97a3b138b9289df51e179742086978b0087e982d6625b
```

```
#-- S. PSRP0..PSRP4 under Linux.  THE FIRST 0xBB804xxx WORD EVER READ UNDER LINUX ON THIS DEVICE.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17b/C1-LXSW28 --send 'echo read 0xBB804128 4 > /proc/rtl865x/memory' --idle 3 --seconds 20
#-- S. MACCR and the MDIO pair.  Loader left 804A0185.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17b/C2-LXSW00 --send 'echo read 0xBB804000 4 > /proc/rtl865x/memory' --idle 3 --seconds 20
#-- S. PITCR and PCRP0..3.  Loader left 00000000 007F0039 047F0039 087F0039.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17b/C3-LXSW100 --send 'echo read 0xBB804100 4 > /proc/rtl865x/memory' --idle 3 --seconds 20
#-- S. PVCR0..3, the PVID registers R6-6 is about.  Loader left 00080008 four times.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17b/C4-LXSWA08 --send 'echo read 0xBB804A08 4 > /proc/rtl865x/memory' --idle 3 --seconds 20
#-- S. MEMCR.  Loader left 00007F7F, whose top half no source explains.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17b/C5-LXSW234 --send 'echo read 0xBB804234 4 > /proc/rtl865x/memory' --idle 3 --seconds 20
#-- S. the whole port file, this time in the SAME power cycle as the loader-side PSRP read.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17b/C6-PORT --send 'cat /proc/rtl865x/port_status' --idle 3 --seconds 25
#-- S. FLS-26's attribution bracket for this morning's ~5 minutes of vendor firmware.  A difference here is the headline.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17b/C7-M0 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines' --seconds 180
```

### 5.1 The numbers this card states, and where each is re-derived FROM

```cardnum
cells-fence	7	count bench/2026-09-17b/PREDICTIONS-B27-block26.md ^bench/2026-09-17b/C[0-9]+-[A-Za-z0-9]+$
image-bytes	1072128	size /home/key/fwre-work/rebuild/bench-only/p11e-work-20260917/p11e-20260917/kroot/rtkload/nfjrom
image-sha16	dc4fae0f53ad926e	sha256-16 /home/key/fwre-work/rebuild/bench-only/p11e-work-20260917/p11e-20260917/kroot/rtkload/nfjrom
declared-date	1	count bench/2026-09-17b/PREDICTIONS-B27-block26.md [*][*]declared date 2026-09-17[*][*]
send-over-127	0	count bench/2026-09-17b/PREDICTIONS-B27-block26.md -{2}send '[^']{128,}'
no-flr	0	count bench/2026-09-17b/PREDICTIONS-B27-block26.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-17b/PREDICTIONS-B27-block26.md -{2}send '[^']*(EW |EB |FLW )
no-mem-poke	0	count bench/2026-09-17b/PREDICTIONS-B27-block26.md -{2}send '[^']*echo write
no-autoexec	0	count bench/2026-09-17b/PREDICTIONS-B27-block26.md ^/usr/bin/python3 .*(allow-autoexec|boot[.]img)
```

---

## 6. The fence

```cells
bench/2026-09-17b/C1-LXSW28
bench/2026-09-17b/C2-LXSW00
bench/2026-09-17b/C3-LXSW100
bench/2026-09-17b/C4-LXSWA08
bench/2026-09-17b/C5-LXSW234
bench/2026-09-17b/C6-PORT
bench/2026-09-17b/C7-M0
```

⚠️ `7 of 7` means *the cells this card types at the shell*. `looprun`'s four
captures are outside it on purpose, and so is its verdict.
