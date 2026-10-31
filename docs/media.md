# Media

rlxfw on video: one bench session, filmed live on 2026-10-24 while `tools/cardrun.py` ran bench
card [`P5E6-c`](../bench/2026-10-24/P5E6-c-CARD.md), in two takes the author cut and uploaded.
Nothing in them is replayed. The image on screen is `v1.0`'s: `T`, version 5, booted from slot A
through the flash `rlxboot`, and `mainline-9bb2bec7.img` booted from RAM. `v1.1` is not on video.

| cut | link | filmed in |
|---|---|---|
| ① one minute, no narration | <https://www.youtube.com/watch?v=WOBuOcHn2t0> (`P5e-6-v1`) | take 1 |
| ② the longer cut | <https://www.youtube.com/watch?v=a2rwQovBzcw> (`P5e-6-v2`) | take 2 |

The author gave the links in this order on 2026-10-30; that ① is take 1 and ② take 2 is read
from that order and from the titles, which YouTube's oEmbed endpoint returned the same day.

## What each take shows, and the capture behind it

Every capture is in [`bench/2026-10-24/`](../bench/2026-10-24/), unedited. `RLXFW-ID0` is compared
with the build's digest by a tool, never read off the screen.

| take | what the terminal shows | captures | `RLXFW-ID0`, and the tool that compared it |
|---|---|---|---|
| 1 | the pre-flight with the board off | `Vc00` | — |
| 1 | power on; `rlxboot` `127a71cf` checks both slots and boots `T` from slot A | `Vc01` | `9BB2BEC7` against the manifest's `9bb2bec7`: `bootslot judge`, `check id pass` (`Vc02`) |
| 1 | `rlx0` both ways, 4 of 4 each; `httpd` answers `HTTP 200`, 3,850 bytes | `Vc03`–`Vc05` | the boot of `Vc01` |
| 2a | a reboot to the loader's prompt; `mainline-9bb2bec7.img` uploaded to RAM and booted; the shell alive | `Vc10`, `Vc11`, `Vc13` | `9bb2bec7` against the build's: `looprun` `A3`, `ok` (`Vc11`) |
| 2b | `R8a`'s `rlxboot` `6395889d` and a container with one payload bit flipped, both in RAM; `RLXBOOT-DIGEST bad`, `RLXBOOT-REFUSE digest`, the reset, and the flash `rlxboot` booting `T` from slot A | `Vc20`–`Vc31` | `9BB2BEC7` against `9bb2bec7`: `bootslot judge`, `check id pass` (`Vc33`, on the capture's flash half) |
| 2c | `rlx0` both ways, 4 of 4 each; `httpd` as uid 100 and `dnsfwd` as uid 101; `httpd`'s root `/srv/www`; `HTTP 200`; the SPI driver's `n_writes 0` | `Vc40`–`Vc46` | the boot of `Vc31` |

Zero flash-writing commands were issued during the session (the card's *What it may do*).

## What this page does not establish

- **Which shots each cut keeps.** The cuts are the author's edit of the two takes, and no tool
  compared a cut with its take or with the captures.
- **That the terminal text is at least 18 pt**, which `P5e-6`'s DoD asks for: not measured, and
  the author was not sure (2026-10-30).
- **The replay** of `R8b`'s power cut during an update that ② was to carry, captioned as a
  replay, and the reel definition that would regenerate it from a clean clone: not recorded.
- **A power cut filmed live** (`P5e-6` ③): not filmed.
- **The cuts' lengths**: not measured.
- That the takes show anything of `v1.1`: they show `v1.0`'s image, filmed before `v1.1` existed.
