# The development loop — what one iteration costs

## 0. What this file owns

`R4-0`. **The cost of one `edit → result` iteration, stage by stage, with
machine time and human time in separate columns.** `SPEC.md` indexes the
numbers; this file owns them and owns the method that produced them.

It does not own: the boot itself (`SPEC.md` `FW-27`/`FW-32`, `notes/` boot
ladder), the build's reproducibility (`notes/reproducible-build.md`), or the
scripted reset that `R4-1`/`R4-2` will measure.

**§1–§3 were written and committed BEFORE any measurement in this file was
taken.** That is not a claim about my discipline; it is checkable —
`git log --follow notes/dev-loop.md` shows a first commit holding the
predictions and no numbers, and a later one holding the numbers. This
project's `check-predictions.py` proves the same ordering for bench captures
by mtime and cannot be used here, because the quantities are desk timings and
not captures.

---

## 1. The loop as it exists on 2026-09-01

### 1.1 The seven stages

An `R5` iteration — the loop this gate exists to make fast — is a change to a
**kernel** source file. That is the loop measured here. A userspace-only
iteration is a different loop and is noted where it differs.

| # | stage | performed by | what an instrument can see |
|---|---|---|---|
| S1 | edit a kernel source file | me, at the desk | nothing. No instrument in this repository times an edit |
| S2 | stage a tree and build it — `tools/rlxfw-kbuild.sh` | machine | its own stdout, one line per phase |
| S3 | assemble the image — `tools/rtkimage.py build` | machine | its own stdout |
| S4 | power the board and catch the ESC window to `<RealTek>` | operator, physically | the capture that was opened before power |
| S5 | TFTP the image to `0x80500000` | machine | `bench/*/*-put.json`, field `seconds` |
| S6 | `J 80500000` | machine, one line typed | the capture |
| S7 | first useful output — the boot text and a shell prompt | machine | `.timing` against `.log` |
| S8 | the result reaches the desk — paste-back and read | operator + me | the gap between one capture ending and the next starting |

**S8 is a stage and it is the one the plan's `< 90 s` never named.** It is in
the list because the loop is not closed until the person who made the edit
knows what the board printed.

### 1.2 Two definitions of "the loop", and they do not give the same number

Written here before either is measured, so that the answer cannot be chosen
after the fact:

* **the machine pipeline** — S2 + S3 + S5 + S7. Every second of it is a
  machine working and a human waiting. This is the quantity `< 90 s` reads
  most naturally as being about.
* **the turnaround** — S1 through S8 as actually served, including the
  operator's hands and the paste-back. This is the quantity that decides how
  many `R5` iterations fit in a day.

A gate that meets the first and not the second has bought nothing. `R4`'s DoD
`D4` names one number and does not say which, and that is a defect in `D4`
found before it was measured against.

### 1.3 What is not in the loop, deliberately

The **wait for a seating to be scheduled** — the loop's largest term by two
orders of magnitude, because the operator and the board are not at the desk
continuously. It is excluded because no engineering change to this repository
moves it, and including it would make every other number invisible. It is
named here so that its exclusion is a decision and not an oversight.

---

## 2. Predictions, written before the measurement

Each has a two-sided refutation condition. A prediction that can only come out
one way is not a prediction.

| id | claim | refuted by |
|---|---|---|
| **P1** | the build total (`rlxfw-kbuild.sh`, `-j4`, today's recipe: `--marks`, declared cflags, declared stamp) is **45–60 s** | a total below 45 s or above 60 s |
| **P2** | the 480 MB stage copy is **5–15 s** and **under 30 %** of the build total | outside that range, or 30 % or more |
| **P3** | `-j8` cuts the build total by **15–32 %** against `-j4` | `-j8` not faster, or faster by more than 40 % |
| **P4** | image assembly (`rtkimage.py build`) is **5–25 s** | outside that range |
| **P5** | the machine pipeline at `-j4` totals **65–95 s** — so `D4`'s 90 s is borderline, not comfortable | below 65 s or above 95 s |
| **P6a** | the gaps inside a seating are **bimodal** — a scripted mode of a few seconds and a human mode of minutes — and the human mode holds **more than 70 %** of the seating's dead time in **fewer than 30 %** of the gaps | a unimodal distribution, taken as max ÷ median below 10 |
| **P6b** | a seating's dead time is **more than 2×** the sum of its capture durations | 2× or less |
| **P7** | NFS root is **not** on this gate's critical path: the upload it removes is **under 3 %** of the machine total, and **0 %** for a kernel change | the upload is more than 10 % of the machine total |
| **P8** | the step list's own stated risk holds — the build is **more than 60 %** of the machine pipeline | 50 % or less |

**P1's basis**, so the reader can see it is arithmetic and not a feeling:
`r3-9/determinism.log` holds `rep4` at 49 s and `rep8` at 40 s, both `-j4`/`-j8`
of the same `.config`; `r3-9/driver.log` holds `quietmc` at 51 s (`-j4`,
`--marks`) and `loudmc` at 61 s; `build2.log` holds `quietmc` at 36 s and
`loudmc` at 51 s, both `-j8` with `-fno-if-conversion`. Six cells, two `-j`
settings, and none of them decomposed into phases — which is the whole reason
this step exists.

---

## 3. Method

**The desk half is run today; the bench half is read out of captures already on
disk.** A stage that neither can reach is recorded **unmeasured**, never
estimated — the step list says so and this is where it binds.

* **S2, S3** — run on this host, `n` ≥ 2 per configuration, each phase boundary
  taken from the driver's own stdout with a timestamp attached per line as it
  arrives. The driver is not modified: it already prints one line per phase,
  and timing its output is a measurement of the tool as it is rather than of a
  tool changed to be measurable.
* **S4, S5, S6, S7** — read out of `bench/`. These are 量 on the device, with
  the seating and the capture named for every number. They are not re-run:
  re-running them costs the most expensive unit this project has.
* **S8** — derived by `tools/looptime.py` from every capture's
  `.meta.json`: `started_wallclock` and `duration_s` give, for consecutive
  captures, the dead time between them. **Ordered by wall clock, not by
  filename**, because the two differ.

### 3.1 What the S8 instrument cannot see

Named before it is run, because a gap is a residual and a residual absorbs
everything nobody named:

1. it cannot separate *the operator reading and pasting* from *me writing the
   next command*; it measures their sum;
2. a gap that spans a break — the operator leaving the bench — is
   indistinguishable from a long round trip, and will be reported as an
   outlier rather than silently averaged in;
3. it sees only captures. A command that produced no capture, and the whole of
   S4, are outside it.

---

## 4. The desk half, measured 2026-09-01

Host: 8 cores, WSL2 Ubuntu 24.04, `/usr/bin/python3` 3.12.3. Recipe: `--config
r3-4/out/quietm.config-installed --initramfs r3-9/…/rlxfw-initramfs.spec
--marks`, `CFLAGS_KERNEL=-fno-if-conversion` from `config/rlxfw-cflags`, stamp
`1788220800`, recipe id `d31f60bd`, 16 mark rows, 2 host-compat patches. Raw
log: `$FWRE_WORK/rebuild/r4-0/desk.log`.

⚠️ **Both of the last two are readings dated 2026-09-01 and neither is current.**
`R4-3` added `host-compat/0003` and `0004` on 2026-09-02, so a build from this
repository now applies **4** patches and the recipe id is **`b1434383`**. The
numbers above are not corrected, because they describe what THIS measurement
ran with; a recipe id that moved is exactly what `ID0` exists to report.

Every boundary below is the driver's own stdout, timestamped as each line
arrived. The driver was not modified.

| cell | `-j` | stage copy | declarations | `oldconfig` | `make` | total |
|---|---:|---:|---:|---:|---:|---:|
| `j4a` | 4 | **6.634** cold | 0.169 | 8.367 | 33.445 | **49.538** |
| `j8a` | 8 | 1.356 | 0.175 | 7.754 | 34.456 | **44.754** |
| `j4b` | 4 | 2.132 | 0.260 | 10.380 | 43.502 | **58.045** |
| `j8b` | 8 | 1.474 | 0.188 | 8.192 | 25.649 | **36.543** |

*`total` is measured outside the driver and exceeds the sum of the phases by
0.7–0.9 s, which is `bash` starting and the driver reading its two declaration
files before it prints anything. Named rather than distributed.*

**All four produced `vmlinux` sha256 `6268def94281659a`** — byte-identical at
two different `-j` settings, which is a fifth and sixth replication of `P4a`'s
Level-1 claim and the first with the declared stamp and `ID0` in place.

Three more machine stages, same session:

| stage | n | measured |
|---|---:|---|
| `rtkimage.py build` (S3) | 2 | **3.551 / 4.131 s** |
| `mkinitramfs build` (userspace iterations only) | 1 | **0.159 s** |
| `vendor-tripwire.sh -- true`, the envelope every `run` pays | 3 | **2.583 / 2.613 / 2.772 s** |

The tripwire is paid twice per build — once around `oldconfig`, once around
`make` — so **about 5.2 s of every build total is the tripwire**, and the
`oldconfig` and `make` columns above each contain one of them.

### 4.1 🔴 The 480 MB re-stage costs 1.4–2.1 s, and this project has been treating it as the reason the loop is slow

This project has treated the re-stage as the loop's structural
cost. ⚠️ **The sentence that says so is in a gitignored study file, so a public
reader cannot check it** — what a public reader can check is
`tools/rlxfw-kbuild.sh`'s own header, which explains at length why the tree is
re-staged every time and **never says what it costs**. That absence is the
gap this measurement fills.
量: **1.356 / 1.474 / 2.132 s warm**, which is **3–4 %** of the build. `j4a`'s
6.634 s is the one cold-cache reading — WSL had been up 27 seconds — and it is
the only value that lands in `P2`'s predicted 5–15 s band.

**`P2` is refuted.** The re-stage is not the cost. It is also the only thing
`--keep` actually skips.

---

## 5. 🔴 `--keep` cannot buy what `R4-3` was braced to fight over, and the reason is that this tree has no incremental build at all

The gate's stop-loss says `--keep` may not be turned on to hit a number. It was
written expecting a large speedup with a large reproducibility cost. Both
halves are now measured and both are small.

| run | elapsed | `make` phase | `CC` lines |
|---|---:|---:|---:|
| `j4a`, fresh stage | 49.538 | 33.445 | 599 |
| `j4a --keep`, **nothing changed** | 39.638 | 33.868 | 599 |
| `j4a --keep`, one `.c` touched | 38.618 | 33.871 | 599 |
| bare `make vmlinux`, nothing touched, no `.config` re-install | 30.881 | — | 599 |
| the same, immediately again | 30.738 | — | 599 |
| the same after `cp .config` | 34.403 | — | 599 |

**A `make vmlinux` with nothing touched recompiles all 599 objects, twice in a
row.** So `--keep` skips the stage copy and the patch and mark steps and
nothing else: **1.5–2.4 s, which is 3–5 %** — 2.4/49.5 = 4.8 % and 1.5/58.0 = 2.6 %.

And it cannot be used with today's recipe at all. `--keep --marks` **refuses**,
in 0.236 s, before any copy:

```
j4a: rlxfw-marks apply FAILED
rlxfw-marks: MK: obj-y += rlxfw_mark.o is already in
  linux-2.6.30/arch/rlx/kernel/Makefile. This tree is not clean; re-stage it
```

讀 `rlxfw-kbuild.sh` before running it: the marks block is guarded by `$MARKS`
and not by `$KEEP`. The refusal is the mark tool's once-only anchor rule doing
exactly what it exists for.

### 5.1 🟢 And `P4a`'s `L2-6` closes, at two bytes

`notes/reproducible-build.md` `L2-6` carried *"unmeasured, and bounded"* for
`.version`. 量: a fresh cell links once and `.version` reads **1**; the same
tree after two `--keep` builds reads **3**. `repdiff` between the two images:

```
differing bytes: 2 of 3968240  (0.000050 %)
  0x2701fe  .rodata  linux_banner+0x3a   #1 -> #3
  0x299438  .data    init_uts_ns+0xc8    #1 -> #3
```

So `--keep` does break byte-identity, it breaks it in exactly two bytes, and
the mechanism is a monotonic link counter no third party can reproduce without
knowing how many times the tree was linked. 🔄 **2026-09-02: two bytes is the
cost while the counter keeps its width.** 量, `#9` against `#10`: **56** bytes,
because the decimal rendering grows a digit and shifts the rest of
`UTS_VERSION` in both of its copies. `notes/incremental-build.md` §5.5. **The claim is unchanged; what
changed is that its cost is a number instead of a worry.**

### 5.2 What actually forces the rebuild, and it is not the `.config`

量, a no-op `make init/main.o` rewrites eight files. Two of them are kernel
headers, and both come back with the same digest:

| file | sha256 pass 1 | sha256 pass 2 | mtime |
|---|---|---|---|
| `include/asm-rlx/asm-offsets.h` | `f7575686e3719433` | `f7575686e3719433` | moves |
| `include/linux/bounds.h` | `bd0652b2b7b1a641` | `bd0652b2b7b1a641` | moves |

**Byte-identical content, new mtime, every time.** 讀 the dependency lists
kbuild itself wrote: `linux/bounds.h` is named in **566 of 731** `.*.o.cmd`
files and `asm-offsets.h` in **17**; **580 of 731** name at least one. The two
files that always move are prerequisites of four objects in five.

讀 this tree's top-level `Kbuild`:

```
always  := $(bounds-file)
kernel/bounds.s: kernel/bounds.c FORCE
        $(call if_changed_dep,cc_s_c)
$(obj)/$(bounds-file): kernel/bounds.s Kbuild
        $(call cmd,bounds)          # cmd, not filechk and not if_changed
```

`$(call cmd,…)` is an unconditional redirect, and the comment two lines above
it in the vendor's own file says why it is there: *"We use internal kbuild
rules to avoid the 'is up to date' message from make."*

⚠️ **Whether that rule is Realtek's or mainline 2.6.30's is undetermined
here.** The four GPL drops hold exactly one `linux-2.6.30` between them and no
mainline tree is on disk, so there is nothing to compare against. One mainline
2.6.30 `Kbuild` settles it.

🟢 **This is `R4-3`'s target and it is now a named one**: a `config/host-compat/`
patch giving those two rules a content check would turn a 31 s full rebuild
into a link. It is not attempted here, and the saving is **not estimated** —
it is whatever a real incremental link costs on this tree, which nobody has
measured because none has ever completed.

🔴 **2026-09-02 (`R4-3`): the measurement above stands and the arrow drawn from
it was wrong.** The two headers *are* rewritten every build with identical
content — that is reproduced — but they are **not** what forces the 599-object
rebuild. 量: with a `filechk` patch applied to a staged tree, both mtimes stop
moving and the rebuild is **still 599**. kbuild's own `V=2` reason macro says
`597 - due to command line change`; the cause is `arg-check` comparing a
`.cmd` line that make **truncates at a bare `#`** when it loads it, 1,131 bytes
on disk against 1,023 in memory. The header rewrite was downstream of the same
cause: once `arg-check` works, `kernel/bounds.s` is no longer regenerated and
the rule never runs. `notes/incremental-build.md` §5 owns the whole of it, and
§5.7 owns the one case where the `filechk` patch is still worth having
(573 `CC` → 3). ⚠️ **`bounds.h` in 566 of 731 and `580 of 731` above are still
correct counts of the dependency graph**; what changed is what they explain.

---

## 6. The bench half, read out of the captures

Nothing was re-run; a power cycle is the most expensive unit this project has.
Every number names its capture. Produced by `tools/looptime.py`, which arrived
with this step.

### 6.1 S4 — power to a typeable prompt

`looptime to-prompt` splits the capture at the first byte the board drove. The
capture is opened before the power goes on, so *open to first byte* is the
operator's hand and *first byte to `<RealTek>`* is the board.

| | n | measured |
|---|---:|---|
| open to first byte (the operator) | 14 | **1.683 – 36.399 s** |
| first byte to `<RealTek>` (the board) | 14 | **2.176 – 2.636 s**, median **2.308 s** |

Three captures are excluded and the reason is in the numbers: the `A-catch` of
`2026-08-24d`, `2026-08-24f` and `2026-08-30b` each show *open to first byte*
under 0.02 s, so their first byte is not the line coming up and their second
interval is not the board booting. `2026-08-24e`'s `A-catch` never reaches a
prompt at all — that is the seating that stopped.

⚠️ **The 14 fall in two groups — NINE at 2.176–2.417 and FIVE at
2.582–2.636**, separated by 0.165 s with nothing between them, and 量 the
metadata: the split follows neither the ESC period (`0.002` and `0.02` both
appear in each group) nor the tool version. The full spread is 0.460 s, 21 %
of the smallest value, where `CLK-15`'s cold-versus-warm effect measured
within one power cycle is +4.5 ms and +14.5 ms — an order of magnitude
smaller. **Unexplained, and recorded as a cell rather than a footnote.**
*(This read "eight … and six … a 300 ms separation" until the numbers were
re-derived from the fourteen values: it is nine and five, and the separation
between the groups is 165 ms.)*

### 6.2 S5, S7 — upload and boot

| | n | measured | source |
|---|---:|---|---|
| TFTP put, about 1 MB | 4 | **1.545 / 1.553 / 1.595 / 1.639 s** | `bench/*/[LVWX]1-put.json` |
| TFTP put, 19–29 KB payload | 2 | 0.040 / 0.058 s | `H1a-put.json`, `Q0-put.json` |
| `J` to shell prompt, `quietm` | 1 | **7.260 s** | `SPEC.md` `FW-32` |

### 6.3 The seating, end to end

| seating | captures | span | instrument held | dead | median gap | largest gap |
|---|---:|---:|---:|---:|---:|---:|
| `2026-08-24b` | 33 | 4868.1 | 200.8 | 4667.3 (95.9 %) | 107.9 | 981.9 |
| `2026-08-24c` | 46 | 2841.1 | 475.2 | 2365.8 (83.3 %) | 0.9 | 319.9 |
| `2026-08-25` | 26 | 3084.1 | 552.1 | 2532.0 (82.1 %) | 17.9 | 988.9 |
| `2026-08-30` | 13 | 842.1 | 397.1 | 445.0 (52.8 %) | 7.4 | 140.9 |
| `2026-08-30b` | 24 | 607.1 | 369.1 | 238.0 (39.2 %) | 0.9 | 67.9 |
| `2026-08-30c` | 21 | 1110.1 | 238.7 | 871.4 (78.5 %) | 12.4 | 580.9 |
| `2026-08-31` | 35 | 1149.1 | 598.2 | 550.9 (47.9 %) | 0.9 | 103.9 |
| `2026-08-31b` | 27 | 900.1 | 383.5 | 516.6 (57.4 %) | 0.4 | 229.9 |
| `2026-08-31c` | 49 | 4963.1 | 733.4 | 4229.7 (85.2 %) | 6.9 | 2307.9 |

Two directories refuse rather than report: `bench/2026-08-23` holds four `.log`
files and no `.meta.json` at all — first silicon, before the format — and
`bench/2026-08-26` holds a prediction block and no capture, the seating that
never happened.

🔴 **`P6b` is refuted, and by more than a margin.** It predicted dead time
above 2× the instrument time. Six of fourteen seatings are above it and eight
are below, including three of the last four. **The seatings got faster**: the
first carded one is 95.9 % dead and the three most recent are 39–57 %.

🔴 **`P6a` is refuted, and how it was written is the more useful finding.** Its
claim — a bimodal distribution with more than 70 % of the dead time in fewer
than 30 % of the gaps — holds in three of fourteen seatings. Its stated
refutation condition, *max ÷ median below 10*, fires in **one**. **So the claim
can fail while the condition written to refute it does not.** A refutation
condition has to be the negation of the claim; this one was a different
statement about the same data, and it would have let a false prediction stand.

### 6.4 🔴 The instrument column is not productive time, and reading it as such would have inverted the conclusion

A capture holds the port for the `--seconds` the card asked for, not for as
long as the board needed. `W-3`, `X-3` and `V-3` each hold **45.1 s** for a
boot that reaches a shell in **7.260 s**. So **37.8 s of every image iteration
is a timeout somebody typed**, and a seating with a high *instrument* share is
not an efficient seating — it is one whose card asked for longer holds.

`console-capture.py` already has `--idle`. No bench card uses it for the boot
capture. That is `R4-3`'s cheapest single item.

#### 🟢 2026-09-01, seating 9: a card used it, and the threshold had to be measured

`bench/2026-09-01/PREDICTIONS-B7-block6.md` is the first card in this project
whose every row carries `--idle`. `T-3` — the same `J 80500000` boot as `V-3`,
`W-3` and `X-3` — held **15.2 s** instead of 45.1 s and came back
**byte-identical** to `X-3.log`, all 849 bytes. So `--idle` does not truncate
the boot text, which is the thing this section said the first seating using it
would have to show.

🔴 **But the number that was obvious would have destroyed the capture.** 量 at
the desk, before power, over every committed capture that carries a boot:

| population | n | largest silence inside the wanted region |
|---|---:|---:|
| cold power-up to `<RealTek>` | 14 | 1.644 s, at byte ≈118, right after the `---RealTek(RTL8196E)` banner |
| watchdog-reset boot to `<RealTek>` | 5 | 1.565 s, the same gap |
| **`quietm`/`quietmc` to a shell** | 3 | 🔴 **4.576 s, at byte 350 of 849** |
| a one-line `DW` reply | 3 | 0.015 s |

An `--idle 3` — the value the first two rows justify — cuts `T-3` at byte 350
and loses **497 of its 849 bytes**, and the log then looks like a boot that
stopped rather than an instrument that gave up. **The threshold is a property
of the cell shape, not of the tool**: this card used 2 / 3 / 8 / 3, each with a
`--seconds` ceiling behind it, because `--idle` cannot end a capture that is
still receiving bytes and the one failure a seating can actually produce — a
missed ESC window, after which the vendor firmware talks for two minutes — is
exactly that case.

🔴 **And the 37.8 s does not all come back.** `V-3`, `W-3` and `X-3` stream no
ESC at all (`esc: {}` in all three `.meta.json`), which is why `--idle` fixes
them outright. On every cell that has to catch an ESC window the hold is
dominated by `--esc-after`, a fixed loop that runs to its deadline whatever the
board does. Seating 9's twenty reset cells went from a 45 s recipe to **13.1 s**
each — real, and smaller than this section implied.

### 6.5 🔴 `CLK-18`'s two groups were this file's instrument, not the board

`SPEC.md` `CLK-18` is computed by `tools/looptime.py to-prompt`, and §6.1 above
is its owner. 量 2026-09-01, seating 9, at the desk:

**Six of fifteen cold captures open on a byte the board did not send.** At
power-on the serial line is not yet driven and the receiver samples it once:
`bench/2026-08-24c/A-catch` starts `FF`, `2026-08-25` and `2026-08-30c/V-A`
start `00`, `2026-08-25b` starts `00 FC`, `2026-08-31/W-A` and
`2026-08-31c/K-A` start `00 FF`. That byte precedes the board's own `Booting`
by **0.321–0.350 s**; the other nine captures start within 0.002 s of it.

`looptime.to_prompt` set `first_byte = rows[0][1]` — the first read, whatever
it carried — so those six were measured from the line moving and the other nine
from the CPU printing.

| origin | n | min | max | range | largest gap |
|---|---:|---:|---:|---:|---:|
| `rows[0]` → `<RealTek>` | 15 | 2.171 | 2.636 | 0.465 | **0.165** |
| `Booting` → `<RealTek>` | 15 | 2.095 | 2.315 | **0.220** | **0.075** |

🟢 **The second source was already in this repository and already right.**
`tools/boot-timeline.py`'s `artifact` column is defined as *byte 0 → the first
byte of the device's own `\r\nBooting`*, and its header has recorded since
2026-08-25 that the prefix is not always one byte. Over the same six captures
it reads **0.3203 .. 0.3495, mean 0.3418, n=6** — the same interval `looptime`
was silently including.

**So two committed instruments read one artefact and disagreed, and `SPEC.md`
cited the one without the model.** `looptime` now reports both and reports the
CPU-relative one as **absent** rather than defaulted when `Booting` is not
there (`P7`, `N11`, `N10`, `A2`; 22 → 26 controls, mutants 20/20). The class —
nothing checks that two tools agree about one file — is `TOOL-1`.

⚠️ **An independent population agrees with the corrected reading.** Seating 9's
twenty-one warm boots, all inside one power cycle, are 2.104–2.365 s from
`Booting` with a largest gap of 0.053 s: unimodal, and overlapping the cold
range, which is what `CLK-15`'s measured cold/warm difference of +4.5 and
+14.5 ms predicts.

---

## 7. The two totals, against the two numbers already in `SPEC.md`

The step's DoD says the sum is **compared** against the published 49 s and
7.260 s rather than replacing them, and it does not replace them: 49 s is
`rep4`'s cell duration and is still true of `rep4`; `FW-32`'s 7.260 s is used
here as a term.

**The machine pipeline, `-j4`, `quietm`:**

| stage | seconds |
|---|---|
| S2 stage + build | 38 – 58 |
| S3 image assembly | 3.6 – 4.1 |
| S5 TFTP upload | 1.5 – 1.6 |
| S7 `J` to shell | 7.260 |
| **total** | **50.4 – 71.1 s** |

The bounds are summed from the **unrounded** values — 38 + 3.551 + 1.545 + 7.260 = 50.356 and 58.045 + 4.131 + 1.639 + 7.260 = 71.075 — because summing the rounded column above would give 71.0, and rounding then adding is not the same operation as adding then rounding.

Using only the two cells run under the prediction, 61.9 – 71.1 s; widening to
every `-j4` cell built with today's recipe — those two plus `p4a1` at 44 s and
`p4a2` at 38 s, read out of `p4a-run1.log` **after** §2 was committed — gives
the 50.4 s floor.

🟢 **`D4`'s 90 s is met by the machine pipeline, with 19–40 s of margin.** The
gate's second stop-loss clause — *if `R4-0` shows the machine stages alone
exceed 90 s* — does not fire, and `D4` does not need renegotiating.

🔴 **And the margin is not comfort.** The build is **75–82 %** of that total,
it is a full 599-object rebuild every time (§5.2), and this host's run-to-run
spread on one configuration is **38–58 s, a factor of 1.5**. Any change worth
less than about 20 s cannot be shown on this machine with n = 2 — which is why
`-j8` is recorded below as *not established* rather than as a 24 % saving.

**The turnaround** is a different quantity and S8 dominates it. The most recent
full-image seating, `bench/2026-08-31`, spans **1149 s** for one upload, one
boot and twelve userspace commands, of which the machine pipeline is about
50–71 s. **The loop as served is 16–23× the loop as computed** — 1149.1 ÷ 71.075 = 16.2 and 1149.1 ÷ 50.356 = 22.8. A single ratio would be one number dividing a range 1.5× wide, and would hide the spread that §7 has just finished making the point of.

---

## 8. Predictions, scored

| id | claim | verdict |
|---|---|---|
| P1 | build 45–60 s at `-j4` | **holds** on the two cells run under it (49.5, 58.0); **fails** when widened to the four `-j4` cells of this recipe (38, 44, 49.5, 58.0). The band was too narrow and the population was fixed before it was known |
| P2 | stage copy 5–15 s and under 30 % | 🔴 **refuted**. 1.4–2.1 s warm, 3–4 % |
| P3 | `-j8` cuts 15–32 % | ⚠️ **not established**. The medians differ by 24 %, and the within-configuration spread (1.5×) is larger than the effect. `j8a`'s `make` phase is *longer* than `j4a`'s |
| P4 | image assembly 5–25 s | 🔴 **refuted**. 3.55 / 4.13 s |
| P5 | machine pipeline 65–95 s | **holds** at the median, 66.5 s; its floor is exceeded by the wider population |
| P6a | bimodal gaps, over 70 % of dead time in under 30 % of gaps | 🔴 **refuted** — and its refutation condition did not fire, which is a defect in the prediction rather than in the data |
| P6b | dead time over 2× instrument time | 🔴 **refuted**. 6 of 14 seatings |
| P7 | the upload is under 3 % of the machine total, 0 % for a kernel change | **holds** on its refutation condition, over 10 %; the point value is 2.2–3.3 % |
| P8 | the build is more than 60 % of the machine pipeline | **holds**. 75–82 % — the step list's own stated risk, confirmed |

Three held, four refuted, one not established, one split.

---

## 9. What this decides, and what it leaves open

**Decided:**

1. 🟢 **NFS root leaves this gate.** It removes the TFTP upload, which is
   **2.2–3.3 %** of the machine pipeline, and it removes **none** of it for a
   kernel change — and `R5`, the gate `R4` exists to serve, is six kernel
   drivers. `PROGRESS.md`'s `R4` section asked for this decision to be visible
   if it went this way. It went this way.
2. 🟢 **`D4` stands as written.** 50–71 s against 90 s.
3. 🟢 **The `--keep` tension closes without turning `--keep` on.** It buys
   3–5 %, refuses to run with `--marks` at all, and its reproducibility
   cost is exactly two bytes. `R4-3` inherits §5.2 instead, which is a bigger
   prize and does not touch `P4a`'s claim.

**Left open, each with the experiment that would close it:**

* 🟢 ~~the full rebuild, §5.2. One `config/host-compat/` patch; the saving is
  unmeasured, because no incremental link has ever completed on this tree.~~
  **CLOSED 2026-09-02, `notes/incremental-build.md`, and the diagnosis in §5.2
  was wrong.** It took two patches, and the one that mattered was not the one
  this bullet names: a no-op `make vmlinux` goes **599 `CC` / 28.0–32.1 s → 2
  `CC` / 6.9–10.3 s**. 🔴 **And it buys exactly zero on this loop's default
  path**, because a fresh stage has no object files to keep.
* 🟢 ~~whether the `cmd,bounds` rule is Realtek's or mainline's. One mainline
  2.6.30 `Kbuild`.~~ **CLOSED 2026-09-02: mainline's, byte-identical** —
  `Kbuild` is sha256 `c1065aab0da23578` in mainline v2.6.30 and in all three
  `linux-2.6.30` trees on disk. So are `scripts/Kbuild.include` and
  `kernel/bounds.c`. The control is the top-level `Makefile`, which the same
  comparison reports as 159 changed lines.
* ⚠️ the 300 ms two-group split in power-to-prompt, §6.1. Apply `C-8`'s
  cold-versus-warm discriminator to the fourteen captures.
* ⚠️ the capture holds, §6.4. `--idle` on the boot capture; one seating to
  confirm it does not truncate the boot text.
* 🔴 `started_wallclock` is written by `strftime` and truncated to the second
  while `duration_s` keeps microseconds. Every gap in §6.3 carries ±1 s, and
  two captures taken in the same second cannot be ordered by it — which
  matters to `check-predictions.py`, whose own docstring proposes that field
  as the clone-stable ordering signal it does not yet have.

**Not established and deliberately not chased:** `-j8`. Four of four `-j8`
cells across three sessions sit below all four `-j4` cells, which is
suggestive; today's data cannot separate them, and a gate that claimed 24 % on
that evidence would be reporting the host's variance as a result.
