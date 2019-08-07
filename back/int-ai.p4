header_type ethernet_t {
    fields{
        dstAddr:48;
        srcAddr:48;
        etherType:16;
    }
}

header ethernet_t ethernet;

header_type ipv4_t {
    fields{
        version:4;
        ihl:4;
        diffserv:8;
        totalLen:16;
        identification:16;
        flags:3;
        flagOffset:13;
        ttl:8;
        protocol:8;
        hdrChecksum:16;
        srcAddr:32;
        dstAddr:32;
    }
}

header ipv4_t ipv4;

header_type int_t {
    fields{
        swid:8;
        qtimedelta:32;
        in_timestamp:32;
	e_timestamp:32;
    }
}

header int_t int[5];

header_type flow_t{
	fields{
		count:8;
		routeid:16;
		protocol:8;
	}
}

header flow_t flow_header;

header_type custom_metadata_t{
    fields{
        parse_int_counter:8;
        routeid:16;
        dstAddr:32;
        register_tmp:32;
    }
}

metadata custom_metadata_t meta;

header_type intrinsic_metadata_t{
    fields{
        ingress_global_timestamp:48;
	egress_global_timestamp:48;
        lf_field_list:8;
        mcast_grp:16;
        egress_rid:16;
        resubmit_flag:8;
        recirculate_flag:8;
    }
}

metadata intrinsic_metadata_t intrinsic_metadata;

header_type queueing_metadata_t{
    fields{
        enq_timestamp:48;
        enq_qdepth:16;
        deq_timedelta:32;
        deq_qdepth:16;
        qid:8;
    }
}

metadata queueing_metadata_t queueing_metadata;

field_list ipv4_checksum_list {
        ipv4.version;
        ipv4.ihl;
        ipv4.diffserv;
        ipv4.totalLen;
        ipv4.identification;
        ipv4.flags;
        ipv4.flagOffset;
        ipv4.ttl;
        ipv4.protocol;
        ipv4.srcAddr;
        ipv4.dstAddr;
}

field_list_calculation ipv4_checksum {
    input {
        ipv4_checksum_list;
    }
    algorithm : csum16;
    output_width : 16;
}

calculated_field ipv4.hdrChecksum  {
    verify ipv4_checksum;
    update ipv4_checksum;
}

@pragma header_ordering ethernet flow_header int ipv4
parser start{
    return parse_ethernet;
}

#define IPV4 0x0800
#define FLOW 0x0801

parser parse_ethernet{
    extract(ethernet);
    return select(latest.etherType){
        IPV4:parse_no_flow_header;
	FLOW:parse_flow_header;
        default:ingress;
    }
}

parser parse_no_flow_header{
    set_metadata(meta.routeid,0);
    return parse_ipv4;
}

#define INT 0x01
#define FLOW_IPV4 0x00

parser parse_flow_header{
	extract(flow_header);
	set_metadata(meta.routeid,flow_header.routeid);
	set_metadata(meta.parse_int_counter,flow_header.count);
	return select(flow_header.protocol){
		INT:parse_int;
		FLOW_IPV4:parse_ipv4;
	}
}

parser parse_int{
    extract(int[next]);
    set_metadata(meta.parse_int_counter,meta.parse_int_counter-1);
    return select(meta.parse_int_counter){
	0:parse_ipv4;
	default:parse_int;
	}
}

parser parse_ipv4{
    extract(ipv4);
    return ingress;
}

action set_routeid(routeid){
    add_header(flow_header);
    modify_field(flow_header.routeid,routeid);
    modify_field(ethernet.etherType,0x0801);
}

table create_flow_header{
    reads{
        ipv4.dstAddr:lpm;
    }
    action_profile:set_routeid_profile;
    size:100;
}

action_profile set_routeid_profile{
    actions{
        set_routeid;
	my_drop;
    }
    size:5;
    dynamic_action_selection:routeid_selector;
}

field_list routeid_hash_fields{
    ipv4.srcAddr;
    ipv4.dstAddr;
    ipv4.protocol;
}

field_list_calculation routeid_hash{
    input{
        routeid_hash_fields;
    }
    algorithm:crc16;
    output_width:16;
}

action_selector routeid_selector{
    selection_key:routeid_hash;
}

counter my_counter{
    type:packets;
    instance_count:10;
}

action my_drop(){
    drop();
}

table routeid_fwd{
    reads{
        flow_header.routeid:exact;
    }
    actions{
        ipv4_fwd;
        fwd2host;
        my_drop;
    }
}

action ipv4_fwd(port){
    modify_field(standard_metadata.egress_spec,port);
    modify_field(ipv4.ttl,ipv4.ttl-1);
    count(my_counter,port);
}

action fwd2host(dstAddr,port){
    modify_field(standard_metadata.egress_spec,port);
    modify_field(ethernet.dstAddr,dstAddr);
    modify_field(ethernet.etherType,0x0800);
    modify_field(ipv4.ttl,ipv4.ttl-1);
}

field_list clone_filed{
    meta.dstAddr;
}

register my_register{
    width:32;
    static:check_register;
    instance_count:1;
}

table check_register{
    actions{
        checkregister;
    }
}

action checkregister(){
    register_read(meta.register_tmp,my_register,0);
    modify_field(meta.register_tmp,intrinsic_metadata.ingress_global_timestamp-meta.register_tmp);
}

table clone_to_controller{
    actions{
        c2c;
    }
}

action c2c(){
    modify_field(meta.dstAddr,ethernet.dstAddr);
    clone_i2e(1,clone_filed);
    register_write(my_register,0,intrinsic_metadata.ingress_global_timestamp);

}

control ingress{
	if(meta.routeid==0){
      		apply(create_flow_header);
    	}
    	apply(routeid_fwd);
    
    	if((flow_header.count==4)||(ethernet.etherType==0x800)){
      		apply(check_register);
      		if(meta.register_tmp>=1000000){
        		apply(clone_to_controller);
      		}
    	}
}

control egress{
	apply(add_int);
	if((standard_metadata.instance_type==0) && (ethernet.etherType==0x800)){
		apply(remove_additional_header);
	}
    	if(standard_metadata.instance_type==2){
      		apply(trunc_header);
	}
}


table add_int{
	reads{
		flow_header.count:exact;
	}
	actions{
		ad_first_int;
		ad_else_int;
	}
	size:2;
}

action ad_first_int(swid){
	add_header(int[0]);
	add_to_field(flow_header.count,+1);
	modify_field(int[0].swid,swid);
    	modify_field(flow_header.protocol,0x01);
	modify_field(int[0].qtimedelta,queueing_metadata.deq_timedelta);
	modify_field(int[0].in_timestamp,intrinsic_metadata.ingress_global_timestamp);
	modify_field(int[0].e_timestamp,intrinsic_metadata.egress_global_timestamp);	
}

action ad_else_int(swid){
	push(int,1);
	modify_field(int[0].swid,swid);
	add_to_field(flow_header.count,+1);
	modify_field(int[0].qtimedelta,queueing_metadata.deq_timedelta);
	modify_field(int[0].in_timestamp,intrinsic_metadata.ingress_global_timestamp);
	modify_field(int[0].e_timestamp,intrinsic_metadata.egress_global_timestamp);
}

table remove_additional_header{
    actions{
        rmv_header;
    }
}

action rmv_header(){
	remove_header(flow_header);
	pop(int,5);
}

table trunc_header{
	actions{tc_header;}
}

action tc_header(){
	remove_header(ethernet);
	remove_header(ipv4);
}
