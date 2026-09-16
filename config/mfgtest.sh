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

MFG_VERSION="mfgtest 1.0"

: "${MFG_ROOT:=}"

P_SPI="$MFG_ROOT/proc/rtl819x-spi"
P_MAP="$MFG_ROOT/proc/rtl819x-spi-map"
P_TIMER="$MFG_ROOT/proc/rtl819x-timer"
P_WDT="$MFG_ROOT/proc/rtl819x-wdt"
P_GPIO="$MFG_ROOT/proc/rtl819x-gpio"
P_KEYS="$MFG_ROOT/proc/rtl819x-keys"
P_PORT="$MFG_ROOT/proc/rtl865x/port_status"
P_LED="$MFG_ROOT/sys/class/leds/n150rt:green:led2/brightness"

# The switch port the cable is in.  量 NET-13: this kernel's netdev numbering
# is the MIRROR of the vendor's (mine = 4 - vendor), so the jack the operator
# uses is switch port 3, which this kernel calls eth4.  The proc file prints
# SWITCH port indices, so the token is Port3.  Writing Port4 here -- the
# netdev number -- would pass on the wrong hole.
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
	live=$(field "$P_TIMER" ce_live) || live="(absent)"
	mode=$(field "$P_TIMER" ce_mode) || mode="(absent)"
	spur=$(field "$P_TIMER" irq_spurious) || spur="(absent)"
	stuck=$(field "$P_TIMER" irq_stuck) || stuck="(absent)"

	# 量: the timer's field is `jiffies`.  `j_now` is the KEYS driver's
	# name for the same quantity, and reading it here returned nothing.
	j0=$(field "$P_TIMER" jiffies) || j0=0
	i0=$(field "$P_TIMER" irq_count) || i0=0
	# Unconditional: see MFG_TICK_SECONDS.  Under a fixture this is the
	# window the harness writes the second state into.
	sleep "$MFG_TICK_SECONDS"
	j1=$(field "$P_TIMER" jiffies) || j1=0
	i1=$(field "$P_TIMER" irq_count) || i1=0
	dj=$((j1 - j0))
	di=$((i1 - i0))
	skew=$((dj - di))
	[ "$skew" -lt 0 ] && skew=$((0 - skew))

	if [ "$live" = "1" ] && [ "$mode" = "2" ] && [ "$spur" = "0" ] &&
	   [ "$stuck" = "0" ] && [ "$dj" -gt 0 ] && [ "$skew" -le "$MFG_TICK_TOL" ]; then
		chk MT-TICK 1 "ce_live=1 ce_mode=2 dj=$dj di=$di skew=$skew"
	else
		chk MT-TICK 0 "ce_live=$live ce_mode=$mode spur=$spur stuck=$stuck dj=$dj di=$di skew=$skew"
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

# MT-PORT.  Link on the connected switch port.
#
# The block for a port runs from the line beginning `PortN ` to the next such
# line.  A down port prints LinkDown and `continue`s, so it emits three fewer
# lines -- the block length is itself a discriminator, and that is why this
# tracks blocks instead of grepping the file for LinkUp anywhere.
mt_port() {
	if [ ! -r "$P_PORT" ]; then
		chk MT-PORT 0 "$P_PORT is not readable"
		return
	fi
	inblk=0
	up=0
	while read -r line; do
		case "$line" in
		"$MFG_PORT "*) inblk=1 ;;
		Port[0-9]" "*|CPUPort" "*) inblk=0 ;;
		esac
		if [ "$inblk" = "1" ]; then
			case "$line" in
			*LinkUp*) up=1 ;;
			esac
		fi
	done < "$P_PORT"
	if [ "$up" = "1" ]; then
		chk MT-PORT 1 "$MFG_PORT LinkUp"
	else
		chk MT-PORT 0 "$MFG_PORT has no LinkUp -- cable out, or the wrong jack"
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
	b0=$(field "$P_GPIO" n_set_ok) || b0=-1
	w0=$(field "$P_GPIO" n_writes) || w0=-1
	if [ -z "$MFG_ROOT" ]; then
		echo 1 > "$P_LED"
	fi
	dat=$(field "$P_GPIO" dat) || dat="(absent)"
	b1=$(field "$P_GPIO" n_set_ok) || b1=-1
	w1=$(field "$P_GPIO" n_writes) || w1=-1
	# bit 6 is the lamp.  BRD-13: LED #2 of eight, ACTIVE LOW, so the bit
	# CLEARS when the lamp lights -- `dat` 0000007C -> 0000003C, 量 at
	# seating 20.
	#
	# 🔴 The first version of this decoded the bit with a shell glob and
	# got the wrong hex digit.  `dat` is eight hex digits and bit 6 lives
	# in the SEVENTH from the left, not the eighth; a pattern that reads
	# the last digit tests bits 0-3 and would have called every value lit.
	# Arithmetic expansion understands 0x and cannot be off by a nibble.
	bit6=$(( (0x$dat >> 6) & 1 ))
	lit=$((1 - bit6))
	if [ "$lit" = "1" ] && [ "$b1" -gt "$b0" ] && [ "$w1" -gt "$w0" ]; then
		chk MT-LED 1 "dat=$dat bit6=0 n_set_ok $b0->$b1 n_writes $w0->$w1 -- OPERATOR: is LED #2 lit?"
	else
		chk MT-LED 0 "dat=$dat bit6=$bit6 (want 0) n_set_ok $b0->$b1 n_writes $w0->$w1"
	fi
}

# MT-BUTTON.  Needs a press, so it is its own phase.
mt_button() {
	o0=$(field "$P_KEYS" n_open) || o0=-1
	p0=$(field "$P_KEYS" n_poll) || p0=-1
	if [ -z "$MFG_ROOT" ]; then
		printf 'OPERATOR: hold the reset button for 3 seconds, starting now.\n'
		sleep 4
	fi
	o1=$(field "$P_KEYS" n_open) || o1=-1
	p1=$(field "$P_KEYS" n_poll) || p1=-1
	if [ "$p1" -gt "$p0" ]; then
		chk MT-BUTTON 1 "n_open $o0->$o1 n_poll $p0->$p1"
	else
		chk MT-BUTTON 0 "n_poll did not move: $p0->$p1"
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
