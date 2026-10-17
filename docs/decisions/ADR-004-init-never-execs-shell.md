# ADR-004: PID 1 never execs a shell

## Context
Until `R7`, every rlxfw image's `/init` was `config/rlxfw-init.sh`: four commands and an `exec /bin/sh`. `R7`'s claim is that nothing in the rootfs reaches a shell through `system()` or `popen()`, and its baseline counts shebang files and shell scripts beside those calls. "A `#!/bin/sh` `/init` is a shell script in the shipped image." (`notes/init.md` § 1)
## Decision
PID 1 is a compiled `/init` (`src/init/`). It mounts, loads the config store by linking its loader, brings the LAN up with `write(2)`s of compile-time literals, and supervises its children; every child is `fork` + `execve` with an argv of string literals and a fixed three-entry environment, and no argv byte comes from the config store, a lease or the kernel command line. 讀 `nm` over the linked binaries: `init` links `execve` and nothing else of that family, and `ifupd` links no `exec*` symbol at all. The bench shell, where a build has one, is a supervised child announced on every boot, never PID 1 itself.
## Alternatives considered
- **The R3-era shell-script `/init`**: replaced, for the reason above. The script stays in the tree; the image's manifest, `config/rlxfw-initramfs.tsv`, points `/init` at the compiled binary.
- **PID 1 running `cfgstore` to read its own configuration**: rejected — "a supervisor that needs a child in order to decide what to supervise has a bootstrap loop in it" (`notes/init.md` § 2).
- **A bench shell a kernel command line can turn on**: rejected — `rlxfw.noshell` turns it off in a build that has it, and nothing turns it on in one that does not: "A door a command line can open is a door." (`notes/init.md` § 5)
## Consequences
- 量 `R7`: PID 1 is `/init`, and `httpd` and `dnsfwd` run as their own uids, `dnsfwd` printing `setuid(0) refused` (`FW-175`).
- `v1.0` is built with `BENCH_SHELL ?= 1`, so it opens a root shell with no password on the serial console; anyone with the header has root ([`docs/known-issues/v1.0.md`](../known-issues/v1.0.md)).
- A shell with a controlling terminal never prints `job control turned off`, so `tools/looprun.py` needs `--boot-until` on these images (`notes/init.md` § 5).
- This SoC cannot power itself off: `RB_POWER_OFF` and `RB_HALT_SYSTEM` both reach `while (1);` (讀), so the poweroff path prints `PULL THE POWER` before it takes it (`notes/init.md` § 4).
## Evidence
[`notes/init.md`](../../notes/init.md) § 1, § 2, § 4 and § 5; [`notes/userspace-integration.md`](../../notes/userspace-integration.md) § 7; [`docs/GATE-RESULTS.md`](../GATE-RESULTS.md) entry 17 (`R7`); [`docs/known-issues/v1.0.md`](../known-issues/v1.0.md); [`SPEC.md`](../../SPEC.md) `FW-175`. Decided 2026-09-30, in `R7`.
## Status
In force. The bench shell is a build choice, and `v1.0` ships with it on.
