# CORRECTIONS — block 50 (card B52, `bench/2026-09-27b/PREDICTIONS-B52-block50.md`)

Written during the press, before the correction is executed, as § 6 requires for anything it
does not list ("no cell runs until the owner has read it; the decision goes into
`bench/2026-09-27b/CORRECTIONS-block50.md` first"). Times are the session's WSL clock, read from
the `XCELL … t0` lines in `/home/key/fwre-work/rebuild/s113/run43b/`.

## 1. `X-RE1`'s attach ran inside the post-detach drop; its attach half is repeated once as `X-RE1b`

**What happened (量).** `I-D3LUR1` stopped at `D3-Y-L` (0 of 4, after `LUR1`, on `LUS1`'s re-armed
1.4 ring). S1 ran as § 6 writes it: the read set (`X-SW1` … `X-HN1`, 14:55:45–14:55:56), `X-C1`
branch a (host tx Δ 6 and port 3 rx Δ 6; board n_tx Δ 6 with CPU-port CRC Δ 3, drop Δ 1, port 3
out Δ 2), `X-NIC1a` (14:57:28: `tx_stopped 0`, no recovery armed or fired), `X-L1a` (14:57:38:
`4 packets transmitted, 0 received`, `follower 1`) — so branch b: `X-PHY1` (14:59:02: PHY 3 reg 0
`0x1100`, reg 1 `0x78ED`), `X-REL1` (14:59:21: the GbE adapter at busid `2-4`, Attached; the
CP2102 at `1-1`, Attached). `X-RE1` (14:59:30) ran
`usbipd.exe detach --busid 2-4 ; usbipd.exe attach --wsl --busid 2-4` through WSL interop: the
detach took effect, the attach issued at once printed
`usbipd: error: There is no device with busid '2-4'.`, and `X-RE1` exited 1. A fresh
`usbipd list` from PowerShell about 2 s later read `2-4` **Shared** (detached) and `1-1`
Attached. `CLAUDE.md` records that right after a detach `usbipd list` looks like a drop for about
a second; `X-RE`'s declared text puts the attach inside that second.

**The correction.** The attach half of `X-RE1` is repeated once, alone, as
`bash /home/key/fwre-work/rebuild/s113/card43b/inv43b.sh --x X-RE1b "usbipd.exe attach --wsl --busid 2-4"`
(accepted by `inv43b.sh --dry --x`, so its rc reaches `rc.tsv`), after a fresh `usbipd list`
has shown `2-4` Shared. Branch b then continues exactly as § 6 writes it from `X-REA1`: the
line after the hold with `X-SW1b` and `X-PS1b`, then `X-TC1` and `X-L1b` beside the watch, and on
`X-L1b` passing S2's line (§ 6: a 1.4 cell stopped its invocation, so the first cell typed after
S1's handling is that arm's end re-arm, typed as `X-RA1` with `D3-Y-SW`'s text at `LUS1`'s policy,
`txlen rlxfw`), whose continuation is `I-D3LUR1` with tag `r2` `--from` the trial's `-S0` (here
`D3-LUS1-S0`, the cell § 6 names for a failure inside `D3`'s invocations) and then `L1`'s
invocations after it (`I-WLUS1` under the next unused watch, `I-D3LUS1`, `I-CN`), then the next
tail watch; on `X-L1b` failing, every later host arm is skipped as § 6 writes (`I-N9` if
`N1.pcap` runs, then `I-Z`). If `X-RE1b` itself fails, that
is branch b's recovery failing: the same skip. Nothing else changes; the card's declared bounce
of port 3's link at a re-attach, and P0 (b) void at the pair that spans it, apply unchanged.

**Alternatives rejected.** (1) Reading `X-RE1`'s exit 1 as branch b's failure and skipping every
later host arm: it would read a timing artefact of the host tool as the host path's state and
give up `NET-131`'s deciding bracket, arm P and `R6b-4` for it, while `X-PHY1` and `X-NIC1a` show
a board with its link up and no stall. (2) Powering off: the same loss. (3) Typing `X-RE`'s whole
text again as `X-RE2`: its detach would act on a device already detached, and the attach it then
issues is the only half that is missing.

**What it does not establish.** Whether `X-L1a`'s 0 of 4 was the host path or 1.4's TX on the
liveness replies: `X-C1` read branch a (every host frame reached port 3; the board's TX side lost
or corrupted its replies), and § 6 sends a failing `X-L<n>a` to branch b regardless. `X-RE1b` is
the first attach through WSL interop not preceded by a detach within a second.

## 2. `X-L1b` failed on `LUS1`'s 1.4 ring; a liveness at the fix decides whether the press goes on

**What happened (量).** After correction 1: `X-RE1b` (15:11:10) rc 0, `2-4` Attached; `X-REA1`
(15:11:23) `UP,LOWER_UP`, 10.1.1.2/24; `X-SW1b` and `X-PS1b` (15:11:41–15:11:46): `psrp3 000001F9
up 1` (bit 8 set by the re-attach's bounce, as § 6 declares), port 3 `LinkUp`; `X-TC1`: `0`;
`X-L1b`: `4 packets transmitted, 0 received`, `follower 1`. § 6: "If it fails: every later host
arm is skipped — `I-N9` if `N1.pcap` runs, then `I-Z`."

**Why the rule is not followed as written (推 from 量).** Every liveness since the stop ran on
`LUS1`'s own ring, re-armed at 1.4 by `D3-Y-SW` (`txlen rlxfw`). `X-C1` read branch a: every frame
the host sent reached port 3 (host tx Δ 6, port 3 rx Δ 6), and the board's replies were lost on
its TX side (n_tx Δ 6, CPU-port CRC Δ 3, drop Δ 1, port 3 out Δ 2) — 1.4's TX fault on the reply
lengths, which a host-side recovery cannot reach. Branch b's re-attach changed nothing (`X-L1b`
0 of 4). The skip rule would give up `NET-131`, arm P and `R6b-4` on a reading that names the
board's 1.4 TX and not the host path. D3's second boot is not at stake: its twelve fix trials and
`LUR1` ran before the stop.

**The correction (the owner's decision, 2026-09-27, after reading this).** One line after the
hold: `X-RA1v`, S2's re-arm text with `<txlen>` = `vendor` (the fix) in place of `LUS1`'s
`rlxfw`, then the tail watch; then `X-L1c`, the liveness (`FL 10.1.1.3 ; PL ; DMW none`) beside
the watch. **If `X-L1c` passes**, the host path is shown reaching the board and the board
answering at the fix: `LUS1` (`I-D3LUR1`'s cells after `D3-Y-L`, `I-WLUS1`, `I-D3LUS1`) is void,
never a result, and the press continues with `L1`'s next invocation, `I-CN`, then `L2`, `L3`,
`L4` and the power-off line as § 6 writes them, every watch renamed to the next unused number (the
card's `X-W15` … `X-W24` become `X-W36` … `X-W45`). `NET-131`'s arm, which re-arms its own ring,
goes by § 6 unchanged, S1 included. **If `X-L1c` fails**, § 6's rule applies as written: every
later host arm is skipped, `I-Z`, the power-off.

**Alternatives rejected.** (1) The rule as written: see above. (2) Running `LUS1` at the fix:
it would no longer be the 1.4 control it is registered as. (3) A further re-attach: `X-L1b`
already showed the re-attach changes nothing.

**What it does not establish.** That the 1.4 ring's liveness failures here and in block 48 are
the length fault and not something else on the 1.4 ring: `X-L1c` separates the host path from the
board at the fix, not the cause at 1.4.

## 3. An unplanned pull and re-plug before arm P's pull window; the board's watch is restarted

**What happened (量, and the owner's report).** `I-P1` ended at 15:20:56: `P-W` started the
board's watch (`LPW start rlx0 v 1 rc 0`, its capture at 15:20:46, 600 s), `P-CW0` read the host
adapter at carrier 1 with `carrier_changes 0`, and `P-WT1` read `cut permit` (since 0.1 min).
The session asked for the pull and stopped. In the reply the owner reported having pulled the
cable by accident before being told, then plugging it back in. The host adapter read at 15:23:53:
carrier 1, `carrier_changes 2`, `carrier_up_count 1`, `carrier_down_count 1` — one link-down and
one link-up after `P-CW0`, inside `P-W`'s span. No window was open; the board's tail watch
`X-W37` held the console. § 6 lists an early action only as a `CW` window that starts at carrier
0; this one ended before any window, so it is not listed.

**The correction (the owner's decision, 2026-09-27, after reading this).** § 6's restart of the
board's watch — written for `P-WT1` refusing — is taken as if `P-WT1` had refused, so that arm P
is read on a watch whose span holds only the planned actions: one line after the hold,
`--stop X-W37`, then `X-SW2` (S1's switch-page text on its own log: a fresh baseline of `PSRP3`,
`lde` and `lj` after the unplanned pair), `X-PW1` (`P-W`'s text on `lpw1.log`) and `X-PWS1`
(`P-WS`'s on that log, which must read `LPW start rlx0 v 1 rc 0`), then the tail watch; then the
pull as § 6 writes it (`L3`, every watch renamed to the next unused number). After the restart at
`P-WT1`, § 6's own rules follow: the check before the re-plug is `X-PWT1` (`P-WT2`'s text on
`X-PW1.meta.json`); the watch read after the re-plug is the later watch's, with `X-LWH1` waiting
for it and `X-PLW1`/`X-PLWR1` reading it, as § 6 writes for a restarted watch. P11 and P12 are
judged on `X-PW1`'s span alone; their deltas are read from `X-SW2`, and also from `P-SW0` as a
reading that includes the unplanned pair.

**The unplanned pair itself** is a reading, not a result: `P-W`'s log (`/tmp/lpw.log`, read by
the card's `P-LW` cells) holds it if the board's watch saw it — an unplanned positive control for
the watch mode, 推 until read.

**Alternatives rejected.** (1) Going on with `P-W` as is: its expected sequence (`1`, pull `0`,
re-plug `1`) would carry an extra `0`/`1` pair and P11 would read it as a mismatch. (2) Voiding
arm P: the board, the cable and both watches are intact; only the span needs moving.

**What it does not establish.** The exact times of the unplanned pair (the host logs no link
events; `carrier_changes` bounds them to 15:20:54–15:23:53); whether the board's first watch saw
both edges (read from `P-W`'s log later).

## 4. The owner extends the press's ceiling; `R6b-4`'s block runs without `I-C4`

**What happened (量).** `CUT-4` (`--since-max 44 --start-by 23:05` on `R1-CATCH.meta.json`,
14:38:16) permits `R6b-4`'s block only if it starts by 15:22:16. S1's handling and corrections 1–3
moved arm P's end to 15:35:52 (`X-LWH1`), 58 min after the catch, so `I-C4` would refuse and S6
would skip `I-4F`, `I-WF` and `I-4F9` (the 31-minute flood, `D4`'s traffic).

**Why.** § 6 states that `CUT-4`'s since-max guards no reading — `D4`'s criterion and `NET-76`'s
reads depend on no boot age — and is derived from the press length the owner accepted (85 min,
2026-09-27) less the 40.60 min to the block's end. The press length is the owner's call.

**The correction (the owner's decision, 2026-09-27, 15:3x, after reading the question).** The
owner extends the ceiling to about 110 minutes. The rest of `L4` runs as one line from `I-P3B`
with `I-C4` omitted (no cell reads `CUT-4`'s log), then `I-4F` … `I-4L9` and `I-Z` as § 6 writes
them; `CUT-T` and `CUT-L` (`--end-by 23:52`, `--need`) run unchanged. The P2/D4 readings are read
as the card defines them; the only change is that the block ran later in the boot than the card's
estimate placed it.

**Alternatives rejected.** Cutting `R6b-4` as written: `D4` would need another press on this
image, for a guard that protects no reading.

**What it does not establish.** Nothing about the flood depends on this; the press's length and the
owner's time are what changed.

## 5. An omission, recorded after the fact: `X-PLW1` was not typed before the power-off

**What happened (量).** Correction 3 took § 6's restarted-watch path, under which the later
watch's log is read by `X-PLW1` (`cat /tmp/lpw1.log`) with `X-PLWR1` (`--expect-seq 1,0,1`)
beside the watch, after the line from `I-P3B`. That line (`L4` from `I-P3B`, `I-C4` omitted by
correction 4) ended at 16:18:57 with `I-Z` rc 0 and `X-W47` holding the console. The session then
asked for the power-off without typing `X-PLW1`; the owner powered off (confirmed by 16:26:37),
and `/tmp/lpw1.log`, in the board's RAM, was lost. This is the session's error, not a stop of
the card.

**What it costs.** P11's board-watch half on `X-PW1`'s span (the planned pull and re-plug alone)
is unmeasured. What remains for arm P: the first watch's log, read by `P-LW2` in `I-P3B` (it
spans the unplanned pair of correction 3 and the planned pull, and ended at 15:30:46, before the
re-plug); the host's carrier watcher in `P-PULL` (carrier 1 → 0 at t 21.054 s) and `P-PLUG`
(0 → 1 at t 11.799 s); the switch pages `X-SW2`, `P-SW1` (`up 0`) and `P-SW2` (`up 1`); and
`linkprobe`'s `get` reads in `I-P2` and `I-P3`.

**No alternative existed after the power-off**: nothing else holds the later watch's log.

## 6. `X-RE1b.log` is kept outside the repository

`X-RE1b`'s capture holds `usbipd`'s own info line naming the host's WSL NAT address, a private
IPv4 that `tools/audit-bench-log.py` flags before any commit. The file is kept under
`$FWRE_WORK/rebuild/s114/post43/withheld/X-RE1b.log`, unedited; its exit code (`XCELL X-RE1b
rc=0`) is in `$FWRE_WORK/rebuild/s113/run43b/rc.tsv`, and the attach it made is read in the
repository from `X-REA1.log` (`UP,LOWER_UP`, `10.1.1.2/24`) and the reads after it.
