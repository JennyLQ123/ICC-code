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

def thrift_connect(thrift_ip, thrift_port, services, out=sys.stdout):
    def my_print(s):
        out.write(s)

    # Make socket
    transport = TSocket.TSocket(thrift_ip, thrift_port)
    # Buffering is critical. Raw sockets are very slow
    transport = TTransport.TBufferedTransport(transport)
    # Wrap in a protocol
    bprotocol = TBinaryProtocol.TBinaryProtocol(transport)

    clients = []

    for service_name, service_cls in services:
        if service_name is None:
            clients.append(None)
            continue
        protocol = TMultiplexedProtocol.TMultiplexedProtocol(bprotocol, service_name)
        client = service_cls(protocol)
        clients.append(client)

    # Connect!
    try:
        transport.open()
    except TTransport.TTransportException:
        my_print("Could not connect to thrift client on port {}\n".format(
            thrift_port))
        my_print("Make sure the switch is running ")
        my_print("and that you have the right port\n")
        sys.exit(1)

    return clients

def MaxMinNormalization(x,Max,Min):
    if Max==Min:
        return float(x)
    x=(x-Min)/float(Max-Min)
    return x

def Z_ScoreNormalization(x,mu,sigma):
    x=(x-mu)/sigma;
    return x

def sigmoid(x,useStatus):
    if useStatus:
        return 1.0/(1+np.exp(-float(x)))
    else:
        return float(x)

def SciKitLearn(v):
    norm=np.linalg.norm(v)
    if norm==0:
        return v
    return v/norm

class SWITCH():

    def __init__(self,thrift_port,thrift_ip="localhost"):
        self.client=thrift_connect(thrift_ip, thrift_port, [("standard", Standard.Client)])[0]

    def counter_read(self,counter_name,index):
        message=self.client.bm_counter_read(cxt_id=0, counter_name=counter_name,index=index)
        return message
    def counter_reset(self,counter_name):
        self.client.bm_counter_reset_all(cxt_id=0, counter_name=counter_name)
    def register_write(self,register_name,index,value):
        self.client.bm_register_write(0,register_name,index,value)

    def table_delete(self,table,entry_handle):
        self.client.bm_mt_delete_entry(0,table,entry_handle)
    def register_read(self, register_name, index):
        return self.client.bm_register_read(0, register_name, index)
    def set_default_action(self,table_name,action,runtime_data,runtime_data_types):
        self.client.bm_mt_set_default_action(0, table_name=table_name, action_name=action, action_data=runtimedata.parse_runtime_data(runtime_data,runtime_data_types))
    def table_modify(self,table,handle,action,runtime_data,runtime_data_types):
        message = self.client.bm_mt_modify_entry(0,table,handle,action,runtimedata.parse_runtime_data(runtime_data,runtime_data_types))
        return message
    #types mean "ip" or "mac" or a "integer", integer is bitwidth of a param
    def table_add_lpm(self,table,match_key,match_key_types,action,runtime_data,runtime_data_types):
        message=self.client.bm_mt_add_entry(0,table,runtimedata.parse_lpm_match_key(match_key,match_key_types),action,runtimedata.parse_runtime_data(runtime_data,runtime_data_types),BmAddEntryOptions(priority = 0))
        return message
    def table_add_exact(self,table,match_key,match_key_types,action,runtime_data,runtime_data_types):
        message=self.client.bm_mt_add_entry(0,table,runtimedata.parse_match_key(match_key,match_key_types),action,runtimedata.parse_runtime_data(runtime_data,runtime_data_types),BmAddEntryOptions(priority = 0))
        return message
    def table_add_ternary(self,table,match_key,match_key_types,action,runtime_data,runtime_data_types,priority):
        message=self.client.bm_mt_add_entry(0,table,rumtimedata.parse_ternary_match_key(match_key,match_key_types),action,runtimedata.parse_runtime_data(runtime_data,runtime_data_types),BmAddEntryOptions(priority=priority))
        return message
    def table_get(self,table_name):
        message = self.client.bm_mt_get_entries(0,table_name)
        return message;
    def mirroring_add(mirror_id, egress_port):
        self.client.mirroring_mapping_add(self, mirror_id, egress_port)
    def create_group(self,action_profile_name):
        message=self.client.bm_mt_act_prof_create_group(0,act_prof_name=action_profile_name)
        return message
    def add_member_to_group(self,action_profile_name, mbr_handle, grp_handle):
        message=self.client.bm_mt_act_prof_add_member_to_group(0,action_profile_name, mbr_handle, grp_handle)
        return message
    def act_prof_add_member(self,action_profile_name,action_name,runtime_data,runtime_data_types):
        message=self.client.bm_mt_act_prof_add_member(0, action_profile_name, action_name, action_data=runtimedata.parse_runtime_data(runtime_data,runtime_data_types))
        return message
    def act_prof_remove_member_from_group(self,action_profile_name,mbr_handle,grp_handle):
        message=self.client.bm_mt_act_prof_remove_member_from_group(0,action_profile_name,mbr_handle,grp_handle)
    def add_entry_to_group(self,table_name, match_key,match_key_types, grp_handle):
        self.client.bm_mt_indirect_ws_add_entry(0, table_name=table_name, match_key=runtimedata.parse_ternary_match_key(match_key,match_key_types), grp_handle=grp_handle, options=BmAddEntryOptions(priority = 0))
