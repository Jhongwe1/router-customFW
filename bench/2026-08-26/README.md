# bench/2026-08-26/ — a prediction with no run, and it is expected to stay that way

**Nothing in this directory is device output, and nothing ever will be.** It
holds one file: `PREDICTIONS-b4-block0.md`, written at the desk at 06:09 on
2026-08-25 and committed in `857d790` at 06:15, hours before power. It predicts
nine cells — `A-catch`, `A0`, `H0a`, `H0a2`, `H0a3`, `H0b`, `H0c`, `H0d-a`,
`H0d-b` — with capture paths under `bench/2026-08-26/`, because the seating it
was written for was planned for the 26th.

**The seating happened early, not late.** All nine cells ran on **2026-08-25**,
in `bench/2026-08-25/`, against a re-homed copy of this file — verbatim except
for the nine paths and one instrument-version correction, which is marked inside
that copy. `bench/README.md` § 2026-08-25 owns that description.

## The red is expected, and this file is what says so

```
$ python3 tools/check-predictions.py bench/2026-08-26/PREDICTIONS-b4-block0.md
  FAIL  bench/2026-08-26/A-catch    no capture -- a predicted cell that never ran is not a pass
  … nine of these …
  0 of 9 captures came after the prediction, 9 did not
$ echo $?
1
```

**量 2026-08-25.** That is the correct behaviour of `N2`, the tool's own control
for *a predicted cell with no capture*, and it will report it forever, because
the nine paths it names will never exist. It is written down here rather than
left for a reader to hit, because a control that goes red for a reason nobody
recorded is a control that gets waved through the second time.

**The file is not edited and not moved.** Editing it moves its mtime and breaks
the one property it exists to carry; moving it would make `bench/README.md`'s
pointer to *the sealed original* point at nothing. `check-predictions.py`'s own
docstring is the rule: *corrections go in a new file.*

## No capture may ever be written into this directory

Not tonight and not later. If a capture landed here, three of the sealed file's
nine cells — `A-catch`, `A0`, `H0d-b` — would go from `FAIL` to `ok`, because
their predicted values are power-cycle invariant and would match a run the file
was not written for. **A prediction file that passes on three cells out of nine
is worse than one that fails on all nine**, because the three passes look like
evidence. It is the defect class that produced `D2c` and `E10d`: an expected
value taken from the wrong power cycle.

The second seating (`R1g-4b`) is `bench/2026-08-25b/`, under `bench/README.md`'s
one-directory-per-power-cycle rule and the `2026-08-24` / `24b` / `24c` …
precedent.

## The rule the sealed file could not write about itself

It says:

> **If the seating slips past 2026-08-26, this file is not edited**; a new block
> is written for the new directory. That is the same rule, applied to itself.

That covers **later** and not **earlier**, and the seating went earlier. The rule
generalises, and the general form belongs here because the file that needs it
cannot be edited:

> A prediction block is bound to a directory; a directory is bound to one power
> cycle. **If the run happens on any power cycle other than the one the
> directory names — earlier, later, or a different unit — the file is neither
> edited nor moved.** A new block is written for the directory the run actually
> uses, and the orphaned directory records that it holds a prediction with no
> run.

## What is not fixed, and it is bigger than this directory

🔴 **Nothing automated ever runs `check-predictions.py`.** It is not in
`.github/workflows/ci.yml`, it is not a row in `tools/ci-expected.tsv`, and
`tools/ci-census.py` does not know it exists — 量 2026-08-25. CI runs
`audit-bench-log.py` over `bench/**/*.log` and nothing else touches `bench/`.

So the tool that enforces `RUNSHEET.md` house rule 2 — *a cell whose expectation
is written afterwards illustrates; it cannot refute* — is invoked by hand, one
block at a time, at the bench. Eleven prediction files now exist across `bench/`
and no single run has ever covered all of them.

**Wiring it in is desk work and it is not free**: a sweep over
`bench/**/PREDICTIONS-*.md` goes red on this directory on its first run, so the
exception has to be a row in `ci-expected.tsv` with a written reason — the shape
that file exists for, and the shape `bench/README.md` demands when it says *a
hit that is waved through without a written reason is a scanner that has been
turned off one value at a time.* Cost **猜, uncalibrated: ½–1 desk segment**, and
it reduces bench risk by zero.
