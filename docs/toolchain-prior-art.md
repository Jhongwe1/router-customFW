# What this repository already holds about the toolchains

**`R1-pub-0b`, desk, 2026-09-12. No power, no `R2c` column built, no new
toolchain reading taken before this file was committed.**

`R1-pub-0` froze the ISA axis's prior art on the same calendar day. This is the
other axis. `R2c` is *three toolchains, the same silicon measurements, three
columns*, and the gate's step table caps it at **2 段** with a stop-loss that
says the third column gets dropped if it runs over. Neither the cap nor the
stop-loss means anything until somebody says what is already here — so this
file freezes, before `R1-pub-6` starts, every toolchain finding this repository
already holds, with the route its evidence came by, the `SPEC.md` mark it
carries, and **whether it is a statement about a toolchain or about the die**.

Its ordering is checkable the way `docs/blind-write-ledger.md` § 1 is: `git
log` shows it committed before `R1-pub-6`. Its contents are checkable a
different way — `tools/tccensus.py check` derives both populations from
instruments and joins them against `tools/toolchain-census.tsv` in both
directions, and the four tables below are generated blocks that the same
command re-derives and compares.

---

## 0. What this claims, and the four things it does not

**Claims.** For every toolchain finding this repository has written down, and
for every toolchain release it can name: which of four evidence routes it
already has, whether a public source states the same thing, and what is left
for `R2c` to do.

🔴 **Does not claim ① — that it is a record of what has been measured.** It is
a record of what has been **written down**. That bound is the ISA census's too,
and here it is worse rather than the same, because of § 1: on the ISA axis the
*population* came from code, so a row could exist with nothing written about
it. Here the population **is** the writing.

🔴 **Does not claim ② — that the ⓟ column is complete.** It is a **lower
bound**, adjudicated only where a concrete public source was read during this
segment. A row with `p` clear means *nobody looked*, not *nothing is public*.
That distinction is the whole reason the column exists at all; see § 2.1.

🔴 **Does not claim ③ — that a route-① row is finished.** Route ① here means
*something was executed at the desk*. It is the strongest route on this axis
and it costs no power, which is exactly why it is so well populated and why
§ 6's answer is uncomfortable.

⚠️ **Does not claim ④ — anything about which toolchain rlxfw should use.**
That is `TC-05`, half of which is still blank, and it is a decision rather than
a reading. This file records what is known, not what follows from it.

---

## 1. The population, and why one instrument is not two

`R1-pub-0` argued at length that a *derived* population beats a *chosen* one,
and took the union of two instruments because neither covered the other. This
axis cannot copy that argument, and saying so is the first honest thing in the
file.

| | instrument | what it contributes | atomic unit |
|---|---|---|---|
| `r2c` | `SPEC.md` through `tools/spec-check.py`'s own parser | every id in an id column whose first token starts `TC-` — **50** in § 14 and one, `TC-h`, that exists only in § 17's blank list. ⚠️ It read **48 and one at the freeze**; § 9's own run added `TC-48` and `TC-49`, which is the derivation doing its job rather than the file drifting | one recorded finding |
| `r2t` | `config/rlxfw-sdk.config`'s `CONFIG_RSDK_*` lines | the only committed **closed set** of the releases on hand — **3**, selected or not | one toolchain release |

🔴 **`r2c`'s instrument is this repository's own record, and that is
circular in a way the ISA census's was not.** `hazlint` and `isa-probe.sh` are
code: they enumerate what an instrument can *ask*, independently of what anyone
wrote down. `SPEC.md` is the record. A population derived from it cannot see a
toolchain fact this project measured and never filed, and it cannot see one
filed under a different id space.

Both of those failures are real and both are in the table:

* **filed elsewhere** — `CPU-16`'s last third is a **three-toolchain × four
  `-march` codegen sweep** (~~1.3.6 emits zero `lwl`, 1.5.5 emits four,
  `-march` moves neither~~ 🔄 **2026-09-13: the two generations' raw drivers
  both emit zero and the asymmetry is the 1.5.5 wrapper injecting `-fuse-uls`
  — `SPEC.md` `CPU-16`, `TC-50`**). It is a toolchain measurement wearing a
  `CPU-*` id, and no `TC-*` derivation can reach it. It is in the table as a
  `declared` row — and 🔴 **the declared row's note is regenerated from the TSV
  while this sentence is not, which is why the correction had to be made twice
  in one file.**
* **not filed at all** — the public Lexra binutils and gcc patches are
  described in `SOURCES.json` and owned by no `TC-*` row, and
  `notes/rebuild-vs-shipped.md` § 4's tenth rebuild cell is owned by none
  either.

`tccensus check` `L13` makes that a rule rather than a paragraph: **a kind
with zero `declared` rows is a finding**, because a census that derives
everything from the record has not looked outside it. `--self-test` `U13` is
the control on `L13`.

⚠️ **A `TC-` prefix does not mean *toolchain* everywhere in this repository, and
a grep-derived population would have been wrong.** 量 2026-09-12:
`PROGRESS.md`'s carried-forward tables use `TC-<letter>` as a **generic**
counter — `TC-n` is qemu's malta COM1, `TC-o` is `printk` flushing at early
console, `TC-p` is `SPEC.md` holding two rows for one mechanism. That is the
same id-space collision `SPEC.md` `NET-25` records against `NET-14`, live in a
second namespace. The population is taken from `SPEC.md`'s id **column**
through the parser, never from a grep, which is also why `TC-22`'s value cell
naming `TC-15`, `TC-h` and `TC-g` in prose does not pull them in twice.

---

## 2. The four routes, and the fifth column

The routes are **not** the ISA census's four and must not be read across. There
the subject is a die that only one seating can reach; here the subject is a
program on this disk.

| | route | what it means | what it cannot see |
|---|---|---|---|
| ① | 量 at the desk | a toolchain program was executed, or an artefact it produced was executed, and the result measured | it says nothing about whether the output is correct **for this silicon** — `tc-smoke.sh`'s own scope limit, in its own words |
| ② | 量 on an artefact | a shipped binary or a device reading was **read** and a toolchain property inferred | it cannot separate *the toolchain did this* from *the build system asked for it* |
| ③ | 讀 vendor material | a Makefile, a wrapper log, a `.config`, source, or a vendor patch says so | it is what Realtek's engineers **believed**, and `notes/vendor-kernel-isa.md` § 6 records two vendor sources disagreeing |
| ④ | nothing | — | — |

### 2.1 ⓟ — the column the ISA census does not have, and why it has to exist

`R1-pub`'s claim is *this is not in public data*. On the die that holds: no
public source has measured this RLX4181's behaviour. **On the toolchain it
largely does not hold.** The Lexra binutils patch is a public gist, the
gcc Lexra patch is public, a mirror of the rsdk-1.3.6 family is on GitHub, and
Lexra's own history page states the unaligned-load story the whole `F34` thread
rests on.

A census that left that out would be the résumé failure this project keeps
naming — so ⓟ is a column, it is counted, and **`p=y` means a public source
*states this row's finding***, not that the material is public and not that
someone could derive it. `tccensus check` `L11` refuses a `p=y` with no `pub=`
cite in either direction.

量 2026-09-12, the strictness costing something: a public mirror of the
rsdk-1.3.6 family exists and states `gcc-3.4.6` with `uClibc-0.9.30`, which
matches this repository's reading. It states **neither the release string nor
a `-march`**, so the two 1.3.6 rows do **not** carry ⓟ, and what is public
about them is in their note instead.

### 2.2 `mx` — where this census and `SPEC.md` disagree, made countable

`SPEC.md` carries a **V** mark per row: 量 measured on this unit, 讀 read from
code or a dump, 推 conjecture, 文 from a document. `L12` computes the strongest
route each mark supports (量 → ①, 讀 → ②, 文 → ③, 推 and — → ④) and requires
anything stronger to be **declared** with `mx=y`.

🔴 **Eighteen rows need it, and fifteen of the eighteen are one shape.** They
are rows whose evidence is a desk **execution** — a compiler run, an assembler
run, a build, an emulator run — carrying **V=讀**. Several of their own value
cells open with the character **量**: `TC-21` reads *"量 2026-08-28，方法是量不是
grep"* beside a V mark of 讀, and `TC-24`, `TC-27`, `TC-28` and `TC-33` do the
same.

**This is not sloppiness; it is a legend meeting an axis it was not written
for.** `SPEC.md` § 0's marks describe readings about *the device*: 量 means
*measured on this unit*, and running a compiler at a desk in Taipei is not that.
On the toolchain axis "a program was executed and its output measured" has **no
mark of its own**, so it has been recorded as 讀 — the same mark as reading a
Makefile. The two are not the same evidence and this census separates them.

The other three are `TC-02`, `TC-02a` and `TC-03`: rows whose *inputs* are
measured and whose *conclusion* is 推, which is the mark being right about the
conclusion and silent about the inputs.

---

## 3. `R2c` — the recorded findings

<!-- tccensus:r2c begin -->
| row | subject | ① | ② | ③ | ⓟ | V | owner / cross-ref | what is held, and what is not |
|---|:-:|:-:|:-:|:-:|:-:|:-:|---|---|
| `TC-06` | tc | y | . | . | y | 量 | `TC-07` | `mips-linux-gnu-gcc-12` executed here. That `-march=mips1` alone is refused is upstream gcc behaviour and is documented, so this row is public prior art as well as ours |
| `TC-07` | tc | y | . | . | . | 量 | `TC-06` | the same C at two `-march` on gcc-12, with the object's existence as its own control -- a zero that never compiled looks like a zero that did |
| `TC-08` | both | y | . | y | y | 量 | `CPU-46` | binutils 2.42 executed here, and COP3's ISA-level history is in the published MIPS IV manual. The die half is `CPU-46` |
| `TC-13` | tc | y | . | y | y | 讀 | `CPU-18` | 🔴 the vendor assembler RUN at eight `-march` values over twenty instructions, 160 cells with two controls. Its answers are a lookup of a hand-maintained flag word, and the public Lexra patch holds that word -- see § 7 |
| `TC-14` | tc | y | . | . | . | 讀 | `TC-16` | all three wrappers executed. `FATAL: -march mismatch` with exit 1 and no output file is an execution result, and the directory name is NOT the raw driver's default |
| `TC-15` | tc | y | . | . | y | 讀 | `TC-21` | the compiler executed, six `-march`, nop-after-load counted. The public gcc Lexra patch states the same split from the other side, and `SOURCES.json` has described it since before this row existed |
| `TC-16` | tc | y | . | . | . | 讀 | `TC-14` | `tc-smoke`'s four rungs, all three releases reaching the top, plus three real builds. The nine encoded words hashing identically across all three is the control that the rungs measured the same thing |
| `TC-18` | tc | y | . | . | . | 讀 | `TC-12` | the single-variable rebuild cells: only `-march` 0.3360, only toolchain generation 0.2132. Toolchains executed, and the row that refuted the plan's own premise about which factor dominates |
| `TC-19` | tc | y | y | . | . | 讀 | `TC-15` | twelve shipped binaries READ, and the ground truth supplied by seven builds RUN here. The strongest leg is the second, which is why the route exceeds the mark |
| `TC-21` | tc | y | . | . | . | 讀 | `TC-15` | each `.S` preprocessed once and assembled twice at two `-march`, then `hazlint` on each. The value cell opens with the character 量 and the mark reads 讀 |
| `TC-22` | both | y | . | . | . | 讀 | `TC-h` | four sites of one shape, found by building and by `hazlint`. Whether they are hazards is `TC-h`, and no image that has booted on this die carries them -- `-fno-if-conversion` removes the sites and `hazlint` is a build gate |
| `TC-23` | tc | y | . | . | . | 讀 | `TC-30` | a kernel built here and executed under `qemu-system-mips` with this unit's own kernel as the positive control. An execution, and the mark reads 讀 |
| `TC-24` | tc | y | . | . | . | 讀 | `TC-26` | `oldconfig` run under five policies with the symbol-level diff taken, after a first version whose four claims were three-quarters wrong. The correction is in the row |
| `TC-25` | tc | y | . | . | . | 讀 | `TC-22` | three builds differing only in `CFLAGS_KERNEL`, with the conditional-move count taken by importing `hazlint` itself rather than by a second scanner that could disagree with it |
| `TC-26` | tc | y | . | . | . | 讀 | `TC-24` | the declared kernel delta, pinned to a baseline by sha256 rather than by filename, and checked by a tool that reads the BUILT `.config` and not the copied-in one |
| `TC-30` | tc | y | . | . | . | 讀 | `TC-29` | marks applied to a staged tree and verified against the BUILT `vmlinux`, which is the half that catches a mark that compiled and is not in the image |
| `TC-31` | tc | y | . | . | . | 讀 | `TC-26` | two builds' sizes and their `(NEW)` counts. The trap fired on the first attempt, which is the evidence that the two variants are declared rather than discovered |
| `TC-32` | tc | y | . | . | . | 量 | `TC-30` | two routes cross-checked, one of them `objcopy -O binary`. The error was in the conservative direction, so nothing over the ceiling ever passed |
| `TC-33` | tc | y | . | . | . | 讀 | `TC-34` | the drop's own `rtkload` pipeline executed end to end with the drop's own `vmlinux.elf` as the positive control, and `nfjrom` came out byte-identical |
| `TC-34` | tc | y | . | . | . | 量 | `TC-33` | `cvimg` executed directly, and the signature it writes is not the one this unit's flash carries. The row's first version claimed more than this and was narrowed |
| `TC-35` | tc | y | . | . | . | 量 | `TC-21` | `hazlint-objs` over objects built here: an excision that is printed and does not happen, in the safe direction. `TC-m` in `PROGRESS.md` is the carried-forward half |
| `TC-37` | tc | y | . | . | . | 量 | `TC-25` | four builds, and the whole difference was one compiler flag that no committed file recorded. Found by diffing kbuild's own `.cmd` files word by word |
| `TC-38` | tc | y | . | . | . | 量 | `TC-37` | four build pairs through `repdiff`: the same tree twice gives the same sha256, and the 84 bytes that once differed are two causes and not one |
| `TC-39` | tc | y | . | . | . | 量 | `TC-38` | one declared epoch rendered into two derived values before staging, so they cannot drift, and verified against the built artefact. Midnight UTC is the signal that it is declared |
| `TC-40` | tc | y | . | . | . | 量 | `TC-43` | four cells timed from the build driver's own stdout with the driver unmodified. Stage boundaries are the instrument, not a stopwatch |
| `TC-41` | tc | y | . | . | . | 量 | `TC-44` | `make vmlinux` rebuilds 599 objects with nothing changed, twice running, and the cause is two generated headers whose contents are byte-identical |
| `TC-42` | tc | y | . | . | . | 量 | `TC-41` | `--keep` buys 3 to 5 per cent and cannot be used with `--marks` at all. Both halves measured, and the reproducibility cost is 2 bytes of 3,968,240 |
| `TC-43` | both | y | . | . | . | 量 | `TC-40` | the machine pipeline total, and its last term is a 7.260 s boot on the silicon. The only row here whose number contains a device reading |
| `TC-44` | tc | y | . | . | . | 量 | `TC-41` | a patch applied and removed inside one sequence, single variable, with kbuild's own `V=2` naming the cause: 597 objects rebuilt for a command line that is byte-identical |
| `TC-45` | tc | y | . | . | . | 量 | `TC-44` | six builds. One real edit costs a full build, and the refutation condition was that the floor could not be reproduced -- it was |
| `TC-46` | tc | y | . | . | . | 量 | `TC-45` | the same real edit at 4 objects instead of 592, product byte-identical. The one consumer in the staged tree is what made a narrower scope legal |
| `TC-47` | tc | y | . | . | . | 量 | `TC-26` | three images carry an undeclared config difference and the gate that would have caught it was never invoked by the build driver. The gate was right and nobody ran it |
| `TC-48` | tc | y | . | . | . | 量 | `TC-13` | 🔴 the three rsdk assemblers are not one table. Two 1.3.6 agree in 160 of 160; 1.5.5 rejects the `-march` spellings `lx4180` and `lx5280` outright and differs on 2 of the 120 cells it can be compared over, both `jalx`. Measured under the vendor tripwire, both ends CLEAN |
| `TC-49` | tc | y | . | y | . | 量 | `TC-13` | the public Lexra patch predicts this repository's committed matrix in 158 of 160 cells, with the prediction committed BEFORE the run and compared by an instrument. ⚠️ ⓟ is not claimed: the patch is public and this agreement rate is not, which is what § 2.1's rule for the column actually says |
| `TC-50` | tc | y | . | . | . | 量 | `TC-14` | the name `mips-linux-gcc` is the raw driver on 1.3.6 and the WRAPPER on 1.5.5, decided by behaviour rather than by filename or size, and the two generations' wrappers inject different flag sets. The consequence is that a committed method sentence names the wrong binary for half of its own table |
| `TC-51` | tc | y | . | . | . | 量 | `TC-15` | the two rsdk-1.3.6 releases' code generators are byte-identical at `-march=4181` and differ at `-march=5281`, where they read 425/0/162 and 424/0/147. The published row is the first one's, and that is the release whose wrapper refuses that `-march` |
| `TC-52` | tc | y | . | . | . | 量 | `TC-50` | of the three flags the 1.5.5 wrapper injects, only `-ffix-bdsl` changes a load-use reading, and what it changes is the unresolved-successor class: nineteen to zero, with the object sha256 identical within each group |
| `TC-53` | tc | y | . | . | . | 量 | `TC-05` | hardening, three columns and a modern control. gcc 3.4.6 refuses `-fstack-protector` outright; gcc 4.4.5-1.5.5p4 accepts it, warns that it is unsupported for this target, emits no guard and exits 0. No `libc.a` in any release carries a `__*_chk` entry point, which attributes `FW-18` to the library rather than to a build-flag choice |
| `lwl-codegen-sweep` | tc | y | . | . | . | — | `CPU-16` | 🔴 a three-toolchain by four-`-march` codegen sweep, recorded under a `CPU-*` id that a `TC-*` derivation cannot see, which is what a declared row is for. 🔴 Its headline -- 1.3.6 emits zero `lwl` and 1.5.5 emits four -- was narrowed on 2026-09-13: the two generations' raw drivers agree at zero and the asymmetry is the 1.5.5 wrapper injecting `-fuse-uls`. See `TC-50` |
| `TC-01` | tc | . | y | y | . | 量 | `TC-09` | this unit's own kernel banner, and `TC-09` finds the same string in a shipped `boa`'s `.comment` -- two artefacts. The toolchain itself has never been run here: the only 1.5.5 on hand is 5281/p4 and this unit is 4181/p2 |
| `TC-02` | tc | . | y | . | . | 推 | `TC-02a` | the banner match is evidence on artefacts and the CONCLUSION is a hypothesis until `R2a`; `SPEC.md` marks the value 推 for the conclusion, which is why the route disagrees with the mark |
| `TC-02a` | tc | . | y | . | . | 推 | `TC-02` | the corpus matrix EXCLUDES the 2019/2020 generation and bounds the rest; six shipped images cannot say which source release sat on the build machine, so the exclusions are 量 and the identification stays 推 |
| `TC-04` | tc | . | y | . | . | 讀 | `CPU-16` | `e_flags` read out of six shipped `boa`, spanning the 2018-03-30 to 2019-03-15 change from `0x1007` with pic to `0x1005`. A header field, not an execution |
| `TC-09` | tc | . | y | . | . | 讀 | `TC-01` | `.comment` survives in two of six trees and carries `TC-01`'s exact string. A second independent artefact -- userland against kernel -- and a read, not a run |
| `TC-10` | tc | . | y | . | . | 讀 | `TC-12` | the 2+2+2 container partition, entirely from ELF metadata with no similarity measure involved. It is the control that `TC-12`'s clustering is not an artefact of the ruler |
| `TC-11` | tc | . | y | . | . | 讀 | `TC-12` | the ruler's own calibration. `binsim` READS binaries, it does not execute them, which is why this is route 2 on an axis where route 1 means something ran |
| `TC-12` | tc | . | y | . | . | 讀 | `TC-10` | three clusters, cell for cell identical to `TC-10`'s container fingerprints, and this unit's nearest neighbour at 0.9818 against 0.8951 |
| `TC-29` | tc | . | y | . | . | 讀 | `TC-30` | `readelf` and `objdump` over an artefact built here. A static read of a binary, and the answer is that by default nothing can put a word on the wire |
| `TC-36` | both | . | y | . | . | 量 | `TC-01` | a format string present in this unit's kernel and absent from both of mine, with the control on the same physical unit under factory firmware. A read, and the second data point that the shipped kernel came from no drop here |
| `TC-03` | tc | . | . | y | . | 推 | `TC-02` | the drop's target board is read out of the drop; that DDR timing, PHY and GPIO may therefore differ is the conjecture the mark is about, and getting it wrong need not crash |
| `TC-17` | tc | . | . | y | . | 讀 | `TC-14` | three drops' top-level `.config` read. Nothing executed, and the control is that each file carries three independent lines naming the same release |
| `TC-20` | tc | . | . | y | . | 讀 | `TC-14` | `grep -rnI` over three trees: a release every drop's `users/Makefile` names and none ships. The row that makes `R2c`'s missing column visible from the vendor's side |
| `TC-27` | tc | . | . | y | . | 讀 | `TC-28` | a grep and find census over a vendor source tree with a seeded positive control. Nothing executed; the finding is that a blind spot is real and that the obvious prescription for it is wrong |
| `TC-28` | tc | . | . | y | . | 讀 | `TC-27` | `git ls-files` and `readlink -f` over three drops: two of the three have `arch/rlx/bsp` pointing at nothing. Read, not run |
| `lexra-binutils-patch` | tc | . | . | y | y | — | `TC-13` | the public binutils-2.24 Lexra patch. `SOURCES.json` has held its `INSN_*` masks and its RLXA/RLXB groupings since the entry was written, no `TC-*` row owns it, and nothing had joined it to `TC-13`. 🔴 The first cite here was the entry's own phrase `100+ Lexra-proprietary mnemonics`, and correcting that phrase to the measured counts BROKE it -- L3 caught the dangling citation on the same run, which is what a declared row's cite is for. It now names the entry by id, and the entry moved to `documents` with a sha256 as its own text instructed |
| `lexra-gcc-patch` | tc | . | . | y | y | — | `TC-15` | the public gcc-4.8.4 Lexra patch: `lwl`/`lwr`/`swl`/`swr` generation disabled for Lexra targets, conditional move gated on `INSN_RLXB`, and `-mno-bdsl` for BRANCH delay slots -- which is not the load-use delay and the distinction has to be kept |
| `rebuild-tenth-cell` | tc | . | . | y | . | — | `TC-18` | the synthesised `rsdk-1.5.5` at `-march=4181`: 推, because the 1.5.5 wrapper refuses that `-march` and the flags were reconstructed from its own log. A column of `R2c`'s table that no toolchain on this disk can produce |
| `TC-05` | tc | . | . | . | . | — | `TC-14` | a DECISION, and half of it is still blank. The environment half closed 2026-08-28; the userspace half is `R7` and the never-built T-modern column is `R2c` itself |
| `TC-h` | die | . | . | . | . | — | `TC-22` | 🔴 the only row in this census whose subject is the silicon: does a conditional move in a load delay slot READ its destination. Owned by `R1a`, no evidence of any class, and the reason `TC-22` stops where it does |
<!-- tccensus:r2c end -->

---

## 4. The toolchain releases

<!-- tccensus:r2t begin -->
| release | subject | ① | ② | ③ | ⓟ | on hand | `SPEC.md` | what is held, and what is not |
|---|:-:|:-:|:-:|:-:|:-:|---|---|---|
| `mips-linux-gnu-gcc-12 with binutils 2.42` | tc | y | . | . | y | . | `TC-06` | the modern host toolchain, and the only one here that is not Realtek's. It has produced `TC-06`, `TC-07` and `TC-08` and has never built a kernel for this board -- the plan's T-modern, still zero columns wide |
| `rsdk-1.3.6-4181-EB-2.6.30-0.9.30` | tc | y | . | . | . | y | `TC-14` | the release rlxfw builds with, and the only wrapper on hand that accepts `-march=4181`. ⚠️ a public mirror of the 1.3.6 family exists and states gcc-3.4.6 with uClibc-0.9.30; it states neither this release string nor a `-march`, so ⓟ is not claimed |
| `rsdk-1.3.6-5281-EB-2.6.30-0.9.30` | tc | y | . | . | . | y | `TC-15` | the 5281 sibling, and the control that makes `TC-15`'s split a measurement: same gcc, same binutils, one `-march` apart, and the delay-slot behaviour differs |
| `rsdk-1.5.5-5281-EB-2.6.30-0.9.30.3-110714` | tc | y | . | . | . | y | `TC-01` | the generation that built this unit's firmware, in the wrong `-march` and the wrong patch level. Its binutils would not start at all until an i386 `libz.so.1` was supplied |
| `gcc 4.4.5-1.5.5p2` | tc | . | y | . | . | . | `TC-01` | 🔴 the toolchain that built THIS unit's firmware, known only by its banner. Not a directory on this disk, so every `R2c` column is a proxy for it and none of them is it |
| `rsdk-1.5.0-4181-EB-2.6.30-0.9.30.{2,3}` | tc | . | . | y | . | . | `TC-20` | two more branches tested for by three files in each drop and shipped by none. Recorded as one row because the record treats them as one item; splitting them here would invent a distinction |
| `rsdk-1.5.5-4181-EB-2.6.30-0.9.30.3-110225` | tc | . | . | y | . | . | `TC-20` | 🔴 named by all three drops' `users/Makefile` and shipped by none. Right generation AND right core -- the one release that would settle `TC-01` directly, and the reason `R2c`'s most relevant column cannot be filled |
<!-- tccensus:r2t end -->

---

## 5. The counts

<!-- tccensus:counts begin -->
| | ① toolchain in hand | ② artefact | ③ vendor material | ④ nothing | ⓟ public | total |
|---|---:|---:|---:|---:|---:|---:|
| `R2c` recorded findings | 39 | 10 | 8 | 2 | 6 | **59** |
| toolchain releases | 4 | 1 | 2 | 0 | 1 | **7** |

| subject | `R2c` rows | toolchain rows |
|---|---:|---:|
| tc | 54 | 7 |
| die | 1 | 0 |
| both | 4 | 0 |
<!-- tccensus:counts end -->

### 5.1 V mark against adjudicated route

<!-- tccensus:marks begin -->
| `SPEC.md` V mark | ① | ② | ③ | ④ | declared disagreements |
|---|---:|---:|---:|---:|---:|
| 量 | 23 | 2 | 0 | 0 | 0 |
| 讀 | 15 | 6 | 4 | 0 | 15 |
| 推 | 0 | 2 | 1 | 0 | 3 |
| — | 0 | 0 | 0 | 1 | 0 |
| (none) | 1 | 0 | 3 | 1 | 0 |
<!-- tccensus:marks end -->

---

## 6. 🔴 The honest answer to the scope question — and this time it fires

The step's refutation condition, written before this census ran, is the same
one `R1-pub-0` carried:

> if the rows this repository already holds cover most of the census, the gate
> is **re-scoped in the open before a payload is written**, not padded out.
> What makes this publishable is that it is not in public data; what makes it
> worth doing is that it is not in *this* data either.

**It did not fire on the ISA axis and it fires here.** The two numbers side by
side are the whole point:

| | route ① | any evidence | rows |
|---|---:|---:|---:|
| `R1a` + `R1b`, the die (`docs/isa-prior-art.md` § 6) | **3** (6.7 %) | 37 (82.2 %) | 45 |
| `R2c`, the toolchains (§ 5 above) | **39** (66.1 %) | 57 (96.6 %) | 59 |

Both totals are the whole table, derived plus declared, so the two rows are
comparable — 量 over both files: 45 is **39 derived and 6 declared**, 59 is
**55 derived and 4 declared**. ⚠️ The toolchain row moved from 33/53 to 35/55
during `R1-pub-0b`, because § 9's run produced two findings and `SPEC.md`
gained two rows for them, and 🔄 **from 35/55 to 39/59 on 2026-09-13**, when
`R1-pub-6`'s assembly produced four more (`TC-50` … `TC-53`). The ratio barely
moves; the fact that a census grows when the record grows is the derivation
working, and the fact that the prose has to be patched beside the generated
block is `XNUM-1`, which is why it is done in the same commit.

🔴 **Thirty-nine of fifty-nine recorded toolchain findings already have a
desk-執行 reading, and only two rows have no evidence of any class.** The
mechanism is not diligence, it is economics: **route ① on this axis costs no
power.** Every one of those rows was obtainable by typing a command, and
over thirty-two segments of `R5` that is what happened. On the die axis the
same route costs the most expensive unit this project has.

**So `R2c` is smaller than the plan's 2 段, and the reason it is smaller is
not that the work was done — it is that the work was cheap.** Three consequences,
stated rather than left to be inferred:

1. 🔴 **`R2c`'s three-column table largely EXISTS and has never been
   assembled.** `notes/rebuild-vs-shipped.md` § 1 holds a 3 drops × 3 rsdk
   matrix; `SPEC.md` `CPU-16` holds a 3 toolchains × 4 `-march` codegen sweep;
   `TC-15` holds the load-delay-slot split across six `-march` on two
   generations; `TC-14` and `TC-16` hold the wrapper and build matrices. Five
   files, one table, nobody has written it.
2. 🔴 **What `R2c` is actually missing is a COLUMN, not measurements.** The
   `r2t` rows say it plainly: the release that would settle `TC-01` —
   `rsdk-1.5.5-4181-EB-2.6.30-0.9.30.3-110225`, right generation and right core
   — is named by all three drops' `users/Makefile` and shipped by none. **The
   most relevant column of `R2c`'s table cannot be filled by any toolchain on
   this disk.**
3. ⚠️ **`TC-13`'s 160-cell assembler matrix records no assembler.** It is one
   toolchain's answer and the committed table does not say which. § 8 is the
   pre-registered experiment that fixes it, and ~~it is the only place where
   `R2c` needs a reading this repository does not already have~~ 🔴 **that last
   clause expired on 2026-09-13: `R1-pub-6`'s assembly took five more readings
   the repository did not have** — which binary is the raw driver in each
   release, the two rsdk-1.3.6 releases separated on `hazlint`, the wrapper's
   injected flags decomposed one at a time, the `lwl` default per driver, and
   the hardening row, which had no cell in any column.
   ⚠️ **The same clause at § 8 is NOT repaired**, and that is deliberate: § 8's
   own preamble says nothing in it was edited after the run, which is the only
   thing making its five predictions predictions. Repairing a sentence there
   would destroy that the way repairing a frozen bench card destroys
   `check-predictions`' mtime evidence.
   🔄 **§ 9: it ran, and the answer is `rsdk-1.3.6-4181` — but it also refuted
   the assumption underneath this item.** The three releases are *not* one
   table, so naming the assembler is not a tidy-up: it is what every
   per-`-march` claim here now needs.

**The gate is re-scoped in the open**: ~~`R1-pub-6` is an *assembly* step
with one measurement in it, not two segments of measurement.~~
🔴 **2026-09-13, the next segment: that sentence is true of the
*assembly* and false of the *step*, and the difference is the one row the
plan says can kill the project quietly.** `plan/router-rebuild-plan.md:1141`
requires the **load-delay row of `R2c`'s table to run on the silicon in all
three columns** — `R1f`'s fragment compiled once per toolchain — and the same
file's § 389 table marks that row as the only cell that can kill the project
silently. **Nothing in this census reaches it**: § 5 records `TC-43` as the
only row here whose number contains a device reading, so two of the three
columns have never had anything run on this die. The correct statement is
that `R1-pub-6`'s **desk** half is one segment and its silicon row is a bench
row this census could not have filled and did not claim to.
⚠️ **This is not a measurement being corrected, it is a requirement that was
never read.** Neither this file nor `PROGRESS.md`'s step-table DoD rejected
it, recorded it as dropped, or named it as an omission; the only thing in
the repository that still remembered it was the `bench 1` in the step's
effort column, with no DoD sentence left to explain why it was there.
The band for the gate as a whole is not touched — that is
`docs/isa-prior-art.md` § 6's arithmetic and nothing here moves it — but
`R2c`'s own 2 段 cap is now expected to come in under **on the desk side
alone**, and this file says so before the work rather than after.
🟢 **And the silicon side is cheaper than it reads, for a structural
reason rather than an optimistic one**: `R1-pub-5` is `R1f` at one toolchain
by ≥ 2 `-march` values, and this row is `R1f` at three toolchains, so one
payload generator taking (toolchain, `-march`) as parameters puts both
steps' bench halves on **one** seating. `PROGRESS.md`'s step table carries
that as the other half of this correction.

---

## 7. 🔴 What this census found that was on nobody's list

**① The public Lexra binutils patch predicts this repository's own committed
assembler matrix, 158 cells of 160.** `SOURCES.json` has described that patch
since before `TC-13` was written — six cores, `INSN_4180 = 0x20000000` through
`INSN_5281 = 0x00000040`, the RLXA/RLXB/RAD1/RAD2 groupings — and nothing had
ever joined it to `isa-probe.sh`'s table. 量 2026-09-12, the patch downloaded
and read. Membership is resolved by `cpu_is_member`, which the patch supplies
in full: `(mask ∩ INSN_<cpu>) ≠ 0`.

| instruction | membership in `opcodes/mips-opc.c` | Lexra cores it admits |
|---|---|---|
| `ll` `sc` | `I2` ∪ `RLX2` ∪ `RLX3` | 4181 5181 4281 5281 |
| `sync` | `I2` ∪ `G1` ∪ `RLX3` | 5181 4281 5281 — see ② |
| `cache` | `I3_32` ∪ `T3` ∪ `RLXB` | 4181 5181 5280 4281 5281 |
| `movz` `movn` | `I4_32` ∪ `IL2E` ∪ `IL2F` ∪ `EE` ∪ `RLXB` | 4181 5181 5280 4281 5281 |
| `mflxc0` `mtlxc0` | `RLXB`, plus an `#H` form at `RLX3` | 4181 5181 5280 4281 5281 |
| `lwl` `lwr` `swl` `swr` | *the patch adds no entry* | all — stock `I1` |

Read against `notes/vendor-kernel-isa.md` § 6's committed matrix, **two cells
disagree and 158 agree**, and three of the agreements matter:

* **`sync` rejected for `rlx4181` and accepted for `rlx5281`** is `RLX3` =
  `INSN_4281` ∪ `INSN_5281`. The row this project calls *two vendor sources
  agreeing on a discriminating fact* is one flag word.
* 🔴 **`ll`/`sc` accepted for `rlx4181` is `RLX2` = `INSN_4181` ∪ `INSN_5181`,**
  and § 6 calls this *the two vendor sources disagree*. It is now visible what
  the disagreement is: a **flag word one engineer wrote**, against a board
  Kconfig that says `ARCH_CPU_LLSC=n`. Those are two beliefs, not two
  measurements, and the row the plan calls the most important one — because it
  decides libc — rests on the weaker of them. **The disagreement is not
  resolved by this; it is located.**
* **`mflxc0`/`mtlxc0` are `RLXB` = every core but `lx4180`.** `CLAUDE.md`'s
  Never-table records, 量 2026-09-04, that they assemble at `rlx4181`,
  `rlx4281`, `rlx5181`, `lx5280` and `rlx5281` and are rejected at `lx4180`.
  **Five for and one against, predicted exactly by a public file nobody had
  opened.**

**② 🔴 `INSN_4281` and `INSN_5181` OVERLAP, so three of the patch's own
groupings leak — and this file's first derivation missed it.** 量, the patch's
own hex: `INSN_5181 = 0x08000000` and `INSN_4281 = 0x0c000000`, whose low bit
of the pair **is** `INSN_5181`. Since membership is `(mask ∩ INSN_<cpu>) ≠ 0`,
every entry marked for `rlx4281` is also live on `rlx5181` and every entry
marked for `rlx5181` is also live on `rlx4281`:

| grouping | as spelled | as it resolves |
|---|---|---|
| `RLX2` | 4181 5181 | 4181 5181 **4281** |
| `RLX3` | 4281 5281 | **5181** 4281 5281 |
| `RAD1` | 5181 5280 5281 | 5181 5280 5281 **4281** — the whole RADIAX set on a core its own name excludes |

**In this grid exactly one cell moves: `sync` at `rlx5181`**, from `.` to `y`,
because `RLX2` ∪ `RLX3` already contained both cores for `ll`/`sc` and `RLXB`
already contained all five for `cache`/`movz`.

⚠️ **This was found by a second derivation that had never seen the first.** The
first pass read the macro definitions and did the set arithmetic on the
*names*; the blind pass read the `#define`s as hex and did it on the *bits*.
They agreed on 159 cells of 160 and the one they differed on is this one, and
the patch's own hex settles it. **A prediction that is going to be published
against a committed table is worth deriving twice**, and this is the segment's
evidence for that rather than its assertion.

**③ `RLX1`, `RLX2` and `RLX3` are defined TWICE in that patch, with different
meanings, and `SOURCES.json` does not record it.** 量: `opcodes/mips-opc.c`
gets `RLX2` = `INSN_4181` ∪ `INSN_5181`; `opcodes/mips16-opc.c` gets `RLX2` =
`INSN_4181` ∪ `INSN_4281` ∪ `INSN_5181` ∪ `INSN_5280` ∪ `INSN_5281`. Same
name, same patch, five cores against two, in separate translation units so
neither compiler warns. **Reading the wrong block flips `sync` at `rlx4181` and
`cache`/`movz` at `lx4180`**, and it is this repository's own committed matrix
that decides which block governs the 32-bit table — a public ambiguity resolved
by local data, which is the opposite of the direction this project usually
works in.

**④ The two cells that do not agree are `cache` at `lx5280` and `sync` at
`rlx5181`, and both misses are in the same direction.** The public patch is
*more permissive* than the committed matrix in both. `cache` is the sharper of
the two: the patch gives `cache` and `movz` the **same** membership word,
`RLXB`, and the committed matrix has them differing at exactly that column —
`movz` `y`, `cache` `.`. One of three things is true and § 8 decides which: the
rsdk assembler's table differs from this 2017 forward-port, the committed cells
are wrong, or the committed matrix was taken with a toolchain whose table
differs. **A hardware fact cannot explain either, because neither is a hardware
fact.** ⚠️ The prior that fits both is that they are different tables of one
lineage: rsdk-1.3.6 ships binutils **2.16.94 (2006)** and this patch targets
**2.24 (2017)**, with the patch's own comments recording a merge from 2.14 to
2.16 and a later Taroko addition.

**⑤ 🔴 `madd` is spelled `mad` on a Lexra `-march`, so `isa-probe.sh`'s `madd`
row is about a SPELLING and the frozen ISA census reads it as an encoding.**
量: the patch changes `{"mad", "s,t", 0x70000000, ...}` from `P3` to
`P3` ∪ `RLXA`, and `RLXA` is all six Lexra cores. Stock `madd` at the **same
word** `0x70000000` keeps `I32` ∪ `N55` and the patch does not touch it.

So the assembler rejects the *string* `madd` for every Lexra `-march` and
accepts the *identical 32-bit instruction* spelled `mad` on all six.
`tools/isa-census.tsv`'s `madd` row reads *"SPECIAL2 form: rejected in all
eight assembler columns, zero in the loader"* — **true about the mnemonic and
misleading about the encoding**, and it is the same shape as
`docs/isa-prior-art.md` § 10 ④: a count taken from one instrument with the
conclusion supplied. The consequence is actionable rather than cosmetic:
**`R1a` must emit the WORD for this row, not the mnemonic**, or it will measure
the assembler's dictionary. The same applies to `msub`, which the patch gives
`I32` ∪ `N55` ∪ `RLXA` and which `isa-probe.sh` does not probe at all.

**⑥ `-march=rlx4181` is not a guard against unaligned loads — and 🔴 this is a
CONFIRMATION, not a finding, because `SOURCES.json` already said so.** That
entry has carried *"NOTE: it does NOT disable `lwl`/`lwr`/`swl`/`swr` — the
assembler still accepts them"* since before this census existed, and the first
draft of this item presented it as new. What is actually added here is the
**count** and the join: 量: `lwl`, `lwr`, `swl` and `swr` appear **zero** times in the patch —
not added, not removed, not re-gated. They keep stock `I1` and therefore
assemble under every one of the six Lexra `-march` values. `notes/vendor-kernel-isa.md`
§ 6 already says the ULS row *"proves nothing"* as an observation; this is the
mechanism, and it has a consequence the observation did not carry: **the
assembler will accept `lwl` for a core whose whole public identity is not
implementing it.** What actually suppresses generation is the *compiler* patch
— `SOURCES.json`'s gcc-4.8.4 entry, `!TARGET_LEXRA && !TARGET_RLX` on those
patterns — so on this axis the guard is in gcc and not in gas. The same holds
for `mfc3`/`mtc3`/`lwc3`/`mfc1`/`lwc1`: all stock `I1`, all accepted for every
Lexra target.

**⑦ The Lexra ASE population gap is 14, not "more than a hundred."**
`docs/isa-prior-art.md`'s *What could still be wrong* says the patch *"adds
more than a hundred proprietary mnemonics to these cores and this project has
not downloaded it — `R2c`"*, sourced from `SOURCES.json`'s description. 量
2026-09-12, downloaded and counted in two units, with the file filter that the
first count needed and did not have:

| | count |
|---|---:|
| opcode-table entries added, `mips-opc.c` + `mips16-opc.c` | **203** |
| distinct mnemonics on those lines | **185** |
| of those, **new** — never appearing as a context or removed line | **148** |
| of the 148, claimed for **RLX4181** by the patch's own membership | **16** |
| of the 16, already in `tools/isa-census.tsv` (`mflxc0`, `mtlxc0`) | 2 |
| 🔴 **new to this repository and claimed for this core** | **14** |

The fourteen are `ltw`, `madh`, `madl`, `mazh`, `mazl`, `msbh`, `msbl`,
`mszh`, `mszl`, `sleep`, `udi0i`, `udi1i`, `udi2i`, `udi3i`. The remaining 132
are gated on flags that exclude `INSN_4181` — the RADIAX DSP set, claimed for
5181/5280/5281 — so **they are not a statement about this core at all**.

🔴 **The first count was wrong and listing the members is what caught it.**
A regex matching `{"name"` anywhere returned 160 new mnemonics, twelve of which
were CPU names: `tc-mips.c`'s CPU table has the same `{"string", ...}` shape as
an opcode entry. The fix is a **file** filter and not a name blacklist, because
a blacklist is tuned to the answer you already got.

⚠️ **These 14 are deliberately NOT added to `tools/isa-census.tsv` tonight.**
That table was frozen with an ordering property — *committed before any payload
source exists* — and growing its population by 36 % the day after, on evidence
from a different axis, muddies the only thing that makes it worth anything. The
bullet that predicted this gap assigned it to `R2c`; **measuring it is the
discharge.** Whether they become `R1a` payload rows is `R1-pub-1`'s decision,
where each extra row's cost is actually paid, and the number it needs — 14 —
now exists.

🔴 **And the row that would have held them was declared and never written.**
`SOURCES.json`'s entry for this patch says it is the *"Source of `R1a`'s named
Lexra ASE row (`F52`)"*. 量 2026-09-13, both directions: **`F52` is defined
nowhere** — not in `SPEC.md`, not under `upstream/`, and its only other
occurrences in this repository are four hex digits inside two bench captures.
So this census's fourteen are the contents of a row this repository promised
itself and never wrote, and the promise was invisible because `SOURCES.json`
is not a `.md` and no citation checker reads it.

**⑧ `isa-probe.sh`'s docstring says *newest rsdk first* and its code takes the
oldest.** 讀: the search is a plain glob, `"$ROOT"/*/toolchain/*/bin/rsdk-linux-as`,
which the shell expands lexicographically, so `rsdk-1.3.6-4181` is the first
candidate and the loop breaks on the first one that assembles. **So `TC-13`'s
committed matrix is almost certainly `rsdk-1.3.6-4181`'s answer and the table
does not say so.** § 8 measures it rather than reasoning about it.

---

## 8. The pre-registered experiment, written before it was run

> **§ 9 has the result.** Nothing in this section was edited after the run —
> `git log` on this file shows § 8 committed at `51a8cba` and § 9 added after
> it, which is the only thing that makes the five predictions below
> predictions.

`R1-pub-6` needs exactly one reading this repository does not have: the
assembler matrix **per toolchain**. All three are on this disk and the run
costs no power. It is written down here, **before the run**, so that the
prediction is a prediction.

### 8.1 The prediction, derived from the public patch alone

Predicted acceptance for all 20 probe rows at all 8 `-march` values, from
`opcodes/mips-opc.c`'s membership words and each Lexra CPU's `ISA_MIPS1` level:

| instruction | lx4180 | rlx4181 | rlx5181 | lx5280 | rlx5281 | rlx4281 | mips1 | mips2 |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `lwl` `lwr` `swl` `swr` | y | y | y | y | y | y | y | y |
| `ll` `sc` | . | y | y | . | y | y | . | y |
| `sync` | . | . | **y** | . | y | y | . | y |
| `cache` | . | y | y | **y** | y | y | . | . |
| `movz` `movn` | . | y | y | y | y | y | . | . |
| `beql` | . | . | . | . | . | . | . | y |
| `madd` `rdhwr` `pref` | . | . | . | . | . | . | . | . |
| `mfc3` `mtc3` `lwc3` | y | y | y | y | y | y | y | y |
| `mfc1` `lwc1` | y | y | y | y | y | y | y | y |
| `jalx` | y | y | y | y | y | y | y | y |

**158 of these 160 cells equal the committed matrix.** The two bold `y` are the
ones that do not, and both are the public patch being the more permissive of
the two tables.

⚠️ **Two caveats that live outside the membership system**, so they are stated
here rather than discovered afterwards. `mfc1` and `lwc1` are gated a second
time by `is_opcode_valid`'s floating-point check and would read `.` under a
soft-float default — `isa-probe.sh` invokes `as` bare and passes no
`-msoft-float`, so the committed `y` is about a bare assembler and not about a
kernel build's command line. And `beql` and `jalx` as the last instruction of a
`.set noreorder` file produce *"end of file in delay slot"*, which is a
**warning**: the probe's exit status is what decides the cell, so a warning
reads as `y` and that is the intended reading.

### 8.2 What is predicted for the run

* **P1** — all three rsdk assemblers produce the **same** 160-cell matrix.
* **P2** — that matrix equals `notes/vendor-kernel-isa.md` § 6's committed one,
  cell for cell, in all 160.
* **P3a** — `cache` at `lx5280` reads `.` on **all three**, so the difference
  from § 8.1 is the rsdk table and not this repository's reading.
* **P3b** — `sync` at `rlx5181` reads `.` on **all three**, for the same
  reason. ⚠️ This one is the weaker prediction of the pair: it needs the rsdk
  table to *not* carry the `INSN_4281` / `INSN_5181` bit overlap of ② , and
  nothing here has seen rsdk's bit assignment.
* **P4** — `isa-probe.sh` names `rsdk-1.3.6-4181` as the assembler it selected
  by default (⑧ above).
* **P5** — both controls hold in all 24 columns: `addu` accepted everywhere,
  `daddu` rejected everywhere.

### 8.3 What each refutation would mean

> **否證 P1** — the three rsdk generations carry **different** Lexra opcode
> tables. Then `TC-13` is one toolchain's answer that has been quoted as if it
> were *the vendor assembler's*, `R2c`'s three columns are three genuinely
> different machine descriptions, and every per-`-march` claim in this
> repository has to name its toolchain.

> **否證 P2** — the committed matrix disagrees with a re-run of the same
> instrument. Then either the matrix was taken with something else, or
> `isa-probe.sh` is not deterministic, and no per-core ISA claim here stands
> until it is told which.

> **否證 P3a or P3b** — `cache` reads `y` at `lx5280`, or `sync` reads `y` at
> `rlx5181`, on some assembler. Then that committed cell is wrong, § 6 of
> `notes/vendor-kernel-isa.md` needs a correction, and the public patch
> predicted one cell more than 158. If **both** refute, the public patch
> predicted **160 of 160** and this repository's twelve-day-old matrix has two
> errors in it.

> **否證 P5** — a control fails and **nothing below it is reported**, which is
> `isa-probe.sh`'s own rule and not an addition here.

⚠️ **What this experiment cannot decide**: whether any of it is true of the
**die**. Every cell is a statement about an opcode table. `notes/vendor-kernel-isa.md`
§ 6 says so in its own words and § 2 above repeats it, because a 480-cell table
is exactly the shape of thing a reader takes for a hardware result.

---

## 9. The run, 2026-09-13, and P1 is refuted

§ 8 was committed at `51a8cba` and the assemblers were run after it. Four
`isa-probe.sh` invocations plus one `-march` vocabulary scan, all under
`tools/vendor-tripwire.sh`: **six trees watched, CLEAN before and CLEAN
after**, and the artefacts are in `$FWRE_WORK/rebuild/r1pub0b/` rather than
here, which is the same rule `notes/vendor-kernel-isa.md` § 6's table follows.

🟢 **The ordering is verifiable to the second, which is stronger than the usual
`git log` argument.** `51a8cba` has committer time **00:15:55** and the first
probe output in `$FWRE_WORK/rebuild/r1pub0b/` has mtime **00:16** — the
prediction was in the history before any of the bytes it predicts existed. The
counts in § 7 are earlier still: the scripts that produced them ran at
**23:28–23:33 on 2026-09-12**, before this file had a § 8.

| | prediction | result |
|---|---|---|
| **P1** | all three assemblers give the same 160-cell matrix | 🔴 **REFUTED** — see below |
| **P2** | the measured matrix equals the committed one | 🟢 **160 of 160**, twelve days later |
| **P3a** | `cache` at `lx5280` reads `.` | 🟢 held |
| **P3b** | `sync` at `rlx5181` reads `.` | 🟢 held |
| **P4** | the default selection is `rsdk-1.3.6-4181` | 🟢 held — `GNU assembler 2.16.94-1.3.6 20060612` |
| **P5** | both controls hold in all 24 columns | 🟢 in the two that ran; 🔴 the third's POS control **fired** |

**So the public patch predicts the rsdk-1.3.6 table in 158 cells of 160, and
that is now measured rather than inferred.** Both misses are the patch being
more permissive, and § 7 ④'s prior — two tables of one lineage, binutils 2.16.94
against 2.24 — is the reading that survives.

### 9.1 🔴 How P1 was refuted, in two separable pieces

**① The `-march` vocabulary is not the same.** 量, `addu` at fourteen spellings
per assembler:

| assembler | `lx4180` | `lx5280` | `4180` | `5280` | the other ten |
|---|:-:|:-:|:-:|:-:|:-:|
| `rsdk-1.3.6-4181` — binutils 2.16.94-1.3.6 | y | y | y | y | all y |
| `rsdk-1.3.6-5281` — binutils 2.16.94-1.3.6 | y | y | y | y | all y |
| `rsdk-1.5.5-5281` — binutils 2.19.92.20091006 | **.** | **.** | y | y | all y |

`rsdk-1.5.5`'s assembler answers `Error: Bad value (lx4180) for -march` and
takes the numeric `4180` for the same core. **So it is a spelling that was
removed between the two generations, not a core** — which a table of
rejections would have reported as the opposite.

**② `isa-probe.sh` REFUSED the whole 1.5.5 table, and that is the tool being
right.** Its POS control failed in exactly those two columns, so it printed
nothing: six columns of data beside two columns of `.` would have read as *1.5.5
rejects everything for lx4180 and lx5280*, which is false. Re-run over the six
`-march` values that assembler **does** know — a narrower question, declared as
one, not a widened control — it produces a full table with both controls
holding.

**③ Over those six shared columns the two generations differ in 2 of 120
cells, and both are `jalx` at `mips1` and `mips2`.** 1.3.6 accepts, 1.5.5
rejects; all four Lexra columns agree. 🔴 **That lands on the row
`docs/isa-prior-art.md` § 10 ② added twelve hours earlier**, whose committed
sentence is *accepted in all eight columns … so it discriminates nothing*. True
of 1.3.6 and **false of 1.5.5**, where the row does discriminate — weakly, by
separating MIPS-I/II from the Lexra set. ⚠️ **Unattributed**: nothing here
separates a Lexra-patch change from an upstream binutils change between 2.16.94
and 2.19.92, and reading stock `mips-opc.c` for both versions is the experiment
that would. 🟢 The blind second derivation of § 8.1 flagged `jalx` in advance as
*"the one row most worth checking against a real build"* — the only row it
marked that way, and the only row that moved.

### 9.2 What the refutation costs, and it is the cost § 8.3 wrote down

> …then `TC-13` is one toolchain's answer that has been quoted as if it were
> *the vendor assembler's*, `R2c`'s three columns are three genuinely different
> machine descriptions, and **every per-`-march` claim in this repository has to
> name its toolchain**.

All three consequences land. `SPEC.md` `TC-13` and `notes/vendor-kernel-isa.md`
§ 6 now name the assembler and its version; the `jalx` bullet there is scoped to
the generation that produced it. 🟢 **And `R2c` gains a column it did not know
it needed**: *which `-march` spellings does each release accept* is a row of the
three-column table, it is measured, and it separates the generations where the
instruction matrix nearly does not.

⚠️ **What this does not settle.** Whether any cell is true of the die — every
one is a statement about an opcode table, and § 2 says so. Whether the 1.5.5
`-march` removal is Realtek's or upstream's. And whether the fourth release,
`rsdk-1.5.5-4181-…-110225`, would agree with either: it is named by all three
drops and shipped by none, so `R2c`'s most relevant column is still the one no
toolchain here can fill.

---

## What could still be wrong

* 🔴 **The population is the record, and the record is not the measurements.**
  § 1 states it and `L13` tests one consequence of it; neither closes it. A
  toolchain reading taken during `R5` and never written into `SPEC.md` has no
  row here and nothing in this repository could find it. The four `declared`
  rows are a lower bound on how much of that there is, not a measurement of it.
* 🔴 **The adjudication is a judgement.** `tccensus check` verifies that every
  derived row is present, that no row is invented, that every cited `SPEC.md`
  id exists, that a `p=y` has somewhere to go, that every row says
  toolchain-or-die, and that a route stronger than its V mark is declared.
  It does **not** verify that route ② is the right call for a given row.
  Thirteen mutation controls fire on the checkable half; the judgement half is
  a person's, and it is this file.
* ⚠️ **The route-① count in § 6 is a count of rows, not of work.** `TC-40`
  through `TC-47` are eight rows about build economics that took one segment
  between them; `TC-15` is one row that took a day. Reading 32/49 as *65 % of
  `R2c` is done* would be reading a row count as an effort estimate, which is
  the `Est.` column defect this repository has recorded three times.
* ⚠️ **`notes/vendor-toolchains.md` was deliberately not opened for editing
  before this file was committed**, on the same ground as `R5-0`'s blind-write
  ledger: a population chosen after reading the prose that would suggest rows
  is a chosen population. It is cited, and citing is reading, not editing.
* 🔴 **The ⓟ column's five `y` values are what one person found in one
  evening.** OpenWrt's Realtek thread, the buildroot patches, the LinuxMIPS
  Lexra page and the rtl8181 cookbook are all named in `SOURCES.json` and none
  of them was re-read for this census. If `R1-pub`'s publishability claim is
  ever put to a hostile reader, the toolchain half of it is the half that will
  be checked first.
