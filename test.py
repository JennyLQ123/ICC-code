switch_num=20

stable_link_list=[] #up and down link, the total is 15
unstable_link_list=[] #left and dowm link, the total is 16
for i in range(switch_num-1):
    if i%4==3:
        pass
    else:
        stable_link_list.append(str(i).zfill(2)+"-"+str(i+1).zfill(2))
for i in range(switch_num-4):
    unstable_link_list.append(str(i).zfill(2)+"-"+str(i+4).zfill(2))

EDGES=stable_link_list+unstable_link_list #edges set, including 31 pairs, A-B,(A<B)

E2I={}   #edges set, including 62 pairs
for i,e in enumerate(EDGES):
    E2I[e]=i
    E2I[e[-2:]+"-"+e[:2]]=i

print E2I
