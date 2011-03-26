#!/usr/bin/python

import queue
import collections
import sys
import time
import jclient
import model
import history
import util
import messages

PAUSED=False

def deliver_message(msg, bot):
     history.STATE.new_state()
     recipients = None
     if msg.recipient is None:
          recipients = list(range(history.STATE['NUMPROCS']))
     else:
          recipients = [msg.recipient]

     for pid in recipients:
          proc = history.STATE[pid]
          resp = { 'msg_type': 'RECV',
                   'from': msg.sender,
                   'to': msg.recipient,
                   'type': msg.msg_type,
                   'from_clock': history.STATE[msg.sender].clock}
          bot.event('sim_event', resp)

     # USE OUTGOING_Q, it's in the History...
     replies = map(lambda p: p.recv_msg(msg), newproc_lst)
     if len(replies) is 0:
          return

     for m in replies:
          resp = { 'msg_type': 'SEND',
                   'from': m.sender,
                   'to': m.recipient,
                   'type': m.msg_type,
                   'from_clock': history.STATE[m.sender].clock}
          bot.even('sim_event', resp)
          messages.outgoing(m)

def handle_pause(msg):
     global PAUSED
     PAUSED = True

def handle_play(msg):
     global PAUSED
     PAUSED = False

def handle_back(msg):
     history.STATE.back()

def handle_forward(msg):
     history.STATE.forward()

def handle_delay(msg):
     delay_map = history.STATE['LINK_DELAY']
     for source, dest, delay in msg['delays']:
          delay_map[(source, dest)] = delay
          delay_map[(dest, source)] = delay

def handle_tiebreaker(msg):
     order = msg['order']
     breaker = lambda a, b: order.index(a.sender) < order.index(b.sender)
     history.STATE['TIEBREAKER'] = breaker

def handle_request_interval(msg):
     proc = history.STATE[msg['proc']]
     if msg['interval'] <= 0:
          proc.event_interval = None
     else:
          proc.event_interval = msg['interval']
     proc.update_req_interval()

def handle_clock_interval(msg):
     proc = history.STATE[msg['proc']]
     if msg['interval'] <= 0:
          proc.clock_increment = None
     else:
          proc.clock_increment = msg['interval']
     proc.update_clock_interval()

def handle_request(msg):
     proc = history.STATE[msg['proc']]
     m = proc.request_resource()
     messages.outgoing(m)
     resp = { 'msg_type': 'SEND',
              'from': m.sender,
              'to': m.recipient,
              'type': m.msg_type,
              'from_clock': proc.clock}

CLIENT_HANDLERS = {
     'PAUSE': handle_pause,
     'PLAY': handle_play,
     'BACK': handle_back,
     'FORWARD': handle_forward,
     'LINK_DELAY': handle_delay,
     'TIEBREAKER': handle_tiebreaker,
     'REQUEST': handle_request,
     'REQ_INT': handle_request_interval,
     'CLOCK_INT': handle_clock_interval
     }

def handle_client_msg(msg, bot):
     try:
          handler = CLIENT_HANLDERS[msg['msg_type']]
     except KeyError:
          util.warn("Ignoring message with unhandled type '{}'".format(msg['msg_type']))
     handler(msg)

def run_events(proc, ticks):
     if proc.next_event <= ticks:
          if proc.has_resource():
               msg = proc.release_resource()
          else:
               msg = proc.request_resource()
          messages.outgoing(msg)
          resp = {'msg_type': 'SEND',
                  'from': msg.sender,
                  'to': msg.recipient,
                  'type': msg.msg_type,
                  'from_clock': proc.clock
                  }
          bot.event('sim_event', resp)
          proc.update_req_interval()

if __name__ == "__main__":
     if len(sys.argv) < 5:
          util.warn("Usage: SimBot jid password mucroom, numprocs [jids]")
          print("Usage: SimBot jid password mucroom")
          sys.exit(1)

     initial_state = { 'NUMPROCS': int(sys.argv[4]),
                       'MAX_RAND_INCREMENT': 10,
                       'TIEBREAKER': lambda m1, m2: m1.sender < m2.sender,
                       'INITIAL_GRANT': 0,
                       'OUTGOING_Q': [],
                       'LINK_DELAYS': collections.defaultdict(lambda : 0),
                       'TICKS': 0,
                       'TIEBREAKER': (lambda a, b: a.sender < b.sender),
                       'BASE_TIME': time.time(),
                    }
     history.STATE = history.History(initial_state)

     for i in range(int(sys.argv[4])):
          history.STATE[i] = model.Process(i, event_interval=5)

     work_queue = queue.Queue()
     bot = jclient.SimBot(sys.argv[1], sys.argv[2], sys.argv[3], work_queue, sys.argv[5:])
     if not bot.connect(('bitworks.hopto.org', 5222)):
          util.warn("Unable to connect")
          sys.exit(1)
     sys.exitfunc = lambda : bot.disconnect()
     bot.process()

     while True:
          if PAUSED:
               continue

          # Process stuff from the client first, since they can't see pending
          # stuff in here
          while True:
               try:
                    client_msg = work_queue.get_nowait()
               except queue.Empty:
                    break
               handle_client_msg(client_msg)
               work_queue.task_done()

          # Process up to one message from the process pool
          delivery_time, msg = history.STATE['OUTGOING_Q'][0]
          if delivery_time <= history.STATE['TICKS']:
               deliver_msg(msg, bot)
               del history.STATE['OUTGOING_Q'][0]

          # Process any timed events from the processes
          for i in range(history.STATE['NUMPROCS']):
               proc = history.STATE[i]
               run_events(proc, history.STATE['TICKS'])

          history.STATE['TICKS'] = time.time() - history.STATE['BASE_TIME']
          print("Clock() is {}".format(time.time()))
          print("TICKS now {}".format(history.STATE['TICKS']))
          time.sleep(.5)
