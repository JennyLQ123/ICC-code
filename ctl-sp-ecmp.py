import sys
import random
from thrift.transport import TTransport
from thrift.transport import TSocket
from thrift.protocol import TBinaryProtocol
from thrift.protocol import TMultiplexedProtocol
import runtimedata
from bm_runtime.standard import Standard
from bm_runtime.standard.ttypes import *
import math
import time
from scapy.all import *
import threading
import re
from time import sleep
from scapy.all import *
import threading
import time
from multiprocessing import Process,Queue
from multiprocessing import Pool
import subprocess
import os,random
import int_paser
import pickle
import tensorflow as tf
import numpy as np
from mppo import PPO
from class_define import SWITCH,thrift_connect,MaxMinNormalization,Z_ScoreNormalization,sigmoid,SciKitLearn

EP_MAX = 1000
EP_LEN = 20
EP_START = 0
BATCH = 5
GAMMA = 0.9

runtime=4

switch_num=20
switch_to_port={"0":-1,"1":1,"2":-4,"3":4}

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

S2IP={str(i).zfill(2):"10.0.%d.1"%(i,) for i in range(switch_num)}
S2ETH={str(i).zfill(2):"10:00:11:11:%d:12"%(i,) for i in range(switch_num)}

with open("path.pickle","r") as f:
    PATHS=pickle.load(f)
UPATH=['1903', '0319', '1908', '0819','1910', '1019', '1600', '0016', '1611', '1116', '1609', '0916']      #the target pairs of nodes

flowsHandleIDdic={}

routeid_handle={}

SWITCH_TO_HOST_PORT=10

def switchConnect():
    try :
        switch_list=[]
        for index in range(switch_num):
            sw=SWITCH(9000+index,"127.0.0.1")
            switch_list.append(sw)
    except:
        print "connect error"
    return switch_list
#write default table rules add int
def ConfigureDefaultRules(sw,swid):
    sw.set_default_action(
        table_name="add_first_int",
        action="ad_f_int",
        runtime_data=[str(swid)],
        runtime_data_types=['9']
    )
    sw.set_default_action(
        table_name="add_else_int",
        action="ad_e_int",
        runtime_data=[str(swid)],
        runtime_data_types=['9']
    )
#create routeid group of a switch
def writeRouteidTable(switch,routeid_list,actionProfileName,dst_ip_addr):
    routeid_num=len(routeid_list) #2
        #create_group
    group_info=switch.create_group(actionProfileName)
        ##add set_routeid action to member
    for i in range(routeid_num):
        member_info=switch.act_prof_add_member(action_profile_name=actionProfileName,
                            action_name="set_routeid",
                            runtime_data=[str(routeid_list[i])],
                            runtime_data_types=['12'])
        routeid_handle[str(routeid_list[i])]=member_info
        switch.add_member_to_group(action_profile_name=actionProfileName,
                            mbr_handle=member_info,
                            grp_handle=group_info)
        #add table_entry
    switch.add_entry_to_group(table_name="create_flow_header",match_key=[dst_ip_addr,"24"],
                            match_key_types=["ip"],grp_handle=group_info)

#write table routeid_fwd
def writeFwdTable(switch_list,flow_rules,route_id,dst_ip_addr,dst_eth_addr):
    flowsHandleIDdic[str(route_id)]={}
    Hop = len(flow_rules)
    sNode=int(route_id[2:4])
    dNode=int(route_id[4:6])
    index=int(route_id[:2])
    first_hop=switch_list[sNode].table_add_exact(
        table="routeid_fwd",
        action="ipv4_fwd",
        match_key=[str(route_id)],
        match_key_types=['12'],
        runtime_data=[str(flow_rules[0])],
        runtime_data_types=['9']
    )
    flowsHandleIDdic[str(route_id)][sNode]=[]
    flowsHandleIDdic[str(route_id)][sNode].append(first_hop)
    flowsHandleIDdic[str(route_id)][sNode].append(flow_rules[0])
    if Hop>=2:
        before_node=sNode
        for i in range(1,Hop):
            node=before_node+switch_to_port[flow_rules[i-1]]
            info=switch_list[node].table_add_exact(
                table="routeid_fwd",
                action="ipv4_fwd",
                match_key=[str(route_id)],
                match_key_types=['12'],    #lpm
                runtime_data=[str(flow_rules[i])],
                runtime_data_types=['9']
            )
            before_node=node
            flowsHandleIDdic[str(route_id)][node]=[]
            flowsHandleIDdic[str(route_id)][node].append(info)
            flowsHandleIDdic[str(route_id)][node].append(flow_rules[i])
    last_hop=switch_list[dNode].table_add_exact(
            table="routeid_fwd",
            action="fwd2host",
            match_key=[str(route_id)],
            match_key_types=['12'],
            runtime_data=[dst_eth_addr,str(SWITCH_TO_HOST_PORT)],
            runtime_data_types=['mac','9']
        )
#create new flow rules between two nodes
def flowRulesInit(switch_list,routeid_list,flowRules_list,dst_ip_addr,dst_eth_addr):
    sNode=int(routeid_list[0][2:4])
    if len(routeid_list) != len(flowRules_list):
        print "routeid num doesn't match flow_rules"
        return
    for i in range(len(routeid_list)):
        if routeid_list[i] in routeid_handle:
            print "route_id has already add in group please use flow rules modify"
    writeRouteidTable(switch=switch_list[sNode],routeid_list=routeid_list,actionProfileName="set_routeid_profile",dst_ip_addr=dst_ip_addr)
    for i in range(len(routeid_list)):
        writeFwdTable(switch_list=switch_list,flow_rules=flowRules_list[i], route_id=routeid_list[i],dst_ip_addr=dst_ip_addr, dst_eth_addr=dst_eth_addr)

def flowRulesModify(switch_list,route_id,flow_rules):
    new_path=[]
    entry_h={}
    old_path=flowsHandleIDdic[route_id]
    sNode=int(route_id[2:4])
    dNode=int(route_id[-2:])
    node=sNode
    for i in flow_rules:
        new_path.append(node)
        node=node+switch_to_port[i]
    new_path.reverse()
    flow_rules=flow_rules[::-1]
    for index,i in enumerate(new_path):
        if not old_path.has_key(i):
            info=switch_list[i].table_add_exact(
                table="routeid_fwd",
                action="ipv4_fwd",
                match_key=[str(route_id)],
                match_key_types=['12'],    #lpm
                runtime_data=[str(flow_rules[index])],
                runtime_data_types=['9']
            )
            entry_h[i]=[]
            entry_h[i].append(info)
            entry_h[i].append(flow_rules[index])
        else:
            entry_h[i]=old_path[i]
            if old_path[i][1]!=flow_rules[index]:
                info=switch_list[i].table_modify(
                    table="routeid_fwd",
                    handle=int(old_path[i][0]),
                    action="ipv4_fwd",
                    runtime_data=[str(flow_rules[index])],
                    runtime_data_types=['9']
                )
                entry_h[i][1]=flow_rules[index]
            del old_path[i]
    for i in old_path:
        switch_list[i].table_delete(
            table="routeid_fwd",
            entry_handle=int(old_path[i][0])
        )
    flowsHandleIDdic[route_id]=entry_h

def NormallizeData(data_info,flag,switch_list,counterName):  #normalize the int information, the latter is more important
    int_recv={}
    int_recv["counter_statics"]={}
    if flag.empty():#during collecting
        for i in range(switch_num):         #initial the int_recv
            int_recv[str(i)]=0
            switch_list[i].counter_reset(counter_name=counterName)
        time.sleep(runtime)
        flag.put("1")        #pause collecting, read INT information
        while data_info.empty()==False:
            one_info=data_info.get(True)
            for key in one_info:
                int_recv[key]=(int_recv[key]+one_info[key])/2
        s_p={"4":{"s":3,"d":2},"1":{"s":1,"d":0}}
        for e in EDGES:
            sNode=int(e[0:2])
            dNode=int(e[-2:])
            s_count=switch_list[sNode].counter_read(counter_name=counterName,index=s_p[str(dNode-sNode)]["s"])
            d_count=switch_list[dNode].counter_read(counter_name=counterName,index=s_p[str(dNode-sNode)]["d"])
            int_recv["counter_statics"][e]=s_count.bytes+d_count.bytes
    return int_recv

def reset(data_info,flag,switch_list):
    for p_ in UPATH:
        flowRulesModify(switch_list,"01"+p_,PATHS[p_][0])
        flowRulesModify(switch_list,"02"+p_,PATHS[p_][1])
    int_data=NormallizeData(data_info,flag,switch_list,counterName="my_counter")
    s= [int_data[str(i)] for i in range(switch_num)]
    s_=[MaxMinNormalization(x,20.0,0) for x in s]
    l=[int_data["counter_statics"][x] for x in EDGES]
    l_=[MaxMinNormalization(x,np.max(l),np.min(l)) for x in l]
    s_.extend(l_)
    flag.get()  #continue to collect data
    return np.array(s_)

def step(data_info,flag,switch_list,w):
    print "modify flow rules"
    for k_ in w:
        flowRulesModify(switch_list,k_,w[k_])
    int_data=NormallizeData(data_info,flag,switch_list,counterName="my_counter")
    s= [int_data[str(i)] for i in range(switch_num)]
    s_=[MaxMinNormalization(x,20.0,0) for x in s]
    l=[int_data["counter_statics"][x] for x in EDGES]
    l_=[MaxMinNormalization(x,np.max(l),np.min(l)) for x in l]
    s_.extend(l_)
    rl=[int_data["counter_statics"][x] for x in EDGES]
    rl_ = [MaxMinNormalization(x,12500000.0,np.min(rl)) for x in rl]
    r = max(rl_)/-.1
    flag.get()  #continue to collect data
    return np.array(s_),r

def select_single_SP(sp,a):
    sp1="01"+sp
    sp2="02"+sp
    w={sp1:"",sp2:""}
    paths=PATHS[sp]
    m1=9e9
    for p in paths:
        mt=0
        for i in p:
            mt+=1
        if mt<m1:
            m1=mt
            w[sp1]=p
    w[sp2]=w[sp1]
    return w

def select_two(sp,a):
    sp1="01"+sp
    sp2="02"+sp
    sNode=int(sp[0:2])
    dN=int(sp[-2:])
    w={sp1:"",sp2:""}
    paths=PATHS[sp]
    m1=9e9
    m2=9e9
    listmin=[]
    for p in paths:
        mt=0
        node=sNode
        for i in p:
            dNode=node+switch_to_port[i]
            mt+=1
            node=dNode
        if mt<m1:
            m1=mt
            w[sp1]=p
    paths.remove(w[sp1])
    node=sNode
    for i in w[sp1]:
        dNode=node+switch_to_port[i]
        listmin.append(dNode)
        node=dNode
    for p in paths:
        mt=0
        cross_flag=1
        node=sNode
        for i in p:
            dNode=node+switch_to_port[i]
            if dNode in listmin and dNode!=dN:
                cross_flag=0
                break
            else:
                mt+=1
            node=dNode
        if cross_flag and mt<m2:
            m2=mt
            w[sp2]=p
    seed=str(random.randint(1,2)).zfill(2)+sp
    a={}
    a[seed]=w[seed]
    return w

def controllerMain(data_info,flag):
    switch_list=switchConnect()
    for i in range(switch_num):
        ConfigureDefaultRules(switch_list[i],swid=i)
    ppo = PPO()
    all_ep_r=[]
    for p_ in UPATH:
        flowRulesInit(switch_list,routeid_list=["01"+p_,"02"+p_],flowRules_list=[PATHS[p_][0],PATHS[p_][1]],dst_ip_addr=S2IP[p_[-2:]], dst_eth_addr=S2ETH[p_[-2:]])
    print "initial success"
    time.sleep(5)
    for ep in range(EP_START,EP_MAX):
        s = reset(data_info,flag,switch_list)
        buffer_s, buffer_a, buffer_r = [], [], []
        ep_r = 0
        for t in range(EP_LEN):    # in one episode
            a = ppo.choose_action(s)
            sp = UPATH[t%len(UPATH)]
            w = select_two(sp,a)
            s_, r = step(data_info,flag,switch_list,w)
            buffer_s.append(s)
            buffer_a.append(a)
            buffer_r.append((r+8)/8)    # normalize reward, find to be useful
            s = s_
            ep_r += r
            print r
            # update ppo
            # if (t+1) % BATCH == 0 or t == EP_LEN-1:
            #     v_s_ = ppo.get_v(s_)
            #     discounted_r = []
            #     for r in buffer_r[::-1]:
            #         v_s_ = r + GAMMA * v_s_
            #         discounted_r.append(v_s_)
            #     discounted_r.reverse()
            #     bs, ba, br = np.vstack(buffer_s), np.vstack(buffer_a), np.array(discounted_r)[:, np.newaxis]
            #     buffer_s, buffer_a, buffer_r = [], [], []
            #     print "update ppo"
            #     ppo.update(bs, ba, br)
        if ep == 0: all_ep_r.append(ep_r)
        else: all_ep_r.append(all_ep_r[-1]*0.9 + ep_r*0.1)
        print(
            'Ep: %i' % ep,
            "|Ep_r: %i" % ep_r,
            )
        # if (ep%10==0):
        #     ppo.save("model/ppo%d"%(ep,))
        with open("res_flow_ecmp","w") as f:
            f.write(len(all_ep_r)*"%f "%tuple(all_ep_r))

if __name__=="__main__":
    data_info = Queue()   #the collected information, eg link-delay and queueing-delay
    flag = Queue()  #the flag of start and pause collection
    ts=[Process(target=int_paser.listen,args=("s%d-int"%(i,),data_info,flag)) for i in range(switch_num)]
    tc=Process(target=controllerMain,args=(data_info,flag))
    for t in ts:
        t.start()
    tc.start()
    for t in ts:
        t.join()
    tc.join()
