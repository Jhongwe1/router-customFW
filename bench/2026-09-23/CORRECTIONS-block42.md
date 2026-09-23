# CORRECTIONS — block 42, seating 39

Every departure from the frozen card `PREDICTIONS-B44-block42.md`, and every
defect found in it. The card itself is **not edited** — `check-predictions`
reads its mtime, and repairing a frozen card destroys the evidence that its
predictions were written first.

---

## § 1 🔴 `Z9-D2`'s `--tsv` has no FILE — found before execution

The card reads:

    HOST bench/2026-09-23/Z9-D2 :: /usr/bin/python3 tools/boot-timeline.py --retro bench/2026-09-23 --tsv

量 2026-09-23, before press 1's first `looprun`: `boot-timeline.py: error:
argument --tsv: expected one argument`, exit 2. `--tsv` takes a FILE
(`ap.add_argument("--tsv", metavar="FILE", …)` in `tools/boot-timeline.py`'s
`main`). As written, the cell that § 3.1 makes the first thing computed after
the seating would print a usage line and nothing else.

**What runs instead** — the card's line with the missing FILE supplied, nothing
else changed:

    /usr/bin/python3 tools/boot-timeline.py --retro bench/2026-09-23 --tsv bench/2026-09-23/Z9-D2.tsv

The printed retro table goes to `Z9-D2.log`, as the card's `HOST` form says. The
TSV carries one `loader` row per capture, and it is what § 3.1's **named**
groups (`P1-A`, `V1-WZ`, …) are computed from.

Rejected: dropping `--tsv` — the printed table pools boots by firmware and
class, and § 3.1's groups are lists of named captures, which a pooled row cannot
be split back into; `--tsv /dev/stdout` — two formats interleaved in one log.

⚠️ **How it survived the freeze.** `cardcheck` checks the commands typed at the
board against the image's command table, and re-derives the card's declared
numbers. Nothing reads a `HOST` cell's arguments. This is the second defect of
that class in two cards — block 41's `CORRECTIONS` § 1.2 found `netblast`
options that do not exist — so it is a checker gap, not a slip.

**The check that found it**, run before press 1's `looprun` on the card's own
expansions (macros parsed from the card's definition lines): each of the 13
`hostprobe run` cells with the card's flags, `--target 127.0.0.1`, `--seconds 1`
and a scratch `--out` — exit 0, one `start` and one `stop` event each; each of
the 4 `looprun` cells in `--mode plan` with a scratch `--out-dir` — exit 0;
`MB`'s pipeline on the committed `2026-09-17b/C7-M0` — the card's predicted body
digest `0927be41e91fe4bd` and both of its `flashmap compare` lines, exactly;
`FL`'s `ip neigh flush to …/32` and `P3-TCPD`'s filter on `lo`. `Z9-D2` was the
only one that failed.

---

## § 2 § 2's row for press 1 describes an order § 5 does not have

§ 2, press 1: *cold catch → **Q quiet rounds 1–4** → map → warm catch → **L loud
rounds 1–3** → map → throughput*. § 5's fenced cells — the ones `cells-fence`
(223) and `cap-cells` (112) count — run `P1L` (loud ×3) → `P1-RZ` → `P1Q`
(quiet ×4) → `P1-M0`: loud first, and **one** map. § 3.1's warm group
(`P1L-r02-rz`, `P1L-r03-rz`, `P1-RZ`, `P1Q-r02-rz` …) and the 104th segment's
`LOG.md` entry both describe § 5's order.

**What runs**: § 5, as fenced. **What it costs**: nothing a prediction rests on —
`D7` is loud minus quiet inside one press in either order, and the bracket's
"before" for `V1`–`M1` is `P1-M0` in both descriptions.

---

## § 3 The seven vendor `J 80500000` cells have no staged-head read-back — run as frozen

`CLAUDE.md` (*At the bench*): *"Before `J 80500000`, read back the staged head: a
reset re-stages that address from flash."* `V1-BOOT` … `V7-BOOT` send
`J 80500000` with only `V*-AB`'s `DW 8040D4A0 1` (the burn flag) before them.
Every `looprun` round does read the head back (`S6b`) before its own `J`.

**Nothing is added.** The rule exists so that a re-staged **vendor** image is not
booted by a cell that believes its own upload is there. In `V1`–`V7` no upload
precedes the jump and the re-staged vendor image is the thing the card means to
boot (`LDR-22`); an extra off-card `DW 80500000` would sit between the catch and
the jump of every vendor press for a question those cells do not ask. What
booted is identified afterwards by `V*-BOOT`'s own bytes, predicted
byte-identical to `G6`/`G7` (1,789 B).

**What that leaves unseen**, stated: if a `V*-BOOT` deviates, these captures
cannot tell a staging that did not happen from a staged image that behaves
differently.

---

## § 4 `P1-TR1` stalled; the card's conditional `P1-SRVR` ran

量: `P1-TR1`'s client ran 0–25 s at 17.8 / 17.5 / 17.6 / 16.8 / 15.3 Mbit/s, printed
no 25–30 s line, moved **0 bytes from 30.00 to 70.84 s**, and was killed by
`timeout 70` (exit 124) with no `receiver` figure. `P1-TR1-S1`, run next as the
card places it, reads `n_tx_stop 1`, `n_recov_fire 1`, `n_recov_ok 1`,
`n_recov_fail 0`, `tx_stopped 0`, `engine_on 1`: one `NET-67` stall, rescued by
the compiled-default `recover`, and the console answering.

The card's § 5 prices exactly this: *"A host client that `timeout` kills can
leave the board's server stuck … then, and only then, the off-card restart
`P1-SRVR` … declared in the closeout."* It ran, verbatim from the card, before
`P1-TR2-S0`; this section is that declaration. `P1-TR1` is published as a stall
with its counters, never as a throughput.

### 4.1 `P1-TR2` stalled the same way; the restart is repeated, pre-declared here

量: `P1-TR2` 17.9 / 17.3 / 17.2 / 17.3 / 15.6 Mbit/s over 0–25.28 s, 61.1 MB sent,
then **0 bytes from 30.00 to 60.82 s**, killed by `timeout` (124), no `receiver`
line. `P1-TR2-S1`: `n_tx_stop 2`, `n_recov_fire 2`, `n_recov_ok 2`.

The two `-S1` dumps put the driver's jiffies on the wall clock (Δj 23,564 over
Δt 235.50 s: **HZ = 100**, 量). Dated that way, `recover`'s firings do not line up
with the data stalls: `P1-TR1`'s fired 16 s **after** its client was killed, and
`P1-TR2`'s at t ≈ 7 s, after which the stream ran on at 17 Mbit/s. In `P1-TR2`
the board received 44,110 frames and transmitted 1,163 (ACK-sized, ~40 s⁻¹).
So the end-of-test stall is **not** one `recover` detected; its mechanism is
open (推, to be settled at the desk: a TX stall with too few frames queued to
fill the ring, which is the only thing `recover` arms on).

**From here, every trial whose client `timeout` kills is followed by the card's
`P1-SRVR` command again, verbatim except its `--out`: `P1-SRVR2`, `P1-SRVR3`, …,
run before the next trial's `-S0` and never otherwise.** The card declared the
remedy once; repeating it is the same remedy for the same event, and each run is
an off-card cell under its own name. Rejected: running the next trial without a
restart — a stuck server would consume that trial's fenced name on a refusal.

---

## § 5 🔴 The HOST's usbip transport degraded from 16:11; four readings are contaminated

量 (WSL `dmesg`, read-only, after `P1-UR2` failed with `No route to host`):
`BUG: using smp_processor_id() in preemptible [00000000] code: vhci_rx/890`
per minute — **0 before 16:11**, then 16 (16:11), 98, 78, 62, 17, 3 (16:16) — and
`vhci_hcd: unlink … urb->status -104` in pairs at 16:12:17, 16:12:21, 16:13:03,
16:13:06, 16:13:43, 16:13:46, 16:15:01, 16:15:12, 16:15:15, 16:16:17. The first
warning falls inside `P1-TS1` (16:11:07–16:11:48), the first trial that drove
sustained traffic INTO the host (23.6 Mbit/s). 推: USB requests stuck in the usbip
path and cancelled by the class driver, losing host frames in both directions.

The board's side over the same window: `P1-UR1-S1` → `P1-UR2-S1`, 75 s apart,
`n_rx` +19 and `n_tx` +25, `n_recov_fire` unchanged, `tx_stopped 0`, console
answering. The host's `enxfc19286184c9` counts 0 RX/TX errors and 0 drops — a loss
inside the USB layer is not a netdev error. ⚠️ `ethtool`'s `Duplex: Half` /
`Auto-negotiation: off` on this adapter is **not** a duplex mismatch: this path's
`ethtool` is known not to be a source (`docs/loader-phy-and-switch.md`, the board's
`PSRP3` reads full duplex, 100M, NWay on).

**Contaminated, published only as such**: `P1-TS2` (0.21 Mbit/s), `P1-TS3`
(0.78 Mbit/s), `P1-UR1` (its end-of-test stall overlaps 16:13–16:14), `P1-UR2`
(`No route to host`). **Not contaminated**: `P1-TR1`–`P1-TR3` (16:01–16:10, no
warning in `dmesg` before 16:11) and `P1-TS1`.

**What runs, off-card, before the next fenced cell**: the GbE adapter only
(busid 2-4; never the console's 1-1) detached and re-attached with `usbipd`, then
`Z1-ADDR`'s own command again as `P1-READDR`, then `dmesg` read for new warnings.
Every later trial is bracketed by a `dmesg` count, and a trial during which the
count rises is published as contaminated. Rejected: continuing on the degraded
transport (every later host-side reading would carry it, and the vendor-driver
arm is measured only here in this seating); stopping `P1` for the owner (the
board is answering; what failed is the host, and the next scheduled event is
already the owner's power-off).

### 5.1 🔴 § 5 is RETRACTED — its two signals were misread; the re-attach it ordered ran

§ 5 is left as written because the re-attach was executed on it. 量, a second
source, `journalctl -k` (journald keeps the kernel log past `dmesg`'s ring):

* The `vhci_rx` BUG line fires **all session, whenever traffic flows**: 3 per
  minute at 15:10, 33–85 per minute during `P1a`'s clean `looprun` rounds
  (15:54–15:57), 60 during `P1-TR1` (16:01), **82 during `P1-TS1`** (16:11), which
  ran a clean 23.6 Mbit/s. Its stack is `usbnet_start_xmit` ←
  `usb_hcd_giveback_urb` ← `vhci_rx_loop`: a debug warning on the host's
  ordinary transmit path, not a failure. **§ 5's "0 before 16:11" was `dmesg`'s
  ring buffer**: the snapshot § 5 read began at 16:11:53, because ~20 lines per
  warning had rotated everything older out. A zero from a window that cannot see
  back is not a zero.
* The `urb->status -104` pairs begin at **15:09:35**, inside `Z0-PRE` with the
  board off, and recur where console captures close the port: the CP2102's
  read requests being cancelled, which is what closing a port does.

So nothing shows the host transport degraded. **`P1-TS2`, `P1-TS3` and `P1-UR2`
are board-side readings again**, and `P1-UR1` is not contaminated. The runner's
per-trial bracket (a raw count of the ring) is withdrawn with § 5: a ring count
is not monotonic, and it read 273 → 272 across `P1-UR3`.

**What the re-attach cost**: it bounced the board's port-3 link at
16:18:36–16:18:50, between `P1-UR2`'s failure and `P1-UR3`, which then connected.
Whether the board's network came back by itself or through that link bounce is
not separable from these captures. `P1-UR3` and everything after it on `rlx0`
are published with that stated.

### 5.2 § 5's wall-clock times are `dmesg -T` conversions, shifted ~25 s

`dmesg -T` turns a kernel timestamp into wall time with the **current** offset
between realtime and the kernel clock, and on this host realtime was stepped
forward repeatedly during the seating. 量, the same `-104` pairs by journald's own
stamps (taken at logging time) against § 5's list: 16:11:52 / 16:12:17,
16:11:55 / 16:12:21, 16:12:38 / 16:13:03, 16:12:42 / 16:13:06, 16:13:18 /
16:13:43, 16:13:21 / 16:13:46, 16:14:36 / 16:15:01, 16:14:47 / 16:15:12,
16:14:50 / 16:15:15, 16:15:51 / 16:16:17 — § 5's are 24–26 s late, and by the
journal's times **every pair falls on a console capture's close** (`P1-TS1-S1`,
`P1-TS2-S0`, …, `P1-UR2-S1`), none inside an `iperf3` cell. § 5's per-minute
BUG histogram carries the same shift. The host's clock steps are a finding of
their own, recorded outside this file.

---

## § 6 Everything run beside the card, complete

| what | when | why | where it is |
|---|---|---|---|
| `P1-SRVR` | 16:04:41 | the card's own conditional restart, after `P1-TR1`'s client was killed | § 4; `bench/2026-09-23/P1-SRVR.*` |
| `P1-SRVR2` … `P1-SRVR6` | 16:09:24 · 16:10:53 · 16:14:36 · 16:21:19 · 16:22:48 | the same restart, verbatim but its `--out`, after `P1-TR2`, `P1-TR3`, `P1-UR1`, `P1-UR3`, `P1-US1` | § 4.1 |
| the host GbE adapter detached and re-attached (`usbipd`, busid 2-4 only) | 16:18:36–16:18:50 | § 5's diagnosis, since retracted (§ 5.1) | § 5, § 5.1 |
| `P1-READDR` | 16:19:04 | `Z1-ADDR`'s command again after the re-attach | § 5; `bench/2026-09-23/P1-READDR.log` |
| host read-only diagnostics (`ip -s link`, `ethtool`, `dmesg`, `journalctl -k`) | 16:16–17:05 | § 5 / § 5.1 / § 5.2 | quoted in § 5–5.2; not under `bench/` |
| `Z9-D2`'s `--tsv` file | 17:41:48 | § 1 | `bench/2026-09-23/Z9-D2.tsv` |

Nothing else was sent to the board. No cell of the fence was run twice, none
was skipped: `check-predictions` read **223 of 223** after `P3-TCPD` ended
(17:44:51). Nine of the 24 fenced `iperf3` trials are readings of failure
rather than of throughput — six whose end-of-test exchange never completed
(`P1-TR1`–`TR3`, `P1-UR1`, `P1-UR3`, `P1-US1`) and three the board never
answered (`P1-UR2`, `P1-US2`, `P1-US3`, `No route to host`) — and are
published as such.
