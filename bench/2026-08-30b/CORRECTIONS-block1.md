# CORRECTIONS — `PREDICTIONS-B5-block1.md`, after the seating

**Written 2026-08-30, after power cycle 2.** The block is frozen. `RUNSHEET`
§B5-c12 already listed what was known wrong about it *before* the seating; this
is what the seating itself showed, and block 0 got such a file on the night
while this one did not — an asymmetry an adversarial pass had to point out.

**The block's own gate passed**: `12 of 12 captures came after the prediction, 0
did not`, and **every one of its substantive predictions held**: the five
`rtkload` prefix lines byte for byte, `start address: 0x80003600`, all eleven
marks in order, `B02=0000CD01` upper case against `CPU revision is: 0000cd01`
lower case, `B07=00000000`, the `L2b` variant discriminator, the `L0-tail`/`L2c`
before-and-after pair, and `L5b`'s build stamp to the character.

---

## 1. 🔴 The port masks are the vendor kernel's, and this build reports them mirrored

`PREDICTIONS-B5-block1.md`'s `L6a` paragraph reads:

> 讀 `G6.log`: `eth0` vid 9 / member port `0x10`, `eth1` vid 8 / port `0x1`,
> `eth2` `0x8`, `eth3` `0x4`, `eth4` `0x2`

`G6.log` is **this unit's shipped kernel**. §B5-c9 corrected the *count* in that
paragraph — six netdevs, not five, with `eth7` — and **nobody corrected the
masks**. 量, `bench/2026-08-30b/L3.log:99-104`, the artefact this seating
actually uploaded:

| netdev | vendor (`G6.log`, `uart-boot.log`) | mine (`L3.log`) | bit index |
|---|---|---|---|
| `eth0` | `0x10` | **`0x1`** | 4 → 0 |
| `eth1` (WAN, vid 8) | `0x1` | **`0x10`** | 0 → 4 |
| `eth2` | `0x8` | **`0x2`** | 3 → 1 |
| `eth3` | `0x4` | `0x4` | 2 → 2 |
| `eth4` | `0x2` | **`0x8`** | 1 → 3 |

**`mine = 4 − vendor` for every one** — a 5-bit reversal with `eth3` as the fixed
midpoint. Four of the block's five mask predictions are refuted, and the one that
holds (`eth3`) holds because it is the reversal's own fixed point.

🔴 **A member-port bit indexes a physical switch port, which the hardware
fixes**, so the netdev↔jack binding differs between the two builds. `NET-04` is
derived from the vendor's numbering, and a driver written against it would drive
the wrong jacks under this kernel. `RTL_WANPORT_MASK` carries both `0x10` and
`0x01` under different `#ifdef`s (讀, `rtl865x_netif.h:400`, `:411`), which is
where the difference enters.

⚠️ **The consequence for `NET-13` is that the answer has to be a port number.**
The cable is on **switch port 3** — `eth4` under this build, `eth2` under the
vendor's. Written as a netdev name it is true only for one build; written as a
port it agrees with `NET-04`'s untouched *"`eth2` 埠 3"*.

## 2. `L6a`'s "five interfaces" — already corrected, and it held in the corrected form

The block predicts **five**; §B5-c9 corrected it to **six** before the seating,
and six is what `ifconfig -a` returned. Recorded here only because §B5-c12's
list is about what was known before the seating and this is the row that was
then confirmed on the device.

⚠️ The driver's own registration line says `eth5 added` where `ifconfig -a`
shows `eth7`. `rtl_nic.c:6479` prints the array **index**, not `dev->name`, and
index 5 is the only entry renamed. **So the boot log's `ethN` is not a netdev
name at all** — which is exactly why item 1's binding is 讀 and only its masks
are 量.

## 3. `L3`'s `--seconds 90` is the only terminator on §B5's card

Not a defect of this block — the block names the window correctly and the
reference (26.05 s for the vendor kernel) is sound; `L3` finished well inside
it. It is recorded here because **14 of §B5's 15 capture rows carry no
terminator at all**, and `L-3` is the one that does.
`bench/2026-08-30/CORRECTIONS-block0.md` §1 owns the measurement.

## 4. What the block deliberately did not predict, and was right not to

The block says the `printk` between the marks is not predicted because *"nothing
has ever observed this kernel printing between B04 and B10 with real
peripherals"*. 量: it printed ~110 lines there, including the whole
`rtl8192cd_init_one` sequence, the SPI/MTD probe and the netdev registration —
none of which any desk channel had produced. **Predicting that content would
have been decoration**, and the two lines it *did* name as cheap to look for —
`Calibrating delay loop… BogoMIPS` and the `Linux version` stamp — both arrived.

⚠️ `TC-o` reproduced exactly as the block predicted it would: **one** replayed
buffered line, `CPU revision is:`, landing after B03. Not more.
