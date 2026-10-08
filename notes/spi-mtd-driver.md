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

#### 🆕 2026-10-04 (123rd segment): the owner chose a third, and the exemption lives in the run's own argv

**Remedy C, and why the exemption is at the call site.** Both remedies above
relax a containment check, which is why the choice was the owner's; a third was
measured and taken instead. The second remedy — teach the pairing rule to read
the symbol's value — was rejected on two grounds: it would make
`tools/rlxfw-marks.py` a second reader of a value `tools/kconfig-delta.py`
already owns, and it would make a row's verdict depend on a file the row does
not name, so a delta edit could turn a containment check green with no diff in
`config/rlxfw-marks.tsv` at all. The first was rejected because it puts the
write translation unit in **every** image for good and retires `D4`'s
build-time layer with it.

Remedy C adds `verify --expect-present ROW-ID`, which **inverts one named
row's `absent:` assertion for one run**. The table keeps saying the TU is not
shipped; `MK5`'s own line and `tools/rlxfw-marks.py`'s parse-time rule are
untouched, and 量 lines 187-192 are byte-identical to `c8980fd6` — which
mattered, because 量 that range is cited from `PROGRESS.md`, from § 12.2 above
and from `MK5`'s own data row, and a shift would have rotted a citation inside
the very row the remedy exists for. The flag names a **row** and never a symbol
or a pattern; it refuses a row that is not a conditional `absent:` row, and it
refuses the same id twice. The "symbol is present" predicate is the one
`sym:` already uses — one owner for one question — and 讀 that predicate is
plain membership of a `System.map`'s third field, with no requirement on the
symbol's type or binding, so an exemption is still satisfied by a local `t`.
That is unchanged on purpose: tightening it is a containment change and the
owner's.

**Refutation conditions, written before the code.** With the flag given and a
`System.map` that does **not** carry the symbol, the row must still go red —
otherwise the flag is `--skip` under another name. With no flag at all, an
armed map must still go red. Both are controls in the tool's own self-test
beside the two green cells, so the four-cell table is the both-ways sweep
`CLAUDE.md` asks of an exemption list; 量 the self-test goes 58 → 71 cases, and
a mutation that makes the flag stop looking turns the first of those two red
while the one-owner identity catches it independently.

⚠️ **What this does not buy, stated rather than found later.** 讀
`tools/rlxfw-kbuild.sh` passes no such flag, and its `gate_verdict` turns a red
`verify` into `exit 6` / `NOT FOR UPLOAD` — so an armed image can be verified
by hand and **still fails the build-path gate**. Closing that is a change to
the build driver, not to this tool. And the tool can now be told the opposite
of what the delta says: only the operator's argv keeps the two consistent,
which is a habit and not a refusal.

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

🔄 **2026-10-05 (124th segment): `W1`'s patch landed without regenerating the
modification record, and nothing was set up to notice.**
`docs/vendor-modifications.md` is generated by `tools/modrecord.py emit`, and
`check` compares it byte for byte with what the declarations derive. 量
2026-10-05, `check` run on each commit's own `tools/`, `config/` and record
(`git archive`; exit codes read in a script, no pipe on the command): green at
`01cff02b` and `57b2cab6` (23 vendor files); **red, rc 1, at `fa36f7a2` — this
item's commit, which added `config/host-compat/0010` and one delta row — and at
the six commits after it, through `8283d033`**; green again at `33cb73a7`,
`a6add876` and `c0349701` (24 vendor files). The first difference is line 12 of
the record: committed 9 patches and 147 delta rows, derived 10 and 148. 讀
`.github/workflows/ci.yml`:
`modrecord` occurs 0 times at `8283d033`, and `33cb73a7` regenerated the record
and added the step *modrecord check (exit-code gate)*. ⚠️ That step runs without
`--tree`, so it checks that the record is what the declarations derive and
**not** that each anchor resolves in a staged tree, which needs the vendor drop
and is not there in CI. `SPEC.md` `FW-233` indexes this.

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
(`quiet-write`). Blast radius, **re-enumerated 2026-10-04 because the first
version of this paragraph priced it with the wrong cost.** 量 41 rows of
`config/rlxfw-kernel.delta`'s 148 carry `@quiet,loud` (the `SWCORE=n` block —
lines 380–420 of 420, contiguous and ending the file), and a variant not named
in each of them would build `SWCORE=y`. 🔄 **But "a retag of heavily cited
lines" is retracted, and it was never true.** 量 every line citation into that
file from a tracked file lands on 2, 82, 83, 89, 90, 138, 139 or 175–178, so the
intersection with those 41 rows — and with the `CONFIG_MTD_RTL819X_WRITE` row at
`:59` — is **empty**; and a retag rewrites field 1 in place, which moves no line
in either direction, so citation movement is not a cost of this route at all.
**The cost that is real is a containment gate.** 讀 `:59` is **untagged**, so it
is a row of every variant, and 讀 `tools/kconfig-delta.py:294-295` drops a row
belonging to other variants **before** reaching the duplicate-symbol guard at
`:308-311` — so an armed variant cannot simply add a `y` row beside it: it has
to come out of the untagged set. Doing so makes `parse_delta(variant=None)` lose
the symbol while `quiet-swcore` keeps it, which turns `E1c` of
`tools/test-config-gates.sh` red — the case that asserts *quiet-swcore reads the
untagged rows alone* (`same=yes`), and one of the owner's 2026-09-28 decisions
rather than an edit to make quietly. So the comparison is one field of one row
against a second owner decision on a gate, not against a renumbering. Worth
revisiting if the write image must coexist with mainline in CI.

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

### 12.4 The erase granularity — one line, and why it stays 未定

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
* 🔄 **This bullet first called itself *the second source this segment adds*,
  and that claim is withdrawn: `SPEC.md` `FLS-23` has owned this reading since
  2026-08-31** — and owns more of it than either this bullet or `FW-209` does,
  namely *29* table rows with no match and the `spi_probe.c:99` →
  `mtdpart.c:471` inheritance that carries `sector_size` into every partition's
  `erasesize`. The reading itself stands and is re-measured here. 量 at the desk
  2026-10-04: `0x1C7016` — the id `FW-191` measured — appears **nowhere in any
  of the three GPL drops**, 0 files each against a positive control of 2 files
  each for `0x001c3016`, and the three drops' `spi_common.c` is one file
  (sha256 `4d5a33e9…`). The Eon entries in that table are `0x001c3115`,
  `0x001c3116`, `0x001c3015`, `0x001c3016`. So `spi_regist()` — `:547-589`,
  with `:546` its comment — takes its **UNKNOWN** branch, whose test is at
  `:565` rather than at the `:570-574` `FW-209` cites for it, and calls
  `set_flash_info(..., SIZE_064K,
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
That exact case is in the host suite, and the suite's 51 cases are green at both
candidate grains — `0x00001000` and `0x00010000` — with the three grain-derived
cases recomputed for each.

#### `R8b` item 1, the settlement: the count of readings of this die is zero

The work order asks for two of ⟨the part's public datasheet, the driver
constant, a measurement⟩ to agree, and expects the desk answer to be *two
readings and a 未定 on the third*. 量 2026-10-04, that arithmetic does not hold:
there is **one** number, read four times, and **no** reading of the chip.

| source | state 2026-10-04 | mark | what would refute the state |
|---|---|---|---|
| the part's public **datasheet** | **not in hand.** 量 `refs/README.md` declares exactly two documents and both are Realtek SoC datasheets; no Eon document is in `refs/`, in `SOURCES.json` or in the tree. The part is nevertheless **named**: 量 `FLS-01`／`FLS-02` read `cFeon · QH32B-104HIP` off `U19`'s own package, so what is missing is a document, not an identification | 未定 | an EN25QH32B datasheet in `refs/` with its sha256 in `SOURCES.json`. It would enter as a `文`, and `SPEC.md` § 0 holds that a lone `文` never puts a value into code |
| the **driver constant** | **four constants, all 4,096, and not one of them a reading of this chip.** 讀 the loader's fallback descriptor `+24` (`FLS-06`), the vendor kernel's fallback `sector_size` (`FLS-23`), rlxfw's `RTL819X_SPI_ERASESIZE` (`FW-187`) and `RLXFW_SPI_WR_ERASE_GRAIN` (`FW-208`). The last two were 讀 **from** the first two, so the four are one number with three re-readings | 讀 | any of the four being traceable to something this chip said. `RDID` is the only thing it has ever said, and 讀 `spi_regist` `:568-574` consumes its third byte as `device_cap` and nothing else — `0x16` is inside `[SIZE2N_128K, SIZE2N_128M]`, so it survives as `1 << 22` = 4 MiB and agrees with `FLS-03`, while every geometry argument of the same call is a literal. That is why `FW-187`'s *"not something the chip reports"* is a reading of the code path rather than an assumption: on this path the chip supplies a capacity and nothing about erase geometry |
| a **measurement** | **partly taken, and not by rlxfw.** 量（行為）`FLS-13`: the loader's command set carries no erase verb, yet `FF` written over a written region reads back `FF`, so `FLW` erases for itself — which *points at* a 4 KiB read-modify-erase-program cycle and bounds no extent. 量 the vendor driver on this die prints `blkSize 10000h secSize 1000h pageSize 100h … UNKNOWN` through `prnFlashInfo` in its own boot banner (`bench/2026-08-30b/L3.log` and three later boots) — the 量 positive control that the UNKNOWN branch is the one taken **here**, which `FW-209` argues from code alone | 量（行為）, extent 未定 | an erase of one grain with the neighbouring grains digested either side of it, which `map 1 <group>` already resolves at 4 KiB |

🔄 **So the work order's stated reason for the 未定 is not the binding one.** It
says the blocker is that *a measurement is a write*. 量 three things against
that: a write has already happened on this device and produced `FLS-13`;
`FLS-26` proved flash bytes changed here; and § 17 carries a **third** row on
this blank — `FLS-06`–`FLS-08`, re-assigned to `R8b` on 2026-10-04 — whose
settling experiment is *"the EN25QH32B datasheet, or follow-on commands after
`RDID`"*, and the second half of that is **not** a write. The binding reason is
the table above: four constants that are one constant.

🔴 **And that non-write route has never been tried.** A JEDEC SFDP read returns
a parameter table whose erase-type entries each carry an opcode and a size,
which is exactly this blank, and it is a **read**. 量 `0x5a` and `sfdp` occur
**0** times in the vendor's `drivers/mtd/chips/rtl819x/` — positive controls in
the same sweep: `0x9f` once, `SPICMD_SE` three times — and **0** times in
rlxfw's own driver sources; 讀 `FLS-18`'s measured command set does not list it
either. So whether this part answers that opcode at all is itself 未定, and what
settles *that* is a read-only verb shaped like the existing `rdid` one, not an
erase. 推 that it answers: this rests on no source in this repository and is
written down to be refuted. **Refutation:** no `SFDP` signature word in the
reply, which closes the route and leaves `FW-187` 殘留's *"the decisive 量 is an
actual erase"* as the only way left.

🆕 **2026-10-05 (124th segment): the id has one name table on this disk, and
what it gives is a name.** 讀 `src-vendor/shibajee-linux-rtl8196e/drivers/mtd/spi-nor/spi-nor.c`
(`SOURCES.json` `shibajee-linux-rtl8196e`, pin `ef14875f9`, a third-party Linux
5.4.27 port) lists `{ "en25qh32", INFO(0x1c7016, 0, 64 * 1024, 64, 0) }` in its
EON block, beside `en25qh64` `0x1c7017`, `en25qh128` `0x1c7018` and `en25qh256`
`0x1c7019`. So `0x7016` is the device code of the Eon **EN25QH32** family — one
source, 讀, and it settles a *name*: it agrees with the `QH32B` that
`FLS-01`/`FLS-02` read off `U19`'s package (the table has no `B`), but the step
from id to family rests on this one table, because the vendor's three drops
carry no row for `0x1C7016` (`FW-209`). ⚠️ **It is not a second source for the
erase size.** Its geometry columns — a 64 KiB sector, 64 of them, flags `0` —
are a third party's reading of a datasheet, not this die's. The flag that would
have said 4 KiB is `SECT_4K`, which that file defines as *`SPINOR_OP_BE_4K` works
uniformly* and whose header comment asks for it on every new entry whose
hardware erases 4 KiB sectors, adding that *"some old entries may be missing 4K
flag"* for historical reasons; it is set on the neighbours `en25f32`, `en25q64`
and `en25qh64`, and not on `en25qh32` or `en25q32b`. 讀 that this is an absent
declaration; it does not say opcode `0x20` is refused, and it does not move the
4,096-or-65,536 question. `SPEC.md` `FLS-04` carries the family name.

⚠️ **One correction to how the fallback should be read.** 量 the whole
`spi_flash_registed[]` table (`:298-544`) is **29** rows, and the
⟨`pfErase`, `sector_size`⟩ pair moves together in every one: **26** rows carry
⟨`ComSrlCmd_SE` 0x20, `SIZE_004K`⟩ and **3** — all Spansion `S25FL` — carry
⟨`ComSrlCmd_BE` 0xD8, `SIZE_064K`⟩, while `block_size` is `SIZE_064K` in all 29
and no `pfErase` reads it. The UNKNOWN branch takes the 26-row pairing. So the
fallback is a **matched** opcode-and-granularity pair rather than a stray
number, and *"it is only a fallback"* does not make it arbitrary; what it does
mean, and the whole of what it means, is that nothing in that table was
consulted about `0x1C7016`. The two-source bar is therefore not *harder* than it
was before `FW-209` — it was never met, and what `FW-209` removed was an
apparent second source that is a fourth copy of the first.

**What this settlement does not establish.** It does not narrow the value: both
4,096 and 65,536 stay live, and `FW-187` 殘留's blast radius — at 64 KiB one
erase block holds the loader, `H601`, COMPDS and COMPCS together — is unchanged.
It does not establish that this part implements SFDP, that `FLS-13`'s behaviour
came from a 4 KiB cycle rather than a larger one, or that the vendor driver's
4,096 stride ever completed a multi-sector erase on this die. It is not a
licence to erase: the measurement stays `R8b`'s, after the owner's dated
`owner-yes` for that exact payload.

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
written down rather than left implicit: one writable `/proc` entry takes verbs,
and the shell that writes it is serial. An armed build has had a second
writable entry since `R8b` Gap A, `/proc/rtl819x-spi-img`; it takes no verb and
reaches no register, it only appends to a RAM buffer under `rtl819x_spi_lock`
(§ 13).

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

## 13. 🆕 2026-10-05 (`R8b` Gap A, 124th segment, desk, no power): the install path and the erase-size probe

§ 12 built a write engine with no way to feed it: `mtd->write` was reachable
only through a refusing `mtdchar`, and the `/proc` dispatcher had no verb that
carries data. This section is the data path, in `CONFIG_MTD_RTL819X_WRITE`
images only. **Not one line of it has run on the die.** Everything below is 讀
(from the code) unless marked; the host and build results are 量 about the host
and the compiler, not about this part. 🔄 2026-10-05: the 123rd segment's *"no
tool question is left undecided"* missed this gap and its twin in `rlxboot`;
`SPEC.md` `FW-230` indexes both, and § 12.1's L3 and § 12.3's `W4` are the
reading that no userspace path reached the engine before this section.

### 13.1 What a mainline image sees: nothing

Every new line in `rtl819x-spi.c` is under `#ifdef CONFIG_MTD_RTL819X_WRITE`,
and every touch point above the file's cited lines is line-neutral. 量
2026-10-05: HEAD's and the changed `rtl819x-spi.c`, compiled by the build's own
command line (from `.rtl819x-spi.o.cmd`, under the vendor tripwire, CLEAN), give
objects identical in section headers, every section's contents, disassembly with
relocations, and symbols (29,904 B each); the same pipeline with the `CONFIG_`
defined differs (`.text` 10,208 → 22,608 B), and the manual command reproduces
the build's own object byte for byte. Re-read 2026-10-05 from the saved objects
(`SPEC.md` `FW-236`): `cmp` finds the objects of both files — before and after
this item — and the build's own object byte-identical as whole files (sha256
`b87e8fb1dcb13190…`, 29,904 B each); the armed object is 52,716 B, and its
`.text*` sections total 22,608 B in 27 sections against 10,208 B in 17. The
files compared are the committed pair —
`a6add876^`'s `rtl819x-spi.c` (sha256 `3553f0d74033d80d…`) and `a6add876`'s
(`ee197f3f6a80bae4…`). One translation unit was compared, not the image:
`rtl819x-spi-write.c` is a separate unit that Kbuild builds only with the
`CONFIG_` (§ 12.1, L1) and was not part of this comparison, and
`rtl819x-spi-install.h` is included only inside the `#ifdef`. The mainline
build's `rlxfw-marks verify` still confirms `MK5`'s `rtl819x_spi_write_page`
ABSENT.

量 at image level, from the saved builds (2026-10-05): the mainline `vmlinux`
built before this item (`c7716fbe`, embedded recipe id `630eb5de`) against two
mainline `vmlinux` built from this item's sources — `s124/p`'s trial 4, built from
a clone at the **committed** `a6add876` (recipe `4be284c6`, `FW-231`), and the
implementer's cell `s124g-main2` (id `980b8bdd`). All three are 4,588,247 B, and
`cmp -l` finds exactly **8** differing bytes against each — the `lui`/`ori`
immediates of the id at its two consumers, `rtl819x_spi_read_proc`'s `sprintf`
(`0x80188a3a`–`0x80188a4b`) and `start_kernel`'s `rlxfw_puts_hex` call
(`0x802975e6`–`0x802975ef`), mapped from the file offsets through the ELF's
`LOAD` segment; for trial 4 the bytes `63 0e b5 de` become `4b e2 84 c6`, which
is `630eb5de` → `4be284c6` — and no other byte. The control is the same
comparison between a mainline and an armed build of the pre-item tree: 2,525,731
differing bytes. So this item's sources, built mainline, change nothing but the
id, in the committed tree's own build as well as in the implementer's.

### 13.2 The path, end to end

```
cat <payload> > /proc/rtl819x-spi-img                 # stage (RAM only)
echo arm 0x70000 0x190000 0x120000 > /proc/rtl819x-spi
echo install slotA sha=<64 hex> > /proc/rtl819x-spi
cat /proc/rtl819x-spi                                 # inst_* lines: the verdict
```

* **Staging.** `/proc/rtl819x-spi-img` is mode `0200`, has no `read_proc`, and
  appends each `write()` to one `vmalloc` buffer of 1,179,648 bytes, the largest
  region. An append that would pass that is refused whole with `EFBIG` and
  *poisons* the buffer: every later append is `EIO` and every install
  `IMG_BAD` until `echo img reset > /proc/rtl819x-spi`. It takes
  `rtl819x_spi_lock`, so an append cannot land inside an install. It issues no
  transaction, which is why it does not reopen § 12.3's rejection of a second
  writable entry *for verbs*.
* **The region table** is compiled in; no verb takes an address. `rlxboot`
  `0x010000`/65,536 and `rescue` `0x020000`/65,536 hold `cr6c` images;
  `barrier` `0x030000`/262,144 is erase-only (`D2`); `slotA` `0x070000` and
  `slotB` `0x190000`, 1,179,648 each, hold format-2 `RLXU` containers; `probe`
  `0x3E0000`/65,536 answers only to `eraseprobe` (§ 13.4). Compile-time asserts
  keep every base at or above `0x010000`, every base and size a multiple of
  64 KiB, the regions ascending and disjoint, and the last one ending at
  `0x3F0000`, where the state block begins.
* **Authorisation, in order.** The verb parses strictly (single spaces, nothing
  trailing, names case-sensitive). The arm in force -- a copy from the write
  TU's getter `rtl819x_spi_wr_get_arm()`, taken under `rtl819x_spi_lock`
  (`D20`) -- must be exactly the region with a budget of at least its size; the
  caller zeroes its copy first, so a failed read is both `ARM_READ` and an
  unarmed copy. For `install`: something staged and no larger than the region;
  the boot KAT passed; the staged bytes' sha256 (the same
  `crypto/sha256_generic.c` `verify` uses) equal to the typed digest -- the
  staged digest is never printed, so a card cannot copy it off the device; and
  the payload's own declaration names this region (`RLXU`: format 2, header 96,
  signed `flash_at` = base, `flash_form` = `WHOL`, length = 160 + payload_len;
  `cr6c`: magic, `burnAddr` = base, 16 + len = staged length, even len, a zero
  16-bit sum). The Ed25519 signature is not checked here; rlxboot checks it at
  boot.
* **One arm, one attempt.** Every `install`, `erase` or `eraseprobe`, whatever
  its outcome -- a typo included -- ends with `rtl819x_spi_wr_do_disarm()`.
* **The write order (`D5`).** Erase the whole region in 4 KiB `SE` steps,
  ascending (so the block holding the old header goes first); program pages
  1 .. n-1; program page 0, the header, LAST; read the whole region back
  through PIO and compare it to the staged bytes, then `0xFF`. Each operation is
  re-checked by `rtl819x-spi-wrpolicy.h` (the forbidden window first) against a
  per-phase arm equal to the region, and executed by § 12's `pp_page` /
  `se_block`. Not through `write_page`/`erase_sector`: their per-operation
  budget is capped at `hi - lo` by the arm verb, and an install spends the size
  twice. A cut anywhere before the last operation leaves the new header absent
  and, after operation 0, the old one erased.
* **Pacing (`D10`).** `pace=1..30000` ms (the cap was 10000 until 2026-10-05,
  raised so a 64 KiB region's paced write lasts 60 s, past the bench's 40 s
  window) is slept after each 64 KiB block of the erase and program phases,
  never after the header page or during read-back; every console line and
  `/proc`'s `inst_paced` say so.

### 13.3 `D11`, from the code

Every erase is `se_block()`: `WREN`, `SE` `0x20` with a 3-byte address, then the
bounded `RDSR` poll. The step is `RLXFW_SPI_WR_ERASE_GRAIN` (`0x1000`), and the
policy's `GEOM` conjunct refuses it unless it equals the mtd `erasesize`. With
every region 64 KiB-aligned and a multiple of 64 KiB, the erased range is the
region exactly whether `SE` clears 4,096 or 65,536 bytes -- at 65,536 each block
is erased sixteen times, which costs time and not correctness. The host suite
computes both unions from the driver's own plan function, with a control (a
64 KiB step on a 4 KiB part) that must come out unequal.

### 13.4 `eraseprobe` -- the reading `FW-227` counts as zero

Under an arm equal to `probe` (`echo arm 0x3e0000 0x3f0000 0x10000 > …`):

1. read the whole block; refuse (`PROBE_DIRTY`, `ENOTEMPTY`, nothing written)
   unless every byte is `0xFF`;
2. count the idle `RDSR` polls that fit in 10 ticks, inside the usual
   claim/release -- read-only, and the only way to turn poll counts into time,
   because `jiffies` is this board's only clocksource (量
   `bench/2026-09-03/TM-2a`, `TM-2b`);
3. program a marker page (`'A'..'Z'`, never `0xFF` or `0x00`) at `+0x0000`,
   `+0x1000`, `+0x8000`, reading each back (`PROBE_MARK` on a mismatch);
4. issue exactly ONE `SE` at `+0x0000`, recording its `RDSR` polls and ticks
   (and one page program's);
5. classify which markers it cleared: `EII` → 4096, `EEI` → 32768, `EEE` →
   65536, `III` → 0 (the opcode did nothing), anything else → -1 (`PROBE_ANOMALY`);
6. re-erase the block at the step the verdict proves (an anomaly at 4,096, the
   step right under every candidate; a no-op part not at all -- this driver has
   no other opcode), verify `0xFF`, and print
   `eraseprobe se_bytes=… se_polls=… se_us=… pp_us=… clean=1|0|-1`, with
   `eraseprobe_detail` beside it (the three marker states, ticks, the
   calibration, the clean-up step and count).

⚠️ **Three sample points bound the size; they do not measure it.** 4096 means
256 ≤ S ≤ 4,096, 32768 means 4,352 ≤ S ≤ 32,768, 65536 means S ≥ 33,024. An
8 KiB part reads 32768 and a 2 KiB part 4096, both cleaning silently -- the host
suite shows both. A part whose `SE` clears more than 64 KiB would reach the state
block at `0x3F0000`; no candidate does (`FW-187`: 4,096 or 65,536), the
2026-08-16 dump read that block erased, and the host suite shows the reach on a
simulated 128 KiB part rather than leaving it a sentence. `se_us` and `pp_us`
are tick-resolution (10,000 µs); `se_polls × cal_ticks × 10,000 / cal_polls` is
the finer figure, and it assumes a poll costs the same busy as idle.

⚠️ **The ceiling's duration is 推, and so is every sentence that says it
outlasts an erase.** 讀 `rtl819x_spi_wait_wip`: one poll is `cs_low` (one `SFCSR`
ready read and one `SFCSR` write), one `SFDR` write (the `RDSR` opcode), a
second `cs_low`, one `SFDR` read, and `cs_high` (one ready read and one write) —
at least **8** register accesses, `SFCSR` read ×3, `SFCSR` write ×3, `SFDR`
write ×1 and `SFDR` read ×1, and each ready loop reads more than once while the
controller is not yet ready. 推, upper end: if no access costs more than the
2.075 µs `FW-34` Group F measured for one uncached load through the flash
window — which the driver's comment calls *the slowest access on this bus*, an
assumption, because no plain register access on this die has been timed — then
200,000 polls cost at most 3.3 s at 8 accesses and 3.7–4.2 s at 9–10.
`FW-48`'s end-to-end PIO rate (at least 1,065,510 B/s) bounds one `SFDR` data
word from above, at 3.754 µs, and gives a poll no floor, so **no lower bound is
written here**. The two readings that make it 量 are already in `eraseprobe`'s
output: `cal_polls` and `cal_ticks` give the idle poll rate, so the ceiling's
duration is 200,000 divided by it; and the real `SE`'s `se_polls` says whether
200,000 outlasted the erase — below 200,000 it did, at exactly 200,000 it did
not and `ENGINE` ended it. `SPEC.md` `FW-238` indexes this, and `eraseprobe` is
now named as the experiment in the three § 17 rows that carry the open erase
size (`FLS-06`–`FLS-08`, `FW-187` 殘留, `FW-191` 殘留), which until 2026-10-05
named a datasheet, follow-on commands, or *an actual erase* and not this probe.

### 13.5 Refusals, by name

`/proc/rtl819x-spi` prints `inst_reason` by name: `SYNTAX`, `REGION`,
`ERASE_ONLY`, `NOT_ERASABLE`, `PROBE_ONLY`, `ARM_READ`, `UNARMED`, `ARM_WINDOW`,
`ARM_BUDGET`, `IMG_BAD`, `IMG_EMPTY`, `IMG_SIZE`, `KAT`, `HASH`, `SHA`,
`HDR_MAGIC`, `HDR_FORMAT`, `HDR_FLASH_AT`, `HDR_FORM`, `HDR_LEN`, `HDR_SUM` and
`PROBE_DIRTY` are decided before anything is sent; `CMP`, `PROBE_MARK`,
`PROBE_ANOMALY` and `PROBE_UNCLEAN` only after something was; `POLICY`, `NOMEM`
and `ENGINE` (which carries the primitive's own errno) can come at either
point. `inst_refused` counts attempts stopped before `install`/`erase` printed
its GO line, or before `eraseprobe` sent its first program; `inst_failed`
counts the rest -- an operation may or may not have been sent by then, and
`eraseprobe`'s `clean=-1` says a stop came after a write and before the block
was read again. On the card side, `cardcheck`
treats a `--send` that writes `install`, `erase` or `eraseprobe` to
`/proc/rtl819x-spi` -- or a write there it cannot read -- as a flash write that
needs the owner's dated yes for that exact payload (`FW-113`, its `A56`-`A62`,
`B16`). The corpus was measured before the rule went in, and re-counted
2026-10-05 (`SPEC.md` `FW-237`): 95 cards; **2,264** `--send` payloads by
`cardcheck`'s own `sends_with_cells` (the commit message and the comment above
`devflash` say 2,265, which this re-count does not reproduce at `fa36f7a2`,
`8283d033`, `94d97924`, `a6add876` or `c0349701`, and the one-send difference is
unattributed); **44** simple
commands writing the node, every one an `echo` of literal words — `map` 32,
`verify` 5, `corrupt` 4, `probe`, `trywrite` and `wedge` 1 each — and **0** flash
verbs, so no committed card's verdict moves. `B16` sweeps that population on
every run and fails below 40 writes, so a sweep that read nothing cannot pass.
What the rule cannot see is `FW-113`'s old boundary: a write made outside a
single-quoted `--send`, and a script on the device that writes the verb; and
`arm` is not refused, because it writes nothing to flash and the yes belongs to
the verb that does.

### 13.6 How it was checked at the desk

* `tools/test-spi-install.sh` (量 2026-10-05, exit 0): the pure decisions in
  `rtl819x-spi-install.h` (571 cases, on fixtures made by `mkfw2.build` and
  `mkcr6c.build_image` with the development seed, digests from `hashlib`), and
  the Gap A block **extracted from the driver** and run against stub kernel
  APIs and a simulated part of each size, a no-op part, a half-erasing part,
  stuck cells, cuts at nine points and a stopped tick (182 cases). Five
  expectation flips and nineteen source mutations, each compiled, each red.
* Builds through a shadow `FWRE_WORK` (a pin-identical sparse clone; tripwire
  CLEAN and TRIPPED both ways; `diff -rq` against the canonical tree empty, with
  a one-byte control): mainline green with `MK5` absent, armed green under
  `--expect-present MK5`, no compiler warning naming either TU.

### 13.7 What § 13 does not establish

That any of it works on this die. The part's erase size and time, which
`eraseprobe` exists to read and has not. That `RTL819X_SPI_WIP_SPINS` (200,000
polls) outlasts an erase here -- if it does not, the install stops with
`ENGINE` and the region is left erased and invalid, and the probe records
`se_polls=200000`. That busybox `cat` streams 1.1 MiB into a procfs write path
on this image — or `nc -l`, which `notes/update-chain.md` § 6 records as the
delivery, because the payloads cannot ride inside the initramfs (`SPEC.md`
`FW-240`). That a container's signature is valid, or that rlxboot accepts
what was written (Gap B). That the simulated cuts -- an operation not done, half
a header page -- cover the part's real partial states.

## 14. 🆕 2026-10-07 (`R8b`, 125th segment, bench): the install path and `eraseprobe` on the die

§ 13 said not one line of the install path had run on the die. 量 `bench/2026-10-07`: 33 write verbs
ran, from armed images `75cfa588` and, after `T2a`, `6b1bde59` (the same code with the `cs6c` guard,
built from a clone-only commit; the committed equivalent is the `cs6c` commit, `f257a848`). 20
completed and
read back equal, 11 were stopped by a power pull after at least one 64 KiB erase block, 2 were
refused before any operation. Every string was an `owner-yes` row of its card (`FW-113`).

### 14.1 The erase size: 4,096, bounded from both sides (`SPEC.md` `FW-244`)

Upper bound. `E02`, under an arm equal to `probe`:
`RLXFW-SI-PROBE se_bytes=4096 m=EII polls=8664 ticks=2`, then `RLXFW-SI-END OK`; `E03`:
`eraseprobe se_bytes=4096 se_polls=8664 se_us=20000 pp_us=0 clean=1` and
`eraseprobe_detail ran=1 m0000=E m1000=I m8000=I se_jiffies=2 pp_polls=144 pp_jiffies=0
cal_polls=40345 cal_ticks=10 clean_step=4096 clean_ops=16`. One `SE` at `0x3E0000 + 0` cleared the
marker there and left the one at `+0x1000`: 256 ≤ S ≤ 4,096 (§ 13.4's own reading of `EII`). The
`STOP` rule written before the reading passed on all four terms.

Lower bound. `W4b` erased the barrier, `0x030000`–`0x06FFFF`, with 64 `SE`s at a 4,096-byte stride,
and read all 262,144 bytes back as `0xFF` (`inst_cmp_ok 1`, `inst_cmp_bytes 262144`,
`inst_cmp_diff 0`; for an erase-only region `rlxfw_spi_inst_cmp()` expects `0xFF` everywhere). Before
the erase that region held only 883 bytes of `0xFF` — `SPEC.md` `FW-225`, two dumps — and was still
the dump's at the seating's start (`A04`'s `map 0`: groups 1–3 equal to the dump, `LOG.md` 125th),
outside every region `W1b`–`W3b` named (`rlxboot`, `rescue`, `slotA`; 讀 the compiled-in region
table), and still not erased after `W2b` (`X-W2c-m1f`: none of units `0x030000`–`0x03F000` carries
`f47a8ec3…`, the sha256 of 4,096 bytes of `0xFF`). If an `SE` cleared S < 4,096 bytes, at least
64 × (4,096 − S) bytes would have kept their old values, at most 883 of them `0xFF`; the read-back
passes only for S ≥ 4,083, so S = 4,096 for any power-of-two erase unit.

So `RLXFW_SPI_WR_ERASE_GRAIN` and `RTL819X_SPI_ERASESIZE`, both `0x00001000u`, are right, and no
code changes; `H601` and `0x010000` are eight erase blocks apart (`FW-187`'s 4 KiB case). Page and
block size were not measured: no `0xD8` was ever issued, and the page is only bounded below
(§ 14.3).

### 14.2 The `RDSR` ceiling, with both of its readings (`FW-245`)

`FW-238` named the two readings that would turn the ceiling into a measurement. 量: the real `SE`
took `se_polls=8664`, against `RTL819X_SPI_WIP_SPINS` = 200,000, about 23 times fewer; the idle
calibration counted 40,345 polls in 10 ticks. 推, on § 13.4's assumption that a busy poll costs
what an idle one does: one `SE` about 21.5 ms, one page program's `WIP` wait about 0.36 ms, and the
200,000-poll ceiling about 0.50 s. The `SE` time has two more readings that agree with the first:
`se_jiffies=2` bounds it to 10–30 ms, and the first 64 KiB erase block (16 `SE`s) of each unpaced
64 KiB install printed at 360–380 ms after its GO line (`W1b`, `W2b`, `K1b`, `K2b`, `RD08b`), about
23 ms each with command overhead. Every armed `/proc` read after an install in the seating reads
`n_wip_timeout 0` and `n_rdy_timeout 0`. `FW-238`'s 推 upper bound of 3.3–4.2 s is loose by about
seven times.

### 14.3 What the path costs (`FW-246`)

From the installs' own `ms=` (two `END` lines cut short by `--until`'s 0–50 ms read-on, `FW-135`,
were read from `/proc`'s `inst_ms`): a 64 KiB region 480–510 ms (`W1b` 500, `W2b` 510, `K1b` 490,
`K2b` 480, `RD08b` 510); a slot — 288 `SE`s, 4,333 page programs, the whole region read back —
10,260 to 11,240 ms over thirteen installs (`W3b` 10,260, `W5b` 10,680, `B2Rb` 10,900, `B3Rb`
10,910, `B4Rb` 11,000, `B5Rb` 11,070, `BCi` 11,240, `A1Rb` 10,690, `A2Rb` 10,760, `A3Rb` 10,760,
`A4Rb` 10,700, `A5Rb` 10,870, `ACb` 11,180); the barrier 1,670 ms. `n_writes` agrees with the
plans: 4,621 per slot (288 + 4,333), 178 for the two 64 KiB regions, 4,685 for slot A plus the
barrier.

Paced at `pace=2000`, from the ten cut writes' progress lines (slopes, not intercepts): `E k` at
about 612 + 2,415·k ms and `P k` at about 43,840 + 2,170·k ms; the latest line seen is
`P 14 74220`. 推, because no paced slot write ran to its end: `P 16` at about 78.6 s, then one more
2 s sleep — the loop sleeps after every block but the header (`rtl819x-spi.c`, `if (r->pace_ms &&
!op.commit) msleep(...)`) — so the header at about 80.6 s and `END` at about 81.8 s. The 125th
segment's *header at about 79 s* left out that sleep.

Page. Each slot install issued 4,333 page programs of 256 bytes and read back equal, so this part's
page is at least 256 bytes; 推 that a smaller page would have wrapped and failed the compare
(JEDEC's definition of `PP`, the part's datasheet not being in hand).

### 14.4 Refusals seen on the die, and one `echo` that called the handler three times (`FW-247`)

Two refusals ran on the die, both before any operation, both with `n_writes 0` after: `Z03`, the
deliberate wrong digest (`RLXFW-SI-END SHA rc=-77`, `RLXFW-SI-RC=FFFFFFB3`), and `BCb`, an install
sent without its arm (`RLXFW-SI-END UNARMED rc=-13`, interleaved with the command's echo as `FW-47`
describes, then `RLXFW-SI-RC=FFFFFFF3`). Both were followed by `RLXFW-SI-END SYNTAX rc=-22`, and
both left `inst_attempts 3`, `inst_refused 3` and `inst_reason SYNTAX` (`Z04`, `X-BCbc-cat`): one
`echo` reached the handler three times, and `/proc` keeps the last call's reason. A success adds one
(`E02`: 3 → 4; `BCi`: 3 → 4). 讀 why the re-sends cannot write: `rtl819x_spi_verb_inst` disarms on
every exit, and the arm check precedes every erase and program. 推 the mechanism: busybox ash's
built-in `echo` re-writing its buffer after a failed `write()`, the path `FW-41` already shows
printing a refused payload minus its last character. **A gate reads the refusal reason from the
console's first `RLXFW-SI-END` line, not from `inst_reason`.**

### 14.5 Staging: the sender finishes before the device has (`FW-248`)

`W3s4` read `img_len 979183` (`img_writes 239`) right after `sendimg: sent 1109152 bytes`; 36 s later
`X-W3s4w1` read 1,109,152 (271 writes). From then on the session's `stage.sh` polled: the first read
of each of the other thirteen 1.1 MB stagings fell between 839,885 and 995,571 bytes, and the next,
about 7 s later, was complete. All seven 18,642-byte stagings were complete at the first read. The
gate that stopped `W3` was `stage.sh`'s *`img_len` equals the manifest's size*; had it not, the
install's sha256 would have refused, so an early read costs a refusal, never a wrong write. 推 the
mechanism: TCP counts the bytes sent once they are in the host's socket buffer, and the device's `nc`
then drains them into procfs at most 4 KiB per `write()`.

### 14.6 Five comments that still mark the erase size open, on purpose

`rtl819x-spi-wrpolicy.h` (three places, including `RLXFW_SPI_WR_ERASE_GRAIN`'s own line) and
`rtl819x-spi.c` (two) still call the erase size unsettled. They are left: every byte under `config/`
moves `RECIPE_ID`, and `v1.0`'s recipe is `9bb2bec7`. 🔄 `034b5a7d` moved the recipe for `R6c` and left them, so they
change in the next commit after `v1.0` that moves the recipe, and § 12.4's quotation of that line stays a true quotation until then.

### 14.7 What § 14 does not establish

The exact page and block size. The `SE` count of any erase but the probe's. A busy poll's cost. The
length of a paced slot write. The re-send's mechanism. That the committed `cs6c` guard runs on the
die — the image that wrote is `6b1bde59`, built from a commit not in this repository. Any part but
this one (`1C7016`), any temperature or supply.
