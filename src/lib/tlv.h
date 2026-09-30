/* tlv.h -- the bounded TLV reader and writer SPEC-R7 § 5 puts under the config
 * record: `type u16 BE, len u16 BE, value[len]`, no padding, ids strictly
 * ascending.
 *
 * ---------------------------------------------------------------------------
 * WHY THIS FILE IS SEPARATE FROM cfg.c
 * ---------------------------------------------------------------------------
 *
 * The vendor defect this replaces (plan D8, CVE-2024-21778's shape) is a TLV
 * length taken from the buffer and handed to `memcpy`.  The fix is not "check
 * the length before that one memcpy" -- it is that nothing in this project
 * ever sees a length that has not already been checked against the bytes that
 * remain.  So the check lives in one function, `tlv_next`, which is the only
 * way any caller gets a `(type, len, value)` triple, and `value` is a pointer
 * INTO the caller's buffer with `len` bytes proven to be there.
 *
 * Consequences that are deliberate:
 *   * `tlv_next` never copies.  A caller that wants a copy bounds its own
 *     destination; the reader cannot overrun a destination it does not know.
 *   * The reader holds the previous id and refuses one that is not strictly
 *     greater.  Duplicate ids are therefore impossible to represent, which is
 *     stronger than "the last one wins" and removes the class of bug where an
 *     encoder and a decoder disagree about which duplicate is live.
 *   * `pos <= len` is an invariant, asserted by construction: every advance is
 *     by an amount already proven to fit.  `len - pos` is therefore never a
 *     wrapped subtraction, and that is the only reason the size_t arithmetic
 *     below is safe to read as arithmetic.
 *
 * ---------------------------------------------------------------------------
 * WHAT IT DOES NOT DO
 * ---------------------------------------------------------------------------
 *
 * It does not know the schema.  A length that fits the buffer but is wrong for
 * the id's type is `cfg.c`'s refusal, not this file's.  It does not validate
 * value bytes.  And it is not a defence against an attacker who can choose the
 * bytes AND the buffer length reported to it: `tlv_reader_init` is trusted on
 * `len`, which is why cfg.c derives that length from the record header only
 * after the header's own CRC has been checked.
 */
#ifndef RLXFW_TLV_H
#define RLXFW_TLV_H

#include <stddef.h>
#include <stdint.h>

#define TLV_HDR_LEN 4		/* type u16 + len u16 */

enum {
	TLVE_OK = 0,
	TLVE_TRUNC = 1,		/* a header or a value ran past the buffer */
	TLVE_ORDER = 2,		/* ids not strictly ascending */
	TLVE_SPACE = 3,		/* writer: the destination is full */
	TLVE_ARG = 4		/* a NULL argument or an impossible request */
};

struct tlv_reader {
	const uint8_t *buf;
	size_t len;
	size_t pos;		/* invariant: pos <= len */
	uint16_t last;
	int started;
};

struct tlv_writer {
	uint8_t *buf;
	size_t cap;
	size_t pos;		/* invariant: pos <= cap */
	uint16_t last;
	int started;
};

/* Big-endian accessors.  Every integer that reaches a disk or a wire goes
 * through these four functions; nothing in this project casts a struct. */
uint16_t tlv_get_be16(const uint8_t *p);
uint32_t tlv_get_be32(const uint8_t *p);
void tlv_put_be16(uint8_t *p, uint16_t v);
void tlv_put_be32(uint8_t *p, uint32_t v);

void tlv_reader_init(struct tlv_reader *r, const uint8_t *buf, size_t len);

/* 0  a TLV was read; *val points into the reader's buffer, *len bytes valid.
 * 1  clean end: every byte of the buffer was consumed by complete TLVs.
 * -TLVE_TRUNC  a length ran past the buffer, or a partial header remains.
 * -TLVE_ORDER  the id is not strictly greater than the previous one.
 * After any negative return the reader is not usable again. */
int tlv_next(struct tlv_reader *r, uint16_t *type, uint16_t *len,
	     const uint8_t **val);

void tlv_writer_init(struct tlv_writer *w, uint8_t *buf, size_t cap);

/* 0 on success, -TLVE_ORDER if `type` is not strictly ascending,
 * -TLVE_SPACE if TLV_HDR_LEN + len would not fit, -TLVE_ARG on a NULL value
 * with a non-zero len.  Nothing is written on any failure. */
int tlv_write(struct tlv_writer *w, uint16_t type, const uint8_t *val,
	      uint16_t len);

size_t tlv_writer_len(const struct tlv_writer *w);

#endif /* RLXFW_TLV_H */
