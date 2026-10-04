# The vendor differential, as measured

Owner of what `R9-6` and `R9-7` read off the silicon. `docs/differential.md`
(`R9-8`) renders a published table from this; this file is the readings.

## 1  The seating, 2026-10-04

**One power action**, the owner's, and it was needed for one reason only: the
vendor firmware has no shell, so nothing can be told to reboot. Getting *in*
cost nothing.

| | |
|---|---|
| into the vendor | `busybox reboot -f` + ESC catch to `<RealTek>` (量, `FW-37`), then `J BFC00000` and send nothing (量, `M2-BOOT`). **Two measured halves rather than one inferred path**, and the jump follows the catch in one invocation, so the board is never left at the prompt (`NET-165`) |
| the vendor booted | `bench/2026-10-04/VEND-BOOT`, **1,979 bytes — the same size as `M2-BOOT`**. `boa: starting server pid=350, port 80`, `MiniIGD v1.09.1`, `WiFi Simple Config v2.18-wps1.0`, `wan_disconnect: StartDnsSpoof`, `Start NTP daemon`; no `rlxfw:` line |
| J | host 12:52:06.4; `boa` up at 12:52:39.1, so **J+32.7 s** |
| the window | `J+33` to `J+601`. The probes ran 12:53:06–07, **one second**, far inside it |
| back to rlxfw | owner's power cycle; catch at 29.8 s; `AUTOBURN` read back `00000000`; ARP 4/4; `nfjrom` 1,108,992 B in 2,167 blocks in 1.69 s; staged head equal to the image's first four words; `f184a` up with all six programs |

### 1.1  Why the episode was contained twice over

`FW-196`: the vendor writes flash on an **unauthenticated** request to a gated
path past an uptime threshold. So the seating owed two containments, and
`CLAUDE.md` is the reason it owed *two*: a containment that holds only if the
experiment comes out as expected is not a containment, and path safety holds
only if the probe list is right.

* **Path.** 量 by reading every `path =` in `config/r9-probes.toml`: exactly one
  carries the substring `htm`, `/status.htm`, which is the third of the seven
  names the branch excludes. Every other path fails `strstr(uri, "htm")`
  outright. The `/boafrm/`, `/goform/` and `/cgi-bin/` probes use an impossible
  handler name, so they test whether the prefix exists without firing a handler
  — which matters because `handleForm` has no method test and a GET fires one
  exactly as a POST does.
* **Timing.** The whole HTTP episode finished at J+61 s against a J+601 s
  threshold. This containment does not depend on the list being right.

## 2  The flash bracket: clean at two granularities

量 `bench/2026-10-04/MAPV0`, `MAPV1` (before) against `MAPW0`, `MAPW1` (after):

| level | units | before | after | |
|---|---|---|---|---|
| 0 | 32 x 131,072 B | `ae87ac03269985d6…` | `ae87ac03269985d6…` | **same** |
| 1, group 0 | 32 x 4,096 B | `44355799377e731e…` | `44355799377e731e…` | **same** |

`map_hashed` 4,186,112 with `map_h601_skipped 8192` at level 0 — the driver
prints the pair verbatim as `map_hashed 4186112` and `map_unit 131072`, without
separators — and 122,880 +
8,192 = 131,072 at level 1 — group 0 fully accounted for. `n_writes` 0 before
and 0 after. The level-0 digest also equals the rehearsal taken at 04:52 the
same day (`FW-192`), so flash did not move across the whole day.

### 2.1  The 推 this section used to carry is REFUTED

The current value: **the device's whole-chip map at 128 KiB granularity has not
changed once across 46 readings spanning 26 days**, so there is no change for
`FW-196` to explain. `SPEC.md` `FW-201` owns the measurement; the story of the
retraction is in `LOG.md` 2026-10-04.

量 2026-10-04 at the desk, by program, over the committed captures, with the
capture's own fields as the gate: the population is every `bench/**/*.log`
carrying `^map_level 0`, and a row is compared only when the number of body
lines the pattern matches **equals that capture's own `map_lines`**, with
`map_truncated` read beside it — so a partial capture is marked and skipped
rather than compared short. **46 captures qualify**, over **22** date
directories from `bench/2026-09-08b` to `bench/2026-10-04`, every one
`map_lines 32` and `map_truncated 0`, and **all 46 carry the identical 32-line
body digest `ae87ac03269985d6`** under § 2's normalisation (`tr -d '\r'`, each
line newline-terminated; without the trailing newline it reads `eec0ff39…` and
a reader concludes flash moved). That span includes both of `P2`'s vendor
seatings and the 2026-10-04 vendor episode with its 27 unauthenticated probes.

**Three controls, because one digest over 46 captures is a claim.** 🟢 The
`map_lines` gate is load-bearing: **24** further captures carry `map_level 0`
with no map body (they are `n_writes` readings) and the gate excludes them —
without it they would enter with an empty body, agree with each other
trivially, and inflate the population to 70. 🟢 The pattern must match an
offset containing an **uppercase** hex letter: 12 of the 32 offsets do, and all
46 captures read 12. 🟢 Four `map_level 1` captures stay out of the population
(negative control), and flipping one byte of one capture's body moves the
digest to `162bbddeac409533` (detection control).

🔴 **So the single `DIFFER` was never a before/after bracket.** It is a standing
*device-versus-2026-08-16-dump* difference — the line's own fourth field is
`dump` — and it is already present in the earliest qualifying capture,
`bench/2026-09-08b`, two weeks before `P2`'s first vendor seating, where that
date's `CORRECTIONS-block14.md` records the same `31 same, 1 DIFFER`. The
differing unit is `000000`, that is `[0, 0x020000)`.

🔴 **And at 4 KiB granularity it fails a second way.** 讀
`notes/spi-mtd-driver.md`: group 0 is **30 same, 2 DIFFER**, and the two
differing units are `009000` and `00D000` — **`0x00C000`, where `FW-196`
writes, is SAME.**

**The residual, which is not nothing.** `00D000` *is* inside COMPCS
(`0x00C000` + `0x1D36` ends at `0x00DD36`, so COMPCS spans both units), so a
vendor configuration write at some time before the dump baseline remains a live
candidate for the dump divergence — it simply cannot be attributed to `P2` or
to the 2026-10-04 episode. `009000` is unexplained and `FLS-26` holds it ⊘.

**What this does not establish.** Not that the vendor never writes
`AUTHG_IP_ADDR`: `FW-196` stands 讀. Not the digest's **sensitivity**: 46 equal
digests over unchanged flash say nothing about whether a small write would be
detected, and a sensitivity control needs a known change, which is a write.
Nothing about two writes that cancel, or about any byte outside the units read.

### 2.2  `P2` sent no HTTP at all, so the sentence saying it did not avoid gated paths is withdrawn

🔄 **2026-10-04 correction.** § 2.1 used to read *`P2` was not avoiding gated
paths; this seating was*. 量 by reading `P2`'s two seating directories
(`bench/2026-09-23`, `bench/2026-09-25`): the only commands issued against the
vendor were `ip neigh flush`, `ping`, and one
`nmap -sT -p- -T4 -n --max-retries 1` per seating. A grep for `curl`, `wget`,
`GET /`, `boafrm`, `goform`, `cgi-bin` and `.htm` over both directories returns
**zero files** — **positive control, same grep, same day**: the identical
pattern over `bench/2026-10-04` returns **six** files. **So `P2` sent no HTTP
and therefore no URI at all**: `FW-196`'s branch is reached through a URI, so
`P2` could not have reached it, and the sentence that distinguished this seating
from it was wrong in the direction that flattered this seating. ⚠️ What is *not*
re-derived here is `P2`'s timing axis — its vendor boots' residency against the
600 s uptime threshold. Those captures carry no `started_wallclock`, so the
bound would need the seating's `.timing` files read, and the path axis above
settles the sentence on its own.

## 3  What the columns found

Both columns, one instrument, same host, cable, port and target (`10.1.1.1` —
量 the vendor and rlxfw share the address, which is why they are comparable at
all). 27 cases, 21 of 89 `V-A` rows, 68 exempted by name with reasons.

| case | vendor | rlxfw | reading |
|---|---|---|---|
| `C02`, `C03` | connect-ok on 52869 and 52881 | **ECONNREFUSED** | the vendor runs two more servers; rlxfw runs none there |
| `C04`–`C09` | ECONNREFUSED on 23, 22, 5555, 7547, 9999, 20005 | — | six closed ports: the negative control that separates *closed* from *never ran* |
| `C26` | **200 OK** | **431 Request Header Fields Too Large** | rlxfw enforces a header-size bound the vendor does not |
| `C19`, `C20` | **200** on `//config.dat` and `/./config.dat` | **400** | the vendor serves its config blob under normalisation variants, unauthenticated; rlxfw rejects the malformed path |
| `C13`–`C18` | 302 to the login page | 404 | different unauthenticated surface shapes |
| `C27` | 206 Partial Content | 200 | rlxfw does not implement Range |
| `C21` | 501 | 501 | a row where they agree, which is worth publishing too |

`compare` reports **137 differing fields over 27 cases**. Bodies for the
config-bearing cases read `not-requested body-bound`: status and length only,
no body and no digest, because this unit's own configuration and hashes of it
may not enter this repository.

### 3.1  The instrument's own control, which found something

Two vendor runs 60 s apart, same cases: **1 differing field of 27 cases** —
`C12 hdr_sha256`, which is `/status.htm`, a status page whose headers vary by
construction. So 26 of 27 reproduce byte for byte and the exception is
localised and explained. That is why `--require-same` is opt-in.

## 4  What this file does not establish

It does not establish that the digest would **detect** a small write: two equal
digests show reproducibility over unchanged flash, and a sensitivity control
needs a known change, which is a write. It does not close `R9`: 68 of 89 `V-A`
rows have no live probe and are exempted by reason, so the published table must
say 21 and not 89. It says nothing about the 52 cases in tiers `V-B`, `V-C` and
`V-D` — 🔄 **2026-10-04: those 52 are not owed, they are carried.**
`config/fix-cases.toml`, `R9-1`'s register, holds one row per upstream case:
讀 141 rows, 89 `V-A` + 29 `V-B` + 10 `V-C` + 13 `V-D` = 141, and 141 of 141
carry `mechanism_class` ①, `vendor_evidence` ②, `rlxfw_evidence` ③ and
`opposite_check` with `opposite_check_reading` ④, with no empty cell among the
five. What this file does not carry for them is a *live probe*, which is the
sentence above. And a 302 to a login page is a reading about a surface, not a
finding about authentication.
