
import sys, os
from scapy.all import *
import simpy
from copy import deepcopy

NSEC_PER_CYCLE = 5 # ns

def pad_pkt(pkt, size):
    if len(pkt) >= size:
        return pkt
    else:
        return pkt / ('\x00'*(size - len(pkt)))

class HW_sim_object(object):
    def __init__(self, env, period):
        self.env = env
        self.period = period
        self.sim_done = False

    def clock(self):
        yield self.env.timeout(self.period)

    def wait_clock(self):
        return self.env.process(self.clock())


class PktGenerator(HW_sim_object):
    def __init__(self, env, period, pkt_out_pipe, rate, base_pkt, base_meta, pkt_mod_cb=None, pkt_limit=None, cycle_limit=None, burst_size=None, burst_delay=None):
        """
        rate (Gbps)
        """
        super(PktGenerator, self).__init__(env, period)
        self.pkt_out_pipe = pkt_out_pipe
        self.rate = rate
        self.base_meta = base_meta
        self.base_pkt = base_pkt
        self.pkt_mod_cb = pkt_mod_cb
        self.pkt_limit = pkt_limit
        self.pkt_cnt = 0
        self.burst_size = burst_size
        self.burst_delay = burst_delay
        self.burst_cnt = 0
        self.burst_delay_cnt = 0
        self.DELAY = 0
        self.BURST = 1
        self.snd_state = self.DELAY

        if type(cycle_limit) == int:
            self.env.process(self.start_timer(cycle_limit))

        self.run()

    def run(self):
        self.proc = self.env.process(self.gen_pkts())

    def start_timer(self, cycle_limit):
        for i in range(cycle_limit):
            yield self.wait_clock()  
        self.sim_done = True

    def gen_pkts(self):
        while (self.pkt_limit is None and not self.sim_done) or (self.pkt_limit is not None and self.pkt_cnt < self.pkt_limit):
            if self.burst_size is not None and self.burst_delay is not None:
                if self.snd_state == self.BURST and self.burst_cnt < self.burst_size:
                    # send pkts in bursts
                    yield self.env.process(self.send_pkt())
                    self.burst_cnt += 1
                    if self.burst_cnt == self.burst_size:
                        self.snd_state = self.DELAY
                        self.burst_cnt = 0
                elif self.snd_state == self.DELAY:
                    self.burst_delay_cnt += 1
                    if self.burst_delay_cnt == self.burst_delay:
                        self.burst_delay_cnt = 0
                        self.snd_state = self.BURST
                    yield self.wait_clock()
                else:
                    yield self.wait_clock()
            else:
                yield self.env.process(self.send_pkt())

    def send_pkt(self):
            pkt = self.base_pkt.copy()
            meta = deepcopy(self.base_meta) 
            # invoke provided callback to provide programmability
            if self.pkt_mod_cb is not None:
                self.pkt_mod_cb(meta, pkt)
            # rate limiting
            pkt_time = len(pkt)*8/self.rate # ns
            cycle_delay = int(pkt_time/NSEC_PER_CYCLE + 0.5)
            for i in range(cycle_delay):
                yield self.wait_clock()
            self.pkt_out_pipe.put((meta, pkt))
            self.pkt_cnt += 1

class PktSender(HW_sim_object):
    def __init__(self, env, period, pkt_out_pipe, done_pipe, pkts, ranks):
        super(PktSender, self).__init__(env, period)
        self.pkt_out_pipe = pkt_out_pipe
        self.done_pipe = done_pipe
        self.pkts = []
        self.run(pkts, ranks)

    def run(self, pkts, ranks):
        self.env.process(self.send_pkts(pkts, ranks))

    def send_pkts(self, pkts, ranks):
        for pkt, rank in zip(pkts, ranks):
            self.pkt_out_pipe.put((rank, pkt))
            self.pkts.append((self.env.now, rank, pkt))
            yield self.done_pipe.get()


class PktReceiver(HW_sim_object):
    def __init__(self, env, period, pkt_in_pipe, ready_pipe, rate):
        super(PktReceiver, self).__init__(env, period)
        self.pkt_in_pipe = pkt_in_pipe
        self.ready_pipe = ready_pipe
        self.rate = rate
        self.pkts = []

        self.run()

    def run(self):
        self.env.process(self.rcv_pkts())

    def rcv_pkts(self):
        while not self.sim_done:
            self.ready_pipe.put(1)
            (rank, pkt) = yield self.pkt_in_pipe.get()
            pkt_time = len(pkt)*8/self.rate # ns
            cycle_delay = int(pkt_time/NSEC_PER_CYCLE + 0.5)
            for i in range(cycle_delay-2):
                yield self.wait_clock()
            self.pkts.append((self.env.now, rank, pkt))


class Arbiter(HW_sim_object):
    def __init__(self, env, period, input_pipes, output_pipe):
        super(Arbiter, self).__init__(env, period)
        self.input_pipes = input_pipes
        self.output_pipe = output_pipe
        self.pkts = []

        self.run()

    def run(self):
        self.env.process(self.arbitrate())


    def arbitrate(self):
        """
        Arbitrate between the input pipes and create one output pipe
        """
        while not self.sim_done:
            for pipe in self.input_pipes:
                if len(pipe.items) > 0:
                    (meta, pkt) = yield pipe.get()
                    self.output_pipe.put((meta, pkt))
                    self.pkts.append((self.env.now, deepcopy(meta), pkt.copy()))
                yield self.wait_clock()





