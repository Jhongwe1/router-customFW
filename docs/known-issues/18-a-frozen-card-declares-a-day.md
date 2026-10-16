Part of [the known-issues index](../KNOWN-ISSUES.md): entry 18 of 19, moved here verbatim from that file on 2026-10-10.

## 🔴 A frozen card declares a day none of its captures happened on — 2026-09-23 (desk)

量 2026-09-23 by `tools/capdate.py`'s card checks (`D5`–`D10`, `CAPD-1`) on
their first sweep. `bench/2026-09-21/PREDICTIONS-B35-block33.md` says
**declared date 2026-09-21**, and all 22 of its dated fenced captures started on
**2026-09-20**, 23:16:54–23:27:08, as did 24 of the 37 dated captures in its
directory that no card fences (23:28:26–23:59:55; the other 13 ran 00:00:15–00:07:47
on 2026-09-21). The card was committed at 2026-09-20 23:16:35; the seating crossed
midnight at `W2-START`, 33 minutes after its last dated carded capture. The
directory check could only report the directory as spanning two days (`D2`);
the card check is what names it. This is the two misnamed directories' failure
(the section headed *Two bench directories are named for a day none of their
captures happened on*), one level down: a date written before power is a
prediction, and this one was wrong by one evening.

The card is **not edited**: a frozen card is never repaired, and `git grep` at
`5972a2a` finds 11 references to it in 9 other files, one of them another frozen
card (`bench/2026-09-21b/PREDICTIONS-B36-block34.md`). It is declared by name in
`capdate.KNOWN_CARD_DATE`, for `D7` and `D8` only, and that list is swept in both
directions like `KNOWN_MISNAMED`.

What this does not establish: which day the seating's owner meant. It says only
that the card's claim and the host clock disagree. The check runs after the
captures exist; before power, a declared date can only be compared with the
directory name, which is the same prediction written twice. `P2`'s seatings plan
not to cross midnight, and split the directory and the card if they do.
