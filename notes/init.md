# rlxfw's PID 1 and `ifupd`

R7, segment 118, 2026-09-30.  Owner of: the boot sequence, the mount table, the
supervision policy, the bench-shell decision, and `ifupd`'s event table.
Sources: `src/init/`, `src/ifupd/`, `src/lib/netutil.{c,h}`.

**Written before anything in it had run on the device**, so every number here is
讀 (read out of a source tree, a `.config` or a built artefact) or a desk
measurement of a host build.  🔄 Both programs have since run on the die: 量
2026-09-30, image `r78a` from RAM, PID 1 is `/init` (`FW-175`), and `ifupd`
applied one hand-fed lease and refused two by name (`FW-181`);
`notes/userspace-integration.md` § 7 owns those readings.  What is 量 on the
silicon is quoted from `SPEC.md` and marked.

## 1. What replaced what

`config/rlxfw-init.sh` — four commands and an `exec /bin/sh`, the `/init` of
every seating since R3 rung 1 — is replaced by a compiled `/init`.  The old
script and `config/rlxfw-init-quiet.sh` are left in the tree; the image stops
pointing at them.  `plan/` § D7 is the reason: the claim R7 is built to support
is `system()`/`popen()` = 0 across the rootfs, and the plan's own baseline
sentence puts shebang files and shell scripts beside it (`plan` L1479-1482).
A `#!/bin/sh` `/init` is a shell script in the shipped image.

## 2. The boot sequence

1. **stdio onto the console.**  `open("/dev/console", O_RDWR|O_NOCTTY)`, then
   `dup2` onto 0, 1, 2.  Done unconditionally, because the kernel's own attempt
   only *warns* when it fails (`init/main.c:818`) and `# CONFIG_PRINTK is not
   set` makes that warning print nothing — a PID 1 with no stdio reads exactly
   like a hang.  Falls back to `/dev/null`.
2. **The rung-1 discriminator**, byte for byte:
   `rlxfw: init running, RLXFW-R3-RUNG1-OK`.  It must be the first line and it
   must not change: `tools/bootbytes.py` compares it across every committed
   rlxfw boot and `RUNSHEET.md` B5/P6 checks that this unit's own kernel and
   rootfs do not contain it.
3. **Signals.**  A self-pipe, then `sigaction` for `SIGCHLD`, `SIGTERM`,
   `SIGINT`, `SIGUSR1`, `SIGHUP`; `SIGPIPE` ignored.  The handler writes one
   byte and nothing else.  PID 1 carries `SIGNAL_UNKILLABLE`
   (`init/main.c:824`) and the kernel discards signals to it that have no
   handler, so an unhandled signal is safe and a handled one has to be installed
   before the first `fork`.
4. **The mount table** (§ 3), then `mkdir` of `/var/lib` 0700, `/srv`,
   `/srv/www`, `/usr`, `/usr/sbin`, `/sbin` 0755.  `/var/lib` is created *after*
   `/var` is mounted, or the mount would hide it.
5. **The config store**, by linking `cfg.h`'s loader directly.  PID 1 does not
   `execve` `cfgstore` to read its own configuration: a supervisor that needs a
   child in order to decide what to supervise has a bootstrap loop in it.
   A store that is absent or invalid gives the § 4 defaults with `source = 0`,
   and one console line saying so.
6. **`sethostname`** from `sys.hostname`, charset re-validated here.
7. **The LAN.**  The six `/proc` verbs `config/rlxfw-init.sh` writes, in its
   order — `unlock i-mean-it`, `init`, `vlan` (since `R6c`), `start` to `/proc/rtl819x-switch`, then
   `unlock`, `netdev on` to `/proc/rtl819x-nic` — each a `write(2)` of a
   compile-time literal to a compile-time path.  Switch core first, because
   B43's control shows `rlx0` carries nothing without it.  Then
   `SIOCSIFADDR`, `SIOCSIFNETMASK`, `SIOCSIFFLAGS` on `rlx0` from
   `lan.ipaddr`/`lan.netmask`.  Address *before* mask: `SIOCSIFADDR` resets the
   mask to the class default, so a mask written first is thrown away.
   `-DRLXFW_SWITCH_BRINGUP=0` writes no `/proc` node and opens no interface,
   which is what `R6b`'s `NET-25` needs (eth4 first after power-on).
8. **`/var/udhcpd.conf`**, built whole in a 240-byte bounded buffer and written
   once.  Every byte is a literal from that function or the decimal form of a
   `uint32_t`; no config STRING reaches it, so no SET can turn a value into a
   udhcpd directive.
9. **The bench shell decision** (§ 5), then the child table (§ 4), then the
   loop: reap everything ready, act on a pending signal, start what is due,
   `poll` the self-pipe until the next due time.

No step aborts the boot.  PID 1 exiting means `Attempted to kill init`, so
"abort" can only mean a panic, and a console with a loud line on it beats a
panic.  A failed *required* mount raises a degraded count and prints
`DEGRADED BOOT`; it does not stop anything.

## 3. The mount table

| src | target | fs | flags | data | required |
|---|---|---|---|---|---|
| proc | `/proc` | proc | nosuid,nodev,noexec | — | yes |
| sysfs | `/sys` | sysfs | nosuid,nodev,noexec | — | no |
| tmpfs | `/var` | tmpfs | nosuid,nodev | `mode=0755` | yes |
| tmpfs | `/run` | tmpfs | nosuid,nodev | `mode=0755` | yes |
| tmpfs | `/tmp` | tmpfs | nosuid,nodev | `mode=1777` | no |
| tmpfs | `/srv/www/run` | tmpfs | nosuid,nodev | `mode=0755` | no |

`EBUSY` counts as success (already mounted).  `required` selects the loudness
and the degraded bit, nothing else.

**devtmpfs or a static `/dev`: it is a static `/dev`, and that is measured.**
讀, with Linux 5.4.27 in `src-vendor/shibajee-linux-rtl8196e` as the positive
control that has all of it: devtmpfs was merged in 2.6.32, so in this 2.6.30
drop `drivers/base/devtmpfs.c` does not exist, `CONFIG_DEVTMPFS` is not a symbol
in any `Kconfig`, and the built `System.map` and `strings vmlinux` hold zero
`devtmpfs` lines.  So `/dev` is the set declared in
`config/rlxfw-initramfs.tsv`, **nothing is mounted on `/dev`**, and a test in
`src/init/test_mounts.c` asserts no row targets `/dev` or anything under it —
a filesystem mounted there would hide the console node and the boot would go
silent.

🔴 **"tmpfs" here is ramfs, and there is no size limit.**
`# CONFIG_TMPFS is not set` and `# CONFIG_SHMEM is not set`, yet
`mount -t tmpfs` works: `mm/shmem.c`'s `#else !CONFIG_SHMEM` branch registers a
`tmpfs_fs_type` whose `get_sb` is `ramfs_get_sb` (confirmed by dumping the
struct out of `vmlinux`'s `.data`: the name pointer resolves to "tmpfs",
`get_sb` to `ramfs_get_sb`, `kill_sb` to `kill_litter_super`).  And
`fs/ramfs/inode.c`'s option table is `mode=%o` and nothing else, with **no
`default:` in its switch** — every other option is silently ignored.  So a
`size=512k` would read as a limit and be none.  It is not written.  Each of
these four mounts can grow until the board is out of RAM (~26 MB), and
`simple_statfs` means `df` cannot show it.  `test_mounts.c` asserts no row
carries a `size=`.  Bounding them needs `CONFIG_TMPFS` and `CONFIG_SHMEM`,
which is a kernel change and not this file's to make.

## 4. Supervision

Children, in start order, from SPEC-R7 § 3:

| name | binary | argv | started when |
|---|---|---|---|
| brokerd | `/usr/sbin/brokerd` | `brokerd` | always |
| httpd | `/usr/sbin/httpd` | `httpd` | always |
| dnsfwd | `/usr/sbin/dnsfwd` | `dnsfwd` | always |
| udhcpd | `/bin/busybox` | `udhcpd -f /var/udhcpd.conf` | `dhcpd.enable` = 1 |
| udhcpc | `/bin/busybox` | `udhcpc -f -i <wan> -s /sbin/ifupd` | `wan.mode` = 1 |
| shell | `/bin/sh` | `sh` | the bench profile (§ 5) |

Every child is `fork` + `execve` with an argv of string literals and a fixed
three-entry environment (`PATH`, `HOME`, `TERM`).  Not one argv byte comes from
the config store, a lease, or the kernel command line.  There is no `system`,
`popen`, `execl*`, `execvp` or `sh -c` anywhere in either program: 讀 `nm` over
the linked target ELFs, `init` links `execve` and nothing else of that family,
and **`ifupd` links no `exec*` symbol at all**.

`-f` on both busybox applets is not in SPEC § 3's argv and has to be: without
it they background themselves, and a supervisor handed an immediately-exiting
parent counts a fast failure every time.

**States.**  `SV_OFF` (its config key says no), `SV_ABSENT` (its binary is not
on the image — one `access(path, X_OK)` before the first start, so a missing
daemon costs one console line instead of eight `execve` failures), `SV_WAIT`,
`SV_RUNNING`, `SV_GIVENUP`, `SV_STOPPING`.

**The policy and its constants** (`src/init/supervise.h`):

| | | |
|---|---|---|
| `SV_RUNOK_MS` | 10,000 | a child that stayed up this long is healthy: its consecutive-failure count and its backoff both reset |
| `SV_BACKOFF_MS` | 250 | the first fast failure waits this long |
| `SV_BACKOFF_MAX_MS` | 16,000 | and the wait doubles to here and stops |
| `SV_FAIL_MAX` | 8 | consecutive fast failures, then `SV_GIVENUP` |
| `SV_TERM_MS` | 2,000 | how long shutdown waits after `SIGTERM` before `SIGKILL` |

So the sequence is 250, 500, 1000, 2000, 4000, 8000, 16000 ms — 31,750 ms of
backoff, about 32 s of trying — and then one loud line and no more restarts.
A child that exits 0 in under `SV_RUNOK_MS` is a fast failure like any other: a
daemon's job is to stay up, and `exit(0)` at once is the shape of a daemon that
cannot parse its own config.  What differs is the record (`exited`, `exit_code`,
`signo`) and the console word.

Reaping is `waitpid(-1, &st, WNOHANG)` in a loop until it returns ≤ 0, so an
orphan the kernel reparented to PID 1 is reaped and otherwise ignored.  PID 1
leaves no zombie.

**Signals.**  `SIGTERM` and `SIGINT` → reboot.  `SIGUSR1` → poweroff.
`SIGHUP` → re-read the config store and re-arm every `SV_GIVENUP` child.
`brokerd`'s REBOOT op can therefore be `kill(1, SIGTERM)` as well as its own
`sync` + `reboot`.

**Shutdown ordering**, and `test_supervise.c` asserts it on an ordered event
log: `SIGTERM` every running child → reap for up to `SV_TERM_MS` → `SIGKILL`
what is left → `sync()` → `reboot()`.  `sync` appears exactly once, `reboot`
exactly once, `sync` before `reboot`, and nothing after `reboot`.

🔴 **This SoC cannot power itself off.**  讀 `arch/rlx/bsp/setup.c`:
`RB_AUTOBOOT` reaches `bsp_machine_restart`, which sets `BSP_WDTCNR = 0` and
spins — a watchdog bite, and 量 (`SPEC.md` `FW-37`) `busybox reboot -f` resets
this board to the loader prompt in 2.407 s.  But `RB_POWER_OFF` reaches
`bsp_machine_power_off` and `RB_HALT_SYSTEM` reaches `bsp_machine_halt`, and
**both are `while (1);`** — `pm_power_off` is set, so there is not even the
usual degrade to halt.  On a console that looks exactly like a crash, so the
poweroff path prints `PULL THE POWER` before it takes it.

**The clock** is `clock_gettime(CLOCK_MONOTONIC)`.  讀: it is in `libc.a`
itself in this sysroot (member `clock_gettime.os`, a bare `__NR_clock_gettime`
= 4263 syscall), so a static uClibc 0.9.30 link needs no `-lrt`.  `times()` was
the first choice and is wrong: its return carries the kernel's
`INITIAL_JIFFIES` offset of `-300 * HZ` (`include/linux/jiffies.h:171`), so it
starts near −30,000 and legitimately returns −1 at about 299.99 s of uptime,
which the usual `(clock_t)-1` error check reads as a failure.  Granularity is
10 ms (clocksource `jiffies`, HZ = 100, no hrtimers, no NOHZ); every constant
above is a multiple of 50 ms.

## 5. The bench shell

**Default for R7's first boots: enabled, and announced.**  Two lines, on every
boot, before the shell is forked:

```
rlxfw: init: *** BENCH PROFILE: A ROOT SHELL IS ENABLED ON /dev/console ***
rlxfw: init: *** build with BENCH_SHELL=0, or boot with 'rlxfw.noshell', to remove it ***
```

A router image that silently spawns a shell on its UART is the vendor's
mistake.  Three ways to decide, and the asymmetry is deliberate:

* `make -C src/init target … BENCH_SHELL=0` — compiled out.  The disabled build
  prints `bench profile OFF: no shell on /dev/console`, so a capture says which
  build it is either way.
* `rlxfw.noshell` on the kernel command line — turns it **off** in a build that
  has it.
* Nothing turns it **on** in a build that does not have it.  A door a command
  line can open is a door.

The shell child gets its own session and a controlling terminal, so job control
works and `^C` reaches the shell (today's `exec /bin/sh` from a script has no
ctty at all, so `^C` does nothing).  It opens `/dev/ttyS0` first and
`/dev/console` second: `CONFIG_CMDLINE` is `console=ttyS0,38400`, so `ttyS0` is
the real device and `/dev/console` is the redirector, and `TIOCSCTTY` on the
redirector is not something this kernel has been shown to honour.

🔴 **This changes bytes a tool depends on.**  `tools/looprun.py`'s
`DEFAULT_BOOT_UNTIL` is `job control turned off[^#]{1,2}# `, and a shell WITH a
controlling tty never prints that line.  Every `looprun` on an image carrying
this `/init` needs `--boot-until`.

## 6. Mutation controls

`make -C src/<prog> mutants O=…` runs the unmutated suite first — a mutation run
on a red suite says nothing — then mutates a **copy** under `$O/mut/`, rebuilds,
and requires the suite to go red.  A mutant the suite still passes is printed as
`HOLE` and exits non-zero.

| | mutation | what goes red |
|---|---|---|
| **M1** | `src/init/supervise.c`: `if (c->fails >= SV_FAIL_MAX)` → `if (0)` — the crash-loop cap removed | `test_supervise` 14 checks, including `T-CAP-TERMINATES`'s `guard < 1000` |
| **M2** | `src/lib/netutil.c`: `return -NU_E_MASK;` → `return p;` — the netmask contiguity check removed | `test_netutil` 8 checks, starting with `nu_mask_prefix(0x00FF00FF) == -NU_E_MASK` |

`T-CAP-TERMINATES` is written as a **bounded** loop (1,000 iterations, 125× the
cap) rather than "restart until it stops".  Without the cap the unbounded
version hangs, and a hang is not a test result; the bounded one fails in finite
time and names the constant it failed on.  What the bounded form gives up: it
shows the assertion going red, not the hang itself.

## 7. `ifupd`

`/sbin/ifupd <event>`, `execve`'d by `udhcpc -s`.  It is the compiled
replacement for busybox's `/usr/share/udhcpc/default.script`, and that script —
a shell script whose inputs come from a DHCP server — is the direct conflict
with D7's "no shell".

| event | what happens |
|---|---|
| `bound` | apply `ip` and `subnet`, bring the interface up, delete then add a default route via `router`, rewrite `/run/wan.dns` |
| `renew` | identical to `bound`; the delete-before-add is what keeps a moved gateway from leaving two default routes |
| `deconfig` | bring the interface **up** (udhcpc cannot DISCOVER on a down interface), set the address to 0.0.0.0, truncate `/run/wan.dns` |
| `nak` | as `deconfig` |
| `leasefail` | as `deconfig`.  busybox sends it, and a firmware that called an unknown event fatal would log a refusal on every failed DISCOVER |
| anything else | refused, `unknown-event`, exit 2, **no ioctl issued** |

Exit status: 0 applied, 1 applied in part, 2 refused, 3 usage.  One console
line always, so a refused lease and an applied one are equally visible in a boot
capture.

### 7.1 What is hostile, and how it is bounded

The environment is chosen by whoever answers the DISCOVER on the WAN.  The rules:

* **Five names are read**: `interface`, `ip`, `subnet`, `router`, `dns`.
  `mtu`, `lease`, `domain`, `hostname`, `serverid` and everything else are never
  looked at, so they cannot be mis-parsed.  The test table sets `mtu=$(reboot)`,
  ``domain=`id` `` and `lease=; rm -rf /` on every row.
* **Every read is length-bounded before the value is examined.**  A 4 KB
  `subnet` costs sixteen byte reads and `subnet-too-long`.  `dns` is scanned for
  at most `IFU_DNS_SCAN` = 256 bytes and bytes past that are never read.
* **Everything that survives is a `uint32_t`.**  Nothing that reaches an
  `ioctl` or a file is a copy of an environment byte.
* **`ip`, `subnet` and `interface` are all validated before the first
  `ioctl`**, so a refusal leaves the interface exactly as it was.  The test
  table is 43 rows — 26 refusing, 5 partial, 12 applied — and it asserts
  `n_ioctl == 0` on every one of the 26.
* **One deliberate partial**: a bad `router` does not throw away a good address.
  The address and mask are applied, the route is refused by name, and the result
  is `IFU_PARTIAL`.  Refusing the whole lease because the gateway is bogus would
  leave a working address unused.
* **`/run/wan.dns` is data, not a script.**  Each line is produced by
  `nu_format_ipv4` from a `uint32_t`, so the file's whole byte alphabet is
  `[0-9.\n]` by construction, and a test asserts it byte by byte.  It is written
  to `.tmp` and `rename`d, so a reader never sees a half-written list.

Named refusals: `unknown-event`, `no-interface`, `interface-too-long`,
`bad-ifname`, `no-ip`, `ip-too-long`, `bad-ip`, `ip-not-unicast`,
`ip-is-network-or-broadcast`, `no-subnet`, `subnet-too-long`, `bad-subnet`,
`bad-netmask`.  Named partials: `addr-ioctl-failed`, `mask-ioctl-failed`,
`bad-router`, `router-unparsable`, `gw-not-unicast`, `gw-off-subnet`,
`gw-is-self`, `route-ioctl-failed`.

`src/lib/netutil.c`'s parser exists because `inet_aton` accepts `1.2.3`,
`0x7f.1`, `017.1.1.1` and `1.2.3.4 ` — four shapes that mean different things to
different resolvers.  This one takes exactly four decimal octets of one to three
digits with no leading zero, single dots, nothing before and nothing after, and
gives every other shape **its own error code**, because a test that only asserts
"refused" cannot tell a refusal for the right reason from one for the wrong
reason.

## 8. What this does NOT establish

* **What ran on the device is narrower than what this file describes.**  Both
  programs have executed on the RTL8196E since it was written (量 2026-09-30,
  `FW-175`, `FW-181`); the readings are their boot lines, `ps`, one respawn of
  `brokerd` and `httpd` after a `kill`, and three hand-fed leases, one applied
  and two refused (`docs/GATE-RESULTS.md` entry 17).  Every other claim here is
  讀 or a host measurement.  The host tests run on little-endian x86-64 with
  glibc; the target is big-endian MIPS-I with uClibc 0.9.30, and `plan` D14 is
  explicit that a host test verifies logic and not codegen.
* **No service dependency ordering beyond start order.**  Children start in
  table order and nothing waits for anything.  `brokerd` may not have its socket
  up when `httpd` first connects; `httpd`'s client code has to cope.  There is
  no `sysinit`, no `After=`, and no readiness protocol.  Adding one is a design
  change, not a tuning knob.
* **The config store was built against a stub.**  `src/lib/cfg.c` did not exist
  when this was written (量, s118 2026-09-30: `ls src` → no such file), so
  `src/init/stub/cfg.c` transcribes SPEC-R7 §§ 4–5 and the Makefile prints which
  loader it used on every build.  If the spec's record layout is wrong, the stub
  is wrong the same way, which is not a second source.  A mismatch degrades to
  the defaults, not to a wrong address.
* **`SIOCADDRT` has never been issued on this board**, by anything.  Whether the
  `rtl819x-nic` netdev accepts a default route through it is 未定.
* **No WAN interface is proven to exist.**  `RLXFW_WAN_IF` defaults to `eth4`
  and is 未定 pending `R6-6` (per-port VLAN, not met).  `wan.mode` defaults to
  0, so `udhcpc` is not started and the name is never used — which also means
  `ifupd` has never been invoked by `udhcpc`, only by its own tests and, on the
  device, by hand (`FW-181`).
* **`udhcpd` runs and `udhcpc` never has.**  🔄 This bullet used to say neither
  existed, which was true of the unit's own busybox; rlxfw's busybox enables
  both (讀 `config/rlxfw-busybox.config`, and `config/image-commands.tsv` lists
  both applets), and 量 2026-09-30 `ps` showed `udhcpd` running as root
  (`FW-175`).  `udhcpc` is not started while `wan.mode` is 0, so it has never run
  on this board (`docs/GATE-RESULTS.md` entry 17).
* **The tmpfs mounts are unbounded** (§ 3), and nothing measures how much RAM
  they take.
* **`reboot(RB_POWER_OFF)`'s behaviour on this SoC is 讀, not 量.**  Nothing has
  issued it.
* **hazlint's 0 is about the sites, not about the hazards.**  It is 0 violations
  in 1,502 loads for `init` and 894 for `ifupd`; whether this core would have
  mis-executed a violation is `TC-h`, still open.
