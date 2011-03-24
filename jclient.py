import json
import sleekxmpp
import util

class SimBot(sleekxmpp.ClientXMPP):
    def __init__(self, jid, password, mucroom, msg_queue):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.start)
        self.msg_queue = msg_queue
        self.mucroom = mucroom

        self.add_event_handler("start", self.start)
        self.add_event_handler("groupchat_message", self.groupchat_message)
        self.add_event_handler("proc_msg_send", self.local_event)
        self.add_event_handler("proc_msg_recv", self.local_event)
        self.add_event_handler("proc_res_claim", self.local_event)
        self.add_event_handler("clock_update", self.local_event)

    def start(self, event):
        self.getRoster()
        self.sendPresence()

    def groupchat_message(self, msg):
        if msg.get_type() is not 'groupchat':
            util.warn("Ignoring message of type '"+ msg.get_type() + "'")
            return
        self.msg_queue.put(json.loads(msg.body), True)

    def local_event(self, data):
        self.send_message(mto=self.mucroom, mbody=json.dumps(data),
                          mfrom=self.jid, mtype='groupchat')

