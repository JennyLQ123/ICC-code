import pickle

SWITCH_TO_SWITCH_PORT=[[] for i in range(20)]
for i in range(20):
    for j in range(20):
        if i==j:
            SWITCH_TO_SWITCH_PORT[i].append(100)
        elif j-i==1 and j%4!=0:
            SWITCH_TO_SWITCH_PORT[i].append(1)
        elif j-i==4:
            SWITCH_TO_SWITCH_PORT[i].append(3)
        elif j-i==-1 and j%4!=3:
            SWITCH_TO_SWITCH_PORT[i].append(0)
        elif j-i==-4:
            SWITCH_TO_SWITCH_PORT[i].append(2)
        else:
            SWITCH_TO_SWITCH_PORT[i].append(100)

def edges(s,n,d,path):    #generate the all paths
    #s,n, d  are the interger, and path is string array,eg['01',['00']]
    if n==d and len(path)<10:
        res[str(s).zfill(2)+str(d).zfill(2)].append(path[:])
        return
    if len(path)>8:
        return
    for i in range(20):
        if (SWITCH_TO_SWITCH_PORT[n][i]!=100 and i not in path):
            path.append(i)
            edges(s,i,d,path)
            path.pop()


# '1903', '0319', '1908', '0819', '1910', '1019', '1600', '0016', '1611', '1116', '1609', '0916'
#pair=['1903', '0319', '1908', '0819', '1910', '1019', '1600', '0016', '1611', '1116', '1609', '0916']
pair=['0003','0008','0009','0010','0019','1611','1603','1608','1609','1610','1103',"1108","1109","1110","1119"]      #the target pairs of nodes
res={i:[] for i in pair}

rres={i:[] for i in pair}

for p in pair:
    edges(int(p[0:2]),int(p[0:2]),int(p[-2:]),[int(p[0:2])])

for i in pair:
  rres[i]=sorted(res[i],key=lambda x:len(x))[:10]
print rres
#with open("path.pickle","wb") as f:
with open("path-packet.pickle",'wb') as f:
  pickle.dump(rres,f)
