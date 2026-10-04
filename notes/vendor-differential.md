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

`map_hashed` 4,186,112 with `map_h601_skipped 8192` at level 0, and 122,880 +
8,192 = 131,072 at level 1 — group 0 fully accounted for. `n_writes` 0 before
and 0 after. The level-0 digest also equals the rehearsal taken at 04:52 the
same day (`FW-192`), so flash did not move across the whole day.

### 2.1  推 — and it would explain a result `P2` left open

`P2` bracketed nine vendor boots and got **31 same / 1 DIFFER in group 0**,
never explained. `FW-196`'s branch writes `AUTHG_IP_ADDR`, which lives in
COMPCS at `0x00C000` — and `0x00C000` is **inside group 0**. `P2` was not
avoiding gated paths; this seating was, and group 0 did not move.

**This is 推, not a result.** What decides it, both desk reads of committed
captures with no device: ① whether `P2`'s probing touched any path carrying
`htm`, and ② which unit index `P2`'s DIFFER named, against the one `0x00C000`
falls in. Until both are read, the honest claim is the narrow one: *this*
episode changed no unit at either granularity.

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
`V-D`, which `R9-4` owes. And a 302 to a login page is a reading about a
surface, not a finding about authentication.
