/* src/rlxboot/container.h -- the `RLXU` version 2 signed container.
 *
 * SPEC-R8a.md s2 is the format and s2's numbered list is the verification
 * order; `notes/update-chain.md` s1 holds the field table this header is
 * checked against.  This header is the contract; `container.c` is the
 * implementation and carries the argument for why the order is the order.
 *
 * FORMAT 2, 2026-10-04 (`R8b` work-order item 3).  Format 1 had 32 reserved
 * bytes at offset 64 and no flash destination anywhere in the container: the
 * destination was an optional argument to `tools/mkfw2.py` and entered no
 * signed byte, so a container built without one was indistinguishable from a
 * container whose destination had been checked -- 量, two builds differing
 * only in `--flash-at` had the same sha256.  Format 2 spends the first 8 of
 * those bytes and leaves 24 reserved:
 *
 *      64   4  flash_at   the destination this container is DECLARED for,
 *                         or RLXU_FLASH_NONE for "not for flash"
 *      68   4  flash_form WHOL: the whole 160+n container lands there
 *                         PAYL: the n payload bytes land there, prefix
 *                               stripped by the writer
 *                         NONE: no destination, so no form
 *      72  24  reserved   all zero; any non-zero byte rejects
 *
 * and `rlxu_env.write_at` / `write_form` are the other half of the
 * comparison: where, and as what, the CALLER is about to write this
 * container.  A container whose signed declaration is not that offset AND
 * that form is refused, and so is one that declares nothing -- an undeclared
 * container may never be written to flash.
 *
 * WHY THE FORM IS A SECOND SIGNED FIELD AND NOT THE WRITER'S CHOICE.  讀
 * `notes/update-chain.md` s 5-6 and `FW-168`: `rlxboot-rescue` at `0x020000`
 * is one of the six 64 KiB candidates the stock loader scans, and it MUST
 * carry a `cr6c` header there or it cannot boot -- which is the whole point
 * of a rescue slot.  量 2026-10-04: a container built over a `cr6c`-headed
 * payload reads `RLXU` at offset 0 and `cr6c` at offset 160.  So if the
 * CONTAINER lands at `0x020000` the base reads `RLXU`, `check_image()`
 * returns 0, and the rescue never boots; if the PAYLOAD lands there it does.
 * Both are correct for some destination -- a slot deliberately carries no
 * header the loader recognises -- so the choice cannot be left to whatever
 * code happens to do the write.  It is declared, it is signed, and the
 * writer's own choice is compared against it.  The landing LENGTH follows
 * from the form, and it is the length `flash_dst` bounds.
 *
 * Format 1 is refused by name at step 1.  Nothing has ever been flashed, so
 * no device holds a verifier that expects it, and reinterpreting its zero
 * bytes as "destination 0x000000" would have been reading a sentence that
 * container never said.
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
#define RLXU_FORMAT       2
#define RLXU_HDR_LEN      96
#define RLXU_SIG_LEN      64
#define RLXU_BODY_OFF     (RLXU_HDR_LEN + RLXU_SIG_LEN)   /* 160 */
#define RLXU_PAYLOAD_MAX  0x00300000UL   /* 3 MiB */
#define RLXU_VER_MIN      1UL
#define RLXU_VER_MAX      0xFFFFFFFEUL

/* Format 2's two fields, and what is left reserved after them. */
#define RLXU_FLASH_OFF    64
#define RLXU_FORM_OFF     68
#define RLXU_RESV_OFF     72
#define RLXU_RESV_LEN     24
/* "this container has no flash destination".  0xFFFFFFFF and not 0, because a
 * zeroed field must not read as a legal offset -- and 0 is the first byte of
 * the boot loader, the one destination that bricks the unit outright. */
#define RLXU_FLASH_NONE   0xFFFFFFFFUL
/* The landing form.  Printable four-byte words rather than a bit, for two
 * reasons: a hex dump of a header reads them, and a garbage header has a
 * 2-in-2^32 chance of naming a form instead of the 1-in-2 a single bit would
 * give.  NONE is zero so that it is also what a zeroed field says, which is
 * the only reading that is safe to default. */
#define RLXU_FORM_NONE    0x00000000UL
#define RLXU_FORM_WHOLE   0x57484F4CUL   /* "WHOL" -- the container lands   */
#define RLXU_FORM_PAYLOAD 0x5041594CUL   /* "PAYL" -- the payload lands     */

/* THE TWO RANGES NO LICENCE, NO FLAG AND NO CALLER CAN OPEN, and the only
 * flash numbers in this file.  量 `FLS-21`: the part is 4 MiB.  讀 CLAUDE.md
 * s Never: `0x000000`-`0x005FFF` is the boot loader and `0x006000`-`0x007FFF`
 * is `H601`, this unit's MAC and radio calibration, which no reset restores.
 * They are adjacent, so one bound covers both.
 *
 * ⚠️ THIS IS A SECOND FENCE, NOT A COPY OF THE POLICY.  `tools/flashguard.py`
 * owns the build-time ranges and this does not restate them: the rescue slot
 * and the other judgement calls are NOT here, because they are licensable and
 * this fence must not be.  What this fence covers is only the part CLAUDE.md
 * states as unconditional, so the two can differ only in the safe direction.
 * `tools/test-mkfw2.sh` `G1` reads these two constants out of this header and
 * requires them to equal what `flashguard.check_unrecoverable` enforces, so a
 * drift is a red case rather than a difference nobody looked for. */
#define RLXU_CHIP_SIZE          0x00400000UL
#define RLXU_FLASH_KEEPOUT_END  0x00008000UL

/* The anti-rollback counter: a 512-byte unary bitmap, 4,096 bits. */
#define RLXU_CTR_BYTES    512
#define RLXU_CTR_BITS     4096
/* The RAM-staged counter's magic word, "RCNT".  SPEC-R8a.md s4. */
#define RLXU_CTR_RAM_MAGIC 0x52434E54UL

/* Verdicts.  0 is accepted; every refusal has a name, and the name is what
 * `RLXBOOT-HDR bad=<field>` prints and what the host tests assert on -- so a
 * test cannot pass by getting a rejection for the wrong reason.
 *
 * The two format-2 reasons are APPENDED, so no existing reason's number
 * moves: a capture of `RLXBOOT-HDR bad=...` reads the same before and after. */
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
	RLXU_R_FLASH_DST,      /* declared flash destination is forbidden   */
	RLXU_R_FLASH_MATCH,    /* ... or is not where the caller is writing */
	RLXU_R_FLASH_FORM,     /* the form is not NONE/WHOL/PAYL, or it     */
	                       /* disagrees with whether there is a dest    */
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
	/* Where this caller is about to write the container in flash, or
	 * RLXU_FLASH_NONE when it is writing nothing, and AS WHAT -- one of
	 * the RLXU_FORM_* words.  EVERY CALLER MUST SET BOTH: a zeroed
	 * `struct rlxu_env` says "I am writing flash offset 0 in form NONE",
	 * which every container is refused against -- the fail-safe direction
	 * for a field somebody forgot. */
	unsigned long write_at;
	unsigned long write_form;
	const unsigned char *pk;              /* 32 bytes                   */
};

struct rlxu {
	/* the header, parsed.  Valid from RLXU_T_HDR onwards; a field this
	 * struct holds is a field that was range-checked or is about to be. */
	unsigned long magic, version, payload_len, load_addr, entry_addr;
	unsigned long flags, recipe_id;
	unsigned long flash_at;               /* the declared destination    */
	unsigned long flash_form;             /* ... and what lands there    */
	unsigned long flash_len;              /* how many bytes land: 0 when */
	                                      /* there is no destination     */
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
