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
        self.hist = collections.deque()
        # Tail holds future events when we step backwards
        self.tail = collections.deque()
        self.cache = None
        if initial_state is not None:
            self.hist.append(initial_state)
            self.cache = initial_state

    def __iter__(self):
        "Return iterator for stored events, from newer to older"
        return itertools.chain(reversed(self.tail), iter(self.hist))

    def __len__(self):
        "Returns the number of states in the history"
        return len(self.hist)+len(self.tail)

    def past_len(self):
        "Returns the number of past states (includes current state)"
        return len(self.hist)

    def new_state(self, *args, **kwargs):
        """Create a new history state.

        Any arguments are passed to the constructor for the state dictionary;
        states may be constructed with keys in this way."""
        self.hist.append(dict(*args, **kwargs))
        if len(self.tail) > 0:
            self.tail.clear()
        self.cache = None

    def set_current_key(self, key, val):
        # We're appending/popping on the right, so hist[-1] is the current state
        self.hist[-1][key] = val

    def get_current_key(self, key):
        if self.cache is None:
            self.fill_cache()
        if key in self.cache:
            return self.cache[key]

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

    def back(self, n=1):
        """Move back n positions in the history.

        If there aren't n past items in the history, move back until we reach the initial state or empty history."""
        for i in range(min(n, len(self.hist)-1)):
            self.tail.append(self.hist.pop())
        self.cache = None
        assert len(self.hist) >= 1

    def forward(self, n=1):
        "Move forward n positions in the history."
        for i in range(min(n, len(self.tail))):
            self.hist.append(self.tail.pop())
        self.cache = None

# Optional getkey parameter is used to filter the history state if non-None
# Ex: getkey=(lambda s: return s["procs"]) will make search the procs dict
# of each state for the specified key
def hist_find(history, key):
    """Find the most recent value for a key in the history.

    The dictionary returned by getkey() is searched."""
    for s in history:
        if key in s:
            return s[key]
    return None
