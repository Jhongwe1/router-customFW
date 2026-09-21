# CORRECTIONS — block 40, seating 37

The card is **not edited**. `check-predictions` reads a capture's mtime against
the card's, so repairing a frozen card destroys the evidence that the captures
came after the predictions. Everything below is recorded here instead.

`check-predictions` reads **34 of 39**, and that number stands.

---

## § 1 The five cells the card named that no capture answers to

All five are **naming departures in `run-partD.sh`**, not cells that failed to
run. The work each one described was done; the capture landed under a different
prefix. The cause is that the runner was written after the card was frozen, to
carry the two declared departures in § 2, and it named its cells after the
runner's own loop variables rather than after the card's.

| card cell | what actually ran | where it landed |
|---|---|---|
| `D0-N` | the dump after the `recover 0` control run | `D0-CTRL-N` |
| `D1-N1` | the dump after run 1 at `recovms 1000` | `D1-R1-N` |
| `D1-N2` | the dump after run 2 | `D1-R2-N` |
| `D1-N3` | the dump after run 3 | `D1-R3-N` |
| `D1-ON` | `echo recover 1` between the control arm and the `D1` arm | `D0-RESCUE` |

🔴 **This is a defect of mine and it is the same shape as one already in the
record.** Seating 14 rebuilt mid-seating under one cell name and lost the first
image's artefacts; the rule that came out of it is *one cell name per image*.
The same discipline applies to capture prefixes and a runner written after the
freeze is exactly where it breaks. **A runner should take its cell names from
the card's `cells` fence rather than inventing them.**

⚠️ Nothing is lost: all five captures exist, are committed, and are cited by
`notes/nic-driver.md` § 16.3 under the names they actually have.

---

## § 2 The two declared departures from the card, and why each was made

Both are written into `run-partD.sh`'s comment header, beside the cells they
produced.

### 2.1 The direction is reversed — the board is the server

The card runs `iperf3 -c` on the **board**, in the foreground. 量 at
`C2-IPERF`: that hangs the board's only shell behind a client with no
total-run timeout, and then nothing can be read. `C3-AFTER.log` is **23
bytes** — the length of its own command echo and nothing else.

🔴 **Seating 31 recorded this exact fix and I did not apply it**: *"讓它可量的
是把板子端的 client 放到背景 `&`"*. The card I wrote carried the defect that
finding exists to prevent.

⚠️ **The NIC was fine throughout.** After the run the board answered `arping`
and pinged 3/3 — so the instrument failed and the subject did not, which is the
distinction that took eight minutes to make. See § 3.

### 2.2 `recovms` is swept

The card says the threshold is left at its default and that sweeping it is a
separate seating. 量 at `B8`: one 8 s / 0.5 Mbit/s ladder produces **three**
stalls, so at `recovms 1000` the interface is out for about a third of the time
under load, and any throughput figure would mostly measure the detector's own
latency. That is the mistake `NET-85`'s 203 MBytes / 23.3 Mbit/s already made
once. So `D5` was taken at **1000 ms and at 20 ms**.

🟢 **The sweep's own control held**: `n_recov_spurious` reads **0** at
`recovms 20` (`recov_jiffies` 2), so a threshold 50× shorter does not fire on
transients the level test has already cleared. 🔴 **And the sweep's result is
negative**: throughput did not move between the two thresholds, so the recovery
latency is not what limits the number.

---

## § 3 Three instrument defects of mine, none of which cost a power cycle

1. 🔴 **A passive console capture cannot test liveness.** A hung board and a
   shell sitting idle at a prompt both produce **0 bytes**. I read 0 bytes as
   *hung* and spent about eight minutes on it, including killing the host
   server to "free" a board that was already free. The discriminator is a
   command that produces **output** — `echo RLXFW-LIVE-MARK` returned its echo,
   its output and the prompt on the first try. `CLAUDE.md` 2026-09-17 states
   this rule for the USB link (*the liveness question is answered by a command
   that comes back*); I applied it to the adapter and not to the board.

2. 🔴 **Piping a bench runner into `head` kills it.** `run-partA.sh` was run as
   `bash … | head -130`; when `head` exited, SIGPIPE killed the runner at cell
   **6 of 8**, and `A5-PING` and `A6-SW` never ran. They were re-run and the
   captures are present. This is the bash form of the `Select-Object -First N`
   trap `CLAUDE.md` already records for PowerShell. **Runners write to a file
   and the file is read.**

3. 🔴 **`cardcheck numbers` refuses a CRLF card and names the wrong cause.**
   `tools/cardcheck.py:322` opens the card `"rb"` and decodes, so there is no
   universal-newline translation, and `FENCE_RE` requires an LF immediately
   after the fence marker. This card was written with a tool that emits CRLF on
   Windows, and the refusal read *"has no cardnum fence"* — true of the bytes
   and useless as a diagnosis. Converted to LF; `15 of 15` re-derived after.
   量: every card in this repository is pure LF, by accident of how each was
   produced. Nothing enforces it and nothing warns. `SPEC.md` `FW-108`.

---

## § 4 Parts F, G, H, J and X — declared off-card

The card's own § before the `cells` fence states that the fence covers **Parts
A–E only**, so `34 of 39` is a statement about A–E and not about the seating.

| cells | what they are |
|---|---|
| `F0`–`F4` | `NET-82`'s A/B, which the card made **conditional** on `n_ph_diff > 0`. That condition was met at `X10-PH` (281 of 1,555) |
| `G0`–`G3`, `H0`–`H3` | `D5`'s runs. `G1`–`G3` failed on the board-side server being stuck in a test state left by `F4`'s timeout; `H0` restarted it and `H1`–`H3` are the runs that produced numbers |
| `J0`–`J2` | does fixing RX prevent the TX stall? It does not |
| `X0`–`X11` | diagnostics: the pre-rescue `AUTOBURN` read, the liveness tests of § 3.1, `NET-82`'s first divergence kept whole, and three by-hand recoveries |
| `C3b-AFTER` | the re-take of `C3-AFTER`, which got only its own echo |

🔴 **Part G of the card — `R6-6`'s write half — did not run, and that was a
decision.** It was the one high-risk cell the owner authorised, scheduled last.
Two of `R6-6`'s three DoD clauses were already measured unreachable before
power (one cable gives one `LinkUp`; rlxfw cannot write the VLAN table, 讀
`rtl819x-switch.c:88-92`), and the vendor `/proc` write path it would have used
is already proven by `NET-100`'s three-source read-back. So a success would
have closed nothing, and a hang costs a power press on a board with no spare.
**Authorisation is not obligation.**


---

## § 5 What a second reader found in what I had already published

Two re-derivations were run over the captures **without sight of the
write-ups**, so a disagreement would be informative rather than an echo. Both
independently produced finding ① below. Everything here was then re-derived
from the captures by me before being written down.

### 5.1 🔴 `n_recov_spurious` is 1, not 0, and `n_recov_fire` is 25, not 26

Published: *"26 stops, 26 recoveries, `n_recov_fail` 0, `n_recov_spurious` 0"*.
量 `E5-RST.log`, the last dump of the seating:

```
n_tx_stop 26   n_tx_wake 1
n_recov_arm 26   n_recov_fire 25   n_recov_ok 25
n_recov_wake 25  n_recov_fail 0    n_recov_spurious 1
```

🟢 **The corrected numbers are better, because they close two ways with no
residual**: `fire 25 + spurious 1 = 26 = arm`, and
`recov_wake 25 + tx_wake 1 = 26 = n_tx_stop`. The one queue restart the
recovery did not perform was done by `:754`'s cheap path after `E0-RESC`'s
hand rescue — so `n_tx_wake 1` beside `n_recov_wake 25` is the ISR path
working once, not a defect.

🟢 **And the single spurious firing is worth more than a zero.** It fell at
`recovms 20`, giving that branch its first positive reading; a counter that has
only ever read 0 is a claim with no control. It does not meet the card's
refutation condition, which needs `spurious >= 1` **with** `fire 0`.

### 5.2 🔴 The `B8` ladder produced TWO stalls, not three

Published in the closeout narrative and in `run-partD.sh`'s header: *"one 8 s /
0.5 Mbit/s ladder produces three stalls"*. 量: `B6-AFTER` reads `n_tx_stop 1`
and `B9-AFTER` reads **3**, so the increment is **2** — and the two dumps
bracket `B7-PING` as well as `B8-LADDER`, so even the 2 cannot be attributed to
the ladder alone. The `recovms` sweep that reasoning motivated still happened
and its result (throughput did not move) is unaffected; the premise was wrong
by one and unattributed by construction.

🔴 `run-partD.sh` is **not edited**. It is a record of what was typed, and its
header's arithmetic is corrected here rather than rewritten there.

### 5.3 🔴 The dereference check the card states cannot be evaluated from a dump

Card § 2.4 and the driver's own comment both say: *`ph_last_bf` must equal
`bufs + ph_last_j × NIC_BUF_SZ + NIC_RX_OFFSET`*.

讀 `nic_ph_buf()`: `nic_ph_last_j` is assigned on **every** call, immediately
after `nic_ph_class()`; `nic_ph_last_bf` is assigned **only** on the branch
where a SKEW resolved to a usable slot. When the last classified frame was an
AGREE, the two fields describe different events and the identity is not
expected to hold — **and no field in the dump says which case it is in**.

量 over the 25 dumps that carry both: the identity holds in **10** and fails in
**15**, and the failures track exactly the windows where `n_ph_diff` did not
move (`ph_last_bf` frozen at one value while `ph_last_j` walks).

🔴 **So this is a defect in my driver, not in the hardware, and the card states
the check as though it were usable.** The fix is one of: give `ph_last_bf` a
companion `ph_last_cls`, or move `ph_last_j` onto the same branch. Neither is
done; no image has been built since.

### 5.4 🔴 The `phtest` control does not exercise the term it exists to certify

All four cells pass slot **0**. With `i = 0` the AGREE test
`w0 == nic_rx_mb + i * NIC_DESC_BYTES` is indistinguishable from
`w0 == nic_rx_mb`, so **a driver that had dropped the `+ i * NIC_DESC_BYTES`
term entirely would produce exactly the four readings observed**. Only
`A3-PH2`'s `ph_test_j 1` carries information; the other three `ph_test_j 0`
values are the echo of the typed slot argument, because `nic_ph_class()` sets
`*j_out = i` first and overwrites it only on the SKEW path.

⚠️ One more cell — `phtest A15B8128 1`, predicting AGREE — would have closed
it, and the verb already accepts it. **A positive control that fires four times
is not automatically a control over everything it appears to test.**

### 5.5 🔴 `G1`–`G3` name three different things in one directory

The frozen card's Part G is `G1-RD` / `G2-WR` / `G3-RB` / `G4-PING`, the
`/proc/rtl865x/memory` switch-register write — the one high-risk cell, which
**did not run** (§ 4). The files `G1.log`, `G2.log`, `G3.log` in this directory
are `iperf3` runs from an off-card script.

🔴 **A reader matching capture names to the card will read them as the switch
test.** The card's cells carry a `-RD`/`-WR`/`-RB` suffix and mine do not, but
that is a distinction that has to be noticed rather than one that cannot be
missed. This is the third identifier collision this project has recorded
(`NET-14`, `regcensus`, and this), and the first inside one bench directory.

### 5.6 ⚠️ Three numbers in the `iperf3` logs that must not be quoted

* **`Retr` and `Cwnd` are meaningless here.** `4698944` is the `Retr` of the
  *first* interval row of all ten runs that produced interval rows — a per-run
  retransmit count cannot be a constant. `F1`'s third row reads
  `Retr 4290268702` with `Cwnd 1.08 GBytes` on a board with 32 MiB of RAM.
  This is `TCP_INFO` coming back wrong under `qemu-mips-static`, which
  `notes/iperf3-port.md` already records; the sender-summary `Retr` comes from
  the same source and is no better.
* **iperf3's own elapsed is not wall clock on a killed run.** `F4` reports
  16.81 s for a window the host measured at 71.9 s, and `H2` reports 33.95 s
  against 71.8 s. Its interval clock advances only when its `select` loop
  wakes, so on a wedged socket it stops. **Every Mbit/s in § 16.3 is therefore
  normalised on the `-t 30` window and cross-checked against the board's own
  counters**, not taken from the `sender` row.
* **`j_now` wrapped mid-seating.** It reads `4294943368` at `A3-PH1` and `112`
  at `X1-REST`. `recov_j_arm`/`recov_j_fire` are raw jiffies, so those two
  dumps carry a fire timestamp 4.29 billion ticks in the "future".
  `fire − arm` is still exactly 100 because both sides wrapped together, but
  any expression of the form `j_now − recov_j_fire` is wrong there. Nothing in
  this seating computes one.

### 5.7 ⚠️ `C2-IPERF` and `C3-AFTER` pass the gate while containing nothing

Both are fence cells and both score as passes: `check-predictions` reads
**existence and mtime, not content**. `C2-IPERF.log` is 84 bytes (the echoed
command and `Connecting to host`) and `C3-AFTER.log` is 23 bytes (the echo of
`cat /proc/rtl819x-nic` with no reply). The cell that actually carries C's
reading, `C3b-AFTER`, is **outside** the fence.

⚠️ This is the limitation `CLAUDE.md` already records for seating 20, arriving
again. It is not a repair I can make here: repairing the card destroys the
mtime evidence.
