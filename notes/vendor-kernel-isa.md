# What this unit's vendor kernel uses, and what it emulates

**`R2a/b/d-2`, desk, 2026-08-27. No power, no flash byte, no device reading.**
This is the owner of `R2d`'s two greps. Every claim below is marked *read out of
the source*, *read out of this unit's binary*, or *inferred*. Nothing here was
measured on the silicon; `R1a` and `R1h` are what will do that.

## The material, and why it is two materials

| | |
|---|---|
| **this unit's kernel** | `r0-vendor-kernel.bin` (sha256 `396561a0…`, 987,138 bytes, cut from this unit's flash dump) decompressed from offset `0x2808` → **3,374,772 bytes, sha256 `cf0d60a8…`**. Banner: `Linux version 2.6.30.9 (admin@office.hopeiot) (gcc version 4.4.5-1.5.5p2 (GCC)) #1526 Wed Jan 10 14:50:54 CST 2018` |
| **three GPL drops** | `src-vendor/{rtl819x-toolchain, saturn49-wecb/rtl819x, wecb-vz-gpl/rtl819x}`, each carrying `linux-2.6.30` |

They are not interchangeable and the conclusions are kept apart throughout. The
drops say what Realtek's source does; the binary says what *this* build did.
Where they disagree — and they do, twice — that is recorded as a disagreement.

**The plan's grep path was wrong and would have returned a false zero.**
`plan/router-rebuild-plan.md:415`–`433` greps `arch/mips/`. This SoC's port is
**`arch/rlx/`**, a sibling tree beside `arch/mips/` in all three drops. Every
needle below was run against both, so `arch/mips/` is the scanner's own liveness
control: it is present, it is not what was built, and the same grep finds hits in
it. A scan that found nothing in `arch/rlx/` and nothing in `arch/mips/` would be
a broken scanner; a scan that finds hits in one and not the other is an answer.

**Which port was built is read, not assumed.** Three literals that exist only in
`arch/rlx`-only files are present in this unit's binary, and none of them exists
anywhere under `arch/mips`:

| literal | source | in this unit's kernel |
|---|---|---|
| `rlx timer` | `arch/rlx/kernel/rlx-cevt.c:139,226` | yes |
| `RLX LOPI` | `arch/rlx/kernel/irq_vec.c:36` | yes |
| `cpu model\t\t: %d` | `arch/rlx/kernel/proc.c:29` — `arch/mips/kernel/proc.c:40` prints `%s V%d.%d` instead | yes |

🆕 **2026-09-02: `arch/rlx/kernel/` carries `rlx-time.c` AS WELL AS
`rlx-cevt.c`**, and the row above is unaffected — `rlx-cevt.c` is still a file
`arch/mips` does not have, which is all the discriminator needs. It is noted
because a reader will ask why the timer literal was taken from the second file
and not the first, and because a `grep -ril rlx-time` over *this repository*
returns **0 files**: nothing here has ever cited `rlx-time.c`. 🔄 **2026-09-04: that stopped being true**, and the file turned out to be a shim — `docs/blind-write-ledger.md` § 4.3. The 2026-09-02 reading is kept as written; it is a dated measurement, not a standing claim. 量, directory
listing, no file opened; `docs/blind-write-ledger.md` § 4.3 owns what that
absence does and does not mean.

⚠️ **A first attempt at this was a null instrument and is recorded because it
was.** Harvesting every C string literal from `arch/rlx` and from `arch/mips` and
taking the set difference gives **0** rlx-only literals: `arch/rlx` is a fork of
`arch/mips`, so almost every string it has, `arch/mips` has too. The three above
were found by looking at files unique to `arch/rlx`, not at strings unique to it.
The filter that killed the good needles was the harvester's own: it dropped any
literal containing `%` and any containing a tab, which is exactly what
`cpu model\t\t: %d` is.

---

## 1. Grep ① — what the kernel emulates

`do_ri()` is `arch/rlx/kernel/traps.c:546`. Read:

```c
#ifndef CONFIG_CPU_HAS_LLSC
    if (status < 0) status = simulate_llsc(regs, opcode);
#endif
#if 0
    if (status < 0) status = simulate_rdhwr(regs, opcode);
#endif
#ifndef CONFIG_CPU_HAS_SYNC
    if (status < 0) status = simulate_sync(regs, opcode);
#endif
```

and `do_cpu()` handles `cpid == 0` only, falling to `force_sig(SIGILL)` for
everything else. There is **no `arch/rlx/math-emu/` directory in any of the three
drops** (`arch/mips/math-emu/` and `arch/x86/math-emu/` both exist, which is the
control that the `ls` was looking in the right place).

The switches come from `boards/rtl8196e/config.in`, Realtek's own board
definition for this exact part, and they are the same in all three drops:

```
config ARCH_CPU_RLX4181   default y
config ARCH_CPU_EB        default y
config ARCH_CPU_ULS       default y      # unaligned load/store
config ARCH_CPU_LLSC      default n
config ARCH_CPU_SYNC      default n
config ARCH_CACHE_WBC     default y      # write-back D-cache
config ARCH_CACHE_L2C     default n
```

and the five shipped `.config`s (`config.linux-2.6.30.RTL8196E_*`) agree:
`CONFIG_CPU_RLX4181=y`, `CONFIG_CPU_HAS_ULS=y`, `CONFIG_CPU_HAS_WBC=y`, and no
`CONFIG_CPU_HAS_LLSC`, no `CONFIG_CPU_HAS_SYNC`.

⚠️ **The first survey of those configs reported ULS=0 for `rtl8196e` and it was a
false zero from a missing file** — `boards/rtl8196e/` has no plain
`config.linux-2.6.30`, only five suffixed variants, and `grep -l` on a file that
does not exist returns nothing without saying so. Caught by asking why the board
also had no `ARCH_CPU_RLX` line.

### The table

| | core has it | kernel emulates it | how that is known |
|---|---|---|---|
| `ll` / `sc` | **undetermined — see §6** | **yes** — `simulate_llsc` is compiled in | source: `ARCH_CPU_LLSC=n`. binary: **0** `ll` and **0** `sc` in 2.85 MB of MIPS32 text. `atomic.h`'s non-LLSC path is `raw_local_irq_save`, so an LLSC build would put hundreds of them in `.text`. ⚠️ **That is the build, not the die**: `ARCH_CPU_LLSC` is a per-board Kconfig knob, and §6 measures the vendor assembler *accepting* `ll`/`sc` for `-march=rlx4181`. The two vendor sources disagree and this row does not resolve them |
| `sync` | **no (推)** | **yes**, as a no-op | source: `ARCH_CPU_SYNC=n`. binary: **0** `SPECIAL`/`0x0f` in the text span. **The one row where the project's two-source rule is actually met**: §6's assembler table rejects `sync` for `rlx4181` and accepts it for `rlx5281`, which is the same split the board configs make |
| `rdhwr` | — | **no** | source: both call sites are `#if 0`. `arch/mips/kernel/traps.c` calls it unconditionally — this is a vendor edit, not a config |
| FPU (COP1) | **undetermined** | **no** | source: no `math-emu` under `arch/rlx`; `do_cpu` gives `SIGILL` for `cpid != 0`. binary: 0 `lwc1`/`swc1`/`sdc1` in the text span, and 0 occurrences of `fpu_emulator`, `cp1emu`, `FPU emulator` as strings. ⚠️ **Every one of those is about emulation, so none of them is evidence that the core has no FPU** — this column was answered from the wrong evidence until 2026-08-28. `Status.CU1` on the device is what decides it. ⚠️ And "0 FPU opcodes" is 0 `lwc1`/`swc1`/`sdc1`; the span also holds **1** `COP1` at `0x80188938` and **2** `ldc1` at `0x801888C8`/`0x80188A1C`, all three inside the non-code island §"What could still be wrong" item 1 names, i.e. excluded by adjudication and not by a bound |
| `lwl`/`lwr`/`swl`/`swr` | **yes** | **no**, and none is needed | source: `ARCH_CPU_ULS=y`, and `unaligned.c` *uses* them. binary: **101** idiom pairs, see §2 |
| unaligned **address** (AdEL/AdES) | — | **yes** | `do_ade()` → `emulate_load_store_insn()`. Its three `die_if_kernel` strings are all present in this unit's binary: `Unhandled kernel unaligned access`, `Unhandled kernel unaligned access or invalid instruction`, `Kernel unaligned instruction access` |

🔴 **This refutes one clause of `CLAUDE.md`'s bench rule.** That rule says *"the
kernel emulates `ll`/`sc` and the FPU, so you would measure the kernel"*. The
`ll`/`sc` half is confirmed. **The FPU half is wrong for this kernel**: there is
no floating-point emulator in it at all, and an FPU instruction from userspace
gets `SIGILL`. The rule's *conclusion* — measure the ISA bare metal — is
untouched, because `simulate_llsc` alone is enough to make a Linux-side ISA
measurement meaningless. Only the reason needs narrowing.

⚠️ **`do_ade` is not the discriminator for `lwl`.** It handles Address Error, i.e.
a misaligned address given to an aligned instruction. A *missing* instruction
raises Reserved Instruction and lands in `do_ri`, which has no unaligned
emulation at all. So finding the AdE emulator says nothing about whether the core
implements `lwl` — it was the first thing this step found and it is the first
thing that had to be set aside.

---

## 2. `C-7` / `F51` — the unaligned instructions

`notes/lwl-mystery.md` asked, as the discriminator: *does the vendor kernel carry
an unaligned-access emulation handler?* The answer is **no such handler exists**,
and the reason is that the core does not need one.

### 2.1 The idiom, and an instrument that can fail

`tools/opcount.py --pairs`, new today. Instead of counting opcodes it looks for
the pair: same `rt`, same base register, byte offsets exactly three apart, within
a few words. Four fields must agree at once, and the pair's **orientation** is a
second reading — on a big-endian target the `l`-half sits at the lower offset, so
a big-endian image that yields little-endian pairs is a broken scan rather than
an answer.

| material | paired sites | orientation | unpaired halves |
|---|---:|---|---:|
| `bin/boa` unit-2018, code region — **positive control** | **70** | BE 70, LE 0 | 4 |
| `bin/busybox` unit-2018, code region | 0 | — | 0 |
| `stage2.bin` code region | 0 | — | 0 |
| 3,374,772 bytes of `/dev/urandom` — **negative control** | **0** | — | 53,085 |
| **this unit's kernel**, `.text` | **101** | **BE 101, LE 0** | 27 |
| this unit's kernel, everything above `.text` | 0 | — | 511 |

The `boa` row reconciles exactly with the count this project already had:
70 × 2 + 4 = **144**. The urandom row is what makes the instrument mean anything:
53,085 halves and **zero** pairs, because four fields agreeing by chance in a
four-word window is about 6 × 10⁻⁸ per half.

### 2.2 What the 101 pairs are

Read, at `0x80002464`:

```
80002464  88a80000  lwl  t0,0(a1)
80002468  88a90004  lwl  t1,4(a1)
8000246c  24c6fff0  addiu a2,a2,-16
80002470  98a80003  lwr  t0,3(a1)
80002474  98a90007  lwr  t1,7(a1)
80002478  88aa0008  lwl  t2,8(a1)
...
8000248c  ac880000  sw   t0,0(a0)
80002490  ac890004  sw   t1,4(a0)
```

`a0` destination, `a1` source, `a2` count, unrolled by four: this is `memcpy`,
compiled from `arch/rlx/lib/memcpy.S`'s `#ifdef CONFIG_CPU_HAS_ULS` branch.

**Inferred, and it is the strongest desk argument available:** the core
implements these four instructions. If it did not, `memcpy` would raise Reserved
Instruction on its first unaligned copy, `do_ri` would reach
`die_if_kernel("Reserved instruction in kernel code")`, and the device would not
boot. It boots.

⚠️ **This is still inferred.** `CPU-15` is closed by one `lwl` under a bare-metal
RI handler on this die and by nothing else.

### 2.3 What actually changed in 2018–2019 — and the first answer here was a false zero

`notes/lwl-mystery.md`'s open question was *what was different about how `boa` was
built*. Three vendor toolchains ship inside `rtl819x-toolchain/toolchain/`, and
**all three run natively in this WSL distro** — no container.

🔴 **The first version of this section got it wrong, by exactly the failure this
project spends its rules on: a scan whose exit status was never checked.** It
reported that the emission "does not move with `-march`", sweeping `lx4180`,
`rlx4181`, `rlx5281` and `mips1`. Those are **binutils** spellings. The rsdk gcc
driver is a wrapper that answers

```
FATAL: -march mismatch. RSDK is configured for -march=4181 only
```

and exits 1 **without writing the output file**, so four of the five sweep points
never compiled and the `grep` counted the previous iteration's leftover `.s`. The
spelling the wrapper wants is the bare number, `-march=4181` / `-march=5281`.
Re-measured 2026-08-28 with `$?` checked at every point:

| toolchain | gcc | default | `-fuse-uls` | `-fno-use-uls` |
|---|---|---:|---:|---:|
| `rsdk-1.3.6-4181-EB` | 3.4.6-1.3.6 | **0** | **4** | 0 |
| `rsdk-1.3.6-5281-EB` | 3.4.6-1.3.6 | **0** | **4** | 0 |
| `rsdk-1.5.5-5281-EB` | 4.4.5-1.5.5p4 | **4** | **4** | 0 |

identical on the `rsdk-linux-gcc` wrapper and on the raw `mips-linux-gcc` driver,
and unchanged by `-march=4181` / `-march=5281`.

🔴 **So the lever is a flag, `-fuse-uls`, and both toolchain generations have
it.** What differs between 1.3.6 and 1.5.5 is only the **default**. And Realtek
turn it on deliberately rather than inheriting it: `rsdk-1.5.5-5281`'s own uClibc
configuration carries

```
UCLIBC_EXTRA_CFLAGS="-march=5281 -EB -fuse-uls -msoft-float -ffix-bdsl"
```

**What that costs, and it is the sentence that has to be retracted**: *"the
presence of compiler-generated `lwl` in a binary dates its toolchain"* is wrong.
It records a **build flag**. `R2a` still gets an instrument out of it, but a much
weaker one — a binary with those instructions was built by something that had
`-fuse-uls` in effect, which a drop can change without changing its compiler.

**What that buys**: the puzzle the first version left open — `boa` going 144 → 0
in 2019, which it had to describe as *"a later rsdk behaving like an earlier
one"* — **stops being a puzzle**. A drop that stops passing `-fuse-uls`, or a
toolchain that defaults it off, does it. That is now the first thing `R2a` should
look for, and it is cheap to look for.

**And it lines the measurement up with a source this repository already had.**
`SOURCES.json` records a **gcc-4.8.4 Lexra patch** (hackpascal's gist, cited,
never downloaded) that *"disables `lwl`/`lwr`/`swl`/`swr` generation for Lexra
targets via `!TARGET_LEXRA && !TARGET_RLX` on those patterns"*. Under `-fuse-uls`
that gate is overridden; under the 1.3.6 default it is what produces the zero.
Two independent descriptions of one mechanism.

⚠️ **Three limits.** The only 1.5.5 in the tree is the **5281** build at patch
level **p4**; this unit was built by a **p2**, and whether a 1.5.5-4181-p2
defaults the same way is not measured. `busybox` scoring 0 in all six trees is
not evidence against any of this — its source never asks for an unaligned 32-bit
access. And **none of this is evidence about the silicon in either direction**,
which is why §2.2's argument rests on this unit's kernel *executing* those
instructions and not on any compiler.

⚠️ One thing worth carrying to `CPU-14`: under `-fuse-uls`, rsdk 1.3.6 emits
`lwl $2,1($4)` / **`nop`** / `lwr $2,4($4)` / `nop` — the vendor compiler putting
a `nop` in the load delay slot, on the same core whose delay slot this project
measured to be architecturally exposed.

`TC-02` is not reopened here: six shipped images still cannot name a source release.

---

## 3. Grep ② — the cache-management model (`F49`)

The plan's second grep is `r3k_cache_init|r4k_cache_init|rlx` over `arch/mips/mm/`.
Read: **this port has neither**, and `arch/mips/mm/cache.c:161–173` does have the
`r3k`/`r4k` branch, which is the scanner's liveness control.

```c
/* arch/rlx/mm/cache.c:166 */
void __cpuinit cpu_cache_init(void)
{
    extern void __weak rlx_cache_init(void);
    rlx_cache_init();
}
```

Unconditional. There is no probe and no branch: a third implementation,
`arch/rlx/mm/cache-rlx.c`.

### 3.1 The mechanism, and why `CPU-44` saw what it saw

`cache-rlx.c` selects its primitives from the CPU model and the cache type. For
`CPU_RLX4181` + `CPU_HAS_WBC` and no `WBIC`, no `L2C`:

| | value for this part | consequence |
|---|---|---|
| `CONFIG_CPU_HAS_DCACHE_OP` | **defined** (4181/5181/4281/5281) | D side uses the `cache` instruction — ⚠️ **not "MIPS-II"**, see §6: the vendor assembler rejects it for `mips1` *and* `mips2`. `CACHE` is MIPS-III/32, carried here as an extension |
| `CONFIG_CPU_HAS_ICACHE_OP` | **not defined** (4281/5281 only) | I side uses **CCTL**, not `cache` |
| `CACHE_DCACHE_FLUSH` | `0x15` `DWBInval` | write-back cache, so flush must write back |
| `CACHE_DCACHE_WBACK` | `0x19` `DWB` | |
| `CCTL_ICACHE_FLUSH` | `0x2` `IInval` | |
| `CCTL_DCACHE_WBACK` / `FLUSH` | `0x100` / `0x200` | |
| unroll macro | `CACHE16_UNROLL8` (because `cpu_dcache_line != 32`) | eight `cache` ops at stride `0x10` |

🔴 **Every one of those is what `CPU-44` read out of this unit's binary on
2026-08-26 without knowing why**: 37 `cache` instructions, D side only, op field
only `0x11`/`0x15`/`0x19`, offsets `0x00`…`0x70` at stride `0x10`, and **zero**
I-side `0x10`. The binary reading and the source now agree op for op, and the
"eight covering 128 bytes, which is the 16-byte-line assumption" is no longer an
assumption — see §3.2.

`CCTL_OP` for everything that is not 4281/5281 — i.e. for this part — is a
read-modify-write with an explicit **0→1 edge**:

```
mfc0 $8,$20 ; ori $8,op ; xori $9,$8,op ; mtc0 $9,$20 ; mtc0 $8,$20
```

which is a second file agreeing with `CPU-24`'s edge-trigger finding.

### 3.2 Geometry — `CPU-25` has a source

`boards/rtl8196e/bsp/bspcpu.h`, byte-identical in all three drops:

```c
#define cpu_scache_size     0
#define cpu_dcache_size     ( 8 << 10)
#define cpu_icache_size     (16 << 10)
#ifdef CONFIG_RTL_8196E
#define cpu_dcache_line     16
#define cpu_icache_line     16
#else
#define cpu_dcache_line     32
#endif
#define cpu_dcache_line_mask	0xF
#define cpu_tlb_entry       32
#define cpu_imem_size       0
#define cpu_dmem_size       0
```

**Read: I-cache 16 KiB, D-cache 8 KiB, both 16-byte line, no L2, 32 TLB
entries.** The 16-byte line has a second source in this unit's own binary — the
8×stride-`0x10` unroll only compiles when `cpu_dcache_line != 32` — and the 32
TLB entries agree with `CPU-19`'s `Random` reading, which was measured on the
device. `CONFIG_RTL_8196E` is `def_bool y` in `boards/rtl8196e/config.in`, so the
16 branch is the live one.

⚠️ **The header contradicts itself** and it is worth writing down: `*_line_mask`
is hard-coded `0xF` in both branches, so a build taking the 32-byte branch gets a
mask for a 16-byte line. Not this build's problem; a real defect in the vendor
header.

🔴 **And `cpu_imem_size 0` is contradicted by this unit's own kernel** — §4.

---

## 4. What was not being looked for: I-MEM, D-MEM, and MIPS16

### 4.1 This unit's kernel sets up both scratchpads at boot

Read, `0x80002230`–`0x800022e8`, which is `arch/rlx/mm/imem-dmem.S`'s
`_imem_dmem_init`:

```
80002230  mtc0  zero,$20            ; CCTL clear
8000223c  li    t0,0x20
80002240  mtc0  t0,$20              ; 0x020 IMEM0OFF
8000224c  mtc0  zero,$20
80002258  li    t0,0x202
8000225c  mtc0  t0,$20              ; 0x200 DWB_Inval | 0x002 IInval
80002268  lui   t0,0x802c
8000226c  addiu t0,t0,0x8000        ; __iram  = 0x802B8000
80002270  lui   t1,0x0fff
80002274  ori   t1,t1,0xc000        ; & 0x0fffc000  -> 16 KiB alignment
8000227c  mtc3  t0,$0               ; IMEM window base
80002288  addiu t0,t0,0x3fff        ; + 16 KiB - 1
8000228c  mtc3  t0,$1               ; IMEM window top
80002298  mtc0  zero,$20
800022a4  li    t0,0x10
800022a8  mtc0  t0,$20              ; 0x010 IMEM0FILL
800022b4  lui   t0,0x802c           ; __dram_start = 0x802C0000
800022bc  lui   t1,0x802d
800022c0  addiu t1,t1,0xc000        ; __dram_end   = 0x802CC000
800022c4  beq   t0,t1,+11           ; skip if the section is empty
800022d0  ori   t1,t1,0xe000        ; & 0x0fffe000 -> 8 KiB alignment
800022d8  mtc3  t0,$4               ; DMEM window base
800022e4  addiu t0,t0,0x1fff        ; + 8 KiB - 1
800022e8  mtc3  t0,$5               ; DMEM window top
```

Read, and every part of it is about this machine:

- **`CP3 $0`/`$1` are the I-MEM window, `$4`/`$5` the D-MEM window.** `CPU-46`
  had that from the leaked datasheet; it is now also read out of this unit's own
  kernel, which is a second source of a different kind.
- **I-MEM 16 KiB, D-MEM 8 KiB**, from the masks and the sizes in this code, not
  from the datasheet.
- `0x010 IMEM0FILL` and `0x020 IMEM0OFF` (`CPU-24`) appear in the boot path, used
  exactly as `CPU-24` describes, with the clear-then-set edge.
- These are the **four `mtc3`** in this image. Anything claiming this kernel does
  not touch COP3 is refuted by its own boot path.
- `__iram = 0x802B8000` is where `.text` ends. Every region bound in this note
  comes from that word, not from a boundary chosen to produce a number.

🔴 **`bspcpu.h` says `cpu_imem_size 0` and this kernel fills a 16 KiB I-MEM.** The
constant does not gate this path. Recorded as a disagreement between the drop and
the binary; not resolved.

⚠️ **And the drops cannot have produced this line.** `imem-dmem.S:63–66` in all
three sets `IMEM0_SIZE` to `4096` unless `CONFIG_RTL_819XD`, i.e. `addiu $8,$8,0xFFF`.
This unit's binary has `0x3FFF`. Material for `R2a`; `TC-02` is not reopened.

### 4.2 🔴 This kernel contains MIPS16 code, and it is called with `jalx`

Opcode `0x1d` appears 217 times in windows that read as MIPS32 code. They behave
like jumps and the control says so:

| opcode | in-code hits | target in `.text` | target in `.iram` | elsewhere in image | outside |
|---|---:|---:|---:|---:|---:|
| `0x1d` | 217 | 1 | **94** | 85 | 37 |
| `jal` — **control** | 31,110 | 30,668 | 16 | 398 | 28 |
| `j` — **control** | 20,234 | 19,679 | 17 | 467 | 71 |

A 26-bit J-format field ranges over 256 MB; this image is 1.3 % of that, so
random data puts ~1.3 % of targets inside it. 82 % land inside. The targets
cluster: **23 distinct entries across `0x802B8118`–`0x802BC9F8`** and three more
just past it.

⚠️ **Two tools here report two different numbers for the same file — 180 and 179
— and the difference is one word, on purpose.** `opcount.py --mips16` counts 180
targets / 27 distinct; `hazlint`'s refusal counts 179 / 26. The word they differ
on is `0x80002310`:

```
8000230c  00000000
80002310  740008c7   reads as `jalx 0x8000231c`
80002314  00000000      ... which would be its delay slot
80002318  00000000      ... and this its return point
8000231c  00000000
80002320  2cca0004   the next real function starts here
```

`hazlint` rejects it, because a call whose delay slot *and* return point are both
`nop`, sitting in the zero padding after a function, is a data word in a gap.
`opcount` does not, because its job is to raise the question and `hazlint`'s is
to gate a build — a detector that must not block a build on a data word needs the
extra rule, and a detector whose only output is a report should not quietly drop
anything. **Neither number is the wrong one; a reader who finds only one of them
would be entitled to think it was.** The third cluster below `.iram`
(`0x8000231C`, one target, one distinct) is that same word, which is why it is
listed separately above rather than folded in.

Disassembled at one of them with **Realtek's own `rsdk-1.3.6-4181` objdump**,
`-m mips:16`:

```
802b8118:  5c30   sltiu a0,48
802b811a:  6a00   li    v0,0
802b811c:  6005   bteqz 0x802b8128
802b811e:  6a50   li    v0,80
802b8120:  ec58   mult  a0,v0
802b8122:  b303   lw    v1,0x802b812c
802b8124:  ec12   mflo  a0
802b8126:  e469   addu  v0,a0,v1
802b8128:  e820   jr    ra
802b812a:  6500   nop
802b812c:  <literal>
```

A complete function — bounds check, index times 80, add base, return — with four
internal consistencies that random bytes cannot produce: the `bteqz` target is
exactly the `jr ra`; the PC-relative load points exactly at the word after the
delay slot; that word holds `0x802FB544`, a kernel address; and the literal pool
of the next function holds `0x804CA900`, `0x804CA8F4` (both past the image end,
i.e. `.bss`) and **`0xB8010028`, a KSEG1 register address**.

**Negative control**, the same disassembler on 48 random bytes: `dsll`, `daddiu`,
`ld` — MIPS64 forms — a `jal` to `0x8acc8b44` outside the image, and branch
targets outside the region. MIPS16 is a dense encoding and almost any bytes
*disassemble*; only these bytes *cohere*.

**Corroboration from the source side**: `arch/rlx/include/asm/cpu-features.h:22`
is `#define cpu_has_mips16 1`, and `arch/rlx/kernel/proc.c:35` prints
`mips16 implemented\t: yes` — a string that is present in this unit's binary.
⚠️ It is hard-coded, not probed, so it is the vendor asserting it, not measuring
it.

⚠️ **None of the five shipped `RTL8196E_*` configs enables any MIPS16 option**
(`CONFIG_RTL865X_KERNEL_MIPS16 is not set` in all five). A second thing the drops
in hand cannot reproduce about this binary. `R2a`.

🔄 **2026-08-28 — that last sentence is refuted, and the refutation came from
doing the build.** `rtl819x-toolchain`'s `linux-2.6.30` was built out of tree
with `boards/rtl8196e/config.linux-2.6.30.RTL8196E_88E_GW` — one of those very
five configs, `CONFIG_RTL865X_KERNEL_MIPS16 is not set` — and the resulting
`vmlinux` **contains MIPS16**: `readelf -s` marks **39 symbols `[MIPS16]`**, and
the vendor's own `objdump` reads `7409506d` at `0x80006bf4` as
`jalx 802541b4 <irq_to_desc>`. The symbols are the wlan and NIC fast path
(`rtl8192cd_interrupt`, `swNic_receive`, `rtl_netif_rx`, `validate_mpdu`, …).
Both toolchains produce it: 25 distinct `jalx` targets from the 1.3.6 build, 24
from the 1.5.5 build. **So the presence of MIPS16 is not a thing the drops fail
to reproduce, and it is not a discriminator.** `IMEM0_SIZE` (§4.1) still is, and
`notes/vendor-toolchains.md` §7 adds a third that is stronger than either.

~~⚠️ **Where the MIPS16 comes from is undetermined.**~~ ✅ **Settled
2026-08-28 (`TC-c`), and the measurement this paragraph proposed would have
returned a false zero.** It said: *"Every `-mips16` in the kernel tree's
Makefiles is either commented out or inside
`ifdef CONFIG_RTL865X_KERNEL_MIPS16_LAYERDRIVER`, which that config does not set;
there is no tracked `.o` anywhere in the tree, so it is not a prebuilt blob. The
measurement that would settle it is a build with `V=1` and a grep of the actual
`-mips16` command lines."*

🔴 **`-mips16` is never on a command line. It is a function attribute in C.**
讀, `drivers/net/wireless/rtl8192e/8192cd_cfg.h:1007-1020`:

```c
#undef __MIPS16
#ifdef __ECOS
  #ifdef RTLPKG_DEVS_ETH_RLTK_819X_USE_MIPS16
  #define __MIPS16   __attribute__ ((mips16))
  #else
  #define __MIPS16
  #endif
#else                                     /* the Linux build takes this branch */
  #if defined(CONFIG_WIRELESS_LAN_MODULE)
  #define __MIPS16                        /* empty, when the driver is a module */
  #else
  #define __MIPS16   __attribute__ ((mips16))   /* <- built-in: the DEFAULT */
  #endif
#endif
```

**On Linux, with the wireless driver built in rather than as a module, `__MIPS16`
expands to `__attribute__((mips16))` unconditionally — no Kconfig symbol gates
it.** `8192cd_osdep.c` applies it at seven sites. That is why a build whose
`.config` says `CONFIG_RTL865X_KERNEL_MIPS16 is not set` still produces MIPS16,
and it is why `make V=1 | grep -- -mips16` would have found nothing and been
read as "not there".

**Corroboration from the symbols rather than from the source.** 讀 the 39
`[MIPS16]` symbols in the `vmlinux` built here: `get_skb_priority`,
`insert_emcontent`, `aes_fill_encheader`, `get_tx_early_info`,
`reorder_ctrl_{pktout,consumeQ,timeout,check}`, `rtl8192cd_rx_data`,
`release_pkthdr`, `re865x_start_xmit`, `rtk_queue_tail`, `rtk_dequeue`,
`interrupt_dsr_rx`, `dev_alloc_skb_priv` — **all of them 8192cd/NIC**, which is
exactly the set `__MIPS16` is applied to and not the set the
`CFLAGS_<obj>.o = -mips16` lines name.

**Control for the zero, because "no `-mips16` on any command line" is a claim.**
The same `grep -rlI -- "-mips16"` over the same tree **does** find 24 such lines,
in seven `drivers/net/rtl819x/*/Makefile` files — 19 active, 5 commented — all
inside `ifdef CONFIG_RTL865X_KERNEL_MIPS16_LAYERDRIVER`, a symbol no shipped
`RTL8196E_*` config defines; and it finds two more in each drop's
`users/Makefile`, under the `rsdk-1.5.0-4181` branches
(`notes/vendor-toolchains.md` §7). The scanner fires; the flag is simply not the
mechanism.

🔴 **And the check that first said "no MIPS16 here" was a false zero of the same
family this file keeps cataloguing.** It read `readelf -h`'s `Flags:` for the
string `mips16` and found none — correctly, because `e_flags` does not carry it.
MIPS16 is marked **per symbol**, in `st_other`, which `readelf -h` never shows.
The `vmlinux` header reads `Flags: 0x1001, noreorder, o32, mips1` and the file is
full of MIPS16 all the same.

✅ **One thing this settles in the other direction.** `opcount --mips16` and
`hazlint`'s MIPS16 refusal have until now had no ground truth to be checked
against — this unit's kernel is stripped, so the symbol table that would confirm
them does not exist. The `vmlinux` built here **has** one, and on it the counter
says *MIPS16 reached, 25 distinct targets* while the symbol table says *39
symbols marked MIPS16*. That is the first positive control either instrument has
had on a real kernel-sized artefact.

### 4.3 What that costs, and it lands on this repo's own tools

`opcount.py`'s docstring claimed a linear 4-byte scan is a **superset** of the
instructions — *"it can count data as code, but it cannot miss an instruction"* —
and `notes/lwl-mystery.md` quotes it. **In a MIPS16 region it is false**: MIPS16
instructions are two bytes, so half of them are invisible to a 4-byte-aligned
scan and the other half are read glued to a neighbour. `F51`'s zeros stand on
that sentence.

**So the six userland binaries and `stage2.bin` were re-checked, by two
independent tests**, and both say the exposure is confined to the kernel:

| | ELF `e_flags` bit `0x04000000` (`EF_MIPS_ARCH_ASE_M16`) | `jalx` targets landing inside the file |
|---|---|---|
| six `boa`, six `busybox` | clear on all twelve (`0x1007` / `0x1005`) | **0** on all twelve |
| `stage2.bin` | **not applicable — raw image, no ELF header** | **0**, control fired |
| this unit's kernel | **not applicable — raw image, no ELF header** | **180** |

⚠️ **So it is two independent tests for the twelve ELF binaries and ONE test for
`stage2.bin`**, and any sentence that says otherwise is wrong. What `stage2.bin`
has instead of a second test is a fired control: 99.4 % of its 499 in-code `jal`
land in range, so its `jalx` zero is a measured zero rather than a wrong base.

The four PIC-generation `boa` each carry exactly one `jalx`-shaped word whose
target is outside the file — data, and the test says so rather than counting it.

**`F51`'s userland numbers are unaffected. The claim in the tool is corrected.**

---

## 5. The core's name — `PRId` and what it maps to

`CLAUDE.md` refused `RLX4181` and `RLX5281` on the grounds that no source maps
`PRId = 0x0000CD01` onto a Lexra model number, and named the thing that would
lift it: **a `PRId` assignment table**. One is in the drops.

`arch/rlx/include/asm/cpu.h`, headed *"Values of the PRId register used to match
up various MIPS cpu types"*, with the field layout drawn out — bits 15:8 are the
Processor ID:

```c
#define PRID_IMP_RLX4180   0xc100
#define PRID_IMP_RLX4181   0xcd00
#define PRID_IMP_RLX5181   0xcf00
#define PRID_IMP_RLX5280   0xc600
#define PRID_IMP_RLX5281   0xdc01
#define PRID_IMP_RLX4281   0xdc02
```

Measured on this die (`CPU-19`, 2026-08-25): `PRId = 0x0000CD01`. Bits 15:8 are
`0xCD` → **`RLX4181`**, revision `0x01`. `RLX5281` is `0xDC` and is positively
excluded, not merely unproven.

Three corroborations, plus one consistency check that is **not** a
corroboration — and 🔄 **the first version of this list said "four, of which two
are independent of the drops", which is false**:

1. `boards/rtl8196e/config.in` — `ARCH_CPU_RLX4181=y` for this exact part. In
   the drop.
2. ⚠️ **A consistency check, not independent evidence.** This unit's kernel has
   **zero `ll`/`sc`/`sync` in 2.85 MB of text**, which matches
   `ARCH_CPU_LLSC=n`/`SYNC=n` for 4181 against `=y`/`=y` for 5281. But the
   binary lacks them *because* `boards/rtl8196e/config.in` says so — this is
   corroboration ① observed downstream, one fact counted twice. It is also
   contradicted in direction by §6, where the vendor assembler accepts `ll`/`sc`
   for `-march=rlx4181`, and by `arch/rlx/include/asm/atomic.h`, which emits
   `ll` under `#if defined(CONFIG_CPU_RLX4181)`. **推**, and about the build
   rather than the silicon.
3. Third-party Linux ports print `CPU0 revision is: 0000cd01 (Lexra LX4380 /
   RLX4181)` on RTL8196E hardware. ⚠️ Those ports are forks of this same
   Realtek SDK and carry this same table, so this is 單一來源 seen twice.
4. The LKML Lexra series defines `PRID_IMP_LX5280 = 0xC600`, which is the same
   value the table above gives `RLX5280`. **This is the only one that is not
   Realtek-downstream, and it checks the `0xC6` entry, not `0xCD`.**

⚠️ **Three weaknesses, written here rather than left for a reader to find:**

- The three drops are **byte-identical** in this header:
  `md5 c99116184b0e81fb987b7a7f4b4bdbba`, 4,422 bytes, all three. That is one
  source in three copies. 🔄 **The digest published here until 2026-08-28 was
  `ceb6bf89…`, which is not any digest of the file** — it is the md5 of the
  21-line slice that was diffed across the drops. The claim it supported was
  right; the number offered as its audit trail was not a digest of the thing it
  named.
- **No code in the port consults the table.** `cpu_probe()` sets
  `processor_id = PRID_IMP_UNKNOWN` and overwrites it with `read_c0_prid()` one
  line later; `cpu_report()` prints the raw value. A table nothing reads can go
  stale silently.
- The table's own encoding is **not uniform**: `RLX5281 = 0xdc01` and
  `RLX4281 = 0xdc02` have non-zero low bytes, so under the bits-15:8 reading both
  are IMP `0xdc` and the low byte is a revision. The rule that reads `0xCD01` as
  `RLX4181` rev 1 is the rule the first four entries follow; the last two break
  it.
- **Provenance.** Three of the four items above are Realtek or downstream of
  Realtek, and the fourth checks a different entry. There is no reading of this
  evidence in which `0xCD` → `RLX4181` has a non-Realtek source.

---

## 6. The per-core ISA table, from the vendor's own opcode table

`tools/isa-probe.sh`. Realtek's binutils knows six Lexra architectures — the same
six as `arch/rlx/Kconfig` — so assembling one instruction at a time against each
`-march` is a direct read of the machine description written by the people who
integrated the core. Both controls hold: `addu` accepted in every column,
`daddu` rejected in every column.

| | lx4180 | **rlx4181** | rlx5181 | lx5280 | rlx5281 | rlx4281 | mips1 | mips2 |
|---|---|---|---|---|---|---|---|---|
| `lwl` `lwr` `swl` `swr` | y | **y** | y | y | y | y | y | y |
| `ll` `sc` | . | **y** | y | . | y | y | . | y |
| `sync` | . | **.** | . | . | y | y | . | y |
| `cache` | . | **y** | y | . | y | y | . | . |
| `movz` `movn` | . | **y** | y | y | y | y | . | . |
| `beql` | . | **.** | . | . | . | . | . | y |
| `madd` `rdhwr` `pref` | . | **.** | . | . | . | . | . | . |
| `mfc3` `mtc3` `lwc3` | y | **y** | y | y | y | y | y | y |
| `mfc1` `lwc1` | y | **y** | y | y | y | y | y | y |

What it settles, and what it does not:

- 🔴 **`movz`/`movn` are accepted for `rlx4181` and rejected for `mips1` and
  `lx4180`.** `CPU-12` asks whether this core implements them, because the
  loader has 18 of them and `check_image()` runs on every boot. ⚠️ **This is not
  a new argument, and saying so would be wrong**: `SOURCES.json` already records
  that the gcc-4.8.4 Lexra patch *"gates conditional move on `INSN_RLXB`, which
  is what lets `CPU-17`'s 18 `movz`/`movn` rule out baseline LX4180"*. What is
  new is that the same conclusion is now **measured on a toolchain in hand**
  rather than read off the description of a gist nobody has downloaded — and the
  two agree, which is the second source the project's rule asks for.
- 🔴 **`cache` likewise** — accepted for `rlx4181`, rejected for `mips1`,
  `mips2` and `lx4180`. `CPU-44`'s desk half now has two sources.
- **`sync`**: rejected for 4181, accepted for 5281 — **exactly** the
  `ARCH_CPU_SYNC` split in the board configs. Two vendor sources agreeing on a
  discriminating fact.
- 🔴 **`ll`/`sc`: the two vendor sources disagree.** The assembler accepts them
  for `rlx4181`; `boards/rtl8196e/config.in` says `ARCH_CPU_LLSC=n` and this
  unit's kernel has none. Not resolved. The reading that fits both is that these
  cores are synthesisable and LL/SC is an option of the *instance*, while
  `-march` describes the *family*; that is inferred, and it is written here as a
  disagreement rather than as a conclusion.
- ⚠️ **The ULS row proves nothing.** Every column accepts `lwl`, including
  `lx4180` and `mips1` — the table inherits MIPS-I's unaligned instructions
  everywhere and only ever *subtracts* per core. So the assembler is not evidence
  about ULS in either direction, and §2's argument does not use it.
- **`rlx4181` is a strict superset of `mips1` here.** `-march=mips1` therefore
  stays a safe conservative choice for `TC-05`, with the consequence written
  down: it forbids `cache` and `movz`, which this core has, so bare-metal probes
  needing either must say so explicitly rather than by accident.

---

## 7. Two corrections to committed files, both found by re-measuring

### 7.1 `hazlint` 1.2's own note records a number the tool does not produce

The 1.2 docstring says that on the decompressed kernel, violations go
**172 → 171**. Measured today on the same sha256, running both versions of the
tool from git:

| | violations |
|---|---:|
| `93af331^` (pre-1.2) | **172** |
| `93af331` (1.2, shipped) | **168** |

**Four sites leave, not one**, and the diff names them:

| site | word after the load | which half of 1.2 removed it |
|---|---|---|
| `0x802BAB68` | `eb8c2309` — opcode `0x3A` `swc2` | the `lwcz`/`swcz` fix |
| `0x802BB094` | `e9a467b1` — opcode `0x3A` `swc2` | the `lwcz`/`swcz` fix |
| `0x802BB11C` | `e9a467b1` — opcode `0x3A` `swc2` | the `lwcz`/`swcz` fix |
| `0x802BC490` | `4df46783` — opcode `0x13` COP3 | the COP3 fix, the one the note describes |

So the note's *"what it cost the gate is one violation"* is correct **for the
COP3 half alone**. What is wrong is the total, and one sentence more: the note
calls the `lwcz`/`swcz` half *"latent only because nothing in this tree emits
one"*. **Three words in this tree's own kernel are exactly that shape and they
moved the gate's answer.** The fix was more load-bearing than its own note
claims.

All four sit above `0x802B8000`, i.e. in `.iram` and past it — the region §4
shows is a mixture of MIPS16 code, literal pools and data. That is why they were
false positives, and it is the same reason `hazlint` must now refuse that region
outright.

### 7.2 `hazlint` was reading MIPS16 as MIPS32

Every number `hazlint` has ever printed for this kernel was produced by a 4-byte
scan over a file that contains two-byte instructions. `K10`, new today, refuses a
span that contains MIPS16 — detected as a `jalx` whose target lands inside the
scanned span — and `stage2.bin` is its negative control at population scale.

Bounded to the MIPS32 span that `_imem_dmem_init` itself defines,
`0x80000000`–`0x802B8000`:

```
loads                                128,440
followed by an explicit nop           40,182   (31.28 %)
successor unresolved                       3
violations                                58
```

and **all 58 are one artefact**: a table of kernel pointers at
`0x802B4754`–`0x802B48E0` and `0x802B5410`–`0x802B5448`, whose words all begin
`0x80…`, so each decodes as `lb` and each appears to read the register the
previous one wrote. Below that table — `0x80000000`–`0x802B4000`, **127,650
loads** — there are **zero** violations.

⚠️ **`K4b` pins the `0x802B8000` span, not the zero.** `0x802B4000` was chosen
*after* seeing where the violations were, and this project's own rule is that a
region bound must come from an independent signal rather than from the number it
produces. `0x802B8000` is read out of the binary at `0x8000226C`. The zero is the
adjudication and is recorded as such; the control is the number the honest bound
gives.

**`K4b` is a population control 87× the size of `K4`** — 128,440 loads against
`stage2.bin`'s 1,474 — on the one artefact in this project that is both real code
and this machine's own.

---

## What could still be wrong

1. **`.text` is not uniformly code.** One 1 KiB block at `0x80188800` is a dense
   blob that is neither MIPS32 nor coherent MIPS16 — it holds every FPU-opcode
   and `SPECIAL2` hit in the span. It is excluded by adjudication, not by a
   bound, and a second such island would not be noticed by anything here.
2. **The `.iram` region is not fully mapped.** 23 MIPS16 entry points are known
   from the call side; where each function ends, and whether the region also
   holds MIPS32, is not established.
3. **The ULS conclusion is an inference from "the device boots".** It is a good
   inference and it is not a measurement. `R1a`.
4. **The `PRId` table is one source in three copies and no code reads it.** §5.
5. **The toolchain comparison used a 5281/p4 build** where this unit was built by
   a 4181/p2. §2.3. 🔄 **2026-08-28: the mechanism behind that comparison is now
   named and it is not the version.** `-fuse-uls` is injected by the rsdk-1.5.5
   *wrapper* and by neither 1.3.6 wrapper, and it appears in no drop's build
   system at all — `notes/vendor-toolchains.md` §6. So the `lwl` signal separates
   rsdk **generations**, not releases, and the p2/p4 gap is not what that table
   was measuring.
6. 🔴 **`jalx` is not the only way into MIPS16, and both new instruments assume
   it is.** Bit 0 of a target address is the ISA-mode bit, so `jr`/`jalr` through
   a register holding an odd address enters MIPS16 — which is how a MIPS16
   routine reached through a function pointer or an ops struct is called, and a
   Realtek `.iram` fast path is built out of exactly those. A region entered only
   that way is invisible to `opcount --mips16` and `hazlint` will report on it as
   32-bit. Searched in this image and not found — 29 words hold an odd in-image
   address and all of them are in data — so §4.2's reading stands; **not-found is
   not absent**, and a stronger test would follow the odd constants.
7. **The codeness cut (80) and window (64 words) are chosen, not derived.**
   `hazlint`'s K10 now pins the cut into `[66, 87]` with two dilution fixtures,
   and the score is bimodal on this artefact with an empty band there — but a
   pinned constant is not a derived one, and the 180-vs-238 difference turns on
   it. This project's own rule about region bounds, applied to a filter.
8. **Everything in §1 and §3 is about the source Realtek released.** 🔄
   **2026-08-28: this item named two places showing the drops did not build this
   image, and one of them is gone.** MIPS16 is **not** one — building one of
   those five configs produces MIPS16 (§4.2). `IMEM0_SIZE` stands, and
   `notes/vendor-toolchains.md` §7 adds a stronger one: each drop's own
   top-level `.config` names the rsdk it is configured for, and all three name a
   **1.3.6** release while this unit's banner is `4.4.5-1.5.5p2`. Any source-side
   claim can be wrong about *this* binary in the same way, and only the
   binary-side column rules that out.
