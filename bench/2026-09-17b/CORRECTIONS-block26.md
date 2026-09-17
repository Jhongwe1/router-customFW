# The first Linux-state switch-register readings on this device — and four of them moved

Card: `bench/2026-09-17b/PREDICTIONS-B27-block26.md`, frozen at `a4234f6`.
`looprun --mode bench` at 12:22, cells 12:25–12:40, **still the one power cycle
spent at 11:02**. `check-predictions`: **7 of 7 captures came after the
prediction, 0 did not.**

---

## 0. The boot

`looprun` closed the loop in **39.54 s** of machine time with **9 assertions**:
the reset discriminator, `AUTOBURN` read back `00000000` at `0x8040D4A0`
(`S5b`, the second of `C-6`'s two sources), the host-link ARP precondition, the
staged head derived from the image rather than typed, the eleven boot marks in
declaration order, a reachable prompt, and 🟢 **`A3`: the board printed
`bb684eb0` and the build computed `bb684eb0`** — the `RECIPE_ID` of image
`p11e`, typed by nobody.

---

## 1. 🔴 The carded cells `C1`–`C5` are unreadable, and the cause is already in `SPEC.md`

All five returned `rc=0` and **114 bytes each**, and all five are **interleaved
character-by-character with busybox ash's echo of the command line**:

```
echo read 0xBB804000 4 > /proc/rtl865x/me  cmd read
m
bb804000:   o80r4Ay01
85
```

**量**, `od -c` on `C2-LXSW00.log`: taking the alternating characters back
apart gives ash's remaining `m`,`o`,`r`,`y` and the driver's
`8`,`0`,`4`,`A`,`0`,`1`,`8`,`5` — **`804A0185`**.

**推, the mechanism**: `memDump` reaches the console through `panic_printk`,
which writes the UART directly, while ash's echo goes through the tty layer and
is still draining. The kernel's output overtakes the pending echo. This is
`FW-47`/`FW-41`'s family — *"a mark the board printed can be absent from a
`grep`"* — arriving on a new path.

🟢 **`C6-PORT` is unaffected and that is the control**: `cat` writes through the
normal console path, and its capture is **585 bytes, exactly as predicted**.

### 1.1 The fix, run as declared off-card cells

`X28`–`X33`: the same reads with a `sleep 1 ; ` prefix, so the echo drains
before the driver prints. **124 bytes each, zero interleaving, six for six.**
🔴 The carded captures are kept as the evidence that the interleaving happened;
the readings below are taken from the `X` cells.

⚠️ **The card could not have avoided this.** Nothing in this repository had
read a `panic_printk`-only `/proc` handler from a shell, so there was no
population to check a payload against. `cardcheck`'s `A22` compares `--idle`
against a `sleep`; it has no rule for *needs* one.

---

## 2. 🔴 The readings, and four of six moved

⚠️ **量, and it corrects a premise this card was written on**: `echo read <a> 4`
prints **one word**, not four — the `4` is a byte count, which is why the
vendor's `/bin/dw` passes `4`.

| address | symbol | loader-state (block 24) | **Linux-state** | |
|---|---|---|---|---|
| `0xBB804000` | `MACCR` | `804A0185` | **`804A0185`** | 🔴 **unchanged — prediction refuted** |
| `0xBB804100` | `PITCR` | `00000000` | `00000000` | 🟢 unchanged, as predicted |
| `0xBB804A08` | `PVCR0` | `00080008` | **`00090009`** | 🔴🔴 **moved, as predicted** |
| `0xBB804234` | `MEMCR` | `00007F7F` | **`00007F00`** | 🔴 moved |
| `0xBB804128` | `PSRP0` | `000010E0` | **`000000E0`** | 🔴 moved by exactly **bit 12** |
| `0xB8010000` | `CPUICR` | `C4000000` | **`00000000`** | 🔴🔴 the DMA engine is off |

### 2.1 🟢🟢 `PVCR0` is the PVID register, and its value is `NET-04`'s VLAN id

**`00080008` → `00090009`.** `NET-04` (量, from the vendor kernel's own boot
lines) records `eth1` on port 0 at **vid 8** and the other four at **vid 9**.
`PVCR0` under Linux holds **9** in both halves of the word.

🟢 **`R6-6`'s premise stops being an assumption.** Its DoD is *"two ports on
different VLANs cannot ping each other while each reaches the CPU port"*, and
until today nothing had shown that PVID lives at `0xBB804A08` on this part —
`SPEC.md` had no value for it in either state. **It does now, in both, and they
differ by exactly the thing VLAN ids differ by.**

⚠️ **推**: that the word is two 16-bit per-port fields. Two ports per register
is consistent with `PVCR0`–`PVCR3` covering ports 0–7, but nothing here
measures the split.

### 2.2 🟢 `MEMCR`'s two bytes are two fields, and the card said what would show it

Block 24 read `00007F7F` and recorded 推: *this part has seven ports, `0x7F` is
a seven-bit all-ports mask, and `MEMCR` carries two of them*, with the note that
the loader's single `sw 127` cannot account for the second. The card then said
**if it moves, that 推 gains a mechanism**.

**It moved, and only the low byte did**: `00007F7F` → `00007F00`. **So the two
bytes are separately writable and software clears the low one.** ⚠️ What they
*mean* is still 未定; this is a mechanism, not a semantics.

### 2.3 🔴 `PSRP` bit 12 exists, nothing names it, and it is not about link

`PSRP0` reads `000010E0` at the prompt and `000000E0` under Linux. Bit 4
(`LinkUp`) is **0 in both** — `/proc/rtl865x/port_status` agrees, printing
`Port0 … LinkDown` — and bits 7/6/5 (`NWayEnable`/`RxPause`/`TxPause`) are set
in both. **The whole difference is bit 12.**

`NET-11`'s bit map covers 8 down to 0 and says nothing above it. **量: bit 12 is
set in loader state and clear under Linux on a port whose link state did not
change.** 🔴 Undetermined, and registered in § 17.

### 2.4 🟢🟢 `CPUICR` going to zero confirms a desk read of the vendor's init order

The loader leaves the CPU-port DMA running (`C4000000`, block 25 § 1). Under
Linux it reads **`00000000`**.

讀, this segment's desk pass over the vendor driver: `probe` does
`CPUIIMR = 0`, then **`CPUICR &= ~(TXCMD|RXCMD)`**, then a 650 ms reset
sequence; `CPUICR = 0xC4000000` is written by **`rtl865x_start()`**, which is
called from `ndo_open` — **not from probe.**

🟢 **No interface was brought up on this boot, so the engine should be off, and
it is.** That is an ordering read out of code at the desk, confirmed on the
silicon by a register nobody had ever read. ⚠️ The *converse* — that bringing
an interface up sets it back to `C4000000` — is **推** and was not tested.

### 2.5 The one that refutes me

`MACCR` was predicted 推 to change, on the reasoning that
`rtl865x_initAsicL2()` reconfigures the MAC. It reads **`804A0185` in both
states, byte for byte.** The vendor's Linux driver leaves the MAC configuration
register exactly as this unit's loader set it.

🟢 **And that refutation is what licenses the rest of the table.** The card's own
block-level 否證 said: *if every register reads what the loader left, either the
`/proc` path is not reaching hardware or the driver never touches the switch
core.* Four of six moved, so the path reaches hardware; `MACCR` not moving is
therefore a fact about the driver rather than about the instrument.

---

## 3. 🟢 `C6-PORT` — byte-identical across two seatings and two images

**585 bytes**, and `cmp` against `bench/2026-09-17/C2-PORT.log` (seating 25,
03:04, a different image and a different power cycle): **identical**, md5
`6413559b8e7bb4b853b91fc9cca7d333`.

That turns `NET-31`'s eighteen-field cross-state agreement into one that no
longer spans a power cycle: block 24 read `PSRP` at the loader prompt at 11:20
and this file was read under Linux at 12:39, **same power-on**, and they agree
field for field.

---

## 4. 🔴🔴 `FLS-26`'s bracket closed, and the near-miss is the more useful half

`C7-M0`: **3,013 bytes in 13.763 s**, `--until` matched at offset 2,997.

The card predicted **byte-identical to `bench/2026-09-10/C1-M0`, digest
`b3d3d7d0…`**, which `SPEC.md` `FLS-26` records as agreeing across four maps and
two seatings.

**The digest is `7de2d527a4edc415`. It differs.**

🔴 **And that reading is wrong — the flash did not change.** `diff` on the two
captures returns **two lines**:

```
5c5    < version rtl819x-spi 1.1     >  version rtl819x-spi 1.2
16c16  < map_jiffies 1280            >  map_jiffies 1279
```

The driver's own version string — `p11e` carries `rtl819x-spi` **1.2** where the
2026-09-10 image carried **1.1** — and a free-running elapsed-jiffies count.
**Every line that is about the flash is byte-identical**: `RLXFW-S-MRC`,
**`RLXFW-S-MDIFF=00000000`**, `RLXFW-S-MH601`, `map_rc 0`, `map_unit 131072`,
`map_entries 32`, `map_hashed 4186112`, and all thirty-two unit digests.
Filtering out those two lines and re-diffing: **identical.**

🟢 **So the bracket closes**: the vendor firmware executed on this part for
about five minutes this morning (block 24 § 0.3) and **wrote nothing to the
4,186,112 bytes this map covers.**

### 4.1 🔴 The finding about the instrument, which is worth more

**`FLS-26`'s four prior maps were compared by taking a digest of the whole
capture.** Those four were all produced by the *same image*. The moment the
image changes, that comparison reports a difference — **and it reports it in the
worst possible direction: as a flash change.**

A digest over a capture containing a version string and a timing measurement is
not a digest over the flash. **The comparison has to be over the map body**, and
this is the first seating where the two could have been told apart.
⚠️ `RLXFW-S-MDIFF=00000000` is the driver's own answer and it read zero — but a
flag reading zero is a claim, and what settled this was the byte-level diff.

---

## 5. What this block did NOT establish

1. **No driver of mine did any of this.** Every reading came through the
   vendor's `rtl819x` and its `/proc`. That is the point — `R6-1` wanted the
   contrast — but it is not a driver result.
2. **A register that moved is not a register understood.** `PVCR0`'s field
   split, `MEMCR`'s two bytes, and `PSRP` bit 12 are all 未定.
3. **`CPUICR` returning to `C4000000` on `ndo_open` was not tested** — no
   interface was brought up.
4. `FLS-26`'s ledger does not move: 99.61 % proven identical, 0.195 % proven
   different, 0.195 % undetermined. This closes an **attribution** interval, not
   the ledger.
5. **Zero flash writes, zero `FLR`.** `AUTOBURN` was set to `0` by `looprun`'s
   `S5` because an upload requires it, and `S5b` read it back `00000000`.
