import collections
import itertools
import util

# Convention: each state in the history is a dictionary of possibly updated
# items. If an item is not in the newest dictionary, earlier dictionaries are
# searched until the item is found.
# Dictionary items:
# {
#   "procs"=>{ pid=>Process() },
#   "res_owner"=>pid of process claiming resource,
#   "tiebreaker"=>tiebreaker ordering of processes
#   "pids"=>list of keys for "procs" dict
# }

class History:
    """Manage a history of application states.

    Only changed items are stored in each state, to reduce storage costs."""
    def __init__(self, initial_state=None):
        # The history is a cons-list of state dicts (two-tuple == cons cell)
        # hist[0] == (car hist), hist[1] == (cdr hist)
        self.hist = ()
        # Tail holds future events when we step backwards
        self.tail = collections.deque()
        self.cache = None
        if initial_state is not None:
            self.hist = (initial_state, self.hist)
            self.cache = initial_state

    def __iter__(self):
        "Return iterator for stored events, from newer to older"
        return itertools.chain(reversed(self.tail), clist_iter(self.hist))

    def __len__(self):
        "Returns the number of states in the history"
        return clist_len(self.hist)+len(self.tail)

    def past_len(self):
        "Returns the number of past or current states"
        return clist_len(self.hist)

    # Get key is passed the new state dict and the key to be inserted
    # Returns the dictionary in which to insert the key
    # getkey will be evaluated more than once per key to update the cache
    def new_state(self, keys, vals, getkey=(lambda s, k: s)):
        newhist = {}
        for k, v in itertools.izip(keys, vals):
            d = getkey(newhist, k)
            d[k] = v
            c = getkey(self.cache, k)
            c[k] = v
        if len(self.tail) > 0:
            self.tail.clear()
        self.hist = (newhist, self.hist)
        self.cache = None

    def fill_cache(self):
        if self.cache is None:
            self.cache = dict()
        owner = hist_find(self.hist, "res_owner")
        if owner is None:
            util.warn("Warning: No resource owner in history")
            return None
        self.cache["res_owner"] = owner
        
        order = hist_find(self.hist, "tiebreaker")
        if order is None:
            util.warn("Warning: No tiebreaker order in history")
            return None
        self.cache["tiebreaker"] = order

        self.cache["procs"] = dict()
        for p in pids:
            proc = hist_find(self.hist, p, getkey=(lambda s: s["procs"]))
            if proc is None:
                util.warn("Warning: no process for PID %s in history" % p)
                return None
            self.cache["procs"][p] = proc
        return self.cache

    def cur_state(self):
        "Returns the current history state"
        if self.cache is not None:
            return self.cache
        return self.fill_cache()

    def back(self, n=1):
        """Move back n positions in the history.

        If there aren't n past items in the history, move back until we reach the initial state or empty history."""
        if not self.hist:
            return
        for i in range(n):
            if not self.hist[1]:
                return
            self.tail.append(self.hist[0])
            self.hist = self.hist[1]
        self.cache = None

    def forward(self, n=1):
        "Move forward n positions in the history."
        for i in range(min(n, len(self.tail))):
            v = self.tail.pop()
            self.hist = (v, self.hist)
        self.cache = None

def clist_iter(clst):
    while clst:
        yield clst[0]
        clst = clst[1]

def clist_len(clst):
    n = 0
    while clst:
        n += 1
        clst = clst[1]
    return n

# Optional getkey parameter is used to filter the history state if non-None
# Ex: getkey=(lambda s: return s["procs"]) will make search the procs dict
# of each state for the specified key
def hist_find(history, key, getkey=(lambda s: s)):
    """Find the most recent value for a key in the history.

    The dictionary returned by getkey() is searched."""
    val = None
    for s in clist_iter(history):
        d = getkey(s)
        if key in d:
            val = d[key]
            break
    return val
