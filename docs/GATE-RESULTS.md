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

## The operating clause, re-run at twelve entries

**Rule:** two consecutive entries whose *what it did not establish* is the same
thing make that thing the next gate.

*(Run for the first time at five entries on 2026-09-01. Re-run 2026-09-02 with
`P4b-gate` inserted in close order and `R4` appended, which changes the pair set
rather than adding to it: the old `P4a` → *(end)* boundary is now two more
pairs, and `P4a`'s neighbour on the right changed. Re-run 2026-09-11 with `R5`
appended, which adds exactly one pair. Re-run 2026-09-16 with `R1-pub + R2c`
appended, which adds exactly one pair — and that pair fires. Re-run 2026-09-16 with `R1z` appended, which adds exactly one pair, and that pair does NOT fire. Re-run 2026-09-17 with `P1` appended, which adds exactly one pair, and that pair does not fire either — for a reason no previous non-firing has used, because the one item the two entries share was CLOSED rather than carried. Re-run 2026-09-22 with `R6` appended, which adds exactly one pair — **and that pair fires**.)*

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
