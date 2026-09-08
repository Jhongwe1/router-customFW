# `rtl819x-spi` — a read-only MTD device driven by programmed I/O

**`R5-5`, desk half. 2026-09-07, forty-first segment. No power, no flash byte,
no `FLR`.** Owner of every finding this step produced; `SPEC.md` indexes them
and does not restate them.

The step's DoD was rewritten and frozen in the fortieth segment
(`PROGRESS.md` § Step list, `R5-5`'s row): four rows, `D1`–`D4`, plus a
negative control. **This file does not reopen it.** What it does is record
seven things measured *before the first line of the driver was written*, two
of which change what two of those rows mean.

---

## 1. The finding that decided the step's shape

🔴 **The Linux MTD read path in this image is programmed I/O through
`SFCSR`/`SFDR`, not the memory-mapped window.**

讀, source, `drivers/mtd/chips/rtl819x/spi_probe.c:101-103` — `spi_chip_setup()`
installs, with no `#ifdef` around it:

```c
mtd->erase = mtd_spi_erase;
mtd->read  = mtd_spi_read;
mtd->write = mtd_spi_write;
```

and `mtd_spi_read` (`spi_flash.c`) reaches `spi_flash_info[chip].pfRead`, which
for an unmatched chip id is `SpiRead_11110B` → `ComSrlCmd_ComRead` → `SFDR`.
`rtl819x_flash.c` gets that `mtd_info` from `do_map_probe("flash_bank_1", …)`,
and `spi_probe.c:70` registers the chip driver under exactly that name.

讀, **artefact**, `bench-only/r54-20260906/vmlinux` (3,978,029 bytes,
sha256-16 `04cd5b151aae6df4`), disassembled with Ubuntu's
`mips-linux-gnu-objdump` 2.42 — **not a vendor binary**, so no tripwire is
needed:

| | |
|---|---|
| `mtd_spi_read` at `801a1928` | loads `mtd->priv` (`+196`), then `map->fldrv_priv` (`+44`), then `chip_info->read` (`+16`), returns **`-122` = `-EOPNOTSUPP`** if NULL, else `jalr v0` |
| `do_spi_read` at `801a40a0` | computes `spi_flash_info + chip*72` (`sll 3; addu; sll 3`, base `lui 0x805e; addiu -28992` = `0x805D8EC0`, matching `System.map`'s `805d8ec0 B spi_flash_info`), loads `+0x3C` = `pfRead`, `jalr v1` |

**Neither function mentions `0xBD000000`.**

### 1.1 The control, and it is one scan with the counters side by side

| scanned | count | |
|---|---:|---|
| `jal → rtl8196_map_copy_from` | **0** | the claim |
| `jal → ComSrlCmd_ComRead` | 1 | the control |
| `jal → ComSrlCmd_InputCommand` | 2 | the control |
| `jal → SFCSR_CS_L` | 17 | the control |
| `.data` words equal to `801a482c` | **0** | `rtl8196_map_copy_from`'s address is never stored |
| `.data` words equal to `bd000000` | 2 | so the scan **can** see `.data` — `spi_map[0].phys` and `.virt` |

A scan whose only output is a zero proves nothing. Four non-zero counters came
out of the same pass.

### 1.2 🔴 A trap that scan walked into, kept because the next census will meet it

`jal → mtd_spi_read` is **0** and `jal → SpiRead_11110B` is **0**, and both
functions are live. They are reached through function pointers — the two
`jalr`s in the table above. **A `jal` census cannot see an indirect call, so a
zero from one is not "dead code".** What rescued it here is that the callers
were disassembled in full first, for a different reason.

⚠️ `FW-39`'s technique is **not** affected: it counts `sw` to an *address*,
which is a different question and has no indirect-call blind spot.

---

## 2. What this does to `FW-34`, and what survives

`SPEC.md` `FW-34` states the chain as `mtd_read → part_read → rtl819x_flash`
and spends its whole alternative-explanation argument on
`rtl8196_map_copy_from`'s 1024-byte silent short read, decided by
`CONFIG_MTD_COMPLEX_MAPPINGS` being unset.

🟢 **The conclusion survives and gets stronger.** `H1` (a truncated read
reported as success) is excluded — not because the macro expansion wins over
the driver's function pointer, but because **the map layer is not on the path
at all**: the chip driver's `mtd->read` bypasses it, and the function's address
is never even stored.

🔴 **The mechanism named is wrong, and so is one number's provenance.** The
`~16×` speed ratio is a measurement and stands. Its decomposition in
`notes/kernel-build.md` §19.7.2 — `4× SPI divider × ≤9× fetch amplification` —
loses **both** terms:

* the `≤9×` compares stage 1's uncached KSEG1 *instruction fetch* against the
  kernel's I-cache-resident loop, over the **window**. The kernel's loop is not
  on the window.
* the `4×` used `REG-13`'s loader-prompt `SFCR = 0x3FC00000` as the kernel's
  divider. It is not — see §3.

**`FW-34`'s own row is where the correction lands**, and `notes/kernel-build.md`
§19.7 is the owner of the decomposition.

### 2.1 And it corrects the frozen `D3`'s citation — the wrong half of the right row

`D3` reads *"the same 4,186,112 bytes read once more through `0xBD000000`
(`FW-34` measured that path over the full 4,194,304 bytes)"*.

🔴 That parenthetical is false. `FW-34`'s 4 MiB reading is
`busybox wc -lc < /dev/mtd0ro`, which goes through `mtd_spi_read` — the PIO
path. **Nothing in this project has ever read the memory-mapped window past
`probe3` Group F's 1,024 words.**

🟢 **The right half of the same row is the one `D3` needed all along.**
Group F: 1,024 uncached loads through `0xBD000000` at stride 4 and at stride
1,024 took the **same 30,354 ticks**, `R = 1.0000` — the window serves a
single-word read as its own transaction and does **not** buffer. That is what
makes `D3` two paths rather than one path read twice: an independence at the
**controller**, not merely in the source. Without it, `equal` would be
compatible with a controller handing back the same buffered data twice.

**So `D3` is not weakened by §1 — it is better founded and it is worth more**,
because the window side of it will be this project's first read of that path
beyond a kilobyte.

### 2.2 🔴 And the closing audit found two `量`-marked rows that are not in `FW-34` at all

Found by `git grep` over the whole repository rather than by re-reading this
segment's own edits, which is the audit method that keeps catching things.

`SPEC.md` `FLS-11` and `MAP-12` both state, in as many words, that what
supports their `量` mark is *"the kernel's 4,194,304 bytes, and that was
under Linux"*, read *"through `map->virt = 0xbd000000`"*. **That reading is the
PIO path.** So neither row's stated evidence is about the window.

🟢 **The `量` survives on different evidence at a different width.**
`probe3` Group F — 1,024 uncached loads through `0xBD000000` at two strides,
both 30,354 ticks, `R = 1.0000`, with `f.faults=0` / `f.alias=0` /
`f.live=0f0f` as refutation controls. **4,096 bytes, not 4,194,304.**

🔴 **And `FLS-11`'s ⚠️ note inverts.** It reads *"that was under
Linux; this repo has never read this window at the loader prompt, so 'it is
live at the prompt' is 推"*. `probe3` is a bare-metal payload entered with
`J`. **The window is measured bare-metal and has never been read under Linux
at all.**

🟢 **Which is a third reason `D3` is worth more than it looked.** Its
MMIO pass is the first read of this window under Linux, and the first past a
kilobyte, and it is what would close the half `FLS-11` now has backwards.

🟢 **2026-09-08 (seating 16): it did, and the two paragraphs above are now
past tense.** `C1-V4` read the window under Linux for the first time (4 KiB),
`C1-VF` for the first time past a kilobyte, and over all **4,194,304** bytes the
window and the PIO path are byte-identical — `cmp_equal 1`,
`cmp_first_diff -1`, `d1_d3_agree 1`. 🔴 **The reading is licensed by a control
that fired**: `C1-NG` corrupted one byte at 1,048,576 and `cmp_first_diff`
landed on 1,048,576 with `cmp_equal` going 1 → 0, so `equal` is not what a
comparator that cannot fail prints. `SPEC.md` `FLS-11`/`MAP-12` are updated;
this section keeps its original wording because it is the argument that made
the cell exist.

⚠️ **One unchanged value, three pieces of evidence, two retracted** —
the loader's `FLW` `printf` (a compile-time constant, 2026-08-31) and `FW-34`'s
4 MiB (the wrong path, today). `0xBD000000` has never been in doubt; the
sentence about how it is known keeps failing.

---

## 3. 🔴 The kernel does not run the SPI bus where the loader left it

讀, artefact, `801a2ac8`–`801a2ad4` inside `ComSrlCmd_RDID`:

```
801a2ac8:  lui  v0,0xb800
801a2acc:  ori  v1,v0,0x1200        ; v1 = SFCR
801a2ad0:  lui  v0,0xffc0           ; 0xFFC00000
801a2ad4:  sw   v0,0(v1)            ; *SFCR = 0xFFC00000
```

and `spi_regist` calls `ComSrlCmd_RDID` **twice** (`801a1b78`, `801a1b94`) at
`device_initcall`.

Decoding with the vendor's own macro `SFCR_SPI_CLK_DIV((ui-2)/2)`:

| | `SFCR` | field | divisor |
|---|---|---:|---:|
| loader prompt, 量 `REG-13` 2026-08-25b | `3FC00000` | 1 | **4** |
| Linux, 讀 from the r54 artefact | `FFC00000` | 7 | **16** |

**Census control, v2** (v1 had two defects, both kept in §7): pairing
`lui …,0xb800` with `ori …,0x120N` and tracking the register until it is
stored through — **`SFCR` has exactly one writing function in the whole image,
`ComSrlCmd_RDID`**; `lui …,0x3fc0` appears **0** times anywhere.

🟢 **And one inference of mine was refuted by the artefact within minutes of
being formed.** Seeing `setFSCR(chip, 40, 1, 1, 15)` in `spi_regist`'s source,
I concluded the kernel reprograms the divider there. It does not: `setFSCR`'s
entire body is inside `#ifndef SPI_KERNEL`, and in the built image the function
is six instructions that store their arguments to the stack and return. The
source explains it and the artefact settled it, in that order — which is the
wrong order and worked anyway.

### 3.1 🟢 And the same route gives `SFCSR` an exact prediction too

`spi_regist`'s last act is `pfRead(chip, 0x00, 4, buf)`; that is
`SpiRead_11110B` → `ComSrlCmd_ComRead`, whose final instruction pair is
`jal SFCSR_CS_H` at `801a35fc` with `a1` and `a2` both zeroed. `SFCSR_CS_H`
builds its word from `lui 0xc800` — `SPI_CSB(3) | SPI_RDY(1)` — or'd with
`ucLen << 28` and `ucIOWidth << 25`, both zero here.

**So the last write to `SFCSR` before `rtl819x_spi_init` reads it is
`0xC8000000`**, and `REG-13` measured `D8050000` at the loader prompt
(`LEN` = 01, `CMD_BYTE` = `0x05`, the `RDSR` the loader left configured).
`S3` is therefore a second 讀 → 量 in the same mark set, derived the same
way and falsifiable the same way. ⚠️ It assumes nothing reads flash
between `device_initcall` and `late_initcall`; if `S3` comes back as something
else, that assumption is what it refutes.

⚠️ **This is 讀, not 量.** The live value under Linux has never been read on
the device. The driver's `S1` mark is what makes it 量 — or refutes it.

🟢 **It is the same shape as the timer's first cell**, and that is why it was
looked for: `R5-3b-1` found `CDBR` dividing by 1000 and `TC0DATA` reloading at
2,000 under Linux where the loader left 14 and 142,858. **The loader's register
state is not the kernel's register state**, twice now, in two unrelated
peripherals. The general rule this project should carry: *a register value
measured at the `<RealTek>` prompt is a measurement of the loader, and a driver
that assumes it is also the kernel's is assuming.*

### 3.1 🟢 2026-09-08, seating 16: this section stops being 讀 and becomes 量

The paragraph above ended with a ⚠️ saying the live value under Linux had never
been read on the device. That stopped being true at 00:07. Ten boots, ten reads
of `/proc/rtl819x-spi`, and ten boot captures carrying the same values as marks:

```
sfcr   FFC00000     RLXFW-S1=FFC00000     against REG-13's loader-prompt 3FC00000
sfcr2  0BA08000     RLXFW-S2=0BA08000
sfcsr  C8000000     RLXFW-S3=C8000000     against D8050000
```

🔴 **Both of the card's declared coin-flips landed on the side read out of the
vendor's *compiled* driver, against a value this project had already measured on
this very device at the loader prompt.** That is the section's own thesis
arriving as a result rather than as an argument.

🟢 **Three things corroborate it without being asked.** The driver's own
classification reads `sfcr_as_loader 0` / `sfcr_as_kernel 1` — arithmetic done
in the kernel, not a comparison of mine. The boot snapshots `boot_sfcr`,
`boot_sfcr2` and `boot_sfcsr` equal the live values, so nothing moved the
controller between `late_initcall` and the read. And `n_state_foreign` read **0**
across **4,115** transfers, so nothing moved it between my transactions either —
which is the coexistence question §4 owns, answered in the affirmative for this
seating.

⚠️ **What is still not established** is the divisor's *effect*. `FFC00000` is
`SFCR_SPI_CLK_DIV` = 16 by the vendor's own macro, and `REG-38` says the window
leg should therefore be about 4× slower than `probe3`'s bare-metal Group F
figure — but no cell timed the window leg separately, and `C1-SZ`'s sidecar
cannot separate *data arrived* from *the tool began waiting* (`FW-35`). The
divisor is 量; what it costs is still 推.

---

## 4. Coexistence: the decision, and what was rejected

`CONFIG_RTL819X_SPI_FLASH=y` in the baseline (量, line 37), so the vendor's PIO
driver is in this image, drives the same four registers, has `mtd->write` and
`mtd->erase`, and holds **no lock** on any of it.

**Chosen: coexist read-only, explicit verbs, save/restore/read-back.**

**Rejected — a shared lock added to the vendor tree via `config/host-compat/`.**
It would have to be taken by every one of the ~20 entry points in
`spi_common.c` to mean anything, and a partially-applied lock *reads* like
serialisation while leaving holes; a spinlock held across a multi-second flash
read is pathological, and a mutex requires proving no vendor path is atomic —
a bigger reading job than the risk it removes. It would also make that patch a
second owner of "which of my files are linked".

**Rejected for now — a sole-owner variant with `CONFIG_RTL819X_SPI_FLASH=n`.**
It deletes the vendor's MTD entirely, and with it `/dev/mtd0ro`,
`/dev/mtdblock1` and `ROOT_DEV`, which `FW-29`, `FW-30` and `FW-34` all stand
on. **It is written down as the isolation experiment to run *if*
`n_state_foreign` or `n_state_bad` ever moves**, not as something skipped.

### 4.1 What makes the choice survivable, and the part that is an instrument

1. Nothing happens on its own. Registration reads three registers and stops.
2. 讀: the vendor's own entry points re-establish the controller on every call —
   `SFCSR_CS_L` spins for `RDY` then writes `SFCSR` whole; `ComSrlCmd_RDID`
   rewrites `SFCR`. A vendor transaction after one of mine does not inherit my
   state.
3. Mine restores `SFCR`, `SFCR2`, `SFCSR` and **reads them back**.
4. 🔴 `n_state_foreign` counts transactions that *began* with `SFCR`/`SFCR2`
   different from the values latched at registration; `n_state_bad` counts
   restores that did not take. **A zero in either is a reading only because the
   `wedge` verb is the positive control that makes them able to move.**

🔴 **`SFDR` is never restored, and that is the subtle one.** It is the command
port: writing it *issues* an SPI command. A generic "save and restore all four
registers" loop — which is what one writes without thinking — would end every
transaction by clocking a stale byte out to the flash chip. Three are saved.
Four would be a bug that looks like tidiness.

---

## 5. The three write-refusal layers, and the draft that was wrong about one

| | what it is | how it fails |
|---|---|---|
| **L1** | the write path is a separate TU that is not compiled | link-time absence, checked by `rlxfw-marks.py`'s new `absent:` witness |
| **L2** | `mtd->write` / `mtd->erase` are stubs that return `-EOPNOTSUPP` and count | an errno from this driver |
| **L3** | `mtd->flags = MTD_CAP_ROM` — no `MTD_WRITEABLE` | an errno from the MTD core at `open()` |

🔴 **L2 was originally "leave the pointers NULL, the core returns
`-EOPNOTSUPP`". That is false on this kernel.** 讀 `drivers/mtd/mtdchar.c`:

```
case MEMERASE:                                        :419
    if (!(file->f_mode & FMODE_WRITE)) return -EPERM;  :423
    …
    ret = mtd->erase(mtd, erase);                      :457
```

No NULL check. A NULL `.erase` is a null-pointer call, not a refusal — so the
three layers were **not independent**: L3 was the only thing between a NULL and
a dereference, and "defence in depth" would have described a single point of
failure. With refusing stubs they are independent and fail differently.

🟢 **L3's own basis is measured, and it is stronger here than for the vendor's
partitions.** `mtd_open` refuses an open for writing twice, on separate
grounds: `:73` for an odd minor, and `:94` for `!(mtd->flags & MTD_WRITEABLE)`.
The vendor's `/dev/mtd0` is an **even** minor and passes `:73`; this device
fails `:94` on either minor. `mtdblock.c:421` reads the same flag and marks the
block device read-only.

### 5.2 🔴 `D4` works only because those two symbols are GLOBAL, and that is not a detail

量, on the shipped `System.map`: several of this driver's own `static`
functions are **not in it at all** — `rtl819x_spi_verify`,
`rtl819x_spi_read_mmio`, `rtl819x_spi_release`, `rtl819x_spi_kat` and every
`verb` — because the compiler inlined them. Only
`rtl819x_spi_init`, `rtl819x_spi_read_pio` and the three `mtd_info` ops
survive as symbols, and those survive because their addresses are taken.

🔴 **So a symbol-absence proof over a `static` function proves nothing.**
Absent and inlined are the same reading. If `rtl819x_spi_write_page` and
`rtl819x_spi_erase_sector` had been `static`, `D4` would be a check that
passes whether or not the TU is built.

🟢 They are `EXPORT_SYMBOL`'d globals instead, so the linker must emit
them and `nm` must show them as `T`. The control build confirms it reads
that way: `801a8a20 T rtl819x_spi_write_page`, capital `T`. **The
`EXPORT_SYMBOL` is load-bearing and is not there for a consumer** — nothing
imports these — which is exactly the kind of line a later cleanup removes as
dead weight, so it is written down here rather than left to look tidy.

### 5.1 🔴 What `D4` proves, said plainly, and what it does not

`D4` proves that **rlxfw contributes no flash-write code to this image**.

It does **not** prove that this image cannot write flash. 量: the vendor's
write path is here and always has been — `mtd_spi_write` / `mtd_spi_erase`
installed unconditionally, reaching `ComSrlCmd_ComWriteData`,
`PageWrite_111002` and `ComSrlCmd_SE`. What keeps those from being reached is
the userspace surface (`/dev/mtd0ro`'s odd minor; `/dev/mtdblock1` declared
`0400`), which is an access control on a path that exists.

⚠️ And `D4`'s control is a control **over stubs**: the write TU's two entry
points return `-EPERM` and contain no SPI transaction, deliberately, because
mainline is zero-write through `R9` and a working page-program in this tree
would be one make-level override from being aimed. Both sentences are true and
only the pair is honest.

---

## 6. The experiment, and its refutation conditions written first

One traversal, 4 KiB chunks, two buffers. Per chunk: PIO read → `bufA`; MMIO
read → `bufB`; compare; hash.

| | claim | refuted by |
|---|---|---|
| `D1` | `sha256` over `[0,0x6000) ∪ [0x8000,0x400000)` = **4,186,112 bytes** equals `a9916fd8…4ce3cba` | any other digest, with `digest_bytes = 4186112` and `h601_hashed = 0` |
| `D3` | the PIO and MMIO reads agree over **all 4,194,304 bytes** | `cmp_first_diff ≥ 0` |
| — | the PIO path is a real SPI transaction and not a `map` over the window | `D3` cannot refute this; §1 and the source do. If it were a map, `D3` would be one path agreeing with itself and **must be deleted rather than quoted** |
| neg | `corrupt <off>` flips one byte of `bufA` after the read | **`D1` must differ AND `D3` must report exactly `<off>`.** If either does not move, `equal`/`match` are what a tool that cannot fail prints |
| ctl | `wedge` forces the read-back comparison to fail | the transaction must return `-EIO`, `n_state_bad` must move by 1, `wedged` must latch, and the **next** transaction must also return `-EIO` |
| ctl | `S4` = 0 | the three FIPS 180-2 vectors passed on this die. Non-zero and every verb refuses with `-EPERM` |

**The H601 guard is a property of the computed value.** The traversal counts
`h601_hashed` — bytes inside `[0x006000,0x008000)` that reached either digest —
and `/proc` prints the digests **only when that count is 0**. So the digest is
printable because the arithmetic came out H601-free, not because the skip was
believed correct. `H601` is exactly two 4 KiB chunks, aligned, so no
partial-chunk arithmetic exists to get wrong; the redundant in-chunk check is
dead today and fires the moment `RTL819X_SPI_CHUNK` or the bounds change.

⚠️ `H601`'s bytes **do** enter DRAM — `D3` compares them. That is what the
`FLR` bracket already does and it is not a capture. What keeps it safe is that
this driver has **no verb and no field that emits a flash byte**: only digests
over the complement, an offset, counters, and controller registers. Adding a
hexdump verb would defeat every paragraph above.

### 6.1 The digest constant, re-derived rather than requoted

量 2026-09-07 on `flash-n150rt-console-2.bin`, two independent routes —
`dd` + `sha256sum`, and Python byte slices — **agreeing digit for digit**, with
two negative controls that both fired: the whole-file digest differs, and
flipping one byte moves it. Elided form `a9916fd8…4ce3cba`, matching `FLS-24`
on both ends. Emitted as the C initialiser by the derivation script and pasted
whole, so the constant in the driver was typed by nobody.

### 6.2 Why the escalation is 4 KiB → 64 KiB → 4 MiB

量: `bsp_timer_init` writes `WDTCNR = 0x00600000` and `rlx_timer_interrupt`
does `WDTCNR |= 1<<23` on every TC0 interrupt — **the watchdog is armed and
petted from the vendor's TC0 handler**, which `R5-3b-2` did **not** displace
(the tick moved to my clockevent; TC0's interrupt kept firing, measured as line
13 advancing 3,009 in 30.10 s). `CLK-08` puts the window near a second.

So a ~6 s traversal is safe **only** in process context with interrupts
enabled and `cond_resched()` per chunk, which is why the driver uses a mutex
and not a spinlock. The verb takes a byte budget so the first transaction of a
seating is four bytes and not four megabytes.

🟢 **And it exposes a `driver-diff` row worth having**: the vendor's
`SFCSR_CS_L`, `SFCSR_CS_H`, `spiFlashReady` and `ComSrlCmd_RDID` all spin on a
hardware bit with an unconditional back-branch and **no counter** (`j 801a29ac`,
讀 from the artefact). On a board with a ~1 s watchdog, a controller that never
raises `RDY` reboots the router. Mine returns `-ETIMEDOUT` and counts.

---

## 7. Two defects in this session's own instruments, both caught by a case whose answer was already known

1. **The register census v1 had a false positive**: it matched `ori …,0x1200`
   without requiring the `lui …,0xb800` that makes it an address, so
   `bvec_alloc_bs` and `mempool_alloc` appeared as SPI-register users. They are
   GFP-flag constants; v2 requires the pair and drops both.
2. **And a false negative, which is the worse kind**: v1's "followed within 4
   instructions by `sw`" window was too short, so it reported **`SFCSR` as
   read-only everywhere** — including in `SFCSR_CS_L`, a function whose full
   disassembly was already on screen ending `sw v0,0(a0)` on `0xb8001208`.
   *A tool reporting 0 is making a claim*, and this one made a false one about
   the register the whole driver turns on.

⚠️ **And `/tmp/r55dis.txt` was wiped mid-session**, which is `CLAUDE.md`'s
documented `systemd-tmpfiles` trap firing on a session that had read the rule.
Working files moved to `$FWRE_WORK/rebuild/_scratch-r55/`.

🟢 **A third was caught by an enforcer rather than by me.** The first draft gave
`MK4` and `MK5` the same anchor, and `rlxfw-marks.py apply` refused before the
build: *"two rows at one point means the order is an accident"*. It is right —
two Kbuild lines at one anchor land in whatever order the table is read in.
`MK5` now anchors on `MK4`'s inserted line, which makes the dependency
explicit.

---

## 8. What this step does not establish

1. **That the flash content matches the dump.** `D1` says the complement hashes
   to what the 2026-08-16 dump hashes to. It says nothing about `H601`, by
   construction. **The flash bracket does not move: 1,024 / 4,194,304 =
   0.0244 %.**
2. **Anything about writing.** L1 means that code is not here, and the write TU
   is stubs.
3. **That the transaction is optimal.** It is the vendor's order at Fast Read
   with one dummy byte. `spi_common.c` has faster shapes (dual IO, `0x3B`,
   `0xBB`); none has been measured on this die, so none is used.
4. **The SPI clock under Linux.** §3 is 讀. `S1` is what would make it 量.
5. **`mtd_index`.** The prediction is **2**, from a two-partition vendor table
   and a `late_initcall`. It is a prediction, not a reading.
6. **That any of this runs.** Not one line of this driver has executed on the
   silicon. That is the bench half.
7. **That it serves an unaligned read.** `.read` returns `-EINVAL` unless both
   offset and length are 4-aligned, and that is a decision rather than an
   oversight. The controller's data phase is word-shaped; the vendor handles
   the tail with `i = uiLen % 4` and a partial `memcpy`, and copying that
   would put **untested code on a path nothing in this image exercises** —
   `mtdchar` reads in `MAX_KMALLOC_SIZE` blocks, `busybox wc -c` reads in
   powers of two, and this unit has no `dd` (`FW-42`), so every real read is
   aligned. An honest refusal beats a plausible partial-word path that has
   never run. ⚠️ It is the first thing to add if a consumer ever needs
   it, and the refusal is what will say so rather than a wrong byte.
8. **That the vendor's driver and mine agree.** They have never run against
   each other. `n_state_foreign` is the instrument that would notice, and it
   has never been read on the die.

---

## 9. 🆕 2026-09-08 (forty-fourth segment, desk, no power): 1.1, and the
   shape of the answer is decided by one page of `read_proc`

`FLS-26` left 4,153,344 bytes -- **99.02 %** -- undetermined, because a prefix
digest finds the first difference and nothing past it.  1.1 is the instrument
for the rest.  **No card is frozen and no image is staged for a seating**: the
scope decision this segment made is that these verbs ride on `R5-6`'s image,
because `RECIPE_ID` is a digest over `config/` and anything built today goes
stale the moment `R5-6`'s first `.c` lands.
🔄 **2026-09-08: it landed, and the id is `b417a3e7`** -- cell `r56c`,
`vmlinux` 4,049,497 bytes, carrying 1.1 and `rtl819x-wdt` together, which is
what the scope decision above was for.  ~~⚠️ Still no seating and still no card,
so 1.1's verbs remain unrun.~~

🟢 **2026-09-08 evening (seating 17): `map` ran on silicon, twice, and the
99.02 % above is now 2.93 %.**  `flashmap compare` against the desk prediction:
**31 same, 1 DIFFER, 0 scope, 0 extra, 0 missing.**  The one group that differs
is **group 0** (`0x000000`-`0x01FFFF`), which is exactly where seating 16's
bisection had put the first difference (`[0x9000,0xA000)`) -- so two instruments
sharing no code agree on where it is.

**31 x 131,072 = 4,063,232 bytes are now proven byte-identical to the
2026-08-16 dump.**  What remains undetermined is inside group 0's 122,880
hashed bytes plus `H601`'s 8,192, which are skipped by rule (`map_h601_hashed
0`, and `flashmap`'s `F6` refuses every reading if that is ever non-zero).

Every field hit its desk prediction: `map_ran 1`, `map_rc 0`, `map_level 0`,
`map_unit 131072`, `map_entries 32`, `map_hashed 4186112`,
`map_h601_skipped 8192`, `map_diff_units 0`, `map_truncated 0`,
`map_lines 32` -- and all 32 digest lines matched, including the internal shape
no digest value can fake: **group 0 hashes 122,880 rather than 131,072**, and
the **last five groups share one digest** because the dump's 737,280-byte
`0xFF` run from `0x34C000` covers them whole.

⚠️ **A level-0 map cannot say whether group 0 holds one difference or
several.**  That needs `map 1 0`, which did not run.  🔴 `map_truncated`'s
positive control still does not exist (§ 9.1's hazard) -- it read 0 both times,
which is correct and is not evidence the flag works.

🟢 **And the traversal answered a question about the WATCHDOG for free.**  The
card ran `map 0` disarmed, then re-armed and ran the identical traversal again:
`map_jiffies` **1280** both times, digests byte-identical, and across the armed
run `Delta n_hw_kick` **485** against 485.7 predicted from the kick period.  So
the kernel timer wheel ran at exactly its programmed rate through a 12.8 s
in-kernel SPI traversal under a live hardware deadline -- which is much stronger
than *the board survived*, and it retires the load-bearing ordering assumption
`PROGRESS.md` `MAP-1` had carried.

### 9.1 🔴 A per-4-KiB list does not fit, and that is a hard limit

`rtl819x_spi_read_proc` is a 2.6.30 `read_proc_t`.  It `sprintf`s into **one
page** -- `PAGE_SIZE` = 4096 -- and sets `*eof`.  There is no bounds check
anywhere in that interface.  The existing dump is 903 bytes, so it has never
been near the edge; 1,024 lines of 80 characters is **78 KiB**, and a driver
that wrote it would corrupt whatever follows the page, on a board with no
spare.

⚠️ **That is also a latent hazard in the file as it stands**: the dump grows
by a few fields every driver revision and nothing checks it against
`PAGE_SIZE`.  1.1 does not fix that for the existing file -- it adds nine
fields, taking it to roughly 1,050 bytes -- and the new file is where the
budget is enforced.  Recorded rather than quietly relied on.

### 9.2 The map: two levels of 32, and why that is the whole design

`32 x 32 = 1024` exactly.

```
map 0        32 digests, one per 128 KiB group   -> which group differs
map 1 <g>    32 digests, one per 4 KiB chunk     -> which sector
```

Two commands answer the whole 4 MiB when one group differs, three when two do.
🟢 **And every one of those lines can be written into a card before the board
is powered**, because `tools/flashmap.py` computes all 32 group digests, and
all 32 chunk digests of any group, from the dump at the desk.

🔴 **That is the property `verify <n> <offset>` alone does not have.**  A
bisection's rungs each depend on the previous rung's answer, so they cannot be
carded -- which is exactly why seating 16's nineteen `BIS-*` rungs were
off-card, and why `check-predictions` read `32 of 32` while nineteen readings
that mattered more than most of the thirty-two were outside the fence.  The
offset form is still added, and it is the primitive the map is built on; it is
not the thing that closes `FLS-26`.

### 9.3 What each line carries, and the one column that is not a digest

```
OOOOOO E BBBBBB <64 hex>          80 characters, fixed
006000 1      0 SKIPPED           23 characters
```

* `OOOOOO` the offset.
* `E` **PIO == MMIO for this entry** -- `D3`, localised.  `verify` reports one
  verdict for the whole traversal; the map reports one per entry, so a
  controller fault is attributable to a range instead of to the run.  A
  verdict reveals no content, so this column covers `H601` exactly as
  `verify`'s does.
* `BBBBBB` the bytes that reached the digest.  **This is the scope, and the
  desk compares it BEFORE the digest** -- `notes/flash-digest-scope.md` § 8.2
  is why: comparing two digests over different byte counts prints a confident
  `DIFFER` that means nothing, and nine of seating 16's finer rungs came back
  `SCOPE?` for that reason.
* the digest, or `SKIPPED` for an entry that hashed nothing.

⚠️ 80 characters is the terminal width, and that is safe here **measured
rather than assumed**: `FW-49` (量 2026-09-08, over 762 committed captures)
separates the two sources of `\r\r\n` and finds that only the *echo* of a
typed line is wrapped -- by busybox ash's line editor, 33 times, always with
`len(sent) >= 80` -- while output is not, an 88-character `/proc/version` line
arriving whole in five captures from five seatings.

### 9.4 The `H601` guard, and it is the same one twice

The map skips chunks 6 and 7 by the same arithmetic `verify` uses, counts
`map_h601_skipped`, and asserts `map_h601_hashed == 0` -- **the digests print
only because that count came out 0**, not because the skip was believed to be
right.  The desk side does not restate the rule: `tools/flashmap.py`
**imports** `flashwin.overlaps_forbidden` and puts every range that is about
to reach a digest through it, so a divergence between the two is a refusal on
both sides rather than a silent disagreement.  `F8` is the control that says
the import is load-bearing.

⚠️ **The residual is stated rather than left to be noticed**: a per-4-KiB
digest is a stronger oracle than the aggregate one already committed --
someone **holding the 2026-08-16 dump** could brute-force a small change
inside a sector from its digest.  That is the owner of the device.  The dump
is not committed and cannot be (`CLAUDE.md`'s Never table), so for everyone
else these digests are a preimage problem over 4 KiB.

### 9.5 🟢 The traversal is timed in the kernel, and that closes `FW-48`'s
    objection rather than arguing with it

`CORRECTIONS-block13.md` § 5 named the experiment: *"the driver can timestamp
its own traversal against the 100 Hz clockevent and take serial timing out of
the path entirely"*.  1.1 does it -- `v_jiffies`, `map_jiffies`, and `hz`
beside them so nothing downstream carries a constant -- and `R5-3b-2` is what
makes it worth doing, because the tick is this project's own clockevent.

`t0` is taken **before any `goto out` can be reached**, so a run that bailed
still says how long it had been going instead of printing an uninitialised
number that looks like a measurement.

### 9.6 量: it builds, and the code is in the image

Cell `spi11`, a compile check and **not** an image for a seating.

| | |
|---|---|
| `RECIPE_ID` | `fce0af22` -> **`7b6bfa83`** (the source edits moved it, as `config/` is what the digest covers -- three times, see below) |
| `vmlinux` | 4,013,779 -> **4,047,318** bytes, **+33,539** |
| `rtl819x-spi.o` | text **10,768** / data **420** / bss **1,536** = 12,724 |
| new symbols in `System.map` | 16, including `rtl819x_spi_map_read_proc` at `801a818c` |
| `rtl819x-spi 1.1` in `vmlinux` | **1** occurrence |
| `rtl819x-spi 1.0` in `vmlinux` | **0** -- the negative half of the same control |
| compiler diagnostics on this file | none |

⚠️ The bss growth is `map_d[32][32]` plus the four per-entry arrays: 1,024 +
128 + 128 + 32 = 1,312 bytes of the 1,536.

🔴 **And the segment produced lifecycle rule 4's mechanism on new material,
by tripping over it.** The first compile check read `RECIPE_ID` **`44c38c7a`**
and `vmlinux` sha256-16 `d2d157595ec31803`.  A **comment** in this file was
then corrected -- § 9.3's line width, which said 75 and is 80 -- and the
second build read **`9155dad0`** with `5e40cf36e56232ca`.  A third, after § 9.7's two review defects were fixed, reads **`7b6bfa83`** with `57f1dc0110b2c294` -- and `vmlinux` is **4,047,318 bytes all three times**, while `rtl819x-spi.o`'s text moved 10,764 -> 10,768 on the third.  ⚠️ A four-byte object growth that leaves the image size unchanged is section padding absorbing it, and it is the reason the image SIZE is the weakest of the three numbers here.

* `RECIPE_ID` moved, because it is a digest over **every file under
  `config/`, comments included**.
* `vmlinux` is **4,047,318 bytes both times** -- byte-for-byte the same size.
* Its digest moved, which is the `-DRLXFW_SRC_ID=0x<recipe>` that the build
  compiles in.  `notes/incremental-build.md` measured that effect at 4 bytes
  of 3,968,240 on a same-width id, and both of these are 8 hex digits.

⚠️ **A number that was published and then went stale is exactly what rule 4
is about**, and it went stale here inside one segment from a comment.  Both
values are kept rather than the first being quietly overwritten.

⚠️ **The cost of catching it this way is rule 2's, in miniature**: the second
build reused the cell name `spi11`, so the first build's `vmlinux`,
`System.map` and manifest are gone and the two images can no longer be
diffed.  Nothing evidential was lost -- `spi11` is a compile check and not an
image any card names -- but it is the same shape as seating 14's `r53b2`.

### 9.6a 🔴 The next card's boot-capture prediction moves, and by exactly 10 bytes

Every card in this project predicts the byte count of its boot capture, and
seating 16's ten were **1,318 against a prediction of 1,318**.  1.1 adds one
mark, `rlxfw_mark("S8")` after `create_proc_entry` for the map file.

`rlxfw-mark.h:45`: `rlxfw_mark(tag)` is `rlxfw_puts("RLXFW-" tag "\n")`, and
`rlxfw_puts` writes `\r` before `\n`, so a plain mark costs
`6 + len(tag) + 2` bytes.  The existing budget re-derives from that exactly:
`S0` 10 + `S1`..`S6` at 19 each (`RLXFW-Sn=XXXXXXXX\r\n`) + `S7` 10 = **134**,
which is the number `LOG.md` recorded for seating 16.

So this driver's contribution goes **134 -> 144** and the boot capture goes
**1,318 -> 1,328**, before whatever `R5-6` adds on top.

🔄 **2026-09-08 (`R5-6`, forty-fifth segment): "whatever `R5-6` adds" is now a
number.** `rtl819x-wdt` emits six boot marks -- `W0` bare (10), `W1`..`W4` as
`markx` (19 each) and `W5` bare (10) -- so **96** bytes, by the same
arithmetic this section derives.  The card's prediction is therefore
**1,318 + 10 + 96 = 1,424**, of which **106 bytes have never been measured**:
neither 1.1's `S8` nor any of the wdt marks has reached a console.  ⚠️ `W5`
appears twice in the image because `RLXFW-W5-NOPROC` shares its prefix; only
one of the two can print, and the failure-path one costs 17.

⚠️ `S8-NOMAP` is on the failure path and costs 16 if it ever fires; the three
`markx` verbs `S-MRC`/`S-MDIFF`/`S-MH601` fire only when `map` is typed and are
not in the boot budget at all.

### 9.7 What 1.1 does not establish

* **Nothing has run on the silicon.**  Every number in § 9.6 is a build
  number.  The map's first reading is `R5-6`'s seating.
* The `map` verb's own negative control (`corrupt <off>` moving exactly one
  entry) is written and has been exercised only against the desk predictor's
  synthetic dump (`F4`), never on the device.
* `map_truncated` has no positive control: the budget is 3,584 bytes and the
  largest real output is about 2,600, so nothing has ever made it fire.  A
  case that shrinks the budget would give it one, and it is not written.
