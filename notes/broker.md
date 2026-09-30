# brokerd — the privileged broker

R7's root daemon: the only process that touches the config store and the only
holder of sessions. `httpd` (uid 100) and `dnsfwd` (uid 101) reach it over one
`AF_UNIX`/`SOCK_STREAM` socket and may do only what the op table lets them.
Realises `plan/router-rebuild-plan.md` § `D7`: the vendor's Boa ran as root and
handed request strings to `system()`; here the privileged side accepts typed
requests only, and the only external program it starts is started with
`execve` and a fixed `argv`.

Files: `src/lib/proto.{c,h}` (wire codec), `src/lib/client.{c,h}` (`bk_call`),
`src/brokerd/{main,session,ops}.c`, `src/brokerd/test_*.c`,
`src/fuzz/fuzz_proto.c`. `AF_UNIX` is available: `CONFIG_UNIX=y` 量 in the
current image's `.config`.

## 1. Wire format (SPEC-R7 § 6)

One request and one response per connection. Every integer big-endian, decoded
with explicit shifts; no struct is ever `memcpy`'d to or from the wire.

### Request header, 48 bytes

| off | size | field | rule |
|---|---|---|---|
| 0 | 4 | magic | `0x524C5842` (`RLXB`), else `BADREQ` |
| 4 | 1 | version | 1, else `BADREQ` |
| 5 | 1 | op | not judged by the codec; an unknown op is `NOTSUP` from the dispatcher |
| 6 | 2 | flags | 0, else `BADREQ` |
| 8 | 16 | session | opaque |
| 24 | 16 | csrf | opaque |
| 40 | 4 | client_ip | honoured only from uid 100; 0 for everyone else |
| 44 | 4 | body_len | ≤ 2048, else `BADREQ` — checked before one body byte is stored |

### Response header, 12 bytes

| off | size | field |
|---|---|---|
| 0 | 4 | magic `0x524C5852` (`RLXR`) |
| 4 | 1 | version 1 |
| 5 | 1 | status |
| 6 | 2 | reserved 0 |
| 8 | 4 | body_len ≤ 4096 |

Status: 0 `OK` · 1 `BADREQ` · 2 `PERM` · 3 `AUTH` · 4 `LOCKED` (body u32 s) ·
5 `INVAL` (body u16 key id or 0) · 6 `IO` · 7 `NOENT` · 8 `BUSY` · 9 `NOTSUP` ·
10 `NOENTROPY`.

### The decoder

`proto_rx_*` is an incremental two-section state machine (`PRX_HDR` →
`PRX_BODY` → `PRX_DONE`/`PRX_ERR`). It never reads past what it was handed,
holds no pointer into the caller's buffer, and has no VLA, no recursion and no
`alloca`. `proto_decode_req` is the one-shot wrapper over the same machine.
`body_len` is validated the instant the 48th header byte lands, so `rx->want`
can never exceed `sizeof(rx->req.body)`; `proto_rx_feed` re-checks the same
bound before every copy, which is why removing the first check is a contract
break rather than a memory-safety break (§ 6).

## 2. Op and authorisation matrix

`ops.c`'s `rules[]` is the whole of it. No op handler reads a uid; `authorise`
inside `bk_dispatch` is the only function that does. `test_authz.c` walks the
same table.

| op | name | body in | body out | uid 0 | uid 100 | uid 101 |
|---|---|---|---|---|---|---|
| 0x01 | GET | u16 ids (≤64) | TLVs, same order | all keys | session | `dns.upstream`, `lan.ipaddr` only |
| 0x02 | SET | TLVs, ids strictly ascending | — | all keys | session + csrf, `web=rw` only | `PERM` |
| 0x03 | REBOOT | — | — | yes | session + csrf | `PERM` |
| 0x04 | STATUS | — | TLVs 0x8001–0x8008 | full set | full with a session, 3 rows without | `PERM` |
| 0x05 | PING | ipv4[4] + count u8 (1..5) | text ≤ 2048 | yes | session + csrf | `PERM` |
| 0x10 | LOGIN | password 1..64 | session[16]+csrf[16]+ttl u32 | yes, rate-limit exempt | rate-limited | `PERM` |
| 0x11 | LOGOUT | — | — | yes, idempotent | session + csrf | `PERM` |
| 0x12 | PWSET | u8 oldlen+old+u8 newlen+new (new 8..64) | — | may bootstrap with oldlen 0 | session + csrf + correct old | `PERM` |
| 0x20–0x22 | UPDATE_* | — | — | `NOTSUP` | `NOTSUP` | `NOTSUP` |

Any uid other than 0, 100, 101 gets `PERM` on every op. `STATUS`'s three public
rows are 0x8001 uptime_s, 0x8006 version, 0x8008 auth_ready.

Decisions SPEC § 6 leaves open, taken here:

* a live session with a **wrong CSRF** answers `PERM`, not `AUTH`. `AUTH` tells
  httpd to clear the cookie; a CSRF mismatch must be refused without logging
  the user out.
* `GET` refuses a `WEB_HIDDEN` key to a non-root peer with `PERM`, so
  `admin.pwhash` cannot leave through httpd.
* the entropy gate applies to **every** uid, root included: `PWSET` needs 16
  random salt bytes whoever asks.
* the rate limiter is keyed on the **effective** `client_ip` and **root is
  exempt** — locking the console out of `cfgstore` buys nothing against a peer
  that already owns the box.
* `need_session` is uid 100's requirement only. uid 101 cannot obtain a session,
  so its access is decided by the table's `allow_101` and the key list. Reading
  `need_session` for uid 101 was a real bug, caught by the named negatives in
  `test_authz.c` — the matrix's own derivation had copied it (§ 6).

## 3. Socket permissions, and why they are not SPEC § 3's

SPEC § 3 asks for mode 0660 owner `root:100` **and** that uid 101 be able to
connect. `connect(2)` on a unix socket needs write permission, and mode bits
cannot express `{0, 100, 101}` unless those uids share a group — which means a
supplementary group in `/etc/group`, and `/etc/group` is `init`'s file, not
brokerd's.

So: **the socket is mode 0666 by default and `SO_PEERCRED` is the
authorisation**; the directory `/srv/www/run/` is expected at 0711 `root:root`
(traverse, no listing). `-m MODE` and `-g GID` are provided, so once init puts
`dnsfwd` in gid 100 the daemon can be tightened to `-m 0660 -g 100` without a
rebuild. Every uid outside the table is answered `PERM` by the op table, which
is where the decision can be exact.

There is deliberately **no option** for the entropy file, the random source or
the ping binary: each would be a runtime bypass of a fail-closed rule.

## 4. Sessions

| constant | value |
|---|---|
| token, CSRF token | 16 bytes each from `/dev/urandom` |
| idle TTL | 900 s — valid while `now - last < 900`, expired at `>= 900` |
| maximum live | 4, LRU eviction (smallest `last`, `born` breaks a tie) |
| clock | `CLOCK_MONOTONIC`, so a `settimeofday` cannot extend a session |

`getrandom(2)` does not exist in 2.6.30 and its wrapper is not in uClibc
0.9.30, so `/dev/urandom` it is; a short read is refused, never padded. Every
token, CSRF token and password hash is compared with `bk_ct_eq`, which reads
every byte whatever the first one said. Dropping a session wipes the slot, so a
stale token cannot match a reused one. Tokens are never passed to `bk_log`. A
`PWSET` invalidates every session including the caller's.

## 5. LOGIN rate limit

16 buckets keyed on the effective client IP, **checked before the KDF runs**.
Five consecutive failures → `LOCKED`, first 60 s, doubling, capped at 3600 s
(60, 120, 240, 480, 960, 1920, 3600, 3600 …). A success clears both the count
and the escalation. At most **one KDF evaluation in flight** globally
(`kdf_busy`); brokerd is one process so this is structural, and the latch keeps
the invariant true if it ever becomes fork-per-connection.

**A locked bucket is never evicted.** With plain "evict the oldest", an attacker
locked out of one address clears the lock by connecting from sixteen others.
Free slots are used first, then the unlocked bucket seen longest ago; if all
sixteen are locked, a new address is answered `LOCKED` with the shortest
remaining wait. That is fail-closed, at the stated cost of refusing logins from
new addresses while the table is saturated.

KDF parameters written into a **new** `admin.pwhash`: `log2N = 12, r = 8,
p = 1` — from plan § D8's anti-DoS budget, `1 evaluation × 128·N·r ≤ 4 MiB`, so
`N ≤ 4096`; 4 MiB exactly. A hash already on disk is verified with its own
parameters out of bytes `[1..5]`. Time on the device: **未定** (agent D's row).

## 6. Entropy: fail-closed, and what that means on this board today

`LOGIN` and `PWSET` answer `NOENTROPY` until brokerd has seen
`/proc/sys/kernel/random/entropy_avail >= 128` at least once since boot; the
flag is sticky, so a pool that drains again does not take the ability to log in
away. `STATUS` reports `entropy_avail` (0x8007) and `auth_ready` (0x8008).

**量 2026-09-30, on the r6b8i image running now:** `entropy_avail` read **0** at
768.26 s of uptime (`bench/2026-09-30/SB-ENT.log`) and **0** again at 1613.27 s
(`SB-RT1.log`), with `poolsize` 4096.

**So on this board, as it is today, brokerd refuses every login.** That is the
honest behaviour of the two available ones: the alternative is to hand out
16-byte session tokens from a pool the kernel says holds nothing, which is a
predictable-token bug shipped to hide a kernel gap. The rule is not weakened to
make login work. Feeding the pool is a kernel-side item and is **not** fixed
here. `test_entropy.c`'s first fixture is that measurement, so the refusal is
a tested behaviour and not an accident.

An unreadable `/proc` file is also "not ready"; so is garbage, and so is a
leading `-`. A saturating decimal is ≥ 128 and opens the gate.

## 7. Concurrency, timeouts, and what still blocks

`poll()` over one listening fd and at most 8 connection slots, one process, one
thread, no shared memory, no locks (MIPS-I has no atomic RMW). Per connection:
**5 s** without a byte, **15 s** hard lifetime cap. The listener is only polled
while a slot is free. `SIGPIPE` ignored; `EINTR` retried everywhere; every fd
`CLOEXEC` — through an explicit `fcntl` helper, because `O_CLOEXEC` is not in
uClibc 0.9.30's `fcntl.h`. A request whose bytes are followed by anything else
is `BADREQ`: one request per connection.

The deadline, not the multiplexing, is what bounds a slow client. `test_wire.c`
holds all eight slots with silent peers and a normal `bk_call` is still served.

**What still blocks, stated rather than hidden:** the KDF and `PING` run
synchronously inside `bk_dispatch`, so one `LOGIN` stalls the loop for one
scrypt and one `PING` for up to 10 s. For the KDF that is deliberate (plan § D8
ruling 3 wants one in flight). For `PING` it is a real latency hole and is not
fixed here.

## 8. PING

`execve("/bin/busybox", {"ping", "-c", N, "-W", "1", dotted, NULL})`, `argv`
built from four typed bytes and one typed count and from nothing else. stdout
and stderr through one pipe, output truncated at 2048 bytes, child reaped with
`SIGTERM` then an unconditional `SIGKILL` and a blocking `waitpid`, so no
zombie survives. Target `0.0.0.0` and count outside 1..5 are `INVAL`.

**The timeout is the primary mechanism, not a safety net.** 讀
`config/image-commands.tsv`: this image's `ping` ignores `-c`, so the count
never stops it. `-c` is passed anyway because a later busybox honours it.
Deadlines are in **milliseconds** (`bk_now_ms`): a whole-second monotonic
deadline is coarse in the wrong direction — flooring the start means `now + 2`
can fall 1.01 s later, so a "10 s" timeout would land anywhere in [9, 10]. The
test measured 1 s for a 2 s timeout before this was fixed.

`test_ping.c` drives both endings with two helper builds: 8 KiB then sleep (the
truncation path, which returns without waiting out the deadline) and 64 bytes
then sleep (the deadline path, the one that matters on the device).

## 9. Test and sweep numbers

Host, `make -C src/brokerd test O=…`; 7 test binaries × gcc-13 and clang-18 =
14 runs, then all 7 again under `-fsanitize=address,undefined`. Clean under both
compilers at `-Wall -Wextra -Werror`; **zero sanitizer findings**.

| | |
|---|---|
| decoder sweep | **124,975 cases** = 122,400 single-byte header corruptions (10 frames × 48 offsets × 255 values) + 2,575 truncations (every length 0..48+body of each frame) |
| each case run twice | one-shot and byte-at-a-time through the incremental machine, so **249,950 decode invocations**; the two must agree on the exact return code |
| authorisation matrix | **264 cells** = 11 ops × 4 uids × 3 session states × 2 CSRF states, each expected status derived from the table |
| mutants | 6 planted, **5 caught** |

The tenth sweep frame is maximal (`body_len` 2048), which is what lets a
single-byte corruption move `body_len` *below* what is delivered as well as
above the cap.

The sweep compares the **exact** refusal code against an independent model of
SPEC § 6's field order, not merely "refused". That is load-bearing twice: a
frame over the cap must say `BADREQ`-because-`BODYLEN` rather than "wait for
more bytes", and with only a sign comparison the removed-bound mutation hides
behind `proto_rx_feed`'s second bound check and the whole sweep stays green.

### Mutations (`make -C src/brokerd mutants O=…`)

Each mutant is a copy made by `src/brokerd/mutate.py`, which refuses unless its
anchor matches exactly once; the shipped sources carry no switch. The unmutated
suite is run first — a mutation run against a red suite proves nothing.

| # | mutation | result |
|---|---|---|
| M1 | `body_len` bound removed | **caught**, 15,660 sweep cases |
| M2 | header length 47 instead of 48 | **caught**, 212,860 assertions |
| M3 | magic check inverted to accept all but one value | **caught**, 20,402 |
| M4 | `proto_be32` byte order reversed | **caught**, 76 |
| M5 | version check removed | **caught**, 5,100 |
| M6 | constant-time compare given an early exit | **NOT caught — predicted before the run** |

M6 is the honest one: it is functionally identical, so no unit test can see it.
A timing side channel needs a timing experiment, and there is none here.

## 10. Fuzzing

`src/fuzz/fuzz_proto.c`, plain `main(argc, argv)`, one file per run. It decodes
the bytes four ways — one-shot, and through the incremental machine in whole,
1-byte and 7-byte chunks — and `abort()`s on any disagreement in accept/refuse,
in the refusal code, in any decoded field, or in the consumed byte count. So a
split-read bug, the class a one-shot harness cannot see, is reported as a crash.
Seeds: `src/fuzz/corpus/proto/`, 25 files, named without an extension — the
repo's `.gitignore` carries `*.bin` to keep flash dumps out of the tree, and a
nested `!*.bin` would be a hole in exactly the rule that must not have one.

Thresholds and the void condition were written before the run, in
`$W/PREREG-fuzz.md` (workspace, not committed): branch coverage of the six
reachable decode functions ≥ 85 %, region coverage ≥ 95 %, every uncovered
branch named, zero crashes on the unmutated decoder — and **if the fuzzer does
not find the planted defect, the harness is not connected and the coverage
figure is void.**

### The clean run, 量 2026-09-30

`afl-fuzz` 4.09c, 720 s, `-D` plus a CMPLOG companion, 25 seeds:
**607,537 execs, 843 exec/s, 47 queue items, stability 100 %, bitmap 32.45 %,
0 crashes, 0 hangs.** Coverage replayed over the 25 seeds plus the 47 queue
items (72 inputs) through an `llvm-cov-18` build:

| function | regions | lines | branches |
|---|---|---|---|
| `rx_header` | 100 % | 100 % | **100 %** (8/8) |
| `proto_rx_feed` | 83.61 % | 87.01 % | 63.04 % (29/46) |
| `proto_decode_req` | 81.25 % | 93.33 % | 60.00 % (6/10) |
| `proto_rx_init` | 80.00 % | 88.89 % | 50.00 % (1/2) |
| `proto_be16`, `proto_be32` | 100 % | 100 % | no branches |
| **the six together** | **87.83 %** (101/115) | **90.84 %** (119/131) | **66.67 %** (44/66) |

Whole file, which includes the encoder and TLV halves no byte stream can reach:
38.55 % regions, 48.37 % lines, 32.84 % branches.

**Two of the three thresholds are MISSED**: branch 66.67 % against ≥ 85 %, region
87.83 % against ≥ 95 %. Reported as a miss, not renegotiated.

**Every one of the 22 uncovered branches, named** — and they are all the same
kind of thing, which is why the threshold was wrong rather than the harness:

| where | branches | why no byte stream reaches it |
|---|---|---|
| `proto_rx_init` `rx == 0` | 1 | a NULL argument; only a caller can pass one |
| `proto_rx_feed` `rx == 0 \|\| (p == 0 && n != 0)` | 3 | same |
| `proto_decode_req` `out == 0 \|\| (buf == 0 && n != 0)` | 3 | same |
| `proto_rx_feed` re-entry on `PRX_ERR` / `PRX_DONE` | 2 | the harness stops feeding a terminal machine |
| `proto_rx_feed` `rx->have > cap \|\| rx->want > cap` and its `used != 0` | 3 | defence in depth, unreachable while the primary `body_len` bound holds — which is exactly why mutation M1 was invisible until the sweep compared exact codes |
| `proto_rx_feed` `room == 0 → take = 0` | 1 | `want == have` on entry cannot happen: the machine changes state the moment a section completes |
| the rest | 9 | in `proto_encode_*`, `proto_decode_resp`, `proto_tlv_*` — a request byte stream does not call them |

So the achievable ceiling for this harness is the 66.67 % it reached. The
pre-registration was set without counting the NULL guards and the
unreachable-by-construction second bound; the correct way to have written it was
to exclude those branches from the denominator **before** the run, or to add a
harness mode that calls the entry points with NULL. `test_proto.c`'s
`test_null_and_zero` covers the NULL guards, so they are tested — just not by
the fuzzer.

### The planted defect: found, and the find is stochastic

`mutate.py off1` — `body_len` bounded at 2049 instead of 2048, a **one-byte**
overflow of `rx->req.body`, built with `AFL_USE_ASAN=1`. Seeds that already crash
the mutant are pre-screened out and named (`bodylen_2049`, 24 of 25 kept), so a
reported crash is a discovery and not a calibration failure. The seed that can
reach it is `maxbody_trail`: `body_len` 2048 with 2,148 bytes delivered.

| run | configuration | execs | result |
|---|---|---|---|
| 1 | 24 seeds, AFL++ defaults | 167,561 / 300 s | not found |
| 2 | 24 seeds, `-D` + CMPLOG | 209,072+ / 900 s | not found |
| 3 | 1 seed (the reaching one), `-D` | 83,484 / 240 s | not found |
| 4 | 24 seeds, `-D` + `-x proto.dict` | 165,409 / 300 s | not found |
| 5 | 24 seeds, `-D` + dict + `AFL_DISABLE_TRIM=1` | 207,918 / 300 s | not found |
| 6 | 1 seed + `AFL_DISABLE_TRIM=1` + `-D` | **4,179 / 7 s** | **FOUND** |

Run 6's crash: 2,099 bytes, `body_len` 2049, 2,051 delivered; ASan
`stack-buffer-overflow`, `WRITE of size 2049`, from an `op:splice`. The **clean**
decoder returns 0 on the same input, so the crash is the defect and not the
harness.

**One find is not a figure, and the first repeat of run 6 missed it.** So the
configuration was run six more times independently, 300 s each, in parallel:

| repeat | result | run_time | execs |
|---|---|---|---|
| 1 | not found | 300 s | 159,601 |
| 2 | not found | 300 s | 160,028 |
| 3 | **found** | 2 s | 441 |
| 4 | **found** | 10 s | 3,644 |
| 5 | not found | 300 s | 159,028 |
| 6 | **found** | 1 s | 442 |

**Hit rate 3 of 6 at 300 s, and the find is bimodal: either inside ~11 s and
~4,000 execs, or not inside 300 s and ~160,000 execs.** Four hundred execs is
AFL's opening splice/havoc pass on a single seed; once the run settles past that
it never comes back to the one byte that matters. So this defect is found by luck
early or not at all, and *run length buys nothing* — which is the same fact as the
missing coverage gradient, seen from the other side.

What that licenses and what it does not: the harness **is** connected to the
decoder — a fuzzer-generated input crashes the mutant and leaves the real decoder
at rc 0, three times independently. It does **not** license "AFL will find a
one-byte overflow in this decoder"; on this evidence it finds this one about half
the time in five minutes, and only once the corpus contains a seed that delivers
more bytes than it declares and trimming is off.

Two causes, each isolated by its own run rather than guessed:

1. **AFL's trim stage removed the reachability.** 量: `dout3/queue/id:000000`
   came out at **2,096 bytes** from a 2,148-byte seed. The 52 bytes it cut are
   past `body_len`, the decoder ignores them, so they add no coverage and
   trimming is right to drop them — but the defect needs ≥ 2,097 bytes present,
   so it became unreachable before the first mutation. Run 3 (no
   `AFL_DISABLE_TRIM`) missed; run 6 (with it) found it in 7 s.
2. **Scheduling.** With 24 seeds, 23 of them under 160 bytes, AFL never spent
   enough energy on the one slow 2 KiB item that can reach the defect — runs 1,
   2, 4 and 5 all kept that entry at 2,148 bytes on disk and still missed.

The dictionary (`src/fuzz/proto.dict`) did not rescue it either, and that is the
substantive lesson: a 32-bit length compared against **one** constant gives
coverage guidance nothing to climb, because every wrong value lands on the same
edge. For this decoder the corpus shape — one seed that delivers more bytes than
it declares — mattered far more than run length, dictionary or CMPLOG.

## 11. Target build

`make -C src/brokerd target O=… TC=… TRIP=…` under
`tools/vendor-tripwire.sh`, sources staged onto ext4 first and every staged
hash compared with the repo's (the rsdk driver is a 32-bit i386 ELF and every
DrvFs path returns `EOVERFLOW` to its `stat()`). `O` on `/mnt/*` is refused. No
`-march` anywhere — the wrapper's default is the 4181 core.

| | |
|---|---|
| ELF | static, big-endian, MIPS R3000, no `PT_INTERP` |
| unstripped | 107,400 bytes |
| stripped | **69,404 bytes** |
| objects kept | 5, at `$O/target/obj/brokerd/*.o` |
| `hazlint` | **0 violations** in 2,744 loads |
| `system`/`popen`/`exec*p` symbols | **0** (control ELF that calls them: 3) |
| `/bin/sh` string | **0** (control: 1) |

Both shell checks show their detector firing on a positive control built with
the same compiler and the same static libc first.

## 12. What this does NOT establish

* **Nothing has run on the device.** Every figure above is a host test or a
  cross-compile. brokerd has never been executed on the RTL8196E.
* **No TLS.** Every byte between a browser and httpd is plaintext on the LAN,
  and the session cookie with it. R7g is out of this gate by the plan's own cut
  order.
* **A root-capable attacker owns everything.** brokerd *is* root. Privilege
  separation buys the case where httpd is compromised and root is not; it buys
  nothing once root is reached, and the broker is a fresh attack surface of its
  own reachable from uid 100 and uid 101.
* The sweep and the fuzzer cover the **request decoder**. `ops.c`'s bodies get
  the authorisation matrix and the named negatives, which are far fewer cases.
  `main.c`'s `poll` loop is exercised by `test_wire.c` only; its reboot path is
  not tested at all.
* The 124,975 sweep cases are single-byte corruptions and truncations of ten
  frames. They say nothing about multi-byte corruptions, and the fuzzer is what
  covers those.
* The config store and the KDF are **other agents'**. brokerd was built and
  tested against local stubs under `src/brokerd/stub/`
  (`cfg.h`, `kdf.h`, `cfg_stub.c`) because `src/lib/cfg.h` was absent from the
  clone; the Makefile prefers the real files the moment they exist, and until
  then no figure here says anything about scrypt or about A/B slot integrity.
  `CFG_NKEYS`, the key order and the `CFGE_*` numbers are the stub's guesses.
* `bk_ct_eq` is asserted for **correctness only**. Its constant-time property is
  not measured anywhere, and M6 shows the suite cannot see it.
