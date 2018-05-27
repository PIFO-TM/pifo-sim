
import sys, os
from scapy.all import *
import simpy
from utils.hwsim_tools import *

class StrictPipe(HW_sim_object):
    def __init__(self, env, period, r_in_pipe, r_out_pipe, w_in_pipe, w_out_pipe):
        """
        r_in_pipe  : used to receive read result ACK
        r_out_pipe : used to return read result
        w_in_pipe  : used to receive write data
        w_out_pipe : used to indicate write completion 
        """
        super(StrictPipe, self).__init__(env, period)

        # Top level interface
        self.r_in_pipe = r_in_pipe
        self.r_out_pipe = r_out_pipe
        self.w_in_pipe = w_in_pipe
        self.w_out_pipe = w_out_pipe

        # register processes for simulation
        self.run()

    def run(self):
        self.env.process(self.compute_rank())

    def compute_rank(self):
        """
        Pipeline to compute rank for pkt
        """
        while not self.sim_done:
            # wait to receive incomming pkt
            (q_id, pkt) = yield self.w_in_pipe.get()
            self.w_out_pipe.put(1)

            rank = pkt.sport

            self.r_out_pipe.put((rank, q_id, pkt))
            yield self.r_in_pipe.get()

