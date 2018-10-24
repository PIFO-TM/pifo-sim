
from scapy.all import *

NUM_PKTS = 1000

MAC1 = "08:11:11:11:11:08"
MAC2 = "08:22:22:22:22:08"
MAC3 = "08:33:33:33:33:08"
MAC4 = "08:44:44:44:44:08"

IP1 = '10.1.1.1'
IP2 = '10.2.2.2'
IP3 = '10.3.3.3'
IP4 = '10.4.4.4'

def pad_pkt(pkt, size):
    if len(pkt) >= size:
        return pkt
    else:
        return pkt / ('\x00'*(size - len(pkt)))

def write_q_ids(q_ids, filename):
    with open(filename, 'w') as f:
        for qid in q_ids:
            f.write('{}\n'.format(qid))

def gen_exp0_data():
    """
    Experiment 0:
        - 1000 100B packets
    """
    flow1_pkt = pad_pkt(Ether(src=MAC1, dst=MAC2) / IP(src=IP1, dst=IP2) / TCP(sport=1), 100)
    pkts = [flow1_pkt]*1000
    wrpcap('exp0_pkts.pcap', pkts)
    q_ids = [0]*len(pkts)
    write_q_ids(q_ids, 'exp0_q_ids.txt')

def gen_exp1_data():
    """
    Experiment 1:
      - Flow 1 - small 100B packets at 1 Gbps, high priority
      - Flow 2 - large 300B packets at 3 Gbps, low priority
    """
    flow1_pkt = pad_pkt(Ether(src=MAC1, dst=MAC2) / IP(src=IP1, dst=IP2) / TCP(sport=1), 100)
    flow2_pkt = pad_pkt(Ether(src=MAC3, dst=MAC4) / IP(src=IP3, dst=IP4) / TCP(sport=2), 300)
    pkt_pattern = [flow2_pkt] + [flow1_pkt]
    qid_pattern = [1] + [0]
    pkts = pkt_pattern*(NUM_PKTS/len(pkt_pattern))
    q_ids = qid_pattern*(NUM_PKTS/len(qid_pattern))
    wrpcap('exp1_pkts.pcap', pkts)
    write_q_ids(q_ids, 'exp1_q_ids.txt')

def main():
    gen_exp0_data()
    gen_exp1_data()

if __name__ == '__main__':
    main()

