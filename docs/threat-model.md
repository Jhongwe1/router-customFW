# threat-model — the positions this device is actually attacked from, and what rlxfw does about each

`R9-9`, 2026-10-04. This is **rlxfw's** threat model, for the TOTOLINK N150RT
as this project runs it: a RAM-booted image on one unit, with the vendor's
loader intact in flash, the vendor's WLAN driver inside rlxfw's own kernel, and
nothing written to flash through `R9`.

**It does not claim rlxfw is secure.** Counted from § 1's table rather than
estimated: **two** of the nine positions are **unmitigated** (`T5`, `T6`), one
has **near-zero containment** and is named rather than argued away (`T7`), one
is bounded only by a default that one typed verb removes (`T4`), one position's
reach is **未定** (`T3`), and the remaining four are bounded — one of them for
half of what it covers (`T8`). What it does claim is that each position is
named, that what rlxfw does about it is a reading rather than an intention, and
that where rlxfw does nothing the file says so.

Marks: **量** measured on the device, **讀** read out of code, a dump or a
document, **推** inferred, **未定** open with a row in
`docs/hardening-matrix.md` § 4 saying what settles it.

## 0. Scope, and the disclosure rule this file is written under

**In scope**: rlxfw's own attack surface, and the positions a deployed unit of
this model is reachable from.

**Out of scope, and not because it is uninteresting**: the vendor firmware's
per-defect detail. Those findings belong to the pinned reverse-engineering
project, and 讀 2026-10-04 from `upstream/docs/disclosure.md`'s status column
at the pin `4d3ff26`, **thirteen** of its ids are marked held — `D-3`,
`D-4`, `D-9`, `D-10`, `D-11`, `D-12`, `D-13`, `D-14`, `D-15`, `D-16`, `D-17`,
`D-18`, `D-19` — with `D-19` additionally marked NOT SEARCHED. ⚠️ `plan/` § 15
says four; the file at the pin says thirteen, and the file wins.

So the rule here, from `plan/` § 15: a **class-level** statement about rlxfw's
own design is publishable; a **named** statement pointing at a specific vendor
line, address or handler follows the disclosure state and is not written while
that state is held; and a **reproduction** — a request anyone could paste —
never appears in this repository while any of those rows is held, and none has
been sent. Where the vendor appears below it appears as one of `plan/` § 8's
published category names, or as prior art with a CVE id, and never with an
endpoint, a parameter name, a payload or an ordering.

**What `docs/KNOWN-ISSUES.md` owns and this file does not restate**: the
defects in rlxfw's own code, including the two the first boot of rlxfw's
userspace found. One piece of state has one owner.

## 1. The positions

| # | position | what it can reach | state |
|---|---|---|---|
| **`T1`** | **LAN peer, unauthenticated** | rlxfw's `httpd` on 80 and `dnsfwd` on UDP 53 (讀 `notes/dnsfwd.md` § 1; 量 both answering on the device, `SPEC.md` `FW-175`), `udhcpd` when `dhcpd.enable` = 1 (讀 `notes/init.md` § 4), ICMP, and the switch's forwarding behaviour | **bounded**, § 2 |
| **`T2`** | **LAN peer with valid credentials** | everything `T1` reaches, plus `brokerd`'s session-gated ops through `httpd` | **bounded**, § 3 |
| **`T3`** | **WAN-side peer** | **未定** — which rlxfw services bind on a WAN interface has not been read; 🔄 2026-10-08: rlxfw has no WAN, and 推 the port the vendor runs as WAN is in rlxfw's LAN VLAN (`NET-174`) | **未定**, § 4 |
| **`T4`** | **Wireless client associating to the radio** | the vendor's WLAN driver directly, in kernel context | **bounded only by the radio being down**, § 5 |
| **`T5`** | **Physical attacker with the board** | the SPI flash off-circuit, the UART console, the loader prompt, every byte of RAM | 🔴 **unmitigated**, § 6 |
| **`T6`** | **Anyone who reaches the loader prompt** | the loader's unauthenticated TFTP rescue, arbitrary memory writes, and a flash burn | 🔴 **unmitigated by design**, § 7 |
| **`T7`** | **The vendor WLAN driver, as code in rlxfw's kernel** | the whole kernel address space, the loader's RX DMA footprint, the watchdog | 🔴 **near-zero containment**, § 8 |
| **`T8`** | **A malicious or corrupt update image** | whatever `rlxboot` accepts | **bounded for the verification half only**, § 9 |
| **`T9`** | **A peer that already holds a uid on the box** | the broker socket, and whatever that uid's row in the op table allows | **bounded**, § 10 |

## 2. `T1` — LAN peer, unauthenticated

**What it reaches.** 量 2026-09-30, first boot of rlxfw's own userspace
(`SPEC.md` `FW-175`): `httpd` runs and answers, `dnsfwd` runs and answers,
`brokerd` listens on a unix socket, `udhcpd` runs, and `rlx0` carries
`10.1.1.1/24`. 量 `SPEC.md` `NET-167`: `rlx0` pings both ways after a cold
power-on and after a warm reboot with no command typed.

**What rlxfw does.**

* **Default deny on the route table.** 讀 `notes/httpd.md` § 2: the route table
  is the whole of what is reachable, exempt endpoints are enumerated rather than
  matched, and comparison is whole-string equality. This is the 架構性 answer to
  the vendor's authorisation class, and it replaces substring matching with a
  table.
* **No command interpreter anywhere on the path.** 量 2026-09-30 (`SPEC.md`
  `FW-177`): over the shipping bytes, all six of rlxfw's programs read **0**
  forbidden names from both of `tools/uspacescan.py`'s sources, with the
  permitted `execve` and `fork` counted separately. 讀 `notes/init.md` § 4:
  every child is `fork` + `execve` with an argv of string literals and a fixed
  three-entry environment — **not one argv byte comes from the config store, a
  lease, or the kernel command line**.
* **A bounded request parser, fuzzed.** `notes/httpd.md` §§ 3, 6, 7 own the
  limits table, the path decoder, the traversal battery and the fuzzing runs,
  including the planted defect and its attribution.
* **Privilege separation, verified by reversing it.** 量 `FW-175`: `httpd` as
  uid 100 inside a chroot on `/srv/www`, `dnsfwd` as uid 101 printing
  `setuid(0) refused (Operation not permitted)`. The host-side battery is 24 of
  24 cases read out of `/proc/<pid>/status` or off the wire, never out of the
  program's own printout.
* **Fail-closed on entropy, and today that means refusing.** 量 2026-09-30:
  `entropy_avail` reads **0** at 768 s and **0** at 1613 s of uptime, and **0**
  through a burst in which 400 ICMP echoes round-tripped and two interrupt
  counters moved by ~770 and ~7,700. `brokerd` answers `NOENTROPY` to `LOGIN`
  and `PWSET` until it has seen `entropy_avail >= 128` once, so on this board as
  it stands **rlxfw issues no session token at all**. The alternative — handing
  out 16-byte tokens from a pool the kernel reports as empty — is a predictable
  token shipped to hide a kernel gap.
* **A per-client connection cap that does not let one address hold the server
  shut.** 量 (`notes/httpd.md` § 4): four silent peers from one address, then a
  request from a second address answered **200**; the fifth connection from the
  first address **503**, not a queue.

**What rlxfw does not do.**

* **No transport security.** Management is plaintext HTTP. 讀 `plan/` `D8`: TLS
  is conditional on the size budget and the decision was left to the numbers;
  no TLS library is in the image and none has been measured into it.
* **No reading of this surface under attack.** The fuzzing and the sweeps are
  host-side; the device readings are of a cooperative boot. ⚠️ The limiter is
  the exception that proves the point: it worked in the host battery and then
  misbehaved on the device, and `docs/KNOWN-ISSUES.md` owns that.
* ⚠️ **Two owner files predated the boot and said so; both were corrected on
  2026-10-04 rather than left to be read as current.** `notes/dnsfwd.md` § 10
  read *nothing has run on the device* and *dnsfwd has never bound :53 …, never
  dropped privileges there*, and `notes/httpd.md` read *nothing in this note has
  run on the device* with § 10 adding *the privilege drop and a real KDF
  evaluation are still unmeasured there* and *no broker has answered*. 量
  `SPEC.md` `FW-175` and `FW-176` falsify all of those. Each file now carries
  the current value and one line pointing at the owner of the correction; the
  device readings above come from `FW-175`, `FW-176`,
  `notes/userspace-integration.md` and `docs/GATE-RESULTS.md` entry 17.
* **Nothing about the switch's own forwarding.** 讀 `notes/switch-driver.md`
  § 21: `vlan` writes the loader's VLAN group and `FFCR`'s two traps, as the
  owner ruled (`SPEC.md` `NET-173`); EEE and the CPU queue count stay as
  booted. A LAN peer's reach through the switch is that layout's policy.

## 3. `T2` — LAN peer with valid credentials

**What it reaches.** `brokerd`'s session-gated ops, through `httpd`. 讀
`notes/broker.md` § 2: `ops.c`'s `rules[]` is the whole authorisation, no op
handler reads a uid, and one function — `authorise` inside `bk_dispatch` —
decides.

**What rlxfw does.** Session token plus CSRF on every mutating op; a wrong CSRF
answers `PERM` rather than `AUTH`, so a CSRF mismatch does not log the user out;
`GET` refuses a `WEB_HIDDEN` key to a non-root peer, so `admin.pwhash` cannot
leave through `httpd`; `UPDATE_*` answers `NOTSUP` to every uid; the entropy
gate applies to every uid, **root included**; and the login rate limiter is
keyed on the effective client address with root deliberately exempt, because
locking the console out buys nothing against a peer that already owns the box.
The KDF is scrypt with parameters chosen from an anti-DoS budget written before
the measurement (`notes/httpd.md` § 5).

**What rlxfw does not do.** There is no second factor and no account lockout
beyond the rate limiter. 讀 `notes/broker.md` § 3: the broker socket is mode
**0666** with `SO_PEERCRED` as the whole authorisation, because mode bits cannot
express `{0, 100, 101}` without a supplementary group, and `/etc/group` is
`init`'s file. The directory is **expected** at 0711 `root:root` — expected, not
asserted on the device by any reading this file can cite.

## 4. `T3` — WAN-side peer

**未定, and narrower than it first reads — three of the four daemons are
already bounded by a reading.** 讀 `notes/broker.md` § 3: `brokerd` listens on
a **unix socket**, so it is not reachable from any network peer. 讀
`notes/dnsfwd.md` § 1: `dnsfwd` binds **UDP :53 on the LAN address**, named
explicitly. 讀 `notes/init.md` § 4: `udhcpd` starts only when
`dhcpd.enable` = 1 and `udhcpc` only when `wan.mode` = 1, and `wan.mode` has
never been set on any image that has booted, so **no boot has brought a WAN
interface up**.

🔴 **What is left is one daemon and one line.** `notes/httpd.md` says `httpd`
*binds TCP :80* and `bind(:80)` without naming an address, where `dnsfwd`'s
equivalent sentence names the LAN address — so whether `httpd` takes the
wildcard or the LAN address is the whole of this position's open value.
`SPEC.md` `FW-177` 殘留 ③ is one read of `bind` in `src/httpd/serve.c` and
settles it at the desk; the host probe from the WAN side was given to `P3`,
deliberately not to `R9`, because a WAN arm would add an uncontrolled variable to
the one vendor seating that gate could afford. 🔄 2026-10-08: `P3` closed without
it, and `SPEC.md` `FW-177` 殘留 names who holds it now.

⚠️ So this file **cannot** say rlxfw's WAN exposure is smaller than the
vendor's. It can say the vendor's WAN reachability for one service class was
also never settled, which is upstream's open question and not an rlxfw result.

🔴 **🆕 2026-10-08 (130th segment): the premise above holds for interfaces, and
not for the port.** rlxfw has no WAN: the switch layout it runs — the loader's on
every RAM boot through the prompt since `R6`, and since `rtl819x-switch` 1.6 its
own on a flash boot too — puts ports 0–5 in one VLAN, untagged (slot 8
`00807E3F`, read back on all three of `R6c-4`'s paths), and port 0 is the port the
vendor firmware runs as its WAN, on VID 8 apart from the LAN's VID 9 (`SPEC.md`
`NET-04`). 推 So a peer on port 0 is a LAN peer to rlxfw: it reaches `rlx0`, and
`dnsfwd`'s LAN address and `httpd` with it, whichever address `httpd` binds. No
boot has had a peer on port 0 and its link under rlxfw was not read; port 0 is
the jack labelled WAN (量 2026-08-25, `NET-13`), so this is 讀 and 推 and not a
probe (`SPEC.md` `NET-174`). Until a WAN exists, that jack is not a boundary.

## 5. `T4` — a wireless client associating to the radio

**What it reaches.** The vendor's WLAN driver, in kernel context, with the reach
of `T7`. 量 `SPEC.md` `RF-01` (value 量 from the part, name 讀): the radio is a
separate Realtek RTL8188ER, 1T1R 802.11n, 2.4 GHz. 量 `RF-07`: the vendor's
firmware brings WPS up at boot.

**What bounds it today, and it is one reading rather than a design.** 讀
`notes/init.md` § 4: rlxfw's supervisor table has **no** wlan entry, so rlxfw's
`/init` does not bring the radio up. 量 `SPEC.md` `FW-51` 殘留: a seating did
bring it up by typing `ifconfig wlan0 up`, with the antenna connected — so the
interface **can** be raised, and when it is, this position is open.

**What rlxfw does about it.** Nothing. There is no rlxfw WLAN driver, no
association policy of rlxfw's, and no WPA implementation of rlxfw's. The radio
being down by default is the whole of the mitigation, and it is one line of a
supervisor table rather than an enforcement.

## 6. `T5` — physical attacker with the board

🔴 **Unmitigated, and it is accepted rather than unsolved.**

**What it reaches, each with a reading.**

* **The flash, off-circuit.** 量 `SPEC.md` `FLS-01`: an Eon (cFeon)
  **EN25QH32B** in an **SOP-8**, board marking `U19`. A clip reads or writes it.
* **The console.** 量 `SPEC.md` `BRD-10`: the console is **38400 8N1** at a
  logic level of **3.3 V**, both marks 量 — the narrowest pulse measured at
  26 µs against 38400's 26.042 µs, self-checked against a 52 µs pulse in the
  same capture and confirmed by decoding to readable ASCII. Nothing
  authenticates it.
* **The loader prompt**, which is `T6`.
* **Every byte of RAM**, because 量 `SPEC.md` `MEM-17`: DRAM survives a power
  cycle on this board.

**What rlxfw does.** Nothing, and the reason is a chain of readings rather than
a preference. Full-disk encryption has nowhere to anchor a key: there is no
secure storage any reading in this repository names, 量 `CPU-42` shows CP0
`Count` reading 0 and not moving so there is no cycle counter to jitter against,
and `entropy_avail` reads 0 on this board, so a key generated here today comes
out of a pool the kernel reports as empty. Whether the part carries an OTP or
key-hash fuse at all is **⊘ out of scope rather than 未定**: the current value
is `PROGRESS.md`'s `R8a` row, *no evidence of a key-hash fuse*, which is an
absence of evidence and not evidence of absence — and a device-side probe for
one is not proposed, because it would mean writing a one-time-programmable
region on the only unit.

**What rlxfw also does not do, and this is the honest part.** rlxfw's own rules
make the physical position *worse* to defend, deliberately: the loader region
`0x000000`–`0x005FFF` and `H601` at `0x006000`–`0x007FFF` are permanently
unwritable by this project's rule, because a brick is unrecoverable and there is
no spare. So the one component that could enforce a root of trust is the one
component rlxfw may never replace.

## 7. `T6` — anyone who reaches the loader prompt

🔴 **Unmitigated by design. The loader's TFTP rescue is a feature, and removing
it bricks the device.**

**What it reaches, each with a reading.**

* **An unauthenticated TFTP server.** 讀 `SPEC.md` `LDR-25`: the loader is a
  TFTP **server**, not a client, with a compiled-in address of `192.168.1.6`.
* **Two filenames that bypass the normal path.** 讀 `LDR-26`: both of them set
  *execute at the instant the transfer ends*. 讀 `LDR-37`: only one of the two
  also forces the write pointer, to `0x80000000`, **over the UTLB refill and
  general exception vectors** — it destroys the loader's own exception handling
  mid-transfer.
* **A flash burn with no further command.** 量 `LDR-23`: `AUTOBURN`'s initial
  value is **1**, exactly one instruction in the whole image reads it, and that
  instruction is on the upload-completion path. An upload with no prior
  `AUTOBURN 0` is burned.
* **Arbitrary memory writes.** 量 `LDR-08` and `LDR-09`: `EW` writes 4 bytes
  and `EB` writes 1 byte to **any** address with no bound check and no output,
  and 讀 `LDR-11` counts **four** arbitrary-write paths in total, the
  post-`LOADADDR` TFTP write among them.
* **The prompt itself, from power.** 量 `LDR-15`: the ESC window is **~4.886 s**
  from banner to `Jump to image start`, and it is open at power-on, so ESC has
  to be streaming before that. 讀 `LDR-20`: a **bad image reaches the rescue
  prompt without waiting for ESC and without printing anything** — so corrupting
  the image is itself a path to the prompt.

**What rlxfw does.** Nothing, and it must not. `plan/` § 8.2 records this row as
*a feature, not a bug — take it away and you brick it*, and this project's
position is that **physical or LAN access to the loader equals complete control,
accepted by design**.

**What is 未定, and it decides how far this position reaches.** 🔴 Whether a
network peer can reach that TFTP server with **no console access at all** has
never been settled. Two readings disagree and have never been reconciled: 讀
`LDR-25` says the compiled-in address responds without `IPCONFIG`, and 量
`NET-95` says the loader does **not** answer ARP before `IPCONFIG`. If
`LDR-25` is right, `T6` is a remote position; if `NET-95` bounds it, `T6`
requires the console and collapses into `T5`. `docs/hardening-matrix.md` § 4
`LDR-25` 殘留 names the one bracket that decides it.

⚠️ And one thing rlxfw **does** do that narrows the burn path by accident
rather than by design: 量 `FW-166`, the stock loader refuses rlxfw's own
container, read two independent ways. That makes rlxfw's images unburnable by
the loader's automatic path — which is protection for rlxfw's development unit
and not protection for a deployed device.

## 8. `T7` — the vendor WLAN driver, as code inside rlxfw's kernel

🔴 **Near-zero containment, stated in the threat model because `plan/` `D16`
requires it to be.** This is a driver this project did not write and cannot
audit, linked into a monolithic kernel. The size figure used here is this
repository's own and not `plan/`'s line count: 量 `SPEC.md` `FW-51`,
`built-in.o` **820,910 bytes**.

**What it reaches, each with a reading.**

* **The whole kernel address space.** 讀 `# CONFIG_MODULES is not set`
  (`SPEC.md` `CLK-21`, `config/rlxfw-kernel.delta`): there is no module
  boundary, no LSM behind it, and nothing to unload.
* **The loader's RX DMA footprint.** 讀 `SPEC.md` `NET-153`: at `SWCORE=n` the
  driver's `.bss` array `obj_buf` is **432,432 bytes** and covers the loader's
  whole receive ring, descriptors and buffers.
* **The watchdog.** 量 `SPEC.md` `FW-51`: four of its sites touch `WDTCNR`, and
  `CONFIG_RTL_WTDOG=n` does **not** remove them, because those sites are gated
  on the board symbol `CONFIG_RTL_8196E` and not on the watchdog symbol. 🔴 The
  first version of that reading came from the wrong directory and was corrected
  by measuring the artefact.

**What this project got right about it, and it is a correction to `plan/`.** The
driver that **builds** is `rtl8192cd/`, **not** `rtl8192e/`: 量 `FW-51`,
`built-in.o` **820,910 bytes**; 讀 `FW-103`, `rtl8192e/` carries the same two
print lines and that directory never enters the image. And at `SWCORE=n` — the
mainline since `R6b-8` 8g — it is the **same source and not the same object**
(讀, `docs/KNOWN-ISSUES.md`), and 🔄 **量 2026-10-04 both halves are counted:
`built-in.o` loses 11 symbol-table entries and 6 references, not the forty this
paragraph said, and `struct sk_buff` is 192 bytes against 200**
(`notes/switch-driver.md` § 19.4). Five of the ten names the
seam defines are its references. `R9` therefore builds `quiet-swcore`, where it
and the NIC driver are the vendor's objects as built at `SWCORE=y` — and even
there, the WLAN driver is listed as a **difference** between the two columns
regardless, because same source is not same object.

**What rlxfw does about it.** Nothing that bounds it. The radio is down unless a
verb is typed (§ 5), which reduces the probability that the code runs and
changes nothing about what it can do when it does.

## 9. `T8` — a malicious or corrupt update image

**What rlxfw does.** 量 `SPEC.md` `FW-170`, four rounds on the silicon in one
seating with no flash-write verb issued: a correct container verified and booted
(`HDR ok` / `SIG ok` / `DIGEST ok` / `VER cur=1 ctr=0 ok` / `BOOT`); one flipped
payload bit refused at the digest with no `BOOT`; a version below the
anti-rollback counter refused (`VER cur=1 ctr=5 bad` / `REFUSE rollback`); and
the same container at counter 0 booting as the control. 讀 `notes/rlxboot.md`
§ 3, the verification order: the header becomes trusted only after Ed25519 over
its bytes 0..95, so nothing the header says is acted on before it is verified.
讀 § 5: Ed25519 and SHA-512 are **imported** (TweetNaCl, declared in
`SOURCES.json`) and are labelled imports, never called rlxfw's code.

**What rlxfw does not do, and `PROGRESS.md`'s `R8a` row says it first.** It
establishes nothing about writing flash, nothing about surviving a power cut,
and nothing about key management; and it is not secure boot on a part with no
evidence of a key-hash fuse. 量: **nothing has advanced the anti-rollback
counter**, so what was read is the comparison and not the bitmap's monotonicity.
⚠️ `notes/rlxboot.md` § 6 keeps its cache handling at **推** and says in its own
words that *it booted* is not evidence; `SPEC.md` `FW-172` carries that and the
second reading it wants was never taken.

## 10. `T9` — a peer that already holds a uid on the box

**What it reaches.** The broker socket at mode 0666, and whatever its uid's row
in the op table allows. 讀 `notes/broker.md` § 2: any uid other than 0, 100 and
101 is answered `PERM` on **every** op; uid 101 cannot obtain a session at all
and its access is the table's `allow_101` plus a two-key list.

**What rlxfw does.** The authorisation is one table walked by one function, and
`test_authz.c` walks the same table. 🟢 The derivation of that matrix had a real
bug — `need_session` was being read for uid 101, which cannot have a session —
and it was caught by named negative cases rather than by review. There is
deliberately **no option** for the entropy file, the random source or the ping
binary, because each would be a runtime bypass of a fail-closed rule.

**What rlxfw does not do.** The mode is 0666 and `SO_PEERCRED` is the whole
authorisation, so any local process can connect and be refused rather than being
unable to connect. Nothing isolates one uid's memory from another beyond what
the 2.6.30 kernel does by default, and `docs/hardening-matrix.md` § 2 shows what
that excludes: no seccomp (推), no `no_new_privs` (推), no LSM, and NX **未定**.

## 11. The seven that cannot be fixed, and where each now stands

`plan/` § 8.2 names seven. 🔴 Four of them are **not** in the state `plan/`
records, because the evidence it cites does not exist in this repository.

| `plan/` § 8.2 row | `plan/`'s evidence | what this repository actually holds |
|---|---|---|
| **NX** | *`R1a`'s NX test* | 🔴 **未定.** No such test ran and no reading of page-level execute permission exists on this die. `SPEC.md` `CPU-49` 殘留 records NX as one of seven items deliberately excluded from `R1a`'s population, ⊘ 2026-09-30 as voluntarily out of scope. `docs/hardening-matrix.md` `SPEC.md` `CPU-49` 殘留 |
| **ASLR** | *`R3` reads the source* | 🔴 **未定.** 量 2026-10-04: zero hits for `aslr`, `randomize_va` or `arch_pick_mmap` across `notes/`, `docs/` and `SPEC.md`. One desk grep settles it. `TC-26` 殘留 ① |
| **seccomp / `no_new_privs`** | *read the 2.6.30 source* | 🔴 **推, not 讀.** The kernel is 2.6.30.9 (讀) and the features are 3.x and 3.5+, but no grep of this tree's `Kconfig` was taken. `TC-26` 殘留 ② |
| **True secure boot** | *the manual's contents has no OTP chapter* | ⚠️ **partly.** The loader half **is** read: 讀 `LDR-18`, an unkeyed 16-bit sum, and the loader region is permanently unwritable by rule. The fuse half is **⊘ out of scope**, owned by `PROGRESS.md`'s `R8a` row — *no evidence of a key-hash fuse* — and not reopened here |
| **Physical attacker** | *threat model's out-of-scope* | ✅ **in scope here, § 6, and stated unmitigated** with four readings of what it reaches |
| **Vendor WiFi driver** | *written plainly in the threat model* | ✅ **§ 8, and with three readings `plan/` did not have** — the directory that builds, the `.bss` that covers the loader's DMA, and the watchdog sites the config flag does not remove |
| **Loader's unauthenticated TFTP rescue** | *physical/LAN access = complete control, accepted* | ✅ **§ 7, accepted and unmitigated** — and with a 未定 `plan/` did not name: whether it is reachable with no console at all (`LDR-25` 殘留) |

## 12. What this threat model does not establish

* **Not that rlxfw is secure, and not that it is more secure than the vendor
  firmware.** Two positions are unmitigated, one has near-zero containment, one
  is bounded only by a default, and one has 未定 reach. **Seven** of
  `docs/hardening-matrix.md`'s vendor cells are 未定 and two are ⊘ Structural, so
  most of its rows are not differential claims at all.
* **Not that the mitigations hold under attack.** Every reading cited above was
  taken on a cooperative system — a boot's `ps`, a `/proc/<pid>/status`, a
  symbol table, a console line, a host battery. The one adversarial step in the
  set is the privilege drop being verified by reversing it, and one step is not
  an adversary.
* **Not that the position list is complete.** It was derived from what this
  project has measured and from `plan/` § 8.2, not from a systematic
  enumeration. A position nobody named has no row, and the absence of a row is
  not evidence.
* **Not anything about the vendor's reachable attack surface.** The vendor's
  firmware **has no shell** (`docs/GATE-RESULTS.md`, `P2`'s ⊘ *Structural, not
  deferred*), and every evidenced path into its userspace opens with a flash
  write — so for most of the vendor's side this gate can read static shape and
  nothing else. `plan/` § 8.1's `CVE-2014-8361` entry is the standing precedent:
  the code shape was present and the effect was not.
* **Not that `plan/` § 8.3's entropy comparison can ever be run.** It needs 100
  reads of `/dev/urandom` across 20 boots of the **vendor** firmware, which
  needs a shell. ⊘ Structural, not deferred.
* **Not a severity ranking.** No position above carries a likelihood, an
  impact or a CVSS-shaped number, because nothing here measured one. `T5` and
  `T6` are listed first among the unmitigated because they are the ones a reader
  will ask about, not because they were scored.
* **Not that rlxfw's own code is free of the classes it designed against.** The
  design removes the *mechanism* — no `system`, no substring authorisation, one
  template layer, a bounded TLV reader — and the readings above confirm the
  mechanism is absent from the shipping bytes. They say nothing about defects of
  other classes, and `docs/KNOWN-ISSUES.md` already holds two that the first
  boot of rlxfw's userspace found.
* **Not a report to anyone.** No vendor defect is reported here, no reproduction
  appears, and nothing has been sent: `upstream/docs/disclosure.md` is ≥ 90 days
  downstream of a send that has not happened.
