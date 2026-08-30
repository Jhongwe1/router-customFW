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

## 🆕 …and none of the fifty can digest a stream, which is what decides the flash question

**Measured 2026-08-30 (`R3-8b`), and it closed a question rather than opening
one.** The section above asked what this `busybox` can run because a bench cell
depended on it. This one asks the same question for a different reason: whether
the flash can be read from **userspace**, as a second path beside the loader's
`FLR`.

`RUNSHEET` §B3's `G8b` row says *"zero flash bytes written"* needs a full
re-dump hashed against `FLS-14`, and on the loader's wire that is **6,300.1 s** —
量, the dump's own metadata. From a shell it would be one line:

```
dd if=/dev/mtd0 bs=64k | md5sum
```

**Neither half of that exists here.** 量, two ways that do not share a code path:

| route | result |
|---|---|
| every symlink in the extracted tree pointing at `busybox` | **exactly 50**, and the names are `ash bunzip2 bzcat cat chpasswd cp cut date echo expr false free getty grep halt head hostname ifconfig init ip kill killall klogd ln login ls mkdir mount nice nslookup ping ping6 poweroff ps reboot renice rm route sed sh sleep syslogd tail telnetd tr traceroute true umount uptime wc` |
| the applet-name table in the binary itself, at **file offset 266740** | the same names, and **`dd`, `md5sum`, `od`, `hexdump`, `cmp`, `cksum`, `sum`, `sha1sum` are none of them** |

⚠️ **`mknod` is the `uname` trap again, and it caught me once today.** A
`strings` grep over the whole binary returns `mknod`; the applet table and the
symlink set both say it is absent. That is the same false positive this file
already documents for `uname`, produced by the same lazy instrument — **the
binary containing a byte string is not the binary implementing an applet.** The
load-bearing measurement is the pair above, and `strings` is not part of it.

**What that costs, precisely.** `config/rlxfw-initramfs.tsv` declares three
device nodes and no `/dev/mtd*`; adding one is a single declared line and is
free. What is not free is the digest: a content check needs a binary that is
**not this unit's**, and Decision B's third leg is *the contents are this unit's
own binaries, unmodified — if the shell does not come up, the shell is not the
new thing* (`notes/kernel-build.md` §4).

🔴 **So the second path is not blocked by the device node, which is what it
looks like. It is blocked by the applet table.** And the node alone still buys
something, because **`wc` IS on the list**: it is a **readability and size**
reading through my own MTD stack — it says the partition opens and reads to EOF
at the length the map declares — and it is not a content check and must not be
quoted as one.

🔴 **But the command is NOT `wc -c < /dev/mtd0`, and this paragraph said it was
until 2026-08-30.** 量, two routes with a positive control on each: 讀 both
built `.config`s carry `# CONFIG_MTD_CHAR is not set` (control: nine other
`^CONFIG_MTD` lines in the same file), and 量 both `System.map`s hold **zero**
mtdchar symbols against **six** mtdblock/mtdcore ones. Major 90 has no chrdev in
either image, so `/dev/mtd0` opens `ENODEV`. What exists is `CONFIG_MTD_BLOCK=y`
→ `/dev/mtdblock<N>` at **b 31 N** (讀 `drivers/mtd/mtdblock.c`:
`.major = 31, .part_bits = 0`), and `/proc/mtd`, which reads **zero flash
bytes**. `config/rlxfw-initramfs.tsv` declares **`/dev/mtdblock1`** and
deliberately not `mtdblock0`: mtd0 is `0x000000`–`0x130000`, which contains the
loader and `H601`, `mtdblock` has a write path, and mode `0400` is not a control
because root ignores DAC. *(Original: "`wc -c < /dev/mtd0` is a readability and
size reading through my own MTD stack".)*

🔄 **2026-08-30, the rebuild: the premise of the paragraph above is no longer
the state of the build, and the command is neither of the two it names.**
`CONFIG_MTD_CHAR=y` went in (`SPEC.md` `FW-29`), so major 90 has a chrdev and
the image declares **`/dev/mtd0ro` `c 90 1`** and **`/dev/mtd1ro` `c 90 3`** —
ODD minors, which 讀 `mtd_open` cannot be opened for writing **by the
kernel**. `/dev/mtdblock1` is **withdrawn**: `mtd1ro` buys the identical
reading (`wc -c` → 2,949,120) and leaves no writable flash node in the image
at all. This paragraph's own sentence — *the control is the absence of a
node* — is what decided it, and it is now enforced by `mkinitramfs`
(`A24`/`A25`/`A26`) rather than argued. 量 for this file's own subject: the
applet census is unchanged and still decides the rest — `mknod` is not among
the fifty, so the declared node set is the only one this image can ever hold.
`notes/kernel-build.md` §18.3. `R3-9` owns the step; `SPEC.md`
`FW-26` owns the applet census and `FW-28`/`FW-29`/`FW-30` the map.

🆕 **2026-08-31: `wc` being ON the list was never the whole question, and the
other half is now measured too.** A cell that predicts a byte count needs the
applet's **output format**, not just its presence, and this file had the first
without the second — so the card's byte counts would have been a guess dressed
as a prediction.

量, this unit's own `bin/busybox` (`BusyBox v1.13.4`) under `qemu-mips-static`,
wrapped in `tools/vendor-tripwire.sh` and run from a scratch directory
(`CLAUDE.md`: running a vendor binary is not a read-only act):

| | |
|---|---|
| `wc -c` on three sizes through stdin | prints the digits and **nothing else** — no field padding, no leading spaces. 1,245,184 / 2,949,120 / 0, all bare |
| a redirect to a target that returns `EACCES` | `sh: can't create <path>: Permission denied` — the message `M-d` predicts, and where its 73 bytes come from |
| the applet table, re-read | unchanged at fifty, `wc` `cat` `echo` `sh` all present, negative control `definitely_not_an_applet: applet not found` in the same run |

⚠️ **The `EACCES` reading is from a NON-root uid.** `qemu-mips-static` runs
under the host user, so DAC applied and a `chmod 000` file produced the refusal.
On the device the shell is root and DAC does **not** apply — which is the whole
point of `M-d`: the refusal there comes from `mtd_open`'s `minor & 1` test in
the kernel, not from a mode bit. The message text is what transfers; the reason
it fires is a different one and `bench/2026-08-31/PREDICTIONS-B5-block3.md`
§7.3 says so.
