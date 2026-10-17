# ADR-005: `-fno-if-conversion`, and the other code-generation constraints for this core

## Context
The RLX4181 exposes the MIPS I load delay slot: there is no interlock (量, `CPU-14`), so code compiled as if there were one gives wrong values with no fault and no warning. Realtek's gcc emits conditional moves for this core, under `.set noreorder`, and a kernel built without a flag carried seven sites of one shape: a `movz` reading the register a `lw` two instructions earlier writes. gas's load-delay model covers a conditional move's `rs` and `rt` and not its `rd` (量, `notes/kernel-build.md` § 7.1). `tools/hazlint` counts load-use violations in a linked image.
## Decision
- The kernel is built with the drop's `rsdk-1.3.6-4181` at `-march=4181`, the side of the split that pads the load delay slot, and never at `-march=mips32` ("Decision A", `notes/kernel-build.md` § 1).
- Every built-in kernel object gets `-fno-if-conversion`, declared in [`config/rlxfw-cflags`](../../config/rlxfw-cflags) and passed as `CFLAGS_KERNEL`, with no source line changed. Recorded reason: it takes `hazlint` from 7 load-use violations to 0 by removing 2,566 of 2,597 conditional moves, at +16,788 bytes of `.text`, +0.69 % (量, `TC-25`).
- Assembly is written under `.set noreorder`, every delay slot filled by hand: "you cannot know what the assembler filled in" (the first `CLAUDE.md`). `hazlint` is a build gate.
## Alternatives considered
- **`-march=mips32`, or the 5281 side**: one `vmlinux` from one source through `rsdk-1.5.5`'s wrapper at the 5281 side carries 21,185 load-use violations (讀, `TC-15`); `mflxc0`/`mtlxc0`, the LOPI interrupt-mask primitive, does not assemble at `mips32` (`docs/interrupt-map.md` § 1.1).
- **`rsdk-1.5.5`, the generation that built the shipped firmware, at `-march=4181`**: its flag set is a reconstruction (推). "If `R3` does not boot, the vendor's own (toolchain, board, config) triple leaves the code generator out of the suspect list; a reconstructed toolchain puts it back in." (`notes/kernel-build.md` § 1)
- **Adding `-fno-if-conversion2`**: it removes no further conditional move and costs 4,808 more bytes (`TC-25`). **The flag in `arch/rlx/Makefile`'s `cflags-y`**: a patch to a vendor file for the same effect (`notes/kernel-build.md` § 7.2).
## Consequences
- The flag removes sites; whether they were hazards was measured later. 量 2026-09-14: with its destination just loaded and the condition false, `movz` acts as write-enable on this die, so the flagless build's sites were not silent corruption; the neighbouring shape, a move whose condition register was just loaded, reads exposed (`TC-h`, `CPU-54`).
- It cannot reach a prebuilt `libc.a`: a statically linked userspace binary keeps the conditional moves Realtek's compiler chose, and the flag "may not be CLAIMED to have bought anything" there (`config/rlxfw-cflags`, `notes/iperf3-port.md` § 4).
- The flag first reached a build typed at a shell, and the image that booted could not be rebuilt from its recorded configuration (量, `TC-37`): the file exists so that no build depends on a typed flag, and an empty `--cflags-kernel` is refused.
## Evidence
[`config/rlxfw-cflags`](../../config/rlxfw-cflags); [`notes/kernel-build.md`](../../notes/kernel-build.md) § 1, § 1.1 and § 7; [`docs/interrupt-map.md`](../interrupt-map.md) § 1.1; [`notes/iperf3-port.md`](../../notes/iperf3-port.md) § 4; [`CLAUDE.md`](../../CLAUDE.md) § Never; [`SPEC.md`](../../SPEC.md) `CPU-14`, `CPU-54`, `TC-15`, `TC-25`, `TC-37`, `TC-h`. Decided: the `-march` and `.set noreorder` rules in the first `CLAUDE.md`, 2026-08-23; the toolchain 2026-08-28; the flag declared 2026-08-30 (`R3-9`).
## Status
In force. `notes/kernel-build.md` § 7.2 allows the flag to be dropped with a reason if `movz` proved write-enable, and `TC-h` found it so for the destination; the flag has not been dropped, and no tracked file records a decision either way.
