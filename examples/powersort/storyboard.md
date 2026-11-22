# Storyboard: python/cpython#28108, powersort merge order

Colors: runs = BLUE (alternating C/D so neighbours read apart), midpoints and gaps = TEAL,
power / tree level = GOLD, cost = ORANGE, old rule = RED, powersort = GREEN.
New names: run, merge cost, power, powerloop(), found_new_run().

### S00Intro: title, PR, size
Captions: the one decision it changes; old home-made rule → powersort (Munro & Wild); end state.

### S01Runs: how list.sort() merges
Picture: the toy runs 4 6 2 5 9 3 3 as bars; then the 1, 2, 3 cost demo as two panels (9 vs 11).
Captions: runs; minrun and toy units; merges of neighbours; cost A + B; 9; 11; order is the question; stack.

### S02Before: the old rule
Picture: stack of A, B, C; rules A > B + C and B > C; "at most 85"; then history chips and the paper.
Captions: two rules; any break merges; Fibonacci → 85; proof found rules broken; repaired, research; powersort.

### S03Power: a run's power
Picture: the toy runs on a 0..32 line, dyadic ticks at levels 1–3, midpoints, gaps, nodes, then the tree.
Captions: interval 0..1; halves/quarters/eighths; midpoints and gap; first pair power 3; second power 2;
the rest 3, 1, 2, 3; nodes are a merge tree; power 1 is root, deeper merges sooner.

### S04Powerloop: computing it
Picture: the loop (left), trace table for (3 | 3) at 26 (right), binary expansions.
Captions: no division; doubled midpoints; a = 55, b = 61; turn 1; turn 2; turn 3 stop; binary; O(1) needs clz; and wide division.

### S05Stack: found_new_run()
Picture: runs row on top with a cursor; stack with power chips; the 3-step rule; cost counter.
Captions: one per run event (see facts.md trace), end collapse, 87 vs 97, log2(n) + 1, 85 → 64.

### S06Cases: better, and sometimes worse
Picture: two contrived run lists from the PR comments with cost bars; then closing facts.
Captions: bad case for old: 250M vs 150M; reverse: 200M vs 150M; quadratic optimum; 3 runs optimal; timing; provable bounds.

### S07Review: how to review it
Picture: read first / then listobject.c items; read carefully / tested / unchanged; size line; takeaway.
