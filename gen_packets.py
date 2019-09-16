from scapy.all import *
import random
src=[0,11,16]
dst=[3,8,10,9,19]
ps=[]

for i in range(1000):
    p = Ether(src="00:00:00:00:16:16",dst="00:00:00:00:07:07") / IP(src="2%d.0.%d.%d"%((i%4+4),random.randint(2,250),random.randint(2,250)),dst="10.0.%d.1"%(dst[i%5],)) / TCP() / Raw()
    ps.append(p)
wrpcap("16.packet",ps)
wrpcap("0.packet",ps)
wrpcap("11.packet",ps)
