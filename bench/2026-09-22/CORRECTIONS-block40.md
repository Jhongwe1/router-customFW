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
