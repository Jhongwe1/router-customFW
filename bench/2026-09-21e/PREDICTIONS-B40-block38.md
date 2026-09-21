# PREDICTIONS — block 38, seating 35 (the vendor baseline, and `NET-77`'s third candidate)

Frozen before any cell runs. **declared date 2026-09-21** — `bench/2026-09-21d`
is seating 34's and this is a new power cycle, so it gets its own directory.

Marks: 量 measured on this device · 讀 read out of code or a dump · 推 inferred,
pending a measurement.

🔴 **One honesty note about the freeze, written rather than left to be found.**
The board was powered **before** this card was written: the operator asked for
the ESC window first, and `bench/2026-09-21e/S0-catch` (19:13–19:17, 1,021 B,
banner with **no** `Reboot Result from Watchdog Timeout!` line, so a cold
power-on) is what caught the loader prompt. **No cell below has run, no image
has been uploaded, and `S0-catch` is deliberately not in the `cells` fence.**
The mtime evidence `check-predictions` reads is intact for every cell that is.

---

## § 0 What this block is, and the two sentences it exists to decide

Four seatings have named a blocker for `D5` and each name was killed by the
next seating's measurement: `NET-59` → `NET-61` → `NET-67` → `NET-78`. That is
a search with no reference implementation, at one power cycle per excluded
candidate. `docs/nic-vendor-diff.md` was written to stop paying that price,
and § 10 of it is this card's design.

**Boot 1 asks: does the VENDOR's driver carry an `iperf3` run on this board?**
Three outcomes, all worth the seating, all written before power (§ 2.5).

**Boot 2 asks: which of `NET-77`'s three remaining candidates is necessary?**
量 `docs/nic-vendor-diff.md` § 10, re-reading `NET-77`'s own `/proc/net/snmp`
numbers: every non-wedging rung is `PassiveOpens`/`OutRsts` and every wedging
run is `ActiveOpens` — four and four, no exceptions — so the row's "two
remaining candidates" is **three**, and the third (**the board OPENS the
connection**) is perfectly confounded with the second in all existing data.

| | candidate | present in |
|---|---|---|
| ⓐ | data actually flowing on an established connection | `W1`, `W2`, `W3`, `W4`, `W5` |
| ⓑ | `iperf3`, the program | `W1`, `W2`, `W4`, `W5` |
| ⓒ | the board opening an outbound connection (`ActiveOpens`) | `W4`, `W5` |

---

## § 1 The image, and why it is not a new one

Unchanged from seating 34's block 37: **`s32a`**, `RECIPE_ID` **`84385d91`**,
`nfjrom` **1,180,672 B**, sha256 `eee556f46adf9c06…`. 量 tonight, on the
artefact rather than from any row:
`sha256sum` = `eee556f46adf9c0623fa3d0a0d4290f244707e4a9d0cdd0abf5ef767d2cd2b85`.
`RECIPE_ID` cannot tell two images apart here (`FW-99`); the discriminator is
`looprun --image-sha256`, which is why it is passed.

**Host side**: `/home/key/fwre-work/iperf3-port/iperf3`, 量 `file` = *ELF
32-bit MSB, MIPS, statically linked*, 252,644 B, sha256 `3144db60…` — the
**same binary the board runs**, executed here under `qemu-mips-static`.
🟢 That makes every `iperf3` rung below a same-version, same-build exchange,
which is what `NET-60` (3.1.3 ↔ 3.16 fails on the real 1500 path) requires.

Addresses: host **10.1.1.2** on `enxfc19286184c9`; board **10.1.1.3** on
`rlx0` (mine), **10.1.1.4** on `eth4` (the vendor's). Two addresses so that
*which driver answered* is a reading and not an assumption.

---

## § 2 The pre-registered predictions

### 2.1 🔴 `V2` — the handover is real, or boot 1 is void

讀 `rtl819x-nic.c:1183-1193`: `nic_ndo_stop()` calls `free_irq(NIC_IRQ, …)`.

* 推 `V2-DOWN` shows **no line 12** in `/proc/interrupts`.
* 🔴 **Refutation**: line 12 still present → `free_irq` did not happen, the
  vendor cannot take the IRQ, and everything after `V2` in boot 1 is void.

### 2.2 🔴 `V3` — the claim this repository has twice recorded as impossible

`docs/KNOWN-ISSUES.md:870`/`:941` say `ifconfig eth4 up` returns `EBUSY`. 量
last segment, at the desk: that capture (`bench/2026-09-20/X9-eth4.log`) never
ran `ifconfig rlx0 down` first, while seating 28 did and the handover worked
(`notes/nic-driver.md:518-519`).

* 推 `V3-ETH4` brings `eth4` up `UP BROADCAST RUNNING` and
  `/proc/interrupts` reads `12: n RLX LOPI eth4`.
* 🔴 **Refutation, and it is a result**: `EBUSY` with `rlx0` already down →
  `KNOWN-ISSUES` is right, `notes/nic-driver.md:518-519` was something else,
  and boot 1 **stops at `V3`**. That correction gets written either way.

### 2.3 ⚠️ `V4` — rlxfw's `/proc` as a read-only observer of the vendor's hardware

`now_icr`, `rpdcr0_pos`, `rmdcr0_pos`, `tpdcr0_pos` are read from hardware
registers, not from driver state, and a `cat` writes nothing.

* 推 after the vendor's `rtl865x_init_hw()`, the ring-base positions **leave**
  rlxfw's `A15B80xx` range.
* ⚠️ **If they still read `A15B80xx`**, the vendor's open did not re-arm the
  engine, both drivers are pointing at rlxfw's rings, and every reading in
  boot 1 after `V3` is ambiguous — say so rather than quoting the numbers.
* 🟢 Control in the same cell: `n_writes` is unchanged by a `cat`.

### 2.4 🟢 `V5` — the vendor carries ICMP, or the link is dead

* 推 4 of 4 both ways on 10.1.1.4.
* 🔴 If neither direction works, boot 1 is measuring a dead link and not a
  baseline. `NET-56` is the known shape (contact fault, one-way); the reading
  that separates it is `V1-ACNT`'s port 3 `CRCAlignErr`/`SymbolErr`, taken
  **before** any of this, which is why that cell is early.

### 2.5 🔴🔴 `V6` — the cell this seating exists for

Three outcomes, written before the board is powered, all worth the seating
(`docs/nic-vendor-diff.md` § 10):

* **The vendor wedges too** → the fault is not in this driver. `D5` is not
  reachable on this hardware by this method, and `R6-7` writes that with a
  measurement behind it.
* **The vendor survives and gives a number** → a platform baseline, a
  single-variable differential, and every later hypothesis becomes an A/B.
* **The vendor survives at about 30 Mbit/s** → § 4's copy cost is excluded and
  `NET-76`'s 29.761 Mbit/s is the path, not this driver's bounce buffer.

**Pre-registered guess, so that being wrong is visible**: 推 the vendor
**survives**. Basis is 讀 not 量 — `NET-79`: the vendor never stops the queue,
recycles in place and retries 128 times, on rings of 128/256 against rlxfw's
4/8. 🔴 **If it wedges anyway, that inference is refuted and the fault is
below both drivers**, which kills every driver-side candidate in `NET-78` at
the cost of one cell.

### 2.6 🔴🔴 The `W` ladder, and what each rung can refute

| rung | who opens | `iperf3` | bulk | bulk direction |
|---|---|---|---|---|
| `W1` | host | both ends | yes | host → board (board mostly RX) |
| `W2` | host | both ends, `-R` | yes | **board → host (board TX)** |
| `W3` | host (`socat`) | none on the wire | bounded | host → board |
| `W4` | **board** | yes | yes, **UDP** | board → host |
| `W5` | **board** | yes | yes, TCP | board → host |

* `W1` wedges → ⓒ is **not** necessary. Strongest early result.
* `W1` clean and `W2` wedges → the factor is the board **transmitting** bulk,
  not who opened; ⓒ refuted, and the next image has a target.
* `W1`+`W2` clean and `W4` wedges → ⓒ plus the program suffice **without a
  TCP bulk stream**; ⓐ refuted as necessary.
* `W1`+`W2`+`W4` clean and `W5` wedges → ⓐ and ⓒ are both necessary; ⓑ stays
  conflated with them and the card says so rather than claiming the program.
* 🔴 **Everything clean, including `W5`** → the wedge did not reproduce.
  Six `iperf3` invocations have wedged this board across seatings 32–34, so a
  non-reproduction is itself the finding and the ladder is uninterpretable —
  record it, do not re-run it into the night.

### 2.7 ⚠️ `W3`'s limit, stated before it runs

`iperf3`'s server reads a 37-byte cookie and closes on a bad one, so `socat`
can only push what fits in the socket buffers before the RST — 推 tens of KB,
not a bulk stream. **A non-wedge at `W3` does NOT refute ⓐ.** It is on the
card because it is the only rung with **no `iperf3` protocol bytes on the
wire** at all, and it costs two cells.

### 2.8 🟢 The shell's liveness after each rung is itself a reading

量 `NET-75`: in seating 31/32's wedge the tty still echoes but the shell does
**not execute** — `echo` returns one line instead of two. 量 seatings 33/34:
after the `NET-78` failure the shell **did** execute, which is how
`C8-SWPOST`/`C9-NICPOST` exist. **So `*-ALIVE` separates the two failure
states**, and it is the first cell after every rung for exactly that reason.

### 2.9 🟢 `NET-81`'s decider rides along for free

`NET-78` 殘留 names *which ports `ph_portlist = 0x3F` resolves to in the
failure state*; `NET-81` names the reading that decides it — the switch's
**per-port MIB counters across the fault**. 量 `NET-42`: `asicCounter` is one
of the 13 `/proc/rtl865x/` entries that survive into rlxfw's image, and
`NET-46` already reconciled it against `ifconfig` with no shared code.
`W0-ACNT` and `W5-ACNT` are that bracket. ⚠️ `NET-46`'s own instrument defect
travels with it: `<CPU port (extension port included)>` is a heading a
`/^<Port:/` filter cannot see, and it invented a contradiction once.

---

## § 3 VOID conditions

1. `V1-PING` not 4 of 4 → boot 1 is not a baseline. Stop and say so.
2. `V3-ETH4` returns `EBUSY` → boot 1 stops there. **That is a reading, not a
   void** (§ 2.2).
3. `W0-SRV` does not leave an `iperf3` server running (`ps`, and a LISTEN row
   in `/proc/net/tcp`) → `W1`, `W2`, `W3` are void. Go to `W4`/`W5`, and do
   not quote a non-wedge from a rung whose listener never existed.
4. A host-side listener or generator not proven alive **in its own cell**
   before the rung that needs it → that rung is VOID. 🔴 `FW-102`: block 35's
   `T6` was void exactly this way (`nohup … &` inside a heredoc died with its
   parent) and it read as a board result.
5. A payload typed into a dead shell scores as a capture. Every `*-ALIVE`
   cell gates the cells after it; when one shows a dead shell, the boot is
   over and the rest of that boot's cells are **not** run (segment 90 typed
   fourteen frozen cells into a dead shell and `check-predictions` gave them
   full marks).
6. 🔴 `rlx0` must **not** be brought back up after `V2-DOWN` in the same boot.
   量 `NET-58`: re-opening does not re-arm the descriptor bases and the engine
   then DMAs outside the ring. `eth4` → `rlx0` costs a reboot, which is what
   `L2-RB` is.

---

## § 4 What this block does NOT establish

* **`D5`.** A number from `V6` is the **vendor's**, and `D5` names *my*
  driver — it cannot close it, and it may not be quoted as if it did.
* **`NET-78`'s mechanism.** The MII side (`PHYR`) and the switch address table
  are still unread; only the per-port MIB half of `NET-78` 殘留's named
  readings is on this card.
* **`R6-6`.** Its two unreachable DoD clauses (one live port on one cable;
  rlxfw cannot write the VLAN table — 讀 `rtl819x-switch.c:88-92`) are
  unchanged by anything here.
* **The `txd ph2/ph3/ph4` dump and `-DRTL_DEBUG_NIC_SKB_BUFFER`.** Both move
  `RECIPE_ID`, so they ride one future image together, and a card that
  predicts a boot capture's byte count has to be written against the image
  that will actually boot.

---

## § 5 The cells

```
#-- BOOT 1 — the vendor baseline
#-- L1    looprun: rescue -> burnflag -> hostlink -> upload -> staged -> boot -> assert
#--       --skip S2,S3,S4 --recipe-override 84385d91 --cell L1
#--       --image  <imgwork>/s32a/s32a/kroot/rtkload/nfjrom
#--       --image-sha256 eee556f46adf9c0623fa3d0a0d4290f244707e4a9d0cdd0abf5ef767d2cd2b85
#--       S4 is skipped because S0-catch already holds the prompt.
CAP --out bench/2026-09-21e/V1-SW --send 'echo unlock i-mean-it > /proc/rtl819x-switch ; echo start > /proc/rtl819x-switch' --seconds 25
CAP --out bench/2026-09-21e/V1-UP --send 'echo unlock > /proc/rtl819x-nic ; echo netdev on > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --seconds 25
HOST bench/2026-09-21e/V1-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
CAP --out bench/2026-09-21e/V1-NIC --send 'cat /proc/rtl819x-nic' --seconds 25
#-- V1-ACNT  the pre-state of the port 3 error counters. § 2.4 reads THIS cell.
CAP --out bench/2026-09-21e/V1-ACNT --send 'sleep 1 ; cat /proc/rtl865x/asicCounter' --seconds 40
#-- V2-DOWN  § 2.1. No line 12 -> the vendor can take the IRQ.
CAP --out bench/2026-09-21e/V2-DOWN --send 'ifconfig rlx0 down ; cat /proc/interrupts' --seconds 30
#-- V3-ETH4  § 2.2. EBUSY here ends boot 1 and is a reading.
CAP --out bench/2026-09-21e/V3-ETH4 --send 'ifconfig eth4 10.1.1.4 up ; ifconfig eth4 ; cat /proc/interrupts' --seconds 40
#-- V4-NIC   § 2.3. Whether rtl865x_init_hw() re-armed shows as the bases leaving A15B80xx.
CAP --out bench/2026-09-21e/V4-NIC --send 'cat /proc/rtl819x-nic' --seconds 25
HOST bench/2026-09-21e/V5-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.4
CAP --out bench/2026-09-21e/V5-BPING --send 'ping 10.1.1.2' --seconds 30
#-- V6-LISTEN host iperf3 3.1.3 under qemu, bound to 10.1.1.2:5201, proven with ss -ltn. § 3 clause 4.
HOST bench/2026-09-21e/V6-LISTEN :: ss -ltn
#-- V6-TCPDUMP runs across V6-IPERF on enxfc19286184c9.
HOST bench/2026-09-21e/V6-TCPDUMP :: sudo tcpdump -i enxfc19286184c9 -c 200 -n
#-- V6-IPERF  🔴 THE CELL THIS SEATING EXISTS FOR. § 2.5.
CAP --out bench/2026-09-21e/V6-IPERF --send 'iperf3 -c 10.1.1.2 -p 5201 -t 10 -i 1 -f m' --seconds 45
#-- V7-ALIVE  § 2.8. Two lines back = the shell executes.
CAP --out bench/2026-09-21e/V7-ALIVE --send 'echo ALIVE-V7' --seconds 15
CAP --out bench/2026-09-21e/V7-NIC --send 'cat /proc/rtl819x-nic' --seconds 25
CAP --out bench/2026-09-21e/V7-SW --send 'cat /proc/rtl819x-switch' --seconds 30
CAP --out bench/2026-09-21e/V7-ACNT --send 'sleep 1 ; cat /proc/rtl865x/asicCounter' --seconds 40
HOST bench/2026-09-21e/V7-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.4
CAP --out bench/2026-09-21e/V7-SNMP --send 'cat /proc/net/snmp' --seconds 25
#-- BOOT 2 — the W ladder.  L2-RB costs no power press (FW-37, 2.407 s).
CAP --out bench/2026-09-21e/L2-RB --send 'busybox reboot -f' --esc-after 25 --seconds 45
#-- L2    looprun again, same image, same flags, --cell L2
CAP --out bench/2026-09-21e/W0-SW --send 'echo unlock i-mean-it > /proc/rtl819x-switch ; echo start > /proc/rtl819x-switch' --seconds 25
CAP --out bench/2026-09-21e/W0-UP --send 'echo unlock > /proc/rtl819x-nic ; echo netdev on > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --seconds 25
HOST bench/2026-09-21e/W0-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
CAP --out bench/2026-09-21e/W0-NIC --send 'cat /proc/rtl819x-nic' --seconds 25
#-- W0-ACNT  the before half of § 2.9's bracket.
CAP --out bench/2026-09-21e/W0-ACNT --send 'sleep 1 ; cat /proc/rtl865x/asicCounter' --seconds 40
#-- W0-SRV   the board becomes the server. § 3 clause 3 reads THIS cell.
CAP --out bench/2026-09-21e/W0-SRV --send 'iperf3 -s > /dev/null 2>&1 & sleep 3 ; ps' --seconds 30
CAP --out bench/2026-09-21e/W0-LISTEN --send 'cat /proc/net/tcp' --seconds 30
#-- W1  board = server, host = client, bulk INBOUND.  ⓒ absent.
HOST bench/2026-09-21e/W1-IPERF :: qemu-mips-static iperf3 -c 10.1.1.3 -p 5201 -t 10 -i 1 -f m
CAP --out bench/2026-09-21e/W1-ALIVE --send 'echo ALIVE-W1' --seconds 15
CAP --out bench/2026-09-21e/W1-NIC --send 'cat /proc/rtl819x-nic' --seconds 25
#-- W2  the same, -R: the BOARD transmits the bulk and still did not open. 🔴 the key rung.
HOST bench/2026-09-21e/W2-RIPERF :: qemu-mips-static iperf3 -c 10.1.1.3 -p 5201 -t 10 -R -i 1 -f m
CAP --out bench/2026-09-21e/W2-ALIVE --send 'echo ALIVE-W2' --seconds 15
CAP --out bench/2026-09-21e/W2-NIC --send 'cat /proc/rtl819x-nic' --seconds 25
#-- W3  real TCP bytes, no iperf3 protocol on the wire.  § 2.7 bounds what it can say.
HOST bench/2026-09-21e/W3-SOCAT :: socat -T5 OPEN:/dev/zero TCP:10.1.1.3:5201
CAP --out bench/2026-09-21e/W3-ALIVE --send 'echo ALIVE-W3' --seconds 15
#-- W4  board opens, iperf3 runs, bulk is UDP.  Separates ⓐ from ⓑ+ⓒ.
CAP --out bench/2026-09-21e/W4-UDP --send 'iperf3 -c 10.1.1.2 -p 5201 -u -b 20M -t 10 -i 1 -f m' --seconds 45
CAP --out bench/2026-09-21e/W4-ALIVE --send 'echo ALIVE-W4' --seconds 15
CAP --out bench/2026-09-21e/W4-NIC --send 'cat /proc/rtl819x-nic' --seconds 25
#-- W5  the known wedge, as the positive control.  This cell ends the boot.
HOST bench/2026-09-21e/W5-TCPDUMP :: sudo tcpdump -i enxfc19286184c9 -c 200 -n
CAP --out bench/2026-09-21e/W5-IPERF --send 'iperf3 -c 10.1.1.2 -p 5201 -t 10 -i 1 -f m' --seconds 45
#-- W5-ALIVE  🔴 the NET-75 / NET-78 discriminator. Everything below is best-effort.
CAP --out bench/2026-09-21e/W5-ALIVE --send 'echo ALIVE-W5' --seconds 15
CAP --out bench/2026-09-21e/W5-NIC --send 'cat /proc/rtl819x-nic' --seconds 25
CAP --out bench/2026-09-21e/W5-SW --send 'cat /proc/rtl819x-switch' --seconds 30
#-- W5-ACNT  the after half of § 2.9's bracket — NET-81's decider.
CAP --out bench/2026-09-21e/W5-ACNT --send 'sleep 1 ; cat /proc/rtl865x/asicCounter' --seconds 40
CAP --out bench/2026-09-21e/W5-SNMP --send 'cat /proc/net/snmp' --seconds 25
HOST bench/2026-09-21e/W5-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
```

```cells
bench/2026-09-21e/L1-ab2
bench/2026-09-21e/L1-2a
bench/2026-09-21e/L1-boot
bench/2026-09-21e/V1-SW
bench/2026-09-21e/V1-UP
bench/2026-09-21e/V1-PING
bench/2026-09-21e/V1-NIC
bench/2026-09-21e/V1-ACNT
bench/2026-09-21e/V2-DOWN
bench/2026-09-21e/V3-ETH4
bench/2026-09-21e/V4-NIC
bench/2026-09-21e/V5-PING
bench/2026-09-21e/V5-BPING
bench/2026-09-21e/V6-LISTEN
bench/2026-09-21e/V6-TCPDUMP
bench/2026-09-21e/V6-IPERF
bench/2026-09-21e/V7-ALIVE
bench/2026-09-21e/V7-NIC
bench/2026-09-21e/V7-SW
bench/2026-09-21e/V7-ACNT
bench/2026-09-21e/V7-PING
bench/2026-09-21e/V7-SNMP
bench/2026-09-21e/L2-RB
bench/2026-09-21e/L2-ab2
bench/2026-09-21e/L2-2a
bench/2026-09-21e/L2-boot
bench/2026-09-21e/W0-SW
bench/2026-09-21e/W0-UP
bench/2026-09-21e/W0-PING
bench/2026-09-21e/W0-NIC
bench/2026-09-21e/W0-ACNT
bench/2026-09-21e/W0-SRV
bench/2026-09-21e/W0-LISTEN
bench/2026-09-21e/W1-IPERF
bench/2026-09-21e/W1-ALIVE
bench/2026-09-21e/W1-NIC
bench/2026-09-21e/W2-RIPERF
bench/2026-09-21e/W2-ALIVE
bench/2026-09-21e/W2-NIC
bench/2026-09-21e/W3-SOCAT
bench/2026-09-21e/W3-ALIVE
bench/2026-09-21e/W4-UDP
bench/2026-09-21e/W4-ALIVE
bench/2026-09-21e/W4-NIC
bench/2026-09-21e/W5-TCPDUMP
bench/2026-09-21e/W5-IPERF
bench/2026-09-21e/W5-ALIVE
bench/2026-09-21e/W5-NIC
bench/2026-09-21e/W5-SW
bench/2026-09-21e/W5-ACNT
bench/2026-09-21e/W5-SNMP
bench/2026-09-21e/W5-PING
```

---

## § 6 The machine-checkable declaration

```cardnum
cells-fence	52	count bench/2026-09-21e/PREDICTIONS-B40-block38.md ^bench/2026-09-21e/[LVW]
declared-date	1	count bench/2026-09-21e/PREDICTIONS-B40-block38.md [*][*]declared date 2026-09-21[*][*]
cap-cells	35	count bench/2026-09-21e/PREDICTIONS-B40-block38.md ^CAP -{2}out
host-cells	11	count bench/2026-09-21e/PREDICTIONS-B40-block38.md ^HOST bench/2026-09-21e/
send-over-127	0	count bench/2026-09-21e/PREDICTIONS-B40-block38.md -{2}send '[^']{128,}'
no-shell-subst	0	count bench/2026-09-21e/PREDICTIONS-B40-block38.md -{2}send '[^']*[$]
no-flr	0	count bench/2026-09-21e/PREDICTIONS-B40-block38.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-21e/PREDICTIONS-B40-block38.md -{2}send '[^']*(EW |EB |FLW )
no-burn	0	count bench/2026-09-21e/PREDICTIONS-B40-block38.md -{2}send '[^']*AUTOBURN
no-arm	0	count bench/2026-09-21e/PREDICTIONS-B40-block38.md -{2}send '[^']*echo arm
ifdown-cells	1	count bench/2026-09-21e/PREDICTIONS-B40-block38.md -{2}send '[^']*ifconfig rlx0 down
no-memory-write	0	count bench/2026-09-21e/PREDICTIONS-B40-block38.md -{2}send '[^']*echo write
no-reset-full	0	count bench/2026-09-21e/PREDICTIONS-B40-block38.md -{2}send '[^']*reset full
no-restore-zero	0	count bench/2026-09-21e/PREDICTIONS-B40-block38.md -{2}send '[^']*restore 0
no-dumb	0	count bench/2026-09-21e/PREDICTIONS-B40-block38.md -{2}send '[^']*echo dumb
s32a-nfjrom-bytes	1180672	size /home/key/fwre-work/rebuild/imgwork/s32a/s32a/kroot/rtkload/nfjrom
s32a-nfjrom-sha256	eee556f46adf9c06	sha256-16 /home/key/fwre-work/rebuild/imgwork/s32a/s32a/kroot/rtkload/nfjrom
host-iperf3-bytes	252644	size /home/key/fwre-work/iperf3-port/iperf3
host-iperf3-sha256	3144db60bd3895f5	sha256-16 /home/key/fwre-work/iperf3-port/iperf3
```
