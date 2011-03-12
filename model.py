#!/usr/bin/python2

import random
import heapq
import warn

MAX_RAND_INCREMENT=500
TIEBREAKER_ORDER=range(len(pids))
INITIAL_GRANT=0

class Message:
    def __init__(self, msg_type, sender_id, timestamp, data=None):
        """Construct a message.

        msg_type -- string (will be interned) describing which type of message
        this is.
        sender_id -- pid of the sending Process.
        timestamp -- value of the sending processes clock when the message
        was sent.
        data -- optional message-specific data."""
        self.msg_type = intern(msg_type)
        self.sender = sender_id
        self.timestamp = timestamp
        self.data = data

    def __lt__(self, other):
        return precedes(self, other)

    def __le__(self, other):
        return self < other

    def __ge__(self, other):
        return self > other

    def __gt__(self, other):
        return not precedes(self, other)

class Process:
    def __init__(self, pid, clock_increment=None, event_interval=0):
        """Construct a Process.

        pid -- the pid of this process.
        clock_increment -- value that the clock is incremented by when an event
        occurs.
        event_interval -- determines how often the process requests the resource."""
        self.clock = 0
        self.pid = pid
        if (clock_increment is None):
            self.clock_increment = random.randint(1, MAX_RAND_INCREMENT)
        else:
            self.clock_increment = clock_increment
        self.next_clock = self.clock+self.clock_increment
        self.event_inteveral = event_interval
        self.msg_queue = [Message("REQUEST", INITIAL_GRANT, -1, set())]

    def update_clock(self, new_clock=None):
        """Update the clock to a new value.

        If new_clock is passed, the process will have new_clock as its clock
        value."""
        if (new_clock is not None and new_clock < self.clock):
            return
        
        if (new_clock is not None):
            self.clock = new_clock
        else:
            self.clock = self.next_clock

        if (self.clock_increment is None):
            self.next_clock = self.clock+random.randint(1, MAX_RAND_INCREMENT)
        else:
            self.next_clock = self.clock+self.clock_increment

    # Convention: methods return None if there is no reply, otherwise a (recipient, msg) pair
    # if recipient is None, msg is broadcast
    def recv_msg(self, msg):
        """Receive an incoming message.

        Updates the clock and performs an action based on message type. Returns
        a (recipient, reply) pair if a reply should be sent, None otherwise."""
        self.update_clock(msg.timestamp)
        heapq.heappush(self.msg_queue, msg)
        if msg.msg_type is intern("REQUEST"):
            reply = Message("ACK", self, self.clock, msg.timestamp)
            return (msg.sender, reply)
        if msg.msg_type is intern("ACK"):
            # Find the request message this is acking
            msg_lst = filter(lambda m: m.timestamp == msg.data and m.sender is self.pid, self.msg_queue)
            if not msg_lst:
                warn("Spurious ACK received (no pending request found)")
                return None
            if len(msg_lst) > 1:
                warn("Warning: ACK matches multiple requests")
            # Request message's data is a set of ack'ed processes
            msg_lst[0].data.add(self.pid)
            return None
        if msg.msg_type is intern("RELEASE"):
            newlst = [m for m in self.msg_queue if m.msg_type is not "REQUEST" or m.sender is not msg.sender]
            self.msg_queue = newlst
            heapq.heapify(self.msg_queue)
            return None

    def request_resource(self):
        """Send a request for the shared resource.

        Updates the clock, and eturns a (recipient, message) pair."""
        self.update_clock()
        msg = Message("REQUEST", self.pid, self.clock, set())
        heapq.heappush(self.msg_queue, msg)
        return (None, msg)

    def release_resource(self):
        """Release the shared resource.

        Updates the clock and returns a (recipient, message) pair."""
        self.update_clock()
        msg = Message("RELEASE", self, self.clock)
        return (None, msg)

# message comparison func
def precedes(a, b):
    "Determine if a message was sent before another."
    if a.timestamp < b.timestamp:
        return True
    if a.timestamp > b.timestamp:
        return False
    for i in TIEBREAKER_ORDERING:
        if i == a:
            return True
        if i == b:
            return False
    return False
