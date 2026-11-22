---
name: pr-explainer-video
description: >-
  Turns a pull request into a 3Blue1Brown-style explainer video: an mp4 animated with manim, with
  subtitles, that builds a reviewer's mental model of what the PR changes before they read the diff.
  Use it whenever the user asks you to explain a PR, walk them through a PR or PR stack, help them
  understand a large change before reviewing it, or asks for a "3b1b", "3blue1brown" or manim video
  of code changes, even when they give only a PR URL and the word "explain" and never say "video".
compatibility: >-
  Docker (or a local manim install), git, and read access to the repository. gh helps but is
  optional.
---

# PR explainer video

The user gives you a pull request and asks you to explain it. You make a 2–8 minute video
(1080p, 60 fps, subtitles, no voice) in the style of 3Blue1Brown: a dark background, a few
shapes on screen, one idea at a time, each idea animated into place while a one-line caption
says what is happening.

The viewer is about to review the PR. They want to know what the system looks like after the PR
merges, compared with before. The video explains that end state. It does not tell the history of
the review or the order of the commits, except in the last scene, which tells them how to read
the PR.

The work takes about an hour. The final render runs in the background, at roughly 2–4 minutes
per minute of video. If you can message the user while you work, tell them this at the start, in
one line.

## What makes these videos good

These are the habits that make the videos useful to a reviewer. Keep them in mind at every
step.

- **Every fact is checked.** Every number, name, path, flag and limit on screen comes from the
  PR description, its design notes or ADRs, or the code. Nothing is guessed. An explainer with
  one invented number cannot be trusted anywhere else. Toy data is fine for a worked example if
  it is labelled as an example ("shown with 6 instead of 100").
- **A diagram must show a mechanism.** Draw like the engineer who has to live with the change,
  not like a decorator. A picture is worth drawing when it shows a reader something they would
  otherwise have to piece together from prose: where data flows, which parts talk to each
  other, what differs between before and after, which states something moves through, what a
  key contains. If a sentence says it faster, use the caption and a simpler picture.
- **Every new name gets a picture.** A PR that adds names (components, facts, stages, types)
  leaves the reader unsure what each one means. Introduce each name once, at the place it lives
  in the diagram, with a one-line meaning. Keep that position and color for the rest of the
  video.
- **Algorithms are shown working.** When the PR adds an algorithm, a rule or a decision table,
  run it on tiny concrete data, step by step. Compute the steps with the PR's own code, or a
  faithful copy of it, so every step on screen is what the code really does.
- **Be honest about size.** If the PR is large, show where the lines go (code, tests, docs,
  generated files). A reader who is told "this simplifies things" while looking at +10k lines
  will ask why.
- **Each color has one meaning.** Pick the roles once (for example measured = orange, derived =
  teal, outcome = green, refusal = red). Show a legend the first time a role matters.

## Workflow

### 0. Set up (start the image pull first)

```bash
WORK=<a scratch directory outside the repository>/video
mkdir -p "$WORK" && cp <this skill>/scripts/* "$WORK"/ && chmod +x "$WORK/pv.sh"
docker pull manimcommunity/manim:v0.22.0 &     # about 2 GB; read the PR while it downloads
```

`pv.sh` runs everything inside that image: manim, LaTeX, the Noto fonts, PyAV and Pillow. No
ffmpeg is needed on the host. Without Docker, install manim locally (it needs Cairo and Pango;
on Debian or Ubuntu: `apt install libcairo2-dev libpango1.0-dev pkg-config fonts-noto-core
fonts-noto-mono`, then `pip install manim==0.22.0`) and run `PV_NATIVE=1 ./pv.sh ...`. If the
Noto fonts are missing, Pango falls back to another font without warning, and the layout
drifts.

Never check out the PR branch in the user's working copy, which may be in use, and do not
create branches in it. Read the PR through git objects, and export its end state to the scratch
directory:

```bash
SRC="$WORK/../src" && mkdir -p "$SRC"
git fetch origin "pull/<N>/head" && HEAD_SHA=$(git rev-parse FETCH_HEAD)   # GitHub; no local branch
git fetch origin "<base branch>" && BASE_SHA=$(git rev-parse FETCH_HEAD)
git archive "$HEAD_SHA" | tar -x -C "$SRC"      # a private copy to read and run
git diff --stat "$BASE_SHA...$HEAD_SHA"         # three dots: against the merge base
```

If the PR has already merged and the main branch has since changed the same code, explain the
PR's own end state (its head against its merge base). Name the later change in one caption or
in the hand-off, so that the viewer does not mistake the video for today's code.

### 1. Read the PR and write down the facts

Read in this order, and stop reading a layer once you understand it:

1. The PR title, description, base branch and size: `gh pr view <N> --json
   title,body,baseRefName,headRefName,additions,deletions,changedFiles,commits`. Without gh,
   use the GitHub REST API (`/repos/<o>/<r>/pulls/<N>`).
2. Its place in a stack. If the base is not the main branch, the PR is a layer: name the layers
   below it in one line. If the user asks for "the whole stack", explain the top layer against
   the stack's bottom base.
3. The design docs and ADRs the PR adds or changes. They are the fastest route to the intent.
4. `git diff --stat "$BASE_SHA...$HEAD_SHA"`, then `git diff --numstat` grouped by area (source,
   tests, docs, generated files). This is the size picture.
5. The key code: new modules, the core algorithm, the public entry points, constants and limits.
6. The tests that encode the reasoning. They tell you which properties the author cares about.

While you read, keep `facts.md` in the work directory: one line per claim you might put on
screen, with its source (`file:line`, `ADR-0012`, `PR description`). Use it twice: to write the
scenes, and to check every number before the final render.

When the PR's description, a design note, an ADR or a comment says something the code does not do,
write it in a separate section of `facts.md`, "Disagreements", with both sources. Do not show either
version as a fact on screen. List these in the hand-off: the viewer is about to review the PR, and
they are often the most useful thing you found.

When the PR contains an algorithm, a rule or a validator that you will animate, run its real
code on your toy input, and save the output next to `facts.md`:

- Import the exported source (`PYTHONPATH="$SRC/..."`) with the project's own environment, if
  one exists (an existing virtualenv, `uv run`, or the project's dev container). Keep it from
  writing outside the work directory, for example with `python -B`.
- Call the smallest function that does the work. Stub out what needs infrastructure (sandboxes,
  network, Docker) when the logic you need does not depend on it.
- If the code cannot run at all, copy the function into your work directory unchanged. Check the
  copy against the PR's own tests or its examples, then drive the animation from it.

### 2. Storyboard

Write `storyboard.md`: one entry per scene, giving its title, the picture, and its captions. Read
`references/storyboard.md` for the usual arc, the scene patterns that work, how to write captions,
and how long scenes should be. Plan 10–14 scenes for a large PR and 4–8 for a small one (see
"Scaling to the PR" below). Fix the color roles and the new names now, before writing code.

### 3. Write the scenes

Write one file, `<topic>.py`, with one class per scene, in video order. Start it with:

```python
from pr3b1b import *      # manim plus the house style and helpers

C_MEAS = ORANGE           # your color roles: one meaning each
C_NEW = TEAL_C

class S00Intro(Captioned):
    def construct(self):
        ...

class S01Before(Captioned):
    def construct(self):
        self.add(badge(1, "where the work happens today"))
        ...
        self.say("Until now, every pull-request job picked its own tests.")
        ...
        self.clear_all()
```

`scripts/pr3b1b.py` is short. Read it once. It provides:

| helper | use |
|---|---|
| `T(s, size, color)`, `M(...)` | sans text, and monospace text for identifiers, paths and values from the code |
| `box`, `box2`, `chip`, `frame` | labelled box, box with a subtitle, small tag, container drawn around other objects |
| `arrow(p, q)` | arrow whose tip stays the same size however long the arrow is |
| `lines`, `code`, `place_row`, `legend`, `strike`, `bars` | text stacks, indented code, table columns, color key, strike-through, mini bar chart |
| `fit(m, w)` | shrinks to width `w`; warns when the result would be too small to read |
| `badge(k, title)` | scene number and title, top left, in every scene but the intro |
| `Captioned.say(text, wait=None, anims=[...])` | replaces the caption and holds it for its reading time; `anims` play in the same step, so a picture and its caption arrive together |
| `clear_all()`, `clear_except(...)` | end a scene, or clear the stage in the middle of one |

`references/example.py` is a complete 13-scene video for a fictional 46-file PR, which adds a
nightly smoke-test suite to a project's CI. Copy its patterns, its density and its pacing: before
and after, new names introduced one at a time, a cache key, an algorithm traced step by step,
decision tables, how to review. Do not copy its subject.

Keep content inside x ±6.9 and above y −3.1, because the caption lives below that line. Put a
scene's main content between y −2.8 and y 2.9.

Text sizes: 22–28 for body text, 18–20 for labels, and 16 for small print you could do without.
Never go below 14; the check warns there. A video that needs smaller text has too much on screen.
Split the picture across two captions instead.

### 4. Check and fix: the loop that makes it look right

```bash
cd "$WORK"
./pv.sh low topic.py                # 480p15 render with LAYOUT warnings, contact sheets in sheets/
./pv.sh check topic.py S03Facts     # warnings only, no video: for a quick look at one or two scenes
```

`low` writes `sheets/<Scene>.png` for each scene: a grid of frames, each taken at the end of a
caption's hold, so each tile shows one finished step with its caption. **Open every sheet and
look at it.**

- **The check catches** text leaving the frame, anything in the caption band, text touching or
  overlapping other text, a line, arrow or box edge passing through text, text below 14 pt, and
  labels that `fit` had to shrink too far.
- **Only your eyes catch** a box hiding another, an arrow that points at the wrong thing,
  highlight boxes of uneven width, a symbol that reads two ways (a ✓ beside "rejected"), a
  diagram that does not say what the caption says, and a step too fast to follow.

The sheets come from the 480p render, so small text looks blurrier there than it will in the
final video. Judge text by its size in the code, not by how blurry it looks on the sheet.

Fix the problems, re-render only the scenes you changed (`./pv.sh low topic.py S03Facts S07Rule`),
and look again. Repeat until no warnings are left and every sheet is clean. Usually this takes
two or three rounds. `references/manim-pitfalls.md` lists the bugs that come up again and again,
with their fixes. Read it before the first round.

Before the final render, check every number and name on screen against `facts.md`.
`./pv.sh text topic.py` prints, scene by scene, every caption and every other text the viewer sees,
with the time it appears. Read that list rather than the source: it shows what the scenes really
draw, whatever helpers built it.

### 5. Final render and hand-off

```bash
./pv.sh high topic.py      # every scene at 1080p60, then joined losslessly into topic.mp4
```

Run it in the background, because it takes about 2–4 minutes per minute of video. Then look at
frames from the joined file, to catch a scene that is missing or out of order. Pick one time inside
each scene, then open `frames/topic_strip.png`, which holds them all:

```bash
./pv.sh frames topic.mp4 20 150 280    # frames/*.png, frames/topic_strip.png, and the stats
```

Reply in a few lines:

- the absolute path of the mp4, with its length, resolution and size
- one line per scene saying what it explains
- what you checked: facts against `facts.md`, worked examples run with the PR's own code
- where the PR's words and its code disagree (the "Disagreements" in `facts.md`), as notes for the
  review
- anything you left out or are unsure about
- where the scene source is, and that the work directory is temporary if it is

## Scaling to the PR

Size the video by the number of ideas a reviewer must hold, not by the line count. Lines of
tests, docs and generated files add little. For a rough guide, use the changed lines of code
only.

- **Small PR (one or two ideas, under about 300 changed lines of code):** 4–8 scenes and 2–5
  minutes: intro, before and after, the mechanism, one worked example, how to review.
- **Large PR or stack:** 10–14 scenes and 5–8 minutes. If there are more ideas than that, leave
  the minor ones to the last scene's reading guide instead of rushing them.
- **A stack of many layers:** a layer that adds an idea gets its own scene. Layers that only move,
  rename or plumb code share one scene, or go to the reading guide. If the user wants every layer
  shown, the video may run past 8 minutes: count the captions in the storyboard (see "Pacing" in
  `references/storyboard.md`) and tell the user the length before you write the scenes.
- **PR with no runtime behavior** (docs, CI, refactor): show the structure before and after:
  moved modules, the dependency graph, which callers changed. For a refactor, show the size of
  what was removed next to what was added.
