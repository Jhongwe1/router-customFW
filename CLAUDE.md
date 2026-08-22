# CLAUDE.md

rlxfw — an independent firmware for the TOTOLINK N150RT: Realtek RTL8196E, Lexra
core, big-endian, 4 MiB SPI NOR. **One device, no spare.** Built from four
vendors' GPL drops and one leaked draft datasheet, because TOTOLINK never
released source.

> **This file holds only what is true today**, and today the repo is at S0 —
> nothing is built yet. Conventions for files that do not exist are not written
> here; they go in when the file appears. Where this contradicts the repo, the
> repo wins and this file is wrong.

## Where things are

|                   |                                                                                                                             |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **`PROGRESS.md`** | sole owner of *where I am* — active gate, active step, blockers, carried-forward. **Read it first, every session**          |
| **`plan/`**       | gitignored, always present locally. Index: `plan/README.md`.  Whole plan: `plan/.md`                                        |
| **`upstream/`**   | the RE project, submodule pinned at `4d3ff26`, **read-only** — that pin is the whole credibility of R9's differential proof |
| **`$FWRE_WORK`**  | `/home/key/fwre-work` — every binary, shared with `../router`. This project's output goes in `$FWRE_WORK/rebuild/`          |

**A gate is not a session.** R6 is 35 work-segments, about a month. A session is
one step inside a gate. When I say "do R5", ask which driver.

## How to work here

**You build the instruments, I read the dials.** When I state a finding, do not
agree — name the tool that could be lying and the second source that settles it.
Agreeable understatement is how a claim reaches a hostile reader undefended.

- **Every sentence about this machine is marked**: *measured on the device*, *read
  out of the code or the dump*, or *inferred, pending a measurement*. Mixed
  together they are worth neither.
- **No register value enters code on one source.** datasheet → SDK header →
  `devmem`; two must agree, or it is recorded as undetermined.
- **Nothing counts as a result until its refutation condition is written first** —
  what outcome would have proved it wrong.
- **A tool reporting `0` is making a claim.** Every sweep needs a positive control;
  a tool that cannot fail proves nothing.
- **Uncertain is a valid answer** — follow it with the experiment that decides it.
  Five minutes at the bench beats a paragraph of reasoning.
- **Propose before writing** anything over ~50 lines: the approach, and where it
  will fail. **Label estimates as guesses** — nothing here is calibrated yet.
- **Negative results stay in place.** So does the record of being wrong.

## Never

|                                                        |                                                                                                                             |
| ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| write flash                                            | mainline is zero-write through R9. A write needs my explicit yes                                                            |
| touch `0x000000–0x005FFF` or `0x006000–0x007FFF`       | loader — bricked is unrecoverable, there is no spare. `H601` — this unit's MAC and radio calibration, not restored by reset |
| build with `-march=mips32`                             | the load delay slot is architecturally exposed; mips32 miscompiles **silently** — no fault, no warning, just wrong values   |
| write asm under `.set reorder`                         | you cannot know what the assembler filled in. `noreorder`, fill every delay slot yourself                                   |
| measure the ISA or a CPU hazard under Linux            | the kernel emulates `ll`/`sc` and the FPU, so you would measure the kernel. Bare metal only                                 |
| commit the datasheet, a flash dump, or a vendor binary | one is someone else's property; the others identify one physical device                                                     |
| open `$FWRE_WORK/disclosure/`                          | unsent vulnerability reports, mode 600                                                                                      |
| write `RLX5281`                                        | until R1 measures it: "Lexra-family core (RLX4181 or RLX5281, undetermined)"                                                |

## Environment

- **The Bash tool is Git Bash, not WSL.** Dispatch the Linux side:
  `wsl -d Ubuntu-24.04 -- bash -lc 'cd /mnt/c/Users/Key20/Desktop/router-rebuild && …'`
  — `-lc` matters. `$VAR` is stripped and a leading `/` is MSYS-translated, so use
  literal paths or write a script and run that.
- **Binaries never live under `/mnt/c`.** DrvFs drops symlinks and permission bits,
  and on this project the findings *are* filesystem metadata.
- Serial console: CP2102, **38400 8N1**. You cannot see it — at the bench you write
  the commands and read what I paste back. One power cycle is the most expensive
  unit here, so list every question before the device is plugged in.

## Committed files

**Written for an engineer, never for a hiring panel.** State the finding, name the
artefact it was measured on, stop. No résumé bullets, no "this proves I can X".
`plan/` is gitignored and may address me directly; committed files may not.

English, except the working log. Commit messages say *why* — the diff says what.

**Before you stop**: update `PROGRESS.md` § Now, and append a dated entry to
`LOG.md` (create it on the first session) — **including desk-only days**, because
a desk-only day is exactly when the next bench visit's plan changes.
