# PREDICTIONS — block 43, seating 40 (`P2-4`, seating B: every `P2-3` number measured again, on a clock the host does not slew)

**declared date 2026-09-24** — **twelve power presses**, all on this date, the last
capture before midnight, and **another day than `bench/2026-09-23/PREDICTIONS-B44-block42.md`**
(`capdate` `D9`, `CAPD-1`): the `P2-4` DoD is every `P2-3` number measured again
on a second calendar day, with the date checked by that checker.

Marks: **量** measured on the device · **讀** read out of code or a dump ·
**推** inferred, pending a measurement.

Seating A is card `B44` (`bench/2026-09-23/PREDICTIONS-B44-block42.md`), what
departed from it is `bench/2026-09-23/CORRECTIONS-block42.md`, and its readings
are `notes/boot-time.md` § 7 and `notes/nic-driver.md` § 19. This card keeps
card A's twelve presses, their order and their groups, so that every cell `D3`
compares has the same composition on both days.

---

## § 0 Honesty notes, written rather than left to be found

**① Five instruments read silicon for the first time on this card, and none of
them has a board reading.** `console-capture` 1.5 and `hostprobe` 1.3 stamp on
`CLOCK_MONOTONIC_RAW` (`FW-115`, `FW-116`); `looprun` 1.3 stamps its stages on
RAW and holds the board up 2.5 s past every prompt (`S9`, `FW-127`); `hostclock`
1.0 logs the host's clocks for the whole seating (`FW-129`); `tools/cardrun.py`
1.0 runs every cell and owns the grammar `cardcheck` read this card with
(`FW-124`, `FW-132`). At the desk after the seating, `tools/iperflog.py` 1.0 reads
the board's own `iperf3` server logs for the first time (`FW-128`). Each has desk
controls and a rehearsal (the 108th segment's, over a pty); a cell that fails
because an instrument is wrong is a finding about the instrument and is reported
as that. **The board-side server strings were dry-run before the freeze** (量
2026-09-24, `$FWRE_WORK/rebuild/s109/qemu-sends/`): in the unit's own busybox ash
with the board's `iperf3`, under qemu, on a pty, through the vendor tripwire (21 runs,
all CLEAN), the four forms parse and run as written, the one-off server writes a
complete log and exits by itself, and `iperflog` at `c2e3caf` reads the logs (parse
0 on the board-receives trials, 1 by design on `-R`; compare AGREE). The same run
showed an option typo invisible at `-S0` — the server's log is still 0 bytes there —
which is why every `-S0` now ends its wait with `ps` and a gate (§ 3.5). The strings with
`ps` were dry-run again the same way (`qemu-sends/v2/`, 17 tripwire runs, all CLEAN): this
busybox cuts every `ps` row at 79 columns, 53 bytes of command line; under qemu a guest
server's row shows qemu's own argv, so no real server row can match there, and a native
process given the board server's exact argv rendered the 67-character row the gate
matches; a broken option, a stale server and the echoed command were all refused.

**② Nine of the twelve presses boot the vendor firmware, and a vendor boot can
write flash** — only its own config sectors, only when its config self-test fails
(`P2` settled item 5). Seating A's three brackets read the prediction exactly
(`FLS-30`). The rule is card A's: a `map` before and after every block that can
boot the vendor, and **a difference in any bracket stops every later vendor boot
until the owner has read it** (`P2` stop-loss). Here the stop is the runner's: the
map's three gates (§ 6) end the invocation.

**③ Every seating-A number this card uses was stamped on a clock that ran slow.**
The host's `CLOCK_MONOTONIC` ran at r = 0.9726–0.9861 of true time from ~15:49 on
2026-09-23 (`CLK-35`), because two time daemons fought over it (`CLK-38`,
`CLK-39`). This card predicts from seating A's values **divided by r**
("corrected": a loader catch by its own `r_best`, from the 106th segment's
`c-clock/f5-best.tsv`; any other capture by the median of the K, N and W references
over the five-minute window it began in, `f6-rt4.tsv` — a rule the 108th segment's
digest applied and no committed text states). The correction is itself derived: a
cold catch's r is uncertain by ±0.3–0.8 % at the loader instant, the 3–20 s swings
(0.953–0.994) are not resolved, and the corrected values still carry `FW-35`'s
per-read latency. A second rule — each kernel boot over the WSL kernel's printk clock
across its own span (this segment's second source) — gathers identical rlxfw boots
tighter (quiet `J` → prompt 0.006 % against 0.108 %), and differs from the window
rule by up to 0.6 % on one vendor boot (`V3`). **Every band below covers both
rules.**

**④ Seating B's clock regime is new, and it is guarded before power.**
`systemd-timesyncd` is stopped for the seating and started again after it; with it
stopped, `CLOCK_MONOTONIC` ran at RAW's rate (量 2026-09-23, E2's B phase, 1.00000
per minute from 100 s after the stop; `CLK-38`). The guard, `Z0-HCG`, is shown
**refusing** on this host (量 2026-09-24 11:03:52–11:04:52, the exact command, but
for its scratch `--out` and its 100 s wait, run with `timesyncd` active, `$FWRE_WORK/rebuild/s109/guard/`: the tick read 9566–10000,
one +0.551906 s step was seen by both of `hostclock`'s detectors, the report read
`strong`, and both of `Z0-HCG`'s gates refused it) and **permitting** only on the
tool's own format of the permitting lines — its permitting case on this host is
the seating's own first reading. Windows synchronizes its clock every 32,768 s
(量, five syncs from 2026-09-22 19:02:06 to 2026-09-24 07:26:38, `w32tm` and the
System log; the 07:26:38 sync wrote no event 37, so the log is not a complete
record of them) and WSL's `chronyd` then slews the guest to follow; the seating
is placed between two syncs (§ 4), and a sync inside it anyway is recorded, not
avoided (§ 3.8).

**⑤ What card A got wrong, and what this card does instead.** Its § 2 described
an order its § 5 did not have (`CORRECTIONS` § 2) — here § 2 is generated from
§ 5's fence. Its `Z9-D2` had no FILE (`CORRECTIONS` § 1) — here `cardcheck`
checked every `HOST` cell against its own tool (`FW-124`). Its vendor jumps had no
staged-head read-back (`CORRECTIONS` § 3) — here every `J 80500000` of the vendor
is preceded by `V*-HD`. Its throughput cells could not give per-trial driver
counters and lost every `rlx0` receive figure (`NET-112`) — here every `rlx0`
trial is bracketed by two driver dumps and read from the board's own server log.
Its `D8` stamp rule was wrong on a stepping host and its lower-edge rule held only
when a cycle's second broadcast was answered (`CLK-36`) — § 3.4 replaces both. Its
predictions that missed (`notes/boot-time.md` § 7.4–7.6: the vendor's `J` →
`boa` range, the 56-byte rtt, `P1-NMAP`'s "every port closed", "`tcp 80` follows
the `boa` line", "a UDP wedge is recovered", the cached-entry regime) are not
copied; each is re-derived from what seating A measured, or dropped with the
reason.

**⑥ One runner limit this card works around rather than fixes.** `cardrun`
stops on a cell's non-zero exit unless it is declared `NAME?`, and a `NAME?`
cell's later gates are skipped. `flashmap compare` exits 1 on the one `DIFFER` in
group 0 that every map since 2026-09-08 has read (`FLS-26`), so the map cell could
be neither stopped on nor gated. The `MB` macro ends in `; true`, and the verdict
is its three `grep=` gates, which require the exact expected lines (§ 6). A crash
of `flashmap` prints none of them and the gates stop the run (`FW-134`).

**⑦ A second runner gap, worked around the same way.** `cardrun` takes its items on its
command line, and this card's gates are regular expressions with backslashes, spaces and
parentheses, which a typed shell line would mangle while `--dry` still ended `ALL ITEMS
DONE`. `runblock.py` (`$FWRE_WORK/rebuild/s109/card/`, pinned by digest in `cardnum`)
lifts one § 6 fence's lines and hands them to `cardrun` as argv, never through a shell,
and refuses a card that differs from its commit; the desk dry run used the same function
and required every gate `cardrun` echoed to equal its fence line (`FW-134`).

---

## § 1 The images

The images seating A booted, unchanged: `p2q` (quiet) and `p2l` (loud), recipe
**`a2c56bc8`**, `nfjrom` **1,155,072 B `4972edbadd2655a8…`** and **1,181,696 B
`888c930aa31763d9…`**, initramfs content `51ea1604c7c163f3…`, driver
`rtl819x-nic 1.4` (card A § 1). 量 the chain is checked again by this card's own
`cardnum` rows at freeze: each manifest `verdict green` with its `vmlinux_sha256`;
each `rtkimage` record naming that vmlinux, that `nfjrom_sha256` and a CLEAN
tripwire verdict; each `nfjrom` on disk with that digest; and `looprun`'s
`--image-sha256` pins it again before the port opens. Nothing was rebuilt.

---

## § 2 The twelve presses, in order (generated from § 5's fence)

| press | block | what boots, and how | what it feeds |
|---|---|---|---|
| — | `Z0` | before power: pre-flight and its artefacts (`Z0-PREC`), the host's address, `hostclock` for the whole seating (`Z0-HC`) and its liveness (`Z0-HCW`), `timesyncd` stopped (`Z0-TSD`), the clock guard (`Z0-HCG`) | § 3.8 |
| **1** | `P1` rlxfw | cold catch (`esc`) → `P1L` loud rounds 1–3 (round 1 at the caught prompt; 2–3 `busybox reboot -f`, `esc_after`; every round held 2.5 s past its prompt) → `P1-RZ` warm catch → `P1Q` quiet rounds 1–4 → tick read `P1-TK0` → `map` → `FREE`/`PS`/`N0`/`AC0` → fifteen offset cells → ICMP, census → twelve `rlx0` trials → the handover → twelve `eth4` trials → tick read `P1-TK1`. A frame capture (`P1-TCPD`) runs across `P1L`…`P1Q` | `D2` rlxfw cold ×1, warm ×6; `D7` loud ×3 vs quiet ×4; `D8` rlxfw both images, framed; the channel offset; `D5` (a) and (b), both drivers; `D6`; `D4`'s `ps`; `NET-109`; ticks over ~35 min |
| **2–4** | `V1`–`V3` vendor cold | cold catch → burn flag → staged head → **`J 80500000`** | `D2` vendor cold ×3; `D8`, `D4` per port; `D5` (a) on the vendor; `V1`'s port census |
| **5** | `M1` vendor cold | **listen only**: the owner presses after `M1-BOOT` opens, and the loader autoboots | the capture-mode control, cold |
| **6** | `P2` rlxfw | cold catch → quiet rounds 1–2 → `TK0` → `map` → ICMP → `TK1` | bracket after `V1`–`M1`; `D2` rlxfw cold ×1, warm ×1; `D5` (a) |
| **7–10** | `V4`–`V7` vendor warm | cold catch → burn flag → **`J BFC00000`** caught warm → burn flag → staged head → **`J 80500000`** | `D2` vendor warm ×4; `D8`, `D4` warm |
| **11** | `M2` vendor warm | cold catch → burn flag → **`J BFC00000` listen only**: the warm reset autoboots | the capture-mode control, warm |
| **12** | `P3` rlxfw | cold catch → frame capture `P3-TCPD` → quiet rounds 1–2 → `TK0` → `map` → ICMP → `TK1` → `Z9-D2` → `D2`'s control and `D2` (`Z9-D2A`, `Z9-D2X`) | bracket after `V4`–`M2`; `D2` rlxfw cold ×1, warm ×1; `D5` (a); the ARP reconstruction's second frame check |
| — | `Z9` | after power-off: `hostclock` stopped and reported, `timesyncd` started | § 3.8 |

Why every vendor boot but two starts from a caught prompt, and why `J BFC00000`
from a prompt is a warm reset: card A § 2, unchanged (量 seating A: `D2` held with
both columns captured this way, `CLK-34`, and `V4`–`V7-WZ` carried the watchdog line
4 of 4).

---

## § 3 What this seating decides, and what would refute each

### 3.0 The clock every number here is on

**Seating B stamps on `CLOCK_MONOTONIC_RAW`** (`console-capture` 1.5, `hostprobe`
1.3, `looprun` 1.3, `hostclock` 1.0, and the runner's transcript). 量 2026-09-23
(§ 7.9 of `notes/boot-time.md`): RAW ran 1.000016 per Windows QPC second while
`CLOCK_MONOTONIC` ran 0.9650 — a second fit of the same log by this segment's second
source reads 1.000024–1.000041, so the method's own spread is tens of ppm — and
Windows' clock runs −36.42 ppm against NTP; so RAW is true time to about 50 ppm (推),
and nothing on this card resolves less.

Five kinds of interval, and what carries each from seating A to seating B (推,
the 108th segment's digest, re-derived here):

| kind | examples | seating A → seating B |
|---|---|---|
| **board** | every boot segment, `J` → prompt, `loader.*` | corrected (A raw ÷ r), then × g, the device factor between days |
| **host timer** | ARP retransmits, `ping -i`, `sleep`, `timeout 70` | face value: they ran on `CLOCK_MONOTONIC` and were stamped on it, and with `timesyncd` stopped MONOTONIC runs at RAW's rate (§ 3.8) |
| **mixed** | `J` → first ICMP reply | split: the board part corrected, the host part at face value (§ 3.4) |
| **clock-free** | bytes, digests, counts, tick ratios | unchanged |
| **realtime** | the host's `iperf3` rates, `ping` rtt | seating A's realtime ran at the slewed rate between steps; a 30 s trial held 0 or 1 step, so it read within about ±2.7 %. Seating B has no steps (§ 3.8) |

**g**, the device's own factor between two days: inference (iii) (§ 3.9) puts
seating B's warm `loader.booting` median in **[0.354469, 0.358031] s** — 0.35625 × 0.995
and × 1.005. 0.35625 s is not a registered value: it is the 106th segment's fit of the
loader factor against the host rate over 21 directories, read at r = 1
(`$FWRE_WORK/rebuild/s106/r-retro/REPORT.md`; 0.356246 refitted by this segment's
second source); the ±0.5 % is the seven directories whose host clock was right, whose
medians, 0.3546–0.3578 s, all lie inside it (`notes/boot-time.md` § 5). Seating A's corrected warm median is
**0.355963 s** (the 13 warm catches over their `r_best`, `c-clock/f5-best.tsv`), so
**g ∈ [0.99580, 1.00581]** (推). Card A's form of the model uses f = B/0.353718:
**f_B point 1.006347, band [1.002122, 1.012194]**. Two computations sharing no code
(this card's and the 108th segment's digest) give every number in this paragraph.

### 3.1 🔴 `D2` first — the identical-code control, computed before any comparison is read

Card A § 3.1, unchanged in every group, band and refutation — the groups by this
card's names:

| group | captures | mode | n |
|---|---|---|---:|
| rlxfw cold | `P1-A`, `P2-A`, `P3-A` | `esc` | 3 |
| vendor cold | `V1-A`, `V2-A`, `V3-A` | `esc` | 3 |
| rlxfw warm | `P1L-r02-rz`, `P1L-r03-rz`, `P1-RZ`, `P1Q-r02-rz`, `P1Q-r03-rz`, `P1Q-r04-rz`, `P2Q-r02-rz`, `P3Q-r02-rz` | `esc_after` | 8 |
| vendor warm | `V4-WZ`, `V5-WZ`, `V6-WZ`, `V7-WZ` | `esc_after` | 4 |
| loader-only cold (context) | `V4-A`…`V7-A`, `M2-A` | `esc` | 5 |
| mode control, cold | `M1-BOOT` | listen | 1 |
| mode control, warm | `M2-BOOT` | listen | 1 |

Quantity `loader.banner` (`Booting` → banner), from `Z9-D2.tsv`'s `loader` rows.
**Bands, as card A wrote them before seating A:** warm vs warm |Δ median| ≤ 10 ms;
cold vs cold ≤ 25 ms, a limit and not a characterisation at n = 3; `M1-BOOT`
against both cold groups and `M2-BOOT` against both warm groups ≤ 10 ms each, sign
not predicted; cold never compared with warm. 🔴 **Refutation** (the plan's): a
difference outside its band means the method is broken, and no comparison from
this seating is published until it agrees.

**What seating A's corrected values predict** (推; `notes/boot-time.md` § 7.1, the
106th segment's correction): warm +0.19 ms, cold +0.15 ms, the four mode-control
differences −0.73 … +0.27 ms. Seating B reads the same quantity on RAW with no
correction, so if the correction was right, seating B's raw differences land near
those and far inside the bands. The prediction is the band; these are what the
correction says, stated so that a seating-B difference near a band's edge is read
against them.

**Computed first, at the bench, from `Z9-D2.tsv`**, by the script the 105th segment
used for seating A: `Z9-D2A` checks its digest and re-runs it on seating A's own
`Z9-D2.tsv`, and its gates require § 7.1's six raw differences (+0.0078, −0.0004,
−0.0000, −0.0005, −0.0070, +0.0008 s) — or it is not the same computation — before
`Z9-D2X` runs it on seating B's.

### 3.2 Clock-free predictions — exact

The images, their `/init` and the loader are those of seating A, so every byte
count seating A measured is predicted exactly (量 seating A, `notes/boot-time.md`
§ 7.4; `cardnum` rows below re-read the seating-A files):

* every `P*Q-rNN-boot` **2,117 B**; every `P1L-rNN-boot` **7,948 + e B**, e = 0…12
  from the twelve `tmpReg[0x%x]` fields, normalised **7,948**; each carries
  **`RLXFW-ID0=A2C56BC8`** and **`RLXFW-N7=00000011`** (`looprun`'s `A3`);
* every map (`P1-M0`, `P2-M0`, `P3-M0`) **3,013 B**, body digest (the `MB`
  pipeline) **`0927be41e91fe4bd…`**, and `flashmap compare` exactly
  `DIFFER  000000  device c66a4126d7b1b862... dump 8494cc8666b5c6f6...` and
  `31 same, 1 DIFFER, 0 scope, 0 extra, 0 missing`; header `map_ran 1`,
  `map_rc 0`, `map_entries 32`, `map_hashed 4186112`, `map_h601_skipped 8192`,
  `map_h601_hashed 0`, `map_diff_units 0`, `map_truncated 0`, `map_lines 32`,
  `corrupt_at -1`. The first bracket's "before" is seating A's `P3-M0`, the last
  map on record. 🔴 **Any other body digest or group-0 digest stops every later
  vendor boot** until the owner has read it;
* every `P1-OFFnn` **139 B**, and `P1-OFF-HP` **15** `udp` events on port 50000,
  each `len=10`;
* every `V*-BOOT` **1,789 B**, ending `boa: starting server pid=350, port 80`, in
  one of seating A's two line orders (sha256 `2f921f7508dd69b4…` or
  `89df2d260b86e48d…`, `LDR-46`); `M1-BOOT` **1,901 B** and `M2-BOOT` **1,979 B**
  (推: the race swaps two whole lines, which moves no byte count);
* every `V*-HD` **118 B**, byte-identical to `bench/2026-08-31c/K2-2a.log` —
  `80500000: 00000000 00008021 40906000 00000000` and
  `80500010: 00000000 00000000 3C10805F 26101000`, the head of the vendor image
  the loader stages from flash at every reset (量 there, and the same words sit at
  `0x80A00110` in ten committed flash reads, e.g. `2026-08-24c/G8pre-rd6`);
* every `*-AB` / `*-AB2` burn flag **`00000001`**, every `looprun` `S5b` read
  **`00000000`**;
* `P1-N0` `recov_mode 1`, `ph_follow 1`; `P1-ETH4` `HWaddr 00:12:34:56:78:94`,
  `inet addr:10.1.1.4`, `Mask:255.0.0.0`, line 12 `eth4`; `P1-DOWN`
  `RLXFW-N-ENGOFF`, `RLXFW-N-NDSTOP` and no line 12;
* `P1-FREE` `MemTotal` **26,984 kB** (推, the same kernel); `MemFree` is a reading.

🔴 Refuted by any other count after normalisation. The mechanism that makes a
capture short (`early_printk.c:46-55`, card A § 3.2) is the one named for it.

### 3.3 `D7` — loud minus quiet, inside one press

Card A's test, unchanged in form (`FW-70`'s sustained rate 3,394.6–3,559.7 B/s,
`FW-32`'s residual 0.250 s, ΔB **5,831 B** at e = 0): **`D7` holds when Δ(`kernel.total`,
loud − quiet, press-1 medians) lies in [f_B·5,831/3,559.7 − 0.250,
f_B·5,831/3,394.6 + 0.250] s**, f_B this seating's own warm `loader.booting` median
over 0.353718. Over f_B's band that is **[1.391536, 1.988674] s** (at the f_B point
[1.398456, 1.978630]).

**Predicted** (推): seating A's Δ, 1.688630 s raw, is **1.712433 s** corrected (r
0.98610, the 15:52 window both press-1 blocks fell in), so seating B reads
1.712433 × g = **1.705 … 1.722 s** — inside the test band by at least 0.26 s, and
inside card A's no-residual range at f_B ([1.641536, 1.738674] over f_B's band) by
16 ms. Beside it, not instead of it: the implied rate f_B·ΔB/Δ, 89.237 % of 3,840
B/s at the f_B point — 0.8 points inside `FW-70`'s 88.4–92.7 %. ⚠️ `FW-70` and
`FW-32` were measured on host clocks whose r is not known, which moves the rate's
verdict and not the test band.

### 3.4 `D8` — network up, from the probe's own RAW ledger, for any k

**The host's ARP state is fixed as card A fixed it**: before every boot whose network
up is read, the host's entry for its address is flushed (`FL`, which prints `0`),
and both firmwares run under the host's own ARP retransmission. What seating A
showed about that regime (`CLK-36`, `notes/boot-time.md` § 7.3, § 7.7) and what
this card does with it:

* **Network up** is the first ICMP echo reply `hostprobe` records after the boot's
  jump, on the probe's own RAW ledger (its read time, and the kernel's receive time
  `t − lag_ms/1000`, both `hostprobe` 1.3 fields). **Card A's stamp rule — ping's
  `-D` realtime through `start_real − start_mono` — is dropped**: it put the first
  replies 1.362–2.270 s late on a stepping host.
* **It is published as a bracket and a k**, k the answered broadcast's place in its
  cycle. The host sends three broadcasts a cycle about 1 s apart, then fails the
  entry, and the next queued echo starts the next cycle. **Lower edge** = the later
  of the last broadcast before the answered one (the same cycle's k−1, or the
  previous cycle's third when k = 1) and, on rlxfw, the console's `RLXFW-N-NDOPEN`;
  **upper edge** = the answered broadcast. `hostprobe` records no ARP, so each
  broadcast is reconstructed from the ledger: a cycle's first at the send of the
  echo that opened it, the next ones at +1.000–1.028 s each (量 `P3-TCPD`, seating A:
  #1→#2 1.0004–1.0255 s, #2→#3 1.0200–1.0280 s, #3 → the failure's read
  1.0203–1.0248 s; the first broadcast −0.113…+0.024 ms from its trigger).
* **Frames check the reconstruction on two presses**: `P1-TCPD` across `P1L`…`P1Q`
  (the loud image's first network-up reading, and seven rlxfw boots), and
  `P3-TCPD` as in seating A, both through § 4's filter, which passes every frame this
  check reads. A reconstructed broadcast that the frames do not show
  cannot be a lower edge — 量 in seating A's `P3`, 11 of the 42 broadcasts the
  ledger implied never reached the wire, because the host loses carrier at each
  boot's NIC probe. On the vendor presses no frame is captured (§ 4), so a vendor
  lower edge rests on the reconstruction (推).
* **Void, decided now, for any k**: a boot whose `--neigh` record shows
  `56:0a:01:01:01:e8` valid between the flush and the first reply; a first reply
  whose answered broadcast has no earlier broadcast in its cycle or the previous
  one (no lower edge); and, on `P1`/`P3`, a boot whose answered broadcast the frames
  do not show.
* **Each round starts with no host entry for 10.1.1.3**, although the previous round's
  board answered (the dwell): 量 2026-09-24 this WSL's `net.ipv4.conf.all` and `.default`
  `arp_evict_nocarrier` read 1 (`$FWRE_WORK/rebuild/s109/premises.out`), so every carrier
  loss — each reset, each NIC probe — evicts the entry; `Z1-EVICT` reads the adapter's own
  value on the day. 推 `--neigh` reads
  no entry, `INCOMPLETE` or `FAILED` at every jump; an entry holding `rlx0`'s MAC at a
  jump is the cached regime, and such a boot is published apart.
* **The frames' clock.** `tcpdump -tt` stamps REALTIME; `hostclock convert` over `Z0-HC`
  puts each stamp on RAW and refuses one inside a step's uncertainty (推 none, with
  `timesyncd` stopped). The digest's optional host carrier log is not added: the frames
  already show which broadcasts reached the wire, and a sysfs poller would be one more
  instrument with no desk control on the seating.

**Predictions** (推; the board part corrected, the host part at face value):

| seconds after J | quiet (`P*Q`, 8 boots) | loud (`P1L`, 3 boots) | vendor (`V`, `M`, 9 boots) |
|---|---|---|---|
| J → NIC probe (board) | 6.621–6.706 (point 6.652) | 7.958–8.052 (7.994) | — |
| J → `N-NDOPEN` (board), or the vendor's ARP onset | 10.715–10.851 (10.764) | 12.450–12.591 (12.506) | onset 14.66–15.05: `Start NTP daemon` (J + 14.84–15.04 corrected) less 0.075–0.116 s, inference (i) |
| the host's broadcasts (host timer) | #2 at NIC + 4.18–4.27 (4.2158 in `P3Q-r02`'s frames), #3 1.020–1.028 later | the same | the host's own phase; seating A answered at a cycle's third (5 boots) or the next cycle's first (4) |
| k | **2**: `N-NDOPEN` leads #2 by 0.035–0.178 s | **3**: #2 comes 0.22–0.36 s before `N-NDOPEN` | 3 or 1 |
| first reply read | **10.81–10.98** (10.873); 11.83–12.01 if k = 3 | **13.16–13.36** (13.238) | **14.66–16.16** |
| bracket | [`N-NDOPEN`, #2], 0.035–0.178 s wide | [`N-NDOPEN`, #3], 0.661–0.806 s wide | [#k−1, #k], 1.020–1.028 s (k = 3) or 1.055–1.105 s (k = 1) |

Each board range is seating A's corrected values under both correction rules (§ 0 ③)
times g, the host part is the frames' timing at face value, and the read adds the
5.0 ms `P3Q-r02`'s frames put between the answered broadcast and the reply's read.
The rlxfw numbers are seating A's `Z9-D2.tsv` landmarks and `RLXFW-N-NDOPEN`'s
`FW-35` arrival, computed twice (this segment's second source and the 108th digest,
which agree to 0.1 ms); the vendor's are § 7.5's table and the `Start NTP daemon`
line's arrival.

* 🔴 **The loud image's k = 3 is refuted** by `P1-TCPD` showing the answered `is-at`
  after #2, or by a loud round with no reply before its next reset. If a first answer
  is lost, the next cycle's first broadcast comes about `N-NDOPEN` + 1.8 s, still
  inside the 2.5 s dwell.
* The quiet margin is thin (0.035–0.178 s): a boot whose `N-NDOPEN` lands after #2 is
  answered at k = 3, 1.02 s later — a reading of the margin on this day, not a miss of
  the method. The bracket then is [`N-NDOPEN`, #3].
* The vendor's first reply is the host's phase more than the boot's: seating A's
  spread 1.16 s in nine boots (§ 7.7). Its bracket, and inference (i), are what `D3`
  and § 3.9 read.

**The channel offset** — card A's fifteen `P1-OFF` cells and its test, unchanged:
offset_i = t_udp − t_console over `P1-OFF02`–`P1-OFF15`, stable when their range is
≤ 260.4 µs. 推 **it fires again**: seating A read 701.0 µs (probe read stamps) and
896.6 µs (kernel receive stamps), and nothing here changed the console's ~1 ms read
quantum. Then network up is published only as a console-side bound, as the plan
says.

### 3.5 `D5` — throughput

**(a) ICMP** — card A's `ICMP` at 56, 256, 512, 1,024 and 1,472 bytes, 20 echoes
each at 50 ms, rlxfw `P1`/`P2`/`P3` and vendor `V1`/`V2`/`V3`. 推 **0 % loss in all
thirty runs**, and each series' average inside seating A's range for its firmware
and size widened by ±10 % (`D3`):

| size | rlxfw, seating A | vendor, seating A |
|---|---|---|
| 56 B | 1.516–1.815 ms | 1.504–1.710 ms |
| 256 B | 1.367–1.641 | 1.653–2.180 |
| 512 B | 1.618–1.736 | 1.580–1.843 |
| 1,024 B | 2.030–2.124 | 1.743–1.998 |
| 1,472 B | 2.052–2.252 | 1.656–1.956 |

⚠️ Seating A's own series of one firmware and size differ by up to ±14 %, so a
single series pair is not a `D3`-stable quantity (§ 3.10); card A's 56-byte band
(1.9–3.5 ms, from 4-echo pings at 1 s) missed low 6/6 and is not reused.

**(b) `iperf3` 3.1.3** — the host client as card A ran it (the same MIPS binary under
`qemu-mips-static`, `timeout 70`, TCP `-t 30 -i 5`, UDP `-l 1400 -b 20M -i 1`, n = 3
each way and protocol, `rlx0` then `eth4`), and a new board side: **each trial
starts its own one-off server with its own log**, `iperf3 -s -1 -f k --logfile
/tmp/<T>.log`, and its `-S1` cell stops any server still running, then prints that
log. So every trial has the board's own figure whether or not the end-of-test
exchange completed (`NET-112`, `FW-128`), no `P1-SRV`, `P1-LSN` or restart is
needed, and every `rlx0` trial is bracketed by two driver dumps (`-S0` and `-S1`),
which card A's cells could not give (`CORRECTIONS` § 4). **`-S0` lists the processes
after its 2 s wait, and its gate requires this trial's own server among them** — a
`ps` row whose COMMAND column is exactly `iperf3 -s -1 -f k --logfile /tmp/<T>.log` —
anchored to the column after PID, USER, VSZ and STAT and to the row's end, so neither the
echoed command nor a shell wrapping the command line can match (量 qemu v2: without the
column anchor a `sh -c` wrapper's row passed). `P1-PS`'s own gate shows on the day that
the board's rows have that shape (`/bin/sh` as PID 1's command), before the first trial. Without it a server that never started shows only at `-S1`, as
`cat: can't open '/tmp/<T>.log'` (量 qemu, the broken-option control), and a server left
running by an earlier trial takes this trial's traffic into its own log while the
host's output looks perfect (量 qemu, the stale-server control); either stops the
invocation at `-S0`.

* `iperflog parse` exits **0** on every board-receives trial with a TEST_END summary
  and **1 by design on every `-R` trial** (the board sent; its figure there is the
  host's `receiver` line); `compare` refuses `-R` trials.

* 🔴 **The positive control comes first**: `iperflog compare` on the six `eth4`
  trials the host sees complete (`ER1`–`ER3`, `EU1`–`EU3`) must **AGREE 6 of 6**
  before any `rlx0` board figure is published. It refuses `-R` trials and any trial
  the host did not finish, so those six are the whole control population.
* `eth4` (推, seating A ±10 %, `NET-114`): TCP board-receives 24.4 / 24.7 / 25.0
  Mbit/s; TCP board-sends 26.2 ×3; UDP board-receives ~70 % lost, 5.956–5.958 Mbit/s
  received; UDP board-sends 19.9–20.0, 0 lost.
* `rlx0` TCP board-receives: **a first board-side reading**; 推 16–18 Mbit/s (the host
  sender ran 15.3–17.9 per 5 s in seating A, `NET-102` read 17.03 / 17.76 / 17.09).
* `rlx0` TCP board-sends: bimodal in seating A (23.6 / 0.21 / 0.78); no prediction of
  which trial collapses.
* `rlx0` UDP: 推 the failures recur (`NET-112`, `NET-113` are unchanged), and the
  board log is a first reading of what the board received.
* Board CPU from `/proc/stat` before and after each trial (推, seating A, `eth4`): TCP
  receive 53.5–55.7 %, TCP send 89.8 %, UDP receive 38.2–38.4 %, UDP send
  81.4–82.2 %.
* Per `rlx0` trial, the driver's `n_tx_stop`, `n_recov_fire`, `n_recov_ok`,
  `n_recov_fail` from `-S0` to `-S1` — first per-trial readings.

Order is card A's, TCP first: a wedged driver would void what follows. (c) ⊘
`iperf3` on the vendor firmware — it has no shell. Never printed beside the
published ~94 Mbit/s, which is NAT forwarding.

### 3.6 `D6`, `D4` and `NET-109`

* **`D6`**: `P1-FREE` (§ 3.2). **`D4` rlxfw**: `P1-PS` — 推 `/bin/sh`, the kernel
  threads and `ps`, as seating A (`NET-115`); `P1-NMAP` — 推 **no TCP port open**
  (seating A: 0 open; the closed/filtered split, 58,989 / 6,546, is loss-driven,
  `NET-112`, and is not predicted).
* **`D4` vendor**: each daemon's console line in the boot captures (`boa: starting
  server pid=350, port 80`, `MiniIGD v1.09.1 (2018.01.10-06:58+0000).`); readiness
  per port as the first `tcp` `result=ok` in each `V*-HP`/`M*-HP`, now on **80, 52869
  and 52881**; `V1-NMAP` — 推 **80, 52869 and 52881 open** (seating A); the closed and
  filtered counts are not predicted.
  * 80: 推 the first ok at **J + 26.53 … 27.08 s** in a boot without the fast step
    (§ 3.7), J + 25.72 … 26.01 s in one with it (seating A: J + 25.2496 … 26.2748 raw,
    `notes/boot-time.md` § 7.5, over each boot's r under both rules, times g); within
    ±0.14 s of the `boa: starting server` line, either side; the first ICMP reply
    precedes it by **10.4–12.2 s** (seating A 10.42–11.75 s raw, `notes/boot-time.md`
    § 7.5; 10.62–12.11 s over each boot's r times g, from `s109/arith2/a1.out` N10; the reply's ARP phase is host time, so the truth lies between).
  * The probe now connects to three ports every 0.2 s each where seating A's connected
    to one: 15 attempts a second instead of 5. 推 negligible — a closed port costs the
    vendor's kernel one RST, an open one an accept and a close — but it is a difference
    between the two days, declared here.
  * 52869 and 52881: **first readiness readings**. 推 they open once `miniigd` runs.
* **`NET-109`**: `P1-N0` then `P1-AC0`, nothing typed between. 推 the healthy shape —
  CPU-port `Rcv 0 bytes` while `CRCAlignErr` equals port 3's egress count. The count
  itself (294 in seating A) is the frames that had passed, and is not predicted.

### 3.7 Segment timing — the reproduction, and card A's model beside it

**The reproduction (推).** Every board interval of seating B is seating A's corrected
value times g. Per group (firmware, variant, cold or warm, segment), **seating B's
median is predicted inside [A's corrected minimum × 0.99580, A's corrected maximum ×
1.00581]** — A's own spread, widened by g's band. The table is seating A's raw and
corrected values from `Z9-D2.tsv`, computed three times — this card's own script
(`$FWRE_WORK/rebuild/s109/segtable.md`, from the files named in its header), the second
source (`s109/arith2`, sharing no code with it) and the 108th segment's digest — which
agree on every window-rule value. **Band = [the smaller of A's corrected minima under
the two rules × 0.99580 − 2 ms, the larger maximum × 1.00581 + 2 ms]**: g's band, and
one `FW-35` read quantum (~1 ms) at each end of an interval (推), which dominates the
short segments:

| firmware | variant | class | segment | n | A raw median (min..max) | A corrected, window rule | A corrected, local rate | **seating B's median in** |
|---|---|---|---|---:|---|---|---|---|
| loader | - | cold | `loader.booting` | 12 | 0.347938 (0.343924..0.355722) | 0.355962 (0.352634..0.357511) | = window (r_best) | **[0.3492, 0.3616]** |
| loader | - | cold | `loader.banner` | 12 | 0.572655 (0.566361..0.586139) | 0.586127 (0.580704..0.588275) | = window (r_best) | **[0.5763, 0.5937]** |
| loader | - | cold | `loader.esc` | 1 | 5.121936 | 5.237582 | = window (r_best) | **[5.2136, 5.2700]** |
| loader | - | warm | `loader.booting` | 13 | 0.347425 (0.341474..0.352177) | 0.355963 (0.355162..0.357101) | = window (r_best) | **[0.3517, 0.3612]** |
| loader | - | warm | `loader.banner` | 13 | 0.582232 (0.572747..0.589023) | 0.596025 (0.595705..0.597277) | = window (r_best) | **[0.5912, 0.6027]** |
| loader | - | warm | `loader.esc` | 1 | 5.102142 | 5.237048 | = window (r_best) | **[5.2131, 5.2695]** |
| rlxfw | loud | cold | `rtkload.decompress` | 1 | 1.231281 | 1.248637 | 1.247587 | **[1.2404, 1.2579]** |
| rlxfw | loud | cold | `rtkload.total` | 1 | 1.246918 | 1.264494 | 1.263431 | **[1.2561, 1.2738]** |
| rlxfw | loud | cold | `kernel.early` | 1 | 1.505786 | 1.527011 | 1.525727 | **[1.5173, 1.5379]** |
| rlxfw | loud | cold | `kernel.wlan` | 1 | 5.140987 | 5.213454 | 5.209070 | **[5.1852, 5.2457]** |
| rlxfw | loud | cold | `kernel.nic` | 1 | 1.224543 | 1.241804 | 1.240760 | **[1.2336, 1.2510]** |
| rlxfw | loud | cold | `kernel.late` | 1 | 3.140063 | 3.184325 | 3.181647 | **[3.1663, 3.2048]** |
| rlxfw | loud | cold | `kernel.total` | 1 | 11.011379 | 11.166595 | 11.157204 | **[11.1084, 11.2335]** |
| rlxfw | loud | cold | `rlxfw.setup` | 1 | 0.275227 | 0.279107 | 0.278872 | **[0.2757, 0.2827]** |
| rlxfw | loud | cold | `rlxfw.initpost` | 1 | 0.012049 | 0.012219 | 0.012209 | **[0.0102, 0.0143]** |
| rlxfw | loud | cold | `user.ready` | 1 | 0.116240 | 0.117879 | 0.117779 | **[0.1153, 0.1206]** |
| rlxfw | loud | cold | `boot.jump_to_ready` | 1 | 12.374537 | 12.548968 | 12.538414 | **[12.4838, 12.6239]** |
| rlxfw | loud | warm | `rtkload.decompress` | 2 | 1.229918 (1.229789..1.230047) | 1.247255 (1.247124..1.247386) | 1.247381 (1.247238..1.247525) | **[1.2399, 1.2568]** |
| rlxfw | loud | warm | `rtkload.total` | 2 | 1.242260 (1.242191..1.242329) | 1.259771 (1.259701..1.259841) | 1.259899 (1.259841..1.259956) | **[1.2524, 1.2693]** |
| rlxfw | loud | warm | `kernel.early` | 2 | 1.503931 (1.503630..1.504232) | 1.525130 (1.524825..1.525436) | 1.525285 (1.524995..1.525575) | **[1.5164, 1.5364]** |
| rlxfw | loud | warm | `kernel.wlan` | 2 | 5.135207 (5.134660..5.135754) | 5.207593 (5.207038..5.208147) | 5.208121 (5.207619..5.208623) | **[5.1832, 5.2409]** |
| rlxfw | loud | warm | `kernel.nic` | 2 | 1.223883 (1.223827..1.223940) | 1.241135 (1.241078..1.241193) | 1.241261 (1.241191..1.241331) | **[1.2339, 1.2505]** |
| rlxfw | loud | warm | `kernel.late` | 2 | 3.138953 (3.138946..3.138961) | 3.183200 (3.183192..3.183208) | 3.183523 (3.183498..3.183548) | **[3.1678, 3.2040]** |
| rlxfw | loud | warm | `kernel.total` | 2 | 11.001975 (11.001176..11.002774) | 11.157058 (11.156248..11.157868) | 11.158190 (11.157492..11.158887) | **[11.1074, 11.2257]** |
| rlxfw | loud | warm | `rlxfw.setup` | 2 | 0.274638 (0.274089..0.275187) | 0.278509 (0.277953..0.279066) | 0.278538 (0.277984..0.279091) | **[0.2748, 0.2827]** |
| rlxfw | loud | warm | `rlxfw.initpost` | 2 | 0.011735 (0.011437..0.012033) | 0.011900 (0.011598..0.012203) | 0.011902 (0.011599..0.012204) | **[0.0095, 0.0143]** |
| rlxfw | loud | warm | `user.ready` | 2 | 0.116382 (0.116062..0.116702) | 0.118023 (0.117698..0.118347) | 0.118034 (0.117711..0.118358) | **[0.1152, 0.1210]** |
| rlxfw | loud | warm | `boot.jump_to_ready` | 2 | 12.360617 (12.359429..12.361805) | 12.534851 (12.533647..12.536056) | 12.536123 (12.535045..12.537200) | **[12.4790, 12.6120]** |
| rlxfw | quiet | cold | `rtkload.decompress` | 2 | 1.188529 (1.187909..1.189148) | 1.219194 (1.217516..1.220873) | 1.217967 (1.217703..1.218231) | **[1.2104, 1.2300]** |
| rlxfw | quiet | cold | `rtkload.total` | 2 | 1.201842 (1.201280..1.202405) | 1.232852 (1.231089..1.234615) | 1.231611 (1.231278..1.231943) | **[1.2239, 1.2438]** |
| rlxfw | quiet | cold | `kernel.early` | 2 | 0.802541 (0.802121..0.802961) | 0.823248 (0.822116..0.824379) | 0.822419 (0.822243..0.822595) | **[0.8167, 0.8312]** |
| rlxfw | quiet | cold | `kernel.wlan` | 2 | 4.485276 (4.482159..4.488393) | 4.601001 (4.595467..4.606535) | 4.596370 (4.596173..4.596568) | **[4.5742, 4.6353]** |
| rlxfw | quiet | cold | `kernel.nic` | 2 | 0.839959 (0.839362..0.840555) | 0.861630 (0.860607..0.862654) | 0.860763 (0.860739..0.860787) | **[0.8550, 0.8697]** |
| rlxfw | quiet | cold | `kernel.late` | 2 | 3.089722 (3.087148..3.092295) | 3.169439 (3.166064..3.172814) | 3.166250 (3.165948..3.166551) | **[3.1507, 3.1932]** |
| rlxfw | quiet | cold | `kernel.total` | 2 | 9.217497 (9.210790..9.224204) | 9.455319 (9.444255..9.466382) | 9.445802 (9.445706..9.445898) | **[9.4026, 9.5234]** |
| rlxfw | quiet | cold | `rlxfw.setup` | 2 | 0.045743 (0.045650..0.045835) | 0.046923 (0.046917..0.046928) | 0.046875 (0.046815..0.046936) | **[0.0446, 0.0492]** |
| rlxfw | quiet | cold | `rlxfw.initpost` | 2 | 0.011523 (0.011458..0.011588) | 0.011820 (0.011776..0.011864) | 0.011808 (0.011750..0.011866) | **[0.0097, 0.0139]** |
| rlxfw | quiet | cold | `user.ready` | 2 | 0.113378 (0.112829..0.113928) | 0.116303 (0.115960..0.116646) | 0.116186 (0.115709..0.116664) | **[0.1132, 0.1193]** |
| rlxfw | quiet | cold | `boot.jump_to_ready` | 2 | 10.532718 (10.524899..10.540537) | 10.804474 (10.791990..10.816957) | 10.793599 (10.793550..10.793648) | **[10.7447, 10.8818]** |
| rlxfw | quiet | warm | `rtkload.decompress` | 6 | 1.201162 (1.187955..1.201430) | 1.218125 (1.218064..1.220920) | 1.218233 (1.218052..1.218550) | **[1.2109, 1.2300]** |
| rlxfw | quiet | warm | `rtkload.total` | 6 | 1.214380 (1.202401..1.215932) | 1.232980 (1.230907..1.235767) | 1.232971 (1.231056..1.234031) | **[1.2237, 1.2449]** |
| rlxfw | quiet | warm | `kernel.early` | 6 | 0.809943 (0.801947..0.811875) | 0.821945 (0.820951..0.824331) | 0.821982 (0.820935..0.823419) | **[0.8155, 0.8311]** |
| rlxfw | quiet | warm | `kernel.wlan` | 6 | 4.533120 (4.482950..4.534946) | 4.597239 (4.596321..4.607348) | 4.597559 (4.597002..4.598777) | **[4.5750, 4.6361]** |
| rlxfw | quiet | warm | `kernel.nic` | 6 | 0.847733 (0.839103..0.848698) | 0.860023 (0.859121..0.862752) | 0.860032 (0.859464..0.860815) | **[0.8535, 0.8698]** |
| rlxfw | quiet | warm | `kernel.late` | 6 | 3.121415 (3.087729..3.122019) | 3.165674 (3.163996..3.173411) | 3.165761 (3.165260..3.166303) | **[3.1487, 3.1938]** |
| rlxfw | quiet | warm | `kernel.total` | 6 | 9.313759 (9.212211..9.314436) | 9.445436 (9.440516..9.467843) | 9.445579 (9.444287..9.446881) | **[9.3989, 9.5248]** |
| rlxfw | quiet | warm | `rlxfw.setup` | 6 | 0.046263 (0.046074..0.046625) | 0.047136 (0.046853..0.047353) | 0.047148 (0.046855..0.047281) | **[0.0447, 0.0496]** |
| rlxfw | quiet | warm | `rlxfw.initpost` | 6 | 0.011720 (0.011626..0.012498) | 0.011939 (0.011790..0.012678) | 0.011941 (0.011790..0.012676) | **[0.0097, 0.0148]** |
| rlxfw | quiet | warm | `user.ready` | 6 | 0.114286 (0.112057..0.115006) | 0.115914 (0.115166..0.116627) | 0.115944 (0.114908..0.116633) | **[0.1124, 0.1193]** |
| rlxfw | quiet | warm | `boot.jump_to_ready` | 6 | 10.642682 (10.526669..10.644789) | 10.793760 (10.789916..10.818776) | 10.794353 (10.793234..10.795272) | **[10.7426, 10.8836]** |
| vendor | - | cold | `rtkload.decompress` | 4 | 1.037063 (1.036748..1.038023) | 1.060934 (1.059853..1.063112) | 1.060184 (1.056727..1.060397) | **[1.0503, 1.0713]** |
| vendor | - | cold | `rtkload.total` | 4 | 1.051220 (1.048721..1.054713) | 1.075694 (1.072093..1.079653) | 1.073138 (1.071216..1.078196) | **[1.0647, 1.0879]** |
| vendor | - | cold | `kernel.early` | 4 | 0.651945 (0.651499..0.652501) | 0.666951 (0.666018..0.668272) | 0.666299 (0.664258..0.666722) | **[0.6595, 0.6742]** |
| vendor | - | cold | `kernel.wlan` | 4 | 4.524712 (4.522136..4.529564) | 4.630051 (4.622916..4.636671) | 4.624258 (4.608735..4.630414) | **[4.5874, 4.6656]** |
| vendor | - | cold | `kernel.nic` | 4 | 0.824428 (0.815464..0.832872) | 0.843410 (0.833637..0.853003) | 0.841499 (0.834047..0.850517) | **[0.8281, 0.8600]** |
| vendor | - | cold | `kernel.late` | 4 | 0.962161 (0.951521..0.975365) | 0.984264 (0.972826..0.998940) | 0.983833 (0.972786..0.992940) | **[0.9667, 1.0067]** |
| vendor | - | cold | `kernel.total` | 4 | 6.963590 (6.942336..6.987898) | 7.123691 (7.097456..7.156798) | 7.107376 (7.097487..7.139956) | **[7.0657, 7.2004]** |
| vendor | - | cold | `user.ready` | 4 | 18.177337 (18.094300..18.317105) | 18.611937 (18.497547..18.727231) | 18.543377 (18.506628..18.726466) | **[18.4179, 18.8380]** |
| vendor | - | cold | `boot.jump_to_ready` | 4 | 26.216994 (26.085752..26.309627) | 26.843809 (26.667095..26.898709) | 26.744967 (26.680187..26.897609) | **[26.5532, 27.0570]** |
| vendor | - | warm | `rtkload.decompress` | 5 | 1.033709 (1.026900..1.034137) | 1.059804 (1.051828..1.060432) | 1.059760 (1.050559..1.062615) | **[1.0441, 1.0708]** |
| vendor | - | warm | `rtkload.total` | 5 | 1.044943 (1.039828..1.049544) | 1.071956 (1.065070..1.077893) | 1.069595 (1.063784..1.077848) | **[1.0573, 1.0862]** |
| vendor | - | warm | `kernel.early` | 5 | 0.650366 (0.646594..0.650658) | 0.666921 (0.662290..0.667478) | 0.667017 (0.661491..0.668276) | **[0.6567, 0.6742]** |
| vendor | - | warm | `kernel.wlan` | 5 | 4.502612 (4.480443..4.510554) | 4.622880 (4.589207..4.627158) | 4.611778 (4.583667..4.624039) | **[4.5624, 4.6560]** |
| vendor | - | warm | `kernel.nic` | 5 | 0.813533 (0.810057..0.814798) | 0.833880 (0.830572..0.834952) | 0.833570 (0.831837..0.833999) | **[0.8251, 0.8418]** |
| vendor | - | warm | `kernel.late` | 5 | 0.948988 (0.945917..0.951517) | 0.973590 (0.969873..0.974659) | 0.972862 (0.971024..0.973550) | **[0.9638, 0.9823]** |
| vendor | - | warm | `kernel.total` | 5 | 6.912024 (6.893352..6.925221) | 7.096403 (7.060690..7.104248) | 7.084383 (7.052167..7.098429) | **[7.0206, 7.1475]** |
| vendor | - | warm | `user.ready` | 5 | 18.249218 (17.406208..18.267388) | 18.705636 (17.828749..18.739627) | 18.669720 (17.807227..18.753057) | **[17.7305, 18.8640]** |
| vendor | - | warm | `boot.jump_to_ready` | 5 | 26.191747 (25.339388..26.237552) | 26.855067 (25.954510..26.915831) | 26.815424 (25.923178..26.913016) | **[25.8124, 27.0742]** |

The loader rows are every catch over its own `r_best`, cold (n = 12) and warm (n = 13)
pooled across both firmwares, since the loader is one code; for `loader.booting`'s
warm median the sharper test, written before this seating (`notes/boot-time.md`
§ 7.7), is inference (iii) (§ 3.9), and the table's band is `D3`'s. The local-rate
column is the second source's side analysis — each kernel boot divided by the WSL
kernel's printk clock over its own span, a rate that reproduces `f5-best.tsv`'s
`r_K5` at the 12 warm catches where both exist, within 0.00025 — and it moves the
rlxfw medians by at most 0.1 %, the vendor's pooled `J` → `boa` median by 0.35 %.

A positive control the correction could have failed (量, the 108th digest,
reproduced by the second source): divided by the `r_best` of the loader catch in its
own round, the eight quiet `J` → prompt values collapse from a 1.14 % spread to
0.066 % (10.7878–10.7949 s), across three presses and host rates of 0.975–0.986.

**Card A's model, with f_B** (推; its constants, § 3.7 of card A; T = f_B × (k × 0.353718
+ Δ)):

| image | quantity | at f = 1 | point (f_B 1.006347) | band over f_B | seating A, corrected (window rule) |
|---|---|---:|---:|---|---|
| `p2q` | `J` → prompt | 10.722171 | 10.790223 | [10.744928, 10.852917] | 10.7899–10.8188 |
| `p2l` | `J` → prompt | 12.482201 | 12.561424 | [12.508694, 12.634409] | 12.5336–12.5490 |
| `p2q` | `kernel.total` | 9.385111 | 9.444677 | [9.405030, 9.499553] | 9.4405–9.4678 |
| `p2q` | `user.ready` (Δ 62.7 … 80.6 ms) | 0.107764 … 0.125664 | — | [0.107992, 0.127196] | 0.1152–0.1166 |

`user.ready`'s band carries Δ's low–high range: at Δ's mid value alone ([0.112302,
0.113430]) seating A's corrected values sit 1.8–3.2 ms above it.

**The vendor.** Its `kernel.total` follows the reproduction rule (seating A's warm
raw range held 5/5 in card A). Its userspace does not follow a factor (`CLK-33`),
and seating A found why its `J` → `boa` spread: one boot of nine (`V4`) ran `WiFi
Simple Config` → `Register to wlan0` in 0.147 s against 1.114–1.131 s in the other
eight (`CLK-37`). So: **a boot whose step takes ≥ 1 s is predicted at J → `boa` in
[26.553, 27.074] s** (the table's rule over seating A's eight such boots), and **a boot
whose step takes < 0.2 s about 1 s earlier** (seating A's one: 25.92–25.95 s corrected); `Init bridge interface...` minus `sysconf wlanapp kill wlan0`
**0.848–0.883 s** in every complete boot (seating A 0.8332–0.8557 raw over r
0.9748–0.9782, times g). `M1`/`M2`'s `loader.esc` **≈ 5.237 s** (seating A 5.121936 / 0.97792
and 5.102142 / 0.97424; card A's cold/warm split was the host clock); `J BFC00000` →
`<RealTek>` **≈ 2.30 s** (`V4`–`V7-WZ`, raw 2.21–2.25 s over their `r_best`).

### 3.8 The host clock and the board's tick

* **The guard, before power** (`Z0-HCG`, § 6): `timesyncd` inactive; then, 100 s
  later, a 60 s `hostclock` run whose report reads the tick check `AGREE … vacuous`
  (every 1 s pair: the kernel's own rate within 100 ppm of RAW, and MONOTONIC agreeing
  with it) and **0** steps. 推 it permits (E2's B phase). **If it refuses, there is no
  power**: after 10 minutes the same line runs once more as the declared off-card
  cell `Z0-HCG2` (a `CORRECTIONS` entry first); after a second refusal there is still
  no power, and the owner decides the day.
* **The log, for the whole seating** (`Z0-HC`, `--no-sntp --no-windows`): 推 **from 100 s
  after `Z0-TSD` on, no `step` row and every `linux` row `tick=10000`**, until `Z9-HCX`
  stops it (before that it records the host as it was: 量 at 11:03 today, a step and a
  moving tick). The
  containment does not depend on that: **a window in which the log shows a step, a
  tick other than 10,000, or `freq` beyond ±100 ppm (the row's `freq` over 65,536) is
  named, and every host-timer
  interval inside it (ARP retransmits, `ping -i`, the `D8` host parts, the trials'
  host sides) is published as affected**. The Windows instrument is off because
  its `powershell.exe` every 60 s has an unmeasured effect on the CP2102 path the
  boot captures ride; SNTP is off so that nothing in the seating waits on a DNS
  answer. RAW's rate against true time is then carried by the board's tick (next
  bullet) and § 7.9's 1.000016 per QPC second.
* **Ticks per RAW second (推, `CLK-35`)**: each rlxfw press's last boot is bracketed by
  `TK0` and `TK1` (`/proc/stat`'s `cpu` ticks and IRQ 13, each line placed at its
  `FW-35` arrival). 99.998 board ticks per NTP second (§ 7.2), and RAW running at
  0.99998–1.000005 RAW seconds per NTP second (1.000016–1.000041 per QPC second, Windows
  −36.42 ppm against NTP), give **99.998–100.000 ticks per RAW second**: within ±0.001 over `P1`'s
  ~35 minutes (two ticks of quantisation in ~210,000), and only within ±0.1 over `P2`'s
  and `P3`'s ~30 s (the map, the probe's stop and the ICMP series: one or two ticks in
  ~3,000 is ±0.03–0.07 per second), which catches a gross error and nothing finer.
  ⚠️ Seating A lost 105 ticks between
  `P1-N0` and `P1-TR1-S0` (`CLK-35`, the cell not identified); a shortfall here is a
  reading of that, and each trial's `-S0`/`-S1` `/proc/stat` places it.
* **One WSL boot.** `hostprobe`'s join refuses clocks from two `boot_id`s. The
  `wsl -- sleep 36000` keeper starts before the attach; the first and last captures'
  metas are compared for `boot_id` at the desk (never `cat` into a bench log). A
  change splits the seating's RAW timeline in two, and no interval is computed across
  the split.

### 3.9 The three inferences `notes/boot-time.md` § 7.7 hands this seating

* **(i)** 推 the vendor answers ARP 0.075–0.116 s before its `Start NTP daemon` line
  reaches the host (+0.924–0.997 s after `Init bridge interface...`). **Refuted by a
  `V`/`M` boot whose bracket (§ 3.4) excludes that offset.**
* **(ii)** 推 `boa` listens 0.111–0.127 s before its `boa: server version` line's first
  byte reaches the host, and the probe's 0.2 s connect phase sets the sign of "ok −
  line". **Refuted by a `V`/`M` boot whose last-refused → first-ok window on port 80
  excludes that offset.** The window is 0.2 s wide, as in seating A: a finer
  `--tcp-interval` would sharpen the test and change the `D4` readiness quantity
  `D3` reproduces, so it is not changed.
* **(iii)** 推 `CLK-32`'s per-seating factor is the host clock: **seating B's warm
  `loader.booting` median (n = 13) lies in [0.354469, 0.358031] s**, and its cold median
  (n = 12) too. **Refuted by either outside it.**

### 3.10 `D3` — what is compared, how, and what is not a stable quantity

Every number seating A published is measured again here. Per number, three columns:
**(a)** seating B RAW against seating A **raw** — the plan's "raw figure", which
carries the host clock's +1.41 % (`P1`), +2.30 % (`V1`–`V3`, `M1`), +2.39 % (`P2`),
+2.53 % (`V4`–`V7`, `M2`) or +2.77 % (`P3`) by construction; **(b)** against seating A
**corrected**; **(c)** each divided by its own seating's warm `loader.booting` ratio
(the pre-registered normalisation, `notes/boot-time.md` § 5). **`D3` holds for a number
only when (a) and (b) are both within ±10 %**; a number inside on one and outside on
the other is a miss, published with both. The ±10 % is not widened. Cold and warm go
in separate tables, each cell with n, median and range.

**Scored and published, and marked before power as not stable quantities**, because
seating A's own spread for them already reaches or passes ±10 %, or because they are
counts of losses: a single ICMP series (±14 % in seating A); the first ICMP reply
after `J` (the host's ARP phase, a ~1 s quantum on a 10–16 s interval); `NMAP`'s closed
and filtered counts; `recover`'s counters; `rlx0`'s TCP board-sends (23.6 / 0.21 / 0.78);
every trial whose exchange failed; and `M1`, `M2` (n = 1). **Network up** is compared
through what the board decides — rlxfw's `N-NDOPEN` and the vendor's ARP onset, each
from `J` — and through the bracket's k and width, never through the first reply alone.

---

## § 4 Standing rules

🔴 **No flash write.** No `FLW`, `EW`, `EB`, no `AUTOBURN` with a non-zero value, no
`FLR`; every upload is `looprun`'s, which refuses `--skip S5b` and requires
`00000000` read back out of `0x8040D4A0` before it uploads. `cardcheck` refuses the
four verbs on this card (`FW-113`); it carries no `owner-yes` fence and needs none.
🔴 **A map before and after every block that can boot the vendor, a `looprun`
block included; any difference in a bracket stops every later vendor boot until the
owner has read it.** The runner enforces it (§ 6).
🔴 **The host's entry for 10.1.1.1 is flushed before every `looprun` block** (`P1-FL`,
`P2-FL`, `P3-FL`): after a vendor boot it holds the unit's own MAC, and `looprun`'s
`S5c` prints the entry. For the same reason **`tcpdump` runs only on `P1` and `P3`**,
never with `-e`, and **through a filter that passes a frame only if it cannot print an
address off the allowlist**. Without `-e`, `tcpdump` prints an ARP request's target
hardware address only when it is not zero, and a reply's **sender** hardware address
(the ARP payload's, not the Ethernet source): so the filter passes ICMP, ARP requests
whose target is zero, and ARP replies whose sender field is `rlx0`'s `02:52:4c:58:46:57`
or the loader's `56:0a:01:01:01:e8` — nothing else. A catch that misses and lets the
vendor boot while it runs therefore prints no address of the unit's. 量 2026-09-24 on
twelve synthetic frames through this host's `tcpdump -r`
(`$FWRE_WORK/rebuild/s109/tcpdfilter/result.txt`): unfiltered, a non-allowlisted address
prints; a first filter on the Ethernet source still printed it through two replies whose
sender field was forged; this one passes exactly the six frames it should and prints it
nowhere. Seating A's 33 host requests in `P3-TCPD` all had a zero target, and so did
rlxfw's one, so every frame `D8` reads passes. `P1-TCPD` ends by its `timeout 300` minutes before `P1-DOWN` brings `eth4` up.
🔴 **No cell touches the reset button while the vendor firmware runs** (`FW-40`, `FW-62`).
🔴 **`ifconfig rlx0 down` once, in `P1-DOWN`, as the handover; `rlx0` is not re-opened
in that boot** (`NET-58`).
🔴 **Every `--send` is at most 127 characters and carries no `$`.** Board `ping` ignores
`-c` (`NET-26`); every ping here is host-side.
🔴 **The seating sits between two Windows clock syncs**, on the owner's date. 推 from the
32,768 s cadence (§ 0 ④), this date's are 2026-09-24 16:32:46 and 2026-09-25 01:38:54:
so `Z0-TSD` runs no sooner than 16:42:46, and the midnight rule, not the next sync,
ends the window. Before `Z0`, `w32tm /query /status` must read *Last Successful Sync
Time* 16:32:46 (or a later sync at least 10 minutes old); any other reading is a
`CORRECTIONS` entry before power.
🔴 **`timesyncd` is stopped only for the seating.** `Z9-TSD` starts it again, and it is
run whenever the seating ends — after `P3`, or after a stop anywhere earlier.
🔴 **`hostclock` never runs under `sudo`** (it refuses `CAP_SYS_TIME`), and every `--out`
is a relative `bench/2026-09-24/…` path.
⚠️ **`J 80500000` and `J BFC00000` without `--esc-after`, in eight cells, is the
declared exception** (`V1`–`V7-BOOT`, `M2-BOOT`; card A § 4 said nine and fenced
eight). In them the vendor booting is the measurement; the rule's purpose — no boot
the card did not plan — is kept by the maps around the blocks.
⚠️ **A catch followed by a `J` gets `DW 8040D4A0 1` in between** (`*-AB`), which
absorbs a swallowed first command and reads the burn flag; **and every vendor
`J 80500000` follows a read-back of the staged head** (`V*-HD`, `CLAUDE.md`), so a
deviating `V*-BOOT` can be told from a staging that did not happen.
⚠️ **The seating ends before midnight**, or it stops at a press boundary and the rest
is a new card.
⚠️ **Off-card cells are declared in `bench/2026-09-24/CORRECTIONS-block43.md` before they
run** (card A declared its restarts afterwards, `CORRECTIONS` § 6). The one conditional
cell written now is `Z0-HCG2` (§ 3.8). Nothing is added to or removed from the fence
at the bench.
🟢 **Every background cell's own start signal is awaited before the next cell** —
`hostprobe`'s `start` event, `hostclock.py wait`, `tcpdump`'s `listening on`
(`FW-116`, `FW-132`); the runner refuses any other background program.

---

## § 5 The cells

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400`
`LR` = `/usr/bin/python3 tools/looprun.py --mode bench --out-dir bench/2026-09-24 --skip S2,S3,S4 --recipe-override a2c56bc8 --dwell-seconds 2.5`
`QIMG` = `--image /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/kroot/rtkload/nfjrom --image-sha256 4972edbadd2655a815e80606a83b8e5e5987334dfd1c990fcc806291eaf182ae`
`LIMG` = `--image /home/key/fwre-work/rebuild/p2-2/rtk/p2l/rlxfw/kroot/rtkload/nfjrom --image-sha256 888c930aa31763d9ed217783d4c9faa82c9652574a18948e35b379d88e8c31fc`
`HP` = `/usr/bin/python3 tools/hostprobe.py run`
`HCL` = `/usr/bin/python3 tools/hostclock.py`
`FL <ip>` = `sudo -n ip neigh flush to <ip>/32 dev enxfc19286184c9 ; ip -4 neigh show <ip> dev enxfc19286184c9 | wc -l` — prints `0`; never `-s -s`, which would print each flushed entry's address
`ICMP <ip>` = `for s in 56 256 512 1024 1472; do ping -I enxfc19286184c9 -c 20 -s $s -i 0.05 -w 10 -q <ip>; done`
`IPERF` = `timeout 70 qemu-mips-static /home/key/fwre-work/iperf3-port/iperf3`
`MB <cap>` = `tr -d '\r' < <cap>.log | sed -n '/^[0-9A-F]\{6\} /,/^map_lines /p' | sha256sum ; FWRE_WORK=/home/key/fwre-work /usr/bin/python3 tools/flashmap.py compare <cap>.log ; true` — `; true` because `flashmap compare` exits 1 on the expected group-0 `DIFFER` (§ 0 ⑥); the verdict is § 6's three gates

A `HOST` cell runs its command on the workstation with its output to
`<prefix>.log`; a `HOST&` cell runs it in the background, and the runner waits for
its start signal before the next item (§ 4). `tools/cardrun.py` reads only the
plain fences below; § 6 names, per invocation, the order, the gates and which
cells' non-zero exits are readings.

### Before press 1 — the address, the clock log, the guard

```
CAP --out bench/2026-09-24/Z0-PRE --seconds 3
HOST bench/2026-09-24/Z0-PREC :: ls bench/2026-09-24/Z0-PRE.log bench/2026-09-24/Z0-PRE.timing bench/2026-09-24/Z0-PRE.meta.json && cat bench/2026-09-24/Z0-PRE.meta.json
HOST bench/2026-09-24/Z1-ADDR :: sudo -n ip link set enxfc19286184c9 up ; sudo -n ip addr replace 10.1.1.2/24 dev enxfc19286184c9 ; ip -4 addr show dev enxfc19286184c9
HOST bench/2026-09-24/Z1-EVICT :: cat /proc/sys/net/ipv4/conf/enxfc19286184c9/arp_evict_nocarrier
HOST& bench/2026-09-24/Z0-HC :: HCL run --out bench/2026-09-24/Z0-HC --seconds 18000 --no-sntp --no-windows
HOST bench/2026-09-24/Z0-HCW :: HCL wait bench/2026-09-24/Z0-HC --timeout 20
HOST bench/2026-09-24/Z0-TSD :: sudo -n systemctl stop systemd-timesyncd ; systemctl show -p ActiveState systemd-timesyncd
HOST bench/2026-09-24/Z0-HCG :: sleep 100 ; HCL run --out bench/2026-09-24/Z0-HCG --seconds 60 --no-sntp --no-windows ; HCL report bench/2026-09-24/Z0-HCG
```

* `Z0-PRE` — the pre-flight with the board off: three artefacts and ~3.08 s, never
  its exit code (a healthy 0-byte run exits 1, so it runs as `Z0-PRE?`). `Z0-PREC`
  gates it as that rule reads it: the three artefacts exist, 0 bytes, 3.0–3.2 s (seating A
  3.075479 s).
* `Z1-ADDR` — `inet 10.1.1.2/24`; the address does not survive a re-attach. It is card A's
  command unchanged. `Z1-EVICT?` — the adapter's `arp_evict_nocarrier` (§ 3.4): a reading,
  not a gate, so a missing file cannot stop the seating.
* `Z0-HC` — `hostclock` for the whole seating, started before `timesyncd` stops so
  its first rows are the host as it was (§ 3.8). Its cap, 18,000 s, is far past the
  seating; `Z9-HCX` stops it. `Z0-HCW` — `hostclock wait`: the logger has written every
  enabled record and is alive, or `timesyncd` is not touched.
* `Z0-TSD` — `ActiveState=inactive`. `Z0-HCG` — the guard (§ 3.8): `AGREE … vacuous`
  and `timerfd 0`, or no power.

### Press 1 — `P1`, rlxfw: loud rounds, quiet rounds, a map, the measurements, both drivers

```
CAP --out bench/2026-09-24/P1-A --esc 180 --esc-period 0.002 --seconds 200
HOST bench/2026-09-24/P1-FL :: FL 10.1.1.1 ; FL 10.1.1.3
HOST& bench/2026-09-24/P1-TCPD :: timeout 300 sudo -n tcpdump -n -tt -i enxfc19286184c9 'icmp or (arp and arp[6:2] = 1 and arp[18:4] = 0 and arp[22:2] = 0) or (arp and arp[6:2] = 2 and ((arp[8:4] = 0x02524c58 and arp[12:2] = 0x4657) or (arp[8:4] = 0x560a0101 and arp[12:2] = 0x01e8)))'
HOST& bench/2026-09-24/P1-HP :: HP --out bench/2026-09-24/P1-HP --target 10.1.1.3 --seconds 900 --icmp --icmp-interval 0.05 --neigh
HOST bench/2026-09-24/P1L :: LR --cell P1L LIMG --iterations 3
CAP --out bench/2026-09-24/P1-RZ --send 'busybox reboot -f' --esc-after 25 --esc-period 0.002 --until '<RealTek>' --seconds 45
HOST bench/2026-09-24/P1Q :: LR --cell P1Q QIMG --iterations 4
CAP --out bench/2026-09-24/P1-TK0 --send 'cat /proc/stat ; cat /proc/interrupts' --idle 3 --seconds 20
CAP --out bench/2026-09-24/P1-M0 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines' --seconds 180
HOST bench/2026-09-24/P1-MB0 :: MB bench/2026-09-24/P1-M0
HOST bench/2026-09-24/P1-HPX :: pkill -INT -f 'P1-HP --target' ; sleep 2 ; tail -n 1 bench/2026-09-24/P1-HP.events
CAP --out bench/2026-09-24/P1-FREE --send 'busybox free ; cat /proc/meminfo' --idle 3 --seconds 30
CAP --out bench/2026-09-24/P1-PS --send 'ps' --idle 3 --seconds 30
CAP --out bench/2026-09-24/P1-N0 --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-24/P1-AC0 --send 'sleep 1 ; cat /proc/rtl865x/asicCounter' --until 'CpuEvent' --seconds 40
HOST& bench/2026-09-24/P1-OFF-HP :: HP --out bench/2026-09-24/P1-OFF-HP --target 10.1.1.3 --seconds 180 --udp-listen 50000
CAP --out bench/2026-09-24/P1-OFF01 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-24/P1-OFF02 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-24/P1-OFF03 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-24/P1-OFF04 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-24/P1-OFF05 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-24/P1-OFF06 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-24/P1-OFF07 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-24/P1-OFF08 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-24/P1-OFF09 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-24/P1-OFF10 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-24/P1-OFF11 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-24/P1-OFF12 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-24/P1-OFF13 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-24/P1-OFF14 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
CAP --out bench/2026-09-24/P1-OFF15 --send 'sleep 1 ; busybox traceroute -n -m 1 -q 1 -w 2 -p 49999 10.1.1.2' --until ' 1  \*' --seconds 10
HOST bench/2026-09-24/P1-ICMP :: ICMP 10.1.1.3
HOST bench/2026-09-24/P1-NMAP :: timeout 900 nmap -sT -p- -T4 -n --max-retries 1 10.1.1.3
```

* `P1-A` — opened **before** power; the owner presses inside its window. 推 as seating
  A: `Booting...`, one space (`C-8`: cold), the banner, `<RealTek>`, `prompt_seen`.
* `P1-FL` — `0` and `0`, before `looprun`, always (§ 4).
* `P1-TCPD` — frames across both `looprun` blocks (§ 3.4), through § 4's filter;
  `timeout 300` ends it.
* `P1L`, `P1Q` — `looprun`'s `A0`–`A4`, `S5b` and `S6b` gates round by round; **each
  round ends with `S9`, 2.5 RAW seconds past its prompt, the last included**
  (`FW-127`); bytes and marks (§ 3.2); timing (§ 3.7). 🔴 Refuted for the dwell: an
  rlxfw round with no ICMP reply before its next reset — 推 none of the seven.
* `P1-RZ` — the warm catch between the blocks (`Reboot Result from Watchdog
  Timeout!`, ends at `<RealTek>`).
* `P1-TK0` — the ticks at the start of the press's last boot's long bracket (§ 3.8).
* `P1-M0` / `P1-MB0` — the seating's first map: its own "before" is seating A's `P3-M0`,
  and it is the "before" of `V1`–`M1`. § 3.2's map, exactly. 🔴 **Any other body or
  group-0 digest stops every later vendor boot.**
* `P1-HPX` — `P1-HP` stopped with SIGINT, which it handles; its last line is `stop`.
* `P1-FREE`, `P1-PS`, `P1-N0` → `P1-AC0` — § 3.6. `P1-PS`'s gate is the control for every
  `-S0` gate: PID 1's row, `/bin/sh`, in the column shape they read. `P1-AC0` is a reading, not a gate: an
  incomplete dump does not stop the press.
* `P1-OFF-HP` + `P1-OFF01`…`P1-OFF15` — § 3.4's offset: each capture **139 B**, and 15
  `udp` events `len=10`; the negative control is card A's (` 1  *`, not an address).
* `P1-ICMP` — § 3.5 (a). `P1-NMAP` — § 3.6: no port open; capped by `timeout 900`
  (seating A's two scans took 36–39 s).

```
CAP --out bench/2026-09-24/P1-TR1-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/TR1.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat ; cat /proc/rtl819x-nic' --idle 4 --seconds 30
HOST bench/2026-09-24/P1-TR1 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m
CAP --out bench/2026-09-24/P1-TR1-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/TR1.log ; cat /proc/rtl819x-nic' --idle 3 --seconds 40
CAP --out bench/2026-09-24/P1-TR2-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/TR2.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat ; cat /proc/rtl819x-nic' --idle 4 --seconds 30
HOST bench/2026-09-24/P1-TR2 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m
CAP --out bench/2026-09-24/P1-TR2-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/TR2.log ; cat /proc/rtl819x-nic' --idle 3 --seconds 40
CAP --out bench/2026-09-24/P1-TR3-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/TR3.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat ; cat /proc/rtl819x-nic' --idle 4 --seconds 30
HOST bench/2026-09-24/P1-TR3 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m
CAP --out bench/2026-09-24/P1-TR3-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/TR3.log ; cat /proc/rtl819x-nic' --idle 3 --seconds 40
CAP --out bench/2026-09-24/P1-TS1-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/TS1.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat ; cat /proc/rtl819x-nic' --idle 4 --seconds 30
HOST bench/2026-09-24/P1-TS1 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m -R
CAP --out bench/2026-09-24/P1-TS1-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/TS1.log ; cat /proc/rtl819x-nic' --idle 3 --seconds 40
CAP --out bench/2026-09-24/P1-TS2-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/TS2.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat ; cat /proc/rtl819x-nic' --idle 4 --seconds 30
HOST bench/2026-09-24/P1-TS2 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m -R
CAP --out bench/2026-09-24/P1-TS2-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/TS2.log ; cat /proc/rtl819x-nic' --idle 3 --seconds 40
CAP --out bench/2026-09-24/P1-TS3-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/TS3.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat ; cat /proc/rtl819x-nic' --idle 4 --seconds 30
HOST bench/2026-09-24/P1-TS3 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m -R
CAP --out bench/2026-09-24/P1-TS3-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/TS3.log ; cat /proc/rtl819x-nic' --idle 3 --seconds 40
CAP --out bench/2026-09-24/P1-UR1-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/UR1.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat ; cat /proc/rtl819x-nic' --idle 4 --seconds 30
HOST bench/2026-09-24/P1-UR1 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M
CAP --out bench/2026-09-24/P1-UR1-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/UR1.log ; cat /proc/rtl819x-nic' --idle 3 --seconds 40
CAP --out bench/2026-09-24/P1-UR2-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/UR2.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat ; cat /proc/rtl819x-nic' --idle 4 --seconds 30
HOST bench/2026-09-24/P1-UR2 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M
CAP --out bench/2026-09-24/P1-UR2-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/UR2.log ; cat /proc/rtl819x-nic' --idle 3 --seconds 40
CAP --out bench/2026-09-24/P1-UR3-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/UR3.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat ; cat /proc/rtl819x-nic' --idle 4 --seconds 30
HOST bench/2026-09-24/P1-UR3 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M
CAP --out bench/2026-09-24/P1-UR3-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/UR3.log ; cat /proc/rtl819x-nic' --idle 3 --seconds 40
CAP --out bench/2026-09-24/P1-US1-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/US1.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat ; cat /proc/rtl819x-nic' --idle 4 --seconds 30
HOST bench/2026-09-24/P1-US1 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M -R
CAP --out bench/2026-09-24/P1-US1-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/US1.log ; cat /proc/rtl819x-nic' --idle 3 --seconds 40
CAP --out bench/2026-09-24/P1-US2-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/US2.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat ; cat /proc/rtl819x-nic' --idle 4 --seconds 30
HOST bench/2026-09-24/P1-US2 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M -R
CAP --out bench/2026-09-24/P1-US2-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/US2.log ; cat /proc/rtl819x-nic' --idle 3 --seconds 40
CAP --out bench/2026-09-24/P1-US3-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/US3.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat ; cat /proc/rtl819x-nic' --idle 4 --seconds 30
HOST bench/2026-09-24/P1-US3 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M -R
CAP --out bench/2026-09-24/P1-US3-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/US3.log ; cat /proc/rtl819x-nic' --idle 3 --seconds 40
```

* Each trial `T`: `-S0` starts the one-off server with its log, waits 2 s, lists the
  processes — its gate requires this trial's server among them (§ 3.5) — and reads the
  ticks and the driver's counters; the host client runs; `-S1` reads the ticks, stops any
  server still running, prints the log and the counters again. 推 a completed trial's
  log ends in a TEST_END summary; a stalled one's, in the SIGTERM shape `iperflog`
  names (`FW-128`). `busybox killall` prints `killall: iperf3: no process killed` when
  `-1` already ended the server, and nothing when it stopped a running one, whose log
  then ends `iperf3: interrupt - the server has terminated` (量 the qemu dry run, § 0 ①).
  The image has no `killall` link, so it is typed `busybox killall`.
* `/tmp/<T>.log` is per trial: the board has no tmpfs, so `/tmp` is the ramfs rootfs,
  ~3.3 kB a trial against 20,932 kB free (`MEM-19`).

```
CAP --out bench/2026-09-24/P1-DOWN --send 'ifconfig rlx0 down ; cat /proc/interrupts' --idle 3 --seconds 30
CAP --out bench/2026-09-24/P1-ETH4 --send 'ifconfig eth4 10.1.1.4 up ; ifconfig eth4 ; cat /proc/interrupts' --idle 3 --seconds 40
HOST bench/2026-09-24/P1-EPING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.4
CAP --out bench/2026-09-24/P1-ER1-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/ER1.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-24/P1-ER1 :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 5 -f m
CAP --out bench/2026-09-24/P1-ER1-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/ER1.log' --idle 3 --seconds 40
CAP --out bench/2026-09-24/P1-ER2-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/ER2.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-24/P1-ER2 :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 5 -f m
CAP --out bench/2026-09-24/P1-ER2-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/ER2.log' --idle 3 --seconds 40
CAP --out bench/2026-09-24/P1-ER3-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/ER3.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-24/P1-ER3 :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 5 -f m
CAP --out bench/2026-09-24/P1-ER3-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/ER3.log' --idle 3 --seconds 40
CAP --out bench/2026-09-24/P1-ES1-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/ES1.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-24/P1-ES1 :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 5 -f m -R
CAP --out bench/2026-09-24/P1-ES1-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/ES1.log' --idle 3 --seconds 40
CAP --out bench/2026-09-24/P1-ES2-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/ES2.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-24/P1-ES2 :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 5 -f m -R
CAP --out bench/2026-09-24/P1-ES2-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/ES2.log' --idle 3 --seconds 40
CAP --out bench/2026-09-24/P1-ES3-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/ES3.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-24/P1-ES3 :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 5 -f m -R
CAP --out bench/2026-09-24/P1-ES3-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/ES3.log' --idle 3 --seconds 40
CAP --out bench/2026-09-24/P1-EU1-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/EU1.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-24/P1-EU1 :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M
CAP --out bench/2026-09-24/P1-EU1-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/EU1.log' --idle 3 --seconds 40
CAP --out bench/2026-09-24/P1-EU2-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/EU2.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-24/P1-EU2 :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M
CAP --out bench/2026-09-24/P1-EU2-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/EU2.log' --idle 3 --seconds 40
CAP --out bench/2026-09-24/P1-EU3-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/EU3.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-24/P1-EU3 :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M
CAP --out bench/2026-09-24/P1-EU3-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/EU3.log' --idle 3 --seconds 40
CAP --out bench/2026-09-24/P1-EV1-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/EV1.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-24/P1-EV1 :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M -R
CAP --out bench/2026-09-24/P1-EV1-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/EV1.log' --idle 3 --seconds 40
CAP --out bench/2026-09-24/P1-EV2-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/EV2.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-24/P1-EV2 :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M -R
CAP --out bench/2026-09-24/P1-EV2-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/EV2.log' --idle 3 --seconds 40
CAP --out bench/2026-09-24/P1-EV3-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/EV3.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-24/P1-EV3 :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M -R
CAP --out bench/2026-09-24/P1-EV3-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/EV3.log' --idle 3 --seconds 40
CAP --out bench/2026-09-24/P1-TK1 --send 'cat /proc/stat ; cat /proc/interrupts' --idle 3 --seconds 20
```

* `P1-DOWN` — `RLXFW-N-ENGOFF`, `RLXFW-N-NDSTOP`, `/proc/interrupts` without line 12.
  **The one `ifconfig rlx0 down` of this seating.**
* `P1-ETH4` — § 3.2's four fields. `P1-EPING` — **4/4, or the vendor-driver trials
  are void and are not run** (`NET-54`); then only `P1-TK1` runs (§ 6).
* The `eth4` trials — § 3.5 (b); `ER1`–`ER3` and `EU1`–`EU3` are `iperflog`'s control.
* `P1-TK1` — the last board cell of the press; then the owner powers off. Nothing
  between `P1-M0` and here boots anything, so `P1-M0` is the bracket's "before" for
  `V1`–`M1`.

### Presses 2, 3, 4 — `V1`, `V2`, `V3`, vendor cold: caught, then `J 80500000`

```
CAP --out bench/2026-09-24/V1-A --esc 180 --esc-period 0.002 --seconds 200
CAP --out bench/2026-09-24/V1-AB --send 'DW 8040D4A0 1' --idle 2 --seconds 6
CAP --out bench/2026-09-24/V1-HD --send 'DW 80500000 8' --idle 2 --seconds 6
HOST bench/2026-09-24/V1-FL :: FL 10.1.1.1
HOST& bench/2026-09-24/V1-HP :: HP --out bench/2026-09-24/V1-HP --target 10.1.1.1 --seconds 60 --icmp --icmp-interval 0.05 --neigh --tcp 80 --tcp 52869 --tcp 52881
CAP --out bench/2026-09-24/V1-BOOT --send 'J 80500000' --until 'port 80' --seconds 90
HOST bench/2026-09-24/V1-ICMP :: ICMP 10.1.1.1
HOST bench/2026-09-24/V1-NMAP :: timeout 900 nmap -sT -p- -T4 -n --max-retries 1 10.1.1.1
CAP --out bench/2026-09-24/V2-A --esc 180 --esc-period 0.002 --seconds 200
CAP --out bench/2026-09-24/V2-AB --send 'DW 8040D4A0 1' --idle 2 --seconds 6
CAP --out bench/2026-09-24/V2-HD --send 'DW 80500000 8' --idle 2 --seconds 6
HOST bench/2026-09-24/V2-FL :: FL 10.1.1.1
HOST& bench/2026-09-24/V2-HP :: HP --out bench/2026-09-24/V2-HP --target 10.1.1.1 --seconds 60 --icmp --icmp-interval 0.05 --neigh --tcp 80 --tcp 52869 --tcp 52881
CAP --out bench/2026-09-24/V2-BOOT --send 'J 80500000' --until 'port 80' --seconds 90
HOST bench/2026-09-24/V2-ICMP :: ICMP 10.1.1.1
CAP --out bench/2026-09-24/V3-A --esc 180 --esc-period 0.002 --seconds 200
CAP --out bench/2026-09-24/V3-AB --send 'DW 8040D4A0 1' --idle 2 --seconds 6
CAP --out bench/2026-09-24/V3-HD --send 'DW 80500000 8' --idle 2 --seconds 6
HOST bench/2026-09-24/V3-FL :: FL 10.1.1.1
HOST& bench/2026-09-24/V3-HP :: HP --out bench/2026-09-24/V3-HP --target 10.1.1.1 --seconds 60 --icmp --icmp-interval 0.05 --neigh --tcp 80 --tcp 52869 --tcp 52881
CAP --out bench/2026-09-24/V3-BOOT --send 'J 80500000' --until 'port 80' --seconds 90
HOST bench/2026-09-24/V3-ICMP :: ICMP 10.1.1.1
```

* `V*-A` — as `P1-A`. `V*-AB` — **`00000001`**, a reading and not a gate: it exists to
  absorb a swallowed first command (card A § 4). `V*-HD` — **118 B**, § 3.2's two lines;
  its gate is the one that stops a `J`.
* `V*-FL` — `0`; no `IPCONFIG` is typed on these presses, so nothing but the vendor
  can answer 10.1.1.1 after it (`NET-95`).
* `V*-HP` — ICMP, the neighbour, and TCP on 80, 52869 and 52881 every 0.2 s each, for
  60 s (§ 3.4, § 3.6).
* `V*-BOOT` — **1,789 B, ending at the `boa` line**; 🔴 a stop before `boa` is a
  reading, not a failure (`X8-WAIT`): the capture runs to its cap, and `V*-HP`'s
  `tcp:80` says whether `boa` came up silently.
* `V*-ICMP` — after `V*-HP` has ended. `V1-NMAP` — § 3.6.

### Press 5 — `M1`, vendor cold, listen-only autoboot (the capture-mode control)

```
HOST bench/2026-09-24/M1-FL :: FL 10.1.1.1
HOST& bench/2026-09-24/M1-HP :: HP --out bench/2026-09-24/M1-HP --target 10.1.1.1 --seconds 300 --icmp --icmp-interval 0.05 --neigh --tcp 80 --tcp 52869 --tcp 52881
CAP --out bench/2026-09-24/M1-BOOT --until 'port 80' --seconds 300
```

* `M1-BOOT` — opened before power, **nothing sent**: the owner presses and the loader
  autoboots through its ESC window. 推 cold `C-8`, `loader.banner` within ±10 ms of
  the cold `esc` groups, `loader.esc` ≈ 5.237 s, `Jump to image start=0x80500000...`
  with no `P0phymode` or `Ethernet init` line (`LDR-46`), **1,901 B** to `boa`.

### Press 6 — `P2`, rlxfw: the bracket after `V1`–`M1`

```
CAP --out bench/2026-09-24/P2-A --esc 180 --esc-period 0.002 --seconds 200
HOST bench/2026-09-24/P2-FL :: FL 10.1.1.1 ; FL 10.1.1.3
HOST& bench/2026-09-24/P2-HP :: HP --out bench/2026-09-24/P2-HP --target 10.1.1.3 --seconds 300 --icmp --icmp-interval 0.05 --neigh
HOST bench/2026-09-24/P2Q :: LR --cell P2Q QIMG --iterations 2
CAP --out bench/2026-09-24/P2-TK0 --send 'cat /proc/stat ; cat /proc/interrupts' --idle 3 --seconds 20
CAP --out bench/2026-09-24/P2-M0 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines' --seconds 180
HOST bench/2026-09-24/P2-MB0 :: MB bench/2026-09-24/P2-M0
HOST bench/2026-09-24/P2-HPX :: pkill -INT -f 'P2-HP --target' ; sleep 2 ; tail -n 1 bench/2026-09-24/P2-HP.events
HOST bench/2026-09-24/P2-ICMP :: ICMP 10.1.1.3
CAP --out bench/2026-09-24/P2-TK1 --send 'cat /proc/stat ; cat /proc/interrupts' --idle 3 --seconds 20
```

* `P2-FL` — after four vendor boots the host holds the unit's address for 10.1.1.1,
  and `P2Q`'s `S5c` would print it; this is the flush that keeps it out.
* `P2-M0` — **identical to `P1-M0`**; any other reading stops `V4`–`M2`.
* `P2-TK0` … `P2-TK1` — about 30 s of the press's last boot (§ 3.8).

### Presses 7, 8, 9, 10 — `V4`–`V7`, vendor warm: caught, a warm reset caught, then `J 80500000`

```
CAP --out bench/2026-09-24/V4-A --esc 180 --esc-period 0.002 --seconds 200
CAP --out bench/2026-09-24/V4-AB --send 'DW 8040D4A0 1' --idle 2 --seconds 6
CAP --out bench/2026-09-24/V4-WZ --send 'J BFC00000' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
CAP --out bench/2026-09-24/V4-AB2 --send 'DW 8040D4A0 1' --idle 2 --seconds 6
CAP --out bench/2026-09-24/V4-HD --send 'DW 80500000 8' --idle 2 --seconds 6
HOST bench/2026-09-24/V4-FL :: FL 10.1.1.1
HOST& bench/2026-09-24/V4-HP :: HP --out bench/2026-09-24/V4-HP --target 10.1.1.1 --seconds 60 --icmp --icmp-interval 0.05 --neigh --tcp 80 --tcp 52869 --tcp 52881
CAP --out bench/2026-09-24/V4-BOOT --send 'J 80500000' --until 'port 80' --seconds 90
CAP --out bench/2026-09-24/V5-A --esc 180 --esc-period 0.002 --seconds 200
CAP --out bench/2026-09-24/V5-AB --send 'DW 8040D4A0 1' --idle 2 --seconds 6
CAP --out bench/2026-09-24/V5-WZ --send 'J BFC00000' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
CAP --out bench/2026-09-24/V5-AB2 --send 'DW 8040D4A0 1' --idle 2 --seconds 6
CAP --out bench/2026-09-24/V5-HD --send 'DW 80500000 8' --idle 2 --seconds 6
HOST bench/2026-09-24/V5-FL :: FL 10.1.1.1
HOST& bench/2026-09-24/V5-HP :: HP --out bench/2026-09-24/V5-HP --target 10.1.1.1 --seconds 60 --icmp --icmp-interval 0.05 --neigh --tcp 80 --tcp 52869 --tcp 52881
CAP --out bench/2026-09-24/V5-BOOT --send 'J 80500000' --until 'port 80' --seconds 90
CAP --out bench/2026-09-24/V6-A --esc 180 --esc-period 0.002 --seconds 200
CAP --out bench/2026-09-24/V6-AB --send 'DW 8040D4A0 1' --idle 2 --seconds 6
CAP --out bench/2026-09-24/V6-WZ --send 'J BFC00000' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
CAP --out bench/2026-09-24/V6-AB2 --send 'DW 8040D4A0 1' --idle 2 --seconds 6
CAP --out bench/2026-09-24/V6-HD --send 'DW 80500000 8' --idle 2 --seconds 6
HOST bench/2026-09-24/V6-FL :: FL 10.1.1.1
HOST& bench/2026-09-24/V6-HP :: HP --out bench/2026-09-24/V6-HP --target 10.1.1.1 --seconds 60 --icmp --icmp-interval 0.05 --neigh --tcp 80 --tcp 52869 --tcp 52881
CAP --out bench/2026-09-24/V6-BOOT --send 'J 80500000' --until 'port 80' --seconds 90
CAP --out bench/2026-09-24/V7-A --esc 180 --esc-period 0.002 --seconds 200
CAP --out bench/2026-09-24/V7-AB --send 'DW 8040D4A0 1' --idle 2 --seconds 6
CAP --out bench/2026-09-24/V7-WZ --send 'J BFC00000' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
CAP --out bench/2026-09-24/V7-AB2 --send 'DW 8040D4A0 1' --idle 2 --seconds 6
CAP --out bench/2026-09-24/V7-HD --send 'DW 80500000 8' --idle 2 --seconds 6
HOST bench/2026-09-24/V7-FL :: FL 10.1.1.1
HOST& bench/2026-09-24/V7-HP :: HP --out bench/2026-09-24/V7-HP --target 10.1.1.1 --seconds 60 --icmp --icmp-interval 0.05 --neigh --tcp 80 --tcp 52869 --tcp 52881
CAP --out bench/2026-09-24/V7-BOOT --send 'J 80500000' --until 'port 80' --seconds 90
```

* `V*-WZ` — **`Reboot Result from Watchdog Timeout!`**, `<RealTek>` ≈ 2.30 s after the
  send (§ 3.7); these four are `D2`'s vendor warm column. `V*-AB2` — `00000001`.
* `V*-HD`, `V*-BOOT` — as `V1`–`V3`.

### Press 11 — `M2`, vendor warm, listen-only autoboot (the capture-mode control)

```
CAP --out bench/2026-09-24/M2-A --esc 180 --esc-period 0.002 --seconds 200
CAP --out bench/2026-09-24/M2-AB --send 'DW 8040D4A0 1' --idle 2 --seconds 6
HOST bench/2026-09-24/M2-FL :: FL 10.1.1.1
HOST& bench/2026-09-24/M2-HP :: HP --out bench/2026-09-24/M2-HP --target 10.1.1.1 --seconds 90 --icmp --icmp-interval 0.05 --neigh --tcp 80 --tcp 52869 --tcp 52881
CAP --out bench/2026-09-24/M2-BOOT --send 'J BFC00000' --until 'port 80' --seconds 90
```

* `M2-BOOT` — **no ESC**: the loader's warm reset autoboots the vendor. 推 warm `C-8`,
  `loader.banner` within ±10 ms of the warm `esc_after` groups, `loader.esc` ≈ 5.237 s,
  **1,979 B** to `boa`.

### Press 12 — `P3`, rlxfw: the bracket after `V4`–`M2`, the second frame check, and `D2`

```
CAP --out bench/2026-09-24/P3-A --esc 180 --esc-period 0.002 --seconds 200
HOST bench/2026-09-24/P3-FL :: FL 10.1.1.1 ; FL 10.1.1.3
HOST& bench/2026-09-24/P3-TCPD :: timeout 240 sudo -n tcpdump -n -tt -i enxfc19286184c9 'icmp or (arp and arp[6:2] = 1 and arp[18:4] = 0 and arp[22:2] = 0) or (arp and arp[6:2] = 2 and ((arp[8:4] = 0x02524c58 and arp[12:2] = 0x4657) or (arp[8:4] = 0x560a0101 and arp[12:2] = 0x01e8)))'
HOST& bench/2026-09-24/P3-HP :: HP --out bench/2026-09-24/P3-HP --target 10.1.1.3 --seconds 300 --icmp --icmp-interval 0.05 --neigh
HOST bench/2026-09-24/P3Q :: LR --cell P3Q QIMG --iterations 2
CAP --out bench/2026-09-24/P3-TK0 --send 'cat /proc/stat ; cat /proc/interrupts' --idle 3 --seconds 20
CAP --out bench/2026-09-24/P3-M0 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines' --seconds 180
HOST bench/2026-09-24/P3-MB0 :: MB bench/2026-09-24/P3-M0
HOST bench/2026-09-24/P3-HPX :: pkill -INT -f 'P3-HP --target' ; sleep 2 ; tail -n 1 bench/2026-09-24/P3-HP.events
HOST bench/2026-09-24/P3-ICMP :: ICMP 10.1.1.3
CAP --out bench/2026-09-24/P3-TK1 --send 'cat /proc/stat ; cat /proc/interrupts' --idle 3 --seconds 20
HOST bench/2026-09-24/Z9-D2 :: /usr/bin/python3 tools/boot-timeline.py --retro bench/2026-09-24 --tsv bench/2026-09-24/Z9-D2.tsv
HOST bench/2026-09-24/Z9-D2A :: sha256sum /home/key/fwre-work/rebuild/s105-analysis/s105-d2.py ; /usr/bin/python3 /home/key/fwre-work/rebuild/s105-analysis/s105-d2.py bench/2026-09-23/Z9-D2.tsv
HOST bench/2026-09-24/Z9-D2X :: /usr/bin/python3 /home/key/fwre-work/rebuild/s105-analysis/s105-d2.py bench/2026-09-24/Z9-D2.tsv
```

* `P3-TCPD` — as `P1-TCPD`, through § 4's filter.
* `P3-M0` — identical to `P1-M0` and `P2-M0`.
* `Z9-D2` — the retro table with its FILE (`CORRECTIONS-block42.md` § 1); `boot-timeline`
  reads no frame capture, so it need not wait for `P3-TCPD`, which the invocation's own end
  waits for. `Z9-D2A` — the `D2` script's digest, and seating A's six
  differences reproduced by it (§ 3.1). `Z9-D2X` — **`D2`, before anything else is
  compared**: `D2: HOLDS`. Then the owner powers off.

### After power-off — the clock log closed, `timesyncd` back

```
HOST bench/2026-09-24/Z9-HCX :: HCL stop bench/2026-09-24/Z0-HC
HOST bench/2026-09-24/Z9-HCR :: HCL report bench/2026-09-24/Z0-HC
HOST bench/2026-09-24/Z9-TSD :: sudo -n systemctl start systemd-timesyncd ; systemctl show -p ActiveState systemd-timesyncd
```

* `Z9-HCX?` — `hostclock stop`, a reading, so that a logger that already died cannot
  keep `timesyncd` stopped; `Z9-HCR` — its report over the whole seating, read as a
  reading (§ 3.8); `Z9-TSD` — `ActiveState=active`.

---

## § 6 How the cells are run

**Before any cell** (none of it a cell): `w32tm /query /status` for the last sync
(§ 4); the keeper `wsl -d Ubuntu-24.04 -- sleep 36000`, started in the background before
any attach; `usbipd list`, read fresh, then `usbipd attach` of the CP2102 and of the GbE
adapter, reading what each prints. Then in WSL, from the repository root:
`mkdir -p /home/key/fwre-work/rebuild/s110` (the transcripts' directory; `cardrun`
refuses a missing one); `sha256sum` of `runblock.py` and of the `D2` script against
their `cardnum` rows; `/usr/bin/python3 tools/check-predictions.py` on this card, reading
**`0 of 246 captures came after the prediction, 246 did not`** (exit 1: nothing is
captured yet); and every invocation below once through `runblock.py … --dry`, each
ending `ALL ITEMS DONE`.

**Each invocation** runs from the repository root in WSL as
`/usr/bin/python3 /home/key/fwre-work/rebuild/s109/card/runblock.py CARD NAME --log LOG`,
with CARD this card, NAME the invocation's and LOG
`/home/key/fwre-work/rebuild/s110/run-NAME.log` (`--from CELL` only where a stop below
says so); it hands its fence's items to `tools/cardrun.py` unchanged, and the transcript
is outside the repository, on RAW (`FW-132`). `NAME?` marks a cell whose non-zero exit is a
reading, not a stop; `gate:` items are the card's decision points; any failed cell or
gate stops the invocation and interrupts its background cells. `I0` runs in the
background for the whole seating, as a background task of the session that runs the
seating (never `nohup … &` inside `wsl -- bash -lc`): the runner waits for its
background cells before it exits, so `I0` ends only when `Z9-HCX` stops the logger, and
`I1b`'s first cell, `Z0-HCW`, is what shows it started.

**The owner's power** (`CLAUDE.md`, *At the bench*): each press's invocation starts with
its catch; the owner is told when it opens and presses inside its 180 s window. `M1`:
the owner presses after `M1-BOOT` opens. After each press's last board cell, the owner
powers off, and the next invocation starts only after that.

One item per line; each line is one argument.

**`I1`** — before power, the pre-flight and the address

```run
Z0-PRE?
Z0-PREC
gate:grep=^  "bytes": 0,$:Z0-PREC
gate:grep=^  "duration_s": 3\.[01][0-9]*,$:Z0-PREC
Z1-ADDR
gate:grep=inet 10\.1\.1\.2/24:Z1-ADDR
Z1-EVICT?
```

**`I0`** — in the background for the whole seating; it ends when Z9-HCX stops the logger

```run
Z0-HC
```

**`I1b`** — the clock guard, before power

```run
Z0-HCW
Z0-TSD
gate:grep=^ActiveState=inactive$:Z0-TSD
Z0-HCG
gate:grep=^  tick check: AGREE over [0-9]+ pair\(s\), worst [-+][0-9.]+ ppm, vacuous:Z0-HCG
gate:grep=^  steps: timerfd 0, :Z0-HCG
```

**`I2`** — press 1, from the catch to the census

```run
P1-A
gate:caught:P1-A
P1-FL
gate:grep=\A(?:0\n)+\Z:P1-FL
P1-TCPD
P1-HP
P1L
P1-RZ
gate:prompt:P1-RZ
P1Q
P1-TK0
P1-M0
gate:until:P1-M0
P1-MB0
gate:grep=^0927be41e91fe4bd32986a48e47c9a3f0d34ce587c7b42324c088b602f45da46  -$:P1-MB0
gate:grep=^  DIFFER  000000  device c66a4126d7b1b862\.\.\. dump 8494cc8666b5c6f6\.\.\.$:P1-MB0
gate:grep=-- 31 same, 1 DIFFER, 0 scope, 0 extra, 0 missing$:P1-MB0
P1-HPX
gate:hpstop:P1-HPX
P1-FREE
P1-PS
gate:grep=^ *1 +\S+ +\S+ +\S+ +/bin/sh *$:P1-PS
P1-N0
P1-AC0
P1-OFF-HP
P1-OFF01
P1-OFF02
P1-OFF03
P1-OFF04
P1-OFF05
P1-OFF06
P1-OFF07
P1-OFF08
P1-OFF09
P1-OFF10
P1-OFF11
P1-OFF12
P1-OFF13
P1-OFF14
P1-OFF15
P1-ICMP?
P1-NMAP?
```

**`I3`** — press 1, rlxfw's driver: twelve trials

```run
P1-TR1-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/TR1\.log *$:P1-TR1-S0
P1-TR1?
P1-TR1-S1
P1-TR2-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/TR2\.log *$:P1-TR2-S0
P1-TR2?
P1-TR2-S1
P1-TR3-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/TR3\.log *$:P1-TR3-S0
P1-TR3?
P1-TR3-S1
P1-TS1-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/TS1\.log *$:P1-TS1-S0
P1-TS1?
P1-TS1-S1
P1-TS2-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/TS2\.log *$:P1-TS2-S0
P1-TS2?
P1-TS2-S1
P1-TS3-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/TS3\.log *$:P1-TS3-S0
P1-TS3?
P1-TS3-S1
P1-UR1-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/UR1\.log *$:P1-UR1-S0
P1-UR1?
P1-UR1-S1
P1-UR2-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/UR2\.log *$:P1-UR2-S0
P1-UR2?
P1-UR2-S1
P1-UR3-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/UR3\.log *$:P1-UR3-S0
P1-UR3?
P1-UR3-S1
P1-US1-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/US1\.log *$:P1-US1-S0
P1-US1?
P1-US1-S1
P1-US2-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/US2\.log *$:P1-US2-S0
P1-US2?
P1-US2-S1
P1-US3-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/US3\.log *$:P1-US3-S0
P1-US3?
P1-US3-S1
```

**`I4`** — press 1, the handover and the vendor's driver; then the owner powers off

```run
P1-DOWN
P1-ETH4
P1-EPING
gate:grep=\b4 packets transmitted, 4 received\b:P1-EPING
P1-ER1-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/ER1\.log *$:P1-ER1-S0
P1-ER1?
P1-ER1-S1
P1-ER2-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/ER2\.log *$:P1-ER2-S0
P1-ER2?
P1-ER2-S1
P1-ER3-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/ER3\.log *$:P1-ER3-S0
P1-ER3?
P1-ER3-S1
P1-ES1-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/ES1\.log *$:P1-ES1-S0
P1-ES1?
P1-ES1-S1
P1-ES2-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/ES2\.log *$:P1-ES2-S0
P1-ES2?
P1-ES2-S1
P1-ES3-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/ES3\.log *$:P1-ES3-S0
P1-ES3?
P1-ES3-S1
P1-EU1-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/EU1\.log *$:P1-EU1-S0
P1-EU1?
P1-EU1-S1
P1-EU2-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/EU2\.log *$:P1-EU2-S0
P1-EU2?
P1-EU2-S1
P1-EU3-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/EU3\.log *$:P1-EU3-S0
P1-EU3?
P1-EU3-S1
P1-EV1-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/EV1\.log *$:P1-EV1-S0
P1-EV1?
P1-EV1-S1
P1-EV2-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/EV2\.log *$:P1-EV2-S0
P1-EV2?
P1-EV2-S1
P1-EV3-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/EV3\.log *$:P1-EV3-S0
P1-EV3?
P1-EV3-S1
P1-TK1
```

**`I-V1`** — press 2, the vendor cold

```run
V1-A
gate:caught:V1-A
V1-AB
V1-HD
gate:grep=^80500010:\t00000000\t00000000\t3C10805F\t26101000$:V1-HD
V1-FL
gate:grep=\A(?:0\n)+\Z:V1-FL
V1-HP
V1-BOOT
wait:V1-HP
V1-ICMP?
V1-NMAP?
```

**`I-V2`** — press 3, the vendor cold

```run
V2-A
gate:caught:V2-A
V2-AB
V2-HD
gate:grep=^80500010:\t00000000\t00000000\t3C10805F\t26101000$:V2-HD
V2-FL
gate:grep=\A(?:0\n)+\Z:V2-FL
V2-HP
V2-BOOT
wait:V2-HP
V2-ICMP?
```

**`I-V3`** — press 4, the vendor cold

```run
V3-A
gate:caught:V3-A
V3-AB
V3-HD
gate:grep=^80500010:\t00000000\t00000000\t3C10805F\t26101000$:V3-HD
V3-FL
gate:grep=\A(?:0\n)+\Z:V3-FL
V3-HP
V3-BOOT
wait:V3-HP
V3-ICMP?
```

**`I-M1`** — press 5, listen only; the owner presses after M1-BOOT opens

```run
M1-FL
gate:grep=\A(?:0\n)+\Z:M1-FL
M1-HP
M1-BOOT
wait:M1-HP
```

**`I-P2`** — press 6, rlxfw between the two vendor groups

```run
P2-A
gate:caught:P2-A
P2-FL
gate:grep=\A(?:0\n)+\Z:P2-FL
P2-HP
P2Q
P2-TK0
P2-M0
gate:until:P2-M0
P2-MB0
gate:grep=^0927be41e91fe4bd32986a48e47c9a3f0d34ce587c7b42324c088b602f45da46  -$:P2-MB0
gate:grep=^  DIFFER  000000  device c66a4126d7b1b862\.\.\. dump 8494cc8666b5c6f6\.\.\.$:P2-MB0
gate:grep=-- 31 same, 1 DIFFER, 0 scope, 0 extra, 0 missing$:P2-MB0
P2-HPX
gate:hpstop:P2-HPX
P2-ICMP?
P2-TK1
```

**`I-V4`** — press 7, the vendor warm

```run
V4-A
gate:caught:V4-A
V4-AB
V4-WZ
gate:prompt:V4-WZ
V4-AB2
V4-HD
gate:grep=^80500010:\t00000000\t00000000\t3C10805F\t26101000$:V4-HD
V4-FL
gate:grep=\A(?:0\n)+\Z:V4-FL
V4-HP
V4-BOOT
wait:V4-HP
```

**`I-V5`** — press 8, the vendor warm

```run
V5-A
gate:caught:V5-A
V5-AB
V5-WZ
gate:prompt:V5-WZ
V5-AB2
V5-HD
gate:grep=^80500010:\t00000000\t00000000\t3C10805F\t26101000$:V5-HD
V5-FL
gate:grep=\A(?:0\n)+\Z:V5-FL
V5-HP
V5-BOOT
wait:V5-HP
```

**`I-V6`** — press 9, the vendor warm

```run
V6-A
gate:caught:V6-A
V6-AB
V6-WZ
gate:prompt:V6-WZ
V6-AB2
V6-HD
gate:grep=^80500010:\t00000000\t00000000\t3C10805F\t26101000$:V6-HD
V6-FL
gate:grep=\A(?:0\n)+\Z:V6-FL
V6-HP
V6-BOOT
wait:V6-HP
```

**`I-V7`** — press 10, the vendor warm

```run
V7-A
gate:caught:V7-A
V7-AB
V7-WZ
gate:prompt:V7-WZ
V7-AB2
V7-HD
gate:grep=^80500010:\t00000000\t00000000\t3C10805F\t26101000$:V7-HD
V7-FL
gate:grep=\A(?:0\n)+\Z:V7-FL
V7-HP
V7-BOOT
wait:V7-HP
```

**`I-M2`** — press 11, a warm reset left to autoboot

```run
M2-A
gate:caught:M2-A
M2-AB
M2-FL
gate:grep=\A(?:0\n)+\Z:M2-FL
M2-HP
M2-BOOT
wait:M2-HP
```

**`I-P3`** — press 12, rlxfw after the warm vendor group; then the owner powers off

```run
P3-A
gate:caught:P3-A
P3-FL
gate:grep=\A(?:0\n)+\Z:P3-FL
P3-TCPD
P3-HP
P3Q
P3-TK0
P3-M0
gate:until:P3-M0
P3-MB0
gate:grep=^0927be41e91fe4bd32986a48e47c9a3f0d34ce587c7b42324c088b602f45da46  -$:P3-MB0
gate:grep=^  DIFFER  000000  device c66a4126d7b1b862\.\.\. dump 8494cc8666b5c6f6\.\.\.$:P3-MB0
gate:grep=-- 31 same, 1 DIFFER, 0 scope, 0 extra, 0 missing$:P3-MB0
P3-HPX
gate:hpstop:P3-HPX
P3-ICMP?
P3-TK1
Z9-D2
Z9-D2A
gate:grep=^b3711d235d01788eba669b088eed1623af887d3ba105c7b9800bccfd460acc92  /:Z9-D2A
gate:grep=^  D2 warm: rlxfw - vendor +\+0\.0078 s  [^\n]*\n  D2 cold: rlxfw - vendor \(a limit, n=3 a side\) +-0\.0004 s  [^\n]*\n  mode cold: M1-BOOT - rlxfw cold +-0\.0000 s  [^\n]*\n  mode cold: M1-BOOT - vendor cold +-0\.0005 s  [^\n]*\n  mode warm: M2-BOOT - rlxfw warm +-0\.0070 s  [^\n]*\n  mode warm: M2-BOOT - vendor warm +\+0\.0008 s  :Z9-D2A
Z9-D2X
gate:grep=^D2: HOLDS$:Z9-D2X
```

**`I9`** — after power-off: the clock log closed, timesyncd back

```run
Z9-HCX?
Z9-HCR?
Z9-TSD
gate:grep=^ActiveState=active$:Z9-TSD
```

**What each stop means, decided now** — every gate, and every cell whose exit stops
the run. Any stop interrupts the invocation's background cells, and `cardrun` never
re-runs a cell whose record exists, so a repeat is always a new name, declared in
`bench/2026-09-24/CORRECTIONS-block43.md` before it runs:

* **`Z0-PREC`**: the port or the attach is wrong — re-attach as `CLAUDE.md` says and repeat
  the pre-flight under a new name; no power.
* **`Z1-ADDR`**: the host has no 10.1.1.2 — nothing networked can run; its command is
  repeated under a new name; no power until it reads.
* **`Z0-HCW`**: the clock log never started or has died — `timesyncd` is still running
  (`Z0-TSD` comes after); `I0` is started again under new names, and the same
  `CORRECTIONS` entry names the replacement's own stop and report (`Z9-HCX` and `Z9-HCR`
  name `Z0-HC`); nothing else runs without a log.
* **`Z0-TSD` / `Z0-HCG`**: no power (§ 3.8).
* **`gate:caught`**, or **`gate:prompt`** on `P1-RZ` or a `V*-WZ`: the loader was not caught
  and may have autobooted the vendor — power off; the press is lost; a retry takes new
  names.
* **an `FL` gate**: the host's entry was not flushed — nothing after it in that press runs
  (a `looprun` would print the entry, a vendor boot's network up would be read through
  it) until the same command, repeated as `<P>-FL2` or `<V>-FL2`, reads `0`; the board
  waits at the loader's prompt meanwhile, and the press continues `--from` the cell after
  the flush. A repeat that does not read `0` ends the press — power off.
* **a `looprun` block's exit** (`P1L`, `P1Q`, `P2Q`, `P3Q`): its artefacts are the reading.
  If its last round reached rlxfw's prompt (its `-boot` capture ends at `# `), the press
  continues in a new invocation `--from` its next cell — the map needs that shell. If
  not, the press ends (power off), and no vendor boot follows before a complete map: the
  block is repeated on a new press with `looprun --attempt 2` (`CLAUDE.md`: never
  `--force`) under new names.
* **`gate:until` on a map** (`P*-M0`): the map did not complete — no vendor boot follows
  until one does: the map is repeated once as `<P>-M0B` and `<P>-MB0B`, and `<P>-MB0B`'s
  output must match the same three patterns as the `MB` gates, applied with `grep -P`
  and read from its output, never by eye; a second failure ends the press.
* **a map gate** (`P*-MB0`, three): a difference — no vendor boot until the owner has
  read it; the rlxfw press may finish `--from` its next cell.
* **`gate:hpstop`**: the probe did not end on SIGINT — its record is read as it stands;
  the press continues `--from` the next cell once `pgrep -f '<P>-HP --target'` prints
  nothing.
* **`P1-PS`'s gate**: the board's `ps` rows are not in the shape every `-S0` gate reads.
  The press continues `--from P1-N0`; `I3` and `I4` run only after a `CORRECTIONS` entry
  states the `-S0` pattern for the shape `P1-PS` showed, checked against `P1-PS`'s own
  output, and runs them with it.
* **a trial's `-S0` gate**, or any stop between a trial's `-S0` and its `-S1`: the next
  invocation starts `--from` that trial's `-S1`, whose `killall` ends any server left —
  never with the next trial's `-S0`, which would meet a stale server.
* **`P1-EPING`'s gate**: the `eth4` trials are void (`NET-54`) and not run; `P1-TK1` runs
  alone, `--from P1-TK1`.
* **a `V*-HD` gate**: no `J`. If its capture shows `Unknown command !` (a swallowed
  command), the read is repeated once as `<V>-HD2` and, if that matches, the press
  continues `--from <V>-FL`; any other reading, or a second failure, ends the press —
  power off at the prompt.
* **a `CAP` cell's non-zero exit**: `console-capture` exits 1 when nothing came back and 2
  when it refused, the port unopened among its reasons — the adapter, the attach or the
  board. `/dev/ttyUSB0` and a command round trip are checked (`CLAUDE.md`, *Environment*),
  then the press continues from that cell under a new name, **and every background cell
  the stop interrupted (a probe, a listener) is repeated with it under a new name**.
  Except a cell that sent `J` (`V*-BOOT`, `M2-BOOT`) or one listening to a boot
  (`M1-BOOT`): the boot it watched cannot be run again — the press ends; power off. No
  stop resumes `--from` a boot cell: `cardrun` refuses it, because its probe would not
  have started (量 the desk dry run of every resumption point).
* **a background cell's exit** never stops a run: `wait:` prints `DONE <cell> rc=N`, and a
  probe that exits non-zero (`hostprobe`'s own instrument failures) is read at the desk
  from the transcript and its record's `problems`.
* **`Z9-D2A`**: the `D2` script is not the one pinned, or does not reproduce seating A —
  `D2` is not computed with it at the bench; the verdict waits for the desk.
* **`Z9-D2X`**: nothing stops but the verdict — no comparison from this seating is
  published until the method is repaired (`P2` stop-loss).
* **`Z9-TSD`**: `timesyncd` did not come back — its command is repeated by hand, declared.

Estimated duration, a guess: seating A's 113.9 active minutes, less its 4.1-minute
re-attach, plus ~0.5 for the dwell, ~0.5 for the tick reads, ~1 for the server logs
net of the restarts they replace, ~0.5 for the head reads and ~3 for the guard — **about
1 h 55 min**, without a pause like seating A's 41 minutes at `P1-A`'s prompt. Every
stalled `rlx0` trial still costs its 70 s.

---

## § 7 What this seating does NOT establish

* **That the numbers are stable to better than `D3`'s ±10 %.** Two days are two
  samples; a hold says the second day landed inside the band, and misses are published.
* **RAW's rate against true time beyond about 50 ppm** (§ 3.0), and the board's tick
  only as far as `TK0`/`TK1`'s brackets resolve.
* **That seating A's corrected values are true durations** — they carry `FW-35`'s
  per-read latency, a cold catch's r is uncertain by ±0.3–0.8 %, and the host's 3–20 s
  swings are not resolved (§ 0 ③). A `D3` miss in column (b) but not (a), or the
  reverse, is read against that.
* **Where inside its bracket either firmware's network came up**; the vendor's brackets
  rest on a reconstruction no frame checks on this card, and the channel offset is
  measured on rlxfw only.
* **That the vendor's daemons are ready beyond TCP 80, 52869 and 52881**, or anything
  about its UDP daemons (the census is an unprivileged TCP scan).
* **Any vendor figure that needs a shell** (`P2` settled item 1).
* **That no flash byte was written.** The maps compare 32 digests over 4,186,112 B of
  4,194,304: they cannot see two writes that cancel, and they do not read `H601`. This
  seating issues no `FLR`.
* **That a boot captured in listen mode measures the same as one caught**, beyond the
  two `M` controls, n = 1 each.
* **The vendor driver's receive path under the vendor firmware**: `eth4`'s trials run
  it on rlxfw's kernel.
* **That the board's server log reads on the board as it read under qemu**: the exact
  sends were dry-run under qemu with the board's own `iperf3` and busybox (§ 0 ①), on
  another kernel (6.6 x86 through qemu 8.2.2, not 2.6.30), another `/tmp` (ext4, not the
  board's ramfs), loopback at ~53 Gbit/s rather than `rlx0`, and a pty rather than the
  38,400-baud console; the `rlx0` stuck-server case never occurred there; and no real
  server's `ps` row was ever matched there — the stand-in showed only how this busybox
  renders those bytes. `P1-PS`'s gate and the `eth4` control are what test it here.
* **That the `tcpdump` filter passes every frame `D8` reads on this day**: seating A's
  host requests all had a zero target; a request with a non-zero one would be dropped.
* **That 2.5 s of dwell is enough on this day** — § 5's refutation line says whether it
  was.
* **Which cell cost the board its ticks**, if `TK0`/`TK1` show a shortfall again: the
  trials' `/proc/stat` pairs narrow it to a cell, not to a cause.

### ⚠️ The fence's scope

The `cells` fence holds every cell in § 5 and every artefact the four `looprun` blocks
write under a name (`*-rNN-rz`, `-ab2`, `-2a`, `-boot`; round 1 has no `-rz`). It does
not hold the conditional cells § 6 names (`Z0-HCG2`, `<V>-HD2`, `<P>-M0B`/`<P>-MB0B`,
the `--attempt 2` repeats), nor anything else `CORRECTIONS` declares. A green `check-predictions` on this card says every fenced cell was captured
after the card; it says nothing about their content.

```cells
bench/2026-09-24/Z0-PRE
bench/2026-09-24/Z0-PREC
bench/2026-09-24/Z1-ADDR
bench/2026-09-24/Z1-EVICT
bench/2026-09-24/Z0-HC
bench/2026-09-24/Z0-HCW
bench/2026-09-24/Z0-TSD
bench/2026-09-24/Z0-HCG
bench/2026-09-24/P1-A
bench/2026-09-24/P1-FL
bench/2026-09-24/P1-TCPD
bench/2026-09-24/P1-HP
bench/2026-09-24/P1L
bench/2026-09-24/P1-RZ
bench/2026-09-24/P1Q
bench/2026-09-24/P1-TK0
bench/2026-09-24/P1-M0
bench/2026-09-24/P1-MB0
bench/2026-09-24/P1-HPX
bench/2026-09-24/P1-FREE
bench/2026-09-24/P1-PS
bench/2026-09-24/P1-N0
bench/2026-09-24/P1-AC0
bench/2026-09-24/P1-OFF-HP
bench/2026-09-24/P1-OFF01
bench/2026-09-24/P1-OFF02
bench/2026-09-24/P1-OFF03
bench/2026-09-24/P1-OFF04
bench/2026-09-24/P1-OFF05
bench/2026-09-24/P1-OFF06
bench/2026-09-24/P1-OFF07
bench/2026-09-24/P1-OFF08
bench/2026-09-24/P1-OFF09
bench/2026-09-24/P1-OFF10
bench/2026-09-24/P1-OFF11
bench/2026-09-24/P1-OFF12
bench/2026-09-24/P1-OFF13
bench/2026-09-24/P1-OFF14
bench/2026-09-24/P1-OFF15
bench/2026-09-24/P1-ICMP
bench/2026-09-24/P1-NMAP
bench/2026-09-24/P1-TR1-S0
bench/2026-09-24/P1-TR1
bench/2026-09-24/P1-TR1-S1
bench/2026-09-24/P1-TR2-S0
bench/2026-09-24/P1-TR2
bench/2026-09-24/P1-TR2-S1
bench/2026-09-24/P1-TR3-S0
bench/2026-09-24/P1-TR3
bench/2026-09-24/P1-TR3-S1
bench/2026-09-24/P1-TS1-S0
bench/2026-09-24/P1-TS1
bench/2026-09-24/P1-TS1-S1
bench/2026-09-24/P1-TS2-S0
bench/2026-09-24/P1-TS2
bench/2026-09-24/P1-TS2-S1
bench/2026-09-24/P1-TS3-S0
bench/2026-09-24/P1-TS3
bench/2026-09-24/P1-TS3-S1
bench/2026-09-24/P1-UR1-S0
bench/2026-09-24/P1-UR1
bench/2026-09-24/P1-UR1-S1
bench/2026-09-24/P1-UR2-S0
bench/2026-09-24/P1-UR2
bench/2026-09-24/P1-UR2-S1
bench/2026-09-24/P1-UR3-S0
bench/2026-09-24/P1-UR3
bench/2026-09-24/P1-UR3-S1
bench/2026-09-24/P1-US1-S0
bench/2026-09-24/P1-US1
bench/2026-09-24/P1-US1-S1
bench/2026-09-24/P1-US2-S0
bench/2026-09-24/P1-US2
bench/2026-09-24/P1-US2-S1
bench/2026-09-24/P1-US3-S0
bench/2026-09-24/P1-US3
bench/2026-09-24/P1-US3-S1
bench/2026-09-24/P1-DOWN
bench/2026-09-24/P1-ETH4
bench/2026-09-24/P1-EPING
bench/2026-09-24/P1-ER1-S0
bench/2026-09-24/P1-ER1
bench/2026-09-24/P1-ER1-S1
bench/2026-09-24/P1-ER2-S0
bench/2026-09-24/P1-ER2
bench/2026-09-24/P1-ER2-S1
bench/2026-09-24/P1-ER3-S0
bench/2026-09-24/P1-ER3
bench/2026-09-24/P1-ER3-S1
bench/2026-09-24/P1-ES1-S0
bench/2026-09-24/P1-ES1
bench/2026-09-24/P1-ES1-S1
bench/2026-09-24/P1-ES2-S0
bench/2026-09-24/P1-ES2
bench/2026-09-24/P1-ES2-S1
bench/2026-09-24/P1-ES3-S0
bench/2026-09-24/P1-ES3
bench/2026-09-24/P1-ES3-S1
bench/2026-09-24/P1-EU1-S0
bench/2026-09-24/P1-EU1
bench/2026-09-24/P1-EU1-S1
bench/2026-09-24/P1-EU2-S0
bench/2026-09-24/P1-EU2
bench/2026-09-24/P1-EU2-S1
bench/2026-09-24/P1-EU3-S0
bench/2026-09-24/P1-EU3
bench/2026-09-24/P1-EU3-S1
bench/2026-09-24/P1-EV1-S0
bench/2026-09-24/P1-EV1
bench/2026-09-24/P1-EV1-S1
bench/2026-09-24/P1-EV2-S0
bench/2026-09-24/P1-EV2
bench/2026-09-24/P1-EV2-S1
bench/2026-09-24/P1-EV3-S0
bench/2026-09-24/P1-EV3
bench/2026-09-24/P1-EV3-S1
bench/2026-09-24/P1-TK1
bench/2026-09-24/V1-A
bench/2026-09-24/V1-AB
bench/2026-09-24/V1-HD
bench/2026-09-24/V1-FL
bench/2026-09-24/V1-HP
bench/2026-09-24/V1-BOOT
bench/2026-09-24/V1-ICMP
bench/2026-09-24/V1-NMAP
bench/2026-09-24/V2-A
bench/2026-09-24/V2-AB
bench/2026-09-24/V2-HD
bench/2026-09-24/V2-FL
bench/2026-09-24/V2-HP
bench/2026-09-24/V2-BOOT
bench/2026-09-24/V2-ICMP
bench/2026-09-24/V3-A
bench/2026-09-24/V3-AB
bench/2026-09-24/V3-HD
bench/2026-09-24/V3-FL
bench/2026-09-24/V3-HP
bench/2026-09-24/V3-BOOT
bench/2026-09-24/V3-ICMP
bench/2026-09-24/M1-FL
bench/2026-09-24/M1-HP
bench/2026-09-24/M1-BOOT
bench/2026-09-24/P2-A
bench/2026-09-24/P2-FL
bench/2026-09-24/P2-HP
bench/2026-09-24/P2Q
bench/2026-09-24/P2-TK0
bench/2026-09-24/P2-M0
bench/2026-09-24/P2-MB0
bench/2026-09-24/P2-HPX
bench/2026-09-24/P2-ICMP
bench/2026-09-24/P2-TK1
bench/2026-09-24/V4-A
bench/2026-09-24/V4-AB
bench/2026-09-24/V4-WZ
bench/2026-09-24/V4-AB2
bench/2026-09-24/V4-HD
bench/2026-09-24/V4-FL
bench/2026-09-24/V4-HP
bench/2026-09-24/V4-BOOT
bench/2026-09-24/V5-A
bench/2026-09-24/V5-AB
bench/2026-09-24/V5-WZ
bench/2026-09-24/V5-AB2
bench/2026-09-24/V5-HD
bench/2026-09-24/V5-FL
bench/2026-09-24/V5-HP
bench/2026-09-24/V5-BOOT
bench/2026-09-24/V6-A
bench/2026-09-24/V6-AB
bench/2026-09-24/V6-WZ
bench/2026-09-24/V6-AB2
bench/2026-09-24/V6-HD
bench/2026-09-24/V6-FL
bench/2026-09-24/V6-HP
bench/2026-09-24/V6-BOOT
bench/2026-09-24/V7-A
bench/2026-09-24/V7-AB
bench/2026-09-24/V7-WZ
bench/2026-09-24/V7-AB2
bench/2026-09-24/V7-HD
bench/2026-09-24/V7-FL
bench/2026-09-24/V7-HP
bench/2026-09-24/V7-BOOT
bench/2026-09-24/M2-A
bench/2026-09-24/M2-AB
bench/2026-09-24/M2-FL
bench/2026-09-24/M2-HP
bench/2026-09-24/M2-BOOT
bench/2026-09-24/P3-A
bench/2026-09-24/P3-FL
bench/2026-09-24/P3-TCPD
bench/2026-09-24/P3-HP
bench/2026-09-24/P3Q
bench/2026-09-24/P3-TK0
bench/2026-09-24/P3-M0
bench/2026-09-24/P3-MB0
bench/2026-09-24/P3-HPX
bench/2026-09-24/P3-ICMP
bench/2026-09-24/P3-TK1
bench/2026-09-24/Z9-D2
bench/2026-09-24/Z9-D2A
bench/2026-09-24/Z9-D2X
bench/2026-09-24/Z9-HCX
bench/2026-09-24/Z9-HCR
bench/2026-09-24/Z9-TSD
bench/2026-09-24/P1L-r01-ab2
bench/2026-09-24/P1L-r01-2a
bench/2026-09-24/P1L-r01-boot
bench/2026-09-24/P1L-r02-rz
bench/2026-09-24/P1L-r02-ab2
bench/2026-09-24/P1L-r02-2a
bench/2026-09-24/P1L-r02-boot
bench/2026-09-24/P1L-r03-rz
bench/2026-09-24/P1L-r03-ab2
bench/2026-09-24/P1L-r03-2a
bench/2026-09-24/P1L-r03-boot
bench/2026-09-24/P1Q-r01-ab2
bench/2026-09-24/P1Q-r01-2a
bench/2026-09-24/P1Q-r01-boot
bench/2026-09-24/P1Q-r02-rz
bench/2026-09-24/P1Q-r02-ab2
bench/2026-09-24/P1Q-r02-2a
bench/2026-09-24/P1Q-r02-boot
bench/2026-09-24/P1Q-r03-rz
bench/2026-09-24/P1Q-r03-ab2
bench/2026-09-24/P1Q-r03-2a
bench/2026-09-24/P1Q-r03-boot
bench/2026-09-24/P1Q-r04-rz
bench/2026-09-24/P1Q-r04-ab2
bench/2026-09-24/P1Q-r04-2a
bench/2026-09-24/P1Q-r04-boot
bench/2026-09-24/P2Q-r01-ab2
bench/2026-09-24/P2Q-r01-2a
bench/2026-09-24/P2Q-r01-boot
bench/2026-09-24/P2Q-r02-rz
bench/2026-09-24/P2Q-r02-ab2
bench/2026-09-24/P2Q-r02-2a
bench/2026-09-24/P2Q-r02-boot
bench/2026-09-24/P3Q-r01-ab2
bench/2026-09-24/P3Q-r01-2a
bench/2026-09-24/P3Q-r01-boot
bench/2026-09-24/P3Q-r02-rz
bench/2026-09-24/P3Q-r02-ab2
bench/2026-09-24/P3Q-r02-2a
bench/2026-09-24/P3Q-r02-boot
```

```cardnum
cells-fence	246	count bench/2026-09-24/PREDICTIONS-B45-block43.md ^bench/2026-09-24/
declared-date	1	count bench/2026-09-24/PREDICTIONS-B45-block43.md [*][*]declared date 2026-09-24[*][*]
another-day	1	count bench/2026-09-24/PREDICTIONS-B45-block43.md [*][*]another day than `bench/2026-09-23/PREDICTIONS-B44-block42[.]md`[*][*]
presses-caught	11	count bench/2026-09-24/PREDICTIONS-B45-block43.md ^CAP -{2}out bench/2026-09-24/[A-Z0-9]+-A -{2}esc 180 -{2}esc-period
presses-listen	1	count bench/2026-09-24/PREDICTIONS-B45-block43.md ^CAP -{2}out bench/2026-09-24/M1-BOOT -{2}until
cap-cells	123	count bench/2026-09-24/PREDICTIONS-B45-block43.md ^CAP -{2}out
host-cells	83	count bench/2026-09-24/PREDICTIONS-B45-block43.md ^HOST&? bench/2026-09-24/
send-over-127	0	count bench/2026-09-24/PREDICTIONS-B45-block43.md -{2}send '[^']{128,}'
no-shell-subst	0	count bench/2026-09-24/PREDICTIONS-B45-block43.md -{2}send '[^']*[$]
no-flr	0	count bench/2026-09-24/PREDICTIONS-B45-block43.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-24/PREDICTIONS-B45-block43.md -{2}send '[^']*(EW |EB |FLW )
no-burn	0	count bench/2026-09-24/PREDICTIONS-B45-block43.md -{2}send '[^']*AUTOBURN
ifdown-cells	1	count bench/2026-09-24/PREDICTIONS-B45-block43.md ^CAP .*-{2}send '[^']*ifconfig rlx0 down
vendor-jumps	7	count bench/2026-09-24/PREDICTIONS-B45-block43.md ^CAP .*-{2}send 'J 80500000' -{2}until 'port 80'
listen-jbfc	1	count bench/2026-09-24/PREDICTIONS-B45-block43.md ^CAP .*-{2}send 'J BFC00000' -{2}until 'port 80'
head-reads	7	count bench/2026-09-24/PREDICTIONS-B45-block43.md ^CAP .*-{2}send 'DW 80500000 8'
burn-reads	12	count bench/2026-09-24/PREDICTIONS-B45-block43.md ^CAP .*-{2}send 'DW 8040D4A0 1'
tick-reads	6	count bench/2026-09-24/PREDICTIONS-B45-block43.md ^CAP .*-{2}send 'cat /proc/stat ; cat /proc/interrupts'
trial-servers	24	count bench/2026-09-24/PREDICTIONS-B45-block43.md ^CAP .*-{2}send 'iperf3 -s -1 -f k -{2}logfile /tmp/[A-Z]{2}[1-3][.]log
trial-server-check	24	count bench/2026-09-24/PREDICTIONS-B45-block43.md ^CAP .*-{2}send .iperf3 -s -1 [^']* & sleep 2 ; ps ; cat /proc/stat
trial-logs-read	24	count bench/2026-09-24/PREDICTIONS-B45-block43.md ^CAP .*-{2}send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/[A-Z]{2}[1-3][.]log
dwell-macro	1	count bench/2026-09-24/PREDICTIONS-B45-block43.md ^`LR` = `.* -{2}dwell-seconds 2[.]5`$
tcpdump-cells	2	count bench/2026-09-24/PREDICTIONS-B45-block43.md ^HOST& .* tcpdump -n -tt -i enxfc19286184c9 'icmp or [(]arp and arp\[6:2\] = 1 and arp\[18:4\] = 0 and arp\[22:2\] = 0[)] or [(]arp and arp\[6:2\] = 2 and [(][(]arp\[8:4\] = 0x02524c58 and arp\[12:2\] = 0x4657[)] or [(]arp\[8:4\] = 0x560a0101 and arp\[12:2\] = 0x01e8[)][)][)]'$
p2q-nfjrom-bytes	1155072	size /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/kroot/rtkload/nfjrom
p2q-nfjrom-sha256	4972edbadd2655a8	sha256-16 /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/kroot/rtkload/nfjrom
p2l-nfjrom-bytes	1181696	size /home/key/fwre-work/rebuild/p2-2/rtk/p2l/rlxfw/kroot/rtkload/nfjrom
p2l-nfjrom-sha256	888c930aa31763d9	sha256-16 /home/key/fwre-work/rebuild/p2-2/rtk/p2l/rlxfw/kroot/rtkload/nfjrom
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
init-bytes	2153	size config/rlxfw-init.sh
A-quiet-boot	2117	size bench/2026-09-23/P1Q-r01-boot.log
A-loud-boot	7948	size bench/2026-09-23/P1L-r01-boot.log
A-map	3013	size bench/2026-09-23/P3-M0.log
A-vendor-boot	1789	size bench/2026-09-23/V1-BOOT.log
A-vendor-boot-order1	2f921f7508dd69b4	sha256-16 bench/2026-09-23/V3-BOOT.log
A-vendor-boot-order2	89df2d260b86e48d	sha256-16 bench/2026-09-23/V1-BOOT.log
A-m1-boot	1901	size bench/2026-09-23/M1-BOOT.log
A-m2-boot	1979	size bench/2026-09-23/M2-BOOT.log
A-offset-cell	139	size bench/2026-09-23/P1-OFF02.log
A-burn-read	71	size bench/2026-09-23/V1-AB.log
burn-read-model	71	dwreply 1
vendor-head-bytes	118	size bench/2026-08-31c/K2-2a.log
vendor-head-sha256	8d152d00beadabba	sha256-16 bench/2026-08-31c/K2-2a.log
head-read-model	118	dwreply 8
A-retro-table	b5870ad92c08b408	sha256-16 bench/2026-09-23/Z9-D2.tsv
A-r-per-catch	7f76052d64455ee7	sha256-16 /home/key/fwre-work/rebuild/s106/c-clock/f5-best.tsv
A-r-per-window	b6773418b85591e1	sha256-16 /home/key/fwre-work/rebuild/s106/c-clock/f6-rt4.tsv
d2-script	b3711d235d01788e	sha256-16 /home/key/fwre-work/rebuild/s105-analysis/s105-d2.py
runblock-script	21287d2e33c7b8e8	sha256-16 /home/key/fwre-work/rebuild/s109/card/runblock.py
no-ab-gates	0	count bench/2026-09-24/PREDICTIONS-B45-block43.md ^gate:grep=.8040D4A0
hd-gates	7	count bench/2026-09-24/PREDICTIONS-B45-block43.md ^gate:grep=.80500010:
console-capture-1.5	1	count tools/console-capture.py ^TOOL_VERSION = "1[.]5"$
hostprobe-1.3	1	count tools/hostprobe.py ^TOOL_VERSION = "1[.]3"$
looprun-1.3	1	count tools/looprun.py ^VERSION = "1[.]3"$
hostclock-1.0	1	count tools/hostclock.py ^TOOL_VERSION = "1[.]0"$
cardrun-1.0	1	count tools/cardrun.py ^TOOL_VERSION = "1[.]0"$
```
