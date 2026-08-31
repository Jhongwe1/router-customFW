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

`config/rlxfw-kernel.delta` — 🔄 **36 rules for `quiet` and 38 for `loud`** as
of 2026-08-30 (`CONFIG_MTD_CHAR`, §18.2); **35 and 37** when this paragraph was
written — each
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
file would be a copy of all the rules and a copy is a second owner. *(The count
was written here as 35 and is 36 since 2026-08-30; it is removed rather than
updated, because this sentence never needed one.)*

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

🔄 **2026-08-30: there are six. `quietmc` and `loudmc` are in §18.6 and not
here**, because this section is `R3-2`'s control — the pipeline reproducing the
vendor's own `nfjrom` byte for byte — and adding rows to its table would make
the control read as a list.

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

---

## 🔴 §16 — it booted. 2026-08-29, `bench/2026-08-30b/`, power cycle 2

`rlxfw-loudm-20260830.bin` — 1,053,696 bytes, sha256 `72928c56…`, the pipeline's
own `nfjrom` renamed — was uploaded to `0x80500000` over TFTP (2,059 blocks,
1.64 s) and entered with `J 80500000`. **It reached a shell and pinged.** All
five of `R3`'s DoD rows are met; `RUNSHEET` § Results — Session B5 owns the
row-by-row statement.

**The upload verified before the jump, and the tail check is the good one.**
`L-0t` read `806013F0` before the transfer and `L-2c` read it after: line 1 went
from DRAM bias to **sixteen zero bytes** (the write reached `image_end`) while
line 2 stayed **byte-identical** (it did not run past). One command carrying a
positive and a negative control, which is what §B5-c1 rebuilt the cell into once
the head was measured not to discriminate between `nfjrom` files.
`L-2a` matched both predicted lines, `0x8050001C` = `26101400` giving
`__vmlinux_end` = `0x80500000 + 1,053,696`; `L-2b` at `0x80540000` confirmed it
was `loudm` and not `quietm`.

### The mark ladder, and the byte model held

All eleven marks arrived in order, then M4:

```
RLXFW-B00 … B03, [    0.000000] CPU revision is: 0000cd01, B04 … B10,
rlxfw: init running, RLXFW-R3-RUNG1-OK
```

* **`RLXFW-B00`** is D2 — the first C instruction of this kernel reaching the
  UART, and a string absent from both vendor artefacts.
* **`RLXFW-B05` clean after a clean B04** — `bsp_serial_init()` did **not**
  change the line rate. That was §12's open risk (`B05` exists to make it one
  readable line) and it is closed in the good direction.
* **`RLXFW-B06`** — `_imem_dmem_init()`, the Lexra CP3 scratchpad sequence,
  returned. The desk channel skipped this body with `--nop-cop3`, so this is the
  first time it has executed anywhere. It is consistent with `probe3`'s
  independent finding the same evening that CP3 is reachable on this die.
* **`RLXFW-B07=00000000`** is D3 — the switch core answered and
  `bsp_machine_halt()`'s bare `while(1)` did not fire. The desk channel printed
  `FFFFFFFF` here because malta has no RTL8196E switch core.

**`PRId` is read three times through three paths in one seating**:
`RLXFW-B02=0000CD01` (upper case, `rlxfw_puts_hex`), `CPU revision is: 0000cd01`
(lower case, `cpu-probe.c:39`), and `/proc/cpuinfo`'s `cpu model : 52481` —
`0xCD01` in decimal. Three formatters, one register; the case and radix
differences are free proof they are three paths rather than one value copied.

⚠️ **`TC-o` reproduced on the device**: exactly one buffered `printk` line was
replayed when the early console registered — `CPU revision is:` — landing after
B03, as the desk channel measured. Not more. `TC-o` is answered in the measured
direction and its mechanism is still not explained.

### 🔴 Decision B's stated premise is false, and it is a safety statement

`PROGRESS.md`'s Decision B argues for initramfs with *"An initramfs boot **never
instantiates an MTD partition map**"*, and the danger it names is that a wrong
map covers the two regions `CLAUDE.md` forbids. 量, `L3.log`:

```
[    6.660000] SPI flash(UNKNOWN) was found at CS0, size 0x400000
[    6.670000] Creating 2 MTD partitions on "flash_bank_1":
[    6.680000] 0x000000000000-0x000000130000 : "boot+cfg+linux"
[    6.690000] 0x000000130000-0x000000400000 : "root fs"
```

**A partition map was instantiated, and its first partition spans
`0x000000–0x130000`, which contains both forbidden regions** —
`0x000000–0x005FFF` (the loader) and `0x006000–0x007FFF` (`H601`).

**Nothing was written**: `AUTOBURN` read `00000000` before every upload, the
payload issues no burn command, and no flash-write command appears in any of the
35 sent lines. ⚠️ **The flash-byte count is UNMEASURED** — no `FLR` bracket ran. The
map existing is not a write. But the reason Decision B was chosen is now known
to be false, and it has to stand on its other three legs — which it does, and
they were always the stronger ones (the drop's `FLASH_OFFSET` is not this unit's
layout; initramfs is the vendor's own supported path; userspace stays a
controlled variable). **The margin this project believed it had on the first RAM
boot was not there**, which matters more than the conclusion it does not change.

### Two smaller things the boot log settled

* **Six netdevs, and §B5-c9 named them exactly**: `eth0`…`eth4` and `eth7`.
  🔴 **The mechanism for the `eth5`/`eth7` disagreement is one line**:
  `rtl_nic.c:6479` prints the **array index `i`**, not `dev->name`, and index 5
  is the only entry the driver renames — `memcpy(dev->name, vlanconfig[i].ifname, 5)`
  guarded on `RTL_DRV_LAN_P7_NETIF_NAME`, which `rtl865x_netif.h:370` defines as
  `"eth7"`. **That matters more than a footnote**: it proves index ≠ name is not
  guaranteed, so the mask→netdev binding is 量 for the *masks* and 讀 for the
  *binding* — the boot log's `ethN` does not name a netdev at all. The binding is
  closed by the MAC tie in `L6a.log` and by `vlanconfig[]`, not by the boot line.
* 🔴 **I first wrote that the recorded port masks were wrong. They were not,
  and the sentence was false in both halves.** 量,
  `upstream/dumps/uart-boot.log`: the vendor firmware on this unit reports
  `eth0=0x10`, `eth1=0x1` (vid 8, WAN), `eth2=0x8`, `eth3=0x4`, `eth4=0x2`.
  The old record matched it exactly and excluded the WAN correctly; the mask
  I accused it of omitting, `0x1`, **is** the WAN's.
  🔴 **The two builds enumerate the switch MIRRORED, and that is the finding.** 量, side by side — `upstream/dumps/uart-boot.log`'s vendor boot against `bench/2026-08-30b/L3.log`: vendor `eth0=0x10 eth1=0x1(vid 8) eth2=0x8 eth3=0x4 eth4=0x2`, mine `eth0=0x1 eth1=0x10(vid 8) eth2=0x2 eth3=0x4 eth4=0x8`. As bit indices that is **`mine = 4 − vendor`** for every one of the five — a 5-bit reversal, with `eth3` at bit 2 as the fixed midpoint. **A member-port bit indexes a physical switch port, which the hardware fixes**, so the netdev↔jack binding differs between the two builds and a driver written against `NET-04` would drive the wrong jacks under my kernel. `RTL_WANPORT_MASK` has both `0x10` and `0x01` variants under different `#ifdef`s (讀, `rtl865x_netif.h:400`, `:411`), which is where the difference enters.
* `Initrd not found or empty - disabling initrd` appears and is **not** a
  failure: that message is about the legacy initrd mechanism, while this image
  carries its rootfs in `.init.ramfs`, which `populate_rootfs` unpacked — the
  shell it produced is the proof.

---

## 17. `R3-8b`: what `quietm` will print, and every term of the count is measured

**Written 2026-08-30 at the desk, before power cycle 3.** `L-3` reached D4, so
`RUNSHEET` §B5's own table selects `quietm` for the next cycle. This section is
what that image can and cannot put on the wire; the card and the cell-by-cell
predictions are `bench/2026-08-30c/PREDICTIONS-B5-block2.md`.

### 17.1 It is a one-variable experiment, and that is 量 rather than intent

量, `diff` of the two `.config` files the two images were built from
(`$FWRE_WORK/rebuild/r3-6/quiet.config` against `loud.config`): **two lines**.

```
226c226,227
< # CONFIG_PRINTK is not set
---
> CONFIG_PRINTK=y
> CONFIG_PRINTK_TIME=y
```

Same tree, same toolchain, same 15 declared mark rows, same initramfs spec, same
`CFLAGS_KERNEL=-fno-if-conversion` — read out of `quietm-build.txt` and
`loudm-build.txt` side by side. So a difference on the wire is attributable to
`CONFIG_PRINTK` and to nothing else that this build system can see.

### 17.2 The 401 bytes, term by term

Every term is 量, read out of `bench/2026-08-30b/L3.log` — the *same* kernel with
those two symbols on:

| | bytes | measured how |
|---|---:|---|
| `J 80500000` echo, the four `rtkload` lines, `start address: 0x80003600` | **169** | the byte slice from the file's start to the end of that line |
| eleven marks, `RLXFW-B00`…`RLXFW-B10` | **139** | nine plain × 11 + two valued × 20 |
| M4, `rlxfw: init running, RLXFW-R3-RUNG1-OK\r\n` | **40** | |
| `/bin/sh: can't access tty; job control turned off\r\n` | **51** | |
| `# ` | **2** | |
| **total** | **401** | |

**And the number it cannot be is measured in the same file**: `loudm` put
**6,459** bytes through that window. 🔴 **2026-08-30: the difference is 5,610, not 6,058, and it is not all `printk`.** *(Original: “the entire 6,058-byte difference is **105 `printk` lines**. 量.”)* 6,058 was `6,459 − 401`, and `quietm` measured **849** — so the same 448 bytes that were missing from the prediction were counted as `printk` here too. 量 `bench/2026-08-30c/V-3.log`: the difference is `6,459 − 849` = **5,610**, and the 448 are `rtlglue_printf`, which `CONFIG_PRINTK=n` does not remove (§17.8). The two totals are still impossible to confuse, which is what makes a single byte count a usable discriminator — and that half of the sentence was the half that mattered.

### 17.3 🆕 How long the boot actually takes, and it is not the number the card was sized against

量, `bench/2026-08-30b/L3.timing` against the offsets in `L3.log`:

| | t from `J` |
|---|---:|
| `start address: 0x80003600` | 1.137 s |
| `RLXFW-B00` | 1.157 s |
| `RLXFW-B07` | 1.195 s |
| `RLXFW-B10` | 8.925 s |
| the shell prompt | **8.98 s** |

🔴 **§B5's card sized `L-3`'s 90-second window against 26.05 s** — this unit's
*vendor* kernel. ⚠️ **That number is in `bench/2026-08-24c/G6.timing`, not in
`G6.meta.json`**, whose `duration_s` is the capture window, `60.076457`.
`RUNSHEET` §B5-c12 corrected exactly this citation once already, and both
`SPEC.md` `FW-27` and this paragraph reproduced the corrected-away form on the
day they were written. My kernel is **2.9× faster to
a shell**, so 90 s was 10× rather than 3.5×. 🔄 **2026-08-30: 量, `quietm` is 7.260 s (`bench/2026-08-30c/V-3.timing`), so the estimate was 1.9 % out — but the arithmetic that produced it was wrong.** *(Original: `quietm` prints 6,058 fewer bytes, which at the 38400 line rate of 3,840 B/s is 1.58 s less, so **≈ 7.4 s (推)**.)* It prints **5,610** fewer, which is 1.461 s of wire; the measured saving is 1.711 s, and the 0.250 s residual is **未定** with n=1 on each side (`SPEC.md` §17, `FW-32 殘留`).
⚠️ **3,840 is the line rate and this repo has measured the only wire rate it
has to be lower** — `LDR-40`, 3,458–3,497 B/s marginal for the *loader's* `DW`.
That measurement is of a different transmitter (the loader's reply path, not the
kernel's `prom_putchar` busy loop) so it does not transfer, but at 3,594 B/s the
same arithmetic gives 7.30 s and the window is unaffected either way and the block's window is
45 s — 6.1× the prediction and still 1.7× the vendor kernel's own figure, which
is the number to be safe against if the ladder stalls somewhere no channel has
reached.


#### 17.3a The landmark segmentation, and the method rather than the script

量 2026-08-30 from `bench/2026-08-30c/V-3.timing` and `bench/2026-08-30b/L3.timing`.
**Method, because the script is a scratchpad one and is not committed**: the
`.timing` sidecar is `offset seconds` pairs where `offset` is the byte count in
`.log` **before** that read; for a landmark at byte `b`, take the first pair
whose `offset >= b` and subtract the first pair's time. Every figure below is
relative to the first read.

| landmark | `quietm` | `loudm` |
|---|---:|---:|
| `start address:` | 1.095 s | 1.137 s |
| `RLXFW-B00` | 1.116 s | 1.144 s |
| `RLXFW-B07` | 1.141 s | 1.182 s |
| `RLXFW-B09` | 1.157 s | 1.418 s |
| `RLXFW-B10` | 7.203 s | 8.912 s |
| last byte | **7.260 s** | **8.971 s** |
| **`B09` → `B10`** | **6.046 s** | **7.494 s** |

**Ten of the eleven marks land inside 1.16 s and the whole of the rest is the
`B09`→`B10` window**, in both builds — that window is `console_init()` returning
through the switch-core and driver bring-up.

⚠️ **`FW-27`'s `loudm` figures are ABSOLUTE capture times and these are relative
to the first read**; the two agree only because the anchor is 12 ms, so
*"the same script reproduces `FW-27`"* is a coincidence of magnitude rather than
a control. Stated because `SPEC.md` carried the claim without the caveat.

⚠️ **`tools/boot-timeline.py` does NOT do this** — it separates cold boots from
warm resets and takes a directory, not a file. 量: it runs cleanly on
`bench/2026-08-30c` and on `bench/2026-08-30b`. *(An adversarial reviewer read
its refusal on a FILE argument as a refusal of this seating's captures; the same
refusal fires on `bench/2026-08-24c/G6.log`, so it discriminates nothing. The
control is what settled it.)*

### 17.4 What survives `CONFIG_PRINTK=n`, read out of the tree and out of the artefact

| | | source |
|---|---|---|
| the eleven marks | **arrive** | `rlxfw_puts` → `prom_putchar`; no console and no `printk` in the path (讀) |
| `[    0.000000] CPU revision is: 0000cd01` | **absent** | it is `arch/rlx/kernel/cpu-probe.c:39`'s `printk` (讀). 量 on the desk channel: `quietm` emits **106** bytes where `loudm` emits **148**, and 148 − 106 = 42 is exactly that line |
| the 105 `printk` lines between B04 and B10 | 🔴 **REFUTED ON THE WIRE 2026-08-30 — fifteen of them ARRIVE** | 量, `bench/2026-08-30c/V-3.log`: 448 bytes of Realtek driver output between `RLXFW-B09` and `RLXFW-B10`. They were never `printk` — they are `rtlglue_printf`, which 讀 `include/net/rtl/rtl_types.h:366` `#define`s to `panic_printk` with no Kconfig symbol in the way. §17.8 |
| the console, and therefore userspace | **arrives** — and it did (量, `V-3.log` reaches a prompt) | 🔄 **The conclusion holds and the source was the wrong file.** *(Original: 讀 `kernel/printk.c`: the `#ifdef CONFIG_PRINTK` spans `:132`–`:539`, while `console_setup()` is at `:802` and `register_console()` at `:1123` — outside it.)* 🔴 量 2026-08-30, `kernel/Makefile:5`: `ifdef CONFIG_RTL_819X` builds **`printk_log.o` instead of `printk.o`**, and `CONFIG_RTL_819X=y` here — so **this board does not compile `kernel/printk.c` at all**. Control: in both built trees `kernel/printk.o` is absent and `kernel/printk_log.o` is present, exactly one of the two. §17.8 |
| 🔴 a **panic**, if it panics | **arrives** | 讀 `kernel/panic.c:27`, `#define printk panic_printk` under `CONFIG_PANIC_PRINTK`; 讀 `init/Kconfig:843`, that symbol is `bool` with **no prompt** and `default y`, so it is not settable and is `=y` in both configs (量). 量 on the built `vmlinux`: `panic_printk` is a **GLOBAL FUNC in `quietm`'s symbol table** and `<0>Kernel panic - not syncing: %s` occurs **once**, while the global `printk` is gone (only three file-local ones remain) |

🔴 **That last row is what makes silence mean something.** In `quietm`, silence
after a mark is a **hang**, not a panic that was suppressed.
⚠️ And the chain's last link is 推: no channel has ever made this build panic, so
*the panic path reaches the UART* has not been observed anywhere.

### 17.5 The addresses that moved with the image

量, on `rlxfw-quietm-20260830.bin` itself (1,027,072 bytes, sha256
`cf8a93d73025292d…`):

| | `loudm` | `quietm` |
|---|---|---|
| `image_end` | `0x80601400` | **`0x805FAC00`** |
| the tail read, `image_end − 0x10` | `0x806013F0` | **`0x805FABF0`** |
| word at file `0x18` / `0x1C` | `3C108060` / `26101400` | `3C108060` / **`2610AC00`** |
| the variant word at `0x80540000` | `CEC3FFD9 …` | **`AFBD0BEE AE8D991B A39DEE9F 2A62E61B`** |
| trailing zero run | 688 B | **552 B** |
| clearance above the staged vendor image's end (`0x805F1002`) | 66,542 B | **39,918 B** |
| the build stamp | `#1 Fri Aug 28 23:37:47 CST 2026` | **`#1 Fri Aug 28 23:39:33 CST 2026`** |

🔴 **`MAP-17` was struck from the row above on 2026-08-30, and this is the third time that citation has had to be removed.** That row is *selected*: its own value column is `—`, so it cannot be a source for `0x805F1002`. The number is 讀 the flash header's `len` = `0x0F1002` (`FLM-09`) **plus** the inference that the loader copies exactly `len` bytes to `startAddr` — 讀 ＋ 推, and not 量. `SPEC.md` `LDR-39` owns it. `bench/2026-08-30c/PREDICTIONS-B5-block2.md` §5 caught it in the card; §12.3 and `RUNSHEET` §B5-c5 each caught it once before; **it was still here.**

The build stamp has two sources that are not each other: `RUNSHEET` §B5's
power-cycle-3 table, and 量 — `strings` on the `quietm` `vmlinux` (3,968,240
bytes, sha256 `dd0c1190f3646561…`, the output `quietm-build.txt` records) finds
`#1 Fri Aug 28 23:39:33 CST 2026` **once**, beside `linux_proc_banner`'s
`%s version %s (key@K) (gcc version 3.4.6-1.3.6) %s`.

### 17.6 🔴 What `quietm` takes away, and it is not only noise

🔴 **REFUTED 2026-08-30, and this section held two claims that look alike and are not.**

*(Original: “The netdev registration lines are `printk`. Under `loudm` the netdev↔switch-port binding was 讀 straight off `L3.log:99-104`; under `quietm` those lines do not exist. On power cycle 3 the binding is 推, carried over from cycle 2…”)*

量, `bench/2026-08-30c/V-3.log`: **all five `ethN added. vid=… Member port …` lines are there**, and they agree with `L3.log` cell for cell — `eth0` `0x1`, `eth1` `0x10` (vid 8), `eth2` `0x2`, `eth3` `0x4`, `eth4` `0x8`. **The binding is 讀 on power cycle 3, not 推.** They are `rtlglue_printf` (`rtl_nic.c:6479`), not `printk` — and the same file prints the same sentence through `printk` at `:10515` with a `==%s(%d)` prefix, which the capture does **not** carry. §17.8.

🔴 **A sixth line came with them and this paragraph called it unpredicted — while §16 of this same file, 155 lines above, already explains it.** *(It read: “A sixth line came with them and nothing predicted it: `eth5 added. vid=9 Member port 0x0`, while `V-6a`'s 23 interfaces contain no `eth5`.”)* §16: `rtl_nic.c:6479` prints the **array index**, not `dev->name`; index 5 is renamed to `eth7` via `RTL_DRV_LAN_P7_NETIF_NAME`. 量, `V-6a.log` lists **`eth7`** — the netdev is in userspace under its other name, and the capture cited as showing it missing is the capture that shows it. **A correction that re-opens a closed question is worse than no correction.**

The host capture's `-e` was kept regardless and earned its place on its own: the ARP request's source MAC is `00:12:34:56:78:94`, and the last octet names `eth4` without the board being asked.

🟢 **The other half of this section HELD, and the seating is what separated them.** The MTD partition table — `Creating 2 MTD partitions on "flash_bank_1"` and the two ranges — **is** `printk`: 量, those lines occur **zero** times in `V-3.log`. So the map that made Decision B's safety leg false is invisible on this boot, it is still created, and `bench/2026-08-30b/L3.log` remains the reading.

🔴 **Two claims, one paragraph, one mechanism assumed for both, and only one of them was true.** The reason the netdev half was wrong is that nobody asked *which* printing function — `printk` was assumed because the lines look like kernel log lines. §17.8 is the answer that was missing.

### 17.7 🔴 Why the flash cannot be cross-read from userspace on this image

The `FLR` bracket reads flash through the **loader**. A second, independent path
exists in principle — my own MTD stack, from the shell — and it is not available,
for two measured reasons rather than out of caution:

1. 量, this unit's own `busybox`, by two routes that share no code — every
   symlink in the extracted tree pointing at it (**exactly 50**) and the
   applet-name table in the binary itself: **`dd`, `md5sum`, `od`, `hexdump`,
   `cmp`, `cksum`, `sum` and `sha1sum` are none of them.** There is nothing in
   this device's userspace that can digest a stream. `notes/rootfs-census.md`
   owns the census and records that `mknod` is the `uname` false positive again
   — `strings` finds it, the applet table does not.
2. 讀 `config/rlxfw-initramfs.tsv`: **three** device nodes were declared —
   `/dev/console`, `/dev/null`, `/dev/tty` — and no `/dev/mtd*`. A fourth was
   added 2026-08-30 and it is **not** the one this section asked for.

The node is one declared line and costs nothing. **The digest is the problem**: a
content check needs a binary that is not this unit's, and Decision B's third leg
is *the contents are this unit's own binaries, unmodified; if the shell does not
come up, the shell is not the new thing*. What the node alone buys is a
**readability and size** reading through my own driver and not a content one.
`R3-9` owns it.

### 17.7a 🔴 The node this section named cannot exist, and the obvious substitute is the dangerous one

**量 2026-08-30 at the desk, before the line was written**, two routes with a
positive control on each:

| route | reading | its control, in the same command |
|---|---|---|
| 讀 `r3-4/out/{quietm,loudm}.config-built` | `# CONFIG_MTD_CHAR is not set`, **both** images | the same grep finds **9** other `^CONFIG_MTD` lines in the same file |
| 量 both `System.map`s | **0** mtdchar-only symbols (`mtd_open`, `init_mtdchar`, `mtd_ioctl`, `mtd_lseek`, `mtdchar_notify_*`) | **6** mtdblock/mtdcore symbols (`init_mtdblock`, `mtdblock_readsect`, `mtd_read_proc`, `add_mtd_partitions`, `register_mtd_blktrans`, `mtdblock_open`) |

So major 90 has no registered chrdev and `wc -c < /dev/mtd0` would read
`No such device`. **A step whose whole purchase was one number would have spent
a bench cell on an error message.**

🔴 **And `/dev/mtdblock0` — the obvious substitution — is the one node this
project must not create.** `CONFIG_MTD_BLOCK=y`, and 讀 `drivers/mtd/mtdblock.c`
`.major = 31, .part_bits = 0`, so `mtdblock<N>` is `b 31 N`. mtd0 is
`boot+cfg+linux`, `0x000000`–`0x130000` = **1,245,184 bytes** (量
`bench/2026-08-30b/L3.log:113`), **which contains both regions `CLAUDE.md`
forbids writing** — the loader and
`H601`. `mtdblock` has a write path (`mtdblock_writesect`, a read-modify-erase-
write of a whole erase block), and **mode `0400` is not a control**: root ignores
DAC, so on an interactive shell `echo x > /dev/mtdblock0` is one typo from an
erase-block write at offset 0 on a device with no spare.

**`/dev/mtdblock1` buys the same reading and leaves no writable node over either
forbidden region.** It runs the identical `mtdblock_readsect` → `part_read` →
`rtl819x_flash` path, so it exercises the same driver; the control is the
**absence** of a node, not the mode bits. Two agreeing sources for its size:

* 量 `bench/2026-08-30b/L3.log:114` — `0x000000000130000-0x000000400000 : "root fs"`
* 讀 `drivers/mtd/maps/rtl819x_flash.c` with this build's own
  `CONFIG_RTL_ROOT_IMAGE_OFFSET=0x130000`, `WINDOW_SIZE 0x400000`,
  `CONFIG_RTL_FLASH_DUAL_IMAGE_ENABLE` and `CONFIG_RTL_TWO_SPI_FLASH_ENABLE`
  both unset — `size = WINDOW_SIZE - CONFIG_RTL_ROOT_IMAGE_OFFSET = 0x2D0000`

`0x400000 − 0x130000 = 0x2D0000` = **2,949,120**. ⚠️ The first draft of the
declaration wrote **2,818,048**, which is `0x2B0000` and a subtraction error; the
second source is what caught it, which is the argument for having one.
🔴 **The opening backtick of that first span was unclosed until 2026-08-30**, so the
whole sentence rendered as one code span and `0x2B0000` — the number it is about —
rendered as prose. Neither `C8b` (tables only) nor `C9` (whitespace-only spans) can
see it; `C10` is the check that now does.

**Cells, and both are cheap**: `cat /proc/mtd` first — it prints the map from my
own driver and reads **zero flash bytes** (`mtd_read_proc` is in both
`System.map`s) — then `wc -c < /dev/mtdblock1`, which must print `2949120`.
**Refuted by** any other number, by `No such device` (the block driver did not
register), or by a hang (the SPI read path does not complete).

🔴 **The declaration is AHEAD of every artefact that exists.** The node is in no
built image on 2026-08-30, and specifically not in `rlxfw-quietm-20260830.bin`,
which `bench/2026-08-30c/PREDICTIONS-B5-block2.md` uploads — that card's `V-0t`
and `V-2c` read `0x805FABF0` because they know where **that** image's
`image_end` sits, so the rebuild that lands this node moves them. Turning
`CONFIG_MTD_CHAR=y` on and declaring `/dev/mtd0ro` (`c 90 1`, where 讀
`mtdchar.c`'s `mtd_open` **enforces** read-only: `if ((f_mode & FMODE_WRITE) &&
(minor & 1)) return -EACCES`) is strictly better than any mode bit and is the
right long-term answer; it costs a kernel rebuild and is carried forward rather
than taken between a card's desk validation and its seating.

### 17.8 🔴 `CONFIG_PRINTK=n` does not make this kernel quiet, and the reason is in the vendor's own headers

**Measured on the wire before it was read out of the tree.** `quietm` was built
with `# CONFIG_PRINTK is not set` and it printed 849 bytes where the prediction
said 401 — 448 of them fifteen lines of Realtek driver output between
`RLXFW-B09` and `RLXFW-B10`.

**The chain, one link at a time:**

| | link | how |
|---|---|---|
| 1 | `drivers/net/rtl819x/rtl_nic.c:6213`, `:6479` and `AsicDriver/rtl865x_asicL2.c:4381` emit these lines with **`rtlglue_printf`** | 讀 |
| 2 | `include/net/rtl/rtl_types.h:366` — `#define rtlglue_printf panic_printk`, inside `#if defined(__linux__) && defined(__KERNEL__)`. **No Kconfig symbol gates it** | 讀 |
| 3 | `include/linux/kernel.h:271-276` — with `CONFIG_PRINTK` unset, `printk` becomes `static inline int __cold printk(const char *s, ...) { return 0; }` while **`panic_printk` is still declared `asmlinkage`**, in the `#else` branch, deliberately | 讀 |
| 4 | `kernel/printk_log.c:668` — `panic_printk`'s body is `vprintk(fmt, args)`, under `#if defined(CONFIG_PANIC_PRINTK)`, which `init/Kconfig:843` gives no prompt and `default y` | 讀 |
| 5 | `kernel/Makefile:5` — `ifdef CONFIG_RTL_819X` puts **`printk_log.o`** in `obj-y` **in place of `printk.o`** | 讀 ⚠️ *(this row said 量; a Makefile is code, and the 量 belongs to the control below it, which reads the built tree)* |
| 6 | `quietm`'s `System.map`: `panic_printk` **`T` at `0x80015204`**, `vprintk` **`T` at `0x80014ef0`**, `printk` three **`t`** stubs | 量 |

**Controls, because five of those six are readings of source:**

* In both built trees `kernel/printk.o` is **absent** and `kernel/printk_log.o`
  is **present** — exactly one of the two, which is what makes step 5 a
  measurement of this build rather than of the Makefile.
* `rtl_nic.c:6213`'s format string opens `"\n\n\n"` and the capture carries
  exactly three blank lines before that line.
* `rtl_nic.c` prints the **same sentence twice**: `:6479` via `rtlglue_printf`
  and `:10515` via `printk` with a `==%s(%d)` prefix. The capture carries the
  first and not the second — a discriminator inside one file.

#### 🔴 The number that answers this is 97, and 274 was published for about an hour

量 2026-08-30, relocations naming each symbol across the built objects:

| population | `quietm` (`PRINTK=n`) | `loudm` (`PRINTK=y`) | |
|---|---:|---:|---|
| whole tree → `panic_printk` | 1,594 | 719 | 🔴 **moves — unusable** |
| whole tree → `printk` | 0 | 6,407 | |
| `drivers/net/rtl819x/**/*.o` → `panic_printk` | 274 | 274 | 🔴 **a glob artefact** |
| the same, **excluding `built-in.o`** | **97** | **97** | ✅ the call-site count |
| `drivers/net/rtl819x` → `printk` (leaves) | **0** | 998 | ✅ the discriminator |

🔴 **This section caught one bad population and published another in the same table, and the adversarial pass caught the second.** *(It read: "The number that answers this is 274.")* `drivers/net/rtl819x/**/*.o` matches **28** objects, **seven of which are `built-in.o`** — `ld -r` aggregations of the leaves beside them — so a call site is counted two or three times. 量: all `*.o` = 274, excluding `built-in.o` = **97**, and the top-level `built-in.o` **alone** = 97, so `97 + 97 + 40 + 40 = 274`. **97 is the call-site count**; the leaves are `rtl865x_proc_debug.o` 41, `rtl865x_asicCom.o` 25, `rtl865x_asicL2.o` 11, `rtl_nic.o` 11, `rtl865xc_swNic.o` 5, `96E/rtl865x_asicBasic.o` 4.

🔴 **And the same contamination is in the whole-tree number twice over**: at the tree root sits `vmlinux.o`, a whole-image aggregate a `-name '*.o'` glob counts as a leaf even after `built-in.o` is excluded (270 quiet / 145 loud). The obvious summary — *"1,594 call sites survive `CONFIG_PRINTK=n"`* — is a count of a **moving, multiply-counted** population and must not be quoted. The tree redefines both
names in **both directions** in at least eight files:
`drivers/net/wireless/rtl8192e/8192cd.h:140` is `#define panic_printk printk`
and `8192cd_mp.c:65` is `#define printk panic_printk`. On
`drivers/net/rtl819x` — the driver that actually printed — the count is
identical in both builds and the `printk` column is what moves.

🟢 **The control that makes "identical" mean mechanism rather than coincidence was missing and is now here**: **22 of those 28 objects are byte-different** between the two builds (`cmp` per file), and across exactly that material `panic_printk` holds at 97 per file while `printk` goes **998 → 0**. A count that does not move across binaries that genuinely differ, beside one that collapses, is a mechanism.

🔴 **And the divergence in the whole-tree figure has a location**: it is *entirely* in `drivers/net/wireless/rtl8192cd/`, Δ 250 — `rtl8192cd.o` 127/2, `8192cd_mp.o` 64/2, `8192cd_ioctl.o` 45/0, `8192cd_proc.o` 7/0, `8192cd_sme.o` 5/0, `8192cd_hw.o` 4/0, `8192cd_osdep.o` 2/0. Every other object in the tree is identical. That is `8192cd.h:136` in action, and it is a finding rather than noise: **the quiet config moves 250 WLAN call sites onto the ungated path.**

#### What this changes

🔴 **`CONFIG_PRINTK` is a variable over the function `printk()`, not over
console output.** §17.1 calls `quiet`/`loud` a one-variable experiment and that
is still true of the *symbols*; what was wrong is the assumption about what the
variable controls. `TC-31` and `SPEC.md` `FW-31` carry the corrected statement.

🟢 **And §17.4's key sentence gets stronger rather than weaker.** *"In
`quietm`, silence after a mark is a hang, not a suppressed panic"* now rests on
more than the panic path: **97 `panic_printk` call sites in the driver directory are
compiled in and `CONFIG_PRINTK=n` removes none of them**. ⚠️ *(This read "are also live …
so silence is the absence of all of them", which is an absence treated as evidence: 量 says
seven of the 97 fired on this boot, and nothing has shown the other 90 can reach the UART on
this build.)* What silence after a mark rules out is the seven that did fire, and the panic
path. ⚠️ The last link is still
推 — no channel has made this build panic, so *the panic path reaches the UART*
remains unobserved — but the driver half of it was observed tonight.

⚠️ **What this does not say.** It does not say `quietm` prints everything
`loudm` prints: 5,610 bytes did not arrive, and those are `printk`. It does not
identify which of the 97 sites can fire on a boot — and 量, the fifteen lines that came out
are **seven** call sites, not fifteen (`rtl_nic.c:6479` is one call in a six-iteration loop
and `:6213` is one format string worth four lines, three of them blank). **A call-site count
is not a line count**, and this section used them interchangeably until the adversarial pass.
⚠️ **Two of the fifteen are not in this directory and not `rtlglue_printf` at all** —
`drivers/net/wireless/rtl8192cd/8192cd_osdep.c:6978` and
`net/rtl/fastpath/fastpath_common.c:1643` are direct `panic_printk` calls, 77 bytes, 17 % of
the 448. And it says nothing about `panic_printk`'s behaviour
before `console_init()`, which is `TC-29`'s question and is unchanged.


---

## 18. `R3-9`'s rebuild: a flash path the kernel will not let anything write

**Written 2026-08-30 18:29, at the desk, BEFORE the build was started.** The
ordering evidence for this section is the commit and this file's mtime, and it
is deliberately not `check-predictions.py` — that tool resolves a cell to
`bench/<prefix>.log` and cannot see a desk build. Said here rather than left
implied, because an ordering discipline that quietly does not apply is the shape
this repository keeps catching itself in.

### 18.1 Why a rebuild, and why today rather than any other day

Three rows had been carried forward waiting for a kernel build, and one of them
is a contradiction rather than a want: `config/rlxfw-initramfs.tsv` declares a
device node that is **in no built image**. A declaration ahead of every artefact
is a document that describes something that does not exist.

The scheduling argument is the one that decided the day. A rebuild moves
`image_end`, so it invalidates the `V-0t`/`V-2c` addresses on any prediction
card that is pinned to an image's sha256. `bench/2026-08-30c/PREDICTIONS-B5-block2.md`
is **spent** — it ran on 2026-08-30 — and the next card is not written. So today
is the one day on which a rebuild costs no rewritten card, and building after the
next card is written would cost exactly one.

⚠️ **The old artefacts are not disturbed, and that was checked rather than
assumed.** 量: `tools/rlxfw-kbuild.sh` writes `$R/out/<cell>.{config-built,
config-installed,oldconfig.log,build.log,System.map,vmlinux.elf}` and stages
into `$R/cells/<cell>`, both keyed on the cell name. New cell names leave
`quietm`'s and `loudm`'s outputs where `FW-27`, `FW-31` and `FW-32` point.
量: 915 G free on this host, and one cell is about 475 MB.

### 18.2 The one config change, and the prediction that it asks kconfig nothing

`CONFIG_MTD_CHAR=y`.

| | | |
|---|---|---|
| 讀 | `drivers/mtd/Kconfig:175` | `tristate "Direct char device access to MTD devices"`, with **no** `depends on` line of its own |
| 量 | the whole drop | `depends on MTD_CHAR` — **0** hits; `select MTD_CHAR` — **0** hits |
| 讀 | `drivers/mtd/Makefile:18` | `obj-$(CONFIG_MTD_CHAR) += mtdchar.o` is the symbol's only consumer |
| 讀 | `include/linux/mtd/mtd.h:21` | `#define MTD_CHAR_MAJOR 90` |

**`P18-1`, and it is §6.6's trap asked in advance:** `(NEW)` stays at **0** in
both `oldconfig` logs. Setting `CONFIG_PRINTK` alone took `(NEW)` from 0 to 1
because it made `CONFIG_PRINTK_TIME` reachable; the four readings above are the
reason to expect nothing of that shape here. **Refuted by** any `(NEW)` line in
either `<cell>.oldconfig.log`, in which case the symbol it names is pinned in
the delta the same way `PRINTK_TIME` was.

**`P18-2`:** exactly **one** symbol line differs between `quietm.config-built`
(2026-08-28) and the new quiet cell's — `# CONFIG_MTD_CHAR is not set` becoming
`CONFIG_MTD_CHAR=y`. **Refuted by** a second differing line.

**`P18-3`, the positive control that the change reached the artefact rather than
the tree:** §17.7a measured **0** mtdchar-only symbols in both `System.map`s,
against 6 mtdblock/mtdcore symbols in the same command. The new maps must carry
`mtd_open`, `mtd_read`, `mtd_lseek`, `mtd_ioctl` and `init_mtdchar`. **Refuted
by** any of them still absent — which would mean the config moved and the build
did not. This is `rlxfw-marks.py`'s own distinction between `check` and
`verify`: only the second reads the built artefact.

**`P18-4`:** the decompressed image grows by **fewer than 65,536 bytes**, so the
ceiling stays under 68 % of 5,242,880. ⚠️ **The point estimate inside that bound
is a guess and is labelled one** — the last estimate of this shape (`CONFIG_PRINTK`,
"150–300 KB") was wrong by 2–4×, which is why the claim written down is a bound
and not a figure. Measured values go in §18.6 beside `quietm`'s 3,472,384 and
`loudm`'s 3,546,112.

### 18.3 🔴 The node set: odd minors only, and `/dev/mtdblock1` is withdrawn

**Two enforcements, and only one of them depends on anything being configured
correctly.** 讀 `drivers/mtd/mtdchar.c`, `mtd_open`:

* `if ((file->f_mode & FMODE_WRITE) && (minor & 1)) return -EACCES;` — an **odd**
  minor cannot be opened for writing, unconditionally, by the kernel.
* `if ((file->f_mode & FMODE_WRITE) && !(mtd->flags & MTD_WRITEABLE)) ...` — the
  second test, which depends on how the partition was registered.

The first is stronger than any mode bit, because root ignores DAC. So the five
nodes this image declares are:

| node | dev | what it reads | writable? |
|---|---|---|---|
| `/dev/console` | `c 5 1` | — | — |
| `/dev/null` | `c 1 3` | — | — |
| `/dev/tty` | `c 5 0` | — | — |
| **`/dev/mtd0ro`** | `c 90 1` | `mtd0`, `0x000000`–`0x130000` — the loader **and** `H601` | **no**, `minor & 1` |
| **`/dev/mtd1ro`** | `c 90 3` | `mtd1`, `0x130000`–`0x400000`, the vendor rootfs | **no**, `minor & 1` |

🔴 **`nod /dev/mtdblock1 b:31:1` is withdrawn, and the reason is that it was the
best answer available while `CONFIG_MTD_CHAR` was off.** §17.7a chose it over
`/dev/mtdblock0` because `mtdblock` has a write path and mtd0 holds the two
regions `CLAUDE.md` forbids; its stated purchase was *a readability and size
reading through my own MTD stack*, `wc -c` printing 2,949,120. `/dev/mtd1ro`
buys that same reading over the same partition through `mtd_read` → `part_read`
→ `rtl819x_flash`, and leaves **no writable flash node in the image at all**.
What withdrawing it costs is the block layer — `mtdblock_readsect` and the
blktrans request queue — which no step of `R3` exercises and which `R5b` will
want. It comes back in the build that needs it, declared then.

🟢 **And the control is now complete rather than argued.** §17.7a's sentence was
*the control is the absence of a node, not the mode bits*, and absence is only a
control if nothing can create one. 量, `notes/rootfs-census.md`: `mknod` is **not**
among this `busybox`'s fifty applets — by the applet-name table in the binary,
not by `strings`, which is the false positive that file already documents twice.
So the declared set is the complete set of device nodes this image can ever hold,
and a mistyped `/dev/mtd0` at the shell is `No such file or directory` rather
than a writable handle on the loader.

**`P18-5`, and its negative control is free.** The cpio inside the new `vmlinux`
holds exactly the declared set: five device nodes, `/dev/mtdblock1` absent,
`/dev/mtd0ro` `c 90 1` and `/dev/mtd1ro` `c 90 3` present. This is checked by
`mkinitramfs verify`, new in this step, which reads the built artefact and not
the tree. **Refuted by** any difference. The negative control is the same command
against `r3-4/out/quietm.vmlinux.elf` from 2026-08-28: it must **fail**, and it
must name exactly the three differences above — a verifier that passes on the old
image is one that is not reading the image.

### 18.4 What the bench cells will be, written now so the card copies rather than invents

| cell | command | prediction | refuted by |
|---|---|---|---|
| `M-a` | `cat /proc/mtd` | two partitions, `0x00130000` and `0x002d0000`, names `boot+cfg+linux` and `root fs` | any other map. Reads **zero** flash bytes — `mtd_read_proc` prints the driver's own table |
| `M-b` | 🔄 **`busybox wc -lc < /dev/mtd0ro`** *(was `wc -c < /dev/mtd0ro`)* | **`␣␣␣␣␣4422␣␣␣1245184`** | any other number; `No such device` (no chrdev registered); `Permission denied` (the odd-minor rule is not what it says); a hang; 🔴 **the byte count right and the line count wrong → the read path truncates (§19.1)** |
| `M-c` | 🔄 **`busybox wc -lc < /dev/mtd1ro`** | **`␣␣␣␣␣7943␣␣␣2949120`** | as above, against 7943 |
| `M-d` | `echo x > /dev/mtd0ro` | **`Permission denied`** | anything else — and a **success** here is a stop-if for the whole seating |


🔴 **2026-08-31: both corrections above are why this table exists, and both were
found by running it.** ① **`wc` is not in the image** — it is one of busybox's
fifty applets and not one of the eleven declared symlinks, so the bare form
returns `/bin/sh: wc: not found`. **Use `busybox <applet>` for anything outside
`sh ash cat echo ls mount ps ifconfig ping mkdir sleep`.** ② **`-c` alone cannot
check content**: it counts what `read()` returns, so a silently truncating
`copy_from` would pass it. `-lc` costs the same read and separates the two by
≥3.6×. ⚠️ **And multi-field `wc` output is column-padded (19 chars) while the
single-field form is not** — §19 and `notes/rootfs-census.md` own that.

🟢 **`M-b` and `M-c` buy more than a size, and it is worth saying because the
obvious reading undersells them.** `wc -c` on a character device has no shortcut:
讀 `mtd_read`, every byte is read through `part_read` → `rtl819x_flash`. So the
two cells together read **4,194,304 bytes — the whole part — through a path the
kernel will not let anything write**, and `M-b` alone reads all 8,192 bytes of
`H601`. ⚠️ **That is not a content check and does not move `FLS-20`'s 0.0183 %**:
nothing compares the bytes to anything, because this userspace has no digest
applet. What it does establish is that the *path* works end to end over the
region a wrong write cannot be undone in — which is the prerequisite for any
future full read, and it costs two typed commands.

`M-d` is the positive control on the safety property itself, it costs no flash
bytes because the `open` fails before any write is issued, and it is the only
one of the four that can fail in the direction that matters. 讀 `mtd_read`:
`if (*ppos + count > mtd->size) count = mtd->size - *ppos;` then
`if (!count) return 0;` — a clean EOF, which is why `wc -c` terminates on a
character device at all.

⚠️ **None of this is a content check, and the sentence `G8b` forbids is still
forbidden.** This userspace has no `dd`, `md5sum`, `od`, `hexdump`, `cmp`,
`cksum`, `sum` or `sha1sum` (量, two routes, `notes/rootfs-census.md`), so
nothing here reads a byte of `H601` and compares it to anything. What the two
nodes buy is size, readability, and a path over the forbidden region that is
provably unable to write it.

⚠️ **One source in three copies.** 量 2026-08-30: `mtdchar.c` is byte-identical
across the three GPL drops that carry it, md5 `83d6fc7bbec987be1cbca27d8bc006bd`
— the same weakness that travels with the `PRId` assignment table. The
enforcement is read, not measured, until `M-d` runs on the silicon.

### 18.5 🔴 The rebuild reproduced nothing, and the reason is a flag no committed file carries

**量 2026-08-30, and it was found by a size that made no sense rather than by a
check.** The first pass of this rebuild produced a `quietmc` whose `.text` was
**11,836 bytes SMALLER** than `quietm`'s, with `+12 / −0` symbols. Adding a
driver does not shrink `.text`, and both variants moved the same way, so the
config was not the cause.

**The ladder, each rung its own build:**

| | build | `.config` | `-j` | `.text` | verdict |
|---|---|---|---|---:|---|
| 1 | `quietm` | quiet | 8 | 2,444,228 | 2026-08-28, the image that BOOTED |
| 2 | `quietmc` | quiet + `MTD_CHAR` | 4 | 2,432,392 | today, first pass |
| 3 | `rep8` | **`quietm.config-installed`, byte for byte** | 8 | **2,427,448** | today |
| 4 | `rep4` | the same file | 4 | **2,427,448** | today |

Rungs 3 and 4 are identical, so **`-j` is not the variable** — which had to be
excluded, because this build's Makefile rewrites its own headers before
compiling and a `-j` race was the obvious suspect. What is left is that
**`quietm` cannot be rebuilt today from its own recorded configuration**: same
pinned drop (`HEAD 5c9be5d9`, worktree clean, **0** ignored files, one reflog
entry from the clone), same `.config-built` (**0** differing lines), same 599
translation units (**0** differing lines in the compiled-file list), same marks
(**0** differing lines), and the same symbol set — 量, `quietm`-only **0**,
`rep8`-only **0**.

🔴 **The whole difference is one compiler flag, and it is in the `.cmd` files
kbuild writes per object.** 🔄 **This paragraph first said so from THREE files
and the adversarial pass made it a census.** 量: all **746** `.cmd` files in the
two trees compared word by word with the cell name normalised — **588 differ,
and there is exactly ONE difference shape across every one of them**: `quietm`
carries `-fno-if-conversion` and `rep8` does not. Nothing else differs anywhere
in the build's own record of what it compiled. *(As written: `kernel/.sched.o.cmd`,
`mm/page_alloc.o` and `net/ipv4/tcp.o` — three samples used to support a sentence
with the word "whole" in it.)*

⚠️ **One difference between `quietm` and `rep8` that is NOT the flag, stated so
the pair is not read as tighter than it is**: `rep8` was built with TODAY's
initramfs spec, 31 entries against `quietm`'s 29. That lands in `.init.ramfs`
and in nothing this section measures — `.text` and the `.cmd` files are both
upstream of it.

🔴 **That is not any flag. It is `SPEC.md` `TC-25`** — the one that takes
`hazlint` from **7 load-use violations to 0**, by removing 98.8 % of the
compiler's conditional moves (2,597 → 31) at a cost of +0.69 % of `.text`.
§7.1 is the section about it: this gcc emits `movz` into a branch delay slot,
under `.set noreorder`, reading a register a `lw` two instructions earlier
writes. It is the codegen safety net Decision A's refutation condition names.

🔴 **And it lives nowhere except the operator's command line.**
`config/rlxfw-kernel.delta` declares 36 kconfig symbols with a reason each;
`config/rlxfw-initramfs.tsv` declares 31 image entries with an owner each;
`config/rlxfw-marks.tsv` declares 15 source insertions with a reason each. The
flag that decides whether this kernel has a load-use hazard in it is in none of
them — it reached the 2026-08-28 build as `--cflags-kernel` typed at a shell,
and `rlxfw-kbuild.sh` does not record it either: the build writes
`<cell>.config-built` and nothing about `CFLAGS_KERNEL`. **A rebuild that
followed every committed file produced an image without it, and every gate in
this repository stayed green.**

⚠️ **This says nothing about the image that booted.** `quietm` and `loudm` were
built WITH the flag — that is what the `.cmd` files say — and `RUNSHEET` `P1`
measured `hazlint` 0 on both. What is refuted is *reproducibility*: until today
the recipe for those two images was not written down anywhere, so a reader with
this repository could not have rebuilt them, and neither could I.

**`P18-7`, written before it was measured:**

* `hazlint` over `rep8.vmlinux.elf` (today, no flag) reports **7** violations.
  **Refuted by** 0, or by any other count — `TC-25`'s fA cell reported 7 and
  this is the same configuration one flag short.
* `hazlint` over the corrected `quietmc` reports **0**.
* the corrected `quietmc`'s `.text` is **2,449,180** — 推, and it is arithmetic
  on two measured deltas rather than a reading: 2,427,448 (`rep8`)
  + 16,788 (`TC-25`'s measured cost) + 4,944 (mtdchar, measured above as
  2,432,392 − 2,427,448). **Refuted by** anything outside ±0.1 %, which would
  mean the two deltas are not additive and would need its own explanation.

### 18.6 The readings, and the one prediction that was wrong in its second half

**量 2026-08-30, second pass, with `config/rlxfw-cflags` in place.**

| | `quietm` 08-28 | `quietmc` today | `loudm` 08-28 | `loudmc` today |
|---|---:|---:|---:|---:|
| `.text` | 2,444,228 | **2,449,212** | 2,483,500 | **2,488,484** |
| `vmlinux` ELF | 3,968,240 | 3,968,635 | 4,042,388 | 4,075,551 |
| decompressed | 3,472,384 | **3,472,384** | 3,546,112 | **3,578,880** |
| of the 5,242,880 ceiling | 66.23 % | **66.23 %** | 67.63 % | **68.26 %** |
| `nfjrom` | 1,027,072 | **1,029,120** | 1,053,696 | **1,054,720** |
| `hazlint` | 0 | **0 in 110,141 loads** | 0 | **0 in 112,021 loads** |
| `CFLAGS_KERNEL` recorded | — | `-fno-if-conversion` | — | `-fno-if-conversion` |

**`P18-1` held** — `(NEW)` is 0 in both `oldconfig` logs. **`P18-2` held** — one
symbol line differs from the 2026-08-28 builds and it is `CONFIG_MTD_CHAR`.
**`P18-3` held** — the five mtdchar symbols are present where §17.7a measured
zero, and 17.7a's own control (six mtdblock/mtdcore symbols) is unmoved; the
whole symbol delta is **+12 / −0** and all twelve are mtdchar's. 🟢 **And one
of the twelve is better evidence than the other eleven**: `__initcall_init_mtdchar6`
is in the map, which says the registration is wired into the init sequence at
level 6 rather than merely compiled. `register_chrdev(MTD_CHAR_MAJOR, "mtd",
&mtd_fops)` is the line it will run (讀 `mtdchar.c:832`), and until it does,
major 90 has no driver — which is exactly the `ENODEV` §17.7a measured.

🟢 **`P18-7`'s third clause is the tightest prediction this project has made.**
`.text` was predicted at **2,449,180** by adding two separately measured deltas
— 2,427,448 (`rep8`, no flag, no mtdchar) + 16,788 (`TC-25`'s cost) + 4,944
(mtdchar, from the flagless pair) — and measured **2,449,212**: **+32 bytes,
0.001 %**. The two deltas are additive, which was the thing being asserted.

🔴 **`P18-4` is refuted in its second half, and the fault is a "so".** It read
*the decompressed image grows by fewer than 65,536 bytes, so the ceiling stays
under 68 %.* The first half holds — `quietmc` grows by **0** and `loudmc` by
**32,768**. The second does not: `loudmc` is at **68.26 %**. The percentage was
derived from `quiet`'s baseline and applied to both variants, and the two have
different baselines. A bound on bytes does not carry to a bound on a ratio whose
denominator this sentence never named.

🔴 **And `P18-5`'s negative control was predicted at the wrong number, by this
section's author, in the direction the tool exists to prevent.** §18.3 said the
old image must fail *and name exactly the three differences*. It names **two**:
`MISSING /dev/mtd0ro` and `MISSING /dev/mtd1ro`. `/dev/mtdblock1` was never in
**any** image, so removing it from the declaration produces no difference against
`quietm` at all. **A change to the declaration was counted as a difference in
the artefact** — which is the exact confusion `verify` was written to stop.
*(Kept as written above; the count there is wrong and this is the correction.)*

**What `verify` reports on the two new images**: `OK 31 entries`, five device
nodes, `/dev/mtd0ro` and `/dev/mtd1ro` both `c 90:odd`, and no major-31 node
anywhere. On `quietm` it reports `FAILED 2 difference(s)`.

⚠️ **`rep8` and `rep4` carry no `<cell>.cflags`**, because they were built before
the guard existed. Rebuilding them now needs `--no-cflags`, which is the point:
the flagless build has to be asked for by name. They are kept as the evidence
that it produces seven violations.

### 18.7 🔄 The leak gate scans 240 of 898 tracked files — and the MAC named in this heading is NOT this model's, see the block below

> 🔴 **2026-08-30, fourteenth session: this section's headline is wrong and its
> owner has moved.** `FC:19:28` is **not this model's OUI** — it is Actions
> Microelectronics, and the value is the **workstation's USB GbE adapter**,
> which is in the dump **0** times. The attribution the section records as
> *undetermined* was determinable the whole time, by a route nobody looked for:
> the arbiter is this unit's own dump. The gap the section describes is real
> and stands; **the finding it names is not.** The one value that genuinely is
> this unit's is a different one, in `upstream/BENCH-LOG.md:216`.
> **Owner: `notes/leak-surface.md`; number: `SPEC.md` `FLS-22`.** The section
> is kept as written below, because it is the record of what was believed.

**量 2026-08-30, with `tools/leakscan.py`, new in this step.** The whole of this
repository's leak checking is one CI step — and 🔴 **none of the narrowness was a discovery. It was
written down twice before this session, once of them EARLIER THE SAME DAY, and
the second time with the consequence spelled out.**

* 讀 `bench/2026-08-26/README.md:104`: *"CI runs `audit-bench-log.py` over
  `bench/**/*.log` and nothing else touches `bench/`."* A clause in a note about
  a different tool.
* 🔴 讀 `bench/README.md`, 2026-08-30, earlier the same day: *"`upstream` is a
  **gitlink** pinned at `4d3ff26`, so `git ls-files` returns nothing under it and
  every sweep built on it — including `audit-bench-log.py`, which walks
  `bench/**/*.log` only — has never looked there"* — and it says what is there:
  `upstream/BENCH-LOG.md` **prints actual `H601` byte values at named offsets**
  and commits a sha256 prefix over the **4 KiB at flash `0x6000`** seven times,
  a superset of the window `FLS-20` refuses to publish a digest for. Its own
  conclusion: *"`flashwin.py` enforces the rule on the paths it knows about, and
  the repository is larger than those paths."*

**So the finding below is not that the gap exists.** What is new is the scan
actually run over it, the identity/topic split that makes a count mean
something, the one-value / seven-files census, the **658 tracked files** nobody
reads — which neither earlier note mentions — the **28 hits inside `bench/`
itself**, and an instrument that can be re-run. The gate:

```
audit-bench-log.py $(find bench -type f -name '*.log')
```

That is **240 files**. 🔄 **The first draft of this paragraph said `git ls-files`
returns 795 and that 555 go unread; both were arithmetic on a number I had not
measured — the same class as the `45` two paragraphs down.** 量: `git ls-files`
returns **899**, of which one is the submodule gitlink, so **898** real files;
**658** of them are never read, and `upstream/` adds **302** that `git ls-files`
cannot see at all. **960 files go unread.** The gap is not a corner:

| population | files | scanned | identity-pattern hits | why nothing had scanned it |
|---|---:|---:|---:|---|
| `bench/**/*.md` | 45 | 45 | **2** | in the directory the gate is named for; the gate globs `*.log` |
| tracked, not `bench/*.log` | 613 | 599 | **46** | `SPEC.md`, `PROGRESS.md`, `LOG.md`, `RUNSHEET.md`, `notes/`, `docs/` |
| `upstream/` | 302 | 276 | **52** | a submodule: `git ls-files upstream` returns **one** line, the gitlink |

🔴 **The gate scans what an instrument wrote and not what a person typed, and a
person is the one who can mistype a MAC into prose.** It also misses
`bench/**/*.txt`: the two host-side `tcpdump` captures from the ping cells,
`V7a-host.txt` and `L7e-host.txt`, are in `bench/` and are not `.log`, so the
gate named for that directory has never read either one. **量: 28 of the identity
hits are inside `bench/` — 2 in the `.md` cards (`PREDICTIONS-B5-block1.md` and
`bench/README.md`) and 26 in those two `.txt` files, 13 each.**

**Raw hits are 2,349 and that number is useless, which is why the tool does not
stop there.** `audit-bench-log.py`'s patterns were written for a device log,
where the string `calib` in the bytes means calibration data; in prose those
words are the subject matter — this project writes `H601` in every other
paragraph. Four of the eight patterns can identify one physical unit
(`MAC, colon form`, `MAC, dash form`, `MAC, bare 12 hex`, `serial-ish`) and
`leakscan.py` splits them out. **100 identity hits, against 2,252 topic hits** — 🔄 **and that first number moved during the session, from 97, because the session's own edits are IN the population.** It is taken at the end, after the last file was written, which is the discipline `PROGRESS.md`'s carried-forward header records having got wrong twice. ⚠️ **Eight of the 100 are `tools/audit-bench-log.py`'s own control string and allowlist literals** — synthetic data belonging to the scanner, and a reading of *this repository's prose* should quote **92**.

🔴 **The one that matters, and it is stated at the strength the evidence
supports.** 量, distinct values, counted across both repositories' text with no
value printed anywhere: **exactly one** MAC on **`FC:19:28`** — TOTOLINK's OUI —
exists in the corpus, and it appears in **seven files, four of them in
`upstream/`**, which is a **public** repository. 🔄 *(This said SIX. The walk
that produced it skipped every directory named `study` — right for rlxfw's
own, which is gitignored and unpublished, and wrong for `upstream/study/`,
which is in the public repository.)* `SPEC.md`'s own opening says
*MAC、序號、射頻校正、WPS PIN —— 完全不在這裡*.

⚠️ **推, and the check that would settle it is not available.** `FW-17` (讀)
says this model's default SSID is `TOTOLINK N150RT` plus the MAC's last six hex
digits, so an SSID of that shape would decide whether this value is this unit's
or a documentation example. 量: **zero** strings of that shape exist in either
repository, so the correlation could not be run and the attribution is
**undetermined**. What is *not* undetermined is that a full six-octet address on
this model's vendor OUI is in a file this repository says holds no MAC.

⚠️ **And 26 of `upstream/`'s 302 files cannot be read by any text scanner** — 22
`.jpg`, 2 `.png`, one undecodable `.log`, one `.pyc`. They are reported NOT
SCANNED rather than counted clean, which is `L6`.

🔴 **The first draft of this paragraph went on to say that nothing records how
those images were handled, and the owner audit refuted it the same evening.**
讀 `upstream/notes/img/README.md`: an inventory table, one row per image, with a
`Redacted` column, under the rule *"Redact **before** `git add`. A redaction
applied after a push is not a redaction."* — and it names both unit-identifying
labels and says the serial QR is the more dangerous because it decodes
automatically and survives downscaling. 量: **24 image files, 24 inventory rows,
0 missing either way.** What stands is `L6` — this instrument cannot read them —
and not any claim about whether they were handled.

**Why `leakscan.py` never prints what matched.** The question is whether a MAC is
in a published file; answering it by printing the MAC answers it in the worst
possible way. `flashwin.py` draws the same line — verdict published, digest
refused. `L5` is the control on it: a synthetic file containing a distinctive
address must produce a finding whose rendered output does not contain it.

🔴 **It is NOT wired into CI as a verdict today, on purpose.** Turning it into a
gate needs an allowlist decision per surviving hit — the workstation's own MAC in
the host captures, the tool's own control literals, and the `FC:19:28` value
above — and allowlisting a possible real leak to get a green build is the wrong
order. What CI gets today is `leakscan.py --self-test`: six controls, including
the two that make a clean result mean anything (`L4`, the population is
non-empty; `L5`, a finding carries no bytes). The verdict run is a desk step
until the allowlist is decided.
### 18.8 What the owner audit found, and it fired six times

**The audit has two halves now**: grep for sentences already known to be wrong,
and — new this session — take every carried-forward row *opened today* back to
the repository and check it is not a question already answered. The second half
exists because 2026-08-30's seating invented one in four files at once.

| | what | verdict |
|---|---|---|
| 1 | *"the whole difference is `-fno-if-conversion`"*, asserted from **three** `.cmd` files | **survives, and gets stronger**: all 746 compared, 588 differ, exactly ONE difference shape |
| 2 | *"45 identity hits are inside `bench/`"* | 🔴 **wrong** — 45 is the FILE count of `bench/**/*.md`. The hit count is **28** |
| 3 | *"`git ls-files` returns 795, so 555 go unread"* | 🔴 **wrong, and never measured** — 899 lines, 898 files, **658** unread plus `upstream/`'s 302 |
| 4 | *"nothing records which images `redact-photo.py` was run on"* | 🔴 **an invented question**: `upstream/notes/img/README.md` is a per-image inventory with a `Redacted` column. 量: 24 images, 24 rows, 0 missing either way. Row **withdrawn** |
| 5 | the `upstream/` blind spot presented as a discovery, in six files | 🔴 **it was written down twice before, once EARLIER THE SAME DAY.** `bench/README.md` names the gitlink, says `audit-bench-log.py` *"has never looked there"*, and records that `upstream/BENCH-LOG.md` prints actual `H601` byte values and a sha256 over the 4 KiB at flash `0x6000`, seven times. **What is new today is the scan, not the gap** — and that is now what the six files say |
| 6 | `tools/test-gitignore.sh`'s positive-control list names `docs/threat-model.md` | 🔴 **no such file.** 量: `git ls-files docs/` returns seven names and that is not one. The case passed anyway, because these are fixture paths created in a throwaway repository — which is exactly why a name that does not exist could sit in a list whose whole job is to name files that must survive. Swapped for `docs/FINDINGS.md` |

**Two and three are the same defect**: a number derived from another number that
was itself never measured, then repeated in five files. Both were caught by
computing them at the end rather than by reading what had been written.

🔴 **Four and five are also the same defect, and it is the one the second half of
the audit was added for**: writing up a gap without asking the repository whether
it already knew. Four invented a question that was answered; five re-announced a
finding the repository had made the same morning. **Two sessions running, and
this is the first in which the check existed** — 2026-08-30's seating invented
`eth5` in four files at once and nothing caught it until the adversarial pass.

⚠️ **And one insertion defect, twice in one session, in the same file class**:
new table rows anchored on the NEXT heading rather than on the LAST ROW, which
leaves the blank line that separated them and strands every row above it. `C8c`
caught both — in `PROGRESS.md` and then in `docs/FINDINGS.md`, whose own newest
row at the time was *"Nine rows of this page were rendering as paragraphs"*.

🔴 **And the audit found one thing that is not about today's work at all.**
`CLAUDE.md`'s pre-push step is `ci-census --only <the suites you touched>` — and
量, on the machine the push happens from, that command **could never go green**:
`--only` restricts the table but not the `not-run-total` assertion, and
`not-run-total` is a **runner**-configuration number, while this host has
`$FWRE_WORK` and runs everything. A documented procedure that cannot pass is one
nobody follows, or one whose red everybody learns to read past. `ci-census.py`
now passes `declared_total` only for a whole-table census, and `C16` asserts both
directions — because a fix that disabled the check outright would pass the first
half alone. 19 → 21.

**Two stale counts in files this session touched**, both corrected in place with
the original quoted: `config/rlxfw-initramfs.tsv`'s own header said *"The 47
busybox symlinks"* (量: 13 `slink` rows, 11 pointing at busybox — 47 is the count
of nothing in that file), and `SPEC.md` `FW-24` said the declaration holds 29
entries (量: 31). Three owner files still described the pre-rebuild state and
each got a forward pointer rather than a rewrite: `notes/rootfs-census.md`,
`RUNSHEET.md` twice, and `docs/FINDINGS.md` — the last of which is a page a
reader is pointed at.
### 18.9 🔴 CI went red on the suite this session added, and the bench could not have caught it

**量 2026-08-30, run 33310864156.** `lint`, `text` and `instruments` all passed.
The **census** job failed:

```
RED   test-kbuild-cflags   ran 8/9  failed 0  not run 0
      UNEXPECTED-SKIP 'C1 the declared flags reach the build'
      CENSUS-MISMATCH 8+0+0 != 9 -- cases went missing with neither a FAIL nor a skip line
→     NOT-RUN-TOTAL MISMATCH: the table declares 456 and this job did not run 455
```

**Mechanism.** 讀 `ci-census.py:201-205`: a printed `skip` line is counted only
when its **label** — `SKIP_RE`'s first field — appears in the allowed-skip column
of `tools/ci-expected.tsv`. The suite prints
`C1 the declared flags reach the build`; the row I wrote said `C1 the GPL drop`.
A label that does not match is not a skip, so the case simply vanishes, and the
build fails on arithmetic that never names the label. The `not-run-total` failure
underneath it is the same one case: 455 + 1 = 456.

🔴 **The pre-push census on this machine is structurally blind to that class,
and this is the second consecutive day CI has caught something the local
procedure could not.** On the bench `$FWRE_WORK` holds the GPL drop, so `C1`
**runs**; no skip line is printed; no label is ever compared. The suite was
**9/9 green here** at the moment CI went red. *(Yesterday it was a hardcoded
population count in `test-boot-timeline`'s `B2`; §18.8 records a third blindness
in the same procedure — `--only` asserting a runner's `not-run-total`.)*

**The fix is a case, not care.** `C7` reads `tools/ci-expected.tsv` and asserts
its allowed-skip column equals the label this suite prints — the only check that
works in **both** configurations, and it needs no vendor material. The label is
now a shell variable used three times (the case, the skip, the assertion), so
the two spellings cannot drift apart again. 9 → 10.

**Verified in the configuration that failed**, which is the part the first pass
skipped: the suite run with `$FWRE_WORK` pointed at an empty directory prints
`9 passed, 0 failed, 1 skipped`, and `ci-census` over that output reports
`ok test-kbuild-cflags ran 9/10 failed 0 not run 1`.

⚠️ **What this does not fix**: every other suite with an allowed skip has the
same exposure, and only this one now reads the table. A general check would
compare every row's skip column against the labels its suite can print, and that
needs a way to enumerate them without running the suite in every configuration.
Carried forward.

### 18.10 🔴 The fix for §18.9 is *"point `$FWRE_WORK` at an empty directory"*, and that is a PARTIAL emulation of a runner

**量 2026-08-31 (fourteenth session), and the census is what said so.** The
procedure §18.9 leaves behind — run the suites again with `$FWRE_WORK` pointing
at an empty directory, then census that output — was followed for the first time
today over the *whole* table. It produced **four red lines, and three of them
were defects in the emulation rather than in the repository**:

| | what the census said | why |
|---|---|---|
| `test-hazlint`, `test-hazlint-objs` | *marked `*bench-only*` and yet the `.out` exists* | `.github/workflows/ci.yml` has **no step** for either. A capture for a bench-only suite is itself the defect, and the census refuses it rather than counting it — which is the check working |
| `test-rlxprobe` | `ran 101/202 failed 101` | 🔴 **its allowed skip is keyed on `command -v mips-linux-gnu-gcc`, not on `$FWRE_WORK`**, and this bench HAS the cross compiler. So an empty `$FWRE_WORK` left it running, with its material gone. `test-opcount` keys on `mips-linux-gnu-as` the same way |
| `test-leakscan-mutants` | `20+0+3 != 24` | the capture predated `Q1` by twenty minutes. Re-run, and the arithmetic closes |

🔴 **So the procedure covers fourteen suites and misses two, and nothing said
which.** 量: of the 16 suites that declare an allowed skip, **14 key it on
`$FWRE_WORK`** and **2 key it on a tool being on `PATH`**. Pointing `$FWRE_WORK`
at an empty directory emulates a runner for the first fourteen and for neither
of the last two — and the failure is silent in the direction that matters, since
a suite that *runs* here where it would *skip* there has its label compared by
nobody, which is the exact class §18.9 is about.

🔴 **It took THREE attempts to state the emulation correctly, and each wrong one
was wrong in a different way.** That is the part worth keeping:

| attempt | what it did | what the census said |
|---|---|---|
| 1 | `$FWRE_WORK` empty, every suite run | four RED. Two bench-only suites had a `.out` at all; `test-rlxprobe` ran and failed 101; `test-leakscan-mutants` predated its own newest case |
| 2 | also filtered the cross tools out of `PATH` — **by directory** | `test-rlxprobe` and `test-opcount` exited **127**: `/usr/bin` holds `mips-linux-gnu-gcc`, so removing that directory removed **`bash`**. The census read the empty output as *0 cases, no skip line*, which is precisely the shape it exists to catch |
| 3 | a symlink farm over every `PATH` directory minus `mips-linux-gnu-*` | green except **461 against a declared 460**, off by exactly `test-opcount`'s one skip |
| 4 | 讀 `ci.yml`: it installs **`binutils-mips-linux-gnu`** and deliberately **not** `gcc-mips-linux-gnu` — so `mips-linux-gnu-as` IS on a runner and `mips-linux-gnu-gcc` is not | **every suite ok, and `NOT RUN IN THIS JOB: 460` against a declared 460** |

**So the emulation is three conditions and one of them is a package list**:
`$FWRE_WORK` pointing at an empty directory, the suite list `ci.yml` actually
runs, and **the runner's exact package set** — which is read out of `ci.yml`'s
`apt` step and is not derivable from anything else. ⚠️ Attempt 3 would have been
recorded as *"the table is off by one"* if the reason had not been chased: a
number this repository declares would have been changed to match a measurement
taken in the wrong configuration.

## 19. `R3-9`/`R3-10b` on the silicon: the MTD path works, and the reason it could have silently not worked

**量 2026-08-31, seating 7, two power cycles.** `bench/2026-08-31/` and
`bench/2026-08-31b/`. The card is `PREDICTIONS-B5-block3.md`; what it got wrong
is `CORRECTIONS-block3.md`; this section owns the **mechanism**.

### 19.1 🔴 The alternative that had to be excluded, and `wc -c` could not have excluded it

讀 `drivers/mtd/maps/rtl819x_flash.c:62-73`:

```c
void rtl8196_map_copy_from(struct map_info *map, void *to, unsigned long from, ssize_t len)
{
	if (from>0x10000)
	    memcpy(to, map->map_priv_1 + from, (len<=1024)?len:1024);//len);
	else
	    memcpy(to, map->map_priv_1 + from, (len<=4096)?len:4096);//len);
}
```

It is asked for `len`, copies at most **1024**, and returns **`void`**. The
commented-out `//len)` on both branches says the truncation was deliberate. The
caller cannot learn it happened: `mtd_read` sets `retlen = len` and
`copy_to_user` hands the whole buffer up, so the bytes past the cap are
uninitialised `kmalloc` memory presented as flash.

🔴 **`wc -c` counts what `read()` returns, not what the flash supplied.** So
`M-b`/`M-c` as originally carded — a byte count — would have returned exactly
`1245184` and `2949120` **whether or not** this function was live. The card's
§7.2 said the cells were "not a content check" and treated that as unavoidable
because the image has no digest applet; it is unavoidable only if the applet on
the row is ignored. `wc -l` is content-derived and costs nothing extra.

### 19.2 Which `copy_from` is live is one config symbol, and it is not the driver's choice

讀 `include/linux/mtd/map.h:425-442`:

| `CONFIG_MTD_COMPLEX_MAPPINGS` | `map_copy_from(...)` | `simple_map_init(map)` |
|---|---|---|
| set | `(map)->copy_from(map, to, from, len)` — the function pointer | assigns the accessors |
| **not set** | `inline_map_copy_from(map, to, from, len)` — **a macro, the pointer is never consulted** | `BUG_ON(!map_bankwidth_supported((map)->bankwidth))`, an assertion and nothing else |

**So with the symbol unset, `rtl8196_map_copy_from` is dead code** — not
overridden at runtime, but *bypassed at compile time*. `init_rtl8196_map` calls
`simple_map_init(&spi_map[i])` at `:261` and nothing after it reassigns
anything, which under the unset branch is a `BUG_ON` that the booting kernel
already proved does not fire.

量: **`# CONFIG_MTD_COMPLEX_MAPPINGS is not set` in all 31 `.config-built`
files on this disk**, `quietmc` — the image seating 7 uploaded — among them.

⚠️ **This is 讀 plus a config grep, and the device is the only thing that can
turn it into 量.** Which is what §19.3 is.

### 19.3 The reading, four times, across two power cycles

| cell | command | reply | bytes |
|---|---|---|---:|
| `M-b2` | `busybox wc -lc < /dev/mtd0ro` | `␣␣␣␣␣4422␣␣␣1245184` | 53 |
| `M-c2` | `busybox wc -lc < /dev/mtd1ro` | `␣␣␣␣␣7943␣␣␣2949120` | 53 |
| `X-b2` | same, cycle 6 | identical | 53 |
| `X-c2` | same, cycle 6 | identical | 53 |

The expected counts were computed at the desk from
`$FWRE_WORK/dumps/flash-n150rt-console-2.bin` (`FLS-14`, sha256 verified in the
same script) over the two partition slices, with three controls: the dump's own
size and hash, a hand-built slice whose newline count is known by construction,
and the requirement that the two partitions tile all 4,194,304 bytes with no gap
or overlap. **A second, independent implementation agreed**: this unit's own
busybox under `qemu-mips-static -L`, run over the same slices, printed the same
two numbers.

**H1 would have given ≤1228 and ≤2007** at a 4,096-byte request, falling to 53
and 71 at `mtd_read`'s 128 KiB ceiling, with slab residue adding an unknown
non-negative amount. **The separation is at least 3.6× everywhere in that
range.** H0 is what came back, four times.

> The whole 4,194,304 bytes have now been read through a path the kernel will
> not let anything write, and what came back is this unit's own flash.

⚠️ **It is an aggregate, not a comparison.** A newline count places no byte and
a permutation of the partition would pass it. `FLS-20` still belongs to the
`FLR` bracket.

### 19.4 The rate, and the estimate it refutes

From the wire-silent gap in each `.timing` — nothing returns until `wc`
finishes, so the gap **is** the read:

| | `M-b2` | `X-b2` | `M-c2` | `X-c2` |
|---|---:|---:|---:|---:|
| gap | 1.356 s | 1.230 s | 2.959 s | 2.933 s |
| rate | 918.6 KB/s | 1012.4 KB/s | 996.6 KB/s | 1005.6 KB/s |

**≈ 0.92–1.01 MB/s**, against the card's `CLK-15`-derived **59.8 KB/s** 推 —
**~16×**. The terminators (45 s / 100 s, set at ~2× the estimate) were therefore
over-provisioned by an order of magnitude. Harmless, and now a 量.

⚠️ 🔄 **Why the two differ was undetermined when this section was written, and §19.7 answers it the same day** — the first candidate below is **refuted** (both paths read a 32-bit word at a time), and what replaces it is instruction-fetch amplification and the SPI clock divider. The paragraph is left as written because it is the record of what was known at the moment §19.4 was written; read §19.7 for the answer. *(As written:)* Both are
uncached: `map->virt` is `0xbd000000`, KSEG1 (讀 `:107-109`), and stage 1 is the
loader's own uncached copy. Candidates: byte-at-a-time versus `memcpy_fromio`'s
word-at-a-time (a factor of 4, not 16); different bus or clock state at the two
moments; `CLK-15`'s 350 ms containing more than the copy. **The first is
settleable at the desk from the two disassemblies and needs no power cycle.**

🔴 **And a band drawn from n=1 was refuted by n=2.**
`PREDICTIONS-B5-block3c.md` §3 predicted 1.30–1.45 s for `mtd0` from `M-b2`
alone; `X-b2` returned **1.230 s**. The band was written before the number was
seen, so this is a refutation rather than a widening. The spread across four
reads is ~10 % and the row that quotes the rate has to carry that.

### 19.5 The safety property, measured at two points instead of argued at one

讀 `mtdchar.c`'s `mtd_open`: `(f_mode & FMODE_WRITE) && (minor & 1)` → `-EACCES`.
量 on the silicon:

| | | |
|---|---|---|
| `M-d` | `echo x > /dev/mtd0ro` (`c 90 1`) | `/bin/sh: can't create /dev/mtd0ro: Permission denied`, 78 B |
| `X-d1` | `echo x > /dev/mtd1ro` (`c 90 3`) | identical shape, 78 B |
| `X-d2` | `busybox wc -c < /dev/mtd0` (even minor) | `/bin/sh: can't open /dev/mtd0: no such file`, 74 B |

**Zero flash bytes** — `open` fails before any write is issued. One instance is
an anecdote; `X-d1` makes it two, on the other declared node. `X-d2` closes the
other half: the even, writable minor **is absent**, so `FW-30`'s *the
declaration set is the whole node set* is measured.

⚠️ **`FW-30`'s typo sentence is true of a read and false of a write.**
`echo x > /dev/mtd0` would make the shell **create a regular file** — initramfs
is writable. That reaches no flash, but it is not `No such file`, and the block
tests the read direction deliberately for exactly that reason.

⚠️ **The message text transferred from qemu; the prefix did not.** The desk
measurement ran busybox with argv[0] = `sh`; the device's shell was invoked
through `/bin/sh` and prints that — **+5 characters on every shell-error cell**.
And the input-redirect failure is busybox's own short `no such file`, not
`strerror`'s `No such file or directory`.

### 19.6 🔴 What the seating found that is not about MTD at all

**`wc` was on the applet list and not in the image.** The image declares eleven
busybox symlinks and `wc` is not one, so the carded command returned
`/bin/sh: wc: not found`. The applet census (`FW-26`) is correct; what is
missing is that **nothing compares a card's typed commands against the
declaration of the image that card uploads**. Same shape as the carried-forward
row *a declaration ahead of every artefact*, one turn further on.

**DRAM retained written data across a power cycle** (`MEM-17`). Cycle 6's four
pre-reads came back byte-identical to the flash expectations before any `FLR`
ran, while addresses nobody had written were still garbage. It voided cycle 6's
bracket, it cost `X-ab` its claim to prove a cold boot, and it was caught by the
pre-read control on the first occasion that control existed.

### 19.7 🔴 `FW-34`'s open half, settled at the desk — and the candidate `SPEC.md` §17 named is the one that is wrong

§19.4 left *why the kernel's path is ~16× the loader's stage 1* undetermined,
with three candidates. §17 said the first was **settleable at the desk from the
two disassemblies and needs no power cycle**. It was. **It is also refuted**,
and the two terms that replace it were not on the list.

**Materials**: `mips-linux-gnu-objdump` (Ubuntu binutils 2.42 — *not* a vendor
binary, so no `vendor-tripwire.sh` wrapper is owed), `quietmc.vmlinux.elf` (the
image that booted on 2026-08-31), and flash `0x000000`–`0x0012F0` cut out of
`$FWRE_WORK/dumps/flash-n150rt-console-2.bin` and disassembled at VMA
`0xBFC00000`. Working files under `$FWRE_WORK/rebuild/bench-only/fw34-desk/`.

#### 19.7.1 讀 — the access width is the SAME on both sides. The candidate is dead.

**Stage 1's copy loop**, at `0xBFC001BC`:

```
bfc001bc:  lui   k0,0xbfc0
bfc001c0:  addiu k0,k0,1264      ; src = 0xBFC004F0
bfc001c4:  lui   k1,0xbfc0
bfc001c8:  addiu k1,k1,22188     ; end = 0xBFC056AC
bfc001cc:  lui   t1,0x8010       ; dst = 0x80100000
bfc001d0:  lw    t0,0(k0)        ; <-- one 32-bit load
bfc001d4:  nop                   ;     Lexra load delay slot, filled by hand
bfc001d8:  sw    t0,0(t1)
bfc001dc:  nop
bfc001e0:  addiu t1,t1,4
bfc001e4:  addiu k0,k0,4
bfc001e8:  bne   k1,k0,0xbfc001d0
bfc001ec:  nop                   ;     branch delay slot
bfc001f0:  lui   k0,0x8010
bfc001f4:  jr    k0              ;     into stage 2
```

🟢 **`22188 - 1264 = 20,924`.** The number `CLK-15` and `docs/FINDINGS.md` have
carried is re-derived here from two immediates in the instruction stream, which
is the first time this repository can show where it comes from rather than
quote it.

**The kernel side.** `inline_map_copy_from` (讀 `include/linux/mtd/map.h:410`)
takes the `else` branch because `spi_map[]` sets no `cached` field (讀
`drivers/mtd/maps/rtl819x_flash.c:107-119`), so it is `memcpy_fromio`, which on
this arch is plain `memcpy` (讀 `arch/rlx/include/asm/io.h:468`). 量 in
`quietmc.vmlinux.elf`: `memcpy` = `0x80002720`, and its aligned fast path at
`0x80002750` is **eight `lw` and eight `sw` per 32 bytes**, unrolled.

| | stage 1 | kernel `memcpy` |
|---|---|---|
| load width | `lw` — 32 bit | `lw` — 32 bit |
| loads per iteration | 1 | 8 |
| bytes per iteration | 4 | 32 |

> **Both paths read the flash a 32-bit word at a time. The byte-versus-word
> candidate — the only one §17 said the desk could settle, and the one worth a
> factor of 4 — is refuted, and it is worth a factor of 1.**

#### 19.7.2 讀 — where the loop *executes* is worth 9×, and it was not a candidate

Stage 1's loop runs at `0xBFC001D0`. **That is KSEG1, which is uncached by
architecture** — the same fact `FW-34` already uses about `map->virt =
0xbd000000`. So every instruction fetch of that loop is itself an uncached read
of the SPI device the loop is reading:

* **stage 1**: 8 instruction words + 1 data word = **9 SPI word reads per 4
  bytes copied**
* **kernel**: the loop body is ~21 instructions in KSEG0 kernel text and the
  I-cache is 16 KiB with 16-byte lines (`CPU-25`, 量 by experiment 2026-08-29),
  so after the first of 38,912 iterations every fetch is a hit — **1 SPI word
  read per 4 bytes copied**

**9×**, and it is a property of *where the code lives*, not of the copy.

⚠️ **The ceiling, not the value.** This assumes the memory-mapped window serves
each fetch as its own transaction. If it prefetches a sequential instruction
stream the amplification is smaller, and nothing here measures that. §19.7.4's
cell is what would.

#### 19.7.3 D + 量 + 讀 — the SPI clock divider is worth 4×, and stage 1 runs at the reset default

讀, over all 4,848 bytes of stage 1: **`0xB8001200` (`SFCR`) is written zero
times.** 讀, `$FWRE_WORK/stage2-vma.dis`: stage 2 writes it **twice**, at
`0x804055F8` and `0x80405900`. So stage 1 copies at whatever the SPI controller
holds out of reset, and everything after stage 2 runs at what stage 2 set.

| source | says |
|---|---|
| **D** — `refs/RTL8196E-VEx-CG_Datasheet_1.1.pdf` §7.4.5 table 8 | `SFCR[31:29] = SPI_CLK_DIV`, `SPI Clock = DRAM Clock / SPI_CLK_DIV`, `111B` → DIV 16, `001B` → DIV 4, **Default `111B`** |
| **A** — `drivers/mtd/chips/rtl819x/spi_common.h:87` | `SFCR_SPI_CLK_DIV(val) ((val) << 29)` — the same field at the same place |
| **量** — `REG-13`, 2026-08-25b, `DW B8001200 4` at the loader prompt | `SFCR = 0x3FC00000` → bits 31:29 = `001` → **DIV 4**, cold and warm alike |

**Reset DIV 16 → running DIV 4 = a 4× faster SPI bit clock**, and stage 1 is on
the wrong side of it.

⚠️ **Two weaknesses travel with this and must not be dropped when it is
quoted.** ① The **reset default has exactly one kind of source**: the
datasheets. `RTL8196C-GR_Datasheet_0.7.pdf` carries the same table with the same
`111B`, but that is one vendor's document family and not an independent
measurement — the same "one source, three copies" shape as the `RLX4181` `PRId`
table. **Nothing in this project has ever read `SFCR` before stage 2 runs**, and
there is no console at that point to read it with. ② The driver's own
`SFCR_SPI_CLK_DIV((ui-2)/2)` maps `ui = 16` to `7 = 111B`, which **agrees** with
the table — but that is a consistency check on the *encoding*, not evidence
about the *default*, and it is the same class of double-counting the `CPU-04`
row had to strike out.

#### 19.7.4 The arithmetic, what it over-predicts, and the free cell that decides it

| term | factor | strength |
|---|---:|---|
| access width | **1×** | 讀 ×2 — **refuted** |
| SPI clock divider (DIV 16 → DIV 4) | **4×** | D + A + 量, with §19.7.3's two caveats |
| instruction-fetch amplification (KSEG1 loop → I-cache-resident loop) | **≤9×** | 讀 ×2, ceiling |
| **product** | **≤36×** | |
| **measured (§19.4)** | **~16×** | 量, n=4 |

🔴 **§19.7.5 ① corrects the outcome table below: the cell reads out the PRODUCT of the two factors and cannot separate them, and ⑤ says the 2.1–2.3× is a lower bound. Read that section before quoting this one.**

🔴 **AND AS OF 2026-08-31 THE CELL BELOW IS WITHDRAWN ENTIRELY — §20 SUPERSEDES
THIS SUBSECTION.** §19.7.5 ③ made *read the `FLR` handler first* a precondition;
it was read, and the handler reaches flash by **programmed I/O through `SFDR`**,
not through the memory-mapped window. So the sentence this subsection rests on —
*"it should run at the bus rate"* — is false in its third clause, and no band
the cell returns can say anything about that window's prefetch behaviour.
**Everything below stands as the record of what was predicted; nothing below
should be taken to the bench.** The replacement measures the SPI controller
rather than the window, and belongs to `R5b`: §20.5.


**The model over-predicts by 2.1–2.3×**, and per-read that reads:

* stage 1: `20,924 / 4 = 5,231` iterations × 9 = **47,079 SPI word reads** in
  351.9 ms (`CLK-15` cold mean) → **7.47 µs per SPI word read at DIV 16**
* at DIV 4, if the transfer is clock-bound → **1.87 µs**
* so the kernel's SPI reads alone predict **4 B / 1.87 µs ≈ 2,140 KB/s**
* §19.4 measured **918.6–1,012.4 KB/s**

🔴 **That gap is not a defect in the model; it is a term the model does not
have.** §19.4's figure is the wire-silent gap of `busybox wc -lc < /dev/mtd0ro`
— an **end-to-end userspace rate** covering `mtd_read`'s chunking, `part_read`,
`copy_to_user`, busybox's `read()` loop and its newline scan over 4,194,304
bytes. The model is of the SPI bus alone. A factor of ~2 of software on top of
the bus is ordinary; what would be alarming is if there were none.

> **The prediction, and it costs no power cycle.** Stage 2's own `FLR` executes
> **from DRAM** (no amplification) at **DIV 4** (no divider penalty) with **no
> Linux software path**. So it should run at the bus rate:
>
> **`FLR 80C00000 100000 100000`** — 1 MiB of the rootfs region into RAM at
> `0x80C00000` — timed from the wire-silent gap in its `.timing`.
>
> | outcome | what it says |
> |---|---|
> | **≈ 0.49 s (≈2,140 KB/s)** | the model holds; the 2.1–2.3× is Linux's software path |
> | **≈ 1.0 s (≈1,000 KB/s)** | the amplification term is wrong — the window prefetches, and the kernel already runs at the bus rate |
> | **≥ 2 s** | the divider term is wrong, and the reset default is not what the datasheet says |
>
> ⚠️ It must not run before a `put` in the same power cycle (`FLR` writes the
> TFTP length global) and `0x80C00000`–`0x80D00000` is chosen to miss the
> bracket's own `0x80A00xxx` destinations. Flash `0x100000`–`0x200000` contains
> **no `H601`**, so nothing about this cell is a forbidden window.

**What `SPEC.md` §17 keeps.** The open question narrows from *why is it 16×* to
**one** unknown with a written experiment: whether the memory-mapped window
prefetches a sequential fetch stream, which is the difference between the 9×
ceiling and whatever the cell above returns.

#### 19.7.5 🔴 What an adversarial pass found in §19.7.1-§19.7.4, the same day

§19.7.1-§19.7.4 stay as written. Six of the findings below change what those
sections are entitled to claim and one of them makes a table in §19.7.4 wrong;
two are new desk measurements that close gaps the pass named.

**① The cell in §19.7.4 measures a PRODUCT, and its three-row table decomposes
it into two factors with no basis. 🔴 That table is wrong.**

Write the model out. With `t(DIV16)` the per-SPI-word time during stage 1,
`A` the amplification and `D` the divider ratio, the proposed `FLR` runs from
DRAM (its own amplification is 1 by construction) at DIV 4, so its rate is
`59,460 x D x A` B/s. **The cell reads out `D x A` and nothing else.** Row 1 is
`D x A = 36`, row 2 is `17`, row 3 is `<= 8`. `D = 4, A = 2.1` -- which is
§19.7.2's own written caveat, a window that prefetches most of a sequential
fetch stream -- lands in row 3 and the table would read it as *"the divider term
is wrong"*. **The three outcomes are one number read three ways.**

What the cell is actually entitled to say:

| outcome | what it establishes |
|---|---|
| `~0.49 s` (`D x A ~ 36`) | both terms are at full strength; the 2.1-2.3x over-prediction is Linux's software path and nothing else |
| `~1.0 s` (`D x A ~ 17`) | the product is about half the model. **Which factor moved is NOT determined** -- prefetch halving `A`, or a reset default of DIV 8 rather than 16, fit equally |
| anything else | the framework is wrong, not one term of it (see ② ) |

**② Row 3's band was unreachable under the note's own model.** `>= 2 s` for
1 MiB is `<= 524 KB/s`, and §19.4 measured **918.6-1012.4 KB/s** on the same
bus *through* `mtd_read`'s chunking, `part_read`, `copy_to_user` and a newline
scan over 4,194,304 bytes. A bare `FLR` from DRAM at DIV 4 cannot be slower than
the same bus reached through all of that -- unless stage 2's `FLR` handler is
not a word copy through the memory-mapped window at all. So a `>= 2 s` reading
is evidence about **the handler**, and it refutes the framework rather than the
divider.

**③ Which makes one thing a precondition rather than an assumption, and it is
free.** §19.7.4 asserts *"it should run at the bus rate"* about a routine
nobody has disassembled. `$FWRE_WORK/stage2-vma.dis` is on disk. **Read the
`FLR` handler before spending the cell**: whether it is a `lw`/`sw` loop through
`0xBD000000` or programmed I/O through `SFDR` decides whether the cell measures
the bus at all.

**④ The `<= 9x` ceiling has the sign backwards on the kernel side.**
§19.7.2 treats prefetch as shrinking stage 1's amplification only. But the
kernel's `memcpy` fast path is **eight sequential `lw` over 32 bytes**; a window
that buffers a line serves seven of those eight from the buffer, so the kernel's
per-4-byte cost falls too. Stage 1's stream cannot benefit the same way -- its
eight fetches sit at one fixed 32-byte block while its data pointer advances,
and the two addresses evict each other every iteration unless the window holds
two buffers. **Under the prefetch hypothesis both terms move**, and the `1` on
the kernel side is not a floor.

**⑤ "Over-predicts by 2.1-2.3x" is a LOWER BOUND presented as a value.**
351.9 ms is `CLK-15`, which owns *the silence after `Booting...`* and not *the
copy loop*. §19.4's own third candidate is *"`CLK-15`'s 350 ms containing more
than the copy"*, and §19.7.4 consumed the whole of it as 47,079 SPI reads
without repeating that. The residue is small -- `CLK-15` prices the DRAM
read-window training and the BSS clear at a few ms each and eliminates
decompression by measurement -- but it is **one-directional**: anything in the
351.9 ms that is not SPI makes `t(DIV16)` smaller, the DIV-4 prediction faster,
and the over-prediction larger. §19.7.4 also quotes the mean and not the
published `348.0-356.9 ms`.

**⑥ `0x80C00000` is justified in the shape `MAP-16` records as refuted.**
`MAP-16`: *"the original argument only excluded two known things ... it did not
exclude anything the loader allocates at runtime. Part one wrote onto a live
structure and nothing broke -- that was luck, not design."* §19.7.4's
justification is *"chosen to miss the bracket's own `0x80A00xxx` destinations"*
-- one known thing, and one that was never binding. `0x80C00000`-`0x80D00000`
has no `MAP-` row, and `MAP-17`'s measured-safe band is `0x80A00000`-
`0x80AF1002`, which this lies entirely outside; the write is **1 MiB, 4,096x the
256-byte windows** the project's address-selection evidence covers.

> **So the cell gains a `G0`-shaped precondition, written before it runs**:
> `DW 80C00000 16`, `DW 80C80000 16`, `DW 80CFFFF0 16` **before** the `FLR`.
> **Refutation condition: any pointer-shaped word (`0x8xxxxxxx`, `0xBxxxxxxx`)
> in any of the three, and the destination is re-chosen rather than argued
> about.** That is verbatim what `MEM-13` did for `MAP-17`.

**⑦ Two things the pass established that make the cell better, not worse.**
The eight recorded replies to `Y` are each a 256-byte `FLR` executed by stage 2
from DRAM at DIV 4. From their `.timing` files -- offsets and timestamps only --
31-34 bytes over a 0.009-0.010 s span with a maximum read-to-read gap of
**1.0-1.8 ms**, while 32 bytes at 38400 8N1 is 8.3 ms of pure line time: the
transfer plus the loader's per-`FLR` fixed cost is buried inside the serial
timing. **That bounds the fixed overhead at `<= ~1.1 ms`, 0.22 % of the
predicted 0.49 s** -- so the bands are not confounded by it, and it is also why
the cell must be 1 MiB: 256 bytes at any of the three candidate rates is
0.12-0.54 ms, under the instrument floor.

**⑧ The timeline in §19.7.3 had a gap, and closing it is one more
disassembly.** §19.7.1's loop copies 20,924 bytes to `0x80100000` and jumps
there; §19.7.3 reads the two `SFCR` writes out of `stage2-vma.dis`, built at VMA
`0x80400000`, at offsets `0x55F8` and `0x5900` -- **both beyond the 20,924 bytes
stage 1 copies**. So a stage sits between them and the divider was unknown
across it.

🟢 **量, the same desk session**: flash `0x0004F0`-`0x0056AC` disassembled at
`0x80100000` (it starts `j 0x80100050`, sets a stack at `0x801051B8+0x1000` and
calls `0x801000A0`) writes `0xB8001200` **zero times**, and it is the stage that
loads stage 2 (`lui s3,0x8040` at `0x801001C0`). **So the reset default holds
across the whole path from reset to stage 2's first write**, which is what
§19.7.3 needed and did not have.

**⑨ The region and the falsifier for the zero-writes claim.**
§19.7.3 says *"over all 4,848 bytes of stage 1"*. The copy source starts at
`0xBFC004F0`, so stage 1's **code** ends before byte 1,264 and 3,584 of the
4,848 are the payload it copies; scanning a superset is the conservative
direction and the claim survives, but the region that matters is the ~`0x1F8`
bytes before the `jr`. **What was scanned**: the disassembly text for
`ori <r>,<r>,0x1200` and for the literal `0xb8001200`. **What would falsify it,
and what was NOT scanned**: any store whose effective address resolves to
`SFCR` without that literal appearing -- `lui 0xB800` plus `sw rt,0x1200(rs)`, a
base loaded from a data word, an `ori`/`addiu` chain -- and the KSEG0 alias
`0x98001200` of the same physical register. **Named here rather than claimed
away.**

## 20. 🔴 `FW-34`'s free cell is withdrawn: the loader's `FLR` does not read through the memory-mapped window

§19.7.5 ③ made one thing a precondition rather than an assumption — *read the
`FLR` handler before spending the cell; whether it is a `lw`/`sw` loop through
`0xBD000000` or programmed I/O through `SFDR` decides whether the cell measures
the bus at all.* **It is programmed I/O through `SFDR`, and the cell as written
in §19.7.4 is withdrawn.**

**Materials**: `$FWRE_WORK/stage2-vma.dis` (56,592 bytes of `stage2.bin`
disassembled flat at VMA `0x80400000`) and `stage2.bin` itself. No vendor binary
was executed, so no `vendor-tripwire.sh` wrapper is owed. Working files under
`$FWRE_WORK/rebuild/bench-only/fw34-flrhandler/`.

### 20.1 What this repository already held, so that none of it is claimed as new

`docs/loader-command-semantics.md` §f already owns the `FLR` handler and goes as
far as its call into the flash driver:

* the handler is `0x804099AC`; three `strtoul(_,_,16)` with **no bound check**;
* **the first typed argument is the RAM destination**, and the echo prints the
  flash source first — the fact `tools/flrbracket.py` exists for;
* `0x80409A04` stores the length into `0x8040DD28`, the TFTP length global,
  which is why no `put` or `get` may follow an `FLR`;
* the confirmation is `0x80409B18`, and `Y`/`y` only;
* `0x80409A44` is `jal 0x80404F38`, labelled there `flash_read(dst, src, len)`.

**That file stops at that call. Everything below it is what §19.7.5 ③ asked for
and is new here.** ⚠️ The owner audit of the fifteenth session was caught twice
inventing a question the repository had already answered; this paragraph exists
so that this section cannot be read as a third instance.

### 20.2 讀 — the chain from `FLR` to the wire, five links, all in the image

| | address | what it is |
|---|---|---|
| 1 | `0x80409A44` | `FLR`'s handler calls `0x80404F38(dst, src, len)` |
| 2 | `0x80404F38` | moves `a0` (RAM dst) to `a3`, sets `a0 = 0`, and calls **through a function pointer at `0x8040FC10`** — so the call is `fp(0, src, len, dst)` |
| 3 | `0x8040FC10` | is `chip[0] + 0x3C` of a 72-byte-per-entry table based at `0x8040FBD4`. **`0x8040FBD4` is past `stage2.bin`'s last byte (`0x8040DD10`)**, so the table is `.bss` and filled at run time |
| 4 | `0x8040533C` | the registration function; `+0x38` gets a hardcoded `0x80406444`, and **`+0x3C` gets the caller's ninth argument** |
| 5 | `0x8040512C`, `0x804051E0`, `0x8040525C` | its **three** call sites — one per chip family — and **all three pass the same `0x804065DC`** at `32(sp)`. So the read method is not chip-dependent |

`0x804065DC` is a six-instruction shim. It supplies four stack arguments and
tail-calls the engine:

```
804065e4:  lui   v0,0xb00        ; 0x0B000000 -- the SPI `Fast Read` opcode
804065e8:  sw    v0,16(sp)       ;   arg5
804065ec:  li    v0,1
804065f0:  sw    v0,20(sp)       ;   arg6 = 1
804065f4:  sw    zero,24(sp)     ;   arg7 = 0
804065f8:  sw    v0,28(sp)       ;   arg8 = 1
804065fc:  jal   0x80405f70      ; the engine
80406600:  andi  a0,a0,0xff      ;   (delay slot) chip index
```

🟢 **`0x0B` is the second appearance of this byte in this project and the first
one predicted it.** `REG-13` (量 2026-08-25b, `DW B8001200 4`) read
`SFCR2`'s top byte as `0x0B` and wrote *`Fast Read`* beside it from the
datasheet. Here the same opcode is a compile-time immediate in the code that
issues the command. **A register reading and an instruction immediate, two
sources, no shared path.**

### 20.3 讀 — the data loop, and it never touches `0xBD000000`

`0x80405F70` issues the command through `0x80405CBC`, which busy-waits on
`SFCSR` bit 27 (`SPI_RDY`, `0x08000000` — the bit `REG-13` decoded as set) and
then writes the command word to `SFDR`. The data then comes back through the
same register:

```
80406000:  lui   v0,0xb800
80406004:  ori   a1,v0,0x120c    ; a1 = 0xB800120C  == SFDR, set ONCE
80406008:  lw    v0,0(a1)        ; <-- loop head: one 32-bit pop from SFDR
8040600c:  nop
80406010:  sw    v0,24(sp)
80406014:  move  v1,v0
80406018:  srl   v0,v0,0x18
8040601c:  sb    v0,0(s0)        ; big-endian unpack, byte 0
80406020:  srl   v0,v1,0x10
80406024:  sb    v0,1(s0)
80406028:  srl   v0,v1,0x8
8040602c:  sb    v0,2(s0)
80406030:  sb    v1,3(s0)
80406034:  addiu a2,a2,1
80406038:  sltu  v0,a2,a0        ; a0 = len >> 2
8040603c:  bnez  v0,0x80406008
80406040:  addiu s0,s0,4
```

**Fifteen instructions per four bytes**, a tail path at `0x80406044` for the
`len & 3` remainder, and a final call to `0x80405868` — 讀 that it is called
with `a1 = a2 = 0` once the loop ends; what it writes is not traced here, and
nothing below depends on it.

Three readings that matter, all 讀:

1. **The window base is not in this path.** 讀, a census of every `lui`
   immediate in the file: `lui <reg>,0xbd00` occurs **exactly once**, at
   `0x80409BC4`, and it is inside the **`FLW`** handler computing
   `offset + 0xBD000000` as a `printf` argument for `Write 0x%x Bytes to SPI
   flash#%d, offset 0x%x<0x%x>, …`. **The loader uses the window base for
   display and never for a load.**
   ⚠️ **The positive control on that census, because a `0` is a claim**: the
   same one-line method over the same file finds `lui …,0xb800` **115** times
   and `lui …,0xbfc0` twice. The search works; the window is absent.
   ⚠️ **The census is written against the mnemonic and its immediate for a
   reason.** A bare text search for `bd00` over the same file returns dozens of
   hits and **every one of them is `$sp`** — register 29 encodes as `bd`, so
   `lw sp,140(sp)` is `8fbd008c` and `addiu sp,sp,40` is `27bd0028`. On a flat
   binary disassembly the operand column and the hex column are the same
   grep-space, and this is the shape that puts a false zero *or* a false
   positive into a census.
   🔴 **AND HERE IS WHAT THE CENSUS DOES NOT COVER, named rather than claimed
   away** — the same treatment §19.7.5 ⑨ gave the `SFCR` zero-writes claim.
   **What was scanned**: the `lui` mnemonic and its immediate. **What would
   falsify the claim and was NOT scanned**: any construction of a
   `0xBD??????` address that never materialises `0xbd00` as a `lui` immediate
   — `lui 0xbcff` plus an `addiu 0x10000`, a base loaded from a data word, an
   `ori`/`addu` chain, or the KSEG0 alias `0x9D000000` of the same window.
   Two things make the residual small rather than absent: the read path was
   followed instruction by instruction from `0x80409A44` to the loop and it
   contains no such chain, and the loop's base register is loaded once, at
   `0x80406004`, from a `lui`/`ori` pair naming `SFDR`. **So the census is
   corroboration and the traversal is the evidence**, which is the opposite of
   how the first draft of this section read.

2. **There is no polling inside the loop.** `a1` is loaded once at `0x80406004`
   and the loop body contains no access to `SFCSR` (`0x1208`). Whatever paces
   the transfer is on the controller's side of the bus, not in the code.
3. **The loop executes from `0x80406008` — stage 2, in KSEG0 DRAM, cached.** So
   §19.7.2's instruction-fetch amplification is `1` here by construction. That
   part of §19.7.4's premise survives; nothing else does.

### 20.4 🔴 What this refutes, and it is §19.7.4's own sentence

> §19.7.4: *"Stage 2's own `FLR` executes **from DRAM** (no amplification) at
> **DIV 4** (no divider penalty) with **no Linux software path**. So it should
> run at the bus rate."*

**The first clause is true, the second is true, the third is false, and the
conclusion does not follow.** `FLR` has a software path of its own — fifteen
instructions and four byte-stores per word — and, decisively, **it reads through
a different port of the SPI controller than the thing it was going to be
compared against.** The kernel's `mtd_read` and stage 1's copy loop both read
the memory-mapped window; `FLR` pops a FIFO register. A number measured on one
says nothing about prefetch behaviour in the other.

**So `FLR 80C00000 100000 100000` cannot answer `FW-34`'s remaining question,
and the cell is withdrawn rather than re-banded.** §19.7.5 ① had already found
that its three-outcome table read one number three ways; ② had found one band
unreachable. This is the third and it is the one that removes the cell: the two
earlier findings would have been repaired by re-writing the table.

⚠️ **What survives from §19.7.5 and is not withdrawn**: ⑦'s bound of `≤ ~1.1 ms`
on the loader's per-`FLR` fixed cost, ⑧'s finding that the intermediate stage
also writes `SFCR` zero times, and ⑨'s named falsifier for the zero-writes
claim. None of them depends on which port the read uses.

### 20.5 The cell that replaces it, and it measures something this project needs

The `FLR` timing is still worth one reading — but for the SPI **controller**,
not for the window, and it is worth writing down because the flash-write work
(`R5b`) goes through this same `SFDR` port.

**The model, 推, with every term named.** After one command the loop pops a
32-bit word per iteration with no polling, so the pacing is either

* **streaming** — the controller keeps the `Fast Read` open and clocks 32 bits
  per word: **32 SPI clocks/word**; or
* **per-word re-issue** — it repeats `cmd(8) + addr(24) + dummy(8) + data(32)`:
  **72 SPI clocks/word**.

`REG-13` 量 `SFCR = 0x3FC00000` at the prompt, cold and warm alike, so
`SPI_CLK_DIV = 001B` = **DIV 4** during `FLR` — this is the one place in this
project where the divider is *measured* rather than defaulted. ⚠️ **The
datasheet's formula is `SPI Clock = DRAM Clock / SPI_CLK_DIV`, and nothing in
this repository has ever asserted that the "DRAM Clock" is `CLK-02`'s measured
200.0049 MHz.** That identification is carried silently by §19.7.3's 4×. **The
cell below is the first thing that would test it.**

At 200 MHz / 4 = 50 MHz: 32 clocks = **640 ns/word**, 72 clocks = **1,440
ns/word**. The loop's own cost is **37.5–112.5 ns/word** (15 instructions;
`CLK-01`'s 400 MHz with CPI between 1 and 3, because `CLK-03` measures `f/CPI`
and not `f` and says so). It is a minority term in every band, which is why the
CPI ambiguity does not have to be resolved first.

> **The cell.** `FLR 80A90000 100000 40000` — **256 KiB** of flash
> `0x100000`–`0x140000` into RAM `0x80A90000`, timed from the wire-silent gap
> between the echo of `Y` and `Flash Read Successed!`, exactly as §19.7.5 ⑦
> measured the 256-byte reads. 65,536 words.
>
> | outcome | what it establishes |
> |---|---|
> | **42–49 ms** | streaming, DIV 4, and the datasheet's *DRAM Clock* is `CLK-02`'s 200 MHz. All three at once — the cell does not separate them |
> | **94–102 ms** | the controller re-issues the command per word. `R5b` inherits that number |
> | **≥ 150 ms** | the divider is not DIV 4 during `FLR`, or the clock is not 200 MHz, or the loop stalls beyond this model. **Not attributable** |
> | **≤ 25 ms** | the SPI clock is *faster* than DIV-4-of-200 MHz — the identification of *DRAM Clock* with `CLK-02` is wrong upward |
>
> **Refutation condition for the whole framework, written first**: any reading
> below the loop's own floor of **2.5–7.4 ms** means the transfer is not
> word-at-a-time through this loop, and the disassembly above is wrong about
> which code ran.

**Three things about the destination, and they are the reason it is not
`0x80C00000`.**

1. §19.7.5 ⑥ objected that `0x80C00000` sits outside `MAP-17`'s measured-safe
   band and that a 1 MiB write is 4,096× the evidence base. **`0x80A90000` +
   256 KiB = `0x80AD0000` lies entirely inside `MAP-17`'s `0x80A00000`–
   `0x80AF1002`.** The objection is answered by construction rather than by a
   new argument, and ⑥'s `G0`-shaped head/middle/tail pre-read becomes a
   confirmation of an existing band instead of a new safety case. **It is still
   run**, and its refutation condition is `MEM-13`'s verbatim: any
   pointer-shaped word and the address is re-chosen.
2. **`0x80A90000` is exactly `probe3`'s `ARENA_END`.** 讀 `probe3.c:440-441 (#define ARENA 0x80A10000u)`:
   `ARENA = 0x80A10000`, `ARENA_END = 0x80A90000`. So the read cannot land in
   the arena — which matters because `MEM-17` (量 2026-08-31) is that **DRAM
   keeps a previous cycle's `FLR` output across a power cycle**, and a
   `probe3` arena pre-loaded with flash bytes would make `V_NEVER` mean two
   things. The destination is chosen against a measurement, not against a map.
3. **256 KiB is what fits, and it is also enough.** `0x80AF1002 − 0x80A90000`
   is 397 KiB, so 256 KiB is the largest power of two inside the band; and at
   the fastest band it is 42 ms against ⑦'s `≤ ~1.1 ms` fixed cost — **38×
   the instrument's own floor**, with the bands themselves ≥45 ms apart. The
   1 MiB of §19.7.4 was sized against a model that no longer applies.

⚠️ **Ordering, unchanged and still binding**: `FLR` writes the TFTP length
global, so this cell must come **after** any `put` on its power cycle and no
`put`/`get` may follow it. `J` needs no TFTP global, so `put` → cell → `J` is
legal on one cycle; whether it is *wise* to put an unrehearsed 256 KiB transfer
in front of a seating is a different question and belongs on the card.

### 20.6 What `FW-34` keeps, and the only instrument that could close it

`SPEC.md` §17's remaining `FW-34` row asks whether the memory-mapped window
prefetches a sequential fetch stream. **Nothing at the loader prompt can answer
it, and that is now 讀 rather than an omission**: the loader has exactly one
instruction that names the window and it is a `printf` argument. The two agents
in this project that read through the window are stage 1 (no console, no timer
the console can read) and the kernel (whose figure §19.4 already has, with a
whole userspace path folded into it).

**The third is a bare-metal payload, and this project has one.** `probe3` ships
a calibrated `TC0` (`CLK-17`, 69.9983 ns/tick; Group T's `t.cal` hi/lo ratio
came out 2.0003, so the bracket scales) and already executes uncached KSEG1
loads. A cell that times N sequential `lw` from `0xBD000000` against N strided
`lw` — stride chosen past any plausible buffer — reads the amplification
directly, with the same loop over uncached DRAM as the negative control that
says the difference belongs to the window rather than to the loop.

**That is a `probe3` change, and it is recorded here rather than started here.**
It would ride the same rebuild as the retained bitmap and the `M(T)` table,
which is the only reason it is worth raising now instead of after the seating.

🔄 **2026-08-31: it was started, and it grew a third address space on the way.**
`probe3` Group F, eleven result words, `docs/probe3-cells.md` § 6.8. The
paragraph above names `0xBD000000` and uncached DRAM; what it does not name is
**`0xBFC00000`**, and that is where § 19.7.2's ≤9× actually lives — stage 1's
loop executes at `0xBFC001D0`, a different physical decode (`0x1FC00000`) from
the window this section proposes to time. Nothing in this project had ever
compared the two, so timing only `0xBD000000` would have left *the two windows
behave alike* in the load-bearing position and unmeasured. `f-alias` is that
comparison, and it costs no committed flash byte: only the count of mismatching
word pairs enters the block.


### 20.7 🟢 2026-08-31 (seating 8) — `FW-34`'s last row is closed, by the instrument § 20.6 named, and two things travel with the closure

`probe3` Group F ran on the silicon. **`f.win.seq = f.win.str = 30,354` ticks,
so `R = 1.0000`** — the `R ≤ 1.15` band. The memory-mapped window does not
buffer a single-word read; an uncached instruction fetch is a single-word read;
so § 19.7.2's `≤9×` is **`9×`**, and the decomposition of the ~16× is

```
access width  1x   (refuted at the desk 2026-08-31: both paths use lw)
SPI divider   4x   (stage 1 runs on the reset default DIV 16; it never writes SFCR)
fetch amp     9x   (stage 1's loop executes at 0xBFC001D0, KSEG1, uncached)
              ---
              36x  upper bound, against a MEASURED ~16x
```

⚠️ **The 2.1–2.3× gap is unchanged and it is still the term the model does not
have**: § 19.4's figure is `busybox wc -lc`'s end-to-end user-space rate and the
model prices only the SPI bus. Closing `FW-34`'s last row does not close that
gap, and this paragraph exists so the two are not read as one.

🟢 **§ 20.6's *"only instrument that could close it"* was right, and it did more
than that row asked.** `f.alias = 0` and `f.boot.seq/str = 30,353/30,354`
compare `0xBFC00000` against `0xBD000000` **for the first time in this
repository** — § 19.7.2's `≤9×` rests on stage 1 executing at `0xBFC001D0`,
which is a different decode (`0x1FC00000`) from the window § 20 spent its whole
length on, and nothing had ever shown the two behave alike.

🔴 **§ 20.5's absolute cell comes back undetermined rather than confirmed.**
`f.win.str / 1024` = **29.64 ticks** = 103.7 SPI clocks at DIV 4 / 50.0 MHz,
against a predicted 72 clocks = 20.57 ticks. It is outside all three rows of
§ 6.8.2's absolute table, so *72 clocks · DIV 4 · the datasheet's `DRAM Clock`
is `CLK-02`'s 200 MHz* — the identification § 20.5 records as never having been
asserted here — **is not established by this reading**. ⚠️ It does not touch
`R`: a ratio of two legs of one loop is clock-independent. And it does not
touch § 20.5's `FLR` cell, which measures the **`SFDR` port** and not this one:
`LDR-42`, two ports of one controller.

🔴 **A control that fired, and it is § 6.8.2's rather than the device's.** The
guard *"`f.dram.str / f.dram.seq` must be strictly less than `R`"* measured
1.3046 against 1.0000. **It is unsatisfiable on the branch that closes this
row.** `docs/probe3-cells.md`'s Ran section owns the rewrite it needs; recorded
here because § 19.7's conclusion now rests on a verdict whose written control
did not hold.

---

## 21. `R3-11`: the artefact, the write-up, and `R3`'s closing conditions read one by one

**2026-08-31, twentieth session, desk, no power.** `R3-11` is the twelfth and
last step of `R3`. It produces two things: the v0.2 artefact `plan/ARTIFACTS.md`
§2 asks for, and this section — the comparison of what `R3` said it would
establish against what it did.

### 21.1 The artefact is a REEL, and the number that was wrong was wrong by being short

The v0.2 take is not a screen recording of a session. It is
`tools/replay-capture.py reel config/r3-11-reel.tsv` — committed captures
replayed into a terminal at their own wire speed, in an order that is data.
🟢 **The property that buys**: a stranger who clones this repository runs one
command and gets the same bytes, and the `.log` remains the artefact rather
than a video file becoming one.

🔴 **Every number below is the tool's, not this paragraph's.**
`replay-capture reel <tsv> --budget` prints them and `--self-test` `R15`–`R18`
assert them; until today **nothing read that file at all**, and its running
time lived in a comment inside it and in a sentence in `PROGRESS.md`.

| | segment | capture | pause |
|---|---|---:|---:|
| 1 | `bench/2026-08-31/W-3` — D1–D4, my kernel from RAM to a shell | 7.021 | 2.0 |
| 2 | `bench/2026-08-31/W-5b` — D2, the build stamp is mine | 0.062 | 2.5 |
| 3 | `bench/2026-08-31/M-a` — D4, a typed command returns output | 0.063 | 2.0 |
| 4 | `bench/2026-08-31b/X-b2` — 4 MiB through my MTD path | 1.268 | 2.0 |
| 5 | `bench/2026-08-31/M-d` — and it cannot be written through it | 0.048 | 2.5 |
| 6 | `bench/2026-08-31/W-7a` — D5, it pings, 4 of 4 | 3.099 | 2.0 |
| 7 | `bench/2026-08-31c/K-J` — **the control** | 33.188 | 2.0 |
| | | **44.749** | **15.000** |

**TOTAL 59.749 s**, against `plan/ARTIFACTS.md` §2's **60 s**. `R16` is the
case that fires if an edit crosses it — 🔴 **and that is the direction nothing
was watching**, because the row that had been wrong all week was wrong by being
*short* (24 s against a spec of 60), and the repair proposed for a short reel
is always *more capture* and never *more pause*.

### 21.2 Segment 7 is a control, and it is the anti-DoD happening on video

`PROGRESS.md`'s anti-DoD paragraph says a banner is not evidence that my kernel
ran, **because this loader re-stages `0x80500000` from flash on a watchdog
reset** — 2026-08-25, `R1g-4b`, where a second `J 80500000` booted the vendor's
kernel. `bench/2026-08-31c/K-J` is that trap happening, in one capture:

* `t = 0 … 2.4 s`, offsets 0–6049: `J 80500000`, then `probe3` runs and prints
  its whole UART report, ending `rlxprobe: end`.
* `t = 2.5 … 33.188 s`, offsets 6066–8002: `Reboot Result from Watchdog
  Timeout!`, `Jump to image start=0x80500000...`, and **the board's own vendor
  firmware boots end to end** — `start address: 0x80003440` where segment 1
  shows `0x80003600`, `Realtek WLAN driver - version 1.6 (2013-02-21)` where
  segment 1 shows `(2012-12-04)`, `init started: BusyBox v1.13.4 (2018-01-10
  14:56:45 CST)`, `boa: starting server pid=350, port 80`.

So a viewer's first objection to segments 1–6 — *how do I know that is not the
stock firmware* — is answered inside the artefact rather than in prose beside
it, with the discriminators visible in both directions.

🔴 **68 % of that segment's 33 s is inter-line gap, and that is NOT the dead
terminal `config/r3-11-reel.tsv` forbids.** The gaps are the vendor firmware's
own: 5.019 s decompressing, 4.400 s in the WLAN driver, 3.416 s after BusyBox's
init line. 量, and the comparison that settles it is segment 1, which is **96 %
gap** and which nobody calls padded. Dead terminal is time the *card* bought
with `--seconds`; this is time the *device* spent.

⚠️ **And a claim this segment does NOT support**: `quietm` reaches a shell in
7.02 s and the vendor firmware takes ~33 s to finish its init, and those are not
comparable. Mine is a kernel plus a small initramfs reaching `/bin/sh`; the
vendor's brings up wifi, a bridge, DHCP, NTP, UPnP and an httpd. The reel shows
both and the title says neither is faster.

### 21.3 What went in, what did not, and why — because the material was named before it was chosen

The nineteenth session's carried-forward names four pieces of seating-8
material for this reel. Two of them went in, inside one capture, because a reel
row is one whole capture by construction:

| material | in | why |
|---|:-:|---|
| `probe3`'s execution | ✅ | `K-J`, `t = 0…2.4 s` |
| its UART report | ✅ | the same 2.4 s |
| a full vendor-firmware boot | ✅ | `K-J`, `t = 2.5…33.2 s` |
| the 718-word read-back | ❌ | `K2b-rb` is 8,486 bytes of hexadecimal in 2.316 s and its claim — *the block was sealed, read back, and `rbcheck` judged it* — is **not visible in the pixels**. It belongs in a write-up where it can be checked. It would also have put the reel at 64.1 s |

⚠️ **`bench/2026-08-31c/K-A` is not material and that is not a judgement call**:
25.065 s of `console-capture --esc 25` spamming ESC at the loader, `<RealTek>`
`Unknown command !` about 130 times. The last ~50 s of `K2-J` is the same
(`--esc-after 60`). **`K-J` is the only clean capture of `probe3`'s report in
this seating**, and what follows it in that file is the vendor boot — the two
cannot be separated.

🟢 **Checked before it went in**: `grep -aoE '([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}'`
over `K-J.log` returns nothing, and `flashwin scan` (new today) returns CLEAN.
A vendor firmware boot printing this unit's MAC into a video would be a leak
the reel's own reproducibility makes permanent.

### 21.4 `R3`'s DoD, read one row at a time

The gate's own decomposition, written 2026-08-28 **before** any of it was
attempted, and each row read against the capture that tested it.

| | claim | met | the capture, and the discriminator |
|:-:|---|:-:|---|
| **D1** | the image is delivered and entered | 🟢 | `---Jump to address=80500000` followed by output that is not the loader's — `bench/2026-08-31/W-3.log`, and 34 further times across seatings 5–8 |
| **D2** | the decompressor runs and **my** kernel is entered | 🟢 | `Linux version 2.6.30.9 (key@K) (gcc version 3.4.6-1.3.6) #1 Sun Aug 30 18:56:00 CST 2026` — 量, `W-5b.log`, and that stamp is `quietmc`'s build minute, not `loudm`'s — 🔴 **and the anti-DoD is satisfied POSITIVELY, not by absence**: three strings the vendor image cannot produce appear together — the header's own `start address: 0x80003600` (the vendor's staged image says `0x80003440`), `RLXFW-B00`…`B10` plus `RLXFW-R3-RUNG1-OK`, twelve marks that exist only in my tree, and that build stamp. `W-3.log`, `W-5b.log` |
| **D3** | early bring-up completes | 🟢 | the console echoes and userspace is reached. ⚠️ **The row's own written observable was `MemTotal:` and that string is not printed by any configuration of this kernel** — recorded as a defect in the DoD rather than as a miss (§16, `R3-6`'s corrections) |
| **D4** | userspace is reached and the shell accepts typing | 🟢 | `bench/2026-08-31/M-a.log`: a typed command returns output. Also `M-b2`/`M-c2`/`M-d` and the seating-7 `X-*` set |
| **D5** | it pings | 🟢 | `bench/2026-08-31/W-7a.log`, 4 of 4 from the board, **and** the host's own capture holds both the echo requests and the replies |

**Five of five.** 🔴 **And the sentence `R3`'s refutation condition asks for is
narrower than that**: *D1 through D5 all hold **in one boot**, with the
discriminator present*. They do — `bench/2026-08-31/W-3` → `W-5b` → `M-a` →
`M-d` → `W-7a` are one power cycle of `quietm`, in order, and `W-5b` carries the
stamp. It is not five rows averaged across four seatings.

### 21.5 The twelve steps

| step | | closed |
|---|---|---|
| `R3-0` | the step list, the DoD decomposition, decisions A and B | 2026-08-28, before any measurement |
| `R3-1` | `TC-g` and the four unexplained violations | 2026-08-28 |
| `R3-2` | `TC-d` part one — the loadable image, against the vendor's own `nfjrom` | 2026-08-29 |
| `R3-3` | `TC-d` part two — the desk execution channel | 2026-08-29 |
| `R3-4` | `rlxfw_defconfig` as an enumerated diff, plus the drift check | 2026-08-28, **and refuted by its own step** |
| `R3-5` | the initramfs from this unit's own rootfs, with a manifest | 2026-08-28 |
| `R3-6` | the boot ladder and the console instrument | 2026-08-28/29 |
| `R3-7` | the seating sheet and the prediction blocks | 2026-08-29 |
| `R3-8` | the first seating: `R3-8a` power cycle 2, `R3-8b` power cycle 3 | 2026-08-29 / 2026-08-30 |
| `R3-9` | the iteration — whatever the first seating refuted | desk half 2026-08-30/31, bench half 2026-08-31 (seating 8) |
| `R3-10` | power cycle 4, the second half of the `FLR` bracket | 2026-08-30 |
| `R3-11` | **this section, and the reel** | 2026-08-31 |

**Twelve of twelve.** Budget was **12 段, 猜, uncalibrated**; actual is counted
in `LOG.md` by the gate board's own definition and recorded there, not here.

### 21.6 The refutation condition, the two decisions, and the stop-loss

**The gate's refutation condition**, verbatim: *"`R3` is not closed by a shell
prompt. It is closed by a capture in which D1 through D5 all hold in one boot
and the discriminator string that only my tree emits is present. Three of five
is `R3a`, recorded as such."* — **met**, §21.4.

**Decision A** (rlxfw's kernel is built with `rsdk-1.3.6-4181`) is refuted by
any of: that toolchain failing to build an object of the `R3` configuration; the
four unexplained violations in the 4181 `vmlinux` turning out to be **compiler
output on an executed path**; or a boot failure whose signature is a load-use
hazard at a compiler-generated site. 🟢 **None fired.** Nine trees built with
it; `RUNSHEET` `P2` and today's residual sweep report **0 violations across
eight object trees** and `Q5` shows the same six sources at `-march=5281` carry
**11**; no boot in seatings 5–8 stopped at a hazard site.

**Decision B** (the initramfs is built from this unit's own extracted rootfs) is
refuted by the initramfs failing to unpack, by `arch/rlx` needing a source change
to support it, or by the decompressed image exceeding 5,242,880 bytes at
`LOAD_START_ADDR = 0x80500000`. 🟢 **None fired**; `/bin/sh` came up on every
boot and the ceiling was never approached.

**The stop-loss**, four clauses, and **not one of them was reached**: no run of
five boot attempts failed to reach D2 (the halving experiment was never needed);
D4 was reached on the **first** seating, not the second; **no capture shows a
flash-write path taken** — 35 `--send`s in seating 5 were `DW` reads, two `J`s
and userspace commands, `AUTOBURN` read `00000000` before every `J`; and `R3-3`
cost one desk segment, as budgeted.

### 21.7 🔴 What `R3` did NOT establish, listed because the gate closes anyway

* **`G8b`'s sentence is still unsayable.** No flash-write command was issued in
  any seating of this gate, and *that is not the same sentence as "not one flash
  byte is written"*. The `FLR` bracket reaches **1,024 of 4,194,304 bytes =
  0.0244 %** and `H601` **512 of 8,192 = 6.3 %**; it cannot see two writes that
  cancel, nor any write outside four 256-byte windows. No full re-dump ran.
  `SPEC.md` `FLS-20`.
* **There is still no driver of mine.** D5's ping went out through the vendor's
  `rtl819x`, which is in the vendor's own configuration. `R6` is the gate that
  changes that sentence, and `R3` must not be written up as though it had.
* **D3's written observable was wrong** and the row passed on a substitute
  (§21.4). A DoD whose observable does not exist is a defect in the DoD, and it
  is recorded rather than quietly repaired.
* **`R3-2`'s `TC-d` half stayed half-done for one step** and is recorded as a
  debt in the running-order note, not as a pass.
* **`R1h`'s decision ② is still `R1-gate`'s**, answered on the D side by
  `probe3` and not by this gate.

