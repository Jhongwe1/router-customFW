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
