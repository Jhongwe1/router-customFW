# Disclosure

How rlxfw handles the vendor defects that its pinned reverse-engineering project, `upstream/`,
marks *held*: not yet reported, so their reproductions stay unpublished. This page holds not one
finding. What each defect is, and its state, belong to upstream's register,
[`docs/disclosure.md` at the pin `4d3ff26`](https://github.com/Jhongwe1/router-firmware-re/blob/4d3ff26bfb8a32986d3db532ca25197ef3043fdb/docs/disclosure.md).
Nothing here is about the device: each statement is read (讀) from the committed file it cites,
and the unsent reports kept outside this repository were not opened to write it. The page's other
half, the findings, is declined in [`GATE-RESULTS.md`](GATE-RESULTS.md), `R9`'s entry, with its
reason and category: its blocker is a report that has not been sent, which is a decision and not
a missing instrument.

## What is held

Thirteen of the register's nineteen ids are held at the pin. [`threat-model.md`](threat-model.md)
§ *Scope* owns the list and the date it was read; re-read at the pin on 2026-10-20, it is the same
thirteen. This page sorts none of them by class: the register leaves `D-9` deliberately
unclassified, and a class given here would be a finding written outside its owner.

## Categories

The register publishes by category, in one sentence of its own: *findings are published,
reproductions follow the disclosure state, tradecraft is not published at all* (its § *The
publication rule*). How this repository writes about the vendor is set out in three tiers, owned
by [`charter.md`](charter.md) § *Disclosure*. For the differential table the rule has an
instrument: its renderer refuses content from any of the thirteen, at class level or below
(`tools/diffrender.py`, guard `D5`; the table is [`differential.md`](differential.md)).

## Contact and deadlines

From the register's § *Procedure when something does become reportable*; [`charter.md`](charter.md)
§ *Disclosure* states the same contact and clock:

- a report goes to TWCERT/CC with the reproduction, after a demonstration on the hardware and a
  prior-art search for that handler and parameter; the procedure plans for silence from the vendor;
- the reproduction stays unpublished until the coordinator closes the case or 90 days pass from
  the report, whichever comes sooner, and the date the clock started goes into the register in the
  same commit as the report;
- a case the coordinator declines is a decision, written into the register with its date, and not
  a licence to publish at once.

## Timeline

| date | what | read from |
|---|---|---|
| 2026-08-19 | the register's last change before the pin; it says that nothing in it has been reported to anyone | the register at `4d3ff26` |
| 2026-08-22 | the pin, `4d3ff26` | `upstream/`'s history |
| 2026-10-04 | thirteen held, read at the pin; and, in the same file, nothing has been sent | [`threat-model.md`](threat-model.md) § *Scope* and § *What this threat model does not establish* |
| 2026-10-04 | the findings half of this page declined, because the report has not been sent | [`GATE-RESULTS.md`](GATE-RESULTS.md), `R9`'s entry |
| 2026-10-20 | the thirteen re-read at the pin; searched for TWCERT/CC, this repository holds the rule in [`charter.md`](charter.md) and not one record of a send | this page |

None of the thirteen has a report date in any committed file, so none of their clocks has started.

## What lets a held item in

[`progress-release-clock-2026-10-09.md`](history/progress-release-clock-2026-10-09.md) records
that held items stay out until this page says otherwise. Three committed rules decide what it can
say, and read together they leave one way in:

- a named fix follows the upstream project's disclosure state, and a reproduction stays out while
  a report is held ([`charter.md`](charter.md) § *Disclosure*);
- that state changes when the coordinator closes the case or 90 days pass from the report, and
  the report's date goes into the register in the commit of the report (the register's procedure,
  step 4);
- the pin does not move: `R9`'s differential is credible only against a baseline this repository
  cannot edit (`SOURCES.json`'s entry for `upstream/`; `CLAUDE.md`, § *Never*).

So the register as this repository pins it reads *held* for all thirteen, permanently. An item
comes in only after a later commit of the register records its report date and a closed case or
90 passed days; reading that commit leaves the pin where it is, and this page names the commit and
the date it was read. Reporting is the author's act (`README.md` § *How it was built*); a report
is read from the register, never inferred from silence.

## What this page does not establish

- the register's state after the pin;
- that a report has been, or will be, sent;
- that TWCERT/CC will take a case about end-of-life hardware: the register's procedure expects
  that it may decline one;
- anything about the held items themselves, or about the device.
