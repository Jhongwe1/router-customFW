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

1. Write the handler to `0x80000080` through **KSEG1** (`0xA0000080`), which
   sidesteps the D-cache entirely, then invalidate I-cache with CP0 20 `0x002`.
   🔴 **And cover `0x80000000` too** — that is the UTLB refill vector on this
   layout, the loader never populated it, and stage 1's DRAM-sizing probe left
   `0x5A5AA5A5` sitting there.
2. Keep the CP0 20 `0x200` D-cache flush before it as the vendor does, because
   the vendor's own comment says the two caches can hold the same address.
3. **Both of those are single-source for the exact bit values.** Before either
   goes into `rlxprobe`, confirm on silicon: write a handler, take an exception,
   and check it ran. That check is its own control — if the I-cache still holds
   the old bytes, the handler does not run and the probe hangs rather than
   lying.

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
