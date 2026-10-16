# `docs/KNOWN-ISSUES.md` — closed entries and earlier releases' sections

Moved here verbatim from `docs/KNOWN-ISSUES.md` at `530dce4c` by `P5e-2` on 2026-10-09: every entry
whose own text records it closed or fixed, and the `v0.5` and `v0.6` sections, each whole and
in the file's order. The current file keeps the entries still open and the `v1.0` section.
First are the two paragraphs of the current file rewritten to point here, as they stood: its
lines 9–12, and lines 1656–1662, the opening of its `v1.0` section. A record: never edited.
`tools/docmove.py` proves the move.

## Rewritten in `docs/KNOWN-ISSUES.md` on 2026-10-09, as they stood at `530dce4c`

⚠️ **This file on `main` is the CURRENT list, not `v1.0`'s.** A release's list is
the copy at that release's tag, which is frozen; this one keeps moving. Anything
that has since been closed is at the bottom rather than deleted, so the two can
be read against each other. 🔄 **`v0.2` → `v0.3` on 2026-09-11.** 🔄 **`v0.3` → `v0.4` on 2026-09-17.** 🔄 **`v0.4` → `v0.5` on 2026-09-29.** 🔄 **`v0.5` → `v0.6` on 2026-10-04.** 🔄 **`v0.6` → `v1.0` on 2026-10-09.**

`v1.0` is defined by `R6c`, `R8`, `R8b`, `R9`, `P3` and `P4b` (`README.md`'s version map). `R8` closed
on 2026-10-04 before `v0.6` was tagged and is in `v0.6`'s section above; this release adds the other
five, and each gate's full list is its entry in `docs/GATE-RESULTS.md` — `R9` 19, `R8b` 20, `P3` 21,
`R6c` 22, `P4b` 23. It is the first release made with a binary: the image `mainline-9bb2bec7.img`,
1,110,016 bytes, sha256 `295d4f6aec14f8b6ee21ebccec05e6b5492d8785274afe676fbfa5a070fb86bd`,
`RECIPE_ID` `9bb2bec7`, built twice byte-equal from `034b5a7d`, and the same bytes in the signed
container `T.rlxu`. The ones a reader of this release most needs:

## 🟢 `cardcheck` refuses a flash-write command on a card — closed 2026-09-23 (`P2-2`)

*(was, 2026-09-23, one hundred and second segment: no tool refused one;
`classify_command` returned `('LOADER', [])` for `FLW 0 0 0` and for
`EW 8040D4A0 1`, so nothing but a reader stood between a card and a flash
write.)*

量 at the desk, 2026-09-23: `FLW`, `EW` and `EB` in any case, and every
`AUTOBURN` but the exact string `AUTOBURN 0`, each draw one `FLASH WRITE` issue
(`A29`, `A30`); `DW`, `J`, `AUTOBURN 0` and `LOADADDR` are untouched (`A21`). The
one way through is the owner's dated yes on the card itself: an `owner-yes`
fence of `YYYY-MM-DD<TAB><payload>` rows, matched byte for byte and not after
whitespace normalisation, because the loader's tokeniser splits on single
spaces (`A31`, `A33`). A malformed row, a second row for one payload and a row
that permits nothing each fail in their own right (`A32`, `A34`). No
`cardabsent` line and no `--expect-absent` reaches a loader issue (`A35`);
before this change `--expect-absent FLR` took `FLR`'s H601 containment issue
from 1 bad to 0. The two frozen cards' three `EW B800311C …` rows are excused
by (card, exact payload) (`A36`), and `B12` sweeps that list both ways. All 85
cards keep their exit status against `HEAD`'s `cardcheck` run in `HEAD`'s own
tree; only those two print a note per excused row. The mutation suite's new
`W0` requires every kill to turn the case its row names red, and it found two
kills counted since 2026-08-31 that were not kills: `M1` never compiled and
`M11` died of an `AttributeError`. `SPEC.md` `FW-113`.

What this does not establish: that a yes came from the owner (presence and
exactness only). Anything written other than as a single-quoted
`--send '...'`: of 15 flash-verb payloads the committed captures record as
sent, 3 are in such a `--send`, and `bench/2026-08-24c/PREDICTIONS-block3c.md`
cell `D4c` (`EW B800311C 40000`, in a table cell) still passes. Anything about an
upload: the `AUTOBURN` read-back before a `put` is still enforced only by
`looprun`'s `S5b`.

## 🔴 rlxfw's NIC driver loses frames it reports as sent, and `recover` cannot see it — 2026-09-23 (seating 39)

🟢 **Fixed as the default, 2026-09-27/28 (`R6b`).** The loss is a descriptor-length fault: with the
vendor's convention (`m_len` = `m_extsize` = `ph_len`) E2's eleven lengths answered 220 of 220 on
two boots, the end-of-test exchanges complete 12 of 12, and 31 minutes of flood fired no recovery;
`rtl819x-nic` 1.6 writes that convention by default (`docs/GATE-RESULTS.md` 2026-09-28, `SPEC.md`
`NET-154`, `NET-158`). What stays open is why the engine damages the old lengths. The rest of this
section is the finding as it stood on 2026-09-23.

量, `P2-3`'s press 1 on `p2q` (`rtl819x-nic 1.4`): of the twelve `iperf3` trials on
`rlx0`, six never completed their end-of-test exchange and three could not
connect (`No route to host`); on the same hardware and kernel the vendor driver
completed all twelve (`notes/nic-driver.md` § 19, `NET-111`, `NET-114`). The
switch's own counters say why: no receive loss the counters can resolve (346,724 =
346,724; 🔄 111th segment: "every frame that entered port 3 reached the driver" until
seating B's same comparison read +2 frames and +134 B across a handover, so the method
bounds a receive loss and cannot show it zero, `notes/nic-driver.md` § 20.4), and at
least 182 frames the driver handed to the engine never
left port 3 (`NET-112`) — the iperf3 server's results, retransmitted and never
acknowledged, and the answers to the host's ARP. `recover` arms only when four TX
descriptors are engine-owned and a fifth frame is offered, so a loss in which the
engine clears OWN never triggers it (`NET-113`).

**What depends on it**: any use of `rlx0` that ends a transfer with a small reply —
a TCP session's close, a request/response, ARP after heavy traffic — can hang
until something else fills the TX ring. A throughput figure from `rlx0` is valid
only while data flows, and `P2`'s rlxfw receive figure has n = 1: `TR1`'s 16.953
Mbit/s, read in seating B from the board's own server log, the host having no
`receiver` line (`NET-116`; 🔄 111th segment: "n = 0 (no `receiver` line exists)"
until then). **What settles the mechanism**: § 19.5's experiments E0–E5, zero
flash, one power press. 🔄 111th segment: block 45, `R6b`'s first bench block, ran
E1–E6 and E10 and placed the loss in frames of lengths the engine was not given
(`NET-119`); the mechanism is `R6b`'s, its eight candidates all 推
(`notes/nic-driver.md` § 21).

## 🟢 `cardcheck` refuses a HOST cell its own tool rejects — closed 2026-09-24 (`P2-4`, `FW-124`)

*(was, 2026-09-23, one hundred and fifth segment: nothing checked a frozen card's
`HOST` cells; twice a card carried one whose own tool rejected its arguments,
found only at the bench — block 41's `netblast` options and card B44's `Z9-D2`.)*

量 at the desk, 2026-09-24 (108th segment): `cardcheck commands` now reads every
`HOST <prefix> :: <cmd>` line of a card, inside a fence or not, with the grammar
of `tools/cardrun.py` — the runner that executes cards and the grammar's one
owner (`FW-132`) — and puts each project-tool command to that tool's own
`build_parser()` and `refuse_args()` in-process, so the reason printed is the
tool's own. Over the 86 committed cards it refuses exactly the twelve cells the
107th segment's research predicted before any code existed; they are excused by
(card, cell, a fragment of the refusal) in `FROZEN_HOST_CELLS`, swept both ways
by `B13`. Every card keeps its `commands` and `numbers` exit status against the
tool at `0dfb2dd`. `SPEC.md` `FW-124`.

What this does not establish: anything about a system command's arguments
(177 in the corpus are counted and named, never checked); anything a tool checks
only after `refuse_args` — routes, interfaces, the iputils floor, image digests,
records that already exist; what a cell means (a correctly spelled `--rates 43`
in Mbit/s passes); that each tool's `refuse_args` is complete.

## 🔴 What `v0.5` does not establish — 2026-09-29 (`R6`, `P2`, `R6b`)

`v0.5` carries `R6`, `P2` and `R6b`; each gate's full list is its entry in
`docs/GATE-RESULTS.md`. The ones a reader of this release most needs:

* **`D8` passes on switch state rlxfw did not write.** `init` sets five bits; the VLAN table, the
  PVIDs, the netif entry, `FFCR`'s two traps, EEE and `QNUMCR` are the loader's. The registers among
  them read the same on 15 boots of the catch → upload → `J` path and the tables on three, and none
  was read on a boot for which the loader did not bring its network up — the way a product boots,
  from flash, which the zero-write rule keeps out of reach through `R9`.
* **How a frame addressed to `rlx0` reaches the CPU is 推 on one source**: the loader's
  unknown-unicast trap (`NET-169`). With `FFCR` inherited, every unknown unicast and multicast frame
  from any LAN port also reaches the CPU; this bench, one host on port 3, has not measured that load.
* **The transmit fault's mechanism is not named.** The fix is one variable; which component inside
  the span between the driver's descriptor fill and the CPU port's receive MAC damages the old
  lengths, and why, is open. The operating clause at fourteen entries names it as the next gate.
* **The flipped mainline has not booted.** Since 8g, `quiet` and `loud` build `SWCORE=n` (recipe
  `8b5ae480`). The image arm I passed on (`r6b8i`, recipe `3685a3a4`) was built under the retired
  name `quiet-noswcore` with the same rule set; no image of the new recipe, and no `SWCORE=n` `loud`
  image, has been built or booted.
* **`D8` is one seating**: one image, one cold and one warm boot, one host on port 3; the address
  half of its neighbour-entry conjunct has one reader.
* **`P2`'s interrupt latency by logic analyser never ran** (`LA-1`, carried to `P3`), and its loud
  column has one boot per seating.
* **`D5` carries one ⊘ that a ruling put there**: the 1,472-B rtt mdev rise (`NET-121`), which the
  owner may override.

## 🔴 `httpd` refuses every login after a child exits holding the KDF grant — 2026-09-30 (`R7-8`, first boot of rlxfw's own userspace)

`POST /api/login` answers `429 {"ok":false,"error":"ratelimit","retry_s":2}` and does not
recover. 量 on the device: refused at 640 s, 660 s and 832 s of uptime, with 20 s and then
90 s of complete quiet in between, while `GET /api/status` answered 200 in the same minute —
so httpd was alive, forking and serving, and only the login path was shut.

**The mechanism, reproduced on the host as a failing unit test before anything was changed.**
`srv_loop()` kept the identity of the child holding the single KDF grant in **two** places:
`kids[i].holds`, and a local `int kdf_inflight`. The decision read the local. `reap()` clears
`holds`, cannot reach its caller's local, runs at the **top** of the loop, and closes
`kids[i].fd` — discarding any unread release byte or EOF, which were the only two paths that
cleared `kdf_inflight`. A child that exited while holding the grant therefore left the marker
set on an empty slot; `if (kdf_inflight >= 0)` was then taken by every later login, and the
literal `retry = 2` in that branch is the constant `retry_s`. The refusal happens **before
either rate bucket is consulted**, which is why 90 s of idle changed nothing.

**It is a race, not a deadlock**, and saying so matters: one `401` did get through at 05:29,
immediately followed by eight consecutive `429`s and a ninth after 15 s of quiet. Whether the
parent reads the release byte before `reap()` closes the fd decides it. Killing `httpd` and
letting `init` respawn it clears the marker, because it is a local in the parent's loop and a
new parent starts clean.

**`rl.c` was exonerated first, and how is worth more than the fix.** Replaying the device's own
timeline through `rl.c` with an injected clock **grants** the login at +20 s and at +90 s; a
sweep of **2,709,903** reachable `(tokens_milli, last_ms)` pairs per bucket found **0** that
refuse after a 90 s gap. An empty global login bucket names `retry_s` 5 and an empty per-IP
bucket names 11 — the value 2 is reachable only within 250 (respectively 100) milli-tokens of
granting, a state that grants within 2 s. `now_ms()` is `clock_gettime(CLOCK_MONOTONIC)` in
milliseconds, not `times()`, so this kernel's `INITIAL_JIFFIES = -300*HZ` never reaches it and
640–830 s is nowhere near the 49.7-day wrap.

**So the honest headline is not "the tested implementation and the deployed implementation were
different code".** `test_rl.c` did cover the deployed bucket, and it was right: the bucket was
never broken. What had no test at all was the **state machine around** it, written inside a
`for(;;)` that needs `fork()`, `accept()` and a listening socket to enter. The defect is
**duplicated state with only one copy maintained, in the one function no unit test could call** —
and the repair makes that function testable by extracting the arbitration behind
`srv_kdf_reset`/`ask`/`gone`, so a test drives the decision that actually ships.

A second, smaller defect was found in the same pass and is not what the device did: a refusal
the *global* bucket caused also charged the caller's per-IP bucket. It self-heals within 11 s.

🟢 **Fixed and proven on the device**, 2026-09-30, on a rebuilt image. The
discriminator was registered before the run: a leaked grant refuses with the *constant*
`retry_s` 2 before either bucket is consulted and never recovers, while a legitimate bucket
refusal names a truthful wait and clears. 量 twelve consecutive logins: attempts 1–3
**HTTP 200** at 0.912 s, 0.909 s and 0.911 s — the burst of three the design allows — then
attempts 4–12 refused with **`retry_s` 9**, a real bucket figure, and after 15 s of quiet
**HTTP 200** again in 0.909 s. The recipe id is *not* the evidence that the fix is in the image
(`RECIPE_ID` digests `config/` only, and `config/` changed for an unrelated reason); the evidence
is that the new stripped `httpd` appears verbatim inside `vmlinux_img` and the old one does not,
with the control run both ways.

## 🟢 `brokerd` never saw a password set after it started, so `cfgstore passwd` had no effect until it restarted — 2026-09-30 (`R7-8`); fixed, and shown on the device 2026-10-03

量 on the device, and it is a separate defect from the one above. `cfgstore passwd` succeeded —
`written: slot 1, seq 2`, and `admin.pwhash set: scrypt log2N=12 r=7 p=1, entropy_avail was
150` — `cfgstore get admin.pwhash` reads `set`, and `/api/status` reports `auth_ready:true`.
Yet the **correct** password was answered `401 {"ok":false,"error":"auth"}` in **14 ms**. 14 ms
means no KDF ran, and that is what `brokerd` answers when it believes no password is set.

**Confirmed by one experiment rather than by reading the code.** `busybox kill 12 13` let `init`
respawn both daemons (`brokerd exited exit=0` → pid 81, `httpd exited signal=15` → pid 82), and
the same password then returned **HTTP 200** with a session's csrf token and `ttl_s 900`. So the
configuration `brokerd` loads at start-up is the only one it ever has.

For the first password this fails **closed**: it refuses a login rather than allowing one. 🔴 **For
a password `cfgstore` replaces, it fails open**, which this entry did not say until 2026-10-03.
On the host, `5eaeb643`'s broker kept accepting the replaced password and kept honouring every
session opened under it (讀 + host test `src/brokerd/test_reload.c`, R2 and R3; on `5eaeb643`'s
`brokerd` it fails 16 of its 40 checks, 2 of them controls). 量 on `r78a`, `F184-old`
(`bench/2026-10-03/`), with `brokerd`'s pid 25 the same before and after: once `cfgstore passwd`
had replaced the password, the **new** one was answered **HTTP 401 in 0.896 s**, a KDF's time, so
it was checked against a stored hash (推: the one `brokerd` loaded when it started), and the
**replaced** one **HTTP 200 in 0.897 s**. The same run reproduced the first half: the first
password, written while `brokerd` ran as pid 12, was answered HTTP 401 in 0.143 s, no KDF, and
HTTP 200 in 0.908 s once `busybox kill 12` had let `init` respawn it as pid 25.

🟢 **Fixed, and shown on the device 2026-10-03.** `brokerd` now re-reads the store before every
request it has not already refused (`bk_cfg_reload()`, called from `bk_dispatch()` before the
session lookup), so each request is answered from the record a broker started at that instant
would load. No lock is needed, 讀: `cfg_store()` writes in place, not by rename, but only into the
slot that does not hold the selected record, and the per-slot header CRC, payload CRC and seq make
a re-read that races a write return the last complete record (`src/cfgstore/test_cfg.c`'s
torn-write sweep). A store that cannot be read, or has bytes and no valid record, leaves the
defaults, which have no `admin.pwhash`; that is logged once per change of state. A changed
`admin.pwhash` drops every session, as PWSET does. `test_reload` passes all 40 checks on the fix,
built with gcc-13, with clang-18, and with clang-18 under asan and ubsan.

量 on fw184's image `f184a`, `F184-fix2`, with `brokerd`'s pid 12 the same before and after: the
first password was answered **HTTP 200 in 0.892 s** straight after `cfgstore passwd` wrote it,
with no restart; after a second `cfgstore passwd`, the **new** password **HTTP 200 in 0.896 s**
and the **replaced** one **HTTP 401 in 0.892 s**. The recipe id is not the evidence that `f184a`
carries the fix: both boots print `RLXFW-ID0=0E45C61D`, because it digests `config/` only. The
evidence is that the new stripped `brokerd` (101,212 bytes) appears verbatim in `f184a`'s
`vmlinux_img` and not in `r78a`'s, the old one (101,172) the reverse, with the other five
programs byte-identical to `r78a`'s; and `ls -l` on the device read `/usr/sbin/brokerd` as
101,212 bytes (`F184-new-id`).

⚠️ **The first run on `f184a` decided nothing, and it is kept.** `F184-fix` read INCONCLUSIVE.
`f184a` had just booted; `brokerd` answers LOGIN and PWSET with NOENTROPY until `entropy_avail`
has reached 128 once (`CB2-boot`: `entropy_avail=0 auth_ready=0`); `/api/status` did not report
`auth_ready` within the script's 180 s, so the script stopped before writing any password (讀,
its step 0). 1,000 echo requests at 7.1 ms (1,000 of 1,000 answered, by the host's ping log
`$FWRE_WORK/rebuild/s119/bench/ENT1-ping1.txt`, outside this repository) then moved
`/proc/rlxfw-entropy`'s `ev_nic` 288 → 2,292, and `bits` and `entropy_avail` both 17 → 142
(`ENT1-e0`, `ENT1-e1`); `F184-fix2` ran next, on the same boot.

What this does not establish: that a session opened under a replaced password is refused on the
device (R3 is a host result; the bench script logs in and walks no session); two writers at once
(a web SET or PWSET racing `cfgstore` can lose one update; for PWSET the window is its two KDFs,
~1.8 s); `main()` itself, which the host test does not drive; a torn write on the device; the
per-request cost on the device (推: one open, two 4 KiB reads, two CRCs over ~200 bytes, no
measurement); and more than one run on each image.

## 🟢 What the first boot of rlxfw's own userspace DID establish — 2026-09-30 (`R7-8`)

Recorded beside the two defects above so the entry is not read as a failure. 量, one boot,
image `r78a`, recipe `bf182de2`: `init` as PID 1; `httpd` running as user `httpd` and `dnsfwd`
as user `dnsfwd` in `ps`; `dnsfwd` printing `setuid(0) refused (Operation not permitted)`, so the
privilege drop is verified by trying to undo it; `uspacescan` reading **0 forbidden imports from
both sources** on all six programs; the config store written and read back (8,192 bytes, mode
0600) with the A/B alternation visible across two writes; `GET /` and `/api/status` answered 200
with all four security headers, through the chain host → httpd (uid 100, chrooted) → unix socket
→ brokerd (root) → typed op; `dnsfwd` echoing a query id and returning SERVFAIL without hanging;
`ifupd` applying a well-formed lease and refusing two malformed ones by name; and, after the
restart above, a login costing **0.902 s** for the right password and **0.9017 s** for the wrong
one — the same, so the timing does not leak which it was.

## 🟢 CI was red on all four heads pushed on 2026-09-30, from `R8a`'s closing commit on, and `census` ran on none of them — 2026-10-02 (the one hundred and nineteenth segment); closed 2026-10-04 on run `37134992834`

量 2026-10-02, `gh`: runs `36683089537` (`f5641f3d`), `36683808713` (`b52dee0d`),
`36719609297` (`8cb929d2`) and `36719878923` (`5eaeb643`) are all `failure`; the last green run
is `36632061486`, on `380cdf6d`. All four fail the same four steps — in `text`, `bootbytes`,
`test-config-gates` and `audit-bench-log (exit-code gate)`; in `instruments`, `nic15check` —
with `lint` green and `census` `skipped`, zero steps run. The first of those pushes carried six
commits, `3e3e14c1`…`f5641f3d`, so neither commit that brought a fault in (`a008fde6`,
`f353b7b8`) had a run of its own. What each step printed is quoted from run `36719878923`,
read through the jobs API, because `gh run view --log` leaves these steps out without saying
so; all four reproduce at the desk on `5eaeb643` (`desk-sweep --only`: 4 ran, 4 red).
**What follows is the diagnosis as it stood on 2026-10-02; each step was then repaired in a
commit of its own, and the entry closed on the first green run (its last paragraph).**
`SPEC.md` `FW-185`.

**`nic15check`.** It prints
`RESULT: 0 passed, 50 failed (header config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic-tx.h)`:
`K0 does not compile`, `K1`–`K22` `not run: K0 failed`, `M0` reading
`the unmutated copy is RED: no kill below is counted`, and `M1`–`M26` each
`SURVIVED: the mutant does not compile` — 23 `K` and 27 `M`. 讀: `a008fde6` added
`#include <linux/rlxfw-entropy.h>` to `rtl819x-nic-tx.h`, a header that lives in the kernel
tree, and `tools/nic15check.py` compiles exactly that header (its `HEADER`) into a harness with
the host's gcc. The tool prints only the first line of gcc's error, so the log never names the
missing file; 量 at the desk, the header compiled alone stops at
`fatal error: linux/rlxfw-entropy.h: No such file or directory`, and its copy at `380cdf6d`
compiles. 🔴 **The include is there because of a fix.** The hook's first version inserted 22
lines into `rtl819x-nic.c`, moved 68 citations of 35 lines in six files and turned `citecheck`
red (`FW-110`; 量 this segment, `citecheck` on `a008fde6^` plus those 22 lines; the commit
message's 61 and a former 70 do not reproduce). Moving the include into a header no file cites by line kept all 68 and broke
a host harness instead. 🟢 **The mutation suite did what it is for**: `M0` refused to count a
kill off a red baseline, and every mutant reads `SURVIVED`, not killed.

**`test-config-gates`.** One failure on the runner, `FAIL M6 fails A24 expected 1, got 0`
(`RESULT: 63 passed, 1 failed, 2 skipped`); `E5-E6` are skipped there, since the runner has no
extracted rootfs (量, the job log and the `ci-out-text` artifact's `test-config-gates.out`).
量 at the desk, four arms with the prediction written first, and read independently by the
agent repairing this step: `M6` runs a copy
of `mkinitramfs.py` with the flash-write node ban's call removed, from a `mktemp -d` directory,
and `f353b7b8` added a second guard beside that call in `resolve()`, `check_no_h601_dumper`,
which imports `tools/appletcensus.py` from the script's own directory. From the temporary copy
the import fails, the new guard refuses every declaration that has an mtd node — for the
import, not the ban — and `A24`'s three bad nodes stay refused with the ban gone. With `tools/`
on `PYTHONPATH` the same mutant's `A24` reads `accepted: mtdblock0, mtdblock1, mtd0 even`, and
the unmutated copy passes `A24`–`A26`. 讀: `tools/test-mkinitramfs-mutants.py` met the same
import in `R7` — its control `B0` requires the unmutated tool to pass in the temporary tree,
and it copies `appletcensus.py` beside the subject — and this suite's mutants were not given
the same copy. ⚠️ **The handoff's diagnosis was wrong about the case.** The account written at
segment 118's close names `E6`, as did the warning before the push. `E6` is broken too, but
only at the desk with `build/` present — 讀, its `sed` target `$UNIT/bin/busybox` became
`$REPO/build/rlxfw-user/busybox/busybox` in `R7-8` (`f353b7b8`), so the `sed` changes
nothing; in a desk-sweep copy, which has no `build/`, `E5` refuses first and `E6` passes
vacuously (the desk-only case `LOG.md` records on 2026-09-28), and on the runner both are
skipped. **The warning was true at the desk and said nothing about the case CI fails on, `M6`,
which nobody predicted.**

**`audit-bench-log (exit-code gate)`.** `13 hit(s) -- review each before committing`, each a
`private IPv4` match on `10.9.9`, in five files of three captures (量, the runner's log; the desk
reproduces 13): `bench/2026-09-30/R78-iu1.log` 5, `R78-iu1.meta.json` 3, `R78-iu2.log` 3,
`R78-iu4.log` 1, `R78-iu4.meta.json` 1. 讀: they come from the synthetic lease typed into
`ifupd` at the desk on 2026-09-30 (`FW-181`); no DHCP server issued it. Twelve are the typed
values — `10.9.9.9` six times, `10.9.9.1` and `10.9.9.53` three each — in ash's echo of the
sent command, the `sent` records of the `.meta.json` files, `ifupd`'s `bound ok` line and the
output of `cat /run/wan.dns`; one was not typed, `Bcast:10.9.9.255`, the broadcast the kernel
derives from the typed address and mask. None is unexplained (讀, the agent repairing this step,
from the capture bytes; the counts by value re-read here). `f353b7b8` committed the
warning together with the captures, in `tools/spec-check.py`'s C6 allowlist entry for `10.9.9`:
the five files "give audit-bench-log.py 13 hits once committed", and the tool's control `A2`
and `leakscan.py`'s `L3` both probe with `10.9.9.9`.

**`bootbytes`.** `FAIL K2 a normalised constant is NOT declared: {2647: 1, 2746: 1}`, from
`bench/2026-09-30/R78-boot.log` (3,890 bytes) and `R79-boot.log` (3,989 bytes), both committed
in `f353b7b8`; `6 of 7 ok` (量, the runner's log). 讀: the tool declares the normalised
boot-capture lengths it accepts, and a capture of a new image moves that population. Whether
2,647 and 2,746 are the right new constants is 推 until each is derived from its image, as
`88b7262` derived 339 on 2026-09-28.

🔴 **The failure that matters is not any of the four steps.** Three of the four were named
before the push (讀, the account written at segment 118's close), two of them in the reports of
the agents whose work caused them: the image agent wrote that `test-config-gates` `E6` would go
red because the string it `sed`s is gone (true at the desk; CI fails on `M6`, above); the
owner-file agent wrote that `audit-bench-log`
would report 13 `10.9.9` hits, that an allowlist entry there would break its own control `A2`
and `leakscan`'s `L3`, which both probe with `10.9.9.9`, and that those probes had to change
first. Both reports were read and relayed to the owner as worth knowing, and neither was acted
on. `bootbytes` is a class with a written rule: `CLAUDE.md` § Closeout says new captures move
population cases, and `LOG.md` records the same case on 2026-09-28 — `2470d6f`'s captures
turned `bootbytes` `K2` red — as the same mistake. The owner's relaxation of 2026-09-30
(`LOG.md`, segment 118: no desk-sweep, the minimum relevant checks per commit, CI instead)
authorised leaving detection to CI, and CI detected: the first two runs had concluded red by
15:50 and 15:58 (+08:00) that day. It did not authorise ignoring a warning already in hand.
`8cb929d2` and `5eaeb643` were pushed onto that red at 21:09 and 21:11, and neither of segment
118's `LOG.md` entries mentions a CI verdict.

**What this does not establish.** `census` ran on none of the four heads, so every layer it
covers is unmeasured there (`CLAUDE.md` § Closeout: a red `text` job hides `census`); it ran
again first on `8a3b3be3`, in the last paragraph. The four causes looked independent — different
files and mechanisms, `nic15check`'s from `a008fde6` and the other three from `f353b7b8` (讀, git
history) — and the green run is the one reading that shows no repair unmasked another, on that
head. Every 量 above about a mechanism was measured at the desk; the runner was not re-run on
the four old heads. Nothing here concerns the device: no failing step reads the board, and no
capture was changed.

**What changes in practice.** A line in an agent's report that says a step will go red is
handled before the push — repaired, or the push waits — and agents now write it as a line
starting `WILL-RED:`, so it cannot be relayed as a remark. After a commit that adds `bench/`
captures, every suite that reads `bench/` runs before the push, under any relaxation. Read 2026-10-02 from `ci.yml` and the tools, and run on a tree without and with new captures: `bootbytes`, `capdate`, `test-boot-timeline`, `test-reply-size`, `xcheck sweep`, `audit-bench-log (exit-code gate)` (`text`);
`viewdecode`, `mustrun` (`instruments`); and the `cardcheck` and `rbcheck` mutation suites, which scan `bench/` and were not run. `capdate` goes red on a new date directory without its `bench/README.md` row; the others hold numbers new captures move. This entry was to close on the first green
run, and it has.

🟢 **Closed 2026-10-04 on run `37134992834`.** 量 `gh`: on `8a3b3be3`, created 2026-10-03
23:56:00 +08:00, `lint`, `text`, `instruments` and `census` all `success`, `census` finishing at
2026-10-04 00:26:50 +08:00 — the first time it had run since `380cdf6d`. The push carried eleven
commits, `5eaeb643..8a3b3be3`, and each red step was repaired in a commit of its own:
`test-config-gates` in `9013a17a` (its mutants run where an unmutated copy passes, with
`appletcensus.py` copied beside the subject as `test-mkinitramfs-mutants.py`'s `B0` does, and a
mutation that changes nothing is refused); `audit-bench-log (exit-code gate)` in `ae9b2b9e` (the
thirteen hits exempted by file name and exact line in `FILE_EXEMPT`, held by control `A4`, so
`ALLOW` and the `10.9.9.9` probes are untouched); `nic15check` in `d96be8b9` (the harness
supplies the kernel header the include asks for, and a header found nowhere refuses the run by
name); and `bootbytes` in `fe141ba9` (the capture tool's echoed ESCs counted as a term, so
`R7`'s userspace boot is one declared constant, 2,029, rather than two). Before the push, a desk
run on the integration clone ran all 26 selected steps and 25 were green; the 26th,
`test-config-gates`, is red at the desk and only there — two `E5` lines and `E6` need the
gitignored `build/` — with 68 passed and 3 failed in the desk shape and 64 passed, 0 failed and
2 skipped in the runner's, both measured, and the same 68 / 3 at `8a3b3be3`'s base. What the
closure does not establish: anything about a head after `8a3b3be3`; that the desk shape of
`test-config-gates` is green, which it is not until `build/` exists; and anything about the host
tests under `src/`, which no CI step runs (讀), so `FW-184`'s regression test,
`src/brokerd/test_reload.c`, runs only at the desk.

## 🔴 What `v0.6` does not establish — 2026-10-04 (`R7`, `R8a`, `R8`, `R1y`)

`v0.6` carries `R7`, `R1y`, `R8a` and `R8`'s closure by split; each gate's full list is its entry in
`docs/GATE-RESULTS.md`. The ones a reader of this release most needs:

* **Nothing in this release is in flash, so nothing in it persists.** The image boots from RAM after
  a TFTP upload, and the config store is on ramfs and does not outlive a power cycle. No update has
  been written to a slot or booted from one, the anti-rollback counter has never advanced, and no
  power cut has interrupted a write: that is `R8b`, booked behind `R9`, whose vendor column needs the
  vendor firmware still bootable from flash, and behind the owner's dated yes for each write.
* **`R8` closed on a rewritten row.** Its 2026-08-25 wording asked for ten power cuts survived; the
  row was split at the flash boundary, so the closure is a decision about scope, not a result.
* **`R7` is one boot of each program and one question each.** Nothing ran under load — the memory
  high-water mark under concurrent logins, with the limiter removed as its refutation control, is not
  done; no refusal was returned by `brokerd` on the board, a half that rests on the host's 264-cell
  matrix; and two readings of the first boot, the first login reply and the `dnsfwd` reply, were
  printed to a terminal and not saved.
* **No TLS**: every password sent to `httpd` crosses the LAN in clear.
* **Four mounts are unbounded.** `/var`, `/run`, `/tmp` and `/srv/www/run` are mounted as tmpfs, which
  this kernel serves with ramfs, and ramfs ignores `size=`; each can grow until the board is out of
  RAM, and `df` cannot show it.
* **The entropy result is an accounting result, not a strength result**: `RLXFW_ENT_PER_BIT` = 16 is a
  derating and not a measurement, and why the driver's `bits` and `entropy_avail` twice diverged by
  exactly 128 bits is not known (`FW-180`).
* **`rlxboot` is one seating of one build and one image**, and the key it trusts is a development seed
  kept in the tree on purpose, so anyone who reads it can sign a container this build accepts. None of
  it is secure boot — there is no evidence of a key-hash fuse on this part, and the stock loader runs
  first, unverified — and it does not resist an attacker who can already write flash.
* **Whether `rlxboot`'s cache flush is necessary is 推** (`FW-172`): booting showed the composite path
  works for one copy on one die, and the deciding experiment is `CPU-19` ①'s and is not scheduled. The
  rescue payload is not built: its region is reserved and refused, and nothing has run there.
* **`FW-184`'s fix was shown in one run on one image**, and its regression test, like every host test
  under `src/`, runs in no CI step.
* **`R1y`'s landed tree was not swept against its control**: CI on the pushed head stood in, at the
  owner's request.
* **Flash.** No `FLW`, `EW`, `EB`, non-zero `AUTOBURN` or `FLR` was issued in `R7`'s or `R8a`'s rounds
  or in the `FW-184` runs. No flash map was taken in them, so they carry no bracket of their own; the
  `FLR` bracket stays at 1,024 of 4,194,304 bytes, 0.0244 %.

## 🟢 Booted from flash, rlxfw received no Ethernet frame — 2026-10-08 (the one hundred and twenty-seventh segment); closed the same day by `R6c-4`

量 2026-10-08: the `v1.0` candidate `a3a75f8c…` (recipe `6a11de02`), booted from slot B through
`rlxboot` after a watchdog reset and after a cold power-on, brings `rlx0` up with `10.1.1.1` and
counts no frame in or out while the host pings; booted from RAM through the loader's prompt, the
same image answers (`SPEC.md` `NET-171`, `notes/switch-driver.md` § 20). The device's normal boot
is from flash, so **an rlxfw image installed in a slot has no Ethernet**: it is reachable through
the console only, or by booting it from RAM through the loader's TFTP path.

推 The cause: rlxfw's switch setup leaves the VLAN group to the loader
(`notes/switch-driver.md` § 16.8), and the loader configures the switch only when it enters its
prompt (`LDR-46`). **`v1.0` is not tagged with this.** The owner decided on 2026-10-08 to fix it
first, as gate `R6c` (`PROGRESS.md`), and to qualify the rebuilt image on the device again. This
entry closes when an image booted from flash pings both ways after a watchdog reset and after a
cold power-on, and a RAM boot through the prompt still does.

🟢 **Closed 2026-10-08 by `R6c-4` (`bench/2026-10-08c`), on that condition.** `rtl819x-switch` 1.6's
`vlan`, typed by PID 1 between `init` and `start`, writes the loader's VLAN group itself
(`SPEC.md` `NET-173`). 量 Booted from slot A through `rlxboot`, image `9bb2bec7` (sha256
`295d4f6a…86bd`) pinged both ways, 4 of 4, after a watchdog reset and after a cold power-on, and
booted from RAM through the prompt it still did (`notes/switch-driver.md` § 21.6). **`v1.0` ships
`9bb2bec7`** (`FW-256`); `6a11de02`, the image above, stays deaf from flash and is not released.
⚠️ What the close does not establish is `NET-173`'s and `docs/GATE-RESULTS.md` entry 22's: one warm
and one cold flash boot, no load, one port, and which part of the written group is necessary.

## Closed since `v0.2` was tagged

**Kept rather than deleted, so this file can be read against the copy at the `v0.2` tag.**

| | |
|---|---|
| 🟢 **CLOSED 2026-09-01 — the per-gate ledger is public.** *(was: `study/weekly-results.md` is not in the public repository)* | 量: `.gitignore:17` is `study/`, and `git ls-files study/` returns nothing. `CHARTER.md` §110 rule 3 asks for one entry per closed gate in that file, and four are owed (`R2a/b/d`, `R1h`, `R3`, `P4a`). **Owner's ruling 2026-09-01: leaving it ignored is acceptable for now.** `P4b-gate` ③ owns the decision. 🟢 **2026-09-01, `P4b-2`:** the file moved to `docs/GATE-RESULTS.md` — committed, English, one entry per closed gate, and its name now says what its unit is. `study/` stays gitignored; the owner's ruling about the directory and the requirement on this artefact turned out not to be in conflict once the artefact stopped living in that directory. Five entries: `R1-gate`, `R2a/b/d`, `R1h`, `R3`, `P4a`. `S0` and `R0` are deliberately not backfilled, with the reason at the top of that file. |
| 🟢 **CLOSED 2026-09-01 — version → contents has one committed owner.** *(was: two owners disagreeing on six of six shared rows)* | `plan/CHARTER.md` §88 is authoritative and is **gitignored**, so a public reader cannot follow a pointer to it; `PROGRESS.md`'s Release clock restates it and is stale. This file and `CHANGELOG.md` now own the contents of the versions that have actually been released; the map of *future* versions still has the defect. `P4b-gate` ① owns it. 🟢 **2026-09-01, `P4b-1`:** `README.md` § *Which gates make which version* is the owner. `PROGRESS.md`'s Release clock dropped both restated columns and keeps only `Shipped`; the planning material's table dropped its contents column and keeps only its estimates; and `CHANGELOG.md`'s `v0.2` section stopped pointing at a gitignored file. 🔴 **The repair also found that the `Target` column beside `Contents` was a restatement too** — it carries the planning material's own ×1.8 multiplier — and it agreed on only two of six rows while never having been flagged. |
