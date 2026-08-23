# Cache management model — F49

**DAY-ZERO item 2b. Desk work, 2026-08-23. Nothing here was measured on the
device.** Two sources, both read: this unit's own bootcode, disassembled from
its flash dump, and the vendor's Linux 2.6.30 tree for this SoC family.

## Why this blocks three later gates

MIPS-I has no `cache` instruction; that is MIPS-II and later. The R3000
generation used `Status.IsC` / `Status.SwC` and byte stores instead — a
completely different mechanism. Which one this core uses decides:

- **R1d** — the bare-metal probe writes an exception handler into RAM at
  `0x80000180` and then has to make the I-cache see it.
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

CP0 register 20 has no meaning in MIPS-I or MIPS32 (binutils prints it as
`c0_xcontext`, which is the MIPS64 name and cannot be what this is). Lexra
documents a CP0 register named CCTL "used to control the instruction and data
memories", accessed with `mtc0`/`mfc0` variants — which is the shape observed.
**Calling this register CCTL is inference from the Lexra documentation plus the
observed behaviour, not something either source states.**

## What is written to CP0 register 20

Every use in both sources is the same idiom: clear, write a command, clear.

```
mtc0 $0, $20      nop
li   $8, <value>
mtc0 $8, $20      nop  nop
mtc0 $0, $20      nop
```

| value | meaning | sources | status |
|---:|---|---|---|
| `0x001` | flush D-cache | `c-r3k.c` `r3k_flush_dcache_range()`, `CONFIG_RTL865XB` path | **one source** |
| `0x002` | **invalidate I-cache** | `c-r3k.c` `r3k_flush_icache_range()`; `stage2` `0x804066e8` | **two sources, agree** |
| `0x200` | flush D-cache (819x variant) | `c-r3k.c`, `CONFIG_RTL8652`/`CONFIG_RTL_819X` path; `stage2` `0x804066c0` | **two sources, agree** |
| `0x202` | `0x200 \| 0x002` — both, in one write | `stage2` `0x804004f8`, boot init | inferred from the two above |
| `0x010` | — | `stage2` `0x80400514`, boot init only | **undetermined** |
| `0x020` | — | `stage2` `0x804004dc`, boot init only | **undetermined** |

The two undetermined rows have exactly one source each and no name in any
source. They are recorded here rather than guessed at. R1e or a `devmem`-class
read is what would settle them.

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

## Not established

Nothing here is a measurement on the device. Both sources are code. In
particular:

- That `Status.IsC` **works** on this core is read out of the kernel source,
  not observed. The bootcode never uses it.
- The `0x010` and `0x020` boot-init commands are unexplained.
- Cache line size, associativity and total size are unknown. `c-r3k.c` sizes
  the caches at runtime with `r3k_cache_size(ST0_ISC)` — that routine is
  therefore also a ready-made measurement for R1d to reproduce bare metal.

**Refutation condition, for the record:** the claim "this core uses the R3000
cache model, not the MIPS32 `cache` instruction" is refuted by finding a `cache`
instruction (primary opcode `0x2F`) anywhere in vendor code that executes. The
scan of `stage2.bin`'s code region found none; the one whole-file hit at
`0x8040d264` decodes as `cache 0x0,786(zero)`, sits after a function epilogue
and before zero padding, and is data (`notes/lwl-mystery.md`).

## What R1d should do with this

1. Write the handler to `0x80000180` through **KSEG1** (`0xA0000180`), which
   sidesteps the D-cache entirely, then invalidate I-cache with CP0 20 `0x002`.
2. Keep the CP0 20 `0x200` D-cache flush before it as the vendor does, because
   the vendor's own comment says the two caches can hold the same address.
3. **Both of those are single-source for the exact bit values.** Before either
   goes into `rlxprobe`, confirm on silicon: write a handler, take an exception,
   and check it ran. That check is its own control — if the I-cache still holds
   the old bytes, the handler does not run and the probe hangs rather than
   lying.
