Part of [the known-issues index](../KNOWN-ISSUES.md): entry 13 of 19, moved here verbatim from that file on 2026-10-17.

## 🔴 A one-word correction that cannot be made without invalidating evidence

量 2026-09-16 (`R1z-3`). `tools/isa-payload.tsv`'s `special0e` row carries
`C2` in its `why` column where the answer is `C5`. The correction is one token
and it has been carried in this project's record seven times.

It is not a carry. The handover rule this project applies — *a row handed over
more than twice must be `⊘` or done now* — has *a change of owner* as its
subject, and across all seven the owner, the reason and the expiry were
identical. Counting them counts segments elapsed.

🔴 **The block is measured.** That column's text goes verbatim into
`cells4.S` and `BUILD_ID` is a digest over that file, so the edit moves
`a87be346bb83e7f9` → `43ddceb652831584` — and three committed bench captures
plus two frozen cards cite the former. Making the correction today would
invalidate evidence in order to satisfy bookkeeping, which is the wrong
direction: this project repairs the record to match the measurement and not
the other way round.

So it is a **rider on the next rebuild**, and its expiry is observable with no
new tool: the first committed capture that prints a `BUILD_ID` other than
`a87be346bb83e7f9`. 🔴 **No checker enforces that, and the absence is named
rather than assumed** — a new instrument is outside `R1z`'s scope, and a check
that would be red from today until the next rebuild is the shape this
repository already refuses, because a permanently red gate trains a reader to
stop reading reds.
