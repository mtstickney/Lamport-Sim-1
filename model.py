#!/usr/bin/python2

import collections
import random
import heapq

procs=nil
MAX_RAND_INCREMENT=500
TIEBREAKER_ORDER=range(len(pids))

class Msg:
    def __init__(self, msg_type, sender_id, timestamp, data=nil):
        self.msg_type = intern(msg_type)
        self.pid = sender_id
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
    def __init__(self, initial_grant, clock_increment=nil, event_interval=0):
        self.clock = 0
        if (clock_increment is nil):
            self.clock_increment = random.randint(1, MAX_RAND_INCREMENT)
        else:
            self.clock_increment = clock_increment
        self.next_clock = self.clock+self.clock_increment
        self.event_inteveral = event_interval
        self.msg_queue = [Msg("REQUEST", initial_grant, -1, {})]

    def update_clock(self, new_clock=nil):
        if (new_clock is not nil and new_clock < self.clock):
            return
        
        if (new_clock is not nil):
            self.clock = new_clock
        else:
            self.clock = self.next_clock

        if (self.clock_increment is nil):
            self.next_clock = self.clock+random.randint(1, MAX_RAND_INCREMENT)
        else:
            self.next_clock = self.clock+self.clock_increment

    # Convention: methods return nil if there is no reply, otherwise a (recipient, msg) pair
    # if recipient is nil, msg is broadcast
    def recv_msg(self, msg):
        self.update_clock(msg.timestamp)
        heapq.heappush(self.msg_queue, msg)
        if msg.msg_type is intern("REQUEST"):
            reply = Message("ACK", self, self.clock, msg.timestamp)
            return (sender, reply)
        if msg.msg_type is intern("ACK"):
            # Find the request message this is acking
            msg_lst = filter(lambda m: m.timestamp == msg.data and m.sender is self, msg_queue)
            if not msg_lst:
                warn("Spurious ACK received (no pending request found)")
                return nil
            # Request message's data is a dictionary of acked/non-acked processes
            msg_lst[0].data[msg.sender] = 1

            
    def request_resource(self, proc_lst):
        self.update_clock()
        msg = Msg("REQUEST", self.pid, self.clock, [0 for p in procs])
        heapq.heappush(self.msg_queue, msg)
        return msg

    def recv_request(self, msg, sender):
        self.update_clock(msg.timestamp)
        heapq.heappush(self.msg_queue, msg)
        msg = Msg("ACK", self.pid, )
        
    def recv_msg(self, msg)
        msg_sym = intern(msg.msg_type)
        self.update_clock(msg.timestamp)
        self.msg_queue.append((sender_id, msg_sym))

    def send_msg(self, msg_type):
        self.update_clock()

# message comparison func
def precedes(a, b):
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

def init(numprocs):
    procs=[Process() for i in range(numprocs)]

def 

random.seed()
