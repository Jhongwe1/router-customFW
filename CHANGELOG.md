# Changelog

**Nothing has been built.** There is no kernel of mine, no image, and no byte of
mine has been written to this device's flash. What exists is the instruments, the
record, and the first thing that ran on the silicon — the vendor's own kernel,
delivered over the network.

Tags mark where the outside world can check the work, not where a feature landed.
`PROGRESS.md` is the only file that says where the work actually is.

---

## Unreleased

**`R2a/b/d-1`, 2026-08-27 — the floor moved, and reading the matrix refuted a
sentence this gate had been carrying since it opened.** Desk only, no power,
zero flash bytes. `notes/which-drop.md` owns all of it.

- 🔴 **`@floor` is now `boa unit-2018` against `busybox unit-2018` = 0.1581 —
  the `CROSS` cell itself**, in a five-field cross-program form the manifest
  grew for it. The route there matters more than the number. The step's first
  answer was `busybox unit-2018 v3.4.0` = 0.1646, on the argument that `boa`
  crosses a source rewrite on that step (讀: −16.5 % of its bytes,
  `+libcjson`, `+libmtdapi`, strings 0.6629) while `busybox` does not. **The
  adversarial review killed it on the denominator.** Containment divides by the
  smaller feature set; busybox's is 42,297 grams against boa's 28,887, a factor
  of 1.46, so the two numbers were read at different denominators. 讀 at a
  matched one, the ordering reverses: a pair sharing its whole upstream source
  across the model change scores **0.1212**, *below* the **0.1551–0.1581** a
  pair sharing no source reaches. At this scale the corpus holds no cell above
  the no-shared-source level and below `BASE`, so the tightest correct floor
  **is** that level.
- **`E7` and `E8` are what make it a reading rather than a choice.** `E7`: the
  named cell must be the highest of every program in the reference's tree at
  least as large as the reference — 0.1581 against `pppd` 0.1578 and `wscd`
  0.1551. Smaller programs are excluded, and 讀 says why: inside `unit-2018`,
  **422 of 630 cross-program cells sit above 0.1646**, topped by
  `sysconf`/`timelycheck` at 0.9967 — two vendor tools that share their source.
  "Two different programs" is not "two programs that share no source". `E8`
  measures what a model change alone costs, which turns the rule's precondition
  into a reading: **a comparison across a compilation-model change is VOID, not
  a fail.**
- 🔴 **`--corpus` exits 0, so the `REFUTED` branch stopped firing** — and a
  verdict that has stopped firing is not one that has been satisfied, it is one
  nobody is watching. The verdict became a function; `D5` drives it in both
  directions, at the boundary, **and with its second argument moved** — a
  reviewer built a mutant that ignored that argument and passed all 24 controls
  and all 74 runner cases, and it is `M12` now. `M11` inverts it, and the suite
  builds a second synthetic corpus on the refuted side. `binsim` 23 → 24
  synthetic controls and 9 → 11 that need the trees, `test-binsim` 71 → 96
  cases, census 306 → 320 not run in CI.
- 🔴 **Product line is crossed with the clustering, not confounded with it**, and
  the corpus refutes the claim on its own. The similarity partition separates
  perfectly — lowest within-cluster cell **0.9740**, highest between-cluster
  cell **0.8951**, no overlap over all fifteen — and 讀 `/etc/version` shows
  product does not line up with it: N150RT appears in all three clusters, two
  *different products* inside one cluster score 0.9863 and 0.9818, and two
  builds of *one product* across clusters score 0.8860 and 0.0650. The high one
  is quoted too: 0.8860 is the best case product line has anywhere here, and it
  is still below every within-cluster cell. The vendor's version number is
  refuted the same way — this unit and `n300rt-2.1.6` are both stamped V2.1.6
  and land in different clusters — their cell is 0.8951, the highest
  between-cluster cell there is and still below the lowest within-cluster one.
  What is still collinear is date and SDK generation,
  which is a tautology.
- 🔴 **`busybox` is a toolchain tracer, and on one edge it separates the two
  halves this metric is supposed to be unable to separate.** One upstream source
  across all six trees, so its cells move only when the toolchain does: across
  the 2016→2018 edge `busybox` is 0.9995–1.0000 while `boa` drops to
  0.877–0.895, so **that step is `boa`'s source and not the toolchain**. The
  sharpest cell is the deliberately different one — `n200re-3.2.0`'s `busybox`
  has 1,869 fewer code words than this unit's and all 40,915 of its 7-grams are
  a strict subset of this unit's 42,297. A third instrument,
  `G(boa_t) ∩ G(busybox_t)` compared between trees, gives the same 4+2 with a
  ninefold gap **without putting two builds of one program side by side**.
- **This unit's nearest neighbour is `n200re-3.2.0` at 0.9818**, second 0.8951,
  a gap of 8.67 pp — 108× the estimated reproducibility error — and the ranking
  holds at every `k` from 2 to 16.
- 🔴 **`TC-02` stays 推, and that is the answer rather than a deferral.** The
  corpus is six *shipped images*; a GPL drop is a source and toolchain release,
  and no similarity between images can name one. The gate's own refutation
  condition did not fire (span 92.8 pp against a 5 pp bar) and the answer is
  still undetermined, which means that condition was never the binding one. The
  binding one is now written down. `SPEC.md` `TC-02a`, `TC-11`, `TC-12`.

**`R2a/b/d-0`, 2026-08-27 — the ruler, and the corpus refuting the plan's own
floor.** `R2b` needs a similarity metric whose thresholds come out of the data.
`tools/binsim.py` is that metric, with **32 controls that run before any number
is reported**. Desk only, no power, zero flash bytes.

- **`binsim(A,B)` is the containment of code 7-grams** over `[DT_INIT, DT_FINI)`,
  with Jaccard printed beside it and never instead of it. The window is not
  `.text` because **four of the six `boa` have no section header table** and
  `objdump -d` emits nothing for them; the two that kept theirs are the
  window's positive control, and the other eight files are covered by a decoding
  invariant — every `j`/`jal` in the window must target the executable segment.
  Measured 1.000 inside, 0.000–0.043 in the 4 KiB after, and 0.000–0.098 over
  the same bytes read two bytes misaligned, which is the negative control on
  that control.
- 🔴 **`k` is 7 and not 4, and the rule that picked it was written first.** A
  word-permutation of `unit-2018/bin/boa` — the identical instruction multiset
  in a destroyed order — still scores **0.4398** at k=4. The token alphabet is
  52 and 96,490 windows yield only 7,333 distinct 4-grams, so 4-grams are mostly
  shared compiler idioms. `E6`/`E6b` re-derive the choice on every corpus run
  rather than trusting the constant.
- 🔴 **The corpus refuted `plan/router-rebuild-plan.md:1128`.** `BASE` 0.9818,
  `FLOOR` 0.0650, and `binsim(unit-2018/boa, unit-2018/busybox)` — same tree,
  same toolchain, **different program** — **0.1581**. `FLOOR` sits *below* the
  cross-program floor, so the plan's warn band swallows the whole no-evidence
  region. Mechanism named: `boa` loses `pic` in 2019 (`TC-04`), and dropping PIC
  rewrites every prologue and every call. The tool prints `REFUTED` and exits 1
  rather than substituting a better number.
- **Three anchors came free with the material.** `bin/acltd` is **one sha256 in
  all six trees** — the identity anchor *and* the positive control on the void
  verdict, whose fifteen cells span exactly zero. The eight-byte busybox pair
  has **byte-identical code windows**, so the code channel says 1.0000 and the
  strings channel says 0.9972 — two channels that never disagreed would be one
  channel counted twice. And the container format partitions the six **2+2+2**
  with no similarity metric at all, which is the same partition
  `notes/lwl-mystery.md` gets from unaligned instruction counts.
- **The matrix discriminates**: `boa` spans 92.8 pp, `busybox` 83.5 pp, against
  the plan's 5 pp void threshold. Noise floor **0.0000** — all sixteen pairs
  with byte-identical code windows score exactly 1.000 on both measures.
  **Reading the matrix is `R2a/b/d-1`**, and date, product line and SDK
  generation are collinear in this corpus.
  🔄 **Two of those three sentences were refuted the same day and are left here
  as written.** The noise floor is not 0.0000 — those sixteen pairs are selected
  *by* byte-equality of the window that is then scored, so 1.000 is arithmetic;
  the estimate is **8.0e-4, 推**, and the adversarial review at the foot of this
  entry is what caught it. And **product line is not collinear** with the
  clustering, which `R2a/b/d-1` measured out of `/etc/version`. See the
  `R2a/b/d-1` entry above.
- 🔴 **And it caught a latent defect in the census.** `ci-census.py`'s case
  regexes were anchored `^\s*`, so a tool a suite *invokes* had its control
  lines counted as the outer suite's cases — with the cross compiler present
  that read `test-rlxprobe` as 116/107 against 202 and reported cases as
  missing, which was false. It never fired in CI, so the 101/101 configuration
  `ci-expected.tsv` documents was a number the census could not reproduce.
  Anchored at exactly two spaces; `ci-census` 12 → 14 controls.

**`R1h-1`, 2026-08-26 to 2026-08-27 — `probe3` is built and runs, and finishing
it corrected the tool that gates it.** The desk half of `R1h` closes here; the
bench half is spent at the tail of `R3`, in the same seating, with `probe3`
first. Desk only, no power, zero flash bytes.

- **`cells.S` and `probe3.c` are new**, through the `hazlint` gate at **804
  loads, 0 violations**, running from banner to `rlxprobe: end` under
  `qemu-system-mips`. **The first qemu capture this repository has committed**
  is beside it — `qemu/2026-08-26/probe3.txt`, in a directory parallel to
  `bench/` rather than under it, because someone sweeping `bench/` for readings
  in six months should not have to infer from a filename which ones came from an
  emulator.
- 🔴 **The core vendor's datasheet arrived the same day and refuted four cells.**
  `c-E0`/`c-E2` would have refuted `CCTL 0x100` by an artefact of their own
  running order (§5.2: an uncached read invalidates a resident line, and `c-E`
  ends with one); cell `c-G` is new, because that same sentence is a per-line
  invalidate primitive that costs one load and no `CCTL`; `w-line`'s void
  threshold sat at `+192` where 128 bytes is a legal line for this family; and
  associativity stopped being sourceless. ⚠️ **The LX4189 is provably not this
  part** — its Table 2 lists no TLB and this die has 32 entries — so every
  citation carries that caveat.
- **The suite went 106 → 195 cases**, twelve mutations and a coverage table that
  **names the cells nothing covers, and why**: on this harness most cache
  readings are identical mutated and unmutated, and a mutation whose predicted
  effect equals the baseline cannot fail.
- 🔴 **Then the gate itself turned out to be reading an opcode under the wrong
  ISA.** `tools/hazlint` called primary opcode `0x13` `COP1X (MIPS-IV)`. On a
  MIPS-I core it is COP3 — and the note that caught it got the history wrong by
  two levels, which is the kind of error that survives by sounding specific.
  **Measured** on binutils 2.42: `mfc3` assembles at `-march=mips1` *and*
  `mips2`, is refused at `mips3`; `lwxc1` waits for `mips4`. **Read**, MIPS IV
  Instruction Set Rev 3.2 § A 8.3.4: *"Coprocessor 3 is optional and
  implementation-specific in the MIPS I and MIPS II architecture levels. It was
  removed from MIPS III and later architecture levels. Note that in MIPS IV the
  COP3 primary opcode was reused for the COP1X instruction class."*
- 🔴 **And that same sentence stopped the fix from going where it was aimed.**
  The plan was to take the MIPS-I COP3 forms off the ISA watch list. *Optional
  and implementation-specific* means ISA membership is not evidence that this
  silicon executes them — and whether it does is the open cell `m-imem`, which
  `probe3` carries eight `mfc3` to answer. **Nothing came off the list.** The
  eight are still reported; they are reported as `mfc3` at level `MIPS-I COP3`,
  each printed with its address and its decode instead of as `.word`.
- **One misreading, three consequences.** The label; `reads()` returning
  `{rs, rt}`, which is COP1X's operand model and made the COPz *function
  selector* a general register — `mtc3`'s selector is `4`, and the tool read
  that `4` as `$a0`; and `control_flow()` not knowing `bc3` is a branch, so a
  load in its delay slot had its successor resolved to the fall-through alone.
  🔴 **That third one had survived the 2026-08-24 decoder sweep precisely
  because the first one was there**: COP1X is not a branch, so there was nothing
  to look for.
- 🔴 **The gate's verdict is unchanged on everything it gates** — measured
  before and after, on `stage2.bin` (1,474 / 646 / 0) and on all four payloads.
  **One number does move, and finding it took an adversarial reader**: the
  decompressed device kernel goes 172 violations to 171, and the one that
  leaves is `0x802BC490` — a `lhu t7` followed by a data word whose `rs` field
  is 15, which the old operand model read as register `$t7`. A false positive,
  in data decoded as code, and the only place in the tree where this fix is
  observable at all. A fix that moves almost no number is a fix the suite
  almost cannot see, so the deliverable is the controls: `hazlint` 10 → **12** (`K6d`; `K9`, eleven fixture words plus
  6,656 swept for the invariant that a strict hit is always a loose hit, and
  which **runs without `stage2.bin`**; and `K6c`'s two counts pinned rather
  than merely asserted unequal), `test-hazlint.sh` 56 → **96**,
  `test-rlxprobe.sh` 195 → **202**. The `--isa` count that moves is `K6c`'s
  strict total, 236 → **261**: a COP3 `CO` word has no fields fixed at zero, so
  the old MIPS-IV funct table was rejecting 69 of the 97 where this rule
  rejects 44 — 40 CO words gained, 15 undefined-`rs` words lost, net +25.
- **Three more defects fell out of the same thread.** `tools/opcount.py` carried
  the identical bad row. A case in `test-hazlint.sh` read `[ -n "$STAGE2" ]`'s
  exit status instead of the tool's, so **it could not fail on the bench machine
  and could not pass anywhere else** — and it was the case checking the gate's
  own exit-code contract. And `cells.S` justified emitting raw words by claiming
  `-march=mips1` refuses both `mfc3` and `cache`; measured, it refuses only
  `cache`. The comment was corrected and the payload was not touched: rebuilt,
  the image is byte-identical.
- **Two files disagreed about the same measurement and the wrong one was the one
  nothing checks.** `ci-expected.tsv` said the suite fails 14 cases on a runner;
  `ci.yml` said 26; measured on HEAD, 26. Both re-measured and dated — three
  times in one afternoon, because each control the review added made the row
  stale again.
- 🔴 **The whole change was then put to five adversarial readers, each finding
  sent to a separate agent whose job was to refute it: 11 of 25 survived.** Two
  of the four substantive ones are above. The others: `notes/cache-model.md`
  claimed no word of the 97 has its low 11 bits zero, and nine do — one of them
  a well-formed `bc3f` that is `hazlint`'s own fixture, so the loader does
  contain a valid COP3 word and the separating property is a valid COP3
  *move*. And the identical mislabel was still alive one opcode along: `0x33`
  is `LWC3` on MIPS-I and was `(pref', 'MIPS-IV')` in two tools, while `reads()` treated `swc3`'s
  coprocessor register as a general one — measured, that made the shipped tool
  refuse `lw t0` / `swc3 t0,0(a0)`, a build stopped for a hazard that is not
  there. Three of the new controls were themselves too weak to catch a mutant
  and were strengthened.

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
