# Block 3b — the console outage left the loader's line buffer in an unknown state

Written after `CONT` returned no data line, before anything else is sent.
`PREDICTIONS-block3.md` is not edited: it recorded what `CONT` was expected to
do, and it is left as it was.

```cells
bench/2026-08-24b/flush-cont
bench/2026-08-24b/CONT2
```

## What `CONT` did and did not establish

*Measured, `bench/2026-08-24b/CONT.log`, 24 bytes:*
`DW 8040DCE8 1` + `\n\r` + `<RealTek>` — the echo and a fresh prompt, **and no
data line**. That is the shape `B8` produced (`DW 8040DBC0 A`), where the length
argument parsed to zero and `DW` printed nothing.

**Established**: the reply is `<RealTek>`. Nothing was streaming ESC across the
outage, so a board that had reset would have run past its ESC window and booted
the vendor kernel, and the console would carry Linux output rather than a loader
prompt. *The board is at the loader prompt.* What is not yet established is
whether it is the **same** prompt — that is what `CONT` was for and it did not
deliver it.

**Not established, and not to be recorded as a board finding**: why `DW` printed
nothing. The candidate is the console outage itself. A USB-serial adapter that is
unplugged and replugged does not leave its TX line clean; whatever the board's
UART received during that window was echoed into no capture and may still be
sitting in the loader's 128-byte `readline` buffer, shifting this command's
tokens. This repository has already paid for that mechanism once — `A0`'s first
attempt, `SPEC.md` `LDR-16` — and the standing response is a bare CR.

## `flush-cont` — `--send ''`

- **Predicted**: `Unknown command !` then `<RealTek>`, ~31 bytes, the shape of
  `bench/2026-08-24b/flush.log`. That would **confirm** residue and explain
  `CONT` completely.
- **Refuted by**: a bare prompt and nothing else. Then the buffer was empty,
  `CONT`'s silence has no explanation yet, and the next thing to suspect is the
  command itself rather than the buffer.

## `CONT2` — `DW 8040DCE8 1`, the same cell again on a clean buffer

Prediction is the same formula `PREDICTIONS-block3.md` wrote, restated here so
this file stands alone:

- **Predicted**: 71 bytes; words 2–4 = `001E8000 0ED80000 8040A2B4`; and
  `tick = (mtime(CONT2.log) − 03:32:51.703) × 100.0078` to within **±5 counts**.
- **Refuted by — the outcome that ends this power cycle**: a tick far below the
  prediction, i.e. the counter restarted. The board reset at some point during
  the outage and stopped at the prompt for a reason nothing here predicts, every
  DRAM-resident thing about this boot is gone, and `bench/` needs a new directory.
- **Refuted by**: still no data line. Then the residue explanation is wrong even
  after a flush, and the next step is `DW 8040DCE8 4` — if a length of 4 prints
  while a length of 1 does not, the argument is arriving mangled rather than the
  address; if neither prints, it is not the argument.
