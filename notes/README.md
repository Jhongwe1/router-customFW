# notes/

Engineering notes, one per subsystem or question: how each part works, what
was measured on it, and what is still open. Each note owns its findings;
[`SPEC.md`](../SPEC.md) indexes the numbers ([how to read it](../docs/spec/README.md)).

## Drivers

- [`timer-driver.md`](timer-driver.md) — `rtl819x-timer`, a clocksource written blind
- [`gpio-driver.md`](gpio-driver.md) — `rtl819x-gpio`, and opening one bit of its write mask
- [`watchdog-driver.md`](watchdog-driver.md) — `rtl819x-wdt`, a `/dev/watchdog`
- [`spi-mtd-driver.md`](spi-mtd-driver.md) — `rtl819x-spi`, a read-only MTD device driven by programmed I/O
- [`nic-driver.md`](nic-driver.md) — `rtl819x-nic`, the CPU-port DMA driver
- [`switch-driver.md`](switch-driver.md) — the switch core, and rlxfw's driver for it
- [`entropy.md`](entropy.md) — why the board's random pool is empty, and rlxfw's source
- [`device-tree.md`](device-tree.md) — the device tree
- [`modern-kernel-port.md`](modern-kernel-port.md) — porting a 2.6.30 driver to a current kernel

## The core

- [`cache-model.md`](cache-model.md) — the cache-management model
- [`lwl-mystery.md`](lwl-mystery.md) — `lwl`, `lwr`, `swl`, `swr`: who uses them on this device
- [`vendor-kernel-isa.md`](vendor-kernel-isa.md) — what the vendor kernel uses, and what it emulates
- [`probe6-build.md`](probe6-build.md) — probe6's build, and the defects it exposed

## Toolchains and builds

- [`vendor-toolchains.md`](vendor-toolchains.md) — the three rsdk toolchains, and what each builds
- [`which-drop.md`](which-drop.md) — which GPL drop built the shipped firmware
- [`binsim.md`](binsim.md) — `binsim`, the ruler, its calibration and its floor
- [`kernel-build.md`](kernel-build.md) — how rlxfw's kernel is built, wrapped and reached
- [`incremental-build.md`](incremental-build.md) — the incremental build, and what it costs
- [`reproducible-build.md`](reproducible-build.md) — `P4a`, the reproducible build
- [`busybox-build.md`](busybox-build.md) — rlxfw's own busybox
- [`iperf3-port.md`](iperf3-port.md) — `iperf3` on the RTL8196E
- [`rebuild-vs-shipped.md`](rebuild-vs-shipped.md) — rebuilding `boa` and `busybox`, scored against the shipped binaries

## Userspace

- [`init.md`](init.md) — PID 1 and `ifupd`
- [`config-store.md`](config-store.md) — the config store
- [`broker.md`](broker.md) — `brokerd`, the privileged broker
- [`httpd.md`](httpd.md) — `httpd` and the password KDF
- [`dnsfwd.md`](dnsfwd.md) — `dnsfwd`, the DNS forwarder
- [`userspace-integration.md`](userspace-integration.md) — the six programs reconciled into one tree
- [`userspace-probe.md`](userspace-probe.md) — `uprobe`, the first userspace binary compiled here
- [`rootfs-census.md`](rootfs-census.md) — what the vendor rootfs reaches the shell with

## Boot, update and the console

- [`rlxboot.md`](rlxboot.md) — `rlxboot`, a second-stage loader that verifies a signed container
- [`update-chain.md`](update-chain.md) — the signed update chain, the host side
- [`self-update.md`](self-update.md) — self-update and anti-rollback from the running firmware, the design (`P6r-10`, `P6r-11`)
- [`slots45-draft.md`](slots45-draft.md) — slots 4 and 5, the Linux half of a seating
- [`boot-time.md`](boot-time.md) — boot time, its instrument and its clock
- [`console-link.md`](console-link.md) — the console link and how fast it goes
- [`flash-digest-scope.md`](flash-digest-scope.md) — what a digest over this unit's flash may say

## The bench and the record

- [`dev-loop.md`](dev-loop.md) — the development loop, and what one iteration costs
- [`power-and-programmer.md`](power-and-programmer.md) — the 1.70 V: what the desk could settle, and what was deliberately not run
- [`leak-surface.md`](leak-surface.md) — what identifies this unit, and where it already is
- [`record-integrity.md`](record-integrity.md) — the record's own instruments
- [`vendor-differential.md`](vendor-differential.md) — the vendor differential, as measured
