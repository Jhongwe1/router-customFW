# The loader's PHY and switch access — what B2 measures, and why

**`RUNSHEET.md` session B2's precondition. Desk work, 2026-08-23. Nothing here
was measured on the device**, except where a line is marked *(measured)* and
names the capture it came from. Every other claim is marked *read out of the
code* or *inferred, pending a measurement*.

**Amended after the bench, 2026-08-23 and 2026-08-24.** Results from both
seatings are folded in where they bear on a claim, each marked 🔴 and naming the
capture it was read from. Superseded claims stay where they were, with the reason
they fell and the cell that killed them.

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
| 4 | `GIMR` bit 8 | **`doBooting()` writes `GIMR = 0` at `0x804086E4` and `0x80408700`, on both of its paths** | 🔴 **measured 2026-08-23: `GIMR` reads `0x00008100` at the prompt — bit 8 is already `1`, and bit 15 (`SWIE`) with it.** `doBooting()`'s zero is not the last write before the prompt; something in the network init or the command-loop entry re-enables both. **This row said "cleared" and it is wrong.** It makes the position safer rather than less safe, and it voids `RUNSHEET.md` `E5`, whose whole design was a bit predicted to flip |

🔴 **2026-09-04 (`R5-10`): this table is correct for the LOADER and for
TC0, and it is neither complete nor right for anything under Linux.** Three
things it cannot say, all 讀 from `arch/rlx`: the SoC has **three** interrupt
domains and the middle one — LOPI, which the vendor's own system tick uses —
is masked in **`ESTATUS[23:16]`**, a different register file reached by
`mflxc0`/`mtlxc0`, not in `Status.IM`; layer 3 folds two independent bits
together, because `TCIR` carries the interrupt **enable** as well as the
pending flag and for TC1 the counter enable (`TCCNR` bit 29) and the
interrupt enable (`TCIR` bit 30) are separate; and TC1 does not use bit 8 —
it is `GIMR` bit 9, routed through `IRR1` and cascaded on CPU `IP2`.

🟢 **2026-09-04, seating 12: all three clauses of that last sentence are
now 量.** `GIMR` bit 9 moved `00209100` → `00209300` on `request_irq` and back
on `free_irq`, three times each; `IRR1` read `C222FA2D` under Linux with
`irr1_tc1_rs = 2` (`BSP_IRQ_CASCADE`); and `Status.IM2` read 1
(`status = 10000401`). It was written here as an inference from source and it
came out exactly. `SPEC.md` `IRQ-08`, `docs/interrupt-map.md` § 3.1.
**The seven-layer version is `docs/interrupt-map.md` § 3.1**, and `SPEC.md`
`IRQ-04` carries the same correction. This table stays because it is what
the loader does and the loader is what `B2` runs against.

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
200e6 / 14 / 142858 = 100.0 Hz          (predicted, before the visit)
```

and `delay(10)` is one tick = 10 ms, which is exactly `mdelay(10)` in **B**.

🔴 **Measured on the device, 2026-08-23** (`RUNSHEET.md` `E2`, `E2b`).
**The rate in this table is superseded; it stays here with the reason it fell:**

| | |
|---|---|
| `0x8040DCE8` | `0x0000473A` → `0x00005F52` = **6,168 counts** |
| elapsed | **61.842 s**, from timestamps taken either side of each read |
| **tick** | **99.74 Hz**, against 100.0 Hz predicted — **0.26 %** |
| `CDBR` (`0xB8003118`) | `0x000E0000`, read on the device |
| `TC0DATA` (`0xB8003100`) | `0x0022E0A0` = 142,858 << 4, read on the device |
| ⇒ base clock | 99.74 × 14 × 142,858 = **199.48 MHz** |

**Three of the four terms are read on silicon**, so this is a derivation and not
a coincidence, and it settles the divisor field's semantics without a second
experiment — a divisor of 15 would put the base at 213.7 MHz, which is not a clock
anyone builds. `CDBR` and `TC0DATA` still stand as read. **The rate does not.**

🔴 **Superseded 2026-08-24, and the cause is the instrument, not the board.**
That 61.842 s was **hand-timed**. A human reading a clock is good to about
±0.15 s, which over 61.842 s is **±0.25 %** — the size of the deviation the row
above reports as a property of this board. **The 0.26 % was the stopwatch.**

**Measured on the device, 2026-08-24**, four reads of `DW 8040DCE8 1` with the
interval taken from each capture's `.log` mtime instead of from a hand-held clock
(`bench/2026-08-24b/`, cells `E1b`, `E2b`, `CONT2`, `CONT3`; one boot throughout).
Ticks and mtimes: **252,061** at 04:14:52.116 · **277,390** at 04:19:05.387 ·
**428,675** at 04:44:18.209 · **485,370** at 04:53:45.148.

| baseline | seconds | f (Hz) | base (MHz) | ppm vs 200.000 |
|---|---|---|---|---|
| `E1b`→`E2b` | 253.270 | 100.0078 | 200.0168 | +84.1 |
| `E1b`→`CONT2` | 1766.093 | 100.0027 | 200.0066 | +32.9 |
| `E1b`→`CONT3` | 2333.032 | 100.0025 | 200.0062 | +30.8 |
| **`E2b`→`CONT2`** | 1512.822 | **100.0018** | **200.0049** | **+24.3** |
| **`E2b`→`CONT3`** | 2079.762 | **100.0018** | **200.0049** | **+24.3** |
| **`CONT2`→`CONT3`** | 566.940 | **100.0018** | **200.0049** | **+24.4** |

**Every baseline that excludes `E1b` returns `100.0018 Hz` to five significant
figures** — three of them, over 567 s, 1513 s and 2080 s, and `CONT2`→`CONT3`
shares no endpoint with `E2b`→`CONT2`. **The residual on the other three has one
name**: `E1b`'s mtime sits ≈15 ms away from the instant its tick was sampled,
which is the CP2102 latency-timer scale (1–16 ms). Fifteen milliseconds over
253 s *is* +59 ppm, so the top row is an artefact of the capture that shrinks as
the baseline grows, and it is why the 253-second fit reads +84 ppm.

Base = f × `CDBR`(14) × `TC0DATA`(142,858), the last two read on the device in
seating 1 and unchanged.

> 🔴 **RENAMED 2026-08-26 — this is the *peripheral Lexra bus* clock, i.e. the divider INPUT.** The datasheet's own § 8.2.8 defines *"Base clock = System_clock (Peripheral Lexra Bus)/N"*, so *base clock* is the divider **output**, which is `CLK-17`'s 14.286057 MHz. Calling this one the timer base clock inverts a factor of 14 for the next reader.
>
> **Peripheral Lexra Bus clock = 200.0049 MHz ± 0.0015 MHz** (±7 ppm at a 2080-second
> baseline); **tick = 100.0018 Hz**. The compiled-in `0x0BEBC200` = 200,000,000
> at `0x8040DBA0` is **right to +24 ppm**, inside a normal crystal's tolerance.

**Refutation:** a pair of reads on a later boot implying an `f` more than
±0.0002 Hz from 100.0018 would make the agreement above a property of one boot
rather than of the crystal. A `.log` mtime that is *not* the moment the last byte
landed would void the method entirely — that is the assumption the whole
measurement rests on, and it is checked against the `.timing` files.

🔴 **The counter starts at ≈0 at boot, which dates `timer_init` on the wall
clock.** *(measured, same four captures.)* Extrapolating `CONT3` back at
`f = 100.0018` puts tick 0 at **03:32:51.54**; the first UART byte of that boot
was at **03:32:50.13**. So **`timer_init` at `0x80408F20` runs 1.41 s into the
boot** — after the banner (+0.585 s) and before the Ethernet/PHY init
(+2.246 s), so layer 3 of the table above is armed before the network init runs
rather than after it. Two derivations agree: a single read divided by elapsed,
and the differential above.
**Refutation:** a non-zero start would make the extrapolated zero point land
*before* the first UART byte, or after the prompt.

**What this does *not* settle, and it must not be read as settling it:** whether
the watchdog counts the same `CDBR`-divided clock. If it does, `OVSEL[3:0]=0000`
= 2¹⁵ ticks = **2.29 ms**; if it counts the undivided base it is 164 µs. (Both
recomputed on 200.0049 MHz; neither moves at this precision.) `C-8`
needs `D1`'s wall-clock delay to choose between them, and `D1` has not run.

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
        phy_write(4,   20, 0xB20 + (1<<phy))   ; ADD, not OR -- see below
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
PHY address 4 hosts the register-20 control for every target — 🔄 **and the
narrower true statement, 2026-09-14: 4 is ALSO a target.** The four bytes at
`0x8040B890` are `{0, 2, 3, 4}`, so PHY 4 receives the same page-select and
register-19 writes as the other three. What is asymmetric is that PHY 4 **hosts a
global control register** the others do not — **B** confirms it by addressing
register 20 at PHY 4 even when its own `port` argument is 4. *(This sentence read
"PHY address 4 is used as the control for register 20 while the others are
targets, which says 4 is not merely another port" until then; the second half was
half right and the first half was wrong.)*

### Why address 1 is skipped, and the explanation that was killed at the bench

`E8` settled the half of this that could be settled by MDIO: address 1 answers
like the other four, so **the skip is about the port, not about the PHY**
(`SPEC.md` `NET-07`). What it does not give is a reason.

🔴 **One reason was proposed during seating 2 and is refuted.** The proposal was
**"port 1 has no jack, so there is nothing to patch"**. It is wrong.
*(Measured 2026-08-24, `bench/2026-08-24b/E11e.log`.)* With the cable in the
fifth RJ45 counted from the WAN side, `PSRP1` read `0x000010F9` — bit 4
`LinkUp` set, and the only port so set on that read. **Port 1 has a jack**;
section 7 carries the whole map. The proposal rested on a jack count that was
*reported at the bench, not measured*, and `E11e`'s refutation condition named
this outcome before the cable was moved. It stays here with what killed it: the
next explanation offered for the skip has to survive the same test.

**The remaining candidate is the help string, read literally.**
`PORT1: port 1 patch for FT2` parses as *a patch **for** port 1* — applied to
the other four ports so that port 1 can be exercised on its own in factory test
2. That is exactly the set the routine touches: the four bytes at `0x8040B890`
are `{0, 2, 3, 4}`, port 1 absent, and the control writes go to PHY 4 rather than
to the port being tested. *Inferred, pending a measurement.*

**Refutation path: read what the routine writes.** The pseudocode above is the
artefact and it is already decoded; what is missing is the *meaning* of the two
payloads — page-1 vendor register 19 (the 17-word Gray-code table at
`0x8040B84C`) and `0xB20 + (1<<phy)` written to register 20 on PHY 4, where the
`1<<phy` shift is the only place a per-port selection appears. If that pair turns
out to configure each target port for its own sake rather than to hold the other
four out of the way, this reading falls and `NET-07`'s reason is open again. **No
source held here documents either register**, so this is desk work against **A**
alone, and it cannot be done by running the command: `PORT1` takes no arguments
and cannot be stopped.

### 🔴 The reading above FELL, 2026-09-14 — desk, zero power

**Instrument**: `/usr/bin/mips-linux-gnu-objdump` 2.42, a distribution binary
and not a vendor one, so no `vendor-tripwire.sh` was required; it was run
anyway and reported `CLEAN  6 tree(s) watched, 0 lines` before and after. The
artefact hashes to the value `docs/loader-command-semantics.md` records, and
that file's own control fires — `ComSrlCmd_RDID` reappears at
`0x8040591C`-`0x80405970`. Every load-bearing instruction below was also
re-decoded from the raw file bytes by a second implementation sharing no code
with objdump. Everything here is **讀**; the device readings it cites
(`E11e`, `E9b`) are **量**.

**① Structure, from A alone.** `0x8040A188` is `sllv a2,a2,s2`: it sets
**exactly one** bit, and that bit is the same `s2` that receives the
register-19 writes three instructions later at `0x8040A1D4`. Holding the other
four out of the way would be one four-bit mask written once; this is one bit
per target, cleared between targets, and the exit write at `0x8040A250` is
`0xB20` with **no** port bit — the "none selected" state a selector has
and a mask does not. And the Gray payload is **identical for every phy**, so
the four are not being configured differently from one another.

**② The vendor's own source.** ⚠️ **This is B, and B is a
DIFFERENT GENERATION** — `CONFIG_RTL8196C_REVISION_B`, where this part is
RTL8196E. It explains why the constant is what it is; it is never a substitute
for A. What makes it load-bearing here is that A's compiled form matches it in
register triple, constant and ordering. `swCore.c:938 (set_gray_code_by_port)`,
identical in both bootcode drops and reproduced at
`rtl865x_asicL2.c:1274 (set_gray_code_by_port)`:

```c
void set_gray_code_by_port(int port) {
       uint32 val;
       rtl8651_setAsicEthernetPHYReg( 4, 31, 1 );
       rtl8651_getAsicEthernetPHYReg( 4, 20, &val );
       rtl8651_setAsicEthernetPHYReg( 4, 20, val + (0x1 << port) );
       rtl8651_setAsicEthernetPHYReg( port, 31, 1 );
       rtl8651_setAsicEthernetPHYReg( port, 19,  0x5400 );
       if (port<4) rtl8651_setAsicEthernetPHYReg( port, 19,  0x5440 );
       if (port<3) rtl8651_setAsicEthernetPHYReg( port, 19,  0x54c0 );
       if (port<2) rtl8651_setAsicEthernetPHYReg( port, 19,  0x5480 );
       if (port<1) rtl8651_setAsicEthernetPHYReg( port, 19,  0x5580 );
       rtl8651_setAsicEthernetPHYReg( 4, 20, 0xb20 );
       rtl8651_setAsicEthernetPHYReg( port, 31, 0 );
       rtl8651_setAsicEthernetPHYReg( 4, 31, 0 );
}
```

The function is named for the port it takes; `0x1 << port` names the same port
that then receives the register-19 writes; and both callers —
`swCore.c:1000 (set_gray_code_by_port)` and
`rtl865x_asicL2.c:1413 (set_gray_code_by_port)` — are `for i=0; i<5; i++`,
**including port 1**. Its runtime caller
`rtl_nic.c:3198 (re865x_setPhyGrayCode)` applies it to the port that has just
gone link-down, under `CONFIG_RTL8196C_ETH_IOT`.

⇒ **`1<<phy` selects the port being patched. It does not mask the others
off.** The four listed ports are the subjects of the patch, not bystanders
being parked, so the candidate reading falls and `NET-07`'s reason is open
again — on much narrower ground.

**The instruction is `addiu`, not `or`, and the distinction is load-bearing.**
`0x8040A198` is `addiu a2,a2,2848`. Here it is equivalent, because `0xB20`'s
bits 4:0 are all clear so `+` is `|` for phy 0-4 — but the vendor's form
composes on a value it has **just read back** (`val + (0x1 << port)`), and
writing it as an OR hides that. `SPEC.md` `NET-07` said 「或上」
and now says 「加上」.

**Register 19 on page 1 now has a NAME, and it is the vendor's own.**
`rtl865x_asicL2.c:4114 (finetune 100M DAC current)` is a comment table giving
page 1, address 19, default `0x4400`, programmed value `0x5400`, purpose
*finetune 100M DAC current*; the surrounding block adds *Port#0~#4 (per port
control), Page1,Reg19,bit[13:11]* and programs bits 13:11 to 2. Arithmetic:
`0x5400` has bits 13:11 = 2, which is exactly that. So **the Gray field is bits
9:6 and it rides on top of the vendor's correct DAC-current constant** — a
different field in the same register. ⚠️ **Bits 9:6 themselves are
still unnamed**: they read 0 in both `0x4400` and `0x5400`, and no source held
says what they do. Undetermined; what closes it is D's page-1 register map or
an 8196E-generation SDK header with the page-1 reg-19 bit fields.

**The routine is SELF-RESTORING.** The last outer round (i = 16) ends the inner
walk on `table[16]` = `0x5400`, which is the vendor's documented programmed
value; the epilogue returns register 20 to `0xB20` with no port bit and both
pages to 0. So `PORT1` leaves all four PHYs at the setting the vendor's own
patch would have left them at — which is worth knowing before it is typed,
even though it stays on the do-not-type list for the reasons above.

**There is no skip in the code, and that reframes the question.** The middle
loop bound is `sltiu v0,s6,4` at `0x8040A214`, so the routine walks a
**four-entry byte table**; the PHY address is `lbu s2,72(v0)`, pure data. A
scan of every word in `0x8040A0A0`-`0x8040A290` for a branch or compare
touching `s2`, or any compare against immediate 1, returns **0 hits** —
and the control fired, because the same scanner counts **7** branches and
compares in the routine, so it was capable of reporting. The routine never
compares a PHY address against anything; it cannot skip 1, it was never given
1. 量: `0x8040B890` is referenced twice in the whole image and
`0x8040B84C` once, all three inside `PORT1`, so neither is a loader-wide list.

⚠️ **What is still open, and it is narrower**: why this loader's
private four-byte table omits 1 when the vendor's loop does not. **The
discriminating experiment costs no power**: read the same table out of a second
RTL8196E loader from a different board. A five-LAN board carrying
`00 01 02 03 04` against this four-LAN board's `00 02 03 04` makes it board
configuration and nothing to do with port 1; both omitting 1 makes it about
port 1. Failing that, the FT2 test procedure, or the bootcode source this
loader was built from.

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

🔴 **The count of 13 is a floor, and the reason is the census's own
form — 2026-09-14 (desk).** A function does one `lui` into a base
register and then many `ori`s off it, so pairing each `lui` with its
FOLLOWING `ori` sees one offset per function. A census of `ori rX,rY,0x4xxx`
immediates finds **33 distinct `0xBB804xxx` offsets**, all 13 above among
them and 20 more that this table does not carry: `0x4108`, `0x410C`,
`0x4110`, `0x4114`, `0x4204`, `0x4300`, `0x4410`, `0x4754`, `0x4924`,
`0x4A0C`, `0x4A10`, `0x4A14`, `0x4D04`, `0x4D20`, `0x4D24`, `0x4D28`,
`0x4D2C`, `0x4D30`, `0x4D34`, `0x4D38`. ⚠️ **The new census has a
form limitation of its own**: it counts one instruction form, does not verify
the base register held `0xbb800000` at every site, and cannot see
displacement forms such as `lw v1,16644(v0)` — which is exactly how the
table above missed the `PCRP` loop below. 33 is a floor, not a total. The
consequence for `PROGRESS.md`'s `C-15` is that the set of unnamed addresses
is LARGER than one, so that row widens rather than closes.

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

🔴 **Withdrawn, 2026-08-23, by measurement.** `PITCR` reads **`0x00000000`** on
this board (`RUNSHEET.md` `E9`), not `0x00000001`, and `PCRP0` reads
`0x007F0039` — `EnForceMode` clear. **The whole strap-gated branch that does
`PITCR |= 1` did not run on this unit**, so the two `|= 1` sites say nothing
about what `PITCR` holds at the prompt.

It follows that **`P0phymode=01` is not `PITCR` bits 1:0.** The paragraph this
replaces claimed the loader names a value the datasheet calls Reserved, and that
claim was built entirely on connecting a printed `01` to a register field
without checking that the code writing that field had run. `PITCR = 0` is
`00: UTP (10/100M embedded PHY)` — which is what the boot line says in words.
**The datasheet and the loader agree; the contradiction was mine.**

### `PCRP0` is configured; `PCRP1`–`PCRP4` are not

The only per-port configuration register the loader writes is `PCRP0`. **(A.)**
It sets `EnForceMode`, `ForceLink` and a forced speed/duplex —
`(PCRP0 & 0xFF83FFFF) | 0x028C0000` on one branch and `| 0x02940000` on another,
selected by a strap read from `0xB800000C & 0xF` compared against 13.

🔴 **~~No loop over `PCRP1`…`PCRP4` exists in the image.~~
REFUTED 2026-09-14 — desk, zero power, and it was found by chasing the
`0xBB804234` census, not by looking for it.** 讀: the loop is at
`0x804033F4`-`0x80403414`. `lui a2,0xbb80` sits three instructions above it;
the body is `lw v1,16644(v0)` / `and v1,v1,a1` / `sw v1,16644(v0)` where
`16644` is `0x4104`, and the tail is `addiu a0,a0,1` / `slti v0,a0,5` /
`bnez` — `i < 5`, so it walks `PCRP0 + i*4` across **all five ports**.
The mask is `0xFDFFFFFF` = `~(1<<25)`, and **B**
`asicregs.h:919 (EnForceMode)` defines `EnForceMode` as `(1<<25)`, so this is
verbatim the vendor's `for i=0; i<5; i++` `REG32(PCRP0+i*4) &= ~EnForceMode`.
A second such site is at `0x804032E4`, and an unrolled `&= ~1` block covering
`PCRP0`-`PCRP4` sits at `0x804092F4`-`0x80409358`. ⚠️ **B is a
different generation** (RTL8196C rev B against this part's RTL8196E); what
carries the claim is A's own instruction stream, and B only names the bit.

🟢 **Prediction 4's READING survives and its REASON does not, and the
distinction is the whole point.** The reason given was *nothing writes them*;
something does. The reading held anyway because the loop touches **bit 25**
and `ExtPHYID` is **bits 30:26** — different fields. `E9b`'s
`047F0039 087F0039 0C7F0039 107F0039` still give `ExtPHYID` = 1, 2, 3, 4
(量), and bit 25 reads **0** in all four, which is what a loop that ran
leaves behind rather than a contradiction. ⚠️ **The heading above
this paragraph is now too strong as well** — `PCRP1`-`PCRP4` ARE written
— and it is left standing rather than edited, because other files cite
this section by its heading text.

*(What follows is this section's original reasoning, kept in place because
its prediction hit:)* So those four should still
hold reset defaults, and **D** Table 64 makes bits 30:26 predictable: `ExtPHYID`
= 1, 2, 3, 4. That is a read of the PHY-address assignment **that does not go
through MDIO**, and it is the cross-check B2 uses on the sweep.

🔴 **Reproduced within one boot, 2026-08-24.** `E9b` (`DW BB804100 8`,
`bench/2026-08-24b/E9b.log`) returned
`00000000 007F0039 047F0039 087F0039 / 0C7F0039 107F0039 00000000 187F0038`,
**byte-identical to seating 1's `E9`** — on a boot during which the cable had
been in four different jacks. So `PCRP` is **link-independent**: it holds
configuration, not link state, and it does not move with the thing `PSRP` moves
with. The practical consequence is that a later sweep of this block has a
comparison basis taken **within the same boot** rather than across a power cycle.
**Refutation:** any `PCRP` word differing between two reads with a cable move
between them.

`PSRP0`…`PSRP4` at `0xBB804128`–`0xBB804138` (**D** Table 62, and **B** agrees at
`PCRAM_BASE + 0x28`) give link state per port without MDIO. **B** names the bits:
8 `LinkDownEventFlag` (latched, **read to clear**), 7 NWayEnable, 6 RxPause,
5 TxPause, **4 LinkUp**, 3 Duplex, 1:0 speed (`00` = 10M, `01` = 100M). **D**
Table 65 confirms bit 8 and the 7:0 field, and leaves 7:0's interior to B.

One divergence, recorded: **B** defines `PSRP5` at `PCRAM_BASE + 0x3C`; **D**'s
Table 62 skips `0x3C` and resumes at `0x40` with `PSRP6`. D is this part.

### `PSRP` on silicon: the jack map, and three fields made to move

🔴 **Measured on the device, 2026-08-24.** Eight reads of `DW BB804128 8` on
one boot, five of them separated by a physical cable move — `bench/2026-08-24b/`,
cells `E10b`, `E11a`, `E11a2`, `E11b`, `E11c`, `E11c2`, `E11d`, `E11e`. `E10b` is
the negative control the sweep needed: **no cable in any jack**, and all five
ports read `0x000010E0`, bit 4 clear on every one. Without that read, a bit 4
that is always set and a bit 4 that follows the cable produce the same five rows
below.

**The socket ↔ port map.** One cable move per row; exactly one port with bit 4
set on each read, and a different one each time.

> 🔴 **The table below was withdrawn on 2026-08-24 and is superseded on
> 2026-08-25. It is left standing because the *readings* in it are real — what
> failed is the labels.** Every "RJ45, counted from the WAN side" in it was
> assigned **after** its reading, from memory, and `SPEC.md` `NET-13` records the
> two occasions that went wrong. **Do not take a port index from this table.**

| RJ45, counted from the WAN side | register | linked in |
|---|---|---|
| 1 = **WAN** | `PSRP0` `0xBB804128` | `E11b` |
| 2 | `PSRP2` `0xBB804130` | `E11a` |
| 3 | `PSRP3` `0xBB804134` | `E11c` |
| 4 | `PSRP4` `0xBB804138` | `E11d` |
| 5 | **`PSRP1`** `0xBB80412C` | `E11e` |

**Refutation, and it has still never fired:** any read with two ports' bit 4 set,
or none, while exactly one cable is in the board. Eight reads on 2026-08-24 and
five more on 2026-08-25 — **thirteen chances, thirteen times exactly one port.**
The bijection between the five sockets and ports `{0,1,2,3,4}` is the part of
this section that survived.

### 🆕 The map that replaced it, 2026-08-25 — silkscreen, not position

**Every point's label was stated by the operator *before* its own capture**, and
the filenames carry it (`bench/2026-08-25/E13-pos1-wan`, `E13-posX-lan1`,
`-lan2`, `-lan3`).

| socket, as the case is printed | port | |
|---|---|---|
| **WAN** | **0** | 量 |
| **LAN1** | **1** | 量 — 🔴 the socket behind the port `PORT1`'s patch list skips (section 4) |
| **LAN2** | **2** | 量 |
| **LAN3** | **3** | 量 |
| **LAN4** | **4** | 推, by elimination from the bijection above |

🔴 **Why this is a different map and not a correction of the old one.** The old
one is **position → port**; this one is **silkscreen → port**. They are the same
map only if the case is printed in ascending order from the WAN socket, **and
that order has never been recorded in this repository.** `RUNSHEET.md` `H3b` said
*"the jack written into the `--out` filename"* and meant position, while an
operator at the bench reads a silkscreen label — **the ambiguity was never
stated, and it is the same one both withdrawals came from.** Filenames now carry
`pos<N>-<silkscreen>` so that a future reader needs neither convention nor
memory; `posX` marks the points where the position is still unknown.

**What a driver should take from this**: the port index comes from `PSRP`, and
where a human-facing label is needed it comes from the **silkscreen** map above.
The position map is a fact about the case drawing, it is still 未定, and what it
needs is one look at the case — not a register read.

**Bit 8 is read-to-clear — confirmed, and only because the cell had a control.**
In order:

1. `E11a`, cable just pushed into jack 2: `PSRP2` = `0x000011F9`, **bit 8 set**.
2. `E11a2`, nothing touched between the two reads: `PSRP2` = `0x000011F9`,
   **bit 8 still set**. 🔴 **The conclusion drawn here — "bit 8 is sticky, and a
   `DW` read does not clear it" — is retracted.** It stays recorded because it
   was a reading of the device, not a slip: two consecutive reads of that port
   really did both show bit 8.
3. `E11c2`, the cell built to separate the two models: read `PSRP0`, which had
   gone down at `E11c` and **whose jack was by then empty**, so no new down-event
   was physically available. Bit 8 went **1 → 0** on a single read.

4. 🆕 **2026-08-25, and this is the first instance from a link settling *down*.**
   All three observations above are up-settles, where *a second real latch* and
   *the read did not clear it* give the identical reading. A **cable pull** is
   the clean version: `E13-pos1-wan` caught `PSRP2` at `0x000011E9` immediately
   after its cable was moved to the WAN socket, and `E11f-psrp2-empty`, with
   **nothing touched between the two reads and that socket empty**, read
   `0x000010E9`. One read, 1 → 0, and no new down-event was physically available.

🆕 **And the same pair measured something nobody had claimed in either direction:
speed and duplex are NOT gated by `LinkUp`.** `0x…E9` on an unplugged port is
bit 4 clear with **bits 3 and 0 still set** — full duplex, 100M — i.e. the last
negotiated result is *retained*, not cleared. The control is inside a single
capture rather than across boots: `E13-posX-lan3` shows the four ports that have
negotiated this power cycle at `…E9` and `PSRP4`, **the only one that never
has**, at `…E0`. 🔴 **A driver that reads speed or duplex without reading bit 4
first will report a live 100M full-duplex link on an empty socket.**

⇒ **Bit 8 is read-to-clear**, as **B**'s `LinkDownEventFlag` and **D**'s Table 65
both say. `E11a2` is then explained as a **second, real autoneg latch on a link
that was still settling** — an event on the wire, not a defect in the instrument
— and a third observation agrees: `PSRP3`'s bit 8 goes 1 → 0 between `E11d` and
`E11e` while jack 3 stayed empty throughout. **The control is the whole finding.**
On a port with a settling link, "a second latch" and "the read does not clear it"
produce the identical reading, so reading the register twice is not a
discriminator unless the port's jack is empty.

🔴 **Bits 6 and 5 are the negotiated flow control, and they were made to move.**
**B** names 6 `RxPause` and 5 `TxPause`; **D** leaves 7:0's interior to B. One
source, and a name is not a measurement. The paired comparison, across two power
cycles, two link partners and two instruments:

| | link partner | `ANLPAR` | bit 11 `ASM_DIR` | bit 10 `PAUSE` | `PSRP` bits 6,5 when linked |
|---|---|---|---|---|---|
| seating 1 | a PC NIC | `0xC1E1` (`E12`, `PHYR 2 5`) | 0 | 0 | **clear** — `PSRP2` = `0x1099` |
| 2026-08-24 | an RTL8153 USB GbE | **`0xCDE1`** (`E12b`, `PHYR 1 5`) | **1** | **1** | **set** — `PSRP1` = `0x10F9` |

**`0xCDE1 XOR 0xC1E1 = 0x0C00`** and **`0x10F9 XOR 0x1099 = 0x0060`**: the two
`ANLPAR`s differ in bits 11 and 10 and in nothing else, the two `PSRP` readings
differ in bits 6 and 5 and in nothing else. That is the point — not that the bits
were seen set, but that the only thing that changed on either side is the pair
they name. **In the down state both are set on every port** (`0x10E0` on all five
in `E10b`), so the default is "enabled" and it is a partner not advertising PAUSE
that clears them. **Not settled, and it must not be read as settled:** which of
the two is Rx and which is Tx. Both moved together, so the assignment is still
**B**'s alone. **Refutation, and it is also the experiment that separates them:**
a partner advertising exactly one of `ASM_DIR`/`PAUSE` should move exactly one of
bits 6, 5; if both still move together, the two bits are not separable this way.

🔴 **The 7th and 8th words of the read have no jack behind them.**
`DW BB804128 8` returns eight words and the map above accounts for five. Words 7
and 8 read **`0000007A`** on **all eight reads**, and word 6 reads `000000E2`
throughout — byte-identical to seating 1's `E10`. `0x7A` is bit 4 `LinkUp` = 1,
bit 3 `Duplex` = 1, and speed bits 1:0 = `10`, a code **above** `01` = 100M.

**Five physical cable moves changed `PSRP0`–`PSRP4` and left these three
untouched** — the invariance had five independent chances to fail and took none
of them. *Inferred, pending a measurement:* they are the switch's internal /
CPU-side ports, permanently up, full duplex, above 100M. `SPEC.md` `NET-10`
already records that the `PCRP` stride past port 4 is an inference and that no
source held here names those addresses; this is the same question on the `PSRP`
side, with an invariance result attached. **Refutation:** a cable move that
changes either word, or a change of link partner that moves the speed code.

🔴 **An unlinked port's `ANLPAR` reads `0x0001`, the selector alone.**
*(Measured 2026-08-24, `E12e`, `PHYR 0 5`, on a port whose jack was empty.)*
`00001` is 802.3's selector field; every ability bit is clear. Two things follow.
It is **different from `E12b`'s `0xCDE1`, read on address 1 minutes earlier on
the same boot**, which refutes the failure mode that would have voided the
flow-control comparison above — *the register is not per-port, and the MDIO block
returns one value whatever address is asked for*. And an unlinked port's
`ANLPAR` is **cleared rather than stale**: it does not keep the last partner's
advertisement. **No source held here predicted this**, and seating 1 never read
the register on an unlinked port.

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

---

## 🔴 A second build reports the switch MIRRORED — 2026-08-30

Everything in §7's table above is the **vendor kernel's** numbering, measured on
this unit, and it stays. What is new is that it is not the only numbering this
silicon reports.

量, `bench/2026-08-30b/L3.log:99-104` — a kernel built in this project from the
GPL drop, booted on the same board the same evening:

| netdev | vendor (`upstream/dumps/uart-boot.log`) | rlxfw (`L3.log`) |
|---|---|---|
| `eth0` | `0x10` | **`0x1`** |
| `eth1` (WAN, vid 8) | `0x1` | **`0x10`** |
| `eth2` | `0x8` | **`0x2`** |
| `eth3` | `0x4` | `0x4` |
| `eth4` | `0x2` | **`0x8`** |

As bit indices: **`rlxfw = 4 − vendor`** for all five, a 5-bit reversal whose
fixed point is `eth3` at bit 2. `RTL_WANPORT_MASK` is defined as `0x10` in one
`#ifdef` branch and `0x01` in another (讀, `rtl865x_netif.h:400`, `:411`), which
is where the two builds diverge.

**Why this file has to carry it**: a member-port bit indexes a physical switch
port, and the hardware fixes that. So the netdev↔jack binding is **not** a
property of the board — it is a property of the build. `NET-04`, `NET-13` and
anything derived from §7 are the *vendor's* binding, and `R5`/`R6` will be
writing against **this project's** kernel.

⚠️ **The safe way to name a jack is by port number.** 2026-08-29's `L-6c`…`L-6f`
sweep found the cable on **switch port 3** — which this project's kernel calls
`eth4` and the vendor's calls `eth2`. Written as a port it agrees with `NET-04`;
written as a netdev name it is true for exactly one of the two kernels.

⚠️ **Which of the two numberings matches the silk-screen labels is undetermined**
and neither log can settle it: both are the driver's own table, not the PCB.


---

## 🆕 2026-09-17 (seating 26) — `NET-10` closes on a header that was here all along, and eleven registers are read in both states

### The closure, and the lesson is about searching

§ 7 above says of `0xBB804118`/`0x411C` that *the spacing is inferred* and that
**no source in hand names these two addresses**. 讀,
`src-vendor/rtl819x-toolchain/linux-2.6.30/drivers/net/rtl819x/AsicDriver/rtl865xc_asicregs.h:1132-1151`:

    #define PCRAM_BASE   (SWCORE_BASE+0x4100)        /* REAL_SWCORE_BASE = 0xBB800000, :147 */
    #define PCRP5        (0x018 + PCRAM_BASE)        -> 0xBB804118
    #define PCRP6        (0x01C + PCRAM_BASE)        /* Port Configuration Register of Ext Port 0 */
    #define PSRP5..PSRP8 (0x03C..0x048 + PCRAM_BASE) -> 0xBB80413C .. 0xBB804148

**Every one of them is named, with an offset and a comment, in a file this
repository has carried since day one.** 🔴 What was missing was not a
measurement; it was somebody opening that file. This is the second finding of
that shape this month and it is about how the project searches.

### The cross-state confirmation — eighteen fields

量 2026-09-17: block 24's loader-prompt `PSRP` readings against the vendor
driver's own `/proc/rtl865x/port_status` (`bench/2026-09-17/C2-PORT.log`, and
again in the same power cycle at `bench/2026-09-17b/C6-PORT.log`, **byte-identical**,
md5 `6413559b8e7bb4b853b91fc9cca7d333`).

| register | loader-state | `/proc` under Linux |
|---|---|---|
| `PSRP3` `0xBB804134` | `000010F9` | `Port3 … LinkUp \| NWay Mode Enabled` / `RXPause \| TXPause` / `Duplex \| Speed 100M` |
| `PSRP5` `0xBB80413C` | `000000E2` | `Port5 … LinkDown` |
| `PSRP6`/`PSRP7` `0x4140`/`0x4144` | `0000007A` | `CPUPort … LinkUp \| NWay Mode **Disabled**` / `RXPause \| TXPause` / `Duplex \| **Speed 1G**` |

🟢 **`NWay Mode Disabled` is the load-bearing field.** Every real port on this
part reads `NWayEnable = 1`; a CPU port does not negotiate. It is the one field
that could not have been guessed from link state, and `/proc` prints it for
exactly the register whose bit 7 is clear. 🟢 § 7's own 2026-08-24 inference that
speed code `10` is *higher than `01` = 100M* becomes 量, by a file that prints
the characters `1G`.

### 🔴 `0xBB804118` is a three-way disagreement, not a confirmation

B names `PCRP5` there. **D's Table 62 skips it.** The silicon reads
**`00000000`** where every neighbour reads `xx7F00xx`. **The measurement sides
with D**: the address decodes — it returns zero rather than garbage — but this
part does not populate that port. A driver written from B alone would program a
register that is not there.

### ~~The eleven registers, both states~~ — 🔴 **the heading says ELEVEN and the table below has TWELVE rows**

*(Corrected in place 2026-09-17, eighty-sixth segment. The heading is left
standing rather than rewritten, because other files quote it.)*

量: the table carries twelve distinct addresses. `SPEC.md` `NET-21` lists
**thirteen** loader-touched addresses, of which **two already carried a value**
(`0x4100 PITCR`, `0x4104 PCRP0`) — so *the eleven* is the other eleven, and
`PROGRESS.md`'s 十一個 is **correct**. What is wrong is this table: it silently
gained `PITCR`, which already had a value, and omits `PCRP0`, which did not.
🔴 **And the omission is the one `R6-2` needed** — `PCRP0` is the Port
Configuration Register of port 0, and 量 `0xBB804104` has **no Linux-state
reading anywhere in `bench/`**.

### The register readings, both states

量 2026-09-17. Loader side `bench/2026-09-17b/C1`–`C9`; Linux side `X28`–`X47`
through `/proc/rtl865x/memory`, which needs no new image.

| address | symbol | loader | Linux |
|---|---|---|---|
| `0xBB804000` | `MACCR` | `804A0185` | `804A0185` |
| `0xBB804004` | `MDCIOCR` | `96181441` | `84001300` |
| `0xBB804008` | `MDCIOSR` | `00000000` | `00001100` |
| `0xBB804100` | `PITCR` | `00000000` | `00000000` |
| `0xBB80414C` | `P0GMIICR` | `00037D00` | `00037D00` |
| `0xBB804234` | `MEMCR` | `00007F7F` | `00007F00` |
| `0xBB804418` | `SWTCR0` | `00080000` | `00097DE0` |
| `0xBB804428` | `FFCR` | `00000003` | `00000009` |
| `0xBB804A08` | `PVCR0` | `00080008` | `00090009` |
| `0xBB804D00` | `SWTACR` | `00000000` | `00000000` |
| `0xBB804D08` | `SWTAA` | `BB060100` | `BB040020` |
| `0xBB804D3C` | `TCR7` | `00000000` | `07000030` |

🔴 **Before this, no word in `0xBB804xxx` had ever been read under Linux** —
量, `grep -rl BB804 bench/` returns 41 files in four directories, newest
`bench/2026-08-25`.

### 🟢 `PVCR` is per-port PVID

`0xBB804A08`–`0xBB804A1C` under Linux: `00090009`, `00090009`, **`00010008`**,
`00010001`, `00000009`, `00021B74`. ~~**Six addresses, five distinct values**~~ 🔴 **the sixth is not a `PVCR`** — `0xBB804A1C` is **`PBVCR0`**, the Protocol-Based VLAN Control Register (讀 `rtl865xc_asicregs.h:2306`), so its `00021B74` is not a PVID word at all. **Five addresses, five distinct values**, so
the block is not aliasing, and both intended negative controls differ. **Exactly
one ~~16-bit~~ **12-bit** field reads `8`** 🔴 *(the field is 12 bits + 3 bits of priority, not 16 — 讀 `:2392-2430`, where the header names `PVIDP0_OFFSET 0` / `DPRIOP0_OFFSET 12` / `PVIDP1_OFFSET 16` / `DPRIOP1_OFFSET 28`. Every priority reads 0 here so no number changes; the description would have misled the first time one was set. `SPEC.md` `NET-37`.)* and the other PVID-shaped fields read `9` or `1` —
and `NET-04`, 量 from the vendor kernel's own boot lines, records exactly one
port on **vid 8** (the WAN) against four on **vid 9**. ⚠️ **推**: which physical
port `0xBB804A10` is.~~ 🟢🟢 **ANSWERED 2026-09-17 (`NET-37`), and this section's own caution was right.** The five words decode to P0=9 P1=9 P2=9 P3=9 **P4=8** P5=1 P6=1 P7=1 P8=9 — the WAN on **port 4**, where `NET-04` says port 0. Both are 量 and they are two different states: 量, this image's own boot line is `eth1 added. vid=8 Member port 0x10` (bit 4) on **104** captures, the vendor firmware's `upstream/dumps/uart-boot.log:27` is `Member port 0x1` (bit 0) on **5**, and all five interfaces are the **4−n mirror** of each other. block 26's capture carries `RLXFW-ID0=BB684EB0`, so it ran under rlxfw. 🟢 **So the mirror is confirmed by a path sharing no code with the register read.** ⚠️ 推: `NET-13` measured this kernel's netdev↔port map as the
**mirror** of the vendor's, so `NET-04`'s port numbers do not carry across.

### 🔴 `ip link set <if> down` is not a link-down event on this RTL8153

量: the host interface went `down → up → down → up` and the board's `PSRP3`
never left `000010F9`. **The peer was identified from the board's side**:
`PHYR 3 5` reads `ANLPAR` = **`0x0000CDE1`** and `PHYR 3 1` reads `BMSR` =
**`0x000078ED`**, and § 7's `NET-14` holds three fingerprints of which **two are
negative controls that did not match** (`0xC1E1` a PC NIC, `0x0001` unlinked;
`0x78C9` unlinked). ⚠️ **推**: the driver leaves the PHY powered and negotiated
while the interface is administratively down.

⚠️ **`ethtool` on this usbip path is not a second source**: it reports
`Supports auto-negotiation: No` and `Duplex: Half` for a gigabit adapter, and it
**disagrees with the board**, whose `PSRP3` bit 3 is set. The board is the
better source.

**Consequence**: a link transition cannot be produced on this bench with
`ip link set`. It needs a physical unplug or a host-side PHY command, and
neither has been shown to work on this adapter.

### 🔴 `PSRP` bit 12 — two instances, and it is not about link

`PSRP0`: `000010E0` at the prompt, `000000E0` under Linux, on a **LinkDown**
port. `PSRP3`: `000010F9` → `000000F9`, on a **LinkUp** port. The low byte is
identical in both ports and both states; **the whole difference is bit 12**, and
§ 7's `NET-11` bit map stops at bit 8. Re-read after `ifconfig eth4 up`: still
clear, so `ndo_open` does not set it either. ~~**未定.**~~
🟢 **CLOSED 2026-09-19 — it is `PortEEEStatus[0]`.** See the seating-27 section
below.

---

## 🆕 2026-09-17 → 2026-09-19 (seating 27) — five PHYs by four register families, and the PHY is identified

**量 on this device 2026-09-19 between 01:42 and 02:40**, captures
`bench/2026-09-19/C1`–`C41` and `X0`–`X24`; the seating's own record is
`bench/2026-09-19/CORRECTIONS-block27.md`. 讀 claims below name the file and
line they came out of.

### 🟢🟢 Section 6's prediction held, and three other families said the same thing independently

§ 6 wrote, before any of this was measured: *"PHY addresses 0–4 answer; 5–31 do
not"*, with the refutation *"all 32 addresses returning the same plausible
value means the bus is echoing and nothing was measured."*

量 `X8-mdior02` — the first execution of `MDIOR` in either project:

> **MDIO addresses `0x00`–`0x04` read `0x1100`. Addresses `0x05`–`0x1F` read
> `0x0000`.**

The refutation did not fire: 27 of the 32 answered `0x0000`, which is the
classic *nothing answers here*. `0x1100` decodes as `BMCR` with bit 12
`aneg_enable` and bit 8 `duplex` — an autonegotiating, full-duplex-preferring
PHY. 🟢 **And address 1 answers like the other four**, which is `SPEC.md`
`NET-07` confirmed a second time and on a second instrument: § 4's `PORT1`
patch list skips address 1, and the skip is about the **port**, not the PHY.

🟢 **Three further families agree, sharing no code with MDIO and none with each
other:**

| family | capture | what it says |
|---|---|---|
| MDIO sweep | `X8` | PHYs answer at 0–4, silence at 5–31 |
| `PCRP` bit 0 `EnablePHYIf` | `C1-L4104`, `C2-L4114` | set on 0–4 (`nn7F0039`), **clear** on 6 and 7 (`187F0038`, `1C7F0038`); `PCRP5` reads `00000000` |
| `PSRP` bits 13:12 `PortEEEStatus` | `C3`, `C4`, `C5` | **1** on 0–4, **0** on 5, 6, 7 and 8 — and EEE is a PHY feature |
| `PSRP` value | `C4`, `C5` | `0x0000007A` on 6, 7 **and 8** — one non-PHY default |

⚠️ **`PCRP`'s top byte is `4n`** — `00 · 04 · 08 · 0C · 10 · — · 18 · 1C` —
which is exactly the address-echo pattern `upstream/BENCH-LOG.md:4790-4791`
worried about. 🟢 **`PCRP5` reading `00000000` rather than `147F00xx` is what
closes it**, for the second time and on a second seating: an echoing bus would
have produced the missing `14`.

### 🟢🟢 The PHY is identified, and the decode is shown rather than asserted

量 `C19-PHYID`, `C20-PHYST`, through the vendor's `/proc/rtl865x/phyReg`
(⚠️ the *write* side — `proc_phyReg_read`'s whole body is
`return PROC_READ_RETURN_VALUE;`, so `cat` on that file prints nothing and the
output arrives on the console):

```
phyId(0) regId(0) = 0x1100     BMCR
phyId(0) regId(1) = 0x78c9     BMSR
phyId(0) regId(2) = 0x001c     PHYIDR1
phyId(0) regId(3) = 0xc880     PHYIDR2
```

🟢 **`BMCR = 0x1100` is byte-identical to what the loader's `MDIOR` read for
PHY 0** — the vendor's `/proc` under Linux and the loader's own MDIO primitive
at `0x80402F80`, two paths, one value, across a power cycle. § 1's three-source
agreement about the primitive now has a fourth leg that is a reading rather
than a document.

**The identifier, decoded by the IEEE 802.3 clause 22.2.4.3.1 split, stated so
it can be redone**: composite `phy_id = (PHYIDR1 << 16) | PHYIDR2` =
**`0x001CC880`**; `PHYIDR1[15:0]` carries OUI bits 3–18, `PHYIDR2[15:10]`
carries OUI bits 19–24, `PHYIDR2[9:4]` is the model number and `PHYIDR2[3:0]`
the revision.

| field | arithmetic | value |
|---|---|---|
| OUI, 22 bits | `(0x001CC880 >> 10) & 0x3FFFFF` | **`0x732`** |
| model number | `(0xC880 >> 4) & 0x3F` | **8** |
| revision | `0xC880 & 0xF` | **0** |

**Recovering the 24-bit OUI.** The 22 bits are OUI bits 3–24 in transmission
order, so they are laid out `000000 · 00000111 · 00110010`; bits 1 and 2 are
the I/G and U/L bits and are **not carried by the register pair at all**, so
they are supplied as zero, which is what an OUI assigned to a manufacturer
has. Reversing each octet into canonical form gives `0x00 · 0xE0 · 0x4C` —
**`00-E0-4C`**.

🔴 **What that OUI is called is external to this repository, and the internal
corroboration is the stronger half.** § 6 above already records that the only
PHY-ID constant anywhere in **B** is `0x001CC912`, whose own comment calls it
*"8212 two giga port"*. 量: `(0x001CC912 >> 10) & 0x3FFFFF` = **`0x732`** — the
**same 22 bits**. So this die's PHY and the vendor tree's own Realtek constant
carry one OUI, established without leaving the repository. 推, from the IEEE
registry and nothing in this project: `00-E0-4C` is Realtek Semiconductor.
⚠️ **The part is NOT named here.** Model 8 revision 0 is what the bits say, and
**no source in this repository maps a Realtek model number to a part number** —
§ 6 looked for a PHY register map in **D** and there is none. Naming an
`RTL8201x` from these four bits would be the same move § 3 records for
`MDIOR`: a confident answer from a tree that is not this unit.

🟢 **`BMSR = 0x78C9` is consistent with three other sources.** Link Status
(bit 2) and Autoneg Complete (bit 5) are **clear**; PHY 0 is port 0; `PSRP0`
reads `LinkUp` clear and `/proc/rtl865x/port_status` prints `Port0 … LinkDown`.
⚠️ `0x78C9` is also one of the three fingerprints § 7's `NET-14` holds, where
it is the **unlinked** negative control — consistent, and it is a negative
control matching, not a new identification.

### 🟢 `NET-10 殘留` closes, and it closes by REMOVING a piece of evidence

§ 7's `A2` proposed the test in advance: *"If `PSRP8` is also `0000007A`, then
`7A` is the non-PHY default and `PSRP7`'s equality with `PSRP6` carries no
information."* 量 `C5-L4148`: **`PSRP8` is `0000007A`** — its first reading
ever. `PSRP6`, `PSRP7` and `PSRP8` are the same word, and that word is what a
port with no PHY reads.

**So what settles which port is the CPU port is a printer's loop variable, not
any property of `PSRP7`.** 讀, and now on two printers rather than one:
`rtl865xC_dumpAsicDiagCounter()`, `rtl865x_asicCom.c:1776-1787`, loops
`i` over `0 … RTL8651_PORT_NUMBER` **inclusive** and prints
`<CPU port (extension port included)>` at `i == RTL8651_PORT_NUMBER`, which is
`RTL8651_MAC_NUMBER` = **6** (`rtl865x_asicCom.h:24-25`). `port_status` prints
`Port0`…`Port5` then one `CPUPort` row for the same reason. **Two `/proc`
files, one constant, and neither is a statement about the silicon.**

### 🔴 `PSRP6_RW` is not a second view of `PSRP6`

量 `C6-L4600`: `0xBB804600` reads **`0000007E`**, where `PSRP6` at `0xBB804140`
reads `0000007A` in the same power cycle. 讀
`rtl865xc_asicregs.h:1825`: `#define PSRP6_RW (SWCORE_BASE+0x4600)
/*CPU Port Status : R/W */`.

`PSRP6 XOR PSRP6_RW` = `0x00000004` — **one bit, bit 2**. The card predicted
`0000007A` from that header comment and the prediction is **refuted**: the
comment does not describe a second view of the same word. **What bit 2 is:
未定.** ⚠️ The other three words the `DW` served are recorded so they are not
read again as a discovery: `+0x04` `00000000`, `+0x08` `00000000`, `+0x0C`
`0C400000`, all **uninterpreted**.

### 🟢 `PSRP` bit 12 is `PortEEEStatus[0]`, and the loader-state values carry their own control

讀 `rtl865xc_asicregs.h:1326-1327`:
`PortEEEStatus_MASK (3<<12)`, `PortEEEStatus_OFFSET 12`, under the comment
`/* PSRP0..PSRP8 - Port Status Register Port 0~8 */`.

🟢 **Two things make this a closure rather than a guess.** First, 量 over the
whole 2.6.30 tree the symbol has **three** occurrences — the two defines and
**one** use, `rtl865x_proc_debug.c:4218-4219`, which is the line that prints
`EEE Status %0x`. *The only consumer of the field in the entire vendor driver
is a printf.* Second, the loader-state readings are their own control: bits
13:12 read **1** on exactly the five ports with an embedded PHY and **0** on
the three without, with the unpopulated port 5 sitting between the classes —
an arrangement a bit that meant something else would have to reproduce by
accident.

⚠️ **It also explains the § above rather than merely renaming it**: the field
is `10E0` at the prompt and `00E0` under Linux on both a LinkDown and a LinkUp
port, so whatever sets it is the loader's own bring-up and the vendor's NIC
driver clears it. `/proc/rtl865x/port_status` under Linux prints
`EEE Status 0` for every port (量 `C21-PORT`), which is the same reading from
the other side. ⚠️ Unlike `PCRP`, this define is **outside every `#if`** — it
sits immediately after the `#endif` at `:1323` — so § 4's double-definition
hazard (`rtl865xc_asicregs.h` defining `PCRP`'s bit positions twice with
different values) does not apply to it.

### 🟢 The cable is in port 3, measured rather than looked at

量 `C3-L4128`: `PSRP0`–`PSRP2` read `000010E0` and **`PSRP3` reads
`000011F9`** — the only one of `PSRP0`–`PSRP4` with `LinkUp` (bit 4) and speed
`01` = 100M. `/proc/rtl865x/port_status` prints `Port3 … LinkUp | NWay Mode
Enabled / Duplex | Speed 100M` and `asicCounter` puts all six frames of a
four-packet ping on `<Port: 3>` in both directions. **Three instruments, one
port**, and the silkscreen map above says port 3 is LAN3.

### 🆕 § 7's census is a floor, and here are the addresses it was missing

§ 7's thirteen addresses come from resolving each `lui …,0xbb80` to its
following `ori` or displacement. 讀 2026-09-19, the same resolution carried
**forward through the base register for 40 instructions** instead of stopping
at the first hit — with § 7's thirteen as the positive control, **all thirteen
re-found**:

| address | what it is | where |
|---|---|---|
| `0xBB804108` · `0x410C` · `0x4110` · `0x4114` | **`PCRP1`–`PCRP4`** | two sites each: `0x80403494`… and the `J` handler |
| `0xBB804204` | `SSIR` — `\|= 1` (`TRXRDY`) | `0x80403970` |
| `0xBB804300` | unnamed in every source here — written `0x00200000` | `0x804039B0` |
| `0xBB804410` | **`MSCR`** — written the literal `0x00000001` | `0x80403950` |
| `0xBB804754` | unnamed in every source here — written `0x00001249` | `0x8040395C` |
| `0xBB804A0C` · `0x4A10` · `0x4A14` | **`PVCR1`–`PVCR3`** — written `0x00080008` | `0x80403930`… |
| `0xBB804D04` · `0x4D20`–`0x4D38` | the TACI block's interior | one site each |

🔴🔴 **The most consequential of those is in the `J` handler, and it explains a
state transition two projects have measured.** 讀 `0x804092F4`–`0x80409354`,
the last thing `J` does before `flush_cache` and `jalr`:

```
ori a0,v1,0x4104 ; lw v0,0(a0) ; and v0,v0,a1 ; sw v0,0(a0)    ; a1 = -2
  ... and the same three instructions for 0x4108, 0x410C, 0x4110, 0x4114
```

**Five registers, one bit each, and the bit is `EnablePHYIf`.** So
`upstream/BENCH-LOG.md:4770-4795`'s August reading — *"At rest under the
loader: `007F0039`… **After `J`: all `...0038`**"* — and seating 27's `S0′`
latch (`nn7F0038` at `subsys_initcall`, `nn7F0039` at the prompt) are the same
fact, and neither is about the kernel. **A payload entered with `J` inherits
five disabled PHY interfaces.** `notes/switch-driver.md` § 8.3 owns the
consequence for a driver.

⚠️ **Two negative results from the same census, each with its control.** It
finds **no site anywhere in the 56,592 bytes** that forms `0xBB804A00` (`VCR0`)
or `0xBB80441C` (`SWTCR1`) — no `ori`/`addiu` with those immediates and no load
or store with displacement 18944 or 17436 — while the controls `0x4410`,
`0x4204` and `0x4A08` each return exactly one. 推 that the loader-prompt
readings `000001FF` and `00000200` are therefore the **power-on** values.
🔴 **The census's blind spots are stated rather than left to be found**: a base
register carried in across a call, or `lui …,0xbb81` with a negative
displacement, would be invisible to it, and either would refute the 推.
⚠️ And `PITCR` is the standing warning against reading a write as a value:
`0x80403904` does `PITCR |= 1` and `PITCR` reads `00000000` at the prompt and
under Linux both.
