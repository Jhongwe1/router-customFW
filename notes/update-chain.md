# The signed update chain — the host side

`R8a`, segment 118. This note owns the host half of the update chain: the `RLXU`
container format, the order its checks run in and why, how the keys are handled,
`flashguard`'s forbidden ranges, the proof that the stock loader does not
recognise a container, and the flash-layout arithmetic `R8b` will be designed
from. The target half is `notes/rlxboot.md`.

**Nothing here writes flash.** No tool in this note emits, prints as a command
or executes `FLW`, `EW`, `EB` or a non-zero `AUTOBURN`, and
`tools/test-mkfw2.sh` `X1`–`X4` are the sweep that says so, with `X2b` as the
control that the sweep can fire at all.

## 1. The container

All integers big-endian. Header 96 bytes, then a 64-byte signature over those 96
bytes, then the payload. `tools/mkfw2.py` is the only producer.

| off | size | field | rule |
|---|---|---|---|
| 0 | 4 | magic | `0x524C5855` = `RLXU` |
| 4 | 2 | format | 1 |
| 6 | 2 | header_len | 96 |
| 8 | 4 | version | the anti-rollback ordinal, 1..`0xFFFFFFFE` |
| 12 | 4 | payload_len | 1..`0x00300000` (3 MiB) |
| 16 | 4 | load_addr | where the payload is copied |
| 20 | 4 | entry_addr | inside `[load_addr, load_addr+payload_len)` |
| 24 | 4 | flags | 0 in `R8a`; bit 0 reserved for "payload is LZMA"; any unknown bit set rejects |
| 28 | 32 | payload SHA-256 | |
| 60 | 4 | recipe id | the four bytes whose hex `RLXFW-ID0` prints |
| 64 | 32 | reserved | all zero; any non-zero byte rejects |
| 96 | 64 | signature | Ed25519 over bytes 0..95 |
| 160 | payload_len | payload | |

A container is `160 + payload_len` bytes and no other length is accepted: a
trailing byte is rejected as `2/container_len`, which is what stops a container
from carrying a second image nobody verified.

## 2. The verification order, and why it is part of the format

1. magic, format, header_len
2. the field bounds — including that `load_addr` and `load_addr+payload_len` lie
   in RAM (`0x80000000`–`0x82000000`) and that the destination overlaps neither
   `rlxboot` itself (`0x81800000`–`0x818FFFFF`) nor the container's own staging
   buffer at `0x81000000`
3. the Ed25519 signature over the 96 header bytes
4. only then the payload's SHA-256, over `payload_len` bytes
5. the version against the anti-rollback counter

**Nothing is copied anywhere before step 4 passes.** The order is not a
preference, it bounds what a hostile container can make the verifier do before
anything in it is trusted:

- A verifier that hashed the payload first would read `payload_len` bytes at an
  address the attacker chose out of a header nobody had authenticated. Step 2
  bounds the length and the destination, and step 3 authenticates them, before
  step 4 reads one payload byte. `mkfw2 --self-test` `C12` is the case: a
  container with an absurd `payload_len` **and** a broken signature must be
  refused at `2/payload_len`, not at the signature and not at the digest.
- A verifier that reported "digest ok, signature bad" would have told an
  attacker that a digest matched. `C11` is that case: a container with both
  broken must report `3/signature`, because reporting the digest is evidence the
  payload was hashed under an unauthenticated header.
- `checks()` therefore stops at the first failure and the reported step name is
  itself part of what the tests assert. `C6` drives all 14 field bounds and
  **re-signs each mutation**, so the refusal comes from the bound and not from
  the signature that would otherwise have caught it first.

## 3. Keys

The signature is Ed25519, RFC 8032. `tools/rlxsign.py` is a pure-Python
implementation from the RFC — `hashlib` and nothing else — because the point of
this gate's key handling is a cross-check between two implementations, and a
wrapper around a library agrees with itself.

**The development key is in the tree on purpose.** The seed is 32 bytes of
`0x42`, it is written in `tools/fixtures/mkfw2/dev-key.tsv` and in
`rlxsign.DEV_SEED`, and it is **not a secret**: anyone who reads it can sign a
container this project's verifier accepts. It exists so that the host signer and
the target verifier, written independently, can be compared without exchanging a
key — if the two derived public keys differ, one implementation is wrong.

    seed    4242…42 (32 bytes)
    public  2152f8d19b791d24453242e15f2eab6cb7cffa7b6a5ed30097960e069881db12

**A production key must not be in this repository, ever.** `R8b` signs images
that a device will accept as authentic; a key committed here would make every
such signature worthless the moment the tree is published, and this tree is
meant to be published. What `R8b` needs is a key held outside the repository,
with the public half — and only the public half — built into `rlxboot`. Nothing
in `R8a` establishes that this key handling is production-grade, and nothing in
it is meant to.

`rlxsign --self-test` runs 16 controls: RFC 8032 § 7.1's vectors `V1`–`V4`, the
three single-bit negative controls § 3 of the spec names (`N1`–`N3`, sweeping
128, 26 and 32 flips), the two canonicality rejections RFC 8032 § 5.1.7 requires
(`N4` `S >= L`, `N5` a non-canonical `y`), a round trip at 24 message lengths
across the SHA-512 block boundaries, and `O1`–`O4`, which are the second source.

**§ 7.1's fifth vector, TEST 1024, is not in the table, and that is deliberate.**
Its message is 1,023 bytes of arbitrary data and this session has no offline copy
of them. A message transcribed from memory would either fail against the RFC's
signature — a false red — or be "repaired" by re-signing it, which deletes the
control and leaves a vector that can only ever agree with `rlxsign.py`. In its
place, `O1`–`O4` use **OpenSSL 3.0.13's** Ed25519, which is an independent
implementation and not a Python module: `O1` has OpenSSL derive the same public
key from the same seed, `O3` has `rlxsign` verify OpenSSL's signature over 1,023
and 4,096 bytes, and `O4` is `O2`'s control — OpenSSL must *reject* a signature
over a different message, or `O2` proves nothing. If `openssl` lacks Ed25519 the
four cases skip and the skip line says what is then unchecked: `V1`–`V4` alone
are a comparison against constants.

## 4. `flashguard` — the ranges, and the reason each is forbidden

`tools/flashguard.py` is a library first and a CLI second: `mkfw2.py` imports
`permitted()`, and anything else that computes a flash destination should too.
Restating the ranges in a second file is how one of them drifts.

| range | id | why it is forbidden |
|---|---|---|
| `0x000000`–`0x005FFF` | loader | The boot loader. `burn()` at `0x80401318` has **no lower bound** at all (`docs/loader-flash-write.md` § 1) and `boot` is one of the eight section signatures it accepts, so the vendor's own upgrade path will write offset 0 if a section header asks it to. A partial write here is an unrecoverable brick and there is no spare unit. |
| `0x006000`–`0x007FFF` | `H601` | This unit's MAC and radio calibration, which no reset restores. **Delegated**, not restated: `flashguard` asks `flashwin.overlaps_forbidden`, and `F3` is the case that goes red if that delegation is ever replaced by a copy. |
| `0x020000`–`0x02FFFF` | rescue | The read-only rescue slot (plan § D6). The stock loader scans `0x020000`, so this is the one image that still boots when `0x010000` is broken; the update path never writes it. |
| `0x400000`– | off-chip | Not a region but the same class of hazard: `burn()`'s only bound is the chip capacity and it **truncates** at it rather than refusing, so a destination running past the end is a silently short write. |

**A guard is shown permitting as well as refusing.** `flashguard table` prints
the forbidden ranges *and* seven probed neighbours, and `test-mkfw2.sh` `B2`
drives eight permitted ranges through the CLI: `0x008000` (the sector above
`H601`), `0x010000`, `0x01F000` and `0x030000` (the sectors either side of the
rescue slot), `0x060000` (the vendor kernel's, which is permitted and is what
`R9`'s vendor column needs), `0x3F0000` (the anti-rollback bitmap) and the last
sector of the chip. A refusal that refuses everything is not a guard, and `B1`
alone would not tell the two apart.

`M1` in `test-mkfw2.sh` is the mutation control for the range test: replacing the
overlap comparison with one that looks only at the start address turns `F8` and
`F13` red — `F13` being the case that a full image based at `0x010000` runs
through the rescue slot, which is § 6's arithmetic arriving as a test failure.

### What `flashguard` cannot see

It guards a **destination range**, which is an argument someone computed. It does
not read the loader's `burnAddr`, it cannot see a `J` into code that writes
flash, and it cannot see a TFTP upload made while the burn word is armed —
`cardcheck.py`'s `FW-113` note lists the same blind spots for the console side. A
permit from `flashguard` is not permission to write anything. It also says
nothing about whether a write is a good idea: `0x060000` is permitted and holds
the vendor kernel, and § 6 is that argument.

## 5. The stock loader does not recognise a container

Plan § D6's requirement, and it is a requirement rather than a nicety. The stock
loader scans `0x010000`, `0x020000`, `0x030000`, `0x040000`, `0x050000`,
`0x060000` and boots the **lowest** that passes `check_image()`. That path does
not go through `rlxboot`, so it goes through neither the signature check nor the
anti-rollback counter. If a slot image carried a header the loader recognised,
corrupting one byte of `0x010000` would make the loader boot an old slot
directly: a downgrade with no signal, at almost no cost to an attacker, and the
anti-rollback bitmap is monotonic but cannot stop a path that never reads it.

`check_image()` at `0x80407D50` takes `cs6c` (returns 1) and `cr6c` (returns 2),
and only 2 satisfies its caller; it then requires the 16-bit big-endian sum of
the RAM copy to be zero. `burn()` matches eight section signatures: `boot`,
`sqsh`, `w6cp`, `jw6c`, `cwmp`, `ksap`, `ALL1`, `ALL2`. `RLXU` is none of the
ten.

Two independent readings, over the 1,114,272-byte container built for this note:

    mkfw2 verify … --stock-loader
      check_image() signature at 0x00: b'RLXU' -- not 'cs6c' and not 'cr6c'
      burn() section signature at 0x00: b'RLXU' -- none of boot sqsh w6cp
        jw6c cwmp ksap ALL1 ALL2
      -> the loader reads no header it recognises here, so it neither boots
         nor burns this file
      stock loader verdict: NOT AN IMAGE

    rtkimage.py check --linuxbin <the container>     (exit 1)
      linux.bin
        signature                b'RLXU'
        flash offset             0x00000001
        sum16                    0x9C4C   (C-4 requires 0)
        body == nfjrom           False

`tools/rtkimage.py` is not this code, and it fails the container on **two
independent conditions**: the signature is not `cr6c`, and the 16-bit sum is not
zero. Its control in the same run reads the vendor-shaped `linux.bin` correctly
(`sum16 0x0000`, `body == nfjrom True`), so the parser is known to work on
something it should accept. `C15` is the same control inside `mkfw2`: the
function that says "not an image" about a container must say "recognised" about a
hand-built `cr6c` header and about a `boot` section, or it is a function that
says "not an image" about everything.

⚠️ **`upstream/tools/loader-unpack.py` does not reproduce `check_image()`.** Both
`SPEC-R8a.md` § 2 and § 5 and plan § D6 say it does; `grep -c check_image` over
it returns **0**. What it reproduces is the LZMA unpack of the loader's second
stage, its command table, its chip table and its IRQ wiring. The reproduction of
`check_image()` that does exist is `tools/rtkimage.py`'s `sum16` plus its
`cr6c` header parser, and that is what is used above and imported by
`mkfw2.stock_loader_verdict` rather than written again.

## 6. The flash layout, and what a provisioning write destroys

Desk calculation. **Nothing here is a proposal to write flash**, and every write
it describes needs the owner's own dated yes, one per write.

量 today's 4,194,304 bytes: loader `0x000000`–`0x005FFF` (24,576), `H601`
`0x006000`–`0x007FFF` (8,192), vendor config `0x008000`–`0x00FFFF` (32,768), the
vendor web image `w6cg` `0x010000`–`0x053A23` (277,028), the vendor kernel
`cr6c` `0x060000`–`0x151011` (987,154), a SquashFS `0x180000`–`0x34A040`
(1,876,033) and an erased tail `0x34C000`–`0x3FFFFF` (737,280).

Today's rlxfw image is 1,114,112 bytes; wrapped in a container it is 1,114,272,
which rounds up to `0x120000` = 1,179,648 on the loader's own 64 KiB step.

**Two full slots fit, with 1.25 MiB spare.** The binding constraint is not size,
it is the scan table:

| range | size | what | scan candidates inside |
|---|---|---|---|
| `0x000000`–`0x00FFFF` | 65,536 | loader + `H601` + vendor config — untouched | — |
| `0x010000`–`0x01FFFF` | 65,536 | `rlxboot`, updatable | `0x010000` |
| `0x020000`–`0x02FFFF` | 65,536 | `rlxboot-rescue`, read-only | `0x020000` |
| `0x030000`–`0x06FFFF` | 262,144 | **erased barrier** | `0x030000` `0x040000` `0x050000` `0x060000` |
| `0x070000`–`0x18FFFF` | 1,179,648 | slot A | — |
| `0x190000`–`0x2AFFFF` | 1,179,648 | slot B | — |
| `0x2B0000`–`0x3EFFFF` | 1,310,720 | free | — |
| `0x3F0000`–`0x3FFFFF` | 65,536 | state: the anti-rollback bitmap at `0x3F0000`, A/B selector | — |

Used 2,883,584 of 4,194,304; free 1,310,720. Splitting the free space evenly,
each slot could grow to 1,835,008 bytes — a payload of 1,834,848, 64.7 % over
today's image — so the layout is not close to its limit.

**`rlxboot` and `rlxboot-rescue` are the only two regions the stock loader can
reach, and they must each carry a `cr6c` header on purpose**, because being
loaded and jumped to by the stock loader is how they run at all. Slots A and B
are reachable only by `rlxboot`, and that is the whole design: the signature
check and the anti-rollback counter are on the only path that leads to them.

**The erased barrier is the part that is easy to get wrong.** The obvious layout
puts slot A at `0x030000`, and then slot A contains **four** of the loader's six
scan candidates. Payload bytes are not chosen by this project in a remote-update
threat model, and the loader needs only four bytes reading `cr6c` at a 64 KiB
boundary plus a zero 16-bit sum to boot a slot directly, without `rlxboot`. So no
slot may contain a scan candidate, the lowest usable slot base is `0x070000`, and
`0x030000`–`0x06FFFF` is left **erased** — an erased NOR word reads `0xFFFFFFFF`,
which is neither `cs6c` nor `cr6c`, so an erased barrier is provably unbootable
rather than merely unlikely to boot. ⚠️ That is a reading of `check_image()`'s
acceptance rule, not a measurement: the experiment that settles it is
`check_image()`'s `bank_offset` argument, which plan § D5 records as never having
been read for this build. If it is not 0 the whole candidate table shifts and
this barrier moves with it.

### What a provisioning write destroys

| write | destroys |
|---|---|
| `rlxboot` `0x010000`–`0x01FFFF` | 65,536 bytes of `w6cg` (of its 277,028) — the vendor web image's header, so `w6cg` is finished |
| rescue `0x020000`–`0x02FFFF` | another 65,536 bytes of `w6cg` |
| slot A `0x070000`–`0x18FFFF` | **921,618 of the vendor kernel `cr6c`'s 987,154 bytes**, and 65,536 of the SquashFS |
| slot B `0x190000`–`0x2AFFFF` | **1,179,648 more of the SquashFS's 1,876,033** |
| state `0x3F0000`–`0x3FFFFF` | 65,536 bytes of the erased tail — nothing |

Being specific, because this is the decision: **slot A's first write ends the
vendor firmware.** `cr6c`'s payload is truncated at `0x070000`, its 16-bit sum
stops being zero, `check_image()` stops returning 2, and the loader has nothing
left to boot from flash. The SquashFS then loses 1,245,184 of its 1,876,033 bytes
across the two slots, leaving 630,849 bytes of a rootfs that no kernel reaches.

That is exactly what gate `R9`'s vendor column needs. `R9` is a three-column
differential proof whose method is *vendor firmware = boots normally, rlxfw = RAM
boot, and switching between them is one power cycle*; every vendor-column
measurement in it depends on the vendor firmware still booting from this chip.
After slot A's first write it does not, and TOTOLINK never released source, so
there is no second copy to build.

⚠️ The honest qualification: the bytes are not unrecoverable in principle. A full
dump taken 2026-08-16 exists under `$FWRE_WORK/dumps/`, outside this repository.
But restoring 3.3 MiB of it means exactly the flash writes this project has spent
nine gates avoiding, through a `burn()` with no lower bound, on one device with no
spare — and a restore that fails partway leaves neither firmware. So *"gone"* is
the right word to plan with, and the ordering `SPEC-R8a.md` § 0 already states —
`R8b` is gated behind `R9` closing — is the consequence, not a preference.

### If two slots did not fit

They do. The single-slot alternative is recorded because it is what a larger
image would force: `0x070000`–`0x3EFFFF` as one slot of 3,670,016 bytes, the same
`rlxboot` / rescue / barrier / state around it. Its payload ceiling is then the
**format's** 3 MiB cap rather than the chip's, with 524,128 bytes spare. What it
costs is the thing `R8b` exists to demonstrate: with one slot there is nothing to
fall back to when a write is interrupted, so the ten power cuts would be a test
of `rlxboot-rescue` plus a TFTP upload rather than of A/B at all. The two-slot
layout is the one `R8b`'s pass criterion ④ needs.

## 7. What this does not establish

Stated as `SPEC-R8a.md` § 6 requires:

- **That an image can be written to flash.** Nothing in `R8a` writes one byte.
  `flashguard` refuses destinations; it does not write to the ones it permits.
- **That a power cut during a write is survivable.** That is `R8b`, and the
  interrupted write *is* the experiment.
- **That the counter advances.** Nothing in `R8a` writes it. The unary bitmap at
  `0x3F0000` is erased today, so it reads 0 and every version passes; `C13`
  drives the boundary (version 5 against counter 4, 5 and 6) against a
  command-supplied counter, not against flash.
- **That the key management is production-grade.** The development key is in the
  tree on purpose; § 3 says what `R8b` needs instead.
- **That `rlxboot` resists an attacker who can already write flash.** Plan § D6
  is explicit that it cannot. It defends the remote update path, not physical
  access — and § 6's erased barrier is a defence against *corruption* reaching a
  bootable header, not against someone who can choose what those bytes are.
- **That this hardware has secure boot.** There is no evidence of OTP or eFuse
  for a public-key hash on this part, and nothing here may imply there is.

Two more, specific to the host side:

- **The cross-check has not been run yet.** The public key above was derived here
  and confirmed against OpenSSL; whether the target's C implementation in
  `src/lib/ed25519.c` derives the same one is a comparison the main session
  makes. A mismatch is a finding in whichever is wrong, and this note is not
  evidence that the two agree.
- **The layout is arithmetic, not a measurement.** It is computed from `SPEC.md`'s
  `FLM-*` rows and the scan table in `docs/loader-command-semantics.md` § a. The
  one input that has never been read is `check_image()`'s `bank_offset`, and the
  barrier depends on it.

## 8. 🆕 2026-10-04 (120th segment): the flash as the device itself reports it, before the first write

The region census in § 6 is derived -- from the loader's structure and from the
2026-08-16 dump. This section is the **second source**: the same part, read out
of the running kernel's own drivers on a board that had issued no flash command
at all. `CLAUDE.md`: no register value enters code on one source.

量 2026-10-04 04:11:32, board running `f184a` (RAM boot, up 8 h 59 m),
`bench/2026-10-04/PRE-MTD`, `PRE-SPI`, `PRE-SMAP`:

| | |
|---|---|
| `mtd0` | `00130000`, `"boot+cfg+linux"` -- `0x000000`-`0x12FFFF`, 1,245,184 B |
| `mtd1` | `002d0000`, `"root fs"` -- `0x130000`-`0x3FFFFF`, 2,949,120 B |
| `mtd2` | `00400000`, `"rtl819x-spi-pio"` -- the whole 4 MiB |
| `erasesize` | `00001000` on all three |
| `/proc/partitions` | `mtdblock0` 1216, `mtdblock1` 2880, `mtdblock2` 4096 blocks of 1 KiB -- each matches its partition's size independently |

The write-path counters were **all zero**: `n_writes 0`, `n_write_refused 0`,
`n_xfer 0`, `n_reg_writes 0`, `n_pio_bytes 0`, `n_mmio_bytes 0`, `n_mtd_read 0`,
`n_rdy_timeout 0`, `n_state_foreign 0`, `n_state_bad 0`, `wedged 0`, with
`added 1`, `kat_rc 0`, `mtd_index 2`, `sfcr FFC00000` and `sfcr_as_kernel 1`.
`complement_expected 4186112` is 4,194,304 - 8,192, the part with `H601` taken
out. `map_ran 0`: no digest had been taken on this boot.

**The driver had never spoken to the chip.** `rdid_ran 0`, `rdid_rc -11`,
`rdid_id 000000` against `rdid_expect 1C7016`. `/proc/cmdline` is only
`console=ttyS0,38400` -- no `root=` -- so the rootfs is in RAM, which is what
makes `n_mtd_read 0` consistent rather than suspicious.

### 8.1 🔴 The erase block is NOT a measurement about the chip

`erasesize 00001000` is the same software constant as the partition map: it is
what the driver was configured with, not what the part reported. `rdid_ran 0`
with `rdid_match 0` is a **fail-open zero** -- the chip was never identified --
and `FLS-06`-`FLS-08` remain 未定.

This is a bricking precondition for `R8b`, not a detail. Every one of
`FW-167`'s six addresses is `0x10000`-aligned and every planned size is a
multiple of 65,536, so at 4,096 B **no planned region shares an erase block
with a forbidden one**, and the margin from `H601` to `0x010000` is eight
blocks. **At 64 KiB the margin is one block, and that single block holds the
loader, `H601`, COMPDS and COMPCS together.** The experiment that settles it:
complete `rdid` and match it against the EN25QH32B table **before any erase**.

### 8.2 What this section does not establish

It does not establish that the vendor's own kernel used this partition table --
`mtd0`/`mtd1` here are rlxfw's declaration (`FW-28`), and the vendor kernel's
own table is unmeasured (`FW-11`). It says nothing about the chip's erase
geometry (§ 8.1). It does not establish that no flash byte has ever been
written: these counters see only this boot through this driver, and `FW-142`
says what `n_writes` is blind to. And `erasesize` agreeing with the partition
map is not corroboration, because they are the same constant.
