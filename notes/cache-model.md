# Cache management model — F49

**DAY-ZERO item 2b. Desk work, 2026-08-23. Nothing here was measured on the
device.** Two sources, both read: this unit's own bootcode, disassembled from
its flash dump, and the vendor's Linux 2.6.30 tree for this SoC family.

## Why this blocks three later gates

MIPS-I has no `cache` instruction. 🔄 **This sentence read *"that is MIPS-II and
later"* until 2026-08-28 and the level was wrong**: 量 with the vendor's own
assembler (`tools/isa-probe.sh`), `cache` is rejected for `-march=mips1` **and**
`-march=mips2` **and** `lx4180`, and accepted from `rlx4181` on. `CACHE` is
MIPS-III/MIPS32, and on these cores it is an extension — which does **not** make
this a MIPS32 core, `Config.M = 0` being 量. The R3000
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
| `0x010` 🔄 | **`IMEM0FILL`** | **fill the local instruction scratchpad from `CP3 $0`/`$1`, stalling the core until it is done.** Not a cache command | `stage2` `0x80400514`; **this unit's kernel `0x800022A8`** — both at reset init only | 🔴 **NAMED 2026-08-26, ×4 with two independent.** See below |
| `0x020` 🔄 | **`IMEM0OFF`** | **clear the scratchpad's valid bit**, so fetches from the IMEM region fall through to the I-cache. Not a cache command | `stage2` `0x804004DC`; **this unit's kernel `0x80002240`** — both at reset init only | 🔴 **NAMED 2026-08-26.** See below |
| `0x040` 🆕 | `IMEM0ON` | — | issued nowhere on this unit | 讀 ×1 (`rlxregs.h`), and the sources **contradict** on this bit — see below. **未定** |
| `0x080` 🆕 | *(contested)* | — | issued nowhere on this unit | LX4189 says `IROMOff`; `rlxregs.h` has nothing here. **未定** |
| `0x400`/`0x800` 🆕 | `DMEM0ON` / `DMEM0OFF` | the D-side scratchpad's equivalents | issued nowhere on this unit | 讀 ×1 (`rlxregs.h`) only, absent from the LX4189 map. **Not written by anything of ours** |

⚠️ **`cache-rlx.c` and `c-r3k.c` are two files, not two independent sources.**
Both live in the same GPL drops and both drops descend from the same Realtek
SDK. What changed is that values which had **no name in any source** now have
one; nothing here is a second vote on a value.

## 🔴 `0x010` and `0x020` are named — 2026-08-26, and they were never cache commands

**The route this file left open was *a document*, and the document was in the
GPL drops this project already holds.** Same failure mode as the `arch/rlx/`
one, one section down: the fact was in the tree and the search went elsewhere.

**`0x010` is `IMEM0FILL` and `0x020` is `IMEM0OFF`** — the lifecycle controls
for a **16 KiB local instruction scratchpad**, which is a structure nothing
committed in this repository had ever mentioned. Four sources, two of them
independent of each other:

| | source | what it gives | class |
|:-:|---|---|---|
| 1 | **`arch/rlx/include/asm/rlxregs.h:630-638`**, in **all three GPL drops here** | `CCTL_IMEM0FILL 0x00000010`, `CCTL_IMEM0OFF 0x00000020`, plus `IMEM0ON 0x40`, `DMEM0ON 0x400`, `DMEM0OFF 0x800` | 讀. ⚠️ **One source, not three** — byte-identical, md5 `623d85d7d39efd1906e8b6b842e60e82`, same SDK ancestor as `cache-rlx.c` |
| 2 | **Lexra LX4189 Data Sheet Rel 1.9 § 5.2** *"Cache Control Register: CCTL"* | the same bit positions **and the semantics in prose**: *"A transition from 0 to 1 on IMEMFill causes the LMI to initiate a series of line read operations to fill the IMEM contents… The processor stalls while the entire IMEM contents are filled"*; *"A transition from 0 to 1 on IMEMOff causes the LMI to clear its internal IMEM valid bit. Subsequent cacheable fetches from the IMEM region will be serviced by the instruction cache"* | 讀, **vendor doc, independent of 1** — Lexra is the core vendor, Realtek the integrator |
| 3 | **`refs/RTL8196E-VEx-CG_Datasheet_1.1.pdf` § 1 p.1, § 2, block diagram** | *"a 16Kbyte I-Cache, 8Kbyte D-Cache, 16Kbyte I-MEM, and 8Kbyte D-MEM are provided"* — **the scratchpads exist on this part, with sizes** | 讀, vendor doc, **already in this repo**, already quoted verbatim at `SOURCES.json:195` |
| 4 | 🔴 **this unit's own kernel, `0x80002210`–`0x80002300`** | the **behaviour** | 讀, on an artefact cut from this device |

Source 4 is what turns a name into an explanation:

```
80002220  or    t0,t0,at          ; Status |= CU3   -- so CP3 is reachable
80002230  mtc0  zero,$20          ; CCTL = 0        -- the 0->1 edge, deliberately
80002240  mtc0  t0,$20            ; CCTL = 0x020    IMEM0OFF
8000225c  mtc0  t0,$20            ; CCTL = 0x202    DWBInval | IInval
80002278  and   t0,t0,t1          ; 0x002B8000, masked by 0x0FFFC000 (16 KiB-aligned)
8000227c  mtc3  t0,$0             ; CP3 $0 = IMEMBASE
80002288  addiu t0,t0,16383       ; +0x3FFF  = 16 KiB
8000228c  mtc3  t0,$1             ; CP3 $1 = IMEMTOP
800022a8  mtc0  t0,$20            ; CCTL = 0x010    IMEM0FILL  -- fill it
800022d4  and   t0,t0,t1          ; 0x002C0000, masked by 0x0FFFE000 (8 KiB-aligned)
800022d8  mtc3  t0,$4             ; CP3 $4 = DMEMBASE
800022e4  addiu t0,t0,8191        ; +0x1FFF  =  8 KiB
800022e8  mtc3  t0,$5             ; CP3 $5 = DMEMTOP
```

**Every element corroborates every other.** 16,384 bytes is the datasheet's
I-MEM size; 8,192 is its D-MEM size; the CP3 register numbers are the ones the
third-party `lxregs.h` calls `IMEMBASE`/`IMEMTOP`/`DMEMBASE`/`DMEMTOP`; the CCTL
writes are **clear-then-set**, which is what an edge-triggered control needs and
what source 2 says it is; and `CU3` is set immediately before the first `mtc3`.
**The name and the behaviour explain each other.**

🔴 **And the loader does none of it.** A scan of `stage2.bin` for primary opcode
`0x13` (COP3) returns 97 words, **all data** — every one at or above
`0x8040A5B8`, where `SPEC.md` `CPU-26` already places the loader's data region,
and every one ASCII (`"LOT\n"`, `"NIC_"`, `"MX25"`). **Zero COP3 instructions in
the loader's code**, so it issues `IMEM0OFF` and `IMEM0FILL` over whatever range
reset left. ⚠️ The control on that zero is weaker than usual: the same scanner
finds the four `mtc3`s in the kernel, so it can see a real COP3 instruction — but
that control is on a *different file*, because `stage2.bin` contains none.

🆕 **讀 2026-08-27 (a re-decode of words already in the dump, not a device
reading), and it sharpens that last sentence.** The 97 were counted by primary
opcode alone. Decoding their `rs` field — which in the COPz encoding selects
MF/DMF/CF/MT/DMT/CT/BC/CO and is **not** a register — gives `DMF` × 11,
`CF` × 3, `MFH` × 3, `BC` × 1, `rs=9` × 6, `rs=0x0A` × 21, and `CO` × 52.
**Only three carry an `rs` that MIPS-I defines as a register move** — all three
are `CF` — and none of those three has its low 11 bits zero (`0x40A`, `0x144`,
`0x144`), so **not one of the 97 decodes as a valid `mfc3`/`cfc3`/`mtc3`/`ctc3`**.
The kernel's four do: `0x4C880000`, `0x4C880800`, `0x4C882000`, `0x4C882800`,
at the four addresses above. So the separating property is *is this a
well-formed COP3 **move***, which is stronger than the address split, and the
scanner's positive control is a real instruction rather than a coincidence of
opcode.

🔴 **The obvious stronger claim is false and this file made it for an hour.**
*Not one of the 97 has its low 11 bits zero* — **nine of them do**: eight `CO`
words (`0x4F4C0000` ×3, `0x4F4B0000` ×3, `0x4F480000`, `0x4F000000`) and
`0x4D000000` at `0x8040B24C`. That last one is a **well-formed `bc3f +0`**, so
`stage2.bin` *does* contain a word that decodes as a valid COP3 instruction —
and it is `tools/hazlint`'s own `K9` fixture, the one `strict` is required to
accept. Caught by a reader sent to refute this paragraph. The conclusion above
survives; the premise it was resting on did not, and the word that saves it is
*move*.

⚠️ **And the ISA level under which all of this is read has a caveat that has to
travel with it.** MIPS IV Instruction Set Rev 3.2 A 8.3.4: *"Coprocessor 3 is
optional and implementation-specific in the MIPS I and MIPS II architecture
levels. It was removed from MIPS III and later architecture levels. Note that in
MIPS IV the COP3 primary opcode was reused for the COP1X instruction class."*
Two consequences, and the second is the one that keeps getting dropped:
① reading `0x13` as COP1X is wrong here, because `Config.M = 0` is 量 and this
is a MIPS-I part — `tools/hazlint` and `tools/opcount.py` both did it until
2026-08-27; ② **"it is MIPS-I" is not an argument that the silicon executes it.**
The architecture declines to require COP3 at that level. The four `mtc3` above
run at reset before `trap_init`, where a trap would be fatal, which is the
strongest thing on hand and is still an inference — `probe3`'s `m-imem` is what
turns it into a measurement, and 否證 M is written for the outcome where it does
not.

🔴 **CCTL is edge-triggered on 0→1** (source 2, and the clear-then-set idiom in
both codebases on this unit). *Writing a bit that is already 1 does nothing* — so
**a probe that writes CCTL once and expects an effect is a tool that cannot
fail.** `rlx_cctl` (讀, `cache.S:70-81`) already does clear / write / clear, and
`CPU-39` measured that CP0 20 reads zero on this die, so the read-modify-write
form the Realtek SDK uses for RLX4181 degenerates to the plain write here.

⚠️ **What is NOT settled.** Bits 6–7 **contradict across sources** (LX4189:
`IROMOn`/`IROMOff`; `rlxregs.h`: `IMEM0ON` at bit 6 and nothing at bit 7). And
the LX4189 is a **write-through** part with no `DWB`/`DWBInval` at all, so its
bits 8–9 are Reserved and live here: **the two maps are provably not identical.**
`0x010` and `0x020` are the only bits every source agrees on without
contradiction — which is exactly the pair that was asked.

🔴 **The consequence, and it is first-order for `CPU-25`.** *"When IMEM is
invalid, all cacheable fetches from the IMEM region will be serviced by the
instruction cache"* — read the other way round, **while it is valid they are
not.** The I-MEM is **16 KiB and the predicted I-cache is 16 KiB**, so no size
measurement can tell them apart. `docs/probe3-cells.md` § 1.2 owns what `probe3`
does about it: read `CP3 $0`/`$1`, and re-run the walk with `CCTL 0x020` issued.
⚠️ One retrospective comfort and only that: `probe1` cell 2 (`CCTL 0x002`) read
`02` FRESH ×2, and a victim inside a live IMEM should have stayed STALE — 推,
about `probe1`'s addresses, transferring to none of `probe3`'s.

*(The old text here said the two values were "still undetermined, and no source
names them", that the deciding route was "a document", and that a payload writing
them was declined. The document is found; the decline stood on the values being
**unnamed** and that premise is gone. `probe3` writes `0x020` as a control and
still declines `0x010` — for a new reason, in `docs/probe3-cells.md` § 8.
The line before that said "R1e or a `devmem`-class read would settle them"; `R1e`
ran and could not, because **a read side that is always zero cannot name a write
side** — `CPU-39`.)*

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
op in this build, so there is no threshold constant to read.

🔴 **2026-08-26, second correction, and this one is the opposite direction.** The
sentence that used to end this paragraph — *"it stays 留白 with no source of any
kind"* — is **wrong, and it was wrong on the day it was written.**
`refs/RTL8196E-VEx-CG_Datasheet_1.1.pdf` states the geometry on its own first
page, in three places: § 1 *"a 16Kbyte I-Cache, 8Kbyte D-Cache, 16Kbyte I-MEM,
and 8Kbyte D-MEM are provided"*; § 2 Features, the same words; and the block
diagram, *"I-Cache=16kB / D-Cache=8kB"*. **`SOURCES.json:195` has quoted that
sentence verbatim since the source index was written.** So both sizes have had a
vendor-datasheet source in this repository all along — the same failure as
`arch/rlx/` two sections up: **the fact was in the project and the search went
somewhere else.**

⚠️ **What the datasheet does *not* give**: no line size and no associativity. A
grep for *"cache line"*, *"line size"*, *"associat"* over all 11,467 extracted
lines returns only switch-MAC-table hits (*"1024 entry 4-way hash L2"*), which is
a different structure. 🔴 **So the thing with no source of any kind, anywhere, is
the associativity of either cache** — not the I-cache size.
⚠️ And the datasheet is a **draft**, its part number is `RTL8196E-VE1/2/3-CG`,
and **the `-VEx` suffix has never been verified on this unit** — identification
rests on `0xB8000000 → 0x8196E001` (量) plus the silkscreen.

⚠️ **And none of it is 量.** A build constant is what the vendor's kernel
*believes* about its own silicon. It agrees with the third-party
`rtl8196e.dtsi` — which is worth something, because those two sources have no
common ancestor on this point — but two beliefs agreeing is still not a
measurement. **It is a prediction with a refutation condition, and it is only
worth writing down because it is written before the walk that tests it.**

| | prediction | refuted by |
|---|---|---|
| I-cache | **16 KiB** — 🔄 **讀 ×2, and the stronger one is a vendor datasheet in this repo**: `refs/RTL8196E-VEx-CG_Datasheet_1.1.pdf` § 1 / § 2 / block diagram, and the third-party dtsi. 🔴 **⚠️ That datasheet is the `-VE1/2/3` variant, and `SOURCES.json` records this unit as NOT being it** — embedded DRAM by MCM against this unit's external W9825G6KH (`MEM-01`, 量), and `CPU-02`'s silkscreen carries no variant suffix at all. The **public `RTL8196E-CG`** datasheet makes the same claim, so it is **two Realtek documents about two variants of a family this die is 量-confirmed to belong to** (`CPU-01`, ×3) — worth more than one document, and still not a reading of this die. *(This row said "still one source, and it is the third-party one" until 2026-08-26. It was wrong: `SOURCES.json:195` already carried the datasheet's sentence.)* | 🔄 **a `probe3` eviction walk** (was: `probe1`'s `GEOM=1` walk, which cannot answer on this core). 🔴 **And the walk cannot separate a 16 KiB I-cache from the 16 KiB I-MEM by size** — see § `0x010`/`0x020` above |
| D-cache | **8 KiB** — 🔄 **讀 ×3 with no common ancestor**: the datasheet (⚠️ variant caveat above), `0x4000` = `cpu_dcache_size * 2` in this unit's own kernel, and the dtsi | the same |
| associativity 🆕 | 🔴 **留白 — no source of any kind, anywhere.** Not the datasheet, not any GPL drop, not the dtsi. Split out 2026-08-26 because this, and not the I-cache size, is the blank | the pattern in `probe3`'s stride sweep. If that walk fails, this stays blank |
| I-MEM / D-MEM 🆕 | **16 KiB / 8 KiB local scratchpads** | 讀 ×2 — the datasheet's sizes, and this unit's kernel programming `+0x3FFF` and `+0x1FFF` into `CP3 $0`/`$1` and `$4`/`$5`. **Refuted by `probe3` reading those four registers** |
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

## 🔴 The core vendor's own datasheet is in hand — 2026-08-26, `R1h-1`

`SOURCES.json`'s `ds-lexra-lx4189` entry ended *"NOT DOWNLOADED INTO `refs/`:
cited only. If it is ever fetched it moves to `documents` WITH a sha256."* It was
fetched (sha256 `6afb1415…`; the PDF is **not committed** — `CLAUDE.md` forbids
it — and lives in `$FWRE_WORK/rebuild/refs-external/`). This section is what it
changes in **this** file; `docs/probe3-cells.md` § 1.4 owns what it changes in
the cell table.

⚠️ **READ THIS BEFORE QUOTING ANY LINE BELOW.** The caveat this project already
carried — *"LX4189 is a write-through part with no `DWB`/`DWBInval`, so the two
CCTL maps are provably not identical"* — got harder rather than softer.
**Table 2 lists the LX4189's entire CP0 register file: 8 `BADVADDR`, 12 `STATUS`,
13 `CAUSE`, 14 `EPC`, 15 `PRID`, 20 `CCTL`, and nothing else. It has no TLB.**
This die has 32 TLB entries — `CPU-08`, 量, corroborated by `probe2`'s census
reading `Random` at 5…29 inside 0…31. **The LX4189 is a sibling and is
demonstrably not this part.** Everything below is 讀 about a related core, from
the core vendor, where every other source here is the integrator or a third
party.

### Cache geometry, from the vendor rather than from a build constant

| | LX4189 § | what it says | what this file said before |
|:-:|---|---|---|
| line size | 5.1, 5.6 | configurable **16 / 32 / 64 / 128 bytes** — *"the cache obtains a cache line (4, 8, 16, or 32 words)"* | nothing; the 16 B here comes from eight `cache` ops at stride `0x10` in this unit's kernel, which is one build's belief |
| I-cache associativity | 5.1 Table 18, 5.3 | *"Direct mapped or two-way set associative"*, with the two-way form's LRU and lock bits described | **"no source of any kind, anywhere"** — withdrawn |
| D-cache associativity | 5.1 Table 18, Table 25 | *"Direct mapped data cache"*, and all seven configurations are direct mapped | as above |
| D-cache write policy | 5.6 | write-through, and **no write-allocate**: *"all data writes that miss the cache are forwarded to the write buffer of the LBC, without disturbing any data currently in the cache"* | ⚠️ **does NOT transfer.** This SoC's `CCTL` has `DWB`/`DWBInval`, which a write-through cache does not need, and both GPL drops build `CONFIG_ARCH_CACHE_WBC=y` |
| write buffer | 5.6 | there is one, in the LBC: *"Writes … may require extra time to be serviced by the LBC if its write buffer is full"* | nothing — and it is what cell `c-E0` controls for |

### 🔴 Two sentences about coherence, and they are what a proxy cannot tell you

LX4189 § 5.2, on alternatives to a full D-cache invalidation:

> *"Another alternative, if the affected memory location has an alias in
> uncacheable (KSEG1) space, is to simply perform an uncached read of the
> affected memory locations. **If the location is resident in the data cache it
> will be invalidated.** … **Note that a write to a KSEG1 address has no affect
> on the contents of the data cache.**"*

And § 5.1: *"**Caches do not snoop the system bus.**"*

Three things follow and none of them was in this file:

1. **An uncached READ is a per-line invalidate**, with no `CCTL` at all. If that
   holds here, `R6` gets an invalidate primitive for the price of a load. It has
   never been tested on this die; `probe3`'s cell `c-G` is the first attempt.
2. **An uncached WRITE does nothing to the cache**, which is what makes the
   KSEG0/KSEG1 alias a usable stand-in for a device write at all — and it gives
   `c-A` an expected value where this file had none.
3. 🔴 **The proxy and the thing differ, and the core vendor says so.** A real bus
   master is **not snooped**; an uncached CPU read **is** handled specially. So
   *"a real DMA write looks like an uncached CPU store from the cache's side"* is
   not a safe assumption — it is a proxy assumption with a document against part
   of it. `docs/rlx-cache-and-cp0.md` § ② carries what that means for `R6`.

### And one datum about the core's identity that changes nothing

Table 2: **`PRID` reads `0x0000c401` for the LX4189.** This unit reads
`0x0000CD01` (量, `CPU-04`). That is the first point this project has had on the
Lexra `PRId` map, and **it says exactly one thing: `0xCD01` is not an LX4189.**
Nothing here maps the space between `0xC4` and `0xCD`. **`CLAUDE.md`'s ban
stands** — a point is not an assignment table, and `RLX4181` and `RLX5281` are
both still unwritable.

🔄 **2026-08-27: the assignment table exists and it was in the vendor tree this
file already reads.** `arch/rlx/include/asm/cpu.h` maps `PRID_IMP_RLX4181` to
`0xcd00`, so `0x0000CD01` is `RLX4181` revision 1 and `RLX5281` (`0xdc01`) is
positively excluded. The paragraph above is left as written because it was the
right judgement on the evidence it had; what it was waiting for arrived.
`notes/vendor-kernel-isa.md` §5 owns it, weaknesses included — the table is one
source in three copies and no code in the port reads it.

*(§ 3.4.2 also gives `0x8000_0080` as the general exception vector with
`BEV = 0` — a fourth independent source, agreeing with the three this file
already records. Nothing changes; it is noted because the wrong address had
reached seven committed sites as recently as 2026-08-25.)*

---

## 🔴 `F49` from the source side — 2026-08-27, `R2a/b/d-2`

The plan's grep for this was `r3k_cache_init|r4k_cache_init|rlx` over
`arch/mips/mm/`. **Two things are wrong with it and both would have produced a
zero.** The path is `arch/rlx/`, and this port has neither of those functions:

```c
/* arch/rlx/mm/cache.c:166 */
void __cpuinit cpu_cache_init(void)
{
    extern void __weak rlx_cache_init(void);
    rlx_cache_init();
}
```

Unconditional — no probe, no branch, a third implementation in
`arch/rlx/mm/cache-rlx.c`. The same grep over `arch/mips/mm/cache.c:161–173`
*does* find the r3k/r4k branch, which is the scanner's liveness control: the
needles are fine, the tree was wrong.

### What this file already believed, now with the `#ifdef` that produces it

`cache-rlx.c` picks its primitives from the CPU model and the cache type. For
`CPU_RLX4181` with `CPU_HAS_WBC` and no `WBIC`, no `L2C`:

| | for this part | what it explains |
|---|---|---|
| `CONFIG_CPU_HAS_DCACHE_OP` | **defined** — 4181/5181/4281/5281 | D side uses the `cache` instruction. 🔄 **Not "MIPS-II"** — 量 2026-08-28 with the vendor's own assembler: `cache` is rejected for `-march=mips1`, `mips2` and `lx4180`, accepted from `rlx4181` on. `CACHE` is MIPS-III/32 and here it is an extension; `Config.M = 0` still says this is not a MIPS32 core |
| `CONFIG_CPU_HAS_ICACHE_OP` | **not defined** — 4281/5281 only | 🔴 I side uses **CCTL `0x2`**, and that is why `CPU-44`'s scan of this unit's kernel found **zero** I-side `cache` ops. It was an observation; it is now a consequence |
| `CACHE_DCACHE_FLUSH` / `WBACK` | `0x15` `DWBInval` / `0x19` `DWB` | the two op-field values `CPU-44` read, and they collapse to `0x11` if `WBC` is off |
| `CCTL_DCACHE_WBACK` / `FLUSH` | `0x100` / `0x200` | this file's own table |
| unroll | `CACHE16_UNROLL8`, taken when `cpu_dcache_line != 32` | eight ops at stride `0x10` — exactly the shape in the binary |
| `CCTL_OP` (not 4281/5281) | `mfc0 $8,$20` `ori` `xori` `mtc0 $9` `mtc0 $8` | a second file agreeing that CCTL is **0→1 edge triggered** |

### Geometry, from the board rather than from a build constant

`boards/rtl8196e/bsp/bspcpu.h`, byte-identical in all three drops, under
`CONFIG_RTL_8196E` (which `boards/rtl8196e/config.in` sets `def_bool y`):

```
cpu_icache_size  16 KiB     cpu_dcache_size   8 KiB     cpu_scache_size  0
cpu_icache_line  16         cpu_dcache_line  16         cpu_tlb_entry   32
```

**The 16-byte line now has two sources**, and the second is this unit's own
binary: `CACHE16_UNROLL8` is only selected when the line is not 32, and that is
the unroll `CPU-44` read. The 32 TLB entries agree with `CPU-08`, measured on
the device by a route with no TLB probe in it.

⚠️ **The header contradicts itself and it is worth recording**:
`cpu_dcache_line_mask` is hard-coded `0xF` in both branches, so a board taking
the 32-byte branch gets a 16-byte mask. Not this board's problem. A real defect
in the vendor header.

⚠️ **Associativity still has no source here.** The LX4189 table above says direct
mapped; nothing in the GPL drops says anything, and the two documents are about
different cores.

### And the write policy, where the datasheet and the drops disagree

The LX4189 table above records *write-through, no write-allocate*, and this file
already noted that it does not transfer, because this SoC's `CCTL` has
`DWB`/`DWBInval` at all. The drops make that explicit rather than implicit:
`ARCH_CACHE_WBC=y` in `boards/rtl8196e/config.in` and `CONFIG_CPU_HAS_WBC=y` in
all five shipped `RTL8196E_*` configs, and the four op-field constants above
**collapse to `0x11`/`0x1` if it is off** — so the kernel's own choice of `0x15`
and `0x19`, read out of this unit's binary, is downstream of a write-back cache.

**That is still 讀, not 量.** `CPU-19`'s residual asks which policy the silicon
implements, and a config file is the vendor's belief about their own part, not a
measurement of it.

---

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

---

## 🔴 The geometry is measured — 2026-08-29, on silicon

This file has carried the geometry as *"a prediction with one weak source"* and
then as *"from the board rather than from a build constant"* — both readings of
`bspcpu.h`. `probe3`'s I-side eviction walk ran on the device on 2026-08-29
(`bench/2026-08-30/QJ.log`), and the numbers are now measurements.

| | measured | previously | agreement |
|---|---|---|---|
| I-cache size | **16 KiB** | 16 KiB (讀, `bspcpu.h:14`) | yes |
| I-cache line | **16 B** | 16 B (讀, `bspcpu.h:19`, under `CONFIG_RTL_8196E`) | yes |
| associativity | **2-way** (量); **512 sets** is 推 | LX4189 says *"direct mapped **or** two-way set associative"* — a sister core's document, and a **disjunction** | ⚠️ a disjunction over {1, 2} is **not** a second vote for 2: it excludes 4- and 8-way and nothing more |
| D-cache | **not measured** | 8 KiB / 16 B (讀, `bspcpu.h:13`) | **no measurement exists** |

### The walk, and both of its controls

```
w.size 00000001 n=00000020 fresh=00000000      1 KiB, 32 victims
w.size 00000002 n=00000040 fresh=00000000      2 KiB
w.size 00000004 n=00000080 fresh=00000000      4 KiB
w.size 00000008 n=00000100 fresh=00000000      8 KiB
w.size 00000010 n=00000200 fresh=00000014     16 KiB, 20 of 512
w.size 00000020 n=00000400 fresh=00000400     32 KiB, all
w.size 00000040 n=00000800 fresh=00000800     64 KiB, all
```

**否證 ⓐ is satisfied in both directions.** Its written negative control — *every
victim must come back STALE at a working-set size no cache could evict from* —
holds at 1, 2, 4 and 8 KiB. Its other side — the walk must be **able** to evict,
or a small number is the tool failing rather than the cache filling — holds at
32 and 64 KiB with every victim FRESH. A walk that satisfied only one of those
would have produced a number that is **void, not approximate**, which is what
this file's refutation condition says.

**It also reproduces inside the seating**: `bmp.rerun.fresh=00000014` re-ran the
16 KiB point and returned the same 20.

⚠️ **FRESH appears one step earlier than the block predicted.** The prediction was
*all STALE up to 16 KiB, FRESH at 32 KiB*. What happened is 20 of 512 at 16 KiB
— 3.9 %. 🔴 **The first version of this paragraph explained that as "a working
set that exactly fills the cache", and that is false.** `W_STRIDE` is 32
(`probe3.c:358`) over a 16-byte line, so the walk touches only **even sets: 256
of 512, two victims each** — it fills half the sets in both ways, not the cache.
The correct reading is the payload's own footprint colliding once both ways are
occupied, and §*the argument for two-way* below turns that into a positive
prediction that the data confirms. An 8 KiB cache is excluded on the numbers
rather than on the story: it would give **512 of 512** at a 16 KiB working set,
not 20.

### Line size, and it is read off victim offsets rather than assumed

`w.line.bits=11222222` and `w.line.bits2=22222000`, against
`L_LINE[] = {13, 0, 8, 16, 24, 32, 48, 64, 96, 128, 160, 192, 256, 320}`
(`probe3.c:378`) and the verdict nibbles `V_STALE=1`, `V_FRESH=2`, `V_NEVER=0`
(`probe3.c:287-294`):

* offset **0** — STALE
* offset **8** — STALE
* offset **16** — FRESH, and every offset above it

**The fetched line covers 0 and 8 and not 16: a 16-byte line.**

`w.line0`, the no-fetch negative control, read `22222222` — all FRESH. Without
it, *all FRESH* at every offset would be indistinguishable from a patch that
never landed.

### Associativity — and the argument below replaces a circular one

`w.assoc.tm=00002003` packs `(best_t & 0xFFFFFF00) | (best_m & 0xFF)`
(`probe3.c:1404`), so **T = 8,192 and M = 3**, with
`w.assoc.capped=00000000` — the search was not clipped by its own bound.

🔴 **The argument for two-way is the argmin over `T`, and it is written out here
because the first version of this section gave a circular one.** What I wrote
was *"T = 8,192 is exactly the way size of a two-way 16 KiB cache — which is
exactly the T the search settled on"*. That is a consistency check dressed as a
derivation: it assumes the size and the ways to explain a number it then offers
as evidence for them. **`M = 3` alone does not imply two ways** — it is equally
"two ways in one set" or "one way in two sets", so direct-mapped at half the way
size gives `M = 3` too.

What discriminates is *which* `T` minimises `M`. `probe3.c:1371-1404` searches
`t ∈ {2048, 4096, 8192, 16384}` and keeps the strictly smallest `M`:

| hypothesis | M at 4096 | M at 8192 | M at 16384 | reported (T, M) |
|---|---:|---:|---:|---|
| 8 KiB, 2-way | **3** | 3 | — | (4096, 3) |
| 16 KiB, **1-way** | 5 | 3 | **2** | (16384, 2) |
| **16 KiB, 2-way** | 5 | **3** | 3 | **(8192, 3)** ✅ |
| 16 KiB, 4-way | **5** | 5 | — | (4096, 5) |
| 32 KiB, 2-way | — | 5 | **3** | (16384, 3) |

**`(8192, 3)` is unique to 16 KiB two-way.** `w.assoc.capped=00000000` says
`T = 16384` really was tried and really did not yield `M = 2`, so the
direct-mapped row is excluded by a reading rather than by assumption.

🔴 **And the four zero rows are themselves the two-way signature.** The one
cached function that must execute between patch and exec is
`rlx_call2_uncached`'s wrapper — `probe3.map` puts it at `0x805001dc`, physical
`0x005001e0`, which is **set 30** under 16 KiB/2-way/16 B. Under direct mapping
that line would evict its victim at *every* working set, so `w.size` would read
non-zero at 1, 2, 4 and 8 KiB. It reads zero at all four. Under two-way the
pollution can only bite once the victims already fill both ways — i.e. only at
16 KiB. **量: the first FRESH victim in the boundary rerun is `k=15` at
`0x80A301E0`, which is also set 30.** One in ~128 by chance.


### 🔴 What the kernel prints is a build constant, and this file is where that has to be said

The `loud` boot prints
`icache: 16kB/16B, dcache: 8kB/16B, scache: 0kB/0B`. 讀,
`arch/rlx/bsp/bspcpu.h:12-22` — every one of those numbers is a `#define`, and
`cache-rlx.c:378` only prints them. They are used in `#if` **preprocessor**
conditionals at `:99`, `:438` and `:649` in that same file, which is proof they
are compile-time constants rather than variables a probe could have filled.

**So there is exactly one measurement and one constant, and they corroborate.**
`R1h-4`'s DoD asks for that distinction *even when the numbers agree*, and the
same line shows why: `dcache: 8kB` is the same kind of constant, and **no D-side
measurement was taken** — Group V was voided by `c-A` coming back negative.
Reporting the printed line as *the geometry* would put an unmeasured 8 KiB
beside a measured 16 KiB in one sentence.

⚠️ **The size measurement still cannot separate the I-cache from the 16 KiB
instruction scratchpad** (`CPU-46`) — they are the same size, which this file has
recorded as a hazard since 2026-08-26. `w-imem` is the cell for it and it stays
未定: `w.imem.differs=00000000`, and the payload printed
`IDENTICAL -- and that is also the no-op reading` because CP0 20 is write-only
(M4), so nothing confirms the `CCTL 0x020` was accepted. **The associativity is
not exposed to that confound** — a scratchpad has no sets — which is the one
part of the geometry the scratchpad cannot be masquerading as.
