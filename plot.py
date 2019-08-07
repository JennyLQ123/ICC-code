import matplotlib.pyplot as plt
import random

with open("flow_load","r") as f:
    a=[float(x) for x in f.read().strip().split(" ")]
with open("res_single","r") as f:
    b=[float(x) for x in f.read().strip().split(" ")]
with open("res_ecmp","r") as f:
    c=[float(x) for x in f.read().strip().split(" ")]
with open("res_linear","r") as f:
    d=[float(x) for x in f.read().strip().split(" ")]

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

extend_func(b,len(a))
extend_func(c,len(a))
extend_func(d,len(a))

x=[i for i in range(len(a))]
plt.plot(x,a,color="red",label="PPO",linewidth=2)
#plt.plot(x,b,color="blue",label="SP",linewidth=2)
#plt.plot(x,c,color="yellow",label="ECMP",linewidth=2)
#plt.plot(x,d,color="black",label="LINEAR",linewidth=2)
plt.xlabel("episode")
plt.legend(loc="best")
plt.ylabel("reward")
plt.show()
