"""Checks powersort_copy.py against the C functions in ./harness, on random inputs."""
import random
import subprocess

from powersort_copy import powerloop, powersort_trace

rng = random.Random(1)
cases = []
for _ in range(20000):
    n = rng.randint(2, 10 ** rng.randint(1, 15))
    s1 = rng.randint(0, n - 2)
    n1 = rng.randint(1, n - s1 - 1)
    n2 = rng.randint(1, n - s1 - n1)
    cases.append((s1, n1, n2, n))
inp = "".join(f"{s1} {n1} {n2} {n}\n" for s1, n1, n2, n in cases)
got = subprocess.run(["./harness", "powers"], input=inp, capture_output=True, text=True, check=True).stdout.split()
bad = [(c, g) for c, g in zip(cases, got) if powerloop(*c) != int(g)]
print(f"powerloop: {len(cases)} cases, {len(bad)} mismatches")

bad = 0
for _ in range(2000):
    runs = [rng.randint(1, rng.choice([5, 50, 5000])) for _ in range(rng.randint(1, 30))]
    out = subprocess.run(["./harness", "new", *map(str, runs)], capture_output=True, text=True, check=True).stdout
    c_merges = [tuple(map(int, line.split("|")[0].split()[1].split("+")))
                for line in out.splitlines() if line.startswith("merge")]
    c_cost = int(out.split("cost")[1])
    ev, cost = powersort_trace(runs)
    py_merges = [(e[2], e[3]) for e in ev if e[0] == "merge"]
    bad += (py_merges != c_merges) or (cost != c_cost)
print(f"merge order: 2000 run lists, {bad} mismatches")
