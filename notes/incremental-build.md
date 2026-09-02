# The incremental build — can this tree do one, and what does it cost

## 0. What this file owns

`R4-3`. **Whether a rebuild of this kernel tree can be made incremental, what
that saves, and what it costs in trust.**

It does not own the diagnosis. `notes/dev-loop.md` §5.2 owns *what forces the
full rebuild* — two generated headers rewritten with identical content and a
fresh mtime — and §9 of that file lists the two things it left open. This file
closes both and owns the answers:

* the ⚠️ **whether the `cmd,bounds` rule is Realtek's or mainline's** → §2;
* the 🔴 **the saving is unmeasured** → §4 predicts it, §5 measures it.

It does not own `--keep`'s reproducibility cost either. That is
`notes/reproducible-build.md` `L2-6`, closed 2026-09-01 at two bytes, and this
file cites it rather than restating it.

**§1–§4 were written and committed BEFORE any measurement in §5 was taken**,
the same way `notes/dev-loop.md` §1–§3 were. That is checkable —
`git log --follow notes/incremental-build.md` shows a first commit holding the
predictions and none of §5's numbers.

⚠️ **§2's digests are an input to the experiment, not an outcome of it.** They
were read before the predictions were written and they say what the tree
contains, not what a build does.

---

## 1. The question, and why `--keep` turned out to be the wrong target

`R4-3` was opened braced for a fight over `rlxfw-kbuild.sh --keep`. The gate's
stop-loss says in as many words that `--keep` may not be turned on to hit a
number, because it breaks `.version` and therefore `P4a`'s Level-2 claim.

`R4-0` measured both halves of that tension and both are small:

* `--keep` skips the 480 MB re-stage, the host-compat patches and the mark
  application, and **nothing else** — 1.5–2.4 s, 3–5 % of a build
  (`notes/dev-loop.md` §4.1, §5);
* its reproducibility cost is **two bytes of 3,968,240**, a monotonic link
  counter (`notes/reproducible-build.md` `L2-6`, §5.1 there).

And it measured the thing that actually costs: **a `make vmlinux` with nothing
touched recompiles all 599 objects, twice in a row.** So `--keep` buys the
stage copy back and leaves the whole `make` phase — 68–77 % of the build —
exactly where it was.

**This file is about that 68–77 %.**

---

## 2. 讀 — the rule that forces it is mainline's, unmodified

`notes/dev-loop.md` §5.2 left this open with the experiment attached: *one
mainline 2.6.30 `Kbuild` settles it.* It was fetched from `torvalds/linux` at
tag `v2.6.30` through the GitHub contents API, which is a source independent of
all four GPL drops.

| file | mainline v2.6.30 | this drop | |
|---|---|---|---|
| `Kbuild` | `c1065aab0da23578` | `c1065aab0da23578` | **SAME** |
| `scripts/Kbuild.include` | `da1c432cee107043` | `da1c432cee107043` | **SAME** |
| `kernel/bounds.c` | `de2218cd6c4b770a` | `de2218cd6c4b770a` | **SAME** |
| `Makefile` | `ff2fe6d9b16b62a2` | `82c8e5e2cd1d93be` | **DIFFERENT**, 159 lines |

🔴 **The last row is the control and it is why the other three mean
anything.** A comparison that returns *same* for every input is not measuring;
the top-level `Makefile` is a file Realtek certainly did change, and the same
method reports it as changed. `Kbuild`'s 2,430 bytes are byte-identical, and so
are they in **all three** `linux-2.6.30` trees on disk
(`rtl819x-toolchain`, `saturn49-wecb/rtl819x`, `wecb-vz-gpl/rtl819x`) — one
source, three copies, which is the same weakness that travels with `PRId`'s
assignment table and matters less here because the reference is mainline
itself rather than a fourth copy.

**So Realtek did not write the rule and did not touch it.** The full rebuild is
a stock 2.6.30 property, and anything found here is a statement about that
kernel and not about this vendor.

### 2.1 And mainline itself fixed it, in the same file

Current mainline's top-level `Kbuild`, same API, `master`:

```make
$(bounds-file): kernel/bounds.s FORCE
	$(call filechk,offsets,__LINUX_BOUNDS_H__)
```

`filechk` against 2.6.30's `$(call cmd,bounds)`. The machinery is already in
this tree — `scripts/Kbuild.include:49`, byte-identical to mainline's — and its
own comment states the property this step wants:

```
# - If no file exist it is created
# - If the content differ the new file is used
# - If they are equal no change, and no timestamp update
```

So the change is not an invention. It is a backport of the fix mainline made to
the same two rules, using a macro this tree already ships.

---

## 3. What the patch does

🔴 **This section was written before §5 and it describes a patch aimed at the
wrong cause.** It is kept as written. §5.1 is where `P2` refutes it, §5.2–§5.3
are the cause it missed and the patch that fixes it
(`0004-kbuild-make-cmd-pound.patch`), and §5.7 is the measurement that kept
this one anyway, for a reason that has nothing to do with why it was written.

`config/host-compat/0003-kbuild-filechk-generated-headers.patch`, applied by
`tools/rlxfw-kbuild.sh` like the other two, failing the build if it does not
apply.

It replaces the two unconditional redirects with content checks:

| rule | 2.6.30 | after |
|---|---|---|
| `$(obj)/$(bounds-file)` | `$(call cmd,bounds)` | `$(call filechk,bounds)` |
| `$(obj)/$(offsets-file)` | `$(call cmd,offsets)` | `$(call filechk,offsets)` |

`filechk_$(1)` is invoked with `$<` on stdin and its stdout compared against
the existing file, so the two `cmd_` bodies become `filechk_` bodies with the
`> $@` redirect and the surrounding `(set -e; …)` removed — `filechk` supplies
both.

⚠️ **What it deliberately does not do.** It does not touch `always`,
`targets`, the `FORCE` prerequisites or the `.s` rules. `kernel/bounds.s` and
`asm-offsets.s` are still regenerated every build by `if_changed_dep`; what
changes is only whether the resulting *header* is rewritten when its content
did not move.

⚠️ **It changes `RECIPE_ID`, by design.** `rlxfw-kbuild.sh` computes
`RLXFW_SRC_ID` as a sha256 over every file under `config/`, so adding a file
there moves it. `notes/dev-loop.md` §4 and `SPEC.md` `TC-40` name
`d31f60bd` as the recipe id of a measurement dated 2026-09-01; those are
historical readings and stay true. Any build after this patch has a different
id, and that is what that mechanism is for.

---

## 4. Predictions, with refutation conditions, written before the measurement

The tree is staged once by `tools/rlxfw-kbuild.sh` with `R4-0`'s recipe, and
the patch is applied **to that same staged tree, in the middle of the
sequence**. One tree, one variable: nothing else can differ between the before
and the after.

| # | prediction | refuted by |
|---|---|---|
| **P1** | 🔴 **negative control.** A no-op `make vmlinux` on the tree **before** the patch issues **599** `CC` lines, and **both** generated headers come back with a new mtime and the same sha256 | fewer than 599 `CC` lines, or either mtime standing still — either would mean §5.2's diagnosis is wrong and this whole step is aimed at the wrong file |
| **P2** | After the patch, a no-op `make vmlinux` issues **0** `CC` lines and moves **neither** mtime | any `CC` line, or either mtime moving |
| **P2′** | ⚠️ The **first** make after the patch still rebuilds everything, because the headers already carry the mtime the unpatched run gave them. Two makes are needed; the first is a settling run and is **not** the reading | the first post-patch make issuing 0 `CC` lines would mean the mtimes were not what forced it |
| **P3** | 猜, uncalibrated: the no-op make after the patch takes **2–8 s**. The floor is not zero — make still descends 731 directories and stats the tree | nothing. This is a guess and any value is recorded as the measurement; it is here so that a wildly different number is visibly a surprise |
| **P4** | Touching `init/main.c` and rebuilding issues **1** `CC` line and relinks | more than a handful would mean header dependencies dominate and an incremental build on this tree is not the win it looks like |
| **P5** | 🔴 **correctness.** The `vmlinux` the patched tree links differs from the one the same tree linked before the patch in **exactly the two bytes `L2-6` names** — `linux_banner+0x3a` in `.rodata` and `init_uts_ns+0xc8` in `.data`, the `.version` counter | a differing byte **anywhere else**. If one appears, an incremental build on this tree is not trustworthy and `R4-3`'s answer to the `--keep` tension is *no* |
| **P6** | 🔴 **the patch does not change the product.** A fresh stage with the patch declared, `--marks`, differs from `j4a`'s `6268def94281659a` in **4 bytes or fewer**, all in `.text`, all inside the single symbol holding the banner `printk` — the `RLXFW_SRC_ID` immediate, which moved because `config/` gained a file. 猜 on the count: a 32-bit constant is `lui`+`ori`, two 16-bit immediates, so 4 bytes if both halves move and 2 if one collides | any differing byte outside that symbol. That would mean the patch changes codegen, and it would be rejected on the spot |
| **P7** | 讀, not measured: the patch's own cost is two `cmp` of a ~2 KB file per build. It is not separable from the 25.6–43.5 s spread the `make` phase already shows, and **no claim is made that it is** | — |
| **P8** | 🔴 **The saving on the DEFAULT path is exactly zero.** A fresh stage has no object files, so every object is compiled whatever the header rule does. The patch buys nothing unless the tree is reused — which is `--keep`, which the gate's stop-loss fences off | a fresh-stage build getting measurably faster with the patch. That would mean the diagnosis in §5.2 is wrong |

🔴 **P8 is the one that decides what this step is allowed to conclude.** If it
holds, then the prize `LOOP-1` named is real and is **unreachable through the
loop's default path**, and saying otherwise would be exactly the trade the
stop-loss forbids. What that leaves is a measured number and a decision to put
in front of the owner, not a faster default arrived at quietly.

---

## 5. Measured, 2026-09-02

One staged tree, `i1`, `R4-0`'s recipe (`--config quietm.config-installed
--initramfs r3-9/initramfs/rlxfw-initramfs.spec --marks -j4`,
`CFLAGS_KERNEL=-fno-if-conversion`, stamp `1788220800`, 16 mark rows).  The
patch is applied and reverted **in the middle of the sequence, to that same
tree**, so nothing else can differ between a before and an after.  Raw log:
`$FWRE_WORK/rebuild/r4-3/exp.log`, `exp2.log`, `exp3.log`.

The full build reproduced `j4a`'s `vmlinux` sha256 **`6268def94281659a`** — a
seventh replication of `P4a`'s Level-1 claim, on a different day.

### 5.1 The predictions, scored

| # | prediction | outcome |
|---|---|---|
| **P1** | negative control: 599 `CC`, both mtimes move, same sha | 🟢 **held.** 599 `CC`, both `1788293473 → 1788293500`, `bd0652b2b7b1a641` and `f7575686e3719433` unchanged |
| **P2** | after the patch, 0 `CC` and neither mtime moves | 🔴 **REFUTED.** Neither mtime moved and `CHK` went 4 → 6 — the patch did exactly what it says — and the rebuild was **still 599 `CC`** |
| **P2′** | the first post-patch make still rebuilds everything | 🔴 **refuted in the other direction.** The mtimes froze on the *first* post-patch make, not the second |
| **P3** | 猜 2–8 s | not reached: the no-op make was 31.2 / 32.1 s, because P2 failed |
| **P4** | touching one `.c` gives 1 `CC` | 🔴 **REFUTED.** 599, the same as touching nothing |
| **P5** | correctness: only `.version`'s two bytes | 🟢 **held**, three times: `B→C`, `C→E` and `A→E` each differ in exactly 2 of 3,968,240 bytes, `linux_banner+0x3a` and `init_uts_ns+0xc8` |
| **P8** | the default path saves exactly zero | 🟢 holds, and §6 is what it costs |

🔴 **So `LOOP-1`'s stated cause is refuted.** The two generated headers are not
what forces the rebuild. `notes/dev-loop.md` §5.2 measured a real thing — they
*are* rewritten every build with identical content — and drew the wrong arrow
from it.

### 5.2 What the cause is, and kbuild says it in its own words

`scripts/Kbuild.include:232` defines a `why` macro that `V=2` appends to every
recipe line make decides to run. One run answers it:

```
597  - due to command line change
 88  - due to: <prereq list>
  1  - due to vmlinux.o not in $(targets)
  1  - due to target is PHONY
```

`arg-check` compares the command saved in `.<target>.o.cmd` with the one make
computes now. 量 on `init/main.o`, both strings extracted and compared word by
word: **byte-identical, 1,132 bytes, zero differing words.** (1,132 is with the
trailing newline both extractions kept; the table below counts the same line
without it, which is why it reads 1,131. Two measurements of one line, and
naming that here rather than letting a reader find two numbers for one thing.)

What differs is what make *loads*:

| | bytes | bare `#` |
|---|---:|---:|
| the `cmd_init/main.o :=` line as it sits on disk | 1,131 | 1 |
| the value make holds after `include`-ing that file | **1,023** | **0** |

108 characters are discarded on every read, and the cut is at
`-D"KBUILD_STR(s)=` — **a bare `#` in a makefile starts a comment**. So
`arg-check` compares a truncated string against a whole one, can never match,
and every object rebuilds forever.

🟢 **And the two exceptions are the two that survive the fix**, which is
the closure that makes this more than a plausible story. Re-deriving the V=2 log
one line at a time: of its **599** `CC` lines, **597** say `command line change`
and exactly **two** name a real prerequisite —
`drivers/net/wireless/rtl8192cd/8192cd_hw.o`, naming all ten `data_*.c` files
Realtek regenerates every build, and `init/version.o`, naming
`include/linux/compile.h`. Those are precisely the two objects a no-op `make`
still compiles after the fix (§5.6). **The 597 that had a spurious reason stop;
the 2 that had a real one continue.** Nothing was tuned to make that come out.

### 5.3 Whose bug it is, and the fix is mainline's own again

`scripts/Makefile.lib:139` writes `-D"KBUILD_STR(s)=\#s"`; make unescapes it,
so the *value* carries a real `#`. `scripts/Kbuild.include:184` is supposed to
put the escape back before `fixdep` writes it out:

```make
make-cmd = $(subst \#,\\\#,$(subst $$,$$$$,$(call escsq,$(cmd_$(1)))))
```

量 under **GNU Make 4.3**, on a value carrying one bare `#`:

| form | result | bare `#` | `\#` |
|---|---|---:|---:|
| `pound := \#` | `#` | — | — |
| 2.6.30's `$(subst \#,\\\#,…)` | unchanged | **1** | **0** |
| mainline's `$(subst $(pound),$$(pound),…)` | `…=$(pound)s…` | **0** | — |

**The escape is a no-op.** `scripts/basic/fixdep.c:140` then writes the command
verbatim — `printf("cmd_%s := %s\n\n", target, cmdline)`, no escaping anywhere
in that program — and the bare `#` lands in the `.cmd` file.

🔴 **Neither file is Realtek's.** 量: `scripts/Makefile.lib` is
`710bda1b500884db` here and in mainline v2.6.30; `scripts/Kbuild.include` is
`da1c432cee107043` in both. **This is a 2009 kernel meeting a 2020 make**, and
it is the same class as `host-compat/0001` (perl 5.22 removed
`defined(@array)`) rather than anything a vendor did. The control is §2's:
the same comparison reports the top-level `Makefile` as 159 changed lines.

⚠️ **This is not a claim about GNU Make's history.** What is measured is what
make 4.3 does; when the behaviour changed, and whether 3.81 did something else,
is not established here and nothing below depends on it.

### 5.4 The second prediction block, scored

Written before the run, in `inc-exp2.sh`'s header:

| # | prediction | outcome |
|---|---|---|
| **P12a** | the `#` fix ALONE gives a no-op `CC` count strictly between 0 and 599; 猜 near 580 | 🔴 **refuted, and in the good direction.** **2**, not ~580. So the header rewrite was a *symptom of the same cause*, not a second cause: with `arg-check` working, `kernel/bounds.s` is no longer regenerated, so `bounds.h`'s rule never runs |
| **P12b** | both patches give 0 `CC` | 🔴 refuted at the letter, held in substance: **2**, and identical to P12a — `0003` adds nothing to this case |
| **P13** | the `.cmd` holds `$(pound)` and no bare `#`, and what make loads matches | 🟢 **held.** Before: raw 1,131 / loaded 1,023 / 1 bare `#` / no `$(pound)`. After: raw 1,138 / loaded 1,130 / **0** bare `#` / **1** `$(pound)`. The 7-byte growth is `$(pound)` replacing one character, exactly |
| **P14** | 猜 3–10 s | 🟢 **6.887 / 7.205 / 8.277 s** on the reused tree, 9.274 / 10.320 on a fresh one |
| **P15** | touching `init/main.c` gives 1 `CC` | ⚠️ **3**, and the two extras are named in §5.6 |
| **P16** | the incremental image differs only in `.version`'s two bytes | ⚠️ **54 bytes**, and §5.5 is why that is still `.version` and why the published bound needed correcting |

### 5.5 🔴 `L2-6`'s "two bytes" is the cost of a digit, not of the counter

`notes/reproducible-build.md` `L2-6` and `notes/dev-loop.md` §5.1 both record
`--keep`'s reproducibility cost as **two bytes**, measured on `#1` against
`#3`. 量 today, a ladder of consecutive links from one tree:

| pair | `.version` | differing bytes | sections |
|---|---|---:|---|
| `F1 → G1` | `#7 → #8` | 2 | `.data` `.rodata` |
| `G1 → F2` | `#8 → #9` | 2 | `.data` `.rodata` |
| **`F2 → G2`** | **`#9 → #10`** | **56** | `.data` `.rodata` **`.symtab`** |
| `G2 → G2b` | `#10 → #11` | 2 | `.data` `.rodata` |
| `A → H` | `#1 → #12` | 54 | `.data` `.rodata` `.symtab` |

**Two bytes is right only while the decimal rendering keeps its width.** The
counter is printed into `UTS_VERSION`, which sits in `linux_banner` and in
`init_uts_ns`; when it grows a digit the rest of both strings shifts, and one
`.symtab` byte moves with it. Nothing here is codegen — but *"the cost is two
bytes"* is a sentence that stops being true at the tenth link, and it was
published as if it were a bound.

### 5.6 What a no-op make still does, and why the floor is not zero

After both patches, a no-op `make vmlinux` is **2 `CC`, 8 `LD`, 6.9–10.3 s**,
and it is stable across repeats. The two objects are named:

* `init/version.o` — 🔴 **the build perturbs itself.** Every link bumps
  `.version`; `scripts/mkcompile_h` writes it into `include/linux/compile.h`,
  which it *does* content-check — and the content changed, so it updates;
  `version.o` includes it, so the next make recompiles it and relinks, which
  bumps `.version` again. The loop is a fixed point at one object, and no
  amount of dependency fixing removes it.
* `drivers/net/wireless/rtl8192cd/8192cd_hw.o` — its source `#include`s ten
  `data_*.c` files that Realtek's own makefile regenerates on every build
  (`data_MAC_REG_88E.c`, `data_PHY_REG_1T_88E.c`, and eight more). This one is
  the vendor's, and it costs one object.

The eight `LD` lines are the built-in.o chain those two force, up to `vmlinux`.

### 5.7 🟢 So `0003` is kept, and the measurement is what kept it

With `arg-check` fixed, `0003` is worth nothing on a no-op make — P12a and
P12b are both 2. It was very nearly dropped on that. 量, one tree, one
variable:

| trigger | with `0003` | without `0003` |
|---|---|---|
| `touch kernel/bounds.c`, then make | **3 `CC`, 6.9 s** | **573 `CC`, 26.3 s** |
| reverting `0003` (which touches `Kbuild`) | — | 572 `CC`, 26.5 s |

`kernel/bounds.s` is regenerated whenever `kernel/bounds.c` or one of the four
headers it includes changes, or whenever the top-level `Kbuild` is touched, and
`$(call cmd,bounds)` then rewrites `bounds.h` unconditionally with identical
content, taking 572 objects with it. **`0003`'s value is not the no-op case; it
is that one edit to a core header costs 3 compilations instead of 573.**
`R5` is six kernel drivers, so that trigger is not hypothetical.

### 5.8 The product is unchanged, and the four bytes that move are the recipe id

量, a fresh stage with `0004` declared against `vmlinux.A` built without it,
both at `.version = 1`:

```
differing bytes: 4 of 3968240  (0.000101 %)
1 run(s)
--- 0x2af5e6..0x2af5ef  4 byte(s)  sec=.init.text  sym=start_kernel+0x7e
```

That is `RLXFW_SRC_ID`'s `lui`/`ori` immediate pair. It moved because
`rlxfw-kbuild.sh` computes `RECIPE_ID` as a sha256 over every file under
`config/` and `config/` gained a file: `d31f60bd → c601eacf`. **Every other
byte of 3,968,240 is identical** — the patch changes when kbuild re-runs a
command, never what the command is.

⚠️ **Two committed lines name `d31f60bd` and stay true**: `notes/dev-loop.md`
§4 and `SPEC.md` `TC-40` both date it to 2026-09-01 and describe that
measurement's recipe. A build after this commit has a different id, which is
what `ID0` exists to say.

### 5.9 The commit gate: the unmodified driver, a fresh stage, both patches

Everything above was measured by applying and reverting patches inside one
staged tree, which is the right shape for a causal claim and the wrong shape
for *"is this safe to commit"*. So the last run is the ordinary driver, from
the real repository, with both patches sitting in `config/host-compat/` where
`rlxfw-kbuild.sh` finds them — and a patch that does not apply **stops the
build**, which is what makes this a gate rather than a report.

| # | prediction | 量 |
|---|---|---|
| **V1** | the driver reports 4 declared patches and exits 0 | 🟢 `applied 4 declared host-compat patch(es)`, rc=0, 36.36 s, recipe `d31f60bd → b1434383` |
| **V2** | the full build is 594 `CC`, not 599 | 🟢 **594**, and the only object compiled twice is `init/version.o` — the five `init/` duplicates are gone |
| **V3** | the image differs from `vmlinux.A` in only the `RLXFW_SRC_ID` immediate | 🟢 **4 bytes of 3,968,240, one run, `.init.text`, `start_kernel+0x7e`** |
| **V4** | a no-op make in the fresh tree: 2 `CC`, under 12 s | 🟢 **2 `CC`, 8 `LD`, 7.192 / 8.475 s** |
| **V5** | `touch kernel/bounds.c` gives 3 `CC`, because `0003` is in | 🟢 **3** — `kernel/bounds.s`, `8192cd_hw.o`, `init/version.o` — 6.889 s |

⚠️ `CHK` reads **6** on a full build and **4** on a no-op, which is the two new
`filechk` rules not running at all when their `.s` prerequisite has not moved.
That is the intended behaviour and it is worth naming, because *"the check
count went down"* looks like a regression and is the opposite.

---

## 6. What this decides, and what it does not

**Decided:**

1. 🟢 **The full rebuild has one root cause and it is a two-line fix.** A no-op
   `make vmlinux` goes **599 `CC` / 28.0–32.1 s → 2 `CC` / 6.9–10.3 s**, and a
   *full* build goes 599 → 594, because the broken comparison was compiling
   five `init/` objects a second time inside every build.
2. 🟢 **It changes nothing about the product**, 4 bytes of recipe id excepted,
   and those are by design.
3. 🟢 **`LOOP-1`'s diagnosis is refuted and replaced.** The header rewrite was
   downstream of the same cause. `0003` is kept for a different, measured
   reason (§5.7).
4. 🔴 **`L2-6`'s two-byte bound is corrected** to *two bytes while the digit
   count holds, 54–56 across a digit boundary.*

**Not decided, and the first one is the whole point:**

* 🔴 **This buys nothing on the loop's default path, and the reason is
  structural.** `rlxfw-kbuild.sh` re-stages 480 MB for every build; a fresh
  stage has no object files, so every object is compiled whatever kbuild
  decides. The saving is only reachable on a **reused** tree, which is
  `--keep`, which `R4`'s stop-loss fences off — *"`--keep` may not be turned on
  to hit a number"*. **It is not turned on here.** What this file establishes
  is the number a decision would be made against, and the decision is the
  owner's:

  | | fresh stage every build (today) | reused tree |
  |---|---|---|
  | `make` phase, no-op | 28.0–32.1 s | **6.9–10.3 s** |
  | reproducible byte-for-byte | 🟢 yes, 7 replications | 🔴 no — `.version`, 2 bytes, 54–56 across a digit |
  | `--marks` usable | 🟢 yes | 🔴 **refused** — `rlxfw-marks.py` will not re-apply to an unclean tree |

  ⚠️ The third row is the one that matters and it is not a preference: today's
  recipe *cannot* run on a reused tree at all. Any adoption needs
  `rlxfw-marks.py` to gain an idempotent path first, and that is not this
  step's work.

* ⚠️ **What an incremental build of a REAL edit costs is still not measured.**
  Touching a file is not editing it; every number above is a no-op or a
  `touch`. The first honest reading of *edit → result* on a reused tree comes
  from `tools/looprun.py`, not from here.
* ⚠️ **`8192cd_hw.o`'s per-build recompilation is not chased.** One object.
* ⚠️ **`init/version.o`'s self-perturbation is not chased.** It is what makes
  the floor 2 instead of 0, and removing it means changing what the banner
  says, which is `P4a`'s territory and not this file's.

### 6.1 ⚠️ How far this generalises, and it is 推 rather than 量

Nothing above is specific to Realtek: the two files involved are byte-identical
to mainline v2.6.30, and the failing escape is in `scripts/Kbuild.include`,
which every kernel of that era ships. **So the inference is that any kernel old
enough to carry the `$(subst \#,\\\#,…)` form of `make-cmd`, built with a make
new enough to treat `\#` the way 4.3 does, loses `arg-check` entirely and rebuilds
everything on every invocation.** That would be a large class of embedded vendor
trees.

🔴 **It is an inference and this file does not measure it.** What is measured is
one tree and one make: `linux-2.6.30` as three GPL drops ship it, under GNU Make
4.3 on WSL2 Ubuntu 24.04. Three things would each falsify or bound the
generalisation and none has been done here:

* **which make version changed the behaviour.** §5.3 says explicitly that this
  is not established. A second make — 3.81, 4.0, 4.2 — on the same tree would
  bound it, and it costs one `apt` and one no-op build;
* **when mainline replaced `make-cmd`.** The `$(pound)` form is in current
  mainline; the commit that introduced it, and therefore which kernels are
  already safe, was not looked up;
* **whether `-D"KBUILD_STR(s)=…"` is the only source of a bare `#`.** It is the
  one this tree hits. A command line carrying a `#` for any other reason would
  fail the same way, and no census of that was taken.

It is written down because *"this is probably not just us"* is a useful thing
for a reader to know and a dangerous thing to state as a finding. **The claim
this file makes is about this tree.**

---

## 7. 🔴 `INC-1`, measured 2026-09-02 (`R5-0`): one real edit costs a full build, and the cause is this project's own identity string

§ 5 and § 6 measured no-ops and `touch`es. `INC-1` was carried forward because
**the cost of one REAL edit on a reused tree had never been measured**, and
`R5` is ~24 segments of exactly that edit.

Two things had to exist before it could be run at all:

* **`rlxfw-marks.py --if-needed`.** `A4` refuses a second `apply` on one tree,
  because applying twice emits the mark twice and a doubled mark reads in a
  capture as a boot loop. So `--keep --marks` could not run. The fix is
  **three states rather than two** — `clean` applies, fully-`applied` is a
  no-op, and 🔴 **`partial` is refused**, which is the state `A4` was guarding
  and the one an "already there, call it success" patch would have laundered.
  `A18`–`A22` are those states; `A20` requires the plain `apply` to *still*
  refuse, so `A4` is bypassed only when asked.
* **`_copy_if_different`.** `apply` used to `shutil.copyfile` my sources
  unconditionally. kbuild triggers on mtime, so that puts a floor under every
  incremental measurement — and `INC-1` is a measurement of that floor.
  `A23`/`A24` are the two halves.

### 7.1 The hypothesis, written before the run

`R5`'s drivers live under `config/rlxfw-src/`. `RECIPE_ID` is a sha256 over
**every file under `config/`**, and `rlxfw-kbuild.sh` passes it as
`KCPPFLAGS=-DRLXFW_SRC_ID=0x<id>`, which `Makefile:572` appends to
`KBUILD_CPPFLAGS` — so it reaches **every C object's command line**. Since
`0004` fixed the truncated `.cmd` files, kbuild's arg-check works.

> **H1** — editing a driver source rebuilds **all** objects, because
> `RECIPE_ID` moved and every command line moved with it.
> **H0** (null) — only the edited object rebuilds, ~3 `CC`.
> **Refutation of the run itself**: `S1`, a no-op on the reused tree, must
> reproduce § 5's known **2 `CC`**. If it does not, the tree is not in the
> state the earlier numbers were taken in and nothing below is comparable.

### 7.2 The reading

量 2026-09-02, cell `inc1`, `-j4`, this host.

| | what | s | `CC` | `LD` | `RECIPE_ID` |
|---|---|---:|---:|---:|---|
| `S0` | fresh stage + full build, `--marks` | 42.56 | 592 | 118 | `6664f2f5` |
| `S1` | `--keep --marks`, nothing changed | 11.98 | **2** | 8 | `6664f2f5` |
| `S2` | **edit `config/rlxfw-src/…/rlxfw_mark.c`**, `--keep --marks` | **32.58** | **592** | 77 | **`449cd25e`** |
| `S3` | revert `config/`, `--keep --marks` | 40.90 | 592 | 77 | `6664f2f5` |
| `S4` | **edit the STAGED copy**, `--keep`, no `--marks` | **11.75** | **3** | 9 | `6664f2f5` |
| `S5` | `--keep`, no `--marks`, nothing changed | 11.69 | 2 | 8 | `6664f2f5` |

🟢 **The refutation held**: `S1` is 2 `CC`, exactly § 5.6's floor.

🔴 **H1 holds and H0 is refuted.** `S2` rebuilds **592 objects — the whole
tree** — for a one-line edit.

🟢 **And `S2` against `S4` is the isolation, single-variable**: the *same
edit*, made where `RECIPE_ID` does not move, is **3 `CC` / 11.75 s**. The
factor between them is **197× in objects and 2.8× in wall-clock**, and it is
entirely `RECIPE_ID`.

**So `--keep` buys nothing for an `R5` iteration, and the reason is not the
build system — it is this project's own identity string.** `notes/dev-loop.md`
§ 5 said *"this tree has no incremental build at all"*; that was right about
the cause it named and it was not the whole cause.

### 7.3 `INC-2`: confining the define, and the product it must not move

The staged tree has **exactly one** consumer of the macro —
`init/main.c:576`, the `ID0` row of `config/rlxfw-marks.tsv` — so the define
does not need to be global. `--id-scope main` passes it as `CFLAGS_main.o`.
`global` stays the default, because it is what every measurement so far was
taken under.

Predictions, written before the run: `P1` the first `main`-scope build rebuilds
everything (a settling run, not a reading); `P2` a no-op after it is 2 `CC`;
`P3` a real edit is a handful; 🔴 `P4` **`vmlinux` is byte-identical between the
two scopes**, refuted by any difference — which would mean something here
compiles differently depending on whether the macro is *defined*; `P5` the
`RLXFW-ID0=` string survives.

| | s | `CC` | note |
|---|---:|---:|---|
| `T0` `--id-scope main`, first | 34.94 | 591 | settling, as `P1` predicted |
| `T1` no-op | 14.66 | **2** | `P2` 🟢 |
| `T2` **edit `config/`** | **12.53** | **4** | `P3` 🟢 — against 592 / 32.58 s |
| `T3` revert | 12.03 | 4 | |

🟢 **`P3` holds: the same real edit is 4 `CC` / 12.53 s under `--id-scope
main`.** The four are `init/main.o` (the moved define), `rlxfw_mark.o` (the
edit), and the two of § 5.6's floor.

🔴 **`P4` was refuted, and the refutation was the experiment's fault, not the
flag's.** It compared two *incremental* builds — and 量: an incremental build
does not reproduce its own product either. `T1`, a **2 `CC` no-op** at the same
recipe and the same scope, produced a different `vmlinux` from the build before
it.

**Cause, then measured rather than assumed**: `linux-2.6.30/.version` is a
build counter incremented at each link and reaching the image through
`UTS_VERSION`'s `#N`. 量: `11 → 12 → 13` across two no-op builds, images
differing each time.

### 7.4 `P4` restated, and the answer

Two **fresh stages** of the same recipe, one per scope. Both start with
`.version` absent, so the counter is equal and the comparison is
single-variable.

| | `CC` | `.version` | `RECIPE_ID` | sha256 of `vmlinux` |
|---|---:|---:|---|---|
| `--id-scope global` | 592 | 1 | `b1434383` | `04545dd254a1b136…` |
| `--id-scope main` | 592 | 1 | `b1434383` | `04545dd254a1b136…` |

🟢 **Byte-identical.** The 591 objects that lose the `-D` never referenced it,
and `P5` holds — `rlxfw-marks verify` reads `RLXFW-ID0=` present once in mine.

⚠️ **`--id-scope main` is not turned on by default and no gate uses it yet.**
`looprun`'s `S2` re-stages, where the scope changes nothing; the win is in the
**desk** iteration, which is where `R5` will live. Turning it on is `INC-2`,
carried forward, and it arrives with a fresh-stage product comparison in the
same commit or it does not arrive — the same condition `P4a`'s `L2-6` put on
`--keep`.

### 7.5 What this section does not establish

* ⚠️ **The stimulus was an added comment line.** kbuild triggers on mtime and
  on the command line and reads no file contents, so a comment and a real
  statement are the same stimulus *to it* — the `CC` counts carry over. The
  **seconds** do not: a real edit gives the compiler more to do, so every
  wall-clock number here is a lower bound.
* ⚠️ **One file, in `arch/rlx/kernel/`.** A driver under `drivers/` sits one
  `built-in.o` aggregation deeper. Same order of magnitude, 推, not measured.
  🔄 **2026-09-03: that file now exists** —
  `config/rlxfw-src/linux-2.6.30/drivers/clocksource/rtl819x-timer.c`, `R5-1` —
  **and the measurement still has not been taken.** `R5-1` ran fresh stages
  only (593 / 595 / 596 / 597 `CC`); no `--keep` incremental cycle was run on
  it, so this row stays 推 with its subject now available rather than
  hypothetical. `INC-2`'s `--id-scope main` is what would make it cheap.
* 🔴 **`.version` means an incremental build is never reproducible**, whatever
  the scope. Every reproducibility claim in `notes/reproducible-build.md` is a
  fresh-stage claim and stays one.
