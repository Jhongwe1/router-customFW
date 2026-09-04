# `R5-10` — the interrupt map, and the layers a timer interrupt has to cross

**Owner of: how an interrupt reaches the CPU on this part.** Which register
masks what, which of them the kernel already owns, what `R5-3` has to write and
in what order, and which fields nothing here has ever read.

Every line is marked **量** (measured on this device), **讀** (read out of code,
a header or a dump) or **推** (inferred, with the experiment that would settle
it). `量` in this file always means *on the silicon*, never *on this desk*.

Written 2026-09-04, thirty-first segment. `R5-10` was the last row of `R5`'s
step table until seating 11 made it `R5-3`'s prerequisite: `TMR-2` closed the
route `R5-3` was designed around, so the next driver step cannot be written
until this file exists. **§ A is what `R5-3` needs; § B is what `R6` needs.**
The step's own DoD says *"written as `R6`'s prerequisite"*, and that is § B.

---

## 0. The one sentence this file defends

**A TC1 interrupt on this SoC crosses seven independent gates (§ 3.1), they
live in three different register files, and two of them are owned by code that
is already in the kernel.** Writing a driver as though there were one gate — a
`GIMR` bit — is how `rtl819x-timer` came to arm a counter for 703 seconds
without arming an interrupt.

⚠️ **Three files for TC1, four for the SoC.** TC1 uses the timer block
(`TCCNR`/`TC1DATA`/`TCIR`), the interrupt controller (`GIMR`/`IRR1`) and CP0
(`Status`). The **fourth** is `lxc0` — `ESTATUS`, reached by `mflxc0` — and it
is on the **LOPI** path, which is where the vendor's own tick (TC0, IRQ 13)
runs. A driver on TC1 never touches it; a reader of `SPEC.md` `IRQ-04` would
have thought TC0 did not either.

*(This paragraph said **five** gates and **four** files until it was re-read
against its own § 3.1 table, which has always said seven. The count was
written before the table was finished and nothing but re-reading it could
have caught it — no checker in this repository compares a document's prose to
its own tables.)*

---

## 1. Three domains, forty-eight lines

讀, `arch/rlx/bsp/bspchip.h` (this board's own BSP; § 6.1 is why that file
took finding) and `arch/rlx/include/asm/mach-generic/irq.h`:

| Linux IRQ | domain | init | the mask lives in | instruction |
|---:|---|---|---|---|
| **0 – 7** | CPU | `rlx_cpu_irq_init` (`arch/rlx/kernel/irq_cpu.c`) | `Status.IM`, bit `8 + n` | `mfc0`/`mtc0` |
| **8 – 15** | LOPI | `rlx_vec_irq_init` (`arch/rlx/kernel/irq_vec.c`) | **`ESTATUS[23:16]`**, bit `16 + (n − 8)` | **`mflxc0`/`mtlxc0`** |
| **16 – 47** | ICTL | `bsp_ictl_irq_init` (`arch/rlx/bsp/irq.c`) | **`GIMR`** bit `n − 16` | ordinary `sw` |

`NR_IRQS` is **48** = 8 + 8 + 32, and the three bases are
`BSP_IRQ_CPU_BASE 0`, `BSP_IRQ_LOPI_BASE 8`, `BSP_IRQ_ICTL_BASE 16`.

🔴 **The middle row is the one no file in this repository had.** `SPEC.md`
`IRQ-04` names *"`Status.IM[7:2]` unmasked"* as the CPU-side layer. That is
right for the ICTL cascade and **wrong for anything on a LOPI line** — the
vendor's own system tick included, since `BSP_TC0_IRQ` is 13. LOPI is masked in
a *different register file*, reached by a *different instruction*.

### 1.1 `mflxc0`/`mtlxc0` is a third coprocessor register file, and it is not CP3

讀 `arch/rlx/include/asm/rlxregs.h`: `LXCP0_ESTATUS $0`, `LXCP0_ECAUSE $1`,
`LXCP0_INTVEC $2`, `LXCP0_CCTL $20`, with `EST0_IM = 0x00ff0000`.

**量 on the built artefact** (`r51quiet.vmlinux.elf`, `objdump -d`), against
the assembler's own encoding of the neighbouring mnemonics:

| written | encoding | opcode | `rs` |
|---|---|---|---|
| `mfc0 v0,$0` | `0x40020000` | `010000` COP0 | 0 |
| `mtc0 v0,$0` | `0x40820000` | `010000` COP0 | 4 |
| **`mflxc0 $2,$0`** (as built) | **`0x40620000`** | `010000` COP0 | **3** |
| **`mtlxc0 $2,$0`** (as built) | **`0x40e20000`** | `010000` COP0 | **7** |
| `mfc3 v0,$0` | `0x4c020000` | `010011` **COP3** | 0 |

So `mflxc0` is **COP0's opcode with a `rs` field MIPS leaves unassigned**, and
it is a different thing from the `mfc3` this project measured reachable on
2026-08-29. 🔴 **Do not carry the CP3 result over to it**; they are separate
register files reached by separate opcodes, and nothing here has probed the
`lxc0` file directly.

⚠️ **And `-march` decides whether the instruction exists at all.** 量, the
rsdk assembler: `mflxc0` assembles at `rlx4181`, `rlx4281`, `rlx5181`,
`lx5280`, `rlx5281`; it is **rejected** at `lx4180` and at **`mips32`**.
🟢 **讀, and this repository already held it**: `SOURCES.json`'s
`reference_only/platform[7]` records the binutils-2.24 Lexra patch as adding
*those six cores, all `ISA_MIPS1`*, with per-core instruction masks
(`INSN_4180 = 0x20000000` … `INSN_5281 = 0x00000040`) and the `RLXA`/`RLXB`
groupings — and it names **`mflxc0`/`mtlxc0`** in its own list of the
Lexra-proprietary mnemonics. So the measurement and the toolchain's own
declaration agree, and the `lx4180` rejection is a mask grouping rather than
an accident. The entry has been in `SOURCES.json` since `R1a`; nothing had
connected it to `arch/rlx`'s interrupt path.

🔴 **The `mips32` rejection is a second, concrete reason for `CLAUDE.md`'s
standing ban, and unlike the first it is not silent.** The first is the
load-delay miscompile — no fault, no warning, wrong values. This one stops the
build: at `-march=mips32` the primitive that masks a LOPI interrupt does not
assemble at all.

---

## 2. The registers, with two sources each

| register | address | source ① | source ② | 量 |
|---|---|---|---|---|
| `GIMR` | `0xB8003000` | D § 8.1.1 Table 14 | `bspchip.h` bit list | `SPEC.md` `REG-01` |
| `GISR` | `0xB8003004` | D § 8.1.2 Table 15 | `bspchip.h` bit list | `REG-02` |
| `IRR0` | `0xB8003008` | `bspchip.h` `BSP_IRR0` | — | **never read** |
| `IRR1` | `0xB800300C` | `bspchip.h` `BSP_IRR1` | A (loader disassembly) | `REG-03`, loader prompt only |
| `IRR2` | `0xB8003010` | `bspchip.h` `BSP_IRR2` | D | **never read** |
| `IRR3` | `0xB8003014` | `bspchip.h` `BSP_IRR3` | — | **never read** |
| `TCCNR` | `0xB8003110` | D Table 24 | `bspchip.h` `BSP_TC0EN`… | `REG-09` |
| `TCIR` | `0xB8003114` | D Table 25 | `bspchip.h` `BSP_TC0IE`… | `REG-10` |

🟢 **`bspchip.h` is a second source for D Tables 24 and 25, and it agrees bit
for bit** — `BSP_TC0EN (1<<31)`, `BSP_TC0MODE_TIMER (1<<30)`,
`BSP_TC1EN (1<<29)`, `BSP_TC1MODE_TIMER (1<<28)`; `BSP_TC0IE (1<<31)`,
`BSP_TC1IE (1<<30)`, `BSP_TC0IP (1<<29)`, `BSP_TC1IP (1<<28)`. Until today
both tables stood on the leaked draft datasheet alone.

🔴 **`IRR0` is a register `SPEC.md` does not have at all.** The step's own
title says *"`IRR1`–`IRR3`"*; there are **four**.

---

## A. What `R5-3` needs

### 3.1 The gates a TC1 interrupt crosses, and the state each was in during seating 11

TC1's Linux IRQ is **25** — `BSP_TC1_IRQ = BSP_IRQ_ICTL_BASE + 9` (讀), so TC1
is an **ICTL** source and TC0 is a **LOPI** source (`BSP_TC0_IRQ = 13`). The
two timers in one register block do not share a route.

| # | gate | register · bit | who owns it | seating 11 | 量 from |
|---:|---|---|---|---|---|
| **L1** | counter enabled | `TCCNR` 29 `TC1En` + 28 `TC1Mode` | `rtl819x-timer` | 🟢 **set** (`C0000000` → `F0000000`) | `TM-3` |
| **L2** | period loaded | `TC1DATA` 31:4 | `rtl819x-timer` | 🟢 `80000000` = 2²⁷ ≪ 4 | `TM-3` |
| **L3** | **timer-block interrupt enable** | **`TCIR` 30 `TC1IE`** | 🔴 **nobody** | 🔴 **CLEAR** — `TCIR` read `80000000` for all 703 s | `TM-5b2` |
| **L4** | controller mask | `GIMR` 9 `TC1_IE` | `bsp_ictl_irq_unmask` for IRQ 25 | 🔴 clear (`gimr = 00209100`) | `TM-5b2` |
| **L5** | routing | `IRR1` 7:4 `TC1_RS` | `bsp_irq_init` | **未讀 under Linux** | — |
| **L6** | cascade line | `Status.IM2` (`Status` bit 10) | `rlx_cpu_irq_init` + `setup_irq(BSP_ICTL_IRQ)` | 未讀 | — |
| **L7** | global enable | `Status.IEc`, `Status.BEV` | the kernel | 推 — the vendor tick runs, so they are right | — |

🆕 **2026-09-04 (`R5-3a`): `L5`, `L6` and `L7` all become readable on the next
seating, and none of them needed a new instrument.** The driver's `/proc` file
now carries `irr0`–`irr3` (the same register block it already mapped) and
`Status`, so one `cat` fills the last three rows of this table. The predictions
are § 4.3's for `L5` and `status_im2=1` for `L6` (讀
`arch/rlx/kernel/irq_cpu.c:44`: `setup_irq(BSP_ICTL_IRQ)` with
`BSP_ICTL_IRQ = 2` calls `set_c0_status(0x100 << 2)` = bit 10).

🔴 **`L7` is written `Status.IEc` and not `Status.IE`.** 讀
`arch/rlx/include/asm/rlxregs.h`: this core has the MIPS-I three-deep
interrupt-enable stack — `ST0_IEC` (bit 0), `ST0_IEP` (bit 2), `ST0_IEO`
(bit 4) — and **no single `ST0_IE` is defined at all**. That agrees with
`SOURCES.json`'s binutils note that every Lexra core is `ISA_MIPS1`, and it is
a second instance of § 1.1's lesson: a MIPS32 name carried over to this part is
a name that may not exist here.

⚠️ **`Status` must be read OUTSIDE a `spin_lock_irqsave`**, or `IEc` reads 0
always and the measurement is a constant. `IM2` and `BEV` are unaffected; only
one of the three bits needed the care.

### 3.2 🔴 `TMR-2`'s attribution is wrong, and correcting it gives `R5-3` back the step it was told it had lost

`bench/2026-09-03/CORRECTIONS-block8.md` § 5, `notes/timer-driver.md` § 8.4 and
`SPEC.md` `REG-10` all say the same sentence:

> *`TC1IP` does not latch in `TCIR` while `TC1IE` is clear in `GIMR` on this die.*

**The observation is correct and the attribution is not, because two different
enables were clear at once and the experiment does not separate them.** 量,
`TM-5b2`, over the whole 703.46 s arm:

```
tcir  = 80000000     -> TC0IE=1  TC1IE=0  TC0IP=0  TC1IP=0
gimr  = 00209100     -> bit 9 (TC1_IE) = 0
```

`TCIR` bit 30 is the **timer block's own** interrupt enable; `GIMR` bit 9 is the
**controller's** mask, one layer downstream. Both were 0.

🟢 **This repository already holds the reading that decides between them, and it
is fourteen days older than the question.** `RUNSHEET` `C5` (量, seating 1,
2026-08-24): `GIMR` bit 8 was cleared **by hand**, a tick elapsed, and `GISR`
moved `88000004` → **`88000104`** → `88000004`. Bit 8 is `TC0_IP`.

**So on this die a `GIMR` mask does not stop the pending bit from latching.**
It stops *delivery*; the latch happens anyway, and re-enabling the mask let the
handler run and ack it. By that reading `GIMR` bit 9 cannot be why `TC1IP` and
`GISR` bit 9 both stayed 0 for 703 seconds — and the remaining clear gate is
`TCIR.TC1IE`.

🔴 **What the driver actually does.** `rtl819x_tc1_arm()` writes `TCCNR` bits
29/28 and `TC1DATA`, and **never writes `TCIR` bit 30**. The only `TCIR` write
in the file is in `disarm`, and it deliberately *preserves* the IE bits
(`(ir & RTL819X_TCIR_IE_BITS) | RTL819X_TCIR_TC1IP`). The file's own header
comment asserts *"`TCIR`'s `TC1IP` (bit 28) latches on a TC1 timeout"* — 推,
and it is that assumption, not the hardware, that seating 11 refuted.

**Consequence: the masked-observation strategy is not dead.** `notes/timer-driver.md`
§ 4 built the driver's safety argument on watching the pending bit with the
interrupt masked. That argument is intact; what was missing is that nothing
ever set the bit that makes a pending flag happen.

### 3.3 The order `R5-3` should write, with each step's refutation

Each step is a separate `/proc` write and a separate `cat`, so a wedge costs the
rest of a seating and not the step before it.

| step | write | expected | 🔴 refuted by | risk |
|---|---|---|---|---|
| **`I1`** | arm as today (`TCCNR` 29/28, `TC1DATA`) | as seating 11 | anything different | none — 量 twice |
| **`I2`** | **`TCIR` \|= bit 30**, `GIMR` bit 9 still 0 | after ≥ one TC1 period, `tcir_tc1ip = 1` **and** `gisr_tc1ip = 1` | both still 0 → § 3.2 is wrong too, and the block needs something else. **That is the informative outcome and it is worth the step** | 🟢 **none by construction**: `C5` measured that delivery needs the `GIMR` bit, and it is clear |
| **`I3`** | write 1 to `TCIR` bit 28 | `tcir_tc1ip` returns to 0 | it does not clear → D Table 25's write-1-to-clear is refuted. **`Q11` is testable again**, and it is this project's only test of that single-source claim | none |
| **`I4`** | `request_irq(25, …)` with a real handler | the handler runs; `/proc/interrupts` shows a rising count on 25 | no count → `L5`/`L6` are the wall, and § 4.3's `IRR1` reading is the next thing to take | 🔴 first real delivery. A handler that does not ack loops the board |

⚠️ **`I2`'s wait is ≥ 671.07 s** at the Linux rate (`CLK-22`), not 9.4 s. Shorten
it by loading a small `TC1DATA` for this cell — the period is the driver's to
choose and `2²⁷` was picked for the clocksource, not for this.

### 3.3.1 🆕 2026-09-04 (`R5-3a`): the four cells are implemented, and `I4`'s stop-if is enforced by the driver rather than by the card

`rtl819x-timer` **2.0** gives each gate its own `/proc` verb — `armirq`,
`ackip`, `reqirq`, `freeirq`, plus `period <bits>` for the wait above (`2²⁰` =
**5.24 s** at 200 kHz). One verb per gate is the § 3.3 design and not an
interface preference: folding `armirq` into `arm` would merge `I1` and `I2`, and
`I1`'s refutation condition is *anything different from seating 11* — which is
untestable if the thing being used as the control has changed.

🔴 **`reqirq` refuses with `-EPERM` unless the driver has itself watched `ackip`
take `TC1IP` from 1 to 0.** The reason is mechanical. 讀 `arch/rlx/bsp/irq.c`:
the ICTL `irq_chip`'s `.mask_ack` is `bsp_ictl_irq_mask`, which **masks and does
not ack the device**. 讀 `kernel/irq/chip.c` `handle_level_irq()`: after the
handler returns it unmasks unless `desc->status & IRQ_DISABLED`. So a handler
that cannot clear `TC1IP` re-triggers immediately and the board is gone.

**A stop-if on the bench card would be a rule whose correctness depends on the
experiment coming out the expected way**, and this repository has already ruled
that shape out once — `CLAUDE.md`'s `H601` pre-read row, where a containment
rule held only while the experiment behaved. The precondition is therefore
checked by the thing that would be destroyed.

🟢 **And the handler carries the same guard at run time**: clear `TC1IP`, read
it back, and if the bit is still set call `disable_irq_nosync()` — which sets
exactly the flag `handle_level_irq()` consults. An interrupt storm becomes
`irq_stuck=1` in `/proc`.

⚠️ **What neither guard does**, written here rather than discovered later: it
cannot save a handler that *hangs*; it cannot act before the first delivery, so
if merely unmasking wedges the part the guard never runs; and one `ackip` is
**n = 1** about a write-1-to-clear claim that has one source.

🟢 **`I2`'s wait also became free of an assumption.** The driver's `/proc` now
carries `irr0`–`irr3` and `Status`, so § 4.3's prediction and § 3.1's `L5`/`L6`
rows are readable in the same dump — 量 2026-09-04,
`config/rlxfw-initramfs.tsv`: this image carries **eleven** busybox symlinks and
`devmem` is not one of them, so **there was no other way to read them** and the
alternative was not a worse command, it was no command.

### 3.4 🔴 `R5-3` must not write `GIMR` bit 9 itself

讀, `arch/rlx/bsp/irq.c`:

```c
static void bsp_ictl_irq_mask(unsigned int irq)
{  REG32(BSP_GIMR) &= ~(1 << (irq - BSP_IRQ_ICTL_BASE));  }

static void bsp_ictl_irq_unmask(unsigned int irq)
{  REG32(BSP_GIMR) |=  (1 << (irq - BSP_IRQ_ICTL_BASE));  }
```

For IRQ 25 that is **exactly bit 9**. So the kernel already has an `irq_chip`
that owns `GIMR` bit 9, registered by `bsp_ictl_irq_init` with
`handle_level_irq`. A driver that writes the bit directly becomes a **second
writer of a register the irqchip owns**, and the two are not synchronised:
`bsp_ictl_irq_mask` is a read-modify-write with no lock.

**So `R5-3`'s `I4` is `request_irq(BSP_TC1_IRQ, …)` and nothing else.**
`PROGRESS.md`'s carried-forward `TMR-2` says *"`R5-3` … 必須在 handler 已裝好的
前提下直接寫 `GIMR` bit 9"* — the "handler installed first" half is right, the
"write `GIMR` directly" half is the thing to drop.

🟢 **And the dispatcher already knows about TC1**, 讀 `bsp_ictl_irq_dispatch`:

```c
pending = REG32(BSP_GIMR) & REG32(BSP_GISR);
if      (pending & BSP_UART0_IP) do_IRQ(BSP_UART0_IRQ);
else if (pending & BSP_UART1_IP) do_IRQ(BSP_UART1_IRQ);
else if (pending & BSP_TC1_IP)   do_IRQ(BSP_TC1_IRQ);
…
else { REG32(BSP_GIMR) &= (~pending); printk("Unknown Interrupt:%x\n", pending); … }
```

Two things follow. **(a)** No vendor patch is needed: a TC1 timeout with bit 9
unmasked reaches `do_IRQ(25)` on the existing path. **(b)** 🔴 The `else` branch
**masks the source it could not name**, so any *other* unhandled bit that
arrives at the same time is silently disabled and printed once. That is the
failure mode to look for in a boot log after `I4`.

### 3.5 What `bsp_timer_init` writes, and why the driver must not re-run it

讀, `arch/rlx/bsp/timer.c` — and it is the file that answers seating 11's
biggest surprise. **It is not `arch/rlx/kernel/rlx-time.c`**, which
`CORRECTIONS-block8.md` § 9 ④ named; that file is a 111-line shim whose
`time_init()` calls `bsp_timer_init()`.

```c
REG32(BSP_TCCNR) = 0;                                   /* before touching CDBR */
REG32(BSP_CDBR)  = (BSP_DIVISOR) << BSP_DIVF_OFFSET;    /* 1000 << 16 */
if ((REG32(BSP_REVR) & 0xFFFFF000) == BSP_RTL8196E)
        REG32(BSP_TC0DATA) = (((sys_clock_rate/BSP_DIVISOR)/HZ)) << 4;
else
        REG32(BSP_TC0DATA) = (((sys_clock_rate/BSP_DIVISOR)/HZ)) << BSP_TCD_OFFSET;
rlx_clockevent_init(BSP_TC0_IRQ);
REG32(BSP_TCCNR) = BSP_TC0EN | BSP_TC0MODE_TIMER;
REG32(BSP_TCIR)  = BSP_TC0IE;
```

with `BSP_SYS_CLK_RATE 200000000`, `BSP_DIVISOR 1000`, `HZ 100`,
`BSP_DIVF_OFFSET 16`, `BSP_TCD_OFFSET 8`, `BSP_REVR 0xB8000000`,
`BSP_RTL8196E 0x8196E000` — all 讀 from `bspchip.h`. Recomputed:

| | source says | device 量 (`TM-1`) |
|---|---|---|
| `CDBR` | `1000 << 16` = **`0x03E80000`** | **`0x03E80000`** |
| `TC0DATA` | `((200000000/1000)/100) << 4` = `2000 << 4` = **`0x00007D00`** | **`0x00007D00`** |
| `TCCNR` after init | `BSP_TC0EN\|BSP_TC0MODE_TIMER` = **`0xC0000000`** | **`0xC0000000`** |
| `TCIR` after init | `BSP_TC0IE` = **`0x80000000`** | **`0x80000000`** |

🟢 **Four registers, four exact matches.** `CORRECTIONS-block8.md` § 1's
refutation of `Q2` is now explained from source rather than observed.

🟢 **And `BSP_TCD_OFFSET`'s 8 is not a contradiction — it is the branch not
taken.** The shift is 4 because a **runtime** test on `BSP_REVR` selects it,
and this device's `BSP_REVR` reading is already in the repository: `REG-29` /
`CPU-32`, 量 2026-08-24, **`0x8196E001`**; `0x8196E001 & 0xFFFFF000` =
`0x8196E000` = `BSP_RTL8196E`. A 2026-08-24 reading closes a 2026-09-04 source
question, and `CLK-19`'s `N`-vs-`N+1` question is untouched by it.

🔴 **Two plain assignments to watch.** `REG32(BSP_TCCNR) = BSP_TC0EN|…` and
`REG32(BSP_TCIR) = BSP_TC0IE` are `=`, not `|=`. They run once at init, so
there is no live race with an armed TC1 — but any code path that re-runs
`bsp_timer_init` disarms TC1 silently, and `R5-3`'s clockevent must not be one.

---

## B. What `R6` needs

### 4.1 `GIMR` / `GISR`, the full bit map

讀, `bspchip.h` (`_IE` in `GIMR`, `_IP` in `GISR`, same positions):

| bit | source | bit | source |
|---:|---|---:|---|
| 0 | `PCIB0TO` | 15 | `SW` (switch core) |
| 1 | `PCIB1TO` | 16 | `GPIO_ABCD` |
| 2 | `LBCTMOm0` | 17 | `GPIO_EFGH` |
| 3 | `LBCTMOm1` | 18 | `NFBI` |
| 4 | `LBCTMOs` | 19 | `PCM` |
| **8** | **`TC0`** | 20 | `CRYPTO` |
| **9** | **`TC1`** | 21 | `PCIE` *(header comment: "shall be 22")* |
| 10 | `USB_H` | 22 | `PCIE2` |
| 11 | `OTG` | 23 | `GDMA` |
| 12 | `UART0` | 26 | `I2S` |
| 13 | `UART1` | | |
| 14 | `PCI` | | |

🟢 **The device reading decodes exactly, in both directions.** 量 seating 11,
under Linux, `gimr = 0x00209100`:

```
bit  8 TC0_IE   | bit 12 UART0_IE | bit 15 SW_IE | bit 21 PCIE_IE
0x100 + 0x1000 + 0x8000 + 0x200000                  = 0x00209100
```

and each of the four has its source line, with the `.config` symbol that turns
it on: `rlx_vec_irq_init` assigns `BSP_TC0_IE | BSP_UART0_IE`, then
`CONFIG_RTL_819X=y` adds `BSP_SW_IE`, and `CONFIG_RTL8192CD=y` with
`CONFIG_RTL_8196E=y` adds `BSP_PCIE_IE`. **Every bit that is on is accounted
for, and every OR-in that is absent has its symbol absent from the `.config`**
— `CONFIG_USB`, `CONFIG_SERIAL_RTL8198_UART1`, `CONFIG_RTL_NFBI_MDIO`,
`CONFIG_RTK_VOIP`, `CONFIG_DWC_OTG`, `CONFIG_RTL_8197D` are all unset, and
bits 10, 13, 18, 19, 11, 22 are all 0.

⚠️ `GIMR` is written by **three** places in an `arch/rlx` boot:
`bsp_irq_init` zeroes it, `rlx_vec_irq_init` **assigns** it (not `|=`), and
`bsp_ictl_irq_unmask` sets single bits later. The assignment is why nothing
before it survives.

### 4.2 `IRR0`–`IRR3`: eight 4-bit routing-select fields each

讀, `bspchip.h`. Each nibble names the destination for one ICTL source; the
vendor's `_RS` macros give either `BSP_IRQ_CASCADE` (2) or a specific IRQ
number. `bsp_irq_init` writes all four, unconditionally, after the three
domains are initialised.

| register | nibble 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 | **value** |
|---|---|---|---|---|---|---|---|---|---|
| `IRR0` | LBCTMOm2 | LBCTMOm1 | SPEED | LBCTMOs0 | LBCTMOm0 | OCPTMO | *(none)* | PCIB0TO | **`0x22222222`** |
| `IRR1` | SW=12 | *(none)*=2 | UART1=2 | UART0=2 | OTG=15 | USB_H=10 | **TC1=2** | **TC0=13** | **`0xC222FA2D`** |
| `IRR2` | GDMA | PCIE2=14 | PCIE=11 | SECURITY | PCM=9 | NFBI=15 | GPIO_EFGH | GPIO_ABCD | **`0x2EB29F22`** |
| `IRR3` | PTM | LBCTMOs2 | LBCTMOs1 | PKT | SPI | 🔴 **absent** | SAR | DMT | **`0x22222022`** |

The four values are **computed from the header's own macros by a script**, not
transcribed.

🔴 **`BSP_IRR3_SETTING` has no `<< 8` term.** Bits 11:8 are therefore written as
`0`, whatever source occupies that field. If `0` means *unrouted*, the vendor
BSP silently disables one ICTL source on every boot; if it means *CPU IRQ 0*,
it routes it somewhere nothing handles. **Undetermined**, and it is a defect in
the vendor's macro rather than a question about the silicon.

### 4.3 🔴 The routing has never been read under Linux, and the two states disagree completely

`SPEC.md` `REG-03` holds one reading of `IRR1`, **at the loader prompt**:
`0x30050004`. Nibble by nibble, low to high:

```
loader  量  0x30050004 :  4  0  0  0  5  0  0  3
Linux   讀  0xC222FA2D : 13  2 10 15  2  2  2 12
```

**Not one nibble agrees.** `bsp_irq_init` overwrites all four registers, so
under Linux `IRR1` should read `0xC222FA2D` — and nothing has ever looked.

🟢 **One command settles it, and it is free**: `DW B8003008 4` at the loader
prompt reads all four (`LDR-07` carries four words), and the same four addresses
read under Linux give the other state. **Prediction, written now:** at the
prompt `IRR0`–`IRR3` are whatever the loader left, with `IRR1 = 0x30050004`
re-confirming `REG-03`; under Linux they are `22222222 / C222FA2D / 2EB29F22 /
22222022`. **Refuted by** any differing word on the Linux side, which would mean
either that this is not the `bspchip.h` the running image was built from — it
is, § 6.1 — or that something writes `IRR` after `bsp_irq_init`.

⚠️ **The `_RS` field's encoding is 未定 and this file does not guess it.** The
vendor's own values span 2 and 9–15, so it is not a 3-bit CPU-line selector; a
4-bit *Linux IRQ number* reading fits `BSP_TC0_RS = 13` and `BSP_USB_H_RS = 10`
but makes `BSP_IRQ_CASCADE = 2` mean "CPU IRQ 2", which is consistent. The
loader's `4` in TC0's nibble fits neither. **The experiment that decides it is
the Linux-side read above**, because it pairs a known intent with a known
outcome on one register.

### 4.4 Dispatch, top to bottom

讀, `arch/rlx/bsp/irq.c` and `arch/rlx/kernel/irq_vec.c`:

```
exception  ->  bsp_irq_dispatch()
                 pending = read_c0_cause() & read_c0_status()
                 IP2 -> bsp_ictl_irq_dispatch()
                          pending = REG32(BSP_GIMR) & REG32(BSP_GISR)
                          -> do_IRQ(16 + n)
                 IP0 -> do_IRQ(0)     IP1 -> do_IRQ(1)
                 else spurious_interrupt(SPURIOS_INT_CPU)

vectored   ->  rlx_do_lopi_IRQ(offset)          [write_lxc0_intvec(&rlx_vec_dispatch)]
                 pending = read_lxc0_ecause() & read_lxc0_estatus() & EST0_IM
                 bit (offset+16) -> do_IRQ(8 + offset)
                 else spurious_interrupt(SPURIOS_INT_LOPI)
```

⚠️ **`bsp_irq_dispatch` tests `IP2` first and only then `IP0`/`IP1`**, so the
ICTL cascade has priority over CPU IRQ 0 and 1 by source order, not by hardware.
Nothing in `arch/rlx` gives `IP3`–`IP7` a path at all: the commented-out block
right beneath it would have unmasked `IP2`–`IP6` in `Status`, and it is
commented out.

---

## 5. What this file does not establish

1. **No interrupt of mine has ever been delivered.** `GIMR` was read in all
   fourteen dumps of seating 11 and written in none.
2. **`IRR0`–`IRR3` have never been read under Linux**, and `IRR0`/`IRR2`/`IRR3`
   have never been read at all. § 4.3 is a prediction.
3. **`Status`/`ESTATUS` have never been read on this device.** `L6` and `L7` in
   § 3.1 are 推 from the fact that the vendor tick runs.
4. **The `_RS` encoding is 未定** (§ 4.3).
5. **`IRR3` bits 11:8** are written as zero by a macro that skips them, and what
   sits in that field is unknown (§ 4.2).
6. **§ 3.2's correction is an argument from a second reading, not a new
   measurement.** It rests on `RUNSHEET` `C5` being about the same latch
   mechanism one bit along. `I2` is what turns it into a measurement.
7. **The `lxc0` register file has never been probed**, and `LXCP0_CCTL $20` —
   a cache-control register reached the same way — is a separate thread from
   the CP3 `CCTL` this project has already used.

---

## 6. Method: three of these facts were nearly missed, and one of them flipped

### 6.1 🔴 `grep -r` over `arch/rlx` cannot see the BSP, and it cost a wrong conclusion in this session

`arch/rlx/bsp` is a **symlink** (`-> ../../../target/bsp -> boards/rtl8196e/bsp`)
and GNU `grep -r` does not follow symlinked directories. 量 today, on the
`rtl819x-toolchain` drop:

| | |
|---|---:|
| files `find` reaches without following | 321 |
| files `find -L` reaches | **334** |
| files `grep -rl ''` reaches | 321 |
| files `grep -Rl ''` reaches | **333** |

**The 13 invisible files are the entire board port** — `irq.c`, `timer.c`,
`setup.c`, `prom.c`, `serial.c`, `pci.c`, `kgdb.c`, `bspchip.h`, `bspcpu.h`,
`bspinit.h`, `Makefile`, `vmlinux.lds.S`, `modules.order` — that is, every fact
in this file.

🟢 **`notes/kernel-build.md` § 10 already carried this, and `hazlint-objs.py`
already guards it** (`-L`, plus a `Q1` case requiring the sweep to reach
`arch/rlx/bsp/setup.o`). This is a *new instance in a different instrument*:
a `grep -r` in this session returned **0 hits** for `REG32(BSP_IRR` over the
whole tree and the conclusion drafted from it — *"the kernel never programs the
routing"* — is the exact opposite of the truth. `grep -R` finds four writes.

⚠️ **And the two counts above are both right.** `find -L` says 334, `grep -R`
says 333, because `bsp/modules.order` is **0 bytes** and `grep -l ''` cannot
list a file with no lines. § 10.1's table counts grep and is correct; its prose
counts the filesystem and is correct. Recorded so the pair is not "fixed" into
agreement.

### 6.2 The CP3 hypothesis was refuted by assembling both mnemonics

§ 1.1. `mflxc0` *looked* like the `mfc3` this project already measured
reachable, which would have made an existing result carry over. It does not.
The check cost one `rsdk-linux-as` invocation.

### 6.3 The contradiction that was a branch

`BSP_TCD_OFFSET 8` against a measured shift of 4 read as a source-versus-device
conflict for about ten minutes. It is an `if`/`else` selected at runtime, and
the repository already held the `BSP_REVR` reading that says which arm is taken
(§ 3.5). **A constant with a consumer is not a claim about this part until you
have read the consumer.**

### 6.4 Every number above was re-derived by a script, and the script's first run failed on itself

Sixty-seven checks re-compute each figure in this file out of `TM-5b2.log`,
`bspchip.h` and the built `.config` — **never by re-reading the prose**, which
is the only way a transcription error can be caught by anything but a second
pair of eyes.

🔴 **Its first run reported `BSP_SYS_CLK_RATE` as 33,860,000.** A plain
`#define BSP_SYS_CLK_RATE` regex matches this line first:

```c
#ifdef CONFIG_FPGA_PLATFORM
//#define BSP_SYS_CLK_RATE	(33860000)      //33.86MHz
#define BSP_SYS_CLK_RATE	(27000000)      //27MHz
#else
#define BSP_SYS_CLK_RATE	(200000000)     //HS1 clock : 200 MHz
#endif
```

— a **commented-out** definition, inside the arm the build does not take.
Had the checker been trusted, it would have "refuted" § 3.5's exact match. The
parser now strips comments, keeps **every** surviving definition of a name, and
**refuses** a name that has more than one unless the caller says how many to
expect; `P1`–`P3` are the three cases that pin it, and `P3` asserts from the
built `.config` that `CONFIG_FPGA_PLATFORM` is unset so the `#else` arm is the
live one. **A checker that reads a header with a regex is a header parser, and
a header parser that does not know about `#if` is wrong by default.**
