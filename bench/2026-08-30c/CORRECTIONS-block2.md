# CORRECTIONS to `PREDICTIONS-B5-block2.md`

**Written 2026-08-30 after the seating.** The block is frozen and is not edited —
`tools/check-predictions.py` reads its mtime, and a block edited after its
captures land is not a prediction. Everything the seating refuted goes here, with
the measurement that forced it.

**The seating ran both power cycles.** `31 of 31 captures came after the
prediction, 0 did not`. Every stop-if on both cards stayed clear, no `V-no`
branch ran, and `V-8a`/`V-8b` did not run because `J` reached D4.

**Of the thirty-one cells, 30 matched a value or a hash written before power and 1 is
refuted.** §7 lists what matched; §1–§6 are the corrections. ⚠️ *(This paragraph opened by
steering the reader to §7 and said “twenty-eight”, which did not close against 31, and
called the refuted cell “the most useful cell in the block”. The count mixed in `V-rdh` and
`Z-rdh`, which §2 states are deliberately not among the 31.)*

---

## §1 `V-3` is **849** bytes, not 401 — and all five predicted terms were right

§9.1 built 401 out of five terms. 量 2026-08-30, recomputed off the capture
itself rather than off the block:

| term | §9.1 said | `V-3.log` | |
|---|---:|---:|---|
| `J` echo + four `rtkload` lines + `start address:` | 169 | **169** | ✅ |
| eleven marks, `RLXFW-B00` … `RLXFW-B10` | 139 | **139** | ✅ |
| M4, `rlxfw: init running, RLXFW-R3-RUNG1-OK` | 40 | **40** | ✅ |
| `/bin/sh: can't access tty; job control turned off` | 51 | **51** | ✅ |
| `# ` | 2 | **2** | ✅ |
| **a sixth term, between `RLXFW-B09` and `RLXFW-B10`** | **0** | **448** | 🔴 |
| | 401 | **849** | |

**So the arithmetic was not wrong and the terms were not wrong.** What was wrong
is a term the block asserted to be zero without ever writing it down as a term.
The same accounting run against `bench/2026-08-30b/L3.log` reproduces all five
numbers exactly and puts **5,248** bytes in the sixth slot, which is the control:
a term-by-term model that is right on both builds is not a coincidence on one.

## §2 The 448 bytes are fifteen lines of Realtek driver output, and they are not `printk`

🔴 **Corrected the same evening by the adversarial pass, in three places.** This section said all fifteen lines are `rtl_nic.c` through `rtlglue_printf`, that the path has no Kconfig gate, and that the number is 274. **Thirteen** lines are `rtlglue_printf`; the path *is* gated, by a different symbol; and the number is **97**. Each is below where it belongs.

```
Realtek WLAN driver driver version 1.6 (2012-12-04)
Probing RTL8186 10/100 NIC-kenel stack size order[3]...
chip name: 8196C, chip revid: 0
NOT YET
eth0 added. vid=9 Member port 0x1...
eth1 added. vid=8 Member port 0x10...
eth2 added. vid=9 Member port 0x2...
eth3 added. vid=9 Member port 0x4...
eth4 added. vid=9 Member port 0x8...
eth5 added. vid=9 Member port 0x0...
[peth0] added, mapping to [eth1]...
Realtek FastPath:v1.03
```

**The chain, 讀 end to end and then 量 on the artefact:**

| | |
|---|---|
| 讀 | `drivers/net/rtl819x/rtl_nic.c:6213` and `:6479`, and `AsicDriver/rtl865x_asicL2.c:4381`, emit these with `rtlglue_printf`, not `printk` |
| 讀 | `include/net/rtl/rtl_types.h:366` — `#define rtlglue_printf panic_printk`, inside `#if defined(__linux__) && defined(__KERNEL__)`. **No Kconfig symbol gates that line** — 🔴 **but "the path is ungated" is false and was refuted the same evening**: `CONFIG_PANIC_PRINTK` gates `panic_printk`'s body (`printk_log.c:667`, 量 `=y` in both `autoconf.h`s — turning it off is a link failure, not silence), and `drivers/net/wireless/rtl8192cd/8192cd.h:134-139` redefines `panic_printk` back to `printk` **keyed on `CONFIG_PRINTK`** — 量 live: `8192cd_osdep.o` carries 2 `panic_printk` / 0 `printk` in `quietm` and 0 / 25 in `loudm`, the same source line compiling to a different symbol. `rtl_nic.c:3955`/`:4049` do it too under two ESD symbols that are unset here, with **no `#undef panic_printk` anywhere in the tree** — one symbol away from wrong |
| 量 | 🟢 **Which of the four `rtl_types.h` in this tree wins is measured, not assumed**: the other three define `rtlglue_printf` to `printk`, and the recorded dependency list in `.rtl_nic.o.cmd` shows this build touched only `include/net/rtl/rtl_types.h`. `include/asm-mips/` and `arch/mips/include/` are not on the include path at all |
| 讀 | `include/linux/kernel.h:271-276` — with `CONFIG_PRINTK` unset, `printk` becomes `static inline int __cold printk(const char *s, ...) { return 0; }` while **`panic_printk` stays `asmlinkage`**, declared in the `#else` branch on purpose |
| 讀 | `kernel/printk_log.c:668` — `panic_printk` is a real function under `#if defined(CONFIG_PANIC_PRINTK)`, and its body is `vprintk(fmt, args)` |
| 量 | `quietm`'s `System.map`: `panic_printk` **`T` at `0x80015204`**, `vprintk` **`T` at `0x80014ef0`**, and `printk` is three **`t`** stubs |

**The attribution is exact rather than plausible.** `rtl_nic.c:6213`'s format
string begins `"\n\n\nProbing RTL8186…"`, and the capture carries exactly three
blank lines before that line. And `rtl_nic.c` holds the *same message* twice —
`:6479` via `rtlglue_printf` and `:10515` via `printk` with a
`==%s(%d)` prefix. The capture carries the first form and not the second, which
is a discriminator inside one file.

🔴 **But "all fifteen" is wrong: it is thirteen, and the other two are not even in that directory.** Traced line by line by the adversarial pass:

| line | source | mechanism |
|---|---|---|
| `Realtek WLAN driver driver version 1.6 (2012-12-04)` | `drivers/net/wireless/rtl8192cd/8192cd_osdep.c:6978` | **direct `panic_printk`**. Two candidates and the format discriminates: `:6976` prints three version components under `CONFIG_RTL8671`, `:6978` prints two. The device printed `1.6 (`, and `CONFIG_RTL8671` is in neither config |
| `Realtek FastPath:v1.03` | `net/rtl/fastpath/96E/fastpath_core.S:5536` then `fastpath_common.c:1643` | **not a print call at its origin** — `get_fastpath_module_info` is a tail call to `sprintf` into the caller's buffer, which `panic_printk("%s", buf)` then emits |
| the other 13 | `rtl_nic.c:6213`, `:6479`, `:9574`; `rtl865x_asicL2.c:4381`, `:5899` | `rtlglue_printf` |

**77 of the 448 bytes — 17 % — come from outside `drivers/net/rtl819x` and outside the `rtlglue_printf` macro.** 🔴 **And the fifteen lines are SEVEN call sites**: `:6479` is one call in a six-iteration loop and `:6213` is one format string worth four lines, **three of which are blank** (only twelve of the fifteen carry text). A call-site count is not a line count, and §2 used them interchangeably.

⚠️ **One term of §1's arithmetic is a sum over two disjoint regions, not a span.** The 139 is 128 bytes of `B00`–`B09` at `[169,297)` plus 11 bytes of `B10` at `[745,756)`, with the whole 448-byte block between them. A reader re-deriving it from prefixes gets a different answer.

## §3 🔴 §9.2 read `kernel/printk.c`, and this board does not compile it

§9.2's row for M4 and the shell reasons from *"讀 `kernel/printk.c`:
`console_setup()` (`:802`) and `register_console()` (`:1123`) are outside the
`#ifdef CONFIG_PRINTK`"*.

量 2026-08-30, `kernel/Makefile:5-15`:

```
ifdef CONFIG_RTL_819X
obj-y     = sched.o fork.o exec_domain.o panic.o printk_log.o \
else
obj-y     = sched.o fork.o exec_domain.o panic.o printk.o \
endif
```

`CONFIG_RTL_819X=y` in both built `.config`s (量), and in the built tree
`kernel/printk.o` is **absent** and `kernel/printk_log.o` is **present**, in
both. Exactly one of the two exists, which is the control.

**The conclusion §9.2 drew was right and its source was a file that is not in
this build.** That is worth more than the byte count: a reading taken from the
mainline file where the vendor substituted its own is the same class of defect as
`TC-27`'s `grep -r` blind spot, and nothing here checks for it.

## §4 §9.4 has a sixth shape, and 849 was not on the list

The block listed five shapes for `V-3` (401, 443, 6,459, short-and-ending-in-a-mark,
169-then-nothing) plus the vendor-image address. **849 is none of them**, and a
reader who took §9.4 literally would have had no row to write it in. The
corrected list needs:

| bytes | what arrives | what it says |
|---:|---|---|
| **849** | the ladder plus fifteen `rtlglue_printf` lines between B09 and B10 | 🟢 the pass. `CONFIG_PRINTK=n` removes `printk` and does not remove the vendor's driver diagnostics |

⚠️ **And 443 is now wrong too**, for the same reason: it was *401 + the 42-byte
`CPU revision is:` line*. On the corrected model that shape is **891**.

## §5 §11.2 is refuted, and in the direction that costs nothing

§11.2 says: *"Under `quietm` those lines are `printk` and do not exist. So on this
power cycle the binding is 推, carried over from `bench/2026-08-30b/L3.log`."*

**They exist.** 量, `V-3.log` carries all five `ethN added. vid=… Member port …`
lines, and they agree with `L3.log` cell for cell: `eth0` `0x1`, `eth1` `0x10`
(vid 8), `eth2` `0x2`, `eth3` `0x4`, `eth4` `0x8`. **The netdev-to-switch-port
binding is 讀 on this power cycle, not 推.**

🔴 **This paragraph carried a sixth line and called it new, unpredicted and unexplained. All three were false, and the adversarial pass found the answers already in this repository.** *(It read: “It also carries a sixth line the last write-up never mentioned — `eth5 added. vid=9 Member port 0x0` — and `V-6a`'s 23 interfaces do not include an `eth5`. A netdev added to the switch table and absent from `ifconfig -a` is not explained here and is not chased.”)*

量 and 讀, four ways:

* **It was observed the day before** — `bench/2026-08-30b/L3.log` carries `eth5 added. vid=9 Member port 0x0`.
* **The last write-up did mention it**, twice: `RUNSHEET.md` §B5's results and `bench/2026-08-30b/CORRECTIONS-block1.md`.
* **The mechanism is 讀 and already banked** — `notes/kernel-build.md` §16: `rtl_nic.c:6479` prints the **array index `i`**, not `dev->name`, and index 5 is the one entry the driver renames, `memcpy(dev->name, vlanconfig[i].ifname, 5)` under `RTL_DRV_LAN_P7_NETIF_NAME`, which `rtl865x_netif.h:370` defines as `"eth7"`.
* **And the premise is false**: 量, `V-6a.log`'s interfaces are `eth0 eth1 eth2 eth3 eth4` **`eth7`** `lo peth0 pwlan0` plus fourteen `wlan0*`. **The netdev is not absent from userspace — it is `eth7`, in the very capture cited as showing its absence.**

**One netdev, two names, one off-by-name print. Nothing is open.**

The host capture's `-e` was kept anyway and it earned its place independently:
the ARP request's source MAC is `00:12:34:56:78:94`, and the last octet names
`eth4` without the board being asked.

## §6 🔴 The number this correction nearly quoted is the wrong one

While writing §2 the obvious summary was *"1,594 call sites survive
`CONFIG_PRINTK=n`"* — 量, relocations naming `panic_printk` over 731 built
objects. **It is a count of a moving population and it must not be quoted.**

| population | `quietm` | `loudm` | |
|---|---:|---:|---|
| whole tree, relocations naming `panic_printk` | 1,594 | 719 | 🔴 **moves** |
| whole tree, relocations naming `printk` | 0 | 6,407 | |
| `drivers/net/rtl819x/**/*.o`, naming `panic_printk` | 274 | 274 | 🔴 **also wrong — see below** |
| the same, **excluding `built-in.o`** | **97** | **97** | ✅ the call-site count |
| `drivers/net/rtl819x` leaves, naming `printk` | **0** | 998 | ✅ the discriminator |

The whole-tree `panic_printk` count moves because this tree redefines both names
in both directions in at least eight files — `drivers/net/wireless/rtl8192e/8192cd.h:140`
has `#define panic_printk printk` and `8192cd_mp.c:65` has `#define printk panic_printk`.
🔴 **And then the adversarial pass caught 274 by the same class of defect, hours later.** `drivers/net/rtl819x/**/*.o` matches 28 objects, **seven of which are `built-in.o`**, so each call site is counted two or three times: 量, all `*.o` = 274, excluding `built-in.o` = **97**, top-level `built-in.o` alone = 97, and `97 + 97 + 40 + 40 = 274`. **97 is the number**, it is identical in both builds, and the control that makes that identity mechanism rather than coincidence is that **22 of the 28 objects are byte-different** while `printk` goes 998 → 0 over the same material. ⚠️ **Scoping to this directory also drops two of the fifteen lines** (`8192cd_osdep.o`, `fastpath_common.o`), so 97 is a number about the driver directory and not about the 448 bytes. *(This paragraph read: "274 is the number that answers the question." One table, two multiply-counted populations, and I caught one of them.)*

## §7 What the block got right, stated so §1–§6 are not read as the whole story

| cell | prediction, written before power | reading |
|---|---|---|
| `V-A` / `Z-A` | 181-byte slice, sha256 `f5287ff9f64b1035…` | **both matched**, and both prefixes were benign (1 byte, 0 bytes) |
| `V-0ab` | `00000000`, 71 bytes | matched, **and byte-identical to `H2a-ab` and `L0-ab`** |
| `V-0t` | line 1 not sixteen zero bytes | `BF03F3A2 FFBFE6A8 2BA8ABBA 32BAEE6F` |
| `V-2a` | `0x80500018`=`3C108060`, `0x8050001C`=`2610AC00` | matched |
| `V-2b` | `AFBD0BEE AE8D991B A39DEE9F 2A62E61B` | matched — the only cell that separates `quietm` from `quiet` |
| `V-2c` | line 1 sixteen zero bytes, line 2 unchanged from `V-0t` | **both**, so the positive and negative control both fired |
| `V-rd0` / `V-rd6` | byte-identical to `bench/2026-08-24d/G8a-rd{0,6}.log` | matched, `cea9a0f1…` and `8c9949bc…` |
| `V-rdh` | equal to the desk expectation | **matched**, 777 bytes, verdict only |
| `V-2d` | byte-identical to `V-2a` | matched |
| `V-5a` | 147 bytes, byte-identical to `L5a.log` | matched, **and `BogoMIPS` had a licence to move and did not** |
| `V-5b` | 111 bytes, sha256 `ef82d7ecd2ca1ff6…` | **matched exactly** — a hash constructed at the desk by substituting three characters |
| `V-6a` | 7,658 bytes, byte-identical to `L6a.log` | matched |
| `V-6b` | 52 bytes | matched |
| `V-7a` | ≈420 bytes, 4/4, request and reply in the host capture | 420 bytes, 4/4, 0% loss, both directions |
| `Z-ab` | **`00000001`** | matched — cycle 4 is a fresh boot by instrument, not by testimony |
| `Z-rd0` / `Z-rd6` / `Z-rdh` | equal to their `V-*` and to the committed baselines | **all three matched** |
| §15's branch table | `21 of 31` after cycle 3, `31 of 31` after cycle 4 | **both observed, in that order** |

## §8 Two deviations from the card, both deliberate, both recorded

**(a) `V-1` was given `--report bench/2026-08-30c/V1-put.json`, which the card's
row does not carry.** §2's *"Not captures at all"* list names *"the
`loader-tftp.py put` transcript"* as an expected artefact of this seating, so the
flag makes the card's own §2 true rather than adding anything to it. Nothing on
the wire changed.

**(b) Each `Y` was gated on `grep -Fq` of the exact expected echo instead of on
the operator reading it.** The card's stop-if is *"read the echo before typing
`Y`"*; the gate is the same test made mechanical, it printed `GATE PASS` with the
matched string on all six, and a failure would have sent nothing rather than
`N`. ⚠️ **It has no negative control** — no echo was ever wrong, so the gate has
never been shown able to refuse. It is a habit turned into a check, and it is not
yet an instrument.

## §9 Two things the card names that are not in this repository

`console-dump.py` and `loader-tftp.py` are written on the card with no path.
They are **not under `tools/`**. 量 2026-08-30: they are in `upstream/tools/`,
the submodule pinned at `4d3ff26`, and byte-identical copies sit in the sibling
`router` checkout. This seating ran the pinned ones, which is what makes the
invocation reproducible — but a reader following the card at the bench has
nothing telling them which of the two to run, and a card that names a tool it
cannot locate is one power cycle from being a problem.
