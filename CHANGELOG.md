# Changelog

**Nothing has been built.** There is no kernel of mine, no image, and no byte of
mine has been written to this device's flash. What exists is the instruments, the
record, and the first thing that ran on the silicon — the vendor's own kernel,
delivered over the network.

Tags mark where the outside world can check the work, not where a feature landed.
`PROGRESS.md` is the only file that says where the work actually is.

---

## Unreleased

**`R1h-0`, 2026-08-26 — `probe3`'s cell table, and writing it refuted two things
the table was going to stand on.** `docs/probe3-cells.md`: eleven sections, every
expected value and refutation condition written before its cell, every expected
value naming its capture or artefact, and *expected under qemu* kept in a
separate column from *expected on the device* — because `probe1` cell 1 came back
FRESH on qemu and STALE on silicon, and that opposition is the whole experiment.
Desk only, no power, zero flash bytes.

- 🔴 **The prediction and the mechanism were about different caches.** The walk's
  mechanism — a store into the instruction stream is not seen — is measured, and
  it measures the **I-cache**; the prediction written for it (D 8 KiB, line 16 B,
  cut from this unit's own kernel) is about the **D-cache**. The walk as
  described could not have refuted the prediction written for it. `probe3` now
  carries two walks, and the D-side one is armed at run time by its own cell A.
- 🔴 **This part has a 16 KiB local instruction scratchpad, and it is exactly the
  size of the predicted I-cache.** Nothing in this repository had ever recorded
  it. It was found by asking what `CCTL 0x010`/`0x020` are: they are
  `IMEM0FILL`/`IMEM0OFF`, named by four sources of which two are independent —
  the Lexra LX4189 datasheet, **`arch/rlx/include/asm/rlxregs.h` in the GPL drops
  this project already held**, the RTL8196E datasheet's *"16Kbyte I-MEM, 8Kbyte
  D-MEM"* (already quoted verbatim at `SOURCES.json:195`), and this unit's own
  kernel programming a 16 KiB window into `CP3 $0`/`$1` and then issuing `0x010`.
  **`CPU-24` closes; `CPU-46` is new.** The same search failure as `arch/rlx/`
  one release earlier: the fact was in the tree and the search went elsewhere.
- 🔴 **`CPU-25`'s source count was wrong in the direction of too few.** The
  datasheet in `refs/` states both cache sizes on its own first page. What has no
  source of any kind is **the associativity**, not the I-cache size. ⚠️ And the
  datasheet documents a variant `SOURCES.json` records this unit as *not being* —
  so the geometry is two vendor documents about two variants of a family this die
  is measured to belong to, and still not a reading of this die.
- **`CCTL` is edge-triggered on 0→1**, so a probe that writes it once and expects
  an effect is a tool that cannot fail. `CLK-17` is new — the 14.286057 MHz rate
  a timing payload actually divides by, which until now existed only inside a
  derivation. `CLK-02`'s name is corrected against the datasheet it cites.
- 🔴 **The table was then put to four adversarial readers and they found eight
  blockers**, two of which would have cost the power cycle: a whole-cache
  `DInval` that discards the return address off a KSEG0 stack, and a CP3 read
  that would have trapped because the preceding cell restored `Status`. Also a
  write-buffer confound that made one cell unable to fail, three line-size cells
  with no must-fire reading, and a timer field read 16× wrong. All fixed; the
  list is in `LOG.md`, because the record of being wrong stays in place.

**`R1-gate` closes, 2026-08-26 — and the write-up refuted two things the gate had
been standing on.** `docs/rlx-cache-and-cp0.md` is the closing statement: the four
downstream decisions, each with the reading that decided it, and what the gate did
not prove. Desk only, no power, zero flash bytes.

- **Three of the four decisions name a measurement. The fourth names none, and
  that is written down rather than smoothed over.** Where the MTD driver flushes
  (`CCTL 0x002`, **instruction side only**), where the exception handler can live
  (`0x80000080`, `BEV = 0`, `break` trapped and returned), and whether the SoC
  timer driver is a prerequisite (it is, `Count` is not implemented) are settled.
  **Whether the Ethernet driver's descriptor rings need an uncached window is
  not**, and it moves to a new gate with a payload, a DoD and a stop-loss rather
  than staying an open row on a closed gate.
- 🔴 **"The D-cache is write-through" was a reading the measurement does not
  carry.** Both cells that established it stored to a line the D-cache did not
  hold — a write **miss** — and under a miss, write-through and write-back
  without write-allocate are indistinguishable. The vendor's own board config for
  this SoC says write-back. **A descriptor ring is a write *hit***, so the CPU→
  memory direction is not covered for the pattern the driver will actually use.
- 🔴 **A refutation condition this project wrote for itself is met.** *"Refuted by
  finding a `cache` instruction anywhere in vendor code that executes"* — the scan
  that returned zero had only ever been run on the 56 KB loader. This unit's own
  kernel carries **37 of them**, D side only, in one span, separated from 15 data
  false positives by three independent properties. It does not make this a MIPS32
  core (`Config.M = 0` is measured); it means there may be a working D-cache
  invalidate here, which is exactly what the open decision needs.
- **Four CCTL commands have names from a source that states them, and one command
  had no row at all.** Found in `arch/rlx/mm/cache-rlx.c` — a directory the
  earlier conclusion never listed, in a tree this repository already cited
  elsewhere. `0x010` and `0x020` remain unnamed in every source, and the only
  instrument that could name them is one this project declines to run on a
  single-device budget.
- 🔴 **`SPEC.md`'s cache row had been outside two of its checker's checks since
  the day it was written.** One unescaped `|` gave it eight cells in a
  seven-column table; every check reads cells by index, so they read the wrong
  cell and passed, and the summary reported the row as *skipped*. `spec-check.py`
  gains **C8** — cell count must equal the header's — and a ninth mutation that
  re-creates that exact defect. Pointing the same scan at the rest of the
  repository found two more, both of which had been mis-rendering tables since
  they were written.

**`R1g-4b`, at the bench, 2026-08-25 — `R1e` closes and `R1-gate` has only its
write-up left.** One power cycle, 23 captures, zero flash bytes, and 16 of 16
captures written after the block that predicted them.

- **The CP0 census ran on this silicon**, under an exception handler installed at
  `0x80000080` and read back word for word before anything was allowed to fault.
  `Status.BEV = 0` — and `break` trapping into that handler and returning is the
  direct evidence that the core *fetches* there, rather than an inference from
  the copy having landed. `PRId = 0x0000CD01`, predicted in writing beforehand.
  `Count` is not implemented, so this SoC's timer driver is a prerequisite.
  The CP0 ignores the select field. `Config.M = 0`, so it is not a MIPS32 core.
- **`nowrite = 0` on all 256 rows is the row that makes the rest mean anything.**
  Reading every register twice with two different primes is what separates *this
  register reads zero* from *the instruction never wrote its destination*, and
  without it `Count = 0` would have been ambiguous exactly where it is
  load-bearing.
- **`Random` (rd 1) came back moving**, sixteen distinct values inside 0…31 —
  the positive control the census could not otherwise have had, and an
  independent corroboration of the 32 TLB entries.
- **Three tool defects, found by pointing the tools at the new captures.**
  `reply-size.py check` crashed on the one input it exists to report; its
  `UNREADABLE` branch existed, was counted, and could never print. Its suite
  goes 12 → 21. `boot-timeline.py`'s artifact anchor assumed a one-byte prefix
  and mis-measured a two-byte one by two orders of magnitude; 12 → 15.
- 🔴 **A power cycle was spent on a wrong assumption and it is recorded as one.**
  A second `J 80500000` booted the vendor kernel, because the loader re-stages
  that address on a watchdog reset too — so a payload cannot be re-run on one
  power cycle without re-uploading. Nothing already measured was lost.

**`R1g-4b`'s desk half, 2026-08-25.** `probe2` is fixed against measured values
rather than read ones, and the suite that would have to tell a fixed payload from
a shipped one went from 66 cases to **106**.

- **`tools/rlxprobe/probe2`** — the five must-fix items from
  `docs/rlxprobe-audit-2026-08-25.md`. `SAFE_A0` before the one instruction in
  the tree guaranteed by design to fault; a 44-word read-back of the installed
  handler, so *the stores did not land* and *the core does not fetch there* stop
  being one hang; one binary instead of two indistinguishable ones; a primed
  destination on every CP0 read; and **no `mtc0` to CP0 register 12 anywhere in a
  device image**, which is what "it does not touch `Status.IsC`" looks like when
  it is a claim about the emitted words instead of about a comment.
- **The census reads every register twice, with two different prime families.**
  *Not written* becomes certain rather than likely, and **a register that changes
  between the two reads reports itself** — a second, independent route to `F50b`.
- **Four mutations, one per must-fix, run under qemu.** One of them exists
  because qemu cannot reach the state it tests: its `mfc0` always writes `rt`, so
  a payload with one census stub emitting `nop` is the only way to show that
  `S_NOWRITE` can be produced at all. The first qemu run of the fixed payload
  found a defect in the fix.
- **`tools/reply-size.py`** — `LDR-07`'s reply-length formula as an instrument.
  Twelve controls; the per-family constants fitted from the captures rather than
  counted by hand; **121 modelled, 0 unexplained** over `bench/`. The two
  captures that never fitted have names now instead of being misses.
- **`tools/boot-timeline.py`** — the named intervals of a boot, with the anchor
  bytes stated. It refutes `CLK-15`'s *"cold and warm are the same"*: the two
  populations do not overlap, and the difference survives **inside a single power
  cycle, twice**.
- `PROGRESS.md`'s `Est.` column is answered: 198 is not the plan's total, not its
  desk+bench, and not any consistent subset of it. No rule reproduces it.

## v0.0 — 2026-08-25

**The instruments and the record.** Fifteen tools, each with the controls that
show it can fail; three loader documents read to instruction level; one gate
closed on silicon; and, from today, something that runs them all on every push.

### What is established

| | |
|---|---|
| **`S0` closed 2026-08-23** | 3-2-1 encrypted backup plus a restore drill. Copy ③ downloaded and read back: 19/19 byte-identical, none missing, none extra, with a positive control that fired |
| **`R0` closed 2026-08-24** | **The vendor's kernel, delivered over TFTP and executed from RAM, reached userspace and answered ping 2/2 at 3.6 ms.** `G7.log` is byte-identical to `G6.log` as a whole file, 1789 bytes, same sha256; `G6` reproduces the pre-existing boot log byte-exactly from `decompressing kernel:` onward, 1687 of 1687 bytes |
| **No flash-write command was issued** | in any of the 81 captures across five power cycles. The flash evidence is **bounded and the wording matters**: the loader head and the `cr6c` image header are byte-identical across three kernel executions and two uploads, and that reaches **512 bytes of a 4,194,304-byte part**. It is not *"zero flash bytes written"*, and no instrument here can establish that |
| **`AUTOBURN` measured off at the burn path's own instruction** | `00000000` at `0x80401B9C` *during* the transfers, and `00000001` after the power cycle — which is the positive control on that ordering |

### What is not

Everything about the core itself. The instruction set, the pipeline hazards and
the CP0 registers are read out of binaries and vendor source; **nothing of mine
has executed a single instruction on this silicon.** That is `R1`, it is the
active gate, and it runs bare metal because Linux emulates the two rows the
toolchain decision rests on.

### In this tag

- **`docs/FINDINGS.md`** — one line per finding, ordered by the decision it
  changed. The map this repository's 400 KB of prose did not have.
- **`.github/workflows/ci.yml`** and **`tools/ci-census.py`** — the suites run on
  every push, and the census refuses a green build whose arithmetic does not
  close. It earned its keep on its first real input: 20 + 23 = 43 against a bench
  total of 45, so two cases had been vanishing out of `tools/test-rlxprobe.sh`
  with neither a `FAIL` nor a `skip` line. **88 cases run on a runner; 101 do
  not, and every one of the 101 is named on the build page** — they need a 56 KiB
  vendor bootloader that may not be redistributed.
- **`tools/rlxprobe/probe1`** — the `R1d` payload: six cells that decide, on
  silicon, which cache-management sequence makes this core see an instruction
  just written into RAM. Not yet run.
- **`tools/console-capture.py` 1.3** — `--esc-period`, and the period each
  capture *achieved* is now measured and recorded rather than assumed.
- `README.md` rewritten: the previous first screen said *"no claim in this
  repository has been observed on silicon"*, which stopped being true on
  2026-08-23.

### Corrections that landed with it

- 🔴 **The general exception vector on this core is `0x80000080`, not
  `0x80000180`.** The MIPS32 address had reached **seven committed sites** and
  five more in the planning material. A handler written there would have landed
  in RAM nothing reads, and the fault would still have hung the board.
- 🔴 **A fault the loader does not handle hangs forever** — `do_reserved` ends in
  a branch to itself with interrupts already off and the watchdog not armed. One
  fault costs one power cycle, and there is no spare unit.
- 🔴 **`do_reserved` dereferences the faulting code's own `$a0`**, and
  `rlx_cctl(0x002)` would have handed it the integer 2 — a kuseg address, a TLB
  refill to a vector nothing populated, and from there **undetermined**. Guarded
  before the payload was ever built, in two instructions. The sharper claim that
  went with it — *"it could branch into the loader's flash-write path"* — was
  refuted by the same day's adversarial pass and withdrawn: `0x5A5AA5A5` decodes
  as `BLEZL`, not a jump.
- 🔴 **A TFTP upload named `boot.img` makes the loader write from `0x80000000`
  upward**, over both exception vectors. On the do-not-type list from today.
- **`SPEC.md` `CPU-26` named the wrong table.** `0x8040A5C0` is the TFTP/ARP boot
  state machine, 24 entries; the exception table is `exception_handlers[32]` at
  `0x8040EB40`, in BSS.
- **`C-16` closes, and the refutation that had been recorded against it was
  itself wrong.** `check_image()` *is* the copier; it reads `gCHKKEY_HIT` at its
  17th instruction, not its first two. The block counter is where the document
  said, and it reads zero because a later rootfs scan sets it to exactly zero.
- **`CLK-15`**: the 350 ms of silence after `Booting...` is stage 1 copying
  20,924 bytes out of memory-mapped SPI NOR, uncached, a word at a time — and
  `Booting...` is printed by **stage 1**, so the experiment this project had
  written down for it pointed at the wrong binary.

Every one of these is in `PROGRESS.md`'s Corrections table with the date and
what caught it.
