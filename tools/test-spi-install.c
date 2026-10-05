/*
 * test-spi-install -- R8b Gap A's decisions, on the host.
 *
 * It #includes the DRIVER's own headers, not copies of their arithmetic:
 *
 *   config/rlxfw-src/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-wrpolicy.h
 *   config/rlxfw-src/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-install.h
 *
 * and, with -DWITH_CONTAINER_H, src/rlxboot/container.h -- the second source
 * for the RLXU offsets the install header restates (it cannot include it: that
 * header is not in the kernel tree).  The payload cases run on files that
 * tools/mkfw2.py and tools/mkcr6c.py PRODUCED, so "the installer accepts what
 * the producer emits" is tested against the producer and not against a fixture
 * built to agree with the parser.
 *
 * 🔴 WHAT A GREEN RUN SAYS, AND IT IS NARROW: the decisions refuse and permit
 * as declared, on x86-64.  It says nothing about the silicon -- no block has
 * been erased and no page programmed by this code anywhere.  The glue that
 * executes these decisions is test-spi-install-glue.c's subject.
 *
 * HOW IT AVOIDS BEING A TEST THAT CANNOT FAIL
 *  1. Every guard is driven refusing AND permitting.
 *  2. Every refusal reason the pure functions can produce is produced by at
 *     least one case; the seven only the kernel glue produces are exempt BY
 *     NAME, and the exemption is checked both ways (a pure case producing one
 *     of them turns this red, and the glue suite must produce all seven).
 *  3. `--mutate N` inverts case N's expectation; tools/test-spi-install.sh
 *     runs the unmutated suite first and requires every mutation to go red,
 *     and it also mutates the HEADER's source and requires red.
 *  4. D11's union check has a negative control that must come out unequal.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>

typedef unsigned int u32;
typedef unsigned short u16;
typedef unsigned char u8;

#include "rtl819x-spi-wrpolicy.h"
#include "rtl819x-spi-install.h"
#ifdef WITH_CONTAINER_H
#include "container.h"
#include "rlxboot.h"	/* Gap B's slot layout: the reader of what this writes */
#endif

#define OK	RLXFW_SPI_INST_OK
#define NREG	RLXFW_SPI_INST_NREGIONS
#define REG(i)	(&rlxfw_spi_inst_regions[(i)])
#define PAGE	RLXFW_SPI_WR_PAGE
#define BLOCK	RLXFW_SPI_INST_BLOCK
#define CHIP	RLXFW_SPI_WR_CHIP

enum { I_RLXBOOT, I_RESCUE, I_BARRIER, I_SLOTA, I_SLOTB, I_PROBE };

/* ------------------------------------------------------------------ cases */

static int ncase, nfail, npermit, nrefuse, mutate = -1;
static int seen[RLXFW_SPI_INST_R_COUNT];

static const char *rn(int r)
{
	return rlxfw_spi_inst_reason_name(r);
}

/* A reason-valued case.  The mutation asks for the one answer the code did
 * not give, so a suite that cannot fail shows up. */
static void ck(const char *name, int got, int want)
{
	int idx = ncase++;

	if (want == OK)
		npermit++;
	else
		nrefuse++;
	if (got >= 0 && got < RLXFW_SPI_INST_R_COUNT)
		seen[got]++;
	if (idx == mutate) {
		want = (want == OK) ? RLXFW_SPI_INST_R_SYNTAX : OK;
		printf("MUTATED case %d: now expecting %s\n", idx, rn(want));
	}
	if (got != want) {
		printf("  FAIL %4d %-52s got %s, want %s\n", idx, name, rn(got),
		       rn(want));
		nfail++;
	} else {
		printf("  ok   %4d %-52s %s\n", idx, name, rn(got));
	}
}

/* A property case: `holds` must be true (or false, under mutation). */
static void ckb(const char *name, int holds)
{
	int idx = ncase++;
	int want = 1;

	if (idx == mutate) {
		want = 0;
		printf("MUTATED case %d: now expecting the property to FAIL\n",
		       idx);
	}
	if ((holds != 0) != want) {
		printf("  FAIL %4d %s\n", idx, name);
		nfail++;
	} else {
		printf("  ok   %4d %s\n", idx, name);
	}
}

/* ------------------------------------------------------------------ files */

struct blob {
	u8 *p;
	u32 n;
};

static struct blob load(const char *dir, const char *name)
{
	struct blob b = { NULL, 0 };
	char path[1024];
	FILE *f;
	long sz;

	snprintf(path, sizeof(path), "%s/%s", dir, name);
	f = fopen(path, "rb");
	if (!f) {
		fprintf(stderr, "test-spi-install: no fixture %s -- refusing to "
			"run without the producers' output\n", path);
		exit(3);
	}
	fseek(f, 0, SEEK_END);
	sz = ftell(f);
	fseek(f, 0, SEEK_SET);
	b.p = malloc((size_t)sz + 1u);
	if (!b.p || fread(b.p, 1, (size_t)sz, f) != (size_t)sz) {
		fprintf(stderr, "test-spi-install: cannot read %s\n", path);
		exit(3);
	}
	fclose(f);
	b.n = (u32)sz;
	return b;
}

/* -------------------------------------------------------------- A: table */

static void t_table(void)
{
	int i, j;
	u32 maxsz = 0;
	char nm[96];

	for (i = 0; i < NREG; i++) {
		const struct rlxfw_spi_inst_region *r = REG(i);

		snprintf(nm, sizeof(nm), "D1 %s: base >= 0x010000", r->name);
		ckb(nm, r->base >= 0x00010000u);
		snprintf(nm, sizeof(nm), "D1 %s: never touches [0, 0x10000)",
			 r->name);
		ckb(nm, !rlxfw_spi_wr_overlaps_never(r->base, r->base + r->size)
		    && r->base >= RLXFW_SPI_INST_FLOOR);
		snprintf(nm, sizeof(nm), "D11 %s: 64 KiB-aligned, 64 KiB multiple",
			 r->name);
		ckb(nm, (r->base % BLOCK) == 0u && (r->size % BLOCK) == 0u &&
		    r->size != 0u);
		snprintf(nm, sizeof(nm), "D3 %s: ends below the state block",
			 r->name);
		ckb(nm, r->base + r->size <= RLXFW_SPI_INST_STATE);
		if (r->size > maxsz)
			maxsz = r->size;
		for (j = i + 1; j < NREG; j++)
			if (!strcmp(r->name, REG(j)->name) ||
			    r->base + r->size > REG(j)->base)
				ckb("regions unique and ascending", 0);
	}
	ckb("D12 the staging capacity is the largest region (1,179,648)",
	    RLXFW_SPI_INST_IMG_CAP == maxsz && maxsz == 1179648u);
	ckb("D1 layout: rlxboot 010000/64K rescue 020000/64K",
	    REG(I_RLXBOOT)->base == 0x010000u && REG(I_RLXBOOT)->size == 65536u
	    && REG(I_RESCUE)->base == 0x020000u &&
	    REG(I_RESCUE)->size == 65536u);
	ckb("D1 layout: barrier 030000/256K, erase-only (D2)",
	    REG(I_BARRIER)->base == 0x030000u &&
	    REG(I_BARRIER)->size == 262144u &&
	    REG(I_BARRIER)->kind == RLXFW_SPI_INST_K_ERASE);
	ckb("D1 layout: slotA 070000/1,179,648 slotB 190000/1,179,648",
	    REG(I_SLOTA)->base == 0x070000u && REG(I_SLOTA)->size == 1179648u
	    && REG(I_SLOTB)->base == 0x190000u &&
	    REG(I_SLOTB)->size == 1179648u);
	ckb("slots hold RLXU, rlxboot/rescue hold cr6c",
	    REG(I_SLOTA)->kind == RLXFW_SPI_INST_K_RLXU &&
	    REG(I_SLOTB)->kind == RLXFW_SPI_INST_K_RLXU &&
	    REG(I_RLXBOOT)->kind == RLXFW_SPI_INST_K_CR6C &&
	    REG(I_RESCUE)->kind == RLXFW_SPI_INST_K_CR6C);
	ckb("D19 probe: 3E0000/64K, after slot B, ends where the state block "
	    "begins, probe-only",
	    NREG == 6 && REG(I_PROBE)->base == 0x3E0000u &&
	    REG(I_PROBE)->size == 65536u &&
	    REG(I_PROBE)->base >= REG(I_SLOTB)->base + REG(I_SLOTB)->size &&
	    REG(I_PROBE)->base + REG(I_PROBE)->size == RLXFW_SPI_INST_STATE &&
	    REG(I_PROBE)->kind == RLXFW_SPI_INST_K_PROBE);
	ckb("D19 probe: inside the tail the 2026-08-16 dump read erased "
	    "(0x34C000-0x3FFFFF)",
	    REG(I_PROBE)->base >= 0x34C000u &&
	    REG(I_PROBE)->base + REG(I_PROBE)->size <= 0x400000u);
	for (i = 0; i < RLXFW_SPI_INST_R_COUNT; i++)
		if (!rlxfw_spi_inst_rname[i])
			ckb("every reason has a name", 0);
}

/* ------------------------------------------------------------- B: verbs */

static const char HEX_LO[] =
	"00112233445566778899aabbccddeeff0123456789abcdef0f1e2d3c4b5a6978";
static const char HEX_UP[] =
	"00112233445566778899AABBCCDDEEFF0123456789ABCDEF0F1E2D3C4B5A6978";

static int parse(const char *s, struct rlxfw_spi_inst_req *rq)
{
	return rlxfw_spi_inst_parse(s, rq);
}

static void t_parse(void)
{
	struct rlxfw_spi_inst_req rq;
	char b[256];
	int r;

	snprintf(b, sizeof(b), "install slotA sha=%s", HEX_LO);
	r = parse(b, &rq);
	ck("install slotA sha=<64 lower>", r, OK);
	ckb("  ... names slotA, unpaced, digest decoded",
	    rq.region == I_SLOTA && rq.pace_ms == 0u &&
	    rq.verb == RLXFW_SPI_INST_V_INSTALL && rq.sha[0] == 0x00u &&
	    rq.sha[10] == 0xAAu && rq.sha[31] == 0x78u);
	snprintf(b, sizeof(b), "install slotB sha=%s pace=500", HEX_UP);
	r = parse(b, &rq);
	ck("install slotB sha=<64 UPPER> pace=500", r, OK);
	ckb("  ... names slotB, pace 500, same digest",
	    rq.region == I_SLOTB && rq.pace_ms == 500u && rq.sha[10] == 0xAAu);
	snprintf(b, sizeof(b), "install rlxboot sha=%s pace=30000", HEX_LO);
	ck("install rlxboot ... pace=30000 (the longest line)", parse(b, &rq),
	   OK);
	ckb("  ... that line is 95 bytes, under the 128-byte buffer",
	    strlen(b) == 95u && strlen(b) + 1u < RLXFW_SPI_INST_LINE_MAX);
	/* The rescue drill (R8b): a 64 KiB region is one block, so two paces --
	 * after its erase and after its program phase -- must reach 60 s, and
	 * the cell that types it must stay one --send under 127 characters. */
	ckb("  ... pace 30000 parsed: two pauses on a 64 KiB region = 60 s",
	    rq.pace_ms == 30000u && 2ul * rq.pace_ms >= 60000ul);
	ckb("  ... `echo <it> > /proc/rtl819x-spi` is 120 characters, < 127",
	    strlen("echo ") + strlen(b) + strlen(" > /proc/rtl819x-spi") == 120u);
	snprintf(b, sizeof(b), "install rescue sha=%s", HEX_LO);
	ck("install rescue sha=...", parse(b, &rq), OK);
	ck("erase barrier", parse("erase barrier", &rq), OK);
	ckb("  ... erase barrier names the barrier, no digest",
	    rq.region == I_BARRIER && rq.verb == RLXFW_SPI_INST_V_ERASE);
	ck("erase barrier pace=1", parse("erase barrier pace=1", &rq), OK);

	ck("empty line", parse("", &rq), RLXFW_SPI_INST_R_SYNTAX);
	ck("install (alone)", parse("install", &rq), RLXFW_SPI_INST_R_SYNTAX);
	ck("install + space", parse("install ", &rq), RLXFW_SPI_INST_R_SYNTAX);
	ck("install slotA (no digest)", parse("install slotA", &rq),
	   RLXFW_SPI_INST_R_SYNTAX);
	snprintf(b, sizeof(b), "install slotA sha=%.63s", HEX_LO);
	ck("63 hex digits", parse(b, &rq), RLXFW_SPI_INST_R_SYNTAX);
	snprintf(b, sizeof(b), "install slotA sha=%s0", HEX_LO);
	ck("65 hex digits", parse(b, &rq), RLXFW_SPI_INST_R_SYNTAX);
	snprintf(b, sizeof(b), "install slotA sha=%.63sg", HEX_LO);
	ck("a non-hex digit", parse(b, &rq), RLXFW_SPI_INST_R_SYNTAX);
	snprintf(b, sizeof(b), "install slotA sha=%s ", HEX_LO);
	ck("a trailing space", parse(b, &rq), RLXFW_SPI_INST_R_SYNTAX);
	snprintf(b, sizeof(b), "install  slotA sha=%s", HEX_LO);
	ck("a double space", parse(b, &rq), RLXFW_SPI_INST_R_SYNTAX);
	snprintf(b, sizeof(b), "install slotA SHA=%s", HEX_LO);
	ck("SHA= in capitals", parse(b, &rq), RLXFW_SPI_INST_R_SYNTAX);
	snprintf(b, sizeof(b), "install slotA sha=%s pace=0", HEX_LO);
	ck("pace=0 (paced must mean paced)", parse(b, &rq),
	   RLXFW_SPI_INST_R_SYNTAX);
	snprintf(b, sizeof(b), "install slotA sha=%s pace=30001", HEX_LO);
	ck("pace=30001, over the ceiling", parse(b, &rq),
	   RLXFW_SPI_INST_R_SYNTAX);
	snprintf(b, sizeof(b), "install slotA sha=%s pace=01", HEX_LO);
	ck("pace=01, a leading zero", parse(b, &rq), RLXFW_SPI_INST_R_SYNTAX);
	snprintf(b, sizeof(b), "install slotA sha=%s pace=", HEX_LO);
	ck("pace= with no number", parse(b, &rq), RLXFW_SPI_INST_R_SYNTAX);
	snprintf(b, sizeof(b), "install slotA sha=%s pace=5 x", HEX_LO);
	ck("a fourth token", parse(b, &rq), RLXFW_SPI_INST_R_SYNTAX);
	snprintf(b, sizeof(b), "install slotA pace=5 sha=%s", HEX_LO);
	ck("pace before sha", parse(b, &rq), RLXFW_SPI_INST_R_SYNTAX);
	snprintf(b, sizeof(b), "Install slotA sha=%s", HEX_LO);
	ck("Install, capitalised", parse(b, &rq), RLXFW_SPI_INST_R_SYNTAX);
	ck("erase (alone)", parse("erase", &rq), RLXFW_SPI_INST_R_SYNTAX);
	snprintf(b, sizeof(b), "erase barrier sha=%s", HEX_LO);
	ck("erase barrier with a digest (no payload)", parse(b, &rq),
	   RLXFW_SPI_INST_R_SYNTAX);
	ck("erase barrier extra", parse("erase barrier extra", &rq),
	   RLXFW_SPI_INST_R_SYNTAX);

	/* D1/D6: no address is nameable, in any spelling. */
	snprintf(b, sizeof(b), "install slota sha=%s", HEX_LO);
	ck("slota, lower case", parse(b, &rq), RLXFW_SPI_INST_R_REGION);
	snprintf(b, sizeof(b), "install 0x70000 sha=%s", HEX_LO);
	ck("an address in hex instead of a name", parse(b, &rq),
	   RLXFW_SPI_INST_R_REGION);
	snprintf(b, sizeof(b), "install 458752 sha=%s", HEX_LO);
	ck("an address in decimal instead of a name", parse(b, &rq),
	   RLXFW_SPI_INST_R_REGION);
	snprintf(b, sizeof(b), "install loader sha=%s", HEX_LO);
	ck("the loader is not nameable", parse(b, &rq),
	   RLXFW_SPI_INST_R_REGION);
	snprintf(b, sizeof(b), "install h601 sha=%s", HEX_LO);
	ck("H601 is not nameable", parse(b, &rq), RLXFW_SPI_INST_R_REGION);
	ck("erase 0x0", parse("erase 0x0", &rq), RLXFW_SPI_INST_R_REGION);
	ck("erase state", parse("erase state", &rq), RLXFW_SPI_INST_R_REGION);

	/* D19: the probe verb takes nothing, and nothing else reaches the probe */
	ck("eraseprobe", parse("eraseprobe", &rq), OK);
	ckb("  ... names the probe block, verb eraseprobe, unpaced",
	    rq.region == I_PROBE && rq.verb == RLXFW_SPI_INST_V_PROBE &&
	    rq.pace_ms == 0u);
	ck("eraseprobe probe (no argument is taken)",
	   parse("eraseprobe probe", &rq), RLXFW_SPI_INST_R_SYNTAX);
	ck("eraseprobe + space", parse("eraseprobe ", &rq),
	   RLXFW_SPI_INST_R_SYNTAX);
	ck("eraseprobe pace=10", parse("eraseprobe pace=10", &rq),
	   RLXFW_SPI_INST_R_SYNTAX);
	ck("eraseprobes", parse("eraseprobes", &rq), RLXFW_SPI_INST_R_SYNTAX);
	ck("erase probe", parse("erase probe", &rq),
	   RLXFW_SPI_INST_R_PROBE_ONLY);
	snprintf(b, sizeof(b), "install probe sha=%s", HEX_LO);
	ck("install probe", parse(b, &rq), RLXFW_SPI_INST_R_PROBE_ONLY);

	/* D2/D6: the barrier is erase-only and only the barrier is erased. */
	snprintf(b, sizeof(b), "install barrier sha=%s", HEX_LO);
	ck("install barrier", parse(b, &rq), RLXFW_SPI_INST_R_ERASE_ONLY);
	ck("erase slotA", parse("erase slotA", &rq),
	   RLXFW_SPI_INST_R_NOT_ERASABLE);
	ck("erase rlxboot", parse("erase rlxboot", &rq),
	   RLXFW_SPI_INST_R_NOT_ERASABLE);
	ck("erase rescue", parse("erase rescue", &rq),
	   RLXFW_SPI_INST_R_NOT_ERASABLE);
}

/* ---------------------------------------------------------- C: arm match */

static void t_arm(void)
{
	struct rlxfw_spi_wr_arm a;
	char nm[96];
	int i;

	for (i = 0; i < NREG; i++) {
		const struct rlxfw_spi_inst_region *r = REG(i);
		const struct rlxfw_spi_inst_region *o = REG((i + 1) % NREG);

		/* the arm verb's own guard can express this region's arm */
		snprintf(nm, sizeof(nm), "arm verb accepts %s's exact arm",
			 r->name);
		ck(nm, rlxfw_spi_wr_chk_arm(r->base, r->base + r->size, r->size)
		   == RLXFW_SPI_WR_OK ? OK : RLXFW_SPI_INST_R_ARM_WINDOW, OK);

		a.armed = 1;
		a.lo = r->base;
		a.hi = r->base + r->size;
		a.budget = r->size;
		snprintf(nm, sizeof(nm), "%s: exact window, budget == size",
			 r->name);
		ck(nm, rlxfw_spi_inst_chk_arm(&a, r), OK);

		a.armed = 0;
		snprintf(nm, sizeof(nm), "%s: unarmed", r->name);
		ck(nm, rlxfw_spi_inst_chk_arm(&a, r), RLXFW_SPI_INST_R_UNARMED);
		a.armed = 1;

		a.lo = r->base + 0x1000u;
		snprintf(nm, sizeof(nm), "%s: window starts one sector late",
			 r->name);
		ck(nm, rlxfw_spi_inst_chk_arm(&a, r),
		   RLXFW_SPI_INST_R_ARM_WINDOW);
		a.lo = r->base;

		a.hi = r->base + r->size - 0x1000u;
		snprintf(nm, sizeof(nm), "%s: window ends one sector early",
			 r->name);
		ck(nm, rlxfw_spi_inst_chk_arm(&a, r),
		   RLXFW_SPI_INST_R_ARM_WINDOW);

		a.lo = r->base - BLOCK;
		a.hi = r->base + r->size;
		snprintf(nm, sizeof(nm), "%s: a superset window", r->name);
		ck(nm, rlxfw_spi_inst_chk_arm(&a, r),
		   RLXFW_SPI_INST_R_ARM_WINDOW);

		a.lo = o->base;
		a.hi = o->base + o->size;
		a.budget = o->size;
		snprintf(nm, sizeof(nm), "%s: armed for %s instead", r->name,
			 o->name);
		ck(nm, rlxfw_spi_inst_chk_arm(&a, r),
		   RLXFW_SPI_INST_R_ARM_WINDOW);

		a.lo = r->base;
		a.hi = r->base + r->size;
		a.budget = r->size - 1u;
		snprintf(nm, sizeof(nm), "%s: budget one byte short", r->name);
		ck(nm, rlxfw_spi_inst_chk_arm(&a, r),
		   RLXFW_SPI_INST_R_ARM_BUDGET);
	}
}

/* -------------------------------------------------------- E: staging */

static void t_img(void)
{
	struct rlxfw_spi_inst_img im;
	const u32 cap = RLXFW_SPI_INST_IMG_CAP;

	memset(&im, 0, sizeof(im));
	ck("chk_img: nothing staged", rlxfw_spi_inst_chk_img(&im,
	   REG(I_SLOTA)), RLXFW_SPI_INST_R_IMG_EMPTY);
	ckb("admit exactly the capacity",
	    rlxfw_spi_inst_img_admit(&im, cap) == RLXFW_SPI_INST_IMG_OK);
	im.len = cap;
	ck("chk_img: slotA full", rlxfw_spi_inst_chk_img(&im, REG(I_SLOTA)),
	   OK);
	ck("chk_img: the same bytes for rlxboot", rlxfw_spi_inst_chk_img(&im,
	   REG(I_RLXBOOT)), RLXFW_SPI_INST_R_IMG_SIZE);
	ckb("one byte past the capacity is refused and poisons",
	    rlxfw_spi_inst_img_admit(&im, 1ul) == RLXFW_SPI_INST_IMG_OVERFLOW
	    && im.err == RLXFW_SPI_INST_IMG_OVERFLOW && im.len == cap);
	ckb("after poisoning even a 0-byte append is refused",
	    rlxfw_spi_inst_img_admit(&im, 0ul) == RLXFW_SPI_INST_IMG_POISONED);
	ck("chk_img: poisoned", rlxfw_spi_inst_chk_img(&im, REG(I_SLOTA)),
	   RLXFW_SPI_INST_R_IMG_BAD);
	rlxfw_spi_inst_img_reset(&im);
	ckb("img reset clears length and error, counts the reset",
	    im.len == 0u && im.err == 0 && im.resets == 1u);
	im.len = cap - 10u;
	ckb("10 bytes into the last 10", rlxfw_spi_inst_img_admit(&im, 10ul)
	    == RLXFW_SPI_INST_IMG_OK);
	ckb("11 bytes into the last 10", rlxfw_spi_inst_img_admit(&im, 11ul)
	    == RLXFW_SPI_INST_IMG_OVERFLOW);
	rlxfw_spi_inst_img_reset(&im);
	ckb("a huge count cannot wrap the comparison",
	    rlxfw_spi_inst_img_admit(&im, ~0ul) ==
	    RLXFW_SPI_INST_IMG_OVERFLOW);
	rlxfw_spi_inst_img_reset(&im);
	im.len = 65536u;
	ck("chk_img: rlxboot exactly full", rlxfw_spi_inst_chk_img(&im,
	   REG(I_RLXBOOT)), OK);
	im.len = 65537u;
	ck("chk_img: rlxboot one byte over", rlxfw_spi_inst_chk_img(&im,
	   REG(I_RLXBOOT)), RLXFW_SPI_INST_R_IMG_SIZE);
}

/* --------------------------------------------------- F/G: the payloads */

static void t_digest(void)
{
	u8 a[32], b[32];
	int i;

	for (i = 0; i < 32; i++)
		a[i] = b[i] = (u8)(i * 7 + 1);
	ckb("digest_eq: equal", rlxfw_spi_inst_digest_eq(a, b));
	b[31] ^= 1u;
	ckb("digest_eq: last bit differs", !rlxfw_spi_inst_digest_eq(a, b));
	b[31] ^= 1u;
	b[0] ^= 0x80u;
	ckb("digest_eq: first bit differs", !rlxfw_spi_inst_digest_eq(a, b));
}

static int pay(const struct blob *b, u32 n, int reg)
{
	return rlxfw_spi_inst_chk_payload(b->p, n, REG(reg));
}

static void t_payload(const char *dir)
{
	struct blob A = load(dir, "slotA.rlxu");
	struct blob AF = load(dir, "slotA-full.rlxu");
	struct blob B = load(dir, "slotB.rlxu");
	struct blob AP = load(dir, "slotA-payl.rlxu");
	struct blob NF = load(dir, "nff.rlxu");
	struct blob R = load(dir, "rlxboot.cr6c");
	struct blob S = load(dir, "rescue.cr6c");

	ck("producer's slotA container on slotA", pay(&A, A.n, I_SLOTA), OK);
	ck("producer's full-size slotA container on slotA",
	   pay(&AF, AF.n, I_SLOTA), OK);
	ckb("  ... and it is exactly the region's size",
	    AF.n == REG(I_SLOTA)->size);
	ck("producer's slotB container on slotB", pay(&B, B.n, I_SLOTB), OK);
	ck("slotA container on slotB (flash_at)", pay(&A, A.n, I_SLOTB),
	   RLXFW_SPI_INST_R_HDR_FLASH_AT);
	ck("slotB container on slotA (flash_at)", pay(&B, B.n, I_SLOTA),
	   RLXFW_SPI_INST_R_HDR_FLASH_AT);
	ck("a PAYL-form container for slotA", pay(&AP, AP.n, I_SLOTA),
	   RLXFW_SPI_INST_R_HDR_FORM);
	ck("a not-for-flash container on slotA", pay(&NF, NF.n, I_SLOTA),
	   RLXFW_SPI_INST_R_HDR_FLASH_AT);
	ck("slotA container less its last byte", pay(&A, A.n - 1u, I_SLOTA),
	   RLXFW_SPI_INST_R_HDR_LEN);
	ck("slotA header and signature only (160)", pay(&A, 160u, I_SLOTA),
	   RLXFW_SPI_INST_R_HDR_LEN);
	ck("slotA, 159 bytes", pay(&A, 159u, I_SLOTA),
	   RLXFW_SPI_INST_R_HDR_LEN);
	ck("slotA, 3 bytes", pay(&A, 3u, I_SLOTA), RLXFW_SPI_INST_R_HDR_MAGIC);
	A.p[A.n] = 0u;
	ck("slotA container plus one trailing byte", pay(&A, A.n + 1u,
	   I_SLOTA), RLXFW_SPI_INST_R_HDR_LEN);
	A.p[5] ^= 3u;	/* format 2 -> 1 */
	ck("slotA container with format 1", pay(&A, A.n, I_SLOTA),
	   RLXFW_SPI_INST_R_HDR_FORMAT);
	A.p[5] ^= 3u;
	ck("FW-168: a container where a cr6c must go (rescue)",
	   pay(&A, A.n, I_RESCUE), RLXFW_SPI_INST_R_HDR_MAGIC);
	ck("a cr6c where a container must go (slotA)", pay(&S, S.n, I_SLOTA),
	   RLXFW_SPI_INST_R_HDR_MAGIC);

	ck("producer's rlxboot.cr6c on rlxboot", pay(&R, R.n, I_RLXBOOT), OK);
	ck("producer's rescue.cr6c on rescue (full 64 KiB)",
	   pay(&S, S.n, I_RESCUE), OK);
	ckb("  ... and rescue.cr6c fills the region", S.n == 65536u);
	ck("rlxboot.cr6c on rescue (burnAddr)", pay(&R, R.n, I_RESCUE),
	   RLXFW_SPI_INST_R_HDR_FLASH_AT);
	ck("rescue.cr6c on rlxboot (burnAddr)", pay(&S, S.n, I_RLXBOOT),
	   RLXFW_SPI_INST_R_HDR_FLASH_AT);
	ck("rlxboot.cr6c less two bytes", pay(&R, R.n - 2u, I_RLXBOOT),
	   RLXFW_SPI_INST_R_HDR_LEN);
	ck("rlxboot.cr6c, 15 bytes", pay(&R, 15u, I_RLXBOOT),
	   RLXFW_SPI_INST_R_HDR_LEN);
	R.p[100] ^= 0x01u;
	ck("rlxboot.cr6c with one payload bit flipped (sum16)",
	   pay(&R, R.n, I_RLXBOOT), RLXFW_SPI_INST_R_HDR_SUM);
	R.p[100] ^= 0x01u;
	ck("payload check on the barrier", pay(&R, R.n, I_BARRIER),
	   RLXFW_SPI_INST_R_ERASE_ONLY);
	ck("payload check on the probe block", pay(&R, R.n, I_PROBE),
	   RLXFW_SPI_INST_R_PROBE_ONLY);
	free(A.p); free(AF.p); free(B.p); free(AP.p); free(NF.p); free(R.p);
	free(S.p);
}

/* --------------------------------------------------- H/I: plan and cuts */

/* One bit per 4 KiB sector of the chip. */
static u8 cleared[CHIP / 0x1000u];

static void clear_marks(void)
{
	memset(cleared, 0, sizeof(cleared));
}

/* Mark what an SE at addr clears if the part's true erase size is g. */
static void se_true(u32 addr, u32 g)
{
	u32 lo = addr & ~(g - 1u), a;

	for (a = lo; a < lo + g; a += 0x1000u)
		cleared[a / 0x1000u] = 1u;
}

/* -> 1 when exactly the region's sectors are marked, no more, no less. */
static int union_is_region(const struct rlxfw_spi_inst_region *r)
{
	u32 s;

	for (s = 0; s < CHIP / 0x1000u; s++) {
		int in = s * 0x1000u >= r->base &&
			 s * 0x1000u < r->base + r->size;

		if ((int)cleared[s] != in)
			return 0;
	}
	return 1;
}

static void t_plan_one(const struct rlxfw_spi_inst_region *r, u32 len)
{
	struct rlxfw_spi_inst_plan pl;
	struct rlxfw_spi_inst_opd op;
	struct rlxfw_spi_wr_arm ae, ap, shifted;
	u32 i, nops, nE = 0, nP = 0, lastE = 0, prevpage = 0;
	u32 lines_e = 0, lines_p = 0, lines_h = 0, g;
	int order = 1, inside = 1, pol = 1, commit_last = 1, firstE = 1;
	int asc = 1, pagesafe = 1, cover = 1;
	u8 *cov;
	char nm[128];

	ck("plan_init", rlxfw_spi_inst_plan_init(&pl, r, len,
	   RLXFW_SPI_WR_ERASE_GRAIN), OK);
	nops = rlxfw_spi_inst_nops(&pl);
	cov = calloc(len ? len : 1u, 1);
	ae.armed = 1;
	ae.lo = r->base;
	ae.hi = r->base + r->size;
	ae.budget = r->size;
	ap = ae;
	for (i = 0; i < nops; i++) {
		int k = rlxfw_spi_inst_op(&pl, i, &op);

		if (op.addr < r->base || op.addr + op.len > r->base + r->size)
			inside = 0;
		if (k == RLXFW_SPI_INST_OP_ERASE) {
			if (nP)
				order = 0;	/* an erase after a program */
			if (i == 0 && op.addr != r->base)
				firstE = 0;
			if (nE && op.addr != lastE + RLXFW_SPI_WR_ERASE_GRAIN)
				asc = 0;
			lastE = op.addr;
			if (rlxfw_spi_wr_chk_erase(&ae, op.addr, op.len,
					RLXFW_SPI_WR_ERASE_GRAIN,
					RLXFW_SPI_WR_ERASE_GRAIN) !=
			    RLXFW_SPI_WR_OK)
				pol = 0;
			ae.budget -= op.len;
			nE++;
			lines_e += op.blk_end ? 1u : 0u;
		} else if (k == RLXFW_SPI_INST_OP_PROG) {
			u32 b;

			if (rlxfw_spi_wr_chk_prog(&ap, op.addr, op.len) !=
			    RLXFW_SPI_WR_OK)
				pol = 0;
			ap.budget -= op.len;
			if ((op.addr % PAGE) + op.len > PAGE || op.off >= len)
				pagesafe = 0;
			if (op.commit != (i == nops - 1u) ||
			    op.commit != (op.off == 0u))
				commit_last = 0;
			if (!op.commit && nP && op.off != prevpage + PAGE)
				asc = 0;
			prevpage = op.off;
			for (b = op.off; b < op.off + op.len && b < len; b++)
				cov[b]++;
			nP++;
			if (op.commit)
				lines_h++;
			else
				lines_p += op.blk_end ? 1u : 0u;
		} else {
			order = 0;	/* END before nops */
		}
	}
	for (i = 0; i < len; i++)
		if (cov[i] != 1u)
			cover = 0;
	free(cov);
	snprintf(nm, sizeof(nm), "D5 %s len %u: every erase before every "
		 "program", r->name, len);
	ckb(nm, order && nE == r->size / RLXFW_SPI_WR_ERASE_GRAIN &&
	    nP == (len + PAGE - 1u) / PAGE);
	snprintf(nm, sizeof(nm), "D5 %s len %u: first block first, ascending",
		 r->name, len);
	ckb(nm, firstE && asc);
	snprintf(nm, sizeof(nm), "D5 %s len %u: page 0 programmed LAST",
		 r->name, len);
	ckb(nm, len == 0u || commit_last);
	snprintf(nm, sizeof(nm), "%s len %u: every staged byte once, no page "
		 "crossed, all inside", r->name, len);
	ckb(nm, cover && pagesafe && inside);
	snprintf(nm, sizeof(nm), "%s len %u: the write policy permits every op",
		 r->name, len);
	ckb(nm, pol);
	snprintf(nm, sizeof(nm), "D10 %s len %u: one E line per 64 KiB block, "
		 "one H line", r->name, len);
	ckb(nm, lines_e == r->size / BLOCK && lines_h == (len ? 1u : 0u) &&
	    (len <= PAGE || lines_p >= 1u));

	/* D11: the cleared range under BOTH candidate sizes */
	for (g = 0x1000u; g <= 0x10000u; g <<= 4) {
		clear_marks();
		for (i = 0; i < nops; i++)
			if (rlxfw_spi_inst_op(&pl, i, &op) ==
			    RLXFW_SPI_INST_OP_ERASE)
				se_true(op.addr, g);
		snprintf(nm, sizeof(nm), "D11 %s: erased range == region if SE "
			 "clears %u", r->name, g);
		ckb(nm, union_is_region(r) && !cleared[0] &&
		    !cleared[RLXFW_SPI_WR_NEVER_HI / 0x1000u - 1u]);
	}

	/* the policy is shown refusing on the same plan: an arm one block up */
	shifted = ae;
	shifted.lo = r->base + BLOCK;
	shifted.hi = r->base + r->size + BLOCK;
	shifted.budget = r->size;
	rlxfw_spi_inst_op(&pl, 0, &op);
	snprintf(nm, sizeof(nm), "%s: an arm one block up refuses op 0 "
		 "(OUTSIDE)", r->name);
	ckb(nm, rlxfw_spi_wr_chk_erase(&shifted, op.addr, op.len,
	    RLXFW_SPI_WR_ERASE_GRAIN, RLXFW_SPI_WR_ERASE_GRAIN) ==
	    RLXFW_SPI_WR_R_OUTSIDE);
}

static void t_plan(u32 lenA)
{
	static const u32 lens[] = { 1u, 255u, 256u, 257u, 65535u, 65536u,
				    65537u, 0u };
	struct rlxfw_spi_inst_plan pl;
	struct rlxfw_spi_inst_opd op;
	u32 i, nops;
	int k;

	t_plan_one(REG(I_BARRIER), 0u);
	for (k = 0; k < NREG; k++) {
		const struct rlxfw_spi_inst_region *r = REG(k);
		int j;

		if (r->kind == RLXFW_SPI_INST_K_ERASE ||
		    r->kind == RLXFW_SPI_INST_K_PROBE)
			continue;
		for (j = 0; lens[j]; j++)
			if (lens[j] <= r->size)
				t_plan_one(r, lens[j]);
		t_plan_one(r, r->size);
	}
	t_plan_one(REG(I_SLOTA), lenA);

	/* D11's NEGATIVE CONTROL: a 64 KiB step on a part whose SE clears
	 * 4 KiB leaves 15/16 of the region unerased.  The union check must
	 * see that, or it is a check that cannot fail. */
	rlxfw_spi_inst_plan_init(&pl, REG(I_SLOTA), 0u, 0x10000u);
	nops = rlxfw_spi_inst_nops(&pl);
	clear_marks();
	for (i = 0; i < nops; i++)
		if (rlxfw_spi_inst_op(&pl, i, &op) == RLXFW_SPI_INST_OP_ERASE)
			se_true(op.addr, 0x1000u);
	ckb("D11 control: a 64 KiB step on a 4 KiB part is NOT the region",
	    !union_is_region(REG(I_SLOTA)));

	ck("plan_init: grain 0", rlxfw_spi_inst_plan_init(&pl, REG(I_SLOTA),
	   1u, 0u), RLXFW_SPI_INST_R_POLICY);
	ck("plan_init: grain 3000", rlxfw_spi_inst_plan_init(&pl,
	   REG(I_SLOTA), 1u, 3000u), RLXFW_SPI_INST_R_POLICY);
	ck("plan_init: grain below a page", rlxfw_spi_inst_plan_init(&pl,
	   REG(I_SLOTA), 1u, 128u), RLXFW_SPI_INST_R_POLICY);
	ck("plan_init: grain above a block", rlxfw_spi_inst_plan_init(&pl,
	   REG(I_SLOTA), 1u, 0x20000u), RLXFW_SPI_INST_R_POLICY);
	ck("plan_init: more bytes than the region", rlxfw_spi_inst_plan_init(
	   &pl, REG(I_RLXBOOT), 65537u, 0x1000u), RLXFW_SPI_INST_R_IMG_SIZE);
	ckb("op past the end of the plan is END",
	    rlxfw_spi_inst_plan_init(&pl, REG(I_RLXBOOT), 300u, 0x1000u) == OK
	    && rlxfw_spi_inst_op(&pl, rlxfw_spi_inst_nops(&pl), &op) ==
	    RLXFW_SPI_INST_OP_END && rlxfw_spi_inst_nops(&pl) == 16u + 2u);
}

/*
 * D5's claim, on a simulated part: a cut after ANY prefix of the sequence
 * leaves the header page NOT the new header, and the old header gone; after
 * the whole sequence the region is the staged bytes then 0xFF.  Run at both
 * candidate erase sizes, ops applied incrementally (a cut after op k is the
 * state after op k).
 */
static void t_cuts(const struct blob *img, int reg, const char *what)
{
	const struct rlxfw_spi_inst_region *r = REG(reg);
	struct rlxfw_spi_inst_plan pl;
	struct rlxfw_spi_inst_opd op;
	u8 *chip = malloc(CHIP);
	u32 i, k, nops, g, first = img->n < PAGE ? img->n : PAGE;
	int hdr_never_early, old_gone, final_ok;
	char nm[128];

	rlxfw_spi_inst_plan_init(&pl, r, img->n, RLXFW_SPI_WR_ERASE_GRAIN);
	nops = rlxfw_spi_inst_nops(&pl);
	for (g = 0x1000u; g <= 0x10000u; g <<= 4) {
		/* old content: a plausible OLD image of the same kind */
		for (i = 0; i < CHIP; i++)
			chip[i] = (u8)(i * 131u + 7u);
		memcpy(chip + r->base, img->p, 4);	/* an old magic */
		chip[r->base + 4] ^= 0x5Au;		/* but not the new one */
		hdr_never_early = old_gone = 1;
		for (k = 0; k < nops; k++) {
			rlxfw_spi_inst_op(&pl, k, &op);
			if (op.kind == RLXFW_SPI_INST_OP_ERASE) {
				u32 lo = op.addr & ~(g - 1u);

				memset(chip + lo, 0xFF, g);
			} else {
				for (i = 0; i < op.len; i++)
					chip[op.addr + i] &= img->p[op.off + i];
			}
			if (k + 1u < nops) {
				/* a cut here */
				if (!memcmp(chip + r->base, img->p, first))
					hdr_never_early = 0;
				if (chip[r->base] != 0xFFu ||
				    chip[r->base + 1] != 0xFFu ||
				    chip[r->base + 2] != 0xFFu ||
				    chip[r->base + 3] != 0xFFu)
					old_gone = 0;
			}
		}
		final_ok = !memcmp(chip + r->base, img->p, img->n);
		for (i = img->n; i < r->size; i++)
			if (chip[r->base + i] != 0xFFu)
				final_ok = 0;
		snprintf(nm, sizeof(nm), "D5 %s at %u: no cut before the last op "
			 "leaves the new header", what, g);
		ckb(nm, hdr_never_early);
		snprintf(nm, sizeof(nm), "D5 %s at %u: every cut after op 0 reads "
			 "an ERASED magic", what, g);
		ckb(nm, old_gone);
		snprintf(nm, sizeof(nm), "D5 %s at %u: complete == staged then "
			 "0xFF", what, g);
		ckb(nm, final_ok);
		/* a cut INSIDE the header page: its first m bytes only */
		if (g == 0x1000u && first > 4u) {
			u32 m = first / 2u;

			memset(chip + r->base, 0xFF, first);
			for (i = 0; i < m; i++)
				chip[r->base + i] &= img->p[i];
			snprintf(nm, sizeof(nm), "D5 %s: half a header page is not "
				 "the header", what);
			ckb(nm, memcmp(chip + r->base, img->p, first) != 0);
		}
	}
	free(chip);
}

/* ------------------------------------------------------ J: the read-back */

static void t_cmp(void)
{
	u8 img[600], got[1024];
	u32 nd = 0, first = 0, i;

	for (i = 0; i < sizeof(img); i++)
		img[i] = (u8)(i ^ 0x3Cu);
	memcpy(got, img, sizeof(img));
	memset(got + sizeof(img), 0xFF, sizeof(got) - sizeof(img));
	rlxfw_spi_inst_cmp(got, 0u, sizeof(got), img, sizeof(img), &nd, &first);
	ckb("cmp: staged then 0xFF reads equal", nd == 0u);
	got[123] ^= 0x10u;
	got[900] = 0x00u;
	nd = 0;
	rlxfw_spi_inst_cmp(got, 0u, sizeof(got), img, sizeof(img), &nd, &first);
	ckb("cmp: one staged byte and one tail byte wrong -> 2, first 123",
	    nd == 2u && first == 123u);
	nd = 0;
	rlxfw_spi_inst_cmp(got + 512, 512u, 512u, img, sizeof(img), &nd,
			   &first);
	ckb("cmp: a later chunk reports its own region offset (900)",
	    nd == 1u && first == 900u);
}

/* ---------------------------------------------- L: D19, the probe's logic */

/* One probe on a simulated 64 KiB block whose SE clears the aligned g-byte
 * block holding its address (g == 0: the opcode does nothing).  Returns the
 * classified size; *clean says whether the proven-step clean-up restored the
 * block.  The glue suite runs the DRIVER's code on the same kind of part. */
static int probe_part(u32 g, int *clean)
{
	static u8 blk[0x10000];
	u8 page[256];
	u32 i, k, off, step;
	int st[RLXFW_SPI_INST_PROBE_NMARK], sz;

	memset(blk, 0xFF, sizeof(blk));
	rlxfw_spi_inst_probe_mark(page);
	for (k = 0; k < RLXFW_SPI_INST_PROBE_NMARK; k++)
		for (i = 0; i < 256u; i++)
			blk[rlxfw_spi_inst_probe_off[k] + i] &= page[i];
	if (g)
		memset(blk, 0xFF, g);			/* the ONE SE, at +0 */
	for (k = 0; k < RLXFW_SPI_INST_PROBE_NMARK; k++)
		st[k] = rlxfw_spi_inst_probe_state(blk +
						   rlxfw_spi_inst_probe_off[k]);
	sz = rlxfw_spi_inst_probe_size(st[0], st[1], st[2]);
	step = rlxfw_spi_inst_probe_clean_step(sz);
	for (off = 0; g && step && off < sizeof(blk); off += step)
		memset(blk + (off & ~(g - 1u)), 0xFF, g);
	*clean = rlxfw_spi_inst_probe_chk_erased(blk, sizeof(blk)) == OK;
	return sz;
}

static void t_probe(void)
{
	static const int v[3] = { 'E', 'I', 'O' };
	static const u32 parts[] = { 0x1000u, 0x8000u, 0x10000u };
	u8 page[256], blk[4096];
	int a, b, c, want, ok, n, clean, sz;
	u32 i, j;
	char nm[128];

	rlxfw_spi_inst_probe_mark(page);
	ok = 1;
	for (i = 0; i < 256u; i++)
		if (page[i] == 0xFFu || page[i] == 0x00u)
			ok = 0;
	ckb("D19 marker page: no 0xFF and no 0x00 byte", ok);
	ck("chk_mark: the marker reads back", rlxfw_spi_inst_probe_chk_mark(page),
	   OK);
	page[200] ^= 1u;
	ck("chk_mark: one bit off", rlxfw_spi_inst_probe_chk_mark(page),
	   RLXFW_SPI_INST_R_PROBE_MARK);
	memset(blk, 0xFF, sizeof(blk));
	ck("chk_erased: an erased chunk", rlxfw_spi_inst_probe_chk_erased(blk,
	   sizeof(blk)), OK);
	blk[sizeof(blk) - 1] = 0xFEu;
	ck("chk_erased: one bit programmed in the last byte",
	   rlxfw_spi_inst_probe_chk_erased(blk, sizeof(blk)),
	   RLXFW_SPI_INST_R_PROBE_DIRTY);
	memset(page, 0xFF, sizeof(page));
	ckb("page state: erased is E", rlxfw_spi_inst_probe_state(page) == 'E');
	rlxfw_spi_inst_probe_mark(page);
	ckb("page state: the marker is I", rlxfw_spi_inst_probe_state(page) ==
	    'I');
	page[0] = 0xFFu;
	ckb("page state: a marker with one byte erased is O",
	    rlxfw_spi_inst_probe_state(page) == 'O');

	ok = 1;
	n = 0;
	for (a = 0; a < 3; a++)
		for (b = 0; b < 3; b++)
			for (c = 0; c < 3; c++) {
				sz = rlxfw_spi_inst_probe_size(v[a], v[b], v[c]);
				want = (a == 0 && b == 1 && c == 1) ? 4096 :
				       (a == 0 && b == 0 && c == 1) ? 32768 :
				       (a == 0 && b == 0 && c == 0) ? 65536 :
				       (a == 1 && b == 1 && c == 1) ? 0 : -1;
				if (sz != want)
					ok = 0;
				if (sz >= 0)
					n++;
			}
	ckb("D19 size table: EII EEI EEE III classify; the other 23 are -1",
	    ok && n == 4);
	ckb("clean step: each size at itself, an anomaly at 4096, a no-op never",
	    rlxfw_spi_inst_probe_clean_step(4096) == 4096u &&
	    rlxfw_spi_inst_probe_clean_step(32768) == 32768u &&
	    rlxfw_spi_inst_probe_clean_step(65536) == 65536u &&
	    rlxfw_spi_inst_probe_clean_step(-1) == 4096u &&
	    rlxfw_spi_inst_probe_clean_step(0) == 0u);
	ck("verdict: sized and clean", rlxfw_spi_inst_probe_verdict(4096, 1), OK);
	ck("verdict: a no-op part, unclean", rlxfw_spi_inst_probe_verdict(0, 0),
	   RLXFW_SPI_INST_R_PROBE_UNCLEAN);
	ck("verdict: an anomaly, cleaned", rlxfw_spi_inst_probe_verdict(-1, 1),
	   RLXFW_SPI_INST_R_PROBE_ANOMALY);
	ck("verdict: an anomaly, unclean (unclean outranks)",
	   rlxfw_spi_inst_probe_verdict(-1, 0), RLXFW_SPI_INST_R_PROBE_UNCLEAN);
	ck("verdict: clean unknown", rlxfw_spi_inst_probe_verdict(65536, -1),
	   RLXFW_SPI_INST_R_PROBE_UNCLEAN);

	for (j = 0; j < sizeof(parts) / sizeof(parts[0]); j++) {
		sz = probe_part(parts[j], &clean);
		snprintf(nm, sizeof(nm), "D19 a %u-byte part reads se_bytes=%u and "
			 "cleans at that step", parts[j], parts[j]);
		ckb(nm, sz == (int)parts[j] && clean);
	}
	sz = probe_part(0u, &clean);
	ckb("D19 a no-op part reads se_bytes=0, and the block stays unclean",
	    sz == 0 && !clean);
	/* the stated bounds, shown rather than claimed */
	sz = probe_part(0x800u, &clean);
	ckb("bound: a 2 KiB part reads 4096 and cleans -- misread silently, "
	    "which is the 256 <= S <= 4096 bound", sz == 4096 && clean);
	sz = probe_part(0x2000u, &clean);
	ckb("bound: an 8 KiB part reads 32768 and cleans: three points bound "
	    "the size, they do not measure it", sz == 32768 && clean);
}

/* ---------------------------------------------- K: what /proc can print */

static void t_emit(void)
{
	static char page[8192];
	struct rlxfw_spi_inst_st s;
	struct rlxfw_spi_inst_img im;
	struct rlxfw_spi_inst_probe pr;
	int n, w;

	memset(&s, 0, sizeof(s));
	memset(&im, 0, sizeof(im));
	memset(&pr, 0, sizeof(pr));
	n = rlxfw_spi_inst_emit(page, &s, &im, &pr, 0x20u, 0x1000u, 10000u);
	ckb("emit, nothing run: inst_ran 0, region -, cmp_first -1, phase -",
	    strstr(page, "inst_ran 0\n") && strstr(page, "inst_region -\n") &&
	    strstr(page, "inst_cmp_first -1\n") &&
	    strstr(page, "inst_phase -\n") && strstr(page, "img_err none\n") &&
	    strstr(page, "inst_erase_op 20\n") &&
	    strstr(page, "inst_erase_step 4096\n"));
	ckb("emit: no field shows a digest (no 64-hex run)",
	    strstr(page, "sha256") == NULL);
	ckb("D19 emit, never probed: the verdict line says so in its own format",
	    strstr(page, "\neraseprobe se_bytes=-1 se_polls=0 se_us=0 pp_us=0 "
		   "clean=-1\n") &&
	    strstr(page, "\neraseprobe_detail ran=0 m0000=- m1000=- m8000=- "
		   "se_jiffies=0 pp_polls=0 pp_jiffies=0 cal_polls=0 cal_ticks=0 "
		   "clean_step=0 clean_ops=0\n"));
	pr.ran = pr.classified = pr.clean_known = pr.clean = 1;
	pr.se_bytes = 4096;
	pr.se_polls = 6428u;
	pr.se_jiffies = 5u;
	pr.m[0] = 'E';
	pr.m[1] = pr.m[2] = 'I';
	n = rlxfw_spi_inst_emit(page, &s, &im, &pr, 0x20u, 0x1000u, 10000u);
	ckb("D19 emit, a 4 KiB reading: the exact verdict line",
	    strstr(page, "\neraseprobe se_bytes=4096 se_polls=6428 se_us=50000 "
		   "pp_us=0 clean=1\n") &&
	    strstr(page, " m0000=E m1000=I m8000=I "));
	memset(&pr, 0, sizeof(pr));

	/* the widest state the fields can hold */
	s.attempts = s.done = s.refused = s.failed = 0xFFFFFFFFu;
	s.r.ran = INT_MIN;
	s.r.reason = RLXFW_SPI_INST_R_PROBE_ANOMALY;	/* the longest name */
	s.r.verb = RLXFW_SPI_INST_V_PROBE;		/* the longest verb */
	s.r.region1 = I_RLXBOOT + 1;
	s.r.base = s.r.size = s.r.len = s.r.pace_ms = 0xFFFFFFFFu;
	s.r.rc = s.r.policy = s.r.arm_ok = s.r.sha_checked = INT_MIN;
	s.r.sha_ok = s.r.hdr_checked = s.r.hdr_ok = INT_MIN;
	s.r.ops_planned = s.r.ops_done = s.r.n_se = s.r.n_pp = 0xFFFFFFFFu;
	s.r.erased = s.r.programmed = 0xFFFFFFFFu;
	s.r.committed = s.r.cmp_ran = s.r.cmp_ok = INT_MIN;
	s.r.phase = 'V';
	s.r.cmp_bytes = s.r.cmp_diff = 0xFFFFFFFFu;
	s.r.cmp_first = 0x7FFFFFFFu;
	s.r.ms = 0xFFFFFFFFu;
	im.len = im.writes = im.resets = 0xFFFFFFFFu;
	im.err = RLXFW_SPI_INST_IMG_POISONED;
	pr.ran = INT_MIN;
	pr.classified = 1;
	pr.se_bytes = 65536;		/* the widest value the table yields */
	pr.m[0] = pr.m[1] = pr.m[2] = 'O';
	pr.se_polls = pr.se_jiffies = pr.pp_polls = pr.pp_jiffies = 0xFFFFFFFFu;
	pr.cal_polls = pr.cal_ticks = pr.clean_step = pr.clean_ops = 0xFFFFFFFFu;
	pr.clean_known = 0;		/* "-1", wider than 0 or 1 */
	n = rlxfw_spi_inst_emit(page, &s, &im, &pr, 0xFFFFFFFFu, 0xFFFFFFFFu,
				0xFFFFFFFFu);
	printf("  (emit worst case %d bytes, ceiling %d)\n", n,
	       RLXFW_SPI_INST_PROC_MAX);
	ckb("emit: the widest state fits RLXFW_SPI_INST_PROC_MAX",
	    n > 0 && n <= RLXFW_SPI_INST_PROC_MAX);
	w = rlxfw_spi_inst_fmt_step(page, 'E', 0xFFFFFFFFu, 0xFFFFFFFFu,
				    0xFFFFFFFFu);
	n = rlxfw_spi_inst_fmt_go(page, &s.r);
	if (n > w)
		w = n;
	s.r.reason = RLXFW_SPI_INST_R_PROBE_ANOMALY;
	n = rlxfw_spi_inst_fmt_end(page, &s.r);
	if (n > w)
		w = n;
	n = rlxfw_spi_inst_fmt_probe(page, &pr);
	if (n > w)
		w = n;
	printf("  (console line worst case %d bytes, buffer %d)\n", w,
	       RLXFW_SPI_INST_SAY_MAX);
	ckb("console lines fit RLXFW_SPI_INST_SAY_MAX",
	    w < RLXFW_SPI_INST_SAY_MAX);
	rlxfw_spi_inst_fmt_step(page, 'P', 3u, 1234u, 500u);
	ckb("D10: a paced step line says paced",
	    !strcmp(page, "RLXFW-SI P 03 1234 paced=500\n"));
	rlxfw_spi_inst_fmt_step(page, 'E', 17u, 99u, 0u);
	ckb("an unpaced step line says nothing about pace",
	    !strcmp(page, "RLXFW-SI E 17 99\n"));
}

/* ------------------------------------------- M: container.h, second source */

static void t_container_h(void)
{
#ifdef WITH_CONTAINER_H
	ckb("RLXU magic == container.h", RLXFW_SPI_INST_RLXU_MAGIC ==
	    RLXU_MAGIC);
	ckb("RLXU format == container.h", RLXFW_SPI_INST_RLXU_FORMAT ==
	    RLXU_FORMAT);
	ckb("RLXU header length == container.h",
	    RLXFW_SPI_INST_RLXU_HDR_LEN == RLXU_HDR_LEN);
	ckb("RLXU body offset == container.h",
	    RLXFW_SPI_INST_RLXU_BODY_OFF == RLXU_BODY_OFF);
	ckb("RLXU flash_at offset == container.h",
	    RLXFW_SPI_INST_RLXU_FLASH_OFF == RLXU_FLASH_OFF);
	ckb("RLXU flash_form offset == container.h",
	    RLXFW_SPI_INST_RLXU_FORM_OFF == RLXU_FORM_OFF);
	ckb("RLXU WHOL word == container.h",
	    RLXFW_SPI_INST_RLXU_FORM_WHOLE == RLXU_FORM_WHOLE);
	ckb("RLXU payload ceiling == container.h",
	    RLXFW_SPI_INST_RLXU_PAYLOAD_MAX == RLXU_PAYLOAD_MAX);
	ckb("container.h's keep-out ends at or below the region floor",
	    RLXU_FLASH_KEEPOUT_END <= RLXFW_SPI_INST_FLOOR &&
	    RLXU_FLASH_KEEPOUT_END == RLXFW_SPI_WR_NEVER_HI);
	ckb("container.h's chip size == the write policy's",
	    RLXU_CHIP_SIZE == RLXFW_SPI_WR_CHIP);
	/* The slot layout has two owners -- this header, which writes the slots,
	 * and src/rlxboot/rlxboot.h, which reads them (Gap B) -- because the
	 * kernel tree cannot include the loader's header.  So the agreement is
	 * this test's to enforce, not a sentence's. */
	ckb("rlxboot.h's slot A base == the installer's",
	    RLXB_SLOT_A_FLASH == RLXFW_SPI_INST_SLOTA_BASE);
	ckb("rlxboot.h's slot B base == the installer's",
	    RLXB_SLOT_B_FLASH == RLXFW_SPI_INST_SLOTB_BASE);
	ckb("rlxboot.h's slot size == both installer slots",
	    RLXB_SLOT_SIZE == RLXFW_SPI_INST_SLOTA_SIZE &&
	    RLXB_SLOT_SIZE == RLXFW_SPI_INST_SLOTB_SIZE);
	ckb("rlxboot.h's counter block == the installer's state block",
	    RLXB_CTR_FLASH == RLXFW_SPI_INST_STATE);
#else
	ckb("built WITHOUT container.h: the RLXU offsets have no second "
	    "source in this run", 0);
#endif
}

/* -------------------------------------------------------------- main */

/* Produced only by rtl819x-spi.c's glue, never by a pure function here
 * (SHA included: the header supplies digest_eq's boolean and the glue turns
 * it into the reason).  test-spi-install-glue.c drives each of them. */
static const int glue_only[] = {
	RLXFW_SPI_INST_R_KAT, RLXFW_SPI_INST_R_HASH, RLXFW_SPI_INST_R_SHA,
	RLXFW_SPI_INST_R_NOMEM, RLXFW_SPI_INST_R_ENGINE, RLXFW_SPI_INST_R_CMP,
	RLXFW_SPI_INST_R_ARM_READ
};

int main(int argc, char **argv)
{
	const char *dir = NULL;
	struct blob A, R, S, AF;
	int i, j, ex;

	for (i = 1; i < argc; i++) {
		if (!strcmp(argv[i], "--mutate") && i + 1 < argc)
			mutate = atoi(argv[++i]);
		else if (!strcmp(argv[i], "--fixtures") && i + 1 < argc)
			dir = argv[++i];
		else {
			fprintf(stderr, "usage: %s --fixtures DIR [--mutate N]\n",
				argv[0]);
			return 2;
		}
	}
	if (!dir) {
		fprintf(stderr, "test-spi-install: --fixtures DIR is required; "
			"tools/test-spi-install.sh builds them\n");
		return 3;
	}
	printf("test-spi-install: %s; grain %08X, page %u, floor %08X, cap %u\n",
	       RLXFW_SPI_INST_VERSION, (unsigned)RLXFW_SPI_WR_ERASE_GRAIN,
	       (unsigned)PAGE, (unsigned)RLXFW_SPI_INST_FLOOR,
	       (unsigned)RLXFW_SPI_INST_IMG_CAP);
	memset(seen, 0, sizeof(seen));

	t_table();
	t_parse();
	t_arm();
	t_img();
	t_digest();
	t_payload(dir);
	A = load(dir, "slotA.rlxu");
	AF = load(dir, "slotA-full.rlxu");
	R = load(dir, "rlxboot.cr6c");
	S = load(dir, "rescue.cr6c");
	t_plan(A.n);
	t_cuts(&A, I_SLOTA, "slotA container");
	t_cuts(&AF, I_SLOTA, "full-size slotA container");
	t_cuts(&R, I_RLXBOOT, "rlxboot cr6c");
	t_cuts(&S, I_RESCUE, "rescue cr6c");
	free(A.p); free(AF.p); free(R.p); free(S.p);
	t_cmp();
	t_probe();
	t_emit();
	t_container_h();

	/* every reason a pure function can produce is produced; the glue's
	 * five are exempt by name, and the exemption is checked both ways */
	for (i = 1; i < RLXFW_SPI_INST_R_COUNT; i++) {
		ex = 0;
		for (j = 0; j < (int)(sizeof(glue_only) / sizeof(glue_only[0]));
		     j++)
			if (glue_only[j] == i)
				ex = 1;
		if (ex && seen[i]) {
			printf("  FAIL      reason %s is exempt as glue-only but a "
			       "pure case produced it: the exemption is stale\n",
			       rn(i));
			nfail++;
		} else if (!ex && !seen[i]) {
			printf("  FAIL      reason %s is never produced: its "
			       "counter could not move\n", rn(i));
			nfail++;
		}
	}
	if (npermit < 20 || nrefuse < 20) {
		printf("  FAIL      %d permitting / %d refusing reason cases; a "
		       "guard is shown both ways\n", npermit, nrefuse);
		nfail++;
	}
	printf("reasons produced:");
	for (i = 1; i < RLXFW_SPI_INST_R_COUNT; i++)
		printf(" %s=%d", rn(i), seen[i]);
	printf("\npermitted %d, refused %d, of %d case(s)\n", npermit, nrefuse,
	       ncase);
	if (nfail) {
		printf("test-spi-install: %d FAILURE(S)\n", nfail);
		return 1;
	}
	printf("test-spi-install: all %d case(s) pass\n", ncase);
	return 0;
}
