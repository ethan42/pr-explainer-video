#!/usr/bin/env bash
# Checks that the layout check reports every planted problem in tests/bad_layout.py, that pv.sh text
# lists every caption and on-screen text of tests/text_dump.py, and that the worked example passes with
# no warnings, and so does examples/powersort. Needs Docker (or PV_NATIVE=1 with a local manim).
# QUICK=1 skips the two examples and the frame strip, which take a few minutes.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
skill="$here/../skills/pr-explainer-video"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cp "$skill"/scripts/* "$skill/references/example.py" "$here/bad_layout.py" "$here/text_dump.py" \
  "$here/../examples/powersort/powersort.py" "$work"/
cd "$work"

fail=0
out=$(./pv.sh check bad_layout.py)
for want in "leaves the frame" "caption band" "too small to read" "overlaps or touches" \
            "crosses the text" "fit shrinks" "caption shrunk"; do
  grep -q "$want" <<<"$out" || { echo "FAIL: bad_layout.py: no '$want' warning"; fail=1; }
done
if grep -q "crosses the text 'removed'" <<<"$out"; then
  echo "FAIL: bad_layout.py: a strike-through was reported as crossing its text"; fail=1
fi

chk=$(./pv.sh check text_dump.py)
grep -q "check: 0 layout warning" <<<"$chk" || { echo "$chk"; echo "FAIL: text_dump.py has layout warnings"; fail=1; }
txt=$(./pv.sh text text_dump.py)
c1="A step and its caption arrive in one play."
c2="Then the second step, with its 42 items."
for want in "== Steps" "$c1" "$c2" "captions and steps" "first step" "second step"; do
  grep -qF "$want" <<<"$txt" || { echo "$txt"; echo "FAIL: pv.sh text: '$want' is not listed"; fail=1; }
done
caps=$(sed -n '/^captions:/,/^on screen:/p' <<<"$txt")
l1=$(grep -nF "$c1" <<<"$caps" | cut -d: -f1 || true)
l2=$(grep -nF "$c2" <<<"$caps" | cut -d: -f1 || true)
[ -n "$l1" ] && [ -n "$l2" ] && [ "$l1" -lt "$l2" ] \
  || { echo "$txt"; echo "FAIL: pv.sh text: the captions are not listed, in order, under captions"; fail=1; }
if sed -n '/^on screen:/,$p' <<<"$txt" | grep -qF "$c1"; then
  echo "FAIL: pv.sh text: a caption is also listed as on-screen text"; fail=1
fi

if [ "${QUICK:-}" != 1 ]; then
  for ex in example.py powersort.py; do
    out=$(./pv.sh check "$ex")
    grep -q "check: 0 layout warning" <<<"$out" || { echo "$out"; echo "FAIL: $ex has layout warnings"; fail=1; }
  done
  ./pv.sh low text_dump.py >/dev/null && ./pv.sh join text_dump.py 480p15 >/dev/null \
    && ./pv.sh frames text_dump.mp4 1 3 >/dev/null
  [ -f frames/text_dump_strip.png ] || { echo "FAIL: pv.sh frames wrote no strip"; fail=1; }
fi

[ "$fail" = 0 ] && echo "ok"
exit "$fail"
