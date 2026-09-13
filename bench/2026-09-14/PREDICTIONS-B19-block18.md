# Block 18 — the first pipeline-hazard measurement on this die, and the qemu leg it must disagree with

**Written 2026-09-14, sixty-fifth segment, at the desk, before power.**
Seating 21, **one power cycle**, **two bare-metal payloads**, **twelve captured
cells**. `R1-pub-3`, slot 1 of `docs/isa-prior-art.md` § 7's schedule.

**Freeze order, and it is not optional** (`RUNSHEET.md` § *Four rules about the
card's lifecycle*):

1. **rule 4, in its payload form.** There is no kernel image tonight, so there
   is no `RECIPE_ID` to re-derive. The analogue is § 1's pair of `sha256` rows
   **plus a from-scratch rebuild into a throwaway `BUILD` directory**, because
   `RECIPE_ID`'s job here is done by the digest and the digest's job is done by
   the second build. Both ran at 05:0x; § 1 records them.
2. **rule 1** — `tools/spec-check.py` green, `rc 0` read **from a script file**
   and not from a pipeline (`CLAUDE.md`'s `EXIT CODE: 0` incident), on a tree
   where this card is already `git add`ed (seating 19's § 7, and the hole
   seating 18's desk sweep found).
3. `cardcheck commands` — every command invocable.
4. `cardcheck numbers` — every stated number re-derivable.
5. `check-predictions` — **`0 of 12`**, because no capture exists yet.
6. **rule 3** — the directory name is a **prediction** until a capture lands in
   it. `tools/capdate.py` is what checks it afterwards, and `bench/2026-08-30`
   and `-30b` are why.

---

## 0. What this block is, in one paragraph

Two payloads that have never executed on this silicon run one after the other on
one cold boot, each handing the prompt back by its own watchdog bite. `probe4`
is `R1a`'s instruction census — 75 rows, the MIPS-I baseline group as the
positive control and a reserved `SPECIAL` function code as the negative one.
`probe5` is `R1b`'s hazard ladder — 24 rungs over 10 families, every rung
computing a value that is **different under interlock and without it**. The
qemu leg ran on 2026-09-13 and was committed before this card existed: **24 of
24 rows `LOCK`**, which is `C4`, the forced anti-control. So a device run that
looks like the qemu run is the run that refutes the experiment. The single
sharpest cell is `lu_alu_d1`, whose device prediction is deliberately empty
because two vendor sources disagree about it and one of them is wrong about this
die.

---

## 1. The two payloads, pinned

Both were rebuilt from scratch into a throwaway `BUILD` directory at 05:0x on
2026-09-14 and both came out **byte-identical** to the in-tree binary the rows
below name. That is the second source `RECIPE_ID` would have been, and it exists
because seating 64 found that `probe4.o` did not depend on its **generated** row
header — a defect that was alive on `probe4`, which is the payload uploaded
first tonight. `make dep-check` is green for both.

| | `probe4` | `probe5` |
|---|---|---|
| step | `R1a` | `R1b` |
| rows | **75** | **24** |
| bytes | **16,736** | **11,056** |
| sha256 | `3320c89bf7970f5df5d11c5b523a6258acd076618a3d8545d14a21fee8871ceb` | `dc90e6d2fe984a709a3a4f1c2514948efc29651e1b9436999c6b1b417b5e9c27` |
| load address | `0x80500000`, entry is byte 0 | `0x80500000`, entry is byte 0 |
| `RB_MAGIC` | `524C5834` | `524C5835` |
| `RB_VERSION` | `00060001` | `00070001` |
| nonce | `7e41c9d0` | `5b1c0de9` |
| `RESULT_BASE` | `0x80A03000` | `0x80A04000` |
| `RB_WORDS` | **633** | **225** |
| `RB_POISON_W` | **641** | **233** |
| gate | `hazlint`: 487 loads, **0** violations | `hazdecl`: 266 loads, **7** violations, 0 unresolved |

🔴 **The two blocks do not overlap and the Makefile refuses at parse time if
they ever do** (`RB_CLASH`). `probe4`'s poison extent ends at `0x80A03A04`;
`probe5`'s base is `0x80A04000`. So `probe4`'s result survives `probe5`'s upload
and run, and the two read-backs are independent even though they share one
power cycle.

🔴 **`probe5`'s gate runs the other way round and that is the whole of `R1b`'s
pass condition.** For `probe5`, `hazlint` **exiting 0 is a build failure** — a
hazard payload with no violations has had its hazards compiled away. Nothing is
filtered and no address window is passed; `tools/hazdecl.py` runs the
**unmodified** `hazlint` over the **whole** linked image and adjudicates in both
directions, twelve checks. That inversion is what makes *each test is able to
produce the wrong answer* a desk fact rather than a hope.

---

## 2. The order, and why one power cycle is enough

Both payloads are built `RESET=1`, so each arms the watchdog at the end of its
report and the loader's prompt comes back without the power switch. That is
what makes a second payload affordable on one seating, and `R4-2` measured the
scripted reset 21/21.

The bite clears the loader's `AUTOBURN`, `LOADADDR` and target IP — measured,
`G8b-ab` read `00000001` after one — so **`probe5` gets its own rescue**, and
the burn-flag read-back is repeated before its upload rather than inherited from
`probe4`'s. `--max-rescue-age` cannot stand in for this: `loader-tftp.py`'s own
docstring says bounding the age does not establish same-boot.

| # | what | why it is where it is |
|---|---|---|
| 1 | `C1-A` — the ESC window; the operator presses power inside it | the only boot whose machine state no kernel has touched |
| 2 | `C1-Q` — `?` | 🟢 the **positive control on the adapter path**. A 3 s capture with the board off returned **0 bytes / 3.065 s** at 04:58, and the tool's own message says silence is three causes. The help text is the other side of that, and it costs one second |
| 3 | `C1-P4pre`, `C1-P5pre` — four words at each result base | 🔴 the **negative control on the writes**. Read on the cold prompt, before either upload, so *the payload wrote this block* is measured and not assumed. `MEM-17` measured DRAM keeping a previous cycle's contents across a **power** cycle, so a pre-read is the only thing that separates *written tonight* from *already there* |
| 4 | `probe4`: rescue → burn flag → upload → staged head → `J` → read-back | the `H1a`/`H2a` shape, which is this project's only precedent for a payload |
| 5 | `probe5`: the same five steps again | its own rescue, because step 4 ended in a bite |

🔴 **`looprun` does not drive either payload, and that is a measurement rather
than a preference.** Its `S4`…`S7` sequence is exactly the five steps above,
with better guards — but `S7`'s capture is `--idle 8 --seconds 45` with **no
`--esc-after`**, and a payload built `RESET=1` bites. Without `--esc-after` the
loader's ESC window is missed and the board boots the vendor firmware, which is
the failure that cost seating 17 two of its three power cycles. Its `S8` then
asserts the kernel's eleven boot marks and `RLXFW-ID0`, neither of which a
payload prints, so it could only be skipped — and skipping the assert turns the
run into an unasserted upload. **The tool is right for a kernel and wrong for a
self-resetting payload**, and `notes/dev-loop.md` is where that goes.

⚠️ **The loop's `S2` → `S7` seam is NOT on this card, and the reason is a desk
measurement taken at 05:2x rather than a scope cut.** `looprun --mode bench`
with no `--skip` is refused before any stage runs, because the `--image`
pre-flight requires `os.path.isfile()` and **`S3` is what creates that file**.
Two arms, both `rc 2`, **zero files created**; the control — `--skip S2,S3` with
an existing image — got past the same guard and reached `S4` in 12.25 s. So
`docs/GATE-RESULTS.md`'s *71 of 71 real bench invocations carried `--skip`* is
not a discipline finding, it is the tool being structurally unable to do it.
`SEAM-1` is therefore answered for **zero power cycles**, and the answer is
negative.

---

## 3. The guards, and every one of them is before an upload

| guard | cell | what must be true | what happens if it is not |
|---|---|---|---|
| burn flag | `C1-P4bf`, `C1-P5bf` | word 1 of `0x8040D4A0` reads **`00000000`** | **STOP. Nothing is uploaded.** `C-6` measured the rescue's own `AutoBurning=0` echo and this word as two sources that can disagree, which is why the read-back is a separate cell and not the rescue's line |
| staged head | `C1-P4sh`, `C1-P5sh` | the eight words at `0x80500000` **are the file that was just sent**, derived in § 4.1 and § 5.1 from the binary and typed by nobody | **STOP. Do not jump.** The reset re-stages `0x80500000` from flash, so the alternative to *my payload is there* is *the vendor's kernel is there*, and `J 80500000` would boot it |
| the filename | both uploads | `--filename probe4` / `--filename probe5` | `LDR-26`: a filename containing `nfjrom` or `boot.img` forces `0x80000000` and auto-executes with nobody at the console. Neither string appears. `--allow-autoexec` is never passed and cannot be |
| the burn path's other two barriers | both uploads | neither binary carries one of the eight section signatures `burn()` matches, and neither length is 4 KiB-aligned (16,736 and 11,056) | stated because they are what stands behind the flag, not instead of it |

⚠️ **Two opposite conventions in one block, twenty seconds apart**:
`console-dump.py rescue --load-addr` is `int(s, 0)` and takes **`0x80500000`**;
`loader-tftp.py put --expect-load` is `int(s, 16)` and takes bare
**`80500000`**. `RUNSHEET` `§G4` records this as a blind spot, because `put` and
`get` both serve `[0x8040D3A8]` and a round trip cannot catch a load address
that is consistently wrong.

---

## 4. `probe4` — `R1a`'s census, predicted field by field

### 4.1 The staged head, derived from the binary

`C1-P4sh` sends `DW 80500000 8` and the loader prints two lines of four
**upper-case** words. These eight are `word32` reads of `probe4.bin` at offsets
0…0x1C and every one is a `cardnum` row:

| address | w0 | w1 | w2 | w3 |
|---|---|---|---|---|
| `80500000:` | `3C1D8051` | `27BD83B0` | `3C088050` | `25084160` |
| `80500010:` | `3C098050` | `252943B0` | `11090004` | `00000000` |

`3C1D8051` is `lui $sp, 0x8051` and it is also the `first word` the Makefile
asserts against `_start`. **`probe5`'s first word is `3C1D8050`** — one digit
apart, on a register nothing else in the head touches, so the two staged heads
are discriminable from each other as well as from the vendor's image.

### 4.2 The fields, in emission order

Every value on the wire is exactly **eight lower-case hex digits** —
`report.c`'s digit table is `"0123456789abcdef"` and the loader's is upper, so
case alone says which side printed a word.

| field | prediction | where it comes from |
|---|---|---|
| banner | `*** rlxprobe P4 7e41c9d0 ***` | `RLX_NONCE`, compiled in |
| `pc` | inside `[80500000, 80504160)` | `rlx_pc()`; the bound is the image's own length, and a value outside it means the payload is not running where it was loaded |
| `rb` | **`80a03000`** | `RESULT_BASE`, and it is **lower** case here against the loader's upper — `Makefile`'s stale-image check is built on exactly that |
| `flags` | **`50010002`** | `0x50` tag, `RESET=1` in bit 16, `CCTL 0x002` low. 🔴 The qemu capture reads `50070002`; **any value but `50010002` and this is not the device build** |
| `status` | `BEV` clear | `CPU-27`, 量 `bench/2026-08-25b`, at the prompt |
| `rows` | **`0000004b`** | 75 |
| `kseg0` | **`00000001`** | 0 would print `NOT IN KSEG0 -- the I-side flush is void` and the length prediction in § 4.3 would break |
| `install.words` | `00000019` | handler length, a build property |
| `install.changed` | non-zero | how many vector words the install actually moved; it depends on what the loader left there |
| `install.bad` | **`00000000`** | the payload reads all installed words back through KSEG1 before it dares `break`. Non-zero aborts the sweep |
| `break.count` | **`00000001`** | 🔴 **this is `C1` and it is mandatory.** If `break` did not trap, the sweep is void before it starts and the payload refuses it |
| `break.cause` | ExcCode **9** (`Bp`) in bits 6:2 | qemu read `00000424`; the other bits are core-dependent and are recorded whole rather than masked |
| `trapped` | the reading | 🔴 the count of rows that took an exception. The **reserved-encoding row must be in it** |
| `ran` | **`0000004b`** | 75. Fewer means the sweep stopped |
| `scratch.bad` | **`00000000`** | |
| `restore.mismatch` | **`00000000`** | the two exception vectors are back as they were |
| `restore.stillhdl` | **`00000000`** | and of the words the install changed, none still holds my handler |
| `seal` | not predictable here | a sum over words that include `status` and `install.changed`. § 6 is how it is checked |
| `words` | **`00000279`** | 633 |

### 4.3 The length of the report is an equality, not an estimate

Every field line is a fixed width and every row line is
`P4 <8 hex> <name> <8 words>`, so the byte count from `*** rlxprobe` through
`rlxprobe: end\r\n` does not depend on a single value — only on which lines
exist. The one line that exists under qemu and not on the device sits **before**
the banner.

> **The device's report must be exactly 7,368 bytes**, the same window measured
> on `qemu/2026-09-13/probe4.txt` (7,429 total minus the 61-byte
> `RLX_CLEAR_BEV` warning and its blank line).

🔴 **This is worth more than the payload's own estimate and it is why the
estimate is not used.** `probe4.c` says *"~68 bytes a row, 75 rows, about
1.3 s"*; 量 on its own committed capture the rows average **90.08** bytes and
the report is **1.92 s** at 3,840 B/s — a **33 %** underestimate.
`probe5.c` corrected that figure and then underestimated its own by 4.6 %. A
prediction of equality with a committed artefact cannot drift that way.

Four distinguishable causes if the length is wrong: an abort line fired
(`HANDLER DID NOT INSTALL`, `BREAK DID NOT TRAP`), `NOT IN KSEG0` fired, a row
is missing, or the capture truncated. Each of the first three is a specific
sentence in the log.

### 4.4 The two controls `R1a` cannot pass without

* **D2b, the positive control**: the MIPS-I baseline group — `add`, `lw`, `sw`,
  `mult`, `beq`, `jr` — must read **right**. The census `R1-pub-0` built
  *excludes* that group by rule, so two sources that would have carried this
  requirement were both silent for two segments. `tools/isapay.py`'s
  `check_controls` is what enforces it now.
* **D2, the negative control**: the reserved `SPECIAL` function code must
  **trap**. 🔴 **If it does not, every zero in the table is unattributable and
  the table is void — not partially valid.** `bench/2026-08-30/QJ.log`'s `x-ri`
  is the precedent that this device does produce ExcCode `0x0A` for an
  unassigned encoding while four `cache` encodings in the same boot read `n=0`,
  so *does not trap* is a reading and not a dead processor.

---

## 5. `probe5` — `R1b`'s hazard ladder, and the cell that matters most

### 5.1 The staged head, derived from the binary

| address | w0 | w1 | w2 | w3 |
|---|---|---|---|---|
| `80500000:` | `3C1D8050` | `27BD6D80` | `3C088050` | `25082B30` |
| `80500010:` | `3C098050` | `25292D80` | `11090004` | `00000000` |

### 5.2 The header fields that differ from `probe4`

`probe5` adds four header words in `probe4`'s slack and prints three more
fields. Scratch word 3 is used where `probe4` left a hole.

| field | prediction | why |
|---|---|---|
| banner | `*** rlxprobe P5 5b1c0de9 ***` | |
| `rb` | **`80a04000`** | |
| `flags` | **`50010002`** | qemu: `50070002` |
| `rows` / `words` | **`00000018`** / **`000000e1`** | 24 and 225, identical to qemu |
| `addr0` | inside `[80500000, 80502B30)` … see below | the `storebase` family's base address, taken from scratch word 3 |
| `addr0.readback` | **equal to `addr0`** | unequal aborts: *the storebase family has no base address* |
| `addr0.bad` | **`00000000`** | |
| `aux.zero` | **`00000000`** | 🔴 `aux` is the **per-row control in every cell**. Without it *the hazard is open* and *the producer never produced* arrive as the same word, and a broken `mult` reads as an exposed `mflo` |
| `epc.end` | **`5a5a5a50`** | identical to qemu, and it is `c0_d2`'s `EPC_NEW` read from outside any cell — valid only beside `trapped` |
| `trapped` | **`00000000`** | 🔴 **this is the one field where `probe5` and `probe4` predict opposite things.** `probe4` must trap on its reserved encoding; **every one of `probe5`'s 24 rungs is trap-free by construction**, so a non-zero here is a finding about `dslot` or about `exc.S` |
| `restore.*` | **`00000000`** / **`00000000`** | |

⚠️ **The `cp0` family writes CP0 14 (EPC) on the device, and this card
re-confirms it rather than inheriting it.** EPC is the only full-width
read-write CP0 register on this core that is inert outside an exception return;
`Status` has reserved bits, so its read-back would not be a self-contained
constant, and writing an unidentified CP0 register on the one device this
project has is refused by `tools/isa-payload.tsv`'s own doctrine. The
containment argument is that a trap **during** a `c0_*` cell overwrites EPC in
hardware and the handler reads the hardware value — so the cell's own writes
cannot mislead the handler. Re-read tonight against `cells5.S`: the sequence is
`mtc0 $11,$14` with `EPC_OLD = A5A5A5A0`, three `nop`, then
`mtc0 $11,$14` with `EPC_NEW = 5A5A5A50` as the write under test, then
`mfc0 $2,$14`. **`probe5` writes CP0 `Status` nowhere on a device build** — its
one writer is in `p5support.S` under `RLX_CLEAR_BEV`, which is qemu only.

### 5.3 The 24 rungs, and the four pre-registered device predictions

The qemu leg read **`LOCK` on all 24** and was committed on 2026-09-13, before
this card existed. `C4` requires that: a row that could not read differently
under interlock has no discriminating power, and *qemu agrees with the device*
is the outcome that refutes the experiment rather than confirming it.

**Only four rows carry a device prediction. The other twenty read `-`, and that
is the honest majority.**

| row | family | d | device prediction | value it must read | why this row has one |
|---|---|---|---|---|---|
| `lu_alu_d0` | `loaduse` | 0 | 🔴 **`open`** | `B10CB10C` — `$9`'s prior value | `CPU-14`. The only route-① hazard reading this project holds, and **it is not this repository's** — upstream's `P9-12` `T-89`/`T-90` on this same physical device. If it reads `LOCK`, either that reading was wrong or this cell is broken, and either is the loudest finding this payload can produce |
| `lu_alu_d2` | `loaduse` | 2 | **`lock`** | `A5A5F00D` | upstream's `P9-12` v2 — the image that worked with two `nop`s |
| `st_p` | `storeprod` | 0 | **`lock`** | `B10CB10C` | a `ctl` row: the two constants are equal, so there is nothing to distinguish and it must read the one value |
| `hl_ctl` | `hiloprime` | 3 | **`lock`** | `CAFE0000` | the control the qemu run itself showed was missing. It primes `LO` and `HI` and reads them with **no `mult` at all**, so `gpr` says `mtlo` worked and `aux` (`BEEF0000`) says `mthi` did |

🔴🔴 **`lu_alu_d1` is the sharpest rung on the card and its device column is
empty on purpose.** Two vendor sources disagree about this one distance and
nobody has measured it: upstream's `P9-12` v2 fixed the failure with **two**
`nop`s, while rsdk 1.3.6 emits **one** under `-fuse-uls`
(`notes/vendor-toolchains.md` 252-255). **One of those two beliefs is wrong
about this die, and tonight is when that stops being an open question.** Both
outcomes are results:

* reads `A5A5F00D` (`LOCK`) → the load-use hazard closes at **d1**, and rsdk's
  single `nop` is sufficient. Upstream's second `nop` was belt-and-braces.
* reads `B10CB10C` (`OPEN`) → it closes at **d2 or later**, and **rsdk 1.3.6's
  `-fuse-uls` emits code that is wrong on this part**. That is a finding about a
  shipping vendor toolchain, not about my payload.
* reads neither → `OTHER`, which is **not a failure**: `expect_open` is 推, and
  MIPS-I says the result of reading too early is UNPREDICTABLE.

The rest of the ladder is the result rather than any single row: for each family,
the distance at which it closes. `hazpay verdict --arm device` prints the
per-row table, the tally, and then the ladder.

### 5.4 The verdict vocabulary, and why `VOID` is separate from `OPEN`

Six verdicts, in outranking order: `NOT-RUN` → `TRAPS` → `VOID` → `LOCK` →
`OPEN` → `OTHER`. `VOID` exists because *the producer never produced* and *the
hazard is open* would otherwise arrive as the same word. `hazpay verdict`
enforces four controls of its own: there must be a `ctl` row; every `ctl` row
must read `LOCK` or the whole table is void; under `--arm qemu` every row must
read `LOCK`; and the `storebase` pair must agree per rung, because exactly one
address can have been written.

---

## 6. The second channel, and the two defects in its tool

The result block is read back with `DW`, which is a **different format carrying
the same values** — the payload prints its rows from the block through KSEG1, so
what it prints is what a `DW` would return and not what it believes it wrote.
Two channels agreeing is a different claim from one channel being
self-consistent.

🔴 **The read-back count is `RB_POISON_W`, not `RB_WORDS`, and the number
`make show` prints is the wrong one.** `LDR-07`: `DW <addr> N` prints
`4 × ceil(N/4)` words and **rounds up**, so a short length does not announce
itself — the reply is always whole lines and looks complete. 量 tonight on
`bench/2026-08-24b/G4-addr-probe.log` and five others: `DW 80A00000 137` printed
the 137th word and then three more `DEADC0DE`.

| | `probe4` | `probe5` |
|---|---|---|
| `make show` prints | `DW 80A03000 633` | `DW 80A04000 225` |
| **this card types** | **`DW 80A03000 641`** | **`DW 80A04000 233`** |
| words actually printed | 644 | 236 |
| reply bytes, `tools/reply-size.py` | **7,593** | **2,799** |
| `rbcheck --words` | **633** | **225** |

`633` shows only three of the eight margin words and nothing past the poison
loop's own end, and a payload that wrote past its block writes **upward** from
the seal — so that first word past is exactly where the evidence is.
`bench/README.md` records the same lesson from `probe2`, where the command was
`817` and not `809`. ⚠️ **`DW` takes 641 and `rbcheck --words` takes 633**: two
numbers, two jobs, and passing `RB_POISON_W` to `rbcheck` reads the seal at the
poison extent, which is what its control `C2` exists for.

🔴 **`tools/rbcheck.py` cannot read tonight's blocks, and both reasons were
measured at the desk at 05:3x rather than discovered at the bench.**

1. Its `PROGRESS`, `MAGICS` and `SRC` tables know `probe1`, `probe2` and
   `probe3` only. `524C5834` and `524C5835` are in none of them, so `ladder()`
   returns `None` and the tool reports *"names no payload this tool has a
   progress ladder for"* and falls back to `restamp = 0x10`.
2. 🔴 **The correct `restamp` for both new payloads is `1`, not `0x10`** —
   both use `P_RESTORED 0xF0` and `P_SEALED 0xF1`. 🟢 **This is `rbcheck`'s own
   control `C9` arriving.** Its docstring says the value *"happens to be `0x10`
   for both payloads that exist, and control `C9` is what would notice if a
   future one differed: a correction quoted as a constant is a constant that goes
   stale."* Because `ladder()` derives it from the table instead of hardcoding
   it, **extending the table is the whole fix and not one line of arithmetic
   changes.** A design decision taken on 2026-08-31 pays tonight.
3. Its `UARTSUM` regex is `rlxprobe:\s*sum=([0-9a-f]{8})`. `probe1`/`2`/`3`
   print `sum=`; **`probe4` and `probe5` print `seal=`**. So channel (1) drops
   out silently — 🟢 except that the tool *says* `absent -- channel (1) did not
   run, and two agreeing channels are not three`, which is the difference
   between a scope limit and a hole.

**So this card does not name an `rbcheck` command.** The read-backs are captured
as evidence tonight and the tool is extended at the next desk segment with
**tonight's real capture as its on-device fixture** — which is the `C16`/`C39`
pattern (a control rewritten to match new code stops being evidence, so the
anchor is a committed capture) and is stronger than a synthetic one. Publishing a
command that goes red on its first run is what segment 59 already refused to do.

---

## 7. What this block does NOT claim

* **A row that reads `LOCK` has not shown there is no hazard.** It has shown
  that at that distance, with that operand set, **on a warm cache**, the
  consumer saw its producer's result.
* ⚠️ **Every rung runs on a warm D-cache and a warm I-cache.** `probe5` does not
  control the cache state of its operand or of its own cells. The primitive to
  force a miss exists and is measured (`cache11`, Hit Invalidate D, 量
  2026-08-29) and `rlx_call2_uncached` is already linked; **using them is the
  second seating's work** and `docs/isa-hazard.md` § 7.1 says so rather than
  leaving it to be found.
* `expect_open` is **推** and stays 推 even if it reads. MIPS-I says the result
  of reading too early is UNPREDICTABLE, so *the consumer sees the register's
  prior value* is a hypothesis about **this implementation**.
* `dslot` puts a load in a branch delay slot while `exc.S` adds 4 to `EPC`
  unconditionally, which is wrong in a delay slot. The rungs are trap-free by
  construction, and `Cause` is recorded **whole** so `BD` is visible if it ever
  is not.
* **`CPU-52`'s residual is untouched.** The store-producer variant that *is*
  measurable — store to one address, load a different address on the same cache
  line — is not on this card; it rides `CPU-45`.
* **`isapay verify --strict` is dumb about `probe5`** — every encoding is
  ordinary MIPS-I, so `hazlint --isa` reports zero hits and zero strays, and a
  clean result there passes by being blind. The check with teeth is `hazdecl`.
* **Slot 2 of the schedule is not on this card.** `CPU-45`'s cells A–G need a
  power cycle of their own by their own stop-loss, and `docs/isa-prior-art.md`
  already records that if either payload needs a re-run, `CPU-45` is what gives
  way. Slots 3–5 (a kernel of mine, `FW-65`, `FW-63`) are Linux-side and cost no
  power cycle, so they lose nothing by waiting.
* ⚠️ **The census row that maps three families onto one is still not split.**
  Splitting changes the census's population and that belongs to `R1-pub-0`;
  `hazpay population` prints the correspondence on every run.

---

## 8. The flash bracket, and the sentence that is not said

**No `FLR` runs. Zero flash-write commands. `H601` is not read.**

Every payload command on this card is a `DW`, a `J`, or the rescue's
`AUTOBURN 0` / `LOADADDR` / `IPCONFIG`. There is no `EW`, no `EB`, no `FLW` and
no burn; both uploads target `LOADADDR 80500000`, which is RAM; and the
burn-flag word is read `00000000` before each of them. `DW` issues **loads
only** (`REG-13`).

🔴 **That is deliberately not the sentence "not one flash byte is written"**, and
`RUNSHEET` `§B3`'s `G8b` is why: that wording needs a full re-dump hashed
against `FLS-14`, and this seating runs no `FLR` bracket at all. The ledger does
not move: **proven identical 4,177,920 B (99.61 %), proven different 8,192 B
(0.195 %), undetermined 8,192 B (0.195 %)**, the last being exactly `H601`.

⚠️ **What this seating *can* contribute to `FLS-26` at zero cost is nothing**,
because `rtl819x-spi`'s map needs Linux and no kernel of mine boots tonight. The
attribution bracket stays where seating 18 closed it.

---

## 9. The drop order, because the directory name is a deadline

Written **2026-09-14 at the desk** with the board off, for a seating on
**2026-09-14**. The three clocks were read at 04:54 before anything else:
Git Bash `Mon Sep 14 04:54:04 TST 2026`, Windows `2026-09-14T04:54:10+08:00`,
WSL `Mon Sep 14 04:54:27 CST 2026`. So the directory name is not a prediction
that a seating will cross midnight — it is the day the card and the captures
share, and `tools/capdate.py` is what will say so afterwards.

🔴 **If the seating slips past midnight**, the captures belong in
`bench/2026-09-15/` and this card is **not** edited to match — a rename before
the freezing commit is rule 3's answer and an edit afterwards destroys
`check-predictions`'s mtime evidence.

---

## 10. The cells

🔴 **Every capture carries a terminator.** `console-capture.py` refuses without
one and has since 2026-08-30.

🔴 **Both `J` cells carry `--esc-after`, and that is the rule seating 17 broke
twice.** A payload built `RESET=1` ends in a watchdog bite, so the cell's own
payload resets the board; `--esc-after` is what catches the ESC window on the
way back. `--until` makes `--esc-after` and `--seconds` caps rather than
durations, and `<RealTek>` is not a substring of `J 80500000`, which is the one
thing `--until` requires.

🔴 **No payload contains a `'`, a `"`, a backtick or a `$`.** The longest is 15
characters against `_check_send`'s 128-byte cliff.

```
#-- the ESC window.  THE OPERATOR PRESSES POWER INSIDE THIS WINDOW.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14/C1-A --esc 150 --esc-period 0.002 --seconds 165
#-- the positive control on the adapter path: 0 bytes with the board off at 04:58, the help text now.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14/C1-Q --send '?' --idle 3 --seconds 12
#-- 🔴 THE NEGATIVE CONTROLS ON THE WRITES.  Both read on the cold prompt, before either upload.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14/C1-P4pre --send 'DW 80A03000 4' --idle 2 --seconds 8
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14/C1-P5pre --send 'DW 80A04000 4' --idle 2 --seconds 8
#-- probe4.  The rescue writes a .json and is not a capture; --load-addr is int(s,0).
/usr/bin/python3 upstream/tools/console-dump.py rescue --at-prompt --ip 10.1.1.1 --load-addr 0x80500000 -o bench/2026-09-14/C1-P4-rescue.json
#-- 🔴 word 1 must be 00000000 or NOTHING IS UPLOADED.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14/C1-P4bf --send 'DW 8040D4A0 1' --idle 2 --seconds 8
#-- the upload.  --expect-load is int(s,16), so bare hex -- the opposite of the line above it.
/usr/bin/python3 upstream/tools/loader-tftp.py put --host 10.1.1.1 --image tools/rlxprobe/build/probe4/probe4.bin --filename probe4 --rescue-report bench/2026-09-14/C1-P4-rescue.json --expect-load 80500000 --yes
#-- 🔴 the eight words must be probe4.bin's own head (section 4.1) or DO NOT JUMP.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14/C1-P4sh --send 'DW 80500000 8' --idle 2 --seconds 8
#-- the run.  75 rows, then the bite, then the prompt.  Report window: exactly 7368 bytes.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14/C1-P4j --send 'J 80500000' --esc-after 60 --esc-period 0.002 --until '<RealTek>' --seconds 120
#-- the second channel.  641 = RB_POISON_W, not the 633 make show prints.  7593 bytes.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14/C1-P4rb --send 'DW 80A03000 641' --idle 3 --seconds 30
#-- probe5.  Its OWN rescue: probe4's bite cleared AUTOBURN, LOADADDR and the target IP.
/usr/bin/python3 upstream/tools/console-dump.py rescue --at-prompt --ip 10.1.1.1 --load-addr 0x80500000 -o bench/2026-09-14/C1-P5-rescue.json
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14/C1-P5bf --send 'DW 8040D4A0 1' --idle 2 --seconds 8
/usr/bin/python3 upstream/tools/loader-tftp.py put --host 10.1.1.1 --image tools/rlxprobe/build/probe5/probe5.bin --filename probe5 --rescue-report bench/2026-09-14/C1-P5-rescue.json --expect-load 80500000 --yes
#-- 🔴 probe5's head differs from probe4's in w0's last digit: 3C1D8050 against 3C1D8051.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14/C1-P5sh --send 'DW 80500000 8' --idle 2 --seconds 8
#-- the run.  24 rungs, then the bite, then the prompt.  Report window: exactly 2974 bytes.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14/C1-P5j --send 'J 80500000' --esc-after 60 --esc-period 0.002 --until '<RealTek>' --seconds 120
#-- 233 = RB_POISON_W.  2799 bytes.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14/C1-P5rb --send 'DW 80A04000 233' --idle 3 --seconds 30
```

⚠️ **Three steps in that list are not captures and are therefore not in the
fence**: two rescues, which write a `.json`, and two uploads, which write
nothing but their own stdout. Stated here rather than left to be noticed,
because seating 15's card had a capture **outside** its fence and `32 of 32`
then did not mean *the whole seating was checked*.

### 10.1 The numbers this card states, and where each is re-derived FROM

🔴 **Every row names a FROZEN artefact or this card itself** — lifecycle rule 2.
The two payload binaries are frozen by § 1's from-scratch rebuild: they are not
rebuilt again tonight.

```cardnum
p4-bytes	16736	size tools/rlxprobe/build/probe4/probe4.bin
p4-sha16	3320c89bf7970f5d	sha256-16 tools/rlxprobe/build/probe4/probe4.bin
p4-head0	3C1D8051	word32 tools/rlxprobe/build/probe4/probe4.bin 0x00
p4-head1	27BD83B0	word32 tools/rlxprobe/build/probe4/probe4.bin 0x04
p4-head2	3C088050	word32 tools/rlxprobe/build/probe4/probe4.bin 0x08
p4-head3	25084160	word32 tools/rlxprobe/build/probe4/probe4.bin 0x0C
p4-head4	3C098050	word32 tools/rlxprobe/build/probe4/probe4.bin 0x10
p4-head5	252943B0	word32 tools/rlxprobe/build/probe4/probe4.bin 0x14
p4-head6	11090004	word32 tools/rlxprobe/build/probe4/probe4.bin 0x18
p4-head7	00000000	word32 tools/rlxprobe/build/probe4/probe4.bin 0x1C
p5-bytes	11056	size tools/rlxprobe/build/probe5/probe5.bin
p5-sha16	dc90e6d2fe984a70	sha256-16 tools/rlxprobe/build/probe5/probe5.bin
p5-head0	3C1D8050	word32 tools/rlxprobe/build/probe5/probe5.bin 0x00
p5-head1	27BD6D80	word32 tools/rlxprobe/build/probe5/probe5.bin 0x04
p5-head2	3C088050	word32 tools/rlxprobe/build/probe5/probe5.bin 0x08
p5-head3	25082B30	word32 tools/rlxprobe/build/probe5/probe5.bin 0x0C
p5-head4	3C098050	word32 tools/rlxprobe/build/probe5/probe5.bin 0x10
p5-head5	25292D80	word32 tools/rlxprobe/build/probe5/probe5.bin 0x14
p5-head6	11090004	word32 tools/rlxprobe/build/probe5/probe5.bin 0x18
p5-head7	00000000	word32 tools/rlxprobe/build/probe5/probe5.bin 0x1C
p4-rb-reply	7593	dwreply 641
p5-rb-reply	2799	dwreply 233
pre-reply	71	dwreply 4
bf-reply	71	dwreply 1
sh-reply	118	dwreply 8
p4-qemu-bytes	7429	size qemu/2026-09-13/probe4.txt
p5-qemu-bytes	3035	size qemu/2026-09-13/probe5.txt
p4-qemu-rows	75	count qemu/2026-09-13/probe4.txt ^P4 [0-9a-f]{8} [a-z0-9_]+( [0-9a-f]{8}){8}
p5-qemu-rows	24	count qemu/2026-09-13/probe5.txt ^P5 [0-9a-f]{8} [a-z0-9_]+( [0-9a-f]{8}){8}
p4-qemu-flags	1	count qemu/2026-09-13/probe4.txt ^rlxprobe: flags=50070002$
p5-qemu-flags	1	count qemu/2026-09-13/probe5.txt ^rlxprobe: flags=50070002$
hazard-rows	24	count tools/isa-hazard.tsv ^(loaduse|storedata|storebase|hilo|cp0|movcond|movrd|dslot|storeprod|hiloprime)\t
hazard-dev-open	1	count tools/isa-hazard.tsv ^loaduse\tlu_alu_d0\t
expansion-captures	12	count bench/2026-09-14/PREDICTIONS-B19-block18.md ^/usr/bin/python3 tools/console-capture[.]py capture .*--out bench/2026-09-14/C1-
expansion-dw	8	count bench/2026-09-14/PREDICTIONS-B19-block18.md ^/usr/bin/python3 tools/console-capture[.]py capture .*-{2}send 'DW [0-9A-F]{8} [0-9]+'
expansion-jump	2	count bench/2026-09-14/PREDICTIONS-B19-block18.md ^/usr/bin/python3 tools/console-capture[.]py capture .*-{2}send 'J 80500000' -{2}esc-after
expansion-rescue	2	count bench/2026-09-14/PREDICTIONS-B19-block18.md ^/usr/bin/python3 upstream/tools/console-dump[.]py rescue -{2}at-prompt
expansion-upload	2	count bench/2026-09-14/PREDICTIONS-B19-block18.md ^/usr/bin/python3 upstream/tools/loader-tftp[.]py put -{2}host
expansion-cold	1	count bench/2026-09-14/PREDICTIONS-B19-block18.md ^/usr/bin/python3 tools/console-capture[.]py capture .*--out bench/2026-09-14/C1-A --esc 150
cells-fence	12	count bench/2026-09-14/PREDICTIONS-B19-block18.md ^bench/2026-09-14/C1-[A-Za-z0-9]+$
send-over-127	0	count bench/2026-09-14/PREDICTIONS-B19-block18.md -{2}send '[^']{128,}'
send-inner-quote	0	count bench/2026-09-14/PREDICTIONS-B19-block18.md ^/usr/bin/python3 .*-{2}send '[^']*'[^ ]
no-flr	0	count bench/2026-09-14/PREDICTIONS-B19-block18.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-14/PREDICTIONS-B19-block18.md -{2}send '[^']*(EW |EB |FLW )
no-autoexec	0	count bench/2026-09-14/PREDICTIONS-B19-block18.md ^/usr/bin/python3 .*(allow-autoexec|nfjrom|boot[.]img)
```

⚠️ **`-{2}send` is written where `--send` would be**, and it is load-bearing:
`cardcheck commands` finds cells with `--send\s+'([^']*)'`, so a guard row
spelling the flag out would be read as a cell typing `[^`. Identical to `re`,
invisible to a scanner reading the file as text. The character classes make each
`count` self-immune, because a `count` expression searches the whole file.

🔴 **Two rows of this fence were wrong on the first `cardcheck numbers` run and
both for the same reason, which is worth the line:** a `count` searches the
**whole card**, so `expansion-cold` matched its own row (2, not 1) and
`no-autoexec` matched its own row *and* § 3's prose — and § 3 has to name
`nfjrom` and `boot.img` to say why they are dangerous, so that row could never
have read 0. Anchoring both at `^/usr/bin/python3` fixes it, and **the guard row
that names a forbidden string cannot be written as a bare search for it.**

---

## 11. The fence

```cells
bench/2026-09-14/C1-A
bench/2026-09-14/C1-Q
bench/2026-09-14/C1-P4pre
bench/2026-09-14/C1-P5pre
bench/2026-09-14/C1-P4bf
bench/2026-09-14/C1-P4sh
bench/2026-09-14/C1-P4j
bench/2026-09-14/C1-P4rb
bench/2026-09-14/C1-P5bf
bench/2026-09-14/C1-P5sh
bench/2026-09-14/C1-P5j
bench/2026-09-14/C1-P5rb
```

**12 cells**, in the order they are typed. The two `.json` rescues and the two
uploads are the only artefacts of this seating outside the fence, and § 10 says
why.
