# PREDICTIONS — block 42, seating 39 (`P2-3`, seating A: both firmwares, cold and warm, through one script, and the throughput matrix)

**declared date 2026-09-23** — **twelve power presses**, every one of them on this
date, and the last capture before midnight: a seating that crosses midnight is
two directories and two cards (`capdate` `D7`/`D8`, `SPEC.md` `FW-120` — card
`B35` declared a day none of its captures happened on).

Marks: **量** measured on the device · **讀** read out of code or a dump ·
**推** inferred, pending a measurement.

---

## § 0 Honesty notes, written rather than left to be found

**① Four instruments read silicon for the first time on this card, and the
images come out of a build chain that changed the day the card was written.**
`looprun` 1.2's rounds (`LOOP-3`, `FW-118`), `hostprobe` 1.2 (`FW-116`),
`console-capture`'s `t0_mono`/`end_mono` (`FW-115`), and `boot-timeline`'s rlxfw
landmarks over an `/init` that brings the LAN up. The images were built under
the two declaration gates (`FW-121`) and assembled under the tripwire
(`FW-122`). Each has desk controls; none has a reading from the board. A cell that
fails because an instrument is wrong is a finding about the instrument and is
reported as that.

**② Nine of the twelve presses boot the vendor firmware, and a vendor boot can
write flash.** 讀: it does so only when its config self-test fails, and then only
its own config sectors (`P2` settled item 5; seating 17's bracket read 0 bytes
changed). The owner accepted the runs on 2026-09-23 with a flash `map` before and
after every block that can boot it. **A difference in any bracket stops every
later vendor boot until the owner has read it** (`P2` stop-loss).

**③ The first loud boot with the bring-up in `/init` has never been captured.**
Every committed bring-up was typed by hand on a quiet image. 讀: the NIC and
switch drivers contain no `printk`, and every `RLXFW-N-*`/`RLXFW-SW-*` mark is
printed in process context — `ndo_open`, the `/proc` write handler, alloc, arm,
engine — so all of it is out before `exec /bin/sh`; the loud `.config` has
`CONFIG_IPV6` unset, so no `ADDRCONF` line can arrive late. 推 nothing lands
between `job control turned off` and `# `.

**④ The build manifest's `initramfs_sha256` digests the SPEC — paths, modes,
owners — and not what was packed** (`FW-123`). 量 2026-09-23: the specs of the last
images and of these are byte-identical (`7130245fbcd92afc`) while `/init` went from
988 B to 2,153 B. So cards `B35`, `B38`, `B39` and `B42` stated *only the kernel
differs* on a digest that cannot see contents; the content records say they were
right. This card identifies the userspace by `initramfs_manifest_sha256` and the
whole image by the `nfjrom` pin.

---

## § 1 The images

| | `p2q` | `p2l` |
|---|---|---|
| variant | quiet, `CONFIG_PRINTK=n` | loud, `PRINTK=y`, `PRINTK_TIME=y` |
| `RECIPE_ID` | **`a2c56bc8`** | **`a2c56bc8`** — the same: `ID0` cannot tell variants apart (`FW-99`); the pin can |
| `vmlinux` | 4,468,487 B, `c5e2cfdba7730d47…` (`s100a` + **1,536**) | 4,575,403 B, `39a4db228131f697…` (`s100L` + **1,536**) |
| gates (`FW-121`) | `kconfig-delta check [quiet]` green, `rlxfw-marks verify` green | `[loud]` green, green |
| `nfjrom` (`rtkimage` record, tripwire CLEAN) | **1,155,072 B**, `4972edbadd2655a8…` | **1,181,696 B**, `888c930aa31763d9…` |
| initramfs content (`initramfs_manifest_sha256`) | `51ea1604c7c163f3…` | the same |
| driver | `rtl819x-nic 1.4` | the same |

量 **the chain, checked by this card's own `cardnum` rows at freeze**: each
manifest says `verdict green` with that `vmlinux_sha256`; each `rtkimage` record
names the same vmlinux, that `nfjrom_sha256` and a CLEAN tripwire verdict; each
`nfjrom` on disk has that digest; `looprun`'s `--image-sha256` pins it again before
the port opens. 量 the build is reproducible: both images were rebuilt the same
day and came out byte-identical.

**What is new against the images seating 38 ran, and each is a compiled default:**

| | before | now |
|---|---|---|
| `recover` (the `NET-67` stall detector) | typed | **compiled on** (`NET-107`) |
| `/init` | mounts, execs a shell | **brings the LAN up first**: switch unlock + start, NIC unlock + `netdev on`, `ifconfig rlx0 10.1.1.3 up` (`P2` settled item 3) |
| vendor Ethernet `open` | refuses (`0007`, `NET-106`) | **whole** — `CONFIG_RLXFW_VENDOR_ETH_OPEN=y`, `0007`'s own switch back at its Kconfig default, for `D5`'s vendor-driver arm |
| boot marks | … `N6` | … `N6`, **`N7=00000011`** = `ph_follow << 4 \| recov_mode` |

---

## § 2 The twelve presses, in order

| press | block | what boots, and how its loader second is captured | what it feeds |
|---|---|---|---|
| **1** | `P1` rlxfw | cold catch (`esc`) → `Q` quiet rounds 1–4 (round 1 at the caught prompt; 2–4 `busybox reboot -f`, `esc_after`) → `map` → warm catch → `L` loud rounds 1–3 → `map` → throughput on `rlx0`, handover, throughput on `eth4` | `D2` rlxfw cold ×1, warm ×6; `D7` quiet ×4 vs loud ×3; `D8` rlxfw and the channel offset; `D5` (a) + (b) both drivers; `D6`; `D4`'s `ps`; `NET-109` before traffic |
| **2–4** | `V1`–`V3` vendor cold | cold catch (`esc`) → **`J 80500000`** — the image the loader staged from flash at this reset (`LDR-22`) | `D2` vendor cold ×3; `D8` vendor ×3; `D4` readiness per port; `D5` (a) on the vendor; the port census |
| **5** | `M1` vendor cold | **listen-only**, autoboot through the loader's ESC window | the capture-mode control, cold; the vendor's natural boot, power to `boa` |
| **6** | `P2` rlxfw | cold catch → quiet rounds 1–2 → `map` | bracket after `V1`–`M1`, before `V4`–`M2`; `D2` rlxfw cold ×1, warm ×1; `D5` (a), second series |
| **7–10** | `V4`–`V7` vendor warm | cold catch → **`J BFC00000` with `--esc-after`** (warm catch, `esc_after`) → **`J 80500000`** | `D2` vendor warm ×4; `D8` vendor warm ×4 |
| **11** | `M2` vendor warm | cold catch → `J BFC00000` **listen-only** → the loader's warm reset autoboots | the capture-mode control, warm |
| **12** | `P3` rlxfw | cold catch → quiet rounds 1–2 → `map` | bracket after `V4`–`M2`; `D2` rlxfw cold ×1, warm ×1; `D5` (a), third series |

🔴 **Why every vendor boot but two starts from a caught prompt.** The loader
runs the same code whatever boots next, so the only thing that could make
`D2`'s two columns differ is how they were captured — and 量 over the corpus,
that is already not zero: a boot captured while ESC streams and one captured
while only listening differ by **2.6–8.6 ms inside one directory** and 12.5 ms
pooled (cold `esc` n=48 median 0.5809 s, cold `listen` n=8 0.5684 s), the size
of the band itself. Every rlxfw boot has to be caught. So the vendor's boots
are caught too, and then started with `J 80500000`: after any reset the loader
has staged the vendor image there, and a `J 80500000` boot is **byte-exact with
an autoboot from `decompressing kernel:` on** (`LDR-22`). Both columns are then
`esc` when cold and `esc_after` when warm, and `D2` compares like with like.
`M1` and `M2` measure the one thing this removes: the listen-vs-ESC shift,
inside this seating, one cold and one warm.

🟢 **`J BFC00000` from a prompt is a warm reset, measured.** 86 committed captures
sent it; 82 carry `C-8`'s `Reboot Result from Watchdog Timeout!` and none prints
`Booting` without it (the other four never rebooted). `busybox reboot -f`: 80, 69,
none. So `V4`–`V7`'s catches are warm in the same sense as rlxfw's rounds 2–N.

⚠️ **Every block that can boot the vendor is bracketed — a `looprun` block
included** (`notes/dev-loop.md` § 19): a round whose catch misses lets the loader
autoboot the vendor, and `looprun`'s `A0a` stops the block. The seating's first
bracket can only follow its first rlxfw boot, so that bracket's "before" is the
last map on record and `tools/flashmap.py predict --level 0` against the
2026-08-16 dump.

---

## § 3 What this seating decides, and what would refute each

### 3.1 🔴 `D2` first — the identical-code control, computed before any comparison is read

The loader's `Booting` → banner is the same code whichever firmware follows, so
it must measure the same in both columns. **This is computed at the desk from
this seating's captures before any rlxfw-vs-vendor number is looked at**
(`Z9-D2`), and seating B is not booked if it fails (`P2` stop-loss).

| group | captures | mode | n |
|---|---|---|---:|
| rlxfw cold | `P1-A`, `P2-A`, `P3-A` | `esc` | 3 |
| vendor cold | `V1-A`, `V2-A`, `V3-A` (each followed by `J 80500000`) | `esc` | 3 |
| rlxfw warm | `P1L-r02-rz`, `P1L-r03-rz`, `P1-RZ`, `P1Q-r02-rz`, `P1Q-r03-rz`, `P1Q-r04-rz`, `P2Q-r02-rz`, `P3Q-r02-rz` | `esc_after` | 8 |
| vendor warm | `V4-WZ`, `V5-WZ`, `V6-WZ`, `V7-WZ` (each followed by `J 80500000`) | `esc_after` | 4 |
| loader-only cold (context) | `V4-A`…`V7-A`, `M2-A` | `esc` | 5 |
| mode control, cold | `M1-BOOT` | listen | 1 |
| mode control, warm | `M2-BOOT` | listen | 1 |

**Bands, written now from the retro spread** (推, derived over the 249 committed
loader boots, `notes/boot-time.md`; `CLK-31`, `CLK-33`):

* **warm vs warm: |median(rlxfw warm) − median(vendor warm)| ≤ 10 ms.** The null
  is every equal-half split of the 11 directories with 4–12 warm boots, 1,865
  splits: p95 5.4 ms, **p99 10.1 ms**, max 12.2 ms; the largest time-ordered
  half-split seen is 14.7 ms. Both columns have ≥ 4 boots, which is what that
  null was computed for.
* **cold vs cold: |Δ median| ≤ 25 ms, and this is a limit, not a
  characterisation**: one committed directory has ≥ 4 cold boots, its time-ordered
  half-split is 25.3 ms, and cold scatter inside one directory has reached 48.7 ms.
  With n = 3 per column, a cold difference inside 25 ms says the method did not
  break; it does not say the cold loader is characterised.
* **cold is never compared with warm** (pooled warm − cold median 13.1 ms, 9.1 ms
  of it `C-8`'s 35 bytes).

🔴 **Refutation** (the plan's): a difference outside the band means the method
is broken, and no comparison is published until it agrees. With both columns now
captured in the same mode, the candidates left are the other two the plan named —
cold and warm pooled (prevented: `C-8` splits them in every capture) and drift
across the seating — and a third this card adds: **a seating-long drift of the
loader itself.** 量, the one committed directory with four cold catches moved
monotonically 0.5370 → 0.5858 s over 80 minutes (`2026-08-31c`, `K-A` → `K4-A`).
The groups are interleaved in time on purpose (P, V, P, V, P) so such a drift
lands in both columns; it is also reported per press.

**The mode controls, predicted without a sign** (推): 量 the corpus has read
listen − `esc` at −2.6 ms (cold, one directory), +8.6 ms and +5.7 ms (warm), and
−12.5 ms pooled across seatings. So `M1-BOOT` against the cold `esc` groups and
`M2-BOOT` against the warm `esc_after` groups are each predicted within **±10 ms**,
sign not predicted. A shift beyond that is the confound this plan removed from
`D2`, measured where it can be seen, and it re-reads every committed D2-shaped
comparison that mixed modes.

### 3.2 The boot captures — hard byte predictions, through the tool that normalises them

`tools/bootbytes.py` model (`:19`): bytes = constant + Σ marks + variable-width excess.
Derived from the last boot of each variant, then the exact deltas:

| | base | + `N7` | + bring-up | = prediction |
|---|---:|---:|---:|---|
| **`p2q`** (every `P*Q-rNN-boot`) | 1,874 (`F179CF21`, `2026-09-21b/A0-boot`; all 10 of the four newest 71-mark quiet images) | +19 | +224 | **2,117 B, exact** — the quiet image has no variable-width field (0 of 111 quiet captures) |
| **`p2l`** (every `P1L-rNN-boot`) | 7,705 (`s100L`, `2026-09-22b/X20-boot`, e = 0) | +19 | +224 | **7,948 + e B**, e = 0…12 from the twelve `tmpReg[0x%x]` fields, read out of the capture; normalised **7,948 exactly** |

`+19` is `RLXFW-N7=00000011\r\n`; `+224` is `rlxfw: lan bring-up\r\n` (21), the
switch's `SW-UNLOCK` 17 and `SW-START` 16, the NIC's `N-UNLOCK` 16 and `N-NDREG`
15, the five marks `ifconfig … up` prints — `N-ALLOC=` 24, `N-ARM=` 22,
`N-ARMR=` 23, `N-ENGON=` 24, `N-NDOPEN` 16 — and `rlxfw: lan up, rlx0
10.1.1.3\r\n` (30). 量 in 8 of 8 hand-typed captures those verbs print nothing
but their marks; `/init` has no line editor, so neither the echo nor its
column-80 `\r\r\n` exists here.

Every rlxfw boot also carries **`RLXFW-ID0=A2C56BC8`** (looprun's `A3`) and
**`RLXFW-N7=00000011`**: `ph_follow` 1 and `recov_mode` 1, the compiled defaults.

🔴 Refuted by: a different count after normalisation. The one mechanism named
that makes a capture **short** (讀 vendor `early_printk.c:46-55`: after 30,000
polls `prom_putchar` resets the TX FIFO and drops the character) would read
1–17 B short with a mark missing a character. ⚠️ `bootbytes` `K2` will see a new
constant on these captures — `SW-UNLOCK` can interleave with the `lan bring-up`
line (`FW-47`), and an interleaved mark does not parse as a mark — so the card
predicts the **total**, never the constant.

### 3.3 `D7` — loud minus quiet, inside one press

Bytes (量 over committed captures): the whole loud−quiet difference lies between
kernel entry and `rlxfw: init running`, and it is **5,831 + e B**. Rate: `FW-70`'s
sustained Linux-side band, 88.4–92.7 % of 3,840 B/s = **3,394.6–3,559.7 B/s**.

* **Prediction** (推): Δ(`kernel.total`, loud − quiet medians) = **f_A × 1.638–1.718
  s** at e = 0 (1.641–1.721 at e = 12), f_A = this seating's own loader `booting`
  median / 0.353718.
* **The test, fixed before power.** The plan's words are *"exceeds the quiet
  one's by its extra console bytes ÷ the sustained rate measured in FW-70, within
  FW-32's residual."* `FW-32`'s residual is what bytes did not explain: **0.250 s**
  of a 1.711 s difference. So `D7` holds when the measured difference lies in
  **[f_A·ΔB/3,559.7 − 0.250, f_A·ΔB/3,394.6 + 0.250] s**. 量 the corpus's only
  same-recipe pair inside one directory (`2026-09-21b`, `F179CF21`) sits at
  −0.067…+0.059 s of the rate band, so the test can pass; read instead as
  "residual inside [0.089, 0.250]", the corpus's own pair would fail, and that
  reading is rejected here, before the measurement, not after it.
* **Beside it, not instead of it:** the implied rate f_A·ΔB/ΔT, which the corpus
  pair puts at 89.4 % and 92.1 %, inside `FW-70`'s band.

### 3.4 `D8` — network up, and the channel offset

**The host's ARP state is part of the measurement, so it is fixed.** 10.1.1.1 is
answered by the loader after `IPCONFIG` (`56:0a:01:01:01:e8`) and by the vendor
firmware with the unit's own address; a host entry holding the loader's MAC
makes the vendor's first reply late by up to ~30 s of the host's own timers
(推 from the host's measured `base_reachable_time_ms 30000`,
`delay_first_probe_time 5`, `retrans_time_ms 1000`, `ucast_solicit 3`,
`mcast_solicit 3`). So **before every boot whose network-up is read, the host's
entry for that boot's address is flushed** (`FL`), and both columns run under
the same host regime: the kernel's own ARP broadcast about once a second.

* **Network up** = the first ICMP echo reply `hostprobe` records after the boot's
  jump, **published as the bracket [last unanswered ARP broadcast, the answered
  one], 1.00–1.09 s wide** — not a point. Stamped with ping's own `-D` realtime
  converted to the probe's clock (`ping_real − (start_real − start_mono)`), the
  probe's read time as the cross-check.
* **Void, decided now:** a boot whose `--neigh` record shows
  `56:0a:01:01:01:e8` valid between the flush and the first reply, or whose first
  reply has no unanswered broadcast before it (no lower edge).
* **Readings with a cached entry** (rlxfw rounds 2–N, where the host still holds
  `rlx0`'s fixed `02:52:4c:58:46:57` from round 1) are published separately and
  labelled by the regime `--neigh` recorded; they are not pooled with flushed ones.
* **The channel offset** (the plan's): fifteen `P1-OFF*` cells, each one `sleep 1`
  then one `traceroute` datagram to 10.1.1.2:50000, where `P1-OFF-HP` listens.
  The console event is the first byte of `traceroute`'s header line — written and
  flushed immediately before the datagram (讀 busybox 1.13.4 `traceroute.c`,
  `:1210-1233`) — timed by `FW-35`'s rule; the network event is the datagram's
  arrival. offset_i = t_udp − t_console. **Repetition `P1-OFF01` is excluded now**
  (its UART may still hold the echo). **"Stable to within one byte time" is read
  as the range of offset_i over `P1-OFF02`–`P1-OFF15` ≤ 260.4 µs** — the plain
  reading of the plan's words, fixed before the reading. 推 it **fires**: 量 the
  console's reads arrive every 0.99 ms carrying 3 bytes (median), so a byte's
  stamp is quantised to ~1 ms, and 52–89 % of committed post-silence bursts admit
  no constant read latency. Then, as the plan says, network up is published only
  as a console-side bound — which costs `D8` nothing material: its own bracket is
  a second wide.

### 3.5 `D5` — throughput

(a) **ICMP at fixed payloads, one host script, both firmwares**: `ICMP` below at
56, 256, 512, 1,024 and 1,472 bytes (none fragments at MTU 1,500), 20 echoes
each at 50 ms, n = 3 per firmware (rlxfw `P1`/`P2`/`P3`, vendor `V1`/`V2`/`V3`).
推 0 % loss, and 56-byte rtt 1.9–3.5 ms for both (the committed 4-echo pings).

(b) **`iperf3` 3.1.3**, the board's server backgrounded, the host's MIPS client under
`qemu-mips-static` with `timeout 70`, 30 s trials, n = 3 each of: TCP board
receives, TCP board sends (`-R`), UDP board receives and UDP board sends, both
`-l 1400 -b 20M -i 1`. On rlxfw's driver (`rlx0`), then on the vendor's driver on
this kernel (`eth4`, after the handover). Board CPU from `/proc/stat` read before
and after every trial, no verb typed. 推:

| | rlxfw `rlx0` | vendor driver `eth4` |
|---|---|---|
| TCP board receives | **16–18 Mbit/s** (`NET-102`: 17.03 / 17.76 / 17.09 with `recover` typed; `recover` is now the default) | first reading |
| TCP board sends | 20–25 Mbit/s, weak (`NET-85`: 23.3 on driver 1.1, abnormal end) | 22–27 Mbit/s (`NET-84`: 25.4, one 10 s run) |
| UDP either way | **first reading on any driver** — every committed UDP rung wedged the old driver; a wedge now should be recovered, and `n_recov_fire` says | first reading |

Every rlxfw figure is published beside that trial's `n_tx_stop` and
`n_recov_fire` (`NET-107`): a throughput from a driver that is being rescued is a
duty cycle unless the rescues are counted with it. (c) ⊘ `iperf3` on the vendor
firmware — it has no shell.

### 3.6 `D6`, `D4` and `NET-109`

* **`D6`**: `P1-FREE` — the first committed `free` and `/proc/meminfo` on rlxfw
  (推 `MemTotal` 26.9–27.0 MB; no prediction is claimed). Sizes are 讀 in § 1.
* **`D4`**: rlxfw — `P1-PS` plus the initramfs content record
  (`initramfs_manifest_sha256` `51ea1604…`). Vendor — each daemon's console line in
  the boot captures (`boa: starting server pid=350, port 80`,
  `MiniIGD v1.09.1 (2018.01.10-06:58+0000).`), `boa`'s readiness as the first
  `tcp:80:ok` in each `V*-HP`/`M*-HP`, and **one TCP census**, `V1-NMAP`, an
  unprivileged connect scan of every port. 推 80 open; everything else is a first
  reading. `miniigd`'s port is configured, not compiled in (`port %d`), so its
  readiness waits for seating B, which will know the port list.
* **`NET-109`**, the reading before `iperf3` traffic: `P1-N0` (the driver's own dump)
  then `P1-AC0` (`asicCounter`), nothing typed between. Not traffic-free — `/init`
  brought `rlx0` up and `P1-HP` pinged — so 推 the healthy state
  `NET-65` measured: CPU-port `Rcv 0 bytes` while `CRCAlignErr` equals port 3's
  egress count. The committed healthy readings (`2026-09-20/D12-AC0`,
  `2026-09-20b/X2-asic`, `2026-09-21e/V1-ACNT`) are the comparison.


### 3.7 Segment timing — the retro table's prediction, carrying the seating factor

`CLK-32`: every segment of one image moves with its seating's loader `booting`
median, so each is predicted as **T_A = k · B_A + f_A · Δ**, with k the segment
over its directory's loader `booting` median in the nearest committed boots, B_A
this seating's own median (known after its first catches), B_REF = 0.353718 s (the
pooled warm median, n = 193), f_A = B_A / B_REF, and Δ what the new image adds.
Before power f_A ∈ [0.953, 1.045] (`CLK-31`'s 16 warm-seating medians). Δ: `N7` is
19 B at `FW-70`'s rate, 5.34–5.60 ms, in `kernel.late` (the 300-jiffy wait is re-based
after `TA6`, so it does not absorb it); the bring-up is 62.7 / 67.0 / 80.6 ms
(low / mid / high: its 194–224 serialised bytes at `FW-70`'s rate, plus
`ifconfig`'s launch gap of 6.7–10.2 ms and its return gap of 1.5–2.4 ms, 量 from the
hand-typed captures' `.timing`), in `user.ready`. 推 throughout:

| image | `kernel.total` at f = 1 | `user.ready` at f = 1 | `J` → prompt | band over k, Δ and f |
|---|---:|---:|---:|---|
| `p2q` (k over `F179CF21` + `EDC94765`, n = 10) | 9.385 s | 0.112 s | **f_A × 10.72 s** | 10.15–11.71 s |
| `p2l` (k over `s100L`, n = 2) | 11.12 s | 0.113 s | **f_A × 12.48 s** | 11.84–13.12 s (11.67–13.19 over all 18 loud boots) |

Arithmetic, one line each: 30.1078 × 0.353718 + 0.0725 = 10.722 s;
35.0836 × 0.353718 + 0.0725 = 12.482 s; 26.5172 × 0.353718 + 0.0055 = 9.385 s;
0.1274 × 0.353718 + 0.0670 = 0.112 s. **The quiet image's `user.ready` goes from
0.044 s to 0.112 s**: that is the LAN coming up inside `/init`, priced here before
it is measured.

**The vendor column** (`CLK-33`, 量 over `G6`, `G7`, `H2a2`, `K-J`): `kernel.total`
warm 6.8895–6.9817 s raw (**f_A × 7.14 s**), cold 6.945 and 7.155 s; `J` → `boa`
25.654–26.126 s raw. Its userspace is not shown to follow the seating factor (its
k spread, 2.7 %, is no smaller than its raw spread, 2.9 %), so **the raw range is
the prediction for `J` → `boa`** and the k form (26.5 s at f = 1) is the second
reading. `Init bridge interface...` follows `sysconf wlanapp kill wlan0` by
0.82–0.89 s in every complete boot; a stop there is `X8-WAIT`'s shape.

---

## § 4 Standing rules

🔴 **No flash write.** No `FLW`, `EW`, `EB`, no `AUTOBURN` with a non-zero value,
no `FLR`; every upload is `looprun`'s, which refuses `--skip S5b` and requires
`00000000` read back out of `0x8040D4A0` before it uploads. `cardcheck` refuses
the four verbs on this card (`FW-113`); the card carries no `owner-yes` fence and
needs none.
🔴 **A map before and after every block that can boot the vendor, a `looprun`
block included; any difference in a bracket stops every later vendor boot until
the owner has read it.**
🔴 **The host's entry for 10.1.1.1 is flushed before every `looprun` block** (`P1-FL`,
`P2-FL`, `P3-FL`). After a vendor boot that entry holds the unit's own MAC, and
`looprun`'s `S5c` prints the entry verbatim: without the flush, `H601` bytes would
land in a file under `bench/`. The same reason keeps `tcpdump` off every press but
`P3`, and `-e` off `tcpdump` altogether.
🔴 **No cell touches the reset button while the vendor firmware runs** (`FW-40`, `FW-62`).
🔴 **`ifconfig rlx0 down` once, in `P1-DOWN`, as the handover; `rlx0` is not
re-opened in that boot** (`NET-58`).
🔴 **Every `--send` is at most 127 characters and carries no `$`.** Board `ping`
ignores `-c` (`NET-26`); every ping here is host-side.
⚠️ **`J 80500000` and `J BFC00000` without `--esc-after`, in nine cells, is the
exception, and it is declared.** `CLAUDE.md` gives a cell that jumps `--esc-after`
so the prompt is caught instead of the vendor booting; in `V1`–`V7-BOOT` the
vendor booting is the measurement, and `M2-BOOT` exists to let the loader's warm
reset autoboot it. The rule's purpose — no boot the card did not plan — is kept by
the maps around the blocks. Streaming ESC into the vendor's console is not done:
it has no shell and what ESC does to its boot is not measured.
⚠️ **A catch followed by a `J` gets a `DW 8040D4A0 1` in between** (`*-AB`): 量 the
first command after an ESC-streaming capture that was killed read
`Unknown command !` (`2026-09-22b/A0-rz`), and 2 of 84 at-prompt sends failed
that way. The `DW` absorbs it and reads the burn flag, **00000001** after any
reset with no rescue (`B6`).
⚠️ **The seating ends before midnight**, or it stops at a press boundary and the
rest is a new card.
🟢 **A background `hostprobe` (`HOST&`) is started and its `start` line is in
`<prefix>.events` before the next cell runs** (`FW-116`).

---

## § 5 The cells

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400`
`LR` = `/usr/bin/python3 tools/looprun.py --mode bench --out-dir bench/2026-09-23 --skip S2,S3,S4 --recipe-override a2c56bc8`
`QIMG` = `--image /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/kroot/rtkload/nfjrom --image-sha256 4972edbadd2655a815e80606a83b8e5e5987334dfd1c990fcc806291eaf182ae`
`LIMG` = `--image /home/key/fwre-work/rebuild/p2-2/rtk/p2l/rlxfw/kroot/rtkload/nfjrom --image-sha256 888c930aa31763d9ed217783d4c9faa82c9652574a18948e35b379d88e8c31fc`
`HP` = `/usr/bin/python3 tools/hostprobe.py run`
`FL <ip>` = `sudo -n ip neigh flush to <ip>/32 dev enxfc19286184c9 ; ip -4 neigh show <ip> dev enxfc19286184c9 | wc -l` — prints `0`; never `-s -s`, which would print each flushed entry's address
`ICMP <ip>` = `for s in 56 256 512 1024 1472; do ping -I enxfc19286184c9 -c 20 -s $s -i 0.05 -w 10 -q <ip>; done`
`IPERF` = `timeout 70 qemu-mips-static /home/key/fwre-work/iperf3-port/iperf3`
`MB <cap>` = `tr -d '\r' < <cap>.log | sed -n '/^[0-9A-F]\{6\} /,/^map_lines /p' | sha256sum ; FWRE_WORK=/home/key/fwre-work /usr/bin/python3 tools/flashmap.py compare <cap>.log`
`HOST <prefix> :: <cmd>` runs `<cmd>` on the workstation with its output to `<prefix>.log`;
`HOST& <prefix> :: <cmd>` the same in the background, and the next cell waits for
its `start` event in `<prefix>.events`.

### Before press 1

```
CAP --out bench/2026-09-23/Z0-PRE --seconds 3
HOST bench/2026-09-23/Z1-ADDR :: sudo -n ip link set enxfc19286184c9 up ; sudo -n ip addr replace 10.1.1.2/24 dev enxfc19286184c9 ; ip -4 addr show dev enxfc19286184c9
```

* `Z0-PRE` — the pre-flight with the board off: three artefacts and ~3.08 s, never
  its exit code (a healthy 0-byte run exits 1).
* `Z1-ADDR` — `inet 10.1.1.2/24`; the address does not survive a re-attach.

### Press 1 — `P1`, rlxfw: loud rounds, quiet rounds, a map, then the quiet image's measurements

```
CAP --out bench/2026-09-23/P1-A --esc 180 --esc-period 0.002 --seconds 200
HOST bench/2026-09-23/P1-FL :: FL 10.1.1.1 ; FL 10.1.1.3
HOST& bench/2026-09-23/P1-HP :: HP --out bench/2026-09-23/P1-HP --target 10.1.1.3 --seconds 900 --icmp --icmp-interval 0.05 --neigh
HOST bench/2026-09-23/P1L :: LR --cell P1L LIMG --iterations 3
CAP --out bench/2026-09-23/P1-RZ --send 'busybox reboot -f' --esc-after 25 --esc-period 0.002 --until '<RealTek>' --seconds 45
HOST bench/2026-09-23/P1Q :: LR --cell P1Q QIMG --iterations 4
CAP --out bench/2026-09-23/P1-M0 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines' --seconds 180
HOST bench/2026-09-23/P1-MB0 :: MB bench/2026-09-23/P1-M0
HOST bench/2026-09-23/P1-HPX :: pkill -INT -f 'P1-HP --target' ; sleep 2 ; tail -n 1 bench/2026-09-23/P1-HP.events
CAP --out bench/2026-09-23/P1-FREE --send 'busybox free ; cat /proc/meminfo' --idle 3 --seconds 30
CAP --out bench/2026-09-23/P1-PS --send 'ps' --idle 3 --seconds 30
CAP --out bench/2026-09-23/P1-N0 --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-23/P1-AC0 --send 'sleep 1 ; cat /proc/rtl865x/asicCounter' --until 'CpuEvent' --seconds 40
HOST& bench/2026-09-23/P1-OFF-HP :: HP --out bench/2026-09-23/P1-OFF-HP --target 10.1.1.3 --seconds 180 --udp-listen 50000
CAP --out bench/2026-09-23/P1-OFF01 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-23/P1-OFF02 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-23/P1-OFF03 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-23/P1-OFF04 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-23/P1-OFF05 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-23/P1-OFF06 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-23/P1-OFF07 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-23/P1-OFF08 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-23/P1-OFF09 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-23/P1-OFF10 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-23/P1-OFF11 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-23/P1-OFF12 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-23/P1-OFF13 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-23/P1-OFF14 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-23/P1-OFF15 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
HOST bench/2026-09-23/P1-ICMP :: ICMP 10.1.1.3
HOST bench/2026-09-23/P1-NMAP :: nmap -sT -p- -T4 -n --max-retries 1 10.1.1.3
```

* `P1-A` — opened **before** power; the owner presses inside its window. 推 `Booting...`,
  ` chipName: UNKNOWN`, `ramSize: 32M`, then **one space** (`C-8`: cold), the banner
  `---RealTek(RTL8196E)at 2014.04.22-16:22+0800 v1.3 [16bit](400MHz)`,
  `---Ethernet init Okay!`, `<RealTek>`; `prompt_seen true`.
* `P1-FL` — `0` and `0`. **Before `looprun`, always** (§ 4).
* `P1L`, `P1Q` — `looprun`'s own `A0`–`A4` and the `S5b`/`S6b` gates, round by round:
  `S5b` reads **`00000000`** before every upload or nothing is uploaded; every
  `*-boot` carries `RLXFW-ID0=A2C56BC8` and `RLXFW-N7=00000011`. Bytes (§ 3.2):
  every `P1L-rNN-boot` **7,948 + e**, every `P1Q-rNN-boot` **2,117**. Rounds
  2–N's `*-rz` carry `Reboot Result from Watchdog Timeout!` and end at `<RealTek>`.
  🔴 **`S7`'s pattern `job control turned off[^#]{1,2}# ` has never met a boot whose
  `/init` brings the LAN up.** 推 it matches (nothing prints after `exec /bin/sh`,
  § 0 ③); if it does not, `S7` runs to its 45 s cap, which costs time and no
  reading, and the round's `S8` says whether the prompt came.
  Timing (§ 3.7): `P1Q-rNN-boot` `J` → prompt **f_A × 10.72 s**
  (band 10.15–11.71 s), `P1L-rNN-boot` **f_A × 12.48 s** (11.84–13.12 s).
* `P1-RZ` — the warm catch between the two blocks: 量 its precedent printed
  `Restarting system.` … `Reboot Result from Watchdog Timeout!` … `<RealTek>`
  (`2026-09-21e/L2-RB`). A `looprun` cannot start from rlxfw's shell (`J: not found`).
* `P1-M0` / `P1-MB0` — **the seating's first map, 3,013 B**, and its "before" is the
  last map on record. Predicted, from all 13 committed `map 0` captures
  (2026-09-08 … 2026-09-17b, selected by their `sent` field): the body digest
  (the `MB` pipeline) **`0927be41e91fe4bd`**, and `flashmap compare` exactly
  `DIFFER  000000  device c66a4126d7b1b862... dump 8494cc8666b5c6f6...` and
  `31 same, 1 DIFFER, 0 scope, 0 extra, 0 missing` — group 0 has differed from the
  2026-08-16 dump in every map since 2026-09-08 (`FLS-26`), and a vendor write to
  its config sectors lands in group 0. The header: `map_ran 1`, `map_rc 0`,
  `map_entries 32`, `map_hashed 4186112`, `map_h601_skipped 8192`,
  `map_h601_hashed 0`, `map_diff_units 0`, `map_truncated 0`, `map_lines 32`,
  `corrupt_at -1`. 🔴 **A different body digest or a different group-0 digest
  stops every later vendor boot** until the owner has read it. It cannot say which
  of seatings 29 and 33's two unbracketed vendor runs wrote, only that something did.
* `P1-HPX` — `P1-HP` stopped with SIGINT, which it handles (`C3`); its last line is `stop`.
* `P1-FREE` (`D6`), `P1-PS` (`D4`) — first readings.
* `P1-N0` → `P1-AC0` (`NET-109`) — § 3.6. `P1-N0`: `recov_mode 1`, `ph_follow 1`.
* `P1-OFF-HP` + `P1-OFF01`…`P1-OFF15` (`D8`'s offset) — 推 each capture **139 B**: the
  64-character echo and CRLF (66), one second of silence, `traceroute to 10.1.1.2
  (10.1.1.2), 1 hops max, 38 byte packets` and CRLF (64), two seconds, ` 1  *` and
  CRLF (7), the prompt (2). `P1-OFF-HP`: **15** `udp` events on port 50000, each
  `len=10`. A free negative control is on the console: with nothing bound on
  50000 the line would read ` 1  10.1.1.2  …ms` instead of ` 1  *`.
* `P1-ICMP` (`D5` (a)) — 0 % loss at every size, 推.
* `P1-NMAP` — 推 every TCP port closed: the board runs a shell and nothing else,
  and `iperf3 -s` has not been started yet.

```
CAP --out bench/2026-09-23/P1-SRV --send 'iperf3 -s > /dev/null 2>&1 & sleep 3 ; ps' --idle 5 --seconds 30
CAP --out bench/2026-09-23/P1-LSN --send 'cat /proc/net/tcp' --idle 3 --seconds 20
CAP --out bench/2026-09-23/P1-TR1-S0 --send 'cat /proc/stat' --idle 3 --seconds 20
HOST bench/2026-09-23/P1-TR1 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m
CAP --out bench/2026-09-23/P1-TR1-S1 --send 'cat /proc/stat ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-23/P1-TR2-S0 --send 'cat /proc/stat' --idle 3 --seconds 20
HOST bench/2026-09-23/P1-TR2 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m
CAP --out bench/2026-09-23/P1-TR2-S1 --send 'cat /proc/stat ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-23/P1-TR3-S0 --send 'cat /proc/stat' --idle 3 --seconds 20
HOST bench/2026-09-23/P1-TR3 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m
CAP --out bench/2026-09-23/P1-TR3-S1 --send 'cat /proc/stat ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-23/P1-TS1-S0 --send 'cat /proc/stat' --idle 3 --seconds 20
HOST bench/2026-09-23/P1-TS1 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m -R
CAP --out bench/2026-09-23/P1-TS1-S1 --send 'cat /proc/stat ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-23/P1-TS2-S0 --send 'cat /proc/stat' --idle 3 --seconds 20
HOST bench/2026-09-23/P1-TS2 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m -R
CAP --out bench/2026-09-23/P1-TS2-S1 --send 'cat /proc/stat ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-23/P1-TS3-S0 --send 'cat /proc/stat' --idle 3 --seconds 20
HOST bench/2026-09-23/P1-TS3 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m -R
CAP --out bench/2026-09-23/P1-TS3-S1 --send 'cat /proc/stat ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-23/P1-UR1-S0 --send 'cat /proc/stat' --idle 3 --seconds 20
HOST bench/2026-09-23/P1-UR1 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M
CAP --out bench/2026-09-23/P1-UR1-S1 --send 'cat /proc/stat ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-23/P1-UR2-S0 --send 'cat /proc/stat' --idle 3 --seconds 20
HOST bench/2026-09-23/P1-UR2 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M
CAP --out bench/2026-09-23/P1-UR2-S1 --send 'cat /proc/stat ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-23/P1-UR3-S0 --send 'cat /proc/stat' --idle 3 --seconds 20
HOST bench/2026-09-23/P1-UR3 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M
CAP --out bench/2026-09-23/P1-UR3-S1 --send 'cat /proc/stat ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-23/P1-US1-S0 --send 'cat /proc/stat' --idle 3 --seconds 20
HOST bench/2026-09-23/P1-US1 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M -R
CAP --out bench/2026-09-23/P1-US1-S1 --send 'cat /proc/stat ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-23/P1-US2-S0 --send 'cat /proc/stat' --idle 3 --seconds 20
HOST bench/2026-09-23/P1-US2 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M -R
CAP --out bench/2026-09-23/P1-US2-S1 --send 'cat /proc/stat ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-23/P1-US3-S0 --send 'cat /proc/stat' --idle 3 --seconds 20
HOST bench/2026-09-23/P1-US3 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M -R
CAP --out bench/2026-09-23/P1-US3-S1 --send 'cat /proc/stat ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
```

* `P1-SRV` — `ps` shows `iperf3 -s`; `P1-LSN` — a `0A` (LISTEN) row on `:1451` (5201).
  **The host runs the same `iperf 3.1.3` MIPS binary as the board** — 3.16 fails on
  the real 1,500-byte path (`NET-60`) — and every host client carries `timeout 70`
  (a client once hung 353 s).
* **Order is TCP first, then UDP**, because every committed UDP rung wedged the old
  driver and a wedged board would void what follows. 推 a UDP wedge is now
  recovered by the default `recover`; every `-S1` dump's `n_tx_stop`,
  `n_recov_fire`, `n_recov_ok` and `n_recov_fail` say whether it happened.
* A host client that `timeout` kills can leave the board's server stuck (seating 37,
  `G1`–`G3`); then, and only then, the off-card restart
  `CAP --out bench/2026-09-23/P1-SRVR --send 'busybox killall iperf3 ; sleep 1 ; iperf3 -s > /dev/null 2>&1 & sleep 3 ; ps' --idle 6 --seconds 40`,
  declared in the closeout. Under `qemu-mips-static` the client's `Retr` and `Cwnd`
  are garbage; the figure is the `receiver` line.

```
CAP --out bench/2026-09-23/P1-DOWN --send 'ifconfig rlx0 down ; cat /proc/interrupts' --idle 3 --seconds 30
CAP --out bench/2026-09-23/P1-ETH4 --send 'ifconfig eth4 10.1.1.4 up ; ifconfig eth4 ; cat /proc/interrupts' --idle 3 --seconds 40
HOST bench/2026-09-23/P1-EPING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.4
CAP --out bench/2026-09-23/P1-ER1-S0 --send 'cat /proc/stat' --idle 3 --seconds 20
HOST bench/2026-09-23/P1-ER1 :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 5 -f m
CAP --out bench/2026-09-23/P1-ER1-S1 --send 'cat /proc/stat' --idle 3 --seconds 20
CAP --out bench/2026-09-23/P1-ER2-S0 --send 'cat /proc/stat' --idle 3 --seconds 20
HOST bench/2026-09-23/P1-ER2 :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 5 -f m
CAP --out bench/2026-09-23/P1-ER2-S1 --send 'cat /proc/stat' --idle 3 --seconds 20
CAP --out bench/2026-09-23/P1-ER3-S0 --send 'cat /proc/stat' --idle 3 --seconds 20
HOST bench/2026-09-23/P1-ER3 :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 5 -f m
CAP --out bench/2026-09-23/P1-ER3-S1 --send 'cat /proc/stat' --idle 3 --seconds 20
CAP --out bench/2026-09-23/P1-ES1-S0 --send 'cat /proc/stat' --idle 3 --seconds 20
HOST bench/2026-09-23/P1-ES1 :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 5 -f m -R
CAP --out bench/2026-09-23/P1-ES1-S1 --send 'cat /proc/stat' --idle 3 --seconds 20
CAP --out bench/2026-09-23/P1-ES2-S0 --send 'cat /proc/stat' --idle 3 --seconds 20
HOST bench/2026-09-23/P1-ES2 :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 5 -f m -R
CAP --out bench/2026-09-23/P1-ES2-S1 --send 'cat /proc/stat' --idle 3 --seconds 20
CAP --out bench/2026-09-23/P1-ES3-S0 --send 'cat /proc/stat' --idle 3 --seconds 20
HOST bench/2026-09-23/P1-ES3 :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 5 -f m -R
CAP --out bench/2026-09-23/P1-ES3-S1 --send 'cat /proc/stat' --idle 3 --seconds 20
CAP --out bench/2026-09-23/P1-EU1-S0 --send 'cat /proc/stat' --idle 3 --seconds 20
HOST bench/2026-09-23/P1-EU1 :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M
CAP --out bench/2026-09-23/P1-EU1-S1 --send 'cat /proc/stat' --idle 3 --seconds 20
CAP --out bench/2026-09-23/P1-EU2-S0 --send 'cat /proc/stat' --idle 3 --seconds 20
HOST bench/2026-09-23/P1-EU2 :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M
CAP --out bench/2026-09-23/P1-EU2-S1 --send 'cat /proc/stat' --idle 3 --seconds 20
CAP --out bench/2026-09-23/P1-EU3-S0 --send 'cat /proc/stat' --idle 3 --seconds 20
HOST bench/2026-09-23/P1-EU3 :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M
CAP --out bench/2026-09-23/P1-EU3-S1 --send 'cat /proc/stat' --idle 3 --seconds 20
CAP --out bench/2026-09-23/P1-EV1-S0 --send 'cat /proc/stat' --idle 3 --seconds 20
HOST bench/2026-09-23/P1-EV1 :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M -R
CAP --out bench/2026-09-23/P1-EV1-S1 --send 'cat /proc/stat' --idle 3 --seconds 20
CAP --out bench/2026-09-23/P1-EV2-S0 --send 'cat /proc/stat' --idle 3 --seconds 20
HOST bench/2026-09-23/P1-EV2 :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M -R
CAP --out bench/2026-09-23/P1-EV2-S1 --send 'cat /proc/stat' --idle 3 --seconds 20
CAP --out bench/2026-09-23/P1-EV3-S0 --send 'cat /proc/stat' --idle 3 --seconds 20
HOST bench/2026-09-23/P1-EV3 :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M -R
CAP --out bench/2026-09-23/P1-EV3-S1 --send 'cat /proc/stat' --idle 3 --seconds 20
```

* `P1-DOWN` — 量 its precedent: `RLXFW-N-ENGOFF`, `RLXFW-N-NDSTOP`, and `/proc/interrupts`
  without line 12. **The one `ifconfig rlx0 down` of this seating; `rlx0` is not
  re-opened** (`NET-58`), and after it rlxfw's `/proc` is only read.
* `P1-ETH4` — 量 precedent `2026-09-21e/V3-ETH4`: `HWaddr 00:12:34:56:78:94` (the SDK's
  placeholder, not the unit's address), `inet addr:10.1.1.4`, `Mask:255.0.0.0`
  (no netmask given), and line 12 `eth4`. The server keeps listening on
  `0.0.0.0:5201`.
* `P1-EPING` — **4/4 or the vendor-driver trials are void** (`NET-54`: an ingress
  hang can outlive the driver that caused it).
* After `P1-EV3-S1` the owner powers off. Nothing between `P1-M0` and here boots
  anything, so `P1-M0` is the bracket's "before" for `V1`–`M1`.

### Presses 2, 3, 4 — `V1`, `V2`, `V3`, vendor cold: caught, then `J 80500000`

```
CAP --out bench/2026-09-23/V1-A --esc 180 --esc-period 0.002 --seconds 200
CAP --out bench/2026-09-23/V1-AB --send 'DW 8040D4A0 1' --idle 2 --seconds 6
HOST bench/2026-09-23/V1-FL :: FL 10.1.1.1
HOST& bench/2026-09-23/V1-HP :: HP --out bench/2026-09-23/V1-HP --target 10.1.1.1 --seconds 60 --icmp --icmp-interval 0.05 --neigh --tcp 80
CAP --out bench/2026-09-23/V1-BOOT --send 'J 80500000' --until 'port 80' --seconds 90
HOST bench/2026-09-23/V1-ICMP :: ICMP 10.1.1.1
HOST bench/2026-09-23/V1-NMAP :: nmap -sT -p- -T4 -n --max-retries 1 10.1.1.1
CAP --out bench/2026-09-23/V2-A --esc 180 --esc-period 0.002 --seconds 200
CAP --out bench/2026-09-23/V2-AB --send 'DW 8040D4A0 1' --idle 2 --seconds 6
HOST bench/2026-09-23/V2-FL :: FL 10.1.1.1
HOST& bench/2026-09-23/V2-HP :: HP --out bench/2026-09-23/V2-HP --target 10.1.1.1 --seconds 60 --icmp --icmp-interval 0.05 --neigh --tcp 80
CAP --out bench/2026-09-23/V2-BOOT --send 'J 80500000' --until 'port 80' --seconds 90
HOST bench/2026-09-23/V2-ICMP :: ICMP 10.1.1.1
CAP --out bench/2026-09-23/V3-A --esc 180 --esc-period 0.002 --seconds 200
CAP --out bench/2026-09-23/V3-AB --send 'DW 8040D4A0 1' --idle 2 --seconds 6
HOST bench/2026-09-23/V3-FL :: FL 10.1.1.1
HOST& bench/2026-09-23/V3-HP :: HP --out bench/2026-09-23/V3-HP --target 10.1.1.1 --seconds 60 --icmp --icmp-interval 0.05 --neigh --tcp 80
CAP --out bench/2026-09-23/V3-BOOT --send 'J 80500000' --until 'port 80' --seconds 90
HOST bench/2026-09-23/V3-ICMP :: ICMP 10.1.1.1
```

* `V*-A` — as `P1-A`. `V*-AB` — **`00000001`**, and it absorbs a swallowed first
  command (§ 4).
* `V*-FL` — `0`. No `IPCONFIG` is typed on these presses, so nothing but the vendor
  can answer 10.1.1.1 after it (量 `NET-95`: before `IPCONFIG` the loader answers no
  ARP for it).
* `V*-BOOT` — **1,789 B each, ending `boa: starting server pid=350, port 80`**: 量 `G6` and
  `G7`, the two committed `J 80500000` boots of the loader-staged vendor image,
  are 1,789 B and byte-identical, and nothing followed the `boa` line for 34 s
  (`G6`) and 57 s (`K-J`). `J` → `boa`: 推 25.65–26.13 s raw (`G6` 26.028, `G7`
  26.126, `H2a2` 25.654, `K-J` 25.671 — the vendor's userspace is not shown to
  follow the seating factor, so the raw range is the prediction); `kernel.total`
  f_A × 6.93–7.15 s. `MiniIGD v1.09.1 (2018.01.10-06:58+0000).` is `miniigd`'s own
  line (`D4`). 🔴 A stop before `boa` is a reading, not a failure (`X8-WAIT` stalled
  after `sysconf wlanapp kill wlan0` and nothing followed for 201 s): the capture
  runs to its cap and `V*-HP`'s `tcp:80` says whether `boa` came up silently.
* `V*-HP` — the first `icmp-reply` (`D8`) and the first `tcp` `result=ok` on 80
  (`D4`); the vendor's address appears as `unlisted-N`. 推 the reply precedes
  `tcp 80 ok`, and `tcp 80 ok` follows the `boa` line within ~1 s.
* `V*-ICMP` (`D5` (a)) — starts after `V*-HP`'s `stop`; 0 % loss, 推.
* `V1-NMAP` (`D4`) — 推 **80/tcp open**; everything else is a first reading. An
  unprivileged `-sT` prints no hardware address.

### Press 5 — `M1`, vendor cold, listen-only autoboot (the capture-mode control)

```
HOST bench/2026-09-23/M1-FL :: FL 10.1.1.1
HOST& bench/2026-09-23/M1-HP :: HP --out bench/2026-09-23/M1-HP --target 10.1.1.1 --seconds 300 --icmp --icmp-interval 0.05 --neigh --tcp 80
CAP --out bench/2026-09-23/M1-BOOT --until 'port 80' --seconds 300
```

* `M1-BOOT` — opened before power, **nothing sent**: the owner presses and the
  loader autoboots through its ESC window. 推 cold `C-8`, `loader.banner` within
  ±10 ms of the cold `esc` groups (§ 3.1), `loader.esc` f_A × ~5.2 s (`X8-WAIT`,
  cold, 5.2101 s), `Jump to image start=0x80500000...`, then the same vendor text
  to `boa`. **This is the first power-on autoboot of the vendor on record that is
  captured from before power**, and the one cold autoboot on record stalled.

### Press 6 — `P2`, rlxfw: the bracket after `V1`–`M1`

```
CAP --out bench/2026-09-23/P2-A --esc 180 --esc-period 0.002 --seconds 200
HOST bench/2026-09-23/P2-FL :: FL 10.1.1.1 ; FL 10.1.1.3
HOST& bench/2026-09-23/P2-HP :: HP --out bench/2026-09-23/P2-HP --target 10.1.1.3 --seconds 300 --icmp --icmp-interval 0.05 --neigh
HOST bench/2026-09-23/P2Q :: LR --cell P2Q QIMG --iterations 2
CAP --out bench/2026-09-23/P2-M0 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines' --seconds 180
HOST bench/2026-09-23/P2-MB0 :: MB bench/2026-09-23/P2-M0
HOST bench/2026-09-23/P2-HPX :: pkill -INT -f 'P2-HP --target' ; sleep 2 ; tail -n 1 bench/2026-09-23/P2-HP.events
HOST bench/2026-09-23/P2-ICMP :: ICMP 10.1.1.3
```

* `P2-FL` — **after four vendor boots the host holds the unit's address for
  10.1.1.1, and `P2Q`'s `S5c` would print it**; this is the flush that keeps it out.
* `P2-M0` — **identical to `P1-M0`**: body `0927be41e91fe4bd`, the same `DIFFER`
  line and total. Any other reading stops `V4`–`M2`.

### Presses 7, 8, 9, 10 — `V4`–`V7`, vendor warm: caught, a warm reset caught, then `J 80500000`

```
CAP --out bench/2026-09-23/V4-A --esc 180 --esc-period 0.002 --seconds 200
CAP --out bench/2026-09-23/V4-AB --send 'DW 8040D4A0 1' --idle 2 --seconds 6
CAP --out bench/2026-09-23/V4-WZ --send 'J BFC00000' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
CAP --out bench/2026-09-23/V4-AB2 --send 'DW 8040D4A0 1' --idle 2 --seconds 6
HOST bench/2026-09-23/V4-FL :: FL 10.1.1.1
HOST& bench/2026-09-23/V4-HP :: HP --out bench/2026-09-23/V4-HP --target 10.1.1.1 --seconds 60 --icmp --icmp-interval 0.05 --neigh --tcp 80
CAP --out bench/2026-09-23/V4-BOOT --send 'J 80500000' --until 'port 80' --seconds 90
CAP --out bench/2026-09-23/V5-A --esc 180 --esc-period 0.002 --seconds 200
CAP --out bench/2026-09-23/V5-AB --send 'DW 8040D4A0 1' --idle 2 --seconds 6
CAP --out bench/2026-09-23/V5-WZ --send 'J BFC00000' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
CAP --out bench/2026-09-23/V5-AB2 --send 'DW 8040D4A0 1' --idle 2 --seconds 6
HOST bench/2026-09-23/V5-FL :: FL 10.1.1.1
HOST& bench/2026-09-23/V5-HP :: HP --out bench/2026-09-23/V5-HP --target 10.1.1.1 --seconds 60 --icmp --icmp-interval 0.05 --neigh --tcp 80
CAP --out bench/2026-09-23/V5-BOOT --send 'J 80500000' --until 'port 80' --seconds 90
CAP --out bench/2026-09-23/V6-A --esc 180 --esc-period 0.002 --seconds 200
CAP --out bench/2026-09-23/V6-AB --send 'DW 8040D4A0 1' --idle 2 --seconds 6
CAP --out bench/2026-09-23/V6-WZ --send 'J BFC00000' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
CAP --out bench/2026-09-23/V6-AB2 --send 'DW 8040D4A0 1' --idle 2 --seconds 6
HOST bench/2026-09-23/V6-FL :: FL 10.1.1.1
HOST& bench/2026-09-23/V6-HP :: HP --out bench/2026-09-23/V6-HP --target 10.1.1.1 --seconds 60 --icmp --icmp-interval 0.05 --neigh --tcp 80
CAP --out bench/2026-09-23/V6-BOOT --send 'J 80500000' --until 'port 80' --seconds 90
CAP --out bench/2026-09-23/V7-A --esc 180 --esc-period 0.002 --seconds 200
CAP --out bench/2026-09-23/V7-AB --send 'DW 8040D4A0 1' --idle 2 --seconds 6
CAP --out bench/2026-09-23/V7-WZ --send 'J BFC00000' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
CAP --out bench/2026-09-23/V7-AB2 --send 'DW 8040D4A0 1' --idle 2 --seconds 6
HOST bench/2026-09-23/V7-FL :: FL 10.1.1.1
HOST& bench/2026-09-23/V7-HP :: HP --out bench/2026-09-23/V7-HP --target 10.1.1.1 --seconds 60 --icmp --icmp-interval 0.05 --neigh --tcp 80
CAP --out bench/2026-09-23/V7-BOOT --send 'J 80500000' --until 'port 80' --seconds 90
```

* `V*-WZ` — **`Reboot Result from Watchdog Timeout!`** (量 82 of 86 committed `J BFC00000`
  sends carry it; the loader's `J BFC00000` writes `WDTCNR = 0`), `<RealTek>` 2.12–2.41 s
  after the send. These four are `D2`'s vendor warm column.
* `V*-AB2` — `00000001` again: the reset reverts the word.
* `V*-BOOT` — as `V1`–`V3`: 1,789 B each; `J` → `boa` 推 the same raw range.

### Press 11 — `M2`, vendor warm, listen-only autoboot (the capture-mode control)

```
CAP --out bench/2026-09-23/M2-A --esc 180 --esc-period 0.002 --seconds 200
CAP --out bench/2026-09-23/M2-AB --send 'DW 8040D4A0 1' --idle 2 --seconds 6
HOST bench/2026-09-23/M2-FL :: FL 10.1.1.1
HOST& bench/2026-09-23/M2-HP :: HP --out bench/2026-09-23/M2-HP --target 10.1.1.1 --seconds 90 --icmp --icmp-interval 0.05 --neigh --tcp 80
CAP --out bench/2026-09-23/M2-BOOT --send 'J BFC00000' --until 'port 80' --seconds 90
```

* `M2-BOOT` — **no ESC**: the loader's warm reset autoboots the vendor, the path
  `K-J` took (`Booting` → `boa` 31.281 s, `loader.esc` 5.0362 s). 推 warm `C-8`,
  `loader.banner` within ±10 ms of the warm `esc_after` groups, `loader.esc`
  f_A × ~5.04 s.

### Press 12 — `P3`, rlxfw: the bracket after `V4`–`M2`, and the ARP reconstruction's control

```
CAP --out bench/2026-09-23/P3-A --esc 180 --esc-period 0.002 --seconds 200
HOST bench/2026-09-23/P3-FL :: FL 10.1.1.1 ; FL 10.1.1.3
HOST& bench/2026-09-23/P3-TCPD :: timeout 240 sudo -n tcpdump -n -tt -i enxfc19286184c9 arp or icmp
HOST& bench/2026-09-23/P3-HP :: HP --out bench/2026-09-23/P3-HP --target 10.1.1.3 --seconds 300 --icmp --icmp-interval 0.05 --neigh
HOST bench/2026-09-23/P3Q :: LR --cell P3Q QIMG --iterations 2
CAP --out bench/2026-09-23/P3-M0 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines' --seconds 180
HOST bench/2026-09-23/P3-MB0 :: MB bench/2026-09-23/P3-M0
HOST bench/2026-09-23/P3-HPX :: pkill -INT -f 'P3-HP --target' ; sleep 2 ; tail -n 1 bench/2026-09-23/P3-HP.events
HOST bench/2026-09-23/P3-ICMP :: ICMP 10.1.1.3
HOST bench/2026-09-23/Z9-D2 :: /usr/bin/python3 tools/boot-timeline.py --retro bench/2026-09-23 --tsv
```

* `P3-TCPD` — the one frame capture of the seating, on the one press where every
  address on the wire is on the allowlist: `rlx0`'s `02:52:4c:58:46:57`, the
  loader's `56:0a:01:01:01:e8` after `P3Q`'s `IPCONFIG`, and the host's adapter.
  No `-e`. It checks the `D8` reconstruction — broadcasts about once a second,
  the first `is-at` for 10.1.1.3 inside the bracket `P3-HP`'s record implies.
  **Never on a vendor press**: its `is-at` would carry the unit's address.
* `P3-M0` — identical to `P1-M0` and `P2-M0`.
* `Z9-D2` — **`D2`, before anything else is compared** (§ 3.1). Then the owner powers off.

---

## § 6 What this seating does NOT establish

* **`D3`.** One calendar day cannot reproduce itself; seating B (`P2-4`) re-measures
  every number here on another day, with `capdate` checking that it is one.
* **That the vendor's daemons are ready where they say so**, beyond `boa`: this
  card probes TCP 80 only, and `miniigd`'s port is configured, not compiled in.
  The census names the ports; their readiness is seating B's.
* **Anything about UDP daemons on the vendor**: the census is TCP-only
  (an unprivileged scan); `udhcpd`, `dnrd` and friends come from its scripts.
* **Where inside its one-second bracket either firmware's network came up**, and
  the vendor's board-side emission latencies: the channel offset is measured on
  rlxfw only and transferred.
* **Any vendor figure that needs a shell** — `iperf3`, `/proc`, memory, per-daemon
  CPU (`P2` settled item 1).
* **That no flash byte was written.** The maps compare 32 digests over 4,186,112 B
  of 4,194,304: they cannot see two writes that cancel, and they do not read
  `H601`. This seating issues no `FLR`.
* **That a boot captured in listen mode measures the same as one caught** beyond the
  two `M` controls, n = 1 each.
* **The vendor driver's receive path under the vendor firmware**: `eth4`'s trials
  run it on rlxfw's kernel, which is `D5` (b)'s question, not a vendor-firmware
  figure.

### ⚠️ The fence's scope

The `cells` fence holds every cell in § 5 and every artefact the four `looprun`
blocks write under a name (`*-rNN-rz`, `-ab2`, `-2a`, `-boot`). It does not hold
the conditional server restart `P1-SRVR` (§ 5), which runs only if a trial leaves
the board's server stuck and is then declared in the closeout. A green
`check-predictions` on this card says every one of the fenced cells was captured
after the card; it says nothing about their content.

```cells
bench/2026-09-23/Z0-PRE
bench/2026-09-23/Z1-ADDR
bench/2026-09-23/P1-A
bench/2026-09-23/P1-FL
bench/2026-09-23/P1-HP
bench/2026-09-23/P1L
bench/2026-09-23/P1-RZ
bench/2026-09-23/P1Q
bench/2026-09-23/P1-M0
bench/2026-09-23/P1-MB0
bench/2026-09-23/P1-HPX
bench/2026-09-23/P1-FREE
bench/2026-09-23/P1-PS
bench/2026-09-23/P1-N0
bench/2026-09-23/P1-AC0
bench/2026-09-23/P1-OFF-HP
bench/2026-09-23/P1-OFF01
bench/2026-09-23/P1-OFF02
bench/2026-09-23/P1-OFF03
bench/2026-09-23/P1-OFF04
bench/2026-09-23/P1-OFF05
bench/2026-09-23/P1-OFF06
bench/2026-09-23/P1-OFF07
bench/2026-09-23/P1-OFF08
bench/2026-09-23/P1-OFF09
bench/2026-09-23/P1-OFF10
bench/2026-09-23/P1-OFF11
bench/2026-09-23/P1-OFF12
bench/2026-09-23/P1-OFF13
bench/2026-09-23/P1-OFF14
bench/2026-09-23/P1-OFF15
bench/2026-09-23/P1-ICMP
bench/2026-09-23/P1-NMAP
bench/2026-09-23/P1-SRV
bench/2026-09-23/P1-LSN
bench/2026-09-23/P1-TR1-S0
bench/2026-09-23/P1-TR1
bench/2026-09-23/P1-TR1-S1
bench/2026-09-23/P1-TR2-S0
bench/2026-09-23/P1-TR2
bench/2026-09-23/P1-TR2-S1
bench/2026-09-23/P1-TR3-S0
bench/2026-09-23/P1-TR3
bench/2026-09-23/P1-TR3-S1
bench/2026-09-23/P1-TS1-S0
bench/2026-09-23/P1-TS1
bench/2026-09-23/P1-TS1-S1
bench/2026-09-23/P1-TS2-S0
bench/2026-09-23/P1-TS2
bench/2026-09-23/P1-TS2-S1
bench/2026-09-23/P1-TS3-S0
bench/2026-09-23/P1-TS3
bench/2026-09-23/P1-TS3-S1
bench/2026-09-23/P1-UR1-S0
bench/2026-09-23/P1-UR1
bench/2026-09-23/P1-UR1-S1
bench/2026-09-23/P1-UR2-S0
bench/2026-09-23/P1-UR2
bench/2026-09-23/P1-UR2-S1
bench/2026-09-23/P1-UR3-S0
bench/2026-09-23/P1-UR3
bench/2026-09-23/P1-UR3-S1
bench/2026-09-23/P1-US1-S0
bench/2026-09-23/P1-US1
bench/2026-09-23/P1-US1-S1
bench/2026-09-23/P1-US2-S0
bench/2026-09-23/P1-US2
bench/2026-09-23/P1-US2-S1
bench/2026-09-23/P1-US3-S0
bench/2026-09-23/P1-US3
bench/2026-09-23/P1-US3-S1
bench/2026-09-23/P1-DOWN
bench/2026-09-23/P1-ETH4
bench/2026-09-23/P1-EPING
bench/2026-09-23/P1-ER1-S0
bench/2026-09-23/P1-ER1
bench/2026-09-23/P1-ER1-S1
bench/2026-09-23/P1-ER2-S0
bench/2026-09-23/P1-ER2
bench/2026-09-23/P1-ER2-S1
bench/2026-09-23/P1-ER3-S0
bench/2026-09-23/P1-ER3
bench/2026-09-23/P1-ER3-S1
bench/2026-09-23/P1-ES1-S0
bench/2026-09-23/P1-ES1
bench/2026-09-23/P1-ES1-S1
bench/2026-09-23/P1-ES2-S0
bench/2026-09-23/P1-ES2
bench/2026-09-23/P1-ES2-S1
bench/2026-09-23/P1-ES3-S0
bench/2026-09-23/P1-ES3
bench/2026-09-23/P1-ES3-S1
bench/2026-09-23/P1-EU1-S0
bench/2026-09-23/P1-EU1
bench/2026-09-23/P1-EU1-S1
bench/2026-09-23/P1-EU2-S0
bench/2026-09-23/P1-EU2
bench/2026-09-23/P1-EU2-S1
bench/2026-09-23/P1-EU3-S0
bench/2026-09-23/P1-EU3
bench/2026-09-23/P1-EU3-S1
bench/2026-09-23/P1-EV1-S0
bench/2026-09-23/P1-EV1
bench/2026-09-23/P1-EV1-S1
bench/2026-09-23/P1-EV2-S0
bench/2026-09-23/P1-EV2
bench/2026-09-23/P1-EV2-S1
bench/2026-09-23/P1-EV3-S0
bench/2026-09-23/P1-EV3
bench/2026-09-23/P1-EV3-S1
bench/2026-09-23/V1-A
bench/2026-09-23/V1-AB
bench/2026-09-23/V1-FL
bench/2026-09-23/V1-HP
bench/2026-09-23/V1-BOOT
bench/2026-09-23/V1-ICMP
bench/2026-09-23/V1-NMAP
bench/2026-09-23/V2-A
bench/2026-09-23/V2-AB
bench/2026-09-23/V2-FL
bench/2026-09-23/V2-HP
bench/2026-09-23/V2-BOOT
bench/2026-09-23/V2-ICMP
bench/2026-09-23/V3-A
bench/2026-09-23/V3-AB
bench/2026-09-23/V3-FL
bench/2026-09-23/V3-HP
bench/2026-09-23/V3-BOOT
bench/2026-09-23/V3-ICMP
bench/2026-09-23/M1-FL
bench/2026-09-23/M1-HP
bench/2026-09-23/M1-BOOT
bench/2026-09-23/P2-A
bench/2026-09-23/P2-FL
bench/2026-09-23/P2-HP
bench/2026-09-23/P2Q
bench/2026-09-23/P2-M0
bench/2026-09-23/P2-MB0
bench/2026-09-23/P2-HPX
bench/2026-09-23/P2-ICMP
bench/2026-09-23/V4-A
bench/2026-09-23/V4-AB
bench/2026-09-23/V4-WZ
bench/2026-09-23/V4-AB2
bench/2026-09-23/V4-FL
bench/2026-09-23/V4-HP
bench/2026-09-23/V4-BOOT
bench/2026-09-23/V5-A
bench/2026-09-23/V5-AB
bench/2026-09-23/V5-WZ
bench/2026-09-23/V5-AB2
bench/2026-09-23/V5-FL
bench/2026-09-23/V5-HP
bench/2026-09-23/V5-BOOT
bench/2026-09-23/V6-A
bench/2026-09-23/V6-AB
bench/2026-09-23/V6-WZ
bench/2026-09-23/V6-AB2
bench/2026-09-23/V6-FL
bench/2026-09-23/V6-HP
bench/2026-09-23/V6-BOOT
bench/2026-09-23/V7-A
bench/2026-09-23/V7-AB
bench/2026-09-23/V7-WZ
bench/2026-09-23/V7-AB2
bench/2026-09-23/V7-FL
bench/2026-09-23/V7-HP
bench/2026-09-23/V7-BOOT
bench/2026-09-23/M2-A
bench/2026-09-23/M2-AB
bench/2026-09-23/M2-FL
bench/2026-09-23/M2-HP
bench/2026-09-23/M2-BOOT
bench/2026-09-23/P3-A
bench/2026-09-23/P3-FL
bench/2026-09-23/P3-TCPD
bench/2026-09-23/P3-HP
bench/2026-09-23/P3Q
bench/2026-09-23/P3-M0
bench/2026-09-23/P3-MB0
bench/2026-09-23/P3-HPX
bench/2026-09-23/P3-ICMP
bench/2026-09-23/Z9-D2
bench/2026-09-23/P1L-r01-ab2
bench/2026-09-23/P1L-r01-2a
bench/2026-09-23/P1L-r01-boot
bench/2026-09-23/P1L-r02-rz
bench/2026-09-23/P1L-r02-ab2
bench/2026-09-23/P1L-r02-2a
bench/2026-09-23/P1L-r02-boot
bench/2026-09-23/P1L-r03-rz
bench/2026-09-23/P1L-r03-ab2
bench/2026-09-23/P1L-r03-2a
bench/2026-09-23/P1L-r03-boot
bench/2026-09-23/P1Q-r01-ab2
bench/2026-09-23/P1Q-r01-2a
bench/2026-09-23/P1Q-r01-boot
bench/2026-09-23/P1Q-r02-rz
bench/2026-09-23/P1Q-r02-ab2
bench/2026-09-23/P1Q-r02-2a
bench/2026-09-23/P1Q-r02-boot
bench/2026-09-23/P1Q-r03-rz
bench/2026-09-23/P1Q-r03-ab2
bench/2026-09-23/P1Q-r03-2a
bench/2026-09-23/P1Q-r03-boot
bench/2026-09-23/P1Q-r04-rz
bench/2026-09-23/P1Q-r04-ab2
bench/2026-09-23/P1Q-r04-2a
bench/2026-09-23/P1Q-r04-boot
bench/2026-09-23/P2Q-r01-ab2
bench/2026-09-23/P2Q-r01-2a
bench/2026-09-23/P2Q-r01-boot
bench/2026-09-23/P2Q-r02-rz
bench/2026-09-23/P2Q-r02-ab2
bench/2026-09-23/P2Q-r02-2a
bench/2026-09-23/P2Q-r02-boot
bench/2026-09-23/P3Q-r01-ab2
bench/2026-09-23/P3Q-r01-2a
bench/2026-09-23/P3Q-r01-boot
bench/2026-09-23/P3Q-r02-rz
bench/2026-09-23/P3Q-r02-ab2
bench/2026-09-23/P3Q-r02-2a
bench/2026-09-23/P3Q-r02-boot
```

```cardnum
cells-fence	223	count bench/2026-09-23/PREDICTIONS-B44-block42.md ^bench/2026-09-23/
declared-date	1	count bench/2026-09-23/PREDICTIONS-B44-block42.md [*][*]declared date 2026-09-23[*][*]
presses-caught	11	count bench/2026-09-23/PREDICTIONS-B44-block42.md ^CAP -{2}out bench/2026-09-23/[A-Z0-9]+-A -{2}esc 180 -{2}esc-period
presses-listen	1	count bench/2026-09-23/PREDICTIONS-B44-block42.md ^CAP -{2}out bench/2026-09-23/M1-BOOT -{2}until
cap-cells	112	count bench/2026-09-23/PREDICTIONS-B44-block42.md ^CAP -{2}out
host-cells	71	count bench/2026-09-23/PREDICTIONS-B44-block42.md ^HOST&? bench/2026-09-23/
send-over-127	0	count bench/2026-09-23/PREDICTIONS-B44-block42.md -{2}send '[^']{128,}'
no-shell-subst	0	count bench/2026-09-23/PREDICTIONS-B44-block42.md -{2}send '[^']*[$]
no-flr	0	count bench/2026-09-23/PREDICTIONS-B44-block42.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-23/PREDICTIONS-B44-block42.md -{2}send '[^']*(EW |EB |FLW )
no-burn	0	count bench/2026-09-23/PREDICTIONS-B44-block42.md -{2}send '[^']*AUTOBURN
ifdown-cells	1	count bench/2026-09-23/PREDICTIONS-B44-block42.md ^CAP .*-{2}send '[^']*ifconfig rlx0 down
vendor-jumps	7	count bench/2026-09-23/PREDICTIONS-B44-block42.md ^CAP .*-{2}send 'J 80500000' -{2}until 'port 80'
listen-jbfc	1	count bench/2026-09-23/PREDICTIONS-B44-block42.md ^CAP .*-{2}send 'J BFC00000' -{2}until 'port 80'
p2q-nfjrom-bytes	1155072	size /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/kroot/rtkload/nfjrom
p2q-nfjrom-sha256	4972edbadd2655a8	sha256-16 /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/kroot/rtkload/nfjrom
p2l-nfjrom-bytes	1181696	size /home/key/fwre-work/rebuild/p2-2/rtk/p2l/rlxfw/kroot/rtkload/nfjrom
p2l-nfjrom-sha256	888c930aa31763d9	sha256-16 /home/key/fwre-work/rebuild/p2-2/rtk/p2l/rlxfw/kroot/rtkload/nfjrom
p2q-vmlinux-bytes	4468487	size /home/key/fwre-work/rebuild/r3-4/out/p2q.vmlinux.elf
p2l-vmlinux-bytes	4575403	size /home/key/fwre-work/rebuild/r3-4/out/p2l.vmlinux.elf
p2q-manifest-green	1	count /home/key/fwre-work/rebuild/r3-4/out/p2q.manifest ^verdict\tgreen$
p2q-manifest-vmlinux	1	count /home/key/fwre-work/rebuild/r3-4/out/p2q.manifest ^vmlinux_sha256\tc5e2cfdba7730d479c5a23664d41fa734cc7989ee3db784f106559e6ed654863$
p2q-manifest-irfs	1	count /home/key/fwre-work/rebuild/r3-4/out/p2q.manifest ^initramfs_manifest_sha256\t51ea1604c7c163f379a70dd7b042dae3d2429db380dda1375675f1a0a5d24a59$
p2q-record-vmlinux	1	count /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/rtkimage-record.tsv ^vmlinux_sha256\tc5e2cfdba7730d479c5a23664d41fa734cc7989ee3db784f106559e6ed654863$
p2q-record-nfjrom	1	count /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/rtkimage-record.tsv ^nfjrom_sha256\t4972edbadd2655a815e80606a83b8e5e5987334dfd1c990fcc806291eaf182ae$
p2q-record-clean	1	count /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/rtkimage-record.tsv ^tripwire_verdict\tVENDOR-TRIPWIRE: CLEAN\s+cmd-rc=0
p2l-manifest-green	1	count /home/key/fwre-work/rebuild/r3-4/out/p2l.manifest ^verdict\tgreen$
p2l-manifest-vmlinux	1	count /home/key/fwre-work/rebuild/r3-4/out/p2l.manifest ^vmlinux_sha256\t39a4db228131f697d2a893b71e44d80f775370b9b84a947a2f6c7c6a562de459$
p2l-manifest-irfs	1	count /home/key/fwre-work/rebuild/r3-4/out/p2l.manifest ^initramfs_manifest_sha256\t51ea1604c7c163f379a70dd7b042dae3d2429db380dda1375675f1a0a5d24a59$
p2l-record-vmlinux	1	count /home/key/fwre-work/rebuild/p2-2/rtk/p2l/rlxfw/rtkimage-record.tsv ^vmlinux_sha256\t39a4db228131f697d2a893b71e44d80f775370b9b84a947a2f6c7c6a562de459$
p2l-record-nfjrom	1	count /home/key/fwre-work/rebuild/p2-2/rtk/p2l/rlxfw/rtkimage-record.tsv ^nfjrom_sha256\t888c930aa31763d9ed217783d4c9faa82c9652574a18948e35b379d88e8c31fc$
p2l-record-clean	1	count /home/key/fwre-work/rebuild/p2-2/rtk/p2l/rlxfw/rtkimage-record.tsv ^tripwire_verdict\tVENDOR-TRIPWIRE: CLEAN\s+cmd-rc=0
quiet-base-boot	1874	size bench/2026-09-21b/A0-boot.log
loud-base-boot	7705	size bench/2026-09-22b/X20-boot.log
loud-base-tmpreg	12	count bench/2026-09-22b/X20-boot.log tmpReg\[0x
vendor-g6-bytes	1789	size bench/2026-08-24c/G6.log
vendor-g7-bytes	1789	size bench/2026-08-24d/G7.log
map-c7-bytes	3013	size bench/2026-09-17b/C7-M0.log
init-bytes	2153	size config/rlxfw-init.sh
```
