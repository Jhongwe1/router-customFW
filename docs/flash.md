# Flash

The 4 MiB SPI NOR flash: which regions may be written, under whose yes, and why
writing the kernel region is recoverable when writing the loader is not. The
policy is the project plan's — its decisions `D3` to `D6` and its size budget,
written 2026-08-22 to 2026-08-25 — translated here on 2026-10-17; the plan is not
published ([`method.md`](method.md) § *Quoting the plan*). The layout as built is
[`notes/update-chain.md`](../notes/update-chain.md) § 6's, and the rule about
writes is [ADR-006](decisions/ADR-006-flash-write-rule.md).

## The regions

| range | policy |
|---|---|
| `0x000000`–`0x005FFF`, the stock loader | never written by this project. A first-stage loader of rlxfw's own, `R10c`, is deliberately not done: there is one device, and this is the one write it cannot recover from |
| `0x006000`–`0x007FFF`, `H601` | never written: this unit's MAC and radio calibration, which no reset restores |
| `0x008000`–`0x00FFFF`, the vendor's configuration (`COMPDS`, `COMPCS`) | written only with a verified backup |
| `0x010000`–`0x3FFFFF` | the kernel and root filesystem: from `R8` on, after one rescue drill |

`SPEC.md` holds these as `TGT-01` to `TGT-04`. Every write also needs the owner's
yes, dated and naming its exact payload (ADR-006, `FW-113`). The tools that
refuse: `tools/flashguard.py` for every computed destination, with each range's
reason in [`update-chain.md`](../notes/update-chain.md) § 4;
`tools/cardcheck.py` for the loader's write verbs on a bench card; and
`tools/flashwin.py` for what of the flash may be printed
([`CLAUDE.md`](../CLAUDE.md) § Flash).

## Why the kernel region is recoverable and the loader is not

The plan's argument (`D4`, its fourth version):

1. The loader occupies `0x000000`–`0x005FFF`, and no operation writes it — by
   rule, not by luck.
2. The loader copies its image into RAM before it offers the ESC window: it
   reads first and asks second, and a read cannot fail — reading garbage is
   still reading.
3. So while `0x000000`–`0x005FFF` is intact, whatever `0x010000` and above
   hold, the loader's prompt comes back, and with it the TFTP rescue.

Writing the kernel region is recoverable by design. The writes that are not —
the loader region, `H601`, and a container whose destination falls in a
forbidden range — are refused where the container is made. The argument's refutation condition, as the
plan wrote it: if the loader, on a failed image check, retried forever or hung
instead of returning to its prompt, the argument is void and `R8` needs a spare
unit. 量 on the failures `R8b` produced, it did not fire: a torn `rlxboot` handed
over to its rescue copy through the loader's own scan
([ADR-002](decisions/ADR-002-ab-slots-rlxboot.md)), and with no image accepted
the loader stopped at `<RealTek>`, its prompt (`FW-241`).

## Mainline: no flash write until `R9`

Until `R9` closed on 2026-10-04, every image ran from RAM: the loader's prompt
caught with ESC, `AUTOBURN 0`, `LOADADDR`, a TFTP upload into RAM, then `J`. Only
persistence needed flash, and persistence was `R8`. 讀 `AUTOBURN` is read at one
instruction in the whole loader, so `AUTOBURN 0` makes upload-and-jump a
zero-write sequence on that instruction's evidence rather than on usage text
([`loader-command-semantics.md`](loader-command-semantics.md) § c). What a record
may claim instead of *not one byte written* is in ADR-006 (`FLS-26`).

## The loader scans

讀 [`loader-command-semantics.md`](loader-command-semantics.md) § a, from two
sources: the loader tries six kernel candidates, `0x010000` to `0x060000` in
64 KiB steps, and the first image that passes `check_image()` wins. That gives a
free fallback — if `0x010000` is broken, the loader tries `0x020000` — and a
hole: a slot carrying a header the loader accepts could be booted directly,
bypassing the signature check and the anti-rollback counter, a downgrade for the
price of one corrupted byte. 量 one refinement the plan did not have: for a
`cr6c` header the loader also searches slot A's range for a root filesystem and,
finding none, stops instead of resuming the scan, which is why `rlxboot` and its
rescue copy carry `cs6c` (`FW-241`).

## `rlxboot`

The stock loader cannot be changed and verifies nothing, so a second-stage loader
of rlxfw's own sits at the first candidate, `0x010000`, and decides which slot
boots; a read-only copy, `rlxboot-rescue`, sits at `0x020000`, the one image the
loader still boots when `0x010000` is broken; and the slots carry no header the
loader recognises, so the only path to them is through the signature check. The
plan's boundary, kept: this is not secure boot. An attacker who can write flash
overwrites `rlxboot` itself; what it defends is the update path against a forged
image, not a physical attacker. The plan found no OTP or eFuse chapter in the
datasheet's contents and ruled that nothing may imply a key-hash fuse; that half
is ⊘ in [`threat-model.md`](threat-model.md) § 11. As built:
[ADR-002](decisions/ADR-002-ab-slots-rlxboot.md), [`notes/rlxboot.md`](../notes/rlxboot.md),
and in [`update-chain.md`](../notes/update-chain.md) § 6 the layout, including the
barrier `0x030000`–`0x06FFFF` that keeps four scan candidates out of slot A
(`FW-167`, `FW-225`).

## The size budget the plan set, and what was built

The plan's budget (v6, 2026-08-25): `rlxboot` ≤ 32 KiB in its 64 KiB; slot A at
`0x040000` and slot B at `0x1F0000`, 1,728 KiB each; state at `0x3A0000`,
384 KiB; in each slot a kernel (LZMA) ≤ 830 KiB and a root filesystem ≤ 830 KiB,
with 68 KiB to spare. It called the slot boundaries provisional until the erase
size and the locator's `bank_offset` were read. For RAM, of the 26,052 kB Linux
reported (`MEM-06`): kernel ≤ 8 MiB, userspace ≤ 6 MiB, an update buffer of
1.92 MiB, DMA rings and the receive pool about 600 KiB, at least 8 MiB to spare.
TLS was left to the numbers: if the root filesystem without it came to at most
650 KiB, TLS would fit; if not, a smaller library (BearSSL, about 150 KiB against
mbedTLS's 280), MIPS16, or one slot instead of two — which the plan called a real
option, not a failure. `SPEC.md` holds the budget as `TGT-07` to `TGT-09`.

Built instead (`FW-167`, [`update-chain.md`](../notes/update-chain.md) § 6): slot A
at `0x070000` and slot B at `0x190000`, 1,179,648 bytes each, and the
anti-rollback bitmap at `0x3F0000`; a slot holds one image, the kernel with its
initramfs, not a kernel and a separate root filesystem.

## What this page does not establish

- **That no flash byte changed unbidden.** 量 the flash differed from the
  2026-08-16 dump in two 4 KiB sectors, at `0x9000` and `0xD000`, cause
  undetermined (`FLS-26`).
- **That `rlxboot` resists an attacker who can write flash.** By design it does
  not.
- **That the plan's dates are commit dates.** The plan is not under version
  control ([`charter.md`](charter.md), *What this page does not establish*).
