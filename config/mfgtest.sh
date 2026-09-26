#!/bin/sh
# mfgtest -- the device-side manufacturing checks.  P1-1.
#
# The table this implements is docs/mfgtest.md 2.  One check, one line, and
# the line shape is the one tools/ci-census.py already parses: exactly two
# leading spaces, then ok / FAIL, then two more spaces.  That is not a
# coincidence -- it means a capture of this script's output can be counted by
# an instrument this repository already has, instead of by eye.
#
# ---------------------------------------------------------------------------
# WHAT THIS IMAGE CAN ACTUALLY RUN, AND WHY THAT SENTENCE IS MEASURED
# ---------------------------------------------------------------------------
#
# config/image-commands.tsv is the census of this unit's own busybox: 50
# applets and 40 ash builtins, extracted statically by tools/appletcensus.py.
# Every command below is on it.  In particular:
#
#   * awk is NOT in this image (FW-83).  Nothing here uses it.  printf IS --
#     a builtin, and the only formatting primitive there is.
#   * grep has no -E (FW-42).  量, and it cost a seating slot once already:
#     bench/2026-09-06c/X18-procls.log is an `ls /proc` whose output was piped
#     into `busybox grep -E` and destroyed.  Plain patterns only.
#   * There is no dd, no md5sum, no bc (FW-46).  Arithmetic is the shell's
#     own $(( )), which is POSIX and needs no applet.
#
# Field reading is done with `read`, a builtin, rather than with cut or sed,
# so the parser depends on nothing that could be absent.
#
# ---------------------------------------------------------------------------
# MFG_ROOT, AND IT IS THE MOST IMPORTANT LINE IN THIS FILE
# ---------------------------------------------------------------------------
#
# Every path below is $MFG_ROOT-prefixed.  On the device MFG_ROOT is empty and
# the paths are the real /proc.  Set it to a directory of fixture files and
# the whole comparator layer runs at a desk, with no board and no power.
#
# That is what makes P1-2's class-S injections possible at all: "feed the
# comparator a wrong id" is a fixture whose rdid_id line says something else,
# not a different flash chip.  docs/mfgtest.md 2 already declares those four
# rows class S -- simulated at the boundary, proving the check's logic and not
# its wiring -- and this is the boundary they are simulated at.
#
# When MFG_ROOT is set, act() does NOT write to /proc.  A fixture run must not
# be able to issue an SPI transaction, and the way to guarantee that is for
# the write to be unreachable rather than for the path to be wrong.

MFG_VERSION="mfgtest 1.1"

: "${MFG_ROOT:=}"

P_SPI="$MFG_ROOT/proc/rtl819x-spi"
P_MAP="$MFG_ROOT/proc/rtl819x-spi-map"
P_TIMER="$MFG_ROOT/proc/rtl819x-timer"
P_WDT="$MFG_ROOT/proc/rtl819x-wdt"
P_GPIO="$MFG_ROOT/proc/rtl819x-gpio"
P_KEYS="$MFG_ROOT/proc/rtl819x-keys"
P_PORT="$MFG_ROOT/proc/rtl819x-switch"
P_LED="$MFG_ROOT/sys/class/leds/n150rt:green:led2/brightness"
# evdev's node for rtl819x-keys, and OPENING IT IS THE ONLY REASON THE DRIVER
# EVER POLLS -- see mt_button.  Prefixed like every other path here so a
# fixture run cannot reach the real one; what actually keeps it unreachable
# at a desk is the `[ -z "$MFG_ROOT" ]` guard, the same one act() uses.
P_EVENT="$MFG_ROOT/dev/input/event0"

# The switch port the cable is in.  量 NET-13: this kernel's netdev numbering
# is the MIRROR of the vendor's (mine = 4 - vendor), so the jack the operator
# uses is switch port 3, which this kernel calls eth4.  Both proc files print
# SWITCH port indices (Port3, psrp3), so the token is Port3 and mt_port reads
# psrp3.  Writing Port4 here -- the netdev number -- would pass on the wrong hole.
MFG_PORT="Port3"

# The JEDEC id this part answers.  FLS-04, and REG-21's descriptor holds the
# same three bytes.  The kernel compares against its own compiled-in copy and
# prints rdid_match; this one is the script's, and it is the comparator
# MT-FLASH-1's class-S injection targets.
MFG_RDID="1C7016"

# MT-TICK's tolerance, and it is NOT zero although docs/mfgtest.md 2 writes
# the criterion as `Djiffies == Dirq_count`.
#
# 量 FW-75: the driver's /proc reads j inside the spin_lock_irqsave and
# irq_count 105 lines later, outside it.  The two values in one dump are
# therefore separated by real time, so each dump can be off by a tick and a
# difference of two dumps by two.  FW-64 adds that one `cat` is two read_proc
# invocations on this kernel.  A factory check written as exact equality would
# fail occasionally on a healthy board, which is the one way a test loses its
# authority permanently.  Two ticks at 100 Hz is 20 ms and cannot hide a
# broken tick: MT-TICK samples over seconds, so a real fault is off by the
# whole interval, not by two.
MFG_TICK_TOL=2

# How long MT-TICK samples for.  Long enough that the tolerance above is a
# rounding error against the expected delta.
#
# Overridable from the environment, and the reason is not convenience.
# MT-TICK is the only check here with a DELTA, so it is the only one a static
# fixture cannot produce: two reads of one unchanging file give dj = 0, which
# is a fail.  tools/mfginject.py rewrites the fixture DURING this sleep, so
# the check sees /proc advance the way it does on the die.  Shortening the
# window for that is not weakening the check -- the tolerance above is
# absolute, not proportional, so a shorter window is a STRICTER test.
: "${MFG_TICK_SECONDS:=5}"

# How long MT-BUTTON holds /dev/input/event0 open, which is also how long the
# operator has to press.
#
# 🔴 NOT 3 OR 4 SECONDS, AND THE REASON IS THIS PROJECT'S BENCH PROTOCOL
# RATHER THAN THE HARDWARE.  The operator cannot see this console -- CLAUDE.md
# 2 Environment: "at the bench you write the commands and read what I paste
# back" -- so the `starting now` line below is never read at the moment it is
# printed, and a 4 s window would ask for a press nobody can time.  The window
# is therefore long enough to be entered at leisure; the verdict does not
# depend on its length, only on a press landing somewhere inside it.
#
# Overridable for the same reason MFG_TICK_SECONDS is: a card states its own
# window, and a longer one is not a weaker test -- b0_n_press must still move
# by at least one, whatever the window.
: "${MFG_BUTTON_SECONDS:=20}"

ok=0
bad=0

# ---------------------------------------------------------------------------
# primitives
# ---------------------------------------------------------------------------

# chk <id> <verdict 0|1> <detail>
chk() {
	if [ "$2" = "1" ]; then
		printf '  ok    %-12s %s\n' "$1" "$3"
		ok=$((ok + 1))
	else
		printf '  FAIL  %-12s %s\n' "$1" "$3"
		bad=$((bad + 1))
	fi
}

# field <file> <name> -- echo the value of `name`.
#
# 🔴 TWO FORMATS, AND THE SECOND ONE IS NOT DEFENSIVE PADDING.  This project's
# drivers do not agree with each other:
#
#   rtl819x-spi, -wdt, -gpio, -keys   sprintf(page+len, "name %u\n", ...)
#   rtl819x-timer                     scnprintf(..., "name=%d\n", ...)
#
# 量 2026-09-17, by counting the format strings: the timer emits 100 fields in
# the `name=value` form and ZERO in the other.  The first version of this
# function split on whitespace only, so it could not read a single field of
# /proc/rtl819x-timer -- and MT-TICK reads four of them.  It was not caught by
# testing, because the fixture had been written in the same wrong format as
# the parser; the two agreed with each other and both disagreed with the
# driver.  What caught it was tools/mfginject.py's C1, which reads the
# DRIVER's own format strings.
#
# Returns 1 and echoes nothing when the name is absent, so a caller can tell
# "absent" from "present and empty" instead of scoring a missing field as 0.
field() {
	_f=$1
	_n=$2
	while read -r _k _v; do
		case "$_k" in
		"$_n")
			printf '%s\n' "$_v"
			return 0
			;;
		"$_n"=*)
			printf '%s\n' "${_k#*=}"
			return 0
			;;
		esac
	done < "$_f"
	return 1
}

# hexupper <string> -- fold a hex string to upper case, one character at a
# time, with no applet and no arithmetic.
#
# `tr` is not among this image's fifty applets (FW-46's family), and
# arithmetic is ruled out by the saturation measured in mt_id below.  The
# first-character idiom `${s%${s#?}}` is POSIX parameter expansion twice over:
# `${s#?}` drops one character and `${s%that}` removes it as a suffix.
# 量 on this unit's own busybox ash under qemu-mips-static, seven inputs
# including b1818b92, 03E7721C already upper, and DeadBeef mixed.
hexupper() {
	_u=""
	_r=$1
	while [ -n "$_r" ]; do
		_c=${_r%${_r#?}}
		_r=${_r#?}
		case $_c in
		a) _c=A ;; b) _c=B ;; c) _c=C ;;
		d) _c=D ;; e) _c=E ;; f) _c=F ;;
		esac
		_u="$_u$_c"
	done
	printf '%s\n' "$_u"
}

# snap <file> -- copy a /proc file, then parse the COPY.
#
# 🔴 量 ON THE DIE 2026-09-17, and no fixture could have shown it.  The shell's
# `read` builtin consumes a file ONE BYTE AT A TIME, so that it does not
# over-read a pipe.  A 2.6.30 read_proc_t re-renders its ENTIRE page on every
# one of those reads and the kernel returns one byte out of the fresh render.
# /proc/rtl819x-timer is 101 fields and several of them are free-running
# counters, so a field that grows by one character between two consecutive
# byte-reads shifts everything after it and a character already consumed is
# served again.
#
# The reading, three passes of the same loop over the live file:
#     [ce_live==1]        <- ONE doubled `=`, a field had grown
#     (nothing)           <- a field had shrunk and a character was skipped
#     (nothing)
# and MT-TICK's own failure line read `ce_live=11 ce_mode=(absent)
# spur=(absent) stuck=(absent)`: the first field corrupted, every field after
# it lost.
#
# The same loop over a `cat` snapshot, same shell, same fields, same minute:
#     [ce_reload=2000] [ce_reload_hz=2000] [ce_live=1] [ce_mode=2] ... all
#     eleven, clean.
# `cat` reads in whole blocks, so ONE render answers the whole file.
#
# 🟢 It also makes a before/after pair atomic, which the old code was not:
# FW-75 records that the driver reads `jiffies` inside the spin lock and
# `irq_count` 105 lines later outside it, and the old code compounded that by
# opening the file twice more.
#
# ⚠️ THE THREE CHECKS THAT COMPARE ACROSS TIME USE THIS, and MT-PORT since
# R6b-6: /proc/rtl819x-switch renders live registers and counters that move on
# every render (n_reads alone grows by 45), which is the hazard above exactly.
# In the capture that caught MT-TICK, the other checks read /proc/rtl819x-spi,
# /proc/rtl819x-wdt and the vendor's port_status correctly: their fields are
# static between verbs, so the hazard is latent there and is carried forward.
: "${MFG_SNAP:=/tmp/mfgtest.snap}"

snap() {
	cat "$1" > "$MFG_SNAP" 2>/dev/null || return 1
	[ -s "$MFG_SNAP" ]
}

# jdelta <before> <after> -- difference of two counters that can exceed
# INT32_MAX, computed without ever handing this shell a number that large.
#
# 🔴 量 ON THE DIE 2026-09-17, this shell's own arithmetic:
#     $((4294950451))            -> 2147483647    PARSING SATURATES
#     $((4294950451-4294950000)) -> 0             so a difference is lost
#     $((2147483647+1))          -> -2147483648   ARITHMETIC WRAPS
# Parsing saturates and arithmetic wraps -- two different behaviours in one
# shell, and the same saturation was measured at the desk hours earlier under
# qemu-mips-static with this unit's own busybox, which predicted the die
# exactly.
#
# jiffies starts at INITIAL_JIFFIES, and this board printed jiffies=4294950451
# with 131 s of uptime, so EVERY jiffies reading here is past the saturation
# point and $(( j1 - j0 )) is 0 whatever really happened.
#
# The last six digits are enough: a 5 s window at 100 Hz is 500.  They are
# zero-padded first so a short counter works, and prefixed with `1` for two
# reasons -- a leading zero would make $(( )) read the value as OCTAL, and the
# prefix keeps both operands far below the saturation point.  The wrap term
# handles the six-digit window rolling over.
jdelta() {
	_s=000000$1
	_a=1${_s#${_s%??????}}
	_s=000000$2
	_b=1${_s#${_s%??????}}
	_d=$((_b - _a))
	[ "$_d" -lt 0 ] && _d=$((_d + 1000000))
	printf '%s\n' "$_d"
}

# act <file> <verb> -- issue a verb, but never under a fixture.
act() {
	if [ -n "$MFG_ROOT" ]; then
		return 0
	fi
	echo "$2" > "$1"
}

# refuse <reason> -- a precondition failed.  Exit 2, never 1: a run that
# could not start and a run whose checks failed are different findings, and
# collapsing them is how a red stops meaning anything.
refuse() {
	printf 'REFUSING: %s\n' "$1"
	printf 'No check below ran.  This is not a failing unit; it is a run that could not begin.\n'
	exit 2
}

# ---------------------------------------------------------------------------
# preconditions.  The DoD's "the tool refuses if it cannot identify the unit".
#
# What identifies it is the IMAGE, not the unit: this unit's serial-equivalent
# is its MAC and that may not be printed (CLAUDE.md's second Never row, and
# docs/mfgtest.md 5 rules on it).  So the refusal is that the /proc surfaces
# this image is supposed to carry are there and are this driver's.
# ---------------------------------------------------------------------------

precheck() {
	for f in "$P_SPI" "$P_MAP" "$P_TIMER" "$P_WDT" "$P_GPIO"; do
		[ -r "$f" ] || refuse "$f is not readable -- this is not an rlxfw image, or a driver did not register"
	done
	v=$(field "$P_SPI" version) || refuse "$P_SPI carries no version field"
	case "$v" in
	"rtl819x-spi 1.2"*) : ;;
	*) refuse "$P_SPI reports [$v]; these checks are written against rtl819x-spi 1.2" ;;
	esac
}

# ---------------------------------------------------------------------------
# the checks
# ---------------------------------------------------------------------------

# MT-ID.  The image's own recipe id, read from /proc rather than from the
# boot console.  The build computes it as a sha256 over config/ and compiles
# it into every object; init/main.c prints it as the RLXFW-ID0 mark and this
# driver now prints it here, so a capture and a /proc read are two independent
# routes to one number.  The comparand is supplied by the caller -- the build
# knows it, the device must not be told what to expect by the device.
mt_id() {
	want=$1
	got=$(field "$P_SPI" recipe_id) || got="(absent)"
	if [ -z "$want" ]; then
		chk MT-ID 0 "no expected id was supplied; read [$got]"
		return
	fi
	# 🔴 FOLD THE COMPARAND, because the two sides of this `=` are produced
	# by different tools in different cases.  量 2026-09-17:
	# tools/rlxfw-kbuild.sh:262 computes the id as `sha256sum | cut -c1-8`,
	# which is LOWER case, and rtl819x-spi.c prints it with "%08X", which is
	# UPPER.  `mfgtest auto 03e7721c` -- the spelling PROGRESS.md and the
	# segment brief both carried -- would have turned MT-ID red with exactly
	# the right image on the board, which is the one failure a factory check
	# may never have.
	#
	# It is the ONLY comparand here that comes from outside this file.
	# MFG_RDID, A5000000 and BOOTGUARD were each written by reading the
	# driver's own format string, so their case was never in question.
	#
	# 🔴 AND IT IS A STRING FOLD, NOT ARITHMETIC, FOR A MEASURED REASON.
	# 量 2026-09-17, this unit's own busybox ash under qemu-mips-static:
	# `$((0xb1818b92))` is **2147483647** -- it SATURATES at INT32_MAX
	# instead of wrapping -- while dash and bash on the build host both give
	# 2978057106.  So `printf '%08X' $((0x$want))` would have silently
	# rewritten every id with its top bit set, which is half of them, and
	# b1818b92 -- the image built four minutes before this fix -- was one.
	# Two hex digits at a time can never reach that, and a pure parameter
	# expansion cannot reach it at all.
	case "$want" in
	"" | *[!0-9A-Fa-f]*)
		chk MT-ID 0 "expected id [$want] is not hex digits; read [$got]"
		return
		;;
	esac
	want=$(hexupper "$want")
	[ "$got" = "$want" ]
	r=$?
	chk MT-ID $((1 - r)) "recipe_id=$got expected=$want"
}

# MT-FLASH-1.  JEDEC Read ID through this project's own driver.
mt_flash1() {
	act "$P_SPI" rdid
	rc=$(field "$P_SPI" rdid_rc) || rc="(absent)"
	id=$(field "$P_SPI" rdid_id) || id="(absent)"
	m=$(field "$P_SPI" rdid_match) || m="(absent)"
	# Two comparators on purpose.  The kernel's rdid_match is against a
	# constant nobody typed; this script's is against MFG_RDID, and it is
	# the one an injection moves.  Both must agree.
	if [ "$rc" = "0" ] && [ "$id" = "$MFG_RDID" ] && [ "$m" = "1" ]; then
		chk MT-FLASH-1 1 "rdid_id=$id rdid_match=$m"
	else
		chk MT-FLASH-1 0 "rdid_rc=$rc rdid_id=$id (want $MFG_RDID) rdid_match=$m"
	fi
}

# MT-FLASH-2.  The write path must refuse, and refuse without writing.
mt_flash2() {
	before=$(field "$P_SPI" n_write_refused) || before=-1
	act "$P_SPI" trywrite
	after=$(field "$P_SPI" n_write_refused) || after=-1
	w=$(field "$P_SPI" n_writes) || w=-1
	# Under a fixture act() is a no-op, so the counter cannot move and the
	# fixture supplies the after-state directly.  On the device both
	# pointers refuse, which is +2.
	if [ -n "$MFG_ROOT" ]; then
		moved=1
	elif [ "$after" = "$((before + 2))" ]; then
		moved=1
	else
		moved=0
	fi
	if [ "$moved" = "1" ] && [ "$w" = "0" ]; then
		chk MT-FLASH-2 1 "n_write_refused=$after n_writes=$w"
	else
		chk MT-FLASH-2 0 "n_write_refused $before->$after n_writes=$w (want 0)"
	fi
}

# MT-FLASH-3.  The 32-group map.
#
# ONLY THE DEVICE-SIDE HALF IS SCORED HERE, and the split is stated rather
# than implied.  docs/mfgtest.md 2 gives the criterion as "31 of 32 groups
# identical to the reference" -- but the reference is a digest list held at
# the desk, and this image has no md5sum, no dd and nothing that can carry
# 32 sha256 constants usefully (FW-46).  What the device can say is that the
# traversal completed, that it hashed nothing inside H601, and that the two
# read paths agree over every unit.  The digest-against-reference half is
# tools/flashmap.py's, run on the capture.
mt_flash3() {
	act "$P_SPI" "map 0"
	ran=$(field "$P_MAP" map_ran) || ran="(absent)"
	rc=$(field "$P_MAP" map_rc) || rc="(absent)"
	hh=$(field "$P_MAP" map_h601_hashed) || hh="(absent)"
	du=$(field "$P_MAP" map_diff_units) || du="(absent)"
	if [ "$ran" = "1" ] && [ "$rc" = "0" ] && [ "$hh" = "0" ] && [ "$du" = "0" ]; then
		chk MT-FLASH-3 1 "map_rc=0 h601_hashed=0 diff_units=0 (digests scored at the desk)"
	else
		chk MT-FLASH-3 0 "map_ran=$ran map_rc=$rc h601_hashed=$hh diff_units=$du"
	fi
}

# MT-TICK.  The clockevent is live, and it advances.
mt_tick() {
	snap "$P_TIMER" || {
		chk MT-TICK 0 "cannot snapshot $P_TIMER"
		return
	}
	live=$(field "$MFG_SNAP" ce_live) || live="(absent)"
	mode=$(field "$MFG_SNAP" ce_mode) || mode="(absent)"
	spur=$(field "$MFG_SNAP" irq_spurious) || spur="(absent)"
	stuck=$(field "$MFG_SNAP" irq_stuck) || stuck="(absent)"

	# 🔴 THE PERIOD TERM, AND WITHOUT IT EVERYTHING BELOW IS A TAUTOLOGY.
	#
	# The delta pair below compares two quantities that are both counted by
	# the same interrupt: one tick is one jiffy and one irq_count.  So a tick
	# running at a tenth of its proper rate keeps skew at 0 and dj > 0, and
	# `sleep 5` simply takes fifty real seconds -- 量 seating 13, which put it
	# exactly this way: "nothing in the kernel could notice".  M28's stated
	# injection is `cereload` to a wrong value, and against the check as first
	# written that was a NO-TAKE: the counters agree with each other whatever
	# the period is.
	#
	# 讀 rtl819x-timer.c:860-861, which is where these two fields come from:
	#     rtl819x_ce_reload      counts per tick, LIVE   (what `cereload` writes)
	#     rtl819x_ce_reload_hz   counts per tick that HZ implies (derived at
	#                            init from hz_used / HZ)
	# and :1544, where the DRIVER ITSELF refuses to hand the tick over with
	# -ERANGE when they differ, its own comment reading "`cereload` has already
	# made the period deliberately wrong".  So this is the driver's criterion
	# read back, not a second one invented here.
	#
	# TWO DIFFERENT SENTINELS on purpose.  With one, two absent fields would
	# compare equal and the term would be satisfied by a timer that reports
	# neither -- a control that cannot fail, which this repository does not
	# accept.
	#
	# ⚠️ WHAT THIS TERM DOES NOT DO, stated rather than left to be found: both
	# values are software, so it catches a period programmed wrong and says
	# nothing about a hardware clock that has drifted.  The independent rate
	# check is Δjiffies against the VENDOR's tick -- /proc/interrupts line 13,
	# which `cereload` does not touch and which seating 13's P3-7 used to take
	# the two apart.  docs/mfgtest.md 2 lists /proc/interrupts among MT-TICK's
	# inputs and this script still does not read it; that gap is carried
	# forward rather than papered over.
	rel=$(field "$MFG_SNAP" ce_reload) || rel=-1
	relhz=$(field "$MFG_SNAP" ce_reload_hz) || relhz=-2

	# 量: the timer's field is `jiffies`.  `j_now` is the KEYS driver's
	# name for the same quantity, and reading it here returned nothing.
	# Both out of the snapshot already taken, so they come from ONE render.
	j0=$(field "$MFG_SNAP" jiffies) || j0=0
	i0=$(field "$MFG_SNAP" irq_count) || i0=0
	# Unconditional: see MFG_TICK_SECONDS.  Under a fixture this is the
	# window the harness writes the second state into.
	sleep "$MFG_TICK_SECONDS"
	snap "$P_TIMER" || {
		chk MT-TICK 0 "cannot snapshot $P_TIMER the second time"
		return
	}
	j1=$(field "$MFG_SNAP" jiffies) || j1=0
	i1=$(field "$MFG_SNAP" irq_count) || i1=0
	dj=$(jdelta "$j0" "$j1")
	di=$(jdelta "$i0" "$i1")
	skew=$((dj - di))
	[ "$skew" -lt 0 ] && skew=$((0 - skew))

	if [ "$live" = "1" ] && [ "$mode" = "2" ] && [ "$spur" = "0" ] &&
	   [ "$stuck" = "0" ] && [ "$rel" = "$relhz" ] && [ "$rel" -gt 0 ] &&
	   [ "$dj" -gt 0 ] && [ "$skew" -le "$MFG_TICK_TOL" ]; then
		chk MT-TICK 1 "ce_live=1 ce_mode=2 reload=$rel=$relhz dj=$dj di=$di skew=$skew"
	else
		chk MT-TICK 0 "ce_live=$live ce_mode=$mode spur=$spur stuck=$stuck reload=$rel want=$relhz dj=$dj di=$di skew=$skew"
	fi
}

# MT-WDT.  The read-only half.  The BITE is P1-4's injection and resets the
# board; nothing here arms anything.
mt_wdt() {
	probe=$(field "$P_WDT" wdtcnr_at_probe) || probe="(absent)"
	state=$(field "$P_WDT" state_name) || state="(absent)"
	# A5000000 is the whole proof that CONFIG_RTL_WTDOG=n took: 00600000
	# would be the vendor still arming it.  One field, two possible values.
	if [ "$probe" = "A5000000" ] && [ "$state" = "BOOTGUARD" ]; then
		chk MT-WDT 1 "wdtcnr_at_probe=$probe state=$state"
	else
		chk MT-WDT 0 "wdtcnr_at_probe=$probe (want A5000000) state=$state (want BOOTGUARD)"
	fi
}

# MT-PORT.  Link on the connected switch port, as rlxfw's own switch driver
# reports it (R6b-6): rtl819x-switch 1.2 prints `psrpN <word> up <0|1> ...`
# and a `version` line that names the reporter; the vendor's port_status leaves
# with the vendor tree at R6b-8.  psrp3 is MFG_PORT's port (mfginject C1d holds
# the two together).  The label says who REPORTED the link and whether the
# vendor tree is present -- never who configured the PHY.
mt_port() {
	snap "$P_PORT" || {
		chk MT-PORT 0 "$P_PORT is not readable"
		return
	}
	ver=$(field "$MFG_SNAP" version) || ver="(absent)"
	case "$ver" in
	"rtl819x-switch "*) ;;
	*)	chk MT-PORT 0 "no driver label in $P_PORT (version $ver)"
		return ;;
	esac
	pw=$(field "$MFG_SNAP" psrp3) || pw="(absent)"
	vt="vendor tree absent"
	[ -d "$MFG_ROOT/proc/rtl865x" ] && vt="vendor tree present"
	up=0
	case "$pw" in
	*" up 1 "*) up=1 ;;
	esac
	if [ "$up" = "1" ]; then
		chk MT-PORT 1 "$MFG_PORT LinkUp by $ver; $vt"
	else
		chk MT-PORT 0 "$MFG_PORT has no LinkUp -- cable out, or the wrong jack (by $ver; psrp3 $pw)"
	fi
}

# MT-MAC and MT-RFCAL.  One read of H601, two verdicts.
#
# NO BYTE OF THAT WINDOW IS PRINTED HERE OR ANYWHERE.  The driver emits
# booleans, a version and a structure size; this script compares them.  hw_len
# is safe because it is sizeof(HW_SETTING_T)+1, identical on every unit of
# this model -- docs/mfgtest.md 4 rules on exactly that.
mt_h601() {
	act "$P_SPI" h601
	rc=$(field "$P_SPI" h601_rc) || rc="(absent)"
	sig=$(field "$P_SPI" hw_sig_ok) || sig="(absent)"
	ver=$(field "$P_SPI" hw_ver) || ver="(absent)"
	hlen=$(field "$P_SPI" hw_len) || hlen="(absent)"
	sane=$(field "$P_SPI" hw_len_sane) || sane="(absent)"
	sum=$(field "$P_SPI" hw_sum_ok) || sum="(absent)"
	nz=$(field "$P_SPI" mac_not_zero) || nz="(absent)"
	nf=$(field "$P_SPI" mac_not_ff) || nf="(absent)"
	gb=$(field "$P_SPI" mac_group_bit) || gb="(absent)"

	# MT-MAC: the block is the uncompressed H6 form, version 1, and the
	# MAC in it is a usable unicast address.
	if [ "$rc" = "0" ] && [ "$sig" = "1" ] && [ "$ver" = "1" ] &&
	   [ "$sane" = "1" ] && [ "$nz" = "1" ] && [ "$nf" = "1" ] &&
	   [ "$gb" = "0" ]; then
		chk MT-MAC 1 "sig_ok=1 ver=1 len=$hlen mac unicast"
	else
		chk MT-MAC 0 "rc=$rc sig=$sig ver=$ver len=$hlen sane=$sane not_zero=$nz not_ff=$nf group_bit=$gb"
	fi

	# MT-RFCAL: the body checksum closes.  It covers the calibration block
	# as well as the MACs, which is why one sum is both checks' evidence
	# and why they are two lines rather than one.
	if [ "$rc" = "0" ] && [ "$sane" = "1" ] && [ "$sum" = "1" ]; then
		chk MT-RFCAL 1 "hw_sum_ok=1 over $hlen body bytes"
	else
		chk MT-RFCAL 0 "rc=$rc hw_len_sane=$sane hw_sum_ok=$sum"
	fi
}

# MT-LED.  Needs the operator's eye, so it is its own phase.
mt_led() {
	snap "$P_GPIO" || {
		chk MT-LED 0 "cannot snapshot $P_GPIO"
		return
	}
	b0=$(field "$MFG_SNAP" n_set_ok) || b0=-1
	w0=$(field "$MFG_SNAP" n_writes) || w0=-1
	if [ -z "$MFG_ROOT" ]; then
		echo 1 > "$P_LED"
	fi
	snap "$P_GPIO" || {
		chk MT-LED 0 "cannot snapshot $P_GPIO after the write"
		return
	}
	dat=$(field "$MFG_SNAP" dat) || dat="(absent)"
	b1=$(field "$MFG_SNAP" n_set_ok) || b1=-1
	w1=$(field "$MFG_SNAP" n_writes) || w1=-1
	# bit 6 is the lamp.  BRD-13: LED #2 of eight, ACTIVE LOW, so the bit
	# CLEARS when the lamp lights -- `dat` 0000007C -> 0000003C, 量 at
	# seating 20.
	#
	# 🔴 The first version of this decoded the bit with a shell glob and
	# got the wrong hex digit.  `dat` is eight hex digits and bit 6 lives
	# in the SEVENTH from the left, not the eighth; a pattern that reads
	# the last digit tests bits 0-3 and would have called every value lit.
	# Arithmetic expansion understands 0x and cannot be off by a nibble.
	# 🔴 GUARD THEN LOW BYTE, and both halves are measured.
	#
	# The guard: `$((0x$dat))` with dat=(absent) is an arithmetic syntax
	# error, which in ash ABORTS the script -- so a missing gpio driver would
	# have ended the phase instead of failing this check, and the population
	# line would have said POPULATION MISMATCH rather than naming the cause.
	#
	# The low byte: 量 2026-09-17, this unit's own busybox ash under
	# qemu-mips-static saturates $(( )) at INT32_MAX -- $((0xb1818b92)) is
	# 2147483647 -- so a `dat` with its top bit set would have been read as
	# 0x7FFFFFFF and bit 6 of that is 1, i.e. `not lit`, whatever the lamp was
	# doing.  This board's dat is 000000xx today and the same driver's `cnr`
	# reads FFFFFF8B, so the exposure is real and has simply not been reached.
	# Bit 6 lives in the low byte; the last two hex digits are all of it and
	# two digits cannot saturate.
	case "$dat" in
	"" | *[!0-9A-Fa-f]*)
		chk MT-LED 0 "dat=[$dat] is not hex -- $P_GPIO did not report it; n_set_ok $b0->$b1 n_writes $w0->$w1"
		return
		;;
	esac
	lowdat=${dat#${dat%??}}
	bit6=$(( (0x$lowdat >> 6) & 1 ))
	lit=$((1 - bit6))
	if [ "$lit" = "1" ] && [ "$b1" -gt "$b0" ] && [ "$w1" -gt "$w0" ]; then
		chk MT-LED 1 "dat=$dat bit6=0 n_set_ok $b0->$b1 n_writes $w0->$w1 -- OPERATOR: is LED #2 lit?"
	else
		chk MT-LED 0 "dat=$dat bit6=$bit6 (want 0) n_set_ok $b0->$b1 n_writes $w0->$w1"
	fi
}

# MT-BUTTON.  Needs a press, so it is its own phase.
#
# 🔴 THREE TERMS, AND THE FIRST TWO ARE WHY THE NEGATIVE CONTROL MEANS
# ANYTHING.  The first version of this read n_poll either side of a bare
# `sleep 4` and scored "n_poll moved".  Both halves were wrong, and the
# second half is the one that would have survived a fix of the first:
#
#   (a) NOTHING IN IT OPENED THE DEVICE, so the delta had no cause.  讀
#       drivers/input/input-polldev.c: the poll work is queued by
#       input_open_polled_device(), which the input core calls through
#       input_dev->open -- when a HANDLER opens the device.  讀
#       rtl819x-keys.c's own header, lines 91-103: "with no handler that
#       opens, poll() is NEVER CALLED ... every counter reads 0 for ever".
#       量 p11a.config-built:769, `# CONFIG_INPUT_EVBUG is not set`, so
#       nothing in this image opens it unprompted.  n_poll would have been
#       flat and MT-BUTTON WOULD HAVE FAILED ON A GOOD UNIT, pressed or not.
#       bench/2026-09-10's card had already measured this and typed
#       `sleep 3 < /dev/input/event0`, with its own note reading "the open
#       is what is needed"; this file dropped the redirect and kept the sleep.
#
#   (b) n_poll DOES NOT SEE THE PRESS.  It counts polls, and polls happen
#       because the node is open.  The field that moves when the button goes
#       down is b0_n_press, incremented in rtl819x_keys_poll() only after
#       `need` consecutive stable samples at the new level (100 ms debounce
#       over a 50 ms poll = 2).  A check that scores n_poll is green with the
#       button unplugged.
#
# So: n_open moved (the node was opened), n_poll moved (the poller actually
# ran), b0_n_press moved (a debounced press was seen).  Three failure modes,
# three terms, and the detail line names which one fired.
#
# 🔴 THE FIRST TWO TERMS ARE WHAT MAKE M26 A KILL RATHER THAN A NO-TAKE.
# M26 is "do not press; the counters must stay flat".  Against the old check
# that proved nothing -- the counters were flat either way -- which is
# pulling a cable that was never plugged in.  With the poller demonstrably
# running, a flat b0_n_press is the button, and nothing else.
mt_button() {
	snap "$P_KEYS" || {
		chk MT-BUTTON 0 "cannot snapshot $P_KEYS"
		return
	}
	o0=$(field "$MFG_SNAP" n_open) || o0=-1
	p0=$(field "$MFG_SNAP" n_poll) || p0=-1
	k0=$(field "$MFG_SNAP" b0_n_press) || k0=-1
	if [ -z "$MFG_ROOT" ]; then
		printf 'OPERATOR: press and hold the reset button for about 3 seconds, any time in the next %s.\n' "$MFG_BUTTON_SECONDS"
		# THE REDIRECT IS THE CAUSE, and it is `sleep N < node` rather
		# than `cat node &` for two measured reasons: the OPEN is what
		# starts the poll work (a background cat opens it no better), and
		# what comes out of the node is raw struct input_event bytes with
		# ESC among them, which on this console is 16 bytes per event on
		# the wire.  bench/2026-09-10's card settles both.
		sleep "$MFG_BUTTON_SECONDS" < "$P_EVENT"
	fi
	snap "$P_KEYS" || {
		chk MT-BUTTON 0 "cannot snapshot $P_KEYS after the window"
		return
	}
	o1=$(field "$MFG_SNAP" n_open) || o1=-1
	p1=$(field "$MFG_SNAP" n_poll) || p1=-1
	k1=$(field "$MFG_SNAP" b0_n_press) || k1=-1
	if [ "$o1" -gt "$o0" ] && [ "$p1" -gt "$p0" ] && [ "$k1" -gt "$k0" ]; then
		chk MT-BUTTON 1 "n_open $o0->$o1 n_poll $p0->$p1 b0_n_press $k0->$k1"
	else
		chk MT-BUTTON 0 "n_open $o0->$o1 (open) n_poll $p0->$p1 (poller) b0_n_press $k0->$k1 (press)"
	fi
}

# ---------------------------------------------------------------------------
# phases
#
# DECLARED is a population constant, the same idea every mutation suite here
# uses: a run that silently executes fewer checks than it has is caught,
# instead of reporting a smaller green.
# ---------------------------------------------------------------------------

DECLARED_auto=9
DECLARED_led=1
DECLARED_button=1

usage() {
	printf '%s\n' "$MFG_VERSION"
	printf 'usage: mfgtest.sh auto <expected-recipe-id> | led | button\n'
	printf '  auto    every check that needs no operator (%s checks)\n' "$DECLARED_auto"
	printf '  led     MT-LED; the operator reads the lamp\n'
	printf '  button  MT-BUTTON; the operator holds reset for 3 s\n'
	exit 2
}

phase=${1:-}
case "$phase" in
auto)
	precheck
	printf '%s  phase=auto\n' "$MFG_VERSION"
	mt_id "${2:-}"
	mt_flash1
	mt_flash2
	mt_flash3
	mt_tick
	mt_wdt
	mt_port
	mt_h601
	want=$DECLARED_auto
	;;
led)
	precheck
	printf '%s  phase=led\n' "$MFG_VERSION"
	mt_led
	want=$DECLARED_led
	;;
button)
	precheck
	printf '%s  phase=button\n' "$MFG_VERSION"
	mt_button
	want=$DECLARED_button
	;;
*)
	usage
	;;
esac

n=$((ok + bad))
if [ "$n" != "$want" ]; then
	printf 'POPULATION MISMATCH: %s checks ran, %s declared.\n' "$n" "$want"
	printf 'A phase that runs fewer checks than it declares reports a smaller green.\n'
	exit 3
fi
printf '%s of %s ok, %s FAIL\n' "$ok" "$n" "$bad"
[ "$bad" = "0" ] || exit 1
exit 0
