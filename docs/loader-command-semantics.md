# Loader command semantics — the six questions R0, R4 and R8 need

**DAY-ZERO item 4. Desk work, 2026-08-23. Nothing here was measured on the
device.** Every claim is marked *read out of the code* or *inferred, pending a
measurement*; where a claim rests only on a vendor tree that is not this unit,
it says so.

Five sources, and they are not equally trustworthy:

| | what it is | weight |
|---|---|---|
| **A** | `stage2.bin` — the LZMA second stage out of **this unit's own** flash dump, disassembled | this unit; definitive for what its loader does |
| **B** | vendor bootcode C — `src-vendor/saturn49-wecb` and `src-vendor/wecb-vz-gpl`, `rtl819x/bootcode/boot/` | **a different bootcode generation.** It explains *why* a constant is what it is. Never a substitute for A |
| **C** | `upstream/` pinned at `4d3ff26` — `notes/loader-tftp-and-commands.md`, `tools/loader-unpack.py` | the same artefact read by tools this repo does not own. **Referenced, not transcribed** — §0 |
| **D** | `refs/RTL8196E-VEx-CG_Datasheet_1.1.pdf` | the datasheet for **this** part, not for the 8196C/8198 that B targets |
| **E** | vendor Linux headers — `src-vendor/rtl819x-toolchain/linux-2.6.30/…/platform.h`, `…/rtl865xc_asicregs.h` | register names and bit fields |

---

## 0. Why this file does not contain upstream's command table

Three of the six questions were answered in **C** before this repo existed. C's
own write-up records that its first version was wrong three ways, and that the
common cause was one thing: *the command table had been transcribed by hand, and
a hand transcription is a claim with no instrument behind it.*

Copying that table into a second repository would reproduce exactly that
failure, and would give one piece of state two owners. So: **C owns the command
table. This file owns the semantics rlxfw needs, and re-runs the instrument
rather than quoting the answer.** Where a statement below repeats something C
already established, the instrument was re-run here and agreed — a second
reading, not a copy.

### Re-deriving everything below

```sh
D=$FWRE_WORK/dumps/flash-n150rt-console-1.bin
W=$FWRE_WORK/rebuild/work-item4

python3 upstream/tools/loader-unpack.py "$D" --extract $W/stage2.bin
sha256sum $W/stage2.bin
#   f88869d108cdafdfcff5d9461b0ead5c061a6725effb0314bb954572c9c1b4ee

mips-linux-gnu-objdump -D -b binary -m mips:3000 -EB \
    --adjust-vma=0x80400000 $W/stage2.bin > $W/stage2-vma.dis

python3 upstream/tools/loader-unpack.py "$D" --commands     # branch-walking reader
python3 upstream/tools/loader-unpack.py "$D" -o $W/loader.json
```

Four controls ran with it, and all four are load-bearing:

| control | what it rules out | result |
|---|---|---|
| the extracted `stage2.bin` must hash to the value above | reading a different artefact from the one C read | matches |
| `docs/loader-flash-write.md`'s quoted `ComSrlCmd_RDID()` sequence must reappear instruction for instruction in the fresh disassembly | a wrong `--adjust-vma`, wrong endianness, wrong architecture flag | reappears at `0x8040591c`–`0x80405970` |
| `loader-unpack.py` refuses to emit a report unless it finds all seventeen commands the console prints | an *absence* result (question d) that is really a broken scan | `documented_commands_missing: []`, `self_check: OK` |
| `-m mips:3000` prints `.word` for anything outside MIPS-I | silently accepting a MIPS32 decode of a MIPS-I core's code | two `.word`s appeared, and they turned out to matter — §9 |

**The disassembly is not committed.** It is 12,288 lines derived in one command
from an artefact that cannot be committed either.

---

## The six questions, and where each one stands

| # | question | owning gate | answer | source |
|---|---|---|---|---|
| **a** | Does the loader scan for the image tag, or is the offset hard-coded? | R8 | **It scans.** Six 64 KiB-aligned candidates, `0x010000`–`0x060000` | A, corroborated by B |
| **b** | What form does `LOADADDR` take, and does it bound-check? | R0 | one hex argument, no bound check, no confirmation | A |
| **c** | Is TFTP server or client, and what does `AUTOBURN` gate? | R0 | server; `AUTOBURN` is read at exactly one instruction | C, re-run here |
| **d** | Is there anywhere to put a kernel command line? | R4 | **No — and the question rlxfw actually has is a different one** | A + C |
| **e** | Where does `burn()` write? | R5b, R8 | `docs/loader-flash-write.md` | — |
| **f** | Which of the seventeen commands writes arbitrary memory? | R4 | **Four paths, not one.** §f | A, corroborated by B |

---

## a. The loader scans. It does not use a hard-coded offset.

**Refutation condition, written before the search:** *if the offset is
hard-coded, then on the path from reset to the header parse there is exactly one
immediate producing `0x060000` (or `0xBD060000`), and no loop around it. Finding
a candidate array or a scan loop refutes "hard-coded".*

**Positive control for the search:** the same sweep must find a loop that is
known to exist — the loader's 32-entry SPI chip-descriptor walk, which
`loader-unpack.py --chip-table` independently reports at a `0x20` stride. It
does.

### What is there

`0x80408084` is the image locator. **(A)** It takes a header buffer, a settings
buffer and a bank offset, and does three fixed probes followed by a sweep:

```
804080b8   lui   a0,0x501            ; flash 0x010000  (biased by 0x05000000)
804080c0   sw    a0,-8900(s0)        ; 0x8040DD3C = the candidate being tried
804080c8   jal   0x80407d50          ; check_image()
804080d0   bnez  v0,...              ; hit -> stop
           …0x502 (0x020000)…  …0x503 (0x030000)…

80408118   lui   s0,0x3              ; scan from 0x030000
80408124   lui   s1,0x1              ; stride 0x010000
80408130   beq   s0,s1,skip          ; 0x010000 already tried
8040813c   beq   s0,0x2<<16,skip     ; 0x020000 already tried
80408144   bne   s0,0x3<<16,check    ; 0x030000 already tried
8040816c   lui   v0,0x6
80408170   slt   v0,v0,s0            ; scan while s0 <= 0x060000
80408188   bne   v1,2,fail           ; only signature "cr6c" counts
```

**Read out of the code:** the kernel candidate set is exactly

```
0x010000   0x020000   0x030000   0x040000   0x050000   0x060000
```

and **this unit's kernel sits at `0x060000`, the last one tried.** The rootfs
locator immediately below does the same over `0x0E0000 · 0x0F0000 · 0x130000`
then `0x100000 · 0x110000 · 0x120000`.

`0x8040DD3C` is written on **every** candidate, so after the scan it holds the
address that was accepted. **(A)** That makes this whole section falsifiable
from the `<RealTek>` prompt with one read and no risk — §8.

### The second source, and what it settles

`bootcode/boot/init/utility.c`, `check_image_header()`. **(B)**

```c
ret = check_system_image(FLASH_BASE + CODE_IMAGE_OFFSET  + bank_offset, …);
if (ret==0) ret = check_system_image(FLASH_BASE + CODE_IMAGE_OFFSET2 + bank_offset, …);
if (ret==0) ret = check_system_image(FLASH_BASE + CODE_IMAGE_OFFSET3 + bank_offset, …);
#ifdef CONFIG_RTL_FLASH_MAPPING_ENABLE
    i = CONFIG_LINUX_IMAGE_OFFSET_START;
    while (i <= CONFIG_LINUX_IMAGE_OFFSET_END && (0==ret)) {
        return_addr = FLASH_BASE + i + bank_offset;
        if (CODE_IMAGE_OFFSET==i || CODE_IMAGE_OFFSET2==i || CODE_IMAGE_OFFSET3==i)
            { i += CONFIG_LINUX_IMAGE_OFFSET_STEP; continue; }
        ret = check_system_image(FLASH_BASE + i + bank_offset, …);
        i += CONFIG_LINUX_IMAGE_OFFSET_STEP;
    }
#endif
```

Every element maps onto A: the three fixed probes, the *skip-the-three*
comparisons, the `return_addr` global, the `START`/`END`/`STEP` triple, and the
`ret==2` gate before the rootfs search. `utility.h` puts `CODE_IMAGE_OFFSET/2/3`
at `0x10000/0x20000/0x30000`, matching A's immediates. **So
`CONFIG_RTL_FLASH_MAPPING_ENABLE` was defined in the build that produced this
unit's loader** — inferred, but from a structural match rather than a guess.

### What it means for R8

R8's A/B layout does not need the loader to be taught anything. **Any 64 KiB
boundary in `0x010000`–`0x060000` is a slot the stock loader will find**, and it
prefers the lowest. Two images at, say, `0x020000` and `0x060000` give an A/B
pair in which A wins whenever its checksum is good — the behaviour an A/B scheme
wants, obtained for free.

`PROGRESS.md` **C-1 closes here.**

### The signature test, and the two return values

`check_image()` at `0x80407D50` **(A)**:

1. copies the 16-byte header out of the memory-mapped flash window
   (`0xB8000000 + biased_offset`) with eight `lhu`/`sh` pairs — not `lw`, and
   not `lwl`/`lwr`;
2. `memcmp`s the signature against `"cs6c"` then `"cr6c"`, both built as
   immediates (`lui 0x6373|ori 0x3663`, `lui 0x6372|ori 0x3663`) rather than
   stored as strings, and returns **1** for the first, **2** for the second;
3. calls `flash_read(header.startAddr, offset+16, header.len)` — **it copies the
   payload into RAM** — and stores `startAddr` at `0x8040DD48`;
4. sums the RAM copy as 16-bit halfwords and **requires the sum to be zero**.

B names the two signatures: `FW_SIGNATURE = "cs6c"`,
`FW_SIGNATURE_WITH_ROOT = "cr6c"` (`bootcode/boot/init/rtk.h`). Only `2`
satisfies the caller, so a firmware without a rootfs section is located and then
rejected.

Step 3 is where **C's `T-09` comes from.** C observed RAM at `0x80500000`
holding a copy of flash `0x060010` that nothing in that session had put there,
and inferred that the loader stages the payload before offering the ESC window.
**That inference now has an instruction behind it:** `jal 0x80404f38` at
`0x80407E44`, executed during the *check*, because this generation computes the
checksum over the RAM copy where B computes it over flash.

### And the image check is located, which closes C-4

`doBooting()` at `0x80408690` **(A)**, and it matches B's `doBooting()` in
`init/utility.c` branch for branch:

```
804086a4   beqz  a0,0x804086f8      ; flag == 0 (image bad) -> the else arm
804086b0   jal   0x80408320         ; user_interrupt(0x3B023380)
804086bc   beq   v0,1,0x804086d0    ; ESC -> skip the boot
804086c8   jal   0x804084b8         ; goToLocalStartMode(addr, pheader)
804086d4   jal   printf             ; "\n---Escape booting by user\n"
804086e4   sw    zero,0(0xB8003000) ; GIMR0 = 0
804086e8   jal   0x80408468         ; goToDownMode()  -> the <RealTek> prompt
                    ---- else arm ----
80408700   sw    zero,0(0xB8003000) ; GIMR0 = 0
80408704   jal   0x80408468         ; goToDownMode()  -- no ESC wait, no message
```

**A bad image does not cost the rescue path — it goes straight there, with no
ESC window and silently.** `docs/loader-flash-write.md` §3 marked this
*inferred for this unit, confirmed only in a different bootcode generation*. It
is now read out of this unit's own code. **C-4 no longer needs a bench test to
establish the structure** — what a bench test would still add is that a
deliberately corrupted image reaches the prompt in practice, which is a
different claim and stays worth doing before R8.

Why the diagnostic strings were missing, which is what made this look
un-locatable: this build compiles out the *system* image messages and keeps the
*rootfs* one.

| string | in this unit's `stage2.bin`? |
|---|---|
| `no sys signature at %X!` | **absent** |
| `sys checksum error at %X!` | **absent** |
| `no rootfs signature at %X!` | **absent** |
| `rootfs checksum error at %X!` | **present**, `0x8040AF50` |
| `imgage checksum error at %X!` (`burn()`'s, vendor's spelling) | **present**, `0x8040A7C7` |

**The check is silent, not missing.** An absent string was read as an absent
check; it was neither.

One measured side-effect while reading it: B polls for ESC inside the checksum
loop every `ACCCNT_TOCHKKEY` blocks. In A that threshold is `0x80000`
(`lui s5,0x8` at `0x80407E5C`) while the counter advances once per 64 KiB, so a
987 KiB image advances it about fifteen times per candidate. **ESC cannot
interrupt the checksum on this unit** — inferred from the arithmetic, and it
predicts that the ESC window is the one in `doBooting` and nowhere earlier.

---

## b. `LOADADDR` — one hex argument, no bound check, no prompt

**(A, instrument re-run here.)** Table row 8, declared argc 1, handler
`0x8040996C`, writes the global `0x8040D3A8`, whose `.data` initialiser is
`0x80500000`. `loader-unpack.py --commands` classifies the handler as
**`dereferences argv unchecked`** — it loads `argv[0]` with no test of the count
it was handed, so `LOADADDR` with no argument reaches `strtoul(NULL, …)`.

Three things R0 needs that the help string does not say:

- **No bound check.** Nothing compares the parsed value against RAM size or
  against the loader's own image. `LOADADDR 80400000` would point the next TFTP
  upload at the running loader.
- **No confirmation.** Unlike `FLR` and `FLW`, `LOADADDR` does not prompt.
- **The upload path can overrule it.** A TFTP write whose filename is `nfjrom`
  or `boot.img` forces the load address to `0x80000000` and arms an
  auto-execute. **(C)** R0 must never use those two names; `loader-tftp.py`
  already refuses them.

---

## c. TFTP is a server; `AUTOBURN` is read at exactly one instruction

**(C, re-run here.)** `loader-unpack.py`'s `P9-3` block reproduces the rescue
path's string cluster from this repo's own run, and the JSON records
`interrupt_wiring.boot_path_to_the_prompt`: ethernet init, `IE` set at
`0x80408494`, command loop entered at `0x80409144`. The loader answers the
network only after `IPCONFIG`, and the read path serves `[0x8040D3A8]` for
`[0x8040DD28]` bytes.

For R0 the operative half is C's instruction-level result that **`AUTOBURN` is
read once in the whole image**, at `0x80401B9C`, on the upload-completion path,
with `0x80409944` the only writer. `AUTOBURN 0` therefore makes "upload into RAM
and jump" a zero-flash-write sequence backed by one instruction rather than by
usage text.

**One thing this file adds** (A, §f): `FLR` also writes `0x8040DD28`. A `FLR`
issued for any reason changes what a subsequent TFTP *read* would serve. R0's
script has to know that, and it is why a `get` between two `FLR`s does not test
what it appears to test.

---

## d. There is nowhere to put a kernel command line — and that is not the question rlxfw has

### The literal question, answered, and the plan's row for it was stale

`plan/DAY-ZERO.md` lists this as *"upstream `P9-1`, still open"*. It is not
open. **C closed it, refuted, with three independent static sources**, and the
dynamic half agreed at the bench on 2026-08-17.

Re-run in this repo rather than quoted:

```
loader.json:  questions.P9-1_kernel_cmdline.needles : 13
              questions.P9-1_kernel_cmdline.hits    : []
              controls.documented_commands_missing  : []
```

Thirteen command-line-shaped needles — `cmdline`, `bootargs`, `bootcmd`,
`console=`, `root=`, `init=`, `mem=`, `rootfstype`, `setenv`, `printenv`,
`env `, `ethaddr`, `bootdelay` — **zero hits**, from a scan demonstrated in the
same run to find all seventeen commands the console prints. There is no
environment mechanism, no storage for one, and no command that sets one.

C's other two sources: the vendor kernel carries
`console=ttyS0,38400 root=/dev/mtdblock1` compiled in with **no `init=`**, and
the string `Kernel command line` is absent from the kernel image, so the boot
log can never print one. That is also why `coldboot-timing.sh` reports a `FAIL`
on this unit and why that `FAIL` is correct.

### The question rlxfw actually has

The plan's stated reason for asking was *"if there is a way, R4's
`root=/dev/nfs` need not change the kernel's built-in cmdline."* There is no way
**through the loader**. But R4 is not constrained by the vendor kernel's layout
— rlxfw builds the image. Three options, and the loader decides which are cheap:

| | how | cost | zero flash writes? |
|---|---|---|---|
| **1** | `CONFIG_CMDLINE` compiled in | a rebuild per change — the thing R4's 90-second budget exists to avoid | yes |
| **2** | **a fixed-address, uncompressed cmdline buffer in my own image, patched with `EB`/`EW` at the console before `J`** | one `EW` line per change; needs the buffer outside the compressed payload and at a stable address | yes |
| **3** | a shim that sets `a0`/`a1`/`a2` before entering `kernel_entry` | more head.S, and buys nothing option 2 does not | yes |

**Option 2 is the recommendation**, and §f is why it works: `EB`/`EW` write any
address with no bound check, and `J` leaves `a0`–`a3` in a state the target
cannot rely on, so a fixed buffer is more dependable than a register convention
anyway.

**Why the same trick does not work on the vendor kernel** — the part worth
keeping: its cmdline lives inside the LZMA payload behind a self-extracting
stub, so patching RAM after `FLR` reaches compressed bytes. **(C, RUNBOOK
§8.12.10.)** The constraint was never the loader's write primitive; it was the
image layout, and rlxfw controls the image layout.

**Inferred, pending a measurement:** that a buffer at a fixed address survives
from `FLR`/TFTP load to kernel entry untouched. The loader's `.bss` begins at
`0x8040DD10` and its stack is below that, so a buffer inside my image at
`0x80500000`+ is not in the loader's way — but "not in the loader's way" is a
reading, not a measurement. R4's first payload should read the buffer back and
print it.

---

## e. `burn()`

`docs/loader-flash-write.md`. Not restated here.

One cross-link that only appears when d, e and f are read together: **`SFCSR`
and `SFDR` do not support byte access (D).** The SPI controller therefore cannot
be poked with `EB` at all — only with `EW`. And there is no `EH` (below), so any
16-bit-only register on this part is unreachable from the console.

---

## f. Four paths write arbitrary memory, not one

The question as the plan phrased it — *"which of the seventeen can write an
arbitrary memory address? is `EB` byte-only? is there a word version?"* — has a
narrower answer than the situation. `EB` is byte-only, `EW` is the word version,
**and two other paths write memory at a scale neither approaches.**

| path | granularity | bound check | confirmation | echo | volume per command |
|---|---|---|---|---|---|
| **`EB <addr> <v>…`** | 1 byte | **none** | none | **silent** | ≤ 18 bytes |
| **`EW <addr> <v>…`** | 4 bytes | **none** | none | **silent** | ≤ 72 bytes |
| **`FLR <dst_RAM> <src_flash> <len>`** | flash → RAM block | **none on `dst`** | `(Y)es , (N)o` | success/fail line | **whole flash regions** |
| **TFTP write, after `LOADADDR`** | network → RAM | **none** | none | size line | **megabytes** |
| ~~`EH`~~ | 2 bytes | — | — | — | **does not exist** — below |

All four are **(A)**, read instruction by instruction.

The per-command volumes come from the tokeniser at `0x80407248` **(A)**: it
`memset`s 80 bytes at `0x8040EAE0` — twenty pointers — and stops splitting at
exactly twenty (`li a1,20`, `beq s1,a1`). The dispatcher passes `argv+1`, so one
line carries at most nineteen arguments, of which the first is the address. The
separator is the space character only (`li a0,32`).

### `EW` — `0x80409650`

```
80409670   lw    a0,0(a1)          ; argv[0]        -- no argc guard before this
80409678   jal   strtoul(_,_,16)
80409680   move  s0,v0             ; the address, verbatim
80409684   andi  v0,v0,0x3
80409688   beqz  v0,aligned
80409690   addiu s0,s0,1           ; NOT aligned: round UP, one byte at a time
80409694   andi  v0,s0,0x3
80409698   bnez  v0,0x80409690
804096a0   beqz  v0,return         ; argc-1 == 0 -> write nothing
804096b4   lw    a0,4(v0)          ; argv[1+i]
804096bc   jal   strtoul(_,_,16)
804096c4   sw    v0,0(s0)          ; *** the store ***
804096d4   addiu s0,s0,4
```

The base register of that `sw` traces to `strtoul(argv[0])` with **no mask and
no comparison against any limit** on the way. §8's refutation condition is
written against exactly this.

Four properties that will bite at the bench, none of them in the help string:

- **An unaligned address is silently rounded *up*.** `EW B800311E 0` writes to
  `0xB8003120`. It does not refuse, and it does not say anything.
- **`EW` prints nothing at all.** Success and "wrote to the wrong place" look
  identical. A write is confirmed only by reading it back with `DW`.
- **`EB` rounds nothing** (it is a byte store), so `EB` and `EW` disagree about
  what a given address means. The unreachable `sh` writer rounds *down*. Three
  policies, three functions, adjacent in the image.
- **A bare `EB` or `EW` with no arguments costs a power cycle.** `argv[0]` is
  loaded before any count test, and the tokeniser zeroes all twenty pointer
  slots each line, so `strtoul(NULL, …)` dereferences. Six handlers share this
  shape; `loader-unpack.py --commands` marks them.

### `EB` — `0x8040978C`

The same shape with `sb`, the value masked to 8 bits, and the address used
verbatim. Two differences from `EW`, both read out of the code: the loop guard
is `blez` (signed) where `EW` uses `beqz`, and the loop index is truncated to
8 bits (`andi s1,v0,0xff`) where `EW` truncates to 16. Both truncations are
unreachable — a line is capped at 20 tokens.

### Measured 2026-08-24: `EW` rounds up, `EB` does not, and the asymmetry is the finding

Both were read out of the code above. Both are now measured on the device, in
one seating, `bench/2026-08-24/C1`–`C4`.

| sent | read back | reading |
|---|---|---|
| `EW 81000000 DEADBEEF CAFEBABE` | `81000000: DEADBEEF CAFEBABE …` | `EW` takes **several** values and writes them as consecutive 32-bit words from the address given. It prints **nothing** |
| `EW 81000102 11111111` | `81000100: 00000400 **11111111** …` | 🔴 **`EW` rounds an unaligned address UP, silently.** `0x81000102` became `0x81000104`. Not down, and not refused |
| `EB 81000200 41 42 43` | `81000200: 41 42 43 00   ABC.` | **`EB` takes the address verbatim.** No rounding |

**One loader, two write primitives, opposite address handling, neither of them
saying so.** For `R4`'s fixed-address command-line buffer that is not trivia:
a byte-granular edit has to go through `EB`, and any `EW` has to be aligned by
the caller, because the loader will align it either way and will not mention it.

`EW`'s silence is only a measurement because the read-back is a separate cell.
**A cell whose expected answer is "nothing" cannot tell a silent command from a
command that never arrived** — which is the same disease as a control that
expects zero, one layer up.

### Measured 2026-08-24b: `EW` writes exactly `argc − 1` words, and the hex parse is `strtoul`-like

Two lines sent at the top of the length cliff below, each with an **over-run
control** — the word immediately past the last one the command should have
written, read back in the same reply.

| | line | chars | log | read back by |
|---|---|---:|---:|---|
| `C7a` | `EW 81000400` + **twelve** values | 119 | 130 bytes, echo only | `C7a-rb`, `DW 81000400 16` |
| `C7b` | `EW 81000440` + **eleven** values, leading-zero padded | 127 | 138 bytes, echo only | `C7b-rb`, `DW 81000440 16` |

**Measured: `EW` writes exactly `argc − 1` words, not "at least".** All twelve of
`C7a`'s values landed in order across `0x81000400`–`0x8100042F`, and the fourth
line of its readback, `0x81000430`, is byte-identical to the pre-state `C7-pre`
read there before either write. All eleven of `C7b`'s landed, and word twelve at
`0x8100046C` still reads the `00000000` `C7-pre` had read there.
**Refutation condition, written before either cell ran:** any change
at `0x81000430` or at `0x8100046C`. Neither moved. What those control words
actually hold is not this file's question — `0x81000400` turned out not to be
scratch memory, and that finding is owned elsewhere; what is used here is only
that they did not move.

That also puts consequence 2 below on silicon rather than in arithmetic: the
twelve-word line was counted from the buffer size, and `C7a` executed it.

**Measured: the loader's hex parse is `strtoul`-like, not fixed-width.** `C7b`'s
first six arguments were written with **ten** characters — `00C7B00001` — and its
last five with nine. Every one read back as the value with its leading zeros
dropped: `C7B00001`, `0C7B00007` → `C7B00007`. **A fixed eight-digit reader would
have taken `00C7B000` and left `01` dangling, shifting every argument after it.**
Refutation condition: `00C7B000` in the readback, or `FFFFFFFF`, or the line
answering `Unknown command !`. **What this does not test:** an argument whose
*value* exceeds 32 bits. None was sent, so the overflow behaviour is still
unmeasured.

**No file in this repository predicted this.** The disassembly names
`strtoul(_,_,16)` at `0x80409678`, and that reading is consistent with the
result, but nothing here had turned it into a claim about digit count — the
eight-digit argument was a convention, not a measurement. The padding was chosen
as `C7b`'s method for exactly that reason: a wrong answer lands a wrong **value**
at a known address rather than a wrong **address** somewhere unknown.

### 🔴 The console line buffer is 128 bytes, and exactly 128 is the dangerous length

Two sources, and the first one arrived by accident.

**Measured.** `§A`'s capture streamed ESC across power-on and kept streaming
after the prompt appeared. The transcript shows the loader taking **exactly 128
ESC bytes and then answering `Unknown command !` — seven times, the same number
every time** (`bench/2026-08-24/A-catch.log`). At roughly 50 ESC per second a
timing artefact would not land on the same count seven times.

**Measured again on a second power cycle, 2026-08-24b: the 128 is a partition of
the byte stream, not the number 128 turning up.** Every ESC byte the loader
echoes is accounted for as `128 × (Unknown command ! lines) + a residue`, and the
residue is still sitting in the buffer when the capture ends:

| capture | ESC echoed | bursts | `Unknown command !` | the residue, and what took it |
|---|---:|---|---:|---|
| `bench/2026-08-24/A-catch.log` | 908 | `[128 × 7, 12]` | 7 | 12 — consumed by the next command, consequence 3 below |
| `bench/2026-08-24b/A-catch.log` | 730 | `[128 × 5, 90]` | 5 | 90 — consumed by `flush` (`--send ''`, one bare CR): 31 bytes and **exactly one** `Unknown command !` |
| `bench/2026-08-24b/B7c.log` | 985 | `[128 × 7, 89]` | 7 | 89 — consumed by `flush-b7c`, one more `Unknown command !` |

`730 = 5 × 128 + 90`; `985 = 7 × 128 + 89`. **Twelve unterminated fills across two
independent power cycles**, and in both 24b cases the leftover was turned into
exactly one further `Unknown command !` by one bare CR.

**Refutation condition:** an ESC capture whose echoed byte count is not
`128 × n + r` for `n` `Unknown command !` lines and `0 ≤ r < 128`, or a residue
that a following bare CR does not turn into exactly one more.

**Two things had to hold for that arithmetic to close, and both are measured.**
*The ESC-window consumer does not echo; the command loop does* — about 115 ESC
bytes were written between power-on (`t = 8.129 s` in the 24b capture) and the
prompt (`t = 10.445 s`) and **not one appears in the log**, while every ESC after
the prompt is echoed. `gCHKKEY_HIT`'s path and `readline` are different code, and
the log counts only the second. And *the ESC rate is the host tool's ceiling, not
the wire* — 730 bytes over 14.55 s = **50.2 ESC/s**, where at 38400 those same
bytes are 0.19 s of wire time. The ceiling is `console-capture.py`'s
`ser.write(ESC); drain(0.02)` loop, 20 ms per byte.

**That is what makes an `--esc-after N` residue predictable, and it is an
operating number.** `--esc-after 20` streams ≈ 1000 bytes ≈ 7 fills plus a
residue near 100; `B7c` measured 985 and a residue of 89. A residue `r` followed
by a command of length `L` with `r + L ≥ 128` **cuts that command** — the
unterminated case above, reached with a line nobody typed. One bare CR before the
next command removes `r`.

**Read.** The command loop at `0x80409144`:

```
80409188:  move  a0,s5          ; s5 = sp+16, the line buffer
80409190:  jal   memset         ; li a2,128    -- 128 bytes, zeroed every time
804091a0:  jal   0x8040708c     ; li a1,128    -- readline(buf, 128, echo=1)
```

and `readline` itself has three exits, of which **only one writes a terminator**:

```
804070e8:  beq  a0,10 -> 8040719c     '
'   returns, NO NUL
804070f8:  j          -> 8040719c     '
'   returns
804070fc:    sb zero,0(s0)            ...     the NUL, in the delay slot
80407190:  sltu v0,s2,s5              count < 128 ?
80407194:  bnez v0    -> loop         count == 128 returns, NO NUL
```

So a line is terminated by one of two things: the `
` path writing a NUL, or a
**leftover zero from the caller's `memset`**. The second only exists while the
text is **shorter** than 128.

> **At exactly 128 characters the buffer is full of text, no NUL was written,
> and there is no leftover zero.** The tokeniser at `0x80407248` then scans past
> `sp+143` into the eight bytes of stack slack below the saved registers, and on
> into `s0` at `sp+152`. The stack frame is 184 bytes with the buffer at `sp+16`.

**Consequences, and the first one caught a cell before it ran.**

1. **`RUNSHEET.md` `C7` sent a 173-character `EW` line.** `readline` would have
   cut it at 128 — `EW 81000400 ` plus twelve values plus the thirteenth's eight
   hex digits is exactly 128 — i.e. precisely the unterminated case, with `EW`
   as the command and the argument count coming out of stack slack. C7 is
   rewritten to twelve values, 119 characters, and **no command line anywhere may
   be exactly 128 characters**.
2. **One console line carries twelve words, 48 bytes.** A 1 KiB bare-metal probe
   needs 22 lines, not the 15 the sheet assumed — `R1`'s no-network path is 47%
   more expensive, and that is now a measurement.
3. **The buffer is per-`readline`, not per-connection.** Twelve ESC bytes left
   over from a truncated capture were still pending when the next command was
   sent, and the loader dispatched the concatenation. Closing the serial port
   does not clear it.
4. For `R9`'s differential table: **the vendor loader's console reads past its
   own input buffer on a full-length line.** Recorded here, not in
   `$FWRE_WORK/disclosure/` — it needs an attacker who already has the serial
   console, which is the same access that can already write arbitrary memory
   with `EW`.

**The standing flush rule, corrected 2026-08-24b: it named the wrong trigger, in
both directions.** As written it read *"after any capture cut short by
`--seconds`, send one bare CR"*.

- **Wider than it needs to be.** **Measured:** part one's `C1 · C2 · C3a · C3b ·
  C4a · C4b · C6-readback` — seven consecutive `--send` captures — were **all**
  stopped by `--seconds` (each `meta.json` carries `stop_reason: --seconds N
  elapsed` and `esc_seconds: 0.0`), **none** was flushed, and every one of them
  is correct. The `--seconds` deadline ends the *reading*. It leaves nothing on
  the wire, because the last byte a `--send` capture wrote to the port is the CR
  the tool itself appended.
- **The real trigger is *any capture whose last byte written to the port was not
  a CR*** — in practice, any capture that ran `--esc` or `--esc-after`. Those
  loops end on a wall-clock deadline and write no terminator, so whatever the
  deadline cut mid-line stays in the buffer.
- **Narrower than it reads.** A USB re-enumeration of the console adapter is not
  a capture at all, and needs the same throwaway.

**The re-enumeration case, measured.** After the CP2102 left the host's USB bus
mid-session and was re-attached, the next command sent — `CONT`,
`DW 8040DCE8 1` — came back **24 bytes**: the echo, `\n\r`, `<RealTek>`, and **no
data line**. That is `len(command) + 11`, the shape of a *silent* command, and 47
bytes — exactly one line — short of the 71 that command's reply weighs (*The read
side*, below). The obvious explanation, residue in the line buffer, is
**refuted**: the next cell, `flush-cont` (`--send ''`), returned **11 bytes, a
bare prompt with no `Unknown command !`**, so the buffer was empty. `CONT2`, the
identical command sent afterwards, returned the structural 71.

> **The first thing sent after the console adapter re-enumerates is a throwaway,
> and its signature is echo + prompt + no output.**

*Inferred, pending a measurement:* the board's UART saw a break or a framing
error during re-enumeration and `readline` discarded what it held, leaving the
trailing CR to produce an empty-line prompt. The behaviour is measured; the
mechanism is not.

**Refutation condition for the corrected rule:** a capture that wrote a CR as its
last byte and nevertheless left residue — a following bare CR answering
`Unknown command !`. Three bare CRs were sent in `bench/2026-08-24b/` and the
probe demonstrably fires: `flush` after `A-catch` and `flush-b7c` after `B7c`,
both ESC captures, both answered `Unknown command !`; `flush-cont` after `CONT`,
a `--send` capture, answered a bare prompt. Two firings and one silence, so the
silence is a result and not a test that cannot fail.

### `FLR` — `0x804099AC`, and it is the one to be careful with

Three `strtoul(_,_,16)`, **no bound check on any of them**, then:

```
80409a04   sw    s0,-8920(v0)      ; 0x8040DD28 = length   <- the TFTP length global
80409a2c   jal   0x80409B18        ; "(Y)es , (N)o ? --> "  -- 'Y' or 'y' only
80409a44   jal   0x80404F38        ; flash_read(dst_RAM, src_flash, len)
```

**`FLR`'s first argument is the RAM destination** — the printf at `0x80409A18`
takes `argv[1]` first (`Flash read from %X to %X with %X bytes`), which is a
third source for the argument order and the one that needs no device. A mistyped
destination writes a flash region over whatever is there, including the loader's
own `.data` at `0x8040D000`+. The `(Y)es` prompt is the only thing between a
typo and that.

**Two operating consequences, desk-verified 2026-08-24b, neither yet run on the
device.**

- **One `FLR` read costs three captures.** The confirmation at `0x80409B18`
  prints `(Y)es , (N)o ? --> ` and takes `Y` or `y` on a second line (read out of
  the code), and `console-capture.py`'s `_check_send` refuses a `\r` or `\n`
  inside `--send`, so the two lines cannot be merged into one cell (read out of
  the tool, `_check_send` in `tools/console-capture.py`). The sequence is
  `FLR …`, then `Y`,
  then the `DW` that reads what landed — three captures, and a runsheet that
  budgets one is wrong by two.
- **No TFTP `put` or `get` may follow an `FLR`.** `0x80409A04` stores the length
  argument into `0x8040DD28`, which is the same global the TFTP read path serves
  from (§c). An `FLR` therefore silently redefines how many bytes a later `get`
  returns, and it says nothing about having done so. Any flash re-read that
  brackets a transfer has to be split into one cell before it and one cell
  after — not one cell on either side of a `put`.

### `EH` exists as code and cannot be reached

`0x804096F4` is a complete halfword writer — `and s0,v0,~1` (round *down*), then
`sh` in a loop. It is **unreachable**:

| search | positive control | result |
|---|---|---|
| `jal` to `0x804096F4` (encoding `0c1025bd`) | the same search for `strtoul` at `0x80406EE0` finds **32** | **0** |
| the word `804096f4` anywhere in the image | the same search finds `EB`'s handler at `0x8040DBF8` and `EW`'s at `0x8040DC08` — their command-table rows | **0** |
| `lui`+`addiu`/`ori` building the address | — | **0** |

**B explains it exactly.** `monitor.c`'s table:

```c
    { "EW",2, CmdWriteWord,  "EW <Address> <Value1> <Value2>..."},
#ifdef REMOVED_UNUSED
    { "EH",2, CmdWriteHword, "EH <Address> <Value1> <Value2>..."},
#endif
    { "EB",2, CmdWriteByte,  "EB <Address> <Value1> <Value2>..."},
```

The **table row** is conditioned out; `CmdWriteHword` itself is not, and the link
has no `--gc-sections`. So the function is in the image, in source order,
between the two that are reachable. B's `CmdWriteWord` / `CmdWriteHword` /
`CmdWriteByte` match A line for line, down to the round-up loop, the round-down
mask, and the per-function value width.

One divergence, and A wins: B declares `unsigned int i` in `CmdWriteWord` while
A truncates the index to 16 bits. Different SDK vintage; the binary is the
authority for this unit.

### The read side, because a silent write needs one

**(A.)** `DB <addr> [len]` and `DW <addr> [len]`, and both carry a trap:

- **the length is parsed base 10** (`li a2,10`) while every other numeric
  argument in the loader is base 16. `DB 80500000 64` reads 64 bytes, not 100.
- `DB` defaults to 16 bytes. `DW` defaults to 1 and counts **words**, four to a
  line. The loop steps `i` by 4 while `i < N` and each pass prints four words, so
  `DW <addr> N` prints **`4 × ceil(N/4)` words** — always a multiple of 16 bytes,
  never fewer than four words, and `N` rounded **up**. The next subsection is
  that arithmetic written out, because a cell got it wrong.
- **`DW` forces the address into KSEG0** when bit 31 is clear
  (`if ((signed)src >= 0) src |= 0x80000000`) and rounds up to 4. `DB` does
  neither. So `DB` and `DW` also disagree about what an address means.
  🆕 **Measured 2026-08-25, and it is the bit 31 = 1 half that had never been
  exercised**: `DW A0000080 32` printed a first address of **`A0000080`** and the
  same 32 words as `DW 80000080 32`. So the rewrite really is conditional, the
  uncached alias really is read through KSEG1, and *the vector is not there* is
  now distinguishable from *a stale D-cache line was handed to `DW`*
  (`bench/2026-08-25/H0a3.log`).
- 🆕 **`DW` does NOT align its start address down**, measured 2026-08-25.
  `DW 8040054C 32` — the first unaligned address this project has ever given it —
  printed `8040054C:` and then `8040055C:`, `8040056C:` …, incrementing by `0x10`
  from wherever it was told to start. **The `4 × ceil(N/4)` round-up is on the
  *count*, not on the *address*.** Written as an open question in that seating's
  prediction block before the read, because every measured reply until then had
  begun on a 16-byte boundary and the two behaviours were indistinguishable
  (`bench/2026-08-25/H0a2.log`). ⚠️ **It is the opposite of `EW`**, which rounds
  an unaligned address up and does not say so — one loader, two commands,
  opposite handling, and the pair is now measured on both sides.
- `DW` is the only one of the four that guards `argv[0]` against NULL. It prints
  `Wrong argument number!` and survives.

### 🔴 `DW <addr> N` prints `4 × ceil(N/4)` words, and `N = 3` is a truncation trap

Read out of the code at `0x804094B4`, measured across two seatings. `N` is not a
word count anything honours; it is a **line count in disguise, rounded up**:

| `N` | words printed | lines | measured on |
|---:|---:|---:|---|
| 1 | 4 | 1 | `A0`, `E1b`, `CONT2` — 71 bytes each |
| **3** | **4** | **1** | never sent, and the reason is below |
| 8 | 8 | 2 | `C7-pre2`, `E10b`, `E9b`, `E11a` — 118 bytes each |
| 10 | 12 | 3 | `B9`, `bench/2026-08-23/B.log` |
| 16 | 16 | 4 | `C7a-rb`, `C7b-rb` — 213 bytes each |
| 28 | 28 | 7 | `C7-pre` — 354 bytes |

**The trap was live.** `RUNSHEET.md` `C7` asked for **`DW 81000400 3`** to read
back the **twelve** words the cell had just written. That prints **one line of
four**. And `C7`'s entire failure mode is the write being *truncated*, so a
four-word readback would have looked exactly like a truncation at the fourth
value: **the cell would have manufactured, out of its own read command, a false
positive of precisely the thing it exists to catch.** Corrected at the bench to
`28`, `16` and `16`.

**Refutation condition, and it costs nothing to check on every future cell:** a
`DW <addr> N` whose reply carries anything other than `4 × ceil(N/4)` words.

#### What a reply weighs

The loader echoes the line, prints fixed-width hex, and ends with a prompt that
carries no newline, so the length of a reply is a function of the command alone:

```
bytes = len(command) + 2      the echo and its \n\r
      + 47 × lines            9 for "AAAAAAAA:" + 4 × (tab + 8 hex) + 2
      + 9                     "<RealTek>"
```

with `lines = ceil(N/4)` for `DW`, and **`lines = 0` for the silent writers** —
`EW` and `EB` print nothing, so their whole reply is `len(command) + 11`.

Six values, each predicted before its cell ran and each exact:

| capture | command | predicted | `.log` |
|---|---|---|---:|
| `A0` | `DW 8040DBC0 1` | 13 + 2 + 47 + 9 | **71** |
| `E10b` | `DW BB804128 8` | 13 + 2 + 2×47 + 9 | **118** |
| `C7a-rb` | `DW 81000400 16` | 14 + 2 + 4×47 + 9 | **213** |
| `C7-pre` | `DW 81000400 28` | 14 + 2 + 7×47 + 9 | **354** |
| `C7a` | `EW …` twelve values, silent | 119 + 2 + 9 | **130** |
| `C7b` | `EW …` eleven values, silent | 127 + 2 + 9 | **138** |

**Scope, because the formula is easy to over-read.** It holds for `DW` and for
the silent writers. It does **not** describe every command: `PHYR 1 5` (`E12b`)
returns 87 bytes of prose, one line of its own shape. And it applies to
`console-capture.py` `.log` files, which hold exactly the bytes the port
delivered — not to a terminal transcript such as `bench/2026-08-23/B.log`.

**Why it is worth carrying:** a predicted reply length is a control that costs
nothing and that a truncated or stale capture cannot pass. A capture short by 47
lost a line; short by 9, lost the prompt; off by anything else, it is not the
reply to the command that was sent. `CONT`'s 24 bytes — 71 predicted, one line
missing — is the case where this fired.

✅ **2026-08-25: this is `tools/reply-size.py` now, and the population went from
fifteen hand-counted cases to 121.** `reply-size.py check bench/` classifies
every capture that carries a `sent` field and no ESC stream: **121 modelled, 0
unexplained.** The per-family constants were FITTED from those captures rather
than read out of the loader or counted in a terminal — `DW` 47×⌈N/4⌉ over 91
samples, `EW`/`EB` no output over 11, `Y` 23 over 6, `PHYR` 68 over 5, and `FLR`
79 over 6 **with no `<RealTek>` at all**, because it stops at its own Y/N prompt.
`DB`, `J` and `MDIOR` are declared UNMODELLED with their sample counts and their
reasons, and an unmodelled capture is never counted as a hit.

🔴 **The two captures that do not match the formula each got a name instead of a
miss.** `CONT`'s 24 bytes are `ECHO-ONLY` — the command was echoed and not acted
on, which is `C-19`'s signature — and `A0-reopen-control`'s 44 are
`UNKNOWN-COMMAND`. Folding either into "short" would throw away the thing a
bench operator actually needs to know.

**The reason it is a tool and not a formula in a document** is `block 3` on
2026-08-25: predicted 214 bytes, measured 213, because `DW 81000400 16` is
fourteen characters and a person counted fifteen. `check-predictions.py` verifies
that a prediction file predates its capture; it does not verify the arithmetic
inside it. `reply-size.py`'s control `C8` is that exact case.

### The reset R4 needs, and it is already a command

`J BFC00000`. **(A.)**

```
804092d4   lui   v0,0xbfc0
804092d8   bne   v1,v0,normal_jump
804092e4   ori   v0,v0,0x311c      ; 0xB800311C
804092e8   sw    zero,0(v0)        ; WDTCNR = 0
804092ec   j     0x804092ec        ; spin until it bites
```

Interrupts are already masked ~~two instructions earlier~~ (`GIMR0 = 0`, `IE`
cleared), so nothing can leave that spin except the watchdog.

🔄 **2026-08-25: *two instructions earlier* is wrong, and the audit was right
to flag it.** `docs/rlxprobe-audit-2026-08-25.md` recorded this sentence as the
reverse of what `tools/rlxprobe/uart.S` says about the same address, and left
which one is wrong open. **Neither is wrong about behaviour.** The three
instructions above -- `lui` / `ori` / `sw zero` -- mask nothing, which is what
`uart.S` says and what `rlx_reset` copies. The masking is real but it is not
local: the two `sw zero,0(0xB8003000)` sites are at **`0x804086E4` and
`0x80408700`**, in the `J` command's own handler, roughly 2,500 bytes before this
and in a different function. So the defect is the phrase, not the claim.

🔴 **Residual, and it is the part that actually matters for a payload**:
whether EVERY path that reaches `0x804092E8` passes through one of those two
sites is **untraced**. This is 讀 out of the two addresses this document already
records, not a fresh disassembly. Until it is traced, *"interrupts are off when a
payload starts"* rests on `J <addr>`'s path and on nothing else -- which is
exactly the leg `probe2` could check for two lines by reading bit 0 of the
`Status` word it already has in hand, and does not.

**`0xB800311C` has four sources, and one of them is behavioural:**

| | says |
|---|---|
| **D**, §8.2.9 Table 27 | `WDTCNR` at `0xB800_311C`. `WDTE[7:0]` at 31:24, **default `0xA5` = stopped, any other value enables**; `WDTCLR` bit 23; `OVSEL[1:0]` at 22:21 and `OVSEL[3:2]` at 18:17, `0000` = 2^15 through `1001` = 2^24 base-clock ticks; **`WatchDogIND` bit 20 — `0` = power-on or pin reset, `1` = a watchdog reset occurred, write 1 to clear** |
| **E** | `TC_BASE 0xB8003100`, `WDTCNR (TC_BASE + 0x1C)`, `WDTE_OFFSET 24`, `WDSTOP_PATTERN 0xA5`, `WDTCLR (1<<23)`, `WDTIND (1<<20)` |
| **B** | `*(volatile unsigned long *)(0xB800311c)=0; /*this is to enable 865xc watch dog reset*/` — in `monitor.c`'s `CmdCfn`, the same function, with the vendor's own comment. And `btcode/start.S`: `REG32_ANDOR(0xb800311c, 0x00ffffff, 0); //WD start, set [31:24] to not "A5"` |
| **A** | this loader writes the same zero at **two** sites: the `J BFC00000` case, and `0x8040130C`, immediately after printing `reboot.......` — the post-flash-write reboot |

So `WDTCNR = 0` means the enable field is not `0xA5`, so the watchdog runs, and
`OVSEL[3:0] = 0000` selects **the shortest of the ten available timeouts**.

**Inferred, pending a measurement:** the wall-clock delay. The base clock comes
from `CDBR`, which this loader sets to `0x000E0000` at `0x80408F34` — divisor
field `0x0E` = 14 — but the bus clock it divides is not established anywhere in
this repo, so 2^15 ticks is a count and not a time. **Do not put a number in a
runbook until R1 measures the clock.**

**Two things this buys R4.** `bench-ci` needs no new primitive and no `EW` at
all — `J BFC00000` is a stock command. And **`WatchDogIND` is a post-reset
discriminator**: bit 20 of `WDTCNR` separates "the watchdog fired" from
"something else reset the board", which is exactly what `C-8` needs and is not
something a boot log can tell you.

### What cannot be reached from the console

Stated because an incomplete capability list reads like a complete one: there is
**no** 16-bit write, **no** memory fill (`CmdWriteAll` is `#ifdef
REMOVED_UNUSED` in B and is absent from A too), **no** register-space command
other than the PHY/switch pair (`MDIOW`, `PHYW`), and **no** way to read or
write CP0. R1's bare-metal payload is not avoidable.

---

## 8. What the bench has to confirm, and what would refute it

**Nothing in this file has been sent to the device.** This section lists what a
reading of the code predicts and what outcome would prove it wrong. It
deliberately does **not** give an operating procedure — that belongs to whichever
runsheet owns the session, and a command re-stated by hand in a file that does
not own it is how C's `A2.7` went wrong four ways at once.

| # | prediction, from the code | what refutes it | risk |
|---|---|---|---|
| **1** | `0x8040DD3C` holds the accepted candidate, biased by `0x05000000`; on this unit it reads `0x05060000` | any other value, or zero | read-only |
| **2** | `0x8040DD48` holds the image's `startAddr` from its header; it reads `0x80500000` | any other value | read-only |
| **3** | RAM at `0x80500000` already holds flash `0x060010` when the prompt appears, because the *check* copied it | the two differ | read-only |
| **4** | a `DW` length argument is decimal, not hex. `DW <addr> 10` prints **three** lines (`i` runs 0, 4, 8 against a limit of ten) | four lines, which is the `0x10` reading | read-only |
| **5** | `EW` rounds an unaligned address **up**; `EB` does not round at all | a write landing below the requested address, or `EW` refusing | writes RAM — pick a scratch address, never `0x8040D000`+ |
| **6** | `EW` and `EB` print nothing on success | any output at all | as 5 |
| **7** | `J BFC00000` resets the board, and **the ESC window still appears afterwards** | no reset; or a reset that boots straight through | reset, no flash write |
| **8** | after that reset, `WDTCNR` bit 20 (`WatchDogIND`) reads **1**; after a power cycle it reads **0** | bit 20 reads the same in both cases → the bit does not discriminate on this part, and `C-8` needs another observable | read-only |
| **9** | a bare `EB`, `EW`, `LOADADDR`, `FLR`, `FLW`, `PHYR` or `PHYW` with no arguments hangs or resets the board | it returns to the prompt | **costs a power cycle. Do not run it to see; it is listed so it is not run by accident** |

Prediction 8 is the one worth the seating. It is the difference between "the
reset worked" and "something reset the board", and `bench-ci` is built on top of
the answer.

**Not settled by any of these, and it must not be inferred from them:** whether
a deliberately corrupted image reaches the prompt in practice (`C-4`'s remaining
half), and anything at all about `AUTOBURN 1`. Neither is in this list, and
neither should be added to a session that is otherwise zero-write.

---

## 9. What this traversal turned up that item 4 did not ask for

### Two MIPS-IV instructions run on this unit's boot path, and nothing complains

`-m mips:3000` printed `.word` twice inside `check_image()`. Decoded with a
MIPS32 reader they are `movz s3,v1,v0` at `0x80407E20` and `movn s3,zero,s4` at
`0x80407ED8` — the "is it `cr6c`" result and the "is the checksum zero" result.

A sweep of the whole image, with the code/rodata boundary at `0x8040A000` — the
same boundary `notes/lwl-mystery.md` used, and a conservative one: the first
string this reading found is at `0x8040A4E0`:

| region | non-MIPS-I opcodes found |
|---|---|
| `0x80400000`–`0x8040A000` (code) | **`movz` × 12, `movn` × 6, and nothing else.** `tools/opcount.py` over the same range reports **zero** for every one of its twenty-one rows: `lwl` `lwr` `swl` `swr` `cache` `ll` `sc` `pref` `beql` `bnel` `blezl` `bgtzl` `SPECIAL2` `SPECIAL3` `COP1` `lwc1` `ldc1` `swc1` `sdc1` `jalx` `sync` |
| `0x8040A000`–`0x8040DD10` (rodata, tables) | 28 hits between the two tools, every one of them ASCII or table data: `'Undefined '`, `'pload, F'`, `'ss! File'`, `'sum erro'`, `0xc0a80001` = `192.168.0.1`, and the SPI chip table's `0x0000004b` at a `0x20` stride |

The second row is the control. **Two decoders that reported zero everywhere
would prove nothing; both demonstrably fire, and every false positive is visible
as text in the hex dump beside it.**

#### Correction, 2026-08-24: the code row reproduces exactly and the data row does not

A third decoder — `tools/hazlint --isa`, written for `DAY-ZERO` item 7 — was run
over the same file with the same boundary.

**The code row is exact and now has three sources.** `[0x80400000, 0x8040A000)`
gives **18** hits, `movz` × 12 and `movn` × 6, at the eighteen addresses above,
one for one, under *both* of that tool's classifiers, and
`mips-linux-gnu-objdump -m mips:3000` emits a `.word` at every one of them.
(It emits four more, at `0x80400C40`, `0x80400C44`, `0x80400C68` and
`0x80400C7C` — `COP0` words with `rs = 3`, which is neither `mfc0` nor `mtc0`
and which no source held here names. They are almost certainly the Lexra CP0
accesses `notes/cache-model.md` describes, and they are **not** counted above.
Recorded here because a decoder that printed them and a decoder that did not
were both called "18".)

**The data row does not reproduce, and the reason is the finding.** Three
classifiers over `[0x8040A000, 0x8040DD10)` give three answers:

| classifier | hits |
|---|---:|
| `hazlint --isa --loose` — opcode and funct only | **445** |
| `hazlint --isa` — strict; the fields an encoding fixes at zero must be zero | **236** |
| `objdump -m mips:3000`, counting `.word` | **829** |

None of them is 28, and no classifier that can be constructed from what this
file records produces 28: the row names `0x0000004b` as `movn`, which a **loose**
reader accepts and a strict one rejects (its `sa` field is 1), and it names
`'pload, F'` as `clo`, which is `SPECIAL2`. A watch list narrow enough to give a
number near 28 was in use, and **that list was never written down**.

**So 28 is withdrawn as a control and kept as a record.** What replaces it is
not another number but the property the row was reaching for, in a form that can
fail: `hazlint` asserts that the loose classifier still finds `ll` at
`0x8040AB14` (`c0a80001` = `192.168.0.1`) and `movn` at all six of the SPI
table's `0x20`-stride `0x0000004b`s — **the two false positives this section
names by value** — and that the strict classifier rejects those six. Both
classifiers' counts are printed side by side on every run.

> **A count whose classifier is not named is not a measurement.** That is the
> general form of what went wrong here, and it is the same shape as the
> hand-copied command table in §8.12.46 of upstream's runbook: a correct set of
> values under a sentence that does not say what produced them reads exactly
> like two correct things.

#### And two hazard shapes that are not load hazards, counted while passing

`tools/hazlint --survey` over the same file, **counts and not verdicts**, because
`C-9` is open and `R1b` owns the rule:

| shape | count | first addresses |
|---|---:|---|
| `mult`/`div` immediately followed by `mfhi`/`mflo` | **16** | `0x80403C14`, `0x80404248`, `0x804042A0`, `0x80405648` |
| `mtc0` immediately followed by `mfc0` | **3** | `0x80400408`, `0x8040041C`, `0x80400660` |
| a load sitting in any branch or jump delay slot | **0** | — |

The first of the `mtc0` sites is `mtc0 zero,c0_status` at `0x80400408` followed
at `0x8040040C` by `mfc0 t1,c0_status` — **the same register, written and then
read with nothing between.** The vendor's compiler inserted no `nop` in any of
the nineteen. That is consistent with a core that interlocks `HI`/`LO` and CP0
while leaving the load delay slot exposed, and it is *also* consistent with
nineteen latent bugs in the loader. **Counting them does not decide between
those**, and R1b's experiment is one `mult`→`mflo` and one `mtc0`→`mfc0` on bare
metal with 0, 1 and 2 `nop`s between.

The third row is why the load check can use a linear scan at all: with zero
loads in a delay slot, "the next word" and "the next instruction executed" are
the same thing everywhere in this file.

Three readings:

1. **`ll`, `sc`, `cache`, `pref` and the FPU loads/stores are absent from the
   loader's code region.** Consistent with the libc decision, and it is the
   first evidence for it out of this unit rather than out of a datasheet.
2. **`lwl`/`lwr`/`swl`/`swr` are absent from the code region**, which
   independently reproduces `notes/lwl-mystery.md`'s `stage2 = 0` with a second
   tool and the same adjudication of the one data-region hit at `0x8040D760`.
3. **`movz`/`movn` are present, and they are on a path this unit runs on every
   boot.** A core without the MIPS-IV conditional moves would take a Reserved
   Instruction exception there.

Reading 3 has a third leg, and it is a measurement on the device rather than a
reading of the code. **The loader carries its own exception reporter**: the
strings `Undefined Exception happen.`, `cp0_cause=%X, cp0_epc=%X`,
`cause by: %s`, `NOT HANDLE TRAP IN JUMP DELAY SLOT` sit at
`0x8040A4E0`–`0x8040A5B0`. 🔄 **The 16-entry table at `0x8040A5C0` above them
is NOT the exception dispatch table** — retracted 2026-08-25, see §10; it is
`BootStateEvent[3][8]`, the TFTP/ARP boot state machine. The real dispatch table
is `exception_handlers[32]` at `0x8040EB40`, in BSS. **(A.)**

`check_image()` necessarily runs between the loader banner and
`Jump to image start=0x80500000...`. **Eighteen console captures of this unit,
four of them covering that whole window, contain neither string.** The
2026-08-18 cold boot spends 4.89 s inside it and prints nothing but the banner
and the jump.

That is an absence claim, so it has a control: the same grep over the same
eighteen files finds `Booting`, `chipName`, `Jump to image start` and
`RealTek`, the last in fourteen of them.

So the alternative to "this core implements `movz`/`movn`" is that something
emulates them *silently*, alongside an exception reporter that would have
printed. **That is a weaker explanation, but it is not excluded here, and it
must not be written down as settled.** What is settled: two MIPS-IV instructions
are executed on this unit's boot path and produce no exception message.

This is an R1a question, not an item-4 question, and it is registered as a
carried-forward item. It matters because it bears on the `-march` decision and
on the Lexra-family core question (RLX4181 or RLX5281, undetermined), and
because **R1a settles it in one instruction**: a bare-metal RI handler, one
`movz`, and a report.

It also hands R1 a fact it would otherwise have discovered by surprise: **the
stock loader has already installed exception handling of its own**, so R1d's
"write my handler to `0x80000080` and make the I-cache see it" is replacing
something, not filling a vacuum. 🔴 **Both halves are measured now,
2026-08-25b.** The vectors live at `0x80000080` in DRAM -- `trap_init` copies 128
bytes there from `0x8040054C` on every boot, and `DW 80000080 32` reproduces it
byte for byte on four consecutive power cycles. And **`Status.BEV = 0`**:
`probe2` read `Status = 0x1000FC00`, and `break` trapped into a handler this
project installed at `0x80000080` and returned (`break.count=1`, `cause=00000024`
= ExcCode 9, `break.epc=80500270`). **That the core FETCHES there is the direct
evidence, not an inference from the copy having landed.**
`bench/2026-08-25b/H2a.log`; `SPEC.md` `CPU-27`.

### A hardware condition that disables image checking

`check_image()` begins by reading the global `0x8040DBA4` and returning 0 —
"no image" — when it is 1. **(A.)** B calls it `gCHKKEY_HIT`. The only writer is
`0x804082B4`, which reads `0xB8002014`, tests bit 24, then compares the top byte
of `0xB8002000` against its argument. That is the UART path, so the flag looks
like *the operator pressed a key*, but the register addresses have not been
confirmed against D and the argument has not been traced. **Inferred, and worth
fifteen minutes before R8**, because a global that makes the loader declare
every image bad is a rescue path and possibly a hazard.

### 🔴 The copier runs on a WARM reset too, and that is structural

**量 2026-08-25b, directly, and it cost a power cycle to find out.** `C-16` asks
what puts flash `0x060010`'s 964 KiB into RAM at `0x80500000` before any `FLR`.
What was not established is **how often**.

The reading: `probe2` was uploaded to `0x80500000` and run; it finished, armed
the watchdog and reset; the loader came back to its prompt; and a **second**
`J 80500000` printed `decompressing kernel:` and booted the factory firmware to
userspace. `bench/2026-08-25b/H2a2.log`.

**So the staging happens on a watchdog reset, not only on a cold power-on, and
the payload had already been overwritten by the time the prompt returned.**

Two consequences, and the second is the one that reaches a procedure:

* `LDR-22`'s blank is narrower: whatever the copier is, it is on the warm-reset
  path as well as the cold one.
* 🔴 **A payload cannot be run twice on one power cycle at
  `LOADADDR = 0x80500000` without re-uploading it.** Any runsheet cell that
  says "run it again to get a repeatability control" is wrong as written. The
  cheap fix for the next payload is a different `LOADADDR`, or a cell that reads
  the first eight words of the jump target immediately before the `J`.

⚠️ **The repository already contained enough to predict this** -- `§G1` in
`RUNSHEET.md` exists to ask whether the image is already staged there, and
`§H1a`'s warning says an image at the wrong address plus `J 80500000` boots the
vendor kernel the loader has already staged. It was still assumed rather than
read.

---

## §10 — the exception path, and what a fault costs a payload

**Read out of this unit's own stage 2, 2026-08-25, and put through an
adversarial pass that broke nine of the first draft's claims.** Nothing here is
measured on the device; the cell that would make it a measurement is
`DW 80000080 32` at the prompt, which is read-only and costs nothing.

### A fault the loader does not handle hangs the board forever

`do_reserved` at **`0x80400BE8`**:

```
80400be8:  addiu sp,sp,-24          <- the FAULTING code's sp
80400bec:  sw    ra,16(sp)
80400bf0:  move  v0,a0              <- the FAULTING code's a0, kept as pt_regs*
80400bf4:  mfc0  a1,c0_cause
80400bf8:  mfc0  a2,c0_epc
80400bfc:  lui   a0,0x8041
80400c00:  lw    a3,148(v0)         <- dereferences that a0
80400c04:  jal   0x8040781c         ; prom_printf "cp0_cause=%X, cp0_epc=%X, ra=%X"
80400c0c:  lui   a0,0x8041
80400c10:  jal   0x8040781c         ; prom_printf "Undefined Exception happen."
80400c18:  j     0x80400c18         <- BRANCH TO ITSELF
80400c1c:  nop
```

`0x08100306` → `imm << 2 = 0x400C18`, `(PC+4)[31:28] = 8` → `0x80400C18`, the
address of the instruction itself. The exception entry has already pushed the
KU/IE stack so `IEc` is 0, and the watchdog is not armed — a raw four-byte search
for `b800311c` finds it in neither stage 1, stage 1.5 nor stage 2 outside the two
deliberate reboots, and the control for that zero is that the same search finds
`b8001050` and `b8001008` in stage 1.5's register table. **Nothing recovers it.
One fault costs one power cycle.**

**Neither string ends in `\n`** (NUL at `0xA52B` and `0xA547`), so what reaches
the wire is one unterminated line followed by permanent silence. A capture tool
that flushes on newline would show the board going quiet with no message at all.

### The table this document used to name was the wrong table

`0x8040A5C0` is **not** the exception dispatch table. It is
`BootStateEvent[3][8]` — 24 function pointers, the TFTP/ARP boot state machine,
indexed `(bootState * 8 + bootEvent)` at `0x80402108`–`0x80402130` and again at
`0x80402310`. The identification has a control that a generic pointer table would
not pass: the vendor source has two deliberate asymmetries between rows 1 and 2
(`setTFTP_RRQ` ↔ `errorTFTP`), and the binary reproduces both, 24 of 24 slots.

The real table is **`exception_handlers[32]` at `0x8040EB40`**, in BSS, with one
writer (`set_except_vector` at `0x80400BD0`, no bounds check) and one reader (the
vector itself at `0x8040055C`). After boot: `[0] = 0x80400580` (IRQ, returns via
`rfe`), `[23] = 0x804007C0` (Watch, returns), and the other thirty =
`0x80400BE8`. So **two ExcCodes are survivable and neither is one a probe will
provoke** — `J <addr>` clears `IE` and zeroes `GIMR0` before entering a payload.

### This loader was not built from either GPL drop this project holds

The vendor's `do_reserved`, byte-identical in `saturn49-wecb` and `wecb-vz-gpl`
at `bootcode/boot/init/irq.c:210`, is:

```c
asmlinkage void do_reserved(struct pt_regs *regs)
{
	int i;
	prom_printf("Undefined Exception happen.");
	for(;;);
	/*Just hang here.*/
}
```

One call, no CP0 reads. The shipped `0x80400BE8` has two `prom_printf`s, two
`mfc0`s and a `pt_regs` load — and `do_watch`, whose string is in the binary,
appears in neither tree. **The string match is evidence of provenance; it is not
evidence that the C on screen is the C that was compiled**, and every argument in
this repository of the form *"the vendor source says why"* has to say which half
it is leaning on.

### `boot.img` and `nfjrom` write from `0x80000000` upward

The name compare against `0x8040A6A8` reaches `0x80401250`, which stores
`0x80000000` into both the `LOADADDR` global (`0x8040D3A8`) and the running TFTP
write pointer (`0x8040DD10`); `0x80401A10`'s memcpy walks up from there. So such
an upload overwrites the UTLB refill vector **and** the general exception vector
while it is in progress. The do-not-type list already carried both names for a
different reason; this is the instruction-level one.
