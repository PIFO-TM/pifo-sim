
# PIFO Simulator

A simple simulator that accepts as input a packet trace (pcap file) and
a text file that contains the rank of each packet. It will plot the input
and output flow rates.

```
$ ./pifo_tb.py --help
usage: pifo_tb.py [-h] pkts ranks

positional arguments:
  pkts        pcap file that contains the packets to be applied in the
              simulation
  ranks       text file that contains the rank for each packet
```


