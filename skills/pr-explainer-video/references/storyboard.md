# Storyboarding a PR explainer

## Contents
1. The arc
2. Scene patterns
3. Captions
4. Pacing
5. A storyboard entry

## 1. The arc

Most PRs fit this order. Drop what does not apply, and split a middle scene that holds two
ideas.

| # | scene | what it does |
|---|---|---|
| 0 | **Intro** | Title, PR number, one-line purpose. Its place in a stack, if there is one. Size: commits, +/− lines, files, new docs or ADRs. One caption saying the video shows the end state. |
| 1 | **Before → after** | The problem, and the change in one picture, as a split screen. What used to happen, and what happens now. Mention what stays as it was (legacy paths, other layouts). |
| 2 | **The picture** | The core objects, introduced one at a time at their place in the diagram, each with its one-line meaning. This is where the new names land. |
| 3…n−2 | **Mechanisms** | One scene per mechanism: a pipeline stage, a key, an algorithm, a rule, a state machine, a failure path. Each has a worked example on tiny concrete data. |
| n−1 | **Use** | Who reads the new thing and how: the consumers, the checks at the boundary, what refuses and why. |
| n | **How to review** | What to read first (a design doc, ADRs) and how long it takes. Commit groups in order, the files that need care, where the reasoning is tested, what to skip (generated or golden files). The size breakdown if it is surprising. |
| end | **Takeaway** | Three short lines that sum up the design. Hold them for 3 s. |

Order the mechanisms the way data flows through the system, not the way the files are laid
out.

## 2. Scene patterns

Each of these is used in `example.py`. The scene named in brackets is the one to copy.

- **Split screen, before and after** (S01): a dashed divider, red heading "before", green
  heading "after". Build the left side, then the right side, with matching shapes, so the
  difference is the only thing that changes.
- **A chain of new names** (S03): one box per name, added one caption at a time, with arrows
  for "derived from". A legend for what the colors mean. Then the consumers on the right.
- **What a key contains** (S04): chips for the fields in the key. A struck-through list of what
  is *not* in it. Then three events: one that leaves the key's value unchanged ("same value: no
  new run"), one that changes it, and one outside every key.
- **A sorted queue and its stop rules** (S05): items as squares that move into their sorted
  order, then a table of stop conditions revealed one row per caption.
- **An algorithm traced on toy data** (S06): a grid (tests × branches), a heap or queue as a
  column of chips, a note beside the popped item ("fresh 1 vs next 3 (t1): push back"), and the
  result accumulating at the bottom. The steps come from `lazy_trace`, a copy of the PR's
  function. Close with the real figures the PR reports.
- **A decision table** (S07, S10): pattern icons, a verdict and its effect, one row per
  caption. A key for the icons at the bottom.
- **One job, its stages and its outcomes** (S08): a container frame holding the stages left to
  right, then two columns: outcomes that are stored and outcomes that are retried.
- **Merging two stores** (S09): A ∪ B = B ∪ A shown with chips, after saying where the second
  store comes from. Then a contrast case, where the merge of plain values would conflict.
- **A record's schema** (S10): monospace keys on the left, plain-language meaning on the right.
- **A reading guide** (S12): a left column (read first, then commits), and a right column (read
  carefully / where it is tested / skip).

When you are torn between two pictures, pick the one where something *moves* because the
mechanism moves: data flowing, an item being chosen, a key changing. A still list is the
weakest picture, so use it only for summaries.

## 3. Captions

The caption carries the explanation. The picture shows the thing the caption talks about.

- One sentence, about 50–90 characters. Above about 95 characters it shrinks, and the check
  warns you. Split it into two captions.
- Plain words, present tense, active voice: "The PR job reads the file and runs every test if it
  is missing." Not "The file is consumed by the PR job."
- Name real identifiers exactly as in the code (`tests_for`, `smoke.json`). Explain a
  name the first time it appears.
- Say what the viewer is looking at, as it appears. A caption that refers to something not yet
  on screen confuses.
- Use no hedging and no filler ("basically", "essentially", "it's important to note").
- Give the reason, when the PR gives one: "...so the figures cannot drift apart." Cite the ADR
  in brackets when a decision has one: "(ADR-0012)".
- Use numbers from `facts.md` only.

Good: `Pop t2: bound 4, but only 1 branch is still new, less than the next bound. Push it back.`
Bad: `The algorithm now efficiently processes the next candidate in the heap.`

## 4. Pacing

From the example (13 scenes, 7m23s):

- A scene lasts 25–70 s, about 35 s on average, with 6–12 captions. The intro is shorter.
- Count the captions to know the length before you write code. In the example a caption costs 5.5 s
  on average, its animations included (81 captions in 443 s); steps played with
  `say(text, anims=[...])` bring that nearer 4 s. So a scene of 14 captions runs 55–75 s. Cut
  captions in the storyboard, where it is cheap, not after the render.
- `say()` holds a caption for its reading time, about 28 characters per second, at least 1.4 s
  and at most 4 s. Pass `wait=` to hold a caption longer, for a picture that needs studying.
- Most `play()` calls take 0.5–1.0 s. Use `LaggedStart` for a group of 3 or more objects so they
  arrive in sequence.
- When a step is what the caption describes, pass it to `say(text, anims=[...])`. It plays with the
  caption change instead of before it, so the two arrive together and the scene is shorter by the
  step's run time.
- Reveal one thing per caption. If a caption explains three things, show three things in three
  captions.
- End every scene with `clear_all()`, so the next one starts on an empty stage.

## 5. A storyboard entry

```markdown
### S04Keys — what the expensive runs are keyed on
Picture: left, two keys as rows of chips. Right, "in no key", 6 struck-through items.
Bottom: event → value → result, shown three times (no change; re-key; outside every key).
Captions:
1. The coverage run is keyed on TEST_LIST, the lockfile and the runner's size.
2. The stability run is keyed on ORDER's value, the runner, and how many runs and tests.
3. Nothing else enters: not the commit, not the docs, not storage, not the deadline.
...
Facts: key fields → ci/keys.py:41; runner 4 CPU / 8 GiB → ci/config.yml:12
```
