# R7's userspace, reconciled into one tree — what the integration measured

`R7-8`, segment 118, 2026-09-30. Seven programs were written in parallel against
`SPEC-R7`'s pinned interfaces, each in its own clone, each with a local stub where
another agent's file did not exist yet. This file owns what happened when the stubs
came out and the real files went in: the disagreements, the ones that turned out to
be real defects, and the checks that settled each. Section 7 owns the other half,
what the first boot of the result measured on the board.

It does not own the programs' designs (`notes/init.md`, `notes/config-store.md`,
`notes/broker.md`, `notes/httpd.md`, `notes/dnsfwd.md`, `notes/busybox-build.md`,
`notes/rlxboot.md` do), and it does not own the image (`config/rlxfw-initramfs.tsv`
does).

## 1  The four stub directories, and what each had guessed

`src/brokerd/stub/`, `src/dnsfwd/stub/`, `src/init/stub/` and `src/httpd/stub/` are
deleted. Every Makefile that had a `$(wildcard …)` preferring the real file now
**refuses** when the real file is absent, because a fallback to a file that is not
there is worse than a build that stops.

| stub | what it guessed | the real header | verdict |
|---|---|---|---|
| `brokerd/stub/cfg.h` | `CFG_NKEYS 17`, its comment saying "§ 4's table has 17 rows" | 16 | **wrong**; `struct cfg` was one 64-byte row too long |
| `brokerd/stub/cfg.h` | seven `CFGE_*` numbers (`INVAL 1, NOENT 2, RANGE 3, CROSS 4, IO 5, CRC 6, FORMAT 7`) | eighteen, in a different order; there is no `CFGE_INVAL` | **wrong**, all seven; brokerd only reads the sign, so nothing broke |
| `brokerd/stub/cfg.h` | `uint16_t cfg_last_key(void)`, which `SPEC-R7` § 5 names in a comment and declares nowhere | identical | **right**, signature included |
| `brokerd/stub/cfg.h` | `CFGID_SYS_HOSTNAME / LAN_IPADDR / DNS_UPSTREAM / ADMIN_PWHASH` | spelled `CFG_ID_HOSTNAME / LAN_IP / DNS_UP / PWHASH` | values **agreed**, names did not |
| `init/stub/cfg.h` | `CFG_NKEYS 16` and the key order | identical | **right** |
| `init/stub/cfg.h` | eleven `CFGE_*` numbers, one of them named `CFGE_BOUND` | `CFGE_RANGE`; no `CFGE_BOUND` exists | **wrong**; init reads none of them |
| `init/init.h` | nine § 4 ids as literals | identical | **right**, all nine |
| `init/main.c` | six default values as literals (`0x0A010101`, `0xFFFFFF00`, `0x0A010164`, `0x0A0101C7`, `0x0A010102`, `86400`) | identical | **right**, all six; still a second transcription, see § 4 |
| `dnsfwd/stub/client.h` | `BK_OP_GET`, `BK_OK`, `BK_PERM` | `OP_GET`, `ST_OK`, `ST_PERM` | values **agreed**, names did not |
| `httpd/stub/client.h` | eleven `BK_*` statuses, eight `BK_*` ops, seven size constants | `ST_*`, `OP_*`, `PROTO_*` | values **agreed** on every one, names did not |
| `httpd/stub/cfgtab.c` | all sixteen rows of § 4 — id, name, type, web class, bounds | `src/lib/schema.c` | **identical on every row** |

The `BK_*` and `CFGID_*` names survive as **aliases** in `src/lib/client.h` and
`src/lib/schema.h` — `#define BK_OK ST_OK`, `#define CFGID_LAN_IPADDR
CFG_ID_LAN_IP`. That is not a second transcription: each expands to the one
enumerator, so the numbers are still written once, and the alternative was a
behaviour-free rewrite of two other agents' call sites.

### 1.1  How the table comparison was made, because "by eye" is not a method

Two one-file programs, one compiled against `httpd/stub/cfgtab.c` and one against
`src/lib/schema.c`, each printing one canonical line per row from **its own**
table; `diff` on the two outputs. No third transcription exists anywhere in the
check. The control is a one-field edit to one of the dumps, which the same `diff`
reports — so "identical" is not the answer a blind comparator would also give.
`httpd`'s transcription carried no default column at all, so the sixteen encoded
defaults were read out of `schema.c` alone and are 量 nowhere else.

## 2  Two real defects the reconciliation found

**`BK_KDF_R` was 8.** `src/brokerd/brokerd.h` set the scrypt `r` to 8 while
`src/lib/kdf.h`'s ruling is 7. `kdf_scrypt` refuses any parameter set whose peak
exceeds `KDF_PEAK_CAP` (4,194,304 B) and `(12, 8, 1)` peaks at 4,197,376 — so
`PWSET` would have returned `-KDFE_NOMEM` on **every** call, and a blob already
carrying `r = 8` could not have been verified either. It is now
`#define BK_KDF_R KDF_R`. Nothing measured this before because brokerd's tests
plant a hash rather than deriving one.

**`cfgstore passwd` could not succeed.** `SPEC-R7-8` § 2 asked for a confirmation
that `cfgstore passwd` and brokerd's `LOGIN` both reach the real `kdf_scrypt`.
`LOGIN` does. `passwd` did not: its `if (!KDF_IMPLEMENTED)` refusal was written
when `kdf.h` returned `-ENOSYS`, and the half after it ended in
`"cfgstore: passwd: unreachable"` and `EX_IO`. With the real KDF in the tree the
gate falls through and the command failed with that word. That is not cosmetic:
`admin.pwhash` has **no default**, and httpd's `/api/password` needs a session,
which needs a password — so with `passwd` unimplemented this image could never have
had an admin password at all. It is implemented now: `pwhash_salt` (which refuses
below `entropy_avail` 128 and never returns a weak salt), `pwhash_make`, `cfg_set`,
and the ordinary `commit` path, so the store's two-slot discipline and cross-field
validation apply to a password like to anything else.

`src/cfgstore/test_cli.c`'s group was rewritten rather than deleted. It asserted
three things about the stub's behaviour (exit 3, the word `REFUSED`, the word
`ENOSYS`) and those were the only three failing cases in the tree. It now requires
**either** success — with `admin.pwhash set`, the parameters `log2N=12 r=7 p=1`, and
a `written: slot` line — **or** the entropy refusal, prints which branch ran, and
still checks that a password in `argv` is refused, that under 8 bytes exits 2, and
that `admin.pwhash`'s presence in `get` matches whichever branch it took.

## 3  What was NOT collapsed, and why

`src/lib/proto.c` keeps its own `proto_tlv_put/get` rather than using
`src/lib/tlv.h`. `SPEC-R7-8` § 2 allows the collapse **only if** the semantics are
identical. They are not, in two ways that matter:

* `tlv_write`/`tlv_next` enforce **strictly ascending** types and answer
  `-TLVE_ORDER` otherwise. `proto_tlv_put/get` enforce no ordering at all — and
  they must not, because `SPEC-R7` § 6's `GET` returns "TLVs, same order" as the
  requested ids, which the *caller* supplies and which need not ascend. Collapsing
  would turn a working `GET` with unsorted ids into a refusal.
* `tlv_next` distinguishes a clean end (returns 1) from a truncation
  (`-TLVE_TRUNC`); `proto_tlv_get` returns `-1` for both, so a caller cannot tell
  "no more TLVs" from "malformed".

Both are left in place. Changing either to make them match would be changing
behaviour to make a tidiness claim true.

## 4  Second transcriptions that remain, named rather than fixed

* `src/init/main.c` passes a literal fallback default to each `cfg_ipv4`/`cfg_u8`
  call (`10.1.1.1`, `255.255.255.0`, `10.1.1.100`, `10.1.1.199`, `10.1.1.2`,
  `86400`). 量 all six agree with `schema.c`. They are reached only when `cfg_get`
  answers `-CFGE_UNKNOWN`, which cannot happen for a declared id, so removing them
  is a behaviour change and not a reconciliation.
* `src/brokerd/ops.c` hand-builds the 56-byte `admin.pwhash` blob (alg, `log2N`,
  `r` BE, `p` BE, zero, salt, key at 24) instead of calling `pwhash_make`. 量 the
  layout agrees with `SPEC-R7` § 4.2 and with `kdf.c`. Left alone for the same
  reason.

## 5  The cross-checks two agents flagged as open

* **httpd's § 6 request encoder against `proto.c`'s codec.** Settled, and not by
  re-typing httpd's 48 bytes into a test: the stub's own `bk_call` was made to
  write to a real `AF_UNIX` socket, the bytes were read off the wire, and
  `proto_decode_req` + `proto_encode_req` were required to round-trip them
  byte-for-byte. Three vectors — an empty body with zero tokens, a 7-byte body with
  both tokens set, and a 2,048-byte body with `client_ip` all ones — all identical,
  48/55/2,096 bytes. Control: one flipped version byte, which the decoder refuses
  (`PROTO_E_VERSION`).
* **`src/lib/sha256.c` against `src/rlxboot/sha256b.c`.** Linked into one binary so
  a difference could not be a build difference. Both agree with RFC 6234 on the
  empty message, `abc`, the 448-bit and 896-bit vectors and 10^6 `a`, and with each
  other on 4 MiB of a counter pattern. Control: two different inputs, which the
  comparator reports as a disagreement. `sha256b.h`'s claim that the two are a
  cross-check rather than a duplication is therefore measured, not asserted.

## 6  The image this produced

| | |
|---|---|
| recipe id | `bf182de2` |
| cell | `r78a`, mainline `quiet` variant, `--marks` |
| vmlinux | 4,588,155 bytes, sha256 `831d3d46…` |
| `.init.ramfs` | 1,265,664 bytes (`0x135000`) at vaddr `0x802b3000` |
| decompressed extent | **4,096,000** bytes, 2 PT_LOAD, `0x80000000`–`0x803e8000`; ceiling 5,242,880, margin **1,146,880** (78.1 % used) |
| nfjrom | 1,107,968 bytes, sha256 `bf41e275a66303bad36f67768d8c8642e76ed162be3c572697de38cb919b0b6a` |
| `rlxfw-marks verify` | green: 12 marks once each, 12 witnesses, 1 confirmed absent, absent from 2 vendor artefacts |
| `kconfig-delta check` | green: 70 derived by kconfig, 75 set by rlxfw |

Stripped target sizes, 量 rather than taken from the authors' figures:
`brokerd` 101,172 · `cfgstore` 86,320 · `httpd` 83,820 · `init` 75,128 ·
`dnsfwd` 73,908 · `ifupd` 23,164; **443,512** together. Each is 79 KB above the
sum the authors reported, and the reason is this file's § 1: the stubs were
self-contained, and the real `src/lib` is five translation units for the store and
two more for the KDF. `init` alone grew by 36,204 bytes.

`hazlint`: 0 violations on each of the six, over the unstripped ELF, and
`hazlint --self-test` is 21 passed / 0 failed in the same run, so those zeroes are
a claim rather than a silence.

## 7  What the first boot measured

The image of § 6 was booted once (`J 80500000` from the loader prompt, `RLXFW-ID0=BF182DE2` on
the console, which is § 6's recipe id `bf182de2`) and each program was asked, from the console
and from the host, whether it answers. 量 2026-09-30; the console captures are
`bench/2026-09-30/R78-*`. The host probe is `func78.sh` in `$FWRE_WORK/rebuild/s118/bench/` and it
saved three files: the index page, and the headers and body of `/api/status`. **Two readings were
printed to a terminal by a script that does not save them**, the `POST /api/login` reply (§ 7.3)
and the `dnsfwd` reply (§ 7.5), and a search for their text over `bench/2026-09-30/` and
`$FWRE_WORK/rebuild/s118/` finds only that script. They are 量 by the session that ran it and
cannot be re-derived from a file, and repeating the login one needs a fresh boot, because a
password was set later in this one (`R78-k2`). Marks: 量 is a reading off the device or the
wire, 讀 is read out of the source tree, 推 is inferred and says what would settle it.

### 7.1  brokerd's socket is mode 0666, and the mode bits are not the guard

| reading | value | mark, origin |
|---|---|---|
| the socket, `ls -l` | `srw-rw-rw-`, owner and group `root`, at `/srv/www/run/broker.sock` | 量 `R78-sock` |
| brokerd's own line at start | `brokerd: listening on /srv/www/run/broker.sock mode 0666` | 量 `R78-boot` |
| the default | `mode_t mode = 0666`, changed only by `-m` | 讀 `src/brokerd/main.c` |

**Anything on the box can open this socket, and that is deliberate.** What a peer may do is
decided by `SO_PEERCRED` (the kernel's record of the connecting process's uid) and by the
per-uid op table in `ops.c` (`notes/broker.md` § 2), not by the file's mode, and the mode cannot
carry that decision: three uids must reach the socket (root, `httpd` 100, `dnsfwd` 101),
`connect(2)` on a unix socket needs write permission, and mode bits can name three unrelated
uids only through a group they share. Putting `dnsfwd` in gid 100 would buy `0660` with a group
shared by the two unprivileged daemons inside `httpd`'s chroot, which the comment above the
`/srv/www` rows of `config/rlxfw-initramfs.tsv` calls "a real widening for a decoration"
(`notes/broker.md` § 3 argues the same from the design side). The board shows no such group
today: `/etc/group` has three rows and no members (`R78-pw`, 量).

* **No refusal was returned on the board.** The only peers these captures involve, `httpd` and
  `dnsfwd`, are both in the table, so the refusal side (a uid outside {0, 100, 101}, or uid 101
  asking for more than its two `GET` keys) has only the host's 264-cell authorisation matrix
  behind it (`notes/broker.md` § 9, little-endian compiler). What decides it is a client that
  `setuid`s to an id outside the table before `connect` and expects `PERM` on every op, and one
  running as uid 101 that tries a `SET`.
* **The directory's own mode was not read.** `init` mounts `/srv/www/run` with `mode=0755`
  (`src/init/mounts.c`) and `notes/broker.md` § 3 expects `0711`. That decides who can list it
  and not who can connect, but the two files disagree and the board was not asked.

### 7.2  Who runs as whom

| process | `ps` USER (量 `R78-ps`) | its own line at start (量 `R78-boot`) |
|---|---|---|
| `brokerd` | root | `brokerd: listening on /srv/www/run/broker.sock mode 0666` |
| `httpd` | `httpd` | `httpd: uid=100 gid=100 root=/srv/www sock=/run/broker.sock port=80 conn=8` |
| `dnsfwd` | `dnsfwd` | `dnsfwd: running as uid 101 gid 101; setuid(0) refused (Operation not permitted)` |
| PID 1, `udhcpd`, `sh` | root | none |

The `dnsfwd` line is a trial and not a report: after `setgroups`, `setgid` and `setuid` it calls
`setuid(0)` and requires it to fail (讀 `drop_privs` in `src/dnsfwd/main.c`, 量 the line).
`httpd` makes the same trial in `src/httpd/serve.c`, where `setuid(0)` and `setgid(0)` must both
fail or the process exits before serving, but prints only `getuid()` and `getgid()`; for `httpd`
the board therefore shows the result of the drop (`uid=100 gid=100`, and `ps`) and that it then
served (§ 7.3), not the trial. The console shell is root and is announced by two `***` lines
(`R78-boot`); all three `/etc/passwd` rows carry `/bin/false` (`R78-pw`), so that shell is
`init`'s doing and not a login.

### 7.3  httpd, from the host

| request | reply | mark, origin |
|---|---|---|
| `GET /` | HTTP 200, **3,850** bytes; the saved body is byte-identical (`cmp`) to the repository's `srv/www/index.html`, sha256 `f7afe413…` | 量 the count, `func78.sh`'s `%{size_download}` (terminal line); 量 the `cmp` and digest, run at the desk on the saved `func78-index.html` |
| `GET /api/status` | HTTP 200, 72 bytes: `{"ok":true,"uptime_s":173,"version":"rlxfw-brokerd-1","auth_ready":true}` | 量 `func78-status.hdr`, `func78-status.json` |
| headers on that reply | `X-Frame-Options: DENY`, `Content-Security-Policy: default-src 'self'`, `X-Content-Type-Options: nosniff`, `Cache-Control: no-store`, all four present | 量 `func78-status.hdr` |
| `POST /api/login`, a dummy password | HTTP 401 `{"ok":false,"error":"auth"}` | 量, terminal only |

The 200 for `GET /` is on the terminal line only; the saved body being the page is the stored
evidence that it was served. `no-store` is written on `/api/*` only (`notes/httpd.md` § 2.3), so
the header set on `GET /` was not read and by design would lack it. The `/api/status` body holds
exactly the three rows `STATUS` gives a peer with no session (`uptime_s`, `version`,
`auth_ready`; `notes/broker.md` § 2), which is what the table says uid 100 gets: consistent with
the request having crossed host, `httpd`, the socket, `brokerd` and the op table, and not a test
of the refusal side.

**`auth`, not `noentropy`.** `op_login` tests the entropy gate before the rate limit and the hash
and answers `NOENTROPY` (503 `noentropy` at `httpd`, `notes/httpd.md` § 2.1) while it is closed,
so a 401 means it had opened: `auth_ready` is sticky, set the first time `entropy_avail` is seen
at 128 or more (`src/brokerd/brokerd.h`), and it read `0` at start (`R78-boot`) and `true` in
this probe's `/api/status`. What refuses next is the missing password: with no `admin.pwhash`
the op answers `AUTH` and counts no failure ("No password set -> AUTH" in its own comment),
which is the fail-closed case. **That this branch produced the 401 is 推**, since a wrong
password against a stored hash answers `AUTH` too. It is likely: `cfgstore show` read
`admin.pwhash <unset>` at 12:33:49 (`R78-cfg1`), the probe ran within fifteen seconds of that,
and no capture sets the hash before the first `cfgstore passwd` (`R78-k2`, 12:41:49). A fresh
boot, with the reply saved to a file, settles it.

### 7.4  cfgstore

| step | console | mark, origin |
|---|---|---|
| `cfgstore show` | `store /var/lib/cfg.bin  bytes 0  source default  seq 0`; both slots `too few bytes for the record (seq 0)`; sixteen keys, each `default` at `SEQ` 0, `admin.pwhash` `<unset>` | 量 `R78-cfg1` |
| `cfgstore set sys.hostname=rlxfw-bench` | `written: slot 0, seq 1` | 量 `R78-cfg2` |
| `cfgstore get sys.hostname`, then `ls -l /var/lib/cfg.bin` | `sys.hostname=rlxfw-bench`; the file is **8192** bytes, `-rw-------` (mode **0600**), owner root | 量 `R78-cfg3` |

Sixteen is § 1's `CFG_NKEYS` read on the device. `8192` is two 4,096-byte slots
(`notes/config-store.md` § 4) and `0600` is the mode `cfg_store` passes to `open`
(`src/lib/cfg.c`), so the device shows that the kernel honoured what the code asks for, not that
either value is the right one.

**The store file did not exist before the first write.** `R78-sock` listed it at 12:31:57 as
`No such file or directory`; the only code that creates it is the `open` with `O_CREAT` in
`cfg_store`; and `cfg_load_info` answers a missing file with the defaults and source 0, leaving
both slots at their initial `too few bytes` verdict. So `bytes 0` in `R78-cfg1` means "no file",
and an absent and a zero-length file print the same `show`: only the earlier `ls` tells them
apart. The first write went to slot 0 at `seq 1`, the rule for a store with no valid slot
(`notes/config-store.md` § 4). The alternation needs a second write, which is not in these
captures (`R78-k2`, later in the boot, printed `written: slot 1, seq 2`).

**It was written to RAM.** `/var` is a tmpfs, which in this kernel is ramfs (`notes/init.md`
§ 3), so the store does not survive a power cycle (`notes/config-store.md` § 11) and an `fsync`
on ramfs is not a durability measurement. The device confirms the record format, the slot choice
and the file's size and mode; the torn-write and read-back properties remain properties of the
code, measured against a file.

### 7.5  dnsfwd

A query for `example.com`, type A, id `0x1234`, sent from the host to port 53 of the board, came
back as **29 bytes** with id `0x1234` echoed and **rcode 2** (SERVFAIL): 量, terminal only. The
probe prints the id with `hexlify`, so it is hexadecimal, `0x1234`, and not decimal 1234. The 29
is also the length of the query itself (12-byte header, 13-byte name, 4 bytes of type and class;
讀 `func78.sh`), which is consistent with the question echoed and no answer record: 推, because
the reply bytes were not saved.

**The cause is 推.** `notes/dnsfwd.md` gives two ways to a SERVFAIL, the 4-second upstream
timeout (§ 2) and an unreadable `/dev/urandom` (§ 4). The configured upstream is `10.1.1.2`
(`dnsfwd: lan 10.1.1.1 mask FFFFFF00 upstream 10.1.1.2`, `R78-boot`), the workstation's address
on this bench, and the probe's own comment expected it to run no resolver. That is an
expectation written before the run and not a reading: nothing was captured on the workstation
and the reply time was not recorded, so the timeout and an immediate refusal are not told apart.
The reading does show that a datagram from the LAN side was answered, with the client's id,
inside the probe's 6-second wait. It does not show the relay: no answer from a working upstream
has been relayed by this program on the board.

### 7.6  ifupd

`wan.mode` is 0 (`R78-cfg1`), so `init` does not start `udhcpc`
(`rlxfw: init: udhcpc: not started (wan.mode is not dhcp)`, `R78-boot`) and nothing execs `ifupd`
by itself: `D14` asks that each program's product run once on the device, and this one had not.
It was run from the console shell, as root, with the lease in its environment, the way `udhcpc`
would hand it one. **The lease is synthetic**: `10.9.9.9`, `10.9.9.1` and `10.9.9.53` were
invented at the desk for this run; no DHCP server issued them and none is an address this unit is
configured with.

| what was typed (the lease is the environment) | console line, and rc | mark, origin |
|---|---|---|
| `ip=10.9.9.9 subnet=255.255.255.0 router=10.9.9.1 dns=10.9.9.53 interface=rlx0 /sbin/ifupd bound` | `ifupd: bound ok reason=ok if=rlx0 ip=10.9.9.9/24 gw=10.9.9.1 dns=1`; rc 0 | 量 `R78-iu1` |
| afterwards, `cat /run/wan.dns` and `ifconfig rlx0` | `10.9.9.53`; `inet addr:10.9.9.9  Bcast:10.9.9.255  Mask:255.255.255.0` | 量 `R78-iu2` |
| `ip=999.1.2.3 subnet=255.0.255.0 router=8.8.8.8 interface=rlx0 /sbin/ifupd bound` | `ifupd: bound REFUSED reason=bad-ip detail=octet-over-255 if=rlx0`; rc 2 | 量 `R78-iu3` |
| `ip=10.9.9.9 subnet=255.255.255.0 interface= /sbin/ifupd bound`, the interface empty | `ifupd: bound REFUSED reason=no-interface`; rc 2 | 量 `R78-iu4` |
| `ip=10.1.1.1 subnet=255.255.255.0 interface=rlx0 /sbin/ifupd bound`, to put the address back | `ifupd: bound ok reason=ok if=rlx0 ip=10.1.1.1/24 dns=0 no-router-no-default-route`; rc not printed | 量 `R78-fix` |

Exit status is `notes/init.md` § 7's: 0 applied, 1 applied in part, 2 refused. The synthetic
address was on `rlx0` for about fifty seconds (capture starts 12:34:58 and 12:35:48). The
`ifconfig` meant to confirm the restoration failed on a usage error (`head -2` is not an option
of this `head`), so that confirmation is `ifupd`'s own `ok` line and not a second reading.

**What the `ok` line certifies.** `gw=` is printed only after the default-route add, a
`SIOCADDRT` ioctl (`nu_route_default_add` in `src/lib/netutil.c`), returned 0 (`do_bound` in
`src/ifupd/netcfg.c`; a failed add reads `PARTIAL reason=route-ioctl-failed`), so on this board the
kernel accepted a default route through `rlx0` for this lease: 讀 the branch, 量 the line.
`notes/init.md` § 8 lists that acceptance as 未定 and is not this file's to edit. Nothing further
follows: the route table was not dumped, nothing was forwarded, and whether the route through
`10.9.9.1` outlived the re-address in `R78-fix` was not read.

**What the refusals certify.** Each named its reason, exited 2 and returned. In `ifu_run` and
`do_bound` every refusal sits before the first ioctl (`do_bound`'s own comment: "parse and
validate everything mandatory, applying nothing"), so a refused lease should leave the interface
as it was: 讀, and the board was not asked, because no `ifconfig` was read between `R78-iu3` or
`R78-iu4` and `R78-fix`. `R78-iu3`'s lease also carried a non-contiguous mask (`255.0.255.0`) and
a router (`8.8.8.8`); the run stopped at the first defect and says nothing about the checks
behind it.

## 8  What this file does not establish

**Sections 1–6 have not run on the device.** Every number in them is a host measurement of a
cross-compiled artefact: the ceiling is an ELF's PT_LOAD extent, not a running kernel's
footprint; the six programs were exercised there only by their host suites under a
little-endian compiler; and `qemu-mips-static` covered the KDF's vectors and dnsfwd's decoder
and nothing else.

**Section 7 is one boot of one image on one unit, from RAM.** It shows that the programs start,
that the privilege separation is visible to the kernel, and that four of them answer a question
put to them. It does not show:

* that the guard refuses anything: no refusal was returned on the board (§ 7.1);
* that a login can succeed: the one login probe was refused, for a reason that is 推 (§ 7.3);
* that the config store survives anything, or works on the medium R8 will give it: it is on
  ramfs (§ 7.4);
* that `dnsfwd` relays: only its failure answer was read, and the cause of that is 推 (§ 7.5);
* that a lease from a DHCP server works: `udhcpc` has never run on the board and `ifupd` was
  driven by hand with a lease the desk made up (§ 7.6);
* anything about `entropy_avail`: `notes/entropy.md` owns the driver and its experiment, and
  § 7.3 uses only its consequence, the `auth_ready` flag.
