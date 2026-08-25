# PREDICTIONS — Session B4, block 7 (`NET-13`, point 3: LAN1 — the decisive socket)

**Written 2026-08-25 at the bench, after the operator moved the cable to the
socket marked LAN1 and said so, and before the register is read.**

## Where the map stands, and why this socket

| socket, as the operator names it | port | capture |
|---|---|---|
| LAN2 | **2** | `E13-posX-lan2` |
| WAN | **0** | `E13-pos1-wan` |

`H_silk` — **WAN → port 0, LAN *n* → port *n*** — has survived two tests.

🔴 **LAN1 is the socket that matters most of the five.** Port 1 is the port the
loader's `PORT1` factory-test routine **skips**: `0x8040B890` holds the four
bytes `{0, 2, 3, 4}` and port 1 is not among them (`NET-07`,
`docs/loader-phy-and-switch.md` §4). A proposal made at the bench on 2026-08-24 —
*"port 1 has no jack, so there is nothing to patch"* — was refuted by `E11e`,
which lit `PSRP1` by plugging a cable into the fifth socket. **But that socket's
label was assigned after the reading**, so *which* socket port 1 is behind has
never been established with the label fixed first. This capture is that.

```cells
bench/2026-08-25/E13-posX-lan1
```

`posX` again: the case's printing order is still not recorded, so this file
establishes *lan1 → port*, not *jackN → port*.

### `E13-posX-lan1` — `--send 'DW BB804128 8' --seconds 5`

```
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400 \
    --out bench/2026-08-25/E13-posX-lan1 --send 'DW BB804128 8' --seconds 5
```

**Three of the five words are now predicted from findings made twenty minutes
ago, which is what makes this read a test of them and not just of the map:**

| word | register | prediction | why |
|---:|---|---|---|
| 2 | `PSRP1` | **`0x000011F9`**, or `0x000010F9` | `H_silk`. Bit 8 set is expected — a settling up-link latches it (`E11a`) — and either value passes |
| 1 | `PSRP0` | 🔴 **`0x000011E9`** | derived, not assumed: bit 4 clear (cable pulled), **bit 8 set** by that pull (block 6's read-to-clear result says the flag was left clear, so a 1 here is this pull), **bits 3 and 0 retained** at 100M full duplex (block 6's retained-state result). **All three parts can fail separately** |
| 3 | `PSRP2` | 🔴 **`0x000010E9`** | the socket emptied two moves ago: bit 8 stays clear because nothing new happened to it, and 3/0 stay set because retained state does not decay. **If bit 8 is set here, retained state is not what block 6 measured and something re-latches without an event** |
| 4 | `PSRP3` | `0x000010E0` | never linked this power cycle |
| 5 | `PSRP4` | `0x000010E0` | never linked this power cycle |
| 6,7,8 | — | `000000E2` · `0000007A` · `0000007A` | twelfth observation |
| bytes | | **118**, 2 lines | |

**Shape / refutation:** exactly one of words 1–5 with bit 4 set. Two or none
refutes the bijection.

**What each outcome means:**

| bit 4 set in | reading |
|---|---|
| `PSRP1` | 🔴 **`H_silk` survives its third test, and the socket behind the port `PORT1` skips is named for the first time with its label fixed in advance.** One socket left to make the map complete |
| `PSRP3` or `PSRP4` | **`H_silk` is dead.** The silkscreen order is not the port order, and the map is whatever these four captures say it is — which is still a map, and still built the right way round |
| `PSRP0` or `PSRP2` | two sockets to one port. That refutes the bijection, and it is worth more than the map |
