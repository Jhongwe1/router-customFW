# Pre-registered prediction for block 19's off-card repeat round

**Written 2026-09-14, seating 22, at the bench, between `C1-P6rb` and
`X1-P6j2`.** The board is at the loader prompt. No capture named below exists
yet. This file is committed before the round runs, for the same reason
`CORRECTIONS-block19.md` § 0.1 is: an ordering a reader can check in git beats
a sentence claiming one.

`PREDICTIONS-B20-block19.md` § 10 declares the round. This file adds what that
paragraph could not contain, because it did not exist when the card froze: two
of the card's field predictions were refuted by `C1-P6j` tonight, an
explanation was derived from the payload's own source, and **the second run is
what can refute the explanation.**

---

## 1. What was refuted, and the explanation being tested

`C1-P6j` read `install.changed=00000015` (21) against the card's `0000002b`
(43, with `2c` admissible), and `restore.stillhdl=00000001` against `00000000`.

讀, `tools/rlxprobe/probe6.c:218-245` against `tools/rlxprobe/probe5.c:220-249`:

* **`ins_changed` changed shape.** `probe5` counts a difference at
  **both** `VEC_UTLB` and `VEC_GENERAL` (two `ins_changed++` sites, :241 and
  :246), so its ceiling is `2 × 22 = 44`. `probe6` counts **only**
  `VEC_GENERAL` (one site, :232), ceiling `22`. Both payloads *write* both
  vectors; only the counting differs. `43 = 44 − 1` and `21 = 22 − 1`.
* **`res_stillhdl` lost a guard.** `probe5:488-494` counts a word only if
  `saved_vec[...] != rlx_exc_entry[i]`, with the comment *"A restore that put
  back a word which was already equal proves nothing."* `probe6:465-467` drops
  that condition, so it also counts the word that was already equal.

**The explanation**: exactly one of `VEC_GENERAL`'s 22 words already held the
value `probe6`'s handler wants. It is invisible to `install.changed` (counted
as *not changed*) and visible to `probe6`'s unguarded `restore.stillhdl`
(counted as *still holds the handler*). `restore.mismatch = 0` — the field that
actually reports whether the restore worked — says every word went back.

**The identity**: `install.changed + restore.stillhdl == install.words`.
Tonight: `21 + 1 == 22`. This identity is not in the payload, is not in the
card, and holds only if the explanation above is right.

## 2. The prediction

`X1-P6j2` is the same binary at the same address on the same power cycle,
entered from a **watchdog-reset** prompt rather than a **cold** one.

| field | predicted | |
|---|---|---|
| `install.words` | `00000016` | fixed by the ELF |
| `install.changed` | `00000015` | |
| `restore.stillhdl` | `00000001` | |
| `install.changed + restore.stillhdl` | **`00000016`** | the identity above |
| `install.bad` | `00000000` | 44 read-backs, both vectors |
| `restore.mismatch` | `00000000` | |
| `flags` | `50010002` | device build, not qemu's `50070002` |
| `pc` | `80501258` | |
| `split` | `00000000` | |
| `trapped` / `cell.bad` | `00000000` | |
| report window | **1,808 bytes** | `C1-P6j` hit it exactly |
| the twelve rows | **5 LOCK, 7 OPEN**, each row the verdict its `pad` column predicts | |
| `c_lock` / `c_open` | LOCK / OPEN | without both, no verdict is reported |

## 3. Refutation, written first

| id | if this happens | what it refutes |
|---|---|---|
| `X1-a` | `install.changed + restore.stillhdl ≠ 22` | **§ 1's explanation.** The two fields are then not two views of one word and the cause is elsewhere |
| `X1-b` | `install.changed` is `21` and `restore.stillhdl` is `0` | the unguarded-counter reading. The word that was already equal would then not be being counted after the restore, and `probe6`'s omission of the guard is not what produced the `1` |
| `X1-c` | either field differs from run 1 at all | 🟢 **not a refutation — a finding about the LOADER.** Run 1 entered from a cold boot and run 2 from a watchdog reset; a change means the loader leaves the exception vectors in a different state on the two paths, which nothing in this repository has measured |
| `X1-d` | any row's verdict differs from run 1 | the table is not a property of the die and the compiler; *this is what the die did* would not become *this is what the die does* |
| `X1-e` | either control fails (`c_lock` not LOCK, `c_open` not OPEN) | `tcpay` refuses a verdict rather than reporting one, and run 2 says nothing |
| `X1-f` | the window is not 1,808 | a line is missing, an abort line fired, or the capture truncated — `PREDICTIONS-B20-block19.md` § 5.3 lists the four causes |

## 4. What this round does not claim

* It is **not** an independent build. Same binary, same sha256, same address.
* It is **not** a second measurement of the load-use hazard. That is `CPU-58`
  (`CORRECTIONS-block19.md` § 0.3.5 corrects the card's `CPU-14` to it).
* Zero flash-write commands. One upload, guarded by a `DW 8040D4A0 1`
  read-back that `CORRECTIONS-block19.md` § 0.3.3 requires and the card's own
  off-card paragraph omitted. The bracket stays at **1,024 of 4,194,304 =
  0.0244 %**.
