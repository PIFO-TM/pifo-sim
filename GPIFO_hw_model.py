
import sys, os
from scapy.all import *
import simpy
from heapq import heappush, heappop, heapify
from utils.hwsim_tools import *

class PIFO(HW_sim_object):
    def __init__(self, env, period, r_in_pipe, r_out_pipe, w_in_pipe, w_out_pipe, rank_w_in_pipe, rank_w_out_pipe, rank_r_in_pipe, rank_r_out_pipe, buf_size=None, num_queues=1):
        """
        r_in_pipe  : used to receive read requests
        r_out_pipe : used to return read result
        w_in_pipe  : used to receive write data
        w_out_pipe : used to indicate write completion 
        """
        super(PIFO, self).__init__(env, period)

        # Top level interface
        self.r_in_pipe = r_in_pipe
        self.r_out_pipe = r_out_pipe
        self.w_in_pipe = w_in_pipe
        self.w_out_pipe = w_out_pipe

        # R/W interface to rank computation pipe
        self.rank_w_in_pipe = rank_w_in_pipe
        self.rank_w_out_pipe = rank_w_out_pipe
        self.rank_r_in_pipe = rank_r_in_pipe
        self.rank_r_out_pipe = rank_r_out_pipe

        self.values = []

        self.buf_size = buf_size
        self.num_queues = num_queues

        # The buffer is divided into some number of queues
        # Prior to entering the PIFO, packets must be assigned to a particular queue
        # A packet is dropped if the queue to which it is assigned is full when it arrives
        self.max_queue_size = None if buf_size is None else float(buf_size)/float(num_queues)
        self.queue_sizes = {}
        # Record queue sizes during experiment
        self.q_size_stats = {}
        self.times = []
        for i in range(num_queues):
            self.queue_sizes[i] = 0
            self.q_size_stats[i] = []
        self.drop_cnt = 0
        

        # register processes for simulation
        self.run()

    def run(self):
        self.env.process(self.write_rank_pipe_sm())
        self.env.process(self.write_pifo_sm())
        self.env.process(self.read_sm())
        self.env.process(self.record_q_sizes())

    def write_rank_pipe_sm(self):
        """
        State machine to write incomming data into rank computation pipe
        """
        while not self.sim_done:
            # wait to receive incoming data
            (q_id, pkt) = yield self.w_in_pipe.get()
            if q_id not in self.queue_sizes.keys():
                q_id = 0
            # write pkt and metadata into rank computation pipe only if queue is not full
            if self.max_queue_size is None or self.queue_sizes[q_id] + len(pkt) < self.max_queue_size:
                self.queue_sizes[q_id] += len(pkt)
                self.rank_w_in_pipe.put((q_id, pkt))
                yield self.rank_w_out_pipe.get() # wait for rank pipe ACK
            else:
                self.drop_cnt += 1
            # indicate write_completion
            self.w_out_pipe.put(1)

    def write_pifo_sm(self):
        """
        State machine to write incomming data into pifo
        """
        while not self.sim_done:
            # wait to receive incoming data
            (rank, q_id, pkt) = yield self.rank_r_out_pipe.get()
            heappush(self.values, (rank, q_id, pkt))
            self.rank_r_in_pipe.put(1)

    def read_sm(self):
        """
        State machine to read data from pifo
        """
        while not self.sim_done:
            # wait to receive a read request
            read_req = yield self.r_in_pipe.get()
            # try to read data from pifo
            read_complete = False
            while not read_complete and not self.sim_done:
                if len(self.values) > 0:
                    (rank, q_id, pkt) = heappop(self.values)
                    # decrement q_size
                    self.queue_sizes[q_id] -= len(pkt)
                    self.r_out_pipe.put((rank, pkt))
                    read_complete = True
                else:
                    yield self.wait_clock()


    def record_q_sizes(self):
        """
        Record queue sizes on every cycle
        """
        while not self.sim_done:
            self.times.append(self.env.now)
            for i in range(self.num_queues):
                self.q_size_stats[i].append(self.queue_sizes[i])
            yield self.wait_clock()


