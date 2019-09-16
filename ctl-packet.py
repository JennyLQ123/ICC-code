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

runtime=5

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

S2IP={str(i).zfill(2):"10.0.%d.1"%(i,) for i in range(switch_num)}
S2ETH={str(i).zfill(2):"10:00:11:11:%d:12"%(i,) for i in range(switch_num)}
with open("path-packet.pickle","rb") as f:
    PATHS=pickle.load(f)
flowsHandleIDdic={}
#UPATH=['1908','1611','0819',"0016","1903","0916","1019",'1116',"0319","1600","1910","1609"]      #the target pairs of nodes
UPATH=['0003','0008','0009','0010','0019','1611','1603','1608','1609','1610','1103',"1108","1109","1110","1119"]      #the target pairs of nodes

routeid_member_handle={} #eg. routeid_member_handle={swid:{"010819":8,"020819":9},}
routeid_group_handle={}  #eg. routeid_group_handle={"0819":0}
SWITCH_TO_HOST_PORT=10
old_routeid_path={}
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
        table_name="add_load_info",
        action="add_l",
        runtime_data=[str(swid)],
        runtime_data_types=['9']
    )
#create routeid group of a switch
def writeRouteidTable(sNode,switch,routeid_list,actionProfileName,dst_ip_addr):
    routeid_num=len(routeid_list) #2
        #create_group
    group_info=switch.create_group(actionProfileName)
    routeid_group_handle[routeid_list[0][2:]]=group_info
        ##add set_routeid action to member
    for i in range(routeid_num):
        routeid_member_handle[sNode][routeid_list[i]]=[]
        member_info=switch.act_prof_add_member(action_profile_name=actionProfileName,
                            action_name="set_routeid",
                            runtime_data=[str(routeid_list[i])],
                            runtime_data_types=['16'])
        routeid_member_handle[sNode][routeid_list[i]].append(member_info)
        routeid_member_handle[sNode][routeid_list[i]].append(1)
        switch.add_member_to_group(action_profile_name=actionProfileName,
                            mbr_handle=member_info,
                            grp_handle=group_info)
    extra_routeid="03"+routeid_list[0][2:]
    routeid_member_handle[sNode][extra_routeid]=[]
    extra_member_info=switch.act_prof_add_member(action_profile_name=actionProfileName,
                        action_name="set_routeid",
                        runtime_data=[str(extra_routeid)],
                        runtime_data_types=['16'])
    routeid_member_handle[sNode][extra_routeid].append(extra_member_info)
    routeid_member_handle[sNode][extra_routeid].append(0)
        #add table_entry
    switch.add_entry_to_group(table_name="create_flow_header",match_key=[dst_ip_addr,4294967040],
                            match_key_types=["ip","32"],grp_handle=group_info)

#write table routeid_fwd
def writeFwdTable(switch_list,flow_rules,route_id,dst_ip_addr,dst_eth_addr):
    flowsHandleIDdic[str(route_id)]={}
    Hop = len(flow_rules)
    dNode=int(route_id[4:6])
    # first_hop=switch_list[sNode].table_add_exact(
    #     table="routeid_fwd",
    #     action="ipv4_fwd",
    #     match_key=[str(route_id)],
    #     match_key_types=['16'],
    #     runtime_data=[str(flow_rules[0])],
    #     runtime_data_types=['9']
    # )
    for i in range(Hop-1):
        s=int(flow_rules[i])
        port=SWITCH_TO_SWITCH_PORT[s][flow_rules[i+1]]
        info=switch_list[s].table_add_exact(
            table="routeid_fwd",
            action="ipv4_fwd",
            match_key=[str(route_id)],
            match_key_types=['16'],
            runtime_data=[str(port)],
            runtime_data_types=['9']
        )
        flowsHandleIDdic[str(route_id)][s]=[]
        flowsHandleIDdic[str(route_id)][s].append(info)
        flowsHandleIDdic[str(route_id)][s].append(port)
    # if Hop>=2:
    #     before_node=sNode
    #     for i in range(1,Hop):
    #         node=before_node+switch_to_port[flow_rules[i-1]]
    #         info=switch_list[node].table_add_exact(
    #             table="routeid_fwd",
    #             action="ipv4_fwd",
    #             match_key=[str(route_id)],
    #             match_key_types=['16'],    #lpm
    #             runtime_data=[str(flow_rules[i])],
    #             runtime_data_types=['9']
    #         )
    #         before_node=node
    #         flowsHandleIDdic[str(route_id)][node]=[]
    #         flowsHandleIDdic[str(route_id)][node].append(info)
    #         flowsHandleIDdic[str(route_id)][node].append(flow_rules[i])
    last_hop=switch_list[dNode].table_add_exact(
            table="routeid_fwd",
            action="fwd2host",
            match_key=[str(route_id)],
            match_key_types=['16'],
            runtime_data=[dst_eth_addr,str(SWITCH_TO_HOST_PORT)],
            runtime_data_types=['mac','9']
        )
#create new flow rules between two nodes
def flowRulesInit(switch_list,routeid_list,flowRules_list,dst_ip_addr,dst_eth_addr):
    sNode=int(routeid_list[0][2:4])
    if len(routeid_list) != len(flowRules_list):
        print "routeid num doesn't match flow_rules"
        return
    # for i in range(len(routeid_list)):
    #     if routeid_list[i] in routeid_member_handle[sNode]:
    #         print "route_id has already add in group please use flow rules modify"
    writeRouteidTable(sNode=sNode,switch=switch_list[sNode],routeid_list=routeid_list,actionProfileName="set_routeid_profile",dst_ip_addr=dst_ip_addr)
    for i in range(len(routeid_list)):
        writeFwdTable(switch_list=switch_list,flow_rules=flowRules_list[i], route_id=routeid_list[i],dst_ip_addr=dst_ip_addr, dst_eth_addr=dst_eth_addr)

def routeid_map(src_dst_pair): #new_route_id,old_route_id
    sNode=int(src_dst_pair[:2])
    A="01"+src_dst_pair
    B="02"+src_dst_pair
    C="03"+src_dst_pair
    member_set=routeid_member_handle[sNode]
    if A in member_set and member_set[A][1]==1:
        if B in member_set and member_set[B][1]==1:
            return C,B
        else:
            return B,A
    else:
        return A,C
next_delete_routeid=''  #in the next period, delete the last update old path
def flowRulesModify(switch_list,route_id,flow_rules,dst_eth_addr):
    entry_h={}
    new_path=flow_rules[::-1]
    old_path=flowsHandleIDdic[route_id] #old_path={swid:[mbr_handle,port]}
    #print "routeid:",route_id,"flow_rules:",flow_rules,"old_path:",old_path
    for index in range(1,len(new_path)): #index,i=flow_rules[index]
        port=SWITCH_TO_SWITCH_PORT[new_path[index]][new_path[index-1]]
        s=new_path[index]
        #print "s:",s,"port:",port
        if not old_path.has_key(s):
            info=switch_list[s].table_add_exact(
                table="routeid_fwd",
                action="ipv4_fwd",
                match_key=[str(route_id)],
                match_key_types=['12'],    #lpm
                runtime_data=[str(port)],
                runtime_data_types=['9']
            )
            entry_h[s]=[]
            entry_h[s].append(info)
            entry_h[s].append(port)
        else:
            entry_h[s]=old_path[s]
            if old_path[s][1]!=port:
                info=switch_list[s].table_modify(
                    table="routeid_fwd",
                    handle=int(old_path[s][0]),
                    action="ipv4_fwd",
                    runtime_data=[str(port)],
                    runtime_data_types=['9']
                )
                entry_h[s][1]=port
            del old_path[s]
    for i in old_path:
        switch_list[i].table_delete(
            table="routeid_fwd",
            entry_handle=int(old_path[i][0])
        )
    flowsHandleIDdic[route_id]=entry_h
    # #delete old path
    # global next_delete_routeid
    # print "srd-dst:",src_dst_pair
    # if next_delete_routeid:
    #     old_path=flowsHandleIDdic[next_delete_routeid]
    #     for i in old_path:
    #         switch_list[i].table_delete(
    #             table="routeid_fwd",
    #             entry_handle=int(old_path[i][0])
    #         )
    #     flowsHandleIDdic.pop(next_delete_routeid)
    # #initial variable: new_path(for routeid_fwd),new_route_id,old_route_id
    # new_path=[]
    # entry_h={}
    # new_route_id,old_route_id=routeid_map(src_dst_pair)
    # sNode=int(src_dst_pair[:2])
    # node=sNode
    #
    # for i in flow_rules:
    #     new_path.append(node)
    #     node=node+switch_to_port[i]
    # #update tha last hop
    # info=switch_list[node].table_add_exact(
    #         table="routeid_fwd",
    #         action="fwd2host",
    #         match_key=[str(new_route_id)],
    #         match_key_types=['16'],
    #         runtime_data=[dst_eth_addr,str(SWITCH_TO_HOST_PORT)],
    #         runtime_data_types=['mac','9']
    # )
    # entry_h[node]=[]
    # entry_h[node].append(info)
    # #update new_path
    # new_path.reverse()
    # flow_rules=flow_rules[::-1]
    #
    # for index,i in enumerate(new_path):
    #     info=switch_list[i].table_add_exact(
    #         table="routeid_fwd",
    #         action="ipv4_fwd",
    #         match_key=[str(new_route_id)],
    #         match_key_types=['16'],    #lpm
    #         runtime_data=[str(flow_rules[index])],
    #         runtime_data_types=['9']
    #     )
    #     entry_h[i]=[]
    #     entry_h[i].append(info)
    #     entry_h[i].append(flow_rules[index])
    #
    # flowsHandleIDdic[new_route_id]=entry_h
    #
    # #insert new_route_id in source switch
    # member_info=routeid_member_handle[sNode][new_route_id][0]
    # switch_list[sNode].add_member_to_group(action_profile_name="set_routeid_profile",
    #                     mbr_handle=member_info,
    #                     grp_handle=routeid_group_handle[src_dst_pair])
    # routeid_member_handle[sNode][new_route_id][1]=1
    # #delete old_route_id in source switch
    # #print sNode,new_route_id,old_route_id
    # switch_list[sNode].act_prof_remove_member_from_group(action_profile_name="set_routeid_profile",mbr_handle=routeid_member_handle[sNode][old_route_id][0],grp_handle=routeid_group_handle[src_dst_pair])
    # routeid_member_handle[sNode][old_route_id][1]=0
    # #update next_delete_routeid
    # next_delete_routeid=old_route_id
    # print "-------------------------------"

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
        for e in EDGES:
            sNode=int(e[0:2])
            dNode=int(e[-2:])
            s_count=switch_list[sNode].counter_read(counter_name=counterName,index=SWITCH_TO_SWITCH_PORT[sNode][dNode])
            d_count=switch_list[dNode].counter_read(counter_name=counterName,index=SWITCH_TO_SWITCH_PORT[dNode][sNode])
            int_recv["counter_statics"][e]=s_count.bytes+d_count.bytes
    return int_recv

def reset(data_info,flag,switch_list):
    #for p_ in UPATH:
    #    flowRulesModify(switch_list,"01"+p_,PATHS[p_][0],dst_eth_addr=S2ETH[p_[-2:]])
    #    flowRulesModify(switch_list,"02"+p_,PATHS[p_][1],dst_eth_addr=S2ETH[p_[-2:]])
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
    #w={s-d:new_path} k_=s-d
    for k_ in w:
        if w[k_]!='':
            flowRulesModify(switch_list,k_,w[k_],dst_eth_addr=S2ETH[k_[-2:]])
            old_routeid_path[k_[2:]][k_]=w[k_]
        else:
            print "no modify********"
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

def transform_value(a):
    k=2/(max(a)-min(a))
    a=[k*(x-min(a)) for x in a]
    return a

def select_single_SP(sp,a):
    w={sp:""}
    pi=[]
    s=[]
    paths=PATHS[str(sp)]
    sNode=int(sp[:2])
    c=old_routeid_path[sp]
    for i in c:
        s.append(i)
        pi.append(c[i])
    p1=pi[0]
    p2=pi[1]
    m1=9e9
    cmp1=0
    cmp2=0
    for p in paths:
        mt=0
        for i in range(len(p)-1):
            mt+=1
		#mt+=a[E2I[str(p[i]).zfill(2)+"-"+str(p[i+1]).zfill(2)]]
        if p==p1:
            cmp1=mt
        if p==p2:
            cmp2=mt
        if mt<m1:
            m1=mt
            w[sp]=p
    if cmp1>cmp2:
        if cmp1>m1*1.2:
            w={s[0]:w[sp]}
        else:
            w[sp]=""
    else:
        if cmp2>m1*1.2:
            w={s[1]:w[sp]}
        else:
            w[sp]=""
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
    return w

def controllerMain(data_info,flag):
    switch_list=switchConnect()
    for i in range(switch_num):
        ConfigureDefaultRules(switch_list[i],swid=i)
    for i in [19,3,8,10,16,0,11,9]:
        routeid_member_handle[i]={}
    ppo = PPO()
    all_ep_r=[]
    # ppo.load("model_packet/ppo%d"%(EP_START,))
    # with open("packet_load","r") as f:
    #    all_ep_r = [float(_) for _ in f.read().strip().split(" ")[:EP_START]]
    for p_ in UPATH:
        old_routeid_path[p_]={}
        #print p_,PATHS[p_]
        flowRulesInit(switch_list,routeid_list=["01"+p_,"02"+p_],flowRules_list=[PATHS[p_][0],PATHS[p_][1]],dst_ip_addr=S2IP[p_[-2:]], dst_eth_addr=S2ETH[p_[-2:]])
        old_routeid_path[p_]["01"+p_]=PATHS[p_][0]
        old_routeid_path[p_]["02"+p_]=PATHS[p_][1]
    print "initial success"
    time.sleep(5)
    for ep in range(EP_START,EP_MAX):
        s = reset(data_info,flag,switch_list)
        buffer_s, buffer_a, buffer_r = [], [], []
        ep_r = 0
        for t in range(EP_LEN):    # in one episode
            a = ppo.choose_action(s)
            a=transform_value(a)
            sp = UPATH[t%len(UPATH)]
            w = select_single_SP(sp,a)
            s_, r = step(data_info,flag,switch_list,w)
            buffer_s.append(s)
            buffer_a.append(a)
            buffer_r.append((r+8)/8)    # normalize reward, find to be useful
            s = s_
            ep_r += r
            print r
#            #update ppo
#            if (t+1) % BATCH == 0 or t == EP_LEN-1:
#                v_s_ = ppo.get_v(s_)
#                discounted_r = []
#                for r in buffer_r[::-1]:
#                    v_s_ = r + GAMMA * v_s_
#                    discounted_r.append(v_s_)
#                discounted_r.reverse()
#                bs, ba, br = np.vstack(buffer_s), np.vstack(buffer_a), np.array(discounted_r)[:, np.newaxis]
#                buffer_s, buffer_a, buffer_r = [], [], []
#                print "update ppo"
#                ppo.update(bs, ba, br)
        if ep == 0: all_ep_r.append(ep_r)
        else: all_ep_r.append(all_ep_r[-1]*0.9 + ep_r*0.1)
        print(
            'Ep: %i' % ep,
            "|Ep_r: %i" % ep_r,
            )
#        if (ep%10==0):
#            ppo.save("model_packet/ppo%d"%(ep,))
        with open("packet_load_ecmp_1.2","w") as f:
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
