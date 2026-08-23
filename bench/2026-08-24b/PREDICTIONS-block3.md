# Block 3 — did the board survive the console dropping out?

Written while `/dev/ttyUSB0` is absent, before the CP2102 is re-seated and before
any command reaches the board again.

```cells
bench/2026-08-24b/CONT
```

## What happened, so the reading is not misattributed

*Measured, Windows and WSL:* at WSL uptime `10679.98 s` = **04:33:57** the
CP2102 left the host's USB bus. `dmesg`: `vhci_hcd: connection closed` → `release
socket` → `usb 1-1: USB disconnect` → `cp210x ttyUSB0 ... disconnected`. Windows
`usbipd list` moved `1-1` out of *Connected* entirely and
`Get-PnpDevice -PresentOnly` finds no `VID_10C4`, so this is a physical
disconnection and not a usbip socket failure alone. WSL did **not** restart
(uptime continuous from 01:35:57).

Block 1's last capture, `E9b`, landed at **04:26:33.51**. The drop is **7 min 24
s of pure idle** later, and the operator pressed the button after that. So the
drop is not attributable to the button, to the cable moves, or to any command.

The one command aimed at the board during the outage, `B7c`, never left the host:
`console-capture.py` validates `--send` and then opens the port, and the open is
what failed — `_check_send` runs above `serial.Serial()` for exactly this reason
(the ordering `N4` tests). Nothing was half-sent.

## `CONT` — `DW 8040DCE8 1`, and the prediction is a formula rather than a value

`E1b`/`E2b` measured the tick rate as **100.0078 Hz** (25,329 counts over 253.270
s of `.log` mtime) and fixed the counter's zero at **03:32:51.703**, from two
independent reads that agree to 7 ms:

| read | tick | mtime | implied zero |
|---|---|---|---|
| `E1b` | 252,061 | 04:14:52.1168 | 03:32:51.703 |
| `E2b` | 277,390 | 04:19:05.387 | 03:32:51.710 |

Both the sample instant and the mtime carry the same fixed offset for the same
command (echo, parse, 58-byte reply), so it cancels: this cell sends the same
`DW 8040DCE8 1`.

- **Predicted**: `tick = (mtime(CONT.log) − 03:32:51.703) × 100.0078`, to within
  **±5 counts** (±50 ms), allowing for host scheduling jitter.
- **Refuted by — and this is the outcome that ends the boot**: a tick far below
  that, i.e. the counter restarted. Then the board reset when the CP2102 went
  away, every DRAM-resident thing about this power cycle is gone, and `bench/`
  needs a new directory because the rule there is one directory per power cycle.
- **Also refuted by**: a tick *above* the prediction by more than the tolerance —
  the rate is not 100.0078 Hz, and `E1b`/`E2b`'s agreement was a coincidence of
  two readings taken 253 s apart. This cell is a third point on the same line, at
  a much longer baseline, so it also sharpens the frequency.
- **Also predicted**: words 2, 3, 4 = `001E8000 0ED80000 8040A2B4`, unchanged
  from `E1b`, `E2b` and seating 1's `E1`. 71 bytes.

**A note on what this cell is worth beyond today.** The tick counter is a
free-running witness of continuous execution with a measured rate and a measured
zero. Any later question of the form *"is this the same boot?"* is answerable by
one read costing 71 bytes, with a predicted value. That is what `D2b` is trying
to do with a scratch word in DRAM, and this one does not depend on DRAM
retention at all.
