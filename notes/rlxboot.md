# rlxboot — a second-stage loader that verifies a signed container

`R8a`, segment 118, 2026-09-30. Desk work. **Nothing in this file was measured on
the device.** Every number here came from the host suite, from
`qemu-mips-static`, from `qemu-system-mips`, or from the emitted image — and the
last section says which of them the bench can still refute.

`SPEC-R8a.md` §§ 2 and 4 own the format and the memory map; this file owns the
reasons.

🔄 **2026-10-05 (124th segment): §§ 1–10 describe the `BOOT=ram` build, which was
the only build when they were written.** The default device build is now
`BOOT=slots` with `KEY=prod` (`R8b-1`, `94d97924`): it reads two flash slots
instead of a container staged in RAM, and the last section below says how. The
numbers in §§ 1, 2 and 8 — 16,240 bytes, 405 loads, the container at
`0x81000000`, the suite counts — are the older build's, and `t_container`'s 71 in
§ 8 was already stale at format 2. The sections after § 10 are dated and are
read in order.

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
address; this note records what pinning it costs. ⚠️ The word reads
`00020060` for format 2 and read `00010060` for format 1 — the 2026-09-30
captures and `FW-171`'s discriminator hold the older value, as a record of the
containers that seating used, and a card re-using that expectation has to
recompute it.

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
`truncated`, `sig`, `digest`, `rollback`, `flash_dst`, `flash_match`,
`flash_form`. Every one is a separate case in `t_container.c` and every case
asserts the reason by name, so a refusal for the wrong reason is a failure and
not a pass. The last three arrived with format 2 and their numbers are
**appended** to the enum, so no existing reason's value moved and a capture of
`RLXBOOT-HDR bad=…` reads the same before and after.

### The three format-2 bounds, and what each one is for

`flash_form` refuses a declared destination with no landing form, a form with
no destination, and a word that is not one of the three — before any
arithmetic is done with it, because the form is what fixes how many bytes
land, and a form nobody checked is a length nobody checked.

`flash_dst` refuses a declared **landing range** inside the loader region,
inside `H601`, or running off the end of the part. It depends on no
caller-supplied value, so no caller can turn it off, and it fires in the boot
path too — where nothing is written at all. It is deliberately **not** the
whole of `tools/flashguard.py`'s table: the rescue slot is licensable, so the
format permits a container that declares it and the host build is where the
owner's dated licence is demanded. `RLXU_FLASH_KEEPOUT_END` and
`RLXU_CHIP_SIZE` are the only flash numbers in `container.h`, and
`test-mkfw2.sh` `G1` reads both out of the header and requires them to equal
what `flashguard.check_unrecoverable` enforces — probed, not grepped for a
literal — with `G2` as the control that the comparison can fail.

`flash_match` compares the signed `flash_at` **and** `flash_form` with
`env.write_at` and `env.write_form`, where and as what the caller says it is
writing. A mismatch in either is refused, and so is a container that declares
nothing. The form half is the one that matters most and is the easiest to
leave out: 量 2026-10-04, a container over a `cr6c`-headed payload reads
`RLXU` at offset 0 and `cr6c` at offset 160, so whether the writer strips the
160-byte prefix decides whether what lands at `0x020000` can boot at all
(`FW-168`). `t_container.c`'s case *declared 0x020000 PAYL, caller writing
0x020000 WHOL* is where that is refused — the base agrees and only the form
differs — and `test-mkfw2.sh` `M7`, which compares the offset alone, is the
mutant that must turn it red.

`RLXU_FLASH_NONE` is `0xFFFFFFFF` and `RLXU_FORM_NONE` is `0`, so a zeroed
`struct rlxu_env` says *I am writing flash offset 0 in no form*, which every
container is refused against. A field somebody forgot fails safe.

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

🔄 2026-10-05: these are `R8a`'s counts (`BOOT=ram`, format 1 at the time); the
suites today are `t_crypto` 36, `t_container` 99 and `t_slots` 61, in the last
section.

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

## 🆕 2026-10-05 (123rd segment, desk, no power): `BUILD_ID` moved at format 2, and every committed copy of it is the old one

`src/rlxboot/Makefile` writes, above the recipe, that the id is **re-derivable**
and that the main session identifies a booted image by recomputing it rather
than by comparing a number someone typed. 量 2026-10-05 that this is exactly
what the tree had stopped doing.

量, with `make -pn`, which evaluates the immediate assignment and runs no rule,
so no compiler and no vendor binary is invoked:

| tree | `BUILD_ID` |
|---|---|
| `457b2314`, `f353b7b8` | **`6395889d`** — **the positive control** |
| `c7e27842` (format 1 → 2) | **`a9727473`** |
| `c8980fd6`, `66ec2abe` | **`a9727473`** |

The control is what makes the rest a reading: `6395889d` is the value `SPEC.md`
`FW-170`, `FW-172` and `FW-215`, three lines of `docs/GATE-RESULTS.md` and four
`bench/2026-09-30/R8A-*j.log` captures record, and the recipe reproduces it at
the commits those readings were taken from. 量 `a9727473` occurs in **0**
tracked lines.

🔴 **What this costs `R8b`, and it is not a bookkeeping point.** `FW-215` 量s
the rescue payload at 16,240 bytes with build id `6395889d` and reasons from
that id that *this build touched no source reaching the image*. Both halves
were true of the tree it was built from; 量 `c7e27842` landed in the same
segment and moved the id, so **the recorded rescue artefact cannot be
reproduced from the committed tree** — a rebuild from `66ec2abe` compiles a
different `-DRLXBOOT_BUILD`, so the payload bytes, its sha256, the `cr6c`
length and the 16-bit sum all move with it. This note's own `Makefile` comment
states the stake: *"a rescue that differed in C would carry a different id …
and would stop being the known-good copy a rescue slot exists to hold"*.
🔄 **2026-10-05 (124th segment): the sentence that followed here said the
difference was not in C, and that was wrong.** It read *"the difference here is
not in C — 讀 the id is a digest of the sources, and `c7e27842`'s change to them
was a container-format change the rescue payload does not use"*. 量, in the
next section (`FW-232`): the format-2 verifier is the payload's own
`rlxu_verify`, and the payload is 336 bytes larger. The difference **is** in C,
and the digest — which cannot tell a comment from code — was right to move.

**Refutation conditions, written before the readings.** *The id moved* is
refuted by HEAD giving `6395889d`; it did not. *The recipe is being read
correctly* is refuted by the control failing to reproduce a recorded value; it
reproduced two. *The move happened at format 2* is refuted by `457b2314` or
`f353b7b8` already giving `a9727473`; neither does.

**What this does not establish.** That any image was ever built or booted with
the wrong id: every committed reading of `6395889d` was taken from a tree that
produces it, so no record here is a misreading of its own artefact. It does not
establish which source file of `c7e27842` moved the digest — the id is one
digest over twenty-two files and this reading does not attribute it. It does
not establish what the rescue slot should hold: whether `R8b` writes the
`FW-215` artefact (reproducible only from `457b2314`-era sources) or a rebuild
at HEAD's id is a decision about what *known-good* means, and it is the
owner's. And nothing was built or compiled for this reading.

## 🆕 2026-10-05 (124th segment, desk, no power): format 2 changed `rlxboot`'s code, not only its id

The section above ends on a reading and an inference. The reading, that
`BUILD_ID` moved at `c7e27842`, stands. The inference, that the difference is not
in C, is refuted here, and that paragraph is corrected where it stands.

**Refutation conditions, in place before the first build** (`s124/e/prereg.md`,
R4; 推 when written, from reading `c7e27842`'s diff): *the format-2 change
reached the payload's code, not only its id* is refuted if `c7716fbe`'s
`rlxboot.bin` is still 16,240 bytes and differs from `FW-215`'s only in the
instruction words that carry the build id, or if none of the strings
`flash_dst`, `flash_match`, `flash_form` occurs in it. Neither fired.

量, tree `c7716fbe`, the recipe `FW-215` used (`make payload`, `make rescue`,
`make rescue-controls`), every `make` under `tools/vendor-tripwire.sh` from a
scratch directory, the toolchain being a sparse `--shared` clone of
`src-vendor/rtl819x-toolchain` at its pin `5c9be5d9`: `diff -rq
--no-dereference` against the canonical `rsdk-1.3.6-4181-EB-2.6.30-0.9.30`
directory was empty (rc 0), the same diff over a copy with one byte changed
returned 1, and the tripwire returned 0 on `true` and 2 on a file created inside
the clone.

| | `FW-215`'s tree (`2200d1d7`, which is `c7e27842^`) | `c7716fbe` |
|---|---:|---:|
| `rlxboot.bin` | 16,240 B | **16,576 B** |
| `.text` | 13,520 | 13,808 (+288) |
| `.rodata` | 2,720 | 2,768 (+48) |
| `.bss` | 2,000 | 2,000 |
| `rlxu_verify` | 1,296 B | **1,572 B** |
| `reason_names` | 72 B | 84 B |
| `rlxprobe_main` | 508 B | 520 B |
| strings `flash_dst`, `flash_match`, `flash_form` | 0 each | 1 each |
| bytes that differ over the common 16,240 | — | 13,572 |
| each `cr6c` image | 16,258 B | 16,594 B (`len` 16,578, 16-bit sum `0x0000`) |
| build id | `6395889d` | `a9727473` |

`reason_names` is 18 four-byte entries before and 21 after: the three reasons
that § 3 lists as arriving with format 2. The control: `c7e27842^` rebuilt in
this same environment gives `rlxboot.bin` and both `cr6c` images byte-identical
to `FW-215`'s (`cmp` rc 0 on all three), so the recorded artefact **is**
reproducible — from `2200d1d7`'s tree and from no later one. Two clones at
different paths built `c7716fbe`'s three artefacts and the ELF byte for byte
(23 of the 26 files each build leaves are identical; the three that differ are
`objdump` listings that print the ELF's path, first difference at byte 38). The
two `cr6c` images differ in one byte, at offset 9 (`0x01` against `0x02`, the
flash-offset field), use 25.3 % of their region and end 48,942 bytes short of
the next scan candidate.

**The second half, 讀 and not run.** `FW-215`'s artefact would refuse every
container this repository's tools now make. 讀 `container.c` at `2200d1d7`:
step 1 requires `format == RLXU_FORMAT`, which is 1 there, and refuses by the
name `format` otherwise. 讀 `tools/mkfw2.py` at `c7716fbe` and at `a6add876`:
`FORMAT = 2`, and `build` refuses to leave `flash_at` or `flash_form` out. Two
sources, and neither is a run — no format-2 container was fed to a format-1
verifier here.

**What this does not establish.** Which source file or line produced the 336
bytes: that is attribution, and this reading makes none. That any of it ran on
the die. What the rescue slot should hold, which the previous section left to
the owner and this one leaves there. And it measures `c7716fbe`'s tree: after
`R8b-1` (next section) the default recipe builds a different program, so none of
these sizes is the current tree's.

## 🆕 2026-10-05 (124th segment, desk, no power): `rlxboot` boots from flash slot A or B (`R8b-1`)

`94d97924`. 讀 from `src/rlxboot/{main.c, slots.c, slots.h, flashread.c,
rlxboot.h, Makefile, prodkey.h, mkprodkey.py}` at that commit unless marked; 量
is about the host, qemu and the compiler. **None of it has run on the die**, and
nobody has seen the stock loader start this payload with the flash window
decoding over the slots.

### Why it exists

§§ 1–10 verify one container, staged in RAM at `0x81000000` by the loader's
TFTP, and the only flash address the payload formed was the counter's. 讀
`src/rlxboot/*.c` and `*.h` at `94d97924^`: **0** lines name a slot's flash
address or a slot macro; at `a6add876` **43** do, which is the control. So the 123rd
segment's *"no tool question is left undecided"* was wrong on this side, as it
was on the kernel's (`SPEC.md` `FW-230`): there was no flash boot at all, and
`R8b` is a write that has to be booted from.

### Two selectors, both fixed when the image is built

**`BOOT=slots`** is the default and the artefact; **`BOOT=ram`** is `R8a`'s path,
kept buildable and not linking `slots.c`. There is no build that tries one and
then the other: `MEM-17`, DRAM survives a power cycle, so a run-time *RAM first*
would let a stale container from any earlier seating win over both slots
without anyone typing a thing. **`KEY=prod`** is the default: the public half of
the owner's production key, compiled in from the generated `prodkey.h`.
**`KEY=dev`** is the development key, whose seed is published in `devkey.h`, so
an image built with it accepts a container anyone signed; it has to be typed.
`RLXBOOT-KEY prod <hex>` or `dev <hex>` is the second console line, so a capture
says which key an image trusts without anyone recomputing an id.

The Makefile's `keycheck` runs before anything is compiled and refuses, naming
the command that fixes it, while `prodkey.h` holds no key — the committed header
is the placeholder — or the development key, text that is not 64 hex digits, 32
bytes that are not a curve point, or a point of small order; `main.c` stops at
`#error` if the Makefile is bypassed. `mkprodkey.py write --pubkey <64 hex>`
writes the header, and its `check` also refuses a header whose three copies of
the key disagree. The seed never enters this repository or `$FWRE_WORK`; the
public half is meant to be committed, so anyone can rebuild the flash image.
Built with `KEY=prod` on the committed tree, `make payload` exits 2 with
*`prodkey.h holds NO production key (it is the placeholder)`* (an agent run,
`s124/f`, tripwire CLEAN).

BUILD_ID is the first eight hex digits of the digest over every source that
reaches the image plus the key header, so each choice has its own. 量 by `make
-pn`, the method of the 123rd segment's section (it evaluates the immediate
assignment and runs no rule), at `94d97924` — `a6add876` gives the same four:

| recipe | `BUILD_ID` | |
|---|---|---|
| default (`BOOT=slots KEY=prod`, placeholder key) | `ef430386` | names a build that refuses, so no artefact carries it |
| `BOOT=slots KEY=dev` | `239582cc` | 18,576 B, `tools/hazlint` 0 violations in 508 loads |
| `BOOT=ram KEY=dev` | `94771052` | 16,704 B, 0 violations in 413 loads |
| `BOOT=ram KEY=prod` | `4b16a0c2` | |

The two sizes are from the agents' builds under the tripwire (`s124/f`), and the
ids reproduce there. Neither `BOOT=ram KEY=dev`'s id nor any other is `FW-215`'s
`6395889d`: `FW-215`'s artefact stays reproducible only from `2200d1d7`'s tree
(`FW-232`). The production-key ids arrive in `R8b-3`.

### D4's rule, as the code does it

1. **Copy.** Slot A (`0x070000`) goes to RAM at `0x81000000` and slot B
   (`0x190000`) to `0x81200000`, 1,179,648 bytes of room each, through the
   uncached window at `0xBD000000` one aligned word at a time. Each slot has its
   own buffer, so verifying B cannot overwrite A's verified copy. The copy is
   sized by the 160-byte header already in RAM: those 160 bytes come first, and
   the rest follows only if they begin `RLXU` and their `payload_len` fits the
   slot, so an erased or torn slot costs a 160-byte read and not 1.1 MB.
2. **Verify each copy where it sits** with the unchanged `rlxu_verify`, with
   `write_at` set to that slot's own base and `write_form` to `WHOL`. This is a
   decision the spec did not make (`slots.c`'s header): a container signed for
   slot B and found in slot A, one that declares no destination, and one declared
   `PAYL` are all refused as `flash_match`, because the signed `flash_at` has to
   name the place the container was read from, in the form that puts a header
   there.
3. **Choose.** The valid slot with the higher `version` boots, and a tie boots A.
   An unverified slot never wins whatever its header claims, because that
   version is an unauthenticated field until `rlxu_verify` returns.
4. **Boot from the winner's own buffer.** Nothing is read from flash after a
   slot's verdict, so there is no second copy whose bytes could differ from the
   ones that were checked.
5. **Neither verifies:** print both reasons, then halt — no reset. A reset would
   come back through the stock loader's scan to this same `rlxboot` and the same
   two slots, forever, and 讀 `docs/loader-command-semantics.md`: the loader's
   only two `WDTCNR` writes are its own deliberate reboots, so nothing arms the
   watchdog under a spin this payload did not arm itself.

The console, from `t_slots show` run here (host, exit 0; the device adds the
per-stage lines between a `READ` and its `VERDICT`, and `refuse-action halt`
after a `HALT`):

```
RLXBOOT-READ A flash=00070000 buf=81000000 n=100160 .
RLXBOOT-VERDICT A ok ver=1
RLXBOOT-READ B flash=00190000 buf=81200000 n=1114272 .................
RLXBOOT-VERDICT B ok ver=2
RLXBOOT-SLOT B
```

```
RLXBOOT-READ A flash=00070000 buf=81000000 n=160
RLXBOOT-VERDICT A bad=magic
RLXBOOT-READ B flash=00190000 buf=81200000 n=300160 ....
RLXBOOT-VERDICT B bad=digest
RLXBOOT-HALT A=magic B=digest
```

`n=` is the byte count this read will cover, printed before the copy so a hang in
the first read of the part ends the console on that line; one dot is printed per
64 KiB copied, so a copy that has stopped shows as dots that stopped.

### D21 — the counter is the flash bitmap, and only that

The slots build reads the anti-rollback counter from the bitmap at flash
`0x3F0000` and nowhere else; the RAM-staged `RCNT` path is not compiled. A stale
or planted block in DRAM (`MEM-17`) would otherwise set the floor lower than
flash's, letting a rollback through, or higher, refusing both slots. The
Makefile's payload gate reads the disassembly and refuses a slots image that
forms `0x81700000` at all, with the RAM image as the control that the census can
see it: 量, in the `s124/f` build logs, **0** census rows naming it in the slots
image and **2** in the RAM image. `RLXBOOT-CTRSRC flash` is therefore a
constant in the slots build. ⚠️ The flash source itself stays 推: § 10 says why
an undecoded window and an erased region both give counter 0.

### The test runners could not fail

`run-host-tests.sh` ran each suite as `"$o/t_container" | tail -3` and
`run-qemu-tests.sh` as `qemu-mips-static ./t_container | tail -8`. Under `set -e`
a pipeline's status is its last command's — `tail`'s, 0 — so a suite that printed
its own `N failures` line did not stop the run, and the script went on to print
*"both suites exited 0"* and *"host suite: PASS"*. 讀 both scripts at
`94d97924^`. 量 2026-10-05, re-measured here with one planted failing check (a
`checks++; failures++;` before `t_container`'s summary line), each runner on its
own `git archive`:

| runner | plant | exit | `host suite: PASS` | `t_container` |
|---|---|---:|---:|---|
| `94d97924^` | none | 0 | 1 | 97 checks, 0 failures |
| `94d97924^` | yes | **0** | **1** | 98 checks, **1 failure**, in all three builds |
| `94d97924` | yes | **1** | 0 | stopped at `cc1`: 100 checks, 1 failure |
| `94d97924` | none | 0 | 1 | 99 / 0, with `t_crypto` 36 / 0 and `t_slots` 61 / 0, in each of the three builds |

So the guard permits as well as refuses. ⚠️ My first unplanted run of the new
runner used an archive of `src/` alone and failed on `mkprodkey.py --self-test`,
which imports `tools/rlxsign.py`: a defect of my scratch tree, but also the new
runner refusing a failure at a later step, which the old one could not do. The
fix writes each suite's output to a file, reads its status with no pipe on the
command, and stops naming the suite; `mkprodkey.py --self-test` is read the same
way. The qemu runner's old shape is 讀, not re-measured, and the commit message
reports `t_slots` 61 / 0 under big-endian qemu, which was not re-run here.
`SPEC.md` `FW-234`.

### What the suites and mutations cover

`t_slots` (61 checks) drives `slots.c` and `container.c` against a 4 MiB array
standing in for the part and two host arrays standing in for the buffers; every
container is built and signed there, every case asserts both verdicts by name and
the console lines exactly, and `rlxb_choose` is checked on eight rows of the D4
table. `mutate.sh` has eight mutations, each confirmed to apply and each caught
after the unmutated suite is shown to pass (`s124/f`'s run ends *all eight
mutations were applied and all eight were caught*; not re-run here): M1 and M2
are § 9's; M3 makes a tie
boot B; M4 verifies the flash and boots the buffer, the *second copy* D4 rules
out; M5 lets a claimed higher version count as valid; M6 verifies a slot without
naming its own base; M7 compiles the RAM counter into the slots build, and M8
compiles it out of the RAM build.

### What this does not establish

Anything on the die: that the stock loader's scan starts this payload at all
with the window decoding over the slots at that moment, and that a slot read
returns what the 2026-08-16 dump holds. What the two reads cost: copying a full
slot is 294,912 words, and at the 2.075 µs `FLS-11` measured for one uncached
load through that window it would be about 0.6 s a slot (推 — that figure is
`probe3`'s loop, not this one), before Ed25519 and SHA-256 over up to 1 MiB on a
core nothing has timed (§ 10). That the owner's key exists: the prod build
refuses until it does, and no container signed with it exists (`R8b-3`). That
`main.c`'s halt and jump behave, which only the qemu payload run reaches and
qemu certifies logic, not the ISA.

## 🆕 2026-10-07 (125th segment, bench): `rlxboot` from flash — the slot choice, the rescue copy and ten power cuts (`R8b-5`, `R8b-6`)

**What ran.** 量 `bench/2026-10-07`, one seating. `rlxboot` build `127a71cf` with the owner's
production key — `RLXBOOT-KEY prod 4a6eda72…3096e` on every boot — installed at `0x010000` and its
rescue copy at `0x020000`, first as `cr6c` and, after `T2a`, as `cs6c` (`SPEC.md` `FW-241`;
`notes/update-chain.md` § 6): the same payload, the signature's second byte changed. Containers
P, Q and R (versions 1, 2, 3), each 1,109,152 bytes, wrapping mainline recipe `f9adc9e8`. Every
judgement below is `tools/bootslot.py judge`'s, with `RLXFW-ID0` checked against the build
manifest's `recipe_id`.

**The slot choice, as D4 says and the silicon did** (`SPEC.md` `FW-242`):

| capture | slot A | slot B | `rlxboot` printed | `bootslot` |
|---|---|---|---|---|
| `T1a` | vendor data | vendor data | `VERDICT A bad=magic`, `VERDICT B bad=magic`, `RLXBOOT-HALT A=magic B=magic`, `refuse-action halt` | PASS |
| `T2ra` | P, version 1 | vendor data | `VERDICT A ok ver=1`, `VERDICT B bad=magic`, `RLXBOOT-SLOT A` | PASS |
| `T3a` | P, version 1 | Q, version 2 | `VERDICT A ok ver=1`, `VERDICT B ok ver=2`, `RLXBOOT-SLOT B` | PASS |
| `F05` | R, version 3 | Q, version 2 | `VERDICT A ok ver=3`, `VERDICT B ok ver=2`, `RLXBOOT-SLOT A` | PASS |

Each `ok` stands on `HDR ok`, `SIG ok`, `DIGEST ok` and `VER cur=N ctr=0 ok` in the same capture,
and every boot ends `RLXBOOT-BOOT load=80500000 entry=80500000` then `RLXFW-ID0=F9ADC9E8`. The
counter read `ctr=0` in all 17 slot boots of the seating: nothing writes the state block (`D3`).

**The verify time** (`FW-250`), 量 from the captures' `.timing` by `FW-35`'s rule, with the USB
serial latency (1–16 ms) as the floor: `RLXBOOT-V1` to `RLXBOOT-BOOT` is 2.623–2.624 s on the six
boots that verified both slots (`T3a`, `RD05`, `RD09`, `BCc`, `ACc`, `F05`) and 1.382–1.384 s on the
three that verified one and refused the other at `bad=magic` (`T2ra`, `B1B`, `A1B`); `T1a`'s two
`bad=magic` refusals took 0.096 s. So one slot — 1,109,152 bytes read through the flash window,
SHA-256, Ed25519 — costs about 1.3 s, console output included. From `busybox reboot -f` to the
mainline prompt is about 15.6 s (`F05`). This is `R8b-1`'s hazard column, *the delay of two
verifies through the flash window*, read.

**The rescue copy** (`FW-242`). `RD03` installed `rlxboot` with `pace=30000`; the console printed
`RLXFW-SI E 00 370 paced=30000` — the 64 KiB region erased — and nothing more before the pull.
`RD05`, power on with no ESC: `RLXBOOT-FROM 05020000`, both slots `ok`, `RLXBOOT-SLOT B`, PASS with
`--expect-from 05020000`. `RD07a` read `0x010000` as `FFFFFFFF` ×4 and `RD07b` read the rescue
header at `0x020000` (`63733663 81800000 00020000 000048C2`); `RD08b` re-installed `rlxboot`
(`cmp=1`) and `RD09` read `RLXBOOT-FROM 05010000` again. The rescue copy's boot is told apart from
`rlxboot`'s only by that `RLXBOOT-FROM` line (`5be604d5`).

**Ten power cuts** (`FW-243`). Each pull cut a write of the slot that wins if the write completes —
slot B ← Q while A held P, then slot A ← R while B held Q — so a torn write boots the other slot and
a completed one boots the written slot. Before each pull the target slot was rewritten unpaced with
the same container and read back (`…Rb`, `cmp=1`; B1 used `W5b`'s), so a cut before the first erase
would read as a control. Writes were paced at `pace=2000`.

| round | last line before the cut | boot |
|---|---|---|
| B1 | `RLXFW-SI E 03 7750 paced=2000` | `VERDICT A ok ver=1`, `VERDICT B bad=magic`, `SLOT A` |
| B2 | `E 11 27120` | 〃 |
| B3 | `P 06 56790` | 〃 |
| B4 | `P 06 56920` | 〃 |
| B5 | `P 09 63480` | 〃 |
| A1 | `E 02 5360` | `VERDICT A bad=magic`, `VERDICT B ok ver=2`, `SLOT B` |
| A2 | `E 10 24560` | 〃 |
| A3 | `E 16 39140` | 〃 |
| A4 | `P 03 50250` | 〃 |
| A5 | `P 14 74220` | 〃 |

10 of 10 PASS (`B1J`–`B5J`, `A1J`–`A5J`); no control round, no refusal, no halt. The closing
controls show the other half: `BCc`, after slot B was rewritten unpaced, booted B over A; `ACc`,
after slot A ← R unpaced, booted A over B.

**What this does not establish.** That `v1.0`'s image boots from flash: every boot here is
`f9adc9e8`, and the `cs6c` commit (`f257a848`) moved the recipe to `6a11de02`. That a cut
anywhere survives:
ten points in paced writes, of which 推 about 83 % (erase phase) and 92 % (program phase) of the
time is the pace's sleep (an erase step is about 2,415 ms, of which about 415 ms is flash work; a
program step about 2,170 ms, of which about 170 ms; `notes/spi-mtd-driver.md` § 14.3); none in block
0's erase, the last six seconds before the header, the header page, the read-back or an unpaced
write. That `rlxboot` refuses a torn slot at its signature or digest on the die — every torn slot
failed at `bad=magic`. That rollback is refused from flash — `ctr=0` throughout. That the rescue
copy takes over from a `rlxboot` that is signed and wrong — the drill erased it.
