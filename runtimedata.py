import struct
from bm_runtime.standard.ttypes import *

def bytes_to_string(byte_array):
    form = 'B' * len(byte_array)
    return struct.pack(form, *byte_array)

def ipv4Addr_to_bytes(addr):
    s = addr.split('.')
    return [int(b) for b in s]

def macAddr_to_bytes(addr):
    s = addr.split(':')
    return [int(b, 16) for b in s]

def int_to_bytes(i, num):
    byte_array = []
    while i > 0:
        byte_array.append(i % 256)
        i = i / 256
        num -= 1
    if num < 0:
        raise UIn_BadParamError("Parameter is too large")
    while num > 0:
        byte_array.append(0)
        num -= 1
    byte_array.reverse()
    return byte_array

def parse_param(input_str, t):
    if t == "ip":
        return ipv4Addr_to_bytes(input_str)
    elif t == "mac":
        return macAddr_to_bytes(input_str)
    else:
        return int_to_bytes(int(input_str), (int(t) + 7) / 8)

def parse_runtime_data(params, types):
    byte_array = []
    for input_str, t in zip(params, types):
        byte_array += [bytes_to_string(parse_param(input_str, t))]
    return byte_array

def parse_match_key(key_fields, types):
    params = []
    #print "key "+ key_fields+ " type" + types
    for input_str, t in zip(key_fields, types):
        key = bytes_to_string(parse_param(input_str,t))
        param = BmMatchParam(type= BmMatchParamType.EXACT,exact = BmMatchParamExact(key))
        params.append(param)
    return params

def parse_lpm_match_key(key_fields, types):
    params = []
    tmp=[]
    #print "key "+ key_fields+ " type" + types
    for input_str, t in zip(key_fields, types):
        key = bytes_to_string(parse_param(input_str,t))
        tmp.append(key)
    param = BmMatchParam(type=BmMatchParamType.LPM,lpm = BmMatchParamLPM(key=tmp[0],prefix_length=int(tmp[1])))
    params.append(param)
    return params
def parse_ternary_match_key(key_fields,types):
    params=[]
    tmp=[]
    for input_str,t in zip(key_fields,types):
        key=bytes_to_string(parse_param(input_str,t))
        tmp.append(key)
    param=BmMatchParam(type=BmMatchParamType.TERNARY,ternary=BmMatchParamTernary(key=tmp[0],mask=tmp[1]))
    params.append(param)
    return params
