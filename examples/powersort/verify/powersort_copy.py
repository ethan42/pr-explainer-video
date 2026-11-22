"""Line-for-line Python copies of the PR's powerloop(), found_new_run() and merge_force_collapse(),
checked against the C originals (harness.c) by check_copy.py."""


def powerloop(s1, n1, n2, n):
    result = 0
    a = 2 * s1 + n1
    b = a + n1 + n2
    while True:
        result += 1
        if a >= n:
            a -= n
            b -= n
        elif b >= n:
            break
        a <<= 1
        b <<= 1
    return result


def powersort_trace(runs):
    """Events of the head's merge loop: ("power", i, p), ("merge", i, na, nb), ("push", n), plus cost."""
    n = sum(runs)
    stack = []  # [start, len, power]
    ev = []
    cost = 0
    start = 0
    for n2 in runs:
        if stack:
            s1, n1, _ = stack[-1]
            power = powerloop(s1, n1, n2, n)
            ev.append(("power", len(stack) - 1, power))
            while len(stack) > 1 and stack[-2][2] > power:
                a, b = stack[-2], stack[-1]
                cost += a[1] + b[1]
                ev.append(("merge", len(stack) - 2, a[1], b[1]))
                stack[-2:] = [[a[0], a[1] + b[1], a[2]]]
            stack[-1][2] = power
        stack.append([start, n2, None])
        ev.append(("push", n2))
        start += n2
    while len(stack) > 1:  # merge_force_collapse, unchanged by the PR
        i = len(stack) - 2
        if i > 0 and stack[i - 1][1] < stack[i + 1][1]:
            i -= 1
        a, b = stack[i], stack[i + 1]
        cost += a[1] + b[1]
        ev.append(("merge", i, a[1], b[1]))
        stack[i:i + 2] = [[a[0], a[1] + b[1], a[2]]]
    return ev, cost
