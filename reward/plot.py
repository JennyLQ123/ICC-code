import numpy as np
import matplotlib.pyplot as plt
import random
from class_define import MaxMinNormalization

with open("reward/flow_1.2","r") as f:
    a=[float(x) for x in f.read().strip().split(" ")]
#with open("packet_load_1.1","r") as f:
#    b=[float(x) for x in f.read().strip().split(" ")]
#with open("packet_load_1.2","r") as f:
#    c=[float(x) for x in f.read().strip().split(" ")]
#with open("res_linear","r") as f:
#    d=[float(x) for x in f.read().strip().split(" ")]

def smooth_line(a):
	t=[(a[i]*8/9.+a[i+1]/9.) for i in range((len(a)-1))] #smooth the line
	for i in range((len(a)-1)):
    		a.insert(2*i+1,t[i])
# def b(a,st,tar):
#     a.extend([a[-1]*((st-i)/float(st))+tar*(i/float(st)) for i in [j+5*random.random() for j in range(1,st+1)]])
def extend_func(x,length):
    if len(x)<length:
        x.extend([x[-1]]*(length-len(x)))
    else:
        x=x[:length]

smooth_line(a)
#smooth_line(b)
#smooth_line(c)
#extend_func(b,len(a))
#extend_func(c,len(a))
#extend_func(d,len(a))
def normallization(a):
	return [MaxMinNormalization(x,np.max(a),np.min(a)) for x in a]
#	return [a[i]/b[i] for i in range(len(a))]
a=normallization(a)
#b=normallization(b)
x=[i for i in range(len(a))]
plt.plot(x,a,color="red",label="PPO_1.0",linewidth=2)
#plt.plot(x,b,color="blue",label="PPO_1.1",linewidth=2)
#plt.plot(x,c,color="green",label="PPO_1.2",linewidth=2)
#plt.plot(x,d,color="black",label="LINEAR",linewidth=2)
plt.xlabel("training epoch")
plt.legend(loc="best")
plt.ylabel("max utilization")
plt.show()
#print x,a
