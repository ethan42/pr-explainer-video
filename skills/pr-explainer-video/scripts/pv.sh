#!/usr/bin/env bash
# pv.sh: render, check and join a PR explainer video.
# Run it from the work directory that holds the scene file, pr3b1b.py and pvtool.py.
#
#   pv.sh check  FILE.py [Scene...]   run scenes without rendering; print LAYOUT warnings
#   pv.sh text   FILE.py [Scene...]   run scenes without rendering; print every caption and on-screen text
#   pv.sh low    FILE.py [Scene...]   render at 480p15 with the layout check on, then build sheets/*.png
#   pv.sh sheets FILE.py [Scene...]   rebuild contact sheets from the 480p15 renders
#   pv.sh high   FILE.py              render every scene at 1080p60 and join them into FILE.mp4
#   pv.sh join   FILE.py [QUALITY]    join already rendered scenes (QUALITY: 480p15 or 1080p60)
#   pv.sh frames VIDEO.mp4 T...       save the frames at times T (seconds) to frames/, one strip of them all,
#                                     and print the video's stats
#
# Uses the manimcommunity/manim Docker image when docker is available, else a local manim
# (PV_NATIVE=1 forces local; PV_PYTHON picks its interpreter; PV_IMAGE overrides the image).
set -euo pipefail

IMAGE=${PV_IMAGE:-manimcommunity/manim:v0.22.0}  # amd64 and arm64; the version the helpers were tested on
PY=${PV_PYTHON:-python3}

[ $# -ge 2 ] || { sed -n '2,15p' "$0"; exit 2; }
cmd=$1
file=$2
shift 2
stem=$(basename "$file" .py)
stem=${stem%.mp4}
[ -f "$file" ] || { echo "no such file: $file" >&2; exit 2; }
[ -f pr3b1b.py ] && [ -f pvtool.py ] || { echo "copy pr3b1b.py and pvtool.py into $PWD first" >&2; exit 2; }

docker_ok() { [ "${PV_NATIVE:-}" != 1 ] && command -v docker >/dev/null 2>&1; }

# Run a command in an environment that has manim, PyAV and Pillow.
run() {
  if docker_ok; then
    docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e PYTHONPATH=/manim \
      -e PV_CHECK="${PV_CHECK:-}" -v "$PWD:/manim" -w /manim "$IMAGE" "$@"
  else
    PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}" "$@"
  fi
}

manim_() { if docker_ok; then run manim "$@"; else run "$PY" -m manim "$@"; fi; }
tool() { if docker_ok; then run python pvtool.py "$@"; else run "$PY" pvtool.py "$@"; fi; }

all_scenes() { tool scenes "$file"; }
scenes_or_all() { if [ $# -gt 0 ]; then echo "$@"; else all_scenes | tr '\n' ' '; fi; }

# Run the scenes with the layout check on but without rendering; leaves manim's output in $out.
dry_run() {
  # shellcheck disable=SC2046
  out=$(PV_CHECK=1 manim_ -ql -s --dry_run --disable_caching --progress_bar none "$file" $(scenes_or_all "$@") 2>&1) || {
    echo "$out" | tail -40; exit 1; }
}

case $cmd in
  check)
    dry_run "$@"
    n=$(echo "$out" | grep -c '^LAYOUT' || true)
    echo "$out" | grep '^LAYOUT' || true
    echo "check: $n layout warning(s)"
    ;;
  text)
    dry_run "$@"
    for s in $(scenes_or_all "$@"); do cat "sheets/text/$s.txt"; done
    ;;
  low)
    # shellcheck disable=SC2046
    PV_CHECK=1 manim_ -ql --disable_caching --progress_bar none "$file" $(scenes_or_all "$@") 2>&1 | tee ".pv-low-$stem.log" \
      | { grep -v '^LAYOUT' || true; }
    # shellcheck disable=SC2046
    tool sheets "media/videos/$stem/480p15" sheets $(scenes_or_all "$@")
    n=$(grep -c '^LAYOUT' ".pv-low-$stem.log" || true)
    grep '^LAYOUT' ".pv-low-$stem.log" || true
    echo "low: $n layout warning(s); contact sheets in sheets/"
    ;;
  sheets)
    # shellcheck disable=SC2046
    tool sheets "media/videos/$stem/480p15" sheets $(scenes_or_all "$@")
    ;;
  high)
    manim_ -qh --disable_caching --progress_bar none -a "$file"
    # shellcheck disable=SC2046
    tool join "media/videos/$stem/1080p60" "$stem.mp4" $(all_scenes)
    tool info "$stem.mp4"
    ;;
  frames)
    tool frames "$file" frames "$@"
    tool info "$file"
    ;;
  join)
    q=${1:-1080p60}
    # shellcheck disable=SC2046
    tool join "media/videos/$stem/$q" "$stem.mp4" $(all_scenes)
    ;;
  *)
    sed -n '2,15p' "$0"; exit 2 ;;
esac
