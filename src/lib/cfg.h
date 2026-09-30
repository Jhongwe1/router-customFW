/* cfg.h -- the config store: SPEC-R7 § 4 (schema) and § 5 (record and store).
 * The declarations between the two PINNED markers are copied from SPEC-R7 § 5
 * and must not change shape; everything else in this header is an addition.
 *
 * ---------------------------------------------------------------------------
 * THE THREE VENDOR DEFECTS THIS REPLACES (plan D8)
 * ---------------------------------------------------------------------------
 *
 *   1. Plaintext credentials (CVE-2019-19823).  There is no plaintext key in
 *      the schema.  `admin.pwhash` is 56 bytes of KDF output and is the only
 *      WEB_HIDDEN key; `cfg_value_to_text` REFUSES a hidden key, so the one
 *      function that turns a value into something printable cannot be the
 *      thing that leaks it.
 *   2. One write clobbering both regions (D-10).  Two slots, and `cfg_store`
 *      writes only the one that does not hold the record currently selected.
 *      A torn write therefore destroys a slot nobody is reading.
 *   3. A TLV length straight into memcpy (CVE-2024-21778's shape).  See tlv.h.
 *
 * And the fourth, which is a behaviour rather than a bug: both regions bad
 * meant "load defaults and open telnet" (D-13, fail-open).  Here both slots
 * bad means defaults with `source == 0`, and `admin.pwhash` has no default, so
 * a caller that authenticates against it cannot authenticate at all.  That is
 * the whole fail-closed claim, and it is a property of the schema (no default)
 * rather than of any code path that could be forgotten.
 *
 * ---------------------------------------------------------------------------
 * ON-DISK RECORD (all big-endian, no struct is ever cast onto these bytes)
 * ---------------------------------------------------------------------------
 *
 *   off size field
 *     0    4 magic 0x524C5843 "RLXC"
 *     4    2 format = 1
 *     6    2 header length = 24
 *     8    4 seq, 1..0xFFFFFFFE  (0 and 0xFFFFFFFF are invalid: erased NOR
 *            reads 0xFF, so the all-ones record must not be a valid one)
 *    12    4 payload length, <= CFG_SLOT_SIZE - CFG_HDR_LEN
 *    16    4 payload CRC-32
 *    20    4 header CRC-32 over bytes 0..19
 *    24  ... payload: TLVs, ids strictly ascending
 *
 * The record's extent is CFG_HDR_LEN + payload length.  Bytes of the slot past
 * that are fill and are not examined -- `cfg_store` writes 0xFF there so that
 * the image is what an erased-then-written NOR sector will hold in R8.
 */
#ifndef RLXFW_CFG_H
#define RLXFW_CFG_H

#include <stddef.h>
#include <stdint.h>

/* ----- PINNED (SPEC-R7 § 5) ---------------------------------------------- */
#define CFG_SLOT_SIZE 4096
#define CFG_VAL_MAX   64
/* ----- end of the pinned defines; CFG_NKEYS follows § 4's row count ------ */

#define CFG_NKEYS     16
#define CFG_HDR_LEN   24
#define CFG_MAGIC     0x524C5843u	/* "RLXC" */
#define CFG_FORMAT    1
#define CFG_NSLOTS    2
#define CFG_FILE_SIZE (CFG_NSLOTS * CFG_SLOT_SIZE)
#define CFG_SEQ_MIN   1u
#define CFG_SEQ_MAX   0xFFFFFFFEu
#define CFG_FILL      0xFFu

/* Longest text form any value can take, plus the NUL.  The widest is a
 * 56-byte BYTES value rendered as hex (112 characters), which only
 * cfg_value_to_hex produces; 32-character hostnames and "255.255.255.255" are
 * far below it.  Every buffer in the CLI is sized from this. */
#define CFG_TEXT_MAX  (2 * CFG_VAL_MAX + 1)

/* ----- PINNED (SPEC-R7 § 5) ---------------------------------------------- */
struct cfg_key {
	uint16_t id;
	const char *name;
	uint8_t type;
	uint8_t web;
	uint32_t min, max;
};

enum { CT_BOOL = 1, CT_U16, CT_U32, CT_IPV4, CT_STR, CT_ENUM, CT_BYTES };
enum { WEB_HIDDEN = 0, WEB_R = 1, WEB_RW = 2 };

struct cfg {
	uint32_t seq;
	int source;		/* 0 defaults, 1 slot 0, 2 slot 1 */
	uint8_t present[CFG_NKEYS];
	uint16_t len[CFG_NKEYS];
	uint8_t val[CFG_NKEYS][CFG_VAL_MAX];
};
/* ----- end PINNED -------------------------------------------------------- */

/* Errors.  Every function returns 0 (or a byte count) or the negation of one
 * of these.  CFGE_OK is never returned negated. */
enum {
	CFGE_OK = 0,
	CFGE_SHORT = 1,		/* fewer bytes than the header or the record needs */
	CFGE_MAGIC,		/* not "RLXC" */
	CFGE_FORMAT,		/* format or header length is not this version's */
	CFGE_CRC,		/* a CRC field does not match the bytes it covers */
	CFGE_SEQ,		/* seq is 0 or 0xFFFFFFFF, or the space is exhausted */
	CFGE_LEN,		/* payload length is impossible for the slot */
	CFGE_TLV,		/* the TLV walk refused: truncation or trailing bytes */
	CFGE_ORDER,		/* ids not strictly ascending */
	CFGE_UNKNOWN,		/* an id the schema does not have */
	CFGE_TYPE,		/* a length that is wrong for the id's type */
	CFGE_RANGE,		/* a value outside the id's bounds */
	CFGE_CROSS,		/* a cross-field rule */
	CFGE_NOENT,		/* absent, and there is no default */
	CFGE_IO,		/* open/read/write/fsync, or a read-back mismatch */
	CFGE_SPACE,		/* the destination buffer is too small */
	CFGE_PERM,		/* refused: a hidden value may not be rendered */
	CFGE_NAME,		/* no such key name */
	CFGE_TEXT,		/* the text is not a value of this type */
	CFGE_LAST
};

/* ----- PINNED (SPEC-R7 § 5) ---------------------------------------------- */
const struct cfg_key *cfg_key_by_id(uint16_t id);
const struct cfg_key *cfg_key_by_name(const char *name);
int  cfg_defaults(struct cfg *c);
int  cfg_parse_record(const uint8_t *buf, size_t n, struct cfg *out);
int  cfg_encode_record(const struct cfg *c, uint32_t seq, uint8_t *buf, size_t n);
int  cfg_load(const char *path, struct cfg *out);
int  cfg_store(const char *path, struct cfg *c);
int  cfg_get(const struct cfg *c, uint16_t id, uint8_t *v, uint16_t *len);
int  cfg_set(struct cfg *c, uint16_t id, const uint8_t *v, uint16_t len);
int  cfg_validate(const struct cfg *c);
int  cfg_text_to_value(const struct cfg_key *k, const char *text, uint8_t *v,
		       uint16_t *len);
int  cfg_value_to_text(const struct cfg_key *k, const uint8_t *v, uint16_t len,
		       char *out, size_t n);
/* ----- end PINNED -------------------------------------------------------- */

/* Additions.  SPEC-R7 § 5 permits functions to be added, not changed. */

/* The key id the last refusal was about, or 0.  Set by cfg_parse_record,
 * cfg_set, cfg_validate and cfg_encode_record.  Single-process, no threads
 * (SPEC-R7 § 2), so a file-static is the whole mechanism. */
uint16_t cfg_last_key(void);

const char *cfg_strerror(int rc);		/* rc may be negative or positive */

int cfg_index_by_id(uint16_t id);		/* 0..CFG_NKEYS-1, or -CFGE_UNKNOWN */
int cfg_present(const struct cfg *c, uint16_t id);	/* 1, 0, or -CFGE_UNKNOWN */
int cfg_unset(struct cfg *c, uint16_t id);	/* the key reverts to its default */

/* Renders BYTES (and anything else) as lower-case hex.  This is the only way
 * to print a WEB_HIDDEN value; cfg_value_to_text refuses one.  Callers that
 * are not tests or `dump` must not use it. */
int cfg_value_to_hex(const uint8_t *v, uint16_t len, char *out, size_t n);

/* What cfg_load found, for a caller that must tell "no store yet" from "a
 * store that is there and broken".  rc[i] is 0 or -CFGE_* for slot i. */
struct cfg_store_info {
	size_t file_bytes;
	int rc[CFG_NSLOTS];
	uint32_t seq[CFG_NSLOTS];
	int selected;		/* 0 none, 1 slot 0, 2 slot 1 */
};

int cfg_load_info(const char *path, struct cfg *out, struct cfg_store_info *info);

/* Builds the CFG_SLOT_SIZE-byte image `cfg_store` would write: the record then
 * 0xFF fill.  Exposed so that the torn-write sweep writes exactly the bytes
 * the store writes, rather than a test's idea of them. */
int cfg_slot_image(const struct cfg *c, uint32_t seq, uint8_t *img, size_t n);

#endif /* RLXFW_CFG_H */
