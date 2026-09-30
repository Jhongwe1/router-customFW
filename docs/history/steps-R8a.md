# `PROGRESS.md` § `R8a`'s step list, archived verbatim

Moved here verbatim from `PROGRESS.md` in `R8a`'s closing commit on 2026-09-30, once its
rows were closed. A record: never edited. Cite a step by its id; `tools/docmove.py`
proves the move.

## `R8a`'s step list — ✅ CLOSED 2026-09-30, in one segment (118th)

**Gate:** the signed update chain, proved with **zero flash writes** (§ Gate
board, row `R8`, split at the flash boundary on 2026-09-30). **Opened**
2026-09-30 by the owner. `R8b` — persistence and the ten power cuts — is booked
and not open: its experiment is an interrupted flash write, so it waits for `R9`
(whose vendor column needs the vendor firmware still bootable from flash), for
its preconditions, and for a dated yes per write.

### Why the split is a ruling and not a convenience

The board row's three clauses were written as one gate. Two of them — a correct
signature accepted, and a single flipped bit rejected — are claims about a
verifier, and a verifier can be driven entirely from RAM: the loader stages a
container and `rlxboot`, `rlxboot` verifies and either boots or refuses, and
nothing is written. The third — surviving ten power cuts during a write —
**cannot** be demonstrated without writing, because the interrupted write is the
experiment. Keeping them in one gate would have smuggled an irreversible,
one-device risk in behind two results that carry none, and it would have spent
`R9`'s evidence base: the first provisioning write to `0x010000` or to a slot
ends the vendor firmware's ability to boot from flash, which is the control
column of the project's own acceptance gate. So the risk is carved out and named
rather than bundled.

### The steps

| Step | | What it produces | DoD | Where it is most likely to be wrong |
|---|---:|---|---|---|
| **`R8a-0`** ✅ **2026-09-30** | desk | This list, the board row's split, and the container format: `RLXU` v1, header then signature then payload, with the verification order pinned | The order is the specification: nothing is copied and no payload byte is hashed before the header's own signature verifies, and the destination bounds are checked before any copy | Repeating the stock loader's defect, which copies the payload to an address taken from the untrusted header *before* checksumming it |
| **`R8a-1`** ✅ **2026-09-30** | desk | `tools/mkfw2.py`, `tools/rlxsign.py` and `tools/flashguard.py` — the plan's precondition ③, and the one new checker this gate justifies, because what it blocks is bricking | `flashguard` refuses the loader region, `H601` and the rescue slot, importing `flashwin.overlaps_forbidden` rather than restating it, **and permits a legitimate neighbour** — a guard that refuses everything is not a guard; `mkfw2` refuses the auto-executed file names and refuses to emit anything the stock loader would accept, proved with the desk reproduction of `check_image()` | A refusal with no positive control, which passes by refusing. A container the loader recognises would let one corrupted byte elsewhere boot an old image without passing through verification |
| **`R8a-2`** ✅ **2026-09-30** | desk | `rlxboot`: a freestanding payload that verifies the container and boots it, with Ed25519 and SHA-512 | RFC 8032 and RFC 6234 vector sets on the host **and** on the target under qemu; a bit-flip sweep over the header and the signature where every single flip is rejected; the crypto's provenance stated — an import is labelled an import, never called mine | Cache handling: this core is write-back without write-allocate, and a missing I-side invalidate after writing code looks exactly like a bad signature. Deep recursion in imported arithmetic on a bare-metal stack |
| **`R8a-3`** ✅ **2026-09-30** | desk | The cross-check: the host signer and the target verifier derive the same public key from one seed, and a container built by the tool verifies inside the payload | Two implementations that share no code agreeing; a mismatch is a finding, not a retry. The counter's flash read exercised against the real erased region, and the rejection case driven from a RAM-staged bitmap, each labelled | Two agreeing because they share a mistake — the reason the seed is fixed and the keys are derived independently |
| **`R8a-4`** ✅ **2026-09-30** | bench | The round on the device: container and payload staged by the loader's TFTP, `rlxboot` entered, and three outcomes read from the console | ① a correct container accepted and the image boots to its own prompt; ② one flipped bit refused, with `RLXBOOT-SIG bad` and no boot; ③ a version below the counter refused, with the counter's source printed. `AUTOBURN` reads `00000000` before any upload and no flash verb is issued in the seating | A refusal that is really a staging failure: the negative cases need the positive one in the same seating to mean anything. The board must not sit at the prompt between rounds (`NET-165`) |
| **`R8a-5`** ✅ **2026-09-30** | desk | The write-up, and `R8b` booked with its preconditions priced: the rescue drill, the MTD write path that does not yet exist, and the layout arithmetic | The entry states what `R8a` established and what it did not — nothing about writing flash, nothing about power cuts, nothing about key management, and no claim of secure boot on a part with no evidence of a key-hash fuse | Letting `R8a`'s success read as the board row met. The row stays open until `R8b` runs |
