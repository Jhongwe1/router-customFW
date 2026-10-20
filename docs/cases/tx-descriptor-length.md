# `rlx0`'s transmit loss was a descriptor length

Seen under gate `P2` on 2026-09-23, located and fixed under `R6b`, whose result is the `R6b`
entry of [`docs/GATE-RESULTS.md`](../GATE-RESULTS.md) (2026-09-28). Ids are rows of
[`SPEC.md`][spec] ([how to read one](../spec/README.md)), owned by
[`notes/nic-driver.md`](../../notes/nic-driver.md) (`NET-122` by
[`docs/nic-vendor-diff.md`](../nic-vendor-diff.md) as well). Marks: 量 measured on the
device, 讀 read out of code or a dump, 推 inferred.

## Symptom

量 On seating 39, nine of twelve `iperf3` trials on `rlx0` (driver 1.4) failed: six
end-of-test exchanges never completed and three could not connect, `No route to host`
([`NET-111`][spec]; [`bench/2026-09-23/`](../../bench/2026-09-23/)). 量 The vendor's driver,
`eth4`, on the same kernel completed all twelve ([`NET-114`][spec]).

## First hypothesis, and why it was wrong

The bench's own record, written during the seating and committed that evening with the log entry,
left the end-of-test stall open: 推 *"a TX stall with too few frames queued to fill the ring"*
([`CORRECTIONS-block42.md`](../../bench/2026-09-23/CORRECTIONS-block42.md) § 4.1). The log entry
([`docs/log/2026-09.md`](../log/2026-09.md), 2026-09-23, 105th segment, § 3), written at the close
after the counters below refuted it, gives another (translated): *"My hypothesis during the
seating was 'the receive side is stuck and swallows `TEST_END`' and 'not answering ARP is the same
receive state'."* 量 The switch's counters, read through `eth4`, resolved no receive loss and
counted 182 fewer frames out than the driver had sent: the loss is on transmit ([`NET-112`][spec]).

Block 45's card, frozen before its power, made length its test — E2, replies at 11 lengths with
every residue mod 4 where earlier controls used ≡ 2 mod 4, predicted 220 of 220, refuted by a
lost reply ([`PREDICTIONS-B47-block45.md`](../../bench/2026-09-25b/PREDICTIONS-B47-block45.md) § 3).
量 Replies of 263, 1,511 and 1,512 B were almost all lost while 60, 276, 1,513 and 1,514 B passed,
and the CPU port counted frames in a size bucket no reply could fill ([`NET-119`][spec]).

## The single-variable cut

讀 Driver 1.5 put the descriptor lengths behind a `/proc` verb, `txlen`: `rlxfw` writes
1.4's lengths, `vendor` the vendor's ([`NET-125`][spec], notes § 23.1); block 47's card ran E2
three times on one boot, in cells that differ only in that word: `E-F1-SW` and `E-F2-SW` type
`txlen vendor`, `E-L1-SW` between them `txlen rlxfw`
([`PREDICTIONS-B49-block47.md`](../../bench/2026-09-26/PREDICTIONS-B49-block47.md), § 5).
量 Both `vendor` arms answered 220 of 220 with the CPU port's error counters at Δ 0; the
`rlxfw` arm answered 145 of 1,327 ([`NET-128`][spec]). 量 Block 48 ran the same three arms on
a second boot: 220 of 220 twice, and 144 of 1,189 between them ([`NET-132`][spec]).
量 In loopback, one field at a time (which field, 讀 notes § 23.1): raising `m_len` alone to
`ph_len` clears every bad length; changing `m_extsize` alone clears none ([`NET-129`][spec]).

## Cause

讀 The loader's send routine writes a TX descriptor's three length fields equal,
`ph_len` = `m_len` = `m_extsize`, as the vendor's two paths do; of four writers, only rlxfw's
three fields are unequal ([`NET-122`][spec]). 讀 1.4 wrote `m_len` = F, four bytes short of
`ph_len` = F + 4, and a constant `m_extsize` of 2,046 ([`NET-129`][spec]). 推 Where the frame
changes is a span, after the driver's fill in descriptor memory and at or before the CPU
port's receive MAC, assembled from 量 parts; that it is the TX DMA engine is not established
([`NET-132`][spec]). 推 Why 1.4's lengths fail is not known: the rule that predicts the bad
lengths in loopback, `M1`-cover8, was fitted after blocks 45 and 46, held on all twelve maps,
and is not a cause ([`NET-129`][spec]).

## Positive control

The `rlxfw` arm between the two `vendor` arms is the control: had the brackets lost the
ability to see the fault, it would have read clean as well. 量 It reproduced the loss on both
boots ([`NET-128`][spec], [`NET-132`][spec]). 量 Under load at the fix, 31 minutes and
2,363,511 frames fired no recovery, while 1.4 fired 12 in 120 s on the same boot
([`NET-141`][spec]).

## The check left behind

讀 Since `rtl819x-nic` 1.6 a boot starts at the vendor's lengths: `NIC15_LEN_BOOT` is
`NIC15_LEN_VENDOR` in [`rtl819x-nic-tx.h`](../../kernel/linux-2.6.30/drivers/net/rtl819x-nic-tx.h)
([`NET-154`][spec]); 量 one boot at that default read E2 at 220 of 220 ([`NET-158`][spec]).
[`tools/nic15check.py`](../../tools/nic15check.py) compiles that header with the host's gcc;
its case `K22` asserts the boot policy — `vendor`, not dirty, `m_len` and `m_extsize` at F + 4
for 60, 61 and 1,514 — and mutant `M26`, which reverts the macro, must be killed by `K22`. CI
runs it: workflow `instruments` ([`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)),
job `instruments`, step `nic15check`; it turns red if the boot policy becomes anything but
`vendor` or the vendor lengths change. It cannot see the kernel's initialiser that reads the
macro, which only the desk tool `tools/storeseq.py` reads in a built ELF; CI runs its self-test only.

[spec]: ../../SPEC.md
