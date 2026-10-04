# dnsfwd — rlxfw's DNS forwarder

R7, segment 118. Source: `src/dnsfwd/` (`dns.h`, `dns.c`, `main.c`,
`test_dns.c`, `Makefile`, `stub/`), fuzz harness `src/fuzz/fuzz_dns.c`, seed
corpus `src/fuzz/corpus/dns/`.

The seeds are named `*.pkt`, not `*.bin`, and that is not a style choice: 量
2026-09-30, `.gitignore`'s `*.bin` — the rule that keeps flash dumps and vendor
binaries out of the tree — **silently swallowed all 15 of them**, and
`git add -A -N` reported nothing. They are 579 bytes of hand-written DNS
packets, largest 81 bytes, none of them from a dump. Anything else adding a
binary fixture under `src/` will hit the same rule.

## 1. Why it exists, and what it is

讀 `SPEC.md` `FW-20`: the vendor rootfs ships `bin/dnsmasq` and it imports
`popen`. R7's pass condition is that the shipped rootfs imports `system` and
`popen` zero times, so keeping dnsmasq would fail the gate by itself; the
plan's ruling (§ `R7f` item 3) is to write the forwarder instead. dnsfwd binds
UDP :53 on the LAN address as root, drops to uid/gid 101 and verifies the drop,
takes `lan.ipaddr` and `dns.upstream` from brokerd at start and on `SIGHUP`, and
then does one thing: for each query from a LAN client it emits **one** fresh
query to the one configured upstream with a random 16-bit ID, and relays the
matching reply back with the client's own ID restored. It is not a resolver: it
never reads an AUTHORITY section for NS records, never follows a referral, and
refuses a query that asks for iterative service (`RD` = 0) rather than pretend.
It has **no cache** in R7 — see § 8. Everything about a byte on the wire lives
in `dns.c` behind an injectable `struct dns_io`, which is why the whole
forwarder is tested on the host without opening a socket.

## 2. Limits

| | value | what happens at the limit |
|---|---|---|
| UDP buffer, both directions | 512 bytes | `recvfrom` uses `MSG_TRUNC`, so a longer datagram is reported at its true length and refused as `DNSE_LONG` rather than silently cut down to something that parses |
| decoded name | 255 bytes incl. the root label | `DNSE_NAME` |
| one label | 63 bytes | enforced by the encoding: a length byte with its top two bits clear cannot exceed 0x3F |
| compression pointers per name | 64 | `DNSE_JUMPS` |
| RRs walked in a reply | 45 = (512 − 12 − 5)/11 | `DNSE_RRCOUNT`, checked from the header counts before any RR is read |
| answer RRs described to a caller | 16 | the rest are still walked and bounds-checked, just not stored |
| in-flight queries | 64 | a full table **drops the new query** and sends nothing; it never grows and never answers, because a SERVFAIL here would turn table pressure into outbound traffic |
| upstream timeout | 4 s | the client gets SERVFAIL and the slot is freed |
| per-source rate | 20 queries/s, burst 40, 32-address table | over-rate queries are dropped in silence |
| processes started | 0 | dnsfwd contains no `fork`, no `exec*`, no `system`, no `popen` (§ 7) |
| static memory for the two tables | **18,436 bytes** (`dns_table` 17,924 + `dns_rate` 512; one entry is 280 B), whole `struct dnsfwd` 18,552 | 量 with `sizeof` on the host; 推 that the target agrees (same field types, 32-bit ABI both sides, not re-measured under the cross compiler). Nothing is allocated at run time at all — no `malloc` in dnsfwd |

## 3. The parser, and the guard that matters

Both directions are hostile. A LAN client's query is obviously
attacker-controlled; an upstream's reply is too, because an off-path attacker
races it and because the upstream is not trusted to be well-formed. So
`dns_parse_query` and `dns_parse_reply` are the same kind of function, share the
name decoder, and are both fuzz targets. No VLA, no recursion, no `alloca`, no
`memcpy` of a struct off the wire, every length checked against the bytes
remaining, and every integer decoded with explicit shifts (§ 6).

**The compression-pointer guard.** `dns_decode_name` carries three independent
termination guards and any one of them suffices:

1. a pointer's target must be **strictly less than the offset of the pointer's
   own first byte**;
2. every target must be **strictly less than the previous target**, so the
   sequence of jump targets strictly decreases and cannot revisit;
3. at most 64 pointers are followed.

Guard 1 alone is **not** sufficient, and that is the whole point of guard 2.
Targets 20, 25 and 30 can each sit below their own pointer's offset and still
form a cycle: the battery's `ptr/cycle3-backwards-legal` case is exactly that
shape (entry at 40 → 20, labels from 20 reach a pointer at 30 whose target 25 is
below 30, labels from 25 reach the pointer at 40 again) and guard 1 passes all
three hops. Guard 2 refuses it. Guard 3 exists because a proof that depends on
reading the argument above correctly is not a guard — and it earns its place:
it is what refuses the 200-pointer chain, in which every hop is legal under
guards 1 and 2.

**The Kaminsky check.** A reply is accepted only if **all four** of these agree
with a table entry: the source address, the source port, the 16-bit ID, and the
whole question section (name compared case-insensitively label by label, plus
QTYPE and QCLASS). That is the Kaminsky check: an off-path attacker who guesses
the ID still has to match the other three, and getting any one wrong drops the
datagram and leaves the genuine reply still acceptable. Two further properties
fall out of it: two in-flight queries are never allowed to share an upstream ID
(the ID is redrawn, up to four times), and the entry is freed on the first
accepted reply, so a second copy of the same datagram is not relayed twice.

**The outbound query is freshly encoded, never relayed.** Only the question
crosses from the client's datagram to the upstream's; the client's ID, AD/CD
bits, opcode and any trailing bytes do not exist on the wire we emit. The
inbound reply, by contrast, **is** relayed byte for byte — but only after every
record in every section has been walked and bounds-checked — with the two ID
bytes rewritten. Nothing is re-encoded, so a legitimate answer reaches the
client unaltered.

**Who may ask.** An open forwarder is a reflection and amplification weapon: a
40-byte spoofed query returns a much larger reply to a victim of the attacker's
choosing. So the source address is checked against the LAN prefix *before
anything is parsed*, and a query from outside is dropped **in silence** — an
error reply would itself be the amplification. The network and broadcast
addresses of the prefix, and 0.0.0.0, are refused as sources too.

**Decisions this file owns.**

* **EDNS0: FORMERR, not truncation.** Any additional record in a query is an
  OPT (or a TSIG); R7 implements neither, so the query is answered FORMERR.
  RFC 6891 § 7 names FORMERR as the answer of a server that does not implement
  EDNS0, and it is the *cheaper* refusal here: setting TC = 1 tells the client
  to retry over TCP, and dnsfwd has no TCP at all, so TC = 1 would buy a wasted
  round trip before the same failure. A resolver that gets FORMERR falls back
  to plain DNS immediately. An OPT record in a **reply** is refused the same
  way, because dnsfwd does not relay bytes whose meaning it declines to
  implement.
* **`/run/wan.dns` is not read.** The brief allows it; dnsfwd does not. brokerd
  is the single source of the upstream address, and `ifupd` runs as root and can
  SET `dns.upstream` when DHCP learns it. One piece of state, one owner — and a
  second input path would be a second parser on an unauthenticated file. The
  cost is a dependency on `ifupd` doing that SET; if it does not, dnsfwd
  forwards to whatever the store holds.
* **Source-port randomisation is per-process, not per-query.** One upstream
  socket takes its ephemeral port from the kernel while dnsfwd is still root,
  and is then `connect()`ed to the upstream so that the kernel *also* drops
  datagrams from anywhere else — a second source for the address half of the
  check, not a replacement for it. A fresh socket per query would add ~16 bits
  of guess space at the cost of a socket per query; that trade is not made in
  R7 and is written down here as the thing to revisit.

## 4. Entropy: a stated weakness, not a footnote

The only unpredictable field in an outbound query is the 16-bit ID, read from
`/dev/urandom`. 讀 `SPEC-R7` § 6, which cites 量 2026-09-30 on the `r6b8i`
image: `/proc/sys/kernel/random/entropy_avail` = **0** at 768 s uptime
(`bench/2026-09-30/SB-ENT.log`; that capture is **not** in the tree this note
was written from, so this line is 讀 from `SPEC-R7`, not re-measured here).

Consequence, stated plainly: on this device today `/dev/urandom` is seeded by
whatever the kernel managed to gather with no entropy accounting, so the ID
stream must be assumed **weak and possibly predictable**, and the 16 bits of
Kaminsky resistance must be assumed to be fewer than 16. dnsfwd does not
pretend otherwise: it has no fallback to a counter or to `time()`, and if
`/dev/urandom` cannot be read at all it answers SERVFAIL and forwards nothing
(`table/no-entropy`). What actually fixes this is feeding the pool, which is a
kernel item and not dnsfwd's; until then the honest claim is "the four-part
match is implemented", not "spoofing is hard here".

## 5. The battery, and what tests the tests

`make -C src/dnsfwd test O=…` — 量 2026-09-30, on both compilers, every
translation unit under `-fsanitize=address,undefined` with
`UBSAN_OPTIONS=halt_on_error=1`:

| | gcc-13 | clang-18 |
|---|---|---|
| checks / failures | 3,701 / 0 | 3,701 / 0 |
| compression-pointer battery | 15 cases, 12 refusals, 3 positive controls | same |
| truncation sweep | 454 cases: **454 refused, 0 accepted** | same |
| single-byte corruption sweep | 2,270 cases: 1,461 refused, 809 accepted, **0 crashes, every bound held on every accepted result** | same |

The truncation sweep is every prefix length of four valid messages (33-byte
query, 49-byte A reply, 78-byte NXDOMAIN-with-SOA, 67-byte CNAME chain) through
both parsers; the corruption sweep is **every** offset of those four messages,
not a sample, with five mutations each (XOR 0x01, XOR 0x80, XOR 0xFF, set 0x00,
set 0xC0). 809 accepted is the right shape, not a failure: a flipped bit in a
TTL, in label content or in rdata still yields a well-formed message, and what
is asserted about those is that the invariants hold (`nlen` ≤ 255, `n_an` ≤ 16,
`rdoff + rdlen` ≤ n) and that ASan/UBSan say nothing.

The battery's refusals are: pointer to itself, forward pointer, two-pointer
cycle, the three-hop cycle guard 1 permits, a 200-pointer chain, a target past
the packet end, a pointer byte as the last byte, a name over 255 bytes, the
256-byte boundary, both reserved top-bit patterns, and a label length running
off the end. Its **positive controls** are a legal one-hop pointer (decoded and
its value checked, including that `next` advances by exactly 2), the root label
alone, the exactly-255-byte name, and — the strongest one — the CNAME chain's
second answer RR, whose name is a **two-hop** compressed name (51 → 45 → 16)
that must decode to `cdn.example.com`.

**Mutation controls.** A green suite is a claim about its controls; these are
what test them. Both are named compile-time mutations, and `make target`/`make
host` refuse to build a product with either defined
(`make mutant-guard-selftest` shows the guard refusing *and* permitting):

| mutation | required outcome | 量 2026-09-30 |
|---|---|---|
| `DNSFWD_MUT_NO_PTR_GUARD` — all three pointer guards removed | a battery case must hang or fail | **hung**: `FAIL: TIMED OUT … in case ptr/self`, exit 3. The suite arms `alarm(5)` around every pointer case precisely so the classic infinite loop is *reported* rather than waited out |
| `DNSFWD_MUT_NO_QMATCH` — the question half of the reply match removed | an anti-spoof case must go red | **red**: `spoof/different-question` relayed 1 datagram for a question never asked, and `spoof/positive-control` then relayed 0 |

The unmutated suite is run first and the mutants are only interpreted if it
passed.

## 6. Byte order, twice

The target is big-endian, the host that runs the tests is little-endian, and
MIPS-I faults on an unaligned halfword load — so every integer goes through
`dns_get16`/`dns_get32`/`dns_put16`/`dns_put32`, which are explicit shifts, and
no struct is ever `memcpy`'d to or from the wire. Two sources that this is
actually true:

1. the host tests assert the scalars against hand-written bytes (including a
   round trip at an odd address) and assert that re-encoding the known-answer
   query reproduces its 33 bytes exactly;
2. 量 2026-09-30, `make -C src/dnsfwd qemu`: the same 49-byte A reply decoded by
   the little-endian host ELF and by the **big-endian target ELF under
   `qemu-mips-static`** produces **byte-identical** output —
   `get16 1234 get32 DEADBEEF / reply rc 0 ok id 1234 rcode 0 qname
   www.example.com. an 1 walked 1 | rr www.example.com. type 1 ttl 300 rdlen 4
   rdoff 45`.

## 7. The honest comparison with `dnsmasq`

Symbol-level, static, no execution of anything — the vendor's `dnsmasq` was
never run. The vendor side used `upstream/tools/fwrecon`'s
`Elf32Reader.dynamic_symbols()` — a `PT_DYNAMIC` → `DT_SYMTAB` walk sized by
`DT_MIPS_SYMTABNO` — because 讀 `FW-20` these binaries carry no section header
table and `readelf --dyn-syms` prints nothing for them, and nothing is what
"pass" looks like. (`upstream/` is not populated in a fresh clone of the base,
so that reader was read out of the base's checkout, never written to, per
`SPEC-R7` § 1.)

| | 讀 | method |
|---|---|---|
| `bin/dnsmasq` dynamic imports, total | **120** (exports 96; `DT_MIPS_SYMTABNO` 217 = `DT_HASH` nchain 217, two sources agreeing) | PT_DYNAMIC walk |
| of those, able to start a process | **3: `popen`, `execl`, `fork`** (+ `pclose`, `waitpid`) | PT_DYNAMIC walk |
| `bin/udhcpd` | `system`, `execle`, `fork`, `daemon` | PT_DYNAMIC walk |
| `bin/busybox` | `execlp`, `execv`, `execve`, `execvp`, `fork`, `vfork`; **`system` and `popen` absent from `.dynstr` entirely** | PT_DYNAMIC walk |
| rootfs-wide | 55 ELFs; **31/55** by string scan, **28/55** by the walk; 3 of the 55 have no `PT_DYNAMIC` (statically linked) and are **undetermined** | both |
| **`dnsfwd`, pre-link objects** | **52 undefined symbols across 3 objects; 0 of 17 process-starting names** | `mips-linux-nm -u` |
| **`dnsfwd`, linked static ELF** | no `PT_DYNAMIC` and no `PT_INTERP`, so 0 dynamic imports by construction; and of 383 symbols in the unstripped link, **none of the 17 is defined either** — uClibc's `system()` code was not pulled in | `readelf -l`, `nm` |

Controls on the dnsfwd side: `socket`, `recvfrom`, `sendto`, `setuid` and
`read` are all seen as undefined (positive), `zzz_not_a_symbol` and
`popen_but_not_really` are not (negative), and `main`, `dnsfwd_on_client` and
`socket` are each found once in the link.

🔴 **Two method findings that matter to R7's own pass condition, both 量
2026-09-30 on dnsfwd's own artefacts.**

* A **naive substring scan** of dnsfwd's stripped binary finds `system`
  **4 times** — every one inside a uClibc `strerror` message: `Interrupted
  system call`, `Too many open files in system`, `Read-only file system`,
  `Interrupted system call should be restarted`. A substring counter would
  therefore report rlxfw's own clean forwarder as a `system` importer.
* The census's stricter variant — NUL-delimited wholly-printable runs,
  **whole-string** exact match — reports 0 for `system`, but it also reports 0
  for `socket` and for `dnsfwd`, i.e. **it cannot be given a positive control on
  this file at all**. A stripped static binary has no `.dynstr`, so no bare
  symbol name appears as a standalone run. Its 0 is therefore not evidence.
  The evidence for dnsfwd is the pre-link objects plus `nm` over the unstripped
  link, which is exactly the "pre-link objects" source R7 § 0 names.

## 8. No cache, deliberately

R7 has no cache. Not caching is cheaper to defend than bounding one: a cache is
a second place where an attacker-supplied name and TTL are stored, it needs its
own eviction under memory pressure on a 26 MB machine, and a cache-poisoning
argument has to be made about *it* as well as about the reply match. The cost is
one upstream round trip per query, which on a LAN router behind a resolver that
caches is a cost paid by the upstream, not by the client.

## 9. Target build

`make -C src/dnsfwd target O=… TC=… TRIP=…`, 量 2026-09-30, through
`tools/vendor-tripwire.sh` (verdict `CLEAN cmd-rc=0 6 tree(s) watched`), sources
staged onto ext4 first and every staged hash proved equal to the source:

| | |
|---|---|
| ELF | big-endian, `MIPS R3000`, `EXEC`, `e_flags 0x1007` (noreorder, pic, cpic, o32, mips1) — the same flags word as `linkprobe`'s C-only build |
| `PT_INTERP` | 0 |
| `tools/hazlint` | **0 violations** in 2,759 loads |
| size | **109,432 bytes linked, 72,108 bytes stripped** |
| objects kept | `$O/target/obj/dnsfwd/{dns,main,client}.o` |
| `-march` | none, and the build refuses if one reaches CFLAGS |

## 10. What this does NOT establish

* 🔄 **2026-10-04: all four device clauses of this bullet were falsified by
  `R7-8` on 2026-09-30, and the correction is `SPEC.md` `FW-175`'s.**
  ~~dnsfwd has never bound :53 on the RTL8196E, never dropped privileges there,
  never talked to brokerd, and the privilege-drop verification and
  `setuid(0)`-must-fail probe have never executed on the real kernel.~~ 量 on
  image `r78a`, two boots, no power action: `ps` shows `dnsfwd`'s USER column as
  `dnsfwd`; the boot prints `dnsfwd: running as uid 101 gid 101; setuid(0)
  refused (Operation not permitted)`, so the drop ran **and** the must-fail
  probe executed on the real kernel; dnsfwd is one of the two broker peers in
  those captures; and it **answered** a query — `R7-8`'s *shown running and
  answering* is met. **What survives, narrower**: every *number* in this note is
  量 on the host or in qemu, or 讀 out of an ELF — no coverage, fuzzing or
  timing figure here was taken on the die. ⚠️ Why the device's reply was
  `SERVFAIL` is 推. Owners of the device half: `SPEC.md` `FW-175`,
  `notes/userspace-integration.md`, `docs/GATE-RESULTS.md` entry 17;
  `docs/KNOWN-ISSUES.md` owns what depends on rlxfw's drivers.
* **No DNSSEC.** No validation, no AD-bit meaning, no DS/RRSIG handling. A
  client setting CD or AD does not get those bits honoured, because the
  outbound query is freshly encoded.
* **No EDNS0, no TCP, no cache, no IPv6 transport.** `AAAA` *records* are
  forwarded fine; dnsfwd itself speaks only IPv4 UDP.
* **The import claim is about capability, not use.** dnsmasq importing `popen`
  does not show that any path reaches it; dnsfwd importing none of the 17 does
  not prove it cannot start a process by some other means (a raw `syscall()`
  would not appear as an import — 量: `syscall` is not among dnsfwd's 52
  undefined symbols either, but that is a second check, not a proof of the
  first).
* **3 of the vendor's 55 ELFs are undetermined**, not clean: they are static and
  have no imports to walk, and one of them (`bin/updatedd`) carries a whole-run
  `system` string. The rootfs number is "28 confirmed, ≤ 29", not 28.
* **The fuzz numbers bound the harness, not the program.** § 5's sweeps and
  § 11's coverage say which branches were reached, not that the unreached ones
  are correct — and **T3 was not met**: 61.9 % of `dns.c`'s branches were never
  taken by the fuzzer, because the forwarder engine is outside the harness.
  The battery covers it; the fuzzer does not.
* **The rate limiter does not stop amplification** — the LAN check does. With
  32 slots and LRU eviction, an attacker spraying 33 source addresses gets a
  fresh bucket each time; the bucket only stops one LAN host starving the
  others.
* **`lan.netmask` is not one of the keys SPEC-R7 § 6 grants uid 101**, so the
  off-LAN check may be running on the schema's default /24 rather than the
  configured prefix. See the SPEC DEVIATIONS in the segment's report.

## 11. Fuzzing

Pre-registered before the run (`$FWRE_WORK/rebuild/s118/dns/fuzz-prereg.txt`,
timestamped 2026-09-30 01:32:34 UTC with the sha256 of `fuzz_dns.c` and
`dns.c`): T1 `dns_decode_name` branch coverage ≥ 80 %, T2 `dns_parse_reply`
≥ 70 %, T3 `dns.c` whole-file ≥ 65 %, T4 the planted off-by-one must be found
within 15 minutes or T1–T3 are **void**, T5 the clean binary must report 0
crashes and 0 hangs. T1's ceiling is below 100 % on purpose: `dns_decode_name`
opens by rejecting NULL pointers and an out-of-range `outcap`, neither of which
a harness input can produce.

量 2026-09-30, afl++ 4.09c, `afl-clang-fast` + `-fsanitize=address`, `-m none`,
on the final source (the campaign was re-run after `dns.c` changed; the
pre-registration file records that the source moved and the thresholds did
not):

| | result | threshold |
|---|---|---|
| clean binary, 720 s | 360,650 execs at 501/s, 113-entry corpus, stability 100 %, bitmap coverage 38.11 %, **0 crashes, 0 hangs** | **T5 met** |
| `dns_decode_name` branch | **80.56 %** (36 branches, 7 missed) | **T1 met** (≥ 80 %) |
| `dns_parse_reply` branch | **100.00 %** (32 branches) | **T2 met** (≥ 70 %) |
| `dns.c` whole-file branch | **38.10 %** (294 branches, 182 missed) | 🔴 **T3 NOT MET** (≥ 65 %) |
| planted off-by-one found | **4 s**, 202 execs | **T4 met** (≤ 15 min) |

For reference, not as a substitute for T3: `dns_parse_query` reached 95.83 %
and, counting only the six functions the harness actually drives
(`dns_decode_name`, `dns_name_eq`, `dns_parse_query`, `dns_parse_reply`,
`question_decode`, `lc`), 102 of 116 branches were taken = 87.9 %.

🔴 **T3 failed, and the threshold was the defect, not the code.** T3 was
registered against `dns.c` as a whole while the harness by design drives only
the parser half; `dns_on_lan`, the in-flight table, the rate limiter,
`dnsfwd_on_client`, `dnsfwd_on_upstream`, `dnsfwd_tick`, `answer` and
`dns_strerr` are all at 0.00 % because nothing in `fuzz_dns.c` calls them —
they are covered by § 5's battery instead. The threshold is **not being moved**
to make the result pass. What fixes the experiment is a second harness that
drives `dnsfwd_on_client`/`dnsfwd_on_upstream` through the fake `dns_io`, which
is worth doing because those two ARE reachable from the network; until it
exists, the honest statement is that **the forwarder engine is covered by the
battery and not by the fuzzer**.

**The planted defect, and its controls.** `make fuzz` copies `dns.c` into
`$O/fuzz/bugtree/` and changes the label-length bound `pos + 1 + c > n` to
`> n + 1` (the build refuses if the anchor does not match exactly once, or if
the copy comes out identical to the original). 量:

* three of the 15 seeds trigger it directly — via the harness's
  `eat_name(buf, n, buf[0] % n)` entry, where a first byte of 0x12 = 18 and an
  18-byte input make the label at offset 0 read one byte past the buffer — so
  the first campaign's "1 s" measured almost nothing. **The run reported above
  used a reduced 12-seed corpus with every triggering seed removed** (control:
  all 12 exit 0 on the clean binary), and afl still found it in **4 s / 202
  execs**;
* ASan on the crashing input: `heap-buffer-overflow … READ of size 1 … #1
  dns_decode_name …`, naming the bug tree's copy at the planted `memcpy`
  (the line number is quoted in the run log, not here: a `file.c` plus a number
  in a tracked `.md` is what `citecheck` reads as a citation);
* **the control that matters**: the same crashing input on the **clean** binary
  exits 0 with 0 bytes of stderr. The crash is the defect, not the input.

**One afl abort was diagnosed, not waved away.** An earlier attempt aborted at
`perform_dry_run` with *'ptr_fwd.bin' results in a timeout* (>1,000 ms). 量:
`ptr_fwd.bin` takes **2.7 ms** per run on the clean binary and 17 ms on the
ASan-reporting bug build, and the load average at the time was **12.78** with
another agent's fuzzers on the same box. It was machine load; the re-run used
`-t 5000`. The parser is not slow on that input — the clean binary refuses it
in the battery's own way (`query rc -3 compression pointer not backwards`).
