# The loader's flash write path — F45

**DAY-ZERO item 2c. Desk work, 2026-08-23. Nothing here was measured on the
device.**

Three sources, and they are not equally trustworthy:

| | what it is | weight |
|---|---|---|
| **A** | `stage2.bin`, disassembled from **this unit's own** flash dump | this unit; definitive for what its loader does |
| **B** | `WECB-VZ-GPL`, `rtl819x/bootcode/` — vendor bootcode C source | **a different bootcode generation.** `SOURCES.json` already flags this: do not assume the command set matches |
| **C** | `WECB-VZ-GPL`, `rtl819x/linux-2.6.30/drivers/mtd/chips/rtl819x/` — the Linux MTD driver for the same SPI controller | same controller, different consumer |

Every statement below says which source it came from. Where only B says
something, it is marked as such, because B is not this unit.

---

## 1. Where `burn()` writes, and what stops it — R8 precondition 2

`burn()` at `0x80401318` is **not** a flash-write primitive. It is the image
parser and dispatcher. **(A)**

It refuses anything shorter than 17 bytes (`li v0,16` / `sltu v0,v0,a1` /
`beqz`), then builds 32-bit fields out of the byte buffer four `lbu` at a time
with shifts and `or` — never `lwl`/`lwr`, which this core's bootcode does not
use anywhere (`notes/lwl-mystery.md`). It matches a four-byte section signature
against a table — **`boot`, `sqsh`, `w6cp`, `jw6c`, `cwmp`, `ksap`, `ALL1`,
`ALL2`** — verifies a checksum (`%s imgage checksum error at %X!`, the vendor's
own spelling), prints

```
burn Addr =0x%x! srcAddr=0x%x len =0x%x
```

and writes. On completion it prints `Flash Write Successed!` or
`Flash Write Failed!`. **(A)**

### The bounds check, and what it does not check

```
804017a8   andi  v0,s1,0xfff        ; length 4 KiB aligned?
804017b0   bnez  v0,...             ; if not, skip
804017bc   lw    v1,0(s6+s1)        ; the word just past the end of the image
804017c0   lui   v0,0xdead
804017c4   ori   v0,v0,0xc0de       ; 0xDEADC0DE
804017c8   bne   v1,v0,...          ; not the marker -> skip
           -> "it is special wrt image need add 4 byte to burnlen =%8x!"
804017e0   addiu s1,s1,4            ; length += 4

80401804   addu  v1,zero,v0         ; v1 = destination offset
80401808   addu  v0,v1,s1           ; v0 = destination + length
80401814   lw    s0,0(0x8040a8a4)   ; chip descriptor pointer
8040181c   lw    a3,12(s0)          ; a3 = capacity
80401824   sltu  v0,a3,v0           ; capacity < end ?
80401828   beqz  v0,0x80401888      ; no  -> ordinary single write
80401840   subu  a3,a3,v1           ; yes -> truncate to (capacity - destination)
```

**Read out of the code:** the only bound is the **top** one — the chip capacity,
taken from the chip descriptor the SPI probe filled in. An overlong write is
truncated at the end of the chip rather than rejected.

**There is no lower bound.** Nothing in `burn()` compares the destination
against a floor, and `boot` is one of the eight signatures it accepts. The
vendor's own upgrade path will therefore write offset 0 if an image section asks
it to.

That is what R8 precondition 2 needed, and it is why the rule in `CLAUDE.md` —
never write `0x000000`–`0x005FFF` — has to be enforced by our own tooling.
**The device does not enforce it.**

`0xDEADC0DE` is a marker sitting immediately after a 4 KiB-aligned image; the
loader extends the burn length by four bytes when it finds one. **(A. What
writes that marker is not established here.)**

`burn()` calls four functions: `0x804012b0`, `0x80404fe4`, `0x80406d3c`, and
`0x80407958` (the last is the printf). Which of them erases and which programs
is **not yet read out**. The SPI block below is what they reach.

---

## 2. The SPI controller — R5b's register map, and the JEDEC ID path

### Registers

| name | address | what |
|---|---|---|
| `SFCR` | `0xb8001200` | configuration — clock divider, read/write byte order, TCS |
| `SFCR2` | `0xb8001204` | command byte, chip size, IO width, dummy cycles |
| `SFCSR` | `0xb8001208` | control/status — chip select, transfer length, ready, command byte |
| `SFDR` | `0xb800120c` | data |
| `SFDR2` | `0xb8001210` | second data register |

**Three independent sources agree**, which is more than the bar `CLAUDE.md`
sets:

- **B** names and documents them (`bootcode/boot/flash/spi_common.c`).
- **A** — this unit's own loader — references `0xb8001200` at 2 sites,
  `0xb8001204` at 1, `0xb8001208` at 19, and `0xb800120c` at 14. Its SPI
  routines sit around `0x804055ac`–`0x80405d44`.
- **D** — `refs/RTL8196E-VEx-CG_Datasheet_1.1.pdf` §7.4.5–7.4.9, which is the
  datasheet for **this** part rather than for the 8196C/8198 that B targets.
  Every address matches.

`SFDR2` is a real register on this part per D, and is referenced **zero** times
by A. Recorded as *present on the silicon, unused by this loader*.

### `SFCSR` bit layout

From D, table 10, and every field matches B's shift macros exactly:

| bits | field | meaning | B's macro |
|---|---|---|---|
| 31 | `SPI_CSB0` | chip select 0. `0` active, `1` not active. Reset `1` | `<< 31` |
| 30 | `SPI_CSB1` | chip select 1, same encoding. Reset `1` | `<< 30` |
| 29:28 | `LEN` | transfer length in bytes: `00`=1, `01`=2, `10`=3, `11`=4. Reset `11` | `<< 28`, 2 bits |
| 27 | `SPI_RDY` | busy flag, read-only. `0` busy, `1` ready | `<< 27` |
| 26:25 | `IO_WIDTH` | `00` serial, `01` dual, `10`/`11` reserved | `<< 25`, 2 bits |
| 24 | `CHIP_SEL` | `0` = CS0#, `1` reserved | `<< 24` |
| 23:16 | `CMD_BYTE` | the 8-bit SPI command. D's own examples: *"'Read Data' is `0x03`. 'Read ID' is `0x9F`."* | `<< 16`, 8 bits |
| 15:0 | — | reserved | |

**`SFCSR` and `SFDR` do not provide byte access** (D). They must be read and
written 32 bits at a time. That is the kind of thing R5b would otherwise find
out by writing a driver that silently does nothing.

The `Read ID is 0x9F` example is D's own, so the JEDEC ID command is now
attested by the datasheet for this part as well as by B.

### A fourth source for the bit layout, and it is the strongest one

A, B and D above are a binary's *references* to an address, a header's macros,
and a document. **A's `RDID` routine is different in kind: it is this unit's own
code demonstrating the semantics by depending on them.**

`ComSrlCmd_RDID()` sits at `0x804058bc` in this unit's loader and is called
twice:

```
8040591c   lui  v0,0xb800
80405920   ori  a0,v0,0x1208     ; a0 = SFCSR
80405924   lui  v1,0x800         ; 0x08000000  = bit 27
80405928   lw   v0,0(a0)
80405930   and  v0,v0,v1
80405934   beqz v0,0x80405928    ; spin until bit 27 is set
8040593c   ori  s0,s0,0x120c     ; s0 = SFDR
80405940   lui  v0,0x9f00        ; 0x9F000000
80405944   sw   v0,0(s0)         ; issue RDID
   …
8040595c   lw   s0,0(s0)         ; read the answer back out of SFDR
80405970   move v0,s0            ; and return it
```

D's table 10 says bit 27 of `SFCSR` is `SPI_RDY`, `0` busy and `1` ready.
**This loader spins on exactly that bit before touching the data register.**
A document can be wrong about a part; code that has been booting this board
since 2018 cannot be wrong about the bit it waits on.

Two further things the sequence settles:

- The command goes into **`SFDR`**, not into `SFCSR`'s `CMD_BYTE` field.
  D marks `CMD_BYTE` as *"Only Used in MMIO Mode"*, and this is the serial path,
  so the two agree.
- **The chip has been answering `RDID` on every boot of this board since it left
  the factory.** `upstream/notes/loader-chip-table.md` already established why
  the banner prints `chipName: UNKNOWN` — the loader looks the answer up in a
  32-entry table and this part has no row. What was missing was never the
  measurement; it was the register-level specification needed to ask the
  question from code we control.

**The value is still not known**, and 🔴 **2026-08-25b tried to read it out of
`SFDR` and that prediction was refuted** — see the reading below.

### The window, read on the device for the first time — 量 2026-08-25b

`DW B8001200 4`, once after a cold power-on and once after a watchdog reset
(`bench/2026-08-25b/SPI-cold.log`, `SPI-warm.log`):

```
cold  B8001200:  3FC00000  0BA08000  D8050000  FFFF0002
warm  B8001200:  3FC00000  0BA08000  D8050000  FFFF0000
                 SFCR      SFCR2     SFCSR     SFDR
```

**`SFCSR = D8050000`, decoded against D table 10 above:** `SPI_CSB0` = 1 and
`SPI_CSB1` = 1 (both chip selects inactive), `LEN` = `01` — **two bytes, not the
reset value `11`** — `SPI_RDY` = 1 (ready), `IO_WIDTH` = `00` (serial),
`CHIP_SEL` = 0, and `CMD_BYTE` = **`0x05`**, which is the SPI `RDSR` opcode.
`SFCR2`'s top byte is **`0x0B`**, `Fast Read`.

**So this loader does not leave the controller at reset; it leaves it configured
for status polling**, with the memory-mapped read command set to `Fast Read`.
That is a fact `R5b` needs and it was not in any of the three sources.

🔴 **A prediction of mine was refuted here, and it is kept.** `ComSrlCmd_RDID()`
runs twice on every boot and its last act is `lw` from `SFDR`; `SPEC.md`
`REG-21`'s flash descriptor at `0x8040FBD4` holds `001C7016 1C701600`, the same
three bytes two ways. So `SFDR` was predicted to still hold the JEDEC ID
`1C 70 16`. **It reads `FFFF0002`.** Either `SFDR` does not retain across an idle
period, or something read it since, or the last transaction was the `RDSR` that
`CMD_BYTE` records — this reading does not separate them.

✅ **What rescued the cell is that `SFDR` MOVED between cold and warm**
(`FFFF0002` → `FFFF0000`). Without that, "the other three words are identical"
would have been compatible with *the divider does not change* **and** with *this
window does not reflect boot-time state at all*, and the cell could not tell them
apart. **A ride-along whose designed positive control fails is worth exactly what
its accidental one is worth**, and here that happened to be enough.

**What it settles**: `SFCR` carries the clock divider, and it is byte-identical
cold and warm — so **the SPI-divider hypothesis for `CLK-15`'s cold-minus-warm
4.5 … 14.5 ms is excluded**. The next candidate is the NOR's own power-on
wake-up, and that is a datasheet question (`tVSL`, deep-power-down recovery) for
the EON part `REG-21` identifies, not a register read.

⚠️ **`SFDR2` at `0x1210` is still unread**, and not by choice: `LDR-07` rounds
`DW`'s word count **up** to a multiple of four, so `DW B8001200 1` through `4`
all print the same four words. Reading the fifth needs a different start address.

⚠️ **`DW` issues loads only.** On this controller a command is issued by
**writing** `SFDR` — `sw` of `0x9F000000` in the `RDID` sequence above — so
reading the window is not a transaction. No `EW`, no flash write.

*(Below: the path as traced on 2026-08-23, before any of it was read.)*
It takes one console command and no new code.

### Where the JEDEC ID ends up, and why `burn()`'s only bound is a fallback

**(A, traced 2026-08-23. This closes `C-3`'s residual, and it also changes what
§1's bounds check means on this unit.)**

`ComSrlCmd_RDID()` has exactly two callers and they are adjacent, both inside
the SPI probe at `0x80405030`:

```
80405050   jal   ComSrlCmd_RDID      ; first call -- the result is DISCARDED
8040505c   jal   ComSrlCmd_RDID      ; second call
80405064   srl   s1,v0,0x8           ; s1 = the 24-bit JEDEC ID
80405074   addiu a0,v0,-10396        ; 0x8040D764 = the 32-row chip table
80405080   lw    v0,0(v1)            ; row[0] = the stored id
80405088   bne   v0,s1,next          ; compare, 0x20 stride, 32 rows
804050b0   bne   s0,a1,found         ; s0 == 32 -> no row matched
```

**Neither caller stores it**, so the first reading of this — that `v0` is a
return register and the value is therefore unreachable — was right about the
callers and wrong about the outcome. The value is stored one level down.

On a miss the loader installs a **fallback descriptor** and this unit takes that
path, which is why the banner prints `chipName: UNKNOWN`:

```
804050b8   li    v0,31
804050c4   li    a1,40
804050d4   li    v0,4096             ; sector size
804050dc   li    v0,256              ; page size
804050e4   v0 = 0x8040ADCC           ; the name -- the string is literally "UNKNOWN"
80405124   move  a1,s1               ; the JEDEC ID
80405128   li    a2,22               ; *** address bits ***
8040512c   jal   0x8040533c
80405130   lui   a3,0x1              ; block size 0x10000
```

and the installer at `0x8040533C` writes a 72-byte record into an array based at
`0x8040FBD4`, indexed by `chip * 72`:

```
80405374   sllv  s1,s1,a2            ; capacity = 1 << address_bits
80405388   addiu v0,v0,-1068         ; 0x8040FBD4
80405390   sw    a1,0(s0)            ; +0   = the JEDEC ID
80405398   sb    v0,4(s0)            ; +4   = manufacturer byte
804053a0   sb    v0,5(s0)            ; +5   = device byte 1
804053a4   sb    a1,6(s0)            ; +6   = device byte 2
804053b8   sb    s4,8(s0)            ; +8   = address bits
804053bc   sw    s1,12(s0)           ; +12  = capacity
804053c0   sw    s3,16(s0)           ; +16  = block size
804053d8   sw    s3,20(s0)           ; +20  = capacity / block
804053dc   sw    s2,24(s0)           ; +24  = sector size
```

**Two things follow, and the second one is the more important.**

**One — the JEDEC ID is at a fixed address.** `0x8040FBD4 + 0` holds it, and
`+4`/`+5`/`+6` hold the same three bytes again in a different layout. So a
single `DW 8040FBD4 8` at the `<RealTek>` prompt reads it, with **four
precomputed values in the same output as the control**:

| offset | expected | where it comes from |
|---|---|---|
| `+0` | **unknown — this is the measurement** | |
| `+12` | `0x00400000` | `1 << 22`, and 22 is the fallback's literal |
| `+16` | `0x00010000` | `lui a3,0x1` |
| `+20` | `0x00000040` | capacity / block |
| `+24` | `0x00001000` | `li v0,4096` |

If those four match, the fifth is trustworthy. If they do not, the address or
the layout is misread and the ID must not be believed. `plan/` §17 listed the
JEDEC ID as removed because R5b's MTD probe would read it; it turns out the
console reads it first, with no driver and no risk.

**Two — `burn()`'s only bounds check is this fallback constant.** §1 established
that the single bound is the top one, `lw a3,12(s0)`, taken from the chip
descriptor. On this unit `+12` is `1 << 22` = 4,194,304, and that number comes
from a **hard-coded default for an unidentified chip**, not from having
identified the part. It is correct for this device by coincidence: a 4 MiB
default was the sane guess in 2014 and this is a 4 MiB part.

**Read out of the code:** the loader never learns how big its flash is. It
assumes. R8 must not rely on that bound, and `flashguard` has to enforce the
`CLAUDE.md` floor itself — which §1 already said, for a different reason.

### Commands

From B, `spi_common.c`, with the vendor's own comments:

| opcode | name | comment |
|---|---|---|
| `0x06` | `WREN` | sets the write enable latch |
| `0x04` | `WRDI` | resets it |
| **`0x9F`** | **`RDID`** | **"outputs JEDEC ID: 1 byte manufacturer ID & 2 byte device ID"** |
| `0x05` | `RDSR` | read status register |
| `0x01` | `WRSR` | write status register |
| `0x03` / `0x0B` | `READ` / `FASTREAD` | |
| `0x20` | `SE` | sector erase; `SPI_SECTOR_SIZE` = `0x1000` |
| `0xD8` | `BE` | block erase; `SPI_BLOCK_SIZE` = `0x10000` |
| `0x60` | `CE` | chip erase |
| `0x02` | `PP` | page program; `SPI_PAGE_SIZE` = `0x100` |
| `0xB9` / `0xAB` | `DP` / `RDP` | deep power down, and release from it |

**This closes the JEDEC ID question at the desk.** `plan/` §17 listed it as
stuck on instrumentation. It is not: the same controller `FLW` already drives on
this device can issue `0x9F`, and B has a function that does exactly that,
`ComSrlCmd_RDID()`. Reading the ID still needs code running on the device
(R5b's MTD probe, or a bare-metal payload) — but the interface is specified now
rather than unknown.

**Not established:** the register map and the command codes are settled, but the
*sequence* — how many `SFCSR` writes make one transaction, where the address
bytes go, how the `SPI_RDY` poll is spaced — has been read from B only. Before
any of it is used to **write**, that sequence must be confirmed against A's own
SPI routines at `0x804055ac`–`0x80405d44`, or against C, which drives the same
registers from Linux. Reading is the safe half; writing is not.

### What A says about `FLW`

This unit's loader carries the strings

```
FLW <dst_ROM_offset><src_RAM_addr><length_Byte> <SPI cnt#>: Write offset-data to SPI from RAM
Write 0x%x Bytes to SPI flash#%d, offset 0x%x<0x%x>, from RAM 0x%x to 0x%x
```

— four arguments, matching B's command table entry exactly. **(A and B agree.)**

---

## 3. What the loader does with a corrupt kernel image — R8 precondition 5

**From B**, `bootcode/boot/init/utility.c`:

```c
void doBooting(int flag, unsigned long addr, IMG_HEADER_Tp pheader)
{
	if (flag)
	{
		switch (user_interrupt(WAIT_TIME_USER_INTERRUPT)) {
		case LOCALSTART_MODE:
		default:
			goToLocalStartMode(addr, pheader);
		case DOWN_MODE:
			dprintf("\n---Escape booting by user\n");
			goToDownMode();
			break;
		}
	}/*if image correct*/
	else
	{
		REG32(GIMR_REG) = 0x0;
		goToDownMode();
	}
	return;
}
```

**A bad image does not cost you the rescue path — it takes you there
immediately, without the ESC wait.** `goToDownMode()` is the same destination
pressing ESC reaches. That is the property D4's safety argument depends on.

`goToLocalStartMode()` additionally checks `user_interrupt(0)` *after* copying
the image into SDRAM and *before* jumping, so there is a second escape point.

### How far this is corroborated on **this** unit

| string | in this unit's `stage2.bin`? |
|---|---|
| `---Escape booting by user` | **yes**, file offset `0xafad` |
| `Jump to image start=0x%x...` | **yes**, `0xaf8c` |
| `FLW <dst_ROM_offset>...` | **yes**, `0xb1f0` |
| `no sys signature at %X!` | **no** |
| `sys checksum error at %X!` | **no** |

Both destinations exist in this unit's loader and the escape message is
identical. **The `if (flag) … else goToDownMode()` structure itself is inferred
for this unit, not confirmed** — this generation prints different messages for a
failed image check, so the check exists but has not been located in A.

**What would settle it is a bench test, not a desk one:** point the loader at a
deliberately corrupted image and see whether the `<RealTek>` prompt still
appears. `PROGRESS.md` carries it as C-4. It has to be done before R8, and it
has to be done to the kernel region only — never the loader region.
