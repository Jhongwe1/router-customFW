# CORRECTIONS — block 47 (card `PREDICTIONS-B49-block47.md`, frozen in `a9e2501`)

Each entry is written before the cell it declares runs. The card is not edited.

## 1. `RB-02-R`'s `until` gate (2026-09-26 13:38:04), and the declared cell `X-RT1`

**What happened (量).** `I-RB` stopped at `gate:until:RB-02-R` (`--seconds 10.0 elapsed`).
`RB-01-C` had read `rbcheck verdict EQUAL`; `RB-02-P` exited 1 (a declared reading: 2
transmitted, 0 received). `RB-02-R.log` (4,811 B) holds the whole page through `ww 84 …`, with
`version rtl819x-nic 1.5`, `nd_up 1`, `n_recov_arm 0`, `n_recov_fire 0` and `v15 … txq 10`
(8 in `RB-02-S`), and no loader or kernel text. After the page the recovery's four marks
(`RLXFW-N-ENGOFF`, `N-ARM`, `N-ARMR`, `N-ENGON`) arrived once, interleaved into the prompt, so
the `until` pattern's `ww …\r\n# ` never occurred (`FW-47`'s interleave).

**What the card decides (§ 6, "A board bracket's gate … with no loader text").** `/dev/ttyUSB0`
is checked (present, 13:37) and the read is typed again as `X-RT1`; if it passes, it stands in
and the invocation continues `--from` the next cell, `RB-02-C`.

**The declared cell** — `RB-02-R`'s own command under the new name:

```
CAP --out bench/2026-09-26/X-RT1 --send 'cat /proc/rtl819x-nic /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
```

It passes if it ends on the prompt with `version rtl819x-nic 1.5` and no loader text. Then
`I-RB` continues `--from RB-02-C`, whose `rbcheck` grades `RB-02-R`'s page (read before the
recovery, as its `n_recov_fire 0` shows) against `RB-02-S`, as written. If `X-RT1` returns
nothing, garbage or never ends on the prompt, the owner powers off (§ 6).

**Alternatives rejected.** Continuing `--from RB-02-C` with no re-read: § 6 requires the board
to be shown answering first. Powering off now: the read returned a whole page and no loader
text, which is § 6's re-read branch, not its power-off branch. Treating the recovery as a
reading here: that is `RB-02-C`'s and `rbcheck`'s to classify (its control reads
`n_recov_fire` in the graded page), not this entry's.

**Not established by this entry.** Why the recovery fired after the page rather than before;
the card's `RB-02` design holds the ring with `txstall on` and the recovery's timer runs while
`rlx0` is up — that is a reading for the record, not decided here.
