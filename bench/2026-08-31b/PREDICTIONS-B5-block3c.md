# PREDICTIONS — Session B5, block 3c: the MTD read repeated on cycle 6, because the rate it measured had n=1

**Written at the bench on 2026-08-31, during cycle 6's boot, BEFORE either cell
below was run.** Block 3's `M-b`/`M-c` were refuted by a missing symlink and
block 3b recovered them with `busybox wc`. Both readings were taken in **one
power cycle**, so everything they measured has n=1.

🔴 **Not to be edited after the first capture lands.**

---

## §1 Why repeat something that already passed

Block 3b returned two exact matches, and an exact match is the outcome that most
deserves a second sample: it is also what a **cached or constant** answer looks
like.

| what block 3b established | why one cycle is not enough |
|---|---|
| the line counts are 4,422 and 7,943 | both were read after the same boot, through the same `mtd_read` on the same warm SPI controller. A second cold power cycle is the only thing that separates *the flash reads correctly* from *this boot read correctly* |
| 🔴 the rate is **919–997 KB/s**, ~16× `CLK-15` | **n=1 per partition, and it refuted the card's own 推 by an order of magnitude.** A number that overturns a published estimate on one sample is exactly the number to take twice |

⚠️ **These two cells do not close `FLS-20` and are not a byte comparison.** Same
caveat as block 3b §3: a newline count is an aggregate over the partition.

## §2 The cells

Run **after `X-5b`**, so nothing here disturbs the `FW-32 殘留` null, which is
decided entirely by `X-3`'s timing.

| # | typed | expect | bytes | 🔴 stop if |
|---|---|---|---:|---|
| **X-b2** | `CAP --out bench/2026-08-31b/X-b2 --send 'busybox wc -lc < /dev/mtd0ro' --seconds 45` | `␣␣␣␣␣4422␣␣␣1245184` — **byte-identical to `M-b2`** | **53** | a different line count with the byte count right → the read path is not deterministic across power cycles, which is a bigger finding than anything else on this card |
| **X-c2** | `CAP --out bench/2026-08-31b/X-c2 --send 'busybox wc -lc < /dev/mtd1ro' --seconds 100` | `␣␣␣␣␣7943␣␣␣2949120` — **byte-identical to `M-c2`** | **53** | as above |

**Byte count** by the framing model block 3b §2 states and that `M-b`, `M-d`,
`M-b2` and `M-c2` have now each confirmed: 28 + 2 + 19 + 2 + 2 = **53**.

## §3 The rate prediction, stated so it can be wrong

推, from block 3b's two points: the gap in each `.timing` gives
**1.30–1.45 s** for `mtd0` and **2.85–3.10 s** for `mtd1`.

**Refuted by** either gap falling outside its band. That would mean the rate is
not a property of the path but of the boot — and the honest reading then is that
block 3b's figure is one sample of something variable, not a measurement of the
SPI read.

⚠️ **The band is 推 and it is drawn from n=1.** It is written down so that
"within expectation" is decided before the number is seen, not after.

## §4 Cells, in order

```cells
bench/2026-08-31b/X-b2
bench/2026-08-31b/X-c2
```

**Two cells.**
