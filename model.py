import random
import bisect
import time
import util
import messages
import history
import itertools

class Process:
    def __init__(self, pid, clock_increment=None, event_interval=1):
        """Construct a Process.

        pid -- the pid of this process.
        clock_increment -- value that the clock is incremented by when an event
        occurs.
        event_interval -- determines how often the process requests the
        resource."""
        self.clock = 0
        self.pid = pid
        if (clock_increment is None):
            max_rand_increment = history.STATE['MAX_RAND_INCR']
            interval = random.randint(1, max_rand_increment)
            self.next_clock = self.clock+interval
        else:
            self.next_clock = self.clock + clock_increment
            self.clock_increment = clock_increment
        self.next_clock = self.clock+self.clock_increment

        self.last_event = time.clock()
        if (event_interval is None):
            max_rand_increment = history.STATE['MAX_RAND_INCR']
            interval = random.randint(1, max_rand_increment)
            self.next_event = self.last_event + interval
        else:
            self.next_event = self.last_event + event_interval
        self.event_interval = event_interval

        # Set initial grant and ACK messages
        initial_grant = history.STATE['INITIAL_GRANT']
        self.msg_queue = [messages.Message("REQUEST", initial_grant, -1, set())]

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
            max_rand_increment = history.STATE['MAX_RAND_INCREMENT']
            self.next_clock = self.clock+random.randint(1, max_rand_increment)
        else:
            self.next_clock = self.clock+self.clock_increment

    # Handle an incoming message. If there is a reply, it is put on the outgoing
    # message queue (queue items have the form (recipient, reply)).
    def recv_msg(self, msg):
        """Receive an incoming message.

        Updates the clock and performs an action based on message type. Returns
        a (recipient, reply) pair if a reply should be sent, None otherwise."""
        self.update_clock(msg.timestamp)
        if msg.msg_type is intern("REQUEST"):
            bisect.insort(self.msg_queue, msg)
            # TODO: convince yourself that ACKs don't need to specify which message they're ACKing
            # (they only work to flush other messages, and we won't act until we got one from everybody)
            reply = messages.Message("ACK", self.pid, self.clock)
            messages.outgoing(msg.sender, reply)
            return
        if msg.msg_type is intern("ACK"):
            bisect.insort(self.msg_queue, msg)
            return
        if msg.msg_type is intern("RELEASE"):
            for m in self.msg_queue:
                if m.msg_type is "REQUEST":
                    break

            if m.sender is not msg.sender:
                util.warn("Got RELEASE from process not owning resource")
                
            # Now find the ACKs for that request
            acked_procs = set()
            ack_msgs = filter(lambda m: m.msg_type is "ACK",
                                         self.msg_queue)
            for m in ack_msgs:
                if len(acked_procs) == history.STATE['NUMPROCS']:
                    break
                if m.sender not in acked_procs:
                    acked_procs.add(m.sender)
                    self.msg_queue.remove(m)
            if len(acked_procs) is not history.STATE['NUMPROCS']:
                util.warn("Got RELEASE from process not owning resource (missing ACK)")

    def request_resource(self):
        """Send a request for the shared resource.

        Updates the clock, and eturns a (recipient, message) pair."""
        self.update_clock()
        msg = messages.Message("REQUEST", self.pid, self.clock, set())
        messages.outgoing(None, msg)

    def release_resource(self):
        """Release the shared resource.

        Updates the clock and returns a (recipient, message) pair."""
        self.update_clock()
        msg = messages.Message("RELEASE", self, self.clock)
        messages.outgoing(None, msg)
