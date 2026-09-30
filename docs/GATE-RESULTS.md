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

## The operating clause, re-run at fifteen entries

**Rule:** two consecutive entries whose *what it did not establish* is the same
thing make that thing the next gate.

*(Run for the first time at five entries on 2026-09-01. Re-run 2026-09-02 with
`P4b-gate` inserted in close order and `R4` appended, which changes the pair set
rather than adding to it: the old `P4a` → *(end)* boundary is now two more
pairs, and `P4a`'s neighbour on the right changed. Re-run 2026-09-11 with `R5`
appended, which adds exactly one pair. Re-run 2026-09-16 with `R1-pub + R2c`
appended, which adds exactly one pair — and that pair fires. Re-run 2026-09-16 with `R1z` appended, which adds exactly one pair, and that pair does NOT fire. Re-run 2026-09-17 with `P1` appended, which adds exactly one pair, and that pair does not fire either — for a reason no previous non-firing has used, because the one item the two entries share was CLOSED rather than carried. Re-run 2026-09-22 with `R6` appended, which adds exactly one pair — **and that pair fires**. Re-run 2026-09-25 with `P2` appended, which adds exactly one pair, and that pair does not fire — the later gate had CLOSED three of the earlier one's residuals, and the nearest remaining candidate is one subject that the two entries name as two different faults. Re-run 2026-09-28 with `R6b` appended, which adds exactly one pair — **and that pair fires**, on a thing the earlier entry handed to the later gate by name; the same run decides the question the thirteen-entry run left to this entry. Re-run 2026-09-30 with `R1y` appended, which adds exactly one pair, and that pair does not fire — the later gate is about this repository's record, and it did not take on the thing the fourteen-entry run fired on.)*

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
