import json
import sleekxmpp
import util

class SimBot(sleekxmpp.ClientXMPP):
    def __init__(self, jid, password, mucroom, msg_queue):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        self.register_plugin('xep_0045')
        self['xep_0045'].plugin_init()

        self.msg_queue = msg_queue
        self.mucroom = mucroom

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("groupchat_message", self.groupchat_message)
        self.add_event_handler("proc_msg_send", self.local_event)
        self.add_event_handler("proc_msg_recv", self.local_event)
        self.add_event_handler("proc_res_claim", self.local_event)
        self.add_event_handler("proc_res_release", self.local_event)
        self.add_event_handler("clock_update", self.local_event)
        self.add_event_handler("message", self.message)
        self.add_event_handler("sim_event", self.local_event)

    def start(self, event):
        print("Starting session")
        self.sendPresence(pstatus='Available')

    def groupchat_message(self, msg):
        print("Got group message '{}'".format(msg))
        if msg.get_type() is not 'groupchat':
            util.warn("Ignoring message of type '"+ msg.get_type() + "'")
            return
        if msg.from is not self.jid:
            self.msg_queue.put(json.loads(msg.body), True)

    def local_event(self, data):
        print("Sending message to group: '{}'".format(json.dumps(data)))
        self.send_message(mto=self.mucroom, mbody=json.dumps(data),
                          mfrom=self.jid, mtype='groupchat')

