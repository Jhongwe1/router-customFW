/* src/rlxboot/container.h -- the `RLXU` version 1 signed container.
 *
 * SPEC-R8a.md s2 is the format and s2's numbered list is the verification
 * order.  This header is the contract; `container.c` is the implementation and
 * carries the argument for why the order is the order.
 *
 * The same two files build for the host and for the target.  Nothing in them
 * touches hardware, allocates, recurses or knows what a UART is: everything
 * environment-dependent arrives in `struct rlxu_env` and every verdict leaves
 * in `struct rlxu`.  That is what makes the bit-flip sweep and the truncation
 * sweep runnable at desk speed on exactly the code that boots the device.
 */
#ifndef RLXBOOT_CONTAINER_H
#define RLXBOOT_CONTAINER_H

#define RLXU_MAGIC        0x524C5855UL   /* "RLXU" */
#define RLXU_FORMAT       1
#define RLXU_HDR_LEN      96
#define RLXU_SIG_LEN      64
#define RLXU_BODY_OFF     (RLXU_HDR_LEN + RLXU_SIG_LEN)   /* 160 */
#define RLXU_PAYLOAD_MAX  0x00300000UL   /* 3 MiB */
#define RLXU_VER_MIN      1UL
#define RLXU_VER_MAX      0xFFFFFFFEUL

/* The anti-rollback counter: a 512-byte unary bitmap, 4,096 bits. */
#define RLXU_CTR_BYTES    512
#define RLXU_CTR_BITS     4096
/* The RAM-staged counter's magic word, "RCNT".  SPEC-R8a.md s4. */
#define RLXU_CTR_RAM_MAGIC 0x52434E54UL

/* Verdicts.  0 is accepted; every refusal has a name, and the name is what
 * `RLXBOOT-HDR bad=<field>` prints and what the host tests assert on -- so a
 * test cannot pass by getting a rejection for the wrong reason. */
enum {
	RLXU_OK = 0,
	RLXU_R_SHORT,          /* fewer than 160 bytes to read at all       */
	RLXU_R_MAGIC,
	RLXU_R_FORMAT,
	RLXU_R_HDRLEN,
	RLXU_R_VERSION,        /* outside 1..0xFFFFFFFE                     */
	RLXU_R_PAYLOAD_LEN,
	RLXU_R_FLAGS,
	RLXU_R_RESERVED,
	RLXU_R_LOAD_ADDR,
	RLXU_R_ENTRY_ADDR,
	RLXU_R_DST_SELF,       /* destination overlaps rlxboot              */
	RLXU_R_DST_BUF,        /* destination overlaps the container        */
	RLXU_R_DST_LOADER,     /* destination overlaps the stage-2 loader   */
	RLXU_R_TRUNCATED,
	RLXU_R_SIG,
	RLXU_R_DIGEST,
	RLXU_R_ROLLBACK,
	RLXU_R__COUNT
};

/* The stages, in the order they run.  `struct rlxu.trace` records the stages
 * that actually ran, and the host suite asserts the recorded sequence -- which
 * is the ONLY test that can see a reordering of the verification, because a
 * reordering changes no accept/reject verdict.  See container.c. */
enum {
	RLXU_T_HDR = 1,        /* magic, format, header_len                 */
	RLXU_T_BOUND,          /* every field bound and every overlap       */
	RLXU_T_SIG,            /* Ed25519 over header bytes 0..95           */
	RLXU_T_DIGEST,         /* SHA-256 over payload_len payload bytes    */
	RLXU_T_VER             /* version against the counter               */
};

struct rlxu_env {
	unsigned long ram_base,  ram_end;     /* [base, end)                */
	unsigned long self_base, self_end;    /* rlxboot's image and stack  */
	unsigned long buf_base,  buf_limit;   /* the container staging area */
	unsigned long ldr_base,  ldr_end;     /* stage 2's code and data    */
	unsigned long counter;                /* the anti-rollback ordinal  */
	const unsigned char *pk;              /* 32 bytes                   */
};

struct rlxu {
	/* the header, parsed.  Valid from RLXU_T_HDR onwards; a field this
	 * struct holds is a field that was range-checked or is about to be. */
	unsigned long magic, version, payload_len, load_addr, entry_addr;
	unsigned long flags, recipe_id;
	unsigned int  format, header_len;
	const unsigned char *digest;          /* 32 bytes, into the container */

	int reason;                           /* RLXU_OK or a refusal        */
	int stage;                            /* the stage that refused      */

	/* Instrumentation.  `hashed` and `copied` are the refutation
	 * conditions for "nothing is hashed or copied before the signature
	 * verifies": on any refusal at or before RLXU_T_SIG both must be 0.
	 * They are not debug aids -- `test/t_container.c` asserts them. */
	unsigned char trace[8];
	int trace_n;
	unsigned long hashed;
	unsigned long copied;
};

const char *rlxu_reason_name(int reason);

/* Called once per stage ENTERED, after that stage's checks, with reason
 * RLXU_OK when the stage passed.  It exists so the console shows which stage
 * the loader is in: Ed25519 over the header and SHA-256 over 3 MiB are each a
 * fraction of a second of silence on this core, and a payload that printed
 * everything at the end would make a hang in one of them indistinguishable from
 * a hang in the other -- on a project with one device and no spare, that
 * difference is a power cycle.  `0` is a legal argument and the host suite
 * passes it, so the verification order does not depend on anyone reporting. */
typedef void (*rlxu_report_fn)(const struct rlxu *r, int stage, int reason);

/* Verify a container.  `c` is its first byte, `avail` how many bytes are
 * guaranteed readable from there.  Copies nothing and writes nothing outside
 * `*r`.  Returns r->reason. */
int rlxu_verify(const unsigned char *c, unsigned long avail,
                const struct rlxu_env *e, struct rlxu *r,
                rlxu_report_fn rep);

/* The anti-rollback counter from a 512-byte unary bitmap: the number of zero
 * bits from the start, MSB first within each byte, bytes in address order.
 * Sets *malformed non-zero when a zero bit appears after the first one bit, in
 * which case the value returned is the TOTAL number of zero bits -- which is
 * never below the leading run, so a malformed bitmap cannot lower the floor. */
unsigned long rlxu_counter_from_bitmap(const unsigned char *bm, int *malformed);

/* Big-endian readers, exported because the test fixtures build headers with
 * them and a fixture that used a different byte order from the parser would
 * make the whole suite agree with itself and with nothing else. */
unsigned long rlxu_be32(const unsigned char *p);
unsigned int  rlxu_be16(const unsigned char *p);

#endif /* RLXBOOT_CONTAINER_H */
