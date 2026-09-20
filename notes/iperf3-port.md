# `iperf3` on the RTL8196E — the build, and what it is and is not evidence of

**`R6-5`'s throughput instrument.** Opened 2026-09-20, eighty-ninth segment, at
the desk, board unpowered.

**This file owns the BUILD and nothing else**: which source, how it was
configured without `./configure`, what was measured present and absent in this
libc, the ISA check on the result, and the four things that were not verified.
The *number* it eventually produces is `R6-5`'s, and belongs to `SPEC.md`.

🔴 **Nothing here has run on the silicon.** Everything below is 量 at the desk
or under `qemu-mips-static`, and the two are not the same claim.

---

## § 0. Why a binary at all, and why not `nc`

量 2026-09-20: this image cannot generate a byte stream. It has no `nc`, no
`dd`, no `/dev/zero`, and no `mknod` with which to make one. The largest
readable source is `/dev/mtd2ro` at **1,040 KiB/s** (`FW-48`), which is *below*
the 100 Mbit link — so a userspace sender reading from flash would measure the
SPI controller and publish it as a network number.

`iperf3` synthesises its buffer in memory, so it sidesteps that entirely. It is
also what `R6-5`'s row in the step list names by name.

⚠️ It is **one** of two instruments and not a replacement for the other.
`CONFIG_NET_PKTGEN=y` measures the **TX path**; `iperf3` measures **TCP
goodput**. A pktgen figure may not be quoted as a throughput number and an
`iperf3` figure may not be quoted as a driver-path rate.

## § 1. The source, and it is not single-sourced

**`iperf 3.1.3`** — 讀 `configure.ac:27`, `AC_INIT(iperf, 3.1.3, ...)`.

Three routes fetched separately, and **all sixteen compiled `.c` files are
byte-identical across all three** 量:

| route | sha256 of archive | bytes |
|---|---|---|
| GitHub tag archive (built from) | `e34cf60cffc80aa1322d2c3a9b81e662c2576d2b03e53ddf1079615634e6f553` | 549,466 |
| `archive.debian.org` orig tarball | `60d8db69b1d74a64d78566c2317c373a85fef691b8d277737ee5d29f448595bf` | 546,899 |
| `git clone --branch 3.1.3` | commit `274eaed5b17f664e4ac6c79f1ba854b55f15a3a3` | — |

`downloads.es.net` was unreachable from this host 量, which is why the primary
fetch is GitHub. The Debian tarball is a genuinely independent origin and it
agrees, so the source is not single-sourced.

🔴 **3.1.3 specifically, and the reason is measured rather than stylistic.**
量 `grep clock_gettime src/*.c` over 3.1.3 returns **nothing** — it is entirely
`gettimeofday`-based, so the `-lrt` / `CLOCK_MONOTONIC` question that a newer
3.x would raise against uClibc 0.9.30 **does not arise at all**. That dependency
arrives later in the 3.x line.

## § 2. No `./configure`, and that is the whole plan

Autotools on a 2005-era gcc with a cross triple is where this port would have
died. It was bypassed: `config/rlxfw-user/iperf3/iperf_config.h` replaces the
file `./configure` would have generated, and **every `#define` in it, and every
deliberate omission, is a probe result** — `probe.sh` compiles a probe per
header / macro / struct member and greps `libc.a`'s symbol table per function.
Nothing is inherited from a host `configure` run and nothing is assumed.

**Measured ABSENT and therefore left undefined**: `netinet/sctp.h`,
`SO_MAX_PACING_RATE` (a 3.13-era sockopt), `cpuset_setaffinity`.

🟢 **The file is live rather than decorative**, and the control is the binary's
own output: `--version` prints *"CPU affinity setting, TCP congestion algorithm
setting, sendfile / zerocopy"* — exactly the three that were enabled and nothing
else.

**Three of the four fights predicted before the attempt do not exist.** 量: gcc
3.4.6 accepted `-std=gnu99`, mixed declarations, designated initialisers and
compound literals with no complaint; `getopt_long`, `getaddrinfo`,
`poll`/`select` and `sigaction` are all present in `libc.a`; and there was no
`clock_gettime` question (§ 1). **Zero source edits were needed.**

## § 3. The build

```
TC=$FWRE_WORK/rebuild/r2ab/tc/rsdk-1.3.6-4181-EB-2.6.30-0.9.30

$TC/bin/mips-linux-gcc -D_GNU_SOURCE -I<src> -std=gnu99 -O2 -Wall \
    -fno-if-conversion -c <each of the sixteen .c> -o <obj>
$TC/bin/mips-linux-gcc -static -o iperf3.elf <sixteen objs> -lm
$TC/bin/mips-linux-strip iperf3
```

`config/rlxfw-user/iperf3/Makefile` and `build.sh` are the committed form.

**No `-march` is passed, and it never needed to be.** 量 `readelf -h` on a
default-flags object: `MIPS R3000, big endian, o32, mips1`. The toolchain's
default *is* the target, so this project's `-march=mips32` ban never came near
being an issue.

**Result**, 量 and re-derived at the desk after the agent that built it
reported: **252,644 bytes**, sha256
`3144db60bd3895f582f84e61da306f96f6e668f07cf9a84fef0ebc6b971a97e8`,
`ELF32 · 2's complement, big endian · EXEC · MIPS R3000 · o32, mips1`.
**246.7 KiB = 15.2 %** of the image's 1.58 MB headroom, and the initramfs is
uncompressed so that cost is 1:1.

## § 4. 🔴 `-fno-if-conversion` cannot reach a prebuilt `libc.a`

**A negative result, and it generalises past this binary.**

量, two builds as a control: flagged and flagless both carry the **same 114**
conditional moves — **65 `movz` + 49 `movn`** — and every one was attributed with
an independent decoder plus `nm` to **uClibc/libm** (`_vfprintf_internal` ×14,
`getaddrinfo` ×3, `__ieee754_sqrt` ×2, across 62 symbols). **`iperf`'s own
sixteen objects emit zero.**

The reason is not subtle once stated: `-fno-if-conversion` is a *compile-time*
option, and Realtek compiled `libc.a` years ago. **`config/rlxfw-cflags`'s
safety net (`TC-25`) applies to anything this project compiles and to nothing it
links.** That is now recorded in that file too.

The flagged build is shipped anyway — a policy with an exception per artefact is
not a policy — **but it may not be claimed to have bought anything here.**

What the 114 rest on is prior art, not this flag: 讀 `docs/isa-prior-art.md`,
the vendor kernel carries **3,183** conditional moves and `CPU-54` measured the
shape executing correctly on this die. The dangerous case is one *in a load
delay slot*, and 量 `hazlint` reports **0 load-use violations in 12,639 loads**,
rc 0.

⚠️ **Three decoders disagree about what to CALL them and agree about where they
are**: `hazlint` names them MIPS-IV, the independent decoder counts 114, and
`objdump` **refuses to name them**, printing raw `0x43300a`, because the ELF is
flagged `mips1`.

## § 5. What ran, and it was not the device

量 under `qemu-mips-static`, a MIPS-BE server and a MIPS-BE client of this same
binary against each other:

* TCP, 2 s, both ends — completed.
* UDP, `-u -b 2M` — **60 datagrams, 0 lost**. This is the path that exercises
  the byte-order helpers.
* `-J` — output parsed clean by Python's `json` module, so cJSON works and the
  `--no-json` fallback is not needed.

**The `#warning platform not supported` from `portable_endian.h` is benign and
that was checked three ways rather than assumed**: it fires because uClibc
defines no `__GLIBC__`, and the fallback arm taken is the *correct* one. 量
`be64toh(x)` preprocesses to `(x)`; `-dD` shows `__BYTE_ORDER __BIG_ENDIAN`; and
a qemu run lays down wire bytes `01 02 03 04 05 06 07 08`. Also 量 **0
implicit-declaration warnings**, which is the check that would have caught a
missing 64-bit helper silently truncating to `int`.

## § 6. 🔴 `TCP_INFO` is the one thing qemu cannot verify, and it has a signature

量: under qemu, `getsockopt(TCP_INFO)` returns **`optlen = 4`** and writes four
bytes; a native build of the same source on the same host returns the full
**104** with sane values. That is why the qemu run's `Retr` column printed
**`4,290,268,504`** — **a qemu artefact with a native control proving it**, not a
port defect.

The best available evidence for the device is two-source agreement on the
layout: uClibc's `netinet/tcp.h` and the vendor kernel's own
`linux-2.6.30/include/linux/tcp.h` are **identical** — `sizeof` 104,
`snd_mss`@16, `rtt`@68, `snd_cwnd`@80, `total_retrans`@100 量/讀 — and the
toolchain's kernel headers are `LINUX_VERSION_CODE 132638` = 2.6.30 量, an exact
match with the running kernel.

**推, and it is the strongest form available without the die**: `Retr` and
`Cwnd` are right on the device. ⚠️ **A nonsense `Retr` column is the signature to
watch for on the bench**, and if it appears the reading is the instrument's and
not the driver's.

## § 7. What is NOT verified

1. **Nothing has run on the silicon.** No throughput figure exists.
2. **No interop test against a modern `iperf3`.** Both ends were this binary;
   3.1 ↔ 3.16 compatibility is 推.
3. **No CPU-cost figure.** qemu's 46 Gbit/s is meaningless. Whether this Lexra
   part can saturate 100 Mbit while `iperf3` does its reporting arithmetic in
   `double` on a soft-float core is **unknown**, and it is a real question: the
   driver copies **byte-at-a-time PIO** in both directions (the buffers sit at
   2 mod 4 and a word load would fault), so the number may be low and the reason
   may not be `iperf3`.
4. **`-Z`, `-C` and `--affinity` are advertised by `--version` and untested.**

## § 7a. 🔴 The interop test in § 7.2 was run on the wrong medium

量 2026-09-20, twice, and the second measurement refutes the first.

**At the desk, over loopback**: this binary as client against an apt-installed
`iperf 3.16` server — four cases, **all rc 0** (TCP, `-R`, `-J`, UDP `-b 10M`
with 0/444 lost). That was reported as retiring § 7.2's 推.

**On the die, over the real 1500-byte Ethernet path**: the same binary against
the same 3.16 server got `iperf3: error - control socket has closed
unexpectedly`, and the server printed
**`WARNING: Size of data read does not correspond to offered length`** with
**no `Accepted connection` from the board at all**.

推, and it is the obvious reading: loopback's MTU is 65536 and delivers
iperf3's length-prefixed control JSON in one read; a 1500-byte path splits it.
**Loopback cannot test a protocol whose failure mode is a short read.**

🟢 **The fix is constructive rather than diagnostic**: run **3.1.3 on both
ends**. 量: `qemu-mips-static ./iperf3 -s -B 10.1.1.2 -p 5201` binds the real
interface (`ss` shows `10.1.1.2:5201 LISTEN users:(("qemu-mips-stati"))`) and a
same-version client completes against it. The emulation cost sits on the server
side, which counts bytes rather than generating them.

⚠️ **The lesson generalises past iperf3**: a desk test of a network protocol run
over loopback has silently removed segmentation, reordering, loss and the MTU.
§ 7's remaining 推 rows should be read with that in mind.

## § 8. ~~It is not in an image yet~~ 🔄 **It is, since 2026-09-20**

🟢 **量 2026-09-20 (ninetieth segment).** `config/rlxfw-initramfs.tsv` gained one
`file` row (38 → **39** entries), so `RECIPE_ID` moved `f2aa2fdd` → **`edc94765`** and
the image was rebuilt as cell `r6if1`. The binary is **not** under `config/` — it is at
`$REPO/build/rlxfw-user/iperf3/iperf3`, produced by an `install` target added to this
directory's Makefile, with objects staged under `$FWRE_WORK` so no `.o` can move the id.
🟢 **The rebuild through that rule reproduced the audited artefact byte for byte**
(sha256 `3144db60…`), which is a control on the recipe rather than a formality: a
different digest would have meant the committed recipe does not build the committed
measurement. Decompressed image **3,943,424** of 5,242,880 = **75.2 %**, margin
1,299,456 — and that figure was predicted from a `gen_init_cpio` delta before the build
and matched exactly. `nfjrom` **1,152,000** bytes, sha256 `89051d6a396c305b`.

⚠️ **`RECIPE_ID` cannot see the binary.** The id is a digest over `config/` and the
product lives under `build/`, so two different builds of `iperf3` give two images with
the **same** `RLXFW-ID0`. What pins the artefact is the assembled image's own sha256.

⚠️ **This file's § 3 headroom figure and the tsv's own SIZE comment block are now
stale by one image**, and are deliberately NOT edited this segment: `config/` is inside
`RECIPE_ID`, two frozen cards state `edc94765`, and moving the id to fix a comment would
make those cards unreproducible. Carried forward.

🔴 **And nothing of it produced a throughput number.** See § 7a and
`SPEC.md` `NET-59`/`NET-60`.

### § 8.1 The original note, kept


The binary lives at `$FWRE_WORK/iperf3-port/iperf3` and is **not** committed —
binaries never are. Putting it in the image means a row in
`config/rlxfw-initramfs.tsv`, which is under `config/`, so it **moves
`RECIPE_ID`** and needs a rebuild. That is `R6-5`'s first desk act, and until it
happens no card may predict an `RLXFW-ID0` that includes it.


## § 9. 🔴 `-n` does not transfer N bytes, and `-t` cannot bound it

量 2026-09-20, on this project's own cross-built MIPS artefact under
`qemu-mips-static`, five points, all consistent.

讀 `iperf_api.c:1853`: the client sends **`multisend = 10`** blocks between
bound checks, and the `break` that fires when the byte budget is spent leaves
the **stream** loop, not the multisend loop. So

    bytes transferred = ceil(N / (10 x blksize)) x 10 x blksize

At the default `-l 128K`, `-n 64K` therefore moves **1,310,720 bytes in ten
128 KiB writes** rather than 65,536 — which is exactly `D14-IP1`'s
configuration, one of the two that ended seating 29.

🟢 **Any `-b` sets `multisend = 1` and makes `-n` exact.** 量:
`-n 64K -l 1K -b 100M` transferred exactly **65,536** bytes in **64** writes of
1,024; `-k 1 -l 1K -b 100M` transferred **1.00 KBytes**.

⚠️ **`-b` on TCP has a floor of `blksize x 8 / 0.1 s`**, because the send timer
is a fixed 100 ms: `-b 100K`, `-b 1M` and `-b 10M` at the default `-l` all gave
the same 11,528 kbit/s, while `-b 200K -l 1K` gave 199 and `-b 50K -l 1K` gave
**90.1** — the floor winning is its own negative control. UDP paces correctly.

🔴 **`-t` and `-n` are mutually exclusive** (`IEENDCONDITIONS`), so an `-n` run
has **no wall-clock cap at all**: a board that stops sending hangs the client
until it is killed. Any card using `-n` has to carry its own timeout.

`SPEC.md` `FW-98`.
