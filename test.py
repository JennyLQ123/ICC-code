from class_define import SWITCH,thrift_connect,MaxMinNormalization,Z_ScoreNormalization,sigmoid,SciKitLearn

def switchConnect():
    try :
        switch_list=[]
        for index in range(switch_num):
            sw=SWITCH(9000+index,"127.0.0.1")
            switch_list.append(sw)
    except:
        print "connect error"
    return switch_list


def writeRouteidTable(switch,routeid_list,actionProfileName,dst_ip_addr,priority):
    routeid_num=len(routeid_list) #2
        #create_group
    group_info=switch.create_group(actionProfileName)
        ##add set_routeid action to member
    for i in range(routeid_num):
        member_info=switch.act_prof_add_member(action_profile_name=actionProfileName,
                            action_name="set_routeid",
                            runtime_data=[str(routeid_list[i])],
                            runtime_data_types=['16'])
        #routeid_handle[str(routeid_list[i])]=member_info
        switch.add_member_to_group(action_profile_name=actionProfileName,
                            mbr_handle=member_info,
                            grp_handle=group_info)
        #add table_entry
    switch.add_entry_to_group(table_name="create_flow_header",match_key=[dst_ip_addr,4294967040],
                            match_key_types=["ip","32"],grp_handle=group_info,priority=priority)
new_route_id="031903"
dst_eth_addr="10:11:11:11:03:12"
SWITCH_TO_HOST_PORT=10
sw=SWITCH(9003,"127.0.0.1")
info=sw.table_add_exact(
        table="routeid_fwd",
        action="fwd2host",
        match_key=[str(new_route_id)],
        match_key_types=['16'],
        runtime_data=[dst_eth_addr,str(SWITCH_TO_HOST_PORT)],
        runtime_data_types=['mac','9']
)
