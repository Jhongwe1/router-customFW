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

| register | address | what it is | why the loader never touched it |
|---|---|---|---|
| **`MSCR`** | `0xBB804410` | Module Switch Control — the L2/L3/L4 mode and both ACL enables | the loader does no forwarding; it never leaves L2 |
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
| **S0′** | after early kernel init, before the vendor NIC driver | latched at `subsys_initcall`. **Nothing has ever measured this state.** |
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

⚠️ **Eight of those nine registers have no prior reading on this die at all**,
so each write is preceded by a read of the same register in the same verb and
the read is the measurement rather than a courtesy.

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
