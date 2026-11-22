#!/usr/bin/env bash
# Recomputes every figure of the powersort example from the PR's own C code.
# Downloads Objects/listobject.c at the PR's base and head, extracts powerloop(), found_new_run(),
# merge_collapse() (base) and merge_force_collapse() unchanged, compiles them into harness.c, then:
#   - prints the cost of each run list shown in the video, with the old rule and with powersort
#   - checks the Python copy in powersort_copy.py (which drives the animation) against the C
# Needs curl, a C compiler and python3. Writes only to a temporary directory.
set -euo pipefail

BASE=863154c9292e70c5a8a1a3f22ef4ee42e2304281  # main, before python/cpython#28108
HEAD=56f8ccfec7ee8a637a776be45262092867426e3e  # the PR's head
here=$(cd "$(dirname "$0")" && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cd "$work"

for ref in base:$BASE head:$HEAD; do
  curl -fsSL "https://raw.githubusercontent.com/python/cpython/${ref#*:}/Objects/listobject.c" \
    -o "listobject.${ref%%:*}.c"
done

# Print one function, from its "static" line to its closing brace, exactly as in the source.
fn() {
  awk -v name="$2" '/^static /{hdr=$0; next}
    hdr != "" && index($0, name "(") == 1 {p=1; print hdr}
    {if (p) print; if (p && /^}/) exit} {hdr=""}' "$1"
}
fn listobject.head.c powerloop > ext_powerloop.c
fn listobject.head.c found_new_run > ext_found_new_run.c
fn listobject.base.c merge_collapse > ext_merge_collapse.c
fn listobject.head.c merge_force_collapse > ext_force.c
cmp -s <(fn listobject.base.c merge_force_collapse) ext_force.c \
  && echo "merge_force_collapse(): unchanged by the PR"

cp "$here/harness.c" "$here/powersort_copy.py" "$here/check_copy.py" .
cc -O1 -Wall -Wno-unused-function -o harness harness.c

cost() { QUIET=1 ./harness "$@" | sed 's/cost //'; }
row() { printf '%-32s old %12s   powersort %12s\n' "$1" "$(cost old "${@:2}")" "$(cost new "${@:2}")"; }
N=100000000
b=$((N / 128))
row "1 2 3" 1 2 3
row "16 31 1" 16 31 1
row "4 6 2 5 9 3 3 (the toy)" 4 6 2 5 9 3 3
row "N/2, N/2-64, 64, 1" $((N / 2)) $((N / 2 - 64)) 64 1
row "(b-1)*64, 64, 64, b*64" $(((b - 1) * 64)) 64 64 $((b * 64))
echo "trace of the toy with powersort:"
./harness new 4 6 2 5 9 3 3 | sed 's/^/  /'
python3 -B check_copy.py
