# probe6's build — what is different about it, and the three defects it exposed

`probe6` is the only payload in `tools/rlxprobe/` whose objects are not all
built by the same compiler. Ten of them — one per compiled row of
`tools/isa-toolchain.tsv` — are built by a driver that is *under test*, and
everything else is built by the host cross-compiler at `-march=mips1`, the
configuration every payload that has ever executed on this die was built with.

That one difference is the whole of this note.

---

## 1. Why the framework is not built by the thing under test

An instrument built out of its own subject cannot separate *the fragment
computed the wrong value* from *the reporting path computed the wrong value*.
So `start.S`, `uart.S`, `report.c`, `cache.S`, `exc.S`, `p6support.S`,
`cells6.S`, `probe6rows.c` and `probe6.c` are all `$(CC)` at `$(ARCH)`, and only
`frag.c` is compiled by `$(P6_CC_<vid>)` at that row's `-march`.

`tools/rlxprobe/Makefile`'s `SRC_probe6` therefore does **not** list `frag.c`.
The fragment objects are named by `FRAGOBJS_probe6`, generated into
`probe6rows.mk`, and added to the link line separately.

---

## 2. 🔴 The `.flags` stamp did not cover `CROSS` or `ARCH`

量 2026-09-14, by reading the Makefile before the first toolchain build.

The stamp existed and its comment already described this defect class twice —
`RESULT_BASE` (measured 2026-08-25) and `LOADADDR` — but it read

```
$(DEFS) LOADADDR=$(LOADADDR) STACK_SIZE=$(STACK_SIZE)
```

Neither `CROSS` nor `ARCH` reaches a `-D`, and both reach every object: `CROSS`
selects the compiler, and `ARCH` reaches `CFLAGS`, `ASFLAGS` **and** `LDFLAGS`.
So `make CROSS=… ARCH=…` in a directory that already held a build relinked
nothing and shipped the previous toolchain's binary, **while `make show`
printed the toolchain that had been asked for beside it**.

🔴 **On a toolchain-comparison seating that is the single most likely way to
publish a false disagreement**, because those are the two knobs the experiment
varies by construction. Both are in the stamp now.

⚠️ `probe6` itself does not rely on the fix: its fragment objects have
per-variant paths (`$(OBJDIR)/frag-<vid>.o`) and per-variant recipes, so two
variants can never be one file. Every *other* payload did rely on a stamp that
could not see those two knobs.

---

## 3. 🔴 A 32-bit vendor driver cannot read a source file on DrvFs

`SPEC.md` `TC-56`. 量 2026-09-14, one variable and one control:

| the file is on | result |
|---|---|
| `/mnt/c` (DrvFs) | `cc1: …/frag.c: Value too large for defined data type` |
| ext4 | a 928-byte object |

`bin/mips-linux-gcc` is an `ELF 32-bit LSB executable, Intel 80386`. DrvFs hands
it inode **49539595901085916**, which does not fit a 32-bit `struct stat`, so
`stat()` returns `EOVERFLOW` and `cc1` reports it against the filename. The ext4
copy's inode is **77448**.

🔴 **The message names the source file and reads like a defect in it.** That is
why the repair is a *named refusal* rather than a comment: `tcpay.py` emits, into
`probe6rows.mk`,

* a `$(error …)` that fires at parse time if `$(abspath $(BUILD))` is under
  `/mnt/`, carrying the cause and the fix in its text; and
* a rule that copies `frag.c` into `$(OBJDIR)` so the fragment is compiled from
  a path on the same filesystem as the output.

**So `probe6` cannot be built into the in-repo `tools/rlxprobe/build/`
directory**, which is on DrvFs. Pass `BUILD=$FWRE_WORK/rebuild/<something>`.

This is the third face of `CLAUDE.md`'s *binaries and vendor source trees never
live under `/mnt/c`*. The first two are git not seeing mode changes and NTFS
case-insensitivity dropping 254 files; this one is a vendor binary being unable
to **read** a file there at all.

---

## 4. 🔴 An unkeyed variable in an unconditionally-included makefile

`probe6rows.mk` is `-include`d by `tools/rlxprobe/Makefile` for **every**
payload, because make has no way to include it conditionally on `$(P)` without
also losing it from `probe6`'s own parse. So a variable named `P6_FRAGOBJS`
would have been in scope for `probe0`…`probe5` as well, and the link line would
have pulled ten foreign objects into an unrelated image.

It is `FRAGOBJS_probe6`, read as `$(FRAGOBJS_$(P))` — the idiom `GENHDR_$(P)`
already uses, for the same reason. Caught by review before the first build;
`tcpay.py`'s `T13` pins it in both directions (the keyed name must be present,
the unkeyed one must be absent).

---

## 5. 🔴 A rule's target line is expanded when make READS it

`probe4rows.mk` and `probe5rows.mk` hold only variables, so they are included
early, beside the other payload tables. `probe6rows.mk` holds **rules**, and a
rule's target line is expanded immediately — so at that point, where `OBJDIR`
has not been assigned yet, every fragment object's target came out as
`/frag-<vid>.o` and the build died with

```
Assembler messages:
Fatal error: can't create /frag-v1.o: Permission denied
```

It is included after `OBJDIR := $(BUILD)/$(P)`, with a note at the old position
saying why it is not there.

⚠️ This one was found by building, not by review — and the reason review missed
it is that the two existing `.mk` files establish a position that is correct for
what they contain and wrong for what this one contains.

---

## 6. The gate

`make P=probe6` runs `tools/tcpay.py gate`, not `tools/hazlint` directly and not
`tools/hazdecl.py`.

`hazdecl.py` is `probe5`'s and cannot be reused: its `P5`…`P12` read `hazpay`'s
row table and `isa-hazard.tsv`'s declared distances. `tcpay gate` is the same
*resolution* — `hazdecl`'s option ③, the unmodified `hazlint` over the whole
linked image with no flag restricting what it scans, adjudicated in both
directions — re-implemented against `isa-toolchain.tsv`, plus `G8`, which reads
the instruction words out of the ELF and does not use `hazlint` at all.

**`hazlint` exiting 0 is a build failure here**, as it is for `probe5`: it would
mean every `nopad` variant had been padded and the experiment is not in the
image.

First run, 2026-09-14:

```
hazlint rc=1  loads=139  unresolved=0  violations=7  parsed=7
declared nopad sites: 7   pad sites: 5
G1..G8 clean
```
