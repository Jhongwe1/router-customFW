# Block 31 — the DRAM post-mortem of `NET-59`'s hang

**Seating 30, 2026-09-20, power cycle 1.** Written at the desk with the board
already parked at the loader prompt, **before any of the reads below was taken**
and before anything was uploaded.

---

## 0. 🔴 What this block is NOT

**It is not a frozen card.** It did not go through `tools/freeze.sh`'s five
gates and `tools/check-predictions.py` was not run against it. It is declared
that way rather than dressed up, for a reason that is itself the finding:

The opportunity this block exploits is **perishable and was not foreseen**. The
board came up on power cycle 1 of this seating into the loader prompt. Until
something is uploaded to `0x80500000` and entered with `J`, DRAM still holds the
image of the kernel that `NET-59` wedged at the end of seating 29. Freezing a
card costs longer than the operator can reasonably be kept waiting; the reads
cost about two minutes; and the alternative to taking them now is **not taking
them at all**, because the next thing this seating does destroys them.

What is preserved of the card discipline, and what is not:

| | |
|---|---|
| preserved | every prediction and every refutation condition in §§ 3–6 is written **before** the first read, in this file, and this file's mtime precedes every capture's `started_wallclock` |
| preserved | the validity gate (§ 3) is a **bracket** — the same control window is read before and after the payload reads, not once |
| preserved | the captures land in `bench/2026-09-20b/`, so `capdate` sees them and the directory name is the day they were taken |
| **NOT** preserved | `cardcheck`, `freeze.sh`, `check-predictions`, a `cells` fence, `cardnum` rows |
| **NOT** preserved | a second reader. Nobody has audited these predictions before the reads |

---

## 1. The opportunity, and why it exists at all

`SPEC.md` `NET-59`: at the end of seating 29 an `iperf3` TCP load wedged the
board — console silent for 100 s at 0 bytes, ping dead, `busybox reboot -f`
ineffective, and **not a panic** (`arch/rlx/kernel/traps.c:52` is
`#define printk panic_printk` with `CONFIG_PANIC_PRINTK=y`, so `die()` would
have printed; nothing did). The mechanism is undetermined; the leading
hypothesis is 推 an interrupt storm.

The driver's counters are not in a struct. They are a **flat contiguous run of
`.bss` statics**, `0x803CF420`…`0x803CF594`, immediately after the switch
driver's own run at `0x803CF3F0`…`0x803CF410`. `.bss` is not in the image file —
it is zeroed by the kernel at boot — so what is at those addresses **right now**
is what the wedged kernel last wrote there, not anything the loader or a fresh
boot put there.

`SPEC.md` `MEM-17` measured that this part's DRAM **retains its contents across a
full power cycle**: 598 of 22,976 bits (2.603 %) after 35.1 minutes unpowered,
and 1 bit after two minutes. The power interruption that produced the current
boot was requested as ~5 s.

**Therefore**: reading `0x803CF3F0`…`0x803CF59F` at the loader prompt, before
anything is uploaded, reads the NIC driver's state as of the moment the board
stopped executing.

---

## 2. The reads

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0`,
each cell adding `--until 'RealTek>' --seconds 15`.

`DW <addr> N` prints `4 × ceil(N/4)` words and rounds **up**
(`docs/loader-command-semantics.md:746`), so every window below is a whole
number of 16-byte lines.

| cell | `--send` | covers | role |
|---|---|---|---|
| `P1-TXTHI` | `DW 80200000 16` | `.text`, 2 MiB in | **control, before** |
| `P2-TXTNIC` | `DW 800F79C0 16` | `.text` at `nic_isr`'s entry | **control, before** |
| `P3-MAC` | `DW 8028ED50 4` | `.rodata`, `nic_mac` | **control, before, semantic** |
| `P4-NIC` | `DW 803CF3F0 108` | `rtl819x_sw_*` tail + the whole `nic_*` run | **the payload** |
| `P5-JIF` | `DW 8027C040 4` | `jiffies_64` / `jiffies` | payload |
| `P6-WDT` | `DW 8064BC90 116` | `rtl819x_wdt_*` + `rtl819x_ce_*` | payload |
| `P7-TXTHI2` | `DW 80200000 16` | same window as `P1-TXTHI` | **control, after** |

Every address is a read. No `EW`, no `EB`, no `FLW`, no burn, no `J`. Nothing in
this block writes anything anywhere.

---

## 3. 🔴 The validity gate, written before the first read

The payload reads mean nothing unless DRAM retained the previous kernel. That is
not assumed; it is measured, with expectations derived from the ELF
(`imgwork/r6if1/r6if1-20260920/kroot/vmlinux`, the image seating 29 booted,
`RECIPE_ID edc94765`, `nfjrom` sha256 `89051d6a396c305b…`) by
`s91-elfread.py` walking the program headers.

**`P1-TXTHI` must read exactly:**

```
80200000:	12020017	00402821	26020008	02202021
80200010:	90430000	90810000	24420001	14230005
80200020:	24840001	1460fffb	90430000	00000000
80200030:	00201821	00611823	14600005	00000000
```

**`P2-TXTNIC` must read exactly:**

```
800F79C0:	00000000	03e00008	27bd0018	3c0d1801
800F79D0:	27bdffe8	25a6002c	3c0ca000	afbf0010
800F79E0:	00cc3025	3c07803d	3c08803d	8cc50000
800F79F0:	8ce3f460	8d04f440	3c02803d	8c49f570
```

**`P3-MAC` must read exactly:**

```
8028ED50:	02524c58	46570000	00000000	00000000
```

**`P7-TXTHI2` must be byte-identical to `P1-TXTHI`.**

**Refutation condition.** If any one of `P1`, `P2`, `P3`, `P7` differs from the
line above it in a single nibble, **every number read by `P4`, `P5` and `P6` is
discarded and not interpreted.** They are not softened, not reported as
approximate and not used to rank hypotheses. The block then has exactly one
result — that DRAM did not retain — and that result is written up.

Three reasons this gate is a gate and not a formality, each already recorded in
this repository:

1. `MEM-17` is a measurement of retention over **minutes**, not over the
   14.5 hours that separate the end of seating 29 from this reading. Whether the
   board was powered through that gap is not known to the instrument.
2. The loader detects RAM size (`ramSize: 32M` in this boot's banner) and a size
   probe writes. Whether its probe addresses fall in `[0x803CF3F0, 0x803CF5A0)`
   is not known; `P2` sits 1 MiB in and `P1` sits 2 MiB in, so the two controls
   bracket the payload from below in address order as well as in time.
3. `P3` is semantic, not just byte-equal: `02:52:4C:58:46:57` is the locally
   administered MAC `NET-51` measured on this interface. A DRAM that decayed to
   a plausible-looking pattern will not decay to that.

---

## 4. 🔴 The asymmetry, written before the first read

`0x803CF420` is a **KSEG0** address, so the counters are cached. A power
interruption loses whatever the D-cache held and never wrote back.

Every one of these counters is **monotonically increasing**. Therefore:

> **the value read from DRAM is a LOWER BOUND on the value the counter actually
> held when the board stopped.**

This makes the whole experiment **one-sided**, and that has to be said before the
number is on screen rather than after:

| reading | what it licenses |
|---|---|
| `nic_n_irq` **large** (≫ packets plausibly sent) | the interrupt-storm hypothesis is **supported**, because the true value is at least this |
| `nic_n_irq` **small** | **nothing.** A storm's increments could have died in the D-cache. This does **not** refute the hypothesis |

Three readings escape the asymmetry because they are **states, not counts**, and
a stale state is still a state that was true at some point during the hang:

* `nic_seen_iisr` — the OR of every `CPUIISR` value the ISR has observed. A bit
  set here was set by the hardware at some point; `NET-53` already used this
  reading to refute its own leading diagnosis.
* `nic_rx_idx` / `nic_tx_idx` — ring indices. A value outside `[0, ring_size)`
  is `NET-58`'s failure shape and needs no magnitude argument.
* `nic_tx_ring` / `nic_rx_ring` / `nic_bufs` — the allocated addresses, which
  `NET-58` measured the engine walking away from.

---

## 5. Predictions

Written before the reads. `n` is the seating-29 value where one is on record.

| symbol | addr | prediction | if it comes out otherwise |
|---|---|---|---|
| `nic_engine_on` | `803CF430` | `00000001` | engine was off at the hang — the hang is not in the RX path |
| `nic_n_irq` | `803CF440` | **no prediction — this is the question.** 推 leading hypothesis says ≫ 10⁵ | see § 4 |
| `nic_n_irq_spurious` | `803CF444` | `00000000` | a spurious-interrupt path fired, which seating 29 never saw |
| `nic_n_rx` | `803CF44C` | ≥ 7 | — |
| `nic_n_tx` | `803CF448` | ≥ 17 | — |
| `nic_n_poll` / `nic_n_napi_poll` | `803CF454` / `803CF574` | ≫ `nic_n_rx` would mean the NAPI poll was looping without retiring descriptors | |
| `nic_n_skb_fail` | `803CF584` | `00000000` | allocation failure under load is then a live mechanism |
| `nic_n_tx_stop` / `nic_n_tx_wake` | `803CF588` / `803CF58C` | `stop ≥ wake` | `wake > stop` is impossible and would indict the reading |
| `nic_n_tx_timeout` | `803CF594` | `00000000` **necessarily** — `NET-57` proves the netdev watchdog timer is never armed on this part | a non-zero value **refutes `NET-57`** |
| `nic_last_iisr` | `803CF45C` | — | the last interrupt cause word the ISR saw |
| `nic_seen_iisr` | `803CF460` | bit 9 (`TX_DONE`) and the RX bits set | bits 17–22 (`PKTHDR_DESC_RUNOUT`) set would revive `NET-53`'s buried diagnosis |
| `nic_rx_idx` / `nic_tx_idx` | `803CF4A4` / `803CF4A8` | both inside the ring | outside ⇒ `NET-58` under load |
| `jiffies` | `8027C044` | ≥ the hang's elapsed time × `HZ` | a small value bounds when the tick stopped |
| `rtl819x_wdt_n_hw_kick` | `8064BCB8` | **this is the second question** — see § 6 | |
| `rtl819x_ce_cycles` | `8064BE10` | — | whether my clockevent was still advancing |

`nic_n_tx_timeout` is the sharpest single row in this table: it is the one field
whose predicted value is forced by a *different* finding, so a surprise there
costs `NET-57` rather than costing this block.

---

## 6. The second question this block can answer for free

`CONFIG_RTL_WTDOG is not set` in this image — and that is the **vendor's**
watchdog. 量 on the built `vmlinux`: the string `rtl819x-wdt` occurs 6 times and
`rtl819x_wdt_*` occupies `.bss` from `0x8064BC90`. **My watchdog driver is in the
image seating 29 ran.**

So "the board wedged and nothing could recover it" needs an explanation it has
not been given. Either

* **(a)** the watchdog was not armed at rest, in which case `NET-59`'s recovery
  problem is a configuration decision and not a fact about the part, and a
  future seating can make every hang self-recovering at the cost of one verb; or
* **(b)** it was armed and something kept kicking it **throughout the hang** —
  in which case *that kick is a liveness probe that ran while the console was
  dead*, and whether it ran discriminates "nothing executes" from "interrupts
  execute and nothing else does". That is a stronger reading than (a).

`rtl819x_wdt_ovsel`, `rtl819x_wdt_deadline`, `rtl819x_wdt_n_arm`,
`rtl819x_wdt_n_bite` and `rtl819x_wdt_n_hw_kick` are all inside `P6-WDT`, so this
costs one command that was being sent anyway.

⚠️ Both branches inherit § 4's asymmetry: `n_hw_kick` is a count.

---

## 7. What this block cannot say, whatever it reads

* It cannot attribute the hang. It reads a final state, not a trajectory.
* It cannot see anything the hardware held: `CPUIISR`, `CPUIIMR`, `CPUICR` and
  the descriptor-position registers are at `0xB8xxxxxx`, they are reset by the
  power interruption, and they are gone.
* It cannot distinguish "the counter stopped because the code stopped" from
  "the counter stopped because its cache line stopped being written back".
* It says nothing about flash. **Zero flash-write commands, zero `FLR`.**
