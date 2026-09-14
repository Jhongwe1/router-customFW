# The console link — what it is, how fast it goes, and what is still 讀 rather than 量

**Owner of `SPEC.md` `FW-70` and of everything this project believes about the
serial console as a *link* rather than as a source of text.** Opened
2026-09-15, seventy-first segment, at the desk, with the board unpowered —
every number below comes from captures that were already committed.

The reason this file exists at all is that `SPEC.md` § 17 has no owner-file
column, so `FW-70`, `FW-69` and `CLK-29` were parked there with an owning
*gate* and no owning *file*. This closes that for `FW-70`.

---

## 1. The link

| | | mark |
|---|---|---|
| adapter | Silicon Labs CP2102, `10c4:ea60` | 量 |
| host settings | 38400, 8 data bits, no parity, 1 stop bit — pyserial defaults at `tools/console-capture.py:496` | 讀 |
| board line control | `LCR = 0x03` — 8 data bits, **1 stop bit**, parity off | **讀 ×2, 量 ×0** |
| board baud, computed | **38,343.6** (divisor 326), −0.147 % from nominal | 讀 |
| board baud, cross-checked | 38,378.1 from `CLK-28`'s measured 200,180 Hz, −0.057 % | 推 from 量 |

🟢 **The clock constant that number stands on was checked rather than taken.**
`boards/rtl8196e/bsp/bspchip.h` defines `BSP_SYS_CLK_RATE` **three** times and
two of them are live `#define`s — 27 MHz under `#ifdef CONFIG_FPGA_PLATFORM`
and **200 MHz** in the `#else`. This is not an FPGA platform, so 200 MHz. And
`boards/rtl8196e/bsp/serial.c`'s `#if 1` arm is the one that compiles:
`s.uartclk = BSP_SYS_CLK_RATE`, `s.flags = UPF_SKIP_TEST` with **no
`UPF_SPD_CUST`**, so the generic driver computes the divisor and the `#else`
arm's `custom_divisor` line is dead code. `quot = (200000000 + 8*38400) /
(16*38400) = 326`; `200e6 / (16*326) = 38,343.56`.

### 1.1 Why `LCR` is 讀 ×2 and not 量 at all

**Source ①, the vendor Linux chain, and it is determined end to end.**
`boards/rtl8196e/bsp/prom.c` puts `console=ttyS0,38400` on the command line —
量, the board prints it back in `bench/2026-08-30b/L3.log`.
`uart_parse_options` overwrites parity and bits only when characters *follow*
the number, and none do. `uart_set_options` builds `CREAD|HUPCL|CLOCAL`, adds
`B38400` and `CS8`, and adds `PARENB` only for `'o'`/`'e'` — **`CSTOPB` does
not appear in that function at all**. `8250.c` maps `CS8` to
`UART_LCR_WLEN8`, `CSTOPB` to `UART_LCR_STOP` (not taken) and `PARENB` to
`UART_LCR_PARITY` (not taken). Two hard controls: `CSTOPB` has exactly **two
consumers and no producer** anywhere in the vendor serial tree, and
`serial8250_startup` independently writes `UART_LCR_WLEN8`. The userspace path
is covered too — `serial_core.c` gives a console port's tty the port's own
`cflag` on open, so a shell's stdout is 8N1 as well.

**Source ②, the loader, a completely different program.**
`rlxdefs.h:195 (stage 1 writes 0x03000000 to LCR)` records stage 1 writing
`0x03000000` to `0xB800200C`. On this part the UART registers are four bytes
apart with the value in the top byte, so that is `0x03` in `LCR` — the same
value. ⚠️ **This is the weaker of the two**: no disassembly address for the
writer, no `SPEC.md` row, no owner. The register *layout* it asserts is
corroborated by `docs/loader-command-semantics.md`; the *value* is not.

**量 is zero.** A sweep of every `DW` address in `bench/` finds sixty distinct
addresses and **not one** in `0xB8002000`–`0xB80020FF`. By this project's own
two-source rule the setting is 讀 ×2 and the measurement is outstanding.

### 1.2 🔴 The cheapest cell that makes it 量 — and the two registers it must not touch

```
DW B800200C 1      expect top byte 03     (8N1)
```

Refutation: `07` is 8N2, `0B` is 8N1 with parity. `DW B8002014` (LSR) is the
other safe one.

🔴 **Never `DW` across the block.** `+0x00` is RBR and reading it **pops a byte
off the receive FIFO**; `+0x08` is IIR and reading it **clears the pending
interrupt ID**. Under Linux the first steals a character from the console
driver, and the fault then appears somewhere else entirely. `RUNSHEET.md`
carries this where an operator reads it before power.

---

## 2. How fast it actually goes

### 2.1 The question `FW-70` opened

588 B ÷ 0.1735 s = 3,389 B/s = 88.3 % of the 3,840 B/s that 38400 baud gives
at 10 bits per character. A total-over-elapsed ratio cannot separate *a slow
wire* from *a nominal wire with idle in the window*: both give the same ratio.

### 2.2 Two estimators, written independently, and one of them refuses

`tools/uartrate.py` implements both. Its docstring carries the row semantics
and the refutation conditions; they are not repeated here.

- **`report`, the lower envelope.** 🔴 **Refuses on this console.** At 38400
  the reader is faster than the wire, so every read returns 3–4 bytes and the
  chunk sizes span nothing. The tool's own selftest quantifies the failure it
  is refusing to commit: at `b ∈ [1,60]` the envelope reads 0.114 bits low, at
  `b ∈ [1,12]` it reads **2.41 bits** low — **21×** — which is why the real
  boot captures come back at 0.90 and 2.80 bits/char. Predictable breakage,
  not random breakage.
- **`sweep`, the minimum over windows.** Every window's reading is an upper
  bound on the truth, because idle only adds. A long baseline defeats the
  timestamp jitter; a minimum defeats the gaps.

### 2.3 The corpus, split by era

量 2026-09-15 over 1,224 captures, classified by each capture's own
`.meta.json` `sent` field — **not by filename**; seating 22's defect #4 was a
comparison that selected cells by filename and named the wrong flash map.
623 loader-era, 505 Linux-era.

| window | Linux floor | loader floor |
|---|---|---|
| 2,000 B | 10.3290 | 🔴 **9.8831** |
| 8,000 B | 10.3848 | 10.2349 |
| 16,000 B | **10.3870** | 10.8045 (n=6, not converged) |

**Linux converges**: an eightfold window growth moves it 0.058 bits.

🔴 **9.8831 is below 10.000, which 8N1 forbids, and the resolution is in the
data rather than in another measurement.** The same capture reads 9.8831 at
w=2,000 and 10.2349 at w=8,000; reconciling those two needs a timestamp jitter
of **≈17.7 ms**, which is the USB latency timer's textbook range. ⚠️ **量
seating 17 gives 0.517–0.868 ms, and that is the MINIMUM inter-read gap, not
the MAXIMUM timestamp delay — two different quantities, and this project has
only measured the first.** So: short-window floors are unusable, converged
long-window values are usable, and the maximum delay is an open number.

### 2.4 What that settles

🟢 **11 bits per character is refuted.** At w=16,000 the window spans 4.33 s,
so a 16 ms jitter bounds the undershoot at 0.038 bits; 11 is sixteen error
budgets away. The loader era says it a second way: 10.2349 bits/char at
w=8,000 is **3,752 B/s**, straight through 8N2's ceiling of 3,490.9 B/s.

🔴 **And 88.3 % is a property of one capture, not of the link.** A second,
independently written instrument — 0.5 s slice medians rather than window
minima — orders the corpus by *who is transmitting*:

| transmitter | % of 3,840 B/s |
|---|---|
| loader `DW`, bare metal | **94.6–95.9** |
| bare-metal `rlxprobe` | 93.6 |
| Linux | 88.4–92.7 |

**A line-level cause yields one number. This is an 8.5 % spread ordered by
software layer**, so the cause is transmitter-side idle. That is a positive
identification, not only an exclusion.

⚠️ **Those three percentages are the slice-median instrument's, not a figure
both tools produced**, and the distinction matters when this is quoted
onwards. The window-minimum instrument agrees on the **ordering** and not on
the magnitudes — loader floor **97.7 %**, Linux floor **96.3 %** — because a
minimum measures the *fastest* window and a median measures the *typical* one.
What the cross-check establishes is the sign and the ordering, and the
ordering is the whole argument.

🔴 **`FW-70`'s own "the two boots agree" is refuted, by both tools.** `C2-R`
and `C3-R` read 3,393 / 3,489 B/s on slice medians (2.8 % apart) and
11.3088 / 11.0090 bits/char on window minima (2.7 % apart). `588 ÷ 0.1735` is
the **slowest** board-paced capture in the whole corpus.

**The correct statement**: *sustained console throughput is 88.4–95.9 % of
3,840 B/s, varying with the transmitting software layer, with the bare-metal
loader fastest.*

### 2.5 What is still open

1. **`LCR` 量.** § 1.2's one-line cell.
2. **The transmitter-idle mechanism is 推 for the delay and 讀 for the batch
   size.** `8250.c`'s `transmit_chars` reloads `tx_loadsz` characters per THRE
   interrupt, so the line idles for (ISR latency − one character time); 7.3 %
   spread over 16 characters is ~304 µs. 🟢 **The 16 is not generic-driver
   folklore — this board sets it**: `boards/rtl8196e/bsp/serial.c` assigns
   `s.fifosize = 16` in the live `#if 1` arm, and `PORT_16550A`'s own
   `uart_config` entry carries `tx_loadsz = 16` as well, so the two agree.
   What is still 推 is the ISR latency. Settling it means measuring the THRE
   interval on the device, which any Linux seating can carry.
3. **The maximum host timestamp delay.** § 2.3. Every window-floor reading
   this file quotes is bounded by it, and it is currently taken as ≤16 ms from
   the CP210x literature rather than measured here.
4. **The loader era has not converged** — only six captures carry 16,000
   bytes. The 1.44 % gap between the two eras at w=8,000 is an upper bound on
   what the kernel console path costs, not a reading of it.

---

## 3. Related rows

`SPEC.md` `FW-70` (this file owns it), `LDR-40` (the loader's `DW` reply
throughput, 3,512–3,726 B/s — the same quantity measured by a third method
before any of this, and nothing had drawn the connection), `CLK-28`
(200,180 Hz, the clock the divisor is computed against), `MAP-06` (the UART
block's address, 讀 from the datasheet), `CLK-14` and `C1-R` (board/host clock
ratio, −484.3 ppm, which is two orders of magnitude below anything here).
