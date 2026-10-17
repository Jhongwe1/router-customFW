Part of [the known-issues index](../KNOWN-ISSUES.md): entry 17 of 19, moved here verbatim from that file on 2026-10-17.

## 🔴 69 citations into `rtl819x-nic.c` rotted in one segment, and they are DECLARED rather than repaired — 2026-09-22

量 2026-09-22, `tools/citecheck.py` on a clean tree immediately after the
hundredth segment's commit, so `0 suspended` and the verdict is real:
**`C3` 69 rotted citations not on the baseline, `C7` 9 new citations onto a
now-blank line**, against `STABLE 310`.

🔴 **The cause is not the `SPEC.md` rows this segment added** — that was my
first reading and it is wrong. `rtl819x-nic.c` went **2,912 → 3,108 lines**
(ethtool ops, the idle ring, `nic_ph_last_cls`, four new dump fields, the
`txrings` verb, two corrected head-comment items), so **every**
`rtl819x-nic.c:NNNN` citation anywhere in the repository moved. The six lines
inserted into `SPEC.md` shift citations into `SPEC.md` itself and are the
smaller half.

⚠️ **Why it is not repaired tonight.** `CLAUDE.md` records that an automatic
citation repairer *"will eventually edit a number a human sentence on the SAME
LINE forbids editing"* — `SPEC.md` already carries one such number, marked
**這一處不准改號碼** because it quotes what a frozen card said. Neither
`citecheck` nor a repairer can tell a live pointer from a historical
quotation; only the prose can. Sixty-nine of those at the end of a long
session is exactly the shape that produces a wrong edit.

🔴 **What this costs right now, stated rather than discovered later**: the
hundredth segment's commits are **not pushed**, because CI runs `citecheck`
and would go red. `citime`'s ledger will therefore show them missing until the
repair lands.

🟢 **The repair is mechanical and the tool hands over the new line numbers**,
but the rule stands: replace only the digits, check the exact old token is on
the exact old line first, re-derive each new number **by reading it back**
rather than copying it from the checker's message, and read the prose on every
line before touching it. The 9 `C7` cases are the ones to do first: a citation
onto a blank line is already meaningless.
