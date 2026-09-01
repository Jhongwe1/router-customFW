# The development loop — what one iteration costs

## 0. What this file owns

`R4-0`. **The cost of one `edit → result` iteration, stage by stage, with
machine time and human time in separate columns.** `SPEC.md` indexes the
numbers; this file owns them and owns the method that produced them.

It does not own: the boot itself (`SPEC.md` `FW-27`/`FW-32`, `notes/` boot
ladder), the build's reproducibility (`notes/reproducible-build.md`), or the
scripted reset that `R4-1`/`R4-2` will measure.

**§1–§3 were written and committed BEFORE any measurement in this file was
taken.** That is not a claim about my discipline; it is checkable —
`git log --follow notes/dev-loop.md` shows a first commit holding the
predictions and no numbers, and a later one holding the numbers. This
project's `check-predictions.py` proves the same ordering for bench captures
by mtime and cannot be used here, because the quantities are desk timings and
not captures.

---

## 1. The loop as it exists on 2026-09-01

### 1.1 The seven stages

An `R5` iteration — the loop this gate exists to make fast — is a change to a
**kernel** source file. That is the loop measured here. A userspace-only
iteration is a different loop and is noted where it differs.

| # | stage | performed by | what an instrument can see |
|---|---|---|---|
| S1 | edit a kernel source file | me, at the desk | nothing. No instrument in this repository times an edit |
| S2 | stage a tree and build it — `tools/rlxfw-kbuild.sh` | machine | its own stdout, one line per phase |
| S3 | assemble the image — `tools/rtkimage.py build` | machine | its own stdout |
| S4 | power the board and catch the ESC window to `<RealTek>` | operator, physically | the capture that was opened before power |
| S5 | TFTP the image to `0x80500000` | machine | `bench/*/*-put.json`, field `seconds` |
| S6 | `J 80500000` | machine, one line typed | the capture |
| S7 | first useful output — the boot text and a shell prompt | machine | `.timing` against `.log` |
| S8 | the result reaches the desk — paste-back and read | operator + me | the gap between one capture ending and the next starting |

**S8 is a stage and it is the one the plan's `< 90 s` never named.** It is in
the list because the loop is not closed until the person who made the edit
knows what the board printed.

### 1.2 Two definitions of "the loop", and they do not give the same number

Written here before either is measured, so that the answer cannot be chosen
after the fact:

* **the machine pipeline** — S2 + S3 + S5 + S7. Every second of it is a
  machine working and a human waiting. This is the quantity `< 90 s` reads
  most naturally as being about.
* **the turnaround** — S1 through S8 as actually served, including the
  operator's hands and the paste-back. This is the quantity that decides how
  many `R5` iterations fit in a day.

A gate that meets the first and not the second has bought nothing. `R4`'s DoD
`D4` names one number and does not say which, and that is a defect in `D4`
found before it was measured against.

### 1.3 What is not in the loop, deliberately

The **wait for a seating to be scheduled** — the loop's largest term by two
orders of magnitude, because the operator and the board are not at the desk
continuously. It is excluded because no engineering change to this repository
moves it, and including it would make every other number invisible. It is
named here so that its exclusion is a decision and not an oversight.

---

## 2. Predictions, written before the measurement

Each has a two-sided refutation condition. A prediction that can only come out
one way is not a prediction.

| id | claim | refuted by |
|---|---|---|
| **P1** | the build total (`rlxfw-kbuild.sh`, `-j4`, today's recipe: `--marks`, declared cflags, declared stamp) is **45–60 s** | a total below 45 s or above 60 s |
| **P2** | the 480 MB stage copy is **5–15 s** and **under 30 %** of the build total | outside that range, or 30 % or more |
| **P3** | `-j8` cuts the build total by **15–32 %** against `-j4` | `-j8` not faster, or faster by more than 40 % |
| **P4** | image assembly (`rtkimage.py build`) is **5–25 s** | outside that range |
| **P5** | the machine pipeline at `-j4` totals **65–95 s** — so `D4`'s 90 s is borderline, not comfortable | below 65 s or above 95 s |
| **P6a** | the gaps inside a seating are **bimodal** — a scripted mode of a few seconds and a human mode of minutes — and the human mode holds **more than 70 %** of the seating's dead time in **fewer than 30 %** of the gaps | a unimodal distribution, taken as max ÷ median below 10 |
| **P6b** | a seating's dead time is **more than 2×** the sum of its capture durations | 2× or less |
| **P7** | NFS root is **not** on this gate's critical path: the upload it removes is **under 3 %** of the machine total, and **0 %** for a kernel change | the upload is more than 10 % of the machine total |
| **P8** | the step list's own stated risk holds — the build is **more than 60 %** of the machine pipeline | 50 % or less |

**P1's basis**, so the reader can see it is arithmetic and not a feeling:
`r3-9/determinism.log` holds `rep4` at 49 s and `rep8` at 40 s, both `-j4`/`-j8`
of the same `.config`; `r3-9/driver.log` holds `quietmc` at 51 s (`-j4`,
`--marks`) and `loudmc` at 61 s; `build2.log` holds `quietmc` at 36 s and
`loudmc` at 51 s, both `-j8` with `-fno-if-conversion`. Six cells, two `-j`
settings, and none of them decomposed into phases — which is the whole reason
this step exists.

---

## 3. Method

**The desk half is run today; the bench half is read out of captures already on
disk.** A stage that neither can reach is recorded **unmeasured**, never
estimated — the step list says so and this is where it binds.

* **S2, S3** — run on this host, `n` ≥ 2 per configuration, each phase boundary
  taken from the driver's own stdout with a timestamp attached per line as it
  arrives. The driver is not modified: it already prints one line per phase,
  and timing its output is a measurement of the tool as it is rather than of a
  tool changed to be measurable.
* **S4, S5, S6, S7** — read out of `bench/`. These are 量 on the device, with
  the seating and the capture named for every number. They are not re-run:
  re-running them costs the most expensive unit this project has.
* **S8** — derived by `tools/looptime.py` from every capture's
  `.meta.json`: `started_wallclock` and `duration_s` give, for consecutive
  captures, the dead time between them. **Ordered by wall clock, not by
  filename**, because the two differ.

### 3.1 What the S8 instrument cannot see

Named before it is run, because a gap is a residual and a residual absorbs
everything nobody named:

1. it cannot separate *the operator reading and pasting* from *me writing the
   next command*; it measures their sum;
2. a gap that spans a break — the operator leaving the bench — is
   indistinguishable from a long round trip, and will be reported as an
   outlier rather than silently averaged in;
3. it sees only captures. A command that produced no capture, and the whole of
   S4, are outside it.
