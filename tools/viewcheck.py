#!/usr/bin/env python3
"""viewcheck -- rtl819x-view 1.0, compiled and driven on the host.

WHAT IT CHECKS, AND WHY IT CAN
------------------------------
`R6b-8` 8c adds config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-view.c, a
/proc node that only loads: `mib`, `tbl vlan|netif`, `peek A [n]`.  This tool
cuts that file below its includes UNCHANGED and compiles it with the host's
gcc in the kernel's dialect (`-std=gnu89 -Werror`) inside a generated harness
that supplies, in place of the kernel:

  * a sparse MMIO model.  The 298 words the admission table of the 8c
    proposal (section 1.3) admits each have a value and a load counter; the
    192 words of the VLAN table (16 slots) and the netif table (8 slots) may
    be loaded only while a `tbl` write is running; SWTACR reads busy for a
    scripted number of loads and a table slot can be torn for a scripted
    number of tries.  ANY STORE, OR A LOAD OF ANY OTHER ADDRESS, ENDS THE
    HARNESS WITH EXIT 9 -- so "refused before the load" is observable;
  * the kernel's simple_strtoul (lib/vsprintf.c:36-75, no whitespace skipped)
    with this kernel's 32-bit unsigned long, so a long number wraps as it
    does on the device;
  * this arch's errno values (EACCES 13, EBUSY 16 and EINVAL 22 are
    asm-generic/errno-base.h's, which arch/rlx/include/asm/errno.h takes);
  * a `cat` that calls read_proc twice (FW-64).

The model's list of words is written HERE, from the proposal's table, and not
from the driver: two copies of one table, so a word both copies get wrong in
the same way passes (the proposal's R5 says what settles that).

Cases (each prints one `  ok`/`  FAIL` line with exactly two leading spaces):

  V0   the cut compiles as the kernel's dialect, warnings as errors; the errno
       table is this arch's; the cut holds no store accessor; the model's list
       is the proposal's (54 + 225 + 17 + 2 = 298, and the per-window tallies)
  V1   boot: /proc/rtl819x-view byte for byte, no load, no mark
  V2   mib: exactly the 225 addresses, once each, in page order; the offsets
       line is the model's list; every word on the page is the model's value
  V3   `mib` with anything after it: -EINVAL, no load, the cache unchanged
  V4   tbl vlan: 16 x (SWTACR, 8 words, the same 8) in that order, `t1 eq`
       per slot, the header line; nothing stored
  V5   tbl netif: the same over 8 slots at 0xBB040000
  V6   a tear on word 7 for k < 10 tries prints t(k+1) `eq` and the settled
       words; for k >= 10, `t10 mis` and the SECOND buffer; one on word 0 of a
       netif slot
  V7   SWTACR busy past the bound: -EBUSY at the slot it began on, no table
       load after it, `busy` counted, the earlier slots kept; busy for exactly
       the bound: the verb proceeds; udelay 10,000 either way
  V8   `tbl` refusals beside the permitted twin: -EINVAL, no load
  V9   peek permitted on every one of the 298: one load of that word, its
       value on the page
  V10  peek over every word of the four windows (switch 0xBB804000-FFF,
       MIB 0xBB801000-FFF, CPU 0xB8010000-7F, PIN_MUX 0xB8000000-7F) and
       eight more (flash, the boot ROM, KSEG0, two table words, an alias):
       each admitted word loads once, each other one is refused -EACCES with
       no load, counted, named with `psrp` or `out`, the cache unchanged
  V11  a request that spans out of a run: the whole of it refused, no
       partial load, the first refused word named, the cache unchanged
  V12  n = 16 inside one run; n = 17 -EINVAL; 16 across a run's end refused
  V13  `cat` loads nothing, and its two renders are identical
  V14  every verb's page at every field's widest: the comment's four figures
       are the measured ones, nothing is cut, and the page fits 4,096 bytes
  V15  the strict parser: a doubled space, a trailing letter, a leading
       non-digit, an unaligned or out-of-range n, a field over ten characters
       -- -EINVAL with no load -- beside permitted twins, and the 32-bit wrap
       the driver's comment names, shown
  V16  the /proc entry failing at init marks VW0-NOPROC and nothing else

M0..M22 then mutate a COPY of the cut, one defect each, and require the case
named for it to go red.  M0 is the unmutated copy through the same path: if
it is not green, no kill is counted.  A mutant whose anchor does not occur
exactly once, that does not compile, or whose named case stays green is a
survivor, never a kill.  Other cases a mutant also turns red are printed.

WHAT IT CANNOT SEE
------------------
The silicon: how long SWTACR is busy, whether a slot tears, whether a MIB
load clears a counter, whether any of the 298 has a read side effect.  The
model is written from the same sources as the driver's table.  Nor the rest
of the kernel: /proc's own read path beyond two calls per `cat`, and whether
rsdk's gcc 3.4.6 compiles the file -- the image build answers that.

Needs gcc and nothing else: no toolchain, no $FWRE_WORK, no device.
    viewcheck.py [--source PATH] [--keep DIR] [--no-mutants]
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
SOURCE = os.path.join(ROOT, "config", "rlxfw-src", "linux-2.6.30", "drivers",
                      "net", "rtl819x-view.c")
CFLAGS = ["-std=gnu89", "-O1", "-Wall", "-Wextra", "-Wno-unused-parameter",
          "-Wdeclaration-after-statement", "-Wstrict-prototypes", "-Werror"]
PAGE = 4096
VERSION = "rtl819x-view 1.0"

# asm-generic/errno-base.h, which arch/rlx/include/asm/errno.h includes for
# every value below 35 -- this arch's values.
ERRNO = {"EIO": 5, "EACCES": 13, "EFAULT": 14, "EBUSY": 16, "EINVAL": 22}

# ------------------------------------------------------------------------
# The 8c proposal's section 1.3, written again (not read from the driver).
# ------------------------------------------------------------------------
SWITCH_RUNS = [(0xBB804000, 4), (0xBB804044, 1), (0xBB804100, 10),
               (0xBB80414C, 2), (0xBB804200, 4), (0xBB804234, 4),
               (0xBB804300, 2), (0xBB80430C, 1), (0xBB804400, 14),
               (0xBB804A00, 8), (0xBB804D00, 3), (0xBB804D3C, 1)]
# RX at 0x100 + 0x80p + {00, 04, 08, 14-58}, TX at 0x800 + 0x80p + {...}
MIB_RX = [0x00, 0x04, 0x08] + [0x14 + 4 * i for i in range(18)]
MIB_TX = [0x00, 0x04, 0x08, 0x0C, 0x10, 0x18, 0x1C, 0x20, 0x24, 0x2C, 0x34]
MIB_CPUEVENT = 0xBB801084
CPU_RUNS = [(0xB8010000, 15), (0xB8010060, 2)]
PIN_RUNS = [(0xB8000040, 2)]
PSRP = [0xBB804128 + 4 * i for i in range(9)]
SWTACR = 0xBB804D00

MIB_OFFS = ([0x100 + o for o in MIB_RX] + [0x800 + o for o in MIB_TX])
MIB_ORDER = ([0xBB801000 + o + 0x80 * p for p in range(7) for o in MIB_OFFS]
             + [MIB_CPUEVENT])


def _runs(runs):
    return [a + 4 * i for a, n in runs for i in range(n)]


SWITCH_WORDS = _runs(SWITCH_RUNS)
CPU_WORDS = _runs(CPU_RUNS)
PIN_WORDS = _runs(PIN_RUNS)
ADMITTED = SWITCH_WORDS + MIB_ORDER + CPU_WORDS + PIN_WORDS
ADMIT_SET = set(ADMITTED)

TABLES = {"vlan": (0xBB060000, 16), "netif": (0xBB040000, 8)}

WINDOWS = [("switch", 0xBB804000, 1024, (54, 9, 961)),
           ("mib", 0xBB801000, 1024, (225, 0, 799)),
           ("cpu", 0xB8010000, 32, (17, 0, 15)),
           ("pinmux", 0xB8000000, 32, (2, 0, 30))]
EXTRAS = [0xBD006000, 0xBFC06000, 0x80000000, 0xB8003500, 0xBB060000,
          0xBB040000, 0x9B804000, 0x1B804000]


def val(a):
    """The model's value of a word (the harness computes the same)."""
    v = ((a * 0x9E3779B1) & 0xFFFFFFFF) ^ 0x5A5A5A5A
    return v & ~1 if a == SWTACR else v


HARNESS = r"""
#include <sys/types.h>
#include <ctype.h>
#include <errno.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
#define __init
#define __user
#define __iomem
#define ARRAY_SIZE(x)	(sizeof(x) / sizeof((x)[0]))
#define UNUSED __attribute__((unused))

/* ------------------------------------------------ the kernel's pieces */
static unsigned long jiffies = 4242;
static char last_mark[64];
static int n_marks;
static unsigned long udelay_total;

static void mark_puts(const char *s)
{
	snprintf(last_mark, sizeof(last_mark), "%s", s);
	n_marks++;
}
static UNUSED void mark_hex(const char *s, unsigned int v)
{
	snprintf(last_mark, sizeof(last_mark), "%s%08X", s, v);
	n_marks++;
}
#define rlxfw_mark(tag)		mark_puts("RLXFW-" tag)
#define rlxfw_markx(tag, v)	mark_hex("RLXFW-" tag "=", (unsigned int)(v))

static UNUSED void udelay(unsigned long us)
{
	udelay_total += us;
}

/* lib/vsprintf.c:36-75, transcribed: no whitespace is skipped.  The result
 * is computed in 32 bits, because this kernel's unsigned long is 32 bits and
 * the original checks no overflow: a long number wraps as it does there. */
static unsigned int k_guess_base(const char *cp)
{
	if (cp[0] == '0') {
		if ((cp[1] | 0x20) == 'x' && isxdigit((unsigned char)cp[2]))
			return 16;
		return 8;
	}
	return 10;
}
static UNUSED unsigned long simple_strtoul(const char *cp, char **endp,
					   unsigned int base)
{
	u32 result = 0;

	if (!base)
		base = k_guess_base(cp);
	if (base == 16 && cp[0] == '0' && (cp[1] | 0x20) == 'x')
		cp += 2;
	while (isxdigit((unsigned char)*cp)) {
		unsigned int value = isdigit((unsigned char)*cp) ? *cp - '0' :
				     (*cp | 0x20) - 'a' + 10;
		if (value >= base)
			break;
		result = result * base + value;
		cp++;
	}
	if (endp)
		*endp = (char *)cp;
	return result;
}
static UNUSED unsigned long copy_from_user(void *d, const void *s,
					   unsigned long n)
{
	memcpy(d, s, n);
	return 0;
}

/* ------------------------------------------------ the MMIO model */
static const u32 adm[] = {
@ADM@
};
#define NADM	(sizeof(adm) / sizeof(adm[0]))
#define SWTACR	0xBB804D00u
#define LOGMAX	(1 << 17)
static unsigned long adm_ld[NADM];
static int in_tbl;			/* a `w tbl ...` op is running */
static unsigned int tcnt[2][16][8];	/* loads per table word, this op */
static unsigned int tear_k[2][16], tear_w[2][16];
static long busy_after, busy_n;
static unsigned long n_loads;
static u32 ldlog[LOGMAX];
static unsigned long n_log, n_dumped;

static u32 mval(u32 a)
{
	u32 v = (a * 0x9E3779B1u) ^ 0x5A5A5A5Au;

	return a == SWTACR ? (v & ~1u) : v;
}
static int adm_index(u32 a)
{
	unsigned int i;

	for (i = 0; i < NADM; i++)
		if (adm[i] == a)
			return (int)i;
	return -1;
}
static int tbl_word(u32 a, int *t, int *s, int *w)
{
	if (a & 3u)
		return 0;
	if (a >= 0xBB060000u && a < 0xBB060000u + 16 * 32) {
		*t = 0;
		a -= 0xBB060000u;
	} else if (a >= 0xBB040000u && a < 0xBB040000u + 8 * 32) {
		*t = 1;
		a -= 0xBB040000u;
	} else {
		return 0;
	}
	*s = (int)(a >> 5);
	*w = (int)((a >> 2) & 7u);
	return 1;
}
static u32 mmio_load(u32 a)
{
	int i, t, s, w;
	unsigned int c;
	u32 v;

	if (n_log < LOGMAX)
		ldlog[n_log] = a;
	n_log++;
	n_loads++;
	i = adm_index(a);
	if (i >= 0) {
		adm_ld[i]++;
		v = mval(a);
		if (a == SWTACR) {
			if (busy_after > 0) {
				busy_after--;
			} else if (busy_n > 0) {
				busy_n--;
				v |= 1u;
			}
		}
		return v;
	}
	if (tbl_word(a, &t, &s, &w)) {
		if (!in_tbl) {
			fprintf(stderr, "harness: table load of %08X outside tbl\n", a);
			exit(9);
		}
		c = tcnt[t][s][w]++;
		v = mval(a);
		if (tear_k[t][s] && (unsigned int)w == tear_w[t][s] && (c & 1u) &&
		    c / 2 < tear_k[t][s])
			v ^= 1u;
		return v;
	}
	fprintf(stderr, "harness: load of %08X\n", a);
	exit(9);
}
static void mmio_store(u32 v, const volatile void *p, int size)
{
	fprintf(stderr, "harness: %d-byte store of %08X to %08X\n", size, v,
		(u32)(uintptr_t)p);
	exit(9);
}
static UNUSED u32 __raw_readl(const volatile void *p)
{
	return mmio_load((u32)(uintptr_t)p);
}
static UNUSED void __raw_writel(u32 v, volatile void *p) { mmio_store(v, p, 4); }
static UNUSED void writel(u32 v, volatile void *p) { mmio_store(v, p, 4); }
static UNUSED void __raw_writew(u16 v, volatile void *p) { mmio_store(v, p, 2); }
static UNUSED void writew(u16 v, volatile void *p) { mmio_store(v, p, 2); }
static UNUSED void __raw_writeb(u8 v, volatile void *p) { mmio_store(v, p, 1); }
static UNUSED void writeb(u8 v, volatile void *p) { mmio_store(v, p, 1); }

/* ------------------------------------------------ /proc */
struct file;
struct proc_dir_entry {
	int (*read_proc)(char *page, char **start, off_t off, int count,
			 int *eof, void *data);
	int (*write_proc)(struct file *file, const char *buf,
			  unsigned long count, void *data);
};
static struct proc_dir_entry the_pde;
static int pde_fail, pde_made;
static UNUSED struct proc_dir_entry *create_proc_entry(const char *name,
						       int mode, void *parent)
{
	if (pde_fail || strcmp(name, "rtl819x-view"))
		return NULL;
	pde_made = 1;
	return &the_pde;
}
#define device_initcall(fn)	static int (*harness_init)(void) = fn

#include "@BLOCK@"

/* ------------------------------------------------ the widest fields */
static void set_widest(void)
{
	rtl819x_view_last_j = 0xFFFFFFFFUL;
	rtl819x_view_last_rc = INT_MIN;
	rtl819x_view_n_mib = rtl819x_view_n_tbl = 0xFFFFFFFFUL;
	rtl819x_view_n_peek = rtl819x_view_n_refused = 0xFFFFFFFFUL;
	rtl819x_view_n_busy = rtl819x_view_n_ld = 0xFFFFFFFFUL;
	rtl819x_view_polls = 0xFFFFFFFFUL;
	rtl819x_view_ref_a = 0xFFFFFFFFu;
	rtl819x_view_ref_why = 2;		/* "psrp", as wide as "none" */
	jiffies = 0xFFFFFFFFUL;
}

int main(void)
{
	static char page[3 * PAGE_SZ], page2[3 * PAGE_SZ];
	char line[512], buf[512];
	int rc, n1, n2, eof, eof2, same;
	long a, b, c, d;
	unsigned long l0, i;
	char *start;

	printf("ERRNO EIO=%d EACCES=%d EFAULT=%d EBUSY=%d EINVAL=%d\n",
	       EIO, EACCES, EFAULT, EBUSY, EINVAL);
	printf("NADM %u\n", (unsigned int)NADM);
	while (fgets(line, sizeof(line), stdin)) {
		line[strcspn(line, "\n")] = '\0';
		if (!strcmp(line, "init")) {
			rc = harness_init();
			printf("OP init -> %d\n", rc);
		} else if (!strncmp(line, "w ", 2)) {
			snprintf(buf, sizeof(buf), "%s\n", line + 2);
			in_tbl = !strncmp(line + 2, "tbl ", 4);
			memset(tcnt, 0, sizeof(tcnt));
			rc = the_pde.write_proc(NULL, buf, strlen(buf), NULL);
			in_tbl = 0;
			printf("OP w %s -> %d\n", line + 2, rc);
		} else if (!strcmp(line, "r")) {
			start = NULL;
			eof = eof2 = 0;
			l0 = n_loads;
			memset(page, 0x5A, sizeof(page));
			memset(page2, 0x5A, sizeof(page2));
			n1 = the_pde.read_proc(page, &start, 0, PAGE_SZ, &eof, NULL);
			n2 = the_pde.read_proc(page2, &start, 0, PAGE_SZ, &eof2,
					       NULL);
			same = n1 == n2 && n1 >= 0 && !memcmp(page, page2, n1);
			page2[n2 < 0 ? 0 : n2] = '\0';
			printf("PAGE-BEGIN\n%sPAGE-END len=%d eof=%d same=%d ld=%lu\n",
			       page2, n2, eof2, same, n_loads - l0);
		} else if (!strcmp(line, "loads")) {
			for (i = n_dumped; i < n_log && i < LOGMAX; i++)
				printf("LD %08X\n", ldlog[i]);
			printf("LD-END n=%lu\n", n_log - n_dumped);
			n_dumped = n_log;
		} else if (!strcmp(line, "stat")) {
			printf("STAT loads=%lu marks=%d mark=%s pde=%d udelay=%lu "
			       "busyleft=%ld\n", n_loads, n_marks,
			       last_mark[0] ? last_mark : "-", pde_made,
			       udelay_total, busy_n);
		} else if (!strcmp(line, "widest")) {
			set_widest();
		} else if (sscanf(line, "set busy %ld %ld", &a, &b) == 2) {
			busy_after = a;
			busy_n = b;
		} else if (sscanf(line, "set tear %ld %ld %ld %ld", &a, &b, &c,
				  &d) == 4) {
			tear_k[a][b] = (unsigned int)c;
			tear_w[a][b] = (unsigned int)d;
		} else if (sscanf(line, "set tearall %ld %ld %ld", &a, &c,
				  &d) == 3) {
			for (b = 0; b < 16; b++) {
				tear_k[a][b] = (unsigned int)c;
				tear_w[a][b] = (unsigned int)d;
			}
		} else if (sscanf(line, "set pdefail %ld", &a) == 1) {
			pde_fail = (int)a;
		} else {
			printf("HARNESS unknown op: %s\n", line);
			return 3;
		}
		fflush(stdout);
	}
	return 0;
}
"""


def die(msg, rc=3):
    print("REFUSED: " + msg)
    sys.exit(rc)


def extract(src_text):
    """(the cut below the includes, version) or die with the reason.

    The includes must be one block, preceded by nothing but the header
    comment, and no #include may follow it: code above the block, or a
    later include, would be outside what the harness compiles."""
    lines = src_text.splitlines(keepends=True)
    inc = [i for i, ln in enumerate(lines) if ln.startswith("#include")]
    if not inc:
        die("the driver has no #include line to cut below")
    first, last = inc[0], inc[-1]
    for i in range(first, last + 1):
        if lines[i].strip() and not lines[i].startswith("#include"):
            die("line %d, between the includes, is neither blank nor an "
                "#include: the includes are not one block" % (i + 1))
    head = re.sub(r"/\*.*?\*/", "", "".join(lines[:first]), flags=re.S)
    if head.strip():
        die("something other than a comment precedes the includes: %r"
            % head.strip()[:60])
    cut = "".join(lines[last + 1:])
    if re.search(r"^\s*#\s*include", cut, re.M):
        die("an #include follows the include block")
    m = re.findall(r'^#define RTL819X_VIEW_VERSION\t"([^"]+)"$', cut, re.M)
    if len(m) != 1:
        die("RTL819X_VIEW_VERSION is defined %d times in the cut" % len(m))
    return cut, m[0]


class Run:
    """One harness process over one script, parsed."""

    def __init__(self, exe, script):
        p = subprocess.run([exe], input="\n".join(script) + "\n",
                           capture_output=True, text=True, timeout=300)
        self.rc = p.returncode
        self.err = p.stderr.strip()
        self.ops, self.pages, self.stats, self.loads = [], [], [], []
        self.errno = {}
        self.nadm = None
        cur = None
        ld = []
        for ln in p.stdout.split("\n"):
            if cur is not None:
                m = re.match(r"PAGE-END len=(-?\d+) eof=(\d+) same=(\d) "
                             r"ld=(\d+)$", ln)
                if m:
                    self.pages.append({"text": "".join(cur),
                                       "len": int(m.group(1)),
                                       "eof": int(m.group(2)),
                                       "same": int(m.group(3)),
                                       "ld": int(m.group(4))})
                    cur = None
                else:
                    cur.append(ln + "\n")
                continue
            if ln == "PAGE-BEGIN":
                cur = []
            elif ln.startswith("OP "):
                m = re.match(r"OP (.*) -> (-?\d+)$", ln)
                self.ops.append((m.group(1), int(m.group(2))))
            elif ln.startswith("STAT "):
                d = {}
                for kv in ln[5:].split(" "):
                    k, _, v = kv.partition("=")
                    d[k] = v
                self.stats.append(d)
            elif ln.startswith("LD "):
                ld.append(int(ln[3:], 16))
            elif ln.startswith("LD-END"):
                self.loads.append(ld)
                ld = []
            elif ln.startswith("ERRNO "):
                for kv in ln[6:].split(" "):
                    k, _, v = kv.partition("=")
                    self.errno[k] = int(v)
            elif ln.startswith("NADM "):
                self.nadm = int(ln.split()[1])

    def op(self, i):
        return self.ops[i][1] if i < len(self.ops) else None

    def rcs(self):
        return [x[1] for x in self.ops]

    def stat(self, i, k):
        return self.stats[i][k] if i < len(self.stats) else None

    def lines(self, i):
        return self.pages[i]["text"].split("\n")[:-1] if i < len(self.pages) \
            else []

    def field(self, i, key):
        for ln in self.lines(i):
            if ln.startswith(key + " "):
                return ln[len(key) + 1:]
        return None

    def result(self, i):
        """The page's result lines: everything after `ref`, before jiffies."""
        return self.lines(i)[5:-1]

    def why(self):
        return self.err or ("rc %d" % self.rc)


def ok_len(cmd):
    return len(cmd) + 1


def hx(v):
    return "%08X" % v


def boot_page():
    return ("version rtl819x-view 1.0\nadmit 298\nlast none j 0 rc 0\n"
            "n_mib 0 n_tbl 0 n_peek 0 refused 0 busy 0 ld 0\n"
            "ref 00000000 none\njiffies 4242\n")


def header(last, j, rc, nm, nt, npk, nref, nbusy, nld, ref_a, ref_why):
    return ["version rtl819x-view 1.0", "admit 298",
            "last %s j %d rc %d" % (last, j, rc),
            "n_mib %d n_tbl %d n_peek %d refused %d busy %d ld %d"
            % (nm, nt, npk, nref, nbusy, nld),
            "ref %08X %s" % (ref_a, ref_why)]


def mib_result():
    out = ["mib base BB801000 stride 080 ports 7 words 225",
           "mo " + " ".join("%03X" % o for o in MIB_OFFS)]
    for p in range(7):
        out.append("m%d " % p + " ".join(
            hx(val(0xBB801000 + o + 0x80 * p)) for o in MIB_OFFS))
    out.append("mc 084 " + hx(val(MIB_CPUEVENT)))
    return out


def tbl_loads(name, slots=None, tries=None, polls=None):
    """The exact load sequence of one `tbl` verb."""
    base, n = TABLES[name]
    out = []
    for s in range(n if slots is None else slots):
        out += [SWTACR] * ((polls or {}).get(s, 1))
        words = [base + 32 * s + 4 * w for w in range(8)]
        out += words * 2 * ((tries or {}).get(s, 1))
    return out


def slot_line(name, s, t=1, eq=True, flip=None):
    base, _ = TABLES[name]
    ws = [val(base + 32 * s + 4 * w) for w in range(8)]
    if flip is not None:
        ws[flip] ^= 1
    return "s%02d t%d %s " % (s, t, "eq" if eq else "mis") + \
        " ".join(hx(w) for w in ws)


def comment_figures(src):
    body = " ".join(re.sub(r"^\s*/?\*+/?\s?", "", ln).strip()
                    for ln in src.split("\n"))
    m = re.search(r"everything before the result is <= ([\d,]+) B, the "
                  r"widest result \(mib's\) is <= ([\d,]+) B and the trailer "
                  r"<= (\d+) B, so the page is <= ([\d,]+) B", body)
    if not m:
        return None
    return tuple(int(g.replace(",", "")) for g in m.groups())


def cases(exe, cut, version):
    """Yield (name, ok, detail) for V1..V16 (V0 is the compile)."""
    E = {k: -v for k, v in ERRNO.items()}

    # V1 boot
    r = Run(exe, ["init", "r", "stat", "loads"])
    ok = (r.rc == 0 and r.op(0) == 0 and version == VERSION
          and r.pages and r.pages[0]["text"] == boot_page()
          and r.stat(0, "loads") == "0" and r.stat(0, "marks") == "0"
          and r.stat(0, "pde") == "1" and r.loads == [[]])
    yield "V1", ok, "boot page %s" % (
        "exact, 0 loads" if ok else repr(r.pages[0]["text"] if r.pages
                                         else r.why())[:200])

    # V2 mib
    r = Run(exe, ["init", "w mib", "loads", "r", "stat"])
    want = header("mib", 4242, 0, 1, 0, 0, 0, 0, 225, 0, "none") + \
        mib_result() + ["jiffies 4242"]
    got = r.lines(0)
    ok = (r.rc == 0 and r.op(1) == ok_len("mib")
          and r.loads[:1] == [MIB_ORDER] and len(set(MIB_ORDER)) == 225
          and got == want and r.pages[0]["same"] == 1)
    yield "V2", ok, "rc %s, %d loads, page %s" % (
        r.op(1), len(r.loads[0]) if r.loads else -1,
        "exact" if got == want else "differs: %r" % (
            [x for x in got if x not in want][:2] or r.why()))

    # V3 mib with anything after it
    cmds = ["mib x", "mib ", " mib", "mibx", "mib 0", "MIB"]
    r = Run(exe, ["init"] + ["w " + c for c in cmds] + ["loads", "r"])
    ok = (r.rc == 0 and r.rcs()[1:] == [E["EINVAL"]] * len(cmds)
          and r.loads == [[]] and r.pages
          and r.pages[0]["text"] == boot_page())
    yield "V3", ok, "rcs %s" % (r.rcs()[1:] if r.rc == 0 else r.why())

    # V4, V5 tbl vlan / netif
    for tag, name in (("V4", "vlan"), ("V5", "netif")):
        base, n = TABLES[name]
        r = Run(exe, ["init", "w tbl " + name, "loads", "r", "stat"])
        want = header(name, 4242, 0, 0, 1, 0, 0, 0, n * 17, 0, "none") + \
            ["tbl %s base %08X slots %d words 8 polls %d" % (name, base, n, n)] + \
            [slot_line(name, s) for s in range(n)] + ["jiffies 4242"]
        got = r.lines(0)
        ok = (r.rc == 0 and r.op(1) == ok_len("tbl " + name)
              and r.loads[:1] == [tbl_loads(name)] and got == want
              and r.stat(0, "udelay") == "0")
        yield tag, ok, "rc %s, %s loads (want %d), page %s" % (
            r.op(1), len(r.loads[0]) if r.loads else r.why(), 17 * n,
            "exact" if got == want else "differs")

    # V6 tears
    script = ["init"]
    plan = [(1, True), (5, True), (9, True), (10, False), (12, False)]
    for k, _ in plan:
        script += ["set tear 0 3 %d 7" % k, "w tbl vlan", "loads", "r"]
    script += ["set tear 0 3 0 7", "set tear 1 0 2 0", "w tbl netif", "loads",
               "r"]
    r = Run(exe, script)
    bad = []
    for i, (k, settle) in enumerate(plan):
        t = min(k + 1, 10)
        want_line = slot_line("vlan", 3, t, settle, None if settle else 7)
        want_ld = tbl_loads("vlan", tries={3: t})
        if r.field(i, "s03") != want_line[4:] or \
                (r.loads[i] if i < len(r.loads) else None) != want_ld or \
                r.field(i, "s02") != slot_line("vlan", 2)[4:]:
            bad.append("k=%d: %s" % (k, r.field(i, "s03")))
    i = len(plan)
    if r.field(i, "s00") != slot_line("netif", 0, 3)[4:] or \
            (r.loads[i] if i < len(r.loads) else None) != \
            tbl_loads("netif", tries={0: 3}):
        bad.append("netif s00: %s" % r.field(i, "s00"))
    ok = r.rc == 0 and not bad and r.rcs()[1:] == [ok_len("tbl vlan")] * 5 + \
        [ok_len("tbl netif")]
    yield "V6", ok, "tears k=1,5,9 -> t2,t6,t10 eq; 10,12 -> t10 mis%s" % (
        "" if ok else "; " + ("; ".join(bad) or r.why()))

    # V7 busy: past the bound at slot 5, then exactly the bound
    B = 10000
    r = Run(exe, ["init", "set busy 5 %d" % (B + 1), "w tbl vlan", "loads",
                  "r", "stat", "w tbl vlan", "loads", "r"])
    ld0 = r.loads[0] if r.loads else []
    want = header("vlan", 4242, E["EBUSY"], 0, 1, 0, 0, 1, 5 * 17 + B + 1,
                  0, "none") + \
        ["tbl vlan base BB060000 slots 16 words 8 polls %d" % (5 + B + 1)] + \
        [slot_line("vlan", s) for s in range(5)] + ["busy s05", "jiffies 4242"]
    ok_a = (r.rc == 0 and r.op(1) == E["EBUSY"] and r.lines(0) == want
            and ld0 == tbl_loads("vlan", slots=5) + [SWTACR] * (B + 1)
            and r.stat(0, "udelay") == str(B) and r.stat(0, "busyleft") == "0"
            and r.op(2) == ok_len("tbl vlan")
            and len(r.loads) > 1 and r.loads[1] == tbl_loads("vlan")
            and r.field(1, "last") == "vlan j 4242 rc 0"
            and r.field(1, "n_mib") == "0 n_tbl 2 n_peek 0 refused 0 busy 1 "
                                      "ld %d" % (5 * 17 + B + 1 + 272))
    r2 = Run(exe, ["init", "set busy 5 %d" % B, "w tbl vlan", "loads", "r",
                   "stat"])
    ok_b = (r2.rc == 0 and r2.op(1) == ok_len("tbl vlan")
            and r2.loads[:1] == [tbl_loads("vlan", polls={5: B + 1})]
            and r2.field(0, "tbl") == "vlan base BB060000 slots 16 words 8 "
                                      "polls %d" % (16 + B)
            and r2.field(0, "s15") == slot_line("vlan", 15)[4:]
            and r2.stat(0, "udelay") == str(B)
            and (r2.field(0, "n_mib") or "").startswith("0 n_tbl 1 n_peek 0 "
                                                        "refused 0 busy 0"))
    yield "V7", ok_a and ok_b, "past the bound: rc %s, %d loads; at it: rc %s%s" % (
        r.op(1), len(ld0), r2.op(1),
        "" if ok_a and ok_b else " (%s | %s)" % (r.why(), r2.why()))

    # V8 tbl refusals beside the permitted twin
    cmds = ["tbl arp", "tbl vlan x", "tbl", "tbl  vlan", "tblvlan",
            "tbl vlan ", "tbl netif0", "tbl VLAN", "tbl l2"]
    r = Run(exe, ["init"] + ["w " + c for c in cmds] + ["loads", "r",
                                                         "w tbl netif", "loads"])
    ok = (r.rc == 0 and r.rcs()[1:-1] == [E["EINVAL"]] * len(cmds)
          and r.loads[:1] == [[]] and r.pages
          and r.pages[0]["text"] == boot_page()
          and r.op(len(cmds) + 1) == ok_len("tbl netif")
          and len(r.loads) > 1 and r.loads[1] == tbl_loads("netif"))
    yield "V8", ok, "rcs %s" % (r.rcs()[1:] if r.rc == 0 else r.why())

    # V9 peek every admitted word
    script = ["init"]
    for a in ADMITTED:
        script += ["w peek 0x%08X" % a, "loads", "r"]
    r = Run(exe, script)
    bad = []
    for i, a in enumerate(ADMITTED):
        if r.op(1 + i) != ok_len("peek 0x%08X" % a) or \
                (r.loads[i] if i < len(r.loads) else None) != [a] or \
                r.result(i) != ["peek %08X n 1" % a, "a %08X %08X" % (a, val(a))]:
            bad.append("%08X" % a)
    ok = (r.rc == 0 and not bad and len(ADMITTED) == 298
          and r.field(len(ADMITTED) - 1, "n_mib") ==
          "0 n_tbl 0 n_peek 298 refused 0 busy 0 ld 298")
    yield "V9", ok, "%d of 298 permitted with one load each%s" % (
        298 - len(bad), "" if ok else ": " + (", ".join(bad[:4]) or r.why()))

    # V10 every word of the four windows, and eight more
    targets = []
    for _, lo, n, _ in WINDOWS:
        targets += [lo + 4 * i for i in range(n)]
    targets += EXTRAS
    first = 0xBB804200
    script = ["init", "w peek 0x%08X" % first, "loads", "r"]
    for a in targets:
        script += ["w peek 0x%08X" % a, "loads", "r"]
    r = Run(exe, script)
    bad, tally, nref = [], {}, 0
    last_ok = first
    for i, a in enumerate(targets, 1):
        rc = r.op(1 + i)
        ld = r.loads[i] if i < len(r.loads) else None
        if a in ADMIT_SET:
            good = rc == ok_len("peek 0x%08X" % a) and ld == [a] and \
                r.result(i) == ["peek %08X n 1" % a, "a %08X %08X" % (a, val(a))]
            last_ok = a
            kind = "in"
        else:
            nref += 1
            kind = "psrp" if a in PSRP else "out"
            good = (rc == E["EACCES"] and ld == []
                    and r.field(i, "ref") == "%08X %s" % (a, kind)
                    and r.result(i) == ["peek %08X n 1" % last_ok,
                                        "a %08X %08X" % (last_ok, val(last_ok))]
                    and (r.field(i, "n_mib") or "").split(" ")[6:7] == [str(nref)])
        for name, lo, n, _ in WINDOWS:
            if lo <= a < lo + 4 * n:
                tally.setdefault(name, {"in": 0, "psrp": 0, "out": 0})[kind] += 1
        if not good:
            bad.append("%08X(%s rc %s)" % (a, kind, rc))
    tallies_ok = all(tuple(tally.get(name, {}).get(k, -1)
                           for k in ("in", "psrp", "out")) == want
                     for name, _, _, want in WINDOWS)
    ok = r.rc == 0 and not bad and tallies_ok
    yield "V10", ok, "%d words, %d refused with no load; %s%s" % (
        len(targets), nref,
        " ".join("%s %d/%d/%d" % (n, t["in"], t["psrp"], t["out"])
                 for n, t in tally.items()),
        "" if ok else ": " + (", ".join(bad[:4]) or r.why()))

    # V11 spanning out of a run: the whole request refused
    spans = [("0xBB804120 4", 0xBB804128, "psrp"),
             ("0xBB80410C 16", 0xBB804128, "psrp"),
             ("0xBB804D08 2", 0xBB804D0C, "out"),
             ("0xB8010064 2", 0xB8010068, "out"),
             ("0xBB801158 2", 0xBB80115C, "out"),
             ("0xB8000044 2", 0xB8000048, "out"),
             ("0xBB804428 16", 0xBB804438, "out")]
    script = ["init", "w mib", "loads"]
    for cmd, _, _ in spans:
        script += ["w peek " + cmd, "loads", "r"]
    script += ["w peek 0xBB804120 2", "loads", "w peek 0xB8010060 2", "loads"]
    r = Run(exe, script)
    bad = []
    mib_res = mib_result()
    for i, (cmd, a, why) in enumerate(spans):
        if r.op(2 + i) != E["EACCES"] or \
                (r.loads[1 + i] if 1 + i < len(r.loads) else None) != [] or \
                r.field(i, "ref") != "%08X %s" % (a, why) or \
                r.result(i) != mib_res or \
                r.field(i, "last") != "mib j 4242 rc 0":
            bad.append(cmd)
    k = 2 + len(spans)
    ok = (r.rc == 0 and not bad and r.op(k) == ok_len("peek 0xBB804120 2")
          and r.loads[1 + len(spans)] == [0xBB804120, 0xBB804124]
          and r.op(k + 1) == ok_len("peek 0xB8010060 2")
          and r.loads[2 + len(spans)] == [0xB8010060, 0xB8010064])
    yield "V11", ok, "%d spans refused whole, twins permitted%s" % (
        len(spans) - len(bad), "" if ok else ": " + (", ".join(bad) or r.why()))

    # V12 n = 16 inside one run
    run16 = [0xBB801114 + 4 * i for i in range(16)]
    r = Run(exe, ["init", "w peek 0xBB801114 16", "loads", "r",
                  "w peek 0xBB801414 16", "loads",
                  "w peek 0xBB801114 17", "w peek 0xBB801120 16", "loads"])
    ok = (r.rc == 0 and r.op(1) == ok_len("peek 0xBB801114 16")
          and r.loads[0] == run16
          and r.result(0) == ["peek BB801114 n 16"] +
          ["a %08X %08X" % (a, val(a)) for a in run16]
          and r.op(2) == ok_len("peek 0xBB801414 16")
          and r.loads[1] == [a + 0x300 for a in run16]
          and r.op(3) == E["EINVAL"] and r.op(4) == E["EACCES"]
          and r.loads[2] == [])
    yield "V12", ok, "rcs %s" % (r.rcs()[1:] if r.rc == 0 else r.why())

    # V13 cat loads nothing
    r = Run(exe, ["init", "w mib", "w tbl vlan", "stat", "r", "r", "stat",
                  "w peek 0xBB804000 4", "r", "stat"])
    ok = (r.rc == 0 and r.stat(0, "loads") == r.stat(1, "loads")
          and len(r.pages) == 3 and r.pages[0] == r.pages[1]
          and all(p["same"] == 1 and p["ld"] == 0 for p in r.pages)
          and int(r.stat(2, "loads") or -1) == int(r.stat(1, "loads") or 0) + 4)
    yield "V13", ok, "loads %s -> %s across two cats" % (
        r.stat(0, "loads"), r.stat(1, "loads"))

    # V14 the widest page of every verb
    r = Run(exe, ["init",
                  "w tbl netif", "widest", "r",
                  "w mib", "widest", "r",
                  "set tearall 0 10 0", "w tbl vlan", "widest", "r",
                  "set tearall 1 10 0", "w tbl netif", "widest", "r",
                  "w peek 0xBB801114 16", "widest", "r"])
    heads, results, trailers, totals = [], {}, [], []
    names = ["netif-head", "mib", "vlan", "netif", "peek"]
    for i, nm in enumerate(names):
        ls = r.lines(i)
        heads.append(sum(len(x) + 1 for x in ls[:5]))
        results[nm] = sum(len(x) + 1 for x in ls[5:-1])
        trailers.append(len(ls[-1]) + 1 if ls else -1)
        totals.append(r.pages[i]["len"] if i < len(r.pages) else -1)
    fig = comment_figures(cut)
    H, T = max(heads), max(trailers)
    R = max(v for k, v in results.items() if k != "netif-head")
    complete = (len([x for x in r.lines(1) if re.match(r"m\d ", x)]) == 7
                and len([x for x in r.lines(1) if x.startswith("mc ")]) == 1
                and len([x for x in r.lines(2) if re.match(r"s\d\d t10 mis ", x)]) == 16
                and len([x for x in r.lines(3) if re.match(r"s\d\d t10 mis ", x)]) == 8
                and len([x for x in r.lines(4) if x.startswith("a ")]) == 16)
    ok = (r.rc == 0 and fig is not None and fig == (H, R, T, H + R + T)
          and results["mib"] == R and complete
          and all(0 < t <= fig[3] <= PAGE for t in totals)
          and all(p["len"] == len(p["text"]) for p in r.pages)
          and all((r.lines(i)[-1:] or [""])[0] == "jiffies 4294967295"
                  for i in range(len(names))))
    yield "V14", ok, "comment %s; measured head %d, results %s, trailer %d, " \
        "pages %s" % (fig, H, {k: v for k, v in results.items()
                               if k != "netif-head"}, T, totals)

    # V15 the strict parser
    wrap = 0xBB804000 + (1 << 32)
    refused = ["peek  0xBB804000", "peek 0xBB804000  2", "peek 0xBB804000 1x",
               "peek 0xBB804000x", "peek xBB804000", "peek 0xBB804000 ",
               "peek 0xBB804001", "peek 0xBB804000 0", "peek 0xBB804000 17",
               "peek", "peek ", "peek 0xBB804000 1 2", "peek 0x1BB804000",
               "peek 0BB804000", "peek -1", "PEEK 0xBB804000", "peek 0x",
               "peek " + "0" * 43]
    permitted = [("peek 0xBB804000", [0xBB804000]),
                 ("peek 0xbb804004", [0xBB804004]),
                 ("peek %d" % 0xBB804008, [0xBB804008]),
                 ("peek 0xBB804000 4", [0xBB804000 + 4 * i for i in range(4)]),
                 ("peek 0xBB804000 04", [0xBB804000 + 4 * i for i in range(4)]),
                 ("peek %d" % wrap, [0xBB804000])]
    script = ["init"]
    for c in refused:
        script += ["w " + c, "loads"]
    for c, _ in permitted:
        script += ["w " + c, "loads", "r"]
    r = Run(exe, script)
    bad = [c for i, c in enumerate(refused)
           if r.op(1 + i) != E["EINVAL"] or
           (r.loads[i] if i < len(r.loads) else None) != []]
    base = 1 + len(refused)
    for j, (c, lds) in enumerate(permitted):
        if r.op(base + j) != ok_len(c) or \
                (r.loads[len(refused) + j] if len(refused) + j < len(r.loads)
                 else None) != lds or \
                r.field(j, "peek") != "%08X n %d" % (lds[0], len(lds)):
            bad.append(c)
    ok = r.rc == 0 and not bad and len(str(wrap)) == 10
    yield "V15", ok, "%d refused, %d permitted, the wrap %d -> BB804000 " \
        "shown%s" % (len(refused), len(permitted), wrap,
                     "" if ok else ": " + (", ".join(bad[:4]) or r.why()))

    # V16 the /proc entry failing at init
    r = Run(exe, ["set pdefail 1", "init", "stat"])
    ok = (r.rc == 0 and r.op(0) == 0
          and r.stat(0, "mark") == "RLXFW-VW0-NOPROC"
          and r.stat(0, "marks") == "1" and r.stat(0, "pde") == "0"
          and r.stat(0, "loads") == "0")
    yield "V16", ok, "mark %s" % (r.stat(0, "mark") if r.stats else r.why())


STORE_RE = re.compile(r"\b(?:__raw_)?write[bwlq]\b|\bout[bwl]\b|\biowrite")


def v0(exe, cut, version):
    """(ok, detail): the compile is implied by `exe`; the rest is here."""
    probe = Run(exe, [])
    tallies = []
    for name, lo, n, want in WINDOWS:
        words = [lo + 4 * i for i in range(n)]
        got = (sum(1 for a in words if a in ADMIT_SET),
               sum(1 for a in words if a in PSRP),
               sum(1 for a in words if a not in ADMIT_SET and a not in PSRP))
        tallies.append(got == want)
    stores = STORE_RE.findall(cut)
    list_ok = (len(ADMITTED) == 298 == len(ADMIT_SET) and probe.nadm == 298
               and len(SWITCH_WORDS) == 54 and len(MIB_ORDER) == 225
               and len(CPU_WORDS) == 17 and len(PIN_WORDS) == 2
               and all(tallies) and not (ADMIT_SET & set(PSRP)))
    ok = probe.errno == ERRNO and not stores and list_ok and version == VERSION
    return ok, "compiles with %s; errno %s; store accessors in the cut: %s; " \
        "model 54+225+17+2 = %d, window tallies %s" % (
            " ".join(CFLAGS),
            "= arch/rlx's" if probe.errno == ERRNO else probe.errno,
            ",".join(stores) or "none", len(ADMIT_SET),
            "= the proposal's" if all(tallies) else tallies)


def build(cut, work, tag):
    """Compile the harness around `cut`; (exe or None, compiler output)."""
    d = os.path.join(work, tag)
    os.makedirs(d, exist_ok=True)
    bpath = os.path.join(d, "cut.c")
    with open(bpath, "w", encoding="utf-8") as fh:
        fh.write(cut)
    adm = ",\n".join("\t0x%08Xu" % a for a in ADMITTED)
    h = (HARNESS.replace("@BLOCK@", bpath).replace("@ADM@", adm)
         .replace("PAGE_SZ", str(PAGE)))
    hpath = os.path.join(d, "harness.c")
    with open(hpath, "w", encoding="utf-8") as fh:
        fh.write(h)
    exe = os.path.join(d, "harness")
    p = subprocess.run(["gcc"] + CFLAGS + ["-o", exe, hpath],
                       capture_output=True, text=True, encoding="utf-8")
    return (exe if p.returncode == 0 else None), p.stdout + p.stderr


def evaluate(cut, version, work, tag):
    exe, out = build(cut, work, tag)
    if exe is None:
        return None, out
    res = {"V0": v0(exe, cut, version)}
    for name, ok, det in cases(exe, cut, version):
        res[name] = (ok, det)
    return res, ""


# Each mutant: (id, what it breaks, the case that must go red, old, new).
PEEK_CHECK = (
    "\tfor (i = 0; i < n; i++) {\n"
    "\t\tw = (u32)a + 4u * i;\n"
    "\t\twhy = rtl819x_view_admit(w);\n"
    "\t\tif (why != RTL819X_VIEW_IN) {\n"
    "\t\t\trtl819x_view_n_refused++;\n"
    "\t\t\trtl819x_view_ref_a = w;\n"
    "\t\t\trtl819x_view_ref_why = why;\n"
    "\t\t\treturn -EACCES;\n"
    "\t\t}\n"
    "\t}\n")
PEEK_LOAD = (
    "\tfor (i = 0; i < n; i++)\n"
    "\t\trtl819x_view_w[i] = rtl819x_view_ld((u32)a + 4u * i);\n")
MUTANTS = [
    ("M1", "PSRP admitted: the PITCR/PCRP run grows over PSRP0-8", "V10",
     "\t{ 0xBB804100, 10, 1, 0 },", "\t{ 0xBB804100, 19, 1, 0 },"),
    ("M2", "MIB_CONTROL admitted", "V2",
     "\t{ 0xBB801084,  1, 1, 0 },",
     "\t{ 0xBB801000,  1, 1, 0 },\n\t{ 0xBB801084,  1, 1, 0 },"),
    ("M3", "a run's end off by one (SWTACR..SWTAA takes 4D0C)", "V10",
     "\t{ 0xBB804D00,  3, 1, 0 },", "\t{ 0xBB804D00,  4, 1, 0 },"),
    ("M4", "peek checks after it loads", "V10",
     PEEK_CHECK + PEEK_LOAD, PEEK_LOAD + PEEK_CHECK),
    ("M5", "peek loads each word as it passes (a partial load)", "V11",
     PEEK_CHECK + PEEK_LOAD,
     PEEK_CHECK.replace("\t\t}\n\t}\n",
                        "\t\t}\n\t\trtl819x_view_w[i] = rtl819x_view_ld(w);\n\t}\n")),
    ("M6", "a cat loads (CpuEvent refreshed at render)", "V13",
     "\tlen += sprintf(page + len, \"version %s\\n\", RTL819X_VIEW_VERSION);",
     "\t(void)rtl819x_view_ld(0xBB801084u);\n"
     "\tlen += sprintf(page + len, \"version %s\\n\", RTL819X_VIEW_VERSION);"),
    ("M7", "nine tries, not ten", "V6",
     "#define RTL819X_VIEW_TRIES\t10", "#define RTL819X_VIEW_TRIES\t9"),
    ("M8", "the SWTACR wait unbounded, as the vendor's", "V7",
     "\t\t\tif (n >= RTL819X_VIEW_BOUND) {\n"
     "\t\t\t\trtl819x_view_n_busy++;\n"
     "\t\t\t\trtl819x_view_busy_s = (int)s;\n"
     "\t\t\t\trc = -EBUSY;\n"
     "\t\t\t\tgoto out;\n"
     "\t\t\t}\n",
     "\t\t\tif (0)\n\t\t\t\tgoto out;\n"),
    ("M9", "a slot stride of 0x10", "V4",
     "\t\ta = base + (s << 5);", "\t\ta = base + (s << 4);"),
    ("M10", "seventeen VLAN slots", "V4",
     "\t{ \"vlan\",  6, 16 },", "\t{ \"vlan\",  6, 17 },"),
    ("M11", "a SWTACR store before the poll", "V4",
     "\tfor (s = 0; s < t->slots; s++) {\n\t\tfor (n = 0; ; n++) {",
     "\tfor (s = 0; s < t->slots; s++) {\n"
     "\t\t__raw_writel(RTL819X_VIEW_ACTION, (void __iomem *)(unsigned long)"
     "RTL819X_VIEW_SWTACR);\n\t\tfor (n = 0; ; n++) {"),
    ("M12", "a byte counter's high word dropped (ifInOctets)", "V2",
     "\t{ 0xBB801100,  2, 7, 0x80 },", "\t{ 0xBB801100,  1, 7, 0x80 },"),
    ("M13", "a numeric field need not start with a digit", "V15",
     "\t\tif (*s < '0' || *s > '9')\n\t\t\treturn -EINVAL;\n", ""),
    ("M14", "a refusal not counted", "V10",
     "\t\t\trtl819x_view_n_refused++;\n", ""),
    ("M15", "the page budget cuts rows", "V14",
     "#define RTL819X_VIEW_PAGE_BUDGET\t3900",
     "#define RTL819X_VIEW_PAGE_BUDGET\t2000"),
    ("M16", "the compare skips the last word", "V6",
     "\t\t\tfor (k = 0; k < RTL819X_VIEW_ENTRY; k++)\n"
     "\t\t\t\tif (b0[k] != b1[k])",
     "\t\t\tfor (k = 0; k < RTL819X_VIEW_ENTRY - 1; k++)\n"
     "\t\t\t\tif (b0[k] != b1[k])"),
    ("M17", "the first buffer kept, not the second", "V6",
     "\t\t\t\tb0[k] = rtl819x_view_ld(a + 4u * k);\n"
     "\t\t\tfor (k = 0; k < RTL819X_VIEW_ENTRY; k++)\n"
     "\t\t\t\tb1[k] = rtl819x_view_ld(a + 4u * k);",
     "\t\t\t\tb1[k] = rtl819x_view_ld(a + 4u * k);\n"
     "\t\t\tfor (k = 0; k < RTL819X_VIEW_ENTRY; k++)\n"
     "\t\t\t\tb0[k] = rtl819x_view_ld(a + 4u * k);"),
    ("M18", "PSRP8 refused as `out`", "V10",
     "\tif (a >= RTL819X_VIEW_PSRP0 && a <= RTL819X_VIEW_PSRP8)",
     "\tif (a >= RTL819X_VIEW_PSRP0 && a < RTL819X_VIEW_PSRP8)"),
    ("M19", "peek takes seventeen words", "V12",
     "#define RTL819X_VIEW_PEEK_MAX\t16", "#define RTL819X_VIEW_PEEK_MAX\t17"),
    ("M20", "a refused peek empties the cache", "V11",
     "\t\t\trtl819x_view_ref_why = why;\n\t\t\treturn -EACCES;",
     "\t\t\trtl819x_view_ref_why = why;\n"
     "\t\t\trtl819x_view_last = RTL819X_VIEW_L_NONE;\n\t\t\treturn -EACCES;"),
    ("M21", "SWTACR polled on the wrong bit", "V7",
     "#define RTL819X_VIEW_ACTION\t(1u << 0)",
     "#define RTL819X_VIEW_ACTION\t(1u << 1)"),
    ("M22", "no cap on a field's length", "V15",
     "\t\tif (e - s > RTL819X_VIEW_FIELD_MAX ||\n\t\t    *e != (i + 1 < n ? ' ' : '\\0'))",
     "\t\tif (*e != (i + 1 < n ? ' ' : '\\0'))"),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--source", default=SOURCE)
    ap.add_argument("--keep", help="keep the build directory here")
    ap.add_argument("--no-mutants", action="store_true")
    a = ap.parse_args()
    if not shutil.which("gcc"):
        die("no gcc on PATH: this tool compiles the driver with the host's gcc")
    if not os.path.isfile(a.source):
        die("no such file: %s" % a.source)
    cut, version = extract(open(a.source, encoding="utf-8").read())
    work = a.keep or tempfile.mkdtemp(prefix="viewcheck-")
    os.makedirs(work, exist_ok=True)
    print("viewcheck 1.0")
    print("  source  %s  (cut %d lines, version %r)"
          % (a.source, cut.count("\n"), version))
    try:
        exe, out = build(cut, work, "M0")
        if exe is None:
            print("  FAIL  V0   the cut does not compile in the harness:")
            print(out)
            return 1
        ok0, det0 = v0(exe, cut, version)
        print("  %-4s  V0   %s" % ("ok" if ok0 else "FAIL", det0))
        fails = 0 if ok0 else 1
        n = 1
        for name, ok, det in cases(exe, cut, version):
            n += 1
            print("  %-4s  %-4s %s" % ("ok" if ok else "FAIL", name, det))
            fails += 0 if ok else 1
        print("RESULT: %d case(s), %d failed" % (n, fails))
        if fails:
            return 1
        if a.no_mutants:
            return 0
        print("")
        print("mutants (M0 is the unmutated cut through the same path)")
        m0, why = evaluate(cut, version, work, "M0b")
        if m0 is None or not all(ok for ok, _ in m0.values()):
            print("  FAIL  M0   the unmutated copy is not green: no kill counts")
            return 1
        print("  ok    M0   unmutated copy green on %d cases" % len(m0))
        survivors = 0
        for mid, what, named, old, new in MUTANTS:
            k = cut.count(old)
            if k != 1:
                print("  FAIL  %-4s anchor occurs %d times (%s)" % (mid, k, what))
                survivors += 1
                continue
            res, why = evaluate(cut.replace(old, new), version, work, mid)
            if res is None:
                print("  FAIL  %-4s does not compile (%s): %s"
                      % (mid, what, why.strip().splitlines()[-1:] or ""))
                survivors += 1
                continue
            red = sorted((x for x, (ok, _) in res.items() if not ok),
                         key=lambda x: int(x[1:]))
            killed = named in red
            survivors += 0 if killed else 1
            print("  %-4s  %-4s %-54s named %-4s red %s"
                  % ("ok" if killed else "FAIL", mid, what, named,
                     ",".join(red) or "-"))
        print("RESULT: %d mutant(s), %d killed by the case named for them, "
              "%d survived" % (len(MUTANTS), len(MUTANTS) - survivors,
                               survivors))
        return 1 if survivors else 0
    finally:
        if not a.keep:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
