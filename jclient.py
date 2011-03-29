import json
import sleekxmpp
import util

class SimBot(sleekxmpp.ClientXMPP):
    def __init__(self, jid, password, mucroom, msg_queue, clients):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        self.register_plugin('xep_0045')
        self['xep_0045'].plugin_init()

        self.msg_queue = msg_queue
        self.mucroom = mucroom

        self.client_lst = clients

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("groupchat_message", self.groupchat_message)
        self.add_event_handler("message", self.message)
        self.add_event_handler("sim_event", self.local_event)

    def start(self, event):
        print("Starting session")
        self.send_presence(pstatus='Available')
        self['xep_0045'].joinMUC(self.mucroom, self.jid)

    def message(self, msg):
        print("Received message '{}'".format(msg))
        if msg.get_type() is not 'chat':
            util.warn("Ignoring message of type '"+msg.get_type()+"'")
            return
        if msg['from'] is not self.jid:
            self.msg_queue.put(json.loads(msg.body))

    def groupchat_message(self, msg):
        print("Got group message '{}'".format(msg))
        if msg.get_type() is not 'groupchat':
            util.warn("Ignoring message of type '"+ msg.get_type() + "'")
            return
        if msg['from'] is not self.jid:
            self.msg_queue.put(json.loads(msg.body), True)

    def local_event(self, data):
        print("Sending message to group: '{}'".format(json.dumps(data)))
        self.send_message(mto=self.mucroom, mbody=json.dumps(data),
                          mfrom=self.jid, mtype='groupchat')
        # for c in self.client_lst:
        #     print("Sending message to client {}".format(c))
        #     self.send_message(mto=c, mbody=json.dumps(data),
        #                       mfrom=self.jid, mtype='chat')

