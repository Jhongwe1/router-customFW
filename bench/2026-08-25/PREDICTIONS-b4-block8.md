# PREDICTIONS — Session B4, block 8 (`NET-13`, point 4: LAN3 — the one that closes the map)

**Written 2026-08-25 at the bench, after the operator moved the cable to the
socket marked LAN3 and said so, and before the register is read.**

## Where the map stands

| socket | port | capture |
|---|---|---|
| WAN | **0** | `E13-pos1-wan` |
| LAN1 | **1** | `E13-posX-lan1` |
| LAN2 | **2** | `E13-posX-lan2` |

`H_silk` — WAN → port 0, LAN *n* → port *n* — has survived three tests.
**Five sockets onto five ports is a bijection** (every read so far has had
exactly one port with bit 4 set, twelve times now, and no read has ever had two
or none), so this capture **closes the map**: whatever LAN3 lights, LAN4 is the
remaining port by elimination.

⚠️ **And elimination is not measurement.** If the operator does not move the
cable a fourth time, LAN4's entry is recorded as *derived by elimination from a
bijection that has not been refuted*, and it is marked 推 rather than 量.

```cells
bench/2026-08-25/E13-posX-lan3
```

### `E13-posX-lan3` — `--send 'DW BB804128 8' --seconds 5`

```
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400 \
    --out bench/2026-08-25/E13-posX-lan3 --send 'DW BB804128 8' --seconds 5
```

**Four of the five port words are derived rather than assumed**, from the two
findings made this session — bit 8 latches on a cable pull and is cleared by the
read that sees it; speed and duplex are retained state not gated by `LinkUp`:

| word | register | prediction | why |
|---:|---|---|---|
| 4 | `PSRP3` | **`0x000011F9`** or `0x000010F9` | `H_silk`. Both pass — bit 8 depends on whether the up-link settles in one latch |
| 2 | `PSRP1` | 🔴 **`0x000011E9`** | just pulled: bit 4 clear, bit 8 set **by this pull**, bits 3/0 retained at 100M full duplex |
| 1 | `PSRP0` | 🔴 **`0x000010E9`** | emptied one move ago and its bit 8 was **read** in the previous capture, so it is clear again; 3/0 retained |
| 3 | `PSRP2` | 🔴 **`0x000010E9`** | emptied two moves ago. Retained state has now had three captures to decay and must not have |
| 5 | `PSRP4` | `0x000010E0` | never linked this power cycle — **the within-read control for the retained-state finding**: it is the only port that has never negotiated, and it is the only one that may read `E0` |
| 6,7,8 | — | `000000E2` · `0000007A` · `0000007A` | thirteenth observation |
| bytes | | **118**, 2 lines | |

**What each outcome means:**

| bit 4 set in | reading |
|---|---|
| `PSRP3` | 🔴 **`H_silk` survives its fourth test and the map closes**: WAN→0, LAN1→1, LAN2→2, LAN3→3, and LAN4→4 by elimination. `NET-13` moves from 未定 to a map whose every point had its label fixed before its own reading |
| `PSRP4` | **`H_silk` is dead at the last point**, LAN3→4 and LAN4→3 by elimination — and that is a **more** interesting result than the clean one, because it is the concrete instance of *take the index from a register, not from a label* that `E12` has only ever stated in the abstract |
| `PSRP0`, `PSRP1` or `PSRP2` | two sockets to one port: the bijection is refuted after thirteen chances, and that is worth more than the map |

**Refutation condition for the whole map**, restated so it is on the page that
closes it: any read with **two ports' bit 4 set, or none**, while exactly one
cable is in the board.
