# Example: python/cpython#28108, powersort

A video made with this skill about a real pull request:
[python/cpython#28108](https://github.com/python/cpython/pull/28108), in which Tim Peters switched
`list.sort()` to the merge order of Munro and Wild's *powersort* (merged on 6 September 2021).

**Watch it:** [powersort.mp4](https://github.com/ethan42/pr-explainer-video/releases/download/v0.1.0/powersort.mp4)
(4 min 7 s, 1080p60). The video is attached to a release rather than committed, so that clones of
this repository stay small.

| scene | what it explains |
|---|---|
| S00 | the PR, its size, and the one decision it changes |
| S01 | runs, merging neighbours, and the merge cost A + B (1, 2, 3 costs 9 or 11) |
| S02 | the old rule, `merge_collapse()`: A > B + C and B > C, its history, and the paper |
| S03 | a run's power: midpoints, dyadic ticks, and the merge tree the powers describe |
| S04 | `powerloop()`, traced on one pair, digit by digit |
| S05 | `found_new_run()`, traced on seven toy runs: cost 87, against 97 for the old rule |
| S06 | two contrived lists from the PR's comments: one bad for each rule |
| S07 | how to review the PR |

## What is here

- `powersort.py`: the scenes. Render with `pv.sh high powersort.py` from a directory that also
  holds the skill's `scripts/`.
- `facts.md`: every claim on screen, with its source (the diff, `listsort.txt`, the issue, the PR's
  comments, or a computation).
- `storyboard.md`: the plan the scenes were written from.
- `verify/`: recomputes every figure from CPython's own C. `verify/verify.sh` downloads
  `Objects/listobject.c` at the PR's base and head, extracts `powerloop()`, `found_new_run()`,
  `merge_collapse()` and `merge_force_collapse()` unchanged, compiles them with a stub
  `merge_at()`, prints the merge cost of each run list shown in the video, and checks the Python
  copy that drives the animation against the C (20,000 power computations and 2,000 merge orders).
  It needs curl, a C compiler and Python 3.

The toy run lengths are labelled as such in the video. Real runs are at least `minrun` (32 to 64)
items long.
