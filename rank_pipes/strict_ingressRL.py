
import sys, os
from scapy.all import *
import simpy
from utils.hwsim_tools import *

TARGET_RATE = 1.5 # Gbps
MAX_BURST = 1500 # bytes
#MAX_BURST = 100 # bytes

class StrictIngressRLPipe(HW_sim_object):
    def __init__(self, env, period, r_in_pipe, r_out_pipe, w_in_pipe, w_out_pipe):
        """
        r_in_pipe  : used to receive read result ACK
        r_out_pipe : used to return read result
        w_in_pipe  : used to receive write data
        w_out_pipe : used to indicate write completion 
        """
        super(StrictIngressRLPipe, self).__init__(env, period)

        # Top level interface
        self.r_in_pipe = r_in_pipe
        self.r_out_pipe = r_out_pipe
        self.w_in_pipe = w_in_pipe
        self.w_out_pipe = w_out_pipe

        # tokens for rate limiting
        # one token = 1 byte
        self.tokens = MAX_BURST
        self.tokens_per_cycle = TARGET_RATE*NSEC_PER_CYCLE/8.0

        self.last_time = 0

        # register processes for simulation
        self.run()

    def run(self):
        self.env.process(self.refill_tokens())
        self.env.process(self.compute_rank_and_time())

    def refill_tokens(self):
        """
        Continuously refill tokens at TARGET_RATE up until MAX_BURST
        """
        while not self.sim_done:
            if self.tokens < MAX_BURST:
                self.tokens += self.tokens_per_cycle
                self.tokens = MAX_BURST if self.tokens > MAX_BURST else self.tokens
            yield self.wait_clock()


    def compute_rank_and_time(self):
        """
        Pipeline to compute rank and send_time for pkt
        """
        while not self.sim_done:
            # wait to receive incomming pkt
            (q_id, pkt) = yield self.w_in_pipe.get()
            self.w_out_pipe.put(1)

            # compute scheduling rank
            rank = pkt.sport

#            print '------------------------------------------------------------------------------------------------'
#            print 'RankPipe: computing send_time: now = {}, len(pkt) = {}, tokens = {}, last_time = {}'.format(self.env.now, len(pkt), self.tokens, self.last_time)
            # compute shaping send_time
            if len(pkt) < self.tokens:
                send_time = self.env.now
                self.tokens -= len(pkt)
            else:
                send_time = self.last_time + (len(pkt) - self.tokens)/self.tokens_per_cycle
                self.tokens = 0
#            print 'RankPipe: computed send_time = {}, tokens = {}'.format(send_time, self.tokens)

            self.last_time = send_time
            self.r_out_pipe.put((rank, send_time, q_id, pkt))
            yield self.r_in_pipe.get()

