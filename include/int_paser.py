from scapy.all import *
import threading
import time
from multiprocessing import Process,Queue
from multiprocessing import Pool
import os,random

#define how long to get the infomation
class INT(Packet):
    fields_desc=[ByteField("swid",0),
                ShortField("qdepth",0)
                ]
    def extract_padding(self,p):
        return "",p
class Flow_header(Packet):
    name="Flow_header"
    fields_desc=[
        #BitField("count",0x0,4),
        #BitField("routeid",0x0,20),
        ByteField("count",0),
        ShortField("routeid",0),
        ByteField("protocol",0),
        PacketListField("int",[],INT,count_from=lambda pkt:(pkt.count*1))
    ]

bind_layers(Ether,Flow_header,type=0x0801)
bind_layers(Flow_header,IP)

def handle_pkt(pkt,data_info,flag):
    #normallize data
    switch_data={}
    switch_id_list=[]
    count=pkt[Flow_header].count
    for i in range(count):
        swid=pkt[Flow_header].int[i].swid
        switch_data[str(swid)]=pkt[Flow_header].int[i].qdepth
        switch_id_list.append(str(swid))
    # if count>=3:
    #     for i in range(1,count-2):
    #         if int(switch_id_list[i])<int(switch_id_list[i+1]):
    #             link_id=switch_id_list[i].zfill(2)+"-"+switch_id_list[i+1].zfill(2)
    #         else:
    #             link_id=switch_id_list[i+1].zfill(2)+"-"+switch_id_list[i].zfill(2)
    #            #eg."01-19"
    #         link_delay=pkt[Flow_header].int[i].in_timestamp-pkt[Flow_header].int[i+1].in_timestamp
    #         if link_delay>0:
    #             switch_data[link_id]=link_delay #single hop delay
    if flag.empty()==True:
        data_info.put(switch_data)
    else:
        pass
    sys.stdout.flush()

def listen(veth,data_info,flag):
    sniff(iface = veth, filter="ether proto 0x0801",prn = lambda x: handle_pkt(x,data_info,flag),store=0)

# def read(data_info,flag):
#     print "processing to read %s" %os.getpid()
#     while True:
#         while flag.empty():
#             time.sleep(runtime)
#             flag.put("1")
#             while data_info.empty()==False:
#                 value=data_info.get(True)
#                 print("get from quene",value)
#             time.sleep(1)
#             flag.get()
#         print flag.qsize()
