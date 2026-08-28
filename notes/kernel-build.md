# How rlxfw's own kernel is built, wrapped and reached

**Owner of: which toolchain builds rlxfw's kernel, what its configuration is
allowed to differ by, what the loadable image is made of, what the first boot
mounts, and how far a kernel for this board can be run at the desk.**
Written 2026-08-28, desk, no power, no device reading. **§1.4 and §6 were
rewritten the same day**, because `R3-4` measured what they had asserted and
both were wrong in the same direction: a span mistaken for its content, and a
mechanism named without being tested. The originals are quoted in place.

Everything here is 讀 or 量-on-this-desk — read out of the vendor's own sources
and binaries, or measured by running them here. **量 in this file never means
what `SPEC.md` §0 means by it**; nothing below was measured on the device.
Where a row needs that mark it goes to `SPEC.md` as 讀.

> **Refutation conditions, written before the results.**
>
> **K1** — *"`rsdk-1.3.6-4181` is the right toolchain for this kernel"* is
> refuted by it failing to build an object of the `R3` configuration, by the
> unexplained load-use violations in its `vmlinux` turning out to be
> compiler output on an executed path, or by a boot failure whose signature is a
> load-use hazard at a compiler-generated site. It is **not** refuted by the
> shipped image being a different toolchain generation.
>
> **K2** — *"the `-march` partition, not the toolchain generation, is what moves
> the load-delay padding"* is refuted by the third-column build — same generation
> as the 4181 build, same `-march` as the 1.5.5 build — landing beside the 4181
> build rather than beside the 1.5.5 one. §1.
>
> **K3** — *"some `arch/rlx` hand-written assembly relies on gas to fill a load
> delay slot"* is a claim that needs a detector that can fail in **both**
> directions, and the first version of the detector did not: it counted
> instructions, and at `-march=4181` gas emits `lw nop jr addu` where at
> `-march=5281` it emits `lw jr addu nop` — four instructions and one `nop`
> either way. §2 carries both controls, and the count is not the metric.
>
> **K4** — *"the image pipeline is understood"* is refuted by the pipeline failing
> to reproduce the drop's own `vmlinux-stripped` and `vmlinux_img`, which the
> drop ships beside the `vmlinux.elf` they came from. §3.
>
> **K5** — *"a desk execution channel exists"* is refuted by **this unit's own
> kernel** — the one measured booting on the silicon on 2026-08-24 — failing in
> the channel. A channel that cannot run the kernel that works is not measuring
> my kernel. §5.
>
> **K6** — *"the 21 differences between the vendor's template and the built
> `.config` are derived by kconfig with no input from me"* is refuted by any of
> them moving when the input argues with it. The experiment argues with all 21
> at once and needs a **negative control in the same run**, or "nothing moved"
> is also what a broken harness prints. §6.5.
>
> **K7** — *"`-fno-if-conversion` is the narrowest change that reaches 0"* is
> refuted by `-fno-if-conversion2` removing a conditional move `-fno-if-conversion`
> leaves, or by either of them leaving a violation. §7.2.
>
> **K8** — *"this build recipe is the recipe"* is refuted by a build from the
> pinned drop plus the declared inputs differing from the one already on disk in
> anything but its build stamp. §8.

---

## 1. Decision A — `rsdk-1.3.6-4181`, through its own wrapper

This fills the half of `TC-05` that was left blank. It is a decision about the
**kernel**; userspace is `R7`'s and is not decided here.

| | reason | mark |
|---|---|---|
| 1 | It is the **only wrapper on hand that accepts `-march=4181`**, and `boards/rtl8196e/config.in` is `ARCH_CPU_RLX4181=y` | 讀 `TC-14` |
| 2 | `{4180, 4181, 5181, mips1}` is the side that exposes the load delay slot and gets the padding. One `vmlinux`, one source, through `rsdk-1.5.5`'s wrapper: **21,185** load-use violations | 讀 `TC-15` |
| 3 | The drop's own top-level `.config` selects this release for this board | 讀 `TC-17` |
| 4 | It is one of two toolchains that has linked a **complete `vmlinux`** for this board, rc=0 — and the other is the one row 2 disqualifies | 讀 `TC-16` |

🔴 **The objection that does not carry over, written down so the decision is not
defended with it.** The reason to fear `rsdk-1.5.5` driving `-march=4181` is that
its uClibc and crt are 5281-built and put three load-use violations into every
program's entry path (`notes/rebuild-vs-shipped.md` §4). **A kernel links
neither**: 量, the 4181 `vmlinux` resolves `__ashldi3`, `__ashrdi3` and
`__lshrdi3` from `arch/rlx/lib/`'s own C files, no Makefile in the link path
mentions `-lgcc`, and a scan for uClibc symbols returns **0**. That
objection is about userspace.

**What is left against the 1.5.5-at-4181 route, and it is enough**: its flag set
is a **reconstruction (推)** read out of the 1.5.5 wrapper's own log with `5281`
substituted, not a reading of a release. If `R3` does not boot, the vendor's own
(toolchain, board, config) triple leaves the code generator out of the suspect
list; a reconstructed toolchain puts it back in. On a gate whose scarce resource
is power cycles, that is the whole argument.

### 1.1 🔴 The control that separates `-march` from the toolchain generation

`notes/vendor-toolchains.md` §4 recorded the `rsdk-1.3.6-5281` column as *not
run* — *"Cheap, and not done."* 量 2026-08-28: **it had been run.**
`vmlinux-136-5281.elf`, 3,207,595 bytes, entry `0x800035a0`, sha256
`47f03df4…`, was linked at 05:57 on 2026-08-28 with `ctl-clean.log`,
`ctl-136-5281.log` and `ctl-vm-136-5281.log` beside it; the note that calls it
not run was committed at 06:45 the same morning. **The build existed and nobody
read it.** That is a different defect from not doing the work, and it is the one
this section repairs.

**The control is only single-variable if the `.config` did not move between the 04:44 build and the 05:57 one.** 量: `config-before-ctl.snapshot` and the tree's `.config` carry **767 symbols each and differ on none**. Same source, same configuration, one flag.

Read with the same tool at the same bound, the three published rows reproduce
exactly — that is the control on the method — and the new row lands where `K2`
said it would not have to.

🔴 **The table itself lives in `notes/vendor-toolchains.md` §5, which owns
`TC-15`, and is not repeated here.** What it settles for *this decision* is the
two single-variable deltas:

* **`-march` alone**, toolchain generation held at 1.3.6: **4 → 20,201**
  violations.
* **generation alone**, `-march` held at 5281: **20,201 → 21,185**, +4.9 %.

**So reason 2 of Decision A is about the `-march` and not about the vintage of
the compiler** — which matters, because Decision A picks the *older* generation
and the shipped firmware was built by the newer one. `K2` is satisfied in the
direction it was written for.

### 1.2 🔴 The four violations are one shape, and it is a shape with an open question behind it

They were recorded as *"four sites in 61,568 loads and nothing here says what
they are."* 量: **all four are a conditional move whose destination is the
register the load just wrote.**

| address | words | symbol | on `R3`'s boot path? |
|---|---|---|---|
| `0x800142CC` | `lw v0,-25112(t2)` / `movz v0,s0,a3` | `__add_preferred_console` | **yes** — 量: this build's `CONFIG_CMDLINE` is `"console=ttyS0,38400 root=/dev/mtdblock1"`, so `console_setup()` runs and calls it |
| `0x8008F978` | `lw v0,40(sp)` / `movn v0,t6,a3` | `__blockdev_direct_IO` | no |
| `0x8008FA08` | `lw a1,40(sp)` / `movn a1,t6,a3` | `__blockdev_direct_IO` | no |
| `0x80092DD8` | `lw a2,92(sp)` / `movn a2,a1,v1` | `load_elf_binary` | **yes** — every `execve` |
| `0x8015EFF8` 🆕 | `lw a1,5136(sp)` / `movz a1,zero,a2` | `rtl8192cd_ioctl` | no |

The fifth is outside the published window and inside a wider one; §1.4.

**`hazlint` is not wrong here, it is conservative, and it says so in its own
source**: *"rd is architecturally preserved rather than read, but a checker that
assumed so would be assuming. Counted as read."* So these are that policy firing.

🔴 **Whether the policy is right on this core is not a style question.** With a
write-enable implementation of `movz`/`movn` — the cheap and usual one — `rd` is
not read and the sequence is correct on any core. With a read-select-write
implementation, the move reads the **stale** `rd` in the delay slot and, on the
branch where the condition is false, writes the pre-load value back over the
loaded one. Silent, wrong, no fault. **This project has never measured which one
this die has**; `C-12` asks whether `movz`/`movn` exist at all, not how they
read.

🔴 **And nothing that has ever run on this die exercises the pattern.** 量 — and the adversarial pass widened this from the 56 % window to everything, because *"nothing that has run on this die"* cannot be read off 56 % of one image:

| artefact | loads | `movz`+`movn` | **conditional move in a load delay slot, rd = the loaded register** |
|---|---:|---:|---:|
| 1.3.6 at 4181 | 61,567 | 1,495 | **4** |
| 1.3.6 at 5281 | 64,729 | 1,523 | 33 |
| 1.5.5 at 5281 | 65,740 | 1,526 | 27 |
| **this unit's kernel** | 63,298 | **1,574** | **0** |
| **this unit's kernel, the WHOLE 3,374,772 bytes** | **143,555** | **3,183** | **0** |
| this unit's shipped `boa` | 24,879 | 141 | **0** |
| this unit's shipped `busybox` | 12,605 | 213 | **0** |
| this unit's loader (`stage2.bin`, `K4`) | 1,474 | 18 | **0** |

The shipped firmware has **more** conditional moves than my build and places
**none** of them there. So the sites my chosen toolchain produces would be the
first code of this shape to execute on this silicon — and two of them are on
`R3`'s own path.

⚠️ **The whole-image row reads the MIPS16 band as 4-byte words, so that part of it is not a valid decoding** — a zero there is neither evidence for nor against. The 32-bit spans are the reading, and they are still ~180,000 loads.

At the 4181 build's rate (4 in 61,567) the expected count over the shipped kernel's 143,555 loads alone is **9.3**, and `P(0) = e^-9.3 ≈ 9e-5`. ⚠️ That null treats two different code bases as one population and they are not, so it is an order-of-magnitude statement rather than a test. What makes it worth acting on is not the count: it is that the consequence is silent and the cost of removing it is small.

**Consequence, and it is `R3-4`'s**: the image `R3` uploads must pass `hazlint`
with **0 violations**, the same gate `probe2` and `probe3` passed. Today's kernel
does not. The narrowest change that reaches zero is measured there, not guessed
here.

### 1.3 The new carried-forward item this produces

**`TC-h` — does `movz`/`movn` read `rd` in the load delay slot on this die?**
One instruction pair under `R1a`'s bare-metal harness settles it:
`lw $2,X` / `movz $2,$3,$4` with `$4 != 0`, then read `$2`. If `$2` holds the
loaded value the implementation is write-enable and `hazlint`'s conservatism can
be relaxed with a reason; if it holds the pre-load value, **every build of this
kernel by this toolchain has four latent silent-corruption sites**. Owned by
`R1a`, and it rides the same payload as `C-12`.

### 1.4 🔄 What `hazlint` was not looking at was **0.62 %** of the text, not 40 %

**Written 2026-08-28 and corrected the same day.** The first version of this
section said the unscanned region was *"975,904 bytes, 40.2 % of `.text`"*. That
number is a **span**, and the content inside it is two orders of magnitude
smaller. The original table is kept below because negative results stay in
place.

> **Original.** The published window stops at `0x80158000` because that is the
> bound that serves all three builds below their lowest `[MIPS16]` symbol.
>
> | span | bytes | loads | violations |
> |---|---:|---:|---:|
> | published window `[0x80000000, 0x80158000)` | 1,409,024 | 61,568 | 4 |
> | widened to the first MIPS16 symbol `[0x80000000, 0x8016c844)` | 1,493,060 | 65,048 | **5** |
> | `.init.text` — the boot path | 81,268 | 2,297 | **0** |
> | `.exit.text` | 4,688 | 157 | 0 |
> | **not scanned**: the MIPS16 band `[0x8016c844, 0x8025ac64]` | **975,904** | — | — |

🔴 **量: the band holds 39 MIPS16 functions totalling 15,050 bytes** — 1.54 % of
the span they are scattered across, and **0.62 % of `.text`**. And the bound is
set by **one** of them: `rtl_MulticastRxCheck`, 714 bytes at `0x8016C844`,
sitting **947,878 bytes** below the next MIPS16 function. Bounding the scan
below the first `[MIPS16]` symbol threw away nine hundred kilobytes of ordinary
32-bit code to avoid seven hundred bytes that could not be read.

**So `TC-f` is not "make `--range` work". It is "stop using a bound".** The
symbol table says where every MIPS16 function is (`st_other == STO_MIPS16`), so
`hazlint` 1.4 cuts them out **by name** and prints the list. Two more classes of
non-code came out with it, both found by removing the bound rather than by
looking for them:

* **`.rodata` was inside the scan.** A linked kernel has one executable
  `PT_LOAD` and the linker puts every read-only section in it, so a
  segment-based scan reads `__ex_table`, `.rodata` and `__param` as
  instructions. 量: two words in `.rodata` (`0x80269308`, `0x8026DA04`) decode
  as `jalx 0x80000000` and tripped the MIPS16 refusal on a kernel with no MIPS16
  anywhere near them. `hazlint` 1.4 scans **executable sections** and falls back
  to `PT_LOAD` only for a stripped image that has none.
* **`sys_call_table` is 2,656 bytes of function pointers declared `STT_OBJECT`
  and linked into `.text`.** Section flags cannot catch that one. Two of its
  entries decoded as a register jump with a load in its delay slot, and they
  were the tool's only two unresolved successors on every build measured today.
  Symbols declared as data are excised the same way, and `K16` is the control —
  with the negative half, that the same bytes declared `STT_FUNC` are still
  scanned.
* **The padding between two MIPS16 functions** is not 32-bit code either. 量:
  the 50 bytes between `interrupt_dsr_rx` and `interrupt_isr` decoded as
  `lb ra,17368(at)` / `lwc3 $31,-1(ra)` and were reported as a violation. The
  rule that removes them carries no threshold: a gap is excised when the
  function on each side is MIPS16 **and no other `STT_FUNC` starts inside it**.
  20 such gaps, 408 bytes.

| the 1.3.6@4181 build, read three ways | scanned | loads | violations |
|---|---:|---:|---:|
| the old bound `[0x80000000, 0x8016c844)` | 1,493,060 | 65,048 | 5 |
| `hazlint` 1.4, executable sections, excisions by name | **2,522,692** | **109,621** | **7** |
| excised and named: 39 MIPS16 fns (15,050) + 20 gaps (406) + `sys_call_table` (2,656) + 12 B of 4-byte rounding | 18,124 | — | — |
| the executable sections in total (`.text` + `.iram` + `.init.text` + `.exit.text`) | 2,540,816 | — | — |

🔄 **Coverage of the executable sections went from 58.8 % to 99.29 %,
and the two extra violations are real** — `0x801DE7EC` and `0x801EE174`, the
same `movz`-after-load shape as the other five. The old figure was hiding them.

⚠️ **What is still not covered is now a list rather than a bound**: 39 named
functions, 20 named gaps and one named data table, printed in full on every run
— **0.71 % of the executable sections**. A four-byte scanner cannot read
MIPS16 and this one does not pretend to.

🔴 **And the excision buys the coverage at a price this file has to state**:
cutting a span in two creates a seam, and a load at word 0 of a new span has
nothing before it that this file can see. 量 on the `R3` kernel: **8 such
loads**, all at span heads created by the MIPS16 cuts, reported by `hazlint` as
*notes — a stated limit, not a finding*. They are not violations and they are
not cleared either: if the linker put a branch immediately before one, that load
is in a delay slot and has a second successor nobody has checked. **"0 violations"
means 0 among the successors this scan can resolve, and 8 it declines to rule on.**

---

## 2. `TC-g` — which `arch/rlx` assembly relies on the assembler

`asm/stackframe.h` sets `.set reorder` outright and seven of the **eighteen** `.S`
files under `arch/rlx` carry no `.set` directive at all, so they are assembled in
gas's default reorder mode. 🔄 **2026-08-28: seventeen was an undercount and
the reason is §10.** `find arch/rlx -name '*.S'` does not follow `arch/rlx/bsp`,
which is a symlink; `find -L` gives **18**. The eighteenth is
`arch/rlx/bsp/vmlinux.lds.S`, a **linker script**, correctly outside `TC-g`'s
scope — but it was outside it because nobody had seen it, which is a different
thing from being excluded. **No count in the table below moves**: it is not
assembly, gas never sees it, and it carries no `.set`. **The question is not which files are in that mode.
It is which of them would carry a live hazard if the assembler were not fixing
it**, and that is a measurement.

**Method.** `notes/vendor-toolchains.md` §5's third reading established that both
generations of gas carry a per-core load-delay model and act on it under
`.set reorder`: at `-march=4181` the `nop` is inserted, at `-march=5281` it is
not. So each file is preprocessed once and assembled twice, changing only that,
and the emitted instruction sequences are compared. Then `hazlint` reads both
objects.

**Controls, and the first version of the detector failed one of them.** `P` is a
`.set reorder` hazard and must differ; `N` is the same hazard under
`.set noreorder` and must not. 🔴 The first detector counted instructions, and `P`
came back identical — because at 4181 gas emits `lw nop jr addu` and at 5281
`lw jr addu nop`: **four instructions and one `nop` either way.** The count is
blind to the thing being measured. With the sequence compared instead, `P`
differs and `N` does not.

| `arch/rlx` file | gas fills the slot? | live load-use hazards without it |
|---|---|---:|
| `kernel/entry.S` | **yes** | **5** |
| `lib/strlen_user.S` | **yes** | **2** |
| `lib/strnlen_user.S` | **yes** | **2** |
| `kernel/genex.S` | **yes** | **1** |
| `kernel/relocate_kernel.S` | **yes** | 1 — ⚠️ **not built for this board**: `CONFIG_KEXEC=n` and neither `relocate_kernel.o` nor `machine_kexec.o` exists in the tree |
| `lib/strncpy_user.S` | **yes** | **1** |
| `kernel/scall32-o32.S` | yes (a `nop`; offsets shift) | 0 |
| `kernel/head.S`, `kernel/rlx-switch.S`, `lib/memcpy.S`, `lib/memcpy-inatomic.S`, `lib/memset.S`, `lib/csum_partial.S`, `mm/imem-dmem.S`, `mm/tlbex-fault.S` | no | 0 |
| `fw/lib/call_o32.S` | **not assembled** standalone — it needs a constant this path does not supply, and it is not in this board's build | — |

🔴 **Eleven load-use hazards in hand-written kernel assembly that this board actually builds are prevented by the assembler and not by the author** — five in the interrupt/exception return path, one in the general exception vector, five in the user-copy routines. **No compiler flag would fix them: there is no compiler in that path.** 🔄 **The first count was twelve**, and the adversarial pass took one away: `relocate_kernel.S`'s hazard is real but `CONFIG_KEXEC=n`, so the file is not in this build. Kept in the table, marked, rather than deleted.

🔴 **And they are not `hazlint`'s conservatism — they are textbook.** 量, the instruction pairs:

* `genex.S`: **`lw k0,0(k0)` / `jr k0`** — the general exception dispatcher loads the vector address and jumps through it in the very next instruction. Without the assembler's `nop` this kernel would jump to `k0`'s **previous** value on every exception.
* `entry.S`: `lw t0,168(sp)` / `andi t0,t0,0x8`; `lw t8,156(sp)` / `mtlo t8`; `lw t8,152(sp)` / `mthi t8`; `lw a2,8(gp)` / `andi t0,a2,0xffef`, twice.
* `strlen_user.S` / `strnlen_user.S` / `strncpy_user.S`: `lw v0,24(gp)` / `and v0,v0,a0` — the user-address mask — and `lb t0,0(v0)` / `bne t0,zero,…`, the loop test on the byte just loaded.

None of these is a conditional move and none depends on `hazlint`'s `movz` policy.

**Independent confirmation, and it was free.** The scratch tree on disk was last
built with `rsdk-1.3.6-5281` (the §1.1 control). `hazlint` over the objects that
build actually produced reports `entry.o` **5**, `genex.o` **1**,
`strlen_user.o` **2**, `strnlen_user.o` **2**, `strncpy_user.o` **1** — every
number this experiment predicted, from a build it did not touch.

⚠️ **`scall32-o32.S` differs without a hazard behind it**: gas emits an extra
`nop` and every later offset shifts, yet `hazlint` reads 0 violations at both
`-march` values. Recorded as *differs, no hazard exposed*, not as *relies*.

### 2.1 The trap this sits next to

`TC-14` measured that **`gcc -c foo.S` does not pass `-march` through to `as`**;
the driver hands the assembler its own default. For `rsdk-1.3.6` that default is
`lx4180`, which is on the padded side, so the real kernel build gets those eleven
`nop`s. **That safety is incidental and it should be asserted rather than
assumed.** The check is one `hazlint` pass over the objects the build produced,
and it is cheap enough to be a build step.

🔄 **2026-08-29: asserted.** `tools/hazlint-objs.py`, `RUNSHEET` `P2`, on all
four `R3` trees — **0 violations in 1,607–1,685 loads across 59–60 objects**,
and the same six sources re-assembled from the build's own recorded command
line with `-Wa,-march=5281` appended carry **11**, split 5/1/2/2/1/0 exactly as
this table predicts. §14. ⚠️ And the check enumerates with `find -L`: plain
`find` misses the six BSP objects (§10), which is where `bsp_swcore_init` is.

---

## 3. The image: what `J 80500000` actually receives

Read out of `boards/rtl8196e/Makefile` and `linux-2.6.30/rtkload/Makefile`:

    vmlinux --strip--> vmlinux-stripped --objcopy -Obinary--> vmlinux_img
            --lzma e--> vmlinux_img.gz  --cvimg vmlinuxhdr--> (+8-byte header)
            --objcopy --add-section .vmlinux--> vmlinux_img.o
            --ld -T ld.script @ LOAD_START_ADDR--> memload-full
            --objcopy -Obinary--> nfjrom
            --cvimg linux-ro--> linux.bin

**`nfjrom` is what goes to RAM and gets jumped to. `linux.bin` is `nfjrom` plus a
flash header, and this project does not write flash.**

### 3.1 The `cr6c` header, and the checksum rule evaluated for the first time

`C-4` records, out of this unit's own loader code, that `check_image()` is a
signature test plus *"a 16-bit sum over the RAM copy that must be zero"*. That
had never been evaluated on an image. 量, on two independent images:

| | signature | startAddr | flash offset | length | sum16 over payload |
|---|---|---|---|---:|---|
| drop `image/linux.bin` | `cr6c` | `0x80500000` | `0x00030000` | 854,018 | **0x0000** |
| this unit, flash `0x060000` | `cr6c` | `0x80500000` | `0x00060000` | 987,138 | **0x0000** |

**Control**: one bit flipped in either payload gives `0xFFFF`. The zero is a
reading, not an arithmetic identity.

So the header is **16 bytes** — signature, load address, flash offset, payload
length — and the payload is `nfjrom` plus a 2-byte tail chosen to make the
big-endian 16-bit sum zero. `r0-vendor-kernel.bin`, the 987,138 bytes `R0`
uploaded and jumped into, is exactly that payload and it sums to zero.

⚠️ **The drop's flash offset is `0x00030000` and this unit's is `0x00060000`.**
The drop's layout is already known not to be this unit's, which is one of the
reasons §4 does not put an MTD map on the first boot.

### 3.2 The self-extracting wrapper, unwrapped on two images

讀 `rtkload/ld.script.in` (the `.vmlinux` section is 1024-aligned),
`rtkload/misc.c:304-305` (two 32-bit words in front: `pending_len`, then
`kernelStartAddr`; the LZMA stream starts at +8) and `rtkload/hfload.h:30`
(`UNCOMPRESS_OUT = 0x80000000`).

| image | `__vmlinux_start` | `pending_len` | `kernelStartAddr` | decompresses to | matches |
|---|---|---:|---|---:|---|
| drop `image/nfjrom` | file `0x2C00` | 1 | `0x80003600` | 2,953,660 | `rtkload/vmlinux_img`, **byte-identical** |
| this unit's `r0-vendor-kernel.bin` | file `0x2800` | 2 | `0x80003440` | 3,374,772 | `vmlinux-rederived.bin`, **byte-identical** |

**Control on the locator**: the same 1024-aligned LZMA scan over `stage2.bin`,
which has no compressed kernel in it, returns **0** candidates.

### 3.3 The pipeline reproduces the vendor's own intermediates — 🔄 and, since 2026-08-29, its output

The drop left `rtkload/vmlinux-stripped` (3,001,168) and `rtkload/vmlinux_img`
(2,953,660) beside the `image/vmlinux.elf` (3,441,133) they came from, so stages
1 and 2 have a vendor-made reference. 量, running the vendor's own `strip` and
`objcopy` from a scratch directory under `tools/vendor-tripwire.sh`:

* `vmlinux-stripped` — **byte-identical to the vendor's**
* `vmlinux_img` — **byte-identical to the vendor's**

`K4` is satisfied. My own kernel through the same two stages: 2,894,792 stripped,
**2,846,948** as a flat image (sha256 `a469c52e…`).

🔄 **2026-08-29: stages 3–6 as well, and the end of the pipeline is byte-identical.**
`nfjrom` rebuilt from the drop's own `vmlinux.elf` is **854,016 bytes, sha256
`5cc8d61d4b4e8914`** — the shipped file, to the byte. `memload-full` differs by
492 bytes and every one of them is DWARF carrying a build path; `linux.bin`
differs by **one byte**, the signature, and this drop's `cvimg` cannot produce
the right one. §13. `K4` is now satisfied for the whole pipeline rather than
for its first two stages, and `TC-d`'s image half is closed.

### 3.4 The ceiling, and it is arithmetic

The image is entered at `0x80500000` and decompresses to `0x80000000`, so the
decompressed image must end below the image it is being read from:
**5,242,880 bytes.**

| | decompressed | headroom | used |
|---|---:|---:|---:|
| this unit | 3,374,772 | 1,868,108 | 64.4 % |
| the drop's own | 2,953,660 | 2,289,220 | 56.3 % |
| **mine, 1.3.6@4181** | **2,846,948** | **2,395,932** | **54.3 %** |

If an initramfs ever exceeds that, the answer is
`LOAD_START_ADDR = 0x80A00000`, which `rtkload/Makefile` already supports for
other boards and which `G0` has already probed on this device.

🔄 **2026-08-29: the arithmetic has a second source and it is Realtek's.**
`rtkload/Makefile:229` runs `cvimg size_chk vmlinux_img $(LOAD_START_ADDR)`,
which prints *Image decompress end addr* and *Available size*. 量 on four
builds: `0x0022ee44` = 2,289,220 for the drop's kernel, `0x001b0400` =
1,770,496 for `quiet`/`quietm`, `0x0019e400` = 1,696,768 for `loud`/`loudm` —
the same numbers §11.6 computes from the program headers, by a route with no
code in common. §13.4. **The `mine, 1.3.6@4181` row above is the pre-`R3-4`
build and is kept as written**; the four current images are in §13.3.

---

## 4. Decision B — the first boot mounts an initramfs from this unit's own userspace

1. 🔴 **Safety dominates on a one-device project.** 🔄 **But not for the reason
   first written here.** This said *"an initramfs boot never instantiates an MTD
   partition map"*, and 讀 the built `.config` says otherwise: `CONFIG_MTD=y`,
   `CONFIG_MTD_PARTITIONS=y`, `CONFIG_RTL_FLASH_MAPPING_ENABLE=y`, and `drivers/mtd/
   maps/rtl819x_flash.o` links with a `module_init` that calls `add_mtd_partitions()`
   at `device_initcall` **whatever root is**. The map is registered; `mtdblock0` even
   spans `0x000000-0x130000`, which covers both regions `CLAUDE.md` forbids. **What
   the initramfs actually buys is that nothing MOUNTS it and the image has no
   `mtdblock` nodes to open it with** — a weaker claim, and still the right
   decision. The flash-root route would need me to author the map, The flash-root route needs me to author
   one, and `CLAUDE.md`'s two forbidden regions — the loader at
   `0x000000–0x005FFF` and `H601` at `0x006000–0x007FFF` — are inside the part a
   wrong map covers. §3.1 shows the drop's own offset is not this unit's, so the
   map would be new work.
2. 讀: it is **the vendor's own supported path**.
   `boards/rtl8196e/Makefile`'s header is *"Build instructions for Realtek RLXOCP
   with initramfs"*, `rtkload/Makefile` branches on `CONFIG_BLK_DEV_INITRD`, and
   `usr/gen_init_cpio.c` and `CONFIG_INITRAMFS_SOURCE` are both in the tree.
3. **It keeps userspace as a controlled variable rather than removing it.** The
   contents are this unit's own binaries, unmodified.
4. The plan's stop-loss for this gate is *swap to an initramfs to halve the
   variables*. Starting there spends the halving; what is held in reserve becomes
   the flash root, which is the closer-to-vendor direction and the better second
   experiment.

**It fits, with room.** 量, the minimum set and its dependencies read out of the
binary itself — `bin/busybox` is dynamically linked, `NEEDED` = `libc.so.0` and
`libgcc_s.so.1`, interpreter `/lib/ld-uClibc.so.0`:

| | bytes |
|---|---:|
| `bin/busybox` | 273,332 |
| `lib/libuClibc-0.9.30.3.so` | 205,452 |
| `lib/libgcc_s.so.1` | 80,156 |
| `lib/ld-uClibc-0.9.30.3.so` | 20,704 |
| **total** | **579,644** — 24.2 % of the headroom in §3.4 |

⚠️ **`/dev/console` has to be created by the image, and the vendor's rootfs will
not supply it.** The extracted tree holds **0** device nodes. ⚠️ And that zero is
weak on its own: `unsquashfs` run as an ordinary user cannot create device nodes,
so the count is a property of the extraction as much as of the image. Either way
the initramfs must declare `/dev/console` itself, which is what
`gen_init_cpio`'s spec-file input is for — and a kernel whose `init` has no
stdio fails in a way that reads exactly like a hang.

---

## 5. The desk execution channel, and its ceiling is measured

`qemu-system-mips` 8.2.2 has no RTL8196E machine. `malta` maps RAM at physical 0,
which is where KSEG0 `0x80000000` lands, so **loading** is plausible; the console
is not — `arch/rlx` writes UART0 at `0xB8002000` and malta's 16550 is behind an
ISA bridge. So the channel is read with an **instruction trace**, not a console.

**`-kernel` cannot be used**: malta writes its prom environment at physical
`0x2000`, inside the image, and qemu refuses with *"Some ROM regions are
overlapping"*. What works is a three-instruction stub in the `-bios` window
(`lui`/`ori`/`jr` to the image's own `kernelStartAddr`) plus
`-device loader,file=…,addr=0,force-raw=on`.

🔴 **The channel is validated on this unit's own kernel before mine goes through
it** — the one measured booting on the silicon on 2026-08-24, `ping` 2/2 at
3.6 ms:

| run | KSEG0 instructions | stops at |
|---|---:|---|
| **control** — this unit's kernel | 880 | `_imem_dmem_init` equivalent, `0x8000227C` |
| mine, 1.3.6@4181 | 880 | `_imem_dmem_init+108`, `0x8000233C` |

**Both stop at the same instruction class**, and it is a reading rather than an inference: 量, the word at the control's stopping address `0x8000227C` is `4c880000`, **opcode `0x13`**, and `[0x80002210, 0x80002310)` — the range this repository already recorded as this unit's `IMEM0FILL`/`IMEM0OFF` sequence — holds **four** such words, the same count as mine. Mine stops at `0x8000233C`, which qemu disassembles as **`lwxc1 $f0,t0(a0)`** —
opcode `0x13` read as MIPS-IV COP1X. On this Lexra core that word is **COP3**,
and qemu's 4Kc has no coprocessor there, so it raises Coprocessor Unusable into
the BEV vector, which is the empty `-bios` window. 🔴 **That is the same
mislabel `hazlint` carried until 2026-08-27** (`R1h-1`, `TC-08`): two independent
tools reading opcode `0x13` as COP1X. It is evidence about the tools, not about
the core.

**With those four COP3 words replaced by `nop` in a copy used only by the
channel — declared, because it changes what is under test by skipping the Lexra
IMEM/DMEM setup:**

| run | KSEG0 instructions | stops at |
|---|---:|---|
| **control** — this unit's kernel | 968 | a `j .` self-loop at `0x8031E218`, reached from `rtl_processBlock` |
| mine, 1.3.6@4181 | 1,003 | `bsp_setup+132` → **`bsp_machine_halt`**, `j .`, reached from `bsp_swcore_init` |

🔴 **Both halt deliberately in the board's switch-core probe**, because malta has
no RTL8196E switch. The vendor kernel calls `bsp_machine_halt` when
`bsp_swcore_init` fails — which is itself a fact about this board's bring-up
path worth carrying into `R6`.

**So the channel's reach is stated, not guessed:**

* ✅ it exercises the image format, the entry point, `head.S`, the CP0 setup, the
  early call chain and `bsp_setup` — about a thousand instructions;
* ❌ it says nothing beyond the switch-core probe: no console, no `start_kernel`,
  no userspace;
* 🔴 and the control stops at the same stage, so **a divergence before that point
  is attributable to my kernel and nothing after it is.**

⚠️ **qemu's 4Kc is a MIPS32 core with load interlocks.** It cannot reproduce a
load-delay bug, which is most of what §1 and §2 are about. *"Runs in the
emulator"* and *"runs on this silicon"* are two claims and `R1a` has not moved.

🔄 **2026-08-29: the four counts above are corrected, and the tables are kept
as written.** They are **listed program counters**, not instructions: `-d in_asm`
logs at translation time and qemu re-translates a block entered at a different
offset, so the same instruction is listed more than once. Re-derived from the
`.pcs` files this run left on disk and reproduced today: **828 / 843 / 908 /
938 distinct**, against the 880 / 880 / 968 / 1,003 printed. 🔴 **And the
control's 880 in the first table is in no log** — `c1.pcs` gives 866 listed and
828 distinct; 880 is the other run's number. The conclusion *"both stop at the
same instruction class"* is unaffected, because it rests on the stop addresses,
which reproduce exactly. **Neither could be checked from what was kept: the
logs were saved and the qemu invocation was not**, so `-cpu`, `-m` and `-d`
were all tried and none of them explains the gap. `tools/deskchan.py` prints
its full command line on every run. §15.1.

---

## 6. 🔄 The configuration. `oldconfig` was banned for a reason that is wrong, and the ban survives for a different one

**Written 2026-08-28 and rewritten the same day, because `R3-4` measured it.**
The original text is kept because negative results stay in place:

> **Original.** 量 2026-08-28: the `vmlinux` on disk differs from the board
> template on **22 symbol lines**. Nineteen are symbols `oldconfig` dropped.
> **Three are not:** `CONFIG_ARCH_CPU_SLEEP` (*not set* → `=y`),
> `CONFIG_CPU_HAS_SLEEP` (absent → `=y`), `CONFIG_PHY_EAT_40MHZ` (`=y` →
> absent). *"`yes '' | make oldconfig` answers every new prompt with the
> **default**, and for `ARCH_CPU_SLEEP` the default is `y` where the vendor
> chose `n`. So the 724-object build is not a build of the vendor's
> configuration, and a CPU sleep path is exactly the kind of thing that turns a
> first bring-up into a hang with no output."*

Four things in that paragraph are wrong and one is right.

### 6.1 There are 21 differences, not 22, and **none of them is an answered prompt**

A line diff of two `.config` files overcounts: kconfig rewrites in menu order,
so a symbol that did not move appears as a delete plus an insert. 量, symbol by
symbol: **18 dropped, 2 added, 1 changed = 21.**

🔴 **And `oldconfig` is asked nothing at all on this template**: `(NEW)` appears
**0** times. Not one of the 21 is a prompt answered with a default.

### 6.2 `< /dev/null` and `yes '' |` are the same input, so banning the string is not a control

讀 `scripts/kconfig/conf.c` in this tree, then 量:

* `oldconfig` is `conf -o` → `input_mode = ask_silent`, `sync_kconfig = 0`.
  `valid_stdin` is initialised to 1 and reassigned **only** inside
  `if (sync_kconfig)` (line 563), so `check_stdin()` never fires for
  `oldconfig` however stdin is connected. It fires for `silentoldconfig`.
* `conf_askvalue()` presets `line` to `"\n"` and then **ignores the return value
  of `fgets`** — the host compiler says so while building the tool:
  `conf.c:105: warning: ignoring return value of 'fgets'`. **EOF and an empty
  line are the same input.**
* 量, four runs from the same template: `< /dev/null`, `yes '' |`, `yes n |`,
  `yes y |` — all four produce `.config` files that differ on **0** symbol
  lines.

⚠️ **That result on its own proves nothing, because nothing was asked.** The
positive control is what makes it a measurement: six promptable symbols
(`SWAP`, `SYSCTL_SYSCALL`, `KALLSYMS`, `BUG`, `ELF_CORE`, `AIO`) were deleted
from the template so `oldconfig` had to ask. Then `yes n |` moved all six to `n`
while the other three left them at `y` — and `ARCH_CPU_SLEEP` was `y` in every
one of the four.

### 6.3 `ARCH_CPU_SLEEP` is not settable, and the vendor ships it on

`boards/rtl8196e/config.in:30`:

```
config ARCH_CPU_SLEEP
  bool
  default y
```

**No prompt string.** A promptless bool is not user-settable — `sym_is_changable()`
is false, it never appears in the menu, and its value is its default whatever any
`.config` says. So `# CONFIG_ARCH_CPU_SLEEP is not set` in the vendor's own
template is a **dead line**, and `rlxfw_defconfig` could not have changed it
either. Turning it off means editing `config.in`.

🔴 **And it does not need turning off.** `sleep` assembles to `0x42000038` on
this toolchain (量, and note `objdump` renders it `c0 0x38` — it is a Lexra
extension the disassembler does not name). Scanning three flat images for that
word:

| image | `sleep` at |
|---|---|
| **this unit's own shipped kernel** | `0x80007EA8` |
| the drop's own `nfjrom` kernel | `0x80007808` |
| mine, 1.3.6@4181, as measured that morning | `0x80007808` |
| **mine, the `R3` kernel** (flag + initramfs) | **`0x80007884`** |

One each. 🔄 **The attribution is only a reading for MY build**: that one has a
symbol table and the word sits in `cpu_idle` via `arch/rlx/kernel/process.c:55`
→ `processor.h:31`. `vmlinux-rederived.bin` is a flat decompressed binary with
**no symbol table at all**, and from a different SDK generation, so *"it is in `cpu_idle`"* there is **推**, not 讀 — what is read is that the word is present,
once, at `0x80007EA8`.

**What carries the safety claim is not the opcode, it is `R0`**: on 2026-08-24
that kernel reached a shell and answered `ping` 2/2 at 3.6 ms. A kernel that
serves a shell has gone through its idle loop. The sleep path on this silicon is
not a hypothesis about an opcode; it is a thing that has already happened.

> **K9, written now because the correction needs one.** *"`ARCH_CPU_SLEEP` does
> not need turning off"* is refuted by a bring-up that stops with no further
> output after the last message before the idle loop — which is exactly the
> failure the original text feared. `R3-8`'s capture is where that would show, and
> the ladder has to be able to tell it from a hang in `bsp_swcore_init`. If it
> happens, this section was wrong and `boards/rtl8196e/config.in` is the file to
> edit. The scan's positive control is that the
same pass found `0x4C880000` at `0x8000227C` and `0x8000233C` — the two
addresses §5 recorded as the desk channel's stopping points, reproduced by a
route with no qemu in it.

The same reasoning disposes of the other two: `CPU_HAS_SLEEP` is promptless
(`arch/rlx/Kconfig:83`, `default y if ARCH_CPU_SLEEP`), and `PHY_EAT_40MHZ` was
not *turned off* — it was **dropped**, because `CONFIG_AUTO_PCIE_PHY_SCAN=y` and
its prompt says `depends on !AUTO_PCIE_PHY_SCAN`.

### 6.4 What is right: the built `.config` is not the file that was copied in

That part stands, and it is the whole reason the check exists.
`config/setconfig:344-356` copies the template into `$LINUXDIR/.config` and then
runs `make -C $LINUXDIR oldconfig`; the two files differ on 21 symbols. A check
that read the copied-in file would pass on a build it had never looked at.
`kconfig-delta.py`'s `C6` is that mistake made on purpose, and it must fail.

### 6.5 So the mechanism, measured rather than argued

Each of the 21 was **argued with**: a `.config` was built asserting the opposite
of what the build produced for all 21 at once, and `oldconfig` was run on it.
量: **nothing moved.** `CONFIG_SWAP`, flipped in the same file as the negative
control, **did**.

| mechanism | n | evidence |
|---|--:|---|
| `dep-unmet` | 13 | this unit is the 88E model, so `depends on … && !RTL_88E_SUPPORT` is unreachable (10); `RTL_92C_SUPPORT` is absent (2); `AUTO_PCIE_PHY_SCAN=y` (1) |
| `undeclared` | 4 | no `config` block declares them anywhere the board reaches |
| `promptless` | 2 | `ARCH_CPU_SLEEP`, `CPU_HAS_SLEEP` |
| `other-board` | 1 | `RTL_ULINKER`, declared only under `boards/rtl8196eu` |
| `selected` | 1 | `rtl8192cd/Kconfig:15` selects `RTL_ODM_WLAN_DRIVER` |

### 6.6 🔴 The ban becomes real the moment rlxfw touches the config, and the fix is not the ban

量: with rlxfw's three changes in the input, `oldconfig` prints `(NEW)` **four**
times. `CONFIG_BLK_DEV_INITRD=y` makes a menu reachable, and then how stdin is
connected **does** decide symbol values.

**So the fix is not to forbid a string; it is to leave nothing to answer.**
Every symbol that menu offers is written into the input `.config`
(`config/rlxfw-kernel.delta`, the eleven `set` rules marked *pinned*), which puts
`(NEW)` back to 0. A build with no prompts cannot be changed by an answer.

`config/rlxfw-kernel.delta` is the file: baseline sha256, 14 `set` rules with a
reason each, 21 `derive` rules with a mechanism from a closed vocabulary. It
**generates** the input (`kconfig-delta.py apply`) and **checks** the output
(`… check`), on purpose — a generator and an auditor that read different files
can drift apart and both keep passing.

---

## 7. `R3-4` part two: the narrowest change that reaches `hazlint` 0, and what it cost

`R3`'s image must pass the same gate `probe2` and `probe3` passed. At the start
of the day it did not, and the honest count was not the published 5 — with the
scan fixed (§1.4) it is **7**, all one shape.

### 7.1 The compiler puts a conditional move in a delay slot and then tells the assembler not to look

量, `rsdk-1.3.6-4181`, `-Os -march=4181`, on `int f(int *p, int c, int b)
{ int v = *p; return c ? v : b; }`:

```
	.set	noreorder
	.set	nomacro
	lw	$2,0($4)
	j	$31
	movz	$2,$6,$5		#RLX4181/RLX4281:conditional move
```

Three things in five lines. The `movz` reads `$2`, which the `lw` two
instructions earlier writes. It is in the **branch delay slot**. And it is under
`.set noreorder`, so the assembler is explicitly told not to insert anything —
gas could not fix this even if it wanted to. **The comment is Realtek's own**:
they patched this gcc to emit conditional moves for RLX4181/RLX4281, and their
scheduler put one directly after the load that writes its destination.

🔴 **And gas could not have fixed it anyway, because its model has the same hole
in the other direction.** 量, four pairs assembled under `.set reorder` at
`-march=lx4181` (the padded side):

| pair | gas inserts a `nop`? |
|---|---|
| `lw $2` / `addu $2,$2,$5` — ordinary read of `rs` | **yes** |
| `lw $3` / `movz $2,$3,$5` — the move's `rs` | **yes** |
| `lw $5` / `movz $2,$3,$5` — the move's `rt` | **yes** |
| **`lw $2` / `movz $2,$3,$5` — the move's `rd`** | **NO** |

**gas's load-delay model covers `rs` and `rt` of `movz`/`movn` and not `rd`** —
and that is exactly and only the shape of all seven sites. One sentence explains
every one of them, and it is the same blind spot `hazlint` had until 2026-08-27,
in a different tool, at the opposite polarity. (`objdump` at these `-march`
values will not even name `movz`; it prints `0x65100a`.)

### 7.2 The measurement, with the cost

Three builds, identical except for `CFLAGS_KERNEL`, each from a freshly staged
tree. Conditional moves counted over exactly the bytes `hazlint` reads, by
importing `hazlint` rather than reimplementing its span construction:

| | flag | violations | `movz`+`movn` | `.text` |
|---|---|---:|---:|---:|
| **fA** | *(none)* | **7** | 2,597 | 2,427,072 |
| **fB** | `-fno-if-conversion` | **0** | **31** | 2,443,860 |
| **fC** | `+ -fno-if-conversion2` | **0** | **31** | 2,448,668 |

**The narrowest change is `-fno-if-conversion` alone, and that is a measurement
rather than a preference**: `-fno-if-conversion2` removes **no further
conditional move** and costs another 4,808 bytes. Its cost:

* **2,566 of 2,597 conditional moves gone, 98.8 %.** 31 survive — they are not
  produced by if-conversion, and none of them is in a load delay slot.
* **+16,788 bytes of `.text`, +0.69 %.** Against 1,770,496 bytes of headroom
  under the ceiling (§9), that is 0.9 % of the margin.

🔴 **It reaches every built-in object without one line of source change.**
`CFLAGS_KERNEL` is consumed at `scripts/Makefile.build:118` as
`modkern_cflags`, which lands last in `c_flags` for non-module objects. The
alternative — `arch/rlx/Makefile`'s `cflags-y` — would have been a patch to a
vendor file for the same effect.

⚠️ **What this does not do.** It removes the *sites*; it does not answer
whether they were hazards. That is `TC-h`, and it is one instruction pair on
`R1a`'s bare-metal harness. If `movz` turns out to be write-enable on this die,
the flag can be dropped with a reason. Removing them first is the cheap
direction: the consequence is silent and the cost is 0.69 % of `.text`.

---

## 8. `R3-4` part one: the configuration as a checked delta

`config/rlxfw-kernel.delta` — **35 rules for `quiet` and 37 for `loud`**, each
with a reason. §6 is why it is shaped this way; this is what it is. 🔄
**2026-08-28/29: the two extra rows carry an `@loud` variant tag** and are
listed in §11.6; a row with no tag is in both images. 量: `apply` with no
`--variant`, or with `--variant quiet`, reports **14 set + 21 derive**; with
`--variant loud`, **16 set + 21 derive**.

| | |
|---|---|
| **baseline** | `rtl819x-toolchain @ 5c9be5d9`, `boards/rtl8196e/config.linux-2.6.30.RTL8196E_88E_GW`, sha256 `44f781de…`, 26,548 bytes |
| **14 `set`** | 3 rlxfw changes (`CMDLINE`, `BLK_DEV_INITRD`, `INITRAMFS_SOURCE`) + 11 pinned so `oldconfig` has nothing to ask |
| **21 `derive`** | measured, not asserted: §6.5 |
| **the tool** | `tools/kconfig-delta.py`, **24** controls, `apply` and `check` reading the same file. 🔄 16 → 24: six from `R3-4`'s adversarial pass, and `C23`/`C24` for the variant mechanism — **`C24` caught that the command line validated a variant name while the library function fell through in silence**, which would have built the quiet image and labelled it whatever was typed |

🔴 **Three build inputs were undeclared until today, and two of them were
invisible.**

1. **`kernel/timeconst.pl`.** The build already on disk carried a one-line
   change (`defined(@val)` → `!@val`, removed from perl in 5.22; this host runs
   5.38.2) and nothing in the repository named it. Without it the build stops at
   `kernel/timeconst.h` with Error 255. Now `config/host-compat/0001-…patch`,
   applied by the build driver, which **stops** if a patch does not apply.
2. **The top-level SDK `.config`.** `arch/rlx/bsp/Makefile:10` and
   `net/rtl/fastpath/Makefile` both `include $(DIR_ROOT)/.config`. It is
   normally written by `config/mconf`, a curses program — a build input that
   exists because somebody once answered a menu. Now `config/rlxfw-sdk.config`,
   with the reason for each of the four selections that matter.
3. **The build writes into its own source tree.** `drivers/net/wireless/
   rtl8192cd/Makefile:163` regenerates `data_*.c` from `.txt` on `FORCE`, so
   `data_MAC_REG_88E.c` comes out 7,092 bytes where the drop ships 7,018.
   **Re-staging before every build is therefore required, not hygiene.**

**The control that this recipe is the recipe**: built from the pinned drop plus
the two declared inputs and the one declared patch, `.text` comes out
**byte-identical** (sha256 `e40a9f36…`) to the `vmlinux` that was already on
disk. The whole difference between the two files is the build timestamp in
`Linux version`.

---

## 9. `R3-5`: the initramfs, declared

`config/rlxfw-initramfs.tsv` — **29 entries**, every one tagged `unit` (carved
out of this device's own flash dump) or `rlxfw` (mine), and the tag is
**checked**, not trusted. `tools/mkinitramfs.py`, **23** controls — 19 → 23 on 2026-08-28/29, and the four new ones are §11.7's: the ceiling was being measured on the ELF file size.

🔴 **It was 31 until the adversarial pass, and the check that found the two
wrong ones did not exist when they were written.** The tag was verified for
`file` entries only, and 15 of the 31 were `slink`. Turning it on for every kind
immediately refused two: **`/bin/dmesg`**, tagged `unit`, is not in this device's
dump at all (50 busybox symlinks and that is not one of them) and the byte string
`dmesg` does not occur in this busybox either, so the applet is not compiled
in — it was removed; and **`/tmp`**, declared a directory tagged `unit`, is a
**symlink to `/var/tmp`** in the dump — it is now a directory of mine, with the
reason.

| | entries | file bytes |
|---|---:|---:|
| `unit` — this device's own binaries, unmodified | 24 | 579,644 |
| `rlxfw` — mine | 5 | 988 |
| **total** | **29** | **580,632** |

⚠️ **Only 4 of the 24 `unit` entries carry bytes**, and they are the 579,644.
The other 20 are directories and symlinks: the declaration says the dump has
those, and the tool checks that it does, but there is nothing to hash.

8 dirs, 5 files, 13 symlinks, 3 device nodes. The five `rlxfw` entries are
`/init`, `/tmp`, `/dev/console`, `/dev/null` and `/dev/tty`. ~~**There is no
symlink of mine left**: because `RUNSHEET` `K5` types `uname -a` and this unit's
dump has 50 busybox symlinks without that being one of them. **It is declared as
mine rather than passed off as the unit's.**~~

🔴 **2026-08-29 (`R3-7`): that passage contradicts itself in three lines** —
*there is no symlink of mine left* and *it is declared as mine* cannot both be
true — and it is the fossil of a `/bin/uname` symlink that was added for `K5`
and then removed. **What settles it is a measurement nobody took at the time**:
`uname` is not an applet in this `busybox` at all (§12.7, 量 —
`busybox uname -a` → `applet not found`, 50 applets listed), so the symlink
would have produced `applet not found` and its removal changed nothing. What
stands from the original: the declaration carries **no symlink of mine**, and
the count above is unaffected. `K5`'s command is now `cat /proc/version`.

**What it refuses to do**, and each is a control: a declared source that is not
there is an error and is never replaced with something similar (`A2`); `/init`
and `/dev/console` must be declared (`A3`, `A4` — the first because
`init/main.c:885-891` otherwise falls through to `prepare_namespace()` and
mounts the vendor's flash rootfs, the second because `init` then runs with no
stdio and it reads exactly like a hang); a source path containing whitespace is
an error, because `gen_initramfs_list.sh` builds its dependency list with
`while read type dir file perm` (`A6`).

### 9.1 The ceiling, measured on the built image

🔄 **The table below is the `quiet` variant.** §11.6 carries both columns,
and §11.7 is why the number in it moved without the image changing: the tool
was measuring `os.path.getsize(vmlinux)`.

| | bytes |
|---|---:|
| initramfs cpio, uncompressed, in **`.init.ramfs`** | 584,704 |
| `vmlinux` with it linked in | 3,968,113 |
| **the decompressed image** | **3,472,384** |
| the ceiling (§3.4) | 5,242,880 |
| **margin** | **1,770,496 — 66.2 % used** |

### 9.2 🔴 `CONFIG_PRINTK` is not set, and it takes two of the four marks with it

**Found by the adversarial pass, 2026-08-28, and it would have failed a seating on a
perfect boot.** 讀 the built `.config`: `# CONFIG_PRINTK is not set` (line 233,
beside `CONFIG_PRINTK_FUNC=y` and `CONFIG_PANIC_PRINTK=y`). `include/linux/kernel.h:271`
then makes `printk()` `static inline int __cold printk(const char *s, ...) { return 0; }`,
so every call site compiles to nothing **and its format string is dropped from the
image**. 量 on my `vmlinux`:

| string | count |
|---|---:|
| `Kernel command line` | **0** |
| `Memory: ` | **0** |
| `Linux version` | 1 — and that is `linux_banner` **as data**, what `/proc/version` reads; nothing prints it |

**Second source, and it is this device's own capture**: `bench/2026-08-24c/G6.log`
goes `start address: 0x80003440` → `Realtek WLAN driver - version 1.6` with no
banner, no command line and no memory line between them. **The vendor ships PRINTK
off, and rlxfw inherited it from the template.** What still prints at kernel stage is
`panic_printk` only — `kernel/panic.c:27`, `arch/rlx/kernel/traps.c:52` and
`arch/rlx/mm/fault.c:30` each `#define printk panic_printk` — plus the Realtek
drivers that do the same.

**Consequences, and they are not all bad.** M1 and M2′ below are struck out: they
cannot appear. `MemTotal:` was never a boot string in any configuration of this
kernel — it is a `/proc/meminfo` field (`fs/proc/meminfo.c:56`); the boot-time
line is `Memory: %luk/%luk available` (`arch/rlx/mm/init.c:301`), and that one is
gone too. **So `R3`'s D3 observable has to change**, and the two marks that survive
are exactly the two that are computed rather than constant.

⚠️ **Turning `CONFIG_PRINTK` on is a decision, not a correction, and it is not
made here.** It would add a fourth `set` rule and change every size in §7 and §9.1;
it also moves rlxfw off the vendor's configuration in the one area — the console —
where `R3-6` owns the question. Carried forward to `R3-6` with the measurement
above attached.

### 9.3 The marks the seating reads, and none of them costs a source change

`RUNSHEET` §`B5` asked for one string emitted by `arch/rlx/bsp/setup.c` before
`start_kernel`. There is a better answer that costs nothing: **two of the four
marks are computed at run time from my own artefacts, so a constant in the
vendor image cannot produce them**, and their expected values are read off my
own build at the desk.

| | mark | when | why the staged vendor image cannot produce it |
|---|---|---|---|
| **M0** | `start address: 0x80003600` | **before the kernel is entered** — `rtkload/hfload.c:114` prints it | it is read out of the image's own header at run time. This unit's staged image holds `0x80003440` (`FW-23`). ⚠️ It does **not** discriminate against the *drop's* kernel, which is also `0x80003600`; that kernel is not on this device |
| ~~**M1**~~ | ~~`Linux version …`~~ | — | 🔴 **struck out: `CONFIG_PRINTK` is not set, so it is never printed.** §9.2 |
| ~~**M2′**~~ | ~~`Kernel command line: …`~~ | — | 🔴 **struck out, same cause.** Removing `root=` is still right for the safety reason alone |
| **M4** | `rlxfw: init running, RLXFW-R3-RUNG1-OK` | after `exec /init` | 量 `P6`: 0 hits in this unit's kernel (both copies) and 0 across all 161 files of its rootfs; 1 in mine, which is the positive control |

⚠️ **M0 and M4 are the two that are not constants in the way M1 and M2′ are** —
M0 is a value read out of the image at boot, M4 is emitted by a program running.
A capture without at least one of those pairs is *unattributed*, never a pass.

---

## 10. 🔴 `grep -r` over `arch/rlx` has never seen the BSP, and the fix prescribed for it is worse than the defect

**Carried into this session as the cheap item.** `PROGRESS.md`'s carried-forward
said: *"`grep -r` over `arch/rlx` excludes the entire BSP, because
`arch/rlx/bsp` is a symlink and GNU `grep -r` does not follow those. Every
conclusion this project has drawn from a `grep -r` over `arch/rlx` should be
re-run with `-R`."*

The first sentence is true. The second is true only inside `arch/rlx`, and
applied anywhere else it fabricates findings.

### 10.1 The blind spot, and the positive control that makes the sweep a measurement

量, `rtl819x-toolchain/linux-2.6.30`:

| | |
|---|---:|
| files `grep -r arch/rlx` can reach | 321 |
| files `grep -R arch/rlx` can reach | 333 |
| **what `-r` never sees** | **13 files, 91,549 bytes — the whole BSP** |

Those 13 are `setup.c`, `prom.c`, `serial.c`, `timer.c`, `irq.c`, `pci.c`,
`kgdb.c`, `bspchip.h`, `bspcpu.h`, `bspinit.h`, `Makefile`, `vmlinux.lds.S` and
a `modules.order`. They are the board: the UART base, the memory sizing,
`bsp_setup()`, and the `while(1)` at the end of it.

🔴 **A sweep reporting "nothing moved" is a claim, so it needs a token that MUST
move.** Two:

| token | `-r` | `-R` |
|---|---:|---:|
| `bsp_swcore_init` | **0** | 1 |
| `BSP_UART0_BASE` | **0** | 2 |

### 10.2 Fifteen conclusions re-run, and not one is refuted

| token | `-r` | `-R` | what rested on it |
|---|---:|---:|---|
| `simulate_llsc` / `simulate_sync` / `simulate_rdhwr` | 1 / 1 / 1 | 1 / 1 / 1 | `CLAUDE.md`'s bench rule |
| `math_emu` / `fpu_emulator` / `cp1emu` | 0 / 0 / 0 | 0 / 0 / 0 | *there is no FPU emulator in this kernel* |
| `PRID_IMP_RLX4181` / `RLX4181` | 1 / 10 | 1 / 10 | the `RLX5281` ban being lifted |
| `r3k_cache_init` / `r4k_cache_init` | 0 / 0 | 0 / 0 | `notes/cache-model.md` |
| `cache-rlx` / `CCTL` / `IMEM0FILL` | 2 / 3 / 1 | 2 / 3 / 1 | `CPU-20`, `CPU-24`, `CPU-43` |
| `movz` / `movn` | 2 / 2 | 2 / 2 | §7 |

**Nothing moves.** The instrument that would detect a false zero fires on its
controls and is silent on all fifteen. The BSP contains none of those tokens —
which is itself readable: it is board glue, not CPU code.

**One enumeration does move**, and it is §2's: `find arch/rlx -name '*.S'` gives
**17**, `find -L` gives **18**, and the eighteenth is
`arch/rlx/bsp/vmlinux.lds.S`. It is a linker script, gas never sees it, and no
number in §2's table changes. What changes is *why* it is not in the table.

### 10.3 🔴 And `-R` everywhere is the wrong instruction, measured

The primary drop carries **28 symlinked directories**, not one. Twenty-five
resolve back inside the tree; **three point at `/var/tmp`**
(`boards/rtl8196eu/romfs/tmp`, `boards/rtl8198/romfs/tmp`,
`boards/rtl819xD/romfs/tmp`).

量 at the drop root, excluding `.git`:

| | |
|---|---:|
| paths `grep -r` reaches | 66,973 |
| paths `grep -R` reaches | **79,857** |
| **distinct real files behind the `-R` population** | **66,977** |

So `-R` reports **79,857 paths for 66,977 files — a 19.2 % inflation**, because
`users/busybox -> busybox-1.13` (2,121 files), four `mips-linux/include ->
../include` (1,170–1,785 each) and the rest are all counted twice. A census that
counts *files* that way is 19 % wrong in the direction that looks like more
evidence.

🔴 **And it leaves the tree.** The four real files `-r` cannot reach are
`/var/tmp/boa-{af,dbg,emu,triage}.log` — **this project's own analysis logs from
the `binsim` work** — which `-R` presents as vendor content, three times each.
The positive control was planted: a file written to `/var/tmp` came back from
`grep -R` at three paths inside the drop and from `grep -r` at none.

**So the rule is not "use `-R`". It is: a recursive search is blind exactly where
its root sits above a symlinked directory, and `-R` is safe only when nothing
under the root leaves the tree.** Inside `arch/rlx`, `-R` is right. At a drop
root it is wrong twice over.

### 10.4 🔴 The bigger finding: `arch/rlx/bsp` DANGLES in two of the three drops

`arch/rlx/bsp -> ../../../target/bsp`, and `target` is itself a symlink.

| drop | `target` | `arch/rlx/bsp` resolves to | files via `-L` |
|---|---|---|---:|
| `rtl819x-toolchain` | tracked symlink → `boards/rtl8196e` | `boards/rtl8196e/bsp` | 13 |
| `saturn49-wecb` | **does not exist** | **— dangling** | **0** |
| `wecb-vz-gpl` | **does not exist** | **— dangling** | **0** |

`target` is a **tracked symlink** (mode 120000) in `rtl819x-toolchain` and
untracked in the other two; it is normally created by `config/setconfig` when a
board is selected, so whether `arch/rlx/bsp` resolves at all is an accident of
what each uploader committed.

🔴 **The consequence is sharper than the original finding.** Re-running a BSP
question with `-R` over `arch/rlx` across all three drops returns 13, 0, 0 — and
a reader would record that as *"only one drop has it"*, which is false.
**The BSP is in all three by a path that is not a symlink**:
`boards/rtl8196e/bsp/`, 12 source files each.

量 across the three: `prom.c`, `serial.c`, `bspchip.h` and `vmlinux.lds.S` are
**byte-identical**; `setup.c` differs, on exactly one preprocessor condition in
`shutdown_netdev()` — `#if defined(CONFIG_RTL8192CD)` against
`#if defined(CONFIG_RTL8192CD) || defined(CONFIG_RTL8192E)`. That is the reboot
path, not the bring-up path. The 13th file in `rtl819x-toolchain` is
`modules.order`, a build product.

**So BSP readings ARE three-source-able, and every one in §11 is taken through
`boards/rtl8196e/bsp/`, never through `arch/rlx/bsp/`.**

---

## 11. `R3-6` — the boot ladder, and the console instrument it needs first

**The step's brief was three rungs plus "early console settled: which of
`earlyprintk` / the vendor's `prom_printf` / `bspchip`'s UART base is in force at
each stage".** That had to be answered before the rungs, because the answer is
that **none of the three is in force and this board prints nothing**.

### 11.1 🔴 What can actually reach the wire, measured on the built image

量 on the `R3` `vmlinux`, by symbol table and disassembly:

| | address | size | binding | does it print? |
|---|---|---:|---|---|
| `printk` | `0x801094ec` (×3) | 20 | — | **no**. `move v0,zero / jr ra` — the `static inline` stub from `include/linux/kernel.h:271`, emitted out of line three times |
| `early_printk` | `0x80013bec` | 16 | **WEAK** | **no**. `sw a1,4(sp) / sw a2,8(sp) / jr ra / sw a3,12(sp)` — the empty `__attribute__((weak))` body at `kernel/printk_log.c:42`, and **nothing under `arch/rlx` overrides it** |
| `panic_printk` | `0x80015140` | 44 | GLOBAL | **yes**, via `jal vprintk` — but only once a console is registered |
| `vprintk` | `0x80014e2c` | 788 | GLOBAL | the real one; `include/linux/kernel.h:274` declares `panic_printk` in **both** branches of `#ifdef CONFIG_PRINTK` |
| **`prom_putchar`** | **`0x8000b080`** | **100** | **GLOBAL** | **yes, always.** `lui v0,0xb800 / ori a2,v0,0x2014 / ori a1,v0,0x2008 / sltiu v0,v1,30000` — poll `UART0_LSR`, write `UART0_THR`; KSEG1, uncached, bounded at 30,000 spins so it cannot hang |
| `prom_putchar` | `0x8017ced8` | 100 | LOCAL | the second one, `boards/rtl8196e/bsp/setup.c:32`, `static`, no caller in the file |

⚠️ **`CONFIG_EARLY_PRINTK=y` is set and is a trap.** It builds
`arch/rlx/kernel/early_printk.c`, which supplies `prom_putchar` and registers an
`early_console` — but the `early_printk()` *function* a caller reaches for is the
mainline weak stub, unoverridden. Someone who saw the config symbol and wrote
`early_printk("...")` would get a silent boot and a correct-looking `.config`.

🔄 **And the risk the step list actually named is retired, measured.** The row
feared `UART0_BASE` being redefined in `arch/rlx/bsp/setup.c:34` over
`rtl865xc_asicregs.h:2893` — a warning in the build log. 量, both sides:
the header is `#define UART0_BASE (SYSTEM_BASE+0x2000) /* 0xB8002000 */` and the
BSP's is the literal `0xB8002000`. **Same address.** `arch/rlx/kernel/early_printk.c:31`
is a third definition of the same value. So the warning is benign and it is not
what threatened this step. What threatened it was that **there is no writer at
all** — an absent output path, not a contested base address.

**Second source, and it is this device's own capture.**
`bench/2026-08-24c/G6.log` goes `start address: 0x80003440` → `Realtek WLAN
driver - version 1.6` with no banner, no command line and no memory line between
them. The vendor ships `PRINTK` off and rlxfw inherited it (§9.2).

🔄 **2026-08-29, and it does not contradict the table — it completes it.** 量
through the desk channel with `prom_putchar` redirected (§15.5): the **`loud`
variant with no marks in it prints `[    0.000000] CPU revision is: 00018000`**,
41 bytes, before `bsp_setup()`. The table above is about the `early_printk()`
*function*, which is a weak empty stub in both variants; what the `loud` build
adds is the `early_console` that `arch/rlx/kernel/early_printk.c` **registers**,
whose `write` goes through `prom_putchar`. So: `quiet` prints nothing at all
without a mark (量: 0 bytes through the same channel), and `loud` has a live
`printk` path from `setup_early_printk()` onward. `RLXFW-B09` therefore marks
the console handover only in `quiet`.

### 11.2 🔴 And the most likely early failure is silent by construction

讀 `boards/rtl8196e/bsp/setup.c:134-175`, through the real path (§10.4):

```c
void __init bsp_setup(void)
{
    ...
    bsp_serial_init();
    _imem_dmem_init();
#if defined(CONFIG_RTL_819X)
    ret = bsp_swcore_init(version);
    if (ret != 0)
        bsp_machine_halt();      /* static void bsp_machine_halt(void) { while(1); } */
#endif
}
```

`bsp_machine_halt()` is a **bare `while(1)` with no message anywhere**. `TC-23`
already records the desk channel stopping at the switch-core probe, and this
unit's own kernel stopping there too. So the single most likely way `R3-8`'s
first power cycle ends is `start address:` and then nothing, forever — with the
return code that explains it living in a register nobody reads.

### 11.3 The instrument: `rlxfw_mark`, and the two defects the tool found in it

`config/rlxfw-src/linux-2.6.30/arch/rlx/kernel/rlxfw_mark.c` (mine) calls
`prom_putchar`. `<linux/rlxfw-mark.h>` supplies two macros so each mark is **one
contiguous literal** in `.rodata`.

🔴 **That last sentence is the finding of the step, and it came from the tool
refusing.** The first version took the tag as a runtime argument
(`rlxfw_puts("RLXFW-"); rlxfw_puts(tag);`). It compiled, it linked,
`rlxfw-marks.py check` was green on the staged tree, and it would have printed
the right bytes on the wire. 量: `rlxfw-marks.py verify` read the built
`vmlinux` and found `RLXFW-B0` **zero times**, because the two literals are never
adjacent in the image. A mark that exists only as fragments **cannot be checked
before the power cycle**, which is the whole shape of `RUNSHEET` `P6`.
Concatenating at the call site fixes it — and `check` would never have said so,
because `check` reads the tree and `verify` reads the artefact.

🔴 **The second defect came from the same tool on the next run.** `RLXFW-B1` was
counted **twice**: `RLXFW-B10` contains it. Two fixes, because the ambiguity is
not only the tool's — a human greps a capture too. The search string now carries
the macro's terminator (`RLXFW-B01` + newline, `RLXFW-B02=`), and tags are
zero-padded, with control `A16` refusing any tag that is a prefix of another.

### 11.4 The eleven marks

Declared in `config/rlxfw-marks.tsv`, one row each with the suspect it brackets.
Applied to the **staged** tree by `tools/rlxfw-marks.py apply`; `src-vendor/` is
never written and the tool refuses a path under it.

| | where | what a gap before it means |
|---|---|---|
| **B00** | `init/main.c`, after `page_address_init()` | **before any console exists**, which `CONFIG_PRINTK=y` cannot reach either — `setup_early_printk()` is not until `setup.c:546`. Silence here with `start address:` printed splits `RUNSHEET` §B3's two causes |
| **B01** | `setup.c`, before `cpu_probe()` | `start_kernel`'s generic prologue — code this port did not write |
| **B02** | after `cpu_probe()`, **prints `PRId`** | the CPU identification table; and it is a **second, independent reading of `CPU-04`** — 量 `0x0000CD01` on 2026-08-25b through `probe2`'s bare-metal CP0 census, which shares no code with this |
| **B03** | after `bsp_init()` | `arch/rlx/bsp/prom.c` sizing DRAM live off `BSP_MC_MTCR0`. The plan's *memory-related* case starts here, not at `paging_init` |
| **B04** | `bsp_setup()` entry | `arch_mem_init`'s prologue |
| **B05** | after `bsp_serial_init()` | **the divisor.** Every mark before it rides the loader's 38400, and `prom_putchar` never touches the divisor. B05 garbled after a clean B04 = the vendor's serial init changed the line rate; B05 missing entirely = `early_serial_setup` failed and `panic()`'d before a console existed to print the panic |
| **B06** | after `_imem_dmem_init()` | `CPU-46`'s I-MEM/D-MEM CP3 sequence — Lexra-specific, coprocessor 3 |
| **B07** | after `bsp_swcore_init()`, **prints `ret`** | §10.2's designed silent hang, turned into a number |
| **B08** | after `paging_init()` | `bootmem_init` + `sparse_init` + `paging_init` as one bracket, deliberately: three rows where one will do is how a ladder stops being read. If the boot stops inside it, the next session splits the row, and the reason for splitting will be a capture |
| **B09** | after `console_init()` | the handover. Before it everything came through `prom_putchar`; after it the `loud` variant's `printk` starts |
| **B10** | `init_post()`, before `if (ramdisk_execute_command)` | **which path userspace is reached by.** Decision B's refutation condition is *the initramfs fails to unpack*, and B10-then-M4 is that answered one way, B10-then-panic the other |

**Cost, 量 rather than estimated**: `vmlinux` +127 bytes; **the decompressed
image does not move at all** — 3,472,384 both ways — because 127 bytes fits in
existing alignment slack. `hazlint` on both marked images: **0 violations**, in
109,922 (quiet) and 111,801 (loud) loads. Eleven marks at a mean 11 bytes is
about 32 ms of UART against a loader stage that already takes 348 ms (`CLK-15`).

**And they are discriminators, checked rather than asserted**: 量, each of the
eleven strings occurs **once** in my `vmlinux` and **zero** times in both
~~`vmlinux-rederived.bin` (the drop's kernel)~~ and `r0-vendor-kernel.bin` (this
unit's own).

🔴 **2026-08-29 (`R3-7`): the parenthetical is wrong and this same file already
said so four hundred lines earlier.** §3.2's table records
`r0-vendor-kernel.bin` decompressing to `vmlinux-rederived.bin`,
**byte-identical** — re-measured today, LZMA-alone from file offset `0x2808`,
3,374,772 bytes out, sha256 `cf0d60a8ae54352e…`. So **`vmlinux-rederived.bin`
is this unit's own kernel, decompressed**, and the two files named above are one
kernel in two forms rather than two vendor artefacts.

🔴 **And the second of them cannot fail.** 量 today, `RLXFW` occurrences:

| artefact | form | `RLXFW` |
|---|---|---:|
| my `loudm`/`quietm` `nfjrom` — **the file that is uploaded** | compressed | **0** |
| my `vmlinux_img` / `vmlinux` | decompressed / ELF | 11 |
| `r0-vendor-kernel.bin` | this unit, compressed | 0 |
| `vmlinux-rederived.bin` | this unit, decompressed | 0 |
| the drop's `nfjrom` | compressed | 0 |
| the drop's `vmlinux_img` (2,953,660 B) | decompressed | 0 |

**My own uploaded image reads 0 too**, so a `strings` sweep over a compressed
artefact is a test that passes on everything. The informative absence is on the
**decompressed** forms, and there the count is a genuine 0 against a genuine 11.
`RUNSHEET` `P10`'s `--absent` set is corrected accordingly (§B5-c5): keep
`vmlinux-rederived.bin`, add the drop's `vmlinux_img` as a real third artefact,
and record `r0-vendor-kernel.bin`'s zero as structural.

⚠️ **The anti-DoD is unaffected.** The image the loader can stage at
`0x80500000` by accident is *this unit's own*, and it is covered. What was
overstated is the breadth of the check, not the guard.

### 11.5 The three rungs, and a correction to the step list's own wording

| rung | what is added | proves the rung | proves the PREVIOUS rung |
|---|---|---|---|
| **1** | kernel + initramfs, `/init` prints M4 | `RLXFW-B10` then `M4` | `RLXFW-B00` (D1/D2), `RLXFW-B07=00000000` (D3) |
| **2** | 🔄 `ifconfig <if> 10.1.1.10 netmask 255.255.255.0 up` | link up | rung 1's `M4` in the same capture |
| **3** | 🔄 `ping -c 4 10.1.1.2` | at least one reply **and** the host `tcpdump` | rung 2's `ifconfig` output |

🔴 **2026-08-29 (`R3-7`): those two lines read `10.1.1.2` and `10.1.1.1` until
today and both were wrong.** `10.1.1.2` is the **workstation's own** address
(讀, `RUNSHEET` §G3: *"`IPCONFIG 10.1.1.1`, workstation at `10.1.1.2/24`"*), so
rung 2 handed the board an outright conflict, and rung 3 pinged the address the
loader had. Both halves fail, and the capture reads exactly like the definition
of a driver that transmits and does not receive. `RUNSHEET` §B5-c4 and §B5-c10.
⚠️ `<if>` and not `eth0`: **four of the five netdevs are LAN** and the jack↔port
map is 未定 (`NET-13`), so the seating tries them in order rather than assuming
— `RUNSHEET` §B5-c9.

⚠️ **Rungs 2 and 3 add no image variable at all in the current build.**
`drivers/net/rtl819x` is already in the vendor configuration and `ping` is
busybox, already in the initramfs. So the three rungs are three *commands typed
at one shell in one boot*, not three uploads — a correction to the step list's
*"three rungs, each adding one variable"*, and it changes the running order in
`RUNSHEET` §B5 rather than the image.

### 11.6 `CONFIG_PRINTK`: decided, and it is two declared images

**Decision, 2026-08-28: two variants from one declaration.** `quiet` is the
vendor's configuration; `loud` is `quiet` plus `CONFIG_PRINTK=y` and
`CONFIG_PRINTK_TIME=y`. Both carry the eleven marks. **The first seating uploads
`loud`.** One delta file with a `@loud` variant column, because a second delta
file would be a copy of all 35 rules and a copy is a second owner.

🔴 **§6.6's trap fired on the first attempt**: setting `CONFIG_PRINTK=y` alone
takes `(NEW)` from **0 to 1** — `CONFIG_PRINTK_TIME` becomes reachable. So it is
pinned, and `(NEW)` is back to 0.

**`PRINTK_TIME=y` is a measurement, not a default.** `printk_time` reads
`cpu_clock` → `sched_clock`, and 讀 **`arch/rlx` defines no `sched_clock`** —
zero hits — so the weak generic at `kernel/sched_clock.c:39` is used:
`(jiffies - INITIAL_JIFFIES) * (NSEC_PER_SEC / HZ)` with `CONFIG_HZ=100`. It is
**not** CP0 `Count`, which is not implemented on this die (`F50b`, 量
2026-08-25b) and would have printed `0.000000` on every line. So timestamps are
real at 10 ms, and the transition from `0.000000` to a moving value marks where
the timer interrupt started — an observable the ladder gets for free.
**Refuted by**: every line reading `0.000000` through to userspace, which would
be a finding about `time_init` and not about printk.

**And `CONFIG_PRINTK` was checked for the `ARCH_CPU_SLEEP` trap before it was
written down.** 讀 `init/Kconfig:834`: `default n`, prompt gated on `EMBEDDED`,
`depends on (!RTL_819X) || (RTL_819X && PRINTK_FUNC)`. 量 on the built config:
`EMBEDDED=y` and `PRINTK_FUNC=y`. It **has** a prompt and is settable — unlike
`ARCH_CPU_SLEEP`, which has the same shape, is not, and cost `R3-4` a session.

| | `quiet` | `loud` | delta |
|---|---:|---:|---:|
| `vmlinux` | 3,968,240 | 4,042,388 | +74,148 |
| `.text` | 2,444,036 | 2,483,308 | +39,272 |
| `.rodata` | 109,184 | 151,024 | +41,840 |
| **decompressed image** | **3,472,384** | **3,546,112** | **+73,728** |
| margin under 5,242,880 | 1,770,496 | 1,696,768 | — |
| **used** | **66.2 %** | **67.6 %** | +1.4 pp |
| `hazlint` | 0 in 109,922 | 0 in 111,801 | — |

⚠️ **The estimate written before the build was "150–300 KB" and it was wrong by
2–4×.** The answer is 73,728. It was labelled a guess at the time; it is
recorded because an uncalibrated guess that missed by 4× is worth what the
measurement replacing it says it was worth, which is nothing.

**What `loud` costs that is not bytes**: 38400 8N1 is 3,840 B/s, so every 4 KB
the kernel prints is another second inside `prom_putchar`'s busy loop, and
`bsp_swcore_init` and the WLAN driver both drive timing-sensitive hardware.
**That is why `quiet` exists rather than being deleted**: it is the configuration
closest to the one thing known to have booted on this silicon.
🔴 **If `loud` reaches D5 and `quiet` does not, that difference is a finding
about the vendor's configuration and is recorded, not averaged.**

### 11.7 🔴 The ceiling was being measured on the wrong file

`mkinitramfs.py --kernel-image` computed the margin from
`os.path.getsize(vmlinux)`. That is the **ELF file size**, and on this kernel it
is 495,729 bytes larger than the image: symbol table, string table and section
headers, none of which is loaded. It read **75.7 % used where the truth is
66.2 %**.

The error was conservative, so nothing over-ceiling ever passed — what it would
have caused is a **false alarm**, and the documented response to that alarm is to
move `LOAD_START_ADDR` to `0x80A00000`: changing the boot address for a reason
that was not real.

🔴 **And `RUNSHEET` `P9` attributed 3,472,384 to this tool while this tool could
not produce it.** That is the more expensive half — a runsheet number whose
stated source does not compute it.

Fixed to read the program headers directly: over `PT_LOAD`,
`max(p_vaddr + p_filesz) − min(p_vaddr)`. `p_filesz` and not `p_memsz`, because
`.bss` is not in what the decompressor writes. 量: **3,472,384, from `2 PT_LOAD,
0x80000000-0x8034fc00`** — reproducing the `objcopy -O binary` route exactly, by
a path with no cross toolchain in it. Read from the phdrs rather than by shelling
out, because this gate has to run where there is no toolchain. `A20`–`A23` are
the controls, and `A20`'s fixture is built so the file size and the load extent
**cannot** coincide.

🔄 **2026-08-29: corroborated by a tool that shares no code with it.**
`rtkload/Makefile:229` runs `cvimg size_chk`, and on `quiet`/`quietm` it prints
*Image decompress end addr* `0x8034fc00` and *Available size* `0x001b0400` =
**1,770,496** — the same end address and the same margin, computed inside
Realtek's own i386 binary from the flat image rather than from the program
headers. §13.4.

⚠️ Separately worth knowing, and **not** what the ceiling is about: `.bss` on
this build ends at `0x805E5280`, above the `0x80500000` the compressed image sits
at. By the time the kernel zeroes it the wrapper has jumped away and its bytes
are dead — but it does mean the uploaded image is destroyed early in the boot, so
there is no second `J` even in principle.

---

## 12. `R3-7`: what these images look like **on the wire**, and the head does not identify them

**Written 2026-08-29 while turning `RUNSHEET` §B5 into a bench card.** ⚠️ **This
section number was a gap** — §11.7 was followed by §13 and nothing in this
repository ever referenced a §12. It is filled here rather than renumbered,
because every cross-reference to §13–§16 in `PROGRESS.md`, `RUNSHEET.md` and
`SPEC.md` would otherwise move.

Everything below is 讀 or 量-on-this-desk. **Nothing was measured on the
device**; the three device readings quoted are re-reads of committed captures.

### 12.1 🔴 The head does not identify the image — 16 bytes measured on the device, 24 across the files

`RUNSHEET` `K2` was built on *"my image and the staged one differ in their first
16 bytes"*. 量:

| | `0x80500000` | `0x80500004` | `0x80500008` | `0x8050000C` |
|---|---|---|---|---|
| **the device**, `DW 80500000`, three captures | `00000000` | `00008021` | `40906000` | `00000000` |
| `quiet` · `quietm` · `loud` · `loudm` · the drop's | `00000000` | `00008021` | `40906000` | `00000000` |

⚠️ **The device evidence is 16 bytes, not 24.** All three captures are
`DW 80500000 1`, which `LDR-07` rounds up to one line — four words — so bytes
16–23 have never been read on this device at all. The 24 is the desk comparison
of five files, where the first differing byte is offset 27.

The three device captures are `bench/2026-08-23/B.log:16`,
`bench/2026-08-24c/G1a.log` and `bench/2026-08-24d/G5-rb1.log` — two power
cycles, and all three byte-identical. **They agree because they are the same
`rtkload` `start.o`**: every image in this family is linked from the same stub,
and `nfjrom` is `objcopy -O binary` over it.

So `DW 80500000 1` reads the same reply whether the upload landed or not. It is
a cell that cannot fail, and it was the seating's *only* check that the right
bytes were at the load address.

### 12.2 The two words that do identify the image, and they are the linker's

量: the first differing byte between any of my images and this unit's staged one
is at **offset 27**, and the pair of words holding it is a `lui`/`addiu`:

| `0x80500018` | `0x8050001C` | decodes | that image |
|---|---|---|---|
| `3C10805F` | `26101000` | `0x805F1000` | **the staged vendor image** — this unit's flash kernel. Its `nfjrom` is 987,136 B; the **payload** `FW-12` defines is 987,138, the extra two being `LDR-18`'s checksum |
| `3C108060` | `2610AC00` | `0x805FAC00` | `quiet` / `quietm`, 1,027,072 |
| `3C108060` | `26101000` | `0x80601000` | `loud`, 1,052,672 |
| `3C108060` | `26101400` | `0x80601400` | `loudm`, 1,053,696 |
| `3C10805D` | `26100800` | `0x805D0800` | the drop's own, 854,016 |

🔴 **`0x80500000 + size` reproduces the four `nfjrom` rows exactly and the
staged row is two bytes short — and the first version of this table said "all
five, exactly" while the script that built it printed `NO` on that row.** 量:
`r0-vendor-kernel.bin` is 987,138 bytes, its last two are `D6 2B`, `sum16` over
all of it is `0x0000` and over the first 987,136 is `0x29D5`. So the staged file
is `nfjrom` **+ the 2-byte `sum16` tail**; `__vmlinux_end` is the end of the
`nfjrom` and the staged copy in RAM runs to `0x805F1002`. `FW-12` already
carried the decomposition, in this same file, and §12.2 quietly used §3.1's word
*payload* for §3.1's other number.

**The honest statement**: four of four `nfjrom` files equal `base + size`; the
staged one equals `base + size − 2`. This is `__vmlinux_end`, which
`rtkload/ld.script.in` aligns to 1024 — so **the uploaded image carries its own
length as an immediate, and one `DW 80500000 8` reads it back.**

⚠️ Two limits, both measured rather than inferred. **`loud`'s low half equals the
staged image's low half** (`26101000`) and only the `lui` separates them, so both
words are required. And **`quiet` and `quietm` are indistinguishable here** —
same size, same words; a word inside the LZMA stream (`DW 80540000 1`) is what
separates the marked variant from the unmarked one, and there no two of the six
images agree in any of the four words.

### 12.3 The tail is sixteen zero bytes — and that is why it is the only cell that can watch a change

量, the last 16 bytes of all five `nfjrom` files: **all zero**, with trailing
zero runs of 312 / 552 / 180 / 688 / 28 bytes — **28 to 688**, and the 28 is
only twelve bytes clear of breaking the premise the cell rests on.
On its own *"expect zeros"* is a
check a dead instrument passes.

🔴 **But the tail is the one part of the upload that is not on top of the
fallback.** The staged vendor image ends at `0x805F1002` — 讀 the flash header's
`len` = `0x0F1002` (`FLM-09`) plus the inference that the loader copies exactly
`len` bytes to `startAddr`, so **讀 + 推 and not 量**. ⚠️ **`MAP-17` is not a
second source for it**: that row is *selected*, its own value column is `—`, and
its bound is `0x80A00000 +` the same `0x0F1002`. Citing it was the defect §12.x
and `RUNSHEET` §B5-c5 both name one level up. While:

| | tail `DW` address | above the staged image by |
|---|---|---:|
| `quietm` | `0x805FABF0` | 39,918 B |
| `loudm` | `0x806013F0` | 66,542 B |

`K2` refuses to poison the region because that would destroy the fallback, and
for the head that is right. For the tail nothing needs poisoning: **read it
before the transfer and again after**, and `DW … 8` gets two lines in one
command — the last line of the image, which must **change** to zeros, and the
first line past `image_end`, which must **not change at all**. The second is a
negative control on the transfer length and it costs nothing.

⚠️ 推, and it is `RUNSHEET` `K8`: after a failed `J` the watchdog resets and the
loader re-stages `0x80500000`, but the re-stage ends at `0x805F1002` and
`loudm`'s `.bss` ends at `0x805F7280` (量, `readelf -S`: `0x80362000` +
`0x295280`), so the tail should survive both. Nothing has ever read that region
after a failed `J`.

### 12.4 The ladder's byte count, validated on two captures before it was used

Each mark is one literal ending `\n` and `rlxfw_puts` turns that into `\r\n`
(讀, §11.3), so a plain mark is **11 bytes** and a valued one **20**:

| | model | 量, `qemu/2026-08-29/` |
|---|---:|---:|
| `quietm`, B00…B07 | 8×11 + 2×9 = **106** | **106**, byte-identical |
| `loudm`, + `[    0.000000] CPU revision is: 00018000` (42 B) | **148** | **148**, byte-identical |
| on the device, B00…B10, B07 = `00000000` | **139** | — |
| + M4 (`echo` 39 B, `ONLCR` 40 — 推) | **179** | — |

At 38400 8N1 = 3,840 B/s that is 36.2 ms for the marks and 46.6 ms with M4.
**A short capture is a number now**: 106 where 139 was predicted is B08–B10
missing, not a garbled line.

⚠️ **The count is a floor for `loud`/`loudm`, not a prediction.**
`setup_early_printk()` registers between B03 and B04 (量), and the desk channel
halts at B07 — so nothing has ever observed this kernel printing between B04 and
B10 with `CONFIG_PRINTK=y` and real peripherals.

🆕 **The two readings of `PRId` in a `loudm` capture will arrive in different
case — 推, and the values below are the DEVICE's, which no capture holds.**
讀: `rlxfw_puts_hex` uses `"0123456789ABCDEF"`, so B02 prints upper case;
`arch/rlx/kernel/cpu-probe.c:39` is `printk("CPU revision is: %08x\n", …)`, so
that line prints lower case. 量, on the only `loudm` capture that exists: **both
print `00018000`** — qemu's 4Kc `PRId`, whose eight digits contain no letters,
so the case difference has never been observed. On this die the same binary must
print `0000CD01` and `0000cd01`, and the case difference then becomes free
evidence that they are two paths rather than one string. **If they disagree in
value, one of the two paths is wrong** — which is what the cross-check is for.

### 12.5 `/proc/cpuinfo` is a third reading of `PRId`, and the shipped kernel prints one field mine does not

讀 `arch/rlx/kernel/proc.c:26-35` — six `seq_printf`s, and line 29 is
`"cpu model\t\t: %d\n"` on `cpu_data[n].processor_id`. **A decimal integer, not
a core name.** 讀 upstream `test-ledger.md` `P5-5`, which read this same file on
**this unit** under the **vendor's** firmware:

| field | vendor kernel, 量 | mine, predicted | source |
|---|---|---|---|
| `system type` | `RTL819xD` | `RTL819xD` | 讀 `boards/rtl8196e/bsp/prom.c:43`, `return "RTL819xD";` |
| `cpu model` | **`52481`** | **`52481`** | `0x0000CD01`. **A third independent reading of `CPU-04`**, in decimal, through `seq_file` and userspace |
| `BogoMIPS` | `398.95` | `398.95` | `udelay_val`; far from it names `time_init`, not the CPU |
| `tlb_entries` | `32` | `32` | corroborates `CPU-08` by a path with no TLB probe in it |
| `mips16 implemented` | `yes` | `yes` | 讀 `proc.c:35` — **a hardcoded string. Not a measurement** |
| `hardware watchpoint` | **`no`** | 🔴 **absent** | 量: the format string `hardware watchpoint\t: %s` occurs in `vmlinux-rederived.bin` and **zero** times in either of my images. The drop's `proc.c` has no such line |

🔴 **The missing seventh field is a free discriminator, and it is a second data
point of `TC-17`'s shape**: this unit's shipped kernel was not built from any of
the three drops in hand. Its *presence* in a capture would mean the vendor
kernel answered.

And `linux_banner`, 量 on both decompressed images:

```
mine    Linux version 2.6.30.9 (key@K) (gcc version 3.4.6-1.3.6) #1 Fri Aug 28 23:37:47 CST 2026
this unit's  Linux version 2.6.30.9 (admin@office.hopeiot) (gcc version 4.4.5-1.5.5p2 (GCC) ) #1526 Wed Jan 10 14:50:54 CST 2018
```

**`#1` against `#1526`.** The release string `2.6.30.9` is identical in both and
is therefore not the discriminator; the version field is.

### 12.6 🔴 `nfjrom` does not force `0x80000000`. `boot.img` does

讀 `$FWRE_WORK/stage2.bin` at `0x80401208`, this unit's own second stage —
a second source for what upstream's note already disassembled:

```
80401210  jal   0x80406D7C          ; against "nfjrom"   @ 0x8040A6A0
80401218  beqz  v0, 0x8040122C      ; no match -> fall through to the boot.img test
80401224  j     0x8040125C          ; MATCH -> skip the boot.img test entirely
80401228  sw    v1,-0x2C70(v0)      ; 0x8040D390 = 1     execute on completion
...
80401234  jal   0x80406C40          ; against "boot.img" @ 0x8040A6A8
8040124C  sw    v1,-0x2C70(v0)      ; 0x8040D390 = 1
80401250  lui   v1,0x8000
80401258  sw    v1,-0x2C58(v0)      ; 0x8040D3A8 = 0x80000000    boot.img ONLY
```

§13.3 said the name *"makes the loader force the load address to `0x80000000`
and execute at the end of the transfer"*, and `SPEC.md` `LDR-26` said the same
of both names. **Only `boot.img` writes the address.** The two tests are
mutually exclusive — a `nfjrom` match branches past the second one — and the
routine at `0x80406D7C` computes both lengths before walking, i.e. it is a
substring search rather than `strcmp`.

**The correction matters in the dangerous direction.** With `nfjrom` as the TFTP
filename the loader jumps to whatever load address is set — `0x80500000`, the
right one — so the accident *looks like a successful boot* and silently costs
the `J` line, the `AUTOBURN` timing and the whole of `K2`. With `boot.img` it
jumps to `0x80000000` and crashes. Those are two different accidents.

⚠️ **And the guard is narrower than §13.3 implied.** `loader-tftp.py put` tests
`--filename` — the name in the WRQ — not `--image`'s basename, which the loader
never sees; `--filename` defaults to `image`. So *"copy the file to another
name"* is not what protects the seating. Passing `--filename` explicitly is.
Both are done: the two upload files are staged as
`bench-only/b5-20260830/rlxfw-{loudm,quietm}-20260830.bin` (量, `cmp`-identical
to the pipeline's `nfjrom`) and the card passes `--filename rlxfw-loudm`.

### 12.7 🔴 `uname` is not an applet in this unit's `busybox`, and the seating asked for it three times

`RUNSHEET` `K5`'s second command was `uname -a`. It is one of D4's two
observables — *a typed command returns output* — and it cannot run.

量 2026-08-29, this unit's **own** `busybox` (273,332 bytes, `BusyBox v1.13.4
(2018-01-10 14:56:45 CST)`, carved out of its own flash dump) executed under
`qemu-mips-static` against its own extracted rootfs:

| | |
|---|---|
| `busybox uname -a` | 🔴 **`uname: applet not found`** |
| applets the binary lists | **50** |
| of the fourteen this seating needs | `uname` is the **only** absent one |
| present | `cat` `ifconfig` `ping` `ls` `ps` `mount` `echo` `sleep` `mkdir` `sh` `ash` `sed` `grep` |

**Both controls are inside the same measurement**, which is what makes the
`applet not found` a reading rather than a broken invocation: a name that is not
an applet returns `sh: definitely_not_an_applet: not found` (negative), and
`cat` gets as far as opening a file and reporting `No such file or directory`
(positive).

⚠️ **`qemu-mips-static` with `-L <rootfs>` is not a sandbox**, and the first
attempt at this measurement proved it: `busybox sh -c 'uname -a'` printed the
**WSL host's** uname, because the shell's `PATH` search fell through to the real
filesystem. That reading is an artefact and is excluded; the load-bearing one is
`busybox uname -a`, which goes to the applet table and never touches `PATH`.
⚠️ And the first tree tried was `rebuild/fakework/extracted/unit-2018`, whose
`/bin` holds only `boa` and `busybox` — a partial carve, whose **0 symlinks**
would have supported a conclusion about the shipped firmware that is false. The
complete tree is `$FWRE_WORK/extracted/unit-2018/squashfs-root`: 163 files,
88 symlinks, **51** of them in `bin`/`sbin`/`usr/bin`/`usr/sbin`.

🔴 **The gap had already been found once and the fix written for it would not
have worked.** §9 above records a `/bin/uname` symlink added *"because
`RUNSHEET` `K5` types `uname -a` and this unit's dump has 50 busybox symlinks
without that being one of them"*, and then removed. **Three passes — the
runsheet cell, the symlink, its removal — and none asked whether the applet
exists.** With the symlink in place the shell would have `exec`'d `busybox` as
`uname`, and `busybox` would have printed `applet not found`.

**The replacement is strictly better than what it replaces**, which is why this
is a correction and not a deletion. `cat /proc/version` prints `linux_banner`
verbatim:

```
Linux version 2.6.30.9 (key@K) (gcc version 3.4.6-1.3.6) #1 Fri Aug 28 23:37:47 CST 2026
```

`uname -a` would have dropped `(key@K)` and the gcc version — two thirds of the
discriminator, and the two thirds the vendor image cannot fake. `cat` is an
applet **and** is declared in `config/rlxfw-initramfs.tsv`; `/proc` is mounted
by `/init` before it `exec`s the shell.

⚠️ `bench/2026-08-30b/PREDICTIONS-B5-block1.md` §`L5b` still says `uname -a`.
**It is not edited** — it was frozen before this was measured, and house rule 2
is that a prediction file is not touched afterwards. The capture prefix is
`L5b` either way, so the ordering check is unaffected; `RUNSHEET` §B5-c7 is
where the change of command lives.

---

## 13. `R3-2` stages 3–6: the pipeline reproduces the vendor's own `nfjrom` byte for byte

**The step's own DoD put the control first**, and this is the result of running
it: with the drop's own `image/vmlinux.elf` (3,441,133 bytes) fed into the
drop's own `rtkload/Makefile`, driven by `tools/rtkimage.py build`:

| artefact | rebuilt | the drop's | |
|---|---:|---:|---|
| `vmlinux-stripped` | 3,001,168 `7b65fdf8d7464aad` | 3,001,168 `7b65fdf8d7464aad` | **identical** |
| `vmlinux_img` | 2,953,660 `48b1a17187bcc729` | 2,953,660 `48b1a17187bcc729` | **identical** |
| `vmlinux_img.gz` | 842,724 `7abeda46c549cf61` | *not shipped* | — |
| `memload-full` | 944,505 `4ebdbb3689b4e196` | 944,997 `e2f3cd1021da410d` | differs, §13.1 |
| **`nfjrom`** | **854,016 `5cc8d61d4b4e8914`** | **854,016 `5cc8d61d4b4e8914`** | **IDENTICAL** |
| `linux.bin` | 854,034 `f612122e47e92930` | 854,034 `f6a51b3130f49182` | differs by **one byte** — and §13.2 closes it |

🔴 **`nfjrom` is the file that is uploaded to `0x80500000` and jumped to, and it
is byte-identical.** That settles four things at once that were open when the
step was written:

* `rtkload/lzma` is a two-branch shell script keyed on `uname -r | grep 2.4`;
  on this host it selects **`lzma-26`** (LZMA 4.06, defaults `-a2 -d23 -fb128
  -lc3 -lp0 -pb2 -mf bt4`), and `lzma-26`'s output is the vendor's, byte for
  byte. ⚠️ **That does not exclude `lzma-24`**, and the first version of this
  bullet said it did — *"a different one cannot produce the same 842,724
  bytes"*, which is an argument and not a measurement. 量: `lzma-24` **cannot
  be run on this host at all** (`error while loading shared libraries:
  libstdc++.so.5`), so whether it would emit the same stream is **untested**.
  What is measured is that the branch this host takes reproduces the bytes.
* `cvimg vmlinuxhdr`'s 8-byte prefix (`pending_len`, `kernelStartAddr`) is
  reproduced exactly, including `pending_len = 1`.
* the loader stub — ten translation units compiled with `rsdk-1.3.6-4181` —
  produces **identical loaded bytes** to the vendor's, so §1's Decision A is
  not merely *a* toolchain that works, it is one that reproduces the drop's own
  output. 讀 the drop's top-level `.config`: `CONFIG_RSDK_rsdk-1.3.6-4181-EB-2.6.30-0.9.30=y`.
* the stub was compiled against **rlxfw's** `include/linux/autoconf.h`, not the
  board template's, and the bytes still match. 讀, before the run: the thirteen
  `CONFIG_` symbols the `rtkload` sources test are identical across the board
  template and both rlxfw variants. That was a necessary and not a sufficient
  check — the kernel headers those sources pull in test many more — and the
  byte identity is what makes it sufficient.

### 13.1 `memload-full` differs by 492 bytes, and all of them are a build path

No allocated section differs in address or in size. Twelve sections differ and
every one is DWARF:

| | mine | the drop's | delta |
|---|---:|---:|---:|
| ten `.debug_info*` | — | — | **+43 each** |
| two `.debug_line*` | — | — | +32 each |
| sum of section deltas | | | **+494** |
| file size | 944,505 | 944,997 | **+492** |

量, `DW_AT_comp_dir` in each: mine is 58 characters, the drop's is **101** —
`/home/<the vendor's builder>/11n/rlx/patch_area/rtl819x-SDK-v32_v321_v3211_322_3221/rtl819x/linux-2.6.30/rtkload`.
**101 − 58 = 43**, once per translation unit, and there are exactly ten. The two
remaining bytes are section-alignment padding. ⚠️ The step list wrote *"a build
stamp is enough to move it, which is why the comparison is structured"* before
any of this ran; this is that sentence with a number on it.

Worth keeping for `which-drop.md`: that path names the SDK the drop came from,
**`rtl819x-SDK-v32_v321_v3211_322_3221`**, read out of DWARF rather than out of
a README.

### 13.2 🔴 The one byte is the signature — and the Makefile's own option is what picks the wrong one

量: the rebuilt `linux.bin` differs from the shipped one at **offset 3 and
nowhere else** — `cr6b` against `cr6c`. The checksum tail is identical
(`a20a`), which is consistent: `sum16` is taken over the payload and the
signature is in the 16-byte header, outside it.

讀 `strings rtkload/cvimg`: the only two signatures **stored in the binary**
are `cs6b` and `cr6b`. 量, by running it: `cvimg linux` writes `cs6b`,
`cvimg linux-ro` writes `cr6b`.

🔴 **The first version of this section then said *"there is no input to this
program that produces `cr6c`"*, and the adversarial pass killed it with one
command.** `cvimg`'s own usage line — printed at the top of every refusal, and
read hours before this was written — ends `[signature]: user-specified
signature (4 characters)`. 量:

```
./cvimg signature nfjrom out.bin 0x80500000 0x30000 cr6c
```

**produces a file byte-for-byte identical to the shipped `linux.bin`.** So the
reproduction is not three of five artefacts, it is **five of five**, and the
only thing that does not reproduce is `memload-full`'s DWARF.

**What the finding actually is, now that it is the right size:** the
Makefile's own `CV_OPTION` selection for this board picks `linux-ro`, because
`CONFIG_SQUASHFS=y`, and `linux-ro` writes `cr6b`. **So the `linux.bin` this
drop ships was not produced by this Makefile path with this configuration.**
It was produced either with `CV_OPTION=signature CV_SIGNATURE=cr6c` — the
branch the Makefile reserves for `CONFIG_RTL_8197B_PANA`, which writes `csys`
— or by the `cvimg` the Makefile prefers and this drop does not contain.

And `cr6c` is what real images carry — two of them, independently:

* the drop's own `boards/rtl8196e/image/linux.bin` (§3.1);
* **this unit's own flash at `0x060000`** (§3.1, 987,138 bytes, `sum16` 0).

讀 `rtkload/Makefile:11-19`: `CVIMG` prefers `$(DIR_USERS)/boa/tools/cvimg`,
then `$(DIR_USERS)/goahead-2.1.1/LINUX/cvimg`, and falls back to `./cvimg` only
if neither exists. 量: this drop contains **exactly one** `cvimg`, the fallback.
So the drop ships a build system that calls a tool it does not ship — and the
tool it does ship reproduces the drop's own flash header only when it is told
the signature, which the option the Makefile picks for this board does not do.

**What this costs `R3`: nothing.** The RAM path takes `nfjrom`; a `cr6c` header
on a TFTP upload is 16 bytes of junk at `0x80500000` (`RUNSHEET` `P5`), and
`nfjrom` is identical. **What it costs `R9`: one argument, not a blocker** —
and the first version of this paragraph called it a blocker, which was the
same overstatement one level up. `check_image()` on the flash path is a
signature test plus the zero-sum rule (`C-4`); an image built the way the
Makefile builds it for this board would fail the first half, and
`CV_SIGNATURE=cr6c` makes it pass. **What `R9` must not do is take the
signature from the Makefile's own option logic without reading what came out**
— which is exactly what happened here, at the desk, where it cost nothing.

### 13.3 The four images, end to end

All four go through the same pipeline. `CONFIG_BLK_DEV_INITRD=y` on all of
them, so `make` skips the `flash_size_chk` step the control tripped on, and all
four builds return 0.

| | `vmlinux` ELF | stripped | **decompressed** | LZMA stream | **`nfjrom`** | `linux.bin` | `pending_len` | ceiling |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `quiet` | 3,968,113 | 3,520,352 | 3,472,384 | 1,015,496 | **1,027,072** | 1,027,090 | 1 | 66.2 % |
| `quietm` | 3,968,240 | 3,520,376 | 3,472,384 | 1,015,256 | **1,027,072** | 1,027,090 | 1 | 66.2 % |
| `loud` | 4,042,261 | 3,594,128 | 3,546,112 | 1,041,228 | **1,052,672** | 1,052,690 | 2 | 67.6 % |
| `loudm` | 4,042,388 | 3,594,152 | 3,546,112 | 1,041,744 | **1,053,696** | 1,053,714 | 3 | 67.6 % |

`nfjrom` sha256: `quiet 09f5eea5ae1f7f5b`, `quietm cf8a93d73025292d`,
`loud b3a068331270ccab`, `loudm 72928c564d903c8d`.
`kernelStartAddr` is **`0x80003600` on all four**, and each one round-trips:
decompressing the `nfjrom` gives back its own `vmlinux_img`, byte for byte.
Every `linux.bin` sums to `0x0000` and carries flash offset `0x00030000`.

🔴 **Three sizes, three different things, and `RUNSHEET` `P3` was conflating
them.** The row said *"the four images this seating can draw from are 3,968,113
/ 3,968,240 / 4,042,261 / 4,042,388"*. Those are `vmlinux` **ELF** sizes. What
the desk channel ingests is the **decompressed** image (3,472,384 / 3,546,112);
what is **uploaded and jumped to** is `nfjrom` — **1,027,072 / 1,053,696**,
about a quarter of the number that was written down. The bench consequences are
the TFTP transfer size and `K2`'s `DW` at `image_end − 16`, and both were wrong.

🔴 **And the artefact is called `nfjrom`, which is one of the two filenames the
loader treats specially.** 讀 `LDR-26`: a TFTP filename containing **`nfjrom`**
or **`boot.img`** makes the loader force the load address to `0x80000000` and
**execute at the end of the transfer**, with nobody at the console. The
pipeline's output is literally that name. So the file has to be **copied to a
different name before it is uploaded**, and `RUNSHEET` `K1` now says so —
before 2026-08-29 that warning was about a filename nobody was going to type by
accident, and now it is about the one the build produces.

🔄 **2026-08-29, later the same day (`R3-7`): that sentence is wrong twice and
§12.6 has the disassembly.** 讀 this unit's own `stage2.bin`: **`nfjrom` sets
only the auto-execute flag; `boot.img` is the one that also writes
`0x80000000`.** And the guard is on `loader-tftp.py`'s **`--filename`**, not on
the local path — so copying the file is hygiene, and passing `--filename`
explicitly is the control.

⚠️ **The marks make the image compress BETTER, not worse.** `quietm`'s
`vmlinux` is 127 bytes larger than `quiet`'s and its LZMA stream is **240 bytes
smaller** (量). *Eleven strings sharing the prefix `RLXFW-B` are close to free
to a match finder* is 推 — it is the obvious explanation and it has not been
tested against, say, removing one mark. `loudm`'s stream is 516 bytes larger than `loud`'s, and its
`nfjrom` is a whole 1,024 bytes larger because `rtkload/ld.script.in` aligns
`__vmlinux_start`/`__vmlinux_end` to 1024. **Neither delta is predictable from
the ELF delta**, which is why they are measured per image and not derived.

### 13.4 The vendor's own tool computes the ceiling, and it agrees

`rtkload/Makefile:229` runs `cvimg size_chk vmlinux_img $(LOAD_START_ADDR)`.
量, from each build's log:

| | *Image decompress end addr* | *Available size* | this project's number |
|---|---|---:|---:|
| the drop's kernel | `0x802d11bc` | `0x0022ee44` = 2,289,220 | 2,289,220 (§3.4) |
| `quiet` / `quietm` | `0x8034fc00` | `0x001b0400` = **1,770,496** | 1,770,496 (§11.6) |
| `loud` / `loudm` | `0x80361c00` | `0x0019e400` = **1,696,768** | 1,696,768 (§11.6) |

🔴 **That is an independent second source for §11.7's correction.** Until
2026-08-28 `mkinitramfs.py` computed the margin from `os.path.getsize(vmlinux)`
and read 75.7 % where the truth is 66.2 %, an error of 495,729 bytes. The
replacement reads the program headers; Realtek's `cvimg` reads the flat image;
the two agree to the byte, and they share no code.

---

## 14. `RUNSHEET` `P2`: `hazlint` over the objects, and `TC-21` asserted rather than assumed

**Owed since `R3-4`, and owed on four trees rather than one.** `P1` runs
`hazlint` over the linked `vmlinux` and reads 0. That is a strong statement
about the bytes that will execute and a weak one about *why* they are safe,
because it cannot separate two things that coincide: the author of
`arch/rlx`'s hand-written assembly filling his delay slots, and `gas` filling
eleven of them for him because the gcc driver handed it `lx4180` (`TC-14`,
`TC-21`). New tool: **`tools/hazlint-objs.py`**, with `tools/test-hazlint-objs.sh`
(28 cases).

### 14.1 🔴 The enumeration is the first control, and the obvious way to write it is blind

`arch/rlx/bsp` is a symlink (§10). 量 on the four trees:

| | `find` | `find -L` | what only `-L` reaches |
|---|---:|---:|---|
| `quiet` / `loud` | 57 | **63** | `bsp/built-in.o`, `bsp/irq.o`, `bsp/prom.o`, `bsp/serial.o`, `bsp/setup.o`, `bsp/timer.o` |
| `quietm` / `loudm` | 58 | **64** | the same six |

Those six are the board. `bsp_setup()`, `bsp_serial_init()` and the call to
`bsp_swcore_init()` whose return value `RLXFW-B07` prints are all in
`bsp/setup.o`. **A `P2` written with plain `find` would have swept the
architecture, skipped the machine, and reported 0.** `Q1` refuses unless
`bsp/setup.o` is in the swept list, and `test-hazlint-objs.sh` `A2`/`M1` are
that refusal in both directions.

### 14.2 The sweep

| tree | leaf objects | loads | `load;nop` | unresolved | **violations** | bytes scanned |
|---|---:|---:|---:|---:|---:|---:|
| `quiet` | 59 | 1,607 | 350 | **0** | **0** | 56,472 |
| `loud` | 59 | 1,675 | 363 | **0** | **0** | 58,344 |
| `quietm` | 60 | 1,617 | 350 | **0** | **0** | 56,784 |
| `loudm` | 60 | 1,685 | 363 | **0** | **0** | 58,652 |

The marked trees carry one extra object, `kernel/rlxfw_mark.o` (8 loads, 188
bytes, 0 violations). `built-in.o` aggregates are reported and **not** added:
they are a second copy of their leaves, and `arch/rlx/lib/built-in.o` is not
even a complete one (`lib-y` goes to `lib.a`), so adding them would be wrong
twice.

**`unresolved` is 0 on all four**, and that is worth more than it looks. A `.o`
carries no applied relocations, so a load sitting in a delay slot whose branch
target is elsewhere would be reported as `unresolved` and *not checked* — a
false-negative channel that `P1` exists to close. 量: the channel is **empty**
on this material. Not one load in these 60 objects sits in a delay slot whose
successor the tool could not resolve.

### 14.3 🔴 `Q5`: the same sources at `-march=5281` carry exactly eleven

A sweep that reports 0 and cannot show what a 1 looks like on the same material
is not a measurement. The control is the build's **own recorded command line** —
read out of kbuild's `.<name>.o.cmd`, not reconstructed — with one token
appended, `-Wa,-march=5281`:

| object | the build's own `.o` | the same source, `-Wa,-march=5281` |
|---|---:|---:|
| `kernel/entry.o` | 0 | **5** |
| `kernel/genex.o` | 0 | **1** |
| `lib/strlen_user.o` | 0 | **2** |
| `lib/strnlen_user.o` | 0 | **2** |
| `lib/strncpy_user.o` | 0 | **1** |
| `kernel/scall32-o32.o` | 0 | **0** |
| | | **11** |

Identical on all four trees. It is §2's table, produced from the objects the
build actually made rather than from a separate two-way assembly, and
`scall32-o32.o` is in the control precisely because it must stay at 0 — a
control whose every cell is expected to fire cannot show that the tool is
reading the `-march` and not the filename.

⚠️ 讀 the recorded command lines: **there is no `-march` anywhere in them.** That
is `TC-14` visible in the build's own record — the driver hands `as` its own
default, and the default is on the padded side.

### 14.4 `TC-m` measured instead of argued, and it is the harmless direction

`TC-m` (carried in `PROGRESS.md`): on an `ET_REL` object the MIPS16 excision is
printed and does not happen, because the holes are computed from `st_value` —
section-relative in a relocatable object — while the spans carry a synthetic
base, so they never intersect.

量, `Q8`: **26 objects (27 in the marked trees) print `EXCISED BY NAME`, and not
one of them scanned fewer bytes than its `SHF_EXECINSTR` sections hold.** The
claimed excision removed nothing, on this material, on every object that
claimed one.

🔴 **The direction matters and it is the safe one.** Those bytes were *scanned*
as 32-bit words rather than skipped, so `TC-m` can manufacture a violation and
cannot hide one. **A 0 from this sweep is therefore not weakened by `TC-m`**;
a non-zero from it would have been suspect until the site was read. `TC-m` is
not fixed here — it stays carried — but `P2` no longer waits on it.

### 14.5 Two refusals that are correct and had to be handled anyway

`hazlint` refuses a file with zero loads (*"that is exactly what a tool that is
not looking reports"*) and dies on a file with no executable section. On a
per-object sweep both are ordinary:

* **7 objects really have no load** — `head.o`, `imem-dmem.o` and the five
  64-bit helper routines. They are re-run once with `--allow-zero-loads`, and
  `Q7a` requires the re-run to still read 0 loads on a **non-zero** number of
  words: the flag lifts a refusal, it must not move a number.
* **1 object holds no code at all** — `init_task.o`, whose only allocated
  section is `.data..init_task`. `Q7b` confirms that against the section
  headers **in this tool**, not from `hazlint`'s message, because *"there is
  nothing to scan here"* is exactly the sentence a broken sweep would also
  print. `M4` is the mutation that makes `Q7b` falsifiable.

⚠️ `cpu-probe.o` is in the zero-load list for `quiet`/`quietm` and not for
`loud`/`loudm`: with `CONFIG_PRINTK=y` it gains the loads behind
`printk("CPU revision is: %08x\n", ...)`. Nothing depends on that; it is
recorded because it is a free consistency check between the two variants.

---

## 15. `RUNSHEET` `P3`: the desk channel runs the boot ladder, and `B07` has a value

**Not run on any of the four images before today.** The only channel run on
disk was from 18:02 on 2026-08-28, on the pre-flag, pre-initramfs, pre-marks
build. New tool: **`tools/deskchan.py`**, with `tools/test-deskchan.sh`
(18 cases).

### 15.1 🔴 §5's four numbers are re-derived, and the metric they were labelled with is wrong

§5's table said *"KSEG0 instructions"*: control 880, mine 880, then 968 and
1,003 with the COP3 words replaced by `nop`. 量 today, and against the four
`.pcs` files the 2026-08-28 run left on disk:

| run | entry | stops at | §5 printed | listed PCs | **distinct PCs** |
|---|---|---|---:|---:|---:|
| this unit's kernel | `0x80003440` | COP3 at `0x8000227C` → BEV | 880 | 866 | **828** |
| the 2026-08-28 build | `0x80003600` | `0x8000233C` | 880 | 880 | **843** |
| this unit's kernel, `nop` | `0x80003440` | `0x8031E218` `j .` | 968 | 968 | **908** |
| the 2026-08-28 build, `nop` | `0x80003600` | `0x80006B2C` | 1,003 | 1,003 | **938** |

Two corrections, and only one of them matters:

* **the numbers are LISTED program counters, not instructions.** `-d in_asm`
  logs at translation time, and qemu re-translates a block when it is entered
  at a different offset, so the same instruction is listed more than once. The
  distinct counts are 828 / 843 / 908 / 938; today's tool reproduces 828 and
  908 exactly from the same images, on `4Kc`, `24Kc` and `24Kf` alike.
* **the control's 880 in the first table is in no log.** `c1.pcs` — this unit's
  kernel, unpatched, stopping at `0x8000227C` — gives 866 listed and 828
  distinct. 880 is the *other* run's number. §5 concluded *"both stop at the
  same instruction class"*, which is true and is supported by the stop
  addresses; the equal counts that were printed beside it were not measured.

🔴 **Neither could be checked, because the invocation was not recorded.** The
`.log` and `.pcs` files were kept and the qemu command line was not, so
reproducing the numbers meant guessing at `-cpu`, `-m` and `-d` flags — all
three were tried and none of them explains the gap. `deskchan.py` prints its
full command line on every run and writes `pcs.txt` beside the trace.

### 15.2 The redirect, and the control that caught the first attempt

`prom_putchar` writes UART0 at `0xB8002000`; malta has nothing there.
`--redirect-uart` rewrites **five words inside `prom_putchar` and nothing else
in the image** — the two `lui v0,0xb800` and the three `ori` that form THR, FCR
and LSR — so that they point at malta's CBUS UART. The window is
`prom_putchar`'s own extent out of the symbol table, and that is not fastidiousness:
`lui v0,0xb800` (`0x3C02B800`) is how *every* KSEG1 register access in this
kernel begins, and a whole-image search-and-replace would have moved the
address of every peripheral in the port and produced an image that runs and
means nothing.

🔴 **The first target was wrong and `C1` said so.** malta's ISA COM1 at
physical `0x180003F8` needs no change to the `lui` at all, which made it the
attractive one. 量, with a `-bios`-only stub that writes two characters blind:
**nothing arrives**, and a poll of `0xB80003FD` reads 0 forever. The redirect
went to the CBUS UART instead — `0xBF000900` THR, `0xBF000928` LSR,
`serial_hd(2)` — which this project's own `qemu-harness/qemu-run.sh` had
recorded in a comment since 2026-08-25.

⚠️ **And that reading contradicts one this repository already had committed.**
`qemu/2026-08-26/probe3.txt` is 5,893 bytes produced by a payload writing
**`0xB80003F8`** — the address that produced nothing today. Both are
measurements and neither is wrong; **one variable differs, and it is the entry
mechanism**: `probe3` went in through `-kernel`, where qemu's malta writes its
own bootloader into the reset window and that code initialises the board first,
while this channel replaces the firmware with four instructions that initialise
nothing. **That the GT64120's PCI/ISA decoders are the specific thing missing is
推** — it is the obvious candidate and nothing here separates it from the
others. `qemu/README.md` now carries the pair so that neither capture is read as
generalising over the other.

⚠️ **An unpolled first write is lost.** 量, four stubs: blind `ABCDE` → `BCDE`;
blind `A` alone → nothing; polled `RLXFW` with no blind write → `RLXFW`,
complete; blind `AB` + polled `CD` → `BCD`. `prom_putchar` always polls, and on
the real images the first mark arrives whole. Mechanism undetermined; `C0` pins
the rule so that a qemu which stops doing it says so rather than quietly
changing what a capture should look like.

### 15.3 The runs

All with `--nop-cop3`, which is declared: it skips the Lexra IMEM/DMEM setup,
because qemu's 4Kc raises Coprocessor Unusable on those four opcode-`0x13`
words. `C3` prints their addresses every run — `0x8000227C`, `0x8000228C`,
`0x800022D8`, `0x800022E8` — and refuses if there are none.

| run | distinct KSEG0 | stops at | serial |
|---|---:|---|---|
| this unit's kernel | 908 | `0x8031E218` `j .`, from `rtl_processBlock` | — |
| **the drop's own kernel** | **938** | `0x80006B28` | — |
| `quiet` | **938** | `bsp_machine_halt+0` `0x80006B94` | — |
| `quietm` | 1,034 | `bsp_machine_halt` `0x80006B9C` | — |
| `loud` | 2,207 | `bsp_machine_halt` `0x80006C64` | — |
| `loudm` | 2,284 | `bsp_machine_halt` `0x80006C6C` | — |
| `quiet` + redirect | 938 | as above | **0 bytes** |
| `loud` + redirect | 2,208 | as above | 42 bytes |
| **`quietm` + redirect** | 1,035 | as above | **106 bytes** |
| **`loudm` + redirect** | 2,285 | as above | **148 bytes** |

🔴 **The drop's own kernel and `quiet` reach the same 938 and both halt in
`bsp_machine_halt`.** That is a better control than §5 had: §5 compared against
*this unit's* kernel, which is a different tree with a different configuration,
and got 908 against 938. Here the vendor's prebuilt `vmlinux.elf` and my build
of the same source reach the identical depth, and only the halt address moves —
because `CFLAGS_KERNEL=-fno-if-conversion` and the initramfs move the layout.

### 15.4 🔴 The ladder prints, and `B07` has a value

`quietm` through the channel:

```
RLXFW-B00
RLXFW-B01
RLXFW-B02=00018000
RLXFW-B03
RLXFW-B04
RLXFW-B05
RLXFW-B06
RLXFW-B07=FFFFFFFF
```

then `bsp_machine_halt`, forever. **Eight of the eleven marks, in order, from an
image that has never been near the device.**

* **`B07 = 0xFFFFFFFF`.** `bsp_swcore_init()` returns −1 when the switch core
  does not answer, and the next four lines are `if (ret != 0) bsp_machine_halt();`
  — the designed, silent, unrecoverable hang §11.2 named. So the seating now
  carries **both** values: `RLXFW-B07=00000000` is the pass, and
  `RLXFW-B07=FFFFFFFF` followed by silence is the switch core not answering,
  read off the wire instead of inferred from the absence of everything after it.
* **`B02 = 0x00018000`** — and that is the point of `B02`. `0x00018000` is the
  `PRId` of qemu's 4Kc. On this die the same binary must print `0000CD01`
  (`CPU-04`, 量 2026-08-25b through `probe2`'s bare-metal CP0 census). **A
  constant cannot do that.** The mark is demonstrated to be a run-time read
  before the power cycle that depends on it, which is the strongest form the
  discriminator ladder has.
* **B08, B09, B10 do not appear**, and they should not: the channel halts inside
  `bsp_setup()`, before `paging_init()`.

### 15.5 The control that makes the output evidence, and the thing it found

`C5`, stated before the runs: **an image with no marks in it must print
nothing through the same channel.** 量:

* `quiet` + redirect → **0 bytes**. The variant that will be uploaded second is
  silent unless a mark runs.
* `loud` + redirect → **42 bytes**, and they are not a mark:
  `[    0.000000] CPU revision is: 00018000`.

🔴 **So `loud` is not silent before the console handover, and §11.1 did not say
it would be.** `CONFIG_EARLY_PRINTK=y` builds `arch/rlx/kernel/early_printk.c`,
which registers an `early_console` whose `write` goes through `prom_putchar`;
what §11.1 measured as a dead end is the `early_printk()` *function*, a weak
empty stub. With `CONFIG_PRINTK=y` the console path is live. The practical
consequences for the seating:

* the `loud` capture will carry vendor-format `printk` lines interleaved with
  the marks, and one of them is a **second reading of `PRId` in the same
  capture** — `CPU revision is:` beside `RLXFW-B02=`, from two different call
  sites;
* `PRINTK_TIME` is visible and reads `0.000000` here, which is the expected
  value before the timer interrupt starts (§11.6);
* and `RLXFW-B09` is no longer *the* line that says which instrument the rest
  of the capture came from — in `loud`, `printk` reaches the wire well before it.

⚠️ **Only one buffered line came out.** `CPU revision is:` is emitted at
`cpu_probe()`, between `B01` and `B02`, and it appears in the stream after
`B03` — so it was buffered and replayed when the console registered. The kernel
banner and everything else printed before that point did **not** appear.
Undetermined, and recorded rather than explained: it is a fact about what the
`loud` capture will look like, and guessing at `CON_PRINTBUFFER` here would
put an unmeasured sentence next to eight measured ones.

### 15.6 What the channel still cannot tell you

* **It is not D1–D5.** qemu's 4Kc has load interlocks, no RTL8196E peripherals,
  and a different `PRId`. `B02` printing `00018000` is the proof of that in one
  line.
* **It says nothing about the divisor.** `bsp_serial_init()` writes
  `0xB8002000`, which malta does not decode, so the CBUS UART keeps its own
  rate and `B05` arrives regardless. On the device that write is real, and
  `B05` is the line that separates a changed line rate from a failed
  `early_serial_setup` — the channel cannot exercise either.
* **It does not run the Lexra IMEM/DMEM setup at all**, by construction.
  `B06` arriving here means `_imem_dmem_init()` returned from a body that was
  four `nop`s.
* **The redirect is a change to the image under test.** Every instruction count
  in §15.3 is given for the unpatched image as well, and the redirect moves it
  by at most 1.

---

## 16. What could still be wrong

* **§1's decision rests on four readings of one vendor's tools.** `SPEC.md` §0's
  two-source rule is not satisfied by any of them alone; what is claimed is
  agreement among four readings of Realtek's own instruments plus this unit's own
  image, not corroboration by a second party.
* **§1.2's conclusion is about a microarchitecture nobody has asked.** The four
  sites are a hazard *if* `movz` reads `rd`, and that is `TC-h`, unmeasured.
* **§2's eleven hazards are counted by `hazlint` in a mode that has never
  produced a false positive on hand-written `arch/rlx` assembly** — and a
  classifier that has not been shown to be able to fire wrongly on this material
  is not the same as one that does not.
* **§5's channel runs a different core.** Everything it certifies, it certifies
  for a MIPS32 4Kc with interlocks, a malta memory map and no RTL8196E
  peripherals.
* **§3's pipeline is verified at stages 1 and 2 only.** The LZMA and `cvimg`
  stages are read out of the vendor's Makefile and confirmed by unwrapping two
  images; they have not been re-run to produce a byte-identical `nfjrom`. **And
  they have to be re-run**: the image is built from the kernel §8 configured and
  §9 filled, so the `nfjrom` this gate uploads does not exist yet.
* **§7's flag removes the sites without answering whether they were hazards.**
  If `TC-h` measures `movz` as write-enable on this die, 0.69 % of `.text` was
  bought for nothing — and the finding would be worth more than the bytes.
* **§7's count of 31 surviving conditional moves has not been looked at one by
  one.** `hazlint` says none is in a load delay slot, which is the property that
  matters; nothing here says what they are.
* **§8's `derive` classification is a measurement of one kconfig run, on one
  tree, on one host.** The experiment argues with all 21 at once and a negative
  control fires, but a symbol whose value depends on something not varied is
  outside what it tests.
* **§9's image has never been unpacked by a kernel.** `gen_init_cpio` produced
  29 entries and `cpio -it` lists 29; that the RLX4181 kernel's own
  `populate_rootfs` accepts them is untested, and it is D3/D4's to test.
* **The whole of §7's 0-violation result is `hazlint` reading 99.29 % of the
  executable sections.** The remaining 0.62 % is 39 named MIPS16 functions and
  20 named gaps. A four-byte scanner cannot read them, and this is a coverage
  figure with a list attached rather than a clean bill for every byte.
* **Nothing in this file has been executed on the device.** Not one number here
  is 量 in `SPEC.md`'s sense.
* **§10's sweep found nothing, and a sweep that finds nothing is the shape
  this project distrusts.** Two positive controls fire on the same command
  (`bsp_swcore_init` 0 → 1, `BSP_UART0_BASE` 0 → 2), so it can detect a false
  zero. What it does not cover is a conclusion drawn from a `grep -r` whose
  wording nobody wrote down: the fifteen tokens are the ones reconstructable
  from committed text, not a proof that the list is complete.
* **§10.4 changes what a "three-drop" BSP reading means, and the older ones
  have not been re-audited.** Anything in this repository citing
  `arch/rlx/bsp/...` was read through `rtl819x-toolchain`, the only drop where
  that path resolves. The bytes are right; the corroboration such a citation
  implies is not, until it is re-taken through `boards/rtl8196e/bsp/`.
* **§11's eleven marks have never executed.** Every claim about what they
  bracket is 讀 from the vendor's source plus 量 on the built image. That
  `prom_putchar` writes a UART still at 38400 when B00 runs is 推 — the loader
  printed at 38400 through the same registers and nothing between touches the
  divisor, but no byte of this has left the die.
* **`hazlint`'s controls got slower and it is a build gate.** 量: a full scan of
  the `R3` kernel 1.51 s → 3.41 s, the self-test 0.75 s → 2.72 s, seven
  subprocesses at about 0.28 s each. Accepted, because the alternative — running
  the `cli` controls only under `--self-test` — puts a different control set on
  the gate path from the self-test path, which is `TC-j` again.
* **§11.4's cost is measured on the image, not on the boot.** +127 bytes and
  ~32 ms of UART are arithmetic; what eleven synchronous UART writes do to a
  timing-sensitive `bsp_swcore_init` is unknown, and the `quiet`/`loud` pair
  does **not** separate it, because both carry the marks.
* **§11.6 decides `CONFIG_PRINTK` on a size budget and a config reading.**
  Neither says whether a kernel spending over a second in `prom_putchar` during
  driver init still brings the switch core up. That is what the first seating
  measures, and it is why `quiet` is built at all.
* **§11.7's corrected ceiling agrees with `objcopy` on THIS kernel.** Two
  routes, one artefact. A kernel whose `PT_LOAD` layout is not two contiguous
  segments would need that agreement re-established.

* **§13's byte identity is one artefact, not a property of the pipeline.**
  `nfjrom` reproduces for the drop's `vmlinux.elf`; nothing says a different
  kernel would not expose a `cvimg` or `lzma` version difference that this one
  happens not to reach. **And `lzma-24` is not excluded, it is unrunnable
  here** (§13).
* **§13's identity is not a comparison of a file with itself, and the proof of
  that is the row above it**: `memload-full`, the immediate parent of `nfjrom`,
  DIFFERS. Two pipelines that were secretly the same file would have matched
  there too.
* **§14's 0 is about `arch/rlx` plus the BSP -- 60 objects, 58,652 bytes.** The
  linked image is 2.4 MB of `.text`. `P2` covers the hand-written assembly and
  the board, which is where the claim lives; it is not a sweep of the kernel.
* **§15's channel prints eight marks on a core with a different `PRId`, no
  RTL8196E peripherals and load interlocks.** It shows the marks are reachable
  and computed. It shows nothing about whether they will reach 38400 8N1 on
  this die.

* **§12.2's image-identity words are the LINKER's, not the loader's.** They say
  what `__vmlinux_end` was when the image was built. A transfer that landed at
  the wrong *address* would still read them correctly at whatever address it
  landed on, and `DW` is pointed by hand. What they identify is **which image**,
  not **where**; `--expect-load` against the loader's own echo is what covers
  the address.
* **§12.3's before/after pair assumes nothing else writes above `image_end`
  between the two reads.** Nothing in the loader is known to, but nothing has
  measured it either — the region has never been read twice in one boot.
* **§12.5's `/proc/cpuinfo` comparison is against a reading taken through the
  vendor's own web shell**, not through a console. The values are the kernel's
  either way, but the path is not one this project controls, and `BogoMIPS`
  `398.95` is a single sample with no stated repeat.
* **§12.6 is two readings of the same disassembly**, mine and upstream's, of
  **one** binary. It is a stronger source than one reading and it is not two
  independent parties.
