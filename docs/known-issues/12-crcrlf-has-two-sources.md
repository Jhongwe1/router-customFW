Part of [the known-issues index](../KNOWN-ISSUES.md): entry 12 of 19, moved here verbatim from that file on 2026-10-17.

## 🔴 `\r\r\n` has two sources and only one of them is a wrap

量 2026-09-08 over all 762 committed captures (`FW-49`). busybox ash's line
editor wraps the **echo** of a typed line at the terminal width: 33 captures,
one wrap each, all with `len(sent)` in 80..121. The other 33 occurrences sit
**after** the echo and are the loader's ordinary `\r` + `\r\n` on a 10-character
command. **A scan that counts `\r\r\n` sees 66 and conflates two mechanisms
whose counts happen to be equal.**

Output is not wrapped -- an 88-character `/proc/version` line arrives whole in
five captures, and two loader commands of 119 and 127 characters do not wrap.
🔴 The consequence is a band: `console-capture.py` refuses a `--send` only at
**128** characters, so **79..127 is accepted and wrapped**, and in that band
both "the first newline ends the command" and "grep for the whole command"
fail.

🔄 **2026-09-16 (`R1z-2`), and the number this row was proudest of is no longer
the bracket.** The 2026-09-08 sweep read 762 committed captures; the corpus is
now **1,273**, of which 1,232 carry a `sent` and **1,194** classify (38
are `FW-47`'s echo-interleaving family). The band that was EMPTY on 2026-09-08 --
71..79 characters, the emptiness that made the threshold 推 rather than 量 --
now holds **40 captures and not one of them wraps**: fourteen at 71, four at
72, one at 75, one at 77, and **twenty at 78**, the last being six distinct
commands across two seatings (`bench/2026-09-10`, `bench/2026-09-14c`). The
shortest wrapped command is still **80** (`bench/2026-09-06b/K1-N`), and the
only two unwrapped captures above 80 are the loader's 119- and 127-character
`EW`s -- this row's own negative control firing a second time. The whole
classified corpus, by length: `<= 70` **1,091** captures and **0** wraps; the
band **40** and **0**; `>= 80` **63**, of which **61** wrap. 🔄 2026-09-26: the loader's two are no longer the only unwrapped sends above 80 — five shell sends of 2026-09-21 are too (below).

🔴🔴 **FOUR SWEEPS OF ONE CORPUS IN ONE HOUR. ONE WAS RIGHT, AND THE THREE
WRONG ONES DISAGREE WITH EACH OTHER.** This row's threshold was measured four
times on 2026-09-16, by four readers working separately from the same 1,273
committed captures.

* A throwaway script reading each log with `io.open(p, encoding='utf-8')` —
  universal newlines — saw **zero** wraps at every length, because the
  translation turns `\r\r\n` into `\n\n`. It reported an empty corpus.
* 🔴 **Two independent readers counted `\r\r\n` ANYWHERE IN THE LOG, both got
  20 of 20 at length 78, and both concluded the threshold was pinned there.**
  One of the two wrote down, in the same report, the objection that breaks it:
  *"`FW-49` says `\r\r\n` has two sources and I did not localise the bytes to
  the echo."* It published the conclusion anyway.
* `capfield wrapcensus`, using `echo_end` on a byte-read log, says **0 of 20**.

量, on `bench/2026-09-10/C11-L1`: `sent` is 78 characters and `echo_end` is
**78** — exactly, so nothing was inserted — and the single `\r\r\n` sits at
offset 78, *immediately after* the echo:
`…brightness ; cat /proc/rtl819x-gpio\r\r\nversion rtl819x-gpi`. Across all
twenty at that length: **0 inside the echo, 20 anywhere in the log.** The
contrast case is `bench/2026-09-03/TM-6` — `sent` 97, `echo_end` **100**, the
three extra characters being the wrap itself, splitting a command mid-token:
`…sleep 30 ; cat \r\r\n/proc/rtl819x-timer`.

🔴 **That is the conflation THIS ROW ALREADY NAMES**, reproduced one layer
down by two readers who had both read it: *a scan that counts `\r\r\n` sees 66
and conflates two mechanisms whose counts happen to be equal*. It is
attractive precisely because **20 equals 20** — the corpus returns the same
number under the wrong method, so the wrong method returns a plausible answer
and no arithmetic complains. One reader said nothing wraps and two said
everything at 78 does; the committed tool, which reads bytes and asks WHERE
the `\r\r\n` sits, is right, and it is right because `echo_end` was written
and tested for this exact question before any of the four sweeps ran.

🔴 **Two sweeps, two classified counts, and the committed tool is the one
that is right.** The first draft of this measurement walked the echo by
SKIPPING any character that did not match `sent`, so it could assemble the
command out of a much longer body and classified **1,218**;
`capfield.echo_end` steps over CR and LF only and returns nothing on a
mismatch, so it classifies **1,194** and declines 38. The band agrees in
both (40, none wrapped) and the difference is entirely at `>= 80`, where
the loose matcher added three captures it should have declined. 🟢 The
sweep now lives in `capfield wrapcensus`, beside `echo_end`, so the wrap
rule has one definition rather than two that can drift; its `K10` is the
positive control (>= 33 wraps above 80, the number this row records),
`K11` the negative (zero below 70) and `K12` the reconciliation, and it
prints the one length inside the bracket that has no capture: **79**.

So the bracket narrows from `70 < T <= 80` to **`78 < T <= 80`**: eight of its
ten values closed with data committed on 2026-09-10 and 2026-09-14 that nothing
had read. 🔴 **It is still not pinned.** The corpus holds **zero** captures at
exactly 79, so `T` is 79 or 80, and the 推 mechanism value -- 78 usable columns
beside a two-column `# ` prompt -- predicts **79**. One 79-character command at
a shell decides it, on any seating, and it costs no power cycle of its own. 🔄 **Pinned 2026-09-25 by block 46: `T` = 79** (below, *What block 46 did NOT establish*).

🔴 **Two independent triage routes reported the band's 40 captures correctly
and both concluded the experiment was already on disk.** Neither classified
whether those captures WRAP. They do not, which is why the threshold moved and
did not pin. The count was right and the conclusion was wrong in both, from the
same missing step.

🔴 **And the first instrument written to measure it returned ZERO wraps at
every length**, including the 33 this row records above 80.
`io.open(path, encoding='utf-8')` is universal-newlines: it turns the `\r\r\n`
being searched for into `\n\n`. The instrument destroyed its own subject and
reported an empty corpus. What caught it was this row's own 33 used as a
positive control; with `newline=''` the same sweep sees **64 of 66**.
