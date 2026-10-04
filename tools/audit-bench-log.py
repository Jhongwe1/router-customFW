#!/usr/bin/env python3
"""Audit the bench logs for anything that identifies this physical unit, before
they are committed and pushed.

CLAUDE.md forbids committing a flash dump because it identifies one device --
its MAC and its radio calibration live in H601.  These logs are not a dump, but
"not a dump" is not the same as "carries nothing", so this checks rather than
assumes.  Every pattern is run against a synthetic positive control first: a
scan that cannot fire proves nothing.
"""
import re, sys, io, os

#: 🔴 2026-08-30 (fourteenth session): `MAC, bare 12 hex` is OUI-restricted and
#: **neither of its two OUIs is this unit's**, so the one pattern written to
#: catch this unit's address in bare form structurally cannot.  量: the OUI at
#: `H601+0x07` in `$FWRE_WORK/dumps/flash-n150rt-console-2.bin` matches neither
#: alternative.  `fc1928` went in believing it was TOTOLINK's; it is Actions
#: Microelectronics (IEEE MA-L, 2020-08-25) and it is the OUI of the
#: WORKSTATION's USB GbE adapter, not of the device (`SPEC.md` §18).
#:
#: **It is not fixed by adding this unit's OUI here**, because writing that OUI
#: into a committed file is a disclosure of half the address, and this file is
#: committed.  The gap is closed instead by `tools/leakscan.py --attribute`,
#: which answers "is this value this unit's?" by looking the bytes up in the
#: reference dump rather than by recognising a prefix -- a measurement where
#: this is a guess.  The two OUIs stay because they still earn their keep:
#: `00e04c` is Realtek's and catches the driver defaults, `fc1928` catches the
#: workstation adapter in bare form.
PATTERNS = [
    ("MAC, colon form",     re.compile(r'\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b')),
    ("MAC, dash form",      re.compile(r'\b(?:[0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}\b')),
    ("MAC, bare 12 hex",    re.compile(r'\b(?:00[eE]0[4-6][cC]|[fF][cC]1928)[0-9A-Fa-f]{6}\b')),
    # 🆕 2026-08-30.  `enx<12 hex>` is systemd's ID_NET_NAME_MAC scheme: the
    # interface name IS the adapter's MAC, and none of the eight patterns above
    # could see it -- `\b` does not fall between `enx` and the first hex digit,
    # so the bare-12-hex pattern misses it by construction.  量: nine tracked
    # files carry such a name and three files under `upstream/` do; **zero
    # `bench/**/*.log` do**, so adding it turns the CI gate red on nothing.
    ("MAC, enx interface",  re.compile(r'\benx[0-9a-fA-F]{12}\b')),
    ("H601 / calibration",  re.compile(r'H601|calib|rf_?cal|txpower|eeprom', re.I)),
    ("serial-ish",          re.compile(r'\bS/?N[:= ]|serial\s*(no|number|:)', re.I)),
    ("private IPv4",        re.compile(r'\b(?:10|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b')),
    ("SSID / passphrase",   re.compile(r'ssid|passphrase|wpa[_-]?psk|password', re.I)),
    ("home path / user",    re.compile(r'/home/[a-z]+|C:\\\\Users\\\\|Key20', re.I)),
]

#: 🔴 2026-08-30 (fourteenth session): the dash-form literal used to be a REAL
#: address -- the workstation's USB GbE adapter, the same value `leakscan.py`
#: classifies `HOST` -- sitting in a block whose whole premise is that it is
#: synthetic.  It is replaced by an obviously-synthetic value on the same OUI as
#: the colon-form line, so the pattern still fires and nothing real is here.
#: *(Original: `"MAC FC-19-28-61-84-C9 here\n"`.)*  A control literal that is a
#: real address is a leak in the file that exists to find leaks.
CONTROL = (
    "banner\n"
    "hwaddr 00:E0:4C:11:22:33 here\n"
    "MAC 00-E0-4C-11-22-33 here\n"
    "enx00e04c112233\n"
    "00e04c112233\n"
    "H601 region calib blob\n"
    "S/N: ABC123\n"
    "IPCONFIG 192.168.1.6\n"
    "ssid=MyNetwork password=hunter2\n"
    "/home/key/fwre-work\n"
)

#: 🆕 2026-08-30.  An allowlist, in the shape `spec-check.py` already uses: one
#: entry per suppressed literal, each carrying the reason it is not identifying.
#: It suppresses the EXACT match only -- a different private address, or a MAC
#: that is not on this list, still fires -- and control A2 below proves that.
#:
#: Why it arrived: seating 5 was the first to put a booted Linux and a host-side
#: ping on the record, so the bench network appears in the transcripts for the
#: first time.  The logs are byte-exact by rule (`.gitattributes` has
#: `bench/** -text`, and `bench/README.md` says so), so redacting them is not an
#: option and this is the alternative.
#: Each entry is (scope, needle, reason).
#:   scope "match" -- the matched text itself is benign wherever it appears.
#:   scope "line"  -- the match is benign ONLY on a line containing `needle`.
#:   scope "exact" -- the match is benign ONLY on a line that IS `needle`, whole,
#:                    once stripped of surrounding whitespace (a CRLF's CR too).
#: 🔴 "match" and "line" are not interchangeable. `Calib` and `Serial:` are matched
#: by patterns aimed at radio calibration and serial numbers; suppressing those
#: two strings outright would hide a real calibration blob. They are allowlisted
#: by the LINE that makes them benign, so `Calibration data: <hex>` still fires.
#: 🔴 R1y (SPEC.md FW-138): "line" is a substring test on the whole line, and it
#: exempts EVERY pattern's match on that line -- whatever else the line carries,
#: and a line where the needle is only the start of a longer value.  量
#: 2026-09-25: the two entries whose reasons said "Scoped to this exact line" and
#: "... exact path" let 12 of 12 widening probes through (a MAC, a calibration
#: word, an IP, a second home path, an SSID and a password on the needle's line;
#: the needle as a prefix or mid-line; the path plus `.bak`).  They are "exact"
#: now, and control A3 below holds every "exact" entry to that.  量 2026-09-30:
#: the control MAC on a line holding the needle was silent under all nine "line"
#: entries.  The three whose silenced lines are ONE text in the CI corpus are
#: "exact" too; each of the other six says in its reason what it does not catch.
ALLOW = [
    ("match", "10.1.1",
     "the bench-side network the operator chose: 10.1.1.1 is what IPCONFIG "
     "gives the loader, 10.1.1.2 the workstation, 10.1.1.10 the board under "
     "Linux. None is this unit's configuration -- the loader's own compiled-in "
     "TFTP address is 192.168.1.6, which is allowlisted in spec-check.py for "
     "the same reason and is deliberately NOT allowlisted here"),
    ("match", "fc:19:28:61:84:c9",
     "\U0001f195 2026-09-21 (seatings 33 and 34). THE SAME ADAPTER AS THE ENTRY "
     "BELOW, in the spelling `tcpdump` prints. The adjudication is not new -- it "
     "was made on 2026-09-20 and is stated in full in the next entry -- only the "
     "spelling is: seating 30 met this adapter through iputils' banner, which "
     "writes the INTERFACE NAME `enxfc19286184c9`, and seatings 33/34 met it "
     "through `tcpdump -e`, which writes the MAC in colon form. \U0001f534 Quoting a "
     "capture under a different spelling to satisfy a checker would misreport "
     "what the instrument printed -- the same reason `h601` and "
     "`02:52:4c:58:46:57` each carry two entries. \u26a0\ufe0f It suppresses the "
     "EXACT literal only, so any other MAC -- including anything read off the "
     "board -- still fires, which control A2 proves. The two captures are "
     "`bench/2026-09-21c/X4-TCPDUMP.log` and `bench/2026-09-21d/X10-TCPDUMP.log`, "
     "and they are `SPEC.md` `NET-78`'s wire-side evidence: three ARP requests "
     "leave the workstation and no frame comes back. **The host's own address is "
     "not what that finding rests on**; the board's is, and the board's is the "
     "driver constant allowlisted in `spec-check.py`"),
    ("match", "56:0a:01:01:01:e8",
     "🆕 2026-09-21 (seating 36). The LOADER's address, and it is "
     "SYNTHESISED rather than stored: 量 bytes 2-5 are `0a:01:01:01` = "
     "10.1.1.1, which is what this desk types into `IPCONFIG` for one seating "
     "-- the same distinction the 10.1.1 entry draws, and for the same reason. "
     "It reaches bench/ because this seating was the first to probe the loader "
     "with ARP as a carded cell, so seven host-side .log files carry it out of "
     "`ip neigh`. 🔴 Allowlisted rather than redacted because a .log is "
     "a measurement artefact and editing one is what --force exists to forbid; "
     "`spec-check.py`'s REDACTION_ALLOWLIST carries the same literal with the "
     "same reason. ⚠️ THE RESIDUAL, stated rather than left out: bytes "
     "1 and 6 (0x56 and 0xe8) are NOT accounted for by that derivation. They "
     "have read the same on every seating that recorded them, which is equally "
     "consistent with a constant and with something unit-specific, and no "
     "seating has set a different IPCONFIG address to tell the two apart. "
     "未定. ⚠️ It suppresses the EXACT literal only, so any "
     "other MAC -- including anything read off the board -- still fires, which "
     "control A2 proves"),
    ("match", "ff:ff:ff:ff:ff:ff",
     "\U0001f195 2026-09-21. The Ethernet BROADCAST address, which the MAC pattern "
     "matches by shape and which identifies nothing by construction -- no NIC "
     "has it as its own address, and every ARP request in every capture carries "
     "it as the destination. \u26a0\ufe0f The all-ZERO MAC already has an entry "
     "below on the same ground (*an all-zero MAC identifies nothing by "
     "construction*); this is its counterpart at the other end. It suppresses "
     "the exact literal only"),
    ("match", "enxfc19286184c9",
     "🆕 2026-09-20 (seating 30). The WORKSTATION's USB Gigabit adapter, on "
     "this desk's side of the cable -- the same distinction the 10.1.1 entry "
     "above draws, and for the same reason: none of it is this unit's. It "
     "reaches bench/ because seating 30 was the first to run host-side "
     "generators as carded cells, so eighteen .log files open with "
     "`$ ping -I <it> ...` and carry iputils' own banner. 🔴 It is "
     "allowlisted rather than redacted because a .log is a measurement "
     "artefact and editing one is exactly what --force exists to be "
     "forbidden. The forward fix is on the CARD and not here: `ping -I "
     "10.1.1.2` binds by source address, needs no interface name, and that "
     "address is already covered above. ⚠️ This suppresses the EXACT literal "
     "only, so a different enx interface -- or anything read off the board -- "
     "still fires, which control A2 proves"),
    ("match", "00:12:34:56:78:9",
     "the six netdev MACs are SDK placeholders compiled into the vmlinux this "
     "seating built -- 量 2026-08-30, found as literal bytes at file offsets "
     "0x2b5d64 and 0x2b5e14. This boot mounted my own initramfs, so no vendor "
     "init script ever read H601"),
    ("match", "00:E0:4C:81:86:86",
     "wlan0's MAC, and it looks exactly like a real radio address, which is why "
     "it was measured rather than assumed: 量 compiled into the same vmlinux at "
     "offset 0x288cc0. A Realtek OUI on a driver default, not from flash"),
    ("match", "00:E0:4C:81:96:96",
     "pwlan0's, same measurement, offset 0x288e04"),
    ("match", "00:00:00:00:00:00",
     "the wlan0-wds interfaces. An all-zero MAC identifies nothing by "
     "construction, and it is the driver's unset value"),
    ("exact", "[    0.060000] Calibrating delay loop... 398.95 BogoMIPS (lpj=1994752)",
     "Linux's CPU-speed calibration (BogoMIPS), which the `calib` pattern "
     "matches and which has nothing to do with radio calibration. Scoped to "
     "this line so a real calibration blob still fires. 🔄 R1y: \"exact\" on "
     "the one text the entry silenced in the CI corpus (量 2026-09-30, 25 "
     "lines, every one this printk time and value); as \"line\" on "
     "`Calibrating delay loop` it also silenced a MAC before or after those "
     "words (probe, rc 0). A boot that prints another time or value fires, "
     "as a line to review"),
    ("line", "Serial: 8250/16550 driver",
     "the 8250 UART driver's registration banner, matched by the pattern aimed "
     "at serial NUMBERS. What that pattern is for still fires on any other "
     "line; on a line holding the banner nothing does -- a MAC before or "
     "after it is silent (probe, 2026-09-30, rc 0). Not \"exact\": the "
     "banner carries a printk time, and 量 2026-09-30 the CI corpus holds "
     "two, 0.86 and 0.98 s, on its 25 lines"),
    ("line", "h601_skipped",
     "rtl819x-spi's /proc output prints the NAME of the region it refused to "
     "hash, followed by a byte COUNT -- `h601_skipped 8192`. The count is the "
     "whole point: it is how the driver reports that H601 stayed out of the "
     "digest. 量 2026-09-08 (seating 16), 39 captures, two hits each. H601 "
     "CONTENT on any other line still fires -- which is the same distinction "
     "spec-check.py's REDACTION_ALLOWLIST draws for the same two field names "
     "-- but not on a line holding the name: whatever shares that line is "
     "exempt with it, a MAC before or after the name included (probe, "
     "2026-09-30, rc 0), and flashwin scan is the byte check. Not \"exact\": "
     "量 2026-09-30 it silences three texts in the CI corpus, `h601_skipped 0`, "
     "`h601_skipped 8192` and `map_h601_skipped 8192` (107 lines)"),
    ("line", "h601_hashed",
     "the sibling field, `h601_hashed 0`. Its value being zero is the "
     "assertion D1 rests on, so it may not be renamed to please a scanner. "
     "It costs what h601_skipped's entry costs: whatever shares a line with "
     "the name is exempt with it, a MAC included (probe, 2026-09-30, rc 0). "
     "Not \"exact\": 量 2026-09-30 it silences four texts in the CI corpus "
     "(120 lines) -- `h601_hashed 0`, `map_h601_hashed 0` and two mfgtest "
     "MT-FLASH-3 result lines that carry `h601_hashed=0` beside other fields"),
    ("exact", "RLXFW-S-MH601=00000000",
     "rtl819x-spi 1.1's boot-time MARK for the same quantity, and it is a "
     "THIRD string carrying the region's name that the two entries above do "
     "not cover: they are scoped to the /proc field lines, and this is a "
     "rlxfw_markx() tag. 量 2026-09-08 (seating 17), C1-M0/C1-M1, one hit "
     "each -- the first captures in this repository to contain it, because "
     "1.1's map had never run on silicon before. The line is "
     "`RLXFW-S-MH601=00000000` and that value IS map_h601_hashed: the mark "
     "the scanner objects to is the mark reporting that H601 stayed out of "
     "the digest. Scoped to that exact line, so a line carrying H601 CONTENT "
     "still fires, whether or not the tag is on it. 🔄 R1y: it was \"line\" on "
     "`RLXFW-S-MH601`, which also silenced a MAC beside the tag (probe, "
     "2026-09-30, rc 0); 量 the same day all 56 of its lines in the CI corpus "
     "are this one text. ⚠️ Whether the value is zero is NOT this tool's "
     "question -- flashmap's F6 control refuses every reading when "
     "map_h601_hashed != 0, and flashwin scan checks the bytes; this tool "
     "checks the topic keyword and cannot tell a field name from a "
     "calibration blob, which is why it is allowlisted by NAME and not by "
     "pattern. A nonzero value is no longer this line, so it fires here too, "
     "as a line to review"),
    ("line", "S-H601=",
     "rtl819x-spi 1.2's `h601` VERB mark, a fourth string carrying the "
     "region's name and a sibling of RLXFW-S-MH601 above -- which does not "
     "cover it, the two tags differing by one letter. 讀 rtl819x-spi.c:1919, "
     "`rlxfw_markx(\"S-H601\", (unsigned)rtl819x_spi_h601_rc)`: the value is "
     "the verb's RETURN CODE and never a byte of the window; the driver emits "
     "booleans, a version and a structure size for that region and nothing "
     "else, which docs/mfgtest.md 4 rules on. 量 2026-09-17 (seating 25), "
     "nine captures, one hit each -- the first in this repository, because "
     "1.2's h601 verb had never run on silicon before.\n"
     "🔴 THE NEEDLE IS `S-H601=` AND NOT `RLXFW-S-H601`, AND THAT IS "
     "MEASURED, NOT TIDINESS. SPEC.md FW-89: rlxfw_mark() interleaves "
     "character by character with busybox ash's still-flushing output, "
     "deterministically, at exactly this point in `mfgtest auto` -- so the "
     "line in all nine captures reads `XFW-S-H601=00000000`, with the `RL` "
     "consumed by the MT-PORT line it collided with. An entry scoped to the "
     "full tag would not have matched a single one of them.\n"
     "\u26a0\ufe0f What that costs is MEASURED, not reasoned. Because the mark "
     "shares a line with whatever it interleaved into, this entry exempts "
     "that other text too -- 量 2026-09-17, three probes with the same "
     "calibration blob: on a DIFFERENT line from the needle it fires (rc 1); "
     "on the SAME line it does not (rc 0); with no needle anywhere it fires "
     "(rc 1). The first and third are what make the second a reading rather "
     "than an assertion. It is a real widening and it is one line wide -- "
     "and flashwin scan, which reads the BYTES against the reference dump "
     "rather than a topic keyword, is the check that cannot be widened this "
     "way at all. 量 2026-09-17: CLEAN over 4,737 committed files"),
    ("line", "h601_ran ",
     "rtl819x-spi 1.2's /proc field for the h601 VERB, `h601_ran %d` -- a "
     "BOOLEAN. 讀 rtl819x-spi.c rtl819x_spi_read_proc: sprintf(page + len, "
     "\"h601_ran %d\\n\", rtl819x_spi_h601_ran). A fifth string carrying the "
     "region's name: h601_skipped/h601_hashed above are the map's /proc "
     "fields, RLXFW-S-MH601 and S-H601= are marks, and this is the verb's "
     "/proc line, which none of them covers. 量 2026-09-25 (block 46), "
     "bench/2026-09-25c/R1-NW0 and R1-NW1 line 58 -- the first captures in "
     "bench/ of the whole 1.2 /proc file (no committed bench .log carried "
     "`h601_ran` before them). H601 CONTENT on any other line still fires; "
     "the needle is the format string's own text up to the value. The cost "
     "is the one measured for S-H601=: whatever shares this line is exempt "
     "with it, one line wide -- a MAC before or after the field is silent "
     "(probe, 2026-09-30, rc 0) -- and flashwin scan is the byte check. Not "
     "\"exact\": the value is 0 or 1 (量 2026-09-30, 22 lines in the CI "
     "corpus)"),
    ("line", "h601_rc ",
     "the sibling field, `h601_rc %d` -- the verb's RETURN CODE, the same "
     "quantity S-H601= marks (rtl819x_spi_h601_rc, initialised -EAGAIN, so "
     "`-11` in a boot that never ran the verb). 讀 rtl819x-spi.c, the "
     "sprintf after h601_ran's. 量 2026-09-25, the same two captures, line "
     "59. It costs what h601_ran's entry costs: whatever shares the line is "
     "exempt with it, a MAC included (probe, 2026-09-30, rc 0). Not "
     "\"exact\": 量 2026-09-30 the CI corpus holds `h601_rc -11` and "
     "`h601_rc 0` (22 lines)"),
    ("match", "02:52:4C:58:46:57",
     "rtl819x-nic's OWN address, a constant compiled into "
     "config/rlxfw-src/.../rtl819x-nic.c: locally administered (0x02) plus "
     "ASCII RLXFW -- \u91cf, `printf '\\x52\\x4c\\x58\\x46\\x57' | od -c` is `R L X F W`. "
     "It exists PRECISELY SO THAT this unit's real address, which lives in "
     "H601 and may not be published, never has to be read, so redacting it "
     "would hide a driver constant while protecting nothing. What this entry "
     "must not be allowed to excuse is a Realtek OUI, and `02:` cannot be "
     "one, because locally-administered addresses are not assigned to any "
     "vendor.\n"
     "\U0001f534 IT WAS ALREADY ON `spec-check.py`'s REDACTION_ALLOWLIST, WITH THIS "
     "REASON, AND WAS NOT ON THIS LIST -- and nothing in this repository "
     "compares the two. The divergence one entry above is a DECISION stated "
     "in its own text (192.168.1.6 is allowlisted there and deliberately not "
     "here); this one was an oversight, and the two are indistinguishable by "
     "reading either file. \u91cf 2026-09-20: it first reached bench/ at seating "
     "28, in C45-ifcfg and C47-ifup -- the first captures here to `ifconfig` "
     "a net_device of this project's own, so the literal could not have "
     "fired before. docs/KNOWN-ISSUES.md carries what would settle the "
     "class: a cross-check over the two allowlists that requires every "
     "difference to be declared rather than merely true"),
    ("match", "02:52:4c:58:46:57",
     "\U0001f195 2026-09-21 (seating 35). THE SAME ADDRESS AS THE ENTRY ABOVE, in the spelling `tcpdump` prints. The adjudication is that entry's and is not repeated: it is a driver constant, locally administered, and it exists precisely so this unit's real address in H601 never has to be read.\n"
     "\U0001f534 WHAT IS NEW IS THAT THIS FILE'S OWN TEXT SAID THIS ENTRY ALREADY EXISTED. The `fc:19:28:61:84:c9` entry, written on 2026-09-21 for seatings 33/34, states that `h601` and `02:52:4c:58:46:57` EACH CARRY TWO ENTRIES; \u91cf, on the commit that shipped it, this address carried ONE here and two in spec-check.py. The case pair was made in the other file and the sentence describing it was written in this one. It fired at seating 35, on the first `tcpdump` here to capture an ARP REPLY from the board -- X7-TCPDUMP and X13-TCPDUMP, 4 hits across 2 files -- because every earlier reading of this address came from the console, which prints it upper-case.\n"
     "\u26a0\ufe0f This is the THIRD instance of the divergence the entry above already names as a class, and the cross-check that would settle it -- every difference between the two allowlists declared rather than merely true -- still does not exist. docs/KNOWN-ISSUES.md owns it"),
    ("match", "10.255.255",
     "the BROADCAST address of the bench network the entry at the top of "
     "this list already allows. \u91cf 2026-09-20, the line busybox prints: "
     "`inet addr:10.1.1.3  Bcast:10.255.255.255  Mask:255.0.0.0` -- a /8 "
     "mask over 10.1.1.x gives 10.255.255.255, so this is the SAME fact in "
     "a second spelling, and the `10.1.1` entry cannot cover it because the "
     "string does not contain `10.1.1`. Same shape as the lower-case MAC "
     "entry in spec-check.py: quoting a measurement under a different "
     "spelling to satisfy a checker would misreport what the instrument "
     "printed, and these logs are byte-exact by rule.\n"
     "\u26a0\ufe0f The scope limit, stated rather than left to be found: the needle "
     "is `10.255.255` because that is the whole of what the pattern matches, "
     "so this suppresses any 10.255.255.x. Nothing on this bench uses such "
     "an address -- \u91cf 2026-09-20, every occurrence in the corpus is the "
     "Bcast field of an ifconfig line -- but a genuine host there would be "
     "suppressed, and that is the cost"),
    ("exact", "ok    MT-RFCAL     hw_sum_ok=1 over 1166 body bytes",
     "the RF-calibration CHECK's id from docs/mfgtest.md 2's table, matched "
     "by the pattern aimed at radio calibration -- the same shape as "
     "`Calibrating delay loop` above, where a word means something else on "
     "the line it sits on. The line is "
     "`ok    MT-RFCAL     hw_sum_ok=1 over <n> body bytes`: a BOOLEAN and a "
     "length. Both are ruled on in docs/mfgtest.md 4 -- hw_len is "
     "sizeof(HW_SETTING_T)+1 and identical on every unit of this model, so it "
     "identifies the MODEL and not this device. Scoped to that exact line, "
     "n = 1166, so a real calibration blob still fires, and so does a "
     "failing check (`hw_sum_ok=0`) or another length. 🔄 R1y: it was "
     "\"line\" on `MT-RFCAL`, which also silenced a MAC on the check's line "
     "(probe, 2026-09-30, rc 0); 量 the same day all 13 of its lines in the "
     "CI corpus are this one text. Renaming the check to please a scanner "
     "would desynchronise it from the table that defines it, which is the "
     "objection h601_hashed's entry already makes"),
    ("exact", "supports-eeprom-access: no",
     "ethtool -i's capability line for the WORKSTATION's USB GbE adapter "
     "(bound to r8153_ecm), matched by the pattern aimed at calibration "
     "through its word `eeprom`. 量 2026-09-25, bench/2026-09-25b/D0-ETH, the "
     "first capture of `ethtool -i` in bench/: the line says the host adapter "
     "offers no EEPROM access, and names nothing of this unit. Scoped to this "
     "exact line, so any other `eeprom` still fires. 🔄 R1y: this entry was "
     "\"line\" until SPEC.md FW-138, and then it exempted anything else on a "
     "line holding the needle, and a longer value the needle only begins"),
    ("exact", "b3711d235d01788eba669b088eed1623af887d3ba105c7b9800bccfd460acc92"
              "  /home/key/fwre-work/rebuild/s105-analysis/s105-d2.py",
     "the D2 script's path as `sha256sum` prints it in Z9-D2A (cards B45 and "
     "B46, section 5), matched by the home-path pattern. 量 2026-09-25, "
     "bench/2026-09-25/Z9-D2A, the first bench log to print it. The same path "
     "is committed in both cards' `d2-script` cardnum row and $FWRE_WORK's in "
     "CLAUDE.md, so the line discloses nothing new. Scoped to this exact "
     "line, so any other home path still fires. 🔄 R1y: the needle is now the "
     "whole line, the script's digest included -- committed in the same log, "
     "and its first 16 digits in both cards' row -- because an \"exact\" entry "
     "equals the line; this path beside another digest, a `.bak`, or anything "
     "else fires. It was \"line\" on the path alone until SPEC.md FW-138"),
]


def allowed(txt, line=""):
    """The allowlist entry covering this match, or None."""
    for scope, needle, why in ALLOW:
        if scope == "match" and needle in txt:
            return (needle, why)
        if scope == "line" and needle in line:
            return (needle, why)
        if scope == "exact" and needle == line.strip():
            return (needle, why)
    return None

#: 🆕 2026-10-02 (s119): exemptions by FILE NAME, which ALLOW cannot express --
#: its three scopes are a value, a substring of a line and a whole line, each
#: wherever it appears.  These rows exist for 10.9.9.x, and 10.9.9.9 is the
#: address control A2 below and leakscan.py's L3 probe with: a "match" entry
#: would blind both, which is why this list is not in ALLOW and why `allowed()`,
#: the function A2 and L3 call, never reads it.  A row is (path from the
#: repository root, pattern label, matched text, the whole line once stripped,
#: reason).  It silences that pattern's that-text hits on that line of that one
#: file: the same line in any other file, and any other line of the named one,
#: still fires.  Control A4 holds every row to being needed -- its file still
#: holds the line, the line still produces the hit, and ALLOW does not already
#: cover it -- so a stale row fails the run instead of waiting for something to
#: land on its line.
_R78 = ("; the lease is SYNTHETIC: 10.9.9.9, 10.9.9.1 and 10.9.9.53 were typed "
        "into ifupd at the console for R78-iu1..4, no DHCP server issued them, "
        "and R78-fix put rlx0 back on 10.1.1.1 (notes/userspace-integration.md "
        "7.6, SPEC.md FW-181)")
#: 🆕 2026-10-04 (s121): `serial-ish` fires on the WORDS `serial number` in
#: `R9-6`/`R9-7`'s probe register, where cell C23's `expect` states why that
#: probe records no body.  Prose about a leak surface, not this unit's serial.
_C23 = (
    "cell C23's `expect` says WHY the probe records no body -- a UPnP "
    "description document carries a UDN uuid and often a serial number -- "
    "so the match is prose about the leak surface, not this unit's serial. "
    "The capture is a frozen record and is never edited (CLAUDE.md); the "
    "exemption is by name, and control A4 turns it red the day the line "
    "stops producing the hit")
FILE_EXEMPT = [
    ("bench/2026-09-30/R78-iu1.log", "private IPv4", "10.9.9",
     "ip=10.9.9.9 subnet=255.255.255.0 router=10.9.9.1 dns=10.9.9.53 "
     "interface=rlx0 /sbin/ifupd bound; echo rc=$?",
     "ash's echo of the typed command" + _R78),
    ("bench/2026-09-30/R78-iu1.log", "private IPv4", "10.9.9",
     "ifupd: bound ok reason=ok if=rlx0 ip=10.9.9.9/24 gw=10.9.9.1 dns=1",
     "ifupd reporting the lease it applied; dns=1 is a count "
     "(src/ifupd/main.c)" + _R78),
    ("bench/2026-09-30/R78-iu1.meta.json", "private IPv4", "10.9.9",
     '"sent": "ip=10.9.9.9 subnet=255.255.255.0 router=10.9.9.1 '
     'dns=10.9.9.53 interface=rlx0 /sbin/ifupd bound; echo rc=$?",',
     "console-capture's record of what it sent" + _R78),
    ("bench/2026-09-30/R78-iu2.log", "private IPv4", "10.9.9", "10.9.9.53",
     "`cat /run/wan.dns`: the dns= ifupd wrote in R78-iu1" + _R78),
    ("bench/2026-09-30/R78-iu2.log", "private IPv4", "10.9.9",
     "inet addr:10.9.9.9  Bcast:10.9.9.255  Mask:255.255.255.0",
     "`ifconfig rlx0` after R78-iu1; Bcast is not typed, it is the broadcast "
     "of the typed ip and subnet" + _R78),
    ("bench/2026-09-30/R78-iu4.log", "private IPv4", "10.9.9",
     "ip=10.9.9.9 subnet=255.255.255.0 interface= /sbin/ifupd bound; echo rc=$?",
     "ash's echo of the typed command" + _R78),
    ("bench/2026-09-30/R78-iu4.meta.json", "private IPv4", "10.9.9",
     '"sent": "ip=10.9.9.9 subnet=255.255.255.0 interface= /sbin/ifupd '
     'bound; echo rc=$?",',
     "console-capture's record of what it sent" + _R78),
    ("bench/2026-10-04/R-DIFF.meta.json", "serial-ish", "serial number",
     "\"expect\": \"vendor 200 or 404; rlxfw no-connect/refused. \\ud83d\\udd34"
     " body = none: a description document carries a UDN uuid and often a "
     "serial number. The row's SSDP half is UDP and outside this instrumen"
     "t.\",",
     _C23),
    ("bench/2026-10-04/V-DIFF.meta.json", "serial-ish", "serial number",
     "\"expect\": \"vendor 200 or 404; rlxfw no-connect/refused. \\ud83d\\udd34"
     " body = none: a description document carries a UDN uuid and often a "
     "serial number. The row's SSDP half is UDP and outside this instrumen"
     "t.\",",
     _C23),
    ("bench/2026-10-04/V-DIFF2.meta.json", "serial-ish", "serial number",
     "\"expect\": \"vendor 200 or 404; rlxfw no-connect/refused. \\ud83d\\udd34"
     " body = none: a description document carries a UDN uuid and often a "
     "serial number. The row's SSDP half is UDP and outside this instrumen"
     "t.\",",
     _C23),
]

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def exempt(path, label, txt, line):
    """The FILE_EXEMPT row covering this hit in this file, or None.  `path` is
    resolved and compared from the repository root, so neither the cwd nor an
    absolute spelling changes the answer, and a path outside it is never named."""
    try:
        rel = os.path.relpath(os.path.realpath(path), ROOT).replace(os.sep, "/")
    except ValueError:                  # another drive, so not under ROOT
        return None
    for name, lab, tok, whole, why in FILE_EXEMPT:
        if (rel, label, txt, line.strip()) == (name, lab, tok, whole):
            return (name, why)
    return None

def scan(name, text):
    """-> [(pattern label, 1-based line number, matched text, the whole line)].

    The line comes back so the allowlist can be scoped to it: `Calib` is benign
    on `Calibrating delay loop` and is not benign on a line that holds a
    calibration blob, and only the line separates those two.
    """
    lines = text.split('\n')
    hits = []
    for label, rx in PATTERNS:
        for m in rx.finditer(text):
            ln = text.count('\n', 0, m.start()) + 1
            line = lines[ln - 1] if ln <= len(lines) else ''
            hits.append((label, ln, m.group(0), line))
    return hits

def main(paths):
    print("=== POSITIVE CONTROL: every pattern must fire on a synthetic file ===")
    ctl = scan("control", CONTROL)
    fired = {h[0] for h in ctl}
    missing = [l for l, _ in PATTERNS if l not in fired]
    for label, ln, txt, _ln in ctl:
        print(f"  fired  {label:22s} line {ln}: {txt!r}")
    if missing:
        print(f"\n  FAIL: these patterns never fired, so a clean result means nothing: {missing}")
        return 2
    print(f"\n  ok  all {len(PATTERNS)} patterns fire on the control\n")

    # 🆕 A2: the allowlist must not be able to swallow the scan.  An allowlist
    # that suppressed a whole pattern would turn every later clean result into
    # a result that means nothing -- which is the same defect the positive
    # control above exists to prevent, one level up.
    print("=== POSITIVE CONTROL 2: the allowlist suppresses ONLY its own literals ===")
    a2 = scan("control", CONTROL)
    swallowed = [h for h in a2 if allowed(h[2], h[3])]
    if swallowed:
        print(f"  FAIL: the allowlist covers {len(swallowed)} control hit(s) "
              f"-- it is suppressing something the control needs: {swallowed}")
        return 2
    probe = "addr 10.9.9.9 and mac 00:12:34:56:AA:BB\n"
    ph = scan("control", probe)
    if not ph or any(allowed(h[2], h[3]) for h in ph):
        print("  FAIL: a NON-allowlisted private address and MAC did not fire, "
              "so the allowlist is matching too widely")
        return 2
    print(f"  ok  no control hit is allowlisted, and a non-listed "
          f"address/MAC still fires ({len(ph)} hit(s))")
    print(f"  ok  {len(ALLOW)} allowlist entr(ies), each with a stated reason\n")

    # 🆕 A3 (R1y, SPEC.md FW-138): an "exact" entry silences its own line -- by
    # that entry -- and nothing wider.  The same line with the control's MAC
    # after it, and before it, must fire: a substring test fails both, and a
    # prefix or a suffix test fails one.
    print("=== POSITIVE CONTROL 3: an \"exact\" entry covers its own line and nothing wider ===")
    exact = [needle for scope, needle, _ in ALLOW if scope == "exact"]
    mac = "00:E0:4C:11:22:33"
    for needle in exact:
        own = scan("control", needle + "\n")
        if not own or any((allowed(h[2], h[3]) or (None,))[0] != needle for h in own):
            print(f"  FAIL: {needle!r} as a whole line is not silenced by its own entry "
                  f"({len(own)} hit(s)), so the entry does not do what its reason says")
            return 2
        for wide in (needle + " " + mac, mac + " " + needle):
            if not any(h[2] == mac and not allowed(h[2], h[3])
                       for h in scan("control", wide + "\n")):
                print(f"  FAIL: a MAC on the line of {needle!r} is allowlisted -- the "
                      f"entry is wider than the line it names")
                return 2
    print(f"  ok  {len(exact)} \"exact\" entr(ies): each silences its own line, and a MAC "
          f"after or before it on that line still fires\n")

    # 🆕 A4 (s119): FILE_EXEMPT, both ways.  Each row must be NEEDED -- its file
    # still holds its line, the line still produces its hit, ALLOW does not
    # already cover that hit, and the row is what silences it -- or it is stale.
    # And no wider than its name: its hit under another path, label or text, its
    # line widened by a MAC either side, and A2's probe under its path all fire.
    print("=== POSITIVE CONTROL 4: a name-scoped exemption is needed, and covers its own line only ===")
    for name, lab, tok, whole, _why in FILE_EXEMPT:
        full = os.path.join(ROOT, name)
        try:
            body = io.open(full, encoding='utf-8', errors='replace', newline='').read()
        except OSError as e:
            print(f"  FAIL: {name} is named by an exemption and cannot be read "
                  f"({e.strerror}), so the row is stale")
            return 2
        own = [h for h in scan(name, body) if (h[0], h[2], h[3].strip()) == (lab, tok, whole)]
        if not own or any(allowed(h[2], h[3]) or not exempt(full, h[0], h[2], h[3])
                          for h in own):
            print(f"  FAIL: {name} no longer holds {whole!r} as a {lab} hit that only "
                  f"this row silences ({len(own)} hit(s)), so the row is stale")
            return 2
        wider = [(full + ".x", lab, tok, whole), (full, lab + " (other)", tok, whole),
                 (full, lab, tok + "0", whole), (full, lab, tok, whole + " " + mac),
                 (full, lab, tok, mac + " " + whole)]
        if any(exempt(*w) for w in wider + [(full, h[0], h[2], h[3]) for h in ph]):
            print(f"  FAIL: the row for {name} silences a hit it does not name -- it is "
                  f"wider than its file and its line")
            return 2
    print(f"  ok  {len(FILE_EXEMPT)} name-scoped exemption(s): each still silences a hit on its "
          f"own line of its own file, and nothing under another path, label, text or line\n")

    print("=== THE ACTUAL LOGS ===")
    total = 0
    suppressed = 0
    named = 0
    for p in paths:
        # newline='' -- WITHOUT it Python's universal newlines collapses every
        # CRLF into one LF, and the number printed below as `bytes` comes out
        # LOWER than the file by exactly the CRLF count.  Measured 2026-08-25 on
        # bench/2026-08-25/: 8855 -> 8797 (58 CRLF), 5356 -> 5307 (49),
        # 10790 -> 10719 (71), and 1671 -> 1671 where there are none.
        #
        # It is the same defect the `.gitattributes` line `bench/** -text` exists
        # to prevent -- these transcripts are byte-exact and the loader's own
        # format strings end \r\n -- applied to git and not to the tool that
        # lives beside them.  The scan itself was never affected: every pattern
        # here is ASCII and survives the decode.  The number was.
        text = io.open(p, encoding='utf-8', errors='replace', newline='').read()
        raw = scan(p, text)
        kept = [h for h in raw if not allowed(h[2], h[3])]
        hits = [h for h in kept if not exempt(p, h[0], h[2], h[3])]
        skipped = len(raw) - len(kept)
        byname = len(kept) - len(hits)
        total += len(hits)
        suppressed += skipped
        named += byname
        nbytes = os.path.getsize(p)
        flag = '' if len(text) == nbytes else f'  <- {len(text)} chars, non-ASCII present'
        note = f", {skipped} allowlisted" if skipped else ''
        note += f", {byname} exempted by name" if byname else ''
        print(f"  {os.path.basename(p):22s} {nbytes:6d} bytes  "
              f"{len(hits)} hit(s){note}{flag}")
        for label, ln, txt, _l in hits:
            print(f"      HIT {label} line {ln}: {txt!r}")
    print()
    if suppressed:
        print(f"  {suppressed} match(es) suppressed by the allowlist, "
              f"which is printed above with a reason per entry")
    if named:
        print(f"  {named} match(es) exempted by name, each row held to its own file "
              f"and line by control A4")
    if total == 0:
        print("  ok  nothing in any log matches a pattern that demonstrably "
              "fires and is not allowlisted")
        return 0
    print(f"  {total} hit(s) -- review each before committing")
    return 1

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
