# An independent audit of `probe1.c` and `probe2.c`

**2026-08-25, at the desk, before either payload had run on the device.**

The 2026-08-25 morning audit checked what surrounds these two payloads — the
runsheet, the `Makefile`, the CI numbers — and found seven defects there. It did
not read the payloads themselves. This one does, and it exists because of one
asymmetry: **`qemu-system-mips` interlocks the load delay slot, implements MIPS32
CP0 semantics, and has a coherent I-cache. Its sign-off is precisely the class of
defect this core rejects** — which is how upstream's `P9-12` was certified by its
own simulator the day before it failed on this silicon.

**Nothing here was measured on the device.** Every claim is marked *讀* (out of
the source), *量* (out of the emitted binary, by disassembly), or *推*.

## What it produced, and what it did not

Six independent lenses — ISA/hazard, cache semantics, result-block arithmetic,
fault cost, qemu divergence, report-vs-runsheet arithmetic — each finding then
sent to a separate reader whose task was to **refute** it.

| | |
|---|---|
| findings produced | **47** |
| put to a refuter | **21** — 10 refuted, 11 survived |
| **never refuted by anyone** | **26**, including **all six** ISA/hazard findings and six of eleven fault-cost findings |

🔴 **The verification stage died on a session limit, and it died on the two lenses
that matter most.** The 26 unverified findings are marked **`[1-src]`** below.
This document's own rule follows the project's: *nothing counts as a result until
its refutation condition is written first*. A `[1-src]` finding is a claim, not a
finding, and it is recorded as one.

The `[1-src]` findings that would change a bench decision were re-checked by hand
against the emitted binaries. Those are marked **`量`** and carry the
disassembly. The rest stand as claims.

## Must-fix, before `probe2` runs — this is `R1g-4b`'s list

Ranked by how much fixing it reduces the chance a power cycle is wasted.

### 1. `rlx_do_break` has no `SAFE_A0`, so the designed "visible failure" is silence — 量

`probe2.c` and `RUNSHEET.md` `H2c` both promise that a handler which did not take
produces `Undefined Exception happen.` — *"an unambiguous observation, not a
silent wrong answer"*. It does not.

```
80500f40:  1480fffb   bnez  a0,80500f30      # rlx_puts' loop exit test
80500f48:  8fbf0014   lw    ra,20(sp)        # nothing after this writes $a0
...
80501328:  24441884   addiu a0,v0,6276       # the last writer of $a0 (a jal delay slot)
80501364:  0c1400b2   jal   805002c8 <rlx_do_break>

805002c8 <rlx_do_break>:
805002c8:  0000000d   break                  # no SAFE_A0
```

`rlx_puts` exits on the string's NUL, so it **always returns with `$a0 = 0`**, and
nothing between `0x80501328` and the call writes `$a0`. On the failure branch:
`break` → the loader's dispatcher → `exception_handlers[9]` → `do_reserved` at
`0x80400BE8` → `move v0,a0` (v0 = 0) → `lw a3,148(v0)`, a load from `0x00000094`,
which is kuseg, which is TLB-mapped, through a TLB the loader never initialises.
**That load is at `0x80400C00`. The first `prom_printf` is at `0x80400C04`.**
Neither line reaches the wire.

`cache.S`'s `SAFE_A0` block spends thirty lines establishing exactly this hazard
and applies the macro to `rlx_cctl`, `rlx_mfc0_cctl` and `rlx_mtc0_status`. **The
one instruction in the tree that is guaranteed by design to fault is the one
without it**, and `tools/test-rlxprobe.sh`'s `S1` — *"`SAFE_A0` is emitted before
every CP0 instruction that could fault"* — scopes it out, because `break` is not
a CP0 instruction.

**Fix:** `SAFE_A0` immediately before `break`. Two instructions.
`probe2.c` already declares `rlx_fault_frame[64]` for this. Widen `S1` to *every
instruction that could fault*, and add a mutation that fails without it.

**Refutation condition:** `exception_handlers[9] == 0x80400BE8` is *讀*, and it is
the single load-bearing unverified link in this entry. **`H0b` measures it.** If
index 9 holds a real `Bp` handler rather than `do_reserved`, this entry's severity
drops to *the failure is diagnosable after all*, and the fix stays worth two
instructions.

### 2. `install_handler` never reads the vector back — 讀

Twenty-two words go to `0x80000000` and `0x80000080` through KSEG1, then
`flush_for_handler()`, then `return words`. **The next thing that touches the
vector is `break`.** Two causes collapse into the same hang:

* **the stores did not land.** `H0a3` (`DW A0000080 32`) establishes that an
  uncached *read* of that page agrees with the cached one. Nothing in this project
  has ever *written* physical 0 through KSEG1, and `probe2` does it 44 times as its
  first act.
* **the flush ate them.** Under `FLUSH_ISC=1` the flush is `rlx_isc_inv` over
  `[0x80000000, 0x80000100)` — 64 `sb $0` at stride 4. If this core does not
  implement `Status.IsC` those are ordinary stores, and big-endian byte 0 is the
  MSB: handler word 20, `jr $26` = `0x03400008`, becomes `0x00400008` = `jr $zero`.
  `cache.S:184-186` states the danger for `probe1`'s use and adds *"probe1 points
  this only at the victim it is about to overwrite anyway, **and never at a range
  it does not own**"*. `probe2` points it at a range it does not own.

**Fix:** after `flush_for_handler()`, read the 22 words back through KSEG1 at both
vectors and compare against `rlx_exc_entry[]`; `return 0` on mismatch, reporting
the failing index. The caller's `words == 0` path already prints and stops — it
needs a second message so *"the handler does not fit"* and *"the bytes are not
there"* are different lines. **44 uncached reads, zero risk, and it converts one
class of power cycle into a printed refusal that still resets the board.**

### 3. `p2a` and `p2b` are indistinguishable on both channels — 量

```
8a15b501c160dd59c1824ab625aa1b9f2703de75d8b75f16999be378f1993c54  build/p2a/probe2/probe2.bin   -DRLX_FLUSH_ISC=0
83806b95aa39e7f7d4e1ec2d64c4c52696c51c9a9189fc16b2d7a47d59542c2e  build/p2b/probe2/probe2.bin   -DRLX_FLUSH_ISC=1
                                                                  both -DRLX_RESULT_BASE=0x80A01000u
```

`FLUSH_ISC` is in no header word, no `field()`, no banner, and `make show` does
not print it. `rb=80a01000` — the existing stale-build check — is identical for
both. The `H2a` command line differs by **four characters**. The precondition
(*only if `H1` said `IsC` is the one that works*) exists as one trailing shell
comment in the runsheet and nowhere else; `tools/rlxprobe/README.md` lists
`FLUSH_ISC` as an ordinary knob with no danger note.

**Fix, and it is not the obvious one.** Adding `field("flush", …)` would help, but
**the correct fix is not to ship two binaries.** `H1` measures which flush works;
`R1g-4b` builds one `probe2` against that measurement. Stamp the knob into a
header word and the banner anyway, because a build that cannot say what it is
cannot be checked from a capture — but the two-image hazard should not survive to
need the check.

### 4. Every CP0 read assumes `mfc0` writes `rt`, and that assumption is what the census exists to test — 量

One root cause, four sites.

```
80500218 <rlx_call0>:
80500220:  0080f809   jalr  a0
80500224:  00000000   nop          # the delay slot is free, and $v0 is never written

805002d4 <rlx_count_delta>:
805002d4:  40084800   mfc0  t0,$9  # $8 is not initialised
805002f0:  400f4800   mfc0  t7,$9  # $15 is written by no instruction in the payload
```

The handler advances `EPC` by 4 and never touches the faulting instruction's
destination register. So on **every** trap:

| site | what gets reported |
|---|---|
| a census stub (`probe2.c:273`) | `v` = whatever `$2` held on entry to `rlx_call0` — the running `zeros` counter. **A steadily increasing small integer, which reads like a family of related registers answering.** `H2d`'s instruction is to transcribe the `v` column |
| `rlx_mfc0_cctl` (`probe1`, `XCT0` row) | `$v0` = 12, the cell loop's exit compare. **CP0 register 20's read side has no second source by construction** — both known sources only ever write it — so nothing can contradict `ex=0000000c` |
| `rlx_count_delta` (`F50b`) | `delta` = (loader's leftover `$t7`) − `0xA0500150`. `H2e` expects `00000000`, so **a large residue-arithmetic value reads as its refutation** and answers `F50b` backwards |

⚠️ **The weak leg and the strong leg are different.** *"`mfc0` retires without
writing `rt`"* is the least likely of the three plausible behaviours for a
reserved `sel` — ignoring `sel` and writing `rt`, or trapping, are both more
common. **But the trap leg needs no such assumption**: on a trap the destination
is certainly not written, and `probe2` records `v` for trapped rows.

**Fix:** `addiu $2, $0, -1` into `rlx_call0`'s existing delay-slot `nop` (net zero
instructions, and it strengthens `probe1`'s `V_VOIDPRIME` for free); zero `$8`
and `$15` before their `mfc0`s; bracket the `rlx_count_delta` call with
`exc_rec(0)` exactly as the census brackets its stubs, and report the count; add
an `S_NOWRITE` state for `0xFFFFFFFF`. **The cross-check already in the run:
census row `0x48` is rd 9, sel 0 — if it reports `S_TRAP`, `count.delta` is
residue arithmetic and `F50b` is answered by row `0x48`, not by `count.delta`.**
Nothing connects the two today.

### 5. `V_NOSTORE` conflates two physically different states — 讀 `[1-src, checked by hand]`

`probe1` reads the patched word back **only** through KSEG1, for every cell —
including the four whose store went through the **cached** window (1, 4, 2, 3). On
a write-back D-cache the store sits dirty, RAM still holds `OLD`, and the verdict
ladder produces `V_NOSTORE`, whose definition asserts *"executed OLD, memory holds
OLD"*. That is literally true and would be read as *the store did not happen*.

**This is carried into `R1g-4a` rather than fixed**, because the discriminator is
already in the run: cell 1 against cell 5 on the `ma` column. `RUNSHEET.md` §H1
now carries the four-way table, the refutation condition, and the consequence —
that in the write-back case **cell 2 against cell 3 measures the D-flush and not
the I-invalidate**, which is the sentence that would otherwise reach `R5b`'s MTD
driver as a wrong flush recipe.

**Fix for `R1g-4b`:** `mem_before` is provably the constant
`RLX_VICTIM_WORD_OLD` on every row that reaches the verdict (`V_NOTVICTIM`
returns first), so **one of the eight row columns carries zero information and is
free**. Put a cached read-back there and add a `V_DIRTY` verdict. Block layout
unchanged — still eight columns, still 137 words, `DW 80A00000 137` unchanged.

## Carried into `R1g-4a` knowingly

* **`CELLS[]` runs cell 4 third.** The `Status.IsC` path is the only cell with a
  demonstrated kill (qemu, 2026-08-25), and it runs ahead of cells 2, 3 and 6,
  whose `mtc0 $t,$20` this unit's loader executes five times on every power-on.
  `probe1.c` argues both orderings, in two comment blocks, about the same pair.
  **Carried** because: the qemu kill's mechanism is now caught by the `V_CORRUPT`
  guard, which did not exist when it happened; rows 0–3 are banked first; and
  `rlx_isc_inv` is entered with `$a0` = the victim address, which `cache.S`
  argues is a real word — **so a fault there prints and hangs rather than
  double-faulting silently, which is the property `rlx_do_break` lacks.**
  Residual, unmeasured: the restore `mtc0 $8,$12` is **five instruction slots**
  ahead of `rlx_call2_uncached`'s `lw $31,0($29)`, and `C-9` is blank.
* **`V_NOSTORE`** — see §5. Handled in the sheet, not in the binary.
* **The hex-case and poison-word mismatches** — fixed in `RUNSHEET.md`, no binary
  change. `report.c`'s digit table is `"0123456789abcdef"`; the loader's is upper
  case; the sheet was written in the loader's.

## Parked, with the reason

* **`GEOM=1`.** `rlx_r3k_size` is the only routine in the payload that sets
  `Status.SwC` and is entered by a direct `jal` from KSEG0 — the invariant
  `cache.S`'s own header states and `probe1.c:299` obeys for the same two bits.
  `GEOM=0` this seating, so it does not run; but `SPEC.md` §17 names `GEOM=1` as
  the path that closes `CPU-25`, so **the next person to arm it must be told**.
  Fix is free: route it through `rlx_call2_uncached`, which already shuffles
  `arg0`/`arg1` into `$a0`/`$a1`.
* **`restore.mismatch` cannot fail for the reason it is named after.** It compares
  `VEC_GENERAL` against the same `saved_vec[]` array that just wrote it; the only
  proposition that can fail is *the uncached store landed*. And the block's words
  8–15 hold the **UTLB** vector while the check covers the **general** one.
  `H2h`, added on 2026-08-25 to cover it, **also cannot fail**: it reads
  `0x80000080` after the watchdog reset, and `trap_init` re-copies those 128 bytes
  on that boot. Belongs to `R1g-4b` with `probe2`.
* **`LOADADDR` is not in `DEFS`**, so the `.flags` stamp added on 2026-08-25 does
  not cover it — the same defect class as the `RESULT_BASE` one, in the one knob
  whose drift ships an image linked for a different address. `B4` uses
  `0x80500000` throughout, so it is not in play; it is a latent build-hygiene
  defect and belongs with the suite work.

## Refuted, and kept

* **"Interrupts are live at the prompt and `probe2` overwrites the vector that
  services them."** Four layers of the timer-interrupt chain are established
  (`REG-01` 量: `GIMR` = `0x00008100` at the prompt; `REG-09`/`REG-10` 量;
  `REG-25` 量: `0x8040DCE8` advancing at 100.0018 Hz over 2,080 s; the ISR at
  `0x80408EE0` is its only writer and it **acks `TCIR`**, which this handler does
  not). The handler adds 4 to `EPC` — which *skips* an interrupted instruction —
  and acknowledges nothing, so `rfe` would return into the same asserted
  interrupt. **Refuted by `docs/loader-command-semantics.md:1054`: `J <addr>`
  clears `IE` and zeroes `GIMR0` before entering a payload**, on every path, not
  only the `J BFC00000` case. Upstream carries `mkramboot.py --irq-restore`
  because of it.
  **Two residuals survive the refutation.** ① `probe2` has the Status word in
  hand, checks bit 22, and ignores bit 0 — two lines would turn a documented
  assumption into a checked precondition at the moment it matters. ② `uart.S`
  §`rlx_reset` says the loader's idiom *"masks no interrupts"*, which is the
  reverse of what `loader-command-semantics.md` records for the same address.
  One of the two is wrong and it is not this document's to decide.
* Nine other findings were refuted by their readers and are in the run journal
  rather than here; three of them were refuted for arithmetic the finder got
  wrong, which is the reason the refutation stage exists.

## What this audit could not check

* **Nothing on the device.** Every entry is *讀* or *量 on the emitted image*.
* **26 of 47 findings never met a refuter** — `[1-src]`. The ones that would
  change a bench decision were re-checked by hand; the rest are claims.
* **The loader-side facts it depends on.** `exception_handlers[9]`, what the UTLB
  refill vector holds, and whether the vector page is coherent uncached are
  `H0b`, `H0c` and `H0a3` — the third, fifth and fourth cells of `R1g-4a`.
  **The plan checks its own premise before it acts on it.**
* **The suite.** Whether `tools/test-rlxprobe.sh`'s 66 cases can tell a patched
  payload from a shipped one was one lens's question and its findings are
  `[1-src]`. It is the same question hazlint 1.0's review answered *no* to, and
  it has not been answered here.
