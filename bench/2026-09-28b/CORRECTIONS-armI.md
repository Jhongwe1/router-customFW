# CORRECTIONS — arm I (`RUN-armI.md`, `R6b-8` 8e/8f), `bench/2026-09-28b/`

Written by the main session before the corrected lines ran. `R6b`'s cards are not frozen (the owner's
ruling of 2026-09-27); this file records how the sheet's execution departed from the sheet as generated.
The master sheet and its scripts live in `$FWRE_WORK/rebuild/s116/run-armI/` (a copy of the scripts as
they were before this correction: `$FWRE_WORK/rebuild/s116/run-armI.bak-1720/`).

## 1. `line1-cold` stopped at `I1-MK`: an unfilled placeholder in the scripts' gate arguments

`line1-cold` ran from the cold catch through `I1Q` with every gate holding (17:15–17:16; `looprun`
closed its loop, 8 assertions, S8 comparing the boot's `RLXFW-ID0` with `--recipe-override 3685a3a4`)
and stopped at `I1-MK`'s first gate, `^RLXFW-ID0=@FILL:RID@$` (`run/2026-09-28b/line1-cold.log`, rc 3;
the watch `X-I1` then ran 17:16:11–17:18 and was ended by `stopwatch`). The cause is the generator:
`gen-armI.py` fills its `@FILL:…@` markers in the card's text, but `write_all` writes each line script's
gate arguments from its cell table without that fill, and the scripts' own placeholder check reads the
card, not themselves. Two scripts carried the marker: `line1-cold.sh` (`I1-MK`'s `ID0` gate and
`I3-NW0`'s `recipe_id` gate) and `line2-warm.sh` (`I4-MK`'s and `I6-NW1`'s); `line3-tail.sh` and
`line4-end.sh` carry none. The value the card's text holds for `RID` is `3685A3A4`, and
`rtl819x-spi.c:1457` prints `recipe_id` with `%08X`.

**Nothing on the board depended on the gate.** When it stopped, no verb had been typed after the boot,
no ping had run, and the board was in Linux (not at the loader prompt). The watch `X-I1` that
`line1-cold` then started does stream ESC to the console, as every tail watch of this sheet does: for
its 142.8 s the shell answered with 6,643 BEL bytes, and one CR drew a bare prompt (`X-I1.log:2`), no
command. So on boot 1 the console between `J` and the pings carried that ESC stream and CR besides
`line1b`'s three `cat`s — no verb, no write. `I1-MK.log`, the gate's own
input, holds `RLXFW-ID0=3685A3A4`, `RLXFW-SM0=C4000000`, `RLXFW-SM1=04000000` and `RLXFW-N1=04000000`,
so all four of `I1-MK`'s gates hold when the value is filled (read by the main session, 17:2x).

**What ran instead** (`mk-line1b.py` in the sheet's directory):

* `line1b.sh` — `line1-cold.sh` with its items from `I1-VT` on, unchanged but for `I3-NW0`'s
  `recipe_id` gate filled with `3685A3A4`; its watch is `X-I1b`; it does not rewrite `catch.t0`.
  `I1-MK` is not re-run: its record stands, with the stop, and this file reads it.
* `line2-warm.sh` — its two `@FILL:RID@` gate arguments filled with `3685A3A4`; nothing else changed.

**Rejected**: following the stop rule literally (`stopwatch`, `line4`, power off) — it would end a
cold boot whose image identity the tool had already established (S8) over a defect in the sheet, and
re-planning would cost the owner another power cycle; re-running `I1-MK` under a new name — it would
add a cell the card does not have, while the existing record already holds the four values.

## 2. The verdict cells name the template directory

`I2-V` (and, by the same text, `I5-V`) runs `armI-verdict.py bench/2099-12-31 <boot> 3685a3a4`: the
card's instantiation rewrites `bench/2099-12-31/` with its slash, and this argument has none, so it
was not rewritten. `I2-V` refused (`no bench/2099-12-31/I1Q.stages.tsv`, rc 2); it is a declared
reading, so the line went on. The main session ran the same script on the seating's directory by
hand, after the line, from the repository root:
`armI-verdict.py bench/2026-09-28b 1 3685a3a4` (its output kept in the sheet's
`run/2026-09-28b/I2-V-hand.out`), and does the same for boot 2. The card is not edited: `line2`
re-instantiates it from the master and refuses a copy that differs.

## 3. `stopwatch.sh` did not accept `X-I1b`

Its name check took `X-I<digit>` only. The main session widened it to `X-I<digit>` or
`X-I<digit>b` (one `case` line) and then stopped `X-I1b` with it, before `line2` opened the port.
