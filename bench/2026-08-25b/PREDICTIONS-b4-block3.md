# PREDICTIONS — Session B4, `R1g-4b`, block 3: `probe2` a second time

**Written at the bench, after run 1's block was recovered on both channels and
before run 2 is launched.**

**Why it runs.** Run 1 answered `R1e`. It cannot say whether the answers are
*reproducible*, and one of them — `moves = 8` on `rd 1` — is the **positive
control that makes every `S_ZERO` in the census mean anything**. If `Random`'s
sixteen values come back **identical**, then `Random` is not free-running: it is
a deterministic function of the code path, `S_MOVES` is an artefact of two reads
at fixed points in a fixed sequence, and *`Count` does not move* stops being
falsifiable. **That is the refutation condition of this block and it is the whole
reason to spend the cell.**

**Cost if it hangs: nothing already earned.** Run 1's block is on disk on both
channels (`bench/2026-08-25b/H2a.log`, `H2g.log`), the payload is unchanged in
DRAM at `0x80500000`, and `rlx_reset` has handed the prompt back twice tonight.

## Cells, in order

```cells
bench/2026-08-25b/H2a2
bench/2026-08-25b/flush-h2a2
bench/2026-08-25b/H2g2-hdr
```

| # | cell | command | bytes |
|---:|---|---|---:|
| 1 | `H2a2` | `--send 'J 80500000' --esc-after 60 --esc-period 0.002 --seconds 120` | report **2,909** if `rows.printed=39` |
| 2 | `flush-h2a2` | `--send '' --seconds 2` | 11, a bare prompt |
| 3 | `H2g2-hdr` | `--send 'DW 80A01000 88' --seconds 8` | **1,059** — the 40 header words **plus rows `0x00`–`0x0f`**, i.e. all eight `Random` rows at words 64–87 |

---

## What must be BYTE-IDENTICAL to run 1

If any of these moves, it is a fact about the machine and not about the payload,
because the payload is the same 9,392 bytes at the same address.

| field | run 1 | why it must not move |
|---|---|---|
| `pc=` | `80501054` | linked address, not state |
| `rb=` `flags=` `vec=` | `80a01000` `50010002` `80000080` | build constants |
| `handler_words=` | `00000016` | |
| `install.bad=` | `00000000` | |
| `break.count=` `break.cause=` `break.epc=` | `00000001` `00000024` `80500270` | `break` is at a fixed address and traps every time |
| `traps=` `nowrite=` `mixed=` | `00000000` ×3 | **`nowrite` is the load-bearing one**: it is what makes run 1's `zeros=208` a real zero rather than *the destination was never written* |
| `values=` `zeros=` `moves=` | `00000028` `000000d0` `00000008` | the partition of the 32 registers is a property of the core |
| `rows.printed=` `rows.suppressed=` | `00000027` `00000000` | |
| `count.*` | `000186a0` `0` `0` `0` `0` `0` | `F50b`. **A different answer here refutes run 1's**, and one of the two is then wrong |
| `restore.mismatch=` `restore.stillhandler=` | `00000000` `00000000` | |
| `status=` `status_end=` | `1000fc00` `1000fc00` | ⚠️ **this one is genuinely a prediction and not a tautology.** Run 1 read `Status` after a **cold** boot; run 2 reads it after a **watchdog reset**. A difference is a finding about the warm-boot path, and `CPU-27` would then need both readings |

### 🔴 `install.changed = 0000002b` again, and it is a third instrument on the restore

Not a tautology either. After the watchdog reset:

* `trap_init` re-wrote the **general** vector, so it holds `H0a` again → **21**;
* nothing on a warm reset writes the **UTLB** vector, so it holds whatever
  `probe2` restored → **22**, *if and only if the restore really put this boot's
  bias back*.

`restore.mismatch = 0` said so from inside the payload and `H2h-utlb` said so
from the loader. **`install.changed = 43` on run 2 says it a third time, through
the arithmetic rather than through a comparison.** Anything other than `0000002b`
means the page is not what run 1 left, and `H2h-utlb`'s identity would then be
the reading in doubt.

---

## 🔴 What must DIFFER, and this is the cell

| | run 1 | prediction for run 2 |
|---|---|---|
| `rd 1` rows `0x08`–`0x0f`, sixteen values | `0a00 1100 / 0900 1000 / 1d00 0800 / 1500 1c00 / 0600 0d00 / 1a00 0500 / 1200 1900 / 1100 1800` | 🔴 **a different set.** Every value in `(v >> 8) & 0x3F` ∈ `0..31`, `state = 00000004` on all eight |
| `sum=` | `ec84408d` | **different**, because the `Random` values are inside the summed region |

**Refutation, written before the run:**

* **All sixteen identical → `Random` is not free-running on this core.** The
  `S_MOVES` mechanism is then measuring a fixed sequence, run 1's positive
  control is void, and every `S_ZERO` in the census — including `Count`'s, which
  is `F50b` — loses its falsifier. `R1e` would close with `F50b` recorded 未定
  rather than answered.
* **Some identical, some not** → report as its own reading. It is neither
  free-running nor fixed, and nothing here explains it.
* **`sum` identical while the `rd 1` values differ** → the seal does not cover
  what it is supposed to cover, and `H2g`'s two-channel agreement is worth less
  than it looked.

⚠️ **`Random`'s range is a second, weaker reading.** Run 1's sixteen values span
5..29 within `0..31`. `CPU-08` holds **32 TLB entries, 量**. A run-2 value ≥ 32
would refute the 32-entry reading; a combined span across both runs that stays
inside `0..31` corroborates it by a route that has nothing to do with the TLB
probe that measured it.

---

## The seal, and the trap in it

🔴 **A straight re-sum of words 0–807 does NOT equal word 808**, and it is not a
corruption. 量 tonight on run 1: the re-sum is `EC84409D` against a stored
`EC84408D`, high by exactly **`0x10`**. `probe2.c` computes the sum, writes it at
word 808, and **then** calls `progress(P_SEALED)` — so word 2 held `P_RESTORED`
(`0x80`) when the sum was taken, not `P_SEALED` (`0x90`). Re-summing with word 2
forced to `0x80` gives `EC84408D`, exact.

Anyone verifying this block — including `R1g-5`'s write-up — must subtract
`P_SEALED − P_RESTORED = 0x10`, or the block reads as corrupt on every complete
run.

---

## What this block does not do

- It does not re-measure `CPU-25`. `Config` read `00000000` on run 1, so
  `Config.M = 0` and there is no `Config1`; the geometry is not in CP0 on this
  core, and the only remaining route is a `probe3` eviction walk at the desk.
- It writes no flash and no new bytes to DRAM outside `probe2`'s own block, the
  two vector pages and its `.bss`. `H2i-below` measured the lower bound on run 1.
- It does not change what `R1e` concluded. It can only leave those conclusions
  standing or take the positive control out from under them.
