# Block 15 — `R5-6` second bench: a rate derived on the die, and a ladder with two degrees of freedom

**Written 2026-09-09, forty-seventh segment, at the desk, before power.**
Seating 18, **one power cycle**, thirteen boots, twelve of which end in a
watchdog bite.

**Freeze order, and it is not optional** (`RUNSHEET.md` § *Four rules about the
card's lifecycle*):

1. **rule 4** — re-derive `RECIPE_ID` and compare with §1. If it moved, the
   image is stale and is **rebuilt**; the card is not edited to match.
2. **rule 1** — `tools/spec-check.py` green, `rc 0` read from a script file and
   not from a pipeline (`CLAUDE.md`'s `EXIT CODE: 0` incident).
3. `cardcheck commands` — every command invocable.
4. `cardcheck numbers` — every stated number re-derivable.
5. `check-predictions` — **`0 of 27`**, because no capture exists yet.
6. **rule 3** — the directory name is a **prediction** until a capture lands in
   it. It is `bench/2026-09-09`, which asserts *the first capture happens before 00:00
   on 2026-09-10*. This card was written at 03:05 on 2026-09-09, so the
   assertion has 21 hours of slack; if the seating slips past 23:50 the
   directory is renamed and §5's fence re-derived **before** the freezing
   commit. `tools/capdate.py` is what checks this afterwards, and it exists
   because three consecutive seatings got it wrong and a human caught all
   three.

---

## 0. What this block is, in one paragraph

`rtl819x-wdt` **1.1** derives the watchdog's counting rate **on the die at
`init`**, from `TC0DATA` and `CDBR`, by two routes that must agree — the way
`rtl819x-timer` derives `hz_used` (`CLK-17`, 2026-09-04) — and reports it
through `/proc` **without touching `rtl819x_wdt_steps[]`**, which is what a
frozen card predicts against. Nothing the driver *acts* on changes: `hw_ovsel`
and `kick_ms` are module parameters and neither reads `RTL819X_WDT_HZ` (量).
So 1.1's behaviour is 1.0's, and §3.1 turns that into a control. The seating
then takes a **four-rung** timing ladder where seating 17 had two, closes
`FLS-26`'s attribution bracket on its first command, scans the eight bits of
`WDTCNR[23:16]` with five positive controls in the scan, and separates a
hypothesis about the **host's clock** that nothing in this repository has ever
bounded to better than 300 ± 170 ppm.

---

## 1. The image, staged and pinned

| | |
|---|---|
| cell | `r57` |
| `RECIPE_ID` | **`f67eed22`** — the board must print `RLXFW-ID0=F67EED22` |
| `vmlinux` | 4,049,730 bytes, sha256 `ef7e8b57a46e06595d2516a4bb86611b93bec687a01ef0abb3de16d90dfc2254` |
| staged image | `/home/key/fwre-work/rebuild/bench-only/r57-20260909/rlxfw-r57-20260909.bin` |
| image bytes | **1,043,456** |
| image sha256 | **`efc2ae0d604f8898d4011280958ea9093aad76d4a6ea922ccc32f791f2b6bd91`** |
| marks | 21 declared, 12 present once, 5 witnesses, 1 confirmed absent |
| host-compat patches | 5 |

🟢 **Rule 4's three sources all ran at the desk and all say `f67eed22`**: the
by-hand formula over `config/` (`find config -type f -print0 | LC_ALL=C sort -z
| xargs -0 sha256sum | sha256sum | cut -c1-8`), the build's own
`manifest.tsv`, and `--dry-run`.

🔴 **The tree was `b58f0903` at the segment's open and `f67eed22` at the
build, and both are correct.** `d4dddb3` (2026-09-09 01:55) recorded that the
tree had moved away from `b417a3e7` — the image seating 17 actually ran —
when the driver header's refuted claims were corrected. This segment then
moved it again, twice: the seven remaining stale claims in the header, and
`config/rlxfw-kernel.delta`'s reason string. **`RECIPE_ID` is a sha256 over
every file under `config/`, comments included**, so a comment-only edit moves
it, and that is the property being relied on rather than tolerated.

🟢 **The initramfs is a determinism control that cost nothing.** It was
regenerated from `config/rlxfw-initramfs.tsv` into a fresh directory and came
out **byte-identical** to `r56c`'s — sha256 `54dc0983785ab82d`, 33 entries —
so the only thing that moved between `r56c` and `r57` is the driver source.

🟢 **Post-build gates, all green before this card was written**: `(NEW)` = **0**
in `oldconfig`; `kconfig-delta check` **23 derived + 22 set, 0 undeclared**;
`rlxfw-marks verify` **12 marks present once, 5 witnesses, 1 confirmed absent,
absent from the vendor artefact**; zero compiler warnings in any file of mine.

⚠️ **The image is the same 1,043,456 bytes as `r56c`'s and a different
sha256.** `nfjrom` is 512-aligned and `vmlinux_img.gz` moved by less than the
padding, so the byte count is not evidence of anything and is recorded here so
that nobody reads it as evidence later.

---

## 2. What is being claimed, and what would refute it

| # | claim | refuted by |
|---|---|---|
| 1 | A driver of mine derives a hardware rate on this die at `init` and reports it | `hz_derived` reading 0, or `hz_agree` 0, in any `/proc` dump |
| 2 | The derivation is **report-only** — 1.1 behaves exactly as 1.0 | any boot capture that is not **1,424 bytes** |
| 3 | The watchdog does **not** count at the timer block's rate | a four-rung fit whose `f` lands within the floor of 200,000 Hz |
| 4 | The 0.09 % is not the host's clock | `Δjiffies × 10 ms ÷ Δt_host` differing from 1 by more than ~50 ppm |
| 5 | `FLS-26`'s 4 MiB is unchanged across a vendor-firmware run | any group of `C1-M0`'s 32 differing from seating 17's, other than group 0 |
| 6 | The flash difference is one erase sector | more than one differing unit in `C1-M1`'s 32 |
| 7 | `OVSEL[2]` is not at bit 19 or 20, and the scan can find where it is | a control bit (18/19/20/21/22) missing its prediction |

---

## 3. Predictions written before power

### 3.1 The boot capture — **1,424 bytes**, and it is a CONTROL this time

量, seating 17's ten committed boot captures: **all ten are 1,424 bytes**, they
fall into three sha256 values, and **the whole difference is one byte** —
`RLXFW-TA5`'s last hex digit (`FFFF8D38` against `FFFF8D37`), which is `jiffies`
at `clockevents_register_device()` and moves ±1 jiffy across boots.

**So the prediction is sharper than a byte count.** Every `C*-boot.log` this
seating is:

* **1,424 bytes**, and
* byte-identical to `bench/2026-09-08b/C1-boot.log` **except** (a) the eight
  characters of `RLXFW-ID0` — `B417A3E7` becomes `F67EED22` — and (b)
  `RLXFW-TA5`, already 量 to move ±1 jiffy.

🔴 **This is the control on claim 2 and it is why `WDT-1` emits no mark.** A
derived rate is a `/proc` read away; nothing at boot depends on it; and adding
a mark would have spent the one cheap measurement that says the driver's
behaviour did not change. `vmlinux` grew 233 bytes and the capture must not
grow at all.

### 3.2 `WDT-1`'s seven fields at `C1-P`

Derived from the two registers `TM-1` measured under Linux on 2026-09-03
(`CDBR` `0x03E80000` = ÷1000 where the loader left ÷14; `TC0DATA` `0x00007D00`
= reload 2,000 where the loader left 142,858):

```
tc0data_at_init 00007D00
cdbr_at_init 03E80000
hz_tick 200000
hz_cdbr 200000
hz_agree 1
hz_derived 200000
hw_timeout_derived_us 83886080
```

The last row is at `armed_ovsel 9`, which is `hw_ovsel`'s default and what
`BOOTGUARD` arms. Beside it the dump still prints `hw_timeout_us 1121101` from
the compiled table — **the 76× on one page**, which is the point of not
rewriting the table.

🔴 **Refutation**: `hz_agree 0`, or either `hz` away from 200,000, means the
timer block was left in a state `TM-1` did not see — a finding about the boot,
not about this driver. `hz_derived 0` means `TC0DATA` read 0 and the driver
said so rather than falling back to a constant known to be 76× wrong.

### 3.3 The ladder — FOUR rungs, so two degrees of freedom

Seating 17 fit `gap(OVSEL) = 2^(15+OVSEL)/f + d` to **two** rungs, which
determines `f` and `d` exactly and leaves nothing to check. Four rungs leave
**two residuals**, and that is the difference between a solve and a test.

量 seating 17: `OVSEL` 3 = **1,334.723 ms**, `OVSEL` 8 = **41,930.599 ms**,
giving `f = 200,179.5 Hz` and `d = +25.179 ms`.

| rung | counts | `WDTCNR` | if `f` = 200,000 | if `f` = 200,180 | separation |
|---|---|---|---|---|---|
| `OVSEL` 0 | 32,768 | `00000000` | **187.843 ms** | **188.872 ms** | 1.029 ms |
| `OVSEL` 3 | 262,144 | `00600000` | **1,334.723 ms** | **1,334.723 ms** | 0.000 ms |
| `OVSEL` 8 | 8,388,608 | `00040000` | **41,967.043 ms** | **41,930.599 ms** | 36.444 ms |
| `OVSEL` 9 | 16,777,216 | `00240000` | **83,910.083 ms** | **83,836.019 ms** | 74.064 ms |

`d` is anchored on rung 3 in both columns, which is why rung 3's separation is
zero by construction and is stated rather than hidden.

🔴🔴 **THE ARITHMETIC THAT MAKES THIS WORTH A SEATING, and it needed no new
reading.** `SPEC.md` `CLK-08b` and this driver's own header both present
`f_wdt = 200,180 Hz` beside `CLK-17`'s `TC0CNT = 200,005 Hz` as agreeing —
*"Ratio 0.999"*. Put through the fit with **one** `d`, they do not:

| forced `f` | `d` from rung 3 | `d` from rung 8 | inconsistency |
|---|---|---|---|
| 200,000 Hz (`hz_tick`) | +24.003 ms | -12.441 ms | **-36.444 ms** |
| 200,005 Hz (`CLK-17`) | +24.036 ms | -11.392 ms | **-35.428 ms** |
| 200,179.5 Hz (the fit) | +25.179 ms | +25.179 ms | 0.000 ms |

**The instrument floor in those same two captures is 0.517 and 0.868 ms.** So
the two rungs already exclude *"the watchdog counts what the timer counts"* by
about **forty times the floor** — and that exclusion was sitting inside numbers
this repository had committed, unread, for a day.

**Three hypotheses.** `H1` the watchdog is genuinely ~0.09 % faster than
TC0/TC1 (two divider chains off one `CDBR`) — a finding about the part. `H2`
the **host** clock differs from the board by ~900 ppm, which enters the fit
**multiplicatively** and is absorbed into `f`; then every interval this
project has read off `console-capture` timestamps carries that scale. `H3` one
of the two rungs is wrong. §3.4 separates `H2`; the ladder's residuals
separate `H3`.

🔴 **Rung 0 is new and it is not a discriminator** — 1.03 ms of separation
against a ~0.9 ms floor. It is a **model** test: a gap far from ~188 ms
refutes the linear form itself. It is a rung at all only because the constant
moved. `CLAUDE.md`'s sixteenth update says *"`OVSEL` 0 is not measurable this
way at all"*, reasoning from `prom_putchar`'s FIFO drain against a 2.190 ms
timeout. 量: `RLXFW-W-GO\n` is 11 bytes and at 38400 8N1 drains in **2.865
ms** — 131 % of 2.190 ms, and **1.75 %** of the measured 163.752 ms. The drain
is a constant and lands in `d`, which is exactly what a four-rung two-parameter
fit is for: the offset does not have to be *explained*, only be the same on
every rung.

### 3.4 `C1-R` — the host against the board, and it needs no bite

One capture, two `/proc` reads 120 s apart, both timestamps in one `.timing`.
The board's own clock is `Δjiffies × 10 ms`; the host's is the `.timing`
offset difference. At 120 s the jiffy quantisation alone is **83 ppm** and the
host timestamp floor (~1 ms) is **8 ppm**, against the **~900 ppm** `H2` needs.

⚠️ **`IRQ-13`'s *"zero lost ticks over 263.73 s"* cannot be used here**: the
263.73 is `Δjiffies × 10 ms`, so both sides of that comparison are the board's.
The only host-against-board number in the repository is `P3-7`'s 3,009 vendor
ticks in 30.10 host seconds — **300 ± 170 ppm** — which does not settle it.

### 3.5 The bit scan — five positive controls and three unknowns

| bit | word | kind | prediction | why |
|---|---|---|---|---|
| 16 | `00010000` | 🔴 unknown | **188.872 ms** | reserved in D Table 27; predicted to behave as `OVSEL` 0 |
| 17 | `00020000` | 🔴 unknown | **188.872 ms** | reserved in D Table 27; predicted to behave as `OVSEL` 0 |
| 18 | `00040000` | 🟢 **control** | **41,930.599 ms** | `OVSEL[3]` -- must reproduce rung 8 to the floor |
| 19 | `00080000` | 🟢 **control** | **68.647 ms** | 量 seating 17 `R2-RAW19` -- reproducibility |
| 20 | `00100000` | 🟢 **control** | **12.336 ms** | 量 seating 17 `R2-RAW20` -- reproducibility |
| 21 | `00200000` | 🟢 **control** | **352.565 ms** | `OVSEL[0]` -- must reproduce the table |
| 22 | `00400000` | 🟢 **control** | **679.951 ms** | `OVSEL[1]` -- must reproduce the table |
| 23 | `00800000` | 🔴 unknown | **188.872 ms** | `WDTCLR`: arms and kicks at t=0, so `OVSEL` 0 |

🟢 **The controls are what make this a scan.** If bit 18 does not reproduce
rung 8, or 21/22 do not reproduce the driver's own table, or 19/20 do not
reproduce seating 17, the instrument is wrong and the three unknowns are not
readable — that is stated *before* the readings, so it cannot be decided
afterwards.

🔴 **If bit 16, 17 or 23 comes out at 2^19/f = 2,644.267 ms, that bit
IS `OVSEL[2]`** and `CLK-28`'s residual closes. If none of them does, the
field's fourth bit is not in `WDTCNR[23:16]` at all, which is a different and
more interesting answer.

### 3.6 `C1-M0` — the 32 group lines, every one predicted from the dump

Predicted by `tools/flashmap.py predict --level 0` against
`$FWRE_WORK/dumps/flash-n150rt-console-2.bin` (2026-08-16). 量 on seating 17's
`C1-M0.log`: **31 same, 1 DIFFER, 0 scope, 0 extra, 0 missing** — the
difference being group 0, where seating 16's bisection put it.

```
000000 1 122880 8494cc8666b5c6f673123a43ce18e52cf3cfc242af881a29a46a3f7b8ed4484a
020000 1 131072 632bf336dc8bb1facfedec872a28ab3ace712131b2941c772059a4290e68e761
040000 1 131072 f69f0b3d64904dff91c63375110d45862c117492999114c09b6872a6233a71a3
060000 1 131072 1850b0416d3a6248d1f7fc477e409ad8cbef3d6e12b179941ce549a198709315
080000 1 131072 4efcd613df7261cfe2c85844467fa3099855132c2cf43ec5e91e3d84f8364f69
0A0000 1 131072 2809be96244841d5dc374e4626e6eaee94b3ea12aa46b26f8384fe86eea6fc3f
0C0000 1 131072 48cc303098a46284a96b2accb3d616ab2af6da3ec74dd5545a212b11b1542175
0E0000 1 131072 95671e429e8d0153b0611676a18c2dd9061f46b33f696d66e532894b4e441f54
100000 1 131072 d1cf9142ce69e29e0f92e080f0e548e9e14bd955ba178a96c659f924804dee17
120000 1 131072 a5db8c4d3b79ace0e44a8e466966bf084d5667b7af52a3ef37aa0f120da41398
140000 1 131072 4fcf3508721256ab8fdd53be03b9bf5af0ebfc629cd992089f2e194f6e1cf4e5
160000 1 131072 fa43239bcee7b97ca62f007cc68487560a39e19f74f3dde7486db3f98df8e471
180000 1 131072 73835d3068ba95e0fa405d913508a239214937f0df0a7b152a6e210f0653fac7
1A0000 1 131072 e2418060f3e24ed10190407d945353d6aa12604a660a8ce7c9a9c2d62428ec0f
1C0000 1 131072 8cae1f52490ed7cde71923ff02c08979830e267922e634749e1043c7b67fe927
1E0000 1 131072 af409d8e211e8cbf15e0d6eac2c31802dba69b9e042a0d5571d13213ed1f7595
200000 1 131072 a79966d9d73a61b907f65715f950b325ff31aa7a2d75049fc82084c80956351a
220000 1 131072 5103beb12c6c1f304a5383f53ce994d7b4ebcc8f1674d17a9557827d21bd2ac0
240000 1 131072 a4b182356df0d4a2e22ffc6716531eb3e53ee91ec46496f18e6fdd008b1736db
260000 1 131072 11974511e341ce05eb7a0c9b3ad3af174d74147f5b40e253c8f0eb97aa08614c
280000 1 131072 a450030f8c318db4ca2401d99435049ba27ce54e889e4d4991b0150831d41afe
2A0000 1 131072 413598d270bd30fd78ca1622ec4203ee007b2685bb969ba28b0ea620da36e05c
2C0000 1 131072 f1cabc84c0c95ba3af68e336fc942981bd91202e21efb0b73358ad40758fd52b
2E0000 1 131072 bf624c11eb9f75b15f2e21e9f86e1fd31f0b20338b53ad401ddb94e9f1bed536
300000 1 131072 b305d71c6d9776c0ce91f8d90fe924130fe481e6e36d0aad483ec815a41097b8
320000 1 131072 bfd415326c7063ffbda5e4294c85afd029c5699a65adea6c74604e7ee11f0769
340000 1 131072 32c35b3b9f044739977cb5ff123afc883f5be592c508f28067a0042a5ed68369
360000 1 131072 b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260
380000 1 131072 b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260
3A0000 1 131072 b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260
3C0000 1 131072 b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260
3E0000 1 131072 b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260
```

🔴 **The claim this seating adds is about ATTRIBUTION, not about the bytes.**
Seating 17 ran `map 0` at 22:45 and the vendor firmware then ran twice by
accident. If these 32 lines come back the same, **those two vendor-firmware
runs wrote nothing to the 4,186,112 bytes this covers** — which is the first
half of a bracket that already exists and costs nothing to close. Any group
other than 0 differing is the attribution.

### 3.7 `C1-M1` — level 1 inside group 0, and it is the sharper cell

32 units of 4,096 bytes, of which **2 are `SKIPPED`** (`H601`'s two
pages, by rule, in the tool and not by convention).

```
000000 1   4096 e7d529d27ad0a31cd7d3f17ea6c3cdbbeca3ab5b37b3bbfdbe962feb9697647d
001000 1   4096 19bd9b8ee2f8a025f87450ed522b0b371e635b3c340a2ca6815735ffe026eeb3
002000 1   4096 d217ca411edb1f8787f26943f6fda8d60bb418b889f0535161db8c9bc627c197
003000 1   4096 245ecefbde63fd20f7d1567c2471ca858f8baa2507444c25e69c3538a3479e42
004000 1   4096 844748566180dbd1414f44c40fe90d76239977cec49db6f6099057bd6d60e317
005000 1   4096 11bdb47de4e73a74996d61f8c657d334138c8ee1b55bbb589c0818bd3f392aca
006000 1      0 SKIPPED
007000 1      0 SKIPPED
008000 1   4096 c18f645672fcc24c67f064ec8d61e9b60fcdd027b1325b518e8a881545e8e3ff
009000 1   4096 c40dc4b895d7da25ec631967b7e6a7946cad2daf0bd07f47ee2976c2f81b82f2
00A000 1   4096 ad7facb2586fc6e966c004d7d1d16b024f5805ff7cb47c7a85dabd8b48892ca7
00B000 1   4096 ad7facb2586fc6e966c004d7d1d16b024f5805ff7cb47c7a85dabd8b48892ca7
00C000 1   4096 0ad3e2fe34745c1b400118b8b28751d044a69d7980c3a00681072392c91b3e42
00D000 1   4096 7f3953fc07530aac0c6f4ce75d720fd2e667818bfb5828d8a325f4ec7accd7ca
00E000 1   4096 ad7facb2586fc6e966c004d7d1d16b024f5805ff7cb47c7a85dabd8b48892ca7
00F000 1   4096 ad7facb2586fc6e966c004d7d1d16b024f5805ff7cb47c7a85dabd8b48892ca7
010000 1   4096 e7335bc08de18174ed3aeae6cbc19578febd9d8eeee690125c0478bfe67c148e
011000 1   4096 f8539afe7307cbfd3305091c7f951cca814c2d76262d6bd1199a686166eb314e
012000 1   4096 6082b580213e7671ff702594df46ed573b3fd9124b0b124e1b1a0138deb85dba
013000 1   4096 9722a423ad95007bd3e0457d795bb4db7f106e60e621049197053bb33dc60cdc
014000 1   4096 f1c63a91aae645466e21fde0db6dad051bc10e901a17d2b5437adf2c941e8fe6
015000 1   4096 a7447adfd0e1936e9c2d0234deb12a310b625bbc2c042143d03e25caaa847242
016000 1   4096 bcf68a3b2cd6d088a6768812f1a12499ab05b4fed92330d67c986aeff768aad3
017000 1   4096 84124d94eb85ede7ea759369925b99259b705081ccec542f06ff563c5cacbe6d
018000 1   4096 e12adf3e20a2e1e5200834ae17f9ec228eebfa515b37be60d301a526a417d3af
019000 1   4096 09116ceb3609b5d7936b10e353b3e661bbd70c6fbc6a4cd55952796f9cc6a826
01A000 1   4096 f61d65985f49d4b60090e0a2b34b7c21e84f3a37e59a2707fb479a468b976f70
01B000 1   4096 7f4b49054e51626c2a709313484d1255a69b9bf9db017a7d100053bc19e9f54a
01C000 1   4096 15f8067880f85f6418addaa1dc1f5b51e47d077be92b4f137a3321ab5f75a421
01D000 1   4096 1a1fd7d220400e04be68b0930f19a60a2f083d9ad4eeaf54be9520d4a6bda38b
01E000 1   4096 53e5767ea8529657ef2c57ee7086315d882c9b5e42e0873e0a4cd76d9343933e
01F000 1   4096 f645a54d255128f683e68c456162b0415b2c11a6fd5f2805fc47ac5760b03480
```

🔴 **The prediction is that EXACTLY ONE unit differs and it is `009000`** —
seating 16's prefix bisection put the first difference in `[0x9000, 0xA000)`,
one erase sector. A prefix digest finds the first difference and nothing past
it, so *"exactly one"* has never been checked; this cell is what checks it.
Two or more differing units means the difference is not confined to one
sector, and `FLS-26`'s *"proven different 4,096 B"* grows.

---

## 4. The cells

### 4.1 The conventions

* Every capture carries a terminator. `console-capture.py` refuses without one
  and has since 2026-08-30; the refusal is a guard, not a habit.
* Every cell whose payload can reset the board carries `--esc-after`. **Two of
  seating 17's three power cycles were this rule not being followed.**
* No payload contains a `'`; the longest is
  **101 bytes** against `_check_send`'s 128-byte cliff.
* `looprun --mode bench` drives reset → rescue → burn-flag → upload → staged
  head → boot → assert with no operator gap; its own `S8` requires the board to
  print `RLXFW-ID0=F67EED22`, which is compiled in and typed by nobody.

### 4.2 🟢 `--until`, and why every window on this card is a CAP

`console-capture.py` **1.4** takes `--until PATTERN`: a regex over bytes that
ends the `--esc-after` loop and the capture as soon as it matches, searched
only in what arrives after the command line goes out.

🔴 **It exists because seating 17's rule does not fix what it was written for.**
The rule was *take three times the prediction*. The headline error that seating
was 76×, which 3× does not cover; and `FW-53`'s bit scan has **no prediction to
multiply**, because not knowing the answer is what the scan is for. 量
`bench/2026-09-08b/R2-B8.timing`: with `echo bite 8` sent, the console emits 65
bytes of command echo and then **nothing at all for 41.931 s**, so `--idle`
cannot wait for a bite either — the wait is pure silence and `--idle` stops
inside it. Stopping on the **event** is the only shape left.

🟢 **The rule is not discarded, it is repurposed.** `--esc-after` is still 3×
the prediction — as a **cap**. With `--until` a cap costs nothing when the
event arrives, so the three unknown bits get 300 s each and pay only what they
take. 23 of this card's 27 cells carry it.

量 on the map cell, which is where it pays first: seating 17's `C1-M0` ran
`--seconds 120` for a traversal whose own counter says **12.8 s**
(`map_jiffies 1280`). `--until 'map_lines'` ends it at ~14 s. Two map cells,
**212 seconds saved**, and the window can still be 180 s.

⚠️ **The one footgun, measured rather than documented**: arming happens when
the command line is *written*, so a pattern that is a substring of `--send`
matches the board's own echo within milliseconds. Case `N36` in the suite
asserts that it does. No pattern on this card is a substring of its own cell's
payload.

### 4.3 The ladder, and the drop order if the seating runs long

Thirteen boots, one power press. `busybox reboot -f` is a watchdog bite
(`FW-37`, 2.407 s to the loader prompt) and every bite here leaves the board at
the loader, so the whole card is one power cycle by construction.

**Priority, highest first, and it is written now so it is not decided at
03:00 with the board hot**:

1. `C1-M0` — the attribution bracket. First command, zero cost, and the only
   cell whose value decays with every further vendor-firmware run.
2. `C1-P`, `C1-R` — `WDT-1`'s fields and the host/board ratio.
3. `C4-B9`, `C3-B8` — the two discriminating rungs.
4. `C1-M1` — the sector localisation.
5. `C1-B0`, `C2-B3` — the model rungs.
6. `C5` — the USER bite.
7. `C6`–`C13` — the bit scan. **This is the first thing dropped**, and
   `PROGRESS.md` already says so: it degrades to riding another seating.

### 4.4 The expansion — one line per cell, and it is what gets typed

量, generated from one list by a script rather than typed, and checked in both
directions against §5's fence: **27 cells, 13 `looprun` lines,
26 `--send` payloads, longest 101
bytes, 0 containing a `'`, 0 at or over 128.**

```
#-- boot 1, cold: the operator presses power inside this window
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C1-A --esc 150 --esc-period 0.002 --seconds 165
/usr/bin/python3 tools/looprun.py --mode bench --cell C1 --out-dir bench/2026-09-09 --skip S2,S3,S4 --recipe-override f67eed22 --image /home/key/fwre-work/rebuild/bench-only/r57-20260909/rlxfw-r57-20260909.bin --image-sha256 efc2ae0d604f8898d4011280958ea9093aad76d4a6ea922ccc32f791f2b6bd91
#-- 🔴 THE FIRST COMMAND OF THE SEATING.  Seating 17's map 0 ran at 22:45 and the VENDOR firmware ran twice after it, so this closes FLS-26's attribution bracket at zero cost.  Nothing on this card can write flash; this cell being FIRST is what makes that a checkable ordering rather than an assurance.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C1-M0 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines' --seconds 180
#-- WDT-1's seven new fields.  None of them is a boot mark, which is why §3.1's 1,424 bytes is a control and not a coincidence.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C1-P --send 'cat /proc/rtl819x-wdt' --idle 3 --seconds 20
#-- hypothesis H2, and it is ONE capture on purpose: both reads and their host timestamps land in one .timing, so the ratio needs no cross-capture wall-clock.  120 s resolves ~8 ppm against the ~900 ppm H2 would need.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C1-R --send 'cat /proc/rtl819x-wdt ; sleep 120 ; cat /proc/rtl819x-wdt' --seconds 150
#-- level 1 inside group 0 -- the only group the 4 MiB digest says differs
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C1-M1 --send 'echo map 1 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines' --seconds 180
#-- rung 0.  🔴 It is a rung at all only because the constant moved: the 11-byte RLXFW-W-GO drains in 2.865 ms, 131 % of the OLD OVSEL 0 (2.190 ms) and 1.75 % of the measured 163.752 ms.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C1-B0 --send 'echo bite 0 > /proc/rtl819x-wdt' --esc-after 30 --esc-period 0.002 --until '<RealTek>' --seconds 45
#-- boot 2: rung 3.  --esc-after is 3x the prediction, as a CAP: --until makes a cap free, which is the whole reason a window can be generous without costing wall clock.
/usr/bin/python3 tools/looprun.py --mode bench --cell C2 --out-dir bench/2026-09-09 --skip S2,S3 --recipe-override f67eed22 --image /home/key/fwre-work/rebuild/bench-only/r57-20260909/rlxfw-r57-20260909.bin --image-sha256 efc2ae0d604f8898d4011280958ea9093aad76d4a6ea922ccc32f791f2b6bd91
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C2-B3 --send 'echo bite 3 > /proc/rtl819x-wdt' --esc-after 30 --esc-period 0.002 --until '<RealTek>' --seconds 45
#-- boot 3: rung 8.  --esc-after is 3x the prediction, as a CAP: --until makes a cap free, which is the whole reason a window can be generous without costing wall clock.
/usr/bin/python3 tools/looprun.py --mode bench --cell C3 --out-dir bench/2026-09-09 --skip S2,S3 --recipe-override f67eed22 --image /home/key/fwre-work/rebuild/bench-only/r57-20260909/rlxfw-r57-20260909.bin --image-sha256 efc2ae0d604f8898d4011280958ea9093aad76d4a6ea922ccc32f791f2b6bd91
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C3-B8 --send 'echo bite 8 > /proc/rtl819x-wdt' --esc-after 150 --esc-period 0.002 --until '<RealTek>' --seconds 170
#-- boot 4: rung 9.  --esc-after is 3x the prediction, as a CAP: --until makes a cap free, which is the whole reason a window can be generous without costing wall clock.
/usr/bin/python3 tools/looprun.py --mode bench --cell C4 --out-dir bench/2026-09-09 --skip S2,S3 --recipe-override f67eed22 --image /home/key/fwre-work/rebuild/bench-only/r57-20260909/rlxfw-r57-20260909.bin --image-sha256 efc2ae0d604f8898d4011280958ea9093aad76d4a6ea922ccc32f791f2b6bd91
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C4-B9 --send 'echo bite 9 > /proc/rtl819x-wdt' --esc-after 300 --esc-period 0.002 --until '<RealTek>' --seconds 320
#-- boot 5: the /dev/watchdog USER path.  `sleep 400 > /dev/watchdog` opens the device and holds the fd for the whole cell -- no shell builtin, no `&`, and `sleep` is a declared slink to busybox.  🔴 The first draft used `exec 3>` and cardcheck REFUSED it: `exec` is on its ASH_BUILTINS list, whose own comment says the list is 推 because nobody has enumerated THIS binary's builtin table, and that no card rests on it.  Making this card the first thing to rest on it was the wrong way to pass a gate.
/usr/bin/python3 tools/looprun.py --mode bench --cell C5 --out-dir bench/2026-09-09 --skip S2,S3 --recipe-override f67eed22 --image /home/key/fwre-work/rebuild/bench-only/r57-20260909/rlxfw-r57-20260909.bin --image-sha256 efc2ae0d604f8898d4011280958ea9093aad76d4a6ea922ccc32f791f2b6bd91
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C5-UO --send 'cat /proc/rtl819x-wdt' --idle 3 --seconds 20
#-- 🟢 The evidence that the open reached WDT_USER is the BITE, not a field: BOOTGUARD is fed every 250 ms and can never bite, so a reset at 60 + 83.8 = 143.8 s IS the proof that opening the device moved the state and that the soft deadline stopped the kicks.  A cell that ends at its cap with the board still in Linux refutes the USER path, and says so.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C5-UB --send 'sleep 400 > /dev/watchdog' --esc-after 450 --esc-period 0.01 --until '<RealTek>' --seconds 470
#-- boots 6-13: FW-53's bit scan, one bit per boot, bit 16 through bit 23.  🔴 FIVE of the eight are POSITIVE CONTROLS -- 18/21/22 must reproduce the driver's own table and 19/20 must reproduce seating 17 -- so this is an instrument with controls and not eight guesses.  The unknowns are 16, 17 and 23.  🔴 For those three there is NO prediction to take three times of, which is exactly why --until exists: the cap is 300 s for every cell and costs only what the event costs.  Each boot ends with a recovery cell that is a no-op if the bite happened and a warm reset if it did not.
/usr/bin/python3 tools/looprun.py --mode bench --cell C6 --out-dir bench/2026-09-09 --skip S2,S3 --recipe-override f67eed22 --image /home/key/fwre-work/rebuild/bench-only/r57-20260909/rlxfw-r57-20260909.bin --image-sha256 efc2ae0d604f8898d4011280958ea9093aad76d4a6ea922ccc32f791f2b6bd91
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C6-X16 --send 'echo unlock > /proc/rtl819x-wdt ; cat /proc/rtl819x-wdt ; echo biteraw 0x00010000 > /proc/rtl819x-wdt' --esc-after 300 --esc-period 0.01 --until '<RealTek>' --seconds 320
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C6-Z16 --send 'busybox reboot -f' --esc-after 20 --esc-period 0.01 --until '<RealTek>' --seconds 30
/usr/bin/python3 tools/looprun.py --mode bench --cell C7 --out-dir bench/2026-09-09 --skip S2,S3 --recipe-override f67eed22 --image /home/key/fwre-work/rebuild/bench-only/r57-20260909/rlxfw-r57-20260909.bin --image-sha256 efc2ae0d604f8898d4011280958ea9093aad76d4a6ea922ccc32f791f2b6bd91
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C7-X17 --send 'echo unlock > /proc/rtl819x-wdt ; cat /proc/rtl819x-wdt ; echo biteraw 0x00020000 > /proc/rtl819x-wdt' --esc-after 300 --esc-period 0.01 --until '<RealTek>' --seconds 320
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C7-Z17 --send 'busybox reboot -f' --esc-after 20 --esc-period 0.01 --until '<RealTek>' --seconds 30
/usr/bin/python3 tools/looprun.py --mode bench --cell C8 --out-dir bench/2026-09-09 --skip S2,S3 --recipe-override f67eed22 --image /home/key/fwre-work/rebuild/bench-only/r57-20260909/rlxfw-r57-20260909.bin --image-sha256 efc2ae0d604f8898d4011280958ea9093aad76d4a6ea922ccc32f791f2b6bd91
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C8-X18 --send 'echo unlock > /proc/rtl819x-wdt ; cat /proc/rtl819x-wdt ; echo biteraw 0x00040000 > /proc/rtl819x-wdt' --esc-after 300 --esc-period 0.01 --until '<RealTek>' --seconds 320
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C8-Z18 --send 'busybox reboot -f' --esc-after 20 --esc-period 0.01 --until '<RealTek>' --seconds 30
/usr/bin/python3 tools/looprun.py --mode bench --cell C9 --out-dir bench/2026-09-09 --skip S2,S3 --recipe-override f67eed22 --image /home/key/fwre-work/rebuild/bench-only/r57-20260909/rlxfw-r57-20260909.bin --image-sha256 efc2ae0d604f8898d4011280958ea9093aad76d4a6ea922ccc32f791f2b6bd91
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C9-X19 --send 'echo unlock > /proc/rtl819x-wdt ; cat /proc/rtl819x-wdt ; echo biteraw 0x00080000 > /proc/rtl819x-wdt' --esc-after 300 --esc-period 0.01 --until '<RealTek>' --seconds 320
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C9-Z19 --send 'busybox reboot -f' --esc-after 20 --esc-period 0.01 --until '<RealTek>' --seconds 30
/usr/bin/python3 tools/looprun.py --mode bench --cell C10 --out-dir bench/2026-09-09 --skip S2,S3 --recipe-override f67eed22 --image /home/key/fwre-work/rebuild/bench-only/r57-20260909/rlxfw-r57-20260909.bin --image-sha256 efc2ae0d604f8898d4011280958ea9093aad76d4a6ea922ccc32f791f2b6bd91
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C10-X20 --send 'echo unlock > /proc/rtl819x-wdt ; cat /proc/rtl819x-wdt ; echo biteraw 0x00100000 > /proc/rtl819x-wdt' --esc-after 300 --esc-period 0.01 --until '<RealTek>' --seconds 320
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C10-Z20 --send 'busybox reboot -f' --esc-after 20 --esc-period 0.01 --until '<RealTek>' --seconds 30
/usr/bin/python3 tools/looprun.py --mode bench --cell C11 --out-dir bench/2026-09-09 --skip S2,S3 --recipe-override f67eed22 --image /home/key/fwre-work/rebuild/bench-only/r57-20260909/rlxfw-r57-20260909.bin --image-sha256 efc2ae0d604f8898d4011280958ea9093aad76d4a6ea922ccc32f791f2b6bd91
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C11-X21 --send 'echo unlock > /proc/rtl819x-wdt ; cat /proc/rtl819x-wdt ; echo biteraw 0x00200000 > /proc/rtl819x-wdt' --esc-after 300 --esc-period 0.01 --until '<RealTek>' --seconds 320
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C11-Z21 --send 'busybox reboot -f' --esc-after 20 --esc-period 0.01 --until '<RealTek>' --seconds 30
/usr/bin/python3 tools/looprun.py --mode bench --cell C12 --out-dir bench/2026-09-09 --skip S2,S3 --recipe-override f67eed22 --image /home/key/fwre-work/rebuild/bench-only/r57-20260909/rlxfw-r57-20260909.bin --image-sha256 efc2ae0d604f8898d4011280958ea9093aad76d4a6ea922ccc32f791f2b6bd91
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C12-X22 --send 'echo unlock > /proc/rtl819x-wdt ; cat /proc/rtl819x-wdt ; echo biteraw 0x00400000 > /proc/rtl819x-wdt' --esc-after 300 --esc-period 0.01 --until '<RealTek>' --seconds 320
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C12-Z22 --send 'busybox reboot -f' --esc-after 20 --esc-period 0.01 --until '<RealTek>' --seconds 30
/usr/bin/python3 tools/looprun.py --mode bench --cell C13 --out-dir bench/2026-09-09 --skip S2,S3 --recipe-override f67eed22 --image /home/key/fwre-work/rebuild/bench-only/r57-20260909/rlxfw-r57-20260909.bin --image-sha256 efc2ae0d604f8898d4011280958ea9093aad76d4a6ea922ccc32f791f2b6bd91
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C13-X23 --send 'echo unlock > /proc/rtl819x-wdt ; cat /proc/rtl819x-wdt ; echo biteraw 0x00800000 > /proc/rtl819x-wdt' --esc-after 300 --esc-period 0.01 --until '<RealTek>' --seconds 320
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-09/C13-Z23 --send 'busybox reboot -f' --esc-after 20 --esc-period 0.01 --until '<RealTek>' --seconds 30
```

### 4.5 The numbers this card states, and where each is re-derived FROM

🔴 **Every row names a FROZEN artefact or this card itself** — lifecycle rule 2.
The four files under `bench-only/r57-20260909/` never move again; nothing here
points at `config/rlxfw-src/`, which is a live tree and would go red on the
next edit for a reason having nothing to do with this seating.

```cardnum
img-bytes	1043456	size /home/key/fwre-work/rebuild/bench-only/r57-20260909/rlxfw-r57-20260909.bin
img-sha16	efc2ae0d604f8898	sha256-16 /home/key/fwre-work/rebuild/bench-only/r57-20260909/rlxfw-r57-20260909.bin
vmlinux-bytes	4049730	size /home/key/fwre-work/rebuild/bench-only/r57-20260909/vmlinux
vmlinux-sha16	ef7e8b57a46e0659	sha256-16 /home/key/fwre-work/rebuild/bench-only/r57-20260909/vmlinux
map-bytes	377513	size /home/key/fwre-work/rebuild/bench-only/r57-20260909/System.map
map-sha16	670b2dbf0a78f3b5	sha256-16 /home/key/fwre-work/rebuild/bench-only/r57-20260909/System.map
ord-spi-late	1	count /home/key/fwre-work/rebuild/bench-only/r57-20260909/System.map ^802d0c98 t __initcall_rtl819x_spi_init7$
ord-wdt-late	1	count /home/key/fwre-work/rebuild/bench-only/r57-20260909/System.map ^802d0c9c t __initcall_rtl819x_wdt_init7$
ord-timer-late	1	count /home/key/fwre-work/rebuild/bench-only/r57-20260909/System.map ^802d0ca0 t __initcall_rtl819x_boot_arm_late7$
n-is-fault	0	count /home/key/fwre-work/rebuild/bench-only/r57-20260909/System.map ^[0-9a-f]{8} [A-Za-z] is_fault$
kept-machine-restart	1	count /home/key/fwre-work/rebuild/bench-only/r57-20260909/System.map ^[0-9a-f]{8} [A-Za-z] bsp_machine_restart$
kept-watchdog-reboot	1	count /home/key/fwre-work/rebuild/bench-only/r57-20260909/System.map ^[0-9a-f]{8} [A-Za-z] write_watchdog_reboot$
wdt-verb-bite	1	count /home/key/fwre-work/rebuild/bench-only/r57-20260909/System.map ^[0-9a-f]{8} [A-Za-z] rtl819x_wdt_verb_bite$
expansion-captures	27	count bench/2026-09-09/PREDICTIONS-B16-block15.md ^/usr/bin/python3 tools/console-capture[.]py capture .*--out bench/2026-09-09/C[0-9]+-
expansion-loops	13	count bench/2026-09-09/PREDICTIONS-B16-block15.md ^/usr/bin/python3 tools/looprun[.]py --mode bench --cell C[0-9]+ --out-dir
expansion-cold	1	count bench/2026-09-09/PREDICTIONS-B16-block15.md --out bench/2026-09-09/C[0-9]+-A --esc 150
expansion-until	23	count bench/2026-09-09/PREDICTIONS-B16-block15.md ^/usr/bin/python3 tools/console-capture.*-{2}until '
expansion-bite	4	count bench/2026-09-09/PREDICTIONS-B16-block15.md -{2}send 'echo bite [0-9]+ > /proc/rtl819x-wdt'
expansion-biteraw	8	count bench/2026-09-09/PREDICTIONS-B16-block15.md echo biteraw 0x[0-9A-F]{8} > /proc/rtl819x-wdt'
cells-fence	27	count bench/2026-09-09/PREDICTIONS-B16-block15.md ^bench/2026-09-09/C[0-9]+-[A-Z0-9]+$
send-over-127	0	count bench/2026-09-09/PREDICTIONS-B16-block15.md -{2}send '[^']{128,}'
send-inner-quote	0	count bench/2026-09-09/PREDICTIONS-B16-block15.md ^/usr/bin/python3 .*-{2}send '[^']*'[^ ]
map0-rows	32	count bench/2026-09-09/PREDICTIONS-B16-block15.md ^[0-9A-F]{6} 1 1[0-9]{5} [0-9a-f]{64}$
map1-skipped	2	count bench/2026-09-09/PREDICTIONS-B16-block15.md ^0[01][0-9A-F]000 1 +0 SKIPPED$
```

---

## 5. The fence

```cells
bench/2026-09-09/C1-A
bench/2026-09-09/C1-M0
bench/2026-09-09/C1-P
bench/2026-09-09/C1-R
bench/2026-09-09/C1-M1
bench/2026-09-09/C1-B0
bench/2026-09-09/C2-B3
bench/2026-09-09/C3-B8
bench/2026-09-09/C4-B9
bench/2026-09-09/C5-UO
bench/2026-09-09/C5-UB
bench/2026-09-09/C6-X16
bench/2026-09-09/C6-Z16
bench/2026-09-09/C7-X17
bench/2026-09-09/C7-Z17
bench/2026-09-09/C8-X18
bench/2026-09-09/C8-Z18
bench/2026-09-09/C9-X19
bench/2026-09-09/C9-Z19
bench/2026-09-09/C10-X20
bench/2026-09-09/C10-Z20
bench/2026-09-09/C11-X21
bench/2026-09-09/C11-Z21
bench/2026-09-09/C12-X22
bench/2026-09-09/C12-Z22
bench/2026-09-09/C13-X23
bench/2026-09-09/C13-Z23
```

**27 cells.** Boot 1 carries seven because its ladder can be stopped at
any point without losing what is above it; every later boot carries one or two,
because a bite ends the boot.

---

## 6. What this block cannot establish, written now

* **It does not make the clocksource mine.** `rating` will read 0 in every
  dump, deliberately, and the system's time *source* is still `jiffies`.
* **A derived rate is not a measured rate.** `hz_derived` is what `TC0DATA`
  and `CDBR` say the *timer* counts at. Whether the *watchdog* counts at that
  rate is the question the ladder asks, and this driver deliberately does not
  assume the answer: it prints both the derived figure and the compiled one.
* **`H2` and `H1` are separated by §3.4 only to ~10 ppm.** A real difference
  smaller than that stays undetermined.
* **Nothing here writes flash.** No `FLW`, `EW`, `EB` or burn command is on
  this card, `n_writes` is expected 0 in every dump, and `FLS-26`'s 99.02 %
  undetermined does not move: `map` compares digests against a dump, which
  cannot see two writes that cancel.
* **The bit scan is a scan of `WDTCNR[23:16]` only.** If `OVSEL[2]` is not in
  that byte, this seating says where it is *not*.

---

## 7. 🔒 FROZEN

Nothing in this file is edited after the freezing commit. A prediction that
turns out wrong is a **finding**, recorded in `CORRECTIONS-block15.md` beside
this file and never by changing the number above.

