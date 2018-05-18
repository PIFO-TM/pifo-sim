#!/usr/bin/env python

import simpy
from utils.hwsim_tools import *
from pifo_model import PIFO

from utils.stats import flow_stats
import matplotlib
import matplotlib.pyplot as plt
import argparse

class PIFO_tb(HW_sim_object):
    def __init__(self, env, period, pkts, ranks):
        super(PIFO_tb, self).__init__(env, period)

        self.pifo_r_in_pipe = simpy.Store(env)
        self.pifo_r_out_pipe = simpy.Store(env)
        self.pifo_w_in_pipe = simpy.Store(env)
        self.pifo_w_out_pipe = simpy.Store(env)

        self.egress_link_rate = 10 # Gbps

        self.pifo = PIFO(env, period, self.pifo_r_in_pipe, self.pifo_r_out_pipe, self.pifo_w_in_pipe, self.pifo_w_out_pipe)
        self.sender = PktSender(env, period, self.pifo_w_in_pipe, self.pifo_w_out_pipe, pkts, ranks)
        self.receiver = PktReceiver(env, period, self.pifo_r_out_pipe, self.pifo_r_in_pipe, self.egress_link_rate)

        self.env.process(self.wait_complete(len(pkts))) 

    def wait_complete(self, num_pkts):

        # wait for receiver to receive all pkts
        while len(self.receiver.pkts) < num_pkts:
            yield self.wait_clock()

        self.pifo.sim_done = True
        self.receiver.sim_done = True


def plot_stats(input_pkts, output_pkts, egress_link_rate):
    # convert cycles to ns and remove metadata from pkt_list
    input_pkts = [(tup[0]*5, tup[2]) for tup in input_pkts]
    output_pkts = [(tup[0]*5, tup[2]) for tup in output_pkts]
    print 'input_pkts:  (start, end) = ({} ns, {} ns)'.format(input_pkts[0][0], input_pkts[-1][0])
    print 'output_pkts: (start, end) = ({} ns, {} ns)'.format(output_pkts[0][0], output_pkts[-1][0])
    flowID_tuple = ((IP, 'sport'),)
    input_stats  = flow_stats(flowID_tuple, input_pkts)
    output_stats = flow_stats(flowID_tuple, output_pkts)
    # create plots
    fig, axarr = plt.subplots(2)
    plt.sca(axarr[0])
    input_stats.plot_rates('Input Flow Rates', linewidth=3)
    plt.sca(axarr[1])
    output_stats.plot_rates('Output Flow Rates', ymax=egress_link_rate*1.5, linewidth=3)

    font = {'family' : 'normal',
            'weight' : 'bold',
            'size'   : 22}
    matplotlib.rc('font', **font)
    plt.show()


def read_rank_file(filename):
    ranks = []
    with open(filename) as f:
        for line in f:
             try:
                 ranks.append(int(line))
             except ValueError as e:
                 print >> sys.stderr, 'ERROR: Encountered invalid value in rank file: {}'.format(line)
                 sys.exit(1)
    return ranks

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('pkts', type=str, help="pcap file that contains the packets to be applied in the simulation")
    parser.add_argument('ranks', type=str, help="text file that contains the rank for each packet")
    args = parser.parse_args()

    try:
        pkts = rdpcap(args.pkts)
    except IOError as e:
        print >> sys.stderr, "ERROR: failed to read pcap file: {}".format(args.pkts)
        sys.exit(1)

    ranks = read_rank_file(args.ranks)

    env = simpy.Environment()
    period = 1
    tb = PIFO_tb(env, period, pkts, ranks)
    env.run()

    plot_stats(tb.sender.pkts, tb.receiver.pkts, tb.egress_link_rate)


if __name__ == '__main__':
    main()

