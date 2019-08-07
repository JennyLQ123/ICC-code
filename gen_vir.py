with open("raw_data/ecmp401","r") as f:
    a=[i for i in f.read().strip().split("\n")[1:21]]

a=[[float(_) for _ in i.strip().split(" ")] for i in a]
res=[]
for i in a:
    v=sum(i)/len(i)
    res.append([1 if(_>2*v)or(_>1.7) else 0 for _ in i])

for i in res:
    print i
