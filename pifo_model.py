
import sys, os
from scapy.all import *
import simpy
from heapq import heappush, heappop, heapify
from utils.hwsim_tools import *

class PIFO(HW_sim_object):
    def __init__(self, env, period, r_in_pipe, r_out_pipe, w_in_pipe, w_out_pipe, write_latency=1, read_latency=1, max_size=None):
        """
        r_in_pipe  : used to receive read requests
        r_out_pipe : used to return read result
        w_in_pipe  : used to receive write data
        w_out_pipe : used to indicate write completion 
        """
        super(PIFO, self).__init__(env, period)

        self.r_in_pipe = r_in_pipe
        self.r_out_pipe = r_out_pipe
        self.w_in_pipe = w_in_pipe
        self.w_out_pipe = w_out_pipe
        self.write_latency = write_latency
        self.read_latency = read_latency
        self.values = []

        self.max_size = max_size
        self.drop_cnt = 0

        # register processes for simulation
        self.run()

    def run(self):
        self.env.process(self.write_sm())
        self.env.process(self.read_sm())

    def write_sm(self):
        """
        State machine to write incomming data into pifo
        """
        while not self.sim_done:
            # wait to receive incoming data
            (rank, data) = yield self.w_in_pipe.get()
            # model write latency
            for i in range(self.write_latency):
                yield self.wait_clock()
            # write pkt and metadata into pifo
            if self.max_size is None or len(self.values) < self.max_size:
                heappush(self.values, (rank, data))
            else:
                heappush(self.values, (rank, data))
                self.values.remove(max(self.values))
                heapify(self.values)
                self.drop_cnt += 1
            # indicate write_completion
            done = 1
            self.w_out_pipe.put(done)    

    def read_sm(self):
        """
        State machine to read data from pifo
        """
        while not self.sim_done:
            # wait to receive a read request
            read_req = yield self.r_in_pipe.get()
            # model read latency
            for i in range(self.read_latency):
                yield self.wait_clock()
            # try to read data from pifo
            read_complete = False
            while not read_complete and not self.sim_done:
                if len(self.values) > 0:
                    (rank, data) = heappop(self.values)
                    self.r_out_pipe.put((rank, data))
                    read_complete = True
                else:
                    yield self.wait_clock()


