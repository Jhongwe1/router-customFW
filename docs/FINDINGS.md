# Findings

What this project found about one TOTOLINK N150RT (RTL8196E SoC, Lexra `RLX4181` core) that
changed what it did next, one line each: the finding, why it mattered, and the file that owns
it, which wins wherever the two disagree. Marked as the rest of the repository is: **量**
measured, on this unit or, for a build or a tool, at the desk, **讀** read out of code or a
dump, **推** inferred, pending a measurement.

| | Finding | Why it mattered | Owner |
|:-:|---|---|---|
| 量 | The core executes `lwl`, `lwr`, `swl` and `swr`, which the public record says its Lexra family lacks; branch-likely, the conditional traps, `clz`, `mul` and `sync` trap | the family's documents are not evidence about this die — in part a legal settlement required that description (讀) — so what code built here may use is read from a bare-metal census with its own trap handler | [`docs/rlx-isa.md`](rlx-isa.md) § 1, § 3 |
| 量 | A load's result is not ready for the instruction after it: the hazard closes at one instruction | `-march=mips32` is banned and `hazlint` gates every build, so no image ships an unfilled load slot | [`docs/isa-hazard.md`](isa-hazard.md) |
| 量 | CP0 `Count` is not implemented | the SoC timer driver became a prerequisite rather than an option | [`docs/rlx-cache-and-cp0.md`](rlx-cache-and-cp0.md) |
| 量 | The D-cache is not coherent with a DMA master: it read-allocates, and a line it holds goes stale under a DMA write | the NIC driver keeps its rings and buffers in the uncached window, a measured requirement rather than a precaution | [`docs/rlx-cache-and-cp0.md`](rlx-cache-and-cp0.md) § ② |
| 量 | DRAM keeps written data across a power cycle | a read-back equal to flash proves nothing on its own, so every flash read here pre-reads its destination | [`bench/2026-08-31/CORRECTIONS-block3.md`](../bench/2026-08-31/CORRECTIONS-block3.md) § 5 |
| 量 | Outside the 8 KiB it never reads (`H601`), this unit's flash differs from its 2026-08-16 dump in two 4 KiB sectors, `0x9000` and `0xD000`; the boot loader's region is unchanged | no claim here says no flash byte was written: each states the commands sent and what the reads cover | [`notes/flash-digest-scope.md`](../notes/flash-digest-scope.md) § 8 |
| 量 | `busybox reboot` does not reset this board; `busybox reboot -f` does, through a watchdog bite | every scripted reset is `busybox reboot -f` | [`notes/watchdog-driver.md`](../notes/watchdog-driver.md) § 1 |
| 量 | rlxfw's lost transmissions were a descriptor-length fault: with the vendor's length convention 220 of 220 pings were answered, on two boots where the old one answered 145 of 1,327 and 144 of 1,189 | the vendor's convention is the NIC driver's default since `rtl819x-nic` 1.6 | [`notes/nic-driver.md`](../notes/nic-driver.md) § 25–§ 29 |
| 量 | Booting by itself from flash, the stock loader skips the switch setup it makes at its prompt, so rlxfw's port received nothing | rlxfw's switch driver writes the loader's VLAN layout at boot | [`notes/switch-driver.md`](../notes/switch-driver.md) § 20–§ 21 |
| 量 | Behind a `cr6c` header the stock loader also looks for a root filesystem in slot A, and stops silently when there is none | `rlxboot` and its rescue copy are installed as `cs6c` | [`notes/update-chain.md`](../notes/update-chain.md) § 6 |
| 量 | Ten power cuts in the middle of a slot write each booted the other slot | the A/B design's answer to a torn write is measured for paced writes; a cut inside an unpaced write, the kind an update makes, is not | [`notes/rlxboot.md`](../notes/rlxboot.md) |
| 量 | Two builds of one tree differed in 84 bytes, 78 of them the initramfs packer's clock; freezing the kernel's build timestamp fixes 6 | the packer's entries carry a declared time too, and a release image rebuilds byte for byte | [`notes/reproducible-build.md`](../notes/reproducible-build.md) § 2 |
| 讀 | In the public Linux port for this SoC, four timer functions read the 32-bit `TCCNR` into a `u16`, so they never set the control bits at 31:28, and `-Wall` is silent | found by diffing the driver written here against it; this tree was then measured to put no register read into a narrow type | [`docs/driver-diff.md`](driver-diff.md) § 3.5 |
| 量 | A check that computes its own population fails silently and green: an empty population reads like a clean one | populations here come from another instrument, and every sweep carries a positive control | [`notes/record-integrity.md`](../notes/record-integrity.md) § 1 |

The page this one replaced — 257 rows of findings, most of them written in August and
September 2026, each under the decision it changed — is
[`docs/history/findings-2026-10-17.md`](history/findings-2026-10-17.md), moved there whole. What closed each gate is indexed in [`docs/reports/`](reports/README.md); every
number, newer findings included, is in [`SPEC.md`](../SPEC.md), entered in English through
[`docs/spec/`](spec/README.md).

## What this page does not establish

It is a selection of fourteen, chosen as findings a reader outside the project can check
against the evidence its owner names; a finding not here is not therefore smaller, and none is
re-measured here. Each line is this page's reading of its owner on 2026-10-17.
