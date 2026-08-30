# CORRECTIONS — Session B5, block 3 (seating 7, 2026-08-31, two power cycles)

**`PREDICTIONS-B5-block3.md` is frozen from the moment `W-A.log` landed.**
Everything below corrects it from here, in the order the seating found each one.
Nine items; **six are defects in the card or in an instrument of mine, three are
findings about the device.**

The seating's own gates: block 3 **42 of 54** (the twelve are §5's voided
bracket and §6's two moved captures), blocks 3b/3c/3d/3e **18 of 18**.

---

## 1. 🔴 `M-b` / `M-c` — refuted, and the premise was wrong at the desk

**Predicted** `␣␣␣␣␣4422␣␣␣1245184`, 45 bytes. **Measured**
`/bin/sh: wc: not found`, **48 bytes**, in 0.037 s.

Card §7.2 justified the cell with *"the binary's applet table lists 50 names and
`wc` is one of them"*. That is a true statement about `busybox` and the cell
needed a true statement about **the image**. 讀 `config/rlxfw-initramfs.tsv`:
eleven symlinks point at busybox — `sh ash cat echo ls mount ps ifconfig ping
mkdir sleep` — and `wc` is not one.

> **The applet table and the symlink set are two different populations, and
> nothing in this repository compares a card's typed commands against the
> declaration of the image that card uploads.**

`FW-26` is not wrong. What is missing is a check, and it is the same shape as
the carried-forward row *a declaration ahead of every artefact* — there a
declared node was in no built image; here a **used command** is in no
declaration.

**Recovered** in `PREDICTIONS-B5-block3b.md`, written before the recovery ran:
`busybox wc -lc` gave **`␣␣␣␣␣4422␣␣␣1245184`** and
**`␣␣␣␣␣7943␣␣␣2949120`**, 53 bytes each, both exact. Repeated on cycle 6
(`X-b2`/`X-c2`, block 3c) — identical.

⚠️ **`M-b`/`M-c` stay refuted.** The recovery cells are a different command and
are recorded as their own cells.

## 2. 🟢 What the recovered cells settled, which was the point of the change

The whole **4,194,304 bytes** were read through `mtd_read` → `part_read` →
`rtl819x_flash`, and the newline counts match the 2026-08-16 dump exactly on
both partitions and on both power cycles.

Block 3 §7.2a named the live alternative — `rtl8196_map_copy_from` caps a copy
at 1024 bytes and returns `void`, so a short read reports success — and
predicted it was dead code because `CONFIG_MTD_COMPLEX_MAPPINGS` is unset in all
31 built configs. **H1 would have given ≤1228 and ≤2007. H0 is what came back,
four times.**

⚠️ Still not a byte comparison and it does not move `FLS-20`.

## 3. 🔴 The read rate was wrong by a factor of ~16, and the correction is a measurement

Card §7.2 sized the terminators on `CLK-15`'s **59.8 KB/s**, marked 推, with
45 s and 100 s at roughly 2×.

量, four reads, from the wire-silent gap in each `.timing`:

| | `M-b2` | `X-b2` | `M-c2` | `X-c2` |
|---|---:|---:|---:|---:|
| gap | 1.356 s | 1.230 s | 2.959 s | 2.933 s |
| rate | 918.6 KB/s | 1012.4 KB/s | 996.6 KB/s | 1005.6 KB/s |

**≈ 0.92–1.01 MB/s.** The terminators were over-provisioned by an order of
magnitude — harmless, and now a 量 rather than a 推.

🔴 **And block 3c's own rate band is REFUTED.** It predicted 1.30–1.45 s for
`mtd0` from `M-b2` alone; `X-b2` returned **1.230 s**, outside it. Written
before the number was seen, which is why it can be reported as a refutation
instead of a widened band. **A band drawn from n=1 is a band drawn from one
sample of something with ~10 % spread.**

## 4. 🔴 `M-d` — 78 bytes, not 73, and the reason transfers to every shell cell

**Measured** `/bin/sh: can't create /dev/mtd0ro: Permission denied`.
The qemu measurement that sized the cell ran busybox with argv[0] = `sh`; on the
device `/bin/sh` is the symlink the shell was invoked through, and it prints
that. **+5 characters, exactly the difference.**

🟢 **The cell itself passed and it is the seating's most important pass**: the
kernel refused a write open on an odd minor, at zero flash bytes, because `open`
fails before any write is issued. `X-d1` (block 3e) repeated it on
`/dev/mtd1ro` — **78 bytes, exact** — so the `minor & 1` rule is now tested at
two points rather than one.

`X-d2` closed the other half: `busybox wc -c < /dev/mtd0` →
`/bin/sh: can't open /dev/mtd0: no such file`, **74 bytes, exact**. The even,
writable minor is **absent**, so `FW-30`'s *the declaration set is the whole node
set* is measured rather than argued.

⚠️ **`FW-30`'s sentence about a typo is true of a read and false of a write.**
`echo x > /dev/mtd0` would make the shell **create a regular file** — initramfs
is writable — which reaches no flash but is not the `No such file` that sentence
promises. Block 3e tests the read direction deliberately and says why.

## 5. 🔴 Cycle 6's bracket is VOID — DRAM retained cycle 5's contents

`X-p0`, `X-p6`, `X-ph`, `X-pc` all normalised **equal** to their flash
expectations, before any `FLR`. Block 3 §3 names that outcome exactly.

量, on the same prompt:

| address | last written by | reads |
|---|---|---|
| `0x80A00400`–`0x80A00700` | cycle 5's four `FLR`s | **the flash content, still** |
| `0x80A00800` / `0x80A00900` / `0x80A01000` | nothing, ever | uninitialised DRAM, 0 all-zero words of 80 |
| `0x805FB400` (`X-0t` line 2) | cycle 5's Linux | ASCII `start address: 0` |

**Retention of written data across the power cycle** — not a reset that did not
happen, since the never-written regions are still garbage.

🟢 **The pre-read control caught it on its first outing.** Without it cycle 6
would have reported four bracket passes that were RAM. That is precisely what
block 3 §3 was added for, firing the first time it ran.

🔴 **`X-ab` is not the control the card claims.** Its row says
*"`00000000` → this is **not** a fresh boot"*, and it did read `00000001`. But
`REG-23` is *every reset puts `AUTOBURN` back to `1`*: the cell separates *a
reset happened* from *no reset happened* and says nothing about DRAM decay.

⚠️ **It puts a doubt on `bench/2026-08-30c` block 2's second half**, which was
forced to reuse cycle 3's RAM destinations. If DRAM retained then as it did now,
those read-backs could have been RAM. **A doubt, not a refutation** — the `FLR`
echo was checked and `Flash Read Successed!` returned — and it is unprovable
from the captures that exist.

**Replaced** by `PREDICTIONS-B5-block3d.md` at `0x80A00800`–`0x80A00B00`, whose
pre-reads were verified to differ first. 12 of 12.

## 6. 🔴 The card sends `H601` pre-reads into `bench/`, and that is only safe when they miss

`W-ph`, `W-pc`, `X-ph`, `X-pc` are carded with `--out` under `bench/`, because a
pre-read is *expected* to be DRAM garbage. **That expectation is the cell's own
hypothesis.** When it failed, `X-ph.log` and `X-pc.log` contained this unit's MAC
and radio calibration, inside the repository.

> A containment rule whose correctness depends on the experiment coming out the
> expected way is not a containment rule.

**Contained**: both moved to `$FWRE_WORK/rebuild/bench-only/b5-20260831/`. 量
`git status` **before** the move — both were `??`, untracked, so nothing entered
history. Cycle 5's `W-ph`/`W-pc` genuinely differ from the expectations and are
safe. **Block 3d writes every `H601` capture, pre-read included, outside the
repository**, taking the carried-forward row *a capture that cannot be committed*
from four files to eight.

## 7. 🟢 What the moved bracket bought, which cycle 5's could not

Cycle 5's bracket ran **before** the `J`. Block 3d's ran **after** a complete
rlxfw run — boot, userspace, 4,194,304 bytes through `mtd_read`, an `EACCES`
write attempt, a ping.

All four windows: **differ from their fresh pre-read** (so the `FLR` wrote),
**identical to the 2026-08-16 dump**, and **identical to cycle 5's read-backs**.

> **First evidence in this project that a full boot of rlxfw leaves the flash
> byte-identical over the sampled windows.**

⚠️ 1,024 of 4,194,304 bytes. The forbidden sentence still needs a full re-dump
(`RUNSHEET` `G8b`).

## 8. 🔴 `W-A`'s "181-byte cold slice" is 179 invariant plus a variable prefix

量, anchored at `Booting...`: **179 bytes, byte-identical across all eleven
comparable cold captures** in `bench/`, `W-A` and `X-A` included. What varies is
the power-on line noise before it — **2, 3, 4 and once 2,816 bytes**.

The first comparison this seating ran did not anchor and reported **DIFFERS on
all thirteen**, including against a capture of the same total length. *A control
that fails on every member of its population is not a control*, and the anchor
is what made it one.

## 9. 🔴 An instrument of mine aborted a correct read

My `FLR` driver compared the echo against the **six**-digit source as typed;
the loader echoes it **zero-padded to eight** (`from 00000000 to 80A00400`) —
which is what the card's own §0 row says. So `W-flr0`'s echo was correct and the
checker rejected it, sent `N`, and got `Abort!`.

**Nothing was read and nothing changed.** Both captures are kept — `W-flr0a`
(the aborted echo, 104 bytes) and `W-no` (20 bytes) — and the abort path is now
exercised on real hardware for the first time, by accident rather than by design.

⚠️ `W-no` is deliberately not in block 3 §2's ordered list, so its ordering is
unenforced; it fired for a reason the card did not anticipate.
