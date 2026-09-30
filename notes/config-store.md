# The config store (R7, `src/lib/cfg.c` + `src/cfgstore/`)

Replaces the vendor's `COMPCS`/`COMPDS` pair. Owner of the record format, the
two-slot store semantics and the `cfgstore` CLI. The schema itself is pinned by
`SPEC-R7 § 4`; this file owns what the format does and what has been measured
about it.

**No number in this file is 量 on the silicon.** Every measurement here was taken
on the build host (gcc-13 / clang-18, x86-64) or read out of a cross-built ELF.
Where a number is about the device it is marked 推 and says what would settle it.

## 1. The three vendor defects this replaces

| vendor | here |
|---|---|
| plaintext credentials (CVE-2019-19823) | no plaintext key exists in the schema; `admin.pwhash` is 56 bytes of KDF output and is the only `WEB_HIDDEN` key |
| one write changing both regions (`D-10`) | two slots; `cfg_store` writes only the slot that does **not** hold the record currently selected |
| a TLV length passed straight to `memcpy` (CVE-2024-21778's shape) | one bounded reader, `tlv_next`, is the only way any caller obtains a `(type, len, value)` triple, and `len` is checked against the remaining bytes first |
| both regions bad → defaults **and telnet** (`D-13`, fail-open) | both slots invalid → defaults with `source == 0`; `admin.pwhash` has **no default**, so a caller that authenticates against it cannot authenticate at all |

The fourth row is a property of the schema (a key with no default row) rather
than of a code path, which is why `schema_self_check` asserts it on every run of
every program.

## 2. Record format

All integers big-endian. Nothing is ever `memcpy`'d onto a struct; every field
goes through `tlv_put_be16/32` and `tlv_get_be16/32`.

| off | size | field | refused when |
|---|---|---|---|
| 0 | 4 | magic `0x524C5843` (`RLXC`) | not equal |
| 4 | 2 | format = 1 | not 1 |
| 6 | 2 | header length = 24 | not 24 |
| 8 | 4 | seq | `< 1` or `> 0xFFFFFFFE` |
| 12 | 4 | payload length | `> 4072`, or `> n - 24` for the bytes held |
| 16 | 4 | payload CRC-32 | does not match the payload |
| 20 | 4 | header CRC-32 over bytes 0..19 | does not match bytes 0..19 |
| 24 | … | payload: TLVs, ids strictly ascending | see § 3 |

CRC-32 is zlib/IEEE: reflected, polynomial `0xEDB88320`, init and xorout
`0xFFFFFFFF`. `crc32_ieee(0, "123456789", 9) == 0xCBF43926` 量 (host) and is a
known-answer test, not a self-comparison.

`seq` excluding 0 and `0xFFFFFFFF` is load-bearing on NOR: an erased sector reads
`0xFF`, so the all-ones slot must not be a valid record, and it is refused on the
`seq` field independently of its CRC. A zeroed slot (what `ftruncate` produces)
is refused the same way. Both directions are tested, including a well-formed
record with a *correct* header CRC and `seq` 0, which still refuses.

**Read order, and it is not the obvious one.** The header CRC is checked
*before* any header field is read. The alternative — magic, then length, then CRC
— uses the length that decides how many bytes get CRC'd before anything has
checked it, which is one bounds error away from the defect the file exists to
remove. The length is still range-checked after the CRC matches, because a CRC
is not an authenticator: anyone who can write the store can compute it.

Bytes between `24 + payload_length` and the end of the slot are **fill and are
not examined**, which is what lets a caller hand the whole 4,096-byte slot to
`cfg_parse_record`. 量 (host), both printed by `test_cfg.c` rather than counted
by hand: the full default record is **131 bytes** (24 + 107) and the largest
record the schema can produce — every variable-length key at its maximum,
`admin.pwhash` present — is **218 bytes** (24 + 194), **5 %** of a slot.

## 3. What makes a record invalid

Any one of these makes the **whole record** invalid, and the loader falls back to
the other slot and then to defaults:

* fewer than 24 bytes, or fewer than `24 + payload_length`
* either CRC mismatching
* magic, format or header length not this version's
* `seq` 0 or `0xFFFFFFFF`
* payload length larger than a slot's payload area
* a TLV length running past the payload (`-CFGE_TLV`)
* a partial TLV header or loose bytes at the end of the payload — "trailing
  bytes" means *inside the declared payload*, not the slot fill
* ids not strictly ascending, which makes a duplicate id unrepresentable rather
  than merely resolved (`-CFGE_ORDER`)
* an id the schema does not have (`-CFGE_UNKNOWN`)
* a length wrong for the id's type (`-CFGE_TYPE`)
* a value outside the id's bounds (`-CFGE_RANGE`)
* a cross-field rule violated (`-CFGE_CROSS`) — a record that cannot be a
  configuration is not a valid record, so the loader falls back rather than
  booting a machine into a state no SET could have produced

Keys absent from a valid record take their defaults. `admin.pwhash` has none, so
`cfg_get` returns `-CFGE_NOENT` for it and no code path can mistake an absent
hash for a zero hash.

## 4. Store semantics

Two 4,096-byte slots at offsets 0 and 4,096 of `/var/lib/cfg.bin`.

* **Load**: parse both slots, take the valid one with the higher `seq`;
  `source` is 1 or 2. None valid → defaults, `source == 0`.
* **Store**: `seq = max(valid seqs) + 1`, or 1 if none. Target = the slot **not**
  holding the current record; both invalid → slot 0. The whole 4,096-byte image
  (record then `0xFF` fill) is written, `fsync`'d, read back and compared both
  as bytes and as a parse. The other slot is never touched.
* `cfg_store` refuses a record that would not load back (it runs `cfg_validate`
  first). `SPEC-R7` does not require that; a store that accepted an invalid
  record would produce a file whose only effect is to make the next boot fall
  back.
* The one exception to "nothing outside the target slot is written": a file
  shorter than 8,192 bytes is `ftruncate`d to 8,192 first. The bytes that adds
  are zero, and a zeroed slot is invalid, so the extension cannot make a slot
  selectable — and it only happens when there was no other slot to protect.

## 5. The torn-write sweep — and the claim it can actually support

The brief asked for: *for a store holding record N, for every truncation length
0..4096 of the new slot image, `cfg_load` must still select record N.*

**That is not satisfiable, and the reason is the format rather than a bug.** The
record is 131 bytes and the remaining 3,965 bytes of the slot are fill the parser
never examines, so a write that got as far as byte 131 has written the *whole*
record and selecting it is correct. The invariant that is both true and worth
having is stronger:

> For every truncation length `L` in 0..4096, and for both possible previous
> contents of the target slot, the loaded configuration is byte-identical to
> record N **or** to record N+1 — never a mixture, never a partial record, never
> a value that was in neither — and "N+1 was selected" implies `L ≥ 131`.

量 (host), `test_cfg.c`, and green under gcc-13 and clang-18 with and without
`-fsanitize=address,undefined`:

| | |
|---|---|
| cases | **8,194** = 2 backgrounds × 4,097 lengths |
| backgrounds | (a) the target slot erased, `0xFF`; (b) the target slot holding an older record, seq 99 |
| selected record N (seq 100) | **262** |
| selected record N+1 (seq 101), complete, `L ≥ 131` | **7,932** = 2 × (4097 − 131) |
| a mixture, a partial record, or a fallback to defaults | **0** |

`L = 4096` is the positive control: without a case in which slot 1 *is* selected,
"always selected N" could be true because slot 1 is unselectable, and every other
case would be vacuous. Both outcomes occur, and the boundary is asserted
exactly, not merely bounded.

Background (b) matters more than (a). With an older record behind the write, a
short prefix can leave the slot byte-identical to the *old* record, which is
still a complete record and is correctly outranked by seq 100. 量 (host), counted
by the sweep rather than derived: that happens in **12** of the 4,097 cases,
longest `L` = **11** — the two records share their first eight header bytes and
three of the four `seq` bytes (100 is `00 00 00 64`, 99 is `00 00 00 63`), so a
prefix of 11 bytes or less changes nothing in the slot at all.

## 6. The bit-flip and single-byte sweeps

量 (host), over the 131-byte extent of a valid record:

| sweep | cases | result |
|---|---|---|
| every single-bit flip in the extent | **1,048** = 131 × 8 | **1,048 rejected**, 0 accepted, 0 accepted with changed values |
| every single-bit flip in the first 64 bytes of `0xFF` fill | **512** | **512 accepted, every value identical** |
| every single-byte change in the extent, all 255 wrong values | **33,405** = 131 × 255 | **0 accepted** |

The fill-region direction is not decoration: "everything in the extent was
rejected" would also be passed by a parser that rejects everything, and the 512
cases are what distinguishes the two. Every flip inside the extent being
*rejected* (rather than the weaker "rejected or self-consistent") follows from
CRC-32 detecting every single-bit and every single-byte error, with the header
CRC covering the payload-CRC field so that a flip there is caught too.

## 7. Fuzzing

Harness: `src/fuzz/fuzz_cfg.c`, a plain `main(argc, argv)` reading one file.
28 seeds in `src/fuzz/corpus/cfg/`.

**The format is fuzz-hostile, and the harness says so out loud.**
`cfg_parse_record` checks the header CRC before it reads any header field, so
essentially every mutation of a valid seed returns after nine instructions and
the TLV walk is unreachable. 量 (host): with no repair, the `badmagic`, `fmt2`
and `hdrlen20` seeds never reach the magic, format or header-length check at all
— they are refused on the CRC. So each input is parsed **twice**: once as-is
(which covers the CRC, magic, format and `seq` refusals) and once with both CRC
fields recomputed (which covers the TLV walk, the schema checks and the
cross-field rules). The payload CRC is only repaired when the payload the header
claims is inside the file, so the "payload length past the bytes we hold"
refusal stays reachable.

**What that costs:** nothing the fuzzer reports is evidence about the two CRC
fields. Pass 2 makes them vacuous. They are covered by § 6 instead, which is a
better instrument for that property than random mutation could be.

The harness copies the input into a `malloc` of exactly `n` bytes. A static 8 KiB
array would absorb a one-byte overread silently — the byte past a 131-byte record
would still be inside the array — and the planted-defect run below would find
nothing. Built with `AFL_USE_ASAN=1`.

### Pre-registered before the first `afl-fuzz` process

Written to `$FWRE_WORK/rebuild/s118/cfg/prereg-fuzz.txt` at 2026-09-30T01:38:34Z,
before any fuzzer ran (the file's mtime is the evidence of the order):

| | threshold | result 量 (host) |
|---|---|---|
| **P1** | branch coverage of `cfg_parse_record`, "taken at least once", ≥ **85 %** | **87.0 %** — 40 of 46 (`gcov -b -f`, over the 28 seeds + 168 queue entries = 196 inputs) — **MET** |
| **P2** | every refusal a file can reach is reached: all of `-1`..`-12` plus 0 | **13 of 13** — **MET** |
| **P3** | with an off-by-one planted in `tlv_next`, `afl-fuzz` finds a crash within **15 min** | **32.3 s** — **MET** |
| **P4** | the clean run reports zero crashes and zero hangs | 720 s, **365,254** execs, 507 exec/s, **0 crashes, 0 hangs**, stability 100 %, 168 queue entries, `bitmap_cvg` 29.34 % — **MET** |

**87.0 % is the ceiling, not a shortfall.** The six branches `gcov` reports as
never taken are each unreachable from a *file*, and every one of the other forty
was reached:

| never taken | why no file can reach it |
|---|---|
| `buf == NULL \|\| out == NULL` (2 branches) | the harness always passes both |
| `cfg_defaults` returning non-zero | it cannot, for a non-NULL argument |
| `cfg_index_by_id` returning `< 0` | `cfg_key_by_id` already succeeded on that id |
| `tmp.present[i]` already set | `tlv_next`'s ordering rule makes a duplicate unrepresentable |
| `len != 0` being false | no key in `SPEC-R7 § 4` accepts a zero-length value, so `schema_check_value` refuses len 0 first |

The pre-registration named the first four classes; the fifth (`len != 0`) is one
it did not, and it is the one that would come alive if a key with a minimum
length of 0 were ever added to the schema. 507 exec/s is low for a parser this
small: four other agents' `afl-fuzz` instances were running on the same 8 cores.

### The planted defect

In a **copy** of the tree, `tlv_next`'s bounds check `> avail - TLV_HDR_LEN`
became `> avail - TLV_HDR_LEN + 1`. Nothing in the repository carries an `#ifdef`
that weakens a bounds check; the planting is a `sed` on a copy.

量 (host):

| corpus | wall | execs | crashes |
|---|---|---|---|
| all 28 seeds | **32.3 s** | 17,554 | **1** |
| `full` + `erased` only (no seed whose payload ends in a variable-length value) | **900 s** (the cap) | 542,139 | **0** |

The crash input is 33 bytes: the `hostname-only` seed with its TLV length field
changed from `00 05` to `00 06`. Under the mutant that is accepted, and
`hostname_ok` then reads one byte past the payload — a heap overflow ASan reports
inside `schema.c`.

**The interesting number is the second row.** The time-to-find is a property of
the *seed corpus*, not of the fuzzer: with no seed whose payload ends in a
variable-length value, 542,139 executions over 15 minutes found nothing. A
fixed-length type at the end of a payload cannot expose an off-by-one, because
its own length check refuses a wrong length before any byte is read — measured
while writing the mutation control, and the reason `test_cfg.c` carries both a
"six bytes too long" and an "exactly one byte too long" case on a
variable-length key.

## 8. The mutation control

A green suite is a claim about its controls. Three copies of the tree, 量 (host):

| mutant | `test_tlv` | `test_cfg` | under ASan |
|---|---|---|---|
| **M0** unmutated | pass | pass | pass |
| **M1** bounds check removed | **1,742 failures** | **4 failures** | heap-buffer-overflow |
| **M2** bounds check off by one | **38 failures** | **1 failure** | heap-buffer-overflow |

M0 passing is the precondition: without it the other two rows would only show
that the tree does not compile the same way twice.

## 9. Test counts

`make -C src/cfgstore test O=<dir>` runs five suites in four configurations
(gcc-13 and clang-18, each with and without
`-fsanitize=address,undefined -fno-sanitize-recover=all`). 量 (host),
2026-09-30, all green, zero sanitizer findings:

| suite | assertions | what it is for |
|---|---|---|
| `test_crc32` | 528 | the IEEE known answers, the chaining identity, and a 512-case control that the CRC reads its input |
| `test_tlv` | 6,294 | the bounded reader, including an exhaustive sweep over buffer length × declared length asserting `accepted ⇔ len ≤ avail − 4` in both directions |
| `test_schema` | 489 | every key at its boundaries, text round trips, and one case per cross-field rule with the key id it must blame |
| `test_cfg` | 8,423 | the record, the two sweeps of § 5 and § 6, the store's alternation, and fail-closed |
| `test_cli` | 62 | the CLI's exit codes and its all-or-nothing SET, by `fork` + `execv` of the real binary |

**15,796 per configuration, 63,184 in all.** `-fno-sanitize-recover=all` is
load-bearing: UBSan's default is to print and continue, so a suite full of
undefined behaviour would exit 0.

## 10. Target build

`make -C src/cfgstore target O=… TC=… TRIP=…`, gcc 3.4.6 / uClibc 0.9.30, no
`-march`, `-Wall -Wextra -Werror`, every vendor binary under
`tools/vendor-tripwire.sh` from a scratch directory inside `$O`. 讀 from the
artefact, 2026-09-30:

| | |
|---|---|
| unstripped ELF | 114,594 bytes |
| **stripped** | **76,944 bytes** (sha256 `6aaebdab3138bbf0…`) |
| `.text` / `.rodata` / `.data` / `.bss` | 0xd3f0 / 0x2240 / 0x250 / 0x23f8 |
| shape | ELF32, big endian, `EXEC`, MIPS, `e_flags 0x1007` (noreorder, pic, cpic, o32, mips1), no `PT_INTERP` |
| `hazlint` | **0 violations** in 2,902 loads, 13,622 words scanned |
| objects kept | 5, at `$O/target/obj/cfgstore/` |

`e_flags 0x1007` equals `linkprobe`'s, for `linkprobe`'s reason: a C-only link
sets `EF_MIPS_PIC` where one linking hand-written non-PIC asm does not.

### `noshell-gate.sh`, and the false positive that shaped it

A byte scan for a function *name* is not an acceptable source, and this
artefact is the fixture. 量 (host), 2026-09-30, on the shipped
`cfgstore.stripped`: the token `system` appears **4 times**, and all four are
uClibc prose —

```
Interrupted system call
Too many open files in system
Read-only file system
Interrupted system call should be restarted
```

— while the symbol table of the same link holds **0** entries named `system`. A
name scan would refuse a clean binary. (The same shape was measured
independently on a static busybox 1.13.4 for this target: 7 string hits, all
prose, symbol table clean.)

So the gate uses two sources and a precondition:

* **①** the symbol table of the *unstripped* link: any entry named `system`,
  `popen`, `pclose`, `execl`, `execlp`, `execvp`, `execv` or `posix_spawn` is a
  violation. `execve`, `fork` and `vfork` are **not** on the list — `SPEC-R7 § 2`
  permits `fork`/`vfork` + `execve` with a fixed `argv`, and a gate that forbade
  them would forbid the sanctioned mechanism. All eight read 0; `execve`, `fork`
  and `vfork` also read 0, because this program executes nothing at all.
* **②** a byte scan of the *shipped* bytes for a shell invocation **path**
  (`/bin/sh`, `/bin/bash`, `/bin/ash`, `/bin/dash`) — bytes that are the
  objection rather than a word inside a sentence. All four read 0.
* **the carry**: ① reads a file that is not shipped, so `.text` must have the
  same offset, size and sha256 in both files. 量: `0x160 + 0xd3f0`, sha256
  `0a16826db381c58b…` in both. If they differ the gate **refuses** rather than
  assuming.

It **refuses** a file with `e_shnum == 0` — the vendor's shape, for which a
`.dynsym` walk through section headers throws and a `PT_DYNAMIC` walk is
required. This gate does not do one and does not pretend to.

Five controls, each shown holding before the verdict: ② sees `/bin/sh` in a file
that has it and not a string that is absent; ① sees `system` in a
cross-compiled ELF that calls it (**without a positive control the gate refuses
to certify**); the `e_shnum` precondition fires on a copy with `e_shoff` and
`e_shnum` zeroed; the `.text` comparison refuses a pair differing by one byte;
and the verdict is still clean on a file that *mentions* `system` — which is the
subject itself. The gate was also shown reporting `VIOLATION` on a stripped
build of the positive control, and refusing when `--positive` points at a clean
ELF.

The `e_shnum` control needed two fields, not one: ELF extended numbering says
that when `e_shnum` is 0 and `e_shoff` is not, the real count lives in section
header 0's `sh_size`, and `readelf` implements it — so zeroing `e_shnum` alone
left the control silently not firing. It refused itself, which is how it was
found.

## 11. What this does not establish

* **Nothing here is on flash.** `/var/lib/cfg.bin` is on tmpfs in R7, so the
  store does not survive a power cycle; R8 supplies the MTD backing. Every
  property above is a property of the format and of the code, measured against a
  file, and the `0xFF` fill and the `seq` exclusions are the parts written *for*
  NOR rather than *on* it.
* **No protection against an attacker who can write the store.** CRC-32 is an
  integrity check against corruption, not a MAC. Anyone who can write the file
  can produce a valid record with any values, `admin.pwhash` included. What the
  A/B design buys against a hostile writer is nothing at all.
* **No login is possible in R7.** `src/lib/kdf.h` declares `kdf_scrypt` and
  returns `-ENOSYS`; the scrypt parameters come from plan `D8`'s anti-DoS budget
  (16 MiB for `N=16384, r=8, p=1` against 26,052 kB of usable RAM, `MEM-06`) and
  are another agent's to settle. `cfgstore passwd` therefore refuses before it
  draws a salt or opens the store, and `admin.pwhash` stays absent. This is the
  intended state, not a gap.
* **The torn-write model is a prefix write.** It does not model a device that
  commits pages out of order, nor one whose partially-programmed word reads back
  as a value that was in neither image. On NOR a programmed-but-incomplete word
  can read as the AND of old and new; that is not covered and cannot be until
  R8 puts the store on the chip.
* **`fsync` on tmpfs is not a durability measurement.** The read-back verify is
  real; what it verifies is that the page cache agrees with itself.
* **No inter-process locking.** brokerd is the single writer by design; a
  concurrent `cfgstore set` can *lose* an update (last writer wins) but cannot
  corrupt the store, because each writer only ever writes the slot the other is
  not reading.
* **`dump --hex` prints the record as it is on the medium**, hash bytes included,
  to a root console. That is deliberate — a diagnostic that hides bytes cannot
  diagnose them — and it is the one place `admin.pwhash` is printable.
* **The fuzz result says nothing about the CRCs** (§ 7), and the coverage figure
  is a host figure over a host build. Nothing in § 7 or § 9 ran on the device.
* **12 minutes of fuzzing is 12 minutes of fuzzing.** 365,254 executions with no
  crash is not an absence proof; what it is worth is bounded by the planted-defect
  result beside it, which is the only reason to believe the harness was connected
  at all. The minimal-corpus row of § 7 shows how narrow that reach can be.
* **`hazlint` 0 violations is about the shipped code, not about the hazard.** It
  reports that no load's result is read in a delay slot in this ELF; whether this
  core would have mishandled one is `TC-h`.
* The `cfgstore` CLI has not been executed on the device. Every CLI number above
  is from the host build; the MIPS build has been linked, gated and measured,
  never run.
