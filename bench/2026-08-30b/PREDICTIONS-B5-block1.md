# PREDICTIONS — Session B5, `R3-8a`, block 1: the `loudm` upload and the boot

**Written at the desk on 2026-08-29, before power, as `R3-7`.** Every value below
was measured on this host before the seating and none of it is conditional on a
reading taken at the bench — which is why this block exists at the desk at all,
where `bench/2026-08-25b`'s blocks 1–3 had to be written between cells.
`tools/check-predictions.py` checks the ordering.

🔴 **Not to be edited after the first capture lands.** Fixing a typo moves the
mtime and the check fails, correctly. Corrections go in a new file.

**This is power cycle 2.** Power cycle 1 is `probe3` (`R1h-3`,
`bench/2026-08-30/`) and it runs first — `R3`'s pass state is *a kernel is
running*, and in that state there is no `<RealTek>` prompt to type `J` into and
no `DW` to recover a result block with. **Power cycle 3 has no block yet and
that is deliberate**: which image it carries is decided by `L-3`, and a
prediction block written for an experiment that may not happen is a prediction
that cannot be refuted.

## Cells, in order

```cells
bench/2026-08-30b/A-catch
bench/2026-08-30b/L0-ab
bench/2026-08-30b/L0-tail
bench/2026-08-30b/L2a
bench/2026-08-30b/L2b
bench/2026-08-30b/L2c
bench/2026-08-30b/L3
bench/2026-08-30b/L5a
bench/2026-08-30b/L5b
bench/2026-08-30b/L6a
bench/2026-08-30b/L6b
bench/2026-08-30b/L7a
```

**Twelve cells, and what the check will report is itself predicted:**

| `L-3` reaches | expected report |
|---|---|
| D5 | `12 of 12 captures came after the prediction, 0 did not` |
| D4 but no link | `10 of 12`, and `L6b`/`L7a` are the two |
| B07 and stops | `7 of 12`, and the five unrun ones are named by `L3` itself |
| nothing after `J` | `7 of 12`, same five, and `L3` is the finding |

**Named but not in the block, on purpose**: `L-6c`/`L-6d`/`L-7b` (the second
interface, run only if `L-7a` gets nothing) and `L-8a`/`L-8b` (the post-mortem,
run only after a failed `J`). Naming both branches guarantees a violation
whichever way the seating goes, which would make the number meaningless. **The
cost is stated rather than hidden**: if a branch cell runs, its ordering is
unenforced — the same gap `bench/README.md` records for `CONT3`.

**Not captures at all**: `L0-rescue.json` and the `loader-tftp.py put`
transcript are JSON, have no `.log`, and are checked by `--expect-load` and by
`L0-ab` instead.

---

## The two files, and the desk checks are already spent on them

| | `loudm` — **this power cycle** | `quietm` — power cycle 3 |
|---|---|---|
| uploaded as | `bench-only/b5-20260830/rlxfw-loudm-20260830.bin` | `…/rlxfw-quietm-20260830.bin` |
| `nfjrom` bytes | **1,053,696** | 1,027,072 |
| sha256 | `72928c564d903c8d49c838faa41fab323aeb11d79ac4e4902c42d2ecb0dfe0b2` | `cf8a93d73025292ddc61f28c7172ad00985efad8569bdfbcae69def3a10dfb8a` |
| `kernelStartAddr` | **`0x80003600`** | `0x80003600` |
| decompressed | 3,546,112 — 67.6 %, margin 1,696,768 | 3,472,384 — 66.2 %, margin 1,770,496 |
| `image_end` | **`0x80601400`** | `0x805FAC00` |
| `pending_len` | 3 | 1 |

量 2026-08-29: both renamed files are byte-identical to the pipeline's own
`nfjrom` (`cmp`, rc 0). **`0x80003600` has two independent sources** — the
`nfjrom` header field via `rtkimage.py check`, and `readelf -h`'s
`Entry point address` on the `vmlinux` they were built from. Different tools,
different files, same number.

⚠️ **`RLXFW` occurs ZERO times in the file that is uploaded** (量) — the marks
are inside the LZMA stream. `P10`'s 11/11 was read on the `vmlinux` and on the
decompressed image; what ties those to the wire is the sha256 above and nothing
else.

---

## `A-catch` — the power-on catch, and it says whether this is a cold boot

`console-capture.py capture --port /dev/ttyUSB0 --out …/A-catch --esc 25 --esc-period 0.002`

**Prediction**: from the first `\r\nBooting` in the log, **181 bytes with
sha256 `f5287ff9f64b1035…`**:

```
\r\nBooting...\r\n\x00chipName: UNKNOWN\n\rramSize: 32M\n\r \n\r
---RealTek(RTL8196E)at 2014.04.22-16:22+0800 v1.3 [16bit](400MHz)\n\r
P0phymode=01, embedded phy\n\r\n\r---Ethernet init Okay!\n\r<RealTek>
```

量 2026-08-29 across **five** cold power-ons — `2026-08-24b`, `24c`, `24d`,
`25`, `25b` — all five byte-identical over those 181 bytes. **The negative
control is in the same measurement**: `2026-08-24e` differs, and it is the warm
boot (`C-8`'s marker at +48). ⚠️ **The instrument prefix before `Booting` is not
predicted** — it has been 0, 1 and 2 bytes across those five (`""`, `ff`, `00`,
`00 fc`), which is the adapter and not the board.

🔴 **If this slice matches `24e` instead, the board was warm-reset, not cold
powered** — and then `AUTOBURN` state, DRAM bias and the staged image are all a
different boot's, so `L0-ab` is re-read rather than assumed and this block's
`L0-tail` baseline is void.

---

## `L0-ab` — the guard, and it is the one cell that can stop the seating

`--send 'DW 8040D4A0 1'`, after `console-dump.py rescue … --ip 10.1.1.1
--load-addr 0x80500000`.

**Prediction: 71 bytes** — `reply-size.py predict "DW 8040D4A0 1"` =
`13 + 2 + 47 + 9`, model fitted on n=91 captures — and the content byte for
byte, identical to `bench/2026-08-25b/H2a-ab.log`:

```
DW 8040D4A0 1\n\r8040D4A0:\t00000000\t00000000\t00000000\t00000000\n\r<RealTek>
```

🔴 **If word 1 is not `00000000`, STOP. Nothing is uploaded.** One instruction
at `0x80401B9C` is the burn path's own read of it, and this is read *after* the
rescue and *before* the transfer because the word that matters is the one the
burn path sees during the transfer. `AUTOBURN` is RAM state and every reset puts
it back to `1` (量, `bench/2026-08-23/B.log` B6: `8040D4A0: 00000001 …` on a
fresh boot).

---

## `L0-tail` — the baseline that makes `L2c` a measurement

`--send 'DW 806013F0 8'`, **before** the transfer. **118 bytes** (two lines).

🔴 **Why this cell exists, and why it did not before today.** `K2` said the
region cannot be poisoned first because `0x80500000` holds the loader's staged
copy of the vendor image. True — for the *head*. 量 2026-08-29: the staged image
is 987,138 bytes and ends at **`0x805F1002`** (`MAP-17` says the same), while
`loudm`'s tail read is at **`0x806013F0`** — **66,542 bytes above it**. So the
tail *can* be read before the upload, at zero risk and with nothing written.

**Prediction, and it is a shape rather than a value:**

| line | before the transfer | why it is not a number |
|---|---|---|
| `806013F0` | DRAM, **not sixteen zero bytes** | power-on bias. `MEM-16`: 89.5 % reproducible across a 16-hour power-off but never written down for this address, and no boot has ever touched it |
| `80601400` | DRAM, and **record it verbatim** | it is `L2c`'s negative control and its value is only needed against itself |

⚠️ **The one way this cell fails informatively**: if line 1 comes back as
sixteen zero bytes *before* the upload, then `L2c`'s first half is void for this
seating — a match would prove nothing. Say so in the results and fall back to
`L2a`, which does not depend on it. **Probability is not the argument** — the
argument is that the check is written down before the reading either way.

---

## `L2a` — which image is at `0x80500000`, and the head cannot answer it

`--send 'DW 80500000 8'`. **118 bytes.**

🔴 **The head is byte-identical to the staged vendor image and `K2` said it was
not.** 量, three device captures across two power cycles —
`bench/2026-08-23/B.log:16`, `bench/2026-08-24c/G1a.log`,
`bench/2026-08-24d/G5-rb1.log` — and 量, the head of all five `nfjrom` files
this project can produce. Same four words. It is the same `rtkload` `start.o`.

**Prediction, both lines, and only the second one carries information:**

```
80500000:	00000000	00008021	40906000	00000000
80500010:	00000000	00000000	3C108060	26101400
```

The last two words are `lui s0,0x8060` / `addiu s0,s0,0x1400` — the linker's
`__vmlinux_end`, `0x80601400`, which is `0x80500000 + 1,053,696` exactly.

| word 6 · word 7 | = | that would be |
|---|---|---|
| `3C108060` · **`26101400`** | `0x80601400` | 🟢 **`loudm`. The pass** |
| `3C10805F` · `26101000` | `0x805F1000` | 🔴 **the staged vendor image — the transfer did not land** |
| `3C108060` · `26101000` | `0x80601000` | 🔴 `loud`, **unmarked**. No ladder. Stop and re-upload |
| `3C108060` · `2610AC00` | `0x805FAC00` | 🔴 `quiet` or `quietm` — the wrong variant |
| `3C10805D` · `26100800` | `0x805D0800` | the drop's own kernel. It is not on this device; if this appears, something is very wrong |

⚠️ **Both words are needed.** `loud`'s low half is the staged image's low half;
only the `lui` separates them. That is why the cell reads eight words and not
one, and why `LDR-07`'s round-up (a length of 1 through 4 still prints four
words) is not enough here.

⚠️ **It cannot separate `quiet` from `quietm`** — same size, same word. `L2b`
is what does.

---

## `L2b` — which variant, and it is the only cell that can tell the marked pair apart

`--send 'DW 80540000 1'`. **71 bytes.** File offset `0x40000`, inside the LZMA
stream, where no two of the six images agree in any of the four words.

**Prediction:**

```
80540000:	CEC3FFD9	C013013E	CE652208	749F1E48
```

The other five, 量 at the desk, so a mismatch is diagnosable rather than merely
wrong:

| | first four words at `0x80540000` |
|---|---|
| `quietm` | `AFBD0BEE AE8D991B A39DEE9F 2A62E61B` |
| `quiet` | `78CBE252 D8BCCA11 8F6166EF 6024973E` |
| `loud` | `231ACB87 6A8FE6C9 9704C109 25B8056C` |
| the drop's | `806892AC E99A8B0B EB0EEE98 7FEB6193` |
| **this unit's staged image** | `A9FDA5F8 40713F77 AB0C8A74 B7566FE0` |

---

## `L2c` — the tail, after. One command, a positive and a negative control

`--send 'DW 806013F0 8'`. **118 bytes.**

| line | prediction | what it refutes |
|---|---|---|
| `806013F0` | **sixteen zero bytes** — `00000000 00000000 00000000 00000000` | the last 16 bytes of `loudm` are zero (量; the trailing zero run is **688 bytes**, from `rtkload/ld.script.in` aligning `__vmlinux_end` to 1024). **A short transfer does not reach here.** On its own a zero is what a dead instrument prints — what makes it evidence is that `L0-tail` read the same address minutes earlier and it was not zero |
| `80601400` | **byte-identical to `L0-tail`'s second line** | the negative control: the transfer wrote **exactly** 1,053,696 bytes and not one more. If this line moved, the loader wrote past `image_end` and every size in this block is suspect |

🔴 **This pair is the only place in the seating where a *change* is observed
rather than a value matched.** The head cannot do it (identical bytes), the
mid-image word cannot do it (the region is inside the staged image), and
poisoning is refused because it would destroy the fallback. The tail can,
because it is above the staged image, and that is measured rather than assumed.

---

## `L3` — the boot. `--send 'J 80500000' --seconds 90`

⏱ Reference: this unit's own kernel, from `J` to its last byte, **26.05 s and
1,789 bytes** (量, `bench/2026-08-24c/G6.meta.json`). 90 s is 3.5×, and `loudm`
prints more than the vendor kernel does.

### The pinned prefix, byte for byte — 169 bytes to M0

讀 `bench/2026-08-24c/G6.log`, this unit's own kernel entered the same way. The
loader ends its lines **LF CR**; the `rtkload` stub ends them **CR LF**:

```
J 80500000\n\r
---Jump to address=80500000\n\r
decompressing kernel:\r\n
Uncompressing Linux... done, booting the kernel.\r\n
done decompressing kernel.\r\n
start address: 0x80003600\r\n
```

🔴 **`0x80003600` is M0 and it is the first discriminator.** This unit's staged
image holds `0x80003440` (`FW-23`, 讀 — and 量 in `G6.log` above). It is
`printf("start address: 0x%08x\n", kernelStartAddr)` at `rtkload/hfload.c:114`,
read out of the image's own header at run time.

⚠️ **`K3` named three of those five lines.** `Uncompressing Linux... done,
booting the kernel.` and `done decompressing kernel.` are the two it missed, and
a capture that stops after `decompressing kernel:` is *not* the same finding as
one that stops after `done decompressing kernel.`

### The ladder, and eleven marks are 139 bytes

| | expected | mark |
|---|---|---|
| `RLXFW-B00\r\n` | 🔴 **D2.** The first C instruction of my kernel reaching the UART | 量 absent from both vendor artefacts |
| `RLXFW-B01\r\n` | `start_kernel`'s generic prologue survived | |
| `RLXFW-B02=0000CD01\r\n` | 🔴 **`PRId`, read off this die at run time. Upper case** — `rlxfw_puts_hex` uses `"0123456789ABCDEF"` (讀) | 量 `0x0000CD01`, 2026-08-25b, `probe2`'s bare-metal CP0 census, which shares no code with this path. **On qemu the same binary printed `00018000`** (量, `P3`) — that is what makes this a reading and not a constant |
| `RLXFW-B03\r\n` | `bsp_init()` sized DRAM off `BSP_MC_MTCR0` and returned | |
| `[    0.000000] CPU revision is: 0000cd01\r\n` | **`loud` only. LOWER case** — `arch/rlx/kernel/cpu-probe.c:39` is `printk("CPU revision is: %08x\n", …)` (讀). **42 bytes**, the same length qemu measured | 🔴 **the second reading of `PRId` in one capture**, same register, two call sites, two formatters. The case difference is free proof they are two paths |
| `RLXFW-B04\r\n` | `bsp_setup()` entered | |
| `RLXFW-B05\r\n` | 🔴 **the divisor.** Clean here after a clean B04 = `bsp_serial_init()` did not change the line rate. Garbage = it did. Missing entirely = `early_serial_setup` failed and `panic()`'d before a console existed | the only place in the ladder where *never reached it* and *the UART stopped carrying* are separated by construction |
| `RLXFW-B06\r\n` | `_imem_dmem_init()` — the Lexra CP3 scratchpad sequence, `CPU-46` — returned | ⚠️ the desk channel **skipped** this body (`--nop-cop3`), so this line is the first time it has ever run anywhere |
| `RLXFW-B07=00000000\r\n` | 🔴 **D3, and `00000000` is the pass** | see below |
| `RLXFW-B08\r\n` | `paging_init()` returned | |
| `RLXFW-B09\r\n` | `console_init()` — the handover | |
| `RLXFW-B10\r\n` | `init_post()`, before the branch that decides how userspace is reached | |
| `rlxfw: init running, RLXFW-R3-RUNG1-OK\r\n` | 🔴 **M4, D4 half one. 40 bytes** — `echo` writes 39 with LF and the console tty's `ONLCR` makes it 40 (推) | 量 present once in my image, **0** in this unit's kernel and **0** across all 161 files of its rootfs |

**Byte counts, and the model has already been validated twice.** A plain mark is
**11 bytes**, a valued mark **20** — the macro emits one literal ending `\n` and
`rlxfw_puts` turns that into `\r\n` (讀). 量 on `qemu/2026-08-29/`: the model
gives **106** for `quietm` and **148** for `loudm` and both captures are exactly
that, byte-identical. So on this device: **eleven marks = 139 bytes**,
**+ M4 = 179**, which at 3,840 B/s is **46.6 ms**.

### `B07 = 00000000`, and the prediction is derived rather than hoped

The desk channel printed `RLXFW-B07=FFFFFFFF` because qemu's malta has no
RTL8196E switch core. **On this die it must be `00000000`, and that is an
inference from a measurement rather than an expectation**: the next four lines
of `boards/rtl8196e/bsp/setup.c` are `if (ret != 0) bsp_machine_halt();`, and
`bsp_machine_halt()` is a bare `while(1)`. This unit's own kernel — same
function, same silicon — **booted to userspace** on 2026-08-24 (`G6.log`, `boa`
starting at 26 s), so on this die that call returned 0.

| reading | what it says |
|---|---|
| `00000000` then B08 | 🟢 D3. The switch core answered |
| **`FFFFFFFF` then silence** | 🔴 the designed silent hang, **read off the wire instead of inferred from the absence of everything after it**. That is the whole reason this mark exists, and it is a result rather than a failure |
| anything else | a return value neither the source nor the desk channel has produced. Record the number |

### What is *not* predicted, and saying so is the point

⚠️ **The `printk` between the marks.** `setup_early_printk()` registers between
B03 and B04 (量), and from there every `printk` in the port reaches the wire.
The desk channel halts at B07, so **nothing has ever observed this kernel
printing between B04 and B10 with real peripherals**. Expect a verbose capture;
its content is not predicted and a prediction invented here would be decoration.
Two lines that should appear and are cheap to look for: `Calibrating delay
loop… %lu.%02lu BogoMIPS (lpj=%lu)` (量, that format string is in my image and
**not** in this unit's) and `Linux version 2.6.30.9 (key@K) (gcc version
3.4.6-1.3.6) #1 Fri Aug 28 23:37:47 CST 2026`.

⚠️ **`TC-o`: exactly one buffered line came out on the desk channel** — the
`CPU revision is:` line — and the banner and everything printed before it did
not. Mechanism undetermined and deliberately not guessed at. **Predicted here as
the measured behaviour: one replayed line, after B03.** More than one on the
device is `TC-o` answered in the other direction, and it is a finding rather
than a miss.

⚠️ **That `prom_putchar` still writes 38400 when B00 runs is 推.** The loader
printed at 38400 through the same UART0 and nothing between touches the divisor
— but this ladder has never executed on this silicon. **If every mark is
garbage, that assumption is what was wrong**, and the capture is still a result.

### Four failure shapes, and they are not one hang

| what arrives | what it says |
|---|---|
| no `decompressing kernel:` | the jump did not land, or the stub did not start (`RUNSHEET` §B3's two causes) |
| `LZMA: Decoding error = %d` / `LZMA: Too big uncompressed stream` | 讀 — both strings are in the stub of every `nfjrom` (file offsets 10,296 and 10,176). The upload is damaged, and `L2a`/`L2b` should have caught it first |
| `start address: 0x80003600` then silence | entered, and died before or inside `start_kernel`'s prologue. **This is exactly the case B00 exists to separate**, and it is the case this seating has the best chance of resolving |
| **`start address: 0x80003440`** | 🔴 the staged **vendor** image booted. `PROGRESS.md`'s anti-DoD, 2026-08-25's own mistake. Recorded as *unattributed*, never as a pass |

---

## `L5a` — `cat /proc/cpuinfo`, and every field is pinned against the same file read on this die

🔴 **This is not a guess.** Upstream's `P5-5` read `/proc/cpuinfo` on **this
unit**, under the **vendor's** firmware, over `boafrm/formSysCmd`. My kernel is
built from the same board sources, so the comparison is field by field:

| field | vendor kernel, 量 (`upstream/test-ledger.md` `P5-5`) | mine, predicted | source |
|---|---|---|---|
| `system type` | `RTL819xD` | **`RTL819xD`** | 讀 `boards/rtl8196e/bsp/prom.c:43`, `return "RTL819xD";` — an RTL8196E board that reports `819xD`, which is the vendor's own naming and not a fault |
| `processor` | — | `0` | one CPU |
| `cpu model` | **`52481`** | **`52481`** | 讀 `arch/rlx/kernel/proc.c:29`, `"%d"` on `cpu_data[0].processor_id`. `0x0000CD01` = 52,481. 🔴 **A THIRD reading of `PRId` in this one seating**, in decimal, through `seq_file` and userspace |
| `BogoMIPS` | `398.95` | **`398.95`**, or a value that names a clock problem | `udelay_val` from `calibrate_delay()`. Far from 398.95 = `time_init`, not the CPU |
| `tlb_entries` | `32` | **`32`** | corroborates `CPU-08` (量 32 entries) by a path with no TLB probe in it |
| `mips16 implemented` | `yes` | `yes` | 讀 `proc.c:35` — **a hardcoded string, not a measurement**, and it is listed so nobody quotes it as one |
| `hardware watchpoint` | **`no`** | 🔴 **ABSENT** | 量: the format string `hardware watchpoint\t: %s` is in this unit's kernel image and occurs **zero** times in mine. The drop's `proc.c` does not have the line |

🔴 **The missing seventh line is a discriminator that costs nothing**, and it is
a second data point of `TC-17`'s shape: this unit's shipped kernel was not built
from any of the three drops in hand. **Its presence would mean the vendor kernel
answered.**

**Predicted length**: six lines, 120 bytes with LF and **126 with `ONLCR`**,
plus the tty's echo of the 17-character command and its CR LF = **145 bytes**.
Computed, not counted.

## `L5b` — `uname -a`, and the build stamp is the discriminator

量, `linux_banner` in my own decompressed image against this unit's:

| | |
|---|---|
| **mine** | `Linux version 2.6.30.9 (key@K) (gcc version 3.4.6-1.3.6) #1 Fri Aug 28 23:37:47 CST 2026` |
| **this unit's** | `Linux version 2.6.30.9 (admin@office.hopeiot) (gcc version 4.4.5-1.5.5p2 (GCC) ) #1526 Wed Jan 10 14:50:54 CST 2018` |

**`#1` against `#1526`, 2026 against 2018, `key@K` against `admin@office.hopeiot`.**
The release string `2.6.30.9` is identical and is therefore *not* the
discriminator — the version field is.

⚠️ The exact `uname -a` tail (`mips`, and whether a trailing `unknown` appears)
is **推**; what is predicted is the `#1 Fri Aug 28 23:37:47 CST 2026` substring.
⚠️ And busybox's `ash` banner is **not** expected: 量, `built-in shell` occurs
zero times in this unit's `busybox` (`BusyBox v1.13.4`, 273,332 bytes).

---

## `L6a` / `L6b` / `L7a` — the network, and three things were wrong with the plan

🔴 **`K6`/`K7` as written gave the board the workstation's own address and then
pinged an address nobody has.** 讀 §G3: *"`IPCONFIG 10.1.1.1`, workstation at
`10.1.1.2/24`"*. Both halves would have failed, and the capture would have read
exactly like `K7`'s own definition of a broken driver.

| | value | measured reason |
|---|---|---|
| workstation | `10.1.1.2/24` on `enxfc19286184c9`, driver `r8153_ecm` | unchanged from the TFTP, so it is not a variable between rungs |
| board, in Linux | **`10.1.1.10`** | no conflict, and **no ARP history** — the host's table holds the loader's synthesised MAC `56:0a:01:01:01:e8` for `10.1.1.1` |
| ping target | **`10.1.1.2`** | `10.1.1.1` is the loader's, and the loader is gone |
| before the ping | `ip neigh flush dev <if>` | 量, this file's § The ARP finding: *"a stale loader entry broke the ping outright until it was flushed"* |
| host filter | `tcpdump -i <if> -n -e 'icmp **or arp**'` | `icmp` alone cannot separate *ARP never resolved* from *the driver does not transmit* |

**`L6a` — `ifconfig -a`.** Predicted: **five interfaces**, `eth0`…`eth4`. 讀
`G6.log`: `eth0` vid 9 / member port `0x10`, `eth1` vid 8 / port `0x1`, `eth2`
`0x8`, `eth3` `0x4`, `eth4` `0x2`, and `[peth0] added, mapping to [eth1]`.
Fewer than five = `bsp_swcore_init` returned 0 and the netdevs still did not
register, which is a different finding from a switch that did not answer.

**`L6b` — `ifconfig eth0 10.1.1.10 netmask 255.255.255.0 up`.** No output on
success.

**`L7a` — `ping -c 4 10.1.1.2`.**

| board says | host `tcpdump` says | reading |
|---|---|---|
| ≥ 1 reply | echo request **and** reply | 🟢 **D5** |
| replies | nothing | 🔴 something else answered. Not the driver |
| no replies | requests present, no replies | the board transmits; the host or the path does not answer |
| no replies | **ARP requests, no ARP replies** | resolution never completed — that is the host or the cable, **not** the driver. This row is the one the `arp` filter buys |
| no replies | nothing at all | the driver does not transmit — **or `eth0` is not the socket the cable is in**. `L-6c`/`L-6d`/`L-7b` are the branch, and if both interfaces are silent that is **two** results: D5 refuted, and the socket question still open |

⚠️ **Which physical socket the cable is in is recorded nowhere in this
repository**, and `eth1` is the likely WAN (`peth0` maps to it). The card tests
rather than assumes, and one interface is up at a time so the host sees one MAC
per attempt. `R0`'s reference is 2/2 at 3.6 ms and it was the **vendor's**
driver.

---

## What this block does not do

* **It writes no flash byte.** `AUTOBURN` is read `00000000` at the burn path's
  own instruction before the transfer, and the file uploaded is an `nfjrom`
  payload with no `cr6c` header — `check_image()` is on the flash path, not this
  one (`P5`).
* **It does not test the load-delay behaviour of this die.** `TC-15`, `TC-21`
  and `TC-22` are readings of Realtek's tools; `R1a` has not moved. A boot that
  works is consistent with a hazard that has not been hit.
* **A pass here is not a pass on `quietm`.** The two variants differ by two
  config symbols and `loudm` spends real time inside `prom_putchar`'s busy loop
  next to two timing-sensitive drivers. **If `loudm` reaches D5 and `quietm`
  does not, that is a finding about the vendor's configuration and it is
  recorded, not averaged.**
* **It says nothing about `probe3`.** That is power cycle 1, `R1h-3`, and its
  four questions are independent of everything here.
* **`check-predictions.py` cannot be satisfied today.** Run at the desk on the
  day this was written it reports `0 of 12`, because control `N2` — *a predicted
  cell whose capture does not exist* — fires on all twelve. What the desk run
  establishes is that the four controls hold, the file parses, and the
  ```cells``` block is non-empty. The ordering claim is established by the same
  command **after** the seating.
* **mtime is not a cryptographic timestamp.** `touch -d` rewrites it. This
  proves ordering to a cooperative auditor and to future-me; it proves nothing
  against someone willing to forge it. The tool's own docstring says so and it
  is repeated here rather than left in a file nobody opens at the bench.
