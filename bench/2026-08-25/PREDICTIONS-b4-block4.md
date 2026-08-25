# PREDICTIONS — Session B4, block 4 (`H3b`, `NET-13`, first point: the cable where it already is)

**Written 2026-08-25 at the bench, after the operator stated where the cable is
and before the register is read.** That ordering is the whole point of this
block: `NET-13` has been got wrong twice, **both times because the jack was
labelled after the reading**.

## The naming rule this block introduces, and why the sheet's was not enough

`RUNSHEET.md` `H3b` says *"the jack written into the `--out` filename"* and names
`E13-jack1`, `E13-jack2`, `E13-jack4`, `E13-jack5`. **`jackN` is a physical
position counted from the WAN socket. The operator reads a silkscreen label.**
Those are two different things and they coincide only if the case is printed
`WAN LAN1 LAN2 LAN3 LAN4` in physical order; a case printed
`WAN LAN4 LAN3 LAN2 LAN1` makes every one of the four filenames a different
socket from the one intended, **and nothing in the capture would say so**.

**So every filename in this block carries both**: `E13-pos<N>-<silkscreen>`,
where `pos1` is the WAN socket and `posN` counts along the case. Where the
physical order is not yet established, the position component is `posX` and this
file says why.

🔴 **Stated for this cell, before the read:** the operator reports **five RJ45s,
one marked WAN and four marked LAN, with the cable in the socket they call the
2nd LAN.** The silkscreen-to-position order is **not yet established**, so this
capture is `E13-posX-lan2` and it establishes *lan2 → port*, not *jackN → port*.
Resolving `posX` is one look at the case and it is asked for in the same message
as this read.

```cells
bench/2026-08-25/E13-posX-lan2
```

### `E13-posX-lan2` — `--send 'DW BB804128 8' --seconds 5`

```
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400 \
    --out bench/2026-08-25/E13-posX-lan2 --send 'DW BB804128 8' --seconds 5
```

🔄 **`0xBB804128` and not `0xB8003250`.** The sheet's `H3b` row carried the
latter, it exists nowhere else in this repository, and it is inside the SoC
register window — so it returns eight plausible words and the cable moves would
have measured something else, silently. Corrected in `RUNSHEET.md` in the same
session, before it was typed.

| | prediction |
|---|---|
| bytes | **118**, 2 lines — `len(cmd) 13 + 2 + 47 × 2 + 9`. Matches `E10b`'s measured 118 |
| **shape** | 🔴 **exactly one of `PSRP0`–`PSRP4` (words 1–5) has bit 4 set.** Two set, or none, refutes the bijection that seven cable moves have not managed to refute |
| the linked port | `0x000010F9` — **or `0x000011F9`**, and both pass. Bit 8 is `LinkDownEventFlag`, latched and read-to-clear, **and this is its first read on this power cycle**, so a latched link-settling event is expected rather than surprising (`E11a`) |
| the four dark ports | `0x000010E0` each. `0xE0` and not `0x99`: bits 6 and 5 are the negotiated pause, they default set, and it is a partner *not* advertising PAUSE that clears them |
| words 6, 7, 8 | `000000E2` · `0000007A` · `0000007A` — 🆕 **and this is the ninth observation and the first on a different power cycle.** The previous eight are all from one boot (`E9`, `E10b`, `E11a`–`E11e`), so *invariant across cable moves* and *invariant across boots* were the same eight readings until now |

**Which register lights is the measurement, and it is not predicted here**,
because predicting it would need the very map this cell exists to establish —
which is exactly how `E10d` became a control that could not fail. What is
pre-registered is the mapping from outcome to conclusion:

| if bit 4 is set in | then |
|---|---|
| `PSRP3` (word 4) | the socket the operator calls **LAN2 is port 3** |
| `PSRP4` (word 5) | **LAN2 is port 4** |
| `PSRP2` (word 3) | **LAN2 is port 2** |
| `PSRP1` (word 2) | **LAN2 is port 1** — the port `PORT1`'s patch list skips |
| `PSRP0` (word 1) | **LAN2 is port 0**, the port the WAN socket is expected to be |

Under the old map (`0,2,3,4,1` by position from the WAN side) and a case printed
in ascending order, LAN2 is position 3 and this reads `PSRP3`. Under the same
old map with a descending case, LAN2 is position 4 and this reads `PSRP4`.
**Both are recorded here before the read, and the case's printing order decides
between them — not this capture.**

**Refutes**: nothing on its own. It is one point of a map, taken for free because
the cable was already in a socket and the operator named that socket first. Three
more points follow when the case order is known.
