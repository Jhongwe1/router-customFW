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
  line, so it always reads a multiple of 16 bytes.
- **`DW` forces the address into KSEG0** when bit 31 is clear
  (`if ((signed)src >= 0) src |= 0x80000000`) and rounds up to 4. `DB` does
  neither. So `DB` and `DW` also disagree about what an address means.
- `DW` is the only one of the four that guards `argv[0]` against NULL. It prints
  `Wrong argument number!` and survives.

### The reset R4 needs, and it is already a command

`J BFC00000`. **(A.)**

```
804092d4   lui   v0,0xbfc0
804092d8   bne   v1,v0,normal_jump
804092e4   ori   v0,v0,0x311c      ; 0xB800311C
804092e8   sw    zero,0(v0)        ; WDTCNR = 0
804092ec   j     0x804092ec        ; spin until it bites
```

Interrupts are already masked two instructions earlier (`GIMR0 = 0`, `IE`
cleared), so nothing can leave that spin except the watchdog.

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
| **4** | a `DW` length argument is decimal, not hex | asking for `10` and getting 16 words | read-only |
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
`0x8040A4E0`–`0x8040A5B0`, above a 16-entry dispatch table at `0x8040A5C0`
pointing into `0x80400DA0`–`0x80401BDC`. **(A.)**

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
"write my handler to `0x80000180` and make the I-cache see it" is replacing
something, not filling a vacuum. Where those vectors live and whether
`Status.BEV` is 0 when the prompt is up has not been traced.

### A hardware condition that disables image checking

`check_image()` begins by reading the global `0x8040DBA4` and returning 0 —
"no image" — when it is 1. **(A.)** B calls it `gCHKKEY_HIT`. The only writer is
`0x804082B4`, which reads `0xB8002014`, tests bit 24, then compares the top byte
of `0xB8002000` against its argument. That is the UART path, so the flag looks
like *the operator pressed a key*, but the register addresses have not been
confirmed against D and the argument has not been traced. **Inferred, and worth
fifteen minutes before R8**, because a global that makes the loader declare
every image bad is a rescue path and possibly a hazard.
