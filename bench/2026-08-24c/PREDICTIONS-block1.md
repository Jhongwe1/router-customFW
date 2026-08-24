# PREDICTIONS — block 1: `§F`, the two cells that can end a visit

**Written before `PHYR 5 2` was sent.** Same power cycle as blocks 0 and 0b,
same instrument (`console-capture.py` 1.2). `§F` writes nothing to memory or
flash — both cells are PHY **reads** — but `F1` is the only cell in either
session that can leave the board unable to answer.

## The risk, restated with what today measured

`phy_read()` at `0x80402F80` spins on `MDCIOSR` bit 31 with **`bltz v1` and no
timeout and no iteration bound**. Three sources agree on the register
(disassembly, datasheet Tables 57–59, the SDK header), and a **fourth** agrees on
the unbounded wait: the vendor bootcode's own
`rtl8651_getAsicEthernetPHYReg()` is `do { status = READ_MEM32(MDCIOSR); } while
((status & STATUS) != 0);`. **That does not make `F1` safer — it establishes that
nobody in the vendor's chain ever bounded it.**

**Why the risk is accepted, and it is an argument about the register's role, not
about nerve.** `MDCIOSR` bit 31 is the *controller's* completion flag, not the
PHY's acknowledgement: an MDIO master clocks out its 64 bits and latches whatever
the line holds, so an absent PHY should yield `0xFFFF` from a bus pulled high
rather than a transaction that never finishes. *Inferred from the register's
role, pending this measurement* — the datasheet's Table 58 does not say what the
bit does when nothing answers.

**The positive control is measured and it is four cells deep.** `E12b`–`E12e`
had this MDIO controller complete transactions on addresses **0 and 1** across
**four registers** minutes before `§F`. So a hang at address 5 is attributable to
address 5 alone, and not to the controller, the bus, or the command.

**What a hang costs today, stated before it happens.** One power cycle, catching
the prompt again, and re-running the arm — about three minutes. *Not* the visit:
`§G` costs two power cycles of its own and the operator is at the bench. The
sheet's "the visit is over" was written when nothing sat behind `§F` and no
power cycle was budgeted.

**A cheaper bound was looked for and does not exist.** Arming the watchdog
(`EW B800311C 240000`) before `PHYR 5 2` would turn a hang into a reset, but the
longest `OVSEL` setting is **84.1 ms** undivided / **1.177 s** through `CDBR`,
and two captures are seconds apart because each opens and closes the port. It
would need a second `--send` line in the instrument, and changing the instrument
on the day of the run is how this project has already lost cells. Recorded as a
negative result rather than left as an unasked question.

## Cells

```cells
bench/2026-08-24c/F1
bench/2026-08-24c/F2
```

### F1 — `--send 'PHYR 5 2' --seconds 10`

| outcome | reading | verdict |
|---|---|---|
| **returns** | **87 bytes exactly** — `PHYR 5 2\n\rPHYID=0x00000005, regID=0x00000002 ,Find PHY Chip! UID=0x0000ffff\r\n\r<RealTek>`. `0x0000ffff` expected; `0x00000000` is the other acceptable value | 🔴 **the inference above is confirmed on silicon.** An MDIO read of an unpopulated address completes. `MDIOR` becomes safe to run on this part, and `F2` is licensed |
| **hangs** | the echo `PHYR 5 2\n` and **nothing else** — no `Find PHY Chip!` line, no prompt, capture ends on `--seconds 10 elapsed` | 🔴 **the finding is that `MDIOR` must never be run on this part**, and `F2` is cancelled permanently rather than deferred. Recovery is a power cycle |
| **returns something else** | any `UID` other than `ffff`/`0000` | 🔴 **a sixth PHY answers**, and `docs/loader-phy-and-switch.md` §6's port map is incomplete. `NET-07` and `C-18` both change |

**87 bytes is a prediction, not a description.** `E12b` (`PHYR 1 5`) and `E12e`
(`PHYR 0 5`) are both **87 bytes** for an 8-character command, and this command
is also 8 characters. A different byte count with a plausible-looking line means
the reply shape is not what those two captures established.

**The `%x` padding is already settled**: `E4`'s rendering was `UID=0x0000001c`,
eight digits, so the expectation above is the loader's actual format and not
mine. `E4`'s cell got this wrong in the other direction — it predicted the
values correctly and the *rendering* wrongly.

### F2 — `--send 'MDIOR 2' --seconds 30`, **only if `F1` returned**

**Arity trap, and it is the reason this line is `MDIOR 2` and not `MDIOR 5 2`.**
The handler at `0x80409C54` reads `argv[0]` only, parses it **base 10**, uses it
as the *register*, and sweeps the PHY address itself 0…31. Its own help string
says `MDIOR <phyid> <reg>` and is wrong. **A**-only: `MDIOR`/`MDIOW` are not in
any vendor tree here — the only `MDIOR` in the vendor sources is
`SlvPCIe_MDIORead` in `test_slvpcie.c`, **a PCIe slave-port command that happens
to share the name**, and reading it to predict this one would give a confident
wrong answer.

| | prediction |
|---|---|
| lines | **32**, one per PHY address 0…31, all at register 2 |
| addresses 0–4 | `0x001c` — `E4`, `E7` and `E8`'s measured value, on five addresses |
| addresses 5–31 | **whatever `F1` returned**, and that is the point of running `F1` first |
| rendering | `PhyID=0x%02x Reg=%02d Data =0x%04x` — **read out of the disassembly and never seen on silicon.** The byte count is deliberately **not** predicted: `%02x` here against `%x` in `PHYR` is exactly the kind of claim this cell can confirm or refute |
| duration | 32 × the unconditional 10 ms erratum delay = **0.32 s** minimum, plus ~32 lines at 38400. Well under a second; `--seconds 30` is slack, not an estimate |

**Its own refutation is built in**: *all 32 lines identical and plausible* means
the bus is echoing and nothing was measured. `E9b` gives the within-boot
comparison basis that makes "identical" checkable against a reading taken on this
same power cycle rather than a previous one.

🔴 **`F2` carries `F1`'s risk 27 more times** — one unbounded `phy_read` per
address 5…31. `F1` returning is what licenses it, and if `F1` hangs this cell
does not run today or ever.
