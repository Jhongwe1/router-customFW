# Known issues

**What this repository does not establish.**
`plan/CHARTER.md` §110 rule 2 asks for a known-issues list beside every release.
This is that list, and it is written to the same standard as everything else
here: each entry names what is *not* true, what was measured instead, and which
gate changes it. Nothing below is a plan; the plan is `PROGRESS.md`'s gate board.

⚠️ **This file on `main` is the CURRENT list, not `v1.0`'s.** A release's list is the copy
at that release's tag, which is frozen; this one keeps moving. It is an index: each open
entry is a page of its own under `docs/known-issues/`, and so is each release's list of what
it does not establish (`docs/known-issues/vX.Y.md`). Entries that have since closed, and the
`v0.5` and `v0.6` lists, are in `docs/history/known-issues-closed.md`; what single segments
did not establish is in `docs/history/known-issues-segment-limits.md`.

Marked the same way as the rest of the repository: **量** measured on the device
· **讀** read out of code, a dump or a document · **推** inferred, pending a
measurement.

---

## What `v1.0` does not establish

One line per limit; the full text, and the image it names by sha256, is
[`docs/known-issues/v1.0.md`](known-issues/v1.0.md).

- Every reading of this image is one unit, one loader build, and one boot per path. ([full text](known-issues/v1.0.md))
- The image opens a root shell on the serial console with no login, so anyone with the serial header has root. ([full text](known-issues/v1.0.md))
- `RLXFW-ID0` names the kernel recipe, not the image. ([full text](known-issues/v1.0.md))
- The device cannot update itself, and nothing the running firmware writes persists. ([full text](known-issues/v1.0.md))
- Rollback is not refused from flash. ([full text](known-issues/v1.0.md))
- Power cuts were survived at ten points of paced writes, and nowhere else. ([full text](known-issues/v1.0.md))
- Booted from flash, the Ethernet rests on two boots and on a write set shown sufficient, not necessary. ([full text](known-issues/v1.0.md))
- rlxfw has no WAN: switch ports 0–5, the jack labelled WAN among them, are in one VLAN. ([full text](known-issues/v1.0.md))
- None of it is secure boot. ([full text](known-issues/v1.0.md))
- Carried from `v0.6`, unchanged: no TLS, four unbounded ramfs mounts, an entropy result that is accounting and not strength, and an `rlxboot` cache flush not shown necessary. ([full text](known-issues/v1.0.md))
- `R9`'s table does not say rlxfw is more secure. ([full text](known-issues/v1.0.md))
- The bring-up report's power tree is a desk reconstruction, and no interrupt latency was taken by logic analyser. ([full text](known-issues/v1.0.md))
- The corresponding source does not rebuild the image bit for bit, and two parts of it are missing. ([full text](known-issues/v1.0.md))
- `iperf3` rebuilds to the shipped bytes only at the path it was first built at. ([full text](known-issues/v1.0.md))
- The tag is unsigned. ([full text](known-issues/v1.0.md))
- Flash: three seatings wrote slots through the armed image's install path, each under the owner's dated yes; the `FLR` bracket stays at 1,024 of 4,194,304 bytes. ([full text](known-issues/v1.0.md))

## Open entries

One line per entry, in the order the entries stood in this file; *since* is the date in the
entry's heading, or else the day its heading entered this file.

| # | Entry | Area | Since | Page |
|---|---|---|---|---|
| 01 | ~~The firmware does not exist~~ — struck at `v1.0` (2026-10-09); each row below says what is still true | firmware | 2026-09-01 | [01-the-firmware-does-not-exist.md](known-issues/01-the-firmware-does-not-exist.md) |
| 02 | Every per-`-march` claim here is about ONE toolchain, and until 2026-09-13 none of them said which | build | 2026-09-13 | [02-march-claims-name-one-toolchain.md](known-issues/02-march-claims-name-one-toolchain.md) |
| 03 | The flash claim, and why it is not "zero bytes written" | firmware | 2026-09-01 | [03-the-flash-claim.md](known-issues/03-the-flash-claim.md) |
| 04 | The reproducible build closes at one machine | build | 2026-09-01 | [04-reproducible-build-one-machine.md](known-issues/04-reproducible-build-one-machine.md) |
| 05 | Gates that closed with a defect recorded | record-and-tools | 2026-09-01 | [05-gates-closed-with-a-defect.md](known-issues/05-gates-closed-with-a-defect.md) |
| 06 | The artefacts | build | 2026-09-01 | [06-the-artefacts.md](known-issues/06-the-artefacts.md) |
| 07 | The repository's own record | record-and-tools | 2026-09-01 | [07-the-repositorys-own-record.md](known-issues/07-the-repositorys-own-record.md) |
| 08 | The image contains a flash-write path, and it is not mine | firmware | 2026-09-07 | [08-a-flash-write-path-not-mine.md](known-issues/08-a-flash-write-path-not-mine.md) |
| 09 | What has never been measured at all | firmware | 2026-09-01 | [09-never-measured.md](known-issues/09-never-measured.md) |
| 10 | The device cannot check the driver's own arithmetic, and a mark it prints can be invisible to a `grep` | firmware | 2026-09-08 | [10-the-device-cannot-check-the-arithmetic.md](known-issues/10-the-device-cannot-check-the-arithmetic.md) |
| 11 | A carriage return is invisible, and so is the tool you would use to see it | record-and-tools | 2026-09-08 | [11-a-carriage-return-is-invisible.md](known-issues/11-a-carriage-return-is-invisible.md) |
| 12 | `\r\r\n` has two sources and only one of them is a wrap | record-and-tools | 2026-09-08 | [12-crcrlf-has-two-sources.md](known-issues/12-crcrlf-has-two-sources.md) |
| 13 | A one-word correction that cannot be made without invalidating evidence | record-and-tools | 2026-09-16 | [13-a-one-word-correction.md](known-issues/13-a-one-word-correction.md) |
| 14 | Two bench directories are named for a day none of their captures happened on | record-and-tools | 2026-09-08 | [14-two-bench-directories-misnamed.md](known-issues/14-two-bench-directories-misnamed.md) |
| 15 | The check that asks whether a committed file holds forbidden flash bytes cannot run in CI, and has been invoked wrong | record-and-tools | 2026-09-15 | [15-flashwin-scan-cannot-run-in-ci.md](known-issues/15-flashwin-scan-cannot-run-in-ci.md) |
| 16 | A closeout gate run on a dirty tree has its own findings switched off | record-and-tools | 2026-09-16 | [16-a-closeout-gate-on-a-dirty-tree.md](known-issues/16-a-closeout-gate-on-a-dirty-tree.md) |
| 17 | 69 citations into `rtl819x-nic.c` rotted in one segment, and they are DECLARED rather than repaired | record-and-tools | 2026-09-22 | [17-69-citations-into-rtl819x-nic.md](known-issues/17-69-citations-into-rtl819x-nic.md) |
| 18 | A frozen card declares a day none of its captures happened on | record-and-tools | 2026-09-23 | [18-a-frozen-card-declares-a-day.md](known-issues/18-a-frozen-card-declares-a-day.md) |
| 19 | The mainline image has no vendor Ethernet driver, so `R9`'s controlled variable holds only in `quiet-swcore` | firmware | 2026-09-28 | [19-no-vendor-ethernet-driver.md](known-issues/19-no-vendor-ethernet-driver.md) |

## Records

- [What single segments and seatings did not establish](history/known-issues-segment-limits.md):
  the eighteen dated lists of 2026-09-16 to 2026-09-25, moved there verbatim on 2026-10-10.
- [Closed entries, and the `v0.5` and `v0.6` lists](history/known-issues-closed.md), moved
  verbatim on 2026-10-09.
