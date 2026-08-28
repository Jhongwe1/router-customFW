# What the vendor rootfs actually reaches the shell with

Measured 2026-08-25 at the desk, on `$FWRE_WORK/extracted/unit-2018/squashfs-root`
— the tree carved out of **this unit's own** flash dump, not a downloaded image.

The question this answers is narrow: **rlxfw's `R7` acceptance condition is
"`system` / `popen` reference count = 0 across the rootfs", and nothing had ever
established what the vendor's number is.** A target of zero is meaningless
without the thing it is zero against, and it turns out the number also decides
which userspace components rlxfw may ship.

## The count

| | |
|---|---:|
| files in the tree | **161** |
| ELF executables and libraries | **55** |
| **ELFs whose `.dynstr` carries `system` or `popen`** | **31** |
| files carrying a `#!` shebang | **75** |
| `.sh` files | **36** |
| symlinks pointing at `busybox` | **50** |

The 31:

```
bin/batchRemoteUpgrade  bin/boa*  bin/buffermemory  bin/ddns_inet  bin/dhcp6c
bin/dnsmasq†  bin/flash  bin/fwd  bin/iapp  bin/igmpproxy  bin/lld2d
bin/miniigd  bin/mldproxy  bin/notice  bin/ntp_inet  bin/ntpclient
bin/ppp_inet  bin/pppd  bin/rebootschedule  bin/rebootschedules  bin/reload
bin/routed  bin/sysconf  bin/timelycheck  bin/udhcpd  bin/updatedd  bin/wscd
lib/libapmib.so  lib/libcrypt-0.9.30.3.so  lib/libstdc++.so.6.0.13
lib/libuClibc-0.9.30.3.so‡
```

`*` both `system` and `popen` · `†` `popen` only · `‡` this is libc, so it is the
definition rather than a use.

## The three that decide a design question

| | |
|---|---|
| **`busybox` carries neither** | It carries `execv`, `execve`, `execvp`, `vfork`, `fork`, `daemon`. **Shipping busybox does not by itself break a zero.** |
| **`bin/udhcpd` carries `system`** | It is a standalone binary. This busybox has **no `udhcp*` applet compiled in at all**, so the vendor could not have used the applet. |
| **`bin/dnsmasq` carries `popen`** | Anything wanting a zero cannot forward DNS with dnsmasq. |

`bin/iptables` carries neither, so driving it through `execve` with an argv array
is compatible with a zero.

## Method, and what it cannot tell you

These binaries have **no section headers** — `file` says so and
`readelf --dyn-syms` returns nothing for them. A check built on `--dyn-syms`
reports **0 findings on every one of the 55**, which is indistinguishable from a
clean result. That is the shape of a tool that cannot fail, so it was not used.

What was used instead: scan the whole file for NUL-delimited printable runs and
match the symbol name exactly. `.dynstr` is present in the file whether or not
section headers are, so every imported symbol name is in the scanned set.

**Positive control** — names known to be imported must be seen:

| | busybox | boa |
|---|---:|---:|
| `malloc` | 1 | 2 |
| `strcpy` | 1 | 1 |
| `socket` | 2 | 1 |

**Negative control** — `zzz_not_a_symbol` and `pthread_create`: 0 and 0 on both.

**The known false negative, recorded because it was observed**: `printf` counts 0
on both, and both certainly format strings. The name only appears inside
`fprintf` / `sprintf` / `snprintf`, and the match is whole-line. So the method
answers "is this exact name present", not "does this program format".

**Therefore 31 is an upper bound.** A match is a name in the file; it is not
proof the name is an imported symbol rather than a message string. Deciding that
needs a walk of `PT_DYNAMIC` → `DT_SYMTAB` for the `UND` entries, which does not
depend on section headers either. Three of the 31 are worth doing that way
before the number is used for anything.

## Why the shebang count is here

`system()` is the mechanism most of the CVE reports name, but it is not the whole
surface. **75 files in this tree begin with `#!`**, and 36 of them are `.sh` —
`firewall.sh`, `init.sh`, `lan.sh`, `connect.sh`, `ip_qos.sh` among them. Every
one of those is a place where a value from configuration reaches a shell parser.
A firmware that reaches the same functionality with zero of them has removed a
class, not a bug, and the count is the evidence for that sentence.

## 🆕 What `busybox` here can actually do — 50 applets, and `uname` is not one

**Measured 2026-08-29 (`R3-7`), and it changed a bench cell.** The table above
counts **50 symlinks pointing at `busybox`**. Until today nobody had asked what
the binary those symlinks point at can actually run — the symlink count and the
applet list are two different questions, and only the second decides whether a
command typed at the shell works.

量, this unit's own `bin/busybox` (273,332 bytes, `BusyBox v1.13.4
(2018-01-10 14:56:45 CST)`) executed under `qemu-mips-static` against its own
extracted tree:

```
$ qemu-mips-static -L <rootfs> <rootfs>/bin/busybox uname -a
uname: applet not found
```

**The binary lists 50 applets.** Of the fourteen `RUNSHEET` §B5 needs, `uname`
is the only absent one; `cat`, `ifconfig`, `ping`, `ls`, `ps`, `mount`, `echo`,
`sleep`, `mkdir`, `sh`, `ash`, `sed` and `grep` are all present.

**Both controls are in the same run**, which is what makes `applet not found` a
reading rather than a broken invocation:

| | |
|---|---|
| negative | a name that is not an applet → `sh: definitely_not_an_applet: not found` |
| positive | `cat` reaches the filesystem and reports `No such file or directory` |

⚠️ **`qemu-mips-static -L <rootfs>` is not a sandbox**, and the first attempt
proved it: `busybox sh -c 'uname -a'` printed the **host's** uname, because the
shell's `PATH` search fell through to the real filesystem. That reading is an
artefact and is excluded. The load-bearing invocation is `busybox uname -a`,
which goes to the applet table and never touches `PATH`.

⚠️ **And the first tree tried was the wrong one.** `rebuild/fakework/extracted/
unit-2018` holds only `boa` and `busybox` under `/bin` — a partial carve — and
its **zero** symlinks would have supported a false conclusion about the shipped
firmware. The complete tree is `$FWRE_WORK/extracted/unit-2018/squashfs-root`:
163 files, 88 symlinks, 51 of them under `bin`/`sbin`/`usr/bin`/`usr/sbin`.

**What it changed**: `RUNSHEET` `K5` typed `uname -a` as one of D4's two
observables. It cannot run, and **adding a `/bin/uname` symlink would not have
fixed it** — the shell would `exec` `busybox` as `uname` and `busybox` would
refuse. `notes/kernel-build.md` §9 records that such a symlink was added for
`K5` and then removed, and neither step asked whether the applet exists.
`K5` reads `/proc/version` instead, which prints `linux_banner` verbatim and
therefore carries `(user@host)` and the gcc version that `uname -a` drops.
`notes/kernel-build.md` §12.7, `SPEC.md` `FW-25`.
