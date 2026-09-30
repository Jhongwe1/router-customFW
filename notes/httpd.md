# httpd and the password KDF (R7, segment 118, 2026-09-30)

rlxfw's web server, the flat JSON reader it sits on, and the scrypt parameters the
stored password uses. What the gate asks of this half is in `SPEC-R7.md` §§ 3, 4.2
and 7; the privilege-separation argument is `plan/` § `D7` and the KDF budget is
§ `D8`'s v6 ruling 4.

Marks: **量** measured, **讀** read out of code or a document, **推** inferred and
pending a measurement. Nothing in this note has run on the device.

---

## 1. What the program is

One process binds TCP :80 as root and then stops being root. Every privileged
action is a typed op on a unix socket to `brokerd`, which is the only process that
can read the config store or a password hash.

```
    peer  --tcp:80-->  httpd (uid 100, chroot /srv/www)
                         |  AF_UNIX, 48-byte typed request
                         v
                       brokerd (uid 0)  -->  /var/lib/cfg.bin
```

httpd holds no config, no password, no session table and no crypto: `src/lib/kdf.c`
is *not* linked into it. The 32-byte constant-time comparison it needs for the CSRF
check is five lines of its own (`routes.c route_ct_eq32`), duplicated on purpose so
that scrypt's code and its 4 MiB working set are not in the address space that
parses attacker bytes.

### 1.1 Files

| file | what |
|---|---|
| `src/httpd/main.c` | argv, then three calls into `serve.c`. No flag can skip the privilege drop |
| `src/httpd/serve.c` | listen, the drop, the fork-per-connection loop, the parent's login limiter |
| `src/httpd/http.c` | the bounded request parser and the path decoder |
| `src/httpd/routes.c` | the eleven routes, the broker status mapping, the header block |
| `src/httpd/rl.c` | token buckets, in the parent |
| `src/httpd/chrootcheck.py` | refuses a web root that could become a shell |
| `src/httpd/kdfbench.c` | one scrypt evaluation, timed and weighed |
| `src/httpd/stub/` | local stubs for `src/lib/client.h` and `src/lib/cfg.h`, absent when this was written |
| `src/lib/json.{c,h}` | the flat JSON reader and a bounded writer |
| `src/lib/sha256.{c,h}`, `src/lib/kdf.{c,h}` | SHA-256, HMAC, PBKDF2, scrypt, the 56-byte blob |
| `srv/www/` | `index.html`, `static/style.css`, `static/app.js` |

---

## 2. The route table

| method | path | session | CSRF | broker op | answer |
|---|---|---|---|---|---|
| GET | `/` | — | — | — | `index.html` |
| GET | `/static/<name>` | — | — | — | the file, typed from a fixed MIME table |
| GET | `/api/status` | optional | — | `0x04` STATUS | JSON of the TLVs that came back |
| POST | `/api/login` | — | — | `0x10` LOGIN | sets `rlxs` and `rlxc`, returns the CSRF token and the TTL |
| POST | `/api/logout` | yes | yes | `0x11` LOGOUT | expires both cookies |
| GET | `/api/config` | yes | — | `0x01` GET | every key the schema marks web-readable |
| POST | `/api/config` | yes | yes | `0x02` SET | TLVs, ids strictly ascending |
| POST | `/api/password` | yes | yes | `0x12` PWSET | |
| POST | `/api/ping` | yes | yes | `0x05` PING | four typed octets and a count; output filtered to printable ASCII |
| POST | `/api/reboot` | yes | yes | `0x03` REBOOT | |
| POST | `/api/firmware` | yes | yes | — | 501, after the same checks as any other write |

A known path with the wrong method is 405 with `Allow: GET, POST`. An unknown path
is 404 with one fixed document, `{"ok":false,"error":"notfound"}`.

### 2.1 Broker status to HTTP status

`0` OK → 200 · `1` BADREQ → 400 · `2` PERM → 403 · `3` AUTH → 401 ·
`4` LOCKED → 429 + `Retry-After` from the broker's own seconds · `5` INVAL → 400
with the key **id as a number** · `6` IO → 500 · `7` NOENT → 404 · `8` BUSY → 503 ·
`9` NOTSUP → 501 · `10` NOENTROPY → **503 with `"error":"noentropy"`**, which the
page renders as a sentence saying the pool is not ready and that the firmware
refuses rather than using a weak salt.

No response body or header in this program contains a byte from the request. The
error tokens are a closed set of string literals selected by a switch; the key id
in an INVAL answer is a number, and the page maps it from its own table. This is
tested by requesting `/nope-MARKER-7e1` and searching the whole answer, head and
body, for `MARKER`.

### 2.2 Session and CSRF

The session cookie is `rlxs=<32 hex>; Path=/; HttpOnly; SameSite=Strict`. httpd
cannot validate it — the session table is brokerd's — so httpd checks only that it
is present and exactly 32 hex digits, and brokerd decides.

CSRF is a **double submit**: the same token goes out in a companion cookie
`rlxc=<32 hex>; Path=/; SameSite=Strict` (deliberately *not* HttpOnly, so the page's
script can copy it) and comes back in `X-RLX-CSRF`. httpd compares header against
cookie in constant time before the body is looked at, so a cross-site POST dies at
the edge without a broker round trip; brokerd then compares the header against the
session's real token, which is the check that decides. Neither cookie is `Secure`:
there is no TLS in R7, and a `Secure` cookie over plain HTTP is a cookie that is
never sent. **The companion cookie is an addition to `SPEC-R7.md` § 7**, which pins
`rlxs` and the header but not a second cookie.

### 2.3 Headers on every response

`X-Frame-Options: DENY`, `Content-Security-Policy: default-src 'self'`,
`X-Content-Type-Options: nosniff`, `Connection: close`, `Content-Type`,
`Content-Length`; `Cache-Control: no-store` on `/api/*` only. They are written by
`route_headers()`, which no route can skip because no route writes this block. The
CSP is why the page's script is `/static/app.js` and not an inline `<script>`: a
`default-src 'self'` policy forbids inline script, and weakening the policy for one
file's convenience is the wrong way round.

---

## 3. The limits table

| limit | value | what happens past it |
|---|---|---|
| request line | 1024 bytes | 414 |
| header lines | 32 | 431 |
| header bytes, total | 4096 | 431 |
| one header line | 1024 bytes | 431 |
| body | 4096 bytes | 413 |
| `Content-Length` on a POST | required | 411 without it |
| `Transfer-Encoding`, any value | — | 501 |
| decoded path | 128 bytes, ≤ 2 segments, name ≤ 64 | 414 or 400 |
| concurrent connections | 8 | 503 from the parent, no ninth child |
| connections from one address | 4 | 503 |
| header timeout | 5 s | 408 |
| body timeout | 10 s | 408 |
| whole connection | 20 s (`alarm`) | the child dies |
| static file | 262,144 bytes | 404 |
| JSON members | 24 | refused |
| JSON string | 64 bytes after unescaping | refused |
| JSON depth | 1 | refused |

Strictness that is deliberate, because a tolerant parser in front of anything is a
request-smuggling primitive: CRLF only (a bare LF is 400); no `obs-fold`; a second
`Content-Length`, `Transfer-Encoding`, `Cookie`, `X-RLX-CSRF` or `Content-Type` is
400 rather than last-wins; origin-form targets only; a `Content-Length` on a GET is
refused rather than ignored.

### 3.1 The path decoder

The set of bytes a decoded path may hold is `[A-Za-z0-9._/-]` and nothing else.
`%` is **not** in it, which is what makes double-encoding impossible rather than
merely detected: `%252e` decodes to a literal `%` and dies. `%2F`, `%5C` and `%00`
are refused before the byte is stored. Every `.` and `..` segment is refused, as is
an empty segment (`//`) and a trailing slash. Then a second, whole-string
`strstr(".."), strstr("//")` runs over the result — two independent readings of the
same rule, the second one cheap and easy for a reader to verify.

At run time `send_file()` opens with `O_NOFOLLOW`, requires `S_ISREG`, and refuses
any file with an execute bit. Those are the same three properties `chrootcheck`
enforces over the tree at build time, checked again per request in case the tree
changed underneath.

---

## 4. The privilege drop, and how it is verified

`srv_drop()` in `serve.c`, in this order, with every step checked and no path that
continues on failure (it prints the step that failed and `_exit(1)`):

1. `bind(:80)` as root — the only thing root is used for.
2. `chroot(root)` — before any credential change, because `chroot(2)` needs
   `CAP_SYS_CHROOT`, which uid 100 does not have.
3. `chdir("/")` — **not optional, and not in the brief's sequence.** A chroot
   without it leaves the working directory outside the new root and every relative
   path still resolves from there; the chroot would be decoration.
4. `stat("index.html")` must succeed and `stat("/etc/passwd")` must fail — the
   guard shown permitting as well as refusing. Without the first, a chroot into the
   wrong directory is indistinguishable from a chroot into the right one.
5. `setgroups(0, NULL)`, then `getgroups(0, NULL) == 0` — **also not optional and
   also not in the brief's sequence.** `setgid()` does not clear the supplementary
   group list, so a process that was in group 0 stays in group 0 after
   `setgid(100)` and every group-0 file stays reachable.
6. `setgid(100)`, then `getgid() == getegid() == 100`.
7. `setuid(100)`, then `getuid() == geteuid() == 100`.
8. `setuid(0)` must fail, and `setgid(0)` must fail. Either succeeding means the
   process is still root in a way the checks above did not see, and serving would
   be worse than not serving.

**There is no `--no-chroot` flag.** A binary that can be told to skip its drop is a
binary that will one day be started that way. So `srv_drop()` cannot be reached
from a unit test — it refuses to run unless it is root — and instead of leaving it
untested, it is tested by running the real binary as root:
`sudo make -C src/httpd rootcheck ROOT=<a root-owned copy of srv/www> PORT=18080`.

量 2026-09-30, **24 of 24 cases**, every one read out of `/proc/<pid>/status` or off
the wire rather than out of the program's own printout:

| | |
|---|---|
| `Uid:` / `Gid:` of the live process | **100 / 100** |
| `Groups:` | **empty** |
| `/proc/<pid>/root` | the web root, so the chroot is the kernel's view and not a claim |
| `/`, `/static/style.css` | 200 — the controls, so the refusals below mean something |
| `/etc/passwd`, `/static/../../../etc/passwd`, `/static/%2e%2e/etc/passwd` | not 200, and no `root:` in any answer |
| the four security headers, on the wire | present; `no-store` on `/api/*` and absent on `/`, so the check can tell them apart |
| four silent peers from 127.0.0.1, then a request from 127.0.0.2 | **200** — one address cannot hold the server shut |
| the fifth connection from 127.0.0.1 | **503**, not a queue |
| that 503's body against its own `Content-Length` | equal (curl exit 0, not 18) |
| five POSTs to `/api/login` | **503 503 503 429 429** with a `Retry-After` |
| zombies | 0; the parent survived every case |

That `503 503 503 429 429` is the login limiter working end to end — through a
`fork()`, over the socketpair, with the bucket in the parent — and not a unit test
calling a function pointer. The three 503s are the broker being absent, which is
the control: they prove the grant was *given* before the 429 proves it was
withheld.

This is Linux 6.x on x86-64 under WSL. The syscalls are the same ones; the kernel
is not 2.6.30 and the CPU is not the Lexra. The device is still the first place any
of this runs for real.

### 4.1 Nothing executable in the web root

`make -C src/httpd chrootcheck ROOT=srv/www` walks the tree with two independent
detectors, because either alone has a blind spot:

* **mode** — any execute bit on a regular file, any setuid/setgid bit, any symlink
  (refused whether or not it points outside: the target can be created later), any
  device node, any FIFO, any world-writable file, and `st_nlink > 1` (a second name
  is a second mode to change).
* **content** — the first bytes of every regular file: ELF, `#!`, gzip, PE, Mach-O,
  zip. A file with no execute bit today is still an ELF, and `chmod` is one syscall.

Plus: an extension the MIME table cannot name is refused, because a web root is not
a download directory.

量 2026-09-30, and the refusal is shown before the pass:

```
planted /srv/www/bin/sh (a copy of /bin/sh)  -> REFUSED, 3 findings
    bin/sh: mode 0755 has an execute bit
    bin/sh: begins with an ELF
    bin/sh: extension '' is not one the MIME table can name
planted symlink bin/sh -> /bin/busybox       -> REFUSED, 1 finding
the real srv/www (3 files)                   -> clean
chrootcheck.py --self-test                   -> 6 planted offenders all REFUSED,
                                                a clean tree of 2 files PASSES
```

The unix socket that *is* meant to be there (`/srv/www/run/broker.sock`) is reported
and allowed: it is the one door out of the chroot, by design.

---

## 5. The KDF, and where the parameters come from

`plan/` § `D8` v6 ruling 4 is the brief: **scrypt on this machine is a DoS path, and
the parameters are decided by an anti-DoS budget, not by a performance
measurement.** The whole value of scrypt is memory hardness, and this device has
26,052 kB of RAM in total (`MEM-06`), one CPU at 400 MHz (`CPU-11`, 量) and no
cgroups on a 2.6.30 kernel — so an unauthenticated POST that allocates 16 MiB (the
usual `N=16384, r=8`) would be over 60 % of the machine, and the OOM killer's choice
of victim is not predictable.

### 5.1 The budget, written before the measurement

| # | line of the budget | value | where it comes from |
|---|---|---|---|
| B1 | concurrent evaluations × bytes per evaluation | **≤ 4,194,304 bytes** | `plan` D8 ruling 1, written before any measurement. Not changed to make a result fit |
| B2 | concurrent evaluations | **1** | ruling 3: the KDF runs only in brokerd, one at a time. So B1 becomes "≤ 4 MiB per evaluation" |
| B3 | seconds one evaluation may occupy brokerd | **≤ 1.0 s** | mine. brokerd serves one op at a time, so an evaluation is head-of-line blocking for every other client; a status poll must not visibly stall |
| B4 | what one connection buys an attacker | **exactly one evaluation** | `Connection: close`, one request per connection |
| B5 | sustained share of brokerd an attacker can hold with KDF work | **≤ 25 %** | B3 × the global login rate below |

B5 is the line that matters, and it is why the limiter is a *rate* and not only a
lockout. `SPEC-R7.md` § 6 gives brokerd a per-client-IP bucket in a 16-entry table;
on a LAN an attacker owns his own stack and can cycle more than 16 source
addresses, which resets his own per-address bucket. **A per-IP bucket is therefore
not a bound.** What bounds the rate is the global bucket, in httpd's parent:

| bucket | burst | refill | worst-case sustained |
|---|---|---|---|
| login, global | 3 | 1 token / 4 s | 0.25 login/s |
| login, per address | 3 | 1 token / 10 s | 0.1 login/s |
| connections, global | 32 | 16 /s | |
| connections, per address | 16 | 8 /s | |

0.25 login/s × 1.0 s per evaluation (B3) = **25 % of brokerd's time**, worst case,
from an attacker with unlimited addresses. At the measured-class figure below
(~0.3 s) it is 7.5 %.

### 5.2 Why the limiter lives in the parent

Ruling 2 says the limiter runs *before* the KDF and blocks on the httpd side. httpd
forks per connection and the design has no shared memory on purpose (D7: MIPS-I has
no atomic read-modify-write, so the architecture is processes, and then there is
nothing to lock). A bucket in the connection handler would therefore be per
connection, which is no bucket at all.

So the buckets live in the parent — the only process that sees every connection —
and a child that is about to spend an evaluation asks over the socketpair it was
forked with: one byte out (`'L'`), five bytes back (a verdict and a big-endian
`Retry-After`). One writer, no shared page, no atomics, and the answer arrives
before the request is forwarded. A refused child answers **429** with
`Retry-After` and never calls the broker. The parent also holds the
"one evaluation in flight" interlock, mirroring brokerd's, and tells a second asker
when rather than queueing it.

量: `test_routes.c` asserts that a refused grant produces 429 **and that the fake
broker's call counter is still 0**, with the control beside it — a granted login
produces exactly one broker call, op `0x10`.

### 5.3 The parameters, and the one that was rejected

scrypt's peak allocation is `128·r·N` for the `V` array, plus `2·128·r` for the
ping-pong scratch and `p·128·r` for the input block — one `malloc`, confirmed by
interposing `malloc` from outside the translation unit (exactly one call per
evaluation, of exactly that size) and again by a planted `printf` at the allocation
site in a cross-compiled build run under qemu.

| log2N | r | p | peak bytes | vs the 4 MiB cap | N·r (CPU work) |
|---|---|---|---|---|---|
| 12 | **7** | **1** | **3,672,704** | under, 521,600 B spare | 28,672 |
| 12 | 8 | 1 | 4,197,376 | **over by 3,072 B (0.073 %)** | 32,768 |
| 13 | 4 | 1 | 4,195,840 | over by 1,536 B | 32,768 |
| 11 | 8 | 1 | 2,100,224 | under | 16,384 |
| 12 | 8 | 2 | 4,198,400 | over | 65,536 |

**Recommendation: `log2N = 12, r = 7, p = 1`.**

The reasoning, in the order it decides:

* For a *fixed* memory budget `M = 128·r·N`, the CPU work is `N·r·p = M·p/128` — so
  at `p = 1` the time is fixed by the memory and the split between `N` and `r` does
  not change it. The choice between `(12,8)` and `(15,1)` is therefore not a
  speed/memory trade-off at all; it is about access pattern. Larger `r` means
  larger sequential reads (896 bytes here), which suits a device whose cache is
  smaller than the `V` array either way and whose DRAM prefers bursts; larger `N`
  means more, smaller random reads. RFC 7914 recommends `r = 8` for exactly this
  reason, and 7 is the largest value that fits the cap at `log2N = 12`.
* `p` stays at **1**. Raising `p` buys CPU work without buying memory — `(11,8,2)`
  has the same `N·r·p` as `(12,8,1)` at half the memory — which is precisely the
  trade the plan forbids: paying scrypt's complexity for PBKDF2's security.
* `(12,8,1)` is the canonical parameter set and it is **rejected**, by 3,072 bytes
  out of 4,194,304. That is 0.073 %, and widening the cap to admit it is the one
  thing not allowed: the cap was written in the plan before any measurement
  (`plan` D8 ruling 1). If the owner ratifies the cap as applying to the `V` array
  rather than the whole allocation, `(12,8,1)` becomes the recommendation and
  nothing else changes — the two differ by 14 % of CPU work. That is a decision
  about the cap, and it is his, not a measurement.
* The **named fallback** (ruling 4) is PBKDF2-HMAC-SHA-256 with **100,000
  iterations**, implemented and vector-tested in the same file. Its iteration count
  comes from the same budget: B3 is 1.0 s, one PBKDF2 iteration is two SHA-256
  compressions of a 64-byte block from precomputed ipad/opad states, ≈ 1,400
  instructions, ≈ 5.3 µs at 400 MHz and CPI 1.5 (推) → ≈ 190,000 iterations per
  second, so 100,000 iterations is ≈ 0.53 s at O(1) memory. It is named and costed
  now, not "if scrypt turns out too slow".

`admin.pwhash` is the 56 bytes of `SPEC-R7.md` § 4.2: alg = 1, `log2N` = 12,
r = 7, p = 1, two zero bytes, a 16-byte salt and the 32-byte key.

⚠️ `pwhash_verify()` reads `log2N`, `r` and `p` **out of the blob**, so the cap is
enforced against a stored value: a blob claiming `log2N = 30` would request 8 GB.
It goes through `kdf_scrypt()`, which refuses anything over `KDF_PEAK_CAP`.
Anyone re-implementing it over `kdf_scrypt_raw()` removes that guard.

### 5.4 The measured numbers

量 2026-09-30, one evaluation per process, 9 runs per cell, median, with a `noop`
run of the same program interleaved as the baseline (`src/httpd/kdfbench.c`;
`make -C src/httpd kdfbench kdfbench-target`):

| where | log2N/r/p | process elapsed | the program's own CLOCK_MONOTONIC | peak RSS | baseline RSS |
|---|---|---|---|---|---|
| qemu-mips-static, target ELF | 12/7/1 | 0.29 s | 0.2733 s | 9,520 kB | 5,804 kB |
| qemu-mips-static, target ELF | 12/8/1 | 0.21 s | 0.1988 s | 10,032 kB | 5,804 kB |
| qemu-mips-static, target ELF | 11/8/1 | 0.11 s | 0.1025 s | 7,984 kB | 5,808 kB |
| host, gcc-13 -O2 | 12/7/1 | 0.01 s | 0.0183 s | 4,864 kB | 1,664 kB |
| host, gcc-13 -O2 | 12/8/1 | 0.02 s | 0.0245 s | 5,376 kB | 1,664 kB |
| host, gcc-13 -O2 | 11/8/1 | 0.01 s | 0.0106 s | 3,328 kB | 1,664 kB |

**qemu time is not the device's time, and this table contains its own proof of
that**: qemu puts 12/8/1 *faster* than 12/7/1, which cannot be true — r = 8
performs 16/14 of the Salsa20/8 cores of r = 7 with identical control flow. The two
cells differ by 14 % of work and qemu's spread over nine runs is wider than that,
so the emulator cannot even *rank* two nearby parameter sets. The host ordering is
correct (0.0183 < 0.0245, and 11/8/1 at 0.0106 against 12/8/1's 0.0245 is 2.3×
where the work ratio predicts 2.0×).

The **RSS differences** are the portable part: host 12/8/1 − 12/7/1 = 512 kB
against a request difference of 512.4 KiB, and 12/7/1 − 11/8/1 = 1,536 kB against
1,535.6 KiB. Slope 1.000. The absolute figure to use is the allocation, which is
`3,672,704 bytes = 3,586 KiB` for the recommended set, not an RSS reading.

**推, the device**: ≈ 0.3 s per evaluation, with a range of 0.15 s to 0.8 s.
Derivation, so the range can be argued with: `2N = 8,192` BlockMix calls, each
`2r = 14` Salsa20/8 cores of ≈ 400 instructions plus ≈ 896 bytes of XOR ≈ 900
instructions, so ≈ 57 M instructions; at 400 MHz (`CPU-11`, 量) and CPI 2 that is
0.29 s, at CPI 4 it is 0.57 s. The memory side agrees in order: ≈ 3.5 MiB written
sequentially plus 4,096 random 896-byte reads plus the XOR traffic ≈ 11 MB of DRAM
traffic, which at 40–100 MB/s is 0.11–0.28 s. Both paths land in the same range,
which is why the range is quoted and not a number. **This stays 推 until the board
prints it**: the cell is `kdfbench eval 12 7 1` on the console with the elapsed
from the program's own `CLOCK_MONOTONIC`, and `VmHWM` from
`/proc/self/status` in the same run. If it comes out above 1.0 s, B3 is violated
and the answer is `log2N = 11` (2,100,224 bytes, half the work), not a wider B3.

### 5.5 Entropy: the refusal is the current behaviour, not a corner case

A salt comes from `/dev/urandom`, and `pwhash_salt()` **refuses** unless
`/proc/sys/kernel/random/entropy_avail` reads at least 128. 量 2026-09-30 on this
board: `entropy_avail` read **0** at 768 s of uptime and **0** again at 1613 s. So
a password cannot honestly be set on this unit today. brokerd answers LOGIN and
PWSET with `NOENTROPY`; httpd turns that into **503 with `"error":"noentropy"`**,
and the page says, in words, that the pool is not ready and that the firmware
refuses rather than using a weak salt. `/api/status` renders `entropy_avail` and
`auth_ready` so the state is visible without trying.

This is a fail-closed path that is *currently taken*, which makes it the one
error path in this program most likely to be exercised first. Feeding the pool is
a kernel item and not httpd's.

### 5.6 The four vector sets

Written from RFC 6234 (SHA-256), RFC 2104/4231 (HMAC), RFC 8018 (PBKDF2) and
RFC 7914 (scrypt, Salsa20/8, BlockMix, ROMix). No third-party code.

| where | result |
|---|---|
| host gcc-13, `-fsanitize=address,undefined` | 37/37, 0 sanitizer findings |
| host clang-18, same | 37/37, 0 findings |
| host gcc-13 `-O2 --big` (the RFC 7914 N=1,048,576 vector, 1 GiB) | 37/37, 7.98 s, 1,049,836 kB peak |
| **target ELF under `qemu-mips-static`** | **37/37**, exit 0 |
| `tools/hazlint` over the target ELF | **0 violations in 2,243 loads** |

The vectors' expected values were recomputed independently with Python
`hashlib`/`hmac`/`hashlib.scrypt` from separately typed inputs, 0 mismatches. That
rules out a typo in one of the two places, not in both.

**The control that makes the qemu run worth its minutes**: replacing the Salsa20
state load with a `memcpy` of a `uint32_t` array — the classic endianness bug —
leaves the host suite **37/37 green** and turns exactly the three scrypt vectors
red on the target. So the target run is load-bearing and its blast radius is right
(SHA-256, HMAC and PBKDF2 stay green, because they are byte-oriented).

---

## 6. Tests, sweeps and their numbers

`make -C src/httpd both O=…` runs the whole suite four ways: gcc-13 and clang-18,
each with and without `-fsanitize=address,undefined`, all with
`-Wall -Wextra -Werror -Wundef -Wshadow`. 量 2026-09-30: **387 cases, 4 × green, 0
warnings, 0 sanitizer findings.**

| program | cases | what it covers |
|---|---|---|
| `rootcheck.sh` | 24 | § 4: the privilege drop and the accept loop, as root, on a real port |
| `test_json` | 66 | the JSON battery: nesting bomb, huge number, long string, duplicate key, truncation at every offset, the writer's bounds |
| `test_http` | 105 | the shape refusals, the three counted limits at their boundaries, the truncation sweep, the corruption sweep, the traversal battery, the MIME table |
| `test_rl` | 20 | the token buckets, including a backwards clock and a zero rate |
| `test_routes` | 133 | the route matrix, the broker status mapping, the headers, the cookies, the config encoding, the limiter-before-broker order |
| `test_serve` | 26 | `srv_conn()` on a socketpair: the wire bytes, a silent peer, a five-write request |
| `test_kdf` | 37 | the four RFC vector sets, the blob, the cap |

Every program also declares how many cases it must have run and refuses if it ran
fewer: a suite that silently ran nothing is what a green tick hides.

### 6.1 The request-parser sweep

One valid POST with every header the program reads (request line, `Host`, `Cookie`
with both cookies, `X-RLX-CSRF`, `Content-Type`, `Content-Length`, a 27-byte JSON
body). 量:

* **256 truncations** — the first `L` bytes for every `L`. 0 were reported
  complete; 0 produced a status outside the table.
* **2,022 single-byte corruptions** — 8 substitutions (`00 0a 0d 20 25 2f 41 ff`) at
  every one of 256 offsets. 0 crashed under ASAN and UBSAN.

The invariant took two attempts, and the first one was wrong in a way worth
recording. "Accepted implies identical to the reference" is **false**: flipping a
hex digit of the session cookie yields a different, perfectly valid session, and
shortening `Content-Length` yields a shorter, perfectly valid body. 779 of the
cases were accepted-and-different. A test that demanded identity would have had to
be relaxed to pass, which is the one move not allowed, so the invariant was
restated per **region** instead: *a corruption inside one header may change only
the fields that header feeds.* A byte in `Host` may change nothing at all; a byte
in the body may change only the body; a byte in `Content-Length` may change the
length and the body. 量: **0 cases changed a field outside their region**, and 0 of
the accepted parses broke the structural invariants (`pathlen == strlen(path)`,
`path[0] == '/'`, `body_len == clen ≤ 4096`, every token empty or exactly 32 hex).

### 6.2 The traversal battery

**34 targets**, every one refused by `http_decode_path()`: plain `..`, `%2e%2e` in
both cases, `..%2f`, fully encoded, double- and triple-encoded (`%252e`,
`%25%32%65`), `..%5c` and a raw backslash, `%00` alone and as a truncator, `..`
above the root, empty first and middle segments, no leading slash, `.` and `..` as
whole segments, `..` after a filename, IIS-style `%u002e`, a `;` parameter, an
all-backslash path, a raw space, a bare `%`, a one-digit `%`, a non-hex `%`, three
segments deep, a trailing slash, a 292-byte name, bytes above 0x7f, the overlong
UTF-8 slash `%c0%af`, and `..` inside the API space.

**Five positive controls**, because a battery without them proves only that the
function can say no: `/static/style.css` decodes unchanged **and is served 200 with
`text/css` from the fixed table**, `/` serves `index.html`, a query string is
dropped rather than becoming path, `%2D` decodes to `-`, and a leading dot in a
name is not a dot segment. Plus three run-time refusals with a real tree: an
executable file in the web root is 404, a symlink out of the tree is 404
(`O_NOFOLLOW`), and an extension outside the MIME table is 404.

### 6.3 The mutation controls

量 2026-09-30, `make -C src/httpd mutate`. `mutate.py` refuses if its anchor has
moved, so a control cannot rot into a no-op. The mutants are built without
`-Werror`, because removing a check leaves the variable it read unused and a mutant
that will not compile is a control that never ran.

| control | what is removed | result |
|---|---|---|
| `traversal` | the `.` and `..` segment refusals **and** the whole-string backstop | **RED**, 3 cases: `T12 .. above the root`, `T16 a single dot segment`, `T17 a trailing .. segment` |
| `hdrcap` | the "more than 32 header lines" refusal | **RED**, 1 case: `33 header lines is refused with 431` |

Three cases and not thirty is itself the finding, and it is good news read
correctly: with the `..` rule gone, the other 31 targets are still refused — by the
`%` ban, the encoded-separator ban, the empty-segment rule and the two-segment
depth limit. The three that flip are exactly the ones where the `..` rule is the
only line of defence. Defence in depth means a single mutation moves few cases;
what the control establishes is that the battery *notices*, and it does.

### 6.4 The forbidden-construct audit

量 2026-09-30 over the eleven `.c` files this agent wrote, every counter shown
reading ≥ 1 on a control file that deliberately contains the thing:

| check | control | mine |
|---|---|---|
| `strcpy` `strcat` `sprintf` `atoi` `alloca` `system` `popen` `gets` `scanf` | 1 each (2 for `alloca`) | **0 each** |
| VLAs, `gcc-13 -Wvla -Werror` per file | 1 warning | **0** |
| cycles in the call graph, `gcc -fcallgraph-info` | 1 (`rec` → `rec`) | **0** across 11 translation units |

The first run of that audit reported `atoi`, `system` and `popen` **found** in my
files. All three were in *comments* saying those functions are not used. A counter
that cannot tell code from prose is not a counter, so every file now goes through
`gcc -fpreprocessed -dD -E` first — which strips comments without expanding
includes — and the control goes through the same pass, so a stripper that ate real
code would make the control go blind and say so. The tool is
`$FWRE_WORK/rebuild/s118/httpd/audit.sh` and `cycles.py`; they are not in the repo
because they are not in this agent's declared file list, and moving them in is a
proposal in the report.

### 6.5 What the tests do not cover

The real `bk_call()` against a real broker — `test_routes.c` and `test_serve.c` link
a fake, and § 4's `rootcheck` runs with no broker at all, so every route that needs
one answers 503 there. The stub key table in
`src/httpd/stub/cfgtab.c` is transcribed from `SPEC-R7.md` § 4 and **nothing checks
it against agent B's `src/lib/schema.c`**; `test_routes.c` prints it so a reviewer
can diff it by eye, and the reconciliation is an open item.

---

## 7. Fuzzing

Both harnesses are plain `main(argc, argv)` over one file, so the afl run and the
gcov run are over the same program: a coverage figure from a harness the fuzzer
never used is a number about nothing. `fuzz_http.c` feeds the input in chunks whose
size comes from the input's own first byte, so the incremental state machine is
exercised across splits, and it calls `http_decode_path()` on the same bytes so a
target no request line would carry is still reached. `fuzz_json.c` re-serialises
every successful parse through the writer and asserts the round trip keeps the
member count.

Thresholds were written before the first run, in `$W/THRESHOLDS.md`:
`http.c` ≥ 85 % line and ≥ 75 % branch; `json.c` ≥ 90 % line and ≥ 80 % branch; and
a **planted off-by-one** that the fuzzer must find inside 15 minutes — *if it does
not, the harness is not connected and every coverage figure is void*. The crash
input is replayed against the unmutated binary and must not crash it, so the
finding is attributed to the planted defect rather than to a pre-existing bug.

### 7.1 The first planted off-by-one was invisible, and that is worth keeping

The control was first planted in `http_feed()`'s line-buffer bound: `>=` became
`>`, so `line[1025]` is written in a 1025-byte array. 量 2026-09-30, on the exact
input that triggers it (a request line of exactly 1024 bytes), the mutant built
with `AFL_USE_ASAN=1` returns **0**. No report, no crash, nothing for a fuzzer to
find.

The reason is a layout fact: `line` is a **member** of `struct http_parser`, and the
member after it is a pointer, so `line` ends at offset 1049 and the pointer starts
at 1052. Byte 1025 of `line` lands in the struct's own two bytes of padding.
AddressSanitizer instruments *object* boundaries, not intra-object ones, and this
write never leaves the object. Fifteen minutes of fuzzing would have found nothing
and the pre-registered rule would have voided the coverage figures — for a defect
that is real and a sanitizer that cannot see it.

So the control moved to `parse_header()`'s header-name bound, where `name` is a
**bare local array** and therefore gets its own ASan redzone. It is kept under the
name `linebound` in `mutate.py` with this paragraph attached, so the next reader
does not spend the fifteen minutes finding it out again. Two consequences worth
carrying forward: parser scratch in a bare local array is checkable and the same
scratch inside a struct is not; and ASan's silence about an intra-struct overflow is
not evidence.

### 7.2 A corpus that could not reach a single limit

The first ten seeds were ordinary requests, and 量: the longest header name in them
was 14 bytes against a 64-byte buffer, the longest request line 44 bytes against
1024, and the most header lines 5 against 32. **None of the parser's length limits
was reachable from the corpus**, which is a fact about the corpus that no
branch-coverage number would have made obvious. Four boundary seeds were added — a
60-character header name, a 990-byte request line, 30 header lines, and two
900-byte header values — chosen by reading `http.h`'s limits table. The 60 is
deliberately not 64: the planted defect triggers at exactly 64, so the fuzzer still
has to find the length.

### 7.3 The planted defect, and its attribution

量 2026-09-30. `mutate.py offbyone` in a copy of the tree, built with
`AFL_USE_ASAN=1 afl-clang-fast`, `AFL_BENCH_UNTIL_CRASH=1`, run twice — once
against each harness:

| | first harness | final harness |
|---|---|---|
| time to the crash | **56 s** | **149 s** (budget 15 minutes) |
| executions to get there | 30,076 | 150,759 |
| crash input | 294 bytes | 267 bytes |
| the same input on the **unmutated** ASAN binary | exits 0 | exits 0 — so the finding is the planted defect, not a pre-existing bug |
| the same input on the mutant | `stack-buffer-overflow`, `WRITE of size 1` | same |

The connected harness takes longer (149 s against 56 s) because it has 314 edges
instead of 256 and afl spends effort on the new ones; both are far inside the
budget.

Both halves of that attribution matter: a crash the unmutated binary also produced
would say nothing about the mutation, and a mutant that did not crash on its own
saved input would mean the crash was not reproducible.

### 7.4 The runs

量 2026-09-30, afl++ 4.09c, `-m none -t 2000`, one input file per execution, on a
host that was running other agents' fuzzers at the same time (so the exec rates are
a floor, not a benchmark).

| run | harness | wall | executions | corpus | edges | crashes |
|---|---|---|---|---|---|---|
| http, first | before § 7 was connected | 780 s | 1,419,076 | 414 | 250 | 0 |
| **http, final** | with `http_mime`/`http_reason`/`http_parse_all` | 780 s | 1,984,445 | 430 | **284** | 0 |
| json | — | 780 s | 2,175,735 | 425 | 243 | 0 |
| http mutant, first | off-by-one planted | 56 s | 30,076 | 170 | 256 | **1** |
| http mutant, final | same, connected harness | 149 s | 150,759 | 277 | 314 | **1** |

The two http rows are the same 780 s over the same corpus with only the harness
changed, and the connected one finds **34 more edges** — which is the coverage gap
of § 7.5 showing up in the fuzzer's own numbers rather than only in gcov's.

### 7.5 Coverage, against the thresholds written before the runs

gcov over the final afl queue plus the seed corpus, 444 and 435 inputs replayed
through the same harnesses the fuzzer used.

| unit | threshold | measured | |
|---|---|---|---|
| `http.c` lines | ≥ 85 % | **91.89 %** of 419 | met |
| `http.c` branches taken at least once | ≥ 75 % | **91.48 %** of 364 | met |
| `json.c` lines | ≥ 90 % | **95.50 %** of 289 | met |
| `json.c` branches taken at least once | ≥ 80 % | **94.37 %** of 213 | met |

**The first harness MISSED the `http.c` line threshold, at 84.96 % against 85 %,**
and that stays on the record. The threshold was not lowered by 0.04 points; the
harness was connected to the three functions it was not calling (`http_reason`,
`http_mime`, `http_parse_all` — 35 of the 63 lines it had never reached), the runs
were done again from the same corpus, and the number moved to 91.89 %. Which of the
two the threshold was "really" testing is answered by the edge count above: the
harness was the thing that was wrong.

What is still unreached, named rather than rounded away — 34 lines in `http.c` and
13 in `json.c`:

* **reason phrases for statuses the parser cannot produce** (11 lines): 200, 204,
  401, 403, 404, 408, 429, 500, 503 and the `default` arm are produced by
  `routes.c` and `serve.c`, not by `http_feed`, so a harness over the parser alone
  cannot reach them. The harness *asserts* that no status the parser does produce
  falls through to `default`, which is the property that matters.
* **guards that cannot fire by construction** (≈ 12 lines): `http_decode_path`'s
  `cap < 2` and its `tlen == 0` refusal (every caller passes `HTTP_PATH_MAX` and a
  non-empty target); the `bodygot + take > HTTP_BODY_MAX` assertion inside the body
  state, which `clen`'s own bound already makes unreachable; `http_feed`'s
  `HS_ERR`/`HS_DONE` re-entry returns, which need a caller that feeds after a
  verdict. These are assertions, and an unreachable assertion is the point of one.
* **two 431 paths** that need the running header total to cross 4,096 inside a line
  rather than at its end, and the 414 on a decoded path longer than 128 within a
  request line shorter than 1,024 — both reachable in principle, not reached in
  13 minutes.
* `json.c`: `JSONE_NUL` and `JSONE_MANY` (the harness's inputs stayed under 24
  members and afl rarely produces an embedded NUL that survives), the `json_get`
  NULL arms, and `json_w_str`, which only `routes.c` calls.

None of this is a claim that the parser is correct. It is a claim about which lines
ran, over one corpus, for 13 minutes each, with a planted defect proving the
harnesses are attached to the code they name.

---

## 8. Target build

`make -C src/httpd target O=… TC=… TRIP=…` — the compiler runs only under
`tools/vendor-tripwire.sh`, from a scratch directory, over sources staged onto ext4
and proved equal to the repository's by sha256 first (the rsdk driver is a 32-bit
i386 ELF whose `stat()` returns `EOVERFLOW` on every DrvFs path). `TCFLAGS` carries
**no `-march`** and the recipe refuses if one appears; `-fno-if-conversion` is
`config/rlxfw-cflags`' one flag, claimed for this project's objects only, because
that file says in as many words that it cannot reach the prebuilt `libc.a`.

量 2026-09-30:

| | |
|---|---|
| ELF | 32-bit MSB, MIPS-I, statically linked, no `PT_INTERP` |
| `e_flags` | `0x1007` (noreorder, pic, cpic, o32, mips1) — linkprobe's value for a C-only build |
| unstripped | 122,315 bytes |
| **stripped** | **83,604 bytes** — 1.59 % of the 5,242,880-byte decompressed image budget |
| `tools/hazlint` | **0 violations in 3,612 MIPS-I loads** |
| `system` / `popen` in the symbol table | **0 / 0** |
| objects kept | 8, in `$O/target/obj/httpd/` |
| vendor tripwire | CLEAN before and after, 6 trees watched |

That table is the build **before** the § 11 fix; § 11.8 has the one after it and
the delta, and it is the row `SPEC.md` should carry.

`src/lib/kdf.c` and `src/lib/sha256.c` are **not** linked into `httpd`: the target
ELF holds no crypto at all. They are cross-built separately for `test_kdf` and
`kdfbench` and get the same hazlint gate (0 violations in 2,243 loads).

One difference between host and target was found by the target build and by nothing
else: `O_NOFOLLOW` is hidden behind `__USE_GNU` in uClibc 0.9.30's `fcntl.h`, so
`routes.c` builds on the host and fails to compile for the device without
`#define _GNU_SOURCE`. That is the class of thing the cross build exists to catch,
and it was a compile error rather than a silent behaviour change only by luck.

---

## 9. Applying this alongside the other R7 agents' trees

讀 2026-09-30, the tree this lands in. Two things will not merge by themselves:

1. **`src/lib/kdf.h` already exists** — an `-ENOSYS` stub with a `KDF_IMPLEMENTED`
   feature macro, which `src/cfgstore/main.c:569` reads. `git apply` refuses to
   create a file that is already there, so the stub is **deleted first** and this
   patch applied second. To make that a delete-and-apply rather than a cross-file
   edit, this `kdf.h` keeps every name the stub defined — `KDF_IMPLEMENTED` (now
   1), `KDF_ALG_SCRYPT`, `KDF_PWHASH_LEN`, `KDF_SALT_OFF`, `KDF_SALT_LEN`,
   `KDF_KEY_OFF`, `KDF_KEY_LEN` — with the values SPEC-R7 § 4.2 gives them.
   One semantic difference to carry: the stub documents `kdf_scrypt` as returning
   "a negative errno"; this one returns `-KDFE_*`, based at 200 so the two spaces
   cannot be confused (§ 5 and the header say why).
2. **`src/lib/schema.h` exposes the key table as an array**
   (`extern const struct cfg_key cfg_keys[CFG_NKEYS]`), not as the three accessors
   `routes.c` calls. So `src/httpd/Makefile` does **not** switch from
   `stub/cfgtab.c` to `schema.c` automatically — a wildcard that switched would
   fail to link and look like a build problem instead of an interface decision.
   Adopting `schema.c` is one include change plus three accessors, in the commit
   that also diffs the two transcriptions of SPEC-R7 § 4 against each other.
   `stub/client.c` **does** switch automatically, because `src/lib/client.c` and it
   implement the same pinned wire format.

## 10. What this does not establish

* **No TLS.** HTTP only: every password on this port crosses the LAN in clear.
  `SPEC-R7.md` puts R7g outside this gate, and the page says so in its footer.
* **Almost nothing has run on the device.** § 11 is the exception: image `r78a`
  served `/api/status` and refused `/api/login` on the silicon on 2026-09-30, and
  that refusal was a defect. The privilege drop and a real KDF evaluation are
  still unmeasured there. Every timing figure for the device is 推 with its
  derivation written down; the qemu figures are measurements of qemu, and § 5.4
  contains the evidence that they cannot even rank two nearby parameter sets.
* **No broker has answered.** Every route test links a fake `bk_call`. The wire
  bytes of `src/httpd/stub/client.c` are a second, independent encoding of
  `SPEC-R7.md` § 6, and two independent encodings of the same table are exactly as
  likely to disagree as to agree; the byte-level reconciliation against agent C's
  `proto.c` has not happened.
* **The schema table is transcribed, not shared.** See § 6.4.
* **No claim about side channels.** Only `ct_memeq()` and `route_ct_eq32()` are
  constant time; scrypt's access pattern is password-dependent by design, and
  nothing here measures a timing channel in the route layer.
* **No claim that a cleared buffer cleared DRAM.** `srv_conn()` zeroes the request
  and response structs and `h_password()` zeroes its body, but a compiler may delete
  a store nothing reads, and nothing here verifies the store survived.
* **The D8 acceptance test is not done.** § 4's `rootcheck` shows the 429 arriving
  after the burst on this host, but the acceptance test `plan` § D8 asks for is the
  **memory high-water mark** under N concurrent login attempts with a real broker
  doing real scrypt — and its refutation control, the same test with the limiter
  removed making the machine lose responsiveness. Both need the device and
  `brokerd`. Open item, not a passed test, and the refutation control is the half
  that matters: without it, a green run proves nothing.

## 11. The login limiter refused for ever (量 2026-09-30, image `r78a`)

The first thing this program did on the silicon was lock the administrator out.
It is worth writing down in full, because the host suite was green at the time
and stayed green, and the reason is not the arithmetic anyone would look at
first.

### 11.1 What the device did

`POST /api/login` answered `HTTP 429 {"ok":false,"error":"ratelimit",`
`"retry_s":2}` and never stopped:

| 量 | observation |
|---|---|
| first attempt of the session | 429 in 0.040 s, before any KDF evaluation |
| after 20 s of no requests | 429, `retry_s: 2` |
| after a further 90 s of no requests at all | **still** 429, `retry_s: 2`, 0.030 s |
| the same minute, `GET /api/status` | 200 |
| uptime | 640–830 s |

A refusal before the KDF is correct and is the whole point of § 5.2; a refusal
that never lifts is not. `/api/status` answering 200 says httpd was alive,
accepting, forking and answering, so only the path that asks for a grant was
broken. A password was set (`cfgstore passwd` had succeeded, `admin.pwhash=set`,
`auth_ready:true`), and before it existed the same route answered
`401 {"error":"auth"}` — so the 429 was the limiter and not the credential.

### 11.2 It was not the bucket, and here is how that was settled

`retry_s: 2` held constant across a 90 s idle gap is the whole clue.
`rl_retry_s()` names `(1000 - tokens_milli + rate - 1) / rate + 1` seconds, so:

* the global login bucket (250 milli-tokens/s) names **5** when it is empty, and
  names 2 only from `tokens_milli` in [750, 999];
* the per-address bucket (100 milli-tokens/s) names **11** when empty, and names
  2 only from [900, 999].

Both windows mean "within a second or two of granting", and a bucket in that
state grants within a second or two. A constant 2 is not a bucket.

Measured rather than argued, before any product code was touched:

* the device's timeline replayed against `rl.c` with the clock supplied — burst
  spent at uptime 640 s, then +60 s, then +20 s, then +90 s — **grants** the
  login at every one of the three gaps;
* a sweep of 2,709,903 reachable `(tokens_milli, last_ms)` pairs per bucket:
  **0** of them refused after a 90 s gap with no call in it. `dt = 90000` forces
  `add` to 22,500 (global) or 9,000 (per-address) milli-tokens, both above a
  3,000 milli-token cap, so the saturating branch fires from every state.
  `test_rl.c` now carries the thirteen-state version of that sweep as a standing
  case, with its refutation condition written into the comment above it.

Both runs are in `$FWRE_WORK/rebuild/s118/rlfix/`, and neither is product code.

The clock was checked in the same pass, because the obvious second suspect was a
unit mix-up: `now_ms()` is `clock_gettime(CLOCK_MONOTONIC)` converted to
milliseconds, **not** a `times()` tick count. This kernel's
`INITIAL_JIFFIES = -300*HZ` therefore never reaches the buckets — a `times()`
clock would have started near −30,000 and returned −1 at 299.99 s of uptime —
and 640–830 s of uptime is nowhere near the 49.7-day wrap of a 32-bit
millisecond field. The two bugs `rl.c`'s own comments record (refilling a
zero-rate bucket after a long gap; dropping the refill remainder) were both
already fixed and neither is reachable here: the login rate is not zero, and the
remainder is carried by advancing `last_ms` only by what the granted tokens cost.

### 11.3 The mechanism: one piece of state, two copies, one of them maintained

`srv_loop()` kept the identity of the child holding the one KDF grant **twice**:

* `kids[i].holds`, a byte in the children table, and
* `int kdf_inflight`, a local of `srv_loop()`.

The decision read `kdf_inflight`. `reap()` cleared `holds`. `reap()` is a
separate function and cannot reach a local of its caller, so it could not clear
`kdf_inflight` — and `reap()` is how a child that has exited stops existing.

The structural reason it fires is the order inside the loop, not a race: `reap()`
runs at the **top** of each iteration, before `select()` and before the ready-fd
scan. It closes `kids[i].fd` and therefore **discards whatever was still unread
on that channel, an unread release byte or EOF included** — and both places that
cleared `kdf_inflight` needed to read from that fd. So a child granted the KDF
(`kdf_inflight = i`) that exits without its last byte having been read leaves the
marker set for ever: `srv_kdf_ask()`'s first branch is taken by every later
login, and the constant in it — now `SRV_KDF_BUSY_S`, then a literal `2` — is the
`retry_s` the device reported.

Two ways to arrive there, and neither needs the other:

* the child never sent a release byte at all — killed by its own `alarm()`,
  crashed, or its `wr_all()` failed — so the only clearing path was the EOF read,
  and `reap()` got there first;
* the parent was not sitting in `select()` when `SIGCHLD` landed (it was in the
  accept-and-fork block, or reading another child's byte), so `got_chld` was set
  and the next iteration reaped before it scanned.

`SIGCHLD` is installed without `SA_RESTART` so `select()` returns on it, which
adds a third route via `EINTR` → `continue` → `reap()`; that one **is** a race
against `select()`'s return value, because Linux's `do_select()` returns the
ready count rather than `EINTR` when an fd was already ready. It is listed third
for that reason, and nothing in the fix depends on which of the three fired.

That is also why the buckets looked innocent from the outside and were: the
refusal happened before either of them was consulted, which is why it took
0.030 s and why it was indifferent to 90 s of idling.

### 11.4 The fix, and the test that had to fail first

There is now **one** copy of the holder: `kids[i].holds`, in the table `reap()`
already clears. `kdf_inflight` is gone. `srv_kdf_ask()` scans eight bytes for a
holder instead of reading a cached answer, and every "this child no longer holds
it" path — the release byte, the channel closing, and `reap()` — goes through
one function, `srv_kdf_gone()`.

The arbitration moved out of the body of `srv_loop()` into `srv_kdf_reset()`,
`srv_kdf_ask()` and `srv_kdf_gone()`, declared in `serve.h`, for one reason: a
host test can now drive the **deployed** decision with its own clock, with no
fork, no socket and no listening port. That reason is the lesson of this defect
and not a tidiness argument. The bucket that `brokerd`'s suite tests and the
bucket httpd deploys are two different implementations, and only one of them had
a test; the honest form of that statement is narrower and worse, and it is in
§ 11.7.

The reproduction was built first, against a tree carrying the same seam with the
deployed two-marker behaviour kept, and it went red:

```
not ok 30 - a grant whose holder was reaped is not still held: got 0 want 1
not ok 31 - and after 20 s of no requests a login is granted: got 0 want 1
not ok 32 - and after a further 90 s of no requests at all: got 0 want 1
not ok 33 - the burst, and only the burst: got 1 want 3
not ok 35 - and at that time the login IS granted: got 0 want 1
not ok 36 - a client that waits quietly is granted at the tick its rate says: got 0 want 100
not ok 41 - and by that bucket's own wait, not the busy constant: got 2 want 5
not ok 42 - a refusal the global caused did not charge the address' own bucket: got 0 want 1
# 37/45 passed (declared at least 45)
```

Case 41's `got 2 want 5` is the device's own number, produced on the host.

`test_serve.c` carries nineteen cases now, and three of them are controls rather
than reproductions: the arbitration must still **permit** a first login, must
still refuse a second asker while one evaluation is genuinely in flight, and must
still refuse it ten minutes later if that holder is still alive — because the
bound on a running evaluation is the child's own `alarm()`, not a timer in the
parent, and a "fix" that expired the grant on a clock would have passed the
reproduction while breaking plan D8 ruling 3.

### 11.5 A second, smaller defect, found while proving the first

The chain consulted the per-address bucket first and the global second, and
`rl_table_take()` **consumes**. An attempt the global refused had therefore
already been charged to the asker's per-address bucket: one refusal, two buckets,
and the slowest bucket here (one token per ten seconds) draining faster than the
rate `rl.h` declares. `rl_table_refund()` gives that token back on exactly that
path, and `test_serve.c`'s case for it is arranged so the arithmetic cannot hide:
three other addresses drain the global bucket, one address is refused by it three
times at a single instant, and four seconds later — when the global holds exactly
one token — that address may have it only if its own bucket kept its burst.

This is the same family as § 11.3 (a refusal changing state it did not pay for)
but it is **not** what the device did: it self-heals in at most eleven seconds and
no sequence of it refuses across a 90 s gap.

### 11.6 `dnsfwd`'s per-client cap does not share it

Asked directly, because it is a third hand-written token bucket (20 q/s, burst
40, `dns_rate_allow()`). The answer is no, on four counts:

* `dnsfwd` has no `fork`, no parent/child channel and no reaper, so there is no
  second copy of any limiter state to leave unmaintained. Its whole state is
  `d->rate`, with one writer.
* `t_ms` is written on **every** path through `dns_rate_allow()`, so no slot can
  freeze at a stale time.
* a sweep of 27,937 reachable `(tok_m, t_ms)` states: **0** refused after a 90 s
  idle gap.
* a refusal does not charge: 500 refused queries at one instant left `tok_m` at
  0, and the first millisecond at which a drained client is granted is 50 whether
  it stays quiet or is refused at every millisecond of the wait.

One real difference, and it points the other way, so it is a finding and not this
defect: `dns_rate_allow()` computes `dt = now_ms - t_ms` unsigned with no
backwards-clock guard, so a 32-bit millisecond wrap hands every client one free
full burst. `rl.c` refuses in that case and has a case for it. Left alone
deliberately — it is once per 49.7 days, it is too permissive rather than too
strict, and it is not the bug being fixed.

### 11.7 What § 11 does not establish

* **The fix has not run on the device.** The image needs rebuilding. Everything
  above is a host measurement plus a reading of the deployed source.
* **"The tested implementation and the deployed implementation were different
  code" is true but it is not the headline.** The deployed limiter had a test
  file of its own, `test_rl.c`, and that file was right: its subject genuinely
  was not broken. What had no test at all was the **state machine around** the
  bucket — the parent's one-grant arbitration — because it was written inside a
  `for (;;)` loop that needs `fork()`, `accept()` and a listening socket to
  enter. The defect lived in the only part of the login path that no unit test
  could reach, and it got there by being unreachable, not by being untested on
  purpose.
* **Nothing here covers the socketpair.** Not the five-byte encoding, not
  `select()`'s ordering against `SIGCHLD`, not a child that neither releases nor
  closes. All three routes in § 11.3 are read out of the source; none is
  reproduced as a running parent and child, and the third one's outcome depends on
  a kernel detail this project has not measured. The fix does not depend on which
  fired: it removes the state they corrupted, so a test of the arbitration is
  enough and a test of the race is not needed to show the marker cannot leak.
* **The exact trigger on the device is undetermined.** Any child that exited
  while holding the grant produces it, and the captures from that seating do not
  say which one did. 未定, and it does not change the fix.
* **No claim that this was the only defect between the host and the silicon.**
  It is the one that was measured.

### 11.8 The target build after the fix

量 2026-09-30, same toolchain, same flags, same gates as § 8:

| | § 8, before | after | delta |
|---|---|---|---|
| unstripped | 122,315 | 123,224 | +909 |
| **stripped** | **83,604** | **83,836** | **+232 bytes (+0.28 %)** |
| `hazlint` | 0 violations / 3,612 loads | **0 violations / 3,740 loads** | +128 loads |
| `e_flags` | `0x1007` | `0x1007` | — |
| `system` / `popen` | 0 / 0 | 0 / 0 | — |
| vendor tripwire | CLEAN | CLEAN, 6 trees watched | — |

+232 bytes on a 5,242,880-byte decompressed budget is 0.0044 % of it. The whole
increase is `kdf_holder()`'s eight-byte scan, `rl_table_refund()`, and the two
extra non-static entry points the link can no longer inline away.

One thing the cross build caught that gcc-13 did not: `srv_kdf_ask()`'s clock
parameter was first called `now_ms`, which shadows `serve.c`'s static `now_ms()`.
gcc-13's `-Wshadow` is silent on a parameter shadowing a function; the rsdk 4181
gcc warns, and `-Werror` made it a refused build. That is the second time in this
file the cross build found something the host could not (§ 8 has `O_NOFOLLOW`),
and it is the argument for running it on every change rather than at the end.
