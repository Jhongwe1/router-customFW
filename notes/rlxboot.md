# rlxboot — a second-stage loader that verifies a signed container

`R8a`, segment 118, 2026-09-30. Desk work. **Nothing in this file was measured on
the device.** Every number here came from the host suite, from
`qemu-mips-static`, from `qemu-system-mips`, or from the emitted image — and the
last section says which of them the bench can still refute.

`SPEC-R8a.md` §§ 2 and 4 own the format and the memory map; this file owns the
reasons.

## 1. What it is

`rlxboot` is a bare-metal payload for the RTL8196E, linked at `0x81800000`,
entered by the stock loader's `J 81800000`. It reads a container staged in RAM at
`0x81000000`, verifies it, and either jumps to the payload the container carries
or refuses and names the check that refused.

It is 16,240 bytes, has no libc, no `malloc`, no recursion and no exception
handler, and `tools/hazlint` finds 0 violations in its 405 loads.

## 2. The memory map

| what | address | why there |
|---|---|---|
| RAM | `0x80000000`–`0x81FFFFFF` | 32 MiB, `SPEC-R8a` § 4 |
| stage 2's code and data | `0x80400000`–`0x8041FFFF` | a **refused** destination, § 4 |
| a normal payload | `0x80500000` | where the loader's own `LOADADDR` defaults |
| the container | `0x81000000` | `SPEC-R8a` § 4, staged by the loader's TFTP |
| the RAM counter | `0x81700000` | `"RCNT"` then a 512-byte bitmap |
| `rlxboot` | `0x81800000` | `SPEC-R8a` § 4; a **refused** destination |
| the flash counter | `0xBD3F0000` | flash offset `0x3F0000` through the MMIO window |

⚠️ **`0x81000000` is the one address in RAM this project has measured being
rewritten.** `MEM-14`: word 1 of `0x81000000` is rewritten to `0x00000144` on
every boot, three times reproduced — which is why `tools/rlxprobe/Makefile` puts
probe1's result block at `0x80A00000` instead. Word 1 of a container is `format`
and `header_len`, so a boot between the upload and the `J` corrupts the container
into `RLXBOOT-HDR bad=format`. That is visible rather than silent, but it is a
constraint on the card: **upload the container after the prompt is reached, and do
not let the board reset between the upload and the jump.** The spec pins the
address; this note records what pinning it costs.

`rlxboot`'s own range is taken from the linker symbols `_rlxboot_start` and
`_stack_top`, not from a constant, so a payload that grows cannot end up
permitting a destination on top of its own `.bss`.

## 3. The verification order, and why it is that order

1. magic, format, header_len
2. every field bound, and every overlap
3. Ed25519 over header bytes 0..95 — **the header becomes trusted here**
4. SHA-256 over `payload_len` payload bytes — **the payload becomes trusted here**
5. `version` against the anti-rollback counter

**Nothing is copied at any point in `rlxu_verify`, and no payload byte is read
before step 4.** `struct rlxu` carries `hashed` and `copied` so that is a
testable claim: on every refusal at or before step 3 both are 0, and
`t_container.c` asserts it on all 9,472 bit-flip cases rather than on a chosen
example.

**This is deliberately not what the stock loader does.** `check_image()` at
`0x80407D50` calls `flash_read(header.startAddr, offset + 16, header.len)` — it
copies the payload to an address taken out of the untrusted header — and *only
then* sums the RAM copy as 16-bit halfwords and requires zero
(`docs/loader-flash-write.md` § 3). No bound on `startAddr` appears anywhere in
that path. So a header its checksum will reject has already been allowed to
scatter `header.len` bytes across an address of its own choosing. rlxboot does
not repeat that, and `container.c`'s header says so where a reader will meet it.

Step 2 runs before step 3 although step 3 is what makes the header trustworthy.
The reason is that step 2 reads nothing but the 96 bytes already in hand and
writes nothing — it is arithmetic over a buffer step 0 has already bounded — so
by the time the signature verifies every number in the header is known to be in
range, and a malformed container is refused **with a field name** even when it is
unsigned garbage. The ordering that would matter, doing anything with the payload
or with an address out of the header before step 3, is the one that does not
happen.

Step 5 is last because `version` is an untrusted 32-bit field until step 3, and
the rollback decision is the only one an attacker gains from flipping.

### The bounds, by name

`short`, `magic`, `format`, `header_len`, `version`, `payload_len`, `flags`,
`reserved`, `load_addr`, `entry_addr`, `dst_self`, `dst_buf`, `dst_loader`,
`truncated`, `sig`, `digest`, `rollback`. Every one is a separate case in
`t_container.c` and every case asserts the reason by name, so a refusal for the
wrong reason is a failure and not a pass.

Four are additions to `SPEC-R8a` § 2 and are listed as such: `payload_len == 0`
refused by name; `load_addr` and `entry_addr` required to be word aligned (an
unaligned jump target is an `AdEL` on this core, which lands in the loader's
`do_reserved` and costs a power cycle instead of printing a refusal); and
`dst_loader`, the stage-2 window, refused because § 4's own sentence says the
loader's code and data must not be overwritten before the jump and rlxboot copies
before it jumps by construction.

A `load_addr` in KSEG1 is refused as a side effect of the RAM bound: `ram_base`
and `ram_end` are KSEG0, so an uncached destination — which would have bypassed
the cache flush below — cannot be asked for.

## 4. The counter, and the boundary rule

A 512-byte unary bitmap, 4,096 bits, read **read-only** from flash offset
`0x3F0000` through the MMIO window at `0xBD000000`, or from a card-staged copy at
`0x81700000` when the word there is `"RCNT"` (`0x52434E54`). `RLXBOOT-CTRSRC
flash|ram` says which was used.

The counter is the number of zero bits from the start, MSB first within each
byte, bytes in address order. An erased NOR byte is `0xFF`, so a factory-erased
region reads 0 and `R8b` advances the counter by clearing one bit per version,
which needs no erase. One bit cleared leaves `0x7F` in byte 0; eight leave
`0x00,0xFF`; nine leave `0x00,0x7F`. All-`0xFF` reads 0 and all-zero reads 4,096.

A zero bit *after* the first one bit is malformed. The value used is then the
**total** zero count, which is never below the leading run: of the two ways to be
wrong, a counter too high refuses updates and a counter too low accepts a
rollback, so the malformed case resolves upward. A plain (non-`RLXBOOT-`) line
says so on the console.

**`version == counter` is ACCEPTED; `version < counter` is refused.** The counter
is the ordinal of the newest version ever installed, so after installing version
N it reads N. Refusing equality would mean the device could not re-install the
image it is running — the ordinary recovery operation — and would require the
counter to advance on a boot rather than on an install. Accepting equality grants
an attacker nothing: version N is already authorised and they already hold a
signed container for it. What the counter must stop is N−1 after N, and `<` stops
exactly that.

## 5. The crypto, and where it came from

**Ed25519 verification and SHA-512 are IMPORTED. They are not rlxfw's code and
nothing in this repository may describe them as rlxfw's.**

* upstream: TweetNaCl 20140427, `https://tweetnacl.cr.yp.to/20140427/tweetnacl.c`
* sha256: `02e65bc3013ff2168983365e55906bc783c4c7e0a60d8100f17bb303a17175c4`
* authors: Bernstein, van Gastel, Janssen, Lange, Schwabe, Smetsers
* licence: public domain

**The decision, and it went the other way from "write everything".** The
repository's claim is that its code is its own and provable. A verifier is the
one place where those two halves come apart: *provable* is the stronger
requirement, and "I wrote this field arithmetic and it passes the RFC 8032
vectors" is a weaker statement than it sounds. Five vectors cannot refute a carry
bug that shows up on one input in 2^30 — the failure mode of arithmetic mod
2^255−19 is not enumerable, so the test set that would establish a hand-written
implementation does not exist at desk scale. An import moves the correctness
claim onto fifteen years of deployment and review that this project cannot
reproduce in one segment, and costs exactly one thing: it must be labelled.

What is rlxfw's, and what `R8a` is actually about, is everything around it: the
container format, the verification order, the bounds, the freestanding linkage,
the cache handling, the big-endian target build and the whole test harness.

**Provenance is an instrument, not an assertion.** `src/rlxboot/test/mk-import.sh`
regenerates `src/lib/ed25519.c` and `src/lib/sha512.c` from the upstream file by
naming the retained line ranges and copying them with `sed -n`, so nothing in
them can differ from upstream by a byte; `check-import.sh` regenerates and diffs.
The retained ranges are printed in `mk-import.sh` and marked in both files with
`BEGIN IMPORTED` / `END IMPORTED`.

Changes to the imported text: **none.** What was done is deletion and one
structural split, each listed in the files:

* deleted (never edited): salsa20, hsalsa20, poly1305, secretbox, box,
  curve25519, `ld32`, `st32`, `L32`, `_0`, `_9`, `_121665`, `crypto_verify_16`,
  `randombytes`, both keypair generators, and `crypto_sign_open`;
* SHA-512 lives in its own file, so `crypto_hash` is declared in `sha512.h` and
  defined in `sha512.c` — the one structural adaptation;
* the typedefs and the two macros upstream takes from `tweetnacl.h`, which this
  tree has no libc to supply, are reproduced outside the markers.

rlxfw's own code in `ed25519.c`, below the last marker and labelled: the
`rlx_ed25519_verify` wrapper, the seed-to-public-key helper and the signer (both
`#ifdef`-ed out of the payload), and `rlx_s_below_L`.

`crypto_sign_open` was replaced rather than called for two reasons. It copies the
whole signed message into a caller buffer and returns the message, which a loader
has no use for and which would put a variable-size buffer in the trust path; and
it does not test that `s < L`, so a signature with `s + L` substituted verifies
there. That is malleability, not forgery — it needs a valid signature to start
from — but a loader for which two byte strings authorise one container is a loader
whose bit-flip sweep proves less than it looks. The wrapper refuses it with its
own reason code, and the host suite drives that branch with a constructed `s + L`.

**One warning exemption in the whole build, on one imported file.**
`src/lib/ed25519.c` is compiled with `-Wno-sign-compare`: its `vn()` compares a
`u32` index against an `int` bound at one site, under gcc-13, clang-18 and gcc
3.4.6 alike. Editing imported crypto to silence a warning is not a trade this
gate makes. Every file rlxfw wrote is built with `-Wall -Wextra -Werror -Wundef
-Wshadow` and no exemption — including `src/lib/sha512.c`, which is also imported
and needs none.

SHA-256 is rlxfw's own (`src/rlxboot/sha256b.c`), and the reason is the mirror
image: a hash has no rare-input failure mode of that kind, the RFC 6234 vectors
exercise the whole round schedule, and the padding is enumerable. It is
cross-checked three ways — against RFC 6234, against coreutils over every message
length 0..200, and against `src/lib/sha256.c`, an independent implementation
written by another hand in the same segment.

Recursion: `crypto_sign_open`'s call graph is a chain, not a tree —
verify → `scalarmult` → `add` → `M` → `car25519`, five deep, no cycle. Measured
stack: see § 8.

## 6. The cache, and how I convinced myself

rlxboot writes instructions into DRAM with ordinary stores and then jumps to
them. Three facts from `notes/cache-model.md` decide what has to happen between:

1. there is no I/D coherence on this R3000-class core;
2. the D side is write-back — a store to a **resident** line leaves the line dirty
   and DRAM stale. It is write-back *without* write-allocate, so a store to a line
   that is not resident goes straight to memory, which is why getting this wrong
   sometimes appears to work and why *"it booted"* is not evidence that the flush
   is unnecessary;
3. CP0 register 20 is `CCTL`, edge-triggered 0→1. The two commands issued are the
   two whose name comes from a source and whose value appears in two files:
   `0x200` `DWB_Inval` and `0x002` `IInval`.

So: **write back D, then invalidate I, then jump.** The order is the argument —
invalidating I first would let the I side refill from a DRAM line the D side still
holds dirty, and that failure looks exactly like a bad signature, because the
digest verified over the bytes the D cache holds and the core executed the bytes
DRAM holds.

Both are issued **through the KSEG1 alias**, with `rlx_call2_uncached`.
Invalidating the I-cache while fetching out of it is the classic way to fetch
garbage, and this unit's own loader does not take that risk either — at
`0x804004a8` it ORs `0xA0000000` into its own next address and jumps.

The container and the RAM counter are read through **KSEG0**, cached, the same way
the loader's TFTP wrote them: a KSEG1 read of a line the loader left dirty would
see stale DRAM. The flash window is read through KSEG1 because it is MMIO and a
cached read of an MMIO window is not a reading of it.

What was deliberately not done: no flush at entry (rlxboot's own code arrived by
the route every probe payload arrives by, and if the I-cache held stale lines for
`0x81800000` the banner would never print, so a flush there could only affect
instructions after it and nothing between it and the copy is self-modified); and
no `Status.IsC` path — probe1 cell 4 measured that this core does not isolate and
that that method's byte stores reach DRAM (`CPU-35`), so `rlx_isc_inv` is not
linked at all (`RLX_ISC=0`).

⚠️ **What is still 推.** That `CCTL 0x002` suffices is 量 for probe1's victims — a
two-word patch inside the payload's own image — and `0x200`'s D-side writeback is
measured nowhere on this die. `R8a`'s boots took the first reading this section
offered (`FW-170`). 🔄 **The second — `DW` of the destination after the copy —
cannot move this to 量** (2026-10-03; recorded, not run). No hazard is armed: the
SHA-256 over the container streams 1.1 MB through the 8 KiB D-cache first (讀), so
the copy stores to lines the D side does not hold (推), probe1's FRESH case (量);
a prompt is reachable only through a reset or a Linux run, and both write back (讀:
the loader's `0x202`, the kernel's `0x200`); and rlxboot has no no-flush arm (讀).
What decides it is `CPU-19` ①'s experiment, not scheduled: a probe1-style store to
a cache-resident line read back through the I side, `0x002` alone against `0x200` +
`0x002`, untreated and store-miss controls. qemu cannot: its Malta writes `XContext`.

## 7. No write path, and how to confirm it from the binary

On this controller the memory-mapped window cannot program or erase: a command is
issued by **writing** `SFDR`, so a store into the window is not a transaction
(`docs/loader-flash-write.md`), and every program and erase in the vendor's own
code goes through the controller registers at `0xB8001200..`. So *"rlxboot has no
program or erase path"* reduces to *"rlxboot never forms an address in the
controller's register block"*, which is a property of the instruction stream.

`src/rlxboot/test/flashscan.py` reads the disassembly of the linked payload and
reconstructs every address the code builds — every `lui` alone, every `lui`
followed by an `ori`/`addiu`, and every load or store displacement against a
register holding a known constant — and refuses if any lands in
`[0xB8001200, 0xB8001300)`. It prints the whole census either way. `flashsafe.sh`
runs it over the payload, then over a planted `sw $0,0($8)` with `$8 = 0xB8001200`
which it must refuse, then over the same store moved to `0xB8002000` which it must
permit. **A guard is shown permitting as well as refusing.**

Its limit, stated: the reconstruction is per-register and forgets a register
written by anything it does not model, so a controller address computed in a way
it does not follow would not appear in the census. It is not a proof about all
possible programs; it is a check on this one, whose own flash access is nine
instructions in `flashread.c`.

Two compile-time refusals in `flashread.c` assert that the counter's flash window
is outside the loader region and outside `H601` (`0x006000`–`0x007FFF`) — with the
negative-array-size idiom, because gcc 3.4.6 has no `_Static_assert`.

## 8. Counts

| | |
|---|---|
| host suite, `t_crypto` | 36 checks, 0 failures |
| host suite, `t_container` | 71 checks, 0 failures |
| RFC 8032 § 7.1 | 5 vectors — TEST 1, 2, 3, 1024, SHA(abc) — each keygen + sign + verify |
| RFC 6234 | 6 messages × SHA-256 and SHA-512; 8 digests cross-checked against the RFC text |
| coreutils cross-check | every message length 0..200, SHA-256 and SHA-512 |
| Ed25519 negative sweeps | 512 signature bits + 512 message bits + 256 public-key bits, all rejected |
| **container bit-flip sweep** | **9,472 flips = 768 header + 512 signature + 8,192 payload; every one rejected** |
| refusal stages the sweep reached | header 64, bounds 376, signature 840, digest 8,192 |
| truncation sweep | 1,184 lengths 0..1,183 all refused; 1,184 accepted |
| counter bitmaps | 0, 1, 7, 8, 9, 4,095, all-`0xFF`, all-zero, malformed |
| target payload | 16,240 bytes, `.bss` 2,000, stack reserve 32,768 |
| verifier stack, **measured** | **4,392 bytes** big-endian MIPS under `qemu-mips-static`; 4,311 on the host |
| `tools/hazlint` | **0 violations in 405 loads, 0 unresolved**, every control held |

The stack figure is a stack-painting high-water mark, so it is a **lower bound**:
it sees bytes that were written, not frames that were merely reserved. 32,768
reserved against 4,392 measured is a 7.5× margin, and the margin is there because
the measurement is a lower bound, not because the number is uncertain. The
deepest call chain is verify → `scalarmult` → `add` → `M` → `car25519`; the two
1,088-byte buffers the verifier and the signer use are `.bss`, not stack.

The vectors are **extracted, not transcribed**: `test/mk-vectors.py` parses RFC
8032 § 7.1 for its own vector blocks and builds the RFC 6234 messages by
construction, taking their digests from `hashlib` and then requiring each to
appear verbatim in the RFC 6234 text — with a negative control that a digest one
nibble different is *not* found. Two of its own refusals fired during development
and are written up in the script: it matched the table of contents first and
refused with "parsed only 0 vectors" rather than emitting an empty suite, and it
found no digests until the search stopped assuming whitespace was the only thing
between a digest's halves.

The coreutils cross-check was wrong in a third way and it is worth recording,
because it is the shape of error this project has a rule about. It rebuilt the
message generator in `awk` instead of being handed the bytes — and `awk` computes
in doubles, so `s * 1103515245` exceeds 2^53 and the LCG silently diverged after
the first two bytes. The run reported **199 of 201 lengths disagreeing with
coreutils** while every digest was in fact correct: a false refutation, produced
by a cross-check that reimplemented its own input. `t_crypto digest N FILE` now
writes the bytes it hashed and coreutils hashes those.

## 9. Mutation controls

A green suite is a claim about its controls. `test/mutate.sh` confirms the
unmutated suite passes first — a mutation run against an already-red suite says
nothing — then applies two mutations and refuses if either fails to apply.

* **M1, the digest comparison tests only the first byte.** The bit-flip sweep goes
  red. 255 of every 256 payload flips would still be caught by byte 0, so it is
  the ~32 that leave byte 0 unchanged that turn it red — which is what makes the
  sweep a test of the comparison and not only of SHA-256.
* **M2, the payload is hashed before the signature is checked** — this unit's own
  `check_image()` defect. 7 failures. Six of them are the order assertions:
  `r.hashed == 1024` on a container refused at the signature stage, and the
  recorded stage sequence. **The seventh is a verdict** and it was not predicted:
  *a flipped digest bit (signature covers it)* changes its refusal reason from
  `sig` to `digest`, because with the steps swapped the digest comparison meets
  the corrupted field first. So one functional case does see M2 — but only
  because that case asserts the reason **by name**. A suite that only asked
  "was it rejected?" would have been blind to M2 entirely, and the honest answer
  would then have been *nothing catches it*.

## 10. What `R8a` does not establish

Per `SPEC-R8a.md` § 6, and each of these is a claim this work does **not** make:

* that an image can be written to flash — nothing here writes one byte, and
  `flashscan` is the check;
* that a power cut during a write is survivable;
* that the counter advances — nothing in `R8a` writes it, and the flash bitmap is
  read-only;
* that the key management is production-grade — the development key is in the tree
  on purpose, derived from a seed of 32 `0x42` bytes, and anyone reading
  `src/rlxboot/devkey.h` can sign a container for this build. `R8b` needs a real
  key that never enters this repository and never enters `$FWRE_WORK`, which is
  shared with another checkout; rotation is a rebuild, because this format has no
  key list and no revocation;
* that `rlxboot` resists an attacker who can already write flash — plan § D6 is
  explicit that it cannot. It defends the remote update path, not physical access;
* that this hardware has secure boot. There is **no** evidence of OTP or eFuse for
  a public-key hash on this part, and nothing here may imply there is: the stock
  loader still runs first, unverified, and can still be replaced by anyone with
  flash write access.

And four more this file adds:

* that the cache handling is correct **on the die** — § 6's 推 and its refutation
  condition;
* that the flash MMIO window is decoded at `0xBD3F0000` at the loader prompt.
  `FLS-11` is 量 at `0xBD000000` over 4,096 bytes; this address is 4,128,768 bytes
  further in and the window's decode size is measured nowhere. An undecoded window
  and an erased region are **not distinguishable by the counter** — both give
  `ctr=0` on the device — which is why test ③ is driven from the RAM source and not
  from flash;
* that `rlxboot` works on the device at all. It has printed its lines on
  `qemu-system-mips` and passed every vector on `qemu-mips-static`; **qemu
  certifies logic and never codegen or the ISA**, and a bench seating is what turns
  any of this into a reading;
* that the timing is bounded. Ed25519 over 96 bytes and SHA-256 over 3 MiB have
  been timed on nothing that resembles this core.
