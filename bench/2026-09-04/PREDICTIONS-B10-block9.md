# PREDICTIONS — Session B10, `R5-3a`, block 9: the interrupt path, four gates at a time, and the first real delivery

**Written at the desk on 2026-09-04, thirty-second segment, before power.** Every
number below was re-derived on this host today from a file already committed or
an image already staged. Nothing here is conditional on a reading taken at the
bench.

🔴 **Not to be edited after the first capture lands.** Fixing a typo moves the
mtime and `tools/check-predictions.py` fails, correctly. Corrections go in
`CORRECTIONS-block9.md`, beside this one.

⚠️ **The directory name is a prediction and the seating date is not known.**
This block is written on 2026-09-04 and lives in `bench/2026-09-04/`. If the
seating lands on another day the directory is renamed **before power** and the
rename is recorded as a deviation — seating 8's Deviation 1, walked twice
already, cost known.

🔴 **This block runs LAST on its seating**, and that is the whole safety
argument. See § 2.

🔴 **This block issues no `FLR`, no `EW`, no `EB`, no `FLW` and no burn.** It
does upload, to **RAM** (`LOADADDR 80500000`). It adds **zero** bytes to the
flash bracket's coverage, which stands at 1,024 of 4,194,304 = **0.0244 %**, and
*not one flash byte is written* is exactly as unsayable after this seating as
before it. Said here so that a block with no bracket is a recorded decision
rather than an omission. **The `FLR` pre-read containment rule is not inherited
by this card**: there is no `FLR` row to attach it to.

**One power cycle.** Cells are `TI-*`, a stem no directory under `bench/` uses.

---

## 0. What this block is, in one paragraph

`docs/interrupt-map.md` § 3.1 says a TC1 interrupt crosses **seven** gates in
three register files. Seating 11 armed a **counter** for 703 seconds and never
armed an **interrupt** — `rtl819x_tc1_arm()` writes `TCCNR` and `TC1DATA` and
never touches `TCIR` bit 30. This block walks the remaining gates one at a time,
in the order § 3.3 sets, with a separate `/proc` write and a separate `cat` for
each, so that a wedge costs the rest of a seating and not the step before it.

🟢 **The first three steps cannot deliver an interrupt, and that is measured
rather than argued.** `RUNSHEET` `C5` (量, seating 1, **2026-08-24** — fourteen
days before the question existed) cleared `GIMR` bit 8 **by hand** and watched
`GISR` go `88000004` → `88000104` → `88000004`. On this die a `GIMR` mask stops
*delivery* and not *latching*. `GIMR` bit 9 stays clear through `TI-1`…`TI-4`.

---

## 1. The image, staged and pinned

| | |
|---|---|
| file | `$FWRE_WORK/rebuild/bench-only/r53b-20260904/rlxfw-r53b-20260904.bin` |
| bytes | **1,032,192** |
| sha256 | `b1273e55552603bf3a7984435aebff3480640f4a998f9587574100d569c12453` |
| `RECIPE_ID` | **`69ee7dea`** — the board must print `RLXFW-ID0=69EE7DEA` |
| driver | `rtl819x-timer` **2.0** (1.0 was seating 11's) |
| `vmlinux` sha256 | `3246e89fbf1eb845…`, 3,974,472 bytes |

🔴 **`RLXFW-ID0=` and `rtl819x-tc1` each appear ONCE in the uncompressed
`vmlinux` and ZERO times in the `nfjrom`.** That is compression, not absence —
seating 11 recorded the same pair — and it is written here so that a `grep` of
the uploaded file is not mistaken for a check of the image.

⚠️ **The image is 1,032,192 bytes and so was the previous build of this same
tree, with a different sha256.** 量 today: `vmlinux_img.gz` differs by 332
bytes between them while `nfjrom` does not move. **So the image size is not an
identity**; the sha256 is. 推 for the mechanism (the vendor `rtkload` Makefile
pads), and the experiment that would settle it is reading that Makefile — not
done, not needed here.

### 1.1 The same thing happened one layer up, and it is worth one line

量: two `vmlinux` builds of this tree, differing by a real driver change, both
report **3,974,472 bytes**. `.text` +380, `.rodata` +128, `__param` −128, and
the last four sections keep identical file offsets **and** sizes, so the ELF
ends at the same byte. **A file size is not a content measure at either layer.**

---

## 2. Where this block sits on the seating, and why LAST converts its worst case to zero

`TI-5` installs an interrupt handler and lets the interrupt controller deliver
to it. The worst case is not a brick and not a flash write: it is **the board
wedging after a shell has been reached**, and the cost of that is *the rest of
the seating*. Running this block last makes "the rest of the seating" empty.

**The three guards, in the order they would fire:**

1. 🟢 `TI-1`…`TI-4` cannot deliver anything (`GIMR` bit 9 clear, `C5`).
2. 🔴 **`reqirq` REFUSES with `-EPERM` unless the driver has itself watched
   `ackip` take `TC1IP` from 1 to 0.** 讀 `arch/rlx/bsp/irq.c`: the ICTL
   `irq_chip`'s `.mask_ack` is `bsp_ictl_irq_mask`, which masks and does **not**
   ack the device; 讀 `kernel/irq/chip.c` `handle_level_irq()`: the source is
   unmasked again after the handler returns unless `IRQ_DISABLED` is set. So a
   handler that cannot clear `TC1IP` re-triggers immediately. **The precondition
   is checked by the driver and not by this card**, because a stop-if a human
   reads off a 38400-baud capture after forty minutes at the bench is a rule
   whose correctness depends on the experiment coming out the expected way.
3. 🔴 **The handler carries the same guard at run time.** It clears `TC1IP`,
   reads it back, and calls `disable_irq_nosync()` if the bit is still set —
   which sets the exact flag `handle_level_irq()` consults before unmasking. An
   interrupt storm becomes `irq_stuck=1` in `/proc`.

**What none of them can do, stated before the seating rather than after:** none
saves a handler that *hangs*; none acts before the first delivery, so if merely
unmasking wedges the part the guard never runs; and `ackip` proving
write-1-to-clear at one instant is **n = 1** and does not prove it at every
instant.

---

## 3. Before power

| | |
|---|---|
| `AUTOBURN` at `0x8040D4A0` | must read `00000000` before any `put` (`RUNSHEET` `G2`/`H1a`; `C-6` is why the loader's echo is a second source and not the same one) |
| the image | the sha256 in § 1, checked on the host before upload |
| the id | `RLXFW-ID0=69EE7DEA` — computed by the build, typed by nobody |
| this block's position | last |

---

## 4. The cells

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0`,
`OUT` = `--out bench/2026-09-04/`. Every row carries a terminator;
`console-capture.py` refuses a capture with neither `--seconds` nor `--idle`.
🔴 **Rows with a `sleep` use `--seconds` ALONE** — a `sleep` on the board is
silence, and `--idle` would cut the capture in the middle of the cell.

量: the longest string inside a `--send` above is `TI-1` at **95**
characters, well under `console-capture.py`'s 128-byte refusal. The
`CAP OUT` prefix is the host's own argv and is not sent to the board.

| capture | cell | typed | **precondition** | expect | 🔴 stop if |
|---|---|---|---|---|---|
| **`TI-L`** | free | `CAP OUT TI-L --send 'DW B8003008 4' --idle 2 --seconds 8` | at the loader prompt, before `J` | four words. `LDR-07` carries four per `DW`. **Whatever the loader left** — `IRR1` should re-confirm `REG-03`'s `30050004` | a differing `IRR1` → `REG-03`'s single reading was not reproducible, which is a finding about the loader and not about Linux |
| **`TI-0`** | `E0` | `CAP OUT TI-0 --send 'cat /proc/rtl819x-timer' --idle 3 --seconds 20` | at a shell; nothing armed this power cycle | § 5.1's whole table: `driver=rtl819x-timer 2.0`, `state=idle`, `hz_tick=200000`, `hz_cdbr=200000`, `hz_agree=1`, `hz_used=200000`, `shift=19`, `mult=2621440000`, and the four `irr*` words | `no such file` → the driver did not register and `MK2`'s witness just became a device measurement. `hz_agree=0` → § 5.2 |
| **`TI-1`** | `I1` | `CAP OUT TI-1 --send 'echo period 20 > /proc/rtl819x-timer ; echo arm > /proc/rtl819x-timer ; cat /proc/rtl819x-timer' --idle 3 --seconds 25` | `TI-0` read `gimr_tc1ie=0` **and** `tc0_undisturbed=1` | `state=armed`, `last_verdict=0`, `mask_bits=20`, `period_cycles=1048576`, `period_jiffies=524`, `ext_interval_j=131`, `tccnr=F0000000`, `tc0_undisturbed=1`, `arm_delta_100us` in **18…24** | any of the five errnos — **each is a result, none is a driver bug until the register dump says otherwise.** `-EIO` or `tc0_undisturbed=0` → disarm and end the block |
| **`TI-2`** | `I2` | `CAP OUT TI-2 --send 'echo armirq > /proc/rtl819x-timer ; cat /proc/rtl819x-timer' --idle 3 --seconds 20` | `TI-1` returned `state=armed` | `last_verdict=0`, **`tcir_tc1ie=1`**, `tc1ie_ours=1`, `tcir=C0000000`; and still `gimr_tc1ie=0`, `tcir_tc1ip=0` (one period has not elapsed) | `tcir_tc1ie=0` after the write → the bit is not writable, and § 3.2 of the map is wrong about which gate was clear. `gimr_tc1ie=1` → **something else moved it; disarm and stop** |
| **`TI-3`** | `I2` | `CAP OUT TI-3 --send 'sleep 8 ; cat /proc/rtl819x-timer' --seconds 30` | `TI-2` returned `tcir_tc1ie=1` | 🟢 **`tcir_tc1ip=1` AND `gisr_tc1ip=1`.** Also `tc1_ext_ticks` ≥ 5 and `tc1_ext_trusted=1` with **nobody reading `/proc`** | 🔴 **both still 0 → § 3.2's correction is wrong too, and the timer block needs something this project has not identified. That is the informative outcome and it is worth the cell.** The board not answering → `H2` firing through a path this design says is masked; power-cycle, do not re-arm |
| **`TI-4`** | `I3` | `CAP OUT TI-4 --send 'echo ackip > /proc/rtl819x-timer ; cat /proc/rtl819x-timer' --idle 3 --seconds 20` | `TI-3` read `tcir_tc1ip=1` | `ackip_before=1`, `ackip_after=0`, **`ack_proven=1`**, `tcir_tc1ip=0` | `ackip_after=1` → **`TC1IP` is not write-1-to-clear on this die**, D Table 25's single-source claim is refuted, `Q11` is answered in the negative — and `reqirq` will refuse, which is the guard working. **End the block here; that is a complete result** |
| **`TI-5`** | `I4` | `CAP OUT TI-5 --send 'echo reqirq > /proc/rtl819x-timer ; cat /proc/rtl819x-timer' --idle 3 --seconds 20` | `TI-4` read `ack_proven=1` | `last_verdict=0`, `irq_requested=1`, and 🔴 **`gimr_tc1ie=1` — set by `bsp_ictl_irq_unmask` through `request_irq`, never by this driver** | `-EPERM` → `ack_proven` was 0 and the precondition held; that is the guard, not a failure. `-EBUSY`/`-EINVAL` → the ordering was broken. **`irq_stuck=1` at any later point → the storm guard fired; stop** |
| **`TI-6`** | `I4` | `CAP OUT TI-6 --send 'sleep 8 ; cat /proc/rtl819x-timer ; cat /proc/interrupts' --seconds 35` | `TI-5` returned `irq_requested=1` | 🟢 **`irq_count` ≥ 1**, `irq_spurious=0`, `irq_stuck=0`, `irq_last_tcir=C0000000`; and a line for IRQ **25** in `/proc/interrupts` with a non-zero count | `irq_count=0` with the board alive → `L5`/`L6` are the wall, and `TI-0`'s `irr1` reading is the next thing to take. **`irq_stuck` ≥ 1 → the ack did not take under interrupt; the guard disabled the line and the board is still yours** |
| **`TI-7`** | `E9` | `CAP OUT TI-7 --send 'echo disarm > /proc/rtl819x-timer ; cat /proc/rtl819x-timer' --idle 3 --seconds 20` | any of the above | **the full unwind**: `state=idle`, `irq_requested=0`, `tc1ie_ours=0`, `tccnr` = `tccnr_at_init` = `C0000000`, `tcir` = `tcir_at_init` = `80000000`, `tcir_tc1ip=0` | `tcir` not returning to `tcir_at_init` → the driver cannot undo its own interrupt enable, and that is worth knowing before `R5-3b`. `tccnr` not returning → seating 11's teardown result did not survive version 2.0 |

### 4.1 Every typed line is inside what `cardcheck` can read

`argv0s()` is not a shell: it splits on whitespace, treats `;` as a separator
and drops redirections with their targets. So `echo` / `cat` / `sleep` are all
seen, and `> /proc/rtl819x-timer` is exempted because `/proc/` is the kernel's,
not the initramfs's. **No `$` appears in any `--send`** — `B9` refuses one in a
committed card, because that is the tokeniser's own precondition, and
`last_verdict` is what makes `echo $?` unnecessary.

---

## 5. Predictions, with refutation conditions

### 5.1 `TI-0`: the derived rate, and the four registers three of which have never been read

**Every value here is computed from a register this project has already read.**

| field | predicted | derivation | 🔴 refuted by |
|---|---|---|---|
| `hz_tick` | **200000** | `(tc0data_at_init >> 4) × HZ` = `(0x7D00 >> 4) × 100` = `2000 × 100` (量 `TM-1`, `REG-05`) | any other value → `TC0DATA` is not what seating 11 read |
| `hz_cdbr` | **200000** | `BSP_SYS_CLK_RATE / (cdbr >> 16)` = `200000000 / 1000` (讀 `bspchip.h`; 量 `TM-1`, `REG-11`) | as above for `CDBR` |
| `hz_agree` | **1** | the two agree exactly, so any tolerance passes | `0` → the tick and the crystal disagree about this block's divider, and **that is a finding about the SoC, not about this driver** |
| `hz_used` | **200000** | `hz_tick`, because it needs no clock constant and `R5-2` measured `ΔTC1 = Δjiffies × (tc0data>>4)` with residual exactly zero | `14286057` → `TC0DATA` read 0 and the driver fell back to the compiled constant |
| `shift` | **19** | the largest shift with `mult ≤ 2³²−1` and `mask × mult ≤ 2⁶³−1` at `hz = 200000`, `mask = 2²⁷−1` (`CLK-24`) | any other → the search is not doing what § 5.3 says |
| `mult` | **2621440000** | `(10⁹ << 19) / 200000` = `5000 × 2¹⁹`, **exact, no rounding** | as above |
| `hz_kernel` | **100** | `CONFIG_HZ=100`, 讀 the built `.config` | any other → this is not the config that was built |
| `irr0` | **`22222222`** | `BSP_IRR0_SETTING`, recomputed from `bspchip.h`'s own macros by script (`IRQ-07`) — **never read on this die** | any differing word → either this is not the `bspchip.h` the image was built from (excluded, `interrupt-map` § 6.1) or something writes `IRR` after `bsp_irq_init` |
| `irr1` | **`C222FA2D`** | `BSP_IRR1_SETTING`. 🔴 **The loader leaves `30050004` and not one nibble agrees** | as above |
| `irr2` | **`2EB29F22`** | `BSP_IRR2_SETTING` — never read on this die | as above |
| `irr3` | **`22222022`** | `BSP_IRR3_SETTING`. ⚠️ Bits 11:8 are `0` because the vendor's macro **has no `<< 8` term** — a defect in the macro, not a question about the silicon | as above |
| `irr1_tc0_rs` | **13** | nibble 0 of `C222FA2D` | — |
| `irr1_tc1_rs` | **2** | nibble 1, `BSP_IRQ_CASCADE` | — |
| `status_im2` | **1** | `setup_irq(BSP_ICTL_IRQ)` with `BSP_ICTL_IRQ = BSP_IRQ_CPU_BASE + 2 = 2` → `rlx_cpu_irq_unmask(2)` → `set_c0_status(0x100 << 2)` = bit 10 (讀 `arch/rlx/kernel/irq_cpu.c:44`) | `0` → the ICTL cascade is masked at the CPU and **no ICTL interrupt can be delivered at all**, which would make `TI-6` fail for a reason `TI-0` already knew |
| `status_bev` | **0** | normal exception vectors after boot | `1` → the kernel is still on the boot vectors |
| `status_iec` | **1** | a `/proc` read is process context with interrupts on. ⚠️ 讀 `asm/rlxregs.h`: this core has the MIPS-I three-deep stack `IEc`/`IEp`/`IEo` at bits 0/2/4 and **no single `ST0_IE`**, which agrees with `SOURCES.json`'s binutils note that every Lexra core is `ISA_MIPS1` | `0` → the read is not where this card thinks it is |

🔴 **`status` is read OUTSIDE the driver's spinlock, on purpose.**
`spin_lock_irqsave()` disables interrupts, so a `Status` read inside it would
report `IEc = 0` **always** — a constant dressed as a measurement. `IM2` and
`BEV` are unaffected by the lock; only one of the three bits needed the care and
all three are taken where all three are true.

### 5.2 The three-way rate check `TI-1` gets for free

`arm_delta_100us` is a `udelay(100)` bracket over the counter. At
`hz = 200,005` that is **20.0 counts**. 🟢 **Seating 11 read `21`** — with the
driver's compiled constant claiming 14,286,057 Hz, which predicts **1,429**.
So that field was already a measurement of the true rate and nothing in block 8
read it as one. The band **18…24** is the prediction; anything near 1,400 would
mean the divider moved back to the loader's.

### 5.3 What `TI-3` decides, and why both outcomes are worth the cell

| `tcir_tc1ip` | `gisr_tc1ip` | what it means |
|---|---|---|
| 1 | 1 | 🟢 § 3.2's correction holds. The masked-observation strategy is real, `Q11` is testable, and `TI-4`/`TI-5` proceed |
| 1 | 0 | the timer block latches but the controller does not see it — `IRR1` routing or a gate this project has not found |
| 0 | 0 | 🔴 § 3.2 is wrong **too**. `TCIR` bit 30 is not the remaining gate, and the block needs something not yet identified. **The most informative outcome of the block** |
| 0 | 1 | the controller sees a pending TC1 that the timer block does not report — two registers disagreeing about one event, which no source here predicts |

### 5.4 The reader-driven defect, shown fixed

`TI-3` sleeps 8 s with **nobody reading `/proc`**. 量 `TM-5c` on version 1.0:
462 s with no reader left `tc1_ext` **92,362,366 counts** behind `tc1_cycles`
and `tc1_ext_trusted` still reading `1`. Version 2.0 advances it from a
`timer_list` at `ext_interval_j = 131` jiffies, so:

* `tc1_ext_ticks` ≥ **5** after an 8 s sleep (8 s / 1.31 s = 6.1, minus edges);
* `tc1_ext` within one `ext_interval_j` of `tc1_cycles`;
* `tc1_ext_gap_max_j` ≈ **131**, and **< `period_jiffies` = 524**, so
  `tc1_ext_trusted=1` is now a statement about jiffies that cannot alias.

🔴 **`tc1_ext_gap_max` (counts) is still printed beside it and still aliases.**
That is deliberate: the pair is what makes the old defect legible. Seating 11's
`(Δtc1_ext = 6,475,804, true gap = 140,693,532)` says "a whole period was lost"
only when both numbers are visible — the first is exactly the second mod 2²⁷.

⚠️ **`tc1_ext_gap_max` read 6,475,672 there and that is a THIRD number**: the
largest single inter-read gap of the two that happened (`tc1_ext_reads` 1 → 3),
not the span. **Nine** committed files said 6,475,672 *was* the aliased value until
this card's numbers were recomputed from the captures by program.

---

## 6. Abort conditions for the block as a whole

1. `TI-0` shows `gimr_tc1ie=1` → **do not arm**. The finding is the reading.
2. Any capture where the board stops answering → power-cycle, do not re-arm,
   and the block ends. `TI-3` and `TI-6` are the two rows where that is a
   result rather than an accident.
3. `irq_stuck` ≥ 1 → the storm guard fired. Read the dump, `disarm`, stop.
4. `tc0_undisturbed=0` at any point → the vendor's tick is at risk; `disarm`
   immediately and end the timer work for the seating.
5. The board printing an `RLXFW-ID0=` that is not `69EE7DEA` → this is not the
   image this card describes and **nothing below `TI-0` may be typed**.

---

## 7. What this block cannot tell you, stated before it runs

1. **It does not raise the clocksource rating and does not register a
   clockevent.** The system time base is still `jiffies` throughout. That is
   `R5-3b`, and this card's `TI-*` cells say nothing about it.
2. **`ESTATUS` is still unread.** `L6`/`L7` in § 3.1 become 量 for `Status`
   only; the LOPI mask lives in a different register file reached by `mflxc0`,
   and TC0 — the vendor's own tick — runs there.
3. **`ack_proven` is n = 1.** One instant, one write.
4. **`irq_count` ≥ 1 shows delivery, not correctness.** It does not show that
   the handler ran at the right rate, and this block does not measure a rate.
5. **Nothing here writes flash, and nothing here can say a flash byte was not
   written.** The bracket is unchanged at 0.0244 %.

---

## 8. The machine-readable halves

`cardcheck numbers` re-derives every value below from the artefact named beside
it, rather than comparing it to a transcription.

```cardnum
img-bytes	1032192	size /home/key/fwre-work/rebuild/bench-only/r53b-20260904/rlxfw-r53b-20260904.bin
img-sha16	b1273e55552603bf	sha256-16 /home/key/fwre-work/rebuild/bench-only/r53b-20260904/rlxfw-r53b-20260904.bin
vmlinux-sha16	3246e89fbf1eb845	sha256-16 /home/key/fwre-work/rebuild/r3-4/out/r53b.vmlinux.elf
vmlinux-bytes	3974472	size /home/key/fwre-work/rebuild/r3-4/out/r53b.vmlinux.elf
prev-img-sha16	39abf11c2d6fd0ce	sha256-16 /home/key/fwre-work/rebuild/bench-only/r51-20260903/rlxfw-r51-20260903.bin
drv-lines	1451	lines config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c
proc-lines	67	count config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c scnprintf
```

⚠️ `prev-img-sha16` is here so the image discriminator is a **contrast** and not
a lone value: `b1273e55…` is tonight's and `39abf11c…` is seating 11's, both
re-derived from files on disk. A stop condition that names only the value it
wants cannot say what it would be seeing instead.

⚠️ `proc-lines` counts `scnprintf` in the driver's source. 量 today: **all 67
are inside `rtl819x_tc_read_proc`**, so it equals the number of `key=value`
lines a dump prints. A dump with fewer lines means the capture was cut, and this
is the number that says so. It was 37 on version 1.0.

⚠️ **`RECIPE_ID` is not in this fence and cannot be**: it is a sha256 over a
whole directory and `cardnum`'s expressions read one file each. It is
**`69ee7dea`**, printed by the build and asserted by `looprun` at `S8`, and § 1
carries it.

```cells
bench/2026-09-04/TI-L
bench/2026-09-04/TI-0
bench/2026-09-04/TI-1
bench/2026-09-04/TI-2
bench/2026-09-04/TI-3
bench/2026-09-04/TI-4
bench/2026-09-04/TI-5
bench/2026-09-04/TI-6
bench/2026-09-04/TI-7
```

Nine captures for **six** cells — `E0`, `I1`, `I2`, `I3`, `I4`, `E9` — plus one
loader-prompt read (`TI-L`, which is not a cell). `TI-2` and `TI-3` are one cell
(`I2`) taken twice because the wait must be a separate capture, and `TI-5`/`TI-6`
are one cell (`I4`) for the same reason. The mapping is the `cell` column of § 4
and it is written there rather than inferred.

*(This sentence read "eight cells" until it was counted against § 4's own table.
Nothing in this repository compares a document's prose to its own tables — the
same defect put "five gates" in `docs/interrupt-map.md` § 0 over a seven-row
table one segment ago, and it is found the same way both times: by counting.)*
