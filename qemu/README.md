# `qemu/` — captures from the emulator, and what they cannot show

**A capture in here is not a measurement of this device.** It is a recording of
what a payload did on `qemu-system-mips -M malta`, and that machine is a 24Kf —
a MIPS32 part with interlocks, a coherent I-cache as far as the guest can tell,
no D-cache modelled at all, and no `cache`-instruction op-field decoding. This
directory is separate from `bench/` for exactly that reason: `bench/` is silicon
and this is not, and a reader sweeping for readings must never have to work out
which is which from a filename.

**Written 2026-08-26, `R1h-1`.** Until that day this repository had never
committed a single qemu serial capture — `qemu-run.sh` wrote into a `mktemp -d` —
so every *"expected under qemu"* value in `docs/probe3-cells.md` rested on prose
plus one CI assertion, with no artefact behind it. That is what this directory
fixes.

## What a pass here means

The four things it demonstrates, and they are all about the payload rather than
about the silicon:

1. the image is linked where it thinks it is and the entry is its first byte;
2. the report is well formed and the run reaches its own end marker, so *"it
   stopped"* and *"it ended"* are different observations;
3. every self-gate fires in the direction it is written for — a group whose
   precondition fails reports **void with a reason** rather than a pass;
4. a mutation planted in one check makes that check, and only that check, fail.

## What it cannot show, stated so a clean run is not read as more than it is

- **qemu interlocks the load delay slot and this core does not.** That is `F46`,
  it is measured on this device, and it is the whole reason `tools/hazlint`
  exists as a build gate rather than as a lint.
- **The expectations are OPPOSITE, and that is the point.** TCG invalidates a
  translation block when a store lands on code it has already translated, keyed
  on the *physical* address — so both the KSEG0 and the KSEG1 window behave like
  a machine with a coherent I-cache, and every cache cell comes back FRESH.
  On silicon `probe1` cell 1 came back **`01` STALE** (量,
  `bench/2026-08-25/H1b.log:9`) where qemu said FRESH.
  **A qemu run that looks like the device is the run to distrust.**
- **An emulator kinder than the device certifies exactly the bugs the device
  rejects.** That is how upstream's `P9-12` was certified by its own simulator
  before it failed on this silicon.
- 🔴 **2026-08-29, THREE more, and they are now measured against the silicon
  rather than predicted.** `probe3` ran on the device
  (`bench/2026-08-30/QJ.log`) after running here (`qemu/2026-08-26/probe3.txt`),
  so every one of these is a paired reading of one binary on two machines:
  - **CP3.** Here, all eight `mfc3` stubs **trap** with `m.cause=1000042C`
    (ExcCode 0x0B, CpU). On the device **none of them traps** — `m.traps=0`,
    `m.cause` still poison — and `CU3` sticks (`1000fc00` → `9000fc00`).
    ⚠️ **The payload itself printed that it could not separate the two
    explanations here**, and it was right to: the emulator's answer was an
    artefact of Malta's coprocessor map, not a fact about Lexra.
  - **The timer.** Here, every read of `0xB8003108` is `FFFFFFFF` and the payload
    prints `Group T VOID -- there is no timer at that address on this machine`.
    On the device the counter is live and the calibration bracket scales
    (`hi/lo = 2.0003`). **The payload separating *nothing is there* from *the
    register is frozen* is what made the qemu run interpretable at all.**
  - **The I-side walk.** Here, all FRESH at every working set — TCG keys TB
    invalidation on the physical address, so the KSEG1 alias buys nothing. On the
    device the walk produced a capacity-eviction curve with both of its controls
    firing, and that curve is the entire content of `CPU-25`.
  **None of the three could have been obtained here, and in all three the
  emulator's answer had the shape of a real reading.**

## 🆕 2026-08-29: there are now TWO channels in here, and they disagree about the UART

Everything above and below was written for `tools/rlxprobe/qemu-run.sh`, which
runs a bare-metal payload. `tools/deskchan.py` runs a **kernel image**, and it
differs in every line that matters:

| | `qemu-run.sh` (`2026-08-26/`) | `deskchan.py` (`2026-08-29/`) |
|---|---|---|
| entry | `-kernel <elf>` | four-instruction `-bios` stub + `-device loader,addr=0` |
| CPU | malta's default, a **24Kf** | `-cpu 4Kc` (量: 4Kc, 24Kc and 24Kf give the same counts) |
| memory | `-m 32` | `-m 128` |
| UART | ISA COM1, `0xB80003F8` / `0xB80003FD`, `-serial` **0** | CBUS, `0xBF000900` / `0xBF000928`, `-serial` **2** |
| what changes in the image | three build constants, recompiled | two patches applied to the binary: four COP3 words → `nop`, five words in `prom_putchar` |

🔴 **And the UART row is a contradiction between two of this repository's own
measurements, which is why it is written out rather than smoothed over.**

* 量 2026-08-26, committed in `2026-08-26/probe3.txt`: a payload writing
  `0xB80003F8` under `-kernel` produced **5,893 bytes**. The ISA window works.
* 量 2026-08-29, `deskchan.py`'s `C1`: a `-bios`-only stub writing the same
  address, with the file chardev on `-serial` 0, produced **nothing**, and a
  poll of `0xB80003FD` read 0 forever.

**One variable differs and it is the entry mechanism.** With `-kernel`, qemu's
malta writes its own bootloader into the reset window and that code initialises
the board before jumping; with `-bios`, the four instructions that replace it
initialise nothing. **That the GT64120's PCI/ISA decoders are what is missing is
推, not measured** — it is the obvious candidate and no experiment here
separates it from the others. What IS measured is that the CBUS UART at
`0xBF000900` answers on both paths, which is why the kernel channel uses it.

**Neither capture is wrong and neither generalises.** A reader taking the UART
addresses out of the table below and using them under `-bios` gets silence, and
would read it as *the code never got there*.

## The build is not the same image

`qemu-run.sh` rebuilds with three constants changed and nothing else:

| | device | qemu | why |
|---|---|---|---|
| `UART_THR` / `UART_LSR` | `0xB8002000` / `0xB8002014` | `0xB80003F8` / `0xB80003FD` | this part's 16550 registers are four bytes apart; Malta's is an ordinary ISA one |
| `VEC_GENERAL` | `0x80000080` | `0x80000180` | R3000 layout vs MIPS32's |
| `CLEAR_BEV` | 0 | 1 | Malta comes out of `-kernel` with `Status.BEV` set, which is the one state the payload refuses to install into |
| `RET_ERET` | 0 | 1 | `rfe` is MIPS-I and a Reserved Instruction on a 24Kf; the handler would fault inside itself |

Each capture's `.build` file records both sets and the **device** image's
`sha256`, because the file next to it was produced by the other one.

## Layout

```
qemu/<date>/<payload>.txt      the serial capture, verbatim
qemu/<date>/<payload>.build    host, qemu version, toolchain, both builds,
                               the device image's sha256, and the capture's own
```

`tools/audit-bench-log.py` is run over this directory before anything in it is
pushed — the same scan `bench/` gets, with the same eight patterns and the same
synthetic positive control, because *"it is only an emulator log"* is not a
reason to skip the check that decides whether a file identifies this unit.

🆕 **2026-08-31: `2026-08-31/` is the FOURTH directory, and the run found a defect in the payload rather than confirming one.** Group F — the memory-mapped SPI window, `docs/probe3-cells.md` § 6.8 — took `probe3` to 718 words and 31,536 bytes, so `2026-08-31/probe3.build` joins `2026-08-26/` in describing an image nobody will upload.

🔴 **What the run is evidence for, and it is the sharper kind: a refutation condition firing where it should.** Malta has no flash at `0x1D000000`, so `0xBD000000` returned sixteen identical words and `f.live`'s window byte came back **`0`** — which is exactly the *floating bus, not flash* condition § 6.8.3 writes. **The emulator is the worked example of a dead window**, and it is the only environment that can drive that branch, in the same way it is the only one that can fire the `M = 1` control below.

🆕 **2026-09-13: `2026-09-13/` is the FIFTH directory, and it is the first one whose payload is GENERATED.**

🆕 **2026-09-14: `2026-09-14/` is the SIXTH directory, and its leg is the one whose vacuous answer is the whole point.** `probe6` -- ten builds of one C fragment by four toolchains -- ran to its end marker here. 🔴 **Every row reading the interlocked answer is required**, not merely expected: qemu interlocks the load delay slot and this core does not (`F46`), so a hazard that survives compilation must read LOCK on this arm. 量: **12 of 12 rows LOCK**, `trapped 0`, `cell.bad 0`, `split 0` -- including the two hand-written controls, whose whole job on the device is to read in OPPOSITE directions. **So a device run that reproduces this capture refutes the experiment**, and the leg was committed before the card that predicts against it existed. 🟢 **It also fixes the device report's length as an equality rather than an estimate**: the window from the first `***` to `rlxprobe: end` is **1,808** bytes, and the 61-byte prefix that has to be subtracted is measured against `probe4`'s and `probe5`'s committed device captures in both directions rather than counted by eye -- a naive subtraction of just the `RLX_CLEAR_BEV` warning line is wrong by two, because the banner's own leading CRLF sits before the window's start. `SPEC.md` `TC-54`.

🆕 **…and 2026-09-13 later the same day it took a SECOND payload, which is the first time one of these directories holds two.** `probe5` -- `R1b`'s 24-row hazard ladder -- ran to its end marker here, and what its run is for is different from `probe4`'s. 🔴 **Every row reading the interlocked answer is the VACUOUS answer**, because `F46` says qemu interlocks the load delay slot and this core does not. That is C4 (`plan/DAY-ZERO.md:603`) and it is MANDATORY: a hazard test that gives the same answer on both machines has not measured a hazard. 量: **24 of 24 rows LOCK, 24 of 24 pre-registered predictions hit**, and the leg was run and committed BEFORE any device leg exists, so the expected difference is on paper rather than reconstructed afterwards. 🟢 **And reading the capture found a hole in the table that nothing else would have**: the `hilo` family's exposed constant is a primed accumulator, and `mult` overwrites both halves -- so *the prime did not land* and *there is no hazard* would have been one capture. `hl_ctl` primes and reads back with NO `mult` at all, and 量 `cafe0000`/`beef0000` says `mtlo` and `mthi` both work. `SPEC.md` `CPU-54`, `docs/isa-hazard.md` § 5. `probe4` -- `R1a`'s 75-row instruction sweep -- ran to its end marker here, and the run is worth more than a harness check for two reasons the earlier four did not have. 🟢 **One: for every row the 24Kf implements, qemu's answer is the MIPS specification's answer produced by an implementation this project did not write** -- a third source for the expected constant, and `plan:706` still forbids reading it as evidence about the die. 🔴 **Two: it refuted three of its own pre-registered predictions and one of those is a finding about qemu.** `0x7940003C` -- Lexra's `ltw`, the one encoding whose membership word names this core by number -- is declined by `objdump` at BOTH `mips:3000` and `mips:isa32r2`, and qemu 8.2.2 on `-M malta` retires it with no exception. **So this arm cannot be the negative control for that row.** `SPEC.md` `CPU-51`.

🔴 **And it found a coupling the desk had missed.** The first build ran Group F's seven timing legs unconditionally; Malta has no `TC0CNT`, so both bracket reads came back all-ones and every leg reported `00000000`. **Seven zeros is a number, not a refusal**, and Group T had already declared itself VOID two stages earlier. Group V is gated on `c-A` and Groups M and X on `h-brk`; a timing group with no gate was the payload disagreeing with its own design. `if (g_timer)` now leaves the legs at stage 0's poison, and `2026-08-31/probe3.build` records the whole thing.

🆕 **2026-08-31: `2026-08-31/` is the third directory here, and it exists because
the payload MOVED.** `probe3`'s block went 641 → 707 words (a retained bitmap
region of its own, and Group W's `M(T)` ladder), so `2026-08-26/probe3.build`
now describes an image nobody will upload and the capture beside it came from a
different binary — which is exactly what the rebuild-on-the-day table in
`docs/probe3-cells.md` says a moved `sha256` means. **Both are kept**; the older
one is the record of what `R1h-1` ran.

🔴 **And the narrow thing this run is evidence FOR is worth stating, because it
is not "the payload works".** It is that the two new code paths EXECUTE:
`bmp.kept=00000020` (the snapshot ran) and `w.assoc.mt=01ffffff` — where the
leading `0x01` is the `M = 1` control **firing correctly**, because qemu's TCG
invalidates a translation block on a store, so here one victim really does
self-evict. **That is the branch the seventeenth session restructured, and qemu
is the only environment that drives it.** On silicon it must NOT fire; if it
does, `w.assoc.tm` reads `000000ff` and every associativity cell is void.

## 🆕 2026-09-15: a SECOND EMULATOR is in here now, and it is not the one above

Everything above this section is `qemu-system-mips -M malta` — a whole
machine, no kernel, the payload at the reset vector. `2026-09-15/` holds two
captures from **`qemu-mips-static`, USER mode**, which is a different program
doing a different thing, and the filenames say so: `uprobe-user.txt`,
`uprobe-user-range.txt`.

`config/rlxfw-user/isaprobe/uprobe.c` is a Linux process. Under
`qemu-mips-static` its instructions are translated by qemu and its **system
calls and signal delivery are the HOST kernel's**, reached through qemu's
translation layer. So this arm is further from the device than the system-mode
arm is, not closer, and it is in here for one narrow purpose.

**What these two captures are evidence for.** Five statements, all about the
instrument, every one of them written down before the run:

1. `install_rc=0` — the five `sigaction` calls succeeded.
2. `c1a_raise=1` — a `raise(SIGILL)` reached the handler. **This is the one
   that matters most.** A harness whose handler never installed reports *no
   signal* for all 75 rows, and *no signal* is exactly the reading that means
   THE SILICON IMPLEMENTS IT — `docs/emulation-surface.md` § 7.3 names that
   backwards reading for `ll`/`sc`, and this is the same trap one level down,
   at the instrument.
3. `c1b_special0e_n=1` — an actual reserved encoding reached the handler too,
   by a mechanism that borrows nothing from libc.
4. 75 well-formed `PU ` rows, and the run reached `rlxuprobe: end`. *It
   stopped* and *it ended* are different observations.
5. `scratch_bad=0` — no cell altered its own inputs.

**What they are NOT evidence for, and the list is longer than the one above.**

- 🔴 **Nothing here is column ② of `docs/emulation-surface.md`.** That column
  is about what *rlxfw's kernel on this die* does with an encoding —
  `simulate_llsc`, `simulate_sync`, `do_cpu`'s `cpid == 0` arm. qemu has none
  of that code. `sync` reads *no signal* in `uprobe-user.txt` because qemu
  implements `sync`, which says nothing whatever about `simulate_sync`.
- 🔴 **The per-row verdicts here are qemu's answers and are not registered
  against anything.** `tools/isa-payload.tsv`'s `qemu` column is a
  pre-registered prediction for the **system-mode, bare-metal** arm; scoring
  this arm against it would be comparing two different experiments.
  `isapay.py verdict --arm user` deliberately gets no prediction scoreboard.
- ⚠️ **The 288-vs-592 `sigcontext` divergence is NOT exercised here.** `arch/rlx`
  truncates `struct sigcontext` after `sc_regs`; the toolchain's own header
  carries the stock 592-byte one; qemu builds the stock frame too. The three
  offsets this harness reads — `uc_mcontext` 24, `sc_pc` 32, `sc_regs[i]`
  40+8i — agree in all three, which is why it works here. The half that
  differs is the half the harness never touches, so neither this arm nor the
  device arm can validate it, and that is by design rather than by omission.
- The load-delay caveat at the top of this file applies unchanged: qemu
  interlocks and this core does not.

量: `qemu-mips version 8.2.2 (Debian 1:8.2.2+ds-0ubuntu1.18)`, and both
captures carry the artefact's own build id in their banner —
`*** rlxuprobe PU a87be346bb83e7f9 … ***` — so a capture from a different
binary cannot be mistaken for one of these.

Captures are committed **only when they are evidence for a written expectation**.
`qemu-run.sh`'s default output goes to `tools/rlxprobe/build/qemu/`, which is
gitignored; putting one here is a deliberate act.
