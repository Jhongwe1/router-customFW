#!/usr/bin/env python3
"""src/brokerd/mutate.py -- plant one named defect in a COPY of a source file.

The real sources never carry a mutation switch: every mutant is a copy made
here, so nothing that could be flipped ships.  Each mutation REFUSES unless its
anchor matches exactly once, because a sed that silently matched nothing turns a
mutation run into a green line that means nothing.

    mutate.py <name> <src> <dst>
"""
import sys

MUTATIONS = {
    # The constant-time compare given an early exit.  Functionally identical,
    # so the unit suite must NOT catch it -- that is the point of having it.
    "early": (
        "\tfor (i = 0; i < n; i++)\n"
        "\t\td = (unsigned char)(d | (unsigned char)(p[i] ^ q[i]));\n",
        "\tfor (i = 0; i < n; i++) {\n"
        "\t\td = (unsigned char)(d | (unsigned char)(p[i] ^ q[i]));\n"
        "\t\tif (d != 0)\n\t\t\tbreak;\n"
        "\t}\n",
    ),
    # The body_len bound removed: an attacker's 32-bit length reaches the copy.
    "nobound": (
        "\tif (blen > PROTO_REQ_BODY_MAX)\n\t\treturn PROTO_E_BODYLEN;\n",
        "\tif (0)\n\t\treturn PROTO_E_BODYLEN;\n",
    ),
    # One byte past the end: the classic off-by-one, for the fuzzer.
    "off1": (
        "\tif (blen > PROTO_REQ_BODY_MAX)\n",
        "\tif (blen > PROTO_REQ_BODY_MAX + 1)\n",
    ),
    # ---- the update path (update.c, loop.c; `make mutants-update`) -------
    # Staged for flash before the checks pass: every DATA piece forwarded to
    # the kernel's image node as it arrives, before END has judged anything.
    "upd_stage_early": (
        "\tmemcpy(u->buf + u->received, rq->body + 4, n);\n"
        "\tu->received += n;\n",
        "\tmemcpy(u->buf + u->received, rq->body + 4, n);\n"
        "\t(void)spictl_stage(&spictl_dev, rq->body + 4, n);\n"
        "\tu->received += n;\n",
    ),
    # BEGIN without its handoff check: a RAM boot receives the body.
    "upd_no_handoff_begin": (
        "\tif (upd_handoff(bk, &run, &ver) != 0)\n"
        "\t\treturn upd_refuse(bk, rs, ST_INVAL, R_HANDOFF);\n",
        "\t(void)upd_handoff(bk, &run, &ver);\n",
    ),
    # END without its handoff check (step 2).
    "upd_no_handoff_end": (
        "\tif (upd_handoff(bk, &run, &ver) != 0)\n"
        "\t\treturn upd_end_refuse(bk, rs, ST_INVAL, R_HANDOFF);\n",
        "\t(void)upd_handoff(bk, &run, &ver);\n",
    ),
    # The install run although END's reply never reached the client.
    "upd_install_undelivered": (
        "\t\tc->install_after_write = 0;\n"
        "\t\t(void)bk_upd_after_reply(bk, 0);\n",
        "\t\tc->install_after_write = 0;\n"
        "\t\t(void)bk_upd_after_reply(bk, 1);\n",
    ),
    # The reboot after an install that failed.
    "upd_reboot_failed": (
        "\tif (upd_install(bk, &lockfd) != 0) {\n"
        "\t\tupd_note(bk, R_INSTALL);\n"
        "\t\tbk_upd_discard(bk);\n"
        "\t\treturn -1;\n"
        "\t}\n",
        "\tif (upd_install(bk, &lockfd) != 0) {\n"
        "\t\tupd_note(bk, R_INSTALL);\n"
        "\t}\n",
    ),
    # The n_writes count not checked after the install.
    "upd_no_nwrites": (
        "\tif ((unsigned long)(uint32_t)(nw1 - nw0) != want) {\n",
        "\tif (0) {\n",
    ),
    # A looser environment than rlxboot's: its own range left empty.
    "upd_env_loose_self": (
        "\te->self_end   = UPD_SELF_END;\n",
        "\te->self_end   = UPD_SELF_BASE;\n",
    ),
    # ... and stage 2's window left empty.
    "upd_env_loose_ldr": (
        "\te->ldr_end    = RLXB_LDR_END;\n",
        "\te->ldr_end    = RLXB_LDR_BASE;\n",
    ),
    # A poison that does not stick: the next DATA in sequence is taken.
    "upd_no_poison": (
        "\tfree(bk->upd.buf);\n"
        "\tbk->upd.buf = 0;\n"
        "\tbk->upd.state = BK_UPD_POISONED;\n",
        "\t(void)bk;\n",
    ),
}


def main(argv):
    if len(argv) != 4:
        sys.stderr.write(__doc__)
        return 2
    name, src, dst = argv[1], argv[2], argv[3]
    if name not in MUTATIONS:
        sys.stderr.write("mutate.py: REFUSED: unknown mutation %r; have %s\n"
                         % (name, ", ".join(sorted(MUTATIONS))))
        return 2
    old, new = MUTATIONS[name]
    with open(src, "r", encoding="utf-8") as f:
        text = f.read()
    n = text.count(old)
    if n != 1:
        sys.stderr.write("mutate.py: REFUSED: anchor for %r matches %d times in "
                         "%s, want exactly 1\n" % (name, n, src))
        return 1
    out = text.replace(old, new, 1)
    if out == text:
        sys.stderr.write("mutate.py: REFUSED: %r changed nothing\n" % name)
        return 1
    tmp = dst + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(out)
    import os
    os.replace(tmp, dst)
    sys.stdout.write("mutate.py: planted %s in %s\n" % (name, dst))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
