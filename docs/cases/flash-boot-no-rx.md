# Booted from flash, `rlx0` received nothing

Found on 2026-10-08 in `v1.0`'s qualification seating; fixed under `R6c`, whose result is the
`R6c` entry of [`docs/GATE-RESULTS.md`](../GATE-RESULTS.md) (2026-10-09). Rows of
[`SPEC.md`][spec] ([how to read one](../spec/README.md)): the `NET-` rows are owned by
[`notes/switch-driver.md`](../../notes/switch-driver.md) §§ 20–21, `LDR-47` by
[`docs/loader-phy-and-switch.md`](../loader-phy-and-switch.md). The record is
[`LOG.md`](../../LOG.md), 2026-10-08, the 127th segment, in Chinese, quoted translated.
Marks: 量 measured on the device, 讀 read out of code or a dump, 推 inferred.

## Symptom

量 `v1.0`'s candidate image, `6a11de02`, booted from flash through `rlxboot` — the stock loader
autobooting, no ESC — brought `rlx0` up and received no frame. 量 After a watchdog reset the
host's ping read 0 of 2 ([`X-V06n.log`](../../bench/2026-10-08/X-V06n.log)); across a
three-packet ping after that reset and again after a cold power-on, `rlx0`'s RX and TX stayed at
0, and after the cold boot the driver read `n_rx 0` and `n_irq 0` with its engine on ([`NET-171`][spec]).

## First hypothesis, and why it was wrong

No record in this repository written before the cause was known states a hypothesis: the card,
finalised before the first capture (the 127th entry), ran the host's pings *"so the host reaches
the image that has just booted"* and named no network risk among what it did not establish
([`V10-CARD.md`](../../bench/2026-10-08/V10-CARD.md)). Outside it, the cold boot's session script,
`$FWRE_WORK/rebuild/s127/bench/phase4c.sh` — uncommitted, dated only by its file times, which
put it before `V08` — names *"H1 (rlx0 needs the loader's ESC-path Ethernet init, LDR-46): ping
0, rlx0 RX 0"* and *"H2 (a watchdog reset wedges ingress, notes/nic-driver.md 6): ping answered"*.
量 The cold boot refuted H2 ([`NET-171`][spec]). The open case was on record: § 17.4 of the notes
listed the VLAN group on the flash autoboot path among what driver 1.5 did not establish, out of
reach under `R9`'s zero-write rule, and nothing re-opened it once `R8b` made it reachable
([`NET-171`][spec]).

## The single-variable cut

量 After the same kind of reset, a watchdog reset, the same image answered 2 of 2 when the
loader stopped at its prompt and the image came from RAM (`V02`,
[`X-V02n.log`](../../bench/2026-10-08/X-V02n.log)), and 0 of 2 when the loader autobooted and
`rlxboot` started it from flash (`V06`, `X-V06n`). 量 The cold row agrees, with its prompt cell
the evening before and another image: a cold boot to the prompt
([`bench/2026-10-07/C03.log`](../../bench/2026-10-07/C03.log)) was followed by an upload to the
image over TCP, and the cold autoboot `V08`, the card's phase 4, was deaf. 量 It follows the
loader's path, not the reset; each cell is one or two boots ([`NET-171`][spec]; notes § 20). The
127th entry sets them out after the owner's question, *"Is it a watchdog problem?"*.

## Cause

Two sources agree, and the mechanism is 推 ([`NET-171`][spec]). 讀 The loader initialises
the switch only on the path that enters its prompt; an autoboot's stage 2 stores nothing to the
switch, its tables or the CPU interface ([`LDR-47`][spec]). 讀 rlxfw's mainline left the VLAN
group to the loader (notes § 16.8; [`NET-171`][spec]). 量 After the cold autoboot, 10 of the
switch's 37 register rows read reset values where a prompt-path RAM boot does not
([`NET-171`][spec]), its three tables were empty, and port 3 counted every frame from the host
into its discard counters, none reaching the CPU port ([`NET-172`][spec]). 推 Whether ingress
filtering or a VID with no entry discards them is not separated ([`NET-172`][spec]).

## Positive control

量 The ping and the host could see a working path that night: the prompt-path cells answered
(`X-V02n`). For the fix, 量 the release image `9bb2bec7`, booted from slot A, pinged both ways
after a watchdog reset and after a cold power-on, 4 of 4 each way on each boot, and port 3's
discard columns stayed at 0, with `vlan` storing 17 words on the flash path (notes § 21.6;
[`NET-173`][spec]). The control is the deaf boots of `6a11de02`, another image on other boots:
no cell took the write set away on one boot (`R6c` entry, the weakest-thing paragraph).

## The check left behind

讀 Driver 1.6's verb `vlan` writes the loader's one-VLAN layout wherever the switch differs
from it, and PID 1 types it between `init` and `start` ([`NET-173`][spec];
[`src/init/main.c`](../../src/init/main.c), `lan_verbs`).
[`tools/mdiocheck.py`](../../tools/mdiocheck.py) compiles the driver's switch block with the
host's gcc against a model of the table engine: case `K48` replays the flash path access by
access, 17 stores and one table command under `STOP_TLU`, `K49` the RAM path, and mutants
`M52`–`M55` must each turn `K48` red. CI runs it: workflow `instruments`
([`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)), job `instruments`, step
`mdiocheck`; it turns red if `vlan` stores anything else on either path. It cannot see the
silicon, its engine modelled from the vendor readings the driver follows, nor whether PID 1
types `vlan` at all: it reads only the driver, and no test reads `lan_verbs`, so 推 dropping
the verb from PID 1 would leave CI green.

[spec]: ../../SPEC.md
