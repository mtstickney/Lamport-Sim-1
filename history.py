import collections
import itertools

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
        if initial_state is None:
            initial_state = dict()
        self.hist = collections.deque()
        # Tail holds future events when we step backwards
        self.tail = collections.deque()
        self.hist.append(initial_state)
        self.cache = dict(initial_state)

    def __iter__(self):
        "Return iterator for stored events, from newer to older"
        return itertools.chain(reversed(self.tail), iter(self.hist))

    def __len__(self):
        "Returns the number of states in the history"
        return len(self.hist)+len(self.tail)

    def past_len(self):
        "Returns the number of past states"
        return len(self.hist)-1

    def new_state(self, *args, **kwargs):
        """Create a new history state.

        Any arguments are passed to the constructor for the state dictionary;
        states may be constructed with keys in this way."""
        self.hist.append(dict(*args, **kwargs))
        if len(self.tail) > 0:
            self.tail.clear()
        self.cache.clear()

    def __setitem__(self, key, val):
        # We're appending/popping on the right, so hist[-1] is the current state
        assert len(self.hist) >= 1
        self.hist[-1][key] = val
        self.cache[key] = val

    def __getitem__(self, key):
        assert self.cache is not None
        try:
            return self.cache[key]
        except KeyError:
            val = hist_find(reversed(self.hist), key)
            self.cache[key] = val
            return val

    def back(self, n=1):
        """Move back n positions in the history.

        If there aren't n past items in the history, move back until we reach the initial state or empty history."""
        for i in range(min(n, len(self.hist)-1)):
            self.tail.append(self.hist.pop())
        self.cache.clear()
        assert len(self.hist) >= 1

    def forward(self, n=1):
        "Move forward n positions in the history."
        for i in range(min(n, len(self.tail))):
            self.hist.append(self.tail.pop())
        self.cache.clear()

# Optional getkey parameter is used to filter the history state if non-None
# Ex: getkey=(lambda s: return s["procs"]) will make search the procs dict
# of each state for the specified key
def hist_find(history, key):
    """Find the most recent value for a key in the history.

    The dictionary returned by getkey() is searched."""
    for s in history:
        if key in s:
            return s[key]
    raise KeyError
