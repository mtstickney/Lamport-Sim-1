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

def handle_job(job, bot):
     if job.msg_type is 'MSG_RECV':
          # message is of form (delivery time, recipient, Message())
          try:
               newproc = copy.deepcopy(history.STATE[recipient])
          except KeyError:
               util.warn("Recipient process {} does not exist".format(recipient))
          history.STATE.new_state()
          history.STATE[job[1][1]] = newproc
          reply = newproc.recv_msg(job[1][2])
          resp = { 'msg_type': 'RECV',
                   'from': job[1][2].sender,
                   'to': job[1][1],
                   'to_clock': newproc.clock
                   }
          bot.event('sim_event', resp)

          if reply is not None:
               resp = { 'msg_type': 'SEND',
                        'from': newproc.pid,
                        'type': reply[1].msg_type,
                        'from_clock': newproc.clock}
               if reply[0] is None:
                    resp['to'] = -1
               else:
                    resp['to'] = reply[0]
               bot.event('sim_event', resp)
               messages.outgoing(reply)
     if job.msg_type is 'PAUSE':
          PAUSED=True
     if job.msg_type is 'PLAY':
          PAUSED=False
     if job.msg_type is 'BACK':
          history.back()
          redraw(bot)
     if job.msg_type is 'FORWARD':
          history.forward()
          redraw(bot)
     if job.msg_type is 'LINK_DELAY':
          pair = (job['from'], job['to'])
          delay_map = history.STATE['LINK_DELAY']
          for sender, recipient, delay in job.delays:
               delay_map[(sender, recipient)] = delay
               delay_map[(recipient, sender)] = delay
     if job.msg_type is 'TIEBREAKER':
          tb_func = lambda a, b: job.order.index(a.sender) < job.order.index(b.sender)
          history.STATE['TIEBREAKER'] = tb_func
     if job.msg_type is 'REQUEST':
          try:
               newproc = copy.deepcopy(history.STATE[job.proc])
          except KeyError:
               util.warn("Requesting process {} does not exist".format(job.proc))
               return
          history.new_state()
          history.STATE[job.proc] = newproc
          newproc.request_resource()
     if job.msg_type is 'REQ_INT':
          try:
               proc = history.STATE[job.proc]
          except KeyError:
               util.warn("Process {} does not exist".format(job.proc))
               return
          if job.interval < 1:
               proc.event_interval = None
               max_rand_incr = history.STATE['MAX_RAND_INCR']
               interval = random.randint(1, max_rand_incr)
               proc.next_event = proc.last_event + interval
          else:
               proc.next_event = proc.last_event + job.interval
               proc.event_interval = job.interval
     if job.msg_type is 'CLOCK_INT':
          try:
               proc = history.STATE[job.proc]
          except KeyError:
               util.warn("Process {} does not exist".format(job.proc))
               return
          if job.interval < 1:
               proc.clock_interval = None
               max_rand_incr = history.STATE['MAX_RAND_INCR']
               interval = random.randint(1, max_rand_incr)
               proc.next_clock = proc.clock + interval
          else:
               proc.next_clock = proc.clock + job.interval
               proc.clock_interval = job.interval
     if job.msg_type is 'QUIT':
          util.warn("Quitting")
          sys.exit(0)

if __name__ == "__main__":
     if len(sys.argv) is not 5:
          util.warn("Usage: SimBot jid password mucroom, numprocs")
          print("Usage: SimBot jid password mucroom")
          sys.exit(1)
          
     initial_state = { 'NUMPROCS': int(sys.argv[4]),
                       'MAX_RAND_INCR': 500,
                       'TIEBREAKER': lambda m1, m2: m1.sender < m2.sender,
                       'INITIAL_GRANT': 0,
                       'OUTGOING_Q': [],
                       'LINK_DELAYS': collections.defaultdict(lambda : 0),
                       'TICKS': 0,
                       'TIEBREAKER': (lambda a, b: a.sender < b.sender),
                       'BASE_TIME': time.clock(),
                    }
     history.STATE = history.History(initial_state)

     for i in range(int(sys.argv[4])):
          history.STATE[i] = model.Process(i, event_interval=5)

     work_queue = queue.Queue()
     bot = jclient.SimBot(sys.argv[1], sys.argv[2], sys.argv[3], work_queue)
     if not bot.connect(('bitworks.hopto.org', 5222)):
          util.warn("Unable to connect")
          sys.exit(1)
     sys.exitfunc = lambda : bot.disconnect()
     bot['xep_0045'].joinMUC(bot.mucroom, bot.jid)
     bot.process()

     while True:
          if PAUSED:
               continue
          try:
               job = work_queue.get_nowait()
          except queue.Empty:
               job = None
          if job is not None:
               handle_job(job)
               work_queue.task_done()
          msgs = messages.get_deliverable(history.STATE['TICKS'])
          for m in msgs:
               work_queue.put(('MSG_RECV', m))

          for i in range(history.STATE['NUMPROCS']):
               proc = history.STATE[i]
               # Some of these CLAIM messages will be spurious (proc will already have claimed resource)
               if history.STATE[i].has_resource():
                    resp = { 'msg_type': 'CLAIM',
                             'pid': i}
                    bot.event('sim_event', resp)
               if proc.next_event <= history.STATE['TICKS']:
                    if proc.has_resource():
                         proc.release_resource()
                    else:
                         proc.request_resource()

          history.STATE['TICKS'] = time.clock() - history.STATE['BASE_TIME']
