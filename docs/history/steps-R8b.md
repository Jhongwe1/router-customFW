# `PROGRESS.md` § `R8b`'s step list, archived verbatim

Moved here verbatim from `PROGRESS.md` in `R8b`'s closing commit on 2026-10-08, once its
rows were closed. A record: never edited. Cite a step by its id; `tools/docmove.py`
proves the move.

## `R8b`'s step list — ✅ CLOSED 2026-10-08, in three segments (124th, 125th, 126th)

**Gate:** persistence and the ten power cuts (§ Gate board, row `R8b`). **Opened**
2026-10-05 by the owner, continuing the relaxation of 2026-09-27 and 2026-09-30;
the flash rules, `H601`, the power handshake and `NET-165` did not relax, and
every flash write is a separate dated yes for that exact payload (`FW-113`).
**The 123rd segment's "no tool question is left undecided" was wrong**: 讀
nothing in userspace reaches the MTD write engine (`MTD_CAP_ROM`, and
`tools/mkinitramfs.py` refuses a writable node), and `rlxboot` verifies only a
container staged in RAM at `0x81000000`. `R8b-1` and `R8b-2` are those two
pieces. The slots hold mainline images; only a RAM-booted armed image writes.

### The steps

| Step | | What it produces | DoD | Where it is most likely to be wrong |
|---|---:|---|---|---|
| **`R8b-0`** ✅ **2026-10-05** | desk | This list and the board row | the board row reads `~` and names this list | — |
| **`R8b-1`** ✅ **2026-10-05** | desk | `rlxboot` boots from flash: verifies slot A and slot B, boots the higher valid version (a tie boots A), halts naming both reasons when neither verifies; a build-time key selector whose flash build refuses without the owner's public key | a host test per case, `qemutest`, and the flash build shown refusing and building | the delay of two verifies through the flash window, which no desk test measures |
| **`R8b-2`** ✅ **2026-10-05** | desk | the armed build's install path: `/proc/rtl819x-spi-img`, `install <region> sha=<hex>`, `erase barrier`, commit-by-header over a compiled-in region table; `cardcheck` refusing those verbs without an `owner-yes` row | each guard shown refusing and permitting; a mainline image's driver code unchanged | the write rate, which decides whether a hand can land a pull inside a write |
| **`R8b-3`** ✅ **2026-10-05** | desk | the payloads: a mainline image on the release recipe, containers P, Q, R (versions 1–3) signed by the owner, `rlxboot` and rescue `cr6c` on the production key, and the armed image they are sent to over `nc` (inside it they overrun the decompression ceiling, `FW-240`) | every digest recorded, two builds byte-equal | the release recipe moving after these builds |
| **`R8b-4`** ✅ **2026-10-05** | desk | the bench plan and the owner's dated yes for each write | one `owner-yes` row per payload, and `cardcheck` reading them | an ordering step that needs the vendor kernel after it is gone |
| **`R8b-5`** ✅ **2026-10-07** | bench | pre-flight with the board off; the readings that need the vendor kernel (`C-1`, `C-13`, the barrier pre-read); then `rlxboot`, rescue, slot A, the barrier erase, slot B, each booted | every write read back and every boot identified by tool | the erase size (**未定**, `FW-227`) |
| **`R8b-6`** ✅ **2026-10-07** | bench | ten pulls inside a write, each followed by a boot from the other slot | ten boots read `RLXBOOT-SLOT` and `RLXFW-ID0` by tool | a pull that lands outside the write, which counts as a control, not a pass |
| **`R8b-7`** ✅ **2026-10-08** | desk | the result: a `docs/GATE-RESULTS.md` entry; `C-1`, `C-3`, `C-4`, `C-13` answered or re-owned; the `SPEC.md` rows | `cfcensus` and `spec-check` green on the closing tree | — |

