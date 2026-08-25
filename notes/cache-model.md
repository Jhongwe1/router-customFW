# Cache management model — F49

**DAY-ZERO item 2b. Desk work, 2026-08-23. Nothing here was measured on the
device.** Two sources, both read: this unit's own bootcode, disassembled from
its flash dump, and the vendor's Linux 2.6.30 tree for this SoC family.

## Why this blocks three later gates

MIPS-I has no `cache` instruction; that is MIPS-II and later. The R3000
generation used `Status.IsC` / `Status.SwC` and byte stores instead — a
completely different mechanism. Which one this core uses decides:

- **R1d** — the bare-metal probe writes an exception handler into RAM at
  `0x80000080` and then has to make the I-cache see it. 🔴 **This line said
  `0x80000180` until 2026-08-25, and that address is MIPS32's, not this core's.**
  See the correction at the bottom of this file.
- **R5b** — the MTD driver writes flash and then has to make the
  memory-mapped window agree.
- **R6** — `dma_map_single()` is this, underneath.

## Answer

**Both mechanisms exist on this silicon, and the two pieces of vendor software
each use a different one.**

| | mechanism | source |
|---|---|---|
| bootcode (`stage2.bin`, this unit) | **CP0 register 20 only.** `Status.IsC`/`SwC` never touched | read out of the dump |
| Linux 2.6.30, `CONFIG_RTL_819X` path | **`Status.IsC`/`SwC` plus a byte-store loop.** The CP0-20 variant is present in the same file but `#if 0`-ed out | read out of `linux-2.6.30/arch/mips/mm/c-r3k.c` |

The kernel file is `c-r3k.c`, reached through `cpu_cache_init()` under
`cpu_has_3k_cache`. `arch/mips/mm/` in that tree contains only the stock
`c-r3k.c`, `c-r4k.c`, `c-tx39.c`, `c-octeon.c` — there is no Lexra-specific
cache file. **So the model is the R3000 one**, and CP0 register 20 is an
addition on top of it, not a replacement for it.

> 🔴 **Correction, 2026-08-26 — the paragraph above searched the wrong
> directory, and the conclusion it drew is narrower than it reads.**
> These trees carry **two** architecture directories, and this SoC builds
> `arch/rlx/`, not `arch/mips/` — a fact this repository already relied on
> elsewhere — **in two places, both written before this paragraph**: `SPEC.md`
> `CPU-33` cites `arch/rlx/kernel/traps.c` as one of its three sources for the
> exception vector, and `SOURCES.json`'s `openwrt-rtk` entry says in as many
> words *"Carries arch/rlx (the Lexra kernel architecture port)"*.
> **`arch/rlx/mm/cache-rlx.c` exists**: *"RLX specific mmu/cache
> code"*, Realtek, Tony Wu, 2008-12-07. So *there is no Lexra-specific cache
> file* is false; what is true is that `arch/mips/mm/` has none.
>
> **What survives**: the bootcode uses CP0 20 only, and `Config.M = 0` is 量, so
> this is not a MIPS32-class CP0. **What does not**: the *"no `cache`
> instruction"* half — see § *The refutation condition below is met*.
> The paragraph is left as written rather than edited to look prescient.

CP0 register 20 has no meaning in MIPS-I or MIPS32 (binutils prints it as
`c0_xcontext`, which is the MIPS64 name and cannot be what this is). Lexra
documents a CP0 register named CCTL "used to control the instruction and data
memories", accessed with `mtc0`/`mfc0` variants — which is the shape observed.
~~**Calling this register CCTL is inference from the Lexra documentation plus the
observed behaviour, not something either source states.**~~
🔴 **2026-08-26: a source states it.** `arch/rlx/mm/cache-rlx.c` calls it
`CCTL`, names four of its commands, and gives the `mtc0`/`mfc0` idiom for two
core families. **The name is 讀 now, not 推** — see the table below.

## What is written to CP0 register 20

Every use in both sources is the same idiom: clear, write a command, clear.

```
mtc0 $0, $20      nop
li   $8, <value>
mtc0 $8, $20      nop  nop
mtc0 $0, $20      nop
```

🔄 **Table rewritten 2026-08-26.** Four of the values have a **name from a
source that states it** rather than a meaning inferred from where they are used,
and one value has been added that this file had no row for. The naming source is
`arch/rlx/mm/cache-rlx.c`, whose header comment reads, verbatim:

```
 *  CCTL OP
 *   0x1   = DInval
 *   0x2   = IInval
 *   0x100 = DWB
 *   0x200 = DWB_Inval
```

| value | name | meaning | where it is issued | status |
|---:|---|---|---|---|
| `0x001` | `DInval` | invalidate D-cache, no writeback | `c-r3k.c` `CONFIG_RTL865XB` path; **this unit's kernel `0x8000CA24`** | 🔄 **name 讀**; value in two files of one SDK |
| `0x002` | `IInval` | **invalidate I-cache** | `c-r3k.c` `r3k_flush_icache_range()`; `stage2` `0x80406704`; **this unit's kernel `0x8000CB34`, `0x8000CB5C`, `0x8000CCA8`** | 🔴 **name 讀; effect 量** — `probe1` cells 2/3/6, `probe2`'s handler install |
| `0x100` 🆕 | `DWB` | write back D-cache, no invalidate | **this unit's kernel `0x8000CA94`, `0x8000CAC0`** | 🆕 **name 讀.** New row 2026-08-26 — this file had never recorded the value |
| `0x200` | `DWB_Inval` | write back **and** invalidate D-cache | `c-r3k.c` `CONFIG_RTL8652`/`CONFIG_RTL_819X`; `stage2` `0x804066CC`; **this unit's kernel `0x8000CB50`, `0x8000CBF4`, `0x8000CCE8`** | 🔄 name 讀. ⚠️ **The old row said "flush D-cache", which does not say whether it invalidates. It does** |
| `0x202` | `DWB_Inval \| IInval` | both, in one write | `stage2` `0x804004F8`; **this unit's kernel `0x8000225C`** | composed of two named bits now, not inferred from two uses |
| `0x010` | — | — | `stage2` `0x80400514`; **this unit's kernel `0x800022A8`** — both at reset init only | 🔴 **still undetermined, and no source names it** |
| `0x020` | — | — | `stage2` `0x804004DC`; **this unit's kernel `0x80002240`** — both at reset init only | 🔴 **still undetermined, and no source names it** |

⚠️ **`cache-rlx.c` and `c-r3k.c` are two files, not two independent sources.**
Both live in the same GPL drops and both drops descend from the same Realtek
SDK. What changed is that values which had **no name in any source** now have
one; nothing here is a second vote on a value.

🔴 **The two unnamed rows: what is new, and why the residual stays open.** They
are no longer *"the bootcode does it once"*. **This unit's own kernel issues the
same two commands, at reset, in the same order relative to `0x202`** — so two
independent implementations on this one device treat them as part of the reset
sequence. That is evidence about their **place**, not about their meaning.

**And the instrument that would name them is one this project declines to run.**
Writing an unnamed command to a cache controller on a one-device budget buys
nothing any downstream decision needs: `R5b` needs `0x002`, and `R6` needs a
D-side invalidate whose candidates (`0x001`, `0x200`, `cache 0x11`/`0x15`) all
have names. Both codebases issue them with cold caches at reset; a payload would
issue them at an arbitrary point, and what makes them safe there is not
established. **The route that stays open is a document** — a Lexra CCTL
bit-field description, or a third SDK generation that comments them. *(The old
line here said "R1e or a `devmem`-class read is what would settle them". `R1e`
ran and did not: the census reads CP0 20 and reading it returns zero, which
`CPU-39` has now measured. **A read side that is always zero cannot name a write
side.**)*

### The `cache`-instruction encoding, from the same source

The same header comment gives the `cache` op field encoding, and it is what the
adjudication in § *The refutation condition below is met* matches against:

```
 *  CACHE OP
 *   0x10 = IInval    0x11 = DInval    0x15 = DWBInval
 *   0x19 = DWB       0x1b = DWB_IInval
```

**讀** `cache-rlx.c` defines the D-side ops for `RLX4181`, `RLX5181`, `RLX4281`
and `RLX5281`, and the **I-side** ops for `RLX4281`/`RLX5281` only. This unit's
kernel contains D-side ops and **zero I-side ops**, which is the shape the
4181/5181 side of that split produces. ⚠️ **That is the build's belief about its
own silicon, not a measurement of the silicon**, and it is one more name-free
input to `CPU-04` rather than an answer.

## The order matters, and the vendor says why

`c-r3k.c` carries the reason in a comment, dated:

> *Flush data cache at first in write-back platform.*
> *Ghhuang (2007/3/9): RD-Center suggest that we need to flush D-cache entries
> which might match to same address as I-cache ... when we flush I-cache.*
> *( Maybe some data is treated as data/instruction, both. )*

`stage2` does exactly that: `0x804066e8` calls `0x804066c0` (D-cache, `0x200`)
before writing `0x002` (I-cache). This is the sequence that matters for R1d —
**writing a handler into RAM and invalidating the I-cache is not enough on a
write-back D-cache; the handler may still be sitting in the D-cache.**

## Where the loader executes from, which is why it can get away with less

The third instruction sequence the loader runs after reset takes the address of
its own next instruction, ORs in `0xA0000000`, and jumps:

```
80400498:  lui   t1,0x8040
8040049c:  addiu t1,t1,1196     ; 0x804004ac   KSEG0, cached
804004a0:  lui   at,0xa000
804004a4:  or    t1,t1,at       ; 0xA04004ac   KSEG1, uncached
804004a8:  jr    t1
804004ac:  mfc0  t0,c0_status   ; delay slot
```

From there the loader runs **uncached**. So "how does the loader make the
I-cache see freshly written RAM" had a third possible answer all along —
*it does not have to, for its own code* — and it uses all three: it runs
uncached itself, it initialises the caches through CP0 20 at boot, and it
flushes D-then-I through CP0 20 immediately before jumping to the kernel image.

The vendor bootcode source confirms the last of these directly
(`sdk-src/wecb-boot/utility.c`, a different bootcode generation):

```c
jump = (void *)(pheader->startAddr);
cli();
flush_cache();
jump();          // jump to start
```

## Measured on the device, 2026-08-25 — and one of the two mechanisms is broken

🔴 **This section used to be called "Not established" and to open with *"nothing
here is a measurement on the device"*. That is no longer true**, and the sentence
it made — *"that `Status.IsC` **works** on this core is read out of the kernel
source, not observed"* — is now **refuted**. `probe1` ran from `0x80500000` on
this unit (`bench/2026-08-25/H1b.log` and `H1c.log`, two channels, 104/104 row
words identical, `RUNSHEET.md` § Results B4). Six cells, twelve victims:

| | measured | what it settles |
|---|---|---|
| **the I-cache is real and it goes stale** | cell 1 — cached store, **no treatment** — executed the OLD constant while memory already held the NEW one, `01` STALE on **both** victims of a pair 7 KiB apart | 🔴 **the negative control.** Without it every other cell would have passed untested. And it came back the **opposite** of qemu, which reports FRESH because TCG invalidates a translation block when a store lands on translated code |
| 🔄 **a cached store to a line the D-cache does not hold reaches memory unaided** — *(this row read **"the D-cache is write-through** (or does not allocate on write)"* until 2026-08-26; see the correction below the table)* | cell 1 and cell 5 — the same store through the cached and the uncached window, both `T_NONE` — agree on `ma = 240222b2`, and `ma` is an **uncached** read-back | for these six cells, nothing dirty was left behind, so cells 2/3/4 are not contaminated by a dirty line. **It does not follow that no dirty line can exist on this core** |
| **`CCTL 0x002` alone is sufficient** | cells 2, 3 and 6 all `02` FRESH, guards intact | **for the store these cells make**, `0x200` had nothing to write back, so the vendor's D-then-I sequence is **unnecessary rather than wrong** on this die — and this file may not upgrade that to *wrong*. 🔄 **Nor to *always unnecessary***: a store that hits a line the D-cache already holds is a case no cell here exercised |
| 🔴 **`Status.IsC` does not isolate** | cell 4 `07` CORRUPT on both victims: `240222b2 → 000222b2`, guard `03e00008 → 00e00008` — **the top byte of every word, stride 4** | `rlx_isc_inv`'s `sb $0, 0($4)` walked real DRAM. The `Status.IsC`/`SwC` path is the one `c-r3k.c` uses and the one this unit's bootcode never touches, and **it is the broken one on this part.** qemu found the same failure one day earlier; the `V_CORRUPT` guard it produced is why the payload finished instead of jumping into the weeds |

🔴 **Correction, 2026-08-26 — "the D-cache is write-through" was a reading of the
measurement, and the measurement does not carry it.**

Both cells stored to a word that had been **executed** and never **loaded**, so
the store was a D-cache **miss** in both. Under those conditions a write-through
cache and a **write-back cache that does not allocate on a write miss** produce
the identical `ma`. The disjunction was in this file from the day it was written
— *"(or does not allocate on write)"* — and **every restatement downstream
dropped the second half**: `SPEC.md` `CPU-19`, `RUNSHEET.md` § Results B4,
`PROGRESS.md` § Now. A parenthesis is not where a load-bearing alternative
belongs.

**And a source votes the other way.** **讀**: both GPL drops carry
`boards/rtl8196e/config.linux-2.6.30.*` with **`CONFIG_ARCH_CACHE_WBC=y`** —
*write-back cache* — in all five board variants of each. ⚠️ **One vote, not
two**: the drops share an ancestor. But it is a vote on the question this file
had recorded as settled.

**Why it matters, and it is not academic.** The descriptor-ring access pattern is
*load the status word, then store the ownership bit* — **a write hit on a
resident line**. Under write-back-no-write-allocate that store stays dirty and a
bus master never sees it, while `probe1`'s cells would have read exactly what
they read. **So the CPU→memory direction is not covered for the pattern `R6`
actually uses**, and that is one half of why decision ② is 未答. The other half
is that nothing was measured in the memory→CPU direction at all.
`docs/rlx-cache-and-cp0.md` § ② owns the decision and lists the cells that
settle it; cell E — *store to a line the CPU has just loaded, then read it
uncached* — is the one that decides this row.

⚠️ **What that fourth row measures is behaviour, not bits.** Stores issued while
`IsC` was set reached memory. Whether the two `Status` bits are implemented at
all, and whether `mtc0` wrote them, needs a `Status` read-back — ~~`probe2`~~
🔴 **and this is a residual whose named experiment ran without it.** `probe2`
was built, by its own audit requirement, to contain **no `mtc0` to CP0 register
12 anywhere**, so `R1g-4b` could not have answered it. Re-pointed at `R1h`.
🆕 **讀, 2026-08-26**: nothing on this device sets `IsC` anyway. The loader never
touches it, and in this unit's kernel the only two `mtc0 rt,$12` sites preceded
within seven words by a `lui rX,0x1` — `0x8002AC08` and `0x801C0750` — both
decode as the R3000 interrupt-disable idiom `mfc0 at,$12 · ori at,at,0x1f ·
xori at,at,0x1f · mtc0 at,$12`, with bit 16 never set. ⚠️ Seven-word window, no
dataflow: it would miss an `ISC` constant loaded from memory.

**Still not established:**

- The `0x010` and `0x020` boot-init commands are unexplained.
- Cache line size, associativity and total size are unknown. `c-r3k.c` sizes
  the caches at runtime with `r3k_cache_size(ST0_ISC)` — 🔴 **and the seating
  that could have run it deliberately did not**: `GEOM=0`, because that walk
  writes 1 MiB of real memory on a core that does not implement `Status.IsC`,
  **and cell 4 has now measured that this core is exactly that core.** Arming it
  needs a before/after read of the window it may scribble on.
- 🔴 **CP0 register 20's read side is SETTLED, 2026-08-25b: it reads zero for
  real.** `probe1`'s cell could not separate *implemented and reads zero* from
  *destination never written*, because `rlx_mfc0_cctl` has exactly one writer of
  `$v0`. `probe2`'s census reads every register **twice, with two different
  primes** (`0xC0DE00nn` then `0xD1CE00nn`), so a non-writing `mfc0` returns its
  own prime and gets its own state. **`nowrite` came back 0 on all 256 rows** —
  `mfc0` always writes `rt` on this core — and row `0xa0` (rd 20) came back
  `S_ZERO`. Both channels agree (`bench/2026-08-25b/H2a.log`, `H2g.log`).
  **The write side was already measured**: cells 2, 3 and 6 prove `mtc0 $t,$20`
  has an effect.

  **So: CP0 register 20 is a write-only command register that reads back zero.**
  That is the sentence `R5b`'s MTD driver needs, and it is now two measurements
  rather than one reading plus an assumption.

## Cache geometry — a prediction with one weak source, written before the measurement

**Added 2026-08-25. Not measured, not corroborated, and the source is the weakest
class in this project.** It is here because a number written *before* the cell
that tests it is a refutation condition, and the same number written after it is
a description.

A third-party OpenWrt-style port for this SoC — `shibajee/linux-rtl8196e`, branch
`RTL8196E`, `arch/mips/boot/dts/realtek/rtl8196e.dtsi`, fetched 2026-08-25 —
carries a `cpu@0` node:

```
compatible      = "lexra,rlx4181";
d-cache-size    = <8192>;      i-cache-size      = <16384>;
d-cache-line-size = <16>;      i-cache-line-size = <16>;
tlb-entries     = <32>;
```

**What this is worth, stated before anyone quotes it.** One source, third party,
and the same file's register addresses are demonstrably placeholders: its `soc`
node declares `ranges = <0 0xB8000000 0x1000>` — a 4 KiB window — while
`interrupt-controller@B8003000` carries `reg = <0x0 0x100>`, which resolves to
`0xB8000000`, and `serial@B8002000` and `serial@B8002100` carry the **same**
`reg`. The tree does not compile: `dtc` stops at `clocks = <&cpu_clk/2>`, a
phandle with an arithmetic operator in it. **So this file is admissible as prior
art for driver shape and for these five integers, and for nothing addressed.**

`tlb-entries = <32>` is **not** recorded as a vote: `SPEC.md` `CPU-08` already
holds 32 as **measured on the device**, and adding a third party's guess beside a
measurement is what the two-source rule exists to prevent.

🔴 **2026-08-25b: THE REFUTATION COLUMN BELOW IS VOID, and it is void by
measurement rather than by neglect.** It named `probe1`'s `GEOM=1` walk. That
walk is `r3k_cache_size()`, and the algorithm **needs cache isolation to work**:
it isolates, writes a marker at `base` and reads it back — *which succeeds on a
core that does not isolate, because the store and the load both went to DRAM, so
the guard passes for the wrong reason* — then zeroes `base + k*4` for
k = 32 … 0x40000, writes −1 at `base`, and walks upward looking for the first
`base + k*4` that reads non-zero. **On a non-isolating core every one of those
words was just zeroed in real DRAM and stays zero**, so the walk reaches its
ceiling and returns `0` — which is the same value it returns for *the core does
not answer*. `probe1` cell 4 measured on 2026-08-25 that this core does not
isolate (`CPU-35`). **So the experiment was already dead before it was armed.**

⚠️ **And the danger wording everywhere in this repository was wrong about the
volume.** `GEOM=1` does not "write 1 MiB of real memory": loop 2 executes one
`sw` per iteration, fourteen iterations, plus two stores at `base` — about
**sixteen words per call**, scattered across a 1 MiB bounding box. The extent is
1 MiB; the volume is not. The hazard that was never priced is different: unlike
`rlx_isc_inv`, `rlx_r3k_size` is called **directly from C**, so instruction fetch
stays cached while `Status.SwC` is set, and what fetch does under `SwC` is the
one thing this core has no documentation for.

**The other route is shut too.** `Config` (rd 16) reads `00000000` with
`nowrite = 0` proving the destination was written, so `Config.M = 0` and **there
is no `Config1`** to carry `IS`/`IL`/`IA` and `DS`/`DL`/`DA`.

🆕 **What can still refute these three numbers**: an eviction walk that needs no
isolation at all, using the mechanism `H1` cell 1 already proved on this die — a
store into the instruction stream is not seen. Prime N victims at stride S,
execute them, rewrite them, execute again; the ones that come back FRESH were
evicted. Sweeping N gives the size, sweeping S the line size, and the pattern
gives the associativity. That is `probe3`, and it is desk work.

🔴 **2026-08-26: two of these three numbers now have a source cut from this
unit, and they are not equally strong.** Read out of the decompressed kernel
above:

```
8000ca18  sltiu v0,a1,0x2001      8000caac  sltiu v1,v1,0x4000
8000cbe0  sltiu v1,v1,0x4000      8000ccd4  sltiu v1,v1,0x4000
```

Those are the *"range too big — flush the whole cache instead"* thresholds, and
in `cache-rlx.c` they are `cpu_dcache_size` and `cpu_dcache_size * 2`. **So this
build declares a D-cache of `0x2000` = 8 KiB.** Independently, the `cache` op
lattice is eight ops at stride `0x10` covering exactly 128 bytes — **a 16-byte
line.**

⚠️ **Two different strengths, and they must never be quoted as one.** The
**16-byte line is readable from the binary alone**: eight ops per 128 bytes *is*
a line-size assumption, whatever the source says. The **8 KiB needs
`cache-rlx.c` to interpret the constant**, so it is one step weaker. And **the
I-cache size is not readable by this route at all** — the I side has no per-line
op in this build, so there is no threshold constant to read. It stays 留白 with
no source of any kind.

⚠️ **And none of it is 量.** A build constant is what the vendor's kernel
*believes* about its own silicon. It agrees with the third-party
`rtl8196e.dtsi` — which is worth something, because those two sources have no
common ancestor on this point — but two beliefs agreeing is still not a
measurement. **It is a prediction with a refutation condition, and it is only
worth writing down because it is written before the walk that tests it.**

| | prediction | refuted by |
|---|---|---|
| I-cache | **16 KiB** — 🔄 **still one source, and it is the third-party one.** Nothing cut from this unit says anything about the I-cache size | 🔄 **a `probe3` eviction walk** (was: `probe1`'s `GEOM=1` walk, which cannot answer on this core) |
| D-cache | **8 KiB** — 🆕 **two sources with no common ancestor on this point**: the dtsi, and `0x4000` = `cpu_dcache_size * 2` in this unit's own kernel | the same |
| line size, D | **16 bytes** — 🆕 **the strongest of the three**: readable from this unit's kernel binary without any source to interpret it, eight `cache` ops per 128 bytes | the same |
| line size, I | **16 bytes** — 🔄 **one source.** Split out of the row above 2026-08-26: the I side of this build has no per-line op, so the binary says nothing about it | the same |
| core | RLX4181 rather than RLX5281 | 🔴 **2026-08-25b: `PRId` row `0x78` read `0x0000CD01`, and it refutes nothing here — because no source in this repository maps that value onto either model number.** The prediction and its refutation condition were both about a name, and the measurement is a value. **What would settle it is a `PRId` assignment table, not another seating.** *(Original condition:)* `probe2`'s `PRId` row `0x78` reading in the 5281 range — which would be worth more than agreement, because it refutes a Realtek datasheet and two public kernel trees at once |

🔴 **`GEOM=1` does not run in `RUNSHEET.md` § Session B4** — the build is
`GEOM=0`, and the walk writes 1 MiB of real memory at `0x80B00000` if this core
does not implement `Status.IsC`, which is one of the things the same seating is
there to find out. So this prediction is not tested by the next seating, and
saying so is the point of writing it down now.

**Refutation condition, for the record:** the claim "this core uses the R3000
cache model, not the MIPS32 `cache` instruction" is refuted by finding a `cache`
instruction (primary opcode `0x2F`) anywhere in vendor code that executes. The
scan of `stage2.bin`'s code region found none; the one whole-file hit at
`0x8040d264` decodes as `cache 0x0,786(zero)`, sits after a function epilogue
and before zero padding, and is data (`notes/lwl-mystery.md`).

## The refutation condition above is met — 2026-08-26

🔴 **The scan that returned zero was run on the loader and on nothing else.**
`stage2.bin` is 56,592 bytes of a 4 MiB device. Re-run on **this unit's own
kernel**, decompressed from its own flash dump, it does not return zero.

**讀, artefact A**, every step reproducible and hash-anchored:

```sh
K=$FWRE_WORK/rebuild/r0-vendor-kernel.bin     # 987,138 B, sha256 396561a0…45a03e90
tail -c +10249 "$K" > kernel.lzma             # LZMA-alone stream at offset 0x2808
python3 -c "import lzma,sys; sys.stdout.buffer.write(
    lzma.LZMADecompressor(format=lzma.FORMAT_ALONE).decompress(
        open('kernel.lzma','rb').read()))" > vmlinux.bin
# 3,374,772 B, sha256 cf0d60a8ae54352e4d7d451b08a2f5551c80d8a34bf5cced19f3440dba610ec0
# strings: Linux version 2.6.30.9 (admin@office.hopeiot) … #1526 Wed Jan 10 2018
```

The hash of the input is the one `RUNSHEET.md` `P4` already records for the image
`R0` booted, so the chain of custody closes against a committed record rather
than against a filename.

**52 words in the image carry primary opcode `0x2F`, and they separate into two
populations on three independent properties at once:**

| | n | addresses | `op` field | base register | offset |
|---|--:|---|---|---|---|
| **code** | **37** | one span, `0x8000CA40` … `0x8000CD4C` | only `{0x11, 0x15, 0x19}` — `DInval`, `DWBInval`, `DWB` | only `{v0, a0}` | only `{0x00, 0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70}` |
| **data** | **15** | scattered, all ≥ `0x802BA660` | ten different values, most undefined | — | arbitrary 16-bit values (`0xffff`, `0xae52`, `0xac42`, …) |

**Controls.** The VMA base is not assumed: with file offset = VMA − `0x80000000`,
**18,068 of 31,145 `jal` targets land on a plausible function prologue
(58.0 %)**, against **1.7 %, 3.0 %, 2.9 % and 0.2 %** for four deliberately
wrong bases. And the same scanner over `stage2.bin` reproduces all five known
CCTL sites **and** the single known data false positive at `0x8040D264` — it
finds what is there and it still finds the thing that is not code.

🔴 **What this changes.**

- **Not** that this is a MIPS32 core. `Config.M = 0` is 量 and settles that.
- The sentence. **The loader uses CCTL only; this unit's kernel uses CCTL for
  whole-cache operations and `cache` ops for ranges, on the D side only.** There
  are **zero** I-side ops (`0x10 IInval`) in the whole image; the I side always
  goes through `CCTL 0x002`.
- 🔴 **There may be a working D-cache invalidate on this part**, which is exactly
  what decision ② needs and what nothing has tested on silicon.

⚠️ **讀 is not 量, and *in the binary* is not *executes*.** These routines are
reached from `_dma_cache_wback_inv`, which the Ethernet path calls per packet,
and this unit routes packets — **that is an argument, not a reading.** The
measurement is one `cache 0x11` in a payload under the handler `R1g-4b` proved
works: it retires, or it takes a Reserved Instruction exception and says so.
Either outcome is worth having and neither costs a power cycle.

## What R1d should do with this — 🔄 done 2026-08-25, and item 3 is what changed

*(Kept as written, with what the seating did to each.)*

1. Write the handler to `0x80000080` through **KSEG1** (`0xA0000080`), which
   sidesteps the D-cache entirely, then invalidate I-cache with CP0 20 `0x002`.
   🔴 **And cover `0x80000000` too** — that is the UTLB refill vector on this
   layout, the loader never populated it, and stage 1's DRAM-sizing probe left
   `0x5A5AA5A5` sitting there.
   ✅ **All three parts confirmed on silicon.** `H0a`/`H0a3` read the vector page
   identically through the cached and uncached windows, so the KSEG1 write path
   is not racing a stale line; `CCTL 0x002` is measured sufficient; and
   `H0c` read `5A5AA5A5` at `0x80000000` — **opcode 22, `BLEZL`, not `j` and not
   `jal`**, which is the reading that let `probe1` run at all.
2. Keep the CP0 20 `0x200` D-cache flush before it as the vendor does, because
   the vendor's own comment says the two caches can hold the same address.
   🔄 **Downgraded from necessary to harmless** — 🔄 **and narrowed again on
   2026-08-26.** For the store `probe1`'s cells make, `0x200` had nothing to write
   back; it does **not** follow that it never does, because those stores were all
   D-cache misses. Keeping it costs one instruction
   and stays defensible for a driver that may run on another die; **claiming it
   is required here would be wrong**, and so would claiming the vendor was.
   🔴 **And `probe2` DROPPED it on 2026-08-25, which is a decision this file
   owns and should state.** `probe2`'s stores go through KSEG1, so there is no
   dirty D-line for `0x200` to write out even in principle; using `0x002` alone
   makes `probe2` **a second, independent test of the item above** — a different
   address range (physical 0, a page it does not own) and a different store path
   (uncached, not cached). And the failure is decomposable, which is the part
   worth having: `probe2` reads all 44 installed words back before it dares
   `break`, so *the stores did not land* and *the I-cache did not see them* stop
   being one hang. A `break` that does not return **with `install.bad = 0`** would
   refute `CCTL 0x002` on ground `probe1` never covered.
   **What goes into `R5b`'s MTD driver is still `0x002`**, and `0x200` in a driver
   is belt and braces rather than a correction.
3. **Both of those are single-source for the exact bit values.** Before either
   goes into `rlxprobe`, confirm on silicon: write a handler, take an exception,
   and check it ran.
   🔴 **This is the item the seating changed, and not in the direction it
   expected.** The check it describes belongs to `probe2`, which did **not** run —
   an independent audit found four defects in it first, including that its
   designed *visible* failure is measured to be complete silence. What ran
   instead was `probe1`, whose cell 4 established the thing this list did not
   think to ask: **the alternative mechanism, `Status.IsC`, destroys memory on
   this core.** So a handler installed the way item 1 describes is the *only*
   route here, and it is a measured route rather than a chosen one.

## Correction, 2026-08-25 — the exception vector address in this file was wrong

**Read out of this unit's own stage 2, plus two independent sources.** This file
said `0x80000180` in two places. That is the **MIPS32** general exception vector.
This is a Lexra RLX with an R3000-class CP0, and the layout is:

| | |
|---|---|
| `0x80000000` – `0x8000007F` | UTLB refill vector. **The loader installs nothing here** |
| `0x80000080` – `0x800000FF` | general exception vector, 128 bytes, installed by `trap_init` |

Three sources, none of which says `0x180`:

- **this unit's binary** — `trap_init` at `0x8040D07C` builds the destination as
  `8040d0d0: lui v0,0x8000` / `8040d0d4: ori t0,v0,0x80`, copies 128 bytes from
  `0x8040054C`, then `8040d238: jal 0x80406728` (`flush_cache`);
- **the vendor bootcode's own comment**, `bootcode/boot/init/irq.c:228` —
  *"remember here we set BEV=0, and vector base is 80000000, offset 0x80"*, and
  the line under it is `memcpy((void *)(KSEG0 + 0x80), &exception_matrix, 0x80);`
- **the vendor's Linux for this core family** —
  `linux-2.6.30/arch/rlx/kernel/traps.c:691`, `#define RLX_TRAP_VEC_BASE
  0x80000080`, with `arch/rlx/mm/tlbex.c:109` `#define RLX_TRAP_TLB_BASE
  0x80000000`.

**Corroborated by the return instruction, with a positive control.** This loader
leaves an exception with `rfe` (`0x42000010`) at `0x804007B0` and `0x80400970`.
The encoding for `eret`, `0x42000018`, occurs **zero** times in the same
disassembly — and that zero is a claim, so the same grep was run for `rfe` on
the same file and found the two. `rfe` is R3000; `eret` is MIPS32.

**Why it matters more than a typo.** A handler written to `0x80000180` lands in
RAM nothing reads. The payload would then look installed, take a fault, and the
loader's own `do_reserved` at `0x80400BE8` would run instead — two prints and
`j 0x80400C18`, a branch to itself, with interrupts already off and the watchdog
not armed. **That is a permanent hang, i.e. one power cycle, and there is no
spare device.**

**Where it was.** Seven committed sites — `notes/cache-model.md` twice,
`docs/loader-command-semantics.md`, `LOG.md`, `PROGRESS.md` twice,
`tools/rlxprobe/README.md` — plus `tools/rlxprobe/probe0.c` and five more in the
gitignored planning material. 🔴 **`SPEC.md` is not one of them**: `CPU-27` is
blank and carries no address at all. A first draft of this correction named it,
which is how a correction pass can invent the error it is correcting. **Not measured**: everything above is read out of code. The
cell that makes it a measurement is `DW 80000080 32` at the prompt, which is
read-only and costs nothing.

## What is actually at `0x80000080`, all 32 words

**Added 2026-08-25, and it is a correction to a correction.** `RUNSHEET.md`'s
`H0a` cell cited *"the 32 words `notes/cache-model.md` lists"*. **This file listed
none** — not 32, not one — and eleven of them existed in exactly one place in the
repository, the runsheet row itself. That is the same failure the correction above
records about itself: *a correction can invent the error it is correcting*. The
expected value of the cell that decides whether `probe2` runs was pointing at a
file that did not hold it.

**Read out of this unit's own stage 2**, at file offset `0x54C`, which is the
source `trap_init` copies 128 bytes from. Big-endian, four words to a line, the
way `DW` prints them:

```
+00  401b6800  00000000  00000000  3c1a8041
+10  275aeb40  337b007c  035bd021  8f5a0000
+20  00000000  03400008  00000000  00000000
+30  00000000  401a6000  00000000  001ad0c0
+40  07400003  03a0d821  3c1b8041  8f7bdd40
+50  03a0d021  277dff50  afba008c  afa30024
+60  afa00018  40036000  afa20020  afa300a8
+70  afa40028  40036800  afa5002c  afa300ac
```

**Words 0-10 are the dispatcher, and they are the only part of the block that
means anything at `0x80000080`:**

| off | word | | |
|---:|---|---|---|
| `+00` | `401b6800` | `mfc0 k1, c0_cause` | rd 13 |
| `+04` | `00000000` | `nop` | the CP0 read hazard |
| `+08` | `00000000` | `nop` | |
| `+0C` | `3c1a8041` | `lui  k0, 0x8041` | |
| `+10` | `275aeb40` | `addiu k0, k0, -5312` | → `0x8040EB40`, the table |
| `+14` | `337b007c` | `andi k1, k1, 0x7c` | `ExcCode`, already ×4 |
| `+18` | `035bd021` | `addu k0, k0, k1` | |
| `+1C` | `8f5a0000` | `lw   k0, 0(k0)` | |
| `+20` | `00000000` | `nop` | the exposed load delay slot |
| `+24` | `03400008` | `jr   k0` | |
| `+28` | `00000000` | `nop` | branch delay slot |

**Words 11-31 are not a second vector and are not padding either.** The copy is
128 bytes and the dispatcher is 44, so `trap_init` drags in whatever follows it:
words 11-12 are zero, and **word 13, `401a6000` = `mfc0 k0,c0_status`, is the
first instruction of the loader's IRQ handler** — `exception_handlers[0]` is
`0x80400580` and `0x80400580 - 0x8040054C = 0x34`, word 13 exactly. So words 13-31
are a verbatim copy of that handler's first nineteen instructions, sitting at
`0x800000B4` where nothing ever executes them. `07400003 03a0d821 3c1b8041
8f7bdd40` is its stack switch; `afba008c` onward is `SAVE_ALL`.

**Why that matters at the bench**: an operator reading *"the first 11 are live
code"* as *"and the rest should be zero"* would see nonzero words past index 10
and abort `probe2` for nothing.

**Three internal cross-checks, and none of them was constructed after the fact.**
`+10` builds `0x8040EB40`, which is the address `RUNSHEET.md`'s `H0b` reads and
`docs/loader-command-semantics.md` names independently; `+14`'s `0x7c` mask is
the same field `H2c` predicts `cause & 0x7c = 0x24` for; and
`0x8040054C + 0x10 = 0x8040055C`, which the same document already calls *the
table's one reader*. `H0a`, `H0b` and `H2c` are three projections of one finding
— any one of them missing means the other two need re-explaining.

**And the dispatcher is itself a hazard reading.** Two `nop`s after `mfc0` and one
after `lw`, in the copy the core actually executes: that is the vendor's own
belief about this core's hazard depth, on the installed path rather than in an SDK
header. It corroborates what `tools/hazlint` enforces, from a different artefact.

🔴 **Still not measured.** Every word above is read out of a file. The cell
that turns it into a measurement is `DW 80000080 32` at the prompt — and the cell
that makes *that* checkable without trusting this list is `DW 8040054C 32`, the
source of the copy, which must come back word for word identical. Both are
read-only, both are in `RUNSHEET.md` § Session B4 as `H0a` and `H0a2`.
