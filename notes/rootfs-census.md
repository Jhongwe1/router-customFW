# What the vendor rootfs actually reaches the shell with

Measured 2026-08-25 at the desk, on `$FWRE_WORK/extracted/unit-2018/squashfs-root`
— the tree carved out of **this unit's own** flash dump, not a downloaded image.
§ *The count*, § *The three that decide a design question* and § *Method* were
re-measured 2026-09-30 with `tools/uspacescan.py`; four of their claims were
wrong and are marked where they stood.

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
| of those, statically linked — no `PT_DYNAMIC` | **3** |
| **ELFs matching a whole-string scan for `system`/`popen`** | **31** |
| **ELFs that *import* `system` or `popen`** | **28** |
| files carrying a `#!` shebang | **75** |
| `.sh` files | **36** |
| symlinks pointing at `busybox` | **50** |

量 2026-09-30, `tools/uspacescan.py --vendor-census`; every row above reproduced
on the same tree. The 31 below are the string scan's; the 28 are the same list
without the three marked `§`. The two numbers are **not** a better and a worse
count of one thing — see § *Method*.

```
bin/batchRemoteUpgrade  bin/boa*  bin/buffermemory  bin/ddns_inet  bin/dhcp6c
bin/dnsmasq†  bin/flash  bin/fwd  bin/iapp  bin/igmpproxy  bin/lld2d
bin/miniigd  bin/mldproxy  bin/notice  bin/ntp_inet  bin/ntpclient
bin/ppp_inet  bin/pppd  bin/rebootschedule  bin/rebootschedules  bin/reload
bin/routed  bin/sysconf  bin/timelycheck  bin/udhcpd  bin/updatedd§  bin/wscd
lib/libapmib.so  lib/libcrypt-0.9.30.3.so  lib/libstdc++.so.6.0.13§
lib/libuClibc-0.9.30.3.so†‡§
```

> 🔴 **2026-09-14 (the sixty-ninth segment, desk): two of those names are a
> safety finding together, and nothing here had put them side by side.**
> 讀 `unsquashfs -ll` on the image itself — the extracted tree shows no device
> nodes at all, because `unsquashfs` could not create them without root and its
> own log says `created 0 devices`, so reading the extraction rather than the
> image gives a false zero here. In the image: `/dev/mtd0`–`/dev/mtd4` at
> `crw-rw-rw-` 90,0–90,4 and **`/dev/mtdblock0`–`3` at `brw-rw-rw-` 31,0–31,3**.
> `/dev/mtdblock0` is **mode 0666 and covers the loader and `H601`** — the two
> regions this project's own rules call unrecoverable — and `bin/flash`
> (87,664 B) sits in the same `PATH`. 讀 the board config's
> `# CONFIG_MTD_CHAR is not set`, so the `mtd*` char nodes are dead (`ENODEV`);
> `CONFIG_MTD_BLOCK=y`, so **`mtdblock*` is live**.
> ⚠️ **What this does and does not say**: it is about the vendor's shipped
> rootfs, not about rlxfw's, and nothing of this project's has ever run there.
> What it changes is the cost of the one route into vendor userspace that is
> known to work — **any injected command line on this device runs one typo away
> from a brick**, which is a reason beyond the flash-write one to leave that
> route alone. `PROGRESS.md`'s `VDR-1` carries the route; this row carries why
> the route is worse than its own flash write.


`*` both names · `†` `popen` only · `‡` libc, so this is a definition, not a use
· `§` matched by the string scan but **not** an import (§ *Method*). 🔴 `‡` was
the only mark on libc and it was not enough: libc matches on `popen` alone, and
its `system` is one of the names the string scan **misses** (§ *Method*).

## The three that decide a design question

Imports, 量 2026-09-30 by the `PT_DYNAMIC` walk.

| | |
|---|---|
| **`busybox` imports neither `system` nor `popen`** | It imports `execlp`, `execv`, `execve`, `execvp`, `fork`, `vfork` (and `waitpid`); 250 imports in all, 275 `.dynsym` entries. **Shipping it breaks no zero over `system`/`popen`** — and that is the whole of what it establishes: `execlp` and `execvp` let `PATH` decide which file runs, so a zero over a wider name set is decided by the *build*, and `R7` builds `udhcpc`/`udhcpd` from busybox. `notes/busybox-build.md` § 3–§ 4 owns rlxfw's own build, its excluded applets and its one `execle` exemption. 🔴 **`daemon` is not absent from `.dynstr` — it is a string-scan hit that lies outside it, with no `.dynsym` entry at all.** 量 the run `daemon` sits at file offset `0x3f768`, while this file's `.dynstr` is `0x1ba8`–`0x2460`; no `.dynsym` entry of that name exists, so it is not an import and not an export. It *is* a genuine import of `bin/udhcpd`, **the row directly below**. Naming that is worth more than the fix: the value moved between two adjacent rows of one table, which is a defect no checker in this repository can see — `spec-check` and `citecheck` read ids, citations and structure, and a plausible name in the wrong row is structurally valid. The only thing that catches it is re-deriving each row from the bytes. *(Superseded: "it carries `execv`, `execve`, `execvp`, `vfork`, `fork`, `daemon`" and "shipping busybox does not by itself break a zero" — `daemon` was never a busybox import, `execlp` was absent from the list, and the zero was asserted without naming the set it is a zero over.)* |
| **`bin/udhcpd` imports `system`** | …and `execle`, `fork`, `daemon`; 84 imports. It is a standalone binary, and this busybox has **no `udhcp*` applet compiled in at all**, so the vendor could not have used the applet. `daemon` is an import *here* — this row, not the one above, is the one it belongs to. |
| **`bin/dnsmasq` imports `popen`, `execl` and `fork`** | …plus `pclose` and `waitpid`; 120 imports, and the entry count has two agreeing sources, `DT_MIPS_SYMTABNO` 217 = `DT_HASH` nchain 217. Anything wanting a zero cannot forward DNS with dnsmasq. `notes/dnsfwd.md` § 7 owns the symbol-level comparison with rlxfw's own forwarder. *(Superseded: "`bin/dnsmasq` carries `popen`", which named one of three.)* |

`bin/iptables` imports none of `system`, `popen`, `execl`, `execlp`, `execvp`,
`execle` — of 118 imports its only two here are `execv` and `fork` — so driving
it through `execve` with an argv array is compatible with a zero; `bin/ip6tables`
is the same at 116. `bin/boa` imports both `system` and `popen`, and `execl`,
`fork` and `pclose` besides.

## Method, and what it cannot tell you

Two methods, both readable with **no section header table** — the constraint that
chose them. **String scan**: every NUL-delimited run of printable bytes in the
whole file, matched *whole*. **Import walk**: `PT_DYNAMIC` → `DT_SYMTAB`, entry
count from `DT_HASH`'s nchain cross-read against `DT_MIPS_SYMTABNO`, counting
`SHN_UNDEF`. 量 2026-09-30 by `tools/uspacescan.py`, whose `--self-test` passes
30 controls with 0 failed and 0 skipped and finds a planted `system()` both
before and after `mips-linux-strip`.

**The 31 − 28 gap is exactly three files, each for its own reason.**
`bin/updatedd` is statically linked, so it has no `PT_DYNAMIC` and the import
walk is *structurally* blind to it; `lib/libstdc++.so.6.0.13` holds the run
`system` at file offset `0xa4b9c`, outside its `.dynstr`, and has no `.dynsym`
entry of that name at all; `lib/libuClibc-0.9.30.3.so` **defines** `popen`
(`st_shndx` 7, `FUNC`, 612 B), which is a definition and not an import.

🔴 **`readelf --dyn-syms` is empty on 54 of the 55, not on all 55.** 量
`bin/acltd` (10,032 B) keeps its section headers — `e_shoff` `0x2348`,
`e_shnum` 25, the only `SHT_DYNSYM` *section header* in the tree — and host
`readelf` 2.42 prints its 51 entries, 29 of them undefined. Every other file has
`e_shoff` 0. That makes `--dyn-syms` **worse** than this section used to argue,
not better: a checker built on it returns one non-empty answer out of 55, and
that one answer is exactly what would make its 0 on the other 54 look earned.
*(Superseded: "these binaries have no section headers … a check built on
`--dyn-syms` reports 0 findings on every one of the 55".)*

**Positive control** — names known to be imported must be seen:

| | busybox | boa |
|---|---:|---:|
| `malloc` | 1 | 2 |
| `strcpy` | 1 | 1 |
| `socket` | 2 | 1 |

**Negative control** — `zzz_not_a_symbol` and `pthread_create`: 0 and 0 on both.

### What each method gets wrong, and what has to hold for a count to mean anything

**A string scan over-reports.** A whole-run match says a name is in the bytes,
not that the program asked for it: 3 of the 31 above are not imports. On a
**stripped, statically linked** ELF the over-report is the whole reading. 量 on
rlxfw's own busybox (447,684 B, no `PT_DYNAMIC`, no `.symtab`): the whole-run
match gives `system` **0**, while a *bare name* scan — substring, the form a
`strings | grep` reaches for — gives **7**, and all seven are other people's
text: five uClibc messages (`Interrupted system call`, `Interrupted system call
should be restarted`, `Bad system call`, `Read-only file system`, `Too many open
files in system`) and two paths (`/etc/filesystems`, `/proc/filesystems`). Such a
file offers a bare scan **no positive control at all**, so its 0 is a statement
about the instrument and not about the file. What decides it instead is a third
method that survives `strip`: a relocation-masked fingerprint of the libc member
that defines the name. 量 on the same binary it finds `execle` at `0x41b690` with
one `.got` reference — so the file is **not** clean, and the string scan's 0 for
`system` was the only true thing a name scan said about it.
`notes/busybox-build.md` owns that build and that `execle`'s exemption;
`tools/uspacescan.py` refuses a file for which it has none of the three methods,
rather than reporting 0. The same reading on a static `cfgstore` is **unmeasured**
— that binary does not exist yet, so there is no 0 to quote; it can be taken once
the image step builds one.

**A string scan also under-reports, and this section denied that.** The old
wording was *"`.dynstr` is present in the file whether or not section headers
are, so every imported symbol name is in the scanned set"*, and that is false: a
string table **tail-merges**, so a shorter name may be stored only as the tail of
a longer one and never appear as a run of its own. 量 over the 52 dynamic ELFs
here — 3,752 (file, import) pairs, of which the scan sees 3,435 and **misses 317
across 61 distinct names**: `malloc` behind `safe_malloc` in `bin/dnsmasq`,
`close` in 37 files, `printf` behind `sprintf` — which this section already
recorded as an oddity without naming the mechanism. 🔴 **And `system` is one of
the missed names, on this tree**: `lib/libuClibc-0.9.30.3.so` stores
`__libc_system`, and its `system` entry points 7 bytes into that run, so no
`system` run exists in it and the scan does not see one. libc is in the 31 only
because it matched `popen`.

**An import walk cannot see a static file at all.** 0 is also its passing answer,
so there it is not a weak reading but a vacuous one. Three of the 55 are static:
`bin/radvd`, `bin/radvdump`, `bin/updatedd`.

**So 28 is not a corrected 31, and neither number is a bound by construction.**
31 over-counts three files; 28 is a count over 52 files and says nothing about
the other three. *"31 is an upper bound"* held here as an **observation** — it
survives because no file both imports `system`/`popen` and is the only place that
name occurs — and the mechanism that would break it is live in this tree, one
name away. A count of this kind means something only when all three hold: every
file in the population is dynamically linked, or the static ones are named and
counted apart; the name counted is not a proper suffix of another name in the
same string table, which is decidable (量 `__libc_system` is exactly that case
for `system`; no name in the tree ends in `popen`); and the instrument is shown
finding a planted positive in the run that reports the 0.

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

🔄 **2026-09-06: re-derived a week later, and the list is published here for
the first time.** Same binary, same method, tripwire CLEAN on four trees:

```
ash bunzip2 bzcat cat chpasswd cp cut date echo expr false free getty grep halt head hostname ifconfig init ip kill killall klogd ln login ls mkdir mount nice nslookup ping ping6 poweroff ps reboot renice rm route sed sh sleep syslogd tail telnetd tr traceroute true umount uptime wc
```

**50, the same number, and `uname` is still not in it.** 🔴 **`dd` is not in
it either**, which is a second source for a reading taken on the board the
same evening — `busybox dd` answered `dd: applet not found` at a shell on the
device (`SPEC.md` `FW-42`). 🟢 **And `grep` IS in it**, so this image's
`grep: invalid option -- E` is a build option and not a missing applet; those
two point at different fixes and only the list separates them.

🟢 **The warning at the top of this section now has an answer, and it is the
one that makes the warning worth keeping.** *The symlink count and the applet
list are two different questions* — 量, they are also the same fifty: every
one of the 50 symlinks names an applet and every one of the 50 applets has a
symlink, `comm` both ways empty. **So on this rootfs the two questions agree,
and the place they come apart is the IMAGE**: `config/rlxfw-initramfs.tsv`
carries **11** of those symlinks, while the binary it links to still has all
50 applets — which is why `busybox <name>` works on the board for commands
that have no bare name.

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
| 🆕 **what rlxfw's own image declares, which is a DIFFERENT population** | **eleven**: `sh ash cat echo ls mount ps ifconfig ping mkdir sleep` (`config/rlxfw-initramfs.tsv`). 🔴 **`reboot` is not among them, and the applet is still reachable as `busybox reboot`** — that gap is exactly what `tools/cardcheck.py commands` exists for. 🔴 **And 量 2026-09-06 (seating 14), the applet being reachable is not the end of it**: `busybox reboot` **does not reset this board**, because busybox's default `reboot` signals PID 1 and this image's PID 1 is `config/rlxfw-init.sh`, a shell script that ignores it. The vendor's rootfs runs busybox `init` there, which does not. **`busybox reboot -f` skips the hand-off and works**, 2.407 s to the loader prompt. `SPEC.md` `FW-37` |
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

### 🔴 2026-08-31, seating 7: BOTH rows above are true and BOTH were read too widely

**① *"no field padding"* is a property of the SINGLE-field form only.** 量 the
same day, same route, on the exact partition slices of the 2026-08-16 dump:

| form | on `mtd0`'s 1,245,184 bytes | width |
|---|---|---:|
| `wc -c` | `1245184` | 7, bare |
| `wc -l` | `4422` | 4, bare |
| 🔴 `wc -lc` | `␣␣␣␣␣4422␣␣␣1245184` | **19, PADDED** |

Two `%9d` fields joined by one space — confirmed on a zero-length control
(`␣␣␣␣␣␣␣␣0␣␣␣␣␣␣␣␣␣0`, also 19). The sentence above says *no field padding*
without qualification, and a card written on it would have predicted 33 against
a measured 45. **The row was right about what it measured and the write-up
generalised past it.**

⚠️ **This paragraph's own measurement nearly went the same way.** The first run
of it printed an empty string for all nine cells and the script reported that as
a format: busybox here is dynamically linked and `qemu-mips-static` needs
`-L <sysroot>`. It was caught because the **negative** control returned the same
error as the positive one — *a tool reporting nothing is making a claim*.

**② `wc` is on the applet list and was NOT in the image.** 量 on the silicon,
seating 7: `wc -lc < /dev/mtd0ro` → **`/bin/sh: wc: not found`**.

> The applet table and the image's symlink set are two different populations.

讀 `config/rlxfw-initramfs.tsv`: eleven symlinks point at busybox — `sh ash cat
echo ls mount ps ifconfig ping mkdir sleep` — and `wc` is not one. This census
answers *what can this binary do*; a bench cell needs *what can this image
invoke*, and **nothing compares a card's typed commands against the declaration
of the image it uploads**. The reading was recovered with `busybox wc`, which
needs only the declared `/bin/busybox` file.

**③ And the `EACCES` message is right in text and wrong in prefix.** 量 on the
device: `/bin/sh: can't create /dev/mtd0ro: Permission denied` — **78 bytes for
the cell, not 73**. `qemu` ran busybox with argv[0] = `sh`; the device's shell
was invoked through the `/bin/sh` symlink and prints that. **+5 characters, on
every shell-error cell this project will ever write.**

**④ The input-redirect failure is busybox's own short message, not
`strerror`'s.** 量: `sh: can't open <path>: no such file` — *not* `No such file
or directory`. `bench/2026-08-31b/PREDICTIONS-B5-block3e.md` is sized on it and
`X-d2` returned **74 bytes, exact**.

⚠️ **The `EACCES` reading is from a NON-root uid.** `qemu-mips-static` runs
under the host user, so DAC applied and a `chmod 000` file produced the refusal.
On the device the shell is root and DAC does **not** apply — which is the whole
point of `M-d`: the refusal there comes from `mtd_open`'s `minor & 1` test in
the kernel, not from a mode bit. The message text is what transfers; the reason
it fires is a different one and `bench/2026-08-31/PREDICTIONS-B5-block3.md`
§7.3 says so.

---

## 🆕 2026-09-06 (seating 13): `ping` ignores `-c`, and it always sends four

The section above asks *what can this binary run*. This one asks a narrower
question about one applet, and the answer changes what a bench card may ask
for.

`bench/2026-09-06/P2-7b` typed `ping -c 20 10.1.1.2` and the board sent four
packets. Five requests were then put to it across three cells:

| capture | asked | transmitted |
|---|---|---|
| `NB-1`, `CE-12` | `-c 4` | 4 |
| `P2-7b` | `-c 20` | 4 |
| `P2-7c` | `-c 2`, then `-c 7` | 4, 4 |
| `P2-7d` | `-c20` (attached form), then `busybox ping -c 3` | 4, 4 |

The echoed command line is intact in every capture, so the shell received what
was typed; the spaced and attached option forms behave the same; and invoking
`busybox ping` directly rather than through the symlink behaves the same.

**量: this image's `ping` ignores `-c` and always sends exactly four packets.**

⚠️ **What it does and does not do to the record.** It invalidates nothing —
four replies is four replies, and `R3`'s D5 got what it needed. What it removes
is a degree of freedom nobody knew was missing: **every `ping -c N` in this
repository has been getting the default rather than the request**, and a card
cannot ask this image for a count other than 4.

🔴 **The mechanism is undetermined and the first place to look is this file's
own subject.** `config/rlxfw-initramfs.tsv` declares which file provides
`ping`; `mkinitramfs verify` reads what the built image actually contains. The
busybox here is this unit's own `bin/busybox`, `BusyBox v1.13.4`, 273,332
bytes — a vendor binary, so if the count is patched in, `config/host-compat/`'s
rule applies and it may only be changed on a staged tree. `SPEC.md` `NET-26`
carries the reading and §17 carries the gap.

---

## 🆕 2026-09-14 — the BUILTIN side, probed for the first time, and one control that did not fire

Every census above is about **applets**. `tools/cardcheck.py:166 (this project has)` says in its own comment that the *builtin* table of this binary **has never been enumerated**, and that nothing currently rests on its guess. A bench card needed a sampling loop, so it was enumerated. `SPEC.md` **`FW-66`**.

量: `qemu-mips-static -L $FWRE_WORK/extracted/unit-2018/squashfs-root` running that unit's own `bin/busybox ash -c`, from a scratch directory, wrapped in `tools/vendor-tripwire.sh`. **BusyBox v1.13.4 (2018-01-10 14:56:45 CST)**.

| construct | result |
|---|---|
| `while` + `[` + `$((n+1))` | rc 0, N lines |
| `until`, `for … in` | rc 0 |
| `cat` of two files in one invocation | rc 0, both emitted |
| `busybox grep -e ^dat`, two `-e` patterns | rc 0 |
| command substitution `$(…)` | rc 0 |
| `printf` | rc 0 |
| `read` **without** `-t` | rc 0 |
| `read -t` | 🔴 **`ash: read: line 1: illegal option -t`** |
| `sleep 0.13` / `sleep .13` / `sleep 0.5` | rc 0, and they really sleep — 0.18 / 0.15 / 0.53 s against a `sleep 0` floor of 0.045 s |

🔴 **One of my controls did not fire, and that is a measurement rather than a harness fault.** I predicted `[[ … ]]` is bash-only and this ash would reject it. **It has it, and it evaluates**: `[[ 1 -eq 1 ]]` takes the true branch and `[[ 1 -eq 2 ]]` the false one, so it is not simply always-true. The harness is still shown able to report failure by two other controls in the same run — an absent applet gives **rc 127** and an absent file **rc 1**.

⚠️ **What this does NOT do.** It does not enumerate the builtin table; it probes the constructs one card needed. `cardcheck`'s guess list is still 推, and the honest change is that the specific words a card now types are 量.

⚠️ **And the applet half is not new** — the run reproduced the same **50** applets § *What `busybox` here can actually do* already records, by a different route (running the binary rather than reading it). Two routes, one number.


## 🆕 2026-10-04 (120th segment) — a bare applet name does not resolve, and `/bin` holds seventeen things

`config/image-commands.tsv`'s header already said this and it was still worth
measuring, because the table is the thing `cardcheck` refuses against: *`kind=applet`
means `busybox <name>` resolves. It does NOT mean the applet works.*

**Refutation condition, written before the test:** if `busybox dmesg` also
failed, the table would be overstating what the image can invoke and the row
would need a 殘留.

量 2026-10-04, `bench/2026-10-04/SOAK-DMSG`, `SOAK-BB1`, `SOAK-BB2`, `SOAK-BB3`:

* bare `dmesg` and bare `tail` both return `sh: not found`, although both are
  listed as applets.
* `busybox dmesg` resolves. `busybox tail -18` returns `tail: invalid option --
  1`: this busybox wants `-n 18`. Same class as `FW-42` (`grep` present,
  `grep -E` absent) and this image's `ping` ignoring `-c`.
* `ls /bin` -- the positive control, and the more useful half -- returns exactly
  seventeen entries: `ash busybox cat echo ifconfig iperf3 linkprobe ls mfgtest
  mkdir mount ping ps sh sleep ucost uprobe`. Five of those are **not** busybox
  applets: `linkprobe`, `mfgtest`, `ucost`, `uprobe`, `iperf3`.
* `busybox free`: 28,488 total / 6,680 used / 21,808 free kB.

So the table is correct as worded, and a bench cell that types a bare applet
name will fail on a name `config/image-commands.tsv` lists.

### What this does not establish

**It is not a census of the image's symlinks**, only of `/bin`. `udhcpd` runs
under its bare name in `ps`, and `brokerd` and `cfgstore` live in `/usr/sbin`,
so directories remain unlisted. It does not establish that the other twelve
`/bin` entries work, only that they resolve -- which is the distinction the
command table's own header draws.

## 🆕 2026-10-04 (`R9-4`) — which uid `bin/boa` runs as, and whether it chroots

`SPEC.md` `FW-199` owns the row; this section owns the reading. Artefact: this
unit's own firmware, `$FWRE_WORK/extracted/unit-2018/` — `rootfs.squashfs`
(1,876,033 B) for anything about modes, and `squashfs-root` for file *contents*,
which the extraction does preserve. Every command and every script is kept in
`$FWRE_WORK/rebuild/s121-r9-4/`. No power action and no flash verb.

`plan/REVIEW-2026-08-22.md` item 14's row reads `chroot + 降權 … ❌（boa 是 root）`
with `ps` in its evidence column. That is an assertion carrying an instrument
that cannot run: the vendor firmware has no shell (`docs/GATE-RESULTS.md`, `P2`'s
⊘ Structural). Four sources below, then the verdict.

### A — the launch path

讀 `/etc/inittab` (361 B) holds exactly **one** non-comment line,
`::sysinit:/etc/init.d/rcS`. Six further lines — an `askfirst` shell, a
`respawn` shell, a `getty` on the console and three `tty2`–`tty4` shells — are
commented out. busybox's inittab format has no user field, so no line in this
file names a uid.

讀 `/etc/init.d/rcS` (2,814 B, 111 lines) launches the web server at **line
109**, bare: line 108 is the comment `# start web server`, line 109 is `boa`,
line 110 is `#skt&`. No `su`, no wrapper, no option, not even a trailing
ampersand.

讀 **Ten uid-changing tokens read 0 files across the tree's text files.** The
instrument is `grep -rIc` — `-I`, so binaries are skipped — counting files with
at least one hit: `su ` 0, `su -` 0, `setuidgid` 0, `chpst` 0,
`start-stop-daemon` 0, `runuser` 0, `setpriv` 0, `setuid` 0, `setgid` 0,
`initgroups` 0. **Positive control, same flags, same run**: `User ` 1 file,
`Group ` 1 file (both `etc/boa/boa.conf.bak`), `chroot` 1 file
(`etc/vsftpd.conf`, six commented `chroot_*` lines). So the instrument finds
tokens where tokens are and the ten zeros are readings.

🔴 **The population is the text files, and saying so is load-bearing.** Drop
`-I` and the same greps read `setuid` **8** files, `setgid` **6**, `chroot` **6**,
`su ` **1**, `User ` **5** — all binaries. A sentence that said *nowhere in the
image* would be false. What the ten zeros establish is that no **script** on any
path changes a uid; what a binary links is source C's question.

讀 busybox's applet list carries `killall` and carries neither
`start-stop-daemon` nor `reinit`.

### B — the configuration file boa actually reads

讀 `/etc/boa/boa.conf` is a symlink to `/var/boa.conf`, and `/var` is a `ramfs`
that `rcS` line 10 mounts with **no options at all** (`mount -t ramfs ramfs
/var`). So the live config is not in the image. **Its generator is**: `bin/sysconf`
and `bin/timelycheck` each carry the two literal shell lines
`cp -a /etc/boa/boa.conf.bak /var/boa.conf` and
`echo "Port 80" >> /var/boa.conf`, so the running config is `boa.conf.bak`
verbatim plus one appended `Port 80`.

讀 `boa.conf.bak` (9,504 B) has exactly **thirteen** uncommented directives:
`User root`, `Group root`, `PidFile /var/run/webs.pid`, `DocumentRoot /web`,
`UserDir public_html`, `DirectoryIndex index.html`, `DirectoryCache /tmp`,
`KeepAliveMax 0`, `KeepAliveTimeout 10`, `MimeTypes /etc/boa/mime.types`,
`DefaultType text/html`, `CGIPath /bin:/usr/bin:/usr/local/bin`,
`SinglePostLimit 4096000`. There is **no `ServerRoot` directive and no chroot
directive** — the only `ServerRoot` in the file is line 15's comment saying it is
not in this configuration file, and Boa 0.94's config language has no chroot
directive at all. `DocumentRoot /web` points at a symlink into the same ramfs,
which `rcS` line 55 fills with `flash extr /web`.

🔴 讀 **And the config's `User`/`Group` values would not have helped even if the
binary applied them.** `/etc/passwd` is a symlink to `/var/passwd`; the image's
`/etc/passwd.org` (213 B) carries five rows, and **three of them are uid 0 gid
0** — `root`, a second credentialled account `onlime_r`, and **`nobody`,
which in this image is uid 0 and gid 0**. The other two are `ftpshare` 501/501
and `sambashare` 502/502; there is no uid 500 row. So the stock `#User nobody`
line `boa.conf.bak` ships commented out at line 48 would also have resolved to
uid 0. Verified field by field with `awk -F:` printing fields 1, 3 and 4 only;
no hash from that file is quoted here or anywhere in this repository.

### C — the binary's import list

讀 `bin/boa` is 485,012 B, ELF32 MSB, `EXEC`, MIPS R3000, `e_shoff` **0**,
`e_shnum` 0, flags `0x1007` (noreorder pic cpic o32 mips1), 8 program headers,
`PT_INTERP` `/lib/ld-uClibc.so.0`, `DT_NEEDED` `libapmib.so`, `libc.so.0`,
`libgcc_s.so.1`.

讀 `readelf --dyn-syms` prints **0 bytes** on this file, and so does
`readelf -D --dyn-syms` — which reproduces `FW-20`'s instrument warning exactly:
with no section headers that route cannot tell clean from unread. The import
list therefore comes from a `PT_DYNAMIC` → `DT_SYMTAB` walk (`DT_HASH`
`0x00400248`, `DT_STRTAB` `0x0040278c`, `DT_SYMTAB` `0x00400d0c`, `DT_SYMENT`
16, `DT_MIPS_SYMTABNO` **424**, `DT_PLTGOT` `0x00485ff0`,
`DT_MIPS_LOCAL_GOTNO` 13, `DT_MIPS_GOTSYM` 13), cross-checked by an independent
`DT_HASH` bucket/chain lookup per name. 424 entries = 1 unnamed + **163** named
`SHN_UNDEF` imports + **260** named and defined.

| name | linear walk | `DT_HASH` walk |
|---|---|---|
| `setuid` `setgid` `seteuid` `setegid` `setreuid` `setregid` `setresuid` `setresgid` `setgroups` `initgroups` | **absent, all ten** | absent, all ten |
| `geteuid` `getegid` `prctl` `capset` `setrlimit` `daemon` | absent | absent |
| `chroot` | PRESENT, idx 417, `SHN_UNDEF` | PRESENT |
| `chdir` `getpwnam` `getgrnam` `getuid` `getgid` `umask` | PRESENT | PRESENT |
| `system` `popen` `malloc` `socket` `fork` | PRESENT (positive controls, already read by `FW-20`) | PRESENT |
| `rlxfw_absent_symbol_control` | absent (negative control) | absent |

Eleven positive controls present, one negative control absent, and the two paths
agree on all twenty-eight names queried. **`bin/boa` links no
privilege-dropping entry point at all**, so the live config's `User root` is a
dead word rather than an operative setting: it cannot change its own
credentials whatever a config file says.

### D — does the text reference those imports, and under what guard

An import says the linker recorded a name; it does not say the text calls it. On
o32 MIPS PIC every external call loads the callee from the GOT, so counting
`lw $t9, X($gp)` words whose `X` maps to a symbol's GOT slot is a reference count
taken from the instruction stream. 讀 `$gp` = `0x0048dfe0`, read out of
`PT_MIPS_REGINFO`'s `ri_gp_value` at offset +20 of that segment rather than
assumed — ⚠️ reading it at +24 instead falls off the end of a 24-byte segment and
returns `0x00000001`, a plausible-looking number rather than an error. 讀
**9,450** such words over **305** distinct `X` in the executable LOADs.

讀 `chroot` **1** site (`0x405504`); `chdir` 9 (first `0x4054c0`); `getuid` 3;
`getpwnam` 2; `getgrnam` 1; `getgid` 1; `umask` 1. Positive controls in the same
run: `system` **187**, `malloc` 28, `fork` 18, `socket` 15, `popen` 1. Negative
control — a gp offset 64 words past the end of the GOT — **0** sites.

讀 The one `chroot` site is a `switch` case, not straight-line code. The loop is
`while ((c = getopt(argc, argv, "c:dl:f:r:")) != -1)`, option string at
`0x462448`; the body starts `addiu v0,v0,-99` (`'c'`), `sltiu v1,v0,16`, `beqz`
to the default, then an indexed `jr` through a 16-word table at `0x4624c0`. The
table's last word, at `0x4624fc`, is `0x004054c0` — index 15, letter 99+15 = 114
= **`'r'`**. The table holds exactly five non-default targets (`0x00405454`,
`0x004054a8`, `0x004054b0`, `0x00405554`, `0x004054c0`) against exactly five
option letters in `c:dl:f:r:`, the other eleven slots all being the default
`0x00405570`, so the mapping is closed rather than guessed.

讀 The `'r'` case body is three calls in sequence, each guarded only by its own
error test (`bne v0,s1` with `li s1,-1` at `0x4053c0`), the fall-through being
`perror(...)` then `exit(1)`:

    0x4054c0  chdir(optarg)      ; on -1 -> perror @0x4623c0 "chdir (to chroot)"
    0x405504  chroot(optarg)     ; on -1 -> perror @0x4623d4 "chroot"
    0x40552c  chdir("/")         ; on -1 -> perror @0x4623dc "chdir (after chroot)"

The three strings at `0x4623c0`, `0x4623d4` and `0x4623dc` read back byte for
byte as above, and `0x46c6e8` — the third call's argument — is the one-byte
string `/`. 讀 With no `-c`, boa instead does `server_root = strdup("/etc/boa")`
(string at `0x462454`, failure message `strdup (SERVER_ROOT)` at `0x462460`) and
`chdir(server_root)` at `0x40561c`. A `chdir`, not a `chroot`.

**Refutation condition, written before the search**: if any launcher in the
image hands `boa` a `-r`, the chroot verdict flips. 讀 a byte grep for `boa`
followed by whitespace, a dash and a letter, over every file of the tree,
returns **one** hit — `boa -c`, inside the comment `# boa -c /usr/local/boa` at
`boa.conf.bak` line 19. **Control, same grep shape, same run**: the pattern
`boa.conf` returns hits in four files, so the search is not silently empty. 讀
The only `/bin/boa` string in the whole image lives inside `bin/boa` itself, at
file offset `0x6892c`, in a (label, pidfile, binary) restart table — `kill boa `,
`/var/run/webs.pid`, `/bin/boa`, then `kill wscd ` — and the byte after
`/bin/boa` is NUL. Six other binaries (`ddns_inet`, `fwd`, `ntp_inet`,
`ppp_inet`, `sysconf`, `timelycheck`) carry `killall -9 boa` or `reinit boa `;
none carries a `boa` command line with an option.

### Verdict ①

讀 **On the shipped image there is no privilege change and no chroot on the path
that starts the vendor's web server.** The launch is `boa` with no argument from
`rcS`, which `/etc/inittab` runs as PID 1's `sysinit`; the binary links no
uid-setting function at all; and its single `chroot` call site is reachable only
through the `-r` command-line case, which no launcher in the image uses.

推 **Therefore `bin/boa` runs with the uid PID 1 holds — 0 — and with `/` as its
root directory.** This half is 推 and not 量: no reading here was taken from a
running vendor system. The four sources do not disagree; they agree, they are of
four different kinds (init script, config generator, import table, instruction
stream), and the interesting part is *how* they agree — the config's `User root`
is inert in this build rather than operative, so a vendor who had written
`User nobody` would have got exactly the same uid, twice over, because `nobody`
is uid 0 here.

**What this does not establish.**

* Not the runtime uid or root directory. The 量 for those is `/proc/<pid>/status`
  and `/proc/<pid>/root`, which need a shell the vendor firmware does not have —
  ⊘ Structural, the same disposition `P2` already carries.
* Not that a script generated into `/var` at runtime cannot relaunch `boa` with
  `-r`. The image cannot answer that; only a running vendor system could, and
  that route is the ⊘ above. Note the direction: that residue could only make
  the vendor's posture *better* than stated, never worse.
* Not anything about exploitability. The 187 `system` GOT loads are a count of
  linked references, and `plan/` § 8.1's `CVE-2014-8361` entry is the standing
  precedent for why code shape is not effect. Which of them a request reaches is
  `FW-20`'s question and is not answered here.
* Not that `getpwnam`/`getgrnam`/`getuid`/`getgid` are unused — they are
  referenced, 2 + 1 + 3 + 1 sites. What is established is that nothing in the
  binary can *apply* their results to the process credentials.
* Not a claim about any other firmware version. Everything above is `unit-2018`.

## 🆕 2026-10-04 (`R9-4`) — the vendor setuid / setgid / exec-bit census, off the image

`SPEC.md` `FW-200` owns the row. Read off the **image**, never off the
extraction. `unsquashfs` version **4.6.1 (2023/03/25)**, run as **uid 1000, not
root** (`id` printed in the same script). `unsquashfs -ll` on `rootfs.squashfs`
(1,876,033 B) → rc 0, **567** lines on stdout, **0** bytes on stderr. `-ll` lists
modes out of the superblock and creates nothing, so running it unprivileged
costs nothing.

讀 567 inodes — and 567 is `FW-08`'s inode count, so the listing is the whole
filesystem: **260** block, **38** char, **20** directories, **161** regular,
**88** symlinks. 260 + 38 + 20 + 161 + 88 = 567.

| | count | detail |
|---|---|---|
| **setuid files** | **0** | no path, no mode — the list is empty |
| **setgid files** | **0** | likewise |
| sticky entries | 0 | |
| regular files | 161 | |
| … with any exec bit | **160** | `-rwxr-xr-x` x114, `-rwxrwxr-x` x46 |
| … with no exec bit | **1** | `etc/version`, `-rw-rw-r--`, 41 B |
| … world-writable | 0 | |
| FIFOs, sockets | 0, 0 | |

114 + 46 + 1 = 161. 讀 Ownership: all 269 regular files, symlinks and
directories are `500/501`; 297 of the 298 device nodes are `root/root` and the
one exception is `/dev/ptmx` at `root/tty`.

**Positive control, in the same run** — the listing must show a device node, and
`FW-68` already read device nodes off this image, so the control is that this run
reproduces them. 讀 **298** device nodes (260 block + 38 char), including
`FW-68`'s exact readings: `/dev/mtd0`–`mtd4` at `crw-rw-rw-` 90,0–90,4 and
`/dev/mtdblock0`–`3` at `brw-rw-rw-` 31,0–31,3. **The named node:
`/dev/mtdblock0`, type `b`, mode `brw-rw-rw-` (0666), major 31 minor 0** —
`FW-68`'s row verbatim, and the reason that row matters is that mtd0 covers the
loader and `H601`.

**Negative control, in the same run** — the identical census over
`squashfs-root`, via `find`/`stat` instead of `-ll`: block **0**, char **0**,
fifo 0, socket 0, setuid **0**, setgid **0**, sticky 0. That is the false zero
the rule exists to name: 298 device nodes become 0. `extract.log`'s own tail says
it in the tool's words — `created 161 files`, `created 20 directories`,
`created 88 symlinks`, **`created 0 devices`**, `created 0 fifos`,
`created 0 sockets`, `created 0 hardlinks` — with **298** lines reading
`because you're not superuser!`, exactly one per dropped node.

🔴 **And the negative control is sharper than the rule.** The extraction's
*regular-file* modes are wrong too: image `-rwxr-xr-x` x114 + `-rwxrwxr-x` x46 +
`-rw-rw-r--` x1 against extraction `-rwxr-xr-x` x160 + `-rw-r--r--` x1. **47 of
161 regular files read a different mode in the extraction**, all 47 by the
group-write bit (umask 022). So a group-writable or world-writable census over
the extraction returns a false zero as well, not only a device-node census.

🔴 **Positive control for the setuid detector itself, because 0 is a claim.** A
census reporting 0 setuid and a census blind to setuid bits print the same
number. So: `mksquashfs` 4.6.1 built `probe.squashfs` from one 4755 file, one
2755 file, one 0644 file and a pseudo-definition `b 666 0 0 31 0`, `-all-root`.
讀 `unsquashfs -ll` on that image prints `-rwsr-xr-x`, `-rwxr-sr-x` and
`brw-rw-rw- 31, 0`, and the same parser reads **setuid 1, setgid 1, device nodes
1**. So the 0/0 on the vendor image is a reading.

🔴 **And extracting that same probe as non-root reads setuid 0, setgid 0, device
nodes 0** — both files come out `-rwxr-xr-x`. **The extraction's zero for setuid
and setgid is a demonstrated false zero, not a suspected one.** The rule written
above for device nodes holds for the setuid bit, the setgid bit and the
group-write bit as well, and that is now shown rather than argued. This is the
most load-bearing line in the reading: before it, a mode census over the
extraction was *suspected* of lying about setuid; now it is known to.

讀 **Second parser, no shared code**: an `awk` field-offset count agrees on
unit-2018 — 161 regular, 160 with an exec bit, 0 setuid, 0 setgid, 298 device
nodes — and reads 1 / 1 / 1 on the probe image. A third parser, written
afterwards without reading either, reproduces all of it plus the mode
multiset 114 / 46 / 1 and the 269 / 297 / 1 ownership split.

讀 **Different population** (other devices, not this unit's firmware), same
instrument, for context only: `n200re-3.2.0` 168 regular / 166 exec,
`n300rt-2.1.6` 164 / 163, `n300rt-3.4.0` 371 / 342, `v2.1.2` 165 / 164,
`v3.4.0` 364 / 363 — **0 setuid and 0 setgid in all five**, 298 device nodes in
three of them and 327 in two.

### Verdict ②

讀 **The shipped vendor image carries zero setuid files and zero setgid files.
160 of its 161 regular files are executable; the one that is not is
`etc/version`.** `plan/REVIEW-2026-08-22.md` item 14's vendor `無 setuid binary`
cell turns out to be right, and now has a reading under it instead of the word
`CI`.

**What this does not establish.**

* Nothing about runtime. 讀 `rcS` line 10 mounts `ramfs` on `/var` with **no
  options** — no `nosuid` — and `/tmp`, `/web`, `/etc/passwd`,
  `/etc/boa/boa.conf`, `/etc/hosts` and `/etc/resolv.conf` are all symlinks into
  it. A root process can create a setuid file there at runtime and an image
  census cannot see it. "No setuid binary in the image" is not "no setuid binary
  on the box".
* Not that 0 setuid is what bounds the vendor here. Every shipped regular file is
  owned by uid **500**, which has no row in `/etc/passwd.org`, so a setuid bit on
  one of them would have conferred uid 500 rather than 0. What puts the vendor's
  userspace at uid 0 is the reading above — the web server itself — not a setuid
  bit.
* Not a hardlink census. `-ll` prints no link count, and `extract.log`'s
  `created 0 hardlinks` is a line from the extraction, which this reading does
  not trust for anything.
* Not the per-file exec-bit *appropriateness*. 160 of 161 executable is a count,
  not a judgement, and 106 of those files are not ELFs at all (`FW-20` reads 55
  ELFs out of the same 161).
* Not a reading of a different firmware version for this device. The five other
  images above are other products.

### Both readings, jointly

Both are tier `V-B` — static, from this unit's own dump-derived image — and
`V-B` carries no executable refutation, because the vendor firmware has no
shell. So they say what the shipped bytes are and what shape the code has. They
do not say that any defect is absent, and they do not say that any of this is
reachable. Where each instrument could be lying: `unsquashfs -ll` could fail to
print modes it cannot see (settled by the probe image); the `-ll` parser could
index the wrong mode column (settled by two further parsers with no shared
code); the extraction drops device nodes, setuid, setgid and group-write (shown
directly on the probe and in `extract.log`'s own words); `readelf --dyn-syms`
reports nothing and nothing looks clean (not used, and `FW-20` already named
it); the `PT_DYNAMIC` walk could mis-size entries (settled by the `DT_HASH`
lookup agreeing on all 28 names); the GOT count counts loads rather than
executed calls (the one `chroot` load at `0x405504` is followed by `jalr t9`,
and a gp offset past the GOT reads 0); the `boa` option grep could be silently
empty (the `boa.conf` control hits four files).
