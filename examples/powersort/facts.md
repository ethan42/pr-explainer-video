# Facts: python/cpython#28108, "bpo-34561: Switch to Munro & Wild "powersort" merge strategy."

Base 863154c929 (main), head 56f8ccfec7, merged 2021-09-06 as 5cb4c672d8. Author tim-one (Tim Peters).

## The PR
- 3 files, +178 −92, 9 commits → `gh pr view 28108 --json additions,deletions,changedFiles,commits`
- Objects/listsort.txt +98 −59; Objects/listobject.c +79 −33; Misc/NEWS.d/...bpo-34561 +1 → gh pr files
- listsort.txt share of changed lines: (98+59)/(178+92) = 157/270 = 58% → computed
- Merged 2021-09-06 → mergedAt
- Issue bpo-34561 (now gh-78742) opened 2018-09-01 by Tim Peters, "Replace list sorting merge_collapse()?" → issue

## Background (unchanged by the PR)
- Runs: the sort cuts the list into runs; a run shorter than minrun is boosted to minrun via binary insertion → listsort.txt:235-238 (base and head)
- minrun is 32..64 when n >= 64; n < 64 → whole list by binary insertion → listobject.c merge_compute_minrun comment
- Merging is always on two consecutive runs at a time → listsort.txt "So merging is always done on two consecutive runs at a time"
- Cost model: merging runs of lengths A and B has cost A+B; "should be viewed as worst case, where the rest of timsort finds nothing to exploit" → Tim, issue comments 2018-09-01 and 2018-09-06
- 1,2,3 example: 1+2 first: 3 + 6 = 9; 2+3 first: 5 + 6 = 11 → Tim, issue 2018-09-06; reproduced by harness (cost 9)

## Before
- merge_collapse() kept invariants on the three rightmost runs A, B, C: 1. A > B+C, 2. B > C → listsort.txt (base) lines 212-217, listobject.c (base) comment
- Lengths grow at least as fast as Fibonacci numbers (reading right to left) → listsort.txt (base)
- MAX_MERGE_PENDING 85, "good for an array with 2**64 elements" → listobject.c (base):1143-1147
- "It was loosely based on invariants involving the Fibonacci sequence" / "the first thing I made up that didn't obviously suck" → listsort.txt (head)
- Intended invariants were not actually preserved; researchers found it while trying to complete a computer-generated correctness proof; repaired → listsort.txt (head)
- "At least a dozen different approaches were developed, some provably having near-optimal worst case behavior" → listsort.txt (head)
- Paper: "Nearly-Optimal Mergesorts: Fast, Practical Sorting Methods That Optimally Adapt to Existing Runs", J. Ian Munro and Sebastian Wild → listsort.txt (head)
- "provably near-optimal in the entropy of the distribution of run lengths" → NEWS entry

## The power
- Power of the first of two adjacent runs (s1, n1), (s2 = s1+n1, n2) in a list of n: the depth of the node connecting the two runs in an ideal binary merge tree; power 1 is the root → listsort.txt (head)
- Least L such that the midpoint interval ((s1 + n1/2)/n, (s2 + n2/2)/n] contains J/2**L → listsort.txt (head)
- Equivalently the first bit position where the binary expansions differ (0 on the left, 1 on the right) → listsort.txt (head)
- powerloop(): emulates the divisions 1 bit at a time with comparisons, subtractions and shifts → listsort.txt; code listobject.c (head) powerloop
- a = 2*s1 + n1 (2× left midpoint), b = a + n1 + n2 (2× right midpoint) → listobject.c (head) powerloop
- Paper's O(1) method needs (1) a count-leading-zeros primitive, no uniform spelling across platforms, (2) integer division on a type twice as wide as Py_ssize_t → listsort.txt (head)
- "the once-per-run overhead of powerloop() seems lost in the noise" → listsort.txt (head)

## The merge rule
- found_new_run(ms, n2) replaces merge_collapse(); called before the new run is pushed → listobject.c (head), diff of list_sort_impl
- Computes the top run's power, then merges p[n-2] and p[n-1] while p[n-2].power > power, then stores the power on the top run → listobject.c (head) found_new_run
- The most recently found run is never merged by found_new_run(): its power needs the next run → listsort.txt (head)
- Powers on the stack strictly decreasing starting from the top (assert p[n-2].power < power) → listsort.txt, listobject.c (head)
- Stack needs at most floor(log2(n)) + 1 entries; MAX_MERGE_PENDING = SIZEOF_SIZE_T * 8 (64 on 64-bit) → listobject.c (head)
- merge_init() gains `lo`; MergeState gains listlen and basekeys (read only), used for the run's start index → diff
- merge_force_collapse() is unchanged: final merges choose by length (merges at n-3 if p[n-3].len < p[n-1].len) → listobject.c base and head identical (diff of extracted function)

## Worked example

Toy run lengths, computed with the PR's C functions (verify/harness.c). The Python copy that drives
the animation matches the C on 20,000 power cases and 2,000 merge orders (verify/check_copy.py).

- Runs 4 6 2 5 9 3 3, n = 32. Starts 0 4 10 12 17 26 29. Midpoints 2 7 11 14.5 21.5 27.5 30.5
- Powers of pairs: (4|6)=3 at tick 4, (6|2)=2 at tick 8, (2|5)=3 at 12, (5|9)=1 at 16, (9|3)=2 at 24, (3|3)=3 at 28
- Trace: push 4; 6 → power 3, push; 2 → power 2, merge 4+6; push 2; 5 → power 3, push; 9 → power 1, merge 2+5, merge 10+7, push 9; 3 → power 2, push; 3 → power 3, push; force collapse 3+3, 9+6, 17+15
- Powersort cost 87; old rule cost 97 (old merges 4+6, 2+5, 7+9, 10+16, 3+3, 26+6)
- powerloop(26, 3, 3, 32): a=55 b=61 → step1 both ≥ 32 → 23,29 → 46,58 → step2 both → 14,26 → 28,52 → step3 a<32≤b → 3
- 27.5/32 = 0.110111 (binary), 30.5/32 = 0.111101 (binary): differ first at bit 3

## Contrived cases (PR comments by Tim, 2021-09-02/03), costs computed with harness.c, N = 100,000,000
- Bad for the old rule: runs N/2, N/2 − 64, 64, 1 → old 250,000,001; powersort 150,000,067
- Bad for powersort: base = N/128; runs (base−1)·64, 64, 64, base·64 → old 150,000,256; powersort 200,000,128
- "they're relatively less bad than the timsort bad cases are for timsort" → Tim PR comment
- Optimal merge order can be computed in time quadratic in the number of runs (needs all run lengths in advance) → listsort.txt (head)
- Powersort is the only strategy seen that is always optimal for 3 run lengths: merge the shorter of A and C with B → listsort.txt (head)
- Timing: "this change isn't expected to make dramatic changes in timing. Indeed, I can barely detect any in ordinary cases (for example, running Lib/test/sortperf.py)" → Tim PR comment 2021-09-02
- "provably stellar worst-case behavior, and a published paper readers can consult for details and proofs" → same comment

## Review
- No test files changed → PR file list
- "I did check the C version on various cases, but agree 'it would be nice' if that were an automated thing. But, it's not" ; C is a "more-than-less mechanical translation of runstack.py's powerloop()" → Tim review reply
- Reviewers requested: rhettinger, taleinat → Tim PR comment

## Disagreements
- None found between the description, listsort.txt, the comments and the code. Observation for the review: the
  text describes powersort's merge order, but the final collapse (merge_force_collapse, unchanged) still picks by
  length, not strictly top-down as in the paper.
