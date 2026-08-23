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

**Two independent sources agree** on the first four, which is the bar
`CLAUDE.md` sets:

- **B** names and documents them (`bootcode/boot/flash/spi_common.c`).
- **A** — this unit's own loader — references `0xb8001200` at 2 sites,
  `0xb8001204` at 1, `0xb8001208` at 19, and `0xb800120c` at 14. Its SPI
  routines sit around `0x804055ac`–`0x80405d44`.

`SFDR2` is declared by B and referenced **zero** times by A. Recorded as
*declared by the vendor, unused by this loader* rather than as a fact about the
silicon.

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

**Not established:** the bit layout of `SFCSR` for one command transaction has
been read from B only, and B is a different bootcode generation. Before any of
it is used to *write*, the sequence must be confirmed against A's own SPI
routines at `0x804055ac`–`0x80405d44`, or against C, which drives the same
registers from Linux.

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
