#!/usr/bin/env python3
"""nic15check -- rtl819x-nic 1.5's pure half, compiled and driven on the host.

WHAT IT CHECKS, AND WHY IT CAN
------------------------------
`R6b-2` put every part of driver 1.5 that DECIDES something into
`config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic-tx.h`, with its inputs
as arguments: the verb parsers, the refusal table, the TX length policy, the
loopback identification and classifier, the sweep's bookkeeping (delta0's
registration, the retry rule, the record key, the map codes, the mark
values), the bytes the `tx` verb writes, the verb dispatcher and both /proc
page formatters.  This tool compiles that header UNCHANGED with the host's
gcc (`-std=gnu89 -Werror`, the kernel's dialect) inside a generated driver
that defines `NIC15_HOST` and the five hooks the header declares, and
asserts, case by case:

  K0  the header compiles as the kernel's dialect, warnings as errors
  K1  each parser accepts its whole list, `sweep ... wire` included
  K2  each parser refuses a fixed malformed list -- no trailing-space case,
      because 1.4's handler strips trailing space before any parser sees it
  K3  the gate table, all 128 states x 7 verbs, equals the refusal table of
      PROPOSAL-R6b-2 section 3 as the review round amended it (a running
      sweep refuses every behaviour verb, `engine on`/ndo_open, a second
      sweep and `swclear`), written out again below in Python
  K4  at `txlen rlxfw`, m_len = F and m_extsize = 1.4's value for F = 0..2,047
      -- and at every value the table does not hold, which is the default arm
  K5  the seven `txlen` values give the (m_len, m_extsize) section 3 names
  K6  every verb's success path returns `count`, every refusal its errno and
      a v15_last record; an unknown verb returns -EINVAL and records nothing;
      `sweep F T P` reaches the sweep as loopback and `... wire` as wire
  K7  a refused behaviour verb leaves the policy alone; an accepted one --
      the same value re-typed included -- sets it and marks it dirty
  K8  the loopback classifier on its boundary cases (REPEAT, DIGIT included)
  K9  the frame bytes the sweep compares against equal, for every offset and
      digit, what `nic_do_tx` writes, re-derived here from 1.4's text
  K10 /proc/rtl819x-nic-tx with every counter at its widest fits under the
      3,900 cap, and the boot defaults print `tx15 txlen rlxfw txoff 2 txrb 0
      dirty 0 p15 1` -- the line R6b-3's first cell predicts
  K11 the map's encoding (one character per pair of lengths, six codes, VOID
      and SKEW their own): chosen codes at chosen lengths, decoded back by a
      decoder written here, nothing else set, and the `mt` counts
  K12 a page over the soft cap ends in `truncated 1` and stops
  K13 the hard bound: with the soft cap out of reach, no byte is stored past
      the size the formatter is given
  K14 the digit state: own digit, the previous frame's (REPEAT), any other
  K15 registration: delta0 only from a RIGHT frame a, and only 0 or 4
  K16 the retry rule: one retry, counted once; FOREIGN twice is VOID, or
      -EPROTO while nothing is registered
  K17 the record key: a sweep under another key -- any of txlen, txoff, txrb,
      mode, probe, txrings -- is refused (-EEXIST) while a record exists
  K18 the mark values (N-SWEEP, N-SWSUM, N-SWEND) and -ENODATA for a sweep
      that scored nothing
  K19 the map code's precedence: VOID, SKEW (never bad), bad a, bad b
  K20 identification: OURS is bytes 6..13 alone; a wrong digit is ours
  K21 the owner's wire bound (nic15_sweep_gate): a wire sweep over more than
      one length is -EPERM at every txlen but vendor, after the table's row;
      loopback is unaffected

M0..M25 then mutate a COPY of the header, one defect each, and require the
case named for it to go red.  M0 is the unmutated copy through the same path:
if it is not green, no kill is counted.  A mutant whose anchor does not occur
exactly once, that does not compile, or that is caught by a different case is
reported as a survivor, never as a kill.  A mutant that CRASHES the harness
fails the case it crashed in, with the reason, and that is a kill only if it
is the named case; the run is not refused (M23 is the control for that).

WHAT IT CANNOT SEE
------------------
The kernel half: the hooks in rtl819x-nic.c that touch the engine, the locks,
the sweep's loop and its waits.  `tools/storeseq.py` reads the built objects
for "default = 1.4" and the bench reads the rest.  The generated driver's
hooks are stubs that apply the same `nic15_set` and `nic15_gate` the kernel
applies; what the kernel does around them is not exercised here.

Needs gcc and nothing else: no toolchain, no $FWRE_WORK, no device.
    nic15check.py [--header PATH] [--keep DIR]
"""
import argparse
import errno
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEADER = os.path.join(ROOT, "config", "rlxfw-src", "linux-2.6.30", "drivers",
                      "net", "rtl819x-nic-tx.h")
CFLAGS = ["-std=gnu89", "-O1", "-Wall", "-Wextra", "-Wno-unused-parameter",
          "-Wdeclaration-after-statement", "-Wstrict-prototypes", "-Werror"]
CAP = 3900
PAGE = 4096

VERBS = ["-", "txlen", "txoff", "txrb", "engine", "sweep", "swshow", "swclear"]
LENS = ["rlxfw", "mlen", "ext", "vendor", "d1", "d2", "d3"]
CLASSES = ["none", "right", "long", "short", "content", "alien", "foreign",
           "skew", "timeout", "failtx", "sent", "void", "repeat", "digit"]
C = {n: i for i, n in enumerate(CLASSES)}
ALPH = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
SWEEPING = 0x40

# --------------------------------------------------------------- the driver
HARNESS = r"""
#include <errno.h>
#include <limits.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
#define NIC15_HOST 1
#include "@HEADER@"

static struct nic15_pol pol;
static unsigned int st;
static int last_v = -1, last_rc;
static int n_ok, n_refused, n_apply, n_sweep, n_show, n_clear, sw_wire;
static u32 sw_from, sw_to, sw_probe, show_l;

static int nic15_apply(int v, int val)
{
	n_apply++;
	return nic15_set(&pol, v, val, st);
}

static int nic15_sweep_run(u32 from, u32 to, u32 probe, int wire)
{
	int rc = nic15_sweep_gate(st, wire, from, to, pol.txlen);

	n_sweep++;
	if (!rc) {
		sw_from = from;
		sw_to = to;
		sw_probe = probe;
		sw_wire = wire;
	}
	return rc;
}

static void nic15_swshow_set(u32 l)
{
	n_show++;
	show_l = l;
}

static int nic15_swclear_run(void)
{
	int rc = nic15_gate(NIC15_V_SWCLEAR, st);

	if (!rc)
		n_clear++;
	return rc;
}

static int nic15_ret(int v, int rc)
{
	last_v = v;
	last_rc = rc;
	if (rc < 0)
		n_refused++;
	else
		n_ok++;
	return rc;
}

static void reset(void)
{
	pol.txlen = NIC15_LEN_RLXFW;
	pol.txoff = 2;
	pol.txrb = 0;
	pol.dirty = 0;
	last_v = -1;
	last_rc = 0;
	n_ok = n_refused = n_apply = n_sweep = n_show = n_clear = 0;
	sw_wire = -1;
	sw_from = sw_to = sw_probe = show_l = 0;
}

static struct nic15_w w[NIC15_TXD];
static u32 q[NIC15_TXD][13];
static u8 qv[NIC15_TXD];
static struct nic15_sum sum;
static struct nic15_rec rec[NIC15_NLEN];
static u8 recd[(NIC15_NLEN + 7) / 8];
static struct nic15_pol vpol;

static void put(u32 l, int ca, int cb, u32 pha, u32 phb, u32 x)
{
	u32 i = l - NIC15_LMIN;

	rec[i].ph_a = (u16)pha;
	rec[i].ph_b = (u16)phb;
	rec[i].cls = (u8)((ca << 4) | cb);
	rec[i].extra = (u8)x;
	recd[i >> 3] |= 0x80 >> (i & 7);
}

static void scenario(const char *name, struct nic15_view *v)
{
	u32 i, k;

	memset(v, 0, sizeof(*v));
	memset(w, 0, sizeof(w));
	memset(q, 0, sizeof(q));
	memset(qv, 0, sizeof(qv));
	memset(&sum, 0, sizeof(sum));
	memset(rec, 0, sizeof(rec));
	memset(recd, 0, sizeof(recd));
	vpol.txlen = NIC15_LEN_RLXFW;
	vpol.txoff = 2;
	vpol.txrb = 0;
	vpol.dirty = 0;
	v->version = "rtl819x-nic 1.5";
	v->pol = &vpol;
	v->p15 = 1;
	v->allocated = 1;
	v->w = w;
	v->q = q;
	v->qv = qv;
	v->sw = &sum;
	v->rec = rec;
	v->recd = recd;
	v->show = 60;
	for (i = 0; i < NIC15_TXD; i++)
		for (k = 0; k < 13; k++)
			v->r[i][k] = 0xA15C8000u + 4 * (13 * i + k);
	if (!strcmp(name, "default"))
		return;
	if (!strcmp(name, "worst")) {
		vpol.txlen = NIC15_LEN_VENDOR;
		vpol.txoff = INT_MIN;
		vpol.txrb = INT_MIN;
		vpol.dirty = INT_MIN;
		v->p15 = INT_MIN;
		v->last_v = NIC15_V_SWCLEAR;
		v->last_rc = INT_MIN;
		v->n_ok = v->n_refused = v->n_txq = v->n_arm15 = 0xFFFFFFFFu;
		for (i = 0; i < NIC15_TXD; i++) {
			w[i].f = w[i].n = 0xFFFFFFFFu;
			w[i].pol = NIC15_LEN_VENDOR;
			w[i].off = w[i].rb = 255;
			w[i].path = 1;
			qv[i] = 0xF;
			for (k = 0; k < 13; k++)
				q[i][k] = 0xFFFFFFFFu;
		}
		v->rb_chk = v->rb_bad = v->rb_n = v->rb_i = v->rb_w = 0xFFFFFFFFu;
		v->rb_got = v->rb_want = 0xFFFFFFFFu;
		sum.state = NIC15_SW_NEVER;
		sum.rc = INT_MIN;
		sum.wire = 1;
		sum.from = sum.to = sum.probe = sum.bufs = 0xFFFFFFFFu;
		sum.reg = INT_MIN;
		sum.delta0 = INT_MIN;
		sum.noreg_cls = NIC15_C_CONTENT;
		sum.noreg_ph = 0xFFFFFFFFu;
		sum.noreg_delta = INT_MIN;
		sum.units = sum.scored = sum.voids = sum.skews = 0xFFFF;
		sum.retries = sum.foreign = sum.alien = 0xFFFF;
		sum.timeouts = sum.cycles = sum.bad_a = sum.bad_b = 0xFFFF;
		sum.drained = sum.j0 = sum.j1 = 0xFFFFFFFFu;
		sum.last_l = 0xFFFFFFFFu;
		sum.last.ph_a = sum.last.ph_b = 0xFFFF;
		sum.last.cls = 0xFF;
		sum.last.extra = 0xFF;
		sum.key.txlen = NIC15_LEN_VENDOR;
		sum.key.txoff = sum.key.txrb = INT_MIN;
		sum.key.wire = 1;
		sum.key.probe = sum.key.rings = sum.n_rec = 0xFFFFFFFFu;
		/* Below 1,000 every length is clean, so the histogram's first
		 * and last lengths all have four digits; from 1,000 on every
		 * length is bad-b with one of 17 five-digit ph_b values -- 16
		 * bins and an `other`.  The window sits in that range, where
		 * every entry is five digits, two classes and extra 255. */
		for (i = NIC15_LMIN; i <= NIC15_LMAX; i++) {
			if (i < 1000)
				put(i, NIC15_C_RIGHT, NIC15_C_RIGHT, 65535,
				    65535, 255);
			else
				put(i, NIC15_C_RIGHT, NIC15_C_CONTENT, 65535,
				    65535 - (i - 1000) % 17, 255);
		}
		v->show = NIC15_LMAX - 31;
		return;
	}
	if (!strcmp(name, "map")) {
		put(60, NIC15_C_RIGHT, NIC15_C_RIGHT, 64, 64, 0);
		put(61, NIC15_C_RIGHT, NIC15_C_LONG, 65, 9831, 4);
		put(62, NIC15_C_ALIEN, NIC15_C_NONE, 9831, 0, 3);
		put(63, NIC15_C_VOID, NIC15_C_VOID, 0, 0, 0);
		put(64, NIC15_C_SKEW, NIC15_C_NONE, 0, 0, 0);
		put(65, NIC15_C_RIGHT, NIC15_C_SKEW, 69, 0, 0);
		put(66, NIC15_C_RIGHT, NIC15_C_REPEAT, 70, 70, 0);
		put(67, NIC15_C_RIGHT, NIC15_C_DIGIT, 71, 71, 0);
		put(187, NIC15_C_RIGHT, NIC15_C_TIMEOUT, 191, 0, 0);
		put(188, NIC15_C_REPEAT, NIC15_C_NONE, 0, 0, 0);
		put(1511, NIC15_C_SENT, NIC15_C_SENT, 0, 0, 0);
		put(1514, NIC15_C_RIGHT, NIC15_C_ALIEN, 1518, 3663, 1);
		v->show = 1500;
		return;
	}
	fprintf(stderr, "no scenario %s\n", name);
	exit(3);
}

static char pagebuf[PAGE_ALLOC];

int main(void)
{
	char line[512];

	reset();
	while (fgets(line, sizeof(line), stdin)) {
		char *a;
		size_t n = strlen(line);

		if (n && line[n - 1] == '\n')
			line[--n] = '\0';
		a = (n > 2) ? line + 3 : line + n;
		if (!strncmp(line, "PT", 2)) {
			printf("PT %d\n", nic15_parse_txlen(a));
		} else if (!strncmp(line, "PO", 2)) {
			printf("PO %d\n", nic15_parse_txoff(a));
		} else if (!strncmp(line, "PR", 2)) {
			printf("PR %d\n", nic15_parse_txrb(a));
		} else if (!strncmp(line, "PS", 2)) {
			u32 f = 0, t = 0, p = 0;
			int wr = -1;
			int rc = nic15_parse_sweep(a, &f, &t, &p, &wr);

			printf("PS %d %u %u %u %d\n", rc, f, t, p, wr);
		} else if (!strncmp(line, "PW", 2)) {
			u32 l = 0;
			int rc = nic15_parse_swshow(a, &l);

			printf("PW %d %u\n", rc, l);
		} else if (!strcmp(line, "G")) {
			int v;
			unsigned int s;

			for (v = NIC15_V_TXLEN; v < NIC15_V_N; v++)
				for (s = 0; s <= NIC15_S_ALL; s++)
					printf("G %d %u %d\n", v, s,
					       nic15_gate(v, s));
		} else if (line[0] == 'L') {
			unsigned long f, e;
			int p;

			sscanf(line + 2, "%lu %d %lu", &f, &p, &e);
			printf("L %u %u\n", nic15_mlen((u32)f, p),
			       nic15_ext((u32)f, p, (u32)e));
		} else if (!strcmp(line, "R")) {
			reset();
		} else if (line[0] == 'D') {
			unsigned long count;
			int off = 0, r;

			sscanf(line + 2, "%u %lu %n", &st, &count, &off);
			r = nic15_write(line + 2 + off, count);
			printf("D %d %d %d %d %d %d %d %d %d %d %d %d %u %u %u %u %d %d\n",
			       r, last_v, last_rc, n_ok, n_refused, pol.txlen,
			       pol.txoff, pol.txrb, pol.dirty, n_apply, n_sweep,
			       n_show, sw_from, sw_to, sw_probe, show_l, sw_wire,
			       n_clear);
		} else if (line[0] == 'S') {
			struct nic15_pol p;
			int v, val, rc;
			unsigned int s;

			sscanf(line + 2, "%d %d %u %d %d %d %d", &v, &val, &s,
			       &p.txlen, &p.txoff, &p.txrb, &p.dirty);
			rc = nic15_set(&p, v, val, s);
			printf("S %d %d %d %d %d\n", rc, p.txlen, p.txoff, p.txrb,
			       p.dirty);
		} else if (line[0] == 'C') {
			int s, ours, dig, ok;
			long d, d0;
			unsigned long ph;

			sscanf(line + 2, "%d %d %d %d %ld %ld %lu", &s, &ours,
			       &dig, &ok, &d, &d0, &ph);
			printf("C %d\n", nic15_classify(s, ours, dig, ok, d, d0,
							(u32)ph));
		} else if (line[0] == 'Q') {
			unsigned int g, dg, pv;

			sscanf(line + 2, "%u %u %u", &g, &dg, &pv);
			printf("Q %d\n", nic15_digit_state((u8)g, dg, pv));
		} else if (line[0] == 'I') {
			unsigned int b[9], dg, pv, k;
			u8 id[9];
			int dig = -1, ours;

			sscanf(line + 2, "%x %x %x %x %x %x %x %x %x %u %u",
			       &b[0], &b[1], &b[2], &b[3], &b[4], &b[5], &b[6],
			       &b[7], &b[8], &dg, &pv);
			for (k = 0; k < 9; k++)
				id[k] = (u8)b[k];
			ours = nic15_identify(id, dg, pv, &dig);
			printf("I %d %d\n", ours, ours ? dig : -1);
		} else if (line[0] == 'W') {
			unsigned int s, f, t;
			int wr, tl;

			sscanf(line + 2, "%u %d %u %u %d", &s, &wr, &f, &t, &tl);
			printf("W %d\n", nic15_sweep_gate(s, wr, f, t, tl));
		} else if (line[0] == 'E') {
			int cls;
			long d;

			sscanf(line + 2, "%d %ld", &cls, &d);
			printf("E %d\n", nic15_register(cls, d));
		} else if (line[0] == 'A') {
			int t, f, g;

			sscanf(line + 2, "%d %d %d", &t, &f, &g);
			printf("A %d\n", nic15_try_act(t, f, g));
		} else if (line[0] == 'K') {
			struct nic15_key h, k2;
			unsigned int nr;

			sscanf(line + 2, "%u %d %d %d %d %u %u %d %d %d %d %u %u",
			       &nr, &h.txlen, &h.txoff, &h.txrb, &h.wire,
			       &h.probe, &h.rings, &k2.txlen, &k2.txoff,
			       &k2.txrb, &k2.wire, &k2.probe, &k2.rings);
			printf("K %d\n", nic15_keycheck(&h, nr, &k2));
		} else if (line[0] == 'V') {
			char kind;
			long x, y, z;

			sscanf(line + 2, "%c %ld %ld %ld", &kind, &x, &y, &z);
			if (kind == 'b')
				printf("V %08X\n", nic15_swbegin_val((int)x,
					(u32)y, (u32)z));
			else if (kind == 's')
				printf("V %08X\n", nic15_swsum_val((u32)x,
								   (u32)y));
			else if (kind == 'e')
				printf("V %08X\n", nic15_swend_val((int)x,
					(u32)y, (u32)z));
			else
				printf("V %d\n", nic15_sweep_rc((int)x, (u32)y));
		} else if (line[0] == 'M') {
			struct nic15_rec r;
			int ca, cb, rd;

			sscanf(line + 2, "%d %d %d", &ca, &cb, &rd);
			memset(&r, 0, sizeof(r));
			r.cls = (u8)((ca << 4) | cb);
			printf("M %d\n", nic15_code(&r, rd));
		} else if (!strcmp(line, "B")) {
			u32 dg, j;

			for (dg = 0; dg < 10; dg++) {
				printf("B %u ", dg);
				for (j = 0; j < 1514; j++)
					printf("%02X", nic15_txbyte(j, dg));
				printf("\n");
			}
		} else if (line[0] == 'F') {
			char name[32];
			int size, cap, len;
			struct nic15_view v;

			sscanf(line + 2, "%31s %d %d", name, &size, &cap);
			scenario(name, &v);
			memset(pagebuf, 0x5A, sizeof(pagebuf));
			len = nic15_format(pagebuf, size, cap, &v);
			printf("F %d %d\n<<<\n", len, (int)strlen(pagebuf));
			fwrite(pagebuf, 1, len, stdout);
			printf(">>>\n");
			printf("FC %d\n", pagebuf[size] == 0x5A &&
			       pagebuf[sizeof(pagebuf) - 1] == 0x5A);
		} else {
			printf("? %s\n", line);
		}
		fflush(stdout);
	}
	return 0;
}
"""


class Refused(Exception):
    pass


class Crashed(Exception):
    pass


def build(header, work):
    """Compile the generated driver against `header`.  -> (path, errtext)."""
    src = os.path.join(work, "harness.c")
    exe = os.path.join(work, "harness")
    text = HARNESS.replace("@HEADER@", header).replace(
        "PAGE_ALLOC", str(PAGE + 64))
    with open(src, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    p = subprocess.run(["gcc"] + CFLAGS + ["-o", exe, src],
                       capture_output=True, encoding="utf-8")
    if p.returncode != 0:
        return None, p.stderr.strip() or ("gcc exit %d" % p.returncode)
    return exe, ""


def drive(exe, lines):
    p = subprocess.run([exe], input="\n".join(lines) + "\n",
                       capture_output=True, encoding="utf-8",
                       errors="replace", timeout=60)
    if p.returncode != 0:
        raise Crashed("the harness exited %d%s" % (
            p.returncode, (": " + p.stderr.strip()[:120]) if p.stderr.strip()
            else ""))
    return p.stdout.split("\n")


def page(exe, scen, size=PAGE, cap=CAP):
    out = drive(exe, ["F %s %d %d" % (scen, size, cap)])
    head = out[0].split()
    ln = int(head[1])
    body = "\n".join(out[2:])
    text = body[:body.rindex(">>>")]
    canary = [x for x in out if x.startswith("FC ")][0].split()[1] == "1"
    return ln, int(head[2]), text, canary


def first(bad):
    return "; first wrong %r" % (bad[0],) if bad else ""


# ------------------------------------------------------------ expectations
def expect_gate(v, s):
    eng, up, dirty = s & 1, s & 2, s & 4
    unl, alloc, armed, sweeping = s & 8, s & 16, s & 32, s & SWEEPING
    name = VERBS[v]
    if name in ("txlen", "txoff", "txrb"):
        return -errno.EBUSY if (eng or up or sweeping) else 0
    if name == "engine":
        if sweeping:
            return -errno.EBUSY
        return -errno.ESTALE if dirty else 0
    if name == "sweep":
        if sweeping or up:
            return -errno.EBUSY
        if not unl:
            return -errno.EPERM
        if not (alloc and armed):
            return -errno.ENXIO
        return 0
    if name == "swclear":
        return -errno.EBUSY if sweeping else 0
    return 0


def expect_byte(j, digit):
    """nic_do_tx (1.4 :2226-2244), re-derived here from its text."""
    head = [0xFF] * 6 + [0x02, 0x52, 0x4C, 0x58, 0x46, 0x57, 0x88, 0xB5]
    if j < 14:
        return head[j]
    k = j - 14
    if k < 10:
        return b"RLXFW-NIC "[k]
    if k == 10:
        return 0x30 + digit
    return 0x40 + (k & 0x3F)


def expect_code(ca, cb, rec):
    """The map code, written again: VOID, SKEW (never bad), bad a, bad b."""
    good = {C["none"], C["right"], C["sent"], C["void"], C["skew"]}
    if not rec:
        return 0
    if ca == C["void"]:
        return 4
    if C["skew"] in (ca, cb):
        return 5
    if ca not in good:
        return 3
    if cb not in good:
        return 2
    return 1


def decode_map(text):
    """{L: code} from the m00..m11 lines: one character per pair of lengths,
    index = 6 x first + second in ALPH.  Written apart from the C."""
    codes, seen = {}, set()
    for line in text.split("\n"):
        m = re.fullmatch(r"m(\d\d) ([0-9A-Z]{64})", line)
        if not m:
            continue
        k = int(m.group(1))
        seen.add(k)
        for d, ch in enumerate(m.group(2)):
            idx = ALPH.index(ch)
            for b, c in enumerate((idx // 6, idx % 6)):
                ln = 60 + 128 * k + 2 * d + b
                if c:
                    codes[ln] = c   # past 1,514 it must stay absent
    return codes, seen


# ------------------------------------------------------------------ the cases
def k1(exe):
    acc = ([("PT", n, str(i)) for i, n in enumerate(LENS)] +
           [("PO", "2", "2"), ("PO", "0", "0")] +
           [("PR", str(i), str(i)) for i in range(16)] +
           [("PS", "60 1514 60", "0 60 1514 60 0"),
            ("PS", "60 60 0", "0 60 60 0 0"),
            ("PS", "61 61 60", "0 61 61 60 0"),
            ("PS", "1514 1514 1514", "0 1514 1514 1514 0"),
            ("PS", "60 1514 0", "0 60 1514 0 0"),
            ("PS", "277 277 60", "0 277 277 60 0"),
            ("PS", "100 200 1514", "0 100 200 1514 0"),
            ("PS", "61 61 60 wire", "0 61 61 60 1"),
            ("PS", "60 1514 60 wire", "0 60 1514 60 1"),
            ("PS", "277 277 0 wire", "0 277 277 0 1")] +
           [("PW", "60", "0 60"), ("PW", "1514", "0 1514"),
            ("PW", "277", "0 277")])
    out = drive(exe, ["%s %s" % (c, a) for c, a, _ in acc])
    bad = [(c, a, o) for (c, a, w), o in zip(acc, out)
           if o != "%s %s" % (c, w)]
    return not bad, "%d accepted forms%s" % (len(acc), first(bad))


def k2(exe):
    ref = ([("PT", x) for x in ("RLXFW", "", "vendor2", " rlxfw", "d4", "d0",
                                 "Vendor", "rlx fw")] +
           [("PO", x) for x in ("1", "4", "02", "", "2x", "-0", "00")] +
           [("PR", x) for x in ("16", "-1", "01", "1x", "", "0x1", "99999",
                                 "+1")] +
           [("PS", x) for x in ("59 1514 60", "60 1515 60", "100 99 60",
                                 "60 1514 59", "60 1514 1515", "60 1514",
                                 "60 1514 60 1", "60  1514 60", "0x3c 100 0",
                                 "060 100 0", " 60 100 0", "", "60 100 00",
                                 "60 100 -1", "60 10000 0",
                                 "60 1514 60 wir", "60 1514 60 wirex",
                                 "60 1514 60 wire x", "60 1514 60 WIRE",
                                 "60 1514 60  wire", "60 1514 60wire",
                                 "60 1514 wire", "wire 60 1514 60",
                                 "60 1514 60 loop", "60 1514 60 wire wire")] +
           [("PW", x) for x in ("59", "1515", "", "0060", "6o", "-60")])
    out = drive(exe, ["%s %s" % (c, a) for c, a in ref])
    bad = [(c, a, o) for (c, a), o in zip(ref, out)
           if o.split()[1] != str(-errno.EINVAL)]
    return not bad, "%d malformed forms refused -EINVAL%s" % (len(ref),
                                                              first(bad))


def k3(exe):
    out = [x for x in drive(exe, ["G"]) if x.startswith("G ")]
    got = {(int(v), int(s)): int(r) for _, v, s, r in (x.split() for x in out)}
    nv = len(VERBS) - 1
    want = {(v, s): expect_gate(v, s) for v in range(1, nv + 1)
            for s in range(128)}
    diff = sorted(k for k in want if got.get(k) != want[k])
    permits = {VERBS[v]: sum(1 for s in range(128) if want[(v, s)] == 0)
               for v in range(1, nv + 1)}
    return (len(got) == 128 * nv and not diff,
            "%d cells; permits %s%s" % (
                128 * nv, " ".join("%s %d" % kv for kv in permits.items()),
                "; first wrong (verb %s, state %02X): got %s want %s" % (
                    VERBS[diff[0][0]], diff[0][1], got.get(diff[0]),
                    want[diff[0]]) if diff else ""))


def k4(exe):
    lines = ["L %d %d %d" % (f, p, e) for f in range(2048)
             for p in (0, -1, 7, 100) for e in (2046,)]
    lines += ["L %d 0 %d" % (f, e) for f in (0, 60, 2047) for e in (0, 65535)]
    out = drive(exe, lines)
    bad = []
    for ln, o in zip(lines, out):
        f, _p, e = map(int, ln.split()[1:])
        if o != "L %d %d" % (f, e):
            bad.append((ln, o))
    return not bad, "%d (F, pol, ext14) points give (F, ext14)%s" % (
        len(lines), first(bad))


def k5(exe):
    tab = {"rlxfw": (0, 0), "mlen": (4, None), "ext": (0, 4),
           "vendor": (4, 4), "d1": (3, None), "d2": (2, None),
           "d3": (1, None)}
    lines, wants = [], []
    for i, n in enumerate(LENS):
        for f in (60, 61, 1514):
            ml, ex = tab[n]
            lines.append("L %d %d 2046" % (f, i))
            wants.append("L %d %d" % (f + ml, 2046 if ex is None or n == "rlxfw"
                                       else f + ex))
    out = drive(exe, lines)
    bad = [(ln, o, w) for ln, o, w in zip(lines, out, wants) if o != w]
    return not bad, "7 values x 3 lengths%s" % first(bad)


def k6(exe):
    ok = 8 | 16 | 32          # unlocked, allocated, armed; off; down; no sweep
    E = errno
    script = [
        ("R", None),
        # the owner's bound, through the dispatcher: at rlxfw (the reset
        # policy) a wire sweep over 1,455 lengths is refused, one length is
        # not, loopback is not; at vendor the full wire sweep is permitted
        ("D %d 19 sweep 60 1514 60 wire" % ok, (-E.EPERM, 5, -E.EPERM)),
        ("D %d 18 sweep 61 61 60 wire" % ok, (18, 5, 18)),
        ("D %d 14 sweep 60 1514 60" % ok, (14, 5, 14)),
        ("D %d 13 txlen vendor" % ok, (13, 1, 13)),
        ("D %d 19 sweep 60 1514 60 wire" % ok, (19, 5, 19)),
        ("D %d 8 txoff 0" % ok, (8, 2, 8)),
        ("D %d 7 txrb 5" % ok, (7, 3, 7)),
        ("D %d 14 sweep 60 60 0" % ok, (14, 5, 14)),
        ("D %d 19 sweep 61 61 60 wire" % ok, (19, 5, 19)),
        ("D %d 11 swshow 277" % ok, (11, 6, 11)),
        ("D %d 7 swclear" % ok, (7, 7, 7)),
        ("D %d 12 txlen RLXFW" % ok, (-E.EINVAL, 1, -E.EINVAL)),
        ("D %d 6 txlen" % ok, (-E.EINVAL, 1, -E.EINVAL)),
        ("D %d 12 txlen vendor" % (ok | 1), (-E.EBUSY, 1, -E.EBUSY)),
        ("D %d 12 txlen vendor" % (ok | 2), (-E.EBUSY, 1, -E.EBUSY)),
        ("D %d 12 txlen vendor" % (ok | SWEEPING), (-E.EBUSY, 1, -E.EBUSY)),
        ("D %d 14 sweep 60 60 0" % (ok | 2), (-E.EBUSY, 5, -E.EBUSY)),
        ("D %d 14 sweep 60 60 0" % (ok | SWEEPING), (-E.EBUSY, 5, -E.EBUSY)),
        ("D %d 14 sweep 60 60 0" % (16 | 32), (-E.EPERM, 5, -E.EPERM)),
        ("D %d 14 sweep 60 60 0" % (8 | 16), (-E.ENXIO, 5, -E.ENXIO)),
        ("D %d 17 sweep 59 1514 60" % ok, (-E.EINVAL, 5, -E.EINVAL)),
        ("D %d 19 sweep 60 60 0 wirex" % ok, (-E.EINVAL, 5, -E.EINVAL)),
        ("D %d 11 swshow 1515" % ok, (-E.EINVAL, 6, -E.EINVAL)),
        ("D %d 7 swclear" % (ok | SWEEPING), (-E.EBUSY, 7, -E.EBUSY)),
        ("D %d 11 swclear now" % ok, (-E.EINVAL, 7, -E.EINVAL)),
        ("D %d 5 bogus" % ok, (-E.EINVAL, 7, -E.EINVAL)),
        ("D %d 12 txlenx vendor" % ok, (-E.EINVAL, 7, -E.EINVAL)),
    ]
    out = iter(x for x in drive(exe, [s for s, _ in script])
               if x.startswith("D "))
    bad, rows = [], []
    for cmd, want in script:
        if want is None:
            continue
        f = next(out).split()
        rows.append(f)
        got = (int(f[1]), int(f[2]), int(f[3]))
        if got != want:
            bad.append((cmd, got, want))
    last = rows[-1]
    # 10 accepted; 15 refusals recorded; the two unknown verbs record nothing
    tail_ok = int(last[4]) == 10 and int(last[5]) == 15
    # what reached the sweep hook: (from, to, probe, wire) after each sweep
    hook = [tuple(r[13:16]) + (r[17],) for r in rows]
    modes_ok = (hook[1] == ("61", "61", "60", "1") and
                hook[2] == ("60", "1514", "60", "0") and
                hook[4] == ("60", "1514", "60", "1") and
                hook[7] == ("60", "60", "0", "0") and
                hook[8] == ("61", "61", "60", "1"))
    return (not bad and tail_ok and modes_ok,
            "%d writes: every accepted verb returned count, every refusal its "
            "errno; at rlxfw `60 1514 60 wire` -EPERM, `61 61 60 wire` and "
            "loopback permitted, at vendor `60 1514 60 wire` permitted%s%s%s" % (
                len(script) - 1, first(bad),
                "" if tail_ok else "; counters %r" % (last[4:6],),
                "" if modes_ok else "; the hook saw %r" % (hook[:9],)))


def k7(exe):
    E = -errno.EBUSY
    sl = [("S 1 3 0 0 2 0 0", "S 0 3 2 0 1"),        # accepted: set, dirty
          ("S 1 0 0 0 2 0 0", "S 0 0 2 0 1"),        # same value: dirty
          ("S 2 0 0 0 2 0 0", "S 0 0 0 0 1"),
          ("S 3 15 0 0 2 0 0", "S 0 0 2 15 1"),
          ("S 1 3 1 0 2 0 0", "S %d 0 2 0 0" % E),   # engine on: untouched
          ("S 3 5 2 0 2 0 0", "S %d 0 2 0 0" % E),   # rlx0 up: untouched
          ("S 2 0 64 0 2 0 0", "S %d 0 2 0 0" % E),  # a sweep: untouched
          ("S 4 1 0 0 2 0 0", "S %d 0 2 0 0" % -errno.EINVAL)]
    out = drive(exe, [a for a, _ in sl])
    bad = [(a, o, w) for (a, w), o in zip(sl, out) if o != w]
    return not bad, "%d set() cases%s" % (len(sl), first(bad))


def k8(exe):
    cl = [((0, 1, 0, 1, 0, 0, 64), "right"), ((0, 1, 0, 0, 0, 0, 64), "content"),
          ((0, 1, 0, 1, 4, 0, 68), "long"), ((0, 1, 0, 1, -1, 0, 63), "short"),
          ((0, 1, 0, 1, 4, 4, 68), "right"), ((0, 1, 0, 1, 0, 4, 64), "short"),
          ((0, 0, 0, 0, 0, 0, 63), "alien"), ((0, 0, 0, 0, 0, 0, 64), "foreign"),
          ((0, 0, 0, 0, 0, 0, 1522), "foreign"), ((0, 0, 0, 0, 0, 0, 1523),
                                                  "alien"),
          ((0, 0, 0, 0, 0, 0, 9831), "alien"), ((0, 0, 0, 1, 0, 0, 100),
                                                "foreign"),
          ((0, 1, 1, 1, 0, 0, 64), "repeat"), ((0, 1, 2, 1, 0, 0, 64), "digit"),
          ((0, 1, 1, 0, 4, 0, 68), "repeat"), ((0, 1, 2, 1, -4, 0, 60), "digit"),
          ((0, 0, 1, 1, 0, 0, 64), "foreign"), ((0, 0, 2, 0, 0, 0, 40), "alien"),
          ((C["timeout"], 1, 0, 1, 0, 0, 64), "timeout"),
          ((C["timeout"], 1, 1, 1, 0, 0, 64), "timeout"),
          ((C["skew"], 0, 0, 0, 0, 0, 0), "skew"),
          ((C["failtx"], 0, 0, 0, 0, 0, 0), "failtx")]
    out = drive(exe, ["C %d %d %d %d %d %d %d" % a for a, _ in cl])
    bad = [(a, o, w) for (a, w), o in zip(cl, out) if o != "C %d" % C[w]]
    return not bad, "%d classifier cases%s" % (len(cl), first(bad))


def k9(exe):
    out = [x for x in drive(exe, ["B"]) if x.startswith("B ")]
    bad = []
    for x in out:
        _, dg, hx = x.split()
        dg = int(dg)
        got = bytes.fromhex(hx)
        want = bytes(expect_byte(j, dg) for j in range(1514))
        if got != want:
            j = next(i for i in range(1514) if got[i] != want[i])
            bad.append((dg, j, got[j], want[j]))
    return len(out) == 10 and not bad, "1,514 offsets x 10 digits%s" % (
        "; first wrong (digit, j, got, want) %r" % (bad[0],) if bad else "")


def k10(exe):
    # The scenario puts every counter at its type's maximum and every int
    # at INT_MIN; the one block it cannot drive to its domain bound is the
    # histogram (16 bins cannot all count past 999 over 1,455 lengths), so
    # that block is charged at its bound: 4 lines x ("hb" + 4 x
    # " 65535:1455:1514-1514" + newline) = 348.
    ln, sl_, text, canary = page(exe, "worst")
    rows_ = [x for x in text.split("\n") if x]
    longest = max(len(x) + 1 for x in rows_)
    hb = sum(len(x) + 1 for x in rows_ if x.startswith("hb ") and ":" in x)
    bound = ln - hb + 4 * (2 + 4 * 21 + 1)
    ok = (bound <= CAP and "truncated" not in text and ln == sl_ and
          len(text) == ln and canary and
          sum(1 for x in rows_ if x.startswith("hb ") and ":" in x) == 4)
    _, _, dtext, _ = page(exe, "default")
    dline = dtext.split("\n")[1] if dtext.count("\n") > 1 else ""
    want_line = "tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1"
    return (ok and dline == want_line,
            "worst case %d, %d with the histogram at its bound, of %d (cap); "
            "longest line %d; default %r%s"
            % (ln, bound, CAP, longest, dline, "" if dline == want_line else
               " != %r" % want_line))


def k11(exe):
    _, _, mtext, _ = page(exe, "map")
    codes, seen = decode_map(mtext)
    want = {60: 1, 61: 2, 62: 3, 63: 4, 64: 5, 65: 5, 66: 2, 67: 2,
            187: 2, 188: 3, 1511: 1, 1514: 2}
    mt = [x for x in mtext.split("\n") if x.startswith("mt ")]
    mt_want = "mt none %d clean 2 bad_b 5 bad_a 2 void 1 skew 2" % (1455 - 12)
    hbv = [x for x in mtext.split("\n") if x.startswith("hb n ")]
    ok = (codes == want and seen == set(range(12)) and mt == [mt_want] and
          hbv and hbv[0].endswith(" void 1"))
    return ok, "12 lines; codes %s; %s%s" % (
        "as planted" if codes == want else "%r != %r" % (codes, want),
        mt[0] if mt else "no mt line",
        "" if mt == [mt_want] else " != %r" % mt_want)


def k12(exe):
    _, _, wtext, _ = page(exe, "worst")
    longest = max(len(x) + 1 for x in wtext.split("\n") if x)
    ln, _, ttext, _ = page(exe, "worst", PAGE, 1000)
    lines = ttext.split("\n")
    ok = (lines[-2:] == ["truncated 1", ""] and 1000 < ln <= 1000 + longest + 12
          and ttext.count("truncated") == 1)
    return ok, "cap 1000: %d bytes, ends %r" % (ln, lines[-2:-1])


def k13(exe):
    ln, sl_, htext, canary = page(exe, "worst", 700, 100000)
    return (ln <= 699 and sl_ == ln and canary,
            "size 700, cap out of reach: %d bytes, canary %s"
            % (ln, "intact" if canary else "OVERWRITTEN"))


def k14(exe):
    lines, wants = [], []
    for dg in range(10):
        pv = (dg + 9) % 10
        for g in range(256):
            lines.append("Q %d %d %d" % (g, dg, pv))
            wants.append("Q %d" % (0 if g == 0x30 + dg else
                                   1 if g == 0x30 + pv else 2))
    out = drive(exe, lines)
    bad = [(ln, o, w) for ln, o, w in zip(lines, out, wants) if o != w]
    return not bad, "%d (byte, digit) points%s" % (len(lines), first(bad))


def k15(exe):
    lines, wants = [], []
    for cls in range(len(CLASSES)):
        for d in (-4, -1, 0, 1, 3, 4, 5, 8):
            lines.append("E %d %d" % (cls, d))
            wants.append("E %d" % (0 if cls == C["right"] and d in (0, 4)
                                   else -errno.EPROTO))
    out = drive(exe, lines)
    bad = [(ln, o, w) for ln, o, w in zip(lines, out, wants) if o != w]
    return not bad, "%d (class, delta0) points; only RIGHT at 0 or 4 " \
                    "registers%s" % (len(lines), first(bad))


def k16(exe):
    want = {(0, 0, 0): 0, (0, 0, 1): 0, (1, 0, 0): 0, (1, 0, 1): 0,
            (0, 1, 0): 1, (0, 1, 1): 1, (1, 1, 1): 2, (1, 1, 0): 3}
    keys = sorted(want)
    out = drive(exe, ["A %d %d %d" % k for k in keys])
    bad = [(k, o) for k, o in zip(keys, out) if o != "A %d" % want[k]]
    return not bad, "8 (tries, foreign, registered) cases: one retry, then " \
                    "VOID, or NOREG unregistered%s" % first(bad)


def k17(exe):
    base = [3, 2, 0, 0, 60, 1]            # txlen txoff txrb wire probe rings
    cases = [(0, base, [0, 0, 0, 1, 0, 4], 0),       # no record: any key
             (5, base, base, 0)]                     # same key: permitted
    for i in range(6):
        other = list(base)
        other[i] += 1
        cases.append((5, base, other, -errno.EEXIST))
    out = drive(exe, ["K %d %s %s" % (n, " ".join(map(str, h)),
                                      " ".join(map(str, w)))
                      for n, h, w, _ in cases])
    bad = [(c, o) for c, o in zip(cases, out) if o != "K %d" % c[3]]
    return not bad, "%d key cases; each of the six fields refuses alone%s" % (
        len(cases), first(bad))


def k18(exe):
    E = errno
    cases = [("V b 0 60 1514", "V 4C03C5EA"), ("V b 1 277 277", "V 57115115"),
             ("V b 1 60 60", "V 5703C03C"),
             ("V s 1455 0", "V 05AF0000"), ("V s 0 3", "V 00000003"),
             ("V s 728 2", "V 02D80002"),
             ("V e 0 0 728", "V 000002D8"), ("V e 0 1 2", "V 00010002"),
             ("V e 0 0 0", "V 00000000"),
             ("V e -145 1 2", "V FFFFFF6F"), ("V e -71 0 0", "V FFFFFFB9"),
             ("V e -61 0 0", "V FFFFFFC3"), ("V e -4 0 0", "V FFFFFFFC"),
             ("V e -17 0 0", "V FFFFFFEF"),
             ("V r 0 0", "V %d" % -E.ENODATA), ("V r 0 5", "V 0"),
             ("V r -4 0", "V -4"), ("V r -145 7", "V -145")]
    out = drive(exe, [c for c, _ in cases])
    bad = [(c, o, w) for (c, w), o in zip(cases, out) if o != w]
    return not bad, "%d mark and end values%s" % (len(cases), first(bad))


def k19(exe):
    cases = []
    for ca in range(len(CLASSES)):
        for cb in range(len(CLASSES)):
            for rd in (0, 1):
                cases.append((ca, cb, rd))
    out = drive(exe, ["M %d %d %d" % c for c in cases])
    bad = [(c, o) for c, o in zip(cases, out)
           if o != "M %d" % expect_code(*c)]
    return not bad, "%d (a, b, recorded) points%s" % (len(cases), first(bad))


def k20(exe):
    own = [expect_byte(6 + k, 3) for k in range(8)]
    cases = []
    for g, want in ((0x33, "I 1 0"), (0x32, "I 1 1"), (0x78, "I 1 2")):
        cases.append((own + [g], want))
    for k in range(8):                       # any byte of 6..13 changed
        b = list(own)
        b[k] ^= 0x01
        cases.append((b + [0x33], "I 0 -1"))
    out = drive(exe, ["I %s 3 2" % " ".join("%02X" % x for x in b)
                      for b, _ in cases])
    bad = [(b, o, w) for (b, w), o in zip(cases, out) if o != w]
    return not bad, "%d identifications: OURS by bytes 6..13, the digit " \
                    "only says which%s" % (len(cases), first(bad))


def k21(exe):
    ok = 8 | 16 | 32
    lines, wants = [], []
    for st in (ok, ok | 2, ok | SWEEPING, 16 | 32, 8 | 16):
        gate = expect_gate(VERBS.index("sweep"), st)
        for wire in (0, 1):
            for f, t in ((60, 1514), (61, 61), (1514, 1514), (277, 278)):
                for tl in range(len(LENS)):
                    lines.append("W %d %d %d %d %d" % (st, wire, f, t, tl))
                    if gate:
                        w = gate
                    elif wire and f != t and LENS[tl] != "vendor":
                        w = -errno.EPERM
                    else:
                        w = 0
                    wants.append("W %d" % w)
    out = drive(exe, lines)
    bad = [(ln, o, w) for ln, o, w in zip(lines, out, wants) if o != w]
    return not bad, "%d (state, mode, range, txlen) points: a wire range is " \
                    "-EPERM but at vendor, after the table's row%s" % (
                        len(lines), first(bad))


CASES = [("K1", k1), ("K2", k2), ("K3", k3), ("K4", k4), ("K5", k5),
         ("K6", k6), ("K7", k7), ("K8", k8), ("K9", k9), ("K10", k10),
         ("K11", k11), ("K12", k12), ("K13", k13), ("K14", k14),
         ("K15", k15), ("K16", k16), ("K17", k17), ("K18", k18),
         ("K19", k19), ("K20", k20), ("K21", k21)]


def cases(exe):
    """-> list of (id, ok, note).  Every case runs on its own: a harness that
    crashes fails the case it crashed in, with the reason, and no other."""
    res = []
    for cid, fn in CASES:
        try:
            ok, note = fn(exe)
        except Crashed as e:
            ok, note = False, "CRASHED: %s" % e
        res.append((cid, bool(ok), note))
    return res


# --------------------------------------------------------------- the mutants
MUTANTS = [
    ("M1", "K3", "the gate stops refusing a behaviour verb while rlx0 is up",
     "(st & (NIC15_S_ENGINE | NIC15_S_UP | NIC15_S_SWEEP)) ?",
     "(st & (NIC15_S_ENGINE | NIC15_S_SWEEP)) ?"),
    ("M2", "K4", "the default arm of m_len changes (F becomes F + 4)",
     "\t\treturn f;\n\treturn f + 4 - nic15_len_tab[pol].d;",
     "\t\treturn f + 4;\n\treturn f + 4 - nic15_len_tab[pol].d;"),
    ("M3", "K6", "a success path returns 0 instead of count",
     "return nic15_ret(v, rc ? rc : (int)count);",
     "return nic15_ret(v, rc ? rc : 0);"),
    ("M4", "K2", "the sweep parser accepts a length below 60",
     "if (f < NIC15_LMIN || t > NIC15_LMAX || f > t)",
     "if (f < NIC15_LMIN - 1 || t > NIC15_LMAX || f > t)"),
    ("M5", "K8", "the classifier's jabber bound moves from 1,522 to 1,518",
     "(ph < 64 || ph > 1522)", "(ph < 64 || ph > 1518)"),
    ("M6", "K9", "the filler is indexed by the frame offset, not the payload",
     "return (u8)(0x40 + (k & 0x3F));", "return (u8)(0x40 + (j & 0x3F));"),
    ("M7", "K11", "the map swaps the two lengths of a pair",
     "line[d] = nic15_alph[c[0] * NIC15_M_N + c[1]];",
     "line[d] = nic15_alph[c[1] * NIC15_M_N + c[0]];"),
    ("M8", "K7", "an accepted behaviour verb no longer marks the policy dirty",
     "\tp->dirty = 1;\n\treturn 0;", "\treturn 0;"),
    ("M9", "K12", "the soft cap is never reached",
     "if (pg->len > pg->cap) {", "if (pg->len > pg->cap + 100000) {"),
    ("M10", "K2", "the wire token is matched as a prefix (` wire x` passes)",
     "else if (!strcmp(e, \" wire\"))", "else if (!strncmp(e, \" wire\", 5))"),
    ("M11", "K3", "a behaviour verb is no longer refused while a sweep runs",
     "(st & (NIC15_S_ENGINE | NIC15_S_UP | NIC15_S_SWEEP)) ?",
     "(st & (NIC15_S_ENGINE | NIC15_S_UP)) ?"),
    ("M12", "K3", "engine on / ndo_open is no longer refused during a sweep",
     "\t\tif (st & NIC15_S_SWEEP)\n\t\t\treturn -EBUSY;\n"
     "\t\treturn (st & NIC15_S_DIRTY)",
     "\t\treturn (st & NIC15_S_DIRTY)"),
    ("M13", "K15", "registration accepts delta0 = 8",
     "(delta == 0 || delta == 4) ? 0 : -EPROTO",
     "(delta == 0 || delta == 4 || delta == 8) ? 0 : -EPROTO"),
    ("M14", "K16", "FOREIGN twice before registration VOIDs instead of refusing",
     "return reg ? NIC15_ACT_VOID : NIC15_ACT_NOREG;",
     "return NIC15_ACT_VOID;"),
    ("M15", "K17", "the record key ignores txrings",
     " || have->rings != want->rings)", ")"),
    ("M16", "K18", "N-SWEND's success value is bad b alone",
     "return ((bad_a & 0xFFFF) << 16) | (bad_b & 0xFFFF);",
     "return bad_b & 0xFFFF;"),
    ("M17", "K18", "a sweep that scored nothing ends 0, not -ENODATA",
     "return scored ? 0 : -ENODATA;", "return 0;"),
    ("M18", "K8", "the classifier loses REPEAT (the previous frame's digit reads DIGIT)",
     "\tif (dig == 1)\n\t\treturn NIC15_C_REPEAT;\n", ""),
    ("M19", "K19", "a VOID unit reads as never swept",
     "\t\treturn NIC15_M_VOID;", "\t\treturn NIC15_M_NONE;"),
    ("M20", "K19", "SKEW is no longer its own code",
     "\tif (ca == NIC15_C_SKEW || cb == NIC15_C_SKEW)\n"
     "\t\treturn NIC15_M_SKEW;\n", ""),
    ("M21", "K14", "the previous frame's digit is not recognised",
     "\tif (got == (u8)('0' + prev % 10))\n\t\treturn 1;\n", ""),
    ("M22", "K20", "a wrong digit makes our own frame not ours (FOREIGN)",
     "\t*dig = nic15_digit_state(id[8], digit, prev);\n\treturn 1;",
     "\t*dig = nic15_digit_state(id[8], digit, prev);\n\treturn *dig ? 0 : 1;"),
    ("M24", "K21", "the wire bound loses its vendor exemption",
     "if (wire && from != to && txlen != NIC15_LEN_VENDOR)",
     "if (wire && from != to)"),
    ("M25", "K21", "the wire bound is dropped (a full wire sweep at rlxfw passes)",
     "\tif (wire && from != to && txlen != NIC15_LEN_VENDOR)\n"
     "\t\treturn -EPERM;\n", ""),
    ("M23", "K8", "CONTROL: the harness crashes in the classifier -- a kill "
     "with its reason, not a refused run",
     "\tif (st)\n\t\treturn st;\n\tif (!ours)",
     "\tif (st)\n\t\treturn *(volatile int *)0;\n\tif (!ours)"),
]


def mutate(src, old, new):
    n = src.count(old)
    if n != 1:
        return None, "anchor occurs %d time(s), not once" % n
    return src.replace(old, new), ""


def run_all(header, keep=None):
    if not shutil.which("gcc"):
        raise Refused("no gcc on PATH -- this tool compiles the header with "
                      "the host's gcc and cannot say anything without it")
    if not os.path.isfile(header):
        raise Refused("no header at %s" % header)
    src = open(header, encoding="utf-8").read()
    work = keep or tempfile.mkdtemp(prefix="nic15check-")
    os.makedirs(work, exist_ok=True)
    rows = []
    try:
        exe, err = build(header, work)
        rows.append(("K0", exe is not None,
                     "gcc %s" % " ".join(CFLAGS[:2]) if exe else
                     "does not compile: " + err.splitlines()[0][:150]))
        if exe:
            rows += cases(exe)
        else:
            rows += [(cid, False, "not run: K0 failed") for cid, _ in CASES]
        base_ok = all(ok for _, ok, _ in rows)
        # M0: the unmutated COPY through the mutants' own path
        mdir = os.path.join(work, "m0")
        os.makedirs(mdir, exist_ok=True)
        hp = os.path.join(mdir, "rtl819x-nic-tx.h")
        with open(hp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(src)
        mexe, err = build(hp, mdir)
        m0 = mexe is not None and all(ok for _, ok, _ in cases(mexe))
        rows.append(("M0", m0 and base_ok,
                     "the unmutated copy passes every K case through the "
                     "mutants' path" if m0 else "the unmutated copy is RED: "
                     "no kill below is counted"))
        for mid, target, what, old, new in MUTANTS:
            msrc, why = mutate(src, old, new)
            if msrc is None:
                rows.append((mid, False, "%s -- SURVIVED: %s" % (what, why)))
                continue
            mdir = os.path.join(work, mid.lower())
            os.makedirs(mdir, exist_ok=True)
            hp = os.path.join(mdir, "rtl819x-nic-tx.h")
            with open(hp, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(msrc)
            mexe, err = build(hp, mdir)
            if mexe is None:
                rows.append((mid, False, "%s -- SURVIVED: the mutant does "
                             "not compile" % what))
                continue
            res = cases(mexe)
            red = [cid for cid, ok, _ in res if not ok]
            crash = [note for cid, ok, note in res
                     if cid == target and note.startswith("CRASHED")]
            killed = m0 and target in red
            rows.append((mid, killed, "%s -> %s %s%s" % (
                what, target, "red" if target in red else
                "GREEN (red: %s)" % (", ".join(red) or "none"),
                " (%s)" % crash[0] if crash else "")))
    finally:
        if not keep:
            shutil.rmtree(work, ignore_errors=True)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--header", default=HEADER)
    ap.add_argument("--keep", help="keep the generated files in this directory")
    a = ap.parse_args()
    try:
        rows = run_all(os.path.abspath(a.header), a.keep)
    except Refused as e:
        print("nic15check: REFUSED: %s" % e)
        return 2
    except (OSError, subprocess.SubprocessError) as e:
        print("nic15check: REFUSED: %s: %s" % (type(e).__name__, e))
        return 2
    fails = 0
    for cid, ok, note in rows:
        print("  %-4s %-4s %s" % ("ok" if ok else "FAIL", cid, note))
        fails += 0 if ok else 1
    print("RESULT: %d passed, %d failed (header %s)"
          % (len(rows) - fails, fails, os.path.relpath(a.header, ROOT)
             if a.header.startswith(ROOT) else a.header))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
