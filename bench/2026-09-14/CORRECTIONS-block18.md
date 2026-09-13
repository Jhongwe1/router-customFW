# Corrections to block 18

**Written 2026-09-14 after the seating, sixty-fifth segment.** The card
`PREDICTIONS-B19-block18.md` is frozen and is not edited: `check-predictions`
reads its mtime and a repair would destroy the evidence for all twelve cells.
Everything that was wrong about it is here.

**The seating itself**: one power cycle against a budget of one, 12 carded cells
+ 4 declared off-card, `check-predictions` **12 of 12**, `capdate` **OK, 14
captures, all 2026-09-14**, `flashwin scan` **CLEAN** over 47 files with its
positive control firing.

---

## 0. Two field predictions in § 4.2 were refuted, and both are the same mistake

| field | card said | device read | what it actually is |
|---|---|---|---|
| `install.words` (probe4) | `00000019` | **`00000016`** | 22, not 25 |
| `ran` (probe4) | `0000004b` | **`00000021`** | 33, and `trapped` is `2a` = 42 |

**① `install.words`: the number was carried across from a different payload's
different build.** `00000019` is 25, and 25 is what
`qemu/2026-09-13/probe5.txt` printed — a **probe5** capture from a **qemu**
build. probe4 on the device installs **22** words. Both payloads read `16` on
this device, and the qemu builds read `19`, because `RET_ERET=1` under
`qemu-run.sh` lengthens the handler. So the field is a build property exactly as
the card said, and the card then quoted the wrong build.

🔴 **This is segment 62's headline one file over.** That segment's result was
*量一張已提交的表時,發現那張表沒說它是用哪一支二進位量的* — measuring a
committed table and finding it never said which binary it was measured on. Here
a card's field prediction did not say which capture it came from, and it came
from the wrong one. **The repair is not "add a `cardnum` row"** — a device field
cannot be re-derived at the desk, which is the whole reason it is a prediction.
The repair is that **a field prediction copied from another capture must name
that capture in the row**, so the reader can see it is a cross-payload quote
rather than a derivation.

**② `ran`: predicted from the field's NAME instead of from its definition.**
`probe4.c:98` says it outright:

```c
#define H_RAN		22u	/* rows with n == 0                           */
```

So `ran` counts the rows that did **not** take an exception, and
`ran + trapped == rows` is the identity: **33 + 42 = 75**. ✓ The card read
`ran` as *rows that ran* and predicted all 75. **The definition was one line
away in the file the card was written beside.**

⚠️ **`cardcheck numbers` passed 45 of 45 and could not have caught either.**
Both are prose inside a markdown table cell, and `cardnum` only re-derives rows
in its own fence. That is `docs/FINDINGS.md:29`'s recorded limit — *a prediction
that no `cardnum` row can re-derive is a number nothing checks until the board
contradicts it* — **firing twice in one seating.**

🟢 **What the two refutations cost: nothing.** Neither is a guard, neither
gates an upload, and neither changes a verdict. `install.words` is a build
property and `ran` is an identity that holds. They are recorded because the
record of being wrong stays in place.

---

## 1. `epc.end` was refuted, and that one IS the result

The card predicted `epc.end = 5a5a5a50`, *identical to qemu*. The device read
**`80500270`**, and § 5.2's own prediction table is where that went wrong — it
carried qemu's value across on the argument that the field is `c0_d2`'s
`EPC_NEW`.

**That prediction failing is the finding**, not an error in the card: it is the
observable that says `mtc0 $x, $14` does not write CP0 14 on this die. Five
reads of the same value (three rows' `out_gpr`, the same three rows' `out_aux`,
and this header field), one identified source for it, and all three alternatives
closed inside the artefact. The owner is `docs/isa-hazard.md`.

⚠️ **What the card DID get right about this family, and it matters**: § 5.2
re-confirmed the containment argument rather than inheriting it — *a trap during
a `c0_*` cell overwrites EPC in hardware and the handler reads the hardware
value, so the cell's writes cannot mislead the handler*. Nothing trapped
(`trapped=00000000`, and all three rows carry `n=0 cause=0`), so the safety half
of § 7.4's reasoning held. **Only its measurability half — *the only full-width
read-**write** CP0 register* — is refuted.**

---

## 2. Two `cardnum` rows were wrong before the freeze, and one of them could never have been right

Recorded in the card itself at § 10.1, because it was caught and fixed **before**
the freezing commit. Repeated here so a reader of the corrections sees it:
`expansion-cold` matched its own row, and `no-autoexec` matched its own row
*and* § 3's prose — and § 3 has to name `nfjrom` and `boot.img` to say why they
are dangerous, so **that row could never have read 0 as written.** Both are
anchored at `^/usr/bin/python3` now.

**The rule that comes out of it: a guard row that names a forbidden string
cannot be written as a bare search for it.**

---

## 3. The off-card cells, declared by name

`X1-P4-rescue.json`, `X1-P4j`, `X1-P5-rescue.json`, `X1-P5j` — a second
execution of both payloads on the same power cycle, re-uploaded because the
watchdog bite re-staged `0x80500000` from flash.

They are **not** in the card's twelve-cell fence and were never going to be:
the card was frozen before the first round's result existed, and the claim they
test — *these readings reproduce* — is one no cell on the card tests. Seating
18's precedent is the shape: an off-card cell is declared by name in the
write-up rather than folded into the fence afterwards, because folding it in
would mean editing a frozen card.

**Reading: 75 of 75 and 24 of 24 row lines byte-identical, and all 18 + 23
header fields identical.** The reason it was worth 45 s of board time is
`FW-53`: seating 17's conclusion about bits 19 and 20 was refuted by
non-reproducibility, so *one execution* is a known failure mode of this bench.

---

## 4. Three things the card got right that were not obvious

Recorded because a corrections file that only lists errors teaches the reader
that predictions are decorative.

1. **The report-length equality.** § 4.3 and § 5.2 predicted **7,368** and
   **2,974** bytes between `*** rlxprobe` and `rlxprobe: end\r\n`, derived as an
   equality with the committed qemu captures rather than from either payload's
   own per-row estimate — `probe4.c`'s `~68 bytes a row` is 33 % low and
   `probe5.c`'s `~88` is 4.6 % low. **Both hit exactly**, on two rounds each.
2. **The read-back count.** § 6 typed `641` and `233` where `make show` prints
   `633` and `225`, on `LDR-07`'s rounding and `probe2`'s recorded precedent.
   The replies were **7,593** and **2,799** bytes, exactly
   `tools/reply-size.py`'s prediction, and the eight margin words past each seal
   were **8 of 8 poison** — which the shorter count would have shown three of.
3. **`looprun` was kept off the payload path** on a desk measurement, not a
   preference. Its `S7` has no `--esc-after` and both payloads bite; the ESC
   window would have been missed and the vendor firmware would have booted,
   which is what cost seating 17 two of its three power cycles.

---

## 5. What did not happen

**Zero flash-write commands. Zero `FLR`. `H601` is not read.** Every `sent`
field in the seating is a `DW` of DRAM (`0x80A03000`, `0x80A04000`,
`0x80500000`) or of loader RAM (`0x8040D4A0`), a `J`, or `?`. The burn-flag word
read `00000000` before both uploads and before both off-card re-uploads. The
`FLS-26` ledger does not move: **proven identical 4,177,920 B (99.61 %), proven
different 8,192 B (0.195 %), undetermined 8,192 B (0.195 %)**.

⚠️ **And the forbidden sentence is not said.** `RUNSHEET` `§B3`'s `G8b` needs a
full re-dump hashed against `FLS-14`; this seating ran no `FLR` bracket at all.
