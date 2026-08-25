# The cache model and the CP0 census on this core

**`R1-gate`'s closing statement.** The gate is `R1d` — the cache-management
model, on silicon — and `R1e` — the CP0 census. Both ran: `R1g-4a` on
2026-08-25 (`bench/2026-08-25/`) and `R1g-4b` on 2026-08-25b
(`bench/2026-08-25b/`), one power cycle each, zero flash bytes.

**Every statement below carries a mark**: **量** measured on this device ·
**讀** read out of code, a dump or a document · **推** inferred, pending a
measurement. Mixed together they are worth neither.

---

## What this file owns, and what it does not

House rule 1: one piece of state has exactly one owner. This file is new, and a
new file is where a second owner gets created by accident, so the boundary is
drawn first.

| | owns |
|---|---|
| **this file** | **the CP0 census as a reading** — what 256 rows say taken together, what they can and cannot tell apart — and **the four downstream decisions**, each with the measurement that decided it and the part it does not cover |
| `notes/cache-model.md` | **the cache-management model itself** and the CP0-20 (`CCTL`) command table: what the mechanism is, what each command value means, where each name comes from |
| `RUNSHEET.md` § Results B4 | **the seatings** — every raw reading, in the order it was taken, against the expected value written before it |
| `SPEC.md` | an index of the numbers. Not an owner of any of them |

Where this file repeats a number, it repeats it to make a decision legible, and
the owner above is what a disagreement is resolved against.

---

## The gate in one paragraph

**量** The I-cache on this core is real and goes stale; `CCTL 0x002` alone makes
freshly written instructions visible, twice, on two independent address ranges
and two store paths; `Status.IsC` does not isolate and its byte stores destroy
DRAM; `Status.BEV` is 0 and the core fetches its general exception vector from
`0x80000080`; `mfc0` always writes its destination; CP0 register 20 is a
write-only command register that reads back zero; `Config.M` is 0, so there is no
`Config1` and this is not a MIPS32-class CP0; the CP0 ignores the select field;
`rfe` balances the R3000 KU/IE stack; and **`Count` is not implemented**.
**Three of the gate's four decisions are settled by those readings. The fourth
is not, and the largest thing this write-up does is refuse to let it read as
settled.**

---

## The four decisions, each with the reading that decided it

These four are why the gate exists (`PROGRESS.md` § Step list). A gate closes
against them or it does not close.

| | decision | verdict | the reading that decided it |
|:-:|---|---|---|
| **①** | where `R5b`'s MTD driver has to flush | 🔴 **answered for the instruction side, and only that side** | `probe1` cells 2/3/6 all `02` FRESH; `probe2`'s handler install through KSEG1 with `install.bad = 0` and `break` trapping and returning |
| **②** | whether `R6`'s descriptor rings need an uncached window or a flush | 🔴 **未答 — unanswered** | none. `R1d` measured the CPU→memory direction for a *write miss* only, and measured nothing at all in the memory→CPU direction |
| **③** | whether `R1a`'s exception handler can live at `0x80000080` | 🔴 **yes** | `Status = 1000fc00`, bit 22 = 0; `break.count = 1`, `cause = 00000024`, `epc = 80500270` |
| **④** | whether `R5-0`'s SoC timer driver is a prerequisite or a bonus | 🔴 **prerequisite** | row `0x48` = `00000000` `S_ZERO`; `count.delta = 0` over a 100,000-iteration loop; `nowrite = 0` over all 256 rows |

### ① `R5b`'s MTD driver: the flush recipe, and the half of the driver it does not cover

**量, `bench/2026-08-25/H1b.log` + `H1c.log`, two channels, 104/104 row words
identical.** `probe1` cell 1 stores an instruction through the cached window and
applies no treatment; both of its victims came back `01` STALE — the old constant
executed while the new word was already in memory. That is the negative control,
and without it the other five cells would have passed untested. Cells 2
(`CCTL 0x002` alone), 3 (`0x200` then `0x002`) and 6 (`0x002`, stored uncached)
are all `02` FRESH on both victims.

**量, second and independent, `bench/2026-08-25b/H2a.log`.** `probe2` writes 44
words to `0x80000000` and `0x80000080` through KSEG1, invalidates with `0x002`
alone, reads all 44 back before it dares fault, and then faults: `install.bad =
0`, `install.changed = 0000002b`, `break.count = 1`, `cause = 00000024`
(ExcCode 9 = `Bp`), `break.epc = 80500270` — the address of the `break`
instruction in the emitted image. **Different address range, different store
path, same answer.**

**So: `CCTL 0x002` alone is sufficient to make freshly written instructions
visible on this die, and the vendor's `0x200` then `0x002` is unnecessary rather
than wrong.** That wording was pre-registered in `PROGRESS.md`'s `R1g-1` row
before the payload existed, and this file may not upgrade it to *wrong*.

🔴 **What ① does not cover, and it is half of what an MTD driver does.** The
readings above are all about **instruction fetch**. An MTD driver also *reads
flash back* — and after an erase or a program, the contents of the
memory-mapped window changed underneath the D-cache, with no CPU store involved.
**That is the memory→CPU direction, it is decision ②'s question, and `R1d`
measured none of it.** So ① closes in this form:

> **The I-side recipe is `CCTL 0x002`, 量.** Whether `R5b` may read the flash
> window through a cached mapping at all is **未答**, and it moves with ② rather
> than with ①.

An MTD driver that reads through the SPI controller's own registers
(`SFCR`/`SFDR`, `SPEC.md` `REG-13`) rather than through the memory-mapped window
never asks the question. **That is a design choice `R5b` gets to make with its
eyes open, which is the point of writing this down now rather than at 2 a.m.**

### ② `R6`'s descriptor rings: 未答, and the obvious answer is not one

**This is the decision the gate did not make.** It is written out at length
because a write-up is exactly where a gate widens its own claim, and this is the
place it would have happened.

**The tempting sentence is: *"the D-cache is write-through, so the CPU side needs
no flush."* Two separate things are wrong with it.**

**(a) `R1d` measured only the memory→CPU direction's opposite, and only for a
write miss.** `probe1` cell 1 (cached store) and cell 5 (uncached store) both
read `ma = 240222b2` — `ma` is an **uncached** read-back, so the cached store
did reach DRAM with no treatment applied. But in both cells the store landed on a
line **the D-cache did not hold**: the victim words had been *executed*, not
*loaded*. A write-through cache and a **write-back cache that does not allocate
on a write miss** produce that identical reading. `notes/cache-model.md` wrote
the disjunction correctly — *"write-through (or does not allocate on write)"* —
and every downstream restatement in this repository dropped the second half.

🔴 **And there is a source on the other side.** **讀**: both GPL drops this
project holds carry `boards/rtl8196e/config.linux-2.6.30.*` with
**`CONFIG_ARCH_CACHE_WBC=y`** — *write-back cache* — in all five board variants
of each drop. ⚠️ **Two drops are not two independent sources**: both descend from
the same Realtek SDK, and this is one vote, not two.

**Why that matters for a ring and not for `probe1`:** the descriptor-ring access
pattern is *read the descriptor, then write it back* — the CPU loads the status
word, decides, and stores the ownership bit. **That is a write hit on a resident
line.** Under write-back-no-write-allocate the store stays dirty in the D-cache
and the DMA engine never sees it, while `probe1`'s cells would still have read
exactly what they read. **So the CPU→device half is not covered for the pattern
`R6` actually uses.**

**(b) The device→CPU direction has no reading at all.** The engine writes a
received frame and a status word into DRAM behind the CPU's back. Whether a
subsequent cached load sees it depends on whether the D-cache allocates on
*read* and on whether anything invalidates it — and **write-through says nothing
about read allocation.** A write-through D-cache still caches reads, so a
descriptor status word the CPU polled last time round can be stale after the
device writes DRAM. This is the classic bug, and this project has measured
nothing about it.

**What would settle ②, and it needs no DMA engine and no driver.** Use the same
KSEG0/KSEG1 aliasing trick `probe1` already proved works on this die, with an
uncached store standing in for a bus master:

| | cell | what it separates |
|:-:|---|---|
| A | uncached store to X · cached load of X · uncached store to X again · cached load of X | if the second load returns the **first** value, the D-cache allocates on read and holds a stale line — **that is the DMA-stale case, reproduced without a DMA engine** |
| B | as A, with `CCTL 0x200` before the second load | whether `DWB_Inval` invalidates a clean line |
| C | as A, with `CCTL 0x001` before the second load | whether `DInval` does — this is the constant this part's own kernel uses on one path |
| D | as A, with `cache 0x11` / `cache 0x15` over the line | 🔴 **whether the `cache` instruction executes on this core at all** — see below |
| E | store to a line the CPU has just **loaded**, then read it uncached | write-through vs write-back-no-write-allocate, decided |

⚠️ **The proxy is a model, not the thing.** It assumes an uncached store neither
updates nor invalidates the D-cache, and that a real bus master's write looks the
same from the cache's side. Cell A returning *fresh* is ambiguous between *no
read allocation*, *the alias is snooped* and *the line was evicted* — so cell A
needs `probe1`'s two-victims-far-apart trick as its own control, and a positive
result in E is what makes A's negative interpretable.

**Until those run, `R6` carries the conservative cost**: rings in an uncached
window (KSEG1), which is what the vendor's own driver does — **讀**,
`drivers/net/rtl819x/rtl865xc_swNic.h`, `UNCACHED_MALLOC(size)` is
`kmalloc(size, GFP_ATOMIC) | 0x20000000`, and every ring in
`rtl865xc_swNic.c` (`rxPkthdrRing`, `txPkthdrRing`, `rxMbufRing`,
`pPkthdrList_start`, `pMbufList_start`) is allocated through it. **That is a
reading of what the vendor chose, not a measurement of what this core requires**,
and the difference is the whole reason ② is still open.

### ③ `R1a`'s exception handler at `0x80000080`: yes

**量, `bench/2026-08-25b/`.** `Status = status_end = 1000fc00`, **bit 22 = 0**,
so `BEV` is clear and the vectors are the RAM ones. `trap_init` copying 128 bytes
to `0x80000080` proves the copy landed (`H0a`, 32/32 words identical to a list
pre-registered at 06:09; `H0a2` reads the same 32 words from the source at
`0x8040054C`; `H0a3` reads them identically through KSEG1, so no stale D line was
involved). **What proves the core *fetches* there is `break`**: it trapped into a
handler this project installed and **came back**, and the handler was restored
afterwards with `restore.mismatch = 0` and `H2h-utlb` byte-identical to the same
seating's `H0c`.

⚠️ **Residual, and it is small but real.** The `Status` word measured is the one
a payload sees after the loader's `J` cleared `IE`; it is not the word at the
`<RealTek>` prompt. The two differ in `IEc` alone, and **no loader command reads
CP0**, so the prompt's own word is not reachable without another payload. The
withdrawn `1000FC01` is vindicated by mechanism rather than resurrected: every
bit identical except bit 0, and `IEc = 0` is what *`J <addr>` clears `IE`*
predicts.

⚠️ **And `0x80000080` is where R3000-class parts put the general vector, not
`0x80000180`.** That address was wrong in seven committed files until
2026-08-25. A handler at `0x180` would have looked installed, changed nothing,
and the first fault would still have reached the loader's permanent hang.

### ④ `R5-0`'s SoC timer driver: a prerequisite

**量, `bench/2026-08-25b/H2a.log` + `H2g.log`.** CP0 rd 9 (`Count`), census row
`0x48`, reads `00000000` and is classified `S_ZERO`. Independently,
`rlx_count_delta` reads `Count` at both ends of a 100,000-iteration
three-instruction loop: `count.before = count.after = count.delta = 0`, with
`count.traps = 0` bracketing the call.

🔴 **The row that makes that zero mean something is `nowrite = 00000000` across
all 256 rows.** The census reads every register **twice, with two different
primes** (`0xC0DE00nn` then `0xD1CE00nn`), so an `mfc0` that retires without
writing `rt` returns its own prime and gets its own state, `S_NOWRITE`. It never
occurred. **So *the destination was never written* is excluded by the instrument
built to detect it, not by assumption** — and that is the difference between
*`Count` reads zero* and *nothing read `Count`*.

**Consequence: `R5-0`'s SoC timer driver is a prerequisite, not a bonus, and
`R1c` loses its first timing route.** That is a decision, not a gap.

⚠️ **Two things ④ does not establish.** First, **`Compare` (rd 11) was read and
never written.** It reads zero, which is consistent with *not implemented* and
equally consistent with *implemented and reset to zero*; a read-only census
cannot separate them. It changes nothing here — with `Count` dead the timer
interrupt route is dead either way — but the row should not be quoted as
*`Compare` is absent*. Second, **the plan's own wording is the honest one**:
*不動 = 沒有實作（或沒在跑）*. A `Count` that exists but is clock-gated reads and
behaves identically. **The experiment that separates them is one `mtc0` and one
`mfc0`** — write a known value to rd 9 and read it back — and it is free to carry
in the next payload, with `IE` already clear so no interrupt can result.

---

## The CP0 census: what 256 rows say

**量, one seating, `bench/2026-08-25b/`.** 256 stubs, rd 0…31 × sel 0…7, each
read twice with a different prime. The report is 2,909 bytes on the UART and 820
words at `0x80A01000`; the two agree on all 40 header words, on the seal
`EC84408D`, and on every spot-checked row.

**The partition closes exactly**: `values 40` + `zeros 208` + `moves 8` = **256**.
Five registers answer (rd 6, 12, 13, 14, 15), one moves (rd 1), 26 read zero,
each × 8 selects.

| reading | what it settles |
|---|---|
| `moves = 8`, and all eight are rd 1's selects; `rows.suppressed = 0`, `rows.printed = 39` | **the CP0 ignores the select field.** Every other register returned identical values across its eight selects. R3000-class decode, 量 |
| `traps = 00000000` on all 256 | reading an unimplemented CP0 register **returns zero and does not trap** on this core. Architecturally that is UNDEFINED rather than an exception; this part's choice is now measured |
| `nowrite = 00000000` on all 256 | `mfc0` always writes `rt`. **The row every other row stands on** |
| `Config` (rd 16, row `0x80`) = `00000000`, `S_ZERO` | **`Config.M = 0`, so this is not a MIPS32-class CP0**, proved outright — and **there is no `Config1`**, so the cache geometry cannot be read out of CP0 on this part |
| CP0 20 (row `0xa0`) = `00000000`, `S_ZERO` | with `nowrite = 0`, this separates *implemented and reads zero* from *destination never written* — which `probe1`'s single-prime read could not. **CP0 20 is a write-only command register that reads back zero** |
| `PRId` (row `0x78`) = `0000CD01`, `S_VALUE`, both primes | 量. ⚠️ **The value is 量 and the name is not** — no source in this repository maps `0xCD01` onto a Lexra model number. **Do not write `RLX5281`** |
| `status_end == status == 1000fc00`, bit for bit | `rfe` pops the R3000 three-deep KU/IE stack correctly. Derived before the run: `status_end` may differ from `status` only in bits 5:4, which after the first exception equal `status`'s bits 3:2, and both are 0 here. **A difference anywhere else would have refuted the R3000 `rfe` model on this core** |
| rd 6 = `00000004`, `S_VALUE`, stable across both primes | 🆕 **unexplained.** Not on the R3000 map; `Wired` sits at rd 6 on R4000-class parts and 4 is a plausible wired count. One reading, no second source — recorded open, not named |

### The positive control, and why the census would be worthless without it

🔴 **量** Row `0x08` is `mfc0 v0, c0_random`, disassembled from the emitted image
at `0x80500330`. It came back `S_MOVES` with sixteen values over its eight rows:

```
0a00 1100 / 0900 1000 / 1d00 0800 / 1500 1c00 / 0600 0d00 / 1a00 0500 / 1200 1900 / 1100 1800
```

`Random`'s index field is bits 13:8, so those are **5 … 29, every one inside
0 … 31** — which corroborates `SPEC.md` `CPU-08`'s 32 TLB entries **by a route
with no TLB probe in it**, and a classic 64-entry R3000 would have wrapped over
8 … 63.

**Why it matters more than any other row.** Decision ④ rests on *`Count` does not
move*. Without a register that **does** move on this die, that reading is
unfalsifiable — a broken double-read mechanism produces the same answer. The
emulator's own `Count` moves, so its `S_MOVES` is a control on the emulator.
**This is the control on this silicon, and it was free.**

### What the census cannot tell apart, stated so a clean table is not read as more

- `S_ZERO` does not separate *implemented and reads zero* from *not implemented
  and the bus returns zero*. Only a register with a write side — CP0 20 — was
  separated, and it was separated by its write side, not by its read side.
- The census **reads**; it never writes. Every *not implemented* below is
  therefore *reads zero and does not move*, which is weaker.
- 256 rows is rd × sel with the select field ignored, so it is **39 distinct
  observations wearing 256 row numbers**. The arithmetic closing at 256 is a
  consistency check on the payload, not 256 independent measurements.

---

## Where the cache model stands after the desk read of 2026-08-26

🔴 **This section exists because the write-up refuted two statements the gate had
been leaning on.** Both were mine, both are **讀** rather than 量, and both were
found by reading further into artefacts this project already had.

### The `cache` instruction executes on this part — in this unit's own kernel

`notes/cache-model.md` carries a refutation condition, verbatim:

> the claim "this core uses the R3000 cache model, not the MIPS32 `cache`
> instruction" is refuted by finding a `cache` instruction (primary opcode
> `0x2F`) anywhere in vendor code that executes.

**The scan that returned zero was run on `stage2.bin` — the loader — and on
nothing else.** Re-run on this unit's own kernel, decompressed from its own flash
dump, it does not return zero.

**讀, artefact A.** Chain of custody, every step reproducible:

```sh
# 987,138 bytes, sha256 396561a0565f8cf62ffd7df6b4105ae3943337ada0fdedc109eb586445a03e90
#   -- the value RUNSHEET.md P4 already records for the image R0 booted
K=$FWRE_WORK/rebuild/r0-vendor-kernel.bin
tail -c +10249 "$K" > kernel.lzma          # LZMA-alone stream at offset 0x2808
python3 -c "import lzma,sys; sys.stdout.buffer.write(
    lzma.LZMADecompressor(format=lzma.FORMAT_ALONE).decompress(
        open('kernel.lzma','rb').read()))" > vmlinux.bin
# 3,374,772 bytes, sha256 cf0d60a8ae54352e4d7d451b08a2f5551c80d8a34bf5cced19f3440dba610ec0
#   -- and the size field inside the LZMA header says 3,374,772 before it is run
```

`strings` gives
`Linux version 2.6.30.9 (admin@office.hopeiot) … #1526 Wed Jan 10 14:50:54 CST 2018`
— **this unit's own kernel, not a downloaded image.**

**The load address is `0x80000000`, and that is checked rather than assumed.**
Taking file offset = VMA − `0x80000000`, **18,068 of 31,145 `jal` targets land on
a plausible function prologue (58.0 %)**; the same test with the image shifted by
+1, +2, +7 and −3 words gives **1.7 %, 3.0 %, 2.9 % and 0.2 %**. The predicate is
crude, which is why the contrast and not the 58 % is the result.

**The finding.** 52 words in the image have primary opcode `0x2F`. They separate
into two populations on **three independent properties at once**:

| | n | addresses | `op` field | base register | offset |
|---|--:|---|---|---|---|
| **code** | **37** | one span, `0x8000CA40` … `0x8000CD4C` | only `{0x11, 0x15, 0x19}` | only `{v0, a0}` | only `{0x00, 0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70}` |
| **data** | **15** | scattered, all ≥ `0x802BA660` | ten different values, most undefined | — | arbitrary 16-bit values (`0xffff`, `0xae52`, `0xac42`, …) |

The three op values are exactly the three the vendor's own Lexra cache file
names: `0x11 = DInval`, `0x15 = DWBInval`, `0x19 = DWB`. The eight offsets are one
`cache` op per **16 bytes** covering exactly 128 bytes, which is what a D-cache
range flush unrolled over a line size of 16 looks like — **and that reading needs
only the binary.**

**The instrument's positive control.** The same scanner, unchanged, over
`stage2.bin`: it reproduces all five CCTL command sites this project had already
recorded (`0x020` @ `0x804004DC`, `0x202` @ `0x804004F8`, `0x010` @ `0x80400514`,
`0x200` @ `0x804066CC`, `0x002` @ `0x80406704`) and finds **exactly one**
`0x2F` word — `0x8040D264`, op field 0 — which is the known data false positive
already adjudicated in `notes/lwl-mystery.md`. **It reproduces both the known
positives and the known false positive.**

🔴 **What this changes, and what it does not.**

- **It does not make this a MIPS32 core.** `Config.M = 0` is 量 and settles that.
- **It does change the sentence.** The model is not *"R3000, no `cache`
  instruction"*. It is: **the loader uses CCTL only; this unit's kernel uses CCTL
  for whole-cache operations and `cache` ops for ranges, on the D side only.**
  **There is no I-side `cache` op anywhere in the image** — zero words with op
  `0x10` (`IInval`) — and the I side always goes through `CCTL 0x002`.
- ⚠️ **讀 is not 量, and *present in the binary* is not *executes*.** The routines
  are reached from `_dma_cache_wback_inv`, which the Ethernet path calls per
  packet, and this unit routes packets — but that is an argument, not a reading.
  **The measurement is cell D of ②'s list: execute one and see whether it
  retires or takes a Reserved Instruction exception.** With a handler that is now
  measured to work, a trap there costs a printed verdict rather than a power
  cycle.

### The CCTL commands have names now, and there is one this project had never recorded

🔴 `notes/cache-model.md` concluded *"there is no Lexra-specific cache file"* —
**and that was decided by looking in `arch/mips/mm/`.** This SoC builds
**`arch/rlx/`** — which this repository already names in **two** files written
before that paragraph: `SPEC.md` `CPU-33` cites `arch/rlx/kernel/traps.c` as one
of its three sources for the exception vector, and `SOURCES.json` describes a
source tree as *"Carries arch/rlx (the Lexra kernel architecture port)"*.
**The fact was in the project twice and the search still went to the wrong
directory.** `arch/rlx/mm/`
contains `cache-rlx.c`, *"RLX specific mmu/cache code"*, Realtek, Tony Wu,
2008-12-07, and it states the encoding outright:

```
 *  CCTL OP                      *  CACHE OP
 *   0x1   = DInval              *   0x10 = IInval
 *   0x2   = IInval              *   0x11 = DInval
 *   0x100 = DWB                 *   0x15 = DWBInval
 *   0x200 = DWB_Inval           *   0x19 = DWB
 *                               *   0x1b = DWB_IInval
```

**讀, and it moves four rows from *inferred* to *stated by a source*** — and
`0x100` (`DWB`) is a command this repository had no row for at all. This unit's
own kernel issues it at `0x8000CA94` and `0x8000CAC0`. The full table with its
provenance is `notes/cache-model.md`'s to own; the changed marks are in
`SPEC.md` `CPU-20` … `CPU-24` and the new `CPU-43`.

⚠️ **`cache-rlx.c` and `c-r3k.c` are two files, not two independent sources.**
Both are in the same GPL drops, and both drops descend from the same Realtek SDK.
What changed is that a value which had **no name in any source** now has one; it
is not a second vote on the value.

### `0x010` and `0x020` are still unnamed, and the residual is now sharper

**讀.** Neither `cache-rlx.c` nor anything else names them. What is new is that
**two independent implementations on this one unit issue them, at reset, in the
same order relative to `0x202`**:

| | `0x020` | `0x202` | `0x010` |
|---|---|---|---|
| this unit's loader (`stage2.bin`) | `0x804004DC` | `0x804004F8` | `0x80400514` |
| this unit's kernel (decompressed) | `0x80002240` | `0x8000225C` | `0x800022A8` |

That upgrades them from *the bootcode does it once* to **part of this SoC's reset
sequence, reproduced by two codebases**, and it says nothing about what they mean.

🔴 **And the route that would name them is closed on purpose, which is a decision
rather than a gap.** The only instrument that could name them from this side is
*writing them from a payload and observing the effect* — and this project does
not write an unnamed command to a cache controller on a one-device budget. Both
codebases issue them with cold caches at reset; a payload would issue them at an
arbitrary point, and what makes them safe there is not established. **They are
needed by no downstream decision**: `R5b` needs `0x002`, and ② needs the D-side
invalidate, whose candidates (`0x001`, `0x200`, `cache 0x11/0x15`) all have
names. **The route that stays open is a document** — a Lexra CCTL bit-field
description, or a third SDK generation that comments them.

### `Status.IsC`: broken here, and unused by everything that runs on this device

**量, `probe1` cell 4, both victims `07` CORRUPT**: `240222b2 → 000222b2` and the
guard `03e00008 → 00e00008` — the top byte of every word, stride 4, which is
exactly `rlx_isc_inv`'s `sb $0, 0($4)` walking real DRAM. On a core that
isolates, those byte stores write cache tags. **Here they wrote memory.** The
emulator found the identical failure one day earlier and the `V_CORRUPT` guard it
produced is why the payload finished.

⚠️ **What is measured is behaviour, not bits.** Stores issued while `IsC` was set
reached memory. **Whether the two `Status` bits are implemented at all, and
whether `mtc0` wrote them, is still not measured** — `SPEC.md` `CPU-19` names
`probe2`/`R1g-4b` as the experiment that would settle it, **and `probe2`
deliberately contains no `mtc0` to CP0 register 12 anywhere**, which was one of
its own audit requirements. **So that residual's named experiment ran and did not
include it.** It is re-pointed at `R1h`, not deleted.

🆕 **讀** Neither piece of software on this device uses the broken mechanism.
`stage2.bin` never touches `IsC` — already recorded. The kernel does not either:
the only two `mtc0 rt, $12` sites preceded within seven words by a `lui rX,0x1`
are `0x8002AC08` and `0x801C0750`, and both decode as the R3000 interrupt-disable
idiom `mfc0 at,$12 · ori at,at,0x1f · xori at,at,0x1f · mtc0 at,$12` — bit 16 is
never set. ⚠️ **That scan is a seven-word window with no dataflow**, so it would
miss an `ISC` constant loaded from memory; `ori` cannot set bit 16, so any set
must come through a `lui`+`or` pair, which is what it looks for.

### Cache geometry: `CPU-25` gains its first source on this unit's own artefact

**讀, from the same image.** Three sites in the D-cache routines compare the
range length against `0x4000` before falling back to a whole-cache CCTL command,
and one compares against `0x2001`:

```
8000ca18  sltiu v0,a1,0x2001      8000caac  sltiu v1,v1,0x4000
8000cbe0  sltiu v1,v1,0x4000      8000ccd4  sltiu v1,v1,0x4000
```

In `cache-rlx.c` those thresholds are `cpu_dcache_size * 2` and
`cpu_dcache_size`. **So this build declares a D-cache of `0x2000` = 8 KiB**, and
the `cache` op lattice above declares a **16-byte line**.

**Two different strengths, and they must not be quoted as one.** The 16-byte
line is readable from the binary alone — eight ops at stride 16 covering 128
bytes is a line-size assumption whatever the source says. **The 8 KiB needs the
source to interpret the constant**, so it is one step weaker. Both agree with
`shibajee/linux-rtl8196e`'s `rtl8196e.dtsi` (`d-cache-size = <8192>`,
`d-cache-line-size = <16>`) — **a third party whose register addresses in the
same file are demonstrably placeholders**, and which now agrees with something
cut from this unit.

⚠️ **None of it is 量, and a build constant can be wrong about its own silicon.**
It is a **prediction with a refutation condition**, which is worth having only
because it is written before the walk that tests it. **The I-cache size is not
readable by this route at all** — the I side has no per-line op in this build, so
there is no threshold constant to read.

---

## What `R1-gate` did not prove

**Written in full, because two consecutive gates whose *did not prove* is the
same thing make that thing the next gate (§18.3).**

1. **Whether a DMA write is visible to a cached CPU read, and whether anything on
   this core invalidates a clean D line.** Decision ②, entirely. Nothing was
   measured in that direction.
2. **Whether the D-cache is write-through or write-back without write allocate.**
   `probe1`'s cells cannot separate them, and the vendor's own board config says
   write-back.
3. **Whether the `cache` instruction retires on this silicon.** It is in this
   unit's kernel, 讀; no payload has executed one.
4. **Cache size, line size and associativity, measured.** Both CP0 routes are
   shut by measurement (`Config.M = 0`; the R3000 sizing walk needs isolation
   this core does not have). What exists is a build constant and a third party's
   device tree that agree — a prediction, not a reading.
5. **What `CCTL 0x010` and `0x020` do.** Unnamed in every source, and the
   instrument that would name them is one this project declines to run.
6. **Whether `Status.IsC`/`SwC` are implemented as bits**, as distinct from
   whether isolation works. Needs a `Status` write and read-back; `probe2` was
   built to contain no `mtc0` to CP0 12.
7. **Whether `Compare` is implemented.** Read, never written.
8. **Anything about the Lexra family.** `R1d` measures **which flush works on
   this core**. It does not measure why, and it licenses no statement about
   RLX4181 versus RLX5281 — `PRId = 0000CD01` is a value with no name attached to
   it in any source this project holds.

**Items 1–3 share one payload and one seating.** They are `R1h`.

---

## Re-running the desk half

Everything in *§ Where the cache model stands* is derived by these commands from
artefacts that cannot be committed. Three controls ran with them and all three
are load-bearing:

| control | what it rules out | result |
|---|---|---|
| `r0-vendor-kernel.bin` must hash to the value `RUNSHEET.md` P4 already records | reading a different artefact from the one `R0` booted | matches, `396561a0…45a03e90` |
| the LZMA header's own uncompressed-size field must equal the decompressed length | a partial or mis-framed stream | both `3,374,772` |
| the same opcode scanner over `stage2.bin` must reproduce the five known CCTL sites **and** the one known data false positive at `0x8040D264` | a scanner that finds `cache` words because it is broken | reproduces all six |

**The VMA base is the fourth control** and it is the one that could most easily
have been assumed: `jal` targets land on plausible prologues at 58.0 % under
base `0x80000000` and at 0.2–3.0 % under four deliberately wrong bases.
