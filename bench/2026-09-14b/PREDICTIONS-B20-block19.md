# Block 19 — ten compilers on one die, and the qemu leg that has to disagree with all of them

**Written 2026-09-14, sixty-sixth segment, at the desk, before power.**
Seating 22, **one power cycle**, **one bare-metal payload**, **seven captured
cells**. `R1-pub-5` (`R1f`) and `R1-pub-6`'s silicon row (`R2c`), which
`PROGRESS.md`'s own step table says are two widths of one experiment.

**Freeze order, and it is not optional** (`RUNSHEET.md` § *Four rules about the
card's lifecycle*):

1. **rule 4, in its payload form.** There is no kernel image tonight, so there
   is no `RECIPE_ID` to re-derive. The analogue is § 1's `sha256` **plus a
   from-scratch rebuild into a throwaway `BUILD` directory**, and for this
   payload it is stronger than usual: `tcpay verify` reads the instruction words
   of every one of the twelve sites out of the linked image and refuses if any
   is not the shape `tools/isa-toolchain.tsv` declares.
2. **rule 1** — `tools/spec-check.py` green, `rc 0` read **from a script file**
   and not from a pipeline (`CLAUDE.md`'s `EXIT CODE: 0` incident), on a tree
   where this card is already `git add`ed.
3. `cardcheck commands` — every command invocable.
4. `cardcheck numbers` — every stated number re-derivable.
5. `check-predictions` — **`0 of 7`**, because no capture exists yet.
6. **rule 3** — the directory name is a **prediction** until a capture lands in
   it. `tools/capdate.py` is what checks it afterwards, and `bench/2026-08-30`
   and `-30b` are why. **`bench/2026-09-14b`** is the second directory of this
   calendar day; `bench/2026-09-14` is seating 21's and is closed.

---

## 0. What this block is, in one paragraph

One C function — `*d = *s` — is compiled **ten times**, by four toolchains at
six `-march` values, and all ten objects are linked into one payload whose
framework is built by none of them. Each is called with the same two words and
with a known sentinel in `$v0` one instruction before its load. On the exposed
`-march` side the compiler puts a `nop` between the load and the store and the
store writes the loaded value; on the non-exposed side it does not, and on this
die `lu_sd_d0` reads **OPEN** (`CPU-14`, 量 seating 21), so the store is
predicted to write the sentinel instead. Two hand-written rows are the controls
and they run in opposite directions. The qemu leg ran at 21:0x and is committed:
**12 of 12 rows LOCK**, which is the forced anti-control — a device run that
looks like the qemu run is the run that refutes the experiment.

---

## 1. The payload, pinned

Built from scratch into a throwaway `BUILD` directory and staged unchanged; the
staged copy is what the upload names and it is `cmp`-identical to the build
tree's.

| | `probe6` |
|---|---|
| steps | `R1f` (`R1-pub-5`) ＋ `R2c`'s silicon row (`R1-pub-6`) |
| rows | **12** — 10 compiled variants ＋ 2 hand-written controls |
| bytes | **8,192** |
| sha256 | `030866f5edf7fd18d9b1d556c8862edee5901300b78b53cc98bfa371fac09728` |
| staged at | `$FWRE_WORK/rebuild/bench-only/s22-20260914/rlxfw-probe6-20260914.bin` |
| load address | `0x80500000`, entry is byte 0 |
| `RB_MAGIC` | `524C5836` |
| `RB_VERSION` | `00080001` |
| nonce | `6c3a91f4` |
| `RESULT_BASE` | `0x80A05000` |
| `RB_WORDS` | **129** |
| `RB_POISON_W` | **137** |
| gate | `tcpay gate`: `hazlint` rc **1**, loads **139**, unresolved **0**, violations **7**, parsed **7**; `G1`…`G8` clean |
| qemu leg | `qemu/2026-09-14/probe6.txt`, **1,869** bytes, `12 of 12 LOCK` |

🔴 **The three result blocks do not overlap and the Makefile refuses at parse
time if they ever do** (`RB_CLASH`). `probe5`'s poison extent ends at
`0x80A043A4`; this base is `0x80A05000`. So seating 21's two blocks are still
readable in DRAM after this payload runs, which is not needed tonight and is
stated because `MEM-17` makes it true.

🔴 **The gate runs the other way round, as `probe5`'s does, and for the same
reason.** `hazlint` exiting **0** on this payload is a **build failure**: it
would mean every `nopad` variant had been padded after all and the experiment
is not in the image. `tools/hazdecl.py` could not be reused — its `P5`…`P12`
read `hazpay`'s row table and `isa-hazard.tsv`'s declared distances, and this
payload has neither — so `tcpay gate` is `hazdecl`'s resolution ③ re-implemented
against this table: the **unmodified** `hazlint` over the **whole** linked
image, no flag restricting what it scans, adjudicated in both directions, plus
`G8`, which reads the instruction words out of the ELF and does not use
`hazlint` at all.

---

## 2. The fragment, and why it is this one

```c
void rlxf(volatile unsigned *d, volatile const unsigned *s) { *d = *s; }
```

🔴 **It was chosen by refutation and the first choice was refuted by its own
build.** 量 2026-09-14, at the desk, before power: the obvious fragment
(`*p ^ seed`) compiled to `lw` / `jr ra` / `xor` in **all nine** configurations
tried — the compiler filled the load delay slot with the return jump, so the
hazard was never present to be exposed. That is `PROGRESS.md:122`'s stated risk
(*a hazard test the compiler has already fixed*) arriving as a measurement, and
`SPEC.md` `TC-07` had recorded the same shape two weeks earlier. Seven
candidates were swept with `tools/hazlint`; this is the only one that is split
by `-march` in **every** column **and** has **zero unresolved successors** in
every column, so `hazlint` can gate it whole.

Every column emits the same two instructions and the register is `$v0` in all
ten — the one the caller can prime:

| | as built |
|---|---|
| exposed side (`mips1`, `4181`) | `lw $v0,0($a1)` · **`nop`** · `sw $v0,0($a0)` |
| non-exposed side (`mips2`, `mips32`, `5281`, `4281`) | `lw $v0,0($a1)` · `sw $v0,0($a0)` |

🔴 **It cannot trap, and that is the half of the plan's sentence this block can
refute.** `lw` and `sw` are MIPS-I; neither is a MIPS32 addition, so no row here
can produce the loud failure `probe4` measured for `clz`/`clo`/`mul`
(`bench/2026-09-14/C1-P4j.log`, ExcCode 10). A wrong answer here can only be a
**silent** one, which is what `plan/router-rebuild-plan.md` calls
*錯誤，且沒有任何警告或 fault*.

⚠️ **The prediction is a COMPOSITION of two measurements and neither is new**:
`TC-15` (desk) says which `-march` values pad, `CPU-14` (silicon, seating 21)
says `lu_sd_d0` is OPEN. What is new is that **nothing built by `T2`, `T3`, or
any non-exposed `-march` has ever executed on this die** — `docs/toolchain-
comparison.md:200` records that as ✅/🔴/🔴 — so `R1f`'s *at least two `-march`
values run* is literally unmet until tonight.

---

## 3. The order, and why one power cycle is enough

`RESET=1`, so the payload arms the watchdog at the end of its report and the
loader's prompt comes back without the power switch. Only one payload runs
tonight, so that property is not load-bearing here — it is what lets the
**off-card** repeat round in § 9 cost nothing.

| # | what | why it is where it is |
|---|---|---|
| 1 | `C1-A` — the ESC window; the operator presses power inside it | the only boot whose machine state no kernel has touched |
| 2 | `C1-Q` — `?` | 🟢 the **positive control on the adapter path**. A 3 s capture with the board off returned **0 bytes** at 12:33 and an 8 s ESC capture returned **0 bytes** at 12:41, and the tool's own message says silence is three causes: the adapter, the port, or the board |
| 3 | `C1-P6pre` — four words at the result base | 🔴 the **negative control on the writes**. Read on the cold prompt, before the upload, so *the payload wrote this block* is measured and not assumed. `MEM-17` measured DRAM keeping a previous cycle's contents across a **power** cycle |
| 4 | rescue → burn flag → upload → staged head → `J` → read-back | the `H1a`/`H2a` shape, which is this project's only precedent for a payload |

🔴 **`looprun` does not drive this payload, and that is a measurement rather than
a preference.** `LOOP-4b`, 量 2026-09-14: `--mode bench` with no `--skip` is
refused before any stage runs, because the `--image` pre-flight requires
`os.path.isfile()` and `S3` is what creates that file; and `S7`'s capture
carries **no `--esc-after`**, so it cannot drive a payload that bites. Its `S8`
then asserts a kernel's boot marks, which a payload never prints.

---

## 4. The guards, and every one of them is before an upload

| guard | cell | what must be true | what happens if it is not |
|---|---|---|---|
| burn flag | `C1-P6bf` | word 1 of `0x8040D4A0` reads **`00000000`** | **STOP. Nothing is uploaded.** `C-6` measured the rescue's own `AutoBurning=0` echo and this word as two sources that can disagree, which is why the read-back is a separate cell and not the rescue's line |
| staged head | `C1-P6sh` | the eight words at `0x80500000` **are the file that was just sent**, derived in § 5.1 from the binary and typed by nobody | **STOP. Do not jump.** The reset re-stages `0x80500000` from flash, so the alternative to *my payload is there* is *the vendor's kernel is there*, and `J 80500000` would boot it |
| the filename | the upload | `--filename probe6` | `LDR-26`: a filename containing `nfjrom` or `boot.img` forces `0x80000000` and auto-executes with nobody at the console. Neither string appears. `--allow-autoexec` is never passed and cannot be |
| the burn path's other two barriers | the upload | the binary carries none of the eight section signatures `burn()` matches, and **8,192 is 4 KiB-aligned** | 🔴 **stated because this one is DIFFERENT from seating 21's.** `probe4` (16,736) and `probe5` (11,056) were both un-aligned and that was one of the two barriers standing behind the flag. **`probe6` is 8,192 bytes and IS 4 KiB-aligned**, so that barrier is gone and the burn flag is carrying more weight tonight than it did last night. The signature barrier is unaffected |

⚠️ **Two opposite conventions in one block, twenty seconds apart**:
`console-dump.py rescue --load-addr` is `int(s, 0)` and takes **`0x80500000`**;
`loader-tftp.py put --expect-load` is `int(s, 16)` and takes bare
**`80500000`**. `RUNSHEET` `§G4` records this as a blind spot, because `put` and
`get` both serve `[0x8040D3A8]` and a round trip cannot catch a load address
that is consistently wrong.

---

## 5. `probe6`, predicted field by field

### 5.1 The staged head, derived from the binary

| address | w0 | w1 | w2 | w3 |
|---|---|---|---|---|
| `80500000` | `3C1D8050` | `27BD6230` | `3C088050` | `25082000` |
| `80500010` | `3C098050` | `25292230` | `11090004` | `00000000` |

Every one of these eight is a `cardnum` row. 🔴 **w1 is the only word that
distinguishes this image from `probe4`'s and `probe5`'s heads at a glance** —
all three start `3C1D8050` (`lui $sp, 0x8050`) and differ in the stack
adjustment, because `_stack_top` moves with the image's length.

### 5.2 The fields, in emission order

Every value on the wire is exactly **eight lower-case hex digits** —
`report.c`'s digit table is `"0123456789abcdef"` and the loader's is upper, so
case alone says which side printed a word.

| field | prediction | where it comes from |
|---|---|---|
| banner | `*** rlxprobe P6 6c3a91f4 ***` | `RLX_NONCE`, compiled in |
| `pc` | **`80501258`** | 🔴 derived, not bounded. `rlx_pc` is `jr $31` / `addu $2,$31,$0` (`uart.S:70-76`), so it returns the `jal`'s address **+ 8**; the `jal` is at `80501250` in this image. **Control**: seating 21's `probe5` read `pc=80501af8` against a `jal` at `80501af0`. *(This row was first written `80501254` from mental arithmetic and the control corrected it.)* |
| `rb` | **`80a05000`** | `RESULT_BASE`, **lower** case here against the loader's upper — the Makefile's stale-image check is built on exactly that |
| `flags` | **`50010002`** | `0x50` tag, `RESET=1` in bit 16, `CCTL 0x002` low. 🔴 The qemu capture reads `50070002`; **any value but `50010002` and this is not the device build** |
| `status` | **`1000fc00`** | 量, seating 21, both payloads. `BEV` clear — `CPU-27`, `bench/2026-08-25b` |
| `rows` | **`0000000c`** | 12 |
| `kseg0` | **`00000001`** | 0 would print `NOT IN KSEG0 -- the I-side flush is void` and § 5.3's length prediction would break |
| `install.words` | **`00000016`** | 🔴 22, read out of **this image's** ELF (`rlx_exc_end 80500268` − `rlx_exc_entry 80500210`). Seating 21 refuted a prediction of `00000019` here that had been copied from a **qemu** build's capture; this one is derived from the device build and agrees with what seating 21 measured |
| `install.changed` | **`0000002b`**, with `0000002c` admissible | 量 seating 21: **43** for `probe4` on a cold boot and 43 again for `probe5`. Two of this handler's 22 words hold absolute addresses that move between images, so one more could differ |
| `install.bad` | **`00000000`** | the payload reads all installed words back through KSEG1 before it dares `break`. Non-zero aborts the sweep |
| `break.count` | **`00000001`** | 🔴 **this is `C1` and it is mandatory.** No row of this table is expected to trap, so this control is what makes `n = 0` on every row mean *nothing trapped* rather than *nothing was counted* |
| `break.cause` | **`00000024`** | 量 seating 21. ExcCode **9** (`Bp`) in bits 6:2. qemu reads `00000424`; the other bits are core-dependent and are recorded whole rather than masked |
| `addr.d` | **`80502110`** | `cell` in `.bss`, from this image's ELF |
| `addr.s` | **`80502114`** | `addr.d` + 4 |
| `cell.d` | **`5a5a0ff2`** | `P6_DST_INIT`, written and read back before any row runs — `C2` |
| `cell.s` | **`a5a5f00d`** | `P6_SRC_VAL`, likewise |
| `trapped` | **`00000000`** | 🔴 a reading, not a formality: `lw` and `sw` are MIPS-I and `probe4` measured both as `RIGHT` on this die |
| `ran` | **`0000000c`** | 12. Fewer means the sweep stopped |
| `cell.bad` | **`00000000`** | rows whose destination was not `P6_DST_INIT` before the call, or whose source was not `P6_SRC_VAL` after it |
| `split` | **the reading, and it is the one nobody has measured** | rows whose cold and warm runs disagree. `docs/isa-hazard.md` § 7.1 records that every `probe5` rung ran on a **warm** cache and that nothing had measured the cold case. **`00000000` is the expectation and a non-zero value is a finding, not a fault** |
| `restore.mismatch` | **`00000000`** | the two exception vectors are back as they were |
| `restore.stillhdl` | **`00000000`** | and of the words the install changed, none still holds my handler |
| `seal` | not predictable here | a sum over words that include `status` and `install.changed`. § 7 is how it is checked |
| `words` | **`00000081`** | 129 |

### 5.3 The length of the report is an equality, not an estimate

Every field line is a fixed width and every row line is
`P6 <8 hex> <name> <8 words>`, so the byte count from `*** rlxprobe` through
`rlxprobe: end\r\n` does not depend on a single value — only on which lines
exist.

> **The device's report must be exactly 1,808 bytes**, the same window measured
> on `qemu/2026-09-14/probe6.txt` (1,869 total minus the 61 bytes before its
> first `***`).

🔴 **The 61 is measured in both directions and a naive subtraction was wrong by
two.** The qemu-only `RLX_CLEAR_BEV` warning line is **59** bytes with its CRLF;
subtracting only that gives 7,370 and 2,976 for `probe4` and `probe5`, against
device readings of **7,368** and **2,974**. The missing two bytes are the
banner's own leading `\r\n`, which sits *before* the `***` the window starts at.
量: the offset of the first `***` is **61** in all three qemu captures, and
`window = total − 61` reproduces both measured device figures exactly.

Four distinguishable causes if the length is wrong: an abort line fired
(`HANDLER DID NOT INSTALL`, `BREAK DID NOT TRAP`, `THE TWO WORDS DID NOT READ
BACK`), `NOT IN KSEG0` fired, a row is missing, or the capture truncated. Each
of the first four is a specific sentence in the log.

### 5.4 The three controls this block cannot pass without

* **`c_lock`, the positive control.** Hand-written `lw` / `nop` / `sw` with this
  payload's own operands, at `0x80500ED4`. **It must read LOCK.** If it does
  not, the thunk is not priming the sentinel or the two words are not what the
  payload believes, and **every OPEN below is unattributable**.
* **`c_open`, the negative control.** Hand-written `lw` / `sw`, at
  `0x80500EEC` — `isa-hazard.tsv`'s `lu_sd_d0` with these operands. **It must
  read OPEN.** If it does not, this die's d0 is not open *tonight* and no
  compiled row can be read as evidence about a compiler: **the table is void,
  not partly valid.**
* **The forced anti-control, already recorded.** Under qemu every row must read
  **LOCK**, because qemu interlocks. 🟢 量 2026-09-14, committed before this
  card existed: `qemu/2026-09-14/probe6.txt`, **12 of 12 LOCK**, `trapped 0`,
  `cell.bad 0`, `split 0`. **A device run that reproduces it refutes the
  experiment.**

`tools/tcpay.py`'s `check_controls` enforces all three and **refuses a verdict**
rather than reporting one when any fails.

---

## 6. The twelve rows, and the ten pre-registered predictions

The site address is where the row's `lw` sits in this image, read out of the ELF
by `tcpay verify`. `pad` is what the build was measured to be; `expect` is what
that plus `CPU-14` predicts the device will do.

| row | toolchain | `-march` | site | `pad` | device prediction |
|---|---|---|---|---|---|
| `c_lock` | hand-written | — | `80500ED4` | pad | **LOCK** · positive control |
| `c_open` | hand-written | — | `80500EEC` | nopad | **OPEN** · negative control |
| `v1` | T4 gcc 12.4.0 | `mips1` | `80501BB0` | pad | **LOCK** · the instrument's own control |
| `v2` | T4 | `mips2` | `80501BD0` | nopad | **OPEN** |
| `v3` | T4 | `mips32` | `80501BE0` | nopad | **OPEN** · the `-march` `CLAUDE.md` bans by name |
| `v4` | T1 rsdk 1.3.6-4181, gcc 3.4.6 | `4181` | `80501BF0` | pad | **LOCK** |
| `v5` | T1 | `5281` | `80501C10` | nopad | **OPEN** |
| `v6` | T2 rsdk 1.3.6-5281, gcc 3.4.6 | `4181` | `80501C20` | pad | **LOCK** |
| `v7` | T2 | `5281` | `80501C40` | nopad | **OPEN** |
| `v8` | T3 rsdk 1.5.5-5281, gcc 4.4.5 | `4181` | `80501C50` | pad | **LOCK** |
| `v9` | T3 | `5281` | `80501C70` | nopad | **OPEN** |
| `v10` | T3 | `4281` | `80501C80` | nopad | **OPEN** · nothing has ever been built at `4281` in this project |

🟢 **`v4`/`v5` against `v6`/`v7` separate the flag from the release**, and the
desk half of that is already 量: the 4181 release at `-march=5281` does **not**
pad and the 5281 release at `-march=4181` **does**. So padding follows the flag
in all three rsdk releases, which narrows `TC-q` without closing it — that row
is about dhrystone counts, not about this one shape.

**The verdict vocabulary**, `tools/tcpay.py verdict`:

| verdict | when |
|---|---|
| `LOCK` | both runs stored `a5a5f00d` — the consumer saw the loaded value |
| `OPEN` | both runs stored `b10cb10c` — the consumer saw `$v0`'s prior value |
| `SPLIT` | the cold and warm runs disagree. **Its own verdict, not an average** |
| `VOID` | the destination was not `5a5a0ff2` before the call, or the source was not `a5a5f00d` after it, or the destination is untouched |
| `TRAPS` | `n > 0`. No row is expected to reach this |
| `NOT-RUN` | the tag word is not `5006000<i>` — this row never started |
| `OTHER` | neither constant. **Not a failure**: the hazard is open and the mechanism is not the prior value, which is a larger finding than `OPEN` |

---

## 7. The second channel

`DW 80A05000 137` — **137 is `RB_POISON_W`, not the 129 `make show` prints.**
`LDR-07` rounds a `DW` up to a multiple of four words, so a block whose length
is a multiple of four would return no word past its own seal — and a payload
that wrote past its block writes **upward from the seal**, which is exactly
where the evidence would be. `129 % 4 = 1`, so the eight words past the seal are
returned and must all read `DEADC0DE`.

Predicted reply: **1,671 bytes** (`tools/reply-size.py predict`).

🔴 **No `rbcheck` command is on this card.** `RB-1` (`PROGRESS.md:1701`):
`tools/rbcheck.py`'s `PROGRESS`/`MAGICS`/`SRC` tables know `probe1`…`probe3`
only, so `524C5836` would fall to the `restamp = 0x10` fallback, and its
`UARTSUM` regex is `sum=` where this payload prints `seal=`. Naming it would be
naming a tool that cannot read this block. The three-way agreement is done by
hand tonight, as it was on seating 21: the UART's `seal=` line, the seal word in
the `DW` read-back, and the sum recomputed from the read-back.

---

## 8. What this block does NOT claim

* **It does not measure the die's load-use hazard.** That is `CPU-14`, 量 seating
  21, and this block *composes* it with a compiler's behaviour. A row reading
  OPEN is evidence about **that build**, given `CPU-14`; it is not a second
  measurement of `CPU-14`. The one row that is a second measurement is `c_open`,
  and it is a control rather than a result.
* **It does not control the D-cache state of the two words.** They are adjacent
  in one static array and written immediately before every call, so both are
  warm in D by construction. Only the **I**-side is controlled, and the `split`
  column is what that control produces.
* **It says nothing about any `-march` value not in the table**, and nothing
  about any optimisation level but `-O2`.
* **It is not a toolchain recommendation.** `R2c`'s decision, if one is made, is
  made by `docs/toolchain-comparison.md`'s table; this block supplies one row of
  it — the row `plan/router-rebuild-plan.md:389` marks as the only cell that can
  silently kill the project.
* ⚠️ **`4281` is a name, not a core.** `v10` establishes that a compiler
  targeting `4281` emits unpadded code and that the code runs; it says nothing
  about whether this die *is* an RLX4281 — `PRId` already answered that
  (`RLX4181` revision 1).

---

## 9. The flash bracket, and the sentence that is not said

**No `FLR` runs tonight and no flash-write command is issued.** The bracket
therefore stands where seating 21 left it: **1,024 of 4,194,304 bytes =
0.0244 %**, and `FLS-26`'s ledger — proven identical 4,177,920 B, proven
different 8,192 B, undetermined 8,192 B — **does not move**.

🔴 *Not one flash byte is written* is **not** said, and this card does not say
it. What is measured is narrower: zero flash-write commands, `AUTOBURN` read as
`00000000` before the one upload, and one `J` to RAM.

⚠️ **And tonight the un-aligned-length barrier is absent** — § 4 says so — so
the burn-flag read-back is doing more work than it did last night.

---

## 10. The drop order, because the directory name is a deadline

Read all three clocks before the first capture — Git Bash, Windows,
WSL — and if the seating crosses midnight the captures go in
`bench/2026-09-15/` and **this card is not edited**: rename the directory,
re-derive the fence and the `expansion-*` rows, re-run `spec-check`, then
commit. ⚠️ PowerShell's `Get-Date -UFormat %s` is off by the UTC offset on this
host; use `[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()` or take the epoch from
Git Bash or WSL.

**Off-card and declared here rather than folded into the fence**: after the
carded cells, the same `DW 80A05000 137` is read a second time as `X1-P6rb2`,
and the payload is re-uploaded and re-run as `X1-P6j2`. Both are free — the
payload hands the prompt back by itself — and the second run is what turns *this
is what the die did* into *this is what the die does*.

---

## 11. The cells

🔴 **Every capture carries a terminator.** `console-capture.py` refuses without
one and has since 2026-08-30.

🔴 **The `J` cell carries `--esc-after`, and that is the rule seating 17 broke
twice.** A payload built `RESET=1` ends in a watchdog bite, so the cell's own
payload resets the board; `--esc-after` is what catches the ESC window on the
way back. `--until` makes `--esc-after` and `--seconds` caps rather than
durations, and `<RealTek>` is not a substring of `J 80500000`, which is the one
thing `--until` requires.

🔴 **No payload contains a `'`, a `"`, a backtick or a `$`.** The longest is 15
characters against `_check_send`'s 128-byte cliff.

🔴 **No cell's payload contains a `sleep`**, so `--idle` cannot end a capture
inside its own silence — the defect that would have emptied five cells of
seating 20's card.

```
#-- the ESC window.  THE OPERATOR PRESSES POWER INSIDE THIS WINDOW.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14b/C1-A --esc 150 --esc-period 0.002 --seconds 165
#-- the positive control on the adapter path: 0 bytes with the board off at 12:33 and 12:41, the help text now.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14b/C1-Q --send '?' --idle 3 --seconds 12
#-- 🔴 THE NEGATIVE CONTROL ON THE WRITES.  Read on the cold prompt, before the upload.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14b/C1-P6pre --send 'DW 80A05000 4' --idle 2 --seconds 8
#-- the rescue writes a .json and is not a capture; --load-addr is int(s,0).
/usr/bin/python3 upstream/tools/console-dump.py rescue --at-prompt --ip 10.1.1.1 --load-addr 0x80500000 -o bench/2026-09-14b/C1-P6-rescue.json
#-- 🔴 word 1 must be 00000000 or NOTHING IS UPLOADED.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14b/C1-P6bf --send 'DW 8040D4A0 1' --idle 2 --seconds 8
#-- the upload.  --expect-load is int(s,16), so bare hex -- the opposite of the line above it.
/usr/bin/python3 upstream/tools/loader-tftp.py put --host 10.1.1.1 --image /home/key/fwre-work/rebuild/bench-only/s22-20260914/rlxfw-probe6-20260914.bin --filename probe6 --rescue-report bench/2026-09-14b/C1-P6-rescue.json --expect-load 80500000 --yes
#-- 🔴 the eight words must be probe6.bin's own head (section 5.1) or DO NOT JUMP.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14b/C1-P6sh --send 'DW 80500000 8' --idle 2 --seconds 8
#-- the run.  12 rows, then the bite, then the prompt.  Report window: exactly 1808 bytes.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14b/C1-P6j --send 'J 80500000' --esc-after 60 --esc-period 0.002 --until '<RealTek>' --seconds 120
#-- the second channel.  137 = RB_POISON_W, not the 129 make show prints.  1671 bytes.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-14b/C1-P6rb --send 'DW 80A05000 137' --idle 3 --seconds 30
```

⚠️ **Two steps in that list are not captures and are therefore not in the
fence**: the rescue, which writes a `.json`, and the upload, which writes
nothing but its own stdout. Stated here rather than left to be noticed, because
seating 15's card had a capture **outside** its fence and `32 of 32` then did
not mean *the whole seating was checked*.

### 11.1 The numbers this card states, and where each is re-derived FROM

🔴 **Every row names a FROZEN artefact or this card itself** — lifecycle rule 2.
The payload binary is frozen by § 1's staging: the card names the **staged**
copy, not the build tree, and the build tree's copy was `cmp`-identical to it
when it was staged.

```cardnum
p6-bytes	8192	size /home/key/fwre-work/rebuild/bench-only/s22-20260914/rlxfw-probe6-20260914.bin
p6-sha16	030866f5edf7fd18	sha256-16 /home/key/fwre-work/rebuild/bench-only/s22-20260914/rlxfw-probe6-20260914.bin
p6-head0	3C1D8050	word32 /home/key/fwre-work/rebuild/bench-only/s22-20260914/rlxfw-probe6-20260914.bin 0x00
p6-head1	27BD6230	word32 /home/key/fwre-work/rebuild/bench-only/s22-20260914/rlxfw-probe6-20260914.bin 0x04
p6-head2	3C088050	word32 /home/key/fwre-work/rebuild/bench-only/s22-20260914/rlxfw-probe6-20260914.bin 0x08
p6-head3	25082000	word32 /home/key/fwre-work/rebuild/bench-only/s22-20260914/rlxfw-probe6-20260914.bin 0x0C
p6-head4	3C098050	word32 /home/key/fwre-work/rebuild/bench-only/s22-20260914/rlxfw-probe6-20260914.bin 0x10
p6-head5	25292230	word32 /home/key/fwre-work/rebuild/bench-only/s22-20260914/rlxfw-probe6-20260914.bin 0x14
p6-head6	11090004	word32 /home/key/fwre-work/rebuild/bench-only/s22-20260914/rlxfw-probe6-20260914.bin 0x18
p6-head7	00000000	word32 /home/key/fwre-work/rebuild/bench-only/s22-20260914/rlxfw-probe6-20260914.bin 0x1C
p6-rb-reply	1671	dwreply 137
pre-reply	71	dwreply 4
bf-reply	71	dwreply 1
sh-reply	118	dwreply 8
p6-qemu-bytes	1869	size qemu/2026-09-14/probe6.txt
p6-qemu-rows	12	count qemu/2026-09-14/probe6.txt ^P6 [0-9a-f]{8} [a-z0-9_]+( [0-9a-f]{8}){8}
p6-qemu-flags	1	count qemu/2026-09-14/probe6.txt ^rlxprobe: flags=50070002$
p6-qemu-lock	12	count qemu/2026-09-14/probe6.txt ^P6 [0-9a-f]{8} [a-z0-9_]+ [0-9a-f]{8} 00000000 00000000 00000000 a5a5f00d a5a5f00d a5a5f00d 5a5a0ff2$
tc-rows	12	count tools/isa-toolchain.tsv ^[a-z0-9_]+\t(T[1-4]|-{2})\t
tc-variants	10	count tools/isa-toolchain.tsv ^v[0-9]+\tT[1-4]\t
tc-controls	2	count tools/isa-toolchain.tsv ^c_(lock|open)\t-{2}\t-{2}\t
tc-pad	5	count tools/isa-toolchain.tsv \tpad\tlock\t
tc-nopad	7	count tools/isa-toolchain.tsv \tnopad\topen\t
expansion-captures	7	count bench/2026-09-14b/PREDICTIONS-B20-block19.md ^/usr/bin/python3 tools/console-capture[.]py capture .*--out bench/2026-09-14b/C1-
expansion-dw	4	count bench/2026-09-14b/PREDICTIONS-B20-block19.md ^/usr/bin/python3 tools/console-capture[.]py capture .*-{2}send 'DW [0-9A-F]{8} [0-9]+'
expansion-jump	1	count bench/2026-09-14b/PREDICTIONS-B20-block19.md ^/usr/bin/python3 tools/console-capture[.]py capture .*-{2}send 'J 80500000' -{2}esc-after
expansion-rescue	1	count bench/2026-09-14b/PREDICTIONS-B20-block19.md ^/usr/bin/python3 upstream/tools/console-dump[.]py rescue -{2}at-prompt
expansion-upload	1	count bench/2026-09-14b/PREDICTIONS-B20-block19.md ^/usr/bin/python3 upstream/tools/loader-tftp[.]py put -{2}host
expansion-cold	1	count bench/2026-09-14b/PREDICTIONS-B20-block19.md ^/usr/bin/python3 tools/console-capture[.]py capture .*--out bench/2026-09-14b/C1-A --esc 150
cells-fence	7	count bench/2026-09-14b/PREDICTIONS-B20-block19.md ^bench/2026-09-14b/C1-[A-Za-z0-9]+$
send-over-127	0	count bench/2026-09-14b/PREDICTIONS-B20-block19.md -{2}send '[^']{128,}'
send-inner-quote	0	count bench/2026-09-14b/PREDICTIONS-B20-block19.md ^/usr/bin/python3 .*-{2}send '[^']*'[^ ]
send-has-sleep	0	count bench/2026-09-14b/PREDICTIONS-B20-block19.md -{2}send '[^']*sleep
no-flr	0	count bench/2026-09-14b/PREDICTIONS-B20-block19.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-14b/PREDICTIONS-B20-block19.md -{2}send '[^']*(EW |EB |FLW )
no-autoexec	0	count bench/2026-09-14b/PREDICTIONS-B20-block19.md ^/usr/bin/python3 .*(allow-autoexec|nfjrom|boot[.]img)
```

⚠️ **`-{2}send` is written where `--send` would be**, and it is load-bearing:
`cardcheck commands` finds cells with `--send\s+'([^']*)'`, so a guard row
spelling the flag out would be read as a cell typing `[^`. Identical to `re`,
invisible to a scanner reading the file as text. The character classes make each
`count` self-immune, because a `count` expression searches the whole file —
which is what made two of seating 21's fence rows wrong on their first run.

---

## 12. The fence

```cells
bench/2026-09-14b/C1-A
bench/2026-09-14b/C1-Q
bench/2026-09-14b/C1-P6pre
bench/2026-09-14b/C1-P6bf
bench/2026-09-14b/C1-P6sh
bench/2026-09-14b/C1-P6j
bench/2026-09-14b/C1-P6rb
```

**7 cells**, in the order they are typed. The `.json` rescue and the upload are
the only artefacts of this block outside the fence, and § 11 says why.
