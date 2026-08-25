# PREDICTIONS — Session B4, block 9 (`H3a`, `C-17`'s second instance through a different reset path)

**Written 2026-08-25 at the bench, after `NET-13` closed and before `J BFC00000`
is sent.**

## Why this runs although `H3a-early` already answered `C-17`

`RUNSHEET.md` §"Running order" says `H3a` is *"the first thing dropped if the
seating runs long"* once the reading exists — and it does exist:
`H3a-early` read `0x81000400` after `H1b`'s reset and found bias garbage with no
self-referential word.

**It runs anyway, and the reason is the two-source rule rather than the clock.**
`H3a-early`'s reset was `rlx_reset`'s **watchdog**; this one is `J BFC00000`,
the **ROM reset vector**. Same claim, different path to the condition. And two
further readings come free from the same capture: `CLK-14` (reset → first console
byte, `2.07 ms` from `D1`, n=1) and whether the ROM-vector path also prints the
watchdog line.

```cells
bench/2026-08-25/H3a
bench/2026-08-25/flush-h3a
bench/2026-08-25/H3a-rb
```

### `H3a` — `--send 'J BFC00000' --esc-after 20 --seconds 45`

```
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400 \
    --out bench/2026-08-25/H3a --send 'J BFC00000' --esc-after 20 --seconds 45
```

| | prediction |
|---|---|
| first | `---Jump to address=BFC00000`, upper case — the loader's own hex |
| then | the boot text, with ESC already streaming across the reset |
| the reset-cause line | 🔶 **`Reboot Result from Watchdog Timeout!` is expected and it discriminates nothing here.** `CLK-13` says the loader reads a hardware bit; **the reset immediately before this one was `H1b`'s watchdog**, so the bit is set whether or not `J BFC00000` sets it. A **space** would be the informative outcome — it would mean the ROM-vector path clears the bit — and it is not predicted |
| `Booting → banner` | **0.573–0.590 s**, the range this session has now widened to (n=7) |
| byte 0 → `Booting` | 🔴 **no ~345 ms gap.** That gap is cold-power-on only: measured 0.340/0.349 s on two cold starts and **0.001 s** on `H1b`'s warm reset. This is the second warm instance |
| `CLK-14` | reset → first console byte, from `.timing`. `D1` measured **2.07 ms**, n=1. **The ESC grid is 20 ms here**, so this capture can only bound it — the tight number needs `H3c`'s 2 ms grid |

### `flush-h3a` — `--send '' --seconds 2`

**11 bytes, a bare prompt, no `Unknown command !`** — `terminate_esc_line`'s CR
went out. This is the flush `D2` was lost to before the instrument wrote its own
terminator.

### `H3a-rb` — `--send 'DW 81000400 16' --seconds 5`

```
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400 \
    --out bench/2026-08-25/H3a-rb --send 'DW 81000400 16' --seconds 5
```

| | prediction |
|---|---|
| bytes | **213**, 4 lines — `len(cmd) 14 + 2 + 47 × 4 + 9`. *(`H3a-early`'s block predicted 214 and measured 213: the command is 14 characters, not 15. My arithmetic, corrected here rather than repeated.)* |
| content | 🔴 **the same sixteen words `H3a-early` read, byte for byte** — no word equal to its own address, no 32-byte period |

**Two things ride on that one comparison, and they fail separately:**

1. **`C-17`'s second instance.** If the structure is absent after the ROM-vector
   reset as well, *the vendor kernel wrote it* stands on two reset paths rather
   than one.
2. 🆕 **DRAM retention across a warm reset, at an address that has never been
   used for it.** `MEM-10` measured a two-word canary at `0x80A00000` surviving
   three warm resets. This is sixteen words at `0x81000400` across a **ROM-vector**
   reset, and the bytes are DRAM power-on bias rather than something written on
   purpose — **which makes it a stronger retention test, not a weaker one**: a
   canary is a value someone chose, and bias garbage is a value nothing chose.

⚠️ **If the sixteen words differ**, the interesting question is *which* words, and
it is not `C-17`'s. Record the diff before reading anything into it: a reset that
rewrites part of `0x81000400` is a finding about the loader, and `MEM-14` already
records `0x81000000` word 1 being rewritten to `0x00000144` on every boot.
