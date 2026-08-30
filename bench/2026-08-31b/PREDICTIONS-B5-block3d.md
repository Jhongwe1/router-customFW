# PREDICTIONS — Session B5, block 3d: cycle 6's bracket, moved because DRAM retained cycle 5's

**Written at the bench on 2026-08-31, board powered, at the loader prompt,
BEFORE any cell below was run.** Block 3's cycle-6 bracket is **void by its own
stop-if** and this block replaces it at addresses that are not.

🔴 **Not to be edited after the first capture lands.**

---

## §1 What happened, in the order it was found

`X-p0`, `X-p6`, `X-ph`, `X-pc` read `0x80A00400`–`0x80A00700` before any `FLR`.
**All four normalised EQUAL to their flash expectations.** Block 3 §3 calls that
outcome exactly: *"the destination already holds the flash content and `X-rd0`
proves nothing"*, and *"it voids that one window for this seating"*.

量, straight after, on this same prompt:

| address | last written by | now reads |
|---|---|---|
| `0x80A00400`–`0x80A00700` | cycle 5's four `FLR`s | **the flash content, still** — `0x80A00400` re-read is byte-identical to `X-p0` and to `expect-000000` |
| `0x80A00800`, `0x80A00900`, `0x80A01000` | nothing, ever | uninitialised DRAM, 0 all-zero words of 80 |
| `0x805FB400` (`X-0t` line 2) | cycle 5's Linux | ASCII `start address: 0` |

**So this is retention of written data across the power cycle, not a reset that
did not happen.** The regions nobody wrote are still garbage; the regions cycle 5
wrote came back.

## §2 🔴 What that costs, beyond this block

**`X-ab` is not the control block 3 says it is.** Its row reads
*"`00000000` → this is **not** a fresh boot"*, and it did return `00000001`. But
`REG-23` is *every reset puts `AUTOBURN` back to `1`* — so the cell separates
*a reset happened* from *no reset happened*, and says **nothing** about whether
DRAM decayed. It cannot distinguish the boot this block is dealing with from a
cold one.

⚠️ **And it puts a doubt on block 2's second half.** `bench/2026-08-30c`'s cycle 4
was *forced* to reuse cycle 3's RAM destinations — its own §-note says so, and
`flashwin normalise` was written to lift that constraint. If DRAM retained then
as it did now, cycle 4's read-backs could have been RAM. **That is a doubt, not
a refutation**: the `FLR` echo was checked and `Flash Read Successed!` returned
both times, so the read very likely happened. It is unprovable from the captures
that exist, and it is the reason the pre-read was added.

🔴 **The `H601` pre-reads should never have been written under `bench/`.** Block 3
puts `W-ph`/`W-pc`/`X-ph`/`X-pc` in the repository because a pre-read is expected
to be garbage. **That expectation is the cell's own hypothesis**, and when it
fails the capture contains this unit's MAC and radio calibration. Today it
failed. `X-ph.log`/`X-pc.log` were moved out before anything else; 量 `git status`
first — both were untracked, so nothing entered history. **In this block every
`H601` capture, pre-read included, is written outside the repository.**

## §3 What the moved bracket buys that cycle 5's did not

Cycle 5's bracket ran **before** the `J`. This one runs **after** a complete run
of my kernel — boot, userspace, 4,194,304 bytes read through `mtd_read`, an
`EACCES` write attempt on `/dev/mtd0ro`, and a ping.

> **It is the first evidence in this project that a full boot of rlxfw leaves
> the flash byte-identical over the sampled windows.**

⚠️ It samples 1,024 of 4,194,304 bytes and cannot see a write outside them. The
forbidden sentence still needs a full re-dump (`RUNSHEET` `G8b`).

## §4 The cells

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0`.
`$B` = `/home/key/fwre-work/rebuild/bench-only/b5-20260831`.

| # | typed | expect | bytes | 🔴 stop if |
|---|---|---|---:|---|
| **X2-p0** | `CAP --out bench/2026-08-31b/X2-p0 --send 'DW 80A00800 64' --seconds 6` | DRAM. **Must NOT normalise equal to `expect-000000.txt`** | **777** | it matches → this address is retained too; move again and say so |
| **X2-p6** | `CAP --out bench/2026-08-31b/X2-p6 --send 'DW 80A00900 64' --seconds 6` | as above vs `expect-060000.txt` | **777** | as above |
| **X2-ph** 🔴 | `CAP --out $B/X2-ph --send 'DW 80A00A00 64' --seconds 6` | as above vs `expect-h601-6000.txt` | **777** | 🔴 **`--out` is NOT under `bench/`**, §2 |
| **X2-pc** 🔴 | `CAP --out $B/X2-pc --send 'DW 80A00B00 64' --seconds 6` | as above vs `expect-h601-6400.txt` | **777** | as above |
| **X2-flr0 / yes0 / rd0** | `FLR 80A00800 000000 100`, `Y`, `DW 80A00800 64` | echo reads `from 00000000 to 80A00800`; `Flash Read Successed!`; `X2-rd0` normalises equal to `expect-000000.txt`, to `W-rd0` and to `bench/2026-08-24d/G8a-rd0.log` | 104 / 35 / **777** | any difference → **STOP, do not `J`** |
| **X2-flr6 / yes6 / rd6** | `FLR 80A00900 060000 100`, `Y`, `DW 80A00900 64` | as above vs `expect-060000.txt`, `W-rd6`, `G8a-rd6.log` | 104 / 35 / **777** | as above |
| **X2-flrh / yesh / rdh** 🔴 | `FLR 80A00A00 006000 100`, `Y`, `DW 80A00A00 64` → **`$B/X2-rdh`** | normalises equal to `expect-h601-6000.txt` and to `W-rdh` | 104 / 35 / **777** | 🔴 not under `bench/` |
| **X2-flrc / yesc / rdc** 🔴 | `FLR 80A00B00 006400 100`, `Y`, `DW 80A00B00 64` → **`$B/X2-rdc`** | normalises equal to `expect-h601-6400.txt` and to `W-rdc` | 104 / 35 / **777** | 🔴 **the canary page.** A difference is a **finding**: my kernel wrote `H601`. Record it, do not `J` |

🔴 **The echo is checked by a machine, not by eye**, and the source is compared
**zero-padded to eight hex digits** — 量 today, the loader echoes
`from 00000000 to 80A00800` while the typed argument is six digits, and the
first version of that check aborted a correct read.

## §5 Cells, in order

```cells
bench/2026-08-31b/X2-p0
bench/2026-08-31b/X2-p6
bench/2026-08-31b/X2-flr0
bench/2026-08-31b/X2-yes0
bench/2026-08-31b/X2-rd0
bench/2026-08-31b/X2-flr6
bench/2026-08-31b/X2-yes6
bench/2026-08-31b/X2-rd6
bench/2026-08-31b/X2-flrh
bench/2026-08-31b/X2-yesh
bench/2026-08-31b/X2-flrc
bench/2026-08-31b/X2-yesc
```

**Twelve cells.** `X2-ph`, `X2-pc`, `X2-rdh`, `X2-rdc` are named in §4 and are
**deliberately not here**: they carry `H601` and are written outside the
repository, so `check-predictions.py` cannot see them and their ordering is
unenforced. That is the carried-forward row *a capture that cannot be committed*,
and this block takes it from four files to **eight**.
