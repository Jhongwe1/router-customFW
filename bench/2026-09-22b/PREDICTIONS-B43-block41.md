# PREDICTIONS — block 41, seating 38 (`D4` becomes a command, and the three TX ring bases nobody has read)

**declared date 2026-09-22** — the power press happens on the evening of
2026-09-22 and every capture in this directory belongs to that cycle. One
press, budgeted one.

Marks: **量** measured on the device · **讀** read out of code or a dump ·
**推** inferred, pending a measurement.

---

## § 0 Three honesty notes, written rather than left to be found

🔴 **① The ethtool ops in this image CANNOT be exercised on the device, and
that is known before power rather than at the bench.** `rtl819x-nic 1.3` adds
`get_drvinfo`, `get_link` and `get_ringparam`, and they are reachable only
through the `SIOCETHTOOL` ioctl, i.e. only from an `ethtool` binary. 量
`config/image-commands.tsv`, derived by `appletcensus.py` from the busybox
this image ships: there is **no `ethtool` applet**, and a sweep of the unit's
own `squashfs-root` finds no `ethtool` or `mii-tool` binary either. So the ops
are verified **in the artefact** (§ 1.2) and are **inert at runtime**. The
honest status of `R6-4` ① is *implemented and statically verified, not
exercised*, and the named next step is a small static MIPS `linkprobe` — a
pattern this project already has, since `/bin/iperf3` reaches the board the
same way. **This is `FW-46`'s class caught one instance earlier**: the last
time, nothing could ask *can this image run this command* until a card had
frozen.

🔴 **② `D4`'s DoD is not met by this image and this card does not pretend
otherwise.** Its words are *"with my driver bound and the vendor's **not**
loaded"*. What this image does is narrower and is the first rung of a ladder:
the vendor's driver is loaded, every one of its hardware initialisations runs,
and its `re865x_open()` **refuses**. The remaining conjunct is owned by a gate,
not by this card — 量 `readelf` over a fully built tree, `CONFIG_RTL_819X_SWCORE=n`
leaves ten undefined symbols at the vmlinux link in four independent places,
and past the link the VLAN table is not a register write but a `TACI`
protocol inside the directory that would vanish.

⚠️ **③ The at-rest addresses below are predicted as OFFSETS, not as absolute
values.** `nic_do_alloc`'s `kmalloc` request grew by 28 bytes for the idle
ring (25,296 → 25,324), which is inside the same slab class, so the base very
likely does not move — but *very likely* is not a prediction. Every address
row is written as a difference from `rx_ring`, which is a property of the
layout rather than of the allocator.

---

## § 1 The image

| | |
|---|---|
| cell | **`s100L`** |
| `RECIPE_ID` | **`82724c8f`** (`s99c` was `c3cb552b`) |
| variant | **loud**, `CONFIG_PRINTK=y` — the same as `s99c`, deliberately |
| `vmlinux` | **4,573,867** bytes, sha256 `b69b2987e84eb4ab…` |
| uploadable image | `<imgwork>/s100L/s100L/kroot/rtkload/nfjrom`, **1,181,696** bytes |
| `--image-sha256` | `671b0c872db59539aa470936a52d2f02295a00a5ff30bf9a5ef14bba2217c590` |
| driver | `rtl819x-nic 1.3`, `rtl819x-switch 1.1` |

🔴 **`RECIPE_ID` is the same for the quiet arm built the same evening
(`s100a`), which is `FW-99` behaving exactly as documented**: the id is a
digest over `config/` and cannot tell two variants apart. The discriminator is
the `--image-sha256` row above, and `looprun` checks it.

### 1.1 What is new

1. **`nic_ph_follow` defaults to 1.** `NET-102`'s 250× fix is the compiled
   default instead of a verb. `phfollow 0` still reaches the old path and has
   a measured signature (0.04–0.07 Mbit/s) to be recognised by.
2. **ethtool ops** — see § 0 ①.
3. **`nic_ph_last_cls`**, written on *every* inspection, which is what makes
   `CORRECTIONS-block40.md` § 5.3's dereference identity evaluable at all.
4. **`rx_ph` / `rx_mb` / `tx_ph` / `tx_mb` / `idle_ring` on the dump**, which
   makes the `phtest` comment's claim — that its arguments come from bases
   *"this same file prints"* — true for the first time.
5. **`tpdcr1_pos` / `tpdcr2_pos` / `tpdcr3_pos` on the dump.**
6. **`txrings 1|4` verb** — `NET-67` H1.
7. **`config/host-compat/0007`** plus one `kconfig-delta` row.

### 1.2 What was verified at the desk, before power

* `kconfig-delta check` — **green**, every difference between the vendor
  template and the built `.config` is declared; `(NEW)` is 0, which is what
  the delta row predicted.
* `rlxfw-marks verify --absent <vendor vmlinux>` — **12 marks present once, 9
  witnesses present, 1 confirmed absent, and absent from the vendor artefact.**
* 🟢🟢 **The guard is in the ARTEFACT, not just in the patch.** 量,
  `mips-linux-gnu-objdump` on `s100L.vmlinux.elf` at the `re865x_open` symbol
  `System.map` names:

  ```
  addiu sp,sp,-32
  li    v0,-19          <- -ENODEV
  jr    ra
  addiu sp,sp,32
  ```

  Four instructions; the whole body is dead-code eliminated. **The control is
  the same tool on `s99c`**, where the same symbol begins
  `addiu sp,sp,-64 / sw s4,48(sp) / … / lw s2,180(a0)` and runs past 0x378.

---

## § 2 What this block decides

### 2.1 🔴🔴 `A` — `D4` stops being an inference and becomes a command

Every previous statement that the vendor is not carrying the traffic has been
about something that **happened not to occur**: a `request_irq` that
succeeded, a `CPUICR` that read 0, rings at addresses this driver allocated.
This cell makes one of them impossible instead.

* **`A3-ETH0` — `ifconfig eth0 up` must FAIL.** 推 an error line on the
  console (`busybox ifconfig` prints `SIOCSIFFLAGS:` plus the strerror of
  `ENODEV`). **REFUTED BY** the command succeeding, which would mean the
  symbol did not take — and § 1.2's disassembly says it did.
* **`A3-DEV` — `/proc/net/dev` still LISTS `eth0`…`eth4`.** This is the half
  that stops the result being over-read: the interfaces are *registered* and
  *un-openable*, not absent. A card that predicted their absence would be
  describing the design I abandoned.
* 🔴 The **negative control is the same command on `rlx0`**, which must
  succeed in the same boot (`A2-UP`).

### 2.2 🔴 `B` — 17 Mbit/s with no verb typed

`docs/KNOWN-ISSUES.md` records seating 37's own limit in as many words: *a
driver whose correct behaviour requires a verb is not a driver that works.*

* **`B2-IPERF` runs before any `phfollow` is typed on this boot.** 推 a figure
  in the **15–18 Mbit/s** band. **REFUTED BY** anything in the 0.04–0.07
  band, which is the arm-0 signature and would mean the compiled default did
  not take.
* **`A4-BASE` must read `ph_follow 1`** *before* `B2` runs, so the claim rests
  on a field and not only on the throughput.
* **`B4-PH0` is the control**: `phfollow 0`, re-run, 推 0.04–0.07 Mbit/s.
  Without it the band above is one arm of a comparison that was never made —
  which is the defect `notes/nic-driver.md` § 16.3b records against seating
  37's own A/B.

### 2.3 🔴 `C` — `NET-67` H1, single variable on one boot

`nic_do_arm` writes **zero** to `CPUTPDCR1/2/3`. 讀 `NET-48`: this die's own
loader runs TX0 **and** TX1 armed (`A040FC88` / `A040FCA0`), and the vendor's
`swNic_init` arms four. `TXFD` is one doorbell bit with **no ring number**
(`rtl865xc_asicregs.h:538`). So *three of the four TX bases hold zero* is a
difference between this driver and **both** implementations that do not wedge,
and no seating has ever read those three registers.

* **`C1-REST` reads them at rest** — 推 `tpdcr1_pos`/`tpdcr2_pos`/`tpdcr3_pos`
  all `00000000`. **This reading alone is worth the cell**: it is the first
  time the register has been on a dump.
* **`C3-ARM4`** sets `txrings 4` and re-arms; 推 all three read `idle_ring`.
* **`C4-DOSE` / `C6-DOSE` are the A/B**: the same `Y5` dose at `txrings 1` and
  at `txrings 4`, `recover 0` in both so the detector cannot mask the answer.
  **REFUTED BY** `n_tx_stop` moving by the same amount in both arms, which
  would retire H1.
* ⚠️ **This is not predicted to succeed.** Seven `NET-67` candidates have died.
  What makes the cell worth a power press is that the *reading* is new
  whatever the outcome.

### 2.4 ⚠️ `A0` — the boot capture is a hard byte prediction

推 **7,717 bytes**, byte-for-byte the count `s99c` produced, because **no mark
on the boot path changed**: the driver gained no `rlxfw_mark`, the switch
driver gained none, the initramfs spec is byte-identical to `s99c`'s (量,
`cmp` returns 0), and `RLXFW-ID0`'s value is the same width. 推
`RLXFW-ID0=82724C8F`.

🔴 **REFUTED BY** any other length. The two ways it can move are worth naming
now: the vendor's `eth%d added…` lines are still printed (its registration
loop is untouched), so their *absence* would mean I patched more than I
think; and a shorter capture would most likely be a boot that stopped.

---

## § 3 Standing rules for this seating

🔴 **No flash write. No `FLR`. No `EW`/`EB`/`FLW`/`AUTOBURN` typed by hand.**
🔴 **No `ifconfig rlx0 down`** — `NET-58`, reproduced on demand as seating 36's
`X16`.
🔴 **No `arm` with the engine running** — `NET-64`, 112 minutes of a hard-hung
board and 0 console bytes. Every re-arm on this card orders `engine off`
first.
🔴 **Every `--send` is ≤ 127 characters.** `_check_send` refuses at `>= 128`;
seating 36 lost a whole cell to a 133-character line.
🔴 **No `$` in any `--send`** — the card's own `no-shell-subst` row counts
them and a shell substitution is evaluated on the board, not by me.
🔴 **Board-side `ping` ignores `-c`** (`NET-26`) — every ping cell is
host-side.
🔴 **Board-side `iperf3` goes to the BACKGROUND with `&`** — seating 31 lost
its only shell to a foreground client, and seating 37 recorded the fix.
⚠️ **One `cat` is TWO `read_proc` invocations** (`FW-64`), so `n_reads` moves
by 2 per dump cell.
🟢 **Extra boots are free**: `busybox reboot -f` reaches the loader prompt in
2.407 s (`FW-37`).

---

## § 4 The cells

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400`
`NB`  = `/usr/bin/python3 tools/netblast.py`
`HOST <prefix> :: <cmd>` runs `<cmd>` on the workstation with output to `<prefix>.log`.

### Part A — boot `s100L`, and `D4`'s discriminator

```
HOST bench/2026-09-22b/A0 :: looprun --mode bench --cell A0 --skip S2,S3 --recipe-override 82724c8f --image /home/key/fwre-work/rebuild/imgwork/s100L/s100L/kroot/rtkload/nfjrom --image-sha256 671b0c872db59539aa470936a52d2f02295a00a5ff30bf9a5ef14bba2217c590
CAP --out bench/2026-09-22b/A1-SW --send 'echo unlock i-mean-it > /proc/rtl819x-switch ; echo start > /proc/rtl819x-switch' --idle 3 --seconds 30
CAP --out bench/2026-09-22b/A2-UP --send 'echo unlock > /proc/rtl819x-nic ; echo netdev on > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 30
CAP --out bench/2026-09-22b/A3-DEV --send 'cat /proc/net/dev' --idle 3 --seconds 30
CAP --out bench/2026-09-22b/A3-ETH0 --send 'ifconfig eth0 up' --idle 5 --seconds 30
CAP --out bench/2026-09-22b/A3-ETH0B --send 'ifconfig eth0' --idle 3 --seconds 30
CAP --out bench/2026-09-22b/A4-BASE --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
HOST bench/2026-09-22b/A5-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
CAP --out bench/2026-09-22b/A6-SW --send 'cat /proc/rtl819x-switch' --idle 3 --seconds 30
```

* `A0` — 推 `A0-boot.log` **7,717 bytes**, `RLXFW-ID0=82724C8F`.
  🔴 **`S5b` must read `00000000`**; if it does not, an upload writes flash and
  **the seating stops**.
* `A1-SW` — `R6-5`'s 通電前必做. Without it every ping is 100 % loss and reads
  as a driver fault.
* `A3-DEV` — 推 `lo`, `rlx0`, **and** `eth0`…`eth4`. § 2.1.
* `A3-ETH0` — 🔴 **must fail.** `--idle 5` because the error line is short and
  a 3 s idle can close the window before the shell finishes echoing.
* `A4-BASE` — 推 `ph_follow 1`, `tx_rings 1`, `tpdcr1_pos`/`tpdcr2_pos`/
  `tpdcr3_pos` all `00000000`, `ph_last_cls -1`, `n_et_link 0`,
  `et_link_last FFFFFFFF`, all `n_recov_*` 0, `truncated` **absent**.
  推 the offsets, not the addresses: `mb_ring − rx_ring` = `0x20`,
  `tx_ring − rx_ring` = `0x40`, `rx_ph − rx_ring` = `0x50`,
  `rx_mb − rx_ring` = `0x110`, `tx_ph − rx_ring` = `0x1D0`,
  `tx_mb − rx_ring` = `0x230`, `bufs − rx_ring` = `0x290`,
  **`idle_ring − bufs` = `0x6000`**.
* `A5-PING` — **4/4 or everything below is void.**

### Part B — the compiled default carries the traffic

```
CAP --out bench/2026-09-22b/B1-SRV --send 'iperf3 -s > /dev/null 2>&1 & sleep 3 ; ps' --idle 5 --seconds 30
HOST bench/2026-09-22b/B2-IPERF :: timeout 70 qemu-mips-static /home/key/fwre-work/iperf3-port/iperf3 -c 10.1.1.3 -p 5201 -t 30 -i 10 -f m
CAP --out bench/2026-09-22b/B3-N --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-22b/B4-PH0 --send 'echo phfollow 0 > /proc/rtl819x-nic' --idle 3 --seconds 20
HOST bench/2026-09-22b/B5-IPERF0 :: timeout 70 qemu-mips-static /home/key/fwre-work/iperf3-port/iperf3 -c 10.1.1.3 -p 5201 -t 30 -i 10 -f m
CAP --out bench/2026-09-22b/B6-N --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-22b/B7-PH1 --send 'echo phfollow 1 > /proc/rtl819x-nic' --idle 3 --seconds 20
```

* `B2-IPERF` — 推 **15–18 Mbit/s**, with **no `phfollow` typed on this boot**.
* `B3-N` — 推 `n_ph_used` **large and non-zero**; that counter increments only
  on the branch that returns the followed pointer, so it is what says the
  compiled default is the one in force.
* `B5-IPERF0` — the control. 推 **0.04–0.07 Mbit/s** and a receiver reporting
  `0.00 Bytes`.
* `B7-PH1` restores the default before Part C, so C's arms differ in one
  variable and not two.

### Part C — `NET-67` H1: three TX bases that have never been read

```
CAP --out bench/2026-09-22b/C1-REST --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-22b/C2-OFF --send 'echo recover 0 > /proc/rtl819x-nic ; echo engine off > /proc/rtl819x-nic' --idle 3 --seconds 20
HOST bench/2026-09-22b/C4-DOSE :: NB blast --host 10.1.1.3 --frames 347 --size 1400 --rate 43
CAP --out bench/2026-09-22b/C5-N --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-22b/C6-ARM4 --send 'echo engine off > /proc/rtl819x-nic ; echo txrings 4 > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic' --idle 3 --seconds 20
CAP --out bench/2026-09-22b/C7-ON --send 'echo engine on > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
HOST bench/2026-09-22b/C8-DOSE :: NB blast --host 10.1.1.3 --frames 347 --size 1400 --rate 43
CAP --out bench/2026-09-22b/C9-N --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
HOST bench/2026-09-22b/C9-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
```

* `C1-REST` — the arm-1 baseline for `n_tx_stop`.
* `C5-N` / `C9-N` — the A/B. 推 nothing; what is measured is whether
  `Δn_tx_stop` differs between the arms.
* `C7-ON` — 推 `tx_rings 4` and all three `tpdcr*_pos` reading `idle_ring`.
  🔴 **If they read `00000000` the verb did not take and `C8` is void.**
* `C9-PING` — the board must still answer. A dead board here is a finding, and
  the recovery is `busybox reboot -f`.

---

## § 5 What this block does NOT do

* It does **not** exercise the ethtool ops (§ 0 ①).
* It does **not** close `D4` as written (§ 0 ②).
* It does **not** run `R6-6`'s write half. Two of its three DoD clauses were
  measured unreachable before power on an earlier card and nothing here moves
  them.
* It does **not** run the 30-minute flood; `D6` was obtained at seating 32 and
  a DoD is cumulative across a gate.
* It runs **no `FLR`**, so the flash bracket stays where it is.

```cells
bench/2026-09-22b/A1-SW
bench/2026-09-22b/A2-UP
bench/2026-09-22b/A3-DEV
bench/2026-09-22b/A3-ETH0
bench/2026-09-22b/A3-ETH0B
bench/2026-09-22b/A4-BASE
bench/2026-09-22b/A5-PING
bench/2026-09-22b/A6-SW
bench/2026-09-22b/B1-SRV
bench/2026-09-22b/B2-IPERF
bench/2026-09-22b/B3-N
bench/2026-09-22b/B4-PH0
bench/2026-09-22b/B5-IPERF0
bench/2026-09-22b/B6-N
bench/2026-09-22b/B7-PH1
bench/2026-09-22b/C1-REST
bench/2026-09-22b/C2-OFF
bench/2026-09-22b/C4-DOSE
bench/2026-09-22b/C5-N
bench/2026-09-22b/C6-ARM4
bench/2026-09-22b/C7-ON
bench/2026-09-22b/C8-DOSE
bench/2026-09-22b/C9-N
bench/2026-09-22b/C9-PING
```

```cardnum
cells-fence	24	count bench/2026-09-22b/PREDICTIONS-B43-block41.md ^bench/2026-09-22b/[A-C]
declared-date	1	count bench/2026-09-22b/PREDICTIONS-B43-block41.md [*][*]declared date 2026-09-22[*][*]
cap-cells	18	count bench/2026-09-22b/PREDICTIONS-B43-block41.md ^CAP -{2}out
host-cells	7	count bench/2026-09-22b/PREDICTIONS-B43-block41.md ^HOST bench/2026-09-22b/
blast-cells	2	count bench/2026-09-22b/PREDICTIONS-B43-block41.md ^HOST .*NB blast
send-over-127	0	count bench/2026-09-22b/PREDICTIONS-B43-block41.md -{2}send '[^']{128,}'
no-shell-subst	0	count bench/2026-09-22b/PREDICTIONS-B43-block41.md -{2}send '[^']*[$]
no-flr	0	count bench/2026-09-22b/PREDICTIONS-B43-block41.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-22b/PREDICTIONS-B43-block41.md -{2}send '[^']*(EW |EB |FLW )
no-burn	0	count bench/2026-09-22b/PREDICTIONS-B43-block41.md -{2}send '[^']*AUTOBURN
no-ifdown	0	count bench/2026-09-22b/PREDICTIONS-B43-block41.md -{2}send '[^']*ifconfig rlx0 down
```
