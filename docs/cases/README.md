# Debugging cases

Five defects, each told from its dated record, and from the record written while it was open
where one survives. Every page has six sections, in this order: symptom; first hypothesis, and
why it was wrong; the single-variable cut; cause; positive control; the check left behind. A page
links the [`SPEC.md`](../../SPEC.md) rows, `bench/` captures, notes and log entries that own its
facts and holds no number they do not; where it relies on the Chinese-language log or `SPEC.md`,
it translates them. Marks: 量 measured on the device, 讀 read out of code or a dump, 推 inferred.

| case | gate or row | first hypothesis read from | check left behind |
|---|---|---|---|
| [`rlx0`'s transmit loss was a descriptor length](tx-descriptor-length.md) | `R6b` | the seating's corrections file and log entry, 2026-09-23 | `nic15check` `K22`, run by CI |
| [The 98.9 % coverage that counted zeros](h601-coverage.md) | `FLS-22` | none survives | none for the measurement |
| [The I-cache handing back stale bytes](icache-stale-bytes.md) | `R1g-4a` | the log entry of 2026-08-23, the gate's stop-loss and the run sheet | none that CI exercises |
| [Booted from flash, `rlx0` received nothing](flash-boot-no-rx.md) | `R6c` | none in the repository; a session script outside it, before the cold boot | `mdiocheck` `K48`, run by CI; nothing checks that PID 1 types the verb |
| [The phase-B script's two latent defects](phase-b-script.md) | `v1.0` | none about the failure; the 130th segment's entry for the belief that phase B was rehearsed | none |

**What these pages do not establish**: that these five are the most instructive defects in the
record; anything new about the device — no page carries a new measurement.
