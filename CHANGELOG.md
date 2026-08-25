# Changelog

**Nothing has been built.** There is no kernel of mine, no image, and no byte of
mine has been written to this device's flash. What exists is the instruments, the
record, and the first thing that ran on the silicon — the vendor's own kernel,
delivered over the network.

Tags mark where the outside world can check the work, not where a feature landed.
`PROGRESS.md` is the only file that says where the work actually is.

---

## Unreleased

**`R1g-4b`'s desk half, 2026-08-25.** `probe2` is fixed against measured values
rather than read ones, and the suite that would have to tell a fixed payload from
a shipped one went from 66 cases to **106**.

- **`tools/rlxprobe/probe2`** — the five must-fix items from
  `docs/rlxprobe-audit-2026-08-25.md`. `SAFE_A0` before the one instruction in
  the tree guaranteed by design to fault; a 44-word read-back of the installed
  handler, so *the stores did not land* and *the core does not fetch there* stop
  being one hang; one binary instead of two indistinguishable ones; a primed
  destination on every CP0 read; and **no `mtc0` to CP0 register 12 anywhere in a
  device image**, which is what "it does not touch `Status.IsC`" looks like when
  it is a claim about the emitted words instead of about a comment.
- **The census reads every register twice, with two different prime families.**
  *Not written* becomes certain rather than likely, and **a register that changes
  between the two reads reports itself** — a second, independent route to `F50b`.
- **Four mutations, one per must-fix, run under qemu.** One of them exists
  because qemu cannot reach the state it tests: its `mfc0` always writes `rt`, so
  a payload with one census stub emitting `nop` is the only way to show that
  `S_NOWRITE` can be produced at all. The first qemu run of the fixed payload
  found a defect in the fix.
- **`tools/reply-size.py`** — `LDR-07`'s reply-length formula as an instrument.
  Twelve controls; the per-family constants fitted from the captures rather than
  counted by hand; **121 modelled, 0 unexplained** over `bench/`. The two
  captures that never fitted have names now instead of being misses.
- **`tools/boot-timeline.py`** — the named intervals of a boot, with the anchor
  bytes stated. It refutes `CLK-15`'s *"cold and warm are the same"*: the two
  populations do not overlap, and the difference survives **inside a single power
  cycle, twice**.
- `PROGRESS.md`'s `Est.` column is answered: 198 is not the plan's total, not its
  desk+bench, and not any consistent subset of it. No rule reproduces it.

## v0.0 — 2026-08-25

**The instruments and the record.** Fifteen tools, each with the controls that
show it can fail; three loader documents read to instruction level; one gate
closed on silicon; and, from today, something that runs them all on every push.

### What is established

| | |
|---|---|
| **`S0` closed 2026-08-23** | 3-2-1 encrypted backup plus a restore drill. Copy ③ downloaded and read back: 19/19 byte-identical, none missing, none extra, with a positive control that fired |
| **`R0` closed 2026-08-24** | **The vendor's kernel, delivered over TFTP and executed from RAM, reached userspace and answered ping 2/2 at 3.6 ms.** `G7.log` is byte-identical to `G6.log` as a whole file, 1789 bytes, same sha256; `G6` reproduces the pre-existing boot log byte-exactly from `decompressing kernel:` onward, 1687 of 1687 bytes |
| **No flash-write command was issued** | in any of the 81 captures across five power cycles. The flash evidence is **bounded and the wording matters**: the loader head and the `cr6c` image header are byte-identical across three kernel executions and two uploads, and that reaches **512 bytes of a 4,194,304-byte part**. It is not *"zero flash bytes written"*, and no instrument here can establish that |
| **`AUTOBURN` measured off at the burn path's own instruction** | `00000000` at `0x80401B9C` *during* the transfers, and `00000001` after the power cycle — which is the positive control on that ordering |

### What is not

Everything about the core itself. The instruction set, the pipeline hazards and
the CP0 registers are read out of binaries and vendor source; **nothing of mine
has executed a single instruction on this silicon.** That is `R1`, it is the
active gate, and it runs bare metal because Linux emulates the two rows the
toolchain decision rests on.

### In this tag

- **`docs/FINDINGS.md`** — one line per finding, ordered by the decision it
  changed. The map this repository's 400 KB of prose did not have.
- **`.github/workflows/ci.yml`** and **`tools/ci-census.py`** — the suites run on
  every push, and the census refuses a green build whose arithmetic does not
  close. It earned its keep on its first real input: 20 + 23 = 43 against a bench
  total of 45, so two cases had been vanishing out of `tools/test-rlxprobe.sh`
  with neither a `FAIL` nor a `skip` line. **88 cases run on a runner; 101 do
  not, and every one of the 101 is named on the build page** — they need a 56 KiB
  vendor bootloader that may not be redistributed.
- **`tools/rlxprobe/probe1`** — the `R1d` payload: six cells that decide, on
  silicon, which cache-management sequence makes this core see an instruction
  just written into RAM. Not yet run.
- **`tools/console-capture.py` 1.3** — `--esc-period`, and the period each
  capture *achieved* is now measured and recorded rather than assumed.
- `README.md` rewritten: the previous first screen said *"no claim in this
  repository has been observed on silicon"*, which stopped being true on
  2026-08-23.

### Corrections that landed with it

- 🔴 **The general exception vector on this core is `0x80000080`, not
  `0x80000180`.** The MIPS32 address had reached **seven committed sites** and
  five more in the planning material. A handler written there would have landed
  in RAM nothing reads, and the fault would still have hung the board.
- 🔴 **A fault the loader does not handle hangs forever** — `do_reserved` ends in
  a branch to itself with interrupts already off and the watchdog not armed. One
  fault costs one power cycle, and there is no spare unit.
- 🔴 **`do_reserved` dereferences the faulting code's own `$a0`**, and
  `rlx_cctl(0x002)` would have handed it the integer 2 — a kuseg address, a TLB
  refill to a vector nothing populated, and from there **undetermined**. Guarded
  before the payload was ever built, in two instructions. The sharper claim that
  went with it — *"it could branch into the loader's flash-write path"* — was
  refuted by the same day's adversarial pass and withdrawn: `0x5A5AA5A5` decodes
  as `BLEZL`, not a jump.
- 🔴 **A TFTP upload named `boot.img` makes the loader write from `0x80000000`
  upward**, over both exception vectors. On the do-not-type list from today.
- **`SPEC.md` `CPU-26` named the wrong table.** `0x8040A5C0` is the TFTP/ARP boot
  state machine, 24 entries; the exception table is `exception_handlers[32]` at
  `0x8040EB40`, in BSS.
- **`C-16` closes, and the refutation that had been recorded against it was
  itself wrong.** `check_image()` *is* the copier; it reads `gCHKKEY_HIT` at its
  17th instruction, not its first two. The block counter is where the document
  said, and it reads zero because a later rootfs scan sets it to exactly zero.
- **`CLK-15`**: the 350 ms of silence after `Booting...` is stage 1 copying
  20,924 bytes out of memory-mapped SPI NOR, uncached, a word at a time — and
  `Booting...` is printed by **stage 1**, so the experiment this project had
  written down for it pointed at the wrong binary.

Every one of these is in `PROGRESS.md`'s Corrections table with the date and
what caught it.
