# rlxfw's own busybox — build, applet decision, and what it does not settle

`R7`, 2026-09-30.  Owner of *how rlxfw's busybox is built and why its applet set
is what it is*.  The recipe is `tools/mkbusybox.sh`; the applet set is
`config/rlxfw-busybox.config`, which is the real deliverable.  Sizes and counts
here are 量 on the artefact this segment built; `$OUT/busybox.build` is the
machine-readable record the build writes beside every binary.

## 1  What this replaces, and why it mattered

Until now `config/rlxfw-initramfs.tsv` declared `/bin/busybox` as **this unit's
own vendor binary**, tagged `unit`: BusyBox v1.13.4, 273,332 bytes, dynamically
linked against three of the unit's own libraries, with eleven applet symlinks
pointing at it.  That single row is why `docs/KNOWN-ISSUES.md` cannot say the
userspace is rlxfw's, and it is the reason Decision B (`notes/kernel-build.md`)
could say "the shell is not the new thing".

The source of that exact version ships in the vendor GPL drops.  This builds it.

## 2  How it is built

    tools/mkbusybox.sh [--config F] [--out D] [--stage D] [--drop N] [--ref N]
                       [--jobs N] [--keep] [--dry-run]

**Which drop, and why it does not matter.**  `busybox-1.13` is present in three
of the trees under `src-vendor/`: `rtl819x-toolchain/users/`,
`saturn49-wecb/rtl819x/users/` and `wecb-vz-gpl/rtl819x/users/`.  量 2026-09-30,
`diff -rq`: their **source is byte-identical**; the only difference is that the
`rtl819x-toolchain` copy has been built in place at some point and carries
fourteen build products (`.config`, `.config.old`, `include/autoconf.h`,
`include/applet_tables.h`, `include/bbconfigopts.h`,
`include/usage_compressed.h`, `include/config/`, `docs/BusyBox.1`,
`docs/BusyBox.html`, `docs/busybox.net/BusyBox.html`, `scripts/basic/docproc`,
`scripts/basic/fixdep`, `scripts/basic/split-include`, `scripts/kconfig/conf`).
The default `--drop` is `rtl819x-toolchain` because `SOURCES.json` gives it role
`base` — *the primary source tree the build is derived from* — and because it is
the drop `tools/rlxfw-kbuild.sh` already stages the kernel from.  Since the
source is equal across all three, the choice changes no byte of the artefact,
and that equality is the build's own first gate rather than a claim made here.

**The gates.**  Each one refuses; none skips.

| | what it establishes |
|---|---|
| `G0` | a **partially staged** tree is refused, not repaired.  `$STAGE/.staged` is written only after the last patch applies, so an interrupted `cp` or a failed patch leaves the tree present and the stamp absent, and `--keep` on it refuses |
| `G1` | the staged source, with those fourteen products deleted **by name** (never by glob), equals a **second, independent drop** byte for byte.  Shown finding a planted file first.  `--ref none` is refused: this is the guard against a stale `include/autoconf.h` deciding the applet set while the installed `.config` says nothing |
| `G2` | every patch in `config/busybox-patches/` applies, in name order, and the count applied equals the count declared |
| `G3` | `make oldconfig` changes **no declared symbol**.  The committed `.config` must therefore be fully resolved.  The comparison is over non-comment lines because kconfig rewrites line 4 with the wall clock; shown seeing a planted symbol first.  It earned its keep on its first real run: a comment-only edit to the header accidentally cut `CONFIG_HAVE_DOT_CONFIG=y` and `G3` stopped the build |
| `G4` | no `-march` anywhere the script controls (tested on the real flag string, not grepped for a literal); `CONFIG_STATIC=y` and `CONFIG_CROSS_COMPILER_PREFIX="mips-linux-"` read out of the `.config` **above the stage**; then, on the artefact, no `PT_INTERP`, big-endian, `e_flags 0x1007, noreorder, pic, cpic, o32, mips1` — the same word `linkprobe` and `iperf3` carry (C-only static links; `uprobe`'s `0x1005` differs only in `EF_MIPS_PIC`) |
| `G5` | `tools/hazlint` over the linked ELF: **0 violations in 26,072 loads** |
| `G6` | the forbidden imports, from the symbol table of the unstripped link, with the **positive control first**: the same `nm` on the same `libc.a` must show all six names, or a clean report only means `nm` stopped working.  Then the one exemption, swept both ways |
| `G7` | the **declared** build stamp is in the banner and today's date is not |

**Flags.**  Target: whatever `Makefile.flags` already gives (`-std=gnu99`, `-Os`
under `CONFIG_DEBUG=n`, `-static` under `CONFIG_STATIC=y`) plus
`EXTRA_CFLAGS="-fno-builtin -fno-strict-aliasing -fno-common"`, which reaches
every object through kbuild's `_c_flags`.  **No `-march`**: the rsdk wrapper's
default is the 4181 core.  Host: `-fgnu89-inline` is added to `HOSTCFLAGS`,
because gcc 13 compiles kconfig's gperf-generated `zconf.hash.c` under C99
inline semantics and `HOSTLD scripts/kconfig/conf` then dies with *undefined
reference to `kconf_id_lookup`*.  That is a host flag and reaches no target byte.

**`-fno-if-conversion` is NOT used, and that is a measurement.**  `SPEC.md`
`TC-25` needs it for the kernel (7 load-use violations → 0).  量 here: without
it, `hazlint` is already 0 over 26,732 loads.  The flag is not added on
speculation; if a later applet set makes `hazlint` non-zero, `config/rlxfw-cflags`
is where the answer comes from.

**Reproducibility.**  量 2026-09-30, first attempt: two runs produced binaries of
the same size differing in **exactly one byte** — the seconds digit of
`BusyBox v1.13.4 (2026-09-30 09:28:29 CST)`.  kconfig writes
`AUTOCONF_TIMESTAMP` into `include/autoconf.h` from the wall clock, and
`Makefile.flags` passes `-DBB_BT=AUTOCONF_TIMESTAMP`, so busybox's banner is a
clock reading.  Same defect `P4a` found in the kernel (84 bytes there), same fix:
one declared epoch from `config/rlxfw-build-stamp`, rendered with `LC_ALL` and
`TZ` pinned so the stamp is a property of the declaration and not of the desk.
With that in place two builds from two independent stages are **byte-identical**,
and a comment-only edit to the `.config` moves no byte of the artefact.

## 3  The excluded applets, and the rule that excludes them

Rule: **no applet whose source reaches `system()`, `popen()`, `execl()`,
`execlp()` or `execvp()`** — by any spelling.  The macro spellings count: 讀
`include/libbb.h`, `BB_EXECVP` expands to `bb_execvp` (itself `execvp`) or
straight to `execvp`, and `BB_EXECLP` to `execlp`; `run_shell()` execs a shell by
construction.  量 2026-09-30 over the staged 1.13.4, **fifty-one** `.c` files
under the applet directories reach one of them.  `libbb/` is excluded from the
count because its objects live in an archive and are pulled in only when
referenced — which is why the finished binary imports none of these names even
though `libbb/execable.c` and `libbb/run_shell.c` were compiled.

The table below is all fifty-one, with files feeding one applet on one row (47
rows).  **Two files are deliberately NOT counted and not in it**:
`e2fsprogs/old_e2fsprogs/fsck.c` and `runit/svlogd.c` reach `execv`, which is not
on the forbidden list — a fixed `argv` array with no PATH search.  `svlogd.c`
nonetheless execs `/bin/sh`; neither applet is in this build, so neither decision
had to be made.

| file | how it reaches | applet(s) |
|---|---|---|
| `archival/dpkg.c` | `system` | dpkg |
| `archival/libunarchive/open_transformer.c` | `BB_EXECVP` | (used by the decompressors) |
| `archival/tar.c` | `BB_EXECLP` | tar |
| `console-tools/openvt.c` | `BB_EXECVP` | openvt |
| `console-tools/reset.c` | `execvp` | reset |
| `coreutils/chroot.c` | `BB_EXECVP` | chroot |
| `coreutils/env.c` | `BB_EXECVP` | env |
| `coreutils/nice.c` | `BB_EXECVP` | **nice** |
| `coreutils/nohup.c` | `BB_EXECVP` | nohup |
| `debianutils/start_stop_daemon.c` | `execvp` | start-stop-daemon |
| `e2fsprogs/old_e2fsprogs/mke2fs.c` | `system`, `popen` | mke2fs |
| `editors/awk.c` | `system`, `popen` | awk |
| `editors/vi.c` | `system` | vi |
| `init/init.c` | `BB_EXECVP` | **init** |
| `loginutils/adduser.c` | `system`, `BB_EXECLP` | adduser |
| `loginutils/getty.c` | `BB_EXECLP` | **getty** |
| `loginutils/login.c` | `run_shell` | **login** |
| `loginutils/su.c` | `run_shell` | su |
| `loginutils/sulogin.c` | `run_shell` | sulogin |
| `mailutils/mail.c`, `mailutils/mime.c` | `BB_EXECVP` | sendmail, reformime |
| `mailutils/popmaildir.c` | `popen` | popmaildir |
| `miscutils/chrt.c` | `BB_EXECVP` | chrt |
| `miscutils/crond.c` | `execl`, `execlp` | crond |
| `miscutils/crontab.c` | `BB_EXECLP` | crontab |
| `miscutils/man.c` | `system` | man |
| `miscutils/setsid.c` | `BB_EXECVP` | setsid |
| `miscutils/taskset.c` | `BB_EXECVP` | taskset |
| `miscutils/time.c` | `system`, `BB_EXECVP` | time |
| `networking/ifupdown.c` | `execle` of `sh -c`, `BB_EXECVP` | ifup, ifdown |
| `networking/inetd.c` | `BB_EXECVP` | inetd |
| `networking/nc.c`, `networking/nc_bloaty.c` | `BB_EXECVP`, `execvp` | nc |
| `networking/slattach.c` | `system` | slattach |
| `networking/tcpudp.c` | `BB_EXECVP` | tcpsvd, udpsvd |
| `networking/telnetd.c` | `BB_EXECVP` | **telnetd** |
| `printutils/lpd.c` | `BB_EXECVP` | lpd |
| `procps/watch.c` | `system` | watch |
| `runit/chpst.c` | `BB_EXECVP` | chpst |
| `runit/runsv.c` | `execvp` | runsv |
| `runit/runsvdir.c` | `execlp` | runsvdir |
| `selinux/runcon.c` | `execvp` | runcon |
| `shell/bbsh.c`, `shell/hush.c`, `shell/lash_unused.c` | `execvp` | hush |
| `shell/cttyhack.c` | `BB_EXECVP` | cttyhack |
| `util-linux/mdev.c` | `system` | mdev |
| `util-linux/script.c` | `execl` | script |
| `util-linux/setarch.c` | `BB_EXECVP` | setarch, linux32, linux64 |
| `networking/udhcp/files.c` | `system` | **udhcpd — PATCHED, see § 4** |
| `networking/udhcp/script.c` | `execle` | **udhcpc — EXEMPT, see § 4** |

Five are among the vendor image's own fifty applets and they are the five this
build drops for this rule: **getty, init, login, nice, telnetd**.  The remainder
were never in the image.

`ash` IS in this build and is a command interpreter.  That is not a contradiction
of the rule: the rule is about what a *process rlxfw wrote* hands to an
interpreter.  What is gone is any such hand-off; the operator's shell stays.

## 4  udhcpc and udhcpd (the plan's item 1)

The vendor firmware's DHCP client and server are **separate executables**, and
its `/bin/udhcpd` imports `system`.  Both are applets here instead.

**udhcpd's lease-notify hook is removed in source**, not left unconfigured:
`config/busybox-patches/0001-udhcpd-drop-notify_file-system-hook.patch`.  With it
left in, the linked ELF held `0041b060 W system` and `0041c280 T execl` — because
`write_leases()` calls `system()`, and uClibc 0.9.30 implements `system()` as
`execl("/bin/sh", "sh", "-c", line, NULL)`, so one call site puts both a shell
interpreter and a variadic exec into the image.  Nothing in rlxfw's own
configuration could reach it (`server_config` is a zero-initialised static and
`notify_file` is one of the six udhcpd.conf keywords that get no compiled-in
default), and that is exactly why the run-time argument is not good enough:
*"the config does not reach it"* is a property of a file in a writable `/var`,
while *"the code is not there"* is a property of the bytes, and `R7` proves its
claim on the bytes.  量 after the patch: `system`, `popen`, `pclose`, `execl`,
`execlp`, `execvp` are all absent from the symbol table.  量 under qemu: udhcpd
starts, parses a conf file containing a `notify_file` line, says nothing about it
and runs nothing.

**udhcpc's script exec survives, by name, with a control.**
`networking/udhcp/script.c`'s `udhcp_run_script()` is
`execle(client_config.script, client_config.script, name, NULL, envp)` — a
two-element argv built from a typed path and one of four literal event names, no
shell and no PATH — and `SPEC-R7` § 3 depends on it (`udhcpc -i <wan> -s
/sbin/ifupd`).  `CONFIG_UDHCPC_DEFAULT_SCRIPT` is set to `/sbin/ifupd` so the
path is compiled in rather than typed on a command line.  `G6` refuses the build
if any object other than `networking/udhcp/script.o` references `execle`, **and
refuses equally if nothing does** — the exemption cannot outlive its reason.

## 5  What the applet set is, and the size arithmetic

**53 applet names, 43 ash builtins.**  量 two ways that share no code: by running
the binary under `qemu-mips-static` and reading the *Currently defined
functions* block, and by `tools/appletcensus.py extract`, which parses the
applet-name table out of the ELF and never executes anything.  They agree
exactly.

    ash cat cp cut date dmesg dumpleases echo egrep expr false fgrep free grep
    halt head hostname ifconfig ip ipaddr iplink iproute kill killall klogd ln
    logger ls mkdir mount netstat nslookup ping poweroff printf ps reboot renice
    rm route sed sh sleep syslogd tail tr traceroute true udhcpc udhcpd umount
    uptime wc

Against `config/image-commands.tsv`'s 50 applet rows: **9 dropped, 12 added**.
The ash builtin table is a strict **superset** — 43 against 40, nothing dropped,
`command`, `getopts` and `help` added.  `ASH_BASH_COMPAT` is set for exactly that
reason: without it `[[` is missing, and `[[` is a row in that file, so a frozen
card could type a word `cardcheck` allows and this image refuses.  量: 2,500 bytes.

**Size.**  The comparison that matters is not binary against binary, because the
vendor's is dynamic and this one is static.

| | bytes |
|---|---|
| this build, stripped | **447,684** |
| this build, unstripped | 557,462 |
| vendor `/bin/busybox` (dynamic) | 273,332 |
| + `lib/libuClibc-0.9.30.3.so` | 205,452 |
| + `lib/libgcc_s.so.1` | 80,156 |
| + `lib/ld-uClibc-0.9.30.3.so` | 20,704 |
| **vendor total, four files** | **579,644** |

So the swap **removes 131,960 bytes** from the initramfs and four files become
one.  1.64× the vendor binary alone, 0.77× the vendor's four files together.
`.text` is 403,708 bytes.  Dropping `od` and `hexdump` (§ 7) cost 11,160 bytes
of applet set and bought the property in § 7.

## 6  The dropped commands — the real cost

The bench's cards are written against the old table, so each of these is a verb
that works on today's image and does not work on one carrying this busybox.

| dropped | why |
|---|---|
| `getty` | `BB_EXECLP` (§ 3).  Nothing in rlxfw's boot uses it: `/init` execs the shell directly |
| `init` | `BB_EXECVP` (§ 3), and `R7`'s PID 1 is rlxfw's own compiled `/init` |
| `login` | `run_shell()` execs a shell (§ 3).  There is no `/etc/shadow` in this image |
| `nice` | `BB_EXECVP` (§ 3) |
| `telnetd` | `BB_EXECVP` (§ 3), **and** a plaintext remote root shell in a firmware whose gate is about privilege separation |
| `chpasswd` | no hazard import; dropped because rlxfw's credential is `admin.pwhash` in the config store and this image has no account database for `chpasswd` to write.  A verb that appears to work and changes nothing is worse than an absent one |
| `bunzip2`, `bzcat` | no hazard import; dropped as a decompressor of attacker-supplied data with no consumer in this image |
| `ping6` | 讀 the board template, `# CONFIG_IPV6 is not set`.  The applet needs `FEATURE_IPV6`, which would add IPv6 code for a kernel that has no IPv6 socket |

**And two more, by the ruling in § 7 rather than by rule 1:** `od` and
`hexdump`.  They were enabled in the first R7 build, at the owner's request,
and turned off when the manifest's own containment argument turned out to rest
on their absence.  What the bench loses is the only way this image had to read a
file as hex.  What is left for looking at bytes is `cat` (raw, on a
CRLF-translating 38400 8N1 console), `tail -c`, `cut -b`, and `wc -c` for a
length; nothing prints an escape or a hex digit.  Had they stayed, two further
facts about them were worth knowing and are recorded here because the next
attempt will want them: 1.13.4's `od` accepts only BSD-style flags (量:
`od -A d -t x1 -N 8` → *invalid option -- A*; the set is
`-aBbcDdeFfHhIiLlOovXx`), while `hexdump -C -n N` worked.

**`sha256sum` does not exist in 1.13.4** — it is not in `applets.h` at all.
`md5sum` and `sha1sum` do exist and are deliberately **not** enabled: § 7.

Added, for the record: `dmesg`, `dumpleases`, `logger`, `netstat`, `printf`,
`udhcpc`, `udhcpd`, and five that came from sub-options rather than from a
separate decision — `egrep` and `fgrep` (from the grep aliases, which also give
the working `-E` that `SPEC.md` `FW-42` measured absent on the vendor build —
量 here: `grep -E 'b(e|a)ta'` matches) and `ipaddr`, `iplink`, `iproute` (from
`FEATURE_IP_SHORT_FORMS`).

## 7  H601: what the applet set can and cannot reach, and the guard that enforces it

`config/rlxfw-initramfs.tsv` declares `/dev/mtd0ro` (`c:90:1`, mode 0400), which
spans the loader **and** `H601` — this unit's MAC and radio calibration, whose
bytes and whose sha256 `CLAUDE.md` forbids from entering this repository at all,
tracked or untracked.  A console capture lands under `bench/` and then in git.
That file's containment sentence is *"量, two routes: this userspace has no
dd/md5sum/od/hexdump/cmp/cksum/sum/sha1sum among its fifty applets, so nothing
here reads a byte of H601 and compares it to anything"*.

**The first R7 build enabled `od` and `hexdump`.**  That put a one-command path
from the node to a committed file, and it is why they are off now: the
image-level property is worth more than the convenience, because it holds
without anyone having to remember a rule.

### 7.1  The audit — can any remaining verb dump bytes?

量 2026-09-30, by running the binary under `qemu-mips-static` against a 6-byte
fixture chosen for the cases a reconstruction has to survive: `41 00 0a ff 1b 42`
(a NUL, a newline, a high byte and an ESC).  Every reading has a positive
control, because a verb that prints nothing looks exactly like a verb that is
not there.

| verb | can it encode arbitrary bytes printably? | 量 |
|---|---|---|
| `od`, `hexdump` | — | `applet not found` |
| `strings`, `xxd`, `base64`, `uuencode`, `uudecode`, `awk`, `vi`, `ed`, `dd`, `md5sum`, `sha1sum`, `sha256sum`, `cksum`, `sum`, `cmp` | — | none is in the 53 |
| `sed -n l` | **no** | it parses and prints **nothing**.  Control: `p` prints `AB`, and `L` answers *unsupported command*, so the parser is working and `l` is a silent no-op in 1.13.4's sed |
| `sed 's/A/\x41\x42/'` | **no** | emits the literal `x41x42` — no `\x` output escape |
| `tr` | **no** | byte→byte, length-preserving; `-d`/`-s` only shorten.  It cannot expand one byte into two printable ones |
| ash `read` + `printf %d` | **no**, and this is the one worth naming | `read` has **no `-n`** (rc=2), and a shell variable is a NUL-terminated C string: 量, `while read -r l; do printf '[%s]' "$l"; done` over the fixture prints exactly `[A]` — everything from the NUL on is gone.  The classic shell byte-dumper does not exist in this build |
| `cat -v` | **no** | `invalid option -- v` |
| `wc -L`, `wc -c`, `ls -l` | **no** | they answer with a length, never with content |
| `printf '\101'` | not a read path | it can *emit* arbitrary bytes; it cannot read a file |

**What remains, stated as what it is.**  `cat`, `tail -c`, `cut -b` and
`grep <pattern>` all put **raw** bytes of an arbitrary file on the console, and
`cat` cannot be removed — `K5` reads `/proc/cpuinfo` with it and the capture
corpus holds 412 `cat` sends.  Raw bytes in a capture are reconstructable.  So
the property this build has is **narrower** than the manifest's sentence:

> no applet can turn arbitrary bytes into a printable, lossless form, and none
> can digest them.

🔴 And the manifest's sentence was already slightly too strong before R7:
`grep -c <byte>` is a **per-byte oracle** (量: `0x41` → 1, `0x43` → 0 on the
fixture), which is a comparison, and `sed -n '/pat/p'` is the same class.  An
oracle reconstructs content in O(256·N) queries and is exactly how a guess at
H601's MAC would be confirmed.  Naming that is the point; nothing here closes it.

### 7.2  The guard, because a list nobody re-checks is not a control

`tools/mkinitramfs.py` `check_no_h601_dumper` — a build-time refusal, at the same
one call site as the flash-write node ban:

* **If** the declaration carries any mtd device node (major 31 or 90 — *any*,
  because which partition a minor lands on is the driver's registration order,
  and that file's own `/dev/mtd2ro` row says so),
* **then** no `file` entry may be a multi-call binary whose **applet table**
  holds one of `H601_DUMPER_APPLETS`.  The table is read out of the built ELF
  with `tools/appletcensus.py`, never out of a `.config`: the question is what
  the shipped bytes can do.
* An applet table that cannot be read is a **refusal**, not a zero — a count of
  zero dumpers from a parser that found no table is not a measurement.

Controls, both directions, in `mkinitramfs.py self-test` (43 → 47 cases):

| | |
|---|---|
| `H1` | an mtd node + a busybox whose table holds `hexdump` → refused, and the refusal names `hexdump` |
| `H2` | the same node with this build's table → **accepted** (the control that stops `H1` passing on a ban that refuses everything) |
| `H3` | `hexdump` with **no** mtd node → accepted; the rule is conditional, as the ruling says |
| `H4` | an unreadable applet table + an mtd node → refused, not reported as zero |

Two mutants in `tools/test-mkinitramfs-mutants.py` (27 → 29) kill `H1` and `H4`.
量 beside the controls, on the real artefacts rather than on fixtures: the
vendor binary (50 applets) and this build (53) are both **permitted**; the same
build with `od` spliced into its applet table is **refused**.

🔴 `B0` — *the unmutated tool must pass in the temp tree* — went red the first
time, because `mkinitramfs.py` now imports `appletcensus.py` and the mutation
suite copied the subject alone.  Five controls failed (`H1`, `H2`, `H4`, and
`A25`/`A26` through the mtd nodes they declare).  That is `B0` doing its job;
`make_tree` copies the companion now and its docstring says why.

### 7.3  What is still owed

The guard covers the encoder class.  It does not cover `cat /dev/mtd0ro`, and
nothing can at the applet level.  That guard belongs in `tools/cardcheck.py` —
a refusal on any `/dev/mtd*` path as an argument to any command, which is
narrower than the command table and catches `cat` and `grep` too.  It does not
exist.

## 8  GPL

busybox is **GPLv2**.  Shipping this binary in a release obliges rlxfw to offer
the corresponding source: the pinned drop (`SOURCES.json`,
`rtl819x-toolchain` at `5c9be5d943318fdb4d048ae22078129594eb5a10`),
`config/busybox-patches/`, `config/rlxfw-busybox.config` and
`tools/mkbusybox.sh` — the recipe is not optional, it is part of the *scripts
used to control compilation and installation*.  All four are committed, which is
what makes the obligation dischargeable rather than a promise.  Assembling and
publishing the offer is `P4b`'s; this section exists so `P4b` inherits a list
rather than a search.

## 9  What this does NOT establish

* **Nothing about the silicon.**  Every applet reading here was taken under
  `qemu-mips-static`, which certifies logic and never codegen or the ISA — the
  repository's own rule.  This binary has not run on the die.  The first boot
  carrying it is the real test, and until then every claim here is about a file.
* **`hazlint` 0 is one hazard class over the words it can reach.**  It scans
  `SHF_EXECINSTR` sections linearly; 44 KB of this ELF is named as not scanned
  because it is not executable, and the load-use rule is not the only way this
  core can be miscompiled.
* **The applet table holding a name is not the applet working.**  `SPEC.md`
  `FW-42` measured `grep` present and `grep -E` absent on the vendor build; the
  same trap applies here in the other direction, and § 6's `od -A` finding is an
  instance of it caught by running the applet rather than by reading the table.
* **§ 7.1 is a census of what this applet set can do, not a proof that no path
  exists.**  Every row was measured with one command; a composition of several
  was not searched for exhaustively, and the `grep` oracle shows the search
  space is not empty.  What § 7.2 enforces is the named list, and a verb that
  belongs on it and is not there is a gap nothing here would report.
* **`G6` reads the symbol table of the *unstripped* link.**  The shipped file is
  stripped and has no symbols at all.  What transfers the claim is that both
  files' `.text` is the same 403,708 bytes with the same sha256 (量), so the
  symbol table describes the shipped code.  A **string scan** would not have
  transferred it: 量, the stripped binary contains the byte string `system`
  seven times — *Interrupted system call*, *Too many open files in system*,
  *Read-only file system*, *Interrupted system call should be restarted*, *Bad
  system call*, `/etc/filesystems`, `/proc/filesystems` — every one of them
  uClibc's own prose and not one an import.  A string-scanning instrument reports
  1 where the symbol table reports 0.
* **`G1` proves the source is a second drop's, not that either is upstream
  1.13.4.**  Both drops are Realtek's; if Realtek modified `busybox-1.13` before
  shipping it, both copies carry the modification and this comparison is silent.
  Diffing against busybox.net's own 1.13.4 tarball would settle it and has not
  been done.
* **🔄 2026-09-30, `R7-8`: the image now declares this build.**  The line above
  said `config/rlxfw-initramfs.tsv` still declared the unit's binary.  It does
  not: `/bin/busybox` is `$REPO/build/rlxfw-user/busybox/busybox`, owner
  `rlxfw`, and the eleven `/bin/*` symlinks point at it.  What that step
  measured, so this file does not have to be read for it: the build was run a
  second time straight into `build/` and came out byte-identical (447,684 bytes,
  sha256 `ef057f6e...`), and the decompressed image with the whole R7 userspace
  in it is 4,096,000 bytes against the 5,242,880 ceiling.  The manifest's
  containment paragraph was rewritten to § 7.1's narrower claim and now cites
  this file instead of restating its table.  What is still owed is unchanged and
  is § 7.3's: a `cardcheck` refusal on a `/dev/mtd*` argument, which does not
  exist.
