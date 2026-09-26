# CORRECTIONS — block 48 (card `PREDICTIONS-B50-block48.md`, frozen in `7c4df71`)

Each entry is written before the cell it declares runs. The card is not edited.

## 1. `D3-LUS1-L`'s liveness gate (2026-09-26 19:35:04), and § 6's read set and recovery (`<n>` = 1)

**What happened (量).** `I-D3` stopped at `gate:grep D3-LUS1-L` (`/^4 packets transmitted, 4
received/ not found`): `D3-LUS1-L.log` reads `4 packets transmitted, 0 received, 100% packet
loss`, and its kernel-log window (`D3-LUR1-H.log`'s `window_end` 1421178 → 1423150) reads
`bug_preempt 2`, `usbnet_xmit 2`, `call_trace 2`, `follower 1`. The cell before it was 1.4's
UDP receive trial `D3-LUR1` and its bracket, which ran to `D3-LUR1-SN` (rc 0). Every
invocation before `I-D3` exited 0 (`I-0` … `I-U`); the twelve trials at the fix and `LUR1`
ran.

**What the card decides (§ 6, "A liveness gate … or a path gate").** `follower` is 1, so this
is not the follower-alone case: the host → board path is the question (`NET-124`, `NET-54`
殘留). Before any recovery and with `rlx0` left as it is, `NET-54` 殘留 ②'s read set runs in its
order as the cells whose text § 6 fixes, logged here as they run; then the recovery (6)–(8). If
`X-L1` passes, `I-D3` continues `--from D3-LUS1-S0` (the trial's `-S0`); if it fails, `I-Z`
runs. No capture runs during `I-D3` (§ 0 ⑤), so the re-attach ends no `tcpdump` and no
`W-TCPE2`/`W-TCPS2` is started; `X-TC1` reads what runs.

**The cells, in order.** Board reads take the card's own capture forms (§ 5): a single page read
as the `-LS` cells (`--idle 3 --seconds 12`), the full bracket as a `-R` read (its `--until`,
15 s). `CAP`, `HP`, `HN`, `FL`, `PL` and `DW` are § 5's macros.

```
CAP --out bench/2026-09-26b/X-SW1 --send 'cat /proc/rtl819x-switch' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/X-PHY1 --send 'echo read 3 0 > /proc/rtl865x/phyReg ; echo read 3 1 > /proc/rtl865x/phyReg ; echo read 3 1 > /proc/rtl865x/phyReg' --idle 3 --seconds 12
HOST bench/2026-09-26b/X-HP1 :: HP
CAP --out bench/2026-09-26b/X-BR1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26b/X-PS1 --send 'cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/X-HN1 :: HN
X-RA1 (PowerShell): usbipd list; usbipd detach --busid <GbE>; usbipd attach --wsl --busid <GbE>; then in WSL R0-ADDR's command
CAP --out bench/2026-09-26b/X-SW1b --send 'cat /proc/rtl819x-switch' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/X-PHY1b --send 'echo read 3 0 > /proc/rtl865x/phyReg ; echo read 3 1 > /proc/rtl865x/phyReg ; echo read 3 1 > /proc/rtl865x/phyReg' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/X-PS1b --send 'cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/X-TC1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-26b/X-L1 :: FL 10.1.1.3 ; PL ; DW none
```

A HOST cell's log is its command's stdout and stderr, as the runner writes one. Any board cell
whose capture holds `Booting...`, `---RealTek`, `<RealTek>` or `Linux version`: the owner powers
off at once (§ 6, the loader gate). A board read that returns nothing, garbage, or never ends:
the owner powers off.

**Alternatives rejected.** Recovering first: § 6 orders the read set before any recovery, since
the re-attach may bounce port 3's link and erase what the reads hold. Skipping `LUS1` and going
to `I-Z`: § 6 continues `--from` the trial's `-S0` when the recovery passes. Retyping the
liveness under its own name: a repeat is a new name, and `X-L1` is the card's.

**Not established by this entry.** Why the path failed after `LUR1`; whether the host adapter,
port 3 or the board's receive side holds the fault — the read set is what the record reads.

**As run (量).** `/dev/ttyUSB0` present (19:34). The read set ran 19:36–19:37:23, every board
cell rc 0 with no loader text: `X-SW1` 1,670 B, `X-PHY1` 241 B (port 3 `BMCR` `0x1100`, `BMSR`
`0x78ed` on both reads), `X-BR1` 10,838 B ending on its `until`, `X-PS1` 585 B (`Port3` `LinkUp`),
`X-HP1` and `X-HN1` written (neighbour `STALE`). `X-RA1`: `usbipd list` read the GbE adapter at
busid `2-4`; `usbipd detach --busid 2-4` rc 0 at 19:37:46.9; the `attach` typed 70 ms later printed
*There is no device with busid '2-4'* (rc 1: the list reads as a drop for about a second after a
detach, CLAUDE.md); `usbipd list` re-read at 19:37:53 showed `2-4` `Shared`, and
`usbipd attach --wsl --busid 2-4` printed its three `info` lines, rc 0, at 19:38:01.9. The
interface was present within about 1 s; R0-ADDR's command (`X-RA1.log`) shows
`inet 10.1.1.2/24`. `X-SW1b` 1,670 B, `X-PHY1b` 241 B, `X-PS1b` 585 B, each rc 0 with no loader
text; `X-TC1` `0`; `X-L1` `4 packets transmitted, 4 received`, `follower 1` (19:38:36). The
recovery passed: `I-D3` continues `--from D3-LUS1-S0`, its transcript
`run-I-D3-r2.log`.
