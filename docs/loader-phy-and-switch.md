# The loader's PHY and switch access — what B2 measures, and why

**`RUNSHEET.md` session B2's precondition. Desk work, 2026-08-23. Nothing here
was measured on the device**, except where a line is marked *(measured)* and
names the capture it came from. Every other claim is marked *read out of the
code* or *inferred, pending a measurement*.

Sources are the same five as `docs/loader-command-semantics.md` §0, with the same
weights. **A** = `stage2.bin` out of this unit's own dump
(`sha256 f88869d1…c9c1b4ee`); **B** = vendor bootcode and kernel C, a different
SDK generation; **C** = `upstream/` pinned at `4d3ff26`; **D** =
`refs/RTL8196E-VEx-CG_Datasheet_1.1.pdf`, this part, draft rev 1.1; **E** =
vendor Linux headers.

This file owns **the semantics of the four PHY commands and the register
interface under them**. `RUNSHEET.md` owns the procedure. Nothing is restated
across that line.

---

## 1. The MDIO primitive, and it has three independent sources

`phy_read(phyid, reg, *out)` at **`0x80402F80`** and
`phy_write(phyid, reg, data)` at **`0x80402FF8`**. **(A.)**

```
; phy_read
80402f90   sll   a0,a0,0x18          ; phyid << 24
80402f94   sll   a1,a1,0x10          ; reg   << 16
80402f9c   lui   v0,0xbb80 ; ori 0x4004
80402fa4   sw    a0,0(v0)            ; MDCIOCR = (phyid<<24)|(reg<<16), COMMAND=0
80402fa8   lui   v1,0xb800 ; ori 0x3000
80402fb0   lw    v0,0(v1) ; ori v0,0x100 ; sw v0,0(v1)    ; GIMR |= 1<<8   -- section 2
80402fc0   jal   0x80407cf0 ; li a0,10                     ; delay(10 ms)  -- section 2
80402fd0   lw    v1,0(0xbb804008)    ; MDCIOSR
80402fd8   bltz  v1,0x80402fd0       ; spin while bit 31 set. NO TIMEOUT
80402fdc   andi  v1,v1,0xffff        ; (delay slot)
80402fe0   sw    v1,0(s0)            ; *out = RDATA

; phy_write
80402ff8   sll a0,0x18 ; sll a1,0x10 ; or a0,a1 ; or a0,a2 ; or a0,0x80000000
80403018   sw    a0,0(0xbb804004)    ; COMMAND=1 (write), WRDATA in 15:0
80403024   lw    v0,0(0xbb804008) ; bltz v0,0x80403024
```

| | says | agrees with A? |
|---|---|---|
| **A** | the two blocks above | — |
| **D**, Tables 57–59 | `0xBB80_4004` `MDCIOCR`: bit 31 `COMMAND` (0 read / 1 write), `PHYADD[4:0]` at 28:24, `REGADD[4:0]` at 20:16, `WRDATA[15:0]` at 15:0. `0xBB80_4008` `MDCIOSR`: bit 31 `STATUS` (1 = in process), `RDATA[15:0]` at 15:0. **Table 57 lists only these two registers in the `0xBB80_4000` block** | field for field |
| **B**, `rtl8196x/asicregs.h` | `MDCIOCR (0x004+SWMACCR_BASE)`, `MDCIOSR (0x008+…)`, `COMMAND_MASK (1<<31)`, `PHYADD_OFFSET 24`, `REGADD_OFFSET 16`, `WRDATA_MASK (0xffff<<0)`, `STATUS (1<<31)`, `RDATA_MASK (0xffff<<0)` | field for field |
| **B**, `rtl865x_asicL2.c:5552` `rtl8651_getAsicEthernetPHYReg()` | `WRITE_MEM32(MDCIOCR, COMMAND_READ \| (phyId<<PHYADD_OFFSET) \| (regId<<REGADD_OFFSET)); do { status = READ_MEM32(MDCIOSR); } while ((status & MDC_STATUS) != 0); status &= 0xffff;` | statement for instruction |

**Three sources, and the strongest one is D — it is this part, not a relative.**
`docs/loader-flash-write.md` got the SPI controller on two; this is on three.

### The `delay(10)` is an erratum workaround, and A applies it unconditionally

**B** guards the same delay:

```c
#elif defined(CONFIG_RTL8196C_REVISION_B)
    if (REG32(REVR) == RTL8196C_REVISION_A)
        mdelay(10);  //wei add, for 8196C revision A. mdio data read will delay 1 mdc clock.
```

**A has no revision test.** It delays 10 ms on every MDIO read, whether or not
this silicon needs it. That is the whole cost of `MDIOR`: 32 reads × 10 ms.

**The two vendor kernel trees do not agree with each other about ordering, and A
follows one of them.** `rtl819x-toolchain`'s `rtl865x_asicL2.c:5556` writes
`MDCIOCR` first and waits afterwards — that is A. `saturn49-wecb` and
`wecb-vz-gpl` at `:5541` take a spinlock and wait for `STATUS` to clear
*before* issuing. So a second `PHYR` on this loader relies on the first having
left `STATUS` clear, which it did, because it spun until it was — but there is
no lock and no pre-check, and the SDK's own later trees added both.

---

## 2. A "PHY read" is not read-only, and its delay has four preconditions

`phy_read()` writes two registers: `MDCIOCR`, and **`GIMR |= 1<<8`**. **(A.)**
**B** names bit 8 `TCIE` — Timer/Counter interrupt enable — and **D** agrees
(`TC_IE`, bit 8 of the Global Interrupt Mask Register at `0xB800_3000`).

That line is there because of this chain, all of it **(A)**:

```
80408f20  timer_init(200000000):  TCCNR=0 ; CDBR=0x000E0000 ; TC0DATA=142858<<4 ;
                                  TCCNR=0xC0000000 ; IRR1=0x00050004 ; TCIR=0x80000000
80408ee0  timer ISR:              ack TCIR ; (*(uint32*)0x8040DCE8)++
80408f10  tick():                 return *(uint32*)0x8040DCE8
80407cf0  delay(ms):              t0=tick(); while (tick()-t0 < ms/10) ;
```

**`0x8040DCE8` has exactly one writer — the ISR at `0x80408F04`.** So `delay()`
returns only if a timer interrupt can be taken, and that needs four things to be
true at once:

| # | layer | where it is set **(A)** | state at the `<RealTek>` prompt |
|---|---|---|---|
| 1 | `Status.IM[7:2]` unmasked, `BEV` cleared | `0x80406694`, called from `0x80408634` | set on the boot path, **never re-masked** |
| 2 | `Status.IE = 1` | `0x8040865C`, and again at `0x80408494` immediately after `---Ethernet init Okay!` | set |
| 3 | `TCCNR`/`TCIR` armed | `timer_init` at `0x80408F20`, reached via `0x80406780` | armed |
| 4 | `GIMR` bit 8 | **`doBooting()` writes `GIMR = 0` at `0x804086E4` and `0x80408700`, on both of its paths** | **cleared** |

Layer 4 is the one `phy_read` repairs itself. That is not a guess about intent:
the loader's own network init runs *after* `GIMR = 0`, so any `phy_read` on that
path would hang without it.

**Refutation, and it is B2's first cell:** if `0x8040DCE8` does not advance
between two `DW`s taken ten seconds apart, one of the four layers is not what
this table says, `delay(10)` will not return, and **no PHY command may be sent
that session** — the board would hang in the delay, not in the MDIO poll.
Nothing else in B2 is worth a power cycle if that cell fails.

### The number this hands `C-8`

`timer_init`'s argument is the compiled-in constant at `0x8040DBA0`, and it reads
**`0x0BEBC200` = 200,000,000** in the image. With `CDBR` divisor 14 and
`TC0DATA = 142858`, the tick is

```
200e6 / 14 / 142858 = 100.0 Hz          (inferred, pending a measurement)
```

and `delay(10)` is one tick = 10 ms, which is exactly `mdelay(10)` in **B**.
`C-8` currently records the watchdog's wall-clock timeout as *not established*
because "the bus clock `CDBR` divides is unmeasured". **Two `DW`s and a stopwatch
measure it**: if the tick advances at 100 counts per second, the base clock is
200 MHz on silicon and `C-8` gets its missing input. If it advances at some other
rate, the 200 MHz constant is a compile-time belief and not this board's clock —
which is worth more than the number.

---

## 3. Four console commands, three argument conventions, and one wrong help string

All **(A)**, decoded instruction by instruction; `argv` slots cross-checked
against `upstream/tools/loader-unpack.py --commands`, whose branch-walking reader
was run again in this repo and agreed.

| | handler | argc check | argv[0] | argv[1] | argv[2] | what it does | prints |
|---|---|---|---|---|---|---|---|
| **`MDIOR`** | `0x80409C54` | **`bgtz a0`** → else `Parameters not enough!` | **register, base 10** | — | — | **loops `phyid` 0…31**, one `phy_read` each | `PhyID=0x%02x Reg=%02d Data =0x%04x` |
| **`MDIOW`** | `0x80409CE8` | **`slti a0,3`** → needs at least 3 | phyid, base 16 | **register, base 10** | data, base 16 | one `phy_write` | `Write PhyID=0x%x Reg=%02d data=0x%x` |
| **`PHYR`** | `0x80409D98` | **none** | phyid, base 16 | register, **base 16** | — | one `phy_read` | `PHYID=0x%x, regID=0x%x ,Find PHY Chip! UID=0x%x` |
| **`PHYW`** | `0x80409E10` | **none** | phyid, base 16 | register, **base 16** | data, base 16 | `phy_write` **then `phy_read` back** | `PHYID=0x%x ,regID=0x%x, Find PHY Chip! UID=0x%x` |

Three things follow, and each of them would produce a wrong answer rather than an
error message.

**The help string in the command table is wrong for `MDIOR`.** The table row says
`MDIOR:  MDIOR <phyid> <reg>`; the handler reads `argv[0]` only, parses it base
10, and uses it as the *register*, sweeping the PHY address itself. So
`MDIOR 0 2` is accepted, ignores the `2`, and sweeps **register 0**. Nothing in
the 32 lines of output says so. The format string is a second witness for the
radix: `Reg=%02d` is printed decimal while `PhyID` and `Data` are printed hex.

**The two `MDIO*` commands parse the register decimal; the two `PHY*` commands
parse it hex.** For registers 0–9 they agree. For register 10 and above they do
not, and MII's vendor space starts at 16 — `PHYR n 10` reads register 16 while
`MDIOR 10` reads register 10.

**`PHYR` and `PHYW` never read `argc`.** A bare `PHYR` reaches
`strtoul(NULL, …, 16)`; the tokeniser zeroes all twenty pointer slots each line,
so that is a null dereference. **B** corroborates: `CmdPHYregR` in
`bootcode/boot/monitor/monitor.c` takes `(int argc, char *argv[])` and never
looks at `argc` either, and its two `strtoul` calls are base 16. Same command
row, same help string, same two format strings including which side of `regID`
the comma falls on — **that is how the two `Find PHY Chip!` strings in this image
are told apart: `0x8040B5B8` is `PHYR`'s, `0x8040B5EC` is `PHYW`'s readback.**

### `MDIOR` and `MDIOW` have exactly one source

They are **not** in **B**'s `monitor.c`. The only `MDIOR` in any vendor tree here
is in `bootcode/boot/monitor/test_slvpcie.c`:

```c
{ "MDIOR", 1, SlvPCIe_MDIORead,  "MDIOR: Reg Read"},
{ "MDIOW", 1, SlvPCIe_MDIOWrite, "MDIOW <reg> <val>:  "},
```

— **a PCIe slave-port command that happens to share the name.** Reading **B** to
predict what this unit's `MDIOR` does would have produced a confident wrong
answer. Everything in the `MDIOR`/`MDIOW` rows above rests on **A** alone, and
`RUNSHEET.md` B2 says so in the cells that use them.

---

## 4. `PORT1` writes PHY registers, takes no arguments, and is one keystroke away

`PORT1` at **`0x8040A294`** is a three-instruction wrapper around **`0x8040A0A0`**.
It reads no `argv` and no `argc`. **(A.)** What `0x8040A0A0` does:

```
copy 17 words from 0x8040B84C onto the stack        ; the payload table
read 4 bytes at 0x8040B890                          ; the target PHY addresses
for s4 in 0..16:
    for s6 in 0..3:
        phy = byte[s6]
        phy_write(4,   31, 1)          ; page select on PHY 4
        phy_write(4,   20, 0xB20 | (1<<phy))
        phy_read (4,   20, &scratch)
        phy_write(phy, 31, 1)          ; page select on the target
        for s1 in 0..s4:
            phy_write(phy, 19, table[s1])
            printf("i=%d phyid=%d gray_code=%x\n", s4, phy, table[s1])
        phy_write(phy, 31, 0)          ; page back
    busy_delay(10000)
phy_write(4, 31, 1); phy_write(4, 20, 0xB20); phy_write(4, 31, 0)
```

The table at `0x8040B84C` is `5400 5440 54C0 5480 5580 55C0 5540 5500 5700 5740
57C0 5780 5680 56C0 5640 5600 5400`, and the loader's own message calls it
`gray_code`. The four bytes at `0x8040B890` are **`00 02 03 04`**. The help string
is `PORT1: port 1 patch for FT2`.

So: **a factory-test routine that walks a Gray-code pattern through PHY vendor
register 19 on four PHYs, with page select at register 31 and no way to stop
it.** The inner loop writes `table[0…s4]` each round, so the payload alone is
`4 × Σ(s4+1) for s4 = 0…16` = **612 writes to register 19**, plus 272 page-select
and control writes around them. **B** corroborates the page-select idiom —
`CmdGPHYW` in `monitor.c` writes register 31 before and after touching a paged
register — but `PORT1` itself is **A**-only, like `MDIOR`.

Two things it hands B2 for free. **This unit's own loader names PHY addresses
`{0, 2, 3, 4}` as PHYs** — and skips 1, which is a prediction B2 can test. And
PHY address 4 is used as the control for register 20 while the others are
targets, which says 4 is not merely another port.

**`PORT1` goes on `RUNSHEET.md`'s do-not-type list.** It was not on it before,
because that list was written from the four memory-write paths, and `PORT1`
writes neither memory nor flash.

---

## 5. The instrument gap: `console-dump.py` has no notion of a register write

```python
FORBIDDEN = ("FLW", "EB", "EW", "AUTOBURN", "LOADADDR", "J ")
```

`PHYW`, `MDIOW` and `PORT1` are not in it. The tool that refuses to send `EW`
because *"EW writes to the device. This tool only reads"* will send `PORT1`
without comment.

That is not a bug in the refusal — it is a refusal built from a model of "write"
that is flash and memory. It is recorded here rather than patched: `upstream/` is
pinned read-only at `4d3ff26`, and that pin is what `R9`'s differential proof
rests on. **B2's driving section carries the gap instead**, which is the same
answer this repo already gave for the `--at-prompt` trap.

---

## 6. Which PHY addresses exist, and what can be predicted before the visit

| source | says | weight |
|---|---|---|
| **D**, Table 64 bits 30:26 | `ExtPHYID[4:0]`, *"Identifies the external PHY ID for MDC/MDIO polling addressing. Only valid for ports 0~4"*, **default Port0~4 = 0x0~4** | this part |
| **A**, `PORT1`'s table at `0x8040B890` | `{0, 2, 3, 4}` | this unit |
| **C**, `upstream/dumps/uart-boot.log` *(measured)* | `eth1 … Member port 0x1` (vid 8), `eth4 … 0x2`, `eth3 … 0x4`, `eth2 … 0x8`, `eth0 … 0x10` — **five ports, 0–4, and port 0 carries vid 8 while the other four carry vid 9** | this unit, on silicon |

**Prediction, written before the measurement:** PHY addresses 0–4 answer; 5–31 do
not, and read back whatever this MDIO controller returns for an unanswered
address. **Refutation:** all 32 addresses returning the same plausible value
means the bus is echoing and nothing was measured; a sixth address answering
means the port map above is incomplete.

**The PHY identifier itself cannot be predicted.** It was looked for and is not
there: **D** documents no PHY MII register map at all (its §11 is `0x4000`,
`0x4100` and `0x4300`, nothing else); **B**'s only PHY-ID constant is
`0x001CC912`, which its own comment calls *"8212 two giga port"* — an external
gigabit part, not this die; **B**'s factory routine at `monitor.c:2337` compares
registers 2 and 3 against values passed in on the command line, not constants;
and **no console capture in `upstream/dumps/` contains `Find PHY Chip!`**,
because section 3 shows those two strings are printed only by `PHYR` and `PHYW`,
and neither has ever been typed on this device.

So the identifier cell carries structural expectations instead, and B2 says so in
the cell rather than pretending otherwise:

- it must be neither `0x0000` nor `0xFFFF` on addresses 0–4;
- **it must be identical on 0, 2, 3 and 4** — `PORT1` patches all four from one
  table, which is **A**'s own evidence that they are one macro;
- **address 1 is the open question.** Same value → `PORT1`'s skip is about the
  port; different value or no answer → it is about the PHY.

---

## 7. The switch registers this loader touches, and where each one is documented

Every `lui …,0xbb80` in the image was resolved to its following `ori` or
displacement — 48 sites, 13 distinct addresses, **all in `0xBB804xxx`**. **(A.)**

| address | **B** calls it | in **D**? | loader's use **(A)** |
|---|---|---|---|
| `0xBB804000` | `MACCR` | Table 57 lists the block, not this offset | `\|= 0x1000` once |
| `0xBB804004` | `MDCIOCR` | **Table 58** | section 1 |
| `0xBB804008` | `MDCIOSR` | **Table 59** | section 1 |
| `0xBB804100` | `PITCR` | **Table 63** | `\|= 0x1`, twice |
| `0xBB804104` | `PCRP0` | **Table 64** | read-modify-write, 5 sites |
| `0xBB80414C` | `P0GMIICR` | **absent** | 5 sites |
| `0xBB804234` | **absent** | **absent** | 1 site — **undetermined** |
| `0xBB804418` | `SWTCR0` | absent | 8 sites |
| `0xBB804428` | `FFCR` | absent | 1 site |
| `0xBB804A08` | `PVCR0` | absent | 1 site |
| `0xBB804D00` | `SWTACR` | absent | 6 sites |
| `0xBB804D08` | `SWTAA` | absent | 1 site |
| `0xBB804D3C` | `TCR7` | absent | 1 site |

Four addresses have two documentary sources plus A's behaviour. Eight have one,
and that one is a different generation. **One has none.** R6 inherits that list
as it stands; nothing here is promoted by being adjacent to something documented.

**`0xBB802000` is not in this table, and that matters.** **B**'s `asicregs.h`
defines `PHY_BASE (SWCORE_BASE + 0x00002000)` with a memory-mapped shadow of MII
registers 0–5 for each of seven ports — `PORT0_PHY_IDENTIFIER_1` at `0xBB802008`
and so on. It looked like a second instrument for the PHY identifier that does
not use MDIO at all. It is not usable here: **D**'s §11 has no such block on this
part, and **this unit's loader never issues an address in `0xBB802xxx`**.
Single-source, and the source is the wrong generation. It is not a B2 cell.

### `PITCR` bit 0, and the draft datasheet is wrong about it

The loader does `PITCR |= 1` at `0x8040371C` and `0x80403904`. **D**'s Table 63
gives `Port0_TypeCfg[1:0]` at bits 1:0 with `00: UTP (10/100M embedded PHY)`,
**`01: Reserved`**, `1x: Reserved`.

`upstream/dumps/uart-bootloader.log` *(measured)*, the line above
`---Ethernet init Okay!`:

```
P0phymode=01, embedded phy
```

**The loader prints a name for a value the datasheet calls Reserved.** The
datasheet is a draft (`Rev. D1.1`, watermarked); the silicon's own boot loader
disagrees with it. Recorded, not resolved — what B2 confirms is only that `PITCR`
reads `0x00000001` on this board.

### `PCRP0` is configured; `PCRP1`–`PCRP4` are not

The only per-port configuration register the loader writes is `PCRP0`. **(A.)**
It sets `EnForceMode`, `ForceLink` and a forced speed/duplex —
`(PCRP0 & 0xFF83FFFF) | 0x028C0000` on one branch and `| 0x02940000` on another,
selected by a strap read from `0xB800000C & 0xF` compared against 13.

**No loop over `PCRP1`…`PCRP4` exists in the image.** So those four should still
hold reset defaults, and **D** Table 64 makes bits 30:26 predictable: `ExtPHYID`
= 1, 2, 3, 4. That is a read of the PHY-address assignment **that does not go
through MDIO**, and it is the cross-check B2 uses on the sweep.

`PSRP0`…`PSRP4` at `0xBB804128`–`0xBB804138` (**D** Table 62, and **B** agrees at
`PCRAM_BASE + 0x28`) give link state per port without MDIO. **B** names the bits:
8 `LinkDownEventFlag` (latched, **read to clear**), 7 NWayEnable, 6 RxPause,
5 TxPause, **4 LinkUp**, 3 Duplex, 1:0 speed (`00` = 10M, `01` = 100M). **D**
Table 65 confirms bit 8 and the 7:0 field, and leaves 7:0's interior to B.

One divergence, recorded: **B** defines `PSRP5` at `PCRAM_BASE + 0x3C`; **D**'s
Table 62 skips `0x3C` and resumes at `0x40` with `PSRP6`. D is this part.

---

## 8. What the bench has to confirm, and what would refute it

The procedure is `RUNSHEET.md` session B2. This is the prediction list.

| # | prediction, from the code | what refutes it | risk |
|---|---|---|---|
| **1** | `0x8040DCE8` advances at **100 counts per second** | no advance → the timer ISR is not running and **no PHY command may be sent**. A different rate → the 200 MHz constant at `0x8040DBA0` is not this board's clock | read-only |
| **2** | `GIMR` bit 8 reads **0** at the prompt and **1** after the first `PHYR` | already 1 → something between `doBooting` and the prompt sets it, and section 2's chain is incomplete. Stays 0 → `phy_read` is not the function at `0x80402F80` | writes one bit of `GIMR` |
| **3** | `PITCR` reads `0x00000001` | anything else → section 7 misreads the two `\|= 1` sites | read-only |
| **4** | `PCRP1`…`PCRP4` bits 30:26 read **1, 2, 3, 4** | different values → the loader configures them somewhere the address scan missed | read-only |
| **5** | exactly one `PSRP` has bit 4 set, and it is the port the cable is in | more than one, or none → the register is not port-indexed the way Table 62 says | read-only |
| **6** | moving the cable moves that bit, and latches bit 8 on the port it left | the bit does not follow the cable → the read is of something cached, not of the switch | read-only |
| **7** | `PHYR 0 2` returns a value that is neither `0x0000` nor `0xFFFF`, and `PHYR 2 2`, `PHYR 3 2`, `PHYR 4 2` return the same one | they differ → the four are not one PHY macro, and `PORT1` patching them from one table is wrong, or they are not what it patches | writes `MDCIOCR` |
| **8** | `PHYR 1 2` returns that same value | different, or no answer → `PORT1`'s skip of address 1 is about the PHY and not the port | as 7 |
| **9** | `PHYR 5 2` **returns**, with `0xFFFF` or `0x0000` | it does not return → the `MDCIOSR` spin has no timeout and no escape on an unanswered address. **`MDIOR` must then never be run on this part** | 🔴 **costs a power cycle if it is wrong.** Last cell of the session |
| **10** | `MDIOR 2` prints 32 lines; 0–4 match cells 7–8, 5–31 match cell 9 | all 32 identical and plausible → the bus is echoing and nothing was measured | as 9, times 27 |

**Not settled by any of these, and it must not be inferred from them:** what the
PHY identifier *is*. No source predicts it, so the first reading of it has no
control except its own internal agreement across four addresses. It is a
measurement, not a confirmation, and B2's results table says so.
