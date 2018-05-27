
# PIFO Simulator

A simple simulator that accepts as input a packet trace (pcap file) and
a text file that contains the queue ID for each packet. It will plot the input
and output flow rates as well as the queue sizes.

```
$ ./pifo_tb.py --help
usage: pifo_tb.py [-h] pkts qids

positional arguments:
  pkts        pcap file that contains the packets to be applied in the
              simulation
  qids        text file that contains the q_id that each packet should enter
              into
```


