# Method

How a claim about this device is made and checked here: the marks a sentence
carries, how many sources a register value needs, the refutation written first,
the controls every instrument carries, why the ISA is measured only on bare
metal, how the work is cut into gates and steps, the three ways of not doing
something, and how pages quote the plan, which is not published. The rules are
[`CLAUDE.md`](../CLAUDE.md)'s, and where this page differs from it, `CLAUDE.md`
wins; this page is the reader's version, written 2026-10-17, with the plan's
bare-metal rules (`D14`, `D15`) and its three categories (its § 17) translated.

## Marks

Every sentence about the machine says how it is known: **量** measured on this
unit, **讀** read out of code or a dump, **推** inferred and waiting for a
measurement — never blended in one sentence. **未定** marks an open value, which
needs a row saying what settles it; **殘留** is the question left once a value is
settled. `SPEC.md` adds **文**, read in a document and never enough on its own,
and **算**, arithmetic on values already held; [`spec/README.md`](spec/README.md)
defines the alphabet and the source letters. Every result also states what it
does not establish.

## Two sources

No register value enters code on one source: two of the datasheet, an SDK header
and a `devmem` reading on this unit must agree, or the value is recorded as
undetermined. The datasheet carries four limitations, cited with it every time:
it is a draft (Rev D1.1, 2013-07-17); it is marked confidential and reached this
project through a third-party mirror, so it is cited and never committed; it
describes the `-VE1/2/3` variants with embedded DRAM, which this unit is not; and
its CPU claims contradict the common account of this core. Before reasoning from
vendor source, the file is confirmed to be in the tree that builds.

## A refutation condition first

Nothing counts as a result until the condition that would refute it was written
before the result was seen. A threshold is never widened to make a result pass;
the experiment changes instead. Bench predictions are written before power and
re-derived from the card's own arithmetic
([ADR-010](decisions/ADR-010-bench-card-predictions.md)).

## Controls

A tool reporting 0 is making a claim. Every sweep, flag and watcher carries a
positive control — a case it must catch — and a check that it ran at all; a guard
is shown permitting as well as refusing. A green suite is a claim about its
controls, and a mutation run is what tests them. A recurring rule becomes a tool
refusal rather than a habit; [`tools/README.md`](../tools/README.md) lists the
tools by class.

## Codegen and the ISA: bare metal only

A model more permissive than the device certifies exactly the bugs the device
rejects. The plan's five rules (`D14`, its fourth and fifth versions):

1. A test that passes on the host, in qemu or under the vendor kernel is no
   evidence that codegen or the ISA is right.
2. Every change of toolchain or `-march` reruns the toolchain's silicon test.
3. Hand-written assembly is written under `.set noreorder` with every delay slot
   filled by hand, and `hazlint` scans every object that goes to the device, not
   only the hand-written ones: whether compiler output carries the hazard
   depends on a flag in the Lexra patch, `flag_fix_bdsl`, that nothing else checks.
4. A claim that this CPU supports an instruction points at a bare-metal
   measurement, never at an observation under Linux.
5. No trap is not evidence of support: a reserved encoding can execute as a
   `nop` or as something else, so a claim of support points at a known answer
   computed correctly.

Why bare metal (`D15`): MIPS Linux can emulate instructions in its
reserved-instruction handler — `ll` and `sc`, a whole FPU, unaligned accesses —
so a census under Linux can report what the kernel supplies rather than what the
core has. 讀 this vendor kernel emulates `ll` and `sc`, and `sync` as a no-op, and
emulates neither the FPU nor `rdhwr` (`CPU-47`). The bare-metal harness reads
each instruction three ways: the right answer (present), a trap with its
`ExcCode` (absent), or no trap and a wrong answer — the dangerous cell, given its
own positive control: an encoding certain not to exist, fed to both checks. Run
again under the vendor kernel, the difference between the columns is the
kernel's emulation surface. Measured:
[`rlx-isa.md`](rlx-isa.md), [`isa-payload.md`](isa-payload.md); `CPU-55` is the
third cell firing, `rotr` decoded as `srl`. The plan's `D1` left the toolchain to
the silicon in the same way: three candidates, measured side by side in
[`toolchain-comparison.md`](toolchain-comparison.md); the code-generation
constraints that follow are [ADR-005](decisions/ADR-005-codegen-constraints.md).

## Gates, steps and seatings

Work is cut into gates, and each gate is a legitimate place to stop
([`charter.md`](charter.md)). A gate's step list gives each step what it
produces, a definition of done written before the work, where it is most likely
to be wrong, and a stop-loss. Closed gates' lists are `history/steps-*.md`; their
results are [`GATE-RESULTS.md`](GATE-RESULTS.md).

At the bench, what cannot be repeated is the loader's prompt: `J` destroys it,
so everything asked there — register reads, TFTP, `FLR`, bare-metal payloads —
is asked before the jump, once, and a power cycle is the costly unit. So a
seating has cold cells, at the prompt, which need a card frozen before power, and
hot cells, after Linux is up — change, build, boot through `looprun`, read
`/proc`, reset by the watchdog — whose assertions are compiled into the image and
compared by a tool, so they need no card. One card per power cycle, not one per
experiment (the plan's ruling of 2026-09-16).

## Deliberately not done

What is not done is recorded in one of three categories, never collapsed:
collapsing them is how *chose not to* becomes *could not*, the flattering way.
The numbers are the plan's, and records cite them.

- **Voluntarily out of scope.** 1: wireless transmit experiments of the
  beacon-injection kind — a beacon is a broadcast, and a malformed one reaches
  every device in range. 2: any test on a device that is not this project's own.
  3: tradecraft — persistence, anti-forensics, lateral movement — which no gate
  needs.
- **Blocked on an instrument** — it would produce a checkable fact, and cannot
  be done now. 4: the flash's JEDEC ID, removed in the plan's fourth version,
  since `R5b`'s MTD driver reads it at probe. 5: an independent second
  instrument for the flash dump, released by either of two conditions — rlxfw's
  own MTD driver reading 4 MiB whose sha256 equals the dump's, a read path
  independent of the loader's `FLR` and free, since it is already `R5b`'s
  acceptance condition; or a 3.3 V programmer. Its state is
  [`notes/power-and-programmer.md`](../notes/power-and-programmer.md) § 4, and
  the driver's read differs from the dump (`FLS-26`). 6: EJTAG. 8: a second
  unit — a measurement on one device is an observation, and two begin to be a
  pattern.
- **Traded away** — the preconditions hold, and the cost does not pay. Among
  them: generating the image with OpenWrt or Buildroot, which does exactly the
  part this project exists to do; a WiFi driver of its own; a byte-identical
  rebuild of the vendor image; and a first-stage loader of its own
  ([`flash.md`](flash.md)).

## Quoting the plan

The project's planning documents are private and have no version history
([`charter.md`](charter.md), *What this page does not establish*), so nothing
they say can be checked from this repository, and no date they carry is a
commit's. The parts the repository applies are published as pages:
[`charter.md`](charter.md), [`flash.md`](flash.md) and this page. Elsewhere, a
page that relies on the plan's words quotes them where it relies on them and
says the plan is unpublished: the quote is the only copy here, and its date is
the plan's own. Where a committed record quoted the same words earlier, the page
cites that record as well, since its commit date is the only date that can be
checked.

## What this page does not establish

- **That the rules were followed.** Each record states what it measured and what
  it did not; a rule is enforced only where a tool refuses.
- **That bare-metal results generalise.** Every measurement is on one unit, and a
  second unit is item 8 above.
