# PREDICTIONS — Session B4, block 5 (`NET-13`, point 2: the WAN socket)

**Written 2026-08-25 at the bench, after the operator moved the cable to the WAN
socket and said so, and before the register is read.** Naming rule and the
outcome-to-conclusion table are in
`bench/2026-08-25/PREDICTIONS-b4-block4.md` and are not restated.

**Point 1, already measured:** the socket the operator calls **LAN2 → port 2**
(`E13-posX-lan2`, `PSRP2` = `0x000010F9`, the only port with bit 4 set).

## What is being built here, and what is not

**Not** the withdrawn position map. `SPEC.md` `NET-13` records both `0,2,3,4,1`
and its linear replacement as withdrawn, **because in both cases the jack labels
were assigned after the reading**. Rebuilding either of them requires the case's
printing order, which this repository has never recorded and which is one look at
the case, not a register read.

**What this block builds is `silkscreen → port`**, one point per capture, each
labelled by the operator *before* its own read. That is the map a driver and a
user actually need — the position map is a fact about the case drawing, and it
is now a separate question with a separate owner.

**Hypothesis under test, stated before this read**, and it has survived exactly
one point so far:

> **`H_silk`: WAN → port 0, and LAN *n* → port *n*.**

`LAN2 → port 2` is consistent with it. **This read is its second test and its
first on a socket that is not a LAN.**

```cells
bench/2026-08-25/E13-pos1-wan
```

⚠️ **`pos1` is not an assumption here.** This project's position numbering is
defined as *counted from the WAN socket*, so the WAN socket is position 1 by
definition, whatever order the LAN labels run in. This is the one socket whose
position and silkscreen label cannot disagree.

### `E13-pos1-wan` — `--send 'DW BB804128 8' --seconds 5`

```
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400 \
    --out bench/2026-08-25/E13-pos1-wan --send 'DW BB804128 8' --seconds 5
```

| word | register | prediction |
|---:|---|---|
| 1 | `PSRP0` | **`0x000011F9`** if `H_silk` holds — bit 4 up, **and bit 8 set**: the cable was just pushed in and a settling link latches a down-event (`E11a` measured exactly that). `0x000010F9` also passes |
| 2 | `PSRP1` | `0x000010E0` |
| 3 | `PSRP2` | 🔴 **`0x000011E0` — down, with bit 8 SET.** This is the sharpest prediction in the block: a real link-down event **just happened** on this port, the flag is latched, and `E13-posX-lan2` read it clear (`0x000010F9`) minutes ago, so the 1 cannot be residue |
| 4 | `PSRP3` | `0x000010E0` |
| 5 | `PSRP4` | `0x000010E0` |
| 6,7,8 | — | `000000E2` · `0000007A` · `0000007A` — **tenth observation, second power cycle** |
| bytes | | **118**, 2 lines |

**Shape, and it is the refutation condition:** exactly one of words 1–5 has bit 4
set. Two, or none, refutes the five-sockets-to-five-ports bijection that eight
cable moves have now failed to refute.

**What each outcome means:**

| bit 4 set in | reading |
|---|---|
| `PSRP0` | 🔴 **`H_silk` survives its second test.** WAN → port 0, and the case's printing order becomes the only thing standing between this and a complete map |
| anything else | 🔴 **`H_silk` is dead**, and the port it names is worth more than the hypothesis it killed. Record it and carry on with the remaining two sockets |

**And bit 8 on `PSRP2` is a control on the instrument, not on the board.** If it
comes back **clear**, then either `DW` is not reading what this block thinks it is
reading, or `LinkDownEventFlag` does not latch on a cable pull — and the second
of those contradicts `E11c2`/`E11e`, on which `NET-11`'s read-to-clear finding
rests. **A cable pull is the cleanest down-event this bench can produce**, and
until now every bit-8 observation came from a link that was settling *up*.
