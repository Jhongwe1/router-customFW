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
