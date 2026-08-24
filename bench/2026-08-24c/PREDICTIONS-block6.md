# PREDICTIONS — block 6: `G6`, the reference boot

**Written before `J 80500000`.** Last cell of `bench/2026-08-24c/`. **This one
ends with the loader gone** — the vendor kernel takes the machine and the only
way back is a power cycle.

## What it is for

`G7` will boot the same image after it has come over the network. The question
R0 asks is **not** "did a kernel boot" but **"did the network path deliver the
same bytes"**, and that needs a reference produced on this board, minutes
earlier, from bytes the loader staged itself. Without `G6`, a successful `G7`
proves only that *some* image booted.

`G1a`/`G1b`/`G1c` established the precondition this cell needed: head, middle and
tail at `0x80500000`, `0x80580000`, `0x805F0FF0` all match the payload file, so
the loader has already staged the whole 964 KiB and this jump runs it.

```cells
bench/2026-08-24c/G6
```

**Command**: `--send 'J 80500000' --seconds 60`

## Prediction

The loader's own line first, then the vendor kernel. Lines quoted from
`upstream/dumps/uart-boot.log`, which is this device's normal boot:

```
---Jump to address=80500000            <- the J handler, NOT "Jump to image start=0x80500000..."
decompressing kernel:
Uncompressing Linux... done, booting the kernel.
done decompressing kernel.
start address: 0x80003440
Realtek WLAN driver - version 1.6 (2013-02-21)(SVN:)
Adaptivity function - version 7.1
SKB_BUF_SIZE=2408 MAX_SKB_NUM=256
Probing RTL8186 10/100 NIC-kenel stack size order[3]...
chip name: 8196C, chip revid: 0
eth0 added. vid=9 Member port 0x10...
eth1 added. vid=8 Member port 0x1...
eth2 added. vid=9 Member port 0x8...
eth3 added. vid=9 Member port 0x4...
eth4 added. vid=9 Member port 0x2...
[peth0] added, mapping to [eth1]...
Realtek FastPath:v1.03
init started: BusyBox v1.13.4 (2018-01-10 14:56:45 CST)
```

🔴 **The first line is the one that differs from the reference log and it is
supposed to differ.** `uart-boot.log` was captured on the loader's **autoboot**
path, which prints `Jump to image start=0x80500000...`; this is the **`J`
handler**, which prints `---Jump to address=80500000` (`0x8040B35C`, the same
string `D1` and `D4` produced with a different argument). From
`decompressing kernel:` onward the two should agree.

**`chip name: 8196C`** is expected and is *not* a contradiction: `0xB8000000`
reads `0x8196E001`, the part naming itself, while the driver's own table prints
`8196C`. Both were already on record before this cell ran.

## The four outcomes, and the fourth is not a failure

Upstream's `P9-12` wrote a three-outcome table for a `J` and **what happened was
the fourth**: the banner appeared and was cut at the same character every
iteration, because a payload a simulator had approved sat an `andi` in a load
delay slot. So:

| | reading | verdict |
|---|---|---|
| **1** | the boot text above, reaching `init started:` | ✅ the reference exists. `G7` has something to be compared against |
| **2** | `---Jump to address=80500000` then **silence** | 🔴 **two causes, not one**: jumped and the target was silent, or never jumped. The vendor kernel has a great deal to say, so silence is informative — it is still two causes |
| **3** | output that **stops mid-line** | 🔴 **its own row, not squeezed into 2.** This is what `P9-12` actually got. The image here is the vendor's, so a delay-slot bug inside it is not on the table — which makes this outcome *more* interesting, not less |
| **4** | different text from the reference | record the diff. The bytes came from the loader's own staging, so a difference is about the staging and not about any transport |

## What this cell says about flash: nothing

`G6` runs the vendor kernel, which has an MTD driver and every ability to write.
**`G8-pre` is why that is now checkable**: flash `0x000000` and `0x060000` were
read in this power cycle, before any kernel executed, and all **128 words matched
the dump**. `G8a` after the power cycle is the same read again, and the
comparison is same-session rather than against a dump from another day.

**Reach, stated before it is quoted**: two `0x100`-byte reads are **512 bytes of
a 4,194,304-byte part**. The evidence line this entitles anyone to is *"the
loader head and the `cr6c` header are unchanged"* — **not** *"zero flash bytes
written"*, which needs a full re-dump.

## After this cell

The loader is gone and the prompt is not coming back. **The board must be power
cycled**, and everything after it lands in `bench/2026-08-24d/` under
`bench/README.md`'s one-directory-per-power-cycle rule.
