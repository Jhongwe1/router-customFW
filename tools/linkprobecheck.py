#!/usr/bin/env python3
"""linkprobecheck -- R6b-6's desk proof of `config/rlxfw-user/linkprobe/linkprobe.c`.

WHAT IT RUNS
------------
It compiles the repository's `linkprobe.c` with the HOST gcc and `-DLP_HOST`,
which swaps the program's four system shims (lp_open, lp_ioctl, lp_now_ns,
lp_sleep_ms) for a scripted fake written below: a fake SIOCETHTOOL that answers
from a per-interface script, a clock that moves only when the program sleeps,
and a log of every call the program made.  Everything else is the same bytes
the rsdk build compiles.

Cases (each prints one `  ok`/`  FAIL` line with exactly two leading spaces):

  K0   the harness compiles warning-free (-Wall -Wextra -Werror -Wundef -Wshadow)
  K1   `get rlx0 lo eth4 nosuch0` prints PROPOSAL-R6b-6 § 2.2's fourteen lines
       exactly, with the board's errno numbers (122, 19), and exits 0
  K2   the fake saw exactly twelve calls, each SIOCETHTOOL with a GDRVINFO,
       GLINK or GRINGPARAM command, a NUL-terminated name equal to the
       argument, and the whole buffer past `cmd` canary-filled BEFORE the call
  K3   a kernel that returns 0 WITHOUT WRITING reads `data A5A5A5A5 can 4`,
       never 1, and LP9 counts it in `nowrite`
  K4   GLINK 0 reads `data 00000000 can 0`: distinct from 1 and from no-write
  K5   a 32-byte field with no NUL prints `nonul`
  K6   `"`, `\\` and non-printable bytes print as `\\xHH`
  K7   every argument refusal, each shown REFUSING and PERMITTING at its
       boundary; a refusal prints LP0 then one LPE line, exits 2, and makes no
       call at all
  K8   a socket() failure prints `LPE socket rc <errno>`, exits 3, no call
  K9   watch: the transitions of a scripted GLINK sequence, their times and
       indices on the fake clock, and the end line's counts, exactly
  K10  watch: n <= floor(s*1000/ms) + 1 holds when the sleep returns EARLY
       (the schedule counter), and the clock bound when it returns late
  K11  watch: a run killed at its first sleep has already printed LPW start
       -- running is told from never started
  K12  watch: a no-write GLINK is classed `nowrite`, not `ones` or `zeros`
  K13  source rules: no ETHTOOL_S*, no ioctl request but SIOCETHTOOL, and no
       `/` or `%` operator (gate G1 counts `break` in the object; this is the
       same rule one level up, where a mutant can be written)

Then the mutants.  M0 runs the UNMUTATED source through the same mutation path
and must be green on every case a mutant names; each Mn changes the source or
the fake's script one way and the case it names must go red.  A mutant whose
anchor does not occur exactly once REFUSES the run rather than being skipped.

WHAT IT CANNOT SEE
------------------
The ABI.  Host structs happen to have the same layout, but the marshalling on
a big-endian MIPS kernel is gate G6's (header identity) and the board's.
qemu-mips-static 8.2.2 does not translate SIOCETHTOOL at all (量 2026-09-26:
rc 25, ENOTTY, on lo, eth0 and a missing name), so the real kernel path is
tested only on the silicon.  It also cannot see the timing of a real
nanosleep: the fake clock tests the logic of both bounds, not HZ.

    linkprobecheck.py [--src PATH]

Exit 0 all green; 1 a case or a mutant failed; 2 refused (no gcc, an anchor
that does not match exactly once, a harness that does not compile).
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "config", "rlxfw-user", "linkprobe", "linkprobe.c")
CFLAGS = ["-std=gnu99", "-Os", "-Wall", "-Wextra", "-Werror", "-Wundef",
          "-Wshadow", "-fno-builtin", "-fno-strict-aliasing", "-DLP_HOST"]
CANARY_U32 = 0xA5A5A5A5


class Refused(Exception):
    pass


# ---------------------------------------------------------------------------
# The fake.  C, so it links against the probe's own externs.
# ---------------------------------------------------------------------------

FAKE_C = r"""
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <net/if.h>
#include <linux/sockios.h>
#include <linux/ethtool.h>

typedef unsigned int u32;
typedef unsigned long long u64;

static u64 fake_t = 5000000000ull;
static unsigned fake_ncall;

static void lg(const char *fmt, ...)
{
	const char *p = getenv("LPFAKE_LOG");
	FILE *f;
	va_list ap;

	if (!p)
		return;
	f = fopen(p, "a");
	if (!f)
		return;
	va_start(ap, fmt);
	vfprintf(f, fmt, ap);
	va_end(ap);
	fclose(f);
}

int lp_fake_socket(void)
{
	const char *e = getenv("LPFAKE_SOCKET_ERR");

	if (e && *e) {
		lg("socket err %s\n", e);
		errno = atoi(e);
		return -1;
	}
	lg("socket ok\n");
	return 3;
}

u64 lp_fake_now_ns(void)
{
	return fake_t;
}

void lp_fake_sleep_ms(u32 ms)
{
	const char *a = getenv("LPFAKE_SLEEP_ABORT");
	const char *p = getenv("LPFAKE_SLEEP_PCT");
	u64 pct = p ? (u64)atoi(p) : 100u;

	if (a && *a) {
		lg("sleep abort\n");
		_exit(9);
	}
	fake_t += (u64)ms * 1000000ull * pct / 100u;
}

/* per-interface call counts, for `seq` */
static char seen_name[16][IFNAMSIZ + 1];
static unsigned seen_n[16];
static unsigned seen_used;

static unsigned bump(const char *nm)
{
	unsigned i;

	for (i = 0; i < seen_used; i++)
		if (!strcmp(seen_name[i], nm))
			return seen_n[i]++;
	if (seen_used < 16) {
		strcpy(seen_name[seen_used], nm);
		seen_n[seen_used] = 1;
		seen_used++;
	}
	return 0;
}

/* LPFAKE = "if req spec;if req spec;..."  req may be `*`.  -> spec or NULL */
static int lookup(const char *nm, const char *req, char *out, size_t cap)
{
	const char *s = getenv("LPFAKE");
	char buf[4096], *save = 0, *ent;

	if (!s)
		return 0;
	snprintf(buf, sizeof(buf), "%s", s);
	for (ent = strtok_r(buf, ";", &save); ent; ent = strtok_r(0, ";", &save)) {
		char a[64], b[64];
		int k = 0;

		if (sscanf(ent, " %63s %63s %n", a, b, &k) != 2)
			continue;
		if (strcmp(a, nm) || (strcmp(b, req) && strcmp(b, "*")))
			continue;
		snprintf(out, cap, "%s", ent + k);
		return 1;
	}
	return 0;
}

static void put32(unsigned char *b, unsigned off, u32 v)
{
	memcpy(b + off, &v, 4);
}

int lp_fake_ioctl(int fd, unsigned long req, struct ifreq *ifr)
{
	unsigned char *b = (unsigned char *)ifr->ifr_data;
	char nm[IFNAMSIZ + 1], spec[256], tok[64];
	const char *rq = "?";
	unsigned size = 4, i, bad = 0, idx;
	int nul;
	u32 cmd;

	memcpy(&cmd, b, 4);
	memcpy(nm, ifr->ifr_name, IFNAMSIZ);
	nm[IFNAMSIZ] = 0;
	nul = memchr(ifr->ifr_name, 0, IFNAMSIZ) != NULL;
	if (cmd == ETHTOOL_GDRVINFO) { rq = "drv"; size = sizeof(struct ethtool_drvinfo); }
	if (cmd == ETHTOOL_GLINK) { rq = "link"; size = sizeof(struct ethtool_value); }
	if (cmd == ETHTOOL_GRINGPARAM) { rq = "ring"; size = sizeof(struct ethtool_ringparam); }
	for (i = 4; i < size; i++)
		if (b[i] != 0xA5)
			bad++;
	fake_ncall++;
	lg("call %u fd %d req %lx if %s nul %d cmd %x canary_bad %u\n",
	   fake_ncall, fd, req, nm, nul, cmd, bad);
	idx = bump(nm);
	if (!lookup(nm, rq, spec, sizeof(spec)))
		snprintf(spec, sizeof(spec), "err 19");
	if (!strncmp(spec, "seq ", 4)) {
		/* the idx-th comma token, the last one repeating */
		char *save = 0, *t, last[64] = "n";
		unsigned k = 0;
		char sb[256];

		snprintf(sb, sizeof(sb), "%s", spec + 4);
		for (t = strtok_r(sb, ",", &save); t; t = strtok_r(0, ",", &save), k++) {
			snprintf(last, sizeof(last), "%s", t);
			if (k == idx)
				break;
		}
		snprintf(tok, sizeof(tok), "%s", last);
		if (tok[0] == 'e')
			snprintf(spec, sizeof(spec), "err %s", tok + 1);
		else if (tok[0] == 'n')
			snprintf(spec, sizeof(spec), "nowrite");
		else
			snprintf(spec, sizeof(spec), "val %s", tok);
	}
	if (!strncmp(spec, "err ", 4))
		return atoi(spec + 4);
	if (!strcmp(spec, "nowrite"))
		return 0;
	/* everything below writes, the way the kernel does: the whole struct
	 * zeroed (ethtool_get_drvinfo's memset, `= { cmd }` for the others),
	 * then the fields */
	memset(b + 4, 0, size - 4);
	if (!strncmp(spec, "val ", 4)) {
		put32(b, 4, (u32)strtoul(spec + 4, 0, 0));
		return 0;
	}
	if (!strcmp(spec, "ok") && cmd == ETHTOOL_GRINGPARAM) {
		put32(b, 4, 8);		/* rx_max_pending  */
		put32(b, 16, 4);	/* tx_max_pending  */
		put32(b, 20, 8);	/* rx_pending      */
		put32(b, 32, 4);	/* tx_pending      */
		return 0;
	}
	if (cmd == ETHTOOL_GDRVINFO) {
		struct ethtool_drvinfo *d = (struct ethtool_drvinfo *)b;

		if (!strcmp(spec, "ok")) {
			strncpy(d->driver, "rtl819x-nic", sizeof(d->driver) - 1);
			strncpy(d->version, "rtl819x-nic 1.5", sizeof(d->version) - 1);
			strncpy(d->bus_info, "platform", sizeof(d->bus_info) - 1);
			return 0;
		}
		if (!strcmp(spec, "nonul")) {
			memset(d->driver, 'x', sizeof(d->driver));
			strncpy(d->version, "v", sizeof(d->version) - 1);
			return 0;
		}
		if (!strcmp(spec, "esc")) {
			strcpy(d->driver, "a\"b\\c\x01\xc3z");
			return 0;
		}
	}
	lg("fake: no rule for spec [%s] cmd %x\n", spec, cmd);
	return 77;
}
"""


# ---------------------------------------------------------------------------
# Build and run
# ---------------------------------------------------------------------------

def have_gcc():
    return shutil.which("gcc") is not None


def compile_probe(src_text, work, tag):
    """-> (binary path or None, compiler output)."""
    d = os.path.join(work, tag)
    os.makedirs(d, exist_ok=True)
    sp = os.path.join(d, "linkprobe.c")
    fp = os.path.join(d, "fake.c")
    with open(sp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(src_text)
    with open(fp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(FAKE_C)
    out = os.path.join(d, "linkprobe-host")
    r = subprocess.run(["gcc"] + CFLAGS + ["-o", out, sp, fp],
                       capture_output=True, text=True, encoding="utf-8")
    msg = (r.stdout + r.stderr).strip()
    return (out if r.returncode == 0 else None), msg


def run(binary, args, script="", env_extra=None, work=None):
    """-> (rc, stdout, [log lines])."""
    fd, logp = tempfile.mkstemp(prefix="lpfake-", suffix=".log", dir=work)
    os.close(fd)
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
           "LPFAKE": script, "LPFAKE_LOG": logp}
    if env_extra:
        env.update(env_extra)
    r = subprocess.run([binary] + list(args), capture_output=True, env=env,
                       timeout=120)
    with open(logp, encoding="utf-8", errors="replace") as fh:
        log = fh.read().splitlines()
    os.unlink(logp)
    return r.returncode, r.stdout.decode("ascii", "replace"), log


def calls(log):
    return [ln for ln in log if ln.startswith("call ")]


# ---------------------------------------------------------------------------
# The scripts and the expected text
# ---------------------------------------------------------------------------

BOARD = ("rlx0 drv ok;rlx0 link val 1;rlx0 ring ok;"
         "lo drv err 122;lo link val 1;lo ring err 122;"
         "eth4 * err 122;nosuch0 * err 19")

LP0 = "LP0 linkprobe 1 build 0000000000000000"

K1_EXPECT = "\n".join([
    LP0,
    'LP drv rlx0 rc 0 driver "rtl819x-nic" version "rtl819x-nic 1.5" fw "" '
    'bus "platform" can 0',
    "LP link rlx0 rc 0 data 00000001 can 0",
    "LP ring rlx0 rc 0 rx 8/8 mini 0/0 jumbo 0/0 tx 4/4 can 0",
    "LP drv lo rc 122 can 192",
    "LP link lo rc 0 data 00000001 can 0",
    "LP ring lo rc 122 can 32",
    "LP drv eth4 rc 122 can 192",
    "LP link eth4 rc 122 can 4",
    "LP ring eth4 rc 122 can 32",
    "LP drv nosuch0 rc 19 can 192",
    "LP link nosuch0 rc 19 can 4",
    "LP ring nosuch0 rc 19 can 32",
    "LP9 calls 12 ok 4 refused 8 nowrite 0",
]) + "\n"

K1_ARGS = ["get", "rlx0", "lo", "eth4", "nosuch0"]

CALL_RE = re.compile(r"^call (\d+) fd (-?\d+) req ([0-9a-f]+) if (\S*) nul (\d) "
                     r"cmd ([0-9a-f]+) canary_bad (\d+)$")


# ---------------------------------------------------------------------------
# The cases.  Each takes the binary and the work dir -> (ok, detail).
# ---------------------------------------------------------------------------

def k1(b, w):
    rc, out, _log = run(b, K1_ARGS, BOARD, work=w)
    if rc == 0 and out == K1_EXPECT:
        return True, "14 lines exact, errno 122 and 19, rc 0"
    diff = [(i, a, e) for i, (a, e) in
            enumerate(zip(out.splitlines(), K1_EXPECT.splitlines())) if a != e]
    return False, "rc=%d first difference %r" % (rc, diff[:1] or out[-200:])


def k2(b, w):
    rc, _out, log = run(b, K1_ARGS, BOARD, work=w)
    cs = [CALL_RE.match(c) for c in calls(log)]
    if len(cs) != 12 or not all(cs):
        return False, "%d calls parsed of %d logged" % (sum(1 for c in cs if c),
                                                        len(calls(log)))
    names = [c.group(4) for c in cs]
    want = [n for n in K1_ARGS[1:] for _ in range(3)]
    reqs = {c.group(3) for c in cs}
    cmds = [c.group(6) for c in cs]
    bad = [int(c.group(7)) for c in cs]
    nul = {c.group(5) for c in cs}
    ok = (names == want and reqs == {"8946"} and cmds == ["3", "a", "10"] * 4
          and bad == [0] * 12 and nul == {"1"} and rc == 0)
    return ok, ("12 calls, SIOCETHTOOL only, cmds 3/a/10 x4, names in order, "
                "every buffer canary-filled before the call" if ok else
                "names=%s reqs=%s cmds=%s canary_bad=%s nul=%s"
                % (names, reqs, cmds, bad, nul))


def k3(b, w):
    rc, out, _ = run(b, ["get", "rlx0"],
                     "rlx0 drv nowrite;rlx0 link nowrite;rlx0 ring nowrite",
                     work=w)
    want_link = "LP link rlx0 rc 0 data A5A5A5A5 can 4"
    want_drv = ("LP drv rlx0 rc 0 driver nonul version nonul fw nonul "
                "bus nonul can 192")
    want9 = "LP9 calls 3 ok 3 refused 0 nowrite 3"
    lines = out.splitlines()
    ok = (rc == 0 and want_link in lines and want_drv in lines
          and want9 in lines and "data 00000001" not in out
          and any(ln.startswith("LP ring rlx0 rc 0 rx 2779096485/2779096485")
                  and ln.endswith(" can 32") for ln in lines))
    return ok, ("a no-write rc 0 reads A5A5A5A5 can 4, drv all nonul can 192, "
                "ring can 32, LP9 nowrite 3" if ok else out[-400:])


def k4(b, w):
    rc, out, _ = run(b, ["get", "rlx0"], "rlx0 link val 0;rlx0 drv ok;rlx0 ring ok",
                     work=w)
    ok = rc == 0 and "LP link rlx0 rc 0 data 00000000 can 0" in out.splitlines()
    return ok, "GLINK 0 reads data 00000000 can 0" if ok else out[-300:]


def k5(b, w):
    rc, out, _ = run(b, ["get", "rlx0"], "rlx0 drv nonul;rlx0 * err 122", work=w)
    ok = rc == 0 and ('LP drv rlx0 rc 0 driver nonul version "v" fw "" bus "" '
                      "can 0") in out.splitlines()
    return ok, "32 bytes with no NUL print `nonul`" if ok else out[-300:]


def k6(b, w):
    rc, out, _ = run(b, ["get", "rlx0"], "rlx0 drv esc;rlx0 * err 122", work=w)
    want = ('LP drv rlx0 rc 0 driver "a\\x22b\\x5Cc\\x01\\xC3z" version "" '
            'fw "" bus "" can 0')
    ok = rc == 0 and want in out.splitlines()
    return ok, ('`"` `\\` 0x01 0xC3 print as \\xHH' if ok else out[-300:])


# (args, must_refuse, the LPE text or None).  Each boundary appears on both
# sides.  The permitting watch runs are fast because the clock is the fake's.
K7_ROWS = [
    ([], True, "usage: linkprobe get <if>... | watch <if> <ms> <s>"),
    (["set", "rlx0"], True, "unknown mode"),
    (["get"], True, "get takes 1 to 8 interface names"),
    (["get"] + ["a%d" % i for i in range(8)], False, None),
    (["get"] + ["a%d" % i for i in range(9)], True,
     "get takes 1 to 8 interface names"),
    (["get", "x" * 15], False, None),
    (["get", "x" * 16], True, "ifname must be 1 to 15 characters"),
    (["get", ""], True, "ifname must be 1 to 15 characters"),
    (["watch", "lo", "10"], True, "watch takes <if> <ms> <s>"),
    (["watch", "x" * 16, "10", "1"], True, "ifname must be 1 to 15 characters"),
    (["watch", "lo", "9", "1"], True, "ms must be 10 to 10000"),
    (["watch", "lo", "10", "1"], False, None),
    (["watch", "lo", "10000", "1"], False, None),
    (["watch", "lo", "10001", "1"], True, "ms must be 10 to 10000"),
    (["watch", "lo", "1x", "1"], True, "ms must be 10 to 10000"),
    (["watch", "lo", "10", "0"], True, "s must be 1 to 600"),
    (["watch", "lo", "100", "600"], False, None),
    (["watch", "lo", "100", "601"], True, "s must be 1 to 600"),
    (["watch", "lo", "10", "1234567890"], True, "s must be 1 to 600"),
]


def k7(b, w):
    bad = []
    for args, refuse, text in K7_ROWS:
        rc, out, log = run(b, args, "lo link val 1", work=w)
        lines = out.splitlines()
        if refuse:
            good = (rc == 2 and lines == [LP0, "LPE " + text]
                    and not calls(log))
        else:
            good = rc == 0 and bool(calls(log)) and not any(
                ln.startswith("LPE") for ln in lines)
        if not good:
            bad.append("%s rc=%d %r" % (args[:3], rc, lines[-1:]))
    nref = sum(1 for r in K7_ROWS if r[1])
    return (not bad, "%d refusals exit 2 with no call, %d permitting twins run"
            % (nref, len(K7_ROWS) - nref) if not bad else "; ".join(bad))


def k8(b, w):
    rc, out, log = run(b, ["get", "rlx0"], BOARD,
                       env_extra={"LPFAKE_SOCKET_ERR": "24"}, work=w)
    ok = (rc == 3 and out.splitlines() == [LP0, "LPE socket rc 24"]
          and not calls(log))
    return ok, "socket failure: LPE socket rc 24, exit 3, no call" if ok else \
        "rc=%d %r" % (rc, out)


WATCH_SEQ = "rlx0 link seq 1,1,1,0,0,e25,0,1"
K9_EXPECT = "\n".join([
    LP0,
    "LPW start rlx0 v 1 rc 0",
    "LPW t 30 i 3 v 0 rc 0",
    "LPW t 50 i 5 v %d rc 25" % CANARY_U32,
    "LPW t 60 i 6 v 0 rc 0",
    "LPW t 70 i 7 v 1 rc 0",
    "LPW end n 101 ms 1000 ones 97 zeros 3 other 0 err 1 nowrite 0 trans 4",
]) + "\n"

END_RE = re.compile(r"^LPW end n (\d+) ms (\d+) ones (\d+) zeros (\d+) other (\d+) "
                    r"err (\d+) nowrite (\d+) trans (\d+)$")


def _end(out):
    for ln in out.splitlines():
        m = END_RE.match(ln)
        if m:
            return [int(x) for x in m.groups()]
    return None


def k9(b, w):
    rc, out, log = run(b, ["watch", "rlx0", "10", "1"], WATCH_SEQ, work=w)
    e = _end(out)
    closes = e is not None and sum(e[2:7]) == e[0] == len(calls(log))
    ok = rc == 0 and out == K9_EXPECT and closes
    return ok, ("four transitions at 30/50/60/70 ms, n 101 = 1000/10 + 1, "
                "ones+zeros+other+err+nowrite = n = calls" if ok else
                "rc=%d closes=%s out=%r" % (rc, closes, out[-300:]))


def k10(b, w):
    rows = []
    # (sleep %, want n, want ms).  Early: the schedule counter holds n at
    # 1000/10 + 1 although only 500 ms pass.  Late: the clock stops it at 51.
    for pct, n_want, ms_want in ((50, 101, 500), (100, 101, 1000),
                                 (200, 51, 1000)):
        rc, out, log = run(b, ["watch", "lo", "10", "1"], "lo link val 1",
                           env_extra={"LPFAKE_SLEEP_PCT": str(pct)}, work=w)
        e = _end(out)
        good = (rc == 0 and e is not None and e[0] == n_want
                and e[1] == ms_want and e[0] <= 1000 // 10 + 1
                and len(calls(log)) == e[0])
        rows.append((pct, good, e))
    ok = all(g for _p, g, _e in rows)
    return ok, ("sleep 50%%/100%%/200%% -> n %s, all <= floor(1000/10)+1"
                % "/".join(str(e[0]) for _p, _g, e in rows) if ok else
                repr(rows))


def k11(b, w):
    rc, out, log = run(b, ["watch", "rlx0", "10", "600"], "rlx0 link val 1",
                       env_extra={"LPFAKE_SLEEP_ABORT": "1"}, work=w)
    lines = out.splitlines()
    ok = (rc == 9 and lines == [LP0, "LPW start rlx0 v 1 rc 0"]
          and len(calls(log)) == 1 and "sleep abort" in log)
    return ok, ("killed at the first sleep, after one call: LPW start is "
                "already out, LPW end is not" if ok else "rc=%d %r" % (rc, lines))


def k12(b, w):
    rc, out, _ = run(b, ["watch", "rlx0", "10", "1"], "rlx0 link nowrite",
                     work=w)
    e = _end(out)
    ok = (rc == 0 and e is not None and e[6] == e[0] == 101 and e[2] == 0
          and e[3] == 0 and "LPW start rlx0 v %d rc 0" % CANARY_U32 in out)
    return ok, "no-write GLINK: nowrite 101 of 101, ones 0, zeros 0" if ok \
        else "rc=%d %r" % (rc, out[-300:])


def strip_c(text):
    """Comments, string and character literals removed."""
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"//[^\n]*", " ", text)
    text = re.sub(r'"(?:\\.|[^"\\\n])*"', '""', text)
    text = re.sub(r"'(?:\\.|[^'\\\n])+'", "0", text)
    return text


def source_rules(text):
    code = strip_c(text)
    code = re.sub(r"^\s*#\s*include[^\n]*", "", code, flags=re.M)
    bad = []
    if re.search(r"\bETHTOOL_S[A-Z]+", code):
        bad.append("an ETHTOOL_S* request")
    siocs = set(re.findall(r"\bSIOC[A-Z]+\b", code))
    if siocs - {"SIOCETHTOOL"}:
        bad.append("ioctl requests %s" % sorted(siocs - {"SIOCETHTOOL"}))
    ops = re.findall(r"[/%]", code)
    if ops:
        bad.append("%d `/` or `%%` outside comments and strings" % len(ops))
    return bad


def k13(_b, _w, text=None):
    bad = source_rules(text)
    ok = not bad
    return ok, ("no ETHTOOL_S*, SIOCETHTOOL only, no / or %" if ok else
                "; ".join(bad))


CASES = [("K1", k1), ("K2", k2), ("K3", k3), ("K4", k4), ("K5", k5),
         ("K6", k6), ("K7", k7), ("K8", k8), ("K9", k9), ("K10", k10),
         ("K11", k11), ("K12", k12), ("K13", k13)]


def run_case(name, fn, binary, work, text):
    """-> (ok, detail), the detail on ONE line: ci-census reads every line
    that starts with two spaces, and a program's output quoted into a
    detail must not be able to start one."""
    try:
        if name == "K13":
            ok, detail = fn(binary, work, text)
        else:
            ok, detail = fn(binary, work)
    except subprocess.TimeoutExpired:
        ok, detail = False, "timed out"
    return ok, " | ".join(str(detail).splitlines())


# ---------------------------------------------------------------------------
# The mutants.  (id, what, the case that must go red, source edit or None,
# script override or None).  A source edit is (old, new): `old` must occur in
# the source exactly once.
# ---------------------------------------------------------------------------

MUTANTS = [
    ("M1", "the fake returns 0 for rlx0's GLINK without writing", "K1",
     None, ("BOARD", BOARD.replace("rlx0 link val 1", "rlx0 link nowrite"))),
    ("M2", "the canary fill is gone (buffer zeroed instead)", "K3",
     ("lp_b.b[i] = (unsigned char)LP_CANARY;", "lp_b.b[i] = 0u;"), None),
    ("M3", "the can count is dropped", "K3",
     ("*can = n;", "*can = 0u;"), None),
    ("M4", "the fake answers the PC's EOPNOTSUPP, 95, in place of 122", "K1",
     None, ("BOARD", BOARD.replace("err 122", "err 95"))),
    ("M5", "the success path skips LP9", "K1",
     ('lp_puts("LP9 calls ");', 'return 0;'), None),
    ("M6", "GLINK's data is printed as a constant 1", "K3",
     ("lp_hex32(lp_b.val.data);", "lp_hex32(1u);"), None),
    ("M7", "the ifname bound is off by one", "K7",
     ("n >= 1u && n < (unsigned)IFNAMSIZ", "n >= 1u && n <= (unsigned)IFNAMSIZ"),
     None),
    ("M8", "the s bound is off by one", "K7",
     ("s < LP_S_MIN || s > LP_S_MAX)", "s < LP_S_MIN || s > LP_S_MAX + 1u)"),
     None),
    ("M9", "the ms lower bound is gone", "K7",
     ("ms < LP_MS_MIN || ms > LP_MS_MAX", "ms < 1u || ms > LP_MS_MAX"), None),
    ("M10", "the nonul test is gone", "K5",
     ("if (len == n) {", "if (0) {"), None),
    ("M11", "`\"` and `\\` are no longer escaped", "K6",
     ("c <= 0x7eu && c != '\"' && c != '\\\\')", "c <= 0x7eu)"), None),
    ("M12", "a value change is not a transition, only an rc change", "K9",
     ("if (rc != rc0 || (rc == 0 && v != v0)) {", "if (rc != rc0) {"), None),
    ("M13", "the schedule counter is gone", "K10",
     ("if (sched > total_ns)", "if (0)"), None),
    ("M14", "LPW start is not printed", "K11",
     ('lp_puts("LPW start ");', 'lp_puts("");'), None),
    ("M15", "LP9's nowrite never counts", "K3",
     ("if (n == r->size - 4u)", "if (0)"), None),
    ("M16", "a refused call is counted as ok", "K1",
     ("lp_n_refused++;", "lp_n_ok++;"), None),
    ("M17", "the watch classes a no-write sample by its value", "K12",
     ("if (can == 4u)\n\t\treturn 1u;", "if (0)\n\t\treturn 1u;"), None),
    ("M18", "a SET request enters the table", "K13",
     ('{ "ring", ETHTOOL_GRINGPARAM,', '{ "ring", ETHTOOL_SRINGPARAM,'), None),
    ("M19", "a division enters the decimal parser", "K13",
     ("v = v * 10u + (u32)(s[k] - '0');", "v = v * 10u / 1u + (u32)(s[k] - '0');"),
     None),
    ("M20", "a socket failure exits 2 instead of 3", "K8",
     ("lp_puts(\"\\n\");\n\t\treturn 3;\n\t}\n\tfor (i = 2;",
      "lp_puts(\"\\n\");\n\t\treturn 2;\n\t}\n\tfor (i = 2;"), None),
    ("M21", "cmd is not written before the call", "K2",
     ("lp_b.val.cmd = r->cmd;", ";"), None),
    ("M22", "an argument refusal happens after the socket and a call", "K7",
     ("\tfor (i = 2; i < argc; i++)\n\t\tif (!lp_ifname_ok(argv[i]))\n"
      "\t\t\treturn lp_refuse(\"ifname must be 1 to 15 characters\");\n"
      "\tfd = lp_open();",
      "\tfd = lp_open();\n\t{ unsigned cz; (void)lp_call(fd, \"x\", &lp_reqs[0], &cz); }\n"
      "\tfor (i = 2; i < argc; i++)\n\t\tif (!lp_ifname_ok(argv[i]))\n"
      "\t\t\treturn lp_refuse(\"ifname must be 1 to 15 characters\");"), None),
]

#: TYPED, never computed from the table: a deleted row would otherwise read
#: as "n of n killed".
DECLARED_MUTANTS = 22


def main(argv):
    global BOARD    # a script mutant swaps it for the run of its one case
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--src", default=SRC)
    a = ap.parse_args(argv)

    print("linkprobecheck 1.0 -- linkprobe.c on the host, against a scripted "
          "SIOCETHTOOL")
    if not have_gcc():
        print("REFUSED: no host gcc on PATH; this check compiles the source "
              "and does not report without it")
        return 2
    if not os.path.isfile(a.src):
        print("REFUSED: no source at %s" % a.src)
        return 2
    text = open(a.src, encoding="utf-8").read()

    if len(MUTANTS) != DECLARED_MUTANTS or \
            len({m[0] for m in MUTANTS}) != DECLARED_MUTANTS:
        print("REFUSED: %d mutant rows, DECLARED_MUTANTS says %d"
              % (len(MUTANTS), DECLARED_MUTANTS))
        return 2
    # Every source anchor must occur exactly once, before anything runs: a
    # mutant that did not apply would read as a kill by a case that was
    # already red, or as a survivor of an edit that never happened.
    for mid, _what, _case, edit, _scr in MUTANTS:
        if edit and text.count(edit[0]) != 1:
            print("REFUSED: %s's anchor occurs %d times in %s; it must occur "
                  "exactly once" % (mid, text.count(edit[0]), a.src))
            return 2
    names = {n for n, _f in CASES}
    for mid, _what, case, _e, _s in MUTANTS:
        if case not in names:
            print("REFUSED: %s names %s, which is not a case" % (mid, case))
            return 2

    work = tempfile.mkdtemp(prefix="linkprobecheck-")
    fails = 0
    try:
        binary, msg = compile_probe(text, work, "base")
        print("  %-4s  %-4s %s" % ("ok" if binary else "FAIL", "K0",
                                   "the harness compiles with -Wall -Wextra "
                                   "-Werror -Wundef -Wshadow" if binary else
                                   " | ".join(msg[-400:].splitlines())))
        if not binary:
            print("REFUSED: the unmutated source does not compile on the host; "
                  "nothing below would mean anything")
            return 2
        for name, fn in CASES:
            ok, detail = run_case(name, fn, binary, work, text)
            print("  %-4s  %-4s %s" % ("ok" if ok else "FAIL", name, detail))
            fails += 0 if ok else 1

        # M0: the unmutated source through the SAME path a mutant takes --
        # written out, compiled in its own directory, every case a mutant
        # names run -- must be green, or a kill below proves nothing.
        m0_bin, m0_msg = compile_probe(text, work, "m0")
        m0_bad = []
        if not m0_bin:
            m0_bad.append("does not compile: %s"
                          % " | ".join(m0_msg[-200:].splitlines()))
        else:
            for case in sorted({m[2] for m in MUTANTS}):
                ok, detail = run_case(case, dict(CASES)[case], m0_bin, work, text)
                if not ok:
                    m0_bad.append("%s: %s" % (case, detail))
        print("  %-4s  %-4s %s" % ("ok" if not m0_bad else "FAIL", "M0",
                                   "the unmutated source through the mutation "
                                   "path is green on all %d named cases"
                                   % len({m[2] for m in MUTANTS})
                                   if not m0_bad else "; ".join(m0_bad)))
        if m0_bad:
            fails += 1
            print("REFUSED: M0 is red, so no kill below would be evidence")
            return 1

        killed = 0
        for mid, what, case, edit, scr in MUTANTS:
            mtext = text if edit is None else text.replace(edit[0], edit[1], 1)
            saved = BOARD
            try:
                if scr is not None:
                    BOARD = scr[1]
                mbin, mmsg = compile_probe(mtext, work, mid)
                if not mbin:
                    verdict, detail = False, "INVALID-MUTANT (does not compile): " \
                        + " | ".join(mmsg[-200:].splitlines())
                else:
                    ok, detail = run_case(case, dict(CASES)[case], mbin, work,
                                          mtext)
                    verdict = not ok
                    detail = ("%s went red: %s" % (case, detail[:160]) if verdict
                              else "SURVIVOR: %s stayed green" % case)
            finally:
                BOARD = saved
            killed += 1 if verdict else 0
            fails += 0 if verdict else 1
            print("  %-4s  %-4s %s -- %s" % ("ok" if verdict else "FAIL", mid,
                                             what, detail))
        print("%d of %d mutants killed, each by the case it names"
              % (killed, len(MUTANTS)))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print("RESULT: %s" % ("green" if not fails else "%d FAIL" % fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
