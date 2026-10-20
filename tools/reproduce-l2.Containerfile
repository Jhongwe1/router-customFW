# reproduce-l2.Containerfile -- the image REPRODUCE.md's layer 2 runs layer 1
# in.  Build it with `bash tools/reproduce-l2.sh image`, which tags it by this
# file's sha256 and reads every pin below back out of the result.  Written for
# podman and docker alike; only rootless podman 4.9.3 has built it.
#
# Nothing of this repository, the release or the drops is copied in: they are
# mounted read-only at run time, with no network.  The image holds an
# operating system and the host programs the build runs, and nothing else.

# The base, by digest: the linux/amd64 manifest that docker.io/library/ubuntu:24.04
# resolved to on 2026-10-20 (Ubuntu 24.04.5; the tag's index was
# sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac).
# amd64 because the drop's toolchain, lzma and cvimg are i386 programs.
FROM docker.io/library/ubuntu@sha256:a2d43bffc46670d7108bb3c0468c67c5557c4c92e83e1e34cbff1322ad1b94dc

# Packages: one dated snapshot of the Ubuntu archive, and each named package
# at the exact version that snapshot serves, so apt refuses rather than
# substitutes; the snapshot also fixes every dependency apt resolves.
# snapshot.ubuntu.com answers only over HTTPS and the base image carries no CA
# bundle, so the TLS peer is not verified: apt checks every index and package
# against the InRelease files signed by the archive key the base image holds,
# as it does over plain HTTP.  Check-Valid-Until is off: a snapshot is old by
# design.
#   gcc, libc6-dev, make, perl, gawk  the kernel's and busybox's host programs
#   python3                           the archive's tools (and this repository's)
#   git                               the pin checks and the sparse clones
#   patch, xz-utils, file, binutils   the archive's scripts and the unpacking
#   libc6-i386, lib32gcc-s1,          the i386 toolchain's loader and libraries,
#   lib32stdc++6                      and lzma-26's C++ runtime
# `awk` is gawk once gawk is installed, as on the machine that built v1.0.
RUN set -eu; \
    rm -f /etc/apt/sources.list /etc/apt/sources.list.d/*; \
    printf '%s\n' 'Types: deb' \
        'URIs: https://snapshot.ubuntu.com/ubuntu/20261019T000000Z/' \
        'Suites: noble noble-updates noble-security' \
        'Components: main universe' \
        'Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg' \
        > /etc/apt/sources.list.d/snapshot.sources; \
    apt-get -o Acquire::https::Verify-Peer=false -o Acquire::Check-Valid-Until=false update; \
    DEBIAN_FRONTEND=noninteractive apt-get -o Acquire::https::Verify-Peer=false \
        install -y --no-install-recommends \
        binutils=2.42-4ubuntu2.10 \
        file=1:5.45-3build1 \
        gawk=1:5.2.1-2ubuntu0.1 \
        gcc=4:13.2.0-7ubuntu1 \
        git=1:2.43.0-1ubuntu7.3 \
        lib32gcc-s1=14.2.0-4ubuntu2~24.04.1 \
        lib32stdc++6=14.2.0-4ubuntu2~24.04.1 \
        libc6-dev=2.39-0ubuntu8.9 \
        libc6-i386=2.39-0ubuntu8.9 \
        make=4.3-4.1build2 \
        patch=2.7.6-7build3 \
        perl=5.38.2-3.2ubuntu0.6 \
        python3=3.12.3-0ubuntu2.1 \
        xz-utils=5.6.1+really5.4.5-1ubuntu0.3 \
        ; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*; \
    git config --system safe.directory '*'; \
    mkdir -p /usr/share/rlxfw-l2; \
    dpkg-query -W -f '${Package}\t${Version}\t${Architecture}\n' | LC_ALL=C sort \
        > /usr/share/rlxfw-l2/dpkg.tsv

# safe.directory: the inputs are mounted read-only and owned by another user
# than the one the build runs as, which git otherwise refuses to read.
# dpkg.tsv: every installed package and version, which each run prints the
# sha256 of.
