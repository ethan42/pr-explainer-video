/* Drives the merge-ordering functions of CPython's Objects/listobject.c, copied unchanged
 * (ext_*.c, which verify.sh extracts from the PR's base and head), on given run lengths.
 * Only merge_at() is a stub: it keeps the real bookkeeping of the pending stack and adds the
 * merge's "cost" (na + nb, the model used in bpo-34561) instead of merging elements.
 *
 *   harness old|new LEN...     print each merge, the stack after it, and the total cost
 *   harness power S1 N1 N2 N   print powerloop(S1, N1, N2, N)
 */
#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef ptrdiff_t Py_ssize_t;
typedef struct { int dummy; } PyObject;
typedef struct { PyObject **keys; PyObject **values; } sortslice;
struct s_slice {
    sortslice base;
    Py_ssize_t len;
    int power;
};
typedef struct {
    Py_ssize_t listlen;
    PyObject **basekeys;
    int n;
    struct s_slice pending[256];
} MergeState;

static long long cost;
static int verbose = 1;

static void show(MergeState *ms, const char *what) {
    if (!verbose) return;
    printf("%s |", what);
    for (int i = 0; i < ms->n; i++) printf(" %zd:%d", ms->pending[i].len, ms->pending[i].power);
    printf("\n");
}

static int
merge_at(MergeState *ms, Py_ssize_t i)
{
    Py_ssize_t na, nb;
    assert(i == ms->n - 2 || i == ms->n - 3);
    na = ms->pending[i].len;
    nb = ms->pending[i+1].len;
    cost += na + nb;
    ms->pending[i].len = na + nb;          /* as in listobject.c */
    if (i == ms->n - 3)
        ms->pending[i+1] = ms->pending[i+2];
    --ms->n;
    char buf[64];
    snprintf(buf, sizeof buf, "merge %zd+%zd", na, nb);
    show(ms, buf);
    return 0;
}

#include "ext_powerloop.c"
#include "ext_found_new_run.c"
#include "ext_merge_collapse.c"
#include "ext_force.c"

int main(int argc, char **argv) {
    if (argc >= 2 && !strcmp(argv[1], "power")) {
        printf("%d\n", powerloop(atoll(argv[2]), atoll(argv[3]), atoll(argv[4]), atoll(argv[5])));
        return 0;
    }
    if (argc >= 2 && !strcmp(argv[1], "powers")) {  /* stdin: lines "s1 n1 n2 n" */
        long long s1, n1, n2, n;
        while (scanf("%lld %lld %lld %lld", &s1, &n1, &n2, &n) == 4) printf("%d\n", powerloop(s1, n1, n2, n));
        return 0;
    }
    if (argc < 3 || (strcmp(argv[1], "old") && strcmp(argv[1], "new"))) {
        fprintf(stderr, "usage: harness old|new LEN... | power S1 N1 N2 N | powers < lines\n");
        return 2;
    }
    int old = !strcmp(argv[1], "old");
    if (getenv("QUIET")) verbose = 0;
    static MergeState ms;
    Py_ssize_t total = 0;
    for (int i = 2; i < argc; i++) total += atoll(argv[i]);
    ms.listlen = total;
    /* found_new_run() only uses differences of key pointers, so no list is allocated: keys
     * point into a pretend array that starts at 0x1000. */
    ms.basekeys = (PyObject **)0x1000;
    PyObject **lo = ms.basekeys;
    for (int i = 2; i < argc; i++) {
        Py_ssize_t n = atoll(argv[i]);
        if (!old && found_new_run(&ms, n) < 0) return 1;
        ms.pending[ms.n].base.keys = lo;
        ms.pending[ms.n].len = n;
        ms.pending[ms.n].power = 0;
        ++ms.n;
        char buf[64];
        snprintf(buf, sizeof buf, "push %zd", n);
        show(&ms, buf);
        if (old && merge_collapse(&ms) < 0) return 1;
        lo += n;
    }
    if (merge_force_collapse(&ms) < 0) return 1;
    printf("cost %lld\n", cost);
    return 0;
}
