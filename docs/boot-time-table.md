# `P2`'s table — boot time, network up and throughput, the vendor firmware beside rlxfw

`P2`'s deliverable (`plan/router-rebuild-plan.md`, `P2`): the boot cut into segments from the
loader's first byte to a usable device, both firmwares, one script; every number with its method
and its repetition count; the feature table beside it; throughput, sizes and memory. This file owns
the table and its method. The findings behind the numbers are owned elsewhere — seating A's readings
by `notes/boot-time.md` § 7, seating B's by § 8, the `rlx0` driver's by `notes/nic-driver.md`
§§ 19–20 — and `SPEC.md` `CLK-48` indexes this file. Written by `P2-5`, 2026-09-25 (the 111th
segment), at the desk, over the committed captures of two seatings on two calendar days: seating A,
`bench/2026-09-23/` (`P2-3`, card `PREDICTIONS-B44-block42.md`), and seating B, `bench/2026-09-25/`
(`P2-4`, card `PREDICTIONS-B46-block44.md`). No capture was taken for this file.

**`D3` holds under its closing rule** (§ 10, `CLK-48`). Seating A published 294 numbers. A list
frozen from seating A's files before any seating-B value of them was read
(`docs/boot-time-d3-list.tsv`, `76deef8`) calls 140 of them stable; seating B reproduced 134 of the
140 within ±10 % on both columns, and none of the six it did not is a row of the segmented table
or `D7`'s Δ. The 69 stable rows on which a miss would have kept `P2` open lie within |a| ≤ 6.712 %
and |b| ≤ 5.229 %. `D2`, the identical-code control, held inside each seating (`CLK-34`,
`CLK-45`).

## 1. How to read the tables

**The columns.** *A raw* is seating A as stamped, on the host's `CLOCK_MONOTONIC`, which two time
daemons slowed to r = 0.9726–0.9861 of true time from about 15:49 on 2026-09-23 (`CLK-35`,
`CLK-38`). *A corrected* divides each capture by r at that moment — a loader catch by its own
`r_best`, any other capture by the median of the K, N and W references over the five-minute window
it began in (card B § 0 ③; `notes/boot-time.md` §§ 7.1–7.2) — and applies to what the board times
(card B § 3.0). A host-timer, clock-free or realtime quantity is carried at face value (`= raw`);
a mixed one is split, its board part corrected; where the frozen list carries only the corrected
median, the cell says `(median)`. *B (RAW)* is seating B as stamped, on `CLOCK_MONOTONIC_RAW` for
the console and the host probe alike, which the host does not slew (§ 9.2). A cell is the median
with its range, min…max; seconds unless the row says otherwise; *n A/B* counts the values in each
seating.

**The ratios.** (a) = B ÷ A raw − 1; (b) = B ÷ A corrected − 1; (c) = (B ÷ seating B's warm
`loader.booting` median) ÷ (A raw ÷ seating A's raw warm `loader.booting` median) − 1, the
normalisation `CLK-32` registered before seating A; the two medians are 0.356060 s and 0.347425 s
(n 13 each). (a) carries seating A's slow clock by
construction: +1.41 % on press 1, +2.30 % on `V1`–`V3` and `M1`, +2.39 % on `P2`, +2.53 % on
`V4`–`V7` and `M2`, +2.77 % on `P3` (card B § 3.10). `signed` marks a difference or an offset
whose values straddle 0, where a ratio means nothing.

**The verdict** (`D3` column). `hit`: (a) and (b) both within ±10 %, inclusive and not widened;
`MISS` otherwise (card B § 3.10). `n.s.`: the frozen list calls the number not stable — scored,
published, deciding nothing (§ 9.3); `inside` and `outside` say where it fell. `exact`: a
clock-free prediction scored exactly (card B § 3.2). `first reading`: no seating-A value exists by
seating B's rule. **LB** marks the 69 rows on which a miss would have kept `P2` open (the closing
rule's (2)).

**The classes** are the tool's own (`tools/boot-timeline.py`, `SEGMENTS`; `notes/boot-time.md`
§ 1). *Identical*: the loader's code, the same bytes in both columns — `D2`'s control.
*Comparable*: the same kind of work by different builds — rtkload's decompression (image sizes in
§ 8) and the kernel between drivers both kernels carry. *Not comparable*: userspace, and rlxfw's
two instrumented segments; there each vendor daemon's own start and readiness stand in (§ 5.3).

**What a cell is not.** A console time is the `FW-35` arrival of a landmark's first byte, an upper
bound: 量 single stamps in seating B are provably late by up to 13.5 ms, and `J`'s — the tool's
`jump` landmark, `---Jump to address=` or `Jump to image start=` — by at least 0.9–6.8 ms in all 23
typed-`J` captures (1.1–6.4 ms in seating A's 23), so an interval from `J` reads short by `J`'s
lateness less its far end's, the same way in both seatings (`CLK-44`). A host
time is a read by `tools/hostprobe.py`. Four decimals here; six in `docs/boot-time-d3-score.tsv`,
which carries every row's medians, (a), (b), (c) and verdict (§ 9.4).

## 2. Cold boots

A cold boot follows a power press (`C-8`'s line; `notes/boot-time.md` § 2). The populations are
seating A's in both seatings (量, the timing job's class check): the loader's twelve cold catches;
the vendor's `V1`–`V3` and `M1`; rlxfw quiet `P2Q-r01` and `P3Q-r01`; rlxfw loud `P1L-r01`.

| segment | class | firmware | n A/B | A raw | A corrected | B (RAW) | (a) | (b) | (c) | `D3` | LB |
|---|---|---|---:|---|---|---|---:|---:|---:|---|---|
| `loader.booting` | identical | loader, both | 12/12 | 0.3479 (0.3439…0.3557) | 0.3560 (0.3526…0.3575) | 0.3559 (0.3515…0.3564) | +2.28 % | −0.03 % | −0.20 % | hit | yes |
| `loader.banner` | identical | loader, both | 12/12 | 0.5727 (0.5664…0.5861) | 0.5861 (0.5807…0.5883) | 0.5860 (0.5815…0.5865) | +2.32 % | −0.03 % | −0.16 % | hit | yes |
| `loader.esc` | identical | loader, both | 1/1 | 5.1219 | 5.2376 | 5.2388 | +2.28 % | +0.02 % | −0.20 % | n.s., inside |  |
| `rtkload.decompress` | comparable | vendor | 4/4 | 1.0371 (1.0367…1.0380) | 1.0609 (1.0599…1.0631) | 1.0601 (1.0600…1.0603) | +2.22 % | −0.08 % | −0.25 % | hit | yes |
|  |  | rlxfw quiet | 2/2 | 1.1885 (1.1879…1.1891) | 1.2192 (1.2175…1.2209) | 1.2180 (1.2180…1.2180) | +2.48 % | −0.10 % | −0.01 % | hit | yes |
|  |  | rlxfw loud | 1/1 | 1.2313 | 1.2486 | 1.2481 | +1.37 % | −0.04 % | −1.09 % | hit | yes |
| `rtkload.total` | comparable | vendor | 4/4 | 1.0512 (1.0487…1.0547) | 1.0757 (1.0721…1.0797) | 1.0736 (1.0708…1.0782) | +2.13 % | −0.19 % | −0.35 % | hit | yes |
|  |  | rlxfw quiet | 2/2 | 1.2018 (1.2013…1.2024) | 1.2329 (1.2311…1.2346) | 1.2312 (1.2291…1.2333) | +2.44 % | −0.14 % | −0.04 % | hit | yes |
|  |  | rlxfw loud | 1/1 | 1.2469 | 1.2645 | 1.2606 | +1.10 % | −0.30 % | −1.35 % | hit | yes |
| `kernel.early` | comparable | vendor | 4/4 | 0.6519 (0.6515…0.6525) | 0.6670 (0.6660…0.6683) | 0.6669 (0.6664…0.6671) | +2.30 % | −0.00 % | −0.18 % | hit | yes |
|  |  | rlxfw quiet | 2/2 | 0.8025 (0.8021…0.8030) | 0.8232 (0.8221…0.8244) | 0.8220 (0.8220…0.8220) | +2.43 % | −0.15 % | −0.05 % | hit | yes |
|  |  | rlxfw loud | 1/1 | 1.5058 | 1.5270 | 1.5239 | +1.20 % | −0.20 % | −1.25 % | hit | yes |
| `kernel.wlan` | comparable | vendor | 4/4 | 4.5247 (4.5221…4.5296) | 4.6301 (4.6229…4.6367) | 4.6232 (4.6228…4.6236) | +2.18 % | −0.15 % | −0.30 % | hit | yes |
|  |  | rlxfw quiet | 2/2 | 4.4853 (4.4822…4.4884) | 4.6010 (4.5955…4.6065) | 4.5974 (4.5971…4.5976) | +2.50 % | −0.08 % | +0.01 % | hit | yes |
|  |  | rlxfw loud | 1/1 | 5.1410 | 5.2135 | 5.2080 | +1.30 % | −0.11 % | −1.15 % | hit | yes |
| `kernel.nic` | comparable | vendor | 4/4 | 0.8244 (0.8155…0.8329) | 0.8434 (0.8336…0.8530) | 0.8341 (0.8340…0.8344) | +1.18 % | −1.10 % | −1.28 % | hit | yes |
|  |  | rlxfw quiet | 2/2 | 0.8400 (0.8394…0.8406) | 0.8616 (0.8606…0.8627) | 0.8603 (0.8602…0.8605) | +2.43 % | −0.15 % | −0.06 % | hit | yes |
|  |  | rlxfw loud | 1/1 | 1.2245 | 1.2418 | 1.2409 | +1.34 % | −0.07 % | −1.12 % | hit | yes |
| `kernel.late` | comparable | vendor | 4/4 | 0.9622 (0.9515…0.9754) | 0.9843 (0.9728…0.9989) | 0.9737 (0.9734…0.9739) | +1.20 % | −1.07 % | −1.25 % | hit | yes |
|  |  | rlxfw quiet | 2/2 | 3.0897 (3.0871…3.0923) | 3.1694 (3.1661…3.1728) | 3.1658 (3.1655…3.1661) | +2.46 % | −0.12 % | −0.02 % | hit | yes |
|  |  | rlxfw loud | 1/1 | 3.1401 | 3.1843 | 3.1829 | +1.36 % | −0.05 % | −1.10 % | hit | yes |
| `kernel.total` | comparable | vendor | 4/4 | 6.9636 (6.9423…6.9879) | 7.1237 (7.0975…7.1568) | 7.0980 (7.0973…7.0981) | +1.93 % | −0.36 % | −0.54 % | hit | yes |
|  |  | rlxfw quiet | 2/2 | 9.2175 (9.2108…9.2242) | 9.4553 (9.4443…9.4664) | 9.4455 (9.4451…9.4459) | +2.47 % | −0.10 % | −0.01 % | hit | yes |
|  |  | rlxfw loud | 1/1 | 11.0114 | 11.1666 | 11.1556 | +1.31 % | −0.10 % | −1.15 % | hit | yes |
| `rlxfw.setup` | not comparable | rlxfw quiet | 2/2 | 0.0457 (0.0456…0.0458) | 0.0469 (0.0469…0.0469) | 0.0474 (0.0474…0.0474) | +3.58 % | +0.98 % | +1.07 % | hit | yes |
|  |  | rlxfw loud | 1/1 | 0.2752 | 0.2791 | 0.2937 | +6.71 % | +5.23 % | +4.12 % | hit | yes |
| `rlxfw.initpost` | not comparable | rlxfw quiet | 2/2 | 0.0115 (0.0115…0.0116) | 0.0118 (0.0118…0.0119) | 0.0119 (0.0116…0.0122) | +3.28 % | +0.69 % | +0.78 % | n.s., inside |  |
|  |  | rlxfw loud | 1/1 | 0.0120 | 0.0122 | 0.0117 | −2.88 % | −4.23 % | −5.24 % | n.s., inside |  |
| `user.ready` | not comparable | vendor | 4/4 | 18.1773 (18.0943…18.3171) | 18.6119 (18.4975…18.7272) | 18.6849 (18.6562…18.8028) | +2.79 % | +0.39 % | +0.30 % | hit | yes |
|  |  | rlxfw quiet | 2/2 | 0.1134 (0.1128…0.1139) | 0.1163 (0.1160…0.1166) | 0.1166 (0.1161…0.1171) | +2.87 % | +0.28 % | +0.37 % | hit | yes |
|  |  | rlxfw loud | 1/1 | 0.1162 | 0.1179 | 0.1182 | +1.72 % | +0.31 % | −0.75 % | hit | yes |
| `boot.jump_to_ready` | not comparable | vendor | 4/4 | 26.2170 (26.0858…26.3096) | 26.8438 (26.6671…26.8987) | 26.8583 (26.8281…26.9717) | +2.45 % | +0.05 % | −0.04 % | hit | yes |
|  |  | rlxfw quiet | 2/2 | 10.5327 (10.5249…10.5405) | 10.8045 (10.7920…10.8170) | 10.7933 (10.7910…10.7956) | +2.47 % | −0.10 % | −0.01 % | hit | yes |
|  |  | rlxfw loud | 1/1 | 12.3745 | 12.5490 | 12.5345 | +1.29 % | −0.12 % | −1.16 % | hit | yes |

* 量 Every load-bearing cold row hits. (a) runs +1.10 % to +2.87 % — the host clock seating A
  carried — except `rlxfw.setup` (+3.58 % quiet, +6.71 % loud); (b) is within ±1.10 % everywhere
  but `rlxfw.setup` loud, whose +5.23 % is the largest (b) of any load-bearing row.
* 量 In `P1L-r01-boot` the read carrying `RLXFW-B09` returned 15.86 ms after its predecessor with
  66 bytes already waiting on the receive path, so its stamp is at least 13.5 ms late by the
  line-rate bound, while `kernel.early`, which contains it, reads 1.5239 s against 1.5249 s warm.
  推 that row's seating-B value is one late read, not a slower `start_kernel`: from the reads
  alone the interval lies in 0.278069–0.291798 s, inside card B § 3.7's band, [0.2757, 0.2827],
  only if `B00` arrived after 1.289105 s — likely, not shown. The band was missed on this one row
  of 68. Whether the host, usbip or the CP2102 held the bytes is not established
  (`notes/boot-time.md` § 8.5).
* 讀 `loader.esc` exists only when the loader autoboots, so only on the listen-mode boots `M1`
  (cold) and `M2` (warm), n = 1: not stable, both inside.

## 3. Warm boots

A warm boot follows a reset with no power cycle — `busybox reboot -f` on rlxfw, `J BFC00000` from a
caught prompt on the vendor. Populations: the loader's thirteen warm catches; the vendor's `V4`–`V7`
and `M2`; rlxfw quiet `P1Q-r01`…`r04`, `P2Q-r02`, `P3Q-r02`; rlxfw loud `P1L-r02`, `r03`.

| segment | class | firmware | n A/B | A raw | A corrected | B (RAW) | (a) | (b) | (c) | `D3` | LB |
|---|---|---|---:|---|---|---|---:|---:|---:|---|---|
| `loader.booting` | identical | loader, both | 13/13 | 0.3474 (0.3415…0.3522) | 0.3560 (0.3552…0.3571) | 0.3561 (0.3556…0.3570) | +2.49 % | +0.03 % | 0.00 % | hit | yes |
| `loader.banner` | identical | loader, both | 13/13 | 0.5822 (0.5727…0.5890) | 0.5960 (0.5957…0.5973) | 0.5960 (0.5958…0.5972) | +2.37 % | −0.00 % | −0.11 % | hit | yes |
| `loader.esc` | identical | loader, both | 1/1 | 5.1021 | 5.2370 | 5.2378 | +2.66 % | +0.01 % | +0.17 % | n.s., inside |  |
| `rtkload.decompress` | comparable | vendor | 5/5 | 1.0337 (1.0269…1.0341) | 1.0598 (1.0518…1.0604) | 1.0601 (1.0600…1.0603) | +2.55 % | +0.03 % | +0.07 % | hit | yes |
|  |  | rlxfw quiet | 6/6 | 1.2012 (1.1880…1.2014) | 1.2181 (1.2181…1.2209) | 1.2176 (1.2170…1.2183) | +1.37 % | −0.04 % | −1.09 % | hit | yes |
|  |  | rlxfw loud | 2/2 | 1.2299 (1.2298…1.2300) | 1.2473 (1.2471…1.2474) | 1.2473 (1.2471…1.2475) | +1.41 % | +0.00 % | −1.05 % | hit | yes |
| `rtkload.total` | comparable | vendor | 5/5 | 1.0449 (1.0398…1.0495) | 1.0720 (1.0651…1.0779) | 1.0744 (1.0720…1.0781) | +2.82 % | +0.23 % | +0.33 % | hit | yes |
|  |  | rlxfw quiet | 6/6 | 1.2144 (1.2024…1.2159) | 1.2330 (1.2309…1.2358) | 1.2310 (1.2300…1.2323) | +1.37 % | −0.16 % | −1.09 % | hit | yes |
|  |  | rlxfw loud | 2/2 | 1.2423 (1.2422…1.2423) | 1.2598 (1.2597…1.2598) | 1.2623 (1.2617…1.2630) | +1.62 % | +0.20 % | −0.85 % | hit | yes |
| `kernel.early` | comparable | vendor | 5/5 | 0.6504 (0.6466…0.6507) | 0.6669 (0.6623…0.6675) | 0.6667 (0.6664…0.6680) | +2.51 % | −0.04 % | +0.02 % | hit | yes |
|  |  | rlxfw quiet | 6/6 | 0.8099 (0.8019…0.8119) | 0.8219 (0.8210…0.8243) | 0.8219 (0.8213…0.8222) | +1.48 % | −0.00 % | −0.98 % | hit | yes |
|  |  | rlxfw loud | 2/2 | 1.5039 (1.5036…1.5042) | 1.5251 (1.5248…1.5254) | 1.5249 (1.5249…1.5250) | +1.40 % | −0.01 % | −1.06 % | hit | yes |
| `kernel.wlan` | comparable | vendor | 5/5 | 4.5026 (4.4804…4.5106) | 4.6229 (4.5892…4.6272) | 4.6226 (4.6220…4.6259) | +2.66 % | −0.01 % | +0.17 % | hit | yes |
|  |  | rlxfw quiet | 6/6 | 4.5331 (4.4830…4.5349) | 4.5972 (4.5963…4.6073) | 4.5976 (4.5971…4.6059) | +1.42 % | +0.01 % | −1.04 % | hit | yes |
|  |  | rlxfw loud | 2/2 | 5.1352 (5.1347…5.1358) | 5.2076 (5.2070…5.2081) | 5.2070 (5.2070…5.2070) | +1.40 % | −0.01 % | −1.06 % | hit | yes |
| `kernel.nic` | comparable | vendor | 5/5 | 0.8135 (0.8101…0.8148) | 0.8339 (0.8306…0.8350) | 0.8343 (0.8314…0.8348) | +2.56 % | +0.05 % | +0.07 % | hit | yes |
|  |  | rlxfw quiet | 6/6 | 0.8477 (0.8391…0.8487) | 0.8600 (0.8591…0.8628) | 0.8606 (0.8515…0.8614) | +1.52 % | +0.07 % | −0.94 % | hit | yes |
|  |  | rlxfw loud | 2/2 | 1.2239 (1.2238…1.2239) | 1.2411 (1.2411…1.2412) | 1.2410 (1.2410…1.2410) | +1.40 % | −0.01 % | −1.06 % | hit | yes |
| `kernel.late` | comparable | vendor | 5/5 | 0.9490 (0.9459…0.9515) | 0.9736 (0.9699…0.9747) | 0.9741 (0.9737…0.9860) | +2.65 % | +0.06 % | +0.16 % | hit | yes |
|  |  | rlxfw quiet | 6/6 | 3.1214 (3.0877…3.1220) | 3.1657 (3.1640…3.1734) | 3.1655 (3.1654…3.1658) | +1.41 % | −0.00 % | −1.05 % | hit | yes |
|  |  | rlxfw loud | 2/2 | 3.1390 (3.1389…3.1390) | 3.1832 (3.1832…3.1832) | 3.1834 (3.1832…3.1836) | +1.41 % | +0.01 % | −1.04 % | hit | yes |
| `kernel.total` | comparable | vendor | 5/5 | 6.9120 (6.8934…6.9252) | 7.0964 (7.0607…7.1042) | 7.0981 (7.0975…7.1097) | +2.69 % | +0.02 % | +0.20 % | hit | yes |
|  |  | rlxfw quiet | 6/6 | 9.3138 (9.2122…9.3144) | 9.4454 (9.4405…9.4678) | 9.4457 (9.4451…9.4465) | +1.42 % | +0.00 % | −1.04 % | hit | yes |
|  |  | rlxfw loud | 2/2 | 11.0020 (11.0012…11.0028) | 11.1571 (11.1562…11.1579) | 11.1563 (11.1561…11.1566) | +1.40 % | −0.01 % | −1.06 % | hit | yes |
| `rlxfw.setup` | not comparable | rlxfw quiet | 6/6 | 0.0463 (0.0461…0.0466) | 0.0471 (0.0469…0.0474) | 0.0472 (0.0471…0.0474) | +2.08 % | +0.19 % | −0.40 % | hit | yes |
|  |  | rlxfw loud | 2/2 | 0.2746 (0.2741…0.2752) | 0.2785 (0.2780…0.2791) | 0.2781 (0.2777…0.2785) | +1.27 % | −0.13 % | −1.18 % | hit | yes |
| `rlxfw.initpost` | not comparable | rlxfw quiet | 6/6 | 0.0117 (0.0116…0.0125) | 0.0119 (0.0118…0.0127) | 0.0120 (0.0118…0.0127) | +2.36 % | +0.49 % | −0.12 % | n.s., inside |  |
|  |  | rlxfw loud | 2/2 | 0.0117 (0.0114…0.0120) | 0.0119 (0.0116…0.0122) | 0.0123 (0.0122…0.0124) | +4.92 % | +3.46 % | +2.37 % | n.s., inside |  |
| `user.ready` | not comparable | vendor | 5/5 | 18.2492 (17.4062…18.2674) | 18.7056 (17.8287…18.7396) | 18.6601 (17.6779…18.8630) | +2.25 % | −0.24 % | −0.23 % | hit | yes |
|  |  | rlxfw quiet | 6/6 | 0.1143 (0.1121…0.1150) | 0.1159 (0.1152…0.1166) | 0.1160 (0.1155…0.1163) | +1.54 % | +0.12 % | −0.92 % | hit | yes |
|  |  | rlxfw loud | 2/2 | 0.1164 (0.1161…0.1167) | 0.1180 (0.1177…0.1183) | 0.1177 (0.1175…0.1179) | +1.11 % | −0.30 % | −1.35 % | hit | yes |
| `boot.jump_to_ready` | not comparable | vendor | 5/5 | 26.1917 (25.3394…26.2376) | 26.8551 (25.9545…26.9158) | 26.8370 (25.8519…27.0352) | +2.46 % | −0.07 % | −0.02 % | hit | yes |
|  |  | rlxfw quiet | 6/6 | 10.6427 (10.5267…10.6448) | 10.7938 (10.7899…10.8188) | 10.7928 (10.7909…10.7942) | +1.41 % | −0.01 % | −1.05 % | hit | yes |
|  |  | rlxfw loud | 2/2 | 12.3606 (12.3594…12.3618) | 12.5349 (12.5336…12.5361) | 12.5363 (12.5357…12.5369) | +1.42 % | +0.01 % | −1.04 % | hit | yes |

* 量 Every load-bearing warm row hits: (a) +1.11 % to +2.82 %, |b| ≤ 0.30 %.
* 量 On RAW the thirteen warm loader catches — identical code across the seating — span 1.363 ms,
  0.383 % of their median; the eight quiet `J` → prompt values of seating B span 4.6 ms, 0.043 %.
* 量 The vendor's warm `user.ready` and `boot.jump_to_ready` ranges are wide in both seatings
  because one boot in each took the fast `WiFi Simple Config` step (§ 4.1).

## 4. Beside the per-class rows

### 4.1 Pooled and per-mode rows, and the vendor's own steps

None of these rows is load-bearing — the pooled and per-mode ones by ruling R1 (§ 9.3), the
vendor's own steps because the closing rule does not name them — and every one that is stable
hits.

| quantity | n A/B | A raw | A corrected | B (RAW) | (a) | (b) | (c) | `D3` | LB |
|---|---:|---|---|---|---:|---:|---:|---|---|
| rlxfw quiet, `J` → prompt, cold and warm | 8/8 | 10.5916 (10.5249…10.6448) | 10.7938 (median) | 10.7928 (10.7909…10.7956) | +1.90 % | −0.01 % | −0.57 % | hit |  |
| rlxfw loud, `J` → prompt, cold and warm | 3/3 | 12.3618 (12.3594…12.3745) | 12.5361 (median) | 12.5357 (12.5345…12.5369) | +1.41 % | −0.00 % | −1.05 % | hit |  |
| rlxfw quiet, `kernel.total`, cold and warm | 8/8 | 9.2689 (9.2108…9.3144) | 9.4454 (median) | 9.4457 (9.4451…9.4465) | +1.91 % | +0.00 % | −0.56 % | hit |  |
| rlxfw loud, `kernel.total`, cold and warm | 3/3 | 11.0028 (11.0012…11.0114) | 11.1579 (median) | 11.1561 (11.1556…11.1566) | +1.39 % | −0.02 % | −1.07 % | hit |  |
| rlxfw quiet, `user.ready`, cold and warm | 8/8 | 0.1141 (0.1121…0.1150) | 0.1160 (median) | 0.1162 (0.1155…0.1171) | +1.82 % | +0.17 % | −0.64 % | hit |  |
| vendor, `kernel.total`, cold and warm | 9/9 | 6.9252 (6.8934…6.9879) | 7.0978 (median) | 7.0980 (7.0973…7.1097) | +2.50 % | +0.00 % | +0.01 % | hit |  |
| vendor, `J` → `boa`, cold and warm | 9/9 | 26.1917 (25.3394…26.3096) | 26.8551 (median) | 26.8370 (25.8519…27.0352) | +2.46 % | −0.07 % | −0.02 % | hit |  |
| vendor, `J` → `boa`, slow WSC step (≥ 1 s) | 8/8 | 26.2038 (26.0574…26.3096) | 26.8633 (median) | 26.8597 (26.8230…27.0352) | +2.50 % | −0.01 % | +0.02 % | hit |  |
| vendor, `J` → `boa`, fast WSC step (< 0.2 s) | 1/1 | 25.3394 | 25.9545 | 25.8519 | +2.02 % | −0.40 % | −0.45 % | hit |  |
| vendor, `WiFi Simple Config` → `Register to wlan0`, slow | 8/8 | 1.1238 (1.1136…1.1307) | 1.1525 (median) | 1.1563 (1.1514…1.1635) | +2.90 % | +0.33 % | +0.40 % | hit |  |
| vendor, `WiFi Simple Config` → `Register to wlan0`, fast | 1/1 | 0.1466 | 0.1502 | 0.1495 | +1.96 % | −0.46 % | −0.51 % | hit |  |
| vendor, `sysconf wlanapp kill wlan0` → `Init bridge interface...` | 9/9 | 0.8387 (0.8332…0.8557) | 0.8585 (median) | 0.8568 (0.8544…0.8602) | +2.16 % | −0.20 % | −0.32 % | hit |  |
| vendor warm reset, `J BFC00000` → `<RealTek>` | 4/4 | 2.2425 (2.2117…2.2488) | 2.3034 (median) | 2.3048 (2.3001…2.3054) | +2.78 % | +0.06 % | +0.29 % | hit |  |

* 量 The vendor's `WiFi Simple Config` → `Register to wlan0` step takes either about 1.15 s or
  about 0.15 s, and no boot of either seating fell between 0.2 and 1 s. The fast step was `V4` in
  seating A (0.146649 s) and `V7` in seating B (0.149520 s); `V7`'s `J` → `boa` is 1.0078 s under
  the slow boots' median, and the step's own shortfall accounts for it to 1.0 ms. 推 a race, tied
  to neither press position nor class.

### 4.2 `D2` — the identical-code control (`CLK-45`)

`Booting` → banner, in the groups card A § 3.1 fixed before seating A; seating B's are the same
captures by name.

| `loader.banner`, group (card B § 3.1) | n A/B | A raw | A corrected | B (RAW) | (a) | (b) | (c) | `D3` | LB |
|---|---:|---|---|---|---:|---:|---:|---|---|
| rlxfw cold | 3/3 | 0.5727 (0.5706…0.5861) | 0.5863 (median) | 0.5860 (0.5858…0.5861) | +2.32 % | −0.06 % | −0.16 % | hit |  |
| vendor cold | 3/3 | 0.5731 (0.5729…0.5733) | 0.5862 (median) | 0.5861 (0.5850…0.5862) | +2.27 % | −0.00 % | −0.21 % | hit |  |
| rlxfw warm | 8/8 | 0.5878 (0.5812…0.5890) | 0.5960 (median) | 0.5968 (0.5958…0.5971) | +1.54 % | +0.13 % | −0.92 % | hit |  |
| vendor warm | 4/4 | 0.5800 (0.5727…0.5822) | 0.5958 (median) | 0.5960 (0.5960…0.5960) | +2.76 % | +0.02 % | +0.27 % | hit |  |
| loader-only cold (context) | 5/5 | 0.5720 (0.5664…0.5732) | 0.5861 (median) | 0.5860 (0.5858…0.5865) | +2.43 % | −0.02 % | −0.05 % | hit |  |
| `M1-BOOT`, cold, listen | 1/1 | 0.5726 | 0.5856 | 0.5815 | +1.55 % | −0.69 % | −0.91 % | n.s., inside |  |
| `M2-BOOT`, warm, listen | 1/1 | 0.5808 | 0.5961 | 0.5972 | +2.83 % | +0.18 % | +0.33 % | n.s., inside |  |

| difference of group medians (s) | n A/B | A raw | A corrected | B (RAW) | (a) | (b) | (c) | `D3` | LB |
|---|---:|---|---|---|---:|---:|---:|---|---|
| warm, rlxfw − vendor (band ±0.010) | 1/1 | 0.007810 | 0.000191 | 0.000824 | signed | signed | signed | n.s., outside |  |
| cold, rlxfw − vendor (band ±0.025) | 1/1 | −0.000442 | 0.000146 | −0.000167 | signed | signed | signed | n.s., outside |  |
| `M1` − rlxfw cold (band ±0.010) | 1/1 | −0.000023 | −0.000731 | −0.004457 | signed | signed | signed | n.s., outside |  |
| `M1` − vendor cold (band ±0.010) | 1/1 | −0.000465 | −0.000585 | −0.004624 | signed | signed | signed | n.s., outside |  |
| `M2` − rlxfw warm (band ±0.010) | 1/1 | −0.007012 | 0.000080 | 0.000354 | signed | signed | signed | n.s., outside |  |
| `M2` − vendor warm (band ±0.010) | 1/1 | 0.000798 | 0.000272 | 0.001178 | signed | signed | signed | n.s., outside |  |

* 量 **`D2` holds in seating B**, every difference inside the band written before seating A
  (warm and listen ±0.010 s, cold ±0.025 s). Three of the six land within 0.64 ms of seating A's
  corrected differences, and a fourth, `M2` − vendor warm, within 0.91 ms.
* 量 `M1`'s two land 3.7–4.0 ms away. `M1-BOOT`'s `loader.booting` is about 4.4 ms under the
  other cold catches while its `banner` − `booting` is −0.12 ms: the read carrying its anchor-C
  byte returned 5.39 ms after its predecessor, against 0.54–1.10 ms in the 24 other loader boots.
  Measured from anchor A instead, `M1` − rlxfw cold is −0.05 ms and `M1` − vendor cold −0.19 ms.
  推 one late read, not a property of listen mode: `M2-BOOT` and seating A's `M1-BOOT` show none.

### 4.3 `D7` — the loud image against the quiet one (`CLK-46`)

Press 1, one recipe built two ways (`a2c56bc8`: `p2l` loud, `p2q` quiet).

| quantity (card B § 3.3) | n A/B | A raw | A corrected | B (RAW) | (a) | (b) | (c) | `D3` | LB |
|---|---:|---|---|---|---:|---:|---:|---|---|
| Δ `kernel.total`, loud − quiet, press 1 (s) | 1/1 | 1.688630 | 1.712433 | 1.710352 | +1.29 % | −0.12 % | −1.17 % | hit | yes |
| f·ΔB/ΔT, % of 3,840 B/s | 1/1 | 88.325 | 89.237 | 89.370 | +1.18 % | +0.15 % | −1.27 % | hit |  |
| ΔB, `B00` → `B09` (bytes) | 12/12 | 810 (810…810) | = raw | 810 (810…810) | 0.00 % | 0.00 % | — | hit |  |
| ΔB, `B09` → `B10` (bytes) | 12/12 | 5021 (5021…5021) | = raw | 5021 (5021…5021) | 0.00 % | 0.00 % | — | hit |  |
| ΔB, loud − quiet boot (bytes) | 12/12 | 5831 (5831…5831) | = raw | 5831 (5831…5831) | 0.00 % | 0.00 % | — | hit |  |

* 量 **`D7` holds.** Δ = 11.156054 − 9.445702 = 1.710352 s, inside the registered band at the
  measured f_B = 0.356060 / 0.353718 = 1.006621, [1.398905, 1.979101] s. Every loud boot is
  7,948 B with e = 0, and the whole 5,831-byte difference lies between `kentry` and
  `rlxfw: init running` in 12 of 12 pairs.
* 量 The implied console rate f_B·ΔB/Δ is 3,431.8 B/s, 89.370 % of 3,840 B/s, inside `FW-70`'s
  88.4–92.7 %; at f = 1 it is 88.782 %, also inside. Which f belongs in the rate is not
  established.

## 5. Network up and readiness

The plan's last two segments, *network up* and *httpd responds*. Network up is the first ICMP echo
reply the host reads after `J` (`D8`); the reply's arrival is set by the host's ARP retransmit
phase as much as by the board, so the board's own decision is compared instead — rlxfw's
`N-NDOPEN`, the vendor's `Start NTP daemon` — together with the bracket that the host's ARP
broadcasts put around the board's first answer: the answered broadcast #k, and the bracket's width
(card B §§ 3.4, 3.10). The channel-offset test fired in both seatings (§ 5.4), so every
network-up figure here is a console-side bound.

### 5.1 rlxfw

| quantity (card B § 3.4) | n A/B | A raw | A corrected | B (RAW) | (a) | (b) | (c) | `D3` | LB |
|---|---:|---|---|---|---:|---:|---:|---|---|
| quiet cold, `J` → NIC probe | 2/2 | 6.4897 (6.4856…6.4938) | 6.6571 (median) | 6.6506 (6.6487…6.6525) | +2.48 % | −0.10 % | −0.01 % | hit |  |
| quiet warm, `J` → NIC probe | 6/6 | 6.5588 (6.4874…6.5604) | 6.6517 (median) | 6.6504 (6.6490…6.6595) | +1.40 % | −0.02 % | −1.06 % | hit |  |
| quiet cold, `J` → `N-NDOPEN` | 2/2 | 10.5029 (10.4956…10.5103) | 10.7739 (median) | 10.7622 (10.7601…10.7642) | +2.47 % | −0.11 % | −0.02 % | hit | yes |
| quiet warm, `J` → `N-NDOPEN` | 6/6 | 10.6126 (10.4974…10.6153) | 10.7633 (median) | 10.7622 (10.7610…10.7632) | +1.41 % | −0.01 % | −1.05 % | hit | yes |
| quiet cold, NIC probe → `N-NDOPEN` | 2/2 | 4.0133 (4.0101…4.0165) | 4.1168 (median) | 4.1116 (4.1114…4.1118) | +2.45 % | −0.13 % | −0.04 % | hit |  |
| quiet warm, NIC probe → `N-NDOPEN` | 6/6 | 4.0538 (4.0099…4.0548) | 4.1116 (median) | 4.1118 (4.1030…4.1129) | +1.43 % | +0.01 % | −1.03 % | hit |  |
| quiet cold, `J` → `lan up` | 2/2 | 10.5090 (10.5016…10.5163) | 10.7801 (median) | 10.7684 (10.7663…10.7704) | +2.47 % | −0.11 % | −0.02 % | hit |  |
| quiet warm, `J` → `lan up` | 6/6 | 10.6186 (10.5033…10.6208) | 10.7694 (median) | 10.7684 (10.7669…10.7700) | +1.41 % | −0.01 % | −1.05 % | hit |  |
| quiet cold, `J` → first ICMP reply read | 1/2 | 10.7145 | 10.8694 | 10.8769 (10.8695…10.8843) | +1.52 % | +0.07 % | −0.95 % | n.s., inside |  |
| quiet warm, `J` → first ICMP reply read | 6/6 | 10.7820 (10.7082…10.8055) | 10.8842 (median) | 10.8870 (10.8400…10.9106) | +0.97 % | +0.03 % | −1.48 % | n.s., inside |  |
| quiet cold, answered broadcast k | 1/2 | 2 | = raw | 2 (2…2) | — | — | — | exact, hit |  |
| quiet warm, answered broadcast k | 6/6 | 2 (2…2) | = raw | 2 (2…2) | — | — | — | exact, hit |  |
| quiet cold, bracket width (midpoint) | 1/2 | 0.1878 | 0.0920 | 0.1046 (0.0946…0.1146) | −44.30 % | +13.71 % | −45.66 % | **MISS** |  |
| quiet warm, bracket width (midpoint) | 6/6 | 0.1772 (0.1448…0.2030) | 0.1001 (median) | 0.1234 (0.0812…0.1350) | −30.40 % | +23.27 % | −32.08 % | n.s., outside |  |
| loud cold, `J` → NIC probe | 1/1 | 7.8937 | 8.0050 | 7.9925 | +1.25 % | −0.16 % | −1.20 % | hit |  |
| loud warm, `J` → NIC probe | 2/2 | 7.8814 (7.8805…7.8823) | 7.9925 (median) | 7.9943 (7.9937…7.9949) | +1.43 % | +0.02 % | −1.03 % | hit |  |
| loud cold, `J` → `N-NDOPEN` | 1/1 | 12.3439 | 12.5179 | 12.5037 | +1.29 % | −0.11 % | −1.16 % | hit | yes |
| loud warm, `J` → `N-NDOPEN` | 2/2 | 12.3300 (12.3289…12.3312) | 12.5038 (median) | 12.5053 (12.5047…12.5059) | +1.42 % | +0.01 % | −1.04 % | hit | yes |
| loud cold, NIC probe → `N-NDOPEN` | 1/1 | 4.4502 | 4.5130 | 4.5113 | +1.37 % | −0.04 % | −1.09 % | hit |  |
| loud warm, NIC probe → `N-NDOPEN` | 2/2 | 4.4486 (4.4484…4.4489) | 4.5114 (median) | 4.5110 (4.5110…4.5110) | +1.40 % | −0.01 % | −1.06 % | hit |  |
| loud cold, `J` → `lan up` | 1/1 | 12.3502 | 12.5243 | 12.5094 | +1.29 % | −0.12 % | −1.17 % | hit |  |
| loud warm, `J` → `lan up` | 2/2 | 12.3360 (12.3352…12.3369) | 12.5099 (median) | 12.5115 (12.5109…12.5121) | +1.42 % | +0.01 % | −1.04 % | hit |  |
| loud cold, `J` → first ICMP reply read | 0/1 | — | — | 13.2309 | — | — | — | first reading |  |
| loud warm, `J` → first ICMP reply read | 0/2 | — | — | 13.2720 (13.2627…13.2813) | — | — | — | first reading |  |
| loud cold, answered broadcast k | 0/1 | — | — | 3 | — | — | — | first reading |  |
| loud warm, answered broadcast k | 0/2 | — | — | 3 (3…3) | — | — | — | first reading |  |
| loud cold, bracket width (midpoint) | 0/1 | — | — | 0.7131 | — | — | — | first reading |  |
| loud warm, bracket width (midpoint) | 0/2 | — | — | 0.7292 (0.7199…0.7386) | — | — | — | first reading |  |

* 量 Every board row hits, (b) −0.16 % to +0.02 %. rlxfw's `J` → `N-NDOPEN`, the closing rule's
  network row, hits in all four cells.
* 量 The quiet image answered the host's second broadcast in 8 of 8 boots, 6 by frames and 2 by
  the probe's ledger (card B predicted k = 2 exactly); `N-NDOPEN` came 0.0715–0.1449 s before that
  broadcast in the six framed boots and was the bracket's lower edge in all eight. First reply:
  `J` + 10.840–10.911 s.
* 量 **The loud image has a reading** (`CLK-47`): seating A reset it 0.189–0.221 s after its prompt,
  before any reply; held 2.5 RAW seconds past the prompt, it answered the third broadcast in 3 of 3
  — the frames put its `is-at` 2.8–3.6 ms after the third `who-has`, and the second came
  0.258–0.309 s before `N-NDOPEN` — at `J` + 13.231–13.281 s, 1.97–2.01 s before the next reset.
* 量 NIC probe → `N-NDOPEN`: seating A's raw 4.01–4.05 s (quiet) and 4.45 s (loud) carried the
  slow clock; corrected medians 4.1116–4.1168 s and 4.5114–4.5130 s; seating B 4.103–4.113 s (n 8)
  and 4.511 s (n 3).
* The one stable network miss, the quiet cold bracket width, is § 10's.

### 5.2 The vendor

| quantity (card B §§ 3.4, 3.6) | n A/B | A raw | A corrected | B (RAW) | (a) | (b) | (c) | `D3` | LB |
|---|---:|---|---|---|---:|---:|---:|---|---|
| cold, `J` → `Start NTP daemon` | 3/3 | 14.5755 (14.5342…14.6851) | 14.9019 (median) | 14.9172 (14.8803…14.9212) | +2.34 % | +0.10 % | −0.14 % | hit |  |
| warm, `J` → `Start NTP daemon` | 4/4 | 14.5451 (14.4749…14.6349) | 14.9035 (median) | 14.8879 (14.8767…14.9269) | +2.36 % | −0.10 % | −0.13 % | hit |  |
| cold, `J` → first ICMP reply read | 3/3 | 14.9857 (14.5406…15.6499) | = raw | 15.7475 (15.7413…15.7712) | +5.08 % | +5.08 % | +2.54 % | n.s., inside |  |
| warm, `J` → first ICMP reply read | 4/4 | 14.5048 (14.4903…15.5855) | = raw | 15.7481 (15.7254…15.7818) | +8.57 % | +8.57 % | +5.94 % | n.s., inside |  |
| cold, answered broadcast k | 3/3 | 1 (1…3) | = raw | 1 (1…1) | 0.00 % | 0.00 % | — | n.s., inside |  |
| warm, answered broadcast k | 4/4 | 3 (1…3) | = raw | 1 (1…1) | −66.67 % | −66.67 % | — | n.s., outside |  |
| cold, bracket width (midpoint) | 3/3 | 1.0621 (1.0140…1.0970) | = raw | 1.0612 (1.0597…1.0662) | −0.08 % | −0.08 % | — | n.s., inside |  |
| warm, bracket width (midpoint) | 4/4 | 1.0140 (1.0140…1.0561) | = raw | 1.0641 (1.0608…1.0654) | +4.94 % | +4.94 % | — | n.s., inside |  |
| cold, `J` → first `tcp:80` ok | 3/3 | 26.2698 (26.0696…26.2748) | 26.8580 (median) | 26.8759 (26.8726…27.0207) | +2.31 % | +0.07 % | −0.17 % | hit | yes |
| warm, `J` → first `tcp:80` ok | 4/4 | 26.1507 (25.2496…26.2577) | 26.8162 (median) | 26.8435 (25.8732…27.0953) | +2.65 % | +0.10 % | +0.16 % | hit | yes |
| slow WSC step, `J` → first `tcp:80` ok | 8/8 | 26.1765 (26.0581…26.2748) | 26.8365 (median) | 26.8743 (26.8187…27.0953) | +2.67 % | +0.14 % | +0.18 % | hit |  |
| fast WSC step, `J` → first `tcp:80` ok | 1/1 | 25.2496 | 25.8625 | 25.8732 | +2.47 % | +0.04 % | −0.02 % | hit |  |
| cold, first `tcp:80` ok − `boa: starting server` | 3/3 | −0.0161 (−0.0398…0.0165) | = raw | 0.0478 (−0.0097…0.0491) | signed | signed | signed | n.s., outside |  |
| warm, first `tcp:80` ok − `boa: starting server` | 4/4 | −0.0420 (−0.1336…0.0418) | = raw | 0.0085 (−0.0899…0.0601) | signed | signed | signed | n.s., outside |  |
| all nine, first ICMP reply → first `tcp:80` ok | 9/9 | 11.0840 (10.4213…11.7453) | = raw | 11.1071 (10.1478…11.3482) | +0.21 % | +0.21 % | −2.22 % | hit |  |
| all nine, `J` → first `tcp:52881` ok | 0/9 | — | — | 17.2729 (17.0799…17.4216) | — | — | — | first reading |  |
| all nine, `J` → first `tcp:52869` ok | 0/9 | — | — | 32.2724 (31.2738…32.4955) | — | — | — | first reading |  |

Listen-only boots (`M1` cold, `M2` warm; n = 1, not stable, each inside):

| listen-only boot | n A/B | A raw | A corrected | B (RAW) | (a) | (b) | (c) | `D3` | LB |
|---|---:|---|---|---|---:|---:|---:|---|---|
| `M1`, `J` → `Start NTP daemon` | 1/1 | 14.6661 | 15.0129 | 14.8526 | +1.27 % | −1.07 % | −1.18 % | n.s., inside |  |
| `M1`, `J` → first ICMP reply read | 1/1 | 15.6368 | = raw | 15.7714 | +0.86 % | +0.86 % | −1.59 % | n.s., inside |  |
| `M1`, `J` → first `tcp:80` ok | 1/1 | 26.0581 | 26.6742 | 26.8785 | +3.15 % | +0.77 % | +0.65 % | n.s., inside |  |
| `M2`, `J` → `Start NTP daemon` | 1/1 | 14.5123 | 14.9042 | 14.8871 | +2.58 % | −0.12 % | +0.09 % | n.s., inside |  |
| `M2`, `J` → first ICMP reply read | 1/1 | 14.5307 | = raw | 15.7402 | +8.32 % | +8.32 % | +5.70 % | n.s., inside |  |
| `M2`, `J` → first `tcp:80` ok | 1/1 | 26.1097 | 26.8149 | 26.8341 | +2.77 % | +0.07 % | +0.28 % | n.s., inside |  |

* 量 The board rows hit: `J` → `Start NTP daemon` (b) +0.10 % cold, −0.10 % warm; port 80 from `J`,
  the closing rule's readiness row, (b) +0.07 % cold and +0.10 % warm.
* 量 **All nine vendor boots of seating B answered at k = 1** — the first broadcast of the cycle
  after a failed one, by the probe's ledger, since no capture ran on a vendor press — against
  k = 3 in five and k = 1 in four in seating A; their first replies fell at `J` + 15.725–15.782 s
  against `J` + 14.490–15.650 s. 推 seating A's slow clock stretched about 9 s of host ARP timers by
  about 0.2 s and moved the race; not tested. The host's ARP phase is why card B § 3.10 listed the
  first reply as not stable before power.
* 量 Port 80: the slow-step boots answer at `J` + 26.819–27.095 s (n 8), the fast one at
  `J` + 25.873 s. The first success lies within ±0.14 s of `boa: starting server` in 9 of 9, five
  after it and four before (−0.090 … +0.060 s).
* 量 Inference (ii) is not refuted: every seating-B window, last refused connect → first success,
  overlaps `boa` listening 0.111–0.127 s before its `boa: server version` line, and the eighteen
  windows of both seatings intersect in (−0.117471, −0.111008] s. 推 one offset for all eighteen
  boots; the 0.111 edge carries seating A's rule of 1 ms added to the first success's start.
  Inference (i), the vendor answering ARP 0.075–0.116 s before `Start NTP daemon`, is not refuted
  in 9 of 9 either, and the test is weak: its brackets are 1.03–1.10 s wide.
* 量 **Ports 52881 and 52869, first readings** (`NET-118`): seating A's probe connected to port 80
  only. 52881 answers at `J` + 17.08–17.42 s, 4.79–5.96 s before the `MiniIGD` line, and its
  listen window fits one offset from the `WiFi Simple Config v2.18` line, (−0.0186, +0.0129] s, in
  9 of 9 and none from `Register to wlan0` or the `MiniIGD` line; 讀 the SDK drop names it
  (`br_input.c`, `#define RTK_WPS_LISTEN_PORT 52881`). 52869 answers at `J` + 31.27–32.50 s and
  fits one offset from each of three lines — `MiniIGD`, `boa: server version`, and, tightest,
  `Register to wlan0` — so timing alone cannot name it; 讀 the SDK drop calls 52869 its IGD port
  (`ip_input.c`, `picsdesc.xml`). 推 52881 is `wscd`'s WPS listener and 52869 `miniigd`'s: the
  SDK is a related drop, not TOTOLINK's build, and no shell exists to stop either daemon.

### 5.3 Each vendor daemon's own start and readiness, seating B

For the not-comparable rows (`D4`): each daemon's console line, its start, and the first host
success on its port, its readiness. 量, seconds after `J`, nine boots (`V1`–`V7`, `M1`, `M2`);
console lines are `FW-35` arrivals, readiness a `hostprobe` read on a 0.2 s connect grid per port.

| event | n | median | min–max | seconds after `J`, V7 (fast WSC step) |
|---|---:|---:|---|---:|
| `Init bridge interface...` (console) | 9 | 13.837 | 13.801–13.853 | 13.805 |
| `Start NTP daemon` (console) | 9 | 14.887 | 14.853–14.927 | 14.890 |
| first ICMP echo reply (host) | 9 | 15.747 | 15.725–15.782 | 15.725 |
| `WiFi Simple Config v2.18` (console) | 9 | 17.100 | 17.065–17.262 | 17.095 |
| first `tcp:52881` ok (host) | 9 | 17.273 | 17.080–17.422 | 17.274 |
| `Register to wlan0` (console) | 9 | 18.251 | 17.244–18.423 | 17.244 |
| `MiniIGD v1.09.1` (console) | 9 | 23.047 | 22.067–23.250 | 22.067 |
| `boa: server version` (console) | 9 | 26.813 | 25.830–27.011 | 25.830 |
| `boa: starting server` (console) | 9 | 26.837 | 25.852–27.035 | 25.852 |
| first `tcp:80` ok (host) | 9 | 26.873 | 25.873–27.095 | 25.873 |
| first `tcp:52869` ok (host) | 9 | 32.272 | 31.274–32.495 | 31.274 |

* 量 `V7`'s fast step moves every line after `WiFi Simple Config` about 1 s earlier, and 52881 not
  at all — 52881 opens before the step.
* rlxfw has no listening port (`P1-NMAP`, both seatings); its readiness is the shell prompt
  (`boot.jump_to_ready`, §§ 2–3) and its network `N-NDOPEN` and the first reply (§ 5.1).

### 5.4 The instruments' own quantities

| instrument quantity | n A/B | A raw | A corrected | B (RAW) | (a) | (b) | (c) | `D3` | LB |
|---|---:|---|---|---|---:|---:|---:|---|---|
| channel offset, probe read stamp, median (s) | 14/14 | 0.000103 (−0.000207…0.000494) | = raw | −0.000042 (−0.000277…0.000215) | signed | signed | signed | n.s., outside |  |
| channel offset, kernel receive stamp, median (s) | 14/14 | −0.000034 (−0.000521…0.000376) | = raw | −0.000249 (−0.000545…−0.000095) | signed | signed | signed | n.s., outside |  |
| channel offset range, probe read stamp (s) | 1/1 | 0.000701 | = raw | 0.000493 | −29.67 % | −29.67 % | −31.38 % | n.s., outside |  |
| channel offset range, kernel receive stamp (s) | 1/1 | 0.000896 | = raw | 0.000451 | −49.67 % | −49.67 % | −50.89 % | n.s., outside |  |
| host ARP retransmit, #1 → #2 (frames) | 11/47 | 1.0071 (1.0004…1.0255) | = raw | 1.0185 (1.0012…1.0335) | +1.14 % | +1.14 % | — | hit |  |
| host ARP retransmit, #2 → #3 (frames) | 8/36 | 1.0240 (1.0200…1.0280) | = raw | 1.0240 (1.0199…1.0280) | −0.00 % | −0.00 % | — | hit |  |
| host ARP, #3 → the failure’s read | 8/37 | 1.0244 (1.0203…1.0248) | = raw | 1.0242 (1.0202…1.0283) | −0.01 % | −0.01 % | — | hit |  |
| host ARP #1 − the echo that triggered it (s) | 10/46 | −0.000068 (−0.000113…−0.000011) | = raw | −0.000064 (−0.004326…−0.000003) | −7.30 % | −7.30 % | — | n.s., inside |  |
| quiet, NIC probe → the host’s #2 (frames) | 2/6 | 4.2407 (4.2158…4.2656) | = raw | 4.2154 (4.1844…4.2568) | −0.60 % | −0.60 % | — | hit |  |
| `J`’s first read − `sent_s` (s) | 19/19 | 0.000081 (0.000061…0.000140) | = raw | 0.000085 (0.000060…0.000375) | +4.94 % | +4.94 % | — | n.s., inside |  |

* 量 The channel offset — a UDP datagram's arrival at the host minus the console arrival of the
  line the same command printed, fifteen `P1-OFF` cells — ranges over 492.6 µs (probe read stamp)
  and 450.8 µs (kernel receive stamp) in seating B, 701.0 µs and 896.4 µs in seating A. Both exceed
  one byte time at 38400 8N1, 260.4 µs: the stability test fired in both seatings, as both cards
  predicted, so network up is published as a console-side bound only (`D8`). The table's (a) and
  (b) on the two range rows are the score's, from seconds rounded to six places; from the ranges
  in microseconds, 492.637 against 700.967 and 450.801 against 896.369, they are −29.72 % and
  −49.71 %. Neither row is stable.
* 量 The host's ARP retransmit: #1 → #2 reached 1.033472 s, 8 of 47 above card B's reconstruction
  range of 1.000–1.028 s; the reconstructed bracket edges are therefore uncertain by up to about
  5.5 ms beyond the rule's.
* 讀 `sent_s` is `tcdrain`'s return, not the send: the board prints `---Jump` only after it has the
  CR, and that byte reached the host 0.8–6.6 ms before `sent_s` in seating B and 1.0–6.3 ms before
  it in seating A, 23 of 23 typed-`J` captures in each (量, if the board sends at most 3,840 B/s;
  `CLK-44`). No interval here is anchored on `sent_s`.

## 6. The feature table (`D4`)

Two sources a column (`D4`). The vendor: its scripts, read from this unit's own root filesystem —
`$FWRE_WORK/extracted/unit-2018/squashfs-root`, `/etc/version`
`TOTOLINK-CX-N150RT-V2.1.6-B20171121.1002`, the tree `config/rlxfw-initramfs.tsv` carves rlxfw's
busybox and libraries from — with the compiled launcher `bin/sysconf` read by `strings`, never
run; and what ran, from the console (the nine vendor boots of each seating) and a TCP port census
(`V1-NMAP`, all 65,535 ports). rlxfw: the initramfs manifest (`p2q` and `p2l` carry the same
initramfs, content `51ea1604…`, card B § 1) and `ps` (`P1-PS`). Console counts are 量 over both
seatings' nine vendor boots, CR stripped, by one script run over both directories; seating B
reproduces seating A's count on every line.

| feature | vendor: started by (讀) | vendor: console line, n of 9 in A / B (量) | vendor: TCP port, A / B (量) | rlxfw: initramfs (讀) and `ps` (量) | class |
|---|---|---|---|---|---|
| a shell | none: `inittab` holds only `::sysinit:/etc/init.d/rcS`; its shell lines are commented out | no prompt; no vendor boot has answered a command (`P2` settled item 1) | — | `/init` execs `/bin/sh` as PID 1; `P1-PS`: `1 /bin/sh` | not comparable |
| web server `boa` | `rcS`'s last line | `boa: server version Boa/0.94.14rc21`, `boa: starting server pid=350, port 80`: 9 / 9 | 80 open / open | absent | not comparable |
| UPnP IGD `miniigd` | `sysconf` | `MiniIGD v1.09.1 (2018.01.10-06:58+0000).`: 9 / 9 | 52869 open / open (推 `miniigd`'s, § 5.2) | absent | not comparable |
| WPS `wscd` | `sysconf wlanapp` (`/bin/wscd`) | `WiFi Simple Config v2.18-wps1.0 …`: 9 / 9 | 52881 open / open (推 `wscd`'s, § 5.2) | absent | not comparable |
| WLAN driver | in the kernel | `Realtek WLAN driver - version 1.6 (2013-02-21)`: 9 / 9 | — | in the kernel, `driver version 1.6 (2012-12-04)` | comparable (`kernel.wlan`) |
| WLAN userspace `iwcontrol`, `iapp` | `sysconf` | `iwcontrol RegisterPID to (wlan0)`, `IEEE 802.11f (IAPP) using interface br0 (v1.8)`: 9 / 9 | — | absent; `wlan0` never comes up | not comparable |
| LAN bring-up | the NIC driver's probe in the kernel; `sysconf init` (switch, bridge) | `Probing RTL8186 10/100 NIC`, `Init bridge interface...`: 9 / 9 | — | the NIC driver's probe in the kernel; `/init` unlocks the switch and NIC and brings `rlx0` up at 10.1.1.3 | the probe comparable (`kernel.nic`; the drivers differ), the userspace bring-up not |
| bridge `br0` | `sysconf` | `Init bridge interface...`: 9 / 9 | — | none: no `brctl`; the address sits on `rlx0` | not comparable |
| DHCP server `udhcpd` | `sysconf` (`udhcpd /var/udhcpd.conf`) | only its restart's `killall: udhcpd: no process killed`: 9 / 9 | UDP 67, which a TCP census cannot see | absent | not comparable |
| DNS relay `dnrd` / `dnsmasq` | `sysconf` | none: 0 / 0 | UDP 53, not seen | absent | not comparable; not shown to run |
| `dnsspoof` | `sysconf`, on WAN disconnect | `wan_disconnect: StartDnsSpoof`: 9 / 9 | — | absent | not comparable |
| NTP client `ntpclient` | `sysconf ntp` | `Start NTP daemon`: 9 / 9 | no listener | absent | not comparable |
| IPv6 (`radvd`, `dhcp6s`, `dhcp6c`, `ndppd`) | `sysconf` | `Start setting IPv6[IPv6]`: 9 / 9 | — | absent | not comparable; which daemon starts is gated by the configuration |
| firewall, NAT | `sysconf firewall`; `rcS` sets the conntrack sysctls | none per rule | — | no netfilter userspace | not comparable |
| `syslogd`, `klogd` | `sysconf syslog` | none: 0 / 0 | — | not started | not comparable; not shown to run |
| `telnetd` | `sysconf`, gated on `TELNET_ENABLED`, which `startup.sh` sets only in its configuration-reset branch | none: 0 / 0 | 23 not open / not open | absent | not comparable; the branch was not taken |
| MIB and flash configuration (`flash`, `sysconf`) | `rcS`, `startup.sh` | `sysconf init gw all`, `sysconf wlanapp kill wlan0`: 9 / 9 | — | none: rlxfw has no MIB layer | not comparable |
| instruments carried, not run | — | — | — | `/bin/uprobe`, `/bin/ucost`, `/bin/iperf3`, and `/bin/mfgtest` (a shell script, `config/mfgtest.sh`); nothing runs them at boot | not comparable |

* 量 The census: `V1-NMAP` read 80, 52869 and 52881 open in both seatings (65,381 closed and 151
  filtered in A; 65,532 closed and 0 filtered in B); `P1-NMAP` read none open in both (58,989
  closed and 6,546 filtered in A; 57,296 and 8,239 in B — 推 RSTs that arrived after `nmap` gave
  up rather than missing ones, by block 45's E3, an analogy since neither scan had host counters,
  `NET-120`). `P1-PS` is the same set in both: `/bin/sh`, the kernel threads and `ps`.
* **`D4`'s refutation did not fire.** Every open port maps to a daemon the scripts start and the
  console announces, and every announced daemon traces to `rcS` or a `sysconf` launcher string.
  The reverse — `telnetd`, `syslogd`/`klogd`, `dnrd`/`dnsmasq`: launch strings present, never
  announced — is recorded as not shown to run, which is what the refutation asks for: the table is
  derived from what ran.

## 7. Throughput (`D5`)

### 7.1 ICMP echo, both firmwares (`D5` (a))

One host script: five payloads, 20 echoes at 50 ms each, one series per press — rlxfw on `P1`,
`P2`, `P3`, the vendor on `V1`, `V2`, `V3`. 量 600 of 600 echoes answered in each seating (0 %
loss in 30 of 30 series). Milliseconds; realtime kind, so (b) = (a).

| firmware, payload, statistic (ms) | n A/B | A raw | A corrected | B (RAW) | (a) | (b) | (c) | `D3` | LB |
|---|---:|---|---|---|---:|---:|---:|---|---|
| rlxfw, 56 B, avg | 3/3 | 1.586 (1.516…1.815) | = raw | 1.723 (1.401…2.305) | +8.64 % | +8.64 % | — | n.s., inside |  |
| rlxfw, 56 B, mdev | 3/3 | 0.682 (0.632…0.773) | = raw | 0.689 (0.369…1.844) | +1.03 % | +1.03 % | — | n.s., inside |  |
| rlxfw, 256 B, avg | 3/3 | 1.518 (1.367…1.641) | = raw | 1.792 (1.546…1.933) | +18.05 % | +18.05 % | — | **MISS** |  |
| rlxfw, 256 B, mdev | 3/3 | 0.920 (0.327…1.178) | = raw | 0.376 (0.308…0.796) | −59.13 % | −59.13 % | — | n.s., outside |  |
| rlxfw, 512 B, avg | 3/3 | 1.640 (1.618…1.736) | = raw | 1.743 (1.685…2.128) | +6.28 % | +6.28 % | — | hit |  |
| rlxfw, 512 B, mdev | 3/3 | 0.401 (0.375…0.496) | = raw | 0.387 (0.158…0.388) | −3.49 % | −3.49 % | — | n.s., inside |  |
| rlxfw, 1024 B, avg | 3/3 | 2.086 (2.030…2.124) | = raw | 2.020 (1.889…2.455) | −3.16 % | −3.16 % | — | hit |  |
| rlxfw, 1024 B, mdev | 3/3 | 0.509 (0.446…0.591) | = raw | 0.394 (0.310…0.448) | −22.59 % | −22.59 % | — | n.s., outside |  |
| rlxfw, 1472 B, avg | 3/3 | 2.139 (2.052…2.252) | = raw | 2.399 (2.364…2.720) | +12.16 % | +12.16 % | — | **MISS** |  |
| rlxfw, 1472 B, mdev | 3/3 | 0.476 (0.462…0.508) | = raw | 0.555 (0.266…0.622) | +16.60 % | +16.60 % | — | **MISS** |  |
| vendor, 56 B, avg | 3/3 | 1.516 (1.504…1.710) | = raw | 1.197 (1.149…1.517) | −21.04 % | −21.04 % | — | n.s., outside |  |
| vendor, 56 B, mdev | 3/3 | 0.708 (0.384…0.988) | = raw | 0.231 (0.170…0.365) | −67.37 % | −67.37 % | — | n.s., outside |  |
| vendor, 256 B, avg | 3/3 | 1.895 (1.653…2.180) | = raw | 1.406 (1.384…1.851) | −25.80 % | −25.80 % | — | n.s., outside |  |
| vendor, 256 B, mdev | 3/3 | 0.723 (0.465…2.080) | = raw | 0.287 (0.250…0.511) | −60.30 % | −60.30 % | — | n.s., outside |  |
| vendor, 512 B, avg | 3/3 | 1.644 (1.580…1.843) | = raw | 1.323 (1.209…1.666) | −19.53 % | −19.53 % | — | n.s., outside |  |
| vendor, 512 B, mdev | 3/3 | 0.370 (0.327…0.922) | = raw | 0.293 (0.100…0.353) | −20.81 % | −20.81 % | — | n.s., outside |  |
| vendor, 1024 B, avg | 3/3 | 1.782 (1.743…1.998) | = raw | 1.347 (1.338…1.626) | −24.41 % | −24.41 % | — | n.s., outside |  |
| vendor, 1024 B, mdev | 3/3 | 0.472 (0.418…1.325) | = raw | 0.195 (0.165…0.278) | −58.69 % | −58.69 % | — | n.s., outside |  |
| vendor, 1472 B, avg | 3/3 | 1.690 (1.656…1.956) | = raw | 1.490 (1.372…1.610) | −11.83 % | −11.83 % | — | n.s., outside |  |
| vendor, 1472 B, mdev | 3/3 | 0.334 (0.280…0.402) | = raw | 0.169 (0.106…0.195) | −49.40 % | −49.40 % | — | n.s., outside |  |

* 量 Three stable rlxfw rows miss — 256 B average +18.05 %, 1472 B average +12.16 %, 1472 B mdev
  +16.60 % — while every vendor row is lower on day B by 11.8–25.8 % in its average (`NET-121`;
  § 10). 推 an mdev of 20 echoes carries about 16 % sampling error of its own (§ 10).

### 7.2 `iperf3` through the vendor's driver on rlxfw's kernel, `eth4` (`D5` (b))

`iperf3` 3.1.3, the host's client (TCP `-t 30 -i 5`, UDP `-l 1400 -b 20M -i 1`) against the
board's server — in seating B a one-off server per trial with its own log — three trials each:
`ER` TCP board receives, `ES` TCP board sends, `EU` UDP board receives, `EV` UDP board sends (card
B § 3.5). Board CPU from `/proc/stat` read before and after each trial. 量 12 of 12 trials
completed in each seating.

| trial set (card B § 3.5) | n A/B | A raw | A corrected | B (RAW) | (a) | (b) | (c) | `D3` | LB |
|---|---:|---|---|---|---:|---:|---:|---|---|
| `ER`, TCP board receives, Mbit/s | 3/3 | 24.7 (24.4…25.0) | = raw | 24.572 (23.923…24.653) | −0.52 % | −0.52 % | — | hit |  |
| `ES`, TCP board sends, Mbit/s | 3/3 | 26.2 (26.2…26.2) | = raw | 26.1 (25.8…26.2) | −0.38 % | −0.38 % | — | hit |  |
| `EU`, UDP board receives, received Mbit/s | 3/3 | 5.957 (5.956…5.958) | = raw | 6.141333 (6.141333…6.146187) | +3.09 % | +3.09 % | — | hit |  |
| `EU`, UDP board receives, lost % | 3/3 | 70.061 (70.057…70.066) | = raw | 69.136382 (69.11315…69.13754) | −1.32 % | −1.32 % | — | n.s., inside |  |
| `EV`, UDP board sends, Mbit/s | 3/3 | 19.9 (19.9…20.0) | = raw | 20.0 (20.0…20.0) | +0.50 % | +0.50 % | — | hit |  |
| `ER`, board CPU busy % | 3/3 | 54.66 (53.55…55.66) | = raw | 50.17 (47.35…74.03) | −8.21 % | −8.21 % | — | hit |  |
| `ES`, board CPU busy % | 3/3 | 89.79 (89.75…89.82) | = raw | 86.87 (86.85…87.09) | −3.25 % | −3.25 % | — | hit |  |
| `EU`, board CPU busy % | 3/3 | 38.37 (38.21…38.41) | = raw | 35.53 (35.08…35.74) | −7.40 % | −7.40 % | — | hit |  |
| `EV`, board CPU busy % | 3/3 | 81.72 (81.37…82.16) | = raw | 78.83 (77.17…79.71) | −3.54 % | −3.54 % | — | hit |  |

* 量 Every rate and every CPU median reproduces. `ER`'s CPU, −8.21 %, is the nearest any stable row
  came to the edge: every eth4 `/proc/stat` window of seating B is 3.1–3.4 % longer, about 1.1 s
  all idle, so about 3.3 points of each eth4 CPU drop is the bracket the procedure sets, not the
  board; `ER3` read 2,499 softirq ticks against 1,610 and 1,689 with the same IRQ 12 count, for a
  reason not established.
* The `ER` rate's seating-A values are the host receiver lines (0.1 Mbit/s steps) while seating B's
  rule reads the board server's figure; in seating B the two differ by 0.028 Mbit/s in their
  medians and by up to 0.047 Mbit/s in a single trial (`ER2`).

### 7.3 `iperf3` through rlxfw's driver, `rlx0`

The same twelve trials on `rlx0`, which loses frames it reports as sent (`NET-112`). None of these
rows is stable: the list names every failed trial not stable before power (card B § 3.10).

| `rlx0` quantity (card B § 3.5) | n A/B | A raw | A corrected | B (RAW) | (a) | (b) | (c) | `D3` | LB |
|---|---:|---|---|---|---:|---:|---:|---|---|
| `TR`, host sender Mbit/s per 5 s interval | 15/5 | 17.3 (15.3…17.9) | = raw | 17.0 (16.9…17.6) | −1.73 % | −1.73 % | — | n.s., inside |  |
| `TR`, the board server’s receiver Mbit/s | 0/1 | — | — | 16.953 | — | — | — | first reading |  |
| `TR`, board CPU busy % | 3/1 | 20.46 (16.65…29.58) | = raw | 28.39 | +38.76 % | +38.76 % | — | n.s., outside |  |
| `UR`, board CPU busy % | 2/2 | 33.13 (33.11…33.15) | = raw | 32.965 (32.63…33.30) | −0.50 % | −0.50 % | — | n.s., inside |  |
| `US`, board CPU busy % | 1/2 | 39.45 | = raw | 39.07 (39.04…39.10) | −0.96 % | −0.96 % | — | n.s., inside |  |
| `UR`, datagrams the host sent | 2/2 | 53514.5 (53504…53525) | = raw | 53543 (53521…53565) | +0.05 % | +0.05 % | — | n.s., inside |  |
| `UR`, datagrams the board’s server received | 0/2 | — | — | 6745 (6431…7059) | — | — | — | first reading |  |
| trials of 12 that connected and never finished the exchange | 1/1 | 6 | = raw | 5 | −16.67 % | −16.67 % | — | n.s., outside |  |
| trials of 12 that could not connect | 1/1 | 3 | = raw | 6 | +100.00 % | +100.00 % | — | n.s., outside |  |
| `recover`, `n_tx_stop` over the twelve | 1/1 | 7 | = raw | 6 | −14.29 % | −14.29 % | — | n.s., outside |  |
| `recover`, `n_writes` over the twelve | 1/1 | 112 | = raw | 96 | −14.29 % | −14.29 % | — | n.s., outside |  |
| `NET-112`, frames counted sent − frames the switch emitted | 1/1 | 182 | = raw | 128 | −29.67 % | −29.67 % | — | n.s., outside |  |
| `NET-112`, bytes counted sent − bytes emitted | 1/1 | 23692 | = raw | 11935 | −49.62 % | −49.62 % | — | n.s., outside |  |
| `NET-112`, frames into port 3 − `n_rx` | 1/1 | 0 | = raw | 2 | — | — | — | n.s., 0 |  |

* 量 In seating B **0 of 12 trials completed**: five connected and never finished the end-of-test
  exchange, six met `No route to host`, one hung before its parameter exchange (seating A: six
  failed exchanges, three could not connect). `TR1`'s board server logged 16.953 Mbit/s received
  over 30.01 s, the first rlxfw TCP receive figure (n = 1). `UR1`/`UR2` lost 87.8 % and 86.6 % of
  their datagrams at the board's server while the driver counted as many frames in as the host sent
  (`NET-116`, `NET-117`, `notes/nic-driver.md` § 20).
* No `rlx0` figure is a throughput result of rlxfw's driver; the driver's TX path is `R6b`'s
  (`NET-119`, `NET-120`).

### 7.4 The switch counters beside it (`NET-109`)

Read at `P1-AC0`, right after `P1-N0`, before any `rlx0` trial.

| switch counter at `P1-AC0` (`NET-109`) | n A/B | A raw | A corrected | B (RAW) | (a) | (b) | (c) | `D3` | LB |
|---|---:|---|---|---|---:|---:|---:|---|---|
| CPU port `CRCAlignErr` | 1/1 | 294 | = raw | 414 | +40.82 % | +40.82 % | — | **MISS** |  |
| port 3 egress unicast | 1/1 | 294 | = raw | 414 | +40.82 % | +40.82 % | — | **MISS** |  |
| `CRCAlignErr` − port 3 egress | 1/1 | 0 | = raw | 0 | — | — | — | n.s., 0 |  |
| CPU port `Rcv` bytes | 1/1 | 0 | = raw | 0 | — | — | — | n.s., 0 |  |
| `CpuEvent` | 1/1 | 0 | = raw | 0 | — | — | — | n.s., 0 |  |

* 量 The healthy shape held in both seatings — CPU port `Rcv` 0 bytes, `CRCAlignErr` equal to
  port 3's egress — while the count itself went 294 → 414, two stable misses that are the length of
  the host's echo run, not a device quantity (§ 10).

## 8. Sizes and memory (`D6`)

| | vendor | rlxfw `p2q` (quiet) | rlxfw `p2l` (loud) |
|---|---|---|---|
| image the loader jumps to (讀) | `cr6c` header and LZMA kernel, 987,138 B (`upstream/notes/flash-layout.md`) | 1,155,072 B, kernel and initramfs in one rtkload image (card B § 1) | 1,181,696 B (card B § 1) |
| kernel ELF, uncompressed (讀) | not read | 4,468,487 B with the initramfs (build manifest) | 4,575,403 B (build manifest) |
| root filesystem (讀) | SquashFS 4.0, LZMA, 1,876,033 B used, 567 inodes (`upstream/notes/flash-layout.md`) | the initramfs inside the image: 912,600 B of file content — `busybox` 273,332 and uClibc, `ld` and `libgcc` 306,312 from this unit's tree, four instruments 330,803, `/init` 2,153 (`p2q.initramfs.manifest.tsv`) | the same initramfs |
| `MemTotal` after boot (量, `MEM-20`) | ⊘, no shell | 26,984 kB, both seatings | not read |
| `MemFree` after boot (量, `MEM-20`) | ⊘ | 20,932 kB (A), 20,924 kB (B) | not read |

| rlxfw, after boot (kB) | n A/B | A raw | A corrected | B (RAW) | (a) | (b) | (c) | `D3` | LB |
|---|---:|---|---|---|---:|---:|---:|---|---|
| `MemTotal` | 1/1 | 26984 | = raw | 26984 | — | — | — | exact, hit |  |
| `MemFree` | 1/1 | 20932 | = raw | 20924 | −0.04 % | −0.04 % | — | hit |  |
| `busybox free`, used | 1/1 | 6012 | = raw | 6028 | +0.27 % | +0.27 % | — | hit |  |

* The images differ in kind as well as size: the vendor stages its kernel alone and mounts a
  separate SquashFS; rlxfw carries its whole userspace inside the kernel image. `rtkload.decompress`
  (class comparable) is timed on 987,138 B against 1,155,072 and 1,181,696 B.
* 量 `MemFree` is one reading after one boot sequence per seating, not a steady state; the vendor's
  runtime memory is ⊘ by structure (`P2` settled item 1).

## 9. Method

### 9.1 The instruments

* **`tools/boot-timeline.py`** (`FW-117`) — landmarks and segments are data: three landmark tables
  and one segment table; one function computes every segment for both firmwares, and the firmware
  only selects the table (`D1`). `--retro DIR --tsv FILE` over a seating's directory wrote its
  `Z9-D2.tsv`. 量 today's run over seating B equals the bench night's byte for byte, and a parser
  that shares no code with the tool agrees on 52 of 52 loader records, 208 of 208 segment records
  and 223 of 223 landmarks (`notes/boot-time.md` § 8.5).
* **`tools/console-capture.py` 1.5** (`FW-115`) — every stamp and deadline on `CLOCK_MONOTONIC_RAW`,
  the origin in `t0_raw`; a byte's time is the last `.timing` row at or before it (`FW-35`). Its
  `--until` reads on for 0–50 ms after the match, which is why one map capture ended 4 bytes short
  (`FW-135`, `FW-136`, § 10).
* **`tools/hostprobe.py` 1.3** (`FW-116`) — the first ICMP reply, the first TCP success on each of
  ports 80, 52869 and 52881 (a 0.2 s connect grid per port), the neighbour table, and UDP arrivals,
  each on `t_raw`. `D8` and `D4` here are joined by the card's rule, which reads every event after
  `J`; `boot-timeline --probe` counts only events inside the capture's window and returns no network
  up for 7 of seating B's 11 rlxfw rounds, which end at the prompt (`FW-137`), and agrees to the
  microsecond where it reads.
* **`tools/looprun.py` 1.3** — rounds per press; `S9` holds each round 2.5 RAW seconds past its
  prompt (`FW-127`). **`tools/hostclock.py` 1.0** — the host clock log (`Z0-HC.clock`) and the
  conversion of `tcpdump`'s realtime stamps onto RAW (0 of 3,051 frames refused).
  **`tools/iperflog.py`** — parses and compares the board's and the host's `iperf3` logs; its
  positive control read AGREE on 6 of 6 `eth4` trials, refused 8 of 8 crossed pairs, and read
  DISAGREE on a one-step edit.

### 9.2 One clock

* Seating A stamped on `CLOCK_MONOTONIC`, which WSL's `chronyd` slewed against `systemd-timesyncd`
  (`CLK-38`); the corrected column divides it out (§ 1).
* 量 Seating B stamped every capture, probe and clock-log row on `CLOCK_MONOTONIC_RAW` inside one
  WSL boot (179 metadata files, one `boot_id`, clocksource `tsc` at both ends), with `timesyncd`
  stopped for the seating. The kernel's tick never read 10,000 in 11,372 rows and no step occurred;
  `CLOCK_MONOTONIC` ran +3.6 to +40.9 ppm fast of RAW per press, so a host timer — an ARP
  retransmit, `ping -i` — of 10 s lasted 9.99959–9.99996 RAW seconds; board-timed intervals are on
  RAW and untouched (`CLK-41`).
* 量 Inference (iii) holds (`CLK-43`): seating B's warm `loader.booting` median on RAW, 0.356060 s
  (n 13), lies inside [0.354469, 0.358031] s, 0.027 % above seating A's corrected 0.355963 s. So
  between seatings A and B `CLK-32`'s factor was the host's clock, and column (b) is the comparison
  the device reproduces; (a) carries the host. For earlier directories the factor stays 推.
* Not established: RAW against true time in seating B's WSL boot (no reference was logged; card B
  § 3.0's "about 50 ppm" is 推), and so whether the board's post-loss rate of 100.002869 ticks per
  RAW second is the board's error or RAW's (`notes/boot-time.md` § 8.3).

### 9.3 The `D3` contract: `docs/boot-time-d3-list.tsv`

The closing rule (`PROGRESS.md`, `P2`'s refutation conditions, committed in `e2f15ff` before any
seating-B interval was computed) and the list (`76deef8`, committed before any seating-B value of a
listed number was read). The list was generated from seating-A files only by two builders sharing no
code, their differences adjudicated from the source files, and six rulings, each written in the
row's `adjudication` column, settled what the rule's text left open. One row per number, 22
columns: among them the seating-A values with their raw median and range, the corrected median and
the rule that made it, the `stable` class with its `reasons`, `load_bearing`, the seating-B rule
(`B_rule`) and the seating-A source.

* **Stable** (the closing rule's (1)): not listed as unstable by card B § 3.10; seating A's own
  values within ±10 % of their median (the larger of |max/median − 1| and |1 − min/median| below
  0.10); seating A's range not containing 0; and not under 20 ms. 量 of 294 rows: 140 stable, 110
  not, 29 exact (clock-free predictions, card B § 3.2), 15 first readings.
* **The rulings.** R1 (10 rows): a pooled or per-mode row is scored beside the per-class cells and
  is not load-bearing, since `D3` puts cold and warm in separate tables. R2 (20): the 20 ms
  criterion names the two `FW-35` read quanta at an interval's ends, so it does not fire on `ping`'s
  own rtt. R3 (3): a discrete k is scored exactly. R4 (3): a bracket width for k ≥ 2 is fixed by the
  reconstruction and cannot fail, so it is not a reproduction. R5 (5): a port scan is not a boot
  interval; `rlx0`'s board-sends figures are listed. R6 (1): the quiet cold bracket width is kept
  stable at n = 1, its (a) expected to miss.
* **Load-bearing** (the closing rule's (2)): a boot segment per firmware, variant and class, `J` →
  prompt, the vendor's `J` → `boa`, rlxfw's `J` → `N-NDOPEN`, the vendor's port-80 readiness from
  `J`, and `D7`'s Δ — 69 stable rows: 62 segment cells, four `J` → `N-NDOPEN`, two port-80 cells
  and `D7`'s Δ.
* **Defects found after the scoring**, which the rule's (4) forbids acting on: the quiet cold
  bracket width can never hit, because its raw and corrected seating-A values are 2.04 apart — the
  windows (a) and (b) allow do not overlap; the `NET-109` counts and `D6`'s `MemFree` and `free`
  `used` are stable because a single reading has no spread, though card B § 3.6 had said the
  `NET-109` count is not predicted; `D5a|rlxfw|256|avg` passed the spread criterion by 0.05 points
  (spread 0.099473).

### 9.4 The score: `docs/boot-time-d3-score.tsv`

The judge's `final-score.tsv`, copied byte for byte: 294 rows in the list's order, 20 columns —
`id`, `family`, `class`, `kind`, `stable`, `load_bearing`, `A_raw_median`, `A_corr_median`, `B_n`,
`B_median`, `a`, `b`, `c_raw`, `c_corr` (seating A normalised by its corrected warm median,
0.355963 s), `verdict`, `edge`, `closing_rule`, and the two scorers' verdicts and their agreement.

* **Three scorers.** Two scored the list independently; a third, the judge, scored it again with
  exact fractions and refuses to run unless the list's digest is `76deef8`'s and the two scorers'
  seating-B values are identical. 量 all three agree on every verdict, and on (a) and (b) to 10⁻⁶.
  Controls: a planted miss on a load-bearing row turns the verdict to "`P2` stays open"; +10 %
  exactly scores a hit and 10⁻⁹ past it a miss.
* **What their agreement is not.** The three share one set of seating-B values, the primary
  readings. Each family was read a second time by a job sharing no code with its primary: of the
  rows both read, timing agreed on 102 of 102, network up on 71 of 72, services on 52 of 54,
  throughput on 67 of 67 and clocks on 12 of 16. Where they disagreed on a list row — one error
  line read 1.6 ms late in network up, two medians rounded through binary floats in services, one
  tick rate and the tick shortfall in clocks — the second reading's `RESULT.json` says which was
  right, and the score's values are that one, with one exception in print: `D4|ok-line|warm`, a
  row that is not stable, prints `B_median` 0.008505 where the second reading gives 0.008506,
  its exact median 0.0085055 printed through a binary float (*Rounding*, below).
* **Rounding.** An even-n median is the mean of the two middle values. `B_median` is printed from
  that exact value through a binary float, so of the 42 rows whose exact median ends in half a
  microsecond, 22 print a last digit other than half-even's; (a), (b) and (c) are computed from
  the exact median, and no verdict lies within a microsecond of an edge. The list's seating-A
  medians carry the same convention. The tables in this file recompute seating B's medians from
  the values and round them half-even.
* 量 The file holds no hardware address: `tools/audit-bench-log.py` reads 0 hits and 1
  allowlisted match, the bench address `10.1.1.4` in the `P1-ETH4` row, whose MAC the scorer
  compared and did not print.

### 9.5 Enumerating the vendor's root filesystem (`GREP-1`, `FW-141`)

The feature table reads the vendor's extracted SquashFS. Of its 88 symbolic links, 50 point to
`busybox`, 21 are absolute links into `/var` and `/tmp` that dangle — their targets are created at
boot — and one more absolute link, `./tmp -> /var/tmp`, resolves on the analysing host to the
host's own directory. 量 over the tree:

| enumerator | entries | what the difference is |
|---|---:|---|
| `find .` | 269 | 161 regular files, 88 symbolic links, 20 directories — the inventory |
| `find -L .` | 278 | +9, all under `./tmp`: the absolute link resolves against the analysing host's root, so `-L` lists four of the host's own log files and five of its `systemd-private-*` directories, and its five lines of standard error are permission refusals from those host directories |
| `grep -rl ''` | 161 | every non-empty regular file; links are not followed |
| `grep -Rl ''` | 231 | +70: the 50 `busybox` links re-read as the `busybox` binary, 16 other resolvable links (`udhcpc`, `./init`, 14 under `lib/`), and the four host files under `./tmp` |

**The rule.** The inventory is `find` without `-L`, every symbolic link listed with its target;
`find -L` runs only beside it, and its excess is reconciled entry by entry; `grep -r` and `grep -R`
never enumerate. `-r` skips links, which on the SDK tree hid the whole BSP behind a relative link
(`GREP-1`); `-R` follows them, which on an extracted root filesystem leaves the tree through an
absolute link.

* The SquashFS superblock counts 567 inodes (`upstream/notes/flash-layout.md`) against 269 entries
  extracted: an unprivileged extraction creates no device nodes (量, its log refuses each one). The
  difference is not reconciled here.

## 10. `D3`, applied

| family | rows | stable, hit | stable, miss | exact, hit | exact, miss | not stable | first reading |
|---|---:|---:|---:|---:|---:|---:|---:|
| `SEG` | 75 | 69 |  |  |  | 6 |  |
| `SEG+` | 1 |  |  |  |  | 1 |  |
| `D2G` | 7 | 5 |  |  |  | 2 |  |
| `D2D` | 6 |  |  |  |  | 6 |  |
| `D7` | 5 | 5 |  |  |  |  |  |
| `D8` | 71 | 31 | 1 | 3 |  | 27 | 9 |
| `D4` | 22 | 6 |  | 3 |  | 11 | 2 |
| `D6` | 3 | 2 |  | 1 |  |  |  |
| `D5a` | 30 | 2 | 3 |  |  | 25 |  |
| `D5b` | 37 | 8 |  |  |  | 26 | 3 |
| `NET109` | 5 |  | 2 |  |  | 3 |  |
| `CLK` | 2 |  |  |  |  | 1 | 1 |
| `VEND` | 8 | 6 |  |  |  | 2 |  |
| `EXACT` | 22 |  |  | 20 | 2 |  |  |
| all | 294 | 134 | 6 | 27 | 2 | 110 | 15 |

**The closing rule, row by row.** (1) Stability was decided from seating A only and was not changed.
(2) No stable miss is a load-bearing row: all 69 hit, the largest |a| 6.712 % and |b| 5.229 % on the
loud cold `rlxfw.setup`, whose seating-B value carries the late read of § 2. (3) The six stable
misses are published here with both columns and carried forward as one row, `D3-MISS`, naming the
experiment that decides each; `PROGRESS.md` § Carried forward says who holds which part. (4) No
number changed class, and ±10 % was not widened. **`P2` closes.**

| stable miss | A raw | A corrected | B | (a) | (b) | what it is | the experiment that decides it |
|---|---|---|---|---:|---:|---|---|
| `D8\|width\|quiet\|cold` | 0.187804 (n 1) | 0.091986 | 0.104598 (n 2) | −44.30 % | +13.71 % | the host's ARP phase against `N-NDOPEN`, not a board quantity; (a) cannot hit (§ 9.3); in (b), `P3Q-r01` has no seating-A partner, and `P2Q-r01` alone reads +2.79 %; the frames put `P3Q-r01`'s answered broadcast at `N-NDOPEN` + 0.103173 s, 11.5 ms before the midpoint the rule uses | a third day on RAW, compared with seating B, with frames on every cold quiet boot |
| `D5a\|rlxfw\|256\|avg` | 1.518 ms | = raw | 1.792 ms | +18.05 % | +18.05 % | rlxfw's rtt up while the vendor's went down 11.8–25.8 % (`NET-121`) | the same ICMP series, at least five with the host's `tcpdump` running and five without, interleaved inside one rlxfw boot, with vendor series in the same seating |
| `D5a\|rlxfw\|1472\|avg` | 2.139 ms | = raw | 2.399 ms | +12.16 % | +12.16 % | as above | as above |
| `D5a\|rlxfw\|1472\|mdev` | 0.476 ms | = raw | 0.555 ms | +16.60 % | +16.60 % | as above; 推 a ±10 % band on the median of three 20-echo standard deviations is narrower than the statistic's own sampling error, about 16 % | as above |
| `NET109\|crcalignerr` | 294 | = raw | 414 | +40.82 % | +40.82 % | the echo replies the host's probe drew inside the last boot, plus two — 292 + 2 and 412 + 2 — a run length, not a device quantity | none: redefine it as the per-echo identity, which held, 414 = 414 |
| `NET109\|p3egress` | 294 | = raw | 414 | +40.82 % | +40.82 % | as above | as above |

* 量 **The rtt rows.** Not `ping`'s own userspace: the capture's frame stamps sit 0.025–0.043 ms
  below `ping`'s averages in both seatings, and the `P3`-against-`P3` pair, both series run under
  `tcpdump`, moves +18.1 % (256-B payload) and +12.3 % (1,472-B) at the frame level, while the
  floors hardly move (1.021 against 1.080 ms, 1.419 against 1.466 ms). Split by whether the
  host's `tcpdump` ran: off, +7.2 % and +9.9 %; on, +13.5 % and +19.7 % (n = 1–2 each). Seating B
  ran two of its three rlxfw series under `tcpdump`, seating A one; the vendor's series never ran
  under it. 推 the host's capture is part of the shift and not all of it: the pair captured on
  both days still moves, and the 1,472-B mdev misses without a capture too (+14.4 %); not tested.
* 量 **The two exact misses**, not device quantities (card B § 3.2): `P2-M0`, one of seating B's
  three flash-map captures, is 3,009 B where 3,013 were predicted, and its body digest reads
  `1de86c73…` where `0927be41…` was. `--until` stopped reading 0–50 ms after its match
  (`FW-135`) before the final line's CR LF and the prompt arrived, and the card's digest hashes
  that last terminator (`FW-136`); its 34-line map section is byte-identical to `P1-M0`'s,
  `P3-M0`'s and seating A's `P3-M0`'s, and with `awk 1` before `sha256sum` all six maps of both
  seatings read `0927be41…`.
  The flash those maps compare is `FLS-31`'s.

## 11. What `P2` did not establish

* **Interrupt latency by logic analyser** — the plan's *中斷延遲（LA 量）*. `P2-6` never ran, and by
  `P2`'s stop-loss the on-die counter does not stand in for it under that name; carried forward as
  `LA-1`.
* **The vendor's throughput, CPU and memory beyond ICMP**: `iperf3`, `/proc` and per-daemon CPU on
  the vendor firmware are ⊘ — it has no shell. The vendor's published ~94 Mbit/s is NAT forwarding
  and is compared with nothing here.
* **rlxfw's throughput**: no `rlx0` trial completed in seating B, and `TR1`'s 16.953 Mbit/s is one
  trial; the loss is `NET-112`'s, and the driver's TX path is `R6b`'s.
* **Where network came up**: every network-up figure is a console-side bound; the vendor's brackets
  are 1.03–1.10 s wide and rest on a reconstruction no frame on a vendor press checks.
* **Power-on → `Booting...` and the root filesystem's mount**: no instrument stamps the power press,
  and neither landmark table has a line for a mount; rlxfw has none to do.
* **A total.** "Boots faster" is not a claim this table makes: past the kernel the two firmwares do
  different work (§ 6), and only the segments marked comparable compare builds.
* **Which daemon owns 52869 and 52881** on this unit, beyond timing and an SDK drop; UDP services,
  which a TCP census cannot see; the configuration-gated branches of `sysconf`, whose MIB was not
  decoded.
* **Time beyond RAW**: RAW against true time in seating B, and whether the board's tick or RAW
  carries their 28.7 ppm difference.
* **`D3` beyond two days**: one unit, one host, one bench, two calendar days; ±10 % is the plan's
  tolerance, not the method's resolution, and column (b) rests on seating A's derived correction,
  uncertain by ±0.3–0.8 % at a cold catch's loader instant.
* **The flash across the seatings**: each map compares 32 digests over 4,186,112 of 4,194,304 bytes,
  cannot see two writes that cancel, and does not read `H601` (`FLS-30`, `FLS-31`).
* **The ticks rlxfw lost**: about 105 jiffies again, between `P1-N0` and the first trial, in both
  seatings; the cell that costs them is 推 (`CLK-42`).
