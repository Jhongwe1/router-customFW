# PREDICTIONS — Session B4, block 6 (`NET-11`: re-read `PSRP2` while its jack is empty)

**Written 2026-08-25 at the bench, after `E13-pos1-wan` and before this read.**
Nothing is touched between the two: the cable stays in the WAN socket and
`PSRP2`'s jack stays empty.

## Why this read exists and why it is free

`E13-pos1-wan` returned **`PSRP2 = 0x000011E9`** — down, with bit 8 latched by a
cable pull, and **bits 3 and 0 still reporting full duplex / 100M on an empty
socket**. Two propositions come out of that word and both are testable by reading
the same register again with nothing changed:

1. **Bit 8 is read-to-clear.** `NET-11` records this as measured, but every
   observation behind it — `E11a2`, `E11c2`, `E11e` — came from a link that was
   settling **up**, where *"a second real latch"* and *"the read did not clear
   it"* produce the same reading. `E11c2` solved that by reading a port whose
   jack was empty. **This read has the same property and a cleaner event**: the
   down-event is a cable pull that has already happened and cannot recur while
   the socket stays empty.
2. 🆕 **Speed and duplex are not gated by `LinkUp`.** Nothing in this repository
   has claimed that in either direction. If bits 3 and 0 are still set on the
   second read, they are retained state and not a transient.

```cells
bench/2026-08-25/E11f-psrp2-empty
```

### `E11f-psrp2-empty` — `--send 'DW BB804128 8' --seconds 5`

```
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400 \
    --out bench/2026-08-25/E11f-psrp2-empty --send 'DW BB804128 8' --seconds 5
```

| word | register | prediction |
|---:|---|---|
| 3 | `PSRP2` | 🔴 **`0x000010E9`** — bit 8 **cleared by the previous read**, bits 3 and 0 **still set** |
| 1 | `PSRP0` | `0x000010F9`, unchanged — the WAN link is up and stable |
| 2,4,5 | `PSRP1`,`PSRP3`,`PSRP4` | `0x000010E0` |
| 6,7,8 | — | `000000E2` · `0000007A` · `0000007A` — eleventh observation |
| bytes | | **118** |

**The four outcomes, and each says something different:**

| `PSRP2` reads | reading |
|---|---|
| **`000010E9`** | 🔴 **both propositions hold.** Bit 8 read-to-clear, now on a down-settle with an empty jack — the strongest instance this bench can produce. And speed/duplex are **retained state**: a driver reading them without checking bit 4 reports a live 100M link on an empty socket |
| `000011E9` | 🔴 **bit 8 is NOT read-to-clear**, and `NET-11`'s measured finding is refuted on the one event class it was never tested against. That is worth more than this cell — the three prior observations were all up-settles, where the two models are indistinguishable |
| `000010E0` | bit 8 cleared **and** speed/duplex cleared. Then the `E9` in the previous read was a transient of the pull itself, and proposition 2 is dead — the fields are gated after all, just late |
| `000011E0` | bit 8 held and speed/duplex cleared. Neither proposition; record it and stop reading this register for conclusions |

**Refutes**: for proposition 1, that the previous bit-8 readings could have been
second up-latches rather than an uncleared flag. For proposition 2, that `PSRP`'s
speed and duplex fields mean anything without bit 4 read first.
