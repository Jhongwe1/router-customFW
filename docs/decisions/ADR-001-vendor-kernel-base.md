# ADR-001: Linux 2.6.30 from the vendor's GPL drop as the kernel base, not a mainline kernel

## Context
The shipped firmware runs `Linux version 2.6.30.9 (admin@office.hopeiot) (gcc 4.4.5-1.5.5p2)` (量, `FW-03`). Three staged Realtek SDK GPL drops each carry a `linux-2.6.30` whose SoC port is `arch/rlx`, a sibling of `arch/mips` (讀, `notes/vendor-kernel-isa.md`); which drop built the shipped image stays 推 (`docs/GATE-RESULTS.md` entry 2). Mainline Linux has no `arch/rlx` at all, and 2.6.30's MIPS has no device tree (`docs/bringup.md` § 1, § 3).
## Decision
rlxfw's kernel is the vendor's `linux-2.6.30` from the drop, built with the drop's own `rsdk` toolchain. rlxfw's drivers live in `kernel/` and reach the staged tree only through `config/rlxfw-marks.tsv` and `config/host-compat/`; vendor source is never edited by hand (`CLAUDE.md` § Never). Device-tree bindings for a current kernel are written and compile-tested beside it, in `dt/`, and have never run.
The repository's first README, 2026-08-23, already describes rlxfw as built from the vendors' GPL drops; no tracked file records the reason at that date. The reason recorded since is the one below.
## Alternatives considered
- **A current kernel with device-tree bindings** ("model B"): four drivers compile against 6.18.50 with 2.84 %–6.98 % code churn, figures that are floors (`notes/modern-kernel-port.md`). It lost as the kernel that runs on the recorded reason: "The device is one unit with no spare. A 2.6.30 driver that has been arming a watchdog on the silicon for two seatings is evidence; a 6.8 driver that has never been near the part is not." (`docs/bringup.md` § 1, 2026-09-09)
- **The two public modern-kernel ports of this SoC**, `shibajee/linux-rtl8196e` and `ggbruno/openwrt`'s OpenWrt 4.14 target: the repository reads them as the comparison for its blind drivers and records which drivers each lacks (`docs/driver-diff.md`). The recorded reason they were not taken as the base was not found; looked in `README.md`, `docs/`, `notes/`, `docs/log/` and `docs/GATE-RESULTS.md`.
## Consequences
- The kernel emulates `ll`/`sc` and runs `sync` as a no-op, so the ISA and CPU hazards are measured on bare metal only (`CPU-47`).
- Drivers are written to 2.6.30's API: their `/proc` instrumentation uses `create_proc_entry`/`read_proc`, which a current kernel no longer has (`docs/bringup.md` § 1.1), and no irqchip driver is written, because 2.6.30 has no `irq_domain` and it would be the wrong shape (`docs/bringup.md` § 4).
- What moving a driver costs is measured only to compilation: compiling is not upstream acceptance, and none of the four ports has run (`docs/bringup.md` § 3a).
## Evidence
[`docs/bringup.md`](../bringup.md) § 1, § 1.1, § 3, § 3a and § 4; [`notes/modern-kernel-port.md`](../../notes/modern-kernel-port.md); [`notes/vendor-kernel-isa.md`](../../notes/vendor-kernel-isa.md); [`docs/driver-diff.md`](../driver-diff.md); [`docs/GATE-RESULTS.md`](../GATE-RESULTS.md) entries 2 (`R2a/b/d`) and 4 (`R3`, the first boot of a kernel built here); [`SPEC.md`](../../SPEC.md) `FW-03`, `CPU-47`; [`SOURCES.json`](../../SOURCES.json); [`CLAUDE.md`](../../CLAUDE.md) § Never. Decided by 2026-08-23; the reason for keeping it recorded 2026-09-09.
## Status
In force. The device-tree kernel stays bindings only: written, compiled, never probed.
