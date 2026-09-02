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
  delay-slot-padding side, `hazlint` 0 violations), decided for the kernel, open
  for userspace. `R7` owns it.
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

## The operating clause, re-run at seven entries

**Rule:** two consecutive entries whose *what it did not establish* is the same
thing make that thing the next gate.

*(Run for the first time at five entries on 2026-09-01. Re-run 2026-09-02 with
`P4b-gate` inserted in close order and `R4` appended, which changes the pair set
rather than adding to it: the old `P4a` → *(end)* boundary is now two more
pairs, and `P4a`'s neighbour on the right changed.)*

| pair | shared? |
|---|---|
| `R1-gate` → `R2a/b/d` | no. `R1-gate`'s residuals are the D side and the cache; `R2a/b/d`'s are drop identification and toolchain choice |
| `R2a/b/d` → `R1h` | no |
| `R1h` → `R3` | **yes — decision ② / `CPU-45`.** `R1h` carries it as 未定 after the first of two allowed seatings; `R3` carries it as still `R1-gate`'s |
| `R3` → `P4a` | no |
| `P4a` → `P4b-gate` 🆕 | no. `P4a`'s are Level-2 reproducibility, one machine, one afternoon; `P4b-gate`'s are the unowned rule, the missing tag, and the ledger's own omission |
| `P4b-gate` → `R4` 🆕 | no |

🔴 **Two new entries and no new firing.** The clause still names exactly one
thing — `CPU-45` — and it names it from the same pair it named it from at five
entries. Written down because the opposite would have been the suspicious
result: a rule that fires more often simply because the ledger got longer is
measuring length, not repetition.

🔴 **And at seven entries the clause's own reach became visible, which it was
not at five.** There *is* a residual that repeats — **a DoD that named an
artefact instead of the property it wanted** — and the clause cannot see it:

* `R3`'s `D3` named the string `MemTotal:`, which this kernel never prints.
* `P4b-gate`'s `D2` named the path `study/weekly-results.md`, which is
  gitignored by a ruling the same gate made.

Those are the same defect and they are **two apart**, with `P4a` between them.
The rule says *consecutive*, so it does not fire, and this entry does not
pretend it did. ⚠️ Whether the rule should read *within any three consecutive*
is a change to the rule, and changing a rule because it failed to produce the
answer you had already reached is exactly how such a rule stops being an
instrument. Recorded, not applied.

⚠️ **Both caveats from the first run still travel with `CPU-45`'s firing**, and
one of them is now weaker in a way worth stating: four of the first five entries
were written in one sitting with hindsight, and `P4b-gate`'s — written a day
late, but before any gate closed after it — is the sixth. `R4`'s was written on
the day `R4` closed, from readings taken that morning. ⚠️ **That is not a claim
to be the first such entry** — `P4a`'s was also written on the day `P4a`
closed. The difference is only that `P4a`'s was written in a sitting that was
simultaneously backfilling four others, which is a statement about the
*selection* of residuals and not about their dates.

🟢 **One thing this run does settle**: `P4a`'s residual *`ID0` has never been
read off the board* is closed by `R4`'s seating, so it cannot repeat forward. A
residual that a later gate closes is removed from the clause's input by being
closed, not by being edited out — `P4a`'s entry keeps its wording and `R4`'s
says which line it closes.

---

## What this file does not do

It does not say where the work is now — `PROGRESS.md` owns that. It does not say
what a released version contains — `CHANGELOG.md` owns that. It does not hold
the standing list of what the project has not established at the current
release — `docs/KNOWN-ISSUES.md` owns that, per release, where this file is per
gate and append-only.
