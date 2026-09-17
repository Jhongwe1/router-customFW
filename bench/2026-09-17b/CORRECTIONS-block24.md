# Corrections and readings — block 24

Card: `bench/2026-09-17b/PREDICTIONS-B25-block24.md`, frozen at `465692e`.
Cells ran 11:19–11:22 on 2026-09-17, one power cycle (the seating's only one,
spent at 11:02). `check-predictions`: **15 of 15 captures came after the
prediction, 0 did not.**

---

## 0. What ran, and one thing that should not have

All fifteen cells returned `rc=0` with the predicted byte counts — **71 bytes
for every `DW … 4` and 118 for every `DW … 8`**, nine and six of each, which is
`reply-size.py`'s model confirmed fifteen more times on this seating's own wire.

🔴 **The runner did not obey the card.** § 5 否證 ① says, in the card's own
words, *"Stop the ladder and record it"*. 否證 ① fired at `C10-PS0` — the first
rung — and the runner went on to run `C11` through `C15` anyway, because it was
written as a straight-line script with no gate on the first rung's content.
**Nothing was harmed** (every rung is a read, and rungs 2–6 turned out to carry
the block's one real ladder result), but the card gave an instruction and the
instrument did not have a way to receive it. **That is the defect, not the
extra reads**: a refutation condition that only a human can act on is one that
gets acted on late. A runner for a card with an abort condition has to be able
to read the abort condition.

---

## 1. 🔴 否證 ① fired, and what it caught is about the HOST

**Predicted** (§ 5, rung `C10-PS0`): with the host NIC down, all five `PSRP`
words read `000010E0`.

**量:**

| rung | host admin state | `PSRP0` | `PSRP1` | `PSRP2` | **`PSRP3`** | `PSRP4` |
|---|---|---|---|---|---|---|
| `C10-PS0` | DOWN | `000010E0` | `000010E0` | `000010E0` | **`000011F9`** | `000010E0` |
| `C11-PS0b` | DOWN | `000010E0` | `000010E0` | `000010E0` | **`000010F9`** | `000010E0` |
| `C12-PS1` | **UP** | `000010E0` | `000010E0` | `000010E0` | **`000010F9`** | `000010E0` |
| `C13-PS1b` | UP | `000010E0` | `000010E0` | `000010E0` | **`000010F9`** | `000010E0` |
| `C14-PS2` | **DOWN** | `000010E0` | `000010E0` | `000010E0` | **`000010F9`** | `000010E0` |
| `C15-PS2b` | DOWN | `000010E0` | `000010E0` | `000010E0` | **`000010F9`** | `000010E0` |

Port 3 was linked before the ladder started and stayed linked through four
host-side transitions. **Predictions for `C12`, `C14` and `C15` are all
refuted, and they are refuted by the same single fact.**

### 1.1 The peer is identified from the BOARD's side, not assumed

Two off-card cells, declared here, taken immediately after the ladder:

```
PHYR 3 5  ->  ANLPAR = 0x0000CDE1      bench/2026-09-17b/X4-anlpar3
PHYR 3 1  ->  BMSR   = 0x000078ED      bench/2026-09-17b/X5-bmsr3
```

`SPEC.md` `NET-14` (量 2026-08-24) holds all three fingerprints and **two of
them are negative controls that did not match**: `ANLPAR` reads `0xCDE1` for an
RTL8153 peer, `0xC1E1` for a PC NIC, `0x0001` for an unlinked port; `BMSR` reads
`0x78ED` with link and `0x78C9` without. **Both hits are exact.**

**量 — the peer on switch port 3 is the workstation's RTL8153 USB GbE**
(`0bda:8153`, WSL `enxfc19286184c9`), and that is the board's own reading of
the link partner's advertisement, not an inference from which cable is in which
jack.

### 1.2 🔴 The finding: `ip link set <if> down` is not a link-down event here

**量** — the host interface went `down → up → down → up` across the ladder, and
`PSRP3` never left `000010F9` (100M, full duplex, both pause bits). The
adapter's administrative state and its PHY's link state are decoupled.

⚠️ **推** — the mechanism is that this RTL8153 driver leaves the PHY powered and
autonegotiated when the interface is administratively down. Not measured here.

**Consequence for `R6`**: a link transition on this bench cannot be produced by
`ip link set`. It needs either a physical unplug (an operator action, which is
what `NET-11`'s earlier three observations used) or a host-side PHY command
(`ethtool -s … autoneg off` / `speed 10`), and **neither has been shown to work
on this adapter**. Any future card that wants a caused link event must
establish that first, on a cell whose failure is visible.

### 1.3 ⚠️ `ethtool` on this adapter is not a second source

量, with the interface up: `Speed: 100Mb/s`, **`Duplex: Half`**, `Supports
auto-negotiation: **No**`, `Supported link modes: **Not reported**`,
`Advertised link modes: Not reported`, `Auto-negotiation: off`. For a gigabit
adapter that is a stub, and it **disagrees with the board** — `PSRP3` bit 3 is
set, which `NET-11` maps to full duplex. **The board is the better source and
the host tool is the one that is wrong.** A card that had taken duplex from
`ethtool` would have recorded a disagreement with the silicon as a silicon
finding.

### 1.4 🟢 What the ladder DID measure, and it is cleaner than its three predecessors

`C10` → `C11`: `000011F9` → `000010F9`. **Bit 8 was set, and `C10`'s own read
cleared it**, with every other bit in all eight words identical between the two
captures.

That is `NET-11`'s read-to-clear `LinkDownEventFlag`, measured a **fourth**
time — and this observation is better controlled than the previous three.
`E11a2`, `E11c2` and `E11e` were all taken while a link was converging or being
physically moved, so *"the latch was cleared"* and *"a second real event
latched again"* were confounded. **Here the link did not move at all** across
six reads, so the only thing that changed between `C10` and `C11` was the act
of reading. 🔴 Where the latched event came from is **未定** — candidates are
the vendor firmware's ~5-minute run (§ 0.3 of the card) and the USB attach at
10:54; nothing here separates them.

---

## 2. Phase L — eight registers read for the first time

| address | symbol | value | source for the name |
|---|---|---|---|
| `0xBB804000` | `MACCR` | **`804A0185`** | D + B + A |
| `0xBB804004` | `MDCIOCR` | `96181441` | D + B + A |
| `0xBB804008` | `MDCIOSR` | `00000000` | D + B + A |
| `0xBB80400C` | — | `00000000` | — |
| `0xBB80414C` | `P0GMIICR` | **`00037D00`** | B |
| `0xBB804234` | `MEMCR` | **`00007F7F`** | B, `rtl865xc_asicregs.h` |
| `0xBB804238` | — | **`000FFFFF`** | 🔴 nothing names it |
| `0xBB804418` | `SWTCR0` | **`00080000`** | B |
| `0xBB80441C` | — | `00000200` | — |
| `0xBB804420` | — | **`07FAC688`** | 🔴 nothing names it |
| `0xBB804428` | `FFCR` | **`00000003`** | B |
| `0xBB804A08` | `PVCR0` | **`00080008`** | B |
| `0xBB804A0C`/`10`/`14` | `PVCR1`–`3` | `00080008` ×3 | B |
| `0xBB804D00` | `SWTACR` | `00000000` | B |
| `0xBB804D08` | `SWTAA` | **`BB060100`** | B |
| `0xBB804D3C` | `TCR7` | `00000000` | B |
| `0xBB804D48` | — | **`BB060100`** | 🔴 nothing names it |

### 2.1 The controls

* 🟢 **Positive** — `C9-SW100`'s eight words are **byte-identical to
  `bench/2026-08-24b/E9b.log`**, 24 days and many power cycles earlier:
  `00000000 007F0039 047F0039 087F0039 / 0C7F0039 107F0039 00000000 187F0038`.
  The loader's switch init is deterministic across power cycles, which the card
  predicted and which nothing had tested.
* 🟢 **Per-word decode** — `0xBB804118` reads `00000000` and `0xBB80411C` reads
  `187F0038`. Adjacent words, different values, so `DW` is not reporting a
  block-granular artefact. This is what licenses reading the other eight cells
  as per-word values.
* 🟢 **Negative control did not fire** — the eight never-read cells returned
  **eight different first words**. Had they all matched, the block would not be
  decoded there and every value above would be an artefact.

### 2.2 🔴 A desk prediction was refuted, and the refutation is the finding

An independent desk pass (datasheet D + this unit's own loader disassembly),
written without sight of this card, predicted `0xBB804234` = **`0x0000007F`**
from an unconditional `sw 127` at `0x80403458` in a function proved to have run.

**量: `0x00007F7F`.**

The low byte is exactly right. **Bits 15:8 hold a second `0x7F` that the
loader's single `sw 127` cannot account for.** 推, stated so it can be wrong:
this part has seven ports, `0x7F` is a seven-bit all-ports mask, and `MEMCR`
carries two of them. **Nothing here measures that**, and the experiment that
would is a read of `0xBB804234` after a switch-state change, which `R6-2` will
produce for free.

### 2.3 🟢 Seven other desk predictions held, and one of them was a refutation test

| predicted, blind | measured | |
|---|---|---|
| `PVCR0` = `0x00080008` | `00080008` | 🟢 |
| `FFCR` = `0x00000003` | `00000003` | 🟢 |
| `SWTCR0` bit 19 = 1, bit 18 = 0 | `00080000` | 🟢 both |
| `MACCR` bits 19:18 = `10` | `804A0185` → `A` = `1010` | 🟢 |
| `MACCR` bits 3:0 = `0101` | `…5` | 🟢 |
| `MACCR` bit 12 = 0 | nibble `[15:12]` = `0` | 🟢 |
| `MDCIOSR` bit 31 = 0 | `00000000` | 🟢 |
| 🔴 `P0GMIICR` bit 6 = **1** would refute the whole reconstructed loader path | `00037D00`, bit 6 = **0** | 🟢 **did not fire** |

The last row matters most: the desk pass concluded that the loader's taken
branch **skips all eleven `P0GMIICR` sites**, and named bit 6 as the cheapest
thing that would prove it wrong. It had a real chance to fire and did not.

### 2.4 Two values nothing explains

* **`0xBB804D08` = `BB060100` and `0xBB804D48` = `BB060100`** — two addresses
  0x40 apart holding the same unusual word. `SWTAA` is the switch table access
  *address* register, so a pointer-shaped value is not surprising, but
  `0xBB06xxxx` is not a block this project has a name for, and the coincidence
  at `+0x40` is not explained. **未定.**
* **`0xBB804420` = `07FAC688`** — no source names the address and the value has
  no obvious structure. **未定.**

---

## 3. What this block did NOT establish

1. It did not name `0xBB804234`, `0xBB804238`, `0xBB804420` or `0xBB804D48`.
   Reading a word is not learning what it is.
2. It gave `R6-2` **loader-state** values, not reset values. `R6-2`'s DoD says
   *differs from reset* and that is still unsatisfiable.
3. It produced no Linux-state reading at all, so the census's headline —
   **no `0xBB804xxx` word has ever been read under Linux** — is still true
   after this block. Block 25 is what changes it.
4. It says nothing about `CPU-45`.
5. `MT-PORT`'s gap is not closed **by this block's own cells**: these are
   loader-state link on a named port, and the gap is the Linux-state half.
   § 4 closes it, and it does so with a capture that was **already on disk
   before this block ran** — which is the point of § 4 and the reason it is
   not listed here as something the block established.

---

## 4. 🟢🟢 The loader/Linux bridge — eighteen fields, eighteen agreements, zero power cycles

This section uses **no cell of this block's own**. It compares block 24's
loader-prompt readings against `bench/2026-09-17/C2-PORT.log` — 585 bytes,
`cat /proc/rtl865x/port_status`, taken on **seating 25 at 03:04 this morning**
through the vendor's driver under Linux. That capture has been in the
repository since, and **no `SPEC.md` row recorded its contents**. `R6-0`'s
census exists to find exactly this: a fact that was measured, written down, and
owned by nothing.

### 4.1 The decode, field by field

`NET-11`'s bit map: 8 `LinkDownEventFlag` · 7 `NWayEnable` · 6 `RxPause` ·
5 `TxPause` · 4 `LinkUp` · 3 `Duplex` · 1:0 speed.

| register | loader-state (量 today) | decoded | `/proc` under Linux (量 seating 25) |
|---|---|---|---|
| `PSRP3` `0xBB804134` | `000010F9` | LinkUp · NWay · RxPause · TxPause · Duplex · speed `01` | `Port3 … LinkUp \| NWay Mode Enabled` / `RXPause Enabled \| TXPause Enabled` / `Duplex Enabled \| Speed 100M` |
| `PSRP5` `0xBB80413C` | `000000E2` | **LinkUp = 0** | `Port5 … LinkDown` |
| `PSRP6`/`PSRP7` `0xBB804140`/`44` | `0000007A` | LinkUp · **NWay = 0** · RxPause · TxPause · Duplex · speed `10` | `CPUPort … LinkUp \| NWay Mode **Disabled**` / `RXPause Enabled \| TXPause Enabled` / `Duplex Enabled \| **Speed 1G**` |

**Six fields on `Port3`, one on `Port5`, six on the CPU port, plus the five
`LinkDown` ports — eighteen agreements and no disagreement.**

### 4.2 Why `NWay = 0` is the load-bearing bit

Every real port on this part reads `NWayEnable = 1`; a CPU port does not
negotiate with anything. So bit 7 is what separates *"this is the CPU port"*
from *"this is another port with nothing plugged into it"*, and it is the one
field that could not have been guessed from the link state. **`/proc` prints
`NWay Mode Disabled` for exactly the register that reads bit 7 clear.**

### 4.3 What this settles, and what it does not

* 🟢 **`NET-10` closes.** Its own text said *"間距是推的；手上沒有任何來源明寫
  這兩個位址"*. 讀 `AsicDriver/rtl865xc_asicregs.h:1132-1151` names every one of
  them, with `PCRAM_BASE = SWCORE_BASE+0x4100` and `REAL_SWCORE_BASE =
  0xBB800000` (`:147`). **The source was in this repository the whole time.**
  🔴 The thing that was missing was not a measurement — it was somebody opening
  that file. That is a finding about how this project searches, not about the
  silicon.
* 🟢 **`NET-10`'s own 推 becomes 量**: it wrote in 2026-08-24 that speed code
  `10` is *"higher than `01` = 100M"*. `/proc` prints the characters `1G`.
* 🔴 **`0xBB804118` (`PCRP5`) is a three-way disagreement, not an agreement.**
  B names it; D's Table 62 **skips** it; the silicon reads **`00000000`** where
  every neighbour reads `xx7F00xx`. **The measurement sides with D**: the
  address decodes (it returns zero rather than garbage) but this part does not
  populate that port. A card that had taken B alone would have written a
  register that is not there.
* ⚠️ **Which of `PSRP6`/`PSRP7` is the CPU port is still 未定** — both read the
  same word and `/proc` lists one `CPUPort`.
* ⚠️ **Two things `/proc` prints that this repository has never mentioned**:
  `Port5` exists (this board has five jacks, ports 0–4, so port 5 has no
  socket), and **`EEE Status 0` on all seven** — `EEE` occurs zero times in
  `SPEC.md`.
