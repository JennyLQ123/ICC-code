import pickle
import random

with open("path.pickle","r") as f:
  PATHS=pickle.load(f)
UPATH=["01","02","07","08","61","62","67","68"]

res={}

for p in UPATH:
  m1=10
  m2=10
  ms1=""
  ms2=""
  for _ in PATHS[p]:
    if(len(_)<m1):
      ms2=ms1
      m2=m1
      m1=len(_)
      ms1=_
    elif(len(_)<m2):
      ms2=_
      m2=len(_)
  res[p]=[ms1,ms2]

print res
