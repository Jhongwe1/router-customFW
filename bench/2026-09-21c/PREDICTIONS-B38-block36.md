# PREDICTIONS — block 36, seating 33 (`s32a`, and a failure it does not fix)

Frozen before the first cell. **declared date 2026-09-21** — same directory and
same seating as block 35; the board has not lost power since
`2026-09-21T12:20:47+0800`.

Marks: 量 measured on this device · 讀 read out of code or a dump · 推 inferred,
pending a measurement.

---

## § 0 What this block is, and why its subject changed before it was written

`s32a` was built to test one sentence read out of Realtek's own driver for this
exact part: **the vendor never stops the transmit queue.** 量 at the desk, over
60 files under `drivers/net/rtl819x/`, `netif_stop_queue` occurs three times and
all three are `close` paths (`rtl_nic.c:4322`, `:4442`, `:7116`);
`netif_wake_queue` and `NETDEV_TX_BUSY` occur **zero** times. On a full ring the
vendor does this instead (讀 `rtl_nic.c:5161-5171`):

```
	while(swNic_send((void *)tx_skb, tx_skb->data, tx_skb->len, &nicTx) < 0)
	{
		swNic_txDone(nicTx.txIdx);
		if ((tx_retry_cnt++)>RTL_NIC_TX_RETRY_MAX) {
			dev_kfree_skb_any(tx_skb);
			return 0;
		}
	}
```

`NET-67`'s mechanism is that rlxfw does the opposite: it stops the queue, and
the wake path tests the slot that will never free. So `s32a` adds `tx_mode 1`,
which is the vendor's contract, default off.

🔴 **And then block 35 produced a failure that is NOT that one.** 量, cell
`X2` of this same seating, immediately after an `iperf3` run made the board
unreachable:

| reading | `NET-67` (seating 31) | `X2` (tonight) |
|---|---|---|
| `tx_stopped` | **1** | **0** |
| `n_tx_stop` | ≥ 1 | **0** |
| `n_xmit_busy` | ≥ 1 | **0** |
| four `txd` OWN bits | all **engine**-owned | all **CPU**-owned (`D0/E8/00/1A`) |
| `n_tx` | frozen at 26 | **still advancing** (+5 over a probe) |
| on the wire | — | **nothing**: host-side `tcpdump` shows 3 ARP requests out and **zero** frames back |

So tonight the driver was in a completely healthy state and the board was
unreachable anyway. **`tx_mode` cannot fix that, and this block does not claim
it will.**

---

## § 1 The image

| | `s32a` |
|---|---|
| variant | loud, `CONFIG_PRINTK=y` |
| `RECIPE_ID` | **`84385d91`** (`s31L` was `f179cf21`) |
| `vmlinux` | 4,572,389 B (`s31L` 4,572,087 → **+302**) |
| assembled `nfjrom` | **1,180,672 B — the same size as `s31L`** |
| `nfjrom` sha256 | `eee556f46adf9c06…` (`s31L` `a038044da964b833…`) |
| initramfs spec sha256 | **`7130245fbcd92afc…` — byte-identical to `s31L`'s** |

🟢 The initramfs digest matching is the control that says **only the kernel
differs**. 🔴 And the `nfjrom` being the *same size* while its digest differs is
`FW-99`'s lesson a second time: a size cannot tell two images apart here.

---

## § 2 The cells, and the pre-registered prediction for each

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0`
`HOST <prefix> :: <cmd>` runs `<cmd>` in WSL with output to `<prefix>.log`.

Standing rules are block 35's § 3 unchanged: no flash write, no `FLR`, no
`echo write` to `/proc/rtl865x/memory`, no `ifconfig rlx0 down`, host-side pings
only. 🔴 **And no `arm`** — `NET-64` hard-hung this board for 112 minutes with
0 console bytes, and there is no power press available this session.

### 2.1 `B3-BASE` — the six new fields exist and read their defaults

* 推 `tx_mode 0`, `n_tx_full 0`, `n_tx_retry 0`, `tx_retry_max_seen 0`,
  `n_tx_recovered 0`, `n_tx_drop_full 0`, and `n_xmit_ctx 0/0/0`.
* 🔴 **If `tx_mode` is absent from the dump the image is not `s32a`** and every
  cell below is void. `RLXFW-ID0` is the other source and `looprun`'s `A3`
  already read it back as `84385d91`.

### 2.2 `B5-MODE1` — the switch takes, and refuses what it should

* `echo txmode 1` then `echo txmode 9`. 推 the first sets it; the second is
  **refused with `-EINVAL`** and leaves the value at 1.
* 🔴 That second half is the control. A verb that accepts anything would put the
  board silently back in mode 0 and the comparison below would be between two
  identical configurations.

### 2.3 `B6-IPERF` — `iperf3` with the vendor's contract

* 推 **the board becomes unreachable anyway**, reproducing `X2` rather than
  `NET-67`, because § 0's table says the failure tonight is not the one
  `tx_mode` changes.
* 🔴 **If it does NOT become unreachable**, one of two things is true and the
  next cell separates them: either `tx_mode 1` prevented it (which would mean
  `X2` *was* ring-related after all and the descriptor reading was taken too
  late), or `X2` was not reproducible. `B10` is the discriminator.
* 🟢 **`n_tx_recovered` is the reading with the most reach.** Greater than zero
  is the **first evidence in this project that the engine resumes on its own** —
  no measurement has ever been able to see it, because the queue-stop killed the
  interface at the first full ring and nothing transmitted again. Zero, with
  `n_tx_drop_full` large, says the pause outlasts 128 polls.
* ⚠️ If `n_tx_full` reads **0** the whole mode-1 path never executed and `B6`
  says nothing about it. That is a real possible outcome: 量 seating 32, four
  concurrent floods never exhausted four descriptors.

### 2.4 `B10-IPERF` — the control, `tx_mode 0`, same boot

* 推 the same outcome as `B6`. Same-boot, same-image, one field different.
* 🔴 If `B6` survived and `B10` does not, `tx_mode 1` is doing the work and that
  is the result this image was built for.

### 2.5 `B7-DUMP` / `B11-DUMP` — `n_xmit_ctx`

* 推 **softirq-dominated**, because `ndo_start_xmit` is normally entered from
  the qdisc with bottom halves disabled. A hardirq count above zero would be a
  surprise worth its own row.

---

## § 3 VOID conditions, written before the cells run

1. `B4-PING` not 4/4 → everything below is uninterpretable.
2. `B3-BASE` has no `tx_mode` field → the image is not `s32a`, all void.
3. Neither `B6` nor `B10` makes the board unreachable → there is no positive
   control in this block and no comparison can be drawn from two healthy runs.
4. The board becomes unreachable at `B6` and is **not** recovered before `B10`
   → `B10` is contaminated and is recorded as not run rather than as a reading.
   Recovery is `busybox reboot -f` + re-upload, never `arm`.

---

## § 4 What this block does NOT establish

* **Why the engine pauses** (`NET-67` 殘留) — untouched.
* **Why the board went silent on the wire in `X2`** — `MEMCR` reading
  `00007F00` against `00007F7F` at boot, and `PSRP0`/`PSRP3` both losing bit 12
  since boot, are 量 and unexplained. Nothing here reads a vendor register.
* **`D5`** — if `iperf3` prints a number it is a number from a board that may be
  mid-failure, and § 2.3 does not license quoting it.
* **Ring depth.** The vendor runs TX 128 / RX 256 on this board (讀
  `rtl865xc_swNic.h:78-88` `#else` + `DELAY_REFILL_ETH_RX_BUF`, which
  `rtl_types.h:430-434` enables for `CONFIG_RTL_819X` && `CONFIG_RTL_ETH_PRIV_SKB`
  — both `=y` in `config.linux-2.6.30.RTL8196E_88E_GW`) against rlxfw's 4 / 8.
  `s32a` deliberately does not change it: `NIC_TX_DESC`/`NIC_RX_DESC` appear at
  35 sites including the de-sync detector's `(pi - mi) % NIC_RX_DESC`, and a new
  variable inside a measurement instrument is how a seating comes back
  uninterpretable.

---

## § 5 The cells

```
#-- B1-SW   the switch first. Without SIRR's TRXRDY the ping is 100 % loss and
#--         reads as a driver fault.
CAP --out bench/2026-09-21c/B1-SW --send 'echo unlock i-mean-it > /proc/rtl819x-switch ; echo start > /proc/rtl819x-switch' --seconds 25
#-- B2-UP   ndo_open does alloc, arm, request_irq, engine on.
CAP --out bench/2026-09-21c/B2-UP --send 'echo unlock > /proc/rtl819x-nic ; echo netdev on > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --seconds 25
#-- B3-BASE § 2.1 reads THIS cell. No tx_mode field -> everything is void.
CAP --out bench/2026-09-21c/B3-BASE --send 'cat /proc/rtl819x-nic' --seconds 25
#-- B4-PING § 3 clause 1 reads THIS cell.
HOST bench/2026-09-21c/B4-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
#-- B5-MODE1 set 1, then offer 9. § 2.2: the refusal is the control, and the
#--          trailing cat is what shows the value SURVIVED the bad verb.
CAP --out bench/2026-09-21c/B5-MODE1 --send 'echo txmode 1 > /proc/rtl819x-nic ; echo txmode 9 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --seconds 25
#-- B6-IPERF the vendor's contract under the load that has wedged this board
#--          five times out of five.
CAP --out bench/2026-09-21c/B6-IPERF --send 'iperf3 -c 10.1.1.2 -p 5201 -t 10 -i 1 -f m' --seconds 45
#-- B7-DUMP  n_tx_full / n_tx_retry / tx_retry_max_seen / n_tx_recovered /
#--          n_tx_drop_full / n_xmit_ctx. § 2.3 reads THIS cell.
CAP --out bench/2026-09-21c/B7-DUMP --send 'cat /proc/rtl819x-nic' --seconds 25
#-- B8-PING  alive?
HOST bench/2026-09-21c/B8-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
#-- B9-MODE0 back to today's path, same boot, one field different.
CAP --out bench/2026-09-21c/B9-MODE0 --send 'echo txmode 0 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --seconds 25
#-- B10-IPERF the control. § 2.4.
CAP --out bench/2026-09-21c/B10-IPERF --send 'iperf3 -c 10.1.1.2 -p 5201 -t 10 -i 1 -f m' --seconds 45
#-- B11-DUMP
CAP --out bench/2026-09-21c/B11-DUMP --send 'cat /proc/rtl819x-nic' --seconds 25
#-- B12-PING
HOST bench/2026-09-21c/B12-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
```

```cells
bench/2026-09-21c/B1-SW
bench/2026-09-21c/B2-UP
bench/2026-09-21c/B3-BASE
bench/2026-09-21c/B4-PING
bench/2026-09-21c/B5-MODE1
bench/2026-09-21c/B6-IPERF
bench/2026-09-21c/B7-DUMP
bench/2026-09-21c/B8-PING
bench/2026-09-21c/B9-MODE0
bench/2026-09-21c/B10-IPERF
bench/2026-09-21c/B11-DUMP
bench/2026-09-21c/B12-PING
```

---

## § 6 The machine-checkable declaration

```cardnum
cells-fence	12	count bench/2026-09-21c/PREDICTIONS-B38-block36.md ^bench/2026-09-21c/B[0-9]
declared-date	1	count bench/2026-09-21c/PREDICTIONS-B38-block36.md [*][*]declared date 2026-09-21[*][*]
cap-cells	9	count bench/2026-09-21c/PREDICTIONS-B38-block36.md ^CAP -{2}out
host-cells	3	count bench/2026-09-21c/PREDICTIONS-B38-block36.md ^HOST bench/2026-09-21c/
send-over-127	0	count bench/2026-09-21c/PREDICTIONS-B38-block36.md -{2}send '[^']{128,}'
no-shell-subst	0	count bench/2026-09-21c/PREDICTIONS-B38-block36.md -{2}send '[^']*[$]
no-flr	0	count bench/2026-09-21c/PREDICTIONS-B38-block36.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-21c/PREDICTIONS-B38-block36.md -{2}send '[^']*(EW |EB |FLW )
no-burn	0	count bench/2026-09-21c/PREDICTIONS-B38-block36.md -{2}send '[^']*AUTOBURN
no-arm	0	count bench/2026-09-21c/PREDICTIONS-B38-block36.md -{2}send '[^']*echo arm
no-ifdown	0	count bench/2026-09-21c/PREDICTIONS-B38-block36.md -{2}send '[^']*ifconfig rlx0 down
no-memory-write	0	count bench/2026-09-21c/PREDICTIONS-B38-block36.md -{2}send '[^']*echo write
s32a-nfjrom-bytes	1180672	size /home/key/fwre-work/rebuild/imgwork/s32a/s32a/kroot/rtkload/nfjrom
s32a-nfjrom-sha256	eee556f46adf9c06	sha256-16 /home/key/fwre-work/rebuild/imgwork/s32a/s32a/kroot/rtkload/nfjrom
s32a-vmlinux-bytes	4572389	size /home/key/fwre-work/rebuild/r3-4/out/s32a.vmlinux.elf
```
