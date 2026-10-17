# `rlxfw-entropy` — an entropy source, and its credit policy

Source: [`rlxfw-entropy.c`](../../kernel/linux-2.6.30/drivers/char/rlxfw-entropy.c), version 1.0, with
[`rlxfw-entropy.h`](../../kernel/linux-2.6.30/include/linux/rlxfw-entropy.h) and
[`0009-random-rlxfw-input.patch`](../../config/host-compat/0009-random-rlxfw-input.patch) ·
reasoning and every reading: [`notes/entropy.md`](../../notes/entropy.md) ·
the file head until 2026-10-18, verbatim: [`rlxfw-entropy.c`](entropy-history.md)

## What it does

On this board the kernel's pool stayed empty: `entropy_avail` read 0 after about 770 NIC
and 7,700 serial interrupts (`FW-160`). No interrupt in the image is registered with
`IRQF_SAMPLE_RANDOM`, and setting the flag would not have fixed it (`FW-161`). The broker's logins fail closed until 128 bits have been seen once,
so without a source rlxfw could never issue a session token.

The source is the arrival phase of `rtl819x-nic`'s interrupts, read on the free-running
TC0 counter at the top of the ISR. Every event mixes 12 bytes into the pool, which makes
no claim. An event qualifies when the first, second and third differences of the phase
series are all non-zero, and the driver credits one bit per sixteen qualifying events,
never more than one bit per jiffy (`FW-164`; notes § 4). The timer tick and the console
were rejected as sources — the tick is periodic by construction, and an unattended boot
types nothing — and `IRQF_SAMPLE_RANDOM` on the NIC would credit the same event twice
(notes § 3.2). `/proc/rlxfw-entropy` prints the counts, a histogram of the smallest
difference, and `TC0DATA` and `CDBR` raw.

## Registers

It reads four words of the timer block and writes none, so neither tick can be disturbed.
Base, offset and shift are the ones `rtl819x-timer.c` already carries on two sources; no
new register value enters code (notes § 3.1).

| register | address | what the driver does | row · V · N |
|---|---|---|---|
| `TC0CNT` | `0xB8003108` | reads, once per event, before taking the lock | `REG-07` · 量 · 讀 |
| `TCCNR` | `0xB8003110` | reads once at probe: refuses to report the source alive unless `TC0EN` is set | `REG-09` · 量 · 讀 |
| `TC0DATA`, `CDBR` | `0xB8003100`, `0xB8003118` | read once at probe and printed raw | `REG-05` · 量 · 量; `REG-11` · 量 · 讀 |

## What holds on the silicon

- 量 the pass conditions written before the run all held: after a first burst
  `qualifying 1151`, `bits 71` and `entropy_avail` 71, the two accounts equal; after a
  flood of 4,000 echoes, 9,125 qualifying events earned 403 bits, the per-jiffy clamp
  firing 2,665 times (`FW-179`, 2026-09-30).

## Known limits

- It is accounting, not strength: a pass shows the source is alive and the accounting
  works, not that an event carries the entropy credited. The sixteen-fold derating is an
  argument, and the min-entropy per event is unmeasured (notes § 6, § 7).
- After the first reading the driver's `bits` and the kernel's `entropy_avail` parted by
  two drops of exactly 128 bits, cause not found (`FW-180`).
- TC0's rate under Linux is not measured; only the ratio of 2,000 counts per jiffy is
  (`CLK-23`), so no decision uses a rate.
- Whether CP0 `Count` is absent or present and clock-gated is open (`CPU-42`), and the
  Lexra `lxc0` register file has never been probed for a counter (notes § 7).
- Packet timing is a source an attacker on the LAN can influence; the clamp bounds a
  flood to at most 100 bits a second (`FW-164`).
