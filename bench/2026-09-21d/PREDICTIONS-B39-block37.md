# PREDICTIONS — block 37, seating 34 (the bracket block 35 did not have)

Frozen before power. **declared date 2026-09-21** — `bench/2026-09-21c` is
seating 33's and this is a new power cycle, so it gets its own directory.

Marks: 量 measured on this device · 讀 read out of code or a dump · 推 inferred,
pending a measurement.

---

## § 0 What this block is, and the one sentence it exists to decide

Seating 33 found a failure that is **not** `NET-67`. After an `iperf3` run the
driver read `tx_stopped 0`, `n_tx_stop 0`, `n_xmit_busy 0`, all four TX
descriptors **CPU**-owned and `n_tx` still advancing — while host-side
`tcpdump` showed three ARP requests out and **zero frames back**. The NIC
driver was healthy and nothing reached the wire.

The only other thing that moved was the **switch**: `X5-SW` read

| register | at probe | after the failure |
|---|---|---|
| `MEMCR` `4234` | `00007F7F` | **`00007F00`** |
| `PSRP0` `4128` | `000010E0` | **`000000E0`** |
| `PSRP3` `4134` | `000010F9` | **`000000F9`** |

🔴 **And that table cannot support the sentence it looks like it supports.**
`X5-SW` was taken **only after**. The `at probe` column is what the driver
snapshotted at `subsys_initcall`, before `start`, before `ndo_open` and before
any traffic — so *"these differ from boot"* is a fact about the whole boot, and
*"`iperf3` changed them"* is a different claim that no capture in this
repository supports. **This block takes the reading before as well.**

---

## § 1 The image

Unchanged from seating 33's block 36: `s32a`, loud, `RECIPE_ID` **`84385d91`**,
assembled `nfjrom` **1,180,672 B** sha256 `eee556f46adf9c06…`, initramfs spec
sha256 `7130245fbcd92afc…` (byte-identical to `s31L`'s, so only the kernel
differs). `RECIPE_ID` cannot tell two images apart here (`FW-99`); the
discriminator is `looprun --image-sha256`.

---

## § 2 The pre-registered predictions

### 2.1 🔴 `MEMCR` — the one the block is for

* 推 **`C2-SWPRE` already reads `00007F00`**, i.e. the low byte is cleared by
  something in the boot or by `start`, and **`iperf3` does not touch it**.
* 🔴 **Refutation, and it is the result if it happens**: `C2-SWPRE` or
  `C4-SWPRE2` reads `00007F7F` and `C8-SWPOST` reads `00007F00`. That would
  make `MEMCR` the first register in this project measured to change *across*
  the failure, and it would name where to look next.

### 2.2 🟢 `PSRP` bit 12 — a free control, two reads with nothing between them

`C2-SWPRE` and `C4-SWPRE2` are two dumps of the same 37 registers with only
`ndo_open` between them.

* 推 **bit 12 (`0x1000`) of `PSRP0`/`PSRP3` is already clear at `C2`**, because
  the likeliest explanation of `000010F9 → 000000F9` is that the bit is
  **clear-on-read** and the driver's own probe-time snapshot consumed it.
* 🔴 If it is **set at `C2` and clear at `C4`**, clear-on-read is measured
  rather than guessed — and every single-sample reading this project has taken
  of `PSRP` is then a lower bound, the same way `NET-61`'s Δ readings are.
* ⚠️ If it is set at both, it is neither, and the bit is undetermined.

### 2.3 The failure itself

* 推 the board becomes unreachable at `C7-IPERF`. Six `iperf3` invocations
  across seatings 32 and 33 have done it six times.
* 🔴 **If nothing among the 37 registers differs between `C4-SWPRE2` and
  `C8-SWPOST` while the board becomes unreachable**, the cause is outside this
  register set, and the next places are named now rather than after the fact:
  the PHY (`MDCIOCR`/`MDCIOSR`, which the dump does carry) and the engine
  block (`GDSR0`, `CPUICR`, `CPUTPDCR0`), which this driver does **not** dump
  and which `NET-71` reached only through the vendor's
  `/proc/rtl865x/memory`.

### 2.4 `R6-6`'s readable half, for free

The dump carries `VCR0`, `VCR1` and `PVCR0`–`PVCR4` — the per-port VLAN
configuration, which is exactly `R6-6`'s subject. 量 seating 33 read
`PVCR0 00090009`, `PVCR1 00090009`, `PVCR2 00010008`, `PVCR3 00010001`,
`PVCR4 00000009`, `VCR0 00000000` against `000001FF` at probe.

* 推 this boot reproduces those seven values.
* ⚠️ **This is not `R6-6`'s DoD and is not offered as it.** Two of `R6-6`'s
  three clauses were proven unreachable before power last seating: a two-port
  test needs two simultaneously-live endpoints and one cable gives one
  `LinkUp` (thirteen readings, no exception), and rlxfw cannot write the VLAN
  table at all — 讀 `rtl819x-switch.c:88-92`, the table is behind the TACI
  indirect path. What this cell produces is a **reading of the VLAN state this
  board actually runs in**, which `R6-7` can cite; the DoD stays unmet and
  says so.

---

## § 3 VOID conditions

1. `C5-PING` not 4/4 → everything below is uninterpretable.
2. `C2-SWPRE` does not return all 37 `r ` rows → the comparison has no
   before-image and the block is void.
3. The board becomes unreachable **before** `C7-IPERF` → the bracket does not
   surround the event it was built for; record and stop.

---

## § 4 What this block does NOT establish

* **Why the engine pauses** (`NET-67` 殘留) — untouched; that state did not
  occur in seating 33 and may not occur here.
* **`D5`.** `C7` is run to break the board, not to measure it, and no number
  from it may be quoted.
* **Whether `MEMCR`'s low byte means what its name suggests.** `NET-29` named
  the address; nothing in this project has read a field definition for it.

---

## § 5 The cells

```
#-- C0    looprun: rescue -> burnflag -> hostlink -> upload -> staged -> boot -> assert
#--       --skip S2,S3,S4 --recipe-override 84385d91
#--       --image  <imgwork>/s32a/s32a/kroot/rtkload/nfjrom
#--       --image-sha256 eee556f46adf9c0623fa3d0a0d4290f244707e4a9d0cdd0abf5ef767d2cd2b85
#-- C1-SW   the switch to its dumb state.
CAP --out bench/2026-09-21d/C1-SW --send 'echo unlock i-mean-it > /proc/rtl819x-switch ; echo start > /proc/rtl819x-switch' --seconds 25
#-- C2-SWPRE 🔴 THE READING BLOCK 35 DID NOT HAVE. Before ndo_open, before any
#--          traffic. § 2.1 and § 2.2 both read THIS cell.
CAP --out bench/2026-09-21d/C2-SWPRE --send 'cat /proc/rtl819x-switch' --seconds 30
#-- C3-UP   ndo_open does alloc, arm, request_irq, engine on.
CAP --out bench/2026-09-21d/C3-UP --send 'echo unlock > /proc/rtl819x-nic ; echo netdev on > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --seconds 25
#-- C4-SWPRE2 the same 37 registers again, with only ndo_open between. § 2.2's
#--           control is the PAIR, not either one alone.
CAP --out bench/2026-09-21d/C4-SWPRE2 --send 'cat /proc/rtl819x-switch' --seconds 30
#-- C5-PING § 3 clause 1 reads THIS cell.
HOST bench/2026-09-21d/C5-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
#-- C6-NICPRE the NIC side of the bracket.
CAP --out bench/2026-09-21d/C6-NICPRE --send 'cat /proc/rtl819x-nic' --seconds 25
#-- C7-IPERF the event. Expected to leave the board unreachable.
CAP --out bench/2026-09-21d/C7-IPERF --send 'iperf3 -c 10.1.1.2 -p 5201 -t 10 -i 1 -f m' --seconds 45
#-- C8-SWPOST 🔴 THE OTHER HALF OF THE BRACKET.
CAP --out bench/2026-09-21d/C8-SWPOST --send 'cat /proc/rtl819x-switch' --seconds 30
#-- C9-NICPOST
CAP --out bench/2026-09-21d/C9-NICPOST --send 'cat /proc/rtl819x-nic' --seconds 25
#-- C10-PING alive?
HOST bench/2026-09-21d/C10-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
#-- C11-SNMP the whole file, for the Icmp pair NET-76 殘留 names.
CAP --out bench/2026-09-21d/C11-SNMP --send 'cat /proc/net/snmp' --seconds 25
```

```cells
bench/2026-09-21d/C0-ab2
bench/2026-09-21d/C0-2a
bench/2026-09-21d/C0-boot
bench/2026-09-21d/C1-SW
bench/2026-09-21d/C2-SWPRE
bench/2026-09-21d/C3-UP
bench/2026-09-21d/C4-SWPRE2
bench/2026-09-21d/C5-PING
bench/2026-09-21d/C6-NICPRE
bench/2026-09-21d/C7-IPERF
bench/2026-09-21d/C8-SWPOST
bench/2026-09-21d/C9-NICPOST
bench/2026-09-21d/C10-PING
bench/2026-09-21d/C11-SNMP
```

---

## § 6 The machine-checkable declaration

```cardnum
cells-fence	14	count bench/2026-09-21d/PREDICTIONS-B39-block37.md ^bench/2026-09-21d/C[0-9]
declared-date	1	count bench/2026-09-21d/PREDICTIONS-B39-block37.md [*][*]declared date 2026-09-21[*][*]
cap-cells	9	count bench/2026-09-21d/PREDICTIONS-B39-block37.md ^CAP -{2}out
host-cells	2	count bench/2026-09-21d/PREDICTIONS-B39-block37.md ^HOST bench/2026-09-21d/
send-over-127	0	count bench/2026-09-21d/PREDICTIONS-B39-block37.md -{2}send '[^']{128,}'
no-shell-subst	0	count bench/2026-09-21d/PREDICTIONS-B39-block37.md -{2}send '[^']*[$]
no-flr	0	count bench/2026-09-21d/PREDICTIONS-B39-block37.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-21d/PREDICTIONS-B39-block37.md -{2}send '[^']*(EW |EB |FLW )
no-burn	0	count bench/2026-09-21d/PREDICTIONS-B39-block37.md -{2}send '[^']*AUTOBURN
no-arm	0	count bench/2026-09-21d/PREDICTIONS-B39-block37.md -{2}send '[^']*echo arm
no-ifdown	0	count bench/2026-09-21d/PREDICTIONS-B39-block37.md -{2}send '[^']*ifconfig rlx0 down
no-memory-write	0	count bench/2026-09-21d/PREDICTIONS-B39-block37.md -{2}send '[^']*echo write
no-reset-full	0	count bench/2026-09-21d/PREDICTIONS-B39-block37.md -{2}send '[^']*reset full
no-restore-zero	0	count bench/2026-09-21d/PREDICTIONS-B39-block37.md -{2}send '[^']*restore 0
s32a-nfjrom-bytes	1180672	size /home/key/fwre-work/rebuild/imgwork/s32a/s32a/kroot/rtkload/nfjrom
s32a-nfjrom-sha256	eee556f46adf9c06	sha256-16 /home/key/fwre-work/rebuild/imgwork/s32a/s32a/kroot/rtkload/nfjrom
```
