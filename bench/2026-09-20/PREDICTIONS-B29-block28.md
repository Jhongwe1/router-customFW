# Block 28 — `R6-5`'s numbers, and a contradiction between this project's own positive control and its own refutation condition

**Frozen before these cells.** Seating 29, `bench/2026-09-20/`.
**declared date 2026-09-20**. Image `r6if1`, `RECIPE_ID` `edc94765`.

🔴 **This card does NOT say "frozen before power", and that is deliberate.** The
board was powered at **01:34:18** and has been at the `<RealTek>` prompt since;
§ 0.3 names every capture that predates this card and says what may and may not
be concluded from each.

---

## 0. What this block is

`R6-5`, the last step of `R6` that needs power. Two DoD rows, quoted verbatim
from `PROGRESS.md`:

> * **D5** an `iperf3` number exists, with the method that produced it and its
>   spread over at least three runs.
> * **D6** 30 minutes of continuous flood: zero drops by the driver's own
>   counters, zero oops, kernel log captured whole.

and the step row's own warning, also verbatim:

> 🔴 **A single number is not a curve.** This project has recorded that shape
> four times; one `iperf3` run is one sample

🔴 **And a third thing, which is not in the DoD and is the reason this card is
not just six `iperf3` runs.** `rtl819x-nic.c:93-110` pre-registers it:

> `rings, descriptors AND packet buffers are all reached through KSEG1. The
> cost is R6-5's to measure; it is not paid here on a guess that it is small.`

Every transmitted byte crosses `cached skb → uncached KSEG1 buffer` and every
received byte crosses back. **A bare throughput number would therefore report a
memory limit while looking like a driver limit.** § 2.5 is the cell group that
tells those apart, and it is the difference between a number and a result.

### 0.1 The instrument

`iperf 3.1.3`, cross-built for this part, **252,644 bytes**, static, no
`PT_INTERP`, MIPS-I MSB o32, sha256
`3144db60bd3895f582f84e61da306f96f6e668f07cf9a84fef0ebc6b971a97e8`.

🟢 **It is in the image for the first time.** `config/rlxfw-initramfs.tsv` gained
one `file` row today (38 → **39** entries), which is a `config/` change, so
`RECIPE_ID` moved and the image was rebuilt. The binary itself is **not** under
`config/` — it is at `$REPO/build/rlxfw-user/iperf3/iperf3`, produced by an
`install` target added to `config/rlxfw-user/iperf3/Makefile` today, mirroring
`isaprobe`'s split for the reason that file states: `RECIPE_ID` is
`find config -type f` with no exclusions and does not consult `.gitignore`.

🟢 **The rebuild through the new rule reproduced the audited binary byte for
byte** — same sha256 as the artefact `notes/iperf3-port.md` recorded. That is a
control on the recipe, not a formality: a different sha256 would have meant the
committed recipe does not build the committed measurement.

⚠️ **`RECIPE_ID` cannot see this binary.** The id is a digest over `config/`
and the product lives under `build/`, so two different builds of `iperf3` give
two images with the **same** `RLXFW-ID0`. What pins the artefact is the
assembled image's own sha256, in § 0.2.

### 0.2 The image, re-derived on this desk today

| | | how |
|---|---|---|
| cell | `r6if1` | a NEW name — `RUNSHEET` rule 2, one cell name per image |
| `RECIPE_ID` | **`edc94765`** | 🟢 **two independent derivations agreed**: the by-hand `find config -type f -print0 \| LC_ALL=C sort -z \| xargs -0 sha256sum \| sha256sum \| cut -c1-8`, and `rlxfw-kbuild.sh --dry-run`, which stages nothing |
| kernel delta | 49 set, 23 derive | from the build's own `kconfig-delta` line |
| initramfs | **39** entries, spec sha256 `7130245fbcd92afc` | `mkinitramfs build` |
| `vmlinux` | **4,464,774** bytes, sha256 `4e2da0b42aaf5e9f` | the manifest |
| decompressed | **3,943,424** of 5,242,880 = **75.2 %** | `mkinitramfs --kernel-image`, margin 1,299,456 |
| **`nfjrom`** | **1,152,000** bytes, sha256 `89051d6a396c305b` | `rtkimage build` |
| marks | 25 | the manifest |

🔴 **`ffe4b5cf` (`r6nic5`) and `f2aa2fdd` (the tree at the eighty-ninth
segment's close) are both STALE.** A card predicting either would judge a board
carrying the correct image RED. Every id above was read off an artefact built
today.

### 0.3 🔴 What predates this card, and what each capture may be used for

| | when | may be used for | may NOT be used for |
|---|---|---|---|
| `s90-C0-escwin` (scratchpad, **not** in `bench/`) | 01:34:18 | that the board reached `<RealTek>` on a **cold** power-on — the loader banner carries no `Reboot Result from Watchdog Timeout!` | nothing about Linux, the drivers, or this image |
| `s90-preflight` (scratchpad) | 01:33 | that the adapter, port and capture tool work with the board OFF — 0 bytes, 3.081839 s, three artefacts, rc 1 | anything about the board |

Both are deliberately **outside** `bench/`, so `check-predictions` never sees
them and `capdate` never counts them. Neither is a cell of this card.

⚠️ **The host side was changed before this card was frozen**, and it is recorded
here rather than left to be inferred: `enxfc19286184c9` was brought up with
`10.1.1.2/24` and the neighbour table flushed, because it was DOWN with no
address and `ip -4 route get 10.1.1.1` resolved through WSL's NAT'd `eth0` —
**the fifth time that state has been reached** (`RUNSHEET` `P3` names seatings
16, 19 and 24). `loader-tftp.py` does not bind a source address, so the upload
would have left the wrong interface. `iperf3 3.16` was installed on the host in
the same window.

### 0.4 🔴 Hazards, pre-registered

**① THE CENTRAL ONE: § 7.6's positive control and § 7.7's refutation condition
contradict each other, and a card that did not notice would have "refuted"
`R6-4a` with the hardware innocent.**

讀, six steps, every one from source:

1. `txstall on` clears `TXCMD` (`rtl819x-nic.c:1686`), so the engine stops
   retiring descriptors.
2. Four frames fill descriptors 0–3; each sets `dev->trans_start = jiffies`
   (`:935`).
3. The fifth finds `OWN` set → `netif_stop_queue()` + `n_tx_stop++`
   (`:851-852`). **`trans_start` is not updated on that path.**
4. `dev_watchdog` fires `ndo_tx_timeout` when the queue is stopped and
   `time_after(jiffies, trans_start + watchdog_timeo)`, and **re-arms itself
   every `watchdog_timeo`** (`net/sched/sch_generic.c:221-232`).
5. `nic_ndo_tx_timeout` **deliberately** does not refresh `trans_start`
   (`:1029-1031`), and `nic_tx_try_wake()` returns 0 while `TXCMD` is clear.
6. `CONFIG_HZ=100` → `watchdog_timeo` = 500 jiffies = **5.00 s**.

∴ **`n_tx_timeout` increments once every 5.00 s for as long as the positive
control holds the queue stopped.** § 7.7 makes `n_tx_timeout > 0` the
refutation of the design.

🟢 **Resolution, decided here and not at the bench**: `C9-BASE` reads
`n_tx_timeout` **before** the stall and `C11-OFF` reads it after, and
**§ 7.7's refutation is applied to the delta across the LOAD phase
(`C23-NIC1` minus `C12-RECOV`), never to the absolute.** A non-zero absolute
after a deliberate multi-second stall is the design working.

⚠️ **The driver is NOT edited to make the experiment agree.** Not refreshing
`trans_start` has its reason written at `:1029-1033`. Changing it would be
repairing the instrument to agree with the experiment — this project's own
`IRQ-13` lesson, where the tolerance was not widened and the window was moved.

⚠️ The first `ndo_tx_timeout` entry costs `dev->stats.tx_errors++` (`:1045`), so
`ifconfig rlx0` will show `TX packets:… errors:1` or more. **That is not a
hardware error** and `C45-FIFC` must not be read as one.

**② The `txstall` control can read `n_tx_stop 0` for a reason that is not the
driver.** 讀 `net/core/neighbour.c:991-1002` with `net/ipv4/arp.c:247`
(`queue_len = 3`): while a neighbour is `NUD_INCOMPLETE`, ICMP is queued in
`arp_queue` and **never reaches `ndo_start_xmit`**. With `TXCMD` clear the ARP
request goes out and no reply returns, so the neighbour stays INCOMPLETE and the
driver is offered **one** frame — not four, not five. `n_tx_stop` reads **0** and
the control looks like it ran.
🟢 **Which is why `C7-PING1` and `C8-PING2` come first**, and why the neighbour
must read `REACHABLE` on the host before `C10-STALL`. ⚠️ And the arithmetic
differs: a cold-ARP ping is `n_tx 5` (one ARP + four ICMP); with ARP warm it is
**4**.

**③ `txstall` is not a flag.** There is no `txstall` field in `/proc`. It is
`CPUICR &= ~TXCMD` (`:1686`), and `txstall off` is **two** writes — restore
`TXCMD` and ring the `TXFD` doorbell (`:1688-1691`). The only observable is
`now_icr` bit 31.

**④ `/proc/rtl865x/asicCounter` returns NOTHING to its reader.** 讀
`rtl865x_proc_debug.c:4406-4413`: the handler returns `len = 0` and writes
straight to the console. **`cat … > file` gives a zero-byte file and a pipe gets
nothing.** The serial capture is the only possible reader, which is why every
`asicCounter` cell uses `--until CpuEvent`.

**⑤ Its "64-bit" value is `lo + (hi << 22)`, not `hi<<32 | lo`.** 量
`rtl865x_asicCom.c:1500-1510`, the `CONFIG_RTL_8196E` branch. **推**, and it is
the inference this card exists partly to test: that shift is arithmetic only if
the low register holds **22 valid bits** (wrapping at 4,194,304 bytes ≈ **0.34 s
at line rate**). No source in this repository says so and nothing has measured
it. § 2.4 is the cheap test.

**⑥ It is NOT read-to-clear** — 讀 three ways (the proc handler has one
statement besides `return`; `rtl8651_returnAsicCounter` is a plain read;
`rtl865xC_returnAsicCounter64` is two plain reads). Clearing is an explicit
`echo clear >`, which is a **write to switch silicon**. 🔴 **Decided before
power: this card issues no `clear`.** Deltas are used instead, and `C13`/`C14`
measure the read-to-clear question directly.

**⑦ `ping` ignores `-c` and always sends four** (`NET-26`). No cell passes `-c`.

**⑧ This image has no `grep`, no `dd`, no `md5sum`** (`FW-46`). All filtering is
host-side. **⑨ `rlxfw_mark()` interleaves character-by-character with ash's
echo** (`FW-47`), so a naive host-side `grep` for a mark misses it; **⑩ one
`cat` is two `read_proc` invocations** (`FW-64`), so `n_reads` moves by two per
`cat`.

**⑪ `C-19`: the console adapter has left the host USB bus after 7 min 24 s of
pure console idle.** A 30-minute flood is the longest unattended console window
this project has ever run. 🟢 **The sampling cadence in § 2.6 is also the
mitigation** — no gap exceeds ~190 s — and it is the same mechanism that makes
the flood a curve rather than two endpoints. One design, three purposes.

**⑫ No `$`, `"`, backtick or `sh -c` appears in any `--send` on this card.**
`cardcheck`'s `B9` sweeps the whole 70-card corpus, so one such character here
would make the tool refuse on **every** card in the repository. This is why no
cell reads `echo rc=$?` — every cell reads its **effect** instead, which is the
stronger reading anyway.

---

## 1. The boot

The board is at `<RealTek>`. Before `J`, `C1-BURN` reads the burn flag at
`0x8040D4A0`; **`00000000` is required and anything else stops the seating**
(`C-6`: the loader's echo and that word are two sources, and only the word
counts). The upload is `loader-tftp.py put` with `--rescue-report` and
`--expect-load 80500000`, to **RAM**, and `--filename` is passed explicitly
because `nfjrom` and `boot.img` are names the loader treats as auto-execute.

**Boot capture prediction: 1,874 bytes.**

Derived, not copied: `tools/bootbytes.py predict` gives `710 const + 1,164
marks (71 marks)` from `bench/2026-09-19b/r6nic2-att2-boot.log`, and
`config/rlxfw-marks.tsv` has not changed since commit `edb7122` — seating 28's
own commit — so `r6if1`'s boot mark set is identical to `r6nic2`'s. `iperf3`
adds **no** mark, because nothing execs it: `/init` does not.

**Refuted by** any other length. If it misses, the delta is divided by the mark
table in `bootbytes` and the responsible tag is named — a miss here is a
diagnosis, not a failure.

| field | predicted | why |
|---|---|---|
| `RLXFW-ID0` | **`EDC94765`** | read off the artefact built today, never copied from a row |
| `version` (2nd line of `/proc/rtl819x-nic`) | **`1.1`** | the cheapest "am I running the right image" gate — `r6nic5`'s source is 1.1 where seating 28's captures read 1.0 |
| `n_writes` at rest | **0** | every hardware write is behind a verb and an unlock |
| `boot_icr` | **`00000000`** | the vendor's probe disarmed the engine on this boot |
| `now_iimr` after `netdev on` | **`007E0FFE`** | 量, twelve seating-28 captures on `r6nic3`. 🔴 The **majority** value in the committed record is `000007FE`, ×20, and it is the **wrong image's** — a card predicting it would report a refutation that is a stale constant |

---

## 2. The predictions

### 2.1 `C4-SW` — the precondition that looks like a broken driver

`TRXRDY` is `SIRR` bit 0 at `0xBB804204`, *"Start normal TX and RX"*. 讀
`rtl865x_asicCom.c:1360`: it is raised by `rtl865x_start()`, called only from
`ndo_open` — **so in the rlxfw arrangement the vendor never runs it and nothing
else will set it.** 量 `NET-52`, a single-variable A/B on one boot: clear →
ping **0 of 4**, `n_rx` **0**, neighbour `INCOMPLETE`; set → ping **4 of 4**,
`n_rx` **5**, `REACHABLE`.

**Predicted**: `SW-START` appears in the capture; `C7-PING1` then completes.
**Refuted by**: 100 % loss after `C4-SW` succeeded — which would mean `TRXRDY`
is not the whole precondition.

### 2.2 `C9`–`C12` — Block A, `txstall`, and it runs BEFORE any load

**The ordering is the argument.** `txstall` settles *reachability* and *the wake
fires* before any load; the load then tests only *does it hold under load*. A
first flood against an untested wake tests two things at once, and a green
result cannot say which.

| cell | predicted | refuted by |
|---|---|---|
| `C9-BASE` | `n_tx_stop 0`, `n_tx_wake 0`, `tx_stopped 0`; **`n_tx_timeout` recorded as the baseline `T0`** | `tx_stopped 1` at rest — the queue is already stuck |
| `C10-STALL` | `now_icr` **`44000000`** (bit 31 clear); **`n_tx_stop > 0`**; the second `ping` shows loss | `n_tx_stop 0` → either the wake site is wrong, or hazard ② fired and the neighbour was not `REACHABLE`. **Those are different and the host's `ip neigh` reading separates them** |
| `C11-OFF` | `now_icr` back to **`C4000000`**; **`n_tx_wake > 0`**; `n_tx_wake + n_tx_wake_race >= n_tx_stop`; `tx_stopped 0` | `n_tx_stop > 0` with **both** wake counters 0 = wrong wake site. `n_tx_wake` exceeding `n_tx_stop + n_tx_wake_race` by more than 1 = the counters do not measure what they claim |
| `C12-RECOV` | `ping` **4 of 4** | 🔴 **transmit does not resume ⇒ clearing `TXCMD` mid-flight wedges the engine, the control is VOID, and this seating falls back to the flood alone.** That is `txstall`'s own refutation condition and it is written here before it runs |

⚠️ `now_icr` reading **`C4800000`** instead of `C4000000` after `C11-OFF` would
mean `TXFD` does **not** self-clear. That is **unmeasured anywhere in this
repository** — it is a finding, not a failure.

⚠️ **`n_tx_timeout` is expected to be NON-ZERO at `C11-OFF`**, by § 0.4 ①.
§ 7.7's refutation applies to `C23-NIC1` minus `C12-RECOV`.

### 2.3 Counter movement, stated so a wrong one is visible

`FW-64`: one `cat` is **two** `read_proc` invocations, so `n_reads` moves by
**2** per `cat`, not 1.

| verb | `n_writes` | why |
|---|---|---|
| `txstall on` | **+1** | `:1684` |
| `txstall off` | **+2** | `:1684` and `:1690` — the restore and the doorbell |

### 2.4 `C13`–`C16` — Block B, the second source, and its own arithmetic

Two questions, both cheap, both answered before anything depends on them.

**Q1 — is it read-to-clear?** `C13-AC1` then `C14-AC2` back to back with no
traffic between. **Predicted: `C14 ≈ C13`** (not read-to-clear, 讀 three ways).
**Refuted by** `C14` reading zeros, which would mean every `asicCounter` reading
this project takes is a delta and not a total.

**Q2 — is the 64-bit value really `lo + (hi << 22)`?** `C15-ACT` puts a known,
small, exactly-counted amount of traffic through (one `ping` = 4 × 98 + 60 bytes
on the measured pattern) and reads the driver's `nd_stats` in the same cell;
`C16-AC3` reads the ASIC side. **Predicted: `ΔasicCounter Snd` equals
`Δnd_stats tx_bytes` while both are far below 2²².** **Refuted by** a
disagreement below 2³², in which case the `<< 22` shift is the first suspect and
`asicCounter` is not usable as the flood's second source without a correction.

🔴 **This matters because the driver's counters are 32-bit** — `%lu` throughout,
and `struct net_device_stats` is `unsigned long` — so `tx_bytes` wraps at
2³² ÷ 12.5 MB/s = **343.6 s** at line rate. Over 30 minutes that is up to five
wraps. `asicCounter` is the independent second source **only if Q2 comes back
the expected way.**

### 2.5 `C17`–`C28` — Blocks C and D, `D5`, and the number's CAUSE

**Block C is `D5`: six runs, five forward and one reverse, each 10 s.** The
number reported is the median with its full spread; **five is more than the
three the DoD asks for**, because a spread over three samples is itself a
one-sample estimate of a spread.

Method, recorded with the number as `D5` requires: board is the **client**, host
is the **server**, `iperf3 -c 10.1.1.2 -t 10 -J`, default TCP, default window,
one stream, over switch port 3 (LAN3), 100 Mbit full duplex by the board's own
`PSRP3`. ⚠️ **Duplex is not taken from the host's `ethtool`** — `NET-30`
measured it reporting `Half` for a gigabit adapter over this usbip path, and the
board is the better source.

**The number is an UNCACHED-RING number and must be labelled so**, per
`rtl819x-nic.c:93-110`.

**Block D is the curve, and it is the part that makes the number mean
something.** Five UDP runs at offered rates 5 / 10 / 20 / 50 M and unlimited.
At each point three readings are taken from one `-J` document: the **achieved**
rate, the **loss**, and **`cpu_utilization_percent.host_total`**, which is the
client's — the board's — own CPU.

| outcome | what it means |
|---|---|
| achieved tracks offered until `host_total` approaches 100, then flattens | **CPU-bound.** The figure is a *this core, with uncached buffers* limit, not a driver limit |
| achieved flattens with `host_total` well under 100 | **not CPU-bound.** The limit is in the driver or the path, and that is the interesting answer |
| loss rises before either flattens | the offered rate exceeds what the ring absorbs; read `n_xmit_busy` and `n_tx_stop` in `C23-NIC1` |

⚠️ **`/proc/stat` is the intended independent second source for `host_total`**
and this card does **not** read it, because nothing in this repository has
confirmed `/proc/stat`'s presence or format on this kernel and a cell that might
print nothing is not a control. **Stated as a gap rather than papered over**;
it is one `cat` on a later seating.

⚠️ **A pktgen figure may not be quoted as a throughput number and an `iperf3`
figure may not be quoted as a driver-path rate.** This card runs no pktgen.

🔴 **`Retr` and `Cwnd` are suspect and the signature is known.** 量 today, the
same binary under `qemu-mips-static` against the host's 3.16:
`Retr 4290268386`, `Cwnd 1.98 GBytes`, `max_rtt 724226048`. Those are `TCP_INFO`
garbage. 讀 `notes/iperf3-port.md` § 6: on the device, uClibc's `netinet/tcp.h`
and this kernel's `linux/tcp.h` are identical (`sizeof` 104), so the 推 is that
they are **right** here. **Refuted by** any value of that shape, in which case
the reading is the instrument's and `bits_per_second` is unaffected.

🟢 **3.1.3 ↔ 3.16 interop is no longer 推.** 量 today, four cases, all rc 0:
TCP forward, TCP reverse, `-J`, and UDP `-b 10M` at **0/444 lost**. That was the
single most likely way this seating produced no number at all, and it cost no
power.

### 2.6 `C29`–`C45` — Block E, `D6`

One **continuous** 1,800 s TCP stream, backgrounded so the shell stays free,
with nine counter samples at ~180 s. 180 s is chosen because it is **below the
343.6 s wrap** of the 32-bit byte counters: every sample interval is
unambiguous without needing to know the rate first.

⚠️ The stream's output is redirected to a **relative** path after `cd /tmp`,
not to `/tmp/f1.txt`. `cardcheck` requires an absolute redirection target to be
a declared path and a runtime file cannot be one; the relative form is not a
way around the check but the honest shape — `/tmp` is declared (`1777`), the
file is runtime state.

| | predicted | refuted by |
|---|---|---|
| `D6` drops | `nd_stats drop 0/0`, `n_skb_fail 0`, `n_irq_spurious 0` throughout | any non-zero, which is `D6` failing and is reported as such |
| `D6` oops | **zero, and it is evidenceable**: `arch/rlx/kernel/traps.c:52` is `#define printk panic_printk` and `CONFIG_PANIC_PRINTK=y`, so the whole `die()` path reaches the console even with `CONFIG_PRINTK=n`. And `CONFIG_RTL_WTDOG=n` means `is_fault` is never set, so a panic **prints and stays** instead of being truncated at ~46 characters | any `die`/`Oops`/register dump in the capture |
| kernel log | **captured whole** — every cell of this block is an ungrepped console capture, and the console *is* the log on this image | — |
| `n_xmit_busy` | 🔴 **expected to MOVE, for the first time.** It read **0** in every flood of seating 28 and `netif_wake_queue` has never been called under real load. 讀 `LOG.md`: *"缺陷是真的，這個負載沒有碰到它"* | `n_xmit_busy` staying 0 across a 30-minute stream ⇒ the stop path is still unreached and `R6-4a` remains untested under load, which is a **narrower result, not a pass** |
| `n_tx_timeout` | **must not move** between `C12-RECOV` and `C43-FNIC` | any movement ⇒ § 7.7 fires: the ISR wake missed and only the 5 s watchdog saved it, so the design is wrong **even though the link survived** |
| two sources agree | `Σ Δnd_stats tx_bytes` (wrap-corrected) equals `Δ asicCounter Snd` | disagreement ⇒ § 0.4 ⑤'s `<< 22` is the first suspect, then the wrap correction |

🔴 **`NET-54`, and it is a result to capture rather than an accident to avoid.**
A four-way parallel 1400-byte flood once left the interface permanently deaf,
below both drivers — the vendor's own driver also sent 2 and received 0 — and
only a cold power-on recovered it. It happened **once**, and once is not a
reproduction; the mechanism is 未定.

**Abort rule, written before it can be needed:**

1. If `C45-FPING` is 0 of 4, **do not power-cycle yet.** Try
   `ifconfig rlx0 down ; ifconfig rlx0 10.1.1.3 up` — `ndo_open` calls
   `netif_start_queue`, so a merely stopped queue needs no power. **推, never
   measured; if it works it saves a power cycle and is itself a finding.**
2. If that does not recover it, take the full reading set **before** touching
   power: all eight `PSRP<n>`, `MACCR`, `FFCR`, `SWTCR0`, `/proc/rtl819x-nic`,
   and above all `/proc/rtl865x/asicCounter` — which is the one reading that
   separates *the switch got the frames and would not forward them to the CPU
   port* from *the port never saw them*. `SPEC.md` `NET-54 殘留` says the
   seating-28 reading set was too thin for exactly that reason.
3. Only then, a cold power-on, with the loader banner read for
   `Reboot Result from Watchdog Timeout!` — **absent** confirms cold.

---

## 3. The guards

* **Zero flash writes.** No `FLW`, `EW`, `EB`, `FLR` or burn command appears on
  this card. `C1-BURN` is a `DW` read. The image goes to **RAM** at
  `0x80500000`.
* **No `FLR` bracket runs**, so `FLS-26`'s ledger does not move and the
  0.0244 % figure is unchanged. Stated rather than left to be inferred.
* **No write to switch silicon beyond `TRXRDY`.** No `echo clear >
  /proc/rtl865x/asicCounter`, decided in § 0.4 ⑥.
* **No `-c` on any `ping`** (`NET-26`).
* **Every `--send` is under 128 characters** and contains no `$`, `"`, backtick
  or `sh -c` (§ 0.4 ⑫).
* **Every capture carries a terminator**, and no cell carries `--idle` at all —
  nine cells begin with a `sleep`, and `--idle` under a `sleep` is the defect
  that would have scored this seating `45 of 45` over empty captures
  (`CLAUDE.md`, eighteenth update). `--seconds` alone, throughout.

---

## 4. What this block does NOT claim

1. **It does not measure the vendor driver's throughput**, so there is no
   contrast number. The vendor's driver is still in the image and is not
   carrying this traffic, which is `R6-4`'s recorded gap, not this card's claim.
2. **It does not separate *uncached buffers* from *this core is slow*.** § 2.5
   tells CPU-bound from not-CPU-bound; it does not attribute the CPU cost to the
   KSEG1 copy. That needs a cached-buffer build as a contrast and is a different
   image.
3. **It does not isolate `NET-54`'s mechanism**, only its reproduction and its
   reading set.
4. **`/proc/stat` is not read**, so `host_total` has one source (§ 2.5).
5. **`ph_queueId`'s layout is still inherited from a declaration nothing has
   executed.** This card's frames are default-MTU; a larger frame may reach it.
6. **Whether TX rings 2 and 3 interrupt at all is undetermined.** This driver
   uses ring 0 only.
7. **It says nothing about the loader**, and no `FLR` ran.

---

## 5. The cells

Every line below is one invocation. `CAP` expands to
`/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0`.

```
#-- 1. the burn flag, at the loader prompt.  00000000 REQUIRED or the seating stops.
CAP --out bench/2026-09-20/C1-BURN --send 'DW 8040D4A0 1' --until 'RealTek>' --seconds 15

#-- 2. the boot.  1874 bytes predicted, RLXFW-ID0=EDC94765.
CAP --out bench/2026-09-20/C2-BOOT --send 'J 80500000' --seconds 45

#-- 3. at rest, before any verb.  version 1.1, n_writes 0, boot_icr 00000000.
CAP --out bench/2026-09-20/C3-NIC0 --send 'cat /proc/rtl819x-nic' --seconds 25

#-- 4. TRXRDY.  Without this, ping is 100 % loss and it looks like a broken driver.
CAP --out bench/2026-09-20/C4-SW --send 'echo unlock i-mean-it > /proc/rtl819x-switch ; echo start > /proc/rtl819x-switch ; cat /proc/rtl819x-switch' --seconds 30

#-- 5. unlock + netdev on.  ndo_open does alloc/arm/request_irq/napi/engine itself.
CAP --out bench/2026-09-20/C5-NIC --send 'echo unlock > /proc/rtl819x-nic ; echo netdev on > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --seconds 30

#-- 6. the interface.  now_iimr 007E0FFE, not 000007FE.
CAP --out bench/2026-09-20/C6-IFUP --send 'ifconfig rlx0 10.1.1.3 up ; ifconfig rlx0' --seconds 30

#-- 7. cold ARP: n_tx 5 (one ARP + four ICMP), not 4.
CAP --out bench/2026-09-20/C7-PING1 --send 'ping 10.1.1.2' --seconds 25

#-- 8. warm ARP: n_tx 4.  The neighbour must be REACHABLE before C10 -- hazard 2.
CAP --out bench/2026-09-20/C8-PING2 --send 'ping 10.1.1.2' --seconds 25

#-- 9. BASELINE for n_tx_timeout.  Hazard 1: the absolute is not the reading.
CAP --out bench/2026-09-20/C9-BASE --send 'cat /proc/rtl819x-nic' --seconds 25

#-- 10. the positive control.  TWO pings: the ring is four deep and ping sends four.
CAP --out bench/2026-09-20/C10-STALL --send 'echo txstall on > /proc/rtl819x-nic ; ping 10.1.1.2 ; ping 10.1.1.2 ; cat /proc/rtl819x-nic' --seconds 45

#-- 11. two writes, not one: restore TXCMD and ring TXFD.  now_icr back to C4000000.
CAP --out bench/2026-09-20/C11-OFF --send 'echo txstall off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --seconds 30

#-- 12. txstall's OWN refutation: no recovery here and the control is VOID.
CAP --out bench/2026-09-20/C12-RECOV --send 'ping 10.1.1.2 ; cat /proc/rtl819x-nic' --seconds 35

#-- 13. asicCounter read A.  Console only -- the handler returns len 0 to its reader.
CAP --out bench/2026-09-20/C13-AC1 --send 'cat /proc/rtl865x/asicCounter' --until 'CpuEvent' --seconds 30

#-- 14. read B, back to back, no traffic between.  B == A => NOT read-to-clear.
CAP --out bench/2026-09-20/C14-AC2 --send 'cat /proc/rtl865x/asicCounter' --until 'CpuEvent' --seconds 30

#-- 15. a known, small, exactly-counted amount of traffic, with the driver's own side.
CAP --out bench/2026-09-20/C15-ACT --send 'ping 10.1.1.2 ; cat /proc/rtl819x-nic' --seconds 35

#-- 16. read C.  Delta vs C15's nd_stats tests the << 22 in returnAsicCounter64.
CAP --out bench/2026-09-20/C16-AC3 --send 'cat /proc/rtl865x/asicCounter' --until 'CpuEvent' --seconds 30

#-- 17..21. D5.  Five forward runs.  A spread over three samples is a one-sample spread.
CAP --out bench/2026-09-20/C17-IP1 --send 'iperf3 -c 10.1.1.2 -t 10 -J' --seconds 45
CAP --out bench/2026-09-20/C18-IP2 --send 'iperf3 -c 10.1.1.2 -t 10 -J' --seconds 45
CAP --out bench/2026-09-20/C19-IP3 --send 'iperf3 -c 10.1.1.2 -t 10 -J' --seconds 45
CAP --out bench/2026-09-20/C20-IP4 --send 'iperf3 -c 10.1.1.2 -t 10 -J' --seconds 45
CAP --out bench/2026-09-20/C21-IP5 --send 'iperf3 -c 10.1.1.2 -t 10 -J' --seconds 45

#-- 22. the other direction: the board RECEIVES.  RX and TX are different paths.
CAP --out bench/2026-09-20/C22-IPR --send 'iperf3 -c 10.1.1.2 -t 10 -J -R' --seconds 45

#-- 23. the LOAD-phase end of the n_tx_timeout delta.  C23 minus C12 is the reading.
CAP --out bench/2026-09-20/C23-NIC1 --send 'cat /proc/rtl819x-nic' --seconds 25

#-- 24..28. the curve.  offered vs achieved vs the board's own CPU, from one -J each.
CAP --out bench/2026-09-20/C24-U5 --send 'iperf3 -c 10.1.1.2 -t 10 -u -b 5M -J' --seconds 45
CAP --out bench/2026-09-20/C25-U10 --send 'iperf3 -c 10.1.1.2 -t 10 -u -b 10M -J' --seconds 45
CAP --out bench/2026-09-20/C26-U20 --send 'iperf3 -c 10.1.1.2 -t 10 -u -b 20M -J' --seconds 45
CAP --out bench/2026-09-20/C27-U50 --send 'iperf3 -c 10.1.1.2 -t 10 -u -b 50M -J' --seconds 45
CAP --out bench/2026-09-20/C28-U0 --send 'iperf3 -c 10.1.1.2 -t 10 -u -b 0 -J' --seconds 45

#-- 29,30. the flood's two zero points, one per instrument.
CAP --out bench/2026-09-20/C29-F0 --send 'cat /proc/rtl819x-nic' --seconds 25
CAP --out bench/2026-09-20/C30-FAC0 --send 'cat /proc/rtl865x/asicCounter' --until 'CpuEvent' --seconds 30

#-- 31. D6.  One CONTINUOUS 1800 s stream, backgrounded so the shell stays free.
CAP --out bench/2026-09-20/C31-FSTART --send 'cd /tmp ; iperf3 -c 10.1.1.2 -t 1800 -i 60 > f1.txt 2>&1 &' --seconds 20

#-- 32..40. nine samples at 180 s.  180 < 343.6 s, so every interval is unambiguous
#--         without knowing the rate first -- and no console gap reaches C-19's 7m24s.
CAP --out bench/2026-09-20/C32-FS1 --send 'sleep 180 ; cat /proc/rtl819x-nic ; cat /proc/rtl865x/asicCounter' --seconds 260
CAP --out bench/2026-09-20/C33-FS2 --send 'sleep 180 ; cat /proc/rtl819x-nic ; cat /proc/rtl865x/asicCounter' --seconds 260
CAP --out bench/2026-09-20/C34-FS3 --send 'sleep 180 ; cat /proc/rtl819x-nic ; cat /proc/rtl865x/asicCounter' --seconds 260
CAP --out bench/2026-09-20/C35-FS4 --send 'sleep 180 ; cat /proc/rtl819x-nic ; cat /proc/rtl865x/asicCounter' --seconds 260
CAP --out bench/2026-09-20/C36-FS5 --send 'sleep 180 ; cat /proc/rtl819x-nic ; cat /proc/rtl865x/asicCounter' --seconds 260
CAP --out bench/2026-09-20/C37-FS6 --send 'sleep 180 ; cat /proc/rtl819x-nic ; cat /proc/rtl865x/asicCounter' --seconds 260
CAP --out bench/2026-09-20/C38-FS7 --send 'sleep 180 ; cat /proc/rtl819x-nic ; cat /proc/rtl865x/asicCounter' --seconds 260
CAP --out bench/2026-09-20/C39-FS8 --send 'sleep 180 ; cat /proc/rtl819x-nic ; cat /proc/rtl865x/asicCounter' --seconds 260
CAP --out bench/2026-09-20/C40-FS9 --send 'sleep 180 ; cat /proc/rtl819x-nic ; cat /proc/rtl865x/asicCounter' --seconds 260

#-- 41. wait out the remainder of the 1800 s, then the stream's own report.
CAP --out bench/2026-09-20/C41-FWAIT --send 'sleep 200 ; cd /tmp ; cat f1.txt' --seconds 280

#-- 42,43. the flood's two end points.
CAP --out bench/2026-09-20/C42-FNIC --send 'cat /proc/rtl819x-nic' --seconds 25
CAP --out bench/2026-09-20/C43-FAC --send 'cat /proc/rtl865x/asicCounter' --until 'CpuEvent' --seconds 30

#-- 44. NET-54.  0 of 4 here starts the abort ladder in section 2.6, not a power cycle.
CAP --out bench/2026-09-20/C44-FPING --send 'ping 10.1.1.2' --seconds 25

#-- 45. errors:N here is ndo_tx_timeout's tx_errors++, NOT a hardware error.
CAP --out bench/2026-09-20/C45-FIFC --send 'ifconfig rlx0' --seconds 25
```

### 5.1 The numbers this card states, and where each is re-derived FROM

```cardnum
cells-fence	45	count bench/2026-09-20/PREDICTIONS-B29-block28.md ^bench/2026-09-20/C[0-9]+-[A-Za-z0-9_]+$
image-bytes	1152000	size /home/key/fwre-work/rebuild/imgwork/r6if1/r6if1-20260920/kroot/rtkload/nfjrom
image-sha16	89051d6a396c305b	sha256-16 /home/key/fwre-work/rebuild/imgwork/r6if1/r6if1-20260920/kroot/rtkload/nfjrom
iperf3-bytes	252644	size build/rlxfw-user/iperf3/iperf3
iperf3-sha16	3144db60bd3895f5	sha256-16 build/rlxfw-user/iperf3/iperf3
initramfs-rows	39	count config/rlxfw-initramfs.tsv ^(dir|file|slink|nod)\t
declared-date	1	count bench/2026-09-20/PREDICTIONS-B29-block28.md [*][*]declared date 2026-09-20[*][*]
send-over-127	0	count bench/2026-09-20/PREDICTIONS-B29-block28.md -{2}send '[^']{128,}'
no-flr	0	count bench/2026-09-20/PREDICTIONS-B29-block28.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-20/PREDICTIONS-B29-block28.md -{2}send '[^']*(EW |EB |FLW )
no-burn	0	count bench/2026-09-20/PREDICTIONS-B29-block28.md -{2}send '[^']*AUTOBURN
no-idle	0	count bench/2026-09-20/PREDICTIONS-B29-block28.md -{2}send '[^']*' -{2}idle
no-shell-subst	0	count bench/2026-09-20/PREDICTIONS-B29-block28.md -{2}send '[^']*[$`]
no-asic-clear	0	count bench/2026-09-20/PREDICTIONS-B29-block28.md -{2}send '[^']*echo clear
no-ping-dash-c	0	count bench/2026-09-20/PREDICTIONS-B29-block28.md -{2}send '[^']*ping -c
no-autoexec	0	count bench/2026-09-20/PREDICTIONS-B29-block28.md ^CAP .*(allow-autoexec|boot[.]img)
sleep-cells	10	count bench/2026-09-20/PREDICTIONS-B29-block28.md -{2}send '[^']*sleep [0-9]
iperf-cells	12	count bench/2026-09-20/PREDICTIONS-B29-block28.md -{2}send '[^']*iperf3 -c
```

Nine of these eighteen rows are the card checking **itself** — the strongest
form, because a half-done edit is a red row before the board is powered rather
than something found at the bench. `no-idle`, `no-shell-subst`,
`no-asic-clear`, `no-ping-dash-c`, `no-burn` and `no-write-verb` are the § 3
guards expressed as arithmetic instead of as a promise.

## 6. The fence

```cells
bench/2026-09-20/C1-BURN
bench/2026-09-20/C2-BOOT
bench/2026-09-20/C3-NIC0
bench/2026-09-20/C4-SW
bench/2026-09-20/C5-NIC
bench/2026-09-20/C6-IFUP
bench/2026-09-20/C7-PING1
bench/2026-09-20/C8-PING2
bench/2026-09-20/C9-BASE
bench/2026-09-20/C10-STALL
bench/2026-09-20/C11-OFF
bench/2026-09-20/C12-RECOV
bench/2026-09-20/C13-AC1
bench/2026-09-20/C14-AC2
bench/2026-09-20/C15-ACT
bench/2026-09-20/C16-AC3
bench/2026-09-20/C17-IP1
bench/2026-09-20/C18-IP2
bench/2026-09-20/C19-IP3
bench/2026-09-20/C20-IP4
bench/2026-09-20/C21-IP5
bench/2026-09-20/C22-IPR
bench/2026-09-20/C23-NIC1
bench/2026-09-20/C24-U5
bench/2026-09-20/C25-U10
bench/2026-09-20/C26-U20
bench/2026-09-20/C27-U50
bench/2026-09-20/C28-U0
bench/2026-09-20/C29-F0
bench/2026-09-20/C30-FAC0
bench/2026-09-20/C31-FSTART
bench/2026-09-20/C32-FS1
bench/2026-09-20/C33-FS2
bench/2026-09-20/C34-FS3
bench/2026-09-20/C35-FS4
bench/2026-09-20/C36-FS5
bench/2026-09-20/C37-FS6
bench/2026-09-20/C38-FS7
bench/2026-09-20/C39-FS8
bench/2026-09-20/C40-FS9
bench/2026-09-20/C41-FWAIT
bench/2026-09-20/C42-FNIC
bench/2026-09-20/C43-FAC
bench/2026-09-20/C44-FPING
bench/2026-09-20/C45-FIFC
```
