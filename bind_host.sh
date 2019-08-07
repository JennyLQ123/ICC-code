intf0=$1
intf1=$2
num=$3
if ! ip link show $intf0 &> /dev/null; then
    ip netns del ns$num &>/dev/null
    ip netns add ns$num
    ip link add name $intf0 type veth peer name $intf1
    ip link set $intf0 netns ns$num
    ip netns exec ns$num ip addr add 10.0.$num.1/24 dev $intf0
    ip netns exec ns$num ip link set dev $intf0 address 10:00:11:11:$num:12
    ip netns exec ns$num ip link set $intf0 up
    ip netns exec ns$num ip link set lo up

    ip link set dev $intf1 address 10:00:11:11:$num:11
    ip addr add 10.0.$num.2/24 dev $intf1
    ip link set dev $intf1 up

    ip netns exec ns$num ip route add default via 10.0.$num.2

    TOE_OPTIONS="rx tx sg tso gso gro lro rxvlan txvlan rxhash"
    for TOE_OPTION in $TOE_OPTIONS; do
        ip netns exec ns$num /sbin/ethtool --offload $intf0 "$TOE_OPTION" off
       /sbin/ethtool --offload $intf1 "$TOE_OPTION" off
    done
fi
sysctl net.ipv6.conf.$intf1.disable_ipv6=1
