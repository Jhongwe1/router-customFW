# CORRECTIONS — block 19, seating 22, 2026-09-14

Beside `PREDICTIONS-B20-block19.md`, which is frozen and was not touched.
`RUNSHEET.md`'s card-lifecycle rule 1 says corrections go here; `tools/check-
predictions.py:50-54` decides *written first* by the card's mtime, so fixing
even a typo in the card would void the ordering evidence for all seven cells.

🔴 **§ 0 was written BEFORE power, before any cell ran, and is committed in a
commit that predates every capture in this directory.** That ordering is the
point of the section and § 0.1 is why.

---

## 0. The pre-power audit

### 0.1 Why this file exists before the seating, and exactly what that is worth

量 2026-09-14 (sixty-eighth segment, desk), one `git log --reverse
--diff-filter=A --name-only -- bench/` pass, comparing committer dates:

> **Eighteen `CORRECTIONS-block*.md` files. Zero were committed before their
> own directory's first `.log`** — seventeen entered in the *same* commit as
> the captures they correct, one (block 18) entered a later commit.

🟢 **The positive control fires**, so *BEFORE* is a verdict this comparison can
reach and no corrections file has ever reached it: **17 of 33 bench directories
have a `PREDICTIONS-*` file committed before their first `.log`**. Same tree,
same comparison, same commit dates.

⚠️ **What that measures and what it does not.** Committer dates, not mtimes —
mtimes are not clone-stable, which is `check-predictions`'s own stated limit.
A corrections file in the *same commit* as its captures is **not** evidence its
text was written afterwards; the text could have been typed first and committed
together. So the claim is about the **committed record**, not about when anyone
typed anything. That is precisely why committing this file in a commit that
predates the captures is the stronger artefact: it puts the ordering somewhere
a reader can check without trusting a sentence.

`bench/2026-09-10/CORRECTIONS-block17.md` § 0 is the precedent for writing a
correction down before it is executed, and `PROGRESS.md`'s `CARD-3` names it as
the precedent to follow. Its own commit is `8933ce7`, 22:10:33, after captures
that begin 19:39 — so it claims the ordering in prose and cannot show it. This
file is that precedent with the ordering made visible in git.

### 0.2 The base rate this audit was sized against

The same corpus, read file by file, counting each corrections file's own
distinct items by whatever structure that file uses:

| | |
|---|---|
| defects recorded over 18 frozen cards | **144, ≈ 8.0 per card** |
| caught **before** power | **18 of 144 — 12.5 %** |
| found only **after** the board was on | 122 of 144 — 84.7 % |
| power cycles spent on a card defect | **4, in 3 of 18 seatings (17 %)** |
| block 17 — the one seating that made a pre-power audit a **policy** | **5 of 10 — 50 %** |

⚠️ **These five figures are 讀, not 量, and the distinction is not pedantic.**
Each file states its defects in its own shape — numbered sections, a `###`
ladder, a table, a self-declared count — so *144* rests on a counting rule
chosen per file rather than on an instrument. The ordering figures in § 0.1
above are different: those came from one `git log` pass and a positive control,
and they are 量.

🔴 **The absolute is the weak half; the RATIO is what this audit was sized
against**, and the ratio survives any reasonable re-count because the two
populations are counted the same way: **12.5 % of defects were caught before
power across seventeen seatings, and 50 % in the one that made a pre-power pass
a policy.** If a re-count moves 144, it moves both numerator and denominator.
⚠️ Nothing in this repository can re-derive 144 automatically, so a reader who
needs it exact has to re-read eighteen files — and this row says so instead of
letting a relayed number read like a measurement.

Two cards and 34 cells are riding one power cycle tonight. At 8 per card the
expectation is ~16 defects; the difference between a deliberate pre-power pass
and none is the difference between 12.5 % and 50 % of them being found while
finding them is still free.

### 0.3 The findings, ranked by what they cost at the bench

Eleven. **None of them costs a power cycle.** Two would act during the seating
and are stated first; the rest are in the reading layer and are recorded so the
write-up does not inherit them.

---

#### 0.3.1 🔴🔴 The burn-flag guard is written as a WORD ORDINAL, and `SPEC.md` says by name not to do that

**Card § 4's guard table and § 10's comment**: *"word 1 of `0x8040D4A0` reads
`00000000`"* and `#-- 🔴 word 1 must be 00000000 or NOTHING IS UPLOADED.`

`DW 8040D4A0 1` does not return one word. `LDR-07` rounds a `DW` up to a
multiple of four, so the reply is
`8040D4A0:<TAB>W0<TAB>W1<TAB>W2<TAB>W3`, and `AUTOBURN` is **W0**, at the
address named. Under a 1-based reading *word 1* is W0 and the guard is right.
Under a 0-based reading *word 1* is W1, at `0x8040D4A4`, **which is not the
flag**.

🔴 **The failure mode is a flash write, and it reads as a pass.** With
`AUTOBURN` set the reply is `00000001 00000000 00000000 00000000`; a 0-based
reader sees `00000000`, judges the guard satisfied, and the upload proceeds.

`SPEC.md` `LDR-38` closes with this exact instruction, and with the precedent:

> ⚠️ **判準用位址寫，不要用字序號** —— 上機卡曾經在相隔四列的兩格裡用了
> 1-based 與 0-based 兩種編號，而 0-based 那一格是停止條件（`RUNSHEET` §B5-c8）

**Correction, and it changes no command and costs nothing.** `C1-P6bf` already
captures all four words, because the loader returns four whatever is asked.
Read the guard as: **the word AT `0x8040D4A0` must be `00000000`, and all four
words of the reply must be `00000000`.** All-four is not stricter than the
evidence — 量 `bench/2026-09-14/C1-P4bf.log`, seating 21 read all four as
`00000000` — and a false stop here costs nothing at all, because the board is
sitting at the prompt with nothing uploaded.

⚠️ **It has never bitten**: every `C1-P4bf`/`C1-P5bf` capture in the record
reads four zero words. *Has never bitten* is not a guard.

#### 0.3.2 🔴 § 7 predicts eight words past the seal; the reply carries eleven, and the last three are not poison

**Card § 7 and § 10**: `DW 80A05000 137`, with *"`129 % 4 = 1`, so the eight
words past the seal are returned and must all read `DEADC0DE`."*

The eight-word half is right. The reply is not eight words long.
`ceil(137/4) × 4 = 140`, so the loader prints **140 words**: the seal at index
128, `RB_POISON_W − RB_WORDS = 8` poison words at 129–136, and **indices 137,
138, 139 — three words of DRAM that `probe6` never wrote**
(`probe6.c:353`, the poison loop runs to `RB_POISON_W`).

🔴 **An operator checking *every word past the seal is `DEADC0DE`* sees a
failure on a block that passed.** The precedent is measured and is in this
repository: `bench/2026-09-14/C1-P4rb.log`'s last line reads
`80A03A00: DEADC0DE 71555751 57B51151 55515547` — one poison word and three
words of garbage, on a run whose three channels agreed.

🔴 **And the card contradicts itself**: § 11.1's predicted reply of **1,671
bytes** is `tools/reply-size.py predict`'s figure for **140** words
(35 lines), not 137. 量, re-run tonight's four sizes:
`DW 80A05000 137 → 1671`, `DW 80A05000 4 → 71`, `DW 8040D4A0 1 → 71`,
`DW 80500000 8 → 118`. Seating 21's card carried a *words actually printed*
row (`644`/`236`); this one dropped it.

**Correction.** Words 129–136 must all read `DEADC0DE`. Words 137–139 are
**unpredicted and carry no verdict**. 🟢 `tools/rbcheck.py`'s `margin()` already
gets this right — it walks `range(count, poison_words)` and stops at 136 — so
the instrument and the card disagree and the instrument is correct.

#### 0.3.3 🔴 The off-card round has an ordering dependency on block 20 that neither card states, and no burn-flag guard

**Card § 10**: after the carded cells, `X1-P6j2` re-uploads and re-runs the
payload and `X1-P6rb2` re-reads `DW 80A05000 137`.

Two things are missing:

1. **Ordering.** `0x80A05000` is DRAM. Block 20's first Linux boot writes it.
   Block 20's card says only *"The board is at the loader prompt, left there by
   block 19's `C1-P6rb`"* — neither card says the off-card round must finish
   **before** block 20 starts. It must.
2. **The guard.** The re-upload is an upload, and § 4 says the rescue's echo
   and the word at `0x8040D4A0` *"are two sources that can disagree, which is
   why the read-back is a separate cell"*. The off-card round declares a fresh
   rescue and **no burn-flag read-back**. 量 seating 21: probe4's bite cleared
   `AUTOBURN`, `LOADADDR` and the target IP, so the rescue is needed — and so
   is its read-back, on the same argument the card makes for the carded one.

**Correction.** The off-card round runs before block 20's first `looprun`, and
it carries a `DW 8040D4A0 1` read-back between its rescue and its upload, read
under 0.3.1's rule.

#### 0.3.4 🔴 § 10's midnight branch cannot be executed as written

It says: if the seating crosses midnight the captures go in `bench/2026-09-15/`
and *"this card is not edited: rename the directory, re-derive the fence and
the `expansion-*` rows, re-run `spec-check`, then commit."*

The fence and six `cardnum` rows contain the literal `bench/2026-09-14b/`.
Re-deriving them **is** editing the frozen card, which the same sentence
forbids and which voids `check-predictions`'s mtime evidence. And if the
directory is renamed while the card is not edited, every `--out
bench/2026-09-14b/…` still names the old directory and
`tools/console-capture.py:439` does `os.makedirs(..., exist_ok=True)` — it
**silently re-creates** `bench/2026-09-14b/` and the seating lands there while
the renamed directory stays empty.

Seating 21's card had the rule right: *"a rename before the freezing commit is
rule 3's answer and an edit afterwards destroys `check-predictions`'s mtime
evidence"* (`bench/2026-09-14/PREDICTIONS-B19-block18.md:452-455`). This card
rewrote a correct rule into an unexecutable one.

**Correction.** If the seating crosses midnight, **nothing is renamed and
nothing is edited.** The captures land in `bench/2026-09-14b/` as the card
names them, and `tools/capdate.py` reports the directory-name mismatch
afterwards — which is what `bench/2026-08-30` and `-30b` are, declared by name
rather than repaired. ⚠️ Low probability tonight: a 19:00 start against ~10
minutes of block-19 captures.

---

#### 0.3.5 ⚠️ `CPU-14` is the wrong `SPEC.md` row — six occurrences — and the card was right when it was written

This payload's fragment is `lw $v0,0($a1)` ; `sw $v0,0($a0)`: the consumer is
the **store's data operand**, which is `lu_sd_d0`. `SPEC.md:132` `CPU-58` owns
that. `SPEC.md:106` `CPU-14` owns the **loaduse** family — `lu_alu_d0/d1/d2`,
consumer is the ALU — and its quantity is not in this payload at all.

量: **six occurrences** on six lines (38, 121, 267, 327, 329, 330), zero of
`CPU-58`. 🔴 `SPEC.md` `CPU-58`'s own row says *"卡片**兩處**"* — **that count
is wrong and this file is where it is corrected.**

🟢 **And the card is exonerated**: `git show 1bbd587:SPEC.md | grep -c CPU-58`
→ **0**. `CPU-58` was added in `44cff1c` at **15:44:47**; this card froze in
`1bbd587` at **13:52:58**, one hour fifty-two minutes earlier. Block 20's card
froze at 15:33:16, eleven minutes before the row existed. **Neither card could
have cited it.** This is a row that arrived late, not a citation nobody
checked.

⚠️ **The unfinished half, and it is deliberate.** `tools/isa-toolchain.tsv`
(lines 50, 57, 77) and `tools/tcpay.py` (251, 257, 889) are **not** frozen and
still say `CPU-14`, so tonight `tcpay verdict` will print *"refutes `CPU-14`
under compiler-generated conditions"* if a `nopad` row reads LOCK, naming a row
the result cannot touch. `tcpay.py:1236`'s self-test `T22` asserts that literal
string, so the tool and its test move together or not at all.

🔴 **The decision is NOT to change the instrument tonight, and the reason is
not convenience.** The card is frozen and says `CPU-14`; a tool that said
`CPU-58` would disagree with the card it is analysing, which is a *new*
inconsistency introduced hours before a measurement. The correction is recorded
here, before power, so the write-up cannot put the result in the wrong row —
and the tool change is carried forward to a desk segment where it can be made
with its test and its own controls.

**Read every `CPU-14` on this card, and every `CPU-14` `tcpay` prints tonight,
as `CPU-58`.**

#### 0.3.6 ⚠️ § 4's alignment claim has no source, and the owner file says something else

**Card § 4**: *"`probe6` is 8,192 bytes and IS 4 KiB-aligned, so that barrier
is gone and the burn flag is carrying more weight tonight than it did last
night."*

讀 `docs/loader-flash-write.md:36-50`, which is the only place the test
appears: `andi v0,s1,0xfff` / `bnez v0,…skip` / `lw v1,0(s6+s1)` /
`bne v1,0xDEADC0DE,…skip` / `addiu s1,s1,4`. It gates **only** the
`0xDEADC0DE` marker's +4 length extension. It does not decide whether `burn()`
writes. 量: two hits repo-wide for `0xfff`/`4 KiB-align`, both that branch.

So un-aligned length was **never** a barrier, seating 21 was not safer than
tonight for this reason, and the sentence is a false statement about last night
dressed as a new hazard. ⚠️ It fails in the **safe** direction — more caution,
not less — but it is an unsourced claim in the one paragraph that has to be
exact, and it sits four lines from 0.3.1's ambiguous guard. **The alarm was
raised for a reason that does not hold and the guard beside it was written
ambiguously.** That pair is the finding.

🟢 The *other* barrier is real and was re-checked on the staged binary: the
eight section signatures `burn()` matches (`boot`, `sqsh`, `w6cp`, `jw6c`,
`cwmp`, `ksap`, `ALL1`, `ALL2`) have **zero occurrences** in all 8,192 bytes,
and so do `nfjrom` and `boot.img`.

#### 0.3.7 ⚠️ § 4's `LDR-26` row restates a claim `SPEC.md` struck through on 2026-08-29

**Card § 4**: *"a filename containing `nfjrom` or `boot.img` **forces
`0x80000000`** and auto-executes."* `SPEC.md:415` `LDR-26` corrected that on
2026-08-29: the two names share only `0x8040D390 = 1`; **only `boot.img` moves
the address**, and with `nfjrom` the loader jumps to the *configured* address —
so the accident **looks like a successful boot**. The correction runs toward
danger, and the card quotes the version before it. Harmless tonight (neither
string is in the binary) but it teaches the wrong hazard. Inherited verbatim
from seating 21's card:136.

#### 0.3.8 ⚠️ Three stale `file:line` citations

* § 6: `RB-1` cited as `PROGRESS.md:1701`. `RB-1` is at **:1700**; **:1701 is
  `LOOP-4b`**, which this card also cites by name in § 3.
* § 3: `docs/toolchain-comparison.md:200` *"records that as ✅/🔴/🔴"* — :200 is
  the `binsim` row; the ✅/🔴/🔴 row is **:203**.
* § 0: `plan/router-rebuild-plan.md:389` *"the row … marks as the only cell
  that can silently kill the project"* — :389 is a lead-in sentence; the row is
  **:393**.

All three were already wrong **at the freeze commit**, so none is drift.
🔴 `PROGRESS.md:1707` closed `CITE-1` in the sixty-sixth segment — **the same
segment that wrote this card**.

#### 0.3.9 ⚠️ Two pre-flight timestamps in § 3 are hand-arithmetic and both are wrong

Card: *"0 bytes at **12:33** … 0 bytes at **12:41**"*. 量, the artefacts'
own `.meta.json` (`$FWRE_WORK/rebuild/scratch-s22/`):
`preflight-off` `started_wallclock 2026-09-14T12:34:24`, `seconds 3.0`,
0 bytes; `preflight-esc` `12:43:00`, `esc 3.0 / seconds 8.0`, 0 bytes. One and
three minutes out. The substance is right; only the clock is. The artefacts are
outside the repository, so nothing here can check either number —
`rlxfw-requote-hazard`'s class, and `CAPD-1`'s one layer up.

#### 0.3.10 ⚠️ § 5.3's "each of the first four is a specific sentence in the log" miscounts

Four causes are listed; only the first two are sentences. 量,
`grep -n 'rlx_puts' tools/rlxprobe/probe6.c` → four conditional sentences at
397, 408, 432, 449; *a row is missing* and *the capture truncated* have none.

#### 0.3.11 ⚠️ `cardcheck numbers`'s `36 of 36` covers none of the twenty image-derived predictions

§ 5.2's and § 6's `pc`, `install.words`, `addr.d`, `addr.s`, `rows`, `words`,
`cell.d`, `cell.s` and the twelve site addresses are **prose table cells**, not
`cardnum` rows, so `cardcheck numbers` cannot see them — the same shape as
seating 20's `cnr_as_spec 1/1` passing `28 of 28`. 🟢 All twenty were
re-derived by hand from the ELF and the binary during this audit and **all
twenty are correct**; the finding is about what the green means, not about the
numbers.

### 0.3a 🟢 A pre-registered prediction: `rbcheck` can now read this block, and here is what it will print

`RB-1` was closed at the desk this segment (`tools/rbcheck.py`, `C40`–`C48`),
and the card's § 6 is right that **no `rbcheck` command is on the card** — it
could not have been, because the tool could not read a `524C5836` block when
the card froze. Running it off-card on `C1-P6rb` tonight is therefore a
**forward prediction by an instrument written without the data**, which is the
`C16`/`C39` shape `PROGRESS.md`'s `RB-1` row asks for. Fixing the tool
afterwards, against tonight's capture, would have made it a curve fit.

**Written before power. Every field below is derived from
`tools/rlxprobe/probe6.c` and from tables added today, and no probe6 block
exists anywhere.**

```
/usr/bin/python3 tools/rbcheck.py bench/2026-09-14b/C1-P6rb.log \
    --base 0x80A05000 --words 129 \
    --uart bench/2026-09-14b/C1-P6j.log --expect-magic 0x524C5836
```

| field | predicted | why |
|---|---|---|
| `magic` | `524C5836   probe6` | `probe6.c:70`; the name comes from the table added today, and before today this line read `unknown` |
| `progress` | `000000F1   P_SEALED   (sealed = 0xf1)` | `probe6.c:139`. Before today: *"no ladder for magic 524C5836"* |
| `seal word` | `w128 at 80A05200` | `RB_WORDS = 33 + 8×12 = 129` |
| `corrected` | `re-sum − 0x1` | **`restamp = 1`**, `P_SEALED − P_RESTORED` = `0xF1 − 0xF0`, derived from the ladder. The old fallback was `0x10`, which would have made the corrected sum wrong by 15 |
| `UART sum` | present, from a **`seal=`** line | `probe6.c:485` prints `field("seal", sum)`. The old pattern matched `sum=` only and channel (1) would read *absent* |
| `margin` | `8 word(s) past the block, 8 poison` | and **not** the three un-poisoned words 0.3.2 is about — `margin()` walks `range(129, 137)` |
| `RESULT` | `the block agrees on 3 channel(s)` | |

🔴 **Refutation condition.** Any one of: `magic … unknown`; a `no ladder`
failure; `corrected ≠ seal`; `UART sum absent`; a margin word that is not
poison. **A `restamp` of anything but 1 refutes the ladder read out of
`probe6.c` today**, and that is the row the whole fix turns on.

⚠️ **It is not a card cell and does not become one.** The three-way agreement
is done by hand tonight as the card specifies; this is a second instrument run
beside it, declared here before power. ⚠️ And it is only worth the sentence if
the block completes — a payload that stops inside the row loop prints
`P_ROWS+0xN (stopped in the row loop)`, which is also new today and is the
other thing the seating could show.

### 0.4 What the audit checked and found correct

Stated so the coverage is visible and so a defect the seating finds can be read
against it.

| | result |
|---|---|
| `cardcheck.py commands` | rc 0 — `6 command(s): 6 LOADER; declaration has 18 invocable name(s)` |
| `cardcheck.py numbers` | rc 0 — **36 of 36 re-derived** (and see 0.3.11 for what that does not cover) |
| `check-predictions.py` | **`0 of 7`**, rc **1** — the correct pre-power value. ⚠️ An operator reading only the exit code sees red |
| `spec-check.py` | rc 0 over 135 tracked `.md`, this card included |
| `capdate.py bench` | 32 dirs, 1,135 captures, 0 RED; `2026-09-14b` = `SKIP no captures` |
| staged payload | **exists**, 8,192 bytes, sha256 `030866f5…fac09728` — **byte-identical to the card's pin**, and to the surviving build copy. This is the class that cost seating 8 a power cycle |
| every predicted reply size | re-run through `tools/reply-size.py predict`: 1671 / 71 / 71 / 118, all matching |
| **Class 1 — terminators** | all seven cells carry `--seconds`; **no payload contains a `sleep`**, so seating 20's five-cell `--idle` trap does not apply; longest `--send` is 15 characters against `_check_send`'s 128 cliff; the `J` cell carries `--esc-after 60 --esc-period 0.002 --until '<RealTek>'`, byte-identical in shape to seating 21's `C1-P4j`/`C1-P5j`, which ended on `until` in 4.64 s and 3.47 s against a 120 s cap |
| **Class 3 — state** | power-on → ESC → prompt → `?` → pre-read → rescue → burn flag → upload → staged head → `J` → bite → ESC catch → prompt → read-back, in the order seating 21 proved. Every abort path in `probe6.c` (408/432/449) ends in `rlx_reset()`, so no refusal strands the board away from the prompt |
| **Class 4 — fence** | 7 entries, matching the 7 `--out` names in typed order; `cells-fence 7` re-derives; no cell outside the fence; directory name is today's |
| **Class 5 — instruments** | `tcpay.read_capture` normalises `\r\n`, tested on a synthesised device-shaped log — the CRLF trap that produced three false STOPs in seating 16 does not reach this card. No gate on a mark rather than a field |
| qemu leg | `tcpay verdict --arm qemu` → **12 of 12 LOCK**, the forced anti-control, 1,869 bytes |
| `tcpay verify` | 12 rows, every site exactly the declared shape, rc 0 |

### 0.5 What this audit did NOT check

* **Nothing in block 20.** That card has its own audit and its own corrections
  file. The one cross-card item found here is 0.3.3's ordering.
* **The physical path.** 量 17:07, the CP2102 is not in `usbipd`'s *Connected*
  list and `/dev/ttyUSB0` does not exist in WSL. That is expected — the board
  is not on the desk yet — but it means **no pre-flight capture was taken by
  this audit**, and the free board-off 3-second capture is still owed before
  power.
* **Anything that needs the device.** Every claim above is desk-side: a file on
  disk, a committed capture, or a tool's output.

---

## 1. What the seating did differently

Seating 22 ran on 2026-09-14, **one power cycle**, the only one budgeted. All
seven carded cells ran in the order § 11 types them, plus the off-card round
§ 10 declares. `check-predictions`: **7 of 7 came after the prediction, 0 did
not**. `capdate`: `bench/2026-09-14b`, 11 captures, all 2026-09-14 — the
directory name's prediction held.

### 1.1 The result

**12 of 12 rows read the verdict their `pad` column predicts**, `tcpay verdict
--arm device` rc 0, both controls held (`c_lock` LOCK, `c_open` OPEN):

| | rows |
|---|---|
| **LOCK** (5) | `c_lock`, `v1` (T4 `mips1`), `v4` (T1 `4181`), `v6` (T2 `4181`), `v8` (T3 `4181`) |
| **OPEN** (7) | `c_open`, `v2` (T4 `mips2`), `v3` (T4 `mips32`), `v5` (T1 `5281`), `v7` (T2 `5281`), `v9` (T3 `5281`), `v10` (T3 `4281`) |

The forced anti-control is the one that matters: the qemu leg read **12 of 12
LOCK**, and § 5.4 says a device run that reproduces it refutes the experiment.
It read 5/7. `trapped 0`, `cell.bad 0`, `split 0`, `ran 0000000c`.

⚠️ Read every `CPU-14` in the card and in `tcpay`'s output as **`CPU-58`**,
per 0.3.5. Nothing in the instrument was changed tonight and that decision is
unchanged.

**The report window is 1,808 bytes, exactly**, against the equality § 5.3
derives from the qemu capture's 1,869 minus 61. Four reply sizes were predicted
by `tools/reply-size.py` and all four hit: `71 / 71 / 118 / 1671`.

### 1.2 The two field predictions that were refuted, and they have one cause

`C1-P6j` read `install.changed=00000015` (21) against the card's `0000002b`
(43, `2c` admissible), and `restore.stillhdl=00000001` against `00000000`.

讀, `tools/rlxprobe/probe6.c:218-245` against `probe5.c:220-249`:

* `probe5` counts `ins_changed` at **both** vectors (two `ins_changed++` sites,
  :241 and :246), ceiling `2 × 22 = 44`. `probe6` counts **only**
  `VEC_GENERAL` (one site, :232), ceiling `22`. Both write both vectors; only
  the counting differs. **`43 = 44 − 1` and `21 = 22 − 1` are the same
  measurement.**
* `probe5:488-494` guards `res_stillhdl` with `saved_vec[...] != rlx_exc_entry[i]`
  and says why in a comment — *"A restore that put back a word which was
  already equal proves nothing."* `probe6:465-467` dropped the guard, so it also
  counts the word that was already equal.

So exactly one of `VEC_GENERAL`'s 22 words already held the handler's value:
invisible to `install.changed`, counted by `probe6`'s unguarded
`restore.stillhdl`. `restore.mismatch = 0` — the field that reports whether the
restore worked — reads 0.

🔴 **The card had been burned by this class one row earlier.** `install.words`
was predicted `00000019` on seating 21 by copying a **qemu** build's capture;
that row was fixed by deriving from the device ELF, and the row directly
beneath it was not.

### 1.3 The identity, and it was committed before the round that could refute it

`install.changed + restore.stillhdl == install.words` is in neither the payload
nor the card and holds only if 1.2 is right. `bench/2026-09-14b/PREDICT-X1-offcard.md`
states it with six refutation conditions and was committed in **`db5510b`,
21:07:44**, before any `X1-*` capture existed. **None of `X1-a`…`X1-f` fired.**

`X1-P6j2`'s report window is **byte-identical** to `C1-P6j`'s — 1,808 bytes,
sha256 `e6c5457c…` on both — and `X1-P6rb2` is byte-identical to `C1-P6rb`.
`21 + 1 == 22` on both runs.

🟢 **`X1-c`'s negative outcome is itself a reading**: run 1 was entered from a
**cold** prompt and run 2 from a **watchdog-reset** prompt, and
`install.changed` read 21 both times. The narrow claim is about the **count**,
not the content: 21 words differing from the handler is not 21 particular
values.

### 1.4 The off-card round carried the guard the card omitted

0.3.3's correction was executed: `X1-P6bf2` reads `DW 8040D4A0 1` between the
rescue and the upload, all four words `00000000`, and the script refuses to
upload otherwise. `X1-P6sh2` re-checks the staged head against the binary before
the jump. Both guards are hard gates in the runner, not judgement calls.

### 1.5 The corrections that acted, and what each was worth

| § | what it changed at the bench |
|---|---|
| 0.3.1 | the burn-flag guard was read **by address**. `C1-P6bf` and `X1-P6bf2` both returned four `00000000` words, so the ambiguity never bit — but it was read the safe way twice rather than by luck |
| 0.3.2 | `C1-P6rb` returned **140** words: seal at 128, poison at 129–136, and **137/138/139 reading `17755557 5DB73175 30555155`**. An operator checking *every word past the seal is `DEADC0DE`* sees a failure on a block that passed. `rbcheck`'s `margin()` walks `range(129, 137)` and reported `8 word(s) past the block, 8 poison` |
| 0.3.3 | the off-card round ran **before** block 20's first `looprun`, and carried a burn-flag read-back |
| 0.3.4 | not reached — the seating did not cross midnight |

### 1.6 The pre-registered `rbcheck` run, field by field

0.3a was written before power and no `probe6` block existed anywhere. Every row
hit, on both runs:

```
magic     524C5836   probe6
progress  000000F1   P_SEALED   (sealed = 0xf1)
seal word BEA03C14   w128 at 80A05200
re-sum    BEA03C15   naive, w0..w127
corrected BEA03C14   minus 0x1 = P_SEALED - P_RESTORED
UART sum  BEA03C14   channel (1), from a seal= line
margin    8 word(s) past the block, 8 poison
RESULT: the block agrees on 3 channel(s)
```

`restamp` is **1**, which is the row 0.3a says the whole fix turns on. All 48
`rbcheck` controls held on both runs.

### 1.7 Defects in this seating's own instruments, all mine

1. 🔴 **A `probe6*` filename glob missed the staged binary.** The pre-power
   check searched `-name 'probe6*'`, which does not match
   `rlxfw-probe6-20260914.bin`. Re-run with `*probe6*` it is present at the
   exact path § 1 names, sha256 `030866f5…fac09728`, mtime identical to the
   build tree's copy **to the nanosecond**. Seating 8 lost a power cycle to a
   card naming a file nobody had staged; this nearly reported the opposite.
2. 🔴 **A `.timing` parser read the columns in the wrong order.** The header
   says `# offset seconds`; the first draft read `(float, int)`. It raised
   rather than producing a number, which is the safe direction.
3. 🔴 **A map comparison selected cells by FILENAME.** It globbed
   `bench/*/C1-M1.log` and reported `bench/2026-09-09/C1-M1` as a differing
   flash map. That cell's `sent` field is `echo map 1 0` — the level-2 map of
   group 0, not a `map 0` at all. Re-selected by the `sent` field in each
   capture's own `.meta.json`, **nine `map 0` captures across five seatings and
   six days digest to one value**. `CLAUDE.md` records this class twice, both
   times in a runner; this is the third and it is in a comparison.

### 1.8 What did not move

**Zero flash-write commands, zero `FLR`, `AUTOBURN` read as four zero words
before each of the two uploads.** The bracket stands at **1,024 of 4,194,304 =
0.0244 %** and `FLS-26`'s ledger does not move. 🟢 An **off-card** `map 0`
(`bench/2026-09-14c/X7-M0`) is byte-identical to the eight before it — see
`bench/2026-09-14c/CORRECTIONS-block20.md` § 1, which owns that reading.
