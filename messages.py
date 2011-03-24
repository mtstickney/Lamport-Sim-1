import sys
import bisect
import history

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

# message comparison func
def precedes(a, b):
    "Determine if a message was sent before another."
    tiebreaker_func = history.STATE['TIEBREAKER']
    if a.timestamp < b.timestamp:
        return True
    if a.timestamp > b.timestamp:
        return False
    return tiebreaker_func(a, b)

def outgoing(recipient, msg):
    outgoing_q = history.STATE['OUTGOING_Q']
    delay_map = history.STATE['LINK_DELAYS']
    cur_ticks = history.STATE['TICKS']
    
    delivery_time = cur_ticks + delay_map[(msg.sender, recipient)]
    bisect.insort(outgoing_q, (delivery_time, recipient, msg))

