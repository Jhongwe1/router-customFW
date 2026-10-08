# CORRECTIONS to R6C-4-CARD.md -- 2026-10-08, the 129th segment

Each entry is written before what it changes is executed.

## C1 (about 20:55, after `R16`): the board's `ping` does not stop by itself

量 `R14`: `ping 10.1.1.2`, typed without `-c` because the card followed `notes/rootfs-census.md`'s
2026-09-06 finding ("this image's `ping` ignores `-c` and always sends exactly four packets"),
printed a reply for every sequence number from 0 to at least 34 and was still running when its
35 s window closed. `R15` and `R16` were typed while it held the console: their captures hold only
its reply lines, and they stopped on `--seconds`, not `--idle`. 讀 The census finding was measured
on the vendor's busybox (273,332 bytes); the busybox in this image is rlxfw's own build
(`prebuilt:busybox/busybox`, 447,684 bytes, pinned to f184a, in the build manifest of
`$FWRE_WORK/rebuild/s128/p/run/r6c/`), and its `ping` runs until it is interrupted. With `-c 4` it
stopped at four this morning (`bench/2026-10-08b/A14`); whether it honours other counts is not
measured here.

Executed instead, as declared off-card cells:

* `X-R14i`: a `--send` of one ETX byte (Ctrl-C) with `--idle 3 --seconds 20`. It interrupts the
  `ping`, whose statistics line closes `R14`'s count; the line discipline flushes the queued
  `R15`/`R16` input on the interrupt.
* `X-R15`, `X-R16`: `R15`'s and `R16`'s commands, typed again once the prompt is back.
* `W13` and `C13` are not run. In their place `X-W13` and `X-C13` run the same HOST line with
  `ping -c 4 10.1.1.2` in place of `ping 10.1.1.2` (R6C-A's `H14` form) and write `X-W14`/`X-C14`;
  `W15`/`W16` and `C15`/`C16` run as written after them.

Rejected: running `R13`, `R15` and `R16` again under their own names (`cardrun` refuses a cell
whose log exists, and those logs are the record of what happened); leaving the `ping` running into
phase 2 (`I01`'s `busybox reboot -f` would be typed behind it and not run); `W13`/`C13` as written
followed by an interrupt (each would hold the console for 35 s and need the same repair).

## C2 (the same time): how `D1` reads `R02` and `R14`

* `R02` failed on `A4` alone (`neither '<RealTek>' nor a shell prompt`): the boot capture's last
  line is `dnsfwd`'s, printed after the prompt (`FW-252`). The card routes that case to `X-R02p`,
  which read `37.53 31.98` and the prompt. `D1`'s "`R02` PASS" is read as that route, as V10's
  `V02` was.
* `R14`'s "`4 packets received`" cannot be read as written, because the `ping` was not bounded.
  `D1` reads instead: every request in `R14` and `X-R14i` answered (the statistics line), and the
  host's `tcpdump` in `R13` showing each request with its reply.

## C3 (after `C17`): the closing count, written here and not on the card

The card's last section asks for the count after the cells; it is written here because any edit
moves the card's mtime past every capture, and `check-predictions` compares the two.

量 Power actions 2, both the owner's, each on the handshake: OFF before `PF2` (the owner's "關好了";
`PF2` 0 bytes at 21:57:04), ON inside `C01`'s window (opened 21:57:13, told "最晚 22:01:13"; the first
byte at 13.6 s, about 21:57:27). Flash-writing commands 1: `I10`, `install slotA` under the owner's
yes of 2026-10-08. `FLW` / `EW` / `EB` / non-zero `AUTOBURN` 0; `FLR` 0. The loader's `AUTOBURN` word
read back `00000000` before each upload (`R02`, `I02`: `A0b`). rlxfw's `n_writes`: `I11` 4,625
(`inst_n_se` 288 + `inst_n_pp` 4,337, `inst_ops_planned` 4,625), `W17` 0 and `C17` 0. The bracket's
reach: `I10`'s read-back of slot A's 1,179,648 bytes (`inst_cmp_bytes` 1179648, `inst_cmp_diff` 0,
`inst_cmp_first` -1), and `rlxboot`'s digest of slot A's 1,110,176 bytes and slot B's 1,109,152 on
both flash boots (`W01`, `C01`: `RLXBOOT-DIGEST ok` for each). What it cannot see: two writes that
cancel; every byte outside slot A and the two containers; no region compared with the 2026-08-16
dump. `flashwin scan --sweep bench/2026-10-08c` with that dump: 208 files, 113 probes, CLEAN.

`I10`'s capture ends inside its last line (`RLXFW-SI-END OK rc=0 c`): `--until` stops reading
0-50 ms after the match. Its result is read from `I11`'s fields, as the card's stop list allows.
