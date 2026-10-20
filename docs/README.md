# docs/

Where to read about rlxfw, in three layers. This page holds links only; what is
true now is in the pages it links.

## Start here

- [`../README.md`](../README.md) — what rlxfw is
- [`architecture.md`](architecture.md) — how it boots, where it sits in the flash, and what runs with which privileges, in three diagrams
- [`charter.md`](charter.md) — what rlxfw set out to do, its boundaries, and the rules every release follows
- [`method.md`](method.md) — how a claim about the device is made and checked here
- [`FINDINGS.md`](FINDINGS.md) — what was found, on one page
- [`KNOWN-ISSUES.md`](KNOWN-ISSUES.md) — what does not work, and what each release does not establish
- [`reports/README.md`](reports/README.md) — one row per gate result: its claim, and what it does not establish
- [`bringup.md`](bringup.md) — the bring-up report
- [`build.md`](build.md) — building rlxfw, and what has been run the way that page says
- [`run.md`](run.md) — `make run`: `v1.0`'s userspace on an emulated board, a simulation and not a measurement

## Reports

- [`GATE-RESULTS.md`](GATE-RESULTS.md) — every gate's result, as written when it closed
- [`cases/README.md`](cases/README.md) — five defects, each from its dated record: the first hypothesis, the cut, the cause and the check left behind
- [`boot-time-table.md`](boot-time-table.md) — boot time, network up and throughput, the vendor firmware beside rlxfw
- [`differential.md`](differential.md) — the vendor firmware against rlxfw, by mechanism class
- [`rlx-isa.md`](rlx-isa.md) — the Lexra RLX4181 instruction set, measured on one die
- [`rlx-cache-and-cp0.md`](rlx-cache-and-cp0.md) — the cache model and the CP0 census
- [`toolchain-comparison.md`](toolchain-comparison.md) — three toolchains, the same measurements
- [`emulation-surface.md`](emulation-surface.md) — where the emulator and the silicon disagree
- [`mfgtest.md`](mfgtest.md) — the manufacturing test
- [`threat-model.md`](threat-model.md) and [`hardening-matrix.md`](hardening-matrix.md) — the positions this device is attacked from, and the mitigations on this part

## Reference and record

- [`spec/README.md`](spec/README.md) — how to read [`SPEC.md`](../SPEC.md), every number held about the device
- [`decisions/README.md`](decisions/README.md) — the decisions that shaped rlxfw, one page each: why, what it cost, and the evidence
- rlxfw's drivers, one page each — what it does, its registers and their sources, what holds on the silicon, its limits: [timer](drivers/timer.md), [gpio](drivers/gpio.md), [keys](drivers/keys.md), [wdt](drivers/wdt.md), [spi](drivers/spi.md), [nic](drivers/nic.md), [switch](drivers/switch.md), [entropy](drivers/entropy.md)
- [`../notes/README.md`](../notes/README.md) — the engineering notes, one per subsystem
- [`flash.md`](flash.md) — the flash: which regions may be written, under whose yes, and why the kernel region is recoverable
- The loader: [`loader-command-semantics.md`](loader-command-semantics.md), [`loader-flash-write.md`](loader-flash-write.md), [`loader-phy-and-switch.md`](loader-phy-and-switch.md)
- rlxfw's drivers against the vendor's: [`driver-diff.md`](driver-diff.md), [`nic-vendor-diff.md`](nic-vendor-diff.md), [`blind-write-ledger.md`](blind-write-ledger.md), [`vendor-modifications.md`](vendor-modifications.md)
- [`interrupt-map.md`](interrupt-map.md) — the interrupt map, and the layers a timer interrupt crosses
- The ISA probes: [`isa-prior-art.md`](isa-prior-art.md), [`isa-payload.md`](isa-payload.md), [`isa-hazard.md`](isa-hazard.md), [`probe3-cells.md`](probe3-cells.md), [`rlxprobe-audit-2026-08-25.md`](rlxprobe-audit-2026-08-25.md), [`toolchain-prior-art.md`](toolchain-prior-art.md)
- Releasing: [`release-process.md`](release-process.md), [`offer.md`](offer.md), [`sbom.md`](sbom.md)
- The record: [`history/README.md`](history/README.md) (text moved out of the state documents), [`log/README.md`](log/README.md) (the log, month by month), [`../LOG.md`](../LOG.md) (this month)
