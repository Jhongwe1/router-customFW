# The switch core on this part, and rlxfw's driver for it

**What this file owns**: the RTL8196E switch-core register map as rlxfw has
derived it, the reset path, the dumb-state configuration `R6-2` writes, and
what `rtl819x-switch.c` does and does not claim. It does **not** own the
CPU-port DMA path — that is `R6-3` and it will get its own file. It does not
own the PHY or the loader's access to it (`docs/loader-phy-and-switch.md`),
and it does not own the gate's position (`PROGRESS.md`).

Marks: **量** measured on this device, **讀** read out of source or a dump,
**推** inferred and pending a measurement.

---

## 1. Why the register population had to be re-derived

`SPEC.md` `NET-21` derives this project's switch-register population from
**48 `lui …,0xbb80` sites in the loader**, converging on **13 distinct
addresses**. Every switch reading this project has taken, in both states, is
inside those 13.

🔴 **That population is one agent's behaviour, and it is blind to everything
that agent ignores.** 量 2026-09-17, `tools/hdrcensus.py` over
`rtl865xc_asicregs.h` under `-D CONFIG_RTL_8196E`: the header declares **546**
addresses; this repository has ever printed **69**; **477 (87.4 %)** it has
never printed at all. In the ALE block alone — `0xBB804400`–`0xBB8044FF` —
**19 of 21** have never been printed.

Three of those are named directly by `R6-2`'s own one-line definition:

| register | address | what it is | ~~why the loader never touched it~~ 🔴 **the premise is refuted for `MSCR` — § 8.9** |
|---|---|---|---|
| **`MSCR`** | `0xBB804410` | Module Switch Control — the L2/L3/L4 mode and both ACL enables | ~~the loader does no forwarding; it never leaves L2~~ 🔴 **the loader DOES touch it**: 讀 `0x80403948`–`0x80403950` in this unit's own stage 2 writes the literal `1`. The *reason* survives — `MSCR = 1` is `Mode_enL2` alone — but *never touched* is false, and 量 `bench/2026-09-19/X3-L4410` reads `00000001` at the prompt, which is that literal |
| **`VCR0`** | `0xBB804A00` | VLAN Control — holds `En1QtagVIDignore` | the loader sends no tagged frames |
| `SWTCR1` | `0xBB80441C` | the stateful-inspection (SPI) enables | likewise |

`tccensus` had to state the same shape one level down — *a population derived
from the record cannot see a fact measured and never written down*. This is
that sentence with "the record" replaced by "the loader's instruction stream".

⚠️ **`hdrcensus`'s coverage number is an upper bound on knowledge, not a lower
one**: it asks *has any committed file ever printed this address*, and a card
that merely NAMES an address counts. The true "read on the die" count is
smaller than 69.

---

## 2. The blocks, 讀, with their bases re-derived rather than copied

`SWCORE_BASE = REAL_SWCORE_BASE = 0xBB800000`
(`rtl865xc_asicregs.h:147`, `:171` — the `#else` of the three
`RTL865X_MODEL_*` host simulators, none of which is defined in a board build).

| block | define | address | line |
|---|---|---|---|
| switch MAC config | `SWMACCR_BASE` | `0xBB804000` | `:995` |
| per-port config | `PCRAM_BASE` | `0xBB804100` | `:1132` |
| misc / reset | `SWMISC_BASE` | `0xBB804200` | `:1399` |
| address-lookup engine | `ALE_BASE` | `0xBB804400` | `:1478` |
| VLAN | — | `0xBB804A00` | `:2299` |
| table access | `TACI_BASE` | `0xBB804D00` | `:195` |

🟢 **The base chain validates against a measurement.** `MEMCR` is declared as
`0x34 + SWMISC_BASE` (`:1447`); resolving that gives `0xBB804234`, which is
**the address measured at the bench** (`bench/2026-09-17b/C3-SW234`). Likewise
`SWMACCR_BASE` resolves to `0xBB804000` = the measured `MACCR`, and
`TACI_BASE` to `0xBB804D00` = the measured `SWTACR`. Three independent
agreements between a symbolic resolution and a reading taken before the
resolution existed.

---

## 3. The reset path — and it is why `R6-2`'s DoD is satisfiable

`PROGRESS.md` `D2` requires *a register read-back whose value differs from
**reset***. `bench/2026-09-17b/PREDICTIONS-B25-block24.md:96` recorded, before
this driver existed, that this is *"not satisfiable today: none of the eight
has a known reset value"*.

🟢 **It is satisfiable, because this part has a documented software reset and
the vendor's own bring-up asserts it.**

讀 `rtl865xc_asicregs.h:1402`, `:1435`, `:1442`–`:1444`:

| | | |
|---|---|---|
| `SSIR` (alias `SIRR`) | `0x04 + SWMISC_BASE` | **`0xBB804204`** |
| `SwitchFullRst` / `FULL_RST` | `(1 << 2)` | *"Reset all tables & queues"* |
| `SwitchSemiRst` / `SEMI_RST` | `(1 << 1)` | *"Reset queues"* |
| `TRXRDY` | `(1 << 0)` | *"Start normal TX and RX"* |

讀 `rtl865x_asicCom.c:2002-2040`, `FullAndSemiReset()`, the `CONFIG_RTL_8196E`
arm — **this board's arm**:

```c
REG32(SIRR) |= FULL_RST;              mdelay(300);
REG32(SYS_CLK_MAG) |=  CM_PROTECT;
REG32(SYS_CLK_MAG) &= ~CM_ACTIVE_SWCORE;   /* switch core clock OFF */
                                      mdelay(300);
REG32(SYS_CLK_MAG) |=  CM_ACTIVE_SWCORE;
REG32(SYS_CLK_MAG) &= ~CM_PROTECT;    mdelay(50);
```

`SYS_CLK_MAG = SYSTEM_BASE + 0x0010 = 0xB8000010` (`:3521`);
`CM_ACTIVE_SWCORE = (1<<11)`, `CM_PROTECT = (1<<27)` (`:3524`, `:3525`).

🔴 **On the 8196E the vendor does not trust `FULL_RST` alone** — it follows it
with a 650 ms clock-gate cycle of the switch core. Whether the extra 650 ms
changes any register is **unmeasured by any source in this repository**, which
is why the driver carries both recipes and the card compares their dumps.

### 3.1 The prediction for the post-reset state, and it has a documentary source

🟢 讀 `rtl865x_asicCom.c:946-1115`, `rtl8651_clearRegister()` — 82 writes with
literal values, including **`MSCR = 0`**, `VCR0 = 0`, `VCR1 = 0`,
`PVCR0..4 = 0`, `SWTCR0 = 0`, `SWTCR1 = 0`, `PBVCR0/1 = 0`, and
`PCRP0..4 = (1 | MacSwReset)` = `0x9` each followed by
`TOGGLE_BIT_IN_REG_TWICE(PCRPn, EnForceMode)`.

🔴 **It has no caller.** 量: `grep -rn clearRegister` over the whole vendor
Ethernet tree returns **three** hits — the prototype in the `.h`, the doc
comment, and the definition. So this is *what Realtek thinks blank looks
like*, not what the silicon reads after `FULL_RST`.

**That makes the block falsifiable in both directions, which is the point:**

* if `FULL_RST` leaves those registers at `clearRegister`'s values, then
  `MSCR`/`VCR0`/`PVCR*`/`SWTCR*` all read **0** after reset and every one of
  the driver's nine dumb writes moves its register — `D2` holds with a
  documentary prediction behind it;
* if `FULL_RST` leaves them alone, **the positive control on the reset fires**
  (`S1 == S0'` everywhere) and the block is void with its reason, which is
  also a result.

🔴🔴 **量 2026-09-19: NEITHER arm happened, and a disjunction written as
exhaustive was not.** `bench/2026-09-19/C27-RST1`, the `cat` taken immediately
after `reset full`: `MSCR` `00000001`, `VCR0` `000001FF`, `SWTCR0` `00080000`,
`SWTCR1` `00000200` — **none of them zero**, so `clearRegister()`'s values are
not what `FULL_RST` leaves; and `PVCR0`–`PVCR3` went `00080008` → `00010001`,
so it did not leave them alone either. `FULL_RST` leaves a **third** state, and
the two arms above between them could not name it. § 8.5 has the numbers.
🟢 **The one prediction in this section that did hit is the datasheet's.**
`PCRP0` after `FULL_RST` reads **`007F0038`** — top half `0x007F`, exactly what
Table 64's assembled per-bit defaults predict (量, same capture). The leaked
draft is corroborated on the one register it could be corroborated on.

🟢 **And there is an independent check on exactly one register.** The draft
datasheet's Table 64 gives per-bit defaults for `PCRP0`–`PCRP4` which assemble
to `0x007F` in bits 31:16, and this unit reads `PCRP0 = 0x007F0039` (量,
`bench/2026-08-24b/E9b.log`). So **after `FULL_RST`, `PCRP0`'s top half is
predicted to be `0x007F`.** If it is, "full reset as a reset baseline" is
validated against a documentary source on the one register that has one. If it
is not, the method is refuted. ⚠️ The datasheet is a leaked draft and is
watermark-scrambled; this is a 讀 of one source, and it is used as a
cross-check rather than as the baseline itself.

### 3.2 The limit, stated rather than left to be found

`FULL_RST` is a **soft** reset of "tables & queues". It is **not** proven
identical to a power-on reset. What `R6-2` can support is *differs from the
state this part's own documented full reset leaves it in, measured on this
die* — strictly stronger than *differs from loader-state*, strictly weaker
than *differs from the power-on default*. Reaching the third would need the
switch's state read before the loader runs, which on this board nothing can do.

---

## 4. The fields that matter, 讀, and the branch that would have got them wrong

🔴 **`rtl865xc_asicregs.h` defines `PCRP`'s bit positions TWICE**, under
`#if defined(CONFIG_RTL_8196C) || … || defined(CONFIG_RTL_8196E)` (`:1168`)
and `#else` (`:1274`), **with different values** — `EnLoopBack` is bit **7** in
the first and bit **10** in the second, `EnForceMode` bit 25 against bit 23.
A `grep`-shaped census takes both and produces a field map that is wrong for
whichever part you are holding. `tools/hdrcensus.py`'s `K3`/`K4` are that pair
and a conditional-blind implementation passes exactly one of them.

### `PCRP` — per-port configuration, the 8196E arm

| bit(s) | name | |
|---|---|---|
| 31 | `BYPASS_TCRC` | |
| 30:26 | `ExtPHYID` | |
| 25 | `EnForceMode` | |
| 24 | `PollLinkStatus` | |
| 23 | `ForceLink` | |
| 22:18 | `FrcAbi_AnAbi_sel` | force params if `EnForceMode`, else N-way advertise |
| 17:16 | `PauseFlowControl` | |
| 11:9 / 8 | `BCSC_Types` / `ENBCSC` | broadcast storm control |
| **7** | **`EnLoopBack`** | *"Enable MAC-PHY interface Mii Loopback"* |
| 6 | `DisBKP` | |
| 5:4 | `STP_PortST` | 0 disable / 1 blocking / 2 learning / 3 forwarding |
| 3 | `MacSwReset` | **0 = reset state, 1 = normal** |
| 2:1 | `AcptMaxLen` | 0=1536 1=1552 2=9K 3=16K |
| 0 | `EnablePHYIf` | |

🟢 **The decode of the measured value closes with no leftover.**
`PCRP0 = 0x007F0039` (量) gives `EnForceMode`=0 so bits 22:18 are the N-way
advertise set, and **all five are set**; `PauseFlowControl`=3; no storm
control; `EnLoopBack`=0; **`STP_PortST`=3 (FORWARDING)**;
**`MacSwReset`=1 (normal)**; `AcptMaxLen`=1536; **`EnablePHYIf`=1**. Every
field lands on a value a working port would have, which is itself the evidence
that this is the right branch — the `#else` map puts `EnablePHYIf` and
`MacSwReset` elsewhere and the decode would not close.

### `MSCR` — the acceleration master switch (`:1553`–`:1562`)

`DisChk_CFI` 9 · `EnRRCP2CPU` 7 · `NATTM` 6 · `Enable_ST` 5 ·
`Ingress_ACL` 4 · `Egress_ACL` 3 · `Mode` 2:0 with
`Mode_enL2 = 1<<0`, `Mode_enL3 = 1<<1`, `Mode_enL4 = 1<<2`.

🟢 **`MSCR = 0x00000001` is L2-only with no ACL, no spanning tree, no L3/L4.**
That is "no acceleration", exactly, in one write.

⚠️ 讀: `RTL_HW_NAPT` is gated on 8198/8196CT/8198T/819XDT and **not** on
8196E, and there is no `rtl865x_asicL4.S` in the `96E/` directory — so
hardware NAPT is not compiled for this part at all. The `MSCR` write is
therefore the whole of "no acceleration" rather than one of several.

### `VCR0` — VLAN control (`:2339`–`:2391`)

bit **31** `En1QtagVIDignore` *"Enable 1Q vlan unware"* · bits 26:9
`Pn_AcptFType`, two per port, 0 = admit all frames · bits 8:0 `EnVlanInF`,
per-port ingress filtering.

### `SWTCR0` — switch table control (`:1570`–`:1598`)

`STOP_TLU_STA` 19 (RO) · `STOP_TLU` 18 · `LIMDBC` 17:16 (0 by VLAN, 1 by port,
2 by MAC) · `EnUkVIDtoCPU` 15 · `NAPTF2CPU` 14 · `MultiPortModeP` 13:5 ·
`WANRouteMode` 4:3 · `EnNAPTAutoDelete` 2 · `EnNAPTAutoLearn` 1 ·
`EnNAPTRNotFoundDrop` 0.

🟢 Decoding the two measured states gives a meaningful difference:
loader `00080000` → `LIMDBC` = **0 = by VLAN**; Linux `00097DE0` → `LIMDBC` =
**1 = by port**, with `NAPTF2CPU` set and `WANRouteMode` = forward.

---

## 5. 🟢 `PVCR` — the word split, and it closes `NET-33` 殘留 ①

讀 `:2392`–`:2430`. The register packs **two ports per 32-bit word**, and the
header names every field individually:

```
bits 11:0  PVID of the even port     bits 14:12  its priority
bits 27:16 PVID of the odd port      bits 30:28  its priority

PVCR0 0xBB804A08 = {P0,P1}   PVCR1 0xBB804A0C = {P2,P3}
PVCR2 0xBB804A10 = {P4,P5}   PVCR3 0xBB804A14 = {P6,P7}
PVCR4 0xBB804A18 = {P8}
```

🔴 **Two corrections to `docs/loader-phy-and-switch.md` § *`PVCR` is per-port
PVID*.** ① It calls the field **16-bit**; it is **12 bits** with three bits of
priority above. Nothing in the readings changes — every priority reads 0 —
but the description is wrong and would mislead the first time a priority is
set. ② It treats **six** addresses as `PVCR`. The sixth, `0xBB804A1C`
(`00021B74`), is **`PBVCR0`**, the Protocol-Based VLAN Control Register
(`:2306`), a different register. The negative-control logic in that section
survives; the identification does not.

### Decoding the measured Linux-state values, and the port map that falls out

量, block 26: `00090009` `00090009` `00010008` `00010001` `00000009`
→ **P0=9 P1=9 P2=9 P3=9 P4=8 P5=1 P6=1 P7=1 P8=9.**

🔴 **`SPEC.md` `NET-04` says the WAN is port 0 on vid 8, and this says port 4.
Both are 量 and they are not in conflict — they are two different states.**

量, `grep` over all of `bench/` and `upstream/dumps/uart-boot.log`:

| interface | vendor firmware | this image (×104 captures) |
|---|---|---|
| `eth1` (WAN, vid 8) | `Member port 0x1` → port 0 | **`Member port 0x10` → port 4** |
| `eth0` | `0x10` → port 4 | `0x1` → port 0 |
| `eth2` | `0x8` → port 3 | `0x2` → port 1 |
| `eth3` | `0x4` → port 2 | `0x4` → port 2 |
| `eth4` | `0x2` → port 1 | `0x8` → port 3 |

**A 4−n mirror on all five**, and `RLXFW-ID0=BB684EB0` in that seating's own
capture proves block 26 ran under rlxfw and not under the vendor firmware.
`NET-33`'s own ⚠️ — *`NET-13` measured this kernel's netdev↔port map as the
mirror of the vendor's, so `NET-04`'s port numbers do not carry across* — is
exactly right, and this is the reading that confirms it.

🟢 **So the `PVCR` decode has a second source that shares no code with it**: a
register's bit fields on one side, a string the driver's own init prints on
the other.

---

## 6. What `rtl819x-switch.c` is, and what it refuses to claim

`config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-switch.c`, `subsys_initcall`,
`/proc/rtl819x-switch`. Built by `MK9` in `config/rlxfw-marks.tsv`.

**Four states, not two**, which is what makes `D2` a measurement:

| | state | how |
|---|---|---|
| S0 | the loader's | 量 already, block 24 |
| **S0′** | after early kernel init, before the vendor NIC driver | latched at `subsys_initcall`. ~~**Nothing has ever measured this state.**~~ 🔄 **量 2026-09-19 — § 8.3** |
| S1 | after `FULL_RST` | the `reset` verb |
| S3 | the dumb configuration | the `dumb` verb |

**Controls, written before the verbs were run once:**

* **positive control on the reset** — at least one register must satisfy
  `S1 ≠ S0′`, or `FULL_RST` did nothing and the block is void;
* **negative control on the writes** — a register the driver never writes must
  satisfy `S3 == S1`;
* **round trip** — `restore` must bring `S0′` back. This part already has one
  register that does not read back (`WDTCLR`, `SPEC.md` `FW-52`), so this is a
  measured hazard and not a hypothetical;
* **read-path control** — `CVIDR` at `0xBB804200` is a chip version id and must
  read the same constant in every phase. ⚠️ Its value is **未定** on this die,
  so on the first seating it is a *negative* control only and becomes a
  positive one from the second seating onward.

**The dumb configuration**, nine writes:

| register | address | value |
|---|---|---|
| `MSCR` | `0xBB804410` | `0x00000001` |
| `VCR0` | `0xBB804A00` | `0x80000000` |
| `PVCR0`–`PVCR3` | `0x4A08`–`0x4A14` | `0x00010001` each |
| `PVCR4` | `0x4A18` | `0x00000001` |
| `SWTCR0` | `0x4418` | read-modify-write, clearing bits 15, 14, 4:3, 2, 1, 0 |
| `SWTCR1` | `0x441C` | `0x00000000` |

~~⚠️ **Eight of those nine registers have no prior reading on this die at
all**~~ 🔴 **Wrong by a factor of four when it was written, and zero now.**
量 2026-09-19 (`bench/2026-09-19/CORRECTIONS-block27.md` F3, which found the
same error in `docs/KNOWN-ISSUES.md:777` and traced this line to it):
`SWTCR1` = `00000200` and `PVCR1`/`2`/`3` = `00080008` were already in
`bench/2026-09-17b` and in `SPEC.md`, so it was **two of nine** — `MSCR` and
`VCR0` — and after this seating's `X3`/`X4` it is **zero of nine**. 推 the
mechanism: `hdrcensus` searches committed files for an 8-hex token, and a
`DW <base> 4` window labels only its base, so the other three words of every
such window are invisible to it. **The sentence the count was supporting still
holds** — each write is preceded by a read of the same register in the same
verb and the read is the measurement rather than a courtesy.

### What it does not do

1. **It writes nothing at boot.** Every write is behind a verb *and* behind an
   explicit runtime unlock, so `n_writes` reads 0 on a boot capture and that
   is a measurement rather than a promise.
2. It does not touch the rings, the interrupt or any `net_device` — `R6-3`.
3. **It does not write the VLAN table.** 讀: on the 8196E the table is a
   16-entry CAM with its own `vid` field at `0xBB060000 + idx*32`, reached
   through the TACI block, which is a protocol and not a register write. 推
   that `En1QtagVIDignore` makes the table irrelevant to a dumb switch; that
   推 is untested and the table is left alone until it is. 🔄 1.6's `vlan` writes it (§ 21.4).
4. 🔴 It cannot promise that a single read of a switch **table** is
   trustworthy. 讀 `96E/rtl865x_asicBasic.S:1043-1211`: the vendor's own
   `_rtl8651_readAsicEntry` reads a table entry **twice into two buffers,
   compares all eight words, and retries up to ten times** if they differ.
   ⚠️ That is about the indirect TABLE path, **not** about the direct register
   reads this driver makes — but nothing here has established that the direct
   path is free of the same problem, and the `snap`/`diff` verbs exist partly
   so a register can be sampled twice.

---

## 7. The CPU interface's control bits — MOVED to `notes/nic-driver.md` § 8

**This section has moved and this is the pointer it left.** It read *"This section is in the wrong file and says so … It moves the day `R6-3`'s driver note appears."* That note appeared on 2026-09-19 (seating 28) and the body went with it, verbatim, subheadings renumbered 7.x → 8.x.

⚠️ **THREE of its readings were refuted by the seating that moved it** — this line first said two, and the third was found by a reviewer asked to disagree with the write-up rather than by any checker. The refutations live in `notes/nic-driver.md` § 4 rung 0, § 3.4 and § 1: ① `SWINTSET` does not raise an interrupt on this die even with the engine on and the mask open; ② the pkthdr stride is 24 rather than the 32 its own § 7.2 left undetermined; ③ **the vendor's NIC driver does NOT own IRQ 12 in this arrangement** — 讀 `rtl_nic.c:4227` puts its `request_irq` in `re865x_open()`, not probe, and 量 `irq_rc 0` says the line was unclaimed. A fourth is weakened rather than refuted: the 推 that `CPUIISR` bit 0 is the software-interrupt pending bit has no source behind it at all. The moved text is not edited to agree with any of them.

# 8. 2026-09-19 (seating 27) — the driver ran

**Everything in this section is 量 on this die unless it is marked otherwise.**
The record of the seating is `bench/2026-09-19/CORRECTIONS-block27.md`; the
captures are `bench/2026-09-19/C1`–`C41` and `X0`–`X24`. Where a number below
disagrees with that file, the disagreement is stated and the recount is shown,
because a count nobody can redo is not a measurement.


## 8.1 What ran

`check-predictions`: **41 of 41** captures came after the prediction, 0 did not.
`looprun --mode bench --skip S2,S3` closed reset → rescue → upload → boot →
assert in **39.24 s** with nine assertions. The boot capture is
**1,759 bytes against a prediction of 1,759** (量 `wc -c r6sw1-boot.log`), and
the id the build computed is the id the board printed:
**`RLXFW-ID0=F681F8E0`**.

```
RLXFW-SW0 · SW1=81964000 · SW2=00000001 · SW3=00000200 · SW4=000001FF
SW5=00080008 · SW6 · RLXFW-ID0=F681F8E0
```

`SW6`, not `SW6-NOPROC` — the `/proc` entry was created.

## 8.2 The read path, before anything is read from it

`SW1` is `boot_cvidr`, latched by `__raw_readl()` at `subsys_initcall`. It reads
**`81964000`**, which is byte-identical to the loader's `DW BB804200` read four
times across a power cycle (`X2`, `X6`, `X7`, `X18`). The live `CVIDR` column
and the slot-0 column of every `cat` read it again. § 6's read-path control was
declared a *negative* control until a second seating gave it a value; **this is
that seating, and it is a positive control from here on.** Two code paths that
share nothing agree on a register nobody writes. Every reading below is
licensed by this one.

## 8.3 `S0′` — the state § 6 said nothing had ever measured

`C9-SW0` prints all 37 registers twice: the live value and the slot-0 latch
taken at `subsys_initcall`. The four registers the boot marks carry are
**byte-identical to loader state**: `MSCR` `00000001`, `SWTCR1` `00000200`,
`VCR0` `000001FF`, `PVCR0` `00080008`.

🔴 **That is not "early init does not touch the switch".** `PCRP0`–`PCRP4` read
`nn7F0038` at `S0′` and `nn7F0039` at the loader prompt (量 `C1-L4104`,
`C2-L4114`) — **`EnablePHYIf`, bit 0, is clear at `S0′` and set at the
prompt.** `upstream/BENCH-LOG.md:4770-4795` recorded the same transition in
August — *"At rest under the loader: `007F0039`… **After `J`: all `...0038`**"*
— three weeks and several power cycles earlier, on a different project's
capture.

🟢 **And the instruction that does it is in the loader, not in the kernel.**
讀, this unit's own stage 2 (`sha256 f88869d1…c9c1b4ee`, load base
`0x80400000`), the `J` command handler at `0x8040925C`, its last act before
`jalr s0`:

```
804092dc  lui v1,0xbb80         ; (delay slot of the bne above) v1 = 0xBB800000
804092f4  ori a0,v1,0x4104      ; PCRP0
804092f8  lw  v0,0(a0)
804092fc  li  a1,-2             ; ~1  == ~EnablePHYIf
80409300  and v0,v0,a1
80409304  sw  v0,0(a0)
80409308  ori a0,v1,0x4108      ; PCRP1, then lw / and / sw
8040931c  ori a0,v1,0x410c      ; PCRP2, then lw / and / sw
80409330  ori a0,v1,0x4110      ; PCRP3, then lw / and / sw
80409344  ori v1,v1,0x4114      ; PCRP4, then lw / and / sw
80409358  jal 0x80406728        ; flush_cache
80409360  jalr s0               ; enter the payload
```

**Five registers, one bit each, and the bit is `EnablePHYIf`.** `0x39 & ~1` is
`0x38`, which is what both projects measured. So `upstream/BENCH-LOG.md`'s
*"After `J`"* is literally right: nothing in rlxfw's early init clears
`EnablePHYIf`, because it was already clear when the kernel got control.
🔴 **Consequence for any bring-up:** a payload entered with `J` inherits five
disabled PHY interfaces. The vendor's NIC driver sets them back — `C9-SW0`'s
live column reads `nn7F0039` again — and a driver of mine that does not will
have no link and no register that says why. `docs/loader-phy-and-switch.md`
§ 7 owns the census this came out of.

**The full `S0′` → live table: 26 of 37 registers move** once the vendor NIC
driver's `device_initcall` has run. ⚠️ **The corrections file says 25, and
names `C9-SW0`.** Recount, `awk '/^r /{if($4!=$5)d++}'`: `C9-SW0` **26**,
`C11-CAT1` **26**, `C12-LOCK` **26**, `C26-UNLK` **25**. The whole difference
is **`SSIR` bit 0 (`TRXRDY`)**, which the vendor driver toggles — it reads
`00000000` live in the first three captures and `00000001` in the fourth,
against an `S0′` of `00000001`. **So the count is not a constant, and quoting
it without its capture is quoting a moment.** 26 is right for the capture the
corrections file names.

🟢 **It also settles `C7`'s undetermined.** `TEACR` (`0x4400`) and `ALECR`
(`0x440C`) read `00000000` at the loader **and** at `S0′`, which alone cannot
separate *the register is zero* from *the window is not decoded*. Live they
read **`00000002`** and **`000505F2`**. Same addresses, non-zero values: the
window decodes and the zeros were real.

## 8.4 Every counter in the derived table hit

Measured, in order across the seating: `n_reads` **38 · 186 · 261 · 335 · 410 ·
521 · 596 · 707 · 782 · 893 · 976**, `n_writes` **0 · 0 · 0 · 0 · 1 · 1 · 2 ·
2 · 7 · 7 · 16**, ending at **`n_writes 25`, `n_refused 1`, `n_reset 3`,
`n_dumb 1`, `n_restore 1`** with all four snapshot slots full.

🟢 **`n_reads 186` on the first `cat` confirms `FW-64` on a second driver.**
`38` at boot, `+74` for `C10-SAME`'s two `snap`s, `+37+37` for the `cat` —
**one `cat` is two `read_proc` invocations** on this kernel, first measured on
`rtl819x-spi` and now on a driver that shares no code with it.

🟢 **`n_writes` 2 → 7 across `reset vendor` confirms it is FIVE writes**, not
one: one `SSIR` plus four `SYS_CLK_MAG` that bypass the guarded write path and
increment the counter by hand (讀 § 3's recipe). A card predicting `+1` would
have been refuted by a driver behaving exactly as written.

🟢 **`n_refused 1`, not 9** (量 `C12-LOCK`, with `n_writes 0` beside it) — a
locked `dumb` costs one read and one refusal, because the verb returns on its
first `-EPERM` rather than trying all nine. The guard was seen refusing, with a
number.

**The whole of `n_writes 25`, with every contribution named**: `reset full` 1
(`C27`) + `reset full` 1 (`C29`) + `reset vendor` 5 (`C31`) + `dumb` 9 (`C34`)
+ `restore 0` 9 (`C39`) = **25**.

## 8.5 The controls, and one of them is quoted against the wrong pair

| control | as § 6 defines it | measured |
|---|---|---|
| **same-state sampling** | `SW-DIFF=00000000` | **`00000000`** (`C10-SAME`) — two back-to-back 37-register snapshots identical |
| **positive control on the reset** | at least one register satisfies `S1 ≠ S0′` | **11 of 37** (`C27-RST1`, live-vs-slot-0). The block is licensed, not void |
| **negative control on the writes** | a register `dumb` never writes satisfies `S3 == S1` | **0 of the 28 non-`dumb` registers moved** (§ 8.6) |
| **idempotence** | `SW-DIFF=00000000` | **`00000000`** by the verb and **0 of 37** by the captures (`C28`/`C29`/`C30`) — two instruments |
| **round trip** | `restore` brings `S0′` back | **9 of 9** (§ 8.7) |

⚠️ **The corrections file gives the positive control as *24 of 37*, and that is
the answer to a different question.** Recount: `S1` against `S0′` — which is
the control as § 6 wrote it — is **11**. `S1` against the *live Linux* state is
**24** when the Linux column is taken from `C11-CAT1` and **25** when it is
taken from `C26-UNLK`, the capture immediately before the reset. All three
numbers are ≥ 1, so the control fires whichever is used; **what does not
survive is the pairing, and a control whose pair is not stated cannot be
re-derived by a reader.**

🔴 **The idempotence control exists because a confound would otherwise have
been invisible.** `rtl819x_sw_do_reset()` asserts `FULL_RST` on **both** paths
(`:336-339`); the vendor recipe only adds the clock gate afterwards. A naive
`reset full` → snap → `reset vendor` → snap → diff measures *the 650 ms clock
gate* **and** *`FULL_RST` applied a second time* and cannot separate them.
Running `FULL_RST` twice with a snapshot between measures idempotence **before**
the clock-gate delta is attributed, and only then is § 8.8's zero a statement
about the clock gate.

## 8.6 🟢🟢 `D2` holds — on two registers, and the sharp part is the other seven

`diff 3 1` = **`SW-DIFF=00000002`** (量 `C35-D2`). By the captures, `S1` → `S3`:

```
SWTCR1  441C  00000200 -> 00000000
VCR0    4A00  000001FF -> 80000000
of the 9 registers `dumb` writes,  2 moved
of the 28 it never writes,         0 moved   <- the NEGATIVE control
```

🔴🔴 **Seven of the nine writes are no-ops against `S1`.** 量 `C27-RST1`'s live
column — the state `dumb` was applied to — beside the values `dumb` writes:

| register | `S1` reads | `dumb` writes | |
|---|---|---|---|
| `MSCR` | `00000001` | `0x00000001` | no-op |
| `SWTCR0` | `00080000` | `v & ~0xC01F` | no-op — none of those bits is set |
| `PVCR0`–`PVCR3` | `00010001` | `0x00010001` | no-op ×4 |
| `PVCR4` | `00000001` | `0x00000001` | no-op |
| **`SWTCR1`** | `00000200` | `0x00000000` | **moves** |
| **`VCR0`** | `000001FF` | `0x80000000` | **moves** |

**So Realtek's own `FULL_RST` is already most of a dumb switch.** That is
`R6-2`'s own named failure mode — *that a dumb switch looks identical to a
switch nobody configured* — arriving as a measurement rather than as a worry.
The DoD survives it because two registers do move and because the card named
which two, from loader-state readings taken twenty minutes earlier, before the
verb ran.

🟢 **And for those two registers the claim is stronger than § 3.2 allows.**
§ 3.2 says `R6-2` can only support *differs from the state this part's own
documented full reset leaves it in*, because nothing on this board can read the
switch before the loader runs. 讀, a census of every `0xBB80xxxx` address this
loader forms — `lui …,0xbb80` followed within 40 instructions by an `ori`,
`addiu` or a load/store displacement off the same register, with `NET-21`'s
thirteen addresses as its positive control (**all thirteen re-found**) —
**finds no site anywhere in the 56,592 bytes that forms `0xBB804A00` or
`0xBB80441C`**, and no load or store with displacement 18944 or 17436 either.
The controls `0x4410`, `0x4204` and `0x4A08` each return exactly one site, so
the zeros are not the instrument failing to look. 推: for `VCR0` and `SWTCR1`
the loader-prompt reading **is** the power-on value, so `D2` on these two is
*differs from the power-on default*. ⚠️ **Refutation**: a site forming either
address in a form this census cannot see — a base register carried in across a
call, or `lui …,0xbb81` with a negative displacement. Until that census exists
the sentence is 推 and § 3.2's weaker claim is the one to quote.

## 8.7 🟢🟢 The round trip: 9 of 9 came back

量 `C39-REST`. After `restore 0`, every one of the nine registers `dumb`
disturbed reads its `S0′` value again — `MSCR` `00000001`, `SWTCR0` `00080000`,
`SWTCR1` `00000200`, `VCR0` `000001FF`, `PVCR0`–`PVCR3` `00080008`, `PVCR4`
`00000001`. **The direct register path on this die reads back.**

§ 6's round-trip control was written because this part already has a register
that does not (`WDTCLR`: written `00A40000`, read `00240000` — `SPEC.md`
`FW-52`). 🔴 **That counter-example does not generalise to this block**, and
the vendor's own ten-retry double-read (`_rtl8651_readAsicEntry`, § 6 item 4)
is about the indirect TABLE path and is not evidence about this one either.
This was the most consequential thing the card could have found, and the answer
is the reassuring one, measured rather than assumed.

## 8.8 What the vendor's 650 ms clock gate adds: nothing, and the one thing that moved is the gate working

`diff 2 3` = **`00000000`** — over all 37 registers, the clock-gate cycle
changes nothing that a snapshot pair can see. The capture diff of the `cat`
immediately before against the one immediately after reads **1 of 37**, and it
is `PSRP0` `000010E0` → `000011E0`: **bit 8, `LinkDownEventFlag`, which
`NET-11` says is read-to-clear.** So the gate **did** drop and restore the
link, and the only register that records it is a latch the next read consumes.

🟢 **That latch is then seen being consumed, in three consecutive captures**:
`C30` `000010E0`, `C32` `000011E0`, `C33` `000010E0`. `NET-11`'s read-to-clear,
demonstrated in the wild rather than read out of a header.

🔴 **The two instruments disagreeing is itself the finding.** `SW-DIFF` compares
two snapshots taken at two instants; `C32`'s `cat` sat between `snap 2` and
`snap 3` and consumed the latch, so the verb could not see it. **A `diff` count
is a statement about two moments, not about an interval**, and any register
that changes for a reason other than the verb is invisible to it.

⚠️ So the honest claim is narrower than *the clock gate changes nothing*: over
the nine `dumb` registers it changes nothing, over 36 of 37 it changes nothing,
and the one that moves is a link-status latch moving because the gate worked.

## 8.9 What the loader itself writes to this block

讀, the same census as § 8.6, on the ~~boot-path~~ prompt-path routine (🔄 2026-10-08: part of `swCore_init`, which an autoboot never runs, `SPEC.md` `NET-171`; the range starts inside the `BOND_8196ES` arm) at `0x804038DC`–
`0x804039B0`. It is listed here because § 1's table asserted the opposite for
one of its three registers:

| site | write | reads back at the prompt? |
|---|---|---|
| `0x804038EC` | `MACCR (0x4000) \|= 0x1000` | 🔄 2026-10-08: not run — the `BOND_8196ES` arm (`SPEC.md` `REG-30`); bit 12 reads 0. The `MACCR` write that runs is `0x804033E0`, `(v & 0xFFF3FFF0) \| 0x00080005`, giving `804A0185` (`NET-28`) |
| `0x80403904` | `PITCR (0x4100) \|= 0x1` | 🔴 **no** — 🔄 2026-10-08: not run, the same arm; `PITCR` reads `00000000` in both states; `docs/loader-phy-and-switch.md` already owns that |
| `0x80403918` | `P0GMIICR (0x414C) \|= 0x40` | 🔄 2026-10-08: not run — the same arm; `P0GMIICR` reads `00037D00`, bit 6 = 0 (`NET-28`) |
| `0x8040392C`–`0x80403944` | `PVCR0`–`PVCR3` = `0x00080008` | 🟢 **yes**, 量 `X4`/`X5` — all four read `00080008` |
| `0x80403950` | **`MSCR (0x4410) = 0x00000001`** | 🟢 **yes**, 量 `X3-L4410` |
| `0x8040395C` | **`QNUMCR (0x4754) = 0x00001249`** | never read on this die; the name 讀 ×1, B `drivers/net/rtl819x/AsicDriver/rtl865xc_asicregs.h:1850` (superseded: *unnamed in every source here*, 2026-09-19 — `LOG.md` 2026-09-26) |
| `0x80403970` | `SSIR (0x4204) \|= 0x1` (`TRXRDY`) | 🟢 consistent — `S0′` latches `00000001` |
| `0x804039B0` | **`LEDCREG (0x4300) = 0x00200000`** | never read on this die; the name 讀 ×2 — B `:2627` (`LEDCR` `:2633` is a second, unlabelled name for the address) and D Table 68 `LEDCR0` (superseded: *unnamed in every source here*, 2026-09-19 — `LOG.md` 2026-09-26) |

🔴 **So § 1's *"why the loader never touched it"* is false for `MSCR`**, and the
row is struck in place above. The reason given there — *the loader never leaves
L2* — is confirmed rather than refuted: `MSCR = 1` is `Mode_enL2` with no ACL
and no L3/L4, which is exactly the value the `dumb` verb writes. **The loader
had already written the acceleration master switch to the dumb value, and this
file said it had never addressed the register.** `VCR0` and `SWTCR1`, the other
two rows, survive: the census finds no site for either (§ 8.6).

🔄 **2026-09-26 (desk): the two names were in a committed tool's output since
2026-09-17** (`SPEC.md` `NET-134`). `tools/hdrcensus.py` over the header copy
the build compiles (the one eleven `.cmd` files of `r6b6q2` name, not
`include/asm-rlx/rtl865x/`), `-D CONFIG_RTL_8196E -D CONFIG_RTL_819X`, prints
`0xBB804754 QNUMCR(:1850)` and `0xBB804300 LEDCR(:2633), LEDCREG(:2627)`; the
commit that wrote *unnamed in every source here* reasons about the same tool's
`cover` mode in this file and did not consult its census. The names are not
values, and neither value may enter code on these sources (讀 only, and
disassembly is not one of the admitted two):

* **`QNUMCR`'s CPU field disagrees between the two readings.** 讀 the loader's
  whole-word `0x00001249` leaves P0–P4 = 1, P5 = 0 and the CPU port's field
  (`P6QNum`, bits 20:18, `:2005`–`:2007`, *"Valid for 1~6"*) = 0; the vendor
  writes that field to 1 (`rtl_nic.c:7306` →
  `rtl865x_asicL2.c:6554`–`6555`, `RTL_CPU_RX_RING_NUM` = 1). The loader
  receives TFTP with the field at 0 (推: the field is not needed for CPU RX).
  Open in `SPEC.md` § 17 `NET-134` 殘留, settled by `R6b-8` 8c's reads.
* **`LEDCREG`'s value agrees between the two readings and not with D.** The
  vendor writes the same `2<<20` (`rtl865x_asicL2.c:4571`); D Table 68 calls
  bits 21:20 `LedTopology` and marks `10` Reserved.
* **The same routine writes outside this block, and the vendor repeats it.**
  讀 the loader clears `PIN_MUX_SEL &= ~0x8F18` at `0x8040398C` and
  `PIN_MUX_SEL2 &= ~0x3B6DB` at `0x804039A4`, the two masks the vendor applies
  at `rtl865x_asicL2.c:4568`–`4569` (the arm without `CONFIG_RTK_VOIP_BOARD`):
  讀 ×2. The mask `0xFFFC4924` is the source of `C-15`'s `0x4924`, which is not
  a switch address (`docs/loader-phy-and-switch.md`, the census-floor table).
  Retained vendor code also writes `PIN_MUX_SEL`: `drivers/char/rtl_gpio.c:2258`
  ORs its GPIO mux bits in (`SPEC.md` `REG-35` reads `|= 0x6` in the compiled
  code), bits outside `0x8F18`.

## 8.10 🔴 `dumb` kills the network, and `restore 0` does not bring it back

`C24-PING0` before: **4 transmitted, 4 received, 0 % loss.** After `dumb`
(`C36-PING1`, whose statistics line is displaced into `C38-PORT2`):
**4 transmitted, 0 received, 100 % loss.** After `restore 0` (`X24-ping3`,
off-card): **no reply in 12.13 s** — the capture holds the two header lines and
then silence, `stop_reason: --idle 12.0 with no bytes`. ⚠️ That is an absence
of reply lines, not a statistics line; a working ping on this image prints four
of them inside about four seconds.

⚠️ **The second half is correct behaviour, not a failure.** `restore 0` writes
back `S0′`, and `S0′` is the state **before** the vendor NIC driver configured
the switch — `VCR0 = 000001FF`, all nine ingress filters on, every PVID at 8.
It was never a working configuration. The card's round-trip prediction is about
**register values**, and those came back 9 of 9 (§ 8.7).

## 8.11 🔴 `SWINTSET` is refuted, and an off-card control says it is the die and not the instrument

`C15-SWSET` wrote `CPUICR = 0x00100000` through the vendor's
`/proc/rtl865x/memory`; the handler's own read-back printed **`0x0`**.
`C16-IMR2`, made character-identical to `C14-IMR` so the over-read is the same
on both sides of the write, reads `CPUIIMR 00000000` and `CPUIISR 80000000` —
**byte-identical to `C14`. Zero bits moved.** `C13-DMA0` and `C18-DMA1` both
read `CPUICR 00000000`.

🔴 **The card had no control for *the write never reached the register*.** Four
off-card cells added one: `X19`–`X22` wrote `0x04000000` — the mbuf-size field,
configuration rather than a trigger, with `TXCMD`/`RXCMD` clear — through the
**same** `echo write` path. It **stuck** (`dat 0x4000000: 0x4000000`, read back
`04000000` by an independent `echo read`) and the restore to `0` also took.

**So `C16`'s zero is a fact about bit 20.** With the engine off (`CPUICR` `0`)
and the mask closed (`CPUIIMR` `0`), writing `SWINTSET` leaves no trace and
raises no `CPUIISR` bit. § 7's `NET-38 殘留` ① — *which `CPUIISR` bit is the
software interrupt* — is **not** answered; 推 it needs `TXCMD`/`RXCMD` set, or
the mask open, or bit 20 is not `SWINTSET` on this part. 🔴 **§ 7's *"the first
rung is a DISCOVERY cell rather than a pass/fail"* is the claim that falls:
`R6-3`'s rung zero as designed does not work**, and it is worth more knowing
that before the driver exists than after.

🟢 `CPUIISR`'s first reading ever is **`80000000`**.
🟢 The output format hit exactly: `%p` lowercase zero-padded (`0xb8010000`),
`%x` **not** padded (`dat 0x100000`). A card predicting `dat 0x00100000` would
have read a correct result as a refutation.

## 8.12 🔴 The `<Port: 5>` tension does not exist — it is a section boundary

`asicCounter` bracketing four pings went from all-zero (`C22-ACNT0`) to
`Rcv 536 bytes, 6 unicast` and `Snd 536 bytes, 5 unicast + 1 broadcast`
(`C25-ACNT1`), and `SPEC.md` `NET-34` records `ifconfig eth4` reading
`RX packets:6 TX packets:6`, `RX bytes:536 TX bytes:536` for the same
operation. 🟢 **The switch silicon's MIB and the Linux netdev's software
accounting agree exactly, sharing no code.**

🔴 **The corrections file § 2.11 reads a TX-only 6 unicast on `<Port: 5>` and
calls it a tension with `PCRP5 = 00000000`. There is no such reading.** 量, by
splitting both captures on their own `^<…>$` headings and extracting each
section's counters:

| section | `C22-ACNT0` | `C25-ACNT1` |
|---|---|---|
| `<Port: 0>`…`<Port: 2>`, `<Port: 4>` | all zero | all zero |
| `<Port: 3>` | all zero | **Rcv 536 / 6 uni · Snd 536 / 5 uni + 1 bcast** |
| **`<Port: 5>`** | all zero | **all zero, both directions** |
| `<CPU port (extension port included)>` | all zero | **Snd 536 / 6 uni**, Rcv 0 bytes with `CRCAlignErr 6` |

**The 6 unicast belongs to `<CPU port (extension port included)>`, which is the
heading *after* `<Port: 5>`.** 讀 `rtl865xC_dumpAsicDiagCounter()`,
`rtl865x_asicCom.c:1776-1787`: it loops `i` over `0 … RTL8651_PORT_NUMBER`
**inclusive** and prints `<CPU port (extension port included)>` when
`i == RTL8651_PORT_NUMBER`, which is `RTL8651_MAC_NUMBER` = **6**
(`rtl865x_asicCom.h:24-25`). So the dump has six port sections and a seventh
that is not a port. **`PCRP5 = 00000000` in
all three states, the desk reading that port 5 is an unpopulated MII port, and
the MIB are consistent, and nothing here needs adjudicating.**

⚠️ **Two instrument caveats on this dump, both unresolved.** The CPU section
counts `CRCAlignErr 6` against `Rcv 0 bytes` while its size buckets hold the
same six frames — 未定. And the third reading (`C37`, displaced into
`C38-PORT2`) is **all zero including port 3**, after three `FULL_RST`s and a
`dumb`; 讀 `rtl8651_returnAsicCounter()` is a plain `READ_MEM32`, and its
caller's comment (`_rtl8651_initialRead`, *"read counter for the first time
will get value -1"*) documents a first-read hazard and **not** a read-to-clear,
so whether the MIB was cleared by the resets or by the reads is 未定. **The
discriminating cell is two `asicCounter` reads back to back with traffic
between them and no reset**, and it costs nothing.

## 8.13 `resetcmp` is not a verb, and this file's verb list is the one the parser has

量: the token `resetcmp` occurs in this repository only as a comment at
`rtl819x-switch.c:375` and as prose in `docs/KNOWN-ISSUES.md` — **it was never
in the parser**, and a frozen card's cell 8 asked for it. Typing it returns
`-EINVAL`. 讀 `rtl819x-switch.c:588-661`, the parser accepts exactly nine
forms and nothing else (1.0–1.3; since 1.4 the rest go to 1.4's forms, § 15.3, then 1.5's, § 17.2):

```
unlock <token>   lock   snap <s>   diff <a> <b>
reset full       reset vendor      start   dumb   restore <s>
```

`snap 0` is refused as well — slot 0 is the boot latch and is not the
operator's to overwrite. What the missing verb was for was composed instead out
of `reset full` → `snap` → `reset vendor` → `snap` → `diff`, and § 8.5 records
what composing it exposed.

## 8.14 🔴🔴 What `/proc/rtl865x/` this image actually has — 8 of the vendor's 42

**`SPEC.md` `NET-42`.** The vendor registers **42** distinct `/proc/rtl865x/`
entries. **Eight are registered on this image**: `asicCounter`, `diagnostic`,
`fc_threshold`, `mac`, `memory`, `mmd`, `phyReg`, `port_status` — 量 the
device's own `ls /proc/rtl865x/` (`bench/2026-09-22b/X8b-ASICLS`), and the
gates below give the same eight (讀). **Thirty-four are not**, among them
`vlan`, `pvid`, `rxRing`, `txRing`, `mbufRing` and `nic_mbuf`. 🔄 **This
section said thirteen from 2026-09-19 to 2026-09-26: the flat-image count below
read as a registration count** (`LOG.md` 2026-09-26).

**The method, 量 2026-09-19 on the built flat image, because a `/proc` entry's
name is a NUL-delimited `.rodata` literal**: search the image for
`b"\x00name\x00"`. Four controls ran with it — `port_status` **1**, `memory`
**2**, `rtl819x-switch` **1** (this driver's own entry, which must be found or
the search is not looking at the right image) and a synthetic name **0**. It
reads **13**, and five of the thirteen are not vendor strings. 量 2026-09-26,
the same search per object, over the `.rodata`/`.data` of `r6b6q2`'s 634
objects with content, 594 compiled leaves and 40 archive members (🔄 2026-09-27: this said *667 compiled objects*, § 11.7; controls: `rtl819x-switch` found in `rtl819x-switch.o`, the
synthetic name nowhere): `stats` (`8192cd_proc.o`), `arp` (`arp.o`,
`x_tables.o`; 🔄 2026-09-27: also `usr/initramfs_data.o`'s `.init.ramfs`, which this search did not read, § 11.7), `ip` (`x_tables.o`; also that `.init.ramfs`), `pppoe` (`pppoe.o`) and `igmp` (`igmp.o`)
occur only in retained non-vendor code; `memory` (`sock.o`) and `mac`
(`xt_mac.o`) occur in both; six names occur only in vendor objects. A name in
the image is a name some object carries, not an entry some driver registered —
`tools/imgprocs.py`'s header already said the second half, and the first half
is why `memory` is no longer one of its controls.

🟢 **讀, the gates that decide it** (`rtl865x_proc_debug.c`, byte-identical in the staged tree and `src-vendor`):

| line | gate | effect here |
|---|---|---|
| `:5227` | `#ifdef CONFIG_RTL_PROC_DEBUG` | off in rlxfw — takes all 34, `stats`, `arp`, `ip`, `pppoe` and `igmp` among them |
| `:5817` | `#if defined(CONFIG_RTL_PROC_DEBUG)\|\|defined(CONFIG_RTL_DEBUG_TOOL)` | **rlxfw has the second**, which is why the eight survive and is the path every register reading in § 8.11 went through |
| `:5396` | `#if defined(RTL_DEBUG_NIC_SKB_BUFFER)` | a plain `#define`, **not a Kconfig symbol**, nested inside `:5227` and closed at `:5412` — it gates `nic_mbuf` alone (🔄 2026-09-26: this row said it also gated `rxRing`, `txRing`, `mbufRing` and `pvid`, which sit under `:5227` only) |

🔴 **The four `R6-3` would want are behind `CONFIG_RTL_PROC_DEBUG`, a Kconfig
symbol, and `nic_mbuf` needs the `-D` besides** (🔄 2026-09-26: this paragraph
said *behind the one gate that costs a `-D` and nothing else*).
`rxRing`, `txRing`, `mbufRing` and `nic_mbuf` are the vendor's
own view of the descriptor rings — the second source the descriptor argument in
§ 7.1 was refuted for lacking — and they are absent from rlxfw's board template
by a configuration decision nobody made deliberately. Carried forward rather
than changed here.

⚠️ **This is a fact about THIS image's configuration, not about the device.**
The vendor firmware has more of them.

🟢 **`FW-46` now has a method, and it killed two cells of the very card that
produced it.** `FW-46` is *nothing in this repository can ask "can this image
run this command" before a card is frozen.* The first draft of seating 27's
card read `/proc/rtl865x/vlan` and `/proc/rtl865x/pvid`; **neither exists in
this image**, both would have printed *"No such file or directory"*, and
`check-predictions` scores existence and mtime rather than content — so the
seating would have reported `41 of 41` with two cells empty. The three-line
search above is what caught them, before power.


## 8.15 🔴 The CPU port counts every CPU-sourced frame as `CRCAlignErr`, so that counter is meaningless for CPU traffic

量 2026-09-20 (seating 30), `bench/2026-09-20b/X2-asic.log`. The
`<CPU port (extension port included)>` block's **receive** side — which is the
switch receiving *from* the CPU — reads `CRCAlignErr 217`, and in the same
capture port 3's output side reads `Unicast 216 pkts` plus `Broadcast 1 pkts`,
which is **217**. The size buckets on that same block are 10 + 4 + 20 + 183 =
**217** as well.

🟢 **And all 217 frames arrived**: rungs `H1-frag1` through `H4-f6` were 1/1 and
three times 20/20 on the host, so the host received every reply the board sent
in that window.

推 the mechanism: the CPU hands the switch a frame without an FCS and the
switch appends one, so the MIB counts each as a CRC/alignment error on the way
in. **It is a constant offset equal to the CPU-sourced frame count, not a
fault.**

🔴 **What this costs**: `NET-56` used port 3's `CRCAlignErr` as the discriminator
that separated a faulty cable from every software cause, and that use is still
sound — it is port 3's **receive** side, i.e. the wire. The CPU port's is a
different counter with the same name, and reading it as an error indicator
would report a healthy board as broken on every frame it transmits.
`SPEC.md` `NET-65`.

# 9. 2026-09-26 (`R6b-6`) — 1.2: every `PSRP` read keeps what it consumes

## 9.1 Why

`PSRP` bit 8, `LinkDownEventFlag`, latches a link-down and **clears when read**.
Two sources: the vendor header, `rtl865xc_asicregs.h:1328` (the copy under
`drivers/net/rtl819x/AsicDriver/`, 3,537 lines), and the datasheet's Table 65
(`docs/loader-phy-and-switch.md`, the `PSRP` paragraph); and 量 `SPEC.md`
`NET-11`, where one read of a port whose jack was already empty cleared it. The
vendor's own comment in `rtl_nic.c:3206` says the same.

So every reader of `PSRP` destroys the evidence the next reader needs. 1.1 had
three readers — the slot-0 snapshot at `subsys_initcall`, the `/proc` table,
and `rtl819x_sw_any_link()`, which `rtl819x-nic`'s ethtool `get_link` calls —
and none of them kept the bit. `R6b-6`'s positive control is a cable pull, read
back through `get_link`; in 1.1 that read would have erased the latch the pull
set, and nothing afterwards could have shown the pull happened.

The vendor has two readers of its own, and neither keeps the bit either:
`port_status_read` (`rtl865x_proc_debug.c:4182-4246`) reads every `PSRP` twice
(`:4194`, `:4221`) and prints bit 4, never bit 8; and the link DSR
(`rtl_nic.c:3613-3618`) reads `PSRP` through
`rtl865x_getPhysicalPortLinkStatus`. Its one named consumer of bit 8,
`re865x_setPhyGrayCode` (`:3197-3232`), is under `CONFIG_RTL8196C_ETH_IOT`,
which this image does not set.

## 9.2 What changed

* **No line of 1.1 moved.** Seven lines changed, each one that was blank or in
  place: the version string (`:118`); three prototypes (`:269`, `:532`, `:676`);
  and three call sites — `rtl819x_sw_rd` (`:278`), the `/proc` page before its
  table (`:553`), the initcall after the slot-0 snapshot (`:689`). 154 lines are
  appended after `:716`. 量 at `f758d62`: seventeen committed files cite this
  driver by line, 23 citations, and no cited range holds a changed line.
* `rtl819x_sw_rd()` — the one read path — hands every value to
  `rtl819x_sw_lde_note()` (`noinline`, 17 call sites in the object), which
  counts a set bit 8 per port and stamps the jiffies of the last one.
* `/proc/rtl819x-switch` prints, **before** the register table, so that the
  table's last line is still the page's last line:

  ```
  n_linkq %lu
  lde0 %02X
  psrp%u %08X up %u lde %lu lj %lu      (x8, PSRP0..PSRP7)
  jiffies %lu
  ```

  Each `psrpN` line is read live and printed after that read's accounting, so a
  latch its own read consumed is already in its `lde`. `n_linkq` is
  `get_link`'s own counter, which 1.1 kept and never printed. `jiffies` is
  printed after the eight reads, so every `lj` on the page is at or before it.
  One render now reads 45 registers (37 table rows and 8 `psrp` lines), so
  `n_reads` grows by 90 per `cat` (`FW-64`: one `cat` is two renders).
* At boot, after the slot-0 snapshot, the `PSRP`s the census table does not
  hold (1, 2 and 4 — asked of the table, not typed) are read once, and
  `RLXFW-SW7=000000XX` carries the S0' mask: bit *p* set if `PSRPp`'s bit 8 was
  set at `subsys_initcall`. It prints between `SW1` and `SW2`, because that is
  when it is known. 20 bytes of boot capture; `bootbytes` derives it from the
  source.
* `#if defined(CONFIG_SMP) || defined(CONFIG_PREEMPT)` → `#error`: the counters
  are unlocked because this `.config` is UP and `PREEMPT_NONE` and no reader
  runs in interrupt context, and that assumption is now a refusal.
* `PSRP8` is not read: nothing has ever read it under Linux, and the
  datasheet's port table stops at `PSRP7`.

## 9.3 What the desk measured

* **The file compiles as the kernel compiles it.** 量, `rtl819x-switch.c` alone
  with the command line kbuild recorded for this object (`s100a`'s
  `.rtl819x-switch.o.cmd`, dependency writer removed), reading that tree and
  writing only to scratch, under `vendor-tripwire`: 1.1 and 1.2 each print the
  one warning 1.1 always had (`rtl819x_sw_lock` defined but not used) and no
  other; 1.2 with `-DCONFIG_SMP=1` prints its own `#error`; a planted syntax
  error fails. The two images' build logs carry the same one warning.
* **The page.** Walked from the driver's own `sprintf` formats, every field at
  the widest its variable can hold: 1.1's worst page is 1,642 bytes, 1.2's
  2,080 (+438: 19 + 8 + 8 × 49 + 19). The table's budget check (3,600) is
  never what ends it, and the page stays inside one 4,096-byte page.
* **The image.** `r6b6q` and `r6b6q2` (quiet, `92aeaa8` + this change, recipe
  `acf8ed3d`) are byte-identical — vmlinux `9e0ff326…`, nfjrom `ef5622d2…`,
  `cmp` rc 0 on both — and both differ from `r6b2q`. Declared gates green
  (12 marks, 9 witnesses, 1 ABSENT); `kconfig-delta` quiet green; `storeseq`
  `r6b2q` → `r6b6q` green on its seven functions, and `rtl819x-nic.c` is
  `92aeaa8`'s byte for byte. In the vmlinux: `RLXFW-SW7=` once,
  `rtl819x-switch 1.2` twice (`.rodata` and `/bin/mfgtest`'s text),
  `rtl819x-switch 1.1` never.
* **S0' already holds bit 8, twice in thirteen boots** — § 9.4.

## 9.4 S0' and bit 8, over every committed dump (`NET-126`)

量 2026-09-26, zero power. The 32 committed `/proc/rtl819x-switch` dumps fall
into 13 boot groups, each bounded by the capture that booted it (session script
`s112/r6b6/work/s0table.py`, written apart from the proposal's survey and
reproducing its count). Control: no group carries two slot-0 values for any
register — slot 0 is written once per boot. Five `PSRP`s are in the table
(0, 3, 5, 6, 7); S0' bit 8 appears on `PSRP3` only, and twice:

| boot capture | `RLXFW-ID0` | S0' `PSRP3` | reading |
|---|---|---|---|
| `2026-09-19b/r6nic3-boot` | `7FE2F8C3` | `000011E9` | bit 8 set, **LinkUp clear**: the link was down at `subsys_initcall`; `D7` at 13:04:44 reads it back up (`000000F9`) |
| `2026-09-20/C2-BOOT` | `EDC94765` | `000011F9` | bit 8 set, link up |
| the other 11 | seven images | `000010F9` | no bit 8 |

**Live words with bit 8 set: two, not the proposal's one.**

* `2026-09-19/C32-CATV`, `PSRP0` = `000011E0`, 36 s after `C31-RSTV`'s
  `reset vendor` (`FULL_RST` plus the four `SYS_CLK_MAG` writes, § 8.8). Port 0
  has no link partner — bit 4 is clear before (`C30-SNP2D`, `000010E0`) and
  after — and the same dump's `PSRP3` reads `000010F9`. **A software reset of
  the switch sets bit 8 on a port that had no link to lose.**
* `2026-09-20/X19-sw`, `PSRP3` = `000001F9`, after the cable was re-seated
  (`PREDICTIONS-B30-block29.md`).

**The windows, joined with their history** (讀, per group: the bench
directory's card and corrections, every capture's `meta.json` `sent` field,
`LOG.md`). No window of the 13 contains a run of the vendor firmware or a
recorded attach of the host's GbE adapter. `C2-BOOT`'s is the one gap: the
adapter was brought up before that card froze, at a time nothing recorded.
All 13 boots went rescue → TFTP → `J 80500000`, and none read `PSRP` or ran
`PHYR`/`PHYW` at the prompt. `r6nic3-boot` followed `C62`'s
`busybox reboot -f` at 13:02:18, inside `NET-54`'s wedge and a run of `rlx0`
down/up.

So `NET-30` 殘留's decisive experiment rested on a premise that is not
established — that a clean boot reads bit 8 = 0 — and its two candidates are
not the whole list: bit 8 has been set by a software reset (`C32`) and by a
re-seat (`X19`), and `r6nic3` booted with the link actually down with neither
candidate in its window. 推: both bit-8 boots came before the 09-20 re-seat
(2 of 4 before it, 0 of 9 after), and both started with port 3's receive
already impaired (`r6nic3` deaf; `C2-BOOT`'s first ping lost 2 of 4) — which
fits `NET-56`'s contact-fault 推 and does not prove it.

**Open**: whether a cold power-on, the loader's rescue path or its TFTP sets or
clears the latch (the loader census finds no `PSRP` site, and states that it
cannot see computed addresses). What settles it: a cold power-on with the
adapter attached and untouched since before power, `DW BB804134 1` at the
prompt, again after `IPCONFIG`, again after the upload. 1.2's `SW7` then gives
the kernel's side of the same boot for nothing.

`study/20260919-study1.md` says the boot read makes that experiment
impossible. Half of that is wrong: slot 0 keeps the value the read consumed.
The study file is a record; the correction is `LOG.md`'s.

## 9.5 What 1.2 does not establish

* Nothing about the silicon: not one line of 1.2 has run.
* `lde` counts **this driver's reads that saw the latch**. It is a lower bound
  on link-down events — the latch saturates, so two events between two reads
  count once — and it is blind to the vendor's reads. A card that reads
  `/proc/rtl865x/port_status` between two reads of this file makes `lde`
  under-count; that is why such a card reads this file first and
  `port_status` last.
* `SW7` records the latch at `subsys_initcall`, after the loader and anything
  the loader ran. It is not "immediately after a cold boot".
* The three reads at `subsys_initcall` clear ports 1, 2 and 4's bit 8 before
  the vendor's probe; that costs nothing only as long as the vendor's one
  consumer stays unbuilt.

# 10. 2026-09-26 (`R6b-7`) — 1.3: an `mii_bus` for PHYs 0–4, and one path for every MDIO command

## 10.1 Why

`R6b-7`'s DoD asks for the PHY IDs read *through Linux's MDIO API* and compared
with the loader's, and for `C-18`'s reopening condition read through the same
path. 1.0–1.2 issue no MDIO command at all. 1.3 adds a phylib `mii_bus` for
the five embedded PHYs rather than a private accessor, because the step names
the kernel's API (the owner's decision A, § 10.7). `SPEC.md` `NET-135`.

## 10.2 The register contract, and where each part comes from

The fields are `SPEC.md` `NET-15`'s; what 1.3 adds is what each part rests on,
and which parts are open. `SPEC.md` `NET-136`.

| part | value | V | N | sources |
|---|---|:-:|:-:|---|
| `MDCIOCR` `0xBB804004` | bit 31 `COMMAND` (0 read, 1 write), 28:24 `PHYADD`, 20:16 `REGADD`, 15:0 `WRDATA`; 30:29 and 23:21 reserved | 讀 | 讀 | ×3 (`NET-15`): D, Tables 57–59; B, `rtl865xc_asicregs.h:1046-1056` (the `drivers/net/rtl819x/AsicDriver/` copy, 3,537 lines); A, the loader's `phy_read`/`phy_write` at `0x80402F80`/`0x80402FF8` |
| `MDCIOSR` `0xBB804008` | bit 31 `STATUS` (1 = in progress), 15:0 `RDATA` | 讀 | 讀 | D Table 59; B `:1058-1062`; A |
| issue, completion | one store of the whole command word issues it; `STATUS` clear is completion | 讀 | 讀 | D's procedure; A; B's two accessors, `rtl865x_asicL2.c:5552-5580` |
| `MDCIOSR` 30:16 | **未定**: D says Reserved, B names bit 30 `MDCIOSR_ReadError` (`:1267`) | — | — | two sources that disagree; 1.3 records the bits (`hi`, `hi_or`) and decides nothing on them |
| `STATUS` set | never observed: all 70 `MDCIOSR` rows in the committed `/proc/rtl819x-switch` dumps read bit 31 clear, live and slot 0 (live `00001100` ×58, `00000000` ×10, `000078C9` ×1, `000078ED` ×1; slot 0 `00000000` ×70) | 量 | 讀 | S; a dump reads the register long after any command, so this bounds nothing about a transaction's length — `spin` measures that |
| the 10 ms delay | not needed: the vendor's **undelayed** `/proc/rtl865x/phyReg` path read PHY 0 registers 2, 3, 0 and 1 as `0x1c`, `0xc880`, `0x1100`, `0x78c9` (`bench/2026-09-19` `C19-PHYID`, `C20-PHYST`), the values the loader's **delayed** reads returned (`F2`, `bench/2026-08-23/E.log`, `X8`, `E12d`); a shifted or late-latched `RDATA` would have made the two paths disagree | 量 | 讀 | B delays only on 8198 and 8196C revision A (`rtl865x_asicL2.c:5558-5564`: "mdio data read will delay 1 mdc clock"); A delays 10 ms before every poll (`0x80402FC0`). Four values on PHY 0; `scan` re-tests 0–4 |
| register 31 | the page select: a page is selected by writing it to register 31 and left by writing 0; a page ≥ 31 goes through 31 ← 7, then 30 ← page | 讀 | 讀 | ×2, code only: A, `PORT1` (`0x8040A0A0`, `docs/loader-phy-and-switch.md` § 4); B, `Set_GPHYWB` (`rtl865x_asicL2.c:1230-1266`). D has no PHY register map |
| register 31, read back | **未定**: no source reads it | — | — | `NET-136` 殘留 in `SPEC.md` § 17; the card's (g) |
| page 1, register 16, bits 15:13 | 110 on PHYs 0–4 after the vendor's init ("Iq Current 110:175uA") | 讀 | 讀 | B, `Setting_RTL8196E_PHY`, `rtl865x_asicL2.c:4177` |
| page 1, register 19, bit 0 | 0 on all five: cleared in the B-cut branch | 讀 | 讀 | B `:4193`; the branch runs because `REVR` reads `0x8196E001` (量, `SPEC.md` `CPU-32`) and the A-cut test is `== 0x8196e000` |
| an empty address, to phylib | `(id & 0x1fffffff) == 0x1fffffff` | 讀 | 讀 | `drivers/net/phy/phy_device.c:231`. Register 2 reads `0x0000` at 5–31 (量, `NET-24`), so none of those 27 IDs can pass as empty, whatever register 3 holds |
| a failed read, to phylib | every negative read becomes `-EIO` | 讀 | 讀 | `get_phy_id`, `phy_device.c:187-209` |
| `ETIMEDOUT`, `EPROTO` | 145 and 71 on this arch, not asm-generic's 110 | 讀 | 讀 | `arch/rlx/include/asm/errno.h:98`, `:48` |

## 10.3 Who else issues MDIO commands in this image, and why IRQs go off

讀, a call census of `r6b6q`'s vmlinux (the design's, not re-derived here): 25
read and 43 write call sites in 20 vendor functions, all through the two
accessors. All of them run in process context — the probe, the `/proc`
writers, `re865x_close` — except `one_sec_timer` (`rtl_nic.c:3845`), a kernel
timer that `re865x_open` arms for `eth0` only (`:4257-4266`). It saves IRQs off
(`:3856`) and calls `refine_phy_setting()` (`:3813-3841`, called at `:4140`)
once a second: page-0 writes to registers 25, 26, 17 and 21 of PHYs 0–4. None
of these paths takes a lock 1.3 could share.

On this `.config` — UP, `PREEMPT_NONE`, and 1.2's `#error` otherwise — another
MDIO user can run between 1.3's store of `MDCIOCR` and its read of `MDCIOSR`
only from interrupt context. So every transaction runs with IRQs off, and
`pread`'s select, read and restore run inside **one** IRQs-off section: a timer
tick between them would land `refine_phy_setting`'s page-0 writes on the
selected page. `/init` opens `rlx0` only, so the timer is not armed unless a
card opens `eth0`.

## 10.4 The design

* **One path.** `rtl819x_mdio_xfer()` is the only `MDCIOCR` store in rlxfw. A
  bounded pre-check (`STATUS` still set after `bound` polls: `-EBUSY`, counted
  in `busy`, and the store is **not** made — a command is still in flight), the
  store, a bounded poll (`-ETIMEDOUT`, counted in `mdio_to`), then `RDATA`.
  `spin` counts the transactions that completed and the fewest and most polls
  any of them needed; bits 30:16 are kept per transaction and ORed into
  `hi_or`. The loader's own wait has no bound at all (`SPEC.md` `NET-17`).
* **The gate** (decision C). Every `MDCIOCR` store — a read is a store too
  (`NET-16`) — needs `unlock mdio-i-mean-it` on `/proc/rtl819x-mdio`: a token of
  its own, because `/init` writes the switch's `unlock i-mean-it` on every boot
  (`config/rlxfw-init.sh`). So a boot issues no MDIO command, `mdio_rd` and
  `mdio_wr` read 0 until a card unlocks, and the header's item 2 (*it writes
  NOTHING at boot*) stays true. `bound` is accepted while locked; it issues
  nothing.
* **`probe`: registration.** One-shot. `mdiobus_alloc`, name `rtl819x-mdio`,
  id `rlxsw`, the two ops, and `phy_mask` = `~0`, so `mdiobus_register` issues
  no command; then `mdiobus_scan(bus, a)` for a = 0–4, phylib's own path: ten
  reads, registers 2 and 3 of each. Each address keeps phylib's result (`rc`)
  beside the rc of the last transaction the read op issued to it (`xrc`),
  because phylib turns every failed read into `-EIO`. Masked, because an
  unmasked scan would register 27 phantom `phy_device`s (§ 10.2). One-shot even
  after a failure, because a second `mdiobus_scan` of an address registers a
  second device under the same name, `device_register` refuses it, and
  `mdio_bus.c:218` then writes `NULL` into `phy_map`. Not at boot: nothing may
  issue MDIO at boot, and `phy_init` is a `subsys_initcall`
  (`phy_device.c:899-920`) in an object linked after `rtl819x-switch.o` (the
  staged `drivers/net/Makefile`, lines 98 and 100), so `rtl819x_sw_init` could
  not register a bus anyway. The boot creates only the `/proc` entry, at
  `device_initcall`: no MDIO command, no phylib call, and no mark unless that
  fails (`MD0-NOPROC`).
* **Nothing attached.** `rlx0` is the CPU port and has no PHY (`NET-39`).
  Nothing calls `phy_connect` or `phy_attach`; genphy matches only the ID
  `FFFFFFFF` (`phy_device.c:886-888`), and the delta pins every other
  `phy_driver` off, so the five devices stay unbound. `drv` and `att` print that
  per address.
* **The bus's write op refuses, always** (`wr_refused`): a phylib write would be
  counted, not done. The only PHY writes 1.3 makes are `pread`'s register-31
  select and restore.
* **`bound n`** (0–10,000) exists to make `scan` time out on purpose: the
  timeout's positive control. `probe` and `pread` refuse with `-EAGAIN`
  (counted in `again`, the one-shot probe not spent) unless `bound` is the fixed
  10,000: at a small bound a probe would spend its one shot on phylib's `-EIO`,
  and a `pread`'s restore could be refused and leave the PHY on page 1.
* **`scan lo hi`**: registers 0–5 of every address in [lo, hi] through
  `mdiobus_read`, then `PSRPa` for a < 5 through the one switch read path, so a
  bit 8 consumed here is counted by 1.2's `lde`. Reading register 1 clears the
  PHY's latched-low link bit (推, IEEE 802.3 22.2.4.2.13): a card that wants a
  link-down latch reads it before a scan.
* **`pread a page reg`**: a 0–4; page 0 (no select — the same register
  unpaged, the control) or 1; reg 0–30. At page 1, after taking
  `bus->mdio_lock` (the lock phylib's own reads take) and inside one IRQs-off
  section: read register 31 (`p0`; not 0 → `-EPROTO`, and nothing is written);
  31 ← 1; read 31 back (`ps`); read the register (`v`); 31 ← 0, always, and
  once more at the full bound if that store was refused `-EBUSY` (`rt`,
  `retry`); read 31 back (`p1`). A restore never stored, or `p1` ≠ 0, sets
  `dirty` to a + 1 and returns `-EIO`, and every later `pread` is refused
  `-EIO` with no store: the PHY may be left on a page the vendor's page-0
  writes would land on. `ps` ≠ 1 returns `-EPROTO` with `v` kept. `PSRPa` is read
  either side, outside the section. A page-1 `pread` is six transactions — four
  reads, two writes; a page-0 `pread` is one read.
* **No `EnForceMode` bracket.** The vendor's `Setting_RTL8196E_PHY` sets
  `EnForceMode` on `PCRP0`–`PCRP4` before its paged writes
  (`rtl865x_asicL2.c:4173-4174`); its `/proc` `extRead` pages without it
  (`rtl865x_proc_debug.c:4836-4881`). 1.3 does not bracket, so the switch's own
  PHY polling may meet a selected page (推). `PSRP` bit 8 either side of the
  section is the only detector, and only while no vendor `eth*` is open, whose
  link DSR reads `PSRP` too.
* **IRQs off, at worst.** A transaction polls `STATUS` at most `bound` + 1
  times before its store and as many after it, with `udelay(1)` between polls:
  ≤ 2 × 10 ms of delay, nominal. A `pread` holds IRQs off across at most seven
  transactions — six, and one retried restore whose first attempt never stored
  and so never polled after — so ≤ 13 × 10 ms = 130 ms nominal, plus the reads.
  推: a transaction that completes takes tens of µs; the worst case is the
  failure the bound exists for. At `HZ` 100 it would cost ~13 ticks, and at
  38,400 baud the UART's FIFO fills in ~4 ms of host input (推), so a card does
  not type while a `pread` may be timing out.
* **The page.** `/proc/rtl819x-mdio` prints cached results only: a `cat` issues
  no MDIO command, which matters because one `cat` renders twice (`FW-64`).

  ```
  version rtl819x-switch 1.3
  unlocked %d
  bus %d reg_rc %d
  bound %u
  mdio_rd %lu
  mdio_wr %lu
  mdio_to %lu busy %lu retry %lu
  refused %lu wr_refused %lu again %lu
  spin %lu %u %u
  hi_or %08X
  dirty %d
  scanned %08X j %lu
  phyN id %08X rc %d xrc %d drv %d att %d     N = 0-4; before a probe: phyN id - rc %d xrc %d
  pr aA pP rRR v %d p0 %d ps %d p1 %d rs %d rt %u rc %d psrp %08X %08X     the last eight preads
  aNN %04X x6 hi %04X psrp %08X n %u     each scanned address; an error prints as Ennn
  jiffies %lu
  ```

  Walked from the formats with every field at its widest: the head is ≤ 1,735
  bytes, a row ≤ 69, the trailer 19, so the page is ≤ 3,962 bytes with all 32
  rows. The rows print under a 3,900-byte budget that cannot fire at these
  widths (the 32nd row starts at ≤ 3,874).
* **The parser.** A numeric field must start with a digit, fields are separated
  by exactly one space, and the last one ends the line. 讀 `simple_strtoul`
  skips no whitespace and reads a field that does not start with a digit as 0
  (`lib/vsprintf.c:54-76`), so under the draft's parser `pread 0  1` (two
  spaces) became a page-0 read of register 1, and trailing letters were
  ignored. Base 0: `0x` is hex and a leading `0` is octal.
* **Marks**, printed when a verb runs: `RLXFW-MD-UNLOCK`, `RLXFW-MD-LOCK`,
  `RLXFW-MD1=` (probe: the mask of addresses holding a device),
  `RLXFW-MD1-REG=` (registration failed: −rc), `RLXFW-MD2=` (scan:
  `hi << 8 | lo`), `RLXFW-MD3=` (pread: `a << 16 | page << 8 | reg`), and
  `RLXFW-MD0-NOPROC`. A card gates on the page, never on a mark (`FW-47`).
* **`#ifndef CONFIG_PHYLIB` → `#error`**: a delta without phylib refuses at
  compile time instead of failing at link.

## 10.5 What the desk measured

* **The delta: 31 rows, declared from a build, not a prediction.** Appended
  after `config/rlxfw-kernel.delta`'s line 294, so none of its cited lines
  moves (2, 82, 89, 138 and 174–177; all of 1–294 read as before). The two
  decisions, `CONFIG_NET_ETHERNET` and `CONFIG_PHYLIB`, went alone into a probe
  cell, `r6b7p0`. 量: its oldconfig log held 22 `(NEW)` prompts — 15 in
  `drivers/net/phy/Kconfig` (fourteen PHY drivers and `MDIO_BITBANG`) and 7 in
  `drivers/net/Kconfig`'s `if NET_ETHERNET` block (`MII`, `AX88796`, `SMC91X`,
  `DM9000`, `ETHOC`, `DNET`, `B44`) — and `kconfig-delta check` refused it with
  29 undeclared: those 22, and seven promptless `CONFIG_IBM_NEW_EMAC_*` that a
  count of prompts cannot show. Both predictions on file before that build
  held (22; 22 + 7). The 31 are 24 `set` (the two decisions, and the 22 pinned
  n) and 7 `derive … promptless`. `SPEC.md` `FW-147`.
* **The images.** `r6b7q` and `r6b7q2` — quiet, `2a3f5e2` plus this change,
  recipe `50e4af55`, each from a fresh stage, one at a time, with `R6b-6`'s
  recipe (`rlxfw-kbuild.sh --variant quiet --initramfs _irfs-r6b6 spec --marks
  --jobs 4`, then `rtkimage.py build`) — are byte-identical: vmlinux
  `b926105b…` (4,530,877 bytes) and nfjrom `548f4fae…` (1,169,408 bytes), `cmp`
  rc 0 on both; the two manifests differ only in the cell name; the initramfs
  digest `d6882c14` is `r6b6q`'s. Both read `(NEW)` 0 and `kconfig-delta check`
  green with 30 derived and 74 set, against `r6b6q`'s 23 and 50 — the 31 rows
  exactly. `rlxfw-marks verify`: 12 marks, 9 witnesses, 1 ABSENT. The loud
  variant's oldconfig alone ran (`r6b7L0`): `(NEW)` 0, `check --variant loud`
  green with 30 and 76. `config/` has not changed between `2a3f5e2` and the
  commit this lands on, so the recipe stands.
* **The size.** `vmlinux_img` is 4,002,304 bytes against the 5,242,880-byte
  ceiling (`SPEC.md` `FW-23`): 76.3 %, margin 1,240,576. `r6b6q`'s is
  3,961,344, so 1.3 and libphy cost 40,960 bytes, and `__init_end` moved by the
  same amount, from `0x803C8000` to `0x803D2000`. The design's guess, +~20 KB,
  was half.
* **In the ELF** (量, byte search of `r6b7q.vmlinux.elf`): `rtl819x-switch 1.3`
  once; `rtl819x-switch 1.2` once, a comment in `config/mfgtest.sh`, whose
  `MT-PORT` accepts any `rtl819x-switch ` version; `rtl819x-mdio` once;
  `mdio-i-mean-it` once. Against `r6b6q`'s `System.map`, 103 global names are
  new — 32 `rtl819x_mdio_*`, the rest libphy's — and none is gone. The build
  logs carry 162 warnings each; this file's one is 1.1's `rtl819x_sw_lock`
  defined but not used.
* **No cited line of the driver moved.** Above the appended block, only the
  version string (line 118) and the comment over `rtl819x_sw_wr` (four lines,
  cited nowhere) changed, each in place. The ranges cited elsewhere — 88–92,
  93–97, 209–213, 323, 375, 560–564, 588–661 — and § 9.2's and `NET-127`'s
  (269, 278, 532, 553, 676, 689, 716) read as they did.
* **`imgprocs` 1.2**, 量 on the commit this lands in: 1.1's controls
  (`asicCounter` in `memory`'s place, § 8.14) with a `--witness NAME` option
  merged in. On `r6b7q` the default run prints what it prints on `r6b6q`, line
  for line (13 of 42 literals, 7 of them shared with retained non-vendor code),
  and `--witness rtl819x-mdio` finds the entry once; the same witness on
  `r6b6q` refuses (rc 2) — the control. `--witness` is an option rather than a
  fourth fixed control because the images cards still boot before 1.3 would
  then be refused. `--self-test` 16 of 16: W1 a carried witness reports, W2 the
  same image without the entry is refused with the option and reported without
  it, W3 the option repeats and a bare `--witness` is refused; three hand
  mutants (no refusal, no bare-name check, no `ok` label) each turn their own
  case red.
* **The suites that read this driver or its image**, run by the
  implementation on `2a3f5e2` plus this change: `storeseq` `r6b6q` → `r6b7q`
  green on every NIC function; `hazlint` 0 violations in 115,650 loads
  (`r6b6q`: 0 in 115,080); `mfginject` identical to `2a3f5e2`'s output (its
  fixtures stay 1.2); `bootbytes` 7 of 7, identical to `2a3f5e2`'s.

## 10.6 `mdiocheck`: the verbs, refusing and permitting, on the host

`tools/mdiocheck.py` cuts the appended block out of the driver **unchanged**
and compiles it with the host's gcc in the kernel's dialect (`-std=gnu89
-Werror`) inside a generated harness: a scripted MDIO controller (`STATUS` held
for a scripted number of reads, PHYs 0–4 with a register-31 page select,
`0x0000` at 5–31); phylib's register, scan and read path transcribed from the
staged tree (`mdio_bus.c:87-139`, `:182-221`, `:234-246`;
`phy_device.c:187-236`); the kernel's `simple_strtoul` (`lib/vsprintf.c:36-75`);
this arch's errno values; and IRQs-off sections, `udelay` and a mutex that are
counted.

Twenty-five cases, K0–K23 and K14b: every verb refused and permitted beside its
twin; the exact `MDCIOCR` words; a `pread` as six stores in one IRQs-off
section with the mutex taken outside it; the restore's retry and `dirty`,
including a register 31 that reads 0 over a restore that was never stored; the
timeout's positive control (at `bound 0`, with `STATUS` held for 3 reads, a row
reads `E145 E016 E016 E145 E016 E016`); the page at its widest (the four figures
in § 10.4 are K16's); a `cat` that issues nothing; stuck hardware spending the
one shot with `xrc -16` kept on every address. M0 runs the unmutated copy
through the mutants' own path, and M1–M20 each break one thing and must turn
the case named for them red. 量 on the commit this lands in: 46 of 46 — 25
cases, M0, and 20 of 20 mutants each killed by its named case. `SPEC.md`
`FW-146`.

It is a CI step, beside `linkprobecheck` in the `instruments` job (host gcc
only; nothing stands down). 量: `desk-sweep` ran that declared step from
`ci.yml` on a verified copy of the tree — 1 ran, 1 green, 13.7 s for its 46
lines — and `ci-census` over the capture reads 46 of 46 against the row's 46,
and red with the row set to 47. The owner's rule of 2026-09-26 admits a new
checker only against bricking, an `H601` leak or a misjudged result. This is the
driver's verb harness, the kind `nic15check` and `linkprobecheck` are, and a
verb that printed a wrong ID or a refusal it did not make would misjudge `D7`.

What it cannot see: the silicon — how long `STATUS` stays set, what register
31 reads back, whether the switch's PHY poller meets a selected page, what
`MDCIOSR` 30:16 means. Its fake was written from the same sources as the
driver, so a misreading shared by both passes. Nor phylib's device model beyond
the name check, nor sysfs, nor whether rsdk's gcc 3.4.6 compiles the block — the
two image builds answered that one.

## 10.7 The review and the owner's decisions, 2026-09-26

The design went through an adversarial review in three lenses (register and
API, build and blast radius, bench and DoD) and a synthesis. Its eight required
changes are in the code: the restore guaranteed or the operation refused; the
bound guard on `probe` and `pread`; the seven promptless rows; the vendor's
`/proc/rtl865x/phyReg` as a planned third source for `D7`; the delay argued by
equality; pages 0 and 1 only, with register 31's marks; `C-18`'s trigger
narrowed; and a per-address prediction for `scan`. The owner decided:

* **A.** `CONFIG_NET_ETHERNET=y` and `CONFIG_PHYLIB=y`, with every row
  `kconfig-delta check` enumerates declared from a build (§ 10.5).
* **B.** rlxfw writes PHY register 31, for the first time, for pages 0 and 1
  only; the restore is guaranteed at the fixed bound or the operation refused;
  `probe` and `pread` refuse with `-EAGAIN` unless `bound` is 10,000, without
  spending the one-shot probe; each address keeps its last transaction's rc.
  The vendor's `extRead N 1 19` through `/proc/rtl865x/phyReg` is a second
  source for the page-1 values on the card, and is not code in the driver.
  推: a power cycle resets the PHY registers.
* **C.** A new unlock token, `mdio-i-mean-it`, separate from the switch's.
* **D.** *Whether port 1 needs the patch* is observed at register level only.
  The functional clause is ⊘. Its price: two cable moves and a comparison arm —
  the cable moved to port 1, the same traffic sent, port 1's per-port counters
  compared with port 3's, and the host path lost while the cable moves. Its
  reason: one link partner cannot establish *not needed*. `C-18` reopens if PHY
  1's page-1 register 19 bits 15:1 differ from the value PHYs 0, 2, 3 and 4
  agree on (void if those four disagree), or if a port-1 link fault is ever
  observed. PHY 4's page-1 register 20 is recorded only: the vendor reads it
  back before adding to it, so its default is 未定 and its bit 1 triggers
  nothing.
* **E.** The seating is its own press on the 1.3 image, after `R6b-6`'s. (h),
  the start of `PSRP`'s 保留態, is ⊘ for now: it needs a cable move and a
  prediction. (i), `reset full` followed by `scan 0 4` (MDIO with
  `EnablePHYIf` 0), is `R6b-8`'s question, and it kills the network for that
  boot.
* **F.** Every change and wording fix of the synthesis applied.

Beyond the review, three changes the implementation made: the strict parser
(§ 10.4), which the harness found; `pread` takes `bus->mdio_lock` before IRQs
go off; and each address's scan rc starts at 1, *not scanned*, rather than 0.

## 10.8 The card, for after `R6b-6`'s seating

Pinned: nfjrom `548f4fae…`; the booted image identified by the tool comparing
`RLXFW-ID0` with `50E4AF55`, never by a typed value; every address from
`r3-4/out/r6b7q.System.map`. Zero flash-write commands, zero `FLR`, the map
bracket. Errno values on this arch: `EPERM` 1, `EIO` 5, `EAGAIN` 11, `EBUSY` 16,
`EEXIST` 17, `ENODEV` 19, `EINVAL` 22, `EPROTO` 71, `ETIMEDOUT` 145. Every
prediction below becomes a `cardnum` row when the card is written.

**At the loader**, same power cycle, prompt caught:

* **L1** `MDIOR 2`: 0–4 read `0x001c`, 5–31 `0x0000` (量, repeats `F2`).
* **L2** `MDIOR 3`: 0 and 1 read `0xc880` (量, `bench/2026-08-23/E.log` — the
  only register-3 reads in `bench/`); 2–4 `0xc880` (推); 5–31 `0x0000` (推).
* Then TFTP, the staged head read back, `J`.

**Under Linux:**

* **(a)** `cat /proc/rtl819x-switch`, first. `version rtl819x-switch 1.3`.
  Slot-0 `MDCIOCR`/`MDCIOSR` read `1F030000`/`00000000` (推: L2's last command
  is a read of address 31, register 3). `96181441`, slot 0's value in all 70
  committed dumps (`NET-28`), would mean the TFTP/`J` path issues that store
  after the prompt. `PSRP3` is the only `LinkUp` port, and `ifconfig` shows
  `rlx0` and `lo` only — otherwise the bit-8 detector is void for this boot.
* **(b)** `cat /proc/rtl819x-mdio`, still locked, byte for byte `mdiocheck`'s
  K1: `version rtl819x-switch 1.3`, `unlocked 0`, `bus 0 reg_rc 1`,
  `bound 10000`, `mdio_rd 0`, `mdio_wr 0`, `mdio_to 0 busy 0 retry 0`,
  `refused 0 wr_refused 0 again 0`, `spin 0 0 0`, `hi_or 00000000`, `dirty 0`,
  `scanned 00000000 j 0`, `phy0`–`phy4` `id - rc 1 xrc 1`, then `jiffies`.
* **(c)** The guards and the probe. `probe` while locked → `EPERM`.
  `unlock mdio-i-mean-it` → `RLXFW-MD-UNLOCK`. `bound 0`, then `probe` →
  `EAGAIN`: the page reads `again 1`, `reg_rc 1`, `mdio_rd 0`. `bound 10000`,
  then `probe` → `RLXFW-MD1=0000001F`: `bus 1 reg_rc 0`, `mdio_rd 10`,
  `mdio_wr 0`, `phy0`–`phy4` `id 001CC880 rc 0 xrc 0 drv 0 att 0`,
  `refused 1`, `again 1`. `ls /sys/bus/mdio_bus/devices` → `rlxsw:00` …
  `rlxsw:04` (`/init` mounts sysfs). A second `probe` → `EEXIST`.
* **(d)** `D7`: `phyN`'s id = `L1[N] << 16 | L2[N]`, for N = 0–4. The loader
  side is `NET-06` and `NET-24`, not `NET-39`, which holds BMCR and the port
  map. The third source: `echo read N 2` and `echo read N 3` into
  `/proc/rtl865x/phyReg` → `read phyId(N), regId(2),regData:0x1c` and
  `…regData:0xc880`, the form `C19-PHYID` printed; those reads do not move
  rlxfw's counters.
* **(e)** `scan 0 31`: `mdio_rd` 10 → 202.
  * 0, 1, 2 and 4: r0 `1100` (量 `C20` on PHY 0 under Linux, `X8` on 0–4 at the
    loader; 推 on 1, 2 and 4 under Linux); r1 `78C9` (量 `E12d` and `C20` on PHY
    0; 推 on the others); r2 `001C`; r3 `C880`; r4 recorded; r5 `0001` (量
    `E12e` on PHY 0; 推 on the others).
  * 3, the cabled port: r1 with bits 2 and 5 set (量 `X5`, `78ED`); r5 non-zero
    with bit 0 set (量 `X4`, `CDE1`, against this desk's RTL8153).
  * 5–31: r0 and r2 `0000` (量 `X8`, `F2`); r1 and r3–r5 `0000` (推).
  * `hi` `0000` on every row (推; the bits are 未定). Record `spin` and `hi_or`.
  * A mismatch refutes 1.3's address path even when `D7` holds: all five IDs
    are equal, so `D7` alone cannot see addresses 0–4 swapped among themselves.
* **(f)** The timeout's positive control: `bound 0`; `pread 0 0 16` → `EAGAIN`
  (`again 2`); `scan 5 5`; `bound 10000`; `scan 5 5`. Conditional on (e)'s
  `spin`: if its min is ≥ 1, the first row holds at least one `E145`; if its
  max is 0, it reads `0000` ×6 with no timeout, and the control is ⊘ for this
  press; between the two, only the accounting is predicted. In every branch
  each `E145` is one `mdio_to`, each `E016` one `busy` with no store, and
  `mdio_rd` rises by 6 − Δ`busy`. (The harness's model, `STATUS` held for 3
  reads, gives `E145 E016 E016 E145 E016 E016`.) The second `scan 5 5` reads
  `0000` ×6 and `mdio_to` does not move.
* **(g)** `C-18`: eight `pread`s, which fill the eight kept. `pread 0 0 16`,
  the unpaged control; `pread 0 1 16` (bits 15:13 read 110, 讀
  `rtl865x_asicL2.c:4177`); `pread a 1 19` for a = 0, 1, 2, 4, then 3, the
  cabled port, last; `pread 4 1 20`, recorded only. Predicted: `p0 0`, `p1 0`,
  `rs 0`, `rt 0`, `dirty 0` (推). `ps` is 未定: if register 31 does not read
  back, every paged read returns `-71` with `v` kept, and that is a reading,
  not a failure. If `p0` ≠ 0 at rest, `-71` with nothing written, and `C-18` is
  not observed this seating. Register 19's bit 0 reads 0 on all five (讀
  `:4193`, 量 `REVR`). With no retry: `mdio_rd` +29, `mdio_wr` +14. Read the page
  at once; then `scan 0 4` and `cat /proc/rtl819x-switch` must equal (e)'s,
  with the `lde` counts unmoved — the detector for a paged write landing on
  the wrong page.
* **(g′)** Decision B: `echo extRead N 1 19` into `/proc/rtl865x/phyReg`, for
  N = 0–4 → `extRead phyId(N), pageId(1), regId(19), regData:0x…`, equal to
  (g)'s `v`. That vendor path pages with no gate, no IRQs off and an unbounded
  poll, which is why it runs after (g).
* **`C-18`'s rule** is decision D's (§ 10.7).
* **(h)** ⊘ this press; **(i)** `R6b-8`'s.
* **(j)** `lock`, then a final page: `dirty 0`, `wr_refused 0`, `mdio_to` and
  `busy` as (f) predicted. A final `probe` → `EPERM`.

Card notes: nothing is typed while a `pread` may be timing out (≤ 130 ms with
IRQs off, nominal). Each `cat` renders twice and issues no MDIO command.
Numbers are typed in decimal without leading zeros.

## 10.9 What 1.3 does not establish

* Anything on the silicon: not one line of the block has run. `STATUS`'s
  latency, what register 31 reads back, whether the switch's PHY poller meets a
  selected page, what `MDCIOSR` 30:16 means, the probe on the die and the sysfs
  names are the card's.
* That the quiet boot capture is unchanged is 推: no boot mark was added and
  `bootbytes` reads 7 of 7, but nothing was booted. On a loud image a probe
  prints `rtl819x-mdio: probed` (`mdio_bus.c:129`).
* `mdiocheck`'s fake shares the driver's sources. 130 ms is an upper bound by
  counting; no scripted case exceeds 3 × bound.
* The loud image: only its oldconfig and its delta check ran.
* How the 40,960 bytes divide between libphy and the block.
* The vendor MDIO call census (25 read, 43 write, 20 functions) is the design's,
  not re-derived.
* That IRQs off contains `one_sec_timer` is 推; `/init` does not arm it, and a
  card that opens `eth0` does.
* The restore's residual: hardware busy past both bounds (~20 ms), or a
  register 31 that reads 0 whatever it holds. `dirty` and `rs` say which was
  seen; the desk excludes neither.
* `D7` and `C-18`. `R6b-7` stays open for its card and its seating.

# 11. 2026-09-27 (`R6b-8` 8a) — the census: is any of the vendor's Ethernet driver left in `vmlinux`

## 11.1 Why, and the scope

`R6b-8`'s DoD (`PROGRESS.md`) asks for `ping` both ways "with no vendor
Ethernet code in `vmlinux` (a symbol census)". A census that reads 0 is making
a claim, so `tools/ethcensus.py` is three censuses, two of which share no
parsing, each with a control that must read non-zero on a vendor-present build:

1. **object** — the leaves the link names, walked from `.vmlinux.cmd` down
   every `ld -r` `.cmd`: 0 in scope;
2. **symbol** — the FUNC and OBJECT names the reference build's in-scope
   objects define, looked up in the new `vmlinux`: exactly the ten seam names
   (the design's § 1.2), each defined by the seam object alone;
3. **string** — `imgprocs`' NUL-bounded search, inverted, on the flat image:
   0 of the vendor-unique `/proc/rtl865x/` names, with `rtl819x-switch`
   present and a synthetic name absent.

`SPEC.md` `NET-137`. The scope is the owner's ruling of 2026-09-26: vendor
Ethernet code is every object under `drivers/net/rtl819x/` plus
`drivers/net/rtk_vlan.o`. The vendor code that stays is printed by every run
with its leaf count in the build read — on `r6b6q2` the IPv4 fast path
(`net/rtl/fastpath/`, 7 leaves), the feature glue (`net/rtl/features/`, 3),
the WLAN driver (`drivers/net/wireless/rtl8192cd/`, 42) and
`drivers/char/rtl_gpio.o` (1), which writes `PIN_MUX_SEL` (§ 8.9). That
printout is the owner's four, not every vendor leaf the census does not read:
`spi_probe.o`, `spi_cmd.o`, `spi_common.o` and `spi_flash.o` under
`drivers/mtd/chips/rtl819x/`, and `drivers/mtd/maps/rtl819x_flash.o`, are
vendor sources with no counterpart in `config/rlxfw-src/`, outside the scope
and not printed (the review's A10).

## 11.2 The numbers on `r6b6q2`, and how each was derived

Every number here is 讀: read at the desk on 2026-09-27 out of `r6b6q2`'s build
artefacts (recipe `acf8ed3d`, `vmlinux` sha256 `9e0ff326…`, 4,486,315 bytes,
the tree `$FWRE_WORK/rebuild/r3-4/cells/r6b6q2/top/linux-2.6.30`) by an
instrument, static and true of that build; none was measured on the device.
(The tool's docstring, and § 8.14 for its per-object search, mark this kind of
reading 量.) Every row was produced by the tool and again by a second source
that shares no code with it — a walker that classifies each `.cmd` by the
program it runs, a hand ELF32 and `ar` reader, `nm` and `objdump -t`
(`$FWRE_WORK/rebuild/s114/r6b8a/second/` and `adv/`) — and the two agree.

| what | value | V | how |
|---|---|:-:|---|
| leaves the link reads | 627, through 89 `ld -r` links from the 22 roots in `.vmlinux.cmd` | 讀 | every `.cmd` whose command has `-r` and `-o`, walked down: 594 gcc-built leaves, 31 empty `rm; ar rcs` `built-in.o` (8 bytes, `!<arch>\n`), and `lib/lib.a` and `arch/rlx/lib/lib.a` with 31 and 9 members. No object is reached twice and none is missing on disk. Completeness control: the 119 `vmlinux` globals no walked object defines are all named in `arch/rlx/bsp/vmlinux.lds`, and dropping `rtl_nic.o` from the walk raises them to 187 |
| in scope | 22: 21 under `drivers/net/rtl819x/`, and `rtk_vlan.o` | 讀 | after `os.path.normpath`, which folds the `rtl865x/../common/` spellings. Composite control: the FUNC/OBJECT entries of `drivers/net/rtl819x/built-in.o` equal the union of its 21 leaves' as a multiset (905 = 905) |
| symbols the two parsers agree on | 13,897 defined, named, non-SECTION/FILE entries over the 634 objects with content (594 leaves and 40 archive members); 0 read by one parser only | 讀 | `mips-linux-gnu-readelf -W -S -s`, split field by field with `st_other` taken as a bracket group, against `mips-linux-gnu-nm -f sysv` (BFD, not readelf's own reader), compared as multisets on member, name, binding, type, value, size and section. `vmlinux`'s 13,821 agree the same way |
| FUNC/OBJECT names in scope | 907 (920 entries: 722 FUNC, 198 OBJECT), 512 of them global or weak; 0 NOTYPE or other-typed | 讀 | the 22 leaves' symbol tables |
| MIPS16 among them | 13: `_swNic_send`, `dev_alloc_skb_priv_eth`, `interrupt_dsr_rx`, `interrupt_isr`, `is_rtl865x_eth_priv_buf`, `re865x_start_xmit`, `release_pkthdr`, `rtk_dequeue`, `rtk_queue_tail`, `rtl8651_rxPktPreprocess`, `rtl_MulticastRxCheck`, `rtl_rxSetTxDone`, `swNic_receive` | 讀 | `st_other` `0xf0`, which `nm` cannot show. Over all leaves: 39 defined MIPS16 entries, 0 undefined |
| excluded by name | 8: `__func__.0`–`__func__.3`; `early_console_write` and `prom_putchar`, also in `arch/rlx/kernel/early_printk.o`; `rtk_dequeue` and `rtl_isPassthruFrame`, also in `drivers/net/wireless/rtl8192cd/8192cd_util.o` | 讀 | a name an object outside scope also defines is in every `vmlinux` and cannot discriminate. `rtk_dequeue` is the eighth: MIPS16, and LOCAL in both `rtl_nic.o` and `8192cd_util.o` |
| the population | 899 = 907 − 8 | 讀 | `tools/ethcensus-population.txt`, written by `ethcensus.py population`; a second run reproduces it byte for byte, and the second source's set equals it |
| population names in `System.map` | 898; `__exitcall_re865x_exit` is not there | 讀 | `System.map`'s third column, and again through `vmlinux`'s own symbol table: the same 898 |
| registered `/proc/rtl865x/` names | 42 | 讀 | `imgprocs.parse_names` over the tree's `rtl865x_proc_debug.c`; an independent regex also gives 42 |
| vendor-unique `/proc` names | 6: `asicCounter`, `diagnostic`, `fc_threshold`, `mmd`, `phyReg`, `port_status` | 讀 | a NUL-bounded search of every `SHF_ALLOC`, non-`NOBITS` section of the 634 objects, through the tool's own ELF and `ar` reader rather than `objcopy`: each of the six is carried by `drivers/net/rtl819x/rtl865x_proc_debug.o` alone. The seven carried by retained code — `arp`, `igmp`, `ip`, `mac`, `memory`, `pppoe`, `stats` — equal `imgprocs.SHARED`, and the tool refuses if they differ. Of the seven only `mac` and `memory` are also carried by the vendor object, which therefore carries 8, `NET-42`'s 8: the 42 split 6 vendor-only, 2 both, 5 retained-only and 29 carried by nothing |
| the string control on the flat image | 6 of 6, each once, all in `.rodata` (`0x8029ae34`–`0x8029ae68`); `rtl819x-switch` 1; `zzzz-not-a-name` 0 | 讀 | `objcopy -O binary` of `vmlinux`: 3,961,344 bytes, sha256 `8e0799f1…`, the same bytes as a hand concatenation of its one `PT_LOAD` at `0x80000000`. Each hit is attributed to `rtl865x_proc_debug.o` |
| the segment-113 parser against `nm` | REFUSED: 43 disagreements, 14 of them in scope | 讀 | the tool with its parser swapped for the design's regex. 43 = 39 `[MIPS16]` lines + 4 sizes above 99,999, which readelf prints in hex (`desc_buf`, `obj_buf`, `skb_buf`, `eth_skb_buf`); in scope, 13 MIPS16 names + `eth_skb_buf` = 14 = 907 − 893 |

`check` on `r6b6q2` itself, the vendor-present reference, reads RED on all
three, and that is the positive control: object 22 of 627, symbol 898 of 899
(`System.map` agreeing), string 6 of 6, and each of the ten seam names printed
with the vendor object that defines it.

## 11.3 The design's numbers this supersedes

The design (segment 113, `$FWRE_WORK/rebuild/s113/r6b8/`, not committed) read
`readelf -sW` with a regex that assumed `Vis` is followed by `Ndx`. A MIPS16
function carries `[MIPS16]` between them, so its line did not match and was
dropped without a word — the vendor's `swNic_receive`, `_swNic_send`,
`re865x_start_xmit` and `interrupt_isr` among them — and a size above 99,999
prints in hex, which a `\d+` field also drops. Each of its numbers, once:
893 FUNC/OBJECT names → **907**; 505 global → **512**; 7 excluded → **8**
(it could not see that `rtk_dequeue` collides with the WLAN driver's); a
population of 886 → **899** (the difference is the 12 non-excluded MIPS16 names
and `eth_skb_buf`, and nothing the other way); 885 in `System.map` → **898**;
the string control's 13 → **6** (13 was the flat image's whole-registry count,
retracted by `NET-42` on 2026-09-26, § 8.14). The step row's *22 objects and
898 names* put the population's `System.map` subset where the population
belongs. The 627 leaves and the 22 in scope stand as the design wrote them.

## 11.4 The flat image a census must refuse: the staged tree's `rtkload/vmlinux_img` is the vendor drop's kernel

讀: `r6b6q2`'s staged tree holds `rtkload/vmlinux_img` (2,953,660 bytes), and its
sha256 is `48b1a171…` — the value the `marks_verify_absent` line of
`r6b6q2.manifest` calls `drop-kernel`, the vendor drop's own kernel, under the
name a flat image goes by. A census, or a card, that took "the tree's
`vmlinux_img`" would read the vendor's image as this build's. `ethcensus check`
refuses any image that is not `objcopy -O binary` of the build's own `vmlinux`,
and refuses this one at the desk (`tools/test-ethcensus.sh`, the reference
layer). That gate matches the real pipeline: for all 37 rlxfw builds under
`$FWRE_WORK/rebuild`, rtkimage's `vmlinux_img` is byte-identical to host
`objcopy` of its `vmlinux` (the review, 2026-09-27). `tools/imgprocs.py` has
no such guard: it reads the image it is given.

## 11.5 The controls

`ethcensus.py self-test`: 51 of 51, on synthetic kbuild trees assembled with the
host binutils — a vendor-present reference, a vendor-free tree with the seam,
the five required mutants (an eleventh vendor name in the seam, a seam name
defined by a second object, an empty population, a surviving MIPS16 vendor
function in a kept object, the segment-113 parser against `nm` in both modes),
and one tree per census and per guard on which only that one decides.
`tools/test-ethcensus.sh`: 74 of 74 at the desk; 66 in CI's `instruments` job,
where one skip line, `reference build`, stands for the 8 cases that read
`r6b6q2`'s tree (`tools/ci-expected.tsv`). Its mutation layer turns each named
case red with one of seventeen edits to the tool (`X1`–`X17`), runs the
unmutated copy through the same path (`M0`), and requires the self-test to
REFUSE without the host binutils (`NB`): there is no binutils skip. The review
wrote 24 further mutants; the full suite kills all 24 and the self-test alone
19. The other five — `nm`'s `W`/`w` mapping, the left NUL in the carrier
search, the walk into composite links that are not `built-in.o` and into `.a`
inputs, and `ABS` symbols — die only in the reference layer, so CI cannot kill
them.

## 11.6 What the census does not establish

As the tool prints: vendor code under another path (the scope is a path rule);
a vendor function the compiler inlined into an out-of-scope object (it leaves
no symbol); a NOTYPE label (0 in scope on `r6b6q2`, counted and printed, not in
the population); and whether the image is the one the board boots —
`RLXFW-ID0` is the bench's half. A name absent is a name no symbol-table entry
carries, not proof that no byte of vendor code survives. And, where the review
limits a reading:

* **A RED can be an operator's error** (A7). An empty `--seam`, or one given as
  an absolute path, reads RED as *seam names not defined by the seam object
  alone*, so a RED from `check` can mean vendor code or a misspelled seam; a
  repeated `--seam` silently takes the last value. Read the seam line before
  the verdict.
* **A COMMON symbol cannot pass the parser cross-check** (A8): readelf prints
  its alignment as the value and `nm` its size, so a leaf with a `.comm` is
  REFUSED as a disagreement between the parsers rather than named. `r6b6q2`
  has none (the kernel builds with `-fno-common`).
* **The string census reads the embedded initramfs too** (A9, § 11.7's S2).
  The flat image carries `.init.ramfs` (934,400 bytes, an uncompressed cpio),
  while the vendor-unique derivation reads kernel objects. On `r6b6q2` the
  ramfs holds no NUL-bounded occurrence of the six or of `rtl819x-switch`.
  推: a NUL-bounded literal in a future userland reads RED as *carried by no
  leaf* — a false RED, never a false GREEN — and the `rtl819x-switch` control
  could be met from the ramfs rather than the kernel.
* **Five population names are compiler-numbered function-static locals**
  (A12): `info.4`, `pMbufList_start.3`, `pPkthdrList_start.2`,
  `totalRxPkthdrRingCnt.0`, `totalTxPkthdrRingCnt.1`. A new rlxfw static with
  the same name and ordinal reads RED; the RED names its definer, and it is a
  collision to read before acting.
* **The seam object's path is not decided.** The suite uses
  `drivers/net/rlxfw-seam.o` as a placeholder, which on `r6b6q2` reads *not
  among the leaves*; 8b's path goes in when the seam lands. 🔄 2026-09-27: it
  landed at that path (§ 13.5), and `check` on `r6b8bn` names it. The ten seam names
  are a constant from the design's § 1.2, and the tool refuses a population
  that lacks one.
* **The fixture is a vendor name list.** It commits the 899 names (names, no
  bytes) and the reference tree's local path on its `# build` line.
* The vendor Ethernet section sizes the design quotes were not re-derived; the
  census does not use them.

## 11.7 Two corrections to § 8.14 and `NET-42`, and one carried item

The census's second source re-read the per-object `/proc` search of 2026-09-26
and found two errors in how it was stated; neither changes a name set.

* **S1 — 667 was not a count of compiled objects.** `r6b6q2`'s link has 634
  objects with content: 594 gcc-built leaves and 40 archive members. 667 is
  627 leaves + 40 members, so it also counts the 31 empty `built-in.o`
  archives and the two `lib.a` containers, which carry no strings of their own
  (推: that is how 8-0 got 667 — its search script was not read, and 627 + 40
  is the only decomposition found).
* **S2 — `arp` and `ip` have a third carrier.** `usr/initramfs_data.o` carries
  both, NUL-bounded, in `.init.ramfs` (`PROGBITS`, `SHF_ALLOC`, `0xe4200`
  bytes; its `.data` is empty). The 2026-09-26 search read `.rodata` and
  `.data` only; the census reads every `SHF_ALLOC`, non-`NOBITS` section, as
  the flat image does. The six vendor-unique names have no carrier outside
  `rtl865x_proc_debug.o`, so the 6 and the 7 stand.

Both are fixed where they stand, in § 8.14 and in `SPEC.md` `NET-42`.
🔄 **2026-09-27: `tools/imgprocs.py`'s comment above `SHARED` is corrected**
with 8c-code's landing (§ 12.7). It said *667 compiled objects searched* and
named only the `.rodata`/`.data` carriers of `arp` and `ip`, and it waited for
seating 43 in case a card pinned the tool by digest; none of the three did.

# 12. 2026-09-27 (`R6b-8` 8c-code) — `rtl819x-view` 1.0: a `/proc` node that only loads, admitted word by word

## 12.1 Why, and why a file of its own

8c-cells reads the MIB, the VLAN and netif tables and a set of switch
registers on this die before `asicCounter` leaves the image (8g), and the step
row asks for each instrument to be shown refusing and permitting before it
runs. rlxfw has to do those reads without writing anything. The page-0 MDIO
read needs no new code: 1.3's `pread a 0 r` is one read and no write, with
IRQs off, behind `mdio-i-mean-it` and `bound 10000` (讀, `mdiocheck` K10, K8
and K2). Everything else is `config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-view.c`,
`rtl819x-view` 1.0, 709 lines. `SPEC.md` `NET-138`.

It is a file of its own and not a 1.4 of `rtl819x-switch.c` (decision D1).
Seating 43's third press, card C, pins HEAD's `rtl819x-switch.c` and
`tools/mdiocheck.py` by sha256 (讀, the draft's `drv-head-is-cell` and
`sha-mdiocheck` rows), and `mdiocheck` cuts that driver from its 1.3 banner to
the end of the file, so a block appended there would enter its harness. The
new file shares no code and no symbol with `rtl819x-switch`, which keeps its
own read path, its `PSRP` bookkeeping and its MDIO gate.

## 12.2 The node

`/proc/rtl819x-view` (0644) is created at `device_initcall`. The boot loads
nothing and prints nothing unless the creation fails (`RLXFW-VW0-NOPROC`).
Three verbs are written to it:

```
mib              the 225 MIB words of ports 0-6, one load each
tbl vlan|netif   the VLAN table's 16 slots, or the netif table's 8
peek A [n]       n words (1-16, default 1) from the KSEG1 address A
```

A `cat` prints the cached result of the last verb that loaded anything, and
loads nothing itself, so one `cat` rendering twice (`FW-64`) costs no load.
The page is five header lines (`version rtl819x-view 1.0`, `admit 298`,
`last` with that verb's jiffies and rc, the counters `n_mib n_tbl n_peek
refused busy ld`, and `ref`, the last refused word and its reason), the
result, and `jiffies` as the terminator. `ld` counts every load the file
makes: `rtl819x_view_ld()` is its only load, and **it has no store accessor
at all**, so there is no unlock. The parser is 1.3's strict one — a field
starts with a digit, one space between fields, nothing after the last — with
a 10-character cap per field. A ten-digit decimal above 4294967295 still wraps
modulo 2³² on this kernel; the admission check sees the wrapped word and the
page prints it, so a wrap can reach only an admitted word, under its own
address. `#error` under `CONFIG_SMP` or `CONFIG_PREEMPT`, as 1.2's counters.

Walked from the formats with every field at its widest: the header is at most
193 bytes, the widest result (`mib`) 2,231, the trailer 19, so a page is at
most 2,443 bytes; the widest real page is 2,441 (`last mib`). The 3,900-byte
budget cannot fire at these widths. `viewcheck` V14 measures all four figures
against the driver's comment. The page format, its 21 `sprintf` literals and
what `viewdecode` refuses were frozen for the decoder by the file's sha256,
`68ec4f21…` (session material, not in this repository); the source owns the
format, and a changed literal is a version change (1.1: 311 words, 26 literals, ≤ 3,774 B, § 17.5).

## 12.3 The admission table: 298 words, and the one word the rule turns on

**The rule** (decision D2): a word is loaded only if it lies inside one of four
named blocks **and** two of three sources place it — B, the header the build
compiles (`drivers/net/rtl819x/AsicDriver/rtl865xc_asicregs.h`, sha256
`e29c3051…`, 3,537 lines); D, the draft datasheet; and 量, a value this die
printed for the word in a capture committed under `bench/`: a loader `DW`
dump, or, for the MIB, the vendor's `/proc/rtl865x/asicCounter` dump.
`CLAUDE.md`'s rule for a register value entering code, applied to an address
entering a read path.

| block | words | what (B's names) | second source |
|---|---:|---|---|
| switch `0xBB804000`–`0xBB804FFF` | 54 | `MACCR`…`PMCR`; `BSCR`; `PITCR`, `PCRP0`–`PCRP8`; `P0GMIICR`, `P5GMIICR`; `CVIDR`, `SSIR`, `CRMR`, `BISTCR`; `MEMCR`, `BISTTSDR0`–`3`; `LEDCREG`, `LEDCR1`, `LEDBCR`; `TEACR`…`MGFCR_E0R2`; `VCR0`, `VCR1`, `PVCR0`–`PVCR4`, `PBVCR0`; `SWTACR`, `SWTASR`, `SWTAA`; `TCR7` | loader `DW` dumps, or D Tables 57, 60–62, 67–70 |
| MIB `0xBB801000` | 225 | the 32 words per port `rtl865xC_dumpAsicDiagCounter` reads, ports 0–6, and `CpuEvent` at `0x084`: 7 × 32 + 1 | the vendor's `asicCounter` dump |
| CPU interface `0xB8010000` | 17 | `CPUICR` … `CPUQDM4`/`5` (`0x00`–`0x38`), `CPUTPDCR2`, `CPUTPDCR3` (`0x60`, `0x64`) | `NET-48` (`DW B8010000 16` twice, `DW B8010060 4`) |
| `PIN_MUX` | 2 | `PIN_MUX_SEL`, `PIN_MUX_SEL2` (`0xB8000040`, `0xB8000044`) | D Tables 35–36 |

`PSRP0`–`PSRP8` (`0xBB804128`–`0xBB804148`) are refused with a reason of their
own, `psrp`: bit 8 clears when read (B `:1328`, D Table 65, 量 `NET-11`), and
`/proc/rtl819x-switch` 1.2 already reads them and keeps what it consumes.
Everything else is refused **before any load, the whole request with it**:
`peek A n` checks all n words first. Flash (`0xBD000000`–`0xBD3FFFFF` and
`0xBFC00000` up) lies in no block, so `H601` cannot reach a capture through
this node. The admission is by exact KSEG1 address, so a KSEG0 alias of an
admitted register and its physical address are refused like any other word.
Out of the MIB: `MIB_CONTROL` at `0x000` (a write restarts the counters, and it
is not read either), the five B-only words per port the vendor's dump does not
read (`0x10C`, `0x110`, `0x814`, `0x828`, `0x830`), and ports 7–8. Out of the
CPU interface: `0x3C`, `0x68`, `0x6C` (a reading, no name) and `0x40`/`0x44`
(`DMA_CR1`/`2`, B only).

**The MIB's 量** is the vendor's dump of exactly these words in 266 committed
`.log` captures at `8520b6c` (291 files hold the string `CpuEvent`), equal to
the netdev's own counts byte for byte (`NET-46`) and cumulative across 76 reads
(`notes/nic-driver.md` § 26). For the 28 words of the 14 byte-counter pairs
(`ifInOctets` and `ifOutOctets`, lo and hi, on seven ports) the dump prints
only `lo + (hi << 22)`, so their 量 is of that sum and not of each word. D has
no MIB section.

**The second source for the table itself** (the proposal's R5: driver and
harness are two copies of one transcription and agree by construction) is a
census that shares no code with either, in the session's scratch area
(`$FWRE_WORK/rebuild/s114/r6b8c/census/`): B parsed with the build's defines
(`-D CONFIG_RTL_8196E -D CONFIG_RTL_819X`), D's extract parsed for register
placements (41 placements, 27 distinct addresses in the four blocks), and every
loader `DW` and every vendor-memory read committed under `bench/` at `8520b6c`
(11,410 files; 692 `DW` commands, 71 memory-node reads). Counted with **any**
reading as 量, it admits **299**; the one difference is `0xBB804500`. Counted
with 量 limited to `DW` dumps and the `asicCounter` dump, it reproduces the
table's **298** exactly (its control C7) — no word the table lacks and none it
has that the census does not place. The review's sweep of the compiled driver
(40,960 `peek` requests in a model where every word of the four blocks can be
loaded) found the same single difference and no other.

**`0xBB804500`**, `SBFCTR`/`SBFCR0` in B (`:1673`–`:1674`, *System Based Flow
Control Threshold Register*), printed `000000F4` on each of the three reads
this repository holds, all through the vendor's `/proc/rtl865x/memory`
(`bench/2026-09-21b/B5-REGc`, `B5-REGc2`, `D2-REGa-a2`; the first shares its
command line with a corrupted read of another word and was counted from its
own clean line). D does not place it. 1.0 refuses it because its 量 does not
count a memory-node read; the driver's comment says so and names the word.
**Decided at the landing, 2026-09-27: refused in 1.0, and the `peek` window
stays at 298 two-source words.** By `CLAUDE.md`'s letter the word has two of
the three source kinds — the header, and a `devmem`-class read (a kernel load
of the address, three times the same value) — so the narrower 量 is the
table's own convention, not a repository rule, and the refusal does not rest
on it. It rests on cost against need: admitting one word changes the table,
which is a version change (the page's `admit 298`, which `viewdecode` checks;
`viewcheck`'s model and tallies; the format the decoder was frozen against)
and two rebuilds from a fresh stage, while 8c-cells can read the word on the
same vendor-present image through the vendor's memory node under `cardcheck`'s
HW-1 (`read 0xBB804500 4` loads `0xBB804500` to `0xBB804510`, inside the switch
window, touching no refused word) — the way all three readings were taken. It
is 8d's to admit, with the one-source words (`QNUMCR`, `CSCR`, `EEECR`,
`IBCR0`–`2`, `WFQRCRPn` and the rest), once 8c-cells has read them another
way and the table changes anyway (1.1 admits the thirteen: 311, § 17.5). `SPEC.md` `NET-139`.

## 12.4 The table read, and the premise of `NET-28` 殘留 it refutes

讀 `_rtl8651_readAsicEntry`
(`drivers/net/rtl819x/AsicDriver/96E/rtl865x_asicBasic.S:1043-1215`), the
reader the vendor's VLAN and netif getters call. It first asks
`rtl865x_accessAsicTable` (`:531-617`) whether the table may be read, and for
types 4 (netif) and 6 (VLAN) the answer is yes whatever the ASIC function
word holds: neither type's bit is in its three masks (`0xe22`, `0x8`,
`0x4000`). It then loads `SWTACR` (`0xBB804D00`) until bit 0,
`ACTION_START`, reads clear, with no bound, and then, up to ten times
(`li $16,10`), loads the slot's eight words at `0xBB000000 + (type << 16) +
(slot << 5)` into a first buffer and the same eight into a second and compares
them. Equal ends the tries; after ten unequal ones it copies the second buffer
out and returns success. **It stores nothing.** The `StopTLU` variant (`:1216`
on), which sets `EN_STOP_TLU` in `SWTCR0`, has no caller in
`drivers/net/rtl819x/` (讀, a grep over its `.c` and `.h`: one declaration in
`rtl865x_asicBasic.h`, no call).

`tbl` copies that reader with the `SWTACR` wait bounded at 10,000 polls,
`udelay(1)` apart (1.3's MDIO bound): past it, `-EBUSY` with the slot named and
no table load after it. It prints the second buffer, the number of tries, and
`eq` or `mis`. Base, types and slot counts are B's (`REAL_SWTBL_BASE` `:151`;
`TYPE_NETINTERFACE_TABLE` 4 and `TYPE_VLAN_TABLE` 6 in `rtl865x_asicBasic.h`;
16 VLAN slots under `CONFIG_RTL_8196E` and 8 netifs in `rtl865x_asicCom.h`),
the stride is the reader's `sll $2,$18,5`, and D has no table section. 量:
`SWTAA` reads `BB060100` at the loader prompt (`NET-28`) and `BB040020` under
Linux on the vendor-present image (`NET-34`), both inside these windows on
slot boundaries. ⚠️ `rtl8651_getAsicVlan` reads index = vid
(`rtl865x_asicCom.c:146`) while the vendor's writer searches for a free slot,
so a slot number here is not a VID, and the decoder never takes one for the
other.

**`NET-28` 殘留's settling cell rested on a false premise.** It read *the same
boot reads `SWTAA` and `0x4D48` before and after 8c's table-read verb changes
`SWTAA`*. Neither the vendor's reader nor `tbl` writes `SWTAA`, so no table read
can move it. The two states this die has already been read in do differ:
`SWTAA` is `BB060100` at the loader, where `0x4D48` reads the same value (量,
block 24), and `BB040020` under Linux (量, `NET-34`). One boot that reads both
words at the loader prompt and again under Linux therefore decides whether
`0x4D48` follows `SWTAA` (推: it is a mirror of it). `0x4D48` has one source —
a reading, no name in B's live branch, none in D — so `peek` refuses it, and its
Linux-side read goes through the vendor's `/proc/rtl865x/memory`, bounded by
`cardcheck`'s HW-1 (§ 12.7): `read 0xBB804D48 4` loads `0xBB804D48` to
`0xBB804D58`. The § 17 row is reworded to that cell. Its other half stands:
`PLITIMR` (`0xBB804420`) is admitted, so 8c-cells reads it on the vendor boot
with `peek` and compares it with the loader's `07FAC688`.

## 12.5 `NET-134` 殘留 changes instrument for `QNUMCR`

`NET-134` 殘留's cell read `0xBB804754` (`QNUMCR`) and `0xBB804300` (`LEDCREG`)
at the loader prompt and again on the vendor boot *with `peek`*. `LEDCREG` is
admitted (B, and D Tables 67–70), so `peek` reads it. `QNUMCR` has one source,
B, so `peek` refuses it before any load; its vendor-boot read goes through the
vendor's `/proc/rtl865x/memory` (`read 0xBB804754 4`, which loads
`0xBB804754` to `0xBB804764`, inside HW-1's switch window and touching no
refused word). The loader half is unchanged. The § 17 row is reworded to say
so; the rule that a value enters code only on two sources is unchanged.

## 12.6 The vendor's `/proc/rtl865x/memory` loads five words for every line it prints

讀 `drivers/net/rtl819x/rtl865x_proc_debug.c` as this image builds it
(`CONFIG_RTL_DEBUG_TOOL=y`, `CONFIG_RTL_PROC_DEBUG` unset). `proc_mem_write`
(`:4115-4178`) hands `read ADDR LEN` to `memDump(ADDR, LEN)` (`:115`) and
`write ADDR DATA` to a store of that word followed by a load of it, each number
through `simple_strtol` with base 0 and neither bounded. `memDump` prints
LEN/16 + 1 lines of up to 16 bytes (`:131`–`:132`) and, for every line, **loads
five words**, `(line & ~3) + 0, 4, 8, 12, 16` (`:139`–`:143`), before its
`max == 0` break (`:150`). So `read A 4` loads `A` to `A + 16` — five words —
and prints one; `read A 16` makes ten loads over `A` to `A + 32` and prints
four. The `4` a card types is a byte count: `NET-33` measured that it prints one
word. A memory-node read is therefore never a one-word read, and what bounds it
is its footprint, not LEN. One more thing the same reading found: the handler
refuses `len > 64` and then writes `tmpbuf[len] = '\0'` into a 64-byte buffer,
so a 64-byte write stores one byte past it (讀; no card sends one, and HW-1's
longest form is 28 bytes). `SPEC.md` `NET-139`.

## 12.7 The host tools

**`tools/viewcheck.py`** cuts `rtl819x-view.c` below its includes, unchanged,
and compiles it with the host gcc in the kernel's dialect (`-std=gnu89
-Werror`) inside a generated harness: a sparse MMIO model in which each of the
298 admitted words and the 192 table words has a value and a load counter, and
**any store, or a load of any other address, ends the harness with exit 9**,
so a refusal before the load is observable. The model's word list is written
from the proposal's table, not from the driver. V0–V17, 18 cases: every verb
refused and permitted beside its twin, every word of the four blocks, the
`SWTACR` bound at slot 5 and at slot 0, a torn slot, a `cat` that loads
nothing, the widest page, the strict parser and its wrap. M0 runs the unmutated
cut through the mutation path; M1–M25 each turn the case named for them red.
V17 and M23–M25 came from the review: the three resets at the top of
`rtl819x_view_tbl` survived V0–V16 when deleted, because V7 stops at slot 5,
after slots 0–4 have rewritten every per-slot field. 44 lines (1.1: 69, § 17.5), a CI step in the
`instruments` job and its `tools/ci-expected.tsv` row. What it cannot see is
the silicon, and its model shares the table's sources.

**`tools/viewdecode.py`** decodes `/proc/rtl819x-view` pages (every word named
from B, with D's name beside it where D's differs), renders the vendor's
`asicCounter` text from a `mib` page's raw words with the vendor's
`lo + (hi << 22)` (`rtl865x_asicCom.c:1506`, one source), and brackets a view
read between two counter readings (`before <= view <= after` for each of the
211 counters the vendor prints). Its self-test is 22 cases — A1, A2, B1–B4,
C1, C2, D1, D2, E1–E12 — M0 and M1–M10: 33 lines (1.1: 41, § 17.5), a CI step and its row. B1
requires the driver's 21 `sprintf` literals verbatim; B3 decodes the pages
`viewcheck`'s harness gets from the compiled driver. **A1 is a finding.** The
proposal expected every committed `asicCounter` capture to re-render byte for
byte; at `8520b6c`, 231 of the 266 cannot — 23 are clean, 12 carry printk
times, 231 are interleaved with other console output (one foreign character in
front of each of their lines; traced in one capture to `cat`'s tty output of
`/proc/rtl819x-nic` draining between printks) and 0 are cut by the capture's
end. The parser refuses the interleaved ones, and a self-test-only reader finds
all 86 lines behind the foreign characters. On this landing's base, `558bd4e`,
with seating 43's captures in, it reads 342: 23 clean, 12 printk-timed, 307
interleaved, 0 cut. A cut shape (floor 0) exists so that one capture ended by a
`--seconds` cap cannot hold the step red for good (A2 is its positive control,
M9 and M10 its mutants). The names, the VLAN and netif field layouts and the
`<< 22` rest on B alone.

**`tools/mkinitramfs.py` 1.2**: `build --init FILE` replaces the source of the
declaration's one `/init` row and nothing else (decision D6: no second
declaration, which would be a second owner of the file list). It refuses a
file that is not tracked under `config/`, differs from the index, is not
`100755` there, or whose first command is not the rung-1 `echo`, because the
kernel falls through to `/bin/sh` when `/init` cannot be executed and on the
quiet console that is a shell with nothing saying why. Without `--init`, 1.2
emits a spec and manifest byte-identical to 1.1's. Controls 34 → 43 (I1–I9),
`test-mkinitramfs-mutants` 12 → 27 lines (M11–M25). `notes/kernel-build.md`
§ 9's count, which still read 23, now reads 43. `config/rlxfw-init-quiet.sh`,
1,859 bytes, sha256 `fd78c441…`, is `config/rlxfw-init.sh` (2,153 bytes)
without its LAN block: the rung-1 line, the two mounts and `exec /bin/sh`. It
opens no interface and writes to no `/proc` node, so `eth4` can be the first
interface opened after power (`NET-25`'s NB-1), and it names no driver's node,
so no marks witness can be met by its text (`FW-143`). **`RECIPE_ID` cannot
tell an image built with `--init` from one built without it from the same
tree** (讀: both `/init` files are always under `config/`, which is all the id
digests) — `FW-99`'s second instance; the image sha256 and the boot capture
can.

**`tools/cardcheck.py`, HW-1**: rtl819x-view refuses flash and `PSRP` for
itself, but 8c-cells reaches one-source words (D5) and makes its one write (D4)
through the vendor's memory node, which bounds nothing (§ 12.6), and no tool
screened what a card sends it. One form per simple command, `echo read 0xADDR
LEN` (LEN a decimal 1–256) or `echo write 0xADDR 0xDATA` into the node; a
read's whole footprint must lie in one register window and touch no `PSRP` word
and not `0xBB804600`; a flash alias is refused naming `flashwin`'s region; a
write must lie in a write window and be declared in the card's `memwrite`
fence. Measured before the rule was written: 31 committed sends name the node,
and 5 distinct (card, payload) pairs on three frozen cards are refused; those
three are excused by that exact pair, and B15 sweeps the list both ways.
`cardcheck` 63 → 70 cases (A50–A55, B15), `test-cardcheck-mutants` 59 → 70
(M60–M70). On `558bd4e` B15 sweeps 94 cards and still finds 31 sends and the
same 5: seating 43's two frozen cards send nothing to the node. What it cannot
see: a command outside a single-quoted `--send`, and what a permitted word does
when it is loaded.

**`tools/imgprocs.py` 1.3 and `tools/ethcensus.py`**: rtl819x-view names its
two tables `vlan` and `netif`, which are also two of the vendor's
`/proc/rtl865x/` names. On an 8c image `imgprocs` read 15 of 42 PRESENT
against `r6b7q`'s 13 and called the two the vendor's — the evidence `NET-42`'s
*no `/proc/rtl865x/vlan`* would be misread against — and `ethcensus population`
on the 8c tree `r6b8cq` REFUSED, deriving 9 shared names where
`imgprocs.SHARED` lists 7. 1.3's `OWN_LITERALS` maps each of the two to the one
rlxfw object that carries it, `rtl819x-view.o`, prints them as rlxfw's and
counts them apart (I12; the self-test is 17 lines), and `ethcensus` drops a
shared name only when every carrier outside its scope is that object. Measured
at this landing, with the landed tools: `population` on `r6b8cr`'s tree exits 0,
prints *rlxfw's own literals: netif vlan* and agrees with `SHARED`, and its 899
names are the committed fixture's; on `r6b6q2` it reproduces
`tools/ethcensus-population.txt` byte for byte; a scratch copy with `vlan`'s
carrier renamed `rtl819x-switch.o` REFUSES on `r6b8cr`, and the unmutated
scratch copy through the same path does not. `NET-42`'s *no
`/proc/rtl865x/vlan`* still stands on the device's own `ls`, which neither
tool replaces.

**§ 11.7's carried item is done**: `tools/imgprocs.py`'s comment above `SHARED`
and its docstring now say 634 objects with content (594 leaves and 40 archive
members, not 667), and that `arp` and `ip` have a third carrier,
`usr/initramfs_data.o`'s `.init.ramfs`, which that `.rodata`/`.data` search did
not read. It had waited for seating 43 because a card might pin the tool by
digest; none of seating 43's three cards does (讀, their text). `SPEC.md`
`FW-148`.

## 12.8 The images, and what the build read

`r6b8cr` and `r6b8cr2`, the quiet variant, `rlxfw-kbuild.sh --variant quiet
--initramfs _irfs-r6b8c spec --marks --jobs 4` then `rtkimage.py build`, each
from a fresh stage, one at a time; `_irfs-r6b8c` is `mkinitramfs build --init
config/rlxfw-init-quiet.sh`. Every figure below was read at the desk on
2026-09-27 out of the build artefacts by an instrument, and none on the device.

| what | value |
|---|---|
| recipe | `527e683b` (both manifests) |
| `vmlinux` | `d57b02e2…`, 4,564,761 bytes; `cmp` rc 0 between the two |
| `nfjrom` | `a6c9c818…`, 1,171,456 bytes; `cmp` rc 0 |
| flat image (`vmlinux_img`) | `921f681d…`, 4,035,072 bytes, 76.963 % of the 5,242,880-byte ceiling (`FW-23`), margin 1,207,808 |
| manifests | differ in `cell` only |
| the image's `/init` | `config/rlxfw-init-quiet.sh`, 1,859 bytes, `fd78c441…` (both initramfs manifests; `r6b7q`'s is `config/rlxfw-init.sh`, `ef2c8797…`) |
| `(NEW)` in `oldconfig` | 0 and 0 |
| `kconfig-delta check` | green, 30 derived and 74 set — `r6b7q`'s |
| `rlxfw-marks verify` | 12 marks, 10 witnesses, 1 ABSENT; `MK11`'s `str:rtl819x-view` 3 times in each image (`mine:3`), 0 in the two vendor artefacts |
| `storeseq r6b7q → r6b8cr` | GREEN on the seven NIC functions: the `rtl819x-nic.c:122` comment moved no store |
| `hazlint` | 0 violations in 115,786 loads (`r6b7q`: 0 in 115,650) |
| build warnings | 162 in each log, the same lines as `r6b7q`'s; none from `rtl819x-view.c` |
| `imgprocs` | 15 of 42 PRESENT, 7 shared and 2 rlxfw's; `--witness rtl819x-view` found once, and refused on `r6b7q` (rc 2) |
| `ethcensus check` | RED on all three, the vendor-present positive control: object 22 of 631 leaves, symbol 898 of 899, string 6 of 6; the tree's `rtkload/vmlinux_img` (the drop's kernel, `48b1a171…`) refused |

**The size grew by alignment, not by the driver.** `r6b7q`'s flat image is
4,002,304 bytes; `r6b8cr`'s is 32,768 more. The driver's own loadable bytes
are 4,764 (`size`: text 4,768, which counts its 24-byte `.reginfo`, and data
20). `.text` grew by 3,924 bytes, its five functions, which took `__ex_table`'s
end past `0x8027C000`, so `.iram`, which starts on a 16 KB boundary, moved
from `0x8027C000` to `0x80280000`. The stretch from `.iram` to the end of
`__param`, which ends on a 4 KB boundary, then grew by one 4 KB step and ended
past `0x802B0000`, so the 32 KB-aligned `.data` moved from `0x802B0000` to
`0x802B8000`, and `__init_end` with it, from `0x803D2000` to `0x803DA000`. The
quiet `/init` is 294 bytes shorter than the standard one and `.init.ramfs` is
`0xE4200` bytes in both images. The proposal's guess, at most 76.6 %, priced
the driver's bytes and not the linker's steps; `FW-147` recorded the same
lesson for 1.3.

**`config/` is what the images were built from.** `git diff 92eb9b6` against
this landing's tree is empty under `config/`, and the landing's own
`RECIPE_ID` derivation (`find config -type f`, sorted, digested, as
`rlxfw-kbuild.sh` computes it) prints `527e683b`, so `r6b8cr` is this
commit's image.

**Four marks witnesses cannot fail, not one.** `FW-143` found that `MK10`'s
`str:rtl819x-nic` is met by the standard `/init`'s own text in `.init.ramfs`.
The same whole-file search finds three more in `/bin/mfgtest`, declared in the
initramfs since `P1-1` and packed in `r6b7q` and `r6b8cr` alike (the same
sha256, `d954de73…`): `config/mfgtest.sh` holds `rtl819x-switch` 4 times,
`rtl819x-wdt` twice and `n150rt:green:led2` once, so `MK9`'s, `MK6`'s and
`MK7`'s witnesses are met without their drivers. Counted over the two ELF files
(the whole-file search `FW-143` marks 量): `rtl819x-switch` 9 times in `r6b7q`
and 7 in `r6b8cr` (the standard `/init`'s
two are gone), `rtl819x-nic` 6 and 4, `rtl819x-wdt` 6 and 6,
`n150rt:green:led2` 2 and 2. On the quiet image `MK10` can fail again — its 4
are the driver's own — and only there. A witness is a gate, so changing one
is the owner's (`FW-143`).

## 12.9 The review, and the landing

The implementation went through an adversarial review in three lenses
(hardware, hygiene, a judge) before these images were built; what it changed
is in the code and above: `viewcheck`'s V17, `viewdecode`'s cut shape,
`cardcheck`'s HW-1, `imgprocs` 1.3 and `ethcensus`'s own-literal rule, and the
driver comment's statement of which 量 the table applies (§ 12.3), a comment
change that moved `RECIPE_ID` and so rebuilt both images. It lands with
`R6b-6`'s `rtl819x-nic.c:122` comment (`notes/nic-driver.md` § 24.4), rebased
without a conflict onto seating 43's captures; the vendor files this reading
opened are `docs/blind-write-ledger.md` § 9.8.

## 12.10 What 8c-code does not establish

* Anything on the silicon: not one line of the file has run. How long `SWTACR`
  stays busy, whether a slot tears, what `tbl` reads on the die against what
  the vendor's reader reads, and the view's page on a real boot are 8c-cells'.
* That the 298 words (1.1: 311, § 17.5) are free of read side effects: none is known (推), and
  which of them were read on this die before is the table's sources column.
  Five were never read here — `BSCR` (`0x4044`), `PCRP8` (`0x4124`), `LEDCREG`,
  `LEDCR1` and `LEDBCR` — and the `PIN_MUX` pair has no reading at all.
* That a `mib` read clears nothing. The vendor's dump of the same words was
  cumulative across 76 reads (§ 12.3), so 推 it does not, and 8c-cells'
  brackets read it. Nor that a byte-counter pair cannot tear across a carry
  between its two loads (推 it can, and nothing here would tell), nor what
  `<< 22` means (B alone; `asicCounter` agreeing with the decoder shows the
  decoder copies the vendor, not that the formula is right).
* That the quiet `/init`'s boot capture falls in `bootbytes`' 710 class (推):
  nothing was booted.
* Anything about a one-source word, or about `0xBB804500` beyond its three
  readings: it is refused in 1.0 (§ 12.3), and its place in 8d's table is 8d's (in 1.1, § 17.5).
* A second copy of the admission table: the census is a second source by
  counts, and `admit 298` on the page is a count, not a list.

# 13. 2026-09-27 (`R6b-8` 8b) — `CONFIG_RTL_819X_SWCORE=n` as a variant: the ten, the seam, and what the link measured

**Every number in this section is 讀**: read at the desk on 2026-09-27 out of build
artefacts by an instrument, true of those builds; none was measured on the device.
The session material, scripts included, is `$FWRE_WORK/rebuild/s115/r6b8b/` (not in
this repository). `SPEC.md` `NET-150`–`NET-153` and `FW-153`.

## 13.1 Why a variant, and the vocabulary it needed

`R6b-8`'s 8b is `SWCORE=n` as its own cell: the owner's rulings of 2026-09-26 keep
`SWCORE=y` in mainline until 8g, after D1–D4, with the `y` config building from every
later tree. A `--config` build cannot carry it — its `kconfig-delta check` reads the
rows common to every variant, and a `SWCORE=n` `.config` is red there — so
`config/rlxfw-kernel.delta` gained a third exclusive variant, `quiet-noswcore`: the
quiet kernel with the vendor Ethernet tree out of the link. `tools/kconfig-delta.py`'s
`VARIANTS` and `tools/rlxfw-kbuild.sh`'s accepted names are the two places that spell
the vocabulary; the script's edits keep its line count (939), because notes and
`config/` cite it by line. `kconfig-delta` self-test 24 of 24, `test-config-gates` 60
of 60 and `test-kbuild-cflags` 96 of 96 on that tree, the counts `tools/ci-expected.tsv`
holds; a dry run takes the new name and refuses a typo of it.

## 13.2 The first probe did not reach the link: three macros, and `host-compat` 0008

Probe `r6b8bp0` carried one delta row, `set@quiet-noswcore CONFIG_RTL_819X_SWCORE y n`,
and nothing else of 8b. The prediction written before it (the design's, segment 113)
was that every object compiles and the link fails on ten names. **Refuted at the first
clause**: `net/rtl/features/rtl_features.c` failed to compile — `GATEWAY_MODE`
undeclared at `:1103`, `WISP_MODE` at `:1117`, `BRIDGE_MODE` at `:1125`, all in
`rtl865x_getWanDev()`, compiled under `CONFIG_NET_SCHED && CONFIG_RTL_IPTABLES_FAST_PATH`
(`:1097`), both of which stay `y`. 讀 `include/net/rtl/rtl_nic.h:213-246`: the three
`#define`s sit inside `#ifdef CONFIG_RTL_LAYERED_DRIVER`, one of the symbols the SWCORE
block declares. The design's census preprocessed 232 objects through a host `cpp` and
counted references to vendor **symbols**; a missing **macro** is a compile error it
could not see, and its conclusion that no vendor line need change does not survive
the build.

`config/host-compat/0008-rtl-nic-h-op-modes-outside-layered-driver.patch` rewrites two
lines of that header and adds none: the blank line after `RTL865X_CONFIG_END` becomes
the `#endif`, and the commented-out `MULTIPLE_VLAN_BRIDGE_MODE` line becomes the
`#ifdef CONFIG_RTL_LAYERED_DRIVER`, the comment kept after it. At `SWCORE=y` both halves
are included, so the preprocessor emits the tokens the unpatched header gives and no
`__LINE__` moves. The patch's prediction — the `y` build's objects byte-identical to
`r6b8cr`'s except those whose inputs 8b changes — held (§ 13.6). It applies once, and a
second `patch --forward` refuses it.

## 13.3 The linker's list: ten names in four places, from two sources

Probe `r6b8bp1` (the row and 0008, still no seam): 0 compile errors, and the link failed
on exactly ten undefined names — `bsp_swcore_init`, `rtl865x_setNetifType`,
`rtl_get_hw_fdb_age`, `igmp_delete_init_netlink`, `cached_dev`, `cached_dev2`,
`cached_eth_addr`, `cached_eth_addr2`, `update_hw_l2table`, `rtl865x_curOpMode` — in
26 reference lines (`r3-4/out/r6b8bp1.build.log`). The second source shares no code with
the linker: over the 22 inputs of `r6b8cr`'s `cmd_vmlinux`, read in the probe's tree
with the host's `mips-linux-gnu-nm`, (every non-weak `U`) − (every defined name) − (every
word of `arch/rlx/bsp/vmlinux.lds`) leaves the same ten, from 1,649 undefined and 12,715
defined names. By leaf, walking each `built-in.o`'s `ld -r` `.cmd`: the BSP
(`arch/rlx/bsp/setup.o`: 1), the vendor fast path (`net/rtl/fastpath/96E/fast_l2tp_core.o`,
`fastpath_core.o`, `filter.o`: 3), the WLAN driver (`drivers/net/wireless/rtl8192cd/
8192cd_rx.o` and `8192cd_osdep.o`: 5 names) and the feature glue
(`net/rtl/features/rtl_features.o`: 1) — the four places `config/host-compat/0007`'s
header records from `R6-4`'s link. `net/core/dev.c` and `net/bridge/br_fdb.c` name two
of the ten in their source and reference neither: `CONFIG_RTL_BATTLENET_ALG` is unset
and the bridge's call is under `#if 0`. `8192cd_sme.c` names the four `cached_*` in its
source and no object references them.

## 13.4 The delta: forty derived rows and one decision, generated from the probe's report

`r6b8bp0`'s oldconfig log held 0 `(NEW)`, and `kconfig-delta check --variant
quiet-noswcore` refused it with 40 undeclared, 0 mismatched, 0 not applied: every one a
symbol `drivers/net/rtl819x/Kconfig` declares inside `if RTL_819X_SWCORE` (`:16-:432`),
every one going to absent (26 from `y` or a value, 14 from `is not set` — the design's
host count, which was not the source). The block appended at the end of
`config/rlxfw-kernel.delta` is one `set@quiet-noswcore` row and forty
`derive@quiet-noswcore … dep-unmet` rows generated from that report, each with the
`Kconfig` line it was read at. The variant parses to 145 rules (75 set, 70 derived),
`quiet` and `loud` to 104 and 106 as before. On the images: `r6b8bn` green (70 derived,
75 set), `r6b8by` green (30, 74); the controls refuse — `r6b8bn`'s `.config` checked as
`quiet` reads 41 undeclared, `r6b8by`'s as `quiet-noswcore` 41 not applied. `emueq check`
green: `CONFIG_RTL_819X_SWCORE` is in `config/emu-path-symbols.tsv` with `exc_path n`,
and none of the forty is.

## 13.5 The seam, and the one write it makes

`config/rlxfw-src/linux-2.6.30/drivers/net/rlxfw-seam.c`, linked by
`config/rlxfw-marks.tsv` `MK12` (`obj-y += rlxfw-seam.o` after MK11's line) — the path
`tools/ethcensus.py` already named as its placeholder (§ 11.6). Its body is under
`#ifndef CONFIG_RTL_819X_SWCORE`; outside it, `const char rlxfw_seam_id[] = "rlxfw-seam
1.0"` is `MK12`'s `str:rlxfw-seam` witness, in both images. The ten, each with the value
the vendor's own code gives when it has nothing to report: `rtl865x_setNetifType` −3
(`RTL_EENTRYNOTFOUND`; both callers overwrite the return); `rtl_get_hw_fdb_age` 0 (the
caller moves a bridge timestamp only at 150, 300 or 450); `igmp_delete_init_netlink`
`-EIO`, no socket (the caller returns 0 whatever it gets); the four `cached_*` as zero
storage, the vendor's empty cache; `update_hw_l2table` a no-op; `rtl865x_curOpMode` 0,
`GATEWAY_MODE`.

`bsp_swcore_init()` makes **the vendor probe's disarm of the loader's DMA engine**, in
the vendor's order: `CPUIIMR = 0`, then `CPUICR &= ~(TXCMD | RXCMD)` (讀 the staged
`rtl_nic.c:6224-6225`; the header's `:491-492`, `:512`, `:527-528`, and 量 `NET-48`'s
loader `C4000000`), between `RLXFW-SM0=` (`CPUICR` before) and `RLXFW-SM1=` (read back
after). With `SWCORE=n` nothing else disarms that engine (`docs/KNOWN-ISSUES.md`,
`R6-4`'s `D4` row). It returns 0 without reading `REVR`, where the vendor's returns
non-zero for an unrecognised chip: `RLXFW-B07=00000000` is the only value of `B07` in a
committed capture (169 lines at `95dabac`). `bsp_setup()` is `arch_mem_init()`'s first
call (`arch/rlx/kernel/setup.c:464`, before `bootmem_init()` at `:481` and
`paging_init()` at `:483`), so the disarm runs before any allocator exists and earlier
than the vendor's `device_initcall`. At `SWCORE=y` neither mark is linked (`RLXFW-SM0=`
0 times in `r6b8by`'s ELF, once in `r6b8bn`'s).

⚠️ **`N1`'s prediction does not carry across, and a gate that copied it would misread a
disarmed engine as a running one** (推). `rtl819x-nic.c` says `N1` must read `00000000`;
63 committed `N1` lines do, on images where the vendor's probe also full-resets the
switch core and `boot_rpdcr0`/`boot_rmdcr0`/`boot_tpdcr0` read 0 (card C's `A-FIXR`).
The seam clears bits 31 and 30 only, so on `r6b8bn` `SM1` and `N1` are predicted
`04000000` — the `MBUF_2048BYTES` field left as the loader set it — and the ring
registers the loader's `A040Fxxx`. Arm II's run gates on bits 31:30 (`RUN-armII.md`,
`N1-MK`); the driver's comment is a `SWCORE=y` statement, and 8g's to revise.

## 13.6 The images, and what the build read

`r6b8bn`/`r6b8bn2` (`--variant quiet-noswcore`) and `r6b8by`/`r6b8by2` (`--variant
quiet`) at `e4c0834`, each `rlxfw-kbuild.sh … --initramfs _irfs-r6b8b spec --marks --jobs 4` from a
fresh stage, one at a time, then `rtkimage.py build`; `_irfs-r6b8b` is `mkinitramfs
build --init config/rlxfw-init-quiet.sh`, spec and manifest equal to `_irfs-r6b8c`'s but
for the repository path, every file re-hashed.

| what | `r6b8bn` (SWCORE=n) | `r6b8by` (SWCORE=y) |
|---|---|---|
| recipe | `024eab44` | `024eab44` |
| `vmlinux` | `9b703bab…`, 4,255,029 B | `f68f6c36…`, 4,564,844 B |
| flat image | `19c632f3…`, 3,764,736 B, 71.807 % of 5,242,880, margin 1,478,144 | `cd2b18bd…`, 4,035,072 B, 76.963 % (as `r6b8cr`) |
| `nfjrom` | `c0e1704a…`, 1,113,088 B | `a7856192…`, 1,171,456 B |
| rebuild | `cmp` rc 0: vmlinux, flat, `nfjrom`; manifests differ in `cell` only | the same |
| `(NEW)` | 0 | 0 |
| `rlxfw-marks verify` | green: 12 marks, 11 witnesses, 1 ABSENT; `MK12` `mine:2` | the same |
| `hazlint` | 0 violations in 108,443 loads | 0 in 115,786 (`r6b8cr`'s count) |
| build warnings | 153, none from `rlxfw-seam.c` | 162, `r6b8cr`'s count |

8b's first builds, at `5bb672d` (recipe `047b31d9`), carried one warning
from the seam, a slash-star inside a comment; `e4c0834` reworded it and the four images
were rebuilt, and nothing of the first build is kept but its logs. The flat images are
`objcopy -O binary` of their `vmlinux` (`cmp` rc 0). **0008 is inert
at `SWCORE=y`**: of `r6b8by`'s 763 objects against `r6b8cr`'s 762, the one new is
`drivers/net/rlxfw-seam.o` and the eight that differ are `init/main.o` and
`drivers/mtd/devices/rtl819x-spi.o` — the two consumers of `RLXFW_SRC_ID` — and the six
links above them (`drivers/built-in.o`, `drivers/mtd/built-in.o`,
`drivers/mtd/devices/built-in.o`, `drivers/net/built-in.o`, `init/built-in.o`,
`vmlinux.o`); `net/rtl/features/rtl_features.o` is identical. The same loop, composites included,
reads 144 objects different between `r6b8by` and `r6b8bn`. `storeseq r6b8cr → r6b8by` is GREEN.

## 13.7 `struct sk_buff` changes, and what `rtl819x-nic` depends on

讀 `include/linux/skbuff.h:331-473`: `srcPort` and `srcVlanId` are under
`CONFIG_RTL_HARDWARE_MULTICAST` (`:415`), `tag` under `CONFIG_RTK_VLAN_SUPPORT` (`:429`)
and `src_info` under `CONFIG_RTK_VLAN_NEW_FEATURE` (`:431`) — three of the symbols
`SWCORE=n` takes away (🔄 **2026-10-04: this said *the forty symbols*; see § 19.4**). So **the layout changes**, measured by compiling a probe of
`offsetof()` and `sizeof()` to assembly with `rtl819x-nic.o`'s own command line from
each tree, through `tools/vendor-tripwire.sh` (CLEAN both times): `sizeof(struct
sk_buff)` 200 → 192; `srcPhyPort` and `dstPhyPort` 132/133 → 128/129 (−4); every field
from `inDev` on — `mark`, `vlan_tci`, the three header offsets, `tail`, `end`, `head`,
`data`, `truesize`, `users` — −12; everything before `srcPort` unmoved;
`sizeof(struct vlan_tag)` 4; `sizeof(struct net_device)` 688 in both.

**What `rtl819x-nic` compiles to follows exactly that.** `rtl819x-nic.o`, `r6b8by`
against `r6b8bn`, host `objdump -d`: 7,955 instructions each, 7,949 identical, and the
6 that differ differ only in a displacement that moved by the measured shift — `tail`
176 → 164 (one `lw`, one `sw`), `data` 188 → 176 (three `lw`, one `sw`) — 0 unexplained;
its four non-executable allocated sections are byte-identical. That is `storeseq
r6b8by → r6b8bn`'s one RED, in `nic_poll`: it aligns stores by displacement, and the
shifted `tail` and `data` stores cannot align. `rtl819x-switch.o` and `rtl819x-view.o`
are byte-identical between the two images, as are rlxfw's other seven objects; of
rlxfw's own, only the seam and `rtl819x-nic.o` differ. Of the 640 objects the two trees
share outside the `built-in.o` composites, 122 differ — 41 under `net/ipv4`, 17 under
`net/netfilter`, 10 under `net/core`: an
`n` image is not a single-variable change against a `y` image's rtt or throughput, and a
number from one is not carried to the other.

## 13.8 What owns `0x8040FC70`

The loader's RX engine writes, when a frame arrives, into rings from `0xA040FC70`,
descriptors, mbufs and four 2,048-byte buffers ending at `0xA0411F9A` (量 at the loader
prompt, `notes/nic-driver.md` §§ 2–3): KSEG0 `[0x8040FC70, 0x80411F9A)`.

* `r6b8bn`: `.bss` (`0x80398000`–`0x804E6650`). One symbol covers the whole footprint:
  `obj_buf`, a static array of the WLAN driver (`drivers/net/wireless/rtl8192cd/
  8192cd_util.o`; `8192cd_util.c:176`/`:203`, the two arms of `#ifdef CONCURRENT_MODE`),
  432,432 bytes at `0x803E9638`, which that driver clears and fills at its own init.
* `r6b8by` and `r6b8cr`: `.bss` (`0x803DA000`–`0x80673950`); `icv_pool` (4,100 B at
  `0x8040F544`, which holds `0x8040FC70`), `mic_pool` (4,100 B) and `desc_buf`
  (106,368 B), all `8192cd_osdep.o`.

Both from `System.map` and again from the ELF's sized symbols. 推: from kernel entry to
the seam's disarm the footprint is `.bss` that `head.S` has zeroed and no code has used,
and a zeroed ring word is CPU-owned (bit 0 clear, `notes/nic-driver.md` § 3.2), so the
engine finds no descriptor to fill; on the `y` images the same memory is the WLAN
driver's until the vendor's `device_initcall` disarms the engine, so the `n` image's
window is the shorter one. Whether the engine caches a descriptor across `head.S`'s
clear is not known here.

## 13.9 The census on the `n` image

`tools/ethcensus.py check --build r6b8bn … --seam drivers/net/rlxfw-seam.o`: **GREEN** —
object 0 of 610 leaves in scope (84 `ld -r` links); symbol 10 of the 899 population names
in `vmlinux` (10 by `System.map`), the ten seam names each defined by
`drivers/net/rlxfw-seam.o` alone, none `[MIPS16]`, the parsers agreeing on the 610 leaves
and on `vmlinux`'s 12,973 symbols; string 0 of the 6 vendor-unique `/proc` names, with
`rtl819x-switch` 1 and the synthetic name 0. On `r6b8by`, RED on all three (22 of 632
leaves, 898 of 899, the positive control); the tree's `rtkload/vmlinux_img` (the drop's
kernel) is refused. **`tools/imgprocs.py` REFUSES the `n` image** (rc 2: its controls
`port_status` and `asicCounter` read 0), which is its design on an image without the
vendor tree — the inverted mode 8e names — and on `r6b8by` reads 15 of 42, as on
`r6b8cr`. `RUN-armII.md` in the session directory is arm II's quick run on `r6b8bn`;
`cardcheck commands` passes it (32 commands, 3 loader, 29 shell, 13 HOST cells, 0
refused) and refuses a copy with a planted `EW` and `FLR`.

## 13.10 What 8b does not establish

* Anything on the silicon: `r6b8bn` has not booted. That the seam's marks print, that
  `N1` reads `04000000`, that `rlx0` comes up without the vendor's probe, and what the
  loader's switch state carries, are arm II's.
* That the kernel's behaviour outside the Ethernet path is unchanged: the symbols the flip
  takes away also recompile the bridge, the IPv4 stack, netfilter and the WLAN driver
  (§ 13.7), and none of that was exercised. 🔄 **2026-10-04: this said *the forty symbols*,
  and the 40 is retracted at § 19.4 — the measured loss is 11 entries and 6 references.
  The clause does not depend on the count.**
* That the ten stand-ins are right for every caller: the census shows who references
  them, not what a WLAN station, an L2TP netif or a bridge would do with the answers; no
  rlxfw image configures any of the three (推).
* A second reading of the variant's forty from anything but `kconfig-delta` and the `Kconfig`
  lines, or `loud` at `SWCORE=n`, which no variant builds (🔄 8g: `loud`'s, never built; § 18).
* Anything about the fast path's NAPT entry with no WAN device: `rtl865x_getWanDev()`
  returns NULL at `SWCORE=n` (no `ppp0`, no `eth1`), and its caller in
  `fastpath_core.S:785` was read no further than its address.

# 14. 2026-09-27 (`R6b-7`, block 51) — 1.3 on the die: `D7` met, `C-18` stays ⊘, and block 50's switch side

## 14.1 What ran

量 2026-09-27 17:51:51–17:57:13, `bench/2026-09-27c/`: card C,
`PREDICTIONS-B53-block51.md` (committed `1b7c1fd` at 17:49:03, two minutes
before the catch opened, with no freeze ceremony — the owner's relaxed
process for `R6b` of 2026-09-27; sha256 `be534627…`, the digest all twelve
transcript headers print; the captures are `fb4226d`). One press of `r6b7q`,
seating 43's third: `rtl819x-switch` 1.3 and `rtl819x-nic` 1.5,
`recipe_id 50E4AF55` at `R1-NW0:51` and `R1-NW1:51`; a cold boot (the catch's
gate in `run-I-1.log` reads `C-8 cold`) after card B's power-off and a host
restart (the host's kernel log starts at its kernel's boot, `R0-DW0:4`).
Twelve invocations, `I-0` to `I-Z`, exited rc 0 and each transcript ends
`ALL ITEMS DONE` (`$FWRE_WORK/rebuild/s114/run43c/`); 267 of 267 gates
passed; 107 cells ran, each once, and every one of the fence's 110 names has
a capture (the 107 and `looprun`'s three). Before power `check-predictions`
read `0 of 110 captures came after the prediction, 110 did not`.

The readings: one reader with parsers of its own, set against `mdpage` 1.1's
verdicts on every value, and the main session's spot checks and rulings
(`$FWRE_WORK/rebuild/s115/read51/`, `READING.md`). Every number below was
re-read from its capture line for this record. Where the reading and a
capture differ, the capture's figure is the one written here: `A-SW`'s first
`psrp3` read came 29.2–29.3 s after the banner (the reading: 28.5 s), the
gap from `X-W1` to `X-OFF1` is 0.45 s on the raw clock (0.46 s by wall
clock), and the reading does not list the 0.43 s before `X-W1`.

Capture names are `bench/2026-09-27c/`'s unless a subsection says otherwise.
`NAME:N` is line N of `NAME.log`, counted on LF with CR stripped (`sed -n`'s
numbering), and `NAME:N–M` a range; "card line N" is line N of card C.

量, each capture's own `.meta.json` and `.timing` (a `.timing` row precedes its
chunk, `FW-35`); wall-clock stamps, intervals on `CLOCK_MONOTONIC_RAW`:

| time | event |
|---|---|
| 17:51:51.26 | `R1-CATCH` opens |
| 17:52:01.50 | its first byte, `Booting...`, 10.25 s into the catch: the power-on is at or before it |
| 17:52:03.79 | the loader's first prompt, 2.29 s after the banner |
| 17:52:03.99–17:52:05.20 | `L1-MD2` and `L2-MD3` |
| 17:52:05.45–17:52:26.63 | `looprun`'s round, `S5` to `S9` (`R1Q.stages.tsv`) |
| 17:52:26.89–17:54:33.59 | the Linux cells, `R1-PS` to `R1-NW1` |
| 17:54:34.01–17:56:26.95 | `X-W1`, `L1`'s tail watch, opened 0.23 s after `I-Z`'s last stamp |
| 17:56:27.41–17:57:07.07 | `X-OFF1`; the board's last byte at 17:56:43.95, 16.54 s into the window |
| 17:57:07.36–17:57:13.72 | `X-W2`: 0 bytes, and rc 1 is an empty capture's normal exit |

The board's last byte is the power-off (推: nothing else ends the replies to
the window's ESC stream). The owner confirmed the power-off in words, which
no capture holds. After `R1-NW1` the port went without a capture three times:
0.43 s to `X-W1`, 0.45 s from `X-W1` to `X-OFF1` and 0.29 s from `X-OFF1` to
`X-W2` (raw clock). The captures' wall-clock stamps wander against the raw
clock by 0.16 s over the press (`t0_real − t0_raw` across `R1-CATCH`,
`R1-NW1`, `X-W1`, `X-OFF1` and `X-W2`), so the difference of two wall-clock
stamps above is good to about ±0.2 s.

## 14.2 `D7`: met (`SPEC.md` `NET-145`)

The predicate is card P4 (card lines 431–442): for N = 0–4, `phyN`'s id is
`L1[N] << 16 | L2[N]`. 量, every cell of this table reads register 2
`0x001C` and register 3 `0xC880`, the ID `001CC880`:

| address | Linux's MDIO API: `phyN id` (`C-PR`), r2 and r3 by `mdiobus_read` (`E-SC`) | the loader, this boot (`L1-MD2`, `L2-MD3`) | the vendor's `phyReg` | earlier loader reads, r2 / r3 |
|---|---|---|---|---|
| 0 | `C-PR:15`, `E-SC:20` | `L1-MD2:2`, `L2-MD3:2` | `D-V0:3–4` | `F2`, `E4` / `E6` |
| 1 | `C-PR:16`, `E-SC:21` | `L1-MD2:3`, `L2-MD3:3` | `D-V1:3–4` | `F2`, `E8` / `E8b` |
| 2 | `C-PR:17`, `E-SC:22` | `L1-MD2:4`, `L2-MD3:4` | `D-V2:3–4` | `F2` / none |
| 3 | `C-PR:18`, `E-SC:23` | `L1-MD2:5`, `L2-MD3:5` | `D-V3:3–4` | `F2` / none |
| 4 | `C-PR:19`, `E-SC:24` | `L1-MD2:6`, `L2-MD3:6` | `D-V4:3–4` | `F2` / none |

* 量 `D-D7:2–6` read `equal yes` at each address, `D-D7:7`
  `d7 verdict hold: 5 of 5` and `D-D7:8` `d7 vendor agrees 5 of 5`. The probe
  registered the five (`C-PR:5` `bus 1 reg_rc 0`; `C-PR:15–19`
  `rc 0 xrc 0 drv 0 att 0`), and sysfs holds `rlxsw:00` to `rlxsw:04` and
  nothing else (`C-SYS:2`, `C-SYR:3`). The loader's `MDIOR 2` and `MDIOR 3`
  read `0x0000` at 5–31 (`L1-MD2:7–33`, `L2-MD3:7–33`), and each reply is
  1,042 bytes up to its first prompt, `F2`'s size (量, both).
* **`NET-06`'s open half is closed.** Register 3 at addresses 2, 3 and 4 had
  never been read; it reads `0xC880` at the loader (`L2-MD3:4–6`), through
  Linux's MDIO API (`C-PR:17–19`) and through the vendor's `phyReg`
  (`D-V2:4`, `D-V3:4`, `D-V4:4`). Both halves of `0x001CC880` are now 量 at
  all five addresses.
* The vendor's reads moved none of rlxfw's counters (量): every page from
  `D-V0` to `D-MD` reads `mdio_rd 272` and `mdio_wr 16`, `G-SC`'s
  (`J-CH:22–27`, each `d 0`).

Not established: a permutation among 0–4 — the five IDs are equal, so `D7`
cannot see two of them swapped, and § 14.4's rows see only a swap that
involves port 3 (which of 0, 1, 2 and 4 is port 1 stays `NET-39`'s); that the
three sources are independent below software — all three issue their reads
through the one `MDCIOCR`/`MDCIOSR` pair (讀: the loader's `phy_read`, the
vendor's accessor, `rtl819x_mdio_xfer`), so a controller fault common to all
three is not excluded; any other boot.

## 14.3 `C-18` at register level: the reopening condition is not met, and `C-18` stays ⊘ (`NET-146`)

The rule is card P7's (card lines 512–515; decision D, § 10.7): `C-18`
reopens if PHY 1's page-1 register 19 bits 15:1 differ from the value PHYs 0,
2, 3 and 4 agree on (void if those four disagree), or if a port-1 link fault
is ever observed.

* 量 Page-1 register 19 reads `0x7380` on all five PHYs: `G-P8:22–26`
  (`v 29568` on a0, a1, a2, a4 and a3, in `pread` order; in hex at
  `G-C18:4–8`). PHYs 0, 2, 3 and 4 agree, and PHY 1 equals their value
  (`G-C18:17`: `c18 stays void-by-ruling`, PHY 1's bits 15:1 `7380` equal
  the value the other four agree on). Bit 0 reads 0 on all five
  (`G-C18:16`).
* 量 The select is shown two ways: `ps 1` on each of the seven paged reads of
  (g) (`G-C18:13`), and, on PHY 0, page 1's register 16 reads `0xD100`
  against page 0's `0x031F` (`G-P8:21`, `G-P8:20`).
* 量 The vendor's `extRead N 1 19` reads `0x7380` on all five (`V-X0:2` …
  `V-X4:2`), equal to rlxfw's `v` at each (`V-CMP:2–6`; `V-CMP:7`
  `vend verdict 5 of 5 equal`). That path writes register 31 with no gate —
  1, then 0 unconditionally (讀 `rtl865x_proc_debug.c`, card C's `cardnum`
  row) — so (g′) made ten PHY writes that rlxfw's counters do not see.
* 讀, in the tree that builds (`r3-4/cells/r6b7q`): `Setting_RTL8196E_PHY`
  clears only bit 0 of page-1 register 19 (`rtl865x_asicL2.c:4193`,
  `Set_GPHYWB(999, 1, 19, 0xffff-(0x1<<0), 0x0<<0)`), and `Set_GPHYWB`'s
  `999` walks PHYs 0–4 alike (`:1236`–`:1238`, `NET-07`); the function is in
  `r6b7q`'s `System.map`. The five equal words agree with that.
* The link-fault clause could not fire: port 1 had no link, reading
  `psrp1 000000E0 up 0 lde 0` on all five switch pages (量, line 19 of `A-SW`,
  `E-SW`, `G-SW`, `V-SW` and `Z-SW`).

By the main session's ruling (segment 115) the reopening condition is not
met and `C-18` stays ⊘. Not established: whether port 1 *needs* the patch —
the functional clause is ⊘ by the owner's ruling of 2026-09-26 (two cable
moves and a comparison arm; one link partner cannot establish "not needed");
what register 19 does (the rule compares bit patterns, not function); another
die or another boot.

## 14.4 `NET-08`: registers 0–5 at addresses 5–31 read `0x0000`

量 `E-SC:25–51`: at every address from 5 to 31, registers 0–5 read `0000`
with `hi 0000` — 27 of 27 rows. Every read completed: `mdio_to 0 busy 0`
(`E-SC:9`) and no `E` token in any row. The loader's `MDIOR 3` reads `0x0000`
at 5–31 on the same boot (`L2-MD3:7–33`), beside `MDIOR 2`'s `0x0000`
(`L1-MD2:7–33`, `F2` repeated). Card P5 (card lines 461–467) registered
registers 1 and 3–5 there as 推 `0000`; they came out as inferred
(`E-RW:37`). `NET-08`'s § 17 question — registers 1, 3, 4 and 5 at 5–31 —
has its answer, one read each.

Not established: that `0x0000` means "no device" rather than the word the
controller returns for a read no device answers; this boot cannot tell the
two apart. phylib's own test for an empty address,
`(id & 0x1fffffff) == 0x1fffffff` (§ 10.2), would call all 27 present, which
is why 1.3 masks them.

## 14.5 `NET-136`'s open contract on the die (`NET-147`; `mdiocheck`'s K7, `FW-151`)

* **Register 31 reads back** (量). Every paged read found register 31 at 0
  before its select (`p0 0`), read 1 after selecting page 1 (`ps 1`) and 0
  after the restore (`p1 0`): the eight at `G-P9:20–27`, each PHY's first
  select among them. That is the `ps 1` branch of `NET-136` 殘留's rule (card
  lines 497–503).
* **Every paged read restored page 0 and read it back** (量): `rs 0`, `rt 0`
  and `p1 0` on 8 of 8 (`G-P9:20–27`), and `retry 0` and `dirty 0` on every
  page from `A-MD` to `J-PR`. The page-0 control reads `rs 1` (`G-P1:20`):
  `rtl819x-switch.c:1002 (RTL819X_MDIO_NOXFER)`, "none issued" — a page-0
  `pread` makes no restore (讀; § 14.8).
* **`MDCIOSR` 30:16** (量): `hi_or 00000000` on every page from `A-MD` to
  `J-PR`, and `hi 0000` on every row of every page — the 5 addresses holding
  a PHY and the 27 that hold none — and on the timeout's row (`F-S0:25`).
  The live register and slot 0 read bits 30:16 as 0 on all five switch pages
  (`A-SW:31`, `E-SW:31`, `G-SW:31`, `V-SW:31`, `Z-SW:31`). What the bits mean
  stays 未定: they moved with neither whether an address answers nor a
  timeout.
* **`STATUS`'s length** (量). Completed transactions needed 22 to 40 polls
  (`spin`'s minimum and maximum over the run, `J-PR:11` `spin 317 22 40`). At
  `bound 0` the first read of `scan 5 5` timed out and `STATUS` was still set
  at the next five pre-checks: `F-S0:25` `a05 E145 E016 E016 E016 E016 E016`,
  and `F-AC:3–5` accounts it (one `E145`, one `mdio_to`; five `E016`, five
  `busy` with no store; `mdio_rd` +1 = 6 − 5). `mdiocheck`'s K7 scripts
  `STATUS` held for three reads (`busy_post 3`) and gives
  `E145 E016 E016 E145 E016 E016`: two busy pre-checks after the timeout,
  where the die gave five (`FW-151`). Back at the full bound, 10,000, the die
  and K7 agree: `F-S1` reads `0000` ×6 and `mdio_to` does not move
  (`F-AC:10–11`).
  At `bound 0` each check is one poll with no `udelay(1)` after it (讀
  § 10.4); 推: the row's six reads all fall inside the first read's
  `STATUS`, which a completed read holds for 22–40 polls with a `udelay(1)`
  between each. The time is not measured: `spin` counts polls, and the MDC
  rate is unknown.
* **P9's absolutes.** `J-CH:40`: `mdio_rd` 302 and `mdio_wr` 16, the
  registered formula (card line 547: 307 − Δ`busy` − 3k − b, with Δ`busy` 5,
  k 0, b 0). The card's "303 under K7's model" on the same line was that
  formula at K7's Δ`busy` of 4.
* **The switch's own poller against a selected page: undetermined.** 量
  `PSRP` bit 8 was clear on both sides of every `pread` (each `pr` line's
  `psrp` pair, `G-P9:20–27`), `lde` rose by 0 at every port after (g) and
  after (g′) (`G-SWD:3–10`, `V-SWD:3–10`), and the livenesses after each read
  4 of 4 (`G-L:9`, `V-L:9`). But `G-PCTL:3` reads `pctl blind yes`: page 1's
  register 2 reads `0x001C` (`G-P9:27`), page 0's value, so a PHY left on page
  1 reads the same registers 0–5, and the scan and `lde` detectors could not
  have seen one (card § 7).

Not established: `STATUS`'s length in time; what `MDCIOSR` 30:16 means;
whether the switch's poller ever meets a selected page; any other boot.

## 14.6 Values read for the first time (`NET-148`)

量, each once, on one boot. "First" rests on a search of the committed
captures under `bench/` (5,282 `.log` files at `95dabac`) for every form in
which this repository has read a PHY register — the loader's `PHYR` and
`MDIOR`, the vendor's `phyReg` `read` and `extRead`, rlxfw's `pread` — which
finds none of these registers read before block 51 (its only hits are the
loader's help text naming `PHYW`).

| PHY | page | register | value | line |
|---|---|---|---|---|
| 0 | 0 | 16 | `0x031F` | `G-P1:20` (`v 799`) |
| 0 | 1 | 16 | `0xD100` | `G-P8:21` (`v 53504`) |
| 0–4 | 1 | 19 | `0x7380` | `G-P8:22–26` (`v 29568`) |
| 4 | 1 | 20 | `0x0000` | `G-P8:27` |
| 0 | 1 | 2 | `0x001C` | `G-P9:27` (`v 28`) |

* Page 1's register 16 reads bits 15:13 = `110` (`G-C18:15`), where the
  source states the default as `100` and writes `110` (讀
  `rtl865x_asicL2.c:4176`–`:4177`, "Iq Current 110:175uA (default 100:
  125uA)"). 推: the vendor's init ran on this boot.
* Page 1's register 19 is `0x7380` with bit 0 clear on all five (§ 14.3); what
  its other bits do is not read. PHY 4's page-1 register 20 is recorded only
  (decision D: the vendor reads it back before adding to it, so its default is
  未定).
* Page 1's register 2 equals page 0's `0x001C`, so `G-PCTL` reads
  `blind yes`, and the scan and `lde` detectors of (g) and (g′) could not have
  seen a PHY left on page 1 (§ 14.5).
* The `EAGAIN` refusal's text is now 量: `F-B0:3`,
  `cat: write error: Resource temporarily unavailable` (card line 475 had it
  推).

## 14.7 Slot 0's `MDCIOCR` records the loader's last MDIO command (`NET-149`)

* 量 `A-SW:30` reads `MDCIOCR` live `84001300` and slot 0 `1F030000`. Slot 0,
  the latch taken at `subsys_initcall` (§ 8.3), holds by `NET-15`'s fields
  (讀) a read (bit 31 clear) of PHY address 31, register 3 — the last command
  of the typed `MDIOR 3` (`L2-MD3:33`, `PhyID=0x1f`). Card P1's 推 (card line
  387) holds (`A-MDC:4`).
* 量 Every earlier committed switch page in `bench/` — 103, one rendering
  each, in 13 directories from `2026-09-19` to `2026-09-27b` — reads slot 0
  `96181441`, the loader's own store on its way to the prompt (`NET-28`;
  `docs/loader-phy-and-switch.md`, *The register readings, both states*). So
  on this boot nothing between the prompt and `subsys_initcall` — the rescue,
  `IPCONFIG`, the TFTP upload and `J` — stored `MDCIOCR`: the TFTP/`J` path
  stores none. 推: the earlier boots' uniform `96181441` means none typed an
  MDIO command at the loader after that store and before its `J`; that is not
  checked boot by boot here.
* 量 The live register reads `84001300`, as on 68 of the 103 earlier pages
  (the other 35 read `03010000` ×24, `00000000` ×10 and `00010000` ×1). 讀
  `NET-15`: a write (bit 31) to PHY 4, register 0 (`BMCR`), data `0x1300` —
  `0x1100`, what register 0 reads at address 4 (量 `E-SC:24`), with bit 9,
  restart auto-negotiation, set. 推: the vendor's side wrote it during the
  boot. 1.3 issued no MDIO command before `A-SW` (`A-MDP:2`: the boot page is
  `mdiocheck`'s K1, `mdio_rd 0` and `mdio_wr 0`), and
  `rtl8651_restartAsicEthernetPHYNway` reads register 0 and writes it back
  with `RESTART_AUTONEGO` (`1 << 9`) set (讀 `rtl865x_asicL2.c:5613`,
  `rtl865xc_asicregs.h:438`; in `r6b7q`'s `System.map`); which of its callers
  issued this one is not read.
* 量 After `E-SC` the live register holds rlxfw's last transaction, `1F050000`
  (`E-SW:30`: a read of address 31, register 5, the last of `scan 0 31`), and
  after `G-SC` `04050000` with `RDATA` `0001` in `MDCIOSR` (`G-SW:30–31`:
  address 4, register 5, whose row reads `0001`). `V-SW` and `Z-SW` read the
  same pair after `V-SC`'s `scan 0 4`. The address encoding of 1.3's command
  word is checked at register level.

Not established: that no earlier boot typed a loader MDIO command before its
`J`; what `96181441`'s write does at MDIO address 22; which vendor call wrote
`84001300`.

## 14.8 The fix, the brackets, liveness (P10), and every prediction

**The fix and the host path** (P10, card lines 561–573), 量: `A-NIC0:133`
read `tx15 txlen rlxfw …` at boot, a reading; `A-FIX` ended on the shell's
prompt (`A-FIX:9`); `A-FIXR` read `txlen vendor`, `armed 1` and `nd_up 1`
(`A-FIXR:133`, `:5`, `:23`). `B-00-R`, `G-99-R` and `V-99-R` passed every
gate, and `B-L`, `G-L` and `V-L` each read 4 transmitted and 4 received with
`follower 1` (`B-L:9`, `:27`; `G-L:9`, `:28`; `V-L:9`, `:28`). Port 3's
output `pause` reads 0 on all three brackets (§ 14.9). Not established: port
3's function beyond 60-B echoes.

**The predictions, one line each** (card § 3; the reading's § 6 table, its
counts re-derived here):

| P (card lines) | what | verdict |
|---|---|---|
| P0 (374–382) | L1 at 0–31; L2 at 0–1; L2 at 2–31, 推; each reply 1,042 B | 3 met, 1 as inferred (`L-RD:34–36`) |
| P1 (386–402) | version 1.3; `psrp3 up 1`; 0–2 and 4 `up 0`; slot-0 `1F030000`; `MDCIOSR` 31 and 15:0 zero; 30:16 recorded; `ifconfig` `0` and `1`; `lo` recorded; "the rest `up 0`" | 6 met, 2 readings, 1 not met as written |
| P2 (403–410) | the locked page is `mdiocheck`'s K1 | met (`A-MDP:2`) |
| P3 (414–427) | the locked probe refused; unlock; the probe; `rlxsw:00`–`04` only; a second probe `EEXIST` | 5 met |
| P4 (431–442) | the IDs; the vendor's; rlxfw's counters unmoved | 3 met |
| P5 (446–470) | `mdio_rd` 202; the 量 rows; the 推 rows; `hi`; (f)'s branch | 3 met, 2 as inferred |
| P6 (474–483) | the `EAGAIN` refusal; the timeout identities; the bound restored; the clean rescan | 4 met |
| P7 (487–519) | the twelve `pread` checks | 8 met, 2 readings, 1 not met as written (`rs`), 1 void as written (`lde`) |
| P8 (523–538) | the gates; `extRead` equal to (g)'s; the rows; `lde` | 4 met |
| P9 (542–557) | lock; the counters; the final probe refused; `spin`'s identity; 302 and 16; the chain | 6 met |
| P10 (561–573) | the fix, livenesses, maps, `n_writes`, `recipe_id` | 6 met, 1 reading (`n_write_refused` Δ 0, `Z-NWR:1–2`) |

P7's twelve: `p0 0`; the select shown; `p1`, `rt` and `dirty` 0; `rs 0`;
register 16's bits `110`; register 19's bit 0 clear; the `C-18` rule;
register 20 (a reading); the accounting, 29 reads and 14 writes (`G-C18:19`);
`pctl` (a reading); rows 0–4 unchanged (`G-C18:20`); `lde` Δ 0. **Totals: 60
predicates — 49 met, 3 as inferred, 5 readings, 2 not met as written, 1 void
as written.** No refutation clause fired.

**The two misses are drafting errors in the card** (committed, left as it is),
each with the main session's ruling (segment 115):

* **P1, card line 396**, predicts `psrp5`–`psrp7` `up 0`. 量 `psrp6` and
  `psrp7` read `0000007A up 1` (`A-SW:24–25`), as on all 31 earlier committed
  pages that print the `psrp` lines (switch 1.2, all block 50's) and on all
  five of this block's; `NET-10` reads those two words as the CPU side's.
  Taken literally, line 399's clause, "a port other than 3 up", then voids
  (g)'s bit-8 detector for this boot. **Ruling:** the clause is read with the
  scope its own reason gives — PHYs 0–4 and the vendor's link DSR — so it does
  not fire, and the detector is not void; P7's `lde` check is counted void as
  written and read under the ruling as Δ 0 (§ 14.5, blind to a PHY left on
  page 1).
* **P7, card line 490**, predicts `rs 0` for all eight `pread`s; the page-0
  control prints `rs 1` (`G-P1:20`), `RTL819X_MDIO_NOXFER`, "none issued"
  (讀, in the built driver, byte-identical to HEAD's, sha256 `80bb3f26…`).
  **Ruling:** the refutation clause (card line 517) covers only reads that
  made their select, so it does not fire.

## 14.9 Block 50's switch side (`bench/2026-09-27b/`, card B52)

Capture names in this subsection are `bench/2026-09-27b/`'s; card B52 is
`PREDICTIONS-B52-block50.md` (frozen `255af14`), and its transcripts are in
`$FWRE_WORK/rebuild/s113/run43b/`. The rest of block 50 is
`notes/nic-driver.md` § 28's.

**One link event after one host `ethtool -r` (`NET-143`).** 量: H2,
`P-H2:1` `ethtool-r-rc 0`, ran between two switch pages (`run-I-P3.log`:
15:33:11, rc 0). Before it, `P-SWH1:21` `psrp3 000000F9 up 1 lde 3 lj 241691`;
0.79 s later (the two pages' starts on the raw clock; `jiffies` 277998 →
278077), `P-SWH2:21` `psrp3 000000E9 up 0 lde 4 lj 278067`. `P-DH2:6` reads
`delta lde 3 d 1` and `P-DH2:14` `delta psrp 3 000000F9->000000E9 up 1->0`.
The next switch page, `F-LS` (15:38:34), reads
`psrp3 000000F9 up 1 lde 4 lj 278067`: the link came back and no second
event was counted. The control, H1 (`ip link set` down, 3 s, up), reads `lde`
Δ 0 at every port (`P-DH1:3–10`). Card B52's P12 (its lines 629–638)
predicted H2 refused (推: `r8153_ecm` implements no `nway_reset`) and `lde 3`
Δ 0; `ethtool -r` returned 0 and `lde 3` rose by one, so P12 is refuted at
H2, and by its own clause that answers `NET-30` 殘留 ②: a command on the host
makes a link event at this desk. One event, at n = 1: that it *makes* one is
推 until it repeats. Not established: why the host adapter's driver honours
`ethtool -r` (seen once); which end dropped the link; how long it was down.

**Port 3's output `pause` counter (`NET-144`).** 量, the vendor's
`asicCounter` dump on every bracket page, read from `<Port: 3>` to
`<Port: 4>` (line 54 of every page but `F-99-R`, where it is line 55), in
capture order:

| pages | arm | port 3 `Output` `pause` |
|---|---|---:|
| `B-00-R`, `D3-00-R` | before the trials | 0 |
| `D3-TR1-R`, `D3-TR2-R`, `D3-TR3-R` | TCP, the board receives | 17,672; 35,530; 53,360 |
| `D3-TS1-R` to `D3-TS3-R` | TCP, the board sends | 53,360 |
| `D3-UR1-R`, `D3-UR2-R`, `D3-UR3-R` | UDP, the board receives | 79,526; 105,108; 131,374 |
| `D3-US1-R` to `D3-US3-R`, `D3-X-00-R` | UDP, the board sends | 131,374 |
| `D3-LUR1-R` | UDP at 1.4, the board receives | 152,616 |
| `X-BR1`, `K1-0061-R0` to `K6-0063-R1`, `M2F-00-R` to `M2F-S12-R`, `P-99-R`, `F-00-R` | the rtt series and the rest | 152,616 |
| `F-99-R` | the 31-minute flood of echo requests | 1,332,638 (Δ 1,180,022) |
| `T-00-R`, `T-R` | TCP, the board sends | 1,332,638 |
| `L-00-R` → `L-99-R` | the 1.4 load | 1,332,638 → 1,346,946 (Δ 14,308) |
| `LE-00-R` | after the re-arm to the fix | 1,346,946 |

Block 49's 26 bracket pages (`bench/2026-09-27/`) and block 51's three read 0
throughout, and port 3's `Rx` `Pause` reads 0 on every page of all three
blocks. So the counter rose only in the arms where the host drove traffic
into the board — TCP and UDP the board receives, the flood, the 1.4 load —
and not while the board sent. The values are 量; the name `pause` is 讀 (the
vendor's `asicCounter` label); "PAUSE frames port 3 sent to the host" is 推.
Not established: that the host honoured them, or that they caused block 50's
per-second stalls (`notes/nic-driver.md` § 28); the counter's width.

**`PSRP3` at the loader's prompt.** 量 `R1-DW:2`: `BB804134:` followed by four
tab-separated words, `000010E0`, `000010E0`, `000000E2`, `0000007A`.
`DW BB804134 1` printed four words (`SPEC.md` `LDR-07`: `DW` prints
4 × ceil(N/4) words and does not align the address down), so the first is
`PSRP3`, read 2.62 s after the banner (0.33 s after the loader's first prompt;
its reply line's arrival, raw clock): bit 8 clear, bit 12 set (the
loader-state bit, `NET-34`), bit 4 clear — no link yet, and the speed and
duplex field at `E0`, the word of a port that has not negotiated since
power-on (`NET-11`). Card B52's P2 (its
lines 418–440) predicted bit 4 set (推, from block 24's `C10-PS0`, `000011F9`
at a prompt); at 2.62 s it was clear. Words 2–4 are 推 `PSRP4`–`PSRP6`:
`000000E2` and `0000007A` equal slot 0's `PSRP5` and `PSRP6` on the first
switch page (`B-SW:42–43`), and `000010E0` is slot 0's word for an unlinked
port (`PSRP0`, `B-SW:40`); a read clears `PSRP` bit 8 (`NET-11`), and all
three read it clear, so the read consumed nothing there. The boot's
`R1-SW7:1` reads `RLXFW-SW7=00000000` and `B-SW:17` `lde0 00`: no `PSRP` held
bit 8 at S0′.

Card B52's gate for that cell (its line 1874, `^BB804134:\t[0-9A-F]{8}$`)
expected one word, contradicting `LDR-07`, and stopped `I-1` (`run-I-1.log`:
`STOP: gate grep R1-DW`, rc 3). By the card's § 6 rule (its lines 3332–3338)
the run went on from `R1-FL` as `I-1-r2`, and P2's loader half is
**unmeasured**: bit 8 = 0 stands as a reading, not as P2's decision. It is one
more reading for `NET-30` 殘留 (where a latched link-down comes from), not a
decision. Beside `PSRP` 保留態的起點 (§ 14.11): port 3's field was `E0` at
this read and `F9` at S0′ (slot 0 `000010F9`, `B-SW:41`, latched before the
`SW7` mark 150.0 s after the banner), so it left `E0` inside that window on
that power-on — a bracket, not the moment.

## 14.10 `C-19`, the flash bracket and the record (block 51)

* **What was sent** (量): 65 strings — the 59 `sent` fields of the captures'
  `.meta.json` and the six steps of `looprun`'s `R1Q-rescue.json`. The card's
  cells typed `MDIOR 2`, `MDIOR 3` and shell lines; `looprun` typed
  `AUTOBURN`, `LOADADDR` and `IPCONFIG`, each first in a colon form the
  loader rejects as an unknown command and then in the form it takes
  (`AUTOBURN 0` among them), and `DW 8040D4A0 1`, `DW 80500000 8` and
  `J 80500000`. **Zero `FLW`, `EW`, `EB`, `DB`, non-zero `AUTOBURN` and
  `FLR`**; the two `DW`s are `looprun`'s reads. The `AUTOBURN` word read
  `00000000` (`R1Q-ab2:2`, the first of the four words `LDR-07` prints) in the
  capture that ran 17:52:05.78–17:52:07.96, before the upload stage began at
  17:52:08.92 (`R1Q.stages.tsv`'s `S6`, placed with the file's own
  `start_raw`/`start_real`). The only write to `/proc/rtl819x-nic` was
  `A-FIX`'s; `/proc/rtl819x-spi` took `map 0` twice (`R1-M0`, `R1-M1`).
* **The map bracket** (量): `R1-MB0` and `R1-MB1` read the digest `0927be41…`
  with `31 same, 1 DIFFER` in group 0, as blocks 46–48 did (`R1-MB0:1–3`,
  `R1-MB1:1–3`); the two map sections are identical byte for byte, with
  `map_hashed 4186112` at both (`R1-M0:12`, `R1-M1:12`). `n_writes` and
  `n_write_refused` read 0 at both ends (`R1-NW0:25–26`, `R1-NW1:25–26`);
  `n_writes` carries no information about writes (`FW-142`). The bracket
  reaches from `R1-M0`'s start, 17:52:35.25, to `R1-M1`'s end, 17:54:29.66.
  What it cannot see: the boot before `R1-M0`; the 2 min 14 s from `R1-M1`'s
  end to the power-off, in which only `R1-NW1`'s `cat` and the watches' ESC
  bytes reached the board; `H601`'s 8,192 bytes, never hashed; two writes
  that cancel; any byte outside the map's windows.
* **`C-19`: no console drop** (量). The host's kernel log
  (`$FWRE_WORK/rebuild/s114/host43c/dmesg-w43c.log`, followed from before the
  attach; no line of it is in `bench/`) holds no `USB disconnect` line up to
  its last stamp, 469.8 s, past `X-W2`, and `usb_disc 0` in every window
  (`R0-DW0:9`, `B-L:19`, `G-L:20`, `V-L:20`, `Z-DW:10`, `Z-DWALL:9`); its four
  `cp210x` lines and one `ttyUSB` line are the attach at 22.35 s, before
  power (`R0-DW0:10–11`). One gap between consecutive console captures
  exceeded a minute — 62.18 s, `R0-PRE` to `R1-CATCH`, with the board off —
  and no drop followed it; the board then sat at its shell for 112.94 s
  inside `X-W1`. Readings beside it: 31 `smp_processor_id()` in preemptible
  `BUG` traces inside the windows (17, 7, 6 and 1 at `B-L:15`, `G-L:16`,
  `V-L:16` and `Z-DW:6`; `Z-DWALL:5`) and one more at kernel time 366.1 s,
  during `X-W1` (推, placed by the transcripts' monotonic stamps); block 49
  logged 511 (`bench/2026-09-27/Z-DWALL.log`).
* **What the watch does to a live shell** (card § 7's 推), 量: the board
  answered the ESC stream with BEL bytes (`0x07`) and nothing else — 5,433 in
  `X-W1`, its longest silence 84 ms, and 800 in `X-OFF1`. The closing CR
  `X-W1` wrote on its stop brought back one more BEL and no line of text; the
  card's 推 of an error line at the head of the next capture was not seen.
* **The record.** Card § 4 (card lines 604–606) wanted the X-cells logged in
  `bench/2026-09-27c/CORRECTIONS-block51.md` as they ran; no such file was
  written at the press and `fb4226d` has none, so it is written late, this
  segment, as a record of the three X-cells that ran, and says so.

## 14.11 What block 51, and § 14.9, do not establish

* **`PSRP` 保留態的起點**: undetermined. The card put it ⊘ (decision E: it
  needs a cable move and a prediction). 量 Port 3 already read `F9` at S0′
  (slot 0 `000010F9`, `A-SW:41`) and at the first Linux read (`A-SW:21`,
  29.2–29.3 s after the banner), and ports 0–2 and 4 read `E0` on all five
  switch pages. Block 50's prompt read (§ 14.9) brackets port 3's leaving
  `E0` on that power-on between 2.62 s after the banner and S0′: a reading,
  not the moment.
* Whether `0x0000` at addresses 5–31 means "no device" (§ 14.4).
* Whether the switch's own PHY poller meets a selected page: the scan and
  `lde` detectors were blind (`G-PCTL`, § 14.5).
* **The vendor's page-0 restores after (g′).** No `pread` ran after `V-X4`,
  and (g′)'s detectors were blind, so which page PHYs 0–4 sat on from the
  vendor's `extRead`s (17:53:49.80–17:54:00.42) to the power-off is known only
  from the vendor's code (讀: `extRead` writes register 31 ← 0
  unconditionally).
* Whether port 1 needs the patch; what page-1 registers 19 and 20 do.
* `STATUS`'s length in time; what `MDCIOSR` 30:16 means.
* A permutation among addresses 0–4 (§ 14.2).
* The probe's own `-EAGAIN` guard on the die (card § 0 ⑦ (1)); that a power
  cycle resets PHY registers (推, decision B); the loud image and phylib's
  `rtl819x-mdio: probed` line; a second boot of 1.3.
* From § 14.9: why the host adapter's driver honours `ethtool -r`; that the
  host honoured port 3's PAUSE frames or that they caused the per-second
  stalls; P2's loader half (unmeasured); where block 24's latched link-down
  came from (`NET-30` 殘留).

# 15. 2026-09-27 (`R6b-10`) — 1.4: `phyif`, arm II's one write class

**Everything in this section is 讀 at the desk** — the driver's text, and build artefacts read by an
instrument — except the readings it cites as 量, which are older captures. Nothing of 1.4 has run on
the silicon. `SPEC.md` `NET-155`; the images are `FW-154` (`notes/nic-driver.md` § 29.5). The session
material is `$FWRE_WORK/rebuild/s115/r6b10/` (not in this repository).

## 15.1 Why

Arm II's step (5) is the one declared write class the plan names, `PCRP0`–`PCRP4 |= EnablePHYIf`,
the inverse of what the loader's `J` does (§ 8.3). 8b found that nothing on the `SWCORE=n` image can
make it — `restore` skips `PCRP`, `rtl819x-view` has no store, `rtl819x-nic` stops at `0x064`, the
vendor's memory node is gone, `EW` writes flash — and named what had to be added (8b's
`RUN-armII.md` § 2). 1.4 is that verb, so arm II can type (5) on the boot that reads (4).

## 15.2 The bit, and where each part comes from

* **`EnablePHYIf` is bit 0 of `PCRPn`, on two sources and a measurement.** D, the draft datasheet's
  Table 64: bit 0 `EnablePHYIf`, *Enable PHY Interface*, RW, default 0 — *"When disabled, the PHY
  interface will be isolated from the MAC. Packets will not be transmitted or received to/from the
  PHY to/from the MAC interface."* B, `rtl865xc_asicregs.h:1258`, `EnablePHYIf (1<<0)`, in the
  `CONFIG_RTL_8196E` arm that opens at `:1168` — the arm the build compiles; the `#else` arm's
  `:1322` names the same bit. 量, the transition: `PCRP0`–`PCRP4` read `nn7F0039` at the prompt and
  `nn7F0038` at `S0′` (`bench/2026-09-19` `C1-L4104`, `C2-L4114`, `C9-SW0`; `NET-43`), and the
  vendor's probe sets the bit back (`C9-SW0`'s live column, `NET-52`). The loader's `J` clears
  exactly this bit, ports 0 to 4 in that order (讀 `0x804092F4`–`0x80409354`, § 8.3); the verb sets
  it in the same order.
* **The identity check's field, `ExtPHYID`, bits 30:26**, is on three: D Table 64 (default ports
  0–4 = `0x0`–`0x4`), B `:1174`–`:1175` in the same arm — the `#else` arm puts it at 28:24
  (`:1277`–`:1278`), which is why the arm is named — and 量 `NET-09` (0, 1, 2, 3, 4 on `E9`).
* **The addresses**, `0xBB804104` + 4n, were already this driver's table since 1.0: B `:1132`–`:1138`,
  D Table 62, and the same captures.

D's default of 0 agrees with `FULL_RST`'s `PCRP0` of `007F0038` (§ 3.1, `C27-RST1`).

## 15.3 The verb

On `/proc/rtl819x-switch`, whose handler now passes every write none of its own verbs took to 1.4
(the old `return -EINVAL` at `:664`); anything 1.4 does not know is still -EINVAL.

| verb | what it does | refused |
|---|---|---|
| `unlock phyif-i-mean-it` | opens this class | — |
| `lock phyif` | closes it | — |
| `phyif <n>` | n = 0–4, one digit and nothing after it: port n | the class locked: -EPERM, counted in `refused`, no register read |
| `phyif all` | ports 0, 1, 2, 3, 4 in that order, stopping at the first that fails | the same |

**Why a token of its own**: `/init` types the switch's `unlock i-mean-it` on every standard boot
(`config/rlxfw-init.sh`) — MDIO's reason (§ 10.4). The store also needs that unlock, because it goes
through `rtl819x_sw_wr`, the one guarded write path: `n_writes` counts it, and a locked switch
refuses it (-EPERM, counted in the switch's `n_refused`). So on a quiet-`/init` image a `phyif` store
needs two words typed, and on a standard one it needs one more word than any other switch write.

**One port**, with IRQs off from the pre-read to the read-back, so nothing that runs from an
interrupt writes the register between them (UP and `PREEMPT_NONE`, which 1.2's `#error` enforces):
read `PCRPn`; -EPROTO, nothing written, unless its `ExtPHYID` is n; if bit 0 is already set, store
nothing (`already`, rc 0); else store exactly the word read with bit 0 set and read it back, which
must equal that word or the port fails -EIO (`rbfail`). A bit 0 that does not stick and any other bit
that moved both fail it. No other bit is ever stored differently from how it was read, and no
register but `PCRP0`–`PCRP4` is ever stored. A verb that reaches the ports resets all five results
first, so the page shows one verb's results; the mark is `RLXFW-SW-PHYIF=` with the stored ports in
bits 12:8 and the ports verified set in bits 4:0.

**The page** gains six lines before the register table, whose last line stays the page's last line:
`phyif unlocked … ok … stored … already … refused … idfail … rbfail …`, then per port `phyifN pre
XXXXXXXX rb XXXXXXXX rc D st D` — the pre-read, the read-back (`00000000` unless `st 1`), the rc (1:
the last verb did not reach the port) and whether it stored. Cached values: a `cat` reads no
register for them. Walked from the formats, every field at its widest, 133 + 5 × 54 = 403 bytes, so
1.2's worst case of 2,080 of 4,096 becomes 2,483 and the table's budget (3,600) still never ends the
page. No mark and no read at boot: the boot capture does not change.

**Line numbers.** 1.3's 1,463 lines keep their numbers: `:118` (the version) and `:664` changed in
place, and `:526`, `:549` and `:587` were blank and hold two prototypes and the page hook. The ranges
other files cite — `:88`–`:92`, `:93`–`:97`, `:375`, `:560`–`:564`, `:588`–`:661` — are byte-identical
to 1.3's. 199 lines are appended after the MDIO block.

## 15.4 What the desk measured

* **`tools/mdiocheck.py` 71 of 71.** Its cut, from the 1.3 banner to the end of the file, now holds
  1.4's block, compiled with the host's gcc (`-std=gnu89 -Werror`) against a transcription of the
  switch's one read path and one guarded write path over a `PCRP0`–`PCRP8` model whose default is
  the post-`J` state, with two faults per port (bit 0 does not stick; bit 3 flips on a store) and
  every `PCRP` access logged with its IRQs-off section. Thirteen new cases, K24–K36: the boot lines
  byte for byte and a `cat` that reads nothing; the class locked (-EPERM, counted, no access); the
  switch's own token, a near miss and a doubled space refused, `unlock phyif-i-mean-it` and `lock
  phyif`; `phyif all` from the post-`J` state — R `nn7F0038`, W `nn7F0039`, R for ports 0 to 4 in
  order, each port's three in one IRQs-off section of its own, mark `00001F1F`; `phyif 3` alone, the
  previous verb's results cleared; ports 5, 6, 8 and 9 and fifteen malformed or unknown forms
  -EINVAL with no access, each beside a permitted neighbour; bit 0 already set (one read, no store);
  a word with port 1's `ExtPHYID` in port 2 (-EPROTO, no store, `all` stops there); bit 0 not
  sticking (-EIO, `all` stops); bit 3 moved (-EIO although bit 0 stuck); the switch locked (one
  read, no store, the switch's `n_refused`); 64 drawn words stored with bit 0 alone changed; the
  lines at their widest against the comment's 403. Twelve new mutants, M21–M32, each killed by the
  case it names. K1's boot page reads `version rtl819x-switch 1.4`. `tools/ci-expected.tsv` 46 → 71.
* **The object.** `rtl819x-switch.o` is byte-identical between `r6b10y` and `r6b10n`, as 8b found
  1.3's. Each `vmlinux` holds `rtl819x-switch 1.4`, `phyif-i-mean-it` and `lock phyif` once. The
  builds add no warning.

## 15.5 Arm II, updated: `RUN-armII.md`

8b's sheet with the image changed to `r6b10n`, the cells renamed (`M…`: `bench/2026-09-27d/`
already holds `X-W1`), step (3) typing no `txlen` — `M3-NICR` gates on the boot policy instead —
and step (5) typeable. **(4) → (5) is a decision point, so it is two lines**: `n-line1` runs (1) to
(4) and ends in Linux; if (4) had no reply, `n-line2` types (5): `M5-REF`, `phyif all` without the
class token, which must be refused with `n_writes 0` — the guard seen refusing on the silicon before
it is seen permitting — then both unlocks, `phyif all` (gated on `ok 1`, `idfail 0`, `rbfail 0` and
every port `rc 0`), both locks, a `peek` of `PCRP` through `rtl819x-view` as a second reader, the
pings again, (6) and the reboot; if (4) was answered, `n-line3` runs (6) and the reboot.
`cardcheck commands`: rc 0, 41 sends (3 loader `DW`, 38 shell), 0 flash-write verbs, 0 `FLR`; a copy
with a planted `EW` and `FLR` is refused (rc 1). Every line dry-run through `cardrun --dry`, rc 0.

## 15.6 What 1.4 does not establish

* Anything on the silicon: whether bit 0 sticks, whether the link follows, whether (4) fails and
  whether (5) is then sufficient — arm II's.
* That `EnablePHYIf` is necessary on any one port: the verb sets five, and a pass at (5) cannot say
  which mattered.
* That the vendor's other `PCRP` writes are unneeded — its `EnForceMode` brackets around paged PHY
  writes (`Setting_RTL8196E_PHY`), for one — or anything about `D8`, which asks for rlxfw's own
  switch init (arm I).
* That the transcription `mdiocheck` drives is the driver's code: the read and write paths above the
  cut are copied into the harness, not compiled from the driver.

# 16. 2026-09-27/28 (`R6b-8` 8c-cells, group A; arm II) — the take-over list in three columns, `reset vendor`, `ByPassTCRC`, and arm II as `D8`'s control

Group A of 8c-cells and arm II, read at the desk (segment 115). `NET-25`'s ten cold boots, `M3`'s
isolated-spacing arm and `R6b-10`'s regression are `notes/nic-driver.md` § 30's. The design is
`$FWRE_WORK/rebuild/s115/r6b8c-cells/DESIGN.md` (not in this repository) and the card `CELLS-A.md`,
committed beside the captures in both directories that hold them — the owner's relaxed process for
`R6b`, no freeze; arm II's sheet is `bench/2026-09-28/RUN-armII.md`. The readings are two readers'
(`$FWRE_WORK/rebuild/s115/read-night/READING-1.md` and `READING-2.md`) and the main session's
rulings on them (`RULINGS-night.md`, same directory, cited as ruling *n*), which bind this record.
Every number below was re-read from its capture for this record by scripts that share no code with
the readers' (`$FWRE_WORK/rebuild/s115/rec-night/scripts/`: `v_cols.py`, `v_all.py`, `v_phy.py`,
`v_s0.py`, `v_xc.py`, `v_mib.py`, `v_clock.py`, `v_sent.py`; each refuses when a planted defect does
not turn it red, and `v_mib.py` reads `tools/viewdecode.py`'s own rendering of the view's words).

Capture names are `bench/2026-09-28/`'s unless marked `27d/` (`bench/2026-09-27d/`). `NAME:N` is
line N of `NAME.log`, counted on LF with CR stripped. Marks: 量 a capture, 讀 code or a document,
推 inferred.

## 16.1 What ran

* **`bench/2026-09-27d/`, a cold power-on** (量; `CORRECTIONS-8c-A.md` there). The owner powered
  the board on for later unattended use, and the loader was caught at 18:01:26 (`27d/S-CATCH`,
  whose line 5 is `C-8`'s one-space line: cold, `CLK-15`). At 20:09:24–20:09:39 `A-L` read the
  **loader-inherited column** at that prompt: 27 cells, 19 `DW` and 6 `MDIOR`, 105 gates, all ok
  (the run record, `$FWRE_WORK/rebuild/s115/r6b8c-cells/run/A/`). The design's two positive
  controls held: `REVR` `8196E001` (`27d/AL-D01:2`) and `CVIDR` `81964000` (`27d/AL-D08:2`).
* **The standby failure** (ruling 9; `NET-165`). `A-B`'s `looprun` round (`27d/A1Q`) passed S5 —
  `AUTOBURN 0`, `LOADADDR` and `IPCONFIG 10.1.1.1` each accepted (`27d/A1Q-rescue.json`) — and
  S5b, the `AUTOBURN` word read back `00000000` (`DW 8040D4A0 1`, `27d/A1Q-ab2:2`), and failed
  S5c: the loader answered no ARP and the host's entry stayed `INCOMPLETE` (`27d/A1Q:10`), 2 h 8
  min after the catch. Nothing was uploaded, and the tail watch ended on the loader prompt. Why an accepted
  `IPCONFIG` was followed by no ARP answer is undetermined: about two hours at the prompt and
  `A-L`'s reads both came before it, and nothing separates them. The loader answers the network
  only after `IPCONFIG` (`NET-95`); a fresh prompt and `IPCONFIG` answered ARP 3 of 3 twice later
  that night (the main session's `arping`, whose output is in no committed file). Ruling 9 records
  it as a bench rule — no unattended standby — and not as a question with an experiment owed.
* **The power cycle after midnight, `bench/2026-09-28/`** (量; `CORRECTIONS-A-r6b10-armII.md`
  there). 27d's power cycle ended with the owner's power-off before `NET-25`'s boot 1. Group A
  resumed from `A-B` at 00:05:31 on boot 10's power cycle, after that boot's `busybox reboot -f`
  (a watchdog reset, `FW-37`; `bench/2026-09-27n/B-RB`, ended 23:55:16) and an off-card `IPCONFIG`
  (`bench/2026-09-27n/X-ARP1`, 23:55:54). Eleven invocations, `A-B` to `A-Z`, ran to 00:13:33,
  each rc 0: 295 cells and 892 gates, all ok (`AT-T1`'s rc 1, the test ping's 0 of 20, is declared
  a reading). `R6b-10`'s regression (`notes/nic-driver.md` § 30.4) and arm II (§ 16.7) followed on
  the same power cycle, with no power action between.
* **So the columns come from two power-ons.** **L** is 27d's cold prompt. **V** (vendor-configured:
  after the vendor's probe, before any rlxfw write or interface open) and **R** (after
  `reset vendor`) are one Linux boot of 28 that followed a watchdog reset. That boot's own
  loader-inherited sample is **S0′**, the 37 words `rtl819x-switch` latches at `subsys_initcall`
  (§ 8.3): `A2-SW`'s S0′ equals, word for word, the S0′ of the ten cold boots
  (`bench/2026-09-27e/B-SW` to `bench/2026-09-27n/B-SW`) and of `Y2-SW` and `M2-SW`, the two later
  boots of 28's power cycle — 37 of 37 each (量). L and S0′ share 30 words: 25 are equal, and the
  other 5 are `PCRP0`–`PCRP4`, differing in bit 0 alone — the loader's `J` clearing `EnablePHYIf`
  (§ 8.3). 推: for words outside the switch page, L stands in for 28's loader-inherited state.

## 16.2 The take-over list: three columns (量 unless marked; `NET-160`)

Δ codes: **LV** changed by the vendor's init (against S0′ where S0′ holds the word); **VR** changed
by `reset vendor`; **LR** R differs from L. `*` marks a one-source word (B only), read through the
vendor's memory node; `=M08:4` says a second instrument printed the same value in `AV-M08:4`. The
cites are L (`27d/`, but `A2-SW`, which is 28's); V; R.

| register | L (S0′) | V | R | Δ | L; V; R |
|---|---|---|---|---|---|
| `MACCR` 4000 | `804A0185` | `804A0185` | `80420186` | VR LR | `AL-D03:2`; `AV-P01:8` =M08:4; `AR-P01:8` |
| `BSCR` 4044 | 0 | 0 | 0 | = | `AL-D04:2`; `AV-P02:8` =P02b; `AR-P02:8` |
| `CSCR`* 4048 | `00000008` | `00000018` | `00000008` | LV VR | `AL-D04:2`; `AV-M02:4`; `AR-M02:4` |
| `PCRP0`–`4` 4104–14 | `nn7F0039` (S0′ `nn7F0038`) | `nn7F0039` | `nn7F0038` | LV VR | `AL-D05:2–3`, `A2-SW:33–37`; `AV-P03:9–13` =M09:4, M10:4; `AR-P03:9–13` |
| `PCRP5`–`8` 4118–24 | 0, `187F0038`, `1C7F0038`, `207F0038` | the same | the same | = | `AL-D06:2`; `AV-P03:14–17` =P03b; `AR-P03:14–17` |
| `EEECR`* 4160 | `294A5294` | 0 | `294A5294` | LV VR | `AL-D07:2`; `AV-M03:4`; `AR-M03:4` |
| `SSIR` 4204 | 1 (S0′ 1) | 0 | 0 | LV LR | `AL-D08:2`; `AV-P05:9` =M11:4; `AR-P05:9` |
| `MEMCR` 4234 | S0′ `00007F7F` | `00007F00` | `00007F00` | LV | `A2-SW:46`; `AV-P06:8`; `AR-P06:8` |
| `LEDCREG` 4300 | `00200000` | `00200000` | 0 | VR LR | `AL-D09:2`; `AV-P07:8` =P07b, M12:4; `AR-P07:8` |
| `LEDCR1`, `LEDBCR` | 0 | 0 | 0 | = | `AL-D09:2`; `AV-P07:9`, `AV-P08:8` =P07b, P08b; `AR-P07:9`, `AR-P08:8` |
| `TEACR` 4400 | 0 | 2 | 0 | LV VR | `AL-D10:2`; `AV-P09:8` =M13:4; `AR-P09:8` |
| `ALECR` 440C | 0 | `000505F2` | 0 | LV VR | `AL-D10:2`; `AV-P09:11`; `AR-P09:11` |
| `MSCR` 4410 | 1 | `00000011` | 1 | LV VR | `AL-D10:3`; `AV-P09:12` =M13:5; `AR-P09:12` |
| `SWTCR0` 4418 | `00080000` | `00097DE0` | `00080000` | LV VR | `AL-D10:3`; `AV-P09:14`; `AR-P09:14` |
| `SWTCR1` 441C | `00000200` | `00000E00` | `00000200` | LV VR | `AL-D10:3`; `AV-P09:15`; `AR-P09:15` |
| `PLITIMR` 4420 | `07FAC688` | `00001000` | `07FAC688` | LV VR | `AL-D10:4`; `AV-P09:16` =M13:6; `AR-P09:16` |
| `DACLRCR` 4424 | 0 | `0FBF7EFD` | 0 | LV VR | `AL-D10:4`; `AV-P09:17`; `AR-P09:17` |
| `FFCR` 4428 | 3 | 9 | 0 | LV VR LR | `AL-D10:4`; `AV-P09:18`; `AR-P09:18` |
| `SBFCTR`* 4500 | `000000F4` | `000000F4` | `000000F4` | = | `AL-D11:2`; `AV-M06:4`; `AR-M06:4` |
| `IBCR0`–`2`* 4704–0C | 0 | 0 | 0 | = | `AL-D12:2`; `AV-M04:4`; `AR-M04:4` |
| `QNUMCR`* 4754 | `00001249` | `00041249` | `00041249` | LV LR | `AL-D13:2`; `AV-M01:4`; `AR-M01:4` |
| `WFQRCRP0`–`4`* / `P5`* | `00003FFF` / 0 | the same | the same | = | `AL-D14:2–5`; `AV-M05:4–7`; `AR-M05:4–7` |
| `VCR0` 4A00 | `000001FF` | 0 | `000001FF` | LV VR | `AL-D15:2`; `AV-P10:8` =M14:4; `AR-P10:8` |
| `PVCR0`–`4` 4A08–18 | `00080008` ×4, 1 | `00090009`, `00090009`, `00010008`, `00010001`, 9 | `00010001` ×4, 1 | LV VR LR | `AL-D15:2–3`; `AV-P10:10–14` =M14:4–5; `AR-P10:10–14` |
| `PBVCR0` 4A1C | 0 | `00021B74` | 0 | LV VR | `AL-D15:3`; `AV-P10:15`; `AR-P10:15` |
| `SWTAA` 4D08 | `BB060100` | `BB040020` | 0 | LV VR LR | `AL-D16:2`; `AV-P11:10` =M15:4; `AR-P11:10` |
| `TCR7` 4D3C | 0 | `07000030` | 0 | LV VR | `AL-D17:2`; `AV-P12:8`; `AR-P12:8` |
| `0x4D48`* | `BB060100` | `BB040020` | 0 | LV VR LR | `AL-D17:2`; `AV-M07:4`; `AR-M07:4` |
| `PSRP0` / `PSRP3` bit 12 | S0′ `000010E0` / `000010F9` | `000000E0` / `000000F9` | `000010E0` / `000010E0`, relinked `000010F9` | LV VR | `A2-SW:40–41`; `AV-SW:40–41`; `AR-RST:41–42`, `AR-MDS:31` |
| `PIN_MUX_SEL` / `SEL2` | 6 / 0 | 6 / 0 | 6 / 0 | = | `AL-D02:2`; `AV-P15:8–9` =P15b, M18:4; `AR-P15:8–9` |
| `CPUICR` B8010000 | `C4000000` | 0 | 0 (`04000000` before) | LV LR | `AL-D18:2`; `AV-P13:8` =M16:4; `AR-P13:8` (`AR-C0:8`) |
| the CPU ring registers (`RPDCR0`, `RMDCR0`, `TPDCR0`–`3`) | the loader's ring addresses | 0 | 0 | LV LR | `AL-D18:2–4`, `AL-D19:2`; `AV-P13:9–17`, `AV-P14:8–9`; `AR-P13`, `AR-P14`, the same lines |
| `CPUIIMR` / `CPUIISR` | `000007F8` / 0 | 0 / `80000000` | 0 / `80000000` | LV LR | `AL-D18:4`; `AV-P13:18–19` =M16:6, M17:4; `AR-P13:18–19` |
| `CPUQDM0`–`5` | 0 | 0 | 0 | = | `AL-D18:5`; `AV-P13:20–22`; `AR-P13:20–22` |
| VLAN table | not read | s00 `00921F0F`, s01 `00842010`, 14 zero | 16 zero | VR | —; `AV-TV:8–23`; `AR-TV:8–23` |
| netif table | not read | s00 and s01 set, 6 zero | 8 zero | VR | —; `AV-TN:8–15`; `AR-TN:8–15` |
| MIB, 225 words | — | all 0 | all 0 (non-zero just before: `AT-R9:44`) | VR | —; `AV-VM1:9–16`; `AR-VM:9–16` |

**The PHY registers.** PHYs 0–4 read the same in every cell. Where both instruments read a register
(17, 21, 22, 26, and page 1's 16 and 19), rlxfw's `pread` equals the vendor's `phyReg` in 30 of 30
reads (量).

| reg | L | V | R | Δ | L; V; R |
|---|---|---|---|---|---|
| 0 | `1100` | `1100` | `3100` | VR LR | `AL-R00:2–6`; `AV-MDS:20–24`; `AR-MDS:28–32` |
| 4 | `0DE1` | `0DE1` | `0DE1` | = | `AL-R04:2–6`; `AV-MDS:20–24`; `AR-MDS:28–32` |
| 17 | `1F10` | `1E10` | `1F10` | LV VR | `AL-R17:2–6`; `AV-MP01:22` to `AV-MP03:26`, `AV-PV01:3` to `AV-PV03:3`; `AR-MP01:28` to `AR-MP03:28` |
| 21 | `02C2` | `02C2` | `02C5` | VR LR | `AL-R21:2–6`; `AV-MP03:27` to `AV-MP05:29`; `AR-MP03:29` to `AR-MP05:29` |
| 22 | `5BC7` | `5BC7` | `5B8F` | VR LR | `AL-R22:2–6`; `AV-MP06:28` to `AV-MP08:28`; `AR-MP06:28` to `AR-MP08:28` |
| 26 | `4000` | `0000` | `4000` | LV VR | `AL-R26:2–6`; `AV-MP08:29` to `AV-MP10:29`; `AR-MP08:29` to `AR-MP10:29` |
| page 1, 16 | — | `D100` | `9100` | VR | —; `AV-MP11:28` to `AV-MP13:28`, `AV-PV11:3` to `AV-PV13:3`; `AR-MP11:28` to `AR-MP13:28` |
| page 1, 19 | — | `7380` | `7381` | VR | —; `AV-MP13:29` to `AV-MP15:29`; `AR-MP13:29` to `AR-MP15:29` |

Registers 1–3 and 5 read the same in V and R (`AV-MDS:20–24`, `AR-MDS:28–32`). A `pread` page keeps
its last eight results, so in each `AR-MP` page only lines 28–29 are the post-reset reads; the lines
above them are the page's history. Page 4's register 16 (EEE) has no reading in any column: the
owner's pages-0-and-1 limit, applied to the vendor's `extRead` too (the main session's ruling of
2026-09-27, the design's § 7).

**What the vendor's init changes (the LV rows).** `TRXRDY` off, and `EnablePHYIf` set again on
`PCRP0`–`4`; `CSCR` bit 4 set; `EEECR` cleared to 0; `TEACR`, `ALECR`, `SWTCR0`, `SWTCR1`,
`PLITIMR`, `DACLRCR`, `FFCR`; `MSCR` 1 → `0x11`; `QNUMCR`'s CPU field 0 → 1; `VCR0` → 0; the PVIDs
(the LAN ports 9, port 4 8; 讀 `NET-37`'s field split); `PBVCR0`; `SWTAA`, `0x4D48` and `TCR7`;
`MEMCR`'s low byte; `PSRP` bit 12; both tables written; the loader's CPU ring registers and
`CPUIIMR` set to 0 and `CPUIISR` bit 31 set; PHY register 17 bit 8 and register 26 bit 14 cleared.

**What it leaves alone (L = V).** `MACCR`, `BSCR`, `PCRP5`–`8`, `CVIDR`, `CRMR`, `BISTCR`, `LEDCREG`,
`LEDCR1`, `LEDBCR`, `TEATCR`, `RMACR`, `L4TOCR`, `MGFCR_E0R0`, `SBFCTR`, `IBCR0`–`2`,
`WFQRCRP0`–`5`, `VCR1`, `SWTACR`, `SWTASR`, `P0GMIICR`, the `PIN_MUX` pair, `CPUQDM0`–`5`, and PHY
registers 0, 4, 21 and 22 (量; `v_all.py` lists every word read in V with its L and R).

## 16.3 What `reset vendor` does (量, one boot; `NET-161`)

Before the reset `CPUICR` read `04000000` by two instruments, the NIC page's `now_icr`
(`AR-NIC:49`) and a `peek` (`AR-C0:8`) — `TXCMD` and `RXCMD` clear, 8d's `reset` refusal applied by
hand after `disarm`. `AR-RST:2` reads `RLXFW-SW-RST=00000002` and `:9` `n_reset 1`.

* **Back to L:** `CSCR`, `EEECR`, `TEACR`, `ALECR`, `MSCR`, `SWTCR0`, `SWTCR1`, `PLITIMR`,
  `DACLRCR`, `VCR0`, `PBVCR0`, `TCR7`, `PSRP` bit 12, and PHY registers 17 and 26.
* **Not back:** `MACCR` `80420186`; `EnablePHYIf` clear (`PCRP0`–`4` `nn7F0038`) and `TRXRDY` 0;
  `FFCR` and `LEDCREG` 0; the PVIDs 1 (`PVCR0`–`3` `00010001`, `PVCR4` 1); `SWTAA` and `0x4D48` 0;
  both tables empty and the MIB zeroed; `CPUICR` `04000000` → 0; PHY registers 0 (`BMCR` `3100`),
  21 and 22 and page 1's 16 and 19 at new values. `QNUMCR` stays `00041249`, and `MEMCR` stays
  `00007F00`, the value the reset started from. Also not back: `MDCIOCR` → 0 (§ 17.7).

**So R is not the loader's state.** 推: the PHY changes are the reset's own, not a vendor handler's
reaction to the link drop the reset causes. Not separated: `FULL_RST` from the 650-ms clock gate,
which the one verb does together.

## 16.4 The reads the design lacked (`NET-162`)

* **`PCRP7` and `PCRP8`**, `1C7F0038` and `207F0038` in all three columns (量), `EnablePHYIf` clear
  throughout. `PCRP8`'s first reading on this die: no committed capture before the night holds
  the word (`PCRP7` was read once, at a prompt, `bench/2026-09-19/C2-L4114:2`). `DW` and `peek`
  are one kind of source, so a write of these values would be undetermined; the vendor does not
  change them, so 8d writes nothing there and the two-source rule is not engaged.
* **`PIN_MUX_SEL` and `SEL2`**, `00000006` and `00000000` in all three columns (量), their first
  readings. The vendor's clears (`PIN_MUX_SEL &= ~0x8F18`, `PIN_MUX_SEL2 &= ~0x3B6DB`, 讀
  `rtl865x_asicL2.c:4568`–`:4569` in the tree that builds) change nothing on these values, and
  `rtl_gpio`'s `|= 6` (`REG-35`) agrees. 8d needs no write.
* **`QNUMCR`**: L `00001249`, the CPU port's field (bits 20:18) 0; V and R `00041249`, field 1. The
  field's value 1 has two sources — the vendor's write (讀 `rtl865x_asicL2.c:6554`–`:6555`) and
  the reads (量) — so it meets the rule **for the field only**, written read-modify-write. The
  other fields rest on the reads and on the loader's disassembly, which is not an admitted source,
  and D does not place the register. V = R: the reset leaves it alone (推 `FULL_RST` does not
  reset it; the clock gate is not separated). Which value rlxfw wants is 8d's to decide; the
  loader receives with the field at 0.
* **`LEDCREG`**: the SDK's `2<<20` (讀 `rtl865x_asicL2.c:4571`) and the reads agree on
  `00200000`, and D's Table 68 calls `10` reserved (`NET-134`): two sources of three, which meets
  the rule. A `reset vendor` clears it.
* **`PLITIMR`**: L `07FAC688` (the value block 24 read, `bench/2026-09-17b/C4-SW418:2`), V
  `00001000` (`peek` and the memory node agree), R `07FAC688`. `NET-28` 殘留's 推 *Linux 態是 0*
  is **refuted**, and the design's prediction of `00001000` held. V rests on reads alone, and the
  one vendor write on record writes 0 (讀 `rtl_nic.c:6370`, under `CONFIG_RTK_VLAN_SUPPORT`, which
  the build sets), so as a register value it stays undetermined (ruling 5). 推: port 4's interface
  index set to 1 (B's one-source field layout). R = L supports `07FAC688` as the reset value (推).
* **`0x4D48` equals `SWTAA` in all three states** — `BB060100`, `BB040020`, 0 — and moved with it
  from V to R on one boot (量). That meets `NET-28` 殘留's condition (*Linux 也讀 `BB040020`*) in
  substance, but L and V are two power-ons, not the one boot the row asked for. The word still
  has no name and one source.
* `QNUMCR`, `CSCR`, `EEECR`, `IBCR0`–`2`, `WFQRCRP0`–`5` and `SBFCTR` now have loader `DW`
  readings (the kind of 量 the view's admission table counts), so each has B and 量 for 8d's
  admission to `rtl819x-view`; `0x4D48` stays one-source.

## 16.5 `NET-109` 殘留: port 3's `ByPassTCRC` (`NET-163`)

The cell is the design's § 2.7 (`AT-*`, four invocations), its three readings written before power.

* **Pre-read**: `PCRP3` `0C7F0039` by `peek` (`AT-P0:8`) and by the memory node (`AT-M0:4`).
* **Control, bit 31 clear**: 20 of 20 (`AT-C0:4`).
* **Write, bit 31 set**: the node's read-back `0x8c7f0039` (`AT-W1:3`), `peek` `8C7F0039`
  (`AT-V1:8`); the word written is the pre-read with bit 31 added, nothing else.
* **Test, bit 31 set: 0 of 20** (`AT-T1:4`).
* **The host, `AT-H1` → `AT-H2`**: `rx_packets` 27886 → 27886 (`AT-H1:14`, `AT-H2:14`),
  **`rx_crc_errors` 0 → 0** (`:5` of both), every other receive counter unchanged, `tx_packets`
  +20 (量).
* **The board, `AT-R0` → `AT-R1`** (control and test together, `AT-D1:2–4`, `:7`, `:10`): `n_tx`
  +40, the CPU port's `CRCAlignErr` +40, **port 3's output +40**; the host +20; `fault jfd 0`.
  Port 3 counted the 20 test frames as sent. That the control accounts for the other 20 is 推: no
  board read sits between control and test.
* **Restore**: the node `0xc7f0039` (`AT-W9:3`), `peek` `0C7F0039` (`AT-V9:8`); liveness 4 of 4
  (`AT-L9:9`); the control again 20 of 20 (`AT-C9:4`); host +25 = board +25 (`AT-D9:2`, `:4`,
  `:7`).

**Against the cell's own three readings** (ruling 4): the result is the third — **0 of 20
received, host CRC Δ 0**, *frames lost on the wire and the adapter counts nothing*. The desk
reading's confirmation (CRC Δ ≥ 20) is not met, and the *not separated* outcome (20 of 20) is
excluded. 量: bit 31 acts on the CPU → port-3 path — 20, 0, 20 on one boot, each write read back
by two instruments — and port 3's MIB counts the lost frames as sent. Open: whether the frames
left with a bad FCS that the adapter drops without counting (推, the likelier; that counter never
had a positive control) or never left port 3; and whether bit 31 means *don't regenerate the CRC
of CRC-errored frames* (D Table 64, B) or no CRC generation at all — both predict this for CPU
frames. Separating them needs a non-CPU source into port 3's egress or a receiver whose CRC counter
has a positive control, and one link offers neither: `NET-109` 殘留 is ⊘ with that reason, reopened
when either exists.

## 16.6 The cross-checks, and what the instruments could not see (`FW-155`)

1. **The quiet MIB bracket** (`AV-AC0`, `AV-VM1`, `AV-AC1`): `viewdecode bracket` holds, 211
   counters pinned (量) — but all zero, since `TRXRDY` was 0 until `start` (推), so it tests no
   offset.
2. **Read-to-clear**, `AV-VM1` against `AV-VM2`: equal and all zero, so vacuous. **Instrument
   gap:** `viewdecode decode --one-boot` compares only a page's own counters (`COUNTS`,
   `tools/viewdecode.py:567`; `one_boot`, `:998`–`:1014`), never the MIB words, so it could not have
   shown `VM2` < `VM1`; and it voided the `VM2` → `AX` pair on a `jiffies` wrap.
3. **The `…b` double reads**, 16 words: all equal (量). Blind to a side effect on a zero word.
4. **The tables**: the design's prediction met exactly; 48 slot reads `t1 eq`, no `mis` and no
   `busy`; every view page `refused 0 busy 0` (`AV-VZ:5`, `AR-VZ:5`).
5. **`peek` against the memory node**, the V boot: 57 of 57 words equal, 25 of them non-zero with
   23 distinct values (量).
6. **The node's positive control**: `CVIDR` `81964000` (`AV-M11:4`).
7. **rlxfw's MDIO against the vendor's `phyReg`**: 30 of 30; the probe found five `001CC880`
   (`AV-MDP:15–19`); the locked page read nothing (`AV-MD0:14–18`).
8. **`port_status` against `PSRPn` and `PCRPn` bit 25**: 7 of 7 ports agree (the reading's count).
9. **`peek` against the switch page**: 30 of 32 registers equal. `MDCIOCR` and `MDCIOSR` differ
   (`AV-P01:9–10` `84001300`, `00001100`; `AV-SW:30–31` `841F0000`, `00007380`) because MDIO
   commands ran between the two reads (推: `841F0000` is PHY 4's page-0 restore after `AV-PV15`'s
   paged read). No address fault.
10. **The MIB after traffic** (`AX-AC0`, `AX-VM`, `AX-AC1`): holds, 211 pinned, 17 non-zero, and
    neither reader clears them (量). Control: `AX-VM` placed between `AV`'s two ends fails on 17
    counters. `lo + (hi << 22)` is not exercised: port 3 carried 147,664 bytes (`AX-VM:12`, word
    0 of `m3`, `000240D0`), below 2²². Its in and out byte counts are equal and two buckets tie at
    60, so a swap between tied counters would pass.
11. **The map bracket**: the same digest at both ends (§ 16.9).
12. **`CPUICR` before the reset**: `04000000` by `now_icr` and by `peek` (§ 16.3).
13. **`NET-28` 殘留**: `0x4D48` = `SWTAA` in all three states (§ 16.4).
14. **Unplanned**: rlxfw's `ENGON` value `C4000000` (`AN-N2:6`) equals the loader's `CPUICR`
    (`27d/AL-D18:2`).

Two § 17 rows move and stay open. **`NET-31` 殘留**: `PSRP` bit 12 moves with `EEECR` and PHY
register 26 in all three states — set, `294A5294`, `4000` in L/S0′ and R; clear, 0, `0000` in V —
so which vendor step clears it is still not separated. **`NET-33` 殘留 ②**: the reset again
started from `7F00`, so it cannot show what `FULL_RST` does to `MEMCR`'s low byte. Arm II (§ 16.7)
adds the first half of both rows' settling reads on a boot with no vendor probe.

## 16.7 Arm II on `r6b10n`: `D8`'s control, passing (`NET-164`)

量 unless marked, `bench/2026-09-28/` `M*` and the run record
`$FWRE_WORK/rebuild/s115/run10/2026-09-28/`: `n-line1` (00:21:34–00:22:58, rc 0), `n-line2`
(00:23:32–00:23:44, rc 3 at `M5-REF`'s `--until`) and `n-line2b` (00:27:11–00:28:03, rc 0; the
resume, correction 6 of `CORRECTIONS-A-r6b10-armII.md`). The image is `r6b10n` (`SWCORE=n`,
`rtl819x-switch` 1.4, `rtl819x-nic` 1.6 at its default; `FW-154`), `RLXFW-ID0=1CC05E88`
(`M1-MK:1`). `ethcensus` is green on it (讀 `FW-154`) and `/proc/rtl865x` is absent
(`M2-DEV:20`).

* **Reads before any write.** At the loader prompt `PCRP0`–`4` read `nn7F0039` (`M1-DWP:2–3`);
  after `J`, `nn7F0038`, live equal to slot 0 (`M2-SW:39–43`), and `rtl819x-view`'s `peek` agrees
  (`M2-VP1:9–13`); `PCRP7` and `PCRP8` `1C7F0038` and `207F0038` (`M2-VP1:16–17`). `psrp3
  000010F9 up 1` (`M2-SW:27`), `MSCR` `00000001` (`:55`), `VCR0` `000001FF`, `PVCR0`–`3`
  `00080008` and `PVCR4` 1 (`:59–65`): with no vendor probe the whole page reads live = S0′
  (`M2-SW:33–69`). The seam's marks: `RLXFW-SM0=C4000000`, `RLXFW-SM1=04000000` and
  `RLXFW-N1=04000000` (`M1-MK:2–3`, `:11`), the value § 13.5 predicted (`NET-150`'s 推, now read).
  **The loader's VLAN table** holds one entry, slot 8 (`M2-VV:16`, `00807E3F`: VID 8, member and
  untagged ports 0–5, `extMemberPort` 0 — 讀 B's field layout, `rtl865x_asicCom.h:230`–`:242`), and
  the netif table one, slot 0 — valid, VID 8, MTU 1500, ACL ranges 0–0 (the reader's decode of
  `M2-VN:8`, whose words carry a MAC address and are not reproduced here).
* **Step (4), before any switch write: no ping either way.** Host → board 0 of 4 at 46 B and 0 of 4
  at 84 B (`M4-PL:4`, `M4-PD:4`), the host's neighbour entry `FAILED` (`M4-NB:1`); board → host 0
  of 4 (`M4-BP:5`). `rlx0` sent 6 frames (`M4-NIC:42`, `nd_stats … tx 6/360`); between `M2-VM`
  and `M4-VM` the CPU port's FCS count and 64-byte bucket rose by 6 and port 3's broadcast output
  by 6 (`viewdecode`'s names), while port 3's input did not move and the host received 0 and sent
  3 (`M4-HP0:1–2` → `M4-HN:14`, `:23`). 推: the loss is at port 3's MAC–PHY interface, which
  `EnablePHYIf` = 0 isolates (D Table 64).
* **The refusal control.** `M5-REF`, `phyif all` without the class token: `refused 1`
  (`M5-REF:12`), `n_writes 0` (`:5`), every port `rc 1` — no register read (`:13–17`) — and
  `PCRP` unchanged (`:39–43`). `phyif al` at `:70` is the refused write's echo (`FW-41`).
* **The write.** `M5-PHY:13–18`: `ok 1 stored 5 already 0 refused 1 idfail 0 rbfail 0` (the
  `refused 1` is `M5-REF`'s), each port `pre nn7F0038 rb nn7F0039 rc 0 st 1`; the switch's
  `n_writes 5` (`:6`). The second reader agrees (`M5-VP1:9–13`).
* **The pings after** (both locks restored): host → board 4 of 4 at 46 B and at 84 B
  (`M5-PL:8`, `M5-PD:8`); board → host 4 of 4 (`M5-BP:9`). The host's neighbour entry is
  `REACHABLE` at rlxfw's locally administered address (`M5-NB:1`, compared by script and not
  printed here): the positive discriminator of `R6`'s `D4` kind. Four counters agree each way
  (`M4-VM` → `M5-VM`; `M4-NIC:14–15` → `M5-NIC:14–15`; `M5-HP0:1–2` → `M5-HN:14`, `:23`): host →
  board, host `tx` +14 = port 3 in +14 (13 unicast, 1 broadcast) = the CPU port's output +14 =
  `n_rx` 14; board → host, `n_tx` +14 (6 → 20) = the CPU port's FCS +14 = port 3's unicast output
  +14 = host `rx` +14.
* **The reads after.** `M6-SW`: `psrp3` unchanged (`:27`), `PCRP0`–`4` live `nn7F0039`
  (`:39–43`), `MSCR` `00000001` (`:55`), `ALECR`, `SWTCR0`, `SWTCR1`, `FFCR`, `VCR0` and the `PVCR`s
  unchanged (`:54–65`); `CPUICR` `C4000000` (`M6-VP5:8`). The VLAN and netif tables were not
  re-read after the write, and no L2 or ACL table was read at all.

**The `MSCR` 0x01 condition** (ruling 6; the owner's ruling of 2026-09-26 in the `R6b-8` row). 量:
with `MSCR` `00000001` (no ACL) throughout and the loader's one VLAN and one netif entry, all 14
frames port 3 received were delivered to the CPU. So *that* the loader's tables reach the CPU
without ACL rules is shown. *How* is 未定 and is `SPEC.md` § 17 `NET-37` 殘留's: VLAN 8 has
`extMemberPort` 0 (讀 B), so the CPU is not a member and delivery is not by VLAN membership. The
candidates are L2 learning of `rlx0`'s source address, a netif rule, or an implicit CPU
membership — none read. Arm I's card reads the L2 and netif path.

**`D8` by its letter** (ruling 6). Arm II establishes, on one boot: no vendor Ethernet code in the
image; ping both ways with four-counter agreement; a positive discriminator; and that the NIC and
the seam work and the switch was the stop. The `phyif` before and after is a single-variable
control at register level — only `PCRP0`–`4` bit 0 moved on the switch page (`M2-SW` against
`M6-SW`) — though the refused write, the unlocks, 4.5 minutes and the host's neighbour flush also
came between; it ties the recovered link to the five bits, and the locally administered address
ties the ping to rlxfw's code. **`D8` is not met**: `R6b-8`'s DoD gives it to arm I, 8d's `init` on
its own boots, with arm II as its control. D1–D4 are met in the record (blocks 47, 48 and 50);
the reading's "D1 and D2 open" is a misreading (ruling 6).

The console during the resume did not go quiet; the main session's "89 seconds of silence" was its
own instrument error and is retracted (`notes/nic-driver.md` § 30.6, `FW-152`).

## 16.8 8d's scope, given arm II (ruling 7; 推 throughout, for arm I to test)

* Arm II ran on S0′ plus `PCRP0`–`4 |= EnablePHYIf` and pinged both ways: the loader's VLAN table,
  PVID 8, `VCR0` `1FF`, `MSCR` 1, `TRXRDY` 1 and `PSRP` bit 12 set (`M2-SW`, `M2-VV`).
* **Must be written for arm I on `SWCORE=n`**: of the vendor's values, only `EnablePHYIf`.
* **May stay loader-inherited, for that ping criterion**: `SSIR`; `MSCR` at the owner's `0x01`;
  `QNUMCR`; `EEECR` with PHY registers 17 and 26; `CSCR`, `ALECR`, `TEACR`, `SWTCR0`, `SWTCR1`,
  `DACLRCR`, `FFCR`, `TCR7`, `MEMCR`; every register where L = V.
* **Matter beyond one ping, plausibly**: the VLAN group — the table, `PVCR0`–`4`, `VCR0`, `PBVCR0`,
  the netif table and `PLITIMR` — is either left loader-inherited as a unit or taken over as a unit,
  never partially. § 8.10's `dumb` loss has the partial shape: `restore 0` put PVID 8 under
  ingress filtering over the vendor's vid-8 entry, which decodes as port 4 only, so port 3 would be
  dropped. EEE, which the vendor turns off (link stability with it on is untested), and `QNUMCR`'s
  CPU field are 8d's to decide with their sources.
* **`init` does not `reset`**: a reset inherits all of R's differences — empty tables, PVID 1
  under `VCR0` `1FF`, `EnablePHYIf` clear, `TRXRDY` 0, `MACCR`, `FFCR`, `LEDCREG`, `BMCR` `3100` —
  about ten register groups to take over instead of one.
* The page-4 EEE register cannot be taken over under the pages-0-and-1 limit; `EEECR` can.

## 16.9 The flash claim, the maps, and the record

* **What was sent** (量, `v_sent.py`, whose control catches six planted verbs and passes six clean
  strings): the night's twelve directories, `bench/2026-09-27d/` to `bench/2026-09-28/`, hold 490
  strings sent to the console — every capture's `sent` and every `looprun` rescue step — and none
  is `FLW`, `EW`, `EB`, `DB`, `FLR` or a non-zero `AUTOBURN`. The loader verbs among them: 49 `DW`,
  6 `MDIOR`, 14 `AUTOBURN 0`, 14 `LOADADDR`, 17 `IPCONFIG` and 13 `J`. The memory node took 2
  writes, both to `PCRP3` (§ 16.5), within `cardcheck`'s HW-1 fence; `AUTOBURN` read back
  `00000000` before every upload.
* **The maps**: `A2-MAPH` and `AZ-MAPH` (group A), `Y2-MB0` and `Y6-MB1` (`R6b-10`), `M2-MB0` and
  `M6-MB1` (arm II) and `bench/2026-09-27e/B-MAPH` and `bench/2026-09-27n/B-MAPH` (boots 1 and 10)
  each read the digest `0927be41…`, 31 groups the same and 1 `DIFFER` at `000000`, as blocks 46 to
  51 did; `n_writes` and `n_write_refused` read 0 at every `NW` read, and `n_writes` carries no
  information about writes (`FW-142`). What the brackets cannot see: `H601`'s 8,192 bytes, never
  hashed; two writes that cancel; anything outside the map's windows; the time between a closing
  map and the next opening one, and after the last.
* **The record's deviations**, each already in a `CORRECTIONS` file: group A split over two
  directories (`CORRECTIONS-8c-A.md`); boot 10's late prep at the owner's request inside the
  driver's pre-midnight window, and the off-card `X-ARP1` (`CORRECTIONS-8c-B10.md`); the first
  `y-line1` stopped at its ARP gate and renamed, the off-card `X-ARP2` and `X-ARP3`, `M5-REF`'s
  `--until`, the watch `X-M2`, and the `n-line2b` resume (`CORRECTIONS-A-r6b10-armII.md`). Ruling
  10 records the late prep and the resume as deviations.

## 16.10 What group A and arm II do not establish

* L and V/R are two power-ons, a cold one and one after a watchdog reset; only S0′'s 37 words
  share V's boot.
* R's changes are not split between `FULL_RST` and the clock gate; that the PHY changes are the
  reset's own is 推.
* A PHY page-1 reading in L, and a page-4 reading anywhere.
* MIB offsets beyond 17 counters, some of them tied; a read side effect on a zero-valued word.
* What `ByPassTCRC` means, and what happened to the test frames on the wire.
* How the loader's tables deliver port 3's frames to the CPU (`NET-37` 殘留); that any one of the
  five `EnablePHYIf` bits is necessary; a second boot of arm II; anything about arm I or `D8`.
* The standby failure's cause.
* § 16.8, which is inference for arm I to test.

# 17. 2026-09-28 (`R6b-8` 8d) — 1.5: `init`, typed by the standard `/init`, and `reset` refused while the CPU port's engine runs

8d's desk landing (segment 116). Its scope is ruling 7 of the night
(`$FWRE_WORK/rebuild/s115/read-night/RULINGS-night.md`) and § 16.8; its decisions are the main
session's rulings on 8d (`$FWRE_WORK/rebuild/s116/RULINGS-8d.md`, not in this repository, cited as
8d ruling *n*), which bind this section. Marks: 量 a capture, 讀 code or a document, 推 inferred.

## 17.1 The decisions (8d rulings 1–6)

* **Where `init` lives** (ruling 1): a verb, typed by the standard `/init` (`config/rlxfw-init.sh`)
  between `unlock i-mean-it` and `start` — the image's boot policy, as P2-2's LAN bring-up already
  is. The driver still writes nothing at boot on its own (its header's item 2), every quiet-`/init`
  boot stays what it was, and the switch keeps one guarded write path. The owner's requirement that
  the product not rely on a typed verb is about the operator, not about `/proc`.
* **What it writes** (ruling 2): `EnablePHYIf` on `PCRP0`–`4`, through 1.4's `rtl819x_phyif_port()`,
  and nothing else. No reset: § 16.3's R is not the loader's state, and a reset would leave about
  ten register groups to take over (§ 16.8).
* ~~**The VLAN group is inherited as a unit** (ruling 3)~~ 🔄 superseded 2026-10-08 by the owner's ruling, § 21.3 — the table, `PVCR0`–`4`, `VCR0`, `PBVCR0`,
  the netif table and `PLITIMR`, none written. Arm II pinged both ways on exactly that state plus
  `EnablePHYIf` (`NET-164`); S0′'s 37 words were equal on 13 boots of the catch → upload → `J` path
  (§ 16.1), while the tables were read on one (`M2-VV`, `M2-VN`). A take-over would need a table
  writer and, for the loader's one-VLAN layout, values whose only source is the loader's reads; the
  vendor's layout, which has two sources, is a two-VID design. So the bounded `TACI` writer the
  `R6b-8` row lists is not built — no table write exists for it to bound — and its spec (clear
  `STOP_TLU` on every refusal, read `SWTCR0` back) is the precondition of any future take-over.
* **EEE and `QNUMCR`'s CPU field are inherited** (ruling 4): `EEECR` `294A5294` with PHY registers
  17 and 26 as the loader leaves them, and field 0, with which the loader receives and arm II
  delivered 14 of 14 frames to the CPU (量). Reopened by a link flap or stall on a `SWCORE=n` image,
  and when a second CPU queue is wanted. This is `NET-28` 殘留's "what to write": nothing.
* **`dumb` and `restore` are kept** (ruling 5), unchanged, and `/init` never types them. `dumb`'s §
  8.10 loss is a partial take-over of the VLAN group (§ 16.8); its candidates are not separated and
  no `R6b` step needs them.
* **The reset guard** (ruling 6), § 17.2.

## 17.2 The code

`rtl819x-switch.c` 1.5 appends one block after 1.4's (`:1663`–`:1865`). Above it seven lines changed
in place and none moved (FW-110; 量, `diff` of `HEAD`'s 1,662 lines against the new file's first
1,662: `118c118`, `569c569`, `637c637`, `1592c1592`, `1617c1617`, `1643c1643`, `1661c1661`): the
version string; three formerly blank lines hold prototypes; the reset branch of the switch's handler
calls the guard; 1.4's handler hands the forms it does not take to 1.5 instead of returning
`-EINVAL`; 1.4's page lines end with 1.5's line.

* **`init`** needs the switch's own unlock and nothing else: locked, `-EPERM` before any register is
  read, counted; the phyif class token is neither needed nor enough. Unlocked: the five per-port
  results reset, then ports 0–4 in order, stopping at the first failure — `phyif all`'s loop, so its
  per-port results are the `phyifN` lines and its stores count in the phyif line (only that line's
  `ok` is phyif's own). The mark is `RLXFW-SW-INIT=`, `SW-PHYIF`'s packing: stored ports in bits
  12:8, ports verified set in 4:0.
* **The guard**: `reset full` and `reset vendor` return `-EBUSY`, counted in `reset_busy`, before
  any write — `SSIR` and `SYS_CLK_MAG` untouched, 1.0's reset not entered — while `CPUICR` has
  `TXCMD` or `RXCMD` set. Address and bits: B `rtl865xc_asicregs.h:491`–`:492` and `:527`–`:528`; 量
  `C4000000` with rlxfw's NIC armed (`bench/2026-09-28/M6-VP5.log:8`, a `peek`; `AN-N2.log:6`,
  `RLXFW-N-ENGON`) and `04000000` after `disarm` (`AR-NIC.log:49`, `AR-C0.log:8`). The test is the
  two bits and not the word: bit 26 stays set after `disarm`. It is a direct KSEG1 load outside the
  switch window, as `SYS_CLK_MAG`'s are, and a check at one instant, not a lock: the NIC's recovery
  timer runs in softirq while the NIC is armed, so the state it protects is the one `disarm` leaves.
* **The page** gains one line before the register table,
  `init calls C ok K refused R rc D stored SS on OO reset_busy B`, from cached values (a `cat` reads
  no register for it): 108 bytes at its widest, so 1.4's worst case of 2,483 of 4,096 becomes 2,591
  (量 on the host: `mdiocheck` K46, and a whole-driver host render).
* **`/init`** types `echo init > /proc/rtl819x-switch` between the unlock and `start`, with the
  reason beside it; the rung-1 line and the quiet `/init` are unchanged, and
  `config/rlxfw-initramfs.tsv`'s note for `/init` names `init`.

What a standard boot now does (推, from the code; arm I reads it): on `SWCORE=n`, five stores,
`n_writes` 1 → 6 after the boot, and one mark line, `RLXFW-SW-INIT=00001F1F`; on `SWCORE=y`, no
store and `RLXFW-SW-INIT=0000001F`.

## 17.3 What the desk measured

* `mdiocheck`, 38 cases and 32 mutants before: **48 cases and 49 mutants, each mutant killed by the
  case named for it** (K37–K46, M33–M49), the unmutated run first; `tools/ci-expected.tsv` 71 → 98
  lines. K37–K46: `init` refused while locked with no register read; the post-`J` and vendor-set
  states, access by access; a stop at an identity failure and at a read-back failure; the phyif
  token neither needed nor enough over four lock states; ten malformed forms; the guard refusing on
  `TXCMD`, `RXCMD` and `C4000000` with no store and no reset, and permitting at `04000000` and at 0;
  the line's 108 bytes against the running total. The main session re-ran it
  (`$FWRE_WORK/rebuild/s116/verify-sw15.sh`): rc 0, 48 and 49.
* `mkinitramfs self-test` 43, `test-mkinitramfs-mutants` 27 and `sh -n` on the new `/init`: rc 0.
  `bootbytes` 7 of 7; its `predict` lists `SW-INIT` at 24 bytes.

## 17.4 What 1.5 does not establish

* Anything on the silicon: that five stores bring the LAN up on a boot arm II did not run is arm
  I's.
* That the guard covers every path to a running engine: it is one load, and `start`, `dumb` and
  `restore` are not guarded.
* That `mdiocheck` drives the driver's reset branch: it is transcribed into the harness from
  `:636`–`:640`, as the read and write paths above the cut are; the in-place lines outside the cut
  were compiled by a whole-driver host build, and by the target's compiler only when an image is
  built.
* Anything about the VLAN group on a boot path on which the loader has not brought its network up
  (autoboot from flash), which `R9`'s zero-write rule keeps unreachable. 🔄 `R8b` made it reachable; measured in § 20 and § 21.1.

## 17.5 rtl819x-view 1.1: tbl l2 and 13 more words

8d ruling 7 asks for `rtl819x-view` 1.1, so that arm I can read on an image with no vendor node:
`tbl l2`, the L2 table read by the existing table protocol, printing only slots whose words are not
all zero, under a page budget, with a count line (ruling 6 of the night gave arm I's card the L2
path, § 16.7); and `peek` admitting the 13 words § 16.4 lists as having B and 量, with `0x4D48` still
refused. The file is `config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-view.c`, 709 → 994 lines,
sha256 `68ec4f21…` → `03109a3c…`; the main session accepted it as written. Marks as in § 17; 量 on
the host is a desk tool's measurement. `SPEC.md` `FW-156`.

**The thirteen words.** Each has B (the header the build compiles, `rtl865xc_asicregs.h`, sha256
`e29c3051…`; the addresses compiled from it with the build's defines,
`-D CONFIG_RTL_8196E -D CONFIG_RTL_819X`, not added up by hand) and 量, a loader `DW` reading of this
die in 8c-cells group A's L column (`bench/2026-09-27d/`, the cold prompt of 2026-09-27), each line
re-read to carry its word; D places none. `NAME:N wK` is word K on line N of `NAME.log`, counted on
LF with CR stripped:

* `CSCR` `0xBB804048`, B `:1015`; `AL-D04:2` w2, `00000008`.
* `EEECR` `0xBB804160`, B `:1365`; `AL-D07:2` w4, `294A5294`.
* `SBFCTR`/`SBFCR0` `0xBB804500` (one address, two names), B `:1673`–`:1674`; `AL-D11:2` w1,
  `000000F4` — the word 1.0 refused (§ 12.3).
* `IBCR0`–`2` `0xBB804704`–`0xBB80470C`, B `:1831`–`:1833`; `AL-D12:2` w2–w4, 0.
* `QNUMCR` `0xBB804754`, B `:1850`; `AL-D13:2` w2, `00001249`.
* `WFQRCRP0`–`5` `0xBB8048B0` + 12p (`PSCR` + `0x0B0`; `PSCR` is B `:2159`), B `:2202`, `:2205`,
  `:2208`, `:2211`, `:2214`, `:2217`; `AL-D14:2–5`, the dump's words 1, 4, 7, 10, 13 and 16:
  `00003FFF` for P0–P4, 0 for P5.

Refused beside them: `0x4D48` (`AL-D17:2` w4, `BB060100`; no name in B's live branch, none in D) and
`WFQRCRP6` (`0xBB8048F8`, B `:2220`; `AL-D14`'s sixteen words end at `0xBB8048EC`, so it was never
read). The thirteen are a second run table at the end of the file, `rtl819x_view_runs11[]`, each row
citing its B lines and its capture; `rtl819x_view_admit` consults it through its last `return`,
after the `PSRP` test, and `rtl819x_view_nadmit` adds it to its sum: `admit 311`. All thirteen were
also read on the V and R boots of 2026-09-28, through the vendor's memory node (§ 16.2).

**The L2 table** (讀; every file cited here is byte-identical, `cmp`, between `r6b8cr`'s staged tree
and `src-vendor/rtl819x-toolchain/linux-2.6.30`):

* Type 0, `TYPE_L2_SWITCH_TABLE` (`rtl865x_asicBasic.h:28`); the window is `REAL_SWTBL_BASE` (B
  `:151`) + (0 << 16), `0xBB000000`–`0xBB007FFF`.
* 1,024 slots: `RTL8651_L2TBL_ROW` 256 × `RTL8651_L2TBL_COLUMN` 4 (B `:2587`–`:2588`, under no
  `#if`). D gives the count too — "a 1024-entry address look-up table with a 10-bit 4-way XOR
  hashing algorithm" (its § 1) and "Internal 1024 entry 4-way hash L2 look-up table" (its § 2) — so
  the count has two sources.
* Slot = row << 2 | column. The vendor's own L2 read path, `rtl8651_getAsicL2Table`
  (`rtl865x_asicL2.c:803-837`), bounds row < 256 and column < 4 (`:806`) and calls
  `_rtl8651_readAsicEntry(TYPE_L2_SWITCH_TABLE, row<<2 | column, &entry)` (`:810`), the reader 1.0's
  `tbl` copies (§ 12.4). Its `rtl865x_accessAsicTable` (`96E/rtl865x_asicBasic.S:531-617`) lets type
  0 through whatever the ASIC function word holds, as it does 4 and 6: bit 0 is in none of `0xe22`,
  `0x8` and `0x4000`.
* 32 bytes a slot: the reader's `sll $2,$18,5` (`:1084`). For type 0 it copies out two words
  (`_rtl8651_asicTableSize`, `:185`), the entry's words 0–1 (`rtl865x_asicL2.h:140-190`; words 2–7
  are reserved), and it loads and compares all eight, as `tbl l2` does.
* `AsicDriver/Makefile` builds `96E/rtl865x_asicBasic.o` and `rtl865x_asicL2.o` when
  `CONFIG_RTL_8196E` is set: the files are in the tree that builds.

量: none. No committed capture has loaded an address in the window (a `git grep` of `bench/` for a
`DW` or a memory-node read of `0xBB000000`–`0xBB007FFF` finds none), and `SWTAA` has never read an
address in it (`BB060100`, `BB040020` and 0 in § 16.2). Type 0 rests on B's enum, whose 4 and 6
`SWTAA` places (§ 12.4); the first `tbl l2` on the die is its reading (推 until then).

**The verb and the page.** `tbl l2` reads all 1,024 slots by 1.0's protocol unchanged — per slot,
`SWTACR` polled to the same 10,000-poll bound with `udelay(1)` between, then up to ten double reads
of the eight words, the second buffer kept — in a helper of its own, because 1.0's `tbl` caches
every slot and 1,024 do not fit. It keeps the first 40 slots whose second buffer is not all zero, in
slot order, and counts the rest. It loads `SWTACR` and the table's words, nothing else, and stores
nothing; a `cat` still loads nothing. After the five header lines:

```
tbl l2 base BB000000 slots 1024 words 8 polls P read R nz N shown S mis M
sNNNN tK eq|mis  the eight words of the second buffer, per kept slot
busy sNNNN       only after -EBUSY, the slot it stopped at
```

`read` is the slots read (1,024 unless `-EBUSY`), `nz` those not all zero, `shown` the slot lines
(`nz` or 40, the smaller), and `mis` the slots whose ten tries all disagreed, shown or not: a torn
slot whose second buffer is zero is counted there and printed nowhere. The filter judges the buffer
the page prints.

**The page's arithmetic** (量 on the host: `viewcheck` V14 measures every term and reads them out of
the driver's comments). At 1.0's widths — every counter at its type's widest; `shown`, the slot
number and `t` at their bounds — the count line is 111 B, a slot line 86 (`s1023 t10 mis` and eight
words) and the busy line 11, so the result is at most 111 + 40 × 86 + 11 = 3,562 B and the page at
most 193 + 3,562 + 19 = 3,774 B: under the 3,900-byte budget, which therefore cannot fire, and under
4,096. The widest real `tbl l2` page is 3,771 B (`last l2` is 3 bytes shorter than `last netif`). 41
kept slots would still fit (3,860 B); 40 is a round number with room. `mib`'s result stays 2,231 B.

**Time, and IRQs.** IRQs stay on, as in 1.0's `tbl`: nothing in the verb masks them. It never
sleeps, so on this UP, `PREEMPT_NONE` kernel no other process runs until it returns; interrupts and
timers do. With `SWTACR` idle and no tear it makes 1,024 × 17 = 17,408 loads (a guess: milliseconds;
no time per load on this bus is on record). At the worst the bound allows — `SWTACR` busy for 10,000
polls at every slot, and ten tries each — it spends 1,024 × 10,000 µs = 10.24 s in `udelay` alone
and makes 1,024 × 10,161 = 10,404,864 loads. Nothing on a `SWCORE=n` image issues a table command
(rlxfw issues none), so that case needs the vendor's driver (推); the six `tbl` pages committed so
far read `polls` equal to their slots, 72 slot reads with `SWTACR` never busy (`bench/2026-09-28/`:
`AV-TV`, `AR-TV`, `M2-VV`, `AV-TN`, `AR-TN`, `M2-VN`). The standard `/init` names no watchdog (讀).

**The name.** `rtl819x_view_lname[5]` is `"tbl l2" + 4`: `l2`, printed from inside the verb's own
literal. `/proc/rtl865x/l2` is one of the vendor's 42 `/proc` names (`rtl865x_proc_debug.c`, parsed
as `tools/imgprocs.py` parses it), which `imgprocs` looks for in an image as NUL-bounded literals
and `ethcensus population` derives its shared set from; a bare `"l2"` in `rtl819x-view.o` would read
there as the vendor's, as `vlan` and `netif` did (§ 12.7). `ethcensus check`, arm I's gate, reads
only its fixture's six vendor-unique names and is untouched either way. `viewcheck` V0 refuses a
bare `"l2"` in the driver's code (M40 is its mutant). The prediction for arm I's build (推 until it
is built): `imgprocs` on the flat image reads `l2` ABSENT. If it reads PRESENT, rsdk gcc 3.4.6
emitted the literal anyway, and the answer is an `OWN_LITERALS` row for `l2`, measured on that
build.

**FW-110.** No line of 1.0 moved (量, `$FWRE_WORK/rebuild/s116/view11/fw110.py`, whose control is a
planted insertion): `git diff -U0` has 27 hunks, 26 replacing N lines with N at the same numbers and
one appending after line 709; 669 of the 709 lines are HEAD's and 40 changed in place — the version,
the `#error` text, the comments that state a count or a list, `lname`'s sixth name, three hooks
(`rtl819x_view_admit`'s last `return`, `rtl819x_view_nadmit`'s sum and the write handler's `tbl`
branch) and five formerly blank lines, four holding prototypes and `:622` the render hook — and none
outside a hunk. citecheck's own `CITE_RX` finds no citation of `rtl819x-view.c:NNN` in the 14,935
tracked files; a planted one is found.

**The host tools** (量 on the host; each unmutated run first, green before its mutants counted):

* `tools/viewcheck.py`: the model holds 311 words (§ 16.4's 13 written again in the tool, not read
  from the driver) and the L2 table's 1,024 slots of 8 words, zero unless a script sets a slot's
  words, tearable on either buffer. V0–V23, 24 cases: V18 an all-zero table (17,408 loads in slot
  order, no slot line); V19 five non-zero slots among zeros, in order, their exact words; V20 the
  cap at 40, 41 and 100 non-zero slots; V21 `SWTACR` past the bound at slot 700, at the bound, and a
  refusal at slot 0 between `tbl l2`, `mib`, `tbl vlan` and `tbl l2`, where the four resets at the
  top of the verb show; V22 tears on either buffer, a zero slot torn on the first counted in `mis`
  and not shown; V23 each of the 13 permitted beside a refused neighbour, `0x4D48` and `WFQRCRP6`
  refused, the three IBCRs permitted as one span and three spans refused whole. M0 and M1–M44, each
  killed by the case named for it; M23–M25 now anchor on 1.0's three resets together, since `tbl l2`
  repeats two of those lines. 69 lines, 44 before (`tools/ci-expected.tsv`); the whole run took 27 s
  at the desk, 10 s before.
* `tools/viewdecode.py`: decodes 1.1 pages and still 1.0's; the version line picks `admit` 298 or
  311, the `last` names and the word set. An L2 slot is decoded from B's entry
  (`rtl865x_asicL2.h:140-190`): word 0 is `mac39_24` (31:16) and `mac23_8` (15:0); word 1 is
  `reserv0` (31:26), `auth` (25), `fid` (24:23), `nxtHostFlag` (22), `srcBlock` (21), `agingTime`
  (20:19), `isStatic` (18), `toCPU` (17), `extMemberPort` (16:14), `memberPort` (13:8) and
  `mac47_40` (7:0). B's two arms, big-endian `:141-157` and little-endian `:159-176`, put every
  field at the same bits of its word (讀), so the decode does not rest on which arm the build takes —
  one document agreeing with itself, not a second source. The MAC is assembled as the getter does
  (`rtl865x_asicL2.c:815-820`): the sixth octet is the row (slot >> 2) XOR the other five XOR
  `fidHashTable[fid]` (`:22`, `00 0F F0 FF`); the getter skips an entry whose `agingTime` is 0 and
  which is not static (`:813-814`) and gives its age as `agingTime` × 150 s (`:832`). 24 cases (C3:
  five slots whose words and decode were written by hand, every `fid` and every flag; E13: 25
  `tbl l2` refusals), M0 and M1–M16, each killed by the case named for it: 41 lines, 33 before; the
  whole run took 278 s at the desk, 148 s before. HEAD's decoder and this one give the same verdict
  on the 65 committed captures holding a view page (all 1.0), and a planted `admit 297` is refused
  by both.

**What 1.1 does not establish.**

* Anything on the silicon: not one line of 1.1 has run, and rsdk gcc 3.4.6 has not compiled it; the
  image build does that.
* That `0xBB000000` holds the L2 table: no reading has touched the window. The read that settles it
  is arm I's: compare by script, never printing, whether the host's MAC decodes at the row its hash
  names — one comparison that checks the window, the field layout and the hash together.
* The decoded fields beyond B: the layout, `fidHashTable` and the 150-second age step have one
  source.
* That the thirteen words have no read side effect (推: none is known), how long a `tbl l2` takes on
  the die, and whether an L2 slot tears there.
* That rsdk gcc 3.4.6 emits no NUL-bounded `l2` for `"tbl l2" + 4`: `imgprocs` on arm I's image
  answers.
* That a `tbl l2` capture may be committed as it stands. Its raw words carry the MAC of every
  station the switch has learned — possibly the loader's own address, which may be `H601`'s (not
  checked here) — split across word 0 (octets 1–4) and word 1's low byte (octet 0). The sixth octet
  is not stored, but it is the row XOR the other five XOR `fidHashTable[fid]`, so the slot number on
  the same line gives it back. `tools/audit-bench-log.py`'s MAC patterns do not match that raw form;
  they do match `viewdecode`'s output, which prints whole MACs. Whether such a capture is committed
  as it is (as the netif page `M2-VN`, whose words also carry a MAC, was) and what `flashwin scan`
  must see first are the owner's to decide.

## 17.6 Arm I on `r6b8i`: `D8` met (`NET-167`)

Arm I ran on one power cycle, 2026-09-28 17:15–17:25, into `bench/2026-09-28b/` (committed at
`1fbd719`, with the sheet `RUN-armI.md` and `CORRECTIONS-armI.md` beside the captures): the owner's
cold power-on, caught; boot 1; `busybox reboot -f` and a catch; boot 2; the tail on boot 2 (§ 17.7);
`busybox reboot -f` to the loader prompt for the owner's power-off. Every number below was re-read
from its capture by scripts that share no code with the sheet's verdict (`armI-verdict.py`), with
`armI-nb.py` or with `viewdecode`'s verdict paths (`$FWRE_WORK/rebuild/s116/read-armI/scripts/`;
each refuses when a planted defect does not turn it red, and `r7_mib.py` reads
`tools/viewdecode.py`'s own rendering of the MIB words). The main session's rulings on that reading
(`$FWRE_WORK/rebuild/s116/RULINGS-armI.md`, cited as arm I ruling *n*) bind this record. Capture
names are `bench/2026-09-28b/`'s unless marked; `NAME:N` is line N of `NAME.log`, counted on LF with
CR stripped. Marks: 量 a capture, 讀 code or a document, 推 inferred.

* **The image** (讀 the build's records; 8d ruling 8). `r6b8i`: `CONFIG_RTL_819X_SWCORE=n`,
  `rtl819x-switch` 1.5, `rtl819x-view` 1.1, `rtl819x-nic` 1.6 at its default, the standard `/init`
  typing `init` between `unlock i-mean-it` and `start`; recipe `3685a3a4`
  (`$FWRE_WORK/rebuild/r3-4/out/r6b8i.manifest`); `nfjrom` 1,114,112 bytes, which `looprun` pinned
  by digest before the port opened (`I1Q:1`, `I4Q:1`). `ethcensus` is GREEN on it — 0 of 610
  in-scope leaves linked, only the 10 seam names, 0 of 6 vendor-unique `/proc` names — and RED on
  its control `r6b10y`: 22 of 632 leaves, 898 of 899 names, 6 of 6 (量 on the host,
  `$FWRE_WORK/rebuild/s116/build/gates/ethcensus-r6b8i.out` and `ethcensus-r6b10y.out`). On the die,
  `/proc/rtl865x` is absent (`I3-DEV:21`, `I6-DEV:21`) and neither boot prints a vendor probe line
  (`I1-VT:1`, `I4-VT:1`: 0).
* **The two boots** (量). Boot 1 is cold — the catch's one-space line (`I1-CATCH:5`), no watchdog
  line — with `J 80500000` at 17:15:58 and `rlxfw: lan up, rlx0 10.1.1.3` inside the 10.05-s boot
  capture (`I1Q-boot:96`). Boot 2 follows `busybox reboot -f`, caught after
  `Reboot Result from Watchdog Timeout!` (`I4-RB:8`), with `J` at 17:22:29 and `lan up` at
  `I4Q-boot:96`. Each boot capture is 1,830 bytes, and `looprun` closed on each with every assertion
  held (`I1Q.stages.tsv:19`, `I4Q.stages.tsv:19`); `bootbytes` reads both at the non-mark constant
  407, arm II's 339 plus the standard `/init`'s 68 bytes (§ 17.9).
* **Ruling 9, re-derived** (量; arm I ruling 1): 7 of 7 conjuncts on each boot. (1)
  `RLXFW-ID0=3685A3A4` (`I1Q-boot:8`, `I4Q-boot:8`) is the manifest's `recipe_id`, and the `/proc`
  route agrees (`I3-NW0:51`, `I6-NW1:51`). (2) `/init` reached `lan up` (`:96` of each boot
  capture), and the capture's only send is `J 80500000` (its `.meta.json`'s `sent`, which `sent_hex`
  repeats). (3) The first command after `J` is `cat /proc/rtl819x-switch` (`I2-SW`, `I5-SW`), whose
  `init` line reads `init calls 1 ok 1 refused 0 rc 0 stored 1F on 1F reset_busy 0` (`I2-SW:18`,
  `I5-SW:18`), each port `pre nn7F0038 rb nn7F0039 rc 0 st 1` (`:13–17`), the phyif line
  `stored 5 already 0` and `rbfail 0` (`:12`), `n_writes 6` (`:5`), and the boot printed
  `RLXFW-SW-INIT=00001F1F` before `RLXFW-SW-START` (`I1Q-boot:87–88`, `I4Q-boot:87–88`). (4) Host →
  board 4 of 4 at 18(46) B (`I2-PL:8`, `I5-PL:8`). (5) 4 of 4 at 56(84) B (`I2-PD:8`, `I5-PD:8`).
  (6) Board → host 4 of 4, seq 0–3 (`I2-BP:9`, `I5-BP:9`). (7) The host's entry `REACHABLE` at
  rlxfw's locally administered address (`I2-NB:1`, `I5-NB:1`: `lladdr=rlxfw-laa`), the state read
  again by a second command (`I2-HN:46`, `I5-HN:46`).
* **The counts each way, the pass bracket** (量). Host tx +14 = `n_rx` +14, and `n_tx` +14 = host rx
  +14, on both boots: boot 1 host rx/tx 2183/2188 (`I2-HP0:1–2`) → 2197/2202 (`I2-HN:14`, `:23`),
  `n_tx`/`n_rx` 0/2 (`I2-NIC0:14–15`) → 14/16 (`I2-NIC1:14–15`); boot 2 4393/4402 → 4407/4416 and
  0/0 → 14/14 at the same lines of `I5-`. The host's ICMP moved by 8 echo requests, 8 replies, 4
  requests from the board and 4 replies to it (`I2-HP0:4` → `I2-HN:28`), and the board's own
  counters read 8, 8, 4, 4 (`I2-SN:5`, `I5-SN:5`).
* **The address half of conjunct 7 has one reader** (arm I ruling 1): `armI-nb.py`, whose self-test
  read 9 of 9 before power (`I0-ST:10`). By design no capture holds the address, and the host's
  table held no entry for 10.1.1.3 when the reading was done, so no second reader can compare it
  after the fact. What the reader re-derived is the comparand: the six bytes of `rtl819x-nic.c`'s
  `nic_mac[6]`, as `notes/nic-driver.md` describes them, are in the vmlinux whose sha256 the image
  record names (three occurrences; 讀 on the binary); the address is locally administered and
  unicast, and it is neither the host adapter's nor the loader's.
* **What reached the console between `J` and the pings** (量, every capture's `.meta.json`). Boot 1:
  `J`; then `X-I1`, the watch line 1 started when it stopped at `I1-MK` (correction 1) — an ESC
  stream for 142.8 s (its write count is not recorded; the shell echoed 6,643 BEL bytes) and one CR,
  which the shell answered with a bare prompt (`X-I1:2`); then 79.0 s with no capture on the port;
  then `cat /proc/rtl819x-switch`, `cat /proc/rtl819x-nic-tx` and `cat /proc/rtl819x-nic` (`I2-SW`,
  `I2-TX`, `I2-NIC0`) and the ping cell `I2-BP`. Boot 2: `J`, the same three `cat`s and `I5-BP`. No
  send in either window carries a redirect, `echo`, `ifconfig`, `reboot`, `mfgtest` or a loader
  verb, and the NIC reports no 1.5 or 1.6 verb since boot (`I2-TX:4`, `I5-TX:4`:
  `v15 last - 0 ok 0 refused 0`). Boot 1's pings came 3 min 57 s after `J`, boot 2's 15 s after.
* **The switch page against S0′** (量; arm I ruling 2). Before the pings (`I2-SW`, `I5-SW`), after
  them (`I3-SW`, `I6-SW`) and at the tail's start (`I7-SW0`), 5 of the 37 rows differ from slot 0 —
  `PCRP0`–`4`, live `nn7F0039` against S0′ `nn7F0038`, XOR `00000001` each (`I2-SW:40–44`) — and the
  other 32 are equal. S0′ is the same, 37 of 37, on all eight arm I pages, and equals
  `bench/2026-09-28/`'s `M2-SW`, `M6-SW` and `A2-SW`. Live: `MSCR` `00000001` (`I2-SW:56`), `VCR0`
  `000001FF` (`:60`), `VCR1` 0 (`:61`), `PVCR0`–`3` `00080008` (`:62–65`), `PVCR4` 1 (`:66`),
  `PBVCR0` 0 (`:67`), `FFCR` `00000003` (`:59`); the same on `I5-SW` and after the pings. At the
  prompt 13 S0′ rows were also read by `DW`: 7 are equal, and the other six are `PCRP0`–`4` in bit 0
  (`nn7F0039`, `I1-DWP:2–3`, `I4-DWP:2–3`) and `PSRP3` (`000010E0` at the prompt, `000010F9` in S0′;
  § 17.8).
* **The tables against arm II's** (量; 讀 B for the fields). `tbl vlan` and `tbl netif` equal
  `bench/2026-09-28/M2-VV` and `M2-VN` word for word on both boots — 16 slots × 8 words and 8 × 8,
  no word different (`I3-VV`, `I6-VV`, `I3-VN`, `I6-VN`), every slot `t1 eq`, `polls` equal to the
  slots (`I3-VV:7`, `I3-VN:7`). VLAN: slot 8 alone (`I3-VV:16`) — VID 8, fid 0, member and untagged
  ports 0–5, `extMemberPort` and `extEgressUntag` 0 (B `rtl865x_asicCom.h:230`–`:242`). netif: slot
  0 alone (`I3-VN:8`) — valid, VID 8, MTU 1500, `macMask` 7, `enHWRoute` 0, ACL ranges 0–0 (B
  `:171`–`:226`; the address assembled as `rtl8651_getAsicNetInterface` does,
  `rtl865x_asicCom.c:607`–`:612`); its address is locally administered, is not rlxfw's, and is the
  address in the L2 table's slot 600 (§ 17.8).
* **The 13 words** (量; arm I ruling 2; 8d ruling 4). By `peek` on both boots, each admitted
  (`refused 0`, `rc 0`): `QNUMCR` `00001249` (`I3-QN:8`), `CSCR` `00000008` (`I3-CS:8`), `EEECR`
  `294A5294` (`I3-EE:8`), `IBCR0`–`2` 0 (`I3-IB:8–10`), `SBFCTR` `000000F4` (`I3-SB:8`),
  `WFQRCRP0`–`4` `00003FFF` and `P5` 0 (`I3-WQ0:8` to `I3-WQ5:8`), and the same at the same lines of
  `I6-`. 13 of 13 equal group A's L as the loader `DW` captures hold it
  (`bench/2026-09-27d/AL-D04:2`, `AL-D07:2`, `AL-D11:2`, `AL-D12:2`, `AL-D13:2`, `AL-D14:2–5`) and
  as § 16.2 types it.
* **The four-counter bracket** (量; arm I ruling 9; the counter names are `viewdecode`'s, from B, one
  source). Boot 2 (`I6-VM0` → `I6-VM1`, `I6-NIC0` → `I6-NIC1`, `I6-HP0` → `I6-HN`): host → board,
  host tx +13 = port 3 in +13 (12 unicast, 1 broadcast) = the CPU port's out +13 (12, 1) = `n_rx`
  +13; board → host, `n_tx` +13 = the CPU port's FCS count +13 = port 3's unicast out +13 = host rx
  +13; port 3's in and out octets and the CPU port's out octets move by 1,136 each. Boot 1 (`I3-*`)
  reads the same except host tx, +14 (`I3-HP0:2` 2202 → `I3-HN:23` 2216) against 13 at port 3, at
  the CPU port and in `n_rx`. The host's ICMP moved by 12 each way on both boots, so the extra frame
  is not a ping; `rlx0` received one more 70-byte frame between `I3-NIC1` (`nd_stats rx 29/2368`,
  `:42`) and `I3-DEV` (30 packets, 2,438 bytes, `:20`), and the host's bracket closed about 1 s
  after the MIB read and 0.01 s after `I3-NIC1`. 推: the host sent that frame at the bracket's edge
  and it reached the board after the NIC page was read; not separated, for there is no host packet
  capture. The two-counter half of ruling 9 holds on both boots (above).
* **`mfgtest auto`** (量). 9 of 9 ok, 0 FAIL on each boot (`I3-MT:18`, `I6-MT:18`); the nine lines at
  `:9–17` are identical but for `MT-TICK`'s `dj` and `di` (523, 522): `MT-ID` `recipe_id=3685A3A4`;
  `MT-FLASH-1` RDID `1C7016`, matched; `MT-FLASH-2` `n_write_refused=2 n_writes=0`; `MT-FLASH-3`
  `map_rc=0 h601_hashed=0 diff_units=0`; `MT-TICK` `reload=2000=2000`, skew 0; `MT-WDT`
  `wdtcnr_at_probe=A5000000 state=BOOTGUARD`; `MT-PORT`
  `Port3 LinkUp by rtl819x-switch 1.5; vendor tree absent`; `MT-MAC`
  `sig_ok=1 ver=1 len=1166 mac unicast`; `MT-RFCAL` `hw_sum_ok=1 over 1166 body bytes`.
  `mfgtest led` and `mfgtest button`, which need the owner's eye and hand, were not run.
* **The corrections** (`CORRECTIONS-armI.md`; arm I ruling 11: the sheet's defects, not the
  board's). 1: `line1-cold` stopped at `I1-MK`'s first gate on an unfilled `@FILL:RID@` —
  `gen-armI.py`'s `write_all` wrote two scripts' gate arguments unfilled; `I1-MK` itself holds
  `RLXFW-ID0=3685A3A4`, `RLXFW-SM0=C4000000`, `RLXFW-SM1=04000000` and `RLXFW-N1=04000000`
  (`I1-MK:1–3`, `:11`); the line resumed as `line1b` from `I1-VT`, and `line2-warm`'s two
  placeholders were filled with `3685A3A4`. 2: the verdict cells named the template directory and
  refused (`I2-V:1`, `I5-V:1`); the main session ran the same script on the seating's directory by
  hand, PASS 7 of 7 on each boot (`$FWRE_WORK/rebuild/s116/run-armI/run/2026-09-28b/I2-V-hand.out`,
  `I5-V-hand.out`), and the reading above agrees. 3: `stopwatch.sh` did not accept `X-I1b`; its name
  check was widened before `line2` opened the port.

**So `D8` is met** (arm I ruling 1): on its own boots, cold and warm, the `SWCORE=n` image whose
standard `/init` types `init` passes ruling 9 with no verb and no write on the console between `J`
and the pings, the census GREEN on the image. Arm II (`NET-164`, § 16.7) is the control: the same
loader state, the same five `EnablePHYIf` bits, typed by hand. 8d's rulings 2–4 — only `EnablePHYIf`
written; the VLAN group, EEE and `QNUMCR` inherited — hold as measured, not only as designed (arm I
ruling 2).

## 17.7 The reset guard on silicon, and `reset full` from the loader's state (`NET-168`)

Line 3's tail ran on boot 2, after every `D8` cell and every read (`I7-*`, 17:24:36–17:24:46). Marks
as in § 17.6.

* **The premise** (量). `I7-SW0`: `unlocked 1` (`:4`), `n_writes 6` (`:5`), `n_reset 0` (`:8`),
  `reset_busy 0` (`:18`). The engine on, by two instruments: `I7-NIC0` `armed 1`, `engine_on 1`,
  `now_icr C4000000` (`:5`, `:6`, `:49`), and `peek` `C4000000` (`I7-C0:8`: bits 31, 30 and 26 set).
* **Refused** (量; arm I ruling 7). `I7-RF:2` reads `cat: write error: Device or resource busy`; the
  page the same `cat` printed after it reads `n_writes 6` (`:6`), `n_reset 0` (`:9`) and
  `reset_busy 1` (`:19`), and its 37 live rows and eight `psrp` lines all equal `I7-SW0`'s: nothing
  on the switch page moved.
* **Disarmed** (量). `ifconfig rlx0 down ; echo disarm > /proc/rtl819x-nic` printed `RLXFW-N-ENGOFF`,
  `RLXFW-N-NDSTOP`, `RLXFW-N-ENGOFF` and `RLXFW-N-DISARM` (`I7-DN:2–5`); `I7-NIC1` reads `armed 0`,
  `engine_on 0`, `nd_up 0` and `now_icr 04000000` (`:5`, `:6`, `:23`, `:49`), the NIC's `n_writes`
  14 → 21 (`I7-NIC0:10` → `I7-NIC1:10`); `peek` reads `04000000` (`I7-C1:8`: bits 31:30 clear, bit
  26 still set). `CPUICR` `C4000000` → `04000000` by two instruments, the state group A made by hand
  (`bench/2026-09-28/AR-NIC:49`, `AR-C0:8`).
* **Permitted** (量; arm I ruling 7). `I7-RS:2` reads `RLXFW-SW-RST=00000001` and no `write error`
  follows; `n_writes` 6 → 7 (`:6`), `n_reset 1` (`:9`), `reset_busy` still 1 (`:19`). One boot, one
  refusal, one permit.
* **`MEMCR`, `NET-33` 殘留 ②** (量, two instruments; arm I ruling 4). `00007F7F` before (`I7-SW0:53`;
  S0′ the same) and `00007F00` after, by the page (`I7-RS:54`, `I7-SW1:53`) and by `peek`
  (`I7-MEM:8`). `FULL_RST` alone, from the loader's value, clears the low byte; § 16.3's
  `reset vendor` could not show it, having started from `7F00`. What the two bytes mean has no
  source, and no rlxfw write depends on them.
* **`PSRP0`–`4` bits 13:12, `NET-31` 殘留** (量; arm I ruling 5). `01` on all five after `/init`'s
  `init` (`I2-SW:25–29`, `I5-SW:25–29`), before the reset (`I7-SW0:25–29`) and after it
  (`I7-RS:26–30`, `I7-SW1:25–29`): `PortEEEStatus[0]` set and `[1]` clear throughout. Which step of
  the vendor's init clears bit 12 (§ 16.2 V) is not separable on an image without the vendor's code.
  Port 3's link went down with the reset — `PSRP3` `000010F9` → `000010E0`, `up 1` → `up 0` — and
  had not come back by `I7-SW1`, 88 jiffies after `I7-RS`.
* **What moved** (量). Across the reset (`I7-SW0` → `I7-SW1`, live), 16 of the 37 rows: `SSIR` 1 → 0
  (`TRXRDY`); `MACCR` `804A0185` → `80420186`; `MDCIOCR` `96181441` → 0; `PCRP0`–`4` `nn7F0039` →
  `nn7F0038` (`EnablePHYIf`); `PSRP3` `000010F9` → `000010E0`; `MEMCR` `00007F7F` → `00007F00`;
  `FFCR` 3 → 0; `PVCR0`–`3` `00080008` → `00010001`; `SWTAA` `BB060100` → 0. The other 21 did not
  move: `CVIDR`, `MDCIOSR`, `PITCR`, `PCRP5`, `PCRP6`, `PSRP0`, `PSRP5`–`7`, `P0GMIICR`, `TEACR`,
  `ALECR`, `MSCR`, `SWTCR0`, `SWTCR1`, `VCR0`, `VCR1`, `PVCR4`, `PBVCR0`, `SWTACR`, `TCR7`. `I7-RS`
  and `I7-SW1` are equal on all 37.
* **`reset full` from L lands where `reset vendor` from V landed** (量; arm I ruling 8). `I7-SW1`'s
  live column equals `bench/2026-09-28/AR-RST`'s on 37 of 37 words, and its `psrp0`–`4` lines too:
  two boots, two recipes, two starting states. 推: on these 37 words the vendor's 650-ms clock gate
  adds nothing visible, so § 16.3's "not separated" is separated here for these words only. Every
  § 16.3 "not back" item the page shows reappears — `MACCR`, `EnablePHYIf`, `TRXRDY`, `FFCR`, the
  PVIDs, `SWTAA` — and `MDCIOCR` → 0, which § 16.3 did not list, is in both (`AR-RST:31`,
  `I7-SW1:37`).
* **Not read after this reset**: the VLAN, netif and L2 tables, the MIB, `CPUICR`, the PHY
  registers, `LEDCREG`, `0x4D48`, `CSCR`, `EEECR`, `QNUMCR`, `PLITIMR` and `DACLRCR`. Nothing here
  says whether `FULL_RST` from L empties the tables or zeroes the MIB, as `reset vendor` from V did.

## 17.8 How port 3's frames reach the CPU (`NET-37` 殘留), and `NET-30` 殘留 (`NET-169`)

* **The L2 table, first read on the die** (量; 讀 B for the fields; arm I ruling 3).
  `tbl l2 base BB000000 slots 1024 words 8 polls 1024 read 1024 nz 3 shown 3 mis 0` on both boots
  (`I3-VL:7`, `I6-VL:7`); every slot `t1 eq`, words 2–7 zero. Each slot is decoded by B's entry
  (`rtl865x_asicL2.h:140`–`:190`), its address assembled as `rtl8651_getAsicL2Table` does
  (`rtl865x_asicL2.c:815`–`:820`, `fidHashTable` at `:22`) and compared by script — never printed —
  with the host adapter's address, rlxfw's, the address the loader answers ARP with, and broadcast.
* **Slot 1** (row 0, column 1; `I3-VL:8`, `I6-VL:8`): the all-zero address. `isStatic` 1, `toCPU` 1,
  `memberPort` ports 0–2, `extMemberPort` 0, fid 0, `auth` 1, `srcBlock` and `nxtHostFlag` 0,
  `agingTime` 1 on boot 1 and 3 on boot 2.
* **Slot 600** (row 150, column 0; `:9` of each): the netif table's locally administered address
  (§ 17.6) — two of B's layouts decode the same 48 bits — with slot 1's fields. It shares octets 0
  and 5 with the address the loader answers ARP with and differs from it in octets 1–4.
* **Slot 900** (row 225, column 0; `:10` of each): the host adapter's address, learned — `isStatic`
  0, `toCPU` 0, `memberPort` port 3, fid 0, `auth` 0, `agingTime` 2 on boot 1 and 3 on boot 2. Its
  hash for fid 0 (`rtl8651_filterDbIndex`, `rtl865x_asicL2.c:706`–`:711`) names row 225 on both
  boots: § 17.5's settling comparison holds, and with it the window, the field layout and the hash
  (量, 讀 B).
* **Not in the table**, on either boot: rlxfw's locally administered address, the loader's ARP
  address and the broadcast address. No slot rebuilds to any of them, and no slot holds their octets
  0–4 at any row — after `rlx0` had sent 27 frames on each boot (`I3-NIC1:14`, `I6-NIC1:14`). So
  § 16.7's first candidate, "L2 learning of `rlx0`'s source address", is refuted (量).
* **So how** (讀 B, one source; 推; arm I ruling 3). The one field of an L2 entry that sends a frame
  to the CPU is `toCPU` (word 1 bit 17, `rtl865x_asicL2.h:154`), set here only on the two static
  entries, neither of them rlxfw's; VLAN 8's `extMemberPort` is 0; the netif entry holds another
  address and has `enHWRoute` 0. `FFCR` (`0xBB804428`, B `rtl865xc_asicregs.h:1490`) reads
  `00000003` in S0′ and live (`I2-SW:59`), and B names its bit 1 `EnUnkUC2CPU`, "Enable Unknown
  Unicast Packet Trap to CPU port", and its bit 0 `EnUnkMC2CPU`, the multicast one
  (`:1666`–`:1667`). 推: frames to rlxfw's address reach the CPU as unknown unicast through that
  trap, and broadcasts through the multicast one; implicit CPU membership is not excluded, and D was
  not consulted, so the bits' names have one source. The owner's `MSCR` `0x01` condition (§ 16.7) is
  met in substance: the loader's own state delivers to the CPU without ACL rules, by the `FFCR`
  traps (推 on one source). The vendor does it the other way: `FFCR` 9 (§ 16.2 V:
  `IPMltCstCtrl_Enable` and bit 0, B `:1662`, `:1667`; the unknown-unicast trap off) and a static
  `toCPU` L2 entry for its own address and one for broadcast (讀 `rtl865x_fdb.c:93`, `:98`,
  `:559`–`:560`).
* **The price** (推; arm I ruling 3). With `FFCR` inherited, every unknown-unicast and multicast
  frame from any LAN port also reaches the CPU. This bench's one link carries only the host, so
  nothing here measures the load that adds.
* **What would settle it** (arm I ruling 3; the owner may override the ruling). The RX packet
  header's `ph_reason` — its word 2, B `common/mbuf.h:107` — which `rtl819x-nic`'s page does not
  print (it prints words 1, 3 and 4 as `rx_ph1`, `rx_ph3` and `rx_ph4`); or a ruled write clearing
  `FFCR` bit 1, with a unicast ping. A lead, not an answer (讀 B, one source): `rx_ph1` `00400819`
  (`I2-NIC1:135`) decodes to `ph_extPortList` 8, the CPU bit (`mbuf.h:66`, `:77`) — the frame's
  destination list held the CPU, not why. Which member bit the CPU NIC is, `NET-37` 殘留's last
  question, is not answered: VLAN 8 has no CPU bit.
* **`NET-30` 殘留, its own deciding experiment** (量; arm I ruling 6). The host adapter was attached
  before power and not touched (carrier 0 with the board off, `I0-LINK:1`), and `DW BB804134 1` read
  `PSRP3` at the caught prompt before and after `IPCONFIG`, on the cold boot and after
  `busybox reboot -f`: `000010E0` all four times (`I1-PSA:2`, `I1-PSB:2`, `I4-PSA:2`, `I4-PSB:2`) —
  bit 8 (`LinkDownEventFlag`) 0, bit 12 1, bit 4 (`LinkUp`) 0. Port 3 had no link at either read of
  either prompt, and the loader answered ARP 4 of 4 right after (`I1-ARP:8`, `I4-ARP:8`). The same
  reply lines hold `PSRP4`–`6`, `000010E0`, `000000E2` and `0000007A`, and every `DW` of the seating
  got `LDR-07`'s reply — ceil(N/4) lines of four words from the address given, 14 of 14. The kernel
  side: `RLXFW-SW7=00000000` on both boots (`I1Q-boot:36`, `I4Q-boot:36`), `lde0 00` and
  `psrp3 000010F9 up 1 lde 0` (`I2-SW:24`, `:28`; `I5-SW` the same). The row's read after the upload
  is not reachable through `looprun`, which has no stop between S6b and S7, and block 24's latched
  event stays unattributable after the fact.

## 17.9 The flash claim, the maps, and the record

* **What was sent** (量; `r9_flash.py`, whose control catches six planted verbs and passes eight
  clean strings, `AUTOBURN 0` and `DW 8040D4A0 1` among them). `bench/2026-09-28b/` holds 104
  strings sent to the console: 92 captures' `sent` — the sheet's 86 `--send` cells, and `looprun`'s
  S5b, S6b and S7 in each of two rounds; each `sent_hex` agrees with its `sent` — and 12 rescue
  steps. Loader, 30: `DW` 14 (10 the card's, 2 × `DW 8040D4A0 1`, 2 × `DW 80500000 8`), `IPCONFIG`
  4, `AUTOBURN 0` 2, `LOADADDR` 2, `J` 2, and the rescue's three colon forms twice, each answered
  `Unknown command !`. Linux, 74: `cat` 26; `rtl819x-view` verbs 35 (`peek` 25, `tbl` 6, `mib` 4);
  `echo map 0` 2; `reset full` 2; `ifconfig rlx0 down ; echo disarm` 1; the board's `ping` 4;
  `busybox reboot -f` 2; `mfgtest auto` 2. Besides these, 16 ESC streams, each followed by one CR:
  the three catches (`I1-CATCH` 7,445 writes, `I4-RB` 1,021, `IZ-RB` 1,037), the ten prompt `DW`s (1
  to 3 each) and the three watches `X-I1`, `X-I1b` and `X-I2` (counts not recorded; 6,643, 1,660 and
  505 BEL bytes echoed). None is `FLW`, `EW`, `EB`, `DB`, `FLR` or a non-zero `AUTOBURN`; there is
  no `FLR` at all, so no `flrbracket` round.
* **`AUTOBURN` before each upload** (量). `I1Q-ab2:2` and `I4Q-ab2:2` read `00000000` at
  `0x8040D4A0`; each S5b ended before S6 began (`I1Q.stages.tsv:11`, `:13`, and the same lines of
  `I4Q.stages.tsv`); each rescue's `AUTOBURN 0` was answered `AutoBurning=0` (step 2 of
  `I1Q-rescue.json` and `I4Q-rescue.json`).
* **The maps** (量). `I3-M0` (boot 1, after its reads) and `I6-M1` (boot 2, before the tail) each end
  `map_lines 32` (`:52`). The digest re-computed here from each capture's own 34 lines is
  `0927be41…`, the value `I3-MB0:1` and `I6-MB1:1` gated, and the two maps' lines are identical;
  `flashmap compare` reads 31 same and 1 `DIFFER` at `000000` (`:2–3` of each), as every map since
  block 46 has. `I3-NW0` and `I6-NW1`: `n_writes 0` (`:25`), `n_write_refused 2` (`:26`, after
  `mfgtest`'s `MT-FLASH-2`, which reads the same pair, `I3-MT:11`), `h601_hashed 0` (`:36`),
  `map_rc 0` (`:47`), `recipe_id 3685A3A4` (`:51`). What the bracket cannot see: `H601`, two writes
  that cancel, anything outside the map's windows, and the time before `I3-M0` (the prompt cells,
  the upload and boot 1's reads) and after `I6-M1` (the tail and the last reboot).
* **`C-19`** (量; arm I ruling 10). One host kernel-log follower ran from before the attach
  (`I0-DMSG:1`); its console-adapter lines (`USB disconnect`, `cp210x`, `ttyUSB`) count 4 at
  `I0-C19:1`, `I3-C19:1`, `I6-C19:1` and `IZ-C19:1`, all four from the attach, before the run: no
  drop in the seating. Its 41,473 lines (9,352, 27,358, 36,340 and 39,036 at those cells) are 36,447
  WSL 9p `LookupFid` errors, 1,700 `vhci_hcd` `unlink->seqnum` lines and 1,700 `urb->status` lines,
  and 79 `vhci_rx` preemption-warning traces — 53 shapes, none the adapter's. One interval over a
  minute had no capture on the port: 79.0 s between `X-I1` and `I2-SW`, the board in Linux (§ 17.6).
* **The record.** The captures and the sheet are committed (`1fbd719`), with `bootbytes`' row for
  the new constant 407 = 339 + 68 = 778 − 371: `I1Q-boot`'s non-mark lines are arm II's `M1Q-boot`'s
  plus exactly the standard `/init`'s 68 bytes (`lan bring-up` with `RLXFW-SW-UNLOCK` interleaved,
  38, and `lan up`, 30), and `bench/2026-09-23/P1Q-r01-boot`'s (778) minus the vendor NIC driver's
  thirteen boot lines (371). The `tbl l2` pages' raw words carry, with their slot numbers, the host
  adapter's address and the netif's; slot 1's is all-zero. Two of the reader's scripts,
  `r4_words.py` and `r5_tail.py`, first opened their plant file for writing before reading it, so
  `r4`'s first control passed on an empty file; both read first now, `r4` requires the unmutated
  copy to read 13 of 13 before it plants, and every number above comes from the corrected runs.

## 17.10 What arm I does not establish

* The neighbour conjunct's address beyond one reader: no capture holds it, by design, and the host's
  entry was gone by the reading.
* More than one cold and one warm boot, on one seating and one power cycle. S0′'s 37 words now read
  the same on 15 boots of the catch → upload → `J` path (§ 16.1's 13 and these two); the tables were
  read on three (arm II's and these).
* How the frames reach the CPU: the `FFCR` mechanism is 推 on one source (B's bit names; D not
  consulted), implicit CPU membership is not excluded, `ph_reason` was not read, and which member
  bit the CPU NIC is stays open. Why the loader's ARP address is in neither table.
* Anything about a boot path on which the loader has not brought its network up (autoboot from
  flash, which `R9`'s zero-write rule keeps unreachable): the VLAN group, the L2 entries and `FFCR`
  are the loader's. 🔄 `R8b` made it reachable; measured in § 20 and § 21.1.
* The tables, the MIB, `CPUICR` and the PHY registers after `reset full`, and whether `FULL_RST`
  alone empties the tables as `reset vendor` did; what the 650-ms clock gate does to words off the
  switch page.
* The guard beyond one refusal and one permit on one boot: it is a check at one instant, not a lock,
  and `start`, `dumb` and `restore` are not guarded (§ 17.4).
* Which of the five `EnablePHYIf` bits is necessary: only port 3 has a link and a peer.
* Link stability with EEE on beyond these minutes (8d ruling 4), and any length, load or traffic
  beyond these pings, `mfgtest auto` and the reads: no throughput, no second host, no other port.
* That boot 1's one-frame gap is the bracket's edge (推), and what the host's 70-byte frames are.
* What `MEMCR`'s two bytes mean; which vendor step clears `PortEEEStatus`; `NET-30`'s read after the
  upload.
* `mfgtest led` and `mfgtest button`.

# 18. 2026-09-28 (`R6b-8` 8g) — the mainline flip: `quiet` and `loud` build SWCORE=n, `quiet-swcore` keeps y

**Every number in this section is 讀**: read at the desk on 2026-09-28 out of committed files and
build artefacts by an instrument. No image was built from the flipped default and nothing ran on
the device. The scripts and their outputs are `$FWRE_WORK/rebuild/s116/r8g/` (not in this
repository): `v03-corpus.py` is the corpus measurement and `v04-gates.sh` the checks. `SPEC.md`
`FW-157`.

## 18.1 The rulings

The owner's ruling of 2026-09-26 (`PROGRESS.md`, `R6b-8`) kept `SWCORE=n` a variant through 8f and
flips the mainline in 8g, after D1–D4, with the `SWCORE=y` config building from every later tree.
D1–D4 are met (blocks 47, 48 and 50) and arm I met `D8` (§ 17.6). What 8g implements are the main
session's 8g rulings, given in its brief for this step:

1. `quiet` and `loud` both flip to `SWCORE=n`: `loud` is `quiet` plus `CONFIG_PRINTK`, which is
   exactly what `test-config-gates`' E1b asserts.
2. The `SWCORE=y` configuration becomes the named variant `quiet-swcore`, with no rows of its own
   for these symbols, so on every SWCORE symbol its built `.config` is the vendor baseline. 8b's
   name, `quiet-noswcore`, is retired; the records that say it are records and are not edited.
3. `kconfig-delta` takes a variant list, `verb@a,b`, which applies to each listed variant and to no
   other. Every listed name must be declared, and an unknown name, an empty list or a repeated name
   refuses with a reason, never a traceback; the corpus is measured before the change.
4. `tools/rlxfw-kbuild.sh` and `tools/kconfig-delta.py` spell `quiet`, `loud` and `quiet-swcore`,
   and the delta's comment blocks that the flip makes wrong are rewritten, with the reason of its
   `CONFIG_RLXFW_VENDOR_ETH_OPEN` row.
5. `docs/KNOWN-ISSUES.md` gains one entry: `R9`'s controlled variable no longer holds for the
   mainline default.

## 18.2 `kconfig-delta` 1.1: a variant list

`set@quiet,loud` puts a row in each listed image and in no other; a row with no list is in every
image, and one name is a list of one, so every `@loud` row reads as before. `parse_variants` checks
the list on every row whatever variant was asked for, so a malformed list anywhere in the file
refuses every image's check. It refuses in this order, each time naming the list it read: `@` with
nothing after it, an empty name (a stray comma), a name that is not declared, a name given twice.
Nothing is dropped or de-duplicated to make a list pass. `VARIANTS` is `quiet`, `loud`,
`quiet-swcore`, and `RETIRED` maps `quiet-noswcore` to what replaced it: the two names are two
letters apart and mean opposite images, so a refusal of the old one, as `--variant` or as a tag,
names the new ones. A list that names all three variants is not refused; it differs from an
untagged row only when no variant is given (a `--config` build), and no ruling asked for more.

The self-test grows from 24 to 34 controls, each refusal beside a list one edit away that parses.
C25: a `@quiet,loud` row is in each image it lists. C26: it is in no image it does not list, nor
with no variant. C27: the flip's two `.config` shapes, the n one green as `quiet` and the y one
green as `quiet-swcore`. C28: each refused as the other image. C29–C32: an undeclared name, `@`
with an empty list, an empty name, a name given twice. C33: `quiet-noswcore` refused as
`--variant` and as a tag, pointing at `quiet-swcore`. C34: `apply --variant` writes each image's
own input from one list; C17–C20 give no variant, so nothing drove that before.

`tools/test-config-gates.sh` gains D7–D10, which mutate the membership test (the first listed name
only), the undeclared-name refusal, the empty-list refusal and the duplicate refusal; each turns
the control it names red: C25, C29 (and C33), C30, C32. E1c states the flip on the committed delta:
`quiet` and `loud` carry `CONFIG_RTL_819X_SWCORE y -> n`, `quiet-swcore` has no row for it and
reads the untagged rows alone, and `quiet-noswcore` is refused. The suite reads 69 passed and 2
failed of 71 (58 and 2 of 60 before); the two are E5, red at the desk before and after (§ 18.4).
`tools/test-kbuild-cflags.sh` gains V7 (`--variant quiet-swcore` accepted), V8 (`quiet-noswcore`
refused above the stage, rc 3) and V8b (the refusal names what replaced it): 99 of 99, from 96.

`tools/rlxfw-kbuild.sh` keeps its 939 lines, and the seventeen lines that tracked files cite (58,
203, 204, 255, 262, 263, 357, 388, 389, 412, 432–435, 567, 597, 598) are unchanged;
`quiet-noswcore` has a refusal arm of its own. `config/rlxfw-kernel.delta` keeps its 419 lines: the
lines cited elsewhere (2, 82, 89, 138, 174–177) are unchanged, and line 294 is still the
`CONFIG_RLXFW_VENDOR_ETH_OPEN` row. Its `loud` block and its SWCORE block's header are rewritten in
place; the header above the derived rows (its "21") is not made wrong by the flip and is left.

## 18.3 The corpus, measured before the change

`v03-corpus.py` loads `kconfig-delta` 1.0 and 1.1 side by side and compares the rules each reads
from a delta, symbol by symbol, on kind, from, to, mechanism, line and reason.

* **The parser change alone.** 1.1, with the retired name put back into its `VARIANTS` for this
  measurement only, reads HEAD's delta exactly as 1.0 does for `quiet`, `loud`, `quiet-noswcore`
  and no variant: 104, 106, 145 and 104 rules.
* **The flip.** 1.1 on the new delta against 1.0 on HEAD's: `quiet` 145 rules (75 set, 70
  derived) = HEAD's `quiet-noswcore`; `quiet-swcore` 104 (74, 30) = HEAD's `quiet`; no variant 104
  = HEAD's no variant; `loud` 147 (77, 70) = HEAD's `loud` plus the same forty-one. `loud` minus
  `quiet` is `CONFIG_PRINTK` and `CONFIG_PRINTK_TIME`, and loud's forty derived rows are quiet's.
  Only the two rows whose reasons 8g rewrites, `CONFIG_RLXFW_VENDOR_ETH_OPEN` and
  `CONFIG_RTL_819X_SWCORE`, differ in reason; both are on their old lines.
* **Controls.** Comparisons that must come out unequal do: the new `quiet` against HEAD's `quiet`,
  the new `loud` against HEAD's `loud`, and the reasons compared with nothing skipped. 1.0 refuses
  the new delta, whose list tags it cannot parse.

## 18.4 The checks, each with its control

`kconfig-delta check` on configurations already built under `$FWRE_WORK/rebuild/r3-4/out/`,
against the baseline whose sha256 the delta's header names (`44f781de…`); nothing was built.

| `.config` | checked as | rc | reading |
|---|---|---|---|
| `r6b10n` (`SWCORE=n`) | `quiet` | 0 | 70 derived, 75 set |
| `r6b10y` (`SWCORE=y`) | `quiet-swcore` | 0 | 30 derived, 74 set |
| `r6b10y` | `quiet` | 1 | 41 not applied: the control |
| `r6b10n` | `quiet-swcore` | 1 | 41 undeclared: the control |
| `r6b8bn`, `r6b8by` | the same four | 0, 0, 1, 1 | the same four readings |
| `r6b10y`, `r6b10n` | no variant | 0, 1 | green; 41 undeclared |
| `r6b7L0` (loud, `SWCORE=y`) | `loud` | 1 | 41 not applied; HEAD's 1.0 read it green as `loud` |
| `r6b7L0` | `quiet-swcore` | 1 | 2 undeclared: `CONFIG_PRINTK`, `CONFIG_PRINTK_TIME` |
| `r6b10n` | `loud` | 1 | 2 not applied, the same two |
| `r6b10n` | `quiet-noswcore` | 3 | refused, naming what replaced it |

No loud `.config` with `SWCORE=n` exists, so `loud` is checked in two halves: the SWCORE rows
through quiet's configuration, the PRINTK rows through `r6b7L0`. Under HEAD's 1.0 and delta the
same files read as they did before the flip: `r6b10n` green as `quiet-noswcore`, `r6b10y` green as
`quiet`, `r6b10n` 41 undeclared as `quiet`.

`emueq check` is green, and a planted `set@quiet,loud CONFIG_CPU_HAS_LLSC` row turns it red on E1
(rc 1), so it reads list-tagged rows; `emueq --self-test` passes 19 of 19. A dry run of
`rlxfw-kbuild.sh` takes `quiet`, `loud` and `quiet-swcore` (rc 0) and refuses `quiet-noswcore` and
`quiett` (rc 3), without reaching a vendor binary or staging a cell. The recipe the default builds
from, a digest over `config/`, moves from `3685a3a4` to `8b5ae480`. `test-config-gates`' E5 is red
at the desk before and after, for one reason: a gitignored build product the initramfs declaration
names is missing (`isaprobe/uprobe` in the worktree these ran in, `linkprobe` in the main tree).

## 18.5 The `CONFIG_RLXFW_VENDOR_ETH_OPEN` row stays in every variant

讀 `config/host-compat/0007`: the symbol is declared in `arch/rlx/Kconfig`, outside
`if RTL_819X_SWCORE`, as a `bool` with a prompt, `default y` and no `depends on`, and its one reader
is the guard 0007 puts at the top of `re865x_open()` in `drivers/net/rtl819x/rtl_nic.c`. A search
of the staged `r6b10y` tree finds those two and the generated `autoconf.h` line, nothing else. So
kconfig writes the symbol into every variant's `.config` (`r6b8bn`'s and `r6b10n`'s, `SWCORE=n`,
carry `=y`), while at `SWCORE=n` its reader is not compiled and its value does nothing.

`v04-gates.sh` tried the other two placements. With the row re-tagged `set@quiet-swcore`, `r6b10n`
and `r6b8bn` checked as `quiet` read 1 undeclared, `CONFIG_RLXFW_VENDOR_ETH_OPEN - -> y`, while
`r6b10y` as `quiet-swcore` stays green; with the row deleted, both sides read that 1 undeclared. So
the row stays common. 推: without it `apply` would stop pinning the symbol and `oldconfig` would ask
for it `(NEW)`. Its value matters in `quiet-swcore` alone: `y` keeps the vendor's `eth*` openable,
and `n` there still rebuilds `R6-4` rung 1's control arm. The row's reason now opens with this;
P2-2's text and `R6-4` rung 1's follow whole, the second one's argument for the symbol instead of
`SWCORE=n` marked superseded, since 8b's seam defines the ten names and 8g made `SWCORE=n` the
mainline.

## 18.6 `R9`'s controlled variable (`docs/KNOWN-ISSUES.md`)

The plan's `D16` builds the vendor's `drivers/net/rtl819x/` into rlxfw's kernel so that the network
driver is the same vendor code in both columns of `R9`'s table (`plan/README.md`, gitignored: its
v3 → v4 table, change 3), and `RUNSHEET.md`'s `K6` calls it *D16's controlled variable*. The
mainline default no longer carries it: `--variant quiet`, `tools/looprun.py`'s default, builds an
image whose only Ethernet driver is `rtl819x-nic`. The new entry in `docs/KNOWN-ISSUES.md` says so,
and that `R9` must build from `quiet-swcore`, the variant that still carries the vendor's driver.
Its first wording also said that an `R9` card must bring up the vendor's `eth*` rather than `rlx0`;
that is more than D16 says, and it was cut back to D16's words. The WLAN driver, the plan's other
identical driver, is the same source at `SWCORE=n` and not the same object: 🔄 **量 2026-10-04 its
`built-in.o` loses 11 symbol-table entries and 6 references, not the forty this sentence said —
§ 19.4 is the retraction** — and it is recompiled against a `struct sk_buff` 8 bytes shorter
(§ 19.5; the four declared fields are § 13.7), and five of the ten names the seam defines are its
references (§ 13.3).

## 18.7 The rows re-pointed, and the other files

* **`NET-54` 殘留 ⊘.** Its read set named `asicCounter`'s port 3 and CPU port, and it said the
  mainline would have no port-3 counter after `R6b-8`; that sentence predates `rtl819x-view`'s
  `mib`, which on a `SWCORE=n` image reads both ports' MIB, 量 in arm I's four-counter bracket
  (§ 17.6, `NET-167`). The row now names `mib` and `/proc/rtl819x-switch`'s page as its instruments
  on `SWCORE=n`, and says that the hand-over to `eth4` exists in `quiet-swcore` only. With `R6b`
  closing it is ⊘: since block 46 (`NET-124`) the shape has not recurred in any seating (blocks
  47–51, 8c-cells, arm II, arm I), and the one network failure since was the loader's standby
  failure (`NET-165`), outside Linux. It reopens on the reproduction the row already names.
* **`NET-124` 殘留 ⊘.** Its instruments `/proc/rtl865x/port_status` and `phyReg` are gone at
  `SWCORE=n`; the row now names the `psrp3` line of `/proc/rtl819x-switch` for the link,
  `/proc/rtl819x-mdio` for the PHY (30 of 30 against `phyReg`, `FW-155`) and `mib` for port 3's
  receive counts. ⊘ for the same reason; it reopens on a liveness failure with the host sending and
  the cable untouched.
* **`NET-109` 殘留 and `NET-30` 殘留** were closed on readings taken before any instrument left:
  `NET-109`'s `ByPassTCRC` cell on the vendor-present image in 8c-cells (`NET-163`), `NET-30`'s
  prompt reads in arm I (`NET-169`). There is nothing to re-point.
* **`NET-151`** carries a pointer to `FW-157` where its third-exclusive-name claim and its counts
  (104, 106, 145) are superseded.
* **`tools/bootbytes.py`**: 710 is `quiet-swcore`'s console, the default until 8g, and 339's row is
  named `set@quiet,loud` since 8g. **`tools/ci-expected.tsv`**: `kconfig-delta` 34,
  `test-config-gates` 71 on both of its rows, `test-kbuild-cflags` 99, each with a note.
* **`quiet-noswcore` elsewhere.** Fixed in place where a file states what is current:
  `config/host-compat/0008`'s header, `MK12`'s reason in `config/rlxfw-marks.tsv`, the comment in
  `rlxfw-seam.c` (its line count kept), and the `Kconfig` row of `docs/blind-write-ledger.md`. Left
  as records: `LOG.md`, `bench/2026-09-28/RUN-armII.md`, § 13 of this file (with a pointer in
  § 13.10), `notes/nic-driver.md` § 29.5, and `SPEC.md` `FW-103` and `FW-154` (`NET-150`: a pointer).

## 18.8 What 8g does not establish

* Anything about a `loud` image at `SWCORE=n`: no such `.config` has been built or checked, loud's
  forty derived rows are 推 until the first loud build's `kconfig-delta check` reads them, and
  `bootbytes` declares no constant for such a boot.
* Anything built from the flipped default, or run on the device at recipe `8b5ae480`. `r6b8i`
  (arm I, § 17.6) was built as `quiet-noswcore` at `3685a3a4`: the same rules as the new `quiet`
  (§ 18.3), not the same recipe.
* That a `quiet-swcore` image's `eth*` carries traffic under this kernel, or that `quiet-swcore`
  makes `R9`'s NIC column equal to the vendor firmware's, whose kernel configuration, toolchain and
  userspace still differ.
* Whether a list naming every variant should be refused (§ 18.2).

# 19. 2026-10-04 (`R9-5`) — `quiet-swcore` built, and the controlled variable read off the artefact

**量 unless marked otherwise**, and the measurement is of two ELFs, not of a board: no image ran,
neither arm went through `rtkimage`, no power action was taken, no flash verb and no `FLR` was
issued. The reports, TSVs and asm dumps are `$FWRE_WORK/rebuild/s121/r9-5/` (not in this
repository) with `scripts/` beside them; the three manifests, `vmlinux` ELFs, `System.map`s,
`.config-installed`, `.config-built` and both gate logs per cell are
`$FWRE_WORK/rebuild/r3-4/out/r95{q,y,q2}.*`. `SPEC.md` `FW-202`, `FW-203`, `FW-204`.

## 19.1 The two builds, and the control that makes the comparison mean anything

讀: `quiet-swcore` had never been built. No `quiet-swcore` manifest exists anywhere under
`$FWRE_WORK/rebuild/r3-4/out/`; the three `quiet-noswcore` manifests are 8b's retired name, and
every `--variant quiet` manifest older than 8g names the opposite configuration (§ 18, `FW-157`).
So both arms had to be built. The `quiet` builds already on record carry a different `RECIPE_ID`,
and `RECIPE_ID` is compiled into every object as `-DRLXFW_SRC_ID` (讀 `tools/rlxfw-kbuild.sh`), so
comparing against a stored artefact would have put a changed constant in all 600 objects and made
every one of them differ for a reason that is not `SWCORE`.

Three builds, one at a time, `-j4`, from HEAD's `config/`, which was not touched:

```
bash tools/rlxfw-kbuild.sh r95y  --variant quiet-swcore --marks --jobs 4 \
     --initramfs $FWRE_WORK/rebuild/r3-4/out/r6b8i.initramfs.spec
bash tools/rlxfw-kbuild.sh r95q  --variant quiet        --marks --jobs 4 \
     --initramfs $FWRE_WORK/rebuild/r3-4/out/r6b8i.initramfs.spec
bash tools/rlxfw-kbuild.sh r95q2 --variant quiet        --marks --jobs 4 \
     --initramfs $FWRE_WORK/rebuild/r3-4/out/r6b8i.initramfs.spec
```

| | `r95q` (`quiet`, `SWCORE=n`) | `r95y` (`quiet-swcore`, `SWCORE=y`) |
|---|---|---|
| `recipe_id` / `RLXFW_SRC_ID` | `575da809` | `575da809`, equal |
| `config_sha256` installed | `8c40643b5b1c1160…` | `5220ac6ada98d25f…` |
| `vmlinux` bytes | 4,257,403 | 4,567,218, +309,815 |
| `vmlinux` sha256 | `0d9f837901866a4d…` | `f1eed782cb2c995c…` |
| `cflags_kernel` / `stamp_epoch` | `-fno-if-conversion` / 1788220800 | same / same |
| `host_compat_patches` / `marks` | 9 / 28 | 9 / 28 |
| `(NEW)` lines from `oldconfig` | 0 | 0 |
| `build_rc` / verdict | 0 / green | 0 / green |
| `CC` / `LD` lines in the build log | 600 / 119 | 620 / 126 |

The equal `recipe_id` is the control the whole comparison rests on, and it is checked rather than
assumed: the comparator refuses to report anything when the two differ. The initramfs spec is the
same file in all three builds — `r6b8i`'s, the one arm I used — so it is held, and all three
manifests agree on `initramfs_sha256` and `initramfs_manifest_sha256`. `--variant quiet-noswcore`
was refused with rc 3 before any 480 MB stage was paid for, and `--dry-run` ran for both live names
first.

## 19.2 The `SWCORE` set `S` — two readings, and they are not the same reading

* The `.config` that `kconfig-delta apply` **installs**: the two differ on exactly **1** symbol,
  `CONFIG_RTL_819X_SWCORE`, `# … is not set` against `=y`.
* The `.config` each build **used** (`.config-built`, after `oldconfig` — the file that matters):
  **800** symbols in `r95q` against **840** in `r95y`, differing on exactly **41**. One is
  `CONFIG_RTL_819X_SWCORE`; the other 40 are absent at `SWCORE=n` and present at `SWCORE=y`, which
  is the `dep-unmet` mechanism the delta declares.

`S` is that set of 41. Second source: the delta's `@quiet,loud`-tagged rows number **41** too, and
the two sets are equal in both directions — 0 declared-but-not-realised, 0 realised-but-not-declared.

🔴 **So the 40 in `R9-5`'s own definition of done is a kconfig-symbol count** (量, 840 − 800 = 40),
and § 19.4 is what the ELF level actually loses.

## 19.3 The artefact comparison

Sections, `mips-linux-gnu-readelf -W -S` from the host's `binutils-mips-linux-gnu` and never the
vendor toolchain: **23** sections in each file, **0 added and 0 removed**, 10 identical in size, 13
different. `.bss` 1,371,392 → 2,727,936; `.text` 2,401,772 → 2,605,296; `.strtab` 225,363 →
248,218; `.symtab` 218,608 → 234,704; `.rodata` 120,688 → 130,944; `.iram` 22,084 → 27,852;
`__param` 2,148 → 4,180. `.init.ramfs` is **934,912** bytes in both — the held variable showing as
held. 推: the +1.33 MiB of `.bss` is the vendor switch core's static tables, which is RAM and not
image bytes. These figures are not comparable with the delta header's recorded cost for
`SWCORE=y`: that is the flat image after `rtkimage`/LZMA, and no flat image was built here.

Objects, over the two staged trees: **735** `.o` files against **764**; present only in one tree
**0** against **29**; present in both and byte-identical **591**; present in both and differing
**144**. **173** differences in all, and every one is classified by a rule that names the evidence
it read:

| rule | what it reads | count |
|---|---|---|
| `R1` presence | the `obj-$(CONFIG_X)` / `subdir-$(CONFIG_X)` line on an ancestor of the path | 29 |
| `R2` link product | `cmd_<path> := … ld … -r -o …`, recursed into the inputs | 32 |
| `R3` content | the `include/config/<p>.h` stamps in the object's own `deps_` line, kbuild's own record of what the preprocessor touched | 112 |
| **outside `S`** | | **0** |

Of the 29 presence differences, **28** are under `drivers/net/rtl819x/`, gated by
`obj-$(CONFIG_RTL_819X_SWCORE) += rtl819x/built-in.o` and
`subdir-$(CONFIG_RTL_819X_SWCORE) += rtl819x` in `drivers/net/Makefile` (讀, both lines), and **1**
is `drivers/net/rtk_vlan.o`, gated by `obj-$(CONFIG_RTK_VLAN_SUPPORT) += rtk_vlan.o` in the same
file. Both gate symbols are in `S`.

Symbols, `readelf -W -s` with `nm -f sysv` as a second reader that disagreed on **0** of the
defined names in either file: **13,402** names against **14,387** (`nm --defined-only`: 12,799
against 13,760); only in `quiet-swcore` **985**; only in mainline **0**; different `st_size` 57;
different address 12,629. The 12,629 are link layout — `.text` growing 203,524 bytes relocates
almost everything below it — and they are counted and set aside, not reported as content. All
**1,042** symbol-level differences (985 + 0 + 57) were traced to a defining object and checked
against that object's verdict: **0 of 1,042** has an owner outside the inside-`S` bucket. That is a
second route to the same answer, and the two had to agree or one of them was wrong.

## 19.4 Same source is not the same object, measured in three places

**The WLAN driver.** `drivers/net/wireless/rtl8192cd/built-in.o`, the same bytes as
`rtl8192cd.o`: **816,475** bytes at `SWCORE=n` against **820,910** at `SWCORE=y`, **+4,435**;
defined symbols 2,355 → 2,366, so `SWCORE=n` is missing **11** symbol-table entries and gains 0;
undefined references 59 → 65, so it is missing **6**; **11** symbols present in both have a
different `st_size`; and of the 44 leaf objects in that directory **15** differ while 29 are
byte-identical. The 11 are **four functions** and their section and relocation symbols —
`rtl8192cd_isIgmpV1V2Report`, `rtl8192cd_isMldV1Report`, `rtl8192cd_proc_vlan_read`,
`rtl8192cd_proc_vlan_write`, plus `.text.<each>` and `.rel.text.` for three of them. The six
references are `eth_skb_free_num`, `priv_skb_copy`, `rtk_vlan_support_enable`,
`rtl_add_vlan_info`, `rx_vlan_process` and `tx_vlan_process`.

🔴 **§ 18.6's "forty symbols" is not reproduced and is retracted here.** The measured loss is 11
symbol-table entries and 6 references. 推 that the 40 was § 19.2's kconfig count read as an
ELF-symbol count; the sentence it supported — the WLAN driver is the same source and not the same
object — stands and is now a number instead of an estimate.

**rlxfw's own drivers.** For each of the 13 `.c` files under `config/rlxfw-src/linux-2.6.30/`:
`drivers/net/rtl819x-nic.o` and `drivers/net/rlxfw-seam.o` **differ** across the flip;
`drivers/mtd/devices/rtl819x-spi-write.o` is absent from both trees; and the other **10** —
`rlxfw-devices`, `rlxfw_mark`, `rlxfw-entropy`, `rtl819x-timer`, `rtl819x-gpio`, `rtl819x-keys`,
`rtl819x-spi`, `rtl819x-switch`, `rtl819x-view`, `rtl819x-wdt` — are byte-identical. Both
differences are inside `S`: the NIC driver is compiled against the shorter `sk_buff` in one arm and
the longer one in the other (§ 19.5), and `rlxfw-seam.o` is the file that supplies the ten names
`SWCORE=n` takes away (§ 13.3).

## 19.5 `sk_buff` is 8 bytes shorter, read out of the instruction stream

2.6.30's `skb_init()` calls `kmem_cache_create("skbuff_head_cache", sizeof(struct sk_buff), …)` and
then `kmem_cache_create("skbuff_fclone_cache", (2*sizeof(struct sk_buff)) + sizeof(atomic_t), …)`.
`objdump -d` at `skb_init`'s address in each image's own `System.map`:

```
r95q (SWCORE=n)  802a4c80:  li  a1,192      802a4ca4:  li  a1,388
r95y (SWCORE=y)  802e667c:  li  a1,200      802e66a0:  li  a1,404
```

So `sizeof(struct sk_buff)` is **192** at `SWCORE=n` against **200** at `SWCORE=y`: 8 bytes
shorter, read off the artefact and not out of a header. The second immediate is an internal
cross-check and it closes — 2 × 192 + 4 = 388 and 2 × 200 + 4 = 404.

讀, the mechanism: the three gating symbols are all in `S` — `CONFIG_RTL_HARDWARE_MULTICAST`,
`CONFIG_RTK_VLAN_SUPPORT` and `CONFIG_RTK_VLAN_NEW_FEATURE` are `1` in `r95y`'s `autoconf.h` and
**not defined** in `r95q`'s. That had to be read with a parser for `#define CONFIG_X 1`; the
`.config` parser silently returned `-` for all of them on the first pass, which is an empty reading
and not a negative one. The fields are `srcPort` (`__u16`), `srcVlanId:12`,
`struct vlan_tag tag` (讀 `include/net/rtl/rtk_vlan.h`: a union of `unsigned long` with two
`unsigned short`, so 4 bytes) and `struct vlan_info *src_info` (4 bytes) — 讀 12 bytes of declared
field. **未定**: the 4 bytes between the 12 declared and the 8 measured are 推 alignment padding
reclaimed. Nothing here measures the padding, and the 8 does not depend on it. § 18.6's "four
fields shorter" counts the same declared fields and is left standing; what is corrected there is
the 40.

## 19.6 What the controlled-variable claim becomes

`R9-5`'s definition of done says any difference beyond the `SWCORE` set withdraws
「相同的只有 NIC 與 WiFi 驅動」, and that the WLAN driver counts as a difference regardless. The
measurement gives both halves at once:

* **Nothing outside `S` was found** — 0 of 173 objects and 0 of 1,042 symbols — so the claim is not
  withdrawn on that clause.
* **Both of the two drivers the claim calls *the same* are not the same object.** The WLAN driver
  is § 19.4's 11 entries and 6 references; rlxfw's `rtl819x-nic.o` is a differing object in its own
  right. So the claim survives only in the narrower form the artefact supports: *the vendor's
  switch-core driver and its dependents are the whole of the difference, and the two drivers the
  claim named are inside that difference rather than outside it.* Ten of rlxfw's twelve built
  drivers are byte-identical across the flip, and that is the part of the claim that survives at
  object level.

§ 18.6's sentence is corrected in place to the measured counts, and the three other files that
repeated the 40 — `docs/KNOWN-ISSUES.md`, `docs/threat-model.md` and `docs/hardening-matrix.md` —
with it. Two statements of it are **not** corrected in this commit and are owed: `PROGRESS.md`'s
`R9-5` row, which is where the 40 entered as a definition of done, and the `residual` of
`config/fix-cases.toml`'s `FC-014` / `P1-11`, which is read at render time but not published, so
`docs/differential.md` does not carry it. Both are outside this commit's reach by instruction, and
the dated `LOG.md` entry the retraction needs is owed with them. `config/rlxfw-kernel.delta`'s
comment calls the same 40 *the forty symbols this one decision takes away*, which is § 19.2's
kconfig count and is right as it stands.

## 19.7 The controls, and two readings about the instruments

Every 0 above has a control that can make it non-zero.

| id | what it tests | reading |
|---|---|---|
| `D` | reproducibility: is "144 differing objects" a reading or build noise? `r95q2`, same argv | 🟢 `vmlinux` byte-identical to `r95q` (`0d9f837901866a4d…` both) and **735 of 735** objects identical, 0 differing |
| `C3` | first classifier: with `S` = every symbol, does a difference classify inside? | 🔴 **FAIL, and that is how the first classifier's defect was found** — it read only the cpp dependency record, and an `ld -r` link product has none, so 41 differences sat outside `S` spuriously. The three rules of § 19.3 are the repair |
| `K1`/`K2` | with `S` emptied, does a leaf classify outside? with `S` = everything, inside? | 🟢 `net/core/dev.o` outside, then inside: both buckets are reachable, so "0 outside `S`" is a reading |
| `K4` | the Makefile gate finder, both ways | 🟢 `rtl819x/built-in.o` gated by `CONFIG_RTL_819X_SWCORE`; `net/core/dev.o` by `CONFIG_NET`, which is **not** in `S` |
| `K5`/`K6` | does the link rule recurse, and is the stamp map right? | 🟢 `net/core/built-in.o` has 24 `ld -r` inputs with `skbuff.o` among them; `net/core/.skbuff.o.cmd` carries `include/config/rtl/hardware/multicast.h` and not an invented path |
| `K7`/`C7` | is either side of a comparison empty, or `S` degenerate? | 🟢 591 identical **and** 144 differing; `S` = 41, strictly between 0 and 800 |
| `K8`/`G7` | can "0 lost symbols" and "0 of 1,042 unowned" go non-zero? | 🟢 removing one name from a copy of `r95q`'s own set reads as 1 lost; one planted unowned symbol reads as residue 1 |
| `C1`/`C4`/`C5`/`C6` | one flipped bit, one dropped section, an empty symbol read, two readers disagreeing | 🟢 digest moves; 1 only-in-`q`; 13,402 and 14,387 names rather than 0; 0 disagreements between `nm` and `readelf` |
| `G2`/`G3` | can `kconfig-delta check` go red on these two files? | 🟢 `r95y` read as `quiet` refuses with **41 not applied**; `r95q` read as `quiet-swcore` refuses with **41 undeclared**. The two refusals are the same 41 seen from the two sides, so the variant column is doing work |
| `H4` | can `rlxfw-marks verify` go red? | 🟢 rc 1, "12 mark(s) and 11 witness(es) not a discriminator", on a vendor kernel offered as the image |
| `A7` | does the driver refuse a retired variant? | 🟢 `--variant quiet-noswcore` gives rc 3 before any stage |

`kconfig-delta check` is green on both arms against the `.config` each build used: 30 derived by
kconfig and 74 set by rlxfw for `r95y`, 70 and 75 for `r95q`. `rlxfw-marks verify`, reading each
artefact with both `--absent` vendor kernels, is rc 0 on both with the identical RESULT line — 12
marks present once, 12 witnesses present, 1 witness confirmed absent, absent from 2 vendor
artefacts.

🔴 **A defect in an instrument, found while building its negative control.**
`tools/rlxfw-marks.py verify` returns **rc 0 when handed the wrong `System.map`** — `r95y`'s image
with `r95q`'s map produced the same RESULT line as the correct pairing. So for this declaration its
green certifies the image's bytes and says nothing about the image/map pairing, and a card that
treats a green `verify` as proof that a map belongs to an image is reading more than the tool
measured. Nothing was changed in the tool here. A second reading in the same family, and this one
is the tool being right: run without its two `--absent` inputs, `verify` refuses with rc 1 and
"0 mark(s) and 0 witness(es) not a discriminator", exactly as `tools/rlxfw-marks-absent.tsv`'s own
header says it should; the first standalone invocation of this step made that mistake and the tool
caught it.

A third instrument reading, and it belongs to `SPEC.md` `FW-173` rather than to this gate. Landing
§ 19's rows hit that row's known blind spot again: `spec-check`'s `C3` decides a row is open by a
bare substring, and the open mark's two characters are the first two of the Chinese for
*undefined*, so `未定義引用` — the `UND` entries § 19.4 counts — read as an open value and `C3`
asked § 17 what fills it. The row says `未解析` instead, which is the precedent `FW-173` set and is
no less precise. What is new is the cost of the repair, 量 2026-10-04 by running both regexes over
every `SPEC.md` row the tool itself parses: tightening the mark to reject the `義` that may follow
it moves the open-row count from **67** to **66**, and the single row whose verdict changes is this
commit's own. On the population as it stood before this commit the two regexes agree on every row,
so the repair is verdict-preserving there — which is what an instrument change has to show before
it is accepted. It was not made here: the decision to reword rather than retune is `FW-173`'s and
the owner's, and this is the measurement it did not have.

## 19.8 What `R9-5` does not establish

* **It has not booted.** Neither arm has run on the silicon, neither went through `rtkimage`, and
  no `nfjrom` was built. § 18.8 already said the post-8g default had not booted; `quiet-swcore` has
  not either. Everything above is a desk reading of an ELF.
* **"0 differences outside `S`" is an attribution, not a cause.** Rule `R3` says the object's
  preprocessing *touched* a symbol in `S`, so the flip *can* explain the difference; it does not
  prove the flip *is* the difference. A per-object diff of preprocessed output would be the sharper
  instrument and was not run.
* **The dependency record is kbuild's, so it inherits kbuild's blind spots.** A difference produced
  by something the preprocessor cannot see would be caught only by `R3`'s second leg, the dep-file
  byte comparison, which found nothing — so that leg was never exercised on a real case and is an
  untested path.
* **The 12,629 address differences were set aside, not explained.** If one of them is a content
  difference wearing a relocation's clothes, this comparison did not look.
* **Nothing about code generation.** `hazlint` was not run, and a green `kconfig-delta` and `marks`
  pair passes a `--no-cflags` image with seven load-use violations.
* **`.bss` +1.33 MiB is a file-level reading.** No measurement here says whether a board with that
  configuration boots, or what it does to free memory.
* **Nothing about the vendor firmware.** This compares two rlxfw builds. Whether `quiet-swcore`
  makes `R9`'s NIC column equal to the vendor firmware's is § 18.8's open item still.
* **殘留, and it is not reconciled here**: `R6-4` counted **five** names still undefined after the
  whole `vmlinux` link that come from `drivers/net/wireless/rtl8192cd/`, while § 19.4 counts
  **six** references present only at `SWCORE=y` in that driver's own object. The two populations
  are taken at different stages of the link and are not obviously the same one. Settled by reading
  both sets by name out of the same two trees, which this step did not do.
* **The `rlxfw-marks verify` reading of § 19.7 bounds one declaration**, this one, with 12 marks
  and one absent witness. It does not establish that the map is never a discriminator for some
  other declaration.

---

## 20. 🆕 2026-10-08 (127th segment): booted from flash, the switch is in its reset state and `rlx0` receives nothing

**The finding.** 量 The release image (`RLXFW-ID0=6A11DE02`), booted from flash through
`rlxboot` — the stock loader autobooting, no ESC — brings `rlx0` up with `10.1.1.1` and
receives no frame. Across a three-packet host ping, `rlx0`'s RX and TX stay 0 in `ifconfig`
and in `/proc/net/dev`, and the host's neighbour entry goes `INCOMPLETE` → `FAILED`
(`bench/2026-10-08/X-V06q-*` after a watchdog reset, `X-V08q-*` after a cold power-on).
`/proc/rtl819x-nic` reads `n_rx 0`, `n_irq 0`, `engine_on 1` and `now_icr C4000000`
(`X-V08r-nic`): the CPU port is armed and nothing reaches it. The same image booted from RAM
through the loader's prompt answers the host's ping 2 of 2 (`X-V02n`).

**Which variable it follows.** 量, one or two boots per cell:

| | the loader enters its prompt (ESC); the image from RAM | the loader autoboots; the image from flash |
|---|---|---|
| warm: a watchdog reset, `Reboot Result from Watchdog Timeout!` printed | answers — `V02` then `X-V02n`; `V04` then `X-V04n` and S's 1,109,152 bytes over TCP | deaf — `V06` then `X-V06q` |
| cold: that line absent | answers — `bench/2026-10-07/C03`, then `sendimg` over TCP | deaf — `V08` then `X-V08q` |

It follows the loader's path, not the reset. `notes/nic-driver.md` § 6's wedge, which a cold
power-on cleared, is not this one. 量 Nor was the board being reset while deaf: `X-V08u`
read an uptime of 950.27 s, sixteen minutes after `V08`.

**The register difference.** 量 `X-V08r-sw` (autoboot, cold) against
`bench/2026-10-04/PER-SW` (a RAM boot through the prompt), 37 rows each, 10 differ:

| register | autoboot (live / boot latch) | RAM boot through the prompt |
|---|---|---|
| `SSIR` | `00000001` / `00000000` | `00000001` / `00000001` |
| `MACCR` | `80420186` | `804A0185` |
| `MDCIOCR` | `00000000` | `96181441` |
| `MEMCR` | `00007F00` | `00007F7F` |
| `FFCR` | `00000000` | `00000003` |
| `PVCR0`–`PVCR3` | `00010001` | `00080008` |
| `SWTAA` | `00000000` | `BB060100` |

The autoboot's values are the reset values § 16.8 lists for state R — PVID 1 under `VCR0`
`1FF`, `TRXRDY` 0 at the latch, `MACCR`, `FFCR` — and `SWTAA` 0 says the table-access
address has not been written since reset.

**Why, from two sources.** 量 above, and 讀 `SPEC.md` `LDR-46`: the loader prints
`P0phymode=01, embedded phy` and `---Ethernet init Okay!` only on the path that enters its
prompt. 讀 § 16.8: the mainline (`SWCORE=n`) leaves the VLAN group — the table, `PVCR0`–`4`,
`VCR0`, `PBVCR0`, the netif table and `PLITIMR` — loader-inherited. The case itself was
recorded as open: § 17.4 and § 17.10 list the VLAN group *on a boot path on which the loader
has not brought its network up (autoboot from flash), which `R9`'s zero-write rule keeps
unreachable* among what 1.5 and arm I do not establish. `R8b` made that path reachable, and
nothing re-opened the item: none of `R8b`'s flash boots read the network (each ping in
`bench/2026-10-07` follows a RAM boot). 推 So rlxfw's Ethernet works only
when the loader has configured the switch, which it does only on its prompt path: booted from
flash, a frame from port 3 meets PVID 1 under ingress filtering with no VLAN entry and never
reaches the CPU port.

**What this does not establish.** Which writes are sufficient: § 16.8 says the group is taken
over as a unit, never partially, and that is untested from this state. That `rlxboot` leaves
the switch untouched: its 37 registers read state R, but the ASIC tables are not among them (🔄 § 21.1: they read empty).
Any flash-path value outside the 37 registers: the tables, `QNUMCR`, the PHY registers and
`LEDCREG` were not read (🔄 § 21.1 read the tables, `QNUMCR` and the ALE run). Whether frames reach port 3 at all: no MIB counter was read (🔄 § 21.1: they do, and the switch discards every one).
Anything about the vendor's firmware, whose own driver configures the switch at boot. The
takeover is `R6c`'s (`PROGRESS.md`).

## 21. 🆕 2026-10-08 (128th segment, `R6c`): the flash-booted switch read, the loader's writes checked, and the take-over's write set

`R6c-1` and `R6c-2` at the desk, and seating A (`bench/2026-10-08b/R6C-A-CARD.md`), a read-only
census of the flash-booted state that `R6c-2`'s design asked for before any code. The rulings are
`$FWRE_WORK/rebuild/s128/RULINGS-R6c.md` (not in this repository): the owner's O1 and O2, and the
main session's E1–E4. Marks: 量 a capture, 讀 code or a document, 推 inferred.

### 21.1 Seating A: every frame from the host dies in the switch (`NET-172`)

**The boot, identified.** 量 The board ran S (`6a11de02`), booted from slot B by `rlxboot` after
`bench/2026-10-08/V08`'s cold power-on and judged by `V09`. `A01` read an uptime of 32,997.09 s at
11:56:10; `X-V08u` read 950.27 s at 03:02:03, which predicts 32,997.3 s, so it is the same boot.
`A17` closes the bracket: 161.98 s of uptime across 162 s of wall clock. Read only: no power
action, no loader, zero `FLW`, `EW`, `EB`, `AUTOBURN` and `FLR`, and no PHY read.

**The tables.** 量 VLAN 16 slots, netif 8, L2 1,024: every word zero (`A05`–`A07`). With `SWTAA`
0 and the 37 words at their post-reset values (§ 20), nothing has written a table since reset —
not the loader (`LDR-47`), not `rlxboot`.

**Words read on this path for the first time.** 量 The ALE run `0xBB804400`–`4434` (`A08`):
`MSCR` 1, `SWTCR0` `00080000`, `SWTCR1` `00000200`, `PLITIMR` `07FAC688` — the value after
`reset full` (`bench/2026-09-28b/I7-SW1`), so the take-over's check of it passes — and `FFCR` 0;
the other nine words 0. `QNUMCR` `00041249` (`A09`): the CPU port's field (bits 20:18) is 1, as in
V and R (§ 16.4), where the loader's path leaves `00001249`. 讀 B documents 1–6 as the field's
valid values (`rtl865xc_asicregs.h:1956`–`:2004`), so the loader's 0 is the one outside them.

**Since power-on.** 量 `A10`, a minute after `A01`'s 32,997 s of uptime: port 3 had received 1,579 frames
(232,571 octets; 1,133 multicast, 446 broadcast, no unicast) and had counted every one of them in
`dot1dTpPortInDiscards` and in `etherStatsDropEvents` (`0x62B` each). Ports 0–2, 4, 5 and the CPU
port read zero in every column, and port 3's out columns zero.

**Host → board.** 量 `H11`'s `tcpdump` shows the host sending three ARP requests. Across them
(`A10` → `A12`) port 3 counts 3 broadcast frames of 64 octets (`ifInOctets` +192), and 3 more in
each discard column; the CPU port's counters, `rlx0`'s RX and `n_irq` do not move (`A13`). That is
the card's (a): the frames enter the switch and the switch discards them before the CPU port, by
its own counters. The MIB does not clear on read: `A12` is `A10` plus the delta.

**Board → host.** 量 The board's `ping -c 4` sent six ARP requests (`A16`: `n_xmit` 6, `rlx0` TX
6 frames, 360 bytes, `n_irq` 6). Port 3 counts 6 broadcast frames out (`ifOutOctets` +384), and the
host's `tcpdump` shows all six and its six replies (`H14`). The replies entered port 3 as unicast
and were discarded: +6 in each discard column (`A12` → `A15`). The CPU port counts its six frames in
column 17, `dot3StatsFCSErrors` — § 8.15's artefact. That is (d): a frame the CPU sends reaches the
wire with no VLAN entry and PVID 1, so the take-over is for receiving.

**The link.** 量 The host's adapter reports 100 Mb/s, half duplex. `PSRP3` reads `000010F9` on both
paths (§ 20); `A02`'s `000011F9` carries bit 8, a latched link event (`NET-126`), consistent
with the host adapter's detach and re-attach before the census; `A02` differs from `X-V08r-sw` in
nothing else but `n_reads` and `jiffies`.

**What seating A does not establish.** Which rule discards — ingress filtering, or the lookup of a
VID with no entry — since both are "no VLAN 1"; that the take-over delivers to `rlx0`; the state
after a watchdog reset (this boot is cold); the PHY registers; whether `QNUMCR`'s CPU field
matters, should the take-over deliver to the CPU port and `rlx0` still count nothing.

### 21.2 What the loader writes, and that an autoboot writes none of it (`LDR-47`)

讀 `docs/loader-phy-and-switch.md`'s 2026-10-08 section owns it: the init's 30 writes in program
order, each with A (`stage2.bin`) and a second source (Bb or Bk); its table protocol; and two
censuses by different methods that agree an autoboot stores nothing to the switch, its tables or
the CPU interface. Three of its readings bear on this file. § 8.9's `MACCR |= 0x1000`,
`PITCR |= 0x1` and `P0GMIICR |= 0x40` sit in the `BOND_8196ES` arm and do not run here, and the
`MACCR` write that does run is `0x804033E0`'s (§ 8.9 is corrected in place). The loader writes its
VLAN and netif entries with all eight TCR words and `SWTACR = 3`, consulting no size table, where
the vendor kernel's setters force-add (`9`) three or five words. And the init has two entries —
the ESC line's, and a flash scan that returned zero, which ESC during the scan also causes — and
neither is an autoboot.

### 21.3 The owner's ruling: the loader's layout, taken over as a unit (8d ruling 3 superseded)

The owner, 2026-10-08 (`RULINGS-R6c.md` O1). 8d ruling 3 is superseded: its own reopening
condition is met (`X-V08r-sw`, `PVCR0`–`3` `00010001`), and its premise — that the one-VLAN layout
has one source — no longer holds. 讀 A, the loader's own stores; 讀 Bb, the bootcode ("Set PVID of
all ports to 8", VLAN 8 with `ALL_PORT_MASK` member and untag, `FFCR`'s two traps); 量 every RAM boot
through the prompt. D has no VLAN, ALE or table section (讀 `pdftotext -layout`; the controls `PCRP`
and `MDIO` are found 8 and 38 times, `VLAN`, `PVCR` and `FFCR` none). SDK (Bb) and devmem (量) are
admitted as the two sources, A as a third.

* **Written**: VLAN slot 8 ← `00807E3F 0 0 0 0 0 0 0`, the other fifteen ← zero; netif slots 0–7 ←
  zero (the RAM path's regression decides; the fallback is netif slot 0 with `rlx0`'s own address);
  `PVCR0`–`3` ← `00080008`; `FFCR` ← 3.
* **Verified, never written** — their only source is 量, equal on both paths and written by neither
  the loader nor the bootcode: `PVCR4` 1, `VCR0` `1FF`, `PBVCR0` 0, `PLITIMR` `07FAC688`. A mismatch
  refuses with nothing written, so the group is determined as a unit or left alone.
* **Not touched**: `MACCR`, `MEMCR`, the PHY patch, `QNUMCR`, `LEDCREG`. 量 `MACCR` is then the one
  configuration word of the 37 where the flash path differs from both working states (L = V =
  `804A0185`, F = R = `80420186`, § 16.2), and under F's value seating A saw port 3 receive 1,588
  frames with no FCS or symbol error.

§ 16.8's rule — the group as a unit, never partially — stands. § 17.1's ruling 3 carries a pointer
here.

### 21.4 The code: `rtl819x-switch` 1.6's `vlan` (`R6c-3`, `NET-173`)

讀 A block appended to `config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-switch.c` as 1.6
(ruling E1). 1.5's handler hands it every write none of 1.5's forms took. PID 1 types `vlan`
between `init` and `start` (`src/init/main.c`'s `lan_verbs[]`; `config/rlxfw-init.sh` at the same
place), and a failure is printed and `start` still runs. The driver still writes nothing at boot
on its own, and the quiet `/init` types none of this. The block comment holds every step with its
source; in short:

* **The order.** The switch's own lock, tested before any access (`-EPERM`). On `SWCORE=y`, rc 0
  and nothing read. The four verified words, all read before any is judged (`-EPROTO`, nothing
  else read). Every target read before any store: VLAN slots 0–15 and netif slots 0–7 through
  the table window with `rtl819x-view`'s double read (`-EIO` after ten unequal tries), then
  `PVCR0`–`3` and `FFCR`. A store only where what was read differs from the target — VLAN slots
  ascending, netif slots ascending, `PVCR0`..`3`, `FFCR` — each read back. Then the whole group,
  the four verified words included, read again as a unit (`-EIO`, with `final` and `at`).
* **One table write** (ruling E2), IRQs off for (1)–(10): (1) `SWTACR` bit 0 idle, rlxfw's own
  step; (2) `SWTCR0 |= STOP_TLU`, read back into `tlu` and not required; (3) bit 19 polled;
  (4) idle again; (5) `TCR7`…`TCR0`, all eight words; (6) `SWTAA`; (7) `SWTACR = 9`; (8) polled
  done; (9) on every exit after (2)'s store, bit 18 cleared and read back clear, or `-EIO`;
  (10) `SWTASR` recorded. (11), with IRQs on: the slot's eight words read back and compared.
  Every poll is bounded at 10,000 with `udelay(1)` between them: 推 at most about 40 ms with IRQs
  off, and only on an engine that never answers. The order has two sources, A's table write
  (`LDR-47`) and Bb's `swTable_forceAddEntry` (`swTable.c:76`–`:98`, `:137`–`:156`). The
  command, 9 (force) where the loader uses 3 (add), is B's: `rtl865x_asicCom.c:121`, `:553` and
  `:1124` — the VLAN setter, the netif setter and the table clear — each call
  `_rtl8651_forceAddAsicEntry`, and the VLAN setter indexes by VID, so VID 8 is slot 8.
* **What a standard boot stores** (推, from the code; `R6c-4` reads it). Booted from flash: VLAN
  slot 8 (12 stores), `PVCR0`–`3` and `FFCR` (5), so `n_writes` after the boot goes from 6 to 23.
  Booted through the prompt: netif slot 0 alone (12), 6 to 18. `n_reads` gains 80 + k and 75 + k,
  k the polls of (8), and `ld` reads 784 on either. No mark, so the boot capture does not change.
  The page gains one line of at most 279 bytes: its worst case goes from 2,591 to 2,870 of 4,096
  (3,042 with every narrow field at its type's widest), under the table's budget of 3,600.

**The review** (2026-10-08, the 129th segment; the code is the 128th segment's implementation
agent's). 讀 The main session read the block line by line and checked every address, bit and
enumerator against B (`rtl865xc_asicregs.h`, the TACI, ALE and VLAN definitions and the `PVCR`
fields; `rtl865x_asicCom.h`'s table sizes, 16 VLAN slots on the 8196E and 8 netif; the table
enum in `rtl865x_asicBasic.h`, netif 4 and VLAN 6) and against this driver's own register table;
`00807E3F` against B's VLAN entry (`rtl865x_asicCom.h:230`–`:242`): VID 8, fid 0, member and
untag ports 0–5, no extension port; the step order against Bb and `LDR-47`; that `rtl819x_sw_wr`
refuses before its store, so a store that failed needs no undo; the format's 22 conversions
against its 22 arguments, and the 279 bytes field by field. FW-110 by its own diff: the first
1,865 lines differ in 30, in nine blocks, each N-for-N; `src/init/main.c` loses a comment line
at 545–547 and gains the `vlan` row at 556, so nothing below 556 moves; of 1,174 line citations
by these files' names, only `rtl819x-switch.c:93`–`:97` changed — the header's item 3, rewritten
in place.

**The harness** (`tools/mdiocheck.py`, 98 → 152 run). 讀 It cuts the block unchanged and drives
it over a TACI engine model: a command busy for N `SWTACR` loads or never done, then copied to the
slot `SWTAA` names, the copy corrupted or doubled on demand; `SWTCR0` with bit 19 reading 1 and
bit 18 read/write, or scripted not to set or not to clear; the nine ALE and VLAN registers; the
VLAN and netif tables behind the window; seating A's state and a synthetic netif slot 0 as the
flash and RAM paths; a second compile with `-DCONFIG_RTL_819X_SWCORE`. K47–K67 (21 cases),
M50–M82 (33 mutants). On the host, the main session ran twelve mutants of its own, outside the
repository (`$FWRE_WORK/rebuild/s129/mut.py`), with the unmutated copy green as their control.
Ten were killed. One — (4)'s busy answer skipping the undo, the exit that would leave
`STOP_TLU` set and so stop every lookup — passed all 68 of the agent's cases. One was the main
session's own error (it did not compile) and counts for nothing. K67 (the engine busy at (4)
once `STOP_TLU` is set: `-EBUSY`, bit 18 cleared and read back in the same IRQs-off section, two
stores) and M82 close the gap; M82 turns K67 alone red. Re-run by the main session on `2009c4eb`
plus the patch, each rc 0: `mdiocheck` 152 run, 0 failed, 82 of 82 mutants killed by the case
named for them; `mkinitramfs` (47) and its mutants (29), `sh -n` on the init script, `bootbytes`
(9), `nic15check` (50), `mfginject` (36, 1 skip), `appletcensus` (11 and 19), `srcarchive` (40),
`ci-census` (30), the config gates (72), `src/init`'s tests and mutants, the file modes (5).

**Also changed, in place** (讀): `rtl819x-switch.c`'s header item 3 and 1.5's last two
paragraphs; `rtl819x-nic.c`'s item 3 (on `SWCORE=n` no probe sets `FFCR`, `vlan` does);
`rlxfw-seam.c`'s item 1; `src/init/init.h`'s count of verbs; `config/rlxfw-initramfs.tsv`'s `/init`
row, which now leaves the binary's size to `docs/sbom.md`. The header's item 2 (`n_writes` reads
0 on a boot capture) was already untrue of a standard `/init` before 1.6 and is left as it was.

### 21.5 What `R6c-3` does not establish

* That the take-over brings `rlx0` up on a flash boot: nothing of 1.6 has run on the device.
  `R6c-4`'s seating is the test, and 2026-10-08's flash boots without the verb (`X-V06q`,
  `X-V08q`, seating A) are its control. 🔄 § 21.6: it does, warm and cold.
* That the RAM path still pings with netif slot 0 cleared: the loader's group minus that entry has
  not been measured on any path, and `R6c-4` tests it before any flash write. `NET-169` makes it
  plausible — on that path `rlx0`'s own address is in no table, so its unicast reaches the CPU by
  `FFCR`'s unknown-unicast trap and not through the netif entry — but that mechanism is itself 推
  on one source. The ruling's fallback, netif slot 0 with `rlx0`'s own address, is not written.
  🔄 § 21.6: the RAM path pings both ways with it cleared, so the netif entry is not the way in;
  that the trap is stays 推 — no L2 table was read and `NET-169`'s deciding experiment did not run.
  (Until 2026-10-09 this line ended "through that trap", the claim the 130th segment retracted.)
* How `SWTCR0` reads while `STOP_TLU` is set, whether the engine copies all eight `TCR` words or
  three and five, how many polls a command takes, and what `SWTASR` reports after a force: the
  harness scripts each, and the silicon has answered none. 🔄 § 21.6: it has answered all but
  the `TCR` count.
* What the switch does with a frame that arrives while `STOP_TLU` holds the lookups: on the RAM
  path the loader has already set `TRXRDY` when `vlan` runs.
* The state after a watchdog reset on the flash path (seating A's boot was cold), and any value
  outside the group: `MACCR` (the one configuration word where F differs from both working
  states), `QNUMCR`'s CPU field, the PHY patch, `LEDCREG`. 🔄 § 21.6: the warm state equals
  the cold one.
* That the harness catches an error it shares with the driver: its engine follows the same two
  vendor readings the driver does.
* Anything under load, with a second port, or on the vendor's firmware.

### 21.6 Seating R6c-4: the take-over on the device (`bench/2026-10-08c`, `NET-173`)

量 2026-10-08, the 129th segment: `bench/2026-10-08c/R6C-4-CARD.md` and its `CORRECTIONS-R6C-4.md`.
One flash write (`I10`, T into slot A under the owner's dated yes) and two power actions (the cold
boot's off and on). The release image `9bb2bec7` ran on all three paths; the armed image `8dce09c5`
only staged and installed T.

| | RAM path, through the prompt (`R03`) | warm flash boot (`W03`) | cold flash boot (`C03`) |
|---|---|---|---|
| `vlan` | rc 0, `vw 0000 nw 01 rw 00` | rc 0, `vw 0100 nw 00 rw 1F` | as warm |
| `n_writes` (predicted) | 18 (18) | 23 (23) | 23 (23) |
| `n_reads` at the first read | 128 = 126 + `sta` 1 + `spin` 1 | 133 = 131 + 1 + 1 | 133 |
| `tlu`, `swtasr`, `final`, `ld`, `to`, `rb` | `000C0000`, 0, 0, 784, 0, 0 | as RAM | as RAM |
| `SWTAA` live / latch | `BB040000` / `BB060100` | `BB060100` / 0 | as warm |
| tables after | VLAN slot 8 `00807E3F`, the rest and netif empty | as RAM | as RAM |
| `QNUMCR` | `00001249` | `00041249` | `00041249` |
| host → board | 4 of 4 | 4 of 4 | 4 of 4 |
| board → host | 225 of 225 (unbounded, `CORRECTIONS` C1) | 4 of 4 | 4 of 4 |

* Every field of the `vlan` line read as `R6c-4`'s card predicted from the code, on all three
  paths; `ld 784` says every double read agreed at once, and `tlu 000C0000` that bit 18 read back
  set after (2), which the code records and does not require.
* The warm flash boot's latches equal the cold boot's and seating A's: a watchdog reset clears the
  ASIC tables with the registers (`vw 0100`). The review's third alternative -- registers reset,
  tables kept, `n_writes` 11 -- did not happen.
* With netif slot 0 cleared, the RAM path still receives: across the host's ping, port 3's in
  columns and the CPU port's out columns moved together column for column and the discard
  columns stayed 0 (`R09` → `R11`, and `X-R15` after the board's 225). So the netif entry is not
  what carries `rlx0`'s unicast, and ruling O1's fallback, netif slot 0 with `rlx0`'s address, is
  not needed. 🔄 2026-10-08 (130th segment): this bullet first called the path `FFCR`'s
  unknown-unicast trap, `NET-169`'s mechanism, "measured for the first time". It is not: no L2
  table was read on these boots, and `NET-169`'s deciding experiment (the RX header's `ph_reason`,
  or a unicast ping with `FFCR` bit 1 cleared) did not run, so the trap stays 推.
* Booted from flash, rlxfw receives (`NET-171` reversed for 1.6): `rlx0`'s RX went 0 → 6 → 10 on
  each flash boot, and port 3's discards stayed 0 where seating A counted every frame.
* The install: 4,625 operations (288 sector erases, 4,337 page programs), slot A's 1,179,648 bytes
  read back with no difference; `rlxboot` then chose A (`ok:5`) over B (`ok:4`) on both flash
  boots, and `bootslot judge` passed both.

**What `R6c-4` does not establish.** How many `TCR` words the engine copies (equal read-backs say
only that the slot reads back as stored); what happens to a frame that arrives while `STOP_TLU`
holds the lookups on the RAM path; which part of the written group is necessary; `MACCR`'s and
`QNUMCR`'s part (they differ between the paths, and both paths work); more than one warm and one
cold boot; load; a second port — the layout makes ports 0–5 one VLAN, port 0, the vendor
firmware's WAN, among them, so 推 a peer there is a LAN peer (`NET-174`); the vendor's firmware.
