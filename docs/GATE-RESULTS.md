# Gate results

**One entry per closed gate: a one-line version, three claims that stand each
with its evidence, and what the gate did not establish.**

The project's planning material has asked for this file since before the first
gate closed. That material is not committed, so the requirement is restated
here as the file's own contract rather than left as a pointer a reader cannot
follow.

**This file owns no state.** Every number below is traceable to the file that
owns it — `SPEC.md` for values, `notes/` and `docs/` for the findings,
`bench/` for the captures. What this file owns is the *act*: on the day a gate
closes, writing down what it established and what it did not, in a form that
can be read against the evidence.

**Three claims is a deliberate cap.** Being able to write five usually means
two of them have no evidence and only sound right.

Marked the way the rest of the repository is: **量** measured on the device ·
**讀** read out of code, a dump or a document · **推** inferred, pending a
measurement.

---

## What this file is for, beyond the record

The rule that asks for these entries carries an operating clause:

> **If two consecutive entries have the same thing in *what it did not
> establish*, that thing is the next gate.**

That clause cannot run on one entry. It is run at the bottom of this file, and
its first result is recorded there whether or not it agrees with the plan.

---

## Two gates are missing from the top of this file, deliberately

`S0` closed 2026-08-23 and `R0` closed 2026-08-24, both before this ledger
existed. They are **not** backfilled, and the reason is mechanical rather than
stylistic.

The operating clause above compares consecutive entries to detect a thing that
keeps not getting established. An entry written today for a gate that closed
two weeks ago would be written by someone who already knows how every gate
since came out — including which residuals were later closed and by what. Feeding
that into a clause whose whole job is to notice an unresolved pattern
contaminates the input. It is the same rule that makes `bench/**/PREDICTIONS-*`
worthless unless committed before the capture.

So the ledger starts at `R1-gate`. `S0`'s and `R0`'s results are in
`PROGRESS.md`'s gate board with their evidence links, and `R0`'s own criterion
change — *"0 flash bytes written"* replaced by what an instrument here can
actually establish — is recorded on that row.

*(Filename note: the planning material calls this file `weekly-results`. The
unit was never the week; it has always been the gate, and the name here says
so.)*

---

## 2026-08-26 — `R1-gate` (`R1d` cache model + `R1e` CP0 census)

### One line

How this core's cache has to be managed, and what is in its CP0, are now
measured rather than read — and of the four downstream decisions this gate
exists to unlock, three have a reading and the fourth has none. **That the
fourth has none is the most important line in this entry.**

### Three claims that stand

**① `CCTL 0x002` on its own is enough to make instructions just written to RAM
be fetched, and the vendor's D-then-I sequence is redundant rather than wrong.
量, twice, on two different grounds, with a negative control.**

* `probe1`, `bench/2026-08-25/H1b.log` + `H1c.log` — two channels, 104/104
  words identical. Cells 2/3/6: six victims, all `02` FRESH.
* **The negative control is why it counts.** Cell 1 applies no treatment and
  both its victims come back `01` STALE, 7 KiB apart, so eviction has to
  explain two of them. **And it is the opposite of what the emulator does** —
  qemu returns FRESH there, because TCG invalidates the translation block. §H1
  was written before the seating: *one device execution that looks like qemu is
  the one that refutes this experiment.*
* The second measurement stands on different ground: `probe2` writes 44 words
  through KSEG1 to `0x80000000`/`0x80000080`, invalidates with `0x002` alone,
  reads them back word by word before it dares to fault — `install.bad = 0`,
  `break.count = 1`, `cause = 00000024`, `epc = 80500270`. Different address
  range, different store path, same answer.
* ⚠️ Claims ① and ③ share a payload and a run. They are two readings of one
  execution, not independent confirmations of each other. What is genuinely
  independent is ① being measured once on `probe1` and once on `probe2`.

**② `Count` (CP0 rd 9) is not implemented, so the SoC timer driver is a
prerequisite rather than a nice-to-have. 量, with a positive control in the
same seating.**

* `bench/2026-08-25b/H2a.log` + `H2g.log`, two channels, 40 header words
  identical, seal `EC84408D` matching: row `0x48` reads `00000000` with
  `S_ZERO`; `rlx_count_delta` over 100,000 iterations of a three-instruction
  loop reads `count.before = count.after = count.delta = 0`, `count.traps = 0`.
* **What makes that zero a real zero** is a different row: `nowrite = 00000000`
  on all 256. Every row is read twice with a different prime
  (`0xC0DE00nn`/`0xD1CE00nn`), so *"the `mfc0` retired without writing `rt`"*
  has its own state and never once appeared.
* **The positive control is in the same run**: `Random` (rd 1) reports
  `S_MOVES`, eight rows, sixteen values, index field in 5…29 and inside 0…31.
  Without a register that does move, *"`Count` does not move"* is not
  falsifiable — a broken double-read gives the identical answer.

**③ `Status.BEV = 0`, and the core really does fetch from `0x80000080`.**

* `bench/2026-08-25b/H2a.log`: `Status = status_end = 0x1000FC00`, bit 22 = 0.
* **The load-bearing half is the second one.** `trap_init` copying 128 bytes to
  `0x80000080` proves only that the copy worked (`H0a` 32/32 words against the
  prediction, `H0a2` from a second source, `H0a3` re-read through KSEG1). What
  proves *fetch* is a `break` trapping into the handler installed there and
  returning, with the vector restored afterwards (`restore.mismatch = 0`,
  `H2h-utlb` byte-identical to `H0c`).
* ⚠️ Residual in `SPEC.md`: what was measured is the `Status` the payload sees
  after `J` clears `IE`, not the one at the loader prompt. They differ only in
  `IEc`, and no loader command can read CP0.

### What `R1-gate` did not establish

1. 🔴 **Whether a cached load sees a DMA write. Not one word measured.** This is
   downstream decision ②, and it has no answer.
2. 🔴 **Write-through versus write-back-without-write-allocate — indistinguishable
   here.** Both of `probe1`'s store cells are write **misses**, and the two
   models predict the same reading. The vendor's own `boards/rtl8196e` config
   says `CONFIG_ARCH_CACHE_WBC=y` (讀).
3. 🔴 **Whether this silicon retires the `cache` instruction — never executed.**
   37 of them in this unit's kernel (讀); none run (量).
4. **Cache size, line size and associativity — not measured.** The CP0 route was
   measured away (`Config.M = 0`) and the R3000 sizing walk needs an isolation
   this part does not have. What was left is a build constant agreeing with a
   third-party device tree — two beliefs agreeing is still not a measurement.
5. **What `CCTL 0x010`/`0x020` are — no source names them**, and the route that
   could (write them and watch) was declined on the budget of a single device.
6. **Whether `Status.IsC`/`SwC` are implemented as bits** — what was measured is
   behaviour (isolation ineffective, the store reached DRAM), not bits.
   ⚠️ The experiment this item originally named was `probe2`, and `probe2`'s own
   audit requires it to contain no `mtc0` to CP0 12 anywhere. **That experiment
   ran and did not contain this item.**
7. **Whether `Compare` is implemented** — read, never written. A read-only census
   cannot separate *not implemented* from *implemented with a reset value of 0*.
8. **Anything about the Lexra family.** `R1d` measured which flush works on this
   core, not why. `PRId = 0x0000CD01` is a value no source gives a name to.
   Neither `RLX5281` nor `RLX4181` may be written.

### Note left for the next entry

Items 1, 2 and 3 are three faces of one thing — what actually happens on the D
side — so if the next entry still carries them, the operating clause turns that
into the next gate.

🔴 **That was not waited for.** `R1h` opened the same day `R1-gate` closed,
because both of `C-6`'s owning gates closed under it and *an item with no owning
gate is a bug in `PROGRESS.md`'s own carried-forward list*. `C-16` had already
demonstrated a gate closing while its item did not, and that was found days
later.

---

## 2026-08-28 — `R2a/b/d` (which GPL drop, and what the vendor kernel emulates)

### One line

The similarity instrument was built with its floor computed from the corpus
rather than chosen, and it clears its own null by 92.8 pp against a 5 pp bar —
**and what it measures turns out to be the toolchain rather than the drop**, so
the gate's own question stays 推 and the reason is now a number instead of a
shrug.

### Three claims that stand

**① The metric has a floor that comes out of the corpus, and the six-tree matrix
clears the metric's own null by a wide margin. 讀, with 32 controls written
before any result.**

* `binsim(A,B)` is 7-gram set containment over normalised MIPS operand tokens in
  the code window `[DT_INIT, DT_FINI)`; Jaccard is printed alongside and never
  substituted. `k = 7` was chosen by a rule written first, which reads only
  anchors whose answer is known. `SPEC.md` `TC-11`, `notes/binsim.md`,
  `tools/test-binsim.sh` (71 cases).
* The matrix: fifteen pairwise scores over six real builds, `boa` and `busybox`
  separately. Three clusters, cell for cell identical to `TC-10`'s container
  fingerprints. This unit's nearest neighbour is `n200re-3.2.0` at `boa`
  containment **0.9818**; second is `n300rt-2.1.6` at **0.8951** — **8.67 pp
  apart** (`TC-12`).
* **The pre-registered null did not fire**: *if the fifteen scores span under 5
  percentage points the metric has no discrimination and its numbers are void.*
  The span is **92.8 pp**. Recorded rather than skipped past, because a null
  that is satisfied and still leaves the answer undetermined is saying it was
  never the binding constraint.
* 🔴 **The first noise floor written for this metric was refuted the day it was
  written.** It came from pairs selected *by* the byte-equality of the window
  they were then scored on, so 1.000 was arithmetic. The replacement estimate is
  **8.0e-4** (推).

**② The channel identifies the toolchain, not the drop — 讀, by three cells that
differ in exactly one factor each.**

* `TC-18`, everything else held fixed (same source, same `.config`, same gcc and
  binutils): changing **only `-march`** (4181 against 5281) gives containment
  **0.3360**; replacing the **source** gives **0.9359**. Containment is a
  similarity, so the smaller number is the larger change: **swapping the target
  core moves this metric far more than swapping the program.**
* Ten rebuild cells (3 drops × 3 rsdk, 7 of 9 building, plus a synthesised
  1.5.5-at-`-march=4181`) score at best **0.8255** against this unit's binary —
  **warn, not pass**.
* So `TC-02` — *which drop built this firmware* — **stays 推**, and the step's
  own DoD did not survive it: the DoD asked for `binsim(rebuild, unit) >= BASE`
  or an explicit undetermined; what it got was the second branch *with the
  reason the first branch was unreachable*.
* The binding constraint, which had never been written down before this gate,
  now is: **a similarity matrix over six shipped images cannot name a
  source-and-toolchain release, whatever it scores.** `notes/which-drop.md` §5.

**③ What this unit's kernel emulates, read out of its own source, with the
positive control the file had already been forced to learn. 讀.**

* `CPU-47`: `ll`/`sc` emulated, `sync` emulated as a no-op, `rdhwr` **not**
  emulated (the vendor `#if 0`'d both call sites mainline calls
  unconditionally), the `lwl` family needing no emulation. `do_ri()` at
  `arch/rlx/kernel/traps.c:546`, under `#ifndef CONFIG_CPU_HAS_LLSC` and
  `#ifndef CONFIG_CPU_HAS_SYNC`. `notes/vendor-kernel-isa.md`.
* **The refutation condition was written first and it is about the zero**: a
  grep returning zero is a claim, refuted by the same scanner finding a hit in a
  second artefact, and if it cannot, the zero is recorded as *not looked for*
  rather than as *not there*. That shape had already produced one false zero in
  this repository (a `cache`-instruction scan run on `stage2.bin` alone), and it
  produced two more inside this step before it held.
* This narrowed a house rule's stated reason rather than the rule: the ban on
  measuring the ISA under Linux said *"and the FPU"*, and 讀 there is **no FPU
  emulator in this kernel at all** — `arch/rlx` has no `math-emu` and `do_cpu`
  raises `SIGILL` for every coprocessor but 0. `simulate_llsc` alone carries the
  rule.

### What `R2a/b/d` did not establish

* 🔴 **Which GPL drop this firmware was built from.** `TC-02` is **推** and this
  gate is the one that was supposed to move it. What it produced instead is the
  reason it cannot be moved from shipped images alone.
* 🔴 **That the three drops in hand can build this image — they cannot.**
  `TC-02` 材料: taking one of the five shipped configs and building
  `rtl819x-toolchain`'s kernel produces an image that differs from this unit's
  on discriminators neither the drop nor the config explains.
* **Whether a reproducible build environment needs a container — it does not**,
  which refutes the premise this gate opened on. Three rsdk releases run
  natively on Ubuntu 24.04; the only thing missing was an i386 `libz.so.1`. The
  container step became a step of this gate and then dissolved.
* **Which toolchain rlxfw itself should use for userspace** (`TC-05` residual ①)
  — narrowed by `TC-19` (twelve shipped binaries across six trees, all on the
  delay-slot-padding side, `hazlint` 0 violations), decided for the kernel, ~~open
  for userspace~~. `R7` owns it.
  🔄 **Expired 2026-09-15 (`SPEC.md` `TC-57`), and by the criterion this
  bullet itself names.** `hazlint` was run over each candidate's whole
  `libc.a` for the first time: `rsdk-1.3.6-4181` reads **0** over 19,096
  loads, the two 5281 releases read **4,574** and **3,741**. It discriminates
  uniquely. ⚠️ What that settles is which toolchain `R1c`'s harness uses;
  the `R7` GATE decision is still `R7`'s, and a reader reaching this bullet
  today must not carry the present tense out of it.
* ⚠️ **It did close something belonging to `R1-gate`**: item 8 above. The
  `PRId` assignment table turned up inside a GPL drop this project already had,
  so `RLX4181` became writable (讀) and `RLX5281` became positively excluded
  rather than merely unproven. A gate closing another gate's residual is the
  carried-forward list working, and it is recorded here because the ledger is
  where that becomes visible.

---

## 2026-08-29 — `R1h` (cache geometry, D-side coherence, `cache` retirement)

### One line

Three of this gate's four questions came back with readings from one payload on
one seating, and **the fourth — the D side, which was already `R1-gate`'s
unanswered decision ② — is still unanswered, this time with the instrument
saying so itself.**

### Three claims that stand

**① The I-cache's geometry is measured by experiment: 16 KiB, 16-byte lines,
2-way. 量, with both of the refutation controls firing in both directions.**

* Size: working sets of 1, 2, 4 and 8 KiB give `fresh = 0` at every point;
  16 KiB gives 20 of 512; 32 KiB gives 1024 of 1024; 64 KiB gives 2048 of 2048.
  The 16 KiB point reproduces inside the same seating (`bmp.rerun.fresh` = 20
  again).
* Line: `w.line.bits = 11222222` — offsets 0 and 8 STALE, offset 16 FRESH.
* **Associativity is the argmin over `T`, and the first version of this argument
  was circular.** What was written first — *"T = 8,192 is exactly the way size
  of a two-way 16 KiB cache"* — assumes the answer to explain the number it then
  offers as evidence. `M = 3` alone is equally *two ways in one set* or *one way
  in two sets*. What discriminates is which `T` minimises `M` over
  {2048, 4096, 8192, 16384}: `(8192, 3)` is unique to 16 KiB two-way, and
  `w.assoc.capped = 00000000` says `T = 16384` really was tried and really did
  not yield `M = 2`, so direct-mapped is excluded by a reading rather than by
  assumption.
* **A second argument, from a different observable in the same run, agrees** —
  different observable, not an independent execution, and the difference matters:
  the one cached function that must run between patch and exec sits at set 30
  under 16 KiB/2-way/16 B. Under
  direct mapping it would evict its victim at *every* working set, so `w.size`
  would read non-zero at 1, 2, 4 and 8 KiB. It reads zero at all four. And the
  first FRESH victim in the boundary rerun is `k = 15`, also set 30 — one in
  ~128 by chance.
* ⚠️ **512 sets is 推.** The set count divides by a line size neither the
  associativity cell nor the size cell can see.
* `docs/rlx-cache-and-cp0.md` § *On silicon* ⓐ, `SPEC.md` `CPU-25`,
  `bench/2026-08-30/`.

**② This core retires the MIPS-II `cache` instruction. 量, positively, with the
positive control in the same run under the same handler.**

* Four ops — `c11`, `c10`, `c15`, `c19` — all return `n = 00000000`, i.e. they
  retired.
* **The positive control is what makes that mean something**: `x ri` in the same
  run under the same handler traps with `cause = 00000028`, ExcCode 10 =
  Reserved Instruction. The cell was written to accept either outcome — *retires,
  or takes an RI* — and it came back the first way. `SPEC.md` `CPU-44` residual.

**③ `Status.IsC` and `SwC` are not implemented as bits, and the refutation
condition did not fire, so the reading carries information. 量.**

* `s.before = s.set = s.restored = 1000FC00`; bits 16, 24 and 6 none of them
  stick.
* The refutation condition was *"`Status` has no write mask at all"*, which
  would have made the reading meaningless. It did not fire: the two control bits
  also read back 0. `SPEC.md` `CPU-19` residual ②.

### What `R1h` did not establish

* 🔴 **Decision ② — whether a cached read sees a write the CPU did not make, and
  whether any command invalidates a clean line. Still 未定** after the first of
  the two seatings its stop-loss allows. `c-A0`, the negative control, ran
  **first** and returned `P1`, precisely so that a negative `c-A` could not be
  read as a dead cell; `c-A` then came back negative, there was no stale line to
  act on, and the payload's own interlock voided Group V. 🟢 **The instrument
  reporting its own cells as void, rather than as passes, is the reason this is
  a structured undetermined and not a gap.** `SPEC.md` `CPU-45`.
* 🔴 **The size measurement cannot separate a 16 KiB I-cache from the 16 KiB
  instruction scratchpad, because they are the same size.** `w-imem` is the cell
  for that and it stays 未定: `w.imem.differs = 00000000` and the payload
  printed `IDENTICAL -- and that is also the no-op reading`, because CP0 20 is
  write-only, so nothing here confirms the `CCTL 0x020` was even accepted.
  `SPEC.md` `CPU-46`.
* 🔴 **Write-through versus write-back-without-write-allocate** (`CPU-19`
  residual ①) — unchanged from `R1-gate`, and it follows `CPU-45`, so it could
  not have been closed here.
* **The scratchpad's extent.** CP3 r0 and r4 both read `20000000` and both tops
  read `00000000`, so what exists is a start address, not a window.
  `CPU-46` residual.
* **The D side has no geometry at all.** The kernel's boot line prints
  `dcache: 8kB/16B`; 讀, that is `arch/rlx/bsp/bspcpu.h` — a build constant.
  Group V never ran, so recording the printed line as *the geometry* would have
  laundered an unmeasured 8 KiB in beside a measured 16 KiB.
* **Associativity has one route in this gate.** A second and independent one
  arrived on 2026-08-31 — at the eviction walk's boundary the re-executed
  victims come back as ten `{k, k+256}` pairs with no singleton, which two-way
  predicts and direct-mapped does not — but that was `R3`'s seating, not this
  gate's, and it is not credited here.

---

## 2026-08-31 — `R3` (my kernel boots to a shell and pings)

### One line

A kernel built from this repository's declarations booted this device from RAM
to a shell that answers a typed command and pinged the workstation in both
directions — and the identification is **positive**, by strings the vendor image
cannot produce, rather than by the absence of vendor strings.

### Three claims that stand

**① The kernel that booted is mine, established by three discriminators the
vendor image cannot produce. 量, on one boot.**

* The image header's `start address: 0x80003600`, against the vendor-staged
  `0x80003440`.
* `RLXFW-B00` — a string that exists only in this tree.
* The build stamp `(key@K) … #1 Fri Aug 28 23:37:47 CST 2026`.
* **This matters because the anti-DoD was designed to be positive**: the loader
  re-stages `0x80500000` from flash after a watchdog reset, so a banner on the
  screen is not evidence of anything. Three strings that only one image can
  contain are.
* Eleven boot marks (`B00`–`B10`), each a row in `config/rlxfw-marks.tsv` with a
  reason, applied by `tools/rlxfw-marks.py` to a **staged** tree — the tool
  refuses any insert that is not one of four declared forms, refuses any path
  under `src-vendor/`, and refuses an anchor that occurs more than once. All
  eleven printed.

**② It reaches a shell that returns output from a typed command, and it pings —
confirmed on both sides. 量.**

* 4/4 replies on the board, and the host's own capture holds both the request
  and the reply. One direction alone would not separate *the board answered*
  from *something answered*.

**③ Every one of the gate's five DoD rows was decomposed into a checkable claim
before the gate was attempted, and the reading was taken against that
decomposition rather than against a recollection.** `notes/kernel-build.md`
§21.4 reads the DoD one row at a time; §21.6 reads the refutation condition, the
two decisions and the stop-loss the same way. **Neither decision's refutation
condition fired and none of the four stop-loss lines was reached.**

### What `R3` did not establish

* 🔴 **`G8b`'s sentence is still unsayable.** No flash-write command was issued
  in any seating of this gate, and *that is not the same sentence as "not one
  flash byte is written"*. The `FLR` bracket reaches **1,024 of 4,194,304 bytes
  = 0.0244 %** and `H601` **512 of 8,192 = 6.3 %**; it cannot see two writes
  that cancel, nor any write outside four 256-byte windows. No full re-dump ran.
  `SPEC.md` `FLS-20`.
* 🔴 **There is still no driver of mine.** D5's ping went out through the
  vendor's `rtl819x`, in the vendor's own configuration. `R6` is the gate that
  changes that sentence.
  🔄 **Expired, and the sentence beside it was imprecise when it was written.**
  This file records what `R3` said on the day it closed and that record stands,
  but a reader reaching it today must not carry the present tense out: a driver
  of mine executed on the silicon on **2026-09-03** (`R5-1`, the timer) and a
  second on **2026-09-06** (`R5-4`, a `gpio_chip`). What `R6` changes is
  narrower than *no driver of mine* — it is the sentence about the **network**,
  which is the one D5's ping actually rests on. The live claim, with its five
  successive narrowings, is `docs/KNOWN-ISSUES.md`.
* 🔴 **D3's written observable did not exist.** The criterion for *early
  bring-up completes* was the string `MemTotal:`, which this kernel never prints
  in any configuration — it is a `/proc/meminfo` field, not a boot message. The
  row passed on a substitute. A DoD whose observable does not exist is a defect
  in the DoD, and it is recorded rather than quietly repaired.
* **`R3-2`'s `TC-d` half stayed half-done for one step**, carried as a debt in
  the running-order note rather than counted as a pass.
* 🔴 **`R1h`'s decision ② is still `R1-gate`'s.** It was answered on the D side
  by a bare-metal payload and not by the gate that owned it, and `CPU-45` is
  still 未定.

---

## 2026-09-01 — `P4a` (reproducible build)

### One line

The same tree built twice now produces the same image byte for byte, twice over
on two independent pairs — **at Level 1, which is one machine**, and the tension
the gate opened on turned out to be one fourteenth of the problem.

### Three claims that stand

**① Two independent pairs of builds are byte-identical. 量.**

* `p4a1`/`p4a2` → `c956c5b7…`; `p4a3`/`p4a4` → `4fc20ce4…`. The two pairs differ
  from each other because `ID0` was added between them, which is the intended
  behaviour and not a failure of the first pair.
* A third build of the first recipe (`p4apc2`) reproduces `c956c5b7…`.

**② The positive control holds twice, and the second time it refuted the DoD's
own wording. 量.**

* `PC-1`: one byte of a string literal moves the sha256.
* Adding `ID0` from a declared row moved `c956c5b7…` → `4fc20ce4…`.
* 🔴 `PC-2` was written to fail and did: changing one byte inside a **comment**
  in the same file left the image byte-identical. The gate board's wording —
  *"the positive control that changing one source byte changes it"* — is false
  as written; it needs *that reaches the image*. **The outcome was predicted
  before the run, because a control that can only come out one way is not a
  control.** Recorded as a defect in the DoD rather than repaired silently.

**③ The 84 differing bytes were two causes, not one, and the one the gate's
opening tension was about is six of them. 量, `tools/repdiff.py` (16 controls,
12/12 mutants killed).**

* 6 bytes are the kernel timestamp; 78 are `gen_init_cpio`'s `time(NULL)`, whose
  fix costs no anti-DoD leg at all.
* Freezing the stamp does not remove an anti-DoD leg, it removes that leg's
  *which build* role — and `RLXFW-ID0`, a sha256 over `config/` as bytes, takes
  it over. `rlxfw-marks.py verify` finds 12/12 marks present exactly once and 0
  in the vendor tree.

### What `P4a` did not establish

* 🔴 **Level 2 is open, and it is one item.** 讀: this drop's
  `scripts/mkcompile_h` has no `KBUILD_BUILD_USER`/`_HOST` (those reached
  mainline after 2.6.30) and writes `(key@K)` from `whoami`/`hostname`, so a
  third party rebuilding the published recipe gets a different banner and a
  different sha256. **Nobody but this workstation can reproduce `4fc20ce4…`**,
  and *the binary really came from the source I published* is Level 2's
  sentence, not Level 1's. Of the seven Level-2 hazards, **three** were settled
  by reading or measuring (`L2-2` `LINUX_COMPILER`, `L2-3` the build path,
  `L2-4` the initramfs mtimes); **one is untestable on this host** (`L2-5`,
  `LC_ALL` — `locale -a` returns three locales, so nothing here can distinguish
  a driver that pins it from one that does not); **two are unmeasured and
  bounded** (`L2-6` `.version` under `--keep`, `L2-7` kbuild's link order
  against `readdir`).
* 🔴 **Two builds, one machine, one afternoon.** Nothing here says the build is
  reproducible next month, on another WSL kernel, or after a `src-vendor`
  re-clone.
* 🔴 **`ID0` has never been read off the board.** It is checked in the image;
  no seating has printed it, so its value on the wire is 推.
* **The `.text` of `p4a3` is not the `.text` of the image that booted.**
  `quietm` and `loudm` are what `SPEC.md` `FW-27`/`FW-31`/`FW-32` are measured
  on; this gate did not rebuild those and does not claim to.

---

## 2026-09-01 — `P4b-gate` (the part of the release process that blocked tagging)

*(Written 2026-09-02. 🔴 **This entry is late, and the reason is the first thing
it has to say: `P4b-2` created this ledger with five entries, and the gate that
did it was closing that same day and did not put itself in.** `D2`'s own
property is *one entry per closed gate*; the only exclusions this file documents
are `S0` and `R0`, on a hindsight-contamination argument that does not apply
here — one day, and no gate has closed in between. So this is an omission that
was found by reading, not a decision that was made. It is placed in close order,
before `R4`, so the operating clause below reads the sequence it would have read
had the entry existed on the day.)*

### One line

Four obligations that `CHARTER.md` §110 imposes and no gate on the board owned
now have a committed owner each — and the gate that gave them owners did not
give the *rule* one.

### Three claims that stand

**① Version → contents has exactly one committed owner, and the repair found a
second copy nobody had flagged. 量.**

* `README.md` § *Which gates make which version* is the owner. `PROGRESS.md`'s
  Release clock dropped `Contents` **and** `Target`; `plan/CHARTER.md` dropped
  its 內容 column; `CHANGELOG.md`'s `v0.2` section stopped opening with a
  pointer into a gitignored file that was shipped inside a public release.
* 🔴 `Target` was never this file's quantity either — it carries CHARTER's own
  `×1.8` multiplier and agreed with §88 on **two of six** rows.

**② This ledger exists and is readable from the public repository — and the step
row's claim about it was false. 量.**

* `docs/GATE-RESULTS.md`, committed, English, one entry per closed gate.
* 🔴 The row asserted that all four owed entries already had their *what it did
  not establish* written. Two did (`notes/kernel-build.md` §21.7 for `R3`,
  `notes/reproducible-build.md` §7 for `P4a`). **`R2a/b/d` and `R1h` had
  none** — what they had was four *What could still be wrong* sections, and
  *doubt about a claim already made* is not *a list of what was never
  established*. Those two entries were derived, not copied.
* 🔴 `D2` named a **path** (`study/weekly-results.md`) and the property it
  wanted was unreachable there, because `study/` is gitignored and the owner
  ruled it stays that way. Recorded as a defect in the DoD's wording, the way
  `R3`'s `D3` was.

**③ A released version now says what it contains and what it does not
establish, and the release itself exists. 量.**

* `CHANGELOG.md` has a `v0.2` section carved out of `Unreleased`;
  `docs/KNOWN-ISSUES.md` is the list §110 rule 2 asks for; and the release is
  published, which had never been done for **any** version.
* 🔴 That row carried a count of `KNOWN-ISSUES.md` **three times and was wrong
  twice after the first correction** — 25 → 25 → 26 → 27 → 28 across one
  session's commits. The count was **deleted** rather than corrected a third
  time: the step is *a known-issues list exists*, and how many rows it has
  carries no weight in that sentence, which is exactly why nobody re-derived it.

### What `P4b-gate` did not establish

* 🔴 **That the obligations have an owner in the way that lasts.** Four *items*
  got owners. `CHARTER.md` §110's **rules 2 and 3** are still owned by no gate
  on the board, and `P4b` — the gate whose name they carry — sits at v1.0. The
  carried-forward table's own heading says an item with no owning gate is a bug
  in that table; the same is true of a rule, and nothing here fixed it.
* 🔴 **It wrote this file and left itself out of it**, which is the same class
  of defect one level up: a ledger whose completeness property is stated in its
  own DoD, and no checker for it. Found 2026-09-02 by reading, not by a tool.
* **`v0.1` was never tagged** (`REL-2`), so `D3`'s *a section per released
  version* is satisfied and *per version* is not. The release spans
  `v0.0` → `v0.2` and says so rather than inventing a boundary.
* **`REEL-1` is open**: the take measures 62.2 s against its own 60 s spec.
  **`IMG-1` has no owning gate at all.**
* **Tagging is not in this gate.** The owner's ruling stands: it waits for their
  word and for the take to be shot. So *the part that blocked tagging* is done
  and the tag is not.

---

## 2026-09-02 — `R4` (edit → result, and a reset without the power switch)

### One line

One `edit → result` iteration now runs as a single command that reports a
number — **73.88 s against a 90 s DoD** — and the audit that made it safe to run
unattended found that until that morning the tool could not chain its own two
desk stages at all.

### Three claims that stand

**① The loop's assertion is derived from the build and never typed, and it was
checked against silicon twice on the same day. 量.**

* `rlxfw-kbuild.sh` computes `RLXFW_SRC_ID` as a sha256 over `config/`, the
  compile carries it, `ID0` prints it, and `S8` requires the board to have
  printed the id the build computed. `A3`, 12:15: *board printed b1434383,
  build computed b1434383*.
* The second check is the stronger one: at 12:29 a **fresh build from the
  working tree** computed `b1434383` and `S8` asserted it against the capture
  the **board** produced at 12:15. Two numbers, one from a build minutes old and
  one from silicon, and nobody typed either.
* 🟢 This closes `P4a`'s residual *`ID0` has never been read off the board*.
* The negative side is positive rather than absent: a stale image, the vendor's
  firmware, and the loader's own re-staging of `0x80500000` from flash after a
  watchdog reset all fail `A3`, and `N4`/`N7` are those cases in the suite.

**② The scripted reset is a loop stage now, and its cost is measured. 量.**

* `R4-2` ran 21 resets in a row on 2026-09-01; three more ran inside the tool on
  2026-09-02, all showing `C-8`'s discriminator, all returning a prompt.
* The machine cost of replacing a human power cycle with a stage is **13.21 s**,
  and that is why this gate's total is *larger* than `R4-0`'s pipeline: `R4-0`
  did not count the reset, because it was a hand.
* 🟢 **`entry` was separated from the instrument for the first time.** It is the
  largest gap between two reads that returned data, so its floor is one read
  period; at a 2.1 ms cadence its 2.4 ms was 1.1 read periods and unreadable.
  At a **3.2× finer** cadence (0.666 ms achieved) it reads **2.3 / 2.4 ms** —
  unchanged — and a coarse-grid reset in the **same power cycle** reads 2.3.
  The ruler got finer and the number did not move.

**③ The two guards that make it safe to run unattended were found by audit an
hour before power, and both fired on the board. 量.**

* `S5b` reads the burn flag back out of `0x8040D4A0` between the rescue and the
  upload. `RUNSHEET` `G2`/`H1a` make that mandatory before a `put`; the tool
  went rescue → upload with the loader's **echo** as its only evidence, and
  `C-6` is the measurement that says an echo and that word are two sources.
  **This seating reproduced `C-6` in its own rescue transcript**: `AUTOBURN: 0`
  → `Unknown command !`, `AUTOBURN 0` → `AutoBurning=0`, for all three commands.
* `S6b` reads back what is at `0x80500000` and requires it to be the file `S6`
  sent, **derived from that file and never typed**.
* `--skip S5b` is refused, because a guard a flag can switch off is not a guard;
  `--skip S6b` is allowed, because that one protects the seating and not the
  device, and the asymmetry is written down.
* 🔴 The suite's own positive control caught a bug in the new parser on its
  first run — the console sends CRLF, `$` under `re.M` sits behind the `\r`,
  and every *negative* control passed while the parse returned nothing.

### What `R4` did not establish

* 🔴 **No single invocation has run `S2` → `S7`.** The bench half ran with
  `--skip S2,S3`; the desk half ran with the bench stages skipped. **73.88 s is
  a sum of two runs, not a measured total**, and the entry says so wherever the
  number appears.
* 🔴 **The image the loop builds has never been uploaded by the loop.** `S8`
  read a capture of an image built the previous night from the same `config/`.
  That is the one stage still untested in one command, and it needs the board.
* 🔴 **`--iterations` cannot repeat, and now refuses rather than pretending.**
  `S4` is a loader command and iteration 1 ends with the loader gone; it would
  have died earlier still on an existing output file. **A loop that runs once is
  not a loop**, and `R5` is six drivers.
* 🔴 **Seventy per cent of the bench half is terminator budget and no one has
  measured what it should be.** ≈24.4 s of 34.74. 推 that it can be cut; the
  experiment is to read the largest inter-byte silence out of the boot captures
  this project already holds, and it was not done.
* 🔴 **`--skip S2,S3` was necessary, not chosen, and nothing knew.** Until
  2026-09-02 `--cell-top` defaulted to a literal placeholder and `S3` exited 1
  against it. It survived 26 controls because every one of them either skipped
  both stages or ran in replay. A defect that only the *unskipped* path can show
  is invisible to a suite that never takes it.
* ⚠️ **One person, one host, two runs.** Nothing here is a claim about n, about
  another machine, or about the loop next month.
* **NFS root left this gate**, on `R4-0`'s measurement that it removes 2.2–3.3 %
  of the machine pipeline and none of it for a kernel change. The gate asked for
  that decision to be visible if it went that way.

---

## 2026-09-11 — `R5` (six drivers, and three of them are load bearing)

### One line

Six drivers are in **one** image, that image booted **seventeen** times with
every one of them printing its own observable on every boot, and three are now
load bearing — the tick is mine before userspace exists, the board reboots
unless my watchdog keeps being fed, and an unmodified upstream `leds-gpio` gets
its line from my `gpio_chip` — while the DoD row that asked for a **frequency**
against `CLK-02` was met as a **ratio**, and the row that asked for
`/proc/timer_list` was met by reading something else.

### Three claims that stand

**① Six drivers are in ONE image, and that is a reading over the whole corpus
rather than a count of six seatings. 量.**

* Image `692A2801` carries `rtl819x-timer`, `rtl819x-gpio`, `rtl819x-spi` + MTD,
  `rtl819x-wdt`, `rtl819x-keys` and upstream `leds-gpio`. **Seventeen** boot
  captures, every one **1,637 bytes**, falling into exactly **two** sha256
  values — 14 × `e5938242…` and 3 × `5717da6a…` — whose whole difference is
  **one line**: `RLXFW-G3`, bit 6, the LED the vendor's own `rtl_gpio_timer`
  blinks (`FW-40`, `FW-62`).
* Presence is a mark family per driver in that same capture: `TA0`…`TA9`,
  `G0`…`G8`, `K0`…`K8`, `S0`…`S8`, `W0`…`W5`. `leds-gpio` prints nothing,
  because it is upstream and unmodified; its evidence is `n_writes` moving
  **2 → 4** with every one of the four accounted for.
* 🟢 **The ladder is monotone, and no capture ever loses a family it had.**
  量 over all **85** boot captures under `bench/` that carry an `RLXFW-` mark:
  **1,069 B** (`EA6EE537`, 11 boots, timer alone) → **1,184** (`5DA34246`, 10,
  plus gpio) → **1,318** (`FCE0AF22`, 10, plus spi) → **1,424** (`B417A3E7`,
  10, plus wdt) → **1,424** (`F67EED22`, 19) → **1,637** (`692A2801`, 17, plus
  keys). Seventeen of the 85 carry all five families and they are the last
  seventeen.
* 🔴 **This claim was on no card and no seating measured it.** Every seating
  measured its own driver; the composition is a sweep of the committed captures
  written at `R5-11`. It is offered as the strongest form of `D1` **and** as
  the reason `D1` as written is weaker than it reads: *ten boots each* was met
  per driver on **five different images**, and five images each carrying one
  new driver is not six drivers coexisting.

**② Three of the six are load bearing, and each dependence is a different
sentence. 量.**

* **The tick.** A `clock_event_device` at rating 300, armed from inside the
  kernel (`arch_initcall` arms, `late_initcall` registers), the tick core
  exchanging the devices on **eleven** independent boots — `ce_live=1`,
  `ce_mode=2`, `ce_mode_calls=2`, `ce_handler` `80036D50` → `80036FC4`, with a
  rating-99 device registered as the negative control and never called.
* 🟢 **Before userspace is proved by an ORDERING, not by a field.**
  `RLXFW-TA8` — printed the instant `clockevents_register_device()` returned —
  precedes `RLXFW-B10`, which sits immediately before `init_post()` branches
  into `/sbin/init`. 量 on all eleven captures of seating 14: byte **925**
  against **965** (raw, as captured), **885** against **923** with the
  carriage returns removed. Nothing was asked of the tick core about itself
  and no shell was required. *(🔴 The pair `887 / 925` appears in **nine**
  committed files and reproduces under neither convention; see § the
  corrections list in `LOG.md` 2026-09-11. The **ordering** holds under both.)*
* 🟢 **And it is caused, not asserted.** `cereload` changes TC1's reload and
  the kernel's clock follows: six rows, ratios `1.0000 / 2.0000 / 1.0000 /
  4.0000 / 1.0000 / 10.0000`, each on its prediction to four decimals. At
  reload 20000 the shell answered a `cat` after a `sleep 5` that took **50
  real seconds** and nothing in the kernel could notice. Zero lost ticks over
  **263.73 s** and again over **654.76 s**, `Δjiffies` = `Δirq_count` =
  `Δce_cycles ÷ 2000` three ways, residual **0** in both.
* 🟢 **The watchdog is a strictly stronger dependence than the tick.**
  `BOOTGUARD` arms the hardware at `late_initcall` and feeds it from a kernel
  timer, so from that instant **the board reboots unless code of mine keeps
  running** — which the tick never was, because a tick can be handed back.
  Nine bites in one seating, every one confirmed by the loader's own
  `Reboot Result from Watchdog Timeout!`, and the user path end to end:
  `sleep 400 > /dev/watchdog` reset the board at **143.563 s** against 143.886
  predicted, **−0.22 %**.
* 🔴 **The evidence that this is engineering and not assertion is a REFUSAL.**
  Driver 4.0 refused its own handover on both boots it was given —
  `RLXFW-TA7=FFFFFFC2`, `-ETIME` — with `ce_check_dj=585 / dc=574`
  byte-identical on a cold boot and a warm one. Its pre-check window spanned
  the vendor's NIC initialisation, over which TC1 delivers 574 of 585
  interrupts: **1.88 %** against a **1 %** tolerance, where the same boot at a
  shell loses **1 in 14,385**. **The tolerance was not widened; the window was
  moved.** `SPEC.md` `IRQ-13`.

**③ The independence the whole diff rests on is measured, with a positive
control and a floor of zero, and the instrument's own defect was caught before
it looked at a candidate. 量 ＋ 讀.**

* **Pre-registration is a clock reading, not a promise.** `docs/driver-diff.md`
  § 1 — what the check may look at, its instrument, its controls and its
  verdict rule — was committed at `161862e`, **15:26:24Z**; the clone of the
  second public tree began at **15:27:49Z**. Eighty-five seconds, in `git log`,
  where "I had not seen it" is otherwise unverifiable.
* **Positive control 175, three negative controls 0.** The positive is one file
  present in two SDK generations — **71,494 bytes against 66,608**, so the
  instrument had to see derivation *through divergence*; the negatives are two
  board directories in one kernel, a cross-tree cross-era pair, and **two
  router SoCs that are not Realtek at all**. Baseline: 178,038 identifiers from
  5,081 files, subtracted from every intersection.
* 🔴 **The controls found a defect in the instrument first, which is the entire
  reason they run first.** Both negatives initially read **2**, both times
  `get_system_type` and `prom_putchar` — mainline platform API that every MIPS
  board *defines* because a generic header *declares* it, and the extractor
  skips declarations on purpose. **The fix went to the baseline, not to the
  threshold**, and its refutation condition was written before it was applied:
  *if the positive falls below 100 the fix has destroyed the sensitivity and
  must be reverted*. 量 after: negatives **0 / 0 / 0**, positive **175 —
  unchanged to the identifier** — across a baseline that grew from 71,469 to
  178,038.
* ⚠️ **No threshold was ever introduced.** The floor is **0**, measured on three
  negative controls rather than chosen, and every verdict is *zero or
  non-zero*.
* **What it bought.** Eleven candidate domains across two public ports:
  ten INDEPENDENT, one DERIVED — `ggbruno`'s `prom.c`, four UART macros
  carrying the vendor's own `BSP_` prefix. 🟢 The trees' own copyright blocks
  agree with the instrument and nobody arranged that: the three files with a
  named author score 0, and the two files with **no copyright line at all**
  are `prom.c` and `setup.c`. The DERIVED row lands outside all six drivers, so
  no row of § 3 is voided.

### What `R5` did not establish

* 🔴 **`D4` was not met as written, and this is the THIRD gate whose DoD named
  an artefact instead of the property it wanted.** `/proc/timer_list` exists in
  this kernel — 讀, `kernel/time/Makefile` carries `obj-y += … timer_list.o`
  and `timer_list.c` calls `proc_create("timer_list", …)` — and it was never
  read. `R5-2` used the driver's own `/proc`, which carries both counters
  inside one `spin_lock_irqsave`, and recorded why in place. **Nor is it a
  frequency**: `wall`, `jiffies` and TC1 all descend from one divider, so what
  is 量 is the **ratio** `TC1 : tick = 2000 : 1` and the absolute 200.005 kHz
  stays 推. The ± 50 ppm bar is met by three orders of magnitude against a bar
  that measures the wrong thing.
* 🔴 **The clocksource half is untouched.** `rating` read **0** in every dump of
  every seating and the system's time *source* is still `jiffies`. Only the
  *tick* is this driver's, and `docs/KNOWN-ISSUES.md` has narrowed that row
  six times rather than let it read as more.
* 🔴 **One of the six is not mine.** `leds-gpio` is upstream and unmodified —
  deliberately, because an unmodified upstream consumer binding to my
  `gpio_chip` is evidence a driver of my own cannot produce. The count is six
  only if an upstream driver counts, and five if it does not.
* 🔴 **`D2` is met by a directory nothing has probed and nothing can.**
  Linux 2.6.30 has no device tree at all, so `dt/` is a compile-test and says
  so in its own first paragraph. **Two of the six bindings are not validated
  by default** — `gpio-leds` and `gpio-keys` are kernel-subsystem schemas that
  `dtschema` does not ship, declared by name in `dt/unmatched-allow.tsv` and
  reached only with `--extra-schema`. And `GPIO-1` is open: **which of
  `PABCD`'s four ports bit 5 belongs to has never been measured**, which is
  exactly the claim a gate full of `PABCD` readings looks like it closed.
* 🔴 **Compiling against 6.18 is not upstream acceptance.** `R5-12` produced
  four `.o` files at rc 0 with zero warnings; three of the four would be
  rejected on sight — a hand-rolled `miscdevice` where a modern driver
  registers a `watchdog_device`, a gpio chip with no `of_node` and no
  `platform_driver`, and a `/proc` file on every one of them.
* 🔴 **The loop has still never run `S2` → `S7` in one invocation, and `R5` had
  decided that it would.** `R5-0` ② closed `SEAM-1` as a decision — *the first
  bench iteration runs without `--skip S2,S3`* — and the desk half executed
  (`--mode desk`, `S4..S7 SKIPPED`, and `S-3` rebuilt an image that had run on
  the die byte for byte). 量 over `bench/`: **71 of 71** real `--mode bench`
  invocations across six seatings carried `--skip`, and 71 of 71 uploaded a
  pre-built `--image` with `--recipe-override`. Each skip was locally correct;
  the pattern is what no seating could see.
* 🔴🔴 **2026-09-14 (seating 21): that never-run is STRUCTURAL, and this entry's
  own sentence was the wrong shape.** `looprun --mode bench` with no `--skip`
  is refused **before any stage runs**: the `--image` pre-flight sits above the
  stage loop and requires `os.path.isfile(img)`, and **`S3` is what creates that
  file**. Two arms, both `rc 2`, **zero files created**; the control —
  `--skip S2,S3` with an existing image — passed the same guard and reached `S4`
  in 12.25 s. So *71 of 71 carried `--skip`* is not a discipline finding and
  *each skip was locally correct* is not the whole of it: **the tool cannot do
  it at all**, and establishing that cost no power cycle.
  `notes/dev-loop.md` § 10.6, `SEAM-1`.
* 🔴 **§ 3.7's five, unchanged**: this is not a claim that my drivers are
  better; neither third-party image has been run on this board and neither
  will be; two of the six drivers have **no partner at all** and two more have
  exactly one, so four cells of the diff are ABSENT; the L1 agreement is worth
  a cross-check on my transcription and no more, because three implementations
  describing one part agree *because it is one part*; and `spi` was not
  compared field by field.
* ⚠️ **`.to_irq` is still `NULL`** — no interrupt path passes through the gpio
  chip — and `IRQ-13`'s loss mechanism is **worked around, not isolated**: the
  driver moves its window rather than explaining why the vendor's NIC
  initialisation costs 11 of 585 interrupts.
* ⚠️ **Nothing the system *needs* depends on the gpio chip.** The LED is an
  indicator no code reads back and the button's events have no consumer in this
  image (`FW-46`). A consumer being bound and the system depending on it are
  two different sentences and only the first one moved.
* ⚠️ **The flash sentence did not move.** Zero flash-write commands and zero
  `FLR` across the whole gate; the bracket stands at **1,024 of 4,194,304 =
  0.0244 %**, and `FLS-26`'s ledger — 4,177,920 B proven identical, 8,192 B
  proven different, 8,192 B undetermined — is where `R5-5`'s driver left it.
* ⚠️ **One board, one unit, one operator, and six seatings.** Nothing here is a
  claim about a second N150RT.
* 🔴 **The estimate, and the gate that was supposed to calibrate it.**
  `R5` ran **32 segments** (the 27th to the 58th) against the plan's 小計 of
  **31** — **1.03×** — and against the gate board's `Est.` of 24, **1.33×**.
  The stop-loss was 34, so it closed with **two segments** of margin. 🔴 The
  prior the step list carried and declined to apply — `0.571×`, pooled from
  `S0` and `R0`, n = 2 — would have predicted **17.7** segments: it
  **under-predicts by 1.81×**, and the step list's own sentence *"it is written
  down so a surprise is visible"* is what made that readable. The calibration
  itself is under the gate board.

---

## 2026-09-16 — `R1-pub + R2c` (what this die's instruction set is, and what the kernel and three toolchains believe about it)

### One line

One die's instruction set is measured rather than read — **75 encodings, three
verdicts, and the cell that matters, *does not trap and computes the wrong
answer*, observed once** — with the kernel's emulation surface priced in
nanoseconds and the load-delay hazard walked to the distance where it closes.
**The weakest thing here is not a reading, it is an arithmetic on top of one**:
`D-cost`'s `E5` is a conjunction, eight days of adjudication quoted one half of
it, and the half nobody counted fails five rungs of sixty-four — enough, counted
honestly, to cross that clause's own void threshold on one of the two boots.

### Three claims that stand

**① This die executes four instructions the public record says its family does
not have, and the census that says so has a three-way verdict whose third cell
was observed. 量, with a two-sided negative control that fires and a positive
control that was missing from the DoD for two segments.**

* `probe4`, bare metal, its own exception handler, 75 encodings on one power
  cycle — seating 21, `bench/2026-09-14/C1-P4j.log`: **RAN 16 · RIGHT 16 ·
  TRAPS 42 · WRONG 1**, three channels agreeing on `seal=AF7A728B`, and every
  expected constant derived at the desk and **printed beside the reading**
  rather than compared inside the payload — which is the only reason the third
  cell can exist at all.
* **`lwl`, `lwr`, `swl` and `swr` all read RIGHT.** They execute, and they
  compute the constant the desk derived. The public Lexra statement is that this
  family removed them. `SPEC.md` `CPU-15` carries the refutation with its own
  scope limit: one RLX4181 revision 1, and the LX5280 claim is untouched.
* **The negative control fires and it is two-sided.** `special0e` traps with
  `ExcCode 0x0A`, and `tools/isa-payload.tsv` sets its `expect` **equal to the
  seed on purpose**, so a checker reading the value instead of the exception
  count would say RIGHT and void the table. It said TRAPS. 🔴 **And it is clean
  by one function code**: `simulate_sync` matches SPECIAL `0x0F` and this row is
  `0x0E`; `0x0000000F` would have been silently emulated and reported as *does
  not trap*.
* **The positive control is `D2b`**, which had to be added to the DoD two
  segments after `D2` — `plan:1074`'s pass condition has two halves and `D2`
  restated the negative one word for word and the positive one not at all,
  because a list organised around refutability drops a requirement that has no
  refutation attached. `probe4`'s seven MIPS-I baseline rows must read RIGHT.
  All seven did.
* 🔴 **The third cell is one row, not a rate.** *Does not trap and computes the
  wrong answer* was observed **once in 75**. One observation is what makes the
  cell real; it is not a measurement of how often this core does that.

**② The load-delay hazard closes at one instruction, and the kernel's emulation
surface costs 366–396 cycles a trip. 量, on two independent boots, with a zero
control four orders of magnitude below the smallest number quoted.**

* `probe5`, 24 behavioural hazard rows, same power cycle: **LOCK 15 · OPEN 6 ·
  VOID 3**. The ladder closes at **d1** for `loaduse`, `storedata`, `storebase`,
  `movcond` and `dslot` — one `nop` suffices, and the second one upstream's
  `P9-12` inserts is not needed on this part. `hilo` reads LOCK at every
  distance: **the HI/LO hazard is not exposed here.** `movz`/`movn`'s
  write-enable is exposed at d0, which is the first measurement of that shape on
  this silicon.
* **The surface is one visible census row and its visibility is bounded rather
  than assumed.** All 37 census rows with a payload row were looked at; exactly
  one — `sync` — shows the trap/no-trap difference; and the reason a second
  could hide is written down: an instruction the silicon retires **and** the
  kernel emulates reads *no signal* in both columns, which is `ll` and `sc`.
* **Priced, and every quoted cost is a slope over four iteration counts, not a
  point.** `sync` **988.6 / 989.5 ns** per iteration and `lwu2` **915.6 /
  915.4 ns**, each on two independent boots with its own rescue, upload and `J`.
  At 400 MHz that is **366–396 cycles**, and two different instructions through
  two different handlers differ by **7.4 %** — so the dominant term is
  trap-and-return rather than either handler's body.
* **The zero control is two separately assembled `nop` cells at two addresses**,
  so what it measures is not `x − x`: **0.0014 / 0.0108 ns**, and the smallest
  quoted cost is **84,700×** it. `tools/ucostfit.py` re-derives all of this from
  the two committed captures, and carries three injected corruptions that each
  have to make a named check fail.
* 🟢 **`sc` costs nothing, and the evidence is a sign rather than a number**:
  **+0.187** on one boot and **−0.194** on the other. A quantity whose sign flips
  between boots is zero more convincingly than a small number is.
* 🔴 **`ll` and `sc` are published as bounds, not costs.** Each failed `E4` on
  one of the two boots, and `E4`'s tolerance is a proportion of **the row's own**
  magnitude, so it is ~50× stricter where the noise share is largest. A
  different row failed on each boot, which is the signature of a threshold
  sitting in the noise rather than a property of either row.

**③ Three vendor toolchains spanning eighteen years of gcc give one answer to the
load-delay question, and what differs between them is the `-march` their shipped
`libc.a` was built for. 量, twelve compiler invocations on the die, both controls
held and the anti-control forced.**

* `probe6`, seating 22, `bench/2026-09-14b/C1-P6j.log`: twelve rows, **one
  compiler invocation each**, all compiling the same one-line fragment at
  identical flags. **12 of 12 read the verdict their `pad` column predicted
  before the board was powered.**
* **Same toolchain, two flags → the behaviour changes** — three times, one
  binary each. **Three toolchains, one flag → it does not**: `v4` = `v6` = `v8`
  all LOCK and `v5` = `v7` = `v9` all OPEN, across gcc **3.4.6, 4.4.5 and
  12.4.0**.
* **The controls**: a hand-written `lw; nop; sw` must read LOCK and a
  hand-written `lw; sw` must read OPEN — both did — and the forced anti-control,
  the same payload under `qemu-system-mips`, read **24 of 24 LOCK**, so the
  device's 5/7 split is the device's.
* 🔴 **The plan's own second refutation condition fired here and nothing in this
  repository said so for two days**: *three identical silicon results mean the
  table has no discriminating power, and that is itself a result to write down*.
  `SPEC.md` `TC-59`, `TC-60`.
* 🟢 **What selects is `TC-57`** — the same criterion, `hazlint` clean, applied
  to each release's whole prebuilt `libc.a`: **0 violations against 4,574 and
  3,741**. Both instruments are right, because `-march` is the variable on both
  sides. So `R2c` chooses **`rsdk-1.3.6-4181`**, and the reason is that its
  shipped `libc.a` was built for a core without a load interlock — **not that
  its compiler is better, because measured, there is no difference to have.**

### What `R1-pub + R2c` did not establish

* 🔴 **One die, one revision, one operator.** `PRId` = `0x0000CD01`, RLX4181
  revision 1. Every payload here ran on that unit. The one repeat that exists —
  `FW-74`, 75 rows byte-identical across two seatings — bounds this instrument's
  reproducibility and says nothing about a second part; the other board this
  project owns has never run any of these payloads.
* 🔴 **`R1-pub-3`'s own DoD clause is not met, and the instrument that should
  have said so could not be asked.** *Every hazard test's own control fires*
  reads **21 of 24**: three `cp0` rows' per-row `ctl` control did not fire, and
  those rows are VOID, which `D3` permits — but the clause says *every*.
  `hazpay`'s `check_controls` inspected **2 of 26** declared controls, and the
  probe's own `aux.zero` header field was blind to the same three rows for a
  different reason: it tests *equal to zero*, and the wrong value was
  `0x80500270`. **Both were fixed in the segment that wrote this entry, and the
  clause is still not met — it is merely measurable now.** `SPEC.md` `FW-76`.
* 🔴🔴 **`D-cost`'s `E5` is a conjunction, and every adjudication of it quoted
  one conjunct.** The other — `Δirq_count == Δjiffies` on every rung — fails
  **5 of 64**, all five in the same direction, and counting both takes boot 1 to
  **10 / 32 = 31.2 %** against `E5`'s own ¼ void threshold. 🟢 **The four costs do
  not move**, and the reason is structural rather than a rescue written
  afterwards: the ruler is `comp_tc1 = Δjiffies × 2000 + Δtc1`, `Δirq` is not in
  it, and both of its terms are snapshotted inside one `spin_lock_irqsave` —
  readable in `ucost.c` and in the timer driver with no reference to the outcome.
  🔴 **The clause's defect is that it put two properties under one threshold and
  only one of them bears on what the threshold protects.** 讀,
  `drivers/clocksource/rtl819x-timer.c`: `j = get_jiffies_64()` sits at line 2001
  inside the lock held from 1998 to 2042, and `irq_count` is read live at line
  2147, **105 lines after the unlock**. ⚠️ **And the five differences are not
  explained by that mechanism**: the gap is symmetric in sign and these are five
  of five one-sided. Recorded as an open question, not as a cause. `SPEC.md`
  `FW-75`.
* 🔴 **Four of the eight emulated instructions are unpriced** — the unaligned
  `lh`, `lhu`, `sh` and `sw`. `E7` required the number to be in the write-up
  rather than discovered by a reader, and it is; the rows are still unpriced.
* 🔴 **Whether an unaligned access costs an exception on BARE METAL is
  undecided.** `CPU-15` measured the four unaligned *instructions* executing at
  the loader prompt; `CPU-75` measured an unaligned *address* costing 915 ns in
  Linux user mode. Two states of one machine, neither refuting the other. The
  deciding experiment is timing the same `lwu2` at the loader prompt, and it
  needs a payload and a seating.
* 🔴 **`R2c`'s mandatory silicon row decided nothing.** The plan calls it the
  only cell that can kill the project silently; it has no discriminating power
  between the three columns. What decided was a desk criterion applied to a
  different artefact, taken for a different step, on a later date — and that
  sequence is why § 8.3's *refuted if a new criterion has to be introduced to
  break a tie* did not fire. It came nearer than a clean confirmation reads.
* 🔴 **A cell the plan names is empty in all three toolchain columns**:
  compressed rootfs size. `R7`'s budget wants it, and this table has no root
  filesystem to compress.
* 🔴 **`docs/rlx-isa.md` is not yet a document an outside reader can use.** It
  compresses eight owner files and assumes its reader knows what rlxfw is. Every
  claim in it is checkable from a clone — § 9 is that table, and one row of it
  was a promise the page could not keep until the day the gate closed — but
  *checkable* and *readable by someone who did not build it* are different
  properties and only the first is established here.
* ⚠️ **`R2c`'s 2-段 cap cannot be scored, and nothing in this repository counts
  it.** Charged three defensible ways, the gate spent **1, 2, or 3–4 段** on it.
  The stop-loss's prescribed remedy — drop the third toolchain and ship two
  columns with the omission named — is **inapplicable**, because all three
  columns are already on silicon. A fired stop-loss whose remedy is impossible
  needs a decision, and this entry records that it did not get one.
* ⚠️ **The population was not widened.** Six `r1b` hazard rows have no cell the
  trap/no-trap vocabulary can fill, and the five unaligned forms have no census
  row and cannot have one under `docs/isa-prior-art.md` § 0's admission rule.

---

## 2026-09-16 — `R1z` (the debts this repository's own record names)

### One line

**v0.3+, three desk segments, zero power cycles.** `tools/cfcensus.py check`
goes from **29 findings to 0** over seven checks, and the instrument that
reports it becomes a gate rather than a ratchet — so a debt with no owner can no
longer be *created*, where before it could be created and found by a later
census.

**The weakest thing here is not a reading, it is a scope**: every number below
is about this repository's record, not about the device. Nothing was measured on
the silicon; the board was unpowered for all three segments.

### Three claims that stand

**① The debt table's own rule — *an item with no owning gate is a bug in this
list* — is now enforced, and every one of the 29 findings was reached by
measuring the item rather than by reading the row.** 量 2026-09-16: `L1` 11→0,
`L2` 1→0, `L3` 5→0, `L6` 4→0, `L10` 2→0, `L12` 2→0, `L15` 4→0.
`cfcensus --self-test` 64/64; `ratchet` at an all-zero `BASELINE`, which is what
makes it a gate — any check leaving zero in either direction is red, and it
names which check and which rows. **No CI step and no `ci-expected.tsv` row
changed**: 量, `check`'s clean output carries no two-space `ok` line and
`ratchet`'s does, so moving the constants was the whole change.

**② Eighteen step rows of four closed gates carried no closure mark, and
measuring them found that *none* of them was unfinished.** 讀
`spec-check.progress_step_state`: closure is read *from the FIRST cell only*.
Nine rows of `R1-gate`/`R4` had no mark anywhere and are now marked; nine rows of
`P4a`/`P4b-gate` carried `✅` in a `done` column their table heads — a **second
owner** of one piece of state, which is house rule 1's subject and is recorded
rather than repaired. 🔴 **The checker was NOT changed.** Its own docstring
carries the argument against changing it: *a checker that stops reporting
because a DIFFERENT tool got smarter is a debt paid by nobody.*
🟢 `R1g-3` was nearly ticked wrongly — `LOG.md`'s section on it is headed *`R1g-3`
的完成定義其實沒滿足* — and reading the whole section showed the DoD was found
unmet mid-segment and then met by `PREDICTIONS-b4-block0.md` alone. The tick
stands and the caveat went into the column headed *where it is most likely to be
wrong*.

**③ Two id collisions were real and are resolved by the earlier user keeping the
id.** 量 by `git log -S`: `CFG-2` was established by the closed timer-comment row
(`bd9fecd`, 2026-09-04) and re-used by the open two-gates-on-no-path row
(`b1a25f8`, 2026-09-08) → the later is `CFG-3`; `REL-3` was established by the
`study/weekly-results.md` row (`2266324`, 2026-09-01) and re-used by the release
row (2026-09-11) → the later is `REL-4`. 🔴 `LOG.md` and `CHANGELOG.md` keep the
old names **deliberately**: they are dated records, and editing one to agree with
a later rename falsifies it. 🟢 And the `REL-3` half ended with `L9` — the
exemption-rot control — firing on cue: marking the closed row made
`L8_EXEMPT['REL-3']` dead within the minute, and it was deleted.

### What `R1z` did not establish

* 🔴🔴 **This census cannot see a debt that has already been PAID.** Its
  population is the table and the table is a claim. 量 2026-09-16: of the rows
  disposed of here, **five had been paid while the record still carried them as
  owing** — `UP-AUD-1` ③④ (paid 13 h 43 m *before* the step row that named them
  as outstanding was written), `①c` and `②`'s third sub-item (one commit whose
  message never names the row), `②a`, and `docs/isa-prior-art.md` § 7 (repaired
  at 03:50:57 and carried as stale by three consecutive closeouts). The file's
  own ⚠️ already says it is blind to a debt never written down; **this is the
  same blindness with the sign flipped, and nothing here fixes it.**
* 🔴 **Four of the findings this segment cleared were created by this segment**,
  and every one was caught by a tool rather than by re-reading: a retraction that
  names what it retracts outside the `~~ ~~`; an owner cell explaining a gate is
  `已關`, which is a token the table's own closure detector reads; a standing
  instruction written as prose where the rule wants a clause head; and a new
  `FILE:NNN` citation onto a blank line, written in the same commit as the
  disposition that says line citations rot. **A fifth appeared when the gate
  closed**: every disposition put `R1z-2` in the owner cell, so eleven rows read
  LIVE by pointing at the step that was disposing of them — circular, and
  invisible until the step was marked.
* 🔴 **`UP-AUD-1` is not finished.** Thirteen of fourteen faces are paid; `⑤c`
  needs a build artefact and this gate ran no build. Re-owned, first handover.
* 🔴 **`CI-5` is `⊘`**, with a re-open condition rather than a plan.
* ⚠️ **`RECIPE_ID` moved** (`CFG-2`→`CFG-3` inside `config/`, and the initramfs
  table's new build commands). No card was frozen against the old value —
  measured, every `bench/` directory already holds captures — but **the next
  card must re-derive `RLXFW-ID0`.**
* **Zero flash-write commands, zero `FLR`, board unpowered throughout.** The
  bracket stays at 1,024 of 4,194,304 bytes = 0.0244 %.

---


## 2026-09-17 — `P1` (a production test, and every check made to fail once)

### One line

**v0.3+, four segments (81st–84th), one power cycle against the one budgeted.**
`config/mfgtest.sh` runs eleven checks on this board. Seating 25 returned
**11 of 11 on a good unit**, then turned **five of them red by physical
injection** — each red specific to the check its row named, each revert measured
before the next injection, and all of `P1-4` for **zero resets**. **The second
half is the gate; the first half is a demonstration**, which is `PROGRESS.md`'s
own sentence written the day the gate opened and not softened since.

**The weakest thing here is not a reading, it is a denominator.** Five of the
eleven live rows are class `S` — simulated at the boundary, so they prove the
check's logic and not its wiring — and 量 2026-09-17, **the two files that say
so both said *four***, from the commit that wrote them.

### Three claims that stand

**① `D2` is paid, and what makes it a payment rather than a demonstration is
that three of the five injections were RE-SPECIFIED against the implementation
before the board was powered.** 量 seating 25: five physical injections, five
kills, each one specific — `M25` `lock 6` (`dat=0000003C bit6=0 (want 0)
n_set_ok 2->2 n_writes 4->4`, the refusal ordered *before* the write rather than
logged after it), `M26` no press (`n_open 2->3 n_poll 2200->2600 b0_n_press
1->1` — the first two terms **move**, which is what makes the third one mean
something), `M27` `corrupt 0x9000` (`diff_units=1`, and **only** `MT-FLASH-3`
red: `8 of 9 ok`), `M28` `cereload 20000` (`reload=20000 want=2000`), `M29`
`stop` (`state=STOPPED (want BOOTGUARD)`). The `WRONG-CASE` control never fired,
every revert was read back before the next injection (`9 of 9 ok` four times,
`1 of 1 ok` once), and `tools/mfginject.py` carries the other 25 rows
host-side: **25 of 25 killed, 0 alive, 5 stood down for `P1-4`** — the stand-down
declared as one skip line rather than as a smaller green.
🟢 **`M25` was read in BOTH directions, and the readout is a photon.** Locked, a
request to turn the lamp *off* left it lit; unlocked, the same request turned it
off (`dat 0000007C`, `n_set_ok 3`, `n_writes 5`); locked again, a request to turn
it *on* left it off (`n_set_ok 3->3 n_writes 5->5`). **The card wrote only the
first direction, where the operator's word is *lit* — the same word as the pass
path.** The two middle cells are off-card and the reason is in
`bench/2026-09-17/CORRECTIONS-block23.md` § 5: *a guard that has only ever been
seen refusing is a wall.*
🔴 **Two of the five could not have gone red as written**, and both were caught
at the desk: `M26` because nothing in `mt_button` opened `/dev/input/event0`, so
the counters were flat whether or not anyone pressed; `M29` because `kickms`
moves neither field `mt_wdt` reads — it lets the hardware bite, which ends the
boot instead of reddening a check. **That second correction is why `P1-4` cost no
reset at all.**

**② Six defects were found by reading a THIRD PARTY, never by re-reading the
thing under test — and the sixth was found by the good unit itself.** 量: four
of the eleven checks could not have gone green on a healthy board, and two of the
five injections could not have gone red on a broken one. The third parties were
the driver's own header (`rtl819x-keys.c:91-103`), the built `.config`
(`p11d.config-built:769`, `# CONFIG_INPUT_EVBUG is not set`), **this project's
own card from `bench/2026-09-10`**, two programs' format strings (`%08X` against
`sha256sum | cut -c1-8`, compared with `=`), and this unit's own busybox `ash`
under `qemu-mips-static`.
🔴 **The obvious fix for the case mismatch was refuted before it shipped.**
`$((0x$want))` is correct under `dash` and wrong on this die: 量, `$((0xb1818b92))`
saturates to **2147483647** in this unit's `ash` against 2978057106 on the host,
so a 2 × 2 (two shells × two forms) has the arithmetic version green under `dash`
and **red under the shell that matters**. The shipped fix is a string fold.
🔴 **The sixth was the good unit refuting the card.** § 5 predicted `9 of 9`;
`C1-AUTO` returned **`8 of 9`** with a clock that was entirely healthy, and the
capture is kept. Two independent causes: a 2.6.30 `read_proc_t` re-renders its
whole page on every `read()` while the shell's `read` builtin consumes one byte
per call, so a free-running field that grows shifts everything after it
(`FW-87`); and this shell saturates its arithmetic, so with `jiffies` counted
from `INITIAL_JIFFIES` **every jiffies delta taken on the device is 0**
(`FW-88`). 🔴🔴 **The second of those had been measured three hours earlier, at
the desk, in the 2 × 2 above — and was not asked of a second place.**

**③ `D3`'s second conjunct was met by an instrument roughly four thousand times
larger than the one it names, and the one it names never ran.** `D3` says *the
`FLR` bracket is byte-identical across the gate*; 量, **zero `FLR` ran in `P1`**
— `grep -rn FLR bench/2026-09-17/` returns nothing. What stands in its place is
`MT-FLASH-3`'s own map: 32 groups over **4,186,112 bytes** (`H601`'s 8,192
skipped by rule, `map_h601_hashed 0`), **line-for-line identical to
`bench/2026-09-09b` and `bench/2026-09-10`** eight days earlier, with
`map_diff_units 0` and `corrupt_at -1`; and **nine** `MT-FLASH-2` readings across
the seating, `n_write_refused` stepping 2 → 16 by twos and `n_writes` reading
**0** in every one. The bracket covers 1,024 bytes; the map covers 4,186,112.
⚠️ **More coverage, less independence, and the difference is not decorative**:
the `FLR` bracket reads flash through the *loader*, with Linux not running and my
driver not loaded, while the map is computed by the same driver whose writes it
is being used to rule out. `n_writes 0` comes from that driver too. **The gate's
flash evidence is therefore wider and shallower than `D3` asked for**, and
`FLS-26`'s ledger does not move.

### What `P1` did not establish

* 🔴🔴 **The design table over-declares on THREE rows and only one of them was
  ever caught.** § 2 is the gate's own DoD input for `D1`, and 量 2026-09-17,
  comparing all eleven pass criteria against the eleven implementations one row
  at a time: **`MT-TICK`** declared `/proc/interrupts` as a second input and the
  script never read it — found at seating 25 and struck in place;
  **`MT-PORT`** declares *"link up on the connected port, **and the output names
  the vendor driver**"* and `mt_port` prints `chk MT-PORT 1 "$MFG_PORT LinkUp"`,
  which names the **port**; **`MT-MAC`** declares *"body checksum 0"* and
  `mt_h601`'s `MT-MAC` condition is `rc && sig && ver && sane && nz && nf && !gb`
  — `hw_sum_ok` is deliberately in `MT-RFCAL`'s condition alone, so a unit with a
  valid header and a broken body checksum scores `MT-MAC` **ok**. All three
  over-declare in the same direction: the table claims a conjunct the script does
  not test. 🔴 **`MT-TICK`'s instance was found, written up and struck, and
  nobody looked at the other ten rows** — which is verbatim the sentence the
  previous segment closed with (*a measurement that refutes one line usually
  refutes two more, and nothing here goes looking for the other two*). This is
  the first time something went looking, and it found exactly two.
* 🔴 **And `MT-PORT`'s missing conjunct is the one `R6` needs.** The plan's own
  ordering note for `P1` says the port check runs against the **vendor's** driver
  until `R6` lands, so *「要在 `mfgtest` 的輸出裡寫明白是哪一支在跑，否則 R6
  落地之後那一格的歷史數字沒有意義」*. The design row promised exactly that and
  the implementation does not print it, so **every `MT-PORT` line this project
  has captured is unlabelled as to which driver served it.** Carried to `R6-0`.
* 🔴 **Five of eleven live rows are class `S`, and § 5 — the section whose whole
  job is to understate nothing — said four.** 量 by two independent routes
  (a column parse with an escaped-pipe guard, and a separate `awk` pass):
  `S` 5, `R` 4, `P` 2. `git log -S` puts the sentence and the `MT-ID` row in the
  **same commit**, `e362ffa`, so it was wrong on the day it was written rather
  than gone stale. Corrected in place today, original quoted. **Nothing in this
  repository counts a table column**, which is why five weeks of gates and a full
  desk sweep walked past it.
* 🔴🔴 **The map digest this gate publishes does not re-derive from the committed
  capture.** `ae87ac03269985d6` is quoted in three files as the digest over the
  32 map lines; 量, `sed -n '19,50p' X8-M0.log | sha256sum` gives
  **`70484defc9714ecc…`**, and the published value comes back only after
  `tr -d '\r'`. Every capture here is CRLF and **no file says the lines are
  CR-stripped first**, so a reader re-deriving it concludes the flash moved.
  🔴 **This is the same root cause as the four false stops the previous segment
  recorded** (`[ "1\r" = "1" ]` is false) **and it is the fourth consumer** — the
  first three were gates, this one is a published number. Negative control: 31 of
  the 32 lines give a third value.
* 🔴 **The independent rate reference `MT-TICK` needs is measured and is not
  wired in.** 量 `FW-91`, one boot, the same cell shape twice with one `cereload`
  between: normal `Δ`line 13 = **503**, `Δ`line 25 = **503**, ratio **1.000**;
  at `cereload 20000`, **5,009** and **501**, ratio **9.998**. 🟢 The number that
  matters is the **501** — the kernel's own view of elapsed time is identical
  whether its clock is right or ten times slow, which is precisely why an
  internal comparison can never see the fault. ⚠️ Line 13's rate comes from the
  same timer block, so it is independent of **this driver's reload** and **not**
  of the SoC's divider. `config/mfgtest.sh` reads `/proc/interrupts` in
  **comments only** (`:461`, `:463`), and that comment still describes § 2 in the
  present tense after § 2 was struck. ⚠️ **And `FW-91`'s declared second source,
  `s25-X9-irq.log`, is not in this repository** — 量, `git ls-files | grep s25-`
  returns 0.
* 🔴 **No capture holds an operator's answer.** 量: five captures contain the
  string `OPERATOR`, one occurrence each, and every one is the **prompt**
  `mfgtest` printed. The register half of each pairing *is* in the capture and
  closes exactly — `n_set_ok` 1→2, refused, →3, refused, 4→5 with `n_set_no 2`
  counting the two refusals; `n_poll` +400 / +1800 / +400 against windows of
  20 / 90 / 20 s at 20 Hz, to the poll. **So the human readings are anchored, not
  unanchored — but they live in `LOG.md` and the corrections file, and a reader
  with only `bench/` cannot recover them.** `MT-LED` and `MT-BUTTON` are the two
  checks whose verdict a machine cannot reconstruct from the evidence directory.
* 🔴 **`MT-ID`'s verdict line is never machine-readable, and the script's header
  claims the opposite.** `FW-89`: 量, `^  (ok|FAIL)  +MT-ID ` matches **0 of 9**
  auto captures while the ` of 9 ok` summary matches 9 of 9 — `rlxfw_mark()` and
  ash's echo interleave deterministically at that exact position. The header says
  the line shape *"is the one `tools/ci-census.py` already parses"*, which is true
  for eight of nine. **The machine-readable contract is the summary, not the
  per-check lines**, and the header has not been narrowed to say so.
* 🔴 **A fourth check compares across time and does not use the snapshot.**
  `config/mfgtest.sh`'s own comment says *ONLY THE THREE CHECKS THAT COMPARE
  ACROSS TIME USE THIS … because those files' fields are static between verbs* —
  and `mt_flash2` reads `$P_SPI` live before and after `act "$P_SPI" trywrite`,
  requiring `n_write_refused` to move by 2 **across a verb**. The stated reason
  names the property that makes the other eight safe and excludes precisely this
  one. Whether `/proc/rtl819x-spi` has a field that moves *within* one traversal
  is unmeasured; the nine readings taken are clean, which is an observation and
  not a proof.
* 🔴 **`MFG_SHELL`'s target-shell pass stays bench-only, and that is this step's
  decision rather than an omission.** `tools/mipsash.sh` runs all 25 injections
  and all six controls under this unit's own busybox `ash`, and the thing it runs
  is this device's userspace carved from its flash dump, which `CLAUDE.md`'s Never
  table forbids committing. **It is not written as a declared skip row**: a skip
  row in `ci-expected.tsv` declares work CI *would* do given the population, and
  the population here can never exist on a runner. It refuses rather than falling
  back (量, `rc=2` on a bad `RLXFW_UNIT_ROOT`), and that refusal is the honest
  form. ⚠️ So the `ci-expected.tsv` not-run ledger does **not** account for it,
  and this paragraph is the only place that says so.
* **Flash writability is untested** — the substitute tests that the write path
  refuses, which is a different claim. **DDR is untested** and struck with its
  reason. **Four of the vendor's eight factory-test areas** — TX power, RX
  sensitivity, PSD, thermal — are outside what this project can measure at all.
  **The unit's identity is the host's, not the device's**: the serial-equivalent
  is its MAC, which may not enter this repository.
* ⚠️ **`MFG_BUTTON_SECONDS` still defaults to 20**, which is too short for this
  project's bench protocol — the operator cannot see the console, so the window's
  start cannot be tied to a conversation turn. 量: the variable appears nowhere in
  `docs/mfgtest.md` and nowhere in `tools/mfginject.py`; the 90 s override that
  made `MT-BUTTON` pass exists only inside two capture files. Changing the default
  needs a rebuild and `RECIPE_ID` is a digest over `config/`, so it is `R6`-era
  work.
* **Zero flash-write commands, zero `FLR`, `n_writes 0` in all nine
  `MT-FLASH-2` readings.** The `FLR` bracket stays at 1,024 of 4,194,304 bytes =
  **0.0244 %**, untouched by this gate.

---

## 2026-09-22 — `R6` (an Ethernet driver of mine, and a memory model that had to be measured before a single ring was allocated)

### One line

**v0.4+, eighteen segments (84th–101st), thirteen seatings (26–38).**
`rtl819x-nic` and `rtl819x-switch` bring this board's CPU port up and carry
traffic: `rlx0` pings both ways with a **positive** discriminator, moves
**17.03 / 17.76 / 17.09 Mbit/s** of bulk TCP (n = 4, one collapse, reported),
and survives **31.66 minutes** of continuous flood with `drop 0/0`, zero
console bytes and 7.067 GB moved. **`D1`, `D2`, `D3`, `D5` and `D6` are met;
`D4` is met in part with its gap named and priced.** `R6-6` is a stretch whose
DoD is unreachable on this hardware for two independent measured reasons, and
what stands in its place is a weaker statement that is true.

**The weakest thing here is not a reading either.** `D5`'s number was taken
with a `/proc` verb armed by hand that is **0** at boot (`NET-107`), and the
gate closes without the one-line change that would fix that having been built
— so the headline figure is reproducible only by someone who knows to type
`recover 1`.

### Three claims that stand

**① `D1` — the precondition this gate opened with UNANSWERED is answered, by a
real bus master, and the answer is the inconvenient one: this D-cache is NOT
coherent.** 量 seating 26, block 25, protocol and decision rule frozen in
`e85fd0c` *before* the run. Cached read `V0` → the host sends eight 1,472-byte
broadcast UDP frames, which the MAC DMAs into mbufs with the CPU storing not
one byte → cached read `V1` → uncached read `V2` last, because of `CPU-70`.
**Two of four buffers, in each of two independent runs: `V1 == V0` and
`V2 ≠ V0`** — the cache returned a stale value after a real engine had
overwritten the DRAM under it. 🟢 **And it is sealed**: `V2 ≠ V0` proves the
DMA landed, a miss would have fetched `V2`, so the line was necessarily
resident — which closes the *evicted* escape that five previous attempts could
not. 🟢 **The payload value was computed before the frames were sent** (buffer
offset 1398, 14+20+8 header, payload index 1356, `1356 mod 256 = 0x4C` →
`4C4D4E4F 50515253 54555657 58595A5B`) and **four of four buffers hit**, which
also establishes that this switch inserts no CPU tag ahead of the frame. 🔴
The other two buffers returned *cannot distinguish*, and that is the control
working: one cache cannot snoop two buffers and not the other two. **The
consequence for the driver is a requirement rather than a precaution** — rings
*and* payload buffers in the uncached window, recorded at
`rtl819x-nic.c:92-113`. `SPEC.md` `CPU-45`; `docs/rlx-cache-and-cp0.md` § ②.

**② `D3` — the ladder refuted its own first rung, and the refutation carries a
positive control taken on the same boot.** 量 seating 28. Rung 0 was
`SWINTSET`: with the engine on and the mask open the software interrupt
**still does not raise one**, and the control that makes that a reading rather
than a dead cell fired in the same power cycle. The four rungs above it were
then walked without skipping, each with an observable before the next was
attempted — loopback byte-for-byte, a TX frame captured by the workstation, an
RX frame decoded into a real ARP, and NAPI's mask → drain → restore →
**interrupt recovery**. `/proc/interrupts`' three-state control (no line 12
before, `12: … RLX LOPI` during, no line 12 after `free_irq`) closes both ends.
`SPEC.md` `NET-48`–`NET-50`; `notes/nic-driver.md` § 4.

**③ `D5` and `D6` — two numbers, and each is published with the thing that
weakens it rather than beside it.** `D6`, seating 32, image `s31L`
(`CONFIG_PRINTK=y`, deliberately, so an oops would print): `ping -f -w 1800 -l
32 -s 1400` for **1,899.593 s = 31.66 min**, `nd_stats … drop 0/0`,
`n_tx_stop 0`, four `txd` OWN bits clear, **console 0 bytes**, one
uninterrupted read-only capture — 7,066,765,224 bytes both ways = **7.067 GB,
29.761 Mbit/s aggregate**. 🔴 Its own gap is in the entry: the capture ran
1,860.084 s against a 1,899.593 s flood, so **coverage is 97.9 %** and an oops
in the last 39.5 s would not have been recorded. `D5`, seating 37: **17.03 /
17.76 / 17.09 Mbit/s**, spread 0.73 = **4.2 %**, against five `phfollow 0`
control-arm runs at **0.04–0.07 Mbit/s** — and the arm-0 figure is *generous*,
because 量 `nd_stats rx` the board received 19–40 % of what the host says it
sent, so from the board's own counters that arm is 0.020–0.067. 🔴 **n = 4 and
the fourth collapsed**, and `notes/nic-driver.md:2038` carries the rule that
the three-run figure may not be quoted without it. 🟢 The pre-registered
refutation condition held: `n_ph_used` read **44,256** in the arm-1 runs and
**0** in every arm-0 run, so the switch took and the two arms were not the same
experiment. `SPEC.md` `NET-76`, `NET-102`.

### The plan's own three acceptance rows, read one at a time

`R6`'s `PROGRESS.md` DoD is a decomposition *of* the plan's row, not a
replacement for it, so the plan's own wording is read here too.

| the plan says | verdict |
|---|---|
| **通過** `ping` 通 | 🟢 met, seating 28, both directions 4 of 4, with a **positive** discriminator — a locally administered MAC no Realtek OUI can hold. `SPEC.md` `NET-51`–`NET-54` |
| **通過** `iperf3` 有一個數字 | 🟢 met, seating 37: **17.03 / 17.76 / 17.09 Mbit/s**, and the figure carries n = 4 with one collapse rather than the three that cluster. `NET-102` |
| **通過** 30 分鐘 flood 不掉封包不 oops | 🟢 met, seating 32: **1,899.593 s = 31.66 min**, `drop 0/0` by the driver's counters, **0 console bytes** on a `CONFIG_PRINTK=y` image. `NET-76`. ⚠️ **Two qualifications that travel with it**: the flood was `ping -f`, not `iperf3`; and the capture ran 1,860.084 s of 1,899.593, so **coverage is 97.9 %** and an oops in the last 39.5 s would not have been recorded |
| **否證 ①** descriptor 欄位在 big-endian 上搞錯 → 送得出去收不回來 | 🟢 **did not fire.** Rung 3 decoded a real ARP out of the RX path on seating 28, and `NET-85` later carried **203 MBytes** in one transfer |
| **否證 ②** 快取一致性沒處理 → 間歇性、與負載相關的資料毀損 | 🔴🔴 **The symptom FIRED and the named cause was innocent, and that distinction is the most expensive thing this gate learnt.** The precondition *was* handled before a ring was allocated: `CPU-45` was answered on silicon — this D-cache is **not** coherent — and the driver put rings *and* payload buffers in the uncached window, recorded at `rtl819x-nic.c:92-113` as a measured requirement. **And intermittent, load-dependent data corruption happened anyway**: `NET-61`, a burst desynchronises the engine's two RX position registers and the driver then delivers frames carrying another frame's length. It cost four seatings. 🟢 The cause was the driver using **one index for two rings** (`NET-82`, read out of the vendor's source), and the fix measured **250×** — 0.06 → 17 Mbit/s (`NET-102`) |
| **中間檢查點** loopback → 單向 TX → RX → NAPI，不要跳 | 🟢 walked, none skipped, each rung with an observable before the next was attempted (seating 28). 🟢 **And a rung BELOW the plan's first was added and then refuted**: `SWINTSET` does not raise a software interrupt on this part with the engine on and the mask open, with the positive control taken in the same power cycle. `NET-48`–`NET-50` |

⚠️ **否證 ② is the row to re-read before `R7`.** A refutation condition names a
cause and a symptom; this one's symptom is a good detector and its cause was a
red herring, so *the cache was handled* did not make the class go away. **What
made it go away was reading the vendor's driver**, which is `D3`'s own
refutation condition (*a field-by-field comparison, written down, and not a
retry*) being executed four seatings late.

### The three questions the plan attaches to this gate

讀 `plan/router-rebuild-plan.md:1946`. `PROGRESS.md` says in its own words that
a gate which produces a working driver and cannot answer them *has produced a
working driver and nothing else*. 🔴 **量 2026-09-23, and the owner's question
is what found it: this entry answered none of the three when it was first
written, and `dma_alloc_coherent` appears ZERO times anywhere in this
repository.**

**① `dma_alloc_coherent` 跟 `dma_map_single` 差在哪？** The first *allocates* a
buffer and hands back a mapping that stays coherent with the device for the
buffer's lifetime — on a machine whose cache is not coherent, that means an
**uncached** mapping, paid once. It is for memory both sides touch
continuously: descriptor rings. The second takes a buffer that already exists
and makes it visible to the device **for one transfer**, with explicit
ownership hand-offs, and on a non-coherent machine those calls are cache
maintenance — writeback before the device reads, invalidate before the CPU
does. It is for streaming data: packet payloads. 🔴 **On this board, and this
is measured rather than recited**: `CPU-45` says the D-cache is not coherent,
so the first API can only be uncached here — and **rlxfw calls neither.** It
takes one `kmalloc` and uses its KSEG1 alias for all three regions, which is
`dma_alloc_coherent`'s job done by hand, and declines the second entirely. The
vendor does the other thing: `UNCACHED_MALLOC` for rings and descriptors (six
call sites, 讀 `rtl865xc_swNic.c:1188-1242`) and leaves packet data **cached**
with `_dma_cache_wback_inv()` at the two hand-off points — `dma_map_single`'s
shape, written by hand. 🔴 **And the difference has a price this project
measured**: per 1,446-byte frame rlxfw issues ~1,446 uncached single-byte bus
transactions in each direction where the vendor issues one writeback over ~91
lines. `docs/nic-vendor-diff.md` § 4.

**② NAPI 為什麼要遮罩中斷？重開中斷的 race 在哪？** The interrupt is a
doorbell that says *there is work*; once the poll loop knows there is work, one
interrupt per frame is pure overhead, so NAPI masks it on entry and drains the
ring in a loop. **The race is at the re-enable, and it is an ordering
problem**: if the driver declares the ring empty and *then* unmasks, a frame
arriving between the last ring read and the unmask raises no interrupt (still
masked) and is seen by no poll (already finished) — the device goes silent with
work pending. The order that closes it is drain → `napi_complete()` → unmask →
**re-read the ring**, and re-schedule if it is not empty. 🟢 量 seating 28:
rung 4 walked mask → drain → restore → **interrupt recovery**, with an
observable at each step. 🔴 **And this driver's own complete path has a
consequence nobody planned**: 讀 `rtl819x-nic.c:1475-1478`, it ORs the run-out
bits back into `CPUIIMR` on *every* completion, which is why § 12.4's run-out
mask experiment **cannot be done through `/proc`** — the next completion
restores whatever was written, and a read-back gives a false green.

**③ `OWN` 位元的寫入順序錯了會怎樣，你怎麼測出來？** `OWN` is the handshake.
Every other field — buffer address, length, flags — must be visible to the
engine **before** ownership is handed over, or the engine can start on a
descriptor whose address field is still the previous one: it transmits from a
stale buffer, or receives into one. An uncached mapping is what makes the
ordering hold on this core, which is the same requirement `CPU-45` produced for
a different reason. 🔴 **And the honest half of the answer is negative: this
gate never ran a deliberate wrong-order experiment.** No cell ever set `OWN`
before the fields to see what happens. What it has instead is ① the four-rung
ladder, which fails at rung 1 if the order is wrong and was walked without
skipping, and ② the descriptor transition captured **at the loader prompt
before any driver of mine ran** (`notes/nic-driver.md` § 3.3), so the layout
was known rather than guessed. **So *how would you test it* is answered by a
ladder that would have caught it, not by an injection that proved it** — and
that is a weaker answer than ① and ②, said here rather than left to be found.

### What `R6` did not establish

🔴 **`D4` is met in part, and the remaining conjunct is a GATE, priced before
this entry was written.** The row asks for *"`ping` both directions with my
driver bound and the vendor's **not** loaded"*. The first half is met with a
positive discriminator — a locally administered MAC (`02:` plus ASCII `RLXFW`)
that no Realtek OUI can hold, chosen so this unit's real address in `H601`
never has to be read. The second half is not: the vendor's driver is in the
image, every hardware initialisation it performs runs, and its `re865x_open()`
refuses with `-ENODEV` while `/proc/net/dev` still lists `eth0`…`eth4`
(`NET-106`). 量 `readelf` over a fully built tree, `CONFIG_RTL_819X_SWCORE=n`
leaves **ten undefined symbols at the vmlinux link in four independent
places**; past the link the VLAN table is not a register write but a `TACI`
protocol inside the directory that would vanish; and the same switch deletes
`/proc/rtl865x/` — the vendor's whole instrument set, which is what
`NET-109 殘留`'s next step reads (`SPEC.md` `NET-109`). **So closing it is a
gate, and it removes the instruments two of this gate's own residuals need.**
~~It is the next gate's headline rather than this gate's overrun.~~ 🔴 **2026-09-23:
that half was a prediction about a decision that was not mine, and the owner
refuted it the next day by opening `P2`** — boot-time breakdown and
throughput across **both** firmwares, which wants the vendor image present
rather than the vendor tree deleted. **So `D4`'s remaining conjunct is not
the next gate's headline; it is unowned**, and it goes on the standing list
with the price this paragraph already measured. ⚠️ The lesson is narrow and
worth keeping: *an entry may record what a gate did not establish; it may not
assign the next gate's subject.* ⚠️ The precedent
is `P4b-gate`, which closed 2026-09-01 with `D2` unmet, the reason recorded and
two items left open *under* the gate; this is the second use of that shape and
the first where the unmet row is priced in symbols rather than argued.

🔴 **`R6-4`'s other two named deliverables.** The `ethtool` ops exist
(`get_drvinfo` / `get_link` / `get_ringparam`, driver 1.3) and are **inert**:
量 `config/image-commands.tsv` has no `ethtool` applet and the unit's own
`squashfs-root` has no binary, so they are verified in the artefact and have
never executed. The named next step is a small static MIPS `linkprobe`, the way
`/bin/iperf3` already reaches this board. **`phylib` is zero lines and
deliberately so**: 量 `SPEC.md` `NET-39`, the CPU port has no PHY — MDIO
`0x05`–`0x1F` all read `0x0000`, `PCRP6` is `nn7F0038` where `PCRP0`–`PCRP4`
are `nn7F0039` (bit 0 `EnablePHYIf` clear), and `PSRP`'s `PortEEEStatus` is
set on 0–4 and clear on 5/6/7/8 — so hanging a
`phy_device` on `rlx0` is architecturally wrong, and the right shape is an
`mii_bus` serving ports 0–4. The owner ruled *record and defer*.

🔴 **`NET-67 殘留` — why the engine stops retiring a TX descriptor.** **Eight
candidates are dead and none has been replaced**, the last of them by a
single-variable A/B on one boot: three zeroed TX ring bases against
`tpdcr1/2/3` all reading `idle_ring` gave first-miss at **1.138 s** and
**1.124 s**, 1.2 % apart (`NET-108`). The gate ends with a repair that works
(`NET-101`) and no mechanism.

🔴 **`NET-109 殘留` — and its next step is blocked by an absence this gate
created.** The CPU port's ingress reads `Rcv 0 bytes` while `CRCAlignErr`
grows +7 for +7 transmitted frames; the obvious reading was refuted in the
same seating by the host's own `RX errors: crc`, 0 before and 0 after. ⚠️
**Every `asicCounter` reading this gate took was after the fault**, so *the
fault caused this* and *it has always read this way* are not separated, and a
healthy baseline costs no power.

🔴 **`R6-6` is not met and two of its three clauses are unreachable for
measured reasons, not for want of a segment.** *Two ports cannot ping each
other* needs two hosts on two jacks at one moment; 量 thirteen reads, exactly
one port carries `LinkUp` each time, and moving the cable tests two ports at
two *times*. *Restoring one VLAN **table*** is unreachable independently:
讀 `rtl819x-switch.c:93-97`, the table is reached through the `TACI` block,
which is a protocol and not a register write — what rlxfw can restore is the
**PVID register**. 🟢 **What stands instead**, and it is the statement the
frozen card wrote before the readings: *on this part the per-port PVID field at
`0xBB804A08 + (port*2 & ~3)` selects whether that physical port's ingress
traffic reaches the CPU port, measured by ping in both directions with the port
identity read from `PSRP` on both sides of every cable move; and writing the
original word back restores it.* The readable half has now been read on four
seatings (33, 34, 35, 38) and is **byte-identical every time**.

🔴 **`D5`'s headline number needs a verb typed, and the gate closes without the
initialiser that would fix it.** `recov_mode` reads **0** at boot; seating 37's
17 Mbit/s was taken with `recover 1` armed by hand. Seating 38 measured what
that costs on the image's own defaults: **0.39 Mbit/s for 10.66 s and then
zero** (`NET-107`). ⚠️ This is the *second* verb dependency this project has
shipped — `phfollow` was made the compiled default in the same image that
exposed `recover` — and the one-line change is carried forward rather than
done, because it needs an image and this segment had no bench half.

🔴 **The comparison `D5` was published with is between two different
directions.** 量 2026-09-22 from the captures: `NET-84` (vendor, 25.4 Mbit/s)
and `NET-85` (rlxfw, 23.3) are both the board **sending**; `D5`'s runs are the
board **receiving**. `notes/nic-driver.md` § 16.3's *"68 % of the vendor"* is
therefore a ratio across directions, and **this project holds no vendor receive
figure at all**. The direction-matched ratio is **0.87–0.92×** and lives in
`docs/nic-vendor-diff.md` § 11.1. The comparison is withdrawn rather than
recomputed; § 16.3c says what it would cost to get the missing number (three
commands, zero power).

🔴 **`MT-PORT` still does not say which driver served the link, and `P1` handed exactly that to `R6-0`.** `P1`'s design table declared *"link up on the connected port, **and the output names the vendor driver**"*; 量 2026-09-22, `config/mfgtest.sh:536` prints `chk MT-PORT 1 "$MFG_PORT LinkUp"`, which names the **port**. `R6-0` quoted the residual and banked the half that was a missing measurement — `SPEC.md` `NET-31`, the Linux-side link state on a named port — and left the half that was a missing label. 🔴 **And `R6` made it matter**: there are two drivers on this board now, and `config/mfgtest.sh:57` reads the **vendor's** `/proc/rtl865x/port_status`, which reports the switch port's link state whatever `net_device` is bound. **The label is not obtainable from the source `mt_port` reads**, so the fix is a different source rather than a different line. This is what the operating clause fires on at twelve entries.

⚠️ **The power ledger is not one number and this entry does not make one.**
The log's own segment headings for these thirteen seatings use **four different
words** — 電源循環, 電源事件, 電源按鍵, 冷開機 — and nothing in this repository
defines them against each other. Counting them gives **23 by a regular expression and 24 by reading
them** — the eighty-seventh segment's heading writes its extra press as
prose (*一次電源循環，加一次因我的失誤而多花的電源按鍵*) rather than as
a count, so a scan misses it. **That is the same defect one layer
down**: the four words are not defined against each other, and they are
not written in one shape either. Neither number is a measured total.

⚠️ **Zero flash-write commands and zero `FLR` over the whole gate.** The
bracket stands where `R5` left it, at 1,024 of 4,194,304 bytes = **0.0244 %**,
and `FLS-26`'s ledger did not move: proven identical 4,177,920 B (99.61 %),
proven different 8,192 B, undetermined 8,192 B — which is exactly `H601`.

---

## 2026-09-25 — `P2` (both firmwares' boot time through one script, and the same numbers on a second calendar day)

### One line

**v0.4+, ten segments (102nd–111th) against the plan's eight, two seatings (39
and 40) of twelve presses each.** `tools/boot-timeline.py` splits both
firmwares' boots into segments with one function that reads a landmark table per
firmware, on one host clock. The segment both firmwares run as the same code —
the loader's `Booting` → banner — measured the same in both columns inside each
seating, and on a second calendar day **134 of the 140 numbers the frozen
contract called stable reproduced within ±10 % on both of its columns; none of
the six that did not is a row of the segmented table or `D7`'s Δ.** The table,
and the feature table beside it, are `docs/boot-time-table.md`. **`D1`–`D4` and
`D6`–`D8` are met. `D5` is met for ICMP and for the vendor's driver; for
rlxfw's own driver its reading is a failure** (`NET-116`), which `R6b` now owns.
The plan's interrupt latency by logic analyser (`P2-6`) never ran and is carried
to `P3` as `LA-1`.

**The weakest thing here is a column with one boot in it.** The loud image boots
cold once per seating (`P1L-r01`), so 11 of the 69 load-bearing stable rows are
one boot against one boot. The largest deviation among all 69, loud cold
`rlxfw.setup` at +6.712 % against seating A's raw value and +5.229 % against
its corrected one, is one of the 11, and its seating-B value carries a console
stamp that arrived provably 13.5 ms late (`CLK-44`). Behind it sits the
contract's own criterion: stability is the spread of seating A's readings, and a
single reading has a spread of 0. **So 24 of the 140 stable numbers rest on one
seating-A value, and three of the six misses are among them.**

### Three claims that stand

**① `D2` held on both days, and what moved every segment of seating A by one
factor was the host's clock, not the board.** 量 seating 40, every capture
stamped on `CLOCK_MONOTONIC_RAW`, which the host does not slew. The loader's
`Booting` → banner in rlxfw's warm boots and the vendor's differ by
**+0.8245 ms**, the cold boots by −0.167 ms, and the four listen-mode
differences run −4.624…+1.178 ms, against the bands card A wrote before seating
A (±10 ms, ±25 ms cold). All six were computed on the bench night by the card's
own `Z9-D2X` and reproduce at the desk to 4 dp. 🟢 **On `RAW` the control is
tighter than seating A could make it**: the 13 warm loader catches span
1.363 ms, 0.383 % of their median, against 3.08 % in seating A on its slewed
clock and 0.545 % after correction. 🟢 **And inference (iii) holds as
registered**: the warm `loader.booting` median on `RAW` is 0.356060 s (n 13),
inside [0.354469, 0.358031], the ±0.5 % of 0.35625 s that seating A's record
wrote down before this seating. So between seatings A and B, `CLK-32`'s factor
was the host's clock (`CLK-43`); for earlier directories it stays 推. 🔴 One
control read was late, and it is named: `M1-BOOT`'s two differences sit
3.7–4.0 ms from seating A's corrected values, the read that carried its anchor
byte came 5.39 ms after its predecessor, against 0.54–1.10 ms in the other 24
loader boots, and measured from the loader's last `.` instead they are −0.05
and −0.19 ms (推 one late read). ⚠️ What this does not reach: `RAW` against
true time, which nothing in seating B logged.
`SPEC.md` `CLK-45`, `CLK-43`; `notes/boot-time.md` §§ 8.4–8.5.

**② `D3` — the segmented table reproduced on a second calendar day, scored
three times against a contract committed before seating B's intervals were
computed.** 讀: the closing rule (`e2f15ff`, 05:19:39) and the list of 294
numbers with their classes (`76deef8`, 06:31:39; `docs/boot-time-d3-list.tsv`)
were both committed before any seating-B interval was computed at the desk; the
only seating-B values read before them are the ones `LOG.md` 第一百一十段
quotes. 量: **140 stable, 134 hits, 6 misses, 0 on a load-bearing row.** On the
other 68 load-bearing rows, column (a) — seating B against seating A's raw
values — reads +1.1…+3.6 %, which is the size of seating A's slow host clock,
and column (b) — against the corrected values — stays within ±1.1 %. 🟢 Two
scorers put all 294 rows in the same category and agree on (a), (b) and (c) to
1e-9. A third, the judge's, in exact fractions, agrees on every verdict; a
planted load-bearing miss turns its verdict to *stays open*, and +10 % exactly
scores a hit while 1e-9 past it scores a miss. ⚠️ **Their agreement tests the
scoring, not the seating-B values, which all three took from the same
pipelines.** Those have second sources of their own, one per family, each
sharing no code with its primary: 208 of 208 segment records, for one, and 71 of
72 common `D8` rows, where the one disagreement is a read 1.58 ms late on the
primary's side that moves no verdict. `SPEC.md` `CLK-48`;
`docs/boot-time-d3-score.tsv`; `notes/boot-time.md` § 8.9.

**③ `D7` — the instrument resolves the difference it is asked to compare, and
the bytes that make the difference were counted before either image booted.**
量 press 1 of seating 40: the loud image's kernel entry → init exceeds the quiet
one's by **Δ = 1.710352 s** (medians of 3 and 4 boots), inside the band
[1.398905, 1.979101] that its extra console bytes predict at the measured
factor. The extra bytes are **5,831 in 12 of 12 loud–quiet pairs**, 810 of them
between `RLXFW-B00` and `RLXFW-B09` and 5,021 between `RLXFW-B09` and
`RLXFW-B10`, and every other landmark pair differs by 0. The rate Δ implies,
3,431.8 B/s, is **89.370 %** of 38400-8N1's 3,840 B/s, inside `FW-70`'s
88.4–92.7 %. It reproduces seating A to +1.29 % raw and −0.12 % corrected.
⚠️ Which factor belongs in that rate is not established; at a factor of 1 it is
88.782 %, also inside. `SPEC.md` `CLK-46`; `notes/boot-time.md` § 8.6.

### The plan's own acceptance rows, and `P2`'s DoD, read one at a time

`P2`'s DoD is a decomposition of the plan's two rows, not a replacement for
them, so both are read.

| the plan says / the DoD says | verdict |
|---|---|
| **通過** 一張表，**分段**，每個數字有量測方法與重複次數，且**功能對照表在旁邊** | 🟢 met: `docs/boot-time-table.md` — cold and warm tables, each cell with n, median and range for seating A raw, seating A corrected and seating B, its class and its `D3` verdict; the feature table beside it, two sources per firmware; a method section naming the instruments, the one clock and the `D3` contract. ⚠️ The loud image's cold column is one boot per day |
| **否證 ①** 任何一個數字無法在另一天重現到 ±10% 以內 → 量測方法有問題 | 🔴 **fired, on six of the 140 stable numbers, and on none of the table's rows.** By the plan's letter the method is broken for those six; `D3`'s own refutation condition says the same and publishes each with its miss. Three are defects of the contract rather than of a measurement: `D8`'s quiet cold network-up width, whose single seating-A reading has raw and corrected values 2.04× apart, so column (a) could not hit; and `NET-109`'s two counts, which on both days are the probe's echo replies plus 2 — a run length, not a device quantity. Three are rlxfw's ICMP round trip at 256 and 1472 B (+12.16…+18.05 %) on a day the vendor's average rtt was 11.8–25.8 % lower; split by whether the host was capturing they move +7.2 % and +9.9 % without and +13.5 % and +19.7 % with, and the pair captured on both days still moves +18.1 % and +12.3 %, so the host's capture is 推 part of the shift and not all of it (`NET-121`). One carried-forward row, `D3-MISS`, names the experiment for each |
| **否證 ②** `ROM → ESC 視窗` 那一段在兩欄之間不同 → 量測方法有問題 | 🟢 **did not fire, on either day** (`CLK-34`, `CLK-45`; claim ①) |
| **`D1`** one script for both firmwares; every comparable segment computed by the same code | 🟢 met at `P2-1` (`FW-117`). 量 seating 40: a second parser sharing no code with the tool agrees on 52 of 52 loader records, 208 of 208 segment records and 223 of 223 landmarks, and the desk's re-run equals the bench night's `Z9-D2.tsv` byte for byte |
| **`D2`** the identical-code control, inside one seating | 🟢 met on both days (claim ①) |
| **`D3`** every number on a second calendar day within ±10 %; cold and warm apart; misses published | 🟢 met under its closing rule (claim ②): six misses published and carried; column (c), each cell over its own seating's warm `loader.booting`, published beside the raw figures and deciding nothing. Of the contract's 29 exact rows 27 hit. The two that missed are one capture's size and digest, `P2-M0`, which the capture tool stopped 4 B short, before the map's last line terminator (`FW-136`); its 34 section lines are the other five maps' byte for byte, less that terminator |
| **`D4`** identical / comparable / not comparable; each daemon's start and readiness; the feature table from two sources each | 🟢 met, and its refutation did not fire: every open port and every announced daemon (量 census and console) traces to `rcS` or `sysconf` (讀), and the scripted daemons never seen are gated (telnet: port 23 closed) or UDP. Readiness has first readings for 52881 (J+17.08–17.42 s) and 52869 (J+31.27–32.50 s). 量 52881 answers 4.79–5.96 s before the `MiniIGD` line in 9 of 9 boots and fits one offset from the `WiFi Simple Config` line; 讀 the SDK drop names 52881 `RTK_WPS_LISTEN_PORT`; so, 推, it is `wscd`'s port and not `miniigd`'s (`NET-118`; `NET-115` corrected in place). Inference (ii) is not refuted in 9 of 9, and the 18 windows of both days intersect in 6.5 ms. The method states `GREP-1`'s enumeration rule (`FW-141`) |
| **`D5`** throughput: ICMP, both firmwares; `iperf3` on both drivers, n ≥ 3; CPU from `/proc/stat`, no typed verb; ⊘ `iperf3` on the vendor firmware | ⚠️ **met for ICMP and for the vendor's driver. For rlxfw's driver the trials ran, and the figure mostly did not.** 量 seating 40: 600 of 600 echoes, 0 % loss in all 30 series. `eth4` completed 12 of 12 trials on both days, and every rate and CPU median is within ±10 % of seating A — TCP board-receive 24.572 / 24.653 / 23.923 Mbit/s from the board's own server log. No verb was typed: `P1-N0` read `recov_mode 1`, `ph_follow 1` as compiled. `rlx0` completed 0 of 12 exchanges (seating A: 3 of 12), and its one TCP board-receive figure is `TR1`'s 16.953 Mbit/s from the board's log, n = 1 (`NET-116`) |
| **`D6`** kernel and rootfs sizes for both (讀); rlxfw memory free after boot (量); ⊘ vendor runtime memory | 🟢 met: 量 `MemFree` 20,924 kB of 26,984 (seating A 20,932; `MEM-20`). 讀 sizes: the compressed images the loader receives, 1,155,072 B quiet and 1,181,696 B loud, each carrying its initramfs, against the vendor's LZMA kernel of 987,138 B and its SquashFS of 1,876,033 B |
| **`D7`** loud − quiet kernel entry → init = extra console bytes ÷ the sustained rate | 🟢 met on both days (claim ③) |
| **`D8`** network up = the first ICMP echo reply, on the console's clock, with the channel offset measured | 🟢 met, with its own refutation fired on both days as predicted: the channel offset spans 701.0 / 896.4 µs (seating A, read / kernel stamps) and 492.6 / 450.8 µs (seating B), beyond one byte time, 260.4 µs, so network up is a console-side bound. 量 seating 40: quiet rlxfw answered the host's second broadcast of a cycle in 8 of 8 boots (6 by frames, 2 by the probe's ledger), `N-NDOPEN` the lower edge each time; **the loud image has its first reading**, on the third broadcast in 3 of 3 by frames, J+13.230903–13.281312 s; the vendor answered a cycle's first broadcast in 9 of 9 by the probe's ledger, no capture having run on a vendor press (seating A: 4 of 9). Inference (i) is not refuted in 9 of 9, and it is a weak test: its brackets are 1.03–1.10 s wide (`CLK-47`) |

### The three questions this gate must be able to answer

讀 `PROGRESS.md`, `P2`'s step list: the plan's § 11 has no `P2` row, so the
questions are derived there.

**① 「你開機比較快，是不是只因為你少跑了東西？」** The table puts the whole
difference in the vendor's userspace, which starts what rlxfw does not run; it
does not show how that time divides among the daemons, or whether it is spent
running rather than waiting. 量 seating 40: **rlxfw's kernel is the slower
one** — kernel entry → init 9.445702 s (quiet, n 8) against the vendor's
7.098017 s (n 9) — and about 3.0 s of rlxfw's is its own timer driver waiting
on purpose (讀 `CLK-27`, `IRQ-13`). rlxfw reaches its prompt at J+10.792753 s
(n 8) and the vendor reaches `boa` at J+26.836990 s (n 9) because the
vendor's userspace then runs for 18.66–18.68 s (warm and cold medians) against
rlxfw's 0.116 s, starting what the feature table lists and rlxfw does not run:
a web server, UPnP, WPS, the WLAN applications, a bridge, NTP and IPv6, each
announced on the console in 9 of 9 boots. ⚠️ What the table does not give is
each vendor daemon's own start cost as an interval: for the three TCP daemons
it has readiness from `J`, and for the rest only the time of a console line.

**② 「換一天量，還是這個數字嗎？」** For the table, yes (claim ②): 134 of 140 stable
numbers, and none of the six misses is a table row. The six are printed with
both columns in `docs/boot-time-table.md` and carried as `D3-MISS`.

**③ 「你的儀器分得出你在比的差嗎？」** For what `P2` compares, yes: `D7`'s
1.710352 s is resolved from bytes counted before the boots (claim ③), and the
identical-code control spans 1.363 ms over 13 boots. 🔴 **For one stamp, no
better than about 14 ms.** 量: a console stamp can arrive provably 13.5 ms late
(`P1L-r01`'s `RLXFW-B09`), which the capture floor seating 17 measured, 0.517
and 0.868 ms, does not bound. The `---Jump` line the board prints on receiving
the typed `J` reaches the host 0.8–6.6 ms (seating B) and 1.0–6.3 ms (seating
A) *before* `console-capture` records the send, and its own stamp is at least
0.9–6.8 ms late, so every `J`-anchored interval reads short by that less its
far end's own lateness, in every boot of both seatings (`CLK-44`). That is
systematic on both days, so no `D3` verdict moves, and the contract already
declines to score a number under 20 ms, where two read quanta alone move it by
10 % — a line that itself assumes quanta of about 1 ms, which one late read
(13.5 ms here) exceeds.

### What `P2` did not establish

🔴 **`P2-6` — the plan's interrupt latency, measured with a logic analyser —
never ran.** The analyser the plan lists as on hand was never connected. By the
stop-loss written with this gate, *中斷延遲* is recorded as not done and is not
substituted by the on-die counter under the plan's name. It is carried forward
as `LA-1`, owned by `P3`, the bring-up report, which is where a latency figure
would be read.

🔴 **Six numbers did not reproduce, and three of them say more about the
contract than about the board.** One carried-forward row, `D3-MISS`:
* `D8|width|quiet|cold` — one seating-A boot, 0.187804 s raw and 0.091986 s
  corrected, against seating B's 0.1045985 s (n 2): (a) −44.30 %, (b) +13.71 %.
  Column (a) could not hit by construction. The experiment: a third calendar
  day on `RAW`, which compares seating B with a seating C on one clock.
* `D5a|rlxfw|256|avg`, `D5a|rlxfw|1472|avg`, `D5a|rlxfw|1472|mdev` — +18.05 %,
  +12.16 %, +16.60 % in both columns. ⚠️ The host's capture explains part of it
  and not all: 量 the third press's pair, run under capture on both days, still
  moves +18.1 % and +12.3 % at the capture tap. The experiment: the same ICMP
  series with and without the host capture inside one boot. It is `R6b`'s,
  whose regression re-measures ICMP.
* `NET109|crcalignerr`, `NET109|p3egress` — 294 → 414, +40.8 %. 量 on both
  days the count is the probe's echo replies inside the last boot plus 2, a
  measure of how long the host's schedule ran; the property the rows stand for
  held, `CRCAlignErr` equal to port 3's egress, 414 = 414. No experiment: the
  rows are redefined as that per-echo identity.

🔴 **rlxfw's own driver has no throughput figure at the n the DoD asks for, and
why is `R6b`'s.** Over the two days `rlx0` completed 3 of 24 end-of-test
exchanges (seating B: 5 connected and failed the exchange, 6 `No route to
host`, 1 hung), and its only TCP board-receive figure is n = 1. 量 seating 40:
at least 128 frames the driver counted as sent never left port 3 (seating A:
182; `NET-112`); UDP board-receive lost 86.6–87.8 % *above* the
driver, whose `n_rx` exceeded what the host sent (`NET-117`); and block 45 —
`R6b`'s first bench block, the same night — placed the transmit loss in frames
of lengths the engine was not given: 1,043 of 1,193 echo replies lost, 678
`JabberErr` at the switch's CPU port (`NET-119`). The mechanisms are eight
candidates, all 推 (`notes/nic-driver.md` § 21). ⚠️ Seating A's exact 0 on the
receive side — every frame into port 3 reached the driver — did not reproduce:
+2 frames and 134 B, with IRQ 12 rising 6 after the last dump, so this method
cannot give an exact 0 (`notes/nic-driver.md` § 19.2, corrected in place).

🔴 **The board lost about 105 jiffies again, in the same stretch as seating A,
and the counter that lost them is not the one `notes/boot-time.md` § 7.2
named.** 量: between `P1-N0` and `P1-TR1-S0`, 105.2 ticks by seating A's
recipe (seating A: 105) and 104.2–109.4 by placement (`notes/boot-time.md`
§ 8.3), and none in any trial. Over
`P1-TK0` → `P1-TR1-S0` the `cpu` line advanced 24,311 ticks and IRQ 25 exactly
24,311, while IRQ 13 advanced 24,376: jiffies are rlxfw's TC1 on IRQ 25, and
TC0 on IRQ 13 lost about 45, the same split as seating A. 推 the cell is the
switch's `asicCounter` read, which in block 45 cost 112–114 jiffies every time,
while the one driver-dump interval without it lost none.
What the read does to the timers is open: the obvious mechanism, interrupts off
for the whole print, cannot explain IRQ 13 counting 65 ticks that jiffies did
not (`CLK-42`).

⚠️ **Where inside its bracket either firmware's network came up.** Network up is
a console-side bound on both days. The vendor's brackets are 1.03–1.10 s wide
and rest on a reconstruction from the probe's own ledger that no frame checks,
since no capture ran on a vendor press, and 量 seating B's frames show that
reconstruction's retransmit range too narrow: the host's first-to-second
broadcast reached 1.033472 s against the 1.028 s it allows. That the vendor
answered at the first broadcast in 9 of 9 against seating A's 4 of 9 is 推 the
host clock, untested.

⚠️ **The vendor's UDP services, and whether any daemon serves.** The port census
is TCP only, so DHCP, the DNS relay and NTP are neither confirmed nor refuted by
a port, and readiness here is a TCP connect accepted, not a request served.
Which daemon owns 52869 and 52881 rests on timing and on a related SDK drop, not
on TOTOLINK's binaries.

⚠️ **The host's clock is measured, not calibrated.** Seating B logged its tick
and frequency every second (`CLK-41`) but no reference for `RAW`, whose WSL
boot is gone; and 量 after the loss the board's timer ran 100.002869 ticks per
`RAW` second against the card's 99.998–100.000. Whether `RAW` or the board is
the one off is not decided (`CLK-42`).

⚠️ **Byte-exact predictions over `--until` captures were predictions about the
instrument's tail as much as about the device.** 讀 and 量 on a pty,
`console-capture` stops 0–50 ms after a match, or about 150 ms after one that
ends `--esc-after` (`FW-135`). 量: of the 51 final-loop `--until` captures of
seating B and block 45, five ended short of their siblings' bytes — 2 of seating
B's 39 and 3 of block 45's 12 — and of the 22 captures behind byte-exact
predictions that held, 13 needed a read that came after the match (`FW-136`).
`boot-timeline --probe` reads network up only inside a capture's window, which
misses 7 of seating B's 11 rlxfw rounds (`FW-137`).

⚠️ **Flash.** No `--send` in card B carries `FLR`, `FLW`, `EW` or `EB` (讀, its
two `cardnum` rows read 0), and every upload was `looprun`'s, each after its
`S5b` read of the `AUTOBURN` word returned `00000000` (量, 11 of 11). The three
maps bracketing the nine vendor boots compare **31 groups the same and 1
`DIFFER`, the expected group 0**, over 4,186,112 B with `H601` not hashed
(`FLS-31`). They cannot see two writes that cancel, `H601`, or any byte outside
the 4,186,112. The `FLR` bracket stays at 1,024 of 4,194,304 bytes =
**0.0244 %**, and `FLS-26`'s ledger does not move.

⊘ **Structural, not deferred:** the vendor firmware has no shell, so its
`iperf3`, its `/proc`, its runtime memory and its per-daemon CPU time are not
measurable (`P2`'s settled item 1).

---

## 2026-09-28 — `R6b` (`rlx0`'s transmit fault located at its descriptor lengths and fixed as the default, and `rlx0` pinging with no vendor Ethernet code in the image)

### One line

**v0.4+, seven segments (110th–116th; the 110th and 111th are `P2`'s as well), no plan estimate to
divide by, and nineteen power-ons: seatings 40 (its second block) to 43, then twelve the record does
not number.** `rlx0`'s transmit loss is a descriptor-length fault, and one variable shows it: with
the vendor's convention — `m_len` = `m_extsize` = `ph_len`, as the loader and both vendor paths write
them — E2's eleven lengths answered 220 of 220 on two boots on which 1.4's convention answered 145 of
1,327 and 144 of 1,189, and a sweep over every frame length from 60 to 1,514 moved `JabberErr` by 0.
The end-of-test exchanges that `P2` could not finish now complete 12 of 12 on two boots; 31 minutes of
traffic at the fix fired no recovery while 1.4 fired 12 in two minutes on the same boot; and since
`rtl819x-nic` 1.6 the fix is the driver's default, so no verb is typed. On an image with no vendor
Ethernet code in it, the standard `/init` brings the switch up with one write class and `rlx0` pings
both ways, after a cold power-on and after `busybox reboot -f`. **All eight DoD rows are met; `D5`
carries one ⊘ that a ruling put there (`1472|mdev`).** Since 8g (`18c9068`) the mainline builds that
image's configuration.

**The weakest thing here is that `D8` passes on switch state rlxfw did not write.** `init` sets five
bits; the VLAN table, the PVIDs, the netif entry, `FFCR`'s two traps, EEE and `QNUMCR` are the
loader's. The registers among them read the same on 15 boots of the catch → upload → `J` path and
the tables on three, and none was read on a boot for which the loader did not bring its network up —
the way a product boots, from flash, and the path `R9`'s zero-write rule keeps out of reach. How a
frame addressed to `rlx0` reaches the CPU is 推 on one source: the loader's unknown-unicast trap
(`NET-169`). And the pass is one seating: one image, one cold and one warm boot, one host on port 3.

### Three claims that stand

**① `D2` with `D1` — one variable, on the same boots, separates the fault from the traffic, and the
stage is a span.** 量 blocks 47 and 48 (seating 42, `r6b2q`, driver 1.5, 2026-09-26): E2 at block
45's spacing ran the fix (`E-F1`), then 1.4's lengths (`E-L1`), then the fix again (`E-F2`), in cells
that differ only in the `txlen` word. The fix read 220 of 220 by the host's ICMP layer and on its
capture in both fix arms of both boots, with the CPU port's `JabberErr`, `FragErr`, `Drop` and
`etherStatsDropEvents`, its 512–1023 bucket and `n_recov_fire` Δ 0, no `0x8100` frame and no excess
byte; 1.4 answered 145 of 1,327 and 144 of 1,189 between them. The wire sweep at the fix, every
length 60–1,514 behind its own clean loopback map, read `JabberErr` 0 over 2,910 frames on each boot,
where 1.4, one length a sweep, jabbered on block 47 at exactly the 19 of 35 lengths its card had
predicted (`NET-128`, `NET-132`). 🟢 **The stage** (`D1`): 1.4 went wrong at the same seven lengths —
61, 62, 63, 263, 277, 1,511 and 1,512 — in the stack, the `tx`-verb and the loopback arms, one length a
bracket, and the fix at none; the descriptor words read back as 1.4 wrote them with the engine's
fetch held (`RB-01-C`, `RB-02-C` EQUAL), and the CPU port counted the damaged frames as jabbers — so
the change happens after the driver's fill in descriptor memory and at or before the CPU port's
receive MAC (推 from 量 parts, `NET-132`). 🟢 In loopback the field is `m_len`: raising it alone to
`ph_len` clears all 728 bad lengths, and changing `m_extsize` alone clears none (量, twelve
full-length maps, on each of which `M1`-cover8 matched 1,455 of 1,455 lengths; `NET-129`). ⚠️ What
this does not reach: which component inside the span changes the frame, what the engine fetched, or
why — `M1`-cover8 is a rule fitted after blocks 45 and 46 and names no cause; both `D2` boots are one
image, one seating and one day, with the fix typed as a verb. `SPEC.md` `NET-123`, `NET-128`,
`NET-129`, `NET-132`; `notes/nic-driver.md` §§ 22, 25, 27.

**② `D4` with `R6b-10` — the fix holds under load and over time, and it is the default: the third
verb dependency this project has shipped was retired inside the gate that shipped it.** 量 block 50
(2026-09-27, `r6b6q`): a 31-minute `ping -f` flood at the fix, every `ping` size 18–1,472 so every
frame length 60–1,514 each way, carried 2,363,511 frames with `n` = `c` = `o`, `JabberErr` 0 and
`n_recov_fire` Δ 0, and a TCP tail after it carried 797 MBytes with none; 1.4 on the same boot fired
12 recoveries in 120 s (`NET-141`). 讀 `rtl819x-nic` 1.6 starts every boot at `txlen vendor`
(`NET-154`); 量 one boot of `r6b10y` from the loader prompt, its page reading `txlen vendor` before any
cell and no policy verb typed, read E2's eleven 220 of 220 with the CPU port's counters Δ 0 and the
`tx` sweep 60–1,514 with `JabberErr` Δ 0 (`NET-158`). `R6`'s entry closed with `recover` needing a
typed verb and carried it to `P2-2`; here the fix was a typed setting wherever it ran before 1.6 —
blocks 47, 48, 50 and 51 and the night's `r6b8cr` — and it is the default on every image built since:
`r6b10y`, `r6b10n` and `r6b8i`. ⚠️ The default-setting run is one boot with no host capture and no
1.4 arm beside it — not a third `D2` boot — and `D4` is one boot and two kinds of traffic. The stall's
mechanism is not named: `M8`'s clause fired on block 46 (a recovery at 61 B with `j` = `f` = `d` =
0), so jabber is not what stalls the ring, and `NET-67` 殘留 is ⊘ with `M8`'s own reason — at `txlen
vendor` no stimulus has reached the stalling state (`notes/nic-driver.md` §§ 28.10, 30.4).

**③ `D8` — `rlx0` pings both ways with no vendor Ethernet code in the image, and the one write that
makes the difference is known to the bit.** 量 arm I (`bench/2026-09-28b/`, one power cycle, `r6b8i`:
`SWCORE=n`, `rtl819x-switch` 1.5, `rtl819x-view` 1.1, `rtl819x-nic` 1.6 at its default, the standard
`/init` typing `init`): after the owner's cold power-on and after `busybox reboot -f`, each of the
seven conditions written before power held — `RLXFW-ID0=3685A3A4`; `/init` reaching `lan up` with no
verb typed; `init … stored 1F on 1F`; host → board 4 of 4 at 46 B and at 84 B; board → host 4 of 4;
and the host's neighbour entry `REACHABLE` at rlxfw's locally administered address, the positive
discriminator `R6`'s `D4` used. `ethcensus` is GREEN on the image and RED on its control `r6b10y`, and
`/proc/rtl865x` is absent (`NET-167`). 🟢 After `init` the switch page differs from the loader's
state in five bits, `PCRP0`–`4` bit 0, and in nothing else; the VLAN and netif tables equal arm II's
word for word. Arm II — the same state with the five bits written by hand — is the control that
separates the NIC and the seam from the switch init: 0 of 4 either way before the write, 4 of 4 after
(`NET-164`). 🟢 `MT-PORT` read `Port3 LinkUp by rtl819x-switch 1.5; vendor tree absent` on both
boots: `D6`'s last clause, on the image it was written for. ⚠️ What is inherited, and on which boot
path, is the weakest-thing paragraph above; the address half of the discriminator has one reader,
by design (`armI-nb.py`: no capture holds the address). `notes/switch-driver.md` §§ 16.7, 17.6–17.10;
`SPEC.md` `NET-164`, `NET-167`–`NET-169`.

### The DoD, read one row at a time

`R6b` has no row in the plan, so its DoD is the only one read. `D8` is `R6`'s `D4` second conjunct,
which `R6`'s entry priced at ten undefined symbols in four places.

| the DoD says | verdict |
|---|---|
| **`D1`** the stage at which a transmitted frame's length or content changes, named by a single-variable experiment — the stack, the `tx` verb and loopback at each of E2's eleven lengths, each in its own bracket — or recorded undetermined with the arm that failed to separate it | 🟢 **met by its letter, after a first boot had recorded it undetermined.** Block 46 (seating 41) was a failed reproduction by the gate's own clause, so `D1` was recorded undetermined with arm A, the reproduction control, as the arm that failed (`NET-123`). Block 47 ran the `tx`-verb arm (`W-2`) and the loopback arm (`LB-1`, the full maps) one length a bracket; block 48 ran the stack arm (`SF`, `SL`), fix and 1.4 in cells that differ only in `txlen` (`NET-132`). The stage is a span, after the driver's fill and at or before the CPU port's receive MAC, 推 from 量 parts (claim ①). ⚠️ Block 47's two arms were assigned to `D1` after that press (the ruling on block 47; card B50's P8 wrote it down before block 48's power); no one boot holds all three arms at all eleven lengths at 1.4; the loopback arm's bracket is the driver's own dump pair, not the switch's counters; the stack path's own descriptors were read back at one length, 61 B, on block 47 only (`RB-02-C`). Earlier records (§ 25.7, `NET-129`) put the upper bound *before the CPU port's receive counters*, which also admits the stretch between that port's MAC and its counters; card B50's P8 wrote *at or before the receive MAC* before block 48's power, `D1` was met under it, and this entry uses it |
| **`D2`** on a fixed image, E2's eleven at block 45's spacing 220 of 220 by the host's ICMP layer and on its capture; the CPU port's four error counters, the 512–1023 bucket, tags, excess bytes and `n_recov_fire` all Δ 0; on two boots, each with 1.4 reproducing the loss; and a `tx` sweep 60–1,514 with `JabberErr` Δ 0 | 🟢 **met on two boots, blocks 47 and 48** (claim ①; `NET-128`, `NET-132`). Boot 1's positive control is `ping`'s count alone, 145 of 1,327: its CPU-port conjunct is void under card B49's P0, whose bracket read port 3 four frames above `c` − `j` − `f` − `d` (`NET-131`). ⚠️ "A fixed image" was `r6b2q` with the fix typed (`txlen vendor`): the image's default was 1.4's until 1.6. Beside it, at the isolated spacing of `M3`'s clause (≥ 200 ms a frame), the fix read 20 of 20 at each of the eleven with the CPU port clean (`NET-159`; one boot, `r6b8cr`, driver 1.5, `txlen vendor` typed) |
| **`D3`** `NET-111`'s end-of-test exchange completes in 12 of 12 `rlx0` trials on the fixed image, or the remaining failure is named | 🟢 **met on two boots: 12 of 12 in block 48 and 12 of 12 in block 50** (`NET-133`, `NET-140`). On block 50, TCP board-receive 16.9 Mbit/s and board-send 21.6–22.4 Mbit/s, the board's figures and the host's agreeing (`iperflog compare` AGREE at all six board-receive trials). ⚠️ UDP board-receive still loses 87–88 %, at the board's socket: `RcvbufErrors` Δ ≥ 0.9 of the loss, and the ~64 datagrams left at exit are a full queue of 63 (`NET-142`). The row asks for the exchange, not the rate, and why the socket refuses is ⊘ (`NET-117` 殘留). Block 50's pass is not the fix's alone: `rtl819x-switch` 1.2, the initramfs and the watch's ESC stream differ from block 48's |
| **`D4`** `NET-67` 殘留: no recovery over ≥ 30 min of traffic that includes every formerly bad length, on the fixed setting, while 1.4's setting stalls on the same boot; or the remaining stall named as a separate fault | 🟢 **met on one boot, block 50** (claim ②; `NET-141`). The first branch holds, so no separate stall is named. ⚠️ `M8`'s clause fired on block 46, so what stops descriptor retirement is not jabber, and it is not known; `NET-67` 殘留 and `NET-78` 殘留 are ⊘ with `M8`'s reason since 1.6 made the fix the default (`NET-158`), each reopened on any fire at `txlen vendor`. `NET-68` 殘留 was read on the same boot (12 fired, 12 recovered, 0 failed); `NET-76` 殘留 was not reproduced |
| **`D5`** every row of the population closed by a reading, re-owned, or ⊘ with a refutable reason; `D3-MISS`'s rtt part closed by `R6b-3`'s reading | ⚠️ **met with a named ⊘.** The population is 40 rows: `R6b-0`'s 35, the two § 19 residuals `P2` assigned, and `D3-MISS`, `WRAP-1` and `C-19`, re-owned at `P2`'s close. 11 are closed by a reading; 28 are ⊘, each with its reopening condition — two of them, `D3-MISS` and `NET-08`, split rows whose main part a reading closed; and 1 is re-owned (`CLK-42` 殘留, to `docs/interrupt-map.md` § 8.4) — each in its own row (`SPEC.md` §§ 17 and 19, `PROGRESS.md` § Carried forward). `D3-MISS`'s rtt part: `256\|avg` and `1472\|avg` closed by block 49's reading with the host's capture off; **`1472\|mdev` ⊘ by the main session's ruling**, which the owner may override — the 1,472-B mdev rose again on a third day, on both drivers and in both capture states, so it is not `rlx0`'s, and a one-day, three-series reference decides nothing at six series a side (`NET-121`, `notes/nic-driver.md` § 28.4). `C-19` is ⊘, deliberately replaced by `CLAUDE.md` § Environment's statement of its question; `NET-54` 殘留 went ⊘ at 8g with its instruments re-pointed (`FW-157`) |
| **`D6`** the `ethtool` ops executed on the board with a positive control; `MT-PORT` names the driver that served the link, from a source that outlives the vendor tree | 🟢 **met.** 量 block 50 (`r6b6q`): `/bin/linkprobe` read `drvinfo` `rtl819x-nic 1.5`, and `get_link` 1, 0, 1 across the owner's pull and re-plug of the cable, the positive control (`FW-144`, `notes/nic-driver.md` § 28.9); `MT-PORT` named `rtl819x-switch 1.2` both ways, from `/proc/rtl819x-switch` (`FW-93`). That the source outlives the tree is 量 on arm I's two boots of the vendor-free image (claim ③). ⚠️ `get_link` means any of ports 0–4 has `LinkUp`, not port 3; the restarted watch's half is unmeasured, its log lost at the power-off; `linkprobe` has not run on a vendor-free image, where `eth4`'s answer is expected to change from 122 to 19 (`notes/nic-driver.md` § 24.4) |
| **`D7`** an `mii_bus` for ports 0–4 whose PHY IDs equal the loader-side values address by address | 🟢 **met** (block 51, `r6b7q`; `NET-145`, `notes/switch-driver.md` § 14.2): `001CC880` at 0–4 through Linux's MDIO API, through the loader on the same boot and through the vendor's `phyReg`, register 3 at 2–4 read for the first time. ⚠️ Five equal IDs cannot show two addresses swapped, and the three sources share one MDIO controller, so a fault common to it is not excluded; one boot. Whether port 1 needs the loader's patch is read at register level only — `C-18` stays ⊘ (`NET-146`) — and the functional clause is ⊘ with its price |
| **`D8`** `R6`'s `D4` conjunct: `ping` both ways with no vendor Ethernet code in the image and a positive discriminator, or ⊘ with its price — only after `D1`–`D4` | 🟢 **met** (claim ③; `NET-167`), after `D1`–`D4` were met in the record (blocks 47, 48 and 50, read in the 113th and 115th segments); the stop-loss, two seatings with arm I failing, was not reached. ⚠️ "No vendor Ethernet code" is the census's scope, `rtl819x/` ∪ `rtk_vlan.o`, read as symbol names: a name absent is not proof that no byte survives (`notes/switch-driver.md` § 11.6), and the fast path, the feature glue, the WLAN driver and `rtl_gpio.c` stay vendor code in the image, which the census prints |

### The refutation conditions, and what each came to

Written with the step list on 2026-09-25, before `R6b-1`'s power.

* **`R6b-1`'s control fired** (block 46): arm A at E2's spacing read FAULT at three controls, so
  `R6b-1` was a failed reproduction, `D1` was recorded undetermined and none of its other arms
  localized anything (`NET-123`). It sent the gate to `R6b-2`'s image A/B, the stop-loss's end
  point, and not to a second per-length seating.
* **`M7`** fired on block 46 at 1,514 B and is void there under the first condition. Where the two
  arms could be compared, on block 48, the stack and the `tx` verb went wrong at the same seven
  lengths: the fault is not in `nic_xmit`'s path.
* **`M3`**: its premise did not hold — 61 B lost at the isolated spacing too (`A2-02`) — so its
  consequence was not triggered. Beside it the isolated-spacing fix arm ran clean (`NET-159`). At
  276 and 1,513 B, E2's losses were the previous length's state: each read 20 of 20 on its own
  re-armed ring (card B50's P6).
* **`M6` did not fire**: the looped `ph_len` was wrong at the seven lengths on blocks 46, 47 and 48.
  Its last sentence — a wrong looped `ph_len` puts the fault in the DMA engine — is not applied:
  where the loop closes was not measured, so no engine is named.
* **`M4` did not fire**, so it stands: at 277 B, on the stack path under 1.4, some replies carried an
  802.1Q tag on every boot (TCI `06E7`, 281 B, 4 bytes past the IP length); none under the fix, and
  none in either boot's sweep.
* **`M8` fired** (block 46, `A2-02`): a recovery in a bracket with `JabberErr` Δ 0. Jabber is not what
  stalls the ring, and `NET-67` 殘留 stayed open after the fix until 1.6 made the fix the default and
  it went ⊘ with `M8`'s reason.
* **The blackouts** were never tested: arm D ran while the host was not reaching the board
  (`NET-124`).
* **`D2`'s clause did not fire**: 0 in every bracket each card had scoped to the fix before its power
  — on block 48 thirty of them, TCP and UDP trials included — and 1.4 never read clean beside it.
* **`D3`'s clause did not fire**: E2 passed and the exchanges completed, 12 of 12 twice.

### The stop-loss, and what it came to

* **No segment cap** (the owner, 2026-09-25): seven segments. On 2026-09-27 the owner said the gate
  had run past the count he had in mind and relaxed its process — no freeze, predictions optional —
  for `R6b` only, the flash rules unchanged (`LOG.md` 第一百一十五段).
* **Zero flash-write commands and zero `FLR`, every press bracketed by a map**: held; see the flash
  paragraph below.
* **No step removes `/proc/rtl865x/` before `D1`–`D4`**: held, in the step list's sense — no image
  without it booted, and the mainline did not flip, before `D1`–`D4` were met in the record. 8b's
  variant build (`9107b20`, 2026-09-27 19:54) preceded the commit that recorded `D3`'s second boot and
  `D4` (`6fd0749`, 20:29) by 35 minutes; arm II first booted `SWCORE=n` at 00:21 on 2026-09-28; the
  mainline flipped at 8g (`18c9068`, `FW-157`).
* **Two seatings of per-length brackets that leave the stage undetermined**: stood at one of two
  after block 46 and never reached two — block 47's sweeps placed the stage, so `R6b-1`'s reopening
  condition did not fire.
* **`D8`'s, the owner's of 2026-09-26** — two seatings with arm I failing end `D8` ⊘ with its price:
  not reached; arm I passed on its first.

### The questions this gate must be able to answer

Derived in the step list; the plan has no `R6b`.

**① 「驅動說送出去了，那個訊框是在哪一層變掉的？」** Between descriptor memory and the switch's CPU
port, and no nearer. 量 the words the driver wrote read back as written with the engine's fetch held
(block 47); the CPU port counts the damaged frames as jabbers; and in loopback, which reaches no
switch counter, the looped `ph_len` comes back wrong at the same seven lengths. Inside that span are
the engine's fetch, its DMA and the CPU interface's framing, and none of them was measured: that it
is the TX DMA engine is 推.

**② 「你怎麼知道是修好了，而不是流量剛好變了？」** Because the unfixed setting failed on the same boot,
in the same cells, at the same spacing (claim ①), and stalled on the same boot under the same kind of
load (claim ②); and because the fix is clean at a spacing four times wider (`NET-159`). What the
answer does not cover: a second image, seating or day for `D2`, and the stack path at lengths other
than E2's eleven — the 1,455-length sweep went through `nic_do_tx`, in TX slots 0 and 1.

**③ 「廠商的驅動為什麼沒事？」** Because it writes the three length fields equal and rlxfw 1.4 did not.
讀 the vendor's `_swNic_send` and the loader's send routine both set `m_len` = `m_extsize` = `ph_len`
(`NET-122`); 1.4 set `m_len` four bytes short and `m_extsize` to a constant 2,046, the one writer of
four that differed. 量 copying the convention clears the fault (claim ①), and in loopback `m_len`
alone does. Why the engine needs them equal — why frame b breaks exactly where 8⌈`m_len`/8⌉ <
`ph_len` — is not known: the rule was fitted, not derived.

**④ 「把廠商的樹拿掉之後，你還看得到什麼？」** `asicCounter`, `port_status` and `eth4` are gone from
the mainline image. In their place `rtl819x-view` reads the MIB, the VLAN, netif and L2 tables and
311 two-source words, loading only (`NET-138`, `FW-156`), and `rtl819x-switch`'s page carries the link
state `MT-PORT` reads; arm I read all of them on the vendor-free image. The first `tbl l2` on the die
decoded its one learned entry at the row its hash names, which checks the window, the field layout
and the hash together (`NET-169`). Lost: `eth4` as a control driver on the same kernel, and the
vendor's memory node.

**⑤ `R6`'s third question — `OWN` 位元的寫入順序錯了會怎樣，你怎麼測出來？** It is not what broke
here, and that is measured. 量 1.5's read-back verb returned each descriptor as 1.4 wrote it with the
fetch held; reading each descriptor back before handing it to the engine (`txrb 1`, `2`) — the cure an
`OWN`-before-the-fields fault would need — left all 728 bad lengths bad; and 1.5's own check counted
0 bad of 5,820 fills (`NET-125`, `NET-129`). ⚠️ The injection `R6`'s entry said it never ran — `OWN`
set before the fields — has still not run.

### What `R6b` did not establish

🔴 **The mechanism of the transmit fault, as a cause.** The stage is a span with none of its
components measured; what the engine fetched is unseen, because the read-back reads memory with the
fetch held; `M1`-cover8 matches twelve maps length by length and is a rule fitted after blocks 45
and 46, not a derivation. `M5` — the port list, `0x3F` against the vendor's `0x1f` — never ran, though
it needs no image. The 802.1Q tag at 277 B (`M4`) is observed under 1.4 and unexplained. `NET-130`
殘留 (a looped `ph_len` of 2,048 that no byte source gives) and `NET-131` 殘留 (port 3's output above
`c` − `j` − `f` − `d` in 1.4 brackets) are ⊘, each reopened only at `txlen vendor`. No step owns the
mechanism (`docs/KNOWN-ISSUES.md`, `NET-112`'s row). It is what the operating clause fires on at
fourteen entries.

🔴 **The stall's mechanism.** `M8` as written is refuted, and the fix removed the stall together with
the corruption, so which engine state stops descriptor retirement is not separated; `NET-67` 殘留 and
`NET-78` 殘留 are ⊘ with `M8`'s reason, and what seating 32's `NET-76` state was stays unknown.

🔴 **The fix's regression on the mainline image.** `R6b-10`'s regression at the default ran on
`r6b10y`, a `SWCORE=y` image. At `SWCORE=n` — the mainline since 8g — `struct sk_buff` is 192 bytes,
not 200, and six of `rtl819x-nic.o`'s 7,955 instructions differ, each by that offset (讀 `NET-152`).
What has run on `SWCORE=n` at 1.6's default is arm I's and arm II's pings of 46 and 84 B and arm I's
`mfgtest auto`: not E2's eleven lengths, not the sweep, not a flood, not `iperf3`. And nothing has
been built from the flipped default: its recipe is `8b5ae480`, and `r6b8i` was built as
`quiet-noswcore` at `3685a3a4` with the same rules (讀, `notes/switch-driver.md` § 18.8).

🔴 **`D8`'s switch state is the loader's, on one boot path.** The weakest-thing paragraph. Beside it:
which of the five `EnablePHYIf` bits is necessary (only port 3 has a peer); link stability with EEE on
beyond arm I's minutes (8d ruling 4); one CPU receive queue (`QNUMCR`'s field inherited at 0); and the
price of the inherited `FFCR` — every unknown-unicast and multicast frame from any LAN port also
reaches the CPU — unmeasured, since this bench's one link carries only the host.

⚠️ **`D8` is one seating.** One image, `r6b8i`; one cold and one warm boot; port 3 and one host. The
discriminator's address half has one reader; boot 1's four-counter bracket is one host frame off,
推 its edge (`notes/switch-driver.md` § 17.6).

⚠️ **"No vendor Ethernet code" is a scope, and `R9`'s controlled variable moved with it.** The census
reads symbol names over `rtl819x/` ∪ `rtk_vlan.o`; vendor code outside that scope stays, and the ten
seam stand-ins answer the WLAN driver, bridge and L2TP paths, none of which was exercised
(`notes/switch-driver.md` § 13.10). Since 8g the mainline carries rlxfw's NIC driver where `R9`'s plan
wanted the vendor's as a controlled variable, so `R9` must build `quiet-swcore` (`docs/KNOWN-ISSUES.md`,
`notes/switch-driver.md` § 18.6, `FW-157`; 讀, nothing of it run).

⚠️ **The reset guard is one refusal and one permit**, on one boot, at one instant: `start`, `dumb` and
`restore` are not guarded, and `dumb`'s loss (`notes/switch-driver.md` § 8.10) is kept unexplained
(8d ruling 5). After `reset full` from the loader's state the tables, the MIB, `CPUICR` and the PHY
registers were not read (`NET-168`).

⚠️ **What `R6b-8`'s list named and did not build or run**: the bounded `TACI` writer (8d ruling 3: no
table write exists for it to bound), `imgprocs`' inverted mode (it refuses a `SWCORE=n` image by
design), `linkprobe` on a vendor-free image, and `mfgtest led` and `mfgtest button`, which need the
owner's eye and hand.

⚠️ **`D2`'s reach.** One image, one seating, one day, the fix typed; the stack path at lengths other
than E2's eleven; TX slots 2 and 3 on the wire at those lengths; any wire byte past 64, where both
captures were cut; 1.4 at the isolated spacing. On boot 1 every per-bracket capture count is the
readers' own, because the card's `pcapwin` never gave a true window (`FW-145`).

⚠️ **`D3`'s rate.** UDP board-receive loses 87–88 % at the socket; why the socket refuses (推 CPU),
why the client's `Sent` is short of the host kernel's count, and the rate and buffer arms (`NET-117`
殘留 ③), which never ran, are ⊘.

⚠️ **`D6` and `D7`'s edges.** `get_link` reads "any of 0–4 has `LinkUp`"; the restarted watch's half is
unmeasured; why the host adapter honoured `ethtool -r` is n = 1 (`NET-143`); a permutation among PHYs
0–4 is invisible to `D7`, and its three sources share one controller.

⚠️ **What `D5` carries.** `1472|mdev` is ⊘ by a ruling (`NET-121`): why the 1,472-B mdev rose across
three days is undetermined, and a capture effect of a few percent is not excluded at this test's
power. Re-owned rather than answered: `CLK-42` 殘留's mechanism, to `docs/interrupt-map.md` § 8.4,
whose row asks the owner to assign it a gate. At the close, `NET-54` 殘留 and `NET-124` 殘留 went ⊘ at
8g with their instruments re-pointed, and each now reopens with a read of `PCRP0`–`4` bit 0: arm II
made their counter shape — `LinkUp`, the host sending, port 3's input still — with `EnablePHYIf` clear
(`notes/switch-driver.md` § 16.7), and neither event read it (推, a candidate, not a cause).
`NET-134` 殘留 closed: `LEDCREG`'s value has three sources (`NET-162`) and 8d writes nothing to
`QNUMCR` (`NET-166`). `NET-25` closed as one unreproduced observation — 0 of 10 bounds the
per-cold-boot failure rate below 25.9 % — for `r6b8cr`'s boot path only, and the driver it was about,
`eth4`, is not in the mainline image any more.

⚠️ **Evidence taken under the relaxed process.** From 2026-09-27, block 51, the night's runs
(`NET-25`, `R6b-10`, `M3`'s arm, arm II) and arm I ran from committed, unfrozen cards and run sheets,
predictions optional, so `check-predictions`' mtime evidence does not exist for `D7`, `D8` or
`NET-25`. What stands in for arm I: its seven conditions were written at 14:59, before the 17:15
power-on, in the main session's rulings file outside the repository — a file's mtime, not a commit —
and 1.5's predicted boot mark, `RLXFW-SW-INIT=00001F1F`, was committed before power (`1f9ebf1`,
`NET-166`).

⚠️ **`C-19`'s instruction was not carried out on one night.** The night's cards and run sheets —
`CELLS-A`, `CELLS-B01`–`B10`, `RUN-r6b10` and `RUN-armII` — name no `C-19` and ran no host kernel-log
follower (讀; arm I's sheet, the control, names both), so the gate's longest idle — 2 h 8 min at the
loader prompt before group A's reads (`bench/2026-09-27d/`) — has no record against the row; the
console answered 27 cells after it (量). The row is ⊘ at this close (§ Carried forward).

⚠️ **The power ledger.** Nineteen power-ons by the segment headings' own counts (1, 2, 1, 2, 12, 1):
the headings say 電源按壓, 開電 and power cycle, and here each names one power-on. Seatings after 43
carry no number in the record.

⚠️ **Flash.** No card or run sheet of the gate sent `FLW`, `EW`, `EB`, `DB`, `FLR` or a non-zero
`AUTOBURN` (量, per block: block 45's card refused nothing under `cardcheck commands`; blocks 46–48's
sent strings, 182, 282 and 210; blocks 49 and 50's 210; block 51's 65; the night's 490; arm I's 104),
and the `AUTOBURN` word read `00000000` before every upload. Every map read in the gate, from block
45's closing map on, gave `0927be41…`, 31 groups the same and group 0 `DIFFER` as expected, over
4,186,112 B with `H601` not hashed; the standby power-on of 2026-09-27 and eight of `NET-25`'s ten
power cycles have no map of their own and lie between maps that agree. The maps cannot see `H601`,
two writes that cancel, or any byte outside their windows, and `n_writes` carries no information
(`FW-142`). The `FLR` bracket stays at 1,024 of 4,194,304 bytes = **0.0244 %**, and `FLS-26`'s ledger
does not move.

### The main session's rulings in this gate, which the owner may override

The owner's own rulings — no segment cap, the relaxed process, `NET-25` run with NB-1 first, `MSCR`
at `0x01`, `SWCORE=n` as a variant until 8g, `D8`'s stop-loss, PHY pages 0 and 1 only — are not
listed. Each below is recorded where it is cited.

1. `1472|mdev` ⊘, and `D5`'s rtt part closed with it (segment 115; `NET-121`, `notes/nic-driver.md`
   § 28.4).
2. `R6b-10` created because no step owned making the fix the default (segment 115), and `NET-67`
   殘留 and `NET-78` 殘留 ⊘ with `M8`'s reason once it landed (`NET-158`).
3. `NET-109` 殘留 ⊘ after `ByPassTCRC` gave the third pre-registered outcome (`NET-163`).
4. `D8` read by its letter as arm I's, with arm II its control rather than its pass
   (`notes/switch-driver.md` § 16.7).
5. 8d's scope: `init` a verb the standard `/init` types, not a driver-side boot write; `EnablePHYIf`
   and nothing else, no reset; the VLAN group inherited as a unit and the bounded `TACI` writer not
   built; EEE and `QNUMCR`'s CPU field inherited; `dumb` and `restore` kept (`NET-166`,
   `notes/switch-driver.md` § 17.1). `NET-28` 殘留 ⊘ with it.
6. `NET-37` 殘留 ⊘, narrowed, with the `MSCR` `0x01` condition called met in substance by the loader's
   `FFCR` traps (推 on one source) and its price stated (`NET-169`); `NET-33` 殘留 ②'s naming, `NET-31`
   殘留 and `NET-30` 殘留 ⊘ (`NET-168`, `NET-169`).
7. The mainline flip covers `quiet` and `loud`, `loud` being `quiet` plus `CONFIG_PRINTK`, and
   `quiet-swcore` keeps `y` (`notes/switch-driver.md` § 18.1, `FW-157`).
8. `R6b-1` recorded ⊘ rather than rerun, the image A/B being the stop-loss's end point (segment 112).
9. `D2`'s first boot met on its `ping` conjunct with its CPU-port conjunct void under card B49's P0;
   block 47's `tx`-verb and loopback arms read as `D1`'s (the rulings on block 47).
10. `D3-MISS` ②'s vendor series run on `eth4`, not on the vendor firmware; "whether port 1 needs the
    patch" read at register level, its functional clause ⊘ — both delegated by the owner to the main
    session (`LOG.md` 第一百一十三段 § 六), though the `R6b-7` row calls the second the owner's ruling.
11. The census's scope, `rtl819x/` ∪ `rtk_vlan.o`, and `R6b-7` as a precondition of 8c-code only —
    the main session's (`LOG.md` 第一百一十三段 § 六), as the `R6b-8` row now says.
12. Block 51's two missed predictions ruled drafting errors, not firings (segment 115).
13. `CLK-42` 殘留 re-owned to `docs/interrupt-map.md` § 8.4 as off the transmit path (segment 112).
14. The standby failure recorded as a bench rule — no unattended standby — not as a device question
    (`NET-165`).
15. `NET-54` 殘留 and `NET-124` 殘留 ⊘ at 8g (`FW-157`), with a read of `PCRP0`–`4` bit 0 added to
    each reopening condition at this close.
16. `C-19` ⊘, deliberately replaced (`PROGRESS.md` § Carried forward); `NET-134` 殘留 closed; and id
    marks set to ⊘ where the cell had already disposed of the row (`PSRP` 保留態的起點, `NET-07`,
    `NET-136` 殘留) and by the split-row rule (`NET-08`, `D3-MISS`).

---

## 2026-09-30 — `R1y` (the record's maintainability: `PROGRESS.md` split into state and record, a resolver for the line citations records keep, and three instrument defects repaired)

### One line

**v0.5+, one desk segment (the 117th) of the three the owner's stop-loss allowed, no plan estimate
to divide by, and zero power-ons.** `PROGRESS.md` holds state only: the fourteen closed
step lists, § Session ladder, § Corrections and 87 closed or declined carried-forward
rows left it verbatim for `docs/history/`, taking it from 1,018,554 bytes to
95,212 bytes, and each closed gate's row on § Gate board is cut to what closing it
meant and its evidence. A record's line citation into the moved text can still be followed:
`tools/citeresolve.py` reads the cited file as it was at the commit that wrote the citing line, and
of `LOG.md`'s 44 citations of `PROGRESS.md` it finds 15 at one place and 26 whose rows were
rewritten or grew in place after the citation. `TOOL-2`'s three instrument defects are repaired,
each against the control its row wrote before the repair, and every open row of `SPEC.md` § 17 names
a live gate. **Five of the six DoD rows are met; `D6` is met in part: CI on the pushed head stands
in for the final tree's full `desk-sweep`, at the owner's request.**

**The weakest thing here is that the tree that landed was never swept against the control.** `R1y-1`
swept a trial move of `7c4c694` beside that control; the move that landed is another tree, with its
parsers adapted and its citations repointed, and what stands between it and the control is CI on the
pushed head and the fifteen suites the move touches, all green, while `CLAUDE.md` § Closeout says targeted runs are no
substitute for the sweep. And every number here is about this repository's record, not about the
device.

### Three claims that stand

**① `D1` with `R1y-1` and `R1y-5` — `PROGRESS.md` holds state, and what left it is conserved where
it went.** 量 first by doing the move in a throwaway clone of `7c4c694` (`R1y-1`): the fourteen
closed step lists, § Session ladder, § Corrections and 86 closed or declined carried-forward rows
took the file from 2,866 lines and 1,018,554 bytes to 434 and 104,241; `docmove` conserved 864 of
864 blocks, and its negative control read 7 missing. A full `desk-sweep` of both trees — 116 steps
declared, 114 run in each — read the control 111 green with one red that any clone reads red
(`test-config-gates`, whose gitignored `build/` a clone lacks), the two census steps red at the desk
by design in both, and the moved tree 105 green and 7 red, six of them green in the control and each
named with its cause: `spec-check` (`C5` on `FW-73` and `FW-75`, `C12` on the trial's index
heading), `citecheck` (8 new rotted citations, 9 baseline rows naming nothing, 4 citations past the
end of their file, 4 onto a blank line), `test-citecheck`, `docsize`'s floor, and `cfcensus` and its
ratchet, which refused a file with no step-list header. `R1y-4` adapted those parsers before the
move landed (`b0850eb`): `docmove` conserved 1,064 of 1,064 blocks, 0 missing, and
`PROGRESS.md` is 522 lines and 95,212 bytes. 量 `R1y-5`
(`504ca55`): the sixteen closed rows of § Gate board are cut to what closing each meant and
its evidence, their old cells moved verbatim to `docs/history/progress-gate-board.md` — `docmove`
886 of 886 — with `cfcensus`'s parse of the board unchanged and no checked citation landing on a
board line; the four record citations of the board's old line lead, through `citeresolve`, to that
history file. Three old cells that were no longer true — `R1h`'s on the D side, `P4b-gate`'s on
`REEL-1` and `IMG-1`, and `P2`'s on what `R6b` owns — are not in the cut rows. ⚠️ What this does not
reach: the landed tree's full sweep (`D6`); the open carried-forward rows, which did not move; and
`SPEC.md`, untouched but for § 17's owner column.

**② `D3` with `R1y-3` — a record's line citation can be read the way the rule reads it, and the
reader depends on the citing commit.** 量 `tools/citeresolve.py` (`e274ccb`; 1,614 lines, about 535
of them its self-test, with a CI step and a `tools/ci-expected.tsv` row) takes the cited file as it
was at the commit that wrote the citing line and looks for that text in today's tree, importing
`citecheck`'s citation grammar and `docmove`'s normalisation rather than restating them. Two things
were measured before it could: dating needs whole-file `git blame -C` — plain blame dates 9,659 of
`LOG.md`'s 33,437 lines to `10b8fbc6`, a commit that only moved two entries to the end of the file,
and against the oldest commit whose patch added each citing line plain blame agrees on 346 of 425
and `-C` on 423 — and a cited path resolves in the citing commit's tree, since `citecheck`'s scan
drops a citation of a file deleted since without a word. 21 cases; a mutant that dates every
citation at `HEAD` is killed by 14 of them and kept in the tool as `R14`. On `LOG.md`'s 44 citations
of `PROGRESS.md`: 15 at one place, 1 ambiguous, 2 refused and 26 nowhere, each class explained
(`D3`; `FW-158`, `notes/record-integrity.md` § 5.7). ⚠️ What this does not reach: where a row that
grew in place lives now — and the 26 are exactly that.

**③ `D4` with `R1y-2` — three instrument defects repaired, each against the control its own row
wrote before the repair.** 量 (`ccc6459`) `FW-137`: `boot-timeline --probe` prints the first host
landmark past the capture's window on an `after` line with its distance; on seating B's twenty pairs
every line the old tool printed is unchanged, and all eleven rlxfw rounds' `net.up` equal the `D8`
values of `notes/boot-time.md` § 8.7 to the printed microsecond, seven through the `after` line and
four inside the window — read by the step's script and by the main session's `verify137.py`, which
share no code (the latter's first run read four `DIFFER`, its own regex expecting one space; the
parse was fixed, not a tolerance). `FW-138`: `audit-bench-log` gains an `"exact"` scope and its
control A3 — the twelve widening probes that passed silently now fire, the nine near-miss controls
still fire, and the two real lines stay silent; the same probe on the nine other `"line"` entries
moved three to `"exact"` and rewrote six reasons, and the CI corpus suppresses 39,093 before and
after. `FW-139`: both comments name `N41`, which alone kills `U3`'s mutant on the repaired tree, the
unmutated suite green at 77. On the real tree: `test-boot-timeline` 87, `test-console-capture` 77,
`hostprobe` 109, `test-leakscan-mutants` 24 and `leakscan` 17, whose `L4` is red in any clone
without `upstream/`, `HEAD`'s as well. ⚠️ `FW-137`'s control reads *七個 `--` 要讀出 `D8` join 的值到 1 µs*;
the value is on the new line and the seven `--` lines are unchanged, which the main session ruled
met. Seating A's rounds were not re-run through `--probe`.

### The DoD, read one row at a time

`R1y` has no row in the plan, so its DoD is the only one read.

| the DoD says | verdict |
|---|---|
| **`D1`** `PROGRESS.md` holds state only — § Now, § Gate board, § Release clock, the open rows of § Carried forward, the census block and the open gate's list — and every block moved out is conserved verbatim (`docmove`, 0 missing), with `docsize`'s budgets at the measured size + 3 % | 🟢 **met** (claim ①). `docmove` 1,064 of 1,064, 0 missing, beside its negative control's 7 missing; `PROGRESS.md` at 95,212 bytes against a `docsize` budget of 98,100. ⚠️ Beside the row's six parts the file holds one index of where each moved block went, headed so that `C12` and `cfcensus` do not read it as a step list — the risk `R1y-1`'s row wrote, which its trial heading met. The open carried-forward rows stand as they were (below) |
| **`D2`** every line citation into moved text in a file `citecheck` checks is repaired and read against its sentence, and `citecheck` reads 0 `ROT` and 0 suspended after the commit; no record's bytes change (`git diff` over `LOG.md`, `bench/`, `CHANGELOG.md`, `docs/GATE-RESULTS.md` and the existing `docs/history/` files shows appends only) | 🟢 **met.** Twelve checked citations of moved text point at the history line that holds what each cited as written, and every citation on every edited line was read against its sentence before the commit (`FW-119`'s reading). The reading found one, in `FW-75`, that had named the wrong row since `f3c425d`, a renumbering that re-dated its line, while `citecheck` called it `STABLE`; it now names the row its sentence is about. `citecheck` after the commit: 0 new, 0 suspended, 0 past the end of a file; its baseline lost the nine rows the move retired and gained none. `git diff` over the records across `R1y-4`'s and `R1y-5`'s commits: empty for `LOG.md`, `bench/`, `CHANGELOG.md`, `docs/GATE-RESULTS.md` and the three older history files, and `docs/history/progress-carried-forward.md` keeps its old bytes as a prefix with the 87 rows appended. ⚠️ For a citation the step repaired, `citecheck`'s 0 is met by construction — the repair re-dates its line, and from then on the oracle compares the new target with itself (`FW-119`) — so for those the reading is the check. Read over the whole gate, `docs/GATE-RESULTS.md` also changes by this entry and the clause's re-run below: an insertion above the clause, and edits to its heading, parenthetical and table, as at every re-run of the clause |
| **`D3`** every line citation of `PROGRESS.md` in `LOG.md` resolves to one location, to several (listed), or to none, each none explained | 🟢 **met, with one class the row did not name** (claim ②). Of 44 citations on 43 lines, at `e274ccb`: 15 at one place, 3 still at the cited line and 12 moved within the file; 1 ambiguous, a table separator; 26 nowhere, each a labelled row whose text changed after the citation — § Now's `Next after this`, `Active step` and `Active gate`, rewritten every segment, the carried-forward rows `R1C-1`, `CF-1`, `WRAP-1`, `LOG-1`, `CITE-1`, `CITE-2` and `C-10`, and the step rows `R1-pub-2`, `-4`, `-6`, `-7` and `R5-5`, which grew in place; and 2 refused, one backwards range that the citing line itself records as a botched repair — a class the row did not write, explained by its own line. Second instruments: the cited text re-read with `git cat-file` matched 323 of 323, every reported location held its text at `HEAD` (509 of 509), single-line match counts agreed with `git grep -F` on 269 of 269, and the main session recomputed two examples with plain `git log -S` and `cat-file`. Its self-test reads 21 of 21 on the moved tree. ⚠️ `R1y-3`'s own population, one `2026-09-23` entry's citations, was empty — those entries cite `PROGRESS.md` nowhere — so all 44 were read |
| **`D4`** `TOOL-2`'s three controls, as its row writes them | 🟢 **met, `FW-137`'s under a ruling** (claim ③; `SPEC.md` `FW-137`–`FW-139`, `notes/dev-loop.md` §§ 20.3–20.5). `FW-138`'s and `FW-139`'s read as written. `FW-137`'s — *七個 `--` 要讀出 `D8` join 的值到 1 µs，讀得到的十三個不動* — held with the value on an `after` line, because the repair left every line the old tool printed unchanged, the seven `--` among them; the main session ruled that met. ⚠️ Seating A's rounds were not re-run through `--probe`; no other case pointer in `tools/` was checked; and a future log that carries the needle of one of the six remaining `"line"` entries can hide a real hit on its line |
| **`D5`** no open § 17 row names only a closed gate, or none | 🟢 **met** (`R1y-6`, `eac5ab2`). 37 rows given a disposition: 4 re-owned — `REG-13`, `REG-14` and `FLS-06`–`FLS-08` to `R8`, `FW-67` to `R9`; 22 ⊘, each with a category, a reason and a reopening condition; 8 marked ✅, answered by their own text or owner file; and 3 split into ✅ and ⊘, the id cell carrying the less settled half's mark. Nine rows stay open, each naming a live gate, `LDR-21` and `FW-68` through `C-13` (`R8`) and `VDR-1` (`R9`); `LDR-22`'s and `CPU-45`'s main rows lost leads that contradicted their owner files. Two parsers that share no code: the step's, and the main session's token parse of the owner cell, which fires on `7c4c694` as its control — 44 open rows, 41 of them naming no live gate — and at `HEAD` reads 9 open, 2 naming no gate by token, `LDR-21` and `FW-68`, resolved by hand. `spec-check` green before and after. ⚠️ The step's edit re-dated a citation that had already rotted, `CPU-04`'s into `SOURCES.json`, which sat on `citecheck`'s baseline: from that commit the oracle called it `STABLE` (`FW-119`) and its baseline row went stale, which `C4` read only after the commit, because a dirty `SPEC.md` suspends its baseline rows; `bbd442a` repaired the citation. Read with `citecheck`'s own oracle at the commit before the edit, the step's 42 edited lines carried 11 citations, 10 `STABLE` and that 1 `ROT`. The row holds at this close only (below) |
| **`D6`** the final tree's full `desk-sweep` reads as `R1y-1`'s control, and CI is green on the pushed head | ⚠️ **met in part.** CI on the pushed head: `b0850eb`, success (run 36628136555). The final tree's full sweep was not run: on 2026-09-30 the owner asked for speed and let CI on the pushed head stand in. What that leaves unread is the comparison the row names — CI's green is each step's verdict on the pushed head, not a reading of the landed tree against `R1y-1`'s control. The sweeps that did run are `R1y-1`'s, of the control and of a trial move of `7c4c694` (claim ①) |

### The refutation conditions, and what each came to

Written with the step list and committed at `R1y-0` (`5063332`), before any step landed.

* **A block `docmove` reports missing** did not fire: 1,064 of 1,064 blocks of the move and 886 of
  886 of the board cut conserved, 0 missing, while the tool's negative control read
  7 missing.
* **A checker's verdict moving on a population the move did not change** moved in `R1y-1`'s trial,
  which is what that step was for, and each move was a checker reading a location rather than a
  meaning: `C12` took the trial's index heading for a step list, `spec-check`'s `C5` fired on
  `FW-73` and `FW-75`, whose values were no longer in the file their owner cells named, and
  `cfcensus` refused a file with no step-list header. `R1y-4` made the parsers read the moved lists
  where they went (`cfcensus` and `spec-check`'s C12 now read `docs/history/steps-*.md` as well, and `cfcensus`'s L11 reads `docs/history/progress-corrections.md`) and repointed the owner cells (`FW-73`, `FW-75`, `MEM-14` and `FLM-10`);
  on the landed move `cfcensus --self-test` reads 64 of 64, its `ratchet` and `check` read as on `e274ccb` — 0 findings, 15 live-owned — and `spec-check` is green.
* **The resolver's `HEAD`-reading mutant survives** did not fire: 14 of its 21 cases kill it, and it
  is kept in the tool as `R14`.
* **A citation in `docs/GATE-RESULTS.md` passing `citecheck` only once its entry is edited** could
  not fire: this file holds no line citation of `PROGRESS.md` — 0 in `R1y-1`'s census at `7c4c694`,
  and 0 again at `e274ccb` (讀, by `grep`). No entry was edited.

### The stop-loss, and what it came to

* **Three segments**, the owner's, who expected one: closed in one, the 117th.
* **No record is edited; a step that would need to stops and goes to the owner**:
  none needed to; `git diff` over the records shows the one append and nothing else.
* **`R1y-4` lands only on a sweep that reads as the control's**: replaced by the owner. On
  2026-09-30 he asked for speed; the final tree's full sweep was not run, and CI on the pushed head
  stands in (`b0850eb`, success (run 36628136555)). `R1y-4` landed on the fifteen suites the move touches, all green instead, and that is why `D6`
  is met in part.

### The questions this gate must be able to answer

Written in the step list at `R1y-0`; the plan has no `R1y`.

**① 「`PROGRESS.md` 為什麼長到 1 MB？」** Because the record of being wrong was kept inside a state
document, and each link of a chain fed the next (`FW-112`, `notes/record-integrity.md` § 5.5). The
rule that negative results stay in place, right for records, was applied to a file whose job is to
say what is true now; frozen cards cited it by line, so no line could be added and new text went
into old cells — over 39 commits it held at 2,434 lines while its bytes grew by 65,906; each session
appended, because appending is locally safe; the checkers came to parse the accreted form; and
nothing measured size. 量 at `7c4c694`, by `awk` over its level-2 headings: 1,018,554 bytes, of which
§ Now with its preamble was 5.5 K, the fourteen closed step lists about 430 K (`R3`'s alone 124 K),
§ Session ladder 199 K, § Carried forward 249 K, § Corrections 93 K and § Gate board 30 K. `D1`
moved the records out: the file is 95,212 bytes under a `docsize` budget of
98,100, which fails above the budget and below half of it. Not covered: `SPEC.md`,
1,410,196 bytes in 821 rows at `7c4c694`, repaired here in one column.

**② 「舊紀錄引用的 `PROGRESS.md` 行號，那一行現在在哪裡？」** Ask `tools/citeresolve.py`. It dates the citing line by
whole-file `git blame -C`, reads the cited lines in that commit's tree, and looks for their text in
today's: the answer is one place, several, none, or a refusal with its reason. Of `LOG.md`'s 44
citations of `PROGRESS.md`, 15 have one place (`D3`), and the four record citations of the board's
old line lead to `docs/history/progress-gate-board.md` (`R1y-5`). For the 26 whose rows were
rewritten or grew in place, the answer is the cited text as it stood and no current location — and a
record's line number is never repaired; it is read through the resolver.

### What `R1y` did not establish

🔴 **Where a row that grew in place lives now.** 26 of `LOG.md`'s 44 citations of `PROGRESS.md`
resolve to the text they cited and to no current location: § Now's three rows were rewritten, and
seven carried-forward rows and five step rows grew in place after the citation (`FW-158`). A
row-identity reading, as `FW-110`'s, would find most of them, and none was built. `citeresolve` also
reads nothing under `upstream/`, `src-vendor/` or `plan/`, and no extensionless file, bare line
number, fenced citation or number written with a thousands comma (`notes/record-integrity.md`
§ 5.7).

🔴 **The tree that landed was not swept against the control** (`D6`, the stop-loss's third line, and
the weakest thing above). CI on the pushed head stands in, at the owner's request of 2026-09-30; the
step-by-step reading against a control was made for `R1y-1`'s trial move, not for the tree that
landed.

🔴 **Four things stay unchecked, because the four enforcers booked for them are ⊘** by the owner's
rule of 2026-09-26, which admits a new checker only against bricking, an `H601` leak or a misjudged
result: a citation wrong the day it was written, which `citecheck` reports `STABLE` (`FW-109`);
citing by line where an id exists; § 17's owner column going dead when its gate closes (`FW-111` ①);
and the census block `cfcensus` generates going stale (`FW-111` ②). Each was repaired once instead —
§ 17 by `R1y-6`, the block by `cfcensus write` at this close — and nothing will say when either is
wrong again.

⚠️ **Records' line citations into moved text can be read, never repaired.** `LOG.md`'s 44, the 15 in
frozen `bench/` artefacts and the 3 in `docs/history/progress-now.md` keep the numbers they were
written with (`R1y-1`'s census at `7c4c694`); a reader who follows one into today's `PROGRESS.md`
lands on whatever that line now holds, unless they ask the resolver.

⚠️ **`FW-119`'s reading is a session's, not a tool's.** The reading it asks for before a commit —
every citation on every edited line, read against its sentence — was done by scripts and readings
kept outside the repository (`$FWRE_WORK/rebuild/s117/redate.sh`, and the landing's `repairs-FW119.txt`); nothing in the tree repeats it. `R1y-6`'s commit
shows what that leaves: its edit re-dated `CPU-04`'s already-rotted citation into `SOURCES.json`,
which `citecheck` saw only after the commit, and only because its baseline held that citation
(`D5`). `notes/record-integrity.md` § 5.6 already says a tool could do the dating half and not the
reading.

⚠️ **Six `"line"`-scoped entries of `audit-bench-log` still exempt every pattern on their lines**
(`FW-138`). The control MAC on a line holding the needle was silent under all nine `"line"` entries;
three moved to `"exact"`, and the six that stay say in their reasons what they do not catch. A
future log that carries one of those needles can hide a real hit on the same line.

⚠️ **`SPEC.md` was repaired in § 17's owner column only**, the owner's scope for this gate: no row
was rewritten and § 19 was not re-sectioned. At `7c4c694` it was 1,410,196 bytes in 821 rows, median
row 1,345 B, the fifty largest rows 22 % of it, § 19 500 K, § 14 239 K and § 17 216 K.

⚠️ **The open carried-forward rows were moved nowhere and not rewritten.** `D1` moved closed and
declined rows only; the 25 open ones stand in § Carried forward as they were, and
nothing measured how much of their text is state.

⚠️ **Fourteen lines in ten files under `tools/` cite `PROGRESS.md` by line number** — comments,
docstrings and one printed message — and eleven of them name the risk columns of `R1-pub-1` and
`R1-pub-2`. 量 at `7c4c694`, before any step of this gate: the four targets they quote, which cover
13 of the 14 lines, each stood on another line, so these were stale before `R1y`; `citecheck` reads
`.md` files only, so nothing checks them, and this gate left them. One more sits in a `bench/`
script, a record.

⚠️ **`D4`'s edges.** `FW-137`'s control is met by a ruling, with the value on a line its words did
not name; seating A's rounds were not re-run through `--probe`; and whether any other case pointer
in `tools/` is right was not asked (`FW-139`).

⚠️ **`D5` holds at this close.** When `R8` or `R9` closes, the rows naming it will name a closed
gate, and no tool reads the column; and an owner question kept in a notes section rather than in
§ 17 was outside the population, by the owner's scope.

⚠️ **Flash.** No step touched the board — zero power-ons in the gate — so zero
flash-write commands and zero `FLR`; the `FLR` bracket stays at 1,024 of 4,194,304 bytes =
**0.0244 %**, and `FLS-26`'s ledger does not move.

### The main session's rulings in this gate, which the owner may override

The owner's own rulings — opening `R1y` with a stop-loss of three segments, `R6b`'s relaxation
carried over with the flash rules unchanged, `SPEC.md` limited to § 17's owner column, CI on the
pushed head in place of the final tree's full sweep, and `NET-165`'s no-unattended-standby rule
restated for `CLAUDE.md` — are not listed. Each below is recorded where it is cited.

1. The four booked enforcers ⊘ under the owner's rule of 2026-09-26, which came after the booking
   (the step list, *Scope*).
2. `FW-137`'s control met with the value on an `after` line, not on the `--` line its wording
   assumed (`FW-137`, `notes/dev-loop.md` § 20.3).
3. `SPEC.md` § 17: all 37 dispositions as drafted; `CLK-15` 冷暖差 ⊘, not a retraction; `MEM-08` and
   `BRD-01` ⊘ rather than re-owned to `P3`.
4. `cfcensus` reads `docs/history/steps-*.md`, rather than owner cells being edited to dodge its
   `L2` (`R1y-4`).
5. `D3` read as met, its two refusals — one backwards range — a class the row did not write,
   explained by the citing line itself.
6. `D6` read as met in part, its CI conjunct holding, rather than not met.
7. The census block regenerated in the move's commit, though `cfcensus check` never compares
   it: it was already stale at `e274ccb`, `LIVE` 16 where the live census read 15.
8. `FW-75`'s citation repointed to the row its sentence is about, `R1-pub-4`'s, rather than to the
   line its digits named.
9. `PROGRESS.md`'s one citation of a 2026-09-14 § Now row left as it is: its text is nowhere, and
   the row it cites was neither moved nor shifted.
10. The full `desk-sweep` dropped at the owner's request for speed, CI on the pushed head
    standing in (`D6`).

---

## 2026-09-30 — `R8a` (a signed container verified on the silicon with zero flash writes, and the half of `R8` that needs a write carved out and booked)

### One line

**v0.5+, one segment (the 118th, shared with `R7`), and zero power-ons of its own. There is no
`R8a` estimate to divide by**: the plan costs `R8` at 22 segments and § Gate board at 18, both
covering the write half as well, and `R8a` is deliberately uncosted for `R1h`'s reason — it is a
split of that work, not work added to it. `rlxboot`, a freestanding 16,240-byte payload linked at
`0x81800000` with no libc, no `malloc` and no recursion, reads an `RLXU` container staged in RAM and
either boots it or refuses and names the check that refused. Four rounds in one seating read all
three of the board row's pass conditions on the die: a correct container accepted and its payload
booted (`RLXBOOT-SIG ok` / `DIGEST ok` / `VER cur=1 ctr=0 ok` / `BOOT load=80500000 entry=80500000`,
then `RLXFW-ID0=3685A3A4` and a shell); one flipped **payload** bit refused at `DIGEST bad` /
`REFUSE digest` with no `BOOT` line; and a version below a RAM-staged counter refused at `VER cur=1
ctr=5 bad` / `REFUSE rollback`, with the same container at counter 0 booting as the control. 43
assertions read line by line, four rounds PASS (`FW-170`, `FW-171`). Six steps of six closed. Ten
uploads, no `FLW`, `EW`, `EB` or non-zero `AUTOBURN`, and both returns to the loader were `busybox
reboot -f`. **`R8a` closing does not close the `R8` board row**, which stays open until `R8b` runs.

**The weakest thing here is that the two readings this seating took off the hardware — the flash
counter and the cache — each cannot distinguish the state they report from another.**
`RLXBOOT-CTRSRC flash` with `ctr=0` in rounds 1 and 2 is what an erased bitmap gives *and* what an
undecoded MMIO window gives: `FLS-11` is 量 at `0xBD000000` over 4,096 bytes and this counter sits
4,128,768 bytes further in, where the window's decode size is measured nowhere — which is why pass
condition ③ was driven from RAM and not from flash. And rounds 1 and 4 copied 1,114,112 bytes to
`0x80500000` and jumped into them, which is the first of the two readings `notes/rlxboot.md` § 6
offered; its second — reading the destination's first instruction word back with `DW` and comparing
it with the container's — was not taken, no cell of the seating read `0x80500000` (量, the 26
captures' `sent` fields are six `DW`/`J` commands a round and two `busybox reboot -f`), and that
section's own sentence is that on a write-back cache **without** write-allocate *"it booted"* is not
evidence that the flush is unnecessary. So the composite path is 量 and `CCTL 0x200`'s effect on
this die is still measured nowhere.

### Three claims that stand

**① The board row's three pass conditions hold on the silicon, and the two refusing rounds each
carry their own positive control inside the same capture.** 量 four rounds, one seating, 2026-09-30
(`bench/2026-09-30/R8A-*`; `FW-170`, `FW-171`). Round 1: the good container with the counter read
from **flash**, erased and therefore 0 — `RLXBOOT-V1 build=6395889d` / `CTRSRC flash` / `HDR ok` /
`SIG ok` / `DIGEST ok` / `VER cur=1 ctr=0 ok` / `BOOT load=80500000 entry=80500000`, then the payload
decompressing and reaching its own prompt. Round 2: the same build with one **payload** bit flipped,
file offset `0x80000` bit 0 — `SIG ok` and then `DIGEST bad` / `REFUSE digest`, no `BOOT`, no boot,
`refuse-action reset`, the watchdog bite and the loader prompt caught by `--esc-after`. Round 3: the
**same** container with a RAM counter of 5 — `CTRSRC ram` / `SIG ok` / `DIGEST ok` and then `VER
cur=1 ctr=5 bad` / `REFUSE rollback`. Round 4: the same container with the RAM bitmap at 0 — `VER
cur=1 ctr=0 ok`, and it boots. 🟢 **Round 2 flips a payload bit so that `SIG ok` prints in the same
capture**, which is what shows Ed25519 ran and passed; a flipped signature bit would have given a
`SIG bad` indistinguishable from a wrong key, a byte-order fault, or a container that never arrived.
🟢 **Rounds 3 and 4 differ in the bitmap's value and in nothing else** — same container, same
`CTRSRC ram` — so round 3's refusal cannot be attributed to a bitmap merely having been staged.
Three discriminator cells carry that, each read in all four rounds: `DW 81080000 4` is the only place
the two containers differ, their headers being byte-identical (`4AE4B216` in rounds 1, 3 and 4 and
`4BE4B216` in round 2), `DW 81000000 4` read `524C5855 00010060 00000001 00110000` four times of
four, so `MEM-14` did not bite and no round is void, and `DW 81700000 4` read `1753169B…` in rounds 1
and 2 against `52434E54 07FFFFFF` and `52434E54 FFFFFFFF` in rounds 3 and 4, so no stale bitmap
survived a reset into a round that was not meant to have one (`MEM-17`). The staged head of
`rlxboot` itself was read back before each jump and read `3C1D8181 27BDC740 3C088180 25083F70` four
times of four. ⚠️ What this does not reach: one seating, one image, one build id and four rounds; the
`--until` of every jump cell accepted the prompt **or** the shell, so the capture did not presuppose
the outcome, but the verdict that compared 43 assertions line by line is
`$FWRE_WORK/rebuild/s118/r8run/40-verdict.py` with a self-test of 14 of 14, and it lives outside this
repository.

**② The verifier's authority is placed where a refutation can be written, and the crypto is an
import that says so.** 讀 and 量 (`FW-166`, `FW-172`; `notes/rlxboot.md` § 5). Ed25519 verification
and SHA-512 are **TweetNaCl 20140427**, declared in `SOURCES.json`, public domain, regenerated from
the upstream file by `src/rlxboot/test/mk-import.sh` naming retained line ranges, with
`check-import.sh` failing on one byte's difference; nothing in the tree calls them rlxfw's. The
argument for importing is refutability rather than difficulty: five RFC 8032 vectors cannot refute a
carry bug that appears on one input in 2^30, so the test set that would establish hand-written
arithmetic mod 2^255−19 does not exist at desk scale, and a hand-written field implementation would
have been a published claim whose refutation condition cannot be written. SHA-256 is rlxfw's own
(`src/rlxboot/sha256b.c`) on the mirror argument — no rare-input failure mode of that kind, the RFC
6234 vectors exercise the whole round schedule, the padding is enumerable — and it is cross-checked
against RFC 6234, against coreutils at every message length 0..200, and against a second
implementation written by another hand in the same segment. 🟢 **Three implementations sharing no
code derive the same public key** `2152f8d1…9881db12` from the one development seed: `tools/rlxsign.py`
(pure Python from the RFC), `src/lib/ed25519.c` (host and big-endian MIPS under `qemu-mips-static`)
and **OpenSSL 3.0.13, run by the main session rather than reported by an agent**. 🟢 The order the
checks run in is itself asserted: nothing is copied and no payload byte is read before the header's
signature verifies, `struct rlxu`'s `hashed` and `copied` make that testable, and all 9,472 bit-flip
cases assert it rather than a chosen example. ⚠️ The mutation that reordered verification to hash the
payload before checking the signature — this unit's own `check_image()` defect — was caught by only
one functional case, and **only because every case asserts its refusal reason by name**; a suite that
asked "was it rejected?" would have been blind to it (`notes/rlxboot.md` § 9, `M2`). ⚠️ `src/lib/ed25519.c`
carries the build's one warning exemption, `-Wno-sign-compare`; `crypto_sign_open` was replaced
rather than called, for its caller buffer and because it does not test `s < L`.

**③ Nothing in the gate can write flash, the guards are shown permitting as well as refusing, and the
stock loader refuses the container on two independent readings.** 量 `tools/mkfw2.py` 21 of 21,
`tools/rlxsign.py` 16 of 16, `tools/flashguard.py` 23 of 23 and `tools/test-mkfw2.sh` 56 of 56
(`FW-166`); that suite's `X` cases are the sweep that no tool here emits, prints or executes `FLW`,
`EW`, `EB` or a non-zero `AUTOBURN`, with `X2b` the control that the sweep can fire at all.
`flashguard` owns four forbidden classes — the loader region, `H601` delegated to
`flashwin.overlaps_forbidden`, the read-only rescue slot, and off-chip destinations, which `burn()`
truncates rather than refuses — and `B2` drives eight **permitted** ranges through the CLI as the
other half, with `M1` the mutation that turns `F8` and `F13` red
(`notes/update-chain.md` § 4). On the target side `flashscan.py` reconstructs every address the
linked payload builds and refuses any in `[0xB8001200, 0xB8001300)`, and `flashsafe.sh` shows it
refusing a planted store into the controller block and permitting the same store moved
(`notes/rlxboot.md` § 7). 🟢 The stock loader reads no header it recognises in a container, on two
independent readings: `mkfw2 verify --stock-loader` (offset `0x00` is `RLXU`, neither `cs6c` nor
`cr6c` and none of `burn()`'s eight section signatures) and `tools/rtkimage.py check`, which is not
this gate's code and exits 1 on **two** conditions — `sum16 0x9C4C` where `C-4` requires 0, and body
≠ `nfjrom` — while reading the vendor-shaped `linux.bin` correctly in the same run as its control.
That refusal is a requirement rather than a nicety: the loader's scan path goes through neither the
signature check nor the counter, so a slot image the loader recognised would let one corrupted byte
elsewhere boot an old image directly (plan § D6). ⚠️ `flashguard` guards a **destination range**,
which is an argument someone computed: it does not read the loader's `burnAddr`, cannot see a `J` into
code that writes flash, and cannot see an upload made while the burn word is armed. ⚠️
`upstream/tools/loader-unpack.py` does **not** reproduce `check_image()`, although both the
out-of-tree `SPEC-R8a.md` and plan § D6 say it does — `grep -c check_image` over it returns 0 — and
what the desk reproduction actually is is `rtkimage.py`'s `sum16` plus its `cr6c` parser, imported
rather than written again.

### The three pass conditions, read one at a time

`R8a`'s conditions are § Gate board row `R8a`'s three clauses, which are also the plan's `R8` pass
row ① to ③; its ④, ten power cuts during a write, is `R8b`'s and is not read here.

| the condition says | verdict |
|---|---|
| **①** a correct signature accepted and the image boots | 🟢 **met on two rounds** (1 and 4; `FW-170`). Both printed `SIG ok` / `DIGEST ok` / `VER … ok` / `BOOT load=80500000 entry=80500000` and both reached `RLXFW-ID0=3685A3A4` and a shell with `rlx0 10.1.1.3`. ⚠️ The image that booted is `r6b8i`'s `nfjrom` wrapped in a container, not a slot image and not a flash boot: the loader staged both files by TFTP and `J 81800000` entered `rlxboot` |
| **②** one flipped bit anywhere refused | 🟢 **met for one flip, by the round that keeps its positive control** (round 2; `FW-171`). The bit was chosen in the **payload** so that `SIG ok` appears in the same capture. The *anywhere* half is the host suite's, not the device's: 9,472 flips — 768 header, 512 signature, 8,192 payload — every one rejected, and the refusal stages the sweep reached were header 64, bounds 376, signature 840 and digest 8,192 (`notes/rlxboot.md` § 8). ⚠️ So *anywhere* is 量 under `qemu-mips-static` and one flip of 9,472 is 量 on the die |
| **③** a version below the anti-rollback counter refused | 🟢 **met with its control** (rounds 3 and 4; `FW-170`, `FW-171`). ⚠️ Driven from the **RAM** source on purpose, because an undecoded window and an erased region both give `ctr=0` on the device and the flash source cannot tell them apart. Nothing in `R8a` advanced the counter, so what is read is the comparison and not the bitmap's monotonicity |

### The steps' DoD, read one row at a time

`R8a` has no row of its own in the plan, so the step list's DoD column is what is read. Six steps,
`R8a-0` through `R8a-5`, all closed.

| the DoD says | verdict |
|---|---|
| **`R8a-0`** the order is the specification: nothing copied and no payload byte hashed before the header's own signature verifies, and the destination bounds checked before any copy | 🟢 **met** (`notes/update-chain.md` § 2, `notes/rlxboot.md` § 3). Steps 1 to 5 are pinned, `hashed` and `copied` are asserted 0 on every refusal at or before step 3 across all 9,472 cases, and seventeen bounds are refused **by name** so a refusal for the wrong reason is a failure. Four bounds were added to the format as the notes say — `payload_len == 0`, word alignment of `load_addr` and `entry_addr`, and the stage-2 window as a refused destination. ⚠️ The format's and the memory map's owner of record is `SPEC-R8a.md`, a segment-local file under `$FWRE_WORK` and not in this repository, cited from committed notes and committed C: what a reader here can follow is `notes/`, `SPEC.md` and the code |
| **`R8a-1`** `flashguard` refuses the three regions and **permits a legitimate neighbour**; `mkfw2` refuses the auto-executed names and refuses to emit anything the stock loader would accept | 🟢 **met** (claim ③). ⚠️ Plan precondition ③ is met only **in half**, and this row is where the half lands: `mkfw2 build --flash-at` is optional and defaults to none, so the guard fires on a destination the caller chose to declare, and the container format carries no flash destination at all. ⚠️ `FW-169` is a defect recorded and deliberately not fixed under the owner's rule of 2026-09-26 |
| **`R8a-2`** RFC vector sets on the host **and** on the target under qemu; a bit-flip sweep where every single flip is rejected; the crypto's provenance stated | 🟢 **met** (claim ②; `FW-172`). `t_crypto` 36 checks, `t_container` 71, the truncation sweep 1,184 lengths refused against the one accepted, `hazlint` 0 violations in 405 loads, and a measured verifier stack of 4,392 bytes against 32,768 reserved — a painting high-water mark, so a **lower** bound. The vectors are extracted by a parser with its own negative control rather than transcribed, and RFC 8032 § 7.1's TEST 1024 is deliberately absent with OpenSSL in its place, because a message transcribed from memory can only be a false red or a re-signed vector that agrees with its own tool. ⚠️ The cache hazard the row named is the one thing the desk could not settle: qemu's Malta writes `XContext` for the same instruction, so both `CCTL` writes were exercised as instructions and not as cache operations |
| **`R8a-3`** two implementations that share no code agreeing, a mismatch being a finding; the counter's flash read exercised against the real erased region and the rejection driven from a RAM bitmap, each labelled | 🟢 **met, and with three implementations rather than two** (claim ②; `FW-172`). The flash read is round 1's and round 2's `CTRSRC flash`, the rejection is rounds 3 and 4's `CTRSRC ram`, and the console line says which was used in every round. ⚠️ *Exercised against the real erased region* is exactly as strong as the window's decode, which is unmeasured at this address |
| **`R8a-4`** the three outcomes read from the console, `AUTOBURN` reading `00000000` before any upload and no flash verb issued in the seating | 🟢 **met, with one precision the row's wording does not carry** (claim ①). The `AUTOBURN` word at `0x8040D4A0` was read **four** times, once at the head of each round, and read `00000000` each time; the seating made **ten** uploads, so the reading is one per round and not one per upload. What the ten uploads sent on the console is `AUTOBURN 0`, `LOADADDR` and `IPCONFIG` — `AUTOBURN 0` disarms and is not one of `CLAUDE.md` § Flash's four verbs — and 量 over every capture and every upload record of the rounds, no `FLW`, `EW`, `EB` or non-zero `AUTOBURN` appears. ⚠️ The rounds cost no power action: `/proc/uptime` read 8,808.87 s at 10:58 and the first round's first cell ran at 11:17, and the two returns to the loader are `busybox reboot -f` with `Reboot Result from Watchdog Timeout!` in the capture (`FW-37`). All four rounds ran inside four minutes of console time, 11:17:44 to 11:21:39 by the captures' own `started_wallclock` |
| **`R8a-5`** the entry states what `R8a` established and what it did not — nothing about writing flash, nothing about power cuts, nothing about key management, no claim of secure boot on a part with no evidence of a key-hash fuse | 🟢 **met by this entry and the booking below.** The row's hazard is *letting `R8a`'s success read as the board row met*, and the answer is in the one line above and on § Gate board: the `R8` row stays open |

### The step list's hazard column, read one at a time

`R8a`'s list carries no numbered refutation conditions and no stop-loss; what it carries is a
per-step column naming where the step is most likely to be wrong, written with the list at `R8a-0`
before any step landed. That is weaker than `R6b`'s `M1`–`M8`, and the entry says so rather than
promoting a hazard into a pre-registration. What stood in for pre-registration on the device is the
run script's ten assertions and its no-flash-verb scan, both run **before the port opened**, and the
per-round expectations the verdict script compared line by line (`FW-170`).

* **`R8a-0`, repeating the stock loader's defect** — did not happen, and the mutation that would
  have introduced it is in the suite: `M2` (`notes/rlxboot.md` § 9) reorders the two steps and 7
  cases go red, six of them order assertions and the seventh a **verdict** that was not predicted.
* **`R8a-1`, a refusal with no positive control** — answered by construction: every forbidden range
  has a permitted neighbour, `B2` drives eight of them, and `F3` is the case that goes red if
  `H601`'s delegation is ever replaced by a copy.
* **`R8a-1`, a container the loader recognises** — refuted twice, once by this gate's own reading and
  once by a tool that is not its code (claim ③).
* **`R8a-2`, cache handling** — the hazard the gate could not close at the desk, and the one the
  bench moved only part of the way (the weakest-thing paragraph).
* **`R8a-2`, deep recursion on a bare-metal stack** — did not fire: the call graph is a chain five
  deep, not a tree, and the stack was measured rather than argued.
* **`R8a-3`, two implementations agreeing because they share a mistake** — the reason the seed is
  fixed and the keys derived independently; the third derivation is OpenSSL, which shares no
  language with either.
* **`R8a-4`, a refusal that is really a staging failure** — this is the hazard the round design
  answers, and it is why the entry's claim ① leads with the two positive controls rather than with
  the four passes.
* **`R8a-5`, letting success read as the board row met** — answered in the negative, in as many
  words.

### The questions this gate must be able to answer

The plan's `R8` interview row asks five. `R8a` answers two and a half of them; the other two are
`R8b`'s and nothing here touches them.

**① 「rollback counter 存在哪？NOR 不能改寫怎麼遞增？」** A 512-byte unary bitmap, 4,096 bits, at flash
offset `0x3F0000`, read through the MMIO window and **read-only** in this gate. The counter is the
number of zero bits from the start, MSB first; an erased NOR byte is `0xFF`, so a factory-erased
region reads 0 and an install clears one bit, which needs no erase. A zero bit after the first one
bit is malformed and resolves **upward**, to the total zero count, because of the two ways to be
wrong a counter too high refuses updates and a counter too low accepts a rollback. `version ==
counter` is accepted and `version < counter` refused, because refusing equality would stop a device
re-installing the image it is running and would require the counter to advance on a boot rather than
on an install (`notes/rlxboot.md` § 4). What the answer does not cover: nothing here advanced it.

**② 「那攻擊者只要弄壞 `0x010000` 就能繞過你的驗簽？」** No, and the reason is that a slot image
deliberately carries no header the stock loader recognises — two independent readings, one from a
tool that is not this gate's (claim ③) — together with an **erased** barrier at
`0x030000`–`0x06FFFF`, so that no slot contains one of the loader's six scan candidates. An erased
NOR word reads `0xFFFFFFFF`, which is neither `cs6c` nor `cr6c`, so the barrier is provably
unbootable rather than merely unlikely to boot. ⚠️ That is a reading of `check_image()`'s acceptance
rule and not a measurement, and its one unread input is `check_image()`'s `bank_offset`, which plan
§ D5 records as never having been read for this build: if it is not 0 the candidate table shifts and
the barrier moves with it.

**③ 「你的 `rlxboot` 壞了會怎樣？」** Half answered. The plan's answer is that the stock loader keeps
scanning to `0x020000`, where a read-only, signature-verifying recovery `rlxboot` sits. The region is
in the layout and `flashguard` refuses every write to it — and **the rescue payload is not built**
(讀: `src/rlxboot/Makefile` has no rescue target). So what exists today is a reserved region and a
refusal, not a fallback that has ever run.

**④ 「寫到一半斷電會怎樣？」and ⑤ 「只有一台機器你敢寫 flash？」** Not answered, and not attempted.
Both are `R8b`'s, the first because the interrupted write **is** the experiment and the second
because its answer is the rescue drill, which has not been done.

### What `R8a` did not establish

🔴 **That an image can be written to flash.** Nothing in `R8a` writes one byte. `flashguard` refuses
destinations and does not write the ones it permits; `flashscan` is the check on the payload's own
instruction stream; and the whole demonstration is a container staged in RAM by the loader's TFTP and
entered with `J`.

🔴 **That a power cut during a write is survivable.** That is `R8b`'s pass criterion ④, ten physical
power pulls, and the interrupted write is the experiment. Nothing here bounds what an interrupted
write leaves behind.

🔴 **That the anti-rollback counter advances.** Nothing in `R8a` writes it. The flash bitmap is
erased today, so it reads 0 and every version passes, and rounds 3 and 4 drove the comparison from a
**RAM** bitmap at `0x81700000`. The boundary cases — version 5 against counter 4, 5 and 6 — are
`C13`'s, against a command-supplied counter (`notes/update-chain.md` § 7). So the monotonicity the
design rests on is asserted and never exercised.

🔴 **That the key management is production-grade.** The development seed is 32 bytes of `0x42` and it
is **in the tree on purpose**: anyone who reads `src/rlxboot/devkey.h` or
`tools/fixtures/mkfw2/dev-key.tsv` can sign a container this build accepts. It exists so that two
independently written implementations can be compared without exchanging a key. What `R8b` needs
instead is a key that never enters this repository and never enters `$FWRE_WORK`, which is shared
with another checkout, with only the public half built into `rlxboot`; rotation is a rebuild,
because this format carries no key list and no revocation.

🔴 **That `rlxboot` resists an attacker who can already write flash.** Plan § D6 says outright that
it cannot. It defends the remote update path, not physical access, and the erased barrier is a
defence against *corruption* reaching a bootable header, not against someone who chooses those
bytes.

🔴 **That this hardware has secure boot, and nothing here may imply it does.** There is **no**
evidence of an OTP or an eFuse for a public-key hash on this part. The stock loader still runs first,
unverified, and can still be replaced by anyone with flash write access; `rlxboot` is a second stage
that verifies what it is handed, which is a different claim.

🔴 **That the `R8` board row is met.** `R8a` is the half of it that needs no flash write. The row
stays open until `R8b` runs, and the booking below prices what that costs.

⚠️ **The cache argument is 量 for a composite path and for nothing narrower.** Rounds 1 and 4 write
back D with `CCTL 0x200`, invalidate I with `0x002`, copy 1,114,112 bytes and jump in, and the
payload boots — so that sequence works on this die for this copy. It does not show `0x200` was
necessary: the D side is write-back **without** write-allocate, a store to a non-resident line goes
straight to memory, and `notes/cache-model.md` records `0x100` `DWB` as a value whose effect no
source documents. The destination was never read back, and `notes/rlxboot.md` § 6's own refutation
condition is only half taken.

⚠️ **That the flash window is decoded at `0xBD3F0000`.** The weakest-thing paragraph. `ctr=0` from
flash is the reading an erased region and an undecoded window share.

⚠️ **That `rlxboot` works anywhere but on this build, this image and these four rounds.** One
seating, one build id `6395889d`, one payload sha256, one container, one `load_addr`. Everything
else is qemu, and **qemu certifies logic and never codegen or the ISA**.

⚠️ **That the timing is bounded.** Ed25519 over 96 bytes and SHA-256 over 3 MiB have been timed on
nothing that resembles this core, and the four rounds' durations were not taken as a measurement of
either.

⚠️ **What pinning the container at `0x81000000` costs.** It is the one address in RAM this project has
measured being rewritten: `MEM-14` puts `0x00000144` into word 1 on every boot, which is a
container's `format` and `header_len`, so a reset between the upload and the jump corrupts the
container into a header refusal. The four rounds read that word and it was intact four times of four
— which is a check that the hazard did not fire, not a demonstration that it cannot.

⚠️ **`rlxboot-rescue` is a region and a refusal, not a payload.** It is not built, has never run, and
the half of question ③ that depends on it is unanswered.

⚠️ **rlxfw's own flash image would not pass the stock loader today, and that was never the claim
anyone checked.** 量 `cvimg` writes `cr6b` and `check_image()` accepts only `cs6c` and `cr6c`
(`FW-168`). It does not touch `R8a`, which boots from RAM, and it decides `R8b`: `rlxboot` and the
rescue **must** carry a `cr6c` header, because being scanned is how they run at all, and a slot must
deliberately **not** — two opposite properties at one producer's output, each needing its own
control. It also records that `R8`'s old *"the stock loader will accept my image"* has never been
verified in this repository.

⚠️ **The layout is arithmetic, not a measurement.** It is computed from `SPEC.md`'s `FLM-*` rows and
the scan table in `docs/loader-command-semantics.md` § a, and `bank_offset` is its one unread input.

⚠️ **`flashscan`'s census is a check on one program, not a proof about programs.** The
reconstruction is per-register and forgets a register written by anything it does not model, which
its own text says.

⚠️ **The MTD refusal's third layer has still never been observed firing**, here or anywhere in this
project: observing `MTD_CAP_ROM` at `mtd_open` needs an even char minor over this device, which
`tools/mkinitramfs.py` refuses to declare. It stays 讀.

⚠️ **The seating's own bookkeeping cannot be re-derived from the repository.** `FW-170` counts the
rounds at 49 cells and breaks them down as 4 `rescue`, 10 TFTP and 31 console captures, which sums
to 45; what is committed under `bench/2026-09-30/R8A-*` is 26 console captures with their `.timing`
and `.meta.json`, ten `*-rescue.json` upload records and four reads of the `AUTOBURN` word, and the
script that counted the rest is outside this repository. The seating was shared with `R7-8`, whose
captures are not in this gate's commits.

⚠️ **Flash.** 量, per round: the four rounds sent 26 console commands in all — six `DW`/`J` a round
and two `busybox reboot -f` — and ten uploads, whose console preparation was `AUTOBURN 0`,
`LOADADDR` and `IPCONFIG`. No `FLW`, `EW`, `EB`, `DB` or `FLR`, and no non-zero `AUTOBURN`, appears
in any capture or upload record of the gate; the `AUTOBURN` word read `00000000` four times, once
per round. What that cannot see: two writes that cancel, every byte outside the words read, and
`H601`, which is never hashed. **No flash map was taken in these rounds**, so there is no bracket of
their own to compare against the 2026-08-16 dump; `n_writes` was not read either, and it carries no
information (`FW-142`). The `FLR` bracket stays at 1,024 of 4,194,304 bytes = **0.0244 %**, and
`FLS-26`'s ledger does not move. The one flash access the gate made is a **read**: `rlxboot`'s
read-only counter read through the MMIO window in rounds 1 and 2.

### `R8b`: the booking, and its preconditions priced from what is now known

`R8b` is **booked and not open**. It is persistence and the ten power cuts, and it waits for `R9`,
for the preconditions below, and for the owner's own dated yes — one per write (`CLAUDE.md`
§ Flash). Every line here is priced against the tree as it is at this close, not against the plan's
expectation of it.

| the plan's precondition | where it stands |
|---|---|
| **①** the rescue drill done: `0x3F0000` deliberately written to garbage, a TFTP rescue walked, timed, and written into the runsheet | 🔴 **not done, and it is itself a flash write.** Nothing in `R8a` wrote a byte, so nothing recovered from a broken one. Plan § D6 splits the drill in two, and the half that drills *a slot is broken and `rlxboot` recovers it* needs the rescue payload, which is not built. So the precondition that licenses the later writes needs a dated yes of its own before it can license anything |
| **②** `burn()` at `0x80401318`'s flash target read out | 🟢 **met at the desk, before this gate** (`docs/loader-flash-write.md` § 1): `burn()` is the image parser and dispatcher, matching eight section signatures, bounded at the top against the chip capacity and with **no lower bound** at all. ⚠️ `C-3`'s residual stands — which of `burn()`'s four callees erases and which programs — and the capacity bound is correct for this device only by coincidence, this unit taking the unknown-chip fallback |
| **③** `mkfw2` refuses a container whose destination lands in a forbidden range, **with a positive control** | ⚠️ **half.** The guard and its positive controls exist and are `R8a`'s (claim ③). The missing half is that a destination is an **optional declaration**: `--flash-at` defaults to none and the container carries no destination field, so a container built without it is emitted unguarded. `R8b`'s producer has to make the destination part of what it signs, or precondition ③ is a check that can be skipped by omission |
| **④** the main write path is rlxfw's own MTD driver, the loader's `AUTOBURN` demoted to a fallback | 🔴 **there is no write path, and the gate this precondition names never existed.** Three layers refuse today: the designated write path `rtl819x-spi-write.c` is a separate translation unit whose `obj-$(CONFIG_MTD_RTL819X_WRITE)` names a `CONFIG_` kconfig never declares, so it is not compiled and its two entry points return `-EPERM`; `mtd->write` and `mtd->erase` in the compiled unit are stubs that refuse with `-EOPNOTSUPP` and count; and `mtd->flags` is `MTD_CAP_ROM`, so `mtdchar` refuses an open for writing before those stubs are consulted. The precondition names `R5b` as the owner and `R5b` was struck as a gate that never entered the board (`C-3`'s owner cell), so the body has no gate but `R8b`. ⚠️ And the accurate sentence is the driver's own: **rlxfw contributes no flash-write code to this image** — not that this image cannot write flash. The vendor's `mtd_spi_write` and `mtd_spi_erase` are installed unconditionally and reach real page-program and sector-erase sequences; what keeps them out of reach is the userspace surface, an odd char minor and a `0400` block node, which are access controls on a path that exists |
| **⑤** stage 2 confirmed: with the kernel region garbage the ESC window still appears | ⚠️ **read, not measured.** `doBooting()`'s else branch goes straight to `goToDownMode()` with no ESC wait — a bad image takes you to the rescue path immediately rather than costing it — and this unit's `stage2.bin` carries the strings (`docs/loader-flash-write.md` § 3). `C-4`'s residual is still a bench item: that a deliberately corrupted image reaches the prompt **in practice**, kernel region only |

**The layout is settled and it is constrained, and the constraint is not capacity.** 讀 (`FW-167`,
`notes/update-chain.md` § 6): today's image wrapped in a container is 1,114,272 bytes, which rounds
up to `0x120000` = 1,179,648 on the loader's own 64 KiB step, and two full slots fit with 1,310,720
bytes free. The binding limit is the stock loader's **scan table**: at the obvious base `0x030000`,
four of its six candidates fall inside slot A, so the lowest usable slot base is `0x070000` and
`0x030000`–`0x06FFFF` is left erased as a provably unbootable barrier. `rlxboot` at `0x010000` and
the rescue at `0x020000` are the only two regions the stock loader can reach and must each carry a
`cr6c` header on purpose; slots A and B are reachable only through `rlxboot`, which is the whole
design.

**Slot A's first write ends the vendor firmware, and that is why the order is a constraint rather
than a preference.** 讀 the arithmetic: slot A spans `0x070000`–`0x18FFFF` and the vendor kernel
`cr6c` spans `0x060000`–`0x151012`, 987,155 bytes, so the first write to slot A destroys **921,619
of those 987,155 bytes** — everything but the one 65,536-byte sector below the slot base — plus
65,536 bytes of the SquashFS. `cr6c`'s 16-bit sum stops being zero, `check_image()` stops returning
2, and the loader has nothing left to boot from flash. Slot B takes another 1,179,648 bytes of the
SquashFS, leaving 630,850 of its 1,876,034 under no kernel. That boot **is** `R9`'s vendor column:
`R9` is this project's acceptance gate and its method is *vendor firmware = boots normally, rlxfw =
RAM boot, and switching between them is one power cycle*, so every vendor-column measurement depends
on the vendor firmware still booting from this chip. TOTOLINK released no source, so there is no
second copy to build. **Therefore `R9` before `R8b` is a constraint, not a preference.** ⚠️ The
honest qualification is that the bytes are not unrecoverable in principle — the 2026-08-16 dump is
outside this repository — but restoring 3.3 MiB means exactly the writes nine gates have avoided,
through a `burn()` with no lower bound, on one device with no spare, and a restore that stops
partway leaves neither firmware. *"Gone"* is the right word to plan with.

**What `R8b`'s own pass criterion needs, beyond the preconditions.** Criterion ④ is ten physical
power pulls during a write, each followed by a boot from the other slot, and its refutation is
written: any one that enters no slot means the A/B design has a hole. That criterion is what makes
the two-slot layout load-bearing — the single-slot alternative is recorded, and with one slot the ten
cuts would test `rlxboot-rescue` plus a TFTP upload rather than A/B at all. Beside it, `R8b` must
make one producer guarantee two opposite properties, a `cr6c` header where the loader must scan and
no recognisable header where it must not, each with its own control (`FW-168`).

### The main session's rulings in this gate, which the owner may override

The owner's own — opening `R7` and `R8a` on 2026-09-30, splitting the `R8` board row at the flash
boundary, and the widened relaxation of no frozen cards and predictions only where they earn it,
with the flash rules, the power handshake and `NET-165` unchanged — are not listed. Each below is
recorded where it is cited.

1. `version == counter` accepted rather than refused, with the recovery argument that refusing it
   would require the counter to advance on a boot (`notes/rlxboot.md` § 4).
2. A malformed bitmap resolved **upward**, to the total zero count (`notes/rlxboot.md` § 4).
3. Ed25519 and SHA-512 imported rather than written, and SHA-256 written rather than imported, on
   the two halves of one argument about refutability (`notes/rlxboot.md` § 5).
4. `crypto_sign_open` replaced rather than called, and `s < L` tested in rlxfw's wrapper
   (`notes/rlxboot.md` § 5).
5. One warning exemption, `-Wno-sign-compare`, on one imported file, rather than editing imported
   crypto (`notes/rlxboot.md` § 5).
6. RFC 8032 § 7.1's TEST 1024 left out of `rlxsign`'s table, with OpenSSL's four cases in its place
   and a skip line that says what is then unchecked (`notes/update-chain.md` § 3).
7. Four bounds added to the pinned format — `payload_len == 0`, word alignment, and the stage-2
   window as a refused destination — and listed as additions (`notes/rlxboot.md` § 3).
8. `RLXBOOT_REFUSE_RESET` left at 1, so a refusal resets rather than halts, which is why rounds 2
   and 3 end at the loader prompt through a watchdog bite.
9. Pass condition ③ driven from the RAM counter rather than from flash, because the flash source
   cannot distinguish an erased region from an undecoded window (`FW-170`, `notes/rlxboot.md` § 10).
10. `FW-169` recorded and not fixed, under the owner's rule of 2026-09-26 that a new or changed
    checker must block bricking, an `H601` leak or a misjudged result.
11. `check_image()`'s desk reproduction taken from `tools/rtkimage.py` rather than from
    `upstream/tools/loader-unpack.py`, which two documents wrongly credit with it
    (`notes/update-chain.md` § 5).

---

## 2026-09-30 — `R7` (my userspace running on the silicon, and a pass condition that had to be re-specified because both of its named sources read 0 by construction)

### One line

**v0.5+, one segment (the 118th, shared with `R8a`), two boots and no power action.** § Gate board
costs `R7` at 34 segments, the plan's own cost table at 40 and its prose at 38; the actual is **1**,
and that ratio measures the scope that was cut and the parallelism of one segment, not the
difficulty (below). Six programs of rlxfw's own — `init` as a compiled PID 1, `cfgstore`, `brokerd`,
`httpd`, `dnsfwd`, `ifupd` — plus busybox rebuilt from the drop's 1.13.4 with an applet set chosen
as a security decision, booted from RAM and answered questions put to them on the die: `httpd` as
uid 100 in a chroot, `dnsfwd` as uid 101 printing `setuid(0) refused (Operation not permitted)`,
`brokerd` as root behind a unix socket, the config store written with its slots alternating, and a
login costing 0.902 s for the right password and 0.9017 s for the wrong one (`FW-175`, `FW-181`).
**The gate's pass condition had to be re-specified before any of that could count**: the two
independent sources named on 2026-08-25 both return 0 on a statically linked binary by
construction, and 0 was the passing answer (claim ①). Ten steps of ten closed, the tenth being this
entry. Two uploads, no `FLW`, `EW`, `EB` or non-zero `AUTOBURN`, and both returns to the loader were
`busybox reboot -f`.

**The weakest thing here is that the readings which settle three of this gate's claims cannot be
re-derived from a file, and one of its instruments prints the same text for two different states.**
Two readings of the first boot — the `POST /api/login` reply and the `dnsfwd` reply — were printed
to a terminal by a script that does not save them, and a search for their text over
`bench/2026-09-30/` and `$FWRE_WORK/rebuild/s118/` finds only that script: they are 量 by the
session that ran them and nothing else (`notes/userspace-integration.md` § 7). Repeating the login
one needs a fresh boot, because a password was set later in that one. And `cfgstore show` printed
`bytes 0` for a file that was **absent**, not empty — 量 the earlier `ls` read `No such file or
directory` — so that instrument cannot tell ENOENT from a zero-length store, which is exactly why
its output alone is not the evidence (`FW-181`; `notes/userspace-integration.md` § 7.4). Beside
those, `$FWRE_WORK` holds the interface specification every program was written against
(`SPEC-R7.md`, `SPEC-R7-8.md`), all four fuzz pre-registrations, and the replay that cleared `rl.c`.

### Three claims that stand

**① The pass condition was an instrument that could not fail, and it was replaced before anything
was measured against it — with a tool that refuses rather than reporting 0, and with the vendor
baseline corrected in the same pass.** 讀 and 量 (`FW-20`, `FW-22`, `FW-174`, `FW-177`;
`notes/rootfs-census.md`). § Gate board's row named two sources — the shipped artefact walked
through `PT_DYNAMIC`/`DT_SYMTAB`, and `nm --undefined-only` over the build products before strip —
and rlxfw's own programs are **static**: a `PT_DYNAMIC` walk finds no such segment, and `system` is
*defined* rather than undefined in a static link. Each therefore reads 0 on every rlxfw binary
whatever the code does, **and 0 is the passing answer**. That is this repository's own `R-28` class,
*an acceptance tool that cannot fail on the file format it must check*, reappearing one level below
where it was first caught — and the sharper reading is that `R-28`'s own countermeasure, *two
sources of different kind, shipped artefact against build product, each with controls*, is the
wording that turned out vacuous. 🟢 `tools/uspacescan.py` replaces both: source ① over the shipped
bytes is a dynamic import walk, then `.symtab`, then a **relocation-masked code fingerprint** of the
libc member that defines the name, which survives `strip`; source ② reads every `*.o` that went into
the program with the tool's own ELF reader and counts `SHN_UNDEF` GLOBAL or WEAK, cross-read against
`mips-linux-nm -u` where a disagreement is a failure and not a vote. **A stripped ELF with no
`PT_DYNAMIC` and no fingerprint source is refused, not passed**; a name with no implementation in
the archive is `UNDECIDED (NOFP)` and never 0, with `wordexp` carried as a permanent control row so
that every run demonstrates it; and a fingerprint leaving fewer than eight distinct unmasked words
is refused as undecided, the threshold chosen with 3 on one side (a `vfork` thunk that matched five
unrelated thunks in `iperf3`) and 19 on the other. 量 `--self-test` 30 controls, 0 failed, 0 skipped,
with a planted `system()` found **both before and after** `mips-linux-strip`, and
`tools/test-uspacescan.sh` 70 of 70. Over the shipped image: six programs, both sources, **0
forbidden names, rc 0**, the allowed calls counted (`execve` two, `fork` three), `execle` exempt by
name with the exemption's control firing — the same ELF under the default name table gives
`rc 1 FINDING` — and `uprobe`/`ucost`/`iperf3`/`linkprobe` reported `UNPAIRED` rather than as
agreeing, because no objects were kept. 🟢 **The two sources disagreed once and it produced a finding
rather than a vote**: over all 199 of busybox's compiled objects they differed on `execvp`, and the
cause is `libbb_vfork_daemon_rexec.o`, compiled but **not linked** (讀 `busybox_unstripped.map`, 199
of 100), which source ① said by the same fingerprint method. 🟢 **The vendor baseline was corrected,
and the correction is that the published method could have missed the very symbol this gate is
about.** 161 files, 55 ELFs, 3 of them static; 31 of 55 by whole-string scan and 28 of 55 by import
walk, the gap exactly three files each with its own reason. A string table **tail-merges**: 量 over
the 52 dynamic ELFs, 3,752 (file, import) pairs of which the scan sees 3,435 and **misses 317 across
61 distinct names**, and `system` is one of the missed names — libc stores `__libc_system` and its
`system` entry points 7 bytes into that run, so no `system` run exists in it and **libc is in the 31
only because it matched `popen`**. `readelf --dyn-syms` is empty on **54 of 55, not on all 55**: 量
`bin/acltd` keeps its section headers (`e_shoff 0x2348`, `e_shnum 25`, the tree's only `SHT_DYNSYM`
section header) and host `readelf` 2.42 prints its 51 entries, 29 of them `SHN_UNDEF` — which makes
that instrument **worse** and not better, because its one non-empty answer out of 55 is exactly what
would make the other 54 zeros look earned. And `daemon` was never busybox's import: 量 the run sits
at file offset `0x3f768` while that file's `.dynstr` is `0x1ba8`–`0x2460` and no `.dynsym` entry of
the name exists; it is `bin/udhcpd`'s import, **the row directly below in the same table**, and
nothing in this repository can see a value that moved between two adjacent rows — `spec-check` and
`citecheck` read ids, citations and structure, and a plausible name in the wrong row is structurally
valid (`FW-174`). ⚠️ What this does not reach: **reachability is undecidable on this ABI and the tool
says so instead of pretending.** The rsdk gcc compiles abicalls PIC (`e_flags 0x1007` on
`linkprobe` and `iperf3`, `0x1005` on `uprobe`/`ucost`), so a libc call is
`lw $t9,%got(f)($gp); jalr $t9` and there is no `jal` to it anywhere; the tool therefore prints the
count of register-indirect transfers in `.text` and reports `reach=INDIRECT` rather than running a
BFS that would return undecided on every real input. What it decides is **presence**, which
over-reports. ⚠️ An inlined or open-coded `execve("/bin/sh", …)` is not this libc's `system` and is
invisible to all three methods, so `R7`'s ban on `sh -c` is not established by this tool. ⚠️ Neither
vendor number is a bound by construction: 31 over-counts three files, 28 is a count over 52 and says
nothing about the other three, one of which (`bin/updatedd`) carries a whole-run `system` string, so
the rootfs figure is *28 confirmed, ≤ 29* (`notes/dnsfwd.md` § 10).

**② rlxfw's own userspace runs on the die, the privilege separation is verified by trying to undo
it, and the KDF has a device number for the first time.** 量 two boots, 2026-09-30, no power action
(`FW-175`, `FW-176`, `FW-179`, `FW-181`; `bench/2026-09-30/R78-*` and `R79-*`;
`notes/userspace-integration.md` § 7). Boot 1 is image `r78a`, `RLXFW-ID0=BF182DE2`, which is § 6's
recipe id `bf182de2` in `notes/userspace-integration.md` § 6; boot 2 is the rebuilt image,
`RLXFW-ID0=0E45C61D`; both entered with
`J 80500000` after the staged head at `0x80500000` was read back. `ps`: PID 1 is `/init`, `brokerd`
root, **`httpd`'s USER column is `httpd`**, **`dnsfwd`'s is `dnsfwd`**, `udhcpd` root, `sh` root, and
all three `/etc/passwd` rows carry `/bin/false`. 🟢 **The drop is verified by reversing it, not by
announcing it**: `dnsfwd: running as uid 101 gid 101; setuid(0) refused (Operation not permitted)`.
Beside it `httpd: uid=100 gid=100 root=/srv/www sock=/run/broker.sock port=80 conn=8`,
`brokerd: listening on /srv/www/run/broker.sock mode 0666`, `rlxfw: lan up, rlx0 10.1.1.1/24`, and
two loud `*** BENCH PROFILE: A ROOT SHELL IS ENABLED ON /dev/console ***` lines. The four daemons
each answered: `cfgstore show` listed sixteen keys at `source default`, `seq 0` with both slots
invalid, `set sys.hostname=rlxfw-bench` gave `written: slot 0, seq 1` and `cfgstore passwd` gave
`written: slot 1, seq 2`, so **the A/B alternation is only visible on the second write**, with
`/var/lib/cfg.bin` at 8,192 bytes, mode 0600, owner root; `GET /` answered 200 in 3,850 bytes and
`/api/status` 200 with `{"ok":true,…,"auth_ready":true}` and all four security headers
(`X-Frame-Options: DENY`, `Content-Security-Policy: default-src 'self'`,
`X-Content-Type-Options: nosniff`, and `Cache-Control: no-store` on `/api/*`), through the whole
chain host → `httpd` (uid 100, chrooted) → unix socket → `brokerd` (root) → typed op; `dnsfwd`
returned 29 bytes with id `0x1234` echoed and rcode 2, neither hanging nor crashing; and `ifupd`,
which `D14` would otherwise have had no reading for at all because `wan.mode` is 0 and `udhcpc`
never execs it, applied one hand-fed lease (`bound ok reason=ok`, rc 0, `/run/wan.dns` written, the
interface really at `inet addr:10.9.9.9 … Mask:255.255.255.0`) and refused two malformed ones **by
name** (`REFUSED reason=bad-ip detail=octet-over-255` and `REFUSED reason=no-interface`, both rc 2).
🟢 **The entropy driver's criteria were registered before the run and all of them were met, while
its ceiling fired.** `notes/entropy.md` § 5.2: pass = `ev_nic` rises, `qualifying` > 0, `bits` > 0
and `entropy_avail == bits`; refutation = `ev_nic` rises while `qualifying` stays 0, or `bits` > 0
while `entropy_avail` stays 0; void = `ev_nic` does not rise. 量 at boot `ev_nic 0 qualifying 0
bits 0` and `entropy_avail 0`; after 1,000 echoes (188 received) `ev_nic 1193 qualifying 1151
bits 71` with `entropy_avail` **71 — the two accountings exactly equal**; after a 4,000-echo flood
(4,000 of 4,000 received) `ev_nic 9194 qualifying 9125 bits 403` and **`clamped 2665`**, so the
one-bit-per-jiffy ceiling fired 2,665 times and 9,125 qualifying events bought 403 bits, which is
what the design asks for. The control is the unchanged `r6b8i` image, on which `entropy_avail` read
0 at 768 s, 1,613 s, 3,289 s and 3,437 s across 400 round-tripping echoes and ~7,700 serial
interrupts (`FW-160`) — and **that control's first round failed and the failure is itself a
reading**: the host pinged 10.1.1.1 while `rlx0` was 10.1.1.3/255.0.0.0, so 300 echoes arrived only
as broadcast ARP, IRQ 12 moved by 15, and the round does not count. 🟢 **The KDF's cost is 量 for the
first time and it refutes the estimate that stood in for it**: `log2N=12 r=7 p=1` takes **0.902 s**
(0.902410 s and 0.902122 s for the correct password, answered HTTP 200 with a csrf and `ttl_s 900`;
0.901743 s for a wrong one, answered 401) — the same time either way, so the timing does not say
which it was. The pre-run figure derived from qemu was ~0.3 s with a **declared** interval of
0.15–0.8 s: three times low and outside its own interval, on an emulator that had already
disqualified itself by ranking `(12,8,1)` faster than `(12,7,1)`. ⚠️ What this does not reach: **no
refusal was returned on the board.** The only peers in these captures are `httpd` and `dnsfwd`, both
in the authorisation table, so the refusal half — a uid outside {0, 100, 101}, or uid 101 attempting
a `SET` — rests on the host's 264-cell matrix and nothing else. ⚠️ The lease was **synthetic**:
`10.9.9.9`, `10.9.9.1` and `10.9.9.53` were invented at the desk, no DHCP server issued them, and
`udhcpc` has never run on this board. ⚠️ Why `dnsfwd` answered SERVFAIL is 推 — the configured
upstream is this host and nothing was read from the board's side to show no resolver is there — and
the reply bytes were not saved.

**③ The device found two defects no host suite could, and the way the first one was cleared is worth
more than the fix.** 量 (`FW-182`, `FW-183`, `FW-184`; `docs/KNOWN-ISSUES.md`; `notes/httpd.md`
§ 11). `POST /api/login` answered `429 {"ok":false,"error":"ratelimit","retry_s":2}` and **did not
recover** — refused at 640 s, 660 s and 832 s of uptime with 20 s and then 90 s of complete quiet in
between, while `GET /api/status` answered 200 in the same minute, so `httpd` was alive, forking and
serving and only the login path was shut. 🟢 **`rl.c` was exonerated before it was suspected, and by
a sweep rather than by reading it**: replaying the device's own timeline through it with an injected
clock **grants** at +20 s and at +90 s, and a sweep of **2,709,903** reachable
`(tokens_milli, last_ms)` pairs per bucket found **0** that refuse after a 90 s gap; an empty global
login bucket names `retry_s` 5 and an empty per-address bucket 11, and the value 2 is reachable only
within 250 (respectively 100) milli-tokens of granting, a state that grants within 2 s; `now_ms()`
is `clock_gettime(CLOCK_MONOTONIC)` in milliseconds and not `times()`, so this kernel's
`INITIAL_JIFFIES = -300*HZ` never reaches it and 640–830 s is nowhere near the 49.7-day wrap. The
mechanism, reproduced on the host as a failing unit test before anything was changed: `srv_loop()`
kept the holder of the single KDF grant in **two** places, `kids[i].holds` and a local
`int kdf_inflight`; the decision read the local, `reap()` clears only `holds`, runs at the **top** of
the loop and closes `kids[i].fd`, discarding the release byte and the EOF that were the only two
paths clearing the local. The literal `retry = 2` in that branch is the constant `retry_s`, and the
refusal happens **before either bucket is consulted**, which is why 90 s of idle changed nothing.
🟡 It is a **race and not a deadlock**: one 401 got through at 05:29, immediately followed by eight
consecutive 429s and a ninth after 15 s of quiet. 🔴 **So the honest headline is not "the tested
implementation and the deployed implementation were different code"** — `test_rl.c` did cover the
deployed bucket and was right — but **duplicated state with only one copy maintained, in the one
function no unit test could call**, because entering it needs `fork()`, `accept()` and a listening
socket; the repair makes that function testable by extracting the arbitration behind
`srv_kdf_reset`/`ask`/`gone`, so a test drives the decision that ships — nineteen cases added to
`test_serve.c`, three of them controls, one of which refuses a holder that is **still alive** ten
minutes later. 🟢 **Fixed and proven on the device against a discriminator registered
first**: a leaked grant refuses with the *constant* `retry_s` 2 before either bucket is consulted and
never recovers, while a legitimate bucket refusal names a truthful wait and clears. 量 twelve
consecutive logins — 1 to 3 HTTP 200 at 0.912/0.909/0.911 s, the burst of three the design allows,
then 4 to 12 refused with **`retry_s` 9**, a real bucket figure, then HTTP 200 again at 0.909 s after
15 s of quiet. 🔴 **The recipe id is not the evidence**: `RECIPE_ID` digests `config/` only and
`config/` changed for an unrelated reason; the evidence is that the new stripped `httpd` appears
verbatim inside `vmlinux_img` and the old one does not, with the control run both ways. The fix cost
232 bytes stripped (83,604 → 83,836, +0.28 %) and `hazlint` stayed at 0 violations over 3,740 loads.
🔴 **The second defect is open, and its consequence must be said plainly: a password set on this
image does nothing until `brokerd` restarts.** `cfgstore passwd` succeeded (`written: slot 1,
seq 2`; `admin.pwhash set: scrypt log2N=12 r=7 p=1, entropy_avail was 150`), `cfgstore get
admin.pwhash` reads `set` and `/api/status` reports `auth_ready:true` — yet the **correct** password
was answered `401 {"ok":false,"error":"auth"}` in **14 ms**, and 14 ms means no KDF ran, which is
what `brokerd` answers when it believes no password is set. Confirmed by an experiment rather than by
reading the code: `busybox kill 12 13` let `init` respawn both (`brokerd exited exit=0` → pid 81,
`httpd exited signal=15` → pid 82) and the same password then returned HTTP 200. It fails **closed**,
which is the right direction, and it is recorded and not fixed (`FW-184`). ⚠️ What this does not
reach: nothing here says these were the only two differences between the host and the silicon — they
are the two that were measured. ⚠️ The exact trigger of the grant leak on the device is 未定: any
child that exited holding the grant produces it, and the captures do not say which one did. ⚠️
Nothing covers the socketpair — not the five-byte encoding, not `select()`'s ordering against
`SIGCHLD`, not a child that neither releases nor closes; all three are read out of the source.

### The steps' DoD, read one row at a time

`R7` has no `D`-row table in this repository — `R7-8`'s DoD cites `D14`, which lives in `plan/` and
is gitignored — so the step list's DoD column is what is read. Ten steps; nine closed and `R7-9` is
this entry.

| the DoD says | verdict |
|---|---|
| **`R7-0`** a fixture that really calls `system()` is caught by both sources; an `execve` fixture is permitted **and** counted; a name that exists nowhere reads 0; the two sources disagreeing is an error, not a vote; a mutated tool exits non-zero | 🟢 **met** (claim ①; `FW-177`). The planted `system()` is caught either side of `strip`, `--self-test` is 30 of 30 with 0 skipped, and `tools/test-uspacescan.sh` is 70 of 70. ⚠️ The row asks for a stripped file to be the case that matters and it is, but the method that answers it needs a `libc` to fingerprint against: without one the tool **refuses**, which is the intended behaviour and also means the reading depends on a toolchain artefact that is not in this repository |
| **`R7-1`** `busybox --list` 量 under qemu, not read off the config; no enabled applet's source calls `system`/`popen`/`execl*`, shown by scanning the built binary; `hazlint` 0; the list of commands the current image has and this build drops | 🟢 **met, with the row's instrument replaced by a better one.** The enumeration is **53 applet names and 43 ash builtins**, 量 two ways sharing no code — running the binary under `qemu-mips-static` and reading its *Currently defined functions* block, and `tools/appletcensus.py extract` parsing the applet-name table out of the ELF without executing anything — which agree exactly; `--list` is not what was used, and the applet table is read out of the built ELF and never out of a `.config`. Against `config/image-commands.tsv`'s 50 rows: **9 dropped, 12 added**, and the builtin table is a strict superset (43 against 40). `hazlint` 0 violations in 26,072 loads (`notes/busybox-build.md` § 2, § 5, § 6). ⚠️ The forbidden-import gate `G6` reads the **unstripped** link's symbol table; what transfers the claim to the shipped file is that both have the same 403,708-byte `.text` with the same sha256 |
| **`R7-2`** mounts, LAN up by `ioctl`, daemons supervised with a backoff and a crash-loop stop; every child `fork`+`execve` with a fixed `argv`; the DHCP lease environment treated as hostile, with a malformed battery; the bench shell enabled **and announced** | 🟢 **met** (`notes/init.md` §§ 2–7). Backoff 250 ms doubling to 16,000 ms, eight consecutive fast failures then `SV_GIVENUP`, about 32 s of trying; every child is `fork` + `execve` with an argv of string literals and a three-entry environment, and **not one argv byte comes from the config store, a lease or the command line**; `ifupd` reads five environment names and nothing else, every read length-bounded before the value is examined, everything surviving is a `uint32_t`, and the battery is **43 rows — 26 refusing, 5 partial, 12 applied — asserting `n_ioctl == 0` on every one of the 26**, with 13 named refusals and 8 named partials. The shell is announced by two `***` lines. ⚠️ `SIOCADDRT` has never been issued on this board by anything, so whether the netdev accepts a default route is 未定 |
| **`R7-3`** the torn-write sweep as a loop over **every** truncation length, each leaving the previous record selected; a bit-flip sweep over the header; both slots invalid → defaults with `source = 0`; the mutation with the length check removed goes red | 🟢 **met, and the row's first clause was refuted as worded and replaced by a stronger invariant** (`notes/config-store.md` §§ 4–6, § 8). *Every truncation leaves record N selected* is not satisfiable and the reason is the format: the record is 131 bytes and the other 3,965 of the slot are fill the parser never reads, so a write that reached byte 131 wrote the whole record and selecting it is **correct**. What was measured instead is that the load is byte-identical to N or to N+1, never a mixture: **8,194 cases** = 2 backgrounds × 4,097 lengths, 262 selecting N, 7,932 selecting a complete N+1 with `L ≥ 131`, and **0** mixtures, partials or fallbacks — with `L = 4096` as the positive control, without which *always N* could be true because N+1 is unselectable. Bit-flips: 1,048 in the extent all rejected, and **512 flips in the `0xFF` fill all accepted with every value identical**, which is what separates this parser from one that rejects everything. Both slots invalid gives defaults with `source == 0`, and `admin.pwhash` has no default, so no password means no login. `M1` (bound removed) 1,742 failures, `M2` (off by one) 38, with `M0` passing first as the precondition |
| **`R7-4`** the decoder sweep over every header offset and truncation; the authorisation matrix per (op × uid × session × CSRF); the lock's doubling **and** a correct password succeeding after it expires; `NOENTROPY` before the pool is ready | 🟢 **met** (`notes/broker.md` §§ 1–9). Decoder sweep **124,975 cases** = 122,400 single-byte header corruptions (10 frames × 48 offsets × 255 values) + 2,575 truncations, each run one-shot and byte-at-a-time for **249,950 invocations** that must agree on the exact return code — and comparing the exact code rather than the sign is what catches `M1`, which hides behind a second bound check otherwise. Matrix **264 cells** = 11 ops × 4 uids × 3 session states × 2 CSRF states, which caught a real bug: uid 101 was being read for `need_session`. Lock 60 s doubling to 3,600 s, and **a locked bucket is never evicted**, because otherwise sixteen addresses clear a lockout. `NOENTROPY` is sticky-once-seen and `test_entropy.c`'s first fixture is the device's own 0. ⚠️ `M6`, a constant-time compare given an early exit, was **not** caught and that was predicted before the run |
| **`R7-5`** every RFC vector set passes on the host **and** on the target under qemu; the traversal battery; the route matrix; `chrootcheck` shown failing on a planted `sh`; the scrypt parameters chosen from an anti-DoS budget, with the numbers | 🟢 **met** (`notes/httpd.md` §§ 4–6). 387 cases in four configurations, zero sanitizer findings; the traversal battery is **34 targets all refused with five positive controls**, and the `traversal` mutation turns 3 cases red while the other 31 targets stay refused. `chrootcheck` refuses a planted `/srv/www/bin/sh` with three findings and a planted symlink with one, passes the real root, and its `--self-test` refuses six planted offenders and passes a clean tree. 🟢 The control that earns the qemu run: replacing the Salsa20 state load with a `memcpy` of a `uint32_t` array — the classic endianness bug — leaves the host suite **37/37 green** and turns exactly the three scrypt vectors red on the target. The budget is B1–B5 written before the measurement, and `r = 7` follows from `(12,8,1)`'s peak of 4,197,376 bytes exceeding the 4,194,304 cap by 3,072 |
| **`R7-6`** the pointer battery (self, forward, cycle, chain, past-end) with a positive control that a legitimate compressed name decodes; the anti-spoof set; off-LAN sources refused; the mutation without the loop guard caught by a time-bounded test | 🟢 **met** (`notes/dnsfwd.md` §§ 3, 5). Three guards, and guard 1 alone is **not** sufficient: the `cycle3-backwards-legal` case has three targets each below its own pointer's offset and still forming a cycle, which guard 2's strictly-decreasing rule refuses, and guard 3 refuses the 200-pointer chain every hop of which is legal under 1 and 2. 15 battery cases, 12 refusals and 3 positive controls, the strongest being a two-hop compressed name (51 → 45 → 16) that must decode to `cdn.example.com`; 3,701 checks with 0 failures; a truncation sweep of 454 prefixes all refused and a corruption sweep of 2,270 with 809 accepted and every bound holding. Off-LAN queries are dropped **in silence**, because an error reply would itself be the amplification. The loop-guard mutation **hung** and was reported by an `alarm(5)` around every pointer case rather than waited out |
| **`R7-7`** the mechanism read out of this kernel's `random.c` with citations; a credit policy that under-credits rather than over-credits; a card whose refutation condition is written first, with the reading on an image **without** the change as its control | 🟢 **met** (`FW-160`–`FW-165`, `FW-179`; `notes/entropy.md`). The deadlock is read out of the tree with three citations and it is not the flag: `add_timer_randomness` mixes `get_cycles()` but credits only from a jiffies difference, and `arch/rlx/include/asm/timex.h`'s `get_cycles()` is `return 0;`. The 0 registrations of `IRQF_SAMPLE_RANDOM` has three controls, including 36 flag sites in the drop against 0 compiled in. The policy credits **1 bit per 16 qualifying events, capped at 1 bit per jiffy**, and its first qualifying condition — `phase != last_phase` — **could not fail on this source** at 7.1 ms packets and was replaced by a third-order difference. The control image is `entq0`, built from the same HEAD without the change, with `rlxfw-marks verify` reading 11 witnesses against 12 |
| **`R7-8`** `uspacescan` over every binary in the image, both sources, 0 forbidden imports and the allowed ones counted; the shell prompt; `cfgstore`, `brokerd`, `httpd` and `dnsfwd` each shown running and answering; the KDF's device timing measured rather than inferred from qemu | 🟢 **met, and it is the only step that looks at the shipped bytes on the die** (claims ② and ③). All six programs 0 from both sources; the decompressed extent is 4,096,000 of 5,242,880 bytes, 78.1 % used with 1,146,880 of margin, and rlxfw's busybox at 447,684 bytes replaces four vendor files totalling 579,644. ⚠️ Each of the six is larger than its author reported, by 79,364 bytes together, because the stubs were self-contained and the real `src/lib` is five translation units for the store and two for the KDF |
| **`R7-9`** the entry states what `R7` established and what it did not | 🟢 **met by this entry.** The row's hazard is calling the gate finished on a green suite instead of on the boot, and the answer is that claim ② and claim ③ are the only claims here that rest on the device, that every note but `userspace-integration.md` says in its own words that nothing in it has run on the silicon, and that the list below is longer than the claims |

### The step list's hazard column, read one at a time

`R7`'s list carries no numbered refutation conditions and no stop-loss. What it carries is a
per-step column naming where the step is most likely to be wrong, written with the list at `R7-0`
before any step landed. That is weaker than `R6b`'s `M1`–`M8`, and this entry says so rather than
promoting a hazard into a pre-registration. What stood in for pre-registration on the device is
`notes/entropy.md` § 5.2's criteria for the entropy round and, for the `httpd` fix, a discriminator
written before the rebuilt image booted (claim ③).

* **`R7-0`, declaring a static binary clean because the instrument cannot see into it** — this is
  the defect the step exists to repair, and it did not survive: the tool refuses such a file.
* **`R7-1`, enabling `udhcpd` and shipping its lease-notify `system()` with it** — refuted at the
  bytes rather than at the configuration. `write_leases()` calls `system()`, and uClibc 0.9.30
  implements it as `execl("/bin/sh", "sh", "-c", …)`, so one call site puts both an interpreter and a
  variadic exec in the image; the hook is removed **in source** by a committed patch, because *the
  config does not reach it* is a property of a file in a writable `/var` while *the code is not
  there* is a property of the bytes. 量 after the patch, all six names absent from the symbol table.
* **`R7-1`, every dropped verb is a bench card that stops working** — fired, and it was paid twice:
  five of the vendor image's fifty applets are dropped for the rule (`getty`, `init`, `login`,
  `nice`, `telnetd`), and `od` and `hexdump` were enabled at the owner's request and then turned off
  when the manifest's containment argument turned out to rest on their absence.
* **`R7-2`, supervision that respawns for ever; a PID 1 that leaves zombies** — neither: the cap is
  bounded and its mutation control `M1` is a **bounded** 1,000-iteration loop, 125× the cap, because
  a hang is not a test result; reaping is `waitpid(-1, …, WNOHANG)` in a loop.
* **`R7-3`, a reader that trusts a length, and a fail-open fallback** — answered by the header CRC
  being checked before any header field is read, by the length being range-checked *after* the CRC
  matches because a CRC is not an authenticator, and by `admin.pwhash` having no default.
* **`R7-4`, a slow client holding the broker shut** — `test_wire.c` holds all eight slots with
  silent peers and a normal call is still served; what **does** block is stated rather than hidden —
  one `LOGIN` stalls the loop for one scrypt, deliberately, and one `PING` for up to 10 s, which is
  a real latency hole and is not fixed.
* **`R7-5`, a KDF that is right little-endian and wrong big-endian** — the hazard the qemu control
  was built for, and it fired on the planted `memcpy`: green on the host, three vectors red on the
  target.
* **`R7-6`, the compression-pointer loop** — refuted by three guards, one of which exists because a
  proof that depends on reading an argument correctly is not a guard.
* **`R7-7`, crediting a periodic timer** — not done: the credited quantity is the third-order
  difference of a phase, and the first version's condition was thrown out precisely because it could
  not fail.
* **`R7-8`, a daemon that works under qemu and faults on the silicon** — **this is the hazard that
  fired**, twice, and both are in `docs/KNOWN-ISSUES.md` (claim ③).

### The questions this gate must be able to answer

The plan's `R7` interview row asks three.

**① 「`strncpy` 真的安全嗎？」** No — it does not NUL-terminate on truncation — and it is not used.
量 over `src/`, `strncpy` appears in exactly one file, `src/brokerd/test_wire.c`, at two call sites
in a test, and in no shipped program; `strcpy`, `strcat` and `pthread` appear nowhere in `src/` at
all. The wider reading is the forbidden-construct audit over the eleven `.c` files of `httpd`:
`strcpy strcat sprintf atoi alloca system popen gets scanf` read **0 each** against a control ELF
reading 1 each (2 for `alloca`), 0 variable-length arrays against the control's 1, and 0 cycles in
the call graph across 11 translation units against the control's 1. `src/lib/netutil.c` exists
because `inet_aton` accepts `1.2.3`, `0x7f.1`, `017.1.1.1` and `1.2.3.4 `, and it gives every
rejected shape **its own error code**, because a test that only asserts *refused* cannot tell a
refusal for the right reason from one for the wrong reason.

**② 「你怎麼證明 rootfs 裡沒有 `system()`？」** This is the gate's own subject, and the honest answer is
that the plan's answer — *two independent sources + CI* — is the thing that had to be replaced;
claim ① is what stands in its place. The short form: 0 from two sources of different kind over the
six shipped programs, with the one exception exempt **by name** and its exemption shown firing both
ways, a tool that refuses rather than reporting 0 when it cannot see, and a vendor number of 28
confirmed and ≤ 29 rather than a clean 31.

**③ 「為什麼是多行程不是多執行緒？」** Because this ISA has no atomic read-modify-write, and because a
process boundary is the privilege boundary the gate is about. `brokerd` is one process, one thread,
`poll()` over one listening fd and at most eight connection slots, **no shared memory and no
locks** (`notes/broker.md` § 7); `httpd` forks a child per connection and the parent holds the
limiter, so the arbitration
of the single KDF grant lives in the parent — which is also where this gate's first device defect
was (claim ③). ⚠️ The ISA half is quoted rather than re-measured here, and `CLAUDE.md`'s rule is that
the ISA is never measured under Linux; what `R7` adds is the consequence, not the reading.

### What `R7` did not establish

🔴 **That anything ran under load.** Six programs, one boot each, one question each. The
eight-connection cap, the four-per-address cap and the 429 after a burst were exercised on the build
host by `rootcheck`, not on the board, and `plan` § D8's acceptance test — the memory high-water
mark under N concurrent login attempts with a real `brokerd` doing real scrypt, **with its refutation
control, the same test with the limiter removed making the machine lose responsiveness** — is not
done. It needs the device and `brokerd`, and without the refutation control a green run would prove
nothing.

🔴 **No TLS.** HTTP only: every password on this port crosses the LAN in clear, and neither cookie is
`Secure`, because a `Secure` cookie over plain HTTP is a cookie that is never sent. `R7g` is outside
this gate by the plan's own cut order.

🔴 **That the config store survives anything.** `/var/lib/cfg.bin` is on a filesystem the image calls
tmpfs; `R8` supplies the MTD backing. `fsync` there verifies that the page cache agrees with itself.
The torn-write model is a **prefix** write: it does not model a device that commits pages out of
order, nor a partially programmed NOR word that reads back as the AND of old and new. The `0xFF`
fill and the `seq` exclusions of 0 and `0xFFFFFFFF` are the parts written **for** NOR rather than
**on** it. 量 beside that: both boots printed `config store slot 0 seq 0` although the first had
written `slot 1, seq 2` — which shows nothing carried across the reset, not that a same-image reboot
behaves differently, because the second boot ran a different image.

🔴 **That any rlxfw filesystem is bounded, and the absence of `CONFIG_TMPFS` is not a simple
absence.** 讀, and confirmed against the built artefact rather than against the `.config` alone:
`# CONFIG_TMPFS is not set` and `# CONFIG_SHMEM is not set`, yet `mount -t tmpfs` works:
`mm/shmem.c`'s `#else !CONFIG_SHMEM` branch registers a `tmpfs_fs_type` whose `get_sb` is
`ramfs_get_sb`, confirmed by dumping the struct out of `vmlinux`'s `.data`. And `fs/ramfs/inode.c`'s
option table is `mode=%o` and nothing else, **with no `default:` in its switch** — so every other
option is silently ignored and a `size=512k` would read as a limit and be none. **Four** mounts —
`/var`, `/run`, `/tmp` and `/srv/www/run` — can each grow until the board is out of RAM (~26 MB),
and `simple_statfs` means `df` cannot show it. `test_mounts.c` asserts that no row carries a `size=`,
which is the only thing that stops one being written and believed. Bounding them needs
`CONFIG_TMPFS` and `CONFIG_SHMEM`, a kernel change (`notes/init.md` § 3, § 8).

🔴 **That the fuzzing is worth more than the minutes it ran, and three pre-registered thresholds were
missed and reported as missed.** 量 on the host, four campaigns, and nothing in any of them ran on
the die. The clean runs are 720–780 s each. `brokerd`: branch coverage
**66.67 % against ≥ 85 %** and region **87.83 % against ≥ 95 %**, both missed and *not renegotiated*
— and the note's own reading is that 66.67 % is the harness's **ceiling**, because the
pre-registration was written without excluding the NULL guards and a second bound that is
unreachable while the first holds; the correct way to have written it was to exclude those branches
from the denominator **before** the run. `dnsfwd`: T3, `dns.c` whole-file branch coverage **38.10 %
against ≥ 65 %**, not met, the threshold **not moved**, and the honest statement is that the
forwarder engine is covered by the battery and not by the fuzzer. `httpd`'s first harness missed the
`http.c` line threshold at **84.96 % against 85 %**, and that stays on the record: the bar was not
lowered by 0.04 points, the harness was connected to three functions it was never calling
(`http_reason`, `http_mime`, `http_parse_all` — 35 of the 63 lines it had never reached) and the
number moved to 91.89 %. The config store's four (P1–P4) were met, with 87.0 % named as a ceiling
and not a shortfall. **365,254 executions with no crash is not an absence proof**; what it is worth
is bounded by the planted-defect result beside it.

🔴 **That "a fuzzer must find it" is a criterion, because `brokerd`'s planted-defect find is
stochastic.** Five of six configurations never found the one-byte overflow — 167,561 execs in 300 s,
209,072 in 900 s, 83,484 in 240 s, 165,409 and 207,918 in 300 s — and the sixth (one seed,
`AFL_DISABLE_TRIM=1`, `-D`) found it in **7 s at 4,179 execs**. **The first repeat of that same
configuration missed it.** Six further independent 300 s runs: found at 2 s / 441 execs, at 10 s /
3,644 and at 1 s / 442; not found in three runs of 300 s at about 160,000 execs each. **3 of 6, and
bimodal** — inside ~11 s and ~4,000 executions, or not inside 300 s — so run length buys nothing.
That is the missing coverage gradient seen from the other side: a 32-bit length compared against
**one** constant gives coverage guidance nothing to climb, because every wrong value lands on the
same edge. A pass condition of this shape needs a named configuration and a hit rate, or it is a
coin flip.

🔴 **That a sanitizer's silence is evidence: the first planted HTTP off-by-one is invisible to
ASAN.** `>=` became `>` in `http_feed()`'s line-buffer bound, so `line[1025]` is written in a
1025-byte array; 量 on the exact triggering input — a request line of exactly 1024 bytes — the
mutant built with `AFL_USE_ASAN=1` returns **0**. No report, no crash, nothing for a fuzzer to find.
The reason is a layout fact: `line` is a **member** of `struct http_parser`, ending at offset 1049
with the next member, a pointer, at 1052, so byte 1025 lands in the struct's own two bytes of
padding, and AddressSanitizer instruments *object* boundaries and not intra-object ones. Fifteen
minutes of fuzzing would have found nothing and the pre-registered rule would have **voided the
coverage figures** — for a defect that is real. Two consequences: parser scratch in a bare local
array is checkable and the same scratch inside a struct is not.

🔴 **That NAT forwarding works, and it is out of reach on this bench rather than merely unmeasured.**
Per-port VLAN was not met at `R6` (`R6-6`) and this host has one NIC, so there is no second segment
to route to; the rules are installed and read back instead. Beside that: `SIOCADDRT` has never been
issued on this board by anything; no WAN interface is proven to exist, `RLXFW_WAN_IF` defaults to
`eth4` and is 未定 pending `R6-6`; and `wan.mode` defaults to 0, so `udhcpc` never started and
`ifupd` has never been invoked by it.

🔴 **That rlxfw's busybox is clean over the wider name set — `execle` is an exemption by name, not an
absence.** 量 `execle` at `0x41b690` with one `.got` reference, from `networking/udhcp/script.o`'s
`udhcp_run_script()`, whose argv is a typed path plus one of four literal event names with
`CONFIG_UDHCPC_DEFAULT_SCRIPT` compiled in rather than typed. `G6` refuses the build if any other
object references it **and refuses equally if nothing does**, so the exemption cannot outlive its
reason — and the exemption is swept both ways rather than dated. The vendor's busybox also imports
`execlp` and `execvp`, which let `PATH` decide which file runs, so a zero over a wider set is
decided by the **build** and not by shipping busybox (`FW-22`; `notes/busybox-build.md` § 3, § 4).

🔴 **That the anti-DoS budget behind `r = 7` is measured.** The cost is: `log2N=12 r=7 p=1` takes
0.902 s on the die. The budget is an **argument** written before it — B1 peak ≤ 4,194,304 bytes, B2
one concurrent evaluation, B3 ≤ 1.0 s each, B4 one evaluation per connection, B5 ≤ 25 % sustained —
and `(12,8,1)`'s 4,197,376 exceeds B1 by 3,072 bytes, 0.073 %, with the cap deliberately not
widened. The 25 % is 0.25 login/s × 1.0 s, worst case from an attacker with unlimited addresses, so
**a per-IP bucket is not a bound**; and the actual memory high-water mark on the board was never
measured. ⚠️ The two notes still disagree about the parameter: `notes/broker.md` § 5 writes
`r = 8` into a new hash and `notes/httpd.md` § 5.3 rejects `(12,8,1)` and rules `r = 7`. The shipped
behaviour is settled — the device wrote `scrypt log2N=12 r=7 p=1` — and the same disagreement was
the compiled defect the integration found, `BK_KDF_R` 8 against `kdf.h`'s 7, which alone would have
made `PWSET` return `-KDFE_NOMEM` every time (`FW-178`).

⚠️ **The entropy result is an accounting result and not a strength result.** `entropy_avail` is a
variable `rlxfw_random_add()` writes; a pass shows the accounting works and the source is alive, not
that the source has the min-entropy claimed — establishing that needs raw samples off the board and
an SP 800-90B style estimate, and `RLXFW_ENT_PER_BIT` = 16 is a **derating**, not a measurement:
`notes/entropy.md` § 4.2's 16× derating and § 4.3's clamp are arguments, and § 6 says so in its own
words. The round's three prohibitions — no reset
press, no mtdblock I/O, no ioctl — are procedure and not instrumentation, and **the second has no
instrument at all** (`FW-162`), so the pool reading is about this driver only if all three held.

⚠️ **殘留: the driver's `bits` and the kernel's `entropy_avail` agree once and then diverge, twice by
exactly 128 bits, and why is not known.** 量 71 = 71, then `bits 403` against 275, then `bits 406`
against 147, then steady at 150. One obvious suspect is excluded: two consecutive reads gave 150,
and a deliberate second of `cat /dev/urandom` still gave 150, so the reads are not draining it. Two
drops of exactly 128 bits — 16 bytes, one session token or one salt — is too tidy for quantisation
error. **Not found out is not found out.** It touches no registered criterion, which looked at the
first reading's equality and at `bits` rising, and it is the live example of a number a tool reports
needing someone to reconcile it (`FW-180`).

⚠️ **The image's margin is an ELF's extent, not a running kernel's footprint.** 量 on the host,
4,096,000 of
5,242,880 bytes over 2 `PT_LOAD`s, `0x80000000`–`0x803e8000`, 78.1 % used. Nothing measured what the
four unbounded mounts take at run time, and `df` cannot be asked.

⚠️ **Almost every number in the nine notes is a host measurement.** `notes/init.md`,
`notes/httpd.md`, `notes/broker.md`, `notes/config-store.md`, `notes/dnsfwd.md` and
`notes/busybox-build.md` each say in their own words that nothing in them ran on the device;
`qemu-mips-static` covered the KDF's vector sets and `dnsfwd`'s decoder and nothing else, and
**qemu certifies logic and never codegen or the ISA**. `hazlint` 0 is one hazard class over the
words it can reach — it scans `SHF_EXECINSTR` sections linearly, 44 KB of the busybox ELF is named
as not scanned — and whether this core would mis-execute a violation is `TC-h`, still open.

⚠️ **Three second transcriptions of one table are unreconciled by any tool.** `httpd`'s stub key
table was diffed row by row against `src/lib/schema.c` — sixteen of sixteen identical, measured by
two programs each printing from its own copy, with a control that a one-field edit is reported — but
nothing checks it automatically, and the byte-level reconciliation of `httpd`'s `client.c` against
`brokerd`'s `proto.c` has not happened. Two independent encodings of one table are exactly as likely
to disagree as to agree.

⚠️ **Four of the seven things the parallel stubs guessed about each other were wrong**, and two
compiled defects each alone would have made a password impossible on this image. `CFG_NKEYS` 17
against the real 16, which made `struct cfg` one 64-byte row too long; seven `CFGE_*` numbers all
wrong, harmless only because `brokerd` reads the sign; `CFGE_BOUND` against the real `CFGE_RANGE`.
Right were `cfg_last_key()`'s signature, `init`'s sixteen key ids and six default literals, and the
`BK_*`/`OP_*` **values** — the names differed and the values did not (`FW-178`).

⚠️ **`M6` is an honest miss and the login timing is not a channel measurement.** `brokerd`'s
constant-time compare given an early exit was **not** caught by any test, and that was predicted
before the run: it is functionally identical, so no unit test can see it. The 0.902 s against
0.9017 s measured on the board compares two whole-request times on one boot; a timing side channel
needs a timing experiment, and there is none here.

⚠️ **`dnsfwd`'s rate limiter does not stop amplification — the LAN check does.** With 32 slots and
LRU eviction an attacker spraying 33 source addresses gets a fresh bucket each time; the bucket only
stops one LAN host starving the others. `dns_rate_allow()` computes `dt` unsigned with no
backwards-clock guard, so a 32-bit millisecond wrap hands every client one free full burst — left
alone deliberately, because it is once per 49.7 days and too permissive rather than too strict.
⚠️ And `lan.netmask` is not one of the keys `SPEC-R7` § 6 grants uid 101, so the off-LAN check may be
running on the schema's default /24 rather than on the configured prefix.

⚠️ **The vendor baseline is a capability count, not a use count, and it is not a bound in either
direction.** `bin/dnsmasq` importing `popen` does not show that a path reaches it, and `dnsfwd`
importing none of the seventeen process-starting names does not prove it cannot start a process some
other way — 量, a raw `syscall()` would not appear as an import either, which is a second check and
not a proof of the first. Three of the vendor's 55 ELFs are static and **undetermined** rather than
clean.

⚠️ **The gate's own specification and every pre-registration are outside this repository.**
`SPEC-R7.md` and `SPEC-R7-8.md`, which pin the interfaces all seven programs were written against,
are segment-local files under `$FWRE_WORK`, cited from committed notes and committed C; so are the
four fuzz pre-registrations (`brokerd`'s `PREREG-fuzz.md`, the config store's `prereg-fuzz.txt`
whose mtime is the evidence of order, `dnsfwd`'s `fuzz-prereg.txt` timestamped with the sha256 of
two sources, and `httpd`'s thresholds), `httpd`'s forbidden-construct audit, and the replay and
state sweep that cleared `rl.c`. What a reader here can follow is `notes/`, `SPEC.md`, `bench/` and
the code.

⚠️ **Three numbers in this gate's own record do not reconcile, and none of them is settled here.**
`SPEC.md` `FW-165` records the entropy build's `.text` growth as **+1,816** bytes while
`notes/entropy.md` § 8, the owner, says **+1,736** and its own table gives 3,582,908 → 3,584,644,
which is 1,736 — an 80-byte disagreement between a value and its owner. `notes/rootfs-census.md`
gives **161** files for the extracted vendor tree in one section (量 2026-09-30) and **163** in
another (量 2026-08-29), for the same path, and never reconciles them. And `notes/init.md` § 8 says
*`udhcpc`/`udhcpd` do not exist on this image*, which `notes/busybox-build.md` § 5 and § 9 supersede
on the same day in the same segment — both are among the shipped 53 applets.

⚠️ **The board row's baseline was not beaten arithmetically, and the step list said so before the
gate ran.** The row reads *Baseline to beat: 31 of 55*. 31 and 28 are counts over dynamically linked
vendor binaries, and *0 of 55* would not be the same measurement; what `R7` establishes is 0 over
six statically linked programs by a re-specified instrument, with the vendor number **restated**
rather than beaten.

⚠️ **The cost ratio is not a measure of difficulty.** 34 on § Gate board, 40 in the plan's own cost
table and 38 in its prose, against 1 segment actual. `R7g` (TLS) was cut by the plan's own order,
`R7f`'s endpoints were 6 rather than 12, functional parity was cut at v4, and this segment ran many
agents in parallel, so one segment of wall clock is not one segment of work. `PROGRESS.md`'s own
note on that column says it is not a quantity.

⚠️ **`spec-check`'s `C3` fired on a faithful quotation of the thing it was describing**, which is
this gate's smallest finding and is recorded because it is a live example of a checker whose
vocabulary is wrong while its behaviour is right: `BLANK_RX` is a bare-substring test on three
open-value markers, so a row whose value mentions an undefined symbol is silently read as open. The
wording was changed and the checker was not (`FW-173`).

⚠️ **Flash.** 量: the two boots made **two** uploads, whose console preparation was `AUTOBURN 0`,
`LOADADDR` and `IPCONFIG` — `AUTOBURN 0` disarms and is not one of `CLAUDE.md` § Flash's four verbs
— and the `AUTOBURN` word at `0x8040D4A0` was read **twice**, once per boot, reading `00000000` each
time. No `FLW`, `EW`, `EB`, `DB` or `FLR`, and no non-zero `AUTOBURN`, appears in any capture or
upload record of the gate; both returns to the loader were `busybox reboot -f` with
`Reboot Result from Watchdog Timeout!` in the capture (`FW-37`). What that cannot see: two writes
that cancel, every byte outside the words read, and `H601`, which is never hashed. **No flash map was
taken in these boots**, so there is no bracket of their own to compare against the 2026-08-16 dump;
`n_writes` was not read and carries no information (`FW-142`). The `FLR` bracket stays at 1,024 of
4,194,304 bytes = **0.0244 %**, and `FLS-26`'s ledger does not move. The closing commit records
`flashwin scan` CLEAN against this unit's dump.

### The main session's rulings in this gate, which the owner may override

The owner's own — opening `R7` and `R8a` on 2026-09-30, asking for both in one segment, enabling
`od` and `hexdump` in the first build, and the widened relaxation of 2026-09-30 — are not listed.
Each below is recorded where it is cited.

1. The pass condition of 2026-08-25 re-specified rather than met as worded, and the vendor baseline
   **restated** rather than beaten arithmetically (`notes/rootfs-census.md`; `FW-20`).
2. `uspacescan` refusing a file it cannot decide, and reporting `UNDECIDED`/`UNPAIRED` rather than
   0, with `wordexp` carried as a permanent control row.
3. `execle` exempt **by name** in rlxfw's busybox, with `G6` swept both ways so the exemption cannot
   outlive its reason (`notes/busybox-build.md` § 4).
4. `od` and `hexdump` turned off after the manifest's containment argument turned out to rest on
   their absence, and the manifest's sentence **narrowed** rather than defended — `grep -c` is a
   per-byte oracle and was already outside the old wording (`notes/busybox-build.md` § 7, § 7.1).
5. `R7-3`'s torn-write clause refuted as worded and replaced by a stronger invariant, with `L = 4096`
   as the positive control that stops the rest being vacuous (`notes/config-store.md` § 5).
6. `brokerd`'s socket left at mode 0666 with `SO_PEERCRED` as the authorisation, rather than
   `SPEC-R7` § 3's `0660`, because three uids must reach it and `dnsfwd` is not in gid 100
   (`notes/broker.md` § 3).
7. A locked rate-limit bucket never evicted, at the stated cost of refusing logins from new
   addresses while all sixteen are locked (`notes/broker.md` § 5).
8. The entropy policy's first qualifying condition thrown out for being unable to fail, and replaced
   by a third-order phase difference; the credit left as a 16× derating and named as one
   (`notes/entropy.md` § 4.1, § 4.2).
9. `r = 7` rather than the canonical 8, because `(12,8,1)` exceeds the pre-written 4 MiB cap by
   3,072 bytes and the cap was not widened (`notes/httpd.md` § 5.3).
10. EDNS0 answered `FORMERR` rather than with `TC = 1`, and source-port randomisation left
    per-process rather than per-query, written down as the thing to revisit (`notes/dnsfwd.md` § 3).
11. `FW-184` recorded and **not fixed**, under the owner's rule of 2026-09-26; the smaller per-IP
    over-charge found beside `FW-182` was fixed, and `dns_rate_allow()`'s clock wrap was left.
12. `FW-173`'s wording changed rather than `spec-check`'s `BLANK_RX`, under the same rule.

---

## 2026-10-04 — `R8` (closed on the three clauses `R8a` read from RAM, and the clause whose experiment is an interrupted flash write given a row of its own, `R8b`, behind `R9`)

### One line

**v0.5+, two segments — the 118th, shared with `R7`, for `R8a`; the 119th for this decision and for
the CI repair that was its first condition — and no power action of its own.** § Gate board costs
`R8` at 18 segments and the plan at 22, both for the two halves; the actual is **2** for the half
that closed, which measures the cut and not the difficulty. **This entry is a split, not a
completion.** `R8`'s row read *signed update accepted, one flipped bit rejected, 10 power-cuts
survived*. It closes on what `R8a` read on the silicon on 2026-09-30 — a signed container accepted
and its payload booted, one flipped payload bit refused at `DIGEST bad`, and a version below a
RAM-staged counter refused at `VER cur=1 ctr=5 bad` — from RAM, with ten uploads and no `FLW`, `EW`,
`EB` or non-zero `AUTOBURN` (entry 16). The third clause, and the persistence it implies, are an
interrupted flash write by construction, so they are `R8b`'s row, booked behind `R9` and behind the
owner's dated yes for each write. Nothing about writing flash or surviving a power cut is
established here.

**The weakest thing here is that nothing was measured to close it.** The row closes on readings
taken a segment earlier and on two conditions set for it in this segment, of which one was met and
one was replaced. Met: CI green with `census` on a head that contains `R8a`'s work — run
`37134992834` on `8a3b3be3`, all four jobs `success`, the first `census` run since `380cdf6d` (量,
`gh`). Replaced: `notes/rlxboot.md` § 6's second reading, a `DW` of `rlxboot`'s destination after
the copy, was designed and then not run, because no value it can return separates *the flush is
necessary* from *it is not* (`FW-172`, `6cfe908e`). So the cache handling on the gate's own success
path is still 推, and the experiment that would decide it is `CPU-19` ①'s and is not scheduled.

### Three claims that stand

**① The row's three clauses hold on the silicon — on entry 16's evidence, which this entry does not
re-measure.** 量 2026-09-30, four rounds in one seating (`bench/2026-09-30/R8A-*`; `FW-170`,
`FW-171`). Round 1: the good container with the counter read from flash — `SIG ok` / `DIGEST ok` /
`VER cur=1 ctr=0 ok` / `BOOT` — and the payload reached its shell. Round 2: one payload bit flipped,
`SIG ok` and then `DIGEST bad` / `REFUSE digest`, no boot, with `SIG ok` in the same capture as the
positive control that Ed25519 ran. Rounds 3 and 4: the same container against a RAM bitmap of 5 and
then of 0 — `VER cur=1 ctr=5 bad` / `REFUSE rollback`, then a boot — differing in the bitmap's value
and in nothing else. ⚠️ One seating, one build id `6395889d`, one image; the *anywhere* of *one
flipped bit anywhere* is the host suite's 9,472 flips under `qemu-mips-static`, not the device's;
and the script that compared 43 assertions line by line lives outside this repository.

**② `R9` before `R8b` is a constraint, and the split is how the board states it.** 讀 the arithmetic
(`FW-167`; entry 16 § `R8b`): slot A spans `0x070000`–`0x18FFFF` and the vendor kernel
`0x060000`–`0x151012`, so the first write to slot A destroys 921,619 of that kernel's 987,155 bytes
and `check_image()` stops finding a bootable image in flash. That boot is `R9`'s vendor column,
TOTOLINK released no source, and restoring the 2026-08-16 dump means 3.3 MiB through a `burn()`
with no lower bound, on a device with no spare. A row that held both halves would read `~` for the
whole of `R9` while nothing in it could move; running `R8b` first would end the vendor column. ⚠️
The arithmetic is 讀 from `SPEC.md`'s flash-map rows and the loader's scan table, and its one unread
input is `check_image()`'s `bank_offset`, never read for this build.

**③ The tree that holds `R8a`'s work is green on every CI layer, `census` included, for the first
time since `380cdf6d`.** 量 `gh`: run `37134992834` on `8a3b3be3`, created 2026-10-03 23:56:00
+08:00; `lint`, `text`, `instruments` and `census` all `success`, `census` finishing at 2026-10-04
00:26:50 +08:00. `8a3b3be3` descends from `f5641f3d`, `R8a`'s closing commit. Each of the four steps
`SPEC.md` `FW-185` records as red on the four 2026-09-30 heads was repaired in a commit of its own —
`test-config-gates` in `9013a17a`, `audit-bench-log (exit-code gate)` in `ae9b2b9e`, `nic15check` in
`d96be8b9`, `bootbytes` in `fe141ba9` — and the push of eleven commits, `5eaeb643..8a3b3be3`,
followed a desk run on the integration clone in which all 26 selected steps ran and 25 were green.
The 26th, `test-config-gates`, is red at the desk and only there: two `E5` lines and `E6` need the
gitignored `build/` — 68 passed and 3 failed in the desk shape, 64 passed, 0 failed and 2 skipped in
the runner's, both measured. ⚠️ A green run is a claim about its controls: it certifies the layers
that ran on `8a3b3be3` and says nothing about a later head.

### The board row's clauses, read one at a time

| the row said, until 2026-10-04 | verdict |
|---|---|
| **signed update accepted** | 🟢 **met** on entry 16's rounds 1 and 4. ⚠️ The update is a container staged in RAM by the loader's TFTP and entered with `J`, not an image written to a slot and booted from flash |
| **one flipped bit rejected** | 🟢 **met** on round 2 for one payload bit, with `SIG ok` as its positive control; *anywhere* is the host's 9,472 flips |
| **10 power-cuts survived** | 🔴 **not met, and not attempted**: the interrupted write is the experiment. It is `R8b`'s row now, booked and not open |
| *(added by `R8a`)* **a version below the anti-rollback counter rejected** | 🟢 **met** on rounds 3 and 4, from a RAM bitmap, because the flash source cannot tell an erased region from an undecoded window. The counter never advanced |

### The questions this gate must be able to answer

The plan's `R8` row asks five. Entry 16 answers ① and ② and half of ③; ④
「寫到一半斷電會怎樣？」and ⑤「只有一台機器你敢寫 flash？」are `R8b`'s, and closing `R8` changes none
of the five answers. ③ is still half: the rescue payload is not built.

### What `R8` did not establish

🔴 **That anything can be written to flash and read back after a reset.** Neither `R8a`'s four
rounds nor anything since issued a flash-write command, so no image has been written to a slot, no
slot has been booted from flash, and the anti-rollback counter has never advanced: the monotonicity
the design rests on is asserted and never exercised.

🔴 **That an update survives a power cut.** The ten power cuts are `R8b`'s criterion ④ — ten
physical pulls during a write, each followed by a boot from the other slot — and nothing here bounds
what an interrupted write leaves behind.

🔴 **That the cache flush is necessary, or correct on its own.** `FW-172` stays 推. Booting showed
the composite path — copy, write back D with `CCTL 0x200`, invalidate I with `0x002`, jump — on one
die for one copy. The second reading `notes/rlxboot.md` § 6 asked for cannot decide it: `rlxboot`'s
SHA-256 streams the container through the 8 KiB D-cache before the copy (讀), so the copy stores to
lines the D side does not hold (推); every route back to a prompt writes back first; and `rlxboot`
has no arm that skips the flush. The deciding experiment is `CPU-19` ①'s — a probe1-style store to
a line resident in the cache, read back by the I side, `0x002` alone against `0x200` plus `0x002`,
with a no-treatment and a store-miss control — and it is not scheduled.

🔴 **That the row's wording of 2026-08-25 is met.** It is not: the row was rewritten to what was
measured, and the rewriting is a decision, recorded below, not a result.

⚠️ **Entry 16's other residuals stand unchanged and are not repeated here**: key management, with a
development seed in the tree on purpose; no secure boot, on a part with no evidence of a key-hash
fuse; no defence against an attacker who can already write flash; the flash window's decode at
`0xBD3F0000`; `rlxboot-rescue` unbuilt; `cvimg`'s `cr6b` against `check_image()`'s `cs6c` and `cr6c`
(`FW-168`); and timing.

⚠️ **The CI evidence is a run, not a property of the tree.** It is green on `8a3b3be3`; the heads
after it — `44b333d6`, `3ad90840`, `82ec19d7` and this entry's commits — had no run when this was
written.

⚠️ **Flash.** 量: closing `R8` took no seating, and its rounds are entry 16's, whose bookkeeping
stands. In the same segment the board was powered once — the owner's cold boot, caught from 23:30:47
on 2026-10-02 — and reset once with `busybox reboot -f`, for `FW-184`'s runs and not for this gate;
it made two uploads, `CB1` and `CB2`, each after `DW 8040D4A0` read `00000000` and the loader
answered ARP, with the staged head read back equal to the file before each `J`. No `FLW`, `EW`,
`EB`, non-zero `AUTOBURN` or `FLR` was issued. What that cannot see: two writes that cancel, every
byte outside the words read, and `H601`, which is never hashed. No flash map was taken, so there is
no bracket of the segment's own; the `FLR` bracket stays at 1,024 of 4,194,304 bytes =
**0.0244 %**, and `FLS-26`'s ledger does not move.

### The main session's rulings in this gate, which the owner may override

The owner delegated the decision on 2026-10-02 —「用最頂的工程思維幫我決定」— and continued the
relaxation of 2026-09-27 and 2026-09-30, with the flash rules, `H601`, the power handshake and
`NET-165` unchanged; those are the owner's own and are not listed.

1. **`R8` closed by splitting its row**, weighed against the other options in the owner's question.
   Keeping `R8` open until `R9` and then `R8b` was rejected: `R8b` depends on `R9` and `R8a` does
   not, so one row would read `~` for the whole of `R9` — the plan guesses about six segments —
   while nothing in it could move. Running `R8b` now, ahead of `R9`, was rejected: slot A's first
   write ends the vendor firmware that `R9`'s vendor column depends on, and it cannot be undone
   short of 3.3 MiB through a `burn()` with no lower bound. Opening `R9` first is the next-gate
   question rather than an alternative to the split; it stays the owner's, and `R9` is the gate that
   unblocks `R8b`.
2. **The second closing condition replaced rather than met**: `notes/rlxboot.md` § 6's second
   reading recorded as unable to decide and not run, `FW-172` left 推, and the deciding experiment
   left with `CPU-19` ①, unscheduled (`6cfe908e`).
3. **The rows that named `R8` as their owner re-owned to `R8b` in the closing commit**:
   `PROGRESS.md` § Carried forward `C-1`, `C-3`, `C-4` and `C-13`, and `SPEC.md` § 17's `REG-13`,
   `REG-14` and `FLS-06`–`FLS-08`. Each is about a slot layout, the flash write path or a boot from
   flash, which is the half that writes; left on a closed `R8`, the four carried-forward rows would
   read `ORPHAN` in `cfcensus`.

---

## 2026-10-04 — `R9` (the differential table published on 16 rows with a mechanism class each, a live column that speaks for 21 of 89 cases and says so, and a 推 of its own retracted inside the gate that produced it)

### One line

**v0.6+, three segments — the 120th for the re-specification and eight of the twelve steps, the
121st for three more, the 122nd for `R9-11` and this closing — and one power action, the vendor
seating, shared with `R9-7`.** § Gate board
costs `R9` at 16 segments; the actual is **3**, which measures the relaxation of 2026-09-27 and the
fact that eight steps were desk work over files that already existed, not the difficulty of the
question. The gate closes on `docs/differential.md`: **16 published rows** standing for the
register's **141** rows, each carrying ① a mechanism class from the closed set, ② a vendor cell that
is a reading from one of three evidence tiers or `⊘ Structural` naming a committed finding, ③ an
rlxfw cell from the same instrument as ②, and ④ a check that would have detected the opposite of
the row's claim together with that check's reading — a row without ④'s reading publishing 未定 and
never a win. 量 over the rendered file: publish reads **win 17, surface-absent 5, not comparable 42,
未定 77**. **Zero flash-write verbs and zero `FLR` were issued in either segment**, and the map
bracket came back equal at two granularities.

**The weakest thing here is that the live column speaks for 21 of 89 cases.** 讀, re-derived from
both files rather than quoted: `config/fix-cases.toml` carries **89** rows at tier `V-A`, the tier
whose refutation needs a live, network-facing reading; `config/r9-probes.toml` holds **27** probe
cases citing **21** distinct register rows, the two numbers differing because **6** rows carry two
cases each — `FC-034`, `FC-038`, `FC-039`, `FC-067`, `FC-078` and `FC-079` — so counting cases would
overstate coverage by 6. The other **68** are exempted by name with a written reason each, and
**21 + 68 = 89** closes against the 89. **So the published table says 21, not 89**, and the renderer
refuses if that sum does not close, if an id is both probed and exempted, if an id is neither, or if
either set names a row that is not `V-A`. Nothing here speaks for the **52** rows in tiers `V-B`,
`V-C` and `V-D`.

### Four claims that stand

**① The gate's own instrument can fail, which is the whole reason the row was re-specified.** 讀
`PROGRESS.md`'s `R9` row as it stood until today: the clause was *a three-column table whose third
column is not empty*, and seven rows of that column were committed in `plan/` § 8.2 **before `R9`
existed**. That is the `R7` defect verbatim — a gate whose instrument cannot fail — and it was
caught before the gate opened rather than at its close. The replacement is a per-row requirement
whose fourth clause is a reading that may be absent: 量 over the register, **109 of 141** rows have
a reading on ④ and **32** read 未定, and `tools/fixcases.py` `C7` refuses a `win` on a 未定 ④ with
mutation `M8` showing it fire and `P2` showing it permit. ⚠️ What this does not establish: that the
re-specification made the gate harder or easier. It made the outcome decidable, which is a different
property, and the owner may read the swap as having lowered the bar.

**② Both firmwares were read by one instrument, on one host, cable and port, in one episode.**
量 2026-10-04 (`FW-197`, `FW-198`; `bench/2026-10-04`): 27 cases on each column, **137 differing
fields**; the vendor connects on 52869 and 52881 where rlxfw refuses outright; six closed ports
separate *closed* from *never ran*; rlxfw answers 431 where the vendor answers 200, so rlxfw bounds
header size and the vendor does not; the vendor serves its configuration blob under
path-normalisation variants **unauthenticated** where rlxfw returns 400; and `C21` agrees on both
sides, which is published too. The link was checked with a control before any probe — 10.1.1.1
answered 3 of 3 and 10.1.1.77 on the same subnet did not — because without it a dead link makes all
27 probes read *closed* and publishes a false rlxfw column. The instrument's own repeat control
found something rather than passing cleanly: two vendor runs 60 s apart differ in **exactly one
field of 27 cases**, `C12`'s header digest over `/status.htm`, a page whose headers vary by
construction; 26 of 27 reproduce byte for byte. ⚠️ One episode, one seating, one cable. A
config-bearing case records status and length only — no body and no digest — because this unit's own
configuration may not enter the repository.

**③ The one vendor boot was contained twice, and the second containment does not depend on the
experiment coming out as expected.** `FW-196` says 讀 the vendor writes flash on an
*unauthenticated* request past an uptime threshold, and `CLAUDE.md` refuses a containment that holds
only if the result is as predicted. Path: 讀 every `path =` in the probe list, exactly one carries
`htm` — `/status.htm`, the third of the seven names the authorisation branch excludes — and the
three prefix probes use an impossible handler name, which matters because `handleForm` has no method
test. Timing: 量 the whole vendor HTTP episode finished at **J+61 s** against a **J+601 s**
threshold, and that bound holds whatever the list says. The lower bound was measured too, not
guessed: `NET-118` has 52869 answering only at J+31.3–32.5 s, so an earlier start reads an opening
port as closed. The board was never left at the loader prompt (`NET-165`), and getting into the
vendor firmware used two measured halves — `busybox reboot -f` with an ESC catch (`FW-37`) then
`J BFC00000` — in one invocation, so the script does not jump if the catch fails.

**④ `R9-5` built `quiet-swcore` for the first time and found 0 differences outside the `SWCORE`
set — and, in the same measurement, that both drivers the controlled-variable claim calls *the same*
are not the same object.** 量 2026-10-04, three builds one at a time with one `config/` so all three
carry `RECIPE_ID` `575da809` (the comparator refuses if they differ, because a moved `RECIPE_ID`
changes a `-D` on every C object): `r95q` (`quiet`, `SWCORE=n`) 4,257,403 B, `r95y`
(`quiet-swcore`, `SWCORE=y`) 4,567,218 B, and `r95q2` as the reproducibility control, byte-identical
to `r95q` over `vmlinux` and over 735 of 735 objects. The set `S` is **41** kconfig symbols — 量 the
installed `.config` differs on **1**, `CONFIG_RTL_819X_SWCORE`, and the `.config` each build *used*
differs on **41**, equal in both directions to the delta's own 41 `@quiet,loud` rows. **173 object
differences** (29 presence, 144 content) classify inside `S` by three rules that each name what they
read, and **0** fall outside; 1,042 symbol-level differences trace to a defining object with **0**
owners outside the same bucket, which is a second independent route to the same answer. 🔴 And 量
`drivers/net/wireless/rtl8192cd/built-in.o` is 816,475 B against 820,910 B, while
`drivers/net/rtl819x-nic.o` and `drivers/net/rlxfw-seam.o` differ and the other ten of rlxfw's
twelve built drivers are byte-identical: **the NIC driver and the WLAN driver — the two the claim
names as the same — are exactly the two that are not the same object.**

### The board row's clauses, read one at a time

| the row said, re-specified 2026-10-04 before opening | verdict |
|---|---|
| **every published row carries a mechanism class from the closed set ⟨架構性／有界化／服務不存在／平台限制／不適用⟩** | 🟢 **met** on 16 of 16 rows. 量 the register's classes are 架構性 35, 有界化 15, 服務不存在 18, 不適用 73 and **平台限制 0**. 🔴 A 0 is a claim: the renderer's `--self-test` `P1` plants a `平台限制` row and requires it to be **accepted**, so the 0 means the register carries none and not that the renderer cannot represent one. 🔄 **2026-10-04, re-measured at the close: `tools/fixcases.py`'s own `CLASSES` now holds **five** and carries `平台限制`** — 量 `tools/fixcases.py`, the set is `{架構性, 有界化, 服務不存在, 不適用, 平台限制}`. The defect this row recorded (a `平台限制` row the renderer accepts and the register's checker refuses) was repaired in `b1b5e8db`, so the two checkers now agree on the closed set and the 0 stands on both |
| **a vendor cell that is a reading from `V-A`/`V-B`/`V-C` naming its capture or artefact, or `⊘ Structural` naming the committed finding** | 🟢 **met** on 16 of 16. Tiers 量 V-A 89, V-B 29, V-C 10, V-D 13 over 141 rows; `V-D` resolves to `⊘ Structural` cited from `P2` and never re-derived |
| **an rlxfw cell from the same instrument as ②** | 🟢 **met**, and it is the clause that cost the seating: `R9-7` ran the same tool, host, cable and port as `R9-6`, in the same episode. ⚠️ Two anchors publish an rlxfw cell from the `P2` image, which predates `R7`, and say so in the cell |
| **a check that would have detected the opposite of the row's claim, with that check's reading; a row without the reading publishes 未定** | 🟢 **met as a refusal rather than as a count**: 量 publish × ④ over 141 rows gives `win`/reading 17 and `win`/no-reading **0**, with zero rows missing the field. 🔴 The clause's value is that 77 rows publish 未定, which is the outcome the old clause could not produce |
| **the gate fails if the renderer accepts a planted row saying 「我的設計修好了這條」, a mechanism outside the closed set, or an evidence link that does not resolve — all shown firing before any real row renders** | 🟢 **met**: the five guards are shown firing on planted rows, and the permitting side is shown too (`P1` accepts a `平台限制` row, `P5` renders the two anchors that publish vendor symbols in full) |
| **the vendor column is static, network-facing or boot-console evidence and never a test run on the vendor firmware** | 🟢 **met**: 量 no command was typed into the vendor firmware, because 讀 it has no shell; every vendor cell is `V-A` (a host-side request), `V-B` (the dump-derived tree) or `V-C` (a boot console already captured) |
| **a row whose tier carries no executable refutation may not claim absence at all** | 🟢 **met**: 量 5 rows publish `surface-absent` and 42 publish `not comparable`, neither of which is an absence claim about behaviour |

### The questions this gate must be able to answer

The plan's `R9` row is the differential proof. Entry 19 answers *what does rlxfw do differently, by
mechanism class, with both columns from one instrument* at class level on 16 rows. It does **not**
answer *is rlxfw more secure*: that question needs the five uncontrolled variables controlled, and
they are not. 讀 `docs/differential.md` § 2 names them — kernel config, libc, toolchain, userspace
population and service set — and column ③ cannot tell a design decision from any of the five.

### What `R9` did not establish

🔴 **That the live column covers the cases it is drawn from.** 68 of 89 `V-A` rows have no probe,
and nothing in the published table speaks for the 52 rows in `V-B`, `V-C` and `V-D` beyond their
tier and their publish verdict. The exemptions are named and reasoned, in six blocks — 31 whose
stimulus is a `/boafrm/` handler or named CGI that the probe list's own refusals bar, 7 held
upstream, 11 whose subject is not a TCP reply this instrument can send, 12 cut upstream, 6 whose
subject is this project's own instrument, and 2 — but a named exemption is not a reading.

🔴 **That the vendor firmware's behaviour was tested.** It was *probed*, from the network, with no
command typed into it. Every statement about the vendor's internals here is 讀 — from its own
shipped bytes, its boot console or upstream's instruction-level work, which is not this repository's
instrument and has not been reproduced here on the same population.

🔴 **That the flash bracket would detect a small write.** 量 the level-0 digest `ae87ac03…` is equal
before and after, and group 0 at 4 KiB is equal at `44355799…`, with `n_writes` 0 on both sides and
`map_hashed` 4,186,112 bytes with `H601`'s 8,192 skipped. 推 nothing about sensitivity: two equal
digests over unchanged flash say nothing about whether a small write would show, and a sensitivity
control needs a known change, which is a write. It cannot see two writes that cancel, or any byte
outside the units read. `FLS-26`'s ledger does not move, and `H601` is never hashed (`FLS-31`).

🔴 **That the held items are answered.** 量 16 of 141 rows are marked held and they name 12 of the
13 held upstream ids — `D-11` is named by no row, which is why the guard keys on the id set as well
as the flag. Those rows reach the table as counts. Whether rlxfw answers their mechanisms is not
published and will not be while they read held: the report has not been sent, and `plan/` § 15
forbids a class-level row that is in substance a named reproduction.

🔴 **That `quiet-swcore` runs.** 量 neither arm of `R9-5` has booted; `quiet-swcore` has never
booted on the silicon, and `rtkimage` was never run on either. `.bss` grows 1,356,544 bytes at
`SWCORE=y` and no measurement here bounds what that does to a running board. "0 differences outside
`S`" is an **attribution, not a cause**: rule `R3` reads kbuild's own dependency stamps, so it
establishes that the flip *can* explain a difference, not that it *is* the difference; a per-object
preprocessed-output diff would settle it and was not run. The 12,629 address-only symbol differences
were counted and set aside, not explained.

🔴 **That the DoD's two figures for the WLAN driver are right — and one of them is not.** The step's
own DoD said *40 symbols gone, shorter `sk_buff`*. 量: the loss is **11** symbol-table entries —
four functions (`rtl8192cd_isIgmpV1V2Report`, `rtl8192cd_isMldV1Report`, `rtl8192cd_proc_vlan_read`,
`rtl8192cd_proc_vlan_write`) plus their section and relocation symbols — and **6** undefined
references, not 40. 推 the 40 in the DoD is the kconfig count (量 840 − 800 = 40), which counts a
different kind of object. `sk_buff` is **8** bytes shorter, 量 off `skb_init`'s instruction stream
(192 against 200, cross-checked by the fclone immediate 388 against 404) against 讀 12 bytes of
declared field — and the remaining 4 are **未定**, 推 alignment padding, unmeasured. The qualitative
half of the DoD stands and is now quantified; its arithmetic did not.

🔴 **That `R9-4` produced a column.** The step's brief was *the `V-B` static column from instruments
that already exist*, and 量 that column was already complete when the step opened: `R9-1` and `R9-2`
had put all 141 rows' ②③④ in the register, and `tools/fixcases.py` `C4`/`C7` already passed over it.
Closing the step on the column's existence would have been the same defect as the old `通過` clause,
one level down. So `R9-4`'s content became `FW-20`'s two 殘留 — the only `V-B` facts the register
had not read — which landed as `FW-199` (`bin/boa` neither drops privilege nor chroots, 讀 from four
independent sources) and `FW-200` (the setuid/setgid census off the image itself). ⚠️ An import
census is not exploitability: `system` being linked is not `system` being reachable from a request,
and the row that would claim otherwise publishes undetermined.

🔴 **That a 推 this gate wrote survived it.** `FW-198` carried the inference that `P2`'s unexplained
31-same/1-DIFFER in group 0 is explained by `FW-196`'s write to `AUTHG_IP_ADDR` at `0x00C000`. 量
inside the same gate, over committed captures and with no power at all: the population is every
`bench/**/*.log` carrying `^map_level 0`, compared only when the matched body-line count equals the
capture's own `map_lines`; **46 captures qualify** across 22 date directories from
`bench/2026-09-08b` to `bench/2026-10-04`, and **all 46 carry the identical 32-line body digest
`ae87ac03269985d6`**. So the whole-chip map at 128 KiB has not moved once in 26 days, including both
of `P2`'s vendor seatings, and there is no change for `FW-196` to explain; the single `DIFFER` is a
standing device-versus-dump difference whose own fourth field reads `dump`, present already in the
earliest qualifying capture. At 4 KiB it fails a second way: 讀 group 0 is 30 same / 2 DIFFER and
the two differing units are `009000` and `00D000` — **`00C000`, where `FW-196` writes, is SAME.**
`FW-201` records the measurement and `FW-198`'s 推 is retracted. 🔴 **Two of the extraction patterns
that produced plausible numbers first had to be caught**: `^DIFFER` missed lines carrying two
leading spaces, and `[0-9a-f]{6}` missed the 12 of 32 offsets with an uppercase hex letter, while
the positive control passed because it used `000000`, which is all digits. A control has to carry
the characteristic that varies. The residual is not nothing: `00D000` *is* inside COMPCS, so a
vendor configuration write before the dump baseline stays a live candidate for the dump divergence
— it simply cannot be attributed to `P2` or to this segment's episode. `009000` is unexplained and
`FLS-26` holds it ⊘.

🔴 **That `R8b` is any closer.** Nothing here writes flash, so nothing rlxfw writes has been shown
to survive anything — the same residual `R8a` → `R7` → `R8` have each carried. 量 there is no write
path in any built image: 讀 `config/rlxfw-marks.tsv` `MK5` gates `rtl819x-spi-write.o` on
`CONFIG_MTD_RTL819X_WRITE`, and 量 `R9-5` found that object absent from both staged trees.

### `R9-11`: the five deliverables that do not complete, and the one test they all fail

Plan § 17 keeps three categories apart — `出於自願的範圍外`, `卡在儀器上（會產出可檢查的事實，只是
現在做不到）` and `刻意換掉（前置都滿足了，但不划算）` — on its own stated ground that collapsing
them is how *I chose not to* becomes *I could not*, which is the flattering direction. The test
applied to each item is: **does the blocker survive the owner's dated yes, or an act of the
owner's?**

| item | the blocker | survives a yes? | category |
|---|---|:---:|---|
| `cvewatch` | the owner's rule of 2026-09-26 — a new checker only for bricking, an `H601` leak or a misjudged result | **no** | `出於自願的範圍外` |
| `docs/disclosure.md`'s findings half | the report has not been sent | **no** | `出於自願的範圍外` |
| the demo recording | nobody has pressed record | **no** | `出於自願的範圍外` |
| `study/QA.md` as a repository deliverable | `.gitignore`'s `study/` line, and `CLAUDE.md`'s rule against a committed file written for a hiring panel | **no** | `出於自願的範圍外` |
| `VDR-1`/`FW-67`'s silicon halves | a flash write, barred by the zero-write mainline and by the owner's serial order | **no** | `出於自願的範圍外` |

🔴 **All five come out the same way, and that is the finding rather than a coincidence: not one of
them is waiting on an instrument.** Each blocker is a decision — the owner's rule, the owner's send,
the owner's camera, the owner's `.gitignore`, the owner's zero-write mainline — and filing any of
them `卡在儀器上` would be exactly the substitution plan § 17's header warns about. 🔴 The test's
boundary is shown rather than asserted: `FLS-24` (`SPEC.md` § 17) is the one row that survives it,
because what is missing there is **money, not permission** — a second unit of this model — and plan
§ 17 item 8 already filed *reproduction on a second machine / a spare / the first thing bought when
the budget loosens* under `卡在儀器上`, so that row follows the precedent rather than re-deciding it.

**What is not ⊘'d, item by item, because naming the half matters:** citing CVE ids as prior art
continues and the register keeps its rows — what is declined is a *watcher*; `docs/disclosure.md`'s
**process** half is desk-doable and resolves a dangling pointer, 量 § Release clock points at a file
that does not exist; the demo **script** is committable as data, bounded by two things — plan
`ARTIFACTS.md`'s 0:15 and 2:15 beats cannot be committed captures, because every evidenced path into
vendor userspace opens with a flash write, and `tools/replay-capture.py` hardcodes one reel path, so
a second reel file is read by no control; `study/QA.md` can be written at the desk tonight, and
*cannot complete* is simply false for it; and `VDR-1`'s qemu-user rehearsal costs neither flash nor
power. ⚠️ Each of those is a half **named**, not delivered. And 讀 **no tool reads a category**: the
set is held by convention, so a mis-filed one is invisible to every check in this repository.

### The main session's rulings in this gate, which the owner may override

The owner continued the relaxation of 2026-09-27 and 2026-09-30 and asked for the decisions to be
taken; the flash rules, `H601`, the power handshake and `NET-165` are the owner's own and are not
listed.

1. **`R9-4` re-scoped from *produce the `V-B` column* to *read `FW-20`'s two 殘留***, because the
   column already existed and was already guarded, so closing on its existence could not fail. The
   alternative — close `R9-4` on the register as delivered — was rejected for that reason.
2. **The vendor seating was taken in the 120th segment rather than the next**, and in the reverse
   order to the plan: rlxfw's column first, because the board was already running rlxfw, which took
   the one-shot resource off the critical path. One power action, for the single reason that the
   vendor firmware has no shell and cannot be told to reboot.
3. **`FW-198`'s 推 was retracted by measurement inside the gate that wrote it**, rather than carried
   to a later gate. A record keeps what it said: `FW-198`'s own entry stands and `FW-201` is the new
   row.
4. **The ⊘ list files all five items as `出於自願的範圍外` and none as `卡在儀器上`**, on the test
   above. The owner may hold that the zero-write mainline is a constraint rather than a choice; the
   ruling says it is a choice because `CLAUDE.md` makes a flash write exactly the owner's explicit
   yes and `cardcheck` already carries the mechanism (`FW-113`).
5. **`P3`'s row moves to `~` and not to `✓`.** 讀 `README.md` owns version → contents and defines
   `v1.0` as `R8` + `R8b` + `R9` + `P3` + `P4b`, and the `P3` row closes at `v1.0`, so `R8b` sits
   between `P3`'s report and `P3`'s close. Marking it `✓` would also orphan `LA-1`, whose only owner
   is `P3`.

### The booking: what moved to another gate, and what was declined

**Re-owned in the closing commit, because leaving them on a closed `R9` makes each read `ORPHAN` in
`cfcensus`** — 量 three § Carried forward rows named only `R9` as a live owner:

| row | to | why |
|---|---|---|
| `FLW-1` | **`P4b`** | the scanner it asks for guards a **publication**: `flashwin scan` runs only at the desk, and the moment a committed digest of a forbidden window matters is the push. ⚠️ The owner's rule of 2026-09-26 names this row **in** rather than out — an `H601` leak is one of the three things a new checker may be written for — so it needs no ⊘ |
| `LEDGER-1` | **`P4b`** | and the first re-owning's reason was an analogy rather than a requirement: `R9`'s differential is between two *firmwares*, not two *commits*. The row's own open decision ③ — whether *in history, not in `HEAD`, in scope* is red — is a question about what the published per-file modification record must contain |
| `VDR-1` | **a standing instruction**, `R9` struck, with the **silicon half only** ⊘ | the qemu-user rehearsal the row itself names costs neither flash nor power and is unscheduled, so a whole-row ⊘ would retire work that is merely unscheduled |

**Declined in the closing commit**, both in `SPEC.md` § 17: `FW-67`'s remaining half — the vendor
*shipped object's* runtime exposure — with its 推 narrowed in the same commit rather than left wide
(量 `NET-33` and `NET-100` drove that handler on this die, but on rlxfw's own build of the vendor
source, and 讀 `CONFIG_RTL_DEBUG_TOOL` is `dep-unmet` in today's derivations, so the instrument is
absent from the current image); and `FLS-24`, the one row filed `卡在儀器上`.

⚠️ **Flash.** 量 across both segments: one power action, the vendor seating of 2026-10-04; uploads
each made after `DW 8040D4A0` read `00000000` with the loader answering ARP and the staged head read
back equal to the file before each `J`; **no `FLW`, `EW`, `EB`, non-zero `AUTOBURN` or `FLR`
issued**. `n_writes` reads 0 on both sides and is stated as carrying no information (`FW-142`) and as
blind to the vendor's own write path. What that cannot see: two writes that cancel, every byte
outside the units read, and `H601`, which is never hashed. The `FLR` bracket stays at 1,024 of
4,194,304 bytes = **0.0244 %**.

---

## 2026-10-08 — `R8b` (an update written to a flash slot boots through `rlxboot`, ten power cuts inside a slot write each boot the other slot, and the stock loader's rootfs rule found by the gate failing once)

### One line

**v0.6+, three segments — the 124th for the opening and `R8b-0` to `R8b-4`, the 125th for the
seating (`R8b-5`, `R8b-6`), the 126th for `R8b-7` and this closing — and twenty-five power
actions, all in the 125th.** § Gate board leaves `R8b` uncosted for `R1h`'s reason, `R8`'s 18
already carrying the work, so there is no estimate to divide by; the desk work orders the 122nd
and 123rd segments ran before the gate opened are not counted. One seating, 2026-10-07, read both
clauses of the row on the die. **An update written to a flash slot boots through `rlxboot`**:
container P (version 1) in slot A gives `RLXBOOT-SLOT A` and `RLXFW-ID0=F9ADC9E8`, the id the
build manifest records (`T2ra`); Q (version 2) beside it in slot B boots B, the higher (`T3a`);
R (version 3) in A boots A again (`F05`). **Ten power pulls inside a slot write each booted the
other slot**, 10 of 10 by `tools/bootslot.py`, with no control round, no refusal and no halt. A
torn `rlxboot` hands over to its rescue copy through the stock loader's own scan (`RD05`,
`RLXBOOT-FROM 05020000`). Every write went through the RAM-booted armed image's install path,
each under the owner's dated yes for that exact string: 33 driver write verbs, of which 20
completed and read back equal, 11 were stopped by a pull and 2 were refused before any operation;
no `FLW`, `EW`, `EB` or non-zero `AUTOBURN` was sent.

**The gate failed once, and that failure is its most consequential reading** (`FW-241`, the
main session's row): behind a `cr6c` header the stock loader also looks for a rootfs, at eleven
candidates that all lie inside slot A, and returns nothing when none is there — so once slot A
held a container the board stopped at `<RealTek>` silently (`T2a`). `rlxboot` and its rescue
copy were re-installed as `cs6c`, which the locator returns without that search, and every boot
after that is on `cs6c`; the repository carries the change in `f257a848`, whose tree rebuilds the
device's `rlxboot` and rescue bytes exactly (build `127a71cf`, `14cebbf5…`, `0c9db2ec…`). That
commit moves the mainline `RECIPE_ID` from `f9adc9e8` to `6a11de02` (the install header compiles
only under `CONFIG_MTD_RTL819X_WRITE=y`), and 量 the `6a11de02` `vmlinux`, built twice
byte-equal, differs from `f9adc9e8`'s in 8 of 4,588,247 bytes — the recipe id, twice — with
`System.map` identical (`FW-254`). **Every reading here is on `f9adc9e8`**; `v1.0` ships
`6a11de02`, to be qualified on the device at a later seating.

**The weakest thing here is that all ten pulls cut a paced write, and the pace is most of what
they cut.** 量 from the ten paced captures' own progress lines, as slopes: an erase block's line
arrives every 2,415 ms and a program block's every 2,170 ms, against `pace=2000`, so about 415 ms
of each erase step and 170 ms of each program step is flash work and the rest is the sleep the
pace inserts (`FW-246`). 推 a pull landing uniformly in time lands in that sleep about 83 % of the
time in the erase phase and 92 % in the program phase, and the record cannot say which pulls did
not: the console prints a block's end, never the moment of the cut. So the torn states measured are mostly
*block k finished, block k+1 not started*; a cut inside one sector erase or one page program is
covered by the design's argument — page 0 is erased first and programmed last — and not by a pull.
No pull was made on an unpaced write, which takes 10.26–11.24 s and is the one an update uses.

### Three claims that stand

**① An update in a flash slot boots through `rlxboot`, and of two valid slots the higher version
boots.** 量 `bench/2026-10-07` (`FW-242`). After the `cs6c` re-install, `T2ra` read, verbatim:
`RLXBOOT-FROM 05010000` · `RLXBOOT-KEY prod 4a6eda72…3096e` · `RLXBOOT-CTRSRC flash` ·
`RLXBOOT-READ A flash=00070000 buf=81000000 n=1109152` with sixteen progress dots · `HDR ok` /
`SIG ok` / `DIGEST ok` / `VER cur=1 ctr=0 ok` · `RLXBOOT-VERDICT A ok ver=1` · slot B `HDR
bad=magic` · `RLXBOOT-SLOT A` · `RLXBOOT-BOOT load=80500000 entry=80500000` · `RLXFW-ID0=F9ADC9E8`.
`T3a` with both slots holding containers read `VERDICT A ok ver=1`, `VERDICT B ok ver=2`, `SLOT B`;
`F05`, after R went into slot A, `VERDICT A ok ver=3`, `VERDICT B ok ver=2`, `SLOT A`. 🟢 **The
verdict is a tool's, not a reader's**: `tools/bootslot.py judge` checked the loader's candidate,
the key, the read/verdict order, each slot's address and copy, the stages behind every `ok`, that
`rlxboot`'s choice follows from its own verdicts, the jump, and the id the board printed against
the build manifest's `recipe_id`, and read PASS on all 18 `rlxboot` runs from flash in the seating
(`T1b`, `T2rb`, `T3b`, `RD06`, `RD09b`, ten `…J`, `BCJ`, `ACJ`, `F05b`); on `T2a`, which never
reached `rlxboot`, it read REFUSED, which is the right answer. 量 off the captures' `.timing` (the
`FW-35` rule): `RLXBOOT-V1` to `RLXBOOT-BOOT` takes 2.62 s with two full verifies and 1.38 s with
one, so one slot — 1,109,152 bytes read, hashed and its signature checked — costs about 1.3 s
(`FW-250`). ⚠️ What this does not reach: one container recipe, one key, and a counter that read
`ctr=0` in every boot; the signature under the production key is checked by `rlxboot` on the die,
and the payload's integrity at install time by the kernel's sha256, never by the loader.

**② Ten physical power pulls during a slot write each booted the other slot.** 量 (`FW-243`). The
design makes the boot itself the reading (`LOG.md` 2026-10-05): each pull cuts a write of the slot
that would win if the write completed — slot B ← Q (version 2) while A holds P (version 1), then
slot A ← R (version 3) while B holds Q — so a torn write boots the other slot and a completed one
the written slot, and the target slot was first rewritten unpaced and read back (`…Rb`, `cmp=1`)
so a cut before the first erase would read as a control. Where each pull landed, from the last
`RLXFW-SI` line of each `…Pb` capture before 32 s of silence ended it:

| round | write | last line before the cut | boot (`…B`) | `bootslot` |
|---|---|---|---|---|
| B1 | slot B ← Q, `pace=2000` | `E 03 7750` | `VERDICT A ok ver=1`, `VERDICT B bad=magic`, `SLOT A` | PASS |
| B2 | 〃 | `E 11 27120` | 〃 | PASS |
| B3 | 〃 | `P 06 56790` | 〃 | PASS |
| B4 | 〃 | `P 06 56920` | 〃 | PASS |
| B5 | 〃 | `P 09 63480` | 〃 | PASS |
| A1 | slot A ← R, `pace=2000` | `E 02 5360` | `VERDICT A bad=magic`, `VERDICT B ok ver=2`, `SLOT B` | PASS |
| A2 | 〃 | `E 10 24560` | 〃 | PASS |
| A3 | 〃 | `E 16 39140` | 〃 | PASS |
| A4 | 〃 | `P 03 50250` | 〃 | PASS |
| A5 | 〃 | `P 14 74220` | 〃 | PASS |

Every boot printed `RLXFW-ID0=F9ADC9E8`. 🟢 **The other half of the design was shown too**: `BCc`
(slot B rewritten unpaced, `BCi`) booted B over A, and `ACc` (slot A ← R unpaced, `ACb`) booted A
over B — so a write that completes does win, and the ten boots of the other slot are not what
`rlxboot` would have done anyway. ⚠️ All ten torn slots failed at the same check, `HDR bad=magic`,
because the header page is the last one programmed (`D5`); `rlxboot`'s signature and digest
refusals were never reached by a torn slot on the die.

**③ When `rlxboot` is torn the stock loader reaches the rescue copy, and when it finds nothing it
will boot it stops at its own prompt — both on this die, the second by accident.** 量 (`FW-242`,
`FW-241`). `RD03`, a `pace=30000` install of `rlxboot`, was cut after `RLXFW-SI E 00 370
paced=30000`; `RD07a` read `0x010000` as `FFFFFFFF` ×4; `RD05`, the next power-on with no ESC,
read `RLXBOOT-FROM 05020000` and `SLOT B`, PASS; `RD08b` put `rlxboot` back (`cmp=1`) and `RD09`
read `RLXBOOT-FROM 05010000` again. The second half is `T2a`: after slot A's first write, a
`busybox reboot -f` with no ESC printed the banner, `P0phymode=01, embedded phy`, `---Ethernet
init Okay!` and `<RealTek>` 0.34 s later — no `Jump to image`, no `---Escape booting by user`;
`X-T2-dba4` read the ESC flag at `0x8040DBA4` as `00000000` and `X-T2-dd3c` read `0x8040DD3C` as
`05010000`, so the loader had accepted `0x010000` and returned nothing for it. The board was
recovered without a power action: `AR3` RAM-booted the armed image from that prompt nine minutes
later, and `K1b`/`K2b` re-installed `rlxboot` and its rescue copy as `cs6c`. 🟢 **The loader region
was never touched**: `map 1 0` read units `0x000000`–`0x005000` equal to the opening baseline at
five points — before the first write, after `W2`, after `W4`, after `K2b` and at the end (`X-A04f`,
`X-W2c-m0f`, `X-W4c-m0f`, `X-K2c-m0f`, `X-F-m0f`). ⚠️ `T2a` reached the prompt through the
locator's rootfs search, not through six content-invalid candidates; what each half shows is
below, under `C-4`.

### The board row's clauses, read one at a time

| the row says | verdict |
|---|---|
| **an update written to a flash slot** | 🟢 **met**: `W3b` slot A ← P, `END OK rc=0 cmp=1 ms=10260`; `W5b` slot B ← Q, `ms=10680`; `ACb` slot A ← R, `ms=11180`, each a whole-region read-back equal to the staged bytes and then `0xFF` (`inst_cmp_bytes 1179648`, `inst_cmp_diff 0`) |
| **and booted from it through `rlxboot`** | 🟢 **met** on `T2ra`, `T3a`, `F05` and the two closing controls (claim ①). ⚠️ Only after `rlxboot` went to `cs6c`: as first installed (`cr6c`) it booted only while the vendor's SquashFS sat at `0x180000` (`T1a`), and stopped booting the moment slot A held a container (`T2a`, `FW-241`) |
| **ten physical power pulls during a write** | 🟢 **met**: ten, B1–B5 and A1–A5, each landing between the write's first and last progress line (claim ②) — ⚠️ all inside writes paced at 2 s per 64 KiB block |
| **each followed by a boot from the other slot** | 🟢 **met**, 10 of 10 by `bootslot`, with `RLXFW-ID0=F9ADC9E8` in every boot |
| *(entry 16's refutation)* any one that enters no slot means the A/B design has a hole | **did not fire**: 0 halts, 0 REFUSED, 0 control rounds |

### The plan's preconditions, as entry 16 booked them

| the plan's precondition | where it stands at this close |
|---|---|
| **①** the rescue drill done | 🟢 **its `rlxboot` half, on the stock loader's own scan** (claim ③). ⚠️ Not its state-block half — `0x3F0000` written to garbage and a TFTP rescue walked and timed: `D3` writes no state block. A TFTP rescue *was* walked, unplanned, after `T2a` (`AR3`, then `K1b`/`K2b`), and was not timed as a drill |
| **②** `burn()`'s flash target read out | unchanged: met at the desk before this gate; `C-3`'s question about its callees is declined below, because nothing in rlxfw reaches `burn()` |
| **③** a destination in a forbidden range refused, with a positive control | 🟢 **by construction, on the host**: format 2 signs `flash_at`, the install path refuses a container whose `flash_at` is not its region's base, and the region table is compiled in (`notes/spi-mtd-driver.md` § 13.2). ⚠️ The refusals exercised **on the die** are two — `Z03`'s `SHA` and `BCb`'s `UNARMED`; every other refusal is the host suite's |
| **④** the main write path is rlxfw's own MTD driver | 🟢 **met**: every write went through `rtl819x-spi`'s install path in the armed image; the loader's write verbs were never sent. ⚠️ That path exists only in an image RAM-booted through the loader: the mainline image in the slots has none (`MTD_CAP_ROM`, `CONFIG_MTD_RTL819X_WRITE=n`) |
| **⑤** with the kernel region garbage, the loader still reaches its rescue path | 🟢 **in practice, by `T2a`**: a locator result of 0 left the board at `<RealTek>` with no ESC and no message, and the prompt carried the recovery. ⚠️ The trigger was the rootfs search, not garbage at all six candidates; the `C-4` extension that would have torn both `rlxboot` and the rescue copy was not run |

One input entries 16 and 18 called unread, and one this gate's step list called 未定, now have
readings. `bank_offset`: the loader found `rlxboot` at `0x010000` and the rescue copy at
`0x020000`, where a zero offset puts them (`FW-241`). The erase size, which `R8b-5`'s hazard
column named: **4,096 bytes** (`FW-244`) — `E02`'s single
`SE` cleared the marker at `+0x0000` and left the one at `+0x1000` (`m=EII`, so at most 4,096),
and `W4b` erased 262,144 bytes that held only 883 `0xFF` before it (`FW-225`) with 64 `SE`s at a
4,096-byte stride and read all of them back as `0xFF` (so at least 4,083, and 4,096 for any
power-of-two erase unit).

### The steps' DoD, read one row at a time

| the DoD says | verdict |
|---|---|
| **`R8b-0`** the board row reads `~` and names this list | 🟢 met 2026-10-05 |
| **`R8b-1`** a host test per case, `qemutest`, and the flash build shown refusing and building | 🟢 met at the desk 2026-10-05 (`94d97924`); the runners that could not fail were repaired first (`FW-234`). On the die: 17 slot boots and one halt (claim ①) |
| **`R8b-2`** each guard shown refusing and permitting; a mainline image's driver code unchanged | 🟢 met at the desk (`a6add876`, `FW-236`); on the die the guards permitted 31 writes and refused 2 (`Z03`, `BCb`) |
| **`R8b-3`** every digest recorded, two builds byte-equal | 🟢 met 2026-10-05 for P, Q, R, `rlxboot` and the armed `75cfa588`. ⚠️ The armed image that wrote after `T2a`, `6b1bde59` (A == B), was built from a clone-only commit (`c05e2671`); 量 2026-10-08, `f257a848`'s `config/` plus the armed flip is that commit's `config/` file for file, so its recipe is reproducible from the repository — the build itself was not repeated |
| **`R8b-4`** one `owner-yes` row per payload, and `cardcheck` reading them | 🟢 met: `R8B-CARD.md` carries eleven rows (nine dated 2026-10-05, the two `pace=2000` strings 2026-10-07), `R8B-CARD-2.md` seven (three `cs6c` strings dated 2026-10-07). ⚠️ `R8B-CARD-2.md` was generated mid-seating and committed after it, under the relaxation in force; `LOG.md` records `cardcheck` refusing its four unsigned cells and then passing, and that output is not committed |
| **`R8b-5`** every write read back and every boot identified by tool | 🟢 met: 20 of 20 completed writes read back equal; every boot capture judged by `bootslot` |
| **`R8b-6`** ten boots read `RLXBOOT-SLOT` and `RLXFW-ID0` by tool | 🟢 met, `B1J`–`B5J`, `A1J`–`A5J` |
| **`R8b-7`** `cfcensus` and `spec-check` green on the closing tree | 🟢 met 2026-10-08 on this entry's tree: `cfcensus check` 0 findings and `ratchet` at baseline, `spec-check` rc 0 |

### The step list's hazard column, read one at a time

* **`R8b-1`, the delay of two verifies through the flash window, which no desk test measures** —
  measured: 2.62 s from `RLXBOOT-V1` to `RLXBOOT-BOOT` with two full verifies, 1.38 s with one,
  0.10 s for two `bad=magic` refusals (`T1a`); `busybox reboot -f` to the mainline prompt about
  15.6 s (`FW-250`).
* **`R8b-2`, the write rate, which decides whether a hand can land a pull inside a write** — it
  decided exactly that: an unpaced slot write takes 10.26–11.24 s over thirteen installs, so the
  pulls needed `pace=2000`, which stretches a slot write past 74 s — 推 about 82 s to `END`,
  projected from the progress lines and the pace rule, because no paced slot write ran to its end
  (`FW-246`).
* **`R8b-3`, the release recipe moving after these builds** — it moved: `f257a848` takes mainline
  from `f9adc9e8` to `6a11de02`, and the armed recipe moved from `75cfa588` to `6b1bde59` in the
  seating. Nothing here was read on `6a11de02`; that image is built and differs only in the id
  (`FW-254`).
* **`R8b-4`, an ordering step that needs the vendor kernel after it is gone** — it fired, in a form
  nobody had written down: `T1a`, the first flash boot of `rlxboot`, needed the vendor's SquashFS
  in slot A's range, and `W3` removed it. It cost no power action, because the loader stops at its
  prompt.
* **`R8b-5`, the erase size (未定, `FW-227`)** — 4,096 bytes (`FW-244`), and the `STOP` rule written
  before the reading passed on all four terms: `se_bytes=4096`, `clean=1`, `inst_reason OK`, and
  `se_polls` 8,664 against a ceiling of 25,000.
* **`R8b-6`, a pull that lands outside the write** — none did: the earliest pull came after `E 02`
  at 5.36 s, the latest after `P 14` at 74.22 s.

### The questions this gate must be able to answer

Entry 16 left three of the plan's `R8` questions to this gate.

**③ 「你的 `rlxboot` 壞了會怎樣？」** The stock loader's scan passes the torn region and boots the
rescue copy at `0x020000`, a byte-for-byte copy of `rlxboot` but for its `burnAddr`; `rlxboot`
prints the candidate the loader accepted, so the hand-over is on the console (`RD05`). ⚠️ The torn
`rlxboot` was erased, not corrupted with a valid header; a `rlxboot` that is signed and wrong is not
this drill.

**④ 「寫到一半斷電會怎樣？」** The slot being written fails `rlxboot`'s first check — its header
page is erased first and programmed last — and the other slot boots: ten pulls, ten boots of the
other slot. ⚠️ At ten points of paced writes, with the caveat in the weakest-thing paragraph.

**⑤ 「只有一台機器你敢寫 flash？」** Yes, on three conditions this gate kept and measured: the loader
region is never named by any write path and read equal at five points; every write is a dated yes
for its exact string, checked by `cardcheck` before power and by the kernel's sha256 at install;
and the floor under every failure is the loader's own prompt, which this gate reached by ESC on 19
boots and once, on `T2a`, with no ESC at all.

### What `R8b` did not establish

🔴 **That rlxfw can update itself.** Every write was made by the armed image, RAM-booted through
the loader's TFTP (`J 80500000`, 20 times) and fed over `nc`; the mainline image that runs from the
slots has no write path. What is established is a provisioning procedure that needs the console,
the loader prompt and a host — not an update the device performs. For the same reason nothing the
running firmware writes persists: `R7`'s config store is still on ramfs, waiting for an MTD backing
that this gate did not give it.

🔴 **That `v1.0`'s image boots from flash.** The slots hold mainline `f9adc9e8`. The `6a11de02`
image is built (`a3a75f8c…`, two builds byte-equal) and differs from it in the recipe id alone
(`FW-254`), but it has not been signed, written or booted: that is the qualification seating's.

🔴 **That a cut at any point of a write is survivable.** Ten points: five in the erase phase, after
`E 02`, `E 03`, `E 10`, `E 11` and `E 16`, and five in the program phase, after `P 03`, `P 06` twice,
`P 09` and `P 14`. None inside block 0's erase, none in the last six seconds before the header (推
the header page at about 80.6 s, after `P 16` and its pause), none during the header page, none
during read-back, none on an unpaced write — and most of what was cut was the pace's sleep. Every
torn slot read `bad=magic`.

🔴 **That rollback is refused from flash.** `D3` writes no state block, so the counter at
`0x3F0000` was never advanced: `ctr=0` in all 17 slot boots. A lower version installed in both
slots would boot. The monotonicity entries 16 and 18 called asserted and never exercised stays so.

🔴 **That every candidate content-invalid reaches the prompt.** The `C-4` extension — tear `rlxboot`
and the rescue copy both, then power on — was not run. `T2a` measured the branch it ends in, by
another route.

🔴 **The last bracket and the expected image.** `F02`, three `FLR`s at `0x000000`, `0x030000` and
`0x060000`, was not carried into the continuation card and did not run. `map 1 21` and `map 1 31`
did not run either, so `0x2B0000`–`0x2BFFFF` is not shown unchanged at 4 KiB: group 21 differs as a
whole because slot B ends at `0x2AFFFF`. And the changed groups were not compared against an image
built at the desk: each region's own read-back, at the moment it was written, is the evidence for
its content.

⚠️ **The `cs6c` rule's reach.** It was measured in one flash state — slot A holding a container,
the vendor rootfs gone — on one loader build; that `cs6c` boots in any other state is 讀
(`FW-241`'s own caveat).

⚠️ **What ESC does with `cs6c` installed.** Every ESC-streamed reboot after the re-install printed
`---Escape booting by user` (16 of 16), which no ESC-streamed capture in this repository had done
before with a bootable `cr6c` first (0 of 238, ten of them at the same 20 ms period); the banner to
`Jump to image` shortened from 4.97 s (`T1a`) to 2.02 s. `docs/FINDINGS.md`'s reading (the ESC
poll that sets `0x8040DBA4` sits in the rootfs scan) predicts it (`FW-249`). The prompt was reached
every time; `C-13`'s sentence that the flag makes the loader declare every image bad does not
describe a `cs6c` image.

⚠️ **The erase size and the times.** 4,096 rests on `E02`'s upper bound and on `W4b`'s read-back
over the barrier's pre-erase content as `FW-225` read it in two dumps and `A04` confirmed at 128 KiB
— arithmetic over two measurements. The times are conversions: one `SE` about 21.5 ms and one page
program about 0.36 ms from poll counts, and the 200,000-poll ceiling about 0.50 s, all assuming a
busy poll costs what an idle one does (推); page and block size were not touched (`FW-244`,
`FW-245`).

⚠️ **Instruments the tree does not hold.** `cell.py`, `stage.sh` and `mkcard2.py` (session tools
under `$FWRE_WORK/rebuild/s125/`), the `FLR` pre-reads (`$FWRE_WORK/rebuild/bench-only/`), the
comparison of `L03`–`L10` against the dump, and the clone-only commit `c05e2671` that built
`6b1bde59`. Two of the session tools were
wrong during the seating — a short `img_len` read too early (`FW-248`), an unchecked `arm` cell's
rc (`FW-251`) — and both were stopped by a guard before a byte was written.

⚠️ **One unit, one part (`1C7016`), one loader build, one evening**; the pull timing was a hand on
a switch after a spoken *now*; no voltage was read, so `P3`'s power tree stays undelivered.

⚠️ **Flash.** 量, counted over the 338 `.meta.json` `sent` fields and the 20 upload records of
`bench/2026-10-07`: `FLW` 0, `EW` 0, `EB` 0, non-zero `AUTOBURN` 0 — `AUTOBURN 0` was sent 20
times, once per upload, and `0x8040D4A0` read back `00000000` 20 times before each; `FLR` 4,
`L07`–`L10`, each through `tools/flrbracket.py run` with a pre-read that differed from flash. The
driver's write verbs: 33 sent — 20 completed with a whole-region read-back equal, 11 stopped by a
pull after at least one 64 KiB erase block, 2 refused before any operation (`Z03`, `SHA`, rc −77;
`BCb`, `UNARMED`, rc −13; `n_writes 0` after each). The bracket's reach: `F03b`'s `map 0` hashed
4,186,112 bytes — all but `H601`'s 8,192 — and groups 22–31 equal the opening `A04`, which equals
the 2026-08-16 dump outside group 0's known `FLS-26` units; groups 0–21 changed, exactly the
groups that hold `0x010000`–`0x2AFFFF`; `X-F-m0f` read group 0's units equal to the opening
baseline except `0x010000`–`0x01F000`. Power: 25 actions, counted from the captures — 13
power-ons, each a capture with `Booting...` and no `Reboot Result from Watchdog Timeout!` (`C03`,
`T1d`, `RD05`, `B1B`–`B5B`, `A1B`–`A5B`), and 12 power-offs, one before each of those but the
first. What none of it sees: `H601`, never hashed, and two writes that cancel.

### The main session's rulings in this gate, which the owner may override

The owner's own — opening `R8b` on 2026-10-05 with `P3` and `P4b`, each flash write a dated yes
for its exact string, holding the production key, the power handshake, and the continued
relaxation of no frozen cards — are not listed.

1. **The barrier erased after slot A's first write** (`D2`), because that write already ends the
   vendor kernel (`FW-167`), so the erase adds no second point of no return.
2. **No voltage reading at the seating**, so `P3`'s power tree is recorded as not delivered.
3. **The payloads delivered over the armed image's `nc` into `/proc/rtl819x-spi-img`** (`D22`)
   rather than inside its initramfs (`D12`, refuted by `FW-240`); integrity is carried by the
   install's sha256 against the typed digest, not by the transport.
4. **Each pull cuts the write that would win if it completed**, and the target slot is rewritten
   unpaced first, so a cut before the first erase reads as a control — the design an agent
   corrected in the 124th segment, because the original could not fail.
5. **`T1` before `W3`**: `rlxboot` booted from flash first while the vendor kernel still could.
6. **`pace=2000`** from the runsheet's formula once `E02` gave `se_us`, with the owner's yes for the
   two paced strings given on the day.
7. **After `T2a`, `cs6c` for `rlxboot` and the rescue copy**, and an install guard that accepts
   only `cs6c` in those two regions, because a `cr6c` there is now known not to boot once slot A
   holds a container.
8. **The armed image rebuilt from a clone-only build commit** (`c05e2671`) rather than the fix
   committed mid-seating, because CI's `test-spi-install` required `cr6c` until `tools/mkcr6c.py`
   and the tests moved with it; the repository fix is `f257a848`.
9. **The `C-4` extension and `F02` left unrun.**
10. **`v1.0` ships a mainline image rebuilt at `6a11de02`**, qualified on the device at a later
    seating, rather than the `f9adc9e8` image every reading here is on.
11. **The four carried-forward rows and the § 17 rows below closed, declined or re-owned** in the
    closing commit, so that none reads `ORPHAN` on a closed `R8b`.

### The booking: what moved to another gate, and what was declined

**`PROGRESS.md` § Carried forward**, each row rewritten in place and its old text moved verbatim to
`docs/history/progress-carried-forward.md`:

| row | disposition | why |
|---|---|---|
| `C-1` | ✅ | the scan is measured — the lowest valid candidate wins (`T1a`, with `0x060000`'s `cr6c` still valid), a refused one passes the scan on (`RD05`) — and *the A/B layout needs no loader change* holds for `cs6c` only (`FW-241`) |
| `C-3` | ⊘ 刻意換掉 | which of `burn()`'s callees erases and which programs is a desk reading of `stage2.bin` that nothing rlxfw does depends on: every write is the driver's, `AUTOBURN` is 0 before every upload |
| `C-4` | ✅ | the refusal half by `RD05`/`RD07a`, the prompt half's branch by `T2a`; the extension's end-to-end trigger declined inside the row with what would reopen it |
| `C-13` | ✅ | the flag reads `1` only after ESC (`L01`, `T1e`) and `0` after a boot without it (`X-T2-dba4`), and ESC reached the prompt on every ESC-streamed boot of the seating; the mechanism's open part moves to `SPEC.md` `LDR-21`'s § 17 row |

**`SPEC.md` § 17**, the rows entry 18 re-owned to `R8b`: `FW-187` 殘留 and `FW-191` 殘留 settle at
4,096 (`FW-244`); `FLS-06`–`FLS-08` settles its sector and declines its page and block, which no
code path uses; `REG-13`'s command-sequence half is answered by 31 writes and `SFDR2` is declined;
`REG-14` is declined; and `LDR-21`, owned by `C-13`, is re-owned as a standing instruction. The
drafts are in the closing commit; what each says is the row's, not this entry's.

---

## 2026-10-08 — `P3` (the bring-up report closes on `R8b`'s readings: the boot from flash through `rlxboot`, the bad-image branch measured on the die, two traps of that boot, and a power tree still not measured, by decision)

### One line

**v0.6+, three segments — the 122nd, which wrote the plan's ten sections as §§ 6–15 of
`docs/bringup.md`; the 124th, which corrected the report against its owner rows and re-specified
this row, the first two shared with `R9`'s close and `R8b`'s opening; and the 128th, for `R8b`'s
readings and this closing — the 126th and the 127th touched the report and the row for other gates
and are not counted (ruling 6) — and no power action of its own.**
§ Gate board costs `P3` at 5, the plan's own figure (5 desk, 0 bench and 0 instrument segments),
so the actual is 3 against 5. Since 2026-10-05 (`f071b162`) the row has closed on *`R8b`'s readings
folded into the report*; `R8b` closed on 2026-10-08 (entry 20), and this closing folds them in,
with the readings of `v1.0`'s qualification seating and of `R6c`'s seating A that bear on them
(`FW-255`, `NET-171`, `NET-172`), at nine places: § 11.2 the erase size (`FW-244`); § 11.4 the
layout the part now carries; § 12.1 the boot from flash through `rlxboot` (`FW-241`, `FW-242`);
§ 12.2 its times (`FW-249`, `FW-250`); § 12.3 ① which window catches ESC on a `cs6c` image
(`FW-249`) and ② the bad-image branch on the die (`RD05`, `T2a`; `C-4`); § 12.4 rlxfw's userspace
started from flash (`FW-242`, `FW-255`); § 14.6 two traps of the boot the device makes by itself —
the stock loader's rootfs rule behind `cr6c` (`FW-241`) and a VLAN group nobody configures on an
autoboot (`NET-171`, `NET-172`); and § 16.7 `R8b`'s limits.
**Nothing on the device was measured for this gate**: every reading the report holds was taken
for another gate's question (its § 16.2), and the report is a second source for nothing (§ 16.1).

**The weakest thing here is the one section the plan asks to be measured and that is not.** The
plan's section 2 is *電源樹（實測，含 `S0b`）*; § 7 is a desk reconstruction with two surviving
hypotheses, `S0b` and `BRD-01` are ⊘ by recorded decisions, and `R8b`'s seating took no voltage,
by a ruling (entry 20, ruling 2). So `P3` closes with one of its ten sections written 讀 and 推
where 量 was asked, which § 0 ③ of the report says on its first page. The operating clause below
meets the same item from the other side.

### Three claims that stand

**① The report holds the plan's ten sections and, now, `R8b`'s readings, each traceable to the row
that owns it.** 讀 `docs/bringup.md`: the plan's ten are §§ 6–15 (`0946243b`, 2026-10-04), and §§ 1–5
with the `### 3a` anchor are byte-identical to the `R5` file — `docmove` read 67 blocks conserved
and 3 declared rewrites at that commit. This closing adds `R8b`'s readings at the nine places above,
and every sentence it adds names its owner — a `SPEC.md` row, a note, a capture under `bench/`, or,
for § 16.7's quotations, entry 20. 量 at this closing, by a script kept outside the tree
(`$FWRE_WORK/rebuild/s128/p3/idcheck.py`), every id, capture and seating cell in the report's lines
this closing adds or rewrites: 49 — 21 `SPEC.md` rows, one carried-forward row, 25 captures, one
seating cell and one card cell that entry 20 records as unrun — and none missing, with four planted
unknowns read as missing as its control. ⚠️ No tool checks that a sentence says what its row says,
and `spec-check` does not check an id cited outside `SPEC.md`, so the agreement was read by hand
against each row, and then line by line by an independent audit
(`$FWRE_WORK/rebuild/s128/p3audit/AUDIT.md`), whose findings are applied here; that is § 0's rule
kept by readers, not by an instrument.

**② § 12 now describes the boot the device makes by itself, and § 14 holds both traps that boot
met, each with how it was hit.** 量 `bench/2026-10-07` and `bench/2026-10-08`. The first was hit by
`R8b` failing once: a `cr6c` `rlxboot` booted while the vendor's SquashFS sat at `0x180000` (`T1a`),
and once slot A held a container the loader stopped at `<RealTek>` having accepted `0x010000`
(`T2a`, `X-T2-dd3c`); `cs6c` avoids it (`T2ra`, `RD05`; `FW-241`). The second was hit at `v1.0`'s
qualification seating by a ping after a flash boot, 0 of 2 (`X-V06n`): booted from a slot, `rlx0`
counts no frame after a watchdog reset and after a cold power-on, while a RAM boot through the
prompt answers (`X-V06q`, `X-V08q`, `X-V02n`; `NET-171`). ⚠️ The second is not worked around — its
fix is `R6c`'s. Its mechanism was 推 at the qualification seating, where no MIB counter was read;
`R6c`'s read-only seating A on the same boot (`bench/2026-10-08b`) then counted the host's frames
into port 3 and discarded there, none reaching the CPU port (`NET-172`), so what remains 推 is
which switch rule discards them.

**③ Closing `P3` leaves no debt it held without an owner.** `LA-1` moves to a standing instruction
by the 126th segment's decision (`LOG.md`, its 2026-10-08 entry) — any segment whose seating has
the logic analyser attached, rung 1 first — and `SPEC.md` `CLK-31` 殘留's analyser half follows
it; `FW-177` 殘留 ③'s device half, the WAN-side host probe `docs/threat-model.md` gave `P3`, moves
to a standing instruction by ruling 4 below. 量 `tools/cfcensus.py check` on this entry's tree: 25
rows, 0 findings, the guard reading `P4b` and `R6c` in progress with one OPEN row live-owned,
`FLW-1`, `P4b`'s; `LA-1` reads `SEGMENT`, and `ratchet` is at its baseline. ⚠️ `cfcensus` reads only
`PROGRESS.md`'s table: no tool reads `SPEC.md` § 17's owners, which is how `FW-177` 殘留's ① and ②
and `TC-26` 殘留 still name `R9-9`, a step of a gate closed on 2026-10-04 — not `P3`'s, recorded in
the booking below and left as they stand.

### The board row's clauses, read one at a time

| the row says | verdict |
|---|---|
| **bring-up report** | 🟢 **met**: `docs/bringup.md`, the plan's ten sections as §§ 6–15 (claim ①). ⚠️ Section 2 is not 實測 (the weakest-thing paragraph) |
| **grows every gate** | ⚠️ **not as worded.** 量 `git log -- docs/bringup.md`, twelve commits: 2026-09-09–11 (`R5`, §§ 1–5), 2026-10-04 (the peripheral census in § 13.1, in `R9`'s first segment, then `P3`'s ten sections), 2026-10-05 (the report corrected against its owner rows, and `R8b`'s desk findings) and 2026-10-08 (the `cs6c` correction). The ten gates that closed between `R5` and `R9` — `R1-pub` through `R8` — added nothing to it, and §§ 6–15 assemble their readings after the fact (§ 16.2) |
| **and closes on `R8b`'s readings** | 🟢 **met**: folded in at nine places (One line), with `R8b`'s limits quoted in § 16.7 |
| *(the evidence cell until this entry)* **or on the record that a pull failed** | not needed: no pull failed — 10 of 10 booted the other slot (entry 20) |

### The questions this gate must be able to answer

The plan's hostile-question list (§ 11) asks none of `P3` by name: its `P1`–`P4` row holds one
question for `P1` and one for `P4`. The question the report is for is the plan's note on its
section 9 — where this part bites, how it was hit and how it was worked around — and § 14 answers
it per row, two of them new here.

### What `P3` did not establish

🔴 **A measured power tree.** The plan's section 2 asks for it, with `S0b`. § 7 holds the only rail
voltages on file, taken through a programmer clip with the board's 3.3 V net at ~1.79 V; the
regulator's output pin was never probed and `BRD-01`'s part is unidentified. `S0b` is ⊘
(`PROGRESS.md`'s `S0` row), `BRD-01` is ⊘ (`SPEC.md` § 17, 2026-09-30), and `R8b`'s seating took no
voltage, by entry 20's ruling 2.

🔴 **An interrupt-latency figure by logic analyser.** `LA-1`, carried from `P2` (entry 13): neither
rung ran and the analyser has never been connected. It leaves this gate as a standing instruction
(claim ③).

🔴 **A network on the boot the device makes by itself.** § 14.6 ② records the trap and no
workaround; the fix is `R6c`'s. So § 12's boot flow, followed from flash, ends at a shell whose
`rlx0` receives nothing.

🔴 **That anything in the report is a second source.** Every number was in an owner file first
(§ 16.1); `R8b`'s readings are in it as `R8b` measured them, and § 16.7 quotes their limits rather
than carrying them.

⚠️ **The open values the report names and does not fill**: the strap word's field layout (`REG-40`
殘留), the clock tree's root (`CLK-50` 殘留), `PIN_MUX_SEL`'s fields (`NET-170` 殘留), the memory
controller never read (`MEM-08` ⊘), the radio's attachment (`RF-04` ⊘) and the CPU clock apart from
CPI (`CLK-03` ⊘) — §§ 8.3, 9.5, 10.3 and 15.5 name the first three, § 0 and § 16.3 the last three.

⚠️ **The WAN-side host probe.** `docs/threat-model.md` § 4 gave it to `P3` (`FW-177` 殘留 ③'s device
half), and no boot has brought a WAN interface up. It moves to a standing instruction (ruling 4).

⚠️ **One unit** (§ 0 ②, § 16.5) **and no minimum configuration** (§ 16.4): what the report holds is
what one board returned while it worked.

⚠️ **Flash.** Closing `P3` took no seating of its own and issued no `FLW`, `EW`, `EB`, non-zero
`AUTOBURN` or `FLR`; no flash map was taken for it. What that cannot see: two writes that cancel,
every byte outside the units read, and `H601`, never hashed. The `FLR` bracket stays at 1,024 of
4,194,304 bytes = **0.0244 %**, and the last map is `R8b`'s (entry 20).

### The main session's rulings in this gate, which the owner may override

The owner's own — the relaxed process with the flash rules, `H601`, the power handshake and
`NET-165` unchanged — are not listed.

1. **`P3` closed without waiting for `R6c`**, as the board and § Now already said: § 14.6 ②'s
   workaround cell and § 12's flash boot change if `R6c` closes with a fix, and the report is a
   finding file that keeps growing after its gate, as it grew before it.
2. **The two traps go in a new § 14.6, and *What § 14 does not establish* becomes § 14.7**, so
   every subsection keeps its *does not establish* last; 量 `git grep` finds no file citing
   § 14.6 by number.
3. **Sentences `R8b`'s readings had made stale corrected in place, beyond the list the owner
   gave** — § 11.4's live layout, § 12.1's third, fifth and sixth rows, § 12.2's ESC-window row and
   § 12.3 ① — because each described a flash layout the part no longer carries.
4. **`FW-177` 殘留 ③'s device half re-owned to a standing instruction — any seating that brings a
   WAN interface up** — because `P3` held no seating in its budget and no boot has brought WAN up.
   A ⊘ was the alternative; it would have left `docs/threat-model.md`'s `T3` with its desk read of
   `bind` and no device-side experiment named.
5. **`README.md`'s *Not measured* cell rewritten where `FW-255` and `NET-171` had made two of its
   clauses false** — `v1.0`'s image has run from a slot, and a boot without the loader's network
   has been measured, deaf — and its gate list given `P3`'s close date and the `R6c` line its
   opening commit left out.
6. **Actual 3**, counting the segments that worked on `P3`'s own report or row after the row
   entered `~` on 2026-10-04 — the 122nd, the 124th and the 128th — not the segments between the
   previous close and this one, the column's first definition. Two segments whose commits touched
   the report or the row for another gate are not counted: the 126th's `f257a848` carried `R8b`'s
   `cs6c` finding into § 12.1's stage-4 row, and the 127th's `2f31b080` added `R6c` to the row's
   list of `v1.0`'s gates. The 120th segment's peripheral census (§ 13.1) was read for the report
   as well and is not counted, because the report's own Contents files § 13.1 as predating `P3`.
   Counted by every segment whose commits touched `docs/bringup.md` or the row from 2026-10-04 on,
   the figure is 6.

### The booking: what moved to another gate, and what was declined

| row | to | why |
|---|---|---|
| `PROGRESS.md` `LA-1` | a standing instruction: **any segment whose seating has the logic analyser attached**, rung 1 first | the 126th segment's decision (`LOG.md`, its 2026-10-08 entry); `P3`'s budget never held a seating, and both rungs need a powered board |
| `SPEC.md` `CLK-31` 殘留, its logic-analyser half | follows `LA-1` | it pointed at `LA-1` and named `P3` beside it |
| `SPEC.md` `FW-177` 殘留 ③, its device half | a standing instruction: **any seating that brings a WAN interface up** | ruling 4; `docs/threat-model.md` § 4 and `docs/hardening-matrix.md` point at the row instead of naming `P3` |

Nothing is declined. ⚠️ `FW-177` 殘留's ① and ② and `TC-26` 殘留 name `R9-9`, a step of `R9`,
closed on 2026-10-04 (claim ③); they were never `P3`'s, and their next owner is a decision this
gate was not handed, so they are recorded here and not re-owned.

---

## 2026-10-09 — `R6c` (booted from a flash slot, rlxfw pings both ways after a watchdog reset and after a cold power-on, because its own switch driver now writes the VLAN group the stock loader configures only on its prompt path; the RAM path still pings, and the write set is shown sufficient as a unit, with no on/off control on one boot)

### One line

**v0.6+, four segments — the 127th, which opened the gate on `v1.0`'s qualification seating's
finding and wrote its list (`R6c-0`); the 128th for `R6c-1`, `R6c-2` and a read-only seating; the
129th for `R6c-3` and `R6c-4`'s seating; the 130th for this closing — and two power actions, the
off and on of one cold boot in the 129th, beside one flash write, `I10`.** § Gate board leaves
`R6c` uncosted — the plan does not name it, and the owner opened it on 2026-10-08 — so there is no
estimate to divide by; the qualification seating that found the fault (`bench/2026-10-08`, two
power actions and the write `V05b`) ran before the gate opened and is `FW-255`'s, not counted
here. **Booted from slot A through `rlxboot`, the release image `9bb2bec7` pings both ways after a
watchdog reset and after a cold power-on**, 4 of 4 each way on each boot (`W10`, `X-W14`; `C10`,
`X-C14`), where the same two kinds of boot of `6a11de02`, on 2026-10-08, counted no frame
(`NET-171`) and its switch discarded every frame from the host at port 3 (`NET-172`). What changed is
`rtl819x-switch` 1.6's `vlan` (`034b5a7d`, `NET-173`): PID 1 types it between `init` and `start`,
and it writes the loader's one-VLAN layout wherever the switch differs from it — VLAN slot 8
`00807E3F` and the other fifteen slots zero, the eight netif slots zero, `PVCR0`–`3` `00080008`,
`FFCR` 3 — after verifying four words it never writes. On a flash boot that is one table write
and five registers, `n_writes` 6 → 23; on a RAM boot through the prompt, where the loader has
written the group, it is netif slot 0 alone, 6 → 18, and that path still pings both ways. The
layout is the owner's (ruling O1, 2026-10-08), admitted on two sources — the vendor bootcode and
the measured working state, with the loader's own stores a third — after `R6c-1` read the
loader's 30 Ethernet-init writes from two sources and found that an autoboot makes none of them
(`LDR-47`).

**The card was wrong once at the bench, and the main session's review passed it.** It wrote the
board's `ping` without `-c` on all three paths, because it took the 2026-09-06 finding — *this
image's `ping` ignores `-c` and always sends exactly four packets* (`NET-26`,
`notes/rootfs-census.md`, restated in `CLAUDE.md`) — as true of the image under test, and pinned
that sentence in a `cardnum` row (`ping-four`). 讀 The finding was measured on the vendor's
busybox (273,332 bytes); the image under test carries rlxfw's own (`prebuilt:busybox/busybox`,
447,684 bytes). 量 Its `ping 10.1.1.2` in `R14` was still answering when the cell's 35 s window
closed, and it held the console through `R15` and `R16`, whose captures hold its reply lines; a
Ctrl-C (`X-R14i`) ended it at 225 transmitted, 225 received, and the two cells were typed again as
`X-R15` and `X-R16`. `CORRECTIONS-R6C-4.md`, each entry written before what it changes ran, typed
the flash boots' board ping with `-c 4` (`X-W13`, `X-C13`, writing `X-W14`, `X-C14`; C1), read
`D1`'s *`R14` `4 packets received`* as every request answered, with the host's `tcpdump` in `R13`
showing each request and its reply (C2), and kept the closing count off the card, whose mtime
`check-predictions` compares with the captures' (C3). It cost two re-taken cells and one
interrupt, and no write or power action. `NET-26` now says it holds for the vendor's busybox
only, and `CLAUDE.md`'s line asks for `-c 4`.

**The weakest thing here is the causal half: the take-over is shown sufficient, as a unit, on one
boot of each kind, against a control that is a different image on other boots.** 讀 `git diff
f257a848 034b5a7d -- config src`: the build inputs of `6a11de02`, deaf from flash, and
`9bb2bec7` differ in seven files, and the code among them is the 1.6 block and the line that
types `vlan`, in `src/init/main.c` and in `config/rlxfw-init.sh` — the rest are comments and the
`/init` row's description — so the comparison has one variable, but it spans two images and four
flash boots, and no cell takes the write set away on one boot and watches the frames die again.
The design asked for exactly that — `vlan reset`, predicted to bring the flash symptom back on a
RAM boot (`$FWRE_WORK/rebuild/s127/r6c2/TAKEOVER-DESIGN.md` § 4.3, B2) — and ruling E1 declined
it, naming 2026-10-08's flash boots without the verb as the control. So which of the 17 stores is
necessary is not measured — O1 writes the group as a unit — and which switch rule discarded the
frames before, ingress filtering or the lookup of a VID with no entry, stays 推: the write set
changes the PVIDs and the table together. And each path is one boot: one warm and one cold flash
boot, which read alike (`W03` and `C03` differ in their `jiffies` line alone), and one RAM boot
through the prompt.

### Three claims that stand

**① Booted from slot A through `rlxboot`, rlxfw receives: the release image pings both ways after
a watchdog reset and after a cold power-on, and the switch now delivers to the CPU port what it
discarded before.** 量 `bench/2026-10-08c` (`NET-173`; `NET-171`'s 🔄). `W01` (`busybox reboot -f`,
then `Reboot Result from Watchdog Timeout!`) and `C01` (the owner's off and on; no such line) each
read `RLXBOOT-FROM 05010000`, `RLXBOOT-VERDICT A ok ver=5`, `RLXBOOT-VERDICT B ok ver=4`,
`RLXBOOT-SLOT A` and `RLXFW-ID0=9BB2BEC7`, and `tools/bootslot.py judge` read PASS on both (`W02`,
`C02`). Host → board: `4 packets transmitted, 4 received, 0% packet loss`, `ping_rc=0`, the host's
entry for `10.1.1.1` `REACHABLE` (`W10`, `C10`); board → host: `4 packets transmitted, 4 packets
received` (`X-W14`, `X-C14`), the host's `tcpdump` showing four echo requests and four replies
(`X-W13`, `X-C13`). `rlx0`'s RX went 0 → 6 → 10 across the two exchanges on each boot (`W08`,
`W12`, `W16`; `C08`, `C12`, `C16`). In the switch's own counters, across the host's ping, port 3's
in columns and the CPU port's out columns moved together, column for column — 536 octets, 5
unicast, 1 broadcast — and port 3's two discard columns stayed 0 (`W09` → `W11`, `C09` → `C11`);
on seating A's flash boot without the verb the host's three ARP requests raised each of port 3's
discard columns by 3 and moved none of the CPU port's (`bench/2026-10-08b`, `A10` → `A12`,
`NET-172`). That seating and 2026-10-08's two flash boots of `6a11de02` (`X-V06q`, `X-V08q`: 0
of 3, the entry `FAILED`) are the control. ⚠️ Four pings each way on each boot, one host on port
3, and a control that is another image (the weakest-thing paragraph).

**② `vlan` stores exactly what differs from the loader's layout, and every field of its line that
the card predicted from the code read as predicted, on all three paths.** 量 `R03`, `W03` and `C03`
against `R6C-4-CARD.md`, whose predictions sit in `cardnum` rows derived from `034b5a7d` by a
script outside the tree (`$FWRE_WORK/rebuild/s129/r6c4/derive.py`, pinned by sha256). From flash:
`vw 0100 nw 00 rw 1F` — one table write, VLAN slot 8, and the five registers — `n_writes 23` = 5
(`init`) + 17 + 1 (`start`), `n_reads 133` = 131 + `sta` + `spin`. Through the prompt: `vw 0000 nw
01 rw 00` — netif slot 0 alone — `n_writes 18`, `n_reads 128` = 126 + `sta` + `spin`. On all
three `rc 0`, `final 0`, `ld 784` (every double read agreed at once), `to 0`, `rb 0`, and the
four fields the card left to be read came back `tlu 000C0000` (bit 18 read back set after step
(2), recorded and not required), `sta 1`, `spin 1`, `swtasr 00000000`; the live `SWTCR0` reads
`00080000`, bit 18 clear. Afterwards the tables hold the write set — VLAN slot 8 `00807E3F` and
seven zero words, the other fifteen slots and all eight netif slots zero (`R04`–`R05`,
`W04`–`W05`, `C04`–`C05`) — and the registers read `PVCR0`–`3` `00080008` and `FFCR` 3, with
`PVCR4` 1, `VCR0` `1FF` and `PBVCR0` 0 on the page and `PLITIMR` `07FAC688` in the ALE run (`R06`,
`W06`, `C06`). 🟢 **The warm flash boot refuted an alternative the review had added to the card**:
a watchdog reset that clears the registers but keeps the on-chip tables would have read `vw
0000` and `n_writes 11`; `W03` read `vw 0100` and 23, as the cold boot did — a watchdog reset
clears the ASIC tables with the registers. ⚠️ Equal read-backs say the slot reads back as stored,
not how many `TCR` words the engine took; and the desk harness that predicted the same fields
(`tools/mdiocheck.py`, 152 run, 0 failed, 82 of 82 mutants killed by the case named for each)
models the engine from the vendor readings the driver follows.

**③ The RAM boot through the loader's prompt still pings both ways with netif slot 0 cleared, so
the netif entry was not what carried `rlx0`'s unicast.** 量 `R02`: `looprun` uploaded
`9bb2bec7` against its pinned sha256 and read `A3` `board printed 9bb2bec7, build computed
9bb2bec7`; it failed `A4` (`neither '<RealTek>' nor a shell prompt`), `FW-252`'s fifth time —
the shell's prompt printed before `dnsfwd`'s lines — and `X-R02p` read `37.53 31.98` and the
prompt, the route the card gave that case. `R05`: all eight netif slots zero. Host → board 4 of 4
(`R10`); board → host 225 of 225 (`X-R14i`, unbounded: the paragraph above). Port 3's in columns
and the CPU port's out columns moved together, column for column, and port 3's discard columns
stayed 0 (`R09` → `R11`, and `R11` → `X-R15` across the board's 225). ⚠️ That `FFCR`'s
unknown-unicast trap is what delivers that unicast stays `NET-169`'s 推 on one source: its
deciding experiment — the RX header's `ph_reason`, or a unicast ping with `FFCR` bit 1 cleared —
was not run, and the L2 table was not read on this boot. What is measured is that the netif
entry is not needed, and ruling O1's fallback, netif slot 0 with `rlx0`'s own address, was not
built.

### The board row's clauses, read one at a time

| the row says | verdict |
|---|---|
| **an image booted from a slot through `rlxboot`** | 🟢 **met**: T — `9bb2bec7` in a container the owner signed as version 5 for slot A — installed by `I10` (`I11`: `inst_reason OK`, 288 sector erases and 4,337 page programs, `inst_cmp_diff 0` over 1,179,648 bytes), then chosen by `rlxboot` over S (`ok:4`) on both flash boots (`W01`, `C01`; `bootslot` PASS) |
| **pings both ways** | 🟢 **met**: 4 of 4 each way on each flash boot, read on the host (`ping`, `tcpdump`) and on the board (`rlx0`'s counters, the switch's MIB) — claim ① |
| **after a watchdog reset** | 🟢 **met**: `W01`, `busybox reboot -f`, `Reboot Result from Watchdog Timeout!` printed |
| **and after a cold power-on** | 🟢 **met**: `C01`, after the owner's off (`PF2`: 0 bytes in 3.08 s, the board off) and on, with no watchdog line |
| **and a RAM boot through the loader's prompt still does** | 🟢 **met** (claim ③): 4 of 4 host → board (`R10`), and every request answered board → host (`X-R14i`, 225 of 225). ⚠️ `looprun` read `R02` as 1 of 8 assertions failed, `A4`, `FW-252`'s, and the board's `ping` was not bounded at four (C1, C2) |
| *(the card's refutation)* any flash boot below 4/4 either way; `n_rx` 0 while the host's TX grows; a table or register other than the write set; `vlan`'s rc not 0; `STOP_TLU` left set; B1 failing | **did not fire**, with `D1` read as `CORRECTIONS-R6C-4.md` C2 reads `R02` and `R14` |

### The steps' DoD, read one row at a time

| the DoD says | verdict |
|---|---|
| **`R6c-0`** the board row reads `~` and names this list | 🟢 met 2026-10-08 (`2f31b080`) |
| **`R6c-1`** a table with both sources per row, each agreeing or recorded undetermined | 🟢 met 2026-10-08 (`b3a32ee5`, `LDR-47`, `docs/loader-phy-and-switch.md` § 2026-10-08): 30 writes in program order, each with A and Bb or Bk and with 量 where read; `MEMCR` stands on A and 量 alone, and row 12's two arms are recorded as not executed. ⚠️ No held tree builds this loader (the hazard column) |
| **`R6c-2`** written, with where it will fail | 🟢 met 2026-10-08: the design (`$FWRE_WORK/rebuild/s127/r6c2/TAKEOVER-DESIGN.md`, nine risks in its § 6), checked by `$FWRE_WORK/rebuild/s128/v2/VERIFY-R6C2.md`, and the rulings (`$FWRE_WORK/rebuild/s128/RULINGS-R6c.md`: O1, O2, and E1–E4, each with where it fails); in the tree, `notes/switch-driver.md` § 21.3. ⚠️ The design and the rulings are outside the tree |
| **`R6c-3`** builds byte-equal; tests green and the mutation red | 🟢 met 2026-10-08 (`034b5a7d`): mainline `s128p-r6c-mA` == `-mB` (`nfjrom` `295d4f6a…`), armed `-aA` == `-aB` (`9328dcf9…`), the six userspace programs A == B; `mdiocheck` 152 run, 0 failed, 82 of 82 mutants killed; the main session's mutant of (4)'s busy exit, green under the implementation agent's 68 cases, is red under `K67` alone (`M82`) |
| **`R6c-4`** each boot judged by `bootslot`, each ping read from both sides | 🟢 met for the two flash boots (`W02`, `C02` PASS; each ping read on the host and on the board). ⚠️ By the letter `bootslot` cannot judge the RAM boot: it reads `rlxboot`'s lines, which a boot through `J 80500000` does not print, and `R02`'s `A3` identified that one. ⚠️ `R14`, unbounded, was read by C2 |
| **`R6c-5`** `cfcensus` and `spec-check` green on the closing tree | 🟢 met 2026-10-09, on this entry's tree: `spec-check` rc 0; `cfcensus` `write`, then `check` rc 0 — 25 rows, 0 findings, the guard reading `P4b` alone in progress with one OPEN row live-owned, `FLW-1`; `docmove` CONSERVED, 150 blocks conserved and the seven in-place rewrites declared (`$FWRE_WORK/rebuild/s130/r6c-move.allow`) |

### The step list's hazard column, read one at a time

* **`R6c-1`, a function in a drop that does not build this loader** — it fired in the form named:
  讀 no held tree builds this loader, whose `P0phymode=%02x, %s phy` format is in neither bootcode
  tree, so every row stands on `stage2.bin`'s disassembly (A) with the vendor bootcode of another
  generation (Bb, built for 8196C and 8198) or the kernel's 8196E arm (Bk) beside it, and nothing
  was admitted for rlxfw on A alone. It also found three rows of `notes/switch-driver.md` § 8.9 —
  `MACCR |= 0x1000`, `PITCR |= 0x1`, `P0GMIICR |= 0x40` — to sit in the `BOND_8196ES` arm, which
  this part does not run (`REG-30`); § 8.9 is corrected in place.
* **`R6c-2`, a value with one source, taken because the loader's state worked** — the design's own
  risk 4, and the reason 8d ruling 3 had refused a take-over. The owner's O1 admitted the layout on
  Bb and 量, A a third; the four words whose only source is 量 — `PVCR4`, `VCR0`, `PBVCR0`,
  `PLITIMR` — are verified and never written, and a mismatch refuses with nothing stored.
* **`R6c-3`, a RAM boot through the prompt broken by writing over the loader's state** — did not
  fire: on that path `vlan` stored netif slot 0 alone (`vw 0000 nw 01 rw 00`) and the boot pinged
  both ways (claim ③).
* **`R6c-4`, a cold boot that differs from the warm one** — did not fire: `W03` and `C03` differ in
  their `jiffies` line alone, the tables, the ALE run and `QNUMCR` read the same (`W04`–`W07`
  against `C04`–`C07`, counter lines aside), and the two pings moved the MIB by the same deltas.

### The questions this gate must be able to answer

The plan's hostile-question list (§ 11) has no row for `R6c`: 量 `grep -c R6c
plan/router-rebuild-plan.md` returns 0, the owner having opened the gate on 2026-10-08. The
question it exists for is the one `v1.0`'s qualification seating raised — *why does an image
booted from flash hear nothing, and is the fix the reason it now does?* — and the answer has three
parts: the loader configures the switch only on the path into its prompt, and an autoboot writes
none of it (`LDR-46`, `LDR-47`); booted from flash, the switch discarded every frame from the host
at port 3 (`NET-172`); and with `vlan`, the same port delivers to the CPU port and its discard
counters stay 0 (claim ①), between two images whose build inputs differ by `R6c-3`'s change set
alone — with no on/off control on one boot (the weakest-thing paragraph). 讀 The plan's own scope
for `R6` lists 「switch 初始化到 dumb 狀態（全 port 同 VLAN，無加速）」; until this gate rlxfw met
it by inheriting the loader's state, which only the prompt path has, and since 1.6 it writes that
state wherever it differs. `R8`'s 「只有一台機器你敢寫 flash？」, entry 20's to answer, had one more
instance here: `I10`, under the owner's dated yes for its exact string, read back whole, with
slot B outside the arm window (`arm 0x70000 0x190000 0x120000`).

### What `R6c` did not establish

🔴 **Why the frames died before, and which of the writes is necessary.** Ingress filtering or the
lookup of a VID with no entry is 推: seating A's discard counters cannot tell them apart, and the
write set changes the PVIDs and the table together. No cell takes the 17 stores apart — O1 writes
the group as a unit — and no cell removes them on one boot, E1 having declined the design's
`vlan reset` (the weakest-thing paragraph).

🔴 **More than one boot of each kind.** One warm and one cold flash boot of one image,
`9bb2bec7`, and one RAM boot through the prompt; no cold boot with ESC.

⚠️ **That `FFCR`'s unknown-unicast trap is what delivers `rlx0`'s unicast** (claim ③). On the
flash path the L2 table read empty on seating A's boot (`A07`, `NET-172`) and was not read after
`vlan` wrote `FFCR`.

⚠️ **The engine's side of the table write.** How many `TCR` words it copies — equal read-backs
say only that the slot reads back as stored — and what the switch does with a frame that arrives
while `STOP_TLU` holds the lookups on the RAM path, where `TRXRDY` is already set: a frame lost
there does not show in a later ping. The rest of the table write the silicon did answer: `SWTCR0`
read `000C0000` with `STOP_TLU` set, one poll at each of steps (3) and (8) (`sta 1`, `spin 1`), and
`SWTASR` 0 after a force (`notes/switch-driver.md` § 21.6).

⚠️ **`MACCR` and `QNUMCR`'s CPU field.** Each differs between the two paths that ping — `MACCR`
`804A0185` through the prompt and `80420186` from flash, `QNUMCR` `00001249` and `00041249`
(`R03` and `R07` against `W03` and `W07`) — and `vlan` writes neither, so neither decides four
pings on port 3; nothing more is shown. The PHY patch and `LEDCREG` were not read.

⚠️ **That a second `vlan` stores nothing on the silicon.** No cell typed it; the harness's `K55`
does (E3).

⚠️ **A second port.** Every frame was counted on port 3, with the host's adapter at 100 Mb/s,
half duplex (seating A). 讀 The written VLAN 8 makes ports 0–5 members, untagged (`00807E3F`,
`notes/switch-driver.md` § 21.4), port 0 among them — the port the vendor firmware runs as its
WAN, on VID 8 apart from the LAN's VID 9 (`NET-04`). 推 So a peer on port 0 now reaches `rlx0`
from flash as a LAN peer does, as it has on every RAM boot through the prompt, whose layout this
is; nothing on a port but 3 was counted (`NET-174`).

⚠️ **Load, and the vendor's firmware.** Four pings each way on each flash boot and 225 on the RAM
path; no throughput and no flood.

⚠️ **The harness shares its sources with the driver.** `tools/mdiocheck.py`'s engine follows the
same two vendor readings the driver does — the step order of A (`LDR-47`) and of Bb's
`swTable_forceAddEntry`, the command and the entry layout of B — so the device agreeing with both
predictions does not separate them, and an error the two share passes both (`NET-173`).

⚠️ **The fallback slot is deaf.** Slot B still holds S — `6a11de02`, version 4 — which `rlxboot`
verified on both flash boots (`RLXBOOT-VERDICT B ok ver=4`); 推 from `NET-171`, a boot that falls
back to it, as a torn or invalid slot A would, comes up with no Ethernet. The counter read
`ctr=0` on both boots, so nothing refuses S either. Rewriting slot B is another flash write.

⚠️ **That `v1.0` is released, or that rlxfw updated itself.** `v1.0`'s image is re-pinned to
`9bb2bec7` (`FW-256`, the owner's instruction for this closing), and `P4b`'s phases are not this gate's. T went into slot
A as `R8b`'s containers did, by the armed image RAM-booted through the loader (`I01`–`I11`); the
release image has no write path (`W17`, `C17`: `wr_linked 0`, `n_mtd_write_calls 0`,
`n_mtd_erase_calls 0`).

⚠️ **What the gate got wrong at the desk**, each caught before a byte reached the device and
recorded in `LOG.md`'s 127th–129th entries. The first draft of `NET-171` counted the switch's
differences as 7 — they are 10, `PVCR0`–`3` being four rows — and said nobody had connected the
two halves, which `notes/switch-driver.md` §§ 17.4 and 17.10 had (the `R6c-2` agent's
correction). The two research reports, checked against the raw sources by two more agents, held
on every disassembly row but carried errors of method — two 量 cells cited wrongly, the loader's
second init entry under-described, a boot mark that would have moved `bootbytes`' counts, a
harness that compared literals only, a bit-18 read-back never measured — and contradicted each
other on whether PVID 8 has a second source (it has: Bb's `swCore.c`). The implementation agent's
68 cases let one of the main session's twelve mutants through — (4)'s busy answer skipping the
undo, which would leave `STOP_TLU` set and stop every lookup — closed by `K67` and `M82` before
the patch was committed. And `034b5a7d` left `src/init/main.c`'s header naming *five* `/proc`
verbs, one short since `vlan`; it was corrected after the build and then reverted, so that no
build input moved after the build, and the comment waits for the next rebuild (`FW-256`).

⚠️ **Instruments the tree does not hold.** The design and its check, the two research reports
and theirs, the rulings (`$FWRE_WORK/rebuild/s127/`, `s128/`); the card's draft, its review and
`derive.py` with `derive.out`, which the card pins by sha256 (`s129/r6c4/`); the main session's
twelve mutants (`s129/mut.py`); the seating's scripts (`s129/bench/`); and the build records
(`s128/p/run/r6c/`). The card's review found three defects in the tools and fixed none before the
seating: `cardcheck`'s `--idle` guard on a `sleep` skips every line without the literal
`console-capture`, so no `CAP` line on any card has been checked by it; V10's `--boot-until`
never matched (`FW-253`); and under `--skip S4` `looprun`'s `A0a` reads only its own `S4`. None
let a write happen. After the seating `tools/bootbytes.py` went red at the desk on `R02-boot.log`,
which `FW-252`'s race had cut 257 bytes short, and was repaired before the push by naming that
capture (`CUT_SHORT`, `K10`, `f19c0e33`) rather than declaring its length.

⚠️ **One unit, one loader build, one evening's seating** (20:19–21:59).

⚠️ **Flash.** 量, counted over the 79 `.meta.json` files of `bench/2026-10-08b` and
`bench/2026-10-08c` — 75 `sent` fields, classified by a script whose planted strings each landed
in their class (`$FWRE_WORK/rebuild/s130/r6c5/sent.py`): `FLW` 0, `EW` 0, `EB` 0 and `AUTOBURN`
0 — not even `AUTOBURN 0` was sent; `looprun` read `0x8040D4A0` back as `00000000` before each of
the two uploads (`R02`, `I02`: `A0b`, through `DW 8040D4A0 1`) — and `FLR` 0. One flash-writing
command, `I10`, `install slotA sha=113f5542…`, under the owner's dated yes of 2026-10-08 (the
card's `owner-yes` row). rlxfw's `n_writes`: 4,625 on the armed image after `I10` (`I11`: 288 sector
erases + 4,337 page programs = `inst_ops_planned` 4,625), and 0 on the release image after each
flash boot (`W17`, `C17`); seating A's image has no install verb. Power: two actions, both the
owner's on the handshake — off before `PF2` (0 bytes in 3.08 s from 21:57:01) and on inside
`C01`'s window, opened at 21:57:13, whose first byte arrived 13.6 s later — and none at seating
A. The bracket's reach: `I10`'s read-back of slot A's 1,179,648 bytes (`inst_cmp_bytes 1179648`,
`inst_cmp_diff 0`, `inst_cmp_first -1`), and `rlxboot`'s digest of slot A's 1,110,176 bytes and
slot B's 1,109,152 on both flash boots (`RLXBOOT-DIGEST ok` twice in each of `W01`, `C01`). What
none of it sees: two writes that cancel; every byte outside slot A and the two containers, slot
B's last 70,496 bytes among them; any region against the 2026-08-16 dump, since no `FLR` ran and
no map was taken (the last map is `R8b`'s, entry 20); and `H601`, never read. `flashwin scan
--sweep` read both directories CLEAN — 54 files and 208, 113 probes each (`LOG.md`, the 128th and
129th entries).

### The main session's rulings in this gate, which the owner may override

The owner's own — opening `R6c` and holding `v1.0` for it, the loader's layout taken over as a
unit (O1, superseding 8d ruling 3), seating A before any code (O2), the dated yes for `I10`,
seating `R6c-4` the same evening, `v1.0` re-pinned to `9bb2bec7` for this closing, and the relaxed process with the flash rules, `H601`, the power
handshake and `NET-165` unchanged — are not listed.

1. **`vlan` is a verb in a 1.6 block of `rtl819x-switch.c`, typed by PID 1 between `init` and
   `start`** (E1); the driver still writes nothing at boot on its own, and a failed `vlan` is
   printed and `start` still runs.
2. **No `vlan reset`, so no on/off control on one boot** (E1): the control is 2026-10-08's flash
   boots without the verb. What that costs is the weakest-thing paragraph.
3. **The table write** (E2): IRQs off, `STOP_TLU` set and, on every exit after it, cleared with
   a read-back; all eight `TCR` words, zero-filled; and the command 9 (force) where the loader uses
   3 (add), because B's VLAN and netif setters and its table clear force-add
   (`rtl865x_asicCom.c:121`, `:553`, `:1124`).
4. **Write only what differs** (E3), so the RAM path's one variable is netif slot 0 and a second
   `vlan` stores nothing; on `SWCORE=y` it stores nothing and says so (E4).
5. **The patch entered the repository on the main session's re-run, not on the implementation
   agent's report**: every suite and twelve mutants of its own on `2009c4eb` plus the patch, and
   the one that survived became `K67` and `M82`.
6. **Three changes to the card in review**: a third alternative for the warm boot (tables kept,
   `n_writes 11`), which `W03` refuted; up to three re-reads before a short `img_len` stops the card
   (`FW-248`); and the owner's choice between `J BFC00000` and a power cycle if a flash boot stops
   at `<RealTek>`.
7. **`CORRECTIONS-R6C-4.md` C1–C3**: an interrupt and two re-takes rather than cells re-run under
   their own names; the flash boots' board ping with `-c 4`; `D1` read through `X-R02p` and
   through `R14`'s statistics line with the host's `tcpdump`; the closing count kept off the card.
8. **`R02-boot.log`'s length named as a capture cut short**, `CUT_SHORT` and `K10`, rather than
   declared as a constant of the console (`f19c0e33`).
9. **`src/init/main.c`'s stale header comment left until the next rebuild**, so that `v1.0`'s
   image is the `9bb2bec7` the device ran, with no build input changed since (`FW-256`).
10. **`docs/sbom.md`, a snapshot of `f184a`, given a 🔄 note on U1 rather than one cell updated**,
    and `notes/userspace-integration.md`'s row left as it stands: one updated cell would mix two
    builds in one SBOM.
11. **`NET-26` narrowed to the vendor's busybox, and `CLAUDE.md`'s line changed to ask for `-c
    4`.**
12. **The card review's three tool defects recorded and left unfixed before the seating**, the
    129th segment keeping `tools/` out of its pre-seating work; `cardcheck`'s is in § Now's next
    line.
13. **Actual 4**, counting the segments that worked on `R6c`'s own steps or row after it opened —
    the 127th to the 130th — entry 21's ruling 6. The 128th, which also closed `P3`, is counted
    because it closed `R6c-1` and `R6c-2` and held seating A.

### The booking: what moved to another gate, and what was declined

Nothing in `PROGRESS.md` § Carried forward or `SPEC.md` § 17 names `R6c` (量 `grep` at
`28a490c7`), so no row is re-owned.

| item | to | why |
|---|---|---|
| `docs/KNOWN-ISSUES.md`, the entry of 2026-10-08 (booted from flash, rlxfw receives no Ethernet frame) | closed in place, on its own condition | its closing condition is the board row's, met by `R6c-4` (claims ①, ③) |
| `v1.0`'s image | `9bb2bec7` (`FW-256`), for `P4b` | the image the board ran in claims ①–③; `6a11de02` is deaf from flash |
| `cardcheck`'s `CAP` blind spot | § Now, *Next after this* | a fix with a control that goes red; no gate owns it |
| V10's `--boot-until`, and `looprun`'s `A0a` under `--skip S4` | recorded, not owned | `FW-253` already says why `job control turned off` no longer matches; `A0a`'s reach is a card's to know, and `R6C-4-CARD.md` says it |
| `NET-169`'s mechanism | stays in its row, whose 判定 names the experiment | one source, as before; `R6c-4` removed one alternative (claim ③). `notes/switch-driver.md` § 21.6 and `NET-173` had called it measured; both are corrected in place, and `NET-169` gains a 🔄 |
| port 0, the vendor firmware's WAN, in the VLAN `vlan` writes | `docs/threat-model.md` § 4 (`T3`) and `SPEC.md` `NET-174`; `v1.0`'s known issues | 推 a peer on port 0 is a LAN peer to rlxfw (*What `R6c` did not establish*, a second port); no gate owns a WAN |
| O1's fallback, netif slot 0 with `rlx0`'s address | not built | the RAM path pinged with netif cleared (claim ③) |
| the design's seating B — `vlan reset`, and `reset full` before `init` | declined | E1, and the design's own condition on `reset full` (the NIC's re-arm after a switch reset, unsettled at the desk) |

**Declined**: which of the writes is necessary. O1 writes the group as a unit, never partially,
and no step of `R6c` set out to take it apart; what that leaves open is the first 🔴 above.

---

## The operating clause, re-run at twenty-two entries

**Rule:** two consecutive entries whose *what it did not establish* is the same
thing make that thing the next gate.

*(Run for the first time at five entries on 2026-09-01. Re-run 2026-09-02 with
`P4b-gate` inserted in close order and `R4` appended, which changes the pair set
rather than adding to it: the old `P4a` → *(end)* boundary is now two more
pairs, and `P4a`'s neighbour on the right changed. Re-run 2026-09-11 with `R5`
appended, which adds exactly one pair. Re-run 2026-09-16 with `R1-pub + R2c`
appended, which adds exactly one pair — and that pair fires. Re-run 2026-09-16 with `R1z` appended, which adds exactly one pair, and that pair does NOT fire. Re-run 2026-09-17 with `P1` appended, which adds exactly one pair, and that pair does not fire either — for a reason no previous non-firing has used, because the one item the two entries share was CLOSED rather than carried. Re-run 2026-09-22 with `R6` appended, which adds exactly one pair — **and that pair fires**. Re-run 2026-09-25 with `P2` appended, which adds exactly one pair, and that pair does not fire — the later gate had CLOSED three of the earlier one's residuals, and the nearest remaining candidate is one subject that the two entries name as two different faults. Re-run 2026-09-28 with `R6b` appended, which adds exactly one pair — **and that pair fires**, on a thing the earlier entry handed to the later gate by name; the same run decides the question the thirteen-entry run left to this entry. Re-run 2026-09-30 with `R1y` appended, which adds exactly one pair, and that pair does not fire — the later gate is about this repository's record, and it did not take on the thing the fourteen-entry run fired on. Re-run 2026-09-30 with `R8a` and `R7` appended, which adds two pairs at once because entry 16 wrote no sixteen-entry run: this run supplies both, `R1y` → `R8a` does NOT fire, and **`R8a` → `R7` FIRES**. Re-run 2026-10-04 with `R8` appended, which adds exactly one pair — **and that pair FIRES on the same thing as the pair before it**, the first time one thing has fired on two consecutive pairs. Re-run 2026-10-04 with `R9` appended, which adds exactly one pair — **and that pair FIRES on the same thing a third consecutive time**. Re-run 2026-10-08 with `R8b` appended, which adds exactly one pair, and that pair does NOT fire — `R8b` closed the thing the three pairs before it fired on, and the one item both entries still carry is a resemblance. Re-run 2026-10-08 with `P3` appended, which adds exactly one pair, and that pair does NOT fire — the one thing both entries name that the clause counts, `P3`'s power tree, was declined three times in writing, and the clause surfaces what nobody decided. Re-run 2026-10-09 with `R6c` appended, which adds exactly one pair, and that pair does NOT fire — `R6c` closed the one counted thing `P3` carried, the thing `P3` had named `R6c` to fix, and the nearest candidate, which of the writes is necessary, the owner had ruled on before any code was written.)*

| pair | shared? |
|---|---|
| `R1-gate` → `R2a/b/d` | no. `R1-gate`'s residuals are the D side and the cache; `R2a/b/d`'s are drop identification and toolchain choice |
| `R2a/b/d` → `R1h` | no |
| `R1h` → `R3` | **yes — decision ② / `CPU-45`.** `R1h` carries it as 未定 after the first of two allowed seatings; `R3` carries it as still `R1-gate`'s. 🔄 **2026-09-14: the seating count is no longer what decides this.** `c-A` has read negative **three** times on silicon, not once — and the question it was gating is answered from `t-hit`, at the desk, with no seating at all (`docs/rlx-cache-and-cp0.md` § ⓑ-2; `SPEC.md` `CPU-45`). What the next seating buys is the **pre-registration**, because the reading that answers it had no refutation condition written first |
| `R3` → `P4a` | no |
| `P4a` → `P4b-gate` | no. `P4a`'s are Level-2 reproducibility, one machine, one afternoon; `P4b-gate`'s are the unowned rule, the missing tag, and the ledger's own omission |
| `P4b-gate` → `R4` | no |
| `R4` → `R5` 🆕 | **yes — the loop has never run `S2` → `S7` in one invocation.** `R4` carries it as *73.88 s is a sum of two runs*; `R5` carries it after six seatings that could each have closed it 🔴🔴 **2026-09-14: this firing is DISCHARGED, and the answer is negative.** The seam is not a thing a seating was going to do — `looprun --mode bench` with no `--skip` cannot run, because its `--image` pre-flight requires the file `S3` creates. Measured at the desk with two refusing arms and a control that passed the same guard, for **zero power cycles**. ⚠️ So the clause's only new firing at eight entries was real and its subject turns out to be a tool defect rather than a missing measurement — which is a reading about the clause too: it names a *thing*, and a thing can be impossible. |
| `R1-pub + R2c` → `R1z` 🆕 | **no, and the reason is the clause's own discipline.** Both residual sets contain an instrument that could not be asked about its own subject — `hazpay`'s `check_controls` inspecting 2 of 26, and this census being blind to a paid debt — but that is the same SHAPE, not the same THING. Every previous firing named one item both entries carry verbatim (`CPU-45`; `S2`→`S7` in one invocation; a same-instant read of two counters). **A clause that fires on a resemblance measures the reader, not the ledger** |
| `R5` → `R1-pub + R2c` 🆕 | **yes — a same-instant read of two kernel counters.** `R5` carries it as `D4` naming `/proc/timer_list`, *which exists in this kernel and cannot carry the property the row wanted — two counters read atomically*. `R1-pub` carries it as `D-cost`'s `E5` requiring `Δirq_count == Δjiffies` on every rung, failing **5 of 64**, and the one `/proc` file that serves both not sampling them together. 🔴 **The sentence that connects them is inside `R5`'s own bullet** — it says the substitute `R5-2` used *carries both counters inside one `spin_lock_irqsave`*, which is true of the pair `R5` used and **false of the pair `R1-pub` needed**: 讀 `drivers/clocksource/rtl819x-timer.c`, `j = get_jiffies_64()` is at line 2001 inside the lock held from 1998 to 2042, and `irq_count` is read live at line 2147, **105 lines after the unlock** |
| `P1` → `R6` 🆕 | **yes — `MT-PORT`'s output does not say which driver served the link, and `P1` handed it to `R6-0` by name.** `P1` carries it as *"every `MT-PORT` line this project has captured is unlabelled as to which driver served it. Carried to `R6-0`"*; `R6` carries it because `R6-0` quoted that residual, banked **half** of it — `SPEC.md` `NET-31`, the Linux-side named-port link state — and left the other half, while `R6` landed the second driver that makes the label necessary. 量 2026-09-22: `config/mfgtest.sh:536` still prints `chk MT-PORT 1 "$MFG_PORT LinkUp"`, which names the **port** |
| `R1z` → `P1` 🆕 | **no, and the reason is one no previous non-firing has used: the single item both entries carry, they carry because `P1` CLOSED it.** `R1z`'s last ⚠️ is *"`RECIPE_ID` moved … the next card must re-derive `RLXFW-ID0`"*; the next segment found the superseded `c433013b` in three places here, its own step row says *"The next card was about to predict `MT-ID` against it"*, and the board then printed `RLXFW-ID0=BB684EB0`. This file's own rule governs — *a residual that a later gate closes is removed from the clause's input by being closed, not by being edited out*. ⚠️ The rest of the two sets do not touch: `R1z`'s residuals are about this repository's record, `P1`'s about a design table that over-declares on three rows and a denominator its own does-not-establish list got wrong |
| `R6` → `P2` 🆕 | **no — `P2` CLOSED three of `R6`'s residuals, each taken on in writing by one of its own steps, and the one subject both still carry is two different observations.** Closed: *"`D5`'s headline number needs a verb typed"* — `P2-2` compiled `recover` on, and `P1-N0` read `recov_mode 1` on both days with no verb typed; *"this project holds no vendor receive figure at all"* — `P2-3`'s `eth4` board-receive trials (`NET-114`), reproduced in seating B at 24.572 / 24.653 / 23.923 Mbit/s; and `NET-109 殘留`'s healthy baseline — `P2-3`'s pre-traffic pair, 294 = 294, and 414 = 414 in seating B. The other half of `NET-109 殘留`, its mechanism, has been `R6b`'s in the row's owner cell since the commit that opened `P2`, so `P2` never took it on. ⚠️ `rlx0`'s transmit path is in both sets: `R6` as `NET-67 殘留`, *why the engine stops retiring a TX descriptor*, and `P2` as frames the driver counts as sent that do not leave port 3 intact (`NET-112`, `NET-116`). What would join them is `R6b`'s candidate M8, and M8 is 推 — the same subject, not yet the same thing 🔄 **2026-09-28, decided at fourteen entries with `M8`'s result in view, as that run asked:** `M8` as written is refuted — block 46 stalled with no jabber — and one variable, `txlen`, removes both symptoms, the corruption (`D2`) and the stall (`D4`: 0 fires at the fix, 12 at 1.4 on the same boot). So the two were one fault at the level of the fix (量) and not of a mechanism (推). The verdict above is what that run could see, recorded and not re-scored (below, fourteen entries) |
| `P2` → `R6b` 🆕 | **yes — the mechanism of `rlx0`'s transmit fault, as a cause.** `P2` carries it as *"rlxfw's own driver has no throughput figure at the n the DoD asks for, and why is `R6b`'s"* and, in the same paragraph, *"The mechanisms are eight candidates, all 推"*; `R6b`'s step list took the candidates on in writing (*"… read on silicon by `R6b-3`, with every mechanism"*), and its entry carries *"the mechanism of the transmit fault, as a cause"*: the stage a span with no component measured, `M1`-cover8 a fitted rule (`NET-129`, `NET-132`). ⚠️ Four more items sit in both lists and are declined, each for its reason below |
| `R6b` → `R1y` 🆕 | **no — `R1y` did not take on the thing the fourteen-entry run fired on, and the rest of the two lists are about different objects.** `R6b`'s residuals are the device's and its bench record's: the transmit fault's and the stall's mechanisms, the fix on `SWCORE=n`, `D8`'s inherited switch state on one seating, the vendor-code scope, the reset guard, what `R6b-8` did not build, four DoD rows' edges, what `D5` set aside, the relaxed process's evidence, `C-19`'s night and the power ledger. `R1y`'s are this repository's record: rows that grew in place, records' citations that can only be read, four enforcers ⊘, a reading kept outside the tree, six exemptions as wide as their lines, `SPEC.md` and the open carried-forward rows left as they were, stale line numbers in `tools/`, a tree not swept. ⚠️ The nearest candidate, `CLK-42` 殘留's missing gate, the nearest resemblance, an instrument blind to its own subject, and the flash boundary are each declined below |
| `R1y` → `R8a` 🆕 | **no — and this run makes that verdict a run late, because entry 16 wrote no sixteen-entry run.** `R1y`'s residuals are text in this repository and the tools that read it; `R8a`'s are a second-stage loader on the silicon, flash, a counter, keys and a cache, and no step of `R8a` took an `R1y` residual on in writing, which the guard written at eight entries decides. ⚠️ The nearest candidate is a reading the tree does not hold — `FW-119`'s pre-commit reading, done by scripts kept outside the repository, beside `SPEC-R8a.md` and the verdict script — and it is declined as a shape: one is a **procedure** the tree does not repeat, the others are **artefacts** the tree does not hold. The flash boundary is not counted, for the thirteen-entry run's reason |
| `R8a` → `R7` 🆕 | **yes — that nothing rlxfw writes survives, because there is no write path and `R8b` owns the half that would give it one.** `R8a` carries *"Nothing in `R8a` writes one byte"* and *"the monotonicity the design rests on is asserted and never exercised"*; `R7` carries *"That the config store survives anything"*, and `notes/config-store.md` § 11 takes it on in writing and names the gate — *"R8 supplies the MTD backing"* — so `R7` built an A/B store with a monotonic `seq`, an erased-value exclusion and a read-back verify **for a medium it never touched**. 🔴 This is **not** the flash boundary the thirteen-entry run declined: that is the § Flash bookkeeping sentence `CLAUDE.md` requires of every entry, while this has a board row of its own and the row is open. ⚠️ Weaker than `P1` → `R6` in that neither entry names the other's gate — both point at a third, `R8` — and `R8b` is already booked behind `R9`, so the firing adds evidence and not an instruction |
| `R7` → `R8` 🆕 | **yes — the same thing as `R8a` → `R7`: persistence, that nothing rlxfw writes survives because there is no write path, and `R8b` owns the half that would give it one.** `R7` carries *"That the config store survives anything"* and names `R8` in it as the gate that supplies the MTD backing; `R8`'s entry carries persistence and the ten power cuts, moved to `R8b`'s row. ⚠️ The weakest firing in this table: `R8`'s list holds it because the decision that closed `R8` moved it there, so it adds no evidence the seventeen-entry run had not, and its instruction — *that thing is the next gate* — points at a gate booked behind `R9` |
| `R8` → `R9` 🆕 | **yes — the same thing a third consecutive time: that nothing rlxfw writes survives, because there is no write path, and `R8b` owns the half that would give it one.** `R8` carries *"That anything can be written to flash and read back after a reset"* and *"the monotonicity the design rests on is asserted and never exercised"*; `R9` carries *"That `R8b` is any closer"* — 讀 `MK5` gates `rtl819x-spi-write.o` on `CONFIG_MTD_RTL819X_WRITE` and 量 `R9-5` found the object absent from both staged trees. 🔴 **The clause's instruction is already carried out**: `R8b` is booked as a gate of its own and is the next gate in the owner's serial order, so this firing adds evidence and not an instruction — the third consecutive firing on one subject, which is itself the reading. ⚠️ What it does not establish: a rule that fires more often because the ledger got longer is measuring length, not repetition, and whether the clause should stop counting a subject already booked as a gate is an open question about the clause that this entry does not decide |
| `R9` → `R8b` 🆕 | **no — `R8b` closed the subject the last three pairs fired on, and a second of `R9`'s residuals with it.** `R9` carries *"That `R8b` is any closer"* and *"That the flash bracket would detect a small write"*; `R8b` wrote a slot, booted it from flash and survived ten cuts (claims ① and ②), and the `cs6c` re-install changed one byte in each of two 64 KiB regions, which the 4 KiB map resolved to exactly those regions' first units — group 0 moved on `0x010000` alone, its other 31 units equal (`X-W2c-m0f` against `X-K2c-m0f`), and in group 1 the rescue region moved on `0x020000` alone (the barrier's sixteen units there moved too, because `W4b` erased them between the two maps) — a known change, which is the sensitivity control `R9` said needed a write. ⚠️ Closed for an image a provisioning boot writes, not for anything the running firmware writes — `R7`'s config store is no nearer, and that is in neither list. Both entries carry a 推 refuted inside the gate that wrote it (`FW-198`; `R8b`'s *"`W3` overwrote the rootfs at `0x130000`"*, refuted by the dump); declined as a resemblance, the ten-entry run's rule. The flash boundary is not counted, the thirteen-entry run's reason |
| `R8b` → `P3` 🆕 | **no — the one thing both entries carry is `P3`'s power tree, and three recorded decisions declined it.** `R8b` carries *"no voltage was read, so `P3`'s power tree stays undelivered"*; `P3` carries the plan's section 2 written 讀 and 推 where 量 was asked. `S0b` and `BRD-01` are ⊘ and entry 20's ruling 2 took no voltage, and the fourteen-entry run's reason governs: *the clause surfaces what nobody decided, and a ⊘ is a decision.* ⚠️ The weakest decline in this table: the earlier entry names the later gate — the shape of `P1` → `R6`, `P2` → `R6b` and `R7` → `R8`, all three of which fired, and of `R9` → `R8b`, declined only because the later gate had closed the thing. Most of `R8b`'s other residuals are quoted in `docs/bringup.md` § 16.7, not carried; the instruments the tree does not hold are in neither the report nor `P3`'s list, and `v1.0`'s image has since booted from a slot (`FW-255`); one unit and the flash boundary are not counted |
| `P3` → `R6c` 🆕 | **no — `R6c` closed the one counted item `P3` carried and named it to fix, and the nearest candidate was ruled on by the owner before any code.** `P3` carries *"A network on the boot the device makes by itself … the fix is `R6c`'s"*; `R6c` booted `9bb2bec7` from slot A after a watchdog reset and after a cold power-on and pinged both ways, 4 of 4 each way (`NET-173`) — the shape of `R9` → `R8b`, declined because the later gate closed the thing. ⚠️ The nearest candidate is the minimum configuration: `P3` carries *"no minimum configuration"* (`docs/bringup.md` § 16.4) and `R6c` carries which of its 17 stores is necessary; the owner's ruling O1 wrote the group as a unit, never partially, before `R6c-3` began — a decision, and the clause surfaces what nobody decided. If the owner reads O1 as a rule for the driver and not a decision about what to measure, the pair fires on the VLAN group's minimum write set. A second port against the WAN-side host probe is declined as two objects, and a harness that shares the driver's sources against *"That anything in the report is a second source"* as a resemblance; one unit and the flash boundary are not counted |

🔴🔴 **THE CLAUSE FIRES ON A NEW THING FOR THE FIRST TIME, AND IT TOOK EIGHT
ENTRIES.** Between five entries and seven it named exactly one thing, `CPU-45`,
from one pair, and that was written down because *a rule that fires more often
simply because the ledger got longer is measuring length, not repetition*. The
eighth entry adds one pair and that pair fires, so the clause now names **two**
things and they came from two different pairs.

**What the new firing names, in the words of the two entries that share it:**

* `R4`: *"No single invocation has run `S2` → `S7`. The bench half ran with
  `--skip S2,S3`; the desk half ran with the bench stages skipped. **73.88 s is
  a sum of two runs, not a measured total**"* — and *"the image the loop builds
  has never been uploaded by the loop … that is the one stage still untested in
  one command, and it needs the board."*
* `R5`: `R5-0` ② made it this gate's question and answered it as a decision —
  *the first bench iteration runs without `--skip S2,S3`* — and 量 over
  `bench/`, **71 of 71** real `--mode bench` invocations across six seatings
  carried `--skip`, and 71 of 71 uploaded a pre-built `--image` with
  `--recipe-override`.

🟢 **This is the shape the clause was written for, and it is the first time it
has been visible.** Every one of those 71 skips was correct where it was made:
the image was already staged, rebuilding at the bench spends ~36 s of the
scarcest resource, and `CORRECTIONS-block8.md` `D1` measured the reason an hour
before power on the first of them. **No seating could see the pattern, because
each seating's decision was locally right.** Two entries side by side is the
smallest instrument that can.

⚠️ **What it does NOT name.** The clause names a *thing*, not a gate — the
precedent is `CPU-45`, which is a question the owner has kept scheduling rather
than a gate. Where this one goes is the owner's, and it is cheap: `SEAM-1`'s own
reading (`notes/dev-loop.md` § 10.6) is that a no-skip run **needs no additional
power cycle** — it rides the opening cold boot of a seating and costs ~39 s of
board idle.

⚠️ **And one honest deduction against the firing**: `R4`'s residual is about
`R4`'s deliverable. It is counted as `R5`'s because `R5`'s own step list took it
on in writing at `R5-0` ②, not because a gate inherits its predecessor's
residuals by default. If the clause is ever read as doing the latter it will
fire on every pair and stop meaning anything.

### 🆕 At nine entries it fires again, and on something smaller than either

**What the new firing names, in the words of the two entries that share it:**

* `R5`: *"`/proc/timer_list` exists in this kernel … and it was never read.
  `R5-2` used the driver's own `/proc`, **which carries both counters inside one
  `spin_lock_irqsave`**"* — and the property `D4` wanted is *two counters read
  atomically*.
* `R1-pub`: `D-cost`'s `E5` required `Δirq_count == Δjiffies` on every rung. It
  fails **5 of 64**, all five one-sided, and the pair it names is not inside that
  lock together.

🟢 **`R5`'s sentence is not wrong, it is over-general, and that is exactly what
makes this a pair rather than a repetition.** `R5-2` read `jiffies` against
`ce_cycles`, and both of those **are** snapshotted inside the lock. The bullet
generalised from the pair it used to *both counters*, and the pair the next gate
needed turned out to be a different one in the same file.

⚠️ **The guard this section carries for itself is applied, and it passes.** *A
gate does not inherit its predecessor's residuals by default; if the clause is
ever read as doing the latter it will fire on every pair and stop meaning
anything.* `D-cost`'s block cites neither `R5`'s `D4` nor this file. It required
the property independently, in its own words, and independently failed to get it.
**Two gates arriving at one wall from different directions is what the clause is
for**, and it is a stronger pair than an inherited residual would have been.

⚠️ **And the honest deduction against it.** `R5`'s bullet was written 2026-09-11
and `R1-pub`'s on 2026-09-16, five days and two sittings apart — but *the reading
that shows `R5`'s sentence to be over-general* was taken in the segment that wrote
the ninth entry, by opening the driver. **The pair is real; one half of it is one
day old**, and the first three runs of this clause carry the same caveat for the
same reason.

🟢 **What it would cost, because a firing that names something unbuildable is
not worth having.** Snapshotting `irq_count` inside `rtl819x_tc_lock` in that
`/proc` read is three lines and needs no new instrument. What it needs after that
is a measurement that the five one-sided differences go away — and 🔴 **if they do
not, the mechanism is something other than sampling skew, and that is the larger
finding**: the gap between the two reads is symmetric in sign, so it does not
predict five differences of the same sign in sixty-four rungs. **Where the thing
goes is the owner's**, which is the precedent `CPU-45` set at five entries.

### The pattern the clause still cannot see, now at three instances

🔴 **At seven entries this section recorded a residual that repeats and that the
rule cannot reach — a DoD that named an artefact instead of the property it
wanted. The eighth entry is the third instance, and they are at entries 4, 6 and
8: every other one.**

* `R3`'s `D3` named the string `MemTotal:`, which this kernel never prints.
* `P4b-gate`'s `D2` named the path `study/weekly-results.md`, which is
  gitignored by a ruling the same gate made.
* `R5`'s `D4` named `/proc/timer_list`, which exists in this kernel and cannot
  carry the property the row wanted — two counters read atomically.

The rule says *consecutive*, and no two of those are. ⚠️ **The rule is still not
changed**, for the reason written here at seven entries and unchanged by a third
instance: changing a rule because it failed to produce the answer you had
already reached is how such a rule stops being an instrument. A third data point
makes the pattern more certain; it does not make the change less circular.

🔴 **What was done instead is a census, with its refutation condition written
before it ran.** *If the census finds a fourth instance nobody here already
knows about, an enforcer has a real target and a real positive control and gets
written in the segment that has one; if it returns only the known instances, the
base rate rests on three points and an instrument fitted to three points should
not exist.*

量 2026-09-11 over the whole population — every gate-level DoD row this project
has written in `D`-row form: `R3` 5, `P4b-gate` 4, `R4` 4, `R5` 4 = **17 rows**
across four gates, plus the gate-board sentence for the four gates that predate
the form. **Three instances, all three already known. No fourth.** So the
enforcer is **not written**, and this paragraph is what that decision rests on
rather than a preference.

🟢 **The census did turn up something else, of a weaker class, and it is
recorded because nothing here connects the two halves.** `R3`'s `D5` names the
observable `ping -c 4`, and `SPEC.md` `NET-26` measures that **this image's
`ping` ignores `-c` and always sends four packets**. The row was met, and it was
met because the default happened to equal the request. That is not the same
defect — the artefact *could* deliver the property — but it is an **inert token
in an observable**, and a search of every committed `.md` finds no file that
puts `NET-26` and `D5` in the same sentence.

### 🆕 The census re-run at nine entries, and what entry 9 adds instead

🔴 **The refutation condition above was pre-registered, so it is re-run rather
than assumed.** 量 2026-09-16 over the widened population: the `D`-row form is now
**30 clauses across five gates** — `R3` 5, `P4b-gate` 4, `R4` 4, `R5` 4, and
`R1-pub`'s `D1`–`D5` plus `D2b` plus `D-cost`'s `E1`–`E7` = **13** — and the four
gates that predate the form carry **13** more, in numbered- or lettered-question
tables rather than in `D` rows. **The three instances are the same three. No
fourth.** The enforcer stays unwritten, for the reason already given.

🔴 **What entry 9 adds is a DIFFERENT shape, three instances deep on its first
appearance.** Not *a DoD that named an artefact instead of the property it
wanted*, but **a threshold a correct instrument could not meet**:

* `E4`'s tolerance is 1 % of **the row's own** largest Δ, so it is ~50× stricter
  on cheap rows — where the absolute noise floor is the same and its share is
  largest. **A different row failed on each boot**, which is what a threshold
  sitting in the noise looks like from the outside.
* `E5`'s second conjunct demanded exact equality of two composites whose own
  source — the frozen card's § 6.2 — had measured as *"716 **or** 717"*. Allow
  that ±1 and 0 of 64 rungs fail.
* `E5`'s first conjunct demanded exact equality of two counters the serving
  `/proc` file does not sample together.

⚠️ **All three sit at entry 9, so there is no consecutive pair and the clause
cannot fire on this shape either.** 推, and written down because it is checkable
later: all three are in one `D-cost` block, and that block was written **late, in
one sitting, to fill a hole a correction left when it struck *"with a measured
cost"* out of `D4` and wrote no replacement anywhere**. A shape that appears three
times in one hurried block and not once in four previous gates is more likely a
property of how that block was written than of this project's DoDs.

🔴 **And there is a widening that would make it fire, declined here for a stated
reason.** `R5`'s `D4` records its ± 50 ppm bar as *"met by three orders of
magnitude against a bar that measures the wrong thing"*. Read as one family — *a
threshold whose scale is not the scale of the quantity it judges* — that is entry
8, `E4` is entry 9, **and the pair is consecutive**. It is declined because the
two fail in opposite directions (one cannot fire at all; the other fires at
random), and because inventing a category that makes a rule fire is the same
circularity as changing a rule that failed to fire, wearing the other coat. **It
is recorded so the tenth entry can decide it with this one in view** — which is
the only thing that stops the decision being made twice by accident.

### 🆕 At eleven entries the clause does not fire, and the reason is one no previous non-firing has used

**What the new pair shares is one item, verbatim, in both entries — and `P1`
CLOSED it.** `R1z`'s last ⚠️ reads *"`RECIPE_ID` moved … the next card must
re-derive `RLXFW-ID0`."* The very next segment found the superseded value
`c433013b` written in three places in this repository and its own step row says
*"The next card was about to predict `MT-ID` against it"*; the id was recomputed
from `config/`, the card was corrected before it froze, and the board printed
**`RLXFW-ID0=BB684EB0`** on both boots. 量 again at this entry, independently of
any record: `find config -type f | sort | xargs sha256sum | sha256sum | cut -c1-8`
over 30 files returns **`bb684eb0`**.

This file's own rule decides it: *a residual that a later gate closes is removed
from the clause's input by being closed, not by being edited out.* So the pair
does not fire, and it does not fire for the **good** reason rather than the
absence of one.

🟢 **An observation about the clause itself, recorded and deliberately not made
into a rule.** There have now been exactly two residuals in this ledger's history
discharged by a later gate rather than repeated — `P4a`'s *`ID0` has never been
read off the board*, closed by `R4`'s seating, and `R1z`'s *the next card must
re-derive `RLXFW-ID0`*, closed by `P1`'s. **Both are the same field.** Two points
is not a pattern; it is written down so a third can be recognised rather than
discovered.

⚠️ **The rest of the two residual sets do not touch**, and the ten-entry run's own
discipline is what says so: `R1z`'s are about this repository's record and `P1`'s
about a design table that over-declares and a denominator that was miscounted.
Both gates contain *an instrument that could not be asked about its own subject* —
which is the same SHAPE the ten-entry run already refused to fire on, and refusing
it twice is cheaper than inventing a precedent.

### 🔴 The tenth entry was handed a decision and did not make it

The nine-entry run closed with a widening it declined, and with a sentence about
what to do next: *"It is recorded so the tenth entry can decide it with this one
in view — which is the only thing that stops the decision being made twice by
accident."*

量 2026-09-17, by `git show` on `126f659` rather than by re-reading: the tenth
entry changed **three** things in this section — the heading, one clause in the
parenthetical, and one row of the pair table. **It did not decide the widening,
and it did not re-run the census**, although the nine-entry run had pre-registered
the census as *"re-run rather than assumed"*. A repository-wide grep finds the
decision made nowhere else either. **So it is made here, one entry late, and the
lateness is part of the record.**

### 🆕 The widening is declined a second time, and this time by a measurement

The family proposed at nine entries was *a threshold whose scale is not the scale
of the quantity it judges*: `R5`'s `D4` ±50 ppm bar, *"met by three orders of
magnitude against a bar that measures the wrong thing"* (entry 8), and `D-cost`'s
`E4`, a 1 %-of-the-row's-own-Δ tolerance sitting in the noise (entry 9). Adopted,
it would have fired on a consecutive pair.

**Entry 11 supplies a third instance, and it is what settles the question.**
`MT-TICK`'s original criterion was `dj > 0 && skew ≤ 2`, and 量 `C10-M28`: with
`cereload 20000` the line reads **`dj=503 di=503 skew=0`** — the tolerance
satisfied, on a board whose clock was running at a tenth of its rate — because one
interrupt advances both counters. That is `D4`'s failure mode exactly: **a bar met
by construction rather than by the hardware being right.** `E4`'s failure mode is
the opposite one, a threshold that fires at random.

**So over three points the family splits two against one, and the two that match
each other are entries 8 and 11, which are not consecutive.** The widening does
not make the clause fire even on its own terms, and it is declined — 🟢 **for a
reason that arrived as a reading rather than as an argument, and which removes a
firing instead of creating one.** That is the opposite of the circularity the
nine-entry run was guarding against, and it is why the decision is worth having
waited for.

⚠️ **The honest deduction against it.** The third instance was nominated by the
entry that also decided the question, which is the shape the clause's own caveats
warn about. What keeps it admissible is that the reading was not fitted: the
`NO-TAKE` diagnosis for `M28` was **pre-registered before the board was powered**
(`bench/2026-09-17/PREDICTIONS-B24-block23.md` §, 讀), and `dj=503 di=503 skew=0`
was then produced by the die in the same capture that reports the clock wrong.

### 🆕 The census re-run at eleven entries — no fourth, and the weaker class doubles

量 2026-09-17 over the widened population: the `D`-row form is now **38 clauses
across seven gates** — `R3` 5, `P4b-gate` 4, `R4` 4, `R5` 4, `R1-pub` 13,
`R1z` 4, `P1` 4 — with the four gates predating the form carrying 13 more in
numbered- or lettered-question tables. **The three instances are the same three.
No fourth.** The enforcer stays unwritten, for the reason given at seven entries
and unchanged by a fourth run of the check.

🔴 **What entry 11 adds is a second instance of the WEAKER class, and the class
had exactly one.** The nine-entry run recorded it as *an inert token in an
observable*: `R3`'s `D5` named `ping -c 4`, and `NET-26` measures that this
image's `ping` ignores `-c` and always sends four — **the row was met because the
default happened to equal the request.** `P1`'s `D3` is the same thing one layer
up: it names *the `FLR` bracket*, **no `FLR` ran in this gate**, and the property
it wanted — the unit unchanged — was delivered by `MT-FLASH-3`'s 32-group map over
4,186,112 bytes, roughly four thousand times the bracket's 1,024. **The named
instrument was capable and idle; a different one did the work.**

⚠️ The two sit at entries 4 and 11, so the rule's *consecutive* still does not
reach them, and the rule is still not changed — the argument at seven entries
holds: changing a rule because it failed to produce an answer you had already
reached is how such a rule stops being an instrument. **What is different is that
the weaker class now has two points and a name**, so the twelfth entry can
recognise a third rather than rediscover the class.

### 🆕 At twelve entries the clause FIRES, and the thing it names was handed from one gate to the next BY NAME

**What the new firing names, in the words of the two entries that share it:**

* `P1`: *"`MT-PORT` declares *"link up on the connected port, **and the output
  names the vendor driver**"* and `mt_port` prints
  `chk MT-PORT 1 "$MFG_PORT LinkUp"`, which names the **port**"* — and, in the
  bullet after it, *"every `MT-PORT` line this project has captured is
  unlabelled as to which driver served it. **Carried to `R6-0`.**"*
* `R6`: `R6-0`'s own cell quotes that residual — *"a row `R6` can bank for free
  and a thing the census must not miss"* — and banks **the half about the
  measurement**, `SPEC.md` `NET-31`, the Linux-side link state on a named port.
  量 2026-09-22, `config/mfgtest.sh:536` is unchanged.

🟢 **This is the first firing where the earlier entry names the later gate**,
so the `R4` → `R5` deduction does not apply: that one had to argue that `R5`
took the residual on *in writing*, and here `P1` assigned it and `R6-0` quoted
it back. **Nothing has to be read into either entry.**

🔴 **And the firing names something that got WORSE rather than staler.** When
`P1` wrote it there was one driver, so an unlabelled `MT-PORT` line was
ambiguous only in principle. `R6` landed a second one. 🔴 量 2026-09-22, and
this is the part that makes the fix bigger than a `printf`:
`config/mfgtest.sh:57` reads `$MFG_ROOT/proc/rtl865x/port_status`, which is
the **vendor's** `/proc` file and is present in every `R6` image
(`SPEC.md` `NET-109`). That file reports the **switch port's** link state,
which is true no matter which `net_device` is bound to the CPU port — so the
label `P1`'s design table promised **is not obtainable from the source
`mt_port` reads at all**. The fix is a different source, not a different line.

⚠️ **Where it goes is the owner's**, as `CPU-45`'s firing was: the clause names
a thing, not a gate. What it costs is small and measured — the discriminating
reading already exists (`NET-31`'s seven fields, and `/proc/interrupts`' line
number, which is `NET-51`'s three-state control) and neither needs power.

### 🆕 The census re-run at twelve entries — THE FOURTH INSTANCE ARRIVES, and the enforcer is still not written

量 2026-09-22 over the widened population, re-derived rather than carried: the
`D`-row form is now **44 clauses across eight gates** — `R3` 5, `P4b-gate` 4,
`R4` 4, `R5` 4, `R1-pub` 13, `R1z` 4, `P1` 4, **`R6` 6** — with the four gates
predating the form carrying 13 more in numbered- or lettered-question tables.
**57 clauses.**

🔴🔴 **There IS a fourth instance, and it is `R6`'s own `D6`.** The row asks
for *"zero drops **by the driver's own counters**"* — an artefact — where the
property it wants is *no frame lost*. 量 `SPEC.md` `NET-62`, seating 30: the
driver's `n_rx` counted **every one of 5,281 frames** while **218 datagrams
died above it**. The named instrument reports zero, truthfully, while the
property fails.

🔴 **The pre-registered condition is still not met, and the wording is why.**
It reads: *if the census finds a fourth instance **nobody here already knows
about**, an enforcer has a real target and a real positive control and gets
written in the segment that has one.* This one is known, with an id, since
2026-09-20 — `D6`'s own row in `PROGRESS.md` says *"the DoD's own instrument is
the one this fault is invisible to, which is `NET-62`"*. **So the trigger is
the unknown fourth, and the fourth is not unknown.**

🔴🔴 **And the second reason is the stronger one: this is the first of the four
an enforcer could not have caught.** The other three fail *loudly*, and each
failure is a question a checker can ask of an artefact — *does this kernel
print `MemTotal:`*, *is this path in `git ls-files`*, *does this `/proc` file
sample two counters together*. `D6`'s counter exists, is read on every run, and
returns **0** correctly. To flag it a checker would have to already know which
fault the counter is blind to — **which is the thing the check was supposed to
find**. An enforcer fitted to the first three would have passed the fourth.

🟢 **That boundary is a measurement and not an excuse, and what shows it is a
SECOND decline made the same day for the OPPOSITE reason.** `SPEC.md` `FW-109`
records a family found while closing this gate — a citation that was wrong the
day it was written, five instances, every one of which `citecheck` reports
`STABLE` — and that family **is** buyable: four of the five quote the cited
text on the citing line, so the rule is *a line carrying a quoted string and a
`FILE:NNN` must find that string at or near `NNN`*, `M4` already does a
narrower version over 28 citations, and the four are its positive controls. It
is declined for a **scheduling** reason. **Two declines, one day, two
different reasons — which is what stops either from being a preference.**

⚠️ **The weaker class does not gain a third and is left at two.** `R6`'s
`ethtool` ops are present-and-inert, which reads like entry 11's *capable and
idle*, but they are named by a **step's deliverable** and not by a `D` row, and
this census's population is `D` rows. Recorded so a thirteenth entry does not
find it and call it a third point.

### 🆕 At thirteen entries the clause does not fire, and the later gate had closed three of the earlier one's residuals

**What the new pair shares, item by item.** `R6`'s entry lists ten things it did
not establish. `P2` closed three of them, and closed each because one of its own
steps took it on in writing before its first seating:

* *"`D5`'s headline number needs a verb typed"* — `P2-2`'s images compiled
  `recover` on (`NET-107`), and `P1-N0` read `recov_mode 1`, `ph_follow 1` on
  both days with no verb typed.
* *"this project holds no vendor receive figure at all"* — `P2`'s list opens by
  saying so, `D5` (b) asks for both directions on both drivers, and `P2-3`'s
  `eth4` board-receive trials made one (`NET-114`), reproduced in seating B.
* `NET-109 殘留`'s *"a healthy baseline costs no power"* — `P2-3`'s own row
  names the pre-traffic `asicCounter` reading, and 量 the pair read the healthy
  shape on both days (294 = 294, 414 = 414).

Three more went to `R6b` by the owner's word when it was booked and opened —
`D4`'s second conjunct, `R6-4`'s `ethtool` and `phylib`, and `MT-PORT`'s
driver label, which was the twelve-entry firing's subject and so now has an
owner (讀 § Gate board, `R6b`). This file's own rule decides the closed three:
*a residual that a later gate closes is removed from the clause's input by being
closed, not by being edited out.* The other half of `NET-109 殘留`, its
mechanism, was never `P2`'s: the row's owner cell has read *`P2`（`P2-3`
流量前的讀數）／`R6b`（機制）* since the commit that opened `P2`. **A gate does
not inherit its predecessor's residuals by default**, which is the guard this
section wrote at eight entries, so the mechanism is not counted as `P2`'s. Two
more, `R6-6`'s unreachable clauses and the power ledger's four undefined words,
are not in `P2`'s list at all. That leaves two, and both are below.

🟢 **And that ends a coincidence this section wrote down at eleven entries.** It
recorded exactly two residuals ever discharged by a later gate rather than
repeated, and noted *"Both are the same field"* — `RLXFW-ID0` — *"written down
so a third can be recognised rather than discovered."* The third, fourth and
fifth arrive together here, and none of them is that field. What the three new
ones share is that a step of the closing gate took each on in writing before its
first seating. ⚠️ Whether `P4a`'s and `R1z`'s were taken on the same way is not
re-read here, so that is not offered as the pattern.

⚠️ **The nearest candidate is one subject seen as two faults, and it is declined
as a resemblance.** `R6` carries `NET-67 殘留`, *why the engine stops retiring a
TX descriptor*: four descriptors held, the queue stopped. `P2` carries what it
found and did not explain: frames the driver counted as sent that never left
port 3 (`NET-112`, reproduced as `NET-116`), which block 45 then placed in
frames of lengths the engine was not given (`NET-119`). Both are `rlx0`'s
transmit path, and `P2`'s trials stopped the queue six times as well. But the
observations differ — in one the engine keeps its descriptors, in the other it
hands them back with the frame wrong — and what would make them one fault is the
candidate `R6b` calls M8, *an overlong frame keeps the engine from retiring
descriptors*, which is 推 (`notes/nic-driver.md` § 21). The ten-entry run's rule
governs: *a clause that fires on a resemblance measures the reader, not the
ledger.* 🔴 **The honest deduction against declining it**: if M8 holds, the
stall and the corruption are one fault and this pair should have fired. A clause
that compares what two entries say cannot see a common cause behind two symptoms
that each entry measured on its own. Declining costs nothing here: the owner
opened `R6b` on this fault on 2026-09-25, before this run, and the entry that
closes `R6b`, which owns both, decides it with M8's result in view.

⚠️ **One item is in both lists, and in `R1z`'s and `P1`'s before them, and
neither of the last two runs mentioned it: the flash boundary** — zero
flash-write commands and zero `FLR`, the reach of the maps or the bracket, and
the 0.0244 % the `FLR` bracket covers. Counted by the letter, it has been a
shared item at every pair since eleven entries. **It is not counted, and this
run says why instead of passing over it a third time**: `CLAUDE.md` § Flash
requires every seating record to close with exactly this — the commands issued,
the bracket's reach and what it cannot see — and each entry carries it forward
from its seatings. It is a sentence the rules put in every entry, not a thing a
gate set out to establish and did not, and a clause that fired on it would be
measuring the rule. ⚠️ What it describes is real and open all the same:
`FLS-26`'s undetermined 8,192 B are exactly `H601`, which the map skips by rule,
and no before-and-after comparison sees two writes that cancel. Where that goes,
if anywhere, is the owner's.

### 🆕 The census re-run at thirteen entries — a fifth instance, and the second an enforcer could not have caught

量 2026-09-25 over a population re-derived by a script
(`$FWRE_WORK/rebuild/s111/land/gate/census.py`, its control `census-ctl.sh`
beside it) that first reproduces the twelve-entry figures from `PROGRESS.md` —
44 clauses across eight gates — and goes red on a copy with one of `P1`'s rows
un-bolded: the `D`-row form is now
**52 clauses across nine gates** — `R3` 5, `P4b-gate` 4, `R4` 4, `R5` 4,
`R1-pub` 13, `R1z` 4, `P1` 4, `R6` 6, **`P2` 8** — with the four gates
predating the form carrying 13 more in numbered- or lettered-question tables,
carried rather than re-derived because those step lists are records. **65
clauses.**

🔴 **There is a fifth instance, and it is `P2`'s own `D8`.** The row reads
*"network up is the first ICMP echo reply"* — an artefact named as the property.
The first reply comes when the host's ARP broadcast of that cycle is answered,
so its time carries the host's retransmit schedule. 量: the vendor's first
replies in seating A spread over 1.1 s, *"made by the host's ARP retransmit
timing, not by the boot"* (`notes/boot-time.md` § 7.7); the vendor answered a
cycle's third broadcast in five boots that day and a cycle's first in all nine
the next; and the contract's quiet cold `D8` width — the host's ARP phase
against `N-NDOPEN` — is one of the six numbers that did not reproduce. The
row's own refutation condition guards the channel offset, a quantity of
hundreds of microseconds; the artefact it named carries an error of up to about
a second. The gate measured around it — every network up is a bracket whose
upper edge is the reply — so what failed is the row's wording, the way
`P4b-gate`'s `D2` named a path while the property landed at another.

🔴 **The pre-registered trigger is still not met, and the twelve-entry run's
second reason decides it on its own.** Whether this instance counts as one
*nobody here already knows about* is arguable: the host-phase dependence has
been written down since seating A's record, two days before this census, but no
one had named it as a DoD defect. It does not need settling, because **like
`R6`'s `D6`, this is an instance an enforcer could not have caught.** The reply
is real and correctly stamped; to flag the row a checker would have to know the
host's ARP schedule, which is the finding and not a property of the artefact.
**Two of the five are now of that kind, and they are the two most recent** —
recorded, not made into a rule, for the reason this section has given since
seven entries. ⚠️ And for the first time two instances sit at consecutive
entries, 12 and 13. The seven-entry run named non-consecutiveness as the reason
the clause could not reach this class; with that gone, the clause still does not
reach it, for the reason the ten-entry run gave: what repeats is a shape of DoD
row, not a thing either entry lists as not established.

⚠️ **The weaker class stays at two.** `P2`'s `D4` names *"a host port census"*,
and the census that ran was TCP only, so for the vendor's UDP daemons the
scripts and the console did the work — which reads like entry 11's *capable and
idle*. It is not counted: the census was not idle, it did the TCP half, and the
gap is a choice of scan the row never made, which the feature table's method
states. Recorded so a fourteenth entry does not find it and call it a third
point.

### 🆕 At fourteen entries the clause FIRES, on the mechanism of `rlx0`'s transmit fault — handed from one gate to the next by name

**What the new firing names, in the words of the two entries that share it:**

* `P2`: *"rlxfw's own driver has no throughput figure at the n the DoD asks for, and why is
  `R6b`'s"* — and in the same paragraph, *"The mechanisms are eight candidates, all 推
  (`notes/nic-driver.md` § 21)."*
* `R6b`: *"The mechanism of the transmit fault, as a cause"* — the stage a span with none of its
  components measured, what the engine fetched unseen, `M1`-cover8 a rule fitted after blocks 45
  and 46. Its step list took the candidates on in writing when it opened: *"M1, M2 and M3's
  descriptor read-back go to `R6b-2`'s image and are read on silicon by `R6b-3`, with every
  mechanism; M5 still has no step"*, with a refutation condition written for five of them.

🟢 **This is the second firing where the earlier entry names the later gate**, after `P1` → `R6`, so
nothing has to be read into either entry: `P2` wrote *"why is `R6b`'s"*, and `R6b`'s list quoted
the candidates back.

🔴 **And `R6b` took it much further than `P2` left it, which is the deduction against the
firing.** `P2`'s throughput half is closed — `D3` met 12 of 12 on two boots — and seven of the eight
candidates were read: `M2` and `M7` refuted, `M1` narrowed in loopback to one field, `m_len`, `M3`
reduced to two lengths' history, `M4` observed and kept, `M6` not fired, `M8` refuted as written;
only `M5` never ran. The fault is fixed, at the default. What both entries still carry is a cause
inside a span no instrument on this bench sees into — the engine's fetch, its DMA, the CPU
interface's framing — for which the documents held (D, B) give the fields and not the engine's
rule. **So the clause names an explanation, not a defect**, and like `R4` → `R5`'s firing it may be
a thing that cannot be done here: the read-back that would show the fetch is a read of memory with
the fetch held. 🟢 What it would cost, for the part that can be done: `M5`, the `tx` verb with the
vendor's port-list mask at the seven lengths under 1.4 — one press, no image.

**The thirteen-entry run's deferred question, decided.** That run declined `R6` → `P2` as one subject
seen as two faults and wrote: *"the entry that closes `R6b`, which owns both, decides it with M8's
result in view."* `M8`'s clause fired on block 46, so `M8` as written — *an overlong frame keeps the
engine from retiring descriptors* — is refuted: a stall came with no jabber. But what that run
needed `M8` for, that the stall and the corruption are one fault, holds at the level of a single
variable: `txlen` removes the corruption on blocks 47 and 48 (`D2`) and the stall on block 50 (`D4`:
0 fires at the fix, 12 at 1.4 on the same boot), 量. At the level of a mechanism it is 推: the
stall follows wrong-length frames, jabbered or counted nowhere (`A2-02` had 14 counted nowhere). So
`R6`'s `NET-67` 殘留 and `P2`'s corruption were one fault seen through two symptoms — the case that
run described, *"a clause that compares what two entries say cannot see a common cause behind two
symptoms that each entry measured on its own."* 🔴 **Recorded, not re-scored**: the thirteen-entry
verdict stands as what it could see, and its row carries this decision. With it, the mechanism of
`rlx0`'s transmit fault has been in three consecutive entries' *what it did not establish* — `R6`'s
as the stall's why, `P2`'s as eight candidates, `R6b`'s as the cause behind the one variable that
removes both.

⚠️ **What the firing does NOT name, item by item — four more things are in both lists:**

* **`1472|mdev`.** `P2` carried it as a miss; `R6b` ran the experiment `P2` named, and the rise
  recurred on both drivers and in both capture states, so it is not `rlx0`'s; the row is ⊘ by a
  ruling with a reopening condition. Declined because the record already decided it: the clause
  surfaces what nobody decided, and a ⊘ is a decision. 🔴 This reason is used here for the first
  time and is weaker than the others — the decision is the main session's, and **if the owner
  overrides it, `1472|mdev` is a second shared item and the pair fires on it too.**
* **The UDP receive loss.** `P2` carried *where above the driver the datagrams die*; `R6b` answered
  it — at the socket, 量, the ~64 a full queue of 63 (`NET-142`) — and carries a narrower question,
  why the socket refuses, which is ⊘ (`NET-117` 殘留). Closed where it was asked; the remainder is
  ⊘.
* **`CLK-42`.** `P2` carried *what the `asicCounter` read does to the timers*; `R6b` closed the
  attribution (block 46: the read, 112.55–115.72 jiffies each) and its own step list re-owned the
  mechanism, in writing, to `docs/interrupt-map.md` § 8.4 as off its path. The guard written at
  eight entries decides it — *a gate does not inherit its predecessor's residuals by default* — and
  here the later gate's list gave it away in writing. ⚠️ Its row asks the owner to assign a gate,
  and none is assigned.
* **The flash boundary**, for the reason the thirteen-entry run gave.

🟢 **And three of `R6`'s residuals, which the owner gave `R6b` when it opened, are closed** — `D4`'s
second conjunct (`D8`), `R6-4`'s `ethtool` ops and `phylib` (`D6`, `D7`), and `MT-PORT`'s driver
label, the twelve-entry firing's subject: `MT-PORT` reads `Port3 LinkUp by rtl819x-switch 1.5;
vendor tree absent` on the vendor-free image (量, arm I). **The twelve-entry firing is discharged**,
by a measurement of the property it named.

⚠️ **Where the new firing goes is the owner's**, as every firing's has been.

### 🆕 The census re-run at fourteen entries — no sixth instance, and one candidate recorded

量 2026-09-28 with the thirteen-entry script (`$FWRE_WORK/rebuild/s111/land/gate/census.py`, read
only), whose control reproduced the twelve-entry figures — 44 clauses across eight gates — before it
printed anything else: the `D`-row form is now **60 clauses across ten gates** — `R3` 5, `P4b-gate`
4, `R4` 4, `R5` 4, `R1-pub` 13, `R1z` 4, `P1` 4, `R6` 6, `P2` 8, **`R6b` 8** — with the four gates
before the form carrying 13 more, carried rather than re-derived because those step lists are
records. **73 clauses.** ⚠️ The script's closing line still says *thirteen-entry*; it was written for
that run, and what is read here is its per-gate lines.

**No sixth instance.** One candidate, recorded so a fifteenth entry does not find it and call it a
sixth: `D2`'s *"on a fixed image"*. Both of its boots ran an image whose default was 1.4's, with the
fix typed as a verb; the image whose default is the fix ran afterwards, once, and not as a `D2` boot
(`NET-158`). It is not counted: the row names a property of the object under test, and that property
was measured on that object in the typed setting, by the same cells as the unfixed setting; what the
word *image* promised arrived one step later, inside the gate. It is `R6`'s verb shape — `recover`
then — and not the artefact-for-property shape. ⚠️ **The weaker class stays at two.**

### 🆕 At fifteen entries the clause does not fire, and the fourteen-entry firing was neither discharged nor carried

**The thing the fourteen-entry run fired on is not in `R1y`'s list, because `R1y` did not take it
on.** That run fired on `P2` → `R6b` — *the mechanism of `rlx0`'s transmit fault, as a cause* — and
left to the owner where it goes. On 2026-09-30 the owner opened `R1y`, a desk gate on this
repository's record, and § Now at `e274ccb` says so: *Entry 14's operating clause still names the
mechanism of `rlx0`'s transmit fault as the next gate by its own rule; the owner opened `R1y` first,
and that gate is not opened.* No step of `R1y` touches the device. The guard written at eight
entries decides the pair — *a gate does not inherit its predecessor's residuals by default* — so the
mechanism is not counted as `R1y`'s, and the fourteen-entry firing is neither discharged, as the
twelve-entry firing was by a measurement of the property it named, nor repeated. 🔴 **The clause's
rule — *that thing is the next gate* — was not followed at the first opening after it fired**, and
this run records that rather than scoring it: the clause names a thing, not a gate, the precedent
`CPU-45` set at five entries.

**Item by item, the rest do not touch.** `R6b`'s entry lists sixteen things it did not establish and
`R1y`'s twelve. `R6b`'s are about the silicon and the bench — a fault's mechanism and a stall's, a
fix not re-tested on the mainline image, one seating, one image, one boot path; `R1y`'s are about
text in this repository and the tools that read it. Nor did `R1y` close any of `R6b`'s: `R1y-6`'s
population was § 17's open rows, and none of them named `R6b`.

⚠️ **The nearest candidate is an owner no gate holds, and it is declined.** `R6b`'s *what `D5`
carries* re-owned `CLK-42` 殘留's mechanism to `docs/interrupt-map.md` § 8.4, *whose row asks the
owner to assign it a gate*, and 讀 at `e274ccb` that section still says *no open gate owns the
question*. `R1y` repaired owners in `SPEC.md` § 17 only, by the owner's scope, and `CLK-42` has no
row there (讀: no occurrence between § 17's heading and § 19's). `R1y`'s list does say that an owner
question kept outside § 17 was outside its population — the class `CLK-42` belongs to — but the step
list never took `CLK-42` on, and the guard written at eight entries decides it, as it decided
`CLK-42` at fourteen entries.

⚠️ **The nearest resemblance is an instrument blind to its own subject, and it is declined as a
shape.** `R6b`'s read-back reads descriptor memory with the engine's fetch held, so it cannot show
what the engine fetched; `R1y`'s `citecheck` calls a citation wrong the day it was written `STABLE`,
and every repair re-dates its own line (`FW-109`, `FW-119`). Two instruments, two subjects; the
ten-entry run's rule governs: *a clause that fires on a resemblance measures the reader, not the
ledger.*

⚠️ **The flash boundary** is in both lists — `R6b`'s with its maps, `R1y`'s with zero
power-ons — and is not counted, for the reason the thirteen-entry run gave.

### 🆕 The census re-run at fifteen entries — no sixth instance, and two candidates recorded

量 2026-09-30 with the thirteen-entry script (`$FWRE_WORK/rebuild/s111/land/gate/census.py`, read
only; sha256 `1e81ac1a…`) on `PROGRESS.md` at `e274ccb`, before `R1y-4` moved the closed lists out,
with the same two control arms run from this segment's directory
(`$FWRE_WORK/rebuild/s117/gr15/census15-ctl.sh`): on the real file it reproduced the twelve-entry
figures — 44 clauses across eight gates — and exited 0, and on a copy with one of `P1`'s rows
un-bolded it exited 1. The `D`-row form is now **66 clauses across eleven gates** — `R3` 5,
`P4b-gate` 4, `R4` 4, `R5` 4, `R1-pub` 13, `R1z` 4, `P1` 4, `R6` 6, `P2` 8, `R6b` 8, **`R1y` 6** —
with the four gates before the form carrying 13 more, carried rather than re-derived because those
step lists are records. **79 clauses.** ⚠️ The script reads `PROGRESS.md` alone, and from `R1y-4` on
the closed lists are in `docs/history/steps-<gate>.md`: 量 on `R1y-4`'s tree it finds `R1y`'s list
only and refuses on its control (rc 1), so a sixteenth-entry run must hand it those files too. Its
closing line still says *thirteen-entry*; what is read here is its per-gate lines.

**No sixth instance.** Two candidates, recorded so a sixteenth entry does not find them and call
either a sixth:

* **`D4`, through `FW-137`'s control.** The row adopts `TOOL-2`'s controls as their rows write them,
  and `FW-137`'s reads *七個 `--` 要讀出 `D8` join 的值到 1 µs* — the seven `--` must read out the `D8`
  join's value. The repair put the value on a new `after` line and changed no old line, the seven
  `--` among them; the control's other half, *讀得到的十三個不動*, asked that only of the thirteen joins that
  already read. The main session ruled it met. Not counted: the same sentence names the property,
  the value for those seven rounds, and the settlement written before it names the mechanism, *join
  報窗之後的第一個事件與它的距離*. What the words assumed was where the value would print, not an artefact in place
  of the property.
* **`D6`'s full `desk-sweep`**, not run on the final tree with CI standing in, which reads like
  entry 11's *capable and idle*. Not counted in the weaker class: the row is met in part, not met
  through a substitute, and the choice was the owner's, made for time, not the row's wording.

⚠️ **One clause is met by construction for part of what it counts.** `D2`'s *`citecheck` reads 0
`ROT`* cannot fail for a citation the step repaired, since the repair re-dates its own line
(`FW-119`); the row names beside it the reading that can fail. That is the shape the eleven-entry
run found at entries 8 and 11 — *a bar met by construction* — and not this census's; at entries 8,
11 and 15 no two are consecutive, so the widening declined at eleven entries would not fire on its
own terms either. **The weaker class stays at two**, and `R6b`'s `D2` *on a fixed image*, the
candidate the fourteen-entry run recorded, stays uncounted.

### 🆕 At seventeen entries the clause FIRES — and this run has to make the sixteen-entry one too, because entry 16 did not

**What this run does first, and why it is two pairs and not one.** 量 at the time this entry was
written: the heading of this section read *re-run at fifteen entries*, its last subsection was the
fifteen-entry run, and the pair table's last row was `R6b` → `R1y`. `R8a`'s entry had landed above
with **no sixteen-entry run beside it.** So two pairs arrive together, and they are decided
separately below rather than merged — a run that merges pairs to reach a verdict is doing exactly
what this section has refused since ten entries. The precedent for the late one is the eleven-entry
run's: *"So it is made here, one entry late, and the lateness is part of the record."*

**`R1y` → `R8a` does not fire.** `R1y` lists twelve things it did not establish and they are about
text in this repository and the tools that read it; `R8a`'s sixteen are about a second-stage loader
on the silicon — flash writes, a counter that never advanced, keys, a cache, a rescue payload that is
not built. Nor did `R8a` close any of `R1y`'s: no step of `R8a` took one on in writing, and the guard
written at eight entries decides that — *a gate does not inherit its predecessor's residuals by
default*. ⚠️ **The nearest candidate is a reading the tree does not hold, and it is declined as a
shape.** `R1y` carries *`FW-119`'s reading is a session's, not a tool's* — the pre-commit reading of
every citation on every edited line was done by scripts kept outside the repository and nothing in
the tree repeats it — and `R8a` carries three of that family: `SPEC-R8a.md` as the format's owner of
record, the 43-assertion verdict script, and a seating whose bookkeeping cannot be re-derived here.
But `R1y`'s is a **procedure** the tree does not repeat and `R8a`'s are **artefacts** the tree does
not hold, and the ten-entry run's rule governs: *a clause that fires on a resemblance measures the
reader, not the ledger.* ⚠️ **The flash boundary** is in both and is not counted, for the reason the
thirteen-entry run gave.

🔴🔴 **`R8a` → `R7` FIRES, and it names persistence: that nothing rlxfw writes survives, because
there is no write path and `R8b` owns the half that would give it one.**

* `R8a`: *"That an image can be written to flash. Nothing in `R8a` writes one byte"*, *"That the
  anti-rollback counter advances. Nothing in `R8a` writes it … So the monotonicity the design rests
  on is asserted and never exercised"*, and *"That the `R8` board row is met."*
* `R7`: *"That the config store survives anything"* — `/var/lib/cfg.bin` is on a filesystem that is
  ramfs in this kernel, **`R8` supplies the MTD backing**, `fsync` there verifies that the page cache
  agrees with itself, the torn-write model is a prefix write that does not model a partially
  programmed NOR word, and the `0xFF` fill and the `seq` exclusions of 0 and `0xFFFFFFFF` are *"the
  parts written **for** NOR rather than **on** it."*

🟢 **This is a firing on something both gates designed for and neither reached, and the earlier entry
does not have to be read into the later one**: `notes/config-store.md` § 11's first bullet takes it
on in writing and names the gate — *"R8 supplies the MTD backing"* — so `R7` built an A/B store with
a monotonic sequence, an erased-value exclusion and a read-back verify **for a medium it never
touched**, while `R8a` proved a loader that reads a counter out of that medium **read-only**. Two
gates arriving at one wall from opposite sides, which is what the nine-entry run said the clause is
for.

🔴 **It is NOT the flash boundary the thirteen-entry run declined, and the difference has to be
stated or this firing is the fourth pass over the same sentence.** What was declined there is the
§ Flash bookkeeping paragraph — commands issued, the bracket's reach, what it cannot see — which
`CLAUDE.md` § Flash requires every entry to carry, so a clause firing on it would be measuring the
rule. What fires here is a **functional** absence that has a board row of its own and is open on it:
`R8`'s row stays open until `R8b` runs, and `R7` shipped a design whose whole durability argument is
untested. That is a thing two gates set out to establish and did not.

⚠️ **The honest deduction against the firing is that it names something the plan has already
ordered, so it changes nothing.** `R8b` is booked and not open, behind `R9`, because `R9`'s vendor
column needs the vendor firmware still bootable from flash and slot A's first write ends that — 讀
`R8a`'s own booking. So *that thing is the next gate* is already the plan's answer, and what this
firing adds is only that the thing is now in two consecutive entries' lists, which is the evidence
the clause exists to produce rather than a new instruction. ⚠️ And unlike `P1` → `R6` and
`P2` → `R6b`, the earlier entry does not name the later **gate**: both entries point at a third gate,
`R8`. That is weaker than those two firings and stronger than `R4` → `R5`, which had to argue that
the later step list took the residual on. **Where it goes is the owner's**, as every firing's has
been.

⚠️ **What the firing does NOT name — four more things are in both lists:**

* **An instrument that could not fail on its own subject.** `R8a` carries *a suite that asked "was it
  rejected?" would have been blind* to the reordering mutation; `R7`'s claim ① is the whole gate's
  pass condition being of that kind. **Declined as a shape for the third time** — the ten- and
  fifteen-entry runs refused it twice, and refusing it a third time is cheaper than inventing a
  precedent. 🔴 Recorded all the same, because `R7`'s is the strongest instance this ledger holds: the
  tool that could not fail **was** the gate's acceptance criterion, not a checker beside it.
* **qemu certifies logic and never codegen or the ISA.** In `R8a`'s list as *"Everything else is
  qemu"* and in `R7`'s as six notes saying nothing in them ran on the device. Not counted, for the
  thirteen-entry run's reason applied to a **second** subject for the first time: it is a sentence
  `CLAUDE.md` puts in every entry that uses an emulator, not a thing a gate set out to establish. ⚠️
  That reason has now retired two candidates, which is worth watching: a rule that exempts every
  house-mandated sentence can exempt a real residual that happens to be one.
* **A piece the plan named and nobody built.** `R8a`'s `rlxboot-rescue` is *"a region and a refusal,
  not a payload"*; `R7g` (TLS) is outside `R7` by the plan's own cut order. Declined as a resemblance
  — one is unbuilt against its own gate's question ③, the other was cut before the gate opened, and a
  cut is a decision.
* **A credential or key that is not production-grade.** `R8a`'s development seed is 32 bytes of
  `0x42` in the tree on purpose; `R7`'s `admin.pwhash` sits behind a CRC-32 that is not a MAC, so
  anyone who can write the store can set any password. Two different objects, and the clause names a
  thing.

⚠️ **The flash boundary**, for the reason the thirteen-entry run gave.

### 🆕 The census re-run at seventeen entries — the script needed the closed lists handed to it, as the fifteen-entry run said, and no sixth instance

🔴 **The fifteen-entry run pre-registered the next run's method and it is followed rather than
assumed**: *"a sixteenth-entry run must hand it those files too."* 量 2026-09-30 with the unchanged
thirteen-entry script (`$FWRE_WORK/rebuild/s111/land/gate/census.py`, read only; sha256
`1e81ac1a…`), three arms, exit codes read inside one script file
(`$FWRE_WORK/rebuild/s118/gr7/census17.sh`):

* **on `PROGRESS.md` alone** it now finds **nothing at all** and refuses, rc 1, with all eight
  control gates reading 0 — worse than at fifteen entries, because `R1y`'s list has since moved out
  as well;
* **on a scratch root whose `PROGRESS.md` is the real file followed by every
  `docs/history/steps-*.md`** it reproduces the twelve-entry figures — **44 clauses across 8 gates** —
  and exits 0;
* **on the same root with one of `P1`'s `D` rows un-bolded** it exits 1 and names `P1: (3, 4)`, so
  the control can still fire.

The `D`-row form is **66 clauses across eleven gates** — `R3` 5, `P4b-gate` 4, `R4` 4, `R5` 4,
`R1-pub` 13, `R1z` 4, `P1` 4, `R6` 6, `P2` 8, `R6b` 8, `R1y` 6 — with the four gates before the form
carrying 13 more, carried rather than re-derived because those step lists are records. **79
clauses**, and **unchanged at both new entries**: 量
`grep -c '^### The DoD, split into what can be refuted' PROGRESS.md` returns **0**, so neither `R7`'s
nor `R8a`'s step list uses the form and the population does not grow. ⚠️ The script's closing line
still says *thirteen-entry*; what is read here is its per-gate lines.

**No sixth instance**, because the population cannot contain one: both new gates read a per-step DoD
column instead of `D` rows. Two candidates recorded so an eighteenth entry does not find either and
call it a sixth:

* 🔴 **`R7`'s § Gate board row is the artefact-for-property shape at its strongest, and it is
  outside this census's population.** The row names two **instruments** — a `PT_DYNAMIC`/`DT_SYMTAB`
  walk and `nm --undefined-only` — where the property is *no `system`/`popen` in the shipped bytes*,
  and both are vacuous on the object under test. It is not counted: the population is `D` rows in
  `PROGRESS.md`, and this is a gate-board cell. It is recorded because **if that population is ever
  widened to gate-board rows, this is the first thing the widening will find** — and because it is the
  first instance of the class that was caught *before* the gate closed on it rather than after,
  which none of the five was.
* **`R7-1`'s `busybox --list` 量 under qemu.** The row names a verb; the enumeration that ran is the
  applet-name table read out of the ELF by `tools/appletcensus.py`, cross-read against the binary's
  own *Currently defined functions* block. Not counted in the weaker class either: the named verb was
  not *capable and idle* — `--list` is absent from this build — so the row named a verb that does not
  exist, which is `R3`'s `MemTotal:` shape and not entry 11's, and it sits outside the `D`-row
  population anyway.

⚠️ **The weaker class stays at two**, and `R6b`'s `D2` *on a fixed image*, the candidate the
fourteen-entry run recorded, stays uncounted.

### 🆕 At eighteen entries the clause FIRES on the same thing as at seventeen — the first time one thing fires on two consecutive pairs, and what it adds is a constraint, not an instruction

**`R7` → `R8` fires, and it names persistence again: that nothing rlxfw writes survives, because
there is no write path and `R8b` owns the half that would give it one.**

* `R7`: *"That the config store survives anything"* — `/var/lib/cfg.bin` is on a filesystem the
  image calls tmpfs, and *"`R8` supplies the MTD backing"*.
* `R8`: *"That anything can be written to flash and read back after a reset"* and *"That an update
  survives a power cut"*, both moved to `R8b`'s row.

🔴 **Three consecutive entries now carry it — `R8a`, `R7`, `R8` — and the clause's instruction
cannot be followed as written.** *That thing is the next gate* points at `R8b`, and `R8b` is booked
behind `R9` because slot A's first write ends the vendor firmware that `R9`'s vendor column boots
(`FW-167`; entry 16 § `R8b`). The clause names a thing and not a gate — `CPU-45` is the precedent —
so what this firing says is that the gate which moves persistence is the one that unblocks it,
`R9`. Which gate opens next stays the owner's, as every firing's destination has been.

⚠️ **The honest deduction is larger than at seventeen entries, and it is why this firing adds no
evidence of its own.** `R8`'s list holds persistence because the decision that closed `R8` moved it
there, and a gate closed by splitting off a clause will always carry that clause: the firing was
predictable from the split before the entry was written. It is counted all the same, because
`R8`'s row carried *10 power-cuts survived* until 2026-10-04 — a thing the gate set out to establish
and did not — and `R7`'s residual names `R8` in writing (`notes/config-store.md` § 11), which is
what the guard written at eight entries asks for.

⚠️ **What the pair does not name.** `FW-172`'s cache argument is in `R8`'s list and not in `R7`'s.
The limits of the CI evidence are about this repository's checks, not about a thing either gate set
out to establish. The flash boundary is not counted, for the reason the thirteen-entry run gave.

### 🆕 The census re-run at eighteen entries — unchanged, because `R8` brings no step list

量 2026-10-04 with the unchanged thirteen-entry script (`$FWRE_WORK/rebuild/s111/land/gate/census.py`,
read only; sha256 `1e81ac1a…`), the seventeen-entry run's three arms pointed at this entry's tree
(`$FWRE_WORK/rebuild/s119/p2b-work/census18.sh`), exit codes read inside one script file:

* **on `PROGRESS.md` alone** it refuses, rc 1, with all eight control gates reading 0, as at
  seventeen entries;
* **on a scratch root whose `PROGRESS.md` is the real file followed by all seventeen
  `docs/history/steps-*.md`** it reproduces **44 clauses across 8 gates** and exits 0, and the
  `D`-row form reads **66 clauses across eleven gates** with every per-gate figure of the
  seventeen-entry run unchanged;
* **on the same root with one of `P1`'s `D` rows un-bolded** it exits 1 and names `P1: (3, 4)`.

**79 clauses, unchanged.** `R8` closed with no step list of its own — `R8a`'s moved to
`docs/history/` at its close and does not use the form — and `PROGRESS.md` holds no step list at
all. **No sixth instance**, by construction. ⚠️ The two candidates recorded at seventeen entries
stay uncounted, and `R8`'s rewritten board row names three properties and no instrument, so it adds
no third.

### 🆕 At twenty entries the clause does not fire — the gate the last three firings named has closed what they named

**`R9` → `R8b` does not fire.** The subject that fired on `R8a` → `R7`, `R7` → `R8` and `R8` → `R9`
— *nothing rlxfw writes survives, because there is no write path, and `R8b` owns the half that would
give it one* — is closed by `R8b`, not carried: an update written to slot A booted through
`rlxboot` (`T2ra`), and ten pulls inside slot writes each booted the other slot. This file's own
rule governs — *a residual that a later gate closes is removed from the clause's input by being
closed, not by being edited out* — so the firing stops because its subject was established.
⚠️ **Closed for an image written by a provisioning boot, and for nothing the running firmware
writes.** The mainline image in the slots still has no write path, so `R7`'s *"the config store
survives anything"* — on ramfs, waiting for an MTD backing — is no nearer, and `R8b`'s own first
🔴, *that rlxfw can update itself*, is the same wall seen from the other side. Neither is in `R9`'s
list, so this pair cannot fire on it; the pair after `R8b` can.

🟢 **And `R8b` closed a second `R9` residual without setting out to.** `R9` said a sensitivity
control for the flash bracket needs a known change, which is a write. The `cs6c` re-install was one:
`rlxboot` and its rescue copy went from `cr6c` to `cs6c`, one byte each, and the 4 KiB map moved on
`0x010000` with the other 31 units of group 0 equal, and on `0x020000` with the other fifteen
units of the rescue region equal (the barrier's units in group 1 also moved, erased by `W4b`
between the two maps). ⚠️ That shows a one-byte change *inside a rewritten 64 KiB region* is seen;
a write the driver did not make — `FLS-26`'s class — is the case `R9` worried about, and the map's
sensitivity to it is the same digest, not a new measurement.

⚠️ **What the pair does not name.** Both entries record a 推 retracted inside its own gate —
`FW-198` in `R9`, *the rootfs at `0x130000`* in `R8b` — which is a habit of the record, not a thing
either gate set out to establish. `R8b`'s residuals that are new — an update path in mainline, the
`v1.0` image from flash, cuts outside the pace, rollback from flash — have no predecessor in `R9`'s
list, so they wait for the next pair.

### 🆕 The census re-run at twenty entries — unchanged, and it covers the nineteen-entry close, which ran none

量 2026-10-08 with the unchanged thirteen-entry script (`$FWRE_WORK/rebuild/s111/land/gate/census.py`,
read only; sha256 `1e81ac1a…`), the eighteen-entry run's three arms pointed at this entry's tree
(`$FWRE_WORK/rebuild/s126/census20.sh`), exit codes read inside one script file:

* **on `PROGRESS.md` alone** it refuses, rc 1, with all eight control gates reading 0, as at
  eighteen entries;
* **on a scratch root whose `PROGRESS.md` is the real file followed by all nineteen
  `docs/history/steps-*.md`**, `R9`'s and `R8b`'s among them, it reproduces **44 clauses across 8
  gates** and exits 0, and the `D`-row form reads **66 clauses across eleven gates** with every
  per-gate figure of the eighteen-entry run unchanged;
* **on the same root with one of `P1`'s `D` rows un-bolded** it exits 1 and names `P1: (3, 4)`.

**79 clauses, unchanged**: neither `R9`'s list nor `R8b`'s carries a `### The DoD, split into what
can be refuted` header (量, `grep -c`), so the population cannot grow. **No sixth instance**, by
construction.

### 🆕 At twenty-one entries the clause does not fire — on the weaker of its reasons, and on the strongest shape it has declined

**`R8b` → `P3` shares one counted item, and the earlier entry names the later gate.** `R8b`'s *what
it did not establish* carries *"no voltage was read, so `P3`'s power tree stays undelivered"*, and
its ruling 2 says the same. `P3`'s carries the plan's section 2 — *電源樹（實測，含 `S0b`）* —
written 讀 and 推. That is the shape of `P1` → `R6` and `P2` → `R6b`, whose runs wrote that nothing
had to be read into either entry, and of `R7` → `R8`; all three fired. `R9` → `R8b` had it too and
was declined, because the later gate had closed the thing.

🔴 **It does not fire, because the thing was decided three times and the clause surfaces what nobody
decided.** `S0b` is ⊘ on `PROGRESS.md`'s `S0` row. `BRD-01`, the regulator whose output pin would
anchor the tree, is ⊘ in `SPEC.md` § 17 since 2026-09-30, its reopen condition naming `P3`'s
power-tree section or a powered seating's side measurement with the owner's word. And entry 20's
ruling 2 kept voltage out of `R8b`'s seating, under a delegation the owner gave on 2026-10-05. The
fourteen-entry run declined `1472|mdev` on this reason and called it weaker than the others,
because the decision there was the main session's; ruling 2 is too. **If the owner reopens
`BRD-01` — an override of ruling 2 would be the owner's word its reopen condition asks for — this
pair fires on the power tree, `S0b` aside** — and its instruction could not be followed as
written, because the gate it names has closed: the thing would need a gate of its own, or the
powered seating's side measurement that `BRD-01`'s own reopen condition already names.

⚠️ **Most of `R8b`'s other residuals are in the report, and not as `P3`'s.** `docs/bringup.md` § 16.7
quotes them — every write a provisioning write, so no update path in mainline, which the
twenty-entry run said the pair after `R8b` could fire on; a rollback refused from flash never seen;
ten cuts all in paced writes; a rescue from an erased `rlxboot` only; the `C-4` extension not run;
the last bracket and the expected image; `cs6c` in one flash state; the erase size by arithmetic.
The `v1.0` image from flash, which the twenty-entry run also sent to this pair, booted from slot B
at `v1.0`'s qualification seating (`FW-255`), so it is not carried; and one of `R8b`'s items — the
instruments the tree does not hold — is in neither the report nor `P3`'s list. `P3`'s row took
`R8b`'s readings on in writing to report them, which is not what `R4` → `R5`'s firing needed of the
later gate: there `R5-0` ② made the residual its own question. A report that quotes a limit has not
set out to establish its opposite, and the guard written at eight entries decides the rest — *a
gate does not inherit its predecessor's residuals by default*. 🔴 This is the first entry whose
definition of done was to quote its predecessor, so the reason is used here for the first time; if
the owner reads quoting as taking on, the pair fires on each of `R8b`'s residuals that § 16.7
quotes.

⚠️ **One unit is in both lists and is not counted** — `R8b`'s *"One unit, one part (`1C7016`), one
loader build, one evening"* and the report's § 0 ② and § 16.5. No gate can set out to establish a
second unit, because the project has one device and no spare by its premise. Counted by the letter
it has been shared once before, at `R5` → `R1-pub + R2c` (*"One board, one unit, one operator, and
six seatings"*; *"One die, one revision, one operator"*), and the nine-entry run passed over it;
counted as what it is — true of every entry, written down or not — it would fire on every pair,
which the eight-entry run said would end its meaning. **The flash boundary** is in both and is not
counted, for the reason the thirteen-entry run gave.

**What `P3` carries that `R8b` does not** — `LA-1`, the WAN-side host probe, the network on an
autoboot, the open values the report names — waits for the next pair.

🔴 **And one of those is a thing the clause could not have seen, which a measurement found
instead.** Entry 14's weakest-thing paragraph carried it — `R6b`'s switch state, *"none was read on
a boot for which the loader did not bring its network up — the way a product boots, from flash, and
the path `R9`'s zero-write rule keeps out of reach"* — and 量 by `grep` over their text, none of
entries 15–20 carries it. `R8b` made the path reachable and read no network on it; a ping after a
flash boot at `v1.0`'s qualification seating found it (`NET-171`), and the owner opened `R6c` on
it. A residual whose premise lapsed — *"the path `R9`'s zero-write rule keeps out of reach"* — went
quiet for six entries, and the clause compares neighbours only. Recorded and not made into a rule,
for the reason given at seven entries.

### 🆕 The census re-run at twenty-one entries — unchanged, because `P3` brings no step list

量 2026-10-08 with the unchanged thirteen-entry script (`$FWRE_WORK/rebuild/s111/land/gate/census.py`,
read only; sha256 `1e81ac1a…`), the twenty-entry run's three arms pointed at this entry's tree
(`$FWRE_WORK/rebuild/s128/p3/census21.sh`), exit codes read inside one script file:

* **on `PROGRESS.md` alone** it refuses, rc 1, with all eight control gates reading 0, as at twenty
  entries;
* **on a scratch root whose `PROGRESS.md` is the real file followed by all nineteen
  `docs/history/steps-*.md`** it reproduces **44 clauses across 8 gates** and exits 0, and the
  `D`-row form reads **66 clauses across eleven gates** with every per-gate figure of the
  twenty-entry run unchanged;
* **on the same root with one of `P1`'s `D` rows un-bolded** it exits 1 and names `P1: (3, 4)`.

**79 clauses, unchanged.** `P3` had no step list of its own, so it brings none to
`docs/history/`, and `R6c`'s list in `PROGRESS.md` does not use the form (量, `grep -c`): the
population cannot grow, and **no sixth instance**, by construction. ⚠️ `P3`'s board row is a
gate-board cell and outside the population, and its *grows every gate* is read above as not met as
worded. It is not recorded beside `R7`'s candidate of seventeen entries — it describes how the
report was to be written, not an artefact named in place of a property — so it stands where the
eighteen-entry run left `R8`'s rewritten row.

### 🆕 At twenty-two entries the clause does not fire — the gate the earlier entry named closed what it named, and the nearest candidate was ruled on before any code

**`P3` → `R6c` shares one counted item, and the earlier entry names the later gate as its fix.**
`P3`'s *what it did not establish* carries *"A network on the boot the device makes by itself.
§ 14.6 ② records the trap and no workaround; the fix is `R6c`'s. So § 12's boot flow, followed
from flash, ends at a shell whose `rlx0` receives nothing."* — one of the four items the
twenty-one-entry run left to this pair. 量 `R6c` booted `9bb2bec7` from slot A through `rlxboot`
after a watchdog reset and after a cold power-on, and it pinged both ways, 4 of 4 each way, with
`rlx0`'s RX going 0 → 6 → 10 on each boot (`bench/2026-10-08c`, `NET-173`): the shell at the end
of § 12's flash boot now receives. This file's own rule governs — *a residual that a later gate
closes is removed from the clause's input by being closed, not by being edited out* — and the
pair has the shape of `R9` → `R8b`, declined for that reason, while `P1` → `R6`, `P2` → `R6b` and
`R7` → `R8`, where the later gate carried the thing instead, fired. ⚠️ **Closed for what `P3`
said, and no more**: `P3`'s sentence was categorical, and one boot of each kind refutes it; that
more boots, load or a second port behave the same is `R6c`'s own residual, with no predecessor in
`P3`'s list.

🔴 **The nearest candidate is the minimum configuration, and it is declined because it was
decided — by the owner, before any code.** `P3` carries *"One unit (§ 0 ②, § 16.5) and no minimum
configuration (§ 16.4): what the report holds is what one board returned while it worked"*, and
§ 16.4 says that no row of the report says which register write is necessary. `R6c` carries which
of its seventeen stores is necessary (its first 🔴). That is one thing at two scopes, since the
group `R6c` writes is now one of the report's writes. But `notes/switch-driver.md` § 16.8 wrote at
`R6b`'s 8d that the VLAN group is *"either left loader-inherited as a unit or taken over as a
unit, never partially"*, and the owner's ruling O1 of 2026-10-08 made `R6c`'s take-over that
unit — *"the group is determined as a unit or not touched"* — before `R6c-3` began. The
fourteen-entry run's reason applies: *the clause surfaces what nobody decided, and a ⊘ is a
decision.* It is stronger here than at fourteen and twenty-one entries, where the decision was the
main session's; this one is the owner's. 🔴 **The honest deduction**: § 16.4 names the one way
this project has measured necessity, a single-variable A/B (`NET-52`, the switch's `TRXRDY`), and
`R6c` added seventeen stores with no such A/B, while E1, the main session's, also declined the
design's on/off control on one boot. **If the owner reads O1 as a rule for what the driver writes
rather than a decision about what to measure, this pair fires on the VLAN group's minimum write
set** — a thing, not a gate, the precedent `CPU-45` set at five entries.

⚠️ **A second port against the WAN-side host probe is declined as two objects.** `P3` carries
*"The WAN-side host probe … no boot has brought a WAN interface up. It moves to a standing
instruction (ruling 4)"*; `R6c` carries that only port 3 was counted while its layout makes ports
0–5 one VLAN, port 0, the vendor firmware's WAN, among them. One is the address a service binds,
the other the jacks that reach `rlx0`. They meet in one place the clause does not score: 推 under
that layout a peer on port 0 is a LAN peer, which bears on `docs/threat-model.md`'s `T3` and is
neither entry's subject.

⚠️ **The nearest resemblance is an instrument that shares its sources with what it checks**:
`P3`'s *"That anything in the report is a second source"*, and `R6c`'s harness, whose engine
follows the vendor readings the driver follows. Two instruments, two subjects; the ten-entry run's
rule governs: *a clause that fires on a resemblance measures the reader, not the ledger.*

⚠️ **One unit and the flash boundary** are in both lists and are not counted, for the
twenty-one- and thirteen-entry runs' reasons.

**What `R6c` carries that `P3` does not** — which rule discarded the frames, the `FFCR` trap's
deciding experiment, the engine's `TCR` count and its `STOP_TLU` window, `MACCR` and `QNUMCR`, a
second `vlan` on the silicon, a fallback slot whose image is deaf from flash, one boot of each
kind — waits for the next pair.

🟢 **And the residual the twenty-one-entry run recorded as one the clause could not see is
closed, in part, by this gate.** Entry 14's weakest thing — *"`D8` passes on switch state rlxfw
did not write … none was read on a boot for which the loader did not bring its network up — the
way a product boots, from flash"* — is answered for the VLAN group: the boots the loader did not
configure were read (`NET-171`, `NET-172`), and on them rlxfw now writes the group itself (`W03`,
`C03`), while on the prompt path it verifies the loader's and rewrites what differs (`R03`). It
stays open for the rest of entry 14's list, EEE and `QNUMCR`, and for what O1 leaves untouched
besides — `MACCR`, `MEMCR`, the PHY patch, `LEDCREG` — and for entry 14's last sentence, which
`R6c` repeats: one image, one cold and one warm boot, one host on port 3. Neither entry 14's
weakest thing nor its closing is in `P3`'s list, so the clause could not have credited this
either.

### 🆕 The census re-run at twenty-two entries — unchanged, because `R6c`'s list does not use the form

量 2026-10-08, in the 130th segment, with the unchanged thirteen-entry script
(`$FWRE_WORK/rebuild/s111/land/gate/census.py`, read only; sha256 `1e81ac1a…`), the twenty-one-entry
run's three arms pointed at this entry's closing tree — its `PROGRESS.md`, with `R6c`'s list moved
out, and all twenty `docs/history/steps-*.md`, `steps-R6c.md` among them, copied from the working
tree before the commit (`$FWRE_WORK/rebuild/s130/r6c5/census22w.sh`) — exit codes read inside one
script file. A reconstruction of the same tree from `28a490c7` (`census22.sh`, whose `build22.py`
refuses unless the moved section, its two declared lines put back, reassembles `28a490c7`'s
`PROGRESS.md` byte for byte) printed the same output:

* **on `PROGRESS.md` alone**, which now holds no step list at all, it refuses, rc 1, with all
  eight control gates reading 0, as at twenty-one entries;
* **on a scratch root whose `PROGRESS.md` is that file followed by all twenty
  `docs/history/steps-*.md`** it reproduces **44 clauses across 8 gates** and exits 0, and the
  `D`-row form reads **66 clauses across eleven gates** with every per-gate figure of the
  twenty-one-entry run unchanged;
* **on the same root with one of `P1`'s `D` rows un-bolded** it exits 1 and names `P1: (3, 4)`.

**79 clauses, unchanged**: `steps-R6c.md` carries no `### The DoD, split into what can be refuted`
header (量, `grep -c`: 0), so the population cannot grow, and **no sixth instance**, by
construction.

One candidate is recorded so a twenty-third entry does not find it and call it a sixth:
`R6c-4`'s DoD, *"each boot judged by `bootslot`"*, names an instrument that cannot judge one of the
step's three boots. `bootslot` reads `rlxboot`'s lines, and the RAM boot through the prompt
prints none (entry 20: on `T2a`, which never reached `rlxboot`, it read REFUSED), so `looprun`'s
`A3` identified that boot. It is not counted: it is a step's DoD cell, outside the `D`-row
population, and the property it stands for — that each boot ran the image under test — was
measured on all three. Were it inside, it would be `R3`'s `MemTotal:` shape, an artefact that
cannot deliver the property for one of its objects, and not entry 11's *capable and idle*.
⚠️ **The weaker class stays at two.**

### Carried unchanged from the seven-entry run

⚠️ **Both caveats from the first run still travel with `CPU-45`'s firing**, and
one of them is now weaker in a way worth stating: four of the first five entries
were written in one sitting with hindsight, and `P4b-gate`'s — written a day
late, but before any gate closed after it — is the sixth. `R4`'s was written on
the day `R4` closed, from readings taken that morning; `R5`'s was written on the
day `R5` closed, and its § ① is a sweep taken that day over captures committed
between 2026-09-06 and 2026-09-10.

🟢 **One thing the seven-entry run settled and this one does not undo**: `P4a`'s
residual *`ID0` has never been read off the board* is closed by `R4`'s seating,
so it cannot repeat forward. A residual that a later gate closes is removed from
the clause's input by being closed, not by being edited out.

---

## What this file does not do

It does not say where the work is now — `PROGRESS.md` owns that. It does not say
what a released version contains — `CHANGELOG.md` owns that. It does not hold
the standing list of what the project has not established at the current
release — `docs/KNOWN-ISSUES.md` owns that, per release, where this file is per
gate and append-only.
