# `R1b` — the hazard ladder, and the build gate that had to be inverted

`R1-pub-2`. The design document for `probe5`.

**The table** is `tools/isa-hazard.tsv`; **the generator** is `tools/hazpay.py`;
**the gate** is `tools/hazdecl.py`; **the payload** is `tools/rlxprobe/probe5.c`
with `cells5.S`, `probe5rows.h`, `probe5rows.c` and `probe5rows.mk` generated
from the table. Nothing here is a second copy of those files — where this
document and the table disagree, the table is right and this document is stale.

`docs/isa-payload.md` is the same document for `R1a`/`probe4`, and the two
payloads share a harness, a register map and a refusal doctrine. What they do
not share is the question, and § 1 is about that.

---

## 0. What this does not claim

1. **A row that reads `LOCK` on the device has not shown there is no hazard.**
   It has shown that at that distance, with that operand set, on a warm cache,
   the consumer saw its producer's result. § 7 lists what that leaves open.
2. **`OPEN` is 推 on its value and 量 only on its inequality.** MIPS-I says
   reading a result too early is UNPREDICTABLE, so *the consumer sees the
   register's prior value* is a hypothesis about this implementation. A row that
   reads neither constant is `OTHER`, and `OTHER` is not a failure — see § 3.
3. **The qemu leg is not evidence about this device**, and here it is less than
   that: `F46` says qemu interlocks the load delay slot and this core does not,
   so every row reading `LOCK` under qemu is the *vacuous* answer. What the qemu
   leg is for is C4 — § 5.
4. **Nothing is compared inside the payload.** `probe5` records eight words per
   row; `hazpay verdict` decides at the desk. With two constants per row that
   matters more than it did with one.

---

## 1. Why this is not `probe4` with more rows

| | `R1a` / `probe4` | `R1b` / `probe5` |
|---|---|---|
| a row is | one encoding | a SEQUENCE: a producer, `dist` `nop`s, a consumer |
| the question | does this instruction exist, and does it compute the right answer | what does the pipeline do when a consumer follows its producer too closely |
| expected values | one constant | TWO, and they are different kinds of claim |
| verdict cells | TRAPS / RIGHT / WRONG / RAN / NOT-RUN | TRAPS / VOID / LOCK / OPEN / OTHER / NOT-RUN |
| the result-block tag | `'R4' << 16` | `'R5' << 16`, so a capture from one cannot be read as the other's |
| the build gate | `tools/hazlint`, which must exit **0** | `tools/hazdecl.py`, and `hazlint` exiting **0 is a build failure** |

The last row is the one nothing in this repository had noticed. § 4.

---

## 2. Why it is a ladder and not a list

`SPEC.md` `CPU-31`'s residual row writes the shape itself:

> 裸機上一組 `mult`→`mflo`、`mtc0`→`mfc0`，中間補 0/1/2 個 `nop`，看讀值何時開始正確。

So every family appears at several distances and the reading is **the distance at
which the value becomes correct**. A single rung answers *is there a hazard*; a
ladder answers *how deep*, and depth is what a compiler flag has to be set from.

**The rungs of one family differ by nothing but the padding.** `hazpay`'s
templates assemble a body out of four parts — setup, producer, `dist` `nop`s,
consumer, settle-and-control — so a rung cannot differ from its twin by anything
else. That is what makes a ladder a single-variable experiment rather than a set
of tests, and it is upstream's `P9-12` v1-against-v2 reproduced inside one
payload with this repository's own instrument.

**The sharpest rung in the table is `lu_alu_d1`, and its `dev` column is empty on
purpose.** Two vendor sources disagree about that distance and nobody has
measured it:

* upstream's `P9-12` v2 — the image that WORKED on this device — fixed the
  failure with **two** `nop`s and nothing else changed
  (`upstream/BENCH-LOG.md` `T-89`/`T-90`);
* rsdk 1.3.6 under `-fuse-uls` emits **one**, and `notes/vendor-kernel-isa.md`
  § 252-255 records it: `lwl $2,1($4)` / `nop` / `lwr $2,4($4)` / `nop`.

One of those two beliefs is wrong about this die.

### 2.1 The ten families, and the six census rows they came from

Eight hazard families and two controls, joined to
`docs/isa-prior-art.md` § 4's six census rows in both directions on every
`hazpay population` run. The mapping is not one-to-one and that is the point:
§ 4's single `store` row became three families once its shape was specified,
which its own text says was this step's first job.

| family | producer → consumer | the reading lands in | census row |
|---|---|---|---|
| `loaduse` | `lw $9` → `addu $2,$9,$0` | `$2` | load then a reader |
| `storedata` | `lw $9` → `sw $9,4($10)` | **mem1** | store, the class … |
| `storebase` | `lw $10` → `sw $9,0($10)` | **which address was written** | store, the class … |
| `hilo` | `mult` → `mflo $2`, LO primed | `$2` | mult/div then mfhi/mflo |
| `cp0` | `mtc0 EPC` → `mfc0 $2,EPC` | `$2` | mtc0 then mfc0 |
| `movcond` | `lw $9` → `movn $2,$8,$9` | `$2` | movz or movn … |
| `movrd` | `lw $2` → `movn $2,$8,$9` | `$2` | movz or movn … |
| `dslot` | `beq`, `lw` in the slot → the target | `$2` | a load sitting in a delay slot |
| `storeprod` | `sw` → `lw` same address | mem0 | store, the class … — **a CONTROL** |
| `hiloprime` | `mtlo` → `mflo`, no `mult` | `$2` | — **a CONTROL, no census row by design** |

`hiloprime` has no census row and `hazpay population` says so rather than
skipping it. The reason is the census's own: `docs/isa-prior-art.md` § 0
excludes what obviously works, and `docs/isa-payload.md` § 1 records that what it
excludes by that rule is exactly a payload's positive control.

---

## 3. The two constants are not the same kind of claim

This is the load-bearing difference from `probe4`, where every constant has two
independent derivations.

| | mark | what it is |
|---|---|---|
| `lock` | **讀** | ordinary ISA semantics: what the consumer computes when it sees its producer's result. `hazpay model` derives it from the operands by name, without reading the column. |
| `open` | **推** | *the consumer sees the register's prior value*. MIPS-I says the result is UNPREDICTABLE; this is a prediction about **this implementation**. |

⚠️ **The `open` halves are not two independent beliefs.** `hazpay model` derives
`open` too, but from the same hypothesis, so what is checked twice is the
arithmetic and not the hypothesis. `hazpay model` prints that sentence on every
run rather than leaving a reader to infer otherwise from the word *model*.

**The consequence is in the verdict vocabulary.** A row that reads neither
constant is `OTHER`, and `OTHER` is **not a failure** — it means *the hazard is
open and the mechanism is not the prior value*, which is a larger finding than
`OPEN` and is the whole reason the payload records the value rather than a
boolean.

### 3.1 The six verdicts, in the order they outrank each other

| | when | why it outranks the next |
|---|---|---|
| `NOT-RUN` | the row's tag is not in the block | a row that did not run cannot have a value |
| `TRAPS` | the exception count is non-zero | an exception explains every other word |
| `VOID` | `aux` is not the row's `ctl` | if the producer never produced, the consumer's reading is about nothing. **Without this a broken `mult` and an exposed `mflo` would arrive as the same verdict.** |
| `LOCK` | the value is `lock` | |
| `OPEN` | the value is `open` | |
| `OTHER` | neither | |

### 3.2 `aux` is always the control, and never a row's reading

Every family writes, after the hazard has settled, what its producer produced:
`$9` for the load-use families, HI for `hilo`, EPC for `cp0`, the settled base as
an offset for `storebase`, the memory operand again for `movrd`.

`probe5.c` zeroes `out_aux` before every cell and counts the rows where it stayed
zero (`aux.zero`), so **0 is the payload's sentinel for *the cell never reached
its control*** — and `hazpay` refuses a table row whose `ctl` is 0, so the
sentinel and a passing control can never be one word.

### 3.3 🔴 `movrd` reads differently from every other row in the table

The destination is the freshly loaded register and the condition is false. A
write-enable implementation leaves the load standing; one that read-selects and
always writes puts the **stale destination** back and destroys the load.
`notes/kernel-build.md` § 155-160 says this project has never measured which one
this die has (`TC-h`).

So for that family **`LOCK` means *write-enable*, not *interlocked***, and
`lu_alu_d0` is the row that separates them: it establishes whether the load
hazard exists at all. A reader who carries the other families' reading of `LOCK`
into this row gets the opposite conclusion.

---

## 4. 🔴 The build gate, and why it had to be inverted

`plan/router-rebuild-plan.md:1038` requires `R1b`'s load-delay-slot test to be

> `lw` 後緊接讀取同一暫存器

and `tools/hazlint`'s own docstring defines a violation as

> for every load, does an instruction that can execute next read the register
> that was loaded

— the same sentence. And `tools/rlxprobe/Makefile` makes `<payload>.bin`
unbuildable unless `hazlint` exits 0, with **no waiver flag anywhere in its
option table**, with a `gate-check` target that fails the build if the gate is
loosened *and insists on exit 1 specifically* so a refusal for the wrong reason
is caught, and with `cells.S:69 (a payload that built its victim instructions at)` foreclosing run-time construction on purpose.

**The build gate prevented exactly the experiment the plan asks for, and no
document in `plan/`, `docs/`, the Makefile or `hazlint` addressed it.**

### 4.1 The two resolutions that are wrong

1. **`--vma-range` or `--section` around the framework.** A hard-coded window is
   a filter that drops silently — the Makefile's own comment under `$(BIN)` says
   so about `--only-section` — and worse, it creates a **seam**: a load at the
   end of one window whose consumer is the first instruction of the other is
   checked by neither.
2. **A hazard body in a data section, copied into a run-time arena.** Invisible
   to the gate by construction, which is `tools/mkramboot.py`'s recorded failure
   — *a model kinder than the device certifies exactly the bugs the device will
   reject* — with the roles swapped.

### 4.2 What `hazdecl` does instead

Run the **unmodified** gate over the **whole** image and adjudicate its output.
`hazlint` is not modified, no flag restricts what it scans, `gate-check` is
untouched, and every other payload's gate is exactly what it was. What changes is
that the gate's output becomes **data for a second, two-sided check**, which is
strictly more than *zero* ever said.

**And the sign is inverted: for probe5, `hazlint` exiting 0 is a build failure.**
A hazard payload with no violations has had its hazards compiled away, which is
`PROGRESS.md:122`'s risk column in one sentence — *`-O` may insert the very `nop`
the test exists to detect; the payload has to be read as built, not as written*.
That inversion is the step's pass condition, and it is a refusal rather than a
report.

### 4.3 The twelve checks

| | |
|---|---|
| **P1** | the number of violation RECORDS parsed equals the `VIOLATIONS` count. **First, because it is the control on this tool's own parser** — and two parsers written against this same output were wrong on 2026-09-13 before this one. One matched hazlint's K2 control line (*Expected: 2 violations*) and read 2 for every case including the negative control; one anchored `VIOLATIONS` at column 0 where the line is indented two spaces. Both printed a number. It also catches `--max-report` truncation. |
| **P2** | `loads > 0`. hazlint's exit 2 covers *the scan found no loads at all*, and a tool that is not looking reports 0 loads and not 0 violations. |
| **P3** | `unresolved == 0`. An unchecked successor is an unchecked load. |
| **P4** | hazlint's exit code is **1**. 0 means the hazards are gone; 2 and 3 mean it refused, and a refusal is not a verdict. |
| **P5** | every violation is at a declared site: load == `addr(_p)` and successor == `addr(_c)` of a row whose channel is `main` or `both`. |
| **P6** | every `main`/`both` row's site appears in the violation list. **The direction a gate that only counts violations can never have.** |
| **P7** | every survey hit is at a declared `survey`/`both` row's producer, in the bucket its family declares. |
| **P8** | every `survey`/`both` row's site appears in its declared bucket. |
| **P9** | no row whose channel is `none` appears in **either** channel. This is what proves the padding is really there. |
| **P10** | the survey's shape names are the three this tool knows. A hazlint whose survey grew a fourth must be loud, not silently unmatched. |
| **P11** | the `dslot` family's record says its successor was reached as a **jump target**, and every other family's says **next word**. 量 2026-09-13 that hazlint prints both forms, so this is free and it is the only check that separates that family's shape from `loaduse`'s. |
| **P12** | `addr(_c) - addr(_p) == 4 * (dist + 1)`, read out of the artefact's symbol table by `hazpay.check_distances`. **Independent of hazlint entirely** — two instruments, two claims, no overlap. |

### 4.4 量 2026-09-13 — which channel each shape lands in

Nine fixtures, each with both controls, `-march=mips1`, big-endian, against the
real `stage2.bin` population control:

| shape | violations | rc | what hazlint said |
|---|:-:|:-:|---|
| `lw $9` ; `addu $2,$9,$0` — POSITIVE control | **1** | 1 | `reads $t1 [next word]` |
| `lw $9` ; `nop` ; `addu` — NEGATIVE control | **0** | 0 | — |
| `lw $2` ; `movn $2,$8,$9` (`rd` is loaded) | **1** | 1 | `reads $v0 [next word]` |
| `lw $9` ; `movn $2,$8,$9` (`rt` is loaded) | **1** | 1 | `reads $t1 [next word]` |
| `mult` ; `mflo $2` | **0** | **2** | refused — the fixture has no loads at all |
| `mtc0 $11,$14` ; `mfc0 $2,$14` | **0** | **2** | refused — same |
| `beq` ; `lw` in the slot ; use | **1** | 1 | `reads $t1 [jump target of 0x…]` |
| `lw $9` ; `sw $9,4($10)` — store DATA | **1** | 1 | `reads $t1 [next word]` |
| `lw $10` ; `sw $9,0($10)` — store BASE | **1** | 1 | `reads $t2 [next word]` |

Two consequences, and both changed the design:

* **`hilo` and `cp0` are invisible to hazlint's main check at every rung**,
  because their producers are not loads. They live in `--survey`, whose output is
  counts and addresses and never a verdict. So `hazdecl` reads **both** channels
  and the table declares which one each rung lives in.
* **rc 2 is a refusal, not a clean image.** Those two fixtures contain no load at
  all, and hazlint's exit 2 covers that case. `hazdecl`'s P2 asserts it rather
  than inheriting it.

### 4.5 The channel column has two sources, and the second one caught the first

`haz` is hand-written and `hazpay.derived_channel` computes it from family and
distance. A disagreement is a row whose author believed something wrong about the
shape — which is what happened, twice, and `hazdecl` caught both on its **first
real build**:

* `main` presence needs *a LOAD whose consumer is next*, so it is
  `dist == 0` **and** a load-producing family. The first draft had only the
  distance, and `hilo`/`cp0` came out wrong.
* `dslot` is counted by the survey at **every** rung. The load sits in a branch
  delay slot whatever the padding, because the padding is between the branch
  TARGET and the consumer. The first draft declared `ds_d1` as `none` on the
  reasoning that a padded rung carries no hazard site — true of the load-use
  check, false of the survey.

`hazpay`'s `H24b` pins the derivation pair by pair. A rule that was wrong twice
needs a table of answers, not a sentence.

---

## 5. C4, and the trap in it

`plan/DAY-ZERO.md:603`:

> **負控制是強制的，而且 R1b 的形式很特別**：
> **每個 hazard 測試在 qemu 下必須給出「有 interlock」的相反答案。**
> 那證明測試本身有鑑別力 —— 否則你分不出「這顆有 interlock」和「我的測試沒測到東西」。

So the `qemu` column is `lock` for every row, **the parser refuses anything
else**, and a qemu-arm row reading anything but `LOCK` is a finding that voids
that row. There is no refuted-prediction allow-list here, unlike `isapay`'s
`QEMU_REFUTED`: a refuted hazard prediction is not a curiosity about qemu's
decoder, it is loss of discriminating power for the row.

**The trap** — `docs/isa-prior-art.md` § 8: *a device run that looks like the
qemu run is the run that refutes the experiment, not the one that confirms it*,
and the qemu leg must be run and recorded **before** the device leg so the
expected difference is on paper rather than reconstructed afterwards.

### 5.1 量 2026-09-13, `qemu/2026-09-13/probe5.txt`

`qemu-system-mips 8.2.2 -M malta`, 3,035 bytes, sha256 `f913be43…8388816d`.

**24 of 24 rows read `LOCK`. Every pre-registered `qemu` prediction hit.** Every
family "closes at d0", which is exactly the vacuous answer C4 predicts — and the
point is that it is recorded first.

The harness's own controls in the same capture: `trapped=0`, `ran=24`,
`scratch.bad=0`, `addr0.bad=0`, **`aux.zero=0`** (every cell reached its
control), `break.count=1` with `break.cause=00000424` → ExcCode 9,
`install.bad=0`, `restore.mismatch=0`, and `epc.end=5a5a5a50` = `EPC_NEW`, so the
`cp0` family's CP0 write was visible from outside a cell.

### 5.2 What the qemu leg CAN settle, and one hole it found

It is the third source for the **`lock`** column: a wrong `lock` constant would
read `OTHER` there. It cannot say anything about `open`.

🔴 **And reading the capture found a hole in the table that nothing else would
have.** The `hilo` family's `open` constant is the primed LO — so if `mtlo` never
landed, that family could only ever read `LOCK` or `OTHER`, and *the prime did not
land* would be indistinguishable from *there is no hazard*. The qemu leg cannot
settle it either: `mult` overwrites both halves of the accumulator.

`hl_ctl` was added for it — prime LO and HI, read them back with **no `mult` at
all**, at a distance beyond the architectural `mflo` window so both machines must
agree. 量 on the re-run: `gpr = cafe0000` (= `PRIME_LO`) and
`aux = beef0000` (= `PRIME_HI`). **`mtlo` and `mthi` both work, so the `hilo`
family's `open` leg is falsifiable.**

No other family needed one, and that is measured rather than assumed:
`sb_m0_d0` reading `LOCK` with value `B10CB10C` **is** the cross-row control that
`$9` really holds `in_b`, which is what the `loaduse`, `storedata` and `dslot`
families' `open` legs rest on.

### 5.3 The `dev` column, and a live demonstration that it has teeth

Three rows carry a pre-registered **device** prediction and every other row's is
`-`, which is the honest majority:

| row | `dev` | source |
|---|---|---|
| `lu_alu_d0` | `open` | `CPU-14` — upstream's `P9-12` `T-89`/`T-90`, the only route-① hazard reading this project holds, **and it is not this repository's** |
| `lu_alu_d2` | `lock` | upstream's `P9-12` v2, the image that worked with two `nop`s |
| `st_p`, `hl_ctl` | `lock` | control rows |

Running `verdict --arm device` against the **qemu** capture refutes `lu_alu_d0`
and confirms the other three, which is correct — qemu has interlocks. That
cross-arm run is a positive control on the `dev` scoring and costs nothing.

---

## 6. The controls, family by family

| | what it is | what it would look like without it |
|---|---|---|
| C1 | `break` before the sweep, inherited from `probe2` | a sweep whose handler was never shown to work reports absences it cannot attribute |
| C4 | every row must read `LOCK` under qemu | *this die has interlocks* and *my test measured nothing* would be one reading |
| per row | `aux` = what the producer produced | *the hazard is open* and *the producer never produced* would be one word |
| `st_p` | store → load, same address, two constants equal by declaration | the memory observable that `storedata` and `storebase` rest on would be unproven |
| `hl_ctl` | the accumulator prime, with no `mult` | `hilo`'s `open` leg would be unfalsifiable — § 5.2 |
| `sb_m0`/`sb_m1` | the same cell read from both words | exactly one address can have been written; they disagree only if the store went nowhere |
| `lu_alu_d0` | `dev = open`, pre-registered | this repository would be quoting a reading it has never taken |
| the table | `lock != open` for a `haz` row, `lock == open` for a `ctl` row | a row that cannot distinguish would read `LOCK` whatever the die did |

**The collapse rule is one rule with opposite signs and the parser enforces
both**, which is `isapay`'s reserved-row trap in the hazard table's own terms.
Its ancestor is a recorded defect: `isapay`'s first `T_JR` template let a `jr`
that did nothing and a `jr` that jumped land on the same value, and *a template
that cannot express failure is the payload version of an answer checker that
always says yes*.

---

## 7. What could still be wrong

1. **Every row runs on a warm D-cache and a warm I-cache.** `probe5` does not
   control the cache state of its memory operand or of its own cells, so every
   reading is *interlock behaviour on a warm cache*. The primitive to force a
   miss exists and is measured (`cache11`, Hit Invalidate D, 量 2026-08-29) and
   `rlx_call2_uncached` is already linked; using them is a second seating's work.
2. **`open` is 推 and stays 推 even if it reads.** A row reading `OPEN` shows the
   consumer saw the prior value *this time, with these operands*. It does not
   establish that the prior value is what an exposed hazard always yields.
3. **`isapay verify --strict`'s converse check is SILENT on probe5**, and that is
   stated rather than left to be found: every encoding here is ordinary MIPS-I,
   so `hazlint --isa` reports zero hits and zero strays. A clean result there is
   passing by being blind. `hazdecl` is the check with teeth.
4. **The `cp0` family writes CP0 14 on the device.** EPC is the only full-width
   read-write CP0 register on this core that is inert outside an exception
   return; `Status` has reserved bits so its read-back would not be a
   self-contained constant, and writing an unidentified CP0 register is refused
   by `tools/isa-payload.tsv`'s own doctrine. A trap during a `c0_*` cell
   overwrites EPC in hardware and the handler reads the hardware value, so the
   cell's writes cannot mislead the handler. **The bench card must re-confirm
   this rather than inherit it.**
5. **`dslot` puts a load in a branch delay slot and `exc.S` adds 4 to EPC
   unconditionally**, which is wrong in a delay slot. The row is trap-free by
   construction — a `lw` from the scratch block cannot fault on a core with no
   MMU in KSEG0 — but that is an argument, and `Cause` is recorded whole so `BD`
   is visible if it ever happens anyway.
6. **`storebase`'s containment is structural, and it is worth restating because
   it is the one row that writes to an address it computed.** The two candidate
   addresses are `scratch+16` and `scratch+20`, which differ in **one bit**, so
   every bitwise mixture of the two words is still one of the two addresses and
   every outcome is inside the scratch block. `probe5.c` writes the loaded
   address into scratch word 3 from C and refuses the sweep if it does not read
   back, because a cell that STORED it there first would itself be the
   store-producer shape the table declares not measurable.
7. **The `DW` read-back parser is not written**, exactly as `isapay`'s is not.
   The `P5 ` line is the only channel qemu has and the second one on the device.
8. **`hazlint`'s survey is a count and this table trusts its ADDRESSES.** 量
   2026-09-13 that the address it prints is the producer's in all three buckets,
   with a fixture that makes each one fire alone. A hazlint that changed which
   end of the pair it printed would move every `survey` row's P7/P8 at once, and
   the only thing that would catch it is the distance check P12, which is
   independent.

---

## 8. The store shape, specified

`docs/isa-prior-art.md` § 4's sixth row says specifying it was the first thing
this step had to do, before any payload. Its wording — *store, the class hazlint
has no rule for* — is **imprecise, and 量 2026-09-13 says how**.

The class splits by the store's ROLE:

| | the store is | shape | `hazlint` rule? | measurable as a hazard? |
|---|---|---|:-:|---|
| **ST-C1** | a consumer, via `rt` (the data) | `lw $9` ; `sw $9,…` | **yes** | **yes** — `storedata` |
| **ST-C2** | a consumer, via `rs` (the base) | `lw $11` ; `sw $9,0($11)` | **yes** | **yes** — `storebase`, and the reading lands in MEMORY rather than in a register |
| **ST-P** | a producer | `sw $9,0($10)` ; `lw $2,0($10)` | **no** | **no** — and the reason is not that the test is hard |

**So what `hazlint` has no rule for is a store as a PRODUCER, on both of the two
shapes tried — and it has a rule for a store as a CONSUMER on both operand
paths.** That is the precise version of the census's sentence.

**ST-P is not measurable, and it is now measurable-as-unmeasurable with a
reason** rather than unspecified:

* MIPS-I requires a load to see a preceding store to the same address; there is
  no architectural store delay slot;
* every program on this die depends on it at population scale — `stage2.bin`'s
  1,474 loads and this unit's kernel's 128,440 — so route ② decides it;
* therefore a payload that observed a violation would be observing **a broken
  payload, not a hazard**: the test cannot fail in a way attributable to the die.

That is exactly the *測不出來* the plan legalises. What it IS is the positive
control on the memory observable that `storedata` and `storebase` rest on, so it
is in the table as `st_p` with `kind = ctl`.

⚠️ **A version of ST-P that IS measurable is named and deferred**: a store to one
address followed by a load of a *different* address in the same cache line or
write-buffer entry. That is about the write buffer, `CPU-45` is its neighbour,
and it is not `R1b`'s question.

⚠️ **The census row is NOT split.** Splitting it changes the census's population,
which `tools/isacensus.py` checks in both directions against derived instruments,
and that belongs to the census's owner rather than to this step. `hazpay
population` maps three families onto the one row and prints the mapping on every
run.

---

## 9. Reading a capture

```
hazpay.py verdict <capture> --arm qemu      # C4, and it must be all LOCK
hazpay.py verdict <capture> --arm device    # the measurement
```

The verdict table prints, per row, the verdict, the value, both constants and a
note; then the tally; then **the ladder** — for each family, every rung's verdict
and the distance at which it closes. The ladder is the result. A table of per-row
verdicts is not yet an answer to *how deep*.

`hazpay.py sites [ELF]` prints the declaration `hazdecl` checks against, with
addresses when an ELF is given.

---

## 10. Where each thing lives

| | |
|---|---|
| the population | `tools/isa-hazard.tsv` — 24 rows, 10 families |
| the generator, the models, the verdict | `tools/hazpay.py` |
| the build gate | `tools/hazdecl.py` |
| the mutant runner and `emit --check` | `tools/test-hazpay.py` |
| the payload | `tools/rlxprobe/probe5.c`, `p5support.S` |
| generated | `cells5.S`, `probe5rows.h`, `probe5rows.c`, `probe5rows.mk` |
| the qemu leg | `qemu/2026-09-13/probe5.txt` |
| the numbers | `SPEC.md` `CPU-52`, `CPU-53`, `CPU-54` |
