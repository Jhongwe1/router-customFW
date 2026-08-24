# PREDICTIONS — block 9b: verifying the poison before relying on it

**Written before the first poison write.** Adds three cells to block 9.

## Why

Block 9 listed `G5-poison1/2/3` (the writes) and `G5-rb1/2/3` (the readbacks
**after** the second upload). It did not list a read **between** them.

🔴 **Without one, `G5` has the defect `D0a`/`D0b` had this morning.** A silent
`EW` is indistinguishable from a refused one, so *"`5A5A5A5A` is gone and the
dump's bytes are there"* cannot be told from *"the poison never landed and the
dump's bytes were there the whole time"* — and `G1` established that they **were**
there the whole time, which is exactly why the poison exists. The cell would pass
without a single packet arriving.

Same repair as `D0-rb`: read it back.

```cells
bench/2026-08-24d/G5-pv1
bench/2026-08-24d/G5-pv2
bench/2026-08-24d/G5-pv3
```

| | command | prediction |
|---|---|---|
| **G5-pv1** | `DW 80500000 1` | `5A5A5A5A 00008021 40906000 00000000` |
| **G5-pv2** | `DW 80580000 1` | `5A5A5A5A 08ABB9AE 978855A8 E63174AD` |
| **G5-pv3** | `DW 805F0FF0 1` | `5A5A5A5A 00000000 00000000 00000000` |

**Word 1 only.** `EW <addr> <one value>` writes exactly one word — established
today by `D0a2`/`D0a2-rb`, where `F00DFACE` landed in word 1 and `CAFEBABE`
survived untouched in word 2. So words 2–4 must still hold the staged image's
own bytes, and they are the in-place control that the poison hit the address it
was given and nothing either side of it.

**If word 1 is not `5A5A5A5A`** the poison did not land, and `G5` must not
proceed — a readback after the upload would then be meaningless in the
most convincing possible way.
