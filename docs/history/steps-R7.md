# `PROGRESS.md` § `R7`'s step list, archived verbatim

Moved here verbatim from `PROGRESS.md` in `R7`'s closing commit on 2026-09-30, once its
rows were closed. A record: never edited. Cite a step by its id; `tools/docmove.py`
proves the move.

## `R7`'s step list — ✅ CLOSED 2026-09-30, in one segment (118th)

**Gate:** my userspace (§ Gate board, row `R7`). **Opened** 2026-09-30 by the
owner, who asked for `R7` and `R8` in one segment. The relaxation of 2026-09-27
carries over and was widened the same day: no frozen cards, predictions only
where they earn it, no desk-sweep per commit, tests beside the code. **Nothing
in `R7` writes flash**, the power handshake stands, and the board is never left
at the loader prompt (`NET-165`).

### The scope ruling this list opens with

The row's pass condition — `system()`/`popen()` = 0 from two independent
sources — was written on 2026-08-25 against the vendor's **dynamically** linked
rootfs, and rlxfw's own programs are **static**. A `PT_DYNAMIC`/`DT_SYMTAB` walk
finds no such segment in a static ELF, and `nm --undefined-only` cannot see
`system` because a static link *defines* it. Each named source therefore returns
0 on every rlxfw binary whatever the code does, and 0 is the passing answer:
this is the repository's own `R-28` class, a tool that cannot fail, reappearing
one level below where it was first caught. `R7-0` re-specifies both sources and
gives each a planted positive control; the gate does not close on the old
wording. The vendor baseline itself is restated rather than beaten
arithmetically: 31 of 55 by string scan and 28 by import walk are counts over
dynamic binaries, and *0 of 55* would not be the same measurement.

Out of scope, each with its reason: **`R7g` TLS** — the plan's own cut order
puts it first to go, and it has no bearing on the gate's claims. **WAN↔LAN NAT
forwarding measured end to end** — per-port VLAN was not met at `R6` (`R6-6`)
and this host has one NIC, so there is no second segment to route to; the rules
are installed and read back instead, which is what this bench can witness.
**A fuzz campaign of hours** — the pass condition is a coverage threshold
written before the run plus a planted defect the fuzzer must find, which is what
separates a connected harness from a silent one.

### The steps

| Step | | What it produces | DoD | Where it is most likely to be wrong |
|---|---:|---|---|---|
| **`R7-0`** ✅ **2026-09-30** | desk | This list, the board rows, and `tools/uspacescan.py`: the re-specified instrument, one source over the shipped bytes and one over the pre-link objects, each with a planted positive control | A fixture that really calls `system()` is caught by both sources; an `execve` fixture is permitted **and** counted; a name that exists nowhere reads 0; the two sources disagreeing is an error, not a vote; a mutated tool exits non-zero | Declaring a static binary clean because the instrument cannot see into it — the defect being repaired. A stripped file is the case that matters, and a method that needs symbols is not a method |
| **`R7-1`** ✅ **2026-09-30** | desk | rlxfw's own busybox, built from the drop's 1.13.4 source with the 4181 toolchain: `config/rlxfw-busybox.config`, `tools/mkbusybox.sh`, any patch under `config/busybox-patches/` | `busybox --list` 量 under qemu, not read off the config; no enabled applet's source calls `system`/`popen`/`execl*`, shown by scanning the built binary; `hazlint` 0; the list of commands the current image has and this build drops | Enabling `udhcpd` and shipping its lease-notify `system()` with it; a config that looks right while the binary says otherwise. Every dropped verb is a bench card that stops working |
| **`R7-2`** ✅ **2026-09-30** | desk | `init`, a compiled PID 1, and `ifupd`, the compiled replacement for `udhcpc`'s shell `-s` script | Mounts, LAN up by `ioctl`, daemons supervised with a backoff and a crash-loop stop; every child `fork`+`execve` with a fixed `argv`; the DHCP lease environment treated as hostile, with a malformed battery; the bench shell enabled **and announced** | Supervision that respawns for ever; a PID 1 that leaves zombies; taking the lease environment on trust, which is a WAN-side input |
| **`R7-3`** ✅ **2026-09-30** | desk | The config store: bounded TLV reader, CRC-32, A/B slots with a monotonic sequence, and the `cfgstore` CLI | The torn-write sweep as a loop over **every** truncation length, each leaving the previous record selected; a bit-flip sweep over the header; both slots invalid → defaults with `source = 0`; the mutation with the length check removed goes red | A reader that trusts a length — the vendor's defect exactly (`CVE-2024-21778`'s shape). A fail-open fallback: no password must mean no login, not no check |
| **`R7-4`** ✅ **2026-09-30** | desk | `brokerd`: `AF_UNIX`, typed ops, sessions, the rate limit, and `PING` as the typed replacement of a string-to-shell diagnostic | The decoder sweep over every header offset and truncation; the authorisation matrix per (op × uid × session × CSRF); the lock's doubling **and** a correct password succeeding after it expires; `NOENTROPY` before the pool is ready | A slow client holding the broker shut; an authorisation rule scattered through the ops instead of in one table. `PING`'s child must be reaped even when this image's `ping` ignores `-c` |
| **`R7-5`** ✅ **2026-09-30** | desk | `httpd` (privilege-dropped, chrooted, no ELF in the root), the JSON and HTTP parsers, and the KDF — SHA-256, HMAC, PBKDF2, scrypt from their RFCs | Every RFC vector set passes on the host **and** on the target under qemu; the traversal battery; the route matrix; `chrootcheck` shown failing on a planted `sh`; the scrypt parameters chosen from an anti-DoS budget, with the numbers | A KDF that is right little-endian and wrong big-endian — the target is big-endian and the host is not. scrypt's memory on a 26 MB machine is a DoS path, so the parameters are a security decision, not a benchmark |
| **`R7-6`** ✅ **2026-09-30** | desk | `dnsfwd`: UDP, forward only, refuses to be an open forwarder, with the compression-pointer guard and the query/reply match | The pointer battery (self, forward, cycle, chain, past-end) with a positive control that a legitimate compressed name decodes; the anti-spoof set; off-LAN sources refused; the mutation without the loop guard caught by a time-bounded test | The compression-pointer loop, which is the classic bug in this exact program. Random query ids are only as good as the pool, and on this board the pool is the open question `R7-7` settles |
| **`R7-7`** ✅ **2026-09-30** | desk | The kernel's entropy source, in rlxfw's own code, and the card that decides it | The mechanism read out of this kernel's `random.c` with citations; a credit policy that under-credits rather than over-credits; a card whose refutation condition is written first, with the reading on an image **without** the change as its control | Crediting a periodic timer, which would be a dishonest number. `entropy_avail` rising proves accounting, never that the bits are strong — and the honest fail-closed consequence is that login is refused until it rises |
| **`R7-8`** ✅ **2026-09-30** | bench | The image: the manifest rewritten to rlxfw's busybox and rlxfw's `/init`, built, and one boot per program's first run on the device (`D14`) | `uspacescan` over every binary in the image, both sources, 0 forbidden imports and the allowed ones counted; the shell prompt; `cfgstore`, `brokerd`, `httpd` and `dnsfwd` each shown running and answering; the KDF's device timing measured rather than inferred from qemu | The decompressed kernel + initramfs must stay under 5,242,880 bytes, and six new static binaries is where that budget goes. A daemon that works under qemu and faults on the silicon is what `D14` exists to catch |
| **`R7-9`** ✅ **2026-09-30** | desk | The write-up: `docs/GATE-RESULTS.md`'s entry, the notes, the `SPEC.md` rows, and what the gate did not establish | The DoD read one row at a time, each with the reading that settles it and the ones it does not | Calling the gate finished on a green test suite instead of on the device boot. The claim is about the shipped bytes, and only `R7-8` looks at those |
