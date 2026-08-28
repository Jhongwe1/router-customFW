# How rlxfw's own kernel is built, wrapped and reached

**Owner of: which toolchain builds rlxfw's kernel, what its configuration is
allowed to differ by, what the loadable image is made of, what the first boot
mounts, and how far a kernel for this board can be run at the desk.**
Written 2026-08-28, desk, no power, no device reading.

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

### 1.4 What `hazlint` is not looking at, and it is 40 % of the text

The published window stops at `0x80158000` because that is the bound that serves
all three builds below their lowest `[MIPS16]` symbol. For the 4181 build alone
the bound can be `0x8016c844`, and `.init.text` and `.exit.text` sit **above** the
whole MIPS16 band and are pure 32-bit code. 量:

| span | bytes | loads | violations |
|---|---:|---:|---:|
| published window `[0x80000000, 0x80158000)` | 1,409,024 | 61,568 | 4 |
| widened to the first MIPS16 symbol `[0x80000000, 0x8016c844)` | 1,493,060 | 65,048 | **5** |
| `.init.text` `[0x8029f000, +0x13d74)` — **the boot path** | 81,268 | 2,297 | **0** |
| `.exit.text` | 4,688 | 157 | 0 |
| **not scanned**: the MIPS16 band `[0x8016c844, 0x8025ac64]` | **975,904** | — | — |

**`.init.text` is clean, and that is the section `R3`'s first boot spends most of
its time in.** The unscanned band is 40.2 % of `.text` and it is the wireless and
NIC driver region. `TC-f` — `hazlint` silently discarding `--range` on an ELF
input — is what has to be fixed before a whole-image gate can exist; the honest
statement today is a coverage figure, not a clean bill.

---

## 2. `TC-g` — which `arch/rlx` assembly relies on the assembler

`asm/stackframe.h` sets `.set reorder` outright and seven of the seventeen `.S`
files under `arch/rlx` carry no `.set` directive at all, so they are assembled in
gas's default reorder mode. **The question is not which files are in that mode.
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
`lx4180`, which is on the padded side, so the real kernel build gets the twelve
`nop`s. **That safety is incidental and it should be asserted rather than
assumed.** The check is one `hazlint` pass over the objects the build produced,
and it is cheap enough to be a build step.

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

### 3.3 The pipeline reproduces the vendor's own intermediates

The drop left `rtkload/vmlinux-stripped` (3,001,168) and `rtkload/vmlinux_img`
(2,953,660) beside the `image/vmlinux.elf` (3,441,133) they came from, so stages
1 and 2 have a vendor-made reference. 量, running the vendor's own `strip` and
`objcopy` from a scratch directory under `tools/vendor-tripwire.sh`:

* `vmlinux-stripped` — **byte-identical to the vendor's**
* `vmlinux_img` — **byte-identical to the vendor's**

`K4` is satisfied. My own kernel through the same two stages: 2,894,792 stripped,
**2,846,948** as a flat image (sha256 `a469c52e…`).

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

---

## 4. Decision B — the first boot mounts an initramfs from this unit's own userspace

1. 🔴 **Safety dominates on a one-device project.** An initramfs boot never
   instantiates an MTD partition map. The flash-root route needs me to author
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

---

## 6. The configuration, and why `oldconfig` is banned

量 2026-08-28: the `vmlinux` on disk differs from
`boards/rtl8196e/config.linux-2.6.30.RTL8196E_88E_GW` on **22 symbol lines**.
Nineteen are symbols `oldconfig` dropped because nothing offers them any more.
**Three are not:**

| symbol | template | built | |
|---|---|---|---|
| `CONFIG_ARCH_CPU_SLEEP` | *not set* | **`=y`** | 🔴 turned **on** |
| `CONFIG_CPU_HAS_SLEEP` | absent | **`=y`** | 🔴 turned **on** |
| `CONFIG_PHY_EAT_40MHZ` | `=y` | absent | turned off |

`yes '' | make oldconfig` answers every new prompt with the **default**, and for
`ARCH_CPU_SLEEP` the default is `y` where the vendor chose `n`. 🔴 **So the
724-object build is not a build of the vendor's configuration**, and a CPU sleep
path is exactly the kind of thing that turns a first bring-up into a hang with no
output.

🆕 **One line of that diff is already known**: `CONFIG_CMDLINE` is `"console=ttyS0,38400 root=/dev/mtdblock1"`, and an initramfs boot must not name a root device that the kernel will try to mount.

`rlxfw_defconfig` is therefore specified as **a diff with a reason per line**
against the vendor template, and the check reads the `.config` the build actually
used rather than the file that was copied in — `oldconfig` sits between them.

---

## 7. What could still be wrong

* **§1's decision rests on four readings of one vendor's tools.** `SPEC.md` §0's
  two-source rule is not satisfied by any of them alone; what is claimed is
  agreement among four readings of Realtek's own instruments plus this unit's own
  image, not corroboration by a second party.
* **§1.2's conclusion is about a microarchitecture nobody has asked.** The four
  sites are a hazard *if* `movz` reads `rd`, and that is `TC-h`, unmeasured.
* **§2's twelve hazards are counted by `hazlint` in a mode that has never
  produced a false positive on hand-written `arch/rlx` assembly** — and a
  classifier that has not been shown to be able to fire wrongly on this material
  is not the same as one that does not.
* **§5's channel runs a different core.** Everything it certifies, it certifies
  for a MIPS32 4Kc with interlocks, a malta memory map and no RTL8196E
  peripherals.
* **§3's pipeline is verified at stages 1 and 2 only.** The LZMA and `cvimg`
  stages are read out of the vendor's Makefile and confirmed by unwrapping two
  images; they have not been re-run to produce a byte-identical `nfjrom`.
* **Nothing in this file has been executed on the device.** Not one number here
  is 量 in `SPEC.md`'s sense.
