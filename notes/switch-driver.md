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
   推 is untested and the table is left alone until it is.
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

讀, the same census as § 8.6, on the boot-path routine at `0x804038DC`–
`0x804039B0`. It is listed here because § 1's table asserted the opposite for
one of its three registers:

| site | write | reads back at the prompt? |
|---|---|---|
| `0x804038EC` | `MACCR (0x4000) \|= 0x1000` | — |
| `0x80403904` | `PITCR (0x4100) \|= 0x1` | 🔴 **no** — `PITCR` reads `00000000` in both states; `docs/loader-phy-and-switch.md` already owns that |
| `0x80403918` | `P0GMIICR (0x414C) \|= 0x40` | — |
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
forms and nothing else:

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
  among the leaves*; 8b's path goes in when the seam lands. The ten seam names
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
🔄 **Carried: `tools/imgprocs.py`'s comment above `SHARED` states both**
(*667 compiled objects searched*; `arp` from `arp.o, x_tables.o`, `ip` from
`x_tables.o`). It stays as it is until seating 43 has run, because a card may
pin the tool by digest, and is corrected after it.
