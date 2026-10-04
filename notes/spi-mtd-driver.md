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
(`LEN` = 01, `CMD_BYTE` = `0x05`, ~~the `RDSR` the loader left configured~~ — 🔴 **refuted 2026-09-17: both fields are constants of the LOADER's own `SFCSR_CS_H` composer, `lui 0xc805` plus a `movz` that turns `len` 0 into 1. `0xD8050000` is what that composer writes and says nothing about the last command.** `docs/loader-flash-write.md`, and it strengthens this section rather than weakening it: the LINUX build of the same routine composes from `lui 0xc800` with no `movz`, which is exactly the `C8000000` measured here).
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

🔄 **§ 10 SUPERSEDES THIS SECTION'S ARITHMETIC.** The 99.02 % below became
2.93 % at seating 17 and is **0.195 % (8,192 bytes, exactly `H601`)** after
seating 18's `map 1 0` -- which also found **two** differing units where this
section's closing paragraph could only say *group 0*. Kept as written, because
what it could and could not say is the record of what the instrument was for.

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

---

## 10. 🟢 2026-09-09 (seating 18): `map 1 0` runs, the 2.93 % becomes 0.195 %, and the level-1 answer is TWO not one

§ 9 closed at *"the 99.02 % above is now 2.93 %"*. That 2.93 % is group 0's
122,880 hashed bytes, and it is what `map 1 0` was built to split. It ran.

### 10.1 The reading

`flashmap compare` on `bench/2026-09-09/C1-M1.log`:

```
SKIPPED 006000  H601, by rule, on both sides
SKIPPED 007000  H601, by rule, on both sides
DIFFER  009000  device d41a56347970b0cb... dump c40dc4b895d7da25...
DIFFER  00D000  device 5bbdf6f72d3a1858... dump 7f3953fc07530aac...
30 same, 2 DIFFER, 0 scope, 0 extra, 0 missing
```

🔴 **TWO differing units, not one, and `00D000` had never been seen.** Seating
16's prefix bisection put the *first* difference in `[0x9000,0xA000)` and — as
§ 9 itself says — a prefix digest finds the first difference and nothing past
it. This is the cell that looks past it. The card predicted *exactly one* and
was refuted, which is the prediction doing its job: the alternative was never
checking.

**The ledger, from `map 0`'s 31 identical groups plus these 28 identical units:**

| | seating 16 | seating 17 | seating 18 |
|---|---|---|---|
| proven identical | 28,672 B (0.684 %) | 4,063,232 B (96.9 %) | **4,177,920 B (99.61 %)** |
| proven different | 4,096 B | 4,096 B | **8,192 B (0.195 %)** |
| undetermined | 4,153,344 B (99.02 %) | 122,880 + 8,192 (2.93 % + `H601`) | **8,192 B (0.195 %)** |

⚠️ **The remaining 8,192 is exactly `H601`**, and it is undetermined *by
decision*: `map_h601_skipped 8192` / `map_h601_hashed 0` in every capture, with
`flashmap`'s `F6` refusing every reading if that second field is ever non-zero.

### 10.2 🟢 The attribution bracket, and it closed byte-identical

`map 0` ran twice more — once at 22:45 on 2026-09-08 (seating 17) and once as
**the first command of seating 18**, before anything else could touch the part.
Between them the **vendor firmware ran twice** (~2 and ~4 minutes, two bites
that were not caught) and the board was power-cycled cold.

```
cmp bench/2026-09-08b/C1-M0.log bench/2026-09-09/C1-M0.log   ->  identical
```

**Byte-identical, 3,013 bytes.** So those two vendor-firmware runs wrote nothing
to the 4,186,112 bytes this driver hashes. The ordering is part of the claim,
not a convenience: a `map 0` run after any other cell would prove less.

### 10.3 🟢 `--until` and what the map cell now costs

`console-capture` 1.4's `--until` ends a capture on a pattern, and
`map_lines` is the map's own last field — unique, and not a substring of the
command that produces it.

| | seating 17 | seating 18 |
|---|---|---|
| bytes | 3,013 | **3,013** |
| duration | **120.106 s** (`--seconds 120` elapsed) | **13.684 s** (`--until matched at offset 2997`) |

The traversal's own counter says `map_jiffies 1280` = 12.8 s in both, so the
107 seconds seating 17 spent were the instrument waiting, not the driver
working. `map 1 0` costs **1.343 s**, because level 1 hashes 131,072 bytes
rather than 4,186,112.

### 10.4 ⚠️ What is still open, and it is smaller and sharper

* **What is IN `[0x9000,0xA000)` and `[0xD000,0xE000)`.** `map` gives digests.
  Reading the content needs the driver to emit a hexdump of those two pages,
  which `flashwin` permits because `0x008000+` is outside the forbidden window.
  Two pages, no power cycle, and it is the obvious next cell for this driver.
* **`n_writes` was read on ONE boot, not thirteen.** `OFF-SPI` reports
  `n_writes 0`, `n_write_refused 0`, `n_reg_writes 0`, `n_xfer 0` — but that
  cell is off-card and after the fact. The thirteen carded boots never had the
  counter read; the card's § 6 claimed they would and no cell tested it.
  🔄 2026-09-26: no reading of it could have said more — no committed version of
  this file increments it (§ 11.6, `FW-142`).
* ***Proven identical* still means *digests agree with the 2026-08-16 dump***.
  It cannot see two writes that cancel, and **no `FLR` full re-dump has run**.


---

## 11. 🆕 2026-09-17 (`P1-1`, desk, no power): 1.2 — two verbs, a page budget, and the contract this file was supposed to have

### 11.1 🔴 The blocking question was framed on a sentence that is not in this file

`docs/mfgtest.md` §7 opened `P1-1` with an undetermined question: `MT-FLASH-1`
needs `RDID`, and *"this driver's own contract is that it **never writes
`SFCR`**"*, while the loader's `ComSrlCmd_RDID` does.

量, by grep: **the only `never writes` in `rtl819x-spi.c` is line 110, and its
subject is SFCSR's `CMD_BYTE` field.** There is no such contract about `SFCR`
and there never was. This driver writes `SFCR` on **every** transaction, at
`:619`, inside `release()`.

The true invariant is narrower, stronger, and enforced rather than asserted:

> **`SFCR` is never written with a value of this driver's own choosing.**
> `release()` writes back exactly what `claim()` read at `:583`, then reads it
> back at `:624` and compares at `:634`. `n_state_bad` is what fires if the
> restore did not take, and `wedge` is the positive control that makes that
> counter able to move.

⚠️ Worth stating plainly, because the wrong version is the memorable one: the
false sentence is **simpler**, which is exactly why it propagated into another
document and became a question that blocked a step.

### 11.2 🔴 And the `C-3` excerpt everyone had been reading is a partial view

`docs/loader-flash-write.md:137` says the routine *"sits at `0x804058bc`"* and
then prints a listing that begins at `0x8040591C`. **96 bytes and 24
instructions separate those two addresses, and nothing says the listing is
elided at the front.** The `SFCR` write lives in them.

Re-derived with the recipe `docs/loader-command-semantics.md` already carries
(`stage2.bin`, sha256 `f88869d1…`, which was re-checked and matches):

| | |
|---|---|
| `804058E4` | spin on `SFCSR` bit 27 |
| `80405900` | **`SFCR = 0xFFC00000`** |
| `80405904` | `jal 0x804057AC` — CS_L/CS_H twice, an idle toggle |
| `80405914` | `jal SFCSR_CS_L(chip, 0, 0)` — **the transaction starts here** |
| `80405944` | `SFDR = 0x9F000000` |
| `80405954` | `jal SFCSR_CS_L(chip, n-1, 0)` |
| `8040595C` | `lw SFDR` |
| `80405968` | `jal SFCSR_CS_H(chip, 0, 0)` |

**CS is asserted sixteen instructions after the `SFCR` write**, so that write
is bus setup done at probe time when the divider is unknown — not a step the
opcode needs. And §3.1 above already measured the divider under Linux as
`FFC00000`, the exact word `ComSrlCmd_RDID` writes, so it would be idempotent
here in any case.

🟢 Two further readings fall out. `ComSrlCmd_RDID` takes **two** arguments and
both callers pass `nbytes = 4` (`80405050`, `8040505C`, each `li a1,4`), with
`80405064` taking the top three bytes — which is `REG-21`'s stored `001C7016`.
So `rdid` here reads four bytes and shifts, reusing the one phase width this
controller is 量 to have served 4,115 times.

⚠️ **The `SFCR` write itself is not a new finding** — `notes/kernel-build.md`
§19.7 recorded stage 2 writing it twice (`0x804055F8`, `0x80405900`) on
2026-08-31. What is new is the **order**, and the order is the whole question.

`SPEC.md` `LDR-43`.

### 11.3 The two verbs

`rdid` is a sibling of `read_pio`: `claim` → `cs_low(0)` → `SFDR = 0x9F000000`
→ `cs_low(3)` → `rd(SFDR)` → `release`. It moves `n_xfer` and `n_reg_writes`,
gets its own `n_rdid`, and **must not move `n_pio_bytes`** — that counter means
*flash array bytes*, and `RDID` reads none of them.

🔴 **It emits a class of value this file's alphabet did not contain.** The
header permits *digests over the complement, an offset, counters and controller
registers*; a JEDEC id is none of those. It is admissible because it identifies
the **part** and not this **unit**, and the value is already committed twice
(`FLS-04`, `REG-21`). That widening is declared in the verb's own comment
rather than left for a reviewer to infer.

`h601` parses the hardware-settings block and prints **verdicts only**.
🔴 **It has to justify itself against `map 1 0`, which already emits a
PIO-vs-MMIO equality boolean for both H601 pages** — so a verb that reported
equality again would be a second instrument measuring one thing, and its zero
would mean nothing. What it answers that `map` cannot is whether the bytes
**parse**: a page can be read identically by two paths and still hold a block
whose checksum does not close.

Four corrections to `docs/mfgtest.md` §4 went into it, all 讀 and three of them
changing a parser — `len` is **big-endian** (§4 was silent), the vendor bounds
it **from below only**, `"H6"` is not the only accepted tag, and the body holds
**ten** MACs rather than two. `SPEC.md` `FLS-29`.

⚠️ And the buffer is zeroed before `kfree`: it held this unit's MAC, the page
goes back to the allocator, and `MEM-17` measured this DRAM keeping a previous
power cycle's contents.

### 11.4 🔴 The page budget, and where it does NOT reach

§9.1 gave the *map's* `read_proc` a budget because its output grows with a
loop. The first file's output grows when someone adds a field, which is slower
and just as unbounded — and it had no budget at all, while the header had named
the hazard since 1.1.

量 before the new fields: the widest this handler could already produce is
**1,101 bytes**. The sixteen new fields add at most **340**, and the
self-measuring line after them at most **40**, so `RESERVE` is 380 rounded to
512 against a `BUDGET` of 3,584.

⚠️ **It guards what follows it and nothing above**, and that is stated in the
code rather than left to be found: retro-fitting a check to 48 existing
`sprintf()`s would be a large edit to code that is 量 to fit, and a large edit
to working code is its own risk.

🔴 That arithmetic was got **wrong** on the first pass — *"fourteen fields, 317
bytes"* — and re-derived by script rather than patched, because a field count
and a reserve that are both wrong by the same amount stay self-consistent
forever.

### 11.5 What 1.2 does not establish

* **Nothing here has run on the silicon.** `p11a` builds, the marks verify, and
  `rdid_ran` / `h601_ran` have never been anything but 0. `P1-3` is the first
  reading.
* **`d1_match` still has no positive control**, unchanged from §8.
* **The `rdid` sequence is the loader's order**, not a measured-optimal one —
  the same limit §8 states for the Fast Read.
* **`h601`'s clamp is mine.** The vendor has no upper bound at all, so there is
  no prior art saying `0x1FFA` is the right ceiling; it is the ceiling that
  keeps every access inside the 8 KiB actually read.

### 11.6 🔴 `n_writes` cannot move: no committed version increments it (`FW-142`)

🆕 2026-09-26, desk, found while landing block 46's P14 (`R6b-1`). 讀 `git log --follow`
lists three committed versions of
`config/rlxfw-src/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c`: 1.0 (`eac2070`), 1.1
(`a62342c`) and 1.2 (`46e6df7`, still the text at `873a471`). In each,
`rtl819x_spi_n_writes` is named on exactly four lines — its `static` declaration (1.0 `:428`,
1.1 `:474`, 1.2 `:526`), the `/proc` print (`:1021`, `:1268`, `:1348`) and two reads in
`trywrite` (`:1165`/`:1178`, `:1529`/`:1542`, `:1991`/`:2004`) — and on none is it
incremented, assigned or passed by address; no `##` token-pasting occurs in any version.
The control: the same pattern finds `rtl819x_spi_n_write_refused++` twice in 1.2 (`:1248`,
`:1255`). 1.2's own comment says so (`:1693`–`:1694`: no code path in this translation unit
increments it). It could not: in all three versions `.write` and `.erase` are stubs that
return `-EOPNOTSUPP` and `.flags` is `MTD_CAP_ROM` (1.2 `:1268`, `:1275`, `:1276`), so the
counter names a path the driver does not have.

**So `n_writes 0` carries no information about writes**, on any image built from a committed
version: every "rlxfw's `n_writes` read 0" in this repository — `FLS-26`'s "`n_writes` read 0
in every dump", `FLS-27`'s positive control, P14's conjunct on block 46's card, the
`MT-FLASH-2` check — says the counter was printed, not that nothing was written. What stands
behind *rlxfw's driver wrote nothing* is the refusing stubs (讀) and the map bracket (量); what
stands behind *nothing was written* at a press is the commands issued and the bracket's reach,
each with its stated blind spots. 推 That each image was compiled from its committed text:
the images are pinned by digest, not by source.

Not established: that a future version with a write path will count its writes — the counter
needs an increment site and a positive control that moves it before its 0 means anything.
`CLAUDE.md` § Flash names the counter as part of a seating's claim; that rule is the owner's
to change, and it is not changed here.

## 12. 🆕 2026-10-04 (`R8b` item 4, 122nd segment, desk, no power): the write path exists and is in no image

`R8b`'s precondition ④ read *there is no write path at all* (`docs/GATE-RESULTS.md`
entry 16). Three layers refused: the write translation unit was declared behind a
kconfig symbol nothing declared, `mtd->write`/`mtd->erase` were refusing stubs,
and `mtd->flags` was `MTD_CAP_ROM`. This section is the four decisions that
change that, each with its alternative rejected and its refutation condition, and
the closing statement that matters more than any of them: **not one line of what
follows has run anywhere.**

### 12.1 The three layers, re-measured rather than quoted

Checked against the tree that **builds** — cell `r95q2`, staged and built
2026-10-04 15:27, which carries rlxfw's sources, the vendor's, and the objects
the compiler produced.

| layer | reading |
|---|---|
| **L1** | 讀 the staged `drivers/mtd/devices/Makefile:19-20` carries `obj-y += rtl819x-spi.o` then `obj-$(CONFIG_MTD_RTL819X_WRITE) += rtl819x-spi-write.o`. 讀 the symbol occurs **0** times in the built `.config` and **0** times in `include/linux/autoconf.h`, against a positive control of `^CONFIG_MTD_CHAR=y` occurring once in the same run; **0** lines declare it in any `Kconfig` of the tree, against a positive control of `config MTD_CHAR` being found. 讀 the artefact: `rtl819x-spi.o` is 29,284 bytes and `rtl819x-spi-write.o` does not exist, while `rtl819x-spi-write.c` **is** staged — so the object's absence is the Kbuild row's doing, not a missing file |
| **L2** | 讀 two `return -EOPNOTSUPP;` sites, each preceded by `rtl819x_spi_n_write_refused++;`, and 讀 that increment occurs at **exactly 2** sites |
| **L3** | 讀 `include/mtd/mtd-abi.h`: `MTD_CAP_ROM` is **0** (`:35`), `MTD_WRITEABLE` is **0x400** (`:29`), `MTD_CAP_NORFLASH` is `MTD_WRITEABLE\|MTD_BIT_WRITEABLE` (`:37`). 讀 `mtdchar.c:73` (odd minor) and `:94` (`!MTD_WRITEABLE`) are two separate refusals; `:419`/`:423`/`:457` call `mtd->erase` with no NULL check; `mtdblock.c:421` reads the same flag. Every line number this driver's own header cites resolves to the line it claims |

### 12.2 🔴 Two things the precondition's wording did not say

**`docs/mfgtest.md` conflates L2 and L3, and has since `P1`.** Its text reads
*"receives `-EOPNOTSUPP` from both **because `.flags = MTD_CAP_ROM`**"*. That
causal clause is false: `trywrite` calls through the function pointers directly,
`mtd->flags` is read only by `mtd_open`, and `mtd_open` is not on that path. The
`-EOPNOTSUPP` is L2's alone and L3 is not consulted at all. The two
`docs/mfgtest.md` lines are corrected in this commit; the same sentence in
`docs/history/steps-P1.md` is a record and stays as it was written.

**`tools/rlxfw-marks.py` structurally forbids the state "conditional Kbuild row,
object present".** 讀 `tools/rlxfw-marks.py:187-192`: a row matching
`OBJ_COND_RE` **must** carry an `absent:` witness, and `str:`/`sym:` there is a
hard refusal with a reason. The rule encodes *conditional ⇒ not in the image*,
which was true while the symbol was undeclared and stops being true the moment
the delta row says `y`. So the moment `MK5`'s object is in an image, `MK5`
cannot be declared in that file as it stands. That is a tool refusal rather than
a documentation gap, and it is the largest consequence of this item: the flip
from `n` to `y` needs either `MK5` converted to an unconditional `obj-y` row
with a `sym:` witness (which retires `D4`'s build-time layer), or the pairing
rule taught to read the delta's value for the symbol. The second keeps the
refusal and makes `rlxfw-marks.py` a second reader of
`config/rlxfw-kernel.delta`; the choice between them is the owner's.

### 12.3 The four decisions

#### `W1` — declare `CONFIG_MTD_RTL819X_WRITE`, `default n`

`config/host-compat/0010` adds one `bool` stanza with `default n` and **no
`depends on`** to `drivers/mtd/devices/Kconfig`; `config/rlxfw-kernel.delta`
gains one row pinning it to `n`.

讀 the stanza needs no `depends on`: the file is `source`d from
`drivers/mtd/Kconfig:321` inside `menu "Self-contained MTD device drivers"`,
whose `depends on MTD!=n` at `:4` already covers every symbol in it. An explicit
`depends on MTD` would be a second owner of a dependency the menu states.

讀 the file is 301 lines, 11,525 bytes, sha256
`0c0688ed1ba1cfc2e1cb29f25021a8195bd664dd5991b32b6ae1bb6880d32333`, and is
**byte-identical in all three Realtek drops** that carry it; `shibajee`'s copy
differs. One source in three copies, the shape `config/rlxfw-kernel.delta`
already records for `mtdchar.c`.

**Alternative rejected:** leave it undeclared, which is *stronger* than `=n`.
Rejected because the only remaining route to the file was
`make CONFIG_MTD_RTL819X_WRITE=y` on the command line in a discarded tree, and
an override like that leaves **no trace in `.config`** — so
`tools/kconfig-delta.py check`, which exists precisely because the copied-in
`.config` and the built one differ on 21 symbols, could not see it. 🔴 This is a
weakening of `D4`'s refusal and is recorded as one.

**Second alternative rejected:** skip kconfig and write `obj-y +=
rtl819x-spi-write.o`. The TU would then be in every rlxfw image, `D4`'s
`absent:` witness would die, and nothing would be left enforcing *a write
needs my explicit yes* at build time at all — the TU would be in every image,
and only the run-time arming would stand between a boot and a page program.

**Refusal path:** `default n` plus the delta row's `n`. **Instruments:**
`kconfig-delta check` and `rlxfw-marks verify`'s `absent:` witness; no counter,
since this is a build-time decision. **Refutation:** an image whose `System.map`
holds `rtl819x_spi_write_page` while the delta says `n`, or the converse; or a
`(NEW)` line naming this symbol in an `oldconfig` log.

#### `W2` — compile the TU: the row's value is `n`

`set CONFIG_MTD_RTL819X_WRITE - n`. The write path ships compiled into nothing.

**Alternative rejected:** ship `y`, so `R8b`'s seating has the image it needs.

🔴 **This reason was re-derived mid-segment, and the first version of it is
retracted.** It read *`R9-11` is outstanding, so `y` would put a live
page-program into every image built before `R9` closes*. 量: `R9` closed at
`fdf86da4`, between this item's read of the tree (`f3263d5a`) and its write-up.
That premise is gone, and the decision is kept on two others:

* `CLAUDE.md` § Never: *a write needs my explicit yes*, which is not conditional
  on `R9`. A compiled write path is not a write, but it is one `echo` away from
  one, and nobody has said yes to that.
* § 12.2's tool refusal is now the binding reason. The flip to `y` makes
  `config/rlxfw-marks.tsv` `MK5` go red and **cannot be re-witnessed** without
  either retiring `D4`'s build-time layer or relaxing
  `tools/rlxfw-marks.py`'s pairing rule. That is a choice about a containment
  check, and `CLAUDE.md` makes it the owner's.

This is still the one decision of the four the owner may want taken the other
way, and it is one field of one row.

**Second alternative rejected:** a fourth `kconfig-delta` variant
(`quiet-write`). Blast radius, enumerated before deciding: 讀 41 rows of
`config/rlxfw-kernel.delta` carry `@quiet,loud` (the `SWCORE=n` block), and a
variant not named in each of them would build `SWCORE=y` — a 41-row retag of
heavily cited lines against a one-row alternative. Worth revisiting if the write
image must coexist with mainline in CI.

**Refusal path:** the row. A `.config` disagreeing with it is refused before
anything compiles. **Counter:** `wr_linked`, printed by `/proc/rtl819x-spi` in
**every** image — `0` mainline, `1` write — so a card discriminates by reading
the device, not by trusting a file name. **Refutation:** `wr_linked 1` on an
image built from a tree whose delta says `n`.

#### `W3` — implement page-program and sector-erase

Three files. `rtl819x-spi-wrpolicy.h` is new and holds every refusal as pure
arithmetic over `u32`, with **no `#include`**, so the kernel TU and
`tools/test-spi-wrpolicy.c` compile the same code — a harness holding its own
copy of the bounds test is the shape where a guard and its test agree with each
other and both are wrong. `rtl819x-spi-write.c` is rewritten from 136 lines of
`-EPERM` stubs to the policy, the per-reason counters, the arming state and the
two MTD-shaped entry points; the names `rtl819x_spi_write_page` and
`rtl819x_spi_erase_sector` and their `EXPORT_SYMBOL`s are kept, because `MK5`'s
witness is a name and a symbol-absence proof over a `static` function proves
nothing. `rtl819x-spi.c` grows 2,204 → 2,655 lines.

**Why the split.** `claim()`/`release()` is the only thing in this project that
saves `SFCR`/`SFCR2`/`SFCSR`, restores them, reads them back and latches
`wedged` when the restore did not take — and deliberately does not restore
`SFDR`, because writing `SFDR` issues a command. A second copy of that guard
would be a second owner of the one invariant that makes this driver survivable
beside the vendor's. So the policy is in the gated TU, where it can be
desk-tested, and the two register-level primitives stay beside the guard under
the same `#ifdef`.

**The sequences are the vendor's**, 讀 from `spi_common.c` in the tree that
builds: erase is `ComSrlCmd_SE` `:819-825` — `WREN` 0x06 (`:129`), `SE` 0x20
(`:138`) with a 3-byte address, then `spiFlashReady()` `:728-742` polling `RDSR`
0x05 bit 0; program is `PageWrite_111002` `:1070-1074` →
`ComSrlCmd_ComWrite` `:964-991` → `ComSrlCmd_InputCommand` `:849-880` — `WREN`,
then `PP` 0x02 with three address bytes and no dummy, then 4-byte `SFDR` phases
and a short tail phase, then the same poll. `docs/blind-write-ledger.md § 9.14`
records every path with its depth, so **this diff is not called blind**.

🟢 **Four things are rlxfw's own, and each has a 讀 of the vendor's opposite:**

1. **The forbidden window** `0x000000–0x007FFF`. 讀 `spi_cmd.c`
   `mtd_spi_erase()` `:46-53`: the `skip 1st block erase` guard is inside
   `#if 0`, so `instr->addr = 0` is accepted and sector 0 is erased. 量
   `docs/loader-flash-write.md` 1: the loader's `burn()` has no lower bound
   either.
2. **Refusing a non-grain-multiple erase length.** 讀 `spi_cmd.c` `:57-60`: the
   length-alignment check is commented out; `:71-78` then round the length
   **up** — `len = len - (len & (mtd->erasesize-1)) + mtd->erasesize;` and
   `if (len < mtd->erasesize) len = mtd->erasesize;`. Asking the vendor's driver
   to erase one byte erases a whole sector, silently, and returns 0. Here that is
   `-EINVAL` and a counter.
3. **Bounded spins.** 讀 `spiFlashReady()` is `while (1)` on the WIP bit with no
   ceiling and no counter; 量 this board arms a watchdog (`CLK-08`), so on the
   vendor's driver a part that never clears WIP reboots the router. Here it is
   `-ETIMEDOUT` and `n_wip_timeout`.
4. **Explicit big-endian word assembly**, where 讀 the vendor's
   `memcpy(&ui, puc, 4)` (`:974-976`) is correct only because this core is
   big-endian.

⚠️ **One vendor oddity deliberately not copied.** 讀 `SeqCmd_Order` `:786-792`
calls `SFCSR_CS_L(ucChip, ucIOWidth, IOWIDTH_SINGLE)` — the io-width in the
length argument and the length in the io-width argument. It is inert only
because `DATA_LENTH1` and `IOWIDTH_SINGLE` are both `0x00`.
`rtl819x_spi_cmd1()` passes a length of 0 on purpose and says so, so a later
reader is not left deciding whether the swap mattered.

**Alternative rejected: the compile switch alone, with no arming.** In the image
`R8b`'s seating needs the switch is already `y` and protects nothing: every boot
would carry a live page-program reachable from `/proc`. So the engine refuses
unless armed by `echo 'arm <lo> <hi> <budget>' > /proc/rtl819x-spi`; all three
fields are required, an omitted one is `-EINVAL` and not a zero; the budget is
debited only on a **successful** operation; and reaching 0 disarms. The arm verb
itself refuses a window overlapping the forbidden region, so that rule lives in
two independent places. 🔴 Arming is **not** a security boundary — root types
the verb and this board's only user is root. It is a containment rule for the
failure this project has: a stray write, a wrong card cell, a payload whose
destination nobody declared. `CLAUDE.md`'s dated `owner-yes` per payload remains
the authorisation.

**Alternative rejected: a second writable `/proc` entry for the write verbs.**
Refused on this driver's own standing argument, which is not relaxed: *a second
writable entry would be a second way to reach the controller.* `arm` and
`disarm` dispatch from `rtl819x_spi_write_proc`, and the TU's fields print from
`rtl819x_spi_read_proc` behind the existing page budget plus a second check
against the TU's own declared maximum, with `wr_truncated` printed either way.

**Nine refusals, nine counters**, printed as `wr_refused_by` in enum order on
one line so adding a reason cannot silently drop it:

| reason | errno | what it refuses |
|---|---|---|
| `FORBIDDEN` | `-EPERM` | any byte of `0x000000–0x007FFF`, **whatever the arming state** |
| `RANGE` | `-EINVAL` | off the end of the chip, or a zero length |
| `UNARMED` | `-EACCES` | no arm in force |
| `OUTSIDE` | `-EPERM` | outside the armed window |
| `BUDGET` | `-ENOSPC` | the arm's byte budget is spent |
| `MISALIGNED` | `-EINVAL` | an erase address not grain-aligned |
| `BADLEN` | `-EINVAL` | an erase length not a grain multiple; a program longer than a page |
| `PAGECROSS` | `-EINVAL` | a program spanning two pages |
| `GEOM` | `-EPROTO` | grain `!=` `mtd->erasesize`, or a grain that is not a sane power of two |

beside `wr_n_prog`, `wr_n_erase`, `wr_n_bytes`, `wr_n_arm_ok` and
`wr_n_engine_fail` — the last being the only counter that can move without a
decision here being wrong.

**The order of the checks is the design.** The forbidden test runs **first** and
reads nothing but the request: not the arming state, not the budget, not the
alignment, not the geometry. No sequence of other decisions reaches past it, and
the host suite drives it **armed** on purpose — *refused while unarmed* would be
a pass that proves nothing.

**Refutation**, at the bench and after the owner's dated yes: a page program
whose read-back does not match the bytes written; an erase that clears a range
other than the one requested, which this driver's own `map 1 <group>` digests at
4 KiB granularity; `n_writes` moving on a refused request; `wr_n_prog` moving
while a refusal counter moves too; or the forbidden window's digest changing
against the 2026-08-16 dump, which would mean the first check did not hold.

#### `W4` — keep `mtd->flags = MTD_CAP_ROM`

Unchanged, and that is a decision rather than an omission.

**Alternative rejected: `MTD_CAP_NORFLASH`.** It buys nothing reachable: 讀
`tools/mkinitramfs.py` refuses to declare an even char minor over this device,
so `mtdchar:73`'s odd-minor rule refuses the open whatever this flag says, and
讀 `config/image-commands.tsv`, there is no `dd` and no `mtd_debug` in this
image. What it would cost is the one static layer that cannot be armed away. So
the write path is reachable only through this driver's own verbs, and `mtdchar`
and `mtdblock` stay outside the trust boundary.

**Second alternative rejected: flip the flag at run time inside `arm`.** 讀
`mtd_open` reads it once, at `open()`, and `mtdblock.c:421` caches it into
`dev->readonly` at add time — so a descriptor opened while armed would stay
writable after the disarm, and whether the refusal held would depend on *when*
the open happened. A guard whose answer depends on timing is not a guard.

**Refusal path:** `MTD_CAP_ROM` is 0, so `mtd_open:94` refuses `-EACCES` before
any stub is consulted. **Counter:** none, and 🔴 **L3 has never been observed
firing, here or anywhere in this project, and `W4` does not change that.**
Observing `:94` needs an even char minor over this device, which `mkinitramfs`
refuses — correctly, since it can check the odd-minor rule from a declaration
and cannot check `mtd->flags`, a run-time property. So L3 is 讀 and stays 讀;
what is instrumented is the layer behind it, by `trywrite`. **Refutation:**
`/dev/mtdblockN` for this device being writable, or `open(O_WRONLY)` on an even
minor of it succeeding.

### 12.4 The erase granularity — one line, and a new second reading

```
config/rlxfw-src/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-wrpolicy.h
#define RLXFW_SPI_WR_ERASE_GRAIN	0x00001000u	/* 未定 FW-187/FW-191 */
```

It occurs exactly once in the header and nowhere else in any file this item adds
or changes. Substituting a settled value means editing that line and setting
`RTL819X_SPI_ERASESIZE` in `rtl819x-spi.c` to the same value in the same commit.

`SPEC.md` `FW-187` 殘留 and `FW-191` 殘留 own the open value and already say the
decisive 量 is an actual erase. Two readings are on hand and **neither is a
reading of the chip**:

* 量 `/proc/mtd` reports `erasesize 00001000` on all three partitions
  (2026-10-04, `bench/2026-10-04/PRE-MTD`, `FW-187`) — but that number is
  `rtl819x-spi.c`'s own constant and the vendor map's partition constants.
* 讀 🆕 **the second source this segment adds.** 量 at the desk 2026-10-04:
  `0x1C7016` — the id `FW-191` measured — appears **nowhere in the GPL drop that
  builds**. The Eon entries in `spi_common.c`'s table are `0x001c3115`,
  `0x001c3116`, `0x001c3015`, `0x001c3016`. So `spi_regist()` takes its
  **UNKNOWN** branch (`:570-574`) and calls `set_flash_info(..., SIZE_064K,
  SIZE_004K, SIZE_256B, "UNKNOWN", ComSrlCmd_SE, ...)`. The code that has driven
  this board since 2018 therefore erases with **SE, opcode 0x20**, calls the
  sector **4,096** bytes, and records a **65,536**-byte `block_size` that its own
  `pfErase` never uses. That is the fallback's constant applied because the part
  was not recognised; it does not settle `FW-187` 殘留. It does answer one half
  of what that row asks — *read out of rlxfw's own source which opcode it
  issues* — and the answer agrees: SE 0x20.

**The guard against the placeholder being wrong is in the code, not in a
comment.** `rlxfw_spi_wr_chk_erase()` refuses every erase with `-EPROTO` while
`RLXFW_SPI_WR_ERASE_GRAIN != mtd->erasesize`, so changing one number and
forgetting the other is loud. And the forbidden test is applied to the
grain-aligned block the erase would **clear**, not to the requested address: at a
64 KiB grain an erase at `0x008000` clears from `0x000000`, and a check on the
address alone would permit the loader's destruction while reading as a guard.
That exact case is in the host suite, and the suite is green at both candidate
grains.

### 12.5 The page bound, 讀 rather than assumed

`RLXFW_SPI_WR_PAGE` is 256. 讀 the vendor's own write path:
`ComSrlCmd_ComWriteSector` (`:1003-1007`) issues `pfPageWrite` exactly
`page_cnt` times with `page_size` bytes each, advancing the address by
`page_size`; `set_flash_info` (`:605-606`) sets `page_size` from the table's
`SIZE_256B` and `page_cnt = sector_size / page_size`; every table entry and the
UNKNOWN fallback pass `SIZE_256B`. And `ComSrlCmd_ComWriteData`'s `calAddr`
(`:659-692`) splits by **sector**, with partial pieces going through
`ComSrlCmd_BufWriteSector`, which read-modify-erase-writes the whole sector. So
the vendor never issues a PP longer than 256 bytes.

⚠️ 推, and the direction is the safe one: that a PP crossing a page boundary
**wraps** to the start of the page is JEDEC's definition of the opcode, and this
part's datasheet is not on hand (`FW-191`: the draft here is the SoC's, not the
flash's). So a crossing request is **refused**, never split silently, and being
wrong about the wrap costs a refused write. The vendor's `ComSrlCmd_ComWrite`
(`:964`) bounds `uiLen` by nothing at all.

### 12.6 🔴 A self-deadlock found by reading, which no run could have found

`mtd->write` and `mtd->erase` must now take `rtl819x_spi_lock`, because in a
write image they issue a transaction. That mutex is not recursive. The existing
`trywrite` verb took the lock and *then* called through the function pointers —
so the first boot of the first write image would have **hung inside the one verb
whose job is to show the refusal works.** 量 is impossible here, because no
committed image links the TU; nothing but reading could find it. `trywrite` now
reads its counters outside the lock, and the assumption that makes that safe is
written down rather than left implicit: there is one writable `/proc` entry and
the shell that writes it is serial.

`trywrite`'s expected errno also had to change, and getting it wrong would have
made the verb **fail on a correct refusal**: both its calls are at offset 0,
which is inside the forbidden window, so in a write image both answer `-EPERM`
(FORBIDDEN, decided before the arming test is reached) and in a mainline image
both answer `-EOPNOTSUPP`. The conjunct now asks that the two **agree with each
other** and with this build's own constant, and `/proc` prints `unarmed_rc` so
no card carries the number.

### 12.7 What § 12 does not establish

**Not one line of the write path has run anywhere.** It is in no committed
image, has never been on this die, and all four decisions are unexercised code
until the seating. The desk statement is: *the path is written and refuses
correctly at the desk; whether it programs a page on this part is unmeasured.*

What the controls do establish, exactly: the policy's nine refusals and twelve
permissions hold **on x86-64, at both candidate grains**; the kernel code
**compiles** with the project's own toolchain and flags in both arms, with the
mainline object holding no engine symbol and the write object holding it; the
kconfig symbol is **declared and settable** while an undeclared one is dropped
by `oldconfig`; and the Kbuild row is what selects the TU. None of that is a
reading of the flash.

**No desk control exists for**: that a page program writes the bytes asked for;
that an erase clears the block asked for and no other; the erase granularity of
this part; that the WIP poll terminates on this part (`RTL819X_SPI_WIP_SPINS` is
推, a guess, with no datasheet for this part); that the claim/release guard
survives a **write** transaction, every reading of it so far being over reads;
and L3 firing, which is unobservable on this image by construction.

**`n_writes` is blind to a vendor-side write.** 量 2026-09-07 and unchanged:
`CONFIG_RTL819X_SPI_FLASH=y`, and 讀 `spi_probe.c:101-103` installs
`mtd->write = mtd_spi_write` and `mtd->erase = mtd_spi_erase` on the vendor's
partitions unconditionally, reaching `PageWrite_111002` / `ComSrlCmd_SE`.
Nothing in rlxfw counts those. What keeps them out of reach is the userspace
surface — an odd char minor and a `0400` block node — which are access controls
on a path that exists. `SPEC.md` `FLS-26` already proved *"not one flash byte is
written"* false for this device. The accurate sentence is: **rlxfw's `n_writes`
counts rlxfw's writes.**

**`FW-142` becomes variant-dependent.** It says no committed `rtl819x-spi`
increments `n_writes`, so its zero carries no information. That stays true of
the three versions it names and of every **mainline** image, where no increment
path is compiled. In a `CONFIG_MTD_RTL819X_WRITE=y` image there is one,
`rtl819x_spi_note_write()`, so the zero starts carrying information there.

### 12.8 Three defects in this segment's own instruments

Kept because the next reader will meet them.

* `-std=c89` has no `inline` keyword and rejected `rtl819x-spi-wrpolicy.h`
  outright. The kernel TU is compiled by gcc 3.4.6 in **gnu89**, so that is the
  dialect the harness uses. The cheapest possible reminder that this header is
  compiled twice.
* `-Wmissing-field-initializers` (from `-Wextra`) caught **two** harness table
  rows one field short, which would have read as `mtd_erasesize = 0` and turned
  two permitting cases into `GEOM` refusals — a suite greener than the code
  deserved.
* The first version of the kconfig control ran `conf -o Kconfig`, and 2.6.30 has
  **no top-level `Kconfig`**: the entry point is `arch/$SRCARCH/Kconfig`, which
  on this drop `source`s `"../target/config.in"` — a path one level **above** the
  kernel directory, into the SDK's own target tree. conf printed *can't find
  file Kconfig*, `|| true` swallowed the status, and both arms then read their
  verdict off a `.config` nothing had regenerated. A false green in a control,
  which is the one failure a control may not have. Its exit code is now read, and
  the third arm — the same `y` against the **unpatched** file, which must be
  dropped — would have caught it anyway.

And one about the diff itself: the Kconfig hunk was written by hand, was
byte-correct on every context line (量, `od -c` against the target's lines
296-300) and arithmetically right, and GNU patch 2.7.6 still refused it with
*Hunk #1 FAILED at 296*, with and without `-l`. `diff -u` places the same
insertion at `-297,5 +297,28`. The hunk is now generated by `diff -u` from a
scratch copy rather than typed, which is the project's own rule about never
rebuilding a tool's output by hand.
