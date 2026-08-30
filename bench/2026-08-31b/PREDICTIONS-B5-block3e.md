# PREDICTIONS — Session B5, block 3e: the safety property's second instance, and the control that the node set IS the declaration

**Written at the bench on 2026-08-31, board powered, shell up, BEFORE either
cell below was run.**

🔴 **Not to be edited after the first capture lands.**

---

## §1 Why two more cells

`M-d` returned `Permission denied` and that is the seating's stop-if control.
**One instance is an anecdote** — this repository's own words, from the
`flush-d3` row in `RUNSHEET` §D. `M-d` exercised `/dev/mtd0ro` (`c 90 1`); the
image also declares `/dev/mtd1ro` (`c 90 3`), and `mtd_open`'s rule is
`minor & 1`, so minor 3 must refuse for the same reason. **A rule tested at one
point is a rule tested at one point.**

The second cell is different in kind. `FW-30`'s claim is that **the declaration
set is the whole node set this image can ever have**, because `mknod` is not one
of the fifty applets. Nothing has tested the consequence: that an **even** minor
— the writable one — is simply absent.

⚠️ **It is tested on the READ side deliberately.** `echo x > /dev/mtd0` would
make the shell **create a regular file** — initramfs is writable — and that
would be a success that looks alarming while proving nothing, since a regular
file is not a device node and reaches no flash. `FW-30`'s sentence *"even a typo
`/dev/mtd0` only gets `No such file or directory`"* is therefore **true of a
read and false of a write**, and this block says so rather than testing the
wrong direction.

## §2 The cells

| # | typed | expect | bytes | 🔴 stop if |
|---|---|---|---:|---|
| **X-d1** | `CAP --out bench/2026-08-31b/X-d1 --send 'echo x > /dev/mtd1ro' --seconds 12` | `/bin/sh: can't create /dev/mtd1ro: Permission denied` | **78** | 🔴 **success is a stop-if**, exactly as `M-d`: an odd minor accepted a write open means `mtd_open` is not the code in this kernel |
| **X-d2** | `CAP --out bench/2026-08-31b/X-d2 --send 'busybox wc -c < /dev/mtd0' --seconds 12` | `/bin/sh: can't open /dev/mtd0: no such file` | **74** | a **number** comes back → an undeclared node exists and `FW-30`'s node-set claim is false. `Permission denied` → the node exists and is merely unreadable, which is a different and worse answer |

**Where the strings come from.** 量 2026-08-31 under `qemu-mips-static -L`
against this unit's own rootfs, through `tools/vendor-tripwire.sh`:

| shape | measured, as `sh` | on the device, as `/bin/sh` |
|---|---|---|
| unwritable existing target | `sh: can't create ./target: Permission denied` (44) | +5 for argv[0], +3 for the longer path = **52** |
| missing input path | `sh: can't open /nope/mtd0: no such file` (39) | +5 for argv[0], −1 for the shorter path = **43** |

🔴 **`can't open …: no such file` is busybox's own short message, not
`strerror`'s `No such file or directory`.** Predicting the `strerror` form would
have made this cell read as a miss. The negative control in the same run: a
redirect that succeeds prints nothing and the file gets the byte.

**Byte counts** by the framing model now confirmed on five captures
(`V-5a` 147, `V-5b` 111, `M-b` 48, `M-d` 78, `M-b2` 53):
`len(cmd) + 2 + len(reply) + 2 + 2`.
`X-d1`: 20 + 2 + 52 + 2 + 2 = **78** — and `M-d` measured exactly 78 for the
same shape at `mtd0ro`, which is this prediction's positive control.
`X-d2`: 25 + 2 + 43 + 2 + 2 = **74**.

## §3 Cells, in order

```cells
bench/2026-08-31b/X-d1
bench/2026-08-31b/X-d2
```

**Two cells.**
