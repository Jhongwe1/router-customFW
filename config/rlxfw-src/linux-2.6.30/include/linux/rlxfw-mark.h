/*
 * rlxfw's boot marks.   R3-6.   THIS FILE IS NOT REALTEK'S.
 *
 * Staged into include/linux/ by tools/rlxfw-marks.py alongside
 * arch/rlx/kernel/rlxfw_mark.c, which is where the reasoning lives.
 *
 * There is a header at all because arch/rlx/kernel/Makefile carries
 * `EXTRA_CFLAGS += -Werror`, so an implicit declaration at the B1/B2/B3/B8
 * call sites is a hard build failure -- which is the correct outcome and not
 * one to work around by dropping the prototype.
 *
 * 🔴 WHY THESE ARE MACROS AND NOT FUNCTIONS, WHICH IS NOT A STYLE CHOICE.
 * The first version took the tag as an argument:
 *
 *     void rlxfw_mark(const char *tag) { puts("RLXFW-"); puts(tag); ... }
 *
 * It compiled, it linked, `rlxfw-marks.py check` was green on the staged tree,
 * and it would have printed the right bytes on the wire.  量:
 * `rlxfw-marks.py verify` read the built vmlinux and found the string
 * `RLXFW-B0` **zero** times -- because "RLXFW-" and "B0" are two separate
 * literals and the bytes are never contiguous in the image.
 *
 * That matters because a mark is only a discriminator if it can be checked
 * BEFORE the power cycle.  `RUNSHEET` P6's whole shape is: present once in
 * mine, absent from the vendor's, read at the desk.  A mark that exists only
 * as two fragments cannot be checked that way, and the seating would have
 * gone ahead on marks nobody had confirmed were in the image.
 *
 * Concatenating the literals at the call site makes each mark one contiguous
 * string constant in .rodata, which is what `verify` reads.
 */
#ifndef _LINUX_RLXFW_MARK_H
#define _LINUX_RLXFW_MARK_H

/* Write a NUL-terminated string synchronously to UART0 through prom_putchar,
 * translating \n to \r\n.  Safe from the first C instruction of the kernel:
 * no console, no log buffer, no lock, and a busy loop Realtek bounds at
 * 30,000 spins so it cannot hang. */
void rlxfw_puts(const char *s);

/* The same, then eight upper-case hex digits and a newline. */
void rlxfw_puts_hex(const char *s, unsigned int v);

/* One line: "RLXFW-<tag>\r\n", as a single .rodata literal. */
#define rlxfw_mark(tag)		rlxfw_puts("RLXFW-" tag "\n")

/* "RLXFW-<tag>=XXXXXXXX\r\n", the prefix again one literal.  Used where the
 * value is the finding -- B2 prints PRId, B7 prints the return code that
 * otherwise disappears into a bare while(1). */
#define rlxfw_markx(tag, v)	rlxfw_puts_hex("RLXFW-" tag "=", \
					       (unsigned int)(v))

#endif /* _LINUX_RLXFW_MARK_H */
