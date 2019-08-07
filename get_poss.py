import pickle

s2p={"1":1,"-1":0,"4":3,"-4":2}

def edges(s,n,d,path):    #generate the all paths
    #s,n, d  are the interger, and path is string array,eg['01',['00']]
    if n==d and len(path)<8:
        p=""
        for i in range(1,len(path)):
            port=s2p[str(path[i]-path[i-1])]
            p=p+str(port)
        res[str(s).zfill(2)+str(d).zfill(2)].append(p)
        return
    for i in [+1,-1,+4,-4]:
        if (n%4==3 and i==1) or (n%4==0 and i==-1):
            continue
        if i+n<20 and i+n>=0 and ((i+n) not in path) and len(path)<8:
            path.append(n+i)
            edges(s,n+i,d,path)
            path.pop()

pair=['1903', '0319', '1908', '0819', '1910', '1019', '1600', '0016', '1611', '1116', '1609', '0916']
# '1903', '0319', '1908', '0819', '1910', '1019', '1600', '0016', '1611', '1116', '1609', '0916'
res={i:[] for i in pair}

rres={i:[] for i in pair}

for p in pair:
    edges(int(p[0:2]),int(p[0:2]),int(p[-2:]),[int(p[0:2])])

for i in pair:
  rres[i]=sorted(res[i],key=lambda i:len(i))[:10]
print rres
with open("path.pickle","w") as f:
  pickle.dump(rres,f)
